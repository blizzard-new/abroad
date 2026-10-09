import json,os,subprocess,sys,time
from pathlib import Path
root=Path('/workspace/abroad-tku-governance-rollback');sha='b8f5e075fe920860492c0eb3e18e06c5da71903b'
kind=sys.argv[1];out=Path('/tmp/tku-governance-b8f5e07');out.mkdir(exist_ok=True)
def state():return {'commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip(),'dirty':subprocess.check_output(['git','status','--porcelain'],cwd=root,text=True).strip()}
before=state();assert before=={'commit':sha,'dirty':''}
command=[sys.executable,'/tmp/tku-governance-b8f5e07/sql-diagnostic-driver.py']
started=time.time()
with (out/f'{kind}.log').open('w') as log:result=subprocess.run(command,cwd=root,env={**os.environ,'PYTHONPATH':str(root/'src'),'PLAYWRIGHT_BROWSERS_PATH':'/tmp/tku-browsers','UV_CACHE_DIR':'/tmp/tku-uv-cache','TKU_ACCEPTANCE_OUTPUT':str(out/'browser')},stdout=log,stderr=subprocess.STDOUT)
after=state();guard=before==after
report={'tested_commit':sha,'starting_state':before,'ending_state':after,'candidate_guard_passed':guard,'command':command,'actual_exit_code':result.returncode,'elapsed_seconds':round(time.time()-started,2),'production_access':False,'scope':'Actual isolated subset: ten original governance migrations, two original canonical functions and two real PostgREST instances. Not full34 Supabase/Storage validation.'}
(out/f'{kind}-run.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(json.dumps(report));raise SystemExit(result.returncode if guard else 2)
