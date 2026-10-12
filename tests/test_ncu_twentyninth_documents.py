"""Faculty restrictions and physical PDF pages remain traceable after full reading."""
import base64
import gzip
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).parents[1]
DOCS = ROOT / 'docs/data/ncu-completion-20261011/resume/twentyninth'


def test_five_cited_originals_and_eleven_physical_pages_are_read():
    ledger = json.loads((DOCS / 'reading-ledger.json').read_text())['items']
    sources = {s['id']: s for s in json.loads(gzip.decompress((ROOT / 'src/exchange_info/official_data/ncu/source-evidence.json.gz').read_bytes()))}
    raw = {s['source_id']: s for s in json.loads(gzip.decompress((ROOT / 'sources/ncu/2026-10-11/resume-twentyninth-original-responses.json.gz').read_bytes()))}
    assert len(ledger) == 5 and sum(len(r['pages_reviewed']) for r in ledger) == 11
    for row in ledger:
        source = sources[row['source_id']]
        assert hashlib.sha256(base64.b64decode(raw[row['source_id']]['body'])).hexdigest() == source['sha256'] == row['source_sha256']
        assert source['content_status']['all_pages_read']
        assert source['content_status']['visual_reviewed_page_count'] == len(source['pages'])
        assert not row['current_116_approval']
        for render in row['rendered_pages']:
            assert hashlib.sha256((ROOT / render['path']).read_bytes()).hexdigest() == render['sha256']


def test_fee_retrieval_uses_visually_verified_rows_without_rewriting_native():
    from exchange_info.ncu_source_coverage import indexable_source_text
    sources = json.loads(gzip.decompress((ROOT / 'src/exchange_info/official_data/ncu/source-evidence.json.gz').read_bytes()))
    source = next(s for s in sources if s['id'] == 'host-tuaf-2026')
    original = source['pages'][1]['text']
    # The known bad extraction survives solely for provenance.
    assert '$95.00/6 Months' in original
    replacement = source['page_transcriptions'][0]['text']
    assert 'ADMINISTRATION FEE: $70' in replacement
    assert 'VISA FEE: $95.00/6 Months' in replacement
    assert source['index_review']['quarantined_pdf_pages'] == [2]
    indexed = indexable_source_text(source)
    assert replacement in indexed
    assert original.strip() not in indexed
    assert '未獨立證明幣別' in indexed


def test_historical_coordinator_and_scholarship_conditions_remain_separate():
    from exchange_info import storage
    ws = [w for w in storage.load_bundled_application_workflows() if w.home_university == '國立中央大學']
    assert all(w.review_status == 'pending_review' for w in ws)
    assert not any(s.deadline_reminder_eligible for w in ws for s in w.steps)
    recs = json.loads((DOCS / 'added-host-records.json').read_text())
    text = lambda rid, key: ' '.join(recs[rid]['fields'][key]['points'])
    assert '不當一般交換錄取GPA' in text('ncu-125', 'cost')
    assert '下載PDF僅兩頁' in text('ncu-125', 'cost')
    assert '不收學生直接送件' in text('ncu-125', 'host_documents')
    assert '不是中央116名額' in text('ncu-125', 'eligibility')
    assert '不等於不用母校提名' in text('ncu-098', 'host_deadline')
    assert '不擅改成全面禁止' in text('ncu-008', 'housing')
    assert len(recs['ncu-098']['host_documents']) == 7
    assert recs['ncu-125']['host_documents'] == []
