"""Regression cases from the independent NTU data audit, including scope safety."""
import gzip
import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from exchange_info.api import create_app
from exchange_info.application_documents import all_application_templates, build_packet_manifest
from exchange_info.models import ApplicationPacketRequest
from exchange_info.ntu_student_view import fetch_ntu_partner_universities
from test_application_documents_api import _authenticated_client

ROOT = Path(__file__).parents[1]
BUNDLE = ROOT / 'src/exchange_info/official_data/ntu'


def packet(group='中語組', international='否', **language):
    return ApplicationPacketRequest.model_validate({
        'context': {'school_name': '國立臺灣大學'},
        'answers': {'exchange-application-data': {'language_group': group,
            'international_degree_student': international, **language}},
        'selections': [{'template_id': 'exchange-application-data'}],
    })


def test_all_288_summaries_reach_dashboard_and_keep_source_text(tmp_path):
    partners = fetch_ntu_partner_universities()
    dashboard = TestClient(create_app(tmp_path)).get('/student-dashboard', params={'school': 'NTU'}).json()
    assert len(dashboard['partner_universities']) == 289
    for raw, payload in zip(partners, dashboard['partner_universities']):
        summary = payload['student_summary_zh']
        for key in ('eligibility_points', 'application_steps', 'tuition_points'):
            assert summary[key] and '116-1' in summary[key][0]
            assert raw.source_url in '\n'.join(summary[key])
        if raw.eligibility:
            assert '本校' in '\n'.join(summary['eligibility_points'])
        else:
            assert '尚未取得資格文字' in '\n'.join(summary['eligibility_points'])
        assert summary['translated_from_english'] is False
    # Existing accurate portal extraction must survive the supplemental review.
    snapshot=json.loads(gzip.decompress((ROOT/'sources/ntu/2026-10-08-import.json.gz').read_bytes()))
    old=[json.loads(line)['partner'] for line in snapshot['files']['verification/partners-116-1-updated-candidates.jsonl'].splitlines()]
    # A later dated portal batch changes only its verified reference text.
    changes=json.loads((ROOT/'sources/ntu/2026-10-10-official-changes.json').read_text())
    by_url={row['official_url']:row for row in changes['schools']}
    for row in old:
        if row['source_url'] in by_url:
            row['eligibility']=by_url[row['source_url']]['sections_by_heading']['申請資格']['text']
    current=json.loads((ROOT/'sources/ntu/2026-10-14-official-update.json').read_text())
    uw_url=f"https://oia.ntu.edu.tw/outgoing/view/semester/1/sn/{current['uw_update']['portal_id']}"
    for row in old:
        if row['source_url']==uw_url:
            row['eligibility']=current['uw_update']['portal_eligibility_after']
    for np in current.get('new_partners',[]):
        old.append({'school_name':np['school_name'],'country':np['country'],'eligibility':np['eligibility_text'],'tuition_info':np['tuition_text']})
    assert [(p.school_name,p.country,p.eligibility,p.tuition_info) for p in partners] == [
        (p['school_name'],p['country'],p['eligibility'],p['tuition_info']) for p in old]
    assert sum(p.quota is None for p in partners) == 262
    assert sum(p.quota == '0 名' for p in partners) == 7


def test_deadline_conflict_keeps_two_sources_without_confirmed_reminder(tmp_path):
    ledger = json.loads((BUNDLE / 'verification_status.json').read_text())
    field = next(x for x in ledger if x['portal_id']=='107')['fields']['deadlines']
    assert field['status']=='conflict'
    value = field['reviewed_partial_value']
    assert {x['date'] for x in value['deadline_candidates']} == {'2027-03-05','2027-03-06'}
    assert len({x['source_url'] for x in value['deadline_candidates']}) == 2
    assert value['confirmed_deadline_at'] is None and not value['reminder_eligible']
    partner = next(p for p in fetch_ntu_partner_universities() if p.school_name=='筑波大學')
    assert all(s in '\n'.join(partner.student_summary_zh.application_steps) for s in ['2027/3/5','2027/3/6','conflict'])
    client=TestClient(create_app(tmp_path))
    deadlines=client.get('/deadlines',params={'school':'NTU'}).json()
    assert '2027-03-05' not in str(deadlines) and '2027-03-06' not in str(deadlines)
    workflow=next(json.loads(x) for x in (BUNDLE/'application_workflows.jsonl').read_text().splitlines() if json.loads(x)['school_name']=='筑波大學')
    assert workflow['review_status']=='pending_review' and workflow.get('published_at') is None
    assert all(not s.get('reminder_eligible',False) for s in workflow['steps'])


def test_helsinki_closure_is_limited_to_medicine_2027_28():
    entry=next(x for x in json.loads((BUNDLE/'verification_status.json').read_text()) if x['portal_id']=='62')
    field=entry['fields']['courses']['reviewed_partial_value']
    assert field['academic_year']=='2027-2028' and field['affected_programme']=='Medicine'
    assert field['activity']=='exchange_course_offer'
    assert field['unaffected_by_notice']==['Psychology','Translational Medicine','research traineeships']
    partner=next(p for p in fetch_ntu_partner_universities() if p.school_name=='赫爾辛基大學')
    text='\n'.join(partner.student_summary_zh.application_steps)
    assert '2027–2028' in text and '並非全校停開' in text


@pytest.mark.parametrize('group,international,required',[
    ('中語組','否',False),('中語組','是',True),('一般組','否',True),('日語組','否',True),
    ('德語組','否',True),('法語組','否',True),('韓語組','否',True),('西語組','否',True)])
def test_language_fields_required_by_group_and_identity(group,international,required):
    item=build_packet_manifest(packet(group,international)).items[0]
    fields={f.field_id:f for f in item.preview_fields}
    assert all(fields[k].required is required for k in ['language_test','language_score','language_result_date'])
    assert fields['language_planned_result_date'].required is False


@pytest.mark.parametrize('group,international,test,error',[
 ('一般組','否','GEPT',False),('一般組','否','BESTEP',False),
 ('一般組','否','TOEIC',True),('一般組','否','Duolingo',True),
 ('日語組','否','JLPT',False),('日語組','否','IELTS Academic',True),
 ('中語組','是','TOCFL',False),('中語組','是','HSK',False),('中語組','是','JLPT',True)])
def test_host_or_other_school_tests_cannot_replace_ntu_group_proof(group,international,test,error):
    item=build_packet_manifest(packet(group,international,language_test=test,language_score='B2',language_result_date='2026-06-01')).items[0]
    field=next(f for f in item.preview_fields if f.field_id=='language_test')
    assert bool(field.validation_error) is error


@pytest.mark.parametrize('actual,planned,error',[
 ('2025-04-30','2026-11-01',True),('2025-05-01','',False),
 ('2099-01-01','',True),('not-a-date','',True),('', '2026-11-01',False)])
def test_planned_result_does_not_substitute_for_actual_valid_exam_date(actual,planned,error):
    item=build_packet_manifest(packet('一般組',language_test='GEPT',language_score='中高級',
        language_result_date=actual,language_planned_result_date=planned)).items[0]
    date=next(f for f in item.preview_fields if f.field_id=='language_result_date')
    assert bool(date.validation_error) is error
    if not actual:
        assert date.is_blank and date.label in item.missing_required_fields


def test_ntu_manifest_api_accepts_chinese_exemption_and_enforces_international_exception(tmp_path):
    client=_authenticated_client(tmp_path,home_school='國立臺灣大學')
    templates=client.get('/application-center/templates',params={'school':'NTU'}).json()
    form=next(t for t in templates if t['id']=='exchange-application-data')
    test=next(f for f in form['fields'] if f['id']=='language_test')
    assert {'GEPT','BESTEP','TOCFL','HSK','JLPT'} <= set(test['options'])
    for international,expected in [('否',False),('是',True)]:
        response=client.post('/application-center/manifest',json=packet(international=international).model_dump(mode='json'))
        assert response.status_code==200
        field=next(f for f in response.json()['items'][0]['preview_fields'] if f['field_id']=='language_test')
        assert field['required'] is expected
    info=client.get('/exchange-info',params={'school':'NTU'}).json()
    rules=info['language_requirement']
    assert any(s.startswith('日語組：') and 'JLPT' in s for s in rules)
    assert any(s.startswith('中語組：') and '國際學位生' in s and 'TOCFL' in s and 'HSK' in s for s in rules)
    assert all('：' in s for s in rules)


def test_documents_supplement_has_read_content_and_truthful_cycle_scope():
    ledger={x['portal_id']:x for x in json.loads((BUNDLE/'verification_status.json').read_text())}
    for id,word in [('1306','兩封推薦信'),('38','Certificate of Health'),('115','Tentative Learning Agreement')]:
        field=ledger[id]['fields']['documents']
        assert word in field['reviewed_partial_value']['value'] and field['source_urls']
        assert field['remaining_questions'] and not ledger[id]['full_116_1_information_confirmed']
    assert ledger['38']['fields']['documents']['reviewed_partial_value']['source_academic_year']=='2027-2028'
    assert ledger['1306']['fields']['documents']['reviewed_partial_value']['source_academic_year'] is None
    assert ledger['115']['fields']['documents']['reviewed_partial_value']['source_academic_year'] is None
    completeness=json.loads((BUNDLE/'catalog-completeness.json').read_text())
    assert completeness['fully_verified_current_cycle_count']==0
    assert completeness['documents_status_counts']['not_confirmed_no_text_evidence']==180
    assert '不等於官方未公告' in completeness['missing_information_note']


def test_uncg_preserves_both_year_and_visa_scope_without_confirming_future_plan():
    entry=next(x for x in json.loads((BUNDLE/'verification_status.json').read_text()) if x['portal_id']=='1202')
    field=entry['fields']['insurance_visa']['reviewed_partial_value']
    assert field['visa_plan_reference']=={'F-1':'Student Blue','J-1':'Global Solutions'}
    assert field['confirmed_2027_28_j1_plan'] is None
    text=field['value']
    assert all(x in text for x in ['2027/28','2026/27','USD1616','waiver','尚待確認'])
    destination=next(json.loads(x) for x in (BUNDLE/'destination_profiles.jsonl').read_text().splitlines() if json.loads(x)['school_name']==entry['school_name'])
    assert '並非已確認的2027/28 J-1保費' in destination['cost_summary']


def test_hope_deadlines_identity_exceptions_and_repayment_are_visible_in_api(tmp_path):
    source=json.loads((BUNDLE/'scholarships.json').read_text())
    rules=source['cancellation_rules']
    general=next(r for r in rules if r['identity']=='一般學生')
    assert '經濟不利' in general['exception'] and '第二階段' in general['trigger']
    assert {r['repay_within_months_after_termination'] for r in source['repayment_rules']}=={2,3}
    assert source['acceptance_contract_deadline']=='2026-12-29T16:00:00+08:00'
    assert source['supplementary_deadline_time'] is None
    dashboard=TestClient(create_app(tmp_path)).get('/student-dashboard',params={'school':'NTU'}).json()
    text=str(dashboard['scholarship_info'])
    assert all(x in text for x in ['2026-12-29','一般學生','經濟不利','三個月','兩個月','2027年10月'])


@pytest.mark.parametrize('school',['長庚大學','國立臺北大學'])
def test_existing_document_templates_keep_language_fields_and_no_ntu_conditions(school):
    template=next(t for t in all_application_templates(school) if t.id=='exchange-application-data')
    fields={f.id:f for f in template.fields}
    assert 'TOEIC' in fields['language_test'].options
    assert all(fields[k].required for k in ['language_test','language_score','language_result_date'])
    assert not fields['language_test'].required_when and not fields['language_test'].options_by_field
    assert 'language_group' not in fields
