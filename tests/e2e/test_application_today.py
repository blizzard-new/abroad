"""我的申請 · 今天: one task to do now, the next confirmed deadline, stage progress and the rule-check status."""
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
    expect(page.locator('#progress-view')).to_be_hidden()
    expect(today.locator('.today-focus h2')).not_to_be_empty()
    start = today.locator('.today-primary')
    expect(start).to_have_attribute('href', re.compile(r'view=level&level='))
    assert today.locator('.today-queue li').count() <= 5
    # one place for the numbers: the headline progress and the stage bar agree with the plan header
    caption = page.locator('#overall-caption')
    expect(caption).to_have_text(re.compile(r'^0 / \d+ 項$'))
    expect(today.locator('.today-head')).to_contain_text(caption.inner_text())
    expect(today.locator('.today-boundary')).to_contain_text('不代表校方受理或錄取')
    # no confirmed deadline in the test data: say so, never guess a date
    expect(today.locator('.today-panel').first).to_contain_text('目前沒有已確認的期限')
    assert page.evaluate('document.documentElement.scrollWidth <= window.innerWidth')
    for text in ('今天', '準備清單', '申請路徑'):
        expect(page.locator('.hub-tabs').get_by_text(text, exact=True)).to_be_visible()
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
    # the summary on 今天 counts exactly the same rule checks
    page.goto(f'{live_server.base_url}/#my-application?' + urlencode({'plan': created['plan']['id'], 'view': 'today'}))
    expect(page.locator('#today-view .today-counts')).to_be_visible()
    counts = page.locator('#today-view .today-counts b').all_text_contents()
    assert sum(int(x) for x in counts) == len(checks)
