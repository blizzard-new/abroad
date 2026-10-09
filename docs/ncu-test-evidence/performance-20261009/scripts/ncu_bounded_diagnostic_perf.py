"""External read-only timing instrumentation; original cases/timeout remain unchanged."""
import asyncio,datetime as dt,functools,hashlib,json,os,threading,time
from pathlib import Path
from urllib.parse import urlsplit
import pytest
from exchange_info import api,storage,ncu_student_view,public_translation
OUT=Path('/tmp/ncu-bounded-performance-b29e28f');OUT.mkdir(exist_ok=True)
LOCK=threading.Lock();EVENTS=[];BASE=time.monotonic();CALLS={}
def record(kind,**data):
 with LOCK:
  if len(EVENTS)<12000:EVENTS.append(dict(kind=kind,ms=round((time.monotonic()-BASE)*1000,2),**data))
def timed(owner,name):
 real=getattr(owner,name)
 @functools.wraps(real)
 def call(*a,**kw):
  start=time.monotonic();cpu=time.thread_time()
  try:return real(*a,**kw)
  finally:
   wall=time.monotonic()-start;used=time.thread_time()-cpu
   with LOCK:
    x=CALLS.setdefault(owner.__name__+'.'+name,dict(calls=0,wall_seconds=0,cpu_seconds=0,max_wall_seconds=0));x['calls']+=1;x['wall_seconds']+=wall;x['cpu_seconds']+=used;x['max_wall_seconds']=max(x['max_wall_seconds'],wall)
   if wall>=.05:record('function',function=owner.__name__+'.'+name,wall_seconds=wall,cpu_seconds=used,argument=str(a[0])[:180] if a and isinstance(a[0],(str,Path))else None)
 setattr(owner,name,call)
for owner,names in [(storage,['read_jsonl','load_bundled_application_workflows','load_application_workflows']), (api,['load_destination_profiles','load_bundled_application_workflows','load_application_workflows']), (ncu_student_view,['_payload','ncu_field_audit','build_ncu_student_dashboard']), (public_translation,['_bundled_machine_translations','_reference_translations'])]:
 for name in names:timed(owner,name)
real_audit_read=Path.read_bytes
def audit_read(path,*a,**kw):
 if path.name in {'field-audit.json','source-evidence.json.gz'}:record('audit_file_read',path=str(path))
 return real_audit_read(path,*a,**kw)
Path.read_bytes=audit_read
class ASGITiming:
 def __init__(self,app):self.app=app
 async def __call__(self,scope,receive,send):
  if scope['type']!='http':return await self.app(scope,receive,send)
  path=scope['path'];start=time.monotonic();cpu=time.process_time();status=None;size=0
  async def measured(message):
   nonlocal status,size
   if message['type']=='http.response.start':status=message['status'];record('http_headers',path=path,status=status,seconds=time.monotonic()-start)
   if message['type']=='http.response.body':size+=len(message.get('body',b''))
   await send(message)
  record('http_start',path=path)
  try:return await self.app(scope,receive,measured)
  finally:record('http_end',path=path,status=status,seconds=time.monotonic()-start,cpu_process_seconds=time.process_time()-cpu,bytes=size)
real_create=api.create_app
@functools.wraps(real_create)
def create(*a,**kw):
 app=real_create(*a,**kw);app.add_middleware(ASGITiming);return app
api.create_app=create
import uvicorn
real_serve=uvicorn.Server.serve
async def serve(self,*a,**kw):
 async def heartbeat():
  before=time.monotonic()
  while True:
   await asyncio.sleep(.05);now=time.monotonic();lag=max(0,now-before-.05);before=now
   if lag>=.10:record('eventloop_lag',seconds=lag)
 task=asyncio.create_task(heartbeat())
 try:return await real_serve(self,*a,**kw)
 finally:task.cancel()
uvicorn.Server.serve=serve
INIT=r"""
window.__ncuDiag=[];
const emit=(kind,data={})=>{if(window.__ncuDiag.length<2500)window.__ncuDiag.push({kind,at:performance.now(),...data})};
const snap=()=>({hash:location.hash,page:document.body?.dataset.activeUniversityPage,searchVisible:!!document.querySelector('#partner-search')?.getClientRects().length,splashVisible:!!document.querySelector('#boot-splash')?.getClientRects().length,auditOpen:document.querySelector('#ncu-source-audit')?.open,auditLoaded:document.querySelector('#ncu-source-audit')?.dataset.loaded,auditPrefix:document.querySelector('#ncu-source-audit-body')?.textContent.slice(0,70)});
let last='';setInterval(()=>{const x=snap(),v=JSON.stringify(x);if(v!==last){last=v;emit('state',x)}},250);
document.addEventListener('click',e=>{const t=e.target.closest('button,summary,a');if(t)emit('click',{id:t.id,text:t.textContent.slice(0,50),...snap()})},true);
document.addEventListener('toggle',e=>{if(e.target.id==='ncu-source-audit')emit('audit_toggle',snap())},true);
document.addEventListener('DOMContentLoaded',()=>emit('dom_content',snap()));window.addEventListener('load',()=>emit('load',snap()));window.addEventListener('hashchange',()=>emit('hashchange',snap()));
try{new PerformanceObserver(list=>{for(const e of list.getEntries())emit('longtask',{duration:e.duration})}).observe({type:'longtask',buffered:true})}catch{}
"""
@pytest.fixture(autouse=True)
def bounded_page_diagnostic(request):
 if 'page' not in request.fixturenames:yield;return
 page=request.getfixturevalue('page');start=time.monotonic();events=[]
 def event(kind,**data):
  if len(events)<5000:events.append(dict(kind=kind,ms=round((time.monotonic()-start)*1000,2),**data))
 page.on('request',lambda r:event('request',url=r.url,resource=r.resource_type))
 page.on('response',lambda r:event('response_headers',url=r.url,status=r.status))
 page.on('requestfinished',lambda r:event('requestfinished',url=r.url,timing=r.timing))
 page.on('requestfailed',lambda r:event('requestfailed',url=r.url,error=r.failure))
 page.on('pageerror',lambda e:event('pageerror',error=str(e)))
 page.add_init_script(INIT)
 page.context.tracing.start(screenshots=True,snapshots=True,sources=False)
 yield
 ident=hashlib.sha256(request.node.nodeid.encode()).hexdigest()[:14];ui=[]
 try:ui=page.evaluate('window.__ncuDiag || []')
 except Exception as e:event('diagnostic_read_failed',reason=str(e)[:180])
 page.context.tracing.stop(path=str(OUT/(ident+'-trace.zip')))
 data=dict(nodeid=request.node.nodeid,events=events,ui_events=ui,system_load=os.getloadavg(),server_events=list(EVENTS),function_calls=dict(CALLS),instrumentation_only=True)
 (OUT/(ident+'-events.json')).write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
@pytest.hookimpl(trylast=True)
def pytest_sessionfinish(session,exitstatus):
 (OUT/'server-summary.json').write_text(json.dumps(dict(events=EVENTS,function_calls=CALLS,system_load=os.getloadavg(),exit_code=exitstatus),ensure_ascii=False,indent=2)+'\n')
