-- Student-visible application workflow error reports are operational feedback.
-- They never create, approve, or publish governed application content.

create table public.application_workflow_issue_reports (
  id text primary key,
  workflow_key text not null,
  workflow_id text not null,
  workflow_version integer not null,
  workflow_snapshot text not null,
  home_school text not null,
  school_name text not null,
  step_rule_id text,
  step_title text,
  college text,
  department text,
  academic_year text,
  application_round text,
  category text not null,
  description text not null,
  official_source_url text not null,
  status text not null,
  reporter_account_id text
    references public.exchange_accounts(id) on delete set null,
  mutation_id text not null,
  request_fingerprint text not null,
  created_at timestamptz not null,
  updated_at timestamptz not null,
  reporter_deleted_at timestamptz,
  retained_until timestamptz,
  constraint application_workflow_issue_reports_workflow_key_length
    check (char_length(workflow_key) between 1 and 500),
  constraint application_workflow_issue_reports_workflow_id_length
    check (char_length(workflow_id) between 8 and 128),
  constraint application_workflow_issue_reports_workflow_version_positive
    check (workflow_version >= 1),
  constraint application_workflow_issue_reports_snapshot_shape
    check (workflow_snapshot ~ '^[0-9a-f]{64}$'),
  constraint application_workflow_issue_reports_home_school_length
    check (char_length(home_school) between 2 and 80),
  constraint application_workflow_issue_reports_school_name_length
    check (char_length(school_name) between 2 and 200),
  constraint application_workflow_issue_reports_step_rule_id_length
    check (step_rule_id is null or char_length(step_rule_id) between 1 and 240),
  constraint application_workflow_issue_reports_step_title_length
    check (step_title is null or char_length(step_title) between 1 and 300),
  constraint application_workflow_issue_reports_college_length
    check (college is null or char_length(college) between 1 and 120),
  constraint application_workflow_issue_reports_department_length
    check (department is null or char_length(department) between 1 and 120),
  constraint application_workflow_issue_reports_academic_year_length
    check (academic_year is null or char_length(academic_year) between 1 and 40),
  constraint application_workflow_issue_reports_round_length
    check (application_round is null or char_length(application_round) between 1 and 80),
  constraint application_workflow_issue_reports_category_value
    check (category in ('eligibility', 'deadline', 'document', 'submission', 'source', 'other')),
  constraint application_workflow_issue_reports_description_length
    check (char_length(description) between 10 and 1000),
  constraint application_workflow_issue_reports_source_length
    check (char_length(official_source_url) between 12 and 2000),
  constraint application_workflow_issue_reports_source_https
    check (official_source_url ~* '^https://'),
  constraint application_workflow_issue_reports_status_value
    check (status in ('pending', 'resolved', 'dismissed')),
  constraint application_workflow_issue_reports_mutation_shape
    check (
      char_length(mutation_id) between 16 and 128
      and mutation_id ~ '^[A-Za-z0-9._:-]+$'
    ),
  constraint application_workflow_issue_reports_fingerprint_shape
    check (request_fingerprint ~ '^[0-9a-f]{64}$'),
  constraint application_workflow_issue_reports_time_order
    check (updated_at >= created_at),
  constraint application_workflow_issue_reports_retention_pair
    check (
      (reporter_deleted_at is null and retained_until is null)
      or (
        reporter_account_id is null
        and reporter_deleted_at is not null
        and retained_until is not null
        and retained_until > reporter_deleted_at
      )
    )
);

create unique index application_workflow_issue_reports_reporter_mutation_unique
  on public.application_workflow_issue_reports (reporter_account_id, mutation_id)
  where reporter_account_id is not null;

create index application_workflow_issue_reports_status_created_idx
  on public.application_workflow_issue_reports (status, created_at desc, id);

create index application_workflow_issue_reports_reporter_created_idx
  on public.application_workflow_issue_reports (
    reporter_account_id,
    created_at desc,
    id
  )
  where reporter_account_id is not null;

create index application_workflow_issue_reports_retention_idx
  on public.application_workflow_issue_reports (retained_until, id)
  where retained_until is not null;

create table public.application_workflow_issue_report_reviews (
  id text primary key,
  report_id text not null unique
    references public.application_workflow_issue_reports(id) on delete cascade,
  status text not null,
  note text not null,
  reviewer_account_id text
    references public.exchange_accounts(id) on delete set null,
  reviewer_display_name text not null,
  mutation_id text not null,
  request_fingerprint text not null,
  reviewed_at timestamptz not null,
  constraint application_workflow_issue_report_reviews_status_value
    check (status in ('resolved', 'dismissed')),
  constraint application_workflow_issue_report_reviews_note_length
    check (char_length(note) between 10 and 1000),
  constraint application_workflow_issue_report_reviews_display_name_length
    check (char_length(reviewer_display_name) between 1 and 200),
  constraint application_workflow_issue_report_reviews_mutation_shape
    check (
      char_length(mutation_id) between 16 and 128
      and mutation_id ~ '^[A-Za-z0-9._:-]+$'
    ),
  constraint application_workflow_issue_report_reviews_fingerprint_shape
    check (request_fingerprint ~ '^[0-9a-f]{64}$')
);

create unique index application_workflow_issue_report_reviews_reviewer_mutation_unique
  on public.application_workflow_issue_report_reviews (
    reviewer_account_id,
    mutation_id
  )
  where reviewer_account_id is not null;

create index application_workflow_issue_report_reviews_reviewed_idx
  on public.application_workflow_issue_report_reviews (reviewed_at desc, id);

create or replace function public.exchange_submit_application_workflow_issue_report(
  p_account_id text,
  p_mutation_id text,
  p_request_fingerprint text,
  p_report jsonb,
  p_rate_limit integer,
  p_rate_window_seconds integer
) returns jsonb
language plpgsql
security definer
set search_path = public, pg_temp
as $$
declare
  v_account public.exchange_accounts%rowtype;
  v_existing public.application_workflow_issue_reports%rowtype;
  v_report public.application_workflow_issue_reports%rowtype;
  v_now timestamptz;
  v_window_start timestamptz;
  v_oldest_in_window timestamptz;
  v_recent_count integer;
  v_retry_after integer;
  v_workflow_key text;
  v_workflow_id text;
  v_workflow_version integer;
  v_workflow_snapshot text;
  v_home_school text;
  v_school_name text;
  v_step_rule_id text;
  v_step_title text;
  v_college text;
  v_department text;
  v_academic_year text;
  v_application_round text;
  v_category text;
  v_description text;
  v_official_source_url text;
  v_fingerprint text;
begin
  if p_account_id is null
     or char_length(p_account_id) not between 8 and 128
     or p_mutation_id is null
     or char_length(p_mutation_id) not between 16 and 128
     or p_mutation_id !~ '^[A-Za-z0-9._:-]+$'
     or p_request_fingerprint !~ '^[0-9a-f]{64}$'
     or p_rate_limit is distinct from 10
     or p_rate_window_seconds is distinct from 3600
     or not public.exchange_community_payload_has_only_keys(
       p_report,
       array[
         'workflow_key', 'workflow_id', 'workflow_version', 'workflow_snapshot',
         'home_school', 'school_name', 'step_rule_id', 'step_title', 'college',
         'department', 'academic_year', 'application_round', 'category',
         'description', 'official_source_url'
       ]
     )
     or not (
       p_report ?& array[
         'workflow_key', 'workflow_id', 'workflow_version', 'workflow_snapshot',
         'home_school', 'school_name', 'step_rule_id', 'step_title', 'college',
         'department', 'academic_year', 'application_round', 'category',
         'description', 'official_source_url'
       ]
     ) then
    return jsonb_build_object('status', 'invalid_request');
  end if;

  if jsonb_typeof(p_report -> 'workflow_version') is distinct from 'number'
     or p_report ->> 'workflow_version' !~ '^[1-9][0-9]{0,8}$' then
    return jsonb_build_object('status', 'invalid_request');
  end if;

  v_workflow_key := nullif(btrim(p_report ->> 'workflow_key'), '');
  v_workflow_id := nullif(btrim(p_report ->> 'workflow_id'), '');
  v_workflow_version := (p_report ->> 'workflow_version')::integer;
  v_workflow_snapshot := nullif(btrim(p_report ->> 'workflow_snapshot'), '');
  v_home_school := nullif(btrim(p_report ->> 'home_school'), '');
  v_school_name := nullif(btrim(p_report ->> 'school_name'), '');
  v_step_rule_id := nullif(btrim(p_report ->> 'step_rule_id'), '');
  v_step_title := nullif(btrim(p_report ->> 'step_title'), '');
  v_college := nullif(btrim(p_report ->> 'college'), '');
  v_department := nullif(btrim(p_report ->> 'department'), '');
  v_academic_year := nullif(btrim(p_report ->> 'academic_year'), '');
  v_application_round := nullif(btrim(p_report ->> 'application_round'), '');
  v_category := nullif(btrim(p_report ->> 'category'), '');
  v_description := nullif(btrim(p_report ->> 'description'), '');
  v_official_source_url := nullif(btrim(p_report ->> 'official_source_url'), '');

  if v_workflow_key is null or char_length(v_workflow_key) > 500
     or v_workflow_id is null or char_length(v_workflow_id) not between 8 and 128
     or v_workflow_snapshot is null
     or v_workflow_snapshot !~ '^[0-9a-f]{64}$'
     or v_home_school is null or char_length(v_home_school) not between 2 and 80
     or v_school_name is null or char_length(v_school_name) not between 2 and 200
     or char_length(coalesce(v_step_rule_id, '')) > 240
     or char_length(coalesce(v_step_title, '')) > 300
     or char_length(coalesce(v_college, '')) > 120
     or char_length(coalesce(v_department, '')) > 120
     or char_length(coalesce(v_academic_year, '')) > 40
     or char_length(coalesce(v_application_round, '')) > 80
     or v_category is null
     or v_category not in ('eligibility', 'deadline', 'document', 'submission', 'source', 'other')
     or v_description is null or char_length(v_description) not between 10 and 1000
     or v_official_source_url is null
     or char_length(v_official_source_url) not between 12 and 2000
     or v_official_source_url !~* '^https://'
     or v_official_source_url ~ '[[:cntrl:]]'
     or v_official_source_url ~* '^https://[^/]*@'
     or v_official_source_url !~* '^https://[^/?#:]+\.[^/?#:]+(:[0-9]{1,5})?([/?#]|$)'
     or v_official_source_url ~* '^https://\['
     or v_official_source_url ~* '^https://(localhost|[^/]+\.localhost)(:|/|$)'
     or v_official_source_url ~* '^https://(10\.|192\.168\.|172\.(1[6-9]|2[0-9]|3[01])\.|169\.254\.|127\.|0\.)'
     or v_official_source_url ~* '^https://100\.(6[4-9]|[7-9][0-9]|1[01][0-9]|12[0-7])\.'
     or v_official_source_url ~* '^https://198\.(1[89])\.'
     or v_official_source_url ~* '^https://(192\.0\.0\.|192\.0\.2\.|198\.51\.100\.|203\.0\.113\.)'
     or v_official_source_url ~* '^https://(22[4-9]|23[0-9]|24[0-9]|25[0-5])\.' then
    return jsonb_build_object('status', 'invalid_request');
  end if;

  v_fingerprint := public.exchange_community_request_fingerprint(
    jsonb_build_object(
      'workflow_key', v_workflow_key,
      'workflow_id', v_workflow_id,
      'workflow_version', v_workflow_version,
      'workflow_snapshot', v_workflow_snapshot,
      'home_school', v_home_school,
      'school_name', v_school_name,
      'step_rule_id', v_step_rule_id,
      'step_title', v_step_title,
      'college', v_college,
      'department', v_department,
      'academic_year', v_academic_year,
      'application_round', v_application_round,
      'category', v_category,
      'description', v_description,
      'official_source_url', v_official_source_url
    )
  );

  if v_fingerprint is distinct from p_request_fingerprint then
    return jsonb_build_object('status', 'invalid_request');
  end if;

  select account.* into v_account
  from public.exchange_accounts account
  where account.id = p_account_id
  for update;

  if not found then
    return jsonb_build_object('status', 'account_missing');
  end if;

  if v_account.profile -> 'student_status_verified' is distinct from 'true'::jsonb
     or nullif(btrim(v_account.profile ->> 'verified_university'), '') is null then
    return jsonb_build_object('status', 'student_verification_required');
  end if;

  select report.* into v_existing
  from public.application_workflow_issue_reports report
  where report.reporter_account_id = p_account_id
    and report.mutation_id = p_mutation_id;

  if found then
    if v_existing.request_fingerprint is distinct from v_fingerprint then
      return jsonb_build_object('status', 'idempotency_conflict');
    end if;
    return jsonb_build_object(
      'status', 'committed',
      'report', to_jsonb(v_existing),
      'idempotent', true
    );
  end if;

  v_now := clock_timestamp();
  v_window_start := v_now - make_interval(secs => p_rate_window_seconds);
  select count(*)::integer, min(report.created_at)
    into v_recent_count, v_oldest_in_window
  from public.application_workflow_issue_reports report
  where report.reporter_account_id = p_account_id
    and report.created_at > v_window_start;

  if v_recent_count >= p_rate_limit then
    v_retry_after := greatest(
      1,
      ceil(extract(epoch from (
        v_oldest_in_window + make_interval(secs => p_rate_window_seconds) - v_now
      )))::integer
    );
    return jsonb_build_object(
      'status', 'rate_limited',
      'retry_after_seconds', v_retry_after
    );
  end if;

  insert into public.application_workflow_issue_reports (
    id, workflow_key, workflow_id, workflow_version, workflow_snapshot,
    home_school, school_name, step_rule_id, step_title, college, department,
    academic_year, application_round, category, description,
    official_source_url, status, reporter_account_id, mutation_id,
    request_fingerprint, created_at, updated_at
  ) values (
    replace(gen_random_uuid()::text, '-', ''),
    v_workflow_key, v_workflow_id, v_workflow_version, v_workflow_snapshot,
    v_home_school, v_school_name, v_step_rule_id, v_step_title, v_college,
    v_department, v_academic_year, v_application_round, v_category,
    v_description, v_official_source_url, 'pending', p_account_id,
    p_mutation_id, v_fingerprint, v_now, v_now
  ) returning * into v_report;

  return jsonb_build_object(
    'status', 'committed',
    'report', to_jsonb(v_report),
    'idempotent', false
  );
end;
$$;

create or replace function public.exchange_review_application_workflow_issue_report(
  p_reviewer_account_id text,
  p_mutation_id text,
  p_request_fingerprint text,
  p_review jsonb
) returns jsonb
language plpgsql
security definer
set search_path = public, pg_temp
as $$
declare
  v_account public.exchange_accounts%rowtype;
  v_report public.application_workflow_issue_reports%rowtype;
  v_existing public.application_workflow_issue_report_reviews%rowtype;
  v_review public.application_workflow_issue_report_reviews%rowtype;
  v_report_id text;
  v_status text;
  v_note text;
  v_reviewer_display_name text;
  v_fingerprint text;
  v_now timestamptz;
  v_response jsonb;
begin
  if p_reviewer_account_id is null
     or char_length(p_reviewer_account_id) not between 8 and 128
     or p_mutation_id is null
     or char_length(p_mutation_id) not between 16 and 128
     or p_mutation_id !~ '^[A-Za-z0-9._:-]+$'
     or p_request_fingerprint !~ '^[0-9a-f]{64}$'
     or not public.exchange_community_payload_has_only_keys(
       p_review,
       array['report_id', 'status', 'note']
     )
     or not (p_review ?& array['report_id', 'status', 'note']) then
    return jsonb_build_object('status', 'invalid_request');
  end if;

  v_report_id := nullif(btrim(p_review ->> 'report_id'), '');
  v_status := nullif(btrim(p_review ->> 'status'), '');
  v_note := nullif(btrim(p_review ->> 'note'), '');

  if v_report_id is null or char_length(v_report_id) > 128
     or v_status is null
     or v_status not in ('resolved', 'dismissed')
     or v_note is null or char_length(v_note) not between 10 and 1000 then
    return jsonb_build_object('status', 'invalid_request');
  end if;

  v_fingerprint := public.exchange_community_request_fingerprint(
    jsonb_build_object(
      'report_id', v_report_id,
      'status', v_status,
      'note', v_note
    )
  );

  if v_fingerprint is distinct from p_request_fingerprint then
    return jsonb_build_object('status', 'invalid_request');
  end if;

  -- Actor rows are always locked before feature rows.  Account deletion uses
  -- the same order, avoiding a review/delete deadlock.
  select account.* into v_account
  from public.exchange_accounts account
  where account.id = p_reviewer_account_id
  for update;

  if not found then
    return jsonb_build_object('status', 'account_missing');
  end if;

  select review.* into v_existing
  from public.application_workflow_issue_report_reviews review
  where review.reviewer_account_id = p_reviewer_account_id
    and review.mutation_id = p_mutation_id;

  if found then
    if v_existing.request_fingerprint is distinct from v_fingerprint then
      return jsonb_build_object('status', 'idempotency_conflict');
    end if;
    select report.* into v_report
    from public.application_workflow_issue_reports report
    where report.id = v_existing.report_id;
    if not found then
      return jsonb_build_object('status', 'report_missing');
    end if;
    return jsonb_build_object(
      'status', 'committed',
      'report', to_jsonb(v_report),
      'review', to_jsonb(v_existing),
      'idempotent', true
    );
  end if;

  select report.* into v_report
  from public.application_workflow_issue_reports report
  where report.id = v_report_id
  for update;

  if not found then
    return jsonb_build_object('status', 'report_missing');
  end if;

  if v_report.status <> 'pending' then
    return jsonb_build_object('status', 'status_conflict');
  end if;

  v_now := clock_timestamp();
  v_reviewer_display_name := coalesce(
    nullif(btrim(v_account.profile ->> 'display_name'), ''),
    '內容管理員'
  );

  insert into public.application_workflow_issue_report_reviews (
    id, report_id, status, note, reviewer_account_id,
    reviewer_display_name, mutation_id, request_fingerprint, reviewed_at
  ) values (
    replace(gen_random_uuid()::text, '-', ''),
    v_report.id, v_status, v_note, p_reviewer_account_id,
    v_reviewer_display_name, p_mutation_id, v_fingerprint, v_now
  ) returning * into v_review;

  update public.application_workflow_issue_reports
  set status = v_status,
      updated_at = v_now,
      retained_until = case
        when reporter_deleted_at is not null then least(
          coalesce(retained_until, v_now + make_interval(hours => 24)),
          v_now + make_interval(hours => 24)
        )
        else retained_until
      end
  where id = v_report.id
  returning * into v_report;

  v_response := jsonb_build_object(
    'status', 'committed',
    'report', to_jsonb(v_report),
    'review', to_jsonb(v_review),
    'idempotent', false
  );

  return v_response;
end;
$$;

create or replace function public.exchange_purge_expired_application_workflow_issue_reports()
returns jsonb
language plpgsql
security definer
set search_path = public, pg_temp
as $$
declare
  v_now timestamptz := clock_timestamp();
  v_purged integer;
begin
  delete from public.application_workflow_issue_reports report
  where report.reporter_account_id is null
    and report.retained_until is not null
    and report.retained_until <= v_now;
  get diagnostics v_purged = row_count;

  return jsonb_build_object(
    'status', 'committed',
    'purged_at', v_now,
    'purged_count', v_purged
  );
end;
$$;

create or replace function public.exchange_deidentify_application_workflow_issue_reports()
returns trigger
language plpgsql
security definer
set search_path = public, pg_temp
as $$
declare
  v_now timestamptz := clock_timestamp();
begin
  -- Closed reports have no remaining safety purpose after their reporter asks
  -- for account deletion, so remove the complete report and review.
  delete from public.application_workflow_issue_reports report
  where report.reporter_account_id = old.id
    and report.status in ('resolved', 'dismissed');

  -- Pending reports retain only operational evidence, without account or
  -- idempotency identifiers, for at most 90 days.
  update public.application_workflow_issue_reports report
  set reporter_account_id = null,
      reporter_deleted_at = v_now,
      retained_until = v_now + make_interval(days => 90),
      mutation_id = 'deleted-' || replace(gen_random_uuid()::text, '-', ''),
      request_fingerprint = public.exchange_community_request_fingerprint(
        jsonb_build_object('deleted_reporter', gen_random_uuid()::text)
      )
  where report.reporter_account_id = old.id
    and report.status = 'pending';

  -- Reviews remain useful as a decision audit, but no deleted reviewer identity
  -- or idempotency key is retained.
  update public.application_workflow_issue_report_reviews review
  set reviewer_account_id = null,
      reviewer_display_name = '已刪除管理員',
      mutation_id = 'deleted-' || replace(gen_random_uuid()::text, '-', ''),
      request_fingerprint = public.exchange_community_request_fingerprint(
        jsonb_build_object('deleted_reviewer', gen_random_uuid()::text)
      )
  where review.reviewer_account_id = old.id;

  return old;
end;
$$;

drop trigger if exists exchange_deidentify_application_workflow_issue_reports_trigger
  on public.exchange_accounts;

create trigger exchange_deidentify_application_workflow_issue_reports_trigger
before delete on public.exchange_accounts
for each row execute function public.exchange_deidentify_application_workflow_issue_reports();

alter table public.application_workflow_issue_reports enable row level security;
alter table public.application_workflow_issue_reports force row level security;
alter table public.application_workflow_issue_report_reviews enable row level security;
alter table public.application_workflow_issue_report_reviews force row level security;

revoke all on table public.application_workflow_issue_reports
  from public, anon, authenticated, service_role;
revoke all on table public.application_workflow_issue_report_reviews
  from public, anon, authenticated, service_role;

grant select on table public.application_workflow_issue_reports to service_role;
grant select on table public.application_workflow_issue_report_reviews to service_role;

revoke all on function public.exchange_submit_application_workflow_issue_report(text, text, text, jsonb, integer, integer)
  from public, anon, authenticated, service_role;
revoke all on function public.exchange_review_application_workflow_issue_report(text, text, text, jsonb)
  from public, anon, authenticated, service_role;
revoke all on function public.exchange_purge_expired_application_workflow_issue_reports()
  from public, anon, authenticated, service_role;
revoke all on function public.exchange_deidentify_application_workflow_issue_reports()
  from public, anon, authenticated, service_role;

grant execute on function public.exchange_submit_application_workflow_issue_report(text, text, text, jsonb, integer, integer)
  to service_role;
grant execute on function public.exchange_review_application_workflow_issue_report(text, text, text, jsonb)
  to service_role;
grant execute on function public.exchange_purge_expired_application_workflow_issue_reports()
  to service_role;
