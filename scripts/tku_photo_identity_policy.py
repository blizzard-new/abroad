"""Explicit fixed-photo withdrawals override stale visual/date passes."""
import json
if __package__:
 from .tku_capture_io import BUNDLE
else:
 from tku_capture_io import BUNDLE

def apply_photo_identity_policy(records):
 path=BUNDLE/'fixed_photo_blocker_holds.json'
 if not path.exists():return records
 holds={r['id']:r for r in json.loads(path.read_text())['schools']}
 return [r for r in records if not (r['id'] in holds and r.get('sha256')==holds[r['id']]['withdrawn_photo_sha256'])]
