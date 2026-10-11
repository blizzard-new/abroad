"""Verify capture period against exact archived image metadata, not upload timestamps."""
from pathlib import Path
from collections import Counter
import gzip,hashlib,io,json,subprocess,zipfile,re
from bs4 import BeautifulSoup
from urllib.parse import unquote,urlparse
sha='93cbd9dfee3af95f9ecc89cceb1ccd0e100778af';prefix='src/exchange_info/official_data/tku/'
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
index={};revision_index={};checked=0;capture_errors=[];wire_encoding_reconstructions=[]
for r in records:
 if not r.get('response_text'):continue
 body=r['response_text'].encode()
 if hashlib.sha256(body).hexdigest()!=r['sha256']:
  matching=[]
  for encoding in ['latin1','cp1252','shift_jis','euc-jp','gb18030','cp950','utf-8-sig']:
   try:candidate=r['response_text'].encode(encoding)
   except UnicodeError:continue
   if hashlib.sha256(candidate).hexdigest()==r['sha256']:matching.append(encoding)
  if matching:wire_encoding_reconstructions.append({'file':r.get('_file'),'source_url':r.get('source_url'),'sha256':r['sha256'],'exact_hash_matching_encodings':matching})
  else:
   capture_errors.append({'file':r.get('_file'),'id':r.get('id'),'source_url':r.get('source_url'),'declared':r['sha256'],'actual_utf8':hashlib.sha256(body).hexdigest()});continue
 checked+=1
 if r.get('http_status')!=200 or not isinstance(r.get('response'),dict):continue
 assert json.loads(body)==r['response']
 pages=r['response'].get('query',{}).get('pages',{})
 if isinstance(pages,dict):pages=pages.values()
 for p in pages:
  if p.get('revisions'):revision_index[(r['sha256'],p['title'])]=(r,p)
  for i in p.get('imageinfo',[]):index[(r['sha256'],p['title'])]=(r,i)
rows=[];errors=[]
for photo in photos:
 title=photo.get('title') or unquote(urlparse(photo['source_url']).path.split('/wiki/',1)[1]).replace('_',' ')
 supported=[];details=[]
 for ev in photo['photo_date_evidence']:
  if ev['role']=='original_uploader_capture_date_statement':
   item=revision_index.get((ev['content_sha256'],title))
   if not item:errors.append({'id':photo['id'],'error':'exact revision capture/title missing'});continue
   r,p=item;body=json.dumps(p,ensure_ascii=False)
   assert ev['quote'] in body,(photo['id'],'revision quote mismatch')
   date=re.search(r'(20\d{2})年(\d{1,2})月(\d{1,2})日',ev['quote'])
   if date and photo['photo_date']=='%04d-%02d-%02d'%tuple(map(int,date.groups())):supported.append('original uploader capture date statement')
   details.append({'source_sha':r['sha256'],'kind':'original_revision','quote':ev['quote']});continue
  item=index.get((ev['content_sha256'],title))
  if not item:errors.append({'id':photo['id'],'error':'exact capture/title missing','sha':ev['content_sha256']});continue
  r,i=item;meta=i.get('extmetadata',{});info=plain(meta.get('DateTimeOriginal',{}).get('value'));exif=next((str(x.get('value') or '') for x in i.get('metadata',[]) if x.get('name')=='DateTimeOriginal'),'');quoted=json.loads(ev['quote'])
  if quoted!={'information_date':info,'camera_exif_date_time_original':exif}:errors.append({'id':photo['id'],'error':'quoted metadata mismatch','quote':quoted,'actual':[info,exif]})
  if photo['photo_date']==info and info and not any(t in info.lower() for t in ['upload','unknown','none','n/a']):supported.append('Information.Date')
  if photo['photo_date']==exif and re.search(r'(?<!\d)(?:19|20)\d{2}(?!\d)',exif):supported.append('camera EXIF.DateTimeOriginal')
  years=[re.findall(r'(?<!\d)(?:19|20)\d{2}(?!\d)',x) for x in [info,exif]]
  if years[0] and years[1] and set(years[0])!=set(years[1]) and 'upload' not in info.lower():errors.append({'id':photo['id'],'error':'information date / camera EXIF year conflict','info':info,'exif':exif})
  details.append({'source_sha':r['sha256'],'date':photo['photo_date'],'information_date':info,'exif':exif,'author':plain(meta.get('Artist',{}).get('value')),'date_source_url_exact':ev['source_url']==r.get('source_url'),'source_url':r.get('source_url')})
 assert photo.get('upload_date_used_as_photo_date') is False
 if not supported:errors.append({'id':photo['id'],'error':'no independent matching capture period','details':details})
 rows.append({'id':photo['id'],'title':title,'supported_by':supported,'evidence':details})
report={'source_commit':sha,'verified_response_text_hashes':checked,'unresolved_capture_wire_hashes':capture_errors,'wire_encoding_reconstructions':wire_encoding_reconstructions,'verified_photo_dates':len(rows),'rows':rows,'errors':errors,'visual_review':'Prior 17 changed assets visually reviewed; two rejected assets withdrawn. No fresh visual review of every unchanged baseline photo claimed.','period_scope':'Historical capture period only; no current nomination campus claim','note':'Date consistency cannot cure wrong school identity or missing attribution. Original-upload dates are distinct from EXIF capture dates. JIU capture2007-03-29 is supported by the original Japanese uploader statement; FIT2010 capture also agrees with its original description. HTML source SHA is wire bytes, not necessarily response_text encoded asUTF8.'}
Path('/workspace/recovery-evidence-20261011/tku-sixth-independent-date-review.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({k:v for k,v in report.items() if k!='rows'},ensure_ascii=False,indent=2))
assert len(rows)==262 and not errors
