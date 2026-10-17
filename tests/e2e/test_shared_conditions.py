"""One editable set of conditions, real APIs, no stale response replacing edits."""
import pytest
import requests
from playwright.sync_api import expect

from .conftest import expand_details
from .test_glass_theme import verified_login, capture
from .test_planning_workspace import create_target
from .test_web_next_phase import _auth_headers


@pytest.mark.parametrize("width", [390,1754])
def test_one_form_keeps_unsaved_conditions_across_modes_and_saves_same_inputs(page, live_server, width):
    page.set_viewport_size({"width":width,"height":956})
    page.emulate_media(reduced_motion="reduce")
    verified_login(page,live_server)
    page.evaluate("location.hash='#advisor'")
    expect(page.locator("#advisor-form")).to_be_visible()
    page.locator("#advisor-college").select_option("工學院")
    page.locator("#advisor-department").select_option("資訊工程學系")
    page.locator("#advisor-degree").select_option("大學部")
    expand_details(page, "#advisor-qualification-fields")
    page.locator("#advisor-academic-score").fill("84")
    expand_details(page, "#advisor-form > .advisor-more-fields:not(#advisor-qualification-fields)")
    page.locator("#advisor-question").fill("我的問題草稿")
    page.locator("#advisor-form").evaluate("node=>window.sharedConditionsNode=node")
    expand_details(page, "#application-workspace-tool-menu")
    page.locator('#application-workspace-tools a[href="#eligibility"]').click()
    expect(page.locator("#eligibility #advisor-form")).to_be_visible()
    expect(page.locator("#eligibility-form,#eligibility-college,#eligibility-department")).to_have_count(0)
    expect(page.locator("#advisor-academic-score")).to_have_value("84")
    expect(page.locator("#advisor-college")).to_have_count(1)
    expect(page.locator("#eligibility-academic-year")).to_be_enabled()
    page.locator("#eligibility-academic-year").select_option("116")
    page.locator("#eligibility-application-round").select_option("第一梯次")
    school = page.locator("#eligibility-preference-1 option").evaluate_all("rows=>rows.find(row=>row.value).value")
    page.locator("#eligibility-preference-1").select_option(school)
    expand_details(page, "#advisor-qualification-fields")
    page.locator("#advisor-academic-score").fill("91")
    expand_details(page, "#application-workspace-tool-menu")
    page.locator('#application-workspace-tools a[href="#advisor"]').click()
    expect(page.locator("#advisor #advisor-form")).to_be_visible()
    assert page.locator("#advisor-form").evaluate("node=>node===window.sharedConditionsNode")
    expect(page.locator("#advisor-academic-score")).to_have_value("91")
    expect(page.locator("#advisor-question")).to_have_value("我的問題草稿")
    expect(page.locator("#eligibility-academic-year")).to_be_disabled()
    # Exploration accepts missing language scores and ignores the hidden period's validation.
    with page.expect_response(lambda r:r.url.endswith('/advisor/plan') and r.request.method=='POST') as updated:
        page.locator("#advisor-submit").click()
    assert updated.value.ok
    assert updated.value.request.post_data_json["academic_score"] == 91
    expect(page.locator("#advisor-profile-status")).to_have_text("已保存條件")
    expand_details(page, "#application-workspace-tool-menu")
    page.locator('#application-workspace-tools a[href="#eligibility"]').click()
    expect(page.locator("#eligibility-preference-1")).to_have_value(school)
    expand_details(page, "#advisor-qualification-fields")
    page.locator("#advisor-language-test").select_option("ielts")
    page.locator("#advisor-language-score").fill("7")
    with page.expect_response(lambda r:r.url.endswith('/application-plan/evaluate') and r.request.method=='POST') as checked:
        page.locator("#advisor-submit").click()
    assert checked.value.ok
    assert checked.value.request.post_data_json["academic_score"] == 91
    assert checked.value.request.post_data_json["department"] == "資訊工程學系"
    expect(page.locator("#eligibility-result")).to_contain_text(school)
    page.wait_for_function("() => document.querySelector('#account-workspace-sync-label').textContent==='已同步'")
    capture(page,f'shared-conditions-{width}.png')
    page.reload()
    expect(page.locator("#eligibility #advisor-form")).to_be_visible()
    expect(page.locator("#advisor-academic-score")).to_have_value("91")
    expect(page.locator("#eligibility-academic-year")).to_have_value("116")
    assert page.evaluate("document.documentElement.scrollWidth<=innerWidth")


@pytest.mark.parametrize("endpoint", ["/advisor/plan","/application-plan/evaluate"])
def test_real_response_after_edit_is_not_applied_or_saved(page,live_server,endpoint):
    session,target = create_target(page,live_server)
    page.wait_for_function("() => document.querySelector('#account-workspace-sync-label').textContent==='已同步'")
    before=requests.get(f'{live_server.base_url}/account/workspace',headers=_auth_headers(session)).json()['workspace']
    page.evaluate("location.hash='#eligibility'" if endpoint.endswith('evaluate') else "location.hash='#advisor'")
    if endpoint.endswith('evaluate'):
        department=page.locator('#advisor-department option').evaluate_all('rows=>rows.find(row=>row.value).value')
        page.locator('#advisor-department').select_option(department)
        page.locator('#eligibility-academic-year').select_option('116')
        page.locator('#eligibility-application-round').select_option('第一梯次')
        page.locator('#eligibility-preference-1').select_option(target)
    page.evaluate("""endpoint=>{
      const fetchReal=window.fetch;
      window.fetch=async (...args)=>{
        const response=await fetchReal(...args);
        if(String(args[0]).endsWith(endpoint)) await new Promise(resolve=>window.releaseConditionsResponse=resolve);
        return response;
      };
    }""",endpoint)
    page.locator('#advisor-submit').click()
    page.wait_for_function("() => typeof window.releaseConditionsResponse==='function'")
    expand_details(page, "#advisor-qualification-fields")
    page.locator('#advisor-academic-score').fill('92')
    page.evaluate('window.releaseConditionsResponse()')
    expect(page.locator('#advisor-submit')).to_be_enabled()
    message=page.locator('#eligibility-result' if endpoint.endswith('evaluate') else '#advisor-result-content')
    expect(message).to_contain_text('未套用或保存')
    expect(page.locator('#advisor-academic-score')).to_have_value('92')
    assert page.evaluate('state.eligibilityProfile.academicScore') == 85
    assert page.evaluate("JSON.parse(localStorage.getItem(STORAGE_KEYS.eligibility)).academicScore") == 85
    saved=requests.get(f'{live_server.base_url}/account/workspace',headers=_auth_headers(session)).json()['workspace']
    # The existing server workspace stores context, not the full score profile.
    assert saved['application_context'] == before['application_context']
    assert saved['application_schools'] == before['application_schools']
