from pathlib import Path
import shutil,hashlib,json,datetime
alias=Path('/workspace/integration-next1-wheel-artifacts-20261011');src=alias.resolve();dest=Path('/workspace/historical-wheel-anchor-disk-20261011');assert not dest.exists();dest.mkdir()
files=[]
for p in src.iterdir():
 assert p.is_file();q=dest/p.name;shutil.copy2(p,q)
 with p.open('rb')as f:a=hashlib.file_digest(f,'sha256').hexdigest()
 with q.open('rb')as f:b=hashlib.file_digest(f,'sha256').hexdigest()
 assert a==b;files.append({'name':p.name,'bytes':p.stat().st_size,'sha256':a})
assert len(files)==1 and files[0]['sha256']=='682c304eaa6926b56a8ab675f601755b907b7a7d4601686d6640002c446e45a4'
for p in src.iterdir():p.unlink()
src.rmdir();src.symlink_to(dest,target_is_directory=True)
Path('/workspace/recovery-evidence-20261011/final4-wheel-anchor-memory-relocation.json').write_text(json.dumps({'stable_alias':str(alias),'old_storage_alias_preserved':str(src),'new_storage':str(dest),'files':files,'reason':'Release900MiB tmpfs memory during unchanged browser tests; no artifact deletion, content/test/config changes. Can move back after browsers finish for runtime disk space.','completed_at':datetime.datetime.now(datetime.timezone.utc).isoformat()},indent=2)+'\n');print(files)
