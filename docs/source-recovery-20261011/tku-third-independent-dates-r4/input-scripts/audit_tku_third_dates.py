"""Verify capture period against exact archived image metadata, not upload timestamps."""
from pathlib import Path
from collections import Counter
import gzip,hashlib,io,json,subprocess,zipfile,re
from bs4 import BeautifulSoup
from urllib.parse import unquote,urlparse
sha='563fb9328c7ce15efc1ac3883d8c3d641df01e98';prefix='src/exchange_info/official_data/tku/'
def blob(path):return subprocess.check_output(['git','show',sha+':'+path])
def obj(path):return json.loads(blob(path))
def plain(v):return BeautifulSoup(str(v or ''),'html.parser').get_text(' ',strip=True)
records=obj(prefix+'photo_date_metadata_checks.json');pack=obj(prefix+'capture_pack_manifest.json');photos=obj(prefix+'campus_asset_manifest.json')
for arc in pack['archives']:
 names=[n for n,r in pack['files'].items() if r['archive']==arc['file'] and n.endswith('.json.gz') and n.split('/')[0] in ('commons_campus_candidates','asset_batch_sources','asset_source_retries')]
 if not names:continue
 data=b''.join(blob(prefix+'capture_packs/'+p['file']) for p in arc['parts']);assert hashlib.sha256(data).hexdigest()==arc['sha256']
 with zipfile.ZipFile(io.BytesIO(data)) as z:
  for n in names:
   b=z.read(n);assert hashlib.sha256(b).hexdigest()==pack['files'][n]['sha256'];r=json.loads(gzip.decompress(b));r['_file']=n;records.append(r)
index={};checked=0;capture_errors=[]
for r in records:
 if not r.get('response_text'):continue
 body=r['response_text'].encode()
 if hashlib.sha256(body).hexdigest()!=r['sha256']:
  capture_errors.append({'file':r.get('_file'),'id':r.get('id'),'source_url':r.get('source_url'),'declared':r['sha256'],'actual':hashlib.sha256(body).hexdigest()});continue
 checked+=1
 if r.get('http_status')!=200 or not isinstance(r.get('response'),dict):continue
 assert json.loads(body)==r['response']
 pages=r['response'].get('query',{}).get('pages',{})
 if isinstance(pages,dict):pages=pages.values()
 for p in pages:
  for i in p.get('imageinfo',[]):index[(r['sha256'],p['title'])]=(r,i)
rows=[];errors=[]
for photo in photos:
 title=photo.get('title') or unquote(urlparse(photo['source_url']).path.split('/wiki/',1)[1]).replace('_',' ')
 for ev in photo['photo_date_evidence']:
  item=index.get((ev['content_sha256'],title))
  if not item:errors.append({'id':photo['id'],'error':'exact capture/title missing','sha':ev['content_sha256']});continue
  r,i=item;meta=i.get('extmetadata',{});info=plain(meta.get('DateTimeOriginal',{}).get('value'));exif=next((plain(x.get('value')) for x in i.get('metadata',[]) if x.get('name')=='DateTimeOriginal'),'');quoted=json.loads(ev['quote']);assert quoted=={'information_date':info,'camera_exif_date_time_original':exif},(photo['id'],quoted,info,exif)
  assert photo['photo_date'] in [info,exif],(photo['id'],photo['photo_date'],info,exif)
  assert photo.get('upload_date_used_as_photo_date') is False
  years=[re.findall(r'(?<!\d)(?:19|20)\d{2}(?!\d)',x) for x in [info,exif]]
  if years[0] and years[1] and years[0]!=years[1]:errors.append({'id':photo['id'],'error':'information date / camera EXIF year conflict','info':info,'exif':exif})
  rows.append({'id':photo['id'],'title':title,'source_sha':r['sha256'],'date':photo['photo_date'],'information_date':info,'exif':exif,'author':plain(meta.get('Artist',{}).get('value')),'date_source_url_exact':ev['source_url']==r.get('source_url'),'source_url':r.get('source_url')})
report={'source_commit':sha,'verified_response_text_hashes':checked,'unusable_capture_hash_mismatches':capture_errors,'verified_photo_dates':len(rows),'rows':rows,'errors':errors,'visual_review':'17 newly added/replaced photo bytes reviewed via three contact sheets; 15 without institution identity/attribution blocker; Sunderland wrong UWE institution and UAEMEX unknown author remain excluded pending resolution','period_scope':'Historical capture period only; no current nomination campus claim','note':'Date consistency cannot cure wrong school identity or missing attribution.'}
Path('/workspace/recovery-evidence-20261011/tku-third-independent-date-review.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({k:v for k,v in report.items() if k!='rows'},ensure_ascii=False,indent=2))
assert len(rows)==264 and not errors
