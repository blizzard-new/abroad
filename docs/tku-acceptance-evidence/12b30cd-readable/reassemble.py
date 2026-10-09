"""Reassemble held evidence using offset/SHA manifests; no network required."""
import argparse,base64,hashlib,json
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('manifest',type=Path);p.add_argument('output',type=Path);a=p.parse_args();m=json.loads(a.manifest.read_text());data=bytearray()
for part in sorted(m['parts'],key=lambda r:r['offset']):
 assert len(data)==part['offset'];raw=base64.b64decode((a.manifest.parent/part['path']).read_bytes());assert len(raw)==part['bytes'] and hashlib.sha256(raw).hexdigest()==part['sha256'];data.extend(raw)
assert len(data)==m['original_bytes'] and hashlib.sha256(data).hexdigest()==m['original_sha256'];a.output.write_bytes(data);print(len(data),hashlib.sha256(data).hexdigest())
