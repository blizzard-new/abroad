from pathlib import Path
import datetime, hashlib, json, os, subprocess
root=Path('/tmp/abroad-ncu-coe-scope-final');out=Path('/tmp/ncu-kyutech-server-diagnostic-e79e0ba-20261009-v2')
out.mkdir(exist_ok=False)
def git(*a):return subprocess.check_output(['git',*a],cwd=root,text=True).strip()
sha=git('rev-parse','HEAD');assert sha=='e79e0ba50cd247284f8a61b86f6fb5ff4c9a6409' and not git('status','--porcelain')
env=dict(os.environ,PYTHONPATH='src:/tmp',PLAYWRIGHT_BROWSERS_PATH='/workspace/.abroad-cloud-tools/ms-playwright',NCU_DIAG_OUT=str(out/'browser-events'),NCU_KYUTECH_TIMING_OUT=str(out/'server'))
for k in ['SUPABASE_URL','SUPABASE_SERVICE_ROLE_KEY']:env.pop(k,None)
args=['/workspace/abroad/.venv/bin/python','-m','pytest','-q','-p','ncu_verify_failure_events','-p','ncu_kyutech_server_diagnostic','tests/e2e/test_ncu_kyutech.py::test_ncu_kyutech_support_levels_arrival_split_and_reading_scope[1440]','--junitxml='+str(out/'browser.xml')]
m={'candidate_sha':sha,'started_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'command':args,'instrumentation':'External diagnostic pytest plugin: ASGI Server-Timing, handler wall/thread CPU, event-loop delays, targeted cProfile. No product or test edits. Profiler overhead possible.','bounded_run_limit':2,'instrumentation_retry_reason':'First run patched a duplicate conftest module and recorded no server timings; retain as instrumentation failure','original_19_passed_1_failed_unchanged':True,'root_cause_closed':False}
(out/'manifest.json').write_text(json.dumps(m,ensure_ascii=False,indent=2)+'\n')
with (out/'browser.log').open('w') as f:
 try:r=subprocess.run(args,cwd=root,env=env,stdout=f,stderr=subprocess.STDOUT,timeout=150);m['exit_code']=r.returncode
 except subprocess.TimeoutExpired:m['timeout_seconds']=150;m['exit_code']=124
m.update(finished_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),end_sha=git('rev-parse','HEAD'),end_clean=not git('status','--porcelain'))
m['files']=[{'path':str(p.relative_to(out)),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}for p in sorted(out.rglob('*'))if p.is_file() and p.name!='manifest.json']
(out/'manifest.json').write_text(json.dumps(m,ensure_ascii=False,indent=2)+'\n');print({k:m[k]for k in ['candidate_sha','exit_code','end_clean','finished_at']})
