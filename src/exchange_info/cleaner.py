from __future__ import annotations

import re

from .classifier import classify_page
from .models import ProcessedPage, RawPage
from .settings import BOILERPLATE_LINE_HINTS


WHITESPACE_RE = re.compile(r"[ \t\r\f\v]+")


def normalize_text(text: str) -> str:
    text = text.replace("\u3000", " ")
    text = WHITESPACE_RE.sub(" ", text)
    lines = [line.strip() for line in text.splitlines()]
    return "\n".join(line for line in lines if line)


def remove_boilerplate(text: str) -> str:
    cleaned_lines: list[str] = []
    seen_lines: set[str] = set()

    for line in normalize_text(text).splitlines():
        if _looks_like_boilerplate(line):
            continue
        if line in seen_lines:
            continue
        seen_lines.add(line)
        cleaned_lines.append(line)

    return "\n".join(cleaned_lines).strip()


def summarize_text(text: str, max_chars: int = 280) -> str:
    compact = re.sub(r"\s+", " ", text).strip()
    if len(compact) <= max_chars:
        return compact
    return compact[: max_chars - 1].rstrip() + "..."


def process_page(raw_page: RawPage) -> ProcessedPage:
    text = remove_boilerplate(raw_page.raw_text)
    category = classify_page(raw_page.title, text, raw_page.source_url)
    return ProcessedPage(
        title=raw_page.title,
        source_url=raw_page.source_url,
        published_at=raw_page.published_at,
        text=text,
        summary=summarize_text(text),
        category=category,
        attachments=raw_page.attachments,
        crawled_at=raw_page.crawled_at,
        content_hash=raw_page.content_hash,
    )


def process_pages(raw_pages: list[RawPage]) -> list[ProcessedPage]:
    return [process_page(raw_page) for raw_page in raw_pages]


def _looks_like_boilerplate(line: str) -> bool:
    if len(line) <= 1:
        return True
    if any(hint in line for hint in BOILERPLATE_LINE_HINTS):
        return True
    if re.fullmatch(r"[-_=|/\\\s]+", line):
        return True
    if re.fullmatch(r"\d+\s*/\s*\d+", line):
        return True
    return False
