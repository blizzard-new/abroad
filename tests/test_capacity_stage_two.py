"""Atomic draft writes and safety gates for the isolated mixed-workload harness."""
import asyncio
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
import importlib.util
from pathlib import Path
import threading

import httpx
import pytest
import requests

from exchange_info.form_drafts import (
    FormDraftConflictError, FormDraftService, LocalFormDraftRepository,
    SupabaseFormDraftRepository, _RevisionConflict,
)
from exchange_info.models import ApplicationFormDraftSave, utc_now


def payload(revision=0, marker='first'):
    return ApplicationFormDraftSave(home_school='長庚大學', template_version='v1',
        revision=revision, answers={'overseas_institution':marker})


def encrypted_record(tmp_path):
    repo = LocalFormDraftRepository(tmp_path)
    FormDraftService(repo, b'k'*32).save_draft('student', 'consent', payload())
    return repo.list_records('student')[0]


@pytest.mark.parametrize('revision,method', [(1,'POST'),(2,'PATCH')])
def test_supabase_draft_writes_compare_and_set(monkeypatch,tmp_path,revision,method):
    record = encrypted_record(tmp_path).model_copy(update={'revision':revision})
    calls=[]
    def request(verb,url,**kwargs):
        calls.append((verb,kwargs))
        response=requests.Response()
        response.status_code=200
        import json
        response._content=json.dumps([record.model_dump(mode='json')]).encode()
        return response
    monkeypatch.setattr('exchange_info.form_drafts.supabase_http.request',request)
    saved=SupabaseFormDraftRepository('https://isolated.test','key').save_record(record)
    assert saved==record
    verb,params=calls[0]
    assert verb==method
    assert params['headers']['Prefer']=='return=representation'
    if revision==1:
        assert params['params'] is None  # unique insertion; never an upsert
    else:
        assert params['params']==dict(account_id='eq.student',home_school_key=f'eq.{record.home_school_key}',
            template_id='eq.consent',revision='eq.1')


@pytest.mark.parametrize('method,status,body', [('insert',409,b'{"code":"23505"}'),('update',200,b'[]'),('delete',200,b'[]')])
def test_atomic_draft_conflicts_never_report_success(monkeypatch,tmp_path,method,status,body):
    record=encrypted_record(tmp_path)
    def request(*args,**kwargs):
        response=requests.Response();response.status_code=status;response._content=body
        return response
    monkeypatch.setattr('exchange_info.form_drafts.supabase_http.request',request)
    repo=SupabaseFormDraftRepository('https://isolated.test','key')
    with pytest.raises(_RevisionConflict):
        if method=='delete': repo.delete_record('student',record.home_school_key,'consent',revision=1)
        else: repo.save_record(record.model_copy(update={'revision':1 if method=='insert' else 2}))


def test_independent_services_cannot_overwrite_same_draft_revision(tmp_path):
    # Force both workers to read revision zero before either commits.
    barrier=threading.Barrier(2)
    class AtomicRepository:
        atomic_revisions=True
        def __init__(self): self.row=None;self.reads=0;self.lock=threading.Lock()
        def find_record(self,*args):
            with self.lock:
                row=self.row; self.reads+=1; wait=self.reads<=2
            if wait: barrier.wait(timeout=5)
            return row
        def save_record(self,record):
            with self.lock:
                if record.revision!=(self.row.revision if self.row else 0)+1: raise _RevisionConflict()
                self.row=record
                return record
    repo=AtomicRepository()
    services=[FormDraftService(repo,b'k'*32) for _ in range(2)]
    def save(index):
        try: return services[index].save_draft('student','consent',payload(marker=str(index)))
        except FormDraftConflictError as error: return error
    with ThreadPoolExecutor(max_workers=2) as pool:
        results=list(pool.map(save,range(2)))
    assert sum(isinstance(x,FormDraftConflictError) for x in results)==1
    winner=next(x for x in results if not isinstance(x,FormDraftConflictError))
    loser=next(x for x in results if isinstance(x,FormDraftConflictError))
    assert winner.revision==1 and loser.current==winner


def load_module():
    path=Path(__file__).resolve().parents[1]/'deploy/capacity/load.py'
    spec=importlib.util.spec_from_file_location('capacity_load',path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module


@pytest.mark.parametrize('status,identity',[(404,{}),(200,{'run_id':'wrong','purpose':'isolated-capacity-test'})])
def test_live_or_foreign_target_gets_no_token_or_writes(status,identity):
    module=load_module();seen=[]
    def respond(request):
        seen.append(request)
        return httpx.Response(status,json=identity)
    async def check():
        async with httpx.AsyncClient(base_url='https://example.test',transport=httpx.MockTransport(respond)) as client:
            with pytest.raises(module.CheckFailed): await module.verify_target(client,'a'*32)
    with ThreadPoolExecutor(max_workers=1) as pool: pool.submit(asyncio.run,check()).result(timeout=10)
    assert len(seen)==1 and seen[0].method=='GET' and 'authorization' not in seen[0].headers


def test_duplicate_or_expired_load_fixtures_are_rejected():
    module=load_module();run_id='a'*32
    fixture=dict(run_id=run_id,expires_at=(utc_now()+timedelta(hours=1)).isoformat(),
        actors=[{'account_id':f'capacity-{run_id}-{i:05d}','token':str(i)} for i in range(4)])
    module.validate_fixture(fixture,run_id,2)
    fixture['actors'][1]['token']='0'
    with pytest.raises(module.CheckFailed): module.validate_fixture(fixture,run_id,2)
    fixture['actors'][1]['token']='1'
    fixture['expires_at']=(utc_now()-timedelta(seconds=1)).isoformat()
    with pytest.raises(module.CheckFailed): module.validate_fixture(fixture,run_id,2)


def test_selfhost_worker_limits_are_configurable_and_restored(tmp_path,monkeypatch):
    from anyio.to_thread import current_default_thread_limiter
    from exchange_info.api import create_app
    monkeypatch.setenv('EXCHANGE_WORKER_THREADS','16')
    monkeypatch.setenv('EXCHANGE_CATALOGUE_CONCURRENCY','2')
    app=create_app(tmp_path)
    async def check():
        limiter=current_default_thread_limiter();before=limiter.total_tokens
        async with app.router.lifespan_context(app): assert limiter.total_tokens==16
        assert limiter.total_tokens==before
    with ThreadPoolExecutor(max_workers=1) as pool: pool.submit(asyncio.run,check()).result(timeout=10)
    monkeypatch.setenv('EXCHANGE_WORKER_THREADS','0')
    with pytest.raises(RuntimeError,match='EXCHANGE_WORKER_THREADS'): create_app(tmp_path)


def test_capacity_stack_cannot_share_production_volumes_ports_or_privileged_load_keys():
    import yaml
    root=Path(__file__).resolve().parents[1]
    stage=yaml.safe_load((root/'deploy/capacity/compose.yml').read_text())
    production=yaml.safe_load((root/'deploy/selfhost/docker-compose.yml').read_text())
    assert stage['name']=='uniway-capacity'
    assert all(not value.get('name') for value in stage['volumes'].values())
    published={name:svc['ports'] for name,svc in stage['services'].items() if svc.get('ports')}
    assert published=={'web':['127.0.0.1:18000:8080']}
    for name in ('db','rest','storage'):
        assert stage['services'][name]['image']==production['services'][name]['image']
    assert not any('SECRET_KEY' in key or 'PASSWORD' in key for key in stage['services']['load']['environment'])
    assert stage['services']['load']['volumes']==['./load.py:/opt/capacity/load.py:ro','./artifacts:/artifacts']
    assert '/capacity/identity' not in (root/'src/exchange_info/api.py').read_text()
    script=(root/'deploy/capacity/Stage.ps1').read_bytes()
    assert script.isascii()
    assert b'--project-name uniway-capacity' in script
    assert b'lib.ps1' not in script and b'04-apply-migrations.ps1' not in script


def test_http_200_with_wrong_account_contents_fails_persistence_check():
    module=load_module()
    reads=0
    def respond(request):
        nonlocal reads
        if request.method=='PUT':
            return httpx.Response(200,json={'workspace':{'revision':1}})
        reads+=1
        return httpx.Response(200,json={'workspace':{'revision':0 if reads==1 else 1,
            'selection_conditions':{'profile':{'course_interests':'another-student'}}}})
    async def check():
        async with httpx.AsyncClient(base_url='http://isolated.test',transport=httpx.MockTransport(respond)) as client:
            load=module.Workload(client,{'school':'長庚大學'})
            with pytest.raises(module.CheckFailed,match='persistence or account isolation'):
                await load.workspace({'token':'synthetic'},'expected-marker')
    with ThreadPoolExecutor(max_workers=1) as pool: pool.submit(asyncio.run,check()).result(timeout=10)
