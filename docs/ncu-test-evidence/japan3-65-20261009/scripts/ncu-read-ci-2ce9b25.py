from pathlib import Path
import requests,json,datetime
sha='2ce9b25f8314dd4be457b3ae1be3fc3dadad12e0';out=Path('/tmp/ncu-ci-2ce9b25');out.mkdir(exist_ok=True)
base='https://api.github.com/repos/blizzard-new/abroad'
paths={'workflow_runs':f'/actions/runs?head_sha={sha}','check_runs':f'/commits/{sha}/check-runs','status':f'/commits/{sha}/status'}
r={'checked_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'sha':sha,'queries':[]}
for name,path in paths.items():
 response=requests.get(base+path,timeout=30);(out/(name+'.json')).write_text(response.text);item={'name':name,'http_status':response.status_code,'url':base+path}
 if response.ok:
  d=response.json()
  if name=='workflow_runs':item['runs']=[{k:x.get(k)for k in ['id','name','status','conclusion','head_sha','html_url']}for x in d['workflow_runs']]
  elif name=='check_runs':item['runs']=[{k:x.get(k)for k in ['id','name','status','conclusion','head_sha','html_url']}for x in d['check_runs']]
  else:item['state']=d.get('state')
 r['queries'].append(item)
(out/'manifest.json').write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n');print(json.dumps(r,ensure_ascii=False))
