from pathlib import Path
import datetime as dt
import hashlib
import json
import os
import subprocess
import sys
import xml.etree.ElementTree as ET

root=Path('/tmp/abroad-ncu-hokkaido-correction'); python='/workspace/abroad/.venv/bin/python'
def git(*args):
    return subprocess.check_output(['git',*args],cwd=root,text=True).strip()
sha=git('rev-parse','HEAD')
if git('status','--porcelain'):
    raise SystemExit('Refusing candidate verification with uncommitted changes')
out=Path('/tmp')/f'ncu-candidate-{sha}';out.mkdir(exist_ok=True)
env=dict(os.environ,PYTHONPATH='src',PLAYWRIGHT_BROWSERS_PATH='/workspace/.abroad-cloud-tools/ms-playwright',UV_CACHE_DIR='/tmp/ncu-uv-cache')
for key in ['SUPABASE_URL','SUPABASE_SERVICE_ROLE_KEY']:env.pop(key,None)
report={'candidate_sha':sha,'started_at':dt.datetime.now(dt.timezone.utc).isoformat(),'start_sha':sha,'start_worktree_porcelain':'','results':[], 'production_actions':False,'full_ci_equivalence':False}
coverage=json.loads((root/'src/exchange_info/official_data/ncu/catalog-completeness.json').read_text())
report['data_coverage']=coverage
report['data_acceptance_passed']=coverage['reviewed_host_records']==coverage['catalog_entries'] and coverage['host_full_116_verification_count']==coverage['catalog_entries']
report['ci_status']='not_checked_yet'
def save():
    (out/'manifest.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
def run(name,argv,cwd=root,junit=False):
    if git('rev-parse','HEAD')!=sha or git('status','--porcelain'):
        report['frozen_candidate_violation']=True;save();raise SystemExit('Candidate changed during checks')
    args=list(argv)
    xml=out/f'{name}.xml'
    if junit:args+=['--junitxml',str(xml)]
    print('START',name,dt.datetime.now(dt.timezone.utc).isoformat(),flush=True)
    started=dt.datetime.now(dt.timezone.utc)
    with (out/f'{name}.log').open('w') as f:
        result=subprocess.run(args,cwd=cwd,env=env,stdout=f,stderr=subprocess.STDOUT)
    row={'name':name,'command':args,'cwd':str(cwd),'exit_code':result.returncode,'started_at':started.isoformat(),'finished_at':dt.datetime.now(dt.timezone.utc).isoformat(),'log':str(out/f'{name}.log')}
    if junit and xml.exists():
        tree=ET.parse(xml).getroot();suites=[tree] if tree.tag=='testsuite' else list(tree.iter('testsuite'))
        row['junit']={k:sum(int(s.attrib.get(k,'0')) for s in suites) for k in ['tests','failures','errors','skipped']}
        row['failed_test_cases']=[{'name':case.attrib.get('name'),'class':case.attrib.get('classname'),'message':failure.attrib.get('message')} for case in tree.iter('testcase') for failure in case if failure.tag in ['failure','error']]
    report['results'].append(row);save();print('END',name,'exit',result.returncode,row.get('junit',{}),flush=True)

save()
run('ncu_unit',[python,'-m','pytest','-q','tests/test_ncu_integration.py','tests/test_ncu_document_conditions.py','tests/test_ncu_source_collector.py','tests/test_school_completeness.py'],junit=True)
run('shared_regression',[python,'-m','pytest','-q','tests/test_school_content.py','tests/test_ntpu_support.py','tests/test_ntu_audit.py','tests/test_ntu_integration.py','tests/test_application_rules.py','tests/test_application_document_catalog.py','tests/test_application_documents_api.py','tests/test_fit_signals.py','tests/test_task_documents_and_reference_plan.py','tests/test_workflow_structuring.py','tests/test_account_workspace_api.py','tests/test_application_workflow.py','tests/test_workflow_context_api.py','tests/test_workflow_catalog_cache.py'],junit=True)
run('existing_gate_failures',[python,'-m','pytest','-q','tests/test_ntpu_bundled_data.py','tests/test_frontend_contract.py','tests/test_rag.py'],junit=True)
run('openapi',[python,'scripts/export_openapi.py','--check'])
run('main_workflow_export',[python,'/tmp/ncu-omu-parity-export.py'],cwd=Path('/tmp/abroad-ncu-baseline'))
run('workflow_parity',[python,'/tmp/ncu-omu-parity-compare.py'])
if Path('/tmp/ncu-omu-cross-parity.json').exists():report['workflow_parity']=json.loads(Path('/tmp/ncu-omu-cross-parity.json').read_text());save()
for name in ['app','discovery-ui','multi-plan']:run('js_'+name,['node','--check',f'src/exchange_info/static/{name}.js'])
run('diff',['git','diff','--check'])
run('lock',['uv','lock','--check'])
run('browser_ncu_ntu',[python,'-m','pytest','-q','tests/e2e/test_ncu_acceptance.py','tests/e2e/test_ncu_niigata.py','tests/e2e/test_ncu_kyutech.py','tests/e2e/test_ncu_hokkaido.py','tests/e2e/test_ncu_school.py','tests/e2e/test_ntu_school.py'],junit=True)
# Preserve original browser screenshots before the cold checks reuse paths.
original=[]
for path in sorted(Path('/tmp/ncu-audit/browser').glob('*.png')):
    if dt.datetime.fromtimestamp(path.stat().st_mtime,dt.timezone.utc).isoformat()>=report['started_at']:
        target=out/'original-browser'/path.name;target.parent.mkdir(exist_ok=True);target.write_bytes(path.read_bytes());original.append({'path':str(target),'sha256':hashlib.sha256(target.read_bytes()).hexdigest()})
report['original_browser_evidence']=original;save()
for i in range(1,4):run(f'performance_cold_{i}',[python,'/tmp/ncu-niigata-perf-v2.py',str(i),sha])
report['performance']=[json.loads(path.read_text()) for path in sorted((out/'performance').glob('cold-*.json'))]
shots=[]
for path in sorted(Path('/tmp/ncu-audit/browser').glob('*.png')):
    if dt.datetime.fromtimestamp(path.stat().st_mtime,dt.timezone.utc).isoformat()>=report['started_at']:
        target=out/'browser'/path.name;target.parent.mkdir(exist_ok=True);target.write_bytes(path.read_bytes());shots.append({'path':str(target),'sha256':hashlib.sha256(target.read_bytes()).hexdigest()})
report['browser_evidence']=shots
report['end_sha']=git('rev-parse','HEAD');report['end_worktree_porcelain']=git('status','--porcelain')
report['same_sha_at_end']=git('rev-parse','HEAD')==sha and not git('status','--porcelain')
report['necessary_local_tests_passed']=all(row['exit_code']==0 for row in report['results'])
report['acceptance_status']='blocked' if not report['data_acceptance_passed'] or not report['necessary_local_tests_passed'] or not report['same_sha_at_end'] else 'awaiting_ci_and_human_review'
report['finished_at']=dt.datetime.now(dt.timezone.utc).isoformat();save()
print('MANIFEST',str(out/'manifest.json'),report['acceptance_status'],flush=True)
sys.exit(0 if report['necessary_local_tests_passed'] and report['same_sha_at_end'] else 1)
