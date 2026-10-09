from pathlib import Path
import datetime as dt
import hashlib
import json
import os
import subprocess
import sys
import xml.etree.ElementTree as ET

root=Path('/workspace/abroad-ncu-kansai-note-check')
out=Path('/workspace/ncu-verification-tmp/kansai-note-sync/candidate-a2578f8');out.mkdir(exist_ok=True)
python='/workspace/abroad/.venv/bin/python'
def git(*args):return subprocess.check_output(['git',*args],cwd=root,text=True).strip()
sha=git('rev-parse','HEAD'); assert sha=='a2578f853d6b16184689b9d29b25ff5f44810d8b' and not git('status','--porcelain')
env=dict(os.environ,TMPDIR='/workspace/ncu-verification-tmp',PYTHONPATH='src:/tmp')
for key in ['SUPABASE_URL','SUPABASE_SERVICE_ROLE_KEY']:env.pop(key,None)
report={'candidate_sha':sha,'started_at':dt.datetime.now(dt.timezone.utc).isoformat(),'start_sha':sha,'start_worktree_porcelain':'','results':[],'scope':'Six Kansai initial-reference confirmation_note fields only, matching source policies, generated policies and provenance input hash. New actual API notes asserted in three preparation states. No workflow, runtime, schema or next-three integration changes.','browser_rerun':False,'prior_browser_evidence_sha':'823450500cc32eb1ccc1e37f7fdefbcdcdf5754e','prior_kyutech_failure_closed':False,'full_ci_equivalence':False}
def save():(out/'manifest.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
def run(name,args,junit=False):
 assert git('rev-parse','HEAD')==sha and not git('status','--porcelain')
 started=dt.datetime.now(dt.timezone.utc).isoformat();argv=list(args)
 if junit:argv+=['--junitxml',str(out/f'{name}.xml')]
 print('START',name,started,flush=True)
 with (out/f'{name}.log').open('w') as f:r=subprocess.run(argv,cwd=root,env=env,stdout=f,stderr=subprocess.STDOUT)
 row={'name':name,'argv':argv,'cwd':str(root),'started_at':started,'finished_at':dt.datetime.now(dt.timezone.utc).isoformat(),'exit_code':r.returncode,'log':f'{name}.log'}
 if junit:
  tree=ET.parse(out/f'{name}.xml').getroot();suites=[tree]if tree.tag=='testsuite'else list(tree.iter('testsuite'))
  row['junit']={k:sum(int(s.attrib.get(k,'0'))for s in suites)for k in ['tests','failures','errors','skipped']}
 report['results'].append(row);save();print('END',name,r.returncode,row.get('junit',{}),flush=True)
 if r.returncode:raise SystemExit(r.returncode)
save()
run('affected_api_document_life',[python,'-m','pytest','-q','tests/test_ncu_japan3.py','tests/test_ncu_shizuoka_chuo_kansai.py','tests/test_ncu_document_conditions.py','tests/test_life_context.py'],True)
run('openapi_snapshot',[python,'scripts/export_openapi.py','--check'])
run('scoped_diff',['git','diff','--check','c8b02117654d16db46587aae3a7532a2cae7864f',sha])
api_capture='''from pathlib import Path
from tempfile import TemporaryDirectory
import json
from fastapi.testclient import TestClient
from exchange_info.api import create_app
out=Path('/workspace/ncu-verification-tmp/kansai-note-sync/candidate-a2578f8')
with TemporaryDirectory(dir='/workspace/ncu-verification-tmp') as directory:
 client=TestClient(create_app(Path(directory)))
 workflow=client.get('/application-workflow',params={'home_school':'NCU','school':'關西大學 Kansai University','academic_year':'116'})
 assert workflow.status_code==200
 names={d['name'] for s in workflow.json()['steps'] if s['rule_id']=='ncu-129-host-initial-reference' for d in s['document_requirements']}
 results=[]
 for admission,housing in [('unknown','unknown'),('accepted','on_campus'),('accepted','off_campus')]:
  params={'school':'NCU','target_school':'關西大學 Kansai University','academic_year':'116','host_admission_status':admission,'housing_choice':housing}
  response=client.get('/application-center/catalog',params=params);assert response.status_code==200
  items=[d for d in response.json()['items']if d['name']in names]
  assert len(items)==6 and all('所有發出三月內'not in d['applicability']['note']and'對護照等文件的適用範圍仍待兩校確認'in d['applicability']['note']for d in items)
  results.append({'params':params,'status':response.status_code,'response':response.json()})
 (out/'actual-api-catalog-responses.json').write_text(json.dumps(results,ensure_ascii=False,indent=2)+'\\n')
 print('Captured three real API catalogs, six corrected initial notes each.')
'''
run('actual_api_payload_capture',[python,'-c',api_capture])
report.update(end_sha=git('rev-parse','HEAD'),end_worktree_porcelain=git('status','--porcelain'),finished_at=dt.datetime.now(dt.timezone.utc).isoformat())
report['same_sha_and_clean']=report['end_sha']==sha and not report['end_worktree_porcelain'];report['necessary_local_tests_passed']=report['same_sha_and_clean']and all(r['exit_code']==0 for r in report['results']);save()
print('DONE',report['necessary_local_tests_passed'],str(out/'manifest.json'),flush=True)
