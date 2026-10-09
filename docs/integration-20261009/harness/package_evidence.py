import gzip,hashlib,json,pathlib,shutil
src=pathlib.Path('/workspace/integration-evidence');out=pathlib.Path('/workspace/abroad-evidence/docs/integration-20261009');out.mkdir(parents=True,exist_ok=True)
compressed=[]
def copy_evidence(source,destination):
 if source.stat().st_size <= 50*1024*1024:
  shutil.copy2(source,destination)
  return
 # GitHub rejects individual blobs over 100 MiB. Preserve exact raw bytes in
 # deterministic lossless gzip, with both raw and delivered SHA256 recorded.
 delivered=destination.with_name(destination.name+'.gz')
 with source.open('rb') as raw,delivered.open('wb') as packed:
  with gzip.GzipFile(filename='',mode='wb',fileobj=packed,mtime=0) as stream:
   shutil.copyfileobj(raw,stream)
 raw_sha=hashlib.sha256(source.read_bytes()).hexdigest()
 with gzip.open(delivered,'rb') as stream:
  assert hashlib.sha256(stream.read()).hexdigest()==raw_sha
 compressed.append({'raw_path':str(destination.relative_to(out)), 'raw_bytes':source.stat().st_size,
                    'raw_sha256':raw_sha,'delivered_path':str(delivered.relative_to(out)),
                    'delivered_sha256':hashlib.sha256(delivered.read_bytes()).hexdigest()})
 if destination.exists():
  assert hashlib.sha256(destination.read_bytes()).hexdigest()==raw_sha
  destination.unlink()  # only the verified staging copy; original raw remains
# Only authored evidence and raw logs/metadata/JUnit; never runtime accounts, vaults, caches or wheel build trees.
for p in src.iterdir():
 if p.is_file() and p.suffix in {'.json','.md','.log','.sql','.png','.patch'}:
  copy_evidence(p,out/p.name)
 elif p.is_dir():
  meta=p/'metadata.json'
  if meta.exists() and json.loads(meta.read_text()).get('test_result')=='running':continue
  for f in p.iterdir():
   if f.is_file() and (f.suffix in {'.json','.xml','.log','.jpg','.sql'} or f.name=='collect-nodeids.txt'):
    dest=out/p.name/f.name;dest.parent.mkdir(exist_ok=True);copy_evidence(f,dest)
for f in pathlib.Path('/workspace/integration-tools').glob('*.py'):
 dest=out/'harness'/f.name;dest.parent.mkdir(exist_ok=True);shutil.copy2(f,dest)
(out/'lossless-compression-manifest.json').write_text(json.dumps(compressed,indent=2)+'\n')
rows=[]
for f in sorted(out.rglob('*')):
 if f.is_file() and f.name!='file-manifest.json':rows.append({'path':str(f.relative_to(out)),'bytes':f.stat().st_size,'sha256':hashlib.sha256(f.read_bytes()).hexdigest()})
(out/'file-manifest.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2)+'\n');print(len(rows),sum(r['bytes'] for r in rows))
