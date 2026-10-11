from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import json,gzip,hashlib,subprocess
from collect_visual_candidates import fetch
R=Path('/workspace/abroad');W=Path('/workspace/ncu-resume-work/twentyfirst');W.mkdir(exist_ok=True)
sources={x['id']:x for x in json.load(gzip.open(R/'sources/ncu/2026-10-08/drive-evidence.json.gz'))};mapping=json.load(open(R/'sources/ncu/2026-10-08/source-map-candidates.json'))
selected=[x for x in mapping if x['row_id']in ['ncu-003','ncu-057','ncu-110','ncu-145','ncu-204']];items=[sources[id] for x in selected for id in x['files']];assert len(items)==11
(W/'candidate-identity-mapping.json').write_text(json.dumps(selected,ensure_ascii=False,indent=2)+'\n')
def run(x):
 p=W/(x['id']+'.pdf');url='https://drive.google.com/uc?export=download&id='+x['id'];raw=fetch(url,p)
 if raw is None:return {'source_id':x['id'],'error':'fetch unsuccessful'}
 sha=hashlib.sha256(raw).hexdigest()
 if sha!=x['sha256']:return {'source_id':x['id'],'error':'remote changed','actual':sha,'expected':x['sha256']}
 subprocess.run(['python','/workspace/ncu-resume-work/eighteenth-render.py',str(p),str(len(x['pages']))],check=True)
 return {'source_id':x['id'],'sha256':sha,'page_count':len(x['pages']),'receipt':json.load(open(p.with_suffix('.pdf.source.json')))}
with ThreadPoolExecutor(max_workers=2)as pool:rows=list(pool.map(run,items))
(W/'fetch-receipts.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2)+'\n');print(json.dumps([{k:v for k,v in r.items()if k!='receipt'}for r in rows],ensure_ascii=False))
