from pathlib import Path
import json,subprocess,datetime,os,xml.etree.ElementTree as E
root=Path('/workspace/abroad-ncu');out=Path('/tmp/ncu-next3-preview-v1');out.mkdir(exist_ok=True)
assert not (out/'manifest.json').exists()
def git(*a):return subprocess.check_output(['git',*a],cwd=root,text=True).strip()
sha=git('rev-parse','HEAD');dirty=git('status','--porcelain');assert dirty
env=dict(os.environ,PYTHONPATH='src:/tmp',PLAYWRIGHT_BROWSERS_PATH='/workspace/.abroad-cloud-tools/ms-playwright',NCU_DIAG_OUT=str(out/'browser-events'));env.pop('SUPABASE_URL',None);env.pop('SUPABASE_SERVICE_ROLE_KEY',None)
argv=['/workspace/abroad/.venv/bin/python','-m','pytest','-q','tests/test_ncu_tcu_toyama_fukui.py','tests/test_ncu_japan3.py','tests/test_life_context.py','--junitxml='+str(out/'unit.xml')]
m={'preview_only':True,'fixed_sha_validation':False,'start_sha':sha,'start_worktree_porcelain':dirty,'started_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'command':argv}
with (out/'unit.log').open('w')as f:r=subprocess.run(argv,cwd=root,env=env,stdout=f,stderr=subprocess.STDOUT)
m.update(exit_code=r.returncode,end_sha=git('rev-parse','HEAD'),end_worktree_porcelain=git('status','--porcelain'),finished_at=datetime.datetime.now(datetime.timezone.utc).isoformat())
xml=out/'unit.xml'
if xml.exists():
 t=E.parse(xml).getroot();m['junit']={k:sum(int(s.attrib.get(k,0))for s in t.iter('testsuite'))for k in ['tests','failures','errors','skipped']}
(out/'manifest.json').write_text(json.dumps(m,ensure_ascii=False,indent=2)+'\n');print(m.get('junit',{}),r.returncode)
