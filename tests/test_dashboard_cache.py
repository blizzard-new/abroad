import gzip

from exchange_info.dashboard_cache import DashboardResponseCache


def response(text):
    raw = text.encode()
    return raw, gzip.compress(raw, mtime=0), 'W/"test"'


def test_expired_generations_are_replaced_and_origins_remain_separate():
    cache = DashboardResponseCache()
    for generation in range(200):
        key = ('ntu', 'https://example.org', generation)
        value = response(f'full response {generation}')
        cache.put(key, value)
        assert cache.get(key) == value
        assert len(cache) == 1
        assert cache.payload_bytes == len(value[0]) + len(value[1])
    other = ('ntu', 'https://other.example.org', 199)
    cache.put(other, response('other absolute image URL'))
    assert len(cache) == 2
    assert cache.get(('ntu', 'https://example.org', 198)) is None


def test_byte_budget_evicts_least_recently_used_response():
    value = response('complete public source data')
    size = len(value[0]) + len(value[1])
    cache = DashboardResponseCache(max_bytes=size * 2, max_entries=32)
    keys = [(school, 'https://example.org', 1) for school in ('ntu', 'ccu', 'cgu')]
    cache.put(keys[0], value)
    cache.put(keys[1], value)
    assert cache.get(keys[0]) == value
    cache.put(keys[2], value)
    assert cache.get(keys[1]) is None
    assert cache.get(keys[0]) == cache.get(keys[2]) == value
    assert cache.payload_bytes == size * 2


def test_large_response_is_not_retained_or_truncated():
    cache = DashboardResponseCache(max_bytes=50, max_entries=2)
    key = ('ntu', 'https://example.org', 1)
    cache.put(key, response('small'))
    large = response('完整來源與欄位' * 100)
    cache.put((*key[:2], 2), large)
    assert not len(cache)
    assert cache.payload_bytes == 0
    assert gzip.decompress(large[1]) == large[0]


def test_entry_count_bounds_tiny_payloads():
    cache = DashboardResponseCache(max_entries=2)
    for i in range(100):
        cache.put((str(i), 'https://example.org', 1), response('ok'))
        assert len(cache) <= 2
