"""Two real browser sessions use one complete condition snapshot; drafts stay local."""
from uuid import uuid4
import requests

from playwright.sync_api import expect

from .conftest import login_through_web
from .test_web_next_phase import _wait_for_workspace, _auth_headers


def saved_profile(envelope):
    return ((envelope.get('workspace',{}).get('selection_conditions') or {}).get('profile') or {})


def test_complete_conditions_reach_new_device_and_clear_stays_cleared(page,browser,live_server):
    email=f'conditions-{uuid4().hex[:8]}@example.com'
    session=live_server.register(email)
    live_server.verify_student(session['profile']['id'])
    login_through_web(page,live_server,email)
    page.evaluate("location.hash='#advisor'")
    page.locator('#advisor-college').select_option('工學院')
    page.locator('#advisor-department').select_option('資訊工程學系')
    page.locator('#advisor-degree').select_option('大學部')
    page.locator('#advisor-academic-score').fill('88.5')
    page.locator('#advisor-language-test').select_option('ielts')
    page.locator('#advisor-language-score').fill('7')
    page.locator('#advisor-country').select_option('日本')
    page.locator('#advisor-target-term').select_option('2027-spring')
    page.locator('.advisor-more-fields > summary').click()
    page.locator('#advisor-current-year').select_option('大三')
    page.locator('#advisor-monthly-budget').fill('42000')
    page.locator('#advisor-scholarship').check()
    with page.expect_response(lambda r:r.url.endswith('/advisor/plan') and r.request.method=='POST') as result:
        page.locator('#advisor-submit').click()
    assert result.value.ok
    saved=_wait_for_workspace(live_server,session,lambda item:saved_profile(item).get('academic_score')==88.5)['workspace']
    profile=saved['selection_conditions']['profile']
    assert profile['monthly_budget']==42000 and profile['needs_scholarship'] is True
    context=browser.new_context(viewport={'width':390,'height':956})
    second=context.new_page()
    try:
        login_through_web(second,live_server,email)
        second.evaluate("location.hash='#advisor'")
        for selector,value in [('college','工學院'),('department','資訊工程學系'),('academic-score','88.5'),('language-test','ielts'),('language-score','7'),('current-year','大三'),('monthly-budget','42000'),('country','日本'),('target-term','2027-spring')]:
            expect(second.locator(f'#advisor-{selector}')).to_have_value(value)
        expect(second.locator('#advisor-scholarship')).to_be_checked()
        # A remote update loads the saved snapshot, without overwriting the first device's draft.
        page.locator('#advisor-academic-score').fill('93')
        second.locator('#advisor-academic-score').fill('90')
        second.locator('#advisor-submit').click()
        _wait_for_workspace(live_server,session,lambda item:saved_profile(item).get('academic_score')==90)
        page.evaluate('loadAccountWorkspace()')
        expect(page.locator('#advisor-academic-score')).to_have_value('93')
        page.reload()
        expect(page.locator('#advisor-academic-score')).to_have_value('90')
        second.evaluate("location.hash='#eligibility'")
        second.locator('#clear-saved-eligibility').click()
        _wait_for_workspace(live_server,session,lambda item:item['workspace']['selection_conditions']=={'profile':None})
        page.reload()
        expect(page.locator('#advisor-academic-score')).to_have_value('')
        expect(page.locator('#advisor-language-score')).to_have_value('')
        expect(page.locator('#advisor-profile-status')).to_have_text('尚未設定')
        second.reload()
        expect(second.locator('#advisor-academic-score')).to_have_value('')
    finally:
        context.close()


def test_conflicting_submissions_keep_one_snapshot_and_tell_student(page,browser,live_server):
    email=f'conditions-conflict-{uuid4().hex[:8]}@example.com'
    session=live_server.register(email)
    live_server.verify_student(session['profile']['id'])
    initial={'college':'工學院','department':'資訊工程學系','degree_level':'大學部',
             'academic_score':85,'language_test':'ielts','language_score':7,
             'target_term':'2027-spring','monthly_budget':40000,'needs_scholarship':False,
             'academic_year':'116','application_round':'第一梯次'}
    seeded=requests.put(f'{live_server.base_url}/account/workspace',headers=_auth_headers(session),json={
        'home_school':'長庚大學','application_context':{'school_name':'長庚大學'},
        'selection_conditions':{'profile':initial}},timeout=10)
    assert seeded.ok
    assert saved_profile(requests.get(f'{live_server.base_url}/account/workspace',headers=_auth_headers(session)).json())['academic_score']==85
    login_through_web(page,live_server,email)
    assert saved_profile(requests.get(f'{live_server.base_url}/account/workspace',headers=_auth_headers(session)).json()).get('academic_score')==85
    page.wait_for_load_state('networkidle')
    assert page.evaluate('state.eligibilityProfile?.academicScore')==85, page.evaluate("({home:activeHomeSchool(),loaded:state.accountWorkspaceLoadedSchool,profile:state.eligibilityProfile,draft:document.querySelector('#advisor-form').dataset.draftOwner})")
    page.evaluate("location.hash='#advisor'")
    expect(page.locator('#advisor-academic-score')).to_have_value('85')
    context=browser.new_context(viewport={'width':390,'height':956})
    second=context.new_page()
    held=[]
    hold=[True]
    def hold_first_write(route):
        if route.request.method=='PUT' and hold[0] and not held:
            held.append(route)
        else:
            route.continue_()
    try:
        login_through_web(second,live_server,email)
        second.evaluate("location.hash='#advisor'")
        expect(second.locator('#advisor-language-score')).to_have_value('7')
        page.route('**/account/workspace',hold_first_write)
        page.locator('#advisor-academic-score').fill('93')
        with page.expect_request(lambda request:request.url.endswith('/account/workspace') and request.method=='PUT'):
            page.locator('#advisor-submit').click()
        second.locator('#advisor-language-score').fill('8')
        second.locator('#advisor-submit').click()
        expect(second.locator('#account-workspace-sync-label')).to_have_text('已同步')
        _wait_for_workspace(live_server,session,lambda item:saved_profile(item).get('language_score')==8)
        assert held
        hold[0]=False
        with page.expect_response(lambda response:response.url.endswith('/account/workspace') and response.status==409):
            held.pop().continue_()
        expect(page.locator('#page-status')).to_contain_text('另一裝置也更新了選校條件')
        expect(page.locator('#account-workspace-sync-label')).to_have_text('已同步')
        result=_wait_for_workspace(live_server,session,lambda item:saved_profile(item).get('academic_score')==93)
        # GPA 93 and language 7 were submitted together; never invent GPA 93 + language 8.
        assert saved_profile(result)['language_score']==7
        second.reload()
        expect(second.locator('#advisor-academic-score')).to_have_value('93')
        expect(second.locator('#advisor-language-score')).to_have_value('7')
    finally:
        page.unroute('**/account/workspace',hold_first_write)
        for route in held:
            route.abort()
        context.close()
