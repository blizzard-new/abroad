from pathlib import Path
import subprocess,json,gzip,hashlib,base64,io,zipfile,collections
from bs4 import BeautifulSoup
from pypdf import PdfReader
SHA='13a4afdc0e99cd5f9b4c66bca5bc426d68bdfd4b';OLD='084f500f091838afe09ddf4f716bffd5ace9b906'
OUT=Path('/workspace/recovery-evidence-20261011/ncu-fourteenth-reviewed-images');OUT.mkdir(exist_ok=True)
def blob(p,s=SHA):return subprocess.check_output(['git','show',s+':'+p])
def obj(p,s=SHA):
 b=blob(p,s);return json.loads(gzip.decompress(b) if p.endswith('.gz') else b)
def digest(b):return hashlib.sha256(b).hexdigest()
base='sources/ncu/2026-10-11/';prod='src/exchange_info/official_data/ncu/';doc='docs/data/ncu-completion-20261011/resume/fourteenth/'
sources={s['id']:s for s in obj(prod+'source-evidence.json.gz')};olds={s['id']:s for s in obj(prod+'source-evidence.json.gz',OLD)}
assert len(sources)==len(olds)+45
rows=obj(base+'resume-fourteenth-original-responses.json.gz');manifest=obj(doc+'reading-manifest.json');assert len(rows)==len(manifest['new_source_ids'])==45
(OUT/'reading-manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
records=[];rendered=[];pdfpages=0
for r in rows:
 sid=r['source_id'];raw=base64.b64decode(r['raw_base64']);rec=r['receipt'];source=sources[sid]
 assert digest(raw)==rec['sha256']==source['sha256'] and not source.get('current_116_applicability_verified',False)
 record={'id':sid,'url':rec['url'],'sha256':digest(raw),'bytes':len(raw),'pages':0}
 if raw.startswith(b'%PDF'):
  pages=[{'page':i+1,'text':p.extract_text() or ''}for i,p in enumerate(PdfReader(io.BytesIO(raw)).pages)]
  (OUT/(sid+'.pages.json')).write_text(json.dumps(pages,ensure_ascii=False,indent=2)+'\n');text='\n'.join(f"PAGE {p['page']}\n{p['text']}" for p in pages);record['pages']=len(pages);pdfpages+=len(pages)
  (OUT/(sid+'.pdf')).write_bytes(raw)
 elif raw.startswith(b'PK'):
  with zipfile.ZipFile(io.BytesIO(raw)) as z:
   text='\n'.join(n+'\n'+BeautifulSoup(z.read(n),'xml').get_text('\n',strip=True) for n in z.namelist() if n.endswith('.xml') and (n.startswith('word/') or n.startswith('xl/')))
  (OUT/(sid+'.office')).write_bytes(raw)
 else:
  soup=BeautifulSoup(raw,'html.parser')
  for n in soup(['script','style','noscript']):n.decompose()
  text=soup.get_text('\n',strip=True)
 (OUT/(sid+'.txt')).write_text(text)
 for page in source.get('visual_review',{}).get('rendered_pages',[]):
  data=blob(page['artifact']);assert digest(data)==page['render_sha256'];rendered.append({'source':sid,**page})
 records.append(record)
assert len(rendered)==39
old=obj(base+'reviewed-host-records.json',OLD);new=obj(base+'reviewed-host-records.json');assert set(new)-set(old)=={'ncu-147','ncu-155','ncu-197'};assert all(new[k]==v for k,v in old.items())
added={k:v for k,v in new.items() if k not in old};(OUT/'new-host-records.json').write_text(json.dumps(added,ensure_ascii=False,indent=2)+'\n')
conditions=obj(base+'document-conditions.json');oldc=obj(base+'document-conditions.json',OLD);assert all(c in conditions for c in oldc);newc=[c for c in conditions if c not in oldc];assert len(newc)==33
for c in newc:
 assert c['requires_institutional_confirmation'] is True
 for source in c['source_versions']:assert sources[source['source_id']]['sha256']==source['sha256']
(OUT/'new-document-conditions.json').write_text(json.dumps(newc,ensure_ascii=False,indent=2)+'\n')
for path in ['supabase/migrations','.github/workflows','uv.lock','src/exchange_info/static','src/exchange_info/official_data/cgu','src/exchange_info/official_data/ntu','src/exchange_info/official_data/ntpu','src/exchange_info/official_data/ccu','src/exchange_info/official_data/tku',base+'campus-locations.json',base+'campus-photo-reviews.json']:
 assert not subprocess.check_output(['git','diff','--name-only',OLD,SHA,'--',path]).strip(),path
partners=[json.loads(x)for x in blob(prod+'partners.jsonl').splitlines()];oldp=[json.loads(x)for x in blob(prod+'partners.jsonl',OLD).splitlines()];assert len(partners)==len(oldp)==214
for a,b in zip(oldp,partners):
 for key in ['school_name','country','quota','availability_status','academic_year','application_round']:assert a.get(key)==b.get(key)
 assert b.get('quota') is None and b['availability_status']=='agreement_only'
report={'source_sha':SHA,'compared_to':OLD,'receipts':records,'new_independent_sources':45,'all_pdf_pages_reextracted':pdfpages,'rendered_page_hash_receipts_checked':rendered,'new_host_records':list(added),'all_prior_host_records_unchanged':True,'new_document_conditions':len(newc),'photos_coordinates_sql_frontend_unchanged':True,'all214_quota_unknown_agreement_only':True,'semantic_review':'Separate bounded original-context and actual image review pending; authors full reading claim not inherited.'}
Path('/workspace/recovery-evidence-20261011/ncu-fourteenth-fixed-input-audit.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items()if k not in ['receipts','rendered_page_hash_receipts_checked']},ensure_ascii=False))
