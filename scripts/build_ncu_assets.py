"""Build NCU-only campus assets from an explicit human review, no network calls."""
from __future__ import annotations

import argparse
from datetime import UTC, datetime
import gzip
import hashlib
import json
from pathlib import Path
import shutil
from urllib.parse import urlsplit

from bs4 import BeautifulSoup
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]


def reviewed_license_url(source):
    """Retain the actual grant; never relabel a non-CC grant as CC or public domain."""
    name, url = source["license"], source["license_url"]
    if name == "Public domain":
        return source["page_url"]
    if name in {"FAL", "Copyrighted free use"}:
        proof = source.get("license_review", {})
        expected = {
            "FAL": "https://commons.wikimedia.org/wiki/Commons:Free_Art_License_1.3",
            "Copyrighted free use": source["page_url"] + "#Licensing",
        }[name]
        if url != expected or proof.get("status") != "reviewed_original_author_grant":
            raise ValueError("非CC授權須逐件核實原作者授權與確切條款。")
        if (proof.get("image_sha256") != source["sha256"]
                or proof.get("declaration", {}).get("url") != source["page_url"]):
            raise ValueError("授權查核須綁定同一照片位元及原始檔案頁。")
        for key in ("declaration", "terms", "upload_history"):
            evidence = proof.get(key, {})
            path = ROOT / evidence.get("file", "")
            data = path.read_bytes() if path.is_file() else b""
            if path.suffix == ".gz" and data:
                data = gzip.decompress(data)
            if not data or hashlib.sha256(data).hexdigest() != evidence.get("sha256"):
                raise ValueError("非CC授權原件或原作者上傳歷史缺失／SHA不符。")
        if not proof.get("author_identity_note") or not proof.get("grant_excerpt"):
            raise ValueError("非CC授權須記錄作者身份及原始授權原文。")
        if name == "FAL" and (not source.get("author_url") or not proof.get("attribution_requirements")):
            raise ValueError("本件FAL照片須附原作者全名、網站與署名條件。")
        if source.get("author_url") and urlsplit(source["author_url"]).scheme != "https":
            raise ValueError("攝影者網站必須是已核對的HTTPS連結。")
        return url
    if not url or urlsplit(url).hostname != "creativecommons.org":
        raise ValueError("可用授權需要原始CC連結或逐件核實的明示授權。")
    return url


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
        license_url = reviewed_license_url(source)
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
            "caption_zh": f"校園參考照片：{source.get('campus_caption_zh', source['title'].removeprefix('File:')).rstrip('。')}。作者：{author}；授權：{source['license']}；拍攝日期：{when}。圖示校區見原始來源，116錄取校區仍待確認；照片未作內容修改。",
        })
        if source.get("author_url"):
            rows[-1]["author_url"] = source["author_url"]
    output = output_path or ROOT / "src/exchange_info/official_data/ncu/campus-assets.json"
    output.write_text(json.dumps({"checked_at": review["checked_at"], "photos": rows}, ensure_ascii=False, indent=2) + "\n")
    credits = [{
        "school_name": row["school_name"], "country": row["country"], "status": row["status"],
        "local_path": row["image_url"], "image_source_url": row["image_source_url"],
        "official_page_url": row["image_page_url"], "license_name": row["license"],
        "license_url": row["license_url"], "note": row["caption_zh"], "checked_at": row["checked_at"],
        **({"author_url": row["author_url"]} if row.get("author_url") else {}),
    } for row in rows]
    (image_dir.parent / "ncu-school-images.json").write_text(
        json.dumps({"home_university": "國立中央大學", "schools": credits}, ensure_ascii=False, indent=2) + "\n")
    return rows


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("review", type=Path)
    args = parser.parse_args()
    print(f"Built {len(build(args.review))} reviewed, attributed campus photographs.")
