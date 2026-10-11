from pathlib import Path
import json,hashlib,zipfile,datetime,shutil
from research_curator import Curator
H=Path(__file__).parent;R=Path('/workspace/abroad-ntu-completion-20261011');D=R/'docs/ntu-completion-20261011/stage5';D.mkdir(exist_ok=True)
c=Curator();before=json.loads((H.parent/'stage4/full-body-field-review-ledger.json').read_text());ledger=json.loads((H/'full-body-field-review-ledger.json').read_text())
key=lambda r:(r['portal_id'],r['field'],r['source_id'],r['body_sha256'])
old={key(r) for r in before};new=[r for r in ledger if key(r) not in old]
assert len(new)==100
sids=sorted({r['source_id'] for r in new});entries=[];archive=D/'第五批已讀原文.zip'
with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
 for sid in sids:
  d=c.read_source(sid);raw=next((p for ext in ['.html','.pdf','.image'] if (p:=d['_folder']/(sid+ext)).is_file()),None);assert raw
  data=raw.read_bytes();assert hashlib.sha256(data).hexdigest()==d['sha256']
  path='bodies/'+sid+raw.suffix;z.writestr(path,data)
  text=d['text'];z.writestr('texts/'+sid+'.txt',text)
  m={k:d.get(k) for k in ['source_id','url','final_url','checked_at','http_status','document_type','pdf_page_count','sha256','title']};m.update(archive_body_path=path,extracted_text_sha256=hashlib.sha256(text.encode()).hexdigest(),text_chars=len(text),candidate_current_cycle_confirmed=False);entries.append(m)
  z.writestr('metadata/'+sid+'.json',json.dumps(m,ensure_ascii=False,indent=2))
  if d.get('pages'):z.writestr('texts/'+sid+'.pages.json',json.dumps(d['pages'],ensure_ascii=False))
 manifest={'stage5_source_versions':len(entries),'distinct_body_sha256':len({e['sha256'] for e in entries}),'source_bodies':entries,'full_body_field_reviews_added':100,'all_raw_sha256_locally_verified':True,'scope_note':'五校原cached全文及另循公開連結的全文；不等已完成當期規定，未讀新連結仍待跟讀。'}
 z.writestr('manifest.json',json.dumps(manifest,ensure_ascii=False,indent=2))
manifest.update(archive_file=archive.name,archive_size_bytes=archive.stat().st_size,archive_sha256=hashlib.sha256(archive.read_bytes()).hexdigest());(D/'已讀原文manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
for name in ['候選增量.json','結構化候選資料.json','full-body-field-review-ledger.json','priority-review-progress.json','priority-source-roster.json']:
 shutil.copyfile(H/name,D/name)
(D/'第五批完整閱讀增量.json').write_text(json.dumps(new,ensure_ascii=False,indent=2)+'\n')
E=D/'evidence';E.mkdir(exist_ok=True)
for p in H.glob('followups*-receipts.json'):shutil.copyfile(p,E/p.name)
for p in [H/'robots-receipts.json',H/'robots-receipt-history.jsonl']:
 if p.exists():shutil.copyfile(p,E/p.name)
S=D/'research-scripts';S.mkdir(exist_ok=True)
for p in H.glob('*.py'):shutil.copyfile(p,S/p.name)
shutil.copyfile(H.parent/'stage4/remote-publication-verification.json',D/'第四批遠端核對收據.json')
print(json.dumps({k:v for k,v in manifest.items() if k!='source_bodies'},ensure_ascii=False))
