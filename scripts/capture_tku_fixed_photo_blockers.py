"""Four fixed public attribution sources; no login or replacement search.

The two original-page captures were taken before this driver was saved. Their
immutable filenames are reused. Follow only actual original-source/history links.
"""
import gzip,hashlib,json
from datetime import datetime,timezone
from pathlib import Path
import requests
from bs4 import BeautifulSoup
from capture_tku_asset_batch import paused
from tku_capture_io import BUNDLE as B,read_bytes,exists

URLS=[
 'https://commons.wikimedia.org/wiki/File:Block_B,_University_of_the_West_of_England_-_geograph.org.uk_-_6031781.jpg',
 'https://commons.wikimedia.org/wiki/File:EidicioA_FCPyS.jpg',
 'https://www.facebook.com/photo.php?fbid=326874986524193&set=pb.100076050829544.-2207520000&type=3',
 'https://commons.wikimedia.org/w/index.php?title=File:EidicioA_FCPyS.jpg&action=history',
]
def main():
 rows=[]
 for url in URLS:
  sid=hashlib.sha256((url+'|fixed-photo-blocker-8b7570').encode()).hexdigest()[:24];file='asset_batch_sources/milestone6-photo-'+sid+'.json.gz';path=B/file
  if exists(path):r=json.loads(gzip.decompress(read_bytes(path)))
  else:
   r=dict(id=sid,source_url=url,checked_at=datetime.now(timezone.utc).isoformat(),scope='Fixed two photo blockers only: source/history attribution; no login or unlimited replacement search')
   if paused('commons'):r.update(error='active_retry_after_pause_no_request')
   else:
    try:
     res=requests.get(url,timeout=(8,22),headers={'User-Agent':'UniWayTKUDataAudit/1.0 (https://github.com/blizzard-new/abroad; public academic reference audit)'})
     r.update(http_status=res.status_code,final_url=res.url,sha256=hashlib.sha256(res.content).hexdigest(),response_text=res.text,text=BeautifulSoup(res.content,'html.parser').get_text(' ',strip=True),retry_after=res.headers.get('Retry-After'));res.raise_for_status()
    except requests.RequestException as e:r['error']=type(e).__name__+': '+str(e)
   path.parent.mkdir(exist_ok=True);path.write_bytes(gzip.compress(json.dumps(r,ensure_ascii=False).encode(),mtime=0))
  rows.append(dict(**{k:v for k,v in r.items() if k!='response_text'},capture_file=file))
  print(url,r.get('http_status'),r.get('error'),flush=True)
  if r.get('http_status')==429:break
 (B/'fixed_photo_blocker_source_checks.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2)+'\n')
if __name__=='__main__':main()
