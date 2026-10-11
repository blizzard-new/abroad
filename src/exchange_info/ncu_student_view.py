from __future__ import annotations
import json
import gzip
import threading
from datetime import datetime, timezone
from collections import OrderedDict
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


# Cache serialized, scoped records rather than two complete all-school graphs.
# Each caller parses its own result, so mutations cannot leak to another reader.
_AUDIT_CACHE_BYTES = 8 * 1024 * 1024
_audit_cache: OrderedDict[tuple, bytes] = OrderedDict()
_audit_cache_bytes = 0


def _json_array_items(handle, chunk_size=256 * 1024):
    """Incrementally decode a top-level array, rejecting truncation/trailing data."""
    decoder = json.JSONDecoder()
    buffer = ""

    def more():
        nonlocal buffer
        chunk = handle.read(chunk_size)
        buffer += chunk
        return bool(chunk)

    def whitespace():
        nonlocal buffer
        buffer = buffer.lstrip()
        while not buffer and more():
            buffer = buffer.lstrip()

    whitespace()
    if not buffer.startswith("["):
        raise json.JSONDecodeError("Expected an array", buffer, 0)
    buffer = buffer[1:]
    whitespace()
    if not buffer.startswith("]"):
        while True:
            while True:
                try:
                    row, end = decoder.raw_decode(buffer)
                    break
                except json.JSONDecodeError:
                    if not more():
                        raise
            buffer = buffer[end:]
            yield row
            whitespace()
            if buffer.startswith("]"):
                break
            if not buffer.startswith(","):
                raise json.JSONDecodeError("Expected comma or closing bracket", buffer, 0)
            buffer = buffer[1:]
            whitespace()
    buffer = buffer[1:]
    whitespace()
    if buffer:
        raise json.JSONDecodeError("Unexpected trailing data", buffer, 0)


def _iter_audit_rows(path: Path):
    opener = gzip.open if path.suffix == ".gz" else open
    with opener(path, "rt", encoding="utf-8") as handle:
        yield from _json_array_items(handle)


def _read_audit_snapshot(path: Path, signature: tuple[int, int], field: str, values: tuple[str, ...]):
    global _audit_cache_bytes
    key = (path, signature, field, values)
    if key in _audit_cache:
        _audit_cache.move_to_end(key)
        return _audit_cache[key]
    selected = set(values)
    rows = [row for row in _iter_audit_rows(path) if row.get(field) in selected]
    payload = json.dumps(rows, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    if len(payload) <= _AUDIT_CACHE_BYTES:
        while _audit_cache and _audit_cache_bytes + len(payload) > _AUDIT_CACHE_BYTES:
            _, old = _audit_cache.popitem(last=False)
            _audit_cache_bytes -= len(old)
        _audit_cache[key] = payload
        _audit_cache_bytes += len(payload)
    return payload


def _clear_audit_cache():
    global _audit_cache_bytes
    with _audit_snapshot_lock:
        _audit_cache.clear()
        _audit_cache_bytes = 0


_read_audit_snapshot.cache_clear = _clear_audit_cache


def _audit_snapshot(filename: str, field: str, values):
    path = NCU_OFFICIAL_DATA_DIR / filename
    stat = path.stat()
    signature = (stat.st_mtime_ns, stat.st_size)
    # Single flight also bounds concurrent cold decompression. Do not retain
    # unrelated institutions' evidence; every selected source remains complete.
    with _audit_snapshot_lock:
        payload = _read_audit_snapshot(path, signature, field, tuple(sorted(values)))
    return json.loads(payload)


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
            for row in _audit_snapshot("field-audit.json", "school_name", (school_name,))
            if row["school_name"] == school_name
        ),
        None,
    )
    return row


def ncu_source_audit(school_name: str) -> dict | None:
    audit = ncu_field_audit(school_name)
    if audit is None:
        return None
    source_ids = {source["id"] for source in audit["read_sources"]}
    return {
        **audit,
        "source_evidence": [
            row
            for row in _audit_snapshot("source-evidence.json.gz", "id", source_ids)
            if row["id"] in source_ids
        ],
    }
