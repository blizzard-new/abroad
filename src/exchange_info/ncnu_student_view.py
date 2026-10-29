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

NCNU_OFFICIAL_DATA_DIR = (
    Path(__file__).resolve().parent / "official_data" / "ncnu"
)
NCNU_INTRO_URL = "https://oia.ncnu.edu.tw/p/412-1017-269.php?Lang=zh-tw"
NCNU_PARTNER_LIST_URL = (
    "https://docs.google.com/spreadsheets/d/1iLyMA1wtTgx_Ygkbcc3Dps179qrr_-g_-7OzivUsslA/edit?usp=sharing"
)


def _payload(filename: str):
  return json.loads(
      (NCNU_OFFICIAL_DATA_DIR / filename).read_text(encoding="utf-8")
  )


@lru_cache(maxsize=2)
def _cached_ncnu_partners(
    path: Path, sig: tuple[int, int] | None
) -> tuple[PartnerUniversity, ...]:
  with path.open(encoding="utf-8") as handle:
    return tuple(
        PartnerUniversity.model_validate_json(line)
        for line in handle
        if line.strip()
    )


def fetch_ncnu_partner_universities() -> list[PartnerUniversity]:
  path = NCNU_OFFICIAL_DATA_DIR / "partners.jsonl"
  return list(_cached_ncnu_partners(path, file_signature(path)))


@lru_cache(maxsize=2)
def _cached_ncnu_dashboard_shell(
    path: Path, sig: tuple[int, int] | None
) -> StudentDashboard:
  raw = json.loads(path.read_text(encoding="utf-8"))
  raw["partner_universities"] = []
  return StudentDashboard.model_validate(raw)


def build_ncnu_student_dashboard(
    *,
    partner_universities: list[PartnerUniversity] | None = None,
    reference_time: datetime | None = None,
) -> StudentDashboard:
  path = NCNU_OFFICIAL_DATA_DIR / "student_dashboard.json"
  dashboard = _cached_ncnu_dashboard_shell(path, file_signature(path))
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
                    or "依國立暨南國際大學國際及兩岸事務處最新公告之海外姊妹校交換生、大陸及港澳地區交換生、跨國雙聯學位與教育部學海獎補助時程辦理。"
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
              else fetch_ncnu_partner_universities()
          ),
      }
  )


@lru_cache(maxsize=2)
def _cached_ncnu_exchange_info(
    path: Path, sig: tuple[int, int] | None
) -> ExchangeInfo:
  return ExchangeInfo.model_validate(
      json.loads(path.read_text(encoding="utf-8"))
  )


def ncnu_exchange_info(
    partners: list[PartnerUniversity] | None = None,
) -> ExchangeInfo:
  path = NCNU_OFFICIAL_DATA_DIR / "exchange_info.json"
  info = _cached_ncnu_exchange_info(path, file_signature(path))
  resolved = (
      partners if partners is not None else fetch_ncnu_partner_universities()
  )
  return info.model_copy(
      update={"partner_universities": [p.school_name for p in resolved]}
  )


@lru_cache(maxsize=2)
def _cached_ncnu_pages(
    path: Path, sig: tuple[int, int] | None
) -> tuple[ProcessedPage, ...]:
  with path.open(encoding="utf-8") as handle:
    return tuple(
        ProcessedPage.model_validate_json(line)
        for line in handle
        if line.strip()
    )


def ncnu_processed_pages() -> list[ProcessedPage]:
  path = NCNU_OFFICIAL_DATA_DIR / "pages.jsonl"
  return list(_cached_ncnu_pages(path, file_signature(path)))


def ncnu_school_location(
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
