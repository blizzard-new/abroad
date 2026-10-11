"""Retire reproducible, clean, inactive task-owned historical worktrees."""
from pathlib import Path
import subprocess,json,hashlib,os,datetime,shutil
common=Path('/workspace/abroad-integration');raw=Path('/workspace/recovery-evidence-20261011')
roots=[Path('/workspace')/n for n in ['abroad-memory','abroad-memory-followup','abroad-pr3','abroad-pr4']]
records=[]
for root in roots:
 def git(*args):return subprocess.check_output(['git',*args],cwd=root)
 assert not git('status','--porcelain','--untracked-files=all').strip(),root
 active=[]
 for proc in Path('/proc').iterdir():
  if not proc.name.isdigit() or int(proc.name)==os.getpid():continue
  try:
   cwd=(proc/'cwd').resolve();args=(proc/'cmdline').read_bytes().decode(errors='replace').split('\0')
   if cwd.is_relative_to(root) or any(a.startswith(str(root)+'/') for a in args):active.append(proc.name)
  except (OSError,RuntimeError):pass
 assert not active,(root,active)
 sha=git('rev-parse','HEAD').decode().strip();tree=git('rev-parse','HEAD^{tree}').decode().strip()
 entries=git('ls-tree','-rz','--full-tree','HEAD').split(b'\0');files=[]
 for line in entries:
  if not line:continue
  meta,name=line.split(b'\t',1);mode,kind,oid=meta.decode().split();assert kind=='blob'
  p=root/os.fsdecode(name)
  data=os.readlink(p).encode() if mode=='120000' else p.read_bytes()
  actual=hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()
  assert actual==oid,(root,p)
  files.append({'path':os.fsdecode(name),'git_blob':oid,'bytes':len(data)})
 row={'path':str(root),'sha':sha,'tree':tree,'tracked_files_verified':len(files),'tracked_bytes':sum(f['bytes'] for f in files),'files':files,'restore_command':['git','-C',str(common),'worktree','add','--detach',str(root),sha],'active_process_references':active,'clean_including_untracked':True,'source_commit_retained_in_common_git':True,'status':'verified_before_retirement'}
 records.append(row)
 (raw/'next2-historical-worktree-retirement.json').write_text(json.dumps({'scope':'Four owned completed Oct9 historical checkouts only; no branches/commits/evidence/wheels/current candidate/current dependency environment removed. All tracked bytes independently verified against retained Git blobs before clean git worktree remove. Reproducible restore commands included.','records':records},indent=2)+'\n')
 subprocess.run(['git','-C',str(common),'worktree','remove',str(root)],check=True)
 assert subprocess.check_output(['git','-C',str(common),'rev-parse',sha]).decode().strip()==sha
 row.update(status='retired',completed_at=datetime.datetime.now(datetime.timezone.utc).isoformat())
 (raw/'next2-historical-worktree-retirement.json').write_text(json.dumps({'scope':'Four owned completed Oct9 historical checkouts only; no branches/commits/evidence/wheels/current candidate/current dependency environment removed. All tracked bytes independently verified against retained Git blobs before clean git worktree remove. Reproducible restore commands included.','records':records},indent=2)+'\n')
 print(json.dumps({k:v for k,v in row.items() if k!='files'}),flush=True)
