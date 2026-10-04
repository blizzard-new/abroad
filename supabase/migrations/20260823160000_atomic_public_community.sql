-- Public community persistence and mutations.
--
-- The FastAPI service remains the only client-facing access path.  All public
-- community mutations are short SECURITY DEFINER transactions with the same
-- lock order: account, identity, parent resource, child resource.  Tables are
-- private to PostgREST roles and service_role receives read-only table access;
-- writes are available only through the RPCs defined below.

create table public.exchange_community_identities (
  id text primary key,
  -- NULL preserves the legacy anonymous-identity creation contract.  Such an
  -- identity can authenticate only itself; every publication RPC separately
  -- requires an exact non-NULL account binding under lock.
  account_id text unique
    references public.exchange_accounts(id) on delete cascade,
  display_name text not null,
  access_token_hash text not null unique,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  constraint exchange_community_identities_id_nonempty
    check (btrim(id) <> '' and char_length(id) <= 128),
  constraint exchange_community_identities_display_name_length
    check (char_length(btrim(display_name)) between 2 and 30),
  constraint exchange_community_identities_token_hash_shape
    check (access_token_hash ~ '^[0-9a-f]{64}$'),
  constraint exchange_community_identities_timestamp_order
    check (updated_at >= created_at)
);

create table public.exchange_community_questions (
  id text primary key,
  author_identity_id text
    references public.exchange_community_identities(id) on delete set null,
  school_name text not null,
  home_university text not null,
  topic text not null,
  title text not null,
  body text not null,
  display_name text not null,
  identity_mode text not null,
  status text not null default 'pending',
  revision bigint not null default 0,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  constraint exchange_community_questions_id_nonempty
    check (btrim(id) <> '' and char_length(id) <= 128),
  constraint exchange_community_questions_school_length
    check (char_length(btrim(school_name)) between 2 and 200),
  constraint exchange_community_questions_home_length
    check (char_length(btrim(home_university)) between 2 and 80),
  constraint exchange_community_questions_topic
    check (topic in (
      'application', 'housing', 'academics', 'life', 'pre_departure',
      'scholarship', 'visa', 'cost', 'career', 'warning'
    )),
  constraint exchange_community_questions_title_length
    check (char_length(btrim(title)) between 4 and 120),
  constraint exchange_community_questions_body_length
    check (char_length(btrim(body)) between 10 and 1000),
  constraint exchange_community_questions_display_name_length
    check (char_length(btrim(display_name)) between 2 and 80),
  constraint exchange_community_questions_identity_mode
    check (identity_mode in (
      'anonymous', 'real_name', 'verified_school', 'verified_department'
    )),
  constraint exchange_community_questions_status
    check (status in ('pending', 'approved', 'hidden')),
  constraint exchange_community_questions_revision_nonnegative
    check (revision >= 0),
  constraint exchange_community_questions_timestamp_order
    check (updated_at >= created_at)
);

create table public.exchange_community_answers (
  id text primary key,
  question_id text not null
    references public.exchange_community_questions(id) on delete cascade,
  author_identity_id text
    references public.exchange_community_identities(id) on delete set null,
  body text not null,
  display_name text not null,
  identity_mode text not null,
  exchange_year text,
  verified_experience boolean not null default false,
  status text not null default 'pending',
  revision bigint not null default 0,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  constraint exchange_community_answers_id_nonempty
    check (btrim(id) <> '' and char_length(id) <= 128),
  constraint exchange_community_answers_body_length
    check (char_length(btrim(body)) between 10 and 1500),
  constraint exchange_community_answers_display_name_length
    check (char_length(btrim(display_name)) between 2 and 80),
  constraint exchange_community_answers_identity_mode
    check (identity_mode in (
      'anonymous', 'real_name', 'verified_school', 'verified_department'
    )),
  constraint exchange_community_answers_exchange_year_length
    check (exchange_year is null or char_length(btrim(exchange_year)) <= 20),
  constraint exchange_community_answers_status
    check (status in ('pending', 'approved', 'hidden')),
  constraint exchange_community_answers_revision_nonnegative
    check (revision >= 0),
  constraint exchange_community_answers_timestamp_order
    check (updated_at >= created_at)
);

create table public.exchange_community_posts (
  id text primary key,
  author_identity_id text
    references public.exchange_community_identities(id) on delete set null,
  board_id text not null,
  board_kind text not null,
  school_name text not null,
  display_name text not null,
  identity_mode text not null,
  post_type text not null default 'discussion',
  topic text not null default 'application',
  country text,
  academic_year text,
  application_stage text,
  title text not null,
  body text not null,
  status text not null default 'approved',
  revision bigint not null default 0,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  constraint exchange_community_posts_id_nonempty
    check (btrim(id) <> '' and char_length(id) <= 128),
  constraint exchange_community_posts_board_id_length
    check (char_length(btrim(board_id)) between 2 and 120),
  constraint exchange_community_posts_board_kind
    check (board_kind in (
      'public_study_abroad', 'public_topic', 'university_exchange'
    )),
  constraint exchange_community_posts_school_length
    check (char_length(btrim(school_name)) between 2 and 200),
  constraint exchange_community_posts_display_name_length
    check (char_length(btrim(display_name)) between 2 and 80),
  constraint exchange_community_posts_identity_mode
    check (identity_mode in (
      'anonymous', 'real_name', 'verified_school', 'verified_department'
    )),
  constraint exchange_community_posts_post_type
    check (post_type in ('discussion', 'question', 'experience')),
  constraint exchange_community_posts_topic
    check (topic in (
      'application', 'housing', 'academics', 'life', 'pre_departure',
      'scholarship', 'visa', 'cost', 'career', 'warning'
    )),
  constraint exchange_community_posts_country_length
    check (country is null or char_length(btrim(country)) <= 80),
  constraint exchange_community_posts_academic_year_length
    check (academic_year is null or char_length(btrim(academic_year)) <= 20),
  constraint exchange_community_posts_application_stage_length
    check (application_stage is null or char_length(btrim(application_stage)) <= 40),
  constraint exchange_community_posts_title_length
    check (char_length(btrim(title)) between 4 and 120),
  constraint exchange_community_posts_body_length
    check (char_length(btrim(body)) between 10 and 1600),
  constraint exchange_community_posts_status
    check (status in ('pending', 'approved', 'hidden')),
  constraint exchange_community_posts_revision_nonnegative
    check (revision >= 0),
  constraint exchange_community_posts_timestamp_order
    check (updated_at >= created_at)
);

create table public.exchange_community_post_comments (
  id text primary key,
  post_id text not null
    references public.exchange_community_posts(id) on delete cascade,
  author_identity_id text
    references public.exchange_community_identities(id) on delete set null,
  display_name text not null,
  identity_mode text not null,
  body text not null,
  status text not null default 'approved',
  revision bigint not null default 0,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  constraint exchange_community_post_comments_id_nonempty
    check (btrim(id) <> '' and char_length(id) <= 128),
  constraint exchange_community_post_comments_display_name_length
    check (char_length(btrim(display_name)) between 2 and 80),
  constraint exchange_community_post_comments_identity_mode
    check (identity_mode in (
      'anonymous', 'real_name', 'verified_school', 'verified_department'
    )),
  constraint exchange_community_post_comments_body_length
    check (char_length(btrim(body)) between 2 and 800),
  constraint exchange_community_post_comments_status
    check (status in ('pending', 'approved', 'hidden')),
  constraint exchange_community_post_comments_revision_nonnegative
    check (revision >= 0),
  constraint exchange_community_post_comments_timestamp_order
    check (updated_at >= created_at)
);

create table public.exchange_community_public_chat_messages (
  id text primary key,
  author_identity_id text
    references public.exchange_community_identities(id) on delete set null,
  school_name text not null,
  display_name text not null,
  identity_mode text not null,
  body text not null,
  status text not null default 'approved',
  revision bigint not null default 0,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  constraint exchange_community_public_chat_messages_id_nonempty
    check (btrim(id) <> '' and char_length(id) <= 128),
  constraint exchange_community_public_chat_messages_school_length
    check (char_length(btrim(school_name)) between 2 and 200),
  constraint exchange_community_public_chat_messages_display_name_length
    check (char_length(btrim(display_name)) between 2 and 80),
  constraint exchange_community_public_chat_messages_identity_mode
    check (identity_mode in (
      'anonymous', 'real_name', 'verified_school', 'verified_department'
    )),
  constraint exchange_community_public_chat_messages_body_length
    check (char_length(btrim(body)) between 2 and 500),
  constraint exchange_community_public_chat_messages_status
    check (status in ('pending', 'approved', 'hidden')),
  constraint exchange_community_public_chat_messages_revision_nonnegative
    check (revision >= 0),
  constraint exchange_community_public_chat_messages_timestamp_order
    check (updated_at >= created_at)
);

create table public.exchange_community_experience_submissions (
  id text primary key,
  author_identity_id text
    references public.exchange_community_identities(id) on delete set null,
  school_name text not null,
  home_university text not null,
  title text not null,
  summary text not null,
  exchange_year text not null,
  themes jsonb not null default '[]'::jsonb,
  source_url text,
  display_name text not null,
  identity_mode text not null,
  status text not null default 'pending',
  revision bigint not null default 0,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  constraint exchange_community_experience_submissions_id_nonempty
    check (btrim(id) <> '' and char_length(id) <= 128),
  constraint exchange_community_experience_submissions_school_length
    check (char_length(btrim(school_name)) between 2 and 200),
  constraint exchange_community_experience_submissions_home_length
    check (char_length(btrim(home_university)) between 2 and 80),
  constraint exchange_community_experience_submissions_title_length
    check (char_length(btrim(title)) between 4 and 120),
  constraint exchange_community_experience_submissions_summary_length
    check (char_length(btrim(summary)) between 20 and 2000),
  constraint exchange_community_experience_submissions_year_length
    check (char_length(btrim(exchange_year)) between 4 and 20),
  constraint exchange_community_experience_submissions_themes_array
    check (jsonb_typeof(themes) = 'array' and jsonb_array_length(themes) <= 8),
  constraint exchange_community_experience_submissions_source_url
    check (
      source_url is null
      or (char_length(source_url) <= 500 and source_url ~* '^https?://')
    ),
  constraint exchange_community_experience_submissions_display_name_length
    check (char_length(btrim(display_name)) between 2 and 80),
  constraint exchange_community_experience_submissions_identity_mode
    check (identity_mode in (
      'anonymous', 'real_name', 'verified_school', 'verified_department'
    )),
  constraint exchange_community_experience_submissions_status
    check (status in ('pending', 'approved', 'hidden')),
  constraint exchange_community_experience_submissions_revision_nonnegative
    check (revision >= 0),
  constraint exchange_community_experience_submissions_timestamp_order
    check (updated_at >= created_at)
);

create table public.exchange_community_publish_events (
  id text primary key,
  account_id text not null
    references public.exchange_accounts(id) on delete cascade,
  identity_id text not null
    references public.exchange_community_identities(id) on delete cascade,
  content_type text not null,
  occurred_at timestamptz not null default now(),
  constraint exchange_community_publish_events_id_nonempty
    check (btrim(id) <> '' and char_length(id) <= 128),
  constraint exchange_community_publish_events_content_type
    check (content_type in (
      'question', 'answer', 'post', 'comment', 'chat', 'experience'
    ))
);

create table public.exchange_community_moderation_audits (
  id text primary key,
  resource_type text not null,
  resource_id text not null,
  previous_status text not null,
  new_status text not null,
  moderator_id text
    references public.exchange_accounts(id) on delete set null,
  note text not null,
  request_fingerprint text not null,
  created_at timestamptz not null default now(),
  retained_until timestamptz not null,
  constraint exchange_community_moderation_audits_id_nonempty
    check (btrim(id) <> '' and char_length(id) <= 128),
  constraint exchange_community_moderation_audits_resource_type
    check (resource_type in (
      'question', 'answer', 'post', 'comment', 'chat', 'experience'
    )),
  constraint exchange_community_moderation_audits_resource_id_nonempty
    check (btrim(resource_id) <> '' and char_length(resource_id) <= 128),
  constraint exchange_community_moderation_audits_previous_status
    check (previous_status in ('pending', 'approved', 'hidden')),
  constraint exchange_community_moderation_audits_new_status
    check (new_status in ('approved', 'hidden')),
  constraint exchange_community_moderation_audits_changed
    check (previous_status <> new_status),
  constraint exchange_community_moderation_audits_note_length
    check (char_length(btrim(note)) between 2 and 500),
  constraint exchange_community_moderation_audits_fingerprint_shape
    check (request_fingerprint ~ '^[0-9a-f]{64}$'),
  constraint exchange_community_moderation_audits_retention
    check (retained_until = created_at + interval '2160 hours')
);

create table public.exchange_community_mutation_receipts (
  id text primary key,
  operation text not null,
  request_fingerprint text not null,
  actor_account_id text
    references public.exchange_accounts(id) on delete set null,
  actor_identity_id text
    references public.exchange_community_identities(id) on delete set null,
  resource_type text not null,
  resource_id text not null,
  response jsonb not null,
  created_at timestamptz not null default now(),
  retained_until timestamptz not null,
  constraint exchange_community_mutation_receipts_id_nonempty
    check (btrim(id) <> '' and char_length(id) <= 128),
  constraint exchange_community_mutation_receipts_operation_shape
    check (operation ~ '^(identity|legacy_identity|publish_(question|answer|post|comment|chat|experience)|delete_(post|comment)|moderate_(question|answer|post|comment|chat|experience)|anonymize_public_author)$'),
  constraint exchange_community_mutation_receipts_fingerprint_shape
    check (request_fingerprint ~ '^[0-9a-f]{64}$'),
  constraint exchange_community_mutation_receipts_resource_type_nonempty
    check (btrim(resource_type) <> '' and char_length(resource_type) <= 40),
  constraint exchange_community_mutation_receipts_resource_id_nonempty
    check (btrim(resource_id) <> '' and char_length(resource_id) <= 128),
  constraint exchange_community_mutation_receipts_response_object
    check (jsonb_typeof(response) = 'object'),
  constraint exchange_community_mutation_receipts_retention
    check (retained_until = created_at + interval '168 hours')
);

-- Every foreign key used for lookup, cascade, or SET NULL has a supporting
-- index.  Read paths use partial indexes matching the approved/pending filters.
create index exchange_community_questions_author_idx
  on public.exchange_community_questions (author_identity_id);
create index exchange_community_questions_approved_school_idx
  on public.exchange_community_questions (home_university, school_name, created_at desc)
  where status = 'approved';
create index exchange_community_questions_pending_idx
  on public.exchange_community_questions (created_at)
  where status = 'pending';

create index exchange_community_answers_question_idx
  on public.exchange_community_answers (question_id, created_at);
create index exchange_community_answers_author_idx
  on public.exchange_community_answers (author_identity_id);
create index exchange_community_answers_pending_idx
  on public.exchange_community_answers (created_at)
  where status = 'pending';

create index exchange_community_posts_author_idx
  on public.exchange_community_posts (author_identity_id);
create index exchange_community_posts_approved_board_idx
  on public.exchange_community_posts (board_id, created_at desc)
  where status = 'approved';
create index exchange_community_posts_approved_topic_idx
  on public.exchange_community_posts (topic, created_at desc)
  where status = 'approved';
create index exchange_community_posts_pending_idx
  on public.exchange_community_posts (created_at)
  where status = 'pending';

create index exchange_community_post_comments_post_idx
  on public.exchange_community_post_comments (post_id, created_at);
create index exchange_community_post_comments_author_idx
  on public.exchange_community_post_comments (author_identity_id);
create index exchange_community_post_comments_pending_idx
  on public.exchange_community_post_comments (created_at)
  where status = 'pending';

create index exchange_community_public_chat_messages_author_idx
  on public.exchange_community_public_chat_messages (author_identity_id);
create index exchange_community_public_chat_messages_approved_school_idx
  on public.exchange_community_public_chat_messages (school_name, created_at desc)
  where status = 'approved';
create index exchange_community_public_chat_messages_pending_idx
  on public.exchange_community_public_chat_messages (created_at)
  where status = 'pending';

create index exchange_community_experience_submissions_author_idx
  on public.exchange_community_experience_submissions (author_identity_id);
create index exchange_community_experience_submissions_approved_school_idx
  on public.exchange_community_experience_submissions (
    home_university,
    school_name,
    created_at desc
  ) where status = 'approved';
create index exchange_community_experience_submissions_pending_idx
  on public.exchange_community_experience_submissions (created_at)
  where status = 'pending';

create index exchange_community_publish_events_account_window_idx
  on public.exchange_community_publish_events (account_id, occurred_at desc);
create index exchange_community_publish_events_identity_idx
  on public.exchange_community_publish_events (identity_id, occurred_at desc);
create index exchange_community_publish_events_expiry_idx
  on public.exchange_community_publish_events (occurred_at);

create index exchange_community_moderation_audits_resource_idx
  on public.exchange_community_moderation_audits (
    resource_type,
    resource_id,
    created_at desc
  );
create index exchange_community_moderation_audits_moderator_idx
  on public.exchange_community_moderation_audits (moderator_id, created_at desc);
create index exchange_community_moderation_audits_retention_idx
  on public.exchange_community_moderation_audits (retained_until);

create index exchange_community_mutation_receipts_account_idx
  on public.exchange_community_mutation_receipts (actor_account_id, created_at desc);
create index exchange_community_mutation_receipts_identity_idx
  on public.exchange_community_mutation_receipts (actor_identity_id, created_at desc);
create index exchange_community_mutation_receipts_retention_idx
  on public.exchange_community_mutation_receipts (retained_until);

create or replace function public.exchange_normalize_community_school(p_value text)
returns text
language sql
immutable
strict
set search_path = public, pg_temp
as $$
  select lower(regexp_replace(btrim(p_value), '[[:space:]]+', ' ', 'g'));
$$;

create or replace function public.exchange_community_payload_has_only_keys(
  p_payload jsonb,
  p_allowed text[]
) returns boolean
language sql
immutable
set search_path = public, pg_temp
as $$
  select jsonb_typeof(p_payload) = 'object'
    and not exists (
      select 1
      from jsonb_object_keys(p_payload) as payload_key(key_name)
      where not (payload_key.key_name = any(p_allowed))
    );
$$;

create or replace function public.exchange_community_canonical_json(
  p_value jsonb
) returns text
language plpgsql
immutable
strict
set search_path = public, pg_temp
as $$
declare
  v_result text;
begin
  case jsonb_typeof(p_value)
    when 'object' then
      select '{' || coalesce(
        string_agg(
          to_jsonb(item.key_name)::text || ':'
            || public.exchange_community_canonical_json(item.item_value),
          ',' order by item.key_name
        ),
        ''
      ) || '}'
      into v_result
      from jsonb_each(p_value) as item(key_name, item_value);
    when 'array' then
      select '[' || coalesce(
        string_agg(
          public.exchange_community_canonical_json(item.item_value),
          ',' order by item.ordinality
        ),
        ''
      ) || ']'
      into v_result
      from jsonb_array_elements(p_value) with ordinality
        as item(item_value, ordinality);
    else
      v_result := p_value::text;
  end case;

  return v_result;
end;
$$;

create or replace function public.exchange_community_request_fingerprint(
  p_value jsonb
) returns text
language sql
immutable
strict
set search_path = public, pg_temp
as $$
  select encode(
    sha256(
      convert_to(public.exchange_community_canonical_json(p_value), 'UTF8')
    ),
    'hex'
  );
$$;

create or replace function public.exchange_community_replay(
  p_event_id text,
  p_operation text,
  p_request_fingerprint text
) returns jsonb
language plpgsql
security definer
set search_path = public, pg_temp
as $$
declare
  v_receipt public.exchange_community_mutation_receipts%rowtype;
begin
  select receipt.* into v_receipt
  from public.exchange_community_mutation_receipts receipt
  where receipt.id = p_event_id;

  if not found then
    return null;
  end if;

  if v_receipt.operation = p_operation
     and v_receipt.request_fingerprint = p_request_fingerprint then
    return v_receipt.response || jsonb_build_object('idempotent', true);
  end if;

  return jsonb_build_object('status', 'idempotency_conflict');
end;
$$;

create or replace function public.exchange_community_display_name(
  p_profile jsonb,
  p_identity_mode text,
  p_content_type text
) returns text
language plpgsql
stable
set search_path = public, pg_temp
as $$
declare
  v_school text := nullif(btrim(p_profile ->> 'verified_university'), '');
  v_department text := nullif(btrim(p_profile ->> 'verified_department'), '');
  v_real_name text := nullif(btrim(p_profile ->> 'display_name'), '');
  v_student_verified boolean := coalesce(
    p_profile -> 'student_status_verified' = 'true'::jsonb,
    false
  );
begin
  if p_identity_mode = 'anonymous' then
    return '匿名學生';
  end if;

  if p_identity_mode = 'real_name' then
    return v_real_name;
  end if;

  if p_identity_mode = 'verified_school' and v_student_verified and v_school is not null then
    return v_school || '學生';
  end if;

  if p_identity_mode = 'verified_department'
     and v_student_verified
     and v_school is not null
     and v_department is not null then
    return v_school || ' ' || v_department;
  end if;

  return null;
end;
$$;

create or replace function public.exchange_enforce_community_moderation_audit_append_only()
returns trigger
language plpgsql
security definer
set search_path = public, pg_temp
as $$
begin
  if tg_op = 'UPDATE' then
    -- Preserve the audit when its moderator account is deleted.  This is the
    -- only FK-driven mutation tolerated by the append-only guard.
    if (to_jsonb(new) - 'moderator_id') = (to_jsonb(old) - 'moderator_id')
       and old.moderator_id is not null
       and new.moderator_id is null then
      return new;
    end if;

    raise exception 'community moderation audits are append-only'
      using errcode = '42501';
  end if;

  if tg_op = 'DELETE'
     and coalesce(
       current_setting('exchange.community_moderation_audit_purge', true),
       'off'
     ) <> 'on' then
    raise exception 'community moderation audits may only be deleted after retention'
      using errcode = '42501';
  end if;

  return old;
end;
$$;

create trigger exchange_enforce_community_moderation_audit_append_only_trigger
before update or delete on public.exchange_community_moderation_audits
for each row execute function public.exchange_enforce_community_moderation_audit_append_only();

-- The .104 suspension mutation locked both account rows but treated the
-- supplied identity id as opaque text.  Once identities are relational, every
-- new suspension audit must lock that identity after the accounts and prove it
-- is linked to the target.  Legacy unlinked identities can never be suspended
-- through an arbitrary account id.
create or replace function public.exchange_validate_community_suspension_identity_binding()
returns trigger
language plpgsql
security definer
set search_path = public, pg_temp
as $$
declare
  v_bound_account_id text;
begin
  select identity.account_id into v_bound_account_id
  from public.exchange_community_identities identity
  where identity.id = new.identity_id
  for update;

  if not found
     or v_bound_account_id is distinct from new.target_account_id then
    raise exception 'community suspension identity does not match target account'
      using errcode = '23514';
  end if;

  return new;
end;
$$;

create trigger exchange_validate_community_suspension_identity_binding_trigger
before insert on public.exchange_community_suspension_audits
for each row execute function
  public.exchange_validate_community_suspension_identity_binding();

-- Forward declarations let the adapter-facing functions below resolve their
-- owner-only implementation calls during migration validation.  Full bodies
-- replace these declarations later without changing signatures or ACLs.
create or replace function public.exchange_commit_community_identity(
  p_event_id text,
  p_identity_id text,
  p_account_id text,
  p_access_token_hash text
) returns jsonb
language plpgsql
security definer
set search_path = public, pg_temp
as $$
begin
  raise exception 'community identity implementation not initialized'
    using errcode = '55000';
end;
$$;

create or replace function public.exchange_commit_public_community_content(
  p_event_id text,
  p_content_id text,
  p_content_type text,
  p_account_id text,
  p_identity_id text,
  p_access_token_hash text,
  p_payload jsonb
) returns jsonb
language plpgsql
security definer
set search_path = public, pg_temp
as $$
begin
  raise exception 'community publication implementation not initialized'
    using errcode = '55000';
end;
$$;

create or replace function public.exchange_delete_public_community_content(
  p_event_id text,
  p_content_type text,
  p_content_id text,
  p_account_id text,
  p_identity_id text,
  p_access_token_hash text,
  p_expected_revision bigint
) returns jsonb
language plpgsql
security definer
set search_path = public, pg_temp
as $$
begin
  raise exception 'community delete implementation not initialized'
    using errcode = '55000';
end;
$$;

create or replace function public.exchange_commit_community_identity(
  p_event_id text,
  p_identity_id text,
  p_account_id text,
  p_access_token_hash text
) returns jsonb
language plpgsql
security definer
set search_path = public, pg_temp
as $$
declare
  v_event_id text := nullif(btrim(p_event_id), '');
  v_identity_id text := nullif(btrim(p_identity_id), '');
  v_account_id text := nullif(btrim(p_account_id), '');
  v_token_hash text := nullif(btrim(p_access_token_hash), '');
  v_operation constant text := 'identity';
  v_fingerprint text;
  v_replay jsonb;
  v_now timestamptz;
  v_display_name text;
  v_account public.exchange_accounts%rowtype;
  v_identity public.exchange_community_identities%rowtype;
  v_identity_exists boolean := false;
  v_response jsonb;
begin
  if v_event_id is null
     or char_length(v_event_id) > 128
     or v_identity_id is null
     or char_length(v_identity_id) > 128
     or v_account_id is null
     or char_length(v_account_id) > 128
     or v_token_hash is null
     or v_token_hash !~ '^[0-9a-f]{64}$' then
    return jsonb_build_object('status', 'invalid_request');
  end if;

  v_fingerprint := public.exchange_community_request_fingerprint(
    jsonb_build_array(
      v_operation,
      v_identity_id,
      v_account_id,
      v_token_hash
    )
  );

  -- Response-lost retries are decided before any clock-dependent work.
  v_replay := public.exchange_community_replay(
    v_event_id,
    v_operation,
    v_fingerprint
  );
  if v_replay is not null then
    return v_replay;
  end if;

  -- Canonical public-community lock order starts with the account.
  select account.* into v_account
  from public.exchange_accounts account
  where account.id = v_account_id
  for update;

  if not found then
    return jsonb_build_object('status', 'account_missing');
  end if;

  -- A same-event request may have committed while this call waited for the
  -- account lock, so repeat the idempotency decision under the lock.
  v_replay := public.exchange_community_replay(
    v_event_id,
    v_operation,
    v_fingerprint
  );
  if v_replay is not null then
    return v_replay;
  end if;

  v_display_name := nullif(btrim(v_account.profile ->> 'display_name'), '');
  if v_display_name is null or char_length(v_display_name) > 30 then
    return jsonb_build_object('status', 'integrity_conflict');
  end if;

  -- Account lock serializes the absent-row case; the identity row is always
  -- the second lock when it already exists.
  select identity.* into v_identity
  from public.exchange_community_identities identity
  where identity.account_id = v_account_id
  for update;
  v_identity_exists := found;
  v_now := clock_timestamp();

  begin
    if v_identity_exists then
      update public.exchange_community_identities identity
      set display_name = v_display_name,
          access_token_hash = v_token_hash,
          updated_at = v_now
      where identity.id = v_identity.id
      returning * into v_identity;
    else
      insert into public.exchange_community_identities (
        id,
        account_id,
        display_name,
        access_token_hash,
        created_at,
        updated_at
      ) values (
        v_identity_id,
        v_account_id,
        v_display_name,
        v_token_hash,
        v_now,
        v_now
      )
      returning * into v_identity;
    end if;

    v_response := jsonb_build_object(
      'status', 'committed',
      'idempotent', false,
      'identity', to_jsonb(v_identity) - 'access_token_hash'
    );

    insert into public.exchange_community_mutation_receipts (
      id,
      operation,
      request_fingerprint,
      actor_account_id,
      actor_identity_id,
      resource_type,
      resource_id,
      response,
      created_at,
      retained_until
    ) values (
      v_event_id,
      v_operation,
      v_fingerprint,
      v_account_id,
      v_identity.id,
      'identity',
      v_identity.id,
      v_response,
      v_now,
      v_now + interval '168 hours'
    );
  exception
    when integrity_constraint_violation or data_exception then
      -- If another account reused this event id, the subtransaction rolls back
      -- the token rotation before classifying the winning receipt.
      v_replay := public.exchange_community_replay(
        v_event_id,
        v_operation,
        v_fingerprint
      );
      if v_replay is not null then
        return v_replay;
      end if;
      return jsonb_build_object('status', 'integrity_conflict');
  end;

  return v_response;
end;
$$;

-- Adapter-facing publication RPC.  It accepts the canonical full model,
-- derives the resource id from content.id, strips server-owned projection
-- fields, and delegates the locked insert to the mutation above.  The caller's
-- hash is never trusted: PostgreSQL rebuilds the exact request envelope first.
create or replace function public.exchange_commit_public_community_publication(
  p_mutation_id text,
  p_request_fingerprint text,
  p_account_id text,
  p_identity_id text,
  p_access_token_hash text,
  p_resource_type text,
  p_content jsonb
) returns jsonb
language plpgsql
security definer
set search_path = public, pg_temp
as $$
declare
  v_mutation_id text := nullif(btrim(p_mutation_id), '');
  v_supplied_fingerprint text := nullif(btrim(p_request_fingerprint), '');
  v_account_id text := nullif(btrim(p_account_id), '');
  v_identity_id text := nullif(btrim(p_identity_id), '');
  v_token_hash text := lower(nullif(btrim(p_access_token_hash), ''));
  v_resource_type text := nullif(btrim(p_resource_type), '');
  v_resource_id text := nullif(btrim(p_content ->> 'id'), '');
  v_operation text;
  v_fingerprint text;
  v_internal_fingerprint text;
  v_payload jsonb;
  v_semantic_content jsonb;
  v_replay jsonb;
  v_account public.exchange_accounts%rowtype;
  v_result jsonb;
begin
  if v_mutation_id is null
     or char_length(v_mutation_id) not between 16 and 128
     or v_account_id is null
     or char_length(v_account_id) > 128
     or v_identity_id is null
     or char_length(v_identity_id) > 128
     or v_token_hash is null
     or v_token_hash !~ '^[0-9a-f]{64}$'
     or v_resource_type not in (
       'question', 'answer', 'post', 'comment', 'chat', 'experience'
     )
     or p_content is null
     or jsonb_typeof(p_content) <> 'object'
     or v_resource_id is null
     or char_length(v_resource_id) > 128
     or v_supplied_fingerprint is null
     or v_supplied_fingerprint !~ '^[0-9a-f]{64}$' then
    return jsonb_build_object('status', 'integrity_conflict');
  end if;

  v_operation := 'publish_' || v_resource_type;
  -- Only client-semantic content participates in idempotency.  A retry may
  -- construct a fresh model id/timestamp, but it must receive the originally
  -- committed resource rather than creating a duplicate.
  v_payload := p_content - array[
    'id', 'author_id', 'author_identity_id', 'display_name', 'created_at',
    'updated_at', 'revision', 'answer_count', 'comment_count',
    'viewer_can_delete', 'verified_experience'
  ];
  v_semantic_content := v_payload - 'status';
  v_fingerprint := public.exchange_community_request_fingerprint(
    jsonb_build_object(
      'operation', 'publication',
      'payload', jsonb_build_object(
        'account_id', v_account_id,
        'identity_id', v_identity_id,
        'access_token_hash', v_token_hash,
        'resource_type', v_resource_type,
        'content', v_semantic_content
      )
    )
  );
  if v_supplied_fingerprint is distinct from v_fingerprint then
    return jsonb_build_object('status', 'invalid_request');
  end if;

  v_replay := public.exchange_community_replay(
    v_mutation_id,
    v_operation,
    v_fingerprint
  );
  if v_replay is not null then
    return v_replay;
  end if;

  -- Serialize same-account publication, replay, and rate-limit decisions before
  -- entering the lower-level account -> identity -> parent lock sequence.
  select account.* into v_account
  from public.exchange_accounts account
  where account.id = v_account_id
  for update;
  if not found then
    return jsonb_build_object('status', 'account_missing');
  end if;

  v_replay := public.exchange_community_replay(
    v_mutation_id,
    v_operation,
    v_fingerprint
  );
  if v_replay is not null then
    return v_replay;
  end if;

  -- Unknown fields were intentionally retained and are rejected by the strict
  -- per-resource allowlists in the locked mutation.
  v_internal_fingerprint := public.exchange_community_request_fingerprint(
    jsonb_build_array(
      v_operation,
      v_resource_id,
      v_account_id,
      v_identity_id,
      v_token_hash,
      v_payload
    )
  );

  v_result := public.exchange_commit_public_community_content(
    v_mutation_id,
    v_resource_id,
    v_resource_type,
    v_account_id,
    v_identity_id,
    v_token_hash,
    v_payload
  );

  if v_result ->> 'status' = 'committed' then
    -- Replace the internal canonical hash with the adapter request-envelope
    -- hash before commit.  Exact retries now resolve without rerunning writes.
    update public.exchange_community_mutation_receipts receipt
    set request_fingerprint = v_fingerprint,
        response = v_result
    where receipt.id = v_mutation_id
      and receipt.operation = v_operation
      and receipt.request_fingerprint = v_internal_fingerprint;
    if not found then
      raise exception 'publication receipt missing after committed mutation'
        using errcode = '23514';
    end if;
    return v_result;
  end if;

  if v_result ->> 'status' = 'invalid_request' then
    return jsonb_build_object('status', 'integrity_conflict');
  end if;
  return v_result;
end;
$$;

-- Adapter-facing owner deletion.  The target revision is read only as an
-- internal optimistic guard; ownership and the final delete are checked again
-- under the canonical account -> identity -> parent -> child locks.
create or replace function public.exchange_delete_public_community_content(
  p_mutation_id text,
  p_request_fingerprint text,
  p_account_id text,
  p_identity_id text,
  p_access_token_hash text,
  p_resource_type text,
  p_resource_id text
) returns jsonb
language plpgsql
security definer
set search_path = public, pg_temp
as $$
declare
  v_mutation_id text := nullif(btrim(p_mutation_id), '');
  v_supplied_fingerprint text := nullif(btrim(p_request_fingerprint), '');
  v_account_id text := nullif(btrim(p_account_id), '');
  v_identity_id text := nullif(btrim(p_identity_id), '');
  v_token_hash text := lower(nullif(btrim(p_access_token_hash), ''));
  v_resource_type text := nullif(btrim(p_resource_type), '');
  v_resource_id text := nullif(btrim(p_resource_id), '');
  v_operation text;
  v_fingerprint text;
  v_internal_fingerprint text;
  v_replay jsonb;
  v_expected_revision bigint;
  v_account public.exchange_accounts%rowtype;
  v_result jsonb;
begin
  if v_mutation_id is null
     or char_length(v_mutation_id) not between 16 and 128
     or v_account_id is null
     or char_length(v_account_id) > 128
     or v_identity_id is null
     or char_length(v_identity_id) > 128
     or v_token_hash is null
     or v_token_hash !~ '^[0-9a-f]{64}$'
     or v_resource_type not in ('post', 'comment')
     or v_resource_id is null
     or char_length(v_resource_id) > 128
     or v_supplied_fingerprint is null
     or v_supplied_fingerprint !~ '^[0-9a-f]{64}$' then
    return jsonb_build_object('status', 'integrity_conflict');
  end if;

  v_operation := 'delete_' || v_resource_type;
  v_fingerprint := public.exchange_community_request_fingerprint(
    jsonb_build_object(
      'operation', 'delete_public_content',
      'payload', jsonb_build_object(
        'mutation_id', v_mutation_id,
        'account_id', v_account_id,
        'identity_id', v_identity_id,
        'access_token_hash', v_token_hash,
        'resource_type', v_resource_type,
        'resource_id', v_resource_id
      )
    )
  );
  if v_supplied_fingerprint is distinct from v_fingerprint then
    return jsonb_build_object('status', 'invalid_request');
  end if;

  v_replay := public.exchange_community_replay(
    v_mutation_id,
    v_operation,
    v_fingerprint
  );
  if v_replay is not null then
    return v_replay;
  end if;

  select account.* into v_account
  from public.exchange_accounts account
  where account.id = v_account_id
  for update;
  if not found then
    return jsonb_build_object('status', 'account_missing');
  end if;

  v_replay := public.exchange_community_replay(
    v_mutation_id,
    v_operation,
    v_fingerprint
  );
  if v_replay is not null then
    return v_replay;
  end if;

  if v_resource_type = 'post' then
    select post.revision into v_expected_revision
    from public.exchange_community_posts post
    where post.id = v_resource_id;
  else
    select comment.revision into v_expected_revision
    from public.exchange_community_post_comments comment
    where comment.id = v_resource_id;
  end if;
  if not found then
    return jsonb_build_object('status', 'resource_missing');
  end if;

  v_internal_fingerprint := public.exchange_community_request_fingerprint(
    jsonb_build_array(
      v_operation,
      v_resource_id,
      v_account_id,
      v_identity_id,
      v_token_hash,
      v_expected_revision
    )
  );
  v_result := public.exchange_delete_public_community_content(
    v_mutation_id,
    v_resource_type,
    v_resource_id,
    v_account_id,
    v_identity_id,
    v_token_hash,
    v_expected_revision
  );

  -- A moderation commit may have advanced the revision between the unlocked
  -- hint read and the target lock.  The first call retains that lock, so one
  -- retry with the returned revision is deterministic and cannot overwrite.
  if v_result ->> 'status' = 'status_conflict' then
    v_expected_revision := (v_result ->> 'current_revision')::bigint;
    v_internal_fingerprint := public.exchange_community_request_fingerprint(
      jsonb_build_array(
        v_operation,
        v_resource_id,
        v_account_id,
        v_identity_id,
        v_token_hash,
        v_expected_revision
      )
    );
    v_result := public.exchange_delete_public_community_content(
      v_mutation_id,
      v_resource_type,
      v_resource_id,
      v_account_id,
      v_identity_id,
      v_token_hash,
      v_expected_revision
    );
  end if;

  if v_result ->> 'status' = 'committed' then
    update public.exchange_community_mutation_receipts receipt
    set request_fingerprint = v_fingerprint,
        response = v_result
    where receipt.id = v_mutation_id
      and receipt.operation = v_operation
      and receipt.request_fingerprint = v_internal_fingerprint;
    if not found then
      raise exception 'delete receipt missing after committed mutation'
        using errcode = '23514';
    end if;
    return v_result;
  end if;

  if v_result ->> 'status' = 'invalid_request' then
    return jsonb_build_object('status', 'integrity_conflict');
  end if;
  return v_result;
end;
$$;

create or replace function public.exchange_commit_public_community_moderation(
  p_mutation_id text,
  p_request_fingerprint text,
  p_moderator_id text,
  p_resource_type text,
  p_resource_id text,
  p_expected_status text,
  p_status text,
  p_note text
) returns jsonb
language plpgsql
security definer
set search_path = public, pg_temp
as $$
declare
  v_mutation_id text := nullif(btrim(p_mutation_id), '');
  v_supplied_fingerprint text := nullif(btrim(p_request_fingerprint), '');
  v_moderator_id text := nullif(btrim(p_moderator_id), '');
  v_resource_type text := nullif(btrim(p_resource_type), '');
  v_resource_id text := nullif(btrim(p_resource_id), '');
  v_expected_status text := nullif(btrim(p_expected_status), '');
  v_new_status text := nullif(btrim(p_status), '');
  v_note text := nullif(btrim(p_note), '');
  v_operation text;
  v_fingerprint text;
  v_replay jsonb;
  v_now timestamptz;
  v_parent_id text;
  v_current_status text;
  v_current_revision bigint;
  v_moderator public.exchange_accounts%rowtype;
  v_question public.exchange_community_questions%rowtype;
  v_answer public.exchange_community_answers%rowtype;
  v_post public.exchange_community_posts%rowtype;
  v_comment public.exchange_community_post_comments%rowtype;
  v_chat public.exchange_community_public_chat_messages%rowtype;
  v_experience public.exchange_community_experience_submissions%rowtype;
  v_audit public.exchange_community_moderation_audits%rowtype;
  v_content jsonb;
  v_response jsonb;
begin
  if v_mutation_id is null
     or char_length(v_mutation_id) not between 16 and 128
     or v_moderator_id is null
     or char_length(v_moderator_id) > 128
     or v_resource_type not in (
       'question', 'answer', 'post', 'comment', 'chat', 'experience'
     )
     or v_resource_id is null
     or char_length(v_resource_id) > 128
     or v_expected_status not in ('pending', 'approved', 'hidden')
     or v_new_status not in ('approved', 'hidden')
     or v_note is null
     or char_length(v_note) not between 2 and 500
     or v_supplied_fingerprint is null
     or v_supplied_fingerprint !~ '^[0-9a-f]{64}$' then
    return jsonb_build_object('status', 'integrity_conflict');
  end if;

  v_operation := 'moderate_' || v_resource_type;
  v_fingerprint := public.exchange_community_request_fingerprint(
    jsonb_build_object(
      'operation', 'moderation',
      'payload', jsonb_build_object(
        'mutation_id', v_mutation_id,
        'moderator_id', v_moderator_id,
        'resource_type', v_resource_type,
        'resource_id', v_resource_id,
        'expected_status', v_expected_status,
        'status', v_new_status,
        'note', v_note
      )
    )
  );
  if v_supplied_fingerprint is distinct from v_fingerprint then
    return jsonb_build_object('status', 'invalid_request');
  end if;

  v_replay := public.exchange_community_replay(
    v_mutation_id,
    v_operation,
    v_fingerprint
  );
  if v_replay is not null then
    return v_replay;
  end if;

  -- Fixed moderation lock order: moderator account, optional parent, target.
  select account.* into v_moderator
  from public.exchange_accounts account
  where account.id = v_moderator_id
  for update;
  if not found then
    return jsonb_build_object('status', 'moderator_missing');
  end if;

  v_replay := public.exchange_community_replay(
    v_mutation_id,
    v_operation,
    v_fingerprint
  );
  if v_replay is not null then
    return v_replay;
  end if;

  if v_resource_type = 'question' then
    select question.* into v_question
    from public.exchange_community_questions question
    where question.id = v_resource_id
    for update;
    if not found then
      return jsonb_build_object('status', 'resource_missing');
    end if;
    v_current_status := v_question.status;
    v_current_revision := v_question.revision;
    v_content := to_jsonb(v_question);
  elsif v_resource_type = 'answer' then
    select answer.question_id into v_parent_id
    from public.exchange_community_answers answer
    where answer.id = v_resource_id;
    if not found then
      return jsonb_build_object('status', 'resource_missing');
    end if;
    select question.* into v_question
    from public.exchange_community_questions question
    where question.id = v_parent_id
    for update;
    if not found then
      return jsonb_build_object('status', 'resource_missing');
    end if;
    select answer.* into v_answer
    from public.exchange_community_answers answer
    where answer.id = v_resource_id
      and answer.question_id = v_parent_id
    for update;
    if not found then
      return jsonb_build_object('status', 'resource_missing');
    end if;
    v_current_status := v_answer.status;
    v_current_revision := v_answer.revision;
    v_content := to_jsonb(v_answer);
  elsif v_resource_type = 'post' then
    select post.* into v_post
    from public.exchange_community_posts post
    where post.id = v_resource_id
    for update;
    if not found then
      return jsonb_build_object('status', 'resource_missing');
    end if;
    v_current_status := v_post.status;
    v_current_revision := v_post.revision;
    v_content := to_jsonb(v_post);
  elsif v_resource_type = 'comment' then
    select comment.post_id into v_parent_id
    from public.exchange_community_post_comments comment
    where comment.id = v_resource_id;
    if not found then
      return jsonb_build_object('status', 'resource_missing');
    end if;
    select post.* into v_post
    from public.exchange_community_posts post
    where post.id = v_parent_id
    for update;
    if not found then
      return jsonb_build_object('status', 'resource_missing');
    end if;
    select comment.* into v_comment
    from public.exchange_community_post_comments comment
    where comment.id = v_resource_id
      and comment.post_id = v_parent_id
    for update;
    if not found then
      return jsonb_build_object('status', 'resource_missing');
    end if;
    v_current_status := v_comment.status;
    v_current_revision := v_comment.revision;
    v_content := to_jsonb(v_comment);
  elsif v_resource_type = 'chat' then
    select chat.* into v_chat
    from public.exchange_community_public_chat_messages chat
    where chat.id = v_resource_id
    for update;
    if not found then
      return jsonb_build_object('status', 'resource_missing');
    end if;
    v_current_status := v_chat.status;
    v_current_revision := v_chat.revision;
    v_content := to_jsonb(v_chat);
  else
    select experience.* into v_experience
    from public.exchange_community_experience_submissions experience
    where experience.id = v_resource_id
    for update;
    if not found then
      return jsonb_build_object('status', 'resource_missing');
    end if;
    v_current_status := v_experience.status;
    v_current_revision := v_experience.revision;
    v_content := to_jsonb(v_experience);
  end if;

  if v_current_status is distinct from v_expected_status then
    return jsonb_build_object(
      'status', 'status_conflict',
      'current_status', v_current_status,
      'content', v_content
    );
  end if;
  if v_current_status = v_new_status then
    return jsonb_build_object(
      'status', 'no_change',
      'content', v_content
    );
  end if;
  if v_current_revision = 9223372036854775807 then
    return jsonb_build_object('status', 'integrity_conflict');
  end if;

  v_now := clock_timestamp();
  begin
    if v_resource_type = 'question' then
      update public.exchange_community_questions question
      set status = v_new_status,
          revision = question.revision + 1,
          updated_at = v_now
      where question.id = v_resource_id
      returning * into v_question;
      v_content := to_jsonb(v_question);
    elsif v_resource_type = 'answer' then
      update public.exchange_community_answers answer
      set status = v_new_status,
          revision = answer.revision + 1,
          updated_at = v_now
      where answer.id = v_resource_id
      returning * into v_answer;
      v_content := to_jsonb(v_answer);
    elsif v_resource_type = 'post' then
      update public.exchange_community_posts post
      set status = v_new_status,
          revision = post.revision + 1,
          updated_at = v_now
      where post.id = v_resource_id
      returning * into v_post;
      v_content := to_jsonb(v_post);
    elsif v_resource_type = 'comment' then
      update public.exchange_community_post_comments comment
      set status = v_new_status,
          revision = comment.revision + 1,
          updated_at = v_now
      where comment.id = v_resource_id
      returning * into v_comment;
      v_content := to_jsonb(v_comment);
    elsif v_resource_type = 'chat' then
      update public.exchange_community_public_chat_messages chat
      set status = v_new_status,
          revision = chat.revision + 1,
          updated_at = v_now
      where chat.id = v_resource_id
      returning * into v_chat;
      v_content := to_jsonb(v_chat);
    else
      update public.exchange_community_experience_submissions experience
      set status = v_new_status,
          revision = experience.revision + 1,
          updated_at = v_now
      where experience.id = v_resource_id
      returning * into v_experience;
      v_content := to_jsonb(v_experience);
    end if;

    insert into public.exchange_community_moderation_audits (
      id, resource_type, resource_id, previous_status, new_status,
      moderator_id, note, request_fingerprint, created_at, retained_until
    ) values (
      v_mutation_id,
      v_resource_type,
      v_resource_id,
      v_current_status,
      v_new_status,
      v_moderator_id,
      v_note,
      v_fingerprint,
      v_now,
      v_now + interval '2160 hours'
    ) returning * into v_audit;

    v_response := jsonb_build_object(
      'status', 'committed',
      'idempotent', false,
      'content', v_content,
      'audit', to_jsonb(v_audit) - 'request_fingerprint'
    );

    insert into public.exchange_community_mutation_receipts (
      id, operation, request_fingerprint, actor_account_id, actor_identity_id,
      resource_type, resource_id, response, created_at, retained_until
    ) values (
      v_mutation_id,
      v_operation,
      v_fingerprint,
      v_moderator_id,
      null,
      v_resource_type,
      v_resource_id,
      v_response,
      v_now,
      v_now + interval '168 hours'
    );
  exception
    when integrity_constraint_violation or data_exception then
      v_replay := public.exchange_community_replay(
        v_mutation_id,
        v_operation,
        v_fingerprint
      );
      if v_replay is not null then
        return v_replay;
      end if;
      return jsonb_build_object('status', 'integrity_conflict');
  end;

  return v_response;
end;
$$;

-- Account-deletion preflight for public content.  The identity itself remains
-- until the later account DELETE cascades, so private/report migrations can
-- still resolve it.  Public attribution and rate-limit history are removed in
-- this one transaction.
create or replace function public.exchange_anonymize_public_community_author(
  p_mutation_id text,
  p_request_fingerprint text,
  p_identity_id text,
  p_expected_account_id text,
  p_replacement_name text
) returns jsonb
language plpgsql
security definer
set search_path = public, pg_temp
as $$
declare
  v_mutation_id text := nullif(btrim(p_mutation_id), '');
  v_supplied_fingerprint text := nullif(btrim(p_request_fingerprint), '');
  v_identity_id text := nullif(btrim(p_identity_id), '');
  v_expected_account_id text := nullif(btrim(p_expected_account_id), '');
  v_replacement_name text := nullif(btrim(p_replacement_name), '');
  v_operation constant text := 'anonymize_public_author';
  v_fingerprint text;
  v_replay jsonb;
  v_now timestamptz;
  v_count bigint;
  v_counts jsonb := '{}'::jsonb;
  v_account public.exchange_accounts%rowtype;
  v_identity public.exchange_community_identities%rowtype;
  v_response jsonb;
begin
  if v_mutation_id is null
     or char_length(v_mutation_id) not between 16 and 128
     or v_identity_id is null
     or char_length(v_identity_id) > 128
     or (
       v_expected_account_id is not null
       and char_length(v_expected_account_id) > 128
     )
     or v_replacement_name is null
     or char_length(v_replacement_name) not between 2 and 30
     or v_supplied_fingerprint is null
     or v_supplied_fingerprint !~ '^[0-9a-f]{64}$' then
    return jsonb_build_object('status', 'integrity_conflict');
  end if;

  v_fingerprint := public.exchange_community_request_fingerprint(
    jsonb_build_object(
      'operation', v_operation,
      'payload', jsonb_build_object(
        'mutation_id', v_mutation_id,
        'identity_id', v_identity_id,
        'expected_account_id', v_expected_account_id,
        'replacement_name', v_replacement_name
      )
    )
  );
  if v_supplied_fingerprint is distinct from v_fingerprint then
    return jsonb_build_object('status', 'invalid_request');
  end if;

  v_replay := public.exchange_community_replay(
    v_mutation_id,
    v_operation,
    v_fingerprint
  );
  if v_replay is not null then
    return v_replay;
  end if;

  -- Fixed actor lock order remains account before identity when linked.
  if v_expected_account_id is not null then
    select account.* into v_account
    from public.exchange_accounts account
    where account.id = v_expected_account_id
    for update;
    if not found then
      return jsonb_build_object('status', 'identity_conflict');
    end if;
  end if;

  select identity.* into v_identity
  from public.exchange_community_identities identity
  where identity.id = v_identity_id
  for update;
  if not found then
    return jsonb_build_object('status', 'identity_missing');
  end if;
  if v_identity.account_id is distinct from v_expected_account_id then
    return jsonb_build_object('status', 'identity_conflict');
  end if;

  v_replay := public.exchange_community_replay(
    v_mutation_id,
    v_operation,
    v_fingerprint
  );
  if v_replay is not null then
    return v_replay;
  end if;

  v_now := clock_timestamp();
  begin
    -- Parent tables precede their children to match moderation/delete locks.
    update public.exchange_community_questions question
    set author_identity_id = null,
        display_name = v_replacement_name,
        identity_mode = 'anonymous',
        revision = question.revision + 1,
        updated_at = v_now
    where question.author_identity_id = v_identity_id;
    get diagnostics v_count = row_count;
    v_counts := v_counts || jsonb_build_object('question', v_count);

    update public.exchange_community_answers answer
    set author_identity_id = null,
        display_name = v_replacement_name,
        identity_mode = 'anonymous',
        revision = answer.revision + 1,
        updated_at = v_now
    where answer.author_identity_id = v_identity_id;
    get diagnostics v_count = row_count;
    v_counts := v_counts || jsonb_build_object('answer', v_count);

    update public.exchange_community_posts post
    set author_identity_id = null,
        display_name = v_replacement_name,
        identity_mode = 'anonymous',
        revision = post.revision + 1,
        updated_at = v_now
    where post.author_identity_id = v_identity_id;
    get diagnostics v_count = row_count;
    v_counts := v_counts || jsonb_build_object('post', v_count);

    update public.exchange_community_post_comments comment
    set author_identity_id = null,
        display_name = v_replacement_name,
        identity_mode = 'anonymous',
        revision = comment.revision + 1,
        updated_at = v_now
    where comment.author_identity_id = v_identity_id;
    get diagnostics v_count = row_count;
    v_counts := v_counts || jsonb_build_object('comment', v_count);

    update public.exchange_community_public_chat_messages chat
    set author_identity_id = null,
        display_name = v_replacement_name,
        identity_mode = 'anonymous',
        revision = chat.revision + 1,
        updated_at = v_now
    where chat.author_identity_id = v_identity_id;
    get diagnostics v_count = row_count;
    v_counts := v_counts || jsonb_build_object('chat', v_count);

    update public.exchange_community_experience_submissions experience
    set author_identity_id = null,
        display_name = v_replacement_name,
        identity_mode = 'anonymous',
        source_url = null,
        revision = experience.revision + 1,
        updated_at = v_now
    where experience.author_identity_id = v_identity_id;
    get diagnostics v_count = row_count;
    v_counts := v_counts || jsonb_build_object('experience', v_count);

    delete from public.exchange_community_publish_events event
    where event.identity_id = v_identity_id
       or (
         v_expected_account_id is not null
         and event.account_id = v_expected_account_id
       );
    get diagnostics v_count = row_count;
    v_counts := v_counts || jsonb_build_object('publish_event', v_count);

    v_response := jsonb_build_object(
      'status', 'committed',
      'idempotent', false,
      'counts', v_counts
    );
    insert into public.exchange_community_mutation_receipts (
      id, operation, request_fingerprint, actor_account_id, actor_identity_id,
      resource_type, resource_id, response, created_at, retained_until
    ) values (
      v_mutation_id,
      v_operation,
      v_fingerprint,
      v_expected_account_id,
      v_identity_id,
      'identity',
      v_identity_id,
      v_response,
      v_now,
      v_now + interval '168 hours'
    );
  exception
    when integrity_constraint_violation or data_exception then
      v_replay := public.exchange_community_replay(
        v_mutation_id,
        v_operation,
        v_fingerprint
      );
      if v_replay is not null then
        return v_replay;
      end if;
      return jsonb_build_object('status', 'integrity_conflict');
  end;

  return v_response;
end;
$$;

create or replace function public.exchange_purge_public_community_operational_data()
returns jsonb
language plpgsql
security definer
set search_path = public, pg_temp
as $$
declare
  v_now timestamptz := clock_timestamp();
  v_publish_events bigint;
  v_receipts bigint;
  v_moderation_audits bigint;
begin
  delete from public.exchange_community_publish_events event
  where event.occurred_at <= v_now - interval '24 hours';
  get diagnostics v_publish_events = row_count;

  delete from public.exchange_community_mutation_receipts receipt
  where receipt.retained_until <= v_now;
  get diagnostics v_receipts = row_count;

  perform set_config(
    'exchange.community_moderation_audit_purge',
    'on',
    true
  );
  delete from public.exchange_community_moderation_audits audit
  where audit.retained_until <= v_now;
  get diagnostics v_moderation_audits = row_count;
  perform set_config(
    'exchange.community_moderation_audit_purge',
    'off',
    true
  );

  return jsonb_build_object(
    'status', 'committed',
    'purged_at', v_now,
    'publish_event_count', v_publish_events,
    'mutation_receipt_count', v_receipts,
    'moderation_audit_count', v_moderation_audits
  );
end;
$$;

-- PostgREST-facing tables are deny-by-default.  service_role may read rows for
-- repository projections, but every write is available only through an
-- explicitly granted SECURITY DEFINER mutation.
alter table public.exchange_community_identities enable row level security;
alter table public.exchange_community_identities force row level security;
alter table public.exchange_community_questions enable row level security;
alter table public.exchange_community_questions force row level security;
alter table public.exchange_community_answers enable row level security;
alter table public.exchange_community_answers force row level security;
alter table public.exchange_community_posts enable row level security;
alter table public.exchange_community_posts force row level security;
alter table public.exchange_community_post_comments enable row level security;
alter table public.exchange_community_post_comments force row level security;
alter table public.exchange_community_public_chat_messages enable row level security;
alter table public.exchange_community_public_chat_messages force row level security;
alter table public.exchange_community_experience_submissions enable row level security;
alter table public.exchange_community_experience_submissions force row level security;
alter table public.exchange_community_publish_events enable row level security;
alter table public.exchange_community_publish_events force row level security;
alter table public.exchange_community_moderation_audits enable row level security;
alter table public.exchange_community_moderation_audits force row level security;
alter table public.exchange_community_mutation_receipts enable row level security;
alter table public.exchange_community_mutation_receipts force row level security;

revoke all on table public.exchange_community_identities
  from public, anon, authenticated, service_role;
revoke all on table public.exchange_community_questions
  from public, anon, authenticated, service_role;
revoke all on table public.exchange_community_answers
  from public, anon, authenticated, service_role;
revoke all on table public.exchange_community_posts
  from public, anon, authenticated, service_role;
revoke all on table public.exchange_community_post_comments
  from public, anon, authenticated, service_role;
revoke all on table public.exchange_community_public_chat_messages
  from public, anon, authenticated, service_role;
revoke all on table public.exchange_community_experience_submissions
  from public, anon, authenticated, service_role;
revoke all on table public.exchange_community_publish_events
  from public, anon, authenticated, service_role;
revoke all on table public.exchange_community_moderation_audits
  from public, anon, authenticated, service_role;
revoke all on table public.exchange_community_mutation_receipts
  from public, anon, authenticated, service_role;

grant select on table public.exchange_community_identities to service_role;
grant select on table public.exchange_community_questions to service_role;
grant select on table public.exchange_community_answers to service_role;
grant select on table public.exchange_community_posts to service_role;
grant select on table public.exchange_community_post_comments to service_role;
grant select on table public.exchange_community_public_chat_messages to service_role;
grant select on table public.exchange_community_experience_submissions to service_role;
grant select on table public.exchange_community_publish_events to service_role;
grant select on table public.exchange_community_moderation_audits to service_role;
grant select on table public.exchange_community_mutation_receipts to service_role;

revoke all on function public.exchange_normalize_community_school(text)
  from public, anon, authenticated, service_role;
revoke all on function public.exchange_community_payload_has_only_keys(jsonb, text[])
  from public, anon, authenticated, service_role;
revoke all on function public.exchange_community_canonical_json(jsonb)
  from public, anon, authenticated, service_role;
revoke all on function public.exchange_community_request_fingerprint(jsonb)
  from public, anon, authenticated, service_role;
revoke all on function public.exchange_community_replay(text, text, text)
  from public, anon, authenticated, service_role;
revoke all on function public.exchange_community_display_name(jsonb, text, text)
  from public, anon, authenticated, service_role;
revoke all on function public.exchange_enforce_community_moderation_audit_append_only()
  from public, anon, authenticated, service_role;
revoke all on function public.exchange_validate_community_suspension_identity_binding()
  from public, anon, authenticated, service_role;

-- Earlier internal signatures remain owner-only implementation details.
revoke all on function public.exchange_commit_community_identity(
  text, text, text, text
) from public, anon, authenticated, service_role;
revoke all on function public.exchange_commit_public_community_content(
  text, text, text, text, text, text, jsonb
) from public, anon, authenticated, service_role;
revoke all on function public.exchange_delete_public_community_content(
  text, text, text, text, text, text, bigint
) from public, anon, authenticated, service_role;

revoke all on function public.exchange_commit_public_community_publication(
  text, text, text, text, text, text, jsonb
) from public, anon, authenticated, service_role;
revoke all on function public.exchange_delete_public_community_content(
  text, text, text, text, text, text, text
) from public, anon, authenticated, service_role;
revoke all on function public.exchange_commit_public_community_moderation(
  text, text, text, text, text, text, text, text
) from public, anon, authenticated, service_role;
revoke all on function public.exchange_anonymize_public_community_author(
  text, text, text, text, text
) from public, anon, authenticated, service_role;
revoke all on function public.exchange_purge_public_community_operational_data()
  from public, anon, authenticated, service_role;

grant execute on function public.exchange_commit_public_community_publication(
  text, text, text, text, text, text, jsonb
) to service_role;
grant execute on function public.exchange_delete_public_community_content(
  text, text, text, text, text, text, text
) to service_role;
grant execute on function public.exchange_commit_public_community_moderation(
  text, text, text, text, text, text, text, text
) to service_role;
grant execute on function public.exchange_anonymize_public_community_author(
  text, text, text, text, text
) to service_role;
grant execute on function public.exchange_purge_public_community_operational_data()
  to service_role;

create or replace function public.exchange_commit_public_community_content(
  p_event_id text,
  p_content_id text,
  p_content_type text,
  p_account_id text,
  p_identity_id text,
  p_access_token_hash text,
  p_payload jsonb
) returns jsonb
language plpgsql
security definer
set search_path = public, pg_temp
as $$
declare
  v_event_id text := nullif(btrim(p_event_id), '');
  v_content_id text := nullif(btrim(p_content_id), '');
  v_content_type text := nullif(btrim(p_content_type), '');
  v_account_id text := nullif(btrim(p_account_id), '');
  v_identity_id text := nullif(btrim(p_identity_id), '');
  v_token_hash text := nullif(btrim(p_access_token_hash), '');
  v_operation text;
  v_fingerprint text;
  v_replay jsonb;
  v_now timestamptz;
  v_status text;
  v_identity_mode text;
  v_display_name text;
  v_verified_school_key text;
  v_required_school_key text;
  v_email_verified boolean;
  v_student_verified boolean;
  v_recent_count bigint;
  v_publish_limit integer;
  v_account public.exchange_accounts%rowtype;
  v_identity public.exchange_community_identities%rowtype;
  v_question public.exchange_community_questions%rowtype;
  v_answer public.exchange_community_answers%rowtype;
  v_post public.exchange_community_posts%rowtype;
  v_comment public.exchange_community_post_comments%rowtype;
  v_chat public.exchange_community_public_chat_messages%rowtype;
  v_experience public.exchange_community_experience_submissions%rowtype;
  v_content jsonb;
  v_response jsonb;
begin
  if v_event_id is null
     or char_length(v_event_id) > 128
     or v_content_id is null
     or char_length(v_content_id) > 128
     or v_content_type not in (
       'question', 'answer', 'post', 'comment', 'chat', 'experience'
     )
     or v_account_id is null
     or char_length(v_account_id) > 128
     or v_identity_id is null
     or char_length(v_identity_id) > 128
     or v_token_hash is null
     or v_token_hash !~ '^[0-9a-f]{64}$'
     or p_payload is null
     or jsonb_typeof(p_payload) <> 'object' then
    return jsonb_build_object('status', 'invalid_request');
  end if;

  v_operation := 'publish_' || v_content_type;
  v_fingerprint := public.exchange_community_request_fingerprint(
    jsonb_build_array(
      v_operation,
      v_content_id,
      v_account_id,
      v_identity_id,
      v_token_hash,
      p_payload
    )
  );

  -- An exact committed replay wins even if its actor is now suspended or its
  -- parent is later hidden/deleted.
  v_replay := public.exchange_community_replay(
    v_event_id,
    v_operation,
    v_fingerprint
  );
  if v_replay is not null then
    return v_replay;
  end if;

  -- Fixed lock order (1): account.  This also serializes rate-limit decisions
  -- and closes the in-flight publication versus suspension/account-delete race.
  select account.* into v_account
  from public.exchange_accounts account
  where account.id = v_account_id
  for update;

  if not found then
    return jsonb_build_object('status', 'account_missing');
  end if;

  -- Fixed lock order (2): actor identity.
  select identity.* into v_identity
  from public.exchange_community_identities identity
  where identity.id = v_identity_id
  for update;

  if not found then
    return jsonb_build_object('status', 'identity_missing');
  end if;

  if v_identity.account_id is distinct from v_account_id
     or v_identity.access_token_hash is distinct from v_token_hash then
    return jsonb_build_object('status', 'identity_conflict');
  end if;

  -- Repeat under both actor locks because another worker may have committed the
  -- event while this call waited.
  v_replay := public.exchange_community_replay(
    v_event_id,
    v_operation,
    v_fingerprint
  );
  if v_replay is not null then
    return v_replay;
  end if;

  v_now := clock_timestamp();
  if v_account.community_suspended_until is not null
     and v_account.community_suspended_until > v_now then
    return jsonb_build_object(
      'status', 'account_suspended',
      'suspended_until', v_account.community_suspended_until
    );
  end if;

  v_email_verified := coalesce(
    v_account.profile -> 'email_verified' = 'true'::jsonb,
    false
  );
  v_student_verified := coalesce(
    v_account.profile -> 'student_status_verified' = 'true'::jsonb,
    false
  );
  v_verified_school_key := public.exchange_normalize_community_school(
    coalesce(v_account.profile ->> 'verified_university', '')
  );
  v_identity_mode := coalesce(p_payload ->> 'identity_mode', 'anonymous');
  v_display_name := public.exchange_community_display_name(
    v_account.profile,
    v_identity_mode,
    v_content_type
  );

  if v_display_name is null then
    return jsonb_build_object('status', 'student_verification_required');
  end if;

  -- Validate payload allowlists and lock a parent resource, when present, only
  -- after account and identity locks.  Parent and child resources never reverse
  -- this order in delete or moderation RPCs below.
  if v_content_type = 'question' then
    if not public.exchange_community_payload_has_only_keys(
      p_payload,
      array[
        'school_name', 'home_university', 'topic', 'title', 'body',
        'identity_mode', 'status'
      ]
    ) then
      return jsonb_build_object('status', 'invalid_request');
    end if;
    v_status := coalesce(p_payload ->> 'status', 'pending');
    v_required_school_key := public.exchange_normalize_community_school(
      coalesce(p_payload ->> 'home_university', '')
    );
    if not v_student_verified
       or v_required_school_key = ''
       or v_verified_school_key <> v_required_school_key then
      return jsonb_build_object('status', 'board_forbidden');
    end if;
  elsif v_content_type = 'answer' then
    if not public.exchange_community_payload_has_only_keys(
      p_payload,
      array[
        'question_id', 'body', 'identity_mode', 'exchange_year', 'status'
      ]
    ) then
      return jsonb_build_object('status', 'invalid_request');
    end if;
    select question.* into v_question
    from public.exchange_community_questions question
    where question.id = nullif(btrim(p_payload ->> 'question_id'), '')
    for update;
    if not found or v_question.status = 'hidden' then
      return jsonb_build_object('status', 'parent_missing');
    end if;
    v_status := coalesce(p_payload ->> 'status', 'pending');
    v_required_school_key := public.exchange_normalize_community_school(
      v_question.home_university
    );
    if not v_student_verified
       or v_verified_school_key <> v_required_school_key then
      return jsonb_build_object('status', 'board_forbidden');
    end if;
  elsif v_content_type = 'post' then
    if not public.exchange_community_payload_has_only_keys(
      p_payload,
      array[
        'board_id', 'board_kind', 'school_name', 'post_type', 'topic',
        'country', 'academic_year', 'application_stage', 'title', 'body',
        'identity_mode', 'status'
      ]
    ) then
      return jsonb_build_object('status', 'invalid_request');
    end if;
    v_status := coalesce(p_payload ->> 'status', 'approved');
    if p_payload ->> 'board_kind' in ('public_study_abroad', 'public_topic') then
      if not v_email_verified then
        return jsonb_build_object('status', 'email_unverified');
      end if;
      if (
           p_payload ->> 'board_kind' = 'public_study_abroad'
           and p_payload ->> 'board_id' <> 'public-study-abroad'
         )
         or (
           p_payload ->> 'board_kind' = 'public_topic'
           and p_payload ->> 'board_id' <> 'language-school'
         ) then
        return jsonb_build_object('status', 'board_forbidden');
      end if;
    elsif p_payload ->> 'board_kind' = 'university_exchange' then
      if not v_email_verified then
        return jsonb_build_object('status', 'email_unverified');
      end if;
      v_required_school_key := public.exchange_normalize_community_school(
        coalesce(p_payload ->> 'school_name', '')
      );
      if not v_student_verified
         or v_required_school_key = ''
         or v_verified_school_key <> v_required_school_key
         or coalesce(p_payload ->> 'board_id', '') !~ '^university:' then
        return jsonb_build_object('status', 'board_forbidden');
      end if;
    else
      return jsonb_build_object('status', 'board_forbidden');
    end if;
  elsif v_content_type = 'comment' then
    if not public.exchange_community_payload_has_only_keys(
      p_payload,
      array['post_id', 'body', 'identity_mode', 'status']
    ) then
      return jsonb_build_object('status', 'invalid_request');
    end if;
    select post.* into v_post
    from public.exchange_community_posts post
    where post.id = nullif(btrim(p_payload ->> 'post_id'), '')
    for update;
    if not found or v_post.status = 'hidden' then
      return jsonb_build_object('status', 'parent_missing');
    end if;
    v_status := coalesce(p_payload ->> 'status', 'approved');
    if v_post.board_kind in ('public_study_abroad', 'public_topic') then
      if not v_email_verified then
        return jsonb_build_object('status', 'email_unverified');
      end if;
    elsif v_post.board_kind = 'university_exchange' then
      if not v_email_verified then
        return jsonb_build_object('status', 'email_unverified');
      end if;
      v_required_school_key := public.exchange_normalize_community_school(
        v_post.school_name
      );
      if not v_student_verified
         or v_verified_school_key <> v_required_school_key then
        return jsonb_build_object('status', 'board_forbidden');
      end if;
    else
      return jsonb_build_object('status', 'board_forbidden');
    end if;
  elsif v_content_type = 'chat' then
    if not public.exchange_community_payload_has_only_keys(
      p_payload,
      array['school_name', 'body', 'identity_mode', 'status']
    ) then
      return jsonb_build_object('status', 'invalid_request');
    end if;
    v_status := coalesce(p_payload ->> 'status', 'approved');
    if not v_student_verified or v_verified_school_key = '' then
      return jsonb_build_object('status', 'board_forbidden');
    end if;
  else
    if not public.exchange_community_payload_has_only_keys(
      p_payload,
      array[
        'school_name', 'home_university', 'title', 'summary',
        'exchange_year', 'themes', 'source_url', 'identity_mode', 'status'
      ]
    ) then
      return jsonb_build_object('status', 'invalid_request');
    end if;
    v_status := coalesce(p_payload ->> 'status', 'pending');
    v_required_school_key := public.exchange_normalize_community_school(
      coalesce(p_payload ->> 'home_university', '')
    );
    if not v_student_verified
       or v_required_school_key = ''
       or v_verified_school_key <> v_required_school_key then
      return jsonb_build_object('status', 'board_forbidden');
    end if;
    if jsonb_typeof(coalesce(p_payload -> 'themes', '[]'::jsonb)) <> 'array'
       or jsonb_array_length(coalesce(p_payload -> 'themes', '[]'::jsonb)) > 8
       or exists (
         select 1
         from jsonb_array_elements(
           coalesce(p_payload -> 'themes', '[]'::jsonb)
         ) as theme(value)
         where jsonb_typeof(theme.value) <> 'string'
           or btrim(theme.value #>> '{}') = ''
           or char_length(theme.value #>> '{}') > 80
       ) then
      return jsonb_build_object('status', 'invalid_request');
    end if;
  end if;

  if v_status not in ('pending', 'approved') then
    return jsonb_build_object('status', 'invalid_request');
  end if;

  -- The account row lock makes count-and-insert atomic across workers.  A new
  -- account gets five publications per ten minutes; established accounts get
  -- twenty, matching the existing Web contract.
  v_publish_limit := case
    when v_account.created_at >= v_now - interval '24 hours' then 5
    else 20
  end;
  select count(*)
    into v_recent_count
  from public.exchange_community_publish_events event
  where event.account_id = v_account_id
    and event.occurred_at >= v_now - interval '10 minutes';

  if v_recent_count >= v_publish_limit then
    return jsonb_build_object(
      'status', 'rate_limited',
      'retry_after_seconds', 600
    );
  end if;

  begin
    insert into public.exchange_community_publish_events (
      id,
      account_id,
      identity_id,
      content_type,
      occurred_at
    ) values (
      v_event_id,
      v_account_id,
      v_identity_id,
      v_content_type,
      v_now
    );

    if v_content_type = 'question' then
      insert into public.exchange_community_questions (
        id, author_identity_id, school_name, home_university, topic, title,
        body, display_name, identity_mode, status, revision, created_at, updated_at
      ) values (
        v_content_id,
        v_identity_id,
        btrim(p_payload ->> 'school_name'),
        btrim(p_payload ->> 'home_university'),
        p_payload ->> 'topic',
        btrim(p_payload ->> 'title'),
        btrim(p_payload ->> 'body'),
        v_display_name,
        v_identity_mode,
        v_status,
        0,
        v_now,
        v_now
      ) returning * into v_question;
      v_content := to_jsonb(v_question);
    elsif v_content_type = 'answer' then
      insert into public.exchange_community_answers (
        id, question_id, author_identity_id, body, display_name, identity_mode,
        exchange_year, verified_experience, status, revision, created_at, updated_at
      ) values (
        v_content_id,
        v_question.id,
        v_identity_id,
        btrim(p_payload ->> 'body'),
        v_display_name,
        v_identity_mode,
        nullif(btrim(p_payload ->> 'exchange_year'), ''),
        false,
        v_status,
        0,
        v_now,
        v_now
      ) returning * into v_answer;
      v_content := to_jsonb(v_answer);
    elsif v_content_type = 'post' then
      insert into public.exchange_community_posts (
        id, author_identity_id, board_id, board_kind, school_name, display_name,
        identity_mode, post_type, topic, country, academic_year,
        application_stage, title, body, status, revision, created_at, updated_at
      ) values (
        v_content_id,
        v_identity_id,
        btrim(p_payload ->> 'board_id'),
        p_payload ->> 'board_kind',
        btrim(p_payload ->> 'school_name'),
        v_display_name,
        v_identity_mode,
        coalesce(p_payload ->> 'post_type', 'discussion'),
        coalesce(p_payload ->> 'topic', 'application'),
        nullif(btrim(p_payload ->> 'country'), ''),
        nullif(btrim(p_payload ->> 'academic_year'), ''),
        nullif(btrim(p_payload ->> 'application_stage'), ''),
        btrim(p_payload ->> 'title'),
        btrim(p_payload ->> 'body'),
        v_status,
        0,
        v_now,
        v_now
      ) returning * into v_post;
      v_content := to_jsonb(v_post);
    elsif v_content_type = 'comment' then
      insert into public.exchange_community_post_comments (
        id, post_id, author_identity_id, display_name, identity_mode, body,
        status, revision, created_at, updated_at
      ) values (
        v_content_id,
        v_post.id,
        v_identity_id,
        v_display_name,
        v_identity_mode,
        btrim(p_payload ->> 'body'),
        v_status,
        0,
        v_now,
        v_now
      ) returning * into v_comment;
      v_content := to_jsonb(v_comment);
    elsif v_content_type = 'chat' then
      insert into public.exchange_community_public_chat_messages (
        id, author_identity_id, school_name, display_name, identity_mode, body,
        status, revision, created_at, updated_at
      ) values (
        v_content_id,
        v_identity_id,
        btrim(p_payload ->> 'school_name'),
        v_display_name,
        v_identity_mode,
        btrim(p_payload ->> 'body'),
        v_status,
        0,
        v_now,
        v_now
      ) returning * into v_chat;
      v_content := to_jsonb(v_chat);
    else
      insert into public.exchange_community_experience_submissions (
        id, author_identity_id, school_name, home_university, title, summary,
        exchange_year, themes, source_url, display_name, identity_mode, status,
        revision, created_at, updated_at
      ) values (
        v_content_id,
        v_identity_id,
        btrim(p_payload ->> 'school_name'),
        btrim(p_payload ->> 'home_university'),
        btrim(p_payload ->> 'title'),
        btrim(p_payload ->> 'summary'),
        btrim(p_payload ->> 'exchange_year'),
        coalesce(p_payload -> 'themes', '[]'::jsonb),
        nullif(btrim(p_payload ->> 'source_url'), ''),
        v_display_name,
        v_identity_mode,
        v_status,
        0,
        v_now,
        v_now
      ) returning * into v_experience;
      v_content := to_jsonb(v_experience);
    end if;

    v_response := jsonb_build_object(
      'status', 'committed',
      'idempotent', false,
      'content_type', v_content_type,
      'content', v_content
    );

    insert into public.exchange_community_mutation_receipts (
      id, operation, request_fingerprint, actor_account_id, actor_identity_id,
      resource_type, resource_id, response, created_at, retained_until
    ) values (
      v_event_id,
      v_operation,
      v_fingerprint,
      v_account_id,
      v_identity_id,
      v_content_type,
      v_content_id,
      v_response,
      v_now,
      v_now + interval '168 hours'
    );
  exception
    when integrity_constraint_violation or data_exception then
      -- The subtransaction rolls back both the rate event and content before
      -- classifying a cross-account event-id race.
      v_replay := public.exchange_community_replay(
        v_event_id,
        v_operation,
        v_fingerprint
      );
      if v_replay is not null then
        return v_replay;
      end if;
      return jsonb_build_object('status', 'integrity_conflict');
  end;

  return v_response;
end;
$$;

create or replace function public.exchange_delete_public_community_content(
  p_event_id text,
  p_content_type text,
  p_content_id text,
  p_account_id text,
  p_identity_id text,
  p_access_token_hash text,
  p_expected_revision bigint
) returns jsonb
language plpgsql
security definer
set search_path = public, pg_temp
as $$
declare
  v_event_id text := nullif(btrim(p_event_id), '');
  v_content_type text := nullif(btrim(p_content_type), '');
  v_content_id text := nullif(btrim(p_content_id), '');
  v_account_id text := nullif(btrim(p_account_id), '');
  v_identity_id text := nullif(btrim(p_identity_id), '');
  v_token_hash text := nullif(btrim(p_access_token_hash), '');
  v_operation text;
  v_fingerprint text;
  v_replay jsonb;
  v_now timestamptz;
  v_parent_post_id text;
  v_deleted_comment_count bigint := 0;
  v_account public.exchange_accounts%rowtype;
  v_identity public.exchange_community_identities%rowtype;
  v_post public.exchange_community_posts%rowtype;
  v_comment public.exchange_community_post_comments%rowtype;
  v_response jsonb;
begin
  if v_event_id is null
     or char_length(v_event_id) > 128
     or v_content_type not in ('post', 'comment')
     or v_content_id is null
     or char_length(v_content_id) > 128
     or v_account_id is null
     or char_length(v_account_id) > 128
     or v_identity_id is null
     or char_length(v_identity_id) > 128
     or v_token_hash is null
     or v_token_hash !~ '^[0-9a-f]{64}$'
     or p_expected_revision is null
     or p_expected_revision < 0 then
    return jsonb_build_object('status', 'invalid_request');
  end if;

  v_operation := 'delete_' || v_content_type;
  v_fingerprint := public.exchange_community_request_fingerprint(
    jsonb_build_array(
      v_operation,
      v_content_id,
      v_account_id,
      v_identity_id,
      v_token_hash,
      p_expected_revision
    )
  );
  v_replay := public.exchange_community_replay(
    v_event_id,
    v_operation,
    v_fingerprint
  );
  if v_replay is not null then
    return v_replay;
  end if;

  -- Fixed lock order: account, identity, optional parent post, target row.
  select account.* into v_account
  from public.exchange_accounts account
  where account.id = v_account_id
  for update;
  if not found then
    return jsonb_build_object('status', 'account_missing');
  end if;

  select identity.* into v_identity
  from public.exchange_community_identities identity
  where identity.id = v_identity_id
  for update;
  if not found then
    return jsonb_build_object('status', 'identity_missing');
  end if;
  if v_identity.account_id is distinct from v_account_id
     or v_identity.access_token_hash is distinct from v_token_hash then
    return jsonb_build_object('status', 'identity_conflict');
  end if;

  v_replay := public.exchange_community_replay(
    v_event_id,
    v_operation,
    v_fingerprint
  );
  if v_replay is not null then
    return v_replay;
  end if;

  v_now := clock_timestamp();
  if v_account.community_suspended_until is not null
     and v_account.community_suspended_until > v_now then
    return jsonb_build_object(
      'status', 'account_suspended',
      'suspended_until', v_account.community_suspended_until
    );
  end if;

  if v_content_type = 'post' then
    select post.* into v_post
    from public.exchange_community_posts post
    where post.id = v_content_id
    for update;
    if not found then
      return jsonb_build_object('status', 'resource_missing');
    end if;
    if v_post.author_identity_id is distinct from v_identity_id then
      return jsonb_build_object('status', 'not_owner');
    end if;
    if v_post.revision <> p_expected_revision then
      return jsonb_build_object(
        'status', 'status_conflict',
        'current_revision', v_post.revision,
        'current_status', v_post.status
      );
    end if;
    select count(*) into v_deleted_comment_count
    from public.exchange_community_post_comments comment
    where comment.post_id = v_post.id;
  else
    -- Read the parent key without taking a child lock, then acquire locks in
    -- parent-before-child order and re-read the target under lock.
    select comment.post_id into v_parent_post_id
    from public.exchange_community_post_comments comment
    where comment.id = v_content_id;
    if not found then
      return jsonb_build_object('status', 'resource_missing');
    end if;

    select post.* into v_post
    from public.exchange_community_posts post
    where post.id = v_parent_post_id
    for update;
    if not found then
      return jsonb_build_object('status', 'resource_missing');
    end if;

    select comment.* into v_comment
    from public.exchange_community_post_comments comment
    where comment.id = v_content_id
      and comment.post_id = v_parent_post_id
    for update;
    if not found then
      return jsonb_build_object('status', 'resource_missing');
    end if;
    if v_comment.author_identity_id is distinct from v_identity_id then
      return jsonb_build_object('status', 'not_owner');
    end if;
    if v_comment.revision <> p_expected_revision then
      return jsonb_build_object(
        'status', 'status_conflict',
        'current_revision', v_comment.revision,
        'current_status', v_comment.status
      );
    end if;
  end if;

  begin
    if v_content_type = 'post' then
      delete from public.exchange_community_posts post
      where post.id = v_content_id;
    else
      delete from public.exchange_community_post_comments comment
      where comment.id = v_content_id;
    end if;

    v_response := jsonb_build_object(
      'status', 'committed',
      'idempotent', false,
      'content_type', v_content_type,
      'resource_id', v_content_id,
      'deleted_comment_count', v_deleted_comment_count,
      'deleted', true
    );

    insert into public.exchange_community_mutation_receipts (
      id, operation, request_fingerprint, actor_account_id, actor_identity_id,
      resource_type, resource_id, response, created_at, retained_until
    ) values (
      v_event_id,
      v_operation,
      v_fingerprint,
      v_account_id,
      v_identity_id,
      v_content_type,
      v_content_id,
      v_response,
      v_now,
      v_now + interval '168 hours'
    );
  exception
    when integrity_constraint_violation or data_exception then
      v_replay := public.exchange_community_replay(
        v_event_id,
        v_operation,
        v_fingerprint
      );
      if v_replay is not null then
        return v_replay;
      end if;
      return jsonb_build_object('status', 'integrity_conflict');
  end;

  return v_response;
end;
$$;

-- Adapter-facing identity mutation.  The JSON shape deliberately supports the
-- legacy unlinked identity contract while keeping publication linked-only.
create or replace function public.exchange_commit_community_identity(
  p_mutation_id text,
  p_request_fingerprint text,
  p_identity jsonb
) returns jsonb
language plpgsql
security definer
set search_path = public, pg_temp
as $$
declare
  v_mutation_id text := nullif(btrim(p_mutation_id), '');
  v_supplied_fingerprint text := nullif(btrim(p_request_fingerprint), '');
  v_identity_id text := nullif(btrim(p_identity ->> 'id'), '');
  v_account_id text := nullif(btrim(p_identity ->> 'account_id'), '');
  v_display_name text := nullif(btrim(p_identity ->> 'display_name'), '');
  v_token_hash text := lower(nullif(btrim(p_identity ->> 'access_token_hash'), ''));
  v_operation constant text := 'identity';
  v_fingerprint text;
  v_replay jsonb;
  v_now timestamptz;
  v_account public.exchange_accounts%rowtype;
  v_identity public.exchange_community_identities%rowtype;
  v_linked_identity public.exchange_community_identities%rowtype;
  v_locked_identity public.exchange_community_identities%rowtype;
  v_response jsonb;
begin
  if v_mutation_id is null
     or char_length(v_mutation_id) not between 16 and 128
     or p_identity is null
     or jsonb_typeof(p_identity) <> 'object'
     or not public.exchange_community_payload_has_only_keys(
       p_identity,
       array['id', 'display_name', 'access_token_hash', 'account_id', 'created_at']
     )
     or v_identity_id is null
     or char_length(v_identity_id) > 128
     or v_display_name is null
     or char_length(v_display_name) not between 2 and 30
     or v_token_hash is null
     or v_token_hash !~ '^[0-9a-f]{64}$'
     or v_supplied_fingerprint is null
     or v_supplied_fingerprint !~ '^[0-9a-f]{64}$' then
    return jsonb_build_object('status', 'integrity_conflict');
  end if;

  v_fingerprint := public.exchange_community_request_fingerprint(
    jsonb_build_object(
      'operation', v_operation,
      'payload', jsonb_build_object(
        'mutation_id', v_mutation_id,
        'identity', p_identity
      )
    )
  );
  if v_supplied_fingerprint is distinct from v_fingerprint then
    return jsonb_build_object('status', 'invalid_request');
  end if;

  v_replay := public.exchange_community_replay(
    v_mutation_id,
    v_operation,
    v_fingerprint
  );
  if v_replay is not null then
    return v_replay;
  end if;

  if v_account_id is not null then
    -- Linked path fixed lock order: account, then identity.
    select account.* into v_account
    from public.exchange_accounts account
    where account.id = v_account_id
    for update;
    if not found then
      return jsonb_build_object('status', 'account_missing');
    end if;

    v_replay := public.exchange_community_replay(
      v_mutation_id,
      v_operation,
      v_fingerprint
    );
    if v_replay is not null then
      return v_replay;
    end if;

    -- Lock every possibly conflicting identity in lexical id order.  This
    -- closes the id-versus-account uniqueness race without reverse row locks.
    for v_locked_identity in
      select identity.*
      from public.exchange_community_identities identity
      where identity.id = v_identity_id
         or identity.account_id = v_account_id
      order by identity.id
      for update
    loop
      if v_locked_identity.id = v_identity_id then
        v_identity := v_locked_identity;
      end if;
      if v_locked_identity.account_id = v_account_id then
        v_linked_identity := v_locked_identity;
      end if;
    end loop;

    if v_identity.id is not null
       and v_identity.account_id is distinct from v_account_id then
      return jsonb_build_object('status', 'identity_conflict');
    end if;
    if v_linked_identity.id is not null then
      -- A concurrent first-login may already have created the one identity
      -- allowed for this account under another candidate id.  Preserve that
      -- stable id and rotate its token, matching the JSONL repository.
      v_identity := v_linked_identity;
    end if;

    v_display_name := nullif(btrim(v_account.profile ->> 'display_name'), '');
    if v_display_name is null or char_length(v_display_name) > 30 then
      return jsonb_build_object('status', 'integrity_conflict');
    end if;
  else
    -- Legacy path has no account row.  It may rotate only its own token and can
    -- never acquire an account binding through this branch.
    select identity.* into v_identity
    from public.exchange_community_identities identity
    where identity.id = v_identity_id
    for update;
    if found and v_identity.account_id is not null then
      return jsonb_build_object('status', 'identity_conflict');
    end if;

    v_replay := public.exchange_community_replay(
      v_mutation_id,
      v_operation,
      v_fingerprint
    );
    if v_replay is not null then
      return v_replay;
    end if;
  end if;

  v_now := clock_timestamp();
  begin
    if v_identity.id is not null then
      update public.exchange_community_identities identity
      set display_name = v_display_name,
          access_token_hash = v_token_hash,
          updated_at = v_now
      where identity.id = v_identity.id
      returning * into v_identity;
    else
      insert into public.exchange_community_identities (
        id, account_id, display_name, access_token_hash, created_at, updated_at
      ) values (
        v_identity_id,
        v_account_id,
        v_display_name,
        v_token_hash,
        v_now,
        v_now
      ) returning * into v_identity;
    end if;

    v_response := jsonb_build_object(
      'status', 'committed',
      'idempotent', false,
      'identity', to_jsonb(v_identity) - 'updated_at'
    );

    insert into public.exchange_community_mutation_receipts (
      id, operation, request_fingerprint, actor_account_id, actor_identity_id,
      resource_type, resource_id, response, created_at, retained_until
    ) values (
      v_mutation_id,
      v_operation,
      v_fingerprint,
      v_account_id,
      v_identity.id,
      'identity',
      v_identity.id,
      v_response,
      v_now,
      v_now + interval '168 hours'
    );
  exception
    when integrity_constraint_violation or data_exception then
      v_replay := public.exchange_community_replay(
        v_mutation_id,
        v_operation,
        v_fingerprint
      );
      if v_replay is not null then
        return v_replay;
      end if;
      return jsonb_build_object('status', 'identity_conflict');
  end;

  return v_response;
end;
$$;

-- This overload is defined last, so harden and expose it only after the fresh
-- migration can resolve its exact signature.
revoke all on function public.exchange_commit_community_identity(
  text, text, jsonb
) from public, anon, authenticated, service_role;
grant execute on function public.exchange_commit_community_identity(
  text, text, jsonb
) to service_role;
