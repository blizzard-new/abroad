"""Official sources must retain source years, word pagination and conditional lists."""
import base64
import gzip
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).parents[1]
DOCS = ROOT / 'docs/data/ncu-completion-20261011/resume/twentyfourth'


def test_eight_sources_and_converted_word_pages_are_traceable():
    ledger = json.loads((DOCS / 'reading-ledger.json').read_text())['items']
    sources = {s['id']: s for s in json.loads(gzip.decompress((ROOT / 'src/exchange_info/official_data/ncu/source-evidence.json.gz').read_bytes()))}
    raw = {s['source_id']: s for s in json.loads(gzip.decompress((ROOT / 'sources/ncu/2026-10-11/resume-twentyfourth-original-responses.json.gz').read_bytes()))}
    assert len(ledger) == 8 and sum(len(r['visual_pages_read']) for r in ledger) == 19
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
        if s['format'] == 'docx':
            assert s['pages'][0]['page'] is None
            assert not s['visual_review']['pdf_pages_reviewed']
            v = s['visual_review']
            assert hashlib.sha256((ROOT / v['converted_pdf_path']).read_bytes()).hexdigest() == v['converted_pdf_sha256']


def test_budget_periods_and_old_templates_are_not_promoted():
    rows = json.loads((ROOT / 'sources/ncu/2026-10-11/reviewed-host-records.json').read_text())
    txt = lambda rid, field: '\n'.join(rows[rid]['fields'][field]['points'])
    assert '原表未寫計價週期' in txt('ncu-060', 'housing')
    assert '相當30 ECTS' in txt('ncu-060', 'courses')
    assert '部分晚於一般學期末' in txt('ncu-060', 'study_period')
    assert '不是已投保保單' in txt('ncu-060', 'host_documents')
    assert '原表特別註明待確認' in txt('ncu-060', 'tuition')
    assert '表內仍印2022/23' in txt('ncu-061', 'host_documents')
    assert '不能把十一個月三人房150歐元套到三個月交換' in txt('ncu-061', 'housing')
    assert '2026/9/28至2027/1/30' in txt('ncu-061', 'study_period')
    assert rows['ncu-061']['fields']['language']['gap_only']
    assert '空白自評欄' in txt('ncu-061', 'language')


def test_initial_documents_preserve_versions_and_conditions():
    from exchange_info import storage
    workflows = [w for w in storage.load_bundled_application_workflows() if w.home_university == '國立中央大學']
    steps = {s.rule_id: s for w in workflows for s in w.steps}
    monaco = steps['ncu-060-host-apply'].document_requirements
    buem = steps['ncu-061-host-apply'].document_requirements
    assert len(monaco) == 8 and len(buem) == 6
    original = json.loads((DOCS / 'added-host-records.json').read_text())
    assert sum(bool(d.get('conditional')) for d in original['ncu-060']['host_documents']) == 1
    # Batch 26's 2026-27 original requires B2 evidence for all, with alternative formats.
    assert not any(d.conditional for d in monaco)
    assert sum(d.conditional for d in buem) == 2
    assert all('2022/23' in d.condition for d in buem if d.conditional)
    assert all(d.stage == 'student_application' for d in monaco + buem)
    assert not any('交換後' in d.name or '已錄取' in d.name for d in buem)
    assert all(d.needs_confirmation and d.applicability_status == 'reference_only' for d in monaco + buem)
    assert all(w.review_status == 'pending_review' for w in workflows)
    assert not any(s.deadline_reminder_eligible for w in workflows for s in w.steps)
