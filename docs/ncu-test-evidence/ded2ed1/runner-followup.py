import os,subprocess,json,datetime as dt
from pathlib import Path
r=Path('/workspace/abroad-ncu'); o=Path('/tmp/ncu-candidate-ded2ed1a79a5f3cb009655790eb560816a7af61a'); p='/workspace/abroad/.venv/bin/python'
e=dict(os.environ,PYTHONPATH='src',PLAYWRIGHT_BROWSERS_PATH='/workspace/.abroad-cloud-tools/ms-playwright')
for k in ['SUPABASE_URL','SUPABASE_SERVICE_ROLE_KEY']:e.pop(k,None)
sha=subprocess.check_output(['git','rev-parse','HEAD'],cwd=r,text=True).strip()
assert sha=='ded2ed1a79a5f3cb009655790eb560816a7af61a'
assert not subprocess.check_output(['git','status','--porcelain'],cwd=r,text=True).strip()
results=[]
commands=[('baseline_gate_failures',Path('/tmp/abroad-ncu-baseline'),['tests/test_ntpu_bundled_data.py','tests/test_frontend_contract.py','tests/test_rag.py'])]+[(f'niigata_phone_repeat_{i}',r,['tests/e2e/test_ncu_niigata.py::test_ncu_niigata_iec_graduate_finance_and_source_scope[390]']) for i in [1,2]]
for name,cwd,tests in commands:
    args=[p,'-m','pytest','-q',*tests,'--junitxml',str(o/f'{name}.xml')]
    start=dt.datetime.now(dt.timezone.utc).isoformat(); print('START',name,flush=True)
    with (o/f'{name}.log').open('w') as f: ret=subprocess.run(args,cwd=cwd,env=e,stdout=f,stderr=subprocess.STDOUT)
    results.append(dict(name=name,sha=sha,cwd=str(cwd),command=args,exit_code=ret.returncode,started_at=start,finished_at=dt.datetime.now(dt.timezone.utc).isoformat()))
    (o/'followup.json').write_text(json.dumps(results,indent=2)+'\n');print('END',name,ret.returncode,flush=True)
