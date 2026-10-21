"""Host references retain their own intake and do not override mother rules."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from .host_source_review_round25 import apply_review_manifest

MANIFEST = 'docs/data-verification-20261021/round45-vilnius-akita-review.json'
MANIFEST_SHA256 = '88a52974cdac2766992981d310e5662a94cdd4eff559ce054fd484b37f18810a'
ARCHIVE_KEY = 'source_review_round45'
COST_MANIFEST = 'docs/data-verification-20261021/round45-cost-applicability-followup.json'
COST_SHA256 = '9fc777852937163d0c5f79f0a4261ed101932ad202abc98f4fd22b1fe63e760f'


def load_manifest(root: Path) -> dict:
    raw = (root / MANIFEST).read_bytes()
    if hashlib.sha256(raw).hexdigest() != MANIFEST_SHA256:
        raise ValueError('Vilnius/Akita source-review manifest hash mismatch')
    return json.loads(raw)


def apply_vilnius_akita_review(root: Path, home: str, *, bundle: Path | None = None) -> int:
    """Replay only inspected old values, including custom builder output folders."""
    manifest = load_manifest(root)
    cost_raw = (root / COST_MANIFEST).read_bytes()
    if hashlib.sha256(cost_raw).hexdigest() != COST_SHA256:
        raise ValueError('Vilnius/Akita cost applicability manifest hash mismatch')
    scopes = [scope for scope in manifest['rows'] + json.loads(cost_raw)['rows'] if scope['home_id'] == home]
    if not scopes:
        raise ValueError(f'No reviewed Vilnius/Akita records for {home}')
    loaded = {}
    for scope in scopes:
        path = bundle / Path(scope['file']).name if bundle is not None else root / scope['file']
        if path not in loaded:
            loaded[path] = [json.loads(line) for line in path.read_text('utf8').splitlines() if line.strip()]
        matches = [row for row in loaded[path] if (row.get('school_name'), row.get('country')) ==
                   (scope['school_name'], scope['country'])]
        if len(matches) != 1:
            raise ValueError(f'Review identity must match exactly once: {home}/{scope["school_name"]}/{path.name}')
        scope['file'] = str(path.resolve())
    manifest['rows'] = scopes
    return apply_review_manifest(root, home, manifest, ARCHIVE_KEY, manage_profile_context=False)
