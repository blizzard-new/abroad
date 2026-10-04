from __future__ import annotations

import hashlib
import re
import time
from collections import deque
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import parse_qsl, unquote, urlencode, urljoin, urlparse, urlunparse

import requests
from bs4 import BeautifulSoup
from pydantic import BaseModel, Field

from .models import Attachment, RawPage
from .settings import (
    ALLOWED_DOMAIN_SUFFIX,
    ATTACHMENT_EXTENSIONS,
    CGU_START_URL,
    DEFAULT_DATA_DIR,
    EXCLUDED_TITLE_KEYWORDS,
    EXCLUDED_TEXT_KEYWORDS,
    EXCLUDED_URL_PARTS,
    GENERIC_DISCOVERY_KEYWORDS,
    RELEVANT_KEYWORDS,
)
from .storage import data_paths, ensure_data_dirs


TRACKING_QUERY_PREFIXES = ("utm_",)
TRACKING_QUERY_NAMES = {"fbclid", "gclid"}
DATE_PATTERNS = [
    re.compile(r"\b20\d{2}[/-]\d{1,2}[/-]\d{1,2}\b"),
    re.compile(r"\b\d{3}[/-]\d{1,2}[/-]\d{1,2}\b"),
    re.compile(r"\b20\d{2}\.\d{1,2}\.\d{1,2}\b"),
]


class CrawlerConfig(BaseModel):
    start_url: str = CGU_START_URL
    max_pages: int = Field(default=60, ge=1, le=500)
    rate_limit_seconds: float = Field(default=1.0, ge=0.0)
    timeout_seconds: float = Field(default=20.0, ge=1.0)
    use_playwright: bool = False
    data_dir: Path = DEFAULT_DATA_DIR
    user_agent: str = (
        "taiwan-exchange-info-mvp/0.1 "
        "(public academic information indexer; low-rate educational MVP)"
    )


class CguOiaCrawler:
    def __init__(self, config: CrawlerConfig | None = None):
        self.config = config or CrawlerConfig()
        self.paths = ensure_data_dirs(self.config.data_dir)
        self.raw_files_dir = data_paths(self.config.data_dir)["raw_files"]
        from .http_client import get_safe_session
        self.session = get_safe_session(require_https=True)
        self.session.headers.update(
            {
                "User-Agent": self.config.user_agent,
                "Accept-Language": "zh-TW,zh;q=0.9,en;q=0.8",
            }
        )
        self._last_request_at = 0.0
        self._downloaded_attachment_urls: set[str] = set()

    def crawl(self) -> list[RawPage]:
        queue: deque[str] = deque([normalize_url(self.config.start_url)])
        visited_urls: set[str] = set()
        seen_hashes: set[str] = set()
        pages: list[RawPage] = []

        while queue and len(pages) < self.config.max_pages:
            url = queue.popleft()
            if url in visited_urls or not is_cgu_url(url):
                continue

            visited_urls.add(url)

            try:
                html = self.fetch_html(url)
            except requests.RequestException:
                continue

            for linked_url, link_text in self.extract_links(html, url):
                normalized = normalize_url(linked_url)
                if (
                    normalized not in visited_urls
                    and not is_attachment_url(normalized)
                    and self.is_relevant_candidate(normalized, link_text)
                ):
                    queue.append(normalized)

            raw_page = self.parse_page(url, html)
            if not raw_page.raw_text or not self.is_relevant_page(raw_page):
                continue
            if raw_page.content_hash in seen_hashes:
                continue

            seen_hashes.add(raw_page.content_hash)
            pages.append(raw_page)

        return pages

    def fetch_html(self, url: str) -> str:
        if self.config.use_playwright:
            return self.fetch_html_with_playwright(url)

        self._rate_limit()
        response = self.session.get(url, timeout=self.config.timeout_seconds)
        response.raise_for_status()
        # Guessing the charset misreads short UTF-8 pages (the visa page came out as mojibake),
        # so a body that decodes as UTF-8 is taken as UTF-8 and only the rest is guessed.
        try:
            return response.content.decode("utf-8")
        except UnicodeDecodeError:
            response.encoding = response.apparent_encoding or response.encoding
            return response.text

    def fetch_html_with_playwright(self, url: str) -> str:
        self._rate_limit()
        from playwright.sync_api import sync_playwright

        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            page = browser.new_page(user_agent=self.config.user_agent)
            page.goto(url, wait_until="networkidle", timeout=int(self.config.timeout_seconds * 1000))
            html = page.content()
            browser.close()
        return html

    def parse_page(self, source_url: str, html: str) -> RawPage:
        soup = BeautifulSoup(html, "html.parser")
        title = extract_title(soup)
        text = extract_main_text(soup)
        published_at = extract_date(text)
        attachments = self.extract_attachments(soup, source_url)
        content_hash = hash_content(title, published_at, text, [item.url for item in attachments])
        return RawPage(
            title=title,
            source_url=source_url,
            published_at=published_at,
            raw_text=text,
            attachments=attachments,
            crawled_at=datetime.now(timezone.utc),
            content_hash=content_hash,
        )

    def extract_links(self, html: str, base_url: str) -> list[tuple[str, str]]:
        soup = BeautifulSoup(html, "html.parser")
        links: list[tuple[str, str]] = []
        for anchor in soup.select("a[href]"):
            href = anchor.get("href")
            if not href:
                continue
            url = urljoin(base_url, href)
            text = anchor.get_text(" ", strip=True)
            links.append((url, text))
        return links

    def extract_attachments(self, soup: BeautifulSoup, base_url: str) -> list[Attachment]:
        attachments: list[Attachment] = []
        for anchor in soup.select("a[href]"):
            url = normalize_url(urljoin(base_url, anchor.get("href", "")))
            if not is_attachment_url(url):
                continue
            attachments.append(self.download_attachment(url))
        return attachments

    def download_attachment(self, url: str) -> Attachment:
        if url in self._downloaded_attachment_urls:
            return Attachment(url=url, filename=safe_filename_from_url(url))

        self._downloaded_attachment_urls.add(url)
        filename = safe_filename_from_url(url)
        file_path = self.raw_files_dir / f"{short_hash(url)}-{filename}"

        if file_path.exists():
            return Attachment(url=url, filename=filename, local_path=str(file_path))

        try:
            self._rate_limit()
            response = self.session.get(url, timeout=self.config.timeout_seconds, stream=True)
            response.raise_for_status()
            with file_path.open("wb") as handle:
                for chunk in response.iter_content(chunk_size=1024 * 64):
                    if chunk:
                        handle.write(chunk)
            return Attachment(
                url=url,
                filename=filename,
                local_path=str(file_path),
                content_type=response.headers.get("Content-Type"),
            )
        except requests.RequestException:
            return Attachment(url=url, filename=filename)

    def is_relevant_candidate(self, url: str, link_text: str = "") -> bool:
        if not is_cgu_url(url):
            return False
        if is_excluded_url(url):
            return False
        parsed = urlparse(url)
        if "/oia" in parsed.path.lower():
            return True
        haystack = f"{url}\n{link_text}".lower()
        return any(keyword.lower() in haystack for keyword in RELEVANT_KEYWORDS)

    def is_relevant_page(self, page: RawPage) -> bool:
        if (
            is_excluded_url(page.source_url)
            or is_excluded_title(page.title)
            or is_excluded_text(page.raw_text)
        ):
            return False
        if normalize_url(page.source_url) == normalize_url(self.config.start_url):
            return True
        haystack = f"{page.title}\n{page.source_url}\n{page.raw_text}".lower()
        content_keywords = [
            keyword
            for keyword in RELEVANT_KEYWORDS
            if keyword not in GENERIC_DISCOVERY_KEYWORDS
        ]
        return any(keyword.lower() in haystack for keyword in content_keywords)

    def _rate_limit(self) -> None:
        elapsed = time.monotonic() - self._last_request_at
        delay = self.config.rate_limit_seconds - elapsed
        if delay > 0:
            time.sleep(delay)
        self._last_request_at = time.monotonic()


def normalize_url(url: str) -> str:
    parsed = urlparse(urljoin(CGU_START_URL, url))
    query_items = [
        (key, value)
        for key, value in parse_qsl(parsed.query, keep_blank_values=True)
        if key not in TRACKING_QUERY_NAMES and not key.startswith(TRACKING_QUERY_PREFIXES)
    ]
    return urlunparse(
        (
            parsed.scheme or "https",
            parsed.netloc.lower(),
            parsed.path.rstrip("/") or "/",
            "",
            urlencode(query_items, doseq=True),
            "",
        )
    )


def is_cgu_url(url: str) -> bool:
    parsed = urlparse(url)
    hostname = parsed.hostname or ""
    return parsed.scheme in {"http", "https"} and (
        hostname == ALLOWED_DOMAIN_SUFFIX or hostname.endswith(f".{ALLOWED_DOMAIN_SUFFIX}")
    )


def is_attachment_url(url: str) -> bool:
    path = urlparse(url).path.lower()
    return "/serverfile/get/" in path or any(
        path.endswith(extension) for extension in ATTACHMENT_EXTENSIONS
    )


def is_excluded_url(url: str) -> bool:
    lowered = url.lower()
    return any(part.lower() in lowered for part in EXCLUDED_URL_PARTS)


def is_excluded_title(title: str) -> bool:
    return any(keyword in title for keyword in EXCLUDED_TITLE_KEYWORDS)


def is_excluded_text(text: str) -> bool:
    return any(keyword in text for keyword in EXCLUDED_TEXT_KEYWORDS)


def extract_title(soup: BeautifulSoup) -> str:
    if soup.title and soup.title.string:
        title = clean_document_title(soup.title.string)
        if title:
            return title
    for selector in ["meta[property='og:title']", "meta[name='twitter:title']"]:
        node = soup.select_one(selector)
        if node and node.get("content"):
            title = clean_document_title(node["content"])
            if title:
                return title
    for selector in ["h1", "h2", ".title", ".page-title", ".article-title"]:
        node = soup.select_one(selector)
        if node:
            title = node.get_text(" ", strip=True)
            if title:
                return title
    return "Untitled"


def clean_document_title(title: str) -> str:
    title = re.sub(r"\s+", " ", title).strip()
    title = re.sub(r"^長庚大學\s+", "", title)
    title = re.sub(r"\s*[-｜|]\s*長庚大學.*$", "", title)
    return title.strip()


def extract_main_text(soup: BeautifulSoup) -> str:
    soup = BeautifulSoup(str(soup), "html.parser")
    for node in soup.select("script, style, noscript, svg, nav, header, footer, form, aside"):
        node.decompose()

    candidates = soup.select(
        "main, article, [role='main'], .content, .main-content, .page-content, "
        ".article, .detail, .subject, .Subject, #content"
    )
    if not candidates and soup.body:
        candidates = [soup.body]
    if not candidates:
        candidates = [soup]

    best = max(candidates, key=lambda node: len(node.get_text(" ", strip=True)))
    lines = [line.strip() for line in best.get_text("\n", strip=True).splitlines()]
    return "\n".join(line for line in lines if line)


def extract_date(text: str) -> str | None:
    for pattern in DATE_PATTERNS:
        match = pattern.search(text)
        if match:
            return match.group(0).replace(".", "/").replace("-", "/")
    return None


def hash_content(
    title: str, published_at: str | None, text: str, attachment_urls: list[str] | None = None
) -> str:
    payload = "\n".join([title, published_at or "", text, *(attachment_urls or [])])
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def short_hash(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()[:12]


def safe_filename_from_url(url: str) -> str:
    path_name = Path(urlparse(url).path).name or f"attachment-{short_hash(url)}"
    decoded = unquote(path_name)
    cleaned = re.sub(r'[<>:"/\\|?*\x00-\x1f]+', "_", decoded).strip(" .")
    if not cleaned:
        cleaned = f"attachment-{short_hash(url)}"
    if not Path(cleaned).suffix:
        cleaned = f"{cleaned}.bin"
    return cleaned
