from pathlib import Path
import hashlib,json,os,stat,datetime
active=Path('/workspace/abroad-globe-20261011')
roots=[active,*[Path('/workspace')/p for p in ['abroad-pr5','abroad-evidence','memory-fix-probe-20261011','globe-baseline-59a20f2']]]
suffixes={'.png','.jpg','.jpeg','.pdf','.zip','.gz','.woff2','.woff','.ttf','.xlsx','.docx','.doc','.webp'}
index={};rows=[];freed=0
for root in roots:
 for relative in ['docs','src/exchange_info/static/assets','src/exchange_info/official_data','sources','output']:
  for p in (root/relative).rglob('*'):
   if p.is_symlink() or not p.is_file() or p.suffix.lower() not in suffixes:continue
   s=p.stat()
   if s.st_size<16384:continue
   with p.open('rb') as f:d=hashlib.file_digest(f,'sha256').hexdigest()
   key=(s.st_dev,s.st_size,stat.S_IMODE(s.st_mode),d);source=index.get(key)
   if source is None:index[key]=p;continue
   if root==active or os.path.samefile(source,p):continue
   with source.open('rb') as f:assert hashlib.file_digest(f,'sha256').hexdigest()==d
   temp=p.with_name(p.name+'.verified-historical-link');assert not temp.exists();os.link(source,temp);os.replace(temp,p)
   with p.open('rb') as f:assert hashlib.file_digest(f,'sha256').hexdigest()==d
   if s.st_nlink==1:freed+=s.st_blocks*512
   rows.append({'historical_path':str(p),'same_immutable_bytes_at':str(source),'bytes':s.st_size,'sha256':d})
r={'completed_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'scope':'Only relocated historical immutable binary source/evidence files coalesced; active candidate indexed read-only and never replaced; no mutable JSON/code/environment/Git metadata changed.','files':rows,'known_released_blocks_bytes':freed}
Path('/workspace/recovery-evidence-20261011/relocated-historical-binary-coalescing.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps({'files':len(rows),'known_released_blocks_bytes':freed}))
