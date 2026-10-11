"""Detail reads preserve reviewed content, provenance checks and caller isolation."""
import json
import os

import pytest

from exchange_info import ccu_overseas as ccu
from exchange_info import life_context as life


@pytest.fixture
def reviewed_bundle(tmp_path, monkeypatch):
    original = ccu.BUNDLE
    rows = json.loads((original / 'overseas-reviewed-fields.json').read_text())
    for path in original.iterdir():
        if path.name != 'overseas-reviewed-fields.json':
            (tmp_path / path.name).symlink_to(path, target_is_directory=path.is_dir())
    matrix = tmp_path / 'overseas-reviewed-fields.json'
    matrix.write_text(json.dumps(rows, ensure_ascii=False))
    monkeypatch.setattr(ccu, 'BUNDLE', tmp_path)
    ccu._reviewed_row_payload.cache_clear()
    yield rows, matrix
    ccu._reviewed_row_payload.cache_clear()


def test_scoped_review_keeps_full_row_and_cannot_mutate_next_reader(reviewed_bundle):
    rows, _ = reviewed_bundle
    expected = rows[0]
    actual = ccu.reviewed_row(expected['ccu_page'])
    assert actual == expected
    actual['fields']['housing']['reason'] = 'invented'
    assert ccu.reviewed_row(expected['ccu_page']) == expected
    assert ccu.reviewed_row(-1) is None


def test_scoped_review_rechecks_changed_matrix_and_rejects_source_hash_tampering(reviewed_bundle):
    rows, matrix = reviewed_bundle
    row = next(r for r in rows if any(f['evidence'] for f in r['fields'].values()))
    assert ccu.reviewed_row(row['ccu_page']) == row
    evidence = next(f['evidence'][0] for f in row['fields'].values() if f['evidence'])
    evidence['content_hash'] = '0' * 64
    stat = matrix.stat()
    matrix.write_text(json.dumps(rows, ensure_ascii=False))
    os.utime(matrix, ns=(stat.st_atime_ns, stat.st_mtime_ns + 1_000_000))
    with pytest.raises(ValueError, match='Changed CCU overseas source'):
        ccu.reviewed_row(row['ccu_page'])


def test_scoped_review_checks_all_identities_and_document_tail(reviewed_bundle):
    rows, matrix = reviewed_bundle
    rows[-1]['ccu_page'] = rows[0]['ccu_page']
    matrix.write_text(json.dumps(rows, ensure_ascii=False))
    with pytest.raises(ValueError, match='55 current/quota-unknown'):
        ccu.reviewed_row(rows[1]['ccu_page'])
    matrix.write_text(json.dumps(rows, ensure_ascii=False) + ' invalid tail')
    with pytest.raises(json.JSONDecodeError):
        ccu.reviewed_row(rows[1]['ccu_page'])


def test_bundled_life_index_matches_all_original_reviewed_models_and_isolates_callers():
    expected = {}
    with life.BUNDLED_NTU_LIFE.open() as handle:
        for line in handle:
            row = life.reviewed_life_snapshot(life.LifeResearchSnapshot.model_validate_json(line))
            if row.extraction_version == life.EXTRACTION_VERSION:
                expected[(life.school_identity_key(row.school_name), row.country or '')] = row
    index = life._bundled_ntu_research()
    assert dict(index.items()) == expected
    key = next(k for k, row in expected.items() if row.evidence)
    result = index[key]
    result.evidence[0].text = 'invented'
    result.notes.append('invented')
    assert index[key] == expected[key]


def test_ccu_completion_index_retains_all_104_full_rows_and_isolates_callers():
    from exchange_info import ccu_completion as completion
    expected = {r['ccu_page']: r for r in json.loads(
        (completion.BUNDLE / 'completion-reviewed-fields.json').read_text())['schools']}
    actual = completion.reviewed_completion()
    assert len(actual) == 104
    assert dict(actual.items()) == expected
    key = next(iter(actual))
    row = actual[key]
    row['general_campus_fields'].clear()
    assert actual[key] == expected[key]
