from pathlib import Path
from datetime import datetime,timezone
import json,gzip,collections,tempfile
from fastapi.testclient import TestClient
from exchange_info.api import create_app
from exchange_info.ncu_student_view import fetch_ncu_partner_universities
R=Path('/workspace/abroad');W=Path('/workspace/ncu-resume-work/twentyseventh');sources=json.loads(gzip.decompress((R/'src/exchange_info/official_data/ncu/source-evidence.json.gz').read_bytes()));records={}
for dt in ['2026-10-08','2026-10-11']:
 for rid,rec in json.loads((R/'sources/ncu'/dt/'reviewed-host-records.json').read_text()).items():
  prev=records.get(rid,{})
  records[rid]={**prev,**rec,'fields':{**prev.get('fields',{}),**rec['fields']},'source_ids':list(dict.fromkeys(prev.get('source_ids',[])+rec['source_ids']))}
byid={x['id']:x for x in sources};citations={rid:set(r['source_ids'])|{s['id']for f in r['fields'].values()for s in f['sources']}for rid,r in records.items()};cited=set().union(*citations.values());items=[]
for s in sources:
 if len(s.get('pages',[]))<=1 or s.get('content_status',{}).get('all_pages_read'):continue
 items.append({'id':s['id'],'url':s['url'],'label':s.get('label'),'sha256':s.get('sha256'),'format':s.get('format'),'page_count':len(s['pages']),'status':s.get('status'),'error':s.get('error'),'cited_by_reviewed_host':s['id']in cited,'row_ids':[rid for rid,ids in citations.items()if s['id']in ids],'reading_review':s.get('reading_review'),'visual_review':s.get('visual_review'),'content_status':s.get('content_status'),'reason':'全文尚無完整閱讀證據；既有引用段落不能代表全部頁面已核實。'})
report={'checked_at':datetime.now(timezone.utc).isoformat(),'base_sha':'573126cce6def44dc4c35c7c0f8ce9b59e093a0b','all_multipage_not_fully_reviewed':len(items),'cited_multipage_not_fully_reviewed':sum(x['cited_by_reviewed_host']for x in items),'cited_total_pages_or_parts':sum(x['page_count']for x in items if x['cited_by_reviewed_host']),'cited_unique_sha':len({x['sha256']for x in items if x['cited_by_reviewed_host']}),'items':items}
(W/'long-document-inventory.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print({k:v for k,v in report.items()if k!='items'},flush=True)
