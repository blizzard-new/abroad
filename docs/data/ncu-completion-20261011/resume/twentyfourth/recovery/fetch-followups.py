from pathlib import Path
import sys,json,concurrent.futures
from urllib.parse import urljoin
from bs4 import BeautifulSoup
sys.path.insert(0,'/workspace/ncu-resume-work')
from collect_visual_candidates import fetch
W=Path('/workspace/ncu-resume-work/twentyfourth')
items=[('buem-studyguide','https://www.vsemba.sk/portals/0/Subory/IncomingStudents_StudyGuide_2023.pdf'),('buem-accommodation','https://www.vsemba.sk/portals/0/Subory/Accommodation_Bratislava_2023.pdf'),('buem-courses','https://www.vsemba.sk/en/International-relations/ERASMUS/Incoming-students/Courses'),('buem-dormitory','https://www.vsemba.sk/en/Study/Study-support-and-resources/Dormitory'),('altinbas-global','https://global.altinbas.edu.tr'),('bingol-erasmus','https://erasmus.bingol.edu.tr/')]

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
