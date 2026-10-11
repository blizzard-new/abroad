from pathlib import Path
import io, os, subprocess, tarfile, hashlib, json
root=Path('/workspace/abroad-globe-20261011');dest=Path('/workspace/recovery-baseline-985224fd')
assert not dest.exists();dest.mkdir()
sha='985224fd01748a6c591fc183362847d6d7d21c35'
proc=subprocess.Popen(['git','archive',sha,'src','tests'],cwd=root,stdout=subprocess.PIPE)
manifest=[]; linked=copied=0
with tarfile.open(fileobj=proc.stdout,mode='r|') as archive:
 for member in archive:
  if not member.isfile():continue
  target=dest/member.name;target.parent.mkdir(parents=True,exist_ok=True)
  raw=archive.extractfile(member).read();current=root/member.name
  if current.is_file() and current.stat().st_size==len(raw) and hashlib.sha256(current.read_bytes()).digest()==hashlib.sha256(raw).digest():
   os.link(current,target);linked+=1
  else:target.write_bytes(raw);copied+=1
  manifest.append({'path':member.name,'sha256':hashlib.sha256(raw).hexdigest()})
assert proc.wait()==0
(dest/'.baseline-sha').write_text(sha+'\n')
(dest/'source-manifest.json').write_text(json.dumps({'sha':sha,'scope':['src','tests'],'files':manifest},indent=2)+'\n')
print({'sha':sha,'files':len(manifest),'hardlinked_unchanged':linked,'copied_changed':copied})
s=Path('/workspace/recovery-tools-20261011/run_check.py').read_text()
s=s.replace("def guard():return {'sha':git('rev-parse','HEAD'),'tree':git('rev-parse','HEAD^{tree}'),'status':git('status','--porcelain=v1')}","def guard():return {'sha':pathlib.Path(a.cwd,'.baseline-sha').read_text().strip(),'status':'archived src/tests snapshot; source-manifest.json records every file; no Git checkout'}")
Path('/workspace/recovery-tools-20261011/run_baseline.py').write_text(s)
