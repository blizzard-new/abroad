from pathlib import Path
import sys,json,concurrent.futures
ROOT=Path(__file__).parent;sys.path.insert(0,str(ROOT.parent/'stage2'))
import public_fetch
public_fetch.ROOT=ROOT
from public_fetch import Fetcher
f=Fetcher();jobs=[('816','https://ciec.kwansei.ac.jp/study/exchange/outline/pdf/2026-27%20KGU%20Exchange%20Program%20Fact%20Sheet.pdf'),('816','https://ciec.kwansei.ac.jp/page/prospective-applicationprocedure.html'),('816','https://ciec.kwansei.ac.jp/study/exchange/prospective/timeline.html')]
def run(job):
 pid,url=job;d=f.fetch(url);r={k:d.get(k) for k in ['source_id','url','checked_at','access_status','http_status','sha256','error','pdf_page_count']};r.update(portal_id=pid,text_chars=len(d.get('text','')));print(json.dumps(r,ensure_ascii=False),flush=True);return r
with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:out=list(pool.map(run,jobs))
(ROOT/'followups01-receipts.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
