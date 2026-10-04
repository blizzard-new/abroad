-- 20260901100000_atomic_application_content_governance.sql
-- Enables atomic Supabase transactions for saving and publishing application workflow revisions,
-- explicitly saving provenance and attestation records (review_approvals) in the revision log,
-- and automatically tracking operations in application_workflow_audit_log.

create or replace function public.exchange_commit_application_workflow_revision(
    p_revision_id text,
    p_workflow_key text,
    p_version integer,
    p_base_version integer,
    p_status text,
    p_content_hash text,
    p_change_summary jsonb,
    p_workflow_payload jsonb,
    p_detected_by text,
    p_detected_at timestamptz,
    p_required_review_count smallint,
    p_review_approvals jsonb,
    p_edit_history jsonb,
    p_reviewed_by text,
    p_reviewed_at timestamptz,
    p_review_note text,
    p_publication_action text,
    p_rolled_back_from_revision_id text,
    p_restored_revision_id text,
    p_home_university text,
    p_partner_university text,
    p_program_type text,
    p_academic_year text,
    p_application_round text,
    p_updated_at timestamptz
) returns jsonb
language plpgsql
set search_path = ''
as $$
declare
    v_revision public.application_workflow_revisions%rowtype;
    v_workflow public.application_workflows%rowtype;
    v_audit public.application_workflow_audit_log%rowtype;
    v_action text;
begin
    -- 1. Ensure the parent workflow exists, updating mutable metadata.
    insert into public.application_workflows (
        workflow_key,
        home_university,
        partner_university,
        program_type,
        academic_year,
        application_round,
        updated_at
    ) values (
        p_workflow_key,
        p_home_university,
        p_partner_university,
        p_program_type,
        p_academic_year,
        p_application_round,
        p_updated_at
    )
    on conflict (workflow_key) do update set
        home_university = excluded.home_university,
        partner_university = excluded.partner_university,
        program_type = excluded.program_type,
        academic_year = excluded.academic_year,
        application_round = excluded.application_round,
        updated_at = excluded.updated_at
    returning * into v_workflow;

    -- 2. Upsert the revision itself, including review_approvals (provenance/attestation)
    insert into public.application_workflow_revisions (
        id,
        workflow_key,
        version,
        base_version,
        status,
        content_hash,
        change_summary,
        workflow_payload,
        detected_by,
        detected_at,
        required_review_count,
        review_approvals,
        edit_history,
        reviewed_by,
        reviewed_at,
        review_note,
        publication_action,
        rolled_back_from_revision_id,
        restored_revision_id
    ) values (
        p_revision_id,
        p_workflow_key,
        p_version,
        p_base_version,
        p_status,
        p_content_hash,
        p_change_summary,
        p_workflow_payload,
        p_detected_by,
        p_detected_at,
        p_required_review_count,
        p_review_approvals,
        p_edit_history,
        p_reviewed_by,
        p_reviewed_at,
        p_review_note,
        p_publication_action,
        p_rolled_back_from_revision_id,
        p_restored_revision_id
    )
    on conflict (id) do update set
        status = excluded.status,
        change_summary = excluded.change_summary,
        workflow_payload = excluded.workflow_payload,
        required_review_count = excluded.required_review_count,
        review_approvals = excluded.review_approvals,
        edit_history = excluded.edit_history,
        reviewed_by = excluded.reviewed_by,
        reviewed_at = excluded.reviewed_at,
        review_note = excluded.review_note,
        publication_action = excluded.publication_action,
        rolled_back_from_revision_id = excluded.rolled_back_from_revision_id,
        restored_revision_id = excluded.restored_revision_id
    returning * into v_revision;

    -- 3. Determine the corresponding audit action
    if p_status = 'pending_review' then
        v_action := 'detected';
    elsif p_status = 'rejected' then
        v_action := 'rejected';
    elsif p_status = 'superseded' then
        v_action := 'superseded';
    elsif p_status = 'published' then
        if p_publication_action = 'rollback' then
            v_action := 'rolled_back';
        else
            v_action := 'published';
        end if;
    else
        v_action := 'detected';
    end if;

    -- 4. Append to the audit log
    insert into public.application_workflow_audit_log (
        workflow_key,
        revision_id,
        action,
        actor_id,
        note,
        metadata,
        created_at
    ) values (
        p_workflow_key,
        p_revision_id,
        v_action,
        p_reviewed_by,
        p_review_note,
        jsonb_build_object(
            'status', p_status,
            'version', p_version,
            'publication_action', p_publication_action,
            'review_approvals_count', jsonb_array_length(p_review_approvals)
        ),
        p_updated_at
    ) returning * into v_audit;

    return jsonb_build_object(
        'revision', to_jsonb(v_revision),
        'audit', to_jsonb(v_audit)
    );
end;
$$;


create or replace function public.exchange_commit_application_workflow_publication(
    p_workflow_key text,
    p_home_university text,
    p_partner_university text,
    p_program_type text,
    p_academic_year text,
    p_application_round text,
    p_published_version integer,
    p_published_payload jsonb,
    p_published_at timestamptz,
    p_current_revision_id text,
    p_updated_at timestamptz
) returns jsonb
language plpgsql
set search_path = ''
as $$
declare
    v_workflow public.application_workflows%rowtype;
begin
    insert into public.application_workflows (
        workflow_key,
        home_university,
        partner_university,
        program_type,
        academic_year,
        application_round,
        published_version,
        published_payload,
        published_at,
        current_revision_id,
        updated_at
    ) values (
        p_workflow_key,
        p_home_university,
        p_partner_university,
        p_program_type,
        p_academic_year,
        p_application_round,
        p_published_version,
        p_published_payload,
        p_published_at,
        p_current_revision_id,
        p_updated_at
    )
    on conflict (workflow_key) do update set
        home_university = excluded.home_university,
        partner_university = excluded.partner_university,
        program_type = excluded.program_type,
        academic_year = excluded.academic_year,
        application_round = excluded.application_round,
        published_version = excluded.published_version,
        published_payload = excluded.published_payload,
        published_at = excluded.published_at,
        current_revision_id = excluded.current_revision_id,
        updated_at = excluded.updated_at
    returning * into v_workflow;

    return to_jsonb(v_workflow);
end;
$$;

revoke all on function public.exchange_commit_application_workflow_revision(text, text, integer, integer, text, text, jsonb, jsonb, text, timestamptz, smallint, jsonb, jsonb, text, timestamptz, text, text, text, text, text, text, text, text, text, timestamptz) from public, anon, authenticated, service_role;
grant execute on function public.exchange_commit_application_workflow_revision(text, text, integer, integer, text, text, jsonb, jsonb, text, timestamptz, smallint, jsonb, jsonb, text, timestamptz, text, text, text, text, text, text, text, text, text, timestamptz) to service_role;

revoke all on function public.exchange_commit_application_workflow_publication(text, text, text, text, text, text, integer, jsonb, timestamptz, text, timestamptz) from public, anon, authenticated, service_role;
grant execute on function public.exchange_commit_application_workflow_publication(text, text, text, text, text, text, integer, jsonb, timestamptz, text, timestamptz) to service_role;
