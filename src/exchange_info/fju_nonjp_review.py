"""Mother reference table review; clipped and conflicting fields stay uncertain."""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
from .host_source_review_round25 import apply_review_manifest

MANIFEST = 'docs/data-verification-20261021/round48-fju-nonjp-review.json'
MANIFEST_SHA256 = 'd7cb1fc6adcd329dc99cc9210ed69882b9965119ee3be7a729c94b4d6e1610ba'
ARCHIVE_KEY = 'source_review_round48_nonjp'


def load_manifest(root: Path) -> dict:
    raw = (root / MANIFEST).read_bytes()
    if hashlib.sha256(raw).hexdigest() != MANIFEST_SHA256:
        raise ValueError('FJU non-Japanese table manifest hash mismatch')
    return json.loads(raw)


def apply_fju_nonjp_review(root: Path, *, bundle: Path | None = None) -> int:
    manifest = load_manifest(root)
    loaded = {}
    for scope in manifest['rows']:
        path = bundle / Path(scope['file']).name if bundle is not None else root / scope['file']
        if path not in loaded:
            loaded[path] = [json.loads(line) for line in path.read_text('utf8').splitlines() if line.strip()]
        matches = [row for row in loaded[path] if (row.get('school_name'), row.get('country')) ==
                   (scope['school_name'], scope['country'])]
        if len(matches) != 1:
            raise ValueError(f'FJU non-Japanese route must match exactly once: {scope["school_name"]}')
        scope['file'] = str(path.resolve())
    return apply_review_manifest(root, 'fju', manifest, ARCHIVE_KEY, manage_profile_context=False)
