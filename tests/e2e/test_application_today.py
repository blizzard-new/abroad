"""我的申請 · 總覽: one task to do now, the next confirmed deadline, and the whole checklist on the same page."""
import re
from urllib.parse import urlencode

import pytest
from playwright.sync_api import expect

from .test_glass_theme import verified_login


def create_plan(page, live_server):
    verified_login(page, live_server)
    response = page.request.post(f'{live_server.base_url}/account/application-paths', data={
        'home_school': '長庚大學', 'target_school': '林肯大學 Lincoln University',
        'academic_year': '116', 'departure_year': '2027', 'semester': 'fall', 'revision': 0,
    })
    assert response.ok, response.text()
    return response.json()


@pytest.mark.parametrize('width', [390, 1440])
def test_today_is_the_default_view_and_leads_with_one_task(page, live_server, width):
    page.set_viewport_size({'width': width, 'height': 844})
    created = create_plan(page, live_server)
    page.goto(f'{live_server.base_url}/#my-application?' + urlencode({'plan': created['plan']['id']}))
    today = page.locator('#today-view')
    expect(today).to_be_visible()
    # the checklist is part of the overview, not a second tab
    expect(page.locator('#progress-view')).to_be_visible()
    expect(page.locator('.hub-tabs a[data-tab="progress"]')).to_have_count(0)
    expect(today.locator('.today-focus h2')).not_to_be_empty()
    start = today.locator('.today-primary')
    expect(start).to_have_attribute('href', re.compile(r'view=level&level='))
    # exactly one primary action, and the next step is marked in the checklist
    expect(today.locator('.today-primary')).to_have_count(1)
    expect(page.locator('#progress-view .task-row.is-next')).to_have_count(1)
    # one place for the number: the plan header
    caption = page.locator('#overall-caption')
    expect(caption).to_have_text(re.compile(r'^0 / \d+ 項$'))
    expect(page.locator('#progress-view .today-boundary')).to_contain_text('不代表校方受理或錄取')
    # plan settings are not checklist rows
    for text in ('確認你的母校', '確認出國學期', '確認交換目標'):
        expect(page.locator('#progress-view').get_by_text(text, exact=True)).to_have_count(0)
    # no confirmed deadline in the test data: say so, never guess a date
    expect(today.locator('.today-panel').first).to_contain_text('目前沒有已確認的期限')
    assert page.evaluate('document.documentElement.scrollWidth <= window.innerWidth')
    for text in ('總覽', '時程', '我的待辦'):
        expect(page.locator('.hub-tabs').get_by_text(text, exact=True)).to_be_visible()
    # comparing plans is offered only when there is more than one plan
    expect(page.locator('.hub-tabs a[data-tab="plans"]')).to_be_hidden()
    first_tab = page.locator('.hub-tabs a').first
    expect(first_tab).to_have_attribute('data-tab', 'today')


def test_start_opens_the_task_and_back_returns_to_today(page, live_server):
    created = create_plan(page, live_server)
    base = f'{live_server.base_url}/#my-application?' + urlencode({'plan': created['plan']['id']})
    page.goto(base)
    page.locator('#today-view .today-primary').click()
    expect(page.locator('#level-view')).to_be_visible()
    page.go_back()
    expect(page.locator('#today-view')).to_be_visible()


def test_rule_check_status_is_shown_before_the_confirm_button(page, live_server):
    created = create_plan(page, live_server)
    checks = [l for s in created['stages'] for l in s['levels'] if l.get('check_status')]
    assert checks, 'the plan should contain rule-check levels'
    first = checks[0]
    page.goto(f'{live_server.base_url}/#my-application?' + urlencode({'plan': created['plan']['id'], 'view': 'level', 'level': first['id']}))
    status = page.locator('#level-view .check-status')
    expect(status).to_be_visible()
    expect(status).to_contain_text(re.compile('符合|不符合|待確認'))
    # the rule's standard explanation is no longer hidden behind a collapsed note
    expect(page.locator('#level-view details.ap-warning')).to_have_count(0)


def test_rule_checks_are_one_step_with_one_form(page, live_server):
    created = create_plan(page, live_server)
    checks = [l for s in created['stages'] for l in s['levels'] if l.get('check_status')]
    base = f'{live_server.base_url}/#my-application?' + urlencode({'plan': created['plan']['id']})
    page.goto(base)
    rows = page.locator('#progress-view .task-row')
    expect(rows.filter(has_text='申請資格')).to_have_count(1)
    for check in checks:
        expect(rows.get_by_text(check['title'], exact=True)).to_have_count(0)
    counted = int(page.locator('#overall-caption').inner_text().split('/')[1].replace('項', '').strip())
    rows.filter(has_text='申請資格').click()
    items = page.locator('#level-view .check-list li')
    expect(items).to_have_count(len(checks))
    for check in checks:
        expect(items.filter(has_text=check['title']).locator('b')).to_have_text(re.compile('符合|不符合|待確認'))
    # every rule that needs the student's data asks for it in the same form, saved once
    expect(page.locator('#level-view #gate-save')).to_have_count(1 if any(c.get('input_fields') for c in checks) else 0)
    assert counted == len([l for s in created['stages'] for l in s['levels'] if l['counted'] and not l.get('check_status')
                           and l['kind'] not in ('write', 'assemble')]) + 1
