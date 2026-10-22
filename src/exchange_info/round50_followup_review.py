"""Round 50 NCKU Yonsei Mirae campus identity and Waseda WBS/NCKU follow-up review."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from .host_source_review_round25 import apply_review_manifest

MANIFEST = "docs/data-verification-20261021/round50-ncku-waseda-followup-review.json"
MANIFEST_SHA256 = "7f81650a7690ad79467f843c2e643b7b68aa143a22752345d0f7ab1ada041fe4"
ARCHIVE_KEY = "source_review_round50"
HOMES = ("ncku", "ntust", "ntu", "nccu")


def load_manifest(root: Path) -> dict:
    raw = (root / MANIFEST).read_bytes()
    if hashlib.sha256(raw).hexdigest() != MANIFEST_SHA256:
        raise ValueError("Round 50 follow-up review manifest hash mismatch")
    return json.loads(raw)


def apply_round50_followup_review(
    root: Path, home: str | None = None, *, bundle: Path | None = None
) -> int:
    manifest = load_manifest(root)
    targets = (home,) if home is not None else HOMES
    changed = 0
    for school in targets:
        school_manifest = dict(manifest)
        if bundle is not None:
            scopes = []
            for scope in manifest["rows"]:
                if scope["home_id"] == school:
                    s_copy = dict(scope)
                    s_copy["file"] = str((bundle / Path(scope["file"]).name).resolve())
                    scopes.append(s_copy)
            school_manifest["rows"] = scopes
        changed += apply_review_manifest(
            root, school, school_manifest, ARCHIVE_KEY, manage_profile_context=False
        )
    return changed
