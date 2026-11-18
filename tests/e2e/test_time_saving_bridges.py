"""Time-saving workflow bridges (TS-01..TS-04) and above-the-fold mobile #partners layout."""
from __future__ import annotations

from urllib.parse import quote

from playwright.sync_api import expect

from .conftest import enter_public_site, expand_details
from .test_glass_theme import verified_login
from .test_partner_globe import LINCOLN, MEIJI


def test_plan_dialog_prefills_saved_conditions_and_semester(page, live_server):
    page.set_viewport_size({"width": 1280, "height": 900})
    verified_login(page, live_server)

    page.evaluate("location.hash = '#advisor'")
    expect(page.locator("#advisor-form")).to_be_visible()
    page.locator("#advisor-college").select_option("工學院")
    page.locator("#advisor-department").select_option("資訊工程學系")
    page.locator("#advisor-degree").select_option("大學部")
    page.locator("#advisor-target-term").select_option("2027-fall")
    expand_details(page, "#advisor-qualification-fields")
    page.locator("#advisor-academic-score").fill("86")
    with page.expect_response(lambda r: r.url.endswith("/advisor/plan") and r.request.method == "POST") as saved:
        page.locator("#advisor-submit").click()
    assert saved.value.ok
    expect(page.locator("#advisor-profile-status")).to_have_text("已保存條件")

    page.goto(f"{live_server.base_url}/#my-application?target={quote(LINCOLN)}")
    dialog = page.locator("#plan-dialog")
    expect(dialog).to_be_visible()
    expect(page.locator("#create-target")).to_have_value(LINCOLN)
    expect(page.locator("#create-college")).to_have_value("工學院")
    expect(page.locator("#create-department")).to_have_value("資訊工程學系")
    expect(page.locator("#create-degree")).to_have_value("大學部")
    expect(page.locator("#create-departure")).to_have_value("2027")
    expect(page.locator("#create-term")).to_have_value("fall")
    expect(page.locator('#create-semesters input[type="radio"]:checked')).to_have_count(1)
    expect(dialog.locator("#create-prefill-note")).to_be_visible()


def test_my_application_empty_view_offers_one_click_shortlist_setup(page, live_server):
    page.set_viewport_size({"width": 390, "height": 844})
    verified_login(page, live_server)

    page.evaluate("location.hash = '#partners'")
    page.locator('[data-partner-view="list"]').click()
    for school in (LINCOLN, MEIJI):
        page.locator(f'#partner-table .favorite-toggle[data-school-name="{school}"]').click()

    page.evaluate("location.hash = '#my-application'")
    empty_view = page.locator("#empty-view")
    expect(empty_view).to_be_visible()
    expect(empty_view).to_contain_text("從已收藏的候選學校一鍵建立計畫")
    expect(empty_view.locator("#empty-create")).to_be_visible()
    lincoln_btn = empty_view.locator(f'[data-path-target="{LINCOLN}"]')
    meiji_btn = empty_view.locator(f'[data-path-target="{MEIJI}"]')
    expect(lincoln_btn).to_be_visible()
    expect(meiji_btn).to_be_visible()

    lincoln_btn.click()
    expect(page.locator("#plan-dialog")).to_be_visible()
    expect(page.locator("#create-target")).to_have_value(LINCOLN)


def test_discovery_comparison_decision_matrix_and_prepare_cta(page, live_server):
    page.set_viewport_size({"width": 1280, "height": 900})
    verified_login(page, live_server)

    page.evaluate("location.hash = '#partners'")
    page.locator('[data-partner-view="list"]').click()
    for school in (LINCOLN, MEIJI):
        page.locator(f'#partner-table [data-compare-pick="{school}"]').check()

    page.locator("#discovery-criteria summary").click()
    page.locator("#discovery-test").evaluate("el => { el.value = 'ielts'; el.dispatchEvent(new Event('change', { bubbles: true })); }")
    page.locator("#discovery-score").fill("6.5")
    page.locator('#discovery-criteria-form [name="grade"]').fill("85")
    page.locator('#discovery-criteria-form [name="scale"]').evaluate("el => { el.value = '100'; el.dispatchEvent(new Event('change', { bubbles: true })); }")
    page.locator('#discovery-criteria-form [name="degree"]').evaluate("el => { el.value = 'undergraduate'; el.dispatchEvent(new Event('change', { bubbles: true })); }")
    page.locator('#discovery-criteria-form [name="term"]').evaluate("el => { el.value = 'fall'; el.dispatchEvent(new Event('change', { bubbles: true })); }")
    page.locator('#discovery-criteria-form button[type="submit"]').click()

    profile = page.evaluate("state.eligibilityProfile")
    assert float(profile["languageScore"]) == 6.5
    assert float(profile["academicScore"]) == 85
    assert profile["gpaScale"] == "100"

    page.evaluate("location.hash = '#favorites'")
    comparison = page.locator("#discovery-comparison")
    expect(comparison).to_be_visible()
    expect(comparison.locator(".compare-avail-badge").first).to_be_visible()
    expect(comparison).to_contain_text("個人條件初步比對")
    expect(comparison.locator(".compare-fit-badge").first).to_be_visible()
    expect(comparison).to_contain_text("申請期限")
    expect(comparison).to_contain_text("官方簡章／來源")
    expect(comparison.locator('.compare-source-links a[target="_blank"]').first).to_be_visible()
    expect(comparison.locator(".compare-remove-btn")).to_have_count(2)

    start_link = comparison.locator(f'.compare-start-btn[href*="{quote(LINCOLN)}"]')
    expect(start_link).to_be_visible()
    start_link.click()

    expect(page.locator("#plan-dialog")).to_be_visible()
    expect(page.locator("#create-target")).to_have_value(LINCOLN)
    expect(page.locator("#create-term")).to_have_value("fall")
    expect(page.locator('#create-semesters input[type="radio"]:checked')).to_have_count(1)


def test_mobile_partners_renders_first_school_card_above_fold_without_overflow(page, live_server):
    page.set_viewport_size({"width": 390, "height": 844})
    enter_public_site(page, live_server, "partners", view="list")

    first_card = page.locator("#partner-table .pr-school-card").first
    expect(first_card).to_be_visible()
    card_box = first_card.bounding_box()
    assert card_box is not None
    assert card_box["y"] < 520, f"Expected first school card top y < 520px on 390x844, got {card_box['y']}"
    assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth")
    assert page.locator("#partner-search-submit").evaluate("el => getComputedStyle(el).boxShadow") == "none"
    expect(first_card.locator(".pr-card-prepare-link")).to_be_visible()
