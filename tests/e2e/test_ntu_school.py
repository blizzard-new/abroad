"""The third school uses its own catalogue, pending labels and grade scale."""
import pytest
from playwright.sync_api import expect

from .conftest import enter_public_site, open_navigation
from .test_open_catalog import wait_until
from .test_open_catalog import attach_session, sign_in_cookie
from .test_web_next_phase import _wait_for_workspace


@pytest.mark.parametrize("width", [390, 1440])
def test_visitor_can_browse_ntu_filter_details_and_switch_back(page, live_server, width):
    page.set_viewport_size({"width": width, "height": 956})
    page.emulate_media(reduced_motion="reduce")
    errors = []
    page.on("pageerror", lambda error: errors.append(str(error)))
    enter_public_site(page, live_server, "partners")
    page.locator("#school-switcher").click()
    expect(page.locator("#school-options [data-home-school]")).to_have_count(6)
    assert page.locator("#school-options [data-home-school]").evaluate_all(
        "nodes => nodes.map(node => node.dataset.homeSchool)"
    ) == ["長庚大學", "國立臺北大學", "國立臺灣大學", "國立中正大學", "國立中央大學", "淡江大學"]
    page.locator('[data-home-school="國立臺灣大學"]').click()
    if width < 700 and page.locator("#glass-menu-toggle").get_attribute("aria-expanded") == "true":
        page.locator("#glass-menu-toggle").click()
    expect(page.locator("#school-switcher-label")).to_have_text("國立臺灣大學")
    wait_until(page, "state.dashboard?.school_name === '國立臺灣大學' && state.dashboard.partner_universities.length === 289")
    page.evaluate("location.hash='#partners'")
    page.locator('[data-partner-view="list"]').click()
    page.locator("#partner-search").fill("蒙大拿州立大學")
    expect(page.locator("#partner-table")).to_contain_text("蒙大拿州立大學")
    expect(page.locator("#partner-table")).to_contain_text("本期名額待核實")
    page.locator("#partner-table .partner-card > summary").first.click()
    expect(page.locator("#partner-table .partner-card-summary")).to_contain_text("GPA")
    page.locator("#partner-table .school-detail-trigger:visible").first.click()
    expect(page.locator("#school-detail-view")).to_be_visible()
    expect(page.locator("#school-detail-view")).to_contain_text("蒙大拿州立大學")
    expect(page.locator("#school-detail-view")).to_contain_text("待確認")
    expect(page.locator("#school-detail-view .partner-student-summary")).to_contain_text("GPA")
    expect(page.locator("#school-detail-view .partner-student-summary")).to_contain_text("免繳")
    expect(page.locator("#school-detail-view .partner-student-summary")).to_contain_text("My Global Connection")
    expect(page.locator("#school-detail-view .partner-student-summary")).to_contain_text("兩封推薦信")
    from pathlib import Path
    output=Path('/tmp/ntu-audit/browser'); output.mkdir(parents=True,exist_ok=True)
    page.screenshot(path=str(output/f'ntu-summary-{width}.png'),full_page=True)
    page.locator("#detail-tab-application").click()
    expect(page.locator("#detail-application")).to_be_visible()
    expect(page.locator("#detail-application")).to_contain_text("臺大")
    page.evaluate("location.hash='#advisor'")
    expect(page.locator("#advisor-academic-score")).to_be_hidden()
    expect(page.locator("#advisor-academic-gpa")).to_be_visible()
    expect(page.locator("#advisor-class-rank")).to_be_visible()
    page.locator("#advisor-college").select_option("工學院")
    page.locator("#advisor-department-text").fill("機械工程學系")
    expect(page.locator("#advisor-department-text")).to_have_value("機械工程學系")
    expect(page.locator("#advisor-academic-rule")).to_contain_text("研究生校內無成績門檻")
    page.locator("#school-switcher").click()
    page.locator('[data-home-school="長庚大學"]').click()
    if width < 700 and page.locator("#glass-menu-toggle").get_attribute("aria-expanded") == "true":
        page.locator("#glass-menu-toggle").click()
    wait_until(page, "state.dashboard?.school_name === '長庚大學'")
    page.evaluate("location.hash='#advisor'")
    expect(page.locator("#advisor-academic-score")).to_be_visible()
    expect(page.locator("#advisor-academic-gpa")).to_be_hidden()
    assert page.locator("#advisor-department").evaluate("node => node.tagName") == "SELECT"
    assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
    assert not errors


def test_ntu_saved_conditions_keep_gpa_and_rank_without_percent_conversion(page, live_server):
    session = sign_in_cookie(live_server, school="國立臺灣大學")
    attach_session(page, live_server, session)
    enter_public_site(page, live_server, "advisor")
    expect(page.locator("#advisor-academic-gpa")).to_be_visible()
    page.locator("#advisor-college").select_option("工學院")
    page.locator("#advisor-department-text").fill("機械工程學系")
    page.locator("#advisor-degree").select_option("大學部")
    page.locator("#advisor-academic-gpa").fill("2.3")
    page.locator("#advisor-class-rank").fill("30")
    page.locator("#advisor-language-test").select_option("toefl_new")
    page.locator("#advisor-language-score").fill("4")
    with page.expect_response(lambda response: response.url.endswith("/advisor/plan") and response.request.method == "POST") as response:
        page.locator("#advisor-submit").click()
    assert response.value.ok
    payload = response.value.request.post_data_json
    assert payload["academic_score"] is None
    assert payload["academic_gpa"] == 2.3 and payload["class_rank_percent"] == 30
    assert "符合校內成績擇一門檻" in str(response.value.json())
    recommendations = response.value.json()["recommendations"]
    assert recommendations and all(item["eligibility_status"] == "needs_confirmation" for item in recommendations)
    assert page.locator("#eligibility-preference-1 option").count() == 283
    saved = _wait_for_workspace(live_server, session, lambda item:
        ((item.get("workspace", {}).get("selection_conditions") or {}).get("profile") or {}).get("class_rank_percent") == 30,
        home_school="國立臺灣大學"
    )["workspace"]["selection_conditions"]["profile"]
    assert saved["academic_gpa"] == 2.3 and saved["academic_score"] is None
    page.locator("#advisor-result-content [data-planning-target]").first.click()
    expect(page.locator("#planning-target-summary")).to_contain_text(recommendations[0]["school_name"])
    page.locator("#planning-deadline-settings > summary").click()
    page.locator("#planning-academic-year").fill("116")
    page.locator("#planning-application-round").fill("")
    with page.expect_response(lambda result: "/application-workflow?" in result.url and result.request.method == "GET") as preview:
        page.locator("#planning-preview-button").click()
    assert preview.value.ok
    expect(page.locator("#planning-schedule-status")).to_contain_text("已顯示參考流程")
    expect(page.locator("#planning-schedule-status")).to_contain_text("不會加入日曆或啟用截止提醒")
    expect(page.locator("#planning-schedule-preview .planning-timeline-item")).to_have_count(11)
    expect(page.locator("#planning-confirm")).to_be_hidden()
    assert page.evaluate("partnerAvailabilityMeta(state.dashboard.partner_universities.find(p=>p.quota === '0 名')).blocked")
    assert not page.evaluate("homeAcademicPass({degree:'在職碩士班',academicGpa:4,classRankPercent:1})")
    page.evaluate("location.hash='#advisor'")
    page.reload()
    expect(page.locator("#advisor-academic-gpa")).to_have_value("2.3")
    expect(page.locator("#advisor-class-rank")).to_have_value("30")


@pytest.mark.parametrize("school", ["長庚大學", "國立臺北大學"])
def test_new_toefl_has_confirmation_instead_of_nan_on_existing_schools(page, live_server, school):
    session = sign_in_cookie(live_server, school=school)
    attach_session(page, live_server, session)
    enter_public_site(page, live_server, "partners")
    wait_until(page, f"state.dashboard?.school_name === '{school}'")
    result = page.evaluate("""() => {
      const partner = state.dashboard.partner_universities.find(item=>item.availability_status === 'open');
      const profile = {college:homeCollegeOptions()[0],degree:'大學部',academicScore:90,languageTest:'toefl_new',languageScore:4.5};
      return {threshold:languageThresholdFromPartner(partner,'toefl_new'),match:partnerMatch(partner,profile)};
    }""")
    assert result["threshold"] is None
    assert "NaN" not in str(result["match"])
    assert "合作校語言門檻需另查" in result["match"]["risks"]


@pytest.mark.parametrize('width',[390,1440])
def test_ntu_document_language_conditions_change_in_real_form(page,live_server,width):
    page.set_viewport_size({'width':width,'height':956})
    page.emulate_media(reduced_motion='reduce')
    session=sign_in_cookie(live_server,school='國立臺灣大學')
    live_server.verify_student(session['profile']['id'],university='國立臺灣大學')
    attach_session(page,live_server,session)
    enter_public_site(page,live_server,'application-center')
    page.locator('[data-open-application-template="exchange-application-data"]').first.click()
    expect(page.locator('#application-document-form')).to_be_visible()
    group=page.locator('#application-field-language_group')
    identity=page.locator('#application-field-international_degree_student')
    test=page.locator('#application-field-language_test')
    actual=page.locator('#application-field-language_result_date')
    group.select_option('中語組'); identity.select_option('否')
    assert not test.evaluate('node=>node.required')
    assert not actual.evaluate('node=>node.required')
    identity.select_option('是')
    assert test.evaluate('node=>node.required') and actual.evaluate('node=>node.required')
    assert test.locator('option').all_text_contents()==['請選擇','TOCFL','HSK']
    test.select_option('TOCFL')
    group.select_option('日語組')
    assert test.input_value()==''
    assert 'JLPT' in test.locator('option').all_text_contents()
    assert 'IELTS Academic' not in test.locator('option').all_text_contents()
    group.select_option('一般組')
    options=test.locator('option').all_text_contents()
    assert 'GEPT' in options and 'BESTEP' in options
    assert 'TOEIC' not in options and 'Duolingo' not in options
    test.select_option('GEPT')
    expect(actual).to_have_attribute('min','2025-05-01')
    page.locator('#application-field-language_planned_result_date').fill('2026-11-01')
    assert actual.input_value()=='' and actual.evaluate('node=>node.validity.valueMissing')
    actual.fill('2025-04-30')
    assert actual.evaluate('node=>node.validity.rangeUnderflow')
    actual.fill('2025-05-01')
    assert actual.evaluate('node=>node.validity.valid')
    from pathlib import Path
    output=Path('/tmp/ntu-audit/browser'); output.mkdir(parents=True,exist_ok=True)
    page.screenshot(path=str(output/f'ntu-language-form-{width}.png'),full_page=True)
    assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
