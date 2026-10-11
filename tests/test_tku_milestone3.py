"""Capture-year gate, actual form scope, and content/year review regressions."""
import gzip
import importlib
import json
from pathlib import Path
from fastapi.testclient import TestClient
from exchange_info.api import create_app
from exchange_info.tku_data import BUNDLE
from scripts.tku_capture_io import read_bytes

ROOT=Path(__file__).resolve().parents[1]


def test_capture_period_does_not_use_upload_filename_or_modified_time(monkeypatch):
    monkeypatch.syspath_prepend(str(ROOT/'scripts'))
    policy=importlib.import_module('tku_photo_date_policy')
    uploaded=dict(extmetadata={'DateTimeOriginal':{'value':'20 June 2008 (original upload date)'}},metadata=[{'name':'DateTime','value':'2011:01:01'}])
    assert policy.reviewed_date(uploaded)[:2]==('capture_year_not_verified',None)
    uploaded['metadata'].append({'name':'DateTimeOriginal','value':'2006:09:30 04:55:42'})
    assert policy.reviewed_date(uploaded)[:2]==('verified_capture_period','2006:09:30 04:55:42')
    conflict=dict(extmetadata={'DateTimeOriginal':{'value':'2010-06-12'}},metadata=[{'name':'DateTimeOriginal','value':'2009:03:27'}])
    assert policy.reviewed_date(conflict)[:2]==('conflicting_capture_years_requires_confirmation',None)


def test_date_holds_and_replacements_are_visible_and_keep_history():
    holds=json.loads((BUNDLE/'photo_date_holds.json').read_text())
    assert {r['id'] for r in holds}=={'tku-sister-37','tku-sister-173'}
    original=json.loads((BUNDLE/'photo_date_review.json').read_text())
    assert len(original)==264 and sum(r['status']!='verified_capture_period' for r in original)==17
    photos={r['id']:r for r in json.loads((BUNDLE/'campus_asset_manifest.json').read_text())}
    assert not set(r['id'] for r in holds).intersection(photos)
    assert '12 March 2021' in photos['tku-sister-30']['photo_date']
    assert photos['tku-sister-78']['photo_date'].startswith('2006:09:30')
    assert '0_DanKooKU_3a.jpg' in photos['tku-sister-41']['source_url']
    assert 'Gatton' in photos['tku-sister-4']['identity_quote']
    history=json.loads((BUNDLE/'new_photo_visual_review_history.json').read_text())
    assert any(r['sha256']=='51adaaedb45c41f82a7bca8464514022a966518c75b01b500c3dcfcddff3a6c5' for r in history['tku-sister-41'])
    assert 'tku-sister-320' not in photos  # Actual candidate is an accreditation letter.


def test_named_place_coordinates_and_conflicting_official_laval_are_separate():
    reviews={r['id']:r for r in json.loads((BUNDLE/'milestone3_geography_review.json').read_text())}
    locations={r['id']:r for r in json.loads((BUNDLE/'campus_location_manifest.json').read_text())}
    assert len(locations)==264
    for identifier in ['tku-sister-337','tku-sister-240','tku-sister-48','tku-sister-14']:
        r=reviews[identifier];point=locations[identifier]['location']
        assert r['rejected_viewport_coordinates'] and point['allocation_status']=='TKU_nomination_campus_not_verified'
        assert point['precision']=='campus' and len(r['accepted_coordinate']['evidence'])==2
    assert locations['tku-sister-48']['location']['latitude']==3.0990297
    assert locations['tku-sister-14']['location']['longitude']==24.8046054
    conflict=reviews['tku-sister-195']
    assert 'accepted_coordinate' not in conflict and 'tku-sister-195' not in locations
    assert {r['longitude'] for r in conflict['claims']}=={-0.8391851,-0.7567847}
    assert all(r['checked_at'] and r['content_sha256'] for r in conflict['claims'])


def test_offline_legacy_doc_is_read_and_excluded_without_erasing_unparsed_attempt():
    review=json.loads((BUNDLE/'legacy_doc_content_review.json').read_text())
    assert review['status']=='read_and_excluded_full_degree_scholarship' and review['applicable_year']=='2026'
    assert review['parser']['conversion_exit_code']==0 and review['parser']['macro_security_level']==3
    assert review['parser']['external_link_update']==0
    old=json.loads(gzip.decompress(read_bytes(BUNDLE/'host_census_sources'/(review['original_capture_id']+'.json.gz'))))
    assert old['content_extraction_status']=='legacy_DOC_parser_not_available'
    parsed=json.loads(gzip.decompress(read_bytes(BUNDLE/'host_census_sources'/(review['source_id']+'.json.gz'))))
    assert '（2026年度）' in parsed['text'] and '博士研究生/ Doctor graduate student' in parsed['text']
    row=next(json.loads(line) for line in (BUNDLE/'partner_enrichment.jsonl').read_text().splitlines() if json.loads(line)['id']=='tku-sister-225')
    assert any(b['id']==review['source_id'] and b['reason']=='2026_full_degree_doctoral_scholarship_not_TKU_exchange' for b in row['blockers'])


def test_reviewed_host_facts_have_verbatim_content_and_keep_period_unknown():
    rows=json.loads((BUNDLE/'milestone3_reviewed_host_facts.json').read_text())
    assert len(rows)==18 and sum(len(r['fields']) for r in rows)==125
    for row in rows:
        for fact in row['fields'].values():
            assert fact['status']=='reference_only' and fact['reason'] and isinstance(fact['source_period_verified'],bool)
            for e in fact['evidence']:
                assert e['source_url'] and e['applicable_year'] and e['checked_at'] and e['content_sha256']
                if e.get('source_id'):
                    s=json.loads(gzip.decompress(read_bytes(BUNDLE/'host_census_sources'/(e['source_id']+'.json.gz'))))
                    assert e['content_sha256']==s['sha256'] and e['quote'] in s['text']
    byid={r['id']:r['fields'] for r in rows}
    assert not any(f['source_period_verified'] for f in byid['tku-sister-212'].values())
    assert 'Erasmus+' in byid['tku-sister-329']['host_deadline']['value']
    assert '5.5' in byid['tku-sister-18']['host_language']['value']
    nics=byid['tku-sister-34'];assert len(nics['latest_forms']['attachment_checks'])==8
    assert '矛盾' in nics['latest_forms']['value'] and '2026/10/31' in nics['host_deadline']['value']
    for a in nics['latest_forms']['attachment_checks']:
        assert a['http_status']==200 and a['content_reviewed']
        if a['local_file']:assert read_bytes(BUNDLE/'host_census_sources'/a['local_file']).startswith((b'%PDF',b'PK'))
    turku=byid['tku-sister-201']
    assert not any(f['source_period_verified'] for f in turku.values())
    assert '6.0' in turku['host_language']['value'] and 'Jan26' in turku['host_language']['value']
    assert '文字差異' in turku['course_restrictions']['value']
    assert len(turku['latest_forms']['attachment_checks'])==3
    doc=turku['latest_forms']['attachment_checks'][0]
    assert doc['original_capture_id']=='ece224cc69debe307237cc3c'
    assert doc['rendered_pages']==2 and doc['visual_review'] and doc['parser']['macro_security_level']==3
    assert read_bytes(BUNDLE/'host_census_sources'/doc['rendered_file']).startswith(b'%PDF')
    parsed=json.loads(gzip.decompress(read_bytes(BUNDLE/'host_census_sources'/(doc['source_id']+'.json.gz'))))
    assert 'Evaluation table' in parsed['text'] and 'signature and date' in parsed['text']
    scopes=json.loads((BUNDLE/'milestone3_source_scope_reviews.json').read_text())
    bysource={s['source_id']:s for s in scopes}
    for n,sid in [(313,'dcf2041d54def6e85510d81d'),(239,'6e3b3818b370626c25471b58'),(55,'baa66800cf0b83ad1ed22084')]:
        row=next(json.loads(line) for line in (BUNDLE/'partner_enrichment.jsonl').read_text().splitlines() if json.loads(line)['id']=='tku-sister-'+str(n))
        assert bysource[sid]['exclude_from_semester_reference_index']
        assert any(b['id']==sid and b['reason']==bysource[sid]['status'] for b in row['blockers'])


def test_buaa_general_scholar_forms_keep_historical_route_and_exclude_other_programmes():
    rows=json.loads((BUNDLE/'milestone3_reviewed_host_facts.json').read_text())
    fields=next(r['fields'] for r in rows if r['id']=='tku-sister-134')
    deadline=fields['host_deadline']
    assert deadline['status']=='reference_only' and deadline['source_period_verified']
    assert '2025/12/30' in deadline['value'] and '2026/6/30' in deadline['value']
    assert '2027新期限未核實' in deadline['value']
    assert 'TKU' in fields['host_eligibility']['value'] and 'route未核實' in fields['host_eligibility']['value']
    attachments=fields['latest_forms']['attachment_checks']
    assert {a['source_id'] for a in attachments}=={'9d90ee5fd05be71cd0090e91','1c166f394bc38069c5b3adeb'}
    for a in attachments:
        assert a['http_status']==200 and a['content_reviewed'] and a['pages']==2
        parsed=json.loads(gzip.decompress(read_bytes(BUNDLE/'host_census_sources'/(a['source_id']+'.json.gz'))))
        if a.get('original_capture_id'):
            assert 'Form004' in parsed['text'] and 'Form005' not in parsed['text']
            assert a['parser']['macro_security_level']==3 and a['parser']['external_link_update']==0
            assert read_bytes(BUNDLE/'host_census_sources'/a['rendered_file']).startswith(b'%PDF')
        else:
            assert read_bytes(BUNDLE/'host_census_sources'/a['local_file']).startswith(b'%PDF')
    scope={s['source_id']:s for s in json.loads((BUNDLE/'milestone3_source_scope_reviews.json').read_text())}
    for sid in ['3dcccb971fe5bb807320f579','43a84c277b5e46de792b9343','cc036c4ec7b374d1419c2673']:
        assert scope[sid]['exclude_from_semester_reference_index']
        assert scope[sid]['quote'] and scope[sid]['content_sha256']
    assert 'for 4 years' in scope['3dcccb971fe5bb807320f579']['quote']


def test_new_host_refs_leave_home_quotas_and_application_catalog_unexpanded(tmp_path):
    client=TestClient(create_app(tmp_path))
    dashboard=client.get('/student-dashboard',params={'school':'TKU'}).json()
    assert len(dashboard['partner_universities'])==287
    assert sum(p['image_status']=='verified' for p in dashboard['partner_universities'])==264
    assert all(p['reference_data']['campus_photo_capture_year_status']=='verified_capture_period' for p in dashboard['partner_universities'] if p['image_status']=='verified')
    audit=client.get('/tku/partner-census').json()
    assert audit['field_counts']['quota']['verified_current']==4 and audit['currently_open_home_applications']==0
    assert sum(v for k,v in audit['field_counts']['quota'].items() if k!='verified_current')==283
    nagasaki=next(p for p in dashboard['partner_universities'] if '長崎外國語' in p['school_name'])
    profile=client.get('/destination-profile',params={'school':nagasaki['school_name'],'home_school':'TKU'}).json()
    assert any(s['key']=='reviewed_host_reference_latest_forms' and '矛盾' in s['summary'] for s in profile['student_guide_sections'])
    for n in ['tku-sister-329','tku-sister-284','tku-sister-212']:
        response=client.get('/tku/partner-census/'+n)
        assert response.status_code==200
        r=response.json()
        assert r['fields']['quota']['status']!='verified_current'
