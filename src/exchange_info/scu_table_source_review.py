"""Keep SCU roster denominators, annual quotas and exceptional years distinct."""
from __future__ import annotations

from collections import Counter
import hashlib
import json
from pathlib import Path

from .host_source_review_round25 import apply_review_manifest
from .ntust_source_review import write_atomic

MANIFEST = "docs/data-verification-20261021/round27-scu-table-source-review.json"
MANIFEST_SHA256 = "46199aa487c925711ff18d75faeb5f028f031b8bbf448be4cf407ae1509d9aff"


def load_manifest(root: Path):
    raw = (root / MANIFEST).read_bytes()
    if hashlib.sha256(raw).hexdigest() != MANIFEST_SHA256:
        raise ValueError("SCU table review manifest hash mismatch")
    return json.loads(raw)


def apply_scu_table_source_review(root: Path):
    manifest = load_manifest(root)
    changed = apply_review_manifest(root, "scu", manifest, "source_review_round27")
    folder = root / "src/exchange_info/official_data/scu"
    counts = Counter(json.loads(line)["availability_status"] for line in (folder / "partners.jsonl").read_text("utf8").splitlines())
    for filename in ("catalog-completeness.json", "verification_status.json"):
        path = folder / filename
        data = json.loads(path.read_text("utf8"))
        targets = [data] + ([data["counts"]] if "counts" in data else [])
        for target in targets:
            archive = target.setdefault("reference_data", {}).setdefault("source_review_round27", {})
            updates = {"open_partners": counts["open"], "needs_confirmation_partners": counts["needs_confirmation"],
                "whole_partner_records_verified": 0, "verified_at": None, "checked_at": manifest["reviewed_at"],
                "review_note": "本輪僅核對指定母校表格欄位；既有圖片、位置等統計不代表本輪逐筆核實。"}
            if "status" in target:
                updates["status"] = "partial_review"
            for key, value in updates.items():
                if target.get(key) != value:
                    archive.setdefault(key, {"existed": key in target, "value": target.get(key)})
                    target[key] = value
        write_atomic(path, data)
    return changed
