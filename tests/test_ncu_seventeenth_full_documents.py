"""New full-document claims retain exact bytes, page coverage and annual limits."""
import base64
import gzip
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).parents[1]
DOCS = ROOT / 'docs/data/ncu-completion-20261011/resume/seventeenth'


def test_six_full_reviews_match_original_responses_and_every_rendered_page():
    ledger = json.loads((DOCS / 'reading-ledger.json').read_text())['items']
    assert len(ledger) == 6
    sources = {r['id']: r for r in json.loads(gzip.decompress((ROOT / 'src/exchange_info/official_data/ncu/source-evidence.json.gz').read_bytes()))}
    responses = {r['source_id']: r for r in json.loads(gzip.decompress((ROOT / 'sources/ncu/2026-10-11/resume-seventeenth-original-responses.json.gz').read_bytes()))}
    for row in ledger:
        source = sources[row['source_id']]
        raw = base64.b64decode(responses[row['source_id']]['body'])
        assert raw.startswith(b'%PDF')
        assert hashlib.sha256(raw).hexdigest() == row['source_sha256'] == source['sha256']
        assert {p['page'] for p in source['pages']} == {1, 2}
        assert source['content_status']['all_pages_read']
        assert source['content_status']['visual_reviewed_page_count'] == 2
        assert source['reading_review']['full_document_read']
        assert not row['current_116_approval']
        for render in row['rendered_pages']:
            assert hashlib.sha256((ROOT / render['path']).read_bytes()).hexdigest() == render['sha256']


def test_contradictions_and_office_scope_are_explicit_without_promoting_quotas():
    rows = json.loads((ROOT / 'sources/ncu/2026-10-11/reviewed-host-records.json').read_text())
    joined = lambda rid, field: '\n'.join(rows[rid]['fields'][field]['points'])
    assert '65–59' in joined('ncu-150', 'courses')
    assert '不自行修正' in joined('ncu-150', 'courses')
    assert '行政辦公地址' in joined('ncu-150', 'city')
    assert '不是全部院系授課校區' in joined('ncu-028', 'city')
    assert '原件抵達日' in joined('ncu-152', 'host_documents')
    assert '不將自評問題當作自動錄取排除' in joined('ncu-152', 'host_documents')
    assert '依學生需求才寄母校' in joined('ncu-121', 'study_period')
    assert '不能把舊學年方案表當2027–28' in joined('ncu-018', 'courses')
    from exchange_info.ncu_student_view import fetch_ncu_partner_universities
    partners = fetch_ncu_partner_universities()
    assert len(partners) == 214
    assert all(p.quota is None and p.availability_status == 'agreement_only' for p in partners)


def test_updated_cards_keep_their_chinese_and_original_source(tmp_path):
    from exchange_info.public_translation import cached_translation, standardize_terms
    rows = json.loads((DOCS / 'updated-card-translations.json').read_text())
    assert len(rows) == 3
    for row in rows:
        assert cached_translation(row['original'], row['url'], tmp_path) == (standardize_terms(row['zh']), 'translated')
        assert cached_translation(row['zh'], row['url'], tmp_path) == (standardize_terms(row['zh']), 'translated')
