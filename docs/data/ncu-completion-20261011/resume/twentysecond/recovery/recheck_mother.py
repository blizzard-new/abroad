from pathlib import Path
import json,sys
sys.path.insert(0,'/workspace/ncu-resume-work')
from collect_visual_candidates import fetch
from bs4 import BeautifulSoup
W=Path('/workspace/ncu-resume-work/twentysecond');url='https://oia.ncu.edu.tw/p/412-1026-1872.php?Lang=zh-tw';p=W/'mother-current-index.html';raw=fetch(url,p)
if raw is None:raise SystemExit('mother recheck failed; no state promotion')
soup=BeautifulSoup(raw,'html.parser');text=soup.get_text(' ',strip=True)
links=[{'text':a.get_text(' ',strip=True),'url':a.get('href')} for a in soup.select('a[href]') if any(x in a.get_text(' ',strip=True)+a['href'] for x in ['名額','115ex','116ex','交換學生甄選'])]
report={'fetch':json.load(open(p.with_suffix('.html.source.json'))),'links':links,'relevant_text':[text[max(0,text.find(k)-120):text.find(k)+450] for k in ['名額','116','115'] if k in text]}
(W/'mother-current-links.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(json.dumps(report,ensure_ascii=False))
