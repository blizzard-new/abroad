"""Round 49 FJU host-source reviews and legacy deposit/cost unification."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from .fju_briefing_review import apply_scoped_briefing_manifest

MANIFEST = "docs/data-verification-20261021/round49-fju-host-and-cost-review.json"
MANIFEST_SHA256 = "c6d9b4052d04dc76ac611f2c58014da30304ab64a142b6a665424fdfaa7de681"
ARCHIVE_KEY = "source_review_round49_host"


def load_manifest(root: Path) -> dict:
    raw = (root / MANIFEST).read_bytes()
    if hashlib.sha256(raw).hexdigest() != MANIFEST_SHA256:
        raise ValueError("FJU host review manifest hash mismatch")
    return json.loads(raw)


def apply_fju_host_review(root: Path, *, bundle: Path | None = None) -> int:
    return apply_scoped_briefing_manifest(root, load_manifest(root), ARCHIVE_KEY, bundle=bundle)
