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

AU_OFFICIAL_DATA_DIR = (
    Path(__file__).resolve().parent / "official_data" / "au"
)
AU_INTRO_URL = "https://cia.au.edu.tw/p/403-1022-109353.php?Lang=zh-tw"
AU_PARTNER_LIST_URL = "https://cia.au.edu.tw/p/403-1022-109350.php?Lang=zh-tw"


def _payload(filename: str):
  return json.loads(
      (AU_OFFICIAL_DATA_DIR / filename).read_text(encoding="utf-8")
  )


@lru_cache(maxsize=2)
def _cached_au_partners(
    path: Path, sig: tuple[int, int] | None
) -> tuple[PartnerUniversity, ...]:
  with path.open(encoding="utf-8") as handle:
    return tuple(
        PartnerUniversity.model_validate_json(line)
        for line in handle
        if line.strip()
    )


def fetch_au_partner_universities() -> list[PartnerUniversity]:
  path = AU_OFFICIAL_DATA_DIR / "partners.jsonl"
  return list(_cached_au_partners(path, file_signature(path)))


@lru_cache(maxsize=2)
def _cached_au_dashboard_shell(
    path: Path, sig: tuple[int, int] | None
) -> StudentDashboard:
  raw = json.loads(path.read_text(encoding="utf-8"))
  raw["partner_universities"] = []
  return StudentDashboard.model_validate(raw)


def build_au_student_dashboard(
    *,
    partner_universities: list[PartnerUniversity] | None = None,
    reference_time: datetime | None = None,
) -> StudentDashboard:
  path = AU_OFFICIAL_DATA_DIR / "student_dashboard.json"
  dashboard = _cached_au_dashboard_shell(path, file_signature(path))
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
                    or "依真理大學國際事務中心（CIA）最新公告之國外／日本姐妹校交換學生、雙聯學制及教育部學海系列／本校出國獎助學金甄選時程辦理。"
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
              else fetch_au_partner_universities()
          ),
      }
  )


@lru_cache(maxsize=2)
def _cached_au_exchange_info(
    path: Path, sig: tuple[int, int] | None
) -> ExchangeInfo:
  return ExchangeInfo.model_validate(
      json.loads(path.read_text(encoding="utf-8"))
  )


def au_exchange_info(
    partners: list[PartnerUniversity] | None = None,
) -> ExchangeInfo:
  path = AU_OFFICIAL_DATA_DIR / "exchange_info.json"
  info = _cached_au_exchange_info(path, file_signature(path))
  resolved = (
      partners if partners is not None else fetch_au_partner_universities()
  )
  return info.model_copy(
      update={"partner_universities": [p.school_name for p in resolved]}
  )


@lru_cache(maxsize=2)
def _cached_au_pages(
    path: Path, sig: tuple[int, int] | None
) -> tuple[ProcessedPage, ...]:
  with path.open(encoding="utf-8") as handle:
    return tuple(
        ProcessedPage.model_validate_json(line)
        for line in handle
        if line.strip()
    )


def au_processed_pages() -> list[ProcessedPage]:
  path = AU_OFFICIAL_DATA_DIR / "pages.jsonl"
  return list(_cached_au_pages(path, file_signature(path)))


def au_school_location(
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
