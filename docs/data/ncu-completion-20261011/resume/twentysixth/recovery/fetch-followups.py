from pathlib import Path
import sys,json,concurrent.futures
from urllib.parse import urljoin
from bs4 import BeautifulSoup
sys.path.insert(0,'/workspace/ncu-resume-work')
from collect_visual_candidates import fetch
W=Path('/workspace/ncu-resume-work/twentysixth')
items=[('bingol-university-brochure','https://erasmus.bingol.edu.tr/media/49102/bingol-university.pdf'),('bingol-info-package-doc','https://www.bingol.edu.tr/documents/file/bu_InternationalOfficeDocument/Bilgi-Paketi.doc')]

def run(item):
 slug,url=item;p=W/(slug+('.doc'if url.endswith('.doc')else'.docx'if'.docx'in url else'.pdf'if'.pdf'in url else'.html'));raw=fetch(url,p)
 if raw and p.suffix=='.html':
  soup=BeautifulSoup(raw,'html.parser')
  for tag in soup(['script','style']):tag.decompose()
  (W/(slug+'.txt')).write_text(soup.get_text('\n',strip=True))
  links=[{'text':a.get_text(' ',strip=True),'url':urljoin(url,a['href'])}for a in soup.select('a[href]')]
  (W/(slug+'-links.json')).write_text(json.dumps(links,ensure_ascii=False,indent=2))
 return {'slug':slug,'ok':bool(raw)}
with concurrent.futures.ThreadPoolExecutor(max_workers=2)as ex:
 for r in ex.map(run,items):print(r,flush=True)
