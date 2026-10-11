from __future__ import annotations
import json
import copy
import gzip
import threading
from datetime import datetime, timezone
from functools import lru_cache
from pathlib import Path
from .models import (
    ApplicationPeriodStatus,
    ExchangeInfo,
    PartnerUniversity,
    ProcessedPage,
    StudentDashboard,
)
from .student_view import _application_period_status

NCU_OFFICIAL_DATA_DIR = Path(__file__).parent / "official_data/ncu"
NCU_GUIDELINES_URL = (
    "https://oia.ncu.edu.tw/static/file/26/1026/img/277/116exchangenotice.pdf"
)
NCU_INDEX_URL = "https://oia.ncu.edu.tw/p/412-1026-1872.php?Lang=zh-tw"
NCU_LIST_115_URL = "https://oia.ncu.edu.tw/static/file/26/1026/img/272/115exchangeschoolist-20251127.pdf"
NCU_FORMS_URL = "https://oia.ncu.edu.tw/static/file/26/1026/img/272/forms-2022.pdf"
NCU_CHECKED_AT = datetime(2026, 10, 8, tzinfo=timezone.utc)
_audit_snapshot_lock = threading.Lock()


@lru_cache(maxsize=2)
def _read_audit_snapshot(path: Path, signature: tuple[int, int]):
    raw = path.read_bytes()
    return json.loads(gzip.decompress(raw) if path.suffix == ".gz" else raw)


def _audit_snapshot(filename: str):
    path = NCU_OFFICIAL_DATA_DIR / filename
    stat = path.stat()
    signature = (stat.st_mtime_ns, stat.st_size)
    # A detail requests completeness and source audit concurrently. Parse each
    # immutable bundle once, and invalidate it when the file changes. Returned
    # records below are copied so a caller cannot modify this shared snapshot.
    with _audit_snapshot_lock:
        return _read_audit_snapshot(path, signature)


def _payload(filename):
    return json.loads((NCU_OFFICIAL_DATA_DIR / filename).read_text(encoding="utf-8"))


def fetch_ncu_partner_universities() -> list[PartnerUniversity]:
    # Stream the reviewed JSONL; read_text().splitlines() retains two copies of
    # the whole Unicode source while the validated models are being built.
    with (NCU_OFFICIAL_DATA_DIR / "partners.jsonl").open(encoding="utf-8") as handle:
        return [PartnerUniversity.model_validate_json(line) for line in handle if line.strip()]


def build_ncu_student_dashboard(
    *, partner_universities=None, reference_time=None
) -> StudentDashboard:
    dashboard = StudentDashboard.model_validate(_payload("student_dashboard.json"))
    now = reference_time or datetime.now(timezone.utc)
    periods = []
    for period in dashboard.application_periods:
        if period.deadline_at is None:
            periods.append(period)
            continue
        status = (
            _application_period_status(
                now, opens_at=period.opens_at, deadline_at=period.deadline_at
            )
            if period.opens_at
            else ApplicationPeriodStatus.CLOSED
            if now > period.deadline_at
            else ApplicationPeriodStatus.ACTION_REQUIRED
        )
        periods.append(
            period.model_copy(update={"status": status, "reminder_eligible": False})
        )
    return dashboard.model_copy(
        update={
            "application_periods": periods,
            "partner_universities": partner_universities
            if partner_universities is not None
            else fetch_ncu_partner_universities(),
        }
    )


def ncu_exchange_info(partners=None) -> ExchangeInfo:
    return ExchangeInfo.model_validate(_payload("exchange_info.json")).model_copy(
        update={
            "partner_universities": [
                p.school_name
                for p in (
                    partners
                    if partners is not None
                    else fetch_ncu_partner_universities()
                )
            ]
        }
    )


def ncu_processed_pages() -> list[ProcessedPage]:
    with (NCU_OFFICIAL_DATA_DIR / "pages.jsonl").open(encoding="utf-8") as handle:
        return [ProcessedPage.model_validate_json(line) for line in handle if line.strip()]


def ncu_field_audit(school_name: str) -> dict | None:
    row = next(
        (
            row
            for row in _audit_snapshot("field-audit.json")
            if row["school_name"] == school_name
        ),
        None,
    )
    return copy.deepcopy(row) if row is not None else None


def ncu_source_audit(school_name: str) -> dict | None:
    audit = ncu_field_audit(school_name)
    if audit is None:
        return None
    source_ids = {source["id"] for source in audit["read_sources"]}
    return {
        **audit,
        "source_evidence": [
            copy.deepcopy(row)
            for row in _audit_snapshot("source-evidence.json.gz")
            if row["id"] in source_ids
        ],
    }
