"""Keep capture dates distinct from upload dates and hold unresolved periods."""
import json,re
from bs4 import BeautifulSoup
from tku_capture_io import BUNDLE

def main():
    sources=json.loads((BUNDLE/'photo_date_metadata_checks.json').read_text())
    captions=json.loads((BUNDLE/'photo_date_wikitext_checks.json').read_text())
    pages={p['title']:p for p in captions.get('response',{}).get('query',{}).get('pages',{}).values()}
    special={26:('2007-03-29','2007年3月29日投稿者が撮影'),24:('2005-12-18','2005年12月18日投稿者が撮影')}
    reviews=[]
    for source in sources:
        requested={r['title']:r for r in source['requested_photos']}
        assert source.get('http_status')==200 and not source.get('error')
        for p in source['response']['query']['pages'].values():
            wanted=requested[p['title']];info=p['imageinfo'][0]
            meta=info.get('extmetadata',{});date=BeautifulSoup(meta.get('DateTimeOriginal',{}).get('value',''),'html.parser').get_text(' ',strip=True)
            camera=next((str(x['value']) for x in info.get('metadata',[]) if x['name']=='DateTimeOriginal'),'')
            years=set(re.findall(r'\b(?:18|19|20)\d{2}\b',date));camera_years=set(re.findall(r'\b(?:18|19|20)\d{2}\b',camera))
            upload_only=bool(re.search(r'upload',date,re.I));evidence=[]
            status='capture_year_not_verified';accepted=None;basis=None
            if years and not upload_only:
                if camera_years and not camera_years.intersection(years):status='conflicting_capture_years_requires_confirmation'
                else:status='verified_capture_period';accepted=date;basis='Commons Information DateTimeOriginal, not upload timestamp'
            elif camera_years:
                status='verified_capture_period';accepted=camera;basis='Camera EXIF DateTimeOriginal; upload-only caption rejected as capture date'
            evidence.append(dict(source_url=source['source_url'],checked_at=source['checked_at'],content_sha256=source['sha256'],locator=p['title']+' imageinfo.extmetadata.DateTimeOriginal / imageinfo.metadata.DateTimeOriginal',quote=json.dumps(dict(information_date=date,camera_exif_date_time_original=camera),ensure_ascii=False),role='licensed_photo_capture_period',applicable_year='photo period only; no current TKU nomination campus claim'))
            n=int(wanted['id'].rsplit('-',1)[-1]) if wanted['id'].startswith('tku-sister-') else None
            if status!='verified_capture_period' and n in special:
                value,needle=special[n];page=pages[p['title']];text=page['revisions'][0]['slots']['main']['*'];assert needle in text
                status='verified_capture_period';accepted=value;basis='Original uploader explicitly states photograph date in retained Commons original-description text'
                evidence.append(dict(source_url=captions['source_url'],checked_at=captions['checked_at'],content_sha256=captions['sha256'],locator=p['title']+' revisions.main original description/upload log',quote=needle,role='original_uploader_capture_date_statement',applicable_year=value))
            reviews.append(dict(id=wanted['id'],title=p['title'],photo_source_url=wanted['source_url'],status=status,photo_date=accepted,basis=basis,upload_date_used_as_photo_date=False,evidence=evidence,reason='本輪要求拍攝年度可核實；只有上傳日、檔名或缺值時暫停展示，不宣稱官方尚未提供照片。'))
    (BUNDLE/'photo_date_review.json').write_text(json.dumps(reviews,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(dict(reviewed=len(reviews),verified=sum(r['status']=='verified_capture_period' for r in reviews),held=sum(r['status']!='verified_capture_period' for r in reviews))))

if __name__=='__main__':main()
