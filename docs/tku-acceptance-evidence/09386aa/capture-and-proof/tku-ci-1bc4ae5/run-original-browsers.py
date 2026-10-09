import json, os, subprocess, sys, time
from pathlib import Path
root=Path('/workspace/abroad-tku-boundaries-fix');out=Path('/tmp/tku-acceptance-1bc4ae5-browsers');sha='1bc4ae5ee856462552645143d6e25c8927e7268e'
def state():
 return {'commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip(),'dirty':subprocess.check_output(['git','status','--porcelain'],cwd=root,text=True).strip()}
before=state();assert before=={'commit':sha,'dirty':''}
names=['test_guest_can_save_device_selections_and_plan_actions_require_login','test_authenticated_plan_notifications_and_progress_sync_across_devices','test_workspace_conflict_preserves_remote_addition_and_local_removal','test_workspace_conflict_retry_keeps_remote_fields_during_new_ui_change','test_workspace_load_advances_base_before_put_conflict','test_expired_session_and_logout_clear_private_browser_state','test_permissions_sensitive_consent_and_account_deletion_are_fail_closed']
command=[sys.executable,'-m','pytest',*[f'tests/e2e/test_web_next_phase.py::{n}' for n in names],'-q','-ra',f'--junitxml={out}/incremental.xml']
started=time.time()
with (out/'incremental.log').open('w') as f:
 result=subprocess.run(command,cwd=root,env={**os.environ,'PYTHONPATH':str(root/'src'),'PLAYWRIGHT_BROWSERS_PATH':'/tmp/tku-browsers','UV_CACHE_DIR':'/tmp/tku-uv-cache'},stdout=f,stderr=subprocess.STDOUT)
after=state();guard=before==after
report={'tested_commit':sha,'starting_state':before,'ending_state':after,'candidate_guard_passed':guard,'command':command,'actual_exit_code':result.returncode,'elapsed_seconds':round(time.time()-started,2),'production_access':False,'scope':'Seven previously unexecuted original browser cases, in a separate pytest invocation; original 409/conflict/privacy assertions unchanged.'}
(out/'incremental-run.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(json.dumps(report));raise SystemExit(result.returncode if guard else 2)
