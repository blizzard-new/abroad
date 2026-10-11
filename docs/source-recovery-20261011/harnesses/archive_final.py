from pathlib import Path
import json,hashlib,shutil,re
root=Path('/workspace/recovery-evidence-20261011');target=Path('/workspace/abroad-globe-evidence/docs/source-recovery-20261011');target.mkdir(parents=True,exist_ok=True)
runs=[]
for folder in sorted(root.iterdir()):
 if not folder.is_dir() or not (folder/'metadata.json').exists():continue
 meta=json.loads((folder/'metadata.json').read_text())
 if meta['test_result']=='running':continue
 for name in ('metadata.json','stdout.log','stderr.log','result.xml','results.xml','shard-coverage/partition.json','shard-coverage/collect-nodeids.txt','shard-coverage/result.json','diagnostic-scope.json'):
  p=folder/name
  if p.exists():
   out=target/folder.name/name;out.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,out)
 for script in (folder/'input-scripts').glob('*.py'):
  out=target/folder.name/'input-scripts'/script.name;out.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(script,out)
 text=(folder/'stdout.log').read_text(errors='replace') if (folder/'stdout.log').exists() else ''
 summary=re.findall(r'(?m)^.*\b\d+ (?:passed|failed|skipped).*$',text)
 runs.append({'name':folder.name,'result':meta['test_result'],'exit_code':meta.get('exit_code'),'start_guard':meta['start_guard'],'end_guard':meta.get('end_guard'),'pytest_summary':summary[-1:]})
# Capture only public source results, memory samples, test screenshots and audit reports; never runtime auth/account data.
for folder in root.iterdir():
 if not folder.is_dir():continue
 for p in folder.rglob('*'):
  if not p.is_file() or 'runtime-data' in p.parts:continue
  is_memory='memory' in folder.name and p.name in ('memory-samples.json','server.log')
  is_public=folder.name.endswith('live-source-acceptance') or folder.name in ('photo-license-live','ncu-osaka-live-source')
  is_visual=folder.name.endswith('images') or folder.name.startswith('browser-source-fixtures')
  is_campus_receipt=folder.name=='uc3m-campus-check' and p.name=='receipts.json'
  if is_memory or is_public or is_visual or is_campus_receipt:
   out=target/p.relative_to(root);out.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,out)
for p in root.iterdir():
 if p.is_file() and (p.suffix in ('.json','.log','.txt') or p.name=='ncu-resume-live-ror-sourcepack.json.gz'):
  shutil.copyfile(p,target/p.name)
for p in Path('/workspace/recovery-tools-20261011').iterdir():
 if p.suffix in ('.py','.md'):
  out=target/'harnesses'/p.name;out.parent.mkdir(exist_ok=True);shutil.copyfile(p,out)
shutil.copyfile('/workspace/integration-tools/local_memory_server.py',target/'harnesses/local_memory_server.py')
shutil.copyfile('/workspace/baseline-third-pass-23365f9/source-manifest.json',target/'latest-data-before-source-manifest.json')
manifest=Path('/workspace/recovery-baseline-985224fd/source-manifest.json')
if manifest.exists():shutil.copyfile(manifest,target/'comparison-baseline-source-manifest.json')
(target/'run-index.json').write_text(json.dumps(runs,ensure_ascii=False,indent=2)+'\n')
files=[]
for p in sorted(target.rglob('*')):
 if p.is_file() and p.name!='artifact-manifest.json':files.append({'path':str(p.relative_to(target)),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
(target/'artifact-manifest.json').write_text(json.dumps(files,indent=2)+'\n')
print(json.dumps({'completed_runs':len(runs),'files':len(files),'bytes':sum(f['bytes'] for f in files)}))
