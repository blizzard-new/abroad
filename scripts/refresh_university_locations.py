"""Offline enrichment of REAL partner records; unknown identities stay unlocated.

Input: JSON array of school_name, country, website and optional city/research_name.
Output: JSONL suitable for review, then inclusion in the public location catalog.
No browser or API request invokes this script. Successful rows are resumable.
"""
from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
import json
import math
from pathlib import Path
import re
import time
from urllib.parse import urlsplit

import requests

from exchange_info.university_locations import UniversityLocation, location_key

COUNTRIES = {
    "臺灣": "TW", "台灣": "TW", "日本": "JP", "韓國": "KR", "南韓": "KR", "中國": "CN", "大陸地區": "CN", "中國大陸": "CN",
    "香港": "HK", "澳門": "MO", "美國": "US", "加拿大": "CA", "紐西蘭": "NZ", "澳洲": "AU", "澳大利亞": "AU",
    "英國": "GB", "法國": "FR", "德國": "DE", "荷蘭": "NL", "比利時": "BE", "義大利": "IT", "西班牙": "ES", "葡萄牙": "PT",
    "瑞典": "SE", "挪威": "NO", "丹麥": "DK", "芬蘭": "FI", "瑞士": "CH", "奧地利": "AT", "捷克": "CZ", "波蘭": "PL",
    "匈牙利": "HU", "俄羅斯": "RU", "土耳其": "TR", "愛爾蘭": "IE", "立陶宛": "LT", "拉脫維亞": "LV", "斯洛伐克": "SK",
    "羅馬尼亞": "RO", "克羅埃西亞": "HR", "斯洛維尼亞": "SI", "馬來西亞": "MY", "新加坡": "SG", "泰國": "TH",
    "越南": "VN", "印尼": "ID", "印度尼西亞": "ID", "印度": "IN", "菲律賓": "PH", "柬埔寨": "KH", "蒙古": "MN",
    "巴西": "BR", "墨西哥": "MX", "智利": "CL", "阿根廷": "AR", "哥倫比亞": "CO", "南非": "ZA", "以色列": "IL",
    "哈薩克": "KZ", "孟加拉": "BD", "摩洛哥": "MA", "緬甸": "MM", "阿爾巴尼亞": "AL",
}
BRANCH = re.compile(r"校區|分校|研究所|研究科|學部|大學.*學院|school of|college of|faculty of|graduate school|campus", re.I)


def domain(url):
    host = (urlsplit(url if "://" in url else "https://" + url).hostname or "").lower().removeprefix("www.")
    parts = host.split(".")
    # The catalog's institutional domains use these public education suffixes.
    # Match alternate language/OIA subdomains without confusing two universities.
    if len(parts) > 3 and parts[-2] in {"edu", "ac"} and len(parts[-1]) == 2:
        return ".".join(parts[-3:])
    return host


def same_domain(left, right):
    return bool(left and right and (left == right or left.endswith("." + right) or right.endswith("." + left)))


def fetch_json(url, **kwargs):
    for attempt in range(3):
        response = requests.get(url, timeout=25, headers={"User-Agent": "UniWay-Exchange-Map/1.0 (university coordinate research)"}, **kwargs)
        if response.status_code in (429, 502, 503, 504) and attempt < 2:
            time.sleep(2 ** (attempt + 1))
            continue
        response.raise_for_status()
        return response.json()


def verified_candidate(row, candidates):
    """A unique official-domain AND country match is required; no fuzzy names."""
    expected_domain = domain(row.get("website") or "")
    expected_country = COUNTRIES.get(row.get("country"))
    if not expected_domain or not expected_country or BRANCH.search(row["school_name"]):
        return None
    matches = []
    for candidate in candidates:
        locations = candidate.get("locations", [])
        domains = candidate.get("domains", []) + [domain(link["value"]) for link in candidate.get("links", []) if link["type"] == "website"]
        if (candidate.get("status") == "active" and "education" in candidate.get("types", [])
            and len(locations) == 1 and locations[0]["geonames_details"]["country_code"] == expected_country
            and any(same_domain(expected_domain, d) for d in domains)):
            matches.append(candidate)
    return matches[0] if len(matches) == 1 else None


def enrich(row):
    pending = UniversityLocation(school_name=row["school_name"], country=row.get("country"), city=row.get("city"))
    if BRANCH.search(row["school_name"]):
        return pending.model_copy(update={"geocode_status": "needs_review", "note": "需確認院系或分校的實際交換校區。"})
    try:
        host = domain(row.get("website") or "")
        if not host:
            return pending
        results = fetch_json("https://api.ror.org/v2/organizations", params={"query.advanced": 'domains:' + host})
        candidate = verified_candidate(row, results.get("items", []))
        if not candidate:
            # Domain indexes do not include every alternate official hostname.
            # A name search is only candidate discovery; strict domain/country
            # checks below still decide whether a result can be used.
            query = row.get("research_name") or re.sub(r"^[^A-Za-z]+", "", row["school_name"]) or row["school_name"]
            results = fetch_json("https://api.ror.org/v2/organizations", params={"query": '"' + query + '"'})
            candidate = verified_candidate(row, results.get("items", []))
        if not candidate:
            return pending
        ids = [x for x in candidate.get("external_ids", []) if x["type"] == "wikidata"]
        entity_id = (ids[0].get("preferred") or ids[0]["all"][0]) if ids else None
        if not entity_id or not re.fullmatch(r"Q\d+", entity_id):
            return pending
        evidence = fetch_json(f"https://www.wikidata.org/wiki/Special:EntityData/{entity_id}.json")["entities"][entity_id]
        coordinates = [x["mainsnak"]["datavalue"]["value"] for x in evidence.get("claims", {}).get("P625", []) if x.get("rank") != "deprecated" and "datavalue" in x.get("mainsnak", {})]
        # Multiple P625 statements may denote different campuses; never choose silently.
        points = {(p["latitude"], p["longitude"]) for p in coordinates if p.get("globe", "").endswith("Q2")}
        if len(points) != 1:
            return pending
        lat, lng = next(iter(points))
        city = candidate["locations"][0]["geonames_details"]
        # Reject conflicting locations (> 100 km from the independently matched registry city).
        dlat = math.radians(lat - city["lat"])
        dlng = math.radians(lng - city["lng"])
        a = math.sin(dlat / 2) ** 2 + math.cos(math.radians(lat)) * math.cos(math.radians(city["lat"])) * math.sin(dlng / 2) ** 2
        if 6371 * 2 * math.asin(min(1, math.sqrt(a))) > 100:
            return pending
        return UniversityLocation(
            school_name=row["school_name"], country=row.get("country"), city=city["name"], latitude=lat, longitude=lng,
            geocode_status="verified", geocoded_at=datetime.now(timezone.utc),
            source_url=f"https://www.wikidata.org/wiki/{entity_id}", identity_source_url=candidate["id"],
            note="校級代表位置：官方網域及國家已與 ROR 比對，座標來源為 Wikidata P625；實際交換校區以錄取通知為準。",
        )
    except (requests.RequestException, KeyError, ValueError, TypeError):
        return pending.model_copy(update={"note": "資料來源無法確認或查詢失敗；保留待確認，不推估座標。"})


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--retry-pending", action="store_true")
    args = parser.parse_args()
    rows = json.loads(args.input.read_text(encoding="utf-8"))
    if isinstance(rows, dict):
        rows = rows["partner_universities"]
    existing = {}
    if args.output.exists():
        for line in args.output.read_text(encoding="utf-8").splitlines():
            r = UniversityLocation.model_validate_json(line)
            existing[location_key(r.school_name, r.country)] = r
    todo = [r for r in rows if location_key(r["school_name"], r.get("country")) not in existing or (args.retry_pending and existing[location_key(r["school_name"], r.get("country"))].geocode_status != "verified")]
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with ThreadPoolExecutor(max_workers=3) as pool:
        for index, future in enumerate(as_completed([pool.submit(enrich, row) for row in todo]), 1):
            record = future.result()
            existing[location_key(record.school_name, record.country)] = record
            # Atomic, resumable catalog write; the script output is chosen by the operator.
            temp = args.output.with_suffix(".tmp")
            temp.write_text("".join(r.model_dump_json() + "\n" for _, r in sorted(existing.items())), encoding="utf-8")
            temp.replace(args.output)
            print(f"Processed {index}/{len(todo)}: {record.geocode_status}", flush=True)
    print(f"Verified: {sum(r.geocode_status == 'verified' for r in existing.values())}; total: {len(existing)}")


if __name__ == "__main__":
    main()
