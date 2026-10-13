"""Verify byte identity, page coverage, and scope for five original documents."""
import base64
import gzip
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).parents[1]
DOCS = ROOT / 'docs/data/ncu-completion-20261011/resume/thirtysecond'


def test_originals_are_bound_to_all_twenty_one_reviewed_pages():
    sources = {s['id']: s for s in json.loads(gzip.decompress((ROOT / 'src/exchange_info/official_data/ncu/source-evidence.json.gz').read_bytes()))}
    raw = {s['source_id']: s for s in json.loads(gzip.decompress((ROOT / 'sources/ncu/2026-10-11/resume-thirtysecond-original-responses.json.gz').read_bytes()))}
    ledger = json.loads((DOCS / 'reading-ledger.json').read_text())['items']
    assert len(ledger) == 5 and sum(len(r['pages_reviewed']) for r in ledger) == 21
    for r in ledger:
        s = sources[r['source_id']]
        assert hashlib.sha256(base64.b64decode(raw[s['id']]['body'])).hexdigest() == r['source_sha256'] == s['sha256']
        assert s['content_status']['all_pages_read']
        assert r['pages_reviewed'] == [p['page'] for p in s['pages']]
        assert not r['current_116_approval']
        for p in r['rendered_pages']:
            assert hashlib.sha256((ROOT / p['path']).read_bytes()).hexdigest() == p['sha256']


def test_same_sha_visual_excerpts_preserve_years_and_correct_study_plan_scope():
    sources = {s['id']: s for s in json.loads(gzip.decompress((ROOT / 'src/exchange_info/official_data/ncu/source-evidence.json.gz').read_bytes()))}
    for sid in ['host-ensea-appform', 'host-chuo-next-02', '18V9vNjSgs4HCh9YSLlzmQYs_qXvLn9yK']:
        s = sources[sid]
        assert s['index_review']['source_sha256'] == s['sha256']
        assert s['index_review']['quarantined_pdf_pages']
        assert all('不是中央116' in p['note_zh'] for p in s['visual_review']['page_transcriptions'])
    ensea = sources['host-ensea-appform']['visual_review']
    assert not ensea['include_native_with_selected_passages']
    assert 'For all students:' in ensea['page_transcriptions'][0]['text']
    assert 'Study Plan Form' in ensea['page_transcriptions'][0]['text']
    identities = json.loads((DOCS / 'identity-review.json').read_text())
    manitoba = next(i for i in identities if i['row_id'] == 'ncu-101')
    assert manitoba['country'] == 'Canada' and 'Winnipeg' in manitoba['school']
