"""Keep current nomination months distinct from final admission and exact dates."""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
from .fju_briefing_review import apply_scoped_briefing_manifest
MANIFEST='docs/data-verification-20261021/round48-fju-process-review.json'
MANIFEST_SHA256='dfdbe0fa564ecdc1512a266b29685480a77e23fd481bc9500efccf77dfa10c7b'
ARCHIVE_KEY='source_review_round48_process'

def load_manifest(root: Path) -> dict:
    raw=(root/MANIFEST).read_bytes()
    if hashlib.sha256(raw).hexdigest()!=MANIFEST_SHA256:
        raise ValueError('FJU process manifest hash mismatch')
    return json.loads(raw)

def apply_fju_process_review(root: Path, *, bundle: Path | None = None) -> int:
    return apply_scoped_briefing_manifest(root,load_manifest(root),ARCHIVE_KEY,bundle=bundle)
