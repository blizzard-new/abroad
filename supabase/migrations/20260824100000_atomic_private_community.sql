-- Atomic private-community persistence for conversations, messages, blocks,
-- reports, and report moderation.  This migration depends on the account,
-- suspension, and public-community migrations from 2026-08-23.

create table public.exchange_community_private_conversations (
  id text primary key,
  school_name text not null,
  sender_id text not null
    references public.exchange_community_identities(id) on delete cascade,
  sender_name text not null,
  recipient_id text not null
    references public.exchange_community_identities(id) on delete cascade,
  recipient_name text not null,
  status text not null default 'pending',
  revision bigint not null default 1,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  constraint exchange_private_conversations_id_shape
    check (btrim(id) <> '' and char_length(id) <= 128),
  constraint exchange_private_conversations_school_length
    check (char_length(btrim(school_name)) between 2 and 200),
  constraint exchange_private_conversations_names
    check (
      char_length(btrim(sender_name)) between 1 and 120
      and char_length(btrim(recipient_name)) between 1 and 120
    ),
  constraint exchange_private_conversations_distinct_participants
    check (sender_id <> recipient_id),
  constraint exchange_private_conversations_status
    check (status in ('pending', 'accepted', 'declined')),
  constraint exchange_private_conversations_revision
    check (revision > 0),
  constraint exchange_private_conversations_timestamps
    check (updated_at >= created_at)
);

create table public.exchange_community_private_messages (
  id text primary key,
  conversation_id text not null
    references public.exchange_community_private_conversations(id)
    on delete cascade,
  author_id text not null
    references public.exchange_community_identities(id) on delete cascade,
  display_name text not null,
  body text not null,
  created_at timestamptz not null default now(),
  constraint exchange_private_messages_id_shape
    check (btrim(id) <> '' and char_length(id) <= 128),
  constraint exchange_private_messages_display_name
    check (char_length(btrim(display_name)) between 1 and 120),
  constraint exchange_private_messages_body
    check (char_length(btrim(body)) between 2 and 1000)
);

create table public.exchange_community_blocks (
  id text primary key,
  owner_id text not null
    references public.exchange_community_identities(id) on delete cascade,
  target_id text not null
    references public.exchange_community_identities(id) on delete cascade,
  created_at timestamptz not null default now(),
  constraint exchange_community_blocks_id_shape
    check (btrim(id) <> '' and char_length(id) <= 128),
  constraint exchange_community_blocks_distinct_participants
    check (owner_id <> target_id),
  constraint exchange_community_blocks_owner_target_unique
    unique (owner_id, target_id)
);

create table public.exchange_community_reports (
  id text primary key,
  reporter_id text
    references public.exchange_community_identities(id) on delete set null,
  resource_type text not null,
  resource_id text not null,
  reason text not null,
  status text not null default 'pending',
  reviewed_by text references public.exchange_accounts(id) on delete set null,
  reviewed_at timestamptz,
  resolution_note text,
  retained_until timestamptz,
  revision bigint not null default 1,
  created_at timestamptz not null default now(),
  constraint exchange_community_reports_id_shape
    check (btrim(id) <> '' and char_length(id) <= 128),
  constraint exchange_community_reports_resource_type
    check (resource_type in ('post', 'comment', 'chat', 'message')),
  constraint exchange_community_reports_resource_id
    check (btrim(resource_id) <> '' and char_length(resource_id) <= 128),
  constraint exchange_community_reports_reason
    check (char_length(btrim(reason)) between 4 and 300),
  constraint exchange_community_reports_status
    check (status in ('pending', 'resolved', 'dismissed')),
  constraint exchange_community_reports_review_shape
    check (
      (status = 'pending' and reviewed_at is null and resolution_note is null)
      or (
        status in ('resolved', 'dismissed')
        and reviewed_at is not null
        and char_length(btrim(resolution_note)) between 2 and 500
      )
    ),
  constraint exchange_community_reports_retention_shape
    check (retained_until is null or retained_until > created_at),
  constraint exchange_community_reports_revision
    check (revision > 0)
);

create index exchange_private_conversations_sender_idx
  on public.exchange_community_private_conversations (sender_id, updated_at desc);
create index exchange_private_conversations_recipient_idx
  on public.exchange_community_private_conversations (recipient_id, updated_at desc);
create index exchange_private_messages_conversation_idx
  on public.exchange_community_private_messages (conversation_id, created_at);
create index exchange_private_messages_author_idx
  on public.exchange_community_private_messages (author_id, created_at);
create index exchange_community_blocks_target_idx
  on public.exchange_community_blocks (target_id, created_at);
create index exchange_community_reports_status_idx
  on public.exchange_community_reports (status, created_at desc);
create index exchange_community_reports_reporter_idx
  on public.exchange_community_reports (reporter_id, created_at desc);
create index exchange_community_reports_reviewer_idx
  on public.exchange_community_reports (reviewed_by, reviewed_at desc);
create index exchange_community_reports_retention_idx
  on public.exchange_community_reports (retained_until)
  where retained_until is not null;
create unique index exchange_community_reports_pending_unique
  on public.exchange_community_reports (reporter_id, resource_type, resource_id)
  where status = 'pending' and reporter_id is not null;

alter table public.exchange_community_mutation_receipts
  drop constraint exchange_community_mutation_receipts_operation_shape;
alter table public.exchange_community_mutation_receipts
  add constraint exchange_community_mutation_receipts_operation_shape
  check (operation ~ '^(identity|legacy_identity|publish_(question|answer|post|comment|chat|experience)|delete_(post|comment)|moderate_(question|answer|post|comment|chat|experience)|anonymize_public_author|private_conversation|private_conversation_status|private_message|community_block|community_report|community_report_review|purge_private_identity)$');

alter table public.exchange_community_moderation_audits
  drop constraint exchange_community_moderation_audits_resource_type,
  drop constraint exchange_community_moderation_audits_previous_status,
  drop constraint exchange_community_moderation_audits_new_status;
alter table public.exchange_community_moderation_audits
  add constraint exchange_community_moderation_audits_resource_type
    check (resource_type in (
      'question', 'answer', 'post', 'comment', 'chat', 'experience', 'report'
    )),
  add constraint exchange_community_moderation_audits_previous_status
    check (
      (resource_type = 'report' and previous_status = 'pending')
      or (
        resource_type <> 'report'
        and previous_status in ('pending', 'approved', 'hidden')
      )
    ),
  add constraint exchange_community_moderation_audits_new_status
    check (
      (resource_type = 'report' and new_status in ('resolved', 'dismissed'))
      or (
        resource_type <> 'report'
        and new_status in ('approved', 'hidden')
      )
    );

create or replace function public.exchange_commit_private_community_mutation(
  p_mutation_id text,
  p_request_fingerprint text,
  p_operation text,
  p_payload jsonb
) returns jsonb
language plpgsql
security definer
set search_path = public, pg_temp
as $$
declare
  v_mutation_id text := nullif(btrim(p_mutation_id), '');
  v_fingerprint text := lower(nullif(btrim(p_request_fingerprint), ''));
  v_operation text := nullif(btrim(p_operation), '');
  v_expected_fingerprint text;
  v_semantic_payload jsonb := p_payload;
  v_replay jsonb;
  v_now timestamptz := clock_timestamp();
  v_account_id text := nullif(btrim(p_payload ->> 'account_id'), '');
  v_identity_id text := nullif(btrim(p_payload ->> 'identity_id'), '');
  v_token_hash text := lower(nullif(btrim(p_payload ->> 'access_token_hash'), ''));
  v_recipient_id text;
  v_conversation_id text;
  v_resource_type text;
  v_resource_id text;
  v_author_id text;
  v_target_id text;
  v_report_id text;
  v_expected_status text;
  v_status text;
  v_note text;
  v_pair_identity_id text;
  v_first_identity_id text;
  v_second_identity_id text;
  v_account public.exchange_accounts%rowtype;
  v_identity public.exchange_community_identities%rowtype;
  v_recipient public.exchange_community_identities%rowtype;
  v_conversation public.exchange_community_private_conversations%rowtype;
  v_message public.exchange_community_private_messages%rowtype;
  v_block public.exchange_community_blocks%rowtype;
  v_report public.exchange_community_reports%rowtype;
  v_audit public.exchange_community_moderation_audits%rowtype;
  v_response jsonb;
begin
  if v_mutation_id is null
     or char_length(v_mutation_id) not between 16 and 128
     or v_fingerprint is null
     or v_fingerprint !~ '^[0-9a-f]{64}$'
     or v_operation not in (
       'private_conversation', 'private_conversation_status',
       'private_message', 'community_block', 'community_report',
       'community_report_review'
     )
     or jsonb_typeof(p_payload) <> 'object' then
    return jsonb_build_object('status', 'integrity_conflict');
  end if;

  if v_operation = 'private_conversation' then
    v_semantic_payload := jsonb_set(
      jsonb_set(
        p_payload,
        '{conversation}',
        coalesce(p_payload -> 'conversation', '{}'::jsonb)
          - 'id' - 'sender_name' - 'recipient_name' - 'status'
          - 'created_at' - 'updated_at'
      ),
      '{initial_message}',
      coalesce(p_payload -> 'initial_message', '{}'::jsonb)
        - 'id' - 'conversation_id' - 'display_name' - 'created_at'
    );
  elsif v_operation = 'private_message' then
    v_semantic_payload := jsonb_set(
      p_payload,
      '{message}',
      coalesce(p_payload -> 'message', '{}'::jsonb)
        - 'id' - 'display_name' - 'created_at'
    );
  elsif v_operation = 'community_block' then
    v_semantic_payload := jsonb_set(
      p_payload,
      '{block}',
      coalesce(p_payload -> 'block', '{}'::jsonb) - 'id' - 'created_at'
    );
  elsif v_operation = 'community_report' then
    v_semantic_payload := jsonb_set(
      p_payload,
      '{report}',
      coalesce(p_payload -> 'report', '{}'::jsonb)
        - 'id' - 'status' - 'reviewed_by' - 'reviewed_at'
        - 'resolution_note' - 'retained_until' - 'created_at'
    );
  end if;

  v_expected_fingerprint := public.exchange_community_request_fingerprint(
    jsonb_build_object('operation', v_operation, 'payload', v_semantic_payload)
  );
  if v_fingerprint is distinct from v_expected_fingerprint then
    return jsonb_build_object('status', 'invalid_request');
  end if;

  v_replay := public.exchange_community_replay(
    v_mutation_id, v_operation, v_fingerprint
  );
  if v_replay is not null then
    return v_replay;
  end if;

  if v_operation = 'community_report_review' then
    v_account_id := nullif(btrim(p_payload ->> 'moderator_id'), '');
  end if;
  if v_account_id is null or char_length(v_account_id) > 128 then
    return jsonb_build_object('status', 'integrity_conflict');
  end if;

  select account.* into v_account
  from public.exchange_accounts account
  where account.id = v_account_id
  for update;
  if not found then
    return jsonb_build_object('status', 'account_missing');
  end if;

  v_replay := public.exchange_community_replay(
    v_mutation_id, v_operation, v_fingerprint
  );
  if v_replay is not null then
    return v_replay;
  end if;

  if v_operation <> 'community_report_review' then
    if v_identity_id is null
       or char_length(v_identity_id) > 128
       or v_token_hash is null
       or v_token_hash !~ '^[0-9a-f]{64}$' then
      return jsonb_build_object('status', 'integrity_conflict');
    end if;
    if v_operation = 'private_conversation' then
      v_pair_identity_id := nullif(
        btrim(p_payload ->> 'recipient_identity_id'), ''
      );
    elsif v_operation = 'community_block' then
      v_pair_identity_id := nullif(btrim(p_payload #>> '{block,target_id}'), '');
    end if;
    v_first_identity_id := least(v_identity_id, coalesce(v_pair_identity_id, v_identity_id));
    v_second_identity_id := greatest(v_identity_id, coalesce(v_pair_identity_id, v_identity_id));
    perform pg_advisory_xact_lock(
      hashtextextended('exchange.private.identity:' || v_first_identity_id, 0)
    );
    if v_second_identity_id <> v_first_identity_id then
      perform pg_advisory_xact_lock(
        hashtextextended('exchange.private.identity:' || v_second_identity_id, 0)
      );
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
    if v_account.community_suspended_until is not null
       and v_account.community_suspended_until > v_now then
      return jsonb_build_object('status', 'account_suspended');
    end if;
  end if;

  if v_operation = 'private_conversation' then
    v_recipient_id := nullif(btrim(p_payload ->> 'recipient_identity_id'), '');
    v_conversation_id := nullif(btrim(p_payload #>> '{conversation,id}'), '');
    if v_recipient_id is null
       or v_recipient_id = v_identity_id
       or v_conversation_id is null
       or p_payload #>> '{conversation,sender_id}' is distinct from v_identity_id
       or p_payload #>> '{conversation,recipient_id}' is distinct from v_recipient_id
       or p_payload #>> '{conversation,status}' is distinct from 'pending'
       or p_payload #>> '{initial_message,conversation_id}' is distinct from v_conversation_id
       or p_payload #>> '{initial_message,author_id}' is distinct from v_identity_id then
      return jsonb_build_object('status', 'integrity_conflict');
    end if;
    select identity.* into v_recipient
    from public.exchange_community_identities identity
    where identity.id = v_recipient_id
      and identity.account_id is not null
    for update;
    if not found then
      return jsonb_build_object('status', 'recipient_missing');
    end if;
    if exists (
      select 1 from public.exchange_community_blocks block
      where (block.owner_id = v_identity_id and block.target_id = v_recipient_id)
         or (block.owner_id = v_recipient_id and block.target_id = v_identity_id)
    ) then
      return jsonb_build_object('status', 'blocked');
    end if;
    insert into public.exchange_community_private_conversations (
      id, school_name, sender_id, sender_name, recipient_id, recipient_name,
      status, revision, created_at, updated_at
    ) values (
      v_conversation_id,
      btrim(p_payload #>> '{conversation,school_name}'),
      v_identity_id,
      v_identity.display_name,
      v_recipient_id,
      v_recipient.display_name,
      'pending', 1, v_now, v_now
    ) returning * into v_conversation;
    insert into public.exchange_community_private_messages (
      id, conversation_id, author_id, display_name, body, created_at
    ) values (
      btrim(p_payload #>> '{initial_message,id}'),
      v_conversation_id,
      v_identity_id,
      v_identity.display_name,
      btrim(p_payload #>> '{initial_message,body}'),
      v_now
    ) returning * into v_message;
    v_resource_type := 'private_conversation';
    v_resource_id := v_conversation_id;
    v_response := jsonb_build_object(
      'status', 'committed', 'idempotent', false,
      'conversation', to_jsonb(v_conversation),
      'message', to_jsonb(v_message)
    );

  elsif v_operation = 'private_conversation_status' then
    v_conversation_id := nullif(btrim(p_payload ->> 'conversation_id'), '');
    v_expected_status := nullif(btrim(p_payload ->> 'expected_status'), '');
    v_status := nullif(btrim(p_payload ->> 'status'), '');
    if v_expected_status <> 'pending' or v_status <> 'accepted' then
      return jsonb_build_object('status', 'integrity_conflict');
    end if;
    select conversation.* into v_conversation
    from public.exchange_community_private_conversations conversation
    where conversation.id = v_conversation_id
    for update;
    if not found then
      return jsonb_build_object('status', 'conversation_missing');
    end if;
    if v_conversation.recipient_id <> v_identity_id then
      return jsonb_build_object('status', 'recipient_only');
    end if;
    if exists (
      select 1 from public.exchange_community_blocks block
      where (block.owner_id = v_conversation.sender_id and block.target_id = v_conversation.recipient_id)
         or (block.owner_id = v_conversation.recipient_id and block.target_id = v_conversation.sender_id)
    ) then
      return jsonb_build_object('status', 'blocked');
    end if;
    if v_conversation.status <> v_expected_status then
      return jsonb_build_object(
        'status', 'status_conflict', 'conversation', to_jsonb(v_conversation)
      );
    end if;
    update public.exchange_community_private_conversations conversation
    set status = v_status, revision = conversation.revision + 1, updated_at = v_now
    where conversation.id = v_conversation_id
    returning * into v_conversation;
    v_resource_type := 'private_conversation';
    v_resource_id := v_conversation_id;
    v_response := jsonb_build_object(
      'status', 'committed', 'idempotent', false,
      'conversation', to_jsonb(v_conversation)
    );

  elsif v_operation = 'private_message' then
    v_conversation_id := nullif(btrim(p_payload #>> '{message,conversation_id}'), '');
    if p_payload #>> '{message,author_id}' is distinct from v_identity_id then
      return jsonb_build_object('status', 'integrity_conflict');
    end if;
    select conversation.* into v_conversation
    from public.exchange_community_private_conversations conversation
    where conversation.id = v_conversation_id
    for update;
    if not found then
      return jsonb_build_object('status', 'conversation_missing');
    end if;
    if v_identity_id not in (v_conversation.sender_id, v_conversation.recipient_id) then
      return jsonb_build_object('status', 'not_participant');
    end if;
    if v_conversation.status <> 'accepted' then
      return jsonb_build_object(
        'status', 'status_conflict', 'conversation', to_jsonb(v_conversation)
      );
    end if;
    if exists (
      select 1 from public.exchange_community_blocks block
      where (block.owner_id = v_conversation.sender_id and block.target_id = v_conversation.recipient_id)
         or (block.owner_id = v_conversation.recipient_id and block.target_id = v_conversation.sender_id)
    ) then
      return jsonb_build_object('status', 'blocked');
    end if;
    insert into public.exchange_community_private_messages (
      id, conversation_id, author_id, display_name, body, created_at
    ) values (
      btrim(p_payload #>> '{message,id}'),
      v_conversation_id,
      v_identity_id,
      v_identity.display_name,
      btrim(p_payload #>> '{message,body}'),
      v_now
    ) returning * into v_message;
    update public.exchange_community_private_conversations conversation
    set revision = conversation.revision + 1, updated_at = v_now
    where conversation.id = v_conversation_id
    returning * into v_conversation;
    v_resource_type := 'private_message';
    v_resource_id := v_message.id;
    v_response := jsonb_build_object(
      'status', 'committed', 'idempotent', false,
      'conversation', to_jsonb(v_conversation),
      'message', to_jsonb(v_message)
    );

  elsif v_operation = 'community_block' then
    v_target_id := nullif(btrim(p_payload #>> '{block,target_id}'), '');
    if p_payload #>> '{block,owner_id}' is distinct from v_identity_id
       or v_target_id is null
       or v_target_id = v_identity_id then
      return jsonb_build_object('status', 'self_target');
    end if;
    select identity.* into v_recipient
    from public.exchange_community_identities identity
    where identity.id = v_target_id and identity.account_id is not null
    for update;
    if not found then
      return jsonb_build_object('status', 'recipient_missing');
    end if;
    if not exists (
      select 1
      from public.exchange_community_private_conversations conversation
      where (conversation.sender_id = v_identity_id and conversation.recipient_id = v_target_id)
         or (conversation.sender_id = v_target_id and conversation.recipient_id = v_identity_id)
    ) then
      return jsonb_build_object('status', 'conversation_required');
    end if;
    select block.* into v_block
    from public.exchange_community_blocks block
    where block.owner_id = v_identity_id and block.target_id = v_target_id
    for update;
    if not found then
      insert into public.exchange_community_blocks (id, owner_id, target_id, created_at)
      values (
        btrim(p_payload #>> '{block,id}'), v_identity_id, v_target_id, v_now
      ) returning * into v_block;
    end if;
    v_resource_type := 'community_block';
    v_resource_id := v_block.id;
    v_response := jsonb_build_object(
      'status', 'committed', 'idempotent', false, 'block', to_jsonb(v_block)
    );

  elsif v_operation = 'community_report' then
    v_resource_type := nullif(btrim(p_payload #>> '{report,resource_type}'), '');
    v_resource_id := nullif(btrim(p_payload #>> '{report,resource_id}'), '');
    if p_payload #>> '{report,reporter_id}' is distinct from v_identity_id
       or p_payload #>> '{report,status}' is distinct from 'pending'
       or v_resource_type not in ('post', 'comment', 'chat', 'message') then
      return jsonb_build_object('status', 'integrity_conflict');
    end if;
    if v_resource_type = 'post' then
      select post.author_identity_id into v_author_id
      from public.exchange_community_posts post where post.id = v_resource_id
      for update;
    elsif v_resource_type = 'comment' then
      select comment.author_identity_id into v_author_id
      from public.exchange_community_post_comments comment where comment.id = v_resource_id
      for update;
    elsif v_resource_type = 'chat' then
      select chat.author_identity_id into v_author_id
      from public.exchange_community_public_chat_messages chat where chat.id = v_resource_id
      for update;
    else
      select message.conversation_id into v_conversation_id
      from public.exchange_community_private_messages message
      where message.id = v_resource_id;
      if not found then
        return jsonb_build_object('status', 'resource_missing');
      end if;
      select conversation.* into v_conversation
      from public.exchange_community_private_conversations conversation
      where conversation.id = v_conversation_id
      for update;
      if not found or v_identity_id not in (
        v_conversation.sender_id, v_conversation.recipient_id
      ) then
        return jsonb_build_object('status', 'resource_missing');
      end if;
      select message.* into v_message
      from public.exchange_community_private_messages message
      where message.id = v_resource_id
        and message.conversation_id = v_conversation_id
      for update;
      if found then
        v_author_id := v_message.author_id;
      end if;
    end if;
    if not found then
      return jsonb_build_object('status', 'resource_missing');
    end if;
    if v_author_id = v_identity_id then
      return jsonb_build_object('status', 'self_report');
    end if;
    select report.* into v_report
    from public.exchange_community_reports report
    where report.reporter_id = v_identity_id
      and report.resource_type = v_resource_type
      and report.resource_id = v_resource_id
      and report.status = 'pending'
    for update;
    if not found then
      insert into public.exchange_community_reports (
        id, reporter_id, resource_type, resource_id, reason, status,
        reviewed_by, reviewed_at, resolution_note, retained_until,
        revision, created_at
      ) values (
        btrim(p_payload #>> '{report,id}'),
        v_identity_id,
        v_resource_type,
        v_resource_id,
        btrim(p_payload #>> '{report,reason}'),
        'pending', null, null, null, null, 1, v_now
      ) returning * into v_report;
    end if;
    v_resource_type := 'community_report';
    v_resource_id := v_report.id;
    v_response := jsonb_build_object(
      'status', 'committed', 'idempotent', false, 'report', to_jsonb(v_report)
    );

  else
    v_report_id := nullif(btrim(p_payload ->> 'report_id'), '');
    v_expected_status := nullif(btrim(p_payload ->> 'expected_status'), '');
    v_status := nullif(btrim(p_payload ->> 'status'), '');
    v_note := nullif(btrim(p_payload ->> 'note'), '');
    if v_expected_status <> 'pending'
       or v_status not in ('resolved', 'dismissed')
       or v_note is null
       or char_length(v_note) not between 2 and 500 then
      return jsonb_build_object('status', 'integrity_conflict');
    end if;
    select report.* into v_report
    from public.exchange_community_reports report
    where report.id = v_report_id
    for update;
    if not found then
      return jsonb_build_object('status', 'report_missing');
    end if;
    if v_report.status <> v_expected_status then
      return jsonb_build_object(
        'status', 'status_conflict', 'report', to_jsonb(v_report)
      );
    end if;
    update public.exchange_community_reports report
    set status = v_status,
        reviewed_by = v_account_id,
        reviewed_at = v_now,
        resolution_note = v_note,
        revision = report.revision + 1
    where report.id = v_report_id
    returning * into v_report;
    insert into public.exchange_community_moderation_audits (
      id, resource_type, resource_id, previous_status, new_status,
      moderator_id, note, request_fingerprint, created_at, retained_until
    ) values (
      v_mutation_id, 'report', v_report_id, v_expected_status, v_status,
      v_account_id, v_note, v_fingerprint, v_now, v_now + interval '2160 hours'
    ) returning * into v_audit;
    v_resource_type := 'community_report';
    v_resource_id := v_report_id;
    v_response := jsonb_build_object(
      'status', 'committed', 'idempotent', false,
      'report', to_jsonb(v_report),
      'audit', to_jsonb(v_audit) - 'request_fingerprint'
    );
    if v_report.reporter_id is null then
      delete from public.exchange_community_reports report
      where report.id = v_report_id;
    end if;
  end if;

  insert into public.exchange_community_mutation_receipts (
    id, operation, request_fingerprint, actor_account_id, actor_identity_id,
    resource_type, resource_id, response, created_at, retained_until
  ) values (
    v_mutation_id,
    v_operation,
    v_fingerprint,
    v_account_id,
    case when v_operation = 'community_report_review' then null else v_identity_id end,
    v_resource_type,
    v_resource_id,
    v_response,
    v_now,
    v_now + interval '168 hours'
  );
  return v_response;
exception
  when unique_violation then
    v_replay := public.exchange_community_replay(
      v_mutation_id, v_operation, v_fingerprint
    );
    if v_replay is not null then
      return v_replay;
    end if;
    return jsonb_build_object('status', 'integrity_conflict');
  when integrity_constraint_violation or data_exception then
    return jsonb_build_object('status', 'integrity_conflict');
end;
$$;

create or replace function public.exchange_commit_private_community_conversation(
  p_mutation_id text,
  p_request_fingerprint text,
  p_account_id text,
  p_identity_id text,
  p_access_token_hash text,
  p_recipient_identity_id text,
  p_conversation jsonb,
  p_initial_message jsonb
) returns jsonb
language sql
security definer
set search_path = public, pg_temp
as $$
  select public.exchange_commit_private_community_mutation(
    p_mutation_id, p_request_fingerprint, 'private_conversation',
    jsonb_build_object(
      'mutation_id', p_mutation_id,
      'account_id', p_account_id,
      'identity_id', p_identity_id,
      'access_token_hash', p_access_token_hash,
      'recipient_identity_id', p_recipient_identity_id,
      'conversation', p_conversation,
      'initial_message', p_initial_message
    )
  );
$$;

create or replace function public.exchange_commit_private_community_conversation_status(
  p_mutation_id text,
  p_request_fingerprint text,
  p_account_id text,
  p_identity_id text,
  p_access_token_hash text,
  p_conversation_id text,
  p_expected_status text,
  p_status text
) returns jsonb
language sql
security definer
set search_path = public, pg_temp
as $$
  select public.exchange_commit_private_community_mutation(
    p_mutation_id, p_request_fingerprint, 'private_conversation_status',
    jsonb_build_object(
      'mutation_id', p_mutation_id,
      'account_id', p_account_id,
      'identity_id', p_identity_id,
      'access_token_hash', p_access_token_hash,
      'conversation_id', p_conversation_id,
      'expected_status', p_expected_status,
      'status', p_status
    )
  );
$$;

create or replace function public.exchange_commit_private_community_message(
  p_mutation_id text,
  p_request_fingerprint text,
  p_account_id text,
  p_identity_id text,
  p_access_token_hash text,
  p_message jsonb
) returns jsonb
language sql
security definer
set search_path = public, pg_temp
as $$
  select public.exchange_commit_private_community_mutation(
    p_mutation_id, p_request_fingerprint, 'private_message',
    jsonb_build_object(
      'mutation_id', p_mutation_id,
      'account_id', p_account_id,
      'identity_id', p_identity_id,
      'access_token_hash', p_access_token_hash,
      'message', p_message
    )
  );
$$;

create or replace function public.exchange_commit_private_community_block(
  p_mutation_id text,
  p_request_fingerprint text,
  p_account_id text,
  p_identity_id text,
  p_access_token_hash text,
  p_block jsonb
) returns jsonb
language sql
security definer
set search_path = public, pg_temp
as $$
  select public.exchange_commit_private_community_mutation(
    p_mutation_id, p_request_fingerprint, 'community_block',
    jsonb_build_object(
      'mutation_id', p_mutation_id,
      'account_id', p_account_id,
      'identity_id', p_identity_id,
      'access_token_hash', p_access_token_hash,
      'block', p_block
    )
  );
$$;

create or replace function public.exchange_commit_private_community_report(
  p_mutation_id text,
  p_request_fingerprint text,
  p_account_id text,
  p_identity_id text,
  p_access_token_hash text,
  p_report jsonb
) returns jsonb
language sql
security definer
set search_path = public, pg_temp
as $$
  select public.exchange_commit_private_community_mutation(
    p_mutation_id, p_request_fingerprint, 'community_report',
    jsonb_build_object(
      'mutation_id', p_mutation_id,
      'account_id', p_account_id,
      'identity_id', p_identity_id,
      'access_token_hash', p_access_token_hash,
      'report', p_report
    )
  );
$$;

create or replace function public.exchange_commit_private_community_report_review(
  p_mutation_id text,
  p_request_fingerprint text,
  p_moderator_id text,
  p_report_id text,
  p_expected_status text,
  p_status text,
  p_note text
) returns jsonb
language sql
security definer
set search_path = public, pg_temp
as $$
  select public.exchange_commit_private_community_mutation(
    p_mutation_id, p_request_fingerprint, 'community_report_review',
    jsonb_build_object(
      'mutation_id', p_mutation_id,
      'moderator_id', p_moderator_id,
      'report_id', p_report_id,
      'expected_status', p_expected_status,
      'status', p_status,
      'note', p_note
    )
  );
$$;

create or replace function public.exchange_purge_private_community_identity(
  p_mutation_id text,
  p_request_fingerprint text,
  p_identity_id text,
  p_expected_account_id text,
  p_pending_report_retention_days integer
) returns jsonb
language plpgsql
security definer
set search_path = public, pg_temp
as $$
declare
  v_mutation_id text := nullif(btrim(p_mutation_id), '');
  v_fingerprint text := lower(nullif(btrim(p_request_fingerprint), ''));
  v_identity_id text := nullif(btrim(p_identity_id), '');
  v_account_id text := nullif(btrim(p_expected_account_id), '');
  v_operation constant text := 'purge_private_identity';
  v_expected_fingerprint text;
  v_replay jsonb;
  v_now timestamptz := clock_timestamp();
  v_account public.exchange_accounts%rowtype;
  v_identity public.exchange_community_identities%rowtype;
  v_conversation_count bigint;
  v_message_count bigint;
  v_block_count bigint;
  v_report_deidentified_count bigint;
  v_report_deleted_count bigint;
  v_report_review_cleared_count bigint;
  v_response jsonb;
begin
  if v_mutation_id is null
     or char_length(v_mutation_id) not between 16 and 128
     or v_fingerprint is null
     or v_fingerprint !~ '^[0-9a-f]{64}$'
     or v_identity_id is null
     or char_length(v_identity_id) > 128
     or v_account_id is null
     or char_length(v_account_id) > 128
     or p_pending_report_retention_days not between 1 and 365 then
    return jsonb_build_object('status', 'integrity_conflict');
  end if;
  v_expected_fingerprint := public.exchange_community_request_fingerprint(
    jsonb_build_object(
      'operation', v_operation,
      'payload', jsonb_build_object(
        'mutation_id', v_mutation_id,
        'identity_id', v_identity_id,
        'expected_account_id', v_account_id,
        'pending_report_retention_days', p_pending_report_retention_days
      )
    )
  );
  if v_fingerprint is distinct from v_expected_fingerprint then
    return jsonb_build_object('status', 'invalid_request');
  end if;
  v_replay := public.exchange_community_replay(
    v_mutation_id, v_operation, v_fingerprint
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
  select identity.* into v_identity
  from public.exchange_community_identities identity
  where identity.id = v_identity_id
  for update;
  if not found then
    return jsonb_build_object('status', 'identity_missing');
  end if;
  if v_identity.account_id is distinct from v_account_id then
    return jsonb_build_object('status', 'identity_conflict');
  end if;

  select count(*) into v_message_count
  from public.exchange_community_private_messages message
  join public.exchange_community_private_conversations conversation
    on conversation.id = message.conversation_id
  where v_identity_id in (conversation.sender_id, conversation.recipient_id);

  delete from public.exchange_community_private_conversations conversation
  where v_identity_id in (conversation.sender_id, conversation.recipient_id);
  get diagnostics v_conversation_count = row_count;

  delete from public.exchange_community_blocks block
  where v_identity_id in (block.owner_id, block.target_id);
  get diagnostics v_block_count = row_count;

  update public.exchange_community_reports report
  set reporter_id = null,
      retained_until = v_now + make_interval(days => p_pending_report_retention_days),
      revision = report.revision + 1
  where report.reporter_id = v_identity_id
    and report.status = 'pending';
  get diagnostics v_report_deidentified_count = row_count;

  delete from public.exchange_community_reports report
  where report.reporter_id = v_identity_id;
  get diagnostics v_report_deleted_count = row_count;

  update public.exchange_community_reports report
  set reviewed_by = null,
      revision = report.revision + 1
  where report.reviewed_by = v_account_id;
  get diagnostics v_report_review_cleared_count = row_count;

  v_response := jsonb_build_object(
    'status', 'committed',
    'idempotent', false,
    'counts', jsonb_build_object(
      'conversation', v_conversation_count,
      'message', v_message_count,
      'block', v_block_count,
      'report_deidentified', v_report_deidentified_count,
      'report_deleted', v_report_deleted_count,
      'report_review_cleared', v_report_review_cleared_count
    )
  );
  insert into public.exchange_community_mutation_receipts (
    id, operation, request_fingerprint, actor_account_id, actor_identity_id,
    resource_type, resource_id, response, created_at, retained_until
  ) values (
    v_mutation_id,
    v_operation,
    v_fingerprint,
    v_account_id,
    v_identity_id,
    'private_identity',
    v_identity_id,
    v_response,
    v_now,
    v_now + interval '168 hours'
  );
  return v_response;
exception
  when unique_violation then
    v_replay := public.exchange_community_replay(
      v_mutation_id, v_operation, v_fingerprint
    );
    if v_replay is not null then
      return v_replay;
    end if;
    return jsonb_build_object('status', 'integrity_conflict');
  when integrity_constraint_violation or data_exception then
    return jsonb_build_object('status', 'integrity_conflict');
end;
$$;

create or replace function public.exchange_purge_private_community_operational_data()
returns jsonb
language plpgsql
security definer
set search_path = public, pg_temp
as $$
declare
  v_now timestamptz := clock_timestamp();
  v_reports bigint;
begin
  delete from public.exchange_community_reports report
  where report.retained_until is not null
    and report.retained_until <= v_now;
  get diagnostics v_reports = row_count;
  return jsonb_build_object('status', 'committed', 'reports', v_reports);
end;
$$;

alter table public.exchange_community_private_conversations enable row level security;
alter table public.exchange_community_private_messages enable row level security;
alter table public.exchange_community_blocks enable row level security;
alter table public.exchange_community_reports enable row level security;

revoke all on table public.exchange_community_private_conversations from anon, authenticated, service_role;
revoke all on table public.exchange_community_private_messages from anon, authenticated, service_role;
revoke all on table public.exchange_community_blocks from anon, authenticated, service_role;
revoke all on table public.exchange_community_reports from anon, authenticated, service_role;
grant select on table public.exchange_community_private_conversations to service_role;
grant select on table public.exchange_community_private_messages to service_role;
grant select on table public.exchange_community_blocks to service_role;
grant select on table public.exchange_community_reports to service_role;

revoke all on function public.exchange_commit_private_community_mutation(
  text, text, text, jsonb
) from public, anon, authenticated;
revoke all on function public.exchange_commit_private_community_conversation(
  text, text, text, text, text, text, jsonb, jsonb
) from public, anon, authenticated;
revoke all on function public.exchange_commit_private_community_conversation_status(
  text, text, text, text, text, text, text, text
) from public, anon, authenticated;
revoke all on function public.exchange_commit_private_community_message(
  text, text, text, text, text, jsonb
) from public, anon, authenticated;
revoke all on function public.exchange_commit_private_community_block(
  text, text, text, text, text, jsonb
) from public, anon, authenticated;
revoke all on function public.exchange_commit_private_community_report(
  text, text, text, text, text, jsonb
) from public, anon, authenticated;
revoke all on function public.exchange_commit_private_community_report_review(
  text, text, text, text, text, text, text
) from public, anon, authenticated;
revoke all on function public.exchange_purge_private_community_identity(
  text, text, text, text, integer
) from public, anon, authenticated;
revoke all on function public.exchange_purge_private_community_operational_data()
  from public, anon, authenticated;

grant execute on function public.exchange_commit_private_community_conversation(
  text, text, text, text, text, text, jsonb, jsonb
) to service_role;
grant execute on function public.exchange_commit_private_community_conversation_status(
  text, text, text, text, text, text, text, text
) to service_role;
grant execute on function public.exchange_commit_private_community_message(
  text, text, text, text, text, jsonb
) to service_role;
grant execute on function public.exchange_commit_private_community_block(
  text, text, text, text, text, jsonb
) to service_role;
grant execute on function public.exchange_commit_private_community_report(
  text, text, text, text, text, jsonb
) to service_role;
grant execute on function public.exchange_commit_private_community_report_review(
  text, text, text, text, text, text, text
) to service_role;
grant execute on function public.exchange_purge_private_community_identity(
  text, text, text, text, integer
) to service_role;
grant execute on function public.exchange_purge_private_community_operational_data()
  to service_role;

comment on table public.exchange_community_private_conversations is
  'Server-only private invitation lifecycle; direct mutation is forbidden.';
comment on table public.exchange_community_private_messages is
  'Server-only private messages; every insert is checked against the locked conversation and block state.';
comment on table public.exchange_community_blocks is
  'Server-only directional blocks with a prior-conversation requirement.';
comment on table public.exchange_community_reports is
  'Safety reports with de-identified retention and atomic moderation audit.';
