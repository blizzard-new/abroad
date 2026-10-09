import subprocess,os,json,time
from pathlib import Path
root=Path('/workspace/abroad-tku-governance-final-check');out=Path('/tmp/tku-governance-5d48a01');sha='5d48a01a7a58aad7fe972e7ec1434e0fb74e93c3'
def state():return {'commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip(),'dirty':subprocess.check_output(['git','status','--porcelain'],cwd=root,text=True).strip()}
before=state();assert before=={'commit':sha,'dirty':''}
command=['/workspace/abroad-tku/.venv/bin/python','-m','pytest','tests','--collect-only','-q']
r=subprocess.run(command,cwd=root,env={**os.environ,'PYTHONPATH':str(root/'src')},capture_output=True,text=True)
(out/'collect-original.log').write_text(r.stdout+r.stderr);assert r.returncode==0
nodes=[line for line in r.stdout.splitlines() if line.startswith('tests/') and '::' in line]
original=set()
for aid in [11598977773,11599295606,11598686528,11599126161]:original.update((Path('/tmp/tku-ci-09386aa/remote-artifacts')/str(aid)/'collect-nodeids.txt').read_text().splitlines())
assert len(original)==1789 and len(nodes)==len(set(nodes))==1827 and original.issubset(nodes)
after=state();assert before==after
(out/'collect-nodeids.txt').write_text('\n'.join(nodes)+'\n')
report={'tested_commit':sha,'starting_state':before,'ending_state':after,'candidate_guard_passed':True,'actual_exit_code':r.returncode,'command':command,'unique_ids':1827,'files':len({n.split('::')[0] for n in nodes}),'removed_ids':[],'added_ids':sorted(set(nodes)-original),'duplicate_ids':0,'comparison':'Actual original093 PR artifact collection, not source-name inference'}
(out/'all-id-preservation.json').write_text(json.dumps(report,indent=2)+'\n');print(report)
