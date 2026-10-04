"""Student decisions and recovery, with isolated accounts and source/date fixtures."""
from datetime import date, timedelta

import pytest
from playwright.sync_api import expect

from .test_glass_theme import verified_login, capture
from .test_planning_workspace import create_target, workflow_fixture


@pytest.mark.parametrize("width", [390, 1754])
def test_calendar_empty_state_enters_planning_and_bad_dates_offer_recovery(page, live_server, width):
    page.set_viewport_size({"width":width,"height":956})
    page.emulate_media(reduced_motion="reduce")
    page.route("**/application-workflow?**", lambda route: workflow_fixture(route, "expired"))
    create_target(page, live_server)
    page.evaluate("location.hash='#calendar'")
    page.locator('#calendar-agenda-list [data-open-planning]').click()
    expect(page.locator('#planning-academic-year')).to_be_focused()
    page.locator('#planning-academic-year').fill('116')
    page.locator('#planning-preview-button').click()
    expect(page.locator('#planning-schedule-recovery')).to_be_visible()
    expect(page.locator('#planning-schedule-recovery')).to_contain_text('本次申請學年度')
    expect(page.locator('#planning-confirm')).to_be_hidden()
    expect(page.locator('.planning-timeline-item')).to_have_count(0)
    page.locator('#planning-schedule-recovery [data-open-manual-task]').click()
    expect(page.locator('#calendar-event-form input[name=title]')).to_be_focused()
    assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')


@pytest.mark.parametrize("width", [390, 1754])
def test_task_duration_changes_require_new_preview_and_save_adjusted_start(page, live_server, width):
    page.set_viewport_size({"width":width,"height":956})
    page.emulate_media(reduced_motion="reduce")
    page.route('**/application-workflow?**', workflow_fixture)
    create_target(page, live_server)
    page.locator('#planning-academic-year').fill('116')
    page.locator('#planning-preview-button').click()
    duration = page.locator('[data-planning-duration]').first
    expect(duration).to_be_visible()
    duration.fill('5')
    expect(page.locator('#planning-confirm')).to_be_hidden()
    page.locator('#planning-update-durations').click()
    expect(page.locator('#planning-schedule-preview')).to_contain_text((date.today()+timedelta(days=35)).isoformat())
    expect(page.locator('#planning-confirm')).to_be_visible()
    expect(page.locator('[data-planning-duration]').first).to_have_value('5')
    page.locator('#planning-confirm').click()
    expect(page.locator('#planning-schedule-status')).to_contain_text('已加入')
    assert page.evaluate('state.calendarEvents.find(item=>item.id.startsWith("preparation-")).preparationDays') == 5
    assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
    capture(page, f'ux-task-durations-{width}.png')


def test_unknown_language_is_saved_without_zero_and_term_carries_to_documents(page, live_server):
    verified_login(page, live_server)
    page.evaluate("location.hash='#advisor'")
    page.wait_for_function("() => document.querySelector('#advisor-college').options.length > 1")
    college = page.locator('#advisor-college option').evaluate_all('rows=>rows.find(row=>row.value).value')
    page.locator('#advisor-college').select_option(college)
    page.locator('#advisor-degree').select_option('大學部')
    page.locator('#advisor-target-term').select_option('2027-spring')
    page.locator('#advisor-submit').click()
    expect(page.locator('#advisor-profile-status')).to_contain_text('已保存')
    assert page.evaluate('state.eligibilityProfile.languageScore') is None
    assert page.evaluate('state.eligibilityProfile.academicScore') is None
    expect(page.locator('#advisor-result-content [data-match-group="needs_confirmation"]')).to_be_visible()
    page.evaluate("location.hash='#application-center'")
    expect(page.locator('#application-context-form select[name=semester]')).to_have_value('第二學期')
    page.reload()
    expect(page.locator('#application-center')).to_be_visible()
    expect(page.locator('#application-context-form select[name=semester]')).to_have_value('第二學期')


@pytest.mark.parametrize("width", [390, 1754])
def test_documents_show_current_phase_and_only_selected_print_items(page, live_server, width):
    page.set_viewport_size({"width":width,"height":956})
    page.emulate_media(reduced_motion="reduce")
    verified_login(page, live_server)
    page.evaluate("location.hash='#application-center'")
    expect(page.locator('.application-template-stage[open]')).to_have_count(1)
    expect(page.locator('.application-template-stage[open]')).to_have_attribute('data-document-stage','校內申請')
    expect(page.locator('.application-packet-row')).to_have_count(0)
    expect(page.locator('.packet-empty')).to_contain_text('只放這次要印')
    checkbox = page.locator('.application-template-stage[open] [data-application-packet-template]').first
    template_id = checkbox.get_attribute('data-application-packet-template')
    checkbox.check()
    expect(page.locator('.application-packet-row')).to_have_count(1)
    expect(page.locator('#download-application-packet')).to_be_disabled()
    page.locator('#application-document-stage').select_option('返國後')
    expect(page.locator('.application-template-stage[open]')).to_have_attribute('data-document-stage','返國後')
    assert page.evaluate('state.account.application_stage') == 'exploring'
    expect(page.locator('.application-packet-row')).to_have_count(1)
    # Removing the row also removes the checkbox; inspect the resulting list.
    page.locator(f'#application-packet-list [data-application-packet-template="{template_id}"]').click()
    expect(page.locator('.application-packet-row')).to_have_count(0)
    assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
    capture(page, f'ux-documents-{width}.png')


def test_target_change_can_be_cancelled_and_preserves_old_tasks_and_draft(page, live_server):
    _, target = create_target(page, live_server)
    # Create in-memory fixtures only for this isolated browser/account.
    page.evaluate('''target=>{
      state.calendarEvents.push({id:'isolated-old-task',schoolName:target,title:'保留原校任務',date:'2027-01-01',origin:'personal'});
      state.applicationAnswers['isolated-draft']={purpose:'草稿需要保留'};
    }''',target)
    button = page.locator('#recommended-match-list [data-planning-target]').filter(has_not_text='已設為目標').first
    next_target = button.get_attribute('data-planning-target')
    button.click()
    dialog = page.locator('#planning-target-change-dialog')
    expect(dialog).to_be_visible()
    expect(dialog).to_contain_text('保留 1 項')
    expect(page.locator('#planning-target-change-cancel')).to_be_focused()
    page.locator('#planning-target-change-cancel').click()
    assert page.evaluate('state.applicationContext.target_school') == target
    button.click()
    dialog.locator('button[value=confirm]').click()
    expect(page.locator('#planning-target-summary')).to_contain_text(next_target)
    assert page.evaluate('state.calendarEvents.find(item=>item.id==="isolated-old-task").schoolName') == target
    assert page.evaluate('state.applicationAnswers["isolated-draft"].purpose') == '草稿需要保留'


def test_known_mismatch_has_no_choose_target_action_and_recommendation_is_not_probability(page, live_server):
    def respond(route):
        route.fulfill(json={"school_name":"長庚大學","summary":"隔離推薦資料", "qualification":[], "tasks":[],
            "recommendations":[{"school_name":"限制測試大學","match_score":95,"fit_label":"目前條件不符", "eligibility_status":"does_not_match",
                                "blocking_reasons":["你的學制不在公開範圍"],"confirmation_items":[],"gaps":[],"reasons":[],"source_urls":[]} ]})
    verified_login(page,live_server)
    page.route('**/advisor/plan',respond)
    page.evaluate("location.hash='#advisor'")
    page.locator('#advisor-submit').click()
    expect(page.locator('#advisor-result-content .match-group.is-blocked')).to_be_visible()
    page.locator('#advisor-result-content .match-group.is-blocked > summary').click()
    expect(page.locator('#advisor-result-content [data-planning-target]')).to_have_count(0)
    expect(page.locator('#advisor-result-content')).to_contain_text('調整條件')
    expect(page.locator('#advisor-result-content')).to_contain_text('排序分數')
