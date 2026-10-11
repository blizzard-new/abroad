"""Fault/recovery experiments on a reviewed design prototype, not production tests."""
from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
from datetime import datetime, timedelta
import json
from pathlib import Path
import threading

import pytest

from snapshot_prototype import Store, records_hash

SOURCE = Path(__file__).parent / 'source-capture/snapshot.json'


@pytest.fixture
def seed():
    return json.loads(SOURCE.read_text())


def stamp(seed, seconds=0):
    return datetime.fromisoformat(seed['fetched_at']) + timedelta(seconds=seconds)


def failed():
    raise RuntimeError('controlled source failure; no actual network')


def changed_batch(seed, records, *, seconds=120):
    result = deepcopy(seed)
    result.update(records=records, record_count=len(records), records_sha256=records_hash(records), fetched_at=stamp(seed, seconds).isoformat())
    return result


def test_cold_start_uses_dated_reference_without_claiming_a_new_fetch(tmp_path, seed):
    store = Store(tmp_path/'snapshot.json', bundled=seed)
    result = store.view()
    assert result['source_status'] == 'stale_reference'
    assert result['last_success_at'] == seed['fetched_at'] and result['last_attempt'] is None
    assert result['records'] == seed['records']


def test_outage_preserves_every_row_and_original_success_time(tmp_path, seed):
    store = Store(tmp_path/'snapshot.json', bundled=seed)
    result = store.refresh(failed, now=stamp(seed, 60))
    assert result['source_status'] == 'stale_reference'
    assert result['records'] == seed['records']
    assert result['last_success_at'] == seed['fetched_at']
    assert result['last_attempt']['at'] == stamp(seed,60).isoformat()


@pytest.mark.parametrize('broken', ['http_error', 'invalid_schema', 'partial_source', 'empty_source', 'empty_records', 'corrupt_hash', 'wrong_school'])
def test_invalid_batch_cannot_replace_known_good_snapshot(tmp_path, seed, broken):
    path = tmp_path/'snapshot.json'
    path.write_text(json.dumps(seed));previous=path.read_bytes()
    candidate=deepcopy(seed)
    if broken=='http_error':candidate['source_receipts'][0]['http_status']=503
    elif broken=='invalid_schema':candidate['source_receipts'][0]['schema_valid']=False
    elif broken=='partial_source':candidate['source_receipts'].pop()
    elif broken=='empty_source':candidate['source_receipts'][0]['raw_rows']=0
    elif broken=='empty_records':candidate.update(records=[],record_count=0,records_sha256=records_hash([]))
    elif broken=='corrupt_hash':candidate['records_sha256']='0'*64
    else:candidate['home_school']='國立臺灣大學'
    store=Store(path)
    result=store.refresh(lambda:candidate, now=stamp(seed,60))
    assert result['source_status']=='stale_reference'
    assert result['records']==seed['records'] and path.read_bytes()==previous


def test_no_snapshot_is_unavailable_never_fresh_zero(tmp_path, seed):
    result=Store(tmp_path/'missing.json').refresh(failed,now=stamp(seed))
    assert result['source_status']=='unavailable' and result['last_success_at'] is None
    assert result['last_attempt']['result']=='failed'
    # Proposed API/UI must render unavailable/503, not call these zero open schools.
    assert result['records']==[]


def test_recovery_can_remove_a_real_row_and_persist_a_complete_new_batch(tmp_path, seed):
    path=tmp_path/'snapshot.json';store=Store(path,bundled=seed)
    store.refresh(failed,now=stamp(seed,60))
    candidate=changed_batch(seed,seed['records'][:-1],seconds=180)
    result=store.refresh(lambda:candidate,now=stamp(seed,180))
    assert result['source_status']=='fresh' and len(result['records'])==76
    assert result['last_success_at']==candidate['fetched_at']
    assert json.loads(path.read_text())==candidate
    reloaded=Store(path,bundled=seed).view()
    assert reloaded['records']==candidate['records'] and reloaded['source_status']=='stale_reference'


def test_failure_retry_is_bounded_and_a_later_attempt_can_recover(tmp_path, seed):
    store=Store(tmp_path/'snapshot.json',bundled=seed);calls=[]
    def failure():calls.append(1);return failed()
    store.refresh(failure,now=stamp(seed));store.refresh(failure,now=stamp(seed,59))
    assert len(calls)==1
    result=store.refresh(lambda:changed_batch(seed,seed['records']),now=stamp(seed,120))
    assert result['source_status']=='fresh'


def test_a_view_cannot_mutate_other_students_snapshot(tmp_path, seed):
    store=Store(tmp_path/'snapshot.json',bundled=seed)
    view=store.view();view['records'][0]['quota']='untrusted mutation'
    assert store.view()['records']==seed['records']


def test_corrupt_runtime_file_falls_back_to_valid_bundled_snapshot(tmp_path, seed):
    path=tmp_path/'snapshot.json';path.write_text('{broken')
    assert Store(path,bundled=seed).view()['records']==seed['records']


def test_untrusted_or_older_snapshot_is_never_promoted(tmp_path, seed):
    wrong=deepcopy(seed);wrong['home_school']='國立中正大學'
    assert Store(tmp_path/'a.json',bundled=wrong).view()['source_status']=='unavailable'
    store=Store(tmp_path/'b.json',bundled=seed)
    prior=changed_batch(seed,seed['records'],seconds=-120)
    assert store.refresh(lambda:prior,now=stamp(seed))['source_status']=='stale_reference'
    assert store.view()['last_success_at']==seed['fetched_at']


def test_parallel_readers_do_not_duplicate_the_source_fetch(tmp_path, seed):
    store=Store(tmp_path/'snapshot.json',bundled=seed)
    started=threading.Event();release=threading.Event();calls=[]
    def fetch():calls.append(1);started.set();assert release.wait(3);return seed
    with ThreadPoolExecutor(max_workers=8) as pool:
        pending=pool.submit(store.refresh,fetch,now=stamp(seed));assert started.wait(3)
        futures=[pool.submit(store.refresh,fetch,now=stamp(seed)) for _ in range(7)]
        prior=[f.result(timeout=3) for f in futures]
        release.set();assert pending.result(timeout=3)['source_status']=='fresh'
    assert len(calls)==1 and all(r['records']==seed['records'] for r in prior)


def test_blank_zero_and_historical_fields_are_not_reclassified(tmp_path, seed):
    rows=deepcopy(seed['records'][:3])
    for row,quota in zip(rows,[None,'0','未公告']):
        row.update(quota=quota,academic_year='115',availability_status='reference_only',application_window_status='needs_confirmation')
    candidate=changed_batch(seed,rows)
    store=Store(tmp_path/'snapshot.json',bundled=candidate)
    assert store.refresh(failed,now=stamp(seed,180))['records']==rows


def test_failed_atomic_replace_leaves_previous_snapshot_readable(tmp_path, seed, monkeypatch):
    import snapshot_prototype
    path=tmp_path/'snapshot.json';path.write_text(json.dumps(seed));before=path.read_bytes()
    store=Store(path)
    def disk_failure(*args):raise OSError('controlled atomic replace failure')
    monkeypatch.setattr(snapshot_prototype.os,'replace',disk_failure)
    result=store.refresh(lambda:changed_batch(seed,seed['records'][:-1]),now=stamp(seed,180))
    assert result['source_status']=='stale_reference' and result['records']==seed['records']
    assert path.read_bytes()==before
    assert Store(path).view()['records']==seed['records']
