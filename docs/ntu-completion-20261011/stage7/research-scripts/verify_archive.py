from pathlib import Path
import json,zipfile,hashlib,re
R=Path('/workspace/abroad-ntu-completion-20261011');S=R/'sources/ntu';D=R/'docs/ntu-completion-20261011';H=Path(__file__).parent
read=lambda p:json.loads(p.read_text());norm=lambda t:re.sub(r'\s+',' ',t).strip();sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
m=read(S/'reviewed-source-bodies-current-manifest.json');snapshot=read(S/'completion-2026-10-11.json');old=read(H/'prior-511-manifest.json');assert all(e in m['entries'] for e in old['entries']);assert all(a in m['archive_files'] for a in old['archive_files'])
entries={(e['source_id'],e['sha256']):e for e in m['entries']};assert len(entries)==len(m['entries']);zs={a['archive_file']:zipfile.ZipFile(S/a['archive_file']) for a in m['archive_files']}
for a in m['archive_files']:assert sha(S/a['archive_file'])==a['sha256']
for e in entries.values():assert hashlib.sha256(zs[e['archive_file']].read(e['archive_body_path'])).hexdigest()==e['sha256']
for sid,r in snapshot['public_source_reviews'].items():
 e=entries[(sid,r['sha256'])];text=zs[e['archive_file']].read('extractions/'+sid+'.txt').decode();assert norm(r['original_quote']) in norm(text),(sid,'source quote')
for r in read(S/'semantic-review-current-2026-10-11.json'):
 for s in r['sources']:assert (s['source_id'],s['sha256']) in entries
ledger=read(S/'full-body-review-current-2026-10-11.json')
for r in ledger:
 assert (r['source_id'],r['body_sha256']) in entries
 for name in r.get('visual_evidence_files',[]):assert any((D/stage/'evidence'/name).is_file() for stage in ['stage4','stage5','stage7'])
visuals=[]
for stage in ['stage4','stage5','stage7']:
 v=D/stage/'evidence/visual-evidence-manifest.json'
 if not v.is_file():continue
 for item in read(v):
  p=v.parent/item.get('file',item.get('image_file'));assert not item.get('size_bytes') or p.stat().st_size==item['size_bytes'];assert sha(p)==item['sha256'];visuals.append(item)
delta=read(D/'stage7/第七批41則已匯入增量.json');assert len(delta)==41
for o in delta:
 e=entries[(o['source_id'],o['raw_body_sha256'])];z=zs[e['archive_file']];text=z.read('extractions/'+o['source_id']+'.txt').decode();assert norm(o['original_quote']) in norm(text)
 if o.get('pdf_page'):
  pages=json.loads(z.read('extractions/'+o['source_id']+'.pages.json'));page=next(p['text'] for p in pages if p['page']==o['pdf_page']);assert norm(o['original_quote']) in norm(page),(o['observation_id'],'exact page')
out={'source_snapshot_sha256':sha(S/'completion-2026-10-11.json'),'observations':sum(len(s['observations']) for s in snapshot['schools']),'all_raw_body_hashes_match':True,'quoted_sources':len(snapshot['public_source_reviews']),'full_body_school_field_source_pairs':len(ledger),'source_versions':len(entries),'distinct_source_ids':len({sid for sid,sha in entries}),'archive_parts':len(zs),'stage6_511_entries_and18_parts_preserved':True,'stage7_41_observation_quotes_and_pdf_pages_verified':True,'visual_evidence_hashes_verified':len(visuals)}
(D/'stage7/archive-verification.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n');print(json.dumps(out))
for z in zs.values():z.close()
