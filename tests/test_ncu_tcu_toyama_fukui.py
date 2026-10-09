"""Keep the three partners' reference years, packet stages and source limits visible."""
import gzip
import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from exchange_info.api import create_app
from exchange_info.ncu_student_view import fetch_ncu_partner_universities, ncu_field_audit
from exchange_info.ncu_source_coverage import attach_public_field_excerpt, source_content_status

ROOT = Path(__file__).parents[1]
BUNDLE = ROOT / 'src/exchange_info/official_data/ncu'
SOURCES = ROOT / 'sources/ncu/2026-10-08'
CASES = [('ncu-123', '東京都市大學', 11, 7, 13),
         ('ncu-124', '富山大學', 10, 6, 12),
         ('ncu-125', '福井大學', 9, 9, 10)]


def source_records():
    return {s['id']: s for s in json.loads(gzip.decompress((BUNDLE / 'source-evidence.json.gz').read_bytes()))}


@pytest.mark.parametrize('row,name,initial,stages,conditions', CASES)
def test_next3_home_host_and_coe_stages_remain_separate_and_pending(tmp_path, row, name, initial, stages, conditions):
    partner = next(p for p in fetch_ncu_partner_universities() if name in p.school_name)
    assert partner.quota is None and partner.availability_status == 'agreement_only'
    client = TestClient(create_app(tmp_path))
    response = client.get('/application-workflow', params={'home_school': 'NCU', 'school': partner.school_name, 'academic_year': '116'})
    assert response.status_code == 200
    workflow = response.json()
    assert workflow['review_status'] == 'pending_review' and workflow['published_at'] is None
    steps = {s['rule_id']: s for s in workflow['steps']}
    assert len(steps['ncu-116-1-home-3']['document_requirements']) == 7
    assert steps[row + '-host-apply']['document_requirements'] == []
    assert len(steps[row + '-host-initial-reference']['document_requirements']) == initial
    assert len([s for k, s in steps.items() if k.startswith(row + '-host-') and k != row + '-host-apply']) == stages
    assert all(not s['deadline_reminder_eligible'] for s in steps.values())
    for admitted, housing in [('unknown', 'unknown'), ('accepted', 'on_campus'), ('accepted', 'off_campus')]:
        response = client.get('/application-center/catalog', params={'school': 'NCU', 'target_school': partner.school_name, 'academic_year': '116', 'host_admission_status': admitted, 'housing_choice': housing})
        assert response.status_code == 200
        rows = [d for d in response.json()['items'] if d['applicability']]
        assert len(rows) == conditions
        assert all(d['applicability']['status'] == 'needs_confirmation' and not d['download_available'] for d in rows)
    policies = json.loads((SOURCES / 'document-conditions.json').read_text())
    selected = [p for p in policies if p['rule_id'].startswith(row + '-host-')]
    assert len(selected) == conditions
    assert all(p['requires_institutional_confirmation'] and not p['current_applicability_verified'] for p in selected)
    if row in ('ncu-124', 'ncu-125'):
        coe = next(p for p in selected if 'COE' in p['requirement_name'])
        assert coe['rule_id'].endswith('-initial-reference') and not coe['requires_host_admission']
    if row == 'ncu-125':
        nomination = steps[row + '-host-officer-nomination']
        assert '非學生自行送件' in nomination['responsible_party']
        health = next(d for d in steps[row + '-host-initial-reference']['document_requirements'] if 'Form3' in d['name'])
        assert 'certification前6月內' in health['name']
        assert health['official_form_url'].endswith('/Application_form-3.zip')


@pytest.mark.parametrize('row,name,initial,stages,conditions', CASES)
def test_next3_degree_language_year_contradictions_and_budget_reach_student_views(tmp_path, row, name, initial, stages, conditions):
    partner = next(p for p in fetch_ncu_partner_universities() if name in p.school_name)
    audit = ncu_field_audit(partner.school_name)
    assert len(audit['fields']) == 17
    for key, field in audit['fields'].items():
        assert field['original_evidence'], key
        if not key.startswith('home_'):
            assert field['status'] == 'needs_confirmation'
            if key != 'quota':
                assert field['unresolved']
        for original in field['original_evidence']:
            assert original['source_url'] and original['text'] and original['checked_at'] and original['applicability']
    client = TestClient(create_app(tmp_path))
    dashboard = client.get('/student-dashboard', params={'school': 'NCU'}).json()
    shown = next(p for p in dashboard['partner_universities'] if p['school_name'] == partner.school_name)
    summary = json.dumps(shown['student_summary_zh'], ensure_ascii=False)
    profile = client.get('/destination-profile', params={'home_school': '中央', 'school': partner.school_name}).json()
    assert profile['home_university'] == '國立中央大學' and profile['coverage_status'] == 'official_partial'
    life = client.get('/school-life-context', params={'home_school': 'NCU', 'school': partner.school_name})
    assert life.status_code == 200
    life_text = json.dumps(life.json(), ensure_ascii=False)
    if row == 'ncu-123':
        for term in ['master', '本科', 'N2／N1', '116', '禁止打工']:
            assert term in summary
        assert 'no excess' in life_text and '家屬' in life_text
    elif row == 'ncu-124':
        for term in ['AY2024Fall', 'up to2', 'JLPT', '10／11', '2/15']:
            assert term in summary
        for term in ['19900', '19050', '不可退', '1340', '不給學分', '2026']:
            assert term in life_text
        assert shown['quota'] is None
    else:
        for term in ['入學GPA至少2.30／3', 'JASSO', '不硬判所有A', 'JPT525', 'CEFR B1', '600000／1100000']:
            assert term in summary
        for term in ['17600', '20400', '19400', '22700', '自付3割', '6000', '二選一', '116']:
            assert term in life_text
        assert '80000' in life_text and '不保證' in life_text


def test_selected_native_html_does_not_claim_whole_document_read():
    original = {'status': 200, 'sha256': 'same-original', 'pages': [{'page': None, 'text': 'Section A; Section B'}],
                'reading_review': {'source_sha256': 'same-original', 'pages_reviewed': [None], 'full_document_read': False, 'note_zh': 'Only Section A was read.'}}
    assert source_content_status(original)['any_text']
    assert source_content_status(original)['downloaded']
    assert not source_content_status(original)['all_pages_read']
    sources = source_records()
    for ident in ['host-kuins-international', 'host-tohoku-attachment-23', 'government-fukui-city-nhi-benefits202608', 'host-fukui-forms2027spring-zip']:
        assert not sources[ident]['content_status']['all_pages_read'], ident


def test_current_forms_are_one_archive_with_four_sha_bound_members_and_reference_scope():
    sources = source_records()
    forms = sources['host-fukui-forms2027spring-zip']
    review = json.loads((SOURCES / 'host-fukui-forms2027spring-members-review.json').read_text())
    assert forms['sha256'] == review['sha256']
    assert len(forms['archive_members']) == len(forms['pages']) == len(review['reviewed_members']) == 4
    assert all(p['page'] is None and p['archive_member'] and p['member_sha256'] for p in forms['pages'])
    assert all(p['native_text_read'] and not p['visual_read'] for p in review['reviewed_members'])
    text = '\n'.join(p['text'] for p in forms['pages'])
    assert '6  months  prior  to  the  certification' in text
    # Word splits the year digits across native text runs. Keep the original
    # excerpt untouched and compare only this certificate's stated periods.
    certificate = next(p for p in forms['pages'] if 'Form4' in p['archive_member'])
    compact = ''.join(certificate['text'].split())
    assert 'cannotgraduateinorbeforeSeptember2027' in compact
    assert 'cannotgraduateinorbeforeMarch2028' in compact
    assert 'Form1' not in '\n'.join(p['archive_member'] for p in forms['pages'])
    assert not forms['content_status']['all_pages_read']


def test_nomination_public_excerpt_omits_submission_identifier_and_rejects_changed_bytes():
    sources = source_records()
    source = sources['host-fukui-nomination2027spring']
    excerpt = json.loads((SOURCES / (source['id'] + '-public-excerpt.json')).read_text())
    text = json.dumps(source['pages'], ensure_ascii=False)
    assert 'ufdeli.cii.u-fukui.ac.jp' not in text
    assert source['sha256'] == excerpt['source_sha256'] and '存取識別值' in text
    original = {'sha256': 'changed-original', 'pages': [{'page': None, 'text': 'new body'}]}
    attach_public_field_excerpt(original, excerpt)
    assert original['pages'] == [] and 'error' in original


def test_visual_values_and_current_handbook_year_are_preserved_as_source_evidence():
    sources = source_records()
    manifest = json.loads((ROOT / 'docs/ncu-source-evidence/tcu-toyama-fukui-original-pages/manifest.json').read_text())
    assert manifest['actual_images_viewed'] == len(manifest['images']) == 7
    assert sources['host-fukui-dormitory-information-en']['visual_review']['pdf_pages_reviewed'] == [1, 2]
    assert sources['host-fukui-dormitory-guide-ja']['visual_review']['pdf_pages_reviewed'] == [1, 2]
    assert sources['host-fukui-catalog2027spring']['visual_review']['pdf_pages_reviewed'] == [19]
    toyama = sources['1OArbu2MdlYVuBbzi2RGCp7opEGwJNstH']
    assert toyama['visual_review']['pdf_pages_reviewed'] == [2]
    assert 'AY 2024 Fall' in toyama['pages'][1]['text']
    handbook = sources['host-fukui-life-handbook2024']
    assert 'Academic Calendar 2026' in handbook['pages'][2]['text']
    assert '2024' in handbook['url'] and '全文年份' not in handbook['source_read_scope_note_zh']
    assert not handbook['content_status']['all_pages_read']
    city = sources['government-fukui-city-nhi-benefits202608']
    assert city['authority_kind'] == 'government'
    assert '2026年8月1日' in city['pages'][0]['text'] and '自己負担割合' in city['pages'][0]['text']
