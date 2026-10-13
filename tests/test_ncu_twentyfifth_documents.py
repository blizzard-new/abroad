"""Official sources must retain source years, word pagination and conditional lists."""
import base64
import gzip
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).parents[1]
DOCS = ROOT / 'docs/data/ncu-completion-20261011/resume/twentyfifth'


def test_eight_sources_and_converted_word_pages_are_traceable():
    ledger = json.loads((DOCS / 'reading-ledger.json').read_text())['items']
    sources = {s['id']: s for s in json.loads(gzip.decompress((ROOT / 'src/exchange_info/official_data/ncu/source-evidence.json.gz').read_bytes()))}
    raw = {s['source_id']: s for s in json.loads(gzip.decompress((ROOT / 'sources/ncu/2026-10-11/resume-twentyfifth-original-responses.json.gz').read_bytes()))}
    assert len(ledger) == 8 and sum(len(r['visual_pages_read']) for r in ledger) == 30
    for row in ledger:
        s = sources[row['source_id']]
        assert hashlib.sha256(base64.b64decode(raw[row['source_id']]['body'])).hexdigest() == s['sha256'] == row['source_sha256']
        assert not row['current_116_approval']
        for render in row['rendered_pages']:
            assert hashlib.sha256((ROOT / render['path']).read_bytes()).hexdigest() == render['sha256']
        if s['format'] == 'html':
            assert not s['content_status']['all_pages_read']
        else:
            assert s['content_status']['all_pages_read']
            assert s['content_status']['visual_reviewed_page_count'] == len(row['visual_pages_read'])
        if s['format'] == 'doc':
            assert s['pages'][0]['page'] is None
            assert not s['visual_review']['pdf_pages_reviewed']
            v = s['visual_review']
            assert hashlib.sha256((ROOT / v['converted_pdf_path']).read_bytes()).hexdigest() == v['converted_pdf_sha256']


def test_direction_and_document_stages_are_preserved():
    from exchange_info import storage
    workflows = [w for w in storage.load_bundled_application_workflows() if w.home_university == '國立中央大學']
    steps = {s.rule_id: s for w in workflows for s in w.steps}
    bingol = steps['ncu-094-host-apply'].document_requirements
    altinbas = steps['ncu-093-host-apply'].document_requirements
    assert len(bingol) == 1 and bingol[0].stage == 'post_offer'
    assert '學習協議' in bingol[0].name
    assert all('25135' not in u and '25128' not in u for d in bingol for u in d.source_urls)
    assert len(altinbas) == 2
    assert {d.stage for d in altinbas} == {'student_application', 'post_offer'}
    assert all(d.needs_confirmation and d.applicability_status == 'reference_only' for d in bingol + altinbas)
    assert all(w.review_status == 'pending_review' for w in workflows)
    assert not any(s.deadline_reminder_eligible for w in workflows for s in w.steps)
    rows = json.loads((ROOT / 'sources/ncu/2026-10-11/reviewed-host-records.json').read_text())
    assert rows['ncu-094']['fields']['host_documents']['gap_only']
    assert rows['ncu-093']['fields']['host_documents']['gap_only']


def test_handbook_version_and_budget_scope_are_retained():
    sources = {s['id']: s for s in json.loads(gzip.decompress((ROOT / 'src/exchange_info/official_data/ncu/source-evidence.json.gz').read_bytes()))}
    new = sources['ncu-093-resume25-altinbas-handbook-2024-link']
    old = sources['ncu-093-resume25-altinbas-handbook']
    assert new['sha256'] != old['sha256']
    assert '20.09.2023' in new['pages'][11]['text']
    assert '13.03.2023' in old['pages'][11]['text']
    assert 'Begining of June' in new['pages'][5]['text']
    rows = json.loads((DOCS / 'added-host-records.json').read_text())
    txt = lambda key: ' '.join(rows['ncu-093']['fields'][key]['points'])
    assert '不是宿舍月租' in txt('cost') and '350歐元' in txt('cost')
    assert '床位有限' in txt('housing') and '不宣稱中央116保證住宿' in txt('housing')
    assert '不能當成中央116名額' in txt('eligibility')
    assert '仍須母校正式英語能力證明信' in txt('language')
