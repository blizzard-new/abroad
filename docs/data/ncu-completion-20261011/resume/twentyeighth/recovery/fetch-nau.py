from pathlib import Path
import json,gzip,sys,hashlib,concurrent.futures
sys.path.insert(0,'/workspace/ncu-resume-work')
from collect_visual_candidates import fetch
R=Path('/workspace/abroad');W=Path('/workspace/ncu-resume-work/twentyeighth');pack=json.load(gzip.open(R/'sources/ncu/2026-10-08/drive-evidence.json.gz'))
ids=['1Pv7Sy8im0xCmvBGkZQk4JfITr0t3iLMC','1BXTeoOlQECl9TMR4sISlJQPyUjt6bwU7','1Bqbinel4T1rSs7y1mw0d6MAsfk1fdfUQ']
items=[s for s in pack if s['id']in ids]
def run(s):
 p=W/(s['id']+'.pdf');raw=fetch(s['download_url'],p)
 if not raw:raise ValueError(s['id'])
 assert raw.startswith(b'%PDF') and hashlib.sha256(raw).hexdigest()==s['sha256'],s['id']
 return {'source_id':s['id'],'sha256':s['sha256'],'receipt':json.load(open(p.with_suffix('.pdf.source.json')))}
with concurrent.futures.ThreadPoolExecutor(max_workers=2)as ex:out=list(ex.map(run,items))
(W/'nau-fetch-receipts.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n');print('3 NAU originals fetched; SHA matches archived sources')
