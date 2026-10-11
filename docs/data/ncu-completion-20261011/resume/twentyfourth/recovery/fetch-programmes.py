from pathlib import Path
import sys,json,concurrent.futures
from urllib.parse import urljoin
from bs4 import BeautifulSoup
sys.path.insert(0,'/workspace/ncu-resume-work')
from collect_visual_candidates import fetch
W=Path('/workspace/ncu-resume-work/twentyfourth')
items=[('buem-application','https://www.vsemba.sk/portals/0/Subory/ERASMUS_IncomingStudents_ApplicationFormForStudy_VSEM.docx'),('buem-learning','https://www.vsemba.sk/portals/0/Subory/ERASMUS_IncomingStudents_LearningAgreement_VŠEM.docx'),('altinbas-incoming','https://global.altinbas.edu.tr/?page_id=339'),('altinbas-other-exchange','https://global.altinbas.edu.tr/?page_id=299'),('altinbas-handbook','https://global.altinbas.edu.tr/wp-content/uploads/2023/03/Handbook-for-Incoming_compressed.pdf'),('bingol-student-documents','https://erasmus.bingol.edu.tr/belgeler/gelen-giden-ogrenci-belgeleri/')]

def run(item):
 slug,url=item;p=W/(slug+('.docx'if'.docx'in url else'.pdf'if'.pdf'in url else'.html'));raw=fetch(url,p)
 if raw and p.suffix=='.html':
  soup=BeautifulSoup(raw,'html.parser')
  for tag in soup(['script','style']):tag.decompose()
  (W/(slug+'.txt')).write_text(soup.get_text('\n',strip=True))
  links=[{'text':a.get_text(' ',strip=True),'url':urljoin(url,a['href'])}for a in soup.select('a[href]')]
  (W/(slug+'-links.json')).write_text(json.dumps(links,ensure_ascii=False,indent=2))
 return {'slug':slug,'ok':bool(raw)}
with concurrent.futures.ThreadPoolExecutor(max_workers=2)as ex:
 for r in ex.map(run,items):print(r,flush=True)
