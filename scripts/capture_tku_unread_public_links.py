"""Read bounded previously unvisited official links; no protection bypass."""
import argparse,json,re,time
from datetime import datetime,timezone,timedelta
from email.utils import parsedate_to_datetime
from urllib.parse import urlsplit
from capture_tku_census_hosts import BUNDLE,capture
from audit_tku_unread_candidates import institution_domain,DISCOVER,REJECT

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--followup',action='store_true');ap.add_argument('--additional',action='store_true');args=ap.parse_args()
    ip=BUNDLE/'host_census_capture_index.json';index=json.loads(ip.read_text());byid={r['id']:r for r in index}
    triage=json.loads((BUNDLE/'milestone3_unread_triage.json').read_text())
    cp=BUNDLE/'milestone3_public_link_checks.json';checks=json.loads(cp.read_text()) if cp.exists() else []
    done={r['source_url'] for r in checks};known={url for r in index for s in r['sources'] for url in (s['source_url'],s.get('final_url')) if url}
    pp=BUNDLE/'host_source_service_pause.json';pauses=json.loads(pp.read_text()) if pp.exists() else {}
    def save(row,link,phase):
        url=link['url'];host=urlsplit(url).netloc.lower()
        if url in done or url in known:return None
        until=pauses.get(host)
        if until and datetime.now(timezone.utc)<datetime.fromisoformat(until):return None
        s=capture(url)
        meta={k:s.get(k) for k in ('id','source_url','final_url','http_status','checked_at','sha256','title','error')}
        meta.update(source_role='bounded_unread_public_link',linked_from=link['linked_from'],link_label=link['label'],scope='Host public reference candidate; actual year and programme require content review')
        row['sources'].append(meta);known.add(url);done.add(url)
        if s.get('final_url'):known.add(s['final_url'])
        check=dict(meta,institution_id=row['id'],phase=phase);checks.append(check)
        if s.get('http_status')==429:
            raw=s.get('retry_after');stamp=datetime.now(timezone.utc)
            try:resume=stamp+timedelta(seconds=max(int(raw),1))
            except (TypeError,ValueError):
                try:resume=parsedate_to_datetime(raw)
                except (TypeError,ValueError):resume=stamp+timedelta(hours=1)
            pauses[host]=resume.isoformat();pp.write_text(json.dumps(pauses,indent=2)+'\n')
        cp.write_text(json.dumps(checks,ensure_ascii=False,indent=2)+'\n');ip.write_text(json.dumps(index,ensure_ascii=False,indent=2)+'\n')
        print(json.dumps(dict(id=row['id'],url=url,status=s.get('http_status'),title=s.get('title'),error=s.get('error'))),flush=True)
        time.sleep(3)
        return s
    if args.additional:
        for link in json.loads((BUNDLE/'milestone3_additional_host_targets.json').read_text()):save(byid[link['institution_id']],link,'explicit_public_attachment_or_language_link')
    elif not args.followup:
        for row in triage['host_unread']:
            for c in row['unread_candidates']:save(byid[row['id']],c,'unread_existing_link')
    else:
        import gzip
        from tku_capture_io import read_bytes
        for task in triage['host_unread']:
            row=byid[task['id']];links={}
            for m in row['sources']:
                if m.get('source_role')!='bounded_unread_public_link' or m.get('http_status')!=200 or m.get('error'):continue
                s=json.loads(gzip.decompress(read_bytes(BUNDLE/'host_census_sources'/(m['id']+'.json.gz'))))
                for l in s.get('links',[]):
                    url=l['url'];label=l['title']
                    if not url.startswith('https://') or url in known or institution_domain(url)!=institution_domain(s.get('final_url',s['source_url'])):continue
                    if not re.search(r'incoming|inbound|exchange student|fact.?sheet|application|deadline|housing|accomm|dormitor|wohnen|logement|留学生|交換|受入|申請|出願|寮|intercambio|austauschstud',label,re.I) or REJECT.search(label):continue
                    if re.search(r'/news/|/events/|Gallery|ViewAlbum|/noticias/|/novedades/',url,re.I):continue
                    links.setdefault(url,dict(url=url,label=label,linked_from=s['source_url']))
            prioritized=sorted(links.values(),key=lambda l:-(8 if re.search(r'fact.?sheet|exchange students|incoming|202[6-8]',l['label'],re.I) else 4 if re.search(r'application|deadline|nomina',l['label'],re.I) else 1))
            for l in prioritized[:3]:save(row,l,'bounded_second_public_link')

if __name__=='__main__':main()
