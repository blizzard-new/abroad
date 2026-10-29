"""Evidence-backed life guidance, kept separate from reviewed official profiles."""
from __future__ import annotations

import hashlib
import json
import math
import re
import threading
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from collections.abc import Mapping
from functools import lru_cache
from pathlib import Path
from typing import Literal
from urllib.parse import urlencode, urlsplit
from uuid import uuid4

from pydantic import BaseModel, Field

from .experience_collector import school_search_name
from .life_claim_review import withdrawn_life_claim, unreviewed_profile_claim
from .life_sources import fetch_public_bytes, public_https_url, read_life_page
from .models import DestinationProfile, PartnerUniversity, StudentExperienceSource
from .public_translation import cached_translation, needs_translation, translate_public_excerpts
from .school_content import school_field_addition
from .school_identity import school_identity_key
from .university_locations import UniversityLocation
from .web_search import search_text

REFERENCE_DATA = Path(__file__).parent / "official_data" / "life_reference_data.json"
BUNDLED_NTU_LIFE = Path(__file__).parent / "official_data" / "ntu" / "student_life.jsonl"
THEMES = ("housing", "cost", "food", "transport", "academics", "climate", "social", "safety", "campus_culture", "travel")
THEME_QUERIES = dict(zip(THEMES, (
    "international student housing", "student living costs", "cafeteria supermarket restaurants",
    "campus access public transport", "exchange course syllabus", "climate weather seasons",
    "international student clubs", "student health clinic insurance", "international student support",
    "tourism public transport",
)))
NEXT_STEPS = dict(zip(THEMES, (
    "先確認錄取校區、宿舍資格與申請期限，再比較租金及實際通勤路線。",
    "以住宿、餐費、交通、保險分項查價；目前資料不足以產生可靠的每月總額。",
    "先查實際上課校區與宿舍附近的餐廳、超市及飲食限制，再確認菜單與營業時間。",
    "以錄取校區和住宿地址核對路線、轉乘及末班車，不能用直線距離換算通勤時間。",
    "查當期課綱、授課語言及考核比例；不能由地理位置推定課程難度或出席規定。",
    "以交換月份和實際城市查官方氣候常值，接近出發時再看天氣預報。",
    "先看國際處迎新、社團與語言交換活動；活動存在不代表每位學生都有相同體驗。",
    "確認校內健康服務與所在地就醫窗口；費用、語言、保險與急診服務須向機構核對。",
    "查看國際學生支援與不同背景學生的分享，不能把單一個案當成全校文化。",
    "從實際校區確認車站及機場路線，再用營運方時刻表規劃週末行程。",
)))
_research_gate = threading.Lock()
EXTRACTION_VERSION = 3
# Bound Latin words: "train" is not rain and "different" is not rent.
OFFICIAL_THEME_PATTERNS = {
    "housing": r"\b(?:dormitor\w*|housing|accommodation|residence halls?|wohnheim|logement)\b|宿舍|住宿|住居|기숙사",
    "cost": r"\b(?:costs?|rent|budget|fees?|living expenses|lebenshaltungskosten)\b|生活費|費用|家賃|생활비",
    "food": r"\b(?:food|meals?|restaurants?|cafeteria|grocer\w*|supermarket|cooking|mensa)\b|食堂|餐廳|飲食|食事|学食|식당",
    "transport": r"\b(?:buses?|transport\w*|commut\w*|metro|subway|stations?)\b|交通|通学|通勤|最寄り|교통",
    "academics": r"\b(?:courses?|lectures?|exams?|assessment|credits?|syllabus|teaching)\b|課程|履修|授業|評量|수업",
    "climate": r"\b(?:weather|climate|temperatures?|rainfall|snowfall|winter|summer)\b|氣候|気候|天氣|天候|날씨",
    "social": r"\b(?:friends?|clubs?|societies|international lounge|social events)\b|社團|交流活動|サークル|동아리",
    "safety": r"\b(?:clinics?|hospital|health|insurance|medical|krankenhaus)\b|診療所|病院|醫院|醫療|保険|병원",
    "campus_culture": r"\b(?:cultural|diversity|international student cent\w*|international office|orientation)\b|國際處|留学生支援|異文化",
    "travel": r"\b(?:airport|flights?|sightseeing|tourism|excursions?)\b|機場|空港|旅行|観光|여행",
}


class LifeSource(BaseModel):
    title: str
    url: str


class LifeEvidence(BaseModel):
    theme: str
    kind: Literal["official", "geographic", "mixed"]
    text: str
    sources: list[LifeSource] = Field(default_factory=list)
    checked_at: datetime | None = None
    scope: str = "校級資訊；適用校區請核對原頁"
    original_excerpt: bool = False
    original_text: str = ""
    translation_status: Literal["original", "translated", "machine", "pending"] = "original"


class LifeInference(BaseModel):
    text: str
    basis_urls: list[str]
    method: Literal["evidence_rules"] = "evidence_rules"
    limitation: str


class LifeCategory(BaseModel):
    theme: str
    evidence: list[LifeEvidence] = Field(default_factory=list)
    inference: LifeInference | None = None
    next_step: str
    search_url: str


class LifeResearchSnapshot(BaseModel):
    school_name: str
    country: str | None = None
    checked_at: datetime | None = None
    status: Literal["not_collected", "ready", "partial", "unavailable"] = "not_collected"
    evidence: list[LifeEvidence] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)
    location_signature: str = ""
    extraction_version: int = EXTRACTION_VERSION


class SchoolLifeContext(BaseModel):
    school_name: str
    location_note: str
    research_status: str
    checked_at: datetime | None = None
    can_refresh: bool = True
    source_count: int = 0
    categories: list[LifeCategory]
    research_notes: list[str] = Field(default_factory=list)


def _identity(partner: PartnerUniversity) -> tuple[str, str]:
    return school_identity_key(partner.school_name), partner.country or ""


def reference_record(partner: PartnerUniversity) -> dict:
    if not REFERENCE_DATA.exists():
        return {}
    records = json.loads(REFERENCE_DATA.read_text(encoding="utf-8"))
    name, country = school_search_name(partner.school_name).casefold(), partner.country or ""
    return next((row for row in records if row["identity"].casefold() == name and row["country"] == country), {})


@lru_cache(maxsize=1)
def _bundled_ntnu_student_experiences() -> dict[tuple[str, str], tuple[StudentExperienceSource, ...]]:
    by_key: dict[tuple[str, str], list[StudentExperienceSource]] = {}
    for school_code in ("ntnu", "cycu", "ntust", "yzu", "fcu", "nsysu", "nchu", "ntut", "nccu", "ncku", "nycu", "nthu", "pccu", "wzu", "nkust", "yuntech", "ntou", "ncue", "nknu", "tmu", "csmu", "cmu", "kmu", "mcu", "ntub", "ncnu", "ndhu", "thu", "shu"):
        exp_path = Path(__file__).parent / "official_data" / school_code / "student_experiences.jsonl"
        if exp_path.exists():
            with exp_path.open(encoding="utf-8") as handle:
                for line in handle:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        row = StudentExperienceSource.model_validate_json(line)
                        by_key.setdefault((school_identity_key(row.school_name), row.country or ""), []).append(row)
                    except ValueError:
                        continue
    return {k: tuple(v) for k, v in by_key.items()}


def reference_student_sources(partner: PartnerUniversity) -> list[StudentExperienceSource]:
    base = [
        StudentExperienceSource.model_validate({**row, "school_name": partner.school_name, "country": partner.country})
        for row in reference_record(partner).get("student_sources", [])
    ]
    seen_urls = {row.source_url for row in base}
    for row in _bundled_ntnu_student_experiences().get((school_identity_key(partner.school_name), partner.country or ""), ()):
        if row.source_url not in seen_urls:
            seen_urls.add(row.source_url)
            base.append(row.model_copy(update={"school_name": partner.school_name, "country": partner.country}))
    return base


def _cache_path(partner: PartnerUniversity, data_dir: Path) -> Path:
    key = hashlib.sha256("|".join(_identity(partner)).encode()).hexdigest()
    return Path(data_dir) / "processed" / "life_research" / f"{key}.json"


def reviewed_life_snapshot(snapshot: LifeResearchSnapshot) -> LifeResearchSnapshot:
    """Exclude error chrome and exact generated claims already withdrawn by review."""
    evidence = [row for row in snapshot.evidence if not any(
        re.search(r"^(?:404|403|not found)\b", source.title.strip(), re.I)
        or re.search(r"/(?:error/)?404(?:[/.]|$)", urlsplit(source.url).path)
        for source in row.sources
    )]
    notes = list(snapshot.notes)
    if len(evidence) != len(snapshot.evidence):
        notes.append("已排除錯誤頁的導覽文字；相關生活資料待補查。")
    filtered = [row for row in evidence if not withdrawn_life_claim(
        snapshot.school_name, snapshot.country, row)]
    generated_removed = len(filtered) != len(evidence)
    if generated_removed:
        notes.append("已排除先前撤下的範本、導覽文字或有誤舊摘錄；相關生活資料仍待逐校核對。")
    if len(filtered) == len(snapshot.evidence):
        return snapshot
    return snapshot.model_copy(update={
        "evidence": filtered,
        "status": "partial" if filtered or generated_removed else "unavailable",
        "notes": notes,
    })


class _LifeSnapshotIndex(Mapping):
    """Keep compact validated JSON; return fresh models only for requested hosts."""
    def __init__(self, records):
        self._records = records

    def __getitem__(self, key):
        return LifeResearchSnapshot.model_validate_json(self._records[key])

    def __iter__(self):
        return iter(self._records)

    def __len__(self):
        return len(self._records)


@lru_cache(maxsize=1)
def _bundled_ntu_research() -> Mapping[tuple[str, str], LifeResearchSnapshot]:
    records = {}
    if BUNDLED_NTU_LIFE.exists():
        with BUNDLED_NTU_LIFE.open(encoding="utf-8") as handle:
            for line in handle:
                try:
                    row = reviewed_life_snapshot(LifeResearchSnapshot.model_validate_json(line))
                    if row.extraction_version == EXTRACTION_VERSION:
                        records[(school_identity_key(row.school_name), row.country or "")] = row.model_dump_json().encode("utf-8")
                except ValueError:
                    continue
    return _LifeSnapshotIndex(records)


@lru_cache(maxsize=1)
def _bundled_extra_research() -> Mapping[tuple[str, str], LifeResearchSnapshot]:
    records = {}
    bundled_files = (
        Path(__file__).parent / "official_data" / "fju" / "student_life.jsonl",
        Path(__file__).parent / "official_data" / "scu" / "student_life.jsonl",
        Path(__file__).parent / "official_data" / "ntnu" / "student_life.jsonl",
        Path(__file__).parent / "official_data" / "cycu" / "student_life.jsonl",
        Path(__file__).parent / "official_data" / "ntust" / "student_life.jsonl",
        Path(__file__).parent / "official_data" / "yzu" / "student_life.jsonl",
        Path(__file__).parent / "official_data" / "fcu" / "student_life.jsonl",
        Path(__file__).parent / "official_data" / "nsysu" / "student_life.jsonl",
        Path(__file__).parent / "official_data" / "nchu" / "student_life.jsonl",
        Path(__file__).parent / "official_data" / "ntut" / "student_life.jsonl",
        Path(__file__).parent / "official_data" / "nccu" / "student_life.jsonl",
        Path(__file__).parent / "official_data" / "ncku" / "student_life.jsonl",
        Path(__file__).parent / "official_data" / "nycu" / "student_life.jsonl",
        Path(__file__).parent / "official_data" / "nthu" / "student_life.jsonl",
        Path(__file__).parent / "official_data" / "pccu" / "student_life.jsonl",
        Path(__file__).parent / "official_data" / "wzu" / "student_life.jsonl",
        Path(__file__).parent / "official_data" / "nkust" / "student_life.jsonl",
        Path(__file__).parent / "official_data" / "yuntech" / "student_life.jsonl",
        Path(__file__).parent / "official_data" / "ntou" / "student_life.jsonl",
        Path(__file__).parent / "official_data" / "ncue" / "student_life.jsonl",
        Path(__file__).parent / "official_data" / "nknu" / "student_life.jsonl",
        Path(__file__).parent / "official_data" / "tmu" / "student_life.jsonl",
        Path(__file__).parent / "official_data" / "csmu" / "student_life.jsonl",
        Path(__file__).parent / "official_data" / "cmu" / "student_life.jsonl",
        Path(__file__).parent / "official_data" / "kmu" / "student_life.jsonl",
        Path(__file__).parent / "official_data" / "mcu" / "student_life.jsonl",
        Path(__file__).parent / "official_data" / "ntub" / "student_life.jsonl",
        Path(__file__).parent / "official_data" / "ncnu" / "student_life.jsonl",
        Path(__file__).parent / "official_data" / "ndhu" / "student_life.jsonl",
        Path(__file__).parent / "official_data" / "thu" / "student_life.jsonl",
        Path(__file__).parent / "official_data" / "shu" / "student_life.jsonl",
    )
    for life_path in bundled_files:
        if life_path.exists():
            with life_path.open(encoding="utf-8") as handle:
                for line in handle:
                    try:
                        row = reviewed_life_snapshot(LifeResearchSnapshot.model_validate_json(line))
                        if row.extraction_version == EXTRACTION_VERSION:
                            records.setdefault((school_identity_key(row.school_name), row.country or ""), row.model_dump_json().encode("utf-8"))
                    except ValueError:
                        continue
    return _LifeSnapshotIndex(records)


def read_research(partner: PartnerUniversity, data_dir: Path) -> LifeResearchSnapshot:
    path = _cache_path(partner, data_dir)
    empty_cache = None
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
        if raw.get("extraction_version") != EXTRACTION_VERSION:
            raw = {}
        snapshot = reviewed_life_snapshot(LifeResearchSnapshot.model_validate(raw))
        if snapshot.country == partner.country and school_identity_key(snapshot.school_name) == _identity(partner)[0]:
            if snapshot.evidence:
                return snapshot
            empty_cache = snapshot
    except (OSError, ValueError):
        pass
    # These are host-school facts, keyed by exact school and country; they do
    # not grant home-school eligibility, quotas or guaranteed accommodation.
    if bundled := _bundled_ntu_research().get(_identity(partner)):
        return bundled
    if extra := _bundled_extra_research().get(_identity(partner)):
        return extra
    return empty_cache or LifeResearchSnapshot(school_name=partner.school_name, country=partner.country)


def research_is_fresh(snapshot: LifeResearchSnapshot) -> bool:
    checked = snapshot.checked_at
    return bool(checked and checked.tzinfo and timedelta() <= datetime.now(timezone.utc) - checked < timedelta(hours=6))


def _location_signature(location: UniversityLocation) -> str:
    return f"{location.geocode_status}:{location.latitude}:{location.longitude}:{location.precision}"


def _for_location(snapshot: LifeResearchSnapshot, location: UniversityLocation) -> LifeResearchSnapshot:
    if snapshot.location_signature == _location_signature(location):
        return snapshot
    if not any(row.kind == "geographic" for row in snapshot.evidence):
        # Official school-wide excerpts do not depend on a map point.
        return snapshot.model_copy(update={"location_signature": _location_signature(location)})
    # A corrected campus must never inherit nearby places from the old point.
    return snapshot.model_copy(update={"checked_at": None, "status": "not_collected",
        "evidence": [row for row in snapshot.evidence if row.kind != "geographic"]})


def _profile_evidence(profile: DestinationProfile) -> list[LifeEvidence]:
    if not profile.coverage_status.startswith("official_"):
        return []
    if profile.home_university == "國立中央大學":
        from .ncu_student_view import ncu_field_audit
        audit = ncu_field_audit(profile.school_name)
        if not audit or not any(
            source["status"] == "reviewed_partial_scope" for source in audit["read_sources"]
        ):
            return []
        # These sections were assembled field by field with explicit source
        # scopes. A caveat in one point must not erase the other reference
        # points, and their source year must remain visible to students.
        themes = {
            "housing": "housing", "cost": "cost", "transport": "transport",
            "courses": "academics", "arrival": "social", "city": "campus_culture",
            "insurance": "safety", "visa": "safety",
        }
        rows = []
        for section in profile.student_guide_sections:
            theme = themes.get(section.key)
            keys = ("tuition", "cost") if section.key == "cost" else (
                ("courses", "study_period") if section.key == "courses" else (section.key,)
            )
            if not any(audit["fields"].get(key, {}).get("original_evidence")
                       and audit["fields"][key]["status"] != "missing" for key in keys):
                continue
            sources = [LifeSource(title=section.title, url=url)
                       for url in section.source_urls if public_https_url(url)]
            if theme and section.points and sources:
                scope = "；".join(filter(None, (section.summary, section.caution)))
                rows.append(LifeEvidence(
                    theme=theme, kind="official", text="\n".join(section.points),
                    sources=sources, checked_at=profile.last_checked, scope=scope,
                ))
        return rows
    sources = [LifeSource(title=s.title, url=s.source_url) for s in profile.sources if public_https_url(s.source_url)]
    if not sources:
        return []
    rows = []
    # Do not relabel the generic survival checklist as verified geographic facts.
    for theme, field in (("housing", "housing_summary"), ("cost", "cost_summary"),
                         ("transport", "transport_summary"), ("social", "campus_life_summary")):
        value = getattr(profile, field)
        if unreviewed_profile_claim(profile, field, value):
            continue
        if value and not re.search(r"未公開|尚未|不足|待查|待確認|無法.*核對", value):
            addition = school_field_addition(profile, field)
            field_sources = ([LifeSource(title=s["title_zh"], url=s["url"]) for s in addition["sources"]]
                if addition else sources[:4])
            checked = (datetime.fromisoformat(addition["sources"][0]["read_at"])
                if addition and addition["sources"][0].get("read_at") else profile.last_checked)
            rows.append(LifeEvidence(theme=theme, kind="official", text=value,
                sources=field_sources, checked_at=checked))
    return rows


def _inference(theme: str, evidence: list[LifeEvidence]) -> LifeInference | None:
    # Conservative planning deductions only. Never infer safety, prices, quality,
    # insurance eligibility, opening times or teaching from city/campus location.
    grounded = [row for row in evidence if row.sources and row.kind in {"official", "geographic"}]
    if not grounded or theme not in {"food", "transport", "housing", "safety"}:
        return None
    text = {
        "food": "可將這些地點列為用餐與採買候選，再比對上課校區及宿舍位置。",
        "transport": "可比較住宿到上述站點的路線，評估通勤選擇。",
        "housing": "先確認交換生住宿資格，再把交通與餐食納入預算。",
        "safety": "可先查詢上述健康服務；接診、語言與保險適用性仍須確認。",
    }[theme]
    return LifeInference(text=text, basis_urls=list(dict.fromkeys(s.url for row in grounded for s in row.sources)),
                         limitation="AI 推論是依列出資料套用規劃規則的參考建議，不是學生親身經驗；未據此推定價格、步行時間或服務品質。")


def _localize_evidence(rows: list[LifeEvidence], data_dir: Path, *, generate: bool = False) -> list[LifeEvidence]:
    candidates = [(row.original_text or row.text, row.sources[0].url) for row in rows
                  if row.kind != "geographic" and row.sources and needs_translation(row.original_text or row.text)]
    if generate:
        translate_public_excerpts(candidates, data_dir)
    localized = []
    for row in rows:
        original = row.original_text or row.text
        if row.kind == "geographic" or not row.sources or not needs_translation(original):
            localized.append(row)
            continue
        translation = cached_translation(original, row.sources[0].url, data_dir)
        localized.append(row.model_copy(update={"original_text": original,
            "text": translation[0] if translation else original,
            "translation_status": translation[1] if translation else "pending"}))
    return localized


def build_life_context(partner: PartnerUniversity, profile: DestinationProfile, location: UniversityLocation, data_dir: Path) -> SchoolLifeContext:
    snapshot = _for_location(read_research(partner, data_dir), location)
    curated = [LifeEvidence.model_validate(row) for row in reference_record(partner).get("evidence", [])]
    candidates = [*curated, *snapshot.evidence, *_profile_evidence(profile)]
    all_rows = _localize_evidence([row for row in candidates if not withdrawn_life_claim(
        partner.school_name, partner.country, row)], data_dir)
    categories = []
    for theme in THEMES:
        seen = set()
        evidence = []
        for row in all_rows:
            if row.theme != theme or row.text in seen:
                continue
            safe_sources = [source for source in row.sources if public_https_url(source.url)]
            if not safe_sources:
                continue
            seen.add(row.text)
            evidence.append(row.model_copy(update={"sources": safe_sources}))
        evidence = evidence[:5]
        query = " ".join(filter(None, (school_search_name(partner.school_name), partner.country, location.city, THEME_QUERIES[theme])))
        categories.append(LifeCategory(theme=theme, evidence=evidence, inference=_inference(theme, evidence),
                                       next_step=NEXT_STEPS[theme], search_url="https://www.google.com/search?" + urlencode({"q": query})))
    located = location.geocode_status == "verified"
    note = (f"地理參考：{location.city or partner.country or ''} · "
            + ("已核對校區座標。" if location.precision == "campus" else "校級代表座標，未必是你的交換校區。")) if located else "尚無已核對的校區座標；不以城市中心代替學校，也不推算附近設施距離。"
    return SchoolLifeContext(school_name=partner.school_name, location_note=note, research_status=snapshot.status,
                             checked_at=snapshot.checked_at, can_refresh=not research_is_fresh(snapshot) or any(row.translation_status == "pending" for row in all_rows), categories=categories,
                             source_count=len({s.url for c in categories for e in c.evidence for s in e.sources}), research_notes=snapshot.notes)


def _official_host(partner: PartnerUniversity) -> str:
    return (urlsplit(partner.website or "").hostname or "").removeprefix("www.")


def _on_official_host(url: str, host: str) -> bool:
    if not public_https_url(url):
        return False
    target = (urlsplit(url).hostname or "").removeprefix("www.")
    return bool(public_https_url(url) and host and (target == host or target.endswith("." + host)))


def _official_research(partner: PartnerUniversity, now: datetime) -> tuple[list[LifeEvidence], str]:
    host = _official_host(partner)
    if not host:
        return [], "尚未確認學校官網，未自動擷取第三方網站作為官方資料。"
    name = school_search_name(partner.school_name)
    # Search snippets are discovery only. A fact is emitted only after reading
    # the page body on the verified university domain (including final URL).
    rows = search_text(f'site:{host} {name} international student campus dining health accommodation transport', max_results=6, timeout_seconds=5)
    urls = list(dict.fromkeys(str(row.get("href") or row.get("url") or "") for row in rows))
    urls = [url for url in urls if _on_official_host(url, host)][:4]
    evidence = []
    with ThreadPoolExecutor(max_workers=3) as pool:
        pages = list(pool.map(read_life_page, urls))
    for page in pages:
        if not page or not _on_official_host(page.final_url, host):
            continue
        sentences = [s.strip() for s in re.split(r"\n+|(?<=[.!?。])\s+", page.text)
                     if 35 <= len(s.strip()) <= 420 and re.search(r"[.!?。！？][\"')）]?$", s.strip())]
        for theme in THEMES:
            pattern = OFFICIAL_THEME_PATTERNS[theme]
            sentence = next((s for s in sentences if re.search(pattern, s, re.I)), None)
            if sentence:
                evidence.append(LifeEvidence(theme=theme, kind="official", text=sentence,
                    sources=[LifeSource(title=page.title or name, url=page.final_url)], checked_at=now,
                    scope=f"{page.title[:100]} · 官網原文自動節錄，校區及適用對象須核對原頁", original_excerpt=True))
    return evidence, f"官網搜尋取得 {len(urls)} 個候選頁，讀到 {len({s.url for e in evidence for s in e.sources})} 個有生活內容的來源；原文節錄未經人工審查。"


def distance_metres(lat1: float, lon1: float, lat2: float, lon2: float) -> int:
    a = math.sin(math.radians(lat2 - lat1) / 2) ** 2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(math.radians(lon2 - lon1) / 2) ** 2
    return round(6371000 * 2 * math.asin(math.sqrt(min(1, max(0, a)))))


def _geographic_research(location: UniversityLocation, now: datetime) -> tuple[list[LifeEvidence], str]:
    if location.geocode_status != "verified" or location.latitude is None or location.longitude is None:
        return [], "沒有已核對座標，本次未搜尋附近設施。"
    lat, lon = location.latitude, location.longitude
    query = (f'[out:json][timeout:8];nwr(around:1500,{lat},{lon})[amenity~"^(hospital|clinic|pharmacy)$"];out center 30;'
             f'(nwr(around:1500,{lat},{lon})[amenity~"^(restaurant|cafe|fast_food)$"];'
             f'nwr(around:1500,{lat},{lon})[shop~"^(supermarket|convenience)$"];);out center 120;'
             f'nwr(around:1500,{lat},{lon})[railway=station];out center 25;')
    result = fetch_public_bytes("https://overpass-api.de/api/interpreter", timeout=10, form={"data": query})
    if not result:
        result = fetch_public_bytes("https://overpass.private.coffee/api/interpreter", timeout=10, form={"data": query})
    if not result:
        return [], "周邊地圖服務暫時無法讀取；不把查詢失敗解讀為附近沒有設施。"
    try:
        payload = json.loads(result[0])
        elements = payload.get("elements", [])
    except (ValueError, AttributeError):
        return [], "周邊地圖回覆無法解析，保留既有資料。"
    rows = []
    for item in elements:
        if not isinstance(item, dict) or not isinstance(item.get("tags", {}), dict):
            continue
        tags = item.get("tags", {})
        name = tags.get("name") or tags.get("name:en")
        if not name or item.get("type") not in {"node", "way", "relation"}:
            continue
        centre = item.get("center", item)
        try:
            y, x = float(centre["lat"]), float(centre["lon"])
            if not (math.isfinite(y) and math.isfinite(x) and -90 <= y <= 90 and -180 <= x <= 180):
                continue
            distance = distance_metres(lat, lon, y, x)
            identity = int(item["id"])
        except (KeyError, TypeError, ValueError):
            continue
        if distance > 1500:
            continue
        amenity = tags.get("amenity")
        if amenity not in {"hospital", "clinic", "pharmacy", "restaurant", "cafe", "fast_food"} and tags.get("shop") not in {"supermarket", "convenience"} and tags.get("railway") != "station":
            continue
        theme = "safety" if amenity in {"hospital", "clinic", "pharmacy"} else "transport" if tags.get("railway") == "station" else "food"
        kinds = {"hospital": "醫院", "clinic": "診所", "pharmacy": "藥局", "restaurant": "餐廳", "cafe": "咖啡店", "fast_food": "速食店", "supermarket": "超市", "convenience": "便利商店", "station": "車站"}
        kind = kinds.get(amenity or tags.get("shop") or tags.get("railway"), "設施")
        source = f'https://www.openstreetmap.org/{item["type"]}/{identity}'
        rows.append((distance, LifeEvidence(theme=theme, kind="geographic", text=f"{str(name)[:100]}（地圖標示：{kind}），距參考座標直線約 {distance} 公尺。",
                    sources=[LifeSource(title="OpenStreetMap 地點資料", url=source)], checked_at=now,
                    scope="1.5 公里範圍的開放地圖紀錄；不是步行路程，未確認營業、可接診或服務品質。")))
    evidence = []
    for theme in ("food", "transport", "safety"):
        evidence.extend([row for _, row in sorted(rows, key=lambda pair: pair[0]) if row.theme == theme][:3])
    note = "周邊地圖來源：© OpenStreetMap contributors（ODbL）；地點可能過時或不完整。"
    if payload.get("remark"):
        note += " 地圖服務回報限制，本次結果可能不完整。"
    return evidence, note


def refresh_life_research(partner: PartnerUniversity, location: UniversityLocation, data_dir: Path) -> LifeResearchSnapshot:
    existing = _for_location(read_research(partner, data_dir), location)
    if research_is_fresh(existing):
        return existing.model_copy(update={"evidence": _localize_evidence(existing.evidence, data_dir, generate=True)})
    if not _research_gate.acquire(blocking=False):
        return existing.model_copy(update={"notes": [*existing.notes, "另一所學校正在補查，請稍後再試。"]})
    try:
        now = datetime.now(timezone.utc)
        with ThreadPoolExecutor(max_workers=2) as pool:
            jobs = [pool.submit(_official_research, partner, now), pool.submit(_geographic_research, location, now)]
            results = []
            for job in jobs:
                try:
                    results.append(job.result())
                except Exception:
                    results.append(([], "部分公開來源暫時無法取得，未以搜尋片段產生事實。"))
        new_rows = _localize_evidence([row for rows, _ in results for row in rows], data_dir, generate=True)
        notes = [note for _, note in results]
        # Network failure must not erase previously collected facts or reset
        # their individual timestamps to a successful-looking current date.
        evidence = list(new_rows)
        keys = {(row.theme, tuple(s.url for s in row.sources)) for row in evidence}
        evidence.extend(row for row in existing.evidence if (row.theme, tuple(s.url for s in row.sources)) not in keys)
        snapshot = LifeResearchSnapshot(school_name=partner.school_name, country=partner.country, checked_at=now,
                    status="ready" if all(rows for rows, _ in results) else "partial" if new_rows else "unavailable",
                    evidence=evidence[:50], notes=notes, location_signature=_location_signature(location))
        path = _cache_path(partner, data_dir)
        path.parent.mkdir(parents=True, exist_ok=True)
        temp = path.with_suffix(f".{uuid4().hex}.tmp")
        temp.write_text(snapshot.model_dump_json(indent=2), encoding="utf-8")
        temp.replace(path)
        return snapshot
    finally:
        _research_gate.release()
