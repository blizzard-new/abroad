"""Faculty restrictions and physical PDF pages remain traceable after full reading."""
import base64
import gzip
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).parents[1]
DOCS = ROOT / 'docs/data/ncu-completion-20261011/resume/twentysixth'


def test_five_originals_and_ten_physical_pages_are_read():
    ledger = json.loads((DOCS / 'reading-ledger.json').read_text())['items']
    sources = {s['id']: s for s in json.loads(gzip.decompress((ROOT / 'src/exchange_info/official_data/ncu/source-evidence.json.gz').read_bytes()))}
    raw = {s['source_id']: s for s in json.loads(gzip.decompress((ROOT / 'sources/ncu/2026-10-11/resume-twentysixth-original-responses.json.gz').read_bytes()))}
    assert len(ledger) == 5 and sum(len(r['pages_reviewed']) for r in ledger) == 10
    for row in ledger:
        source = sources[row['source_id']]
        assert hashlib.sha256(base64.b64decode(raw[row['source_id']]['body'])).hexdigest() == source['sha256'] == row['source_sha256']
        assert source['content_status']['all_pages_read']
        assert source['content_status']['visual_reviewed_page_count'] == len(source['pages'])
        assert not row['current_116_approval']
        for render in row['rendered_pages']:
            assert hashlib.sha256((ROOT / render['path']).read_bytes()).hexdigest() == render['sha256']


def test_programme_scope_and_new_year_evidence_are_distinct():
    rows = json.loads((DOCS / 'added-host-records.json').read_text())
    txt = lambda rid, field: ' '.join(rows[rid]['fields'][field]['points'])
    assert '不能跨學程混選' in txt('ncu-060', 'courses')
    assert '新版考試及補考全部待確認' in txt('ncu-060', 'study_period')
    assert '不是中央116' in txt('ncu-060', 'host_deadline')
    assert '年度雜支' in txt('ncu-022', 'cost')
    assert 'Level 2春季已開放' in txt('ncu-022', 'study_period')
    assert '不能當成中央雙邊交換必繳學費' in txt('ncu-086', 'tuition')
    assert '最低B2' in txt('ncu-086', 'language') and 'B1–B2' in txt('ncu-086', 'language')
    assert '不把房租重複加到生活總額' in txt('ncu-081', 'cost')
    assert '2027/8/15–10/1' in txt('ncu-081', 'host_deadline')
    assert '不自動校正PDF提名年' in txt('ncu-081', 'host_deadline')


def test_verified_partial_and_universal_document_rules():
    from exchange_info import storage
    workflows = [w for w in storage.load_bundled_application_workflows() if w.home_university == '國立中央大學']
    steps = {s.rule_id: s for w in workflows for s in w.steps}
    monaco = steps['ncu-060-host-apply'].document_requirements
    hanze = steps['ncu-065-host-apply'].document_requirements
    rennes = steps['ncu-022-host-apply'].document_requirements
    assert len(monaco) == 8 and not any(d.conditional for d in monaco)
    assert any('B2' in d.name and '正式證明信' in d.name for d in monaco)
    assert len(hanze) == 1 and hanze[0].stage == 'post_offer'
    assert len(rennes) == 8 and sum(d.conditional for d in rennes) == 1
    assert not any('動機信' in d.name for d in rennes)
    assert all(d.needs_confirmation and d.applicability_status == 'reference_only' for d in monaco + hanze + rennes)
    assert all(w.review_status == 'pending_review' for w in workflows)
    assert not any(s.deadline_reminder_eligible for w in workflows for s in w.steps)
