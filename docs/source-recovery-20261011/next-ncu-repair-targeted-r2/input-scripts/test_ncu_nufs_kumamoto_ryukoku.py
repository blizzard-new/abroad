"""Keep three reference packets, conditional alternatives and current-year gaps visible."""
import gzip
import hashlib
import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from exchange_info.api import create_app
from exchange_info.ncu_student_view import fetch_ncu_partner_universities, ncu_field_audit

ROOT = Path(__file__).parents[1]
BUNDLE = ROOT / 'src/exchange_info/official_data/ncu'
CASES = [('ncu-130', '名古屋外國語大學', 13, 8),
         ('ncu-134', '熊本大學', 4, 7),
         ('ncu-135', '龍谷大學', 14, 9)]


def sources():
    return {s['id']: s for s in json.loads(gzip.decompress((BUNDLE/'source-evidence.json.gz').read_bytes()))}


@pytest.mark.parametrize('row,name,documents,stages', CASES)
@pytest.mark.parametrize('admission,housing', [('unknown','unknown'), ('accepted','on_campus'), ('accepted','off_campus')])
def test_home_host_coe_visa_tickets_arrival_and_conditional_downloads(tmp_path,row,name,documents,stages,admission,housing):
    partner = next(p for p in fetch_ncu_partner_universities() if name in p.school_name)
    assert partner.quota is None and partner.availability_status == 'agreement_only'
    assert partner.degree_levels is None and partner.colleges is None
    client=TestClient(create_app(tmp_path))
    response=client.get('/application-workflow',params={'home_school':'NCU','school':partner.school_name,'academic_year':'116'})
    assert response.status_code == 200
    workflow=response.json();steps={s['rule_id']:s for s in workflow['steps']}
    assert workflow['review_status']=='pending_review' and workflow['published_at'] is None
    assert len(steps['ncu-116-1-home-3']['document_requirements'])==7
    assert not steps[row+'-host-apply']['document_requirements']
    host=[s for k,s in steps.items() if k.startswith(row+'-host-')]
    assert len(host)==stages+1 and all(not s['deadline_reminder_eligible'] and s['deadline_at'] is None for s in host)
    coe,visa,tickets,arrival=[steps[row+'-host-'+s]for s in ['coe','visa','tickets','arrival']]
    assert coe['order']<visa['order']<tickets['order']<arrival['order']
    assert len({s['phase']for s in [coe,visa,tickets,arrival]})==4
    assert all(s['checked_at'].startswith('2026-10-09')for s in host)
    response=client.get('/application-center/catalog',params={'school':'NCU','target_school':partner.school_name,'academic_year':'116','host_admission_status':admission,'housing_choice':housing})
    assert response.status_code==200
    conditional=[d for d in response.json()['items'] if d['applicability']]
    assert len(conditional)==documents
    for d in conditional:
        assert d['applicability']['status']=='needs_confirmation'
        assert not d['applicability']['current_applicability_verified'] and not d['download_available']
        assert '116當期' in d['applicability']['note']
    if row=='ncu-134':
        assert len(coe['document_requirements'])==4
        assert not steps[row+'-host-officer-packet']['document_requirements']
        assert '未取得' in steps[row+'-host-officer-packet']['summary']
    else:
        assert len(steps[row+'-host-initial-reference']['document_requirements'])==(10 if row=='ncu-135' else documents)
    if row=='ncu-130':
        note=' '.join(d['applicability']['note']for d in conditional)
        for term in ['擇一','父母帳戶','有病況','無則不用','不是所有文件三月內','印尼','線上']:
            assert term in note or term in str(steps[row+'-host-initial-reference']),term
    elif row=='ncu-135':
        health=next(d for d in conditional if '健康表' in d['name'])
        assert '不能Xray可其他結核檢查' in health['name']
        assert '正式結果' in health['name']
    other=client.get('/application-workflow',params={'home_school':'NCU','school':partner.school_name,'academic_year':'115'})
    assert other.status_code==200
    assert other.json()['applicability_status']=='needs_confirmation' and not other.json()['steps']


@pytest.mark.parametrize('row,name,documents,stages', CASES)
def test_full_field_originals_student_summary_and_life_preserve_scope(tmp_path,row,name,documents,stages):
    partner=next(p for p in fetch_ncu_partner_universities()if name in p.school_name)
    a=ncu_field_audit(partner.school_name);by=sources()
    assert len(a['fields'])==17 and a['checked_at'].startswith('2026-10-09')
    for key,field in a['fields'].items():
        assert field['original_evidence'],key
        if not key.startswith('home_'):
            assert field['status']=='needs_confirmation'
            if key!='quota':assert field['unresolved']
        for e in field['original_evidence']:
            assert e['source_url'] and e['text'] and e['checked_at'] and e['applicability']
            if e.get('source_id')in by:assert e['checked_at']==by[e['source_id']]['checked_at']
    client=TestClient(create_app(tmp_path))
    dashboard=client.get('/student-dashboard',params={'school':'NCU'}).json()
    shown=next(p for p in dashboard['partner_universities']if p['school_name']==partner.school_name)
    summary=json.dumps(shown['student_summary_zh'],ensure_ascii=False)
    response=client.get('/school-life-context',params={'home_school':'NCU','school':partner.school_name})
    assert response.status_code==200;life=json.dumps(response.json(),ensure_ascii=False)
    terms={'ncu-130':['GJP','N2','N1','2026/10/31','不是所有文件三月內'],
           'ncu-134':['packet','三年級','594,600','平台加總','非原文總額'],
           'ncu-135':['建議','300','N4','正式結果','JEP','tentative']}
    for term in terms[row]:assert term in summary or term in life or term in json.dumps(a,ensure_ascii=False),term
    living={'ncu-130':['3.5萬','6,600','NHI','80%'],
            'ncu-134':['plan','9–16','7/17','403','一月'],
            'ncu-135':['1,960','1,980','5日與7日','1,500–2,000']}
    for term in living[row]:assert term in life or term in summary,term


def test_frozen_download_packet_is_immutable_and_new_reading_is_sha_bound():
    by=sources();ledger=json.loads((ROOT/'sources/ncu/next3-review-20261009/reading-ledger.json').read_text())
    assert len(ledger)==75 and sum(s['reading_review']['full_document_read']for s in ledger)==73
    for entry in ledger:
        s=by[entry['source_id']]
        assert not s['current_116_applicability_verified']
        assert s['reading_review']['source_sha256']==s['sha256']
        assert s['content_status']['all_pages_read']==entry['reading_review']['full_document_read']
        for p in s['pages']:
            original=(ROOT/p['text_path']).read_bytes()
            assert hashlib.sha256(original).hexdigest()==p['text_sha256']
            assert original.decode()==p['text']
    frozen=list((ROOT/'sources/ncu/candidates/2026-10-09').glob('ncu-*/sources/*/metadata.json'))
    assert len(frozen)==56
    assert all(not json.loads(p.read_text())['full_document_read']for p in frozen)
    viewed=json.loads((ROOT/'sources/ncu/next3-review-20261009/actual-visual-review.json').read_text())
    assert len(viewed)==104 and all(x['actually_viewed']for x in viewed)
    assert by['host-kumamoto-next3-isa-address']['status']==403
    assert '入口' in by['host-ryukoku-next3-syllabus-index']['error']


def test_visual_original_passages_do_not_invent_grade_scope_or_budget_total():
    by=sources();s=by['host-kumamoto-next3-ug-brochure']
    text={p['page']:p['text']for p in s['page_transcriptions']}
    assert 'full-time 3rd year' in text[4] and 'and above' not in text[4]
    assert 'Total' not in text[8] and '106,000' not in text[8]
    assert '¥30,000 Dormitory & Utilities' in text[8]
    assert s['visual_review']['pdf_pages_reviewed']==list(range(1,13))
    assert by['host-ryukoku-next3-recommendation']['index_review']['quarantined_pdf_pages']==[1]
