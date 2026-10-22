"""Verified 2026-10-22 TKU official announcement update: 2027–2028 Info Session Registration Full.

Verifies the 2026-10-22 update on https://enroll.tku.edu.tw/course.aspx?cid=auix1106:
- Registration for the 2027–2028 Outbound Exchange Selection Info Session changed from
  yesterday's 168 participants to FULL (capacity 170: `170 名 (額滿)`).
- Epistemic boundaries:
  1. This is info-session registration full (`說明會報名額滿`), NOT exchange program quota full
     (`不是交換名額額滿`), and NOT an exchange application deadline.
  2. Event time remains 2026/11/06 (Fri) 18:00–19:30 at Ching-sheng International Conference Hall;
     walk-in standby (`現場候補`) is still allowed and seated/arranged after 18:10 according to
     seat availability.
  3. Japanese selection guidelines, 4-school quota table, and 6 scholarship PDFs are unchanged;
     English/European formal new quotas and overseas partner details remain incomplete.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from bs4 import BeautifulSoup

from .models import ProcessedPage, SourceReference, StudentInfoItem

ROOT = Path(__file__).resolve().parents[2]
UPDATE_JSON_PATH = ROOT / "sources" / "tku" / "2026-10-22-official-update.json"

CHECKED_DATE = "2026-10-22"
CHECKED_AT_ISO = "2026-10-22T02:30:00+00:00"
INFO_SESSION_URL = "https://enroll.tku.edu.tw/course.aspx?cid=auix1106"
DASHBOARD_OVERVIEW_TITLE = "2027–2028 年赴姊妹校交換生聯合甄選說明會報名額滿與現場候補提醒（2026-10-22 查核）"


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def load_tku_oct22_update_payload(update_json_path: Path = UPDATE_JSON_PATH) -> dict[str, Any]:
    if not update_json_path.exists():
        raise FileNotFoundError(f"Missing TKU Oct 22 update JSON: {update_json_path}")
    payload = json.loads(update_json_path.read_text(encoding="utf-8"))
    if payload.get("school_id") != "tku" or payload.get("checked_date") != "2026-10-22":
        raise ValueError("Invalid TKU Oct 22 update payload metadata")
    if (
        payload.get("treated_as_exchange_application_deadline") is not False
        or payload.get("treated_as_exchange_program_quota_full") is not False
        or payload.get("english_and_european_new_quotas_confirmed") is not False
    ):
        raise ValueError(
            "TKU Oct 22 info session full status must not be treated as exchange quota full or application deadline"
        )
    info = payload.get("info_session_registration_update", {})
    if (
        info.get("capacity") != 170
        or info.get("registered_count_before_20261021") != 168
        or info.get("registered_count_after_20261022") != 170
        or info.get("registration_status") != "full"
        or info.get("walk_in_standby_allowed") is not True
        or info.get("check_in_priority_cutoff") != "18:10"
    ):
        raise ValueError("Unexpected TKU Oct 22 info session registration counts or standby rules")
    return payload


def validate_tku_oct22_update_snapshot(update_json_path: Path = UPDATE_JSON_PATH) -> dict[str, Any]:
    payload = load_tku_oct22_update_payload(update_json_path)
    manifest = payload.get("source_manifest", {})
    if set(manifest) != {"enroll_auix1106_20261022"}:
        raise ValueError("Expected enroll_auix1106_20261022 in TKU Oct 22 source_manifest")
    meta = manifest["enroll_auix1106_20261022"]
    local_path = (ROOT / meta["local_file"]).resolve()
    if not local_path.is_relative_to((ROOT / "sources/tku/2026-10-22-official").resolve()):
        raise ValueError("Invalid TKU Oct 22 archive path")
    if not local_path.exists():
        raise FileNotFoundError(f"Missing archived TKU Oct 22 HTML: {local_path}")
    raw = local_path.read_bytes()
    if len(raw) != meta["bytes"]:
        raise ValueError(f"Byte count mismatch for enroll_auix1106_20261022: expected {meta['bytes']}, got {len(raw)}")
    if _sha256_bytes(raw) != meta["sha256"]:
        raise ValueError("SHA256 mismatch for enroll_auix1106_20261022")
    text = BeautifulSoup(raw, "html.parser").get_text(" ", strip=True)
    if "(額滿)" not in text or "170 名" not in text or "18:10" not in text:
        raise ValueError("Archived TKU enroll_auix1106 HTML does not contain verified full/18:10 text")
    return payload


def tku_oct22_program_overview_item() -> StudentInfoItem:
    payload = validate_tku_oct22_update_snapshot()
    info = payload["info_session_registration_update"]
    return StudentInfoItem(
        title=DASHBOARD_OVERVIEW_TITLE,
        details=[
            f"報名狀態更新：2027–2028 年赴姊妹校交換生聯合甄選說明會線上報名人數由昨日 168 人變為額滿（容量 {info['capacity']} 人，系統顯示「{info['status_display']}」）。",
            f"時間與現場候補規則：活動時間仍為 2026/11/06（五）18:00–19:30（{info['venue']}）；已完成線上報名者請於 18:10 前報到，未完成線上報名者仍可於當日現場報到排隊候補，工作人員將於 18:10 後視現場座位狀況安排入座或站區位置。",
            "查核邊界聲明：這是說明會報名額滿，不是交換名額額滿，亦非交換生出國申請截止；日語二甄簡章、4 校表與 6 份獎學金 PDF 未變，英歐組正式新名額及海外詳情仍待後續查核。",
        ],
        source=SourceReference(
            title=info["title"],
            source_url=info["registration_url"],
            summary="查核2026-10-22；說明會報名由168人變為170名額滿（非交換名額額滿），仍可現場候補並於18:10後視座位安排。",
        ),
    )


def tku_oct22_sources() -> list[SourceReference]:
    payload = validate_tku_oct22_update_snapshot()
    meta = payload["source_manifest"]["enroll_auix1106_20261022"]
    return [
        SourceReference(
            title=meta["title"],
            source_url=meta["url"],
            summary="查核2026-10-22；2027–2028交換甄選說明會線上報名達170人額滿（非交換名額額滿），當日仍開放現場候補（18:10後安排）。",
        )
    ]


def tku_oct22_processed_pages() -> list[ProcessedPage]:
    payload = validate_tku_oct22_update_snapshot()
    meta = payload["source_manifest"]["enroll_auix1106_20261022"]
    info = payload["info_session_registration_update"]
    return [
        ProcessedPage(
            title=f"淡江 {DASHBOARD_OVERVIEW_TITLE}",
            source_url=info["registration_url"],
            text=(
                f"{info['title']}（2026-10-22 查核更新）\n"
                f"報名狀態：由昨日 {info['registered_count_before_20261021']} 人變為 {info['status_display']}（容量 {info['capacity']} 人）\n"
                "活動時間：2026/11/06（五）18:00–19:30\n"
                f"活動地點：{info['venue']}\n"
                f"現場候補規定：{info['walk_in_standby_rule']}\n"
                f"邊界聲明：{info['epistemic_boundary']}"
            ),
            summary="查核2026-10-22；2027–2028 交換甄選說明會報名額滿（170人），非交換名額額滿；仍可現場候補並於 18:10 後安排入座。",
            category="info_session",
            crawled_at=CHECKED_DATE,
            content_hash=meta["sha256"],
        )
    ]
