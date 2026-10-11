"""Preserve owned tools/artifacts on the larger tmp filesystem, with stable symlinks."""
from pathlib import Path
import datetime,hashlib,json,os,shutil,sys

target_root=Path('/tmp/abroad-recovery-capacity-20261011');target_root.mkdir(exist_ok=True)
receipt=Path('/workspace/recovery-evidence-20261011/owned-artifact-relocations.json')
records=json.loads(receipt.read_text()) if receipt.exists() else []
allowed={
 '/workspace/integration-tools/npm-cache',
 '/workspace/integration-tools/tku-handoff',
 '/workspace/integration-tools/tku-evidence-handoff.tar',
 '/workspace/integration-tools/browsers',
 '/workspace/integration-tools/uv-cache',
 '/workspace/.abroad-cloud-tools/uv-cache',
 '/workspace/abroad-globe-evidence',
}
def digest(path):
    with path.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
for name in sys.argv[1:]:
    assert name in allowed,name
    src=Path(name);assert src.exists() and not src.is_symlink(),name
    dest=target_root/(src.parent.name+'-'+src.name);assert not dest.exists(),str(dest)
    if src.is_dir():shutil.copytree(src,dest,symlinks=True)
    else:shutil.copy2(src,dest)
    pairs=[(src,dest)] if src.is_file() else [(p,dest/p.relative_to(src)) for p in src.rglob('*')]
    verified=0;bytes_=0
    for old,new in pairs:
        if old.is_symlink():assert new.is_symlink() and os.readlink(old)==os.readlink(new)
        elif old.is_file():
            assert old.stat().st_size==new.stat().st_size and digest(old)==digest(new),str(old)
            verified+=1;bytes_+=old.stat().st_size
    backup=src.with_name(src.name+'.owned-relocation-original');assert not backup.exists()
    src.rename(backup);src.symlink_to(dest,target_is_directory=dest.is_dir())
    if backup.is_dir():shutil.rmtree(backup)
    else:backup.unlink()
    records.append({'source_path_preserved_by_symlink':str(src),'storage_path':str(dest),'files_hash_verified':verified,'logical_bytes':bytes_,'completed_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'scope':'Owned test tools/evidence only; no app source, Docker settings, external service, credential, user data or production state changed.'})
    receipt.write_text(json.dumps(records,indent=2)+'\n')
    print(json.dumps(records[-1]),flush=True)
