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


def _payload(filename: str):
    return json.loads((SCU_OFFICIAL_DATA_DIR / filename).read_text(encoding="utf-8"))


def fetch_scu_partner_universities() -> list[PartnerUniversity]:
    with (SCU_OFFICIAL_DATA_DIR / "partners.jsonl").open(encoding="utf-8") as handle:
        return [PartnerUniversity.model_validate_json(line) for line in handle if line.strip()]


def build_scu_student_dashboard(
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


def scu_exchange_info(partners: list[PartnerUniversity] | None = None) -> ExchangeInfo:
    info = ExchangeInfo.model_validate(_payload("exchange_info.json"))
    resolved = partners if partners is not None else fetch_scu_partner_universities()
    return info.model_copy(update={"partner_universities": [p.school_name for p in resolved]})


def scu_processed_pages() -> list[ProcessedPage]:
    with (SCU_OFFICIAL_DATA_DIR / "pages.jsonl").open(encoding="utf-8") as handle:
        return [ProcessedPage.model_validate_json(line) for line in handle if line.strip()]


def scu_school_location(partner: PartnerUniversity, fallback, data_dir: Path | None = None):
    if data_dir is not None:
        from .university_locations import local_location_override

        operator = local_location_override(data_dir, partner.school_name, partner.country)
        if operator is not None:
            return operator
    if partner.location is not None and partner.location.geocode_status == "verified":
        return partner.location
    return fallback
