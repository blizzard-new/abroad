"""Five source-confirmed corrections keep historical scope and conditional timing."""
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
RYU_INITIAL = ['證件照（Passport-style ID Photo）', '護照照片頁影像', '正式成績單（Official Transcript）', 'JLPT成績證明（有則附；不是全員必交）']
RYU_HOUSING = ['NASIC入寮日期回覆件（申請校方宿舍者；NASIC另送，原件未取得）', 'NASIC Pledge（申請校方宿舍者；本人簽名，原件未取得）']
RYU_ARRIVAL = ['日本銀行帳戶開戶表（入寮時無日本可用帳戶者；入寮後發，原件未取得）', '在留卡影本（入寮時無日本可用帳戶者的開戶附件）']


def partner(term):
    return next(p for p in fetch_ncu_partner_universities() if term in p.school_name)


def workflow(tmp_path):
    return TestClient(create_app(tmp_path)).get('/application-workflow', params={'home_school': 'NCU', 'school': partner('龍谷').school_name, 'academic_year': '116'}).json()


def test_ryukoku_initial_four_items_are_separate_and_jlpt_is_optional(tmp_path):
    steps = {s['rule_id']: s for s in workflow(tmp_path)['steps']}
    docs = steps['ncu-135-host-initial-reference']['document_requirements']
    assert len(docs) == 10
    assert {d['name'] for d in docs} >= set(RYU_INITIAL)
    assert all(d['needs_confirmation'] for d in docs)
    assert not set(RYU_HOUSING + RYU_ARRIVAL) & {d['name'] for d in docs}
    a = ncu_field_audit(partner('龍谷').school_name)['fields']['host_documents']
    text = a['note']
    for term in ['證件照', '護照照片頁', '正式成績單', 'JLPT', '有則附']:
        assert term in text
    assert '另填照片／個人資訊' not in text


def test_ryukoku_later_conditional_items_keep_stage_and_missing_forms(tmp_path):
    steps = {s['rule_id']: s for s in workflow(tmp_path)['steps']}
    for stage, names in [('housing', RYU_HOUSING), ('arrival', RYU_ARRIVAL)]:
        docs = steps['ncu-135-host-' + stage]['document_requirements']
        assert [d['name'] for d in docs] == names
        assert all(d['needs_confirmation'] and not d.get('official_form_url') for d in docs)
        assert all('#page=13' in d['source_urls'][0] for d in docs)
    pledge = steps['ncu-135-host-housing']['document_requirements'][1]
    assert pledge['signatures'] == ['本人']
    assert steps['ncu-135-host-arrival']['document_requirements'][1]['copy_type'] == 'copy'


def test_kumamoto_nationality_and_language_submission_conditions_are_distinct(tmp_path):
    p = partner('熊本'); a = ncu_field_audit(p.school_name)
    assert '非日本國籍學生' in a['fields']['eligibility']['note']
    text = a['fields']['language']['note']
    assert '非英語母語者須交' in text and '日本語能力N2相當以上' in text
    assert '非日本母語' not in text
    assert '英頁' in text and '日頁' in text
    shown = TestClient(create_app(tmp_path)).get('/student-dashboard', params={'school': 'NCU'}).json()
    shown = next(x for x in shown['partner_universities'] if x['school_name'] == p.school_name)
    summary = json.dumps(shown, ensure_ascii=False)
    assert '非英語母語者須交' in summary and '非日本國籍學生' in summary
    assert '非日本母語' not in summary
    assert p.degree_levels is None


def test_kumamoto_private_insurance_is_historical_one_time_not_annual(tmp_path):
    p = partner('熊本'); a = ncu_field_audit(p.school_name)['fields']['insurance']
    text = a['note']
    assert '一次性付款' in text and '15,000' in text and '2022' in text
    assert '私人保險年額' not in text
    evidence = next(x for x in a['original_evidence'] if x.get('source_id') == 'host-kumamoto-next3-ug-brochure')
    assert evidence['page'] == 8 and 'One-time payment' in evidence['text'] and '一括' in evidence['text']
    life = TestClient(create_app(tmp_path)).get('/school-life-context', params={'home_school': 'NCU', 'school': p.school_name}).json()
    assert '一次性付款' in json.dumps(life, ensure_ascii=False)
    assert a['status'] == 'needs_confirmation'


def test_nufs_study_abroad_cannot_take_gjp_and_no_program_change_is_separate(tmp_path):
    p = partner('名古屋外國語'); a = ncu_field_audit(p.school_name)
    assert '不能修GJP課程' in a['fields']['courses']['note']
    assert '錄取後不能換方案' in a['fields']['eligibility']['note']
    evidence = next(x for x in a['fields']['courses']['original_evidence'] if x.get('source_id') == 'host-nufs-next3-study-abroad')
    assert 'cannot take classes in the Global Japan Program' in evidence['text']
    shown = TestClient(create_app(tmp_path)).get('/student-dashboard', params={'school': 'NCU'}).json()
    shown = next(x for x in shown['partner_universities'] if x['school_name'] == p.school_name)
    assert '不能修GJP課程' in json.dumps(shown['student_summary_zh'], ensure_ascii=False)


@pytest.mark.parametrize('admission,housing', [('unknown', 'unknown'), ('accepted', 'on_campus'), ('accepted', 'off_campus')])
def test_ryukoku_reference_conditions_do_not_unlock_current_forms(tmp_path, admission, housing):
    response = TestClient(create_app(tmp_path)).get('/application-center/catalog', params={'school': 'NCU', 'target_school': partner('龍谷').school_name, 'academic_year': '116', 'host_admission_status': admission, 'housing_choice': housing})
    assert response.status_code == 200
    items = {d['name']: d for d in response.json()['items']}
    for name in RYU_INITIAL + RYU_HOUSING + RYU_ARRIVAL:
        d = items[name]
        assert not d['download_available'] and d['needs_confirmation']
        assert d['applicability']['status'] == 'needs_confirmation'
        assert not d['applicability']['current_applicability_verified']
        assert '116當期' in d['applicability']['note']
    for name in RYU_ARRIVAL:
        assert '無日本可用帳戶' in items[name]['applicability']['note']


def test_new_reference_policies_bind_original_versions_and_explicit_conditions():
    policies = json.loads((BUNDLE / 'document-conditions.json').read_text())
    sources = {s['id']: s for s in json.loads(gzip.decompress((BUNDLE / 'source-evidence.json.gz').read_bytes()))}
    for name in RYU_INITIAL + RYU_HOUSING + RYU_ARRIVAL:
        p = next(p for p in policies if p['requirement_name'] == name)
        assert p['requires_institutional_confirmation'] and not p['current_applicability_verified']
        assert p['requires_host_admission'] == (name not in RYU_INITIAL)
        assert p['requires_on_campus_housing'] == (name not in RYU_INITIAL)
        for v in p['source_versions']:
            assert v['sha256'] == sources[v['source_id']]['sha256']
        if name in RYU_HOUSING + RYU_ARRIVAL:
            assert '第13頁' in p['confirmation_note']


def test_correction_locators_bind_frozen_lines_and_same_pdf_image():
    ledger = json.loads((ROOT / 'sources/ncu/next3-review-20261009/five-corrections-source-ledger.json').read_text())
    sources = {s['id']: s for s in json.loads(gzip.decompress((BUNDLE / 'source-evidence.json.gz').read_bytes()))}
    assert len(ledger) == 7
    for item in ledger:
        assert item['source_sha256'] == sources[item['source_id']]['sha256']
        assert not item['current_116_verified']
        if item.get('original_file'):
            raw = (ROOT / item['original_file']).read_bytes()
            assert hashlib.sha256(raw).hexdigest() == item['native_text_sha256']
            assert '\n'.join(raw.decode().splitlines()[item['line_start']-1:item['line_end']]) == item['verbatim_passage']
        else:
            raw = (ROOT / item['rendered_review_image_path']).read_bytes()
            assert hashlib.sha256(raw).hexdigest() == item['rendered_image_sha256']
            assert item['pdf_page'] == 8 and item['actually_viewed']


def test_ryukoku_preparation_tasks_display_pending_documents_without_active_tool_links(tmp_path):
    response = TestClient(create_app(tmp_path)).post('/application-plan/evaluate', json={'home_school': 'NCU', 'academic_year': '116', 'application_round': '第一梯次', 'preferences': [{'rank': 1, 'school_name': partner('龍谷').school_name}]})
    assert response.status_code == 200
    tasks = response.json()['tasks']
    for title, names, count in [('龍谷初次申請與十項參考文件', RYU_INITIAL, 10), ('龍谷等候交換宿舍另送申請資訊', RYU_HOUSING, 2), ('龍谷到校orientation', RYU_ARRIVAL, 2)]:
        task = next(t for t in tasks if title in t['title'])
        assert task['needs_confirmation'] and task['official_deadline_at'] is None
        assert len(task['document_applicability']) == count
        assert {d['requirement_name'] for d in task['document_applicability']} >= set(names)
        assert all(d['status'] == 'needs_confirmation' for d in task['document_applicability'])
        assert not task['document_link']['requirement_names']
