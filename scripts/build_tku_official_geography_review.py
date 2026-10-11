"""Explicit physical/representative geography decisions, never nomination campus."""
import gzip,json,re
from urllib.parse import unquote_plus
from bs4 import BeautifulSoup
from pathlib import Path
from tku_capture_io import read_bytes
from fetch_tku_asset_entities import values
B=Path(__file__).resolve().parents[1]/'src/exchange_info/official_data/tku'

def main():
    checks=json.loads((B/'official_geography_checks.json').read_text());census={r['id']:r for r in map(json.loads,(B/'partner_census.jsonl').read_text().splitlines())}
    wikipedia=json.loads((B/'wikipedia_named_institutions.json').read_text())
    pages={p['title']:p for p in wikipedia['response']['query']['pages'].values()}
    captures=json.loads((B/'wikidata_asset_entities.json').read_text());entities={q:(e,s) for s in captures for q,e in s.get('response',{}).get('entities',{}).items()}
    def official(identifier,url):
        s=next(r for r in reversed(checks) if r['institution_id']==identifier and r['source_url']==url and r.get('http_status')==200)
        raw=json.loads(gzip.decompress(read_bytes(B/s['capture_file'])));return s,BeautifulSoup(raw['response_text'],'html.parser').get_text(' ',strip=True)
    rows=[]
    def add(n,lat,lon,source,quote,locator,precision,note,secondary):
        d=census['tku-sister-'+str(n)]
        evidence=dict(source_url=source['source_url'],content_sha256=source['sha256'],checked_at=source['checked_at'],applicable_year='public named campus geography checked 2026-10-11; no TKU nomination allocation',role='public_named_campus_geography',locator=locator,quote=quote)
        r=dict(id=d['id'],status='accepted_named_physical_reference',identity_evidence=dict(source_url=d['directory_url'],checked_at=d['detail_checked_at'],applicable_year='TKU agreement identity; current programme unverified',locator='institution/country/domain/address',quote=' / '.join(str(d.get(k) or '') for k in ('english_name','country','directory_website','directory_address'))),evidence=evidence,secondary_identity_evidence=secondary)
        r['accepted_coordinate']=dict(id=d['id'],verification_status='verified_asset',acquisition_status='new_reviewed_official_geography',location=dict(city=None,latitude=lat,longitude=lon,geocode_status='verified',geocoded_at=source['checked_at'],source_url=source['source_url'],identity_source_url=d['directory_url'],precision=precision,note=note),evidence=evidence,identity_evidence=[r['identity_evidence'],secondary])
        rows.append(r)
    for n,url,lat,lon,place in [(320,'https://goo.gl/maps/or14QCNwWHb7LBpC7',11.5362739,104.9919952,'IIC University of Technology'),(246,'https://goo.gl/maps/c19ZKqQVsz22',22.3319288,114.1654064,'香港科技專上書院')]:
        s,text=official('tku-sister-'+str(n),url)
        assert place in unquote_plus(s['final_url']) and f'!3d{lat}!4d{lon}' in s['final_url']
        institution=next(r for r in json.loads((B/'host_census_capture_index.json').read_text()) if r['id']==s['institution_id'])
        sources=[json.loads(gzip.decompress(read_bytes(B/'host_census_sources'/(m['id']+'.json.gz')))) for m in institution['sources']]
        primary=next(r for r in sources if not r.get('error') and any(x['url']==url for x in r.get('links',[])))
        link=next(x for x in primary['links'] if x['url']==url)
        add(n,lat,lon,s,s['final_url'],'Officially linked named Google place !3d/!4d target; viewport @ rejected','campus','官方命名機構地標點；不採地圖視窗中心，非宿舍或已確定交換分配校區。'+('香港地理所在地與TKU原中國大陸標籤分開保留。' if n==246 else ''),dict(source_url=primary['source_url'],checked_at=primary['checked_at'],content_sha256=primary['sha256'],locator='Official map link',applicable_year='general institution address',quote=link['title']+' '+link['url']))
    s,text=official('tku-sister-323','https://www.nilai.edu.my/');assert 'Nilai University' in s['title']
    e,source=entities['Q7036842'];p=values(e,'P625');assert len(p)==1
    add(323,p[0]['latitude'],p[0]['longitude'],source,json.dumps({'entity':'Q7036842','P625':p[0],'P17':values(e,'P17')},ensure_ascii=False),'Q7036842 P625/P17 plus official Nilai homepage title','representative','母體代表點；官方網站身份另核實，Wikidata無P856不自行補成官方聲明。未確認交換或照片所示校區。',dict(source_url=s['source_url'],checked_at=s['checked_at'],applicable_year='general current institution identity',content_sha256=s['sha256'],quote=s['title']))
    for n,title,url,needle in [(188,'Gakushuin University','https://www.univ.gakushuin.ac.jp/','学習院大学'),(25,'Josai University','https://www.josai.ac.jp/access/sakado/','坂戸')]:
        s,text=official('tku-sister-'+str(n),url);assert needle in s['title'];p=pages[title]['coordinates'];assert len(p)==1 and p[0]['globe']=='earth'
        add(n,p[0]['lat'],p[0]['lon'],wikipedia,json.dumps(p[0]),'Named Wikipedia page '+title+' coordinates; independent official campus identity','representative','精確命名機構公開代表點，與官方學習院／坂戶校區身份核對；非精確校園中心或本期提名分配。',dict(source_url=s['source_url'],checked_at=s['checked_at'],content_sha256=s['sha256'],applicable_year='general campus identity',quote=s['title']))
    s,text=official('tku-sister-28','https://maps.app.goo.gl/BmuzK1KroJtHquaVA');assert '/35.7218769,139.4649951/@' in s['final_url']
    primary,text=official('tku-sister-28','https://www.tsuda.ac.jp/access.html');assert '東京都小平市津田町2-1-1' in text
    add(28,35.7218769,139.4649951,s,s['final_url'],'Official Kodaira campus walking route named numeric destination; origin, via points and viewport rejected','campus','小平校區官方步行路線目的入口點；非校園中心。千駄谷校區與不同學部另列，不推定交換分配。',dict(source_url=primary['source_url'],checked_at=primary['checked_at'],content_sha256=primary['sha256'],applicable_year='general campus access',quote='小平キャンパス / 東京都小平市津田町2-1-1'))
    source=json.loads((B/'brandon_named_coordinate_alternative.json').read_text())
    page=next(p for p in source['response']['query']['pages'].values() if p['title']=='Brandon University')
    assert page['pageprops']['wikibase_item']=='Q4957110' and len(page['coordinates'])==1
    p=page['coordinates'][0];assert p['lat']==49.84527778 and p['lon']==-99.9625
    primary,text=official('tku-sister-8','https://www.brandonu.ca/campus-map/')
    assert 'Brandon University' in primary['title']
    add(8,p['lat'],p['lon'],source,json.dumps(page['coordinates']),'Exact named Wikipedia campus coordinate + official Brandon campus map identity; earlier Wikidata Winnipeg point rejected','representative','Brandon, Manitoba機構公開代表點；與官方Brandon校園及TKU270-18th Street身份核對。舊Wikidata Winnipeg方向點拒用歷史保留，未把此點稱作交換分配校區／校園中心。',dict(source_url=primary['source_url'],checked_at=primary['checked_at'],content_sha256=primary['sha256'],applicable_year='general campus geography',quote=primary['title']))
    (B/'official_geography_review.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2)+'\n');print(json.dumps(dict(accepted=len(rows))))

if __name__=='__main__':main()
