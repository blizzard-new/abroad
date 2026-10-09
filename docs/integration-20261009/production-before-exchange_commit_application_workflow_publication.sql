CREATE OR REPLACE FUNCTION public.exchange_commit_application_workflow_publication(p_workflow_key text, p_home_university text, p_partner_university text, p_program_type text, p_academic_year text, p_application_round text, p_published_version integer, p_published_payload jsonb, p_published_at timestamp with time zone, p_current_revision_id text, p_updated_at timestamp with time zone)
 RETURNS jsonb
 LANGUAGE plpgsql
 SET search_path TO ''
AS $function$
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
$function$
