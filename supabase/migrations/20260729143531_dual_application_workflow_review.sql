alter table public.application_workflow_revisions
  add column if not exists required_review_count smallint not null default 2
    check (required_review_count >= 2 and required_review_count <= 10),
  add column if not exists review_approvals jsonb not null default '[]'::jsonb
    check (jsonb_typeof(review_approvals) = 'array');

comment on column public.application_workflow_revisions.required_review_count is
  'Minimum number of independent content-admin approvals required before publication.';

comment on column public.application_workflow_revisions.review_approvals is
  'Reviewer sign-offs captured by FastAPI; reviewer IDs must be unique per revision.';

-- FastAPI remains the only write path. Existing RLS and service-role-only grants
-- from 202607280002_application_content_governance.sql continue to apply.
