"""Bounded browser events for the actual fixed-SHA test, without timeout changes."""
import hashlib,json,os,time
from pathlib import Path
import pytest

INIT=r"""(()=>{
window.__ncuVerifyStates=[];let last='',queued=false;
const state=()=>{queued=false;const s={at:performance.now(),hash:location.hash,page:document.body?.dataset.activeUniversityPage,searchVisible:!!document.querySelector('#partner-search')?.getClientRects().length,splashVisible:!!document.querySelector('#boot-splash')?.getClientRects().length,auditOpen:document.querySelector('#ncu-source-audit')?.open,auditLoaded:document.querySelector('#ncu-source-audit')?.dataset.loaded,auditPrefix:document.querySelector('#ncu-source-audit-body')?.textContent.slice(0,70)};const key=JSON.stringify({...s,at:0});if(key!==last&&window.__ncuVerifyStates.length<120){last=key;window.__ncuVerifyStates.push(s)}};
const schedule=()=>{if(!queued){queued=true;setTimeout(state,250)}};
document.addEventListener('DOMContentLoaded',()=>{state();new MutationObserver(schedule).observe(document.body,{subtree:true,attributes:true,childList:true,attributeFilter:['hidden','class','data-loaded','data-active-university-page']})});window.addEventListener('load',schedule);window.addEventListener('hashchange',schedule);
})();"""
@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item,call):
 outcome=yield;report=outcome.get_result()
 if report.failed:item._ncu_actual_failure=dict(phase=report.when,message=str(report.longrepr)[:1800])

@pytest.fixture(autouse=True)
def actual_browser_events(request):
 if 'page'not in request.fixturenames:yield;return
 page=request.getfixturevalue('page');started=time.monotonic();events=[]
 def record(kind,**data):
  if len(events)<4000:events.append(dict(kind=kind,ms=round((time.monotonic()-started)*1000,2),**data))
 page.on('request',lambda r:record('request',url=r.url,resource=r.resource_type))
 page.on('response',lambda r:record('response_headers',url=r.url,status=r.status))
 page.on('requestfinished',lambda r:record('requestfinished',url=r.url,timing=r.timing))
 page.on('requestfailed',lambda r:record('requestfailed',url=r.url,error=r.failure))
 page.on('pageerror',lambda e:record('pageerror',error=str(e)))
 page.add_init_script(INIT)
 yield
 out=Path(os.environ['NCU_DIAG_OUT']);out.mkdir(exist_ok=True,parents=True);ident=hashlib.sha256(request.node.nodeid.encode()).hexdigest()[:14]
 failure=getattr(request.node,'_ncu_actual_failure',None);states=[]
 try:states=page.evaluate('window.__ncuVerifyStates || []')
 except Exception as e:record('diagnostic_state_read_failed',error=str(e)[:180])
 if failure:
  try:page.screenshot(path=str(out/(ident+'-failure.png')),timeout=3000)
  except Exception as e:record('diagnostic_screenshot_failed',error=str(e)[:180])
 (out/(ident+'.json')).write_text(json.dumps(dict(nodeid=request.node.nodeid,actual_result='failed'if failure else'passed',failure=failure,events=events,states=states,original_timeouts_and_assertions_unchanged=True),ensure_ascii=False,indent=2)+'\n')
