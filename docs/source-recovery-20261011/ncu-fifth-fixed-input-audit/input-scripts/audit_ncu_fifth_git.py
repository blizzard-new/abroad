"""Independently audit the next immutable NCU input without changing active candidate."""
from pathlib import Path
from collections import Counter
import subprocess,json,gzip,base64,hashlib,io
from PIL import Image,ImageDraw,ImageFont
from bs4 import BeautifulSoup
app=Path('/workspace/abroad-globe-20261011');sha='baf98c0df400ef96aa83fb587107eb22513c0b97';base='e25ff02a1ebc69ea126a814d105e88b272539351';pre='sources/ncu/2026-10-11/';bundle='src/exchange_info/official_data/ncu/';rawroot=Path('/workspace/recovery-evidence-20261011');images=rawroot/'ncu-fifth-reviewed-images';images.mkdir(exist_ok=True)
def blob(p,head=sha):return subprocess.check_output(['git','show',head+':'+p],cwd=app)
def data(p,head=sha):
 b=blob(p,head);return json.loads(gzip.decompress(b) if p.endswith('.gz') else b)
photos=data(bundle+'campus-assets.json')['photos'];old={(r['school_name'],r['country']):r for r in data(bundle+'campus-assets.json',base)['photos']};new=[];hashes=[]
for r in photos:
 p='src/exchange_info/'+r['image_url'].lstrip('/');b=blob(p);digest=hashlib.sha256(b).hexdigest();assert digest==r['content_sha256'];im=Image.open(io.BytesIO(b));im.verify();hashes.append(digest)
 previous=old.get((r['school_name'],r['country']))
 if previous:
  for k in ['content_sha256','author','license','license_url','image_page_url']:assert previous[k]==r[k],(r['school_name'],k)
 else:
  name=Path(p).name;(images/name).write_bytes(b);new.append(r)
assert len(photos)==200 and len(new)==7 and len(set(hashes))==197
packs=[];receipts={};pdfs=[]
for name in ['resume-fourth-location-sourcepack.json.gz','resume-fifth-photo-sourcepack.json.gz','resume-fifth-location-sourcepack.json.gz','resume-ktu-meiji-original-responses.json.gz']:
 rows=data(pre+name);statuses=Counter()
 for r in rows:
  receipt=r['receipt'];statuses[receipt['status']]+=1
  b=base64.b64decode(r['raw_base64']) if 'raw_base64'in r else r['raw_utf8'].encode('utf-8');assert hashlib.sha256(b).hexdigest()==receipt['sha256'],(name,receipt['url']);receipts[receipt['sha256']]={'receipt':receipt,'body':b}
  if b.startswith(b'%PDF'):
   filename=r.get('source_id') or r.get('local_evidence_key','source').replace('/','-');path=images/(filename+'.pdf');path.write_bytes(b);pdfs.append(str(path))
 packs.append({'path':pre+name,'records':len(rows),'all_raw_response_hashes_verified':True,'http_statuses':dict(statuses)})
reviews=data(pre+'campus-photo-reviews.json')['rows'];grant=[]
for r in reviews:
 if not r.get('license_review'):continue
 proof=r['license_review'];assert proof['image_sha256']==r['sha256'];assert proof['declaration']['url']==r['page_url'];assert proof['status']=='reviewed_original_author_grant';parts=[]
 for key in ['declaration','terms','upload_history']:
  ev=proof[key];b=blob(ev['file']);b=gzip.decompress(b) if ev['file'].endswith('.gz') else b;assert hashlib.sha256(b).hexdigest()==ev['sha256'];parts.append({'kind':key,**ev});path=images/(r['id']+'-'+key+'.txt');path.write_text(BeautifulSoup(b,'html.parser').get_text(' ',strip=True) if key!='upload_history' else b.decode())
 grant.append({'id':r['id'],'school_name':r['school_name'],'author':r['author_html'],'author_url':r.get('author_url'),'license':r['license'],'license_url':r['license_url'],'proof':proof,'source_parts_hashes':parts})
locations=data(bundle+'campus-locations.json')['locations'];previous={(r['school_name'],r['country']):r for r in data(bundle+'campus-locations.json',base)['locations']};add=[r for r in locations if (r['school_name'],r['country']) not in previous];changed=[r for r in locations if (r['school_name'],r['country']) in previous and r!=previous[(r['school_name'],r['country'])]]
assert len(add)==7 and not changed and Counter(r['geocode_status'] for r in locations)=={'verified':188,'needs_review':1}
workflow_changes={}
for name in ['partners.jsonl','application_workflows.jsonl','destination_profiles.jsonl']:
 oldrows=blob(bundle+name,base).splitlines();newrows=blob(bundle+name).splitlines();assert len(oldrows)==len(newrows)==214
 change=[{'index':i,'school':json.loads(a)['school_name']} for i,(a,b) in enumerate(zip(oldrows,newrows)) if a!=b];assert [x['index'] for x in change]==[90,136];workflow_changes[name]=change
protected=[f'src/exchange_info/official_data/{home}' for home in ['cgu','ntpu','ntu','ccu','tku']]+['supabase/migrations','.github/workflows','uv.lock','src/exchange_info/university_locations.py','src/exchange_info/official_data/university_locations.jsonl']
assert not subprocess.check_output(['git','diff','--name-only',base,sha,'--',*protected],cwd=app).strip()
font=ImageFont.truetype('/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc',17)
for start in [0,4]:
 sheet=Image.new('RGB',(1100,720),'white');draw=ImageDraw.Draw(sheet)
 for i,r in enumerate(new[start:start+4]):
  im=Image.open(images/Path(r['image_url']).name).convert('RGB');im.thumbnail((535,290));x=(i%2)*550;y=(i//2)*360;sheet.paste(im,(x,y));draw.text((x+2,y+294),r['school_name'][:27],fill='black',font=font);draw.text((x+2,y+318),r['license']+' '+r['author'][:32],fill='black',font=font)
 sheet.save(images/f'contact-{start//4+1}.jpg')
report={'source_commit':sha,'baseline':base,'licensed_photos':len(photos),'distinct_photo_sha':len(set(hashes)),'prior193bytes_attribution_unchanged':True,'new_photos':new,'raw_source_packs':packs,'nonCC_grants':grant,'all_scoped_locations':len(locations),'verified_locations':188,'new_locations':add,'changed_existing_locations':changed,'changed_generated_rows':workflow_changes,'protected_unchanged':protected,'native_pdfs':pdfs,'visual_licensing_named_campus_and_host_body_review':'pending independent manual review','all_current_school_complete':False}
(rawroot/'ncu-fifth-fixed-input-audit.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if k not in ['new_photos','nonCC_grants','new_locations']},ensure_ascii=False,indent=2))
