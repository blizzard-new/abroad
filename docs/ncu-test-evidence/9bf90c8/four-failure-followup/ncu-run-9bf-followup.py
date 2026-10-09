from pathlib import Path
import json,datetime as dt,os,subprocess,xml.etree.ElementTree as ET
root=Path('/tmp/abroad-ncu-hokkaido-correction');sha='9bf90c8748fd33747c625e1f5154f6838540d64a';original=Path('/tmp/ncu-candidate-'+sha);out=Path('/tmp/ncu-9bf90c8-browser-followup');out.mkdir(exist_ok=True)
def git(*args):return subprocess.check_output(['git',*args],cwd=root,text=True).strip()
assert git('rev-parse','HEAD')==sha and not git('status','--porcelain')
cases=[c for c in ET.parse(original/'browser_ncu_ntu.xml').getroot().iter('testcase') if any(f.tag=='failure' for f in c)]
args=['/workspace/abroad/.venv/bin/python','-m','pytest','-q','-p','ncu_browser_diagnostic']+[c.attrib['classname'].replace('.','/')+'.py::'+c.attrib['name'] for c in cases]+['--junitxml='+str(out/'four-original-failures.xml')]
env=dict(os.environ,PYTHONPATH='src:/tmp',PLAYWRIGHT_BROWSERS_PATH='/workspace/.abroad-cloud-tools/ms-playwright');env.pop('SUPABASE_URL',None);env.pop('SUPABASE_SERVICE_ROLE_KEY',None)
report=dict(tested_sha=sha,start_head=git('rev-parse','HEAD'),start_porcelain=git('status','--porcelain'),started_at=dt.datetime.now(dt.timezone.utc).isoformat(),command=args,scope='Only the four original browser failures; diagnostic event recording added by an external /tmp pytest plugin; original 52 passed / 4 failed result is retained, not replaced.')
with (out/'four-original-failures.log').open('w')as f:result=subprocess.run(args,cwd=root,env=env,stdout=f,stderr=subprocess.STDOUT)
report.update(exit_code=result.returncode,end_head=git('rev-parse','HEAD'),end_porcelain=git('status','--porcelain'),finished_at=dt.datetime.now(dt.timezone.utc).isoformat());(out/'manifest.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(json.dumps(report,ensure_ascii=False))
