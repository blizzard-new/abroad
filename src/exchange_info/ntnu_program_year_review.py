"""Retain the source term of inspected NTNU program aggregates."""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
from .host_source_review_round25 import apply_review_manifest

MANIFEST = "docs/data-verification-20261021/round38-ntnu-program-year-review.json"
MANIFEST_SHA256 = "af3b984689be9874464a399f248dc0f3404b71d7e7f831eb28e000053b5bcd73"

def load_manifest(root: Path):
    raw = (root / MANIFEST).read_bytes()
    if hashlib.sha256(raw).hexdigest() != MANIFEST_SHA256:
        raise ValueError("NTNU program-year review manifest hash mismatch")
    return json.loads(raw)

def apply_ntnu_program_year_review(root: Path):
    return apply_review_manifest(root, "ntnu", load_manifest(root), "source_review_round38")
