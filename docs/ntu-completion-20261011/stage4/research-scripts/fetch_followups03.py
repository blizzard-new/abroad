from pathlib import Path
import sys,json,concurrent.futures
ROOT=Path(__file__).parent;sys.path.insert(0,str(ROOT.parent/'stage2'))
import public_fetch
public_fetch.ROOT=ROOT
from public_fetch import Fetcher
f=Fetcher();jobs=[('1001','https://gao.um.edu.mo/mobility/inbound/programmes-application/'),('14','https://manoa.hawaii.edu/mix/inbound/how-to-apply-undergraduate-students/'),('14','https://manoa.hawaii.edu/mix/inbound/how-to-apply-postgraduate-students/'),('14','https://manoa.hawaii.edu/mix/inbound/english-language-requirements/'),('14','https://manoa.hawaii.edu/mix/inbound/costs-and-fees/'),('14','https://manoa.hawaii.edu/mix/inbound/official-transcript-requirements/'),('800','https://kanagawa-u.box.com/s/xp8897nzen91olifus3rdavd91sosx8q'),('800','https://www.kanagawa-u.ac.jp/international/welcome/exchange/file/file_chart.pdf?20260302')]
def run(job):
 pid,url=job;d=f.fetch(url);r={k:d.get(k) for k in ['source_id','url','checked_at','access_status','http_status','sha256','error','pdf_page_count']};r.update(portal_id=pid,text_chars=len(d.get('text','')));print(json.dumps(r,ensure_ascii=False),flush=True);return r
with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:out=list(pool.map(run,jobs))
(ROOT/'followups03-receipts.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
