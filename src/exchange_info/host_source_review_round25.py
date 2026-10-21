"""Scoped, value-guarded admissions corrections for Pittsburg and Kurume."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from .ntust_source_review import write_atomic

MANIFEST = "docs/data-verification-20261021/round25-host-source-review.json"
MANIFEST_SHA256 = "415d4528f21c80377144d8028533632cb43d820b8564b4abe22a9091bb60c242"


def load_manifest(root: Path):
    raw = (root / MANIFEST).read_bytes()
    if hashlib.sha256(raw).hexdigest() != MANIFEST_SHA256:
        raise ValueError("Round 25 source-review manifest hash mismatch")
    return json.loads(raw)


def pointer_parent(row, pointer, *, create=False):
    parts = [part.replace("~1", "/").replace("~0", "~") for part in pointer.split("/")[1:]]
    parent = row
    for part in parts[:-1]:
        if isinstance(parent, list):
            parent = parent[int(part)]
        else:
            if create and part not in parent:
                parent[part] = {}
            parent = parent[part]
    return parent, int(parts[-1]) if isinstance(parent, list) else parts[-1]


def apply_host_source_review(root: Path, school: str):
    """Only change inspected variants; keep independent later edits intact."""
    return apply_review_manifest(root, school, load_manifest(root), "source_review_round25")


def apply_review_manifest(root: Path, school: str, manifest: dict, archive_key: str, *, manage_profile_context: bool = True):
    """Replay a separately pinned manifest with its own original-value archive."""
    changed = 0
    loaded_files = {}
    for scope in manifest["rows"]:
        if scope["home_id"] != school:
            continue
        path = root / scope["file"]
        if path not in loaded_files:
            loaded_files[path] = [json.loads(line) for line in path.read_text("utf8").splitlines() if line.strip()]
        rows = loaded_files[path]
        for row in rows:
            if (row.get("school_name"), row.get("country")) != (scope["school_name"], scope["country"]):
                continue
            for patch in scope["patches"]:
                try:
                    parent, key = pointer_parent(row, patch["pointer"])
                    previous, exists = parent[key], True
                except (KeyError, IndexError):
                    previous, exists = None, False
                except (TypeError, ValueError):
                    continue
                if exists:
                    if previous == patch["value"] or previous not in patch["expected_values"]:
                        continue
                elif not patch["expected_missing"]:
                    continue
                try:
                    parent, key = pointer_parent(row, patch["pointer"], create=True)
                except (TypeError, ValueError, IndexError):
                    continue
                references = row.setdefault("reference_data", {})
                archive = references.get(archive_key, {})
                if isinstance(archive, str):
                    archive = json.loads(archive)
                archive.setdefault(patch["pointer"], {"existed": exists, "value": previous})
                references[archive_key] = (json.dumps(archive, ensure_ascii=False)
                    if path.name == "partners.jsonl" else archive)
                parent[key] = patch["value"]
                changed += 1
            if path.name == "destination_profiles.jsonl" and manage_profile_context:
                # New inspected text must not inherit an old whole-profile
                # verification stamp or omit the source of its correction.
                archive = row.get("reference_data", {}).get(archive_key, {})
                if archive and "__profile_source_context" not in archive:
                    archive["__profile_source_context"] = {key: row.get(key) for key in
                        ("sources", "last_checked", "coverage_status", "coverage_note")}
                    sources = list(row.get("sources", []))
                    present = {item["source_url"] for item in sources}
                    for patch in scope["patches"]:
                        url = patch.get("source_url")
                        if url and url not in present:
                            sources.append({"title": "指定欄位查核來源", "source_url": url,
                                "summary": patch["reason"]})
                            present.add(url)
                    row["sources"] = sources
                    row["last_checked"] = manifest["reviewed_at"]
                    row["coverage_status"] = "official_partial"
                    row["coverage_note"] = "本輪僅修正指定欄位並核對其來源；其餘生活內容仍待查核。"
    for path, rows in loaded_files.items():
        write_atomic(path, rows, True)
    return changed
