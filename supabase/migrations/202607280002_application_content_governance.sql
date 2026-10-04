create table if not exists public.application_workflows (
  workflow_key text primary key,
  home_university text not null,
  partner_university text not null,
  program_type text,
  academic_year text,
  application_round text,
  published_version integer check (published_version is null or published_version >= 1),
  published_payload jsonb,
  published_at timestamptz,
  current_revision_id text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists public.application_workflow_revisions (
  id text primary key,
  workflow_key text not null references public.application_workflows(workflow_key) on delete cascade,
  version integer not null check (version >= 1),
  base_version integer check (base_version is null or base_version >= 1),
  status text not null check (
    status in ('legacy', 'draft', 'pending_review', 'published', 'rejected', 'superseded')
  ),
  content_hash text not null,
  change_summary jsonb not null default '[]'::jsonb,
  workflow_payload jsonb not null,
  detected_by text not null default 'automated_refresh',
  detected_at timestamptz not null default now(),
  reviewed_by text,
  reviewed_at timestamptz,
  review_note text,
  unique (workflow_key, version)
);

create table if not exists public.application_workflow_audit_log (
  id bigint generated always as identity primary key,
  workflow_key text not null references public.application_workflows(workflow_key) on delete cascade,
  revision_id text references public.application_workflow_revisions(id) on delete set null,
  action text not null check (
    action in ('detected', 'submitted', 'published', 'rejected', 'superseded', 'rolled_back')
  ),
  actor_id text,
  note text,
  metadata jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now()
);

create index if not exists application_workflows_home_partner_idx
  on public.application_workflows (home_university, partner_university);

create index if not exists application_workflow_revisions_status_idx
  on public.application_workflow_revisions (status, detected_at desc);

create index if not exists application_workflow_revisions_workflow_idx
  on public.application_workflow_revisions (workflow_key, version desc);

alter table public.application_workflows enable row level security;
alter table public.application_workflow_revisions enable row level security;
alter table public.application_workflow_audit_log enable row level security;

revoke all on table public.application_workflows from anon, authenticated;
revoke all on table public.application_workflow_revisions from anon, authenticated;
revoke all on table public.application_workflow_audit_log from anon, authenticated;

grant select, insert, update, delete on table public.application_workflows to service_role;
grant select, insert, update, delete on table public.application_workflow_revisions to service_role;
grant select, insert, update, delete on table public.application_workflow_audit_log to service_role;

revoke all on sequence public.application_workflow_audit_log_id_seq from anon, authenticated;
grant usage, select on sequence public.application_workflow_audit_log_id_seq to service_role;

-- FastAPI is the only data path; never expose a secret/service-role key to Web or Flutter.
