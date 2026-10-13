"""Complete TKU evidence survives compact indexing and cannot leak mutations."""
import json
import os

from exchange_info import tku_census as census


def test_all_census_rows_and_aliases_match_original_and_isolate_readers():
    original = json.loads((census.BUNDLE / 'full_census_audit.json').read_text())
    expected_aliases = {}
    for row in original['schools']:
        names = {row['school_name'], census.census_school_name(row)}
        names.update(census.programme_map()[pid]['fields']['school_name']['value']
                     for pid in row.get('programme_ids', []))
        expected_aliases.update({name: row for name in names})
        assert census.school_audit_by_id(row['id']) == row
    assert len(original['schools']) == 287
    assert dict(census.school_index().items()) == expected_aliases
    assert census.census_audit() == original
    assert census.census_summary() == {k:v for k,v in original.items() if k != 'schools'}
    for name, row in expected_aliases.items():
        assert census.school_identifier(name) == row['id']
    name = next(iter(expected_aliases))
    changed = census.school_audit(name)
    changed['fields'].clear()
    assert census.school_audit(name) == expected_aliases[name]
    exported = census.census_audit()
    exported['schools'][0]['fields'].clear()
    exported['field_counts'].clear()
    assert census.census_audit() == original
    assert census.school_audit_by_id('absent-institution') is None
    assert census.school_identifier('absent-school') is None


def test_replaced_census_file_invalidates_compact_snapshot(tmp_path, monkeypatch):
    original = json.loads((census.BUNDLE / 'full_census_audit.json').read_text())
    census.programme_map()  # Identity programmes are unchanged by this fixture.
    path = tmp_path / 'full_census_audit.json'
    path.write_text(json.dumps(original, ensure_ascii=False))
    monkeypatch.setattr(census, 'BUNDLE', tmp_path)
    try:
        row = original['schools'][0]
        assert census.school_audit_by_id(row['id']) == row
        stat = path.stat()
        row['selection_note'] += ' fixture source revision'
        replacement = tmp_path / 'replacement.json'
        replacement.write_text(json.dumps(original, ensure_ascii=False))
        os.replace(replacement, path)
        os.utime(path, ns=(stat.st_atime_ns, stat.st_mtime_ns + 1_000_000))
        assert census.school_audit_by_id(row['id']) == row
        assert census.school_audit(row['school_name']) == row
    finally:
        census.census_audit.cache_clear()
