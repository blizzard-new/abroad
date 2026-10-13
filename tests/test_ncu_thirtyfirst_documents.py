"""Campus directories and empty sheets retain their original reference scope."""
import base64
import gzip
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).parents[1]
DOCS = ROOT / 'docs/data/ncu-completion-20261011/resume/thirtyfirst'


def test_five_originals_and_thirteen_physical_pdf_pages_are_traceable():
    ss = {s['id']: s for s in json.loads(gzip.decompress((ROOT / 'src/exchange_info/official_data/ncu/source-evidence.json.gz').read_bytes()))}
    raw = {s['source_id']: s for s in json.loads(gzip.decompress((ROOT / 'sources/ncu/2026-10-11/resume-thirtyfirst-original-responses.json.gz').read_bytes()))}
    ledger = json.loads((DOCS / 'reading-ledger.json').read_text())['items']
    assert len(ledger) == 5 and sum(len(r['pages_reviewed']) for r in ledger) == 13
    for row in ledger:
        s = ss[row['source_id']]
        assert hashlib.sha256(base64.b64decode(raw[s['id']]['body'])).hexdigest() == row['source_sha256'] == s['sha256']
        assert s['content_status']['all_pages_read']
        assert not row['current_116_approval']
        for render in row['rendered_pages']:
            assert hashlib.sha256((ROOT / render['path']).read_bytes()).hexdigest() == render['sha256']


def test_blank_workbook_has_thirteen_fields_and_no_extra_required_documents():
    sheet = json.loads((DOCS / 'sdu-blank-workbook-cells.json').read_text())
    assert len(sheet['sheets']['Sayfa1']) == 14  # Title plus thirteen blank data fields.
    assert sheet['sheets']['Sayfa2'] == sheet['sheets']['Sayfa3'] == []
    assert sheet['media_count'] == 0 and not sheet['visual_layout_reviewed']
    records = json.loads((DOCS / 'added-host-records.json').read_text())
    assert len(records['ncu-098']['host_documents']) == 7


def test_school_directory_does_not_expand_exchange_eligibility_or_double_count_housing():
    records = json.loads((DOCS / 'added-host-records.json').read_text())
    text = lambda key: ' '.join(records['ncu-126']['fields'][key]['points'])
    assert '不能把名錄當全都開放交換' in text('courses')
    assert '不是五人同住一間房' in text('housing')
    assert '包含滯在費' in text('cost')
    for sid in ['host-shizuoka-next-02', 'host-shizuoka-next-03', 'host-shizuoka-next-04']:
        policy = json.loads((ROOT / f'sources/ncu/2026-10-08/{sid}-index-review.json').read_text())
        assert policy['quarantined_pdf_pages']
        assert all('不是中央116' in p['note_zh'] for p in json.loads((ROOT / f'sources/ncu/2026-10-08/{sid}-visual-review.json').read_text())['page_transcriptions'])
