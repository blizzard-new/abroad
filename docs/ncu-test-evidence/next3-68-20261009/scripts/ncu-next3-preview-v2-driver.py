from pathlib import Path
import datetime, hashlib, json, os, subprocess, sys, xml.etree.ElementTree as E
root=Path('/workspace/abroad-ncu');out=Path('/tmp/ncu-next3-preview-v2');out.mkdir(exist_ok=True)
assert not (out/'manifest.json').exists()
def git(*a): return subprocess.check_output(['git',*a],cwd=root,text=True).strip()
env=dict(os.environ,PYTHONPATH='src:/tmp',PLAYWRIGHT_BROWSERS_PATH='/workspace/.abroad-cloud-tools/ms-playwright',NCU_DIAG_OUT=str(out/'browser-events'))
for key in ['SUPABASE_URL','SUPABASE_SERVICE_ROLE_KEY']: env.pop(key,None)
m={'preview_only':True,'fixed_sha_validation':False,'start_sha':git('rev-parse','HEAD'),'start_worktree_porcelain':git('status','--porcelain'),'started_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'results':[]}
for name,args in [('corrected_certificate_test',['tests/test_ncu_tcu_toyama_fukui.py::test_current_forms_are_one_archive_with_four_sha_bound_members_and_reference_scope']),('browser',['-p','ncu_verify_failure_events','tests/e2e/test_ncu_tcu_toyama_fukui.py'])]:
    argv=['/workspace/abroad/.venv/bin/python','-m','pytest','-q',*args,'--junitxml='+str(out/(name+'.xml'))]
    print('START',name,flush=True)
    with (out/(name+'.log')).open('w')as f: r=subprocess.run(argv,cwd=root,env=env,stdout=f,stderr=subprocess.STDOUT)
    item={'name':name,'command':argv,'exit_code':r.returncode}
    if (out/(name+'.xml')).exists():
        t=E.parse(out/(name+'.xml')).getroot();item['junit']={k:sum(int(s.attrib.get(k,0))for s in t.iter('testsuite'))for k in ['tests','failures','errors','skipped']}
    m['results'].append(item);(out/'manifest.json').write_text(json.dumps(m,ensure_ascii=False,indent=2)+'\n');print('END',name,item,flush=True)
    if r.returncode: break
m.update(end_sha=git('rev-parse','HEAD'),end_worktree_porcelain=git('status','--porcelain'),finished_at=datetime.datetime.now(datetime.timezone.utc).isoformat())
m['browser_evidence']=[]
for p in sorted(Path('/tmp/ncu-audit/browser').glob('ncu-next3-*.png')):
    if datetime.datetime.fromtimestamp(p.stat().st_mtime,datetime.timezone.utc).isoformat()>=m['started_at']:
        target=out/'browser'/p.name;target.parent.mkdir(exist_ok=True);target.write_bytes(p.read_bytes());m['browser_evidence'].append({'path':str(target),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
(out/'manifest.json').write_text(json.dumps(m,ensure_ascii=False,indent=2)+'\n')
sys.exit(0 if all(x['exit_code']==0 for x in m['results'])else 1)
