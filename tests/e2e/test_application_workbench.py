"""我的申請 workbench: menu, semester picker, undo, 計畫 comparison, 時程 and the old 準備與時程 address."""
import re
from datetime import date
from urllib.parse import urlencode

import pytest
from playwright.sync_api import expect

from .test_glass_theme import verified_login


def make_plan(page, live_server, **changes):
    body = {'home_school': '長庚大學', 'target_school': '林肯大學 Lincoln University',
            'academic_year': '116', 'departure_year': '2027', 'semester': 'fall', 'revision': 0, **changes}
    response = page.request.post(f'{live_server.base_url}/account/application-paths', data=body)
    assert response.ok, response.text()
    return response.json()


def open_view(page, live_server, plan, view='today', **extra):
    page.goto(f'{live_server.base_url}/#my-application?' + urlencode({'plan': plan['plan']['id'], 'view': view, **extra}))


def test_header_actions_live_in_one_menu(page, live_server):
    verified_login(page, live_server)
    plan = make_plan(page, live_server)
    open_view(page, live_server, plan)
    expect(page.locator('#today-view')).to_be_visible()
    for selector in ('#new-plan', '#archive-plan', '#refresh-path'):
        expect(page.locator(selector)).to_be_hidden()
    page.locator('.ap-menu summary').click()
    for selector in ('#new-plan', '#archive-plan', '#refresh-path'):
        expect(page.locator(selector)).to_be_visible()
    page.keyboard.press('Escape')
    page.locator('#today-view').click(position={'x': 5, 'y': 5})
    expect(page.locator('#archive-plan')).to_be_hidden()


def test_new_plan_asks_for_a_semester_and_works_out_the_academic_year(page, live_server):
    verified_login(page, live_server)
    page.goto(f'{live_server.base_url}/#my-application')
    page.locator('[data-path-new]').first.click()
    expect(page.locator('#plan-dialog')).to_be_visible()
    options = page.locator('#create-semesters input[type=radio]')
    assert options.count() == 6  # four semesters, a full year, undecided
    for hidden in ('#create-year', '#create-departure'):
        expect(page.locator(hidden)).to_have_attribute('type', 'hidden')
    page.locator('#create-target').select_option(index=1)
    fall = page.locator('#create-semesters input[value^="fall:"]').first
    fall.check()
    year = int(fall.get_attribute('value').split(':')[1])
    expect(page.locator('#create-departure')).to_have_value(str(year))
    expect(page.locator('#create-year')).to_have_value(str(year - 1911))
    expect(page.locator('#create-term')).to_have_value('fall')
    expect(page.locator('#create-derived')).to_contain_text(f'{year - 1911} 學年度')
    spring = page.locator('#create-semesters input[value^="spring:"]').first
    spring.check()
    spring_year = int(spring.get_attribute('value').split(':')[1])
    expect(page.locator('#create-year')).to_have_value(str(spring_year - 1912))
    page.get_by_role('button', name='建立計畫', exact=True).click()
    expect(page.locator('#today-view')).to_be_visible()


def test_a_swapped_year_is_refused_by_the_server(page, live_server):
    verified_login(page, live_server)
    response = page.request.post(f'{live_server.base_url}/account/application-paths', data={
        'home_school': '長庚大學', 'target_school': '林肯大學 Lincoln University',
        'academic_year': '2027', 'departure_year': '116', 'semester': 'fall', 'revision': 0})
    assert response.status == 422
    assert '民國年' in response.text() or '西元年' in response.text()


def test_archive_has_no_browser_dialog_and_can_be_undone(page, live_server):
    verified_login(page, live_server)
    plan = make_plan(page, live_server)
    dialogs = []
    page.on('dialog', lambda d: (dialogs.append(d.message), d.dismiss()))
    open_view(page, live_server, plan)
    expect(page.locator('#today-view')).to_be_visible()
    page.locator('.ap-menu summary').click()
    page.locator('#archive-plan').click()
    toast = page.locator('#toast')
    expect(toast).to_contain_text('已封存')
    page.locator('#toast .toast-action').click()
    expect(page.locator('#toast')).to_contain_text('已恢復')
    page.locator('.ap-menu summary').click()
    expect(page.locator('#archive-plan')).to_have_text(re.compile('封存計畫'))
    assert dialogs == []


def test_finishing_a_task_shows_progress_and_can_be_undone(page, live_server):
    verified_login(page, live_server)
    plan = make_plan(page, live_server)
    open_view(page, live_server, plan, 'level', level='check-availability')
    page.get_by_role('button', name='確認內容', exact=True).click()
    toast = page.locator('#toast')
    expect(toast).to_contain_text(re.compile(r'準備進度 1 / \d+'))
    toast.locator('.toast-action').click()
    expect(page.locator('#toast')).to_contain_text('已撤銷')
    open_view(page, live_server, plan, 'progress')
    expect(page.locator('#overall-caption')).to_have_text(re.compile(r'^0 / \d+ 項$'))


def test_plans_view_compares_two_plans_side_by_side(page, live_server):
    verified_login(page, live_server)
    first = make_plan(page, live_server)
    make_plan(page, live_server, semester='spring', departure_year='2028', revision=first['revision'])
    open_view(page, live_server, first, 'plans')
    expect(page.locator('.plan-card')).to_have_count(2)
    table = page.locator('.plan-compare')
    expect(table).to_be_visible()
    for label in ('下個期限', '準備進度', '還缺的文件', '目前階段', '下一步'):
        expect(table.get_by_role('rowheader', name=label)).to_be_visible()
    expect(page.locator('.hub-tabs a[aria-current=page]')).to_have_attribute('data-tab', 'plans')


def test_old_schedule_address_opens_the_schedule_tab_with_this_plans_tasks(page, live_server):
    verified_login(page, live_server)
    plan = make_plan(page, live_server)
    open_view(page, live_server, plan)
    expect(page.locator('#today-view')).to_be_visible()
    page.evaluate('location.hash = "#overview"')
    expect(page.locator('#schedule-view')).to_be_visible()
    assert page.evaluate('location.hash') == '#my-application?view=schedule'
    expect(page.locator('.hub-tabs a[aria-current=page]')).to_have_attribute('data-tab', 'schedule')
    rows = page.locator('#schedule-view [data-tracker-row]')
    expect(rows.first).to_be_visible()
    assert rows.count() >= 3
    expect(rows.first.locator('a.pr-task-title')).to_have_attribute('href', re.compile('view=level'))
    expect(page.locator('#schedule-view .pr-stat').first).to_contain_text(re.compile(r'0 / \d+'))
    expect(page.locator('#schedule-view .sched-deadlines')).to_be_visible()
    # the old navigation item is gone
    expect(page.locator('.uniway-public-nav a[href="#overview"]')).to_have_count(0)


def test_a_personal_task_can_be_added_without_leaving_the_page(page, live_server):
    verified_login(page, live_server)
    plan = make_plan(page, live_server)
    open_view(page, live_server, plan)
    form = page.locator('[data-today-quick]')
    form.locator('input[name=title]').fill('請系主任簽名')
    form.locator('input[name=date]').fill(date.today().isoformat())
    form.get_by_role('button', name='加入').click()
    expect(page.locator('.today-own')).to_contain_text('請系主任簽名')
    assert '#my-application' in page.evaluate('location.hash')
    page.evaluate('location.hash = "#my-application?view=schedule"')
    expect(page.locator('#schedule-view')).to_contain_text('請系主任簽名')


def test_offline_save_says_so_in_plain_language_and_keeps_the_text(page, live_server):
    verified_login(page, live_server)
    plan = make_plan(page, live_server)
    open_view(page, live_server, plan, 'level', level='motivation')
    expect(page.locator('#level-input')).to_be_visible()
    page.context.set_offline(True)
    page.locator('#level-input').fill('我想去紐西蘭是因為…')
    expect(page.locator('#save-note')).to_have_text('尚未儲存，請重試', timeout=8000)
    expect(page.locator('#level-error')).to_contain_text('沒有網路連線')
    assert 'Failed to fetch' not in page.locator('#level-view').inner_text()
    expect(page.locator('#level-input')).to_have_value('我想去紐西蘭是因為…')
    page.context.set_offline(False)
    expect(page.locator('#save-note')).to_have_text('已儲存', timeout=15000)


@pytest.mark.parametrize('view', ['today', 'plans', 'schedule'])
def test_phone_layout_has_no_horizontal_scroll(page, live_server, view):
    page.set_viewport_size({'width': 390, 'height': 844})
    verified_login(page, live_server)
    plan = make_plan(page, live_server)
    open_view(page, live_server, plan, view)
    expect(page.locator(f'#{view}-view')).to_be_visible()
    page.wait_for_timeout(500)
    assert page.evaluate('document.documentElement.scrollWidth <= window.innerWidth + 1')
