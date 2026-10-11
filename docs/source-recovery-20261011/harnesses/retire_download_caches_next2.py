"""Retire only the task-owned dependency download caches after test completion."""
from pathlib import Path
import json,shutil,hashlib,datetime,subprocess,os
raw=Path('/workspace/recovery-evidence-20261011')
for i in range(4):
 m=json.loads((raw/f'integration-next1-full-shard-{i}/metadata.json').read_text())
 assert m['test_result']!='running'
# The installed interpreter, browser and dependencies must not point into caches.
venv=Path('/workspace/abroad-six-final/.venv')
cache_names=['/workspace/integration-tools/npm-cache','/workspace/integration-tools/uv-cache','/workspace/.abroad-cloud-tools/uv-cache']
roots=[Path(n).resolve() for n in cache_names]
for p in venv.rglob('*'):
 if p.is_symlink():assert not any(p.resolve().is_relative_to(r) for r in roots),str(p)
processes=subprocess.check_output(['ps','-eo','comm='],text=True).splitlines()
assert not any(p.strip() in ['uv','npm','npx'] for p in processes)
records=[]
for alias,root in zip(cache_names,roots):
 assert root.is_relative_to('/tmp/abroad-recovery-capacity-20261011'),str(root)
 rows=[]
 for p in root.rglob('*'):
  if p.is_file() and not p.is_symlink():
   with p.open('rb') as f:d=hashlib.file_digest(f,'sha256').hexdigest()
   rows.append({'path':str(p.relative_to(root)),'bytes':p.stat().st_size,'sha256':d})
 records.append({'alias':alias,'resolved_root':str(root),'files':rows,'logical_bytes':sum(x['bytes'] for x in rows)})
 # No source, environments, original wheels, test/evidence files or Docker state.
 shutil.rmtree(root);root.mkdir()
report={'completed_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'scope':'Only task-created re-downloadable npm/uv caches. Existing aliases retained as empty cache roots. No installed environment, source, wheel artifact, evidence, credential, config or Docker state removed. All currently executing full-suite runs were complete before removal.','records':records}
(raw/'next2-download-cache-retirement.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({'cache_roots':len(records),'logical_bytes':sum(r['logical_bytes'] for r in records)}))
