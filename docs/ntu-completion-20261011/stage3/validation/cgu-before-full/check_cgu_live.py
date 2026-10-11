from pathlib import Path
from datetime import datetime,timezone
import json,hashlib,requests,sys
sys.path.insert(0,'/workspace/abroad-ntu-completion-20261011/src')
from exchange_info.student_view import EXCHANGE_SHEET_ID,DOUBLE_DEGREE_SHEET_ID,fetch_partner_universities
p=Path(__file__).parent;receipts=[]
for label,sid in [('exchange',EXCHANGE_SHEET_ID),('double',DOUBLE_DEGREE_SHEET_ID)]:
 u=f'https://docs.google.com/spreadsheets/d/{sid}/gviz/tq?tqx=out:json&sheet=%E7%B8%BD%E8%A1%A8';r=requests.get(u,timeout=20);name=f'cgu-live-{label}-exact-gviz.json';(p/name).write_bytes(r.content);receipts.append(dict(url=u,checked_at=datetime.now(timezone.utc).isoformat(),http_status=r.status_code,sha256=hashlib.sha256(r.content).hexdigest(),size_bytes=len(r.content),body_file=name));r.raise_for_status()
partners=fetch_partner_universities(timeout_seconds=20);out=dict(checked_at=datetime.now(timezone.utc).isoformat(),scope='Actual CGU live sheet URLs and actual unmocked fetch_partner_universities',parsed_partner_count=len(partners),lincoln_present=any('林肯' in x.school_name or 'Lincoln' in x.school_name for x in partners),receipts=receipts)
(p/'cgu-live-exact-source-check.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n');print(json.dumps(out,ensure_ascii=False))
assert len(partners)==77 and out['lincoln_present']
