from pathlib import Path
import json,gzip,subprocess,hashlib,io,zipfile
from pypdf import PdfReader
from bs4 import BeautifulSoup
p=Path('/tmp/ccu-eighth-fixed-review-20261011/src/exchange_info/official_data/ccu');old=json.loads(subprocess.check_output(['git','show','258ce9bbb38081792658f9720bdb457a5344b2bb:src/exchange_info/official_data/ccu/completion-reviewed-fields.json']))['schools'];new=json.loads((p/'completion-reviewed-fields.json').read_text())['schools'];output=Path('/workspace/recovery-evidence-20261011/ccu-eighth-reviewed-images');output.mkdir(exist_ok=True);sources={};changes=[]
for a,b in zip(old,new):
 for group in ['host_fields','general_campus_fields','profile_fields']:
  for k,v in b[group].items():
   if v!=a[group][k]:
    changes.append({'page':b['ccu_page'],'school':b['school_name'],'group':group,'field':k,'status':v['status'],'value':v['value'],'evidence':v['evidence']})
    for e in v['evidence']:
     sid=e.get('source_id');rp=p/'completion_sources'/f'{sid}.receipt.json'
     if not sid or not rp.exists():continue
     receipt=json.loads(rp.read_text());f=p/receipt['bundled_file'];body=gzip.decompress(f.read_bytes()) if f.suffix=='.gz' else f.read_bytes();assert hashlib.sha256(body).hexdigest()==e['content_hash'];sources[sid]={'source_id':sid,'url':e['source_url'],'body_sha256':e['content_hash'],'receipt':receipt};ext='.pdf' if body.startswith(b'%PDF') else '.docx' if body.startswith(b'PK') else '.body';(output/(sid+ext)).write_bytes(body)
     if ext=='.pdf':
      reader=PdfReader(io.BytesIO(body));text='\n\n'.join(f'PAGE {i+1}\n'+(page.extract_text() or '') for i,page in enumerate(reader.pages));sources[sid]['pages']=len(reader.pages)
     elif ext=='.docx':
      with zipfile.ZipFile(io.BytesIO(body)) as z:
       xmls=['word/document.xml'] if 'word/document.xml' in z.namelist() else [n for n in z.namelist() if n.startswith('xl/') and n.endswith('.xml')]
       text='\n\n'.join(n+'\n'+BeautifulSoup(z.read(n),'xml').get_text('\n',strip=True) for n in xmls)
       if xmls[0]!='word/document.xml':
        (output/(sid+'.xlsx')).write_bytes(body);(output/(sid+'.docx')).unlink()
     else:
      soup=BeautifulSoup(body,'html.parser')
      for t in soup(['script','style','noscript']):t.decompose()
      text=soup.get_text('\n',strip=True)
     (output/(sid+'.txt')).write_text(text)
(output/'changed-fields.json').write_text(json.dumps(changes,ensure_ascii=False,indent=2)+'\n');(output/'source-index.json').write_text(json.dumps(list(sources.values()),ensure_ascii=False,indent=2)+'\n');print({'changed':len(changes),'sources':len(sources),'pdf':len(list(output.glob('*.pdf'))),'docx':len(list(output.glob('*.docx')))})
print(json.dumps([{'sid':x['source_id'],'url':x['url'],'pages':x.get('pages')} for x in sources.values()],ensure_ascii=False,indent=2))
