"""Discover CCU campus candidates; photographs require a separate visual review.

ROR city coordinates are identity corroboration only and are NEVER campus points.
Domain, exact reviewed names and country must all match. Faculty agreements cannot
inherit the parent university's point or photograph automatically.
"""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import re
import unicodedata
from urllib.parse import urlencode, urlsplit

from bs4 import BeautifulSoup
import requests

from fetch_ccu_completion_sources import BUNDLE, OUT, USER_AGENT, fetch

FACULTY_SCOPES = {74, 88, 103, 104, 111}


def normalize(value):
    return re.sub(r"[^a-z0-9]", "", unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode().lower())


def domain(value):
    return (urlsplit(value if "://" in value else "https://" + value).hostname or "").removeprefix("www.").lower()


def same_domain(left, right):
    def institution_domain(value):
        pieces = value.split(".")
        education_suffixes = {"ac.jp", "ac.kr", "ac.th", "ac.uk", "edu.tw", "edu.cn", "edu.my", "edu.ph"}
        if ".".join(pieces[-2:]) in education_suffixes:
            return ".".join(pieces[-3:])
        return value
    left, right = institution_domain(left), institution_domain(right)
    return bool(left and right and (left == right or left.endswith("." + right) or right.endswith("." + left)))


def candidates(row):
    results = {}
    for label in ["ror", "ror-name"]:
        path = OUT / f"p{row['ccu_page']}-{label}.json"
        if not path.exists():
            continue
        for candidate in json.loads(path.read_text()).get("items", []):
            if (candidate.get("status") != "active" or "education" not in candidate.get("types", [])
                    or len(candidate.get("locations", [])) != 1
                    or candidate["locations"][0]["geonames_details"]["country_code"] != row["country_code"]):
                continue
            names = {normalize(name["value"]) for name in candidate["names"]}
            if normalize(row["canonical_name"]) not in names:
                continue
            domains = [domain(value) for value in candidate.get("domains", [])]
            domains += [domain(value["value"]) for value in candidate.get("links", []) if value["type"] == "website"]
            if not any(same_domain(domain(row["website"]), value) for value in domains):
                continue
            results[candidate["id"]] = (candidate, label)
    return list(results.values())


def evidence(receipt, excerpt, *, applicability="校園／機構身份資料；非2027春季接收政策"):
    return {"source_id": receipt["source_id"], "source_url": receipt["source_url"],
            "source_pages": [], "excerpt": excerpt, "academic_year": applicability,
            "checked_at": receipt["checked_at"], "content_hash": receipt["sha256"]}


def distance(first, second):
    lat, lng = first
    other_lat, other_lng = second
    a = math.sin(math.radians(lat - other_lat) / 2) ** 2 + math.cos(math.radians(lat)) * math.cos(math.radians(other_lat)) * math.sin(math.radians(lng - other_lng) / 2) ** 2
    return 6371 * 2 * math.asin(min(1, math.sqrt(a)))


def collect(row):
    page = row["ccu_page"]
    result = {"ccu_page": page, "school_name": row["school_name"], "country": row["country"],
              "mother_identity_source_url": row["mother_identity_source_url"], "source_pages": row["source_pages"],
              "coordinates": {"status": "missing", "value": None, "evidence": [], "reason": "未取得唯一的校名、官方網域及國家一致的機構座標來源；不使用ROR城市中心。"},
              "photo": {"status": "missing", "value": None, "evidence": [], "reason": "未取得對應校園且有明確重用授權的照片。"}}
    matches = candidates(row)
    result["identity_candidate_count"] = len(matches)
    if len(matches) != 1:
        return result
    candidate, ror_label = matches[0]
    result["ror_id"] = candidate["id"]
    ror_receipt = json.loads((OUT / f"p{page}-{ror_label}.receipt.json").read_text())
    ror_evidence = evidence(ror_receipt, json.dumps({"id": candidate["id"], "names": candidate["names"], "domains": candidate["domains"], "country_code": row["country_code"]}, ensure_ascii=False))
    ids = [identifier for identifier in candidate.get("external_ids", []) if identifier["type"] == "wikidata"]
    if not ids:
        result["coordinates"]["reason"] = "官方網域、名稱、國家已比對ROR；沒有Wikidata機構點，ROR城市座標不可代替校園。"
        return result
    entity_id = ids[0].get("preferred") or ids[0]["all"][0]
    if not re.fullmatch(r"Q\d+", entity_id):
        return result
    result["wikidata_id"] = entity_id
    receipt = fetch(page, "wikidata", f"https://www.wikidata.org/wiki/Special:EntityData/{entity_id}.json")
    if receipt.get("error"):
        result["coordinates"]["reason"] = receipt["error"]
        return result
    entity = json.loads((BUNDLE / receipt["bundled_file"]).read_text())["entities"][entity_id]
    claims = entity.get("claims", {})
    points = [statement["mainsnak"]["datavalue"]["value"] for statement in claims.get("P625", []) if statement.get("rank") != "deprecated" and "datavalue" in statement.get("mainsnak", {})]
    unique = {(point["latitude"], point["longitude"]) for point in points if point.get("globe", "").endswith("Q2")}
    city = candidate["locations"][0]["geonames_details"]
    result["coordinate_candidate_count"] = len(unique)
    if page in FACULTY_SCOPES:
        result["coordinates"]["reason"] = "協議為院系／機構群範圍；母機構Wikidata位置不能代替指定接收校區，需逐址核對。"
    elif len(unique) == 1 and distance(next(iter(unique)), (city["lat"], city["lng"])) < 100:
        latitude, longitude = next(iter(unique))
        result["coordinates"] = {
            "status": "needs_identity_review", "value": {"school_name": row["school_name"], "country": row["country"],
                "city": city["name"], "latitude": latitude, "longitude": longitude,
                "geocode_status": "needs_review", "geocoded_at": receipt["checked_at"],
                "source_url": f"https://www.wikidata.org/wiki/{entity_id}", "identity_source_url": candidate["id"],
                "precision": "representative", "note": "機構代表位置；精確名稱、官方網域及國家已交叉比對。多校區實際分配須以接待校通知為準；未用ROR城市中心。"},
            "reason": "取得單一地球座標；仍需核對官方校園身份及位置。",
            "evidence": [ror_evidence, evidence(receipt, json.dumps(claims.get("P625", []), ensure_ascii=False))],
        }
    images = [statement["mainsnak"]["datavalue"]["value"] for statement in claims.get("P18", []) if statement.get("rank") != "deprecated" and "datavalue" in statement.get("mainsnak", {})]
    if page in FACULTY_SCOPES:
        result["photo"]["reason"] = "院系／機構群協議，不能直接以母機構圖片充指定校園照片。"
        return result
    if not images:
        return result
    title = "File:" + images[0]
    commons_url = "https://commons.wikimedia.org/w/api.php?" + urlencode({"action": "query", "format": "json", "prop": "imageinfo", "iiprop": "url|extmetadata|size", "iiurlwidth": 1200, "titles": title})
    photo_receipt = fetch(page, "commons", commons_url)
    if photo_receipt.get("error"):
        result["photo"]["reason"] = photo_receipt["error"]
        return result
    pages = json.loads((BUNDLE / photo_receipt["bundled_file"]).read_text()).get("query", {}).get("pages", {})
    infos = [info for item in pages.values() for info in item.get("imageinfo", [])]
    if not infos:
        return result
    info = infos[0]
    metadata = info.get("extmetadata", {})
    def plain(key):
        return BeautifulSoup(metadata.get(key, {}).get("value", ""), "html.parser").get_text(" ", strip=True)
    license_name, license_url = plain("LicenseShortName"), plain("LicenseUrl")
    result["photo"]["candidate"] = {"file_title": title, "artist": plain("Artist"), "description": plain("ImageDescription"), "license_name": license_name, "license_url": license_url, "copyrighted": plain("Copyrighted"), "source_page_url": info.get("descriptionurl"), "image_source_url": info.get("thumburl") or info["url"], "width": info.get("thumbwidth") or info["width"], "height": info.get("thumbheight") or info["height"]}
    result["photo"]["evidence"] = [ror_evidence, evidence(photo_receipt, json.dumps(metadata, ensure_ascii=False))]
    if not (license_name.startswith(("CC BY", "CC0")) or license_name == "Public domain"):
        result["photo"]["reason"] = "授權不在已核對的可重用授權範圍；保留候選但不刊登。"
        return result
    if not license_url or not plain("Artist"):
        result["photo"]["reason"] = "授權連結或作者不完整；不能刊登。"
        return result
    try:
        response = requests.get(result["photo"]["candidate"]["image_source_url"], headers={"User-Agent": USER_AGENT}, timeout=25)
        response.raise_for_status()
        path = OUT / f"p{page}-campus-candidate.image"
        path.write_bytes(response.content)
        result["photo"].update(status="needs_visual_review", reason="授權、作者與來源已取得；須檢視實際影像和校區描述，不能以P18直接當作校景。",
                               value={"candidate_file": str(path.relative_to(BUNDLE)), "sha256": hashlib.sha256(response.content).hexdigest(), "checked_at": datetime.now(timezone.utc).isoformat()})
    except requests.RequestException as error:
        result["photo"]["reason"] = type(error).__name__ + ": " + str(error)
    return result


def main():
    rows = json.loads((BUNDLE / "completion-targets.json").read_text())
    output = BUNDLE / "campus-assets-candidates.json"
    results = []
    with ThreadPoolExecutor(max_workers=4) as pool:
        for future in as_completed([pool.submit(collect, row) for row in rows]):
            result = future.result()
            results.append(result)
            output.write_text(json.dumps({"schools": sorted(results, key=lambda row: row["ccu_page"])}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            print(f"{len(results)}/{len(rows)} p{result['ccu_page']} {result['coordinates']['status']} {result['photo']['status']}", flush=True)


if __name__ == "__main__":
    main()
