"""Keep KUINS, Komazawa and Tohoku reference packets distinct and pending."""
import copy
import gzip
import hashlib
import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from exchange_info.api import create_app
from exchange_info.ncu_source_coverage import attach_public_field_excerpt
from exchange_info.ncu_student_view import fetch_ncu_partner_universities, ncu_field_audit

ROOT = Path(__file__).parents[1]
BUNDLE = ROOT / 'src/exchange_info/official_data/ncu'
SOURCES = ROOT / 'sources/ncu/2026-10-08'
CASES = [
    ('ncu-118', '關西國際大學', 'initial-reference', 11, 7, 13),
    ('ncu-119', '駒澤大學', 'initial-reference', 8, 7, 9),
    ('ncu-122', '東北大學', 'initial-support', 3, 16, 20),
]


def evidence():
    return {s['id']: s for s in json.loads(gzip.decompress((BUNDLE / 'source-evidence.json.gz').read_bytes()))}


def test_tohoku_coe_passport_repeat_upload_and_unconditional_jasso_exclusion(tmp_path):
    partner = next(p for p in fetch_ncu_partner_universities() if '東北大學' in p.school_name)
    audit = ncu_field_audit(partner.school_name)
    originals = audit['fields']['visa']['original_evidence']
    assert any(o['source_id'] == 'host-tohoku-attachment-1' and o['page'] == 6 and 'passport (PDF)' in o['text'] for o in originals)
    assert any(o['source_id'] == 'host-tohoku-attachment-1' and o['page'] == 10 and 'NOT acceptable' in o['text'] for o in originals)
    assert any(o['source_id'] == 'host-tohoku-attachment-2' and o['page'] == 1 and 'Proceeding' in o['text'] for o in originals)
    assert any(o['source_id'] == 'host-tohoku-attachment-2' and o['page'] == 2 and 'DO NOT' in o['text'] for o in originals)
    assert '核定與否皆禁用' in audit['fields']['visa']['note']
    assert 'JASSO未核定不當financial證明' not in audit['fields']['visa']['note']
    assert '>200萬不另income proof' in audit['fields']['visa']['note']
    client = TestClient(create_app(tmp_path))
    workflow = client.get('/application-workflow', params={'home_school': 'NCU', 'school': partner.school_name, 'academic_year': '116'}).json()
    steps = {s['rule_id']: s for s in workflow['steps']}
    assert len(steps['ncu-122-host-initial-support']['document_requirements']) == 3
    coe = steps['ncu-122-host-coe-financial']
    assert coe['phase'] == '校方COE通知後（可早於正式錄取）'
    assert '收到校方正式COE通知後' in coe['summary']
    policies = json.loads((SOURCES / 'document-conditions.json').read_text())
    coe_policies = [p for p in policies if p['rule_id'] == coe['rule_id']]
    assert len(coe_policies) == 4
    assert all(not p['requires_host_admission'] and p['requires_institutional_confirmation']
               and not p['current_applicability_verified'] for p in coe_policies)
    assert len(coe['document_requirements']) == 4
    passport = next(d for d in coe['document_requirements'] if '再次上傳護照PDF' in d['name'])
    assert 'Proceeding' in passport['name'] and '有ID card／舊護照時' in passport['name']
    assert passport['needs_confirmation'] and passport['official_form_url'] is None
    assert not coe['deadline_reminder_eligible'] and workflow['review_status'] == 'pending_review'
    dashboard = client.get('/student-dashboard', params={'school': 'NCU'}).json()
    shown = next(p for p in dashboard['partner_universities'] if p['school_name'] == partner.school_name)
    summary = json.dumps(shown['student_summary_zh'], ensure_ascii=False)
    assert '再次上傳護照PDF' in summary and '核定與否皆禁用' in summary
    life = client.get('/school-life-context', params={'home_school': 'NCU', 'school': partner.school_name})
    assert 'JASSO獎學金證明一律不接受' in json.dumps(life.json(), ensure_ascii=False)
    for admission in ['unknown', 'not_accepted', 'accepted']:
        catalog = client.get('/application-center/catalog', params={'school': 'NCU', 'target_school': partner.school_name, 'academic_year': '116', 'host_admission_status': admission}).json()
        document = next(d for d in catalog['items'] if d['name'] == passport['name'])
        assert document['applicability']['status'] == 'needs_confirmation' and not document['download_available']
        assert '收到校方正式COE通知後' in document['applicability']['note']


@pytest.mark.parametrize('row,name,initial,count,stage_count,conditional_count', CASES)
def test_japan3_pending_packets_have_separate_home_initial_and_later_documents(
    tmp_path, row, name, initial, count, stage_count, conditional_count,
):
    partner = next(p for p in fetch_ncu_partner_universities() if name in p.school_name)
    assert partner.quota is None and partner.availability_status == 'agreement_only'
    client = TestClient(create_app(tmp_path))
    response = client.get('/application-workflow', params={
        'home_school': 'NCU', 'school': partner.school_name, 'academic_year': '116',
    })
    assert response.status_code == 200
    workflow = response.json()
    assert workflow['review_status'] == 'pending_review' and workflow['published_at'] is None
    steps = {s['rule_id']: s for s in workflow['steps']}
    assert len(steps['ncu-116-1-home-3']['document_requirements']) == 7
    assert steps[row + '-host-apply']['document_requirements'] == []
    assert len(steps[row + '-host-' + initial]['document_requirements']) == count
    assert len([s for key, s in steps.items() if key.startswith(row + '-host-') and key != row + '-host-apply']) == stage_count
    assert all(not s['deadline_reminder_eligible'] for s in steps.values())
    for admission, housing in [('unknown', 'unknown'), ('accepted', 'on_campus'), ('accepted', 'off_campus')]:
        result = client.get('/application-center/catalog', params={
            'school': 'NCU', 'target_school': partner.school_name, 'academic_year': '116',
            'host_admission_status': admission, 'housing_choice': housing,
        })
        assert result.status_code == 200
        conditional = [i for i in result.json()['items'] if i['applicability']]
        assert len(conditional) == conditional_count
        assert all(i['applicability']['status'] != 'applicable' and not i['download_available'] for i in conditional)
        if row == 'ncu-118' and housing == 'off_campus':
            dorm = next(i for i in conditional if '當期指定宿舍資料' in i['name'])
            assert dorm['applicability']['status'] == 'needs_confirmation'
    if row == 'ncu-118':
        documents = steps[row + '-host-' + initial]['document_requirements']
        assert 'if any' in documents[-2]['name'] and 'if applicable' in documents[-1]['name']
        assert any(d['copies'] == 6 and '30×40mm' in d['name'] for d in documents)
        assert all(d['official_form_url'] is None for d in documents)
    elif row == 'ncu-119':
        assert steps[row + '-host-' + initial]['submission']['method'] == 'email'
        assert '母校email全部件' in steps[row + '-host-' + initial]['responsible_party']
        assert all(d['copies'] is None for d in steps[row + '-host-' + initial]['document_requirements'])
        assert any('700000' in d['name'] for d in steps[row + '-host-' + initial]['document_requirements'])
    else:
        assert len(steps[row + '-host-colabs-consent']['document_requirements']) == 4
        assert len(steps[row + '-host-coe-financial']['document_requirements']) == 4
        assert '內諾不是錄取' in steps[row + '-host-colabs-consent']['summary']
        assert 'IPLA排除' in steps[row + '-host-research-pledge-jcd']['summary']
        assert '只有JASSO' in steps[row + '-host-bank-if-jasso']['title']
        assert '公開存取碼' not in steps[row + '-host-bank-if-jasso']['summary']


@pytest.mark.parametrize('row,name,initial,count,stage_count,conditional_count', CASES)
def test_japan3_reference_restrictions_reach_dashboard_life_and_field_sources(
    tmp_path, row, name, initial, count, stage_count, conditional_count,
):
    partner = next(p for p in fetch_ncu_partner_universities() if name in p.school_name)
    audit = ncu_field_audit(partner.school_name)
    assert len(audit['fields']) == 17
    for key, field in audit['fields'].items():
        assert field['original_evidence']
        if key.startswith('home_'):
            assert field['status'] == 'available' and field['unresolved'] is None
        elif key == 'quota':
            assert field['status'] == 'needs_confirmation' and '2026/10/12' in field['note']
        else:
            assert field['unresolved']
        for source in field['original_evidence']:
            assert source['source_url'].startswith(('http://', 'https://')) and source['text']
            assert source['checked_at'] and source['applicability']
    client = TestClient(create_app(tmp_path))
    shown = next(p for p in client.get('/student-dashboard', params={'school': 'NCU'}).json()['partner_universities'] if p['school_name'] == partner.school_name)
    summary = json.dumps(shown['student_summary_zh'], ensure_ascii=False)
    life = client.get('/school-life-context', params={'home_school': 'NCU', 'school': partner.school_name})
    assert life.status_code == 200
    life_text = json.dumps(life.json(), ensure_ascii=False)
    if row == 'ncu-118':
        for text in ['N2或同等能力', 'N3或同等能力', 'JLPT證明if any', '反向套', '四校區']:
            assert text in summary
        assert 'April' in summary and '116' in summary
        assert '30000–47000' in life_text and '所得申報' in life_text
    elif row == 'ncu-119':
        for text in ['desirable', '未到N2仍可申請', '研究所地理與經營管理是全年', '不提供Grad']:
            assert text in summary
        for component in ('room5000', 'room10000', 'utilities30000', 'utilities20000', 'deposit30000'):
            assert component in life_text
    else:
        for text in ['GPA2.30／3是獎學金', '臺灣列NTU／CCU／NYCU而未列NCU', '不硬拒博士', 'M1／M2', 'Level1–4']:
            assert text in summary
        for text in ['38500', '10280', 'I沒有rescue', 'Category B', '只有JASSO', '學位學費調整']:
            assert text in life_text
    destination = client.get('/destination-profile', params={'home_school': 'NCU', 'school': partner.school_name}).json()
    assert destination['home_university'] == '國立中央大學'
    assert destination['coverage_status'] == 'official_partial'
    for section in destination['student_guide_sections']:
        if section['key'] in audit['fields']:
            keys = ['tuition', 'cost'] if section['key'] == 'cost' else (
                ['courses', 'study_period'] if section['key'] == 'courses' else [section['key']]
            )
            expected = list(dict.fromkeys(url for key in keys for url in audit['fields'][key]['source_urls']))
            assert section['source_urls'] == expected


@pytest.mark.parametrize('alias', ['NCU', '中央', 'National Central University'])
def test_japan3_shared_host_destination_alias_uses_ncu_packet_not_other_home(tmp_path, alias):
    partner = next(p for p in fetch_ncu_partner_universities() if '東北大學' in p.school_name)
    client = TestClient(create_app(tmp_path))
    result = client.get('/destination-profile', params={'home_school': alias, 'school': partner.school_name})
    assert result.status_code == 200
    profile = result.json()
    assert profile['home_university'] == '國立中央大學' and profile['coverage_status'] == 'official_partial'
    assert '38500' in profile['housing_summary'] and '學位學費調整' in profile['cost_summary']
    assert '116' in profile['coverage_note']


def test_japan3_life_keeps_known_points_with_caveats_and_skips_unread_extraction(monkeypatch):
    from exchange_info.life_context import _profile_evidence
    from exchange_info.models import DestinationProfile
    from exchange_info import ncu_student_view
    row = next(json.loads(line) for line in (BUNDLE / 'destination_profiles.jsonl').read_text().splitlines()
               if json.loads(line)['school_name'].startswith('駒澤大學'))
    profile = DestinationProfile.model_validate(row)
    social = next(r for r in _profile_evidence(profile) if r.theme == 'social')
    assert '尚未取得116包' in social.text and 'orientation' in social.text
    assert social.scope and '2025' in social.scope
    sources = next(s.source_urls for s in profile.student_guide_sections if s.key == 'arrival')
    assert [s.url for s in social.sources] == sources
    original = ncu_student_view.ncu_field_audit(profile.school_name)
    unread = copy.deepcopy(original)
    for source in unread['read_sources']:
        source['status'] = 'extracted_not_cycle_approved'
    monkeypatch.setattr(ncu_student_view, 'ncu_field_audit', lambda school: unread)
    assert _profile_evidence(profile) == []


def test_japan3_visual_native_and_selected_read_scopes_are_not_download_counts():
    sources = evidence()
    brochure = sources['13TdQ1U2b_ZrDuvPl876SKV0UpL8KWn9R']
    assert brochure['reading_review']['pages_reviewed'] == [2, 3, 4, 5]
    assert brochure['visual_review']['pdf_pages_reviewed'] == [1, 3, 4]
    assert brochure['content_status']['all_pages_read']
    assert '無適用年度' in brochure['reading_review']['scope']
    for ident, pages, visual in [('host-tohoku-attachment-19', [3], [4]), ('host-tohoku-attachment-20', [], [3, 4])]:
        source = sources[ident]
        assert source['content_status']['page_count'] == 10 and not source['content_status']['all_pages_read']
        assert source['reading_review']['pages_reviewed'] == pages
        assert source['visual_review']['pdf_pages_reviewed'] == visual
        assert '未讀' in source['reading_review']['scope'] or '未人工讀' in source['reading_review']['scope']
    arrival = sources['host-tohoku-attachment-23']
    assert arrival['content_status']['page_count'] == 57 and not arrival['content_status']['all_pages_read']
    assert arrival['reading_review']['pages_reviewed'] == []
    assert '仍可繼續公開查核' in arrival['reading_review']['scope']
    general = sources['host-tohoku-attachment-24']
    assert general['content_status']['page_count'] == 15 and not general['content_status']['all_pages_read']
    assert general['reading_review']['selected_passages_reviewed']
    assert general['visual_review']['pdf_pages_reviewed'] == [13, 14]
    assert '日文字型破損' in general['reading_review']['scope']
    assert not sources['host-kuins-international']['content_status']['all_pages_read']
    assert '63800' in sources['host-kuins-international']['reading_review']['scope']


def test_japan3_format_failures_retries_and_discontinued_publication_keep_original_history():
    sources = evidence()
    for suffix in ['26', '27']:
        old = sources['host-tohoku-attachment-' + suffix]
        recovered = sources['host-tohoku-attachment-' + suffix + '-html-response']
        assert old['status'] == 200 and old['error'] and not old['content_status']['downloaded']
        assert recovered['status'] == 200 and recovered['content_status']['all_pages_read']
        assert '停止出版' in recovered['reading_review']['scope']
    assert sources['host-tohoku-colabs-curriculum']['error']
    assert sources['host-tohoku-colabs-curriculum-retry']['content_status']['all_pages_read']
    assert sources['host-tohoku-attachment-25']['status'] == 503
    first = sources['host-komazawa-foreign-students2026']
    recheck = sources['host-komazawa-foreign-students2026-recheck']
    assert first['status'] == recheck['status'] == 200
    assert first['sha256'] == recheck['sha256']
    assert first['content_status']['all_pages_read'] and recheck['content_status']['all_pages_read']


@pytest.mark.parametrize('ident', [
    'host-tohoku-attachment-11', 'host-tohoku-attachment-22',
    'host-tohoku-ipla-course-information2026fall',
])
def test_japan3_public_excerpt_is_sha_bound_and_cannot_restore_omitted_access_or_example_fields(ident):
    source = evidence()[ident]
    excerpt = json.loads((SOURCES / (ident + '-public-excerpt.json')).read_text())
    assert source['source_excerpt_only'] and not source['content_status']['all_pages_have_text']
    assert source['sha256'] == excerpt['source_sha256'] == source['public_copy_redaction']['original_source_sha256']
    assert source['pages'] == excerpt['public_pages'] and source['privacy_note']
    raw = copy.deepcopy(source)
    raw['pages'] = [{'page': 1, 'text': 'an unreviewed newly downloaded original'}]
    attach_public_field_excerpt(raw, excerpt)
    assert raw['pages'] == excerpt['public_pages']
    changed = copy.deepcopy(source)
    changed['sha256'] = 'changed-original'
    attach_public_field_excerpt(changed, excerpt)
    assert changed['pages'] == [] and '原件已變更' in changed['error']
    specs = json.loads((SOURCES / 'host-web-checks.json').read_text())
    assert next(s for s in specs if s['id'] == ident)['requires_public_field_excerpt']


def test_japan3_viewed_original_images_have_matching_source_and_image_hashes():
    directory = ROOT / 'docs/ncu-source-evidence/japan3-original-pages'
    manifest = json.loads((directory / 'manifest.json').read_text())
    sources = evidence()
    assert len(manifest['images']) == 20
    for row in manifest['images']:
        source = sources[row['source_id']]
        assert row['original_source_url'] == source['url']
        assert row['original_source_sha256'] == source['sha256']
        assert row['image_sha256'] == hashlib.sha256((directory / row['image']).read_bytes()).hexdigest()
        assert row['pdf_page'] in source['visual_review']['pdf_pages_reviewed']
