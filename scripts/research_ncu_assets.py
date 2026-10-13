"""Discover source-bound NCU identity/coordinate/photo candidates for review.

Only unique registry country/name matches proceed. Shared domains never suffice. Campus or
department names are held for manual review. No candidate enters the platform
without a separate review manifest; raster image content needs visual review.
"""
from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import UTC, datetime
import hashlib
import json
from pathlib import Path
import re
import sys
import unicodedata
from urllib.parse import urlsplit
import requests

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT))
from exchange_info.school_identity import school_identity_key
from scripts.refresh_university_locations import COUNTRIES, domain, same_domain
from scripts.collect_ncu_completion_sources import HEADERS


def name_key(value):
    value = unicodedata.normalize("NFKD", value)
    return "".join(c.casefold() for c in value if c.isalnum() and not unicodedata.combining(c))


def identity_matches(spec, candidate):
    """A shared web domain can belong to a college/centre, never sufficient alone."""
    country = {**COUNTRIES, "摩納哥": "MC", "巴哈馬": "BS"}.get(spec["country"])
    aliases = spec.get("explicit_identity_aliases", [school_identity_key(spec["school_name"])])
    return (candidate.get("status") == "active" and "education" in candidate.get("types", [])
            and len(candidate.get("locations", [])) == 1
            and candidate["locations"][0]["geonames_details"]["country_code"] == country
            and any(name_key(alias["value"]) == name_key(expected)
                    for alias in candidate.get("names", []) for expected in aliases))


def get(url, path, *, params=None):
    response = requests.get(url, params=params, headers=HEADERS, timeout=(10, 20))
    path.write_bytes(response.content)
    record = {"url": response.url, "status": response.status_code,
              "sha256": hashlib.sha256(response.content).hexdigest(), "file": path.name,
              "checked_at": datetime.now(UTC).isoformat()}
    response.raise_for_status()
    return response.json(), record


def research(spec, output):
    folder = output / spec["id"]
    folder.mkdir(parents=True, exist_ok=True)
    result = {**spec, "checked_at": datetime.now(UTC).isoformat(), "sources": [], "status": "needs_review"}
    try:
        country = {**COUNTRIES, "摩納哥": "MC", "巴哈馬": "BS"}.get(spec["country"])
        expected_domain = domain(spec.get("url") or "")
        name = school_identity_key(spec["school_name"])
        if re.search(r"校區|分校|院級|校級|自費|school of|school of engineering", name, re.I):
            result["reason"] = "須逐一確認院級／分校／track；不自動選取全校代表位置。"
        else:
            queries = [{"query.advanced": "domains:" + expected_domain}] if expected_domain else []
            queries.append({"query": '"' + name + '"'})
            candidates = []
            for n, query in enumerate(queries):
                body, source = get("https://api.ror.org/v2/organizations", folder / f"ror-{n}.json", params=query)
                result["sources"].append(source)
                candidates = [row for row in body.get("items", []) if identity_matches(spec, row)]
                if len(candidates) == 1:
                    break
            if len(candidates) != 1:
                result["reason"] = f"未取得唯一國別與英文校名相符的ROR記錄（符合{len(candidates)}筆）。"
            else:
                candidate = candidates[0]
                result["identity"] = candidate
                ids = [row for row in candidate.get("external_ids", []) if row["type"] == "wikidata"]
                entity_id = (ids[0].get("preferred") or ids[0]["all"][0]) if ids else None
                if not entity_id or not re.fullmatch(r"Q\d+", entity_id):
                    result["reason"] = "已核對身份，但ROR未列Wikidata實體；需官方地圖或其他座標原件。"
                else:
                    body, source = get(f"https://www.wikidata.org/wiki/Special:EntityData/{entity_id}.json", folder / "wikidata.json")
                    result["sources"].append(source)
                    entity = body["entities"][entity_id]
                    result["wikidata_id"] = entity_id
                    result["entity_labels"] = entity.get("labels", {})
                    values = [row["mainsnak"]["datavalue"]["value"] for row in entity.get("claims", {}).get("P625", [])
                              if row.get("rank") != "deprecated" and "datavalue" in row.get("mainsnak", {})]
                    points = {(point["latitude"], point["longitude"]) for point in values if point.get("globe", "").endswith("Q2")}
                    if len(points) == 1:
                        lat, lon = next(iter(points))
                        result["coordinate_candidate"] = {"latitude": lat, "longitude": lon,
                            "precision": "representative", "source_url": f"https://www.wikidata.org/wiki/{entity_id}",
                            "identity_source_url": candidate["id"], "city": candidate["locations"][0]["geonames_details"]["name"]}
                    else:
                        result["coordinate_gap"] = f"P625有{len(points)}個不同地球位置；不選取城市中心或任意校區。"
                    pictures = [row["mainsnak"]["datavalue"]["value"] for row in entity.get("claims", {}).get("P18", [])
                                if row.get("rank") != "deprecated" and "datavalue" in row.get("mainsnak", {})]
                    if pictures:
                        body, source = get("https://commons.wikimedia.org/w/api.php", folder / "commons.json", params={
                            "action": "query", "format": "json", "titles": "|".join("File:" + name for name in pictures),
                            "prop": "imageinfo", "iiprop": "url|extmetadata|size", "iiurlwidth": 1200})
                        result["sources"].append(source)
                        result["photo_candidates"] = list(body.get("query", {}).get("pages", {}).values())
                    else:
                        result["photo_gap"] = "此已比對實體無P18校園照片；須查其他具可用授權的真實校園來源。"
                    result["status"] = "identity_candidate_for_review"
    except Exception as error:
        result["error"] = f"{type(error).__name__}: {error}"
    (folder / "review-candidate.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("spec", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    specs = json.loads(args.spec.read_text())
    args.output.mkdir(parents=True, exist_ok=True)
    with ThreadPoolExecutor(max_workers=3) as pool:
        futures = [pool.submit(research, spec, args.output) for spec in specs
                   if not (args.output / spec["id"] / "review-candidate.json").exists()]
        for n, future in enumerate(as_completed(futures), 1):
            record = future.result()
            print(f"{n}/{len(futures)} {record['id']} {record['status']} {record.get('error', '')[:90]}", flush=True)
    rows = [json.loads((args.output / spec["id"] / "review-candidate.json").read_text()) for spec in specs]
    (args.output / "manifest.json").write_text(json.dumps(rows, ensure_ascii=False, indent=2) + "\n")


if __name__ == "__main__":
    main()
