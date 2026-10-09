"""Protect school/track-specific packet stages, old years and unread originals."""
import gzip
import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from exchange_info.api import create_app
from exchange_info.ncu_student_view import fetch_ncu_partner_universities, ncu_field_audit
from exchange_info.ncu_source_coverage import attach_public_field_excerpt

ROOT = Path(__file__).parents[1]
BUNDLE = ROOT / 'src/exchange_info/official_data/ncu'
SOURCES = ROOT / 'sources/ncu/2026-10-08'
CASES = [('ncu-126', '靜岡大學', 8, 7, 13),
         ('ncu-128', '日本中央大學', 7, 8, 18),
         ('ncu-129', '關西大學', 6, 9, 12)]


def source_records():
    return {s['id']: s for s in json.loads(gzip.decompress((BUNDLE / 'source-evidence.json.gz').read_bytes()))}


@pytest.mark.parametrize('row,name,initial,stages,conditions', CASES)
def test_reference_packets_stay_separate_from_home_and_block_current_downloads(tmp_path, row, name, initial, stages, conditions):
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
    assert steps[row + '-host-initial-reference']['submission']['method'] == 'online'
    assert '中央116指定入口' in steps[row + '-host-initial-reference']['submission']['deadline_note']
    assert len([k for k in steps if k.startswith(row + '-host-') and k != row + '-host-apply']) == stages
    assert all(s['deadline_at'] is None and not s['deadline_reminder_eligible'] for k,s in steps.items() if k.startswith(row+'-host-'))
    for admitted, housing in [('unknown', 'unknown'), ('accepted', 'on_campus'), ('accepted', 'off_campus')]:
        response = client.get('/application-center/catalog', params={'school': 'NCU', 'target_school': partner.school_name, 'academic_year': '116', 'host_admission_status': admitted, 'housing_choice': housing})
        assert response.status_code == 200
        rows = [d for d in response.json()['items'] if d['applicability']]
        assert len(rows) == conditions
        assert all(d['applicability']['status'] == 'needs_confirmation' and not d['download_available'] for d in rows)
    if row == 'ncu-128':
        plan = next(d for d in steps[row+'-host-initial-reference']['document_requirements'] if 'C1' in d['name'])
        assert len(plan['source_urls']) == 2
        assert {u.rsplit('/',1)[-1]for u in plan['source_urls']} == {
            'english_admissions_exchange_semester-or-full-year_C1_20260904.docx',
            'english_admissions_exchange_semester-or-full-year_C2_20260904.docx'}
        assert 'Kenkyusei' in json.dumps(steps[row+'-host-conditional-part1'],ensure_ascii=False)
    if row == 'ncu-129':
        assert 'medical information' in json.dumps(steps[row+'-host-initial-reference'],ensure_ascii=False)
        assert not any('成績' in d['name'] for d in steps[row+'-host-initial-reference']['document_requirements'])
        order = list(steps)
        assert order.index(row+'-host-initial-housing') < order.index(row+'-host-apply')
        assert order.index(row+'-host-coe-entry') > order.index(row+'-host-apply')
        policies = json.loads((SOURCES/'document-conditions.json').read_text())
        guarantee = next(p for p in policies if p['rule_id'] == row+'-host-initial-housing')
        assert guarantee['requires_on_campus_housing'] and not guarantee['requires_host_admission']


@pytest.mark.parametrize('row,name,initial,stages,conditions', CASES)
def test_degree_language_contradictions_and_costs_reach_dashboard_detail_and_life(tmp_path, row, name, initial, stages, conditions):
    partner = next(p for p in fetch_ncu_partner_universities() if name in p.school_name)
    audit = ncu_field_audit(partner.school_name)
    assert len(audit['fields']) == 17 and audit['checked_at'].startswith('2026-10-09')
    sources = source_records()
    for key, field in audit['fields'].items():
        assert field['original_evidence'], key
        if not key.startswith('home_'):
            assert field['status'] == 'needs_confirmation'
        if not key.startswith('home_') and key != 'quota':
            assert field['unresolved'], key
        for original in field['original_evidence']:
            assert original['text'] and original['source_url'] and original['checked_at'] and original['applicability']
            if original.get('source_id') in sources:
                assert original['checked_at'] == sources[original['source_id']]['checked_at']
    client = TestClient(create_app(tmp_path))
    shown = next(p for p in client.get('/student-dashboard',params={'school':'NCU'}).json()['partner_universities'] if p['school_name']==partner.school_name)
    summary = json.dumps(shown['student_summary_zh'],ensure_ascii=False)
    profile = client.get('/destination-profile',params={'home_school':'中央','school':partner.school_name})
    assert profile.status_code == 200 and profile.json()['coverage_status']=='official_partial'
    response = client.get('/school-life-context',params={'home_school':'NCU','school':partner.school_name})
    assert response.status_code == 200
    life = json.dumps(response.json(),ensure_ascii=False)
    if row == 'ncu-126':
        for term in ['不是正式申請門檻','10/1','10/14','closed','faculty agreement']:
            assert term in summary, term
        for term in ['27400','23300','2013/1','14日','20日前','80000–100000']:
            assert term in life, term
    elif row == 'ncu-128':
        for term in ['Tentative','N3','Kenkyusei','五門','六列','9/20']:
            assert term in summary, term
        for term in ['350000','1150000','50000','1500','Part2']:
            assert term in life or term in summary, term
    else:
        for term in ['六月','三月','500000','不是','11/10','MCL','不以護照發照日期自動拒收','medical information']:
            assert term in summary or term in life, term
        for term in ['41000','63000','末月','1650','404','all exchange']:
            assert term in life or term in summary, term


def test_unread_worksheets_wrong_200_and_viewer_do_not_count_as_complete_sources():
    sources=source_records()
    for ident,count in [('host-chuo-next-12',9),('host-chuo-next-13',2)]:
        source=sources[ident]
        assert len(source['pages'])==count and not source['reading_review']['sheets_reviewed']
        assert not source['content_status']['all_pages_read']
        assert '未逐門' in source['source_read_scope_note_zh']
    for ident in ['host-shizuoka-housing-current','host-shizuoka-insurance-current']:
        s=sources[ident]
        assert s['status']==200 and s['sha256'] and s['content_status']['response_bytes_received']
        assert not s['content_status']['downloaded'] and not s['content_status']['any_text']
        assert 'English Top' in s['error']
    assert sources['host-kansai-kugf2026-pdf']['status']==404
    first,other=sources['host-kansai-third-2'],sources['host-kansai-third-3']
    assert first['sha256']==other['sha256'] and not first['content_status']['all_pages_read']
    assert '未取得PDF第19頁' in other['source_read_scope_note_zh']


def test_selected_public_passages_visuals_and_version_dates_remain_bound_to_original_bytes():
    sources=source_records()
    for ident,pages in [('host-kansai-next-07',[9]),('host-kansai-next-08',[1,5])]:
        s=sources[ident];ex=json.loads((SOURCES/f'{ident}-public-excerpt.json').read_text())
        assert [p['page']for p in s['pages']]==pages and s['source_excerpt_only']
        assert s['sha256']==ex['source_sha256'] and not s['content_status']['all_pages_read']
        changed={'sha256':'changed','pages':[{'page':1,'text':'new'}]}
        attach_public_field_excerpt(changed,ex)
        assert not changed['pages'] and changed['error']
    assert sources['host-chuo-next-01']['sha256']==sources['host-chuo-next-15']['sha256']
    assert sources['host-chuo-next-01']['visual_review']['pdf_pages_reviewed']==[13,18]
    assert sources['host-chuo-next-08']['visual_review']['pdf_pages_reviewed']==[1]
    manifest=json.loads((ROOT/'docs/ncu-source-evidence/shizuoka-chuo-kansai-original-pages/manifest.json').read_text())
    assert manifest['actual_images_viewed']==len(manifest['images'])==4
    for item in manifest['images']:
        assert item['source_sha256']==sources[item['source_id']]['sha256']
    attempts=json.loads((SOURCES/'host-shizuoka-chuo-kansai-original-manifest-20261009.json').read_text())
    assert len(attempts)==51 and all(a['checked_at'].startswith('2026-10-09')for a in attempts)
    assert all(not sources[a['id']]['content_status']['all_pages_read']for a in attempts)
