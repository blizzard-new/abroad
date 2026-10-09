import sys,os,json,time,subprocess,datetime as dt
from pathlib import Path
from urllib.parse import urlparse
from playwright.sync_api import sync_playwright,expect
from tests.e2e import conftest as ct
from tests.e2e.test_ncu_niigata import test_ncu_niigata_iec_graduate_finance_and_source_scope as original_test
root=Path.cwd();sha=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip();assert sha=='ded2ed1a79a5f3cb009655790eb560816a7af61a';assert not subprocess.check_output(['git','status','--porcelain'],text=True).strip()
run=sys.argv[1];out=Path('/tmp/ncu-niigata-performance-ded2ed1');out.mkdir(exist_ok=True);server_metrics=[];original_create=ct.create_app

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
server_gen=ct.live_server.__wrapped__(Factory());server=next(server_gen);report={'tested_sha':sha,'run':run,'started_at':dt.datetime.now(dt.timezone.utc).isoformat(),'cold_python_process':True,'worktree_clean_at_start':True,'original_default_5s_test_unchanged':True,'instrumentation':'in-memory ASGI server timing and browser performance/DOM observer only'}
script='''(() => {window.__ncuTiming=[]; const orig=window.fetch; window.fetch=function(...args){const url=String(args[0]);const start=performance.now();window.__ncuTiming.push({event:"fetch_start",url,t:start});return orig.apply(this,args).then(r=>{window.__ncuTiming.push({event:"fetch_headers",url,t:performance.now(),status:r.status});return r});};const observe=()=>{const o=new MutationObserver(ms=>{for(const m of ms){if(m.type==="attributes"&&m.target.id==="workflow-content")window.__ncuTiming.push({event:"workflow_busy",value:m.target.getAttribute("aria-busy"),t:performance.now()});}});o.observe(document.documentElement,{subtree:true,attributes:true,attributeFilter:["aria-busy"]});};document.addEventListener("DOMContentLoaded",observe);})();'''
try:
 with sync_playwright()as p:
  b=p.chromium.launch(headless=True);ctx=b.new_context(viewport={'width':390,'height':956});page=ctx.new_page();page.add_init_script(script);errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
  start=time.perf_counter()
  try:
   original_test(page,server,390);report['original_test_result']='passed'
  except Exception as e:
   report['original_test_result']='failed';report['failure_type']=type(e).__name__;report['failure']=str(e)[:2000]
   # This observation continues measuring readiness, not rerunning/waiving the failed test.
   try:expect(page.locator('#detail-application')).to_contain_text('IEC No.1／2',timeout=60000);report['eventual_workflow_ready']=True
   except Exception as e2:report['eventual_workflow_ready']=False;report['eventual_failure']=str(e2)[:700]
  report['test_elapsed_s']=time.perf_counter()-start;report['page_errors']=errors
  report['browser_trace']=page.evaluate('window.__ncuTiming')
  report['browser_resources']=page.evaluate('performance.getEntriesByType("resource").filter(x=>new URL(x.name).origin===location.origin && !x.name.includes("/static/")).map(x=>({path:new URL(x.name).pathname,startTime:x.startTime,duration:x.duration,requestStart:x.requestStart,responseStart:x.responseStart,responseEnd:x.responseEnd,transferSize:x.transferSize,encodedBodySize:x.encodedBodySize,decodedBodySize:x.decodedBodySize}))')
  b.close()
finally:
 server_gen.close();report['server_requests']=server_metrics;report['finished_at']=dt.datetime.now(dt.timezone.utc).isoformat();report['end_sha']=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip();report['worktree_clean_at_end']=not subprocess.check_output(['git','status','--porcelain'],text=True).strip();(out/f'cold-{run}.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(json.dumps({'run':run,'result':report.get('original_test_result'),'elapsed':report.get('test_elapsed_s'),'workflow_requests':[x for x in server_metrics if x['path']=='/application-workflow']},ensure_ascii=False))
