"""Named official campus/contact pages for the remaining geography gaps."""
import gzip,hashlib,json,re,time
from urllib.parse import urlsplit,urljoin
from datetime import datetime,timezone,timedelta
from email.utils import parsedate_to_datetime
import requests
from bs4 import BeautifulSoup
from capture_tku_asset_batch import B,HEADERS,now

TARGETS={337:['https://oga.cityu.edu.mo/contact'],322:['https://hz.nl/en/our-campuses','https://hz.nl/en/locations/contact'],312:['https://desarrollo.edu.py/contacto/'],242:['https://www.iact.edu.my/contact-us/'],207:['https://www.uma.es/conoce-la-uma/info/5577/campus/'],203:['https://u-paris.fr/nos-sites-et-campus/'],195:['https://www.esiea.fr/ecole/campus-laval/'],175:['https://www.um.edu.mo/campus-life/'],48:['https://www.hanxin.edu.my/zh/contact-us'],15:['https://www.umlp.fr/contact'],240:['https://www.yorku.ca/international/contact'],319:['https://adelaide.edu.au/life-at-adelaide/campuses/adelaide-city-campus/']}
TARGETS[322]+=['https://hz.nl/en/studying-in-vlissingen-hz-location-edisonweg','https://hz.nl/en/studying-in-middelburg-hz-location-het-groene-woud']
TARGETS[14]=['https://www.laurea.fi/tietoa-meista/kampukset/leppavaara/']

def main():
    path=B/'official_geography_checks.json';records=json.loads(path.read_text())
    known={(r['institution_id'],r['source_url']) for r in records}
    census={r['id']:r for r in map(json.loads,(B/'partner_census.jsonl').read_text().splitlines())}
    for r in json.loads((B/'full_census_audit.json').read_text())['schools']:
        census.setdefault(r['id'],r)
    pp=B/'host_source_service_pause.json'
    def save(d,url,linked_from=None):
        if (d['id'],url) in known:return None
        pauses=json.loads(pp.read_text()) if pp.exists() else {}
        host=urlsplit(url).netloc.lower();until=pauses.get(host)
        if until and now()<datetime.fromisoformat(until):return None
        r=dict(institution_id=d['id'],source_url=url,checked_at=now().isoformat(),identity_source_url=d['directory_url'],applicable_year='public named campus geography; TKU nomination allocation unverified',linked_from=linked_from,phase='milestone3_official_named_campus')
        try:
            res=requests.get(url,headers=HEADERS,timeout=(8,25));r.update(http_status=res.status_code,final_url=res.url,sha256=hashlib.sha256(res.content).hexdigest(),response_text=res.text,retry_after=res.headers.get('Retry-After'))
            if res.status_code==429:
                raw=r['retry_after']
                try:resume=now()+timedelta(seconds=max(1,int(raw)))
                except (TypeError,ValueError):
                    try:resume=parsedate_to_datetime(raw)
                    except (TypeError,ValueError):resume=now()+timedelta(hours=1)
                pauses[host]=resume.isoformat();pp.write_text(json.dumps(pauses,indent=2)+'\n');r.update(error='rate_limit_stop_host',resume_not_before=resume.isoformat())
            elif res.status_code!=200:r['error']='HTTP'+str(res.status_code)
            else:
                soup=BeautifulSoup(res.content,'html.parser');r['title']=soup.title.get_text(' ',strip=True) if soup.title else ''
                r['map_links']=[dict(url=urljoin(res.url,x.get('href') or x.get('src') or ''),label=x.get_text(' ',strip=True)) for x in soup.select('a[href],iframe[src]') if re.search(r'maps\.|google\..*map|openstreetmap|@-?\d+\.',x.get('href') or x.get('src') or '',re.I)]
                r['coordinate_snippets']=[res.text[max(0,m.start()-100):m.end()+180] for m in re.finditer(r'geo.position|latitude|longitude|"geo"|@-?\d+\.\d+,-?\d+\.\d+',res.text,re.I)][:20]
        except requests.RequestException as e:r['error']=str(e)
        raw=json.dumps(r,ensure_ascii=False).encode();key=hashlib.sha256((d['id']+'|'+url+'|'+r['checked_at']).encode()).hexdigest()[:24]
        target=B/'asset_batch_sources'/(key+'-official-geography.json.gz');target.write_bytes(gzip.compress(raw,mtime=0))
        summary={k:v for k,v in r.items() if k!='response_text'};summary.update(capture_file=target.relative_to(B).as_posix(),attempt=1)
        records.append(summary);known.add((d['id'],url));path.write_text(json.dumps(records,ensure_ascii=False,indent=2)+'\n')
        print(json.dumps(dict(id=d['id'],url=url,status=r.get('http_status'),map_links=r.get('map_links'),error=r.get('error'))),flush=True)
        time.sleep(3)
        return r
    for n,urls in TARGETS.items():
        d=census['tku-sister-'+str(n)]
        for url in urls:
            source=save(d,url)
            if source is None:
                source=next((r for r in reversed(records) if r['institution_id']==d['id'] and r['source_url']==url and r.get('http_status')==200 and not r.get('error')),None)
            if not source or source.get('http_status')!=200 or source.get('error'):continue
            for l in source.get('map_links',[])[:2]:
                if l['url'].startswith('https://'):save(d,l['url'],url)
    d=census['tku-programme-mainland-macau-kinmen-115-88b1b8ee97f6']
    save(d,'https://global.sjtu.edu.cn/en/about-us/leadership-governance/contact-us')

if __name__=='__main__':main()
