from pathlib import Path
import datetime,json,tempfile
from fastapi.testclient import TestClient
from exchange_info.api import create_app
root=Path('/workspace/abroad-ncu-next3-fixed');out=Path('/workspace/ncu-verification-tmp/next3-bb806740e702892e78d358973cb2c54b739d3dbd/actual-api');out.mkdir(exist_ok=True)
rows=[('ncu-130','名古屋外國語大學 Nagoya University of Foreign Studies'),('ncu-134','熊本大學 Kumamoto University'),('ncu-135','龍谷大學 Ryukoku University')];manifest=[]
with tempfile.TemporaryDirectory(dir='/workspace/ncu-verification-tmp')as directory:
 client=TestClient(create_app(Path(directory)))
 dashboard=client.get('/student-dashboard',params={'school':'NCU'});assert dashboard.status_code==200
 for row,name in rows:
  records=[('workflow','/application-workflow',{'home_school':'NCU','school':name,'academic_year':'116'}),('life','/school-life-context',{'home_school':'NCU','school':name})]
  for admission,housing in [('unknown','unknown'),('accepted','on_campus'),('accepted','off_campus')]:records.append(('catalog-'+admission+'-'+housing,'/application-center/catalog',{'school':'NCU','target_school':name,'academic_year':'116','host_admission_status':admission,'housing_choice':housing}))
  for kind,route,params in records:
   result=client.get(route,params=params);assert result.status_code==200
   body=result.json()
   if kind.startswith('catalog'):
    docs=[d for d in body['items']if d['applicability']];assert len(docs)=={'ncu-130':13,'ncu-134':4,'ncu-135':6}[row]
    assert all(d['applicability']['status']=='needs_confirmation'and not d['download_available']and not d['applicability']['current_applicability_verified']for d in docs)
   p=out/(row+'-'+kind+'.json');p.write_text(json.dumps({'route':route,'params':params,'status':result.status_code,'body':body},ensure_ascii=False,indent=2)+'\n');manifest.append({'path':p.name,'route':route,'params':params})
  selected=next(p for p in dashboard.json()['partner_universities']if p['school_name']==name)
  (out/(row+'-dashboard-partner.json')).write_text(json.dumps(selected,ensure_ascii=False,indent=2)+'\n')
(out/'manifest.json').write_text(json.dumps({'candidate_sha':'bb806740e702892e78d358973cb2c54b739d3dbd','checked_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'requests':manifest,'current_116_verified':False},ensure_ascii=False,indent=2)+'\n')
print('15 real API responses and3 dashboard rows captured;23 docs in3states remain blocked')
