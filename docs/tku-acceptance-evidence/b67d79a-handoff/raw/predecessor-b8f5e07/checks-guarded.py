import json,subprocess,time,os,sys
from pathlib import Path
root=Path('/workspace/abroad-tku-governance-rollback');out=Path('/tmp/tku-governance-b8f5e07');sha='b8f5e075fe920860492c0eb3e18e06c5da71903b'
def state():return {'commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip(),'dirty':subprocess.check_output(['git','status','--porcelain'],cwd=root,text=True).strip()}
before=state();assert before=={'commit':sha,'dirty':''}
checks=[('openapi',[sys.executable,'scripts/export_openapi.py','--check']),('migrations-parse',[sys.executable,'scripts/validate_supabase_migrations.py']),('dependency-audit',[sys.executable,'-m','pip_audit','.', '--strict','--progress-spinner','off','--cache-dir',str(out/'dependency-cache')]),('JS-app',['node','--check','src/exchange_info/static/app.js']),('JS-content-review',['node','--check','src/exchange_info/static/content-review.js']),('JS-icon-motion',['node','--check','src/exchange_info/static/icon-motion.js']),('git-diff-check',['git','diff','--check'])]
reports=[]
for name,cmd in checks:
 started=time.monotonic()
 with (out/(name+'-guarded.log')).open('w') as log:r=subprocess.run(cmd,cwd=root,env={**os.environ,'PYTHONPATH':str(root/'src')},stdout=log,stderr=subprocess.STDOUT)
 reports.append({'name':name,'command':cmd,'actual_exit_code':r.returncode,'elapsed_seconds':round(time.monotonic()-started,3)})
after=state();guard=before==after
report={'tested_commit':sha,'starting_state':before,'ending_state':after,'candidate_guard_passed':guard,'checks':reports,'production_access':False,'dependency_cache_note':'First original wrapper run failed on read-only /home/agent/.cache/pip-audit. Rerun retains exact original audit arguments and adds supported --cache-dir within task /tmp; no auth/permission/billing/config changes.'}
(out/'checks-run.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report));raise SystemExit(0 if guard and all(r['actual_exit_code']==0 for r in reports) else 1)
