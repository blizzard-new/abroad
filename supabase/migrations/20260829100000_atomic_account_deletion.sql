-- Atomic account deletion and durable encrypted-Storage cleanup handoff.
--
-- PostgreSQL owns every relational delete/de-identification step.  Encrypted
-- objects live behind the Supabase Storage API, so their keys are captured in
-- the durable receipt before account metadata cascades.  The API deletes those
-- objects after commit and acknowledges completion through a second RPC.

create table public.exchange_account_deletion_receipts (
  mutation_id text primary key,
  request_fingerprint text not null,
  replay_proof text not null,
  response jsonb not null,
  storage_completed_at timestamptz,
  created_at timestamptz not null default now(),
  retained_until timestamptz not null,
  constraint exchange_account_deletion_receipts_id_shape
    check (char_length(btrim(mutation_id)) between 16 and 128),
  constraint exchange_account_deletion_receipts_fingerprint_shape
    check (request_fingerprint ~ '^[0-9a-f]{64}$'),
  constraint exchange_account_deletion_receipts_replay_shape
    check (replay_proof ~ '^[0-9a-f]{64}$'),
  constraint exchange_account_deletion_receipts_response_object
    check (jsonb_typeof(response) = 'object'),
  constraint exchange_account_deletion_receipts_retention
    check (retained_until = created_at + interval '168 hours'),
  constraint exchange_account_deletion_receipts_completion_order
    check (storage_completed_at is null or storage_completed_at >= created_at)
);

create unique index exchange_account_deletion_receipts_replay_idx
  on public.exchange_account_deletion_receipts (replay_proof);
create index exchange_account_deletion_receipts_pending_storage_idx
  on public.exchange_account_deletion_receipts (created_at)
  where storage_completed_at is null;
create index exchange_account_deletion_receipts_retention_idx
  on public.exchange_account_deletion_receipts (retained_until)
  where storage_completed_at is not null;

create or replace function public.exchange_account_deletion_replay_proof(
  p_session_token_hash text
) returns text
language sql
immutable
strict
set search_path = public, pg_temp
as $$
  select public.exchange_community_request_fingerprint(
    jsonb_build_object(
      'purpose', 'account_deletion_replay',
      'session_token_hash', lower(btrim(p_session_token_hash))
    )
  );
$$;

create or replace function public.exchange_account_deletion_replay(
  p_mutation_id text,
  p_request_fingerprint text,
  p_replay_proof text
) returns jsonb
language plpgsql
security definer
set search_path = public, pg_temp
as $$
declare
  v_receipt public.exchange_account_deletion_receipts%rowtype;
begin
  select receipt.* into v_receipt
  from public.exchange_account_deletion_receipts receipt
  where receipt.mutation_id = p_mutation_id;

  if not found then
    return null;
  end if;
  if v_receipt.request_fingerprint is distinct from p_request_fingerprint
     or v_receipt.replay_proof is distinct from p_replay_proof then
    return jsonb_build_object('status', 'idempotency_conflict');
  end if;
  return v_receipt.response || jsonb_build_object('idempotent', true);
end;
$$;

create or replace function public.exchange_commit_account_deletion(
  p_mutation_id text,
  p_request_fingerprint text,
  p_account_id text,
  p_session_id text,
  p_session_token_hash text,
  p_email_fingerprint text,
  p_pending_report_retention_days integer,
  p_replacement_name text
) returns jsonb
language plpgsql
security definer
set search_path = public, pg_temp
as $$
declare
  v_mutation_id text := nullif(btrim(p_mutation_id), '');
  v_fingerprint text := lower(nullif(btrim(p_request_fingerprint), ''));
  v_account_id text := nullif(btrim(p_account_id), '');
  v_session_id text := nullif(btrim(p_session_id), '');
  v_session_token_hash text := lower(nullif(btrim(p_session_token_hash), ''));
  v_email_fingerprint text := lower(nullif(btrim(p_email_fingerprint), ''));
  v_replacement_name text := nullif(btrim(p_replacement_name), '');
  v_expected_fingerprint text;
  v_replay_proof text;
  v_replay jsonb;
  v_now timestamptz := clock_timestamp();
  v_account public.exchange_accounts%rowtype;
  v_session public.exchange_account_sessions%rowtype;
  v_storage_object_keys jsonb := '[]'::jsonb;
  v_identity_count bigint := 0;
  v_public_count bigint := 0;
  v_private_conversation_count bigint := 0;
  v_private_message_count bigint := 0;
  v_block_count bigint := 0;
  v_pending_report_count bigint := 0;
  v_closed_report_count bigint := 0;
  v_community_receipt_count bigint := 0;
  v_email_challenge_count bigint := 0;
  v_count bigint := 0;
  v_response jsonb;
begin
  if v_mutation_id is null
     or char_length(v_mutation_id) not between 16 and 128
     or v_fingerprint is null
     or v_fingerprint !~ '^[0-9a-f]{64}$'
     or v_session_token_hash is null
     or v_session_token_hash !~ '^[0-9a-f]{64}$'
     or (
       v_email_fingerprint is not null
       and v_email_fingerprint !~ '^[0-9a-f]{64}$'
     )
     or p_pending_report_retention_days not between 1 and 365
     or v_replacement_name is null
     or char_length(v_replacement_name) not between 2 and 30 then
    return jsonb_build_object('status', 'invalid_request');
  end if;

  v_expected_fingerprint := public.exchange_community_request_fingerprint(
    jsonb_build_object(
      'operation', 'account_deletion',
      'payload', jsonb_build_object(
        'mutation_id', v_mutation_id,
        'pending_report_retention_days', p_pending_report_retention_days,
        'replacement_name', v_replacement_name,
        'session_token_hash', v_session_token_hash
      )
    )
  );
  if v_fingerprint is distinct from v_expected_fingerprint then
    return jsonb_build_object('status', 'invalid_request');
  end if;

  v_replay_proof := public.exchange_account_deletion_replay_proof(
    v_session_token_hash
  );
  v_replay := public.exchange_account_deletion_replay(
    v_mutation_id,
    v_fingerprint,
    v_replay_proof
  );
  if v_replay is not null then
    return v_replay;
  end if;

  -- A missing actor shape is permitted only for a replay after the account and
  -- session have already been removed by the first committed request.
  if v_account_id is null or v_session_id is null then
    return jsonb_build_object('status', 'session_invalid');
  end if;
  if char_length(v_account_id) > 128 or char_length(v_session_id) > 128 then
    return jsonb_build_object('status', 'invalid_request');
  end if;

  -- All account-owned mutation paths use account first.  Locking it before the
  -- session and ordered identities keeps deletion compatible with those paths.
  select account.* into v_account
  from public.exchange_accounts account
  where account.id = v_account_id
  for update;
  if not found then
    v_replay := public.exchange_account_deletion_replay(
      v_mutation_id,
      v_fingerprint,
      v_replay_proof
    );
    if v_replay is not null then
      return v_replay;
    end if;
    return jsonb_build_object('status', 'account_missing');
  end if;

  select session.* into v_session
  from public.exchange_account_sessions session
  where session.id = v_session_id
    and session.account_id = v_account_id
    and session.token_hash = v_session_token_hash
    and session.expires_at > v_now
  for update;
  if not found then
    return jsonb_build_object('status', 'session_invalid');
  end if;

  perform identity.id
  from public.exchange_community_identities identity
  where identity.account_id = v_account_id
  order by identity.id
  for update;

  select count(*) into v_identity_count
  from public.exchange_community_identities identity
  where identity.account_id = v_account_id;

  select coalesce(
    jsonb_agg(to_jsonb(version.object_key) order by version.object_key),
    '[]'::jsonb
  ) into v_storage_object_keys
  from public.exchange_vault_versions version
  where version.account_id = v_account_id;

  update public.exchange_community_questions question
  set author_identity_id = null,
      display_name = v_replacement_name,
      identity_mode = 'anonymous',
      revision = question.revision + 1,
      updated_at = v_now
  where question.author_identity_id in (
    select identity.id
    from public.exchange_community_identities identity
    where identity.account_id = v_account_id
  );
  get diagnostics v_count = row_count;
  v_public_count := v_public_count + v_count;

  update public.exchange_community_answers answer
  set author_identity_id = null,
      display_name = v_replacement_name,
      identity_mode = 'anonymous',
      revision = answer.revision + 1,
      updated_at = v_now
  where answer.author_identity_id in (
    select identity.id
    from public.exchange_community_identities identity
    where identity.account_id = v_account_id
  );
  get diagnostics v_count = row_count;
  v_public_count := v_public_count + v_count;

  update public.exchange_community_posts post
  set author_identity_id = null,
      display_name = v_replacement_name,
      identity_mode = 'anonymous',
      revision = post.revision + 1,
      updated_at = v_now
  where post.author_identity_id in (
    select identity.id
    from public.exchange_community_identities identity
    where identity.account_id = v_account_id
  );
  get diagnostics v_count = row_count;
  v_public_count := v_public_count + v_count;

  update public.exchange_community_post_comments comment
  set author_identity_id = null,
      display_name = v_replacement_name,
      identity_mode = 'anonymous',
      revision = comment.revision + 1,
      updated_at = v_now
  where comment.author_identity_id in (
    select identity.id
    from public.exchange_community_identities identity
    where identity.account_id = v_account_id
  );
  get diagnostics v_count = row_count;
  v_public_count := v_public_count + v_count;

  update public.exchange_community_public_chat_messages chat
  set author_identity_id = null,
      display_name = v_replacement_name,
      identity_mode = 'anonymous',
      revision = chat.revision + 1,
      updated_at = v_now
  where chat.author_identity_id in (
    select identity.id
    from public.exchange_community_identities identity
    where identity.account_id = v_account_id
  );
  get diagnostics v_count = row_count;
  v_public_count := v_public_count + v_count;

  update public.exchange_community_experience_submissions experience
  set author_identity_id = null,
      display_name = v_replacement_name,
      identity_mode = 'anonymous',
      source_url = null,
      revision = experience.revision + 1,
      updated_at = v_now
  where experience.author_identity_id in (
    select identity.id
    from public.exchange_community_identities identity
    where identity.account_id = v_account_id
  );
  get diagnostics v_count = row_count;
  v_public_count := v_public_count + v_count;

  select count(*) into v_private_message_count
  from public.exchange_community_private_messages message
  join public.exchange_community_private_conversations conversation
    on conversation.id = message.conversation_id
  where conversation.sender_id in (
      select identity.id from public.exchange_community_identities identity
      where identity.account_id = v_account_id
    )
    or conversation.recipient_id in (
      select identity.id from public.exchange_community_identities identity
      where identity.account_id = v_account_id
    );

  delete from public.exchange_community_private_conversations conversation
  where conversation.sender_id in (
      select identity.id from public.exchange_community_identities identity
      where identity.account_id = v_account_id
    )
    or conversation.recipient_id in (
      select identity.id from public.exchange_community_identities identity
      where identity.account_id = v_account_id
    );
  get diagnostics v_private_conversation_count = row_count;

  delete from public.exchange_community_blocks block
  where block.owner_id in (
      select identity.id from public.exchange_community_identities identity
      where identity.account_id = v_account_id
    )
    or block.target_id in (
      select identity.id from public.exchange_community_identities identity
      where identity.account_id = v_account_id
    );
  get diagnostics v_block_count = row_count;

  update public.exchange_community_reports report
  set reporter_id = null,
      retained_until = v_now + make_interval(
        days => p_pending_report_retention_days
      ),
      revision = report.revision + 1
  where report.status = 'pending'
    and report.reporter_id in (
      select identity.id from public.exchange_community_identities identity
      where identity.account_id = v_account_id
    );
  get diagnostics v_pending_report_count = row_count;

  delete from public.exchange_community_reports report
  where report.reporter_id in (
    select identity.id from public.exchange_community_identities identity
    where identity.account_id = v_account_id
  );
  get diagnostics v_closed_report_count = row_count;

  -- Mutation receipts can contain private message/report response payloads.
  -- Removing only actor-owned receipts avoids retaining that private snapshot
  -- after their identity and account foreign keys become NULL.
  delete from public.exchange_community_mutation_receipts receipt
  where receipt.actor_account_id = v_account_id
     or receipt.actor_identity_id in (
       select identity.id from public.exchange_community_identities identity
       where identity.account_id = v_account_id
     );
  get diagnostics v_community_receipt_count = row_count;

  if v_email_fingerprint is not null then
    delete from public.exchange_email_verifications challenge
    where challenge.email_fingerprint = v_email_fingerprint;
    get diagnostics v_email_challenge_count = row_count;
  end if;

  -- Remaining account-owned rows use ON DELETE CASCADE or SET NULL.  The
  -- public author projections and private report retention rules were handled
  -- explicitly above before identities disappear.
  delete from public.exchange_accounts account
  where account.id = v_account_id;
  if not found then
    return jsonb_build_object('status', 'account_missing');
  end if;

  v_response := jsonb_build_object(
    'status', 'committed',
    'idempotent', false,
    'storage_object_keys', v_storage_object_keys,
    'counts', jsonb_build_object(
      'identity', v_identity_count,
      'public_content', v_public_count,
      'private_conversation', v_private_conversation_count,
      'private_message', v_private_message_count,
      'block', v_block_count,
      'pending_report_deidentified', v_pending_report_count,
      'closed_report_deleted', v_closed_report_count,
      'community_receipt', v_community_receipt_count,
      'email_challenge', v_email_challenge_count
    )
  );

  insert into public.exchange_account_deletion_receipts (
    mutation_id,
    request_fingerprint,
    replay_proof,
    response,
    created_at,
    retained_until
  ) values (
    v_mutation_id,
    v_fingerprint,
    v_replay_proof,
    v_response,
    v_now,
    v_now + interval '168 hours'
  );
  return v_response;
exception
  when unique_violation then
    v_replay := public.exchange_account_deletion_replay(
      v_mutation_id,
      v_fingerprint,
      v_replay_proof
    );
    if v_replay is not null then
      return v_replay;
    end if;
    return jsonb_build_object('status', 'integrity_conflict');
  when integrity_constraint_violation or data_exception then
    return jsonb_build_object('status', 'integrity_conflict');
end;
$$;

create or replace function public.exchange_complete_account_deletion_storage(
  p_mutation_id text,
  p_session_token_hash text
) returns jsonb
language plpgsql
security definer
set search_path = public, pg_temp
as $$
declare
  v_mutation_id text := nullif(btrim(p_mutation_id), '');
  v_session_token_hash text := lower(nullif(btrim(p_session_token_hash), ''));
  v_replay_proof text;
  v_receipt public.exchange_account_deletion_receipts%rowtype;
begin
  if v_mutation_id is null
     or char_length(v_mutation_id) not between 16 and 128
     or v_session_token_hash is null
     or v_session_token_hash !~ '^[0-9a-f]{64}$' then
    return jsonb_build_object('status', 'invalid_request');
  end if;
  v_replay_proof := public.exchange_account_deletion_replay_proof(
    v_session_token_hash
  );
  select receipt.* into v_receipt
  from public.exchange_account_deletion_receipts receipt
  where receipt.mutation_id = v_mutation_id
  for update;
  if not found then
    return jsonb_build_object('status', 'receipt_missing');
  end if;
  if v_receipt.replay_proof is distinct from v_replay_proof then
    return jsonb_build_object('status', 'idempotency_conflict');
  end if;
  update public.exchange_account_deletion_receipts receipt
  set storage_completed_at = coalesce(receipt.storage_completed_at, clock_timestamp())
  where receipt.mutation_id = v_mutation_id;
  return jsonb_build_object('status', 'committed');
end;
$$;

create or replace function public.exchange_purge_account_deletion_receipts()
returns jsonb
language plpgsql
security definer
set search_path = public, pg_temp
as $$
declare
  v_count bigint;
begin
  delete from public.exchange_account_deletion_receipts receipt
  where receipt.storage_completed_at is not null
    and receipt.retained_until <= clock_timestamp();
  get diagnostics v_count = row_count;
  return jsonb_build_object('status', 'committed', 'receipts', v_count);
end;
$$;

create or replace function public.exchange_list_pending_account_deletion_storage(
  p_limit integer default 100
) returns jsonb
language plpgsql
security definer
set search_path = public, pg_temp
as $$
declare
  v_jobs jsonb;
begin
  if p_limit not between 1 and 500 then
    return jsonb_build_object('status', 'invalid_request', 'jobs', '[]'::jsonb);
  end if;
  select coalesce(
    jsonb_agg(
      jsonb_build_object(
        'mutation_id', pending.mutation_id,
        'storage_object_keys', pending.response -> 'storage_object_keys'
      ) order by pending.created_at, pending.mutation_id
    ),
    '[]'::jsonb
  ) into v_jobs
  from (
    select receipt.mutation_id, receipt.response, receipt.created_at
    from public.exchange_account_deletion_receipts receipt
    where receipt.storage_completed_at is null
    order by receipt.created_at, receipt.mutation_id
    limit p_limit
  ) pending;
  return jsonb_build_object('status', 'committed', 'jobs', v_jobs);
end;
$$;

create or replace function public.exchange_complete_pending_account_deletion_storage(
  p_mutation_id text
) returns jsonb
language plpgsql
security definer
set search_path = public, pg_temp
as $$
declare
  v_mutation_id text := nullif(btrim(p_mutation_id), '');
begin
  if v_mutation_id is null
     or char_length(v_mutation_id) not between 16 and 128 then
    return jsonb_build_object('status', 'invalid_request');
  end if;
  update public.exchange_account_deletion_receipts receipt
  set storage_completed_at = coalesce(receipt.storage_completed_at, clock_timestamp())
  where receipt.mutation_id = v_mutation_id;
  if not found then
    return jsonb_build_object('status', 'receipt_missing');
  end if;
  return jsonb_build_object('status', 'committed');
end;
$$;

alter table public.exchange_account_deletion_receipts enable row level security;
alter table public.exchange_account_deletion_receipts force row level security;

revoke all on table public.exchange_account_deletion_receipts
  from public, anon, authenticated, service_role;
revoke all on function public.exchange_account_deletion_replay_proof(text)
  from public, anon, authenticated;
revoke all on function public.exchange_account_deletion_replay(text, text, text)
  from public, anon, authenticated;
revoke all on function public.exchange_commit_account_deletion(
  text, text, text, text, text, text, integer, text
) from public, anon, authenticated;
revoke all on function public.exchange_complete_account_deletion_storage(text, text)
  from public, anon, authenticated;
revoke all on function public.exchange_purge_account_deletion_receipts()
  from public, anon, authenticated;
revoke all on function public.exchange_list_pending_account_deletion_storage(integer)
  from public, anon, authenticated;
revoke all on function public.exchange_complete_pending_account_deletion_storage(text)
  from public, anon, authenticated;

grant execute on function public.exchange_commit_account_deletion(
  text, text, text, text, text, text, integer, text
) to service_role;
grant execute on function public.exchange_complete_account_deletion_storage(text, text)
  to service_role;
grant execute on function public.exchange_purge_account_deletion_receipts()
  to service_role;
grant execute on function public.exchange_list_pending_account_deletion_storage(integer)
  to service_role;
grant execute on function public.exchange_complete_pending_account_deletion_storage(text)
  to service_role;

-- Account deletion now has one audited transaction boundary.  Production code
-- can no longer bypass it with a direct PostgREST DELETE.
revoke delete on table public.exchange_accounts from service_role;
