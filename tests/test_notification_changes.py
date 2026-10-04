"""Publication authorization and student-scoped field-level change evidence."""
import hashlib
from datetime import timedelta

from fastapi.testclient import TestClient

from exchange_info.api import create_app
from exchange_info.content_governance import LocalContentGovernanceStore, stage_workflow_refresh, workflow_review_source_urls, workflow_review_rule_keys
from exchange_info.models import AccountSessionRecord, ApplicationRuleScope, UserAccount, utc_now
from exchange_info.repositories import JsonlAccountRepository
from test_notifications import _content_account, _content_workflow, _published_content_store


def session(repository, account, token):
    repository.save_account(account)
    repository.save_session(AccountSessionRecord(account_id=account.id,
        token_hash=hashlib.sha256(token.encode()).hexdigest(), expires_at=utc_now()+timedelta(hours=1)))
    return {"Authorization":f"Bearer {token}"}


def test_changes_are_owned_and_hide_unrelated_department_and_reviewer(tmp_path):
    store, published = _published_content_store(tmp_path/'content')
    # A modern workspace stores application_round separately from the semester.
    student = _content_account()
    student.application_workspaces[0].application_context.application_round = '第一梯次'
    student.application_workspaces[0].application_context.semester = '2027 春季'
    unrelated = published.workflow.steps[0].model_copy(update={
        'rule_id':'nursing-private-scope', 'title':'護理學系專用規定',
        'scope':ApplicationRuleScope(departments=['護理學系']),
    })
    published = published.model_copy(update={'workflow':published.workflow.model_copy(
        update={'steps':[*published.workflow.steps, unrelated]})})
    store.save_revision(published)
    repository = JsonlAccountRepository(tmp_path/'accounts')
    headers = session(repository,student,'student-changes')
    foreign = session(repository,UserAccount(email='foreign@example.com',display_name='別的學生'),'foreign-changes')
    client = TestClient(create_app(tmp_path/'app',account_repository=repository,content_governance_store=store))
    rows = client.get('/account/notifications',headers=headers).json()['items']
    assert len(rows) == 1
    notification_id = rows[0]['id']
    endpoint=f'/account/notifications/{notification_id}/changes'
    assert client.get(endpoint).status_code == 401
    assert client.get(endpoint,headers=foreign).status_code == 404
    response=client.get(endpoint,headers=headers)
    assert response.status_code == 200
    assert 'no-store' in response.headers['cache-control']
    result=response.json()
    assert result['has_base'] and result['matches_current_plan']
    assert [row['step_key'] for row in result['step_changes']] == ['eligibility']
    title_change=next(row for row in result['step_changes'][0]['changes'] if row['field']=='title')
    assert title_change['before']=='舊版資格' and title_change['after']=='新版資格與文件'
    assert 'review_approvals' not in response.text and 'content-admin' not in response.text
    student.application_workspaces[0].application_context.academic_year='117'
    repository.save_account(student)
    result=client.get(endpoint,headers=headers).json()
    assert not result['matches_current_plan'] and result['step_changes'] == []


def test_review_gate_rejects_non_admin_duplicate_and_incomplete_publication(tmp_path,monkeypatch):
    repository=JsonlAccountRepository(tmp_path/'accounts')
    store=LocalContentGovernanceStore(tmp_path/'content')
    store.publish_workflow(_content_workflow('舊版本',version=1),'baseline')
    revision=stage_workflow_refresh(store,_content_workflow('新版本',version=1),detected_by='fixture').revision
    admin=UserAccount(email='admin@example.com',display_name='審查 A')
    second=UserAccount(email='second@example.com',display_name='審查 B')
    outsider=UserAccount(email='outsider@example.com',display_name='一般學生')
    headers=session(repository,admin,'admin-review')
    second_headers=session(repository,second,'second-review')
    foreign=session(repository,outsider,'outsider-review')
    monkeypatch.setenv('EXCHANGE_CONTENT_ADMIN_EMAILS',f'{admin.email},{second.email}')
    client=TestClient(create_app(tmp_path/'app',account_repository=repository,content_governance_store=store))
    endpoint=f'/admin/application-workflow-revisions/{revision.id}'
    payload={'expected_content_hash':revision.content_hash,'reviewed_source_urls':workflow_review_source_urls(revision.workflow),
             'reviewed_rule_keys':workflow_review_rule_keys(revision.workflow),'note':'測試資料已核對'}
    assert client.get('/admin/application-workflow-revisions').status_code==401
    assert client.get('/admin/application-workflow-revisions',headers=foreign).status_code==403
    assert client.post(endpoint+'/approve',headers=foreign,json=payload).status_code==403
    assert client.post(endpoint+'/publish',headers=headers,json={}).status_code==409
    assert client.post(endpoint+'/approve',headers=headers,json={**payload,'expected_content_hash':'0'*64}).status_code==409
    assert client.post(endpoint+'/approve',headers=headers,json={**payload,'reviewer_id':second.id}).status_code==422
    approved=client.post(endpoint+'/approve',headers=headers,json=payload)
    assert approved.status_code==200 and approved.json()['review_approvals'][0]['reviewer_id']==admin.id
    assert client.post(endpoint+'/approve',headers=headers,json=payload).status_code==409
    assert client.post(endpoint+'/publish',headers=headers,json={}).status_code==409
    assert client.post(endpoint+'/approve',headers=second_headers,json=payload).status_code==200
    assert client.post(endpoint+'/publish',headers=second_headers,json={}).status_code==200
    assert client.post(endpoint+'/publish',headers=second_headers,json={}).status_code==409
