"""Materialize fixed CCU input, sharing unchanged sources read-only; retire this snapshot before changing active candidate."""
from pathlib import Path
import hashlib, json, os, subprocess
sha='52ed6370c63f053da445a9aff6eb9e2a3d2ad6c8'
app=Path('/workspace/abroad-globe-20261011')
root=Path('/tmp/ccu-ninth-fixed-review-20261011');root.mkdir(exist_ok=False)
def git(*args):return subprocess.check_output(['git',*args],cwd=app)
rows=[]
for line in git('ls-tree','-r',sha,'--','src/exchange_info/official_data/ccu','src/exchange_info/static/assets/ccu/campuses').decode().splitlines():
    meta,name=line.split('\t');mode,kind,blob=meta.split();assert kind=='blob'
    dest=root/name;dest.parent.mkdir(parents=True,exist_ok=True)
    source=app/name
    linked=False
    if source.exists():
        body=source.read_bytes()
        if hashlib.sha1(b'blob '+str(len(body)).encode()+b'\0'+body).hexdigest()==blob:
            os.link(source,dest);linked=True
    if not linked:dest.write_bytes(git('show',sha+':'+name))
    body=dest.read_bytes();assert hashlib.sha1(b'blob '+str(len(body)).encode()+b'\0'+body).hexdigest()==blob
    rows.append({'path':name,'bytes':len(body),'sha256':hashlib.sha256(body).hexdigest(),'shared_unchanged_readonly_file':linked})
Path('/workspace/recovery-evidence-20261011/ccu-ninth-fixed-review-materialization.json').write_text(json.dumps({'sha':sha,'root':str(root),'files':rows},indent=2)+'\n')
print(json.dumps({'files':len(rows),'shared':sum(r['shared_unchanged_readonly_file'] for r in rows),'copied_bytes':sum(r['bytes'] for r in rows if not r['shared_unchanged_readonly_file'])}))
