"""Tests for Stage 2, Stage 3, and Stage 4 Shared Host Fact-Sheet Registry & Program Verification."""

from __future__ import annotations

import json
from pathlib import Path

from exchange_info.shared_host_registry import (
    DIRECT_HOST_REVIEW_ROUNDS,
    PINNED_PARTNER_BUNDLES,
    SHARED_FACTSHEET_PATH,
    STAGE234_MANIFEST_PATH,
    make_host_key,
)


def test_shared_host_factsheets_cover_all_2775_unique_hosts() -> None:
    payload = json.loads(SHARED_FACTSHEET_PATH.read_text(encoding="utf-8"))
    assert payload["total_unique_hosts"] == 2775
    assert payload["total_partner_rows_covered"] == 4956
    assert payload["total_open_or_active_rows_audited"] == 1456
    hosts = payload["hosts"]
    assert len(hosts) == 2775

    tiers = payload["verification_tier_counts"]
    assert tiers["direct_host_source_verified"] >= 20
    assert tiers["cross_bundle_host_audit_synced"] >= 950
    assert (
        tiers["direct_host_source_verified"]
        + tiers["cross_bundle_host_audit_synced"]
        + tiers["home_catalog_and_destination_verified"]
        == 2775
    )

    required_dims = {
        "host_language_requirements",
        "host_academic_requirements",
        "host_course_and_credit_rules",
        "host_application_deadlines",
        "host_living_and_housing_costs",
        "host_calendar_visa_insurance",
    }
    for h_key, entry in hosts.items():
        assert entry["host_key"] == h_key
        assert entry["canonical_website"] and entry["canonical_website"].startswith(
            ("http://", "https://")
        )
        assert set(entry["dimensions"].keys()) == required_dims
        for dim_val in entry["dimensions"].values():
            assert dim_val["summary"]
            assert dim_val["status"] in {
                "direct_host_source_verified",
                "cross_bundle_host_audit_synced",
                "home_catalog_reference",
            }


def test_stage2_and_stage3_synced_to_mutable_partner_bundles() -> None:
    manifest = json.loads(STAGE234_MANIFEST_PATH.read_text(encoding="utf-8"))
    s2 = manifest["stage2_shared_host_registry"]
    s3 = manifest["stage3_open_program_12gate_verification"]
    assert s2["total_unique_hosts"] == 2775
    assert s2["total_partner_rows_covered"] == 4956
    assert s3["total_open_or_active_rows_audited"] == 1456
    assert s3["open_status_rows"] == 1359
    assert s3["ncku_published_current_year_rows"] == 97
    assert len(s3["gates_evaluated"]) == 12

    data_root = Path("src/exchange_info/official_data")
    for uni_dir in sorted(data_root.iterdir()):
        if not uni_dir.is_dir():
            continue
        pf = uni_dir / "partners.jsonl"
        if not pf.exists():
            continue
        if uni_dir.name in PINNED_PARTNER_BUNDLES:
            continue
        for line in pf.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            row = json.loads(line)
            ref = row.get("reference_data") or {}
            assert "stage2_shared_host_factsheet" in ref, (
                f"{uni_dir.name} row {row.get('school_name')} missing stage2_shared_host_factsheet"
            )
            is_open_or_active = row.get("availability_status") == "open" or (
                uni_dir.name == "ncku" and row.get("quota_status") == "published"
            )
            if is_open_or_active:
                audit_raw = ref.get("stage3_open_program_audit")
                assert audit_raw is not None, (
                    f"{uni_dir.name} open row {row.get('school_name')} missing stage3_open_program_audit"
                )
                audit = json.loads(audit_raw)
                assert len(audit["gates"]) == 12


def test_stage4_experience_audit_has_zero_unverified_synthetic_full_text() -> None:
    manifest = json.loads(STAGE234_MANIFEST_PATH.read_text(encoding="utf-8"))
    s4 = manifest["stage4_longtail_and_experience_verification"]
    assert s4["total_experience_entries"] == 2354
    assert s4["universities_with_experiences"] == 23
    assert s4["unverified_full_text_remaining"] == 0
    assert s4["content_status_counts"] == {"metadata_only": 2354}
    assert s4["perspective_counts"]["official_student_story"] == 2


def test_direct_host_review_identities_present_in_registry() -> None:
    payload = json.loads(SHARED_FACTSHEET_PATH.read_text(encoding="utf-8"))
    hosts = payload["hosts"]
    for canonical_k, meta in DIRECT_HOST_REVIEW_ROUNDS.items():
        if canonical_k == "美國::university of california santa cruz":
            # UCSC is a 116 UST summer research partner recorded in Stage 1, not a partners.jsonl row
            continue
        matched = [
            entry
            for entry in hosts.values()
            if entry["verification_tier"] == "direct_host_source_verified"
            and any(u in entry["dimensions"]["host_language_requirements"]["source_urls"] for u in meta["source_urls"])
        ]
        assert matched, f"Direct host review identity {canonical_k} not matched in registry"
