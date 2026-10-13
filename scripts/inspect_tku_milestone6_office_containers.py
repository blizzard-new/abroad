"""Identify two unexpected public Office containers without opening/decryption."""
import gzip,hashlib,json,struct,time
from datetime import datetime,timezone
import requests
from tku_capture_io import BUNDLE,exists,read_bytes

URLS=['https://u-aizu.ac.jp/osip/information/ay2027_spring_sas_1_course_selection_form.xlsx','https://u-aizu.ac.jp/osip/information/ay2027_spring_sas_2_4_common.docx']
OLE=bytes.fromhex('d0cf11e0a1b11ae1')
def directory_names(blob):
 # CFB directory entries are128-byte aligned and contain UTF16 names/type.
 # Read only this public container metadata; no password/decryption attempt.
 result=[]
 for off in range(512,len(blob)-127,128):
  item=blob[off:off+128];size=struct.unpack_from('<H',item,64)[0]
  if item[66] not in (1,2,5) or size<4 or size>64 or size%2:continue
  try:name=item[:size-2].decode('utf-16le')
  except UnicodeDecodeError:continue
  if name and '\x00' not in name and all(ord(c)>=32 for c in name):result.append(name)
 return sorted(set(result))
def main():
 store=BUNDLE/'host_census_sources';idxpath=BUNDLE/'host_census_capture_index.json';idx=json.loads(idxpath.read_text());school=next(r for r in idx if r['id']=='tku-sister-39');reviews=[]
 for url in URLS:
  sid=hashlib.sha256((url+'-milestone6-office-format-inspection').encode()).hexdigest()[:24];path=store/(sid+'.json.gz')
  if exists(path):record=json.loads(gzip.decompress(read_bytes(path)))
  else:
   record=dict(id=sid,source_url=url,checked_at=datetime.now(timezone.utc).isoformat(),text='',content_scope='Container format inspection only; no decryption, no password, no document content/year verified')
   try:
    response=requests.get(url,timeout=(8,22),headers={'User-Agent':'UniWayTKUReference/1.0'});blob=response.content;record.update(http_status=response.status_code,final_url=response.url,bytes=len(blob),sha256=hashlib.sha256(blob).hexdigest(),response_magic=blob[:16].hex(),content_type=response.headers.get('Content-Type'));response.raise_for_status()
    if blob.startswith(OLE):
     names=directory_names(blob);locked={'EncryptionInfo','EncryptedPackage'}<=set(names);filename=sid+'.ole';(store/filename).write_bytes(blob);record.update(local_file=filename,container='OLE Compound File',directory_names=names,encrypted_office_package=locked,content_opened=False,error='EncryptedOfficeContainer: public binary obtained; no decryption attempted' if locked else 'OLEOfficeContainer: unexpected format; content not parsed')
    else:record.update(error='UnexpectedContentFormat: not OLE; no document body verified',response_preview=blob[:256].decode('utf-8',errors='replace'))
   except requests.RequestException as exc:record['error']=type(exc).__name__+': '+str(exc)
   path.write_bytes(gzip.compress(json.dumps(record,ensure_ascii=False).encode(),mtime=0));time.sleep(1)
  if not any(e['id']==sid for e in school['sources']):school['sources'].append(dict(id=sid,source_url=url,final_url=record.get('final_url'),http_status=record.get('http_status'),error=record.get('error'),checked_at=record['checked_at'],sha256=record.get('sha256'),title='Public Office container metadata inspection',source_role='milestone6_encryption_boundary_review',linked_from='https://www.u-aizu.ac.jp/osip/en/information/icrp-app.html',scope='Opaque bytes retained; no readable content or academic-year verification'))
  reviews.append(record)
 idxpath.write_text(json.dumps(idx,ensure_ascii=False,indent=2)+'\n');(BUNDLE/'milestone6_office_container_reviews.json').write_text(json.dumps(reviews,ensure_ascii=False,indent=2)+'\n');print(json.dumps([{k:r.get(k) for k in ['id','http_status','bytes','container','directory_names','encrypted_office_package','content_opened','error']} for r in reviews],ensure_ascii=False))
if __name__=='__main__':main()
