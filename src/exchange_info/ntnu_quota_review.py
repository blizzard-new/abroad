"""Value-guarded review of NTNU's complete 116-1 public quota list."""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

from .host_source_review_round25 import apply_review_manifest
from .ntust_source_review import write_atomic

MANIFEST = "docs/data-verification-20261021/round39-ntnu-live-quota-review.json"
MANIFEST_SHA256 = "bd9309f7e0bccdd99bc09f454c83fc085a5e6a9d47b6868ef78bf41ed759f686"


def load_manifest(root: Path):
    raw = (root / MANIFEST).read_bytes()
    if hashlib.sha256(raw).hexdigest() != MANIFEST_SHA256:
        raise ValueError("NTNU live quota review manifest hash mismatch")
    return json.loads(raw)


def apply_ntnu_quota_review(root: Path):
    manifest = load_manifest(root)
    changed = apply_review_manifest(root, "ntnu", manifest, "source_review_round39")
    folder = root / "src/exchange_info/official_data/ntnu"
    # These files contain legacy publication markers, not proof of a complete
    # factual review. Retain their original values and state this review's scope.
    for filename in ("catalog-completeness.json", "verification_status.json"):
        path = folder / filename
        if not path.exists():
            continue
        payload = json.loads(path.read_text("utf8"))
        archive = payload.setdefault("source_review_round39", {})
        if filename == "catalog-completeness.json":
            if payload.get("open_partners") == 236:
                archive.setdefault("open_partners", 236)
                payload["open_partners"] = 72
                changed += 1
        else:
            if payload.get("status") == "official_verified":
                archive.setdefault("status", payload["status"])
                payload["status"] = "official_partial"
                changed += 1
            if payload.get("counts", {}).get("open_partners") == 236:
                archive.setdefault("counts/open_partners", 236)
                payload["counts"]["open_partners"] = 72
                changed += 1
        payload["quota_review"] = {
            "reviewed_at": manifest["reviewed_at"], "source": "https://bds.oia.ntnu.edu.tw/bds/web/outgoing-quotalist",
            "contracts": 285, "schools": 236, "all_contracts_equal_archived_1161": True,
            "school_categories": manifest["school_categories"], "whole_schools_verified": 0,
            "scope": "僅核對 116-1 全頁名額、合約層級與校級申請日期；其他欄位的舊 verified 標記不代表本輪核實。",
        }
        write_atomic(path, payload)
    return changed


def current_ntnu_application_window(partner, reference_time: datetime | None = None):
    """Re-evaluate only the reviewed, purely university-level 116-1 entries.

    The PDF gives the opening date without an opening hour. On that date,
    confirm the system itself instead of inventing a midnight opening time.
    Mixed/departmental contracts retain their separately pending deadlines.
    """
    if (partner.academic_year != "116" or partner.application_window_status != "upcoming"
            or "source_review_round39" not in partner.reference_data):
        return partner
    now = reference_time or datetime.now(timezone.utc)
    if now.tzinfo is None:
        raise ValueError("NTNU application-window reference time must include a timezone")
    local = now.astimezone(ZoneInfo("Asia/Taipei"))
    day = local.date().isoformat()
    status = ("upcoming" if day < "2026-11-01" else "needs_confirmation" if day == "2026-11-01"
              else "open" if local <= datetime(2026, 11, 15, 23, 59, 59, tzinfo=local.tzinfo) else "closed")
    return partner.model_copy(update={"application_window_status": status})
