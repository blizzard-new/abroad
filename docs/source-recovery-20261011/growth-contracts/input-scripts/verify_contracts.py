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
for name in ('app.js','partner-map.js','content-review.js','icon-motion.js','tku-campus-assets.js'):
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
protected=['supabase/migrations','uv.lock','.github/workflows','src/exchange_info/ntu_official_changes.py','src/exchange_info/static/icon-motion.js']
assert not subprocess.check_output(['git','diff','--name-only','59a20f2','HEAD','--',*protected],text=True).strip()
print(json.dumps({'checks':checks,'workflow_parity':parity,'protected_files_unchanged':protected,'governance_identity_functions_unchanged':True},ensure_ascii=False,indent=2))

import tomllib
before = tomllib.loads(subprocess.check_output(['git','show','59a20f2:pyproject.toml'],text=True))
after = tomllib.loads((root/'pyproject.toml').read_text())
assert before['project'] == after['project'] and before['build-system'] == after['build-system']
old_patterns=set(before['tool']['setuptools']['package-data']['exchange_info'])
new_patterns=set(after['tool']['setuptools']['package-data']['exchange_info'])
assert new_patterns-old_patterns == {'official_data/ccu/completion_sources/*','official_data/tku/capture_packs/*.zip.*'} and not old_patterns-new_patterns
needed=[*list((root/'src/exchange_info/official_data/cgu_catalogue').glob('*')),*list((root/'src/exchange_info/official_data/ccu/completion_sources').glob('*')),*list((root/'src/exchange_info/static/assets/ccu/campuses').glob('*')),*list((root/'src/exchange_info/static/assets/ncu-schools').glob('*'))]
needed.extend((root/'src/exchange_info/official_data/tku').glob('capture_packs/*.zip.*'))
needed.extend((root/'src/exchange_info/static/assets/tku-campuses').glob('*'))
selected={str(p.relative_to(root/'src/exchange_info')) for pattern in new_patterns for p in (root/'src/exchange_info').glob(pattern) if p.is_file()}
assert all(str(p.relative_to(root/'src/exchange_info')) in selected for p in needed if p.is_file())
print('PACKAGE_SELECTION',len(needed),'required new public source/asset files selected; dependency requirements unchanged')
# The parent-owned 13 cases are byte/AST unchanged, not rewritten by the CGU integration.
cases=json.loads(pathlib.Path('/workspace/pr9-review-20261011/13-tests.json').read_text())
for case in cases:
 path,name=case.split('::',1)
 old=ast.parse(subprocess.check_output(['git','show','59a20f2:'+path],text=True))
 new=ast.parse((root/path).read_text())
 extract=lambda tree:ast.dump(next(n for n in ast.walk(tree) if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)) and n.name==name),include_attributes=False)
 assert extract(old)==extract(new),case
print('PARENT_13_TEST_FUNCTIONS_UNCHANGED',len(cases))
