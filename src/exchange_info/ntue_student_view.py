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

NTUE_OFFICIAL_DATA_DIR = (
    Path(__file__).resolve().parent / "official_data" / "ntue"
)
NTUE_INTRO_URL = "https://oia.ntue.edu.tw/p/405-1066-46773,c4763.php?Lang=zh-tw"
NTUE_PARTNER_LIST_URL = "https://oia.ntue.edu.tw/p/405-1066-46779,c4938.php?Lang=zh-tw"


def _payload(filename: str):
    return json.loads(
        (NTUE_OFFICIAL_DATA_DIR / filename).read_text(encoding="utf-8")
    )


@lru_cache(maxsize=2)
def _cached_ntue_partners(
    path: Path, sig: tuple[int, int] | None
) -> tuple[PartnerUniversity, ...]:
    with path.open(encoding="utf-8") as handle:
        return tuple(
            PartnerUniversity.model_validate_json(line)
            for line in handle
            if line.strip()
        )


def fetch_ntue_partner_universities() -> list[PartnerUniversity]:
    path = NTUE_OFFICIAL_DATA_DIR / "partners.jsonl"
    return list(_cached_ntue_partners(path, file_signature(path)))


@lru_cache(maxsize=2)
def _cached_ntue_dashboard_shell(
    path: Path, sig: tuple[int, int] | None
) -> StudentDashboard:
    raw = json.loads(path.read_text(encoding="utf-8"))
    raw["partner_universities"] = []
    return StudentDashboard.model_validate(raw)


def build_ntue_student_dashboard(
    *,
    partner_universities: list[PartnerUniversity] | None = None,
    reference_time: datetime | None = None,
) -> StudentDashboard:
    path = NTUE_OFFICIAL_DATA_DIR / "student_dashboard.json"
    dashboard = _cached_ntue_dashboard_shell(path, file_signature(path))
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
                        or "依國立臺北教育大學國際事務處國際學生事務組（行政大樓 7 樓 A709／A710 室）最新公告時程辦理。"
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
                else fetch_ntue_partner_universities()
            ),
        }
    )


@lru_cache(maxsize=2)
def _cached_ntue_exchange_info(
    path: Path, sig: tuple[int, int] | None
) -> ExchangeInfo:
    return ExchangeInfo.model_validate(
        json.loads(path.read_text(encoding="utf-8"))
    )


def ntue_exchange_info(
    partners: list[PartnerUniversity] | None = None,
) -> ExchangeInfo:
    path = NTUE_OFFICIAL_DATA_DIR / "exchange_info.json"
    info = _cached_ntue_exchange_info(path, file_signature(path))
    resolved = (
        partners if partners is not None else fetch_ntue_partner_universities()
    )
    return info.model_copy(
        update={"partner_universities": [p.school_name for p in resolved]}
    )


@lru_cache(maxsize=2)
def _cached_ntue_pages(
    path: Path, sig: tuple[int, int] | None
) -> tuple[ProcessedPage, ...]:
    with path.open(encoding="utf-8") as handle:
        return tuple(
            ProcessedPage.model_validate_json(line)
            for line in handle
            if line.strip()
        )


def ntue_processed_pages() -> list[ProcessedPage]:
    path = NTUE_OFFICIAL_DATA_DIR / "pages.jsonl"
    return list(_cached_ntue_pages(path, file_signature(path)))


def ntue_school_location(
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
