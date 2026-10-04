-- Open school boards to every account with a verified e-mail.
--
-- Before: posting or commenting on a university_exchange board, and reacting to its posts, needed
-- a verified student of that same school. Now any account with a verified e-mail (Google sign-in
-- provides one) can. Unchanged on purpose: questions, answers, shared experiences and chat stay
-- verified-student only, and a school-named byline (verified_school / verified_department) still
-- needs a verified student, so an unverified account cannot present itself as that school's student.
--
-- Both functions are the 20260930100000 definitions with only those conditions removed.
-- create or replace keeps their existing ownership and grants; they are restated below.

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
      -- Any account with a verified e-mail may post on a school board. A school-named
      -- byline still needs a verified student (exchange_community_display_name).
      v_required_school_key := public.exchange_normalize_community_school(
        coalesce(p_payload ->> 'school_name', '')
      );
      if v_required_school_key = ''
         or not (
           coalesce(p_payload ->> 'board_id', '') ~ '^university:'
           or (p_payload ->> 'board_id' = 'cgu' and v_required_school_key = '長庚大學')
           or (p_payload ->> 'board_id' = 'ntpu' and v_required_school_key = '國立臺北大學')
         ) then
        return jsonb_build_object('status', 'board_forbidden');
      end if;
    else
      return jsonb_build_object('status', 'board_forbidden');
    end if;
  elsif v_content_type = 'comment' then
    if not public.exchange_community_payload_has_only_keys(
      p_payload,
      array['post_id', 'parent_id', 'body', 'identity_mode', 'status']
    ) then
      return jsonb_build_object('status', 'invalid_request');
    end if;
    select post.* into v_post
    from public.exchange_community_posts post
    where post.id = nullif(btrim(p_payload ->> 'post_id'), '')
    for update;
    if not found or v_post.status <> 'approved' then
      return jsonb_build_object('status', 'parent_missing');
    end if;
    if nullif(p_payload ->> 'parent_id', '') is not null then
      select comment.* into v_comment from public.exchange_community_post_comments comment
      where comment.id = p_payload ->> 'parent_id' and comment.post_id = v_post.id
      for update;
      if not found or v_comment.parent_id is not null or v_comment.status <> 'approved' then
        return jsonb_build_object('status', 'parent_missing');
      end if;
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
      -- Comments on a school board follow the same rule as posts: a verified e-mail is enough.
      null;
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
        id, post_id, parent_id, author_identity_id, display_name, identity_mode, body,
        status, revision, created_at, updated_at
      ) values (
        v_content_id,
        v_post.id,
        nullif(p_payload ->> 'parent_id', ''),
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

create or replace function public.exchange_set_community_reaction(
  p_account_id text, p_resource_type text, p_resource_id text, p_reaction text,
  p_is_platform_admin boolean default false
) returns jsonb language plpgsql security definer set search_path = '' as $$
declare
  v_account public.exchange_accounts%rowtype;
  v_post public.exchange_community_posts%rowtype;
  v_comment public.exchange_community_post_comments%rowtype;
  v_parent public.exchange_community_post_comments%rowtype;
  v_post_id text;
  v_helpful bigint;
  v_thanks bigint;
begin
  if p_resource_type is null or p_resource_type not in ('post', 'comment')
     or (p_reaction is not null and p_reaction not in ('helpful', 'thanks')) then
    return jsonb_build_object('status', 'forbidden');
  end if;
  select * into v_account from public.exchange_accounts where id = p_account_id for update;
  if not found or not coalesce((v_account.profile ->> 'email_verified')::boolean, false)
     or v_account.community_suspended_until > clock_timestamp() then
    return jsonb_build_object('status', 'forbidden');
  end if;
  if p_resource_type = 'post' then v_post_id := p_resource_id;
  else
    select post_id into v_post_id from public.exchange_community_post_comments where id = p_resource_id;
  end if;
  -- Same parent-before-child order as publication/deletion. The post lock serializes counts across accounts.
  select * into v_post from public.exchange_community_posts where id = v_post_id for update;
  if not found or v_post.status <> 'approved' then return jsonb_build_object('status', 'missing'); end if;
  if p_resource_type = 'comment' then
    select * into v_comment from public.exchange_community_post_comments where id = p_resource_id;
    if v_comment.parent_id is not null then
      select * into v_parent from public.exchange_community_post_comments where id = v_comment.parent_id for update;
      if not found or v_parent.status <> 'approved' or v_parent.post_id <> v_post.id then
        return jsonb_build_object('status', 'missing');
      end if;
    end if;
    select * into v_comment from public.exchange_community_post_comments where id = p_resource_id for update;
    if not found or v_comment.status <> 'approved' or v_comment.deleted then
      return jsonb_build_object('status', 'missing');
    end if;
  end if;
  -- School boards no longer limit reactions to verified students; the e-mail check above applies.
  if p_reaction is null then
    delete from public.exchange_community_reactions where account_id = p_account_id and resource_type = p_resource_type and resource_id = p_resource_id;
  else
    insert into public.exchange_community_reactions(account_id, resource_type, resource_id, reaction)
    values(p_account_id, p_resource_type, p_resource_id, p_reaction)
    on conflict(account_id, resource_type, resource_id) do update set reaction = excluded.reaction;
  end if;
  select count(*) filter (where reaction = 'helpful'), count(*) filter (where reaction = 'thanks')
    into v_helpful, v_thanks from public.exchange_community_reactions
    where resource_type = p_resource_type and resource_id = p_resource_id;
  return jsonb_build_object('status', 'committed', 'counts', jsonb_build_object('helpful', v_helpful, 'thanks', v_thanks), 'viewer_reaction', p_reaction);
end;
$$;

-- The content function is an internal step called only by exchange_commit_public_community_publication,
-- so it stays unreachable for every role, exactly as in 20260823160000.
revoke all on function public.exchange_commit_public_community_content(
  text, text, text, text, text, text, jsonb
) from public, anon, authenticated, service_role;
revoke all on function public.exchange_set_community_reaction(text, text, text, text, boolean) from public, anon, authenticated;
grant execute on function public.exchange_set_community_reaction(text, text, text, text, boolean) to service_role;
