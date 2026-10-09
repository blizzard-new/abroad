import hashlib,json
from pathlib import Path
root=Path(__file__).resolve().parent
manifest=json.loads((root/'manifest.json').read_text())
for row in manifest['files']:
 data=(root/row['path']).read_bytes()
 assert len(data)==row['bytes'] and hashlib.sha256(data).hexdigest()==row['sha256'],row['path']
print(f"Verified {len(manifest['files'])} evidence files at {manifest['tested_commit']}; checksum success is not full acceptance.")
