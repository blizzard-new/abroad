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

NPUST_OFFICIAL_DATA_DIR = (
    Path(__file__).resolve().parent / "official_data" / "npust"
)
NPUST_INTRO_URL = (
    "https://oia2.npust.edu.tw/zh/cooperation/%e4%ba%a4%e6%8f%9b%e5%ad%b8%e7%94%9f-2/"
)
NPUST_PARTNER_LIST_URL = "https://oia2.npust.edu.tw/zh/sister-schools/"


def _payload(filename: str):
  return json.loads(
      (NPUST_OFFICIAL_DATA_DIR / filename).read_text(encoding="utf-8")
  )


@lru_cache(maxsize=2)
def _cached_npust_partners(
    path: Path, sig: tuple[int, int] | None
) -> tuple[PartnerUniversity, ...]:
  with path.open(encoding="utf-8") as handle:
    return tuple(
        PartnerUniversity.model_validate_json(line)
        for line in handle
        if line.strip()
    )


def fetch_npust_partner_universities() -> list[PartnerUniversity]:
  path = NPUST_OFFICIAL_DATA_DIR / "partners.jsonl"
  return list(_cached_npust_partners(path, file_signature(path)))


@lru_cache(maxsize=2)
def _cached_npust_dashboard_shell(
    path: Path, sig: tuple[int, int] | None
) -> StudentDashboard:
  raw = json.loads(path.read_text(encoding="utf-8"))
  raw["partner_universities"] = []
  return StudentDashboard.model_validate(raw)


def build_npust_student_dashboard(
    *,
    partner_universities: list[PartnerUniversity] | None = None,
    reference_time: datetime | None = None,
) -> StudentDashboard:
  path = NPUST_OFFICIAL_DATA_DIR / "student_dashboard.json"
  dashboard = _cached_npust_dashboard_shell(path, file_signature(path))
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
                    or "依國立屏東科技大學國際事務處與教務處課務組最新公告之交換學生甄選、跨國雙聯學制及教育部學海系列計畫時程辦理。"
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
              else fetch_npust_partner_universities()
          ),
      }
  )


@lru_cache(maxsize=2)
def _cached_npust_exchange_info(
    path: Path, sig: tuple[int, int] | None
) -> ExchangeInfo:
  return ExchangeInfo.model_validate(
      json.loads(path.read_text(encoding="utf-8"))
  )


def npust_exchange_info(
    partners: list[PartnerUniversity] | None = None,
) -> ExchangeInfo:
  path = NPUST_OFFICIAL_DATA_DIR / "exchange_info.json"
  info = _cached_npust_exchange_info(path, file_signature(path))
  resolved = (
      partners if partners is not None else fetch_npust_partner_universities()
  )
  return info.model_copy(
      update={"partner_universities": [p.school_name for p in resolved]}
  )


@lru_cache(maxsize=2)
def _cached_npust_pages(
    path: Path, sig: tuple[int, int] | None
) -> tuple[ProcessedPage, ...]:
  with path.open(encoding="utf-8") as handle:
    return tuple(
        ProcessedPage.model_validate_json(line)
        for line in handle
        if line.strip()
    )


def npust_processed_pages() -> list[ProcessedPage]:
  path = NPUST_OFFICIAL_DATA_DIR / "pages.jsonl"
  return list(_cached_npust_pages(path, file_signature(path)))


def npust_school_location(
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
