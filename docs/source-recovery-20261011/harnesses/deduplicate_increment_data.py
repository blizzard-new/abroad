"""Coalesce byte-identical immutable evidence/assets in owned historical checkouts."""
from pathlib import Path
import hashlib,json,os,stat,datetime
roots=[Path('/workspace')/p for p in ['abroad-integration','abroad-pr3','abroad-pr4','abroad-pr5','abroad-memory','abroad-memory-followup','abroad-six-final','globe-baseline-59a20f2','memory-fix-probe-20261011','ccu-seventh-fixed-review-capacity-20261011']]
suffixes={'.png','.jpg','.jpeg','.pdf','.zip','.gz','.part','.webp','.woff2','.bin','.json','.jsonl','.csv'}
groups={}; seen_inodes=set(); records=[]; freed=0
for root in roots:
 for relative in ['docs','src/exchange_info/static/assets','src/exchange_info/official_data']:
  for p in (root/relative).rglob('*'):
   if p.is_symlink() or not p.is_file() or p.suffix.lower() not in suffixes:continue
   s=p.stat()
   if s.st_size<16384:continue
   inode=(s.st_dev,s.st_ino)
   if inode in seen_inodes:continue
   seen_inodes.add(inode)
   with p.open('rb') as f:d=hashlib.file_digest(f,'sha256').hexdigest()
   key=(s.st_dev,s.st_size,stat.S_IMODE(s.st_mode),d)
   if key not in groups:groups[key]=p;continue
   prior=groups[key]
   with prior.open('rb') as f:assert hashlib.file_digest(f,'sha256').hexdigest()==d
   with p.open('rb') as f:assert hashlib.file_digest(f,'sha256').hexdigest()==d
   temp=p.with_name(p.name+'.verified-coalesce-tmp');assert not temp.exists()
   os.link(prior,temp);os.replace(temp,p)
   with p.open('rb') as f:assert hashlib.file_digest(f,'sha256').hexdigest()==d
   if s.st_nlink==1:freed+=s.st_blocks*512
   records.append({'retained_path':str(p),'same_bytes_at':str(prior),'sha256':d,'bytes':s.st_size,'original_links':s.st_nlink})
report={'completed_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'scope':'Only task-owned historical checkout binary evidence and source assets; active candidate, environments, configuration, credentials and files outside explicit roots excluded. All paths/content/modes retained. Originals and resulting files hash-verified. No source edits.','file_links_coalesced':len(records),'known_released_blocks_bytes':freed,'records':records}
Path('/workspace/recovery-evidence-20261011/historical-data-deduplication-next1.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({k:v for k,v in report.items() if k!='records'}))
