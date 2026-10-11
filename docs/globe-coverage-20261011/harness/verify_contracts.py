import ast, hashlib, json, os, pathlib, subprocess, sys
root=pathlib.Path.cwd()
checks=[]
def run(command):
 print('RUN',command,flush=True)
 r=subprocess.run(command,check=False)
 checks.append({'command':command,'exit_code':r.returncode})
 if r.returncode: raise SystemExit(r.returncode)
run(['/workspace/.abroad-cloud-tools/python/bin/uv','lock','--check'])
run([sys.executable,'-m','compileall','-q','src'])
for name in ('app.js','partner-map.js','content-review.js','icon-motion.js'):
 run(['node','--check',f'src/exchange_info/static/{name}'])
run([sys.executable,'scripts/export_openapi.py','--check'])
run([sys.executable,'scripts/validate_supabase_migrations.py'])
from exchange_info.storage import load_bundled_application_workflows
rows=load_bundled_application_workflows()
parity={}
for school,label,expected in [('cgu','長庚大學',154),('ntpu','國立臺北大學',409),('ntu','國立臺灣大學',288)]:
 path=f'src/exchange_info/official_data/{school}/application_workflows.jsonl'
 old=subprocess.check_output(['git','show','f6ad1b8:'+path])
 now=(root/path).read_bytes()
 assert old==now,path
 matched=[r for r in rows if r.home_university==label]
 assert len(matched)==expected,(label,len(matched))
 parity[school]={'count':len(matched),'byte_identical_to_original_f6ad1b8':True,'file_sha256':hashlib.sha256(now).hexdigest()}
path='src/exchange_info/school_identity.py'
old=ast.parse(subprocess.check_output(['git','show','59a20f2:'+path],text=True))
new=ast.parse((root/path).read_text())
for name in ['school_identity_key','same_school']:
 extract=lambda module:ast.dump(next(n for n in module.body if isinstance(n,ast.FunctionDef) and n.name==name),include_attributes=False)
 assert extract(old)==extract(new),name
protected=['supabase/migrations','pyproject.toml','uv.lock','.github/workflows','src/exchange_info/ntu_official_changes.py','src/exchange_info/static/icon-motion.js']
assert not subprocess.check_output(['git','diff','--name-only','59a20f2','HEAD','--',*protected],text=True).strip()
print(json.dumps({'checks':checks,'workflow_parity':parity,'protected_files_unchanged':protected,'governance_identity_functions_unchanged':True},ensure_ascii=False,indent=2))
