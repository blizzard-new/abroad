"""What the office knows about UniWay: live platform numbers, today's verified announcements, voice and strategy.

Numbers come from the repository's university registry (the same list the website serves at /universities), so a
post can never claim more schools than the site supports. News comes from the daily official-source audit ledgers in
sources/audit/, and only entries marked as confirmed updates are offered to the writers.
"""

from __future__ import annotations

import ast
import importlib
import json
import sys
from dataclasses import dataclass, field
from datetime import date
from functools import lru_cache
from pathlib import Path

import httpx

from .config import Settings


@dataclass(frozen=True)
class BrandFacts:
    university_count: int
    partner_count: int
    universities: tuple[str, ...]
    site_url: str
    source: str

    def summary(self) -> str:
        return (
            f"目前支援 {self.university_count} 所大學、合計 {self.partner_count:,} 筆合作校資料（來源：{self.source}）。"
            f"網址 {self.site_url}。"
        )


@dataclass(frozen=True)
class NewsItem:
    school: str
    summary: str
    source_url: str
    checked_date: str


@dataclass
class Briefing:
    """Everything the strategist reads before planning a day."""

    day: date
    facts: BrandFacts
    news: list[NewsItem] = field(default_factory=list)
    recent_titles: list[str] = field(default_factory=list)
    winners: list[dict] = field(default_factory=list)
    research: list = field(default_factory=list)  # models.Finding from the research desk
    insights: list[str] = field(default_factory=list)  # the analyst's notes from the last metrics run


def load_facts(settings: Settings) -> BrandFacts:
    src = settings.repo_root / "src"
    if (src / "exchange_info" / "university_registry.py").is_file():
        added = str(src) not in sys.path
        if added:
            sys.path.insert(0, str(src))
        try:
            registry = importlib.import_module("exchange_info.university_registry")
        finally:
            if added:
                sys.path.remove(str(src))
        schools = registry.SUPPORTED_UNIVERSITIES
        return BrandFacts(
            university_count=len(schools),
            partner_count=sum(school.partner_count_hint or 0 for school in schools),
            universities=tuple(school.short_name for school in schools),
            site_url=settings.site_url,
            source="UniWay 支援大學清單",
        )
    response = httpx.get(f"{settings.site_url}/universities", timeout=20)
    response.raise_for_status()
    schools = response.json()
    return BrandFacts(
        university_count=len(schools),
        partner_count=sum(school.get("partner_count") or 0 for school in schools),
        universities=tuple(school["short_name"] for school in schools),
        site_url=settings.site_url,
        source=f"{settings.site_url}/universities",
    )


@dataclass(frozen=True)
class School:
    """One university the platform supports, as the platform records it: what a colleague checks against."""

    id: str
    name: str
    official_url: str
    note: str
    level: str
    partners: int


def load_schools(settings: Settings) -> list[School]:
    src = settings.repo_root / "src"
    if (src / "exchange_info" / "university_registry.py").is_file():
        added = str(src) not in sys.path
        if added:
            sys.path.insert(0, str(src))
        try:
            registry = importlib.import_module("exchange_info.university_registry")
        finally:
            if added:
                sys.path.remove(str(src))
        return [School(u.id, u.school_name, u.official_url, u.coverage_note, u.support_level, u.partner_count_hint or 0)
                for u in registry.SUPPORTED_UNIVERSITIES]
    response = httpx.get(f"{settings.site_url}/universities", timeout=20)
    response.raise_for_status()
    return [School(u.get("id") or u["short_name"], u.get("school_name") or u["short_name"], u.get("official_url", ""),
                   u.get("coverage_note", ""), u.get("support_level", ""), u.get("partner_count") or 0) for u in response.json()]


DEADLINES_FILE = ("src", "exchange_info", "verified_window_deadlines.py")
RULE_KEYS = ("online_deadline", "paper_deadline", "study_plan_limit")
RULE_FIELDS = ("label", "value_text", "verification_status", "last_checked_at", "source_url")


@lru_cache(maxsize=4)
def _deadline_specs(path: str, mtime: float) -> dict[str, dict]:
    """The platform's verified deadline rules per school, read from the source with `ast` and never imported: the module
    pulls in the whole web app, and reading it as text means no repository code runs inside the office."""
    try:
        tree = ast.parse(Path(path).read_text(encoding="utf-8"))
    except (OSError, SyntaxError):
        return {}
    specs: dict[str, dict] = {}
    for node in ast.walk(tree):
        value = node.value if isinstance(node, (ast.Assign, ast.AnnAssign)) else None
        names = [t.id for t in (node.targets if isinstance(node, ast.Assign) else [node.target]) if isinstance(t, ast.Name)] \
            if isinstance(node, (ast.Assign, ast.AnnAssign)) else []
        if "_RAW_SPECS" not in names or not isinstance(value, ast.List):
            continue
        for entry in value.elts:
            if not isinstance(entry, ast.Dict):
                continue
            row = {}
            for key, item in zip(entry.keys, entry.values):
                if not (isinstance(key, ast.Constant) and isinstance(key.value, str)):
                    continue
                if isinstance(item, ast.Constant) and isinstance(item.value, (str, bool, type(None))):
                    row[key.value] = item.value
                elif key.value in RULE_KEYS and isinstance(item, ast.Call):
                    row[key.value] = {kw.arg: kw.value.value for kw in item.keywords
                                      if kw.arg in RULE_FIELDS and isinstance(kw.value, ast.Constant) and isinstance(kw.value.value, str)}
            if isinstance(row.get("school_id"), str):
                specs[row["school_id"]] = row
    return specs


def platform_record(settings: Settings, school_id: str) -> str:
    """What the platform says today about one school's deadlines and rules, as text for the colleague who verifies a finding."""
    path = settings.repo_root.joinpath(*DEADLINES_FILE)
    if not path.is_file():
        return "（這台電腦上讀不到平台的已核實規則，請只依官網判斷）"
    row = _deadline_specs(str(path), path.stat().st_mtime).get(school_id)
    if not row:
        return f"（平台沒有 {school_id} 的已核實截止日規則）"
    lines = [f"來源檔 {'/'.join(DEADLINES_FILE)}，school_id={school_id}："]
    for key in ("window_badge", "cycle_label"):
        if row.get(key):
            lines.append(f"- {key}：{row[key]}")
    for key in RULE_KEYS:
        rule = row.get(key)
        if rule:
            lines.append(
                f"- {key}（{rule.get('label', '')}）：{rule.get('value_text', '')[:420]}"
                f"｜狀態 {rule.get('verification_status', '?')}｜查核日 {rule.get('last_checked_at', '?')}｜來源 {rule.get('source_url', '?')}"
            )
    return "\n".join(lines)


CONFIRMED = {"confirmed_update", "confirmed_updates"}


def load_news(settings: Settings, limit: int = 6) -> list[NewsItem]:
    """Confirmed official updates from the newest audit ledger."""
    ledgers = sorted((settings.repo_root / "sources" / "audit").glob("*.json"))
    for ledger in reversed(ledgers):
        try:
            data = json.loads(ledger.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        items = [
            NewsItem(
                school=school["school_name"],
                summary=school.get("summary", ""),
                source_url=school.get("source_url", ""),
                checked_date=data.get("checked_date", ""),
            )
            for school in data.get("schools", [])
            if school.get("category") in CONFIRMED and school.get("source_url")
        ]
        if items:
            return items[:limit]
    return []


# ---------------------------------------------------------------------------------------------------------------
# Strategy, adapted from the Threads × Instagram playbook: Threads tests topics and builds a real voice, Instagram
# shows the product and converts. Content mix on Instagram is 3:3:3:1 (value, reach, trust, story).

PILLARS = {
    "value": "價值／教育：申請知識、避坑指南、懶人包，目標是被收藏",
    "reach": "引流／娛樂：Reels 情境、迷因、反差開場，目標是觸及非粉絲",
    "trust": "信任／轉換：平台功能實際操作、學長姐心得、資料來源，搭配明確行動呼籲",
    "story": "品牌故事：小編日常、做這個網站的原因、幕後整理資料的過程",
}
# Ten-day rotation that keeps the 3:3:3:1 ratio.
PILLAR_ROTATION = ("value", "reach", "trust", "value", "reach", "trust", "value", "reach", "trust", "story")
PILLAR_FORMAT = {"value": "carousel", "reach": "reel", "trust": "carousel", "story": "carousel"}

THREADS_ANGLES = {
    "pain": "第一行直接點名族群或痛點，接著給一個具體解法",
    "choice": "二選一或投票式提問，降低留言門檻",
    "list": "實用清單或懶人包，3～5 點",
    "story": "小編真實碎碎念或幕後小故事，不推銷",
    "news": "今天查到的官方公告重點，附「以官方公告為準」",
}

HASHTAGS = ("#交換學生", "#出國交換", "#交換申請", "#留學準備", "#UniWay")
TOPIC_TAG = "交換學生"

BANNED_PHRASES = (
    "保證錄取",
    "保證上",
    "一定上",
    "穩上",
    "100%錄取",
    "百分百錄取",
    "官方授權",
    "官方合作",
    "學校指定",
    "最便宜",
    "全台唯一",
)

# What the mascot looks like, for every AI that describes or draws it. The pictures the office renders itself use the
# real artwork with its face drawn on top (render/mascot-face.css); this is for art an AI draws from a description.
MASCOT = (
    "UniWay 的吉祥物是一個圓潤的淺藍色 3D 小行李箱，頂端有提把，底下有兩個深藍色小輪子。"
    "牠一定有臉：正面上半部有兩顆深灰黑色的橢圓形眼睛（略向右傾，帶一點白色高光），兩頰有淡粉紅色腮紅；"
    "沒有嘴巴、沒有眉毛、沒有手腳。畫面裡出現牠的時候，眼睛不能省略。"
)

VOICE_GUIDE = f"""你們是 UniWay 行銷辦公室的成員。UniWay（app.uniway-tw.com）是給台灣大學生的交換申請整理網站：
依母校列出真正能申請的合作校、校內截止日與倒數提醒、申請文件工作台、交換預算與補助、學長姐心得；每筆資料都附官方來源。
公開資料免登入就能查。UniWay 不是任何大學的官方單位，也不代辦、不保證錄取。

共同原則
- 讀者是準備或考慮出國交換的台灣大學生，用台灣慣用的繁體中文與用語。
- 只寫你拿到的事實：平台數字、公告內容、日期都必須來自簡報資料；沒有給的數字、名額或日期一律不寫。
- 提到各校規定或日期時加上「以各校官方公告為準」，不要替學校做結論（例如說明會額滿不等於名額額滿）。
- 不使用：{"、".join(BANNED_PHRASES)} 等誇大或暗示官方背書的說法。
- 不放學生個資，不捏造學生心得或引言。

吉祥物
- {MASCOT}
- 任何描述或繪製吉祥物的文字（例如封面插圖的 art_prompt）都要寫出牠的眼睛，不要寫成沒有臉的行李箱。

Threads（脆）
- 拿掉品牌官腔，像團隊裡一個真實小編在講話：可以吐槽、碎碎念、分享不完美。
- 第一行就要抓住人：點名族群或痛點。多用提問、二選一、清單，讓人想留言或引用。
- 主文不放任何網址（含外部連結的貼文觸及會變低）；網址放在第一則留言。主文 500 字以內，通常 80～250 字最好讀。
- 每則只用一個主題標籤（topic tag），不在主文堆 hashtag。

Instagram
- 不是商品型錄。輪播圖文以「值得收藏」為目標：一張只講一件事，大標 14 字內，內文 40 字內。
- 第一張是封面鉤子，最後一張是行動呼籲（收藏、分享給要交換的朋友、連結在主頁）。
- 說明欄第一行重述鉤子，條列重點，結尾一個提問；hashtag 最多 5 個，放在最後。
- 說明欄網址不能點，寫「連結在主頁」。

Reels／YouTube Shorts
- 直式 9:16、30～45 秒；前 3 秒是鉤子（提問、反差或驚人對比），之後每 4～6 秒一個重點，最後是品牌片尾。
- 每個畫面都有大字幕（多數人靜音觀看），一行 12 字內。
- YouTube 標題 60 字內並加 #Shorts，描述前兩行就講清楚影片在說什麼。

YouTube 長影片（每週一支，橫式）
- 2～4 分鐘的本週交換情報懶人包：開場 10 秒說明本集重點，分段講，結尾提醒訂閱與到 UniWay 查資料。
"""


def pillar_for(day: date) -> str:
    return PILLAR_ROTATION[day.toordinal() % len(PILLAR_ROTATION)]

