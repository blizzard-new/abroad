"""Failure, replay and CAS behavior of real stores with synthetic content."""
from pathlib import Path
import json
import os
import subprocess
import sys

import pytest

from exchange_info import governance_commands as commands
from exchange_info.content_governance import (
    LocalContentGovernanceStore, SupabaseContentGovernanceStore,
    approve_workflow_revision, publish_workflow_revision, stage_workflow_refresh,
    workflow_content_hash, workflow_review_rule_keys, workflow_review_source_urls,
    update_pending_workflow_applicability, build_application_workflow_publication_history,
    rollback_published_workflow,
)
from exchange_info.models import ApplicationWorkflowApplicabilityUpdateRequest, ApplicationWorkflowRollbackRequest
from exchange_info.release_readiness import build_application_workflow_review_batch_rows, stage_application_workflow_review_batch
from exchange_info.storage import data_paths, load_application_workflows
from test_notifications import _content_workflow as _original_content_workflow


def _content_workflow(title):
    return _original_content_workflow(title, version=1)


def approve(store, revision, reviewer):
    return approve_workflow_revision(store, revision.id, reviewer_id=reviewer, note="Synthetic independently verified evidence",
        expected_content_hash=revision.content_hash, reviewed_source_urls=workflow_review_source_urls(revision.workflow),
        reviewed_rule_keys=workflow_review_rule_keys(revision.workflow))


def ready_store(path):
    store = LocalContentGovernanceStore(path)
    baseline = stage_workflow_refresh(store, _content_workflow("Synthetic original")).revision
    approve(store, baseline, "synthetic-a")
    approve(store, baseline, "synthetic-b")
    publish_workflow_revision(store, baseline.id, reviewer_id="synthetic-a")
    candidate = stage_workflow_refresh(store, _content_workflow("Synthetic changed")).revision
    approve(store, candidate, "synthetic-a")
    approve(store, candidate, "synthetic-b")
    return store, baseline, candidate


def persisted_bytes(store):
    paths = data_paths(store.data_dir)
    return {name: path.read_bytes() if path.exists() else None for name, path in {
        "revisions": paths["application_workflow_revisions"], "public": paths["application_workflows"],
        "audit": paths["application_workflows"].parent / "application_workflow_audit_log.jsonl"}.items()}


def audit_rows(store):
    path = Path(store.data_dir) / "processed/application_workflow_audit_log.jsonl"
    return [json.loads(row) for row in path.read_text().splitlines()] if path.exists() else []


def test_late_publication_failure_restores_every_byte_before_retry(tmp_path, monkeypatch):
    store, baseline, candidate = ready_store(tmp_path)
    before = persisted_bytes(store)
    original = commands._replace_bytes
    failed = False

    def fail_public_write(path, value):
        nonlocal failed
        if path.name == "application_workflows.jsonl" and not failed:
            failed = True
            raise OSError("synthetic failure after revision write")
        return original(path, value)

    monkeypatch.setattr(commands, "_replace_bytes", fail_public_write)
    with pytest.raises(OSError, match="after revision"):
        publish_workflow_revision(store, candidate.id, reviewer_id="synthetic-a")
    assert failed and persisted_bytes(store) == before
    assert store.load_published_workflows()[0].version == baseline.version
    assert not (tmp_path / "processed/.content-governance-command.json").exists()
    published = publish_workflow_revision(store, candidate.id, reviewer_id="synthetic-a")
    assert published.version == candidate.version
    assert len([row for row in store.list_revisions() if row.status.value == "published"]) == 1
    assert audit_rows(store)[-1]["operation"] == "publish_workflow_revision"


def test_process_crash_recovers_before_public_read_and_can_retry(tmp_path):
    store, baseline, candidate = ready_store(tmp_path)
    before = persisted_bytes(store)
    script = """import os,sys
from pathlib import Path
from exchange_info import governance_commands as c
from exchange_info.content_governance import LocalContentGovernanceStore,publish_workflow_revision
original=c._replace_bytes
def crash(path,data):
    original(path,data)
    if path.name=='application_workflow_revisions.jsonl': os._exit(79)
c._replace_bytes=crash
publish_workflow_revision(LocalContentGovernanceStore(Path(sys.argv[1])),sys.argv[2],reviewer_id='synthetic-a')
"""
    result = subprocess.run([sys.executable, "-c", script, str(tmp_path), candidate.id], capture_output=True,
        env={**os.environ, "PYTHONPATH": str(Path(__file__).resolve().parents[1] / "src")})
    assert result.returncode == 79, result.stderr.decode()
    assert (tmp_path / "processed/.content-governance-command.json").exists()
    # This ordinary public loader, rather than a special recovery command,
    # must never expose the interrupted publication.
    assert load_application_workflows(tmp_path)[0].version == baseline.version
    assert persisted_bytes(store) == before
    assert not (tmp_path / "processed/.content-governance-command.json").exists()
    assert publish_workflow_revision(store, candidate.id, reviewer_id="synthetic-a").version == candidate.version


def test_concurrent_approval_snapshot_conflicts_without_lost_evidence(tmp_path):
    store = LocalContentGovernanceStore(tmp_path)
    candidate = stage_workflow_refresh(store, _content_workflow("Synthetic pending")).revision
    first, second = commands.WorkflowCommandBuffer(store), commands.WorkflowCommandBuffer(store)
    approve(first, candidate, "synthetic-a")
    approve(second, candidate, "synthetic-b")
    first.commit("approve_workflow_revision", "synthetic-a")
    before = persisted_bytes(store)
    with pytest.raises(ValueError, match="快照"):
        second.commit("approve_workflow_revision", "synthetic-b")
    assert persisted_bytes(store) == before
    assert [row.reviewer_id for row in store.list_revisions()[0].review_approvals] == ["synthetic-a"]
    approve(store, candidate, "synthetic-b")
    assert {row.reviewer_id for row in store.list_revisions()[0].review_approvals} == {"synthetic-a", "synthetic-b"}


def test_batch_staging_has_zero_approval_publication_and_is_idempotent(tmp_path):
    store = LocalContentGovernanceStore(tmp_path)
    store.publish_workflow(_content_workflow("Synthetic reference"), "synthetic-baseline")
    public = [row.model_dump_json() for row in store.load_published_workflows()]
    row = build_application_workflow_review_batch_rows(store, batch_size=1)[0]
    first = stage_application_workflow_review_batch(store, row.batch_id, batch_size=1,
        expected_snapshot=row.review_content_fingerprint, detected_by="synthetic-a")
    before = persisted_bytes(store)
    second = stage_application_workflow_review_batch(store, row.batch_id, batch_size=1,
        expected_snapshot=row.review_content_fingerprint, detected_by="synthetic-a")
    assert first.created_count == 1 and second.existing_count == 1 and second.created_count == 0
    assert first.items[0].revision_id == second.items[0].revision_id
    assert first.approvals_created is False and first.workflows_published is False and first.public_student_data_changed is False
    assert all(not row.review_approvals for row in store.list_revisions())
    assert next(row for row in store.list_revisions() if row.id == first.items[0].revision_id).status.value == "pending_review"
    assert not any(row.status.value == "published" for row in store.list_revisions())
    assert [row.model_dump_json() for row in store.load_published_workflows()] == public
    assert persisted_bytes(store) == before
    with pytest.raises(RuntimeError, match="快照"):
        stage_application_workflow_review_batch(store, row.batch_id, batch_size=1, expected_snapshot="0" * 64, detected_by="synthetic-a")
    assert persisted_bytes(store) == before


def test_legacy_public_refresh_keeps_a_reference_baseline_without_publishing(tmp_path):
    store = LocalContentGovernanceStore(tmp_path)
    original = _content_workflow("Synthetic legacy public")
    store.publish_workflow(original, "synthetic-legacy")
    assert store.list_revisions() == []
    public_before = persisted_bytes(store)["public"]
    candidate = stage_workflow_refresh(store, _content_workflow("Synthetic legacy changed")).revision
    revisions = store.list_revisions()
    assert len(revisions) == 2
    assert {row.status.value for row in revisions} == {"superseded", "pending_review"}
    assert all(row.review_approvals == [] for row in revisions)
    assert next(row for row in revisions if row.status.value == "superseded").detected_by == "legacy_import"
    assert candidate.version == original.version + 1
    assert persisted_bytes(store)["public"] == public_before


@pytest.mark.parametrize("order_key", ["id", "workflow_key"])
def test_capped_snapshot_reads_all_rows_and_rejects_unverifiable_truncation(order_key):
    from types import SimpleNamespace
    from unittest.mock import Mock
    rows = [{order_key: str(index), "event_payload": {"index": index}} for index in range(3)]
    offsets = []
    def fetch(method, table, *, headers, params):
        assert headers["Prefer"] == "count=exact"
        offset = params["offset"];offsets.append(offset)
        page = rows[offset:offset + 2]
        return SimpleNamespace(headers={"Content-Range": f"{offset}-{offset + len(page) - 1}/3"}, json=lambda: page)
    store = SimpleNamespace(_request=fetch)
    assert commands.read_governance_snapshot_rows(store, "synthetic", select="*", order_key=order_key) == rows
    assert offsets == [0, 2]
    store._request = Mock(return_value=SimpleNamespace(headers={"Content-Range": "0-1/*"}, json=lambda: rows[:2]))
    with pytest.raises(RuntimeError, match="完整筆數"):
        commands.read_governance_snapshot_rows(store, "synthetic", select="*", order_key=order_key)
    assert store._request.call_count == 1


def test_source_edit_clears_approvals_and_retains_complete_old_attestations(tmp_path):
    store, _, candidate = ready_store(tmp_path)
    before = persisted_bytes(store)
    request = ApplicationWorkflowApplicabilityUpdateRequest(expected_content_hash=candidate.content_hash,
        academic_year="117", note="Synthetic yearly evidence edit; never an automatic publication")
    with pytest.raises(ValueError, match="修改"):
        update_pending_workflow_applicability(store, candidate.id, request.model_copy(update={"expected_content_hash": "0" * 64}), edited_by="synthetic-a")
    assert persisted_bytes(store) == before
    updated = update_pending_workflow_applicability(store, candidate.id, request, edited_by="synthetic-a")
    assert updated.review_approvals == [] and updated.status.value == "pending_review"
    assert {row.reviewer_id for row in updated.edit_history[-1].invalidated_review_approvals} == {"synthetic-a", "synthetic-b"}
    assert updated.content_hash != candidate.content_hash
    assert persisted_bytes(store)["public"] == before["public"]
    event = audit_rows(store)[-1]
    assert len(event["revisions_before"][0]["review_approvals"]) == 2 and event["revisions_after"][0]["review_approvals"] == []


def test_duplicate_original_url_roles_are_preserved_in_nonreplacement_edit(tmp_path):
    store = LocalContentGovernanceStore(tmp_path)
    workflow = _content_workflow("Synthetic shared URL roles")
    source = workflow.sources[0]
    workflow.sources = [source, source.model_copy(update={"title": "Synthetic other official role"})]
    candidate = stage_workflow_refresh(store, workflow).revision
    request = ApplicationWorkflowApplicabilityUpdateRequest(expected_content_hash=candidate.content_hash,
        academic_year="117", note="Synthetic same-URL applicability edit; do not merge evidence roles")
    updated = update_pending_workflow_applicability(store, candidate.id, request, edited_by="synthetic-a")
    assert len(updated.workflow.sources) == 2
    assert {row.title for row in updated.workflow.sources} == {row.title for row in workflow.sources}
    assert all(row.source_url == source.source_url for row in updated.workflow.sources)


def test_safe_rollback_restores_content_with_new_version_and_replays_without_new_audit(tmp_path):
    store, baseline, candidate = ready_store(tmp_path)
    publish_workflow_revision(store, candidate.id, reviewer_id="synthetic-a")
    history = build_application_workflow_publication_history(store)
    item = history.items[0]
    request = ApplicationWorkflowRollbackRequest(workflow_key=item.workflow_key, expected_current_revision_id=item.current_revision_id,
        expected_current_version=item.current_version, expected_current_content_hash=item.current_content_hash,
        restore_revision_id=baseline.id, note="Synthetic emergency restoration of independently reviewed baseline")
    before = persisted_bytes(store)
    with pytest.raises(ValueError):
        rollback_published_workflow(store, request.model_copy(update={"expected_current_content_hash": "0" * 64}), rolled_back_by="synthetic-a")
    assert persisted_bytes(store) == before
    restored = rollback_published_workflow(store, request, rolled_back_by="synthetic-a")
    after = persisted_bytes(store)
    replay = rollback_published_workflow(store, request, rolled_back_by="synthetic-a")
    assert replay.id == restored.id and persisted_bytes(store) == after
    assert restored.version == candidate.version + 1
    assert workflow_content_hash(store.load_published_workflows()[0]) == baseline.content_hash
    assert len([row for row in store.list_revisions() if row.status.value == "published"]) == 1
    assert {row.reviewer_id for row in restored.review_approvals} == {"synthetic-a", "synthetic-b"}
    assert audit_rows(store)[-1]["operation"] == "rollback_published_workflow"


def test_older_supabase_schema_is_read_only_before_any_command_envelope():
    calls = []
    class Response:
        def raise_for_status(self): pass
        def json(self): return []
    def request(method, url, **kwargs):
        calls.append((method, url))
        return Response()
    store = SupabaseContentGovernanceStore("https://synthetic.invalid", "synthetic-key", request_func=request)
    with pytest.raises(RuntimeError, match="migration"):
        stage_workflow_refresh(store, _content_workflow("Synthetic capability test"))
    assert len(calls) == 1 and calls[0][0] == "GET" and calls[0][1].endswith("/application_workflow_audit_log")


def test_old_workflow_rollback_cannot_replace_a_later_publication(tmp_path):
    store, baseline, candidate = ready_store(tmp_path)
    publish_workflow_revision(store, candidate.id, reviewer_id="synthetic-a")
    item = build_application_workflow_publication_history(store).items[0]
    request = ApplicationWorkflowRollbackRequest(workflow_key=item.workflow_key,
        expected_current_revision_id=item.current_revision_id, expected_current_version=item.current_version,
        expected_current_content_hash=item.current_content_hash, restore_revision_id=baseline.id,
        note="Synthetic restore before later independently reviewed publication")
    rollback_published_workflow(store, request, rolled_back_by="synthetic-a")
    later = stage_workflow_refresh(store, _content_workflow("Synthetic later publication")).revision
    approve(store, later, "synthetic-a")
    approve(store, later, "synthetic-b")
    publish_workflow_revision(store, later.id, reviewer_id="synthetic-a")
    before = persisted_bytes(store)
    with pytest.raises(ValueError):
        rollback_published_workflow(store, request, rolled_back_by="synthetic-a")
    assert persisted_bytes(store) == before
    assert store.load_published_workflows()[0].steps[0].title == "Synthetic later publication"


def destination_fixture():
    from datetime import datetime, timezone
    from exchange_info.models import DestinationProfile, SourceReference
    return DestinationProfile(home_university="淡江大學", school_name="Synthetic governance host",
        coverage_status="official_partial", coverage_note="Synthetic facts remain scoped to one program",
        cost_summary="Synthetic cost; no claim about an actual destination",
        sources=[SourceReference(title="Synthetic official source", source_url="https://synthetic.edu/exchange")],
        last_checked=datetime(2026, 10, 9, tzinfo=timezone.utc))


def destination_review(store, profile, reviewer, *, decision="approve"):
    from exchange_info.destination_profile_review import (
        build_destination_profile_review_queue, record_destination_profile_review,
        REQUIRED_DESTINATION_PROFILE_REVIEW_SECTIONS,
    )
    from exchange_info.models import DestinationProfileReviewSubmitRequest
    queue = build_destination_profile_review_queue([profile], home_university=profile.home_university, review_events=store.list_events(),
        promotion_events=store.list_promotion_events(), rollback_events=store.list_rollback_events(),
        current_reviewer_id=reviewer)
    target = queue.items[0]
    request = DestinationProfileReviewSubmitRequest(home_university=profile.home_university, school_name=profile.school_name,
        expected_snapshot=queue.snapshot_fingerprint, expected_profile_content_hash=target.profile_content_hash,
        decision=decision, note="Synthetic independent review of every source and section",
        reviewed_source_urls=[row.source_url for row in profile.sources],
        reviewed_section_keys=[row.key for row in REQUIRED_DESTINATION_PROFILE_REVIEW_SECTIONS])
    return record_destination_profile_review(store, [profile], request, reviewer_id=reviewer, reviewer_display_name=reviewer)


def destination_promotion_request(store, profile):
    from exchange_info.destination_profile_review import build_destination_profile_review_queue
    from exchange_info.models import DestinationProfilePromotionRequest
    queue = build_destination_profile_review_queue([profile], home_university=profile.home_university, review_events=store.list_events(),
        promotion_events=store.list_promotion_events(), rollback_events=store.list_rollback_events())
    return DestinationProfilePromotionRequest(home_university=profile.home_university, school_name=profile.school_name,
        expected_snapshot=queue.snapshot_fingerprint, expected_profile_content_hash=queue.items[0].profile_content_hash,
        note="Synthetic explicit promotion following two independent reviews")


def destination_bytes(store):
    paths = [store.path, store.promotion_path, store.rollback_path,
        store.path.parent / "application_workflow_audit_log.jsonl"]
    return {path.name: path.read_bytes() if path.exists() else None for path in paths}


def test_destination_double_review_failure_atomicity_and_rollback_replay(tmp_path, monkeypatch):
    from exchange_info.destination_profile_review import (LocalDestinationProfileReviewStore,
        promote_destination_profile, rollback_destination_profile, apply_destination_profile_promotions,
        build_destination_profile_publication_history)
    from exchange_info.models import DestinationProfileRollbackRequest
    store = LocalDestinationProfileReviewStore(tmp_path)
    profile = destination_fixture()
    destination_review(store, profile, "synthetic-a")
    before = destination_bytes(store)
    with pytest.raises(ValueError, match="兩位"):
        promote_destination_profile(store, [profile], destination_promotion_request(store, profile),
            promoted_by_id="synthetic-a", promoted_by_display_name="Synthetic A")
    assert destination_bytes(store) == before
    # A second attestation by the same identity cannot count as a second human.
    destination_review(store, profile, "synthetic-a")
    assert destination_bytes(store) == before
    destination_review(store, profile, "synthetic-b")
    request = destination_promotion_request(store, profile)
    before = destination_bytes(store)
    original = commands._replace_bytes
    failed = False
    def fail_audit(path, value):
        nonlocal failed
        if path.name == "application_workflow_audit_log.jsonl" and not failed:
            failed = True
            raise OSError("synthetic late destination audit failure")
        return original(path, value)
    monkeypatch.setattr(commands, "_replace_bytes", fail_audit)
    with pytest.raises(OSError, match="late destination"):
        promote_destination_profile(store, [profile], request, promoted_by_id="synthetic-a", promoted_by_display_name="Synthetic A")
    assert failed and destination_bytes(store) == before
    assert apply_destination_profile_promotions([profile], store.list_promotion_events(), store.list_rollback_events())[0] == profile
    promotion = promote_destination_profile(store, [profile], request, promoted_by_id="synthetic-a", promoted_by_display_name="Synthetic A")
    published = destination_bytes(store)
    assert promote_destination_profile(store, [profile], request, promoted_by_id="synthetic-a", promoted_by_display_name="Synthetic A").id == promotion.id
    assert destination_bytes(store) == published
    item = build_destination_profile_publication_history([profile], store.list_promotion_events(), store.list_rollback_events()).items[0]
    rollback = DestinationProfileRollbackRequest(home_university=profile.home_university, school_name=profile.school_name,
        expected_active_promotion_event_id=item.active_promotion_event_id,
        expected_latest_publication_event_id=item.latest_event_id, expected_public_profile_content_hash=item.current_public_profile_content_hash,
        note="Synthetic audited restoration of the previous public profile")
    restored = rollback_destination_profile(store, [profile], rollback, rolled_back_by_id="synthetic-a", rolled_back_by_display_name="Synthetic A")
    after = destination_bytes(store)
    assert rollback_destination_profile(store, [profile], rollback, rolled_back_by_id="synthetic-a", rolled_back_by_display_name="Synthetic A").id == restored.id
    assert destination_bytes(store) == after
    assert apply_destination_profile_promotions([profile], store.list_promotion_events(), store.list_rollback_events())[0] == profile
    assert len(store.list_events()) == 2 and len(store.list_promotion_events()) == len(store.list_rollback_events()) == 1
    # Rollback invalidates prior approvals. New explicit reviews are required.
    with pytest.raises(ValueError, match="兩位"):
        promote_destination_profile(store, [profile], destination_promotion_request(store, profile),
            promoted_by_id="synthetic-a", promoted_by_display_name="Synthetic A")
    destination_review(store, profile, "synthetic-a")
    destination_review(store, profile, "synthetic-b")
    promote_destination_profile(store, [profile], destination_promotion_request(store, profile),
        promoted_by_id="synthetic-a", promoted_by_display_name="Synthetic A")
    later = destination_bytes(store)
    with pytest.raises(ValueError, match="後續公開版本"):
        rollback_destination_profile(store, [profile], rollback, rolled_back_by_id="synthetic-a", rolled_back_by_display_name="Synthetic A")
    assert destination_bytes(store) == later


def test_destination_concurrent_reviews_and_source_change_keep_old_evidence(tmp_path):
    from exchange_info.destination_profile_review import LocalDestinationProfileReviewStore, promote_destination_profile
    store = LocalDestinationProfileReviewStore(tmp_path)
    profile = destination_fixture()
    first, second = commands.DestinationCommandBuffer(store), commands.DestinationCommandBuffer(store)
    destination_review(first, profile, "synthetic-a")
    destination_review(second, profile, "synthetic-b")
    store.commit_command(first.expected, first.added, profiles=[profile], operation="record_destination_profile_review", actor="synthetic-a")
    before = destination_bytes(store)
    with pytest.raises(ValueError, match="其他命令"):
        store.commit_command(second.expected, second.added, profiles=[profile], operation="record_destination_profile_review", actor="synthetic-b")
    assert destination_bytes(store) == before
    destination_review(store, profile, "synthetic-b")
    old_request = destination_promotion_request(store, profile)
    changed = profile.model_copy(update={"cost_summary": "Synthetic revised cost"})
    before = destination_bytes(store)
    with pytest.raises(ValueError):
        promote_destination_profile(store, [changed], old_request, promoted_by_id="synthetic-a", promoted_by_display_name="Synthetic A")
    with pytest.raises(ValueError, match="兩位"):
        promote_destination_profile(store, [changed], destination_promotion_request(store, changed),
            promoted_by_id="synthetic-a", promoted_by_display_name="Synthetic A")
    assert destination_bytes(store) == before and len(store.list_events()) == 2
