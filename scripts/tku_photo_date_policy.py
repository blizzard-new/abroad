"""TKU-only capture-year gate; upload dates never establish a photo period."""
import json
import re
from urllib.parse import unquote
from bs4 import BeautifulSoup
from tku_capture_io import BUNDLE


def file_title(url):
    return unquote(url.split('/wiki/File:', 1)[-1]).replace('_', ' ').split('#', 1)[0]


def reviewed_date(info):
    value = info.get('extmetadata', {}).get('DateTimeOriginal', {}).get('value', '')
    original = BeautifulSoup(value, 'html.parser').get_text(' ', strip=True)
    camera = next((str(x['value']) for x in info.get('metadata', []) if x['name'] == 'DateTimeOriginal'), '')
    years = set(re.findall(r'\b(?:18|19|20)\d{2}\b', original))
    camera_years = set(re.findall(r'\b(?:18|19|20)\d{2}\b', camera))
    if re.search('upload', original, re.I):
        years = set()
    if years and camera_years and not years.intersection(camera_years):
        return 'conflicting_capture_years_requires_confirmation', None, original, camera
    if years or camera_years:
        return 'verified_capture_period', original if years else camera, original, camera
    return 'capture_year_not_verified', None, original, camera


def apply_capture_year_policy(records):
    reviews = {(r['id'], file_title(r['photo_source_url'])): r for r in json.loads((BUNDLE/'photo_date_review.json').read_text())}
    batches = json.loads((BUNDLE/'commons_asset_batches.json').read_text())
    accepted, held = [], []
    for record in records:
        title = file_title(record['source_url'])
        review = reviews.get((record['id'], title))
        if review is None:
            source_pages = [(s, p) for s in batches for p in s.get('response', {}).get('query', {}).get('pages', {}).values()
                                if s.get('institution_id') == record['id'] and p.get('title', '').removeprefix('File:').replace('_', ' ') == title
                                and p.get('imageinfo')]
            source_pages.sort(key=lambda pair: (any(x.get('name') == 'DateTimeOriginal' for x in pair[1]['imageinfo'][0].get('metadata', [])),
                                               pair[0].get('sha256') == record.get('metadata_source_sha256')), reverse=True)
            source_page = source_pages[0] if source_pages else None
            if source_page:
                source, page = source_page
                status, date, original, camera = reviewed_date(page['imageinfo'][0])
                review = dict(id=record['id'], title=page['title'], status=status, photo_date=date,
                    upload_date_used_as_photo_date=False, evidence=[dict(source_url=source['source_url'],
                    content_sha256=source['sha256'], checked_at=source['checked_at'],
                    locator=page['title']+' imageinfo.extmetadata.DateTimeOriginal / imageinfo.metadata.DateTimeOriginal',
                    quote=json.dumps(dict(information_date=original,camera_exif_date_time_original=camera),ensure_ascii=False),
                    applicable_year=date or 'capture year not verified',role='licensed_photo_capture_period')])
            else:
                review = dict(status='capture_year_not_verified', reason='Selected file has no retained capture-period metadata review.')
        if review['status'] != 'verified_capture_period':
            held.append(dict(id=record['id'], school_name=record.get('school_name'), source_url=record['source_url'],
                sha256=record.get('sha256'), status=review['status'], evidence=review.get('evidence', []),
                reason='拍攝年份未核實或來源矛盾，依本輪要求停止展示；舊檔與查核歷史保留。不能以上傳日或檔名補值。'))
            continue
        record.update(photo_date=review['photo_date'], capture_year_status=review['status'],
                      photo_date_evidence=review['evidence'], upload_date_used_as_photo_date=False)
        accepted.append(record)
    (BUNDLE/'photo_date_holds.json').write_text(json.dumps(held,ensure_ascii=False,indent=2)+'\n')
    return accepted
