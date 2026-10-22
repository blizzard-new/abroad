"""Replay the bounded USP source corrections without replacing later edits."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from .ntust_source_review import write_atomic
from .life_claim_review import life_claim_key

MANIFEST = "docs/data-verification-20261021/round23-usp-source-review.json"
MANIFEST_SHA256 = "cfd2a452391cf5b683fe2969c6ddfe7762dd6bce4f928b9f113c3210526a8689"


def load_manifest(root: Path):
    raw = (root / MANIFEST).read_bytes()
    if hashlib.sha256(raw).hexdigest() != MANIFEST_SHA256:
        raise ValueError("USP source-review manifest hash mismatch")
    return json.loads(raw)


def pointer_parent(row, pointer):
    parts = [part.replace("~1", "/").replace("~0", "~") for part in pointer.split("/")[1:]]
    parent = row
    for part in parts[:-1]:
        parent = parent[int(part)] if isinstance(parent, list) else parent[part]
    key = int(parts[-1]) if isinstance(parent, list) else parts[-1]
    return parent, key


def apply_usp_source_review(root: Path, school: str, *, bundle: Path | None = None, rebuild=False):
    manifest = load_manifest(root)
    changed = 0
    for scope in manifest["rows"]:
        if scope["home_id"] != school:
            continue
        path = bundle / Path(scope["file"]).name if bundle is not None else root / scope["file"]
        rows = [json.loads(line) for line in path.read_text("utf8").splitlines() if line.strip()]
        for row in rows:
            if (row.get("school_name"), row.get("country")) != (scope["school_name"], scope["country"]):
                continue
            evidence_changed = False
            for patch in scope["patches"]:
                try:
                    parent, key = pointer_parent(row, patch["pointer"])
                    previous = parent[key]
                except (KeyError, IndexError, TypeError, ValueError):
                    continue
                replacement = patch["value"]
                if patch["pointer"] == "/evidence":
                    # Earlier build stages can already have removed part of the
                    # old bundle. Preserve independent additions in either case.
                    known = set(manifest["runtime_index"]["life_claim_keys"])
                    keep = [item for item in previous if life_claim_key(
                        row["school_name"], row["country"], item) not in known]
                    if len(keep) == len(previous):
                        continue
                    if rebuild:
                        # Pydantic serializes UTC as Z; the pinned audit stores
                        # the equivalent +00:00 form. Keep stable replay bytes.
                        canonical = manifest["reviewed_at"]
                        keep = [{**item, "checked_at": canonical}
                            if item.get("checked_at") == canonical.replace("+00:00", "Z") else item
                            for item in keep]
                    existing = {life_claim_key(row["school_name"], row["country"], item) for item in keep}
                    replacement = keep + [item for item in replacement if life_claim_key(
                        row["school_name"], row["country"], item) not in existing]
                    evidence_changed = True
                elif (scope["file"].endswith("/student_life.jsonl")
                      and patch["pointer"] in {"/notes", "/checked_at"} and not evidence_changed):
                    continue
                elif (rebuild and evidence_changed and patch["pointer"] in {"/notes", "/checked_at"}):
                    pass
                elif previous == replacement or previous not in patch["expected_values"]:
                    continue
                references = row.setdefault("reference_data", {})
                archive = references.get("source_review_round23", {})
                if isinstance(archive, str):
                    archive = json.loads(archive)
                archive.setdefault(patch["pointer"], previous)
                # PartnerUniversity keeps reference_data values as strings.
                references["source_review_round23"] = (json.dumps(archive, ensure_ascii=False)
                    if scope["file"].endswith("/partners.jsonl") else archive)
                parent[key] = replacement
                changed += 1
            if rebuild and evidence_changed:
                # A fresh build replays historical stages that discard unknown
                # model fields. Restore the original audit snapshot consistently.
                row.setdefault("reference_data", {})["source_review_round23"] = {
                    patch["pointer"]: patch["expected_values"][0] for patch in scope["patches"]}
        write_atomic(path, rows, True)
    return changed
