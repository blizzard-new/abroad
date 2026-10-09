"""Exercise the deployed five-school governance client on the upgraded local DB."""
import hashlib
import subprocess
import sys
import types
from urllib.parse import urlsplit
import requests

BASE = 'e5c6d5ceafcb2099d45b67ab47aa464f7f82fa86'
PATH = 'src/exchange_info/content_governance.py'

def validate(context):
    from scripts.validate_governance_runtime import workflow, require
    from exchange_info.content_governance import SupabaseContentGovernanceStore
    source = subprocess.check_output(['git', 'show', BASE + ':' + PATH])
    legacy = types.ModuleType('exchange_info._deployed_governance_client')
    legacy.__package__ = 'exchange_info'
    sys.modules[legacy.__name__] = legacy
    exec(compile(source, BASE + ':' + PATH, 'exec'), legacy.__dict__)
    calls = []
    def transport(method, url, **kwargs):
        parsed = urlsplit(url)
        require(parsed.hostname == 'runtime-supabase.invalid', 'Legacy client left isolated gateway')
        result = requests.request(method, context.postgrest_url + parsed.path.removeprefix('/rest/v1'), **kwargs)
        calls.append({'method': method, 'path': parsed.path, 'status': result.status_code})
        return result
    store = legacy.SupabaseContentGovernanceStore('https://runtime-supabase.invalid', context.service_token,
                                                request_func=transport)
    document = workflow('Synthetic deployed client compatibility').model_copy(update={
        'school_name': 'Synthetic legacy compatibility host'})
    revision = legacy.stage_workflow_refresh(store, document).revision
    require(revision is not None, 'Legacy client did not stage revision')
    for actor in ('legacy-synthetic-a', 'legacy-synthetic-b'):
        revision = legacy.approve_workflow_revision(store, revision.id, reviewer_id=actor,
            expected_content_hash=revision.content_hash, note='Synthetic complete old-client attestation',
            reviewed_source_urls=legacy.workflow_review_source_urls(revision.workflow),
            reviewed_rule_keys=legacy.workflow_review_rule_keys(revision.workflow))
    legacy.publish_workflow_revision(store, revision.id, reviewer_id='legacy-synthetic-a')
    legacy_public = [r for r in store.load_published_workflows() if r.school_name == document.school_name]
    current = SupabaseContentGovernanceStore('https://runtime-supabase.invalid', context.service_token,
                                           request_func=transport)
    new_public = [r for r in current.load_published_workflows() if r.school_name == document.school_name]
    require(len(legacy_public) == 1 and len(new_public) == 1, 'Legacy publication missing')
    require(legacy_public[0].model_dump(mode='json') == new_public[0].model_dump(mode='json'),
            'New and deployed client disagree on published payload')
    require(all(r['status'] == 200 for r in calls), 'Legacy client RPC failed')
    return {'status': 'passed', 'deployed_client_commit': BASE,
            'client_source_sha256': hashlib.sha256(source).hexdigest(),
            'scope': 'Exact deployed governance client, current compatible models, complete new local DB',
            'stage_dual_review_publication': True, 'old_and_new_read_payload_identical': True, 'calls': calls}
