"""NCU acceptance uses real matching, account persistence and public bundled data."""
from pathlib import Path

import pytest
import requests
from playwright.sync_api import expect

from .conftest import enter_public_site, open_navigation
from .test_open_catalog import sign_in_cookie, attach_session, wait_until

NCU = '國立中央大學'


@pytest.mark.parametrize('width', [390, 1440])
def test_ncu_matching_favorites_documents_plan_reload_and_home_switch(page, live_server, width):
    session = sign_in_cookie(live_server, school=NCU)
    live_server.verify_student(session['profile']['id'], university=NCU)
    attach_session(page, live_server, session)
    page.set_viewport_size({'width': width, 'height': 956})
    page.emulate_media(reduced_motion='reduce')
    errors = []; page.on('pageerror', lambda error: errors.append(str(error)))
    enter_public_site(page, live_server, 'advisor')
    expect(page.locator('#boot-splash')).to_be_hidden(timeout=60_000)
    wait_until(page, "state.dashboard?.school_name === '國立中央大學' && state.accountWorkspaceLoadingCount === 0", timeout=60)
    expect(page.locator('#advisor-academic-rule')).to_contain_text('60分')
    college = page.locator('#advisor-college option').evaluate_all('rows=>rows.find(row=>row.value).value')
    page.locator('#advisor-college').select_option(college)
    if page.locator('#advisor-department').is_visible():
        department = page.locator('#advisor-department option').evaluate_all('rows=>rows.find(row=>row.value).value')
        page.locator('#advisor-department').select_option(department)
    else:
        department = '學籍所屬系所待校方確認'
        page.locator('#advisor-department-text').fill(department)
    page.locator('#advisor-degree').select_option('大學部')
    page.locator('#advisor-academic-score').fill('85')
    page.locator('.advisor-more-fields > summary').click()
    page.locator('#advisor-current-year').select_option('大三')
    page.locator('#advisor-language-test').select_option('ielts')
    page.locator('#advisor-language-score').fill('7')
    page.locator('#advisor-country').select_option('日本')
    with page.expect_response(lambda r: r.url.endswith('/advisor/plan') and r.request.method == 'POST', timeout=60_000) as matched:
        page.locator('#advisor-submit').click()
    assert matched.value.ok
    result = matched.value.json()
    assert result['recommendations']
    expect(page.locator('#advisor-result-content')).to_contain_text('待確認')
    target = page.locator('#advisor-result-content [data-planning-target]').first.get_attribute('data-planning-target')
    assert target and any(r['school_name'] == target for r in result['recommendations'])
    page.locator('#advisor-result-content [data-planning-target]').first.click()
    expect(page.locator('#overview')).to_be_visible()
    expect(page.locator('#planning-target-summary')).to_contain_text(target)
    expect(page.locator('.planning-profile-summary')).to_contain_text('IELTS 7')
    wait_until(page, "document.querySelector('#account-workspace-sync-label').textContent === '已同步'", timeout=60)
    out = Path('/tmp/ncu-audit/browser'); out.mkdir(parents=True, exist_ok=True)
    page.locator('#planning-target-summary').evaluate('el=>el.scrollIntoView({block:"start"})')
    page.evaluate('scrollBy(0,-100)')
    page.screenshot(path=str(out / f'ncu-acceptance-matching-plan-{width}.png'))

    page.evaluate("location.hash='#partners'")
    page.locator('[data-partner-view="list"]').click()
    favorites = []
    for keyword in ['大阪公立', '廣島']:
        page.locator('#partner-search').fill(keyword)
        if width < 700:
            page.locator('#partner-table .partner-card > summary').first.click()
        button = page.locator('#partner-table .favorite-toggle:visible').first
        favorites.append(button.get_attribute('data-school-name'))
        button.click(); expect(button).to_have_attribute('aria-pressed', 'true')
    page.evaluate("location.hash='#favorites'")
    for school in favorites:
        expect(page.locator('#selection-workspace')).to_contain_text(school)
        page.locator(f'#selection-workspace [data-compare-school="{school}"]').check()
        expect(page.locator('#discovery-comparison')).to_contain_text(school)
    page.locator('#discovery-comparison').evaluate('el=>el.scrollIntoView({block:"start"})')
    page.evaluate('scrollBy(0,-100)')
    if width >= 1000:
        ranking = page.locator('.discovery-ranking').bounding_box()
        comparison = page.locator('#discovery-comparison').bounding_box()
        assert ranking['y'] + ranking['height'] <= comparison['y']
    page.screenshot(path=str(out / f'ncu-acceptance-comparison-{width}.png'))
    wait_until(page, "document.querySelector('#account-workspace-sync-label').textContent === '已同步'", timeout=60)

    page.evaluate("location.hash='#application-center'")
    expect(page.locator('#application-target-school')).to_have_value(target)
    expect(page.locator('#application-requirement-list')).to_contain_text('家長同意書')
    expect(page.locator('#application-requirement-list')).to_contain_text('國際移動力')
    expect(page.locator('#application-template-list [data-open-application-template]')).to_have_count(6)
    assert page.locator('#application-requirement-list').get_by_text('下載校方正式表格', exact=True).count() == 0
    sources = page.locator('#application-requirement-list .application-requirement-source a').evaluate_all('rows=>rows.map(row=>row.href)')
    assert any('oia.ncu.edu.tw' in url for url in sources)
    assert all('cgu.edu.tw' not in url for url in sources)
    page.locator('[data-open-application-template="exchange-application-data"]').first.click()
    expect(page.locator('#application-document-form')).to_be_visible()
    expect(page.locator('#application-document-fields')).to_contain_text('實際考試日期')
    page.locator('#application-document-fields').get_by_text('實際考試日期', exact=False).first.scroll_into_view_if_needed()
    page.screenshot(path=str(out / f'ncu-acceptance-document-tool-{width}.png'))
    page.evaluate("location.hash='#application-center'")
    expect(page.locator('#application-requirement-list')).to_be_visible()

    saved = requests.get(f'{live_server.base_url}/account/workspace', params={'home_school': NCU},
        headers={'Authorization': f"Bearer {session['access_token']}"}, timeout=15)
    assert saved.ok
    workspace = saved.json()['workspace']
    assert workspace['application_context']['target_school'] == target
    assert set(favorites) <= set(workspace['favorite_schools'])
    page.reload(); expect(page.locator('#boot-splash')).to_be_hidden(timeout=60_000)
    expect(page.locator('#application-target-school')).to_have_value(target)
    page.evaluate("location.hash='#advisor'")
    expect(page.locator('#advisor-academic-score')).to_have_value('85')
    expect(page.locator('#advisor-department' if page.locator('#advisor-department').is_visible() else '#advisor-department-text')).to_have_value(department)

    def switch_school(school):
        open_navigation(page); page.locator('#school-switcher').click()
        page.locator(f'[data-home-school="{school}"]').click()
        wait_until(page, f"state.dashboard?.school_name === '{school}' && state.accountWorkspaceLoadingCount === 0", timeout=60)
        if width < 700 and page.locator('#glass-menu-toggle').get_attribute('aria-expanded') == 'true':
            page.locator('#glass-menu-toggle').click()

    switch_school('長庚大學')
    assert page.evaluate('state.applicationContext.target_school') != target
    switch_school(NCU)
    page.evaluate("location.hash='#overview'")
    expect(page.locator('#planning-target-summary')).to_contain_text(target)
    expect(page.locator('.planning-profile-summary')).to_contain_text('IELTS 7')
    page.evaluate("location.hash='#favorites'")
    for school in favorites:
        expect(page.locator('#selection-workspace')).to_contain_text(school)
    assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
    assert not errors
