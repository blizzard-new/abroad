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

ASIA_OFFICIAL_DATA_DIR = (
    Path(__file__).resolve().parent / "official_data" / "asia"
)
ASIA_INTRO_URL = "https://oia.asia.edu.tw/p/412-1008-258.php?Lang=zh-tw"
ASIA_PARTNER_LIST_URL = "https://oia.asia.edu.tw/zh_tw/Map"


def _payload(filename: str):
  return json.loads(
      (ASIA_OFFICIAL_DATA_DIR / filename).read_text(encoding="utf-8")
  )


@lru_cache(maxsize=2)
def _cached_asia_partners(
    path: Path, sig: tuple[int, int] | None
) -> tuple[PartnerUniversity, ...]:
  with path.open(encoding="utf-8") as handle:
    return tuple(
        PartnerUniversity.model_validate_json(line)
        for line in handle
        if line.strip()
    )


def fetch_asia_partner_universities() -> list[PartnerUniversity]:
  path = ASIA_OFFICIAL_DATA_DIR / "partners.jsonl"
  return list(_cached_asia_partners(path, file_signature(path)))


@lru_cache(maxsize=2)
def _cached_asia_dashboard_shell(
    path: Path, sig: tuple[int, int] | None
) -> StudentDashboard:
  raw = json.loads(path.read_text(encoding="utf-8"))
  raw["partner_universities"] = []
  return StudentDashboard.model_validate(raw)


def build_asia_student_dashboard(
    *,
    partner_universities: list[PartnerUniversity] | None = None,
    reference_time: datetime | None = None,
) -> StudentDashboard:
  path = ASIA_OFFICIAL_DATA_DIR / "student_dashboard.json"
  dashboard = _cached_asia_dashboard_shell(path, file_signature(path))
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
                    or "依亞洲大學國際事務處（行政大樓 L105）最新公告之學期交換、亞大 318 亮點計畫、雙聯學位及學海計畫獎助學金時程辦理。"
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
              else fetch_asia_partner_universities()
          ),
      }
  )


@lru_cache(maxsize=2)
def _cached_asia_exchange_info(
    path: Path, sig: tuple[int, int] | None
) -> ExchangeInfo:
  return ExchangeInfo.model_validate(
      json.loads(path.read_text(encoding="utf-8"))
  )


def asia_exchange_info(
    partners: list[PartnerUniversity] | None = None,
) -> ExchangeInfo:
  path = ASIA_OFFICIAL_DATA_DIR / "exchange_info.json"
  info = _cached_asia_exchange_info(path, file_signature(path))
  resolved = (
      partners if partners is not None else fetch_asia_partner_universities()
  )
  return info.model_copy(
      update={"partner_universities": [p.school_name for p in resolved]}
  )


@lru_cache(maxsize=2)
def _cached_asia_pages(
    path: Path, sig: tuple[int, int] | None
) -> tuple[ProcessedPage, ...]:
  with path.open(encoding="utf-8") as handle:
    return tuple(
        ProcessedPage.model_validate_json(line)
        for line in handle
        if line.strip()
    )


def asia_processed_pages() -> list[ProcessedPage]:
  path = ASIA_OFFICIAL_DATA_DIR / "pages.jsonl"
  return list(_cached_asia_pages(path, file_signature(path)))


def asia_school_location(
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
