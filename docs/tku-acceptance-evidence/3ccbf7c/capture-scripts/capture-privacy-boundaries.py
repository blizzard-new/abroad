"""Add read-only HTTP/RPC telemetry to the unmodified 19 regression cases."""
from datetime import datetime,timezone
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT=Path('/workspace/abroad-tku');OUT=Path('/tmp/tku-acceptance-3ccbf7c')
os.chdir(ROOT);sys.path.insert(0,str(ROOT))
from fastapi.testclient import TestClient
import pytest

original_request=TestClient.request
events=[];current_case=''

def state():
    return dict(commit=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),
        dirty=subprocess.check_output(['git','status','--porcelain'],text=True).strip())


def request(client,method,url,*args,**kwargs):
    method=method.upper();path=str(url)
    tracked=path=='/auth/me' or path.startswith('/community/posts')
    repository=client.app.state.account_repository
    rpc=[];commit=getattr(repository,'commit_account_deletion',None)
    if method=='DELETE' and path=='/auth/me' and commit:
        def traced_commit(mutation,*a,**kw):
            result=commit(mutation,*a,**kw)
            rpc.append(dict(mutation_id=mutation.mutation_id,account_id=mutation.account_id,
                session_id=mutation.session_id,returned_status=getattr(result.status,'value',str(result.status))))
            return result
        repository.commit_account_deletion=traced_commit
    try:
        response=original_request(client,method,url,*args,**kwargs)
    finally:
        if method=='DELETE' and path=='/auth/me' and commit:
            repository.commit_account_deletion=commit
    if tracked:
        supplied=kwargs.get('headers') or {}
        events.append(dict(case=current_case,request=dict(method=method,path=path,json=kwargs.get('json'),
            deletion_mutation_header=supplied.get('X-Account-Deletion-Mutation-ID'),
            credentials='omitted; all sessions are isolated synthetic fixtures'),
            response=dict(status=response.status_code,raw_body=response.content.decode('utf-8'),
                returned_mutation_id=response.headers.get('X-Account-Deletion-Mutation-ID')),
            repository_backend=getattr(repository,'backend_name','unknown'),
            rpc_routing_simulated='test_supabase_backend_' in current_case,
            atomic_commit_calls=rpc))
    return response


class Plugin:
    def pytest_runtest_setup(self,item):
        global current_case
        current_case=item.nodeid


before=state();assert before==dict(commit='3ccbf7c3de75b47f2f93f7aa56e96143e2e48a38',dirty='')
TestClient.request=request
started=datetime.now(timezone.utc).isoformat()
try:
    code=pytest.main(['tests/test_tku_privacy_regressions.py','-vv',
        f'--junitxml={OUT}/privacy-boundary-regressions.xml'],plugins=[Plugin()])
finally:
    TestClient.request=original_request
after=state()
payload=dict(tested_commit=before['commit'],before=before,after=after,
    candidate_guard_passed=before==after and not after['dirty'],started_at=started,
    ended_at=datetime.now(timezone.utc).isoformat(),actual_exit_code=int(code),
    synthetic_only=True,production_database_access=False,events=events,
    instrumentation='Only HTTP response and existing commit-result telemetry; assertions, payloads and repository behavior remain the candidate tests. Supabase cases use explicit test fakes, not a database.',
    source_tests='tests/test_tku_privacy_regressions.py')
(OUT/'privacy-boundary-http-trace.json').write_text(json.dumps(payload,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(dict(tested_commit=before['commit'],actual_exit_code=int(code),
    candidate_guard_passed=payload['candidate_guard_passed'],captured_http_calls=len(events),
    deletes=[dict(case=e['case'],status=e['response']['status'],simulated=e['rpc_routing_simulated'],
                 atomic_calls=e['atomic_commit_calls']) for e in events if e['request']['method']=='DELETE']),ensure_ascii=False))
raise SystemExit(int(code) if payload['candidate_guard_passed'] else 2)
