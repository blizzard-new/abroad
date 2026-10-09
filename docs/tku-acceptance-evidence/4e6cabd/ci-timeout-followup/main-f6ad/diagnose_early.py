from pathlib import Path
from urllib.parse import urlsplit
import json,time,subprocess
import pytest
root=Path('/workspace/abroad-tku-main-baseline');out=Path('/tmp/tku-ci-timeout-main-f6ad')
head=lambda:subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip()
dirty=lambda:subprocess.check_output(['git','status','--porcelain'],cwd=root,text=True).splitlines()
before=dict(head=head(),dirty=dirty());assert before['head']=='f6ad1b8cedc4dadb4d00c29eb3456a7a87856d59' and not before['dirty']
def record(value):
 with (out/'early-timings.jsonl').open('a') as f:f.write(json.dumps(value,ensure_ascii=False)+'\n')
import exchange_info.api as api
assert Path(api.__file__).resolve().is_relative_to(root)
original=api.create_app
def traced_app(*args,**kwargs):
 app=original(*args,**kwargs)
 @app.middleware('http')
 async def trace(request,call_next):
  started=time.monotonic()
  try:
   response=await call_next(request)
   record(dict(type='server_http',path=request.url.path,status=response.status_code,seconds=time.monotonic()-started))
   return response
  except Exception as exc:
   record(dict(type='server_http',path=request.url.path,error=type(exc).__name__,seconds=time.monotonic()-started));raise
 return app
api.create_app=traced_app
class Trace:
 @pytest.hookimpl(hookwrapper=True)
 def pytest_fixture_setup(self,fixturedef,request):
  started=time.monotonic();outcome=yield
  record(dict(type='fixture',name=fixturedef.argname,case=request.node.nodeid,seconds=time.monotonic()-started))
  if fixturedef.argname=='page' and outcome.excinfo is None:
   page=outcome.get_result();starts={}
   page.on('request',lambda r:starts.__setitem__(id(r),time.monotonic()))
   def done(r,failed=False):
    url=urlsplit(r.url)
    record(dict(type='browser_http',case=request.node.nodeid,host=url.hostname,path=url.path,failed=failed,seconds=time.monotonic()-starts.pop(id(r),time.monotonic())))
   page.on('requestfinished',done);page.on('requestfailed',lambda r:done(r,True))
 def pytest_runtest_logreport(self,report):
  record(dict(type='test_phase',case=report.nodeid,phase=report.when,outcome=report.outcome,seconds=report.duration))
cases=['tests/e2e/test_analytics_tracking.py','tests/e2e/test_application_periods.py','tests/e2e/test_discovery_workspace.py']
start=time.monotonic();code=pytest.main([*cases,'-vv','--durations=20','--tb=short',f'--junitxml={out}/early-suite.xml'],plugins=[Trace()])
after=dict(head=head(),dirty=dirty());assert before==after
(out/'early-run.json').write_text(json.dumps(dict(tested_commit=before['head'],before=before,after=after,invariant_passed=True,cases=cases,exit_code=code,duration_seconds=time.monotonic()-start,telemetry_only=True),indent=2)+'\n')
raise SystemExit(code)
