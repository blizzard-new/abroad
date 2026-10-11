"""Coalesce identical immutable extracted package files in our two task caches."""
from pathlib import Path
import hashlib,json,os,stat,datetime
first=Path('/workspace/integration-tools/uv-cache/archive-v0').resolve()
second=Path('/workspace/.abroad-cloud-tools/uv-cache/archive-v0').resolve()
assert first.is_relative_to('/tmp/abroad-recovery-capacity-20261011') and second.is_relative_to('/tmp/abroad-recovery-capacity-20261011')
def digest(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
index={}
for p in first.rglob('*'):
 if p.is_symlink() or not p.is_file() or '__pycache__' in p.parts or p.suffix in ['.pyc','.lock'] or p.stat().st_size<4096:continue
 s=p.stat();index.setdefault((s.st_size,stat.S_IMODE(s.st_mode),digest(p)),p)
rows=[]
for p in second.rglob('*'):
 if p.is_symlink() or not p.is_file() or '__pycache__' in p.parts or p.suffix in ['.pyc','.lock'] or p.stat().st_size<4096:continue
 s=p.stat();key=(s.st_size,stat.S_IMODE(s.st_mode),digest(p));source=index.get(key)
 if source is None or os.path.samefile(source,p):continue
 before=key[2];temp=p.with_name(p.name+'.owned-dedup-tmp');assert not temp.exists();os.link(source,temp);assert digest(temp)==before;os.replace(temp,p);assert digest(p)==before and os.path.samefile(source,p)
 rows.append({'path':str(p.relative_to(second)),'canonical':str(source.relative_to(first)),'bytes':s.st_size,'sha256':before})
r={'completed_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'scope':'two task-owned uv archive caches only; identical bytes and modes verified before/after atomic hardlink replacement; every path retained; no app/venv/source/wheel/evidence/Docker/config/credentials touched','first':str(first),'second':str(second),'files':rows,'coalesced_files':len(rows),'coalesced_logical_bytes':sum(r['bytes'] for r in rows)}
Path('/workspace/recovery-evidence-20261011/owned-uv-archive-deduplication.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps({k:v for k,v in r.items() if k!='files'}))
