from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from datetime import datetime,timezone
import gzip,hashlib,json,re
import requests
from bs4 import BeautifulSoup
root=Path.cwd();dest=Path('/workspace/recovery-evidence-20261011/photo-license-live');dest.mkdir(exist_ok=True)
snap=json.loads((root/'sources/ntu/completion-2026-10-11.json').read_text());manifest=json.loads((root/'sources/ntu/reviewed-source-bodies-current-manifest.json').read_text());existing={e['url'] for e in manifest['entries']}
rows=[r for r in snap['schools'] if r.get('photo') and r['photo']['official_page_url'] not in existing]
def one(row):
 p=row['photo'];result={'school_name':row['school_name'],'url':p['official_page_url'],'checked_at':datetime.now(timezone.utc).isoformat(),'baseline_author':p['artist'],'baseline_license':p['license_name']}
 try:
  r=requests.get(p['official_page_url'],timeout=18);result.update(http_status=r.status_code,final_url=r.url)
  if r.status_code==200:
   name=f"{row['portal_id']}.html.gz";(dest/name).write_bytes(gzip.compress(r.content));body=BeautifulSoup(r.content,'html.parser').get_text(' ',strip=True);author=p['artist'].split('(')[0].strip();result.update(body_file=name,sha256=hashlib.sha256(r.content).hexdigest(),author_present=author.lower() in body.lower(),license_url_present=p['license_url'].replace('https:','').rstrip('/') in r.text)
 except requests.RequestException as error:result['error']=type(error).__name__
 return result
with ThreadPoolExecutor(max_workers=3) as pool:result=list(pool.map(one,rows))
(dest/'receipts.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(json.dumps(result,ensure_ascii=False,indent=2))
