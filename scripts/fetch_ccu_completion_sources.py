"""Acquire public CCU completion evidence with normal certificate validation.

No authenticated endpoints, form submissions, speculative policies, or browser
certificate bypass. Acquisition is independent of the later content review.
"""
from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from urllib.parse import urlsplit, urlencode

from bs4 import BeautifulSoup
import requests

ROOT = Path(__file__).resolve().parents[1]
BUNDLE = ROOT / "src/exchange_info/official_data/ccu"
OUT = BUNDLE / "completion_sources"
USER_AGENT = "UniWay-CCU-research/1.0 (https://github.com/blizzard-new/abroad; public university catalogue)"


def fetch(page, label, url, *, refresh=False):
    stem = f"p{page}-{label}"
    receipt_path = OUT / (stem + ".receipt.json")
    if receipt_path.exists() and not refresh:
        return json.loads(receipt_path.read_text())
    receipt = {
        "source_id": stem, "ccu_page": page, "source_url": url,
        "checked_at": datetime.now(timezone.utc).isoformat(), "tls_verify": True,
        "acquisition_method": "requests.get(verify=True), public read only",
        "review_status": "acquired_not_policy_verified",
    }
    try:
        response = requests.get(url, timeout=20, headers={"User-Agent": USER_AGENT})
        receipt.update(http_status=response.status_code, resolved_url=response.url,
                       content_type=response.headers.get("content-type"), bytes=len(response.content),
                       sha256=hashlib.sha256(response.content).hexdigest())
        content_type = receipt["content_type"] or ""
        extension = ("pdf" if response.content.startswith(b"%PDF-") else "json" if "json" in content_type
                     else "pdf" if "pdf" in content_type else "html")
        payload = OUT / (stem + "." + extension)
        payload.write_bytes(response.content)
        receipt["bundled_file"] = str(payload.relative_to(BUNDLE))
        response.raise_for_status()
        if extension == "html":
            soup = BeautifulSoup(response.content, "html.parser")
            receipt["title"] = soup.title.get_text(" ", strip=True) if soup.title else None
            receipt["links"] = [{"label": tag.get_text(" ", strip=True), "url": requests.compat.urljoin(response.url, tag["href"])} for tag in soup.find_all("a", href=True)]
            for tag in soup(["script", "style", "noscript"]):
                tag.decompose()
            text = soup.get_text(" ", strip=True)
            (OUT / (stem + ".txt")).write_text(text, encoding="utf-8")
            receipt["text_sha256"] = hashlib.sha256(text.encode()).hexdigest()
        elif extension == "json":
            response.json()
    except (requests.RequestException, ValueError) as error:
        receipt["error"] = type(error).__name__ + ": " + str(error)
        receipt["review_status"] = "source_technical_failure"
    receipt_path.write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return receipt


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--refresh", action="store_true")
    parser.add_argument("--kind", choices=["root", "ror", "ror-name"], required=True)
    args = parser.parse_args()
    OUT.mkdir(exist_ok=True)
    rows = json.loads((BUNDLE / "completion-targets.json").read_text())
    with ThreadPoolExecutor(max_workers=4) as pool:
        tasks = []
        for row in rows:
            url = row["website"] if args.kind == "root" else "https://api.ror.org/v2/organizations?" + urlencode({"query": row.get("canonical_name") or row["research_name"]} if args.kind == "ror-name" else {"query.advanced": "domains:" + (urlsplit(row["website"]).hostname or "").removeprefix("www.")})
            tasks.append(pool.submit(fetch, row["ccu_page"], args.kind, url, refresh=args.refresh))
        for number, future in enumerate(as_completed(tasks), 1):
            record = future.result()
            print(f"{number}/{len(rows)} {record['source_id']} HTTP {record.get('http_status')} {record.get('review_status')}", flush=True)


if __name__ == "__main__":
    main()
