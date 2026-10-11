"""Install the exact wheel into an empty target and exercise it outside checkout."""
from pathlib import Path
import hashlib, json, os, subprocess, sys, tempfile

root = Path('/workspace/recovery-evidence-20261011')
build = json.loads((root/'integration-final5-wheel-integrity.json').read_text())
wheel = Path(build['wheel'])
assert hashlib.file_digest(wheel.open('rb'), 'sha256').hexdigest() == build['wheel_sha256']
target = Path('/workspace/abroad-integration-final5-wheel-installed-20261011')
assert not target.exists()
subprocess.run([sys.executable, '-m', 'pip', 'install', '--no-index', '--no-deps',
                '--no-compile', '--no-cache-dir', '--target', str(target), str(wheel)], check=True)
for row in build['files']:
    file = target/row['path']
    assert file.is_file() and hashlib.file_digest(file.open('rb'), 'sha256').hexdigest() == row['sha256'], row['path']
smoke = r'''
from pathlib import Path
import json, os
from fastapi.testclient import TestClient
import exchange_info.api as api
from exchange_info.storage import load_bundled_application_workflows
from exchange_info import cgu_catalogue
from exchange_info.tku_census import census_audit, school_audit_by_id
target=Path(os.environ['WHEEL_TARGET']).resolve()
assert Path(api.__file__).resolve().is_relative_to(target)
assert not any('/workspace/abroad-globe-20261011' in p for p in __import__('sys').path)
data=Path(os.environ['EXCHANGE_INFO_DATA_DIR'])
store=cgu_catalogue.CguCatalogue(data/'live-snapshot.json');view=store.refresh()
assert view.source.status=='retrieved' and view.source.last_attempt_result=='success'
live={'source':view.source.model_dump(mode='json'),'rows':len(view.partners),
      'receipts':json.loads(store.path.read_text())['source_receipts']}
app=api.create_app(data)
results=[]
with TestClient(app) as client:
    blocked=['/static/assets/tku-campuses/tku-sister-65-alternative-deea7d07.jpg','/static/assets/tku-campuses/tku-sister-52-alternative-e2537ab5.jpg']
    for path in blocked:assert client.get(path).status_code==404
    for path in ['/health','/','/static/app.js','/static/tku-campus-assets.js']:
        response=client.get(path);assert response.status_code==200,(path,response.status_code)
        results.append({'path':path,'status':response.status_code,'bytes':len(response.content)})
    for school,count in [('CGU',77),('NTPU',206),('NTU',288),('CCU',104),('NCU',214),('TKU',287)]:
        response=client.get('/student-dashboard',params={'school':school});assert response.status_code==200
        rows=response.json()['partner_universities'];assert len(rows)==count,(school,len(rows))
        for path in blocked:
            assert path not in response.text
            assert client.get(path).status_code==404
        coverage=client.get('/coverage',params={'school':school});assert coverage.status_code==200
        results.append({'school':school,'partner_rows':len(rows),'dashboard_bytes':len(response.content),'coverage_bytes':len(coverage.content)})
    original=census_audit();summary=client.get('/tku/partner-census')
    assert summary.json()=={k:v for k,v in original.items() if k!='schools'}
    for row in (original['schools'][0],original['schools'][-1]):
        assert client.get('/tku/partner-census/'+row['id']).json()==row
    assert client.get('/tku/partner-census/absent').status_code==404
workflows=load_bundled_application_workflows()
counts={name:sum(row.home_university==name for row in workflows) for name in ['長庚大學','國立臺北大學','國立臺灣大學']}
assert list(counts.values())==[154,409,288]
report={'imported_api':api.__file__,'working_directory':str(Path.cwd()),'api_results':results,'workflow_counts':counts,'cgu_live_public_fetch':live,'not_current_cycle_verification':True}
Path(os.environ['WHEEL_SMOKE_REPORT']).write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(report,ensure_ascii=False),flush=True)
'''
with tempfile.TemporaryDirectory(prefix='abroad-installed-wheel-smoke-') as work:
    env=dict(os.environ, PYTHONPATH=str(target), WHEEL_TARGET=str(target),
             PYTHONDONTWRITEBYTECODE='1', EXCHANGE_INFO_DATA_DIR=work+'/runtime-data',
             WHEEL_SMOKE_REPORT=str(root/'integration-final5-installed-wheel-smoke.json'))
    subprocess.run(['/workspace/abroad-six-final/.venv/bin/python','-c',smoke],cwd=work,env=env,check=True)
report={'sha':build['sha'],'wheel_sha256':build['wheel_sha256'],'target':str(target),
        'all_installed_files_hash_verified':len(build['files']),'fresh_target':True,'withdrawn_images_static404_after_each_of_six_dashboards':True,
        'dependency_scope':'Application installed fresh with --no-deps; dependency environment is the existing validated venv, not a fresh dependency resolution.',
        'smoke_report':'integration-final5-installed-wheel-smoke.json'}
(root/'integration-final5-installed-wheel-integrity.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report),flush=True)
