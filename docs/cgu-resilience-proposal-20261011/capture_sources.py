"""Two read-only public CGU sheet requests; evidence only, no application writes."""
import datetime,hashlib,json,pathlib,sys
sys.path.insert(0,'/workspace/abroad-globe-20261011/src')
from exchange_info import student_view
root=pathlib.Path('/workspace/cgu-resilience-proposal-20261011');out=root/'source-capture';out.mkdir(exist_ok=True)
original=student_view.requests.get
receipts=[]
def capture(url,*args,**kwargs):
    assert url.startswith('https://docs.google.com/spreadsheets/d/') and '/gviz/tq' in url
    started=datetime.datetime.now(datetime.timezone.utc).isoformat()
    result=original(url,*args,**kwargs)
    sid=url.split('/d/')[1].split('/')[0]
    raw=result.content;target=out/(sid+'.gviz.json');target.write_bytes(raw)
    receipt={'spreadsheet_id':sid,'url':url,'requested_at':started,'completed_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'http_status':result.status_code,'sha256':hashlib.sha256(raw).hexdigest(),'content_type':result.headers.get('content-type'),'file':target.name}
    if result.status_code==200:
        try:
            payload=student_view._parse_gviz_payload(result.text)
            receipt.update(schema_valid=all(k in payload.get('table',{}) for k in ('cols','rows')) and any(c.get('label')=='校名' for c in payload['table']['cols']),raw_rows=len(payload['table']['rows']))
        except Exception as e:receipt.update(schema_valid=False,error_type=type(e).__name__)
    receipts.append(receipt)
    return result
student_view.requests.get=capture
rows=student_view.fetch_partner_universities()
finished=datetime.datetime.now(datetime.timezone.utc).isoformat()
(root/'source-capture/receipts.json').write_text(json.dumps(receipts,ensure_ascii=False,indent=2)+'\n')
assert len(receipts)==2 and all(r['http_status']==200 and r.get('schema_valid') and r.get('raw_rows',0)>0 for r in receipts),receipts
raw=[row.model_dump(mode='json') for row in rows]
canonical=json.dumps(raw,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()
snapshot={'format_version':1,'home_school':'長庚大學','source_state':'complete_successful_fetch','fetched_at':finished,'snapshot_use':'proposal_and_tests_only_not_adopted_by_application','unit':'displayed partner rows; not confirmed current-cycle selectable institutions','source_receipts':receipts,'record_count':len(raw),'records_sha256':hashlib.sha256(canonical).hexdigest(),'records':raw}
(root/'source-capture/snapshot.json').write_text(json.dumps(snapshot,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'source_requests':len(receipts),'both_valid':True,'row_count':len(raw),'records_sha256':snapshot['records_sha256'],'fetched_at':finished},ensure_ascii=False))
