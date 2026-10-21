"""Ordered review decisions in bounded JSONL parts suitable for a source PR."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path

MAX_PART_BYTES = 8 * 1024 * 1024
LEGACY_NAME = "review-decisions.jsonl"
PARTS_NAME = "review-decisions"


def ledger_paths(directory: Path):
    directory = Path(directory)
    legacy, parts = directory / LEGACY_NAME, directory / PARTS_NAME
    if parts.exists():
        if legacy.exists():
            raise ValueError("Both legacy and split review ledgers exist; resolve migration before writing")
        paths = sorted(parts.glob("part-*.jsonl"))
        if [p.name for p in paths] != [f"part-{i:05d}.jsonl" for i in range(1, len(paths) + 1)]:
            raise ValueError("Review ledger part sequence is incomplete")
        return paths
    return [legacy] if legacy.exists() else []


def iter_decisions(directory: Path):
    for path in ledger_paths(directory):
        with path.open(encoding="utf8") as stream:
            for line in stream:
                if line.strip():
                    yield json.loads(line)


def _binding(row):
    return row["base_record_id"], row["pointer"], row["base_value_sha256"]


def _write_new_part(path: Path, body: bytes):
    if path.exists():
        raise FileExistsError(path)
    temporary = path.with_suffix(".jsonl.audit-tmp")
    with temporary.open("xb") as stream:
        stream.write(body)
    os.replace(temporary, path)


def append_decisions(directory: Path, decisions, *, max_bytes=MAX_PART_BYTES):
    """Append new IDs in order; existing parts are immutable and replay is safe.

    A conflicting original-field binding is an error. To revise the conclusion
    for an existing binding, callers must issue a new review ID rather than
    silently replace earlier evidence.
    """
    directory = Path(directory)
    if (directory / LEGACY_NAME).exists():
        raise ValueError("Split the legacy ledger before appending")
    known = {}
    for row in iter_decisions(directory):
        rid = row["review_id"]
        if rid in known:
            raise ValueError(f"Duplicate review ID in existing ledger: {rid}")
        known[rid] = _binding(row)
    pending = []
    for row in decisions:
        rid, binding = row["review_id"], _binding(row)
        if rid in known:
            if binding != known[rid]:
                raise ValueError(f"Conflicting original-field binding: {rid}")
            continue
        encoded = (json.dumps(row, ensure_ascii=False) + "\n").encode("utf8")
        if len(encoded) > max_bytes:
            raise ValueError(f"Single review decision exceeds part limit: {rid}")
        pending.append(encoded)
        known[rid] = binding
    if not pending:
        return 0
    parts = directory / PARTS_NAME
    parts.mkdir(parents=True, exist_ok=True)
    number = len(ledger_paths(directory)) + 1
    body = bytearray()
    for line in pending:
        if body and len(body) + len(line) > max_bytes:
            _write_new_part(parts / f"part-{number:05d}.jsonl", bytes(body))
            number += 1
            body.clear()
        body.extend(line)
    if body:
        _write_new_part(parts / f"part-{number:05d}.jsonl", bytes(body))
    return len(pending)


def split_legacy(directory: Path, archive: Path, *, max_bytes=MAX_PART_BYTES):
    """Preserve every source byte and line in bounded parts and a local archive."""
    directory, archive = Path(directory).resolve(), Path(archive).resolve()
    legacy = directory / LEGACY_NAME
    parts, stage = directory / PARTS_NAME, directory / ".review-decisions-split"
    if parts.exists() or stage.exists() or archive.exists():
        raise FileExistsError("Split target, staging directory or archive already exists")
    if not legacy.is_file() or not archive.parent.is_dir():
        raise FileNotFoundError("Legacy ledger or archive parent does not exist")
    stage.mkdir()
    source_hash, concatenated_hash = hashlib.sha256(), hashlib.sha256()
    entries, body, count, number = [], bytearray(), 0, 1

    def flush():
        nonlocal number
        data = bytes(body)
        path = stage / f"part-{number:05d}.jsonl"
        _write_new_part(path, data)
        stored = path.read_bytes()
        if stored != data:
            raise ValueError("Split write mismatch")
        concatenated_hash.update(stored)
        entries.append({"file": path.name, "bytes": len(stored),
            "lines": stored.count(b"\n"), "sha256": hashlib.sha256(stored).hexdigest()})
        number += 1
        body.clear()

    with legacy.open("rb") as stream:
        for line in stream:
            if not line.endswith(b"\n") or not line.strip():
                raise ValueError("Legacy ledger must contain complete nonempty JSONL records")
            json.loads(line)
            if len(line) > max_bytes:
                raise ValueError("Single legacy review decision exceeds part limit")
            source_hash.update(line)
            count += 1
            if body and len(body) + len(line) > max_bytes:
                flush()
            body.extend(line)
    if body:
        flush()
    if source_hash.digest() != concatenated_hash.digest():
        raise ValueError("Concatenated parts differ from the legacy ledger")
    receipt = {"format": "ordered_jsonl_parts_v1", "original_file": LEGACY_NAME,
        "original_sha256": source_hash.hexdigest(), "original_records": count,
        "max_part_bytes": max_bytes, "parts": entries,
        "preserves": "Exact original bytes and line order; no decisions reclassified or reserialized."}
    (stage / "migration.json").write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", "utf8")
    # Move only the named, validated file. The full original remains recoverable.
    os.replace(legacy, archive)
    try:
        stage.rename(parts)
    except Exception:
        os.replace(archive, legacy)
        raise
    return receipt
