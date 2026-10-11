"""Run the declared setuptools backend with its lossless hard-link copy mode."""
from pathlib import Path
import hashlib,inspect,json,os,subprocess,zipfile,datetime,shutil
import setuptools
import setuptools._distutils.file_util as file_util
from setuptools import build_meta
app=Path('/workspace/abroad-globe-20261011');root=Path('/tmp/integration-final4-wheel-build-20261011');root.mkdir(exist_ok=False)
sha=subprocess.check_output(['git','rev-parse','HEAD'],cwd=app,text=True).strip()
tracked=subprocess.check_output(['git','ls-files','src','pyproject.toml','README.md'],cwd=app,text=True).splitlines()
for name in tracked:
 source=app/name;target=root/name;target.parent.mkdir(parents=True,exist_ok=True);os.link(source,target)
original=file_util.copy_file;signature=inspect.signature(original)
def hard_link_copy(*args,**kwargs):
    bound=signature.bind_partial(*args,**kwargs);bound.arguments['link']='hard'
    return original(*bound.args,**bound.kwargs)
file_util.copy_file=hard_link_copy
from setuptools.command.build_py import build_py
from setuptools.command.install_lib import install_lib
linked = {"files": 0, "bytes": 0}
def stage_link(source, target):
    source, target = Path(source), Path(target)
    if target.is_dir(): target = target/source.name
    assert target.resolve().is_relative_to(root.resolve()), str(target)
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists():
        if os.path.samefile(source, target): return str(target), False
        target.unlink()
    os.link(source, target)  # Fail instead of silently falling back to a full copy.
    assert os.path.samefile(source, target)
    linked["files"] += 1
    linked["bytes"] += source.stat().st_size
    return str(target), True

def command_copy_file(self, source, target, *args, **kwargs):
    return stage_link(source, target)

def command_copy_tree(self, source, target, *args, **kwargs):
    source, target = Path(source), Path(target)
    return [stage_link(p, target/p.relative_to(source))[0]
            for p in source.rglob('*') if p.is_file()]

build_py.copy_file = command_copy_file
install_lib.copy_tree = command_copy_tree
out=Path('/workspace/integration-final4-wheel-artifacts-20261011');out.mkdir(exist_ok=True)
os.chdir(root)
wheel=out/build_meta.build_wheel(str(out))
verified=[]
blocked={'34569cf28e24ee8da835dda27c0bee84a415c2e63b29480c2fa70da349f2cf42','bb222e9a7ffa4ffe5493dcad6cb859f217a2cf8463b2b4aa13a84fa15871b493'}
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
        assert digest not in blocked,info.filename
        assert not any(name in info.filename for name in ['tku-sister-65-alternative-deea7d07.jpg','tku-sister-52-alternative-e2537ab5.jpg','withdrawn-campus-assets']),info.filename
        verified.append({'path':info.filename,'bytes':info.file_size,'sha256':digest})
    import tomllib
    config=tomllib.loads((app/'pyproject.toml').read_text())
    expected={str(p.relative_to(app/'src')) for pattern in config['tool']['setuptools']['package-data']['exchange_info'] for p in (app/'src/exchange_info').glob(pattern) if p.is_file()}
    expected.update(str(p.relative_to(app/'src')) for p in (app/'src/exchange_info').rglob('*.py'))
    missing=expected-set(package.namelist());assert not missing,sorted(missing)
    assert package.testzip() is None
with wheel.open('rb') as body:wheel_digest=hashlib.file_digest(body,'sha256').hexdigest()
report={'sha':sha,'completed_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'backend':'setuptools.build_meta','setuptools_version':setuptools.__version__,'storage_optimization':'build_py.copy_file / install_lib.copy_tree use verified os.link staging; declared package discovery, package-data, wheel assembly and metadata unchanged','hardlinked_staging':linked,'wheel':str(wheel),'wheel_bytes':wheel.stat().st_size,'wheel_sha256':wheel_digest,'verified_files':len(verified),'verified_uncompressed_bytes':sum(r['bytes'] for r in verified),'all_declared_package_data_present':True,'zip_crc_check':'passed','withdrawn_image_hashes_and_paths_absent':True,'files':verified}
Path('/workspace/recovery-evidence-20261011/integration-final4-wheel-integrity.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({k:v for k,v in report.items() if k!='files'},indent=2),flush=True)
# Only remove our generated staging tree; original source hardlinks stay intact.
shutil.rmtree(root)
