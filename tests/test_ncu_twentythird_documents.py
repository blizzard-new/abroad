"""Faculty restrictions and physical PDF pages remain traceable after full reading."""
import base64
import gzip
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).parents[1]
DOCS = ROOT / 'docs/data/ncu-completion-20261011/resume/twentythird'


def test_five_originals_and_seven_physical_pages_are_read():
    ledger = json.loads((DOCS / 'reading-ledger.json').read_text())['items']
    sources = {s['id']: s for s in json.loads(gzip.decompress((ROOT / 'src/exchange_info/official_data/ncu/source-evidence.json.gz').read_bytes()))}
    raw = {s['source_id']: s for s in json.loads(gzip.decompress((ROOT / 'sources/ncu/2026-10-11/resume-twentythird-original-responses.json.gz').read_bytes()))}
    assert len(ledger) == 5 and sum(len(r['pages_reviewed']) for r in ledger) == 7
    for row in ledger:
        source = sources[row['source_id']]
        assert hashlib.sha256(base64.b64decode(raw[row['source_id']]['body'])).hexdigest() == source['sha256'] == row['source_sha256']
        assert source['content_status']['all_pages_read']
        assert source['content_status']['visual_reviewed_page_count'] == len(source['pages'])
        assert not row['current_116_approval']
        for render in row['rendered_pages']:
            assert hashlib.sha256((ROOT / render['path']).read_bytes()).hexdigest() == render['sha256']


def test_mixed_identity_and_language_conflicts_are_not_silently_resolved():
    rows = json.loads((ROOT / 'sources/ncu/2026-10-11/reviewed-host-records.json').read_text())
    txt = lambda rid, field: '\n'.join(rows[rid]['fields'][field]['points'])
    assert all(rows['ncu-061']['fields'][k]['gap_only'] for k in ['eligibility', 'language', 'study_period'])
    assert '不能據此變更既有BUEM照片與座標' in txt('ncu-061', 'city')
    assert '不能宣稱所有學生免語言證明' in txt('ncu-202', 'language')
    assert 'IELST 4.0' in txt('ncu-202', 'language')
    assert '不是每間房4至6人' in txt('ncu-202', 'housing')
    assert '每月200萬' in txt('ncu-202', 'cost') and '每學期500萬' in txt('ncu-202', 'cost')
    assert '仍須各授課教師同意' in txt('ncu-202', 'courses')
    assert all(rows['ncu-094']['fields'][k]['gap_only'] for k in ['study_period', 'host_documents', 'host_deadline', 'housing', 'cost'])


def test_hkbp_eight_attachment_categories_keep_conditions_and_two_photos():
    from exchange_info import storage
    workflows = [w for w in storage.load_bundled_application_workflows() if w.home_university == '國立中央大學']
    steps = {s.rule_id: s for w in workflows for s in w.steps}
    docs = steps['ncu-202-host-apply'].document_requirements
    assert len(docs) == 8
    language = next(d for d in docs if '英語能力' in d.name)
    assert language.conditional and '存在衝突' in language.condition
    assert any('兩封推薦信' in d.name for d in docs)
    assert sum('彩色護照照片' in d.name for d in docs) == 1
    assert any('其中一張貼申請表' in d.name for d in docs)
    assert all(d.needs_confirmation and d.applicability_status == 'reference_only' for d in docs)
    assert all(w.review_status == 'pending_review' for w in workflows)
    assert not any(s.deadline_reminder_eligible for w in workflows for s in w.steps)
