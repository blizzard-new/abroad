from research_curator import Curator,ROOT
from pathlib import Path
import json,gzip,zipfile,hashlib,shutil
REPO=Path('/workspace/abroad-ntu-completion-20261011');sp=REPO/'sources/ntu';current=sp/'reviewed-source-bodies-current-manifest.json';frozen=ROOT/'prior-511-manifest.json'
assert frozen.exists()
m=json.loads(frozen.read_text());entries={(e['source_id'],e['sha256']):e for e in m['entries']};c=Curator();wanted={(sid,r['sha256']) for sid,r in c.sources.items()};reviews=json.loads((sp/'semantic-review-current-2026-10-11.json').read_text());ledger=json.loads((ROOT/'full-body-field-review-ledger.json').read_text())
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
for i,part in enumerate(parts,19):
 name=f'reviewed-source-bodies-stage7-2026-10-11-part-{i:02d}.zip';path=sp/name
 with zipfile.ZipFile(path,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
  pe=[]
  for sid,d,raw in part:
   arc='bodies/'+sid+'-'+d['sha256'][:12]+raw.suffix;z.write(raw,arc);z.writestr('extractions/'+sid+'.txt',d.get('text',''))
   if d.get('pages'):z.writestr('extractions/'+sid+'.pages.json',json.dumps(d['pages'],ensure_ascii=False))
   clean={k:v for k,v in d.items() if k not in ['_folder','_manual_visual_quote_file','text','pages','paragraphs','links','local_file','field_candidates','error_preview']};z.writestr('receipts/'+sid+'.json',json.dumps(clean,ensure_ascii=False,indent=2)+'\n')
   e=dict(source_id=sid,url=d['url'],checked_at=d['checked_at'],sha256=hashlib.sha256(raw.read_bytes()).hexdigest(),size_bytes=raw.stat().st_size,archive_body_path=arc,archive_file=name,role='stage7_adopted_or_complete_body_semantic_review');pe.append(e);entries[(sid,e['sha256'])]=e
  z.writestr('manifest.json',json.dumps(pe,ensure_ascii=False,indent=2)+'\n')
 m['archive_files'].append(dict(archive_file=name,sha256=hashlib.sha256(path.read_bytes()).hexdigest(),size_bytes=path.stat().st_size,source_count=len(part)))
m.update(entries=list(entries.values()),source_count=len(entries),distinct_source_id_count=len({sid for sid,sha in entries}),same_url_versions_preserved=True,original_body_total_bytes=sum(e['size_bytes'] for e in entries.values()),citation_body_join_count=len(c.sources),manual_semantic_rows=len(reviews),stage6_unchanged_archive_parts=18)
current.write_text(json.dumps(m,ensure_ascii=False,indent=2)+'\n')
# Versioned receipts remain distinct from readable-field keywords; their body evidence is above.
a=json.loads(gzip.decompress((sp/'host-access-current-2026-10-11.json.gz').read_bytes()));rows={x['portal_id']:x for x in a['schools']};receipts=[]
for p in sorted((ROOT/'sources').glob('*.json')):
 d=json.loads(p.read_text())
 if isinstance(d,dict) and d.get('url'):receipts.append({k:v for k,v in d.items() if k not in ['text','pages','paragraphs','links','local_file','error_preview']})
bykey={(r.get('source_id'),r.get('sha256'),r.get('checked_at')):r for r in receipts}
for receipt_file in sorted(ROOT.glob('followups*-receipts.json')):
 for r in json.loads(receipt_file.read_text()):
  s=bykey.get((r['source_id'],r.get('sha256'),r['checked_at']))
  if not s:continue
  q=rows[r['portal_id']];key=(r['source_id'],r.get('sha256'),r['checked_at']);oldkeys={(x['source'].get('source_id'),x['source'].get('sha256'),x['source'].get('checked_at')) for x in q['sources']}
  if key not in oldkeys:q['sources'].append({'source':s,'field_candidate_counts':{},'stage7_full_body_review_separate':True})
a['stage7_source_receipts']=receipts;a['stage7_scope']='Manual full cached body and public followup reading; fixed501 original priority school-field rows/117schools/890unique body hashes. Followups do not increase that denominator. Scanned PDFs rendered and visually read. No current-cycle complete field claimed. No auth/site-block bypass.'
old={json.dumps(r,sort_keys=True) for r in a['robots_receipts']}
for line in (ROOT/'robots-receipt-history.jsonl').read_text().splitlines():
 if line.strip() and json.dumps((r:=json.loads(line)),sort_keys=True) not in old:a['robots_receipts'].append(r);old.add(json.dumps(r,sort_keys=True))
a['counts']['stage7_unique_source_receipts']=len(receipts);a['counts']['all_school_joined_attempt_records']=sum(len(r['sources']) for r in rows.values());(sp/'host-access-current-2026-10-11.json.gz').write_bytes(gzip.compress(json.dumps(a,ensure_ascii=False).encode(),mtime=0))
for src,dst in [('full-body-field-review-ledger.json','full-body-review-current-2026-10-11.json'),('priority-review-progress.json','priority-review-progress-current-2026-10-11.json')]:shutil.copyfile(ROOT/src,sp/dst)
print('body count',len(entries),'added',len(new),'new parts',len(parts),'citations',len(c.sources),'receipts',len(receipts))
