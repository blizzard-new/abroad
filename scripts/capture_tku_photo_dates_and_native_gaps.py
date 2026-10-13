"""Exact photo-date metadata and native institution names; no acceptance here."""
import argparse,json,re,time
from urllib.parse import unquote,urlsplit
import requests
from capture_tku_asset_batch import B,request,paused

TERMS={339:'"闽南师范大学"',332:'"Đại học Công nghệ" "Hà Nội"',328:'"American College of Acupuncture and Oriental Medicine"',322:'"Hogeschool Zeeland"',320:'"IIC" "Cambodia"',314:'"Kalasalingam" "building"',312:'"Instituto Desarrollo" "Asunción"',317:'"Đại học Đồng Tháp"',316:'"Văn Lang Sài Gòn"',289:'"EBS Paris"',287:'"Presidency" "Yelahanka"',288:'"Đại học Nông Lâm" "Thái Nguyên"',253:'"Đại học Nguyễn Tất Thành"',275:'"Southern Cross" "Lismore"',242:'"IACT" "Malaysia"',212:'"Vel Tech" "Chennai"',206:'"Saint-Louis" "Bruxelles"',155:'"安徽财经大学"',166:'"江西财经大学"',51:'"In-House Multimedia College"',48:'"韩新学院"',52:'"UAEMex" "Toluca"',44:'"청주대학교"'}

def main():
    ap=argparse.ArgumentParser();ap.add_argument('phase',choices=['dates','native']);args=ap.parse_args()
    if args.phase=='dates':
        manifest=json.loads((B/'campus_asset_manifest.json').read_text())
        pending=manifest
        path=B/'photo_date_metadata_checks.json';records=json.loads(path.read_text()) if path.exists() else []
        done={i for r in records for i in r.get('institution_ids',[])}
        pending=[r for r in pending if r['id'] not in done]
        for offset in range(0,len(pending),15):
            batch=pending[offset:offset+15]
            if paused('commons'):break
            titles=[unquote(urlsplit(r['source_url']).path.split('/wiki/',1)[1]).replace('_',' ') for r in batch]
            params=dict(action='query',format='json',titles='|'.join(titles),prop='imageinfo',iiprop='extmetadata|metadata|commonmetadata')
            url=requests.Request('GET','https://commons.wikimedia.org/w/api.php',params=params).prepare().url
            r=request(url,'commons');r.update(institution_ids=[x['id'] for x in batch],requested_photos=[dict(id=x['id'],source_url=x['source_url'],title=t) for x,t in zip(batch,titles)],phase='exact_original_photo_date_metadata')
            records.append(r);path.write_text(json.dumps(records,ensure_ascii=False,indent=2)+'\n')
            print(json.dumps(dict(status=r.get('http_status'),institutions=len(batch),pages=len(r.get('response',{}).get('query',{}).get('pages',{})))),flush=True)
            if r.get('http_status')==429:break
            time.sleep(3)
    else:
        path=B/'commons_asset_batches.json';index=json.loads(path.read_text());done={r['institution_id'] for r in index if r.get('phase')=='native_institution_campus_search'}
        census={r['id']:r for r in map(json.loads,(B/'partner_census.jsonl').read_text().splitlines())}
        for n,term in TERMS.items():
            identifier='tku-sister-'+str(n)
            if identifier in done:continue
            if paused('commons'):break
            url=requests.Request('GET','https://commons.wikimedia.org/w/api.php',params=dict(action='query',format='json',generator='search',gsrsearch=term+' -logo -map',gsrnamespace=6,gsrlimit=6,prop='imageinfo',iiprop='url|extmetadata|sha1',iiurlwidth=1200)).prepare().url
            r=request(url,'commons');d=census[identifier];r.update(institution_id=identifier,school_name=d['school_name'],country=d['country'],query=term,phase='native_institution_campus_search',identity_source_url=d['directory_url'],reason='Native exact identity/campus discovery; licence, original photo year and pixels require separate review.')
            index.append(r);path.write_text(json.dumps(index,ensure_ascii=False,indent=2)+'\n')
            print(json.dumps(dict(id=identifier,status=r.get('http_status'),files=[p['title'] for p in r.get('response',{}).get('query',{}).get('pages',{}).values()])),flush=True)
            if r.get('http_status')==429:break
            time.sleep(3)

if __name__=='__main__':main()
