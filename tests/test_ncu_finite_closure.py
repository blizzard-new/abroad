"""Check repaired homonym mapping and honest bounded citation coverage."""
import gzip
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).parents[1]
DOCS = ROOT / 'docs/data/ncu-completion-20261011/resume/finite-closure'


def test_same_chinese_name_keeps_spain_and_malaysia_sources_separate():
    from exchange_info.ncu_student_view import fetch_ncu_partner_universities
    maps = {r['row_id']: r for r in json.loads((ROOT / 'sources/ncu/2026-10-08/source-map-candidates.json').read_text())}
    assert len(maps['ncu-074']['files']) == 2 and len(maps['ncu-198']['files']) == 4
    assert not set(maps['ncu-074']['files']) & set(maps['ncu-198']['files'])
    partners = fetch_ncu_partner_universities()
    es = next(p for p in partners if 'Ramon Llull' in p.school_name)
    my = next(p for p in partners if 'Tunku' in p.school_name)
    assert es.country == '西班牙' and my.country == '馬來西亞'
    assert '西班牙文B2' in es.eligibility and 'TOEIC' not in es.eligibility
    assert 'RM1000' not in es.tuition_info and '1cWQi5Dl' not in es.eligibility
    assert 'TOEIC' in my.eligibility and '西班牙文B2' not in my.eligibility
    assert 'RM1000-RM1200' in my.tuition_info and '1wBS543c' not in my.eligibility
    assert es.quota is None and my.quota is None
    assert es.availability_status == my.availability_status == 'agreement_only'


def test_selected_cited_pages_are_sha_bound_without_promoting_unread_remainders():
    sources = {s['id']: s for s in json.loads(gzip.decompress((ROOT / 'src/exchange_info/official_data/ncu/source-evidence.json.gz').read_bytes()))}
    ledger = json.loads((DOCS / 'reading-ledger.json').read_text())['items']
    assert len(ledger) == 14 and sum(len(r['pages_this_review']) for r in ledger) == 61
    for r in ledger:
        s = sources[r['source_id']]
        assert s['sha256'] == r['source_sha256'] == r['retrieval_receipt']['sha256']
        assert set(r['pages_this_review']) <= set(s['reading_review']['pages_reviewed'])
    for sid in ['host-undip-courses-fall', 'host-tuaf-newhandbook', 'host-dhu-coursedesc', 'host-sgntu-info']:
        assert not sources[sid]['content_status']['all_pages_read']
    assert sources['host-tohoku-attachment-24']['visual_review']['pdf_pages_reviewed'] == [10, 11, 13, 14]
    kyutech = sources['host-kyutech-lsse-timetable2026-en-web-excerpt']
    assert hashlib.sha256((DOCS / (kyutech['id'] + '.pdf')).read_bytes()).hexdigest() == kyutech['sha256']
    assert kyutech['content_status']['all_pages_read']
    assert kyutech['index_review']['quarantined_pdf_pages'] == [1, 2]
    hcm = sources['host-hcm-iex-2018-browser']
    assert hcm['source_excerpt_only'] and not hcm.get('sha256')
    assert not hcm['latest_original_retrieval_attempt']['retrieved_original']


def test_frozen_inventory_reconciles_every_source_and_separates_triage_from_reading():
    x = json.loads((DOCS / 'frozen-candidate-classification.json').read_text())
    assert len(x['items']) == len({r['source_id'] for r in x['items']}) == 300
    assert sum(x['category_counts'].values()) == 300
    assert (x['full_original_read_since_freeze'], x['remaining_not_full_read']) == (20, 280)
    assert x['remaining_cited_sources'] == 59
    assert (x['remaining_cited_valid_unique_sha'], x['remaining_cited_sources_without_sha'], x['remaining_cited_alias_extras']) == (55, 1, 3)
    assert not x['cited_field_sources_without_reading_evidence']
    assert x['category_counts']['exact_sha_alias_of_reviewed_original'] == 6
    assert all(not r['current_116_approval'] for r in x['items'])
    assert len(json.loads((DOCS / 'schools-without-manual-host-review.json').read_text())) == 59
