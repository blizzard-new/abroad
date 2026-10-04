from __future__ import annotations

import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from exchange_info.models import (
    ApplicationWorkflowSourceMetadataResearchCandidate,
)
from exchange_info.review_source_metadata_candidates import (
    SOURCE_METADATA_RESEARCH_CANDIDATES_PATH,
    load_source_metadata_research_candidates,
    source_metadata_research_candidate_for_url,
)
from exchange_info.source_url_policy import canonical_source_url_identity


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DOCUMENTATION_MANIFEST_PATH = (
    PROJECT_ROOT
    / "docs"
    / "review-batches"
    / "data-003-batch-002-source-metadata-candidates.json"
)


def test_packaged_source_metadata_research_manifest_is_fail_closed() -> None:
    packaged = json.loads(
        SOURCE_METADATA_RESEARCH_CANDIDATES_PATH.read_text(encoding="utf-8")
    )
    documented = json.loads(
        DOCUMENTATION_MANIFEST_PATH.read_text(encoding="utf-8")
    )

    assert documented == packaged
    assert packaged["schema_version"] == 1
    assert packaged["expected_candidate_count"] == 6
    assert packaged["expected_verified_exact_source_count"] == 5
    assert packaged["expected_source_unavailable_count"] == 1
    assert packaged["review_status"] == "human_review_required"
    assert packaged["publication_effect"] == "none"
    assert packaged["approvals_created"] is False
    assert packaged["public_student_data_changed"] is False

    candidates = load_source_metadata_research_candidates()
    assert len(candidates) == 6
    assert len({candidate.source_url.casefold() for candidate in candidates}) == 6
    assert all(candidate.can_prefill is False for candidate in candidates)
    assert all(candidate.automated_evidence for candidate in candidates)
    assert all(candidate.required_human_checks for candidate in candidates)
    assert all(candidate.reason_not_ready for candidate in candidates)
    assert all(candidate.source_url.startswith("https://") for candidate in candidates)
    assert all(
        candidate.transport_final_url.startswith("https://")
        for candidate in candidates
    )
    assert all(200 <= candidate.transport_http_status < 300 for candidate in candidates)


def test_source_metadata_research_candidates_keep_exact_and_unavailable_sources_separate() -> None:
    candidates = load_source_metadata_research_candidates()
    by_url = {candidate.source_url: candidate for candidate in candidates}

    english = by_url[
        "https://cms-carrier.ntpu.edu.tw/uploads/115_1003_f908ed3fae.pdf"
    ]
    assert english.research_status == "verified_exact_source"
    assert english.proposed_title == "115學年度交換學生申請資訊一覽表(英語組)"
    assert english.proposed_role.value == "home_university"
    assert english.proposed_authority.value == "home_official_notice"
    assert english.proposed_priority == 1
    assert english.proposed_effective_academic_year == "115"

    unavailable = by_url[
        "https://new.ntpu.edu.tw/oia/overseas-partner-schools"
    ]
    assert unavailable.research_status == "source_unavailable"
    assert unavailable.application_level_status == "not_found_page"
    assert unavailable.transport_http_status == 200
    assert unavailable.proposed_title is None
    assert unavailable.proposed_role is None
    assert unavailable.proposed_authority is None
    assert unavailable.proposed_priority is None
    assert unavailable.proposed_effective_academic_year is None
    assert len(unavailable.research_leads) == 1
    assert unavailable.research_leads[0].eligible_as_replacement is False
    assert unavailable.research_leads[0].url == (
        "https://new.ntpu.edu.tw/oia/sister-schools"
    )


def test_source_metadata_candidate_lookup_uses_exact_url_without_mutation() -> None:
    source_url = "https://www.cgu.edu.tw/oia-ch/Contents?nodeId=17533"
    candidate = source_metadata_research_candidate_for_url(source_url)

    assert candidate is not None
    assert candidate.source_url == source_url
    assert candidate.proposed_title == "長庚大學 可申請學校 (雙學位)"
    assert source_metadata_research_candidate_for_url(
        "HTTPS://WWW.CGU.EDU.TW/oia-ch/Contents?nodeId=17533"
    ) is not None
    assert source_metadata_research_candidate_for_url(
        "https://www.cgu.edu.tw/oia-ch/contents?nodeId=17533"
    ) is None
    assert source_metadata_research_candidate_for_url(
        "https://www.cgu.edu.tw/oia-ch/Contents?nodeid=17533"
    ) is None
    assert source_metadata_research_candidate_for_url("https://example.invalid") is None
    zero_padded_port = canonical_source_url_identity(
        "HTTPS://EXAMPLE.EDU:0443/A?Q=1"
    )
    assert zero_padded_port == "https://example.edu:0443/A?Q=1"
    assert zero_padded_port != canonical_source_url_identity(
        "https://example.edu:443/A?Q=1"
    )
    assert canonical_source_url_identity("HTTPS://EXAMPLE.EDU:/A") == (
        "https://example.edu:/A"
    )
    assert canonical_source_url_identity("HTTPS://EXAMPLE.EDU:/A") != (
        canonical_source_url_identity("https://example.edu/A")
    )
    assert canonical_source_url_identity("https://faß.de/A") != (
        canonical_source_url_identity("https://fass.de/A")
    )
    assert canonical_source_url_identity("HTTPS://EXAMPLE.EDU/A?") == (
        "https://example.edu/A?"
    )
    assert canonical_source_url_identity("HTTPS://EXAMPLE.EDU/A#") == (
        "https://example.edu/A#"
    )
    malformed_ipv6 = "HTTPS://2001:DB8::A/A"
    assert canonical_source_url_identity(malformed_ipv6) == malformed_ipv6
    assert canonical_source_url_identity(
        "HTTPS://User:Pass@EXAMPLE.EDU:0443/A?Q=1"
    ) == "https://User:Pass@example.edu:0443/A?Q=1"
    assert canonical_source_url_identity(
        "HTTPS://[2001:DB8::A]:0443/A?Q=1"
    ) == "https://[2001:db8::a]:0443/A?Q=1"
    assert canonical_source_url_identity(
        "HTTPS://[2001:DB8::A]:/A"
    ) == "https://[2001:db8::a]:/A"
    for control_character in ("\n", "\r", "\t", "\x00", "\x1f", "\x7f"):
        unsafe_url = f"https://EXAMPLE.edu/A{control_character}B"
        assert canonical_source_url_identity(unsafe_url) == unsafe_url
        assert canonical_source_url_identity(unsafe_url) != (
            canonical_source_url_identity("https://example.edu/AB")
        )


def test_source_metadata_candidate_model_rejects_unsafe_shortcuts() -> None:
    exact_payload = {
        "batch_id": "DATA-003-BATCH-002",
        "checked_at": "2026-08-30",
        "source_url": "https://official.example.edu/source",
        "research_status": "verified_exact_source",
        "application_level_status": "content_available",
        "transport_checked_at": "2026-08-30",
        "transport_final_url": "https://official.example.edu/source",
        "transport_http_status": 200,
        "proposed_title": "正式來源",
        "proposed_role": "home_university",
        "proposed_authority": "home_official_notice",
        "proposed_priority": 1,
        "can_prefill": False,
        "automated_evidence": ["已讀取原始頁面。"],
        "required_human_checks": ["逐流程確認內容適用性。"],
        "reason_not_ready": "仍須兩位真人逐流程確認後才能保存與發布。",
    }
    validated = ApplicationWorkflowSourceMetadataResearchCandidate.model_validate(
        exact_payload
    )
    assert validated.can_prefill is False

    with pytest.raises(ValidationError):
        ApplicationWorkflowSourceMetadataResearchCandidate.model_validate(
            {**exact_payload, "can_prefill": True}
        )
    with pytest.raises(ValidationError):
        ApplicationWorkflowSourceMetadataResearchCandidate.model_validate(
            {**exact_payload, "source_url": "http://official.example.edu/source"}
        )
    with pytest.raises(ValidationError):
        ApplicationWorkflowSourceMetadataResearchCandidate.model_validate(
            {**exact_payload, "proposed_title": None}
        )
    with pytest.raises(ValidationError):
        ApplicationWorkflowSourceMetadataResearchCandidate.model_validate(
            {
                **exact_payload,
                "research_status": "source_unavailable",
                "application_level_status": "not_found_page",
            }
        )
