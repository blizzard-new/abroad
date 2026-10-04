create table if not exists public.destination_profile_promotion_events (
    id text primary key,
    profile_key text not null,
    source_profile_content_hash text not null check (
        source_profile_content_hash ~ '^[0-9a-f]{64}$'
    ),
    promoted_profile_content_hash text not null check (
        promoted_profile_content_hash ~ '^[0-9a-f]{64}$'
    ),
    promoted_by_id text not null,
    promoted_at timestamptz not null,
    event_payload jsonb not null,
    unique (profile_key, source_profile_content_hash)
);

create index if not exists destination_profile_promotion_events_profile_idx
    on public.destination_profile_promotion_events (
        profile_key,
        promoted_at desc
    );

alter table public.destination_profile_promotion_events enable row level security;

revoke all on table public.destination_profile_promotion_events from anon, authenticated;
grant select, insert on table public.destination_profile_promotion_events to service_role;

comment on table public.destination_profile_promotion_events is
    'Append-only, backend-only destination profile promotions pinned to two current human approvals.';
