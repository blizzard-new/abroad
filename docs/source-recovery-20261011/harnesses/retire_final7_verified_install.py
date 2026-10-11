from pathlib import Path
import datetime, hashlib, json, shutil
root=Path('/workspace/recovery-evidence-20261011')
meta=json.loads((root/'integration-final7-wheel-install/metadata.json').read_text())
build=json.loads((root/'integration-final7-wheel-integrity.json').read_text())
install=json.loads((root/'integration-final7-installed-wheel-integrity.json').read_text())
assert meta['test_result']=='passed' and meta['start_guard']==meta['end_guard']
wheel=Path(build['wheel']); target=Path(install['target'])
assert str(target)=='/workspace/abroad-integration-final7-wheel-installed-20261011'
assert hashlib.file_digest(wheel.open('rb'),'sha256').hexdigest()==build['wheel_sha256']
for row in build['files']:
    assert hashlib.file_digest((target/row['path']).open('rb'),'sha256').hexdigest()==row['sha256']
receipt={'candidate':build['sha'],'verified_package_files':len(build['files']),'verified_bytes':build['verified_uncompressed_bytes'],'completed_fresh_install_receipt':'integration-final7-installed-wheel-integrity.json','retained_exact_wheel':str(wheel),'wheel_sha256':build['wheel_sha256'],'retired_directory':str(target),'scope':'Only this completed generated installation; exact wheel and all evidence retained. Recreate with pip --no-index --no-deps --no-compile --target <empty directory> <retained wheel>.','completed_at':datetime.datetime.now(datetime.timezone.utc).isoformat()}
shutil.rmtree(target)
(root/'final7-completed-wheel-install-retirement.json').write_text(json.dumps(receipt,indent=2)+'\n')
print(json.dumps(receipt))
