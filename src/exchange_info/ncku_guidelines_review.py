"""Source-bound 116-1 mother rules and date-aware application windows."""
from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from zoneinfo import ZoneInfo

from .host_source_review_round25 import apply_review_manifest, pointer_parent
from .ntust_source_review import write_atomic

MANIFEST = "docs/data-verification-20261021/round44-ncku-guidelines-review.json"
MANIFEST_SHA256 = "5122276e0dbea63c79c58f949076a25ef2d49d1bc1ee271d5ade83e0bb9980f2"
DISPLAY_MANIFEST = "docs/data-verification-20261021/round44-ncku-display-followup.json"
DISPLAY_SHA256 = "749cc18e0ed227604a687b0180f704f15d3db0400eda5fc34ae4fd0532760a46"
ARCHIVE_KEY = "source_review_round44"
GUIDE_URL = "https://oia.ncku.edu.tw/var/file/32/1032/img/107138261.pdf"


def ncku_1161_rules_apply(partner, academic_year=None, application_round=None) -> bool:
    evidence = partner.field_evidence.get("home_degree_requirement")
    return bool(
        partner.academic_year == "116"
        and academic_year in (None, "", "116")
        and application_round in (None, "", "116-1", partner.application_round)
        and evidence is not None and evidence.source_url == GUIDE_URL
        and evidence.academic_year == "116" and evidence.application_round == "116-1"
        and evidence.status == "verified_current"
    )


def load_manifest(root: Path) -> dict:
    raw = (root / MANIFEST).read_bytes()
    if hashlib.sha256(raw).hexdigest() != MANIFEST_SHA256:
        raise ValueError("NCKU 116-1 guidelines review manifest hash mismatch")
    return json.loads(raw)


def apply_ncku_guidelines_review(root: Path) -> int:
    manifest = load_manifest(root)
    display_raw = (root / DISPLAY_MANIFEST).read_bytes()
    if hashlib.sha256(display_raw).hexdigest() != DISPLAY_SHA256:
        raise ValueError("NCKU guidelines display follow-up manifest hash mismatch")
    # The manifest explicitly preserves and updates profile metadata itself.
    changed = apply_review_manifest(root, "ncku", manifest, ARCHIVE_KEY, manage_profile_context=False)
    for scope in manifest["singletons"]:
        path = root / scope["file"]
        row = json.loads(path.read_text("utf8"))
        for patch in scope["patches"]:
            try:
                parent, key = pointer_parent(row, patch["pointer"])
                old, exists = parent[key], True
            except (KeyError, IndexError):
                old, exists = None, False
            if exists and (old == patch["value"] or old not in patch["expected_values"]):
                continue
            if not exists and not patch["expected_missing"]:
                continue
            parent, key = pointer_parent(row, patch["pointer"], create=True)
            archive = row.setdefault("reference_data", {}).setdefault(ARCHIVE_KEY, {})
            archive.setdefault(patch["pointer"], {"existed": exists, "value": old})
            parent[key] = patch["value"]
            changed += 1
        write_atomic(path, row)
    return changed + apply_review_manifest(root, "ncku", json.loads(display_raw),
                                          "source_review_round44_display", manage_profile_context=False)


def ncku_1161_window(reference_time: datetime | None = None) -> str:
    """An opening date without a stated hour cannot establish midnight opening."""
    now = reference_time or datetime.now(timezone.utc)
    if now.utcoffset() is None:
        raise ValueError("NCKU application-window reference time must include a timezone")
    local = now.astimezone(ZoneInfo("Asia/Taipei"))
    day = local.date().isoformat()
    if day < "2026-10-30":
        return "upcoming"
    if day == "2026-10-30":
        return "needs_confirmation"
    return "open" if local <= datetime(2026, 11, 19, 16, tzinfo=local.tzinfo) else "closed"


def current_ncku_application_window(partner, reference_time: datetime | None = None):
    evidence = partner.field_evidence.get("application_window_status")
    if (partner.academic_year != "116" or ARCHIVE_KEY not in partner.reference_data or evidence is None
            or evidence.source_url != GUIDE_URL or evidence.academic_year != "116"
            or evidence.application_round != "116-1" or evidence.status != "verified_current"):
        return partner
    return partner.model_copy(update={"application_window_status": ncku_1161_window(reference_time)})
