"""Read-only contracts plus a wheel whose generated build tree is kept as evidence."""
import hashlib,json,subprocess,sys,shutil,zipfile
from pathlib import Path
root=Path.cwd();out=Path('/workspace/integration-evidence')/(sys.argv[1] if len(sys.argv)>1 else 'memory-final-release-checks')
uv='/workspace/.abroad-cloud-tools/python/bin/uv'
commands=[('lock',[uv,'lock','--check']),('openapi',[sys.executable,'scripts/export_openapi.py','--check']),('python',[sys.executable,'-m','compileall','-q','src']),('javascript',['node','--check','src/exchange_info/static/app.js']),('whitespace',['git','diff','--check','1c715d21','HEAD']),('sql-parser',[sys.executable,'scripts/validate_supabase_migrations.py']),('wheel',[uv,'build','--wheel','--out-dir',str(out/'wheel')])]
assert not (root/'build').exists()
results=[]
try:
 for name,cmd in commands:
  with (out/(name+'.log')).open('wb') as f:r=subprocess.run(cmd,stdout=f,stderr=subprocess.STDOUT,timeout=600)
  results.append({'name':name,'command':cmd,'exit_code':r.returncode});print(name,r.returncode,flush=True)
finally:
 if (root/'build').exists():shutil.move(root/'build',out/'build-output')
(out/'checks.json').write_text(json.dumps(results,indent=2)+'\n')
assert all(row['exit_code']==0 for row in results),results
wheel=next((out/'wheel').glob('*.whl'))
with zipfile.ZipFile(wheel) as z:
 names=z.namelist();checked=0
 for n in names:
  p=root/'src'/n
  if n.startswith('exchange_info/') and p.is_file():
   assert z.read(n)==p.read_bytes(),n;checked+=1
 assert not any('quarantined' in n for n in names)
 review=json.loads((root/'sources/ntu/photo-license-review-2026-10-09.json').read_text())
 for row in review['rows']:
  if not row['existing_shared_asset']:assert 'exchange_info'+row['original_local_path'] not in names
 proof={'head':subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),'wheel':wheel.name,'sha256':hashlib.sha256(wheel.read_bytes()).hexdigest(),'entries':len(names),'source_files_byte_identical':checked,'quarantined_new_photos_excluded':15,'no_tracked_or_untracked_changes':not subprocess.check_output(['git','status','--porcelain=v1'],text=True).strip()}
 assert proof['no_tracked_or_untracked_changes']
proof_path=out.parent/(out.name+'-wheel-proof.json') if len(sys.argv)>1 else out.parent/'memory-final-wheel-proof.json'
proof_path.write_text(json.dumps(proof,indent=2)+'\n');print(proof,flush=True)
