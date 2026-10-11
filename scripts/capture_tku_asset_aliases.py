"""Bounded official identity aliases after empty/irrelevant exact-name results."""
import json,time,requests
from capture_tku_asset_batch import B,request,paused

ALIASES={335:'Baruch College',332:'VNU University of Engineering and Technology',328:'American College of Acupuncture and Oriental Medicine',324:'University of St. Thomas Houston',322:'HZ University of Applied Sciences',320:'IIC University of Technology',314:'Kalasalingam Academy of Research and Education',312:'Instituto Desarrollo Paraguay',316:'Van Lang Saigon College',315:'Shanghai University',307:"Chang'an University",287:'Presidency University Bangalore',244:"King Mongkut's Institute of Technology Ladkrabang",264:'Sepuluh Nopember Institute of Technology',279:'Trinity College Dublin',216:'Business Breakthrough University',215:'University of Poitiers',219:'Hacettepe University',200:'J. F. Oberlin University',195:'ESIEA',194:'University of Texas at San Antonio',123:"Fukuoka Women's University",59:'Babeș-Bolyai University',55:'University of Panama',96:'University of Michigan-Flint',39:'University of Aizu',54:'Technological University of Panama',50:'Han Chiang University College of Communication',51:'IHM College Malaysia',49:'New Era University College Malaysia',48:'Hanxing Academy Malaysia',67:'Hertford College Oxford',17:'Paris-Sorbonne University',61:'Moscow State Linguistic University',12:'Prague University of Economics and Business',76:'Ohio University',73:'University of West Florida',71:"St. John's University New York",86:'Trinity College Connecticut',69:'University of Bristol',135:'Nanjing University of Aeronautics and Astronautics',155:'Anhui University of Finance and Economics',280:'Thai Nguyen University'}


def main():
    path=B/'wikidata_asset_batches.json';index=json.loads(path.read_text())
    done={r['institution_id'] for r in index if r.get('phase')=='official_identity_alias'}
    census={r['id']:r for r in map(json.loads,(B/'partner_census.jsonl').read_text().splitlines())}
    for number,term in ALIASES.items():
        identifier='tku-sister-'+str(number)
        if identifier in done:continue
        if paused('wikidata'):print(json.dumps(dict(status='paused_retry_after',resume_not_before=paused('wikidata')['resume_not_before'])),flush=True);break
        row=census[identifier]
        url=requests.Request('GET','https://www.wikidata.org/w/api.php',params=dict(action='wbsearchentities',search=term,language='en',format='json',limit=3)).prepare().url
        s=request(url,'wikidata');s.update(institution_id=identifier,school_name=row['school_name'],country=row['country'],query=term,phase='official_identity_alias',identity_source_url=row['directory_url'],reason='Exact institution alias/site identity; changed query retained; no automatic candidate acceptance.')
        index.append(s);path.write_text(json.dumps(index,ensure_ascii=False,indent=2)+'\n')
        print(json.dumps(dict(id=identifier,query=term,http_status=s.get('http_status'),hits=[h['id'] for h in s.get('response',{}).get('search',[])])),flush=True)
        if s.get('http_status')==429:break
        time.sleep(3)


if __name__=='__main__':main()
