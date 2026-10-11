"""Download reviewed original campus photos; retain attribution and exact licenses."""
import gzip
from tku_capture_io import read_bytes, exists, captures
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit

import requests
from tku_baseline_assets import existing_ritsumeikan_photo
from bs4 import BeautifulSoup
from PIL import Image

ROOT=Path(__file__).resolve().parents[1]
BUNDLE=ROOT/"src/exchange_info/official_data/tku"
ASSETS=ROOT/"src/exchange_info/static/assets/tku-campuses"
PICKS={
    343:("File:Sathyabama Administration building.png","Jeppiar Nagar校園行政大樓"),
    342:("File:MU panoramic.JPG","Manipal校園行政大樓（歷史照片）"),
    336:("File:University of Trier Main Campus.jpg","Trier主校區全景（歷史照片）"),
    341:("File:Chennai Institute of Technology.jpg","清奈理工學院校景"),
    340:("File:Finster Hall, Ateneo de Davao University (2007).jpg","Jacinto校區Finster Hall（2007照片）"),
    338:("File:Mapua (Intramuros, Manila)(2018-02-07) (cropped).jpg","Intramuros校區（2018照片，Commons原檔已裁切）"),
    337:("File:City University of Macau 04.jpg","澳門城市大學行政大樓（2016照片；不套用GDC校區）"),
    329:("File:Las cuatro columnas en la UAB.jpg","Bellaterra校區四柱校景"),
    327:("File:Cardiff University main building.jpg","卡地夫大學主建築（Cathays Park）"),
}
MANUAL=[
    (274,"https://commons.wikimedia.org/wiki/File:Seikei_University_(16).jpg","https://upload.wikimedia.org/wikipedia/commons/0/07/Seikei_University_%2816%29.jpg","李維俊(alen2864)","CC BY-SA 4.0","https://creativecommons.org/licenses/by-sa/4.0/","成蹊大學東京都校園（2017/4/8）","2017-04-08"),
    (34,"https://commons.wikimedia.org/wiki/File:Nagasaki_University_of_Foreign_Studies.JPG","https://upload.wikimedia.org/wikipedia/commons/d/d5/Nagasaki_University_of_Foreign_Studies.JPG","Ackeyyama","CC BY-SA 3.0","https://creativecommons.org/licenses/by-sa/3.0/","長崎外國語大學横尾校園（2013照片）","2013-04-22"),
    (30,"https://commons.wikimedia.org/wiki/File:Uec_koudou.jpg","https://upload.wikimedia.org/wikipedia/commons/a/a5/Uec_koudou.jpg","Kaoruitoh（Japanese Wikipedia）","Public domain","https://commons.wikimedia.org/wiki/File:Uec_koudou.jpg#Licensing","電氣通信大學調布校區講堂（歷史照片）","2006-04-05 original upload"),
]


def plain(value):return BeautifulSoup(value or "","html.parser").get_text(" ",strip=True)


def main():
    ASSETS.mkdir(parents=True,exist_ok=True)
    schools={r["id"]:r for r in map(json.loads,(BUNDLE/"partner_census.jsonl").read_text().splitlines())}
    reviewed_path=BUNDLE/"campus_asset_visual_review.json"
    visual_reviews=json.loads(reviewed_path.read_text()) if reviewed_path.exists() else {}
    records=[]
    for number,(title,caption) in PICKS.items():
        capture=json.loads(gzip.decompress(read_bytes(BUNDLE/"commons_campus_candidates"/f"tku-sister-{number}.json.gz")))
        page=next(p for p in capture["response"]["query"]["pages"].values() if p["title"]==title)
        info=page["imageinfo"][0];meta=info["extmetadata"]
        records.append(dict(id=f"tku-sister-{number}",source_url=info["descriptionurl"],image_source_url=info["url"],
            author=plain(meta.get("Artist",{}).get("value")),license=plain(meta["LicenseShortName"]["value"]),
            license_url=meta.get("LicenseUrl",{}).get("value") or info["descriptionurl"]+"#Licensing",
            caption=caption,photo_date=plain(meta.get("DateTimeOriginal",{}).get("value")),
            identity_quote=plain(meta["ImageDescription"]["value"]),license_capture_url=capture["source_url"],checked_at=capture["checked_at"]))
    for number,page,url,author,license,license_url,caption,date in MANUAL:
        records.append(dict(id=f"tku-sister-{number}",source_url=page,image_source_url=url,author=author,
            license=license,license_url=license_url,caption=caption,photo_date=date,
            identity_quote=caption,license_capture_url=page+"#Licensing",checked_at=datetime.now(timezone.utc).isoformat(),
            review_method="Commons page Summary and Licensing read via web source; author and original-file link checked"))
    for record in records:
        record['license_url_original']=record['license_url']
        if record['license_url'].startswith('http://creativecommons.org/'):
            record['license_url']=record['license_url'].replace('http://','https://',1)
        school=schools[record["id"]]
        record.update(school_name=school["school_name"],country=school["country"],identity_source_url=school["directory_url"],
            identity_address=school["directory_address"],applicable_year="campus photograph at stated historic date; not current exchange-campus allocation",
            transformations="none; original downloaded bytes retained",review_status="metadata_reviewed_visual_pending")
        ext=Path(urlsplit(record["image_source_url"]).path).suffix.lower()
        path=ASSETS/(record["id"]+ext)
        if not path.exists():
            try:
                response=requests.get(record["image_source_url"],timeout=(8,30),headers={"User-Agent":"UniWayTKUDataAudit/1.0 (https://github.com/blizzard-new/abroad; public academic reference audit)"});response.raise_for_status();path.write_bytes(response.content)
            except requests.RequestException as exc:
                record.update(review_status="download_failed",download_error=str(exc),download_http_status=response.status_code if 'response' in locals() else None)
                continue
        with Image.open(path) as image:
            image.verify()
        with Image.open(path) as image:
            record.update(width=image.width,height=image.height)
        record.update(local_path="/static/assets/tku-campuses/"+path.name,sha256=hashlib.sha256(path.read_bytes()).hexdigest(),bytes=path.stat().st_size)
        review=visual_reviews.get(record["id"])
        if review and review["sha256"]==record["sha256"]:
            record.update(review_status="verified_asset",visual_review=review)
    records.append(existing_ritsumeikan_photo())
    reviews=BUNDLE/'reused_asset_review.json'
    if reviews.exists():
        present={r['id'] for r in records}
        records.extend(r['accepted_photo'] for r in json.loads(reviews.read_text()) if 'accepted_photo' in r and r['id'] not in present)
    candidates=BUNDLE/'new_photo_candidates.json';visual=BUNDLE/'new_photo_visual_review.json'
    if candidates.exists() and visual.exists():
        decisions=json.loads(visual.read_text());present={r['id'] for r in records}
        for photo in json.loads(candidates.read_text()):
            review=decisions.get(photo['id'])
            if photo['id'] in present or not review or review['result']!='pass' or review['sha256']!=photo.get('sha256'):continue
            assert review['sha256']==photo['sha256']
            file=ROOT/'src/exchange_info'/photo['local_path'].removeprefix('/')
            assert hashlib.sha256(file.read_bytes()).hexdigest()==photo['sha256']
            if review.get('metadata_conflict'):
                photo.update(source_metadata_conflict=review['metadata_conflict'],caption='The Saigon International University — Lewis Campus（照片招牌）；Commons檔名Fleming與招牌矛盾保留，不推定為Fleming。')
            if review.get('campus_scope'):photo['campus_pair_scope']=review['campus_scope']
            photo.update(review_status='verified_asset',visual_review=review,acquisition_status='new_reviewed_licensed_download')
            records.append(photo)
    (BUNDLE/"campus_asset_manifest.json").write_text(json.dumps(records,ensure_ascii=False,indent=2)+"\n")
    print(json.dumps(dict(photos=len(records),downloaded=sum('local_path' in r for r in records),bytes=sum(r.get("bytes",0) for r in records),visual_review_required=True)))


if __name__=="__main__":main()
