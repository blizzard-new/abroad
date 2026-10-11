"""Run original memory workload unchanged; capture browser evidence only on failure."""
from pathlib import Path
import sys,runpy,json,datetime,hashlib
from playwright.sync_api import Browser,Page
root=Path('/workspace/recovery-evidence-20261011')/(sys.argv[1]+'-diagnostic-images');root.mkdir(exist_ok=True)
events={};new_page=Browser.new_page;wait=Page.wait_for_function
def observing_page(self,*args,**kwargs):
 page=new_page(self,*args,**kwargs);rows=[];events[id(page)]=rows
 def log(kind,**values):rows.append({'time':datetime.datetime.now(datetime.timezone.utc).isoformat(),'kind':kind,**values})
 page.on('requestfailed',lambda r:log('requestfailed',url=r.url,error=r.failure))
 page.on('response',lambda r:log('response',url=r.url,status=r.status) if any(p in r.url for p in ['/student-dashboard','/school-life-context','/health']) else None)
 page.on('pageerror',lambda e:log('pageerror',error=str(e)))
 return page
def observing_wait(self,*args,**kwargs):
 try:return wait(self,*args,**kwargs)
 except Exception as error:
  report={'exception':str(error),'original_args':args,'original_kwargs':kwargs,'url':self.url,'events':events.get(id(self),[])}
  try:report['browser_state']=self.evaluate('''() => ({school:state.dashboard?.school_name, count:state.dashboard?.partner_universities?.length, loading:state.partnerDataLoading, selectedHomeSchool:state.selectedHomeSchool, publicSchool:state.publicSchool, schoolChoice:document.querySelector('#school-switcher')?.innerText, activeModal:document.querySelector('#school-modal')?.className, messages:[...document.querySelectorAll('[role="alert"],.toast,.notice')].map(x=>x.innerText), bodyTail:document.body.innerText.slice(-2000)})''')
  except Exception as capture_error:report['state_capture_error']=str(capture_error)
  (root/'wait-failure.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
  try:self.screenshot(path=str(root/'wait-failure.png'),full_page=True,timeout=10000)
  except Exception as capture_error:(root/'screenshot-error.txt').write_text(str(capture_error))
  raise
Browser.new_page=observing_page;Page.wait_for_function=observing_wait
original=Path('/workspace/recovery-tools-20261011/profile_final4_growth_memory.py')
assert hashlib.sha256(original.read_bytes()).hexdigest()=='850c281ddb88552be1eee6df287630893520e8990a32a1ad9164b842fe2e47d3'
sys.argv[0]=str(original)
runpy.run_path(str(original),run_name='__main__')
