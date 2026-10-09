import json,subprocess,sys,time,datetime,os
from pathlib import Path
root=Path('/tmp/tku-governance-b67d79a');source=Path('/workspace/abroad-tku-governance-array-fixed');sha='b67d79aa3b6c30a9449801501256b64951f2c291'
while not all((root/f'shard-{i}/guard.json').exists() for i in range(4)):time.sleep(1)
for folder,commit in [(Path('/tmp/tku-governance-b8f5e07'),'b8f5e075fe920860492c0eb3e18e06c5da71903b'),(root,sha)]:
 with (folder/'full-summary-original.log').open('w') as log:r=subprocess.run([sys.executable,str(root/'summarize-full.py'),str(folder),commit],stdout=log,stderr=subprocess.STDOUT)
 if r.returncode:raise RuntimeError('Full result summarizer failed; original log retained at '+str(folder))
ids=sorted(set(json.loads((root/'full-suite-summary.json').read_text())['failure_nodeids']+json.loads(Path('/tmp/tku-governance-b8f5e07/full-suite-summary.json').read_text())['failure_nodeids']))
if ids:
 def state():return {'commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=source,text=True).strip(),'dirty':subprocess.check_output(['git','status','--porcelain'],cwd=source,text=True).strip()}
 before=state();assert before=={'commit':sha,'dirty':''};folder=root/'isolated-original-failures';folder.mkdir(exist_ok=True)
 cmd=[sys.executable,'-m','pytest',*ids,'-vv','--tb=short','--durations=25','--capture=tee-sys','--junitxml='+str(folder/'suite.xml')]
 started=datetime.datetime.now(datetime.timezone.utc).isoformat();clock=time.monotonic()
 with (folder/'pytest.log').open('w') as log:r=subprocess.run(cmd,cwd=source,env={**os.environ,'PYTHONPATH':str(source/'src'),'PLAYWRIGHT_BROWSERS_PATH':'/tmp/tku-browsers','TKU_ACCEPTANCE_OUTPUT':str(folder/'browser'),'EXCHANGE_INFO_DATA_DIR':str(folder/'isolated-data')},stdout=log,stderr=subprocess.STDOUT)
 after=state();guard={'tested_commit':sha,'starting_state':before,'ending_state':after,'candidate_guard_passed':before==after,'actual_exit_code':r.returncode,'command':cmd,'selected_nodeids':ids,'started_at':started,'elapsed_seconds':round(time.monotonic()-clock,3),'test_source_timeout_skip_assertions_unchanged':True,'execution':'Original b8 and b67 full suites both completed before this sequential isolated run. This does not replace either original full-suite result.','production_access':False}
 (folder/'guard.json').write_text(json.dumps(guard,indent=2)+'\n');assert before==after
print(json.dumps({'fixed_full_summary':str(root/'full-suite-summary.json'),'original_full_summary':'/tmp/tku-governance-b8f5e07/full-suite-summary.json','isolated_failure_ids':ids,'completed':True}),flush=True)
