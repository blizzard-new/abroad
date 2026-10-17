"""Plan tasks open the matching document, and unpublished years stay labelled as estimates."""
import pytest
from playwright.sync_api import expect

from .conftest import expand_details
from .test_glass_theme import verified_login


def choose_two_schools(page, academic_year='', application_round=''):
    page.evaluate("location.hash='#overview'")
    expand_details(page, "#application-plan-details")
    expect(page.locator('#multi-plan-workspace')).to_be_visible()
    page.locator('#multi-plan-settings > summary').click()
    page.wait_for_function("() => state.dashboard && document.querySelector('#multi-plan-preferences select').options.length > 1", timeout=30000)
    if academic_year:
        # Set after the account workspace has hydrated, or it would be overwritten.
        page.evaluate("([year, round]) => { state.applicationContext = {...state.applicationContext, academic_year:year, application_round:round}; }", [academic_year, application_round])
    selects = page.locator('#multi-plan-preferences select')
    names = selects.first.locator('option').evaluate_all('rows=>rows.filter(row=>row.value).slice(0,2).map(row=>row.value)')
    selects.nth(0).select_option(names[0])
    selects.nth(1).select_option(names[1])
    page.locator('#multi-plan-preferences button').click()
    return names


@pytest.mark.parametrize('width', [390, 1754])
def test_unpublished_year_shows_estimated_tasks_with_documents_and_suggested_hours(page, live_server, width):
    page.set_viewport_size({'width': width, 'height': 956})
    page.emulate_media(reduced_motion='reduce')
    errors = []
    page.on('pageerror', lambda error: errors.append(str(error)))
    verified_login(page, live_server)
    choose_two_schools(page, academic_year='116', application_round='第一梯次')
    expect(page.locator('#multi-plan-status')).to_contain_text('準備工作', timeout=30_000)
    page.locator('#multi-plan-tasks .multi-plan-branch > summary').first.click()
    tasks = page.locator('#multi-plan-tasks .multi-plan-branch[open] .multi-plan-task')
    expect(tasks.first).to_be_visible(timeout=30_000)
    expect(page.locator('.multi-plan-estimate-badge').first).to_contain_text('預估，非官方期限')
    expect(tasks.first).to_contain_text('預估：')
    # The estimated tasks never show an official deadline.
    assert page.locator('#multi-plan-tasks').inner_text().count('來源記載期限') == 0

    # A task with a matching preparation tool offers it, and the tool opens.
    open_buttons = page.locator('#multi-plan-tasks .multi-plan-branch[open] [data-journey-document]')
    expect(open_buttons.first).to_be_visible()
    template_id = open_buttons.first.get_attribute('data-journey-document')
    open_buttons.first.click()
    expect(page.locator('#application-document-form')).to_be_visible(timeout=15_000)
    assert page.evaluate('state.activeApplicationTemplateId') == template_id

    # Back on the plan: hours are not required because the system suggests them.
    page.evaluate("location.hash='#overview'")
    page.locator('#multi-plan-tasks .multi-plan-branch').first.evaluate('element => { element.open = true; }')
    expect(tasks.first).to_be_visible(timeout=15_000)
    tasks.first.locator('.multi-task-settings > summary').click()
    effort = tasks.first.locator('input[name="effort_hours"]')
    assert effort.get_attribute('required') is None
    assert '系統建議約' in (effort.get_attribute('placeholder') or '')
    assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
    assert errors == []
