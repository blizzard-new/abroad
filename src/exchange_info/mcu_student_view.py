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

MCU_OFFICIAL_DATA_DIR = (
    Path(__file__).resolve().parent / "official_data" / "mcu"
)
MCU_INTRO_URL = "https://iee.mcu.edu.tw/%E5%87%BA%E5%9C%8B%E7%95%99%E5%AD%B8%E8%A8%88%E7%95%AB%E8%AA%AA%E6%98%8E/"
MCU_PARTNER_LIST_URL = "https://iee.mcu.edu.tw/%E5%87%BA%E5%9C%8B%E7%95%99%E5%AD%B8%E5%AD%B8%E6%A0%A1%E4%B8%80%E8%A6%BD%E8%A1%A8/"


def _payload(filename: str):
  return json.loads(
      (MCU_OFFICIAL_DATA_DIR / filename).read_text(encoding="utf-8")
  )


@lru_cache(maxsize=2)
def _cached_mcu_partners(
    path: Path, sig: tuple[int, int] | None
) -> tuple[PartnerUniversity, ...]:
  with path.open(encoding="utf-8") as handle:
    return tuple(
        PartnerUniversity.model_validate_json(line)
        for line in handle
        if line.strip()
    )


def fetch_mcu_partner_universities() -> list[PartnerUniversity]:
  path = MCU_OFFICIAL_DATA_DIR / "partners.jsonl"
  return list(_cached_mcu_partners(path, file_signature(path)))


@lru_cache(maxsize=2)
def _cached_mcu_dashboard_shell(
    path: Path, sig: tuple[int, int] | None
) -> StudentDashboard:
  raw = json.loads(path.read_text(encoding="utf-8"))
  raw["partner_universities"] = []
  return StudentDashboard.model_validate(raw)


def build_mcu_student_dashboard(
    *,
    partner_universities: list[PartnerUniversity] | None = None,
    reference_time: datetime | None = None,
) -> StudentDashboard:
  path = MCU_OFFICIAL_DATA_DIR / "student_dashboard.json"
  dashboard = _cached_mcu_dashboard_shell(path, file_signature(path))
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
                    or "依銘傳大學國際教育交流處（IEE）及僑陸事務組最新公告之海外留學交換、雙學位、赴大陸頂尖大學交換與獎助學金時程辦理。"
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
              else fetch_mcu_partner_universities()
          ),
      }
  )


@lru_cache(maxsize=2)
def _cached_mcu_exchange_info(
    path: Path, sig: tuple[int, int] | None
) -> ExchangeInfo:
  return ExchangeInfo.model_validate(
      json.loads(path.read_text(encoding="utf-8"))
  )


def mcu_exchange_info(
    partners: list[PartnerUniversity] | None = None,
) -> ExchangeInfo:
  path = MCU_OFFICIAL_DATA_DIR / "exchange_info.json"
  info = _cached_mcu_exchange_info(path, file_signature(path))
  resolved = (
      partners if partners is not None else fetch_mcu_partner_universities()
  )
  return info.model_copy(
      update={"partner_universities": [p.school_name for p in resolved]}
  )


@lru_cache(maxsize=2)
def _cached_mcu_pages(
    path: Path, sig: tuple[int, int] | None
) -> tuple[ProcessedPage, ...]:
  with path.open(encoding="utf-8") as handle:
    return tuple(
        ProcessedPage.model_validate_json(line)
        for line in handle
        if line.strip()
    )


def mcu_processed_pages() -> list[ProcessedPage]:
  path = MCU_OFFICIAL_DATA_DIR / "pages.jsonl"
  return list(_cached_mcu_pages(path, file_signature(path)))


def mcu_school_location(
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
