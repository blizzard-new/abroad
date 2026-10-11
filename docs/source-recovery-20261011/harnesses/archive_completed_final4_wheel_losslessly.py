"""Preserve exact old wheel bytes as ZIP-range recipes against a retained base wheel."""
from pathlib import Path
import json,hashlib,zipfile,struct,base64,os,datetime
raw=Path('/workspace/recovery-evidence-20261011')
archive=Path('/tmp/abroad-historical-wheel-lossless-20261011');archive.mkdir(exist_ok=True);chunks=archive/'chunks';chunks.mkdir(exist_ok=True)
base=Path('/workspace/integration-next1-wheel-artifacts-20261011/taiwan_exchange_info-0.1.0-py3-none-any.whl')
assert base.is_file()
def hashfile(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
basehash=hashfile(base);assert basehash=='682c304eaa6926b56a8ab675f601755b907b7a7d4601686d6640002c446e45a4'
def ranges(path):
 with zipfile.ZipFile(path) as z,path.open('rb') as f:
  prior=0
  for entry in sorted(z.infolist(),key=lambda r:r.header_offset):
   f.seek(entry.header_offset);header=f.read(30);assert header[:4]==b'PK\x03\x04'
   names,extra=struct.unpack_from('<HH',header,26);start=entry.header_offset+30+names+extra
   assert start>=prior
   yield prior,start-prior,'metadata'
   yield start,entry.compress_size,'compressed_member'
   prior=start+entry.compress_size
  assert prior<=path.stat().st_size
  yield prior,path.stat().st_size-prior,'metadata'
baseindex={}
with base.open('rb') as f:
 for start,size,kind in ranges(base):
  if kind!='compressed_member' or size<4096:continue
  f.seek(start);data=f.read(size);assert len(data)==size
  baseindex.setdefault((hashlib.sha256(data).hexdigest(),size),start)
roots=[Path('/workspace/integration-final4-wheel-artifacts-20261011')]
receipt=raw/'final4-wheel-lossless-archive.json';records=json.loads(receipt.read_text())['wheels'] if receipt.exists() else []
seen=set()
for folder in roots:
 files=list(folder.glob('*.whl'));assert len(files)==1,(folder,files)
 source=files[0];assert source.resolve()!=base.resolve()
 if source.resolve() in seen:continue
 seen.add(source.resolve());original_hash=hashfile(source);size_before=source.stat().st_size
 assert original_hash=='b3e3dfe6c560dfd02c85bb4a89a246b914ff35774d2fe7bcdd596c47a6728953'
 recipe=[];new_chunk_bytes=0;reuse_bytes=0
 with source.open('rb') as f:
  for start,size,kind in ranges(source):
   if not size:continue
   f.seek(start);data=f.read(size);assert len(data)==size;h=hashlib.sha256(data).hexdigest()
   if kind=='compressed_member' and (h,size) in baseindex:
    recipe.append({'base_offset':baseindex[(h,size)],'bytes':size,'sha256':h});reuse_bytes+=size
   elif size<=4096:
    recipe.append({'inline_base64':base64.b64encode(data).decode(),'bytes':size,'sha256':h})
   else:
    target=chunks/h
    if not target.exists():
     with target.open('xb') as out:out.write(data)
     assert hashfile(target)==h;new_chunk_bytes+=size
    else:assert hashfile(target)==h
    recipe.append({'chunk':h,'bytes':size,'sha256':h})
 document={'format':'exact-contiguous-zip-byte-ranges-v1','original_path':str(source),'original_bytes':size_before,'original_sha256':original_hash,'base_path':str(base),'base_sha256':basehash,'chunks_directory':str(chunks),'pieces':recipe}
 target=archive/(original_hash+'.json');target.write_text(json.dumps(document,separators=(',',':'))+'\n')
 # Re-read the committed recipe and reconstruct every byte into a hash before
 # retiring the duplicate old wheel. No ZIP rewriting or recompression occurs.
 saved=json.loads(target.read_text());reconstructed=hashlib.sha256();total=0
 with base.open('rb') as bf:
  for piece in saved['pieces']:
   if 'base_offset' in piece:bf.seek(piece['base_offset']);data=bf.read(piece['bytes'])
   elif 'inline_base64' in piece:data=base64.b64decode(piece['inline_base64'])
   else:data=(chunks/piece['chunk']).read_bytes()
   assert len(data)==piece['bytes'] and hashlib.sha256(data).hexdigest()==piece['sha256']
   reconstructed.update(data);total+=len(data)
 assert total==size_before and reconstructed.hexdigest()==original_hash
 row={'original_path':str(source),'original_bytes':size_before,'original_sha256':original_hash,'lossless_recipe':str(target),'recipe_sha256':hashfile(target),'new_chunk_bytes':new_chunk_bytes,'bytes_referenced_from_retained_base':reuse_bytes,'all_reconstructed_bytes_hash_verified_before_retirement':True,'completed_at':datetime.datetime.now(datetime.timezone.utc).isoformat()}
 hint=source.with_name(source.name+'.lossless-recipe.json');hint.write_text(json.dumps(row,indent=2)+'\n')
 source.unlink();records.append(row)
 report={'scope':'Completed historical wheel duplicates stored losslessly as literal headers/trailers plus exact compressed member byte ranges. Base4a wheel retained intact; all reconstruction hashes match original wheel bytes, including ZIP timestamps/metadata. This is storage deduplication, not new build/test acceptance. Every original can be restored without network.','archive_root':str(archive),'retained_base_path':str(base),'retained_base_sha256':basehash,'wheels':records}
 receipt.write_text(json.dumps(report,indent=2)+'\n');(archive/'final4-manifest.json').write_text(json.dumps(report,indent=2)+'\n')
 print(json.dumps({k:v for k,v in row.items() if k!='completed_at'}),flush=True)
