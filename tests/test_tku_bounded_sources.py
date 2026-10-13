"""Prevent source challenges, wrong-campus candidates and host/home confusion."""
import importlib,json
from datetime import datetime,timezone,timedelta
from pathlib import Path
from exchange_info.tku_data import BUNDLE
from exchange_info.tku_census import school_audit

ROOT=Path(__file__).resolve().parents[1]

def test_retry_after_blocks_network_for_service(monkeypatch,tmp_path):
    monkeypatch.syspath_prepend(str(ROOT/'scripts'))
    module=importlib.import_module('capture_tku_asset_batch')
    monkeypatch.setattr(module,'B',tmp_path)
    until=(datetime.now(timezone.utc)+timedelta(hours=1)).isoformat()
    (tmp_path/'commons_service_pause.json').write_text(json.dumps({'resume_not_before':until}))
    def forbidden(*a,**k):raise AssertionError('Retry-After must prevent network calls')
    monkeypatch.setattr(module.requests,'get',forbidden)
    result=module.request('https://commons.wikimedia.org/w/api.php','commons')
    assert result['error']=='paused_retry_after_no_request' and result['resume_not_before']==until

def test_pdf_http202_challenge_is_retained_as_failed_content(monkeypatch,tmp_path):
    monkeypatch.syspath_prepend(str(ROOT/'scripts'))
    module=importlib.import_module('capture_tku_census_hosts')
    monkeypatch.setattr(module,'STORE',tmp_path)
    monkeypatch.setattr(module,'exists',lambda p:p.exists())
    class Response:
        status_code=202;url='https://official.example/guide.pdf';content=b'<html>challenge</html>';headers={}
        def raise_for_status(self):pass
    monkeypatch.setattr(module.requests,'get',lambda *a,**k:Response())
    source=module.capture(Response.url,key_suffix='|test-finite-retry')
    assert source['http_status']==202 and 'no PDF magic' in source['error']
    assert 'local_file' not in source and 'pages' not in source
    assert (tmp_path/(source['id']+'.json.gz')).exists()

def test_geo_review_rejects_wrong_city_parent_and_multiple_campus_points():
    reviews={r['id']:r for r in json.loads((BUNDLE/'wikidata_asset_review.json').read_text())}
    assert 'Winnipeg' in reviews['tku-sister-8']['reason']
    assert 'accepted_coordinate' not in reviews['tku-sister-8']
    assert 'Q10841229' in reviews['tku-sister-280']['candidate_ids']
    assert 'accepted_coordinate' not in reviews['tku-sister-280']
    for identifier in ['tku-sister-240','tku-sister-268','tku-sister-175','tku-sister-337']:
        assert reviews[identifier]['status']=='deferred_identity_or_campus'
    assert reviews['tku-sister-7']['selected_entity']=='Q612665'
    assert reviews['tku-sister-279']['selected_entity']=='Q258464'

def test_visual_rejections_and_siu_campus_metadata_conflict_survive():
    reviews=json.loads((BUNDLE/'new_photo_visual_review_history.json').read_text())
    for identifier in ['tku-sister-322','tku-sister-301','tku-sister-52']:
        assert any(r['result'] in {'rejected','reject'} for r in reviews[identifier])
    photos={r['id']:r for r in json.loads((BUNDLE/'campus_asset_manifest.json').read_text())}
    siu=photos['tku-sister-330']
    assert 'Lewis' in siu['caption'] and 'Fleming' in siu['source_metadata_conflict']

def test_confirmed_map_alternatives_and_non_exchange_document_scope():
    geo={r['id']:r for r in json.loads((BUNDLE/'official_geography_review.json').read_text())}
    assert geo['tku-sister-8']['accepted_coordinate']['location']['longitude']==-99.9625
    hkit=geo['tku-sister-246']['accepted_coordinate']['location']
    assert hkit['longitude']==114.1654064 and '視窗' in hkit['note'] and '中國大陸' in hkit['note']
    assert geo['tku-sister-28']['accepted_coordinate']['location']['latitude']==35.7218769
    assert '目的' in geo['tku-sister-28']['evidence']['locator'] or 'destination' in geo['tku-sister-28']['evidence']['locator']
    row=next(r for r in rows_enrichment() if r['id']=='tku-sister-225')
    assert any(r['reason']=='2026_full_degree_doctoral_scholarship_not_TKU_exchange' for r in row['blockers'])
    assert any(r['reason']=='binary_opened_content_and_period_not_verified' for r in row['blockers'])

def rows_enrichment():
    return [json.loads(line) for line in (BUNDLE/'partner_enrichment.jsonl').read_text().splitlines()]

def test_jwu_2027_rules_preserve_host_programme_year_and_estimate_conflict():
    row=next(r for r in json.loads((BUNDLE/'curated_partner_facts.json').read_text()) if r['id']=='tku-sister-326')
    f=row['fields']
    assert '男性' in f['host_eligibility']['value']
    assert '秋' in f['department_scope']['value']
    assert '12' in f['course_restrictions']['value'] and '14' in f['course_restrictions']['value']
    assert any('2026 academic year' in e['quote'] for e in f['course_restrictions']['evidence'])
    assert '2027/3/1' in f['host_nomination_deadline']['value']
    assert '2027/4/10' in f['host_deadline']['value']
    assert '4,840' in f['housing_costs']['value'] and '不一致' in f['housing_costs']['value']
    for fact in f.values():
        assert fact['status']=='reference_only'
        assert all(e['role']=='host_incoming' and e['locator'].startswith('PDF p.') for e in fact['evidence'])
    audit=school_audit('日本女子大學')
    assert audit['fields']['quota']['status']=='reference_only'
    assert all(f['selection_status']=='reference_only' for f in audit['fields']['quota']['values'])
