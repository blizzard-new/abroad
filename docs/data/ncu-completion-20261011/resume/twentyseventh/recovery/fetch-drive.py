from pathlib import Path
import json,gzip,sys,hashlib,concurrent.futures
sys.path.insert(0,'/workspace/ncu-resume-work')
from collect_visual_candidates import fetch
R=Path('/workspace/abroad');W=Path('/workspace/ncu-resume-work/twentyseventh');pack=json.load(gzip.open(R/'sources/ncu/2026-10-08/drive-evidence.json.gz'))
ids=['1hqaCisXb0JKE2xJnmyzffbaoMi4mdQQv','1K6mXo5lNNese80U4L9TA0QLoQ_UTYuw8','1lvagqWUlDqhK_qQ7Pv9TH2zpIaw716ON','18uF0TkNzOklcOqAuFibsmrAbeApPkBuW','1q5M5_iYOGRTDESA9MXtnHvocmxg2ONAr']
items=[s for s in pack if s['id']in ids]
def run(s):
 p=W/(s['id']+'.pdf');raw=fetch(s['download_url'],p)
 if not raw:raise ValueError(s['id'])
 assert raw.startswith(b'%PDF') and hashlib.sha256(raw).hexdigest()==s['sha256'],s['id']
 return {'source_id':s['id'],'sha256':s['sha256'],'receipt':json.load(open(p.with_suffix('.pdf.source.json')))}
with concurrent.futures.ThreadPoolExecutor(max_workers=2)as ex:out=list(ex.map(run,items))
(W/'fetch-receipts.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n');print('5 public originals fetched; SHA matches archived sources')
