"""Reconcile round8 source values against the accepted integrated baseline."""
from pathlib import Path
import json, subprocess, hashlib
app=Path('/workspace/abroad-globe-20261011')
raw=Path('/workspace/recovery-evidence-20261011')
def git(*args):return subprocess.check_output(['git',*args],cwd=app)
base_sha=git('rev-parse','HEAD').decode().strip()
assert base_sha=='4a011fab8ecdb98e4bca2ca2368ec28eaf194b78'
assert git('rev-parse','MERGE_HEAD').decode().strip()=='1b9563c58e2fa83c3c2510a40b7ccdd126db9dd1'
old='11項Yes/No/Remarks'.encode();new='10項Yes/No/Remarks'.encode()
paths=git('diff','--name-only','--diff-filter=U').decode().splitlines()
assert paths and all(p.startswith('src/exchange_info/official_data/ccu/') for p in paths)
for p in paths:
    base,ours,theirs=[git('show',f':{i}:{p}') for i in (1,2,3)]
    assert ours==base.replace(old,new),p
    assert old in theirs,p
    (app/p).write_bytes(theirs.replace(old,new))
    git('add','--',p)
bundle=app/'src/exchange_info/official_data/ccu'
source=bundle/'completion-eighth-field-input.json'
fields=json.loads(source.read_text())
review=json.loads((raw/'ccu-eighth-independent-semantic-review.json').read_text())
for fix in review['integration_clarifications_required']:
    field=next(r for r in fields if r['ccu_page']==fix['page'] and r['field']==fix['field'])
    assert field['value'].count(fix['original'])==1
    field['value']=field['value'].replace(fix['original'],fix['replacement'])
source.write_text(json.dumps(fields,ensure_ascii=False,indent=2)+'\n')
# The incoming snapshot contains the upstream11-question error. Bind this
# comparison to the actual integration baseline, with upstream provenance kept,
# so a previous integration correction is not counted as new round8 research.
baseline=bundle/'completion-eighth-baseline.json'
data=json.loads(baseline.read_text())
prior=json.loads(git('show',base_sha+':src/exchange_info/official_data/ccu/completion-reviewed-fields.json'))['schools']
normalized=json.loads(json.dumps(data['prior_fields'],ensure_ascii=False).replace(old.decode(),new.decode()))
assert normalized==prior
data['upstream_prior_commit']=data['prior_commit'];data['prior_commit']=base_sha
data['upstream_baseline_sha256']=hashlib.sha256(git('show','MERGE_HEAD:src/exchange_info/official_data/ccu/completion-eighth-baseline.json')).hexdigest()
data['integration_baseline_note']='Prior integrated CCU fields, retaining the previously verified10-question Medical Assessment correction. Other baseline fields exactly match the upstream seventh batch.'
data['prior_fields']=prior
baseline.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
(raw/'ccu-eighth-merge-resolution.json').write_text(json.dumps({'base':base_sha,'input':'1b9563c58e2fa83c3c2510a40b7ccdd126db9dd1','conflicts_resolved':paths,'overlap':'Only prior11to10medical correction','source_clarifications':review['integration_clarifications_required'],'baseline_provenance':data['upstream_baseline_sha256']},ensure_ascii=False,indent=2)+'\n')
