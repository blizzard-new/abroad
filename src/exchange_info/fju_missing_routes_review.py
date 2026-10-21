"""Append independently named FJU self-funded reference routes without guessing gaps."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from .ntust_source_review import write_atomic
from .school_identity import school_program_identity_key

MANIFEST = 'docs/data-verification-20261021/round47-fju-missing-routes.json'
MANIFEST_SHA256 = 'c1875524cd56c1bf94ecf866a8105855370a09291b0edfa9d6926a63b836a3b6'


def load_manifest(root: Path) -> dict:
    raw = (root / MANIFEST).read_bytes()
    if hashlib.sha256(raw).hexdigest() != MANIFEST_SHA256:
        raise ValueError('FJU added-route manifest hash mismatch')
    return json.loads(raw)


def apply_fju_missing_routes(root: Path, *, bundle: Path | None = None) -> int:
    manifest = load_manifest(root)
    folder = bundle if bundle is not None else root / 'src/exchange_info/official_data/fju'
    files = {}
    added = 0
    for scope in manifest['records']:
        path = folder / Path(scope['file']).name
        if path not in files:
            files[path] = [json.loads(line) for line in path.read_text('utf8').splitlines() if line.strip()]
        key = (school_program_identity_key(scope['school_name']), scope['country'])
        matches = [r for r in files[path] if (school_program_identity_key(r['school_name']), r.get('country')) == key]
        if len(matches) > 1 or (matches and matches[0]['school_name'] != scope['school_name']):
            raise ValueError(f'Ambiguous added FJU route: {scope["school_name"]}')
        if matches:
            # Later independent reviews are authoritative, never reset them.
            continue
        files[path].append(scope['data'])
        added += 1
    for path, rows in files.items():
        write_atomic(path, rows, True)
    partners = files[folder / 'partners.jsonl']
    for filename in ('catalog-completeness.json', 'verification_status.json'):
        path = folder / filename
        row = json.loads(path.read_text('utf8'))
        counts = row['counts'] if filename == 'verification_status.json' else row
        counts['total_partners'] = len(partners)
        counts['overseas_partners'] = sum(p.get('country') not in ('中國大陸', '香港', '澳門') for p in partners)
        counts['added_self_funded_reference_plans'] = 3
        counts['count_unit_note'] = '計算方案列，不是不同機構數；新增自費方案不增加已核實校區、圖片或網站數。'
        write_atomic(path, row, False)
    path = folder / 'exchange_info.json'
    info = json.loads(path.read_text('utf8'))
    info['partner_universities'] = [p['school_name'] for p in partners]
    write_atomic(path, info, False)
    return added
