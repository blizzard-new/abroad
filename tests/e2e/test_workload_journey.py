from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import pytest
import requests
from playwright.sync_api import expect

from .test_glass_theme import verified_login, capture
from .test_web_next_phase import _auth_headers


def workload_response(response):
    return (response.url.endswith('/calendar/tasks/schedule') and response.request.method == 'POST'
            and response.request.post_data_json.get('availability') is not None)


def seed_tasks(page, live_server):
    session = verified_login(page, live_server)
    headers = _auth_headers(session)
    endpoint = f"{live_server.base_url}/account/workspace"
    page.wait_for_function("() => document.querySelector('#account-workspace-sync-label').textContent === '已同步'")
    payload = requests.get(endpoint, params={"home_school":"長庚大學"}, headers=headers).json()["workspace"]
    deadline = (datetime.now(ZoneInfo("Asia/Taipei")).date() + timedelta(days=30)).isoformat()
    payload["deadline_events"] = [
        dict(id="common", title="校內文件準備", date=deadline, preparation_days=7, effort_hours=2),
        dict(id="branch", title="合作校表格準備", date=deadline, preparation_days=7, effort_hours=4, depends_on=["common"]),
    ]
    saved = requests.put(endpoint, headers=headers, json=payload)
    for _ in range(3):
        if saved.status_code != 409:
            break
        latest = requests.get(endpoint, params={"home_school":"長庚大學"}, headers=headers).json()["workspace"]
        latest["deadline_events"] = payload["deadline_events"]
        saved = requests.put(endpoint, headers=headers, json=latest)
    saved.raise_for_status()
    page.reload()
    page.evaluate("location.hash='#overview'")
    page.locator('#application-schedule-details > summary').click()
    expect(page.locator('#journey-workspace')).to_be_visible()
    expect(page.locator('[data-journey-task-row]')).to_have_count(2)
    return headers, endpoint


@pytest.mark.parametrize("width", [390,1754])
def test_capacity_persists_replans_and_document_action_focuses_first_gap(page, live_server, width):
    page.set_viewport_size({"width":width,"height":956})
    page.emulate_media(reduced_motion="reduce")
    errors = []
    page.on("pageerror", lambda error: errors.append(str(error)))
    headers, endpoint = seed_tasks(page, live_server)
    page.locator('#journey-capacity-settings > summary').click()
    settings = page.locator('#journey-availability-form')
    settings.locator('[name=weekly_hours]').fill('8')
    with page.expect_response(workload_response) as scheduled:
        settings.get_by_role('button',name='依剩餘工作重新安排').click()
    report = scheduled.value.json()
    assert report['mode'] == 'workload'
    assert report['issues'] == []
    assert report['work_sessions'][0]['event_id'] == 'common'
    expect(page.locator('#journey-schedule-result')).to_contain_text('你的工作安排')
    page.locator('#journey-task-settings > summary').click()
    row = page.locator('[data-journey-task-row="branch"]')
    row.locator('summary').click()
    form = row.locator('form')
    expect(form.locator('[name=document_id] option')).not_to_have_count(1)
    document_id = form.locator('[name=document_id] option').nth(1).get_attribute('value')
    form.locator('[name=document_id]').select_option(document_id)
    form.locator('[name=remaining_hours]').fill('1')
    with page.expect_response(lambda response: workload_response(response) and any(row.get('remaining_hours') == 1 for row in response.request.post_data_json['events'])) as replanned:
        form.get_by_role('button',name='保存這項工作並重排').click()
    report = replanned.value.json()
    assert sum(item['hours'] for item in report['work_sessions'] if item['event_id'] == 'branch') == 1
    page.wait_for_function("() => document.querySelector('#account-workspace-sync-label').textContent === '已同步'")
    restored = requests.get(endpoint, params={"home_school":"長庚大學"}, headers=headers).json()['workspace']
    assert restored['planning_availability']['weekly_hours'] == 8
    branch = next(item for item in restored['deadline_events'] if item['id'] == 'branch')
    assert branch['remaining_hours'] == 1
    assert branch['depends_on'] == ['common']
    assert branch['document_id'] == document_id
    page.reload()
    expect(page.locator('#journey-schedule-result')).to_contain_text('你的工作安排')
    page.locator('#application-schedule-details > summary').click()
    page.locator('#journey-capacity-settings > summary').click()
    expect(page.locator('#journey-availability-form [name=weekly_hours]')).to_have_value('8')
    assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
    capture(page, f'workload-journey-{width}.png')
    page.locator('#journey-schedule-result [data-journey-document]').first.click()
    expect(page.locator('#application-form-page')).to_be_visible()
    focused = page.locator('#application-document-fields [data-application-field]:focus')
    expect(focused).to_have_count(1)
    assert focused.get_attribute('required') is not None
    assert errors == []


def test_waiting_then_resuming_does_not_reset_completed_work(page, live_server):
    seed_tasks(page, live_server)
    page.locator('#journey-capacity-settings > summary').click()
    page.locator('#journey-availability-form').get_by_role('button').click()
    expect(page.locator('#journey-schedule-result')).to_contain_text('你的工作安排')
    page.locator('#journey-task-settings > summary').click()
    row = page.locator('[data-journey-task-row="common"]')
    row.locator('summary').click()
    form = row.locator('form')
    form.locator('[name=waiting_reason]').fill('等系辦回覆')
    form.get_by_role('button').click()
    expect(page.locator('#journey-today')).to_contain_text('等系辦回覆')
    expect(page.locator('#journey-schedule-result')).to_contain_text('前置任務尚不能安排')
    row.locator('summary').click()
    form.locator('[name=waiting_reason]').fill('')
    form.locator('[name=status]').select_option('ready')
    with page.expect_response(lambda response: workload_response(response) and any(row['id'] == 'common' and row['status'] == 'ready' for row in response.request.post_data_json['events'])) as replanned:
        form.get_by_role('button').click()
    report = replanned.value.json()
    assert not any(item['event_id'] == 'common' for item in report['work_sessions'])
    assert any(item['event_id'] == 'branch' for item in report['work_sessions'])
