"""Streaming census reads preserve values and publish only complete snapshots."""
from concurrent.futures import ThreadPoolExecutor
from io import StringIO
import json
import threading
import time

import pytest

from exchange_info import tku_census as census
from exchange_info.json_stream import read_json_object_array


@pytest.mark.parametrize('chunk_size', [1, 2, 3, 7, 128, 257])
def test_object_array_stream_keeps_complete_values_across_chunk_boundaries(chunk_size):
    original = {'before': {'keep': True}, 'schools': [12, -1.125e120, 1e-5,
        True, False, None, '中😀\\x' * 40, [1, 2], {'field': 'value'}], 'after': [3, 4]}
    class BoundedReader(StringIO):
        def read(self, size=-1):
            assert 0 < size <= chunk_size
            return super().read(size)
    rows = []
    metadata = read_json_object_array(BoundedReader(json.dumps(original, ensure_ascii=False)),
                                     'schools', rows.append, chunk_size)
    assert {**metadata, 'schools': rows} == original


@pytest.mark.parametrize('payload', [
    '', '[]', '{}', '{"schools":null}', '{"schools":{}}',
    '{"schools":[}', '{"schools":[1,]}', '{"schools":[1 2]}',
    '{"schools":[12e]}', '{"schools":[]', '{"schools":[]} true',
    '{"schools":[],"schools":[]}', '{"schools":[],"key":1,"key":2}',
    '{"schools":[],}', '{"schools":[],"key" 1}', '{"schools":[]\u00a0}',
])
def test_object_array_stream_rejects_incomplete_or_ambiguous_documents(payload):
    with pytest.raises(json.JSONDecodeError):
        read_json_object_array(StringIO(payload), 'schools', lambda row: None, 2)


@pytest.fixture
def small_snapshot(tmp_path, monkeypatch):
    original = {'field_counts': {'missing': 1}, 'schools': [
        {'id': 'test-1', 'school_name': '測試大學', 'english_name': 'Test University',
         'programme_ids': [], 'fields': {'quota': {'value': None, 'status': 'missing'}}}]}
    path = tmp_path/'full_census_audit.json'
    path.write_text(json.dumps(original, ensure_ascii=False))
    monkeypatch.setattr(census, 'BUNDLE', tmp_path)
    monkeypatch.setattr(census, 'programme_map', lambda: {})
    census.census_audit.cache_clear()
    yield original, path
    census.census_audit.cache_clear()


def test_concurrent_first_read_constructs_only_one_complete_snapshot(small_snapshot, monkeypatch):
    original, path = small_snapshot
    actual_reader = census.read_json_object_array
    visits = []
    barrier = threading.Barrier(6)
    def counting_reader(*args, **kwargs):
        visits.append(1)
        time.sleep(.02)
        return actual_reader(*args, **kwargs)
    monkeypatch.setattr(census, 'read_json_object_array', counting_reader)
    def read(_):
        barrier.wait(timeout=5)
        return census.school_audit_by_id('test-1')
    with ThreadPoolExecutor(max_workers=6) as pool:
        results = list(pool.map(read, range(6)))
    assert results == [original['schools'][0]] * 6
    assert len(visits) == 1
    assert len({id(row) for row in results}) == 6
    assert census.census_audit() == original


def test_late_parse_failure_does_not_cache_partial_census(small_snapshot):
    original, path = small_snapshot
    path.write_text('{"schools":[' + json.dumps(original['schools'][0]) + ',')
    for _ in range(2):
        with pytest.raises(json.JSONDecodeError):
            census.school_audit_by_id('test-1')
    path.write_text(json.dumps(original))
    assert census.census_audit() == original
