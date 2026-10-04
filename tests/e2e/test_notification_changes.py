import os
from pathlib import Path
from uuid import uuid4

import pytest
from playwright.sync_api import expect

from exchange_info.repositories import JsonlAccountRepository
from exchange_info.storage import load_application_workflow_revisions, save_application_workflow_revisions
from test_notifications import _content_account, _published_content_store
from .conftest import login_through_web, open_navigation


@pytest.mark.parametrize('width',[390,1754])
def test_student_change_comparison_retries_and_fits_dialog(page,live_server,request,width):
    page.set_viewport_size({'width':width,'height':956})
    page.emulate_media(reduced_motion='reduce')
    email=f'change-ui-{uuid4().hex[:8]}@example.com'
    account_session=live_server.register(email,'規定變更學生')
    live_server.verify_student(account_session['profile']['id'])
    repository=JsonlAccountRepository(live_server.data_dir)
    account=repository.find_account_by_id(account_session['profile']['id'])
    account.application_workspaces=_content_account().application_workspaces
    account.application_workspaces[0].application_context.application_round='第一梯次'
    repository.save_account(account)
    original=load_application_workflow_revisions(live_server.data_dir)
    request.addfinalizer(lambda:save_application_workflow_revisions(original,live_server.data_dir))
    _published_content_store(live_server.data_dir)
    errors=[]
    page.on('pageerror',lambda error:errors.append(str(error)))
    login_through_web(page,live_server,email)
    open_navigation(page)
    page.locator('#notification-button').click()
    button=page.locator('[data-notification-changes]').first
    expect(button).to_be_visible()
    failures=[1]
    def transient(route):
        if failures[0]:
            failures[0]=0
            route.fulfill(status=503,content_type='application/json',body='{"detail":"暫時無法讀取版本"}')
        else:
            route.continue_()
    page.route('**/account/notifications/*/changes',transient)
    button.click()
    changes=page.locator('.notification-changes').first
    expect(changes).to_contain_text('收合後再展開即可重試')
    button.click()
    expect(changes).to_be_hidden()
    button.click()
    expect(changes).to_contain_text('舊版資格')
    expect(changes).to_contain_text('新版資格與文件')
    expect(changes).to_contain_text('已完成工作及個人排程會保留')
    affected=changes.locator('.notification-affected-tasks')
    expect(affected).to_be_visible()
    expect(affected).to_contain_text('這次變更影響你的 1 項準備工作')
    expect(affected.locator('li').first).to_have_attribute('data-affected-action','review_progress')
    expect(affected).to_contain_text('不會自動修改你的進度、工時或個人期限')
    assert errors==[]
    assert changes.evaluate('(node)=>node.scrollWidth<=node.clientWidth+1')
    assert page.locator('#notification-dialog').evaluate('(node)=>node.scrollWidth<=node.clientWidth+1')
    if os.environ.get('UNIWAY_GLASS_ARTIFACT_DIR'):
        path=Path(os.environ['UNIWAY_GLASS_ARTIFACT_DIR'])/f'notification-changes-{width}.png'
        page.screenshot(path=str(path),animations='disabled')
    page.get_by_role('link',name='查看這所學校',exact=True).click()
    expect(page.locator('#school-detail-title')).to_have_text('林肯大學 Lincoln University')
    assert errors==[]


def test_unverified_account_syncs_its_workspace_like_any_other(page,live_server):
    # An account no longer needs a verified school to load or sync its own plan and progress.
    email=f'unverified-sync-{uuid4().hex[:8]}@example.com'
    live_server.register(email,'尚未驗證學生')
    login_through_web(page,live_server,email)
    expect(page.locator('#account-workspace-sync-label')).to_have_text('已同步',timeout=15000)
    expect(page.locator('#account-workspace-sync-status')).to_have_attribute('aria-busy','false')
