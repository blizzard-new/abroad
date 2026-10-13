"""One exact category/title batch for remaining licensed-photo gaps."""
import json,time,requests
from capture_tku_asset_batch import B,request,paused
CATEGORIES={339:'Minnan Normal University',332:'VNU University of Engineering and Technology',334:'Universidad Autónoma del Estado de Hidalgo',322:'HZ University of Applied Sciences',317:'Dong Thap University',289:'European Business School Paris',287:'Presidency University, Bangalore',288:'Thai Nguyen University of Agriculture and Forestry',253:'Nguyen Tat Thanh University',275:'Southern Cross University',242:'IACT College',232:'Universitas Indonesia',216:'Business Breakthrough University',206:'Université Saint-Louis - Bruxelles',155:'Anhui University of Finance and Economics',166:'Jiangxi University of Finance and Economics',51:'IHM College',48:'Hanxing Academy',17:'Université Paris-Sorbonne',52:'Autonomous University of State of Mexico',44:'Cheongju University'}
FILES={49:'New Era University College (220709) 01.jpg'}
CATEGORIES.update({69:'University of Bristol',219:'Hacettepe University',314:'Kalasalingam Academy of Research and Education',212:'Vel Tech University'})
def main():
    path=B/'commons_asset_batches.json';index=json.loads(path.read_text());done={r['institution_id'] for r in index if r.get('phase')=='commons_exact_category'}
    census={r['id']:r for r in map(json.loads,(B/'partner_census.jsonl').read_text().splitlines())}
    for n,term in {**CATEGORIES,**FILES}.items():
        identifier='tku-sister-'+str(n)
        if identifier in done:continue
        if paused('commons'):break
        params=dict(action='query',format='json',prop='imageinfo',iiprop='url|extmetadata|sha1',iiurlwidth=1200)
        if n in FILES:params['titles']='File:'+term
        else:params.update(generator='categorymembers',gcmtitle='Category:'+term,gcmnamespace=6,gcmlimit=12)
        url=requests.Request('GET','https://commons.wikimedia.org/w/api.php',params=params).prepare().url
        r=request(url,'commons');d=census[identifier];r.update(institution_id=identifier,school_name=d['school_name'],country=d['country'],query=term,phase='commons_exact_category',identity_source_url=d['directory_url'],reason='Named institution category; file metadata and pixels require separate review.')
        index.append(r);path.write_text(json.dumps(index,ensure_ascii=False,indent=2)+'\n')
        print(json.dumps(dict(id=identifier,http_status=r.get('http_status'),files=[p['title'] for p in r.get('response',{}).get('query',{}).get('pages',{}).values()],error=r.get('error'))),flush=True)
        if r.get('http_status')==429:break
        time.sleep(3)
if __name__=='__main__':main()
