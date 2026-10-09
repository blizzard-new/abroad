import datetime as dt,hashlib,json,os,subprocess,sys,xml.etree.ElementTree as ET
from pathlib import Path
root=Path('/workspace/abroad-ncu-p1-fixed');python='/workspace/abroad/.venv/bin/python'
def git(*args):return subprocess.check_output(['git',*args],cwd=root,text=True).strip()
sha=git('rev-parse','HEAD');assert not git('status','--porcelain')
out=Path('/workspace/ncu-verification-tmp')/('p1-five-'+sha);out.mkdir(exist_ok=True)
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
run('ncu_api_sources_life',[python,'-m','pytest','-q','tests/test_ncu_integration.py','tests/test_ncu_document_conditions.py','tests/test_ncu_source_collector.py','tests/test_school_completeness.py','tests/test_ncu_snapshot_cache.py','tests/test_ncu_japan3.py','tests/test_ncu_tcu_toyama_fukui.py','tests/test_ncu_shizuoka_chuo_kansai.py','tests/test_ncu_nufs_kumamoto_ryukoku.py','tests/test_ncu_next3_review_corrections.py'],True)
run('cgu_ntpu_ntu_shared_regression',[python,'-m','pytest','-q','tests/test_school_content.py','tests/test_cgu_bundled_data.py','tests/test_ntpu_support.py','tests/test_ntu_audit.py','tests/test_ntu_integration.py','tests/test_application_rules.py','tests/test_application_document_catalog.py','tests/test_application_documents_api.py','tests/test_fit_signals.py','tests/test_task_documents_and_reference_plan.py','tests/test_workflow_structuring.py','tests/test_account_workspace_api.py','tests/test_application_workflow.py','tests/test_workflow_context_api.py','tests/test_workflow_catalog_cache.py','tests/test_life_context.py','tests/test_public_translation.py','tests/test_public_translation_cold_cache.py'],True)
run('existing_contract_gate',[python,'-m','pytest','-q','tests/test_ntpu_bundled_data.py','tests/test_frontend_contract.py','tests/test_rag.py'],True)
run('openapi_snapshot',[python,'scripts/export_openapi.py','--check'])
run('frozen_71_index',[python,'scripts/build_ncu_review_index.py','--check','--output-dir','docs/ncu-review-index/71-2637de2'])
run('prior_three_school_index',[python,'scripts/build_ncu_review_index.py','--check','--output-dir','docs/ncu-review-index/next3-bb806740'])
run('browser_corrected_three_school_content_and_save',[python,'-m','pytest','-q','tests/e2e/test_ncu_nufs_kumamoto_ryukoku.py'],True)
run('lock_writable_cache',['uv','lock','--check'])
run('scoped_whitespace',['git','diff','--check',report['baseline_sha'],sha])
shots=[]
for p in sorted((out/'browser').glob('*.png')):shots.append({'path':'browser/'+p.name,'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'bytes':p.stat().st_size})
report['browser_screenshots']=shots;report['end_sha']=git('rev-parse','HEAD');report['end_porcelain']=git('status','--porcelain');report['same_sha_and_clean']=report['end_sha']==sha and not report['end_porcelain'];report['necessary_local_tests_passed']=all(r['exit_code']==0 for r in report['results']);report['finished_at']=dt.datetime.now(dt.timezone.utc).isoformat();save()
print('MANIFEST',str(out/'manifest.json'),flush=True)
sys.exit(0 if report['necessary_local_tests_passed']and report['same_sha_and_clean']else 1)
