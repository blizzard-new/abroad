from __future__ import annotations

from datetime import datetime, timezone
from functools import lru_cache
import json
from pathlib import Path

from .models import (
    ApplicationPeriodStatus,
    ExchangeInfo,
    PartnerUniversity,
    ProcessedPage,
    StudentDashboard,
)
from .storage import file_signature
from .student_view import _application_period_status

NTUNHS_OFFICIAL_DATA_DIR = (
    Path(__file__).resolve().parent / "official_data" / "ntunhs"
)
NTUNHS_INTRO_URL = "https://icsed-rnd.ntunhs.edu.tw/p/412-1037-3251.php?Lang=zh-tw"
NTUNHS_PARTNER_LIST_URL = "https://icsed-rnd.ntunhs.edu.tw/p/412-1037-3250.php?Lang=zh-tw"


def _payload(filename: str):
    return json.loads(
        (NTUNHS_OFFICIAL_DATA_DIR / filename).read_text(encoding="utf-8")
    )


@lru_cache(maxsize=2)
def _cached_ntunhs_partners(
    path: Path, sig: tuple[int, int] | None
) -> tuple[PartnerUniversity, ...]:
    with path.open(encoding="utf-8") as handle:
        return tuple(
            PartnerUniversity.model_validate_json(line)
            for line in handle
            if line.strip()
        )


def fetch_ntunhs_partner_universities() -> list[PartnerUniversity]:
    path = NTUNHS_OFFICIAL_DATA_DIR / "partners.jsonl"
    return list(_cached_ntunhs_partners(path, file_signature(path)))


@lru_cache(maxsize=2)
def _cached_ntunhs_dashboard_shell(
    path: Path, sig: tuple[int, int] | None
) -> StudentDashboard:
    raw = json.loads(path.read_text(encoding="utf-8"))
    raw["partner_universities"] = []
    return StudentDashboard.model_validate(raw)


def build_ntunhs_student_dashboard(
    *,
    partner_universities: list[PartnerUniversity] | None = None,
    reference_time: datetime | None = None,
) -> StudentDashboard:
    path = NTUNHS_OFFICIAL_DATA_DIR / "student_dashboard.json"
    dashboard = _cached_ntunhs_dashboard_shell(path, file_signature(path))
    now = reference_time or datetime.now(timezone.utc)
    periods = []
    for period in dashboard.application_periods:
        if period.deadline_at is None:
            periods.append(period)
            continue
        if period.opens_at is not None:
            status = _application_period_status(
                now, opens_at=period.opens_at, deadline_at=period.deadline_at
            )
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
                    "status_note": (
                        period.status_note
                        or "依國立臺北護理健康大學研究發展處國際暨兩岸教育中心最新公告之海外長短期交換、跨國雙聯學位、海外專業實習及教育部學海系列獎學金甄選簡章時程辦理。"
                    ),
                }
            )
        )
    return dashboard.model_copy(
        update={
            "application_periods": periods,
            "partner_universities": (
                list(partner_universities)
                if partner_universities is not None
                else fetch_ntunhs_partner_universities()
            ),
        }
    )


@lru_cache(maxsize=2)
def _cached_ntunhs_exchange_info(
    path: Path, sig: tuple[int, int] | None
) -> ExchangeInfo:
    return ExchangeInfo.model_validate(
        json.loads(path.read_text(encoding="utf-8"))
    )


def ntunhs_exchange_info(
    partners: list[PartnerUniversity] | None = None,
) -> ExchangeInfo:
    path = NTUNHS_OFFICIAL_DATA_DIR / "exchange_info.json"
    info = _cached_ntunhs_exchange_info(path, file_signature(path))
    resolved = (
        partners
        if partners is not None
        else fetch_ntunhs_partner_universities()
    )
    return info.model_copy(
        update={"partner_universities": [p.school_name for p in resolved]}
    )


@lru_cache(maxsize=2)
def _cached_ntunhs_pages(
    path: Path, sig: tuple[int, int] | None
) -> tuple[ProcessedPage, ...]:
    with path.open(encoding="utf-8") as handle:
        return tuple(
            ProcessedPage.model_validate_json(line)
            for line in handle
            if line.strip()
        )


def ntunhs_processed_pages() -> list[ProcessedPage]:
    path = NTUNHS_OFFICIAL_DATA_DIR / "pages.jsonl"
    return list(_cached_ntunhs_pages(path, file_signature(path)))


def ntunhs_school_location(
    partner: PartnerUniversity, fallback, data_dir: Path | None = None
):
    if data_dir is not None:
        from .university_locations import local_location_override

        operator = local_location_override(
            data_dir, partner.school_name, partner.country
        )
        if operator is not None:
            return operator
    if (
        partner.location is not None
        and partner.location.geocode_status == "verified"
    ):
        return partner.location
    return fallback
