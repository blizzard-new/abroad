from pathlib import Path
import datetime, json, os, subprocess, sys, xml.etree.ElementTree as E
root=Path('/tmp/abroad-ncu-coe-scope-final');out=Path('/tmp/ncu-bounded-coe-kyutech-e79e0ba');out.mkdir(exist_ok=True)
assert not (out/'manifest.json').exists()
def git(*a):return subprocess.check_output(['git',*a],cwd=root,text=True).strip()
sha=git('rev-parse','HEAD');assert sha=='e79e0ba50cd247284f8a61b86f6fb5ff4c9a6409' and not git('status','--porcelain')
env=dict(os.environ,PYTHONPATH='src:/tmp',PLAYWRIGHT_BROWSERS_PATH='/workspace/.abroad-cloud-tools/ms-playwright',NCU_DIAG_OUT=str(out/'browser-events'),NCU_VISUAL_OUT=str(out/'visual'),NCU_VISUAL_SHA=sha)
for key in ['SUPABASE_URL','SUPABASE_SERVICE_ROLE_KEY']:env.pop(key,None)
args=['/workspace/abroad/.venv/bin/python','-m','pytest','-q','-p','ncu_verify_failure_events','-p','ncu_coe_visual_capture','tests/e2e/test_ncu_kyutech.py::test_ncu_kyutech_support_levels_arrival_split_and_reading_scope[1440]','tests/e2e/test_ncu_japan3.py','-k','test_ncu_kyutech or tohoku','--junitxml='+str(out/'browser.xml')]
m={'sha':sha,'started_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'start_clean':True,'command':args,'bounded_once':True,'original_20_case_failure_remains_open':True}
with (out/'browser.log').open('w')as f:r=subprocess.run(args,cwd=root,env=env,stdout=f,stderr=subprocess.STDOUT)
m.update(exit_code=r.returncode,end_sha=git('rev-parse','HEAD'),end_clean=not git('status','--porcelain'),finished_at=datetime.datetime.now(datetime.timezone.utc).isoformat())
t=E.parse(out/'browser.xml').getroot();m['junit']={k:sum(int(s.attrib.get(k,0))for s in t.iter('testsuite'))for k in ['tests','failures','errors','skipped']}
m['visual_capture_results']=[json.loads(p.read_text())for p in sorted((out/'visual').glob('visual-*.json'))]
(out/'manifest.json').write_text(json.dumps(m,ensure_ascii=False,indent=2)+'\n');print({k:m[k]for k in ['exit_code','junit','end_clean','finished_at']});sys.exit(r.returncode)
