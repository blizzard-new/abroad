import datetime as dt,hashlib,json,os,subprocess
from pathlib import Path
from fastapi.testclient import TestClient
from exchange_info.api import create_app
root=Path('/workspace/abroad-ncu-p1-fixed');sha=subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip();assert sha=='2159409cacb6d8ac36bbafcc3ca6f2925f860fc9'
out=Path('/workspace/ncu-verification-tmp')/('p1-five-'+sha)/'api';out.mkdir(exist_ok=True)
client=TestClient(create_app(out/'isolated-data'))
report={'candidate_sha':sha,'captured_at':dt.datetime.now(dt.timezone.utc).isoformat(),'source':'real local API response without overrides','responses':[]}
dash=client.get('/student-dashboard',params={'school':'NCU'});assert dash.status_code==200
def save(file,response,params,path):
 raw=(json.dumps(response,ensure_ascii=False,indent=2)+'\n').encode();(out/file).write_bytes(raw);report['responses'].append({'path':path,'params':params,'file':file,'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw)})
for slug,term in [('nufs','名古屋外國語'),('kumamoto','熊本'),('ryukoku','龍谷')]:
 p=next(p for p in dash.json()['partner_universities']if term in p['school_name']);name=p['school_name'];save(slug+'-dashboard-partner.json',p,{'school':'NCU'},'/student-dashboard')
 for endpoint in ['application-workflow','school-life-context']:
  params={'home_school':'NCU','school':name,'academic_year':'116'};response=client.get('/'+endpoint,params=params);assert response.status_code==200;save(slug+'-'+endpoint+'.json',response.json(),params,'/'+endpoint)
 for admission,housing in [('unknown','unknown'),('accepted','on_campus'),('accepted','off_campus')]:
  params={'school':'NCU','target_school':name,'academic_year':'116','host_admission_status':admission,'housing_choice':housing};response=client.get('/application-center/catalog',params=params);assert response.status_code==200
  data=response.json();conditional=[i for i in data['items']if i.get('applicability')];expected={'nufs':13,'kumamoto':4,'ryukoku':14}[slug];assert len(conditional)==expected
  assert all(not i['download_available']and i['applicability']['status']=='needs_confirmation'for i in conditional)
  save(slug+'-catalog-'+admission+'-'+housing+'.json',data,params,'/application-center/catalog')
(out/'manifest.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print('18 API payloads preserved at',sha)
