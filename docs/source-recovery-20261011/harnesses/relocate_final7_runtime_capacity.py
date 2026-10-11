"""Preserve owned historical files byte-for-byte while releasing runtime disk space."""
from pathlib import Path
import datetime, hashlib, json, os, shutil

archive=Path('/tmp/abroad-recovery-capacity-20261011')
roots=[Path('/workspace/integration-evidence'),
       Path('/workspace/abroad-integration/sources'),
       Path('/workspace/abroad-integration/docs/ncu-review-index')]
report=[]
def inventory(root):
    rows=[]
    for path in sorted(root.rglob('*')):
        relative=str(path.relative_to(root))
        if path.is_symlink():
            rows.append({'path':relative,'symlink':os.readlink(path)})
        elif path.is_file():
            with path.open('rb') as body: digest=hashlib.file_digest(body,'sha256').hexdigest()
            rows.append({'path':relative,'bytes':path.stat().st_size,'sha256':digest})
    return rows

for index,source in enumerate(roots):
    assert source.is_dir() and not source.is_symlink(),source
    dest=archive/f'final7-historical-runtime-space-{index}'
    assert not dest.exists()
    before=inventory(source)
    shutil.copytree(source,dest,symlinks=True)
    assert inventory(dest)==before
    shutil.rmtree(source)
    source.symlink_to(dest,target_is_directory=True)
    assert inventory(source)==before
    record={'original_path_preserved_as_symlink':str(source),'storage_path':str(dest),
            'entries':len(before),'file_bytes':sum(r.get('bytes',0) for r in before),
            'all_file_hashes_and_symlinks_equal':True,'manifest_sha256':hashlib.sha256(json.dumps(before,sort_keys=True).encode()).hexdigest()}
    report.append(record)
    Path('/workspace/recovery-evidence-20261011/final7-historical-runtime-relocation.json').write_text(json.dumps({'scope':'Only owned completed historical source/evidence trees. All paths and bytes preserved; no Docker prune, daemon/config, production or active candidate modification.','completed_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'records':report},indent=2)+'\n')
    print(json.dumps(record),flush=True)
