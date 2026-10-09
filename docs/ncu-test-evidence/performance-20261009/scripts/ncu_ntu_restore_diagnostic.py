"""External read-only timing instrumentation; original cases/timeout remain unchanged."""
import asyncio,datetime as dt,functools,hashlib,json,os,threading,time
from pathlib import Path
from urllib.parse import urlsplit
import pytest
from exchange_info import api,storage,ncu_student_view,public_translation
OUT=Path('/tmp/ncu-bounded-ntu-restore-3b14037');OUT.mkdir(exist_ok=True)
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

INIT=r"""(()=>{
const emit=(kind,data={})=>console.debug('__ncu_restore_diag__'+JSON.stringify({kind,t:performance.now(),...data}));
const context=()=>({home:typeof activeHomeSchool==='function'?activeHomeSchool():null,dashboardReady:typeof state!=='undefined'&&!!state.dashboard,profilePresent:typeof state!=='undefined'&&!!state.eligibilityProfile,gpa:document.querySelector('#advisor-academic-gpa')?.value,gpaDisabled:document.querySelector('#advisor-academic-gpa')?.disabled,splashVisible:!!document.querySelector('#boot-splash')?.getClientRects().length});
document.addEventListener('DOMContentLoaded',()=>{emit('dom_content',context());for(const name of ['renderDashboard','renderAdvisorForm','renderAcademicFields','applyAccountWorkspace','renderAccountWorkspaceState','loadDashboard']){const original=window[name];if(typeof original!=='function')continue;window[name]=function(...args){const start=performance.now();emit('function_start',{name,...context()});try{const result=original.apply(this,args);if(result&&typeof result.then==='function')result.then(()=>emit('async_complete',{name,elapsed:performance.now()-start,...context()}),()=>emit('async_failed',{name,elapsed:performance.now()-start,...context()}));return result;}finally{emit('function_return',{name,elapsed:performance.now()-start,...context()})}}}const originalDone=window.UniWaySplash?.done;if(originalDone){window.UniWaySplash.done=function(...a){emit('boot_done',context());return originalDone.apply(this,a)}}});
window.addEventListener('load',()=>emit('load',context()));try{new PerformanceObserver(list=>{for(const e of list.getEntries())emit('longtask',{start:e.startTime,duration:e.duration})}).observe({type:'longtask',buffered:true})}catch{}
})();"""
@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item,call):
 outcome=yield;report=outcome.get_result()
 if report.failed:item._ncu_failure=str(report.longrepr)
@pytest.fixture(autouse=True)
def observe_restore(request):
 if 'page'not in request.fixturenames:yield;return
 page=request.getfixturevalue('page');start=time.monotonic();events=[];browser=[]
 def event(kind,**data):events.append(dict(kind=kind,ms=round((time.monotonic()-start)*1000,2),**data))
 page.on('request',lambda r:event('request',url=r.url,resource=r.resource_type));page.on('response',lambda r:event('response_headers',url=r.url,status=r.status));page.on('requestfinished',lambda r:event('requestfinished',url=r.url,timing=r.timing));page.on('requestfailed',lambda r:event('requestfailed',url=r.url,error=r.failure));page.on('pageerror',lambda e:event('pageerror',error=str(e)))
 def console(message):
  if message.text.startswith('__ncu_restore_diag__'):browser.append(dict(json.loads(message.text[len('__ncu_restore_diag__'):]),test_ms=round((time.monotonic()-start)*1000,2)))
 page.on('console',console);page.add_init_script(INIT)
 yield
 failure=getattr(request.node,'_ncu_failure',None)
 try:page.screenshot(path=str(OUT/'final-actual-state.png'),timeout=3000)
 except Exception as e:event('diagnostic_screenshot_failure',error=str(e)[:180])
 (OUT/'restore-events.json').write_text(json.dumps(dict(nodeid=request.node.nodeid,result='failed'if failure else'passed',failure=failure,browser_events=browser,events=events,server_events=list(EVENTS),function_calls=dict(CALLS),original_timeouts_unchanged=True),ensure_ascii=False,indent=2)+'\n')
@pytest.hookimpl(trylast=True)
def pytest_sessionfinish(session,exitstatus):
 (OUT/'server-summary.json').write_text(json.dumps(dict(events=EVENTS,function_calls=CALLS,system_load=os.getloadavg(),exit_code=exitstatus),ensure_ascii=False,indent=2)+'\n')
