import json,hashlib,base64,sys
from pathlib import Path
root=Path(__file__).resolve().parent
m=json.loads((root/'manifest.json').read_text())
for r in m['raw_files']:
 data=(root/r['relative_path']).read_bytes();assert len(data)==r['bytes'] and hashlib.sha256(data).hexdigest()==r['SHA256']
 assert hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()==r['git_blob_SHA1']
for r in m['large_raw_readable_indexes']:
 p=root/r['readable_index_path'];idx=json.loads(p.read_text());chunks=[];position=0
 for name in idx['chunks']:
  c=json.loads((p.parent/name).read_text());part=base64.b64decode(c['content']);assert c['offset']==position and len(part)==c['bytes'] and hashlib.sha256(part).hexdigest()==c['chunk_SHA256'];chunks.append(part);position+=len(part)
 data=b''.join(chunks);assert len(data)==idx['original_bytes'] and hashlib.sha256(data).hexdigest()==idx['original_SHA256'];assert data==(Path(__file__).resolve().parents[3]/idx['raw_repository_path']).read_bytes()
print(json.dumps({'raw_files_verified':len(m['raw_files']),'original94_verified':m['original94_copied_byte_identical'],'chunked_originals_reassembled':len(m['large_raw_readable_indexes']),'tested_product_commit':m['tested_product_commit']}))
