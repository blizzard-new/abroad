import json,os,subprocess,sys,time
from pathlib import Path
root=Path('/workspace/abroad-tku-contract-final');out=Path('/tmp/tku-acceptance-contract-c6e6155');sha='c6e6155f2268a029f8dff0020f658d95b4c0ecc1'
def state():return {'commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip(),'dirty':subprocess.check_output(['git','status','--porcelain'],cwd=root,text=True).strip()}
before=state();assert before=={'commit':sha,'dirty':''}
command=[sys.executable,'-m','pytest','tests/e2e/test_system_motion.py::test_search_updates_are_bounded_and_rapid_navigation_cancels_old_motion','-q','-ra',f'--junitxml={out}/motion-diagnostic.xml']
started=time.time()
with (out/'motion-diagnostic.log').open('w') as log:r=subprocess.run(command,cwd=root,env={**os.environ,'PYTHONPATH':str(root/'src'),'PLAYWRIGHT_BROWSERS_PATH':'/tmp/tku-browsers'},stdout=log,stderr=subprocess.STDOUT)
after=state();guard=before==after
report={'tested_commit':sha,'starting_state':before,'ending_state':after,'candidate_guard_passed':guard,'actual_exit_code':r.returncode,'command':command,'elapsed_seconds':round(time.time()-started,2),'scope':'Original unchanged case for new PR shard1 opacity failure; no production access, no animation disabling or mocked response'}
(out/'motion-diagnostic-run.json').write_text(json.dumps(report,indent=2)+'\n');print(report);raise SystemExit(r.returncode if guard else 2)
