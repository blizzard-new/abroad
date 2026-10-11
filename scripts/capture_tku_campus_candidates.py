"""Collect CC0 Wikidata identity/coordinate and Commons license candidates.

Nothing from this script is automatically a verified exchange-campus location
or photo. Keep candidate identity, country, official domain and campus distinct.
"""
from __future__ import annotations

import concurrent.futures
import gzip
from tku_capture_io import read_bytes, exists, captures
import hashlib
import json
import threading
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit

import requests

ROOT = Path(__file__).resolve().parents[1]
BUNDLE = ROOT / "src/exchange_info/official_data/tku"
STORE = BUNDLE / "campus_source_candidates"
HEADERS = {"User-Agent": "UniWayTKUReference/1.0 (public licensed campus source audit)"}
RATE_LIMITED = threading.Event()


def api(endpoint, params):
    url = requests.Request("GET", endpoint, params=params).prepare().url
    key = hashlib.sha256(url.encode()).hexdigest()[:24]
    path = STORE / (key + ".json.gz")
    if exists(path):
        return json.loads(gzip.decompress(read_bytes(path)))
    record = dict(source_url=url, checked_at=datetime.now(timezone.utc).isoformat())
    if RATE_LIMITED.is_set():
        record["error"] = "not_requested_after_service_rate_limit; resume only after backoff"
        return record
    try:
        response = requests.get(url, headers=HEADERS, timeout=(8, 30))
        record.update(http_status=response.status_code, sha256=hashlib.sha256(response.content).hexdigest())
        if response.status_code == 429:
            RATE_LIMITED.set()
        response.raise_for_status()
        record["response"] = response.json()
    except Exception as exc:
        record["error"] = f"{type(exc).__name__}: {exc}"
    STORE.mkdir(parents=True, exist_ok=True)
    path.write_bytes(gzip.compress(json.dumps(record, ensure_ascii=False).encode(), mtime=0))
    return record


def values(entity, prop):
    return [c["mainsnak"]["datavalue"]["value"] for c in entity.get("claims", {}).get(prop, [])
            if c.get("rank") != "deprecated" and "datavalue" in c["mainsnak"]]


def domain(url):
    return urlsplit(url).netloc.casefold().removeprefix("www.")


def main():
    STORE.mkdir(parents=True, exist_ok=True)
    rows = json.loads((BUNDLE / "full_census_audit.json").read_text())["schools"]
    def search(row):
        term = row.get("english_name") or row["school_name"]
        return api("https://www.wikidata.org/w/api.php", dict(action="wbsearchentities", search=term, language="en", format="json", limit=3))
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
        searches = list(pool.map(search, rows))
    qids = sorted({hit["id"] for result in searches for hit in result.get("response", {}).get("search", [])})
    entities = {}
    for start in range(0, len(qids), 40):
        result = api("https://www.wikidata.org/w/api.php", dict(action="wbgetentities", ids="|".join(qids[start:start+40]), format="json", languages="en|zh|zh-tw|ja", props="labels|aliases|claims|descriptions|sitelinks"))
        entities.update(result.get("response", {}).get("entities", {}))
    countries = sorted({v["id"] for e in entities.values() for v in values(e, "P17") if isinstance(v, dict)})
    labels = {}
    for start in range(0, len(countries), 40):
        result = api("https://www.wikidata.org/w/api.php", dict(action="wbgetentities", ids="|".join(countries[start:start+40]), format="json", languages="en|zh|zh-tw", props="labels|aliases"))
        labels.update(result.get("response", {}).get("entities", {}))
    images = sorted({"File:"+name for e in entities.values() for name in values(e, "P18") if isinstance(name, str)})
    imageinfo = {}
    for start in range(0, len(images), 25):
        result = api("https://commons.wikimedia.org/w/api.php", dict(action="query", titles="|".join(images[start:start+25]), format="json", prop="imageinfo", iiprop="url|extmetadata|sha1", iiurlwidth=640))
        for page in result.get("response", {}).get("query", {}).get("pages", {}).values():
            imageinfo[page["title"]] = {**page, "capture_url":result["source_url"], "checked_at":result["checked_at"]}
    result_rows = []
    for row, search_result in zip(rows, searches):
        candidates = []
        for hit in search_result.get("response", {}).get("search", []):
            entity = entities.get(hit["id"], {})
            websites = values(entity, "P856")
            country_ids = [v["id"] for v in values(entity, "P17") if isinstance(v, dict)]
            candidates.append(dict(qid=hit["id"], labels=entity.get("labels", {}), aliases=entity.get("aliases", {}),
                                   descriptions=entity.get("descriptions", {}), websites=websites,
                                   official_domain_matches=any(domain(url) == domain(row.get("directory_website") or "") for url in websites if isinstance(url,str)),
                                   countries=[labels.get(q, {"id":q}) for q in country_ids],
                                   coordinates=values(entity, "P625"), location_entities=values(entity, "P131"),
                                   images=[imageinfo.get("File:"+name, {"title":"File:"+name}) for name in values(entity, "P18") if isinstance(name,str)],
                                   entity_url=f"https://www.wikidata.org/wiki/{hit['id']}", search_evidence=search_result["source_url"]))
        result_rows.append(dict(id=row["id"], school_name=row["school_name"], country=row["country"],
                                checked_at=search_result["checked_at"], candidates=candidates,
                                status="requires_identity_country_campus_and_license_review", error=search_result.get("error")))
    (BUNDLE / "campus_candidates.json").write_text(json.dumps(result_rows, ensure_ascii=False, indent=2)+"\n")
    print(json.dumps(dict(institutions=len(rows), wikidata_candidates=len(qids), country_entities=len(labels),
                         photo_candidates=len(imageinfo), search_errors=sum("error" in s for s in searches))))


if __name__ == "__main__":
    main()
