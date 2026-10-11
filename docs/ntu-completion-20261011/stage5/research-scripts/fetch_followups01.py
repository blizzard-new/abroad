from pathlib import Path
import sys,json,concurrent.futures
ROOT=Path(__file__).parent;sys.path.insert(0,str(ROOT.parent/'stage2'))
import public_fetch
public_fetch.ROOT=ROOT
from public_fetch import Fetcher
f=Fetcher();base='https://www.unisg.ch/fileadmin/user_upload/HSG_ROOT/_Kernauftritt_HSG/Studium/Austauschprogramme/Incoming_Gaststudierende/'
jobs=[('89',base+'Austausch_Partneruniversitaeten/FactSheet_2026-27.pdf'),('89',base+'FactSheet_2026-2027_V05.pdf'),('89','https://www.unisg.ch/en/studying/exchange-programme/the-housing-office/'),('1268','https://d2xwywryb7yxbo.cloudfront.net/s3bucket-images/Hostel-Notice.pdf')]
def run(job):
 pid,url=job;d=f.fetch(url);r={k:d.get(k) for k in ['source_id','url','checked_at','access_status','http_status','sha256','error','pdf_page_count']};r.update(portal_id=pid,text_chars=len(d.get('text','')));print(json.dumps(r,ensure_ascii=False),flush=True);return r
with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:out=list(pool.map(run,jobs))
(ROOT/'followups01-receipts.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
