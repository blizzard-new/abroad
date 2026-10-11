from pathlib import Path
import json,gzip,hashlib,re,subprocess
from bs4 import BeautifulSoup
from scripts.tku_capture_io import BUNDLE,read_bytes
raw=Path('/workspace/recovery-evidence-20261011');out=raw/'tku-final-source-samples';out.mkdir(exist_ok=True)
rows=json.loads((raw/'tku-final-reviewed-delta-values.json').read_text());norm=lambda t:re.sub(r'\s+',' ',t).strip();sources={};errors=[];count=0
for f in rows:
 assert f['status']=='reference_only' and f['reason'] and f['evidence']
 for e in f['evidence']:
  sid=e.get('source_id') or Path(e['capture_file']).name.removesuffix('.json.gz')
  if sid not in sources:
   p=BUNDLE/e.get('capture_file',f'host_census_sources/{sid}.json.gz')
   try:r=json.loads(gzip.decompress(read_bytes(p)))
   except (KeyError,FileNotFoundError):errors.append({'id':sid,'error':'not in host capture pack'});continue
   sources[sid]=r
  r=sources[sid];assert r['sha256']==e['content_sha256']
  txt=r.get('text') or BeautifulSoup(r.get('response_text',''),'html.parser').get_text(' ',strip=True)
  if norm(e['quote']) not in norm(txt):errors.append({'id':sid,'field':f['field'],'school':f['id'],'error':'quote not literal normalized extracted text','quote':e['quote'][:150]})
  count+=1
  (out/(sid+'.txt')).write_text(txt)
report={'input':'93cbd9dfee3af95f9ecc89cceb1ccd0e100778af','all_added_chinese_facts_read':len(rows),'unique_source_captures':len(sources),'quoted_references_checked':count,'errors':errors,'independent_semantic_review_extent':'All320 added M3-M6 Chinese values read; preserve host/home, source year, nomination/application, conditional documents and fee/income distinctions. Original contexts are risk-based samples, not a full reread of every source.','original_sources_index':[{k:r.get(k)for k in ['id','source_url','sha256','http_status','local_file']}for r in sources.values()]}
(raw/'tku-final-independent-semantic-review.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items()if k!='original_sources_index'},ensure_ascii=False,indent=2));assert not errors
