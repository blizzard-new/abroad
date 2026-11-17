-- Allow recipients to decline pending private conversation invitations
-- (pending -> accepted | declined) while keeping all CAS, block, and
-- idempotency guarantees intact.

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
    if v_expected_status <> 'pending' or v_status not in ('accepted', 'declined') then
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

revoke all on function public.exchange_commit_private_community_mutation(
  text, text, text, jsonb
) from public, anon, authenticated;
