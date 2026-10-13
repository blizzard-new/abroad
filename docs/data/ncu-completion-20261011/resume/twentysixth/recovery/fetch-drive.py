from pathlib import Path
import json,gzip,sys,hashlib,concurrent.futures
sys.path.insert(0,'/workspace/ncu-resume-work')
from collect_visual_candidates import fetch
R=Path('/workspace/abroad');W=Path('/workspace/ncu-resume-work/twentysixth');pack=json.load(gzip.open(R/'sources/ncu/2026-10-08/drive-evidence.json.gz'))
ids=['13fvTs2j9VwsZKxmTjGxqI2bvhBzUSr07','18gqKN0ML2pIZLf1aVd8BM7fBKsjyoxba','1vODypBeHScxOw41FSLYABSWq-ggmGDVp','1GrxLPz2lPZQlllQoMj7gIVZ-0n49q0Zp','13HE9I87Z-H0yMUBeKXGxGkPpFPHiUApF']
items=[s for s in pack if s['id']in ids]
def run(s):
 p=W/(s['id']+'.pdf');raw=fetch(s['download_url'],p)
 if not raw:raise ValueError(s['id'])
 assert raw.startswith(b'%PDF') and hashlib.sha256(raw).hexdigest()==s['sha256'],s['id']
 return {'source_id':s['id'],'sha256':s['sha256'],'receipt':json.load(open(p.with_suffix('.pdf.source.json')))}
with concurrent.futures.ThreadPoolExecutor(max_workers=2)as ex:out=list(ex.map(run,items))
(W/'fetch-receipts.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n');print('5 public originals fetched; SHA matches archived sources')
