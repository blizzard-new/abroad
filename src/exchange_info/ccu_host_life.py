"""Host-published services for CCU students, independent of term-specific eligibility."""
from __future__ import annotations

import json
from datetime import datetime
from functools import lru_cache
from pathlib import Path

from .models import DestinationProfile, PageCategory, SourceReference, StudentGuideSection

SERVICES = Path(__file__).parent / "official_data" / "ccu" / "host-life-services.json"


@lru_cache(maxsize=1)
def _services() -> tuple[datetime, dict]:
    review = json.loads(SERVICES.read_text(encoding="utf-8"))
    return datetime.fromisoformat(review["checked_at"]), {row["school_name"]: row for row in review["profiles"]}


def with_host_life_service(profile: DestinationProfile) -> DestinationProfile:
    checked, reviews = _services()
    review = reviews.get(profile.school_name)
    if (not review or (profile.last_checked and profile.last_checked.date() > checked.date())
            or any(section.key == "host_life_service" for section in profile.student_guide_sections)):
        return profile
    section = StudentGuideSection(
        key="host_life_service", title=review["title"], summary=review["summary"],
        points=[review["next_step"]], source_urls=[s["url"] for s in review["sources"]],
        evidence_type="official", caution=f"接待校一般服務查核於 {checked.date().isoformat()}。當期床位與報到安排以個別通知為準。",
    )
    sources = {s.source_url: s for s in profile.sources}
    for s in review["sources"]:
        sources.setdefault(s["url"], SourceReference(
            title=s["title"], source_url=s["url"], category=PageCategory.PARTNER_SCHOOL,
            summary=s["excerpt"],
        ))
    updates = dict(student_guide_sections=[section, *profile.student_guide_sections], sources=list(sources.values()))
    if profile.coverage_status == "needs_confirmation":
        updates.update(
            coverage_status="official_partial",
            coverage_note="已核對接待校公開的生活服務與聯絡方式。各項當期交換條件的查核狀態列於下方。",
        )
    if profile.last_checked is None or checked.date() > profile.last_checked.date():
        updates["last_checked"] = checked
    return profile.model_copy(update=updates)
