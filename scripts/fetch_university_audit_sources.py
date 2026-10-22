"""Resume bounded public-source acquisition; HTTP success never verifies a claim."""
from __future__ import annotations

import argparse
import collections
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
import gzip
import hashlib
import io
import json
from pathlib import Path
import sys
import threading
import time
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
import requests
from requests.adapters import HTTPAdapter
from urllib3.connection import HTTPSConnection
from urllib3.connectionpool import HTTPSConnectionPool
from urllib3.poolmanager import PoolManager
from exchange_info.http_client import SSRFSafeguardConnectionMixin, SafeHTTPConnectionPool

MAX_BYTES = 12 * 1024 * 1024
_locks = collections.defaultdict(threading.Lock)
_guard = threading.Lock()
_retry_after = {}


class AuditHTTPSConnection(SSRFSafeguardConnectionMixin, HTTPSConnection):
    """Keep urllib3's standard certificate validation and verified-state handling."""


class AuditHTTPSPool(HTTPSConnectionPool):
    ConnectionCls = AuditHTTPSConnection


class AuditPoolManager(PoolManager):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.pool_classes_by_scheme = {"http": SafeHTTPConnectionPool, "https": AuditHTTPSPool}


class AuditAdapter(HTTPAdapter):
    def init_poolmanager(self, connections, maxsize, block=False, **kwargs):
        self.poolmanager = AuditPoolManager(num_pools=connections, maxsize=maxsize, block=block, **kwargs)


def audit_session():
    session = requests.Session()
    session.trust_env = False
    session.mount("https://", AuditAdapter())
    session.mount("http://", AuditAdapter())
    return session


def fetch(row: dict, cache: Path) -> dict:
    from bs4 import BeautifulSoup
    from pypdf import PdfReader
    url = row["url"]
    key = row["url_id"]
    result = {
        "url_id": key, "url": url, "started_at": datetime.now(timezone.utc).isoformat(),
        "review_status": "pending_review",
        "transport": "urllib3_tls_with_public_ip_pinning",
    }
    hostname = urlsplit(url).hostname
    with _guard:
        lock = _locks[hostname]
    try:
        with lock:
            if _retry_after.get(hostname, 0) > time.monotonic():
                result.update(transport_result="deferred_rate_limit", completed_at=datetime.now(timezone.utc).isoformat())
                return result
            with audit_session() as session:
                session.headers.update({"User-Agent": "UniWay-source-audit/1.0 (public exchange-information verification)"})
                with session.get(url, timeout=(6, 18), stream=True) as response:
                    result.update(
                        status_code=response.status_code, final_url=response.url,
                        content_type=response.headers.get("Content-Type", ""),
                        redirect_chain=[{"url": r.url, "status": r.status_code} for r in response.history],
                    )
                    if response.status_code == 429:
                        retry = response.headers.get("Retry-After", "")
                        _retry_after[hostname] = time.monotonic() + max(60, int(retry) if retry.isdigit() else 900)
                        result["retry_after_header"] = retry
                    response.raise_for_status()
                    chunks = []
                    size = 0
                    start = time.monotonic()
                    for chunk in response.iter_content(65536):
                        size += len(chunk)
                        if size > MAX_BYTES:
                            raise ValueError("body_exceeds_12_MiB")
                        if time.monotonic() - start > 40:
                            raise TimeoutError("body_read_exceeds_40_seconds")
                        chunks.append(chunk)
                    body = b"".join(chunks)
                    result.update(bytes=len(body), sha256=hashlib.sha256(body).hexdigest(), transport_result="retrieved")
                    # Retain the exact generation cited by a review even after refetches.
                    (cache / "bodies").mkdir(exist_ok=True)
                    with gzip.open(cache / "bodies" / f"{result['sha256']}.gz", "wb") as stream:
                        stream.write(body)
                    with gzip.open(cache / f"{key}.body.gz", "wb") as stream:
                        stream.write(body)
                    content_type = result["content_type"].lower()
                    text = ""
                    if body.startswith(b"%PDF"):
                        reader = PdfReader(io.BytesIO(body))
                        text = "\n".join(f"\n[page {i + 1}]\n{page.extract_text() or ''}" for i, page in enumerate(reader.pages))
                        result["pages"] = len(reader.pages)
                        result["extraction"] = "pdf_text_requires_layout_review"
                    elif "html" in content_type or body.lstrip().lower().startswith((b"<!doctype html", b"<html")):
                        soup = BeautifulSoup(body, "html.parser")
                        result["title"] = soup.title.get_text(" ", strip=True) if soup.title else ""
                        for tag in soup(["script", "style", "noscript"]):
                            tag.decompose()
                        text = soup.get_text("\n", strip=True)
                        result["extraction"] = "html_text"
                        title = result["title"].lower()
                        if any(marker in title for marker in ("just a moment", "access denied", "sign in", "登入", "login", "403 forbidden")):
                            result["extraction"] = "possible_login_or_block_page"
                    elif "text/" in content_type or "json" in content_type or "javascript" in content_type:
                        response.encoding = response.encoding if response.encoding and response.encoding.lower() != "iso-8859-1" else "utf-8"
                        text = body.decode(response.encoding or "utf-8", errors="replace")
                        result["extraction"] = "text"
                    else:
                        result["extraction"] = "binary_requires_reader"
                    if text:
                        with gzip.open(cache / f"{key}.txt.gz", "wt", encoding="utf-8") as stream:
                            stream.write(text)
                        result["text_sha256"] = hashlib.sha256(text.encode()).hexdigest()
                        (cache / "texts").mkdir(exist_ok=True)
                        with gzip.open(cache / "texts" / f"{result['text_sha256']}.gz", "wt", encoding="utf-8") as stream:
                            stream.write(text)
                        result["text_characters"] = len(text)
            time.sleep(0.4)
    except Exception as exc:
        result["transport_result"] = "error" if "sha256" not in result else "retrieved_extraction_error"
        result["error"] = f"{type(exc).__name__}: {exc}"[:1200]
    result["completed_at"] = datetime.now(timezone.utc).isoformat()
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--inventory", type=Path, default=ROOT / "output/data-verification-20261021/baseline")
    parser.add_argument("--receipts", type=Path, default=ROOT / "docs/data-verification-20261021/source-receipts.jsonl")
    parser.add_argument("--cache", type=Path, default=ROOT / "output/data-verification-20261021")
    parser.add_argument("--kinds", nargs="*", default=[])
    parser.add_argument("--homes", nargs="*", default=[])
    parser.add_argument("--workers", type=int, choices=range(1, 7), default=4)
    parser.add_argument("--retry-errors", action="store_true")
    args = parser.parse_args()
    args.cache.mkdir(parents=True, exist_ok=True)
    receipt_file = args.receipts
    receipt_file.parent.mkdir(parents=True, exist_ok=True)
    sources = json.loads((args.inventory / "sources.json").read_text("utf-8"))
    previous = {}
    if receipt_file.exists():
        for line in receipt_file.read_text("utf-8").splitlines():
            row = json.loads(line)
            previous[row["url_id"]] = row
    selected = [
        row for row in sources
        if (not args.kinds or set(args.kinds).intersection(row["kinds"]))
        and (not args.homes or set(args.homes).intersection(row["home_ids"]))
        and (row["url_id"] not in previous or (args.retry_errors and previous[row["url_id"]]["transport_result"] != "retrieved"))
    ]
    print(json.dumps({"selected_sources": len(selected), "previous_receipts": len(previous)}, ensure_ascii=False), flush=True)
    counts = collections.Counter()
    with receipt_file.open("a", encoding="utf-8", newline="\n") as stream, ThreadPoolExecutor(max_workers=args.workers) as pool:
        jobs = {pool.submit(fetch, row, args.cache): row["url"] for row in selected}
        for i, future in enumerate(as_completed(jobs), 1):
            result = future.result()
            stream.write(json.dumps(result, ensure_ascii=False, separators=(",", ":")) + "\n")
            stream.flush()
            counts[result["transport_result"]] += 1
            if i % 10 == 0 or i == len(selected):
                print(json.dumps({"completed": i, "total": len(selected), "counts": dict(counts)}, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
