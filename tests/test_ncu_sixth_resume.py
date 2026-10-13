"""Exact sources must preserve programme, year and document-stage boundaries."""
import base64
import gzip
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).parents[1]
SOURCE=ROOT/'sources/ncu/2026-10-11'
BUNDLE=ROOT/'src/exchange_info/official_data/ncu'


def test_sixth_raw_responses_and_visual_pages_match_saved_bytes():
    raw=json.loads(gzip.decompress((SOURCE/'resume-sixth-original-responses.json.gz').read_bytes()))
    evidence={r['id']:r for r in json.loads(gzip.decompress((BUNDLE/'source-evidence.json.gz').read_bytes()))}
    assert len(raw)==56
    for r in raw:
        e=evidence[r['source_id']]
        if r['raw_base64']:
            assert hashlib.sha256(base64.b64decode(r['raw_base64'])).hexdigest()==r['receipt']['sha256']==e['sha256']
        for image in e.get('visual_review',{}).get('rendered_pages',[]):
            assert hashlib.sha256((ROOT/image['artifact']).read_bytes()).hexdigest()==image['render_sha256']
    health=evidence['ncu-121-resume6-9a831de302']
    assert len(health['pages'])==15
    assert 'CERTIFICATE OF HEALTH' not in health['pages'][14]['text']
    assert health['visual_review']['pdf_pages_reviewed']==[15]
    assert 'within 6 months' in health['page_transcriptions'][0]['text']
    assert health['reading_status']=='full_native_text_reviewed'
    spring=evidence['ncu-121-resume6-c8e63329ed']
    assert spring['reading_status']=='full_native_text_reviewed'
    assert spring['reading_review']['full_document_read']
    assert spring['visual_review']['pdf_pages_reviewed']==[15]


def test_funded_sdu_calls_do_not_become_ncu_eligibility():
    e={r['id']:r for r in json.loads(gzip.decompress((SOURCE/'host-web-evidence.json.gz').read_bytes()))}
    for key in ['06e4269bb7','40f83142bc']:
        r=e['ncu-098-resume6-'+key]
        assert r['reading_review']['full_document_read']
        assert r['visual_review']['pdf_pages_reviewed']==[3]
        assert '沒有NCU' in r['exclusion_reason']
    all_workflows=[json.loads(l) for l in (BUNDLE/'application_workflows.jsonl').read_text().splitlines()]
    assert all(w['review_status']=='pending_review' for w in all_workflows)
    assert all(not s.get('deadline_reminder_eligible') for w in all_workflows for s in w['steps'] if '-host-' in s['rule_id'])
    partners=[json.loads(l) for l in (BUNDLE/'partners.jsonl').read_text().splitlines()]
    assert len(partners)==214
    assert all(p.get('quota') is None and p['availability_status']=='agreement_only' for p in partners)


def test_shinshu_japanese_and_jasso_conditions_do_not_gate_entire_exchange():
    records=json.loads((SOURCE/'reviewed-host-records.json').read_text());r=records['ncu-121']
    assert '2.3/3.0' not in ' '.join(r['fields']['eligibility']['points'])
    assert '不是全部exchange門檻' in ' '.join(r['fields']['cost']['points'])
    workflows=[json.loads(l) for l in (BUNDLE/'application_workflows.jsonl').read_text().splitlines()]
    w=next(w for w in workflows if 'Shinshu University' in w['school_name'])
    initial=next(s for s in w['steps'] if s['rule_id']=='ncu-121-host-apply')
    docs=initial['document_requirements'];assert len(docs)==9
    japanese=next(d for d in docs if d['name']=='日語能力證明影本')
    assert japanese['conditional'] and '已持有' in japanese['condition']
    jasso=next(d for d in docs if d['name'].startswith('JASSO'))
    assert not jasso.get('conditional') and '不申請也選No' in jasso['name']
    health=next(d for d in docs if d['name'].startswith('Sheet7'))
    assert health['stage']=='student_application' and health['official_form_verified']
    coe=next(s for s in w['steps'] if s['rule_id']=='ncu-121-host-shinshu-coe')
    assert len(coe['document_requirements'])==1 and coe['document_requirements'][0]['stage']=='after_application'


def test_udine_departure_and_utt_arrival_documents_stay_out_of_initial_uploads():
    workflows=[json.loads(l) for l in (BUNDLE/'application_workflows.jsonl').read_text().splitlines()]
    ud=next(w for w in workflows if 'University of Udine' in w['school_name'])
    initial=next(s for s in ud['steps'] if s['rule_id']=='ncu-076-host-apply')
    assert len(initial['document_requirements'])==4
    assert not any('Attendance Certificate' in d['name'] for d in initial['document_requirements'])
    later=next(s for s in ud['steps'] if s['rule_id']=='ncu-076-host-udine-departure')
    assert len(later['document_requirements'])==2 and '離校前' in later['timing']
    utt=next(w for w in workflows if 'University of Technology of Troyes' in w['school_name'])
    first=next(s for s in utt['steps'] if s['rule_id']=='ncu-036-host-apply')
    assert len(first['document_requirements'])==1
    stage=next(s for s in utt['steps'] if s['rule_id']=='ncu-036-host-utt-arrival')
    assert len(stage['document_requirements'])==4
    minor=next(d for d in stage['document_requirements'] if '未成年' in d['name'])
    assert minor['conditional'] and minor['stage']=='post_offer'


def test_older_supplements_preserve_existing_2025_and_2027_readings():
    current=json.loads((SOURCE/'reviewed-host-records.json').read_text())
    original=json.loads((ROOT/'sources/ncu/2026-10-08/reviewed-host-records.json').read_text())
    for rid in ['ncu-119','ncu-121']:
        for key,field in original[rid]['fields'].items():
            # Seventeenth review translates the same provisional dates; every datum must survive.
            expected = [p.replace('Fall 2027', '2027秋季').replace('orientation', '迎新') if rid == 'ncu-121' and key == 'study_period' else p for p in field['points']]
            assert set(expected).issubset(current[rid]['fields'][key]['points'])
            assert all(s in current[rid]['fields'][key]['sources'] for s in field['sources'])
        assert current[rid]['applicability'].startswith(original[rid]['applicability'])
    assert '2027/4/25' in ' '.join(current['ncu-121']['fields']['host_deadline']['points'])
    assert '15,500' in ' '.join(current['ncu-121']['fields']['insurance']['points'])
    assert 'desirable' in ' '.join(current['ncu-119']['fields']['language']['points'])
