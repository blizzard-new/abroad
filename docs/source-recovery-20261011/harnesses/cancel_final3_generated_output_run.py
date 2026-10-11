from pathlib import Path
import os,signal,json,time,datetime,re,subprocess
procs={}
for p in Path('/proc').iterdir():
 if not p.name.isdigit():continue
 try:cmd=(p/'cmdline').read_bytes().split(b'\0');status=(p/'status').read_text();parent=int(re.search(r'^PPid:\s*(\d+)',status,re.M)[1])
 except (OSError,ValueError,TypeError):continue
 procs[int(p.name)]=(parent,cmd)
roots=[pid for pid,(_,cmd)in procs.items() if len(cmd)>1 and cmd[1]==b'/workspace/recovery-tools-20261011/run_final3_full_suite.py'];assert len(roots)==1,roots
ids=set(roots)
while True:
 new={p for p,(pp,cmd)in procs.items()if pp in ids}-ids
 if not new:break
 ids|=new
root=roots[0];os.kill(root,signal.SIGSTOP)
for pid in sorted(ids-{root},reverse=True):
 try:os.kill(pid,signal.SIGTERM)
 except ProcessLookupError:pass
os.kill(root,signal.SIGKILL)
r=Path('/workspace/recovery-evidence-20261011');records=[]
for i in range(4):
 d=r/f'integration-final3-full-shard-{i}'
 if not d.exists():records.append({'shard':i,'status':'notrun'});continue
 m=json.load(open(d/'metadata.json'));text=(d/'stdout.log').read_text(errors='replace');cases=re.findall(r'WEB_CASE (.*?) call (passed|failed) ([\d.]+)s',text);status=subprocess.check_output(['git','status','--porcelain'],cwd='/workspace/abroad-globe-20261011',text=True)
 m.update(test_result='cancelled',exit_code=None,finished_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),reason='Four new NCU browser modules write screenshots under tracked docs paths. Test/application assertions unchanged; stop to redirect output and bind complete rerun to a clean new SHA.',end_guard={'sha':subprocess.check_output(['git','rev-parse','HEAD'],cwd='/workspace/abroad-globe-20261011',text=True).strip(),'status':status},observed_call_results=[{'case':a,'result':b,'seconds':float(c)}for a,b,c in cases]);(d/'metadata.json').write_text(json.dumps(m,indent=2)+'\n');records.append({'shard':i,'status':'cancelled','observed_completed_test_calls':len(cases),'passed':sum(b=='passed'for a,b,c in cases),'failed':sum(b=='failed'for a,b,c in cases),'not_run_or_not_completed':len(json.load(open(d/'shard-coverage/partition.json'))['assigned_cases'])-len(cases) if 'assigned_cases' in json.load(open(d/'shard-coverage/partition.json')) else 'see partition and observed cases; remaining not completed'})
(r/'integration-final3-cancellation.json').write_text(json.dumps({'root_pid':root,'terminated_task_process_count':len(ids),'reason':'Tracked screenshot output; no product-source modification during run','records':records},indent=2)+'\n');print(records)
