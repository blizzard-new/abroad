"""Exact institution/building categories, bounded to named campus subcategories."""
import json,re,time,requests
from capture_tku_asset_batch import B,request,paused
ROOTS={99:'Campus of San Francisco State University',78:'University of Missouri–St. Louis',342:'Manipal University',4:'University of Queensland',37:'平成国際大学',75:'California State University, Sacramento',173:'Universidad Latina de Panamá',150:'Sichuan University',307:"Chang'an University",32:'Kyoto Tachibana University',65:'University of the West of England',86:'Trinity College (Connecticut)'}

def main():
    path=B/'commons_asset_batches.json';index=json.loads(path.read_text());done={(r['institution_id'],r.get('query')) for r in index if r.get('phase')=='dated_named_campus_subcategory'}
    census={r['id']:r for r in map(json.loads,(B/'partner_census.jsonl').read_text().splitlines())}
    def save(n,category):
        identifier='tku-sister-'+str(n)
        if (identifier,category) in done:return next(r for r in index if r['institution_id']==identifier and r.get('query')==category and r.get('phase')=='dated_named_campus_subcategory')
        if paused('commons'):return None
        url=requests.Request('GET','https://commons.wikimedia.org/w/api.php',params=dict(action='query',format='json',generator='categorymembers',gcmtitle='Category:'+category,gcmnamespace='6|14',gcmlimit=18,prop='imageinfo',iiprop='url|extmetadata|metadata|sha1',iiurlwidth=1200)).prepare().url
        r=request(url,'commons');d=census[identifier];r.update(institution_id=identifier,school_name=d['school_name'],country=d['country'],query=category,phase='dated_named_campus_subcategory',identity_source_url=d['directory_url'],reason='Exact named institution/building category; bounded child discovery. No automatic acceptance or use of unknown capture years.')
        index.append(r);done.add((identifier,category));path.write_text(json.dumps(index,ensure_ascii=False,indent=2)+'\n')
        print(json.dumps(dict(id=identifier,category=category,status=r.get('http_status'),files=[p['title'] for p in r.get('response',{}).get('query',{}).get('pages',{}).values()])),flush=True);time.sleep(3)
        return r
    for n,category in ROOTS.items():
        r=save(n,category)
        if not r or r.get('http_status')!=200:continue
        children=[p['title'].removeprefix('Category:') for p in r.get('response',{}).get('query',{}).get('pages',{}).values() if p.get('ns')==14 and re.search(r'building|campus|hall|library|校舎|大学|校区|校區|大學',p['title'],re.I) and not re.search(r'people|alumni|sports|athlet|event|map|logo',p['title'],re.I)]
        for child in children[:2]:save(n,child)

if __name__=='__main__':main()
