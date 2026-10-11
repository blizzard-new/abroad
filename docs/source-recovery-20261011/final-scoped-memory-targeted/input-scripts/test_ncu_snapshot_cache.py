"""NCU audit cache keeps exact source records and invalidates changed bundles."""
import gzip
import json
import os
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest

from exchange_info import ncu_student_view as ncu


@pytest.fixture
def snapshot(monkeypatch, tmp_path):
    audit = [{'school_name': '測試大學', 'read_sources': [{'id': 'host-a'}],
              'fields': {'housing': {'note': '2025參考，116待核',
                                     'original_evidence': [{'page': 2, 'text': 'Rent 12000'}]}}}]
    sources = [{'id': 'host-a', 'url': 'https://example.edu/host.pdf',
                'checked_at': '2026-10-09', 'pages': [{'page': 2, 'text': 'Rent 12000'}],
                'source_excerpt_only': True, 'reading_review': {'scope': '只讀第2頁'}},
               {'id': 'other', 'pages': [{'page': 1, 'text': 'Other packet'}]}]
    (tmp_path / 'field-audit.json').write_text(json.dumps(audit, ensure_ascii=False))
    (tmp_path / 'source-evidence.json.gz').write_bytes(gzip.compress(json.dumps(sources).encode()))
    ncu._read_audit_snapshot.cache_clear()
    monkeypatch.setattr(ncu, 'NCU_OFFICIAL_DATA_DIR', tmp_path)
    yield tmp_path, audit, sources
    ncu._read_audit_snapshot.cache_clear()


def test_source_audit_matches_uncached_record_and_keeps_read_scope(snapshot):
    root, audits, sources = snapshot
    assert ncu.ncu_field_audit('測試大學') == audits[0]
    assert ncu.ncu_source_audit('測試大學') == {**audits[0], 'source_evidence': sources[:1]}
    assert ncu.ncu_source_audit('未收錄') is None


def test_audit_callers_cannot_modify_shared_field_or_source_records(snapshot):
    root, audits, sources = snapshot
    result = ncu.ncu_source_audit('測試大學')
    result['fields']['housing']['original_evidence'][0]['text'] = 'changed'
    result['source_evidence'][0]['pages'][0]['text'] = 'changed'
    result['source_evidence'].append({'id': 'invented'})
    assert ncu.ncu_source_audit('測試大學') == {**audits[0], 'source_evidence': sources[:1]}


def test_changed_bundle_signature_invalidates_each_snapshot(snapshot):
    root, audits, sources = snapshot
    ncu.ncu_source_audit('測試大學')
    for filename, changed in [('field-audit.json', [{**audits[0], 'fields': {'housing': {'note': '2027新版'}}}]),
                              ('source-evidence.json.gz', [{**sources[0], 'pages': [{'page': 3, 'text': 'New source'}]}])]:
        path = root / filename
        stat = path.stat()
        raw = json.dumps(changed).encode()
        path.write_bytes(gzip.compress(raw) if path.suffix == '.gz' else raw)
        os.utime(path, ns=(stat.st_atime_ns, stat.st_mtime_ns + 1_000_000))
    result = ncu.ncu_source_audit('測試大學')
    assert result['fields']['housing']['note'] == '2027新版'
    assert result['source_evidence'][0]['pages'] == [{'page': 3, 'text': 'New source'}]


def test_concurrent_details_read_each_bundle_once(snapshot, monkeypatch):
    root, audits, sources = snapshot
    real = ncu._iter_audit_rows
    calls = []; barrier = threading.Barrier(6); lock = threading.Lock()

    def read(path):
        if path.parent == root:
            with lock: calls.append(path.name)
            time.sleep(.02)
        return real(path)

    monkeypatch.setattr(ncu, '_iter_audit_rows', read)

    def load(index):
        barrier.wait()
        return ncu.ncu_source_audit('測試大學') if index % 2 else ncu.ncu_field_audit('測試大學')

    with ThreadPoolExecutor(max_workers=6) as pool:
        results = list(pool.map(load, range(6)))
    assert calls.count('field-audit.json') == calls.count('source-evidence.json.gz') == 1
    assert all(result['fields'] == audits[0]['fields'] for result in results)


def test_failed_snapshot_load_does_not_poison_retry(snapshot):
    root, audits, sources = snapshot
    path = root / 'field-audit.json'
    path.write_text('{')
    with pytest.raises(json.JSONDecodeError): ncu.ncu_field_audit('測試大學')
    path.write_text(json.dumps(audits))
    assert ncu.ncu_field_audit('測試大學') == audits[0]


@pytest.mark.parametrize('chunk_size', [1, 7, 64])
def test_streamed_json_preserves_unicode_nested_arrays_and_escapes(chunk_size):
    from io import StringIO
    rows=[{'id':'a', 'text':'中文 \" [ ] 串流', 'pages':[{'text':'line\nnext'}]}, {'id':'b','null':None,'zero':0}]
    assert list(ncu._json_array_items(StringIO(json.dumps(rows,ensure_ascii=False)),chunk_size))==rows


@pytest.mark.parametrize('payload', ['', '{}', '[', '[{}', '[{},]', '[{}]x', '[{} {}]'])
def test_streamed_json_rejects_incomplete_or_invalid_documents(payload):
    from io import StringIO
    with pytest.raises(json.JSONDecodeError):list(ncu._json_array_items(StringIO(payload),3))


def test_cache_is_bounded_in_bytes_and_never_truncates_large_records(snapshot, monkeypatch):
    root,audits,sources=snapshot
    monkeypatch.setattr(ncu,'_AUDIT_CACHE_BYTES',100)
    actual=ncu.ncu_source_audit('測試大學')
    assert actual=={**audits[0],'source_evidence':sources[:1]}
    assert ncu._audit_cache_bytes<=100
    assert all(len(blob)<=100 for blob in ncu._audit_cache.values())


def test_empty_results_cannot_accumulate_unbounded_cache_keys(snapshot):
    for i in range(24):assert ncu.ncu_field_audit(f'未收錄-{i}') is None
    assert len(ncu._audit_cache)<=ncu._AUDIT_CACHE_ITEMS
    assert ncu._audit_cache_bytes<=ncu._AUDIT_CACHE_BYTES
