"""Country-level "things to sort out before you go", every item tied to a public source.

The guides live in ``official_data/destination_tips_zh.json``. They are written offline from official or
widely used public references, never generated at request time, and stay ``draft`` until two different people
have reviewed them (the same rule the application workflows follow). ``validate_guides`` is the gate: the
bundled file must pass it, so an item without a source or a "reviewed" guide without two reviewers cannot ship.
"""
from __future__ import annotations

import json
import re
from datetime import date
from functools import lru_cache
from pathlib import Path
from typing import Literal
from urllib.parse import urlsplit

from pydantic import BaseModel, Field

GUIDES_FILE = Path(__file__).parent / "official_data" / "destination_tips_zh.json"

TOPICS: dict[str, str] = {
    "documents": "證件、簽證與入境",
    "phone_internet": "手機、網路與常用 App",
    "payment": "付款、銀行與換錢",
    "health_insurance": "保險與醫療",
    "housing": "住宿與落地登記",
    "transport": "交通",
    "safety_law": "安全與當地法規",
    "culture": "文化與生活習慣",
    "packing_power": "電壓、插座與行李",
    "emergency": "緊急聯絡",
}
IMPORTANCE = ("must", "should", "good_to_know")
DISCLAIMER = (
    "這份整理來自公開的官方資料與常用參考，尚未經過兩位審核者逐項確認。簽證、入境與法規會變動，"
    "出發前請點進每一項的來源，並以當地官方公告與駐外館處最新資訊為準。"
)


class TipSource(BaseModel):
    name: str
    url: str


class DestinationTip(BaseModel):
    title: str
    detail: str
    importance: Literal["must", "should", "good_to_know"] = "should"
    sources: list[TipSource] = Field(default_factory=list)
    checked_at: str


class DestinationTipTopic(BaseModel):
    topic: str
    title: str
    tips: list[DestinationTip] = Field(default_factory=list)


class DestinationGuide(BaseModel):
    country: str
    display_name: str
    intro: str = ""
    topics: list[DestinationTipTopic] = Field(default_factory=list)
    review_status: Literal["draft", "reviewed"] = "draft"
    reviewers: list[str] = Field(default_factory=list)
    last_checked: str = ""
    disclaimer: str = DISCLAIMER


class DestinationGuideSummary(BaseModel):
    country: str
    display_name: str
    tip_count: int
    last_checked: str
    review_status: Literal["draft", "reviewed"]


def _is_iso_date(value: str) -> bool:
    try:
        date.fromisoformat(value)
    except (TypeError, ValueError):
        return False
    return bool(re.fullmatch(r"\d{4}-\d{2}-\d{2}", value))


def validate_guides(payload: dict) -> list[str]:
    """Every reason the data may not ship, in plain language; an empty list means it is valid."""
    problems: list[str] = []
    guides = payload.get("guides")
    if payload.get("version") != 1 or not isinstance(guides, dict):
        return ["檔案格式不是 version 1 的 {guides: {...}}。"]
    for country, raw in guides.items():
        where = f"{country}"
        try:
            guide = DestinationGuide.model_validate(raw)
        except Exception as error:  # pydantic's message already names the field
            problems.append(f"{where}：欄位格式錯誤（{str(error).splitlines()[0]}）")
            continue
        if guide.country != country:
            problems.append(f"{where}：country 欄位 {guide.country!r} 與鍵名不一致。")
        if not guide.display_name.strip():
            problems.append(f"{where}：缺少 display_name。")
        if guide.review_status == "reviewed" and len({name.strip() for name in guide.reviewers if name.strip()}) < 2:
            problems.append(f"{where}：標示 reviewed 但不到兩位不同的審核者。")
        if guide.review_status == "draft" and guide.reviewers:
            problems.append(f"{where}：draft 不應列出審核者。")
        if guide.last_checked and not _is_iso_date(guide.last_checked):
            problems.append(f"{where}：last_checked 不是 YYYY-MM-DD。")
        seen_topics: set[str] = set()
        total = 0
        for topic in guide.topics:
            if topic.topic not in TOPICS:
                problems.append(f"{where}：未知主題 {topic.topic!r}。")
            elif topic.topic in seen_topics:
                problems.append(f"{where}：主題 {topic.topic} 重複。")
            elif topic.title != TOPICS[topic.topic]:
                problems.append(f"{where}/{topic.topic}：標題應為「{TOPICS[topic.topic]}」。")
            seen_topics.add(topic.topic)
            titles: set[str] = set()
            for tip in topic.tips:
                total += 1
                label = f"{where}/{topic.topic}/{tip.title[:20]}"
                if not tip.title.strip() or not tip.detail.strip():
                    problems.append(f"{label}：標題或內容是空的。")
                if tip.title in titles:
                    problems.append(f"{label}：同一主題內標題重複。")
                titles.add(tip.title)
                if tip.importance not in IMPORTANCE:
                    problems.append(f"{label}：importance 無效。")
                if not tip.sources:
                    problems.append(f"{label}：沒有任何來源。")
                for source in tip.sources:
                    parts = urlsplit(source.url)
                    if parts.scheme != "https" or not parts.netloc or not source.name.strip():
                        problems.append(f"{label}：來源必須有名稱與 https 網址（{source.url}）。")
                if not _is_iso_date(tip.checked_at):
                    problems.append(f"{label}：checked_at 不是 YYYY-MM-DD。")
        if total == 0:
            problems.append(f"{where}：沒有任何提醒項目。")
    return problems


# Partner lists name the same country in different ways ("大陸地區", "中國", "China"); the guides use one name each.
COUNTRY_ALIASES: dict[str, tuple[str, ...]] = {
    "大陸地區": ("中國", "中國大陸", "中国", "中华人民共和国", "中華人民共和國", "大陸", "China", "Mainland China", "PRC"),
    "香港": ("香港特別行政區", "Hong Kong", "HK"),
    "韓國": ("南韓", "大韓民國", "South Korea", "Korea"),
    "美國": ("美利堅合眾國", "United States", "USA", "US"),
    "英國": ("聯合王國", "大不列顛", "United Kingdom", "UK"),
    "日本": ("Japan",), "法國": ("France",), "德國": ("Germany",), "俄羅斯": ("Russia",), "越南": ("Vietnam", "Viet Nam"),
    "泰國": ("Thailand",), "印度": ("India",), "印尼": ("印度尼西亞", "Indonesia"), "菲律賓": ("Philippines",),
    "馬來西亞": ("Malaysia",), "新加坡": ("Singapore",), "紐西蘭": ("New Zealand",), "澳洲": ("澳大利亞", "Australia"),
    "加拿大": ("Canada",), "荷蘭": ("Netherlands",), "瑞士": ("Switzerland",), "瑞典": ("Sweden",), "西班牙": ("Spain",),
    "義大利": ("意大利", "Italy"), "奧地利": ("Austria",), "比利時": ("Belgium",), "波蘭": ("Poland",), "匈牙利": ("Hungary",),
    "挪威": ("Norway",), "立陶宛": ("Lithuania",), "拉脫維亞": ("Latvia",), "羅馬尼亞": ("Romania",), "斯洛伐克": ("Slovakia",),
    "捷克": ("捷克共和國", "Czech Republic", "Czechia"), "土耳其": ("土耳其共和國", "Türkiye", "Turkey"),
    "哈薩克": ("哈薩克斯坦", "Kazakhstan"), "孟加拉": ("孟加拉國", "Bangladesh"), "阿爾巴尼亞": ("Albania",),
    "蒙古": ("Mongolia",), "緬甸": ("Myanmar", "Burma"), "摩洛哥": ("Morocco",), "柬埔寨": ("Cambodia",), "巴西": ("Brazil",),
}
_ALIAS_TO_CANONICAL = {alias.casefold(): canonical for canonical, aliases in COUNTRY_ALIASES.items() for alias in aliases}


def canonical_country(name: str) -> str:
    """The name a guide is filed under; unknown names come back trimmed and unchanged."""
    value = (name or "").strip()
    return _ALIAS_TO_CANONICAL.get(value.casefold(), value)


@lru_cache(maxsize=1)
def _load() -> dict[str, DestinationGuide]:
    payload = json.loads(GUIDES_FILE.read_text(encoding="utf-8"))
    problems = validate_guides(payload)
    if problems:
        raise ValueError("destination_tips_zh.json 無法通過驗證：" + "；".join(problems[:5]))
    return {country: DestinationGuide.model_validate(raw) for country, raw in payload["guides"].items()}


def load_guides() -> dict[str, DestinationGuide]:
    return _load()


def guide_for_country(country: str) -> DestinationGuide | None:
    guides = _load()
    name = canonical_country(country)
    if name in guides:
        return guides[name]
    return next((guide for guide in guides.values() if guide.display_name == name), None)


def guide_summaries() -> list[DestinationGuideSummary]:
    return [
        DestinationGuideSummary(
            country=guide.country,
            display_name=guide.display_name,
            tip_count=sum(len(topic.tips) for topic in guide.topics),
            last_checked=guide.last_checked,
            review_status=guide.review_status,
        )
        for guide in sorted(_load().values(), key=lambda item: item.country)
    ]
