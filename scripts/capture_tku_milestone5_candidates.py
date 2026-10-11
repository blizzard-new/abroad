"""Account for every frozen candidate; serial per-host, preserve capture history."""
import concurrent.futures
import argparse
import gzip
import json
import time
from collections import defaultdict
from datetime import datetime, timezone
from urllib.parse import urlsplit

from audit_tku_unread_candidates import canonical_public_url
from capture_tku_census_hosts import BUNDLE, capture
from tku_capture_io import read_bytes


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--inputs',default='milestone5_route_inputs.json')
    ap.add_argument('--checks',default='milestone5_route_capture_checks.json')
    args=ap.parse_args()
    input_record=json.loads((BUNDLE/args.inputs).read_text())
    inputs=input_record['candidates']
    index_path=BUNDLE/'host_census_capture_index.json'
    index=json.loads(index_path.read_text());byid={r['id']:r for r in index}
    checks_path=BUNDLE/args.checks
    checks=json.loads(checks_path.read_text()) if checks_path.exists() else []
    complete={c['ordinal'] for c in checks};known={}
    for row in index:
        for s in row['sources']:
            for url in (s['source_url'],s.get('final_url')):
                if url:known.setdefault(canonical_public_url(url),s)
    pauses_path=BUNDLE/'host_source_service_pause.json'
    pauses=json.loads(pauses_path.read_text()) if pauses_path.exists() else {}
    groups=defaultdict(list)
    for c in inputs:
        if c['ordinal'] not in complete:groups[urlsplit(c['url']).netloc].append(c)

    def read_host(candidates):
        result=[]
        for c in candidates:
            host=urlsplit(c['url']).netloc;pause=pauses.get(host)
            old=known.get(canonical_public_url(c['url']))
            if old:
                s=json.loads(gzip.decompress(read_bytes(BUNDLE/'host_census_sources'/(old['id']+'.json.gz'))))
                mode='existing_canonical_capture_body_review_no_repeat_request'
            elif pause and datetime.now(timezone.utc)<datetime.fromisoformat(pause):
                result.append(dict(**c,capture_mode='not_requested_active_Retry_After',pause_until=pause,checked_at=datetime.now(timezone.utc).isoformat()));continue
            else:
                s=capture(c['url']);mode='public_GET_or_immutable_exact_capture'
                # Do not make additional requests on this host after rate limiting.
                if s.get('http_status')==429:
                    from datetime import timedelta
                    from email.utils import parsedate_to_datetime
                    raw=s.get('retry_after');now=datetime.now(timezone.utc)
                    try:resume=now+timedelta(seconds=max(1,int(raw)))
                    except (ValueError,TypeError):
                        try:resume=parsedate_to_datetime(raw)
                        except (ValueError,TypeError):resume=now+timedelta(hours=1)
                    pauses[host]=resume.isoformat()
                time.sleep(1)
            result.append({**c,'discovery_source_id':c.get('source_id'),'capture_mode':mode,'source_id':s['id'],'source_url':s['source_url'],'final_url':s.get('final_url'),'http_status':s.get('http_status'),'error':s.get('error'),'checked_at':s['checked_at'],'content_sha256':s.get('sha256'),'title':s.get('title'),'text_characters':len(s.get('text','')),'pages':len(s.get('pages',[])),'local_file':s.get('local_file')})
        return result

    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
        futures={pool.submit(read_host,c):host for host,c in groups.items()}
        for future in concurrent.futures.as_completed(futures):
            results=future.result()
            for c in results:
                if c.get('source_id'):
                    row=byid[c['institution_id']]
                    if not any(s['id']==c['source_id'] for s in row['sources']):
                        row['sources'].append(dict(id=c['source_id'],source_url=c['source_url'],final_url=c['final_url'],http_status=c['http_status'],error=c['error'],checked_at=c['checked_at'],sha256=c['content_sha256'],title=c['title'],source_role='milestone5_incoming_route_candidate',linked_from=c['linked_from'],link_label=c['label'],scope='Candidate only; body/year/programme review separately'))
                checks.append(c)
            checks.sort(key=lambda c:c['ordinal'])
            checks_path.write_text(json.dumps(checks,ensure_ascii=False,indent=2)+'\n')
            index_path.write_text(json.dumps(index,ensure_ascii=False,indent=2)+'\n')
            pauses_path.write_text(json.dumps(pauses,indent=2)+'\n')
            print(json.dumps(dict(completed=len(checks),host=futures[future],results=[dict(n=c['ordinal'],status=c.get('http_status'),chars=c.get('text_characters'),error=c.get('error')) for c in results])),flush=True)
    assert len(checks)==len(inputs)==input_record['input_count']


if __name__=='__main__':main()
