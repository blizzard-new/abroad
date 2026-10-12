from pathlib import Path
import json,hashlib,shutil,datetime,re,subprocess
R=Path('/workspace/abroad-ntu-completion-20261011');H=Path(__file__).parent;V=R/'docs/ntu-completion-20261011/stage8/validation'
read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
receipt=read(V/'run-receipt.json');assert receipt.get('completed_at') and receipt['source_code_tests_and_materialized_bytes_unchanged_during_tests']
assert receipt['jobs']['pr8-combined-focused']['returncode']==1
assert all(j['returncode']==0 for name,j in receipt['jobs'].items() if name!='pr8-combined-focused')
corrected=read(H/'corrected-focused-run.json');assert corrected['returncode']==0
assert '34 passed' in (V/corrected['log']).read_text()
oldlog=V/'pr8-combined-focused-before-isolated-harness-fix.log'
assert '1 failed, 33 passed' in oldlog.read_text() and 'schoolVisualRecordFor is not defined' in oldlog.read_text()
receipt.setdefault('superseded_failed_runs',[]).append({**receipt['jobs']['pr8-combined-focused'],'log':oldlog.name,'failure_cause':'Partial-JavaScript extraction test omitted fixed PR8 helper dependencies.','correction':'Only isolated acceptance-tree test harness dependencies expanded; original assertions and fixed PR8 app.js bytes unchanged.','correction_receipt':'isolated-test-harness-fix.json'})
receipt['jobs']['pr8-combined-focused']={**corrected,'log':'pr8-combined-focused.log','original_log':corrected['log'],'isolated_test_harness_sha256':read(V/'isolated-test-harness-fix.json')['test_after_sha256']}
shutil.copyfile(V/corrected['log'],V/'pr8-combined-focused.log')
assert sha(R/'sources/ntu/completion-2026-10-11.json')==receipt['source_sha256']
for key in ['test_files_sha256','code_files_sha256','materialized_files_sha256']:
    assert all(sha(R/path)==digest for path,digest in receipt[key].items())
receipt['correction_completed_at']=datetime.datetime.now(datetime.timezone.utc).isoformat()
receipt['all_current_jobs_passed']=True
(V/'run-receipt.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n')
old=read(H/'parallel-base-747.json');old700=json.loads(subprocess.check_output(['git','show','HEAD:sources/ntu/completion-2026-10-11.json'],cwd=R));current=read(R/'sources/ntu/completion-2026-10-11.json')
mapping=lambda d:{o['observation_id']:o for s in d['schools'] for o in s['observations']};before=mapping(old700);after=mapping(current)
assert len(before)==700 and len(after)==1373 and all(after[k]==v for k,v in before.items())
(V/'prior-observation-preservation.json').write_text(json.dumps({'prior_observations':700,'current_observations':1373,'all_prior_observation_values_identical':True,'deleted_prior_observation_ids':[]},indent=2)+'\n')
files=['main-browser-evidence/new-reference-browser/東京外國語大學-390.png','main-browser-evidence/new-reference-browser/關西學院大學-1440.png']
review={'reviewed_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'manual_visual_checks':'Root visually inspected two actual browser screenshots. Scoped years, official links and continuing unconfirmed selection language are readable; mobile is within viewport. Remaining cases have automated assertions, not manual visual claims.','screenshots':[{'path':p,'sha256':sha(V/p)} for p in files]}
(V/'manual-browser-visual-review.json').write_text(json.dumps(review,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'observations':1373,'all_current_jobs_passed':True,'superseded_failure_preserved':True,'shared_inputs_unchanged':True}))
