from pathlib import Path
import shutil,hashlib,json,datetime,os
raw=Path('/workspace/recovery-evidence-20261011')
for i in range(4):assert json.loads((raw/f'integration-next1-full-shard-{i}/metadata.json').read_text())['test_result']!='running'
src=Path('/workspace/integration160-wheel-artifacts-20261011');dest=Path('/tmp/abroad-recovery-capacity-20261011/integration160-wheel-artifacts-20261011')
assert src.is_dir() and not src.is_symlink() and not dest.exists()
files=[p for p in src.rglob('*') if p.is_file()];assert len(files)==1 and files[0].suffix=='.whl'
assert shutil.disk_usage(dest.parent).free>files[0].stat().st_size+150*1024*1024
report=[]
shutil.copytree(src,dest)
for old in files:
 new=dest/old.relative_to(src)
 with old.open('rb') as f:a=hashlib.file_digest(f,'sha256').hexdigest()
 with new.open('rb') as f:b=hashlib.file_digest(f,'sha256').hexdigest()
 assert a==b
 report.append({'path':str(old),'preserved_at':str(new),'bytes':old.stat().st_size,'sha256':a})
backup=src.with_name(src.name+'.completed-relocation-original');assert not backup.exists()
src.rename(backup);src.symlink_to(dest,target_is_directory=True);shutil.rmtree(backup)
for row in report:
 with Path(row['path']).open('rb') as f:assert hashlib.file_digest(f,'sha256').hexdigest()==row['sha256']
(raw/'next2-prior160-wheel-preserved-relocation.json').write_text(json.dumps({'completed_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'scope':'Only completed owned wheel moved across local filesystems; every byte verified, original path preserved by symlink; no artifact loss.','files':report},indent=2)+'\n')
print(json.dumps(report))
