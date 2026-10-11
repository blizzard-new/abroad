from pathlib import Path
import hashlib,json,os,subprocess,sys
root=Path(sys.argv[1]);manifest=root/'source-manifest.json';expected=json.loads(manifest.read_text())
def check():
 bad=[r['path'] for r in expected['files'] if hashlib.sha256((root/r['path']).read_bytes()).hexdigest()!=r['sha256']]
 assert not bad,bad
 return {'source_sha':expected['sha'],'files':len(expected['files']),'manifest_sha256':hashlib.sha256(manifest.read_bytes()).hexdigest(),'mismatches':0}
print(json.dumps({'snapshot_start':check()}),flush=True)
os.chdir(root)
result=subprocess.call([sys.executable,*sys.argv[2:]])
print(json.dumps({'snapshot_end':check()}),flush=True)
raise SystemExit(result)
