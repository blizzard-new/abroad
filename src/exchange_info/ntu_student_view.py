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


from functools import lru_cache
from .storage import file_signature


def _payload(filename: str):
    return json.loads((NTU_OFFICIAL_DATA_DIR / filename).read_text(encoding="utf-8"))


@lru_cache(maxsize=2)
def _cached_ntu_partners(path: Path, sig: tuple[int, int] | None) -> tuple[PartnerUniversity, ...]:
    return tuple(
        with_ntu_partner_summary(PartnerUniversity.model_validate_json(line))
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    )


def fetch_ntu_partner_universities() -> list[PartnerUniversity]:
    """Use the reviewed source snapshot offline, keeping unpublished quotas pending."""
    path = NTU_OFFICIAL_DATA_DIR / "partners.jsonl"
    return list(_cached_ntu_partners(path, file_signature(path)))


@lru_cache(maxsize=2)
def _cached_ntu_dashboard_shell(path: Path, sig: tuple[int, int] | None) -> StudentDashboard:
    raw = json.loads(path.read_text(encoding="utf-8"))
    raw["partner_universities"] = []
    return StudentDashboard.model_validate(raw)


def build_ntu_student_dashboard(
    *, partner_universities: list[PartnerUniversity] | None = None,
    reference_time: datetime | None = None,
) -> StudentDashboard:
    path = NTU_OFFICIAL_DATA_DIR / "student_dashboard.json"
    dashboard = _cached_ntu_dashboard_shell(path, file_signature(path))
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


@lru_cache(maxsize=2)
def _cached_ntu_exchange_info(path: Path, sig: tuple[int, int] | None) -> ExchangeInfo:
    return ExchangeInfo.model_validate(json.loads(path.read_text(encoding="utf-8")))


def ntu_exchange_info(partners: list[PartnerUniversity] | None = None) -> ExchangeInfo:
    path = NTU_OFFICIAL_DATA_DIR / "exchange_info.json"
    info = _cached_ntu_exchange_info(path, file_signature(path))
    return info.model_copy(update={"partner_universities": [p.school_name for p in (partners if partners is not None else fetch_ntu_partner_universities())]})


@lru_cache(maxsize=2)
def _cached_ntu_pages(path: Path, sig: tuple[int, int] | None) -> tuple[ProcessedPage, ...]:
    return tuple(ProcessedPage.model_validate_json(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip())


def ntu_processed_pages() -> list[ProcessedPage]:
    path = NTU_OFFICIAL_DATA_DIR / "pages.jsonl"
    return list(_cached_ntu_pages(path, file_signature(path)))
