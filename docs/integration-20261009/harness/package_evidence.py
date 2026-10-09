import hashlib,json,pathlib,shutil
src=pathlib.Path('/workspace/integration-evidence');out=pathlib.Path('/workspace/abroad-evidence/docs/integration-20261009');out.mkdir(parents=True,exist_ok=True)
# Only authored evidence and raw logs/metadata/JUnit; never runtime accounts, vaults, caches or wheel build trees.
for p in src.iterdir():
 if p.is_file() and p.suffix in {'.json','.md','.log','.sql','.png'}:
  shutil.copy2(p,out/p.name)
 elif p.is_dir():
  meta=p/'metadata.json'
  if meta.exists() and json.loads(meta.read_text()).get('test_result')=='running':continue
  for f in p.iterdir():
   if f.is_file() and (f.suffix in {'.json','.xml','.log','.jpg','.sql'} or f.name=='collect-nodeids.txt'):
    dest=out/p.name/f.name;dest.parent.mkdir(exist_ok=True);shutil.copy2(f,dest)
for f in pathlib.Path('/workspace/integration-tools').glob('*.py'):
 dest=out/'harness'/f.name;dest.parent.mkdir(exist_ok=True);shutil.copy2(f,dest)
rows=[]
for f in sorted(out.rglob('*')):
 if f.is_file() and f.name!='file-manifest.json':rows.append({'path':str(f.relative_to(out)),'bytes':f.stat().st_size,'sha256':hashlib.sha256(f.read_bytes()).hexdigest()})
(out/'file-manifest.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2)+'\n');print(len(rows),sum(r['bytes'] for r in rows))
