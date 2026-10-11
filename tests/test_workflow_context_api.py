from cgu_catalogue_fixture import fixed_cgu_catalogue
from fastapi.testclient import TestClient

from exchange_info.api import create_app
from exchange_info.content_governance import LocalContentGovernanceStore
from exchange_info.models import PartnerUniversity
from test_application_rules import _workflow
from test_notification_changes import session
from exchange_info.models import UserAccount
from exchange_info.repositories import JsonlAccountRepository


def test_details_use_effective_rounds_and_department_overrides(tmp_path,monkeypatch):
    import exchange_info.api as api
    workflow=_workflow().model_copy(update={
        'home_university':'長庚大學','academic_year':'116',
        'application_round':None,'effective_application_rounds':['第一梯次','第二梯次'],
    })
    store=LocalContentGovernanceStore(tmp_path)
    store.publish_workflow(workflow,'fixture')
    partner=PartnerUniversity(program_type='交換學生',country='日本',school_name=workflow.school_name,
        website='https://example.edu/',source_url='https://example.edu/exchange')
    monkeypatch.setattr(api,'create_cgu_catalogue',fixed_cgu_catalogue(lambda:[partner]))
    repository=JsonlAccountRepository(tmp_path)
    auth=session(repository,UserAccount(display_name='規則測試',student_status_verified=True,
        verified_university='長庚大學',verified_department='資訊工程學系'),'workflow-context-token')
    client=TestClient(create_app(tmp_path,account_repository=repository,content_governance_store=store))
    client.headers.update(auth)
    params={'school':workflow.school_name,'home_school':'長庚大學','academic_year':'116',
            'application_round':'第一梯次','department':'資訊工程學系'}
    response=client.get('/application-workflow',params=params)
    assert response.status_code==200
    result=response.json()
    assert [step['title'] for step in result['steps']]==['資工系紙本送件','資工系額外系主任簽章','116 第一梯次補件']
    assert result['applied_context']['department']=='資訊工程學系'
    assert client.get('/application-workflow',params={**params,'application_round':'第二梯次'}).json()['steps']
    assert client.get('/application-workflow',params={**params,'application_round':'第三梯次'}).json()['steps']==[]
    assert client.get('/application-workflow',params={**params,'academic_year':'117'}).json()['steps']==[]
    assert [row.title for row in store.load_published_workflows()[0].steps]==[row.title for row in workflow.steps]
