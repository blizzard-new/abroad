"""Preserve explicit public NCU source attempts for review; no inferred facts.

Downloads, text extraction, identity candidates and reading approval are separate.
Run offline, never inside a request. No credentials, login or paid services.
"""
from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import UTC, datetime
import hashlib
import io
import json
from pathlib import Path
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup
from pypdf import PdfReader

HEADERS = {"User-Agent": "UniWay-NCU-Research/1.0 (public university source verification; https://github.com/blizzard-new/abroad)"}


def collect(spec, output):
    result = {**spec, "checked_at": datetime.now(UTC).isoformat(), "reading_status": "not_reviewed", "pages": []}
    target = output / spec["id"]
    target.mkdir(parents=True, exist_ok=True)
    try:
        response = requests.get(spec["url"], headers=HEADERS, timeout=(10, 20))
        result.update(status=response.status_code, final_url=response.url,
                      sha256=hashlib.sha256(response.content).hexdigest(), content_type=response.headers.get("content-type"))
        (target / "original.bin").write_bytes(response.content)
        response.raise_for_status()
        if response.content.startswith(b"%PDF"):
            result["format"] = "pdf"
            result["pages"] = [{"page": n, "text": page.extract_text() or ""}
                               for n, page in enumerate(PdfReader(io.BytesIO(response.content)).pages, 1)]
        else:
            soup = BeautifulSoup(response.content, "html.parser")
            result["links"] = [{"label": link.get_text(" ", strip=True), "url": urljoin(response.url, link["href"])}
                               for link in soup.select("a[href]")]
            for node in soup.select("script,style,noscript"):
                node.decompose()
            result["format"] = "html_no_pdf_pages"
            result["pages"] = [{"page": None, "text": soup.get_text("\n", strip=True)}]
        for page in result["pages"]:
            name = f"page-{page['page']:03}.txt" if page["page"] else "page-web.txt"
            (target / name).write_text(page["text"])
    except Exception as error:
        result["error"] = f"{type(error).__name__}: {error}"
    (target / "source.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("spec", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--workers", type=int, default=4)
    args = parser.parse_args()
    specs = json.loads(args.spec.read_text())
    args.output.mkdir(parents=True, exist_ok=True)
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = {}
        for spec in specs:
            cached = args.output / spec["id"] / "source.json"
            if cached.exists():
                continue
            futures[pool.submit(collect, spec, args.output)] = spec["id"]
        for n, future in enumerate(as_completed(futures), 1):
            record = future.result()
            print(f"{n}/{len(futures)} {record['id']}: {record.get('status', 'no_response')} {record.get('error', '')[:80]}", flush=True)
    records = [json.loads((args.output / spec["id"] / "source.json").read_text()) for spec in specs]
    (args.output / "manifest.json").write_text(json.dumps(records, ensure_ascii=False, indent=2) + "\n")
    print(f"attempts={len(records)} failures={sum(bool(record.get('error')) for record in records)}")


if __name__ == "__main__":
    main()
