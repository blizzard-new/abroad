"""Final exact institutional aliases for unresolved licensed-campus candidates."""
import json,time,requests
from capture_tku_asset_batch import B,request,paused
TERMS={339:'"闽南师范大学"',332:'"VNU University of Engineering and Technology"',328:'"American College of Acupuncture"',322:'"HZ University" "building"',320:'"IIC University"',314:'"Kalasalingam" "campus"',312:'"Instituto Desarrollo" "Paraguay"',317:'"Dong Thap University"',316:'"Van Lang Saigon College"',289:'"European Business School Paris"',287:'"Presidency University" "Bangalore"',288:'"Thai Nguyen University of Agriculture and Forestry"',253:'"Nguyen Tat Thanh University"',275:'"Southern Cross University" "campus"',242:'"IACT College"',216:'"Business Breakthrough University"',206:'"Université Saint-Louis" "Bruxelles"',155:'"Anhui University of Finance and Economics"',166:'"Jiangxi University of Finance and Economics"',69:'"Bristol" "Wills Memorial"',51:'"IHM College" "Malaysia"',48:'"Hanxing"',17:'"Paris-Sorbonne" "building"',52:'"Universidad Autónoma del Estado de México"',44:'"Cheongju University"',212:'"Vel Tech" "campus"'}
def main():
    path=B/'commons_asset_batches.json';index=json.loads(path.read_text());done={r['institution_id'] for r in index if r.get('phase')=='quoted_institution_alternative'}
    census={r['id']:r for r in map(json.loads,(B/'partner_census.jsonl').read_text().splitlines())}
    for n,term in TERMS.items():
        identifier='tku-sister-'+str(n)
        if identifier in done:continue
        if paused('commons'):break
        url=requests.Request('GET','https://commons.wikimedia.org/w/api.php',params=dict(action='query',format='json',generator='search',gsrsearch=term+' -logo -map',gsrnamespace=6,gsrlimit=4,prop='imageinfo',iiprop='url|extmetadata|sha1',iiurlwidth=1200)).prepare().url
        r=request(url,'commons');d=census[identifier];r.update(institution_id=identifier,school_name=d['school_name'],country=d['country'],query=term,phase='quoted_institution_alternative',identity_source_url=d['directory_url'],reason='Exact institution phrase after unrelated unquoted query; no automatic photo acceptance.')
        index.append(r);path.write_text(json.dumps(index,ensure_ascii=False,indent=2)+'\n')
        print(json.dumps(dict(id=identifier,http_status=r.get('http_status'),files=[p['title'] for p in r.get('response',{}).get('query',{}).get('pages',{}).values()],error=r.get('error'))),flush=True)
        if r.get('http_status')==429:break
        time.sleep(3)
if __name__=='__main__':main()
