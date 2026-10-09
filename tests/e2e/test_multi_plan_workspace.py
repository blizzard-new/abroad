import pytest
import requests
from playwright.sync_api import expect

from exchange_info.application_rules import build_personal_application_plan
from exchange_info.models import (ApplicationRuleScope, ApplicationStep, PartnerUniversity,
    PersonalApplicationPlanRequest, UniversityApplicationWorkflow)
from .test_glass_theme import verified_login, capture
from .test_web_next_phase import _auth_headers


def evaluate_fixture(route):
    payload = PersonalApplicationPlanRequest.model_validate(route.request.post_data_json)
    partners = []
    workflows = []
    for preference in payload.preferences:
        name = preference.school_name
        partners.append(PartnerUniversity(school_name=name,program_type="交換",colleges="四院皆可",
            degree_levels="大學部",source_url="https://home.edu/partners"))
        common = ApplicationStep(rule_id="home-submit",order=1,phase="校內申請",title="共用校內表格",
            responsible_party="學生",summary="準備並核對校內表格",support_status="verified",
            scope=ApplicationRuleScope(home_universities=[payload.home_school]),source_urls=["https://home.edu/notice"])
        branch = common.model_copy(deep=True,update={"rule_id":"host-submit","title":"合作校文件",
            "phase":"合作校申請","scope":ApplicationRuleScope(partner_universities=[name])})
        workflows.append(UniversityApplicationWorkflow(home_university=payload.home_school,school_name=name,steps=[common,branch]))
    plan=build_personal_application_plan(payload,partners,workflows,academic_score_minimum=75)
    route.fulfill(json=plan.model_dump(mode="json"))


@pytest.mark.parametrize("width",[390,1754])
def test_shared_progress_survives_reorder_removal_and_reload(page,live_server,width):
    page.set_viewport_size({"width":width,"height":956})
    page.emulate_media(reduced_motion="reduce")
    page.route("**/application-plan/evaluate",evaluate_fixture)
    session=verified_login(page,live_server)
    # Sign-in closes before noncritical hydration. Finish the real initial
    # workspace load before this persistence scenario starts editing its form.
    page.wait_for_function("() => state.accountWorkspaceHasSynced && state.accountWorkspaceLoadingCount === 0")
    page.wait_for_load_state("networkidle")
    errors=[]
    page.on("pageerror",lambda error:errors.append(str(error)))
    page.evaluate("location.hash='#overview'")
    expect(page.locator('#multi-plan-workspace')).to_be_visible()
    page.locator('#multi-plan-settings > summary').click()
    page.wait_for_function("() => state.dashboard && document.querySelector('#multi-plan-preferences select').options.length > 1",timeout=30000)
    selects=page.locator('#multi-plan-preferences select')
    expect(selects.first.locator('option')).not_to_have_count(1)
    names=selects.first.locator('option').evaluate_all('rows=>rows.filter(row=>row.value).slice(0,2).map(row=>row.value)')
    selects.nth(0).select_option(names[0]); selects.nth(1).select_option(names[1])
    page.locator('#multi-plan-preferences button').click()
    expect(page.locator('#multi-plan-status')).to_contain_text('2 個志願 · 3 項準備工作')
    shared=page.locator('.multi-plan-shared [data-multi-task]')
    expect(shared).to_have_count(1)
    task_id=shared.get_attribute('data-multi-task')
    with page.expect_response(lambda r: r.request.method == 'PUT'
            and '/account/workspace' in r.url
            and (r.request.post_data_json or {}).get('application_schools') == names
            and (r.request.post_data_json or {}).get('application_progress', {}).get('長庚大學', {}).get(task_id) is True) as progress_saved:
        shared.check()
    assert progress_saved.value.status == 200
    page.wait_for_function("() => document.querySelector('#account-workspace-sync-label').textContent === '已同步'")
    selects.nth(0).select_option(names[1]); selects.nth(1).select_option(names[0])
    # The previous save can still show 已同步 before this click's debounce runs.
    # Wait for this exact reordered payload to be acknowledged, then retain the
    # original direct server/readback/progress/reload assertions below.
    with page.expect_response(lambda r: r.request.method == 'PUT'
            and '/account/workspace' in r.url
            and (r.request.post_data_json or {}).get('application_schools') == [names[1], names[0]]) as reordered:
        page.locator('#multi-plan-preferences button').click()
    assert reordered.value.status == 200
    expect(page.locator('.multi-plan-branch').first).to_contain_text(names[1])
    expect(page.locator(f'[data-multi-task="{task_id}"]')).to_be_checked()
    page.wait_for_function("() => document.querySelector('#account-workspace-sync-label').textContent === '已同步'")
    workspace=requests.get(f'{live_server.base_url}/account/workspace',headers=_auth_headers(session)).json()['workspace']
    assert workspace['application_schools'] == [names[1],names[0]]
    assert workspace['application_progress']['長庚大學'][task_id] is True
    page.reload()
    expect(page.locator('.multi-plan-branch').first).to_contain_text(names[1])
    expect(page.locator(f'[data-multi-task="{task_id}"]')).to_be_checked()
    page.locator('#multi-plan-settings > summary').click()
    selects.nth(1).select_option('')
    page.locator('#multi-plan-preferences button').click()
    expect(page.locator('#multi-plan-status')).to_contain_text('1 個志願 · 2 項準備工作')
    expect(page.locator(f'[data-multi-task="{task_id}"]')).to_be_checked()
    selects.nth(1).select_option(names[0])
    page.locator('#multi-plan-preferences button').click()
    expect(page.locator('#multi-plan-status')).to_contain_text('2 個志願 · 3 項準備工作')
    expect(page.locator(f'[data-multi-task="{task_id}"]')).to_be_checked()
    assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
    assert errors == []
    capture(page,f'multi-plan-{width}.png')
