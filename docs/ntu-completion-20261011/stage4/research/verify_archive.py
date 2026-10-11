from pathlib import Path
import json,zipfile,hashlib,re
r=Path('/workspace/abroad-ntu-completion-20261011');sp=r/'sources/ntu';docs=r/'docs/ntu-completion-20261011/stage4';docs.mkdir(exist_ok=True);m=json.loads((sp/'reviewed-source-bodies-current-manifest.json').read_text());snap=json.loads((sp/'completion-2026-10-11.json').read_text());norm=lambda t:re.sub(r'\s+',' ',t).strip();entries={(e['source_id'],e['sha256']):e for e in m['entries']};assert len(entries)==len(m['entries']);zs={a['archive_file']:zipfile.ZipFile(sp/a['archive_file']) for a in m['archive_files']}
for a in m['archive_files']:assert hashlib.sha256((sp/a['archive_file']).read_bytes()).hexdigest()==a['sha256']
for e in entries.values():assert hashlib.sha256(zs[e['archive_file']].read(e['archive_body_path'])).hexdigest()==e['sha256']
manual_visual=[]
for sid,review in snap['public_source_reviews'].items():
 e=entries[(sid,review['sha256'])];z=zs[e['archive_file']];text=z.read('extractions/'+sid+'.txt').decode();assert norm(review['original_quote']) in norm(text),(sid,'quote join')
 if review.get('quote_verification_method')=='manual_visual_rendered_pdf_with_transcription':
  v=json.loads((Path(__file__).parent/'kumamoto-visual-review.json').read_text());assert v['raw_pdf_sha256']==review['sha256'];assert review['quote_pdf_page']==v['quote_pdf_page']==1;assert review['original_quote']==v['manually_transcribed_quote'];manual_visual.append(sid)
for row in json.loads((sp/'semantic-review-current-2026-10-11.json').read_text()):
 for s in row['sources']:assert (s['source_id'],s['sha256']) in entries
for row in json.loads((sp/'full-body-review-current-2026-10-11.json').read_text()):assert (row['source_id'],row['body_sha256']) in entries
frozen=json.loads((sp/'reviewed-source-bodies-stage3-manifest.json').read_text());assert all(e in m['entries'] for e in frozen['entries']);assert all(a in m['archive_files'] for a in frozen['archive_files'])
visual_manifest=json.loads((docs/'evidence/visual-evidence-manifest.json').read_text())
for item in visual_manifest:
 image=docs/'evidence'/item['file'];assert image.stat().st_size==item['size_bytes'];assert hashlib.sha256(image.read_bytes()).hexdigest()==item['sha256']
for item in json.loads((sp/'full-body-review-current-2026-10-11.json').read_text()):
 for name in item.get('visual_evidence_files',[]):assert (docs/'evidence'/name).is_file()
out={'all_raw_body_hashes_match':True,'all_quoted_sources_join_exact_body_sha':True,'source_body_versions':len(entries),'distinct_source_ids':len({sid for sid,sha in entries}),'archive_parts':len(zs),'stage3_345_entries_and12_parts_preserved':True,'quote_sources':len(snap['public_source_reviews']),'manually_visually_verified_quote_sources':manual_visual,'visual_evidence_image_hashes_verified':len(visual_manifest),'full_body_school_field_source_pairs':len(json.loads((sp/'full-body-review-current-2026-10-11.json').read_text())),'source_snapshot_sha256':hashlib.sha256((sp/'completion-2026-10-11.json').read_bytes()).hexdigest()};(docs/'archive-verification.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n');print(json.dumps(out))
for z in zs.values():z.close()
