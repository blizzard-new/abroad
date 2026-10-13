from pathlib import Path
import json,gzip,sys,hashlib,concurrent.futures
sys.path.insert(0,'/workspace/ncu-resume-work')
from collect_visual_candidates import fetch
R=Path('/workspace/abroad');W=Path('/workspace/ncu-resume-work/finite-closure');ss={s['id']:s for s in json.load(gzip.open(R/'src/exchange_info/official_data/ncu/source-evidence.json.gz'))};gaps=json.load(open(W/'cited-evidence-gaps.json'))
def run(g):
 sid=g['id'];s=ss[sid];p=W/(sid+'.pdf');raw=fetch(s.get('download_url',s['url']),p);receipt=json.load(open(p.with_suffix('.pdf.source.json')))
 result={'source_id':sid,'archived_sha256':s.get('sha256'),'sha256':hashlib.sha256(raw).hexdigest()if raw else None,'receipt':receipt,'pdf':bool(raw and raw.startswith(b'%PDF'))}
 result['unchanged']=bool(result['sha256'] and result['sha256']==s.get('sha256'));print({k:v for k,v in result.items()if k!='receipt'},flush=True);return result
with concurrent.futures.ThreadPoolExecutor(max_workers=2)as ex:out=list(ex.map(run,gaps))
(W/'fetch-receipts.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
