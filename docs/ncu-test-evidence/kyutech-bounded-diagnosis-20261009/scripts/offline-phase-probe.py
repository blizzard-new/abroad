"""Exactly one three-request concurrent ASGI probe, no browser/profile reruns."""
from pathlib import Path
import concurrent.futures, contextvars, datetime, functools, importlib, json, os, shutil, threading, time
from fastapi.testclient import TestClient
from exchange_info import api, storage
from exchange_info.storage import ensure_data_dirs
from ncu_kyutech_server_diagnostic import ServerTiming, ROWS, RID, record
out=Path(os.environ['NCU_KYUTECH_TIMING_OUT']);data=out/'isolated-data';ensure_data_dirs(data)
for name in ['application_workflows.jsonl','collection_audits.jsonl','exchange_info.json','pages.jsonl','structured_sources.jsonl']:
 p=Path('data/processed')/name
 if p.exists():shutil.copy2(p,data/'processed'/name)
SPAN=[];LOCK=threading.Lock()
def timed(fn,label):
 @functools.wraps(fn)
 def run(*a,**kw):
  start=time.monotonic();cpu=time.thread_time()
  try:return fn(*a,**kw)
  finally:
   with LOCK:SPAN.append({'rid':RID.get(),'function':label,'wall_ms':(time.monotonic()-start)*1000,'thread_cpu_ms':(time.thread_time()-cpu)*1000})
 return run
for mod,names in [(api,['load_bundled_application_workflows','load_application_workflows','load_destination_profiles','complete_destination_profile']), (storage,['read_jsonl','_cached_workflows'])]:
 for name in names:
  if hasattr(mod,name):setattr(mod,name,timed(getattr(mod,name),mod.__name__+'.'+name))
app=api.create_app(data)
for route in app.routes:
 if not hasattr(route,'dependant'):continue
 fn=route.dependant.call
 if not __import__('inspect').iscoroutinefunction(fn):route.dependant.call=timed(fn,'handler:'+route.path)
app.add_middleware(ServerTiming)
params={'school':'九州工業大學 Kyushu Institute of Technology','home_school':'國立中央大學'}
started=datetime.datetime.now(datetime.timezone.utc).isoformat()
with TestClient(app) as client:
 def request(path):
  t=time.monotonic();r=client.get(path,params=params);return {'path':path,'status':r.status_code,'wall_ms':(time.monotonic()-t)*1000,'server_timing':r.headers.get('server-timing'),'document_title_present':'校規初次三類'in r.text,'response_length':len(r.content)}
 with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:results=list(pool.map(request,['/application-workflow','/destination-profile','/school-data-completeness']))
report={'started_at':started,'finished_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'candidate_sha':os.environ['NCU_DIAG_SHA'],'request_limit':3,'concurrent_group_count':1,'browser_reruns':0,'production_actions':False,'results':results,'spans':SPAN,'server_events':ROWS,'limitation':'Cold isolated ASGI three-request group only. No browser boot/public-translations/static-font load, no original-run server timestamps; cannot establish original failure root cause.'}
(out/'offline-phase-probe.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(results)
