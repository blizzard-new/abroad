"""Prepare immutable SQL and expected body hashes without accessing production."""
from pathlib import Path
import hashlib
import json
import re

root = Path('/workspace/abroad-six-final')
out = Path('/workspace/integration-evidence')
before = json.loads((out / 'production-pre-tku-function-definitions-decoded.json').read_text())
metadata = {row['signature'].split('(')[0]: row for row in before}
records = []
for name in ('verified_email_school_community', 'community_byline_aliases', 'atomic_governance_commands'):
    paths = list((root / 'supabase/migrations').glob('*_' + name + '.sql'))
    assert len(paths) == 1, (name, paths)
    source = paths[0].read_text()
    target = out / ('tku-release-' + name + '.sql')
    target.write_text(source)
    functions = []
    for match in re.finditer(r'create or replace function public\.(\w+)\(.*?\)\s*returns\b.*?\bas \$\$(.*?)\$\$;', source, re.S | re.I):
        fn, body = match.groups()
        prior = metadata[fn]
        functions.append({'name': fn, 'signature': prior['signature'],
                          'expected_source_md5': hashlib.md5(body.encode()).hexdigest(),
                          'owner': prior['owner'], 'acl': prior['acl'],
                          'security_definer': prior['security_definer'], 'config': prior['config']})
    assert len(functions) == (2 if name == 'atomic_governance_commands' else 1)
    row = {'name': name, 'original_path': str(paths[0].relative_to(root)),
           'release_sql': str(target), 'sha256': hashlib.sha256(source.encode()).hexdigest(),
           'expected_functions': functions}
    if name == 'verified_email_school_community':
        prior = metadata['exchange_commit_public_community_content']
        old = "           or (p_payload ->> 'board_id' = 'ntu' and v_required_school_key = '國立臺灣大學')"
        new = "           or (p_payload ->> 'board_id' = 'tku' and v_required_school_key = '淡江大學')"
        assert prior['definition'].count(old) == 1 and new not in prior['definition']
        after = prior['definition'].replace(old, old + '\n' + new)
        row['expected_board_definition_md5'] = hashlib.md5(after.encode()).hexdigest()
    records.append(row)
(out / 'tku-release-sql-manifest.json').write_text(json.dumps(records, ensure_ascii=False, indent=2) + '\n')
print(json.dumps([{'name':r['name'], 'sha256':r['sha256'], 'function_count':len(r['expected_functions'])} for r in records]))
