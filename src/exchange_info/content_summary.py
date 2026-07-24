from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

import requests
from bs4 import BeautifulSoup
from playwright.sync_api import Error as PlaywrightError
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from playwright.sync_api import sync_playwright

from .ai_gateway import structured_response


USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "Chrome/126.0 Safari/537.36 TaiwanExchangeGuide/0.1"
)
BLOCK_TAGS = ("script", "style", "noscript", "svg", "nav", "footer", "form")
MODEL_META_MARKER = re.compile(
    r"(?:<--\s*ERROR|ERROR\s*:\s*malformed\s+JSON|malformed\s+JSON|"
    r"Need\s+to\s+fix|Let(?:'|’)s\s+recompose|Sorry[,.]?\s+I(?:'|’)ll\s+correct)",
    re.IGNORECASE,
)


@dataclass(slots=True)
class FetchedPageContent:
    title: str
    text: str
    final_url: str
    status: str


def fetch_page_content(
    url: str,
    *,
    timeout_seconds: float = 18.0,
    max_chars: int = 18_000,
) -> FetchedPageContent | None:
    """Read the actual article/page body instead of relying on a search snippet."""
    response_text = ""
    final_url = url
    content_type = "text/html"
    try:
        response = requests.get(
            url,
            timeout=timeout_seconds,
            allow_redirects=True,
            headers={
                "User-Agent": USER_AGENT,
                "Accept-Language": "zh-TW,zh;q=0.9,en;q=0.8",
            },
        )
        response.raise_for_status()
        response_text = response.text
        final_url = response.url
        content_type = response.headers.get("Content-Type", "").casefold()
    except requests.RequestException:
        browser_page = _fetch_html_with_browser(url, timeout_seconds=timeout_seconds)
        if not browser_page:
            return None
        final_url, response_text = browser_page
    if not any(kind in content_type for kind in ("html", "text/plain", "xhtml")):
        return None
    if "html" not in content_type:
        text = _compact(response_text)
        return (
            FetchedPageContent(
                title="",
                text=text[:max_chars],
                final_url=final_url,
                status="full_text",
            )
            if len(text) >= 160
            else None
        )

    soup = BeautifulSoup(response_text, "html.parser")
    for tag in soup.find_all(BLOCK_TAGS):
        tag.decompose()
    title = _compact(
        (soup.find("meta", property="og:title") or {}).get("content")
        if soup.find("meta", property="og:title")
        else ""
    ) or _compact(soup.title.get_text(" ", strip=True) if soup.title else "")
    container = (
        soup.find("article")
        or soup.find("main")
        or soup.find(attrs={"role": "main"})
        or soup.body
        or soup
    )
    blocks: list[str] = []
    seen: set[str] = set()
    for node in container.find_all(("h1", "h2", "h3", "p", "li", "dt", "dd")):
        block = _compact(node.get_text(" ", strip=True))
        key = re.sub(r"\W+", "", block).casefold()
        if len(block) < 24 or len(key) < 16 or key in seen:
            continue
        seen.add(key)
        blocks.append(block)
    text = "\n".join(blocks)
    if len(text) < 240:
        text = _compact(container.get_text(" ", strip=True))
    text = _trim_for_summary(text, max_chars=max_chars)
    if len(text) < 160:
        return None
    return FetchedPageContent(
        title=title,
        text=text,
        final_url=final_url,
        status="full_text",
    )


def _fetch_html_with_browser(
    url: str,
    *,
    timeout_seconds: float,
) -> tuple[str, str] | None:
    timeout_ms = int(timeout_seconds * 1000)
    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            context = browser.new_context(ignore_https_errors=True, user_agent=USER_AGENT)
            page = context.new_page()
            page.goto(url, wait_until="domcontentloaded", timeout=timeout_ms)
            page.wait_for_timeout(900)
            result = (page.url, page.content())
            browser.close()
            return result
    except (PlaywrightError, PlaywrightTimeoutError):
        return None


def summarize_student_link(
    *,
    title: str,
    source_url: str,
    page_text: str,
    allowed_themes: list[str],
    timeout_seconds: float = 45.0,
) -> dict[str, Any] | None:
    if len(_compact(page_text)) < 160:
        return None
    schema = {
        "type": "object",
        "properties": {
            "summary_zh": {"type": "string", "minLength": 20, "maxLength": 420},
            "theme_points": {
                "type": "array",
                "maxItems": 10,
                "items": {
                    "type": "object",
                    "properties": {
                        "theme": {"type": "string", "enum": allowed_themes},
                        "point_zh": {"type": "string", "minLength": 10, "maxLength": 180},
                    },
                    "required": ["theme", "point_zh"],
                    "additionalProperties": False,
                },
            },
        },
        "required": ["summary_zh", "theme_points"],
        "additionalProperties": False,
    }
    payload = structured_response(
        schema_name="student_experience_link_summary",
        schema=schema,
        instructions=(
            "你是台灣大學生交換資訊編輯。只根據提供的網頁正文，以繁體中文摘要這一個連結。"
            "保留校名、地名、金額、時間與限制等具體資訊；不得用常識補充，不得把校方行銷文案"
            "改寫成學生親身經驗。summary_zh 要讓學生不用先讀原文也能掌握內容。"
            "theme_points 每點只能放正文中可核對的具體敘述；沒有證據就不要建立該主題。"
        ),
        input_text=f"標題：{title}\n網址：{source_url}\n\n網頁正文：\n{page_text}",
        tier="fast",
        timeout=timeout_seconds,
    )
    return _sanitize_summary_payload(payload) if payload else None


def summarize_official_life_link(
    *,
    title: str,
    source_url: str,
    page_text: str,
    timeout_seconds: float = 45.0,
) -> dict[str, Any] | None:
    if len(_compact(page_text)) < 160:
        return None
    point_array = {
        "type": "array",
        "maxItems": 3,
        "items": {"type": "string", "minLength": 10, "maxLength": 190},
    }
    schema = {
        "type": "object",
        "properties": {
            "summary_zh": {"type": "string", "minLength": 20, "maxLength": 360},
            "housing_points": point_array,
            "cost_points": point_array,
            "transport_points": point_array,
            "campus_life_points": point_array,
        },
        "required": [
            "summary_zh",
            "housing_points",
            "cost_points",
            "transport_points",
            "campus_life_points",
        ],
        "additionalProperties": False,
    }
    payload = structured_response(
        schema_name="official_partner_life_link_summary",
        schema=schema,
        instructions=(
            "你是台灣大學生交換資訊編輯。只根據提供的合作校官方頁面正文，以繁體中文整理。"
            "summary_zh 要說明這個連結實際提供什麼資訊。四組 points 只放能從正文直接核對的"
            "具體事實，保留原始金額、期間、地名、交通方式與限制；沒有資料時回傳空陣列。"
            "不得猜測、不得把一般招生宣傳當作生活事實。"
        ),
        input_text=f"標題：{title}\n網址：{source_url}\n\n官方頁面正文：\n{page_text}",
        tier="fast",
        timeout=timeout_seconds,
    )
    return _sanitize_summary_payload(payload) if payload else None


def sanitize_summary_text(value: object, *, max_chars: int = 420) -> str:
    """Remove model-formatting chatter before a summary reaches student-facing data."""
    text = _compact(value).replace("```json", "").replace("```", "")
    marker = MODEL_META_MARKER.search(text)
    if marker:
        text = text[: marker.start()]
    text = re.sub(r'[」”"]?[\]\}]\s*,?\s*$', "", text).strip()
    text = text.strip(" \t\r\n,;:[]{}<>`'")
    if text and text[-1] not in "。！？.!?)）":
        text += "。"
    return text[:max_chars].strip()


def _sanitize_summary_payload(payload: dict[str, Any]) -> dict[str, Any]:
    cleaned: dict[str, Any] = {}
    for key, value in payload.items():
        if isinstance(value, str):
            cleaned[key] = sanitize_summary_text(
                value,
                max_chars=420 if key == "summary_zh" else 190,
            )
            continue
        if isinstance(value, list):
            items: list[Any] = []
            for item in value:
                if isinstance(item, str):
                    text = sanitize_summary_text(item, max_chars=190)
                    if text:
                        items.append(text)
                elif isinstance(item, dict):
                    row = dict(item)
                    if "point_zh" in row:
                        row["point_zh"] = sanitize_summary_text(
                            row["point_zh"], max_chars=180
                        )
                    if row.get("point_zh", True):
                        items.append(row)
                else:
                    items.append(item)
            cleaned[key] = items
            continue
        cleaned[key] = value
    return cleaned


def _trim_for_summary(text: str, *, max_chars: int) -> str:
    compact = re.sub(r"[ \t]+", " ", text)
    compact = re.sub(r"\n{3,}", "\n\n", compact).strip()
    if len(compact) <= max_chars:
        return compact
    head = compact[: max_chars // 2]
    keywords = re.compile(
        r"housing|accommodation|dorm|cost|fee|transport|campus|student|course|class|"
        r"住宿|宿舍|費用|交通|校園|學生|課程|社團|安全|醫療",
        re.IGNORECASE,
    )
    relevant = [line for line in compact.splitlines() if keywords.search(line)]
    tail = "\n".join(relevant)[: max_chars // 2]
    return f"{head}\n{tail}"[:max_chars]


def _compact(value: object) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()
