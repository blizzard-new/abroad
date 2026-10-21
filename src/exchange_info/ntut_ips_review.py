"""Replay the source-bound IPS degree review without replacing later edits."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from .host_source_review_round25 import apply_review_manifest, pointer_parent
from .ntust_source_review import write_atomic

MANIFEST = "docs/data-verification-20261021/round42-ntut-waseda-ips-review.json"
MANIFEST_SHA256 = "5cd5995a768e79bc6a5e090a5c829fc6cd4226a23bfe9af686999624e6cec0ef"
ARCHIVE_KEY = "source_review_round42"
METADATA_MANIFEST = "docs/data-verification-20261021/round42-derived-metadata-review.json"
METADATA_SHA256 = "91fade155ff252fb536f61abe67e6e1c0dab237eb055841ec1dea2ad519d5850"
DISPLAY_MANIFEST = "docs/data-verification-20261021/round42-ntut-ips-display-followup.json"
DISPLAY_SHA256 = "25905dc969ec9d8bc32a82a29361cd4842f180d18bb8930b742fd3613407eaa0"


def load_manifest(root: Path) -> dict:
    raw = (root / MANIFEST).read_bytes()
    if hashlib.sha256(raw).hexdigest() != MANIFEST_SHA256:
        raise ValueError("NTUT IPS source-review manifest hash mismatch")
    return json.loads(raw)


def apply_ntut_ips_review(root: Path) -> int:
    changed = apply_review_manifest(root, "ntut", load_manifest(root), ARCHIVE_KEY)
    display_raw = (root / DISPLAY_MANIFEST).read_bytes()
    if hashlib.sha256(display_raw).hexdigest() != DISPLAY_SHA256:
        raise ValueError("NTUT IPS display-review manifest hash mismatch")
    changed += apply_review_manifest(root, "ntut", json.loads(display_raw), "source_review_round42_display")
    raw = (root / METADATA_MANIFEST).read_bytes()
    if hashlib.sha256(raw).hexdigest() != METADATA_SHA256:
        raise ValueError("NTUT IPS metadata-review manifest hash mismatch")
    manifest = json.loads(raw)
    partners = [json.loads(line) for line in
                (root / "src/exchange_info/official_data/ntut/partners.jsonl").read_text("utf8").splitlines()]
    counts = {
        "verified_locations": sum(p.get("location", {}).get("geocode_status") == "verified" for p in partners),
        "open_partners": sum(p.get("availability_status") == "open" for p in partners),
        "reference_only_partners": sum(p.get("availability_status") == "reference_only" for p in partners),
    }
    for scope in manifest["rows"]:
        path = root / scope["file"]
        if not path.exists():
            continue
        value = json.loads(path.read_text("utf8"))
        for patch in scope["patches"]:
            parent, key = pointer_parent(value, patch["pointer"])
            if key in counts and counts[key] != patch["value"]:
                continue
            if parent[key] != patch["expected_value"]:
                continue
            archive = value.setdefault("reference_data", {}).setdefault("source_review_round42_metadata", {})
            archive.setdefault(patch["pointer"], parent[key])
            parent[key] = patch["value"]
            changed += 1
        write_atomic(path, value)
    return changed
