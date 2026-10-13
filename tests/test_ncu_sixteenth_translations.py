"""Legacy life cards keep their source, limits, numbers and current-year hold."""
import gzip
import hashlib
import json
import re
from pathlib import Path

from exchange_info.public_translation import cached_translation, standardize_terms

ROOT = Path(__file__).parents[1]
DOCS = ROOT / 'docs/data/ncu-completion-20261011/resume/sixteenth'


def reviewed():
    return json.loads(gzip.decompress((DOCS / 'reviewed-chinese-translations.json.gz').read_bytes()))['items']


def test_all_known_legacy_excerpts_have_source_bound_chinese(tmp_path):
    rows = reviewed()
    assert len(rows) == 517
    assert {r['index'] for r in rows} == set(range(517))
    for row in rows:
        assert hashlib.sha256(row['original'].encode()).hexdigest() == row['original_sha256']
        for url in row['bound_source_urls']:
            assert cached_translation(row['original'], url, tmp_path) == (standardize_terms(row['zh']), 'translated')
        assert re.findall(r'https?://[^\s）)<>；，。]+', row['original']) == re.findall(r'https?://[^\s）)<>；，。]+', row['zh'])
        # Source URL remains an exact part of the lookup identity.
        assert not cached_translation(row['original'], 'https://invalid.example/ncu-unrelated-source', tmp_path) or cached_translation(row['original'], 'https://invalid.example/ncu-unrelated-source', tmp_path)[0] != row['zh']


def test_numeric_editorial_differences_are_individually_explained():
    notes = json.loads((DOCS / 'numeric-review.json').read_text())
    rows = reviewed()
    differences = {str(r['index']) for r in rows if r['numeric_literal_removed'] or r['numeric_literal_added']}
    assert differences == set(notes['items'])
    assert all(len(note) > 15 for note in notes['items'].values())
    for row in rows:
        for pattern in (r'TOEIC\s*\d+', r'IELTS\s*[\d.]+', r'TOEFL\s*(?:iBT\s*)?[\d.]+', r'(?<![A-Za-z])[ABC][12](?![A-Za-z])', r'(?<![A-Za-z])N[1-5](?![A-Za-z])'):
            normalize = lambda value: sorted(set(re.sub(r'\s+', '', token) for token in re.findall(pattern, value)))
            assert normalize(row['original']) == normalize(row['zh']), (row['index'], pattern)


def test_every_original_pending_card_is_localized(tmp_path):
    from exchange_info.life_context import LifeEvidence, _localize_evidence
    pending = json.loads(gzip.decompress((DOCS / 'pending-chinese-cards.json.gz').read_bytes()))['items']
    assert len(pending) == 539
    for item in pending:
        original = LifeEvidence.model_validate(item['evidence'])
        localized = _localize_evidence([original], tmp_path)[0]
        assert localized.translation_status == 'translated', item['school_name']
        assert localized.original_text == original.original_text
        assert localized.scope == original.scope


def test_frontend_recheck_keeps_reviewed_chinese_with_source_identifiers(tmp_path):
    from exchange_info.public_translation import PublicTranslationBatch, translate_public_batch
    bindings = json.loads((DOCS / 'reviewed-display-bindings.json').read_text())['items']
    reviewed_by_index = {row['index']: row for row in reviewed()}
    assert bindings
    for row in bindings:
        reviewed_row = reviewed_by_index[row['reviewed_index']]
        assert row['original'] == row['zh'] == standardize_terms(reviewed_row['zh'])
        assert row['url'] in reviewed_row['bound_source_urls']
        result = translate_public_batch(PublicTranslationBatch(entries=[{'text': row['original'], 'source_url': row['url']}]), tmp_path)['entries'][0]
        assert result['status'] != 'pending'
        assert result['zh'] == row['zh']


def test_program_fee_insurance_and_old_year_qualifications_survive():
    rows = {r['index']: r['zh'] for r in reviewed()}
    for index, terms in {
        18: ['不是116學年度', '兩週後不得更改', '不能把全課必修'],
        33: ['當作116學年度', '僅讀第1–4頁'],
        115: ['並非整個學程額滿', '不能從別頁補值', '保留矛盾'],
        188: ['不在 guard.me 承保範圍', '等待期也須私人保險'],
        213: ['60%', '並非一半', '不含交通'],
        280: ['交換生不可用', '沒有保證早到可入住'],
        322: ['債務保證上限', '不是須先存入', '不保證'],
        499: ['其餘281頁', '尚未逐課核對', '不能稱2027課單已全讀'],
        505: ['原文僅$符號', '幣別仍待確認'],
    }.items():
        for term in terms:
            assert term in rows[index], (index, term)


def test_current_year_review_and_quota_are_not_changed_by_translation():
    from exchange_info.ncu_student_view import fetch_ncu_partner_universities
    partners = fetch_ncu_partner_universities()
    assert len(partners) == 214
    assert all(p.quota is None and p.availability_status == 'agreement_only' for p in partners)
