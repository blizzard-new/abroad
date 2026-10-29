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

NSYSU_OFFICIAL_DATA_DIR = (
    Path(__file__).resolve().parent / "official_data" / "nsysu"
)
NSYSU_INTRO_URL = "https://oia.nsysu.edu.tw/p/412-1308-20539.php?Lang=zh-tw"
NSYSU_PARTNER_LIST_URL = (
    "https://oia.nsysu.edu.tw/p/412-1308-20623.php?Lang=zh-tw"
)
NSYSU_OCT21_TIMELINE_NOTICE_URL = (
    "https://oia.nsysu.edu.tw/p/405-1308-384613,c20621.php?Lang=zh-tw"
)
NSYSU_2027_2028_BROCHURE_URL = (
    "https://oia.nsysu.edu.tw/p/405-1308-384608,c20621.php?Lang=zh-tw"
)


def _payload(filename: str):
    return json.loads(
        (NSYSU_OFFICIAL_DATA_DIR / filename).read_text(encoding="utf-8")
    )


@lru_cache(maxsize=2)
def _cached_nsysu_partners(
    path: Path, sig: tuple[int, int] | None
) -> tuple[PartnerUniversity, ...]:
    with path.open(encoding="utf-8") as handle:
        return tuple(
            PartnerUniversity.model_validate_json(line)
            for line in handle
            if line.strip()
        )


def fetch_nsysu_partner_universities() -> list[PartnerUniversity]:
    path = NSYSU_OFFICIAL_DATA_DIR / "partners.jsonl"
    return list(_cached_nsysu_partners(path, file_signature(path)))


@lru_cache(maxsize=2)
def _cached_nsysu_dashboard_shell(
    path: Path, sig: tuple[int, int] | None
) -> StudentDashboard:
    raw = json.loads(path.read_text(encoding="utf-8"))
    raw["partner_universities"] = []
    return StudentDashboard.model_validate(raw)


def build_nsysu_student_dashboard(
    *,
    partner_universities: list[PartnerUniversity] | None = None,
    reference_time: datetime | None = None,
) -> StudentDashboard:
    path = NSYSU_OFFICIAL_DATA_DIR / "student_dashboard.json"
    dashboard = _cached_nsysu_dashboard_shell(path, file_signature(path))
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
                    "status_note": period.status_note
                    or "依國立中山大學國際事務處公告之出國交換甄選簡章與線上甄選系統時程辦理。",
                }
            )
        )
    return dashboard.model_copy(
        update={
            "application_periods": periods,
            "partner_universities": (
                list(partner_universities)
                if partner_universities is not None
                else fetch_nsysu_partner_universities()
            ),
        }
    )


@lru_cache(maxsize=2)
def _cached_nsysu_exchange_info(
    path: Path, sig: tuple[int, int] | None
) -> ExchangeInfo:
    return ExchangeInfo.model_validate(
        json.loads(path.read_text(encoding="utf-8"))
    )


def nsysu_exchange_info(
    partners: list[PartnerUniversity] | None = None,
) -> ExchangeInfo:
    path = NSYSU_OFFICIAL_DATA_DIR / "exchange_info.json"
    info = _cached_nsysu_exchange_info(path, file_signature(path))
    resolved = (
        partners
        if partners is not None
        else fetch_nsysu_partner_universities()
    )
    return info.model_copy(
        update={"partner_universities": [p.school_name for p in resolved]}
    )


@lru_cache(maxsize=2)
def _cached_nsysu_pages(
    path: Path, sig: tuple[int, int] | None
) -> tuple[ProcessedPage, ...]:
    with path.open(encoding="utf-8") as handle:
        return tuple(
            ProcessedPage.model_validate_json(line)
            for line in handle
            if line.strip()
        )


def nsysu_processed_pages() -> list[ProcessedPage]:
    path = NSYSU_OFFICIAL_DATA_DIR / "pages.jsonl"
    return list(_cached_nsysu_pages(path, file_signature(path)))


def nsysu_school_location(
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
