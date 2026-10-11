"""Restore one byte-exact wheel from a verified lossless ZIP-range recipe."""
from pathlib import Path
import argparse,json,hashlib,base64,os,re
p=argparse.ArgumentParser();p.add_argument('recipe');p.add_argument('--output');a=p.parse_args()
recipe=json.loads(Path(a.recipe).read_text());assert recipe['format']=='exact-contiguous-zip-byte-ranges-v1'
base=Path(recipe['base_path']);chunks=Path(recipe['chunks_directory'])
with base.open('rb') as f:assert hashlib.file_digest(f,'sha256').hexdigest()==recipe['base_sha256']
target=Path(a.output or recipe['original_path']);target.parent.mkdir(parents=True,exist_ok=True);assert not target.exists(),target
partial=target.with_name(target.name+'.restoring');assert not partial.exists()
digest=hashlib.sha256();size=0
try:
 with base.open('rb') as bf,partial.open('xb') as out:
  for piece in recipe['pieces']:
   assert piece['bytes']>=0
   if 'base_offset' in piece:
    assert piece['base_offset']>=0;bf.seek(piece['base_offset']);data=bf.read(piece['bytes'])
   elif 'inline_base64' in piece:data=base64.b64decode(piece['inline_base64'],validate=True)
   else:
    assert re.fullmatch('[0-9a-f]{64}',piece['chunk']);data=(chunks/piece['chunk']).read_bytes()
   assert len(data)==piece['bytes'] and hashlib.sha256(data).hexdigest()==piece['sha256']
   out.write(data);digest.update(data);size+=len(data)
 assert size==recipe['original_bytes'] and digest.hexdigest()==recipe['original_sha256']
 os.replace(partial,target)
except BaseException:
 partial.unlink(missing_ok=True);raise
print(json.dumps({'output':str(target),'bytes':size,'sha256':digest.hexdigest(),'exact_original_bytes_restored':True}))
