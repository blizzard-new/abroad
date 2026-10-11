"""Run the declared setuptools backend with its lossless hard-link copy mode."""
from pathlib import Path
import hashlib,inspect,json,os,subprocess,zipfile,datetime,shutil
import setuptools
import setuptools._distutils.file_util as file_util
from setuptools import build_meta
app=Path('/workspace/abroad-globe-20261011');root=Path('/workspace/recovery-wheel-build-20261011');root.mkdir(exist_ok=False)
sha=subprocess.check_output(['git','rev-parse','HEAD'],cwd=app,text=True).strip()
tracked=subprocess.check_output(['git','ls-files','src','pyproject.toml','README.md'],cwd=app,text=True).splitlines()
for name in tracked:
 source=app/name;target=root/name;target.parent.mkdir(parents=True,exist_ok=True);os.link(source,target)
original=file_util.copy_file;signature=inspect.signature(original)
def hard_link_copy(*args,**kwargs):
    bound=signature.bind_partial(*args,**kwargs);bound.arguments['link']='hard'
    return original(*bound.args,**bound.kwargs)
file_util.copy_file=hard_link_copy
out=Path('/workspace/recovery-wheel-artifacts-20261011');out.mkdir(exist_ok=True)
os.chdir(root)
wheel=out/build_meta.build_wheel(str(out))
verified=[]
with zipfile.ZipFile(wheel) as package:
    for info in package.infolist():
        if not info.filename.startswith('exchange_info/') or info.is_dir():continue
        source=app/'src'/info.filename
        assert source.is_file(),info.filename
        with package.open(info) as body:
            digest=hashlib.file_digest(body,'sha256').hexdigest()
        with source.open('rb') as body:
            expected=hashlib.file_digest(body,'sha256').hexdigest()
        assert digest==expected,info.filename
        verified.append({'path':info.filename,'bytes':info.file_size,'sha256':digest})
    import tomllib
    config=tomllib.loads((app/'pyproject.toml').read_text())
    expected={str(p.relative_to(app/'src')) for pattern in config['tool']['setuptools']['package-data']['exchange_info'] for p in (app/'src/exchange_info').glob(pattern) if p.is_file()}
    expected.update(str(p.relative_to(app/'src')) for p in (app/'src/exchange_info').rglob('*.py'))
    missing=expected-set(package.namelist());assert not missing,sorted(missing)
    assert package.testzip() is None
with wheel.open('rb') as body:wheel_digest=hashlib.file_digest(body,'sha256').hexdigest()
report={'sha':sha,'completed_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'backend':'setuptools.build_meta','setuptools_version':setuptools.__version__,'storage_optimization':'distutils copy_file(link=hard); declared package discovery, package-data, wheel assembly and metadata unchanged','wheel':str(wheel),'wheel_bytes':wheel.stat().st_size,'wheel_sha256':wheel_digest,'verified_files':len(verified),'verified_uncompressed_bytes':sum(r['bytes'] for r in verified),'all_declared_package_data_present':True,'zip_crc_check':'passed','files':verified}
Path('/workspace/recovery-evidence-20261011/final-wheel-integrity.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({k:v for k,v in report.items() if k!='files'},indent=2),flush=True)
# Only remove our generated staging tree; original source hardlinks stay intact.
shutil.rmtree(root)
