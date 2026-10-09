import datetime as dt,hashlib,json,os,subprocess,sys,xml.etree.ElementTree as ET
from pathlib import Path
root=Path('/workspace/abroad-ncu-next3-fixed');python='/workspace/abroad/.venv/bin/python'
def git(*args):return subprocess.check_output(['git',*args],cwd=root,text=True).strip()
sha=git('rev-parse','HEAD');assert not git('status','--porcelain')
out=Path('/workspace/ncu-verification-tmp')/('next3-'+sha);out.mkdir(exist_ok=True)
env=dict(os.environ,TMPDIR='/workspace/ncu-verification-tmp',PYTHONPATH='src:/tmp',PLAYWRIGHT_BROWSERS_PATH='/workspace/.abroad-cloud-tools/ms-playwright',NCU_NEXT3_BROWSER_OUT=str(out/'browser'))
for k in ['SUPABASE_URL','SUPABASE_SERVICE_ROLE_KEY']:env.pop(k,None)
report={'candidate_sha':sha,'start_sha':sha,'start_porcelain':'','started_at':dt.datetime.now(dt.timezone.utc).isoformat(),'baseline_sha':'012b580b9c38b20da0e52394eef1428c2ea90261','scope_rows':['ncu-130','ncu-134','ncu-135'],'data_coverage':json.loads((root/'src/exchange_info/official_data/ncu/catalog-completeness.json').read_text()),'results':[],'full_ci_equivalence':False,'current_116_data_acceptance':False,'prior_kyutech_root_closed':False,'production_actions':False}
def save():(out/'manifest.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
def run(name,argv,junit=False):
 assert git('rev-parse','HEAD')==sha and not git('status','--porcelain')
 args=list(argv)
 if junit:args+=['--junitxml',str(out/(name+'.xml'))]
 begin=dt.datetime.now(dt.timezone.utc).isoformat();print('START',name,begin,flush=True)
 with (out/(name+'.log')).open('w')as f:x=subprocess.run(args,cwd=root,env=env,stdout=f,stderr=subprocess.STDOUT)
 row={'name':name,'argv':args,'cwd':str(root),'exit_code':x.returncode,'started_at':begin,'finished_at':dt.datetime.now(dt.timezone.utc).isoformat(),'log':name+'.log'}
 if junit and (out/(name+'.xml')).exists():
  tree=ET.parse(out/(name+'.xml')).getroot();ss=[tree]if tree.tag=='testsuite'else list(tree.iter('testsuite'))
  row['junit']={k:sum(int(s.attrib.get(k,'0'))for s in ss)for k in ['tests','failures','errors','skipped']}
  row['failed_cases']=[{'name':c.attrib.get('name'),'message':a.attrib.get('message')}for c in tree.iter('testcase')for a in c if a.tag in ['failure','error']]
  row['skipped_cases']=[{'name':c.attrib.get('name'),'reason':a.attrib.get('message')}for c in tree.iter('testcase')for a in c if a.tag=='skipped']
 report['results'].append(row);save();print('END',name,row['exit_code'],row.get('junit'),flush=True)

save()
assert git('diff','--name-only','bb806740',sha)=='tests/e2e/test_ncu_nufs_kumamoto_ryukoku.py'
report['data_candidate_sha']='bb806740e702892e78d358973cb2c54b739d3dbd'
report['data_and_shared_runtime_identical_to_bb806740']=True
report['prior_full_api_manifest']='../next3-bb806740e702892e78d358973cb2c54b739d3dbd/manifest.json'
report['prior_browser_result']={'tests':6,'passed':2,'failed':4,'cause':'NUFS and Ryukoku orientation title selectors used English; existing public translation renders 新生說明會. Original failures/logs/screenshots preserved.'}
env['UV_CACHE_DIR']='/workspace/ncu-verification-tmp/uv-cache'
run('affected_three_school_api',[python,'-m','pytest','-q','tests/test_ncu_nufs_kumamoto_ryukoku.py'],True)
run('openapi_snapshot',[python,'scripts/export_openapi.py','--check'])
run('browser_three_school_content',[python,'-m','pytest','-q','tests/e2e/test_ncu_nufs_kumamoto_ryukoku.py'],True)
run('lock_writable_cache',['uv','lock','--check'])
run('test_only_scoped_diff',['git','diff','--check','bb806740',sha])
shots=[]
for p in sorted((out/'browser').glob('*.png')):shots.append({'path':'browser/'+p.name,'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'bytes':p.stat().st_size})
report['browser_screenshots']=shots;report['end_sha']=git('rev-parse','HEAD');report['end_porcelain']=git('status','--porcelain');report['same_sha_and_clean']=report['end_sha']==sha and not report['end_porcelain'];report['necessary_local_tests_passed']=all(r['exit_code']==0 for r in report['results']);report['finished_at']=dt.datetime.now(dt.timezone.utc).isoformat();save()
print('MANIFEST',str(out/'manifest.json'),flush=True)
sys.exit(0 if report['necessary_local_tests_passed']and report['same_sha_and_clean']else 1)
