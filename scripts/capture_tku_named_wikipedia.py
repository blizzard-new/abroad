"""Exact named-page alternatives for unresolved institutions; no promotion."""
import json,requests
from capture_tku_asset_batch import B,request

TITLES={328:'American College of Acupuncture and Oriental Medicine',324:'University of St. Thomas (Texas)',323:'Nilai University',322:'HZ University of Applied Sciences',330:'Saigon International University',320:'IIC University of Technology',312:'Instituto Desarrollo',316:'Van Lang Saigon College',307:"Chang'an University",287:'Presidency University, Bangalore',280:'Thai Nguyen University',242:'IACT College',216:'Business Breakthrough University',200:'J. F. Oberlin University',188:'Gakushuin University',173:'Latin University of Panama',169:'Osaka Metropolitan University',14:'Laurea University of Applied Sciences',96:'University of Michigan–Flint',50:'Han Chiang University College of Communication',51:'IHM College',49:'New Era University College',48:'Han Chiang High School',86:'Trinity College (Connecticut)',30:'University of Electro-Communications',25:'Josai University',28:'Tsuda University',15:'University of Franche-Comté',71:"St. John's University (New York City)"}
# Hanxing is unrelated to Han Chiang High School; do not query that near-name.
TITLES.pop(48)

def main():
    target=B/'wikipedia_named_institutions.json'
    if target.exists():return
    url=requests.Request('GET','https://en.wikipedia.org/w/api.php',params=dict(action='query',format='json',titles='|'.join(TITLES.values()),redirects=1,prop='pageprops|coordinates',ppprop='wikibase_item',colimit='max')).prepare().url
    source=request(url,'wikipedia');target.write_text(json.dumps(source,ensure_ascii=False,indent=2)+'\n')
    if source.get('error'):print(json.dumps(source));return
    redirects={r['from']:r['to'] for r in source['response']['query'].get('redirects',[])}
    normalized={r['from']:r['to'] for r in source['response']['query'].get('normalized',[])}
    pages={p['title']:p for p in source['response']['query']['pages'].values()}
    census={r['id']:r for r in map(json.loads,(B/'partner_census.jsonl').read_text().splitlines())}
    path=B/'wikidata_asset_batches.json';index=json.loads(path.read_text())
    for n,title in TITLES.items():
        identifier='tku-sister-'+str(n);name=normalized.get(title,title);name=redirects.get(name,name)
        page=pages.get(name,{});q=page.get('pageprops',{}).get('wikibase_item');d=census[identifier]
        r={k:source.get(k) for k in ('id','source_url','checked_at','service','http_status','sha256','error')}
        r.update(institution_id=identifier,school_name=d['school_name'],country=d['country'],query=title,phase='exact_wikipedia_pageprops',identity_source_url=d['directory_url'],response={'search':[dict(id=q,label=name)] if q else []},named_page=page,raw_capture='wikipedia_named_institutions.json',reason='Exact named-page identity alternative; not a rank-selected or accepted coordinate.')
        index.append(r);print(json.dumps(dict(id=identifier,title=name,q=q,coordinates=page.get('coordinates',[]))),flush=True)
    path.write_text(json.dumps(index,ensure_ascii=False,indent=2)+'\n')

if __name__=='__main__':main()
