import pytest
import requests
import os
from pathlib import Path
from playwright.sync_api import expect

from exchange_info.models import ApplicationStep, ApplicationRuleScope, UniversityApplicationWorkflow
from exchange_info.storage import replace_application_workflow
from .test_glass_theme import verified_login, capture
from .test_web_next_phase import _auth_headers


def response_for(response):
    return response.url.endswith('/application-plan/schedule') and response.request.method == 'POST'


@pytest.mark.parametrize('width',[390,1754])
def test_real_shared_plan_settings_schedule_documents_and_reload(page,live_server,width):
    page.set_viewport_size({'width':width,'height':956})
    page.emulate_media(reduced_motion='reduce')
    session=verified_login(page,live_server)
    errors=[]
    page.on('pageerror',lambda error:errors.append(str(error)))
    page.evaluate("location.hash='#overview'")
    page.locator('#multi-plan-settings > summary').click()
    page.wait_for_function("() => state.dashboard && document.querySelector('#multi-plan-preferences select').options.length > 1",timeout=30000)
    selects=page.locator('#multi-plan-preferences select')
    names=selects.first.locator('option').evaluate_all('rows=>rows.filter(row=>row.value).slice(0,2).map(row=>row.value)')
    # Source fixtures are saved only to the isolated server. Both evaluate and
    # schedule use the real API and its current catalogue; no response interception.
    for name in names:
        common=ApplicationStep(rule_id='shared',order=1,phase='校內申請',title='共用文件準備',
            responsible_party='學生',summary='準備共用的校內文件',support_status='verified',
            scope=ApplicationRuleScope(home_universities=['長庚大學']),source_urls=['https://home.edu/notice'])
        branch=ApplicationStep(rule_id='host',depends_on_rule_ids=['shared'],order=2,phase='合作校申請',
            title='合作校文件準備',responsible_party='學生',summary='準備合作校表格',support_status='verified',
            scope=ApplicationRuleScope(partner_universities=[name]),source_urls=['https://host.edu/notice'])
        replace_application_workflow(UniversityApplicationWorkflow(home_university='長庚大學',school_name=name,
            academic_year='119',application_round='隔離驗證梯次',review_status='published',steps=[common,branch]),live_server.data_dir)
    endpoint=f'{live_server.base_url}/account/workspace'
    page.wait_for_function("() => document.querySelector('#account-workspace-sync-label').textContent === '已同步'")
    workspace=requests.get(endpoint,headers=_auth_headers(session)).json()['workspace']
    workspace['application_context'].update(academic_year='119',application_round='隔離驗證梯次')
    requests.put(endpoint,headers=_auth_headers(session),json=workspace).raise_for_status()
    page.reload()
    page.locator('#multi-plan-settings > summary').click()
    page.wait_for_function("() => state.dashboard && state.applicationContext.academic_year === '119' && document.querySelector('#multi-plan-preferences select').options.length > 1",timeout=30000)
    selects.nth(0).select_option(names[0]); selects.nth(1).select_option(names[1])
    page.locator('#multi-plan-preferences button').click()
    expect(page.locator('#multi-plan-status')).to_contain_text('2 個志願 · 3 項準備工作',timeout=30000)
    shared=page.locator('.multi-plan-shared [data-multi-task]')
    task_id=shared.get_attribute('data-multi-task')
    editor=page.locator(f'[data-multi-editor="{task_id}"]')
    editor.locator('summary').click()
    form=editor.locator('form')
    form.locator('[name=effort_hours]').fill('2')
    expect(form.locator('[name=document_id] option')).not_to_have_count(1)
    document_id=form.locator('[name=document_id] option').nth(1).get_attribute('value')
    form.locator('[name=document_id]').select_option(document_id)
    form.get_by_role('button',name='保存並重新安排').click()
    page.locator('#journey-capacity-settings > summary').click()
    capacity=page.locator('#journey-availability-form')
    capacity.locator('[name=weekly_hours]').fill('6')
    with page.expect_response(lambda response:response_for(response) and response.request.post_data_json['task_settings'].get(task_id,{}).get('effort_hours') == 2) as scheduled:
        capacity.get_by_role('button',name='依剩餘工作重新安排').click()
    result=scheduled.value.json()['schedule']
    assert sum(row['hours'] for row in result['work_sessions'] if row['event_id'] == task_id) == 2
    assert next(row for row in result['items'] if row['event_id'] == task_id)['deadline_date'] is None
    expect(page.locator('#journey-schedule-result')).to_contain_text('共用文件準備')
    page.locator('#journey-schedule-result [data-journey-document]').first.click()
    expect(page.locator('#application-form-page')).to_be_visible()
    focused=page.locator('#application-document-fields [data-application-field]:focus')
    expect(focused).to_have_count(1)
    assert focused.get_attribute('required') is not None
    page.evaluate("location.hash='#overview'")
    branches=page.locator('.multi-plan-branch')
    branches.first.locator('summary').first.click()
    branch_editor=branches.first.locator('[data-multi-editor]')
    branch_id=branch_editor.get_attribute('data-multi-editor')
    branch_editor.locator('summary').click()
    branch_form=branch_editor.locator('form')
    branch_form.locator('[name=effort_hours]').fill('3')
    expect(branch_form.locator('[name=depends_on]')).to_have_values([task_id])
    with page.expect_response(lambda response:response_for(response) and response.request.post_data_json['task_settings'].get(branch_id,{}).get('effort_hours') == 3) as scheduled:
        branch_form.get_by_role('button',name='保存並重新安排').click()
    result=scheduled.value.json()['schedule']
    assert any(row['event_id'] == branch_id for row in result['work_sessions'])
    branch_form.locator('[name=remaining_hours]').fill('1')
    with page.expect_response(lambda response:response_for(response) and response.request.post_data_json['task_settings'].get(branch_id,{}).get('remaining_hours') == 1) as replanned:
        branch_form.get_by_role('button',name='保存並重新安排').click()
    result=replanned.value.json()['schedule']
    assert sum(row['hours'] for row in result['work_sessions'] if row['event_id'] == branch_id) == 1
    with page.expect_response(lambda response:response_for(response) and response.request.post_data_json['task_settings'].get(task_id,{}).get('status') == 'ready') as completed:
        page.locator(f'[data-multi-task="{task_id}"]').check()
    result=completed.value.json()['schedule']
    assert not any(row['event_id'] == task_id for row in result['work_sessions'])
    assert any(row['event_id'] == branch_id for row in result['work_sessions'])
    page.wait_for_function("() => document.querySelector('#account-workspace-sync-label').textContent === '已同步'")
    saved=requests.get(endpoint,headers=_auth_headers(session)).json()['workspace']
    assert saved['preparation_tasks'][task_id]['status'] == 'ready'
    assert saved['preparation_tasks'][branch_id]['depends_on'] == [task_id]
    assert saved['preparation_tasks'][task_id]['document_id'] == document_id
    assert saved['preparation_tasks'][branch_id]['remaining_hours'] == 1
    page.reload()
    expect(page.locator(f'[data-multi-task="{task_id}"]')).to_be_checked(timeout=30000)
    expect(page.locator('#journey-schedule-result')).to_contain_text('合作校文件準備',timeout=30000)
    assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
    # Every allocated work day is visible on the real calendar, not merely a start marker.
    page.evaluate("location.hash='#calendar'")
    expect(page.locator('#calendar-task-schedule-list')).to_contain_text('個人完成目標')
    assert page.locator('[data-calendar-task-deadline="null"]').count() == 0
    page.evaluate("location.hash='#overview'")
    capture(page,f'unified-preparation-{width}.png')
    if width == 1754 and os.environ.get('UNIWAY_GLASS_ARTIFACT_DIR'):
        page.locator('#journey-workspace').scroll_into_view_if_needed()
        page.screenshot(path=str(Path(os.environ['UNIWAY_GLASS_ARTIFACT_DIR'])/'unified-schedule-desktop.png'),animations='disabled')
    assert errors == []
