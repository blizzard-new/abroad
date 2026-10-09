import requests,json,tarfile,hashlib,time,posixpath,datetime,sys
from pathlib import Path
out=Path('/tmp/tku-governance-runtime-recovery')
repo=sys.argv[1];pinned=sys.argv[2];label=sys.argv[3];session=requests.Session()
r=session.get('https://auth.docker.io/token',params={'service':'registry.docker.io','scope':'repository:'+repo+':pull'},timeout=30)
assert r.status_code==200, 'Registry anonymous token HTTP '+str(r.status_code)
headers={'Authorization':'Bearer '+r.json()['token'],'Accept':'application/vnd.oci.image.index.v1+json,application/vnd.oci.image.manifest.v1+json,application/vnd.docker.distribution.manifest.list.v2+json,application/vnd.docker.distribution.manifest.v2+json'}
r=session.get('https://registry-1.docker.io/v2/'+repo+'/manifests/'+pinned,headers=headers,timeout=30);assert r.status_code==200;assert 'sha256:'+hashlib.sha256(r.content).hexdigest()==pinned
(out/(label+'-pinned-manifest.json')).write_bytes(r.content);manifest=r.json()
if 'manifests' in manifest:
 target=next(x for x in manifest['manifests'] if x.get('platform',{}).get('architecture')=='amd64' and x.get('platform',{}).get('os')=='linux');r=session.get('https://registry-1.docker.io/v2/'+repo+'/manifests/'+target['digest'],headers=headers,timeout=30);assert r.status_code==200;assert 'sha256:'+hashlib.sha256(r.content).hexdigest()==target['digest'];manifest=r.json()
(out/(label+'-amd64-manifest.json')).write_bytes(r.content);state={};rows=[]
class HashStream:
 def __init__(self,raw):self.raw=raw;self.hasher=hashlib.sha256();self.count=0
 def read(self,n=-1):
  data=self.raw.read(n);self.hasher.update(data);self.count+=len(data);return data
for index,layer in enumerate(manifest['layers']):
 response=session.get('https://registry-1.docker.io/v2/'+repo+'/blobs/'+layer['digest'],headers=headers,timeout=(30,60),stream=True)
 assert response.status_code==200, 'Layer '+str(index)+' HTTP '+str(response.status_code)
 stream=HashStream(response.raw); added=0;members=0
 with tarfile.open(fileobj=stream,mode='r|gz') as archive:
  for member in archive:
   members+=1;name=posixpath.normpath(member.name).removeprefix('./');parent=posixpath.dirname(name);base=posixpath.basename(name)
   if base=='.wh..wh..opq':
    for key in list(state):
     if key.startswith(parent+'/'):del state[key]
   elif base.startswith('.wh.'):
    target=posixpath.join(parent,base[4:])
    for key in list(state):
     if key==target or key.startswith(target+'/'):del state[key]
   elif member.isfile():state[name]=('file',member.size);added+=member.size
   elif member.isdir():state[name]=('dir',4096)
   elif member.islnk():state[name]=('link',posixpath.normpath(member.linkname).removeprefix('./'))
   elif member.issym():state[name]=('symlink',len(member.linkname))
 while stream.read(1024*1024):pass
 response.close();assert stream.count==layer['size'];assert 'sha256:'+stream.hasher.hexdigest()==layer['digest']
 logical=sum(v[1] for v in state.values() if v[0]=='file')
 allocated=sum(((v[1]+4095)//4096)*4096 for v in state.values() if v[0] in ('file','dir','symlink'))
 row={'index':index,'digest':layer['digest'],'compressed_bytes':stream.count,'compressed_digest_verified':True,'tar_members':members,'added_regular_file_bytes':added,'snapshot_regular_file_bytes':logical,'snapshot_estimated_4KiB_allocated_bytes':allocated,'snapshot_hardlinks':sum(v[0]=='link' for v in state.values())};rows.append(row)
 print(json.dumps(row),flush=True)
 (out/(label+'-space-progress.json')).write_text(json.dumps(rows,indent=2)+'\n')
proof={'checked_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'pinned_index':pinned,'amd64_manifest_SHA256':hashlib.sha256((out/(label+'-amd64-manifest.json')).read_bytes()).hexdigest(),'layers':rows,'compressed_bytes':sum(r['compressed_bytes'] for r in rows),'final_regular_file_bytes':rows[-1]['snapshot_regular_file_bytes'],'vfs_sum_snapshot_regular_bytes':sum(r['snapshot_regular_file_bytes'] for r in rows),'vfs_sum_snapshot_estimated_4KiB_allocated_bytes':sum(r['snapshot_estimated_4KiB_allocated_bytes'] for r in rows),'credentials_saved':False,'image_or_layer_content_saved':False,'production_access':False,'limitations':'Read-only model from all public layer tar metadata and verified compressed bytes; handles whiteouts and hardlinks without extracting. Excludes inode/xattr/daemon quota/current Docker-store usage and import transient copies; physical available space and exact required additional bytes remain unverified.'}
(out/(label+'-space-estimate.json')).write_text(json.dumps(proof,indent=2)+'\n');print(json.dumps({k:v for k,v in proof.items() if k!='layers'}),flush=True)
