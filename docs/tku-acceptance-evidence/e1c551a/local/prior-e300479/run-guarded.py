import json,os,subprocess,sys,time
from pathlib import Path
root=Path('/workspace/abroad-tku-governance-adapters');sha='e300479cb263019528c6f5f4dc4df69017f020ca'
kind=sys.argv[1];out=Path('/tmp/tku-governance-e300479');out.mkdir(exist_ok=True)
def state():return {'commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip(),'dirty':subprocess.check_output(['git','status','--porcelain'],cwd=root,text=True).strip()}
before=state();assert before=={'commit':sha,'dirty':''}
unit=['tests/test_next_phase_contract.py','tests/test_tku_governance_routes.py']
browser=['tests/e2e/test_web_next_phase.py::test_verified_student_reports_workflow_issue_and_admin_closes_it']
files=unit if kind=='unit' else browser
command=[sys.executable,'-m','pytest',*files,'-q','-ra',f'--junitxml={out}/{kind}.xml']
started=time.time()
with (out/f'{kind}.log').open('w') as log:result=subprocess.run(command,cwd=root,env={**os.environ,'PYTHONPATH':str(root/'src'),'PLAYWRIGHT_BROWSERS_PATH':'/tmp/tku-browsers','UV_CACHE_DIR':'/tmp/tku-uv-cache','TKU_ACCEPTANCE_OUTPUT':str(out/'browser')},stdout=log,stderr=subprocess.STDOUT)
after=state();guard=before==after
report={'tested_commit':sha,'starting_state':before,'ending_state':after,'candidate_guard_passed':guard,'command':command,'actual_exit_code':result.returncode,'elapsed_seconds':round(time.time()-started,2),'production_access':False,'scope':'Twelve corrected original contracts and related source/display/catalog/notification checks' if kind=='unit' else 'Original notification, shared conditions, routing/public catalog, document-flow and all system-motion browser cases; new queued-frame barrier; closed reader/alias/case4 not repeated'}
(out/f'{kind}-run.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(json.dumps(report));raise SystemExit(result.returncode if guard else 2)
