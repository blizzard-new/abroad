import sys,os,json,time,subprocess,datetime as dt
from pathlib import Path
from urllib.parse import urlparse
from playwright.sync_api import sync_playwright,expect
sys.path.insert(0,str(Path.cwd()))
from tests.e2e import conftest as ct
from tests.e2e.test_ncu_niigata import test_ncu_niigata_iec_graduate_finance_and_source_scope as original_test
root=Path.cwd();sha=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip();assert sha==sys.argv[2];assert not subprocess.check_output(['git','status','--porcelain'],text=True).strip()
run=sys.argv[1];out=Path('/tmp')/f'ncu-candidate-{sha}'/'performance-boot-v4';out.mkdir(parents=True,exist_ok=True);server_metrics=[];original_create=ct.create_app;catalog_builds=[];build_lock=__import__('threading').Lock()
from exchange_info import storage
original_cached=storage._cached_workflows
def counted_catalog(key,build):
 def counted():
  start=time.perf_counter()
  try:return build()
  finally:
   with build_lock:catalog_builds.append({'kind':key[0],'key':repr(key),'elapsed_ms':(time.perf_counter()-start)*1000})
 return original_cached(key,counted)
storage._cached_workflows=counted_catalog

def instrumented_create(*args,**kwargs):
 app=original_create(*args,**kwargs)
 @app.middleware('http')
 async def duration(request,call_next):
  start=time.perf_counter();response=await call_next(request)
  server_metrics.append({'path':request.url.path,'query':request.url.query,'status':response.status_code,'server_ms':(time.perf_counter()-start)*1000})
  return response
 return app
ct.create_app=instrumented_create
class Factory:
 def mktemp(self,name):
  p=out/f'{run}-{name}';p.mkdir(exist_ok=False);return p
server_gen=ct.live_server.__wrapped__(Factory());server=next(server_gen);report={'tested_sha':sha,'run':run,'started_at':dt.datetime.now(dt.timezone.utc).isoformat(),'cold_python_process':True,'worktree_clean_at_start':True,'original_default_5s_test_unchanged':True,'instrumentation':'v4: boot-ready timer handles splash removal (100ms precision), no additional wait after failure; ASGI timings, per-key catalog builds, browser ResourceTiming buffer5000, LongTask/render/DOM observers; native network and assertions unchanged'}
script='''(() => {performance.setResourceTimingBufferSize(5000); window.__ncuTiming=[]; window.__ncuLongTasks=[]; try{new PerformanceObserver(list=>window.__ncuLongTasks.push(...list.getEntries().map(e=>({startTime:e.startTime,duration:e.duration})))).observe({type:"longtask",buffered:true});}catch(e){} const orig=window.fetch; window.fetch=function(...args){const url=String(args[0]);const start=performance.now();window.__ncuTiming.push({event:"fetch_start",url,t:start});return orig.apply(this,args).then(r=>{window.__ncuTiming.push({event:"fetch_headers",url,t:performance.now(),status:r.status});return r});};const observe=()=>{for(const name of ["renderApplicationWorkflow","renderApplicationCalendar","scheduleCalendarConflictAnalysis"]){const fn=window[name];if(typeof fn==="function"){window[name]=function(...args){const start=performance.now();try{return fn.apply(this,args);}finally{window.__ncuTiming.push({event:"render",method:name,t:start,end:performance.now()});}};window.__ncuTiming.push({event:"instrumented_render",method:name,t:performance.now()});}}const o=new MutationObserver(ms=>{for(const m of ms){if(m.type==="attributes"&&m.target.id==="workflow-content")window.__ncuTiming.push({event:"workflow_busy",value:m.target.getAttribute("aria-busy"),t:performance.now()});}});o.observe(document.documentElement,{subtree:true,attributes:true,attributeFilter:["aria-busy"]});};document.addEventListener("DOMContentLoaded",observe);})();'''
try:
 with sync_playwright()as p:
  b=p.chromium.launch(headless=True);ctx=b.new_context(viewport={'width':390,'height':956});page=ctx.new_page();page.add_init_script(script+"window.__ncuLifecycle=[];let splashSeen=false,bootSeen=false;const lifecycle=(kind)=>window.__ncuLifecycle.push({kind,t:performance.now(),hash:location.hash});document.addEventListener('DOMContentLoaded',()=>lifecycle('dom_content'));window.addEventListener('load',()=>lifecycle('load'));const timer=setInterval(()=>{const node=document.querySelector('#boot-splash');if(node&&node.getClientRects().length)splashSeen=true;if(splashSeen&&(!node||!node.getClientRects().length)&&!bootSeen){bootSeen=true;lifecycle('boot_ready');clearInterval(timer)}},100);");errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
  start=time.perf_counter()
  try:
   original_test(page,server,390);report['original_test_result']='passed'
  except Exception as e:
   report['original_test_result']='failed';report['failure_type']=type(e).__name__;report['failure']=str(e)[:2000]
   report['no_additional_wait_after_failure']=True
  report['test_elapsed_s']=time.perf_counter()-start;report['page_errors']=errors
  report['browser_lifecycle']=page.evaluate('window.__ncuLifecycle');report['browser_navigation']=page.evaluate('performance.getEntriesByType("navigation").map(e=>({domContentLoadedEventEnd:e.domContentLoadedEventEnd,loadEventEnd:e.loadEventEnd,responseEnd:e.responseEnd}))');report['browser_trace']=page.evaluate('window.__ncuTiming');report['browser_long_tasks']=page.evaluate('window.__ncuLongTasks')
  report['browser_resources']=page.evaluate('performance.getEntriesByType("resource").filter(x=>new URL(x.name).origin===location.origin && !x.name.includes("/static/")).map(x=>({path:new URL(x.name).pathname,startTime:x.startTime,duration:x.duration,requestStart:x.requestStart,responseStart:x.responseStart,responseEnd:x.responseEnd,transferSize:x.transferSize,encodedBodySize:x.encodedBodySize,decodedBodySize:x.decodedBodySize}))')
  b.close()
finally:
 server_gen.close();report['catalog_builds']=catalog_builds;report['server_requests']=server_metrics;report['finished_at']=dt.datetime.now(dt.timezone.utc).isoformat();report['end_sha']=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip();report['worktree_clean_at_end']=not subprocess.check_output(['git','status','--porcelain'],text=True).strip();(out/f'cold-{run}.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(json.dumps({'run':run,'result':report.get('original_test_result'),'elapsed':report.get('test_elapsed_s'),'workflow_requests':[x for x in server_metrics if x['path']=='/application-workflow']},ensure_ascii=False))
