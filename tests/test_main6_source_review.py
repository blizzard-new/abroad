"""Regression tests for Round 51 provenance and template review on main's 6 new schools."""
from __future__ import annotations

from collections import Counter
import json
from pathlib import Path
import shutil

import pytest

from exchange_info.cost_estimates import budget_fit, extract_monthly_estimates
from exchange_info.experience_collector import build_experience_digest
from exchange_info.experience_digests import source_kind
from exchange_info.generated_content_review import ROUND51_MANIFEST, load_manifest
from exchange_info.life_claim_review import unreviewed_profile_claim, withdrawn_life_claim
from exchange_info.life_context import LifeResearchSnapshot, _profile_evidence
from exchange_info.main6_source_review import (
    ARCHIVE_KEY,
    MAIN6_SCHOOLS,
    PARTNER_EVIDENCE_FIELDS,
    apply_main6_source_review,
    review_main6_school,
)
from exchange_info.models import (
    DestinationProfile,
    PartnerUniversity,
    StudentExperienceSource,
)

ROOT = Path(__file__).resolve().parents[1]


def test_round51_main6_bundles_have_field_evidence_and_no_generated_testimony() -> None:
    manifest = load_manifest(ROOT, round_id=51)
    assert set(manifest["schools"]) == set(MAIN6_SCHOOLS)

    total_partners = 0
    total_stories = 0
    total_life = 0
    total_destinations = 0
    story_roles: Counter[str] = Counter()

    for school in MAIN6_SCHOOLS:
        folder = ROOT / "src/exchange_info/official_data" / school

        for meta_name in ("catalog-completeness.json", "verification_status.json"):
            meta = json.loads((folder / meta_name).read_text("utf-8"))
            assert meta["whole_partner_records_verified"] == 0
            assert meta["round51_audit"]["whole_partner_records_verified"] == 0
            if "counts" in meta:
                assert meta["counts"]["whole_partner_records_verified"] == 0

        for line in (folder / "partners.jsonl").read_text("utf-8").splitlines():
            raw = json.loads(line)
            partner = PartnerUniversity.model_validate(raw)
            assert ARCHIVE_KEY in partner.reference_data
            assert isinstance(partner.reference_data[ARCHIVE_KEY], str)
            expected_status = (
                "verified_current"
                if partner.availability_status == "open"
                else "reference_only"
            )
            for field in PARTNER_EVIDENCE_FIELDS:
                ev = partner.field_evidence[field]
                assert ev.status == expected_status
                assert ev.source_url == partner.source_url
                assert ev.note
            total_partners += 1

        for line in (folder / "destination_profiles.jsonl").read_text("utf-8").splitlines():
            raw = json.loads(line)
            profile = DestinationProfile.model_validate(raw)
            assert profile.coverage_status == "official_partial"
            assert profile.cost_evidence is not None
            assert profile.cost_evidence.status == "reference_only"
            estimates = extract_monthly_estimates(profile)
            assert estimates
            fit = budget_fit(estimates, 80000)
            assert fit["status"] == "unknown"
            assert "尚未逐校核對接待校當期官方費用頁" in fit["reason"]
            for field in (
                "housing_summary",
                "cost_summary",
                "transport_summary",
                "campus_life_summary",
            ):
                val = getattr(profile, field)
                assert val and unreviewed_profile_claim(profile, field, val)
            assert not _profile_evidence(profile)
            total_destinations += 1

        for line in (folder / "student_experiences.jsonl").read_text("utf-8").splitlines():
            raw = json.loads(line)
            source = StudentExperienceSource.model_validate(raw)
            assert source.content_status == "metadata_only"
            assert not source.themes and not source.theme_summaries and not source.theme_summaries_zh
            assert raw["reference_data"]["generated_claims_before_review"]
            story_roles[source.perspective] += 1
            digest_res = build_experience_digest(source.school_name, source.country, [source])
            assert not digest_res.highlights and not digest_res.common_strengths
            if source.perspective == "official_program_record":
                assert digest_res.total_sources == 0
            elif source.perspective == "official_directory":
                assert source_kind(source) == "source_index"
            total_stories += 1

        for line in (folder / "student_life.jsonl").read_text("utf-8").splitlines():
            raw = json.loads(line)
            snap = LifeResearchSnapshot.model_validate(raw)
            assert snap.status == "partial" and not snap.evidence
            old = raw["reference_data"]["generated_life_before_review"]
            assert len(old["evidence"]) == 5
            assert all(
                withdrawn_life_claim(raw["school_name"], raw.get("country"), item)
                for item in old["evidence"]
            )
            total_life += 1

    assert total_partners == 938
    assert total_destinations == 938
    assert total_life == 938
    assert total_stories == 190
    assert story_roles == {"official_directory": 143, "official_program_record": 47}


@pytest.mark.parametrize("school", ["ncue", "kmu"])
def test_round51_replay_is_idempotent_and_preserves_independent_edits(
    tmp_path: Path, school: str
) -> None:
    manifest_dst = tmp_path / ROUND51_MANIFEST
    manifest_dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(ROOT / ROUND51_MANIFEST, manifest_dst)

    src_folder = ROOT / "src/exchange_info/official_data" / school
    dst_folder = tmp_path / "src/exchange_info/official_data" / school
    shutil.copytree(src_folder, dst_folder)

    # First replay on already-reviewed bundle must be a no-op.
    assert not any(review_main6_school(tmp_path, school).values())

    # Restore baseline state on the first partner and first destination row,
    # while making an independent edit on the second partner row.
    partners = [
        json.loads(line)
        for line in (dst_folder / "partners.jsonl").read_text("utf-8").splitlines()
        if line.strip()
    ]
    partners[0].pop("field_evidence", None)
    partners[0]["reference_data"].pop(ARCHIVE_KEY, None)

    partners[1].pop("field_evidence", None)
    partners[1]["quota"] = "獨立更新後的新名額文字"
    edited_partner = json.loads(json.dumps(partners[1]))
    (dst_folder / "partners.jsonl").write_text(
        "\n".join(json.dumps(r, ensure_ascii=False) for r in partners) + "\n",
        encoding="utf-8",
    )

    counts = review_main6_school(tmp_path, school)
    assert counts["partners_changed"] == 1
    reloaded = [
        json.loads(line)
        for line in (dst_folder / "partners.jsonl").read_text("utf-8").splitlines()
        if line.strip()
    ]
    assert reloaded[0].get("field_evidence")
    assert reloaded[1] == edited_partner
