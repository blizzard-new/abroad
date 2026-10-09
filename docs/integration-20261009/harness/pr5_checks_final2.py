import json,pathlib,subprocess,sys,zipfile
O=pathlib.Path('/workspace/integration-evidence/pr5-final2-checks');uv='/workspace/.abroad-cloud-tools/python/bin/uv'
commands=[('lock',[uv,'lock','--check']),('openapi',[sys.executable,'scripts/export_openapi.py','--check']),('python',[sys.executable,'-m','compileall','-q','src']),('js',['node','--check','src/exchange_info/static/app.js']),('sql-parser',[sys.executable,'scripts/validate_supabase_migrations.py']),('dependencies',['env','XDG_CACHE_HOME=/workspace/integration-tools/audit-cache',sys.executable,'scripts/audit_python_dependencies.py']),('replay',[sys.executable,'-m','scripts.build_ntu_destination_enrichment']),('clean',['git','diff','--exit-code']),('whitespace',['git','diff','--check','f6ad1b8','HEAD']),('wheel',[uv,'build','--wheel','--out-dir',str(O/'wheel')])]
results=[]
for name,cmd in commands:
 with (O/(name+'.log')).open('wb') as f:r=subprocess.run(cmd,stdout=f,stderr=subprocess.STDOUT,timeout=300)
 results.append({'name':name,'command':cmd,'exit_code':r.returncode});print(name,r.returncode,flush=True)
if results[-1]['exit_code']==0:
 with zipfile.ZipFile(next((O/'wheel').glob('*.whl'))) as z:
  assert not any('quarantined' in name for name in z.namelist())
  manifest=json.loads(z.read('exchange_info/static/assets/school-images.json'))
  assert sum(r['status']=='needs_review' for r in manifest['schools'])>=20
  review=json.loads(pathlib.Path('sources/ntu/photo-license-review-2026-10-09.json').read_text())
  for r in review['rows']:
   if not r['existing_shared_asset']:assert 'exchange_info'+r['original_local_path'] not in z.namelist()
  print('Wheel excludes all 15 quarantined new photo files',flush=True)
 import shutil
 shutil.move('build',str(O/'build-output'))
(O/'checks.json').write_text(json.dumps(results,indent=2));raise SystemExit(any(r['exit_code'] for r in results))
