"""Full-denominator, source scope, asset licenses, and offline acceptance."""
import gzip
from scripts.tku_capture_io import read_bytes
import hashlib
import json
import subprocess
from collections import Counter
from datetime import datetime,timezone

from fastapi.testclient import TestClient

from exchange_info.api import create_app
from exchange_info.tku_census import census_audit,school_audit
from exchange_info.tku_data import BUNDLE,load_tku_records
from exchange_info.tku_student_view import fetch_tku_partner_universities


def rows(name):
    return [json.loads(line) for line in (BUNDLE/name).read_text().splitlines() if line.strip()]


def test_full_denominator_retains_omitted_institution_and_all_prior_programmes():
    census=rows('partner_census.jsonl');audit=census_audit()
    assert len(census)==len({r['id'] for r in census})==286
    assert len(audit['schools'])==len({r['id'] for r in audit['schools']})==287
    assert len(load_tku_records(include_reference=True))==128
    first=rows('earlier_round_programmes.jsonl')
    assert len(first)==len({r['id'] for r in first})==25
    assert sum(r['quota_number'] for r in first)==50
    assert all(r['selection_status']=='reference_only' and r['academic_year']=='2027-2028' for r in first)
    assert audit['programme_count']==153 and audit['currently_open_home_applications']==0
    omitted=[r for r in audit['schools'] if r['id'].startswith('tku-programme-')]
    assert len(omitted)==1 and '上海交通' in omitted[0]['school_name']
    assert '矛盾' in omitted[0]['selection_note']


def test_all_22_fields_preserve_reference_missing_and_current_counts():
    audit=census_audit();baseline=json.loads((BUNDLE/'full_census_baseline.json').read_text())
    assert baseline['institution_denominator']==287 and baseline['programme_count']==128
    for key,counts in audit['field_counts'].items():
        assert len(audit['field_counts'])==22 and sum(counts.values())==287
        assert Counter(r['fields'][key]['status'] for r in audit['schools'])==counts
        for r in audit['schools']:
            cell=r['fields'][key]
            assert cell['reason'] and cell['checked_entries']
            assert all(e['source_url'].startswith('http') and e['checked_at'] and e['applicable_year'] for e in cell['checked_entries'])
            for f in cell['values']:
                if f['status'] in {'missing_in_source','not_verified_new'}:
                    assert f['value'] is None
                assert f['evidence']
    assert audit['field_counts']['quota']['verified_current']==4
    assert audit['field_counts']['coordinates']['verified_asset']>=260
    assert audit['field_counts']['campus_photo']['verified_asset']>=264


def test_home_application_windows_never_promote_directory_or_old_quota():
    active=datetime(2026,9,24,tzinfo=timezone.utc)
    partners=fetch_tku_partner_universities(reference_time=active)
    assert len(partners)==len({p.school_name for p in partners})==287
    assert sum(p.availability_status=='open' for p in partners)==4
    assert sum(int(p.quota) for p in partners[:4])==7
    for p in partners[4:]:
        assert p.quota is None and p.quota_status=='reference_only'
        assert p.availability_status in {'agreement_only','reference_only'}
        assert p.eligibility is None and p.application_deadline is None
        assert all('不得沿用名額' in op.program_type for op in p.program_options)
    assert len(fetch_tku_partner_universities(include_agreements=False))==4


def test_reviewed_host_year_is_not_home_nomination_and_form_retries_keep_history():
    curated=json.loads((BUNDLE/'curated_partner_facts.json').read_text())[0]
    assert curated['id']=='tku-sister-178'
    assert school_audit('明治大學 Meiji University')['fields']['quota']['status']=='not_verified_new'
    fields=curated['fields']
    assert fields['latest_forms']['status']=='reference_only'
    assert all(r['http_status']==503 and r['error'] and not r['local_file'] for r in fields['latest_forms']['attachment_check_history'])
    checks=fields['latest_forms']['attachment_checks']
    assert len(checks)==5 and all(r['http_status']==200 and r['prior_http_status']==503 and r['content_reviewed'] for r in checks)
    for r in checks:
        blob=read_bytes(BUNDLE/r['local_file'])
        assert hashlib.sha256(blob).hexdigest()==r['sha256'] and blob.startswith((b'%PDF',b'PK'))
    assert any('after April 2026' in e['quote'] for e in fields['latest_forms']['evidence'])
    assert any('Courses (AY2026)' in e['quote'] for e in fields['latest_forms']['evidence'])
    assert fields['course_schedule']['status']=='explicit_not_finalized'
    for fact in fields.values():
        for e in fact['evidence']:
            s=json.loads(gzip.decompress(read_bytes(BUNDLE/'host_census_sources'/(e['source_id']+'.json.gz'))))
            assert e['content_sha256']==s['sha256'] and not s.get('error')
            text=s['pages'][int(e['locator'].split('.')[-1])-1]['text'] if e['locator'].startswith('PDF p.') else s['text']
            assert e['quote'] in text and e['role']=='host_incoming'
    guide=json.loads(gzip.decompress(read_bytes(BUNDLE/'host_census_sources/032fde05c3b972dc0c87ee4e.json.gz')))
    assert '2027 Academic Year' in guide['pages'][0]['text']
    assert read_bytes(BUNDLE/'host_census_sources'/guide['local_file']).startswith(b'%PDF')


def test_licensed_images_require_author_license_hash_and_actual_visual_review():
    photos=json.loads((BUNDLE/'campus_asset_manifest.json').read_text())
    assert len(photos)>=264
    assert sum(p.get('acquisition_status')=='reused_baseline_asset' for p in photos)==54
    for photo in photos:
        assert photo['review_status']=='verified_asset' and photo['author'] and photo['license']
        assert photo['license_url'].startswith('https://')
        assert photo['identity_source_url'].startswith(('https://sister.tku.edu.tw/','https://oieie.tku.edu.tw/'))
        path=BUNDLE.parents[1]/photo['local_path'].split('?')[0].removeprefix('/')
        assert hashlib.sha256(path.read_bytes()).hexdigest()==photo['sha256']==photo['visual_review']['sha256']
        assert photo['visual_review']['result']=='pass' and photo['photo_date']
    searches=json.loads((BUNDLE/'commons_campus_index.json').read_text())
    assert len(searches)==287 and any(r.get('http_status')==429 for r in searches)
    assert any(r['status']=='not_requested_after_rate_limit' for r in searches)


def test_offline_full_api_and_non_current_profile(tmp_path,monkeypatch):
    def offline(*args,**kwargs):raise AssertionError('TKU requests must use bundled data')
    monkeypatch.setattr('requests.get',offline)
    client=TestClient(create_app(tmp_path))
    dashboard=client.get('/student-dashboard',params={'school':'TKU'}).json()
    assert len(dashboard['partner_universities'])==287
    assert sum(p['image_status']=='verified' for p in dashboard['partner_universities'])>=264
    assert sum(p['location']['geocode_status']=='verified' for p in dashboard['partner_universities'])>=260
    ritsu=dashboard['partner_universities'][0]
    assert ritsu['image_url'] and ritsu['location']['latitude']==35.032579
    assert ritsu['location']['precision']=='representative'
    assert 'cropped' in ritsu['reference_data']['campus_photo_transformations']
    meiji=next(p for p in dashboard['partner_universities'] if '明治大學' in p['school_name'])
    assert meiji['quota'] is None and meiji['availability_status']=='agreement_only'
    profile=client.get('/destination-profile',params={'school':meiji['school_name'],'home_school':'TKU'}).json()
    assert profile['home_university']=='淡江大學' and 'JPY150,000' in profile['cost_summary']
    assert any(s['key']=='course_schedule' and '尚未定案' in s['summary'] for s in profile['student_guide_sections'])
    assert client.get('/tku/partner-census').json()['institution_denominator']==287
    row=client.get('/tku/partner-census/tku-sister-178').json()
    assert row['fields']['host_nomination_deadline']['public_reference']['source_period_verified']
    assert client.get('/tku/partner-census/not-a-school').status_code==404
    assert client.post('/tku/eligibility-check',json={'partner_id':'meiji'}).status_code==422
    forms=client.get('/application-center/catalog',params={'school':'TKU','target_school':meiji['school_name'],'academic_year':'2027-2028'}).json()
    assert not forms['workflow_found'] and forms['items']==[]


def test_reuse_requires_reviewed_identity_and_campus_scene_not_chinese_name_only():
    reviews={r['id']:r for r in json.loads((BUNDLE/'reused_asset_review.json').read_text())}
    assert len(reviews)==287
    vub=reviews['tku-sister-7']
    assert vub['photo_decision']==vub['coordinate_decision']=='rejected_wrong_institution'
    assert 'Vrije Universiteit Brussel' in vub['rejection_reason'] and 'Université libre de Bruxelles' in vub['rejection_reason']
    assert 'accepted_photo' not in vub and 'accepted_coordinate' not in vub
    assert reviews['tku-sister-260']['photo_decision']=='rejected_not_campus_scene'
    assert 'accepted_photo' not in reviews['tku-sister-260']
    assert 'accepted_coordinate' in reviews['tku-sister-260']
    utar=reviews['tku-sister-163']
    assert 'Sungai Long' in utar['campus_pair_scope'] and 'Kampar' in utar['campus_pair_scope']
    assert utar['accepted_coordinate']['location']['precision']=='representative'
    assert all(r['identity_evidence'] and r['checked_at'] for r in reviews.values())


def test_tku_browser_asset_scope_and_visible_attribution_do_not_use_shared_unlicensed_match():
    script=BUNDLE.parents[1]/'static/tku-campus-assets.js'
    harness="""
    const fs=require('fs'),vm=require('vm');
    const ctx={window:{schoolImageFor:()=>({local_path:'shared.jpg'})},normalize:s=>s.toLowerCase(),state:{dashboard:{school_name:'淡江大學',partner_universities:[
      {school_name:'Campus',country:'日本',image_status:'verified',image_url:'licensed.jpg',image_page_url:'https://commons.wikimedia.org/photo',reference_data:{campus_photo_author:'Author',campus_photo_license:'CC BY-SA 4.0',campus_photo_license_url:'https://creativecommons.org/licenses/by-sa/4.0/',campus_photo_caption:'actual campus'}}
    ]}}};
    vm.createContext(ctx);vm.runInContext(fs.readFileSync(process.argv[1],'utf8'),ctx);
    const image=ctx.window.schoolImageFor('Campus','日本');
    if(image.local_path!=='licensed.jpg'||!image.note.includes('Author')||!image.license_url)throw Error('missing licensed attribution');
    if(ctx.window.schoolImageFor('unknown','日本')!==undefined)throw Error('unreviewed substitution');
    ctx.state.dashboard.school_name='長庚大學';
    if(ctx.window.schoolImageFor('Campus').local_path!=='shared.jpg')throw Error('other home altered');
    """
    subprocess.run(['node','-e',harness,str(script)],check=True,capture_output=True)
