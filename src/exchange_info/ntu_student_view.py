from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from .models import ApplicationPeriodStatus, ExchangeInfo, PartnerUniversity, ProcessedPage, StudentDashboard
from .student_view import _application_period_status
from .ntu_eligibility import ntu_home_rules, ntu_selection_rules
from .ntu_partner_summary import with_ntu_partner_summary


NTU_OFFICIAL_DATA_DIR = Path(__file__).resolve().parent / "official_data" / "ntu"
NTU_GUIDELINES_URL = "https://studyabroad.ntu.edu.tw/wp-content/uploads/2026/07/116-1-Selection-Guidelines_CH.pdf"


def _payload(filename: str):
    return json.loads((NTU_OFFICIAL_DATA_DIR / filename).read_text(encoding="utf-8"))


def fetch_ntu_partner_universities() -> list[PartnerUniversity]:
    """Use the reviewed source snapshot offline, keeping unpublished quotas pending."""
    return [
        with_ntu_partner_summary(PartnerUniversity.model_validate_json(line))
        for line in (NTU_OFFICIAL_DATA_DIR / "partners.jsonl").read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def build_ntu_student_dashboard(
    *, partner_universities: list[PartnerUniversity] | None = None,
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
            status = ApplicationPeriodStatus.CLOSED if now > period.deadline_at else ApplicationPeriodStatus.ACTION_REQUIRED
        periods.append(period.model_copy(update={
            "status": status,
            "status_note": "已公告的校內甄選時程；是否適用此階段須依申請及錄取狀態確認。",
            "reminder_eligible": False,
        }))
    return dashboard.model_copy(update={
        "selection_rules": ntu_selection_rules(),
        "language_score_minimums": ntu_home_rules()["language_score_minimums"],
        "application_periods": periods,
        "partner_universities": [with_ntu_partner_summary(p) for p in partner_universities] if partner_universities is not None else fetch_ntu_partner_universities(),
    })


def ntu_exchange_info(partners: list[PartnerUniversity] | None = None) -> ExchangeInfo:
    info = ExchangeInfo.model_validate(_payload("exchange_info.json"))
    return info.model_copy(update={"partner_universities": [p.school_name for p in (partners if partners is not None else fetch_ntu_partner_universities())]})


def ntu_processed_pages() -> list[ProcessedPage]:
    return [ProcessedPage.model_validate_json(line) for line in (NTU_OFFICIAL_DATA_DIR / "pages.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]
