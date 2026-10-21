"""Keep FJU's reference-table routes separate and retain evidence boundaries."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from .host_source_review_round25 import apply_review_manifest

MANIFEST = 'docs/data-verification-20261021/round46-fju-route-source-review.json'
MANIFEST_SHA256 = 'e710fe9d14ee07a2f596eaf51d310733e12adf95ebaff90ca40bebb549dc5d24'
ARCHIVE_KEY = 'source_review_round46'


def load_manifest(root: Path) -> dict:
    raw = (root / MANIFEST).read_bytes()
    if hashlib.sha256(raw).hexdigest() != MANIFEST_SHA256:
        raise ValueError('FJU route review manifest hash mismatch')
    return json.loads(raw)


def apply_fju_route_review(root: Path, *, bundle: Path | None = None) -> int:
    manifest = load_manifest(root)
    loaded = {}
    for scope in manifest['rows']:
        path = bundle / Path(scope['file']).name if bundle is not None else root / scope['file']
        if path not in loaded:
            loaded[path] = [json.loads(line) for line in path.read_text('utf8').splitlines() if line.strip()]
        matches = [row for row in loaded[path] if (row.get('school_name'), row.get('country')) ==
                   (scope['school_name'], scope['country'])]
        if len(matches) != 1:
            raise ValueError(f'FJU route must match exactly once: {scope["school_name"]}/{path.name}')
        scope['file'] = str(path.resolve())
    return apply_review_manifest(root, 'fju', manifest, ARCHIVE_KEY, manage_profile_context=False)
