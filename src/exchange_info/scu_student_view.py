from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from .models import (
    ApplicationPeriodStatus,
    ExchangeInfo,
    PartnerUniversity,
    ProcessedPage,
    StudentDashboard,
)
from .student_view import _application_period_status

SCU_OFFICIAL_DATA_DIR = Path(__file__).resolve().parent / "official_data" / "scu"
SCU_INTRO_URL = "https://icae.scu.edu.tw/zh-hant/outbound-exchange/intro"
SCU_PARTNER_LIST_URL = "https://icae.scu.edu.tw/zh-hant/outbound-exchange/intl/2025-2026schools"


from functools import lru_cache
from .storage import file_signature


def _payload(filename: str):
    return json.loads((SCU_OFFICIAL_DATA_DIR / filename).read_text(encoding="utf-8"))


@lru_cache(maxsize=2)
def _cached_scu_partners(path: Path, sig: tuple[int, int] | None) -> tuple[PartnerUniversity, ...]:
    with path.open(encoding="utf-8") as handle:
        return tuple(PartnerUniversity.model_validate_json(line) for line in handle if line.strip())


def fetch_scu_partner_universities() -> list[PartnerUniversity]:
    path = SCU_OFFICIAL_DATA_DIR / "partners.jsonl"
    return list(_cached_scu_partners(path, file_signature(path)))


@lru_cache(maxsize=2)
def _cached_scu_dashboard_shell(path: Path, sig: tuple[int, int] | None) -> StudentDashboard:
    raw = json.loads(path.read_text(encoding="utf-8"))
    raw["partner_universities"] = []
    return StudentDashboard.model_validate(raw)


def build_scu_student_dashboard(
    *,
    partner_universities: list[PartnerUniversity] | None = None,
    reference_time: datetime | None = None,
) -> StudentDashboard:
    path = SCU_OFFICIAL_DATA_DIR / "student_dashboard.json"
    dashboard = _cached_scu_dashboard_shell(path, file_signature(path))
    now = reference_time or datetime.now(timezone.utc)
    periods = []
    for period in dashboard.application_periods:
        if period.deadline_at is None:
            periods.append(period)
            continue
        if period.opens_at is not None:
            status = _application_period_status(now, opens_at=period.opens_at, deadline_at=period.deadline_at)
        else:
            status = (
                ApplicationPeriodStatus.CLOSED
                if now > period.deadline_at
                else ApplicationPeriodStatus.ACTION_REQUIRED
            )
        periods.append(
            period.model_copy(
                update={
                    "status": status,
                    "status_note": period.status_note or "依東吳大學國際與兩岸學術交流事務處公告之 116 學年度甄選時程辦理。",
                }
            )
        )
    return dashboard.model_copy(
        update={
            "application_periods": periods,
            "partner_universities": (
                list(partner_universities)
                if partner_universities is not None
                else fetch_scu_partner_universities()
            ),
        }
    )


@lru_cache(maxsize=2)
def _cached_scu_exchange_info(path: Path, sig: tuple[int, int] | None) -> ExchangeInfo:
    return ExchangeInfo.model_validate(json.loads(path.read_text(encoding="utf-8")))


def scu_exchange_info(partners: list[PartnerUniversity] | None = None) -> ExchangeInfo:
    path = SCU_OFFICIAL_DATA_DIR / "exchange_info.json"
    info = _cached_scu_exchange_info(path, file_signature(path))
    resolved = partners if partners is not None else fetch_scu_partner_universities()
    return info.model_copy(update={"partner_universities": [p.school_name for p in resolved]})


@lru_cache(maxsize=2)
def _cached_scu_pages(path: Path, sig: tuple[int, int] | None) -> tuple[ProcessedPage, ...]:
    with path.open(encoding="utf-8") as handle:
        return tuple(ProcessedPage.model_validate_json(line) for line in handle if line.strip())


def scu_processed_pages() -> list[ProcessedPage]:
    path = SCU_OFFICIAL_DATA_DIR / "pages.jsonl"
    return list(_cached_scu_pages(path, file_signature(path)))


def scu_school_location(partner: PartnerUniversity, fallback, data_dir: Path | None = None):
    if data_dir is not None:
        from .university_locations import local_location_override

        operator = local_location_override(data_dir, partner.school_name, partner.country)
        if operator is not None:
            return operator
    if partner.location is not None and partner.location.geocode_status == "verified":
        return partner.location
    return fallback
