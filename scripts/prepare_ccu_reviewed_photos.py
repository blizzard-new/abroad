"""Materialize explicitly selected Commons images with intact attribution."""
from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json

from bs4 import BeautifulSoup
import requests

from fetch_ccu_completion_sources import BUNDLE, OUT, USER_AGENT, fetch


def prepare(page, selected):
    artifact_label = selected.get("artifact_label", "reviewed-campus")
    record_path = OUT / f"p{page}-{artifact_label}.json"
    if record_path.exists():
        return str(record_path.relative_to(BUNDLE))
    label = selected.get("metadata_label") or {
        "wikidata_p18": "commons", "wikidata_p18_license_page": "commons",
        "commons_alternatives": "commons-alternatives",
        "commons_exact_search": "commons-exact-search",
        "commons_category_selection": "commons-category-selected",
        "commons_campus_followup": "commons-campus-followup",
    }[selected["source"]]
    receipt = json.loads((OUT / f"p{page}-{label}.receipt.json").read_text())
    pages = json.loads((BUNDLE / receipt["bundled_file"]).read_text())["query"]["pages"]
    item = pages[str(selected["pageid"])] if "pageid" in selected else next(iter(pages.values()))
    info = item["imageinfo"][0]
    metadata = info["extmetadata"]

    def plain(key):
        return BeautifulSoup(metadata.get(key, {}).get("value", ""), "html.parser").get_text(" ", strip=True)

    artist = selected.get("artist") or plain("Artist")
    license_url = plain("LicenseUrl")
    evidence = [{
        "source_id": receipt["source_id"], "source_url": receipt["source_url"],
        "source_pages": [], "academic_year": "一般校園照片及授權；攝影日期另依來源",
        "checked_at": receipt["checked_at"], "content_hash": receipt["sha256"],
        "excerpt": json.dumps(metadata, ensure_ascii=False),
        "location_in_source": f"query.pages.{item['pageid']}.imageinfo[0].extmetadata",
    }]
    if selected["source"] == "wikidata_p18_license_page":
        licensing = json.loads((OUT / f"p{page}-commons-license-page.receipt.json").read_text())
        license_url = license_url or info["descriptionurl"] + "#Licensing"
        evidence.append({
            "source_id": licensing["source_id"], "source_url": licensing["source_url"],
            "source_pages": [], "academic_year": "Commons檔案頁實際授權條款",
            "checked_at": licensing["checked_at"], "content_hash": licensing["sha256"],
            "excerpt": (OUT / f"p{page}-commons-license-page.txt").read_text(),
            "location_in_source": "File description, author and Licensing section",
        })
    if not all([artist, plain("LicenseShortName"), license_url, info.get("descriptionurl")]):
        raise ValueError(f"Incomplete attribution p{page}")
    image_url = info.get("thumburl") or info["url"]
    response = requests.get(image_url, headers={"User-Agent": USER_AGENT}, timeout=30)
    response.raise_for_status()
    raw_path = OUT / f"p{page}-{artifact_label}.image"
    raw_path.write_bytes(response.content)
    result = {
        "artist": artist, "license_name": plain("LicenseShortName"), "license_url": license_url,
        "campus_caption": plain("ImageDescription") or item["title"],
        "source_page_url": info["descriptionurl"], "image_source_url": image_url,
        "file_title": item["title"], "candidate_file": str(raw_path.relative_to(BUNDLE)),
        "sha256": hashlib.sha256(response.content).hexdigest(),
        "checked_at": datetime.now(timezone.utc).isoformat(), "evidence": evidence,
    }
    record_path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    return str(record_path.relative_to(BUNDLE))


def main():
    review_path = BUNDLE / "campus-photo-review.json"
    review = json.loads(review_path.read_text())
    for page, selected in review["selected"].items():
        selected["reviewed_photo_record"] = prepare(page, selected)
        review_path.write_text(json.dumps(review, ensure_ascii=False, indent=2) + "\n")
        print(page, selected["reviewed_photo_record"], flush=True)


if __name__ == "__main__":
    main()
