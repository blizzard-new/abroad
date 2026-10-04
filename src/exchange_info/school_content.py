"""Source-bound additions to school details, independent of review approvals."""
from __future__ import annotations

import json
import re
from functools import lru_cache
from pathlib import Path

from .models import DestinationProfile, PageCategory, SourceReference
from .school_identity import school_identity_key
from .university_locations import load_university_locations, location_key

SUPPLEMENTS = Path(__file__).parent / "official_data" / "school_content_supplements.json"
FIELDS = {"cost_summary", "housing_summary", "transport_summary", "campus_life_summary"}


@lru_cache(maxsize=1)
def _city_names() -> dict:
    return json.loads(SUPPLEMENTS.with_name("city_names_zh.json").read_text(encoding="utf-8"))


def _city_chinese(value: str) -> str:
    # Translate display names only; coordinates and campus identities stay intact.
    names = _city_names()
    pattern = "|".join(re.escape(name) for name in sorted(names, key=len, reverse=True))
    return re.sub(pattern, lambda match: names[match[0]], value)


@lru_cache(maxsize=1)
def _supplements() -> dict:
    if not SUPPLEMENTS.exists():
        return {}
    rows = json.loads(SUPPLEMENTS.read_text(encoding="utf-8"))
    return {(school_identity_key(r["home_university"]), school_identity_key(r["school_name"]),
        r["country"]): r for r in rows}


def school_field_addition(profile: DestinationProfile, field: str) -> dict | None:
    """Attribute an applied addition to its own evidence, not other profile URLs."""
    key = (school_identity_key(profile.home_university or ""),
        school_identity_key(profile.school_name), profile.country)
    return next((item for item in _supplements().get(key, {}).get("fields", [])
        if item.get("field") == field and getattr(profile, field, None) == item.get("summary_zh")), None)


def complete_destination_profile(profile: DestinationProfile, data_dir: Path, *, locations: dict | None = None) -> DestinationProfile:
    """Only fill the exact gaps researched; never overwrite later operator edits."""
    key = (school_identity_key(profile.home_university or ""),
        school_identity_key(profile.school_name), profile.country)
    supplement = _supplements().get(key, {})
    updates = {}
    additions = []
    for item in supplement.get("fields", []):
        field = item.get("field")
        if (field not in FIELDS or getattr(profile, field) != item.get("previous")
                or not item.get("summary_zh") or not item.get("sources")):
            continue
        updates[field] = item["summary_zh"]
        for source in item["sources"]:
            additions.append(SourceReference(title=source["title_zh"],
                source_url=source["url"], category=PageCategory.PARTNER_SCHOOL,
                summary=source["excerpt_zh"]))
    location = (locations if locations is not None else load_university_locations(data_dir)).get(location_key(profile.school_name, profile.country))
    if not profile.city and location and location.geocode_status == "verified" and location.city:
        updates["city"] = location.city
    if city := updates.get("city") or profile.city:
        chinese_city = _city_chinese(city)
        if chinese_city != profile.city:
            updates["city"] = chinese_city
    if not updates:
        return profile
    if additions:
        sources = {source.source_url: source for source in profile.sources}
        sources.update({source.source_url: source for source in additions})
        updates.update(sources=list(sources.values()), coverage_status="official_partial",
            coverage_note="已依所列官方頁面補充部分生活資訊，保留來源與適用限制；"
                "此次補查與翻譯不代表真人雙人審核。費用為原頁參考值，申請前請核對當期公告。")
    return profile.model_copy(update=updates)
