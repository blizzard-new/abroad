from pathlib import Path
import os,json,hashlib,datetime,subprocess
R=Path('/workspace/abroad-ntu-completion-20261011');V=R/'docs/ntu-completion-20261011/stage8/validation';H=Path(__file__).parent
read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();now=lambda:datetime.datetime.now(datetime.timezone.utc).isoformat()
original=read(V/'first-run-receipt.json');receipt=read(V/'run-receipt.json');assert receipt['jobs']['full-regression']['returncode']==1
assert sha(R/'sources/ntu/completion-2026-10-11.json')==receipt['source_sha256']
for key in ['code_files_sha256','materialized_files_sha256']:
    assert all(sha(R/path)==digest for path,digest in receipt[key].items())
tests={str(p.relative_to(R)):sha(p) for p in (R/'tests').rglob('*.py')}
changed={p for p,digest in receipt['test_files_sha256'].items() if tests[p]!=digest}
assert changed=={'tests/test_ntu_destination_enrichment.py'}
receipt['superseded_failed_runs']=[{**receipt['jobs']['full-regression'],'log':'full-regression-before-life-count-refresh.log','failure_cause':'Old fixed-count life fixture expected1963; reviewed dataset contains2124. Error-page exclusion assertions unchanged.','correction_receipt':'life-count-fixture-refresh.json','test_files_sha256_before':original['test_files_sha256']}]
receipt['test_files_sha256']=tests;receipt['source_code_tests_and_materialized_bytes_unchanged_during_tests']=False
receipt['test_input_change_between_attempts']={'path':'tests/test_ntu_destination_enrichment.py','reason':'Update fixed snapshot count after161 reviewed life references added.','source_code_materialized_and_e2e_inputs_unchanged':True,'before_after_receipt':'life-count-fixture-refresh.json'}
for name in ['browser','pr8-combined-browser']:
    receipt['jobs'][name]['retained_successful_attempt_after_non_e2e_fixture_refresh']=True
    receipt['jobs'][name]['source_and_runtime_input_bytes_unchanged']=True
    receipt['jobs'][name]['e2e_test_files_unchanged']=True
command=['/workspace/abroad/.venv/bin/python','-m','pytest','-q','--ignore=tests/e2e'];job={'command':command,'cwd':str(R),'started_at':now(),'log':'full-regression.log','source_sha256':receipt['source_sha256'],'test_files_sha256':tests,'correction_receipt':'life-count-fixture-refresh.json'}
receipt['jobs']['full-regression']=job;(V/'run-receipt.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n')
with (V/'full-regression.log').open('w') as log:
    result=subprocess.run(command,cwd=R,env=dict(os.environ,PYTHONPATH='src'),stdout=log,stderr=subprocess.STDOUT)
job.update(returncode=result.returncode,completed_at=now())
assert sha(R/'sources/ntu/completion-2026-10-11.json')==receipt['source_sha256']
for key in ['test_files_sha256','code_files_sha256','materialized_files_sha256']:
    assert all(sha(R/path)==digest for path,digest in receipt[key].items())
receipt['source_code_tests_and_materialized_bytes_unchanged_during_tests']=True;receipt['completed_at']=now()
(V/'run-receipt.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'full_regression_returncode':result.returncode,'source_sha256':receipt['source_sha256'],'unchanged_during_corrected_full_run':True}));raise SystemExit(result.returncode)
