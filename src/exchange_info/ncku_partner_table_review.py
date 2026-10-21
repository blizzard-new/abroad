"""Replay NCKU's source-bound table review while preserving later independent edits."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from .host_source_review_round25 import apply_review_manifest, pointer_parent
from .ntust_source_review import write_atomic

MANIFEST = "docs/data-verification-20261021/round43-ncku-partner-table-review.json"
MANIFEST_SHA256 = "5bd90615b19ab2618c9ec332d49e93a6ad154518cb11c72a6155ba69b25bfcbd"
ARCHIVE_KEY = "source_review_round43"
METADATA_MANIFEST = "docs/data-verification-20261021/round43-ncku-metadata-review.json"
METADATA_SHA256 = "baacd6261e20dd42464e5a75e32dd686538968a7201fa9d6e990ad59bfe9110c"


def load_manifest(root: Path) -> dict:
    raw = (root / MANIFEST).read_bytes()
    if hashlib.sha256(raw).hexdigest() != MANIFEST_SHA256:
        raise ValueError("NCKU partner-table review manifest hash mismatch")
    return json.loads(raw)


def apply_ncku_partner_table_review(root: Path) -> int:
    changed = apply_review_manifest(root, "ncku", load_manifest(root), ARCHIVE_KEY)
    raw = (root / METADATA_MANIFEST).read_bytes()
    if hashlib.sha256(raw).hexdigest() != METADATA_SHA256:
        raise ValueError("NCKU review metadata manifest hash mismatch")
    partners = [json.loads(line) for line in
                (root / "src/exchange_info/official_data/ncku/partners.jsonl").read_text("utf8").splitlines()]
    open_count = sum(r.get("availability_status") == "open" for r in partners)
    for scope in json.loads(raw)["rows"]:
        path = root / scope["file"]
        data = json.loads(path.read_text("utf8"))
        for patch in scope["patches"]:
            parent, key = pointer_parent(data, patch["pointer"])
            if key == "open_partners" and open_count != patch["value"]:
                continue
            if parent[key] != patch["expected_value"]:
                continue
            archive = data.setdefault("reference_data", {}).setdefault("source_review_round43_metadata", {})
            archive.setdefault(patch["pointer"], parent[key])
            parent[key] = patch["value"]
            changed += 1
        write_atomic(path, data)
    return changed
