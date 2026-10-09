from __future__ import annotations

import json

from fastapi.testclient import TestClient

from exchange_info import storage
from exchange_info.api import create_app
from exchange_info.models import (
    ApplicationApplicabilityStatus,
    ApplicationDeadlineStatus,
    PartnerResearchRecord,
    PartnerUniversity,
    UniversityApplicationWorkflow,
)


def test_bundled_ntpu_catalog_is_complete(monkeypatch, tmp_path) -> None:
    # A caller-supplied data directory stays isolated unless it is the configured
    # default directory. This mirrors a fresh Git clone that has no local refresh.
    assert storage.load_partner_research(tmp_path) == []
    assert storage.load_application_workflows(tmp_path) == []
    assert storage.load_destination_profiles(tmp_path) == []

    monkeypatch.setattr(storage, "DEFAULT_DATA_DIR", tmp_path)

    research = [row for row in storage.load_partner_research(tmp_path) if row.home_university == "國立臺北大學"]
    workflows = [
        row
        for row in storage.load_application_workflows(tmp_path)
        if row.home_university == "國立臺北大學"
    ]
    destinations = [
        row
        for row in storage.load_destination_profiles(tmp_path)
        if row.home_university == "國立臺北大學"
    ]

    assert len(research) == 206
    # Both rounds are bundled: 203 flows for 115 and 206 for 116, all unreviewed baselines.
    assert len(workflows) == 409
    assert sorted({row.academic_year for row in workflows}) == ["115", "116"]
    assert len(destinations) == 206
    assert all(
        step.deadline_status == ApplicationDeadlineStatus.REFERENCE_ONLY
        and not step.deadline_reminder_eligible
        for row in workflows
        for step in row.steps
    )
    assert all(
        source.effective_academic_year is None
        and source.application_round is None
        for row in workflows
        for source in row.sources
    )
    assert all(
        row.applicability_status
        == ApplicationApplicabilityStatus.NEEDS_CONFIRMATION
        for row in workflows
    )
    # 同濟大學 is new in 116; no official site could be identified for it yet, and it
    # stays listed as a gap instead of being filled in.
    unverified = [row.school_name for row in research if row.verification_status != "official_verified"]
    assert unverified == ["同濟大學"]
    assert all(row.official_website for row in research if row.school_name != "同濟大學")
    incomplete = [
        row.school_name
        for row in destinations
        if not (row.housing_summary and row.cost_summary and row.transport_summary and row.campus_life_summary)
    ]
    assert len(incomplete) <= 3
    assert all(row.home_university == "國立臺北大學" for row in destinations)


def test_runtime_includes_tracked_ntpu_public_baseline_with_isolated_private_data(
    monkeypatch,
    tmp_path,
) -> None:
    research = storage.read_jsonl(
        storage.BUNDLED_NTPU_DIR / "partner_research.jsonl",
        PartnerResearchRecord,
    )[0]
    partner = PartnerUniversity(
        program_type="交換學生（英語組）",
        country=research.country,
        school_name=research.school_name,
        source_url="https://new.ntpu.edu.tw/oia/sister-schools",
    )
    monkeypatch.setattr(
        "exchange_info.api.fetch_ntpu_partner_universities",
        lambda: [partner],
    )

    client = TestClient(create_app(tmp_path))
    coverage = client.get(
        "/coverage",
        params={"school": "國立臺北大學"},
    ).json()
    destination = client.get(
        "/destination-profile",
        params={
            "school": partner.school_name,
            "home_school": "國立臺北大學",
        },
    ).json()

    assert coverage["total_partner_schools"] == 1
    assert coverage["official_website_count"] == 1
    assert coverage["partners"][0]["official_website_url"] == research.official_website
    assert coverage["destination_profile_count"] == 1
    assert destination["home_university"] == "國立臺北大學"
    assert destination["coverage_status"] != "not_collected"
    assert coverage["partners"][0]["destination_status"] == destination["coverage_status"]
    assert coverage["partners"][0]["destination_last_checked"] == destination["last_checked"]
    assert coverage["partners"][0]["destination_last_checked"] is not None


def test_bundled_ntpu_completeness_report_has_all_required_fields() -> None:
    report_path = storage.BUNDLED_NTPU_DIR / "catalog-completeness.json"
    report = json.loads(report_path.read_text(encoding="utf-8"))

    assert report["academic_year"] == "116"
    assert report["partner_count"] == 206
    assert report["open_count"] == 169
    assert report["agreement_only_count"] == 37
    assert report["verified_image_count"] == 205
    assert report["workflow_count"] == 206
    assert report["destination_count"] == 204
    # Every field is complete except the gaps of the schools new in 116 (listed, not filled).
    assert min(report["fields"].values()) >= 204
    assert report["fields"]["structured_workflow"] == 206
    assert report["workflow_structure"] == {
        "workflow_count": 206,
        "structured_workflow_count": 206,
        "step_count": 1236,
        "structured_step_count": 1236,
        "known_submission_method_count": 207,
        "steps_needing_confirmation": 1236,
        "document_count": 3925,
        "documents_needing_confirmation": 3099,
        "source_count": 1056,
        "prioritized_source_count": 1056,
        "published_workflow_count": 0,
        "legacy_workflow_count": 206,
        "published_at_workflow_count": 0,
        "applicability_verified_workflow_count": 0,
        "verified_exact_deadline_count": 0,
        "reference_only_deadline_count": 1236,
        "deadlines_needing_confirmation_count": 0,
        "deadline_not_applicable_count": 0,
        "reminder_eligible_deadline_count": 0,
        "structure_issue_count": 0,
    }


def test_default_loader_structures_local_overrides_before_merging_bundle(
    monkeypatch,
    tmp_path,
) -> None:
    storage.ensure_data_dirs(tmp_path)
    bundled = storage.read_jsonl(
        storage.BUNDLED_NTPU_DIR / "application_workflows.jsonl",
        UniversityApplicationWorkflow,
    )
    local = bundled[0].model_copy(
        update={
            "academic_year": None,
            "workflow_id": None,
        }
    )
    storage.write_jsonl(
        storage.data_paths(tmp_path)["application_workflows"],
        [local],
    )
    monkeypatch.setattr(storage, "DEFAULT_DATA_DIR", tmp_path)

    workflows = [
        row
        for row in storage.load_application_workflows(tmp_path)
        if row.home_university == "國立臺北大學"
    ]

    assert len(workflows) == 409
    assert sum(row.school_name == local.school_name and row.academic_year == "115" for row in workflows) == 1
    loaded = next(
        row for row in workflows
        if row.school_name == local.school_name and row.academic_year == "115"
    )
    assert loaded.academic_year == "115"
