from pathlib import Path
import json,hashlib,base64,subprocess,sys
root=Path('/tmp/tku-governance-b67d79a');out=root/'readable';out.mkdir(exist_ok=True)
paths=[root/'sql-diagnostic/result.json',root/'original-envelope-fixed/result.json',root/'missing-array-original-fixed/result.json',root/'missing-array-original-fixed-initial/result.json',root/'missing-array-original-fixed-second/result.json',Path('/tmp/tku-governance-runtime-recovery/rollback-pre-fix/result.json'),Path('/tmp/tku-governance-runtime-recovery/missing-published-pre-fix/case-result.json')]
manifest=[]
for raw in paths:
 data=raw.read_bytes();sha=hashlib.sha256(data).hexdigest();folder=out/(raw.parent.name+'-'+sha[:10]);folder.mkdir(exist_ok=True);chunks=[]
 for offset in range(0,len(data),150000):
  part=data[offset:offset+150000];filename=f'chunk-{offset//150000:03}.json';item={'original_absolute_path':str(raw),'original_SHA256':sha,'original_bytes':len(data),'offset':offset,'bytes':len(part),'chunk_SHA256':hashlib.sha256(part).hexdigest(),'encoding':'base64','content':base64.b64encode(part).decode()};path=folder/filename;path.write_text(json.dumps(item,ensure_ascii=False,indent=2)+'\n');assert path.stat().st_size<500000;chunks.append(filename)
 rebuilt=b''.join(base64.b64decode(json.loads((folder/name).read_text())['content']) for name in chunks);assert rebuilt==data
 spec={'original_absolute_path':str(raw),'original_SHA256':sha,'original_bytes':len(data),'chunks':chunks,'actual_local_reassembly_byte_identical':True,'candidate_commit':'b67d79aa3b6c30a9449801501256b64951f2c291','original_result_status_not_relabelled':True};(folder/'index.json').write_text(json.dumps(spec,indent=2)+'\n');manifest.append(spec)
(root/'readable-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n');print(json.dumps({'original_files':len(manifest),'readable_chunks':sum(len(x['chunks']) for x in manifest),'all_actual_reassemblies_byte_identical':True,'largest_readable_bytes':max(p.stat().st_size for p in out.rglob('*.json'))}))
