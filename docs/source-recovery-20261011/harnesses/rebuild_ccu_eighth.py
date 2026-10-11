from pathlib import Path
import subprocess,json,hashlib,sys
app=Path('/workspace/abroad-globe-20261011');raw=Path('/workspace/recovery-evidence-20261011')
scripts=['review_ccu_public_round8.py','build_ccu_completion_reviews.py','build_ccu_completion_inventory.py','build_ccu_gap_research_queue.py','build_ccu_remaining_public_worklist.py','build_ccu_public_round8_progress.py']
records=[]
for iteration in range(2):
 for script in scripts:
  result=subprocess.run([sys.executable,'scripts/'+script],cwd=app,check=True,text=True,capture_output=True)
  print(script,result.stdout,flush=True)
 bundle=app/'src/exchange_info/official_data/ccu'
 hashes={str(p.relative_to(app)):hashlib.file_digest(p.open('rb'),'sha256').hexdigest() for p in bundle.glob('*.json')}
 records.append(hashes)
assert records[0]==records[1],set(k for k in records[0] if records[0][k]!=records[1].get(k))
progress=json.loads((bundle/'completion-eighth-public-progress.json').read_text())
assert progress['changed_host_fields']==24
assert progress['previously_missing_host_fields_filled']==14
assert progress['all_public_policy_research_exhausted'] is False
assert progress['original_urls_with_recorded_reading_extent']==370
assert progress['all_reading_records']==378
assert progress['original_all_visible_read_records']==107
assert progress['original_partially_screened_records']==263
p=app/'src/exchange_info/official_data/ccu/application_workflows.jsonl'
assert p.read_bytes()==subprocess.check_output(['git','show','HEAD:'+str(p.relative_to(app))],cwd=app)
report={'input':'1b9563c58e2fa83c3c2510a40b7ccdd126db9dd1','scripts':scripts,'offline_rounds':2,'all_ccu_top_level_json_hashes_identical_after_second_round':True,'workflow_byte_parity_to_prior_head':True,'progress':progress,'final_hashes':records[1]}
(raw/'ccu-eighth-offline-rebuild.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({k:v for k,v in report.items() if k not in ['progress','final_hashes']}))
