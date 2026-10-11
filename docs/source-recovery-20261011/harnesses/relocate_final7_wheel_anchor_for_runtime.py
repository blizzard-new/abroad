from pathlib import Path
import datetime, hashlib, json, shutil

alias=Path('/workspace/integration-next1-wheel-artifacts-20261011')
source=alias.resolve()
target=Path('/tmp/abroad-recovery-capacity-20261011/final7-wheel-anchor-runtime')
assert str(source)=='/workspace/historical-wheel-anchor-disk-20261011'
assert not target.exists()
target.mkdir()
rows=[]
for path in source.iterdir():
    assert path.is_file()
    copied=target/path.name
    shutil.copy2(path,copied)
    with path.open('rb') as body: before=hashlib.file_digest(body,'sha256').hexdigest()
    with copied.open('rb') as body: after=hashlib.file_digest(body,'sha256').hexdigest()
    assert before==after=='682c304eaa6926b56a8ab675f601755b907b7a7d4601686d6640002c446e45a4'
    rows.append({'name':path.name,'bytes':path.stat().st_size,'sha256':before})
assert len(rows)==1
for path in source.iterdir():path.unlink()
source.rmdir();source.symlink_to(target,target_is_directory=True)
assert alias.resolve()==target
report={'stable_alias':str(alias),'previous_storage_path_preserved':str(source),'storage':str(target),'files':rows,'purpose':'Restore disk headroom for complete owned local Supabase runtime; all exact historical wheels remain recoverable and no Docker daemon/image configuration changed.','completed_at':datetime.datetime.now(datetime.timezone.utc).isoformat()}
Path('/workspace/recovery-evidence-20261011/final7-wheel-anchor-runtime-relocation.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report))
