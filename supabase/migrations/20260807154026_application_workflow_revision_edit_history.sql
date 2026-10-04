alter table public.application_workflow_revisions
  add column if not exists edit_history jsonb not null default '[]'::jsonb
    check (jsonb_typeof(edit_history) = 'array');

comment on column public.application_workflow_revisions.edit_history is
  'Append-only FastAPI audit records for pending revision edits; approvals reset after every content change.';

-- Existing RLS and service-role-only grants remain unchanged. The Web client
-- reaches this data only through the protected FastAPI content-admin API.
