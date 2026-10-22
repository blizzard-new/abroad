"""Withdraw only inspected SCU template assumptions from receiving-school facts."""
import hashlib
import json
from pathlib import Path

from .host_source_review_round25 import apply_review_manifest

MANIFEST = "docs/data-verification-20261021/round30-scu-template-source-review.json"
MANIFEST_SHA256 = "32c1af19f16ac9bd04da5101167dd8c721fd3a020cc4ceeaac26381f7b0b77fe"


def load_manifest(root: Path):
    raw = (root / MANIFEST).read_bytes()
    if hashlib.sha256(raw).hexdigest() != MANIFEST_SHA256:
        raise ValueError("SCU template source-review manifest hash mismatch")
    return json.loads(raw)


def apply_scu_template_source_review(root: Path):
    return apply_review_manifest(root, "scu", load_manifest(root), "source_review_round30")
