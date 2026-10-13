"""List concrete TKU gaps and bounded unread public links without promotion."""
import argparse,gzip,json,re
from collections import Counter
from urllib.parse import urlsplit,urlunsplit,parse_qsl,urlencode
from pathlib import Path
from tku_capture_io import BUNDLE,read_bytes

DISCOVER=re.compile(r'incoming|inbound|exchange|intercambio|movilidad|mobility|erasmus|international|internacional|internationale|austausch|ausland|mobilit|logement|housing|accommodation|dormitor|residence|wohn|外国|留学|国際|国际|國際|學生宿舍|学生寮|english|英語|英语',re.I)
REJECT=re.compile(r'outbound|outgoing|study abroad|outgoing|login|log in|apply now|staff|news|event|出国|出國|派遣|海外留学|海外留學',re.I)

def institution_domain(url):
    host=urlsplit(url).netloc.lower().removeprefix('www.')
    suffixes=('edu.cn','ac.jp','ac.kr','edu.my','edu.au','ac.uk','ac.in','edu.vn','edu.tw','ac.th','edu.kh','ac.za','edu.pl')
    n=3 if any(host.endswith('.'+s) for s in suffixes) else 2
    return '.'.join(host.split('.')[-n:])

def canonical_public_url(url):
    parsed=urlsplit(url)
    query=urlencode([(k,v) for k,v in parse_qsl(parsed.query,keep_blank_values=True) if k!='grid' and not k.startswith('utm_')])
    return urlunsplit((parsed.scheme,parsed.netloc,parsed.path.rstrip('/') or '/',query,''))

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--remaining',action='store_true');args=ap.parse_args()
    rows=[json.loads(x) for x in (BUNDLE/'partner_enrichment.jsonl').read_text().splitlines()]
    gap=json.loads((BUNDLE/'continuation_gap_closure.json').read_text())
    known={canonical_public_url(url) for r in rows for s in r['source_checks'] for url in (s['source_url'],s.get('final_url')) if url}
    audit=[]
    for r in rows:
        if r['fields']:continue
        candidates=[];source_reads=[]
        for meta in r['source_checks']:
            s=json.loads(gzip.decompress(read_bytes(BUNDLE/'host_census_sources'/(meta['id']+'.json.gz'))))
            source_reads.append(dict(id=s['id'],source_url=s['source_url'],http_status=s.get('http_status'),title=s.get('title'),error=s.get('error'),text_characters=len(s.get('text','')),reason='existing capture read; no indexed application/language/life excerpt yet'))
            if s.get('error') or s.get('http_status')!=200:continue
            base=institution_domain(s.get('final_url',s['source_url']))
            for link in s.get('links',[]):
                label=link['title'];url=link['url']
                if not url.startswith('https://') or institution_domain(url)!=base or canonical_public_url(url) in known or not DISCOVER.search(label) or REJECT.search(label):continue
                score=6 if re.search(r'incoming|inbound|exchange student|international student|交換|交换|受入|留学生|intercambio|austauschstud|studenti internaz',label,re.I) else 4 if re.search(r'housing|accommod|dorm|residence|wohn|logement',label,re.I) else 2
                if score<6 and re.search(r'news|event|noticias|novedades|tufstoday|featured-stories|Gallery|ViewAlbum|/node/|/post/|/info/',url,re.I):continue
                if re.search(r'conference|festival|seminar|webinar|summer camp|讲座|講演|论坛|研讨|研討|学術|訪問|访问|国际顶|世界大学ランキング|日報|research|first.year incoming|Bachelor Student Cost',label,re.I):continue
                scope=('event_or_person_story' if re.search(r'/news/|/events?/|/évènement/|REPORT |EVENT |Farewell|Welcome Party|留学生の声|Voices of International|開催報告|交流について|交換.*イベント|promueve el intercambio',url+' '+label,re.I)
                       else 'degree_admission_not_verified_exchange' if re.search(r'入試|examination_info|bachelors-and-masters|招生简章|/2019|2019.*pdf|admission\.pku|entry-2022|Preparatory department',url+' '+label,re.I)
                       else 'teaching_material_or_historical_course_not_exchange_rule' if re.search(r'教材|learning_tool|MA \(English\).*2023',url+' '+label,re.I)
                       else 'general_international_directory' if re.search(r'prospective|international|internacional|国际|国際|留学生',label,re.I) and score<6
                       else 'programme_scope_and_period_require_reading')
                candidates.append(dict(url=url,label=label,linked_from=s['source_url'],score=score,source_id=s['id'],candidate_scope=scope))
        unique={}
        for c in sorted(candidates,key=lambda c:-c['score']):unique.setdefault(c['url'],c)
        blocked=[s for s in source_reads if s['http_status'] in (403,412,429) or s.get('error')]
        audit.append(dict(id=r['id'],school_name=r['school_name'],country=r['country'],source_reads=source_reads,unread_candidates=list(unique.values())[:5],blockers=blocked,status='unread_public_candidates_available' if unique else 'no_additional_safe_public_candidate_in_existing_links'))
    assets=[]
    for r in gap['schools']:
        if r['photo_status']=='verified_asset' and r['coordinate_status']=='verified_asset':continue
        visual=[v['reason'] for v in r.get('photo_visual_history',[]) if v.get('result')=='rejected']
        geo=r.get('coordinate_candidate_review') or {}
        assets.append(dict(id=r['id'],school_name=r['school_name'],country=r['country'],photo_status=r['photo_status'],coordinate_status=r['coordinate_status'],photo_reason=' / '.join(visual) or r['remaining_photo_requirement'],coordinate_reason=geo.get('reason') or r['remaining_coordinate_requirement'],official_geography_checks=r.get('official_geography_checks',[]),photo_source_checks=r.get('photo_source_checks',[])))
    record=dict(base_commit='88bd00531d9a77fb98ba54dbfd8786cbde18db96',checked_date='2026-10-11',denominator=287,assets=assets,host_unread= audit,interpretation='Every listed school was checked against stored captures. A public link is a reading candidate, not evidence of current TKU nomination, deadline or form. Failed access and absent candidate are not an official announcement of non-publication.')
    name='milestone3_remaining_triage.json' if args.remaining else 'milestone3_unread_triage.json'
    (BUNDLE/name).write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n')
    md=['# 淡江第三輪續查：逐校缺口及未讀候選（2026-10-11）','',f'基準88bd0053：照片缺23、座標缺27；無官方索引欄位148校。下列「未讀候選」只表示已捕捉頁面提供的安全公開連結，不表示當期申請規定。','', '| 學校 | 照片阻礙 | 座標阻礙 |','|---|---|---|']
    for r in assets:
        md.append('|'+r['school_name']+'|'+(r['photo_reason'] if r['photo_status']!='verified_asset' else '已核對')+'|'+(r['coordinate_reason'] if r['coordinate_status']!='verified_asset' else '已核對')+'|')
    md+=['','| 無官方欄位的學校 | 來源狀態 | 未讀候選數 |','|---|---|---|']
    for r in audit:
        statuses=Counter(str(s['http_status'] or 'connection_error') for s in r['source_reads'])
        md.append('|'+r['school_name']+'|'+', '.join(k+':'+str(v) for k,v in statuses.items())+'|'+str(len(r['unread_candidates']))+'|')
    if not args.remaining:Path('docs/tku-unread-triage-milestone3-20261011.md').write_text('\n'.join(md)+'\n')
    print(json.dumps(dict(schools_without_reference_fields=len(audit),schools_with_unread_candidates=sum(bool(r['unread_candidates']) for r in audit),unread_candidate_links=sum(len(r['unread_candidates']) for r in audit),asset_gap_schools=len(assets))))

if __name__=='__main__':main()
