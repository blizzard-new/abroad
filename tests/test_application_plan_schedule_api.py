from cgu_catalogue_fixture import fixed_cgu_catalogue
from test_application_plan_api import _verified_client, _partner, _workflow, _payload
from exchange_info.storage import ensure_data_dirs, replace_application_workflow


def setup_plan(tmp_path, monkeypatch):
    ensure_data_dirs(tmp_path)
    partner=_partner("測試合作校")
    replace_application_workflow(_workflow("長庚大學",partner.school_name),tmp_path)
    monkeypatch.setattr('exchange_info.api.create_cgu_catalogue',fixed_cgu_catalogue(lambda:[partner]))
    client=_verified_client(tmp_path)
    payload=_payload("長庚大學",[partner.school_name],"資訊工程學系")
    plan=client.post("/application-plan/evaluate",json=payload).json()
    return client,payload,plan


def test_current_plan_schedule_and_saved_settings_preserve_legacy_clients(tmp_path,monkeypatch):
    client,payload,plan=setup_plan(tmp_path,monkeypatch)
    key=plan['tasks'][0]['id']
    settings={key:{"effort_hours":3,"remaining_hours":1,"personal_due_date":"2026-10-09","document_id":"study-plan"}}
    response=client.post('/application-plan/schedule',json={"plan":payload,"task_settings":settings,
        "availability":{"weekly_hours":6,"weekdays":[1,3,5]},"as_of":"2026-10-05"})
    assert response.status_code == 200,response.text
    assert "no-store" in response.headers['cache-control']
    result=response.json()
    assert result['schedule']['work_sessions'][0]['hours'] == 1
    assert result['schedule']['items'][0]['deadline_kind'] == 'personal'
    before=client.get('/account/workspace').json()
    assert before['exists'] is False  # A scheduling preview does not persist.
    workspace=before['workspace']; workspace['preparation_tasks']=settings
    assert client.put('/account/workspace',json=workspace).status_code == 200
    restored=client.get('/account/workspace').json()['workspace']
    assert restored['preparation_tasks'][key]['remaining_hours'] == 1
    restored.pop('preparation_tasks')
    assert client.put('/account/workspace',json=restored).status_code == 200
    restored=client.get('/account/workspace').json()['workspace']
    assert restored['preparation_tasks'][key]['remaining_hours'] == 1
    restored['preparation_tasks']={}
    assert client.put('/account/workspace',json=restored).status_code == 200
    assert client.get('/account/workspace').json()['workspace']['preparation_tasks'] == {}


def test_schedule_home_isolation_entitlements_and_source_snapshot_rejection(tmp_path,monkeypatch):
    client,payload,plan=setup_plan(tmp_path,monkeypatch)
    request={"plan":payload,"availability":{"weekdays":[1]}}
    assert client.post('/application-plan/schedule',json={**request,"plan_snapshot":plan}).status_code == 422
    # Any supported school may be scheduled; this plan's partner is not on NTPU's list, so it is invalid.
    request['plan']={**payload,"home_school":"國立臺北大學"}
    assert client.post('/application-plan/schedule',json=request).status_code == 422
    request['plan']={**payload,"home_school":"國立某某大學"}
    assert client.post('/application-plan/schedule',json=request).status_code == 422
    request['plan']=payload
    monkeypatch.setenv('EXCHANGE_PRODUCT_RELEASE_MODE','public')
    assert client.post('/application-plan/schedule',json=request).status_code == 403
    client.headers.pop('Authorization')
    assert client.post('/application-plan/schedule',json=request).status_code == 401
