"""One bounded Commons alternate per missing campus, without asset promotion.

Literal alternate names refer to the TKU directory institution. P18 titles below
were manually read against accepted institution entities, not selected by rank.
"""
import json,time,requests
from capture_tku_asset_batch import B,request,paused

TITLES={171:'Tongjidaxue Tushuguan.JPG',152:'Main gate of Beijing Institute of Technology main campus (20210523072112).jpg',133:'South gate of UIBE (20230215153342).jpg',127:'Gate of UCAS Yuquanlu Campus (20230906102500).jpg',24:'Reitakuuniv.jpg',74:'UIUC Illini Union and Main Quad.jpg',315:'SHU library in Baoshan.jpg',264:'Its library front.JPG',279:'ImeldaCasey TrinityatNight.jpg',215:'Hôtel-Pinet-Poitiers.jpg',123:"Fukuoka Women's University01.jpg",69:'University of Bristol.jpg',135:'Ming Palace Campus of Nanjing University of Aeronautics and Astronautics.jpg',61:'Moscow State Linguistic University at Ostozhenka (2013) by shakko 01.jpg'}
TERMS={335:'Baruch College',332:'VNU University of Engineering and Technology',334:'Universidad Autónoma del Estado de Hidalgo',328:'American College of Acupuncture Oriental Medicine',333:'西南大学',322:'HZ University Vlissingen building',320:'IIC University Technology Phnom Penh',314:'Kalasalingam University',312:'Instituto Desarrollo Paraguay',317:'Dong Thap University',316:'Van Lang Saigon College',301:'Vytautas Magnus University building',289:'EBS Paris building',287:'Presidency University Bangalore',288:'Thai Nguyen University Agriculture Forestry',268:'Université de Lille campus',275:'Southern Cross University campus',248:'IIT Kanpur campus',244:'King Mongkut Institute Technology Ladkrabang',242:'IACT College Malaysia',240:'York University Toronto campus',232:'Universitas Indonesia Depok',217:'Amity University Noida',216:'大前研一大学院',219:'Hacettepe University campus',212:'Vel Tech University campus',207:'Universidad de Málaga campus',203:'Paris Diderot campus',206:'Université Saint Louis Bruxelles',187:'Universidad de Murcia campus',173:'Universidad Latina de Panamá',155:'安徽财经大学',166:'江西财经大学',54:'Universidad Tecnológica de Panamá',51:'IHM College Malaysia',49:'New Era University College Kajang',48:'Hanxing Academy Malaysia',45:'경기대학교',17:'Paris Sorbonne University building',87:'Florida State University Westcott',86:'Trinity College Hartford Connecticut',8:'Brandon University Clark Hall',52:'Universidad Autónoma del Estado de México campus',44:'청주대학교',71:'St Johns University Queens campus'}

def main():
    path=B/'commons_asset_batches.json';index=json.loads(path.read_text())
    covered={r['id'] for r in json.loads((B/'campus_asset_manifest.json').read_text())}
    done={r['institution_id'] for r in index if r.get('phase')=='reviewed_campus_alternative'}
    census={r['id']:r for r in map(json.loads,(B/'partner_census.jsonl').read_text().splitlines())}
    for n in list(TITLES)+list(TERMS):
        identifier='tku-sister-'+str(n)
        if identifier in covered or identifier in done:continue
        if paused('commons'):break
        d=census[identifier]
        params=dict(action='query',format='json',prop='imageinfo',iiprop='url|extmetadata|sha1',iiurlwidth=1200)
        if n in TITLES:params['titles']='File:'+TITLES[n]
        else:params.update(generator='search',gsrsearch=TERMS[n]+' -logo -map',gsrnamespace=6,gsrlimit=4)
        url=requests.Request('GET','https://commons.wikimedia.org/w/api.php',params=params).prepare().url
        r=request(url,'commons');r.update(institution_id=identifier,school_name=d['school_name'],country=d['country'],query=TITLES.get(n) or TERMS[n],phase='reviewed_campus_alternative',identity_source_url=d['directory_url'])
        index.append(r);path.write_text(json.dumps(index,ensure_ascii=False,indent=2)+'\n');done.add(identifier)
        print(json.dumps(dict(id=identifier,http_status=r.get('http_status'),files=[p['title'] for p in r.get('response',{}).get('query',{}).get('pages',{}).values()],error=r.get('error'))),flush=True)
        if r.get('http_status')==429:break
        time.sleep(3)

if __name__=='__main__':main()
