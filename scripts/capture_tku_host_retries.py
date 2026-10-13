"""One finite retry of historic503 endpoints; stop a host on429."""
import argparse,json,time
from datetime import timedelta
from email.utils import parsedate_to_datetime
from urllib.parse import urlsplit
from capture_tku_census_hosts import BUNDLE,capture
from capture_tku_asset_batch import now


def main():
    p=argparse.ArgumentParser();p.add_argument('--limit',type=int,default=100);args=p.parse_args()
    path=BUNDLE/'host_source_retry_checks.json';checks=json.loads(path.read_text()) if path.exists() else []
    index_path=BUNDLE/'host_census_capture_index.json';index=json.loads(index_path.read_text())
    done={r['source_url'] for r in checks}
    latest={}
    for institution in index:
        for s in institution['sources']:
            if s['source_url'] not in latest or s['checked_at']>latest[s['source_url']]['checked_at']:latest[s['source_url']]=s
    done.update(url for url,s in latest.items() if s.get('http_status')!=503)
    targets={s['source_url']:(r,s) for r in index for s in r['sources'] if s.get('http_status')==503 and s['source_url'] not in done}
    # Other HTTP errors are not retried, and unsupported old binary formats are
    # retained as gaps rather than pretending their content is an HTML page.
    pending=[v for v in targets.values() if not urlsplit(v[1]['source_url']).path.lower().endswith('.xls')]
    pending.sort(key=lambda v:(not any(x in v[1]['source_url'].lower() for x in ['2027','exchange','incoming','inbound','.pdf','.docx']),v[0]['id']))
    for institution,prior in pending[:args.limit]:
        host=urlsplit(prior['source_url']).netloc
        waits=[r for r in checks if r.get('resume_not_before') and urlsplit(r['source_url']).netloc==host]
        if waits and now().isoformat()<waits[-1]['resume_not_before']:continue
        source=capture(prior['source_url'],key_suffix='|finite503-retry1-20261011')
        check=dict(source_id=source['id'],institution_id=institution['id'],source_url=source['source_url'],checked_at=source['checked_at'],http_status=source.get('http_status'),error=source.get('error'),prior_source_id=prior['id'],prior_http_status=503,attempt=2,sha256=source.get('sha256'))
        if source.get('http_status')==429:
            raw=source.get('retry_after');stamp=now()
            try:until=stamp+timedelta(seconds=int(raw))
            except (TypeError,ValueError):
                try:until=parsedate_to_datetime(raw)
                except (TypeError,ValueError):until=stamp+timedelta(hours=1)
            check.update(retry_after=raw,resume_not_before=until.isoformat())
        institution['sources'].append({k:source.get(k) for k in ('id','source_url','final_url','http_status','checked_at','sha256','title','error')})
        checks.append(check);path.write_text(json.dumps(checks,ensure_ascii=False,indent=2)+'\n');index_path.write_text(json.dumps(index,ensure_ascii=False,indent=2)+'\n')
        print(json.dumps(check),flush=True);time.sleep(3)
    print(json.dumps(dict(attempts=len(checks),still_not_attempted=max(0,len(pending)-args.limit))),flush=True)


if __name__=='__main__':main()
