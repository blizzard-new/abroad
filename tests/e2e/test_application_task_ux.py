"""Regression coverage for audited data-loss, mobile next-action and click flows."""
from urllib.parse import urlencode
from uuid import uuid4
from datetime import datetime, timedelta, timezone
import copy

from playwright.sync_api import expect

from .test_glass_theme import verified_login


def plan(page, live_server):
    session = verified_login(page, live_server)
    response = page.request.post(f'{live_server.base_url}/account/application-paths', data={
        'home_school': '長庚大學', 'target_school': '林肯大學 Lincoln University',
        'academic_year': '116', 'departure_year': '2027', 'semester': 'fall', 'revision': 0,
    })
    assert response.ok, response.text()
    result = response.json()
    url = f'{live_server.base_url}/#my-application?' + urlencode({'plan': result['plan']['id'], 'view': 'progress'})
    page.goto(url)
    expect(page.locator('#progress-view')).to_be_visible()
    return session, result, url


def open_writing(page, url):
    page.evaluate('(hash) => location.hash = hash', url.split('#')[1].replace('view=progress', 'view=level') + '&level=motivation')
    expect(page.locator('#level-input')).to_be_visible()


def test_unsynced_history_back_forward_and_save_failure_preserve_text(page, live_server):
    _, _, url = plan(page, live_server)
    open_writing(page, url)
    page.route('**/account/application-paths/*/steps/*', lambda route: route.fulfill(status=503, json={'detail': '測試暫時離線'}))
    page.locator('#level-input').fill('不能在返回時消失的測試草稿')
    page.go_back()
    expect(page.locator('#progress-view')).to_be_visible()
    page.go_forward()
    expect(page.locator('#level-input')).to_have_value('不能在返回時消失的測試草稿')
    page.locator('#save-draft').click()
    expect(page.locator('#level-error')).to_contain_text('仍保留在此分頁')
    expect(page.locator('#level-input')).to_have_value('不能在返回時消失的測試草稿')
    page.unroute('**/account/application-paths/*/steps/*')
    page.locator('#save-draft').click()
    expect(page.locator('#save-note')).to_have_text('已儲存')
    page.reload()
    expect(page.locator('#level-input')).to_have_value('不能在返回時消失的測試草稿')


def test_completion_focus_and_unchanged_save_do_not_reset_progress(page, live_server):
    _, _, url = plan(page, live_server)
    open_writing(page, url)
    page.locator('#level-input').fill('完整的測試申請動機')
    page.get_by_role('button', name='標記準備完成', exact=True).click()
    expect(page.locator('.success-state')).to_be_focused()
    expect(page.locator('.success-state h3')).to_have_text('已完成這項準備')
    page.locator('#edit-level').click()
    expect(page.locator('#save-note')).to_contain_text('已完成')
    page.locator('#save-draft').click()
    expect(page.locator('#save-note')).to_have_text('已儲存')
    page.reload()
    expect(page.locator('.level-progress')).to_contain_text('已完成')


def test_expired_session_returns_only_same_accounts_unsynced_draft(page, live_server):
    session, _, url = plan(page, live_server)
    open_writing(page, url)
    page.route('**/account/application-paths/*/steps/*', lambda route: route.fulfill(status=401, json={'detail': 'expired'}))
    page.locator('#level-input').fill('只屬於原帳號的未保存草稿')
    page.locator('#save-draft').click()
    expect(page.locator('#auth-dialog')).to_be_visible()
    expect(page.locator('#level-input')).to_have_count(0)
    page.unroute('**/account/application-paths/*/steps/*')
    page.locator('#login-form input[name=email]').fill(session['profile']['email'])
    page.locator('#login-form input[name=password]').fill('CodexE2E!2026')
    page.locator('#login-form button[type=submit]').click()
    expect(page.locator('#auth-dialog')).to_be_hidden()
    expect(page.locator('#level-input')).to_have_value('只屬於原帳號的未保存草稿')
    # Explicit logout must clear in-memory recovery as well as rendered data.
    page.evaluate('logoutAccount()')
    expect(page.locator('#level-input')).to_have_count(0)
    page.evaluate('openAuthDialog("login")')
    page.locator('#login-form input[name=email]').fill(session['profile']['email'])
    page.locator('#login-form input[name=password]').fill('CodexE2E!2026')
    page.locator('#login-form button[type=submit]').click()
    expect(page.locator('#auth-dialog')).to_be_hidden()
    expect(page.locator('#level-input')).to_have_value('')


def test_phone_and_tablet_keep_action_deadline_and_large_text(page, live_server):
    _, _, url = plan(page, live_server)
    for width in [390, 834, 1440]:
        page.set_viewport_size({'width': width, 'height': 844})
        expect(page.locator('#next-link')).to_be_visible()
        expect(page.locator('#deadline-card')).to_be_visible()
        assert page.locator('#next-link').bounding_box()['height'] >= 44
        assert page.locator('#next-link').bounding_box()['y'] < 800
        assert float(page.locator('#next-prompt').evaluate('e=>getComputedStyle(e).fontSize').replace('px', '')) >= 16
        assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
    page.emulate_media(reduced_motion='reduce')
    expect(page.locator('#next-link')).to_have_css('animation-name', 'none')
    page.locator('#next-link').click()
    expect(page.locator('#level-form')).to_be_visible()
    assert 'view=level' in page.url
    for width in [390, 834, 1440]:
        page.set_viewport_size({'width': width, 'height': 844})
        expect(page.locator('#save-note')).to_be_visible()
        assert float(page.locator('#level-form button[type=submit]').evaluate('e=>getComputedStyle(e).fontSize').replace('px', '')) >= 18


def test_existing_plan_visible_in_scheduling_without_creating_duplicate_preference(page, live_server):
    _, result, url = plan(page, live_server)
    page.evaluate('location.hash="#overview"')
    expect(page.locator('#application-plan-index')).to_contain_text('林肯大學')
    expect(page.locator('#tracker-body')).not_to_contain_text('還沒有志願')
    page.locator('#application-plan-index a').first.click()
    expect(page.locator('#progress-view')).to_be_visible()
    assert result['plan']['id'] in page.url


def test_edit_during_save_is_not_overwritten_by_older_ack(page, live_server):
    _, _, url = plan(page, live_server)
    open_writing(page, url)
    first = True
    def mutate_during_request(route):
        nonlocal first
        if first:
            first = False
            response = route.fetch()
            page.locator('#level-input').fill('較新的內容必須留下')
            route.fulfill(response=response)
        else:
            route.continue_()
    page.route('**/account/application-paths/*/steps/*', mutate_during_request)
    page.locator('#level-input').fill('第一版內容')
    page.locator('#save-draft').click()
    expect(page.locator('#level-input')).to_have_value('較新的內容必須留下')
    expect(page.locator('#save-note')).to_have_text('已儲存', timeout=15000)
    page.reload()
    expect(page.locator('#level-input')).to_have_value('較新的內容必須留下')


def test_conflicting_tab_requires_comparison_before_local_draft_overwrites(page, live_server):
    _, created, url = plan(page, live_server)
    open_writing(page, url)
    api = f"{live_server.base_url}/account/application-paths/{created['plan']['id']}"
    saved = page.request.put(api + '/steps/motivation?home_school=長庚大學', data={
        'revision': created['revision'], 'step': {'value': '其他分頁先保存的版本'},
    })
    assert saved.ok, saved.text()
    page.locator('#level-input').fill('此分頁的獨立版本')
    page.locator('#save-draft').click()
    expect(page.locator('#conflict-reload')).to_be_visible()
    expect(page.locator('#level-input')).to_have_value('此分頁的獨立版本')
    page.locator('#conflict-reload').click()
    expect(page.locator('.conflict-comparison')).to_contain_text('其他分頁先保存的版本')
    page.locator('#level-input').fill('比對後選擇這個版本')
    # Editing must not silently overwrite a conflicting server version.
    page.evaluate('dispatchEvent(new Event("online"))')
    page.wait_for_timeout(1200)
    remote = page.request.get(api + '?home_school=長庚大學').json()
    assert remote['plan']['steps']['motivation']['value'] == '其他分頁先保存的版本'
    page.locator('#save-draft').click()
    expect(page.locator('#save-note')).to_have_text('已儲存')
    page.reload()
    expect(page.locator('#level-input')).to_have_value('比對後選擇這個版本')


def test_expired_draft_never_crosses_account_boundary(page, live_server):
    original, _, url = plan(page, live_server)
    open_writing(page, url)
    other = live_server.register(f'other-ux-{uuid4().hex[:8]}@example.com')
    page.route('**/account/application-paths/*/steps/*', lambda route: route.fulfill(status=401, json={'detail': 'expired'}))
    page.locator('#level-input').fill('原帳號私人內容')
    page.locator('#save-draft').click()
    expect(page.locator('#auth-dialog')).to_be_visible()
    page.unroute('**/account/application-paths/*/steps/*')
    for session in [other, original]:
        page.locator('#login-form input[name=email]').fill(session['profile']['email'])
        page.locator('#login-form input[name=password]').fill('CodexE2E!2026')
        page.locator('#login-form button[type=submit]').click()
        expect(page.locator('#auth-dialog')).to_be_hidden()
        if session == other:
            expect(page.locator('[data-path-new]')).to_be_visible()
            expect(page.locator('#application-path')).not_to_contain_text('原帳號私人內容')
            page.evaluate('logoutAccount()')
            page.evaluate('openAuthDialog("login")')
        else:
            expect(page.locator('#level-input')).to_have_value('')


def test_school_detail_starts_plan_directly_and_repeat_creation_is_idempotent(page, live_server):
    verified_login(page, live_server)
    page.evaluate('location.hash="#my-application"')
    expect(page.get_by_role('link', name='找適合的學校', exact=True)).to_be_visible()
    page.get_by_role('link', name='找適合的學校', exact=True).click()
    page.locator('[data-partner-view="list"]').click()
    page.locator('#partner-search').fill('Lincoln')
    page.locator('#partner-table .school-detail-trigger:visible').first.click()
    expect(page.locator('#detail-prepare-plan-button')).to_be_visible()
    page.locator('#detail-prepare-plan-button').click()
    expect(page.locator('#plan-dialog')).to_be_visible()
    expect(page.locator('#create-target')).to_have_value('林肯大學 Lincoln University')
    page.locator('#create-year').fill('116')
    page.locator('#create-departure').fill('2027')
    page.locator('#create-term').select_option('fall')
    page.get_by_role('button', name='建立計畫', exact=True).dblclick()
    expect(page.locator('#today-view')).to_be_visible()  # a new plan lands on 今天
    first_plan = page.locator('#plan-select').input_value()
    page.evaluate('UniWayApplicationPath.startTarget("林肯大學 Lincoln University")')
    expect(page.locator('#plan-dialog')).to_be_hidden()
    expect(page.locator('#plan-select')).to_have_value(first_plan)
    saved = page.request.get(f'{live_server.base_url}/account/application-paths?home_school=長庚大學').json()
    assert len(saved['items']) == 1


def test_unsynced_drafts_remain_separate_when_switching_terms(page, live_server):
    _, first, url = plan(page, live_server)
    created = page.request.post(f'{live_server.base_url}/account/application-paths', data={
        **first['plan']['context'], 'semester': 'spring', 'revision': first['revision'],
    })
    assert created.ok, created.text()
    other_url = url.replace(first['plan']['id'], created.json()['plan']['id'])
    page.route('**/account/application-paths/*/steps/*', lambda route: route.fulfill(status=503, json={'detail': '隔離測試：暫時離線'}))
    open_writing(page, url)
    page.locator('#level-input').fill('上學期的獨立草稿')
    open_writing(page, other_url)
    expect(page.locator('#level-input')).to_have_value('')
    page.locator('#level-input').fill('下學期的獨立草稿')
    open_writing(page, url)
    expect(page.locator('#level-input')).to_have_value('上學期的獨立草稿')
    open_writing(page, other_url)
    expect(page.locator('#level-input')).to_have_value('下學期的獨立草稿')


def test_oauth_reauthentication_preserves_original_tab_and_checks_server_session(page, live_server):
    # Mock the provider window only; the original tab verifies a real test session.
    page.route('**/auth/providers', lambda route: route.fulfill(json=[
        {'provider': 'email', 'enabled': True}, {'provider': 'google', 'enabled': True},
    ]))
    session, _, url = plan(page, live_server)
    open_writing(page, url)
    response = page.request.post(f'{live_server.base_url}/auth/logout')
    assert response.ok
    page.locator('#level-input').fill('Google 重新登入後應恢復的內容')
    page.locator('#save-draft').click()
    expect(page.locator('#auth-dialog')).to_be_visible()
    page.locator('#terms-consent').check()
    original_url = page.url
    page.context.route('**/auth/oauth/google/start?*', lambda route: route.fulfill(content_type='text/html; charset=utf-8', body='<h1>隔離登入測試</h1>'))
    with page.expect_popup() as opened:
        page.locator('[data-oauth-provider=google]').click()
    popup = opened.value
    expect(popup.get_by_role('heading')).to_have_text('隔離登入測試')
    assert popup.evaluate('opener === null')
    assert page.url == original_url
    # An opened popup alone cannot authenticate or expose drafts.
    expect(page.locator('#level-input')).to_have_count(0)
    login = page.request.post(f'{live_server.base_url}/auth/login', data={
        'email': session['profile']['email'], 'password': 'CodexE2E!2026',
    })
    assert login.ok, login.text()
    expect(page.locator('#auth-dialog')).to_be_hidden(timeout=15000)
    expect(page.locator('#level-input')).to_have_value('Google 重新登入後應恢復的內容')


def test_blocked_oauth_popup_keeps_draft_in_original_tab(page, live_server):
    page.route('**/auth/providers', lambda route: route.fulfill(json=[
        {'provider': 'email', 'enabled': True}, {'provider': 'google', 'enabled': True},
    ]))
    _, _, url = plan(page, live_server)
    open_writing(page, url)
    page.route('**/account/application-paths/*/steps/*', lambda route: route.fulfill(status=401, json={'detail': 'expired'}))
    page.locator('#level-input').fill('被擋視窗時保留的草稿')
    page.locator('#save-draft').click()
    expect(page.locator('#auth-dialog')).to_be_visible()
    original_url = page.url
    page.evaluate('window.open=()=>null')
    page.locator('#terms-consent').check()
    page.locator('[data-oauth-provider=google]').click()
    expect(page.locator('#path-reauth-status')).to_contain_text('允許開啟登入視窗')
    assert page.url == original_url
    assert page.evaluate('UniWayApplicationPath.hasRecoverableDrafts()')


def test_next_action_prioritizes_confirmed_deadlines_then_saved_drafts(page, live_server):
    _, created, url = plan(page, live_server)
    data = copy.deepcopy(created)
    all_levels = [level for stage in data['stages'] for level in stage['levels']]
    writing = next(level for level in all_levels if level['id'] == 'motivation')
    writing['progress']['value'] = 1
    data['plan']['steps']['motivation'] = {'value': '續接草稿', 'updated_at': datetime.now(timezone.utc).isoformat()}
    deadline = next(level for level in reversed(all_levels) if level['kind'] == 'confirm' and level['id'] not in ['home', 'term', 'target'])
    deadline['official_deadline_at'] = (datetime.now(timezone.utc) + timedelta(days=2)).isoformat()
    deadline['deadline_confirmed'] = False
    pattern = f"**/account/application-paths/{created['plan']['id']}?*"
    page.route(pattern, lambda route: route.fulfill(json=data))
    page.reload()
    expect(page.locator('#next-title')).to_have_text(writing['title'])
    expect(page.locator('#next-prompt')).to_have_text('接著完成上次的草稿。')
    deadline['deadline_confirmed'] = True
    page.reload()
    expect(page.locator('#next-title')).to_have_text(deadline['title'])
    expect(page.locator('#next-prompt')).to_have_text('官方期限將近，先處理這項。')
    page.locator('#next-link').click()
    expect(page.locator('#level-title')).to_have_text(deadline['title'])
