"""Finite public official geography checks; all point candidates need review."""
import gzip,hashlib,json,re,time
from urllib.parse import urlsplit,urljoin
import requests
from bs4 import BeautifulSoup
from capture_tku_asset_batch import B,HEADERS,now

MAPS={337:'https://www.cityu.edu.mo/en/campus-map/',324:'https://viewer.mapme.com/4387d020-596e-410e-b20f-49cf4e8f129a',320:'https://goo.gl/maps/or14QCNwWHb7LBpC7',246:'https://goo.gl/maps/c19ZKqQVsz22',240:'https://map.concept3d.com/?id=1200',200:'https://www.obirin.ac.jp/access/index.html',96:'https://www.umflint.edu/campus-map',48:'https://www.hanxin.edu.my/zh/contact-us',86:'https://map.trincoll.edu',30:'https://www.uec.ac.jp/eng/about/access/',8:'https://www.brandonu.ca/campus-map/',25:'https://www.josai.ac.jp/access/sakado/',28:'https://www.tsuda.ac.jp/access.html'}

MAPS.update({50:'https://hcu.edu.my/',188:'https://www.univ.gakushuin.ac.jp/',28:'https://maps.app.goo.gl/BmuzK1KroJtHquaVA'})

def main():
    path=B/'official_geography_checks.json';records=json.loads(path.read_text()) if path.exists() else []
    done={(r['institution_id'],r['source_url']) for r in records}
    covered={r['id'] for r in json.loads((B/'campus_location_manifest.json').read_text())}|{r['id'] for r in json.loads((B/'wikidata_asset_review.json').read_text()) if r.get('accepted_coordinate')}
    census=list(map(json.loads,(B/'partner_census.jsonl').read_text().splitlines()))
    for d in census:
        if d['id'] in covered:continue
        n=int(d['id'].rsplit('-',1)[-1]) if d['id'].startswith('tku-sister-') else None
        seeds=[MAPS[n]] if n in MAPS else []
        if d.get('directory_website'):seeds.append(d['directory_website'].replace('http://','https://',1))
        for url in seeds:
            previous=[r for r in records if r['institution_id']==d['id'] and r['source_url']==url]
            if previous and (previous[-1].get('http_status')!=503 or len(previous)>=2):continue
            host=urlsplit(url).netloc
            paused=[r for r in records if r.get('resume_not_before') and urlsplit(r['source_url']).netloc==host and now().isoformat()<r['resume_not_before']]
            if paused:continue
            r=dict(institution_id=d['id'],source_url=url,checked_at=now().isoformat(),identity_source_url=d['directory_url'],applicable_year='public physical geography; exchange campus allocation not verified')
            try:
                res=requests.get(url,headers=HEADERS,timeout=(8,25));r.update(http_status=res.status_code,final_url=res.url,sha256=hashlib.sha256(res.content).hexdigest(),response_text=res.text,retry_after=res.headers.get('Retry-After'))
                if res.status_code==429:
                    from datetime import timedelta
                    from email.utils import parsedate_to_datetime
                    try:until=now()+timedelta(seconds=int(r['retry_after']))
                    except (TypeError,ValueError):
                        try:until=parsedate_to_datetime(r['retry_after'])
                        except (TypeError,ValueError):until=now()+timedelta(hours=1)
                    r.update(error='rate_limit_stop_host',resume_not_before=until.isoformat())
                elif res.status_code!=200:r['error']='HTTP'+str(res.status_code)
                else:
                    soup=BeautifulSoup(res.content,'html.parser')
                    r['title']=soup.title.get_text(' ',strip=True) if soup.title else ''
                    r['map_links']=[dict(url=urljoin(res.url,x.get('href') or x.get('src') or ''),label=x.get_text(' ',strip=True)) for x in soup.select('a[href],iframe[src]') if re.search(r'maps\.|google\..*map|openstreetmap|@-?\d+\.',x.get('href') or x.get('src') or '',re.I)]
                    r['coordinate_snippets']=[res.text[max(0,m.start()-80):m.end()+150] for m in re.finditer(r'geo.position|latitude|longitude|"geo"|@-?\d+\.\d+,-?\d+\.\d+',res.text,re.I)][:20]
            except requests.RequestException as e:r['error']=str(e)
            r['attempt']=len(previous)+1
            raw=json.dumps(r,ensure_ascii=False).encode();key=hashlib.sha256((d['id']+'|'+url+'|'+r['checked_at']).encode()).hexdigest()[:24]
            target=B/'asset_batch_sources'/(key+'-official-geography.json.gz');target.write_bytes(gzip.compress(raw,mtime=0))
            summary={k:v for k,v in r.items() if k!='response_text'};summary['capture_file']=target.relative_to(B).as_posix()
            records.append(summary);path.write_text(json.dumps(records,ensure_ascii=False,indent=2)+'\n')
            print(json.dumps(dict(id=d['id'],url=url,http_status=r.get('http_status'),map_links=len(r.get('map_links',[])),coordinate_snippets=len(r.get('coordinate_snippets',[])),error=r.get('error'))),flush=True)
            time.sleep(3)

if __name__=='__main__':main()
