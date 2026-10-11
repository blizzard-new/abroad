"""Independently audit PR9's fixed third batch without moving the active worktree."""
import hashlib,io,json,re,subprocess,zipfile
from pathlib import Path
from exchange_info.life_context import LifeResearchSnapshot, reviewed_life_snapshot
sha='ed7479073df36deb8fc0393e86fedb102e1cf2b7';previous='b6607a0ee5d01e23878950d556f9540aa25aeaf2'
def blob(path,head=sha):return subprocess.check_output(['git','show',head+':'+path])
def obj(path,head=sha):return json.loads(blob(path,head))
base='sources/ntu/'
manifest=obj(base+'reviewed-source-bodies-current-manifest.json');snapshot=obj(base+'completion-2026-10-11.json')
entries={x['source_id']:x for x in manifest['entries']};assert len(entries)==345 and len(manifest['archive_files'])==12
prior=obj(base+'reviewed-source-bodies-current-manifest.json',previous);assert prior['source_count']==217
assert all(entries[x['source_id']]==x for x in prior['entries'])
normal=lambda x:re.sub(r'\s+',' ',x).strip()
checked=set();quotes=set();page_quotes=0;archives=[]
reviews=snapshot['public_source_reviews'];assert len(reviews)==268
home=obj(base+'home-selection-current-2026-10-11.json')
for part in manifest['archive_files']:
 raw=blob(base+part['archive_file']);assert hashlib.sha256(raw).hexdigest()==part['sha256'];assert len(raw)==part['size_bytes']
 count=0
 with zipfile.ZipFile(io.BytesIO(raw)) as archive:
  for sid,e in entries.items():
   if e['archive_file']!=part['archive_file']:continue
   body=archive.read(e['archive_body_path']);assert len(body)==e['size_bytes'] and hashlib.sha256(body).hexdigest()==e['sha256'];checked.add(sid);count+=1
   if sid in reviews:
    r=reviews[sid];quote=normal(r['original_quote']);assert e['sha256']==r['sha256'] and len(quote.split())<=25
    assert quote in normal(archive.read('extractions/'+sid+'.txt').decode())
    if page:=r.get('quote_pdf_page'):
     pages=json.loads(archive.read('extractions/'+sid+'.pages.json'));assert quote in normal(next(x['text'] for x in pages if x['page']==page));page_quotes+=1
    quotes.add(sid)
   if sid==home['source_id']:
    pages=json.loads(archive.read('extractions/'+sid+'.pages.json'));assert e['sha256']==home['sha256'];assert normal(home['original_quote']) in normal(next(x['text'] for x in pages if x['page']==home['quote_pdf_page']))
 archives.append({'file':part['archive_file'],'bodies':count,'sha256':part['sha256']})
assert len(checked)==345 and len(quotes)==268
manual=obj(base+'semantic-review-current-2026-10-11.json');assert len(manual)==178
for row in manual:
 for source in row['sources']:assert entries[source['source_id']]['sha256']==source['sha256']
path='src/exchange_info/official_data/ntu/partners.jsonl';before=[json.loads(x) for x in blob(path,previous).splitlines() if x.strip()];after=[json.loads(x) for x in blob(path).splitlines() if x.strip()]
assert len(before)==len(after)==288
fields=('school_name','country','quota','eligibility','application_deadline','availability_status','source_url')
assert all({k:a.get(k) for k in fields}=={k:b.get(k) for k in fields} for a,b in zip(before,after))
for school in ('cgu','ntpu','ntu'):
 p=f'src/exchange_info/official_data/{school}/application_workflows.jsonl';assert blob(p)==blob(p,previous)
photos='src/exchange_info/static/assets/school-images.json';a=obj(photos);b=obj(photos,previous);a.pop('updated_at');b.pop('updated_at');assert a==b
life=[reviewed_life_snapshot(LifeResearchSnapshot.model_validate_json(line)) for line in blob('src/exchange_info/official_data/ntu/student_life.jsonl').splitlines() if line.strip()]
assert len(life)==288 and sum(len(x.evidence) for x in life)==1913 and sum(bool(x.evidence) for x in life)==272
report={'source_commit':sha,'compared_to':previous,'current_bodies':len(checked),'current_archive_parts':12,'reviewed_citations':len(quotes),'quote_pages_checked':page_quotes,'home_pdf_citation_checked':True,'manual_semantic_rows':178,'stage2_217_entries_unchanged':True,'protected_partner_fields':list(fields),'protected_partner_rows':288,'original_three_school_workflows_unchanged':True,'photo_records_unchanged_except_timestamp':True,'life_schools_with_any_evidence':272,'life_schools_without_any_evidence':16,'life_evidence_rows':1913,'independent_host_life_gap':'Author ledger:38 schools; separate from the16 with no evidence. No completeness promotion.','archives':archives}
Path('/workspace/recovery-evidence-20261011/ntu-third-fixed-input-audit.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(json.dumps(report,ensure_ascii=False,indent=2))
