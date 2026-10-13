"""Capture TKU's complete sister directory without treating agreements as quotas.

The directory is an institution denominator, not an exchange selection list.
Run this independently of build_tku_catalog.py; no other school's data is edited.
"""
from __future__ import annotations

import concurrent.futures
import gzip
from tku_capture_io import read_bytes, exists, captures
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
BUNDLE = ROOT / "src/exchange_info/official_data/tku"
CAPTURES = BUNDLE / "census_sources"
BASE = "https://sister.tku.edu.tw/"


def capture(url: str, name: str) -> dict:
    path = CAPTURES / (name + ".json.gz")
    if exists(path):
        return json.loads(gzip.decompress(read_bytes(path)))
    checked = datetime.now(timezone.utc).isoformat()
    try:
        response = requests.get(url, timeout=(10, 35))
        response.raise_for_status()
        soup = BeautifulSoup(response.content, "html.parser")
        record = dict(source_url=url, final_url=response.url, checked_at=checked,
                      http_status=response.status_code, sha256=hashlib.sha256(response.content).hexdigest(),
                      html=str(soup), text=soup.get_text("\n", strip=True))
    except requests.RequestException as exc:
        record = dict(source_url=url, checked_at=checked, error=str(exc))
    CAPTURES.mkdir(parents=True, exist_ok=True)
    path.write_bytes(gzip.compress(json.dumps(record, ensure_ascii=False).encode(), mtime=0))
    return record


def parse_listing(record: dict) -> list[dict]:
    soup = BeautifulSoup(record["html"], "html.parser")
    result = []
    for detail in soup.select('a[href*="school-detail.asp?id="]'):
        cells = detail.find_parent("tr").find_all("td", recursive=False)
        if len(cells) != 7:
            raise ValueError(f"unexpected directory row: {len(cells)} cells")
        name_parts = list(cells[2].stripped_strings)
        home_link = cells[2].find("a", href=True)
        result.append(dict(
            id="tku-sister-" + detail["href"].split("id=")[-1],
            school_name=name_parts[0], english_name=" ".join(name_parts[1:]),
            continent=cells[0].get_text(" ", strip=True), country=cells[1].get_text(" ", strip=True),
            agreement_date=cells[3].get_text(" ", strip=True),
            agreement_academic_year=cells[4].get_text(" ", strip=True),
            directory_address=cells[5].get_text(" ", strip=True),
            directory_website=(home_link.get("href") or None) if home_link else None,
            directory_url=urljoin(BASE, detail["href"]), listing_url=record["source_url"],
            checked_at=record["checked_at"],
            scope="sister_agreement_reference", availability_status="agreement_only",
            selection_note="姊妹校協議目錄不證明本梯可申請；以校級或院系所甄選公告及名額表另外判定。",
        ))
    return result


def main():
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
        listings = list(pool.map(lambda offset: capture(
            f"{BASE}schools.asp?pagecount=30&offset={offset}", f"list-{offset:03d}"), range(0, 286, 30)))
    rows = [row for record in listings for row in parse_listing(record)]
    if len(rows) != 286 or len({r["id"] for r in rows}) != 286:
        raise ValueError("Directory count changed or pages overlap; review before replacing census")
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
        details = list(pool.map(lambda row: capture(row["directory_url"], row["id"]), rows))
    for row, detail in zip(rows, details):
        row["detail_http_status"] = detail.get("http_status")
        row["detail_error"] = detail.get("error")
        row["detail_sha256"] = detail.get("sha256")
        row["detail_checked_at"] = detail["checked_at"]
    (BUNDLE / "partner_census.jsonl").write_text("".join(
        json.dumps(row, ensure_ascii=False) + "\n" for row in rows), encoding="utf-8")
    print(json.dumps(dict(directory_rows=len(rows), details_open=sum("html" in d for d in details),
                         detail_failures=sum("error" in d for d in details)), ensure_ascii=False))


if __name__ == "__main__":
    main()
