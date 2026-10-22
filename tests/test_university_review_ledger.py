"""Lossless migration, stable order and safe review-ledger replay."""
import hashlib
import importlib.util
import json
from pathlib import Path

import pytest

SPEC = importlib.util.spec_from_file_location("review_ledger", Path(__file__).parents[1] / "scripts/university_review_ledger.py")
ledger = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(ledger)


def decision(number):
    return {"review_id": str(number), "base_record_id": "大學", "pointer": f"/field/{number}",
        "base_value_sha256": hashlib.sha256(str(number).encode()).hexdigest(), "base_value": number}


def test_split_preserves_original_bytes_and_order_and_archives_source(tmp_path):
    directory = tmp_path / "docs"
    directory.mkdir()
    original = b"".join((json.dumps(decision(i), ensure_ascii=False) + "\r\n").encode() for i in range(7))
    source = directory / ledger.LEGACY_NAME
    source.write_bytes(original)
    archive = tmp_path / "original.jsonl"
    receipt = ledger.split_legacy(directory, archive, max_bytes=500)
    assert receipt["original_records"] == 7
    assert receipt["original_sha256"] == hashlib.sha256(original).hexdigest()
    assert not source.exists() and archive.read_bytes() == original
    parts = ledger.ledger_paths(directory)
    assert len(parts) > 1 and all(p.stat().st_size <= 500 for p in parts)
    assert b"".join(p.read_bytes() for p in parts) == original
    assert list(ledger.iter_decisions(directory)) == [decision(i) for i in range(7)]
    saved = {p: p.read_bytes() for p in parts}
    assert ledger.append_decisions(directory, [decision(6), decision(7), decision(8)], max_bytes=500) == 2
    assert all(p.read_bytes() == data for p, data in saved.items())
    assert ledger.append_decisions(directory, [decision(7), decision(8)]) == 0
    assert list(ledger.iter_decisions(directory)) == [decision(i) for i in range(9)]


def test_conflicting_binding_is_rejected_before_any_append(tmp_path):
    ledger.append_decisions(tmp_path, [decision(1)])
    before = {p: p.read_bytes() for p in ledger.ledger_paths(tmp_path)}
    with pytest.raises(ValueError, match="Conflicting"):
        ledger.append_decisions(tmp_path, [decision(2), {**decision(1), "pointer": "/different"}])
    assert {p: p.read_bytes() for p in ledger.ledger_paths(tmp_path)} == before


def test_missing_part_and_oversized_record_cannot_silently_pass(tmp_path):
    with pytest.raises(ValueError, match="exceeds"):
        ledger.append_decisions(tmp_path, [decision(1)], max_bytes=1)
    assert ledger.ledger_paths(tmp_path) == []
    parts = tmp_path / ledger.PARTS_NAME
    parts.mkdir()
    (parts / "part-00002.jsonl").write_text(json.dumps(decision(1)) + "\n", "utf8")
    with pytest.raises(ValueError, match="sequence"):
        list(ledger.iter_decisions(tmp_path))
