import json,os,subprocess,sys,time
from pathlib import Path
root=Path('/workspace/abroad-tku-governance-array-fixed');sha='b67d79aa3b6c30a9449801501256b64951f2c291'
shard=int(sys.argv[1]);out=Path('/tmp/tku-governance-b67d79a')/f'shard-{shard}';out.mkdir(exist_ok=True)
def state():return {'commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip(),'dirty':subprocess.check_output(['git','status','--porcelain'],cwd=root,text=True).strip()}
before=state();assert before=={'commit':sha,'dirty':''}
command=[sys.executable,'scripts/run_web_quality_tests.py','--shard',str(shard),'--shards','4','--junitxml',str(out/'suite.xml'),'--evidence-dir',str(out)]
started=time.time()
with (out/'pytest.log').open('w') as log:result=subprocess.run(command,cwd=root,env={**os.environ,'PYTHONPATH':str(root/'src'),'PLAYWRIGHT_BROWSERS_PATH':'/tmp/tku-browsers','TKU_ACCEPTANCE_OUTPUT':str(out/'browser'),'EXCHANGE_INFO_DATA_DIR':str(out/'isolated-data')},stdout=log,stderr=subprocess.STDOUT)
after=state();guard=before==after
report={'tested_commit':sha,'starting_state':before,'ending_state':after,'candidate_guard_passed':guard,'command':command,'actual_exit_code':result.returncode,'elapsed_seconds':round(time.time()-started,2),'production_access':False,'scope':'Same repository full-suite partition command as CI; this is local execution, not a GitHub runner or full Supabase runtime.'}
(out/'guard.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report));raise SystemExit(result.returncode if guard else 2)
