from pathlib import Path
import sys,json,concurrent.futures
ROOT=Path(__file__).parent;sys.path.insert(0,str(ROOT.parent/'stage2'))
import public_fetch
public_fetch.ROOT=ROOT
from public_fetch import Fetcher
fetcher=Fetcher()
jobs=[
 ('1115','https://internationaloffice.usp.br/new/en/admission/undergraduate-student/'),
 ('1115','https://internationaloffice.usp.br/new/en/admission/graduate-student/'),
 ('798','https://www.liaison.nagasaki-u.ac.jp/download/172/koukan_youkou.pdf'),
 ('798','https://www.liaison.nagasaki-u.ac.jp/download/176/jlcp_e_youkou.pdf'),
 ('24','https://www.waseda.jp/inst/cie/en/exchange/application'),
 ('1187','https://docs.google.com/presentation/d/1OiXjG2qL3iY_01DGjvHtNbQOzOJZDwY4TnXhDibARpk/edit?usp=drive_link'),
 ('1305','https://sites.google.com/hufs.ac.kr/hufsinternationalexchange/Frequently-Asked-Questions/General-FAQ'),
 ('1305','https://sites.google.com/hufs.ac.kr/hufsinternationalexchange/Overview/Factsheet-and-Eligibility'),
 ('1164','https://hsuhk.sharepoint.com/:b:/t/GAO-Intranet/IQAT4421rG92SYUYoeNIVlHeATFw0SDQ6ZnTeBZNHJfs4Yo?e=QTRYrW'),
 ('1283','https://vivienda.uniandes.edu.co/index.php/tarifas-2026-1'),
 ('1293','https://ewww.kumamoto-u.ac.jp/media/medialibrary/2022/02/ShortTermExchangeProgramBrochure.pdf'),
 ('1299','https://www.njit.edu/global/j1application'),
 ('1299','https://www.njit.edu/global/j1costs'),
 ('1302','https://web.umons.ac.be/fr/plan-des-campus/'),
 ('67','https://commons.wikimedia.org/w/api.php?action=query&format=json&generator=search&gsrsearch=UTT%20Troyes&gsrnamespace=6&gsrlimit=10&prop=imageinfo&iiprop=url%7Cextmetadata'),
 ('1302','https://www.wikidata.org/w/api.php?action=wbsearchentities&search=University%20of%20Mons&language=en&format=json&limit=5')]
def run(job):
 pid,url=job;d=fetcher.fetch(url);r={'portal_id':pid,'source_id':d['source_id'],'url':url,'checked_at':d['checked_at'],'access_status':d['access_status'],'http_status':d.get('http_status'),'sha256':d.get('sha256'),'text_chars':len(d.get('text','')),'pages':d.get('pdf_page_count')};print(json.dumps(r,ensure_ascii=False),flush=True);return r
with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:results=list(pool.map(run,jobs))
(ROOT/'followups01-receipts.json').write_text(json.dumps(results,ensure_ascii=False,indent=2)+'\n')
