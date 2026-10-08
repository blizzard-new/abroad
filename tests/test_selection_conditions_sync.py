"""Account-owned conditions survive devices, older clients and explicit clearing."""
import pytest
import hashlib
from datetime import timedelta
from pathlib import Path

from exchange_info.models import AccountSessionRecord, UserAccount, utc_now
from exchange_info.repositories import JsonlAccountRepository
from test_account_workspace_api import _two_session_clients, _workspace, _client


def profile():
    return {"college":"工學院", "department":"資訊工程學系", "current_year":"大三",
            "degree_level":"大學部", "academic_score":88.5, "academic_gpa":None,
            "class_rank_percent":None, "language_test":"ielts",
            "language_score":7, "monthly_budget":42000, "preferred_country":"日本",
            "target_term":"2027 春季", "needs_scholarship":True,
            "academic_year":"116", "application_round":"第一梯次",
            "preferred_teaching_language":"english", "course_interests":"資料科學"}


def test_conditions_persist_across_sessions_and_legacy_write_does_not_erase(tmp_path):
    device_a, device_b, auth_a, auth_b = _two_session_clients(tmp_path)
    payload = {**_workspace(), "selection_conditions":{"profile":profile()}}
    written = device_a.put('/account/workspace',headers=auth_a,json=payload)
    assert written.status_code == 200
    read = device_b.get('/account/workspace',headers=auth_b).json()['workspace']
    assert read['selection_conditions']['profile'] == profile()
    old_client = {**_workspace(), 'revision':read['revision']}
    old_client['favorite_schools'] = []
    preserved = device_b.put('/account/workspace',headers=auth_b,json=old_client)
    assert preserved.status_code == 200
    assert preserved.json()['workspace']['selection_conditions']['profile'] == profile()
    clear = {**preserved.json()['workspace'], 'selection_conditions':{'profile':None}}
    assert device_a.put('/account/workspace',headers=auth_a,json=clear).status_code == 200
    assert device_b.get('/account/workspace',headers=auth_b).json()['workspace']['selection_conditions'] == {'profile':None}


@pytest.mark.parametrize('field,value', [('academic_score',101),('language_test','invented'),('monthly_budget',-1),('phone','0912345678')])
def test_conditions_reject_invalid_or_unrelated_fields(tmp_path,field,value):
    client, auth = _client(tmp_path)
    response=client.put('/account/workspace',headers=auth,json={**_workspace(),'selection_conditions':{'profile':{**profile(),field:value}}})
    assert response.status_code == 422
    assert client.get('/account/workspace',headers=auth).json()['exists'] is False


def test_conditions_require_login_and_are_isolated_by_account_and_home(tmp_path):
    client, auth = _client(tmp_path)
    assert client.put('/account/workspace',headers=auth,json={**_workspace(),'selection_conditions':{'profile':profile()}}).status_code == 200
    other_home=client.get('/account/workspace?home_school=國立臺北大學',headers=auth).json()
    assert other_home['exists'] is False
    assert other_home['workspace']['selection_conditions'] is None
    repository=JsonlAccountRepository(tmp_path)
    other=repository.save_account(UserAccount(display_name='另一位學生'))
    other_token='other-conditions-test-session'
    repository.save_session(AccountSessionRecord(account_id=other.id,token_hash=hashlib.sha256(other_token.encode()).hexdigest(),expires_at=utc_now()+timedelta(days=1)))
    other_read=client.get('/account/workspace',headers={'Authorization':f'Bearer {other_token}'}).json()
    assert other_read['exists'] is False
    assert other_read['workspace']['selection_conditions'] is None
    # An unauthenticated request cannot observe either the profile or its existence.
    assert client.get('/account/workspace').status_code == 401


def test_workspace_extension_migration_keeps_atomic_commit_and_progress_ownership():
    root=Path(__file__).parents[1]/'supabase'/'migrations'
    sql=(root/'20261002120000_workspace_selection_and_planning.sql').read_text(encoding='utf-8')
    previous=(root/'20260823130000_atomic_workspace_and_suspension.sql').read_text(encoding='utf-8')
    # Exact retention of the commit section, not just the presence of lock keywords.
    start='  select account.*'
    end='\n$$;'
    assert sql[sql.index(start):sql.index(end)] == previous[previous.index(start,previous.index('create or replace function public.exchange_commit_account_workspace(')):previous.index(end,previous.index('create or replace function public.exchange_commit_account_workspace('))]
    assert "'selection_conditions'" in sql and "'planning_availability'" in sql
    assert "'discovery'" in sql and "'preparation_tasks'" in sql
    assert "'effort_hours'" in sql and "'document_id'" in sql
    assert 'from public, anon, authenticated, service_role' in sql
    assert ') to service_role;' in sql


def test_older_client_without_teaching_language_or_course_fields_still_round_trips(tmp_path):
    client, auth = _client(tmp_path)
    legacy = {key: value for key, value in profile().items() if key not in {"preferred_teaching_language", "course_interests"}}
    saved = client.put('/account/workspace',headers=auth,json={**_workspace(),'selection_conditions':{'profile':legacy}})
    assert saved.status_code == 200
    stored = saved.json()['workspace']['selection_conditions']['profile']
    assert stored['preferred_teaching_language'] is None and stored['course_interests'] == ''
