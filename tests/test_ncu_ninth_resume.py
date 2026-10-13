"""New readings must preserve original bytes, track/year boundaries and old forms."""
import base64
import gzip
import hashlib
import json
from pathlib import Path
from fastapi.testclient import TestClient
from exchange_info.api import create_app
ROOT=Path(__file__).parents[1]
S=ROOT/'sources/ncu/2026-10-11'
B=ROOT/'src/exchange_info/official_data/ncu'
def evidence():return {x['id']:x for x in json.loads(gzip.decompress((B/'source-evidence.json.gz').read_bytes()))}
def records():return json.loads((S/'reviewed-host-records.json').read_text())

def test_ninth_twenty_pdf_originals_and_selected_visual_pages_are_lossless():
    pack=json.loads(gzip.decompress((S/'resume-ninth-original-responses.json.gz').read_bytes()));e=evidence()
    assert len(pack)==20
    for row in pack:
        r=e[row['source_id']]
        assert hashlib.sha256(base64.b64decode(row['raw_base64'])).hexdigest()==r['sha256']==row['same_as_original_sha256']
        assert r['reading_review']['full_document_read']
        assert r['reading_review']['pages_reviewed']==[p['page'] for p in r['pages']]
        for v in r.get('visual_review',{}).get('rendered_pages',[]):
            assert hashlib.sha256((ROOT/v['artifact']).read_bytes()).hexdigest()==v['render_sha256']
    assert e['ncu-152-follow-8729148c6a']['page_transcriptions'][0]['page']==12
    assert '2021' in e['ncu-152-follow-8729148c6a']['page_transcriptions'][0]['text']
    assert 'within 6 months' in e['ncu-121-resume6-c8e63329ed']['page_transcriptions'][0]['text']


def test_ninth_preserves_kansai_and_shinshu_existing_years_and_every_document_stage():
    new=records();old=json.loads((ROOT/'sources/ncu/2026-10-08/reviewed-host-records.json').read_text())
    for rid in ['ncu-129','ncu-121']:
        assert set(old[rid]['source_ids'])<=set(new[rid]['source_ids'])
        for key,field in old[rid]['fields'].items():
            # Seventeenth review translates the same provisional dates; every datum must survive.
            expected = [p.replace('Fall 2027', '2027秋季').replace('orientation', '迎新') if rid == 'ncu-121' and key == 'study_period' else p for p in field['points']]
            assert set(expected).issubset(new[rid]['fields'][key]['points'])
            assert all(x in new[rid]['fields'][key]['sources'] for x in field['sources'])
    assert new['ncu-129']['host_document_stages']==old['ncu-129']['host_document_stages']
    assert new['ncu-129']['host_documents']==old['ncu-129'].get('host_documents',[])
    assert '2027/4/25' in ' '.join(new['ncu-121']['fields']['host_deadline']['points'])


def test_ninth_language_conflicts_and_course_capacity_keep_exact_scope():
    r=records();lang=' '.join(r['ncu-012']['fields']['language']['points'])
    assert 'B2' in lang and 'p3' in lang and '不能自行選較低門檻' in lang
    courses=' '.join(r['ncu-059']['fields']['courses']['points'])
    assert 'Fully booked只指Blockweek International Management' in courses
    assert 'after semester start' in courses and 'before semester start' in courses
    em=' '.join(r['ncu-009']['fields']['language']['points'])
    assert 'TOEIC785是Grande École Master畢業要求' in em
    assert 'TOEIC790' in em
    assert '開課前兩週' not in ' '.join(r['ncu-009']['fields']['courses']['points'])


def test_ninth_faculty_health_form_and_hub_registration_do_not_become_initial_requirements():
    e=evidence();assert 'Veterinary' in e['ncu-104-p4z-8c0a0c6c6b']['exclusion_reason']
    workflows=[json.loads(x) for x in (B/'application_workflows.jsonl').read_text().splitlines()]
    for w in workflows:
        assert w['review_status']=='pending_review'
        assert not any(s.get('deadline_reminder_eligible') for s in w['steps'] if '-host-' in s['rule_id'])
    uf=next(w for w in workflows if 'University of Florida' in w['school_name'])
    initial=next(s for s in uf['steps'] if s['rule_id']=='ncu-104-host-apply')
    assert not any('Rabies' in d['name'] or 'GatorLink' in d['name'] for d in initial['document_requirements'])
    em=next(w for w in workflows if any(s['rule_id']=='ncu-009-host-apply' for s in w['steps']))
    initial=next(s for s in em['steps'] if s['rule_id']=='ncu-009-host-apply')
    assert len(initial['document_requirements'])==4
    hub=next(s for s in em['steps'] if s['rule_id']=='ncu-009-host-post-offer-hub-enrolment')
    assert '兩週' in hub['summary']


def test_ninth_icp_named_library_point_reaches_api_while_mons_hold_remains(tmp_path):
    d=json.loads((S/'resume-ninth-location-review.json').read_text())['coordinate_decisions'][0]
    raw=json.loads(gzip.decompress((S/'resume-ninth-visual-sourcepack.json.gz').read_bytes()))
    x=next(x for x in raw if x['capture']=='icp-bnf.html')
    assert hashlib.sha256(x['raw_utf8'].encode()).hexdigest()==d['coordinate_receipt']['sha256']
    assert '48.8481246' in x['raw_utf8'] and '2.3295844' in x['raw_utf8'] and '751069905' in x['raw_utf8']
    assert d['record_date']=='2021-12-16' and d['canonical_source_rows']
    ps=TestClient(create_app(tmp_path)).get('/student-dashboard',params={'school':'NCU'}).json()['partner_universities']
    assert len(ps)==214 and sum(p['location']['geocode_status']=='verified' for p in ps)==214
    icp=next(p for p in ps if p['school_name']==d['school_name'])
    assert icp['location']['latitude']==48.8481246 and '2021/12/16' in icp['location']['note']
    assert not d['published_record']['current_exchange_campus_confirmed']
    assert all(p.get('quota') is None and p['availability_status']=='agreement_only' for p in ps)
    mons=next(p for p in ps if 'De Mons' in p['school_name'])
    assert mons['location']['geocode_status']=='verified' and mons['location']['latitude']==50.459072565
