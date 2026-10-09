"""One diagnostic run; instrument timing only, preserve original test and data."""
import asyncio, cProfile, contextvars, datetime, functools, json, os, sys, threading, time
from pathlib import Path
import pytest

OUT = Path(os.environ['NCU_KYUTECH_TIMING_OUT'])
OUT.mkdir(parents=True, exist_ok=True)
RID = contextvars.ContextVar('diagnostic_request_id', default=None)
ROWS = []; LOCK = threading.Lock(); PROFILES = []; START = time.monotonic()
def record(kind, **fields):
    with LOCK:
        ROWS.append(dict(kind=kind, ms=round((time.monotonic()-START)*1000,3), **fields))

class ServerTiming:
    def __init__(self, app): self.app=app
    async def __call__(self, scope, receive, send):
        if scope['type']!='http': return await self.app(scope,receive,send)
        rid=f'{time.monotonic_ns()}'; token=RID.set(rid); started=time.monotonic()
        record('asgi_received',rid=rid,path=scope['path'],query=scope.get('query_string',b'').decode())
        async def wrapped(message):
            if message['type']=='http.response.start':
                ms=(time.monotonic()-started)*1000
                message=dict(message);message['headers']=list(message.get('headers',[]))+[(b'server-timing',f'ncu_diag;dur={ms:.3f}'.encode())]
                record('response_start',rid=rid,path=scope['path'],status=message['status'],duration_ms=round(ms,3))
            if message['type']=='http.response.body' and not message.get('more_body',False):record('response_body_end',rid=rid,path=scope['path'])
            await send(message)
        try: await self.app(scope,receive,wrapped)
        finally: RID.reset(token)

@pytest.fixture(scope='module',autouse=True)
def instrument_server():
    targets=[(name,mod) for name,mod in list(sys.modules.items()) if getattr(mod,'__file__',None) and Path(mod.__file__).name=='conftest.py' and hasattr(mod,'LiveServer') and hasattr(mod,'create_app')]
    record('instrumentation_targets',names=[name for name,mod in targets])
    assert targets, 'No actual pytest live-server conftest module loaded'
    originals=[(mod,mod.create_app) for name,mod in targets]
    original=originals[0][1]
    def build(*a,**kw):
        app=original(*a,**kw)
        for route in app.routes:
            if not hasattr(route,'dependant'):continue
            handler=route.dependant.call
            if asyncio.iscoroutinefunction(handler):continue
            path=route.path
            def wrap(call,path):
                @functools.wraps(call)
                def measured(*a,**kw):
                    rid=RID.get();started=time.monotonic();cpu=time.thread_time()
                    record('handler_enter',rid=rid,path=path,thread=threading.get_ident())
                    prof=cProfile.Profile() if path in ['/application-workflow','/destination-profile','/school-data-completeness','/student-experiences','/application-period-options'] else None
                    if prof:prof.enable()
                    try:return call(*a,**kw)
                    finally:
                        if prof:prof.disable();PROFILES.append((rid,path,prof))
                        record('handler_exit',rid=rid,path=path,wall_ms=round((time.monotonic()-started)*1000,3),thread_cpu_ms=round((time.thread_time()-cpu)*1000,3))
                return measured
            route.dependant.call=wrap(handler,path)
        app.add_middleware(ServerTiming)
        async def heartbeat():
            last=time.monotonic()
            while True:
                await asyncio.sleep(.05);now=time.monotonic();delay=(now-last-.05)*1000
                if delay>20:record('event_loop_delay',delay_ms=round(delay,3))
                last=now
        @app.on_event('startup')
        async def start():app.state.ncu_diag_heartbeat=asyncio.create_task(heartbeat())
        @app.on_event('shutdown')
        async def stop():app.state.ncu_diag_heartbeat.cancel()
        return app
    for mod,old in originals:mod.create_app=build
    record('diagnostic_start',utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),load_average=os.getloadavg())
    yield
    for mod,old in originals:mod.create_app=old
    for rid,path,prof in PROFILES:
        prof.dump_stats(str(OUT/(rid+'-'+path.strip('/').replace('/','_')+'.pstats')))
    (OUT/'server-events.json').write_text(json.dumps(ROWS,ensure_ascii=False,indent=2)+'\n')

@pytest.fixture(autouse=True)
def browser_server_timing(request):
    if 'page' not in request.fixturenames:yield;return
    page=request.getfixturevalue('page');responses=[]
    def response(r):
        if r.request.resource_type=='fetch':responses.append({'url':r.url,'status':r.status,'server_timing':r.headers.get('server-timing')})
    page.on('response',response)
    yield
    (OUT/'browser-server-timing.json').write_text(json.dumps(responses,ensure_ascii=False,indent=2)+'\n')
