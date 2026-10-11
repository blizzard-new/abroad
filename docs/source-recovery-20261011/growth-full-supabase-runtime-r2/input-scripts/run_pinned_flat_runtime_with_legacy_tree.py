"""Run the original complete harness using an exact-content, single-layer image."""
import json
from pathlib import Path
import sys
root = Path.cwd()
sys.path.insert(0,str(root))
sys.path.insert(0,str(root/'scripts'))
from scripts import validate_supabase_runtime as runtime
from scripts import validate_tku_community_runtime as tku
import requests
import inspect

if '--legacy-client' in sys.argv:
    from legacy_client_compatibility import validate as validate_legacy
    original_validate = runtime.validate_runtime
    def validate_with_legacy(context):
        result = original_validate(context)
        result['deployed_client_compatibility'] = validate_legacy(context)
        from legacy_tree_client_compatibility import validate as validate_legacy_tree
        result['deployed_full_python_source_compatibility'] = validate_legacy_tree(context)
        return result
    runtime.validate_runtime = validate_with_legacy

if '--deployed-order' in sys.argv:
    source=inspect.getsource(runtime._apply_migrations)
    original_sort='migration_files = sorted(MIGRATIONS_DIR.glob("*.sql"))'
    assert source.count(original_sort)==1
    reordered='''migration_files = sorted(MIGRATIONS_DIR.glob("*.sql"), key=lambda path: (
        1 if path.name.endswith("_ccu_ncu_school_board_compatibility.sql") else
        2 if path.name.endswith(("_verified_email_school_community.sql", "_community_byline_aliases.sql", "_atomic_governance_commands.sql")) else 0,
        path.name))'''
    exec(source.replace(original_sort,reordered),runtime.__dict__)
    print('MIGRATION ORDER: existing baseline, already-released CCU/NCU compatibility, then TKU 040000/060000/080000',flush=True)

# Observe the first real error without changing the request, result or assertions.
original_request = requests.sessions.Session.request
def observed_request(self, method, url, **kwargs):
    response = original_request(self, method, url, **kwargs)
    if response.status_code >= 400 and '/rpc/' in url and ('127.0.0.1' in url):
        print(json.dumps({'runtime_rpc_failure':url,'http_status':response.status_code,'body':response.text},ensure_ascii=False),flush=True)
    return response
requests.sessions.Session.request = observed_request

proof = json.loads(Path('/workspace/integration-evidence/pinned-image-flat-proof.json').read_text())
original = runtime.COMPOSE_FILE.read_text()
pinned = 'supabase/postgres:17.6.1.136@sha256:f371b5f3f2ac0a05703f33d6e6134515fb2498cab708fb948a0aeb7481467c00'
assert original.count(pinned)==1
replacement = proof['local_image_id']
content = original.replace(pinned,replacement)
assert content.replace(replacement,pinned)==original
compose = Path('/workspace/integration-tools') / ('runtime-flat-'+root.name+'.yml')
compose.write_text(content)
runtime.COMPOSE_FILE=compose
print(json.dumps({'mode':'complete original harness with exact-rootfs VFS packaging adaptation','repository':str(root),'original_pinned_image':pinned,'local_image':replacement,'runtime_config_identical':proof['runtime_config_identical'],'compose_only_difference':'postgres image identity for local repack','migrations':len(list(runtime.MIGRATIONS_DIR.glob('*.sql')))},ensure_ascii=False),flush=True)
raise SystemExit(tku.main())
