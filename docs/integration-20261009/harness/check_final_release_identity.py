"""Verify only three exact SQL renames and the release note follow the full suite."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys

BASE = '0fdc6cfa6a4902fb83374a77025f45dffb071562'
root = Path.cwd()
def git(*args):
    return subprocess.check_output(['git', *args], text=True).strip()
assert not git('status', '--porcelain=v1')
head = git('rev-parse', 'HEAD')
mapping = json.loads(Path('/workspace/integration-evidence/production-tku-migration-mapping.json').read_text())
changed = git('diff', '--name-status', '-M', BASE, head).splitlines()
expected = {'A\tdocs/six-school-release-2026-10-09.md'}
for row in mapping:
    expected.add('R100\t' + row['original_path'] + '\t' + row['new_path'])
    assert hashlib.sha256((root / row['new_path']).read_bytes()).hexdigest() == row['sql_sha256']
    assert git('rev-parse', BASE + ':' + row['original_path']) == git('rev-parse', head + ':' + row['new_path'])
assert set(changed) == expected, changed
old_paths = git('ls-tree', '-r', '--name-only', BASE, 'supabase/migrations').splitlines()
def deployed_order(path):
    return (1 if path.endswith('_ccu_ncu_school_board_compatibility.sql') else
            2 if path.endswith(('_verified_email_school_community.sql', '_community_byline_aliases.sql',
                                '_atomic_governance_commands.sql')) else 0, path)
old_paths.sort(key=deployed_order)
new_paths = sorted(git('ls-tree', '-r', '--name-only', head, 'supabase/migrations').splitlines())
old_blobs = [git('rev-parse', BASE + ':' + path) for path in old_paths]
new_blobs = [git('rev-parse', head + ':' + path) for path in new_paths]
assert len(old_blobs) == len(new_blobs) == 35 and old_blobs == new_blobs
assert git('rev-parse', BASE + ':src') == git('rev-parse', head + ':src')
assert git('rev-parse', BASE + ':tests') == git('rev-parse', head + ':tests')
proof = {'full_pytest_sha': BASE, 'release_head': head, 'only_changes': changed,
         'app_src_tree': git('rev-parse', head + ':src'), 'tests_tree': git('rev-parse', head + ':tests'),
         'sql_bytes_identical': True, 'validated_deployed_order_equals_final_natural_order': True,
         'migration_count': 35, 'old_order': old_paths, 'final_order': new_paths, 'sql_blob_order': new_blobs}
Path('/workspace/integration-evidence/six-release-identity-proof.json').write_text(json.dumps(proof, indent=2) + '\n')
print(json.dumps({k: v for k, v in proof.items() if k not in ('old_order', 'final_order', 'sql_blob_order')}), flush=True)
subprocess.run([sys.executable, 'scripts/validate_supabase_migrations.py'], check=True)
subprocess.run([sys.executable, '-m', 'pytest', '-q', 'tests/test_supabase_migration_syntax.py',
                '--junitxml=/workspace/integration-evidence/six-final-release-identity/results.xml'], check=True)
