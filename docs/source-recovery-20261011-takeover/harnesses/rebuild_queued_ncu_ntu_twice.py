"""Replay reconciled source data twice and require byte-for-byte determinism."""
from pathlib import Path
import gzip
import hashlib
import json
import subprocess
import sys

app = Path('/workspace/abroad-globe-20261011')
raw = Path('/workspace/recovery-evidence-20261011')
assert json.loads((raw/'integration-final7-full-suite-summary.json').read_text())['all_shards_same_clean_fixed_sha']
base = '5e7114182093fa77203ee946a4f86a88d3b10345'
protected = ['src/exchange_info/official_data/'+school for school in ['cgu','cgu_catalogue','ntpu','ccu','tku']]
protected += ['supabase/migrations','.github/workflows','uv.lock']
before = {path: subprocess.check_output(['git','ls-tree','-r',base,'--',path],cwd=app) for path in protected}

def hashes():
    paths = []
    for school in ['ncu','ntu']:
        paths.extend((app/'src/exchange_info/official_data'/school).rglob('*'))
    paths.append(app/'docs/data/ncu-completion-20261011/exchange-field-inventory.json.gz')
    paths.extend([app/'src/exchange_info/static/assets/school-images.json',
                  app/'src/exchange_info/official_data/university_locations.jsonl'])
    return {str(p.relative_to(app)): hashlib.file_digest(p.open('rb'),'sha256').hexdigest()
            for p in sorted(paths) if p.is_file()}

results = []
for iteration in range(2):
    for script in ['scripts/build_ncu_catalog.py','scripts/build_ntu_completion.py']:
        result = subprocess.run([sys.executable,script],cwd=app,check=True,capture_output=True,text=True)
        print(json.dumps({'iteration':iteration+1,'script':script,'output':result.stdout},ensure_ascii=False),flush=True)
    # Use the actual inventory function, preserving gzip's deterministic mtime.
    code = "from scripts.audit_ncu_completion import inventory; import gzip,json; from pathlib import Path; Path('docs/data/ncu-completion-20261011/exchange-field-inventory.json.gz').write_bytes(gzip.compress((json.dumps(inventory(),ensure_ascii=False,indent=2)+'\\n').encode(),mtime=0))"
    subprocess.run([sys.executable,'-c',code],cwd=app,check=True)
    results.append(hashes())
assert results[0] == results[1], [key for key in results[0] if results[0][key] != results[1].get(key)]
for path in protected:
    # Compare real working bytes, not just the unchanged index.
    for line in before[path].decode().splitlines():
        meta,name = line.split('\t',1)
        assert (app/name).read_bytes() == subprocess.check_output(['git','show',base+':'+name],cwd=app),name
for school in ['cgu','ntpu','ntu']:
    path = f'src/exchange_info/official_data/{school}/application_workflows.jsonl'
    assert (app/path).read_bytes() == subprocess.check_output(['git','show','f6ad1b8:'+path],cwd=app),path
report = {'offline_rounds':2,'all_generated_file_hashes_identical':True,
          'generated_files':len(results[1]),'hashes':results[1],
          'other_school_data_and_sql_workflow_dependency_bytes_unchanged_from':base,
          'original_cgu154_ntpu409_ntu288_workflows_byte_identical':True,
          'scope':'Rebuild integrity only; requires focused checks followed by clean same-SHA full acceptance.'}
(raw/'queued-ncu-ntu-offline-rebuild.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({k:v for k,v in report.items()if k!='hashes'},ensure_ascii=False))
