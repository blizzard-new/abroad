from pathlib import Path
import datetime as dt,json,os,subprocess,xml.etree.ElementTree as E
root=Path('/tmp/abroad-ncu-hokkaido-correction');out=Path('/tmp/ncu-bounded-performance-9bf90c8');sha='9bf90c8748fd33747c625e1f5154f6838540d64a'
def git(*a):return subprocess.check_output(['git',*a],cwd=root,text=True).strip()
assert git('rev-parse','HEAD')==sha and not git('status','--porcelain')
cases=[c for c in E.parse(Path('/tmp/ncu-candidate-'+sha)/'browser_ncu_ntu.xml').getroot().iter('testcase')if c.find('failure')is not None]
args=['/workspace/abroad/.venv/bin/python','-m','pytest','-q','-p','ncu_bounded_diagnostic']+[c.attrib['classname'].replace('.','/')+'.py::'+c.attrib['name']for c in cases]+['--junitxml='+str(out/'four-cases.xml')]
env=dict(os.environ,PYTHONPATH='src:/tmp',PLAYWRIGHT_BROWSERS_PATH='/workspace/.abroad-cloud-tools/ms-playwright');env.pop('SUPABASE_URL',None);env.pop('SUPABASE_SERVICE_ROLE_KEY',None)
report=dict(sha=sha,started_at=dt.datetime.now(dt.timezone.utc).isoformat(),bounded_runs=1,cases=len(cases),command=args,start_porcelain=git('status','--porcelain'),instrumentation='External /tmp timing plugin and Playwright trace; original test code and timeout unchanged')
with(out/'four-cases.log').open('w')as f:r=subprocess.run(args,cwd=root,env=env,stdout=f,stderr=subprocess.STDOUT,timeout=600)
report.update(exit_code=r.returncode,finished_at=dt.datetime.now(dt.timezone.utc).isoformat(),end_sha=git('rev-parse','HEAD'),end_porcelain=git('status','--porcelain'));(out/'bounded-manifest.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(json.dumps(report,ensure_ascii=False))
