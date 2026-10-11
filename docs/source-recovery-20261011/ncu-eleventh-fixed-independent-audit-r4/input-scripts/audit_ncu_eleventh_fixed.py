from pathlib import Path
import subprocess,json,gzip,hashlib,base64,io,re,collections
from PIL import Image
from bs4 import BeautifulSoup
from pypdf import PdfReader
SHA='a2df55b16f72455f7154d7afff44934fc8dbf99d';PREV='baf98c0df400ef96aa83fb587107eb22513c0b97'
OUT=Path('/workspace/recovery-evidence-20261011/ncu-eleventh-reviewed-images');OUT.mkdir(exist_ok=True)
def blob(p,s=SHA):return subprocess.check_output(['git','show',s+':'+p])
def obj(p,s=SHA):
 b=blob(p,s);return json.loads(gzip.decompress(b) if p.endswith('.gz') else b)
def source(p,s=SHA):return obj('sources/ncu/2026-10-11/'+p,s)
def digest(b):return hashlib.sha256(b).hexdigest()
changed=subprocess.check_output(['git','diff','--name-only',PREV,SHA],text=True).splitlines()
packs=[p for p in changed if p.startswith('sources/ncu/') and p.endswith('.gz') and 'host-web-evidence' not in p and 'photo-searches' not in p]
byhash=collections.defaultdict(list);receipts=[];binary=[]
for p in packs:
 for i,r in enumerate(obj(p)):
  rec=r['receipt'];raw=None
  if 'raw_utf8' in r:raw=r['raw_utf8'].encode()
  if 'raw_base64' in r:raw=base64.b64decode(r['raw_base64'])
  if raw is not None:
   assert digest(raw)==rec['sha256'],(p,i)
   byhash[rec['sha256']].append(r)
  receipts.append({'pack':p,'key':r.get('local_evidence_key',r.get('source_id')),'url':rec['url'],'status':rec['status'],'sha256':rec.get('sha256'),'full_body':raw is not None,'bytes':len(raw) if raw else None})
  if raw and 'raw_base64' in r:
   sid=r.get('source_id',rec['sha256'][:20]);ext='.pdf' if raw.startswith(b'%PDF') else '.docx' if raw.startswith(b'PK') else '.binary'
   (OUT/(sid+ext)).write_bytes(raw)
   if ext=='.pdf':
    reader=PdfReader(io.BytesIO(raw));txt='\n'.join(f'PAGE {j+1}\n'+(page.extract_text() or '') for j,page in enumerate(reader.pages))
   elif ext=='.docx':
    import zipfile
    with zipfile.ZipFile(io.BytesIO(raw)) as z:txt=BeautifulSoup(z.read('word/document.xml'),'xml').get_text('\n',strip=True)
   else:txt=''
   (OUT/(sid+'.txt')).write_text(txt);binary.append({'source_id':sid,'url':rec['url'],'sha256':digest(raw),'ext':ext})
loc=source('campus-locations.json')['locations'];old=source('campus-locations.json',PREV)['locations'];assert loc==obj('src/exchange_info/official_data/ncu/campus-locations.json')['locations']
byname={r['school_name']:r for r in loc};oldname={r['school_name']:r for r in old};decisions=[];contexts=[]
for batch in ['seventh','eighth','ninth','tenth','eleventh']:
 for r in source('resume-'+batch+'-location-review.json')['coordinate_decisions']:
  pub=r['published_record'];sid=r['capture_row_id'];assert pub==byname[r['school_name']]
  assert pub['precision']=='representative' and pub['current_exchange_campus_confirmed'] is False
  assert -90<pub['latitude']<90 and -180<pub['longitude']<180
  rec=r['coordinate_receipt'];rawrows=byhash[rec['sha256']];assert rawrows,(sid,'missing full coordinate body')
  raw=rawrows[0]['raw_utf8'];assert str(pub['latitude']) in raw and str(pub['longitude']) in raw,(sid,'coordinate literal absent')
  snippets=[]
  for value in [str(pub['latitude']),str(pub['longitude'])]:
   positions=[m.start() for m in re.finditer(re.escape(value),raw)]
   snippets.extend(raw[max(0,i-650):i+650] for i in positions[:4])
  ids=[]
  for k in ['official_identity_receipt','official_link_receipt']:
   if k in r:ids.append(r[k])
  ids.extend(r.get('supporting_receipts',[]));ids.extend(r.get('additional_receipts',[]))
  texts=[]
  for identity in ids:
   matches=byhash.get(identity['sha256'],[])
   if matches:
    text=matches[0].get('raw_utf8','');soup=BeautifulSoup(text,'html.parser')
    for t in soup(['script','style','noscript']):t.decompose()
    text=soup.get_text('\n',strip=True);f=OUT/(sid+'-'+identity['sha256'][:12]+'.txt');f.write_text(text);texts.append({'url':identity['url'],'file':f.name,'chars':len(text)})
   else:texts.append({'url':identity['url'],'full_archived_body':False,'author_excerpts':r.get('evidence_original_excerpts')})
  contexts.append({'id':sid,'school':r['school_name'],'published':pub,'derivation':r['derivation'],'coordinate_original_contexts':snippets,'identity_texts':texts})
  decisions.append(r)
changedloc=[r['school_name'] for r in loc if r!=oldname.get(r['school_name'])];assert len(changedloc)==len(decisions)==26
assert set(changedloc)=={r['school_name'] for r in decisions}
assets=obj('src/exchange_info/static/assets/ncu-school-images.json')['schools'];oldassets=obj('src/exchange_info/static/assets/ncu-school-images.json',PREV)['schools'];assert len(oldassets)==200 and len(assets)==202
for a in oldassets:assert a in assets
newphotos=[];photo_rows=source('campus-photo-reviews.json')['rows'];hashes=[]
for a in assets:
 b=blob('src/exchange_info'+a['local_path']);h=digest(b);hashes.append(h)
 if a in oldassets:continue
 r=next(x for x in photo_rows if x.get('sha256')==h);assert byhash[r['commons_metadata_sha256']]
 md=json.loads(byhash[r['commons_metadata_sha256']][0]['raw_utf8']);assert md==r['commons_metadata']
 page=next(x for x in md['query']['pages'].values() if x['title']==r['title']);ext=page['imageinfo'][0]['extmetadata']
 assert ext['LicenseShortName']['value']==r['license']==a['license_name'];assert r['page_url']==a['official_page_url']
 im=Image.open(io.BytesIO(b));im.load();(OUT/(r['id']+'.jpg')).write_bytes(b)
 newphotos.append({k:v for k,v in r.items() if k!='commons_metadata'}|{'extmetadata':ext,'dimensions':im.size})
assert len(set(hashes))==199
for p in ['src/exchange_info/official_data/'+s for s in ['cgu','ntpu','ntu','tku']]+['supabase/migrations','uv.lock','.github/workflows','src/exchange_info/static/app.js']:
 assert not subprocess.check_output(['git','diff','--name-only',PREV,SHA,'--',p]).strip(),p
partners=[json.loads(x) for x in blob('src/exchange_info/official_data/ncu/partners.jsonl').splitlines()];oldpartners=[json.loads(x) for x in blob('src/exchange_info/official_data/ncu/partners.jsonl',PREV).splitlines()];assert len(partners)==len(oldpartners)==214
for a,b in zip(oldpartners,partners):
 for k in ['school_name','country','quota','availability','application_status','academic_year','application_round']:assert a.get(k)==b.get(k),(a['school_name'],k)
workflows=[json.loads(x) for x in blob('src/exchange_info/official_data/ncu/application_workflows.jsonl').splitlines()];oldflows=[json.loads(x) for x in blob('src/exchange_info/official_data/ncu/application_workflows.jsonl',PREV).splitlines()];assert len(workflows)==len(oldflows)==214
home_metadata_deltas=[]
for a,b in zip(oldflows,workflows):
 assert a['review_status']==b['review_status']=='pending_review'
 for step in a['steps']:
  if '-home-' in step['rule_id']:
   new=next(x for x in b['steps'] if x['rule_id']==step['rule_id'])
   delta={k:{'before':step.get(k),'after':new.get(k)} for k in step.keys()|new.keys() if step.get(k)!=new.get(k)}
   assert not set(delta)-{'order','checked_at'},(a['school_name'],step['rule_id'],delta)
   if delta:home_metadata_deltas.append({'school':a['school_name'],'rule_id':step['rule_id'],'delta':delta})
report={'source_commit':SHA,'baseline':PREV,'changed_paths':len(changed),'source_receipts':receipts,'original_binary_sources':binary,'all_26_coordinate_contexts':contexts,'old_200_photo_objects_exact':True,'new_photos':newphotos,'unique_photos':199,'locations':214,'representative_only':True,'all214_home_rule_semantics_and_quota_status_unchanged':True,'home_metadata_deltas':home_metadata_deltas,'all214_workflows_pending_review':True,'independent_semantic_and_visual_review':'pending separate read of source contexts and actual photo files'}
(OUT/'source-coordinate-contexts.json').write_text(json.dumps(contexts,ensure_ascii=False,indent=2)+'\n')
(OUT/'photo-provenance.json').write_text(json.dumps(newphotos,ensure_ascii=False,indent=2)+'\n')
(OUT/'binary-sources.json').write_text(json.dumps(binary,ensure_ascii=False,indent=2)+'\n')
Path('/workspace/recovery-evidence-20261011/ncu-eleventh-fixed-input-audit.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'receipts':len(receipts),'full_bodies':sum(x['full_body'] for x in receipts),'coordinates':len(contexts),'new_photos':len(newphotos),'original_binaries':len(binary)},ensure_ascii=False))
