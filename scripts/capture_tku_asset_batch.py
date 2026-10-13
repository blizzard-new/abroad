"""Bounded, single-connection campus-source batches; retain every failed attempt.

No candidate is promoted here. Honor Retry-After and stop the service on429.
503 receives at most one later retry, never a route/proxy/cookie bypass.
"""
from pathlib import Path
from datetime import datetime,timezone,timedelta
from email.utils import parsedate_to_datetime
import argparse,gzip,hashlib,json,time
import requests

ROOT=Path(__file__).resolve().parents[1]
B=ROOT/'src/exchange_info/official_data/tku'
STORE=B/'asset_batch_sources'
HEADERS={'User-Agent':'UniWayTKUDataAudit/1.0 (https://github.com/blizzard-new/abroad; public academic reference audit)'}


def now():return datetime.now(timezone.utc)


def paused(service):
    path=B/f'{service}_service_pause.json'
    if path.exists():
        state=json.loads(path.read_text())
        if now()<datetime.fromisoformat(state['resume_not_before']):return state
    return None


def request(url,service):
    stamp=now();key=hashlib.sha256(url.encode()).hexdigest()[:24]
    record=dict(id=key,source_url=url,checked_at=stamp.isoformat(),service=service)
    state=paused(service)
    if state:
        return dict(record,http_status=429,error='paused_retry_after_no_request',resume_not_before=state['resume_not_before'])
    try:
        res=requests.get(url,headers=HEADERS,timeout=(8,30))
        record.update(http_status=res.status_code,retry_after=res.headers.get('Retry-After'),sha256=hashlib.sha256(res.content).hexdigest())
        if res.status_code==429:
            raw=res.headers.get('Retry-After')
            try:until=stamp+timedelta(seconds=int(raw))
            except (TypeError,ValueError):
                try:until=parsedate_to_datetime(raw)
                except (TypeError,ValueError):until=stamp+timedelta(hours=1)
            record.update(error='rate_limit_stop_service',resume_not_before=until.isoformat(),response_text=res.text[:5000])
            (B/f'{service}_service_pause.json').write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n')
        elif res.status_code>=400:record.update(error=f'HTTP{res.status_code}',response_text=res.text[:5000])
        else:record.update(response=res.json(),response_text=res.text)
    except requests.RequestException as exc:record['error']=str(exc)
    STORE.mkdir(parents=True,exist_ok=True)
    path=STORE/(key+'-'+stamp.strftime('%Y%m%dT%H%M%S%f')+'.json.gz')
    path.write_bytes(gzip.compress(json.dumps(record,ensure_ascii=False).encode(),mtime=0))
    return record


def main():
    p=argparse.ArgumentParser();p.add_argument('service',choices=['commons','wikidata']);p.add_argument('--limit',type=int,default=40);p.add_argument('--interval',type=float,default=3);args=p.parse_args()
    assert args.interval>=3 and 0<args.limit<=100
    STORE.mkdir(parents=True,exist_ok=True)
    path=B/f'{args.service}_asset_batches.json';index=json.loads(path.read_text()) if path.exists() else []
    previous=[r for r in index if r.get('resume_not_before')]
    if previous and now()<datetime.fromisoformat(previous[-1]['resume_not_before']):
        print(json.dumps(dict(status='paused_retry_after',resume_not_before=previous[-1]['resume_not_before'])),flush=True);return
    photos={r['id'] for r in json.loads((B/'campus_asset_manifest.json').read_text())};locations={r['id'] for r in json.loads((B/'campus_location_manifest.json').read_text())}
    covered=photos if args.service=='commons' else locations
    rows=json.loads((B/'full_census_audit.json').read_text())['schools']
    done={r['institution_id'] for r in index if r.get('response') or r.get('http_status') not in {429,503}}
    # Failed503 may be retried once after a prior batch, not forever.
    attempts={r['institution_id']:sum(x['institution_id']==r['institution_id'] for x in index) for r in index}
    selected=[r for r in rows if r['id'] not in covered and r['id'] not in done and attempts.get(r['id'],0)<2][:args.limit]
    for i,row in enumerate(selected):
        term=row.get('english_name') or row['school_name']
        if args.service=='commons':
            params=dict(action='query',format='json',generator='search',gsrsearch='"'+term+'" -logo -map',gsrnamespace=6,gsrlimit=4,prop='imageinfo',iiprop='url|extmetadata|sha1',iiurlwidth=1200)
            endpoint='https://commons.wikimedia.org/w/api.php'
        else:
            params=dict(action='wbsearchentities',search=term,language='en',format='json',limit=3)
            endpoint='https://www.wikidata.org/w/api.php'
        url=requests.Request('GET',endpoint,params=params).prepare().url
        record=request(url,args.service);record.update(institution_id=row['id'],school_name=row['school_name'],country=row['country'],query=term)
        index.append(record);path.write_text(json.dumps(index,ensure_ascii=False,indent=2)+'\n')
        print(json.dumps(dict(service=args.service,processed=i+1,id=row['id'],http_status=record.get('http_status'),candidates=len(record.get('response',{}).get('query',{}).get('pages',{})) if args.service=='commons' else len(record.get('response',{}).get('search',[])),error=record.get('error'))),flush=True)
        if record.get('http_status')==429:break
        time.sleep(args.interval)
    print(json.dumps(dict(service=args.service,attempts=len(index),covered_before=len(covered),remaining_before=287-len(covered))),flush=True)


if __name__=='__main__':main()
