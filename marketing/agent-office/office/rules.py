"""Platform and brand rules the reviewer checks before anything reaches the queue.

Limits follow the platforms' published rules: Threads posts are 500 characters (emoji count as their UTF-8 bytes) with
at most 5 links and one topic tag; Instagram captions are 2,200 characters and posts take at most 5 hashtags;
YouTube titles are 100 characters and descriptions 5,000.
"""

from __future__ import annotations

import re
import unicodedata

from . import humanize
from .brand import BANNED_PHRASES, BrandFacts
from .models import CarouselDraft, ThreadsDraft, VideoScript

URL_RE = re.compile(r"https?://\S+|www\.\S+|\b[\w-]+\.(?:com|tw|net|org|io)(?:/\S*)?", re.IGNORECASE)
HASHTAG_RE = re.compile(r"#[^\s#]+")
DATE_RE = re.compile(r"\b\d{1,2}\s*/\s*\d{1,2}\b|\d{1,2}\s*月\s*\d{1,2}\s*日")
SCHOOL_COUNT_RE = re.compile(r"(\d[\d,]*)\s*(?:所|間)(?:大學|學校)")
PARTNER_COUNT_RE = re.compile(r"(\d[\d,]*)\s*(?:筆|間|所)?\s*合作校")

THREADS_LIMIT = 500
IG_CAPTION_LIMIT = 2200
IG_HASHTAG_LIMIT = 5
YT_TITLE_LIMIT = 100
YT_DESCRIPTION_LIMIT = 5000


def threads_length(text: str) -> int:
    """Threads counts an emoji as its UTF-8 byte length."""
    total = 0
    for ch in text:
        if ord(ch) >= 0x1F000 or unicodedata.category(ch) == "So" or 0xFE00 <= ord(ch) <= 0xFE0F or ch == "‍":
            total += len(ch.encode("utf-8"))
        else:
            total += 1
    return total


def display_width(text: str) -> float:
    """Caption width in full-width characters: Latin letters and digits take about half a CJK character."""
    return sum(0.55 if ch.isascii() else 1 for ch in text)


def _claims(text: str, facts: BrandFacts, has_source: bool) -> list[str]:
    issues = []
    for phrase in BANNED_PHRASES:
        if phrase in text:
            issues.append(f"不能使用「{phrase}」這類誇大或暗示官方背書的說法")
    for match in SCHOOL_COUNT_RE.finditer(text):
        if int(match.group(1).replace(",", "")) > facts.university_count:
            issues.append(f"「{match.group(0)}」超過平台目前支援的 {facts.university_count} 所大學")
    for match in PARTNER_COUNT_RE.finditer(text):
        if int(match.group(1).replace(",", "")) > facts.partner_count:
            issues.append(f"「{match.group(0)}」超過平台目前的 {facts.partner_count:,} 筆合作校資料")
    if DATE_RE.search(text) and not has_source:
        issues.append("提到日期但沒有官方來源；請刪掉日期或改用有來源的公告")
    return issues


def check_threads(draft: ThreadsDraft, facts: BrandFacts, source_url: str = "") -> list[str]:
    issues = []
    length = threads_length(draft.text)
    if not draft.text.strip():
        issues.append("主文是空的")
    if length > THREADS_LIMIT:
        issues.append(f"主文 {length} 字，超過 Threads 的 {THREADS_LIMIT} 字上限")
    if URL_RE.search(draft.text):
        issues.append("主文不能放網址（會降低觸及），請把連結移到第一則留言")
    if HASHTAG_RE.search(draft.text):
        issues.append("Threads 主文不要放 hashtag，改用 topic tag")
    tag = draft.topic_tag.strip().lstrip("#")
    if not tag or len(tag) > 50 or "." in tag or "&" in tag:
        issues.append("topic tag 必須是 1～50 字，且不能有句點或 &")
    if threads_length(draft.first_reply) > THREADS_LIMIT:
        issues.append("第一則留言超過 500 字")
    if len(URL_RE.findall(draft.first_reply)) > 5:
        issues.append("第一則留言的連結超過 5 個")
    if facts.site_url.split("//")[-1] not in draft.first_reply:
        issues.append(f"第一則留言要放 {facts.site_url.split('//')[-1]}")
    text = draft.text + "\n" + draft.first_reply
    issues += _claims(text, facts, bool(source_url))
    issues += humanize.check(text)
    return issues


def _hashtags(caption: str, hashtags: list[str]) -> set[str]:
    return {tag.lower() for tag in HASHTAG_RE.findall(caption)} | {
        ("#" + tag.lstrip("#")).lower() for tag in hashtags if tag.strip()
    }


def instagram_caption(caption: str, hashtags: list[str]) -> str:
    tags = " ".join("#" + tag.strip().lstrip("#") for tag in hashtags if tag.strip())
    return f"{caption.strip()}\n\n{tags}".strip()


def check_carousel(draft: CarouselDraft, facts: BrandFacts, source_url: str = "") -> list[str]:
    issues = []
    if not 3 <= len(draft.slides) <= 10:
        issues.append(f"輪播 {len(draft.slides)} 張，請控制在 3～10 張")
    if draft.slides and draft.slides[0].kind != "cover":
        issues.append("第一張要是封面")
    if draft.slides and draft.slides[-1].kind != "cta":
        issues.append("最後一張要是行動呼籲")
    for index, slide in enumerate(draft.slides, 1):
        if len(slide.title) > 20:
            issues.append(f"第 {index} 張大標 {len(slide.title)} 字，請縮到 20 字內")
        if len(slide.body) > 60:
            issues.append(f"第 {index} 張內文 {len(slide.body)} 字，請縮到 60 字內")
    caption = instagram_caption(draft.caption, draft.hashtags)
    if len(caption) > IG_CAPTION_LIMIT:
        issues.append(f"說明欄 {len(caption)} 字，超過 {IG_CAPTION_LIMIT} 字")
    if len(_hashtags(draft.caption, draft.hashtags)) > IG_HASHTAG_LIMIT:
        issues.append(f"hashtag 超過 {IG_HASHTAG_LIMIT} 個")
    if URL_RE.search(draft.caption):
        issues.append("Instagram 說明欄的網址不能點，請改寫「連結在主頁」")
    text = "\n".join([draft.caption, *(f"{s.title} {s.body}" for s in draft.slides)])
    issues += _claims(text, facts, bool(source_url))
    issues += humanize.check(text, max_dashes=humanize.PAGES_DASHES)
    return issues


def check_video(script: VideoScript, facts: BrandFacts, length: str, source_url: str = "") -> list[str]:
    issues = []
    total = sum(scene.seconds for scene in script.scenes)
    low, high = (15, 60) if length == "short" else (60, 300)
    if not low <= total <= high:
        issues.append(f"影片長度 {total:.0f} 秒，{'直式短影音' if length == 'short' else '長影片'}請控制在 {low}～{high} 秒")
    if not script.scenes or script.scenes[0].kind != "hook":
        issues.append("第一個畫面要是鉤子")
    elif length == "short" and script.scenes[0].seconds > 3.5:
        issues.append("鉤子要在 3 秒左右講完")
    if script.scenes and script.scenes[-1].kind != "cta":
        issues.append("最後一個畫面要是品牌片尾")
    for index, scene in enumerate(script.scenes, 1):
        for line in scene.lines:
            if display_width(line) > 16:
                issues.append(f"第 {index} 個畫面字幕「{line}」太長，一行請在 16 字內")
    if len(script.youtube_title) > YT_TITLE_LIMIT:
        issues.append(f"YouTube 標題超過 {YT_TITLE_LIMIT} 字")
    if len(script.youtube_description) > YT_DESCRIPTION_LIMIT:
        issues.append(f"YouTube 描述超過 {YT_DESCRIPTION_LIMIT} 字")
    if len(_hashtags(script.caption, script.hashtags)) > IG_HASHTAG_LIMIT:
        issues.append(f"hashtag 超過 {IG_HASHTAG_LIMIT} 個")
    if URL_RE.search(script.caption):
        issues.append("Reels 說明欄的網址不能點，請改寫「連結在主頁」")
    text = "\n".join(
        [script.caption, script.youtube_title, *(f"{s.heading} {' '.join(s.lines)}" for s in script.scenes)]
    )
    issues += _claims(text, facts, bool(source_url))
    issues += humanize.check(text, max_dashes=humanize.PAGES_DASHES)
    return issues
