"""Bounded public-page reader for life research and exchange-report PDFs."""
from __future__ import annotations

import re
import time
from io import BytesIO
from urllib.parse import urlsplit

from bs4 import BeautifulSoup
from pypdf import PdfReader

from .content_summary import FetchedPageContent
from .http_client import get_safe_session


def public_https_url(value: str) -> str:
    try:
        parsed = urlsplit(value)
        if (parsed.scheme != "https" or not parsed.hostname or parsed.username
                or parsed.password or parsed.port not in (None, 443)
                or any(ord(char) < 32 for char in value)):
            return ""
        return value
    except ValueError:
        return ""


def fetch_public_bytes(url: str, *, timeout: float = 7, max_bytes: int = 2_000_000, form: dict | None = None):
    if not public_https_url(url):
        return None
    try:
        with get_safe_session() as session:
            session.trust_env = False
            session.max_redirects = 3
            started = time.monotonic()
            with session.request("POST" if form is not None else "GET", url, data=form,
                             timeout=(3, timeout), stream=True,
                             headers={"User-Agent": "UniWayExchangeGuide/0.1 (university student-life research; cached campus amenities)"}) as response:
                response.raise_for_status()
                if not public_https_url(response.url):
                    return None
                data = bytearray()
                for chunk in response.iter_content(32768):
                    data.extend(chunk)
                    if len(data) > max_bytes or time.monotonic() - started > timeout + 4:
                        return None
                return bytes(data), response.url, response.headers.get("Content-Type", "")
    except Exception:
        return None


def read_life_page(url: str, *, timeout_seconds: float = 7) -> FetchedPageContent | None:
    result = fetch_public_bytes(url, timeout=timeout_seconds)
    if not result:
        return None
    data, final_url, content_type = result
    try:
        if data.startswith(b"%PDF-") or "application/pdf" in content_type:
            reader = PdfReader(BytesIO(data))
            if reader.is_encrypted:
                return None
            text = "\n".join(page.extract_text() or "" for page in reader.pages[:12])
            title = str((reader.metadata or {}).get("/Title", ""))
        elif "html" in content_type or "text/plain" in content_type:
            soup = BeautifulSoup(data, "html.parser")
            title = soup.title.get_text(" ", strip=True) if soup.title else ""
            for node in soup.select("script, style, nav, footer, header, noscript, form"):
                node.decompose()
            root = soup.select_one("article, main, [role=main]") or soup.body or soup
            blocks = root.find_all(["p", "li", "h1", "h2", "h3", "h4", "tr"])
            # Inline links must stay in their sentence; splitting at every tag
            # otherwise turns fragments into misleading standalone statements.
            lines = [node.get_text(" ", strip=True) for node in blocks if not node.find(["p", "li", "tr"])]
            text = "\n".join(dict.fromkeys(lines)) if lines else root.get_text(" ", strip=True)
        else:
            return None
        text = re.sub(r"[ \t]+", " ", text).strip()[:18000]
        if len(text) < 160 or re.search(r"just a moment|checking your browser|verify you are human", text[:600], re.I):
            return None
        return FetchedPageContent(title=title[:220], text=text, final_url=final_url, status="full_text")
    except Exception:
        return None
