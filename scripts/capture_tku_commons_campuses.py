"""Search licensed real campus candidates for every institution, politely.

Commons is a separate photo catalogue, not the rate-limited Wikidata search.
Stop the entire run on HTTP 429 and retain the response as a blocker.
"""
import gzip
from tku_capture_io import read_bytes, exists, captures
import hashlib
import json
import time
from datetime import datetime, timezone
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[1]
BUNDLE = ROOT / "src/exchange_info/official_data/tku"
STORE = BUNDLE / "commons_campus_candidates"


def main():
    STORE.mkdir(parents=True, exist_ok=True)
    rows = json.loads((BUNDLE / "full_census_audit.json").read_text())["schools"]
    results = []
    blocked = False
    for row in rows:
        path = STORE / (row["id"]+".json.gz")
        if exists(path):
            results.append(json.loads(gzip.decompress(read_bytes(path))))
            continue
        term = row.get("english_name") or row["school_name"]
        params = dict(action="query", format="json", generator="search", gsrsearch='"'+term+'" -logo -map',
                      gsrnamespace=6, gsrlimit=2, prop="imageinfo", iiprop="url|extmetadata|sha1", iiurlwidth=640)
        url = requests.Request("GET", "https://commons.wikimedia.org/w/api.php", params=params).prepare().url
        record = dict(id=row["id"], school_name=row["school_name"], source_url=url, query=term,
                      checked_at=datetime.now(timezone.utc).isoformat(), status="requires_campus_identity_and_license_review")
        if blocked:
            record.update(status="not_requested_after_rate_limit", error="Stop after Commons HTTP429; no bypass or unlicensed fallback")
        else:
            try:
                res = requests.get(url, timeout=(8,25), headers={"User-Agent":"UniWayTKUReference/1.0 (public campus-photo licensing audit)"})
                record.update(http_status=res.status_code, sha256=hashlib.sha256(res.content).hexdigest())
                if res.status_code == 429:
                    blocked = True
                res.raise_for_status()
                record["response"] = res.json()
            except requests.RequestException as exc:
                record["error"] = str(exc)
            time.sleep(2)
        path.write_bytes(gzip.compress(json.dumps(record,ensure_ascii=False).encode(),mtime=0))
        results.append(record)
        if len(results)%30==0:
            print(json.dumps(dict(processed=len(results), rate_limited=blocked)),flush=True)
    (BUNDLE/"commons_campus_index.json").write_text(json.dumps(results,ensure_ascii=False,indent=2)+"\n")
    print(json.dumps(dict(institutions=len(results), opened=sum("response" in r for r in results),
                         photo_candidates=sum(len(r.get("response",{}).get("query",{}).get("pages",{})) for r in results), rate_limited=blocked)))


if __name__=="__main__":main()
