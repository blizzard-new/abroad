from pathlib import Path
import json,fitz,hashlib
W=Path('/workspace/ncu-resume-work/finite-closure');gaps=json.load(open(W/'cited-evidence-gaps.json'));manifest=[]
for s in gaps:
 sid=s['id'];p=W/(sid+'.pdf')
 if sid=='host-tuaf-newhandbook':p=W/(sid+'-confirmed.pdf')
 if not p.exists()or not p.read_bytes().startswith(b'%PDF'):continue
 raw=p.read_bytes();sha=hashlib.sha256(raw).hexdigest()
 if s.get('sha256'):assert sha==s['sha256']
 d=fitz.open(p)
 for page in sorted(s['pages']):
  q=W/f'{sid}-p{page:03}';q.with_suffix('.txt').write_text(d[page-1].get_text());d[page-1].get_pixmap(matrix=fitz.Matrix(1.4,1.4)).save(str(q.with_suffix('.png')))
 manifest.append({'source_id':sid,'source_sha256':sha,'physical_pages':len(d),'rendered':sorted(s['pages']),'viewed':False})
(W/'render-manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n');print(manifest)
