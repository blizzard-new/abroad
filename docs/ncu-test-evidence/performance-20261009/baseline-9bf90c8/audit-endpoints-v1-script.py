import datetime as dt,hashlib,json,sys,tempfile,time,subprocess
from pathlib import Path
from fastapi.testclient import TestClient
from exchange_info.api import create_app
from exchange_info.ncu_student_view import fetch_ncu_partner_universities
out=Path(sys.argv[1]);out.mkdir(exist_ok=True)
partners=fetch_ncu_partner_universities();names=[next(p.school_name for p in partners if word in p.school_name)for word in ['太原農林','復旦','新潟','北海道大學 Hokkaido University']]
report=dict(head=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),porcelain=subprocess.check_output(['git','status','--porcelain'],text=True).strip(),started_at=dt.datetime.now(dt.timezone.utc).isoformat(),scope='Exactly eight sequential local TestClient source-audit requests; first and second four-school cycle. Not whole browser boot.',requests=[])
with tempfile.TemporaryDirectory(prefix='ncu-bounded-api-',dir='/tmp')as tmp:
 with TestClient(create_app(Path(tmp)))as client:
  for cycle in range(2):
   for name in names:
    started=time.perf_counter();cpu=time.process_time();r=client.get('/partner-source-audit',params=dict(home_school='國立中央大學',school=name));elapsed=time.perf_counter()-started;used=time.process_time()-cpu
    assert r.status_code==200,(r.status_code,r.text[:100]);data=r.json();digest=hashlib.sha256(json.dumps(data,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest()
    report['requests'].append(dict(cycle=cycle,school=name,wall_seconds=elapsed,cpu_seconds=used,sha256=digest,response_bytes=len(r.content),source_count=len(data['source_evidence'])))
report['finished_at']=dt.datetime.now(dt.timezone.utc).isoformat();(out/'audit-endpoints.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(json.dumps([dict(cycle=x['cycle'],school=x['school'],seconds=round(x['wall_seconds'],3))for x in report['requests']],ensure_ascii=False))
