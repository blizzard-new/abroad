import datetime as dt,hashlib,json,os,subprocess,sys,xml.etree.ElementTree as ET
from pathlib import Path
root=Path('/workspace/abroad-ncu-p1-unit-fixed');python='/workspace/abroad/.venv/bin/python'
def git(*args):return subprocess.check_output(['git',*args],cwd=root,text=True).strip()
sha=git('rev-parse','HEAD');assert not git('status','--porcelain')
out=Path('/workspace/ncu-verification-tmp')/('p1-five-save-'+sha);out.mkdir(exist_ok=True)
env=dict(os.environ,TMPDIR='/workspace/ncu-verification-tmp',PYTHONPATH='src:/tmp',PLAYWRIGHT_BROWSERS_PATH='/workspace/.abroad-cloud-tools/ms-playwright',NCU_NEXT3_BROWSER_OUT=str(out/'browser'),UV_CACHE_DIR='/workspace/ncu-verification-tmp/uv-cache')
for k in ['SUPABASE_URL','SUPABASE_SERVICE_ROLE_KEY']:env.pop(k,None)
report={'candidate_sha':sha,'start_sha':sha,'start_porcelain':'','started_at':dt.datetime.now(dt.timezone.utc).isoformat(),'baseline_sha':'bb4cecd8030946e59bed494509d206c356e5c210','scope_rows':['ncu-130','ncu-134','ncu-135'],'correction_groups':5,'data_coverage':json.loads((root/'src/exchange_info/official_data/ncu/catalog-completeness.json').read_text()),'results':[],'full_ci_equivalence':False,'current_116_data_acceptance':False,'prior_kyutech_root_closed':False,'production_actions':False}
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
import ast
old_reading=ast.parse(subprocess.check_output(['git','show','2159409c:tests/e2e/test_ncu_nufs_kumamoto_ryukoku.py'],cwd=root,text=True))
new_reading=ast.parse((root/'tests/e2e/test_ncu_nufs_kumamoto_ryukoku.py').read_text())
def reading_ast(tree):return ast.dump(next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='test_next3_reference_packets_and_living_content'))
assert reading_ast(old_reading)==reading_ast(new_reading)
report['unchanged_six_reading_cases_ast_sha256']=hashlib.sha256(reading_ast(new_reading).encode()).hexdigest()
report['prior_e7_save_failure']='Arrival task used a localized title that differs from the planner title; first two stages reached synchronized checked state. Replaced title lookup with explicit requirement names.'
assert git('diff','--name-only','2159409c',sha).splitlines()==['tests/e2e/test_ncu_nufs_kumamoto_ryukoku.py','tests/test_ncu_next3_review_corrections.py']
report['data_candidate_sha']='2159409cacb6d8ac36bbafcc3ca6f2925f860fc9'
report['data_and_shared_runtime_identical_to_2159409c']=True
report['prior_full_api_manifest']='../p1-five-2159409cacb6d8ac36bbafcc3ca6f2925f860fc9/manifest.json'
report['prior_browser_result']={'tests':8,'passed':6,'failed':2,'reason':'Pending requirements are displayed in confirmation paragraphs; test incorrectly looked for an active document-link list. No pending gate or runtime changed.'}
report['api_candidate_sha']='cc3c37c74e01fc9c602453a75a0f6a85d63954af'
assert git('diff','--name-only',report['api_candidate_sha'],sha)=='tests/e2e/test_ncu_nufs_kumamoto_ryukoku.py'
report['unit_test_data_runtime_identical_to_cc3c37c7']=True
run('browser_ryukoku_account_save',[python,'-m','pytest','-q','tests/e2e/test_ncu_nufs_kumamoto_ryukoku.py','-k','stage_checkboxes_save'],True)
report['browser_candidate_sha']='5d2536530296523fa99137d9f5ac570d87257c9b'
report['prior_browser_capture_failure_note']='The 5d253653 locator was detached by normal account-state rerender after checking. Wait for synchronization and screenshot the page without a stale element handle.'
report['browser_reading_cases_unchanged_from_2159409c']=True
report['prior_5d_unit_failure_note']='New plan test used shorthand NCU, while actual browser planner sends canonical 國立中央大學. Test now uses actual browser context and exact phase/document names.'
run('test_only_whitespace',['git','diff','--check','2159409c',sha])

shots=[]
for p in sorted((out/'browser').glob('*.png')):shots.append({'path':'browser/'+p.name,'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'bytes':p.stat().st_size})
report['browser_screenshots']=shots;report['end_sha']=git('rev-parse','HEAD');report['end_porcelain']=git('status','--porcelain');report['same_sha_and_clean']=report['end_sha']==sha and not report['end_porcelain'];report['necessary_local_tests_passed']=all(r['exit_code']==0 for r in report['results']);report['finished_at']=dt.datetime.now(dt.timezone.utc).isoformat();save()
print('MANIFEST',str(out/'manifest.json'),flush=True)
sys.exit(0 if report['necessary_local_tests_passed']and report['same_sha_and_clean']else 1)
