"""Faculty-specific source material must preserve home restrictions and original errors."""
import base64
import gzip
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).parents[1]
DOCS = ROOT / 'docs/data/ncu-completion-20261011/resume/twentieth'


def test_ten_originals_and_all_fourteen_pages_are_traceable():
    ledger = json.loads((DOCS / 'reading-ledger.json').read_text())['items']
    sources = {s['id']: s for s in json.loads(gzip.decompress((ROOT / 'src/exchange_info/official_data/ncu/source-evidence.json.gz').read_bytes()))}
    raw = {s['source_id']: s for s in json.loads(gzip.decompress((ROOT / 'sources/ncu/2026-10-11/resume-twentieth-original-responses.json.gz').read_bytes()))}
    assert len(ledger) == 10 and sum(len(r['pages_reviewed']) for r in ledger) == 14
    assert {r['row_id'] for r in ledger} == {'ncu-025', 'ncu-034', 'ncu-062', 'ncu-079', 'ncu-087'}
    for row in ledger:
        source = sources[row['source_id']]
        assert hashlib.sha256(base64.b64decode(raw[row['source_id']]['body'])).hexdigest() == row['source_sha256'] == source['sha256']
        assert source['content_status']['all_pages_read']
        assert source['content_status']['visual_reviewed_page_count'] == len(source['pages'])
        assert row['pages_reviewed'] == list(range(1, len(source['pages']) + 1))
        assert not row['current_116_approval']
        for render in row['rendered_pages']:
            assert hashlib.sha256((ROOT / render['path']).read_bytes()).hexdigest() == render['sha256']


def test_uspn_initial_learning_agreement_does_not_require_premature_host_signature():
    from exchange_info import storage
    workflows = [w for w in storage.load_bundled_application_workflows() if w.home_university == '國立中央大學']
    w = next(w for w in workflows if w.school_name.startswith('索邦北巴黎'))
    initial = next(s for s in w.steps if s.rule_id == 'ncu-034-host-apply')
    accepted = next(s for s in w.steps if s.rule_id == 'ncu-034-host-accepted-learning-agreement')
    assert len(initial.document_requirements) == 8
    assert not initial.document_requirements[0].signatures
    assert '外校線上簽署在申請完成接受後' in initial.document_requirements[0].name
    assert initial.order < accepted.order and '獲接收後' in accepted.timing
    assert accepted.document_requirements[0].conditional
    assert accepted.document_requirements[0].stage == 'post_offer'
    assert all(w.review_status == 'pending_review' for w in workflows)
    assert not any(s.deadline_reminder_eligible for w in workflows for s in w.steps)


def test_programme_restrictions_overlaps_and_budget_scope_remain_explicit():
    rows = json.loads((ROOT / 'sources/ncu/2026-10-11/reviewed-host-records.json').read_text())
    txt = lambda rid, field: '\n'.join(rows[rid]['fields'][field]['points'])
    assert all(not rows[rid]['host_documents'] for rid in ['ncu-025', 'ncu-062', 'ncu-079', 'ncu-087'])
    assert '國際商務與管理' in txt('ncu-034', 'eligibility')
    assert '不能用一般教師信替代' in txt('ncu-034', 'language')
    assert '前半B1未明列語種' in txt('ncu-034', 'language')
    assert '限理、工、生醫理工及資電學院' in txt('ncu-062', 'eligibility')
    assert '不保證住宿' in txt('ncu-062', 'housing')
    assert '不能再把校方房租380歐元重複加' in txt('ncu-062', 'cost')
    assert 'B為77–88、C為65–77' in txt('ncu-079', 'courses')
    assert 'E及格40–52與F不及格小於51' in txt('ncu-079', 'courses')
    assert '原件有矛盾' in txt('ncu-087', 'arrival')
    assert 'year=2025' in txt('ncu-087', 'courses')
    assert 'B2或C1' in txt('ncu-025', 'language')
    from exchange_info.ncu_student_view import fetch_ncu_partner_universities
    assert all(p.quota is None and p.availability_status == 'agreement_only' for p in fetch_ncu_partner_universities())


def test_two_chinese_cards_keep_the_exact_source(tmp_path):
    from exchange_info.public_translation import cached_translation, standardize_terms
    rows = json.loads((DOCS / 'updated-card-translations.json').read_text())
    assert {r['theme'] for r in rows} == {'academics', 'campus_culture'}
    for row in rows:
        assert cached_translation(row['original'], row['url'], tmp_path) == (standardize_terms(row['zh']), 'translated')
        assert cached_translation(row['zh'], row['url'], tmp_path) == (standardize_terms(row['zh']), 'translated')
