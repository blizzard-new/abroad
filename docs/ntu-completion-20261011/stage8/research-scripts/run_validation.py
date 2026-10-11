from pathlib import Path
import os,json,hashlib,subprocess,datetime,time,shutil
R=Path('/workspace/abroad-ntu-completion-20261011');A=Path('/workspace/abroad-ntu-pr8-acceptance-20261011');H=Path(__file__).parent;D=R/'docs/ntu-completion-20261011/stage8/validation';D.mkdir(parents=True,exist_ok=True)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();now=lambda:datetime.datetime.now(datetime.timezone.utc).isoformat();py='/workspace/abroad/.venv/bin/python';source=R/'sources/ntu/completion-2026-10-11.json';snap=json.loads(source.read_text());count=sum(len(s['observations']) for s in snap['schools']);(D/'tested-source-snapshot.json').write_bytes(source.read_bytes());materialized={str(p.relative_to(R)):sha(p) for p in (R/'src/exchange_info/official_data/ntu').iterdir() if p.is_file()};tests={str(p.relative_to(R)):sha(p) for p in (R/'tests').rglob('*.py')};code={str(p.relative_to(R)):sha(p) for base in ['src','scripts'] for p in (R/base).rglob('*.py')};receipt={'started_at':now(),'source_sha256':sha(source),'observations':count,'summary_adapter_sha256':sha(R/'src/exchange_info/ntu_partner_summary.py'),'test_files_sha256':tests,'code_files_sha256':code,'materialized_files_sha256':materialized,'current_cycle_rules_promoted':False,'merge_or_deploy':False,'jobs':{}};env=os.environ.copy();env['PYTHONPATH']='src';env['PLAYWRIGHT_BROWSERS_PATH']='/workspace/.abroad-cloud-tools/ms-playwright'
ntu=['tests/e2e/test_ntu_school.py','tests/e2e/test_ntu_destination_enrichment.py','tests/e2e/test_ntu_official_changes.py','tests/e2e/test_ntu_completion.py','tests/e2e/test_ntu_reference_scope.py'];focused=['tests/test_visual_coverage.py','tests/test_school_photo_and_match.py','tests/test_university_locations.py','tests/test_ntu_completion.py','tests/test_ntu_official_changes.py']
jobs=[('full-regression',R,['--ignore=tests/e2e']),('browser',R,ntu),('pr8-combined-browser',A,ntu+['tests/e2e/test_six_school_visual_coverage.py']),('pr8-combined-focused',A,focused)];running=[]
queued=[j for j in jobs if j[0]=='pr8-combined-browser'];jobs=[j for j in jobs if j[0]!='pr8-combined-browser']
def start(name,cwd,args):
 command=[py,'-m','pytest','-q',*args];log=D/(name+'.log');f=log.open('w');job_env=dict(env);job_env['VISUAL_EVIDENCE_DIR']=str(D/'pr8-combined-visual');p=subprocess.Popen(command,cwd=cwd,env=job_env,stdout=f,stderr=subprocess.STDOUT);running.append((name,p,f));receipt['jobs'][name]={'command':command,'cwd':str(cwd),'started_at':now(),'log':log.name};print('started '+name,flush=True)
for job in jobs:start(*job)
(D/'run-receipt.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n')
while running:
 for job in list(running):
  name,p,f=job
  if p.poll() is not None:
   f.close();receipt['jobs'][name].update(returncode=p.returncode,completed_at=now());running.remove(job);print('finished '+name+' exit '+str(p.returncode),flush=True)
   if name=='browser':
    for source_folder in [R/'docs/ntu-completion-20261011/browser',R/'docs/ntu-completion-20261011/stage7/validation/new-reference-browser',Path('/tmp/ntu-destinations-browser'),Path('/tmp/ntu-audit/browser'),Path('/workspace/ntu-research-2026-10-10/test-evidence')]:
     if source_folder.exists():
      target=D/'main-browser-evidence'/source_folder.name;target.mkdir(parents=True,exist_ok=True)
      for image in source_folder.glob('*.png'):shutil.copyfile(image,target/image.name)
    for original in [R/'docs/ntu-completion-20261011/browser',R/'docs/ntu-completion-20261011/stage7/validation/new-reference-browser']:
     for image in original.glob('*.png'):
      tracked=str(image.relative_to(R));old=subprocess.run(['git','show','HEAD:'+tracked],cwd=R,capture_output=True)
      if old.returncode==0:image.write_bytes(old.stdout)
    for delayed in queued:start(*delayed)
    queued.clear()
 if running:time.sleep(20)
assert sha(source)==receipt['source_sha256'],'Source mutated while testing';assert all(sha(R/p)==s for p,s in materialized.items());assert all(sha(R/p)==s for p,s in tests.items());assert all(sha(R/p)==s for p,s in code.items());receipt['completed_at']=now();receipt['source_code_tests_and_materialized_bytes_unchanged_during_tests']=True;(D/'run-receipt.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n');print('all bound checks complete',flush=True);assert all(v['returncode']==0 for v in receipt['jobs'].values()),'check failing log(s)'
