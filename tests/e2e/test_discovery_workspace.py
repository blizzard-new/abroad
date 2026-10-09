import json
from pathlib import Path
from urllib.parse import quote
from uuid import uuid4

import requests
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError, expect

from exchange_info.repositories import JsonlAccountRepository

from .conftest import enter_public_site, login_through_web
from .test_partner_globe import LINCOLN, MEIJI, inject_dashboard, open_partners, ready
from .test_web_next_phase import _wait_for_workspace, _workspace


def setup_catalog(page):
    def catalog(payload):
        payload["partner_universities"] = [p for p in payload["partner_universities"] if p["school_name"] in [LINCOLN, MEIJI]]
        for p in payload["partner_universities"]:
            p["program_options"] = []
            p["eligibility"] = "IELTS 6.0；GPA 3.0 / 4.0" if p["school_name"] == LINCOLN else "IELTS 7.5"
            p["student_summary_zh"]["eligibility_points"] = [p["eligibility"]]
            p["degree_levels"] = "大學部"
            p["study_period"] = "春季、秋季"
    inject_dashboard(page, catalog)
    def sources(route):
        source = {"school_name": LINCOLN, "country":"紐西蘭", "title":"宿舍與通勤心得", "source_url":"https://www.lincoln.ac.nz/student-story", "source_type":"article", "platform":"學生分享", "summary":"I cooked in the residence kitchen.", "original_summary":"I cooked in the residence kitchen.", "summary_zh":"我在宿舍廚房煮飯，平日騎車上學。", "translation_status":"machine", "exchange_term":"2025 秋季", "published_at":"2026-01-01", "themes":["housing","food","transport"], "theme_summaries":{"food":"I cooked in the residence kitchen."}, "theme_summaries_zh":{"food":"我在宿舍廚房煮飯。"}}
        route.fulfill(json={"school_name":LINCOLN,"total_sources":1,"sources":[source],"highlights":[],"common_strengths":[],"common_challenges":[],"mixed_opinions":[]})
    page.route("**/student-experiences?*", sources)


def test_combined_search_map_preview_and_chinese_reader(page, live_server):
    setup_catalog(page)
    errors=[];page.on("pageerror",lambda error:errors.append(str(error)))
    open_partners(page,live_server,{"view":"list"})
    expect(page.locator(".partner-table tbody tr")).to_have_count(2)
    page.locator("#discovery-criteria summary").click()
    page.locator("#discovery-test").select_option("ielts")
    page.locator("#discovery-score").fill("6.5")
    page.locator('[name="grade"]').fill("3.4")
    page.locator('#discovery-criteria-form [name="scale"]').select_option("4")
    page.locator('#discovery-criteria-form [name="degree"]').select_option("undergraduate")
    page.locator('#discovery-criteria-form [name="term"]').select_option("fall")
    page.locator('#discovery-criteria-form [type="submit"]').click()
    expect(page.locator(".partner-table tbody tr")).to_have_count(1)
    expect(page.locator(".partner-table tbody")).to_contain_text("已知門檻符合")
    page.locator('[data-partner-view="map"]').click();ready(page)
    page.locator("#map-school-select").select_option(LINCOLN)
    expect(page.locator(".discovery-preview-extras")).to_contain_text("平日騎車上學")
    expect(page.locator("#partner-map-preview")).to_contain_text("交換名額")
    page.locator("#partner-map-preview [data-read-experience]").click()
    expect(page.locator("#discovery-reader")).to_be_visible()
    expect(page.locator("#discovery-reader")).to_contain_text("2025 秋季")
    expect(page.locator(".discovery-reader-original p").first).to_be_hidden()
    page.locator(".discovery-reader-original summary").click()
    expect(page.locator(".discovery-reader-original")).to_contain_text("I cooked")
    page.locator("[data-close-reader]").click()
    expect(page.locator("#partner-map-preview")).to_be_visible()
    page.locator("#partner-map-preview .school-detail-trigger").click()
    page.get_by_role("tab",name="學生心得",exact=True).click()
    page.locator('[data-experience-theme="food"]').click()
    expect(page.locator("#experience-content")).to_contain_text("我在宿舍廚房煮飯。")
    page.locator("#experience-content [data-save-experience]").click()
    page.locator("#experience-content [data-read-experience]").click()
    page.locator("[data-close-reader]").click()
    page.goto(f"{live_server.base_url}/#favorites")
    page.locator('[data-discovery-shelf="experiences"]').click()
    page.locator("#discovery-saved-country").select_option("紐西蘭")
    page.locator("#discovery-saved-school").select_option(LINCOLN)
    expect(page.locator("#discovery-saved-experiences")).to_contain_text("宿舍與通勤心得")
    page.reload()
    page.locator('[data-discovery-shelf="experiences"]').click()
    expect(page.locator("#discovery-saved-experiences")).to_contain_text("宿舍與通勤心得")
    assert not errors


def test_cloud_selection_roundtrip_home_isolation_and_logout(page, browser, live_server):
    email = f"discovery-{uuid4().hex[:10]}@example.com"
    session = live_server.register(email)
    setup_catalog(page)
    login_through_web(page, live_server, email)
    expect(page.locator("#account-workspace-sync-label")).to_have_text("已同步", timeout=15000)
    page.evaluate("location.hash = '#partners'")
    page.locator(f'.desktop-partner-table .favorite-toggle[data-school-name="{LINCOLN}"]').click()
    page.evaluate("location.hash = '#favorites'")
    page.locator(f'[data-interest-school="{LINCOLN}"][data-interest="4"]').click()
    page.locator(f'[data-school-note="{LINCOLN}"]').fill("只給這個帳號看的選校理由")
    page.locator(f'[data-school-note="{LINCOLN}"]').press("Tab")
    page.locator(f'.discovery-candidates [data-preference-toggle="{LINCOLN}"]').click()
    page.locator(f'.discovery-candidate .school-detail-trigger[data-school-name="{LINCOLN}"]').click()
    page.get_by_role("tab", name="學生心得", exact=True).click()
    page.locator("#experience-content [data-read-experience]").click()
    page.locator("#discovery-reader [data-save-experience]").click()
    page.locator("[data-close-reader]").click()
    saved = _wait_for_workspace(live_server, session, lambda response: (
        response["workspace"]["discovery"]["school_preferences"].get(LINCOLN, {}).get("note") == "只給這個帳號看的選校理由"
        and len(response["workspace"]["discovery"]["saved_experiences"]) == 1
        and len(response["workspace"]["discovery"]["recent_views"]) == 2
    ))["workspace"]["discovery"]
    assert saved["preference_order"] == [LINCOLN]
    assert saved["school_preferences"][LINCOLN]["interest"] == 4

    # A fresh browser has no local cache to mask a failed cloud write/read.
    other_context = browser.new_context(viewport={"width": 1280, "height": 900})
    try:
        other = other_context.new_page()
        setup_catalog(other)
        login_through_web(other, live_server, email)
        expect(other.locator("#account-workspace-sync-label")).to_have_text("已同步", timeout=15000)
        other.evaluate("location.hash = '#favorites'")
        expect(other.locator(f'[data-school-note="{LINCOLN}"]')).to_have_value("只給這個帳號看的選校理由")
        expect(other.locator("[data-rank-school]")).to_have_count(1)
        other.locator('[data-discovery-shelf="experiences"]').click()
        expect(other.locator("#discovery-saved-experiences")).to_contain_text("宿舍與通勤心得")
        other.locator("#account-button").click()
        expect(other.locator("#profile-dialog [data-discovery-recents]")).to_contain_text("宿舍與通勤心得")
        other.locator("#logout-button").click()
        expect(other.locator("#account-button-label")).to_have_text("登入")
        assert other.evaluate("Object.keys(localStorage).filter(k => k.startsWith('uniway-discovery-v1:') && !k.startsWith('uniway-discovery-v1:guest:'))") == []
        expect(other.locator(".discovery-candidate")).to_have_count(0)
        expect(other.locator("#discovery-saved-experiences")).not_to_contain_text("宿舍與通勤心得")
    finally:
        other_context.close()

    page.locator("#back-to-schools").click()
    page.locator("#school-switcher").click()
    page.locator('[data-home-school="國立臺北大學"]').click()
    page.locator("#confirm-school").click()
    expect(page.locator("#school-switcher-label")).to_have_text("國立臺北大學")
    page.evaluate("location.hash = '#favorites'")
    expect(page.locator(".discovery-candidate")).to_have_count(0)
    expect(page.locator("[data-rank-school]")).to_have_count(0)
    page.locator("#school-switcher").click()
    page.locator('[data-home-school="長庚大學"]').click()
    page.locator("#confirm-school").click()
    expect(page.locator(f'[data-school-note="{LINCOLN}"]')).to_have_value("只給這個帳號看的選校理由", timeout=15000)
    assert _workspace(live_server, session, "國立臺北大學")["workspace"]["discovery"]["school_preferences"] == {}
    cookie = next(c for c in page.context.cookies() if c["name"] == "exchange_guide_session")
    revoked = requests.post(f"{live_server.base_url}/auth/logout", cookies={cookie["name"]: cookie["value"]}, timeout=10)
    assert revoked.status_code == 204
    # A background protected request can already discover the revoked session
    # and remove this private form. Either route must expose login and clear
    # private state; attempting to fill a detached form only obscures that check.
    note = page.locator(f'[data-school-note="{LINCOLN}"]')
    if not page.locator("#auth-dialog").is_visible():
        try:
            note.fill("過期後不能上傳", timeout=5000)
            note.press("Tab", timeout=5000)
        except PlaywrightTimeoutError:
            if not page.locator("#auth-dialog").is_visible():
                raise
    expect(page.locator("#auth-dialog")).to_be_visible(timeout=15000)
    expect(page.locator(".discovery-candidate")).to_have_count(0)
    assert not page.evaluate("Object.keys(localStorage).some(k => k.startsWith('uniway-discovery-v1:') && !k.startsWith('uniway-discovery-v1:guest:'))")
    persisted = JsonlAccountRepository(live_server.data_dir).find_account_by_id(session["profile"]["id"])
    assert persisted is not None
    assert "過期後不能上傳" not in persisted.model_dump_json()


def test_candidates_notes_order_persistence_mobile_and_history(page,live_server):
    setup_catalog(page);open_partners(page,live_server,{"view":"list"})
    errors=[];page.on("pageerror",lambda error:errors.append(str(error)))
    for school in [LINCOLN, MEIJI]:
        page.locator(f'.desktop-partner-table .favorite-toggle[data-school-name="{school}"]').click()
    page.goto(f"{live_server.base_url}/#favorites")
    expect(page.locator(".discovery-candidate")).to_have_count(2)
    page.locator(f'[data-interest-school="{LINCOLN}"][data-interest="5"]').click()
    page.locator(f'[data-school-note="{LINCOLN}"]').fill("課程適合，但住宿要再確認。")
    page.locator(f'[data-school-note="{LINCOLN}"]').press("Tab")
    for school in [LINCOLN,MEIJI]:
        page.locator(f'.discovery-candidates [data-preference-toggle="{school}"]').click()
    page.locator(f'[data-rank-up="{MEIJI}"]').click()
    expect(page.locator("[data-rank-school]").first).to_have_attribute("data-rank-school",MEIJI)
    page.locator(f'[data-rank-school="{MEIJI}"]').press("Alt+ArrowDown")
    expect(page.locator("[data-rank-school]").first).to_have_attribute("data-rank-school",LINCOLN)
    page.reload()
    expect(page.locator(f'[data-school-note="{LINCOLN}"]')).to_have_value("課程適合，但住宿要再確認。")
    expect(page.locator(f'[data-interest-school="{LINCOLN}"][data-interest="5"]')).to_have_attribute("aria-pressed","true")
    expect(page.locator("[data-rank-school]").first).to_have_attribute("data-rank-school",LINCOLN)
    page.locator("#discovery-use-preferences").click()
    expect(page.locator("#eligibility-preference-1")).to_have_value(LINCOLN)
    expect(page.locator("#eligibility-preference-2")).to_have_value(MEIJI)
    page.goto(f"{live_server.base_url}/#school={quote(LINCOLN)}")
    expect(page.locator("#school-detail-title")).to_have_text(LINCOLN)
    page.goto(f"{live_server.base_url}/#partners")
    expect(page.locator("#partners [data-discovery-recents]")).to_contain_text(LINCOLN)
    page.goto(f"{live_server.base_url}/#favorites")
    page.set_viewport_size({"width":393,"height":852})
    expect(page.locator(".discovery-candidate").first).to_be_visible()
    assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
    artifact=Path("output/selection-workspace");artifact.mkdir(parents=True,exist_ok=True)
    page.screenshot(path=str(artifact/"mobile.png"),full_page=True)
    page.set_viewport_size({"width":1440,"height":1000})
    page.screenshot(path=str(artifact/"desktop.png"),full_page=True)
    assert not errors
