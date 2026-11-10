"""A real saved exchange plan, from a notice to preparation, living and peer exchange."""
import re

import pytest
from playwright.sync_api import expect

from .conftest import enter_public_site
from .test_application_workbench import make_plan
from .test_glass_theme import verified_login, capture


@pytest.fixture(autouse=True)
def no_uncaught_javascript_errors(page):
    errors=[]
    page.on('pageerror', lambda error: errors.append(str(error)))
    yield
    assert not errors


def start(page, live_server, **changes):
    page.emulate_media(reduced_motion="reduce")
    verified_login(page, live_server)
    plan=make_plan(page, live_server, **changes)
    enter_public_site(page, live_server, f'my-application?plan={plan["plan"]["id"]}&view=workspace')
    expect(page.get_by_role('heading', name='準備工作台', exact=True)).to_be_visible()
    return plan


def editor(page, title):
    page.locator('[data-ex-new]').click()
    form=page.locator('#exchange-task-form')
    form.locator('[name=title]').fill(title)
    return form


def saved(page, form):
    form.get_by_role('button', name='保存任務', exact=True).click()
    expect(page.locator('#exchange-task-dialog')).not_to_be_visible(timeout=20_000)
    expect(page.locator('#exchange-message')).to_contain_text('已保存')


def test_notice_review_batches_today_schedule_and_reload(page, live_server):
    plan=start(page,live_server)
    page.locator('[data-ex-tab=notice]').click()
    form=page.locator('#exchange-notice-form')
    form.locator('[name=source_label]').fill('合作校入學通知')
    form.locator('[name=text]').fill('第一批：2027/1/10 前請回傳家長簽名同意書。\n第二批：2027/2/10 前請上傳體檢報告。')
    form.get_by_role('button',name='整理待辦草稿').click()
    rows=page.locator('[data-ex-preview]')
    expect(rows).to_have_count(2)
    rows.nth(0).locator('[name=title]').fill('回傳本人與家長簽名同意書')
    rows.nth(0).locator('[name=recipient]').fill('母校國際處')
    rows.nth(0).locator('[name=signers]').fill('本人、家長')
    expect(rows.nth(0).locator('[name=due_date]')).to_have_value('2027-01-10')
    expect(rows.nth(1).locator('[name=due_date]')).to_have_value('2027-02-10')
    page.locator('#exchange-review-form [name=reviewed]').check()
    page.get_by_role('button',name='加入選取的待辦').click()
    expect(page.locator('.ex-task')).to_have_count(2)
    expect(page.locator('.ex-task').first).to_contain_text('母校國際處')
    expect(page.locator('.ex-task').first).to_contain_text('通知期限・本人核對 2027-01-10')
    page.locator('.hub-tabs [data-tab=today]').click()
    expect(page.locator('.ex-summary:visible')).to_contain_text('回傳本人與家長簽名同意書')
    page.locator('.hub-tabs [data-tab=schedule]').click()
    expect(page.locator('.ex-summary:visible')).to_contain_text('2027-02-10')
    expect(page.locator('#schedule-view [data-tracker-row]',has_text='回傳本人與家長簽名同意書')).to_be_visible()
    page.evaluate("state.calendarMonth=new Date(2027,0,1); state.calendarSelectedDate='2027-01-10'; state.calendarAgendaMode='selected'; renderApplicationCalendar()")
    expect(page.locator('#calendar-agenda-list')).to_contain_text('通知期限・本人核對')
    expect(page.locator('#calendar-agenda-list [data-delete-calendar-event]')).to_have_count(0)
    expect(page.locator('#calendar-agenda-list')).not_to_contain_text('官方日期')
    page.reload()
    expect(page.locator('.ex-summary:visible')).to_contain_text('2027-02-10',timeout=30_000)
    page.locator('.hub-tabs [data-tab=workspace]').click()
    capture(page,'workspace-notice-desktop.png')


@pytest.mark.parametrize('theme',['light','dark'])
def test_phone_personal_goal_waiting_notes_and_no_overflow(page,live_server,theme):
    page.set_viewport_size({'width':390,'height':844})
    page.add_init_script(f"localStorage.setItem('exchange-guide-theme','{theme}')")
    start(page,live_server)
    form=editor(page,'確認宿舍收件與用品')
    form.locator('[name=kind]').select_option('life')
    form.locator('[name=date_kind]').select_option('personal')
    form.locator('[name=due_date]').fill('2027-01-15')
    form.locator('[name=status]').select_option('waiting')
    form.locator('[name=waiting_for]').fill('宿舍管理員確認代收規則')
    form.locator('[name=notes]').fill('先整理用品清單，收到回覆後再決定寄送方式。')
    assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
    saved(page,form)
    expect(page.locator('.ex-task')).to_contain_text('個人目標 2027-01-15')
    expect(page.locator('.ex-task')).to_contain_text('等待：宿舍管理員')
    page.locator('.hub-tabs [data-tab=today]').click()
    expect(page.locator('.ex-summary:visible')).to_contain_text('正在等待 1 項')
    page.locator('.hub-tabs [data-tab=workspace]').click()
    assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
    for field in ['#exchange-stage','#exchange-kind','#exchange-status']:
        assert page.locator(field).locator('..').get_by_role('combobox').bounding_box()['width'] >= 120
    for selector in ['[data-ex-new]','.hub-tabs>a.active']:
        foreground,background=page.locator(selector).evaluate('(el)=>[getComputedStyle(el).color,getComputedStyle(el).backgroundColor]')
        def luminance(color):
            rgb=[int(v)/255 for v in re.findall(r'\d+',color)[:3]]
            return sum(weight*(v/12.92 if v<=0.04045 else ((v+0.055)/1.055)**2.4) for weight,v in zip([.2126,.7152,.0722],rgb))
        light,dark=sorted([luminance(foreground),luminance(background)],reverse=True)
        assert (light+.05)/(dark+.05) >= 4.5
    capture(page,f'workspace-mobile-{theme}.png')


def test_courses_conflicts_and_downloaded_dates(page,live_server):
    start(page,live_server)
    for title,start_time,end_time in [('課程甲','09:00','11:00'),('課程乙','10:00','12:00')]:
        form=editor(page,title)
        form.locator('[name=kind]').select_option('course')
        form.locator('[name=stage]').select_option('abroad')
        form.locator('[name=credits]').fill('3')
        form.locator('[name=weekday]').select_option('1')
        form.locator('[name=start]').fill(start_time)
        form.locator('[name=end]').fill(end_time)
        form.locator('[name=date_kind]').select_option('personal')
        form.locator('[name=due_date]').fill('2027-01-15')
        saved(page,form)
    page.locator('#exchange-kind').select_option('course')
    expect(page.locator('.ex-course')).to_contain_text('已記錄 6 學分')
    expect(page.locator('.ex-course')).to_contain_text('時間衝突：課程甲／課程乙')
    with page.expect_download() as download:
        page.locator('[data-ex-export=calendar]').click()
    text=download.value.path().read_text()
    assert 'DTSTART;VALUE=DATE:20270115' in text and '[個人目標]' in text
    capture(page,'workspace-courses.png')


def test_destination_pack_interview_answers_and_idempotent_import(page,live_server):
    start(page,live_server,target_school='明治大學 Meiji University')
    page.locator('.ex-tabs [data-ex-tab=library]').click()
    packs=page.locator('.ex-pack')
    expect(packs.filter(has_text='日本行前提醒')).to_be_visible(timeout=20_000)
    interview=packs.filter(has=page.locator('[data-ex-select-pack=interview]'))
    interview.locator('summary').click()
    interview.locator('[data-ex-select-pack=interview]').click()
    page.get_by_role('button',name='加入選取項目',exact=True).click()
    expect(page.locator('.ex-task')).to_have_count(5)
    page.locator('.ex-task',has_text='為什麼選擇這所學校？').get_by_role('button',name='寫下回答',exact=True).click()
    form=page.locator('#exchange-task-form')
    expect(form.locator('[name=notes]')).to_have_value(re.compile('明治大學'))
    form.locator('[name=notes]').fill('我已查核課程官方來源，希望修讀與研究方向相關的課程。')
    saved(page,form)
    page.locator('#exchange-kind').select_option('interview')
    page.locator('[data-ex-pack=interview]').click()
    expect(page.locator('#exchange-message')).to_contain_text('沒有新的項目')
    with page.expect_download() as download:
        page.locator('[data-ex-export=text]').click()
    assert '我已查核課程官方來源' in download.value.path().read_text()


def test_failed_save_keeps_the_draft_and_retry_persists_it(page,live_server):
    start(page,live_server)
    form=editor(page,'保留失敗時的面試草稿')
    form.locator('[name=notes]').fill('這段內容在保存失敗後仍需保留。')
    pattern='**/account/application-paths/*/workspace?*'
    page.route(pattern,lambda route: route.fulfill(status=503,content_type='application/json',body='{"detail":"暫時無法保存"}'))
    form.get_by_role('button',name='保存任務').click()
    expect(page.locator('#exchange-edit-error')).to_contain_text('暫時無法保存')
    expect(form.locator('[name=notes]')).to_have_value('這段內容在保存失敗後仍需保留。')
    page.unroute(pattern)
    saved(page,form)
    page.reload()
    expect(page.locator('.ex-task')).to_contain_text('保留失敗時的面試草稿',timeout=30_000)


def test_notice_attachment_and_edited_preview_survive_tab_navigation(page,live_server):
    start(page,live_server)
    page.locator('[data-ex-tab=notice]').click()
    page.locator('#exchange-notice-form summary').click()
    page.locator('#exchange-notice-file').set_input_files({'name':'notice.txt','mimeType':'text/plain','buffer':'第一批 2027/1/10\n請回傳家長簽名同意書'.encode()})
    page.locator('#exchange-extract-consent').check()
    page.get_by_role('button',name='讀取附件文字').click()
    expect(page.locator('#exchange-notice-form [name=text]')).to_have_value(re.compile('家長簽名'))
    page.get_by_role('button',name='整理待辦草稿').click()
    row=page.locator('[data-ex-preview]')
    expect(row).to_have_count(1)
    row.locator('[name=recipient]').fill('母校承辦老師')
    row.locator('[name=due_date]').fill('2027-01-09')
    page.locator('.ex-tabs [data-ex-tab=tasks]').click()
    saved(page,editor(page,'先保存另一項準備'))
    page.locator('.ex-tabs [data-ex-tab=notice]').click()
    expect(row.locator('[name=recipient]')).to_have_value('母校承辦老師')
    expect(row.locator('[name=due_date]')).to_have_value('2027-01-09')
    capture(page,'workspace-notice-review.png')
    page.locator('#exchange-review-form [name=reviewed]').check()
    page.get_by_role('button',name='加入選取的待辦').click()
    expect(page.locator('.ex-task')).to_have_count(2)


def test_task_draft_is_scoped_to_its_plan(page,live_server):
    original=start(page,live_server)
    other=make_plan(page,live_server,semester='spring',revision=original['revision'])
    page.reload()
    expect(page.locator('#plan-select option')).to_have_count(2,timeout=30_000)
    form=editor(page,'只屬於上學期的草稿')
    form.locator('[name=notes]').fill('不應出現在另一個計畫。')
    form.get_by_role('button',name='關閉任務').click()
    page.locator('#plan-select').select_option(other['plan']['id'])
    expect(page.locator('#today-view')).to_be_visible()
    page.locator('.hub-tabs [data-tab=workspace]').click()
    expect(page.locator('#exchange-task-dialog')).not_to_be_visible()
    expect(page.locator('.ex-task')).to_have_count(0)
    page.locator('#plan-select').select_option(original['plan']['id'])
    expect(page.locator('#today-view')).to_be_visible()
    page.locator('.hub-tabs [data-tab=workspace]').click()
    expect(page.locator('#exchange-task-form [name=notes]')).to_have_value('不應出現在另一個計畫。')
    saved(page,page.locator('#exchange-task-form'))


def test_submission_requires_all_selected_prerequisites(page,live_server):
    start(page,live_server)
    for title in ['收到提名通知','收到接收校申請說明']:
        saved(page,editor(page,title))
    form=editor(page,'向接收校正式送件')
    form.locator('details summary',has_text='分批文件').click()
    form.locator('[name=action]').select_option('submit')
    form.locator('[name=depends_on]').select_option(label=['收到提名通知','收到接收校申請說明'])
    form.locator('[name=status]').select_option('done')
    form.get_by_role('button',name='保存任務').click()
    expect(page.locator('#exchange-edit-error')).to_contain_text('前置任務尚未完成')
    form.locator('[name=status]').select_option('doing')
    saved(page,form)
    expect(page.locator('.ex-task',has_text='向接收校正式送件')).to_contain_text('等待中')
    for title in ['收到提名通知','收到接收校申請說明']:
        page.get_by_role('button',name=title,exact=True).click()
        form=page.locator('#exchange-task-form')
        form.locator('[name=status]').select_option('done')
        saved(page,form)
    page.get_by_role('button',name='向接收校正式送件',exact=True).click()
    form=page.locator('#exchange-task-form')
    form.locator('[name=status]').select_option('done')
    saved(page,form)
    expect(page.locator('.ex-task',has_text='向接收校正式送件')).to_contain_text('已完成')


def test_peer_invitation_uses_existing_forum_and_is_filtered_by_semester(page,live_server):
    plan=start(page,live_server)
    page.locator('[data-ex-tab=peers]').click()
    expect(page.locator('#exchange-peers-list')).to_contain_text('目前沒有',timeout=20_000)
    form=page.locator('#exchange-peer-form')
    form.locator('[name=body]').fill('想一起確認宿舍報到與交通，歡迎同梯在這裡交流。')
    form.locator('[name=consent]').check()
    form.get_by_role('button',name='發布同梯邀請').click()
    expect(page.locator('#exchange-peers-list')).to_contain_text('想一起確認宿舍報到與交通',timeout=20_000)
    link=page.locator('#exchange-peers-list a')
    expect(link).to_have_attribute('href',re.compile(r'discussion=.+#public-board'))
    current=page.request.get(f'{live_server.base_url}/account/application-paths',params={'home_school':'長庚大學'}).json()
    other=make_plan(page,live_server,semester='spring',revision=current['revision'])
    enter_public_site(page,live_server,f'my-application?plan={other["plan"]["id"]}&view=workspace')
    page.locator('[data-ex-tab=peers]').click()
    expect(page.locator('#exchange-peers-list')).to_contain_text('目前沒有',timeout=20_000)
