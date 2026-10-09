"""Concurrent public boot batches validate one offline bundle and keep source keys."""
import json
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest

from exchange_info import public_translation as tr


@pytest.fixture
def bundle(monkeypatch, tmp_path):
    path = tmp_path / 'translations.json'
    rows = [{'status': 'machine', 'original': 'Monthly rent is 12000 yen.',
             'url': 'https://example.edu/housing', 'zh': '每月租金為12000日圓。'},
            {'status': 'machine', 'original': 'The application fee is 50 dollars.',
             'url': 'https://example.edu/fees', 'zh': '申請費用為500美元。'},
            {'status': 'reviewed', 'original': 'No dormitory guarantee.',
             'url': 'https://example.edu/housing', 'zh': '不保證宿位。'}]
    path.write_text(json.dumps(rows))
    tr._bundled_machine_translations.cache_clear()
    monkeypatch.setattr(tr, 'BUNDLED_MACHINE_TRANSLATIONS', path)
    yield path, rows
    tr._bundled_machine_translations.cache_clear()


def test_concurrent_translation_batches_load_and_validate_once(bundle, monkeypatch):
    path, rows = bundle
    real_read = Path.read_text; real_valid = tr._valid_translation
    reads = []; validations = []; barrier = threading.Barrier(6)

    def read(source, *args, **kwargs):
        if source == path:
            reads.append(source); time.sleep(.03)
        return real_read(source, *args, **kwargs)

    def valid(original, zh):
        validations.append(original)
        return real_valid(original, zh)

    monkeypatch.setattr(Path, 'read_text', read)
    monkeypatch.setattr(tr, '_valid_translation', valid)

    def load(index):
        barrier.wait()
        return tr._bundled_machine_translations()

    with ThreadPoolExecutor(max_workers=6) as pool:
        results = list(pool.map(load, range(6)))
    assert len(reads) == 1 and validations == [rows[0]['original'], rows[1]['original']]
    expected = {tr._key(rows[0]['original'], rows[0]['url']): rows[0]['zh']}
    assert results == [expected] * 6
    assert tr._key(rows[0]['original'], 'https://other.example/housing') not in results[0]


def test_failed_cold_translation_load_releases_lock_for_retry(bundle):
    path, rows = bundle
    path.write_text('{')
    with pytest.raises(json.JSONDecodeError): tr._bundled_machine_translations()
    path.write_text(json.dumps(rows))
    assert tr._bundled_machine_translations() == {tr._key(rows[0]['original'], rows[0]['url']): rows[0]['zh']}


def test_existing_cached_reader_interface_invalidates_replaced_bundle(bundle):
    path, rows = bundle
    first = tr._bundled_machine_translations()
    assert tr._bundled_machine_translations.cache_info().misses == 1
    assert tr._bundled_machine_translations.cache_parameters() == {'maxsize': 1, 'typed': False}
    changed = {**rows[0], 'original': 'Monthly rent is 13000 yen.', 'zh': '每月租金為13000日圓。'}
    path.write_text(json.dumps([changed]))
    tr._bundled_machine_translations.cache_clear()
    assert tr._bundled_machine_translations() == {tr._key(changed['original'], changed['url']): changed['zh']}
    assert tr._key(rows[0]['original'], rows[0]['url']) in first
