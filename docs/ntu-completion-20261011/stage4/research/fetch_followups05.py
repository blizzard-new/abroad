from pathlib import Path
import sys,json,concurrent.futures
ROOT=Path(__file__).parent;sys.path.insert(0,str(ROOT.parent/'stage2'))
import public_fetch
public_fetch.ROOT=ROOT
from public_fetch import Fetcher
f=Fetcher();jobs=[('378', 'https://www.nhis.or.kr/english/wbheaa02900m01.do'), ('378', 'https://www.nhis.or.kr/lm/lmxsrv/law/joHistoryContent.do?DATE_END=20250423&DATE_START=20250423&SEQ=41&SEQ_CONTENTS=3247414')]
def run(job):
 pid,url=job;d=f.fetch(url);r={k:d.get(k) for k in ['source_id','url','checked_at','access_status','http_status','sha256','error','pdf_page_count']};r.update(portal_id=pid,text_chars=len(d.get('text','')));print(json.dumps(r,ensure_ascii=False),flush=True);return r
with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:out=list(pool.map(run,jobs))
(ROOT/'followups05-receipts.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
