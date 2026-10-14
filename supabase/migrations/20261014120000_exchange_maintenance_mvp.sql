-- Phase 1 & 2 Migration Draft: Uniway All-Taiwan Exchange Information Maintenance Architecture (Local Server v1.1)
-- Covers Sections 4.1 (Core Entities), 4.2 (Sources & Evidence), 4.3 (Review & Publication), 4.4 (Ops, Queue & Submissions),
-- and Section 6.2 (Lease Fencing & Idempotent Queue Effects).
-- All tables enable RLS and revoke anon/authenticated access; public reads go through FastAPI pinned release projections.

create table if not exists public.exchange_maint_institutions (
  id text primary key,
  country_code text not null,
  canonical_name text not null,
  english_name text,
  institution_type text not null check (institution_type in ('home', 'host', 'both')),
  official_url text,
  current_revision_id text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists public.exchange_maint_institution_aliases (
  id text primary key,
  institution_id text not null references public.exchange_maint_institutions(id) on delete cascade,
  alias text not null,
  normalized_alias text not null,
  language text not null default 'und',
  source_id text,
  created_at timestamptz not null default now(),
  unique (institution_id, normalized_alias)
);

create table if not exists public.exchange_maint_campuses (
  id text primary key,
  institution_id text not null references public.exchange_maint_institutions(id) on delete cascade,
  code text not null,
  canonical_name text not null,
  city text,
  created_at timestamptz not null default now(),
  unique (institution_id, code)
);

create table if not exists public.exchange_maint_academic_units (
  id text primary key,
  institution_id text not null references public.exchange_maint_institutions(id) on delete cascade,
  campus_id text references public.exchange_maint_campuses(id) on delete set null,
  unit_type text not null check (unit_type in ('college', 'department', 'graduate_institute', 'program', 'other')),
  canonical_name text not null,
  created_at timestamptz not null default now()
);

create table if not exists public.exchange_maint_programs (
  id text primary key,
  home_id text not null references public.exchange_maint_institutions(id) on delete cascade,
  program_type text not null check (program_type in ('university_level', 'college_level', 'department_level', 'dual_degree', 'short_term', 'visiting')),
  official_label text not null,
  created_at timestamptz not null default now()
);

create table if not exists public.exchange_maint_cycles (
  id text primary key,
  program_id text not null references public.exchange_maint_programs(id) on delete cascade,
  original_label text not null,
  application_year integer,
  target_year_start integer,
  target_year_end integer,
  term_scope text not null check (term_scope in ('fall', 'spring', 'full_year', 'both_semesters', 'summer', 'unspecified')),
  conversion_rule text,
  year_verified boolean not null default false,
  created_at timestamptz not null default now()
);

create table if not exists public.exchange_maint_offerings (
  id text primary key,
  home_id text not null references public.exchange_maint_institutions(id) on delete cascade,
  host_id text not null references public.exchange_maint_institutions(id) on delete cascade,
  program_id text not null references public.exchange_maint_programs(id) on delete cascade,
  cycle_id text not null references public.exchange_maint_cycles(id) on delete cascade,
  scope_key text not null unique,
  lifecycle_status text not null default 'unknown' check (
    lifecycle_status in ('announced', 'open', 'closed', 'withdrawn', 'agreement_only', 'unknown')
  ),
  current_revision_id text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists public.exchange_maint_offering_scopes (
  id text primary key,
  offering_id text not null references public.exchange_maint_offerings(id) on delete cascade,
  dimension text not null check (dimension in ('campus', 'academic_unit', 'degree_level')),
  scope_mode text not null check (scope_mode in ('all', 'explicit', 'unspecified', 'not_applicable')),
  target_id text not null default '',
  target_label text not null default '',
  created_at timestamptz not null default now(),
  unique (offering_id, dimension, scope_mode, target_id)
);

create table if not exists public.exchange_maint_sources (
  id text primary key,
  owner_institution_id text not null references public.exchange_maint_institutions(id) on delete cascade,
  source_type text not null check (
    source_type in ('official_announcement', 'official_quota_list', 'official_partner_detail', 'official_fact_sheet', 'authorized_experience_feed', 'manual_admin')
  ),
  authority_scope jsonb not null default '[]'::jsonb,
  approved_domains jsonb not null default '[]'::jsonb,
  entry_url text not null,
  terms_url text,
  reuse_basis text not null check (reuse_basis in ('official_public_fact', 'explicit_consent', 'link_and_short_excerpt_only', 'internal_verification_only')),
  enabled boolean not null default true,
  policy_version text not null default 'v1',
  risk_class text not null default 'high' check (risk_class in ('high', 'medium', 'low')),
  min_interval_seconds integer not null default 86400 check (min_interval_seconds >= 60),
  max_interval_seconds integer not null default 604800 check (max_interval_seconds >= min_interval_seconds),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists public.exchange_maint_source_resources (
  id text primary key,
  source_id text not null references public.exchange_maint_sources(id) on delete cascade,
  normalized_url text not null,
  original_url text not null,
  resource_kind text not null check (resource_kind in ('html_list', 'html_detail', 'pdf_attachment', 'doc_attachment', 'api_json', 'rss_feed')),
  discovered_from_id text references public.exchange_maint_source_resources(id) on delete set null,
  expected_scope jsonb not null default '{}'::jsonb,
  etag text,
  last_modified text,
  health_status text not null default 'healthy' check (health_status in ('healthy', 'temporary_error', 'blocked', 'missing')),
  last_checked_at timestamptz,
  last_successfully_checked_at timestamptz,
  last_meaningful_change_at timestamptz,
  next_due_at timestamptz,
  created_at timestamptz not null default now(),
  unique (source_id, normalized_url)
);

create table if not exists public.exchange_maint_content_blobs (
  id text primary key,
  raw_sha256 text not null unique check (raw_sha256 ~ '^[0-9a-f]{64}$'),
  normalized_content_hash text not null check (normalized_content_hash ~ '^[0-9a-f]{64}$'),
  storage_key text not null unique,
  mime text not null,
  byte_count bigint not null check (byte_count >= 0),
  retention_class text not null default 'standard_90d' check (retention_class in ('standard_90d', 'published_evidence', 'ephemeral_metadata_only')),
  created_at timestamptz not null default now()
);

create table if not exists public.exchange_maint_snapshots (
  id text primary key,
  resource_id text not null references public.exchange_maint_source_resources(id) on delete cascade,
  blob_id text not null references public.exchange_maint_content_blobs(id) on delete restrict,
  fetched_at timestamptz not null default now(),
  source_published_at timestamptz,
  source_modified_at timestamptz,
  content_language text not null default 'zh-TW',
  input_context_hash text not null check (input_context_hash ~ '^[0-9a-f]{64}$')
);

create table if not exists public.exchange_maint_fetch_attempts (
  id text primary key,
  resource_id text not null references public.exchange_maint_source_resources(id) on delete cascade,
  started_at timestamptz not null,
  finished_at timestamptz not null,
  status_code integer,
  outcome text not null check (outcome in ('fetched_200', 'not_modified_304', 'redirected', 'http_error', 'network_error', 'ssrf_blocked', 'size_exceeded', 'mime_rejected')),
  redirect_chain jsonb not null default '[]'::jsonb,
  bytes bigint not null default 0,
  error_class text,
  retry_after integer,
  validated_snapshot_id text references public.exchange_maint_snapshots(id) on delete set null
);

create table if not exists public.exchange_maint_source_links (
  id text primary key,
  parent_snapshot_id text not null references public.exchange_maint_snapshots(id) on delete cascade,
  child_resource_id text not null references public.exchange_maint_source_resources(id) on delete cascade,
  link_text text not null default '',
  relation_type text not null check (relation_type in ('detail_page', 'attachment', 'amendment', 'fact_sheet', 'external_reference')),
  context_hash text not null check (context_hash ~ '^[0-9a-f]{64}$'),
  created_at timestamptz not null default now()
);

create table if not exists public.exchange_maint_extraction_runs (
  id text primary key,
  snapshot_id text not null references public.exchange_maint_snapshots(id) on delete cascade,
  blob_id text not null references public.exchange_maint_content_blobs(id) on delete cascade,
  parser_name text not null,
  parser_version text not null,
  schema_version text not null,
  model_version_optional text,
  input_context_hash text not null check (input_context_hash ~ '^[0-9a-f]{64}$'),
  semantic_field_hash text not null check (semantic_field_hash ~ '^[0-9a-f]{64}$'),
  change_origin text not null check (change_origin in ('source_change', 'parser_change', 'context_change', 'unchanged')),
  status text not null check (status in ('succeeded', 'failed_schema', 'failed_ abrupt_drop', 'page_limit_exceeded')),
  created_at timestamptz not null default now()
);

create table if not exists public.exchange_maint_evidence (
  id text primary key,
  snapshot_id text not null references public.exchange_maint_snapshots(id) on delete cascade,
  locator jsonb not null,
  short_excerpt text not null,
  excerpt_hash text not null check (excerpt_hash ~ '^[0-9a-f]{64}$'),
  evidence_kind text not null check (evidence_kind in ('html_section', 'html_table_row', 'pdf_table_cell', 'pdf_paragraph', 'official_api_field')),
  access_class text not null default 'private_snapshot' check (access_class in ('private_snapshot', 'link_only', 'suppressed')),
  created_at timestamptz not null default now()
);

create table if not exists public.exchange_maint_field_assertions (
  id text primary key,
  entity_scope text not null,
  field_path text not null,
  typed_value jsonb,
  value_state text not null check (
    value_state in ('known', 'not_stated', 'not_applicable', 'conflicting', 'unverified', 'legacy_unverified')
  ),
  unit text,
  effective_scope jsonb not null default '{}'::jsonb,
  evidence_id text not null references public.exchange_maint_evidence(id) on delete cascade,
  extraction_run_id text not null references public.exchange_maint_extraction_runs(id) on delete cascade,
  supersedes_assertion_id text references public.exchange_maint_field_assertions(id) on delete set null,
  verification_checks jsonb not null default '{}'::jsonb,
  verification_outcome text not null check (verification_outcome in ('pass', 'fail', 'needs_review')),
  created_at timestamptz not null default now()
);

create table if not exists public.exchange_maint_change_sets (
  id text primary key,
  entity_scope text not null,
  home_id text references public.exchange_maint_institutions(id) on delete cascade,
  host_id text references public.exchange_maint_institutions(id) on delete cascade,
  program_id text references public.exchange_maint_programs(id) on delete set null,
  cycle_id text references public.exchange_maint_cycles(id) on delete set null,
  base_release_id text,
  candidate_version integer not null default 1 check (candidate_version >= 1),
  evidence_set_hash text not null check (evidence_set_hash ~ '^[0-9a-f]{64}$'),
  risk text not null check (risk in ('high', 'medium', 'low')),
  change_origin text not null default 'source_change' check (change_origin in ('source_change', 'parser_change', 'context_change', 'manual_correction')),
  status text not null default 'pending' check (
    status in ('pending', 'approved', 'partially_approved', 'rejected', 'deferred', 'superseded', 'published', 'conflicting')
  ),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists public.exchange_maint_change_items (
  id text primary key,
  change_set_id text not null references public.exchange_maint_change_sets(id) on delete cascade,
  field_path text not null,
  before_value jsonb,
  after_value jsonb,
  before_state text,
  after_state text not null,
  unit text,
  effective_scope jsonb not null default '{}'::jsonb,
  supporting_assertions jsonb not null default '[]'::jsonb,
  conflicting_assertions jsonb not null default '[]'::jsonb,
  reason text not null,
  approval_status text not null default 'pending' check (approval_status in ('pending', 'approved', 'rejected', 'deferred')),
  unique (change_set_id, field_path)
);

create table if not exists public.exchange_maint_review_decisions (
  id text primary key,
  change_set_id text not null references public.exchange_maint_change_sets(id) on delete cascade,
  candidate_version integer not null,
  evidence_set_hash text not null check (evidence_set_hash ~ '^[0-9a-f]{64}$'),
  reviewer_id text not null,
  decision text not null check (decision in ('approve', 'reject', 'defer', 'recheck', 'flag_source')),
  selected_fields jsonb not null default '[]'::jsonb,
  reason text not null,
  idempotency_key text not null unique,
  decided_at timestamptz not null default now()
);

create table if not exists public.exchange_maint_entity_revisions (
  id text primary key,
  entity_type text not null check (entity_type in ('institution', 'offering', 'experience')),
  entity_id text not null,
  payload_schema_version text not null default 'v1',
  payload jsonb not null,
  provenance_map jsonb not null default '{}'::jsonb,
  revision_hash text not null check (revision_hash ~ '^[0-9a-f]{64}$'),
  created_at timestamptz not null default now()
);

create table if not exists public.exchange_maint_releases (
  id text primary key,
  previous_release_id text references public.exchange_maint_releases(id) on delete restrict,
  reason text not null,
  published_by text not null,
  published_at timestamptz not null default now(),
  status text not null default 'published' check (status in ('published', 'rolled_back_source')),
  idempotency_key text not null unique
);

create table if not exists public.exchange_maint_release_members (
  release_id text not null references public.exchange_maint_releases(id) on delete cascade,
  entity_type text not null check (entity_type in ('institution', 'offering', 'experience')),
  entity_id text not null,
  revision_id text not null references public.exchange_maint_entity_revisions(id) on delete restrict,
  primary key (release_id, entity_type, entity_id)
);

create table if not exists public.exchange_maint_publication_head (
  singleton_id boolean primary key default true check (singleton_id),
  current_release_id text references public.exchange_maint_releases(id) on delete restrict,
  lock_version bigint not null default 0,
  updated_at timestamptz not null default now()
);

create table if not exists public.exchange_maint_suppressions (
  id text primary key,
  target_type text not null check (target_type in ('entity', 'revision', 'evidence', 'experience', 'source')),
  target_id text not null,
  reason text not null,
  suppressed_by text not null,
  suppressed_at timestamptz not null default now(),
  active boolean not null default true,
  unique (target_type, target_id)
);

create table if not exists public.exchange_maint_audit_events (
  id bigint generated always as identity primary key,
  actor_id text not null,
  action text not null,
  target_type text not null,
  target_id text not null,
  from_id text,
  to_id text,
  reason text,
  request_id text,
  metadata jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now()
);

create table if not exists public.exchange_maint_jobs (
  id text primary key,
  job_type text not null check (
    job_type in ('discover', 'fetch', 'extract', 'validate', 'reconcile', 'recheck_health', 'reprocess')
  ),
  resource_id text references public.exchange_maint_source_resources(id) on delete cascade,
  snapshot_id text references public.exchange_maint_snapshots(id) on delete cascade,
  entity_scope text,
  payload jsonb not null default '{}'::jsonb,
  dedupe_key text not null,
  status text not null default 'queued' check (
    status in ('queued', 'leased', 'succeeded', 'retry_wait', 'dead_letter', 'cancelled')
  ),
  priority integer not null default 100,
  scheduled_at timestamptz not null default now(),
  attempts integer not null default 0 check (attempts >= 0),
  max_attempts integer not null default 5 check (max_attempts >= 1),
  lease_until timestamptz,
  lease_token bigint not null default 0 check (lease_token >= 0),
  worker_id text,
  error_class text,
  error_detail text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists public.exchange_maint_job_effects (
  effect_key text primary key,
  job_id text not null references public.exchange_maint_jobs(id) on delete cascade,
  lease_token bigint not null,
  result_id text not null,
  result_payload jsonb not null default '{}'::jsonb,
  committed_at timestamptz not null default now()
);

create table if not exists public.exchange_maint_usage_daily (
  usage_date date not null,
  source_id text not null,
  step text not null,
  requests_count bigint not null default 0,
  bytes_count bigint not null default 0,
  ocr_pages bigint not null default 0,
  model_tokens bigint not null default 0,
  execution_seconds numeric(12, 3) not null default 0,
  estimated_cost_twd numeric(12, 4) not null default 0,
  primary key (usage_date, source_id, step)
);

create table if not exists public.exchange_maint_experiences (
  id text primary key,
  home_id text references public.exchange_maint_institutions(id) on delete set null,
  host_id text not null references public.exchange_maint_institutions(id) on delete cascade,
  campus_id text references public.exchange_maint_campuses(id) on delete set null,
  author_display_mode text not null check (author_display_mode in ('anonymous', 'nickname', 'real_name')),
  author_display_name text not null,
  student_role text not null check (student_role in ('exchange_student', 'local_degree_student', 'international_degree_student', 'other')),
  experience_period text not null,
  experience_year integer not null,
  topics jsonb not null default '[]'::jsonb,
  consent_status text not null check (consent_status in ('active', 'withdrawn', 'expired')),
  current_revision_id text,
  created_at timestamptz not null default now()
);

create table if not exists public.exchange_maint_experience_revisions (
  id text primary key,
  experience_id text not null references public.exchange_maint_experiences(id) on delete cascade,
  summary_zh text not null,
  cost_data jsonb,
  source_url text,
  is_ai_summary boolean not null default false,
  is_translated boolean not null default false,
  review_status text not null default 'pending' check (review_status in ('pending', 'approved', 'rejected', 'suppressed')),
  consent_version text not null,
  created_at timestamptz not null default now()
);

create table if not exists public.exchange_maint_consent_records (
  id text primary key,
  experience_id text not null references public.exchange_maint_experiences(id) on delete cascade,
  contact_email_hmac text,
  public_scope text not null,
  allow_summary boolean not null default true,
  allow_translation boolean not null default true,
  consent_text_version text not null,
  consented_at timestamptz not null default now(),
  withdrawn_at timestamptz
);

create table if not exists public.exchange_maint_reports (
  id text primary key,
  report_kind text not null check (report_kind in ('stale_or_error', 'experience_submission', 'withdrawal_request')),
  target_entity_type text not null,
  target_entity_id text not null,
  published_release_id text,
  published_revision_id text,
  category text not null,
  reason_text text not null,
  evidence_url text,
  status text not null default 'pending' check (status in ('pending', 'triaged', 'resolved', 'dismissed')),
  created_at timestamptz not null default now(),
  resolved_at timestamptz
);

create index if not exists exchange_maint_jobs_claim_idx
  on public.exchange_maint_jobs (status, priority desc, scheduled_at asc);

create index if not exists exchange_maint_jobs_dedupe_idx
  on public.exchange_maint_jobs (dedupe_key, status);

create index if not exists exchange_maint_change_sets_queue_idx
  on public.exchange_maint_change_sets (status, risk, created_at desc);

create index if not exists exchange_maint_offerings_lookup_idx
  on public.exchange_maint_offerings (home_id, cycle_id, host_id);

-- Atomic lease claim with FOR UPDATE SKIP LOCKED and fencing token increment
create or replace function public.exchange_maint_claim_next_job(
  p_worker_id text,
  p_lease_seconds integer default 120
) returns jsonb
language plpgsql
set search_path = ''
as $$
declare
  v_job public.exchange_maint_jobs%rowtype;
begin
  if coalesce(btrim(p_worker_id), '') = '' or p_lease_seconds is null or p_lease_seconds < 10 then
    raise exception using errcode = '22023', message = 'Invalid worker_id or lease_seconds';
  end if;

  update public.exchange_maint_jobs
     set status = 'queued',
         worker_id = null,
         lease_until = null,
         updated_at = now()
   where status in ('leased', 'retry_wait')
     and lease_until is not null
     and lease_until <= now();

  select *
    into v_job
    from public.exchange_maint_jobs
   where status = 'queued'
     and scheduled_at <= now()
   order by priority desc, scheduled_at asc, id asc
   for update skip locked
   limit 1;

  if not found then
    return null;
  end if;

  update public.exchange_maint_jobs
     set status = 'leased',
         worker_id = p_worker_id,
         lease_token = v_job.lease_token + 1,
         lease_until = now() + make_interval(secs => p_lease_seconds),
         attempts = v_job.attempts + 1,
         updated_at = now()
   where id = v_job.id
   returning * into v_job;

  return to_jsonb(v_job);
end;
$$;

-- Lease heartbeat validating worker_id, fencing token, and DB-clock expiration
create or replace function public.exchange_maint_heartbeat_job(
  p_job_id text,
  p_worker_id text,
  p_lease_token bigint,
  p_lease_seconds integer default 120
) returns jsonb
language plpgsql
set search_path = ''
as $$
declare
  v_job public.exchange_maint_jobs%rowtype;
begin
  update public.exchange_maint_jobs
     set lease_until = now() + make_interval(secs => p_lease_seconds),
         updated_at = now()
   where id = p_job_id
     and status = 'leased'
     and worker_id = p_worker_id
     and lease_token = p_lease_token
     and lease_until > now()
   returning * into v_job;

  if not found then
    raise exception using errcode = '40001', message = 'Job lease expired or fencing token superseded';
  end if;

  return to_jsonb(v_job);
end;
$$;

-- Idempotent job completion guarded by fencing token and DB-clock expiration
create or replace function public.exchange_maint_complete_job(
  p_job_id text,
  p_worker_id text,
  p_lease_token bigint,
  p_effect_key text,
  p_result_id text,
  p_result_payload jsonb default '{}'::jsonb
) returns jsonb
language plpgsql
set search_path = ''
as $$
declare
  v_existing public.exchange_maint_job_effects%rowtype;
  v_job public.exchange_maint_jobs%rowtype;
begin
  select *
    into v_existing
    from public.exchange_maint_job_effects
   where effect_key = p_effect_key;

  if found then
    return jsonb_build_object(
      'idempotent_replay', true,
      'effect_key', v_existing.effect_key,
      'result_id', v_existing.result_id,
      'result_payload', v_existing.result_payload
    );
  end if;

  select *
    into v_job
    from public.exchange_maint_jobs
   where id = p_job_id
   for update;

  if not found
     or v_job.status <> 'leased'
     or v_job.worker_id <> p_worker_id
     or v_job.lease_token <> p_lease_token
     or v_job.lease_until is null
     or v_job.lease_until <= now() then
    raise exception using errcode = '40001', message = 'Stale lease token or expired lease rejected';
  end if;

  insert into public.exchange_maint_job_effects (
    effect_key, job_id, lease_token, result_id, result_payload, committed_at
  ) values (
    p_effect_key, p_job_id, p_lease_token, p_result_id, coalesce(p_result_payload, '{}'::jsonb), now()
  );

  update public.exchange_maint_jobs
     set status = 'succeeded',
         lease_until = null,
         updated_at = now()
   where id = p_job_id;

  return jsonb_build_object(
    'idempotent_replay', false,
    'effect_key', p_effect_key,
    'result_id', p_result_id,
    'result_payload', coalesce(p_result_payload, '{}'::jsonb)
  );
end;
$$;

-- Enable RLS and lock down direct PostgREST table access on all new tables
alter table public.exchange_maint_institutions enable row level security;
alter table public.exchange_maint_institution_aliases enable row level security;
alter table public.exchange_maint_campuses enable row level security;
alter table public.exchange_maint_academic_units enable row level security;
alter table public.exchange_maint_programs enable row level security;
alter table public.exchange_maint_cycles enable row level security;
alter table public.exchange_maint_offerings enable row level security;
alter table public.exchange_maint_offering_scopes enable row level security;
alter table public.exchange_maint_sources enable row level security;
alter table public.exchange_maint_source_resources enable row level security;
alter table public.exchange_maint_content_blobs enable row level security;
alter table public.exchange_maint_snapshots enable row level security;
alter table public.exchange_maint_fetch_attempts enable row level security;
alter table public.exchange_maint_source_links enable row level security;
alter table public.exchange_maint_extraction_runs enable row level security;
alter table public.exchange_maint_evidence enable row level security;
alter table public.exchange_maint_field_assertions enable row level security;
alter table public.exchange_maint_change_sets enable row level security;
alter table public.exchange_maint_change_items enable row level security;
alter table public.exchange_maint_review_decisions enable row level security;
alter table public.exchange_maint_entity_revisions enable row level security;
alter table public.exchange_maint_releases enable row level security;
alter table public.exchange_maint_release_members enable row level security;
alter table public.exchange_maint_publication_head enable row level security;
alter table public.exchange_maint_suppressions enable row level security;
alter table public.exchange_maint_audit_events enable row level security;
alter table public.exchange_maint_jobs enable row level security;
alter table public.exchange_maint_job_effects enable row level security;
alter table public.exchange_maint_usage_daily enable row level security;
alter table public.exchange_maint_experiences enable row level security;
alter table public.exchange_maint_experience_revisions enable row level security;
alter table public.exchange_maint_consent_records enable row level security;
alter table public.exchange_maint_reports enable row level security;

revoke all on table public.exchange_maint_institutions from anon, authenticated;
revoke all on table public.exchange_maint_institution_aliases from anon, authenticated;
revoke all on table public.exchange_maint_campuses from anon, authenticated;
revoke all on table public.exchange_maint_academic_units from anon, authenticated;
revoke all on table public.exchange_maint_programs from anon, authenticated;
revoke all on table public.exchange_maint_cycles from anon, authenticated;
revoke all on table public.exchange_maint_offerings from anon, authenticated;
revoke all on table public.exchange_maint_offering_scopes from anon, authenticated;
revoke all on table public.exchange_maint_sources from anon, authenticated;
revoke all on table public.exchange_maint_source_resources from anon, authenticated;
revoke all on table public.exchange_maint_content_blobs from anon, authenticated;
revoke all on table public.exchange_maint_snapshots from anon, authenticated;
revoke all on table public.exchange_maint_fetch_attempts from anon, authenticated;
revoke all on table public.exchange_maint_source_links from anon, authenticated;
revoke all on table public.exchange_maint_extraction_runs from anon, authenticated;
revoke all on table public.exchange_maint_evidence from anon, authenticated;
revoke all on table public.exchange_maint_field_assertions from anon, authenticated;
revoke all on table public.exchange_maint_change_sets from anon, authenticated;
revoke all on table public.exchange_maint_change_items from anon, authenticated;
revoke all on table public.exchange_maint_review_decisions from anon, authenticated;
revoke all on table public.exchange_maint_entity_revisions from anon, authenticated;
revoke all on table public.exchange_maint_releases from anon, authenticated;
revoke all on table public.exchange_maint_release_members from anon, authenticated;
revoke all on table public.exchange_maint_publication_head from anon, authenticated;
revoke all on table public.exchange_maint_suppressions from anon, authenticated;
revoke all on table public.exchange_maint_audit_events from anon, authenticated;
revoke all on table public.exchange_maint_jobs from anon, authenticated;
revoke all on table public.exchange_maint_job_effects from anon, authenticated;
revoke all on table public.exchange_maint_usage_daily from anon, authenticated;
revoke all on table public.exchange_maint_experiences from anon, authenticated;
revoke all on table public.exchange_maint_experience_revisions from anon, authenticated;
revoke all on table public.exchange_maint_consent_records from anon, authenticated;
revoke all on table public.exchange_maint_reports from anon, authenticated;

grant select, insert, update, delete on table public.exchange_maint_institutions to service_role;
grant select, insert, update, delete on table public.exchange_maint_institution_aliases to service_role;
grant select, insert, update, delete on table public.exchange_maint_campuses to service_role;
grant select, insert, update, delete on table public.exchange_maint_academic_units to service_role;
grant select, insert, update, delete on table public.exchange_maint_programs to service_role;
grant select, insert, update, delete on table public.exchange_maint_cycles to service_role;
grant select, insert, update, delete on table public.exchange_maint_offerings to service_role;
grant select, insert, update, delete on table public.exchange_maint_offering_scopes to service_role;
grant select, insert, update, delete on table public.exchange_maint_sources to service_role;
grant select, insert, update, delete on table public.exchange_maint_source_resources to service_role;
grant select, insert, update, delete on table public.exchange_maint_content_blobs to service_role;
grant select, insert, update, delete on table public.exchange_maint_snapshots to service_role;
grant select, insert, update, delete on table public.exchange_maint_fetch_attempts to service_role;
grant select, insert, update, delete on table public.exchange_maint_source_links to service_role;
grant select, insert, update, delete on table public.exchange_maint_extraction_runs to service_role;
grant select, insert, update, delete on table public.exchange_maint_evidence to service_role;
grant select, insert, update, delete on table public.exchange_maint_field_assertions to service_role;
grant select, insert, update, delete on table public.exchange_maint_change_sets to service_role;
grant select, insert, update, delete on table public.exchange_maint_change_items to service_role;
grant select, insert, update, delete on table public.exchange_maint_review_decisions to service_role;
grant select, insert, update, delete on table public.exchange_maint_entity_revisions to service_role;
grant select, insert, update, delete on table public.exchange_maint_releases to service_role;
grant select, insert, update, delete on table public.exchange_maint_release_members to service_role;
grant select, insert, update, delete on table public.exchange_maint_publication_head to service_role;
grant select, insert, update, delete on table public.exchange_maint_suppressions to service_role;
grant select, insert, update, delete on table public.exchange_maint_audit_events to service_role;
grant select, insert, update, delete on table public.exchange_maint_jobs to service_role;
grant select, insert, update, delete on table public.exchange_maint_job_effects to service_role;
grant select, insert, update, delete on table public.exchange_maint_usage_daily to service_role;
grant select, insert, update, delete on table public.exchange_maint_experiences to service_role;
grant select, insert, update, delete on table public.exchange_maint_experience_revisions to service_role;
grant select, insert, update, delete on table public.exchange_maint_consent_records to service_role;
grant select, insert, update, delete on table public.exchange_maint_reports to service_role;

revoke all on sequence public.exchange_maint_audit_events_id_seq from anon, authenticated;
grant usage, select on sequence public.exchange_maint_audit_events_id_seq to service_role;

revoke all on function public.exchange_maint_claim_next_job(text, integer) from public, anon, authenticated;
grant execute on function public.exchange_maint_claim_next_job(text, integer) to service_role;

revoke all on function public.exchange_maint_heartbeat_job(text, text, bigint, integer) from public, anon, authenticated;
grant execute on function public.exchange_maint_heartbeat_job(text, text, bigint, integer) to service_role;

revoke all on function public.exchange_maint_complete_job(text, text, bigint, text, text, jsonb) from public, anon, authenticated;
grant execute on function public.exchange_maint_complete_job(text, text, bigint, text, text, jsonb) to service_role;
