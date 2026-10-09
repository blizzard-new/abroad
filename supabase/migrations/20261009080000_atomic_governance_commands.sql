-- Existing RPC transaction boundary; no grants, ACL, RLS, ownership, or security mode changes.
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
    v_command jsonb;
    v_current_revisions jsonb;
    v_current_workflows jsonb;
    v_row jsonb;
    v_payload jsonb;
    v_hash_payload jsonb;
    v_key text;
    v_source jsonb;
    v_approvals jsonb;
    v_distinct integer;
    v_cutoff timestamptz;
    v_latest_reviews jsonb;
    v_prior_publication jsonb;
    v_prior_revision jsonb;
    v_previous_approval_count integer;
    v_command_hash text;
    v_public_revision jsonb;
    v_from_revision jsonb;
    v_restore_revision jsonb;
    v_provenance_revision jsonb;
    v_lineage_from jsonb;
    v_lineage_restore jsonb;
    v_public_current jsonb;
    v_lineage_depth integer;

begin

    -- The same service-only RPC now accepts an atomic unit of work. Its
    -- original signature, grants, invoker security and ownership are unchanged.
    perform pg_advisory_xact_lock(hashtextextended('exchange-content-governance-command', 0));
    if jsonb_typeof(p_change_summary) = 'object' and p_change_summary ? 'governance_command' then
        v_command := p_change_summary->'governance_command';
        v_command_hash := public.exchange_community_request_fingerprint(v_command);
        -- An exact previously committed envelope is a completed retry even
        -- though its original expected snapshot is now stale. The durable
        -- append-only audit is the receipt; never replay its mutations.
        if exists(select 1 from public.application_workflow_audit_log where
            metadata->>'governance_command_hash'=v_command_hash and
            metadata - 'governance_command_hash' = v_command) then
            return jsonb_build_object('committed',true,'operation',v_command->>'operation');
        end if;
        if coalesce(btrim(v_command->>'actor'), '') = '' or
           coalesce(v_command->>'operation','') not in (
             'stage_existing_workflow_for_review', 'stage_workflow_refresh',
             'stage_application_workflow_review_batch', 'update_pending_workflow_applicability',
             'approve_workflow_revision', 'publish_workflow_revision',
             'rollback_published_workflow', 'reject_workflow_revision',
             'record_destination_profile_review', 'promote_destination_profile', 'rollback_destination_profile') then
            raise exception using errcode='22023', message='Invalid governance command actor or operation';
        end if;
        if v_command->>'kind' = 'workflow' then
            if v_command->>'operation' not in ('stage_existing_workflow_for_review','stage_workflow_refresh',
                'stage_application_workflow_review_batch','update_pending_workflow_applicability',
                'approve_workflow_revision','publish_workflow_revision','rollback_published_workflow','reject_workflow_revision') then
                raise exception using errcode='22023', message='Invalid workflow command operation';
            end if;
            select coalesce(jsonb_agg(jsonb_build_object(
                'id', id,
                'workflow_key', workflow_key,
                'version', version,
                'base_version', base_version,
                'status', status,
                'content_hash', content_hash,
                'change_summary', change_summary,
                'workflow_payload', workflow_payload,
                'required_review_count', required_review_count,
                'review_approvals', review_approvals,
                'edit_history', edit_history,
                'reviewed_by', reviewed_by,
                'reviewed_at', reviewed_at,
                'review_note', review_note,
                'publication_action', publication_action,
                'rolled_back_from_revision_id', rolled_back_from_revision_id,
                'restored_revision_id', restored_revision_id,
                'detected_by', detected_by,
                'detected_at', detected_at) order by id), '[]'::jsonb)
                into v_current_revisions from public.application_workflow_revisions;
            select coalesce(jsonb_agg(jsonb_build_object(
                'workflow_key', workflow_key,
                'published_version', published_version,
                'published_payload', published_payload,
                'current_revision_id', current_revision_id,
                'home_university', home_university,
                'partner_university', partner_university,
                'program_type', program_type,
                'academic_year', academic_year,
                'application_round', application_round,
                'published_at', published_at) order by workflow_key), '[]'::jsonb)
                into v_current_workflows from public.application_workflows;
            if v_command->'expected'->'revisions' is distinct from v_current_revisions or
               v_command->'expected'->'workflows' is distinct from v_current_workflows then
                raise exception using errcode='PT409', message='Governance snapshot changed';
            end if;
            -- Missing keys produce SQL NULL: <> alone would skip rejection.
            -- Check types before invoking array functions on untrusted values.
            if jsonb_typeof(v_command->'revisions') is distinct from 'array' or
               jsonb_typeof(v_command->'published') is distinct from 'array' then
                raise exception using errcode='22023', message='Governance revisions and published payloads must be arrays';
            end if;
            if jsonb_array_length(v_command->'revisions') not between 1 and 100 or
               jsonb_array_length(v_command->'published') > 1 then
                raise exception using errcode='22023', message='Invalid bounded governance command';
            end if;
            if v_command->>'operation' in ('stage_existing_workflow_for_review','stage_workflow_refresh','stage_application_workflow_review_batch') and
               (jsonb_array_length(v_command->'published') <> 0 or exists (
                   select 1 from jsonb_array_elements(v_command->'revisions') r where
                       (r->>'status' <> 'pending_review' and not (r->>'status' = 'superseded' and r->>'detected_by' = 'legacy_import')) or jsonb_array_length(r->'review_approvals') <> 0)) then
                raise exception using errcode='22023', message='Staging cannot approve or publish';
            end if;
            if v_command->>'operation' in ('publish_workflow_revision','rollback_published_workflow') and
               jsonb_array_length(v_command->'published') <> 1 then
                raise exception using errcode='PT409', message='Publication must atomically include exactly one public payload';
            end if;
            if v_command->>'operation' not in ('publish_workflow_revision','rollback_published_workflow') and
               jsonb_array_length(v_command->'published')<>0 then
                raise exception using errcode='PT409', message='Only publication and rollback commands may change public payloads';
            end if;
            if (select count(distinct r->>'id') from jsonb_array_elements(v_command->'revisions') r)
               <> jsonb_array_length(v_command->'revisions') then
                raise exception using errcode='PT409', message='Revision identities must be unique within a command';
            end if;
            if v_command->>'operation' in ('publish_workflow_revision','rollback_published_workflow') then
                if (select count(*) from jsonb_array_elements(v_command->'revisions') r where r->>'status'='published')<>1 then
                    raise exception using errcode='PT409', message='Publication must identify exactly one published revision';
                end if;
                select value into v_public_revision from jsonb_array_elements(v_command->'revisions')
                    where value->>'status'='published';
                if v_public_revision->>'reviewed_by' is distinct from v_command->>'actor' or
                   v_public_revision->>'reviewed_at' is null or
                   v_public_revision->'workflow_payload'->>'review_status'<>'published' or
                   v_public_revision->'workflow_payload'->>'governance_key' is distinct from v_public_revision->>'workflow_key' or
                   v_public_revision->'workflow_payload'->>'version' is distinct from v_public_revision->>'version' or
                   v_public_revision->'workflow_payload'->>'published_at' is null then
                    raise exception using errcode='PT409', message='Publication metadata must bind the actor and revision';
                end if;
                if v_command->>'operation'='publish_workflow_revision' and (
                    v_public_revision->>'publication_action' is distinct from 'standard' or
                    v_public_revision->>'rolled_back_from_revision_id' is not null or
                    v_public_revision->>'restored_revision_id' is not null) then
                    raise exception using errcode='PT409', message='Standard publication cannot carry a rollback action or chain';
                end if;
                if v_command->>'operation'='rollback_published_workflow' then
                    if v_public_revision->>'publication_action' is distinct from 'rollback' or
                       v_public_revision->>'rolled_back_from_revision_id' is null or
                       v_public_revision->>'restored_revision_id' is null then
                        raise exception using errcode='PT409', message='Rollback requires an explicit restoration action and chain';
                    end if;
                    select value into v_from_revision from jsonb_array_elements(v_current_revisions)
                        where value->>'id'=v_public_revision->>'rolled_back_from_revision_id';
                    select value into v_restore_revision from jsonb_array_elements(v_current_revisions)
                        where value->>'id'=v_public_revision->>'restored_revision_id';
                    select value into v_public_current from jsonb_array_elements(v_current_workflows)
                        where value->>'workflow_key'=v_public_revision->>'workflow_key';
                    if v_from_revision is null or v_restore_revision is null or v_public_current is null or
                       exists(select 1 from jsonb_array_elements(v_current_revisions) r where r->>'id'=v_public_revision->>'id') or
                       v_from_revision->>'status'<>'published' or v_restore_revision->>'status'<>'superseded' or
                       v_from_revision->>'workflow_key' is distinct from v_public_revision->>'workflow_key' or
                       v_restore_revision->>'workflow_key' is distinct from v_public_revision->>'workflow_key' or
                       (v_restore_revision->>'version')::integer >= (v_from_revision->>'version')::integer or
                       v_public_current->>'current_revision_id' is distinct from v_from_revision->>'id' or
                       v_public_current->>'published_version' is distinct from v_from_revision->>'version' or
                       v_public_current->'published_payload' is distinct from v_from_revision->'workflow_payload' or
                       v_public_revision->>'base_version' is distinct from v_from_revision->>'version' or
                       v_public_revision->'workflow_payload'->>'supersedes_version' is distinct from v_from_revision->>'version' or
                       (v_public_revision->>'version')::integer <> (select max((r->>'version')::integer)+1 from
                           jsonb_array_elements(v_current_revisions) r where r->>'workflow_key'=v_public_revision->>'workflow_key') or
                       v_public_revision->>'detected_by' is distinct from v_command->>'actor' or
                       v_restore_revision->'workflow_payload'->>'review_status'<>'published' or
                       v_restore_revision->'workflow_payload'->>'published_at' is null or
                       v_public_revision->>'content_hash' is distinct from v_restore_revision->>'content_hash' or
                       v_public_revision->>'required_review_count' is distinct from v_restore_revision->>'required_review_count' or
                       v_public_revision->'review_approvals' is distinct from v_restore_revision->'review_approvals' or
                       jsonb_array_length(v_command->'revisions')<>2 or
                       not exists(select 1 from jsonb_array_elements(v_command->'revisions') r where
                           r->>'id'=v_from_revision->>'id' and r->>'status'='superseded') then
                        raise exception using errcode='PT409', message='Rollback must restore an audited older snapshot from the unique current publication';
                    end if;
                end if;
            elsif exists(select 1 from jsonb_array_elements(v_command->'revisions') r where r->>'status'='published') then
                raise exception using errcode='PT409', message='Published rows require a publication command and public payload';
            end if;
            for v_row in select value from jsonb_array_elements(v_command->'revisions') loop
                select value into v_prior_revision from jsonb_array_elements(v_current_revisions)
                    where value->>'id'=v_row->>'id';
                if v_command->>'operation' in ('publish_workflow_revision','rollback_published_workflow') and
                   v_row->>'id'<>v_public_revision->>'id' then
                    if v_prior_revision is null or v_prior_revision->>'status'<>'published' or
                       v_row->>'status'<>'superseded' or
                       v_row->>'workflow_key' is distinct from v_public_revision->>'workflow_key' or
                       (v_row-array['status','required_source_urls','required_rule_keys','detected_at','reviewed_at']) is distinct from
                           (v_prior_revision-array['status','detected_at','reviewed_at']) or
                       (v_row->>'detected_at')::timestamptz is distinct from (v_prior_revision->>'detected_at')::timestamptz or
                       (v_row->>'reviewed_at')::timestamptz is distinct from (v_prior_revision->>'reviewed_at')::timestamptz then
                        raise exception using errcode='PT409', message='Publication companions may only supersede the unchanged current revision';
                    end if;
                end if;
                if v_command->>'operation'='approve_workflow_revision' then
                    v_previous_approval_count := jsonb_array_length(v_prior_revision->'review_approvals');
                    if v_prior_revision is null or v_prior_revision->>'status'<>'pending_review' or
                       v_row->>'status'<>'pending_review' or
                       v_prior_revision->>'content_hash' is distinct from v_row->>'content_hash' or
                       v_prior_revision->>'required_review_count' is distinct from v_row->>'required_review_count' or
                       jsonb_array_length(v_command->'revisions')<>1 or jsonb_array_length(v_command->'published')<>0 or
                       jsonb_array_length(v_row->'review_approvals')<>v_previous_approval_count+1 or
                       (v_row->'review_approvals') - v_previous_approval_count is distinct from v_prior_revision->'review_approvals' or
                       v_row->'review_approvals'->v_previous_approval_count->>'reviewer_id' is distinct from v_command->>'actor' or
                       exists(select 1 from jsonb_array_elements(v_prior_revision->'review_approvals') a where
                           lower(btrim(a->>'reviewer_id'))=lower(btrim(v_command->>'actor'))) then
                        raise exception using errcode='PT409', message='Approval must independently append one actor-bound attestation to the stored revision';
                    end if;
                elsif v_row->>'status'='published' and v_row->>'publication_action'='standard' then
                    if v_prior_revision is null or v_row->'review_approvals' is distinct from v_prior_revision->'review_approvals' then
                        raise exception using errcode='PT409', message='Publication cannot introduce or change stored approvals';
                    end if;
                    if v_row->>'status'='published' and (
                        v_prior_revision->>'status'<>'pending_review' or
                        v_prior_revision->>'content_hash' is distinct from v_row->>'content_hash' or
                        v_prior_revision->>'required_review_count' is distinct from v_row->>'required_review_count' or
                        v_row->>'reviewed_by' is distinct from v_command->>'actor' or
                        not exists(select 1 from jsonb_array_elements(v_prior_revision->'review_approvals') a where a->>'reviewer_id'=v_command->>'actor') or
                        (v_row-array['status','workflow_payload','reviewed_by','reviewed_at','review_note','required_source_urls','required_rule_keys','detected_at']) is distinct from
                            (v_prior_revision-array['status','workflow_payload','reviewed_by','reviewed_at','review_note','detected_at']) or
                        (v_row->>'detected_at')::timestamptz is distinct from (v_prior_revision->>'detected_at')::timestamptz) then
                        raise exception using errcode='PT409', message='Publication requires independently persisted actor-bound approval provenance';
                    end if;
                elsif v_command->>'operation'='update_pending_workflow_applicability' then
                    if v_prior_revision is null or v_prior_revision->>'status'<>'pending_review' or
                       v_row->>'status'<>'pending_review' or v_row->'review_approvals'<>'[]'::jsonb or
                       jsonb_array_length(v_row->'edit_history')<>jsonb_array_length(v_prior_revision->'edit_history')+1 or
                       (v_row->'edit_history') - (jsonb_array_length(v_row->'edit_history')-1) is distinct from v_prior_revision->'edit_history' or
                       v_row->'edit_history'->-1->'invalidated_review_approvals' is distinct from v_prior_revision->'review_approvals' or
                       v_row->'edit_history'->-1->>'edited_by' is distinct from v_command->>'actor' then
                        raise exception using errcode='PT409', message='Source edits must retain the complete stored invalidated attestations';
                    end if;
                end if;
                if v_row->>'status'='published' then
                    -- The row's actual publication state determines provenance.
                    -- An operation label cannot exempt a published snapshot.
                    v_provenance_revision := case when v_row->>'publication_action'='rollback'
                        then v_restore_revision else v_prior_revision end;
                    v_lineage_depth := 0;
                    while v_provenance_revision->>'publication_action'='rollback' loop
                        v_lineage_depth := v_lineage_depth+1;
                        select value into v_lineage_from from jsonb_array_elements(v_current_revisions)
                            where value->>'id'=v_provenance_revision->>'rolled_back_from_revision_id';
                        select value into v_lineage_restore from jsonb_array_elements(v_current_revisions)
                            where value->>'id'=v_provenance_revision->>'restored_revision_id';
                        if v_lineage_depth>jsonb_array_length(v_current_revisions) or
                           v_lineage_from is null or v_lineage_restore is null or
                           v_lineage_from->>'workflow_key' is distinct from v_row->>'workflow_key' or
                           v_lineage_restore->>'workflow_key' is distinct from v_row->>'workflow_key' or
                           (v_lineage_restore->>'version')::integer >= (v_provenance_revision->>'version')::integer or
                           (v_lineage_from->>'version')::integer >= (v_provenance_revision->>'version')::integer or
                           v_provenance_revision->>'base_version' is distinct from v_lineage_from->>'version' or
                           v_provenance_revision->'workflow_payload'->>'supersedes_version' is distinct from v_lineage_from->>'version' or
                           v_provenance_revision->>'content_hash' is distinct from v_lineage_restore->>'content_hash' or
                           v_provenance_revision->>'required_review_count' is distinct from v_lineage_restore->>'required_review_count' or
                           v_provenance_revision->'review_approvals' is distinct from v_lineage_restore->'review_approvals' or
                           not exists(select 1 from public.application_workflow_audit_log e,
                               lateral jsonb_array_elements(e.metadata->'revisions') r where
                               e.metadata->>'operation'='rollback_published_workflow' and
                               e.actor_id=e.metadata->>'actor' and e.actor_id=r->>'reviewed_by' and
                               r->>'id'=v_provenance_revision->>'id' and r->>'status'='published' and
                               r->>'publication_action'='rollback' and
                               r->>'restored_revision_id'=v_lineage_restore->>'id' and
                               r->>'rolled_back_from_revision_id'=v_lineage_from->>'id' and
                               r->>'content_hash'=v_provenance_revision->>'content_hash' and
                               r->>'required_review_count'=v_provenance_revision->>'required_review_count' and
                               r->'review_approvals'=v_provenance_revision->'review_approvals' and
                               r->'workflow_payload'=v_provenance_revision->'workflow_payload' and
                               e.metadata->'published' @> jsonb_build_array(r->'workflow_payload')) then
                            raise exception using errcode='PT409', message='Historical rollback lineage must preserve its audited restoration snapshot';
                        end if;
                        v_provenance_revision := v_lineage_restore;
                    end loop;
                    if v_provenance_revision is null or
                       v_provenance_revision->>'workflow_key' is distinct from v_row->>'workflow_key' or
                       v_provenance_revision->'review_approvals' is distinct from v_row->'review_approvals' or
                       exists(select 1 from jsonb_array_elements(v_provenance_revision->'review_approvals') a where
                           not exists(select 1 from public.application_workflow_audit_log e,
                               lateral jsonb_array_elements(e.metadata->'revisions') r where
                               e.metadata->>'operation'='approve_workflow_revision' and
                               e.actor_id=a->>'reviewer_id' and e.metadata->>'actor'=a->>'reviewer_id' and
                               r->>'id'=v_provenance_revision->>'id' and r->>'content_hash'=v_provenance_revision->>'content_hash' and
                               r->'review_approvals' @> jsonb_build_array(a))) or
                       (v_row->>'publication_action'='rollback' and not exists(
                           select 1 from public.application_workflow_audit_log e,
                               lateral jsonb_array_elements(e.metadata->'revisions') r where
                           e.metadata->>'operation'='publish_workflow_revision' and
                           e.actor_id=e.metadata->>'actor' and e.actor_id=r->>'reviewed_by' and
                           r->>'id'=v_provenance_revision->>'id' and r->>'status'='published' and
                           r->>'publication_action'='standard' and
                           r->>'content_hash'=v_provenance_revision->>'content_hash' and
                           r->>'required_review_count'=v_provenance_revision->>'required_review_count' and
                           r->'review_approvals'=v_provenance_revision->'review_approvals' and
                           r->'workflow_payload'=v_provenance_revision->'workflow_payload' and
                           e.metadata->'published' @> jsonb_build_array(r->'workflow_payload'))) then
                        raise exception using errcode='PT409', message='Every published snapshot requires independently stored review and publication provenance';
                    end if;
                end if;
                v_hash_payload := (v_row->'workflow_payload') - array[
                    'workflow_id','governance_key','issue_report_snapshot','version','review_status',
                    'published_at','supersedes_version','applied_context','last_checked'];
                v_hash_payload := jsonb_set(v_hash_payload, '{steps}',
                    (select coalesce(jsonb_agg(value - 'checked_at' order by ord), '[]'::jsonb)
                     from jsonb_array_elements(v_hash_payload->'steps') with ordinality e(value,ord)));
                v_hash_payload := jsonb_set(v_hash_payload, '{sources}',
                    (select coalesce(jsonb_agg(value - 'checked_at' order by ord), '[]'::jsonb)
                     from jsonb_array_elements(v_hash_payload->'sources') with ordinality e(value,ord)));
                if public.exchange_community_request_fingerprint(v_hash_payload) <> v_row->>'content_hash' then
                    raise exception using errcode='PT409', message='Workflow content hash mismatch';
                end if;
                if (v_row->>'required_review_count')::integer < 2 then
                    raise exception using errcode='22023', message='Independent double review is required';
                end if;
                for v_source in select value from jsonb_array_elements(v_row->'review_approvals') loop
                    if v_source->>'reviewed_content_hash' is distinct from v_row->>'content_hash' or
                       coalesce(btrim(v_source->>'reviewer_id'),'') = '' or
                       (select coalesce(jsonb_agg(url order by url),'[]'::jsonb) from
                           (select distinct lower(btrim(value)) url from jsonb_array_elements_text(v_source->'reviewed_source_urls')) s)
                       is distinct from
                       (select coalesce(jsonb_agg(url order by url),'[]'::jsonb) from
                           (select distinct lower(btrim(value)) url from jsonb_array_elements_text(v_row->'required_source_urls')) s) or
                       (select coalesce(jsonb_agg(key order by key),'[]'::jsonb) from
                           (select distinct value key from jsonb_array_elements_text(v_source->'reviewed_rule_keys')) s)
                       is distinct from
                       (select coalesce(jsonb_agg(key order by key),'[]'::jsonb) from
                           (select distinct value key from jsonb_array_elements_text(v_row->'required_rule_keys')) s) then
                        raise exception using errcode='PT409', message='Approval evidence does not bind current hash, sources and rules';
                    end if;
                end loop;
                if v_row->>'status' = 'published' then
                    select count(distinct lower(btrim(value->>'reviewer_id'))) into v_distinct
                        from jsonb_array_elements(v_row->'review_approvals');
                    if v_distinct < (v_row->>'required_review_count')::integer or
                       jsonb_array_length(v_row->'required_source_urls') = 0 or
                       exists(select 1 from jsonb_array_elements_text(v_row->'required_source_urls') s where lower(value) not like 'https://%') then
                        raise exception using errcode='PT409', message='Publication requires independent complete double review';
                    end if;
                end if;
                v_payload := v_row->'workflow_payload';
                perform public.exchange_commit_application_workflow_revision(
                    v_row->>'id', v_row->>'workflow_key', (v_row->>'version')::integer,
                    (v_row->>'base_version')::integer, v_row->>'status', v_row->>'content_hash',
                    v_row->'change_summary', v_payload, v_row->>'detected_by',
                    (v_row->>'detected_at')::timestamptz, (v_row->>'required_review_count')::smallint,
                    v_row->'review_approvals', v_row->'edit_history', v_row->>'reviewed_by',
                    (v_row->>'reviewed_at')::timestamptz, v_row->>'review_note',
                    v_row->>'publication_action', v_row->>'rolled_back_from_revision_id', v_row->>'restored_revision_id',
                    v_payload->>'home_university', v_payload->>'school_name', v_payload->>'program_type',
                    v_payload->>'academic_year', v_payload->>'application_round', p_updated_at);
            end loop;
            for v_payload in select value from jsonb_array_elements(v_command->'published') loop
                select value into v_row from jsonb_array_elements(v_command->'revisions') where
                    value->>'workflow_key' = v_payload->>'governance_key' and value->>'status' = 'published';
                if v_row is null or v_row->'workflow_payload' is distinct from v_payload then
                    raise exception using errcode='PT409', message='Public payload does not match reviewed publication';
                end if;
                perform public.exchange_commit_application_workflow_publication(
                    v_row->>'workflow_key', v_payload->>'home_university', v_payload->>'school_name',
                    v_payload->>'program_type', v_payload->>'academic_year', v_payload->>'application_round',
                    (v_payload->>'version')::integer, v_payload, (v_payload->>'published_at')::timestamptz,
                    v_row->>'id', p_updated_at);
            end loop;
            if exists(select 1 from public.application_workflow_revisions where status='published'
                group by workflow_key having count(*) > 1) then
                raise exception using errcode='PT409', message='Multiple current workflow publications';
            end if;
        elsif v_command->>'kind' = 'destination' then
            if v_command->>'operation' not in ('record_destination_profile_review','promote_destination_profile','rollback_destination_profile') or
               jsonb_typeof(v_command->'added') <> 'object' or
               jsonb_array_length(v_command->'added'->'reviews') + jsonb_array_length(v_command->'added'->'promotions') +
               jsonb_array_length(v_command->'added'->'rollbacks') <> 1 then
                raise exception using errcode='22023', message='Destination commands append exactly one typed event';
            end if;
            select jsonb_build_object(
                'reviews', (select coalesce(jsonb_agg(event_payload order by id),'[]'::jsonb) from public.destination_profile_review_events),
                'promotions', (select coalesce(jsonb_agg(event_payload order by id),'[]'::jsonb) from public.destination_profile_promotion_events),
                'rollbacks', (select coalesce(jsonb_agg(event_payload order by id),'[]'::jsonb) from public.destination_profile_rollback_events))
                into v_current_revisions;
            if v_command->'expected' is distinct from v_current_revisions then
                raise exception using errcode='PT409', message='Destination review snapshot changed';
            end if;
            for v_row in select value from jsonb_array_elements(v_command->'added'->'reviews') loop
                select value into v_source from jsonb_array_elements(v_command->'source_profiles') where
                    value->'profile'->>'home_university'=v_row->>'home_university' and value->'profile'->>'school_name'=v_row->>'school_name';
                if v_source is null or public.exchange_community_request_fingerprint(v_source->'profile') <> v_row->>'profile_content_hash' then
                    raise exception using errcode='PT409', message='Destination source profile hash mismatch';
                end if;
                if v_row->>'reviewer_id' is distinct from v_command->>'actor' or
                   (select coalesce(jsonb_agg(url order by url),'[]'::jsonb) from
                       (select distinct lower(btrim(value)) url from jsonb_array_elements_text(v_row->'reviewed_source_urls')) s)
                   is distinct from
                   (select coalesce(jsonb_agg(url order by url),'[]'::jsonb) from
                       (select distinct lower(btrim(value->>'source_url')) url from jsonb_array_elements(v_source->'profile'->'sources')) s) or
                   jsonb_array_length(v_row->'reviewed_section_keys') <> 12 or
                   (select jsonb_agg(value order by value) from jsonb_array_elements_text(v_row->'reviewed_section_keys'))
                   is distinct from '["buy_after_arrival","campus_life","cost","coverage_boundary","first_72_hours","housing","identity_location","last_checked","official_sources","packing","student_guide","transport"]'::jsonb then
                    raise exception using errcode='PT409', message='Destination attestation must bind actor, all sources and sections';
                end if;
                if v_row->>'decision'='approve' and (
                    jsonb_array_length(v_source->'profile'->'sources')=0 or v_source->'profile'->>'last_checked' is null or
                    exists(select 1 from jsonb_array_elements(v_source->'profile'->'sources') where lower(value->>'source_url') not like 'https://%')) then
                    raise exception using errcode='PT409', message='Destination approval lacks current safe official evidence';
                end if;
                insert into public.destination_profile_review_events(id,profile_key,profile_content_hash,reviewer_id,decision,reviewed_at,event_payload)
                    values((v_row->>'id')::uuid,v_source->>'profile_key',v_row->>'profile_content_hash',v_row->>'reviewer_id',
                        v_row->>'decision',(v_row->>'reviewed_at')::timestamptz,v_row);
            end loop;
            for v_row in select value from jsonb_array_elements(v_command->'added'->'promotions') loop
                select value into v_source from jsonb_array_elements(v_command->'source_profiles') where
                    value->'profile'->>'home_university'=v_row->>'home_university' and value->'profile'->>'school_name'=v_row->>'school_name';
                if v_source is null or public.exchange_community_request_fingerprint(v_source->'profile') <> v_row->>'source_profile_content_hash' or
                   public.exchange_community_request_fingerprint(v_row->'promoted_profile') <> v_row->>'promoted_profile_content_hash' then
                    raise exception using errcode='PT409', message='Destination promotion profile hash mismatch';
                end if;
                if v_row->>'promoted_by_id' is distinct from v_command->>'actor' or
                   v_row->'promoted_profile'->>'coverage_status' <> 'official_verified' or
                   ((v_row->'promoted_profile') - array['coverage_status','coverage_note','last_checked'])
                   is distinct from ((v_source->'profile') - array['coverage_status','coverage_note','last_checked']) then
                    raise exception using errcode='PT409', message='Promotion cannot invent candidate facts or another actor';
                end if;
                select max(r.rolled_back_at) into v_cutoff from public.destination_profile_rollback_events r
                    join public.destination_profile_promotion_events p on p.id=r.rolled_back_promotion_event_id
                    where p.profile_key=v_source->>'profile_key' and p.source_profile_content_hash=v_row->>'source_profile_content_hash';
                select coalesce(jsonb_agg(event_payload order by id),'[]'::jsonb) into v_latest_reviews from (
                    select distinct on (lower(reviewer_id)) id,event_payload from public.destination_profile_review_events
                    where profile_key=v_source->>'profile_key' and profile_content_hash=v_row->>'source_profile_content_hash'
                        and (v_cutoff is null or reviewed_at > v_cutoff)
                    order by lower(reviewer_id),reviewed_at desc,id desc) t;
                if jsonb_array_length(v_latest_reviews) < 2 or exists(select 1 from jsonb_array_elements(v_latest_reviews)
                    where value->>'decision' <> 'approve') or
                    (select jsonb_agg(value->>'id' order by value->>'id') from jsonb_array_elements(v_latest_reviews))
                    is distinct from (select jsonb_agg(value order by value) from jsonb_array_elements_text(v_row->'review_event_ids')) then
                    raise exception using errcode='PT409', message='Promotion requires all latest independent approvals after any rollback';
                end if;
                select count(distinct lower(reviewer_id)) into v_distinct from public.destination_profile_review_events
                    where id::text in (select jsonb_array_elements_text(v_row->'review_event_ids')) and decision='approve'
                    and profile_key=v_source->>'profile_key' and profile_content_hash=v_row->>'source_profile_content_hash';
                if v_distinct < 2 or not exists(select 1 from public.destination_profile_review_events where
                    id::text in (select jsonb_array_elements_text(v_row->'review_event_ids')) and lower(reviewer_id)=lower(v_row->>'promoted_by_id')) then
                    raise exception using errcode='PT409', message='Destination promotion requires two independent approvals';
                end if;
                insert into public.destination_profile_promotion_events(id,profile_key,source_profile_content_hash,promoted_profile_content_hash,promoted_by_id,promoted_at,event_payload)
                    values(v_row->>'id',v_source->>'profile_key',v_row->>'source_profile_content_hash',v_row->>'promoted_profile_content_hash',
                        v_row->>'promoted_by_id',(v_row->>'promoted_at')::timestamptz,v_row);
            end loop;
            for v_row in select value from jsonb_array_elements(v_command->'added'->'rollbacks') loop
                select profile_key into v_key from public.destination_profile_promotion_events where id=v_row->>'rolled_back_promotion_event_id';
                if v_key is null or public.exchange_community_request_fingerprint(v_row->'restored_profile') <> v_row->>'restored_profile_content_hash' then
                    raise exception using errcode='PT409', message='Destination rollback target or content hash mismatch';
                end if;
                if v_row->>'rolled_back_by_id' is distinct from v_command->>'actor' or
                   v_row->>'rolled_back_from_event_id' <> v_row->>'rolled_back_promotion_event_id' or
                   exists(select 1 from public.destination_profile_rollback_events where rolled_back_promotion_event_id=v_row->>'rolled_back_promotion_event_id') or
                   (select id from public.destination_profile_promotion_events where profile_key=v_key order by promoted_at desc,id desc limit 1)
                       is distinct from v_row->>'rolled_back_promotion_event_id' then
                    raise exception using errcode='PT409', message='Destination rollback must target the latest active promotion';
                end if;
                select event_payload into v_payload from public.destination_profile_promotion_events where id=v_row->>'rolled_back_promotion_event_id';
                if v_payload->>'promoted_profile_content_hash' is distinct from v_row->>'previous_profile_content_hash' then
                    raise exception using errcode='PT409', message='Destination current publication hash changed';
                end if;
                select event_payload into v_prior_publication from (
                    select promoted_at as event_at,id,event_payload from public.destination_profile_promotion_events where profile_key=v_key
                    union all
                    select rolled_back_at,id,event_payload from public.destination_profile_rollback_events where profile_key=v_key
                ) t where (event_at,id) < ((v_payload->>'promoted_at')::timestamptz,v_payload->>'id')
                order by event_at desc,id desc limit 1;
                if v_prior_publication is null then
                    select value into v_source from jsonb_array_elements(v_command->'source_profiles') where value->>'profile_key'=v_key;
                    if v_source is null or v_row->'restored_profile' is distinct from v_source->'profile' or
                       v_row->>'restored_promotion_event_id' is not null then
                        raise exception using errcode='PT409', message='Rollback must restore the original candidate profile';
                    end if;
                elsif v_prior_publication ? 'promoted_profile' then
                    if v_row->'restored_profile' is distinct from v_prior_publication->'promoted_profile' or
                       v_row->>'restored_promotion_event_id' is distinct from v_prior_publication->>'id' then
                        raise exception using errcode='PT409', message='Rollback must restore the preceding reviewed promotion';
                    end if;
                elsif v_row->'restored_profile' is distinct from v_prior_publication->'restored_profile' or
                      v_row->>'restored_promotion_event_id' is distinct from v_prior_publication->>'restored_promotion_event_id' then
                    raise exception using errcode='PT409', message='Rollback must restore the preceding audited rollback state';
                end if;
                insert into public.destination_profile_rollback_events(id,profile_key,rolled_back_from_event_id,rolled_back_promotion_event_id,
                    restored_promotion_event_id,rolled_back_by_id,rolled_back_at,event_payload)
                    values(v_row->>'id',v_key,v_row->>'rolled_back_from_event_id',v_row->>'rolled_back_promotion_event_id',
                        v_row->>'restored_promotion_event_id',v_row->>'rolled_back_by_id',(v_row->>'rolled_back_at')::timestamptz,v_row);
            end loop;
        else
            raise exception using errcode='22023', message='Unknown governance command kind';
        end if;
        insert into public.application_workflow_audit_log(workflow_key,action,actor_id,note,metadata,created_at)
            values(case when v_command->>'kind'='workflow' then v_command->'revisions'->0->>'workflow_key' else '__governance_command_schema__' end,
                'submitted',v_command->>'actor',v_command->>'operation',
                v_command || jsonb_build_object('governance_command_hash',v_command_hash),p_updated_at);
        return jsonb_build_object('committed',true,'operation',v_command->>'operation');
    end if;

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
        content_hash = excluded.content_hash,
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
    perform pg_advisory_xact_lock(hashtextextended('exchange-content-governance-command', 0));
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


-- Capability evidence is read before sending a command envelope. Older schemas
-- cannot accidentally persist it as an ordinary legacy revision.
insert into public.application_workflows(workflow_key,home_university,partner_university)
    values('__governance_command_schema__','Internal governance schema','No public workflow') on conflict do nothing;
insert into public.application_workflow_audit_log(workflow_key,action,note,metadata)
    select '__governance_command_schema__','detected','Atomic governance command schema 1',jsonb_build_object('governance_command_schema',1)
    where not exists(select 1 from public.application_workflow_audit_log where metadata->>'governance_command_schema'='1');
