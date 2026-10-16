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

FJU_OFFICIAL_DATA_DIR = Path(__file__).resolve().parent / "official_data" / "fju"
FJU_PROCESS_URL = "https://iscoie.fju.edu.tw/generalServices.jsp?labelID=39"
FJU_PARTNER_LIST_URL = "https://iscoie.fju.edu.tw/generalServices.jsp?labelID=40"


def _payload(filename: str):
    return json.loads((FJU_OFFICIAL_DATA_DIR / filename).read_text(encoding="utf-8"))


def fetch_fju_partner_universities() -> list[PartnerUniversity]:
    with (FJU_OFFICIAL_DATA_DIR / "partners.jsonl").open(encoding="utf-8") as handle:
        return [PartnerUniversity.model_validate_json(line) for line in handle if line.strip()]


def build_fju_student_dashboard(
    *,
    partner_universities: list[PartnerUniversity] | None = None,
    reference_time: datetime | None = None,
) -> StudentDashboard:
    dashboard = StudentDashboard.model_validate(_payload("student_dashboard.json"))
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
                    "status_note": period.status_note or "依輔大國際學生中心公告之甄選時程；正式送件與開放日期以當期最新公告為準。",
                }
            )
        )
    return dashboard.model_copy(
        update={
            "application_periods": periods,
            "partner_universities": (
                list(partner_universities)
                if partner_universities is not None
                else fetch_fju_partner_universities()
            ),
        }
    )


def fju_exchange_info(partners: list[PartnerUniversity] | None = None) -> ExchangeInfo:
    info = ExchangeInfo.model_validate(_payload("exchange_info.json"))
    resolved = partners if partners is not None else fetch_fju_partner_universities()
    return info.model_copy(update={"partner_universities": [p.school_name for p in resolved]})


def fju_processed_pages() -> list[ProcessedPage]:
    with (FJU_OFFICIAL_DATA_DIR / "pages.jsonl").open(encoding="utf-8") as handle:
        return [ProcessedPage.model_validate_json(line) for line in handle if line.strip()]


def fju_school_location(partner: PartnerUniversity, fallback, data_dir: Path | None = None):
    if data_dir is not None:
        from .university_locations import local_location_override

        operator = local_location_override(data_dir, partner.school_name, partner.country)
        if operator is not None:
            return operator
    if partner.location is not None and partner.location.geocode_status == "verified":
        return partner.location
    return fallback

