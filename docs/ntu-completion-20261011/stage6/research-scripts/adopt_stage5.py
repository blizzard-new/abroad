from pathlib import Path
import json,hashlib,gzip,zipfile,shutil,datetime
R=Path('/workspace/abroad-ntu-completion-20261011');S=R/'sources/ntu';H=Path(__file__).parent;D=R/'docs/ntu-completion-20261011/stage6';B=D.parent/'stage5';P=H.parent/'stage5'
read=lambda p:json.loads(p.read_text())
write=lambda p,x:p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(S/'completion-2026-10-11.json')=='45a9d975e8beae64bad8d75de4069e76abbec493e700563eb7d3ae13acb87d8d'
shutil.copyfile(S/'completion-2026-10-11.json',H/'prior-608.json');shutil.copyfile(S/'reviewed-source-bodies-current-manifest.json',H/'prior-478-manifest.json')
x=read(B/'結構化候選資料.json');old=read(H/'prior-608.json');oldids={o['observation_id'] for s in old['schools'] for o in s['observations']};delta=[]
for s in x['schools']:
 for o in s['observations']:
  if o['observation_id'] not in oldids:
   assert o['selection_rule_confirmed'] is False and o['review_status']=='reviewed_public_reference'
   o['publication_role']='draft_platform_public_reference_not_formal_selection_rule';delta.append({'portal_id':s['portal_id'],'school_name':s['school_name'],**o})
assert len(delta)==51
x.pop('candidate_only');x.pop('research_stage');x.pop('research_meta');x['reviewed_at']=datetime.datetime.now(datetime.timezone.utc).isoformat();x['scope']='All 288 NTU partners; 659 scoped, reviewed public-reference observations materialized in Draft PR9 only; not merged/deployed and no current-cycle host selection approval.'
x['integration_stage']={'stage':'stage6_51_references_materialized','previous_source_sha256':sha(H/'prior-608.json'),'new_observations':51,'candidate_reference_only':True,'formal_selection_rules_promoted':False,'merged_or_deployed':False}
write(S/'completion-2026-10-11.json',x);write(D/'第五批51則已匯入增量.json',delta)
# Append new source versions while keeping all prior archive parts and entries identical.
m=read(H/'prior-478-manifest.json');existing={(e['source_id'],e['sha256']) for e in m['entries']};sm=read(B/'已讀原文manifest.json');wanted=[e for e in sm['source_bodies'] if (e['source_id'],e['sha256']) not in existing]
parts=[];part=[];size=0
with zipfile.ZipFile(B/sm['archive_file']) as src:
 for e in wanted:
  data=src.read(e['archive_body_path']);assert hashlib.sha256(data).hexdigest()==e['sha256']
  if part and size+len(data)>12000000:parts.append(part);part=[];size=0
  part.append((e,data));size+=len(data)
 if part:parts.append(part)
 for i,part in enumerate(parts,17):
  name=f'reviewed-source-bodies-stage6-2026-10-11-part-{i:02d}.zip';path=S/name;entries=[]
  with zipfile.ZipFile(path,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
   for e,data in part:
    sid=e['source_id'];arc='bodies/'+sid+'-'+e['sha256'][:12]+Path(e['archive_body_path']).suffix
    z.writestr(arc,data);z.writestr('extractions/'+sid+'.txt',src.read('texts/'+sid+'.txt'));pages='texts/'+sid+'.pages.json'
    if pages in src.namelist():z.writestr('extractions/'+sid+'.pages.json',src.read(pages))
    z.writestr('receipts/'+sid+'.json',src.read('metadata/'+sid+'.json'))
    entry={k:e[k] for k in ['source_id','url','checked_at','sha256']};entry.update(size_bytes=len(data),archive_body_path=arc,archive_file=name,role='stage6_stage5_reference_adoption_and_complete_body_review');entries.append(entry)
   z.writestr('manifest.json',json.dumps(entries,ensure_ascii=False,indent=2)+'\n')
  m['entries'].extend(entries);m['archive_files'].append({'archive_file':name,'sha256':sha(path),'size_bytes':path.stat().st_size,'source_count':len(part)})
m.update(source_count=len(m['entries']),distinct_source_id_count=len({e['source_id'] for e in m['entries']}),original_body_total_bytes=sum(e['size_bytes'] for e in m['entries']),citation_body_join_count=len(x['public_source_reviews']),stage4_unchanged_archive_parts=16,same_url_versions_preserved=True)
write(S/'reviewed-source-bodies-current-manifest.json',m)
for src,dst in [('full-body-field-review-ledger.json','full-body-review-current-2026-10-11.json'),('priority-review-progress.json','priority-review-progress-current-2026-10-11.json')]:shutil.copyfile(B/src,S/dst)
ledger=read(S/'full-body-review-current-2026-10-11.json');manual=read(S/'semantic-review-current-2026-10-11.json');dm={(r['portal_id'],r['field']):r for r in manual};dispositions=read(B/'第五批逐項語意待解.json')
for d in dispositions:
 key=(d['portal_id'],d['field']);rows=[l for l in ledger if (l['portal_id'],l['field'])==key and l['full_extracted_text_read_for_field']];uniq={(l['source_id'],l['body_sha256']):l for l in rows}
 sources=[dict(source_id=l['source_id'],sha256=l['body_sha256'],url=l['source_url'],checked_at=l['source_checked_at']) for l in uniq.values()]
 r=dict(d,sources=sources,reviewed_at=x['reviewed_at'],review_method='人工完整閱讀固定原cached正文與已讀公開後續文件；原版本SHA逐一對照，不等當期全部子項核實')
 if key in dm:r['prior_review_outcome']=dm[key]['outcome'];r['prior_review_note_zh']=dm[key]['note_zh']
 dm[key]=r
write(S/'semantic-review-current-2026-10-11.json',list(dm.values()));m['manual_semantic_rows']=len(dm);write(S/'reviewed-source-bodies-current-manifest.json',m)
# Append source and robots receipts without rewriting prior retrieval dates.
a=json.loads(gzip.decompress((S/'host-access-current-2026-10-11.json.gz').read_bytes()));by={s['portal_id']:s for s in a['schools']};receipts=[]
for p in sorted((P/'sources').glob('*.json')):
 d=read(p)
 if isinstance(d,dict) and d.get('url'):receipts.append({k:v for k,v in d.items() if k not in ['text','pages','paragraphs','links','local_file','error_preview']})
receiptmap={(r.get('source_id'),r.get('sha256'),r.get('checked_at')):r for r in receipts}
for p in sorted(P.glob('followups*-receipts.json')):
 for r in read(p):
  key=r['source_id'],r.get('sha256'),r['checked_at'];d=receiptmap[key];school=by[r['portal_id']]
  oldkeys={(s['source'].get('source_id'),s['source'].get('sha256'),s['source'].get('checked_at')) for s in school['sources']}
  if key not in oldkeys:school['sources'].append({'source':d,'field_candidate_counts':{},'stage6_full_body_review_separate':True})
a['stage6_source_receipts']=receipts;a['counts']['stage6_source_receipts']=len(receipts);a['counts']['all_school_joined_attempt_records']=sum(len(s['sources']) for s in a['schools'])
oldrobots={json.dumps(r,sort_keys=True) for r in a['robots_receipts']}
for line in (P/'robots-receipt-history.jsonl').read_text().splitlines():
 if line.strip():
  d=json.loads(line);key=json.dumps(d,sort_keys=True)
  if key not in oldrobots:a['robots_receipts'].append(d);oldrobots.add(key)
(S/'host-access-current-2026-10-11.json.gz').write_bytes(gzip.compress(json.dumps(a,ensure_ascii=False).encode(),mtime=0))
print(json.dumps({'adopted_observations':len(delta),'total_observations':659,'new_raw_body_versions':len(wanted),'total_raw_body_versions':len(m['entries']),'archive_parts':len(m['archive_files']),'manual_semantic_rows':len(dm),'full_body_pairs':len(ledger)},ensure_ascii=False))
