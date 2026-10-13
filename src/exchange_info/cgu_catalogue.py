"""CGU's complete, dated catalogue, shared by every API reader.

Only a validated two-sheet batch can replace the saved catalogue. Source failure
never changes year, quota, availability or publication values in retained rows.
The bundled snapshot also survives an ephemeral host's restart during an outage.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import hashlib
import json
import os
from pathlib import Path
import tempfile
import threading
import time
from typing import Callable

import requests

from .models import CatalogueSourceStatus, PartnerUniversity
from .student_view import (
    DOUBLE_DEGREE_SHEET_ID, DOUBLE_DEGREE_SOURCE_URL,
    EXCHANGE_SHEET_ID, EXCHANGE_SOURCE_URL,
    _departmental_reference_partners, _merge_partner_universities,
    _parse_gviz_payload, _partner_rows_from_payload,
)
from .school_identity import school_identity_key

BUNDLED_SNAPSHOT = Path(__file__).parent / "official_data/cgu_catalogue/snapshot.json"
SOURCE_IDS = {EXCHANGE_SHEET_ID, DOUBLE_DEGREE_SHEET_ID}
SOURCE_URLS = [EXCHANGE_SOURCE_URL, DOUBLE_DEGREE_SOURCE_URL]
MAX_SNAPSHOT_BYTES = 8 * 1024 * 1024


class CatalogueFetchError(ValueError):
    """A classified public-source error; no private path or response body is exposed."""


def records_hash(records: list[dict]) -> str:
    return hashlib.sha256(json.dumps(records, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _stamp(value: str) -> datetime:
    stamp = datetime.fromisoformat(value)
    if stamp.tzinfo is None or stamp > _utc_now() + timedelta(minutes=5):
        raise ValueError("invalid_snapshot_timestamp")
    return stamp


def validate_snapshot(snapshot: dict) -> tuple[PartnerUniversity, ...]:
    if (snapshot["format_version"] != 1 or snapshot["home_school"] != "長庚大學"
            or snapshot["source_state"] != "complete_successful_fetch"):
        raise ValueError("invalid_snapshot_scope")
    stamp = _stamp(snapshot["fetched_at"])
    receipts = snapshot["source_receipts"]
    if len(receipts) != 2 or {r["spreadsheet_id"] for r in receipts} != SOURCE_IDS:
        raise ValueError("incomplete_source_set")
    for receipt in receipts:
        if (receipt["http_status"] != 200 or receipt["schema_valid"] is not True
                or receipt["raw_rows"] <= 0 or len(receipt["sha256"]) != 64
                or not receipt["url"].startswith(f'https://docs.google.com/spreadsheets/d/{receipt["spreadsheet_id"]}/gviz/tq')
                or not _stamp(receipt["requested_at"]) <= _stamp(receipt["completed_at"]) <= stamp):
            raise ValueError("invalid_source_receipt")
    rows = snapshot["records"]
    if not rows or snapshot["record_count"] != len(rows) or snapshot["records_sha256"] != records_hash(rows):
        raise ValueError("invalid_snapshot_payload")
    parsed = tuple(PartnerUniversity.model_validate(row) for row in rows)
    if any(not row.school_name.strip() or not row.source_url for row in parsed):
        raise ValueError("invalid_partner_row")
    return parsed


def fetch_complete_snapshot(timeout_seconds: float = 8.0) -> dict:
    rows, receipts = [], []
    for sheet_id, program_type, source_url in (
        (EXCHANGE_SHEET_ID, "交換學生 / 自費研修", EXCHANGE_SOURCE_URL),
        (DOUBLE_DEGREE_SHEET_ID, "雙學位", DOUBLE_DEGREE_SOURCE_URL),
    ):
        url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:json&sheet=%E7%B8%BD%E8%A1%A8"
        requested_at = _utc_now().isoformat()
        try:
            response = requests.get(url, timeout=timeout_seconds)
            response.raise_for_status()
            if response.status_code != 200:
                raise CatalogueFetchError("http_error")
            if len(response.content) > MAX_SNAPSHOT_BYTES:
                raise CatalogueFetchError("invalid_response")
            payload = _parse_gviz_payload(response.text)
            table = payload["table"]
            labels = [col.get("label") for col in table["cols"]]
            required = {"國家", "校名", "學校網站", "學費資訊", "排名資訊", "名額", "申請資格"}
            required |= {"可申請學院", "可申請學制", "研修期間", "該校申請期限", "該校申請資訊"} if sheet_id == EXCHANGE_SHEET_ID else {"本校可申請學院", "本校可申請學制", "預計研修期間", "申請程序"}
            if any(labels.count(label) != 1 for label in required) or not isinstance(table["rows"], list):
                raise CatalogueFetchError("invalid_response")
            parsed = _partner_rows_from_payload(payload, program_type=program_type, source_url=source_url)
            if not parsed:
                raise CatalogueFetchError("empty_response")
        except requests.Timeout as error:
            raise CatalogueFetchError("timeout") from error
        except requests.HTTPError as error:
            raise CatalogueFetchError("http_error") from error
        except requests.RequestException as error:
            raise CatalogueFetchError("transport_error") from error
        except CatalogueFetchError:
            raise
        except (KeyError, TypeError, ValueError, AttributeError) as error:
            raise CatalogueFetchError("invalid_response") from error
        rows.extend(parsed)
        receipts.append({
            "spreadsheet_id": sheet_id, "url": url, "requested_at": requested_at,
            "completed_at": _utc_now().isoformat(), "http_status": 200,
            "sha256": hashlib.sha256(response.content).hexdigest(),
            "content_type": response.headers.get("Content-Type", ""),
            "schema_valid": True, "raw_rows": len(table["rows"]),
        })
    current_keys = {school_identity_key(row.school_name) for row in rows}
    rows.extend(row for row in _departmental_reference_partners() if school_identity_key(row.school_name) not in current_keys)
    records = [row.model_dump(mode="json") for row in _merge_partner_universities(rows)]
    snapshot = {
        "format_version": 1, "home_school": "長庚大學", "source_state": "complete_successful_fetch",
        "fetched_at": _utc_now().isoformat(), "snapshot_use": "dated_reference_not_current_cycle_verification",
        "unit": "displayed partner rows; not confirmed current-cycle selectable institutions",
        "source_receipts": receipts, "record_count": len(records), "records_sha256": records_hash(records), "records": records,
    }
    validate_snapshot(snapshot)
    return snapshot


@dataclass(frozen=True)
class CatalogueView:
    partners: list[PartnerUniversity]
    source: CatalogueSourceStatus


class CguCatalogue:
    def __init__(self, path: Path, *, bundled: Path | None = BUNDLED_SNAPSHOT,
                 fetcher: Callable[[], dict] = fetch_complete_snapshot,
                 clock: Callable[[], float] = time.monotonic,
                 success_seconds: float = 600, retry_seconds: float = 60):
        self.path, self.fetcher, self.clock = Path(path), fetcher, clock
        self.success_seconds, self.retry_seconds = success_seconds, retry_seconds
        self._lock = threading.Lock()
        self._next_refresh = 0.0
        self._state: tuple[dict | None, tuple[PartnerUniversity, ...], dict | None] = (None, (), None)
        for candidate in (bundled, self.path):
            if candidate is None:
                continue
            try:
                if candidate.stat().st_size > MAX_SNAPSHOT_BYTES:
                    continue
                snapshot = json.loads(candidate.read_text(encoding="utf-8"))
                parsed = validate_snapshot(snapshot)
                if self._state[0] is None or _stamp(snapshot["fetched_at"]) > _stamp(self._state[0]["fetched_at"]):
                    self._state = (snapshot, parsed, None)
            except (OSError, ValueError, KeyError, TypeError, AttributeError):
                continue

    def view(self, *, refresh: bool = True) -> CatalogueView:
        snapshot, partners, attempt = self._state  # one consistent generation per response
        status = "unavailable" if snapshot is None else "saved_reference"
        if attempt and attempt["result"] == "success" and self.clock() < self._next_refresh:
            status = "retrieved"
        view = CatalogueView(
            [row.model_copy(deep=True) for row in partners],
            CatalogueSourceStatus(
                status=status, last_success_at=snapshot["fetched_at"] if snapshot else None,
                snapshot_hash=snapshot["records_sha256"] if snapshot else None,
                last_attempt_at=attempt["at"] if attempt else None,
                last_attempt_result=attempt["result"] if attempt else None,
                failure_reason=attempt.get("reason") if attempt else None,
                source_urls=SOURCE_URLS,
            ),
        )
        if refresh and self.clock() >= self._next_refresh and self._lock.acquire(blocking=False):
            threading.Thread(target=self._refresh_locked, name="cgu-source-refresh", daemon=True).start()
        return view

    def refresh(self) -> CatalogueView:
        """Run a due refresh synchronously (also used by maintenance and acceptance)."""
        if self.clock() >= self._next_refresh and self._lock.acquire(blocking=False):
            self._refresh_locked()
        return self.view(refresh=False)

    def _refresh_locked(self) -> None:
        temp_path = None
        try:
            snapshot = self.fetcher()
            parsed = validate_snapshot(snapshot)
            previous = self._state[0]
            if previous and _stamp(snapshot["fetched_at"]) < _stamp(previous["fetched_at"]):
                raise CatalogueFetchError("older_snapshot")
            self.path.parent.mkdir(parents=True, exist_ok=True)
            with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=self.path.parent, prefix=".cgu-", suffix=".tmp", delete=False) as handle:
                temp_path = Path(handle.name)
                json.dump(snapshot, handle, ensure_ascii=False)
                handle.write("\n")
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temp_path, self.path)
            self._next_refresh = self.clock() + self.success_seconds
            self._state = (snapshot, parsed, {"at": _utc_now(), "result": "success"})
        except Exception as error:
            # Bad source / full disk must not destroy the saved catalogue or poison the next retry.
            reason = str(error) if isinstance(error, CatalogueFetchError) else "storage_failure" if isinstance(error, OSError) else "invalid_response"
            self._next_refresh = self.clock() + self.retry_seconds
            self._state = (*self._state[:2], {"at": _utc_now(), "result": "failed", "reason": reason})
        finally:
            if temp_path is not None:
                try:
                    temp_path.unlink(missing_ok=True)
                except OSError:
                    pass
            self._lock.release()


def create_cgu_catalogue(data_dir: Path) -> CguCatalogue:
    return CguCatalogue(data_dir / "source_cache/cgu_catalogue.json")
