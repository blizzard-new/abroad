from pathlib import Path
import datetime, json, requests
sha='e79e0ba50cd247284f8a61b86f6fb5ff4c9a6409'
out=Path('/tmp/ncu-ci-e79e0ba');out.mkdir(exist_ok=True)
assert not (out/'manifest.json').exists()
base='https://api.github.com/repos/blizzard-new/abroad'
paths={'workflow_runs':f'/actions/runs?head_sha={sha}','check_runs':f'/commits/{sha}/check-runs','status':f'/commits/{sha}/status'}
manifest={'checked_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'sha':sha,'queries':[]}
for name,path in paths.items():
    response=requests.get(base+path,timeout=15);(out/(name+'.json')).write_text(response.text)
    item={'name':name,'http_status':response.status_code,'url':base+path}
    if response.ok:
        d=response.json()
        if name=='workflow_runs':
            item['runs']=[{k:x.get(k)for k in ['id','name','status','conclusion','head_sha','html_url']}for x in d['workflow_runs']]
            for run in d['workflow_runs']:
                url=base+f'/actions/runs/{run["id"]}/jobs'
                jobs=requests.get(url,timeout=15);(out/f'jobs-{run["id"]}.json').write_text(jobs.text)
                item.setdefault('job_queries',[]).append({'run_id':run['id'],'http_status':jobs.status_code,'url':url,'total_count':jobs.json().get('total_count')if jobs.ok else None})
        elif name=='check_runs':item['runs']=[{k:x.get(k)for k in ['id','name','status','conclusion','head_sha','html_url']}for x in d['check_runs']]
        else:item['state']=d.get('state')
    manifest['queries'].append(item)
(out/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(manifest,ensure_ascii=False))
