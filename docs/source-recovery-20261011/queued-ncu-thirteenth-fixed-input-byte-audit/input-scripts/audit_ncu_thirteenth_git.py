from pathlib import Path
import subprocess,json,gzip,hashlib,base64,io,zipfile
from bs4 import BeautifulSoup
from pypdf import PdfReader
SHA='084f500f091838afe09ddf4f716bffd5ace9b906';OLD='a2df55b16f72455f7154d7afff44934fc8dbf99d'
OUT=Path('/workspace/recovery-evidence-20261011/ncu-thirteenth-reviewed-images');OUT.mkdir(exist_ok=True)
def blob(p,s=SHA):return subprocess.check_output(['git','show',s+':'+p])
def obj(p,s=SHA):
 b=blob(p,s);return json.loads(gzip.decompress(b) if p.endswith('.gz') else b)
def digest(b):return hashlib.sha256(b).hexdigest()
base='sources/ncu/2026-10-11/';prod='src/exchange_info/official_data/ncu/';doc='docs/data/ncu-completion-20261011/resume/'
sources={s['id']:s for s in obj(prod+'source-evidence.json.gz')};old_sources={s['id']:s for s in obj(prod+'source-evidence.json.gz',OLD)}
assert len(sources)==len(old_sources)+13
records=[];pdfpages=0;rendered=0
for part in ['twelfth','thirteenth']:
 rows=obj(base+'resume-'+part+'-original-responses.json.gz');manifest=obj(doc+part+'/reading-manifest.json')
 (OUT/(part+'-reading-manifest.json')).write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
 for i,r in enumerate(rows):
  raw=base64.b64decode(r['raw_base64']);rec=r['receipt'];expected=r.get('member_sha256') or rec['sha256'];assert digest(raw)==expected,(part,i)
  sid=r.get('source_id',r.get('capture_id','container-'+str(i)))
  record={'part':part,'id':sid,'url':rec['url'],'sha256':expected,'bytes':len(raw),'pages':0}
  if raw.startswith(b'%PDF'):
   reader=PdfReader(io.BytesIO(raw));pages=[{'page':j+1,'text':p.extract_text() or ''} for j,p in enumerate(reader.pages)]
   (OUT/(sid+'.pages.json')).write_text(json.dumps(pages,ensure_ascii=False,indent=2)+'\n');text='\n'.join(f"PAGE {p['page']}\n{p['text']}" for p in pages)
   record['pages']=len(pages)
   if part=='thirteenth':pdfpages+=len(pages)
   (OUT/(sid+'.pdf')).write_bytes(raw)
  elif raw.startswith(b'PK'):
   with zipfile.ZipFile(io.BytesIO(raw)) as z:
    text='\n'.join(n+'\n'+BeautifulSoup(z.read(n),'xml').get_text('\n',strip=True) for n in z.namelist() if n.endswith('.xml') and (n.startswith('word/') or n.startswith('xl/')))
   (OUT/(sid+'.zip' if r.get('container') else sid+'.office')).write_bytes(raw)
  else:
   soup=BeautifulSoup(raw,'html.parser')
   for n in soup(['script','style','noscript']):n.decompose()
   text=soup.get_text('\n',strip=True)
  (OUT/(sid+'.txt')).write_text(text)
  if part=='thirteenth':
   s=sources[sid];assert s['sha256']==digest(raw) and not s.get('current_116_applicability_verified',False)
   for page in s.get('visual_review',{}).get('rendered_pages',[]):
    b=blob(page['artifact']);assert digest(b)==page['render_sha256'];rendered+=1
  records.append(record)
 if part=='twelfth':
  container=next(r for r in rows if r.get('container'));z=zipfile.ZipFile(io.BytesIO(base64.b64decode(container['raw_base64'])))
  captures={r['capture_id']:r for r in rows if r.get('capture_id')}
  for c in manifest['existing_nufs_packet_revalidation']:
   raw=base64.b64decode(captures[c['capture_id']]['raw_base64']);assert digest(raw)==c['sha256']
   if c['source_container']:assert z.read(c['source_container']['member'])==raw
   else:assert sources[c['same_content_as_prior_source']]['sha256']==digest(raw)
   for page in (c.get('visual_review') or {}).get('rendered_pages',[]):assert digest(blob(page['artifact']))==page['render_sha256']
assert pdfpages==rendered==66
old=obj(base+'reviewed-host-records.json',OLD);new=obj(base+'reviewed-host-records.json');assert set(new)-set(old)=={'ncu-136','ncu-151'}
assert all(new[k]==v for k,v in old.items());assert 'ncu-018' not in new and 'ncu-130' not in new
added={k:v for k,v in new.items() if k not in old};(OUT/'new-host-records.json').write_text(json.dumps(added,ensure_ascii=False,indent=2)+'\n')
conditions=obj(base+'document-conditions.json');oldc=obj(base+'document-conditions.json',OLD);assert all(c in conditions for c in oldc)
newc=[c for c in conditions if c not in oldc];assert len(newc)==25
for c in newc:
 assert c['requires_institutional_confirmation'] is True
 for source in c['source_versions']:assert sources[source['source_id']]['sha256']==source['sha256']
(OUT/'new-document-conditions.json').write_text(json.dumps(newc,ensure_ascii=False,indent=2)+'\n')
for path in ['supabase/migrations','.github/workflows','uv.lock','src/exchange_info/static','src/exchange_info/official_data/cgu','src/exchange_info/official_data/ntu','src/exchange_info/official_data/ntpu','src/exchange_info/official_data/ccu','src/exchange_info/official_data/tku',base+'campus-locations.json',base+'campus-photo-reviews.json']:
 assert not subprocess.check_output(['git','diff','--name-only',OLD,SHA,'--',path]).strip(),path
partners=[json.loads(x)for x in blob(prod+'partners.jsonl').splitlines()];oldp=[json.loads(x)for x in blob(prod+'partners.jsonl',OLD).splitlines()]
assert len(partners)==len(oldp)==214
for a,b in zip(oldp,partners):
 for key in ['school_name','country','quota','availability_status','academic_year','application_round']:assert a.get(key)==b.get(key)
 assert b['quota'] is None and b['availability_status']=='agreement_only'
report={'source_sha':SHA,'compared_to':OLD,'receipts':records,'new_independent_sources':13,'new_pdf_pages_hash_and_reextraction':pdfpages,'new_visual_page_receipts_hash_checked':rendered,'new_host_records':list(added),'all_prior_host_records_unchanged':True,'new_document_conditions':len(newc),'photos_coordinates_sql_workflows_shared_runtime_code_unchanged':True,'all214_quota_unknown_agreement_only':True,'semantic_review':'Original contexts and selected rendered pages require separate independent review; author full-read claim not inherited.'}
Path('/workspace/recovery-evidence-20261011/ncu-thirteenth-fixed-input-audit.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items()if k!='receipts'},ensure_ascii=False))
