"""Explicit reviewed files only; prior rejected attempts and bytes remain intact."""
import hashlib,json,time,requests,re
from PIL import Image
from capture_tku_asset_batch import B,HEADERS,now,paused
from capture_tku_reviewed_photo_candidates import plain
from capture_tku_campus_alternatives import TITLES

PICKS={**TITLES,335:'Baruch College October 2025.jpg',333:'Swu beidamen1.JPG',314:'Kalasalingam University.jpg',301:"Rector's Office of the Vytautas Magnus University in Kaunas, Lithuania in 2016.jpg",268:'Batiment SH3 Université de Lille 1.JPG',248:'IIT Kanpur 4.jpg',244:"King Mongkut's Institute of Technology Ladkrabang Stadium.jpg",240:'York University, Toronto, Canada - June 2023 3.jpg',217:'Amity University D Block.jpg',219:'Hacettepe Üniversitesi Beytepe Kampüsü - Hacettepe University Beytepe Campus (10.05.2023) 149.jpg',212:'Campus-vtu.jpg',207:'Edificio López de Peñalver UMA.jpg',203:'Parisdiderot 2.jpg',187:'Murcia - Universidad de Murcia, Campus de la Merced, Facultad de Derecho 1.jpg',173:'ULAT PA-2.jpg',54:'Postgrado.jpg',45:'경기대학교 야경.jpg',87:'Westcott Building and fountain at Florida State University.jpg',86:'MMDA-Photos - 2020-12-14 - Trinity College Chapel.jpg'}

PICKS.update({8:'2009-0520-BrandonUniversity.jpg',71:'St Johns St Augustine Hall.jpg'})
PICKS.update({334:'Ciudaduniversitariaentrada.jpg',232:'Ui Central Library, Crystal of Knowledge Library.jpg',49:'New Era University College (220709) 01.jpg'})
PICKS.update({69:'Wills Memorial Building Tower (from south-west, post-2000s-restoration).jpg',219:'Hacettepe Üniversitesi Beytepe Kampüsü - Hacettepe University Beytepe Campus (10.05.2023) 171.jpg',17:'Université Paris-Sorbonne.jpg',52:'Edificio CUPA.jpg',216:'Business Breakthrough University(Kojimachi).JPG'})
PICKS.update({9:'Athabasca University (J).jpg',41:'0 DanKooKU 6.jpg',151:'Chemistry Building, ECNU.jpg',30:'The University of Electro-Communications gate.jpg',211:'贵州大学 - Guizhou University - 2015.07 - panoramio.jpg',317:'Trường Đại học Đồng Tháp.jpg',322:'Hogeschool Zeeland.PNG',320:'Establishment of IIC University of Technology.jpg'})
PICKS.update({99:'Fine Arts building at San Francisco State University, California, US.jpg',78:'UMSL 01.jpg',342:'MAHEMANIPALEDU.jpg',4:'Foundation Building UQ Gatton Campus from SW (2009).jpg',75:'California State University, Sacramento - University Library.jpg',150:"Jiang'an Library of Sichuan University.JPG",307:"2023-10-10 陕西西安 长安大学 Chang'an University 01.jpg",32:'Kyoto Tachibana University.JPG',65:'Block B, University of the West of England - geograph.org.uk - 6031781.jpg',86:'Albert C. Jacobs Life Sciences Center Trinity College Hartford.jpg'})
PICKS[41]='0 DanKooKU 3a.jpg'
PICKS[52]='EidicioA FCPyS.jpg'

def main():
    path=B/'new_photo_candidates.json';records=json.loads(path.read_text());done={(r['id'],r['title']) for r in records}
    schools={r['id']:r for r in map(json.loads,(B/'partner_census.jsonl').read_text().splitlines())}
    searches=[r for r in json.loads((B/'commons_asset_batches.json').read_text()) if r.get('phase') in {'reviewed_campus_alternative','commons_exact_category','quoted_institution_alternative','native_institution_campus_search','strict_photo_date_alternative','dated_named_campus_subcategory'}]
    for s in searches:
        n=int(s['institution_id'].rsplit('-',1)[-1]);title='File:'+PICKS[n] if n in PICKS else None
        if not title or (s['institution_id'],title) in done:continue
        if paused('commons'):break
        pages=s.get('response',{}).get('query',{}).get('pages',{}).values()
        p=next((p for p in pages if p['title']==title),None)
        if not p:continue
        info=p['imageinfo'][0];m=info['extmetadata'];d=schools[s['institution_id']]
        license=plain(m,'LicenseShortName');artist=plain(m,'Artist')
        assert license in {'CC0','Public domain','CC BY 2.0','CC BY 2.5','CC BY 3.0','CC BY 4.0','CC BY-SA 2.0','CC BY-SA 2.5','CC BY-SA 3.0','CC BY-SA 4.0'} and artist
        date=plain(m,'DateTimeOriginal')
        if not re.search(r'\b(?:18|19|20)\d{2}\b',date) or re.search('upload',date,re.I):
            date=next((x['value'] for x in info.get('metadata',[]) if x['name']=='DateTimeOriginal'),'')
        if not re.search(r'\b(?:18|19|20)\d{2}\b',date):
            print(json.dumps(dict(id=d['id'],title=title,status='capture_year_not_verified_no_download')),flush=True);continue
        r=dict(id=d['id'],title=title,school_name=d['school_name'],country=d['country'],source_url=info['descriptionurl'],image_source_url=info['url'],download_url=info.get('thumburl') or info['url'],author=artist,license=license,license_url=(m.get('LicenseUrl',{}).get('value') or info['descriptionurl']+'#Licensing').replace('http://creativecommons.org/','https://creativecommons.org/'),license_capture_url=s['source_url'],metadata_source_sha256=s['sha256'],metadata_checked_at=s['checked_at'],checked_at=now().isoformat(),identity_source_url=d['directory_url'],identity_address=d['directory_address'],photo_date=date,identity_quote=plain(m,'ImageDescription') or title,caption=(plain(m,'ImageDescription') or title)+' — '+title,applicable_year='historic named institution campus scene; current TKU nomination campus unverified',transformations='Commons upstream thumbnail; downloaded bytes unchanged',campus_pair_scope='命名照片校區與代表座標分開核對；未推定為淡江本期提名校區。',review_status='metadata_reviewed_visual_pending',acquisition_batch='official_identity_alternative')
        try:
            res=requests.get(r['download_url'],headers=HEADERS,timeout=(8,30));r.update(http_status=res.status_code,retry_after=res.headers.get('Retry-After'))
            if res.status_code==429:
                from datetime import timedelta
                from email.utils import parsedate_to_datetime
                try:until=now()+timedelta(seconds=int(r['retry_after']))
                except (TypeError,ValueError):
                    try:until=parsedate_to_datetime(r['retry_after'])
                    except (TypeError,ValueError):until=now()+timedelta(hours=1)
                r.update(error='rate_limit_stop_service',resume_not_before=until.isoformat())
                (B/'commons_service_pause.json').write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n')
            else:
                res.raise_for_status();suffix='.png' if res.content.startswith(b'\x89PNG') else '.jpg'
                file=B.parents[1]/'static/assets/tku-campuses'/(d['id']+'-alternative-'+hashlib.sha256(title.encode()).hexdigest()[:8]+suffix);file.write_bytes(res.content)
                with Image.open(file) as image:image.verify()
                with Image.open(file) as image:r.update(width=image.width,height=image.height)
                r.update(local_path='/static/assets/tku-campuses/'+file.name,sha256=hashlib.sha256(res.content).hexdigest(),bytes=len(res.content))
        except (requests.RequestException,OSError) as e:r.update(error=str(e),review_status='download_failed')
        records.append(r);done.add((r['id'],title));path.write_text(json.dumps(records,ensure_ascii=False,indent=2)+'\n')
        print(json.dumps(dict(id=r['id'],title=title,http_status=r.get('http_status'),error=r.get('error'))),flush=True)
        if r.get('http_status')==429:break
        time.sleep(3)

if __name__=='__main__':main()
