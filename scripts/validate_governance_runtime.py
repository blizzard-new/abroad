"""Actual command transactions in the harness's two isolated PostgREST services.

All identities and content are synthetic. This module never obtains a project
URL or secret from the application's environment.
"""
from datetime import datetime, timezone
from urllib.parse import urlsplit
import json

import requests

from exchange_info import governance_commands as commands
from exchange_info.content_governance import (
    SupabaseContentGovernanceStore, stage_workflow_refresh, approve_workflow_revision,
    publish_workflow_revision, workflow_review_source_urls, workflow_review_rule_keys,
    update_pending_workflow_applicability, build_application_workflow_publication_history,
    rollback_published_workflow, workflow_content_hash,
)
from exchange_info.destination_profile_review import (
    SupabaseDestinationProfileReviewStore, REQUIRED_DESTINATION_PROFILE_REVIEW_SECTIONS,
    record_destination_profile_review, build_destination_profile_review_queue,
    promote_destination_profile, build_destination_profile_publication_history,
    rollback_destination_profile, apply_destination_profile_promotions,
)
from exchange_info.models import (
    UniversityApplicationWorkflow, ApplicationStep, ApplicationWorkflowSource,
    ApplicationWorkflowApplicabilityUpdateRequest, ApplicationWorkflowRollbackRequest,
    ApplicationWorkflowSourceApplicabilityUpdate,
    ApplicationWorkflowReviewStatus,
    DestinationProfile, SourceReference, DestinationProfileReviewSubmitRequest,
    DestinationProfilePromotionRequest, DestinationProfileRollbackRequest,
)


def require(condition, message):
    if not condition:
        raise RuntimeError("Atomic governance runtime: " + message)


def workflow(title):
    return UniversityApplicationWorkflow(home_university="Synthetic governance home",
        school_name="Synthetic governance host", academic_year="117", application_round="Synthetic round",
        applicability_status="verified", coverage_status="official_verified",
        steps=[ApplicationStep(rule_id="synthetic-rule", order=1, phase="Synthetic phase", title=title,
            responsible_party="Synthetic student", summary="Synthetic bounded requirement",
            source_urls=["https://synthetic.edu/exchange"], support_status="verified")],
        sources=[ApplicationWorkflowSource(title="Synthetic official notice",
            source_url="https://synthetic.edu/exchange", role="home_university",
            authority="home_official_notice", effective_academic_year="117",
            application_round="Synthetic round", checked_at=datetime(2026,10,9,tzinfo=timezone.utc))],
        last_checked=datetime(2026,10,9,tzinfo=timezone.utc))


def approve(store, revision, actor):
    return approve_workflow_revision(store, revision.id, reviewer_id=actor,
        expected_content_hash=revision.content_hash, note="Synthetic complete independent attestation",
        reviewed_source_urls=workflow_review_source_urls(revision.workflow),
        reviewed_rule_keys=workflow_review_rule_keys(revision.workflow))


def validate_atomic_governance(context, *, psql):
    checks = []
    calls = []
    def transport(base):
        def request(method, url, **kwargs):
            parsed = urlsplit(url)
            require(parsed.hostname == "runtime-supabase.invalid" and parsed.path.startswith("/rest/v1/"), "unexpected gateway URL")
            entry = {"method": method, "path": parsed.path, "instance": base}
            calls.append(entry)
            is_rpc = method == "POST" and "/rpc/" in parsed.path
            before = json.loads(snapshot()) if is_rpc else None
            if is_rpc:
                entry["envelope"] = kwargs["json"]
            response = requests.request(method, base + parsed.path.removeprefix("/rest/v1"), **kwargs)
            if is_rpc:
                after = json.loads(snapshot())
                entry.update(http_status=response.status_code, response=response.json(), snapshot_unchanged=before==after,
                    full_delta={key:{"before":[row for row in before[key] or [] if row not in (after[key] or [])],
                        "after":[row for row in after[key] or [] if row not in (before[key] or [])]}
                        for key in before if before[key]!=after[key]})
            return response
        return request
    first = SupabaseContentGovernanceStore("https://runtime-supabase.invalid", context.service_token,
        request_func=transport(context.postgrest_url))
    second = SupabaseContentGovernanceStore("https://runtime-supabase.invalid", context.service_token,
        request_func=transport(context.postgrest_secondary_url))
    def snapshot():
        return psql(context, """select jsonb_build_object(
            'workflows',(select jsonb_agg(to_jsonb(t) order by workflow_key) from public.application_workflows t),
            'revisions',(select jsonb_agg(to_jsonb(t) order by id) from public.application_workflow_revisions t),
            'audit',(select jsonb_agg(to_jsonb(t) order by id) from public.application_workflow_audit_log t),
            'reviews',(select jsonb_agg(to_jsonb(t) order by id) from public.destination_profile_review_events t),
            'promotions',(select jsonb_agg(to_jsonb(t) order by id) from public.destination_profile_promotion_events t),
            'rollbacks',(select jsonb_agg(to_jsonb(t) order by id) from public.destination_profile_rollback_events t));""")
    baseline = stage_workflow_refresh(first, workflow("Synthetic original")).revision
    require(not baseline.review_approvals and baseline.status.value == "pending_review" and not first.load_published_workflows(), "staging approved or published")
    before = snapshot()
    require(stage_workflow_refresh(second, workflow("Synthetic original")).revision.id == baseline.id, "staging replay changed revision")
    require(snapshot() == before, "staging replay changed audit or data")
    checks.append("stage_zero_approval_zero_publication_idempotent")

    a, b = commands.WorkflowCommandBuffer(first), commands.WorkflowCommandBuffer(second)
    approve(a, baseline, "synthetic-a")
    approve(b, baseline, "synthetic-b")
    a.commit("approve_workflow_revision", "synthetic-a")
    before = snapshot()
    try:
        b.commit("approve_workflow_revision", "synthetic-b")
    except ValueError:
        pass
    else:
        raise RuntimeError("Concurrent approval unexpectedly accepted stale snapshot")
    require(snapshot() == before, "CAS conflict changed persisted evidence")
    try:
        publish_workflow_revision(first, baseline.id, reviewer_id="synthetic-a")
    except ValueError:
        pass
    else:
        raise RuntimeError("Single reviewer publication unexpectedly succeeded")
    require(snapshot() == before, "single reviewer denial mutated data")
    # Bypass service validation deliberately, to verify the existing service-only
    # RPC independently rejects single-human and duplicate-human publications.
    db_buffer = commands.WorkflowCommandBuffer(first)
    one = next(row for row in db_buffer.list_revisions() if row.id == baseline.id)
    public = one.workflow.model_copy(update={"governance_key":one.workflow_key,
        "review_status":ApplicationWorkflowReviewStatus.PUBLISHED,"published_at":datetime.now(timezone.utc)})
    forced = one.model_copy(update={"status":ApplicationWorkflowReviewStatus.PUBLISHED,"workflow":public,
        "reviewed_by":"synthetic-a","reviewed_at":datetime.now(timezone.utc)})
    forged_second = one.review_approvals[0].model_copy(update={"reviewer_id":"synthetic-b"})
    for approvals in [one.review_approvals, [one.review_approvals[0],one.review_approvals[0]],
                      [one.review_approvals[0],forged_second]]:
        try:
            first.commit_command(db_buffer.expected,[forced.model_copy(update={"review_approvals":approvals})],[public],
                operation="publish_workflow_revision",actor="synthetic-a")
        except ValueError:
            pass
        else:
            raise RuntimeError("SQL accepted publication without independent double review")
        require(snapshot() == before,"SQL denial committed revision, public payload or audit")
    checks.append("sql_independent_double_review_denies_single_duplicate_and_unpersisted_reviewer")
    wrong_actor = commands.WorkflowCommandBuffer(first)
    approve(wrong_actor, baseline, "synthetic-b")
    try:
        wrong_actor.commit("approve_workflow_revision","synthetic-a")
    except ValueError:
        pass
    else:
        raise RuntimeError("SQL accepted an approval appended for another actor")
    require(snapshot()==before,"wrong-actor approval denial committed evidence")
    checks.append("approval_is_one_independently_persisted_actor_bound_attestation")
    approve(second, baseline, "synthetic-b")
    publish_workflow_revision(first, baseline.id, reviewer_id="synthetic-a")
    checks.append("two_instances_cas_and_independent_double_review")

    candidate = stage_workflow_refresh(second, workflow("Synthetic changed")).revision
    approve(first, candidate, "synthetic-a")
    approve(second, candidate, "synthetic-b")
    request = ApplicationWorkflowApplicabilityUpdateRequest(expected_content_hash=candidate.content_hash,
        academic_year="118", application_round="Synthetic round",
        source_updates=[ApplicationWorkflowSourceApplicabilityUpdate(source_url="https://synthetic.edu/exchange",
            effective_academic_year="118", application_round="Synthetic round", title="Synthetic official notice",
            role="home_university", authority="home_official_notice")],
        note="Synthetic official source applicability changed")
    before = snapshot()
    try:
        update_pending_workflow_applicability(first, candidate.id, request.model_copy(update={"expected_content_hash":"0"*64}), edited_by="synthetic-a")
    except ValueError:
        pass
    else:
        raise RuntimeError("Stale source hash unexpectedly accepted")
    require(snapshot() == before, "hash conflict mutated data")
    edited = update_pending_workflow_applicability(first, candidate.id, request, edited_by="synthetic-a")
    require(not edited.review_approvals and len(edited.edit_history[-1].invalidated_review_approvals) == 2, "source edit discarded or retained active old attestations")
    require(next(row for row in second.list_revisions() if row.id == edited.id).content_hash == edited.content_hash, "SQL persisted stale hash")
    retained = json.loads(psql(context,"select jsonb_build_object('active',review_approvals,'history',edit_history) "
        "from public.application_workflow_revisions where id='"+edited.id+"';"))
    require(retained["active"]==[] and retained["history"][-1]["invalidated_review_approvals"]==
        [row.model_dump(mode="json") for row in edited.edit_history[-1].invalidated_review_approvals],
        "DB readback failed to retain complete invalidated approvals")
    approve(first, edited, "synthetic-a")
    approve(second, edited, "synthetic-b")
    checks.append("source_edit_hash_conflict_invalidates_retains_attestations")

    # A real database trigger raises after revision writes at public-payload
    # update. The entire RPC, including audit rows, must roll back.
    psql(context, """create function public.runtime_governance_fail_publication() returns trigger language plpgsql as $$
        begin if new.published_version is distinct from old.published_version then
            raise exception 'synthetic late workflow publication failure'; end if; return new; end $$;
        create trigger runtime_governance_fail_publication before update of published_payload on public.application_workflows
        for each row execute function public.runtime_governance_fail_publication();""")
    before = snapshot()
    try:
        publish_workflow_revision(first, edited.id, reviewer_id="synthetic-a")
    except requests.HTTPError as error:
        require("synthetic late workflow" in error.response.text, "unexpected publication failure")
    else:
        raise RuntimeError("Late failure trigger was not exercised")
    require(snapshot() == before, "late workflow failure committed partial rows or audit")
    psql(context, "drop trigger runtime_governance_fail_publication on public.application_workflows; drop function public.runtime_governance_fail_publication();")
    publish_workflow_revision(second, edited.id, reviewer_id="synthetic-a")
    after = snapshot()
    publish_workflow_revision(first, edited.id, reviewer_id="synthetic-a")
    require(snapshot() == after, "publication retry appended duplicate evidence")
    checks.append("workflow_late_failure_atomicity_retry_idempotency")

    item = build_application_workflow_publication_history(second).items[0]
    rollback = ApplicationWorkflowRollbackRequest(workflow_key=item.workflow_key,
        expected_current_revision_id=item.current_revision_id, expected_current_version=item.current_version,
        expected_current_content_hash=item.current_content_hash, restore_revision_id=baseline.id,
        note="Synthetic audited restoration of the first reviewed version")
    restored = rollback_published_workflow(first, rollback, rolled_back_by="synthetic-a")
    after = snapshot()
    require(rollback_published_workflow(second, rollback, rolled_back_by="synthetic-a").id == restored.id and snapshot() == after, "rollback retry was not idempotent")
    require(workflow_content_hash(second.load_published_workflows()[0]) == baseline.content_hash, "rollback public content differs from history")
    checks.append("workflow_history_rollback_consistency")

    dest_a = SupabaseDestinationProfileReviewStore("https://runtime-supabase.invalid", context.service_token, request_func=transport(context.postgrest_url))
    dest_b = SupabaseDestinationProfileReviewStore("https://runtime-supabase.invalid", context.service_token, request_func=transport(context.postgrest_secondary_url))
    profile = DestinationProfile(home_university="Synthetic governance home", school_name="Synthetic governance host",
        coverage_status="official_partial", coverage_note="Synthetic scope boundaries remain unchanged",
        cost_summary="Synthetic bounded cost", sources=[SourceReference(title="Synthetic official source", source_url="https://synthetic.edu/exchange")],
        last_checked=datetime(2026,10,9,tzinfo=timezone.utc))
    def queue(store):
        return build_destination_profile_review_queue([profile], home_university=profile.home_university,
            review_events=store.list_events(), promotion_events=store.list_promotion_events(), rollback_events=store.list_rollback_events())
    def attest(store, actor):
        current = queue(store)
        request = DestinationProfileReviewSubmitRequest(home_university=profile.home_university, school_name=profile.school_name,
            expected_snapshot=current.snapshot_fingerprint, expected_profile_content_hash=current.items[0].profile_content_hash,
            decision="approve", note="Synthetic full independent destination attestation",
            reviewed_source_urls=[row.source_url for row in profile.sources], reviewed_section_keys=[row.key for row in REQUIRED_DESTINATION_PROFILE_REVIEW_SECTIONS])
        return record_destination_profile_review(store, [profile], request, reviewer_id=actor, reviewer_display_name=actor)
    da, db = commands.DestinationCommandBuffer(dest_a), commands.DestinationCommandBuffer(dest_b)
    attest(da, "synthetic-a")
    attest(db, "synthetic-b")
    dest_a.commit_command(da.expected, da.added, profiles=[profile], operation="record_destination_profile_review", actor="synthetic-a")
    before = snapshot()
    try:
        dest_b.commit_command(db.expected, db.added, profiles=[profile], operation="record_destination_profile_review", actor="synthetic-b")
    except ValueError:
        pass
    else:
        raise RuntimeError("Destination stale snapshot unexpectedly accepted")
    require(snapshot() == before, "destination CAS conflict mutated evidence")
    attest(dest_b, "synthetic-b")
    current = queue(dest_a)
    promotion = DestinationProfilePromotionRequest(home_university=profile.home_university, school_name=profile.school_name,
        expected_snapshot=current.snapshot_fingerprint, expected_profile_content_hash=current.items[0].profile_content_hash,
        note="Synthetic explicit promotion following complete independent reviews")
    psql(context, """create function public.runtime_governance_fail_audit() returns trigger language plpgsql as $$
        begin if new.metadata->>'operation'='promote_destination_profile' then raise exception 'synthetic late destination audit failure'; end if; return new; end $$;
        create trigger runtime_governance_fail_audit before insert on public.application_workflow_audit_log
        for each row execute function public.runtime_governance_fail_audit();""")
    before = snapshot()
    try:
        promote_destination_profile(dest_a,[profile],promotion,promoted_by_id="synthetic-a",promoted_by_display_name="Synthetic A")
    except requests.HTTPError as error:
        require("synthetic late destination" in error.response.text, "unexpected destination failure")
    else:
        raise RuntimeError("Destination late audit failure was not exercised")
    require(snapshot() == before, "late destination failure committed event or audit")
    psql(context, "drop trigger runtime_governance_fail_audit on public.application_workflow_audit_log; drop function public.runtime_governance_fail_audit();")
    promoted = promote_destination_profile(dest_b,[profile],promotion,promoted_by_id="synthetic-a",promoted_by_display_name="Synthetic A")
    after = snapshot()
    require(promote_destination_profile(dest_a,[profile],promotion,promoted_by_id="synthetic-a",promoted_by_display_name="Synthetic A").id == promoted.id and snapshot() == after, "destination promotion replay changed data")
    item = build_destination_profile_publication_history([profile], dest_a.list_promotion_events(), dest_a.list_rollback_events()).items[0]
    rollback = DestinationProfileRollbackRequest(home_university=profile.home_university, school_name=profile.school_name,
        expected_active_promotion_event_id=item.active_promotion_event_id, expected_latest_publication_event_id=item.latest_event_id,
        expected_public_profile_content_hash=item.current_public_profile_content_hash, note="Synthetic audited restoration of the previous profile")
    restored = rollback_destination_profile(dest_a,[profile],rollback,rolled_back_by_id="synthetic-a",rolled_back_by_display_name="Synthetic A")
    after = snapshot()
    require(rollback_destination_profile(dest_b,[profile],rollback,rolled_back_by_id="synthetic-a",rolled_back_by_display_name="Synthetic A").id == restored.id and snapshot() == after, "destination rollback replay changed data")
    require(apply_destination_profile_promotions([profile],dest_b.list_promotion_events(),dest_b.list_rollback_events())[0] == profile, "destination rollback public content differs")
    checks.append("destination_two_instances_cas_atomic_failure_replay_history_rollback")
    from validate_governance_followup import validate_followup
    followup = validate_followup(context,psql=psql,first=first,second=second,
        destination_store=dest_a,snapshot=snapshot,calls=calls,transport=transport)
    checks.extend(followup["checks"])
    audit = json.loads(psql(context,"select jsonb_agg(metadata order by id) from public.application_workflow_audit_log where metadata ? 'operation';"))
    require(len(audit) >= 15 and all(row.get("actor") and row.get("expected") for row in audit), "full command audit missing")
    require({row["instance"] for row in calls} == {context.postgrest_url,context.postgrest_secondary_url}, "second instance not exercised")
    checks.append("append_only_full_command_audit")
    return {"passed_checks": checks, "check_count": len(checks), "actual_rpc_post_count": sum(row["method"]=="POST" for row in calls),
        "actual_command_audit_count": len(audit), "independent_postgrest_instances": 2, "production_access": False,
        "rpc_evidence":[row for row in calls if row["method"]=="POST"],
        "invalidated_approvals_DB_readback":retained,"followup":followup,
        "fixtures": "synthetic identities and content only; existing RPC signatures and service permissions"}
