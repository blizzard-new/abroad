from pathlib import Path
import sys,json,concurrent.futures
ROOT=Path(__file__).parent;sys.path.insert(0,str(ROOT.parent/'stage2'))
import public_fetch
public_fetch.ROOT=ROOT
from public_fetch import Fetcher
f=Fetcher();jobs=[('26', 'https://www.ocha.ac.jp/intl/studyjp/menu/application/exchange_d/fil/ApplicationGuidelines2027.pdf'), ('26', 'https://www.ocha.ac.jp/intl/studyjp/menu/application/exchange_d/fil/JP_ApplicationGuidelines.pdf'), ('378', 'https://site.hanyang.ac.kr/web/exchangein/field-of-study'), ('378', 'https://site.hanyang.ac.kr/web/exchangein/faq'), ('378', 'https://site.hanyang.ac.kr/web/exchangein/insurance'), ('1115', 'https://internationaloffice.usp.br/new/en/incoming/undergraduate-student/'), ('1115', 'https://internationaloffice.usp.br/new/en/incoming/graduate-student/')]
def run(job):
 pid,url=job;d=f.fetch(url);r={k:d.get(k) for k in ['source_id','url','checked_at','access_status','http_status','sha256','error','pdf_page_count']};r.update(portal_id=pid,text_chars=len(d.get('text','')));print(json.dumps(r,ensure_ascii=False),flush=True);return r
with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:out=list(pool.map(run,jobs))
(ROOT/'followups04-receipts.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
