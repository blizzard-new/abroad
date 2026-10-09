from pathlib import Path
import json,pytest,subprocess
ROOT=Path('/workspace/abroad-tku');OUT=Path('/tmp/tku-restore-probe-3ccbf7c');OUT.mkdir(exist_ok=True)
TRACE='''
window.__restoreTrace=[];
const sample=(step)=>{
 const m=JSON.parse(localStorage.getItem('exchange-guide-workspace-sync-v1')||'{}');
 __restoreTrace.push({step,account:state.account?.id||'',quarantined:state.quarantinedAccountOwnerId,syncOwner:state.accountWorkspaceSyncAccountId,storedOwner:m.account_id||'',storedPending:Object.keys(m.pending||{}),pending:Object.keys(state.accountWorkspacePending||{}),favorite:[...state.favorites],home:activeHomeSchool(),auth:state.authRestoreState,draftOwner:document.querySelector('#advisor-form')?.dataset.draftOwner,score:document.querySelector('#advisor-academic-score')?.value});
};
for(const name of ['readStoredState','readStoredAuthenticatedState','prepareAccountWorkspaceSyncForAccount','resetAccountWorkspaceOwnerScopedState','persistAccountWorkspaceSyncMetadata','clearProtectedCatalog','restoreAccount','acceptAccountSession','hydrateAccountWorkspace']){
 const f=window[name];window[name]=function(...args){sample(name+':before');const value=f.apply(this,args);sample(name+':after-sync');if(value?.then)value.then(()=>sample(name+':resolved'),()=>sample(name+':rejected'));return value;};
}
'''
class Capture:
 @pytest.hookimpl(hookwrapper=True)
 def pytest_fixture_setup(self,fixturedef,request):
  outcome=yield
  if fixturedef.argname=='page' and outcome.excinfo is None:
   page=outcome.get_result()
   def instrument(route):
    response=route.fetch();source=response.text();needle='boot().finally(() => window.UniWaySplash?.done());';assert needle in source;route.fulfill(response=response,body=source.replace(needle,TRACE+'\n'+needle))
   page.route('**/static/app.js?*',instrument)
 @pytest.hookimpl(hookwrapper=True)
 def pytest_runtest_makereport(self,item,call):
  outcome=yield;report=outcome.get_result()
  if report.when=='call' and 'page' in item.funcargs:
   page=item.funcargs['page'];name=item.name;values=page.evaluate('() => __restoreTrace');(OUT/(name+'.json')).write_text(json.dumps(dict(case=item.nodeid,outcome=report.outcome,trace=values,instrumentation='read-only browser wrappers; no repository source changes; synthetic data only'),ensure_ascii=False,indent=2)+'\n')
cases=['test_advisor_waits_for_login_and_clears_private_conditions_on_logout','test_session_restore_outage_quarantines_private_state_then_recovers_same_owner','test_reload_drains_pending_workspace_for_inactive_home_school']
before=subprocess.check_output(['git','status','--porcelain'],cwd=ROOT,text=True);assert not before
code=pytest.main(['tests/e2e/test_web_next_phase.py::'+x for x in cases]+['-vv','--tb=short',f'--junitxml={OUT}/suite.xml'],plugins=[Capture()]);assert not subprocess.check_output(['git','status','--porcelain'],cwd=ROOT,text=True)
(OUT/'result.json').write_text(json.dumps(dict(tested_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),cases=cases,actual_exit_code=int(code),clean_start_end=True,scope='instrumented diagnostic, not full acceptance'),indent=2)+'\n');raise SystemExit(code)
