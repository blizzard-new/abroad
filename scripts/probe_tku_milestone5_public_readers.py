"""Normal public Chromium reader for readable roots whose links need JS.

No certificate bypass, login, challenge solving or private endpoint probing.
DOM capture is discovery evidence only; academic rules require a manual overlay.
"""
import gzip,hashlib,json
from datetime import datetime,timezone
from urllib.parse import urljoin
from playwright.sync_api import sync_playwright
from tku_capture_io import BUNDLE,exists,read_bytes

TARGETS=[(341,'https://www.citchennai.edu.in/'),(334,'https://www.uaeh.edu.mx/'),(267,'https://www.uniroma1.it/en/pagina-strutturale/home'),(22,'https://www.cgu.ac.jp/'),(44,'https://www.cju.ac.kr/eng/index.do'),(86,'https://www.trincoll.edu/oiss/'),(56,'https://www.ust.edu.ph/contacts/'),(285,'https://uni-bge.hu/en/')]

def main():
 checks=[];index_path=BUNDLE/'host_census_capture_index.json';index=json.loads(index_path.read_text());byid={r['id']:r for r in index}
 with sync_playwright() as p:
  browser=p.chromium.launch(headless=True)
  context=browser.new_context(ignore_https_errors=False)
  for n,url in TARGETS:
   key=hashlib.sha256((url+'milestone5-public-chromium-reader').encode()).hexdigest()[:24];path=BUNDLE/'host_census_sources'/(key+'.json.gz')
   if exists(path):s=json.loads(gzip.decompress(read_bytes(path)))
   else:
    s=dict(id=key,source_url=url,checked_at=datetime.now(timezone.utc).isoformat(),reader='normal Chromium; TLS validation enabled; DOM discovery only')
    page=context.new_page()
    try:
     response=page.goto(url,wait_until='domcontentloaded',timeout=25000);s.update(http_status=response.status if response else None,final_url=page.url)
     if s['http_status'] in [401,403,429,503]:raise RuntimeError('Public reader stopped on access/rate/service limit; no bypass')
     page.wait_for_timeout(1500)
     html=page.content().encode();s.update(sha256=hashlib.sha256(html).hexdigest(),bytes=len(html),title=page.title(),text=page.locator('body').inner_text(timeout=5000),links=page.locator('a[href]').evaluate_all('(links)=>links.map(a=>({title:a.innerText,url:a.href}))'))
    except Exception as e:s['error']=f'{type(e).__name__}: {e}'
    finally:page.close()
    path.write_bytes(gzip.compress(json.dumps(s,ensure_ascii=False).encode(),mtime=0))
   row=byid['tku-sister-'+str(n)]
   if not any(t['id']==key for t in row['sources']):row['sources'].append({k:s.get(k) for k in ['id','source_url','final_url','http_status','error','checked_at','sha256','title']}|dict(source_role='milestone5_normal_public_reader',scope='DOM discovery only; human scope and year review separately'))
   checks.append(dict(institution_id=row['id'],source_id=key,source_url=url,http_status=s.get('http_status'),error=s.get('error'),checked_at=s['checked_at'],content_sha256=s.get('sha256'),text_characters=len(s.get('text','')),reader=s.get('reader')))
   (BUNDLE/'milestone5_public_reader_checks.json').write_text(json.dumps(checks,ensure_ascii=False,indent=2)+'\n');index_path.write_text(json.dumps(index,ensure_ascii=False,indent=2)+'\n')
   print(json.dumps(checks[-1],ensure_ascii=False),flush=True)
  browser.close()
if __name__=='__main__':main()
