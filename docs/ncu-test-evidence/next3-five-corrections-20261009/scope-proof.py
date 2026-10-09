import copy,gzip,hashlib,json,subprocess
from pathlib import Path
root=Path('/workspace/abroad-ncu');oldsha='bb4cecd8030946e59bed494509d206c356e5c210';sha='2159409cacb6d8ac36bbafcc3ca6f2925f860fc9';out=Path('/workspace/ncu-p1-five-20261009')
def raw(sha,path):return subprocess.check_output(['git','show',sha+':'+path],cwd=root)
def doc(sha,path):return json.loads(raw(sha,path))
def diffpaths(a,b):return set(subprocess.check_output(['git','diff','--name-only',a,b],cwd=root,text=True).splitlines())
manual='sources/ncu/2026-10-08/reviewed-host-records.json';a=doc(oldsha,manual);b=doc(sha,manual);changed={k for k in a if a[k]!=b[k]};assert changed=={'ncu-130','ncu-134','ncu-135'}
allowed={'ncu-130':{'courses'},'ncu-134':{'eligibility','language','insurance'},'ncu-135':{'host_documents','housing','arrival'}}
fields={}
for id in changed:
 fields[id]=[f for f in a[id]['fields']if a[id]['fields'][f]!=b[id]['fields'][f]];assert set(fields[id])==allowed[id]
 left,right=copy.deepcopy(a[id]),copy.deepcopy(b[id])
 for key in ['fields','checked_at']:left.pop(key);right.pop(key)
 if id=='ncu-135':
  x,y=left.pop('host_document_stages'),right.pop('host_document_stages')
  assert len(x)==len(y)==9
  stage_changes=[p['id']for p,q in zip(x,y)if p!=q];assert stage_changes==['initial-reference','housing','arrival']
 assert left==right,id
polpath='sources/ncu/2026-10-08/document-conditions.json';p,q=doc(oldsha,polpath),doc(sha,polpath)
assert len(q)==len(p)+8
policy_changes=[]
for x,y in zip(p,q):
 if x!=y:
  assert x['rule_id']=='ncu-135-host-initial-reference'
  keys={k for k in set(x)|set(y)if x.get(k)!=y.get(k)};assert keys=={'confirmation_note','checked_at'}
  policy_changes.append(x['requirement_name'])
assert len(policy_changes)==6
new_policies=q[len(p):];assert all(x['school_name']=='龍谷大學 Ryukoku University'and x['requires_institutional_confirmation']and not x['current_applicability_verified']for x in new_policies)
delta=diffpaths(oldsha,sha);assert all(x.startswith(('sources/ncu/','src/exchange_info/official_data/ncu/','tests/'))for x in delta)
protected=['sources/ncu/candidates/','docs/ncu-review-index/71-2637de2/','docs/ncu-review-index/next3-bb806740/','docs/ncu-test-evidence/']
assert not any(path.startswith(tuple(protected))for path in delta)
peers={}
for label,ref in [('CCU','origin/data/ccu-exchange-20261008'),('TKU','origin/data/tku-exchange-20261008')]:
 peer_sha=subprocess.check_output(['git','rev-parse',ref],cwd=root,text=True).strip();paths=diffpaths('f6ad1b8',peer_sha)
 whole=diffpaths('f6ad1b8',sha)
 peers[label]={'sha':peer_sha,'this_correction_shared_paths':sorted(paths&delta),'whole_ncu_branch_shared_paths':sorted(paths&whole)}
 assert not(paths&delta)
inputs=['sources/ncu/2026-10-08/reviewed-host-records.json','sources/ncu/2026-10-08/document-conditions.json','sources/ncu/2026-10-08/host-web-evidence.json.gz','sources/ncu/2026-10-08/host-kumamoto-next3-ug-brochure-visual-review.json']
proof={'candidate_sha':sha,'baseline_sha':oldsha,'changed_manual_rows':sorted(changed),'manual_rows_unchanged':len(a)-len(changed),'changed_fields':fields,'changed_ryukoku_stages':stage_changes,'existing_policy_note_changes':policy_changes,'added_document_policies':len(new_policies),'changed_files':sorted(delta),'input_sha256':{path:hashlib.sha256(raw(sha,path)).hexdigest()for path in inputs},'preserved_paths':protected,'peers':peers,'current_116_verified':False,'unreviewed_new_schools':0,'runtime_schema_ui_shared_files_changed':False,'generated_scope':json.loads((out/'generated-scope.json').read_text())}
(out/'committed-scope.json').write_text(json.dumps(proof,ensure_ascii=False,indent=2)+'\n')
pretest=root.parent/'abroad-ncu-p1-before/tests/test_ncu_next3_review_corrections.py'
pre={'baseline_sha':oldsha,'test_overlay_path':'tests/test_ncu_next3_review_corrections.py','test_overlay_sha256':hashlib.sha256(pretest.read_bytes()).hexdigest(),'runtime_and_data_clean_baseline':True,'selected_cases':5,'failed_product_cases':5,'command':"pytest -q tests/test_ncu_next3_review_corrections.py -k 'initial_four or later_conditional or nationality or private_insurance or study_abroad'",'primary_log':'pre-fix-corrected.log','primary_junit':'pre-fix-corrected.xml','earlier_invalid_probe':{'log':'pre-fix.log','junit':'pre-fix.xml','reason':'Test used nonexistent audit points property in three cases; corrected to note before valid baseline replay.'},'intermediate_unbuilt_probe':{'log':'working-api.log','junit':'working-api.xml','reason':'Scope-copy script stopped before applying generated bundle (nonexistent optional research_records.jsonl); tests read old generated bundle. Superseded by rebuilt result and fixed-SHA validation.'},'pre_commit_rebuilt_probe':{'log':'working-api-rebuilt.log','junit':'working-api-rebuilt.xml','passed':23,'fixed_sha_evidence':False}}
assert subprocess.check_output(['git','diff','--name-only'],cwd=root.parent/'abroad-ncu-p1-before',text=True).strip()==''
(out/'pre-fix-manifest.json').write_text(json.dumps(pre,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'candidate_sha':sha,'manual_rows_unchanged':len(a)-len(changed),'policy_additions':8,'protected_paths_unchanged':True,'shared_file_delta':{k:len(v['this_correction_shared_paths'])for k,v in peers.items()}}))
