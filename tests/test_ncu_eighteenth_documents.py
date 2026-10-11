"""Full EM Normandie sources preserve conflicting scopes and annual holds."""
import base64
import gzip
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).parents[1]
DOCS = ROOT / 'docs/data/ncu-completion-20261011/resume/eighteenth'


def test_full_sources_match_all_original_bytes_and_visual_pages():
    ledger = json.loads((DOCS / 'reading-ledger.json').read_text())['items']
    sources = {s['id']: s for s in json.loads(gzip.decompress((ROOT / 'src/exchange_info/official_data/ncu/source-evidence.json.gz').read_bytes()))}
    raw = {s['source_id']: s for s in json.loads(gzip.decompress((ROOT / 'sources/ncu/2026-10-11/resume-eighteenth-original-responses.json.gz').read_bytes()))}
    assert sorted(len(r['pages_reviewed']) for r in ledger) == [17, 51]
    for row in ledger:
        source = sources[row['source_id']]
        assert hashlib.sha256(base64.b64decode(raw[row['source_id']]['body'])).hexdigest() == row['source_sha256'] == source['sha256']
        assert source['content_status']['all_pages_read']
        assert source['content_status']['visual_reviewed_page_count'] == len(source['pages'])
        assert row['pages_reviewed'] == list(range(1, len(source['pages']) + 1))
        assert not row['current_116_approval']
        for render in row['rendered_pages']:
            assert hashlib.sha256((ROOT / render['path']).read_bytes()).hexdigest() == render['sha256']


def test_course_seasons_internal_errors_and_degree_scope_do_not_become_eligibility():
    row = json.loads((ROOT / 'sources/ncu/2026-10-11/reviewed-host-records.json').read_text())['ncu-009']
    text = lambda field: '\n'.join(row['fields'][field]['points'])
    assert 'Dubai U3與M1僅春季、BBA4僅秋季' in text('courses')
    assert 'Dublin U2僅春、U3僅秋' in text('courses')
    assert '地緣情勢' in text('courses')
    assert 'FX失敗寫成7<12' in text('courses')
    assert '第2頁說國際校區不提供，第8頁Dubai U3春季卻列5ECTS' in text('courses')
    assert '不能把60／180已修學分與60修讀中自動當作全部' in text('eligibility')
    assert 'Paris M2財務數據管理秋春皆標短期' in text('study_period')
    assert '其餘47頁仍待讀' not in row['fields']['courses']['unresolved']
    assert len(row['host_documents']) == 4  # Full review adds no invented mandatory initial documents.
    assert '6000AED' in text('visa') and '4500AED' in text('visa')
    from exchange_info.ncu_student_view import fetch_ncu_partner_universities
    partners = fetch_ncu_partner_universities()
    assert len(partners) == 214
    assert all(p.quota is None and p.availability_status == 'agreement_only' for p in partners)


def test_updated_chinese_cards_keep_exact_source_boundaries(tmp_path):
    from exchange_info.public_translation import cached_translation, standardize_terms
    rows = json.loads((DOCS / 'updated-card-translations.json').read_text())
    assert {r['theme'] for r in rows} == {'cost', 'academics', 'social', 'safety'}
    for row in rows:
        assert cached_translation(row['original'], row['url'], tmp_path) == (standardize_terms(row['zh']), 'translated')
        assert cached_translation(row['zh'], row['url'], tmp_path) == (standardize_terms(row['zh']), 'translated')
    courses = next(r['zh'] for r in rows if r['theme'] == 'academics')
    assert '杜拜U3與M1僅春季、BBA4僅秋季' in courses
    assert '7<12' in courses and '10<12' in courses
    assert '雙聯' in courses and '15 ECTS' in courses
