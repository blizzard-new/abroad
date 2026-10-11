from pathlib import Path
import sys,json,concurrent.futures
ROOT=Path(__file__).parent;sys.path.insert(0,str(ROOT.parent/'stage2'))
import public_fetch
public_fetch.ROOT=ROOT
from public_fetch import Fetcher
f=Fetcher();jobs=[('371', 'https://www.unibe.ch/studies/mobility/incoming/general_information/health_insurance/index_eng.html'), ('371', 'https://www.unibe.ch/studies/mobility/incoming/general_information/partner_information/index_eng.html'), ('366', 'https://studyabroad.wisc.edu/exchange/application-process/'), ('366', 'https://studyabroad.wisc.edu/exchange/information-for-partner-universities/'), ('366', 'https://www.uhs.wisc.edu/ship/international/'), ('361', 'https://oia.ewha.ac.kr/oia/1143/subview.do'), ('361', 'https://oia.ewha.ac.kr/oia/1144/subview.do'), ('361', 'https://oia.ewha.ac.kr/oia/1145/subview.do')]
def run(job):
 pid,url=job;d=f.fetch(url);r={k:d.get(k) for k in ['source_id','url','checked_at','access_status','http_status','sha256','error','pdf_page_count']};r.update(portal_id=pid,text_chars=len(d.get('text','')));print(json.dumps(r,ensure_ascii=False),flush=True);return r
with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:out=list(pool.map(run,jobs))
(ROOT/'followups06-receipts.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
