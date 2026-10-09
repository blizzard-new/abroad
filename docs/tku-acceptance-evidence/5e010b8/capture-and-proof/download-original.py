import argparse,hashlib,json,zipfile
from datetime import datetime,timezone
from pathlib import Path
import requests
p=argparse.ArgumentParser();p.add_argument('--record',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();d=json.loads(a.record.read_text());a.output.mkdir(parents=True,exist_ok=True)
response=requests.get(d['url'],timeout=90)
print(json.dumps({'artifact_id':d['artifact_id'],'http_status':response.status_code}),flush=True)
response.raise_for_status()  # Any denied path is stopped; no fallback, token or rights changes.
raw=response.content;sha=hashlib.sha256(raw).hexdigest();assert sha==d['expected_sha256']
target=a.output/f"{d['artifact_id']}.zip"
if target.exists():assert target.read_bytes()==raw
else:target.write_bytes(raw)
folder=a.output/str(d['artifact_id'])
if not folder.exists():
 folder.mkdir()
 with zipfile.ZipFile(target) as z:
  for name in z.namelist():assert (folder/name).resolve().is_relative_to(folder.resolve())
  z.extractall(folder)
with zipfile.ZipFile(target) as z:
 for name in z.namelist():
  if not name.endswith('/'):assert z.read(name)==(folder/name).read_bytes()
proof={'artifact_id':d['artifact_id'],'retrieved_at':datetime.now(timezone.utc).isoformat(),'http_status':response.status_code,'zip_bytes':len(raw),'original_zip_sha256':sha,'published_digest_matched':True,'all_extracted_members_byte_identical':True,'artifact_bytes_reconstructed':False}
(a.output/f"{d['artifact_id']}-download-proof.json").write_text(json.dumps(proof,indent=2)+'\n')
print(json.dumps(proof))
