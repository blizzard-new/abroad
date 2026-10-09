"""Reassemble already-held evidence bytes; no network or third-party modules."""
import argparse,base64,hashlib,json
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('manifest',type=Path);p.add_argument('output',type=Path);a=p.parse_args();m=json.loads(a.manifest.read_text());result=[]
for part in sorted(m['parts'],key=lambda r:r['sequence']):
 encoded=(a.manifest.parent/part['file']).read_bytes();assert len(encoded)==part['encoded_bytes'] and hashlib.sha256(encoded).hexdigest()==part['encoded_sha256'];raw=base64.b64decode(encoded,validate=False);assert len(raw)==part['raw_bytes'] and hashlib.sha256(raw).hexdigest()==part['raw_sha256'];result.append(raw)
data=b''.join(result);assert len(data)==m['original_bytes'] and hashlib.sha256(data).hexdigest()==m['original_sha256'];a.output.write_bytes(data);print(len(data),hashlib.sha256(data).hexdigest())
