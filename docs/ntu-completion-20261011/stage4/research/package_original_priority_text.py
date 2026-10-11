from pathlib import Path
import json,hashlib,zipfile
R=Path('/workspace/abroad-ntu-completion-20261011');H=Path(__file__).parent;q=json.loads((H/'priority-source-roster.json').read_text());data={};joins=[]
for pid,school in q.items():
 for sid,lead in school['sources'].items():
  p=Path(lead['path']);d=json.loads(p.read_text());t=d.get('text')
  if t is None:t=p.with_suffix('.txt').read_text()
  raw=Path(d.get('local_file','/missing'))
  if not raw.exists():raw=next((f for ext in ['.html','.pdf','.image'] if (f:=p.with_suffix(ext)).is_file()),None)
  assert raw and hashlib.sha256(raw.read_bytes()).hexdigest()==d['sha256']
  key=sid,d['sha256'];data[key]=(t,d);joins.append({'portal_id':pid,'school_name':school['name'],'source_id':sid,'raw_body_sha256':d['sha256'],'fields':[f for f,sids in school['fields'].items() if sid in sids]})
p=R/'sources/ntu/priority-original-cached-texts-2026-10-11.zip';entries=[]
with zipfile.ZipFile(p,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
 for (sid,rawsha),(t,d) in sorted(data.items()):
  path='texts/'+sid+'-'+rawsha[:12]+'.txt';z.writestr(path,t)
  e={k:d.get(k) for k in ['source_id','url','final_url','title','checked_at','http_status','document_type','pdf_page_count']};e.update(raw_body_sha256=rawsha,extracted_text_sha256=hashlib.sha256(t.encode()).hexdigest(),text_chars=len(t),archive_text_path=path,role='Original cached priority discovery candidate; not proof of a verified field or current-cycle publication')
  entries.append(e)
  if d.get('pages'):z.writestr(path+'.pages.json',json.dumps(d['pages'],ensure_ascii=False))
 manifest={'original_priority_field_rows':501,'school_count':117,'source_id_versions':len(entries),'distinct_source_ids':len({sid for sid,sha in data}),'distinct_raw_body_hashes':len({sha for sid,sha in data}),'raw_bytes_matched_locally_before_packaging':True,'raw_bodies_included':False,'scope_note':'Portable extracted text and exact source version metadata for continued reading. Raw PDF/HTML for reviewed sources is separately stored in reviewed-body manifest; unreviewed raw bodies are not asserted archived here. Scans may have empty or incomplete text and still require visual/source review.','entries':entries,'school_source_field_joins':joins}
 assert manifest['distinct_raw_body_hashes']==890
 z.writestr('manifest.json',json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
(R/'sources/ntu/priority-original-cached-texts-manifest.json').write_text(json.dumps({k:v for k,v in manifest.items() if k not in ['entries','school_source_field_joins']}|{'archive_file':p.name,'size_bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()},ensure_ascii=False,indent=2)+'\n')
print(json.dumps({k:v for k,v in manifest.items() if k not in ['entries','school_source_field_joins']},ensure_ascii=False));print('zipbytes',p.stat().st_size)
