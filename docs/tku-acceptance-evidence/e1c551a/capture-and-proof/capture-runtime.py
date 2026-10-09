from pathlib import Path
import json,re
root=Path('/tmp/tku-ci-governance-e1c551a')
steps=[]
for kind in ['pr','push']:
    obj=json.loads((root/f'{kind}-jobs.json').read_text())
    if isinstance(obj.get('jobs'),dict): obj=obj['jobs']
    for job in obj['jobs']:
        step=next(x for x in job['steps'] if x['name']=='Validate isolated Supabase runtime')
        assert step['conclusion']=='success'
        steps.append({'kind':kind,'job_id':job['id'],'conclusion':step['conclusion']})
reports=[]
for path in sorted(root.glob('job-*.log')):
    objects=[]
    for line in path.read_text().splitlines():
        plain=re.sub(r'^\d{4}-\d\d-\d\dT\S+Z ', '', line)
        if plain.startswith('{') and '"cleanup_status"' in plain:
            objects.append(json.loads(plain))
    assert len(objects)==1
    val=objects[0]
    assert val['status']==val['cleanup_status']=='passed' and val['migration_count']==33
    policy=val['tku_selected_community_policy']
    assert policy['registry_alias_vectors']==27 and policy['verified_alias_publications']==2
    assert policy['retry_duplicates']==0 and policy['unverified_writes_denied']==8
    reports.append({'job_id':int(path.stem.split('-')[1]),'source_original_decoded_log':path.name,'actual_runtime':val})
assert len(steps)==8 and len(reports)==6
result={'head_sha':'e1c551a80ae4503a0c3be4359d028dd1562f3c6c','runtime_successful_steps':len(steps),'step_evidence':steps,'held_complete_runtime_json_count':len(reports),'reports':reports,'limitation':'Full decoded shard0 job logs were not retrieved; eight successful runtime steps are original job metadata. Six runtime JSON reports are actual complete original smaller-job log lines; the other two reports are not invented. No production database used.'}
(root/'actual-supabase-runtime.json').write_text(json.dumps(result,indent=2)+'\n')
print({'successful_steps':len(steps),'held_actual_complete_reports':len(reports)})
