"""Validate the deployed governance code and models in a separate interpreter."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
from urllib.parse import urlsplit

import requests

BASE = 'e5c6d5ceafcb2099d45b67ab47aa464f7f82fa86'
CHILD = r'''
import json,sys
from urllib.parse import urlsplit
import requests
config=json.load(sys.stdin)
sys.path.insert(0,config['source'])
from exchange_info import content_governance as legacy
from exchange_info.models import UniversityApplicationWorkflow as ApplicationWorkflow
assert legacy.__file__.startswith(config['source'])
assert sys.modules[ApplicationWorkflow.__module__].__file__.startswith(config['source'])
calls=[]
def transport(method,url,**kwargs):
    parsed=urlsplit(url)
    assert parsed.hostname=='runtime-supabase.invalid'
    result=requests.request(method,config['gateway']+parsed.path.removeprefix('/rest/v1'),**kwargs)
    calls.append({'method':method,'path':parsed.path,'status':result.status_code})
    return result
store=legacy.SupabaseContentGovernanceStore('https://runtime-supabase.invalid',config['token'],request_func=transport)
document=ApplicationWorkflow.model_validate(config['workflow'])
revision=legacy.stage_workflow_refresh(store,document).revision
assert revision is not None
for actor in ('legacy-tree-synthetic-a','legacy-tree-synthetic-b'):
    revision=legacy.approve_workflow_revision(store,revision.id,reviewer_id=actor,
        expected_content_hash=revision.content_hash,note='Synthetic full deployed-source attestation',
        reviewed_source_urls=legacy.workflow_review_source_urls(revision.workflow),
        reviewed_rule_keys=legacy.workflow_review_rule_keys(revision.workflow))
legacy.publish_workflow_revision(store,revision.id,reviewer_id='legacy-tree-synthetic-a')
published=[r for r in store.load_published_workflows() if r.school_name==document.school_name]
assert len(published)==1 and all(c['status']==200 for c in calls)
print(json.dumps({'calls':calls,'published':published[0].model_dump(mode='json')},ensure_ascii=False))
'''

def validate(context):
    from scripts.validate_governance_runtime import workflow, require
    from exchange_info.content_governance import SupabaseContentGovernanceStore
    require(urlsplit(context.postgrest_url).hostname in {'127.0.0.1', 'localhost'},
            'Legacy full-source test requires the isolated local gateway')
    paths = subprocess.check_output(['git', 'ls-tree', '-r', '--name-only', BASE, 'src'], text=True).splitlines()
    python_paths = [path for path in paths if path.endswith('.py')]
    tree = subprocess.check_output(['git', 'rev-parse', BASE + ':src'], text=True).strip()
    document = workflow('Synthetic complete deployed source compatibility').model_copy(update={
        'school_name': 'Synthetic full legacy tree compatibility host'})
    source_hashes = {}
    with tempfile.TemporaryDirectory(prefix='abroad-legacy-source-') as directory:
        root = Path(directory)
        for path in python_paths:
            source = subprocess.check_output(['git', 'show', BASE + ':' + path])
            target = root / path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(source)
            source_hashes[path] = hashlib.sha256(source).hexdigest()
        config = {'source': str(root / 'src'), 'gateway': context.postgrest_url,
                  'token': context.service_token, 'workflow': document.model_dump(mode='json')}
        # The generated local service token travels only over stdin, never argv,
        # artifacts or process output. No production credentials are available.
        child = subprocess.run([sys.executable, '-c', CHILD], input=json.dumps(config),
                               text=True, capture_output=True, cwd=directory, timeout=180)
        require(child.returncode == 0, 'Exact deployed-source child failed: ' + child.stderr)
        result = json.loads(child.stdout)
    calls = result['calls']
    def transport(method, url, **kwargs):
        parsed = urlsplit(url)
        require(parsed.hostname == 'runtime-supabase.invalid', 'Current read left isolated gateway')
        response = requests.request(method, context.postgrest_url + parsed.path.removeprefix('/rest/v1'), **kwargs)
        calls.append({'method': method, 'path': parsed.path, 'status': response.status_code})
        return response
    current = SupabaseContentGovernanceStore('https://runtime-supabase.invalid', context.service_token,
                                            request_func=transport)
    published = [r for r in current.load_published_workflows() if r.school_name == document.school_name]
    require(len(published) == 1, 'Current client cannot read exact legacy-tree publication')
    require(published[0].model_dump(mode='json') == result['published'],
            'Current and exact deployed models disagree on published payload')
    require(all(c['status'] == 200 for c in calls), 'Legacy full-source RPC failed')
    return {'status': 'passed', 'deployed_commit': BASE, 'deployed_src_tree': tree,
            'scope': 'Exact deployed Python modules and models in separate interpreter, existing compatible dependency environment, upgraded local DB',
            'python_module_count': len(python_paths), 'python_source_sha256': source_hashes,
            'stage_dual_review_publication': True, 'old_and_new_read_payload_identical': True,
            'calls': calls}
