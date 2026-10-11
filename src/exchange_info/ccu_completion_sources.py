"""Validate CCU completion receipts, including lossless response archives."""
from __future__ import annotations

import gzip
import hashlib
import json
from pathlib import Path
from urllib.parse import urlsplit


def validate_completion_source(bundle: Path, evidence: dict, checked: dict):
    for key in ["source_url", "service_url"]:
        if evidence.get(key) and urlsplit(evidence[key]).scheme not in {"http", "https"}:
            raise ValueError("CCU completion sources require public HTTP(S) URLs")
    sid = evidence.get("source_id")
    if not sid:
        return  # Existing mother-list evidence retains its original validators.
    receipt_path = bundle / "completion_sources" / f"{sid}.receipt.json"
    if not receipt_path.exists():
        if (bundle / "overseas_sources" / f"{sid}.json").exists():
            return  # The original independent 55-school source validator applies.
        raise ValueError(f"Missing CCU completion source receipt: {sid}")
    expected = evidence["content_hash"]
    if sid in checked:
        if expected != checked[sid]:
            raise ValueError("Inconsistent CCU completion evidence hashes")
        return
    record = json.loads(receipt_path.read_text())
    raw_path = (bundle / record["bundled_file"]).resolve()
    if not raw_path.is_relative_to(bundle.resolve()):
        raise ValueError("CCU response archive must stay inside its school bundle")
    raw = raw_path.read_bytes()
    if raw_path.suffix == ".gz":
        if hashlib.sha256(raw).hexdigest() != record["stored_sha256"]:
            raise ValueError("Changed CCU compressed response archive")
        raw = gzip.decompress(raw)
    if (record.get("tls_verify") is not True or record.get("http_status") != 200
            or record.get("error") or record["sha256"] != expected
            or hashlib.sha256(raw).hexdigest() != expected):
        raise ValueError("Unread or changed CCU completion source")
    checked[sid] = expected
