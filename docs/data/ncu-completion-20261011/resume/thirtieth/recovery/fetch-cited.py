from pathlib import Path
import json,gzip,sys,hashlib,concurrent.futures
sys.path.insert(0,'/workspace/ncu-resume-work')
from collect_visual_candidates import fetch
R=Path('/workspace/abroad');W=Path('/workspace/ncu-resume-work/thirtieth')
ids={'host-ph-ssp-cgaf','host-ph-9f-cgaf','host-xmu-course-reference-2025-26','ncu-155-resume14-cuk-courses','host-kansai-next-08'}
items=[s for s in json.load(gzip.open(R/'src/exchange_info/official_data/ncu/source-evidence.json.gz'))if s['id']in ids]
def run(s):
 p=W/(s['id']+'.pdf');raw=fetch(s.get('download_url',s['url']),p)
 if not raw:raise ValueError(s['id'])
 fmt='pdf' if raw.startswith(b'%PDF') else 'xlsx' if raw.startswith(b'PK') else 'xls' if raw.startswith(bytes.fromhex('d0cf11e0a1b11ae1')) else 'unknown'
 assert fmt!='unknown',s['id'];sha=hashlib.sha256(raw).hexdigest()
 if fmt!='pdf':(W/(s['id']+'.'+fmt)).write_bytes(raw)
 return {'source_id':s['id'],'archived_sha256':s['sha256'],'sha256':sha,'format':fmt,'unchanged':sha==s['sha256'],'receipt':json.load(open(p.with_suffix('.pdf.source.json')))}
with concurrent.futures.ThreadPoolExecutor(max_workers=2)as ex:out=list(ex.map(run,items))
(W/'fetch-receipts.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n');print([{k:v for k,v in x.items()if k!='receipt'}for x in out])
