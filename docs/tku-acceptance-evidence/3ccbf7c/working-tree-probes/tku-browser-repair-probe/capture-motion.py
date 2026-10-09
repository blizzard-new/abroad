import pytest,json
from pathlib import Path
class Capture:
 @pytest.hookimpl(hookwrapper=True)
 def pytest_runtest_makereport(self,item,call):
  outcome=yield;report=outcome.get_result()
  if report.failed and 'page' in item.funcargs:
   page=item.funcargs['page'];v=page.evaluate('''() => ({url:location.href,body:document.body.className,scrollY,motions:__motionLog.map(x=>({id:x.id,kind:x.animation.id})),roots:[...document.querySelectorAll('#community-hub,#dashboard-view > section[data-university-page]')].map(x=>({id:x.id,hidden:x.hidden,rect:x.getBoundingClientRect().toJSON()}))})''');Path('/tmp/tku-browser-repair-probe/motion-dom.json').write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n');page.screenshot(path='/tmp/tku-browser-repair-probe/motion-failed.png')
raise SystemExit(pytest.main(['tests/e2e/test_system_motion.py::test_all_routes_share_motion_and_back_retains_working_history','-vv','--tb=short'],plugins=[Capture()]))
