from pathlib import Path
import sys,json,concurrent.futures
from urllib.parse import urljoin
from bs4 import BeautifulSoup
sys.path.insert(0,'/workspace/ncu-resume-work')
from collect_visual_candidates import fetch
W=Path('/workspace/ncu-resume-work/twentyfourth')
items=[('buem-incoming','https://www.vsemba.sk/en/International-relations/ERASMUS/Incoming-students'),('monaco-abroad','https://www.monaco.edu/en/the-experience-monaco/study-abroad/'),('monaco-factsheet-2025-26','https://carleton.ca/go-isso/wp-content/uploads/sites/102/IUM-FactSheet-2025-2026-.pdf'),('altinbas-life','https://altinbas.edu.tr/en/student/student-life/'),('bingol-home','https://www.bingol.edu.tr/')]
def run(item):
 slug,url=item;p=W/(slug+('.pdf'if'.pdf'in url else'.html'));raw=fetch(url,p)
 if raw and p.suffix=='.html':
  soup=BeautifulSoup(raw,'html.parser')
  for tag in soup(['script','style']):tag.decompose()
  (W/(slug+'.txt')).write_text(soup.get_text('\n',strip=True))
  links=[{'text':a.get_text(' ',strip=True),'url':urljoin(url,a['href'])}for a in soup.select('a[href]')]
  (W/(slug+'-links.json')).write_text(json.dumps(links,ensure_ascii=False,indent=2))
 return {'slug':slug,'ok':bool(raw)}
with concurrent.futures.ThreadPoolExecutor(max_workers=2)as ex:
 for r in ex.map(run,items):print(r,flush=True)
