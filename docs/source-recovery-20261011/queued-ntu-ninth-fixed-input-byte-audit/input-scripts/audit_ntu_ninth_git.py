"""Read-only independent byte, quotation, version and evidence audit of fixed NTU input."""
import hashlib,io,json,re,subprocess,zipfile
from pathlib import Path
from pypdf import PdfReader
sha='23757a06778f7569716a19987dd1d39effce13f2';previous='c7357f974faaec8e60ef19698d4d21633c322dc8';base='sources/ntu/'
out=Path('/workspace/recovery-evidence-20261011/ntu-ninth-reviewed-images');out.mkdir(exist_ok=True)
def blob(p,h=sha):return subprocess.check_output(['git','show',h+':'+p])
def obj(p,h=sha):return json.loads(blob(p,h))
norm=lambda s:re.sub(r'\s+',' ',s).strip()
manifest=obj(base+'reviewed-source-bodies-current-manifest.json');snapshot=obj(base+'completion-2026-10-11.json');old=obj(base+'completion-2026-10-11.json',previous)
entries={(x['source_id'],x['sha256']):x for x in manifest['entries']};prior=obj(base+'reviewed-source-bodies-current-manifest.json',previous)
assert len(entries)==1389 and len({k[0] for k in entries})==1388 and len(manifest['archive_files'])==44
assert all(entries[(x['source_id'],x['sha256'])]==x for x in prior['entries'])
reviews=snapshot['public_source_reviews'];assert len(reviews)==648
old_obs={x['observation_id'] for row in old['schools'] for x in row['observations']}
added=[dict(portal_id=s['portal_id'],school_name=s['school_name'],**o) for s in snapshot['schools'] for o in s['observations'] if o['observation_id'] not in old_obs]
(out/'new-observations.json').write_text(json.dumps(added,ensure_ascii=False,indent=2)+'\n')
new_sids={o['source_id'] for o in added};old_reviews=old['public_source_reviews'];new_sids|=set(reviews)-set(old_reviews)
conclusions=[c for school in snapshot['schools'] for c in school.get('field_review_conclusions',[])]
assert len(conclusions)==429 and sum(bool(s.get('field_review_conclusions')) for s in snapshot['schools'])==121
for conclusion in conclusions:
 assert conclusion['full_current_cycle_requirement_verified'] is False and conclusion['bounded_field_conclusion_complete'] is True
 for source in conclusion['sources']:
  entry=entries[(source['source_id'],source['sha256'])]
  assert source['url']==entry['url'] and source['checked_at']==entry['checked_at']
  assert source['field_fitness_note_zh']
  new_sids.add(source['source_id'])
(out/'field-conclusions.json').write_text(json.dumps(conclusions,ensure_ascii=False,indent=2)+'\n')
critical=('puc-rio.br','utexas.edu','unc.edu','uncc.edu','uconn.edu','hku.hk','uvic.ca','montana.edu','kyungpook','knu.ac.kr','sc.edu','hufs.ac.kr')
checked=set();quoted=set();archives=[];fallbacks=[];visual=[];copied=[]
home=obj(base+'home-selection-current-2026-10-11.json')
paths=subprocess.check_output(['git','ls-tree','-r','--name-only',sha,'docs/ntu-completion-20261011'],text=True).splitlines()
for part in manifest['archive_files']:
 raw=blob(base+part['archive_file']);assert len(raw)==part['size_bytes'] and hashlib.sha256(raw).hexdigest()==part['sha256'];count=0
 with zipfile.ZipFile(io.BytesIO(raw)) as z:
  for key,e in entries.items():
   if e['archive_file']!=part['archive_file']:continue
   sid,rawhash=key;body=z.read(e['archive_body_path']);assert len(body)==e['size_bytes'] and hashlib.sha256(body).hexdigest()==rawhash;checked.add(key);count+=1
   txtpath='extractions/'+sid+'.txt';text=z.read(txtpath).decode() if txtpath in z.namelist() else ''
   if sid in new_sids:
    (out/(sid+'-'+rawhash[:8]+'.txt')).write_text(text);copied.append(dict(source_id=sid,sha256=rawhash,url=e['url'],text_file=sid+'-'+rawhash[:8]+'.txt',raw_pdf_pages=None))
    if any(domain in e['url'] for domain in critical):
     ext='.pdf' if body.startswith(b'%PDF') else '.docx' if body.startswith(b'PK') and 'docx' in e['url'].lower() else '.body'
     (out/(sid+'-'+rawhash[:8]+ext)).write_bytes(body)
     if ext=='.pdf':
      p=PdfReader(io.BytesIO(body));pages=[{'page':i+1,'text':page.extract_text() or ''} for i,page in enumerate(p.pages)];(out/(sid+'-'+rawhash[:8]+'.pages.json')).write_text(json.dumps(pages,ensure_ascii=False,indent=2));copied[-1]['raw_pdf_pages']=len(pages)
   if sid in reviews and reviews[sid]['sha256']==rawhash:
    r=reviews[sid];q=norm(r['original_quote']);assert len(q.split())<=25 and q in norm(text),(sid,'quote')
    if pg:=r.get('quote_pdf_page'):
     if r.get('quote_verification_method')=='manual_visual_rendered_pdf_with_transcription':
      matches=[p for p in paths if p.endswith('/evidence/'+r['visual_evidence_reference'])];assert len(matches)==1
      p=matches[0];ev=obj(p);assert ev['source_id']==sid and ev['raw_pdf_sha256']==rawhash and ev['quote_pdf_page']==pg
      assert norm(ev['manually_transcribed_quote'])==q and hashlib.sha256((ev['manually_transcribed_quote']+'\n').encode()).hexdigest()==ev['transcription_sha256']==r['visual_quote_transcription_sha256']
      parent=p.rsplit('/',1)[0];m={x['file']:x for x in obj(parent+'/visual-evidence-manifest.json')}
      for fn in ev['evidence_files']:
       data=blob(parent+'/'+fn);assert len(data)==m[fn]['size_bytes'] and hashlib.sha256(data).hexdigest()==m[fn]['sha256'];(out/Path(fn).name).write_bytes(data)
      (out/Path(p).name).write_text(json.dumps(ev,ensure_ascii=False,indent=2));visual.append(dict(source_id=sid,images=len(ev['evidence_files']),independent_visual_review='pending'))
     else:
      pagespath='extractions/'+sid+'.pages.json'
      if pagespath in z.namelist():textpage=next(p['text'] for p in json.loads(z.read(pagespath)) if p['page']==pg)
      else:textpage=PdfReader(io.BytesIO(body)).pages[pg-1].extract_text() or '';fallbacks.append({'source_id':sid,'page':pg})
      assert q in norm(textpage),(sid,pg)
    quoted.add(sid)
   if sid==home['source_id'] and rawhash==home['sha256']:
    p=PdfReader(io.BytesIO(body));assert norm(home['original_quote']) in norm(p.pages[home['quote_pdf_page']-1].extract_text());homeok=True
 archives.append(dict(file=part['archive_file'],bodies=count,sha256=part['sha256']))
assert len(checked)==1389 and len(quoted)==648 and homeok
manual=obj(base+'semantic-review-current-2026-10-11.json');assert len(manual)==1009
for row in manual:
 for src in row['sources']:assert (src['source_id'],src['sha256']) in entries
historical=obj(base+'reviewed-source-bodies-stage1-manifest.json');assert len(historical)==59
with zipfile.ZipFile(io.BytesIO(blob(base+'reviewed-source-bodies-stage1-2026-10-11.zip'))) as z:
 for e in historical:assert hashlib.sha256(z.read(e['archive_path'])).hexdigest()==e['sha256']
(out/'extracted-review-index.json').write_text(json.dumps(copied,ensure_ascii=False,indent=2)+'\n')
report=dict(source_commit=sha,compared_to=previous,current_bodies=1389,distinct_source_ids=1388,archive_parts=44,prior1228body_versions_exactly_preserved=True,reviewed_citations=648,pdf_page_reextractions=fallbacks,manual_visual_receipts=visual,manual_semantic_source_references=1009,historical59_body_hashes_checked=True,home_pdf_quote_checked=True,new_observations=len(added),new_source_texts_preserved=len(copied),archives=archives,semantic_acceptance='Byte/quotation verification only; independent original-context review remains separate.')
Path('/workspace/recovery-evidence-20261011/ntu-ninth-fixed-input-audit.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(json.dumps(report,ensure_ascii=False,indent=2))
