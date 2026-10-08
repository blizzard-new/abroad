"""Fetch only the reviewed public CCU source manifest into a candidate directory.

This script does not overwrite reviewed evidence, publish, contact schools, or
authenticate. A changed file remains a candidate until its contents/year/scope
are reviewed. Download success is deliberately distinct from current applicability.
"""

from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
import hashlib
import io
import json
from pathlib import Path
import re
import sys
from urllib.parse import urljoin, urlsplit

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from exchange_info.ccu_sources import BUNDLE
from bs4 import BeautifulSoup
from docx import Document
from pypdf import PdfReader
import requests


def fetch_public_source(item: dict, output: Path, session=None) -> dict:
    url = item["url"]
    if urlsplit(url).scheme not in {"http", "https"}:
        raise ValueError("CCU source URLs must be public HTTP(S)")
    result = {
        **item,
        "status": "fetch_failed",
        "content_applicability": "needs_confirmation",
        "checked_at": datetime.now(timezone.utc).isoformat(),
    }
    target = url
    match = re.search(r"drive\.google\.com/file/d/([^/?]+)", url)
    if match and item["authority"] == "partner_issued_document_linked_by_ccu":
        target = f"https://drive.usercontent.google.com/download?id={match[1]}&export=download"
    client = session or requests.Session()
    try:
        response = client.get(target, timeout=(10, 35))
        result.update(
            requested_url=target,
            final_url=response.url,
            http_status=response.status_code,
            content_type=response.headers.get("Content-Type"),
            bytes=len(response.content),
        )
        response.raise_for_status()
        body = response.content
        if len(body) > 32 * 1024 * 1024:
            raise ValueError(
                "Source exceeds 32 MiB; inspect separately before extraction"
            )
        result["sha256"] = hashlib.sha256(body).hexdigest()
        if body.startswith(b"%PDF-"):
            result.update(
                status="pdf",
                text_pages=[
                    page.extract_text() for page in PdfReader(io.BytesIO(body)).pages
                ],
            )
            (output / (item["source_id"] + ".pdf")).write_bytes(body)
        elif body.startswith(b"PK"):
            doc = Document(io.BytesIO(body))
            result.update(
                status="docx",
                text_pages=[
                    "\n".join(
                        [paragraph.text for paragraph in doc.paragraphs]
                        + [
                            " | ".join(cell.text for cell in row.cells)
                            for table in doc.tables
                            for row in table.rows
                        ]
                    )
                ],
            )
            (output / (item["source_id"] + ".docx")).write_bytes(body)
        elif body.startswith(b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1"):
            # A legacy Word binary is not HTML. Preserve it for a real DOC
            # converter rather than treating decoded binary strings as evidence.
            result.update(status="downloaded_doc_unextracted", text_pages=[])
            (output / (item["source_id"] + ".doc")).write_bytes(body)
        else:
            soup = BeautifulSoup(body, "html.parser")
            result["links"] = [
                {
                    "label": a.get_text(" ", strip=True),
                    "url": urljoin(response.url, a["href"]),
                }
                for a in soup.select("a[href]")
                if urlsplit(urljoin(response.url, a["href"])).scheme
                in {"http", "https"}
            ]
            for node in soup(["script", "style", "nav", "footer", "header"]):
                node.decompose()
            result.update(status="html", text_pages=[soup.get_text("\n", strip=True)])
        result["text_sha256"] = hashlib.sha256(
            json.dumps(result["text_pages"], ensure_ascii=False).encode()
        ).hexdigest()
        result["review_note"] = (
            "Fetch succeeded; applicable year, round, program and field semantics still require review."
        )
    except Exception as exc:
        result.update(status="fetch_failed", error=f"{type(exc).__name__}: {exc}")
    (output / (item["source_id"] + ".json")).write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    )
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        type=Path,
        required=True,
        help="Candidate directory, outside the reviewed bundle",
    )
    parser.add_argument("--workers", type=int, default=4)
    args = parser.parse_args()
    if args.output.resolve().is_relative_to(BUNDLE.resolve()):
        parser.error(
            "Output must be outside the reviewed bundle; review candidates before integration"
        )
    args.output.mkdir(parents=True, exist_ok=True)
    items = json.loads((BUNDLE / "overseas-source-requests.json").read_text())
    results = []
    with ThreadPoolExecutor(max_workers=max(1, min(args.workers, 6))) as pool:
        pending = [
            pool.submit(fetch_public_source, item, args.output) for item in items
        ]
        for future in as_completed(pending):
            result = future.result()
            results.append(result)
            print(
                result["source_id"],
                result["status"],
                result.get("http_status"),
                flush=True,
            )
    (args.output / "acquisition.json").write_text(
        json.dumps(results, ensure_ascii=False, indent=2) + "\n"
    )
    print(f"Fetched {len(results)} sources; no reviewed catalogue was modified.")


if __name__ == "__main__":
    main()
