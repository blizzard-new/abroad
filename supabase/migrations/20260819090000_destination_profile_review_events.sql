create table if not exists public.destination_profile_review_events (
    id uuid primary key,
    profile_key text not null,
    profile_content_hash text not null
        check (profile_content_hash ~ '^[0-9a-f]{64}$'),
    reviewer_id text not null,
    decision text not null
        check (decision in ('approve', 'changes_required')),
    reviewed_at timestamptz not null,
    event_payload jsonb not null
        check (jsonb_typeof(event_payload) = 'object'),
    created_at timestamptz not null default now()
);

create index if not exists destination_profile_review_events_profile_idx
    on public.destination_profile_review_events (
        profile_key,
        profile_content_hash,
        reviewed_at
    );

create index if not exists destination_profile_review_events_reviewer_idx
    on public.destination_profile_review_events (reviewer_id, reviewed_at);

alter table public.destination_profile_review_events enable row level security;

revoke all on table public.destination_profile_review_events from anon, authenticated;
grant select, insert on table public.destination_profile_review_events to service_role;

comment on table public.destination_profile_review_events is
    'Append-only, backend-only evidence for independent destination profile review. Events never publish or mutate student-visible profiles.';
