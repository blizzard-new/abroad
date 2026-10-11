from field_worker import Worker,H
ROOT=H
from pathlib import Path
import json,gzip,zipfile,hashlib,shutil
REPO=Path('/workspace/abroad-ntu-completion-20261011');sp=REPO/'sources/ntu';current=sp/'reviewed-source-bodies-current-manifest.json';frozen=ROOT/'base-body-manifest1228.json'
assert frozen.exists()
m=json.loads(frozen.read_text());entries={(e['source_id'],e['sha256']):e for e in m['entries']};c=Worker('root');c.sources=json.loads((sp/'completion-2026-10-11.json').read_text())['public_source_reviews'];wanted={(sid,r['sha256']) for sid,r in c.sources.items()};reviews=json.loads((sp/'semantic-review-current-2026-10-11.json').read_text());ledger=json.loads((sp/'full-body-review-current-2026-10-11.json').read_text())
for r in reviews:
 for s in r['sources']:wanted.add((s['source_id'],s['sha256']))
for r in ledger:wanted.add((r['source_id'],r['body_sha256']))
new=[]
for sid,sha in sorted(wanted):
 if (sid,sha) in entries:continue
 d=c.read_source(sid);folder=d['_folder'];raw=Path(d.get('local_file','/missing'))
 if not raw.is_file():raw=next((p for ext in ['.html','.pdf','.image'] if (p:=folder/(sid+ext)).is_file()),None)
 assert raw and hashlib.sha256(raw.read_bytes()).hexdigest()==sha,(sid,raw)
 new.append((sid,d,raw))
parts=[];part=[];size=0
for item in new:
 if part and size+item[2].stat().st_size>12000000:parts.append(part);part=[];size=0
 part.append(item);size+=item[2].stat().st_size
if part:parts.append(part)
for i,part in enumerate(parts,43):
 name=f'reviewed-source-bodies-stage9-2026-10-11-part-{i:02d}.zip';path=sp/name
 with zipfile.ZipFile(path,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
  pe=[]
  for sid,d,raw in part:
   arc='bodies/'+sid+'-'+d['sha256'][:12]+raw.suffix;z.write(raw,arc);z.writestr('extractions/'+sid+'.txt',d.get('text',''))
   if d.get('pages'):z.writestr('extractions/'+sid+'.pages.json',json.dumps(d['pages'],ensure_ascii=False))
   clean={k:v for k,v in d.items() if k not in ['_folder','_manual_visual_quote_file','text','pages','paragraphs','links','local_file','field_candidates','error_preview']};z.writestr('receipts/'+sid+'.json',json.dumps(clean,ensure_ascii=False,indent=2)+'\n')
   e=dict(source_id=sid,url=d['url'],checked_at=d['checked_at'],sha256=hashlib.sha256(raw.read_bytes()).hexdigest(),size_bytes=raw.stat().st_size,archive_body_path=arc,archive_file=name,role='stage9_adopted_or_terminal_field_fitness_review');pe.append(e);entries[(sid,e['sha256'])]=e
  z.writestr('manifest.json',json.dumps(pe,ensure_ascii=False,indent=2)+'\n')
 m['archive_files'].append(dict(archive_file=name,sha256=hashlib.sha256(path.read_bytes()).hexdigest(),size_bytes=path.stat().st_size,source_count=len(part)))
m.update(entries=list(entries.values()),source_count=len(entries),distinct_source_id_count=len({sid for sid,sha in entries}),same_url_versions_preserved=True,original_body_total_bytes=sum(e['size_bytes'] for e in entries.values()),citation_body_join_count=len(c.sources),manual_semantic_rows=len(reviews),prior_unchanged_archive_parts=42)
current.write_text(json.dumps(m,ensure_ascii=False,indent=2)+'\n')

assert all(e in m['entries'] for e in json.loads(frozen.read_text())['entries'])
assert all(p in m['archive_files'] for p in json.loads(frozen.read_text())['archive_files'])
print('body versions',len(entries),'added',len(new),'parts',len(m['archive_files']))
