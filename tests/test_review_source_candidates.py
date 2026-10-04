import json
from pathlib import Path
from urllib.parse import urlsplit

import pytest

from exchange_info.content_governance import (
    LocalContentGovernanceStore,
    list_workflow_review_backlog,
    workflow_review_source_urls,
)
from exchange_info.models import (
    ApplicationWorkflowRevision,
    ApplicationWorkflowSourceReplacementCandidateDefinition,
    UniversityApplicationWorkflow,
)
from exchange_info.review_source_candidates import (
    enrich_source_replacement_candidate_counts,
    list_source_replacement_candidate_review_rows,
    list_source_replacement_candidates,
    load_source_replacement_candidate_definitions,
)
from exchange_info.workflow_identity import workflow_storage_key


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
REVIEW_BATCH_DIR = REPOSITORY_ROOT / "docs" / "review-batches"
OFFICIAL_WORKFLOW_PATHS = (
    REPOSITORY_ROOT
    / "src"
    / "exchange_info"
    / "official_data"
    / "cgu"
    / "application_workflows.jsonl",
    REPOSITORY_ROOT
    / "src"
    / "exchange_info"
    / "official_data"
    / "ntpu"
    / "application_workflows.jsonl",
)


def _official_workflows() -> list[UniversityApplicationWorkflow]:
    workflows: list[UniversityApplicationWorkflow] = []
    for path in OFFICIAL_WORKFLOW_PATHS:
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                workflows.append(
                    UniversityApplicationWorkflow.model_validate_json(line)
                )
    return workflows


def _load_manifest(name: str) -> dict:
    return json.loads((REVIEW_BATCH_DIR / name).read_text(encoding="utf-8"))


def test_data_010_manifest_covers_every_current_insecure_review_source_once() -> None:
    manifest = _load_manifest("data-010-batch-001-source-candidates.json")
    # The batch was prepared against the 115 workflows (workflow IDs are per year).
    actual = {
        (workflow.workflow_id, source_url)
        for workflow in _official_workflows()
        if workflow.academic_year != "116"
        for source_url in workflow_review_source_urls(workflow)
        if urlsplit(source_url).scheme.casefold() == "http"
    }
    documented = {
        (item["workflow_id"], item["current_url"]) for item in manifest["items"]
    }
    # The 116 workflows were cloned from the 115 ones: they carry exactly the same
    # insecure partner URLs, so the batch's replacement candidates apply to them too
    # and no new insecure source has entered the catalogue.
    cloned = {
        (workflow.school_name, source_url)
        for workflow in _official_workflows()
        if workflow.academic_year == "116"
        for source_url in workflow_review_source_urls(workflow)
        if urlsplit(source_url).scheme.casefold() == "http"
    }
    assert cloned == {
        (item["school_name"], item["current_url"]) for item in manifest["items"]
    }

    assert len(documented) == len(manifest["items"])
    assert documented == actual
    assert len({workflow_id for workflow_id, _ in documented}) == 9
    assert len(documented) == 12
    assert manifest["expected_workflow_count"] == 9
    assert manifest["expected_insecure_source_count"] == 12
    assert manifest["expected_verified_https_candidate_count"] == 10
    assert manifest["expected_transport_blocked_candidate_count"] == 2


def test_data_010_candidates_remain_non_publishing_human_review_evidence() -> None:
    manifest = _load_manifest("data-010-batch-001-source-candidates.json")

    assert manifest["review_status"] == "human_review_required"
    assert manifest["publication_effect"] == "none"
    assert manifest["approvals_created"] is False
    assert manifest["public_student_data_changed"] is False
    for item in manifest["items"]:
        assert item["candidate_status"] in {
            "strong_candidate",
            "conditional_candidate",
        }
        assert urlsplit(item["current_url"]).scheme == "http"
        assert urlsplit(item["candidate_url"]).scheme == "https"
        assert item["candidate_url"] != item["current_url"]
        assert item["automated_evidence"]
        assert item["required_human_checks"]
    research_leads = [
        lead
        for item in manifest["items"]
        for lead in item.get("research_leads", [])
    ]
    assert len(research_leads) == 6
    assert {lead["url"] for lead in research_leads} == {
        "https://int.unn.ru/studentu-inostrannogo-vuza/",
        "https://int.unn.ru/obrazovanie/student_exchange/",
        "https://int.unn.ru/kontakty/",
        "https://international.ruc.edu.cn/application",
        "https://international.ruc.edu.cn/template/GaranteeLetter.pdf",
        "https://international.rmbs.ruc.edu.cn/incoming/web/admissions_application.php",
    }
    assert all(lead["transport_status"] == "verified_https" for lead in research_leads)
    assert all(lead["eligible_as_replacement"] is False for lead in research_leads)
    assert all(urlsplit(lead["url"]).scheme == "https" for lead in research_leads)
    assert all(lead["reason_not_equivalent"] for lead in research_leads)
    assert sum(
        item["transport_status"] == "verified_https"
        for item in manifest["items"]
    ) == 10
    assert sum(
        item["transport_status"] == "downgrades_to_http"
        for item in manifest["items"]
    ) == 2
    blocked_workflows = {
        "workflow-e7823f7764c62954887ae1db",
        "workflow-36508fa323666a9b5f5f8305",
    }
    for item in manifest["items"]:
        expected_checked_at = (
            "2026-08-30"
            if item["workflow_id"] in blocked_workflows
            else "2026-08-29"
        )
        assert item["transport_checked_at"] == expected_checked_at
        assert item["transport_http_status"] == 200
        expected_scheme = (
            "http"
            if item["transport_status"] == "downgrades_to_http"
            else "https"
        )
        assert urlsplit(item["transport_final_url"]).scheme == expected_scheme


def test_data_010_candidate_identity_and_evidence_match_official_workflows() -> None:
    manifest = _load_manifest("data-010-batch-001-source-candidates.json")
    workflows = {item.workflow_id: item for item in _official_workflows()}

    for item in manifest["items"]:
        workflow = workflows[item["workflow_id"]]
        assert item["home_university"] == workflow.home_university
        assert item["school_name"] == workflow.school_name
        evidence = " ".join(
            [*item["automated_evidence"], *item["required_human_checks"]]
        )
        other_home_university = (
            "長庚大學"
            if workflow.home_university == "國立臺北大學"
            else "國立臺北大學"
        )
        assert other_home_university not in evidence


def test_data_003_current_year_pdf_is_only_a_candidate_not_public_data() -> None:
    manifest = _load_manifest("data-003-batch-001-source-candidates.json")
    candidate = manifest["replacement_candidates"][0]
    workflow = next(
        item
        for item in _official_workflows()
        if item.workflow_id == manifest["workflow_id"]
    )
    public_sources = set(workflow_review_source_urls(workflow))

    assert manifest["review_status"] == "human_review_required"
    assert manifest["publication_effect"] == "none"
    assert manifest["approvals_created"] is False
    assert manifest["public_student_data_changed"] is False
    assert candidate["candidate_status"] == "strong_candidate"
    assert candidate["current_url"] in public_sources
    assert candidate["candidate_url"] not in public_sources
    assert candidate["current_source_scope"] == "2022–2023 Academic Year"
    assert candidate["candidate_source_scope"] == "2026–2027 Academic Year"
    assert candidate["pdf_page_count"] == 8
    assert len(candidate["retrieved_sha256"]) == 64
    assert candidate["required_human_checks"]


def test_packaged_candidates_match_documented_replacements_and_remain_nonpublishing() -> None:
    data_003 = _load_manifest("data-003-batch-001-source-candidates.json")
    data_010 = _load_manifest("data-010-batch-001-source-candidates.json")
    documented_identities = {
        (
            data_003["workflow_id"],
            item["current_url"],
            item["candidate_url"],
            item["candidate_status"],
        )
        for item in data_003["replacement_candidates"]
    } | {
        (
            item["workflow_id"],
            item["current_url"],
            item["candidate_url"],
            item["candidate_status"],
        )
        for item in data_010["items"]
    }
    packaged = load_source_replacement_candidate_definitions()

    assert len(packaged) == 13
    assert {
        (
            item.workflow_id,
            item.current_url,
            item.candidate_url,
            item.candidate_status,
        )
        for item in packaged
    } == documented_identities
    assert all(item.review_status == "human_review_required" for item in packaged)
    assert all(item.publication_effect == "none" for item in packaged)
    assert all(item.approvals_created is False for item in packaged)
    assert all(item.public_student_data_changed is False for item in packaged)
    packaged_data_010 = {
        (item.workflow_id, item.current_url): item
        for item in packaged
        if item.batch_id == "DATA-010-BATCH-001"
    }
    for documented_item in data_010["items"]:
        packaged_item = packaged_data_010[
            (documented_item["workflow_id"], documented_item["current_url"])
        ]
        for field in (
            "candidate_url",
            "candidate_status",
            "transport_status",
            "transport_checked_at",
            "transport_final_url",
            "transport_http_status",
            "automated_evidence",
            "required_human_checks",
            "supporting_urls",
            "research_leads",
        ):
            documented_value = (
                documented_item.get(field, [])
                if field == "research_leads"
                else documented_item[field]
            )
            assert packaged_item.model_dump(mode="json")[field] == documented_value
    assert sum(item.can_prefill for item in packaged) == 11
    assert sum(not item.can_prefill for item in packaged) == 2


def test_candidate_transport_metadata_fails_closed_when_inconsistent() -> None:
    base = {
        "batch_id": "DATA-010-BATCH-001",
        "checked_at": "2026-08-13",
        "workflow_id": "workflow-123abc",
        "current_url": "http://example.edu/source",
        "candidate_url": "https://example.edu/source",
        "candidate_status": "strong_candidate",
        "transport_checked_at": "2026-08-29",
        "transport_http_status": 200,
        "automated_evidence": ["研究證據"],
        "required_human_checks": ["人工檢查"],
    }

    verified = ApplicationWorkflowSourceReplacementCandidateDefinition(
        **base,
        transport_status="verified_https",
        transport_final_url="https://example.edu/source",
    )
    assert verified.can_prefill is True
    downgraded = ApplicationWorkflowSourceReplacementCandidateDefinition(
        **base,
        transport_status="downgrades_to_http",
        transport_final_url="http://example.edu/source",
        can_prefill=True,
    )
    assert downgraded.can_prefill is False
    with pytest.raises(ValueError, match="最終網址必須仍為 HTTPS"):
        ApplicationWorkflowSourceReplacementCandidateDefinition(
            **base,
            transport_status="verified_https",
            transport_final_url="http://example.edu/source",
        )
    with pytest.raises(ValueError, match="2xx"):
        ApplicationWorkflowSourceReplacementCandidateDefinition(
            **{**base, "transport_http_status": 503},
            transport_status="verified_https",
            transport_final_url="https://example.edu/source",
        )
    research_lead = {
        "label": "官方申請入口",
        "url": "https://international.example.edu/application",
        "relationship": "application_system",
        "transport_status": "verified_https",
        "transport_checked_at": "2026-08-29",
        "transport_final_url": "https://international.example.edu/application",
        "transport_http_status": 200,
        "eligible_as_replacement": False,
        "reason_not_equivalent": "只提供一般申請系統，沒有合作交換的提名與文件規定。",
    }
    with_lead = ApplicationWorkflowSourceReplacementCandidateDefinition(
        **base,
        transport_status="verified_https",
        transport_final_url="https://example.edu/source",
        research_leads=[research_lead],
    )
    assert with_lead.research_leads[0].eligible_as_replacement is False
    with pytest.raises(ValueError):
        ApplicationWorkflowSourceReplacementCandidateDefinition(
            **base,
            transport_status="verified_https",
            transport_final_url="https://example.edu/source",
            research_leads=[
                {**research_lead, "eligible_as_replacement": True}
            ],
        )
    with pytest.raises(ValueError, match="最終網址必須維持 HTTPS"):
        ApplicationWorkflowSourceReplacementCandidateDefinition(
            **base,
            transport_status="verified_https",
            transport_final_url="https://example.edu/source",
            research_leads=[
                {
                    **research_lead,
                    "transport_final_url": "http://international.example.edu/application",
                }
            ],
        )


def test_candidates_are_returned_only_for_exact_pending_revision_sources() -> None:
    workflow = next(
        item
        for item in _official_workflows()
        if item.workflow_id == "workflow-36508fa323666a9b5f5f8305"
    )
    revision = ApplicationWorkflowRevision(
        workflow_key="candidate-workflow-key",
        version=workflow.version + 1,
        base_version=workflow.version,
        content_hash="0" * 64,
        workflow=workflow,
    )

    candidates = list_source_replacement_candidates([revision])

    assert len(candidates) == 1
    assert candidates[0].revision_id == revision.id
    assert candidates[0].workflow_key == revision.workflow_key
    assert candidates[0].current_url in workflow_review_source_urls(workflow)

    published_revision = revision.model_copy(update={"status": "published"})
    assert list_source_replacement_candidates([published_revision]) == []

    source_removed = workflow.model_copy(update={"sources": [], "steps": []})
    stale_revision = revision.model_copy(update={"workflow": source_removed})
    assert list_source_replacement_candidates([stale_revision]) == []

    candidate_already_present = workflow.model_copy(
        update={
            "sources": [
                *workflow.sources,
                workflow.sources[0].model_copy(
                    update={"source_url": candidates[0].candidate_url}
                ),
            ]
        }
    )
    already_replaced_revision = revision.model_copy(
        update={"workflow": candidate_already_present}
    )
    assert len(list_source_replacement_candidates([already_replaced_revision])) == 1


def test_candidate_coverage_identifies_exact_current_review_queue(
    tmp_path,
) -> None:
    store = LocalContentGovernanceStore(
        tmp_path,
        include_bundled_baseline=True,
    )
    published = store.load_published_workflows()
    backlog = list_workflow_review_backlog(store)

    enriched = enrich_source_replacement_candidate_counts(
        backlog,
        published,
        [],
    )

    candidate_items = [
        item
        for item in enriched.items
        if item.source_replacement_candidate_count > 0
    ]
    assert enriched.workflows_with_source_replacement_candidates == 7
    assert enriched.source_replacement_candidate_count == 8
    assert enriched.transport_blocked_source_replacement_candidate_count == 2
    assert len(candidate_items) == 7
    assert sum(
        item.source_replacement_candidate_count for item in candidate_items
    ) == 8
    assert sum(
        item.strong_source_replacement_candidate_count for item in candidate_items
    ) == 5
    assert sum(
        item.conditional_source_replacement_candidate_count
        for item in candidate_items
    ) == 3
    assert sum(
        item.transport_blocked_source_replacement_candidate_count
        for item in candidate_items
    ) == 2

    target = next(
        workflow
        for workflow in published
        if workflow.workflow_id == "workflow-36508fa323666a9b5f5f8305"
    )
    source_removed = target.model_copy(update={"sources": [], "steps": []})
    pending = ApplicationWorkflowRevision(
        workflow_key=workflow_storage_key(target),
        version=target.version + 1,
        base_version=target.version,
        content_hash="1" * 64,
        workflow=source_removed,
    )
    after_pending_replacement = enrich_source_replacement_candidate_counts(
        backlog,
        published,
        [pending],
    )
    target_item = next(
        item
        for item in after_pending_replacement.items
        if item.workflow_key == pending.workflow_key
    )
    assert target_item.source_replacement_candidate_count == 0
    assert (
        after_pending_replacement.workflows_with_source_replacement_candidates
        == 6
    )
    assert after_pending_replacement.source_replacement_candidate_count == 7
    assert (
        after_pending_replacement.transport_blocked_source_replacement_candidate_count
        == 1
    )


def test_source_replacement_review_queue_covers_staged_and_unstaged_workflows(
    tmp_path,
) -> None:
    store = LocalContentGovernanceStore(
        tmp_path,
        include_bundled_baseline=True,
    )
    published = store.load_published_workflows()
    fingerprint = "a" * 64

    rows = list_source_replacement_candidate_review_rows(
        published,
        [],
        review_content_fingerprint=fingerprint,
    )

    assert len(rows) == 13
    assert len({row.workflow_key for row in rows}) == 10
    assert sum(row.candidate_status == "strong_candidate" for row in rows) == 8
    assert sum(row.candidate_status == "conditional_candidate" for row in rows) == 5
    assert sum(row.can_prefill for row in rows) == 11
    assert sum(not row.can_prefill for row in rows) == 2
    assert all(row.review_content_fingerprint == fingerprint for row in rows)
    assert all(row.has_pending_revision is False for row in rows)
    assert all(row.pending_revision_id is None for row in rows)
    assert all(row.workbench_path.startswith("/admin/content-review?workflow_key=") for row in rows)
    assert all(f"review_snapshot={fingerprint}" in row.workbench_path for row in rows)
    assert all(row.review_status == "human_review_required" for row in rows)
    assert all(row.publication_effect == "none" for row in rows)
    assert all(row.approvals_created is False for row in rows)
    assert all(row.public_student_data_changed is False for row in rows)

    target = next(
        workflow
        for workflow in published
        if workflow.workflow_id == "workflow-36508fa323666a9b5f5f8305"
    )
    source_removed = target.model_copy(update={"sources": [], "steps": []})
    pending = ApplicationWorkflowRevision(
        workflow_key=workflow_storage_key(target),
        version=target.version + 1,
        base_version=target.version,
        content_hash="1" * 64,
        workflow=source_removed,
    )
    after_pending_replacement = list_source_replacement_candidate_review_rows(
        published,
        [pending],
        review_content_fingerprint=fingerprint,
    )

    assert len(after_pending_replacement) == 12
    assert len({row.workflow_key for row in after_pending_replacement}) == 9
    assert not any(row.workflow_key == pending.workflow_key for row in after_pending_replacement)
