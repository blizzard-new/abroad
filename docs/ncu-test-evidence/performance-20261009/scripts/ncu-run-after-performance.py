from pathlib import Path
import os,subprocess,json,datetime,xml.etree.ElementTree as E
py='/workspace/abroad/.venv/bin/python';fixed=Path('/tmp/abroad-ncu-performance-final');active=Path('/workspace/abroad-ncu');out=Path('/tmp/ncu-after-performance-20261009');out.mkdir(exist_ok=True)
env=dict(os.environ,PYTHONPATH='src:/tmp',PLAYWRIGHT_BROWSERS_PATH='/workspace/.abroad-cloud-tools/ms-playwright',NCU_DIAG_OUT=str(out/'japan3-browser-events'));env.pop('SUPABASE_URL',None);env.pop('SUPABASE_SERVICE_ROLE_KEY',None)
manifest={'started_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'results':[],'bounded_restore_diagnostic_runs':1,'bounded_boot_v4_runs':1}
def git(root,*args):return subprocess.check_output(['git',*args],cwd=root,text=True).strip()
phases=[('ntu_restore_diagnostic',fixed,[py,'-m','pytest','-q','-p','ncu_ntu_restore_diagnostic','tests/e2e/test_ntu_school.py::test_ntu_saved_conditions_keep_gpa_and_rank_without_percent_conversion','--junitxml=/tmp/ncu-bounded-ntu-restore-3b14037/one-case.xml'],180,True),('boot_lifecycle_v4',fixed,[py,'/tmp/ncu-niigata-perf-v4.py','1','3b1403701edc957bba1796f30dae1a6bc0bf4712'],180,True),('japan3_preview_v2',active,[py,'-m','pytest','-q','-p','ncu_verify_failure_events','tests/e2e/test_ncu_japan3.py','--junitxml='+str(out/'japan3-preview-v2.xml')],600,False)]
for name,root,argv,bound,mustclean in phases:
 sha=git(root,'rev-parse','HEAD');dirty=git(root,'status','--porcelain');assert not mustclean or not dirty
 row={'name':name,'started_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'start_sha':sha,'start_worktree_porcelain':dirty,'fixed_sha_validation':mustclean,'preview_only':not mustclean,'command':argv,'bound_seconds':bound}
 print('START',name,flush=True)
 try:
  with(out/(name+'.log')).open('w')as f:r=subprocess.run(argv,cwd=root,env=env,stdout=f,stderr=subprocess.STDOUT,timeout=bound)
  row['exit_code']=r.returncode
 except subprocess.TimeoutExpired:row['exit_code']=124;row['bounded_timeout']=True
 row.update(finished_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),end_sha=git(root,'rev-parse','HEAD'),end_worktree_porcelain=git(root,'status','--porcelain'))
 xml=Path(next((arg.split('=',1)[1]for arg in argv if arg.startswith('--junitxml=')),'/tmp/nonexistent'))
 if xml.exists():
  tree=E.parse(xml).getroot();row['junit']={k:sum(int(s.attrib.get(k,0))for s in tree.iter('testsuite'))for k in ['tests','failures','errors','skipped']}
 manifest['results'].append(row);(out/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n');print('END',name,row['exit_code'],row.get('junit',{}),flush=True)
print('COMPLETE',flush=True)
