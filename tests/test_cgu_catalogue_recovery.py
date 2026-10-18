"""Failure injection / dated fixtures, explicitly distinct from live acceptance."""
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import threading

from fastapi.testclient import TestClient
import pytest
import requests

from exchange_info import api, cgu_catalogue as cgu


@pytest.fixture
def seed():
    return json.loads(cgu.BUNDLED_SNAPSHOT.read_text())


def changed(seed):
    result = deepcopy(seed)
    result["fetched_at"] = datetime.now(timezone.utc).isoformat()
    result["records"] = result["records"][1:]
    result["record_count"] = len(result["records"])
    result["records_sha256"] = cgu.records_hash(result["records"])
    return result


def test_bundled_snapshot_is_replayable_from_both_recorded_bodies(seed, monkeypatch):
    def get(url, **_):
        sheet_id = url.split('/d/')[1].split('/')[0]
        receipt = next(r for r in seed['source_receipts'] if r['spreadsheet_id'] == sheet_id)
        body = (cgu.BUNDLED_SNAPSHOT.parent / receipt['file']).read_bytes()
        assert hashlib.sha256(body).hexdigest() == receipt['sha256']
        response = requests.Response(); response.status_code = 200; response._content = body; response.encoding = 'utf-8'
        return response
    monkeypatch.setattr(cgu.requests, 'get', get)
    replayed = cgu.fetch_complete_snapshot()
    assert replayed['records'] == seed['records']
    assert replayed['records_sha256'] == seed['records_sha256']
    assert replayed['record_count'] == 77


@pytest.mark.parametrize('failure', ['timeout', 'http_error', 'transport_error', 'empty_response', 'invalid_response'])
def test_failed_refresh_retains_exact_rows_times_and_persisted_snapshot(tmp_path, seed, failure):
    path = tmp_path/'snapshot.json'; path.write_text(json.dumps(seed))
    before = path.read_bytes()
    def fail(): raise cgu.CatalogueFetchError(failure)
    store = cgu.CguCatalogue(path, fetcher=fail)
    view = store.refresh()
    assert len(view.partners) == 77 and view.source.status == 'saved_reference'
    assert view.source.last_attempt_result == 'failed' and view.source.failure_reason == failure
    assert view.source.last_success_at.isoformat() == seed['fetched_at']
    assert view.source.current_cycle_verified is False
    assert [row.model_dump(mode='json') for row in view.partners] == seed['records']
    assert path.read_bytes() == before


@pytest.mark.parametrize('damage', ['scope','receipt','empty','hash','older','missing_field'])
def test_invalid_replacements_are_not_published(tmp_path, seed, damage):
    candidate = changed(seed)
    if damage == 'scope': candidate['home_school'] = '國立臺灣大學'
    if damage == 'receipt': candidate['source_receipts'].pop()
    if damage == 'empty': candidate.update(records=[], record_count=0, records_sha256=cgu.records_hash([]))
    if damage == 'hash': candidate['records_sha256'] = '0'*64
    if damage == 'older': candidate['fetched_at'] = '2020-01-01T00:00:00Z'
    if damage == 'missing_field': del candidate['source_receipts'][0]['schema_valid']
    store = cgu.CguCatalogue(tmp_path/'snapshot.json', fetcher=lambda:candidate)
    assert len(store.refresh().partners) == 77
    assert store.view(refresh=False).source.last_attempt_result == 'failed'
    assert not store.path.exists()


def test_cold_start_uses_bundle_when_runtime_missing_or_corrupt(tmp_path):
    path = tmp_path/'snapshot.json'
    for body in ('{broken', '{}'):
        path.write_text(body)
        view = cgu.CguCatalogue(path).view(refresh=False)
        assert len(view.partners) == 77
        assert view.source.status == 'saved_reference' and view.source.last_attempt_at is None


def test_empty_cold_start_is_unavailable_then_recovers_without_restart(tmp_path, seed):
    tick = [0.0]; fail = [True]
    def fetch():
        if fail[0]: raise cgu.CatalogueFetchError('timeout')
        return seed
    store = cgu.CguCatalogue(tmp_path/'snapshot.json', bundled=None, fetcher=fetch, clock=lambda:tick[0])
    assert store.refresh().source.status == 'unavailable'
    fail[0] = False
    assert store.refresh().source.status == 'unavailable', 'failure retry is rate-limited'
    tick[0] = 61
    assert len(store.refresh().partners) == 77
    assert store.view(refresh=False).source.status == 'retrieved'
    restarted = cgu.CguCatalogue(store.path, bundled=None).view(refresh=False)
    assert len(restarted.partners) == 77 and restarted.source.status == 'saved_reference'


def test_atomic_write_failure_does_not_publish_new_rows_or_leave_partial_file(tmp_path, seed, monkeypatch):
    path = tmp_path/'snapshot.json'; path.write_text(json.dumps(seed)); original = path.read_bytes()
    store = cgu.CguCatalogue(path, fetcher=lambda:changed(seed))
    def no_space(*_): raise OSError(28, 'No space left')
    monkeypatch.setattr(cgu.os, 'replace', no_space)
    result = store.refresh()
    assert result.source.failure_reason == 'storage_failure' and len(result.partners) == 77
    assert path.read_bytes() == original and not list(tmp_path.glob('.cgu-*.tmp'))


def test_readers_share_one_refresh_and_receive_independent_copies(tmp_path, seed):
    entered, release = threading.Event(), threading.Event(); calls=[]
    def fetch(): calls.append(1); entered.set(); assert release.wait(5); return changed(seed)
    store = cgu.CguCatalogue(tmp_path/'snapshot.json', fetcher=fetch)
    first = store.view(); assert entered.wait(5)
    first.partners[0].quota = 'MUTATED'
    for _ in range(8): assert len(store.view().partners) == 77
    assert store.view(refresh=False).partners[0].quota == seed['records'][0]['quota']
    release.set()
    for thread in threading.enumerate():
        if thread.name == 'cgu-source-refresh': thread.join(10)
    assert calls == [1] and len(store.view(refresh=False).partners) == 76


@pytest.mark.parametrize('fault', ['second_timeout', 'http503', 'login_html', 'empty', 'bad_schema'])
def test_real_fetcher_rejects_partial_or_invalid_two_sheet_batch(monkeypatch, fault):
    def get(url, **_):
        sheet_id = url.split('/d/')[1].split('/')[0]
        if sheet_id == cgu.DOUBLE_DEGREE_SHEET_ID and fault == 'second_timeout': raise requests.Timeout()
        response=requests.Response(); response.status_code=503 if fault == 'http503' else 200
        response._content=(cgu.BUNDLED_SNAPSHOT.parent/f'{sheet_id}.gviz.json').read_bytes(); response.encoding='utf-8'
        if sheet_id == cgu.DOUBLE_DEGREE_SHEET_ID:
            if fault == 'login_html': response._content=b'<html>login</html>'
            if fault in ('empty', 'bad_schema'):
                payload=cgu._parse_gviz_payload(response.text)
                payload['table']['rows']=[]
                if fault=='bad_schema': payload['table']['cols']=[{'label':'校名'}]
                response._content=json.dumps(payload).encode()
                response._content=b'google.visualization.Query.setResponse('+response._content+b');'
        return response
    monkeypatch.setattr(cgu.requests, 'get', get)
    with pytest.raises(cgu.CatalogueFetchError): cgu.fetch_complete_snapshot()


def test_dashboard_and_workflow_share_success_failure_and_recovery(tmp_path, seed, monkeypatch):
    tick=[0.0]; state=[None]
    def fetch():
        if state[0] is None: raise cgu.CatalogueFetchError('timeout')
        return state[0]
    store=cgu.CguCatalogue(tmp_path/'snapshot.json', fetcher=fetch, clock=lambda:tick[0]); store.refresh()
    monkeypatch.setattr(api, 'create_cgu_catalogue', lambda _:store)
    monkeypatch.setattr('exchange_info.student_view.fetch_document_explanations', lambda **_:[])
    client=TestClient(api.create_app(tmp_path))
    params={'school':'林肯大學 Lincoln University','home_school':'長庚大學'}
    first=client.get('/student-dashboard').json()
    assert len(first['partner_universities'])==77 and first['catalogue_source']['failure_reason']=='timeout'
    assert client.get('/application-workflow',params=params).status_code==200
    state[0]=changed(seed); tick[0]=61; store.refresh()
    second=client.get('/student-dashboard').json()
    assert len(second['partner_universities'])==76 and second['catalogue_source']['status']=='retrieved'
    assert client.get('/application-workflow',params=params).status_code==404
    state[0]=None; tick[0]=662; store.refresh()
    third=client.get('/student-dashboard').json()
    assert len(third['partner_universities'])==76 and third['catalogue_source']['status']=='saved_reference'
    assert second['partner_universities']==third['partner_universities']


def test_no_snapshot_returns_explicit_unavailable_and_retryable_lookup_only_for_cgu(tmp_path, monkeypatch):
    def fetch():raise cgu.CatalogueFetchError('timeout')
    store=cgu.CguCatalogue(tmp_path/'snapshot.json', bundled=None, fetcher=fetch);store.refresh()
    monkeypatch.setattr(api,'create_cgu_catalogue',lambda _:store)
    monkeypatch.setattr('exchange_info.student_view.fetch_document_explanations',lambda **_:[])
    client=TestClient(api.create_app(tmp_path))
    dash=client.get('/student-dashboard',params={'school':'長庚大學'}).json()
    assert dash['partner_universities']==[] and dash['catalogue_source']['status']=='unavailable'
    lookup=client.get('/application-workflow',params={'school':'林肯大學 Lincoln University','home_school':'長庚大學'})
    assert lookup.status_code==503 and lookup.headers['retry-after']=='60'
    assert len(client.get('/universities').json())==16
    for home in ('國立臺北大學','國立臺灣大學','國立中正大學','國立中央大學','淡江大學'):
        reply=client.get('/student-dashboard',params={'school':home})
        assert reply.status_code==200 and reply.json()['partner_universities']
        assert reply.json().get('catalogue_source') is None


def test_quota_zero_missing_and_pending_states_survive_success_and_failure(tmp_path, seed):
    candidate = deepcopy(seed)
    for row, quota, status in zip(candidate['records'], ['0', None, ''], ['open', 'quota_unconfirmed', 'agreement_only']):
        row['quota'] = quota
        row['availability_status'] = status
    candidate['records_sha256'] = cgu.records_hash(candidate['records'])
    tick = [0.0]
    store = cgu.CguCatalogue(tmp_path/'snapshot.json', fetcher=lambda:candidate, clock=lambda:tick[0])
    success = store.refresh()
    assert [p.quota for p in success.partners[:3]] == ['0', None, '']
    assert [p.availability_status for p in success.partners[:3]] == ['open', 'quota_unconfirmed', 'agreement_only']
    def fail(): raise cgu.CatalogueFetchError('timeout')
    store.fetcher = fail; tick[0] = 601
    failure = store.refresh()
    assert [p.model_dump() for p in failure.partners] == [p.model_dump() for p in success.partners]
