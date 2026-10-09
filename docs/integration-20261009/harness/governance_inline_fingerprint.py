"""Canonical JSON fingerprint using only built-ins, preserving invoker ACLs."""
from pathlib import Path
import re

def fingerprint(value):
    return '''(
          with recursive hash_nodes(path, value, prefix) as (
            select array[]::integer[], VALUE_INPUT, ''::text
            union all
            select parent.path || child.position, child.value,
                   case when child.position > 1 then ',' else '' end
                   || case when child.key is not null then to_jsonb(child.key)::text || ':' else '' end
            from hash_nodes parent
            cross join lateral (
              select entry.key, entry.value, row_number() over (order by entry.key)::integer as position
              from jsonb_each(case when jsonb_typeof(parent.value) = 'object' then parent.value else '{}'::jsonb end) entry
              union all
              select null::text, entry.value, entry.ordinality::integer
              from jsonb_array_elements(case when jsonb_typeof(parent.value) = 'array' then parent.value else '[]'::jsonb end)
                   with ordinality entry(value, ordinality)
            ) child
          ), hash_tokens as (
            select path || 0 as position, prefix || case jsonb_typeof(value)
                     when 'object' then '{' when 'array' then '[' else value::text end as token
            from hash_nodes
            union all
            select path || 2147483647, case jsonb_typeof(value) when 'object' then '}' else ']' end
            from hash_nodes where jsonb_typeof(value) in ('object', 'array')
          )
          select encode(sha256(convert_to(string_agg(token, '' order by position), 'UTF8')), 'hex')
          from hash_tokens
        )'''.replace('VALUE_INPUT',value)

if __name__=='__main__':
    p=Path('/workspace/abroad-six/supabase/migrations/20261009080000_atomic_governance_commands.sql')
    text=p.read_text()
    pattern=r'public\.exchange_community_request_fingerprint\(([^()]+)\)'
    assert len(re.findall(pattern,text))==6
    text=re.sub(pattern,lambda m:fingerprint(m[1]),text)
    text=text.replace('-- Existing RPC transaction boundary;', '-- Canonical hashing is computed with built-ins inside this invoker RPC.\n-- The community hashing helpers are deliberately owner-only; no ACL expansion.\n-- Existing RPC transaction boundary;',1)
    p.write_text(text)
