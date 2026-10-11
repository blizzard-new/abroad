from pathlib import Path
import sys,json,concurrent.futures
ROOT=Path(__file__).parent;sys.path.insert(0,str(ROOT.parent/'stage2'))
import public_fetch
public_fetch.ROOT=ROOT
from public_fetch import Fetcher
f=Fetcher()
# The previous HTTP200 Kumamoto download exceeded our own 20MB cap; preserve that
# receipt before a normal public HTTPS download with a 60MB cap, not a server bypass.
p=ROOT/'sources/64063575a13c4723.json'
if p.exists() and json.loads(p.read_text()).get('error')=='ValueError: bounded_size_exceeded':p.rename(p.with_suffix('.20mb-cap-receipt.json'))
jobs=[('1187','https://docs.google.com/presentation/d/1OiXjG2qL3iY_01DGjvHtNbQOzOJZDwY4TnXhDibARpk/htmlpresent'),('1293','https://ewww.kumamoto-u.ac.jp/media/medialibrary/2022/02/ShortTermExchangeProgramBrochure.pdf'),('1115','https://internationaloffice.usp.br/new/en/')]
d=json.loads((ROOT/'sources/b72528f679f2995f.json').read_text())
for link in d.get('links',[]):
 if 'NHIS' in link['text']:jobs.append(('1305',link['url']))
def run(job):
 pid,url=job;d=f.fetch(url,max_bytes=60000000 if pid=='1293' else 20000000);r={k:d.get(k) for k in ['source_id','url','checked_at','access_status','http_status','sha256','error','pdf_page_count','size_bytes']};r.update(portal_id=pid,text_chars=len(d.get('text','')));print(json.dumps(r,ensure_ascii=False),flush=True);return r
with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:out=list(pool.map(run,jobs))
(ROOT/'followups02-receipts.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
