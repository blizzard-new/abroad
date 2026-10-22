"""Round 51 provenance and template review for main's 6 newly onboarded schools.

Binds partner field_evidence to archived mother-school sources, marks regional
template monthly living estimates on destination_profiles as reference_only,
withdraws template-generated student_life and student_experiences testimony
while keeping candidate links, and records whole_partner_records_verified = 0.
"""
from __future__ import annotations

from collections import Counter
from pathlib import Path

from .generated_content_review import (
    ROUND51_MANIFEST,
    ROUND51_MANIFEST_SHA,
    digest,
    load_manifest,
    review_generated_content,
)
from .ntust_source_review import write_atomic

MAIN6_SCHOOLS = ("ncue", "nknu", "tmu", "csmu", "cmu", "kmu")
ARCHIVE_KEY = "source_review_round51"
PARTNER_EVIDENCE_FIELDS = (
    "quota",
    "colleges",
    "degree_levels",
    "language_requirement",
    "study_period",
    "gpa_requirement",
)
COST_NOTE = (
    "原月生活費區間由母校簡章或地區參考範圍整理，尚未逐校核對接待校當期官方費用頁，"
    "僅供規劃參考、不直接判定符合預算。"
)
COVERAGE_NOTE = (
    "母校簡章、雙聯／見實習公告及地區參考整理；個別接待校當期費用、宿位、選課、"
    "校曆與簽證仍須核對接待校官方 Fact Sheet 或入學通知。"
)


def review_main6_school(root: Path, school: str) -> dict[str, int]:
    import json

    manifest = load_manifest(root, round_id=51)
    scope = manifest["schools"][school]
    reviewed_at = manifest["reviewed_at"]
    folder = root / "src/exchange_info/official_data" / school
    counts = review_generated_content(root, school, round_id=51)
    counts.update(partners_changed=0, destinations_changed=0)

    partner_specs = {
        (r["school_name"], r.get("program_type"), r["baseline_fields_sha256"]): r
        for r in scope["partners"]
    }
    partners_path = folder / "partners.jsonl"
    if partners_path.exists():
        partners = [
            json.loads(line)
            for line in partners_path.read_text("utf-8").splitlines()
            if line.strip()
        ]
        for row in partners:
            fields_snap = {k: row.get(k) for k in PARTNER_EVIDENCE_FIELDS}
            spec = partner_specs.get(
                (row["school_name"], row.get("program_type"), digest(fields_snap))
            )
            if spec is None:
                continue
            ref = row.setdefault("reference_data", {})
            if isinstance(ref.get(ARCHIVE_KEY), dict) or (
                row.get("field_evidence") and ARCHIVE_KEY in ref
            ):
                if isinstance(ref.get(ARCHIVE_KEY), dict):
                    ref[ARCHIVE_KEY] = json.dumps(
                        ref[ARCHIVE_KEY], ensure_ascii=False, sort_keys=True
                    )
                    counts["partners_changed"] += 1
                continue
            ref[ARCHIVE_KEY] = json.dumps(
                {
                    "/field_evidence": {
                        "present": "field_evidence" in row,
                        "value": json.loads(json.dumps(row.get("field_evidence", {}))),
                    }
                },
                ensure_ascii=False,
                sort_keys=True,
            )
            row["field_evidence"] = {
                key: {
                    "source_url": spec["source_url"],
                    "status": spec["field_status"],
                    "checked_at": reviewed_at,
                    "note": spec["note"],
                }
                for key in PARTNER_EVIDENCE_FIELDS
            }
            counts["partners_changed"] += 1
        if counts["partners_changed"]:
            write_atomic(partners_path, partners, True)
    else:
        partners = []

    dest_specs = {
        (r["school_name"], r.get("country"), r["baseline_cost_sha256"]): r
        for r in scope["destinations"]
    }
    dest_path = folder / "destination_profiles.jsonl"
    if dest_path.exists():
        destinations = [
            json.loads(line)
            for line in dest_path.read_text("utf-8").splitlines()
            if line.strip()
        ]
        for row in destinations:
            cost_snap = {
                "cost_summary": row.get("cost_summary"),
                "coverage_status": row.get("coverage_status"),
            }
            spec = dest_specs.get(
                (row["school_name"], row.get("country"), digest(cost_snap))
            )
            if spec is None or row.get("cost_evidence") is not None:
                continue
            ref = row.setdefault("reference_data", {})
            arch = ref.setdefault(ARCHIVE_KEY, {})
            for field in ("coverage_status", "coverage_note", "cost_evidence"):
                arch["/" + field] = {
                    "present": field in row,
                    "value": json.loads(json.dumps(row.get(field))),
                }
            row["coverage_status"] = "official_partial"
            row["coverage_note"] = COVERAGE_NOTE
            row["cost_evidence"] = {
                "source_url": spec["source_url"],
                "status": "reference_only",
                "checked_at": reviewed_at,
                "note": COST_NOTE,
            }
            counts["destinations_changed"] += 1
        if counts["destinations_changed"]:
            write_atomic(dest_path, destinations, True)

    avail_counts = Counter(p.get("availability_status") for p in partners)
    audit_meta = {
        "reviewed_at": reviewed_at,
        "manifest": ROUND51_MANIFEST,
        "manifest_sha256": ROUND51_MANIFEST_SHA,
        "whole_partner_records_verified": 0,
        "open_partners": avail_counts.get("open", 0),
        "reference_only_partners": avail_counts.get("reference_only", 0),
        "scope": "僅綁定母校簡章／名冊欄位來源並撤下未逐篇核對的共用生活與心得範本；各接待校當期 Fact Sheet、宿位、費用與選課限制仍待逐校核實。",
    }
    for name in ("catalog-completeness.json", "verification_status.json"):
        meta_path = folder / name
        if not meta_path.exists():
            continue
        payload = json.loads(meta_path.read_text("utf-8"))
        payload.setdefault(ARCHIVE_KEY, {
            "whole_partner_records_verified": payload.get("whole_partner_records_verified"),
        })
        payload["whole_partner_records_verified"] = 0
        payload["round51_audit"] = audit_meta
        if "counts" in payload and isinstance(payload["counts"], dict):
            payload["counts"]["whole_partner_records_verified"] = 0
        write_atomic(meta_path, payload)

    for name in ("import_provenance.json", "import-provenance.json"):
        prov_path = folder / name
        if not prov_path.exists():
            continue
        payload = json.loads(prov_path.read_text("utf-8"))
        payload[ARCHIVE_KEY] = audit_meta
        write_atomic(prov_path, payload)

    return counts


def apply_main6_source_review(root: Path) -> dict[str, dict[str, int]]:
    return {school: review_main6_school(root, school) for school in MAIN6_SCHOOLS}
