"""Additional visual guards on the unchanged b455a18 candidate, separate from suite."""
import json
import os
from pathlib import Path
import subprocess
import sys
import time

ROOT=Path('/workspace/abroad-tku')
OUT=Path('/tmp/tku-acceptance-ce83a50')
os.chdir(ROOT)
sys.path.insert(0,str(ROOT))
os.environ['TKU_ACCEPTANCE_OUTPUT']=str(OUT/'browser-followup')
from playwright.sync_api import expect
import pytest


def state():
    return dict(commit=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),
        dirty=subprocess.check_output(['git','status','--porcelain'],text=True).strip())


class VisualPlugin:
    wrapped=False
    def pytest_runtest_setup(self,item):
        if self.wrapped or 'test_tku_jlpt_comparison_persistence_and_closed_cycle' not in item.name:
            return
        original=item.module.record
        def record(page,name,width,errors,**facts):
            expect(page.locator('#boot-splash')).to_be_hidden(timeout=30000)
            expect(page.locator('#advisor-jlpt-level')).to_be_visible()
            expect(page.locator('#advisor-jlpt-level')).to_have_value('N1')
            expect(page.locator('#tku-eligibility-result')).to_have_attribute('data-language-status','pass')
            expect(page.locator('#tku-eligibility-result')).to_have_attribute('data-application-status','closed')
            page.locator('#advisor-jlpt-level').scroll_into_view_if_needed()
            original(page,name,width,errors,**facts,extra_visual_guard=True,
                boot_overlay_hidden=True,reloaded_jlpt_visibly_selected=True,
                interpretation='Additional focused visual evidence; does not replace guarded full-suite records or waive failures.')
        item.module.record=record
        self.wrapped=True


before=state();started=time.time()
assert before==dict(commit='ce83a502e33a42906fdf716bfaa606e777970d61',dirty='')
code=pytest.main(['tests/e2e/test_tku_acceptance.py::test_tku_jlpt_comparison_persistence_and_closed_cycle',
    '-q',f'--junitxml={OUT}/visual-followup.xml'],plugins=[VisualPlugin()])
after=state()
(OUT/'visual-followup-run.json').write_text(json.dumps(dict(tested_commit=before['commit'],
    before=before,after=after,started_at=started,ended_at=time.time(),actual_exit_code=int(code),
    synthetic_only=True,auxiliary_only=True,full_suite_records_unchanged=True,
    candidate_guard_passed=before==after and not after['dirty']),indent=2)+'\n')
raise SystemExit(int(code) if before==after else 2)
