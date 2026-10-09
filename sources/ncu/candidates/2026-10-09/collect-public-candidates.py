from pathlib import Path
import requests,json,hashlib,datetime,io,gzip,zipfile,sys
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import urljoin,urlparse
from bs4 import BeautifulSoup
from pypdf import PdfReader
BASE=Path(__file__).resolve().parent
def collect(job):
 school,ident,url=job;p=BASE/school/'sources'/ident;p.mkdir(parents=True,exist_ok=True)
 if (p/'metadata.json').exists():return json.loads((p/'metadata.json').read_text())
 m=dict(id=ident,school_row_id=school,url=url,checked_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),tls_verification=True,current_116_applicability_verified=False,review_status='downloaded_extracted_not_manually_reviewed',full_document_read=False,original_path=str(p.relative_to(BASE)))
 try:
  assert url.startswith('https://')
  r=requests.get(url,timeout=(15,35),verify=True);m.update(status=r.status_code,final_url=r.url,content_type=r.headers.get('content-type',''),sha256=hashlib.sha256(r.content).hexdigest(),bytes=len(r.content),redirects=[dict(url=h.url,status=h.status_code)for h in r.history]);r.raise_for_status()
  data=r.content;m['pages']=[]
  if data.startswith(b'%PDF'):
   (p/'original.pdf').write_bytes(data)
   for i,page in enumerate(PdfReader(io.BytesIO(data)).pages,1):
    text=page.extract_text() or '';name=f'page-{i:03d}.txt';(p/name).write_text(text);m['pages'].append(dict(page=i,text_path=name,text_sha256=hashlib.sha256(text.encode()).hexdigest(),char_count=len(text)))
  elif data.startswith(b'PK'):
   (p/'original.zip').write_bytes(data);members=[]
   with zipfile.ZipFile(io.BytesIO(data))as z:
    for i,n in enumerate(z.namelist()):
     if n.endswith('/'):continue
     b=z.read(n);item=dict(member=n,sha256=hashlib.sha256(b).hexdigest(),bytes=len(b),read=False)
     if b.startswith(b'%PDF'):
      for j,page in enumerate(PdfReader(io.BytesIO(b)).pages,1):
       text=page.extract_text()or'';name=f'member-{i:02d}-page-{j:03d}.txt';(p/name).write_text(text);m['pages'].append(dict(page=j,archive_member=n,member_sha256=item['sha256'],text_path=name,text_sha256=hashlib.sha256(text.encode()).hexdigest(),char_count=len(text)))
     members.append(item)
   m['archive_members']=members
  elif 'html' in m['content_type'] or b'<html' in data[:1000].lower():
   (p/'original.html.gz').write_bytes(gzip.compress(data,mtime=0));s=BeautifulSoup(data,'html.parser');m['title']=s.title.get_text(' ',strip=True)if s.title else None
   m['links']=[dict(text=a.get_text(' ',strip=True),url=urljoin(r.url,a['href']))for a in s.find_all('a',href=True)]
   for el in s(['script','style','noscript']):el.decompose()
   text=s.get_text('\n',strip=True);(p/'page-web.txt').write_text(text);m['pages']=[dict(page=None,text_path='page-web.txt',text_sha256=hashlib.sha256(text.encode()).hexdigest(),char_count=len(text))]
  else:
   (p/'original.bin').write_bytes(data);m['review_status']='downloaded_unparsed'
 except Exception as e:m.update(error_type=type(e).__name__,error=str(e),review_status='unretrieved_normal_tls')
 (p/'metadata.json').write_text(json.dumps(m,ensure_ascii=False,indent=2)+'\n');return m
if __name__=='__main__':
 jobs=json.loads(Path(sys.argv[1]).read_text())
 with ThreadPoolExecutor(max_workers=4)as pool:
  for m in pool.map(collect,jobs):print(m['school_row_id'],m['id'],m.get('status'),len(m.get('pages',[])),m.get('error_type',''),flush=True)
