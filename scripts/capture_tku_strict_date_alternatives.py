"""Read original Commons captions and dated alternatives for held photos."""
import json,time,requests
from capture_tku_asset_batch import B,request,paused

CATEGORIES={41:'Dankook University',9:'Athabasca University',99:'San Francisco State University',78:'University of Missouri–St. Louis',151:'East China Normal University',173:'Latin University of Panama',342:'Manipal Academy of Higher Education',30:'University of Electro-Communications',211:'Guizhou University',4:'University of Queensland',37:'Heisei International University',26:'Josai International University',75:'California State University, Sacramento',24:'Reitaku University'}

def main():
    unresolved=json.loads((B/'photo_date_unresolved_candidates.json').read_text())
    wp=B/'photo_date_wikitext_checks.json'
    if not wp.exists() and not paused('commons'):
        url=requests.Request('GET','https://commons.wikimedia.org/w/api.php',params=dict(action='query',format='json',titles='|'.join(r['title'] for r in unresolved),prop='revisions',rvprop='content',rvslots='main')).prepare().url
        r=request(url,'commons');r.update(requested_photos=unresolved,phase='exact_original_caption_date_review')
        wp.write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n');print(json.dumps(dict(phase='original_captions',status=r.get('http_status'))),flush=True);time.sleep(3)
    path=B/'commons_asset_batches.json';index=json.loads(path.read_text());done={r['institution_id'] for r in index if r.get('phase')=='strict_photo_date_alternative'}
    census={r['id']:r for r in map(json.loads,(B/'partner_census.jsonl').read_text().splitlines())}
    for n,category in CATEGORIES.items():
        identifier='tku-sister-'+str(n)
        if identifier in done:continue
        if paused('commons'):break
        url=requests.Request('GET','https://commons.wikimedia.org/w/api.php',params=dict(action='query',format='json',generator='categorymembers',gcmtitle='Category:'+category,gcmnamespace=6,gcmlimit=10,prop='imageinfo',iiprop='url|extmetadata|metadata|sha1',iiurlwidth=1200)).prepare().url
        r=request(url,'commons');d=census[identifier];r.update(institution_id=identifier,school_name=d['school_name'],country=d['country'],query=category,phase='strict_photo_date_alternative',identity_source_url=d['directory_url'],reason='Original accepted photo has no verified capture year; exact institutional category alternatives, no automated acceptance.')
        index.append(r);path.write_text(json.dumps(index,ensure_ascii=False,indent=2)+'\n')
        print(json.dumps(dict(id=identifier,status=r.get('http_status'),files=[p['title'] for p in r.get('response',{}).get('query',{}).get('pages',{}).values()])),flush=True)
        if r.get('http_status')==429:break
        time.sleep(3)

if __name__=='__main__':main()
