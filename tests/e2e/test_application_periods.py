from uuid import uuid4

import pytest
from playwright.sync_api import expect

from exchange_info.storage import load_application_workflows, save_application_workflows
from test_application_periods import workflow
from .conftest import login_through_web
from .test_glass_theme import capture


@pytest.mark.parametrize("width",[390,1754])
def test_sourced_rounds_retry_and_keep_unsent_draft(page,live_server,request,width):
    original=load_application_workflows(live_server.data_dir)
    request.addfinalizer(lambda:save_application_workflows(original,live_server.data_dir))
    save_application_workflows([*original,workflow("隔離年度梯次校",academic_year="113")],live_server.data_dir)
    email=f'period-{uuid4().hex[:8]}@example.com'
    account=live_server.register(email)
    live_server.verify_student(account['profile']['id'])
    page.set_viewport_size({'width':width,'height':956})
    page.emulate_media(reduced_motion='reduce')
    errors=[]
    page.on('pageerror',lambda error:errors.append(str(error)))
    failures=[0]
    def fail_once(route):
        if failures[0]:
            failures[0]=0
            route.fulfill(status=503,content_type='application/json',body='{"detail":"測試暫時無法讀取"}')
        else:
            route.continue_()
    page.route('**/application-period-options?*',fail_once)
    # The catalogue is public, so visitors load period options too; arm the failure only for the load
    # that happens on the eligibility page after signing in.
    login_through_web(page,live_server,email)
    # Login closes its dialog before catalogue hydration finishes. Let those
    # requests finish so the injected failure belongs to the reload under test.
    page.wait_for_load_state("networkidle", timeout=60_000)
    page.evaluate("location.hash='#eligibility'")
    failures[0]=1
    with page.expect_response(lambda response:'/application-period-options?' in response.url and response.status==503):
        page.reload()
    assert errors==[]
    expect(page.locator('#application-period-retry')).to_be_visible()
    page.locator('#eligibility-academic-year').select_option('116')
    page.locator('#eligibility-application-round').select_option('第二梯次')
    page.locator('#advisor-academic-score').fill('93')
    # Delay a real successful response; continuing to edit must not be overwritten.
    page.evaluate("""()=>{
      const real=window.fetch;
      window.fetch=async (...args)=>{
        const response=await real(...args);
        if(String(args[0]).includes('/application-period-options?'))
          await new Promise(resolve=>window.releasePeriodResponse=resolve);
        return response;
      };
    }""")
    page.locator('#application-period-retry').click()
    page.wait_for_function("() => typeof window.releasePeriodResponse==='function'")
    page.locator('#eligibility-academic-year').select_option('117')
    page.locator('#advisor-academic-score').fill('94')
    page.evaluate('window.releasePeriodResponse()')
    expect(page.locator('#application-period-retry')).to_be_hidden()
    expect(page.locator('#eligibility-academic-year')).to_have_value('117')
    expect(page.locator('#eligibility-application-round')).to_have_value('第二梯次')
    expect(page.locator('#advisor-academic-score')).to_have_value('94')
    expect(page.locator('#application-period-hint')).to_contain_text('尚無對應流程')
    page.locator('#eligibility-academic-year').select_option('113')
    page.locator('#eligibility-application-round').select_option('秋季梯次')
    expect(page.locator('#application-period-hint')).to_contain_text('113 學年度 · 秋季梯次')
    expect(page.locator('#application-period-source')).to_have_attribute('href','https://example.edu/notice')
    assert '此年度流程待確認' in page.locator('#eligibility-application-round option[value="第一梯次"]').text_content()
    page.locator('#eligibility-academic-year').select_option('117')
    expect(page.locator('#eligibility-application-round')).to_have_value('秋季梯次')
    expect(page.locator('#application-period-source')).to_be_hidden()
    assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
    assert errors==[]
    capture(page,f'application-periods-{width}.png')
