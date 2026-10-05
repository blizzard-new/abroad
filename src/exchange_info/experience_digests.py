"""Traditional Chinese write-ups of student experiences, kept apart from the collected source records.

``official_data/experience_digests_zh.json`` maps a source URL to a digest we wrote ourselves from the page: what
the author actually says (costs, housing, courses, practical tips) in our own words. It is not a translation of
the page. The collector only ever stores short metadata and a summary, so showing a source with its digest is the
way a student reads "the experience" without us republishing someone else's writing.

Sources are also classified by what kind of page they are, so rankings, course directories and review-site
listings are not presented as if a student wrote them.
"""
from __future__ import annotations

import hashlib
import json
import re
from datetime import date
from functools import lru_cache
from pathlib import Path
from urllib.parse import urlsplit

from .experience_collector import normalize_school
from .models import ExperienceDigestZh, ExperienceSourceType, StudentExperienceDigest, StudentExperienceSource

DIGESTS_FILE = Path(__file__).parent / "official_data" / "experience_digests_zh.json"

KIND_LABELS = {
    "personal_story": "學生分享",
    "review_collection": "評論彙整頁",
    "community_thread": "社群討論串",
    "video": "影片",
    "directory": "學校介紹、排名或課程目錄",
    "other": "其他來源",
}
# Order matters: the first matching rule wins.
REVIEW_COLLECTION_HOSTS = (
    "eduopinions.com", "studyabroad101.com", "iagora.com", "edarabia.com", "wanderlog.com", "docsity.com",
    "capitainestudy.fr", "gooverseas.com", "cucas.cn", "niche.com", "princetonreview.com",
)
COMMUNITY_HOSTS = ("reddit.com", "redditmedia.com", "quora.com", "ptt.cc", "dcard.tw")
DIRECTORY_HOSTS = (
    "unirank.org", "mastersportal.com", "shortcoursesportal.com", "bachelorsportal.com", "timesofcollege.com",
    "japanrar.com", "studyjapan.jp", "jpcampus.net", "smapse.com", "culko.in", "studykorea.in", "gogohanguk.com",
    "visualnarrative.sg", "topuniversities.com", "usnews.com", "timeshighereducation.com", "erasmusplay.com",
    "japan-explore.jp", "pathivy.com", "applyforchina.com",
)
VIDEO_HOSTS = ("youtube.com", "youtu.be", "tiktok.com", "bilibili.com")
THEME_KEYS = frozenset({"housing", "food", "transport", "academics", "cost", "visa", "social", "climate", "safety", "travel",
                        "campus_culture", "support", "career", "challenges"})
REQUIRED_SOURCE_FIELDS = ("school_name", "country", "title", "platform", "language", "source_type", "themes")


def _host(url: str) -> str:
    return (urlsplit(url).hostname or "").lower().removeprefix("www.")


def _matches(host: str, domains: tuple[str, ...]) -> bool:
    return any(host == domain or host.endswith("." + domain) for domain in domains)


def source_kind(source: StudentExperienceSource) -> str:
    """What the page is. Only a personal story reads as one student's account."""
    host = _host(source.source_url)
    if source.source_type.value == "video" or _matches(host, VIDEO_HOSTS):
        return "video"
    if source.source_type.value == "community" or _matches(host, COMMUNITY_HOSTS):
        return "community_thread"
    if _matches(host, REVIEW_COLLECTION_HOSTS):
        return "review_collection"
    if _matches(host, DIRECTORY_HOSTS):
        return "directory"
    return "personal_story" if source.perspective in {"student_created", "official_student_story"} or host else "other"


def _is_iso_date(value: str) -> bool:
    try:
        date.fromisoformat(value)
    except (TypeError, ValueError):
        return False
    return bool(re.fullmatch(r"\d{4}-\d{2}-\d{2}", value))


def validate_digests(payload: dict) -> list[str]:
    """Every reason the bundled digests may not ship; an empty list means valid."""
    problems: list[str] = []
    digests = payload.get("digests")
    if payload.get("version") != 1 or not isinstance(digests, dict):
        return ["檔案格式不是 version 1 的 {digests: {...}}。"]
    sources = payload.get("sources")
    if not isinstance(sources, dict):
        return ["缺少 sources：每篇整理都要附上學校、標題、平台等來源資料。"]
    for url in sorted(set(digests) ^ set(sources)):
        problems.append(f"{url[:70]}：digests 與 sources 兩邊要一一對應。")
    for url, raw in digests.items():
        label = url[:70]
        parts = urlsplit(url)
        if parts.scheme not in {"http", "https"} or not parts.netloc:
            problems.append(f"{label}：鍵名不是網址。")
        meta = sources.get(url)
        if isinstance(meta, dict):
            missing = [field for field in REQUIRED_SOURCE_FIELDS if not meta.get(field)]
            if missing:
                problems.append(f"{label}：來源資料缺少 {'、'.join(missing)}。")
            if meta.get("source_type") not in {"article", "video", "community"}:
                problems.append(f"{label}：source_type 無效。")
            themes = meta.get("themes") or []
            if not isinstance(themes, list) or not set(themes) <= THEME_KEYS:
                problems.append(f"{label}：themes 含有未知主題。")
        try:
            digest = ExperienceDigestZh.model_validate(raw)
        except Exception as error:
            problems.append(f"{label}：欄位格式錯誤（{str(error).splitlines()[0]}）")
            continue
        if len(digest.overview.strip()) < 40:
            problems.append(f"{label}：概述少於 40 字，不比通用摘要有用。")
        if not digest.sections:
            problems.append(f"{label}：沒有任何分段整理。")
        for section in digest.sections:
            if not section.heading.strip() or not section.points:
                problems.append(f"{label}：有空的分段或沒有要點。")
        if not _is_iso_date(digest.written_at):
            problems.append(f"{label}：written_at 不是 YYYY-MM-DD。")
        everything = [digest.overview, *digest.tips, *(point for section in digest.sections for point in section.points)]
        if sum(len(text) for text in everything) > 2600:
            problems.append(f"{label}：整理超過 2600 字，已接近重製原文而不是整理。")
        if any(re.search(r"[぀-ヿ가-힯]{6,}", text) for text in everything):
            problems.append(f"{label}：含有一整段日文或韓文，應改寫成繁體中文。")
        if any(re.search(r"[A-Za-z][A-Za-z ,'’\-]{70,}", text) for text in everything):
            problems.append(f"{label}：含有一整段英文原文，應改寫成繁體中文。")
    return problems


@lru_cache(maxsize=1)
def _load() -> tuple[dict[str, ExperienceDigestZh], dict[str, dict]]:
    payload = json.loads(DIGESTS_FILE.read_text(encoding="utf-8"))
    problems = validate_digests(payload)
    if problems:
        raise ValueError("experience_digests_zh.json 無法通過驗證：" + "；".join(problems[:5]))
    digests = {url: ExperienceDigestZh.model_validate(raw) for url, raw in payload["digests"].items()}
    return digests, payload["sources"]


def load_digests() -> dict[str, ExperienceDigestZh]:
    return _load()[0]


def _synthesize(url: str, meta: dict, digest: ExperienceDigestZh) -> StudentExperienceSource:
    return StudentExperienceSource(
        school_name=meta["school_name"], country=meta.get("country"), title=meta["title"], source_url=url,
        source_type=ExperienceSourceType(meta.get("source_type", "article")), platform=meta["platform"],
        author_name=meta.get("author_name"), language=meta.get("language", "unknown"), summary=digest.overview,
        themes=list(meta["themes"]), content_status="full_text", perspective=meta.get("perspective", "student_created"),
        published_at=meta.get("published_at"), exchange_term=meta.get("exchange_term"),
        content_hash=hashlib.sha256(url.encode("utf-8")).hexdigest(),
    )


def with_bundled_sources(digest: StudentExperienceDigest, school_name: str) -> StudentExperienceDigest:
    """Add the curated stories for this school that the crawl did not find, so they show on any deployment."""
    digests, metas = _load()
    known = {source.source_url for source in digest.sources}
    added = [
        _synthesize(url, meta, digests[url])
        for url, meta in metas.items()
        if url not in known and normalize_school(meta["school_name"]) == normalize_school(school_name)
    ]
    if not added:
        return digest
    return digest.model_copy(update={
        "sources": [*digest.sources, *added],
        "total_sources": digest.total_sources + len(added),
        "article_count": digest.article_count + sum(source.source_type == ExperienceSourceType.ARTICLE for source in added),
    })


def attach_digests(sources: list[StudentExperienceSource]) -> list[StudentExperienceSource]:
    """Each source with its kind and, when we wrote one, its Chinese digest. Order is kept."""
    digests = load_digests()
    return [
        source.model_copy(update={"source_kind": source_kind(source), "digest_zh": digests.get(source.source_url)})
        for source in sources
    ]
