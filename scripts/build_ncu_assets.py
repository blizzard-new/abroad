"""Build NCU-only campus assets from an explicit human review, no network calls."""
from __future__ import annotations

import argparse
from datetime import UTC, datetime
import hashlib
import json
from pathlib import Path
import shutil
from urllib.parse import urlsplit

from bs4 import BeautifulSoup
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]


def build(review_path, *, output_path=None):
    review = json.loads(review_path.read_text())
    rows = []
    image_dir = ROOT / "src/exchange_info/static/assets/ncu-schools"
    image_dir.mkdir(parents=True, exist_ok=True)
    for source in review["rows"]:
        if source["review_status"] != "accepted_campus_reference":
            continue
        original = Path(source["file"])
        if not original.is_absolute():
            original = ROOT / original
        digest = hashlib.sha256(original.read_bytes()).hexdigest()
        if digest != source["sha256"]:
            raise ValueError("已檢視照片的原件SHA已改變，須重新檢視。")
        author = BeautifulSoup(source["author_html"], "html.parser").get_text(" ", strip=True)
        license_url = source["license_url"]
        if source["license"] == "Public domain":
            license_url = source["page_url"]  # exact declaration, not an inferred CC licence
        elif not license_url or urlsplit(license_url).hostname != "creativecommons.org":
            raise ValueError("可用授權需要原始CC連結或明列的public-domain聲明。")
        with Image.open(original) as opened:
            suffix = {"JPEG": ".jpg", "PNG": ".png"}.get(opened.format)
        if suffix is None:
            raise ValueError("校園照片須為已檢視的JPEG或PNG點陣照片。")
        target = image_dir / (digest[:20] + suffix)
        if original.resolve() != target.resolve():
            shutil.copyfile(original, target)  # Commons thumbnail bytes, no alteration
        metadata = source.get("commons_metadata")
        if metadata is None:
            metadata_path = review_path.parent / "assets-research" / source["id"] / "commons.json"
            metadata = json.loads(metadata_path.read_text())
        picture = next(pic for pic in metadata["query"]["pages"].values() if pic["title"] == source["title"])
        meta = picture["imageinfo"][0]["extmetadata"]
        when = source.get("photographed_at_original") or meta.get("DateTimeOriginal", {}).get("value", "原來源未列拍攝日期")
        when = BeautifulSoup(when, "html.parser").get_text(" ", strip=True)
        description = BeautifulSoup(source["description_html"], "html.parser").get_text(" ", strip=True)
        rows.append({
            "school_name": source["school_name"], "country": source["country"],
            "status": "verified", "image_url": "/static/assets/ncu-schools/" + target.name,
            "image_source_url": source["original_url"], "image_page_url": source["page_url"],
            "content_sha256": digest, "title_original": source["title"], "description_original": description,
            "photographed_at_original": when, "author": author, "license": source["license"],
            "license_url": license_url, "identity_source_url": source["identity_source_url"],
            "checked_at": source.get("reviewed_at", review["checked_at"]), "review_note": source["review_note"],
            "caption_zh": f"校園參考照片：{source['title'].removeprefix('File:')}。作者：{author}；授權：{source['license']}；拍攝日期：{when}。圖示校區見原始來源，116錄取校區仍待確認；照片未作內容修改。",
        })
    output = output_path or ROOT / "src/exchange_info/official_data/ncu/campus-assets.json"
    output.write_text(json.dumps({"checked_at": review["checked_at"], "photos": rows}, ensure_ascii=False, indent=2) + "\n")
    credits = [{
        "school_name": row["school_name"], "country": row["country"], "status": row["status"],
        "local_path": row["image_url"], "image_source_url": row["image_source_url"],
        "official_page_url": row["image_page_url"], "license_name": row["license"],
        "license_url": row["license_url"], "note": row["caption_zh"], "checked_at": row["checked_at"],
    } for row in rows]
    (image_dir.parent / "ncu-school-images.json").write_text(
        json.dumps({"home_university": "國立中央大學", "schools": credits}, ensure_ascii=False, indent=2) + "\n")
    return rows


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("review", type=Path)
    args = parser.parse_args()
    print(f"Built {len(build(args.review))} reviewed, attributed campus photographs.")
