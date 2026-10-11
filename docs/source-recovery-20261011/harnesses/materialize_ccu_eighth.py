"""Materialize fixed CCU input, sharing only unchanged immutable binary sources."""
from pathlib import Path
import hashlib, json, os, subprocess
sha='1b9563c58e2fa83c3c2510a40b7ccdd126db9dd1'
app=Path('/workspace/abroad-globe-20261011')
root=Path('/tmp/ccu-eighth-fixed-review-20261011');root.mkdir(exist_ok=False)
def git(*args):return subprocess.check_output(['git',*args],cwd=app)
rows=[]
for line in git('ls-tree','-r',sha,'--','src/exchange_info/official_data/ccu','src/exchange_info/static/assets/ccu/campuses').decode().splitlines():
    meta,name=line.split('\t');mode,kind,blob=meta.split();assert kind=='blob'
    dest=root/name;dest.parent.mkdir(parents=True,exist_ok=True)
    source=app/name
    linked=False
    if source.exists() and source.suffix in {'.gz','.pdf','.jpg','.png','.zip','.webp'}:
        body=source.read_bytes()
        if hashlib.sha1(b'blob '+str(len(body)).encode()+b'\0'+body).hexdigest()==blob:
            os.link(source,dest);linked=True
    if not linked:dest.write_bytes(git('show',sha+':'+name))
    body=dest.read_bytes();assert hashlib.sha1(b'blob '+str(len(body)).encode()+b'\0'+body).hexdigest()==blob
    rows.append({'path':name,'bytes':len(body),'sha256':hashlib.sha256(body).hexdigest(),'shared_immutable_binary':linked})
Path('/workspace/recovery-evidence-20261011/ccu-eighth-fixed-review-materialization.json').write_text(json.dumps({'sha':sha,'root':str(root),'files':rows},indent=2)+'\n')
print(json.dumps({'files':len(rows),'shared':sum(r['shared_immutable_binary'] for r in rows),'copied_bytes':sum(r['bytes'] for r in rows if not r['shared_immutable_binary'])}))
