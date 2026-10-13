"""Download manually selected licensed candidates; promotion requires visual hash review."""
from pathlib import Path
from datetime import timedelta
from email.utils import parsedate_to_datetime
import argparse,hashlib,json,time
import requests
from bs4 import BeautifulSoup
from PIL import Image
from capture_tku_asset_batch import B,HEADERS,now,paused

# Index positions are bound to recorded Commons responses, not a name matcher.
# Each entry was read for institution and actual campus/building description.
PICKS={324:0,326:0,323:0,322:0,330:0,321:1,319:1,313:2,311:0,310:0,308:3,301:3,300:2,303:0,290:3,307:2,306:0,285:0,283:0,281:2,284:0,299:2,280:3,277:1,278:1,270:2,276:2,272:2,266:1,261:1,263:2,260:0,267:1,258:1,248:1,252:1,251:1,249:3,239:2,243:0,246:1,241:3,245:3,238:1,236:0,228:2,227:2,225:2,223:0,224:0,214:2,213:3,218:0,221:0,209:0,210:3,202:0,201:3}
PICKS.update({199:0,200:0,211:1,195:2,197:0,192:2,190:0,194:1,193:0,191:2,198:3,187:2,188:1,186:1,183:1,184:1,185:2,177:3,174:3,176:0,175:2,169:3,168:0,167:1,118:1,119:0,117:1,151:3,110:0,108:1,107:1,146:1,147:2,105:0,154:3,103:1,4:2,100:1,40:3,7:2,99:2,69:2,68:2,98:1,97:3,59:1,55:2,96:0,39:0,95:0,38:0,37:1,94:3,93:2,21:1,50:0,92:0,90:2,141:0,140:2,88:3,89:0,67:2,47:0,20:1,9:0,6:0,161:0,32:2,31:2,62:2,87:1,70:3,10:0,3:0,53:2,85:1,84:3,130:3,66:0,27:1,83:1,25:3,26:0,28:2,52:0,60:3,12:1,65:0,82:0,15:2,81:0,63:0,57:3,43:0,79:2,80:2,11:1,42:1,56:1,78:2,77:0,76:3,75:3,73:1,72:0,41:0})
PICKS.update({23:2,22:0})


def plain(meta,key):return BeautifulSoup(meta.get(key,{}).get('value',''),'html.parser').get_text(' ',strip=True)


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--limit',type=int,default=100);args=parser.parse_args()
    path=B/'new_photo_candidates.json';records=json.loads(path.read_text()) if path.exists() else []
    done={r['id'] for r in records}
    schools={r['id']:r for r in map(json.loads,(B/'partner_census.jsonl').read_text().splitlines())}
    searches=json.loads((B/'commons_asset_batches.json').read_text());assets=B.parents[1]/'static/assets/tku-campuses'
    for s in searches:
        number=int(s['institution_id'].rsplit('-',1)[-1]) if s['institution_id'].startswith('tku-sister-') else None
        if number not in PICKS or s['institution_id'] in done:continue
        if paused('commons'):
            print(json.dumps(dict(status='paused_retry_after',resume_not_before=paused('commons')['resume_not_before'])),flush=True);break
        if args.limit<=0:break
        p=list(s['response']['query']['pages'].values())[PICKS[number]];info=p['imageinfo'][0];m=info['extmetadata']
        school=schools[s['institution_id']];license=plain(m,'LicenseShortName');artist=plain(m,'Artist')
        assert license in {'CC0','Public domain','CC BY 2.0','CC BY 2.5','CC BY 3.0','CC BY 4.0','CC BY-SA 2.0','CC BY-SA 2.5','CC BY-SA 3.0','CC BY-SA 4.0'},(p['title'],license)
        r=dict(id=s['institution_id'],title=p['title'],school_name=school['school_name'],country=school['country'],source_url=info['descriptionurl'],
            image_source_url=info['url'],download_url=info.get('thumburl') or info['url'],author=artist,license=license,
            license_url=(m.get('LicenseUrl',{}).get('value') or info['descriptionurl']+'#Licensing').replace('http://creativecommons.org/','https://creativecommons.org/'),
            license_capture_url=s['source_url'],checked_at=now().isoformat(),metadata_checked_at=s['checked_at'],metadata_source_sha256=s['sha256'],
            photo_date=plain(m,'DateTimeOriginal') or '來源未提供拍攝日期；不以查核日期替代',identity_quote=plain(m,'ImageDescription') or p['title'],
            caption=plain(m,'ImageDescription') or p['title'],identity_source_url=school['directory_url'],identity_address=school['directory_address'],
            applicable_year='historical campus scene at source date; TKU nomination campus unverified',review_status='metadata_reviewed_visual_pending',
            transformations='Commons upstream 1200px thumbnail; downloaded bytes unchanged' if info.get('thumburl') else 'none; original downloaded bytes retained',
            campus_pair_scope='照片來源所述校區與獨立校級代表點未推定相同，亦未確認為淡江本期交換分配校區。')
        if number==319:r['caption']+='；University of Adelaide歷史North Terrace校區照片；2026合併後當期TKU對應另待核實。'
        if number==246:r['caption']+='；香港地理所在地與淡江名錄原中國大陸標籤分開保留。'
        try:
            assert artist,'missing source artist'
            res=requests.get(r['download_url'],headers=HEADERS,timeout=(8,30));r.update(http_status=res.status_code,retry_after=res.headers.get('Retry-After'))
            if res.status_code==429:
                raw=res.headers.get('Retry-After')
                try:until=now()+timedelta(seconds=int(raw))
                except (TypeError,ValueError):
                    try:until=parsedate_to_datetime(raw)
                    except (TypeError,ValueError):until=now()+timedelta(hours=1)
                r.update(error='rate_limit_stop_service',resume_not_before=until.isoformat())
                (B/'commons_service_pause.json').write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n')
            else:
                res.raise_for_status();suffix='.png' if res.content.startswith(b'\x89PNG') else '.webp' if res.content.startswith(b'RIFF') else '.jpg'
                file=assets/(r['id']+'-batch'+suffix);file.write_bytes(res.content)
                with Image.open(file) as image:image.verify()
                with Image.open(file) as image:r.update(width=image.width,height=image.height)
                r.update(local_path='/static/assets/tku-campuses/'+file.name,sha256=hashlib.sha256(res.content).hexdigest(),bytes=len(res.content))
        except (requests.RequestException,AssertionError,OSError) as exc:r.update(error=str(exc),review_status='download_or_metadata_failed')
        records.append(r);path.write_text(json.dumps(records,ensure_ascii=False,indent=2)+'\n');args.limit-=1
        print(json.dumps(dict(id=r['id'],file=r['title'],http_status=r.get('http_status'),error=r.get('error'))),flush=True)
        if r.get('http_status')==429:break
        time.sleep(3)


if __name__=='__main__':main()
