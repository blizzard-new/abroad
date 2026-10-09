import json,subprocess,pytest
from pathlib import Path
from playwright.sync_api import expect
ROOT=Path('/workspace/abroad-tku');OUT=Path('/tmp/tku-acceptance-ce83a50/source-followup');OUT.mkdir(exist_ok=True)
SHA='ce83a502e33a42906fdf716bfaa606e777970d61'
def guard():return dict(commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),dirty=subprocess.check_output(['git','status','--porcelain'],cwd=ROOT,text=True).strip())
class Capture:
 @pytest.hookimpl(hookwrapper=True)
 def pytest_runtest_makereport(self,item,call):
  outcome=yield;report=outcome.get_result()
  if report.when=='call' and 'page' in item.funcargs:
   p=item.funcargs['page'];name=item.name;expect(p.locator('#boot-splash')).to_be_hidden();original=p.locator('.destination-original-summary');expect(original).to_be_visible();original.scroll_into_view_if_needed();p.screenshot(path=str(OUT/(name+'.png')),full_page=True)
   data={'tested_commit':SHA,'case':item.nodeid,'actual_status':report.outcome,'original_summary':original.inner_text(),'visible_current_limits':p.locator('.destination-facts').inner_text(),'source_links':p.locator('.destination-source-card a').evaluate_all('links => links.map(a=>a.href)'),'scope':'additional fixed-SHA source visual evidence; not added to the main suite count'};(OUT/(name+'.json')).write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
before=guard();assert before==dict(commit=SHA,dirty='')
code=pytest.main(['tests/e2e/test_tku_source_rendering.py','-vv','--tb=short',f'--junitxml={OUT}/suite.xml'],plugins=[Capture()]);after=guard();assert after==before
(OUT/'result.json').write_text(json.dumps(dict(tested_commit=SHA,before=before,after=after,actual_exit_code=int(code),auxiliary_only=True,candidate_guard_passed=True),indent=2)+'\n');raise SystemExit(int(code))
