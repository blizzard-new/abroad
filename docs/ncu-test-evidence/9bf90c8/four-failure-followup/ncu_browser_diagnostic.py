import datetime as dt,json,time
from pathlib import Path
import pytest
out=Path('/tmp/ncu-9bf90c8-browser-followup');out.mkdir(exist_ok=True)
@pytest.fixture(autouse=True)
def diagnostic(request):
    if 'page' not in request.fixturenames:
        yield;return
    page=request.getfixturevalue('page');started=time.monotonic();events=[]
    def event(kind,**data):events.append(dict(kind=kind,ms=round((time.monotonic()-started)*1000,1),**data))
    page.on('request',lambda r:event('request',url=r.url,resource=r.resource_type))
    page.on('response',lambda r:event('response',url=r.url,status=r.status))
    page.on('requestfailed',lambda r:event('requestfailed',url=r.url,error=r.failure))
    page.on('pageerror',lambda e:event('pageerror',error=str(e)))
    page.on('console',lambda m:event('console',text=m.text) if m.text.startswith('NCU_DIAG') else None)
    page.add_init_script("""
    document.addEventListener('toggle', event => {
      if (event.target.id === 'ncu-source-audit') console.log('NCU_DIAG audit_toggle ' + JSON.stringify({open:event.target.open,loaded:event.target.dataset.loaded,at:performance.now()}));
    },true);
    document.addEventListener('DOMContentLoaded',()=>console.log('NCU_DIAG dom_content '+performance.now()));
    window.addEventListener('load',()=>console.log('NCU_DIAG load '+performance.now()));
    """)
    yield
    filename=str(request.node.nodeid).replace('/','_').replace(':','_')
    filename=filename[:150]
    data=dict(nodeid=request.node.nodeid,started_at=dt.datetime.now(dt.timezone.utc).isoformat(),url=page.url,events=events)
    (out/(filename+'.json')).write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
