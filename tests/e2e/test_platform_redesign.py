"""The platform redesign: home landing, explore, guide, tracker, forum and the profile page."""
import json
import re
from uuid import uuid4

import pytest
from playwright.sync_api import expect

from .conftest import enter_public_site, login_through_web

ROUTES = ("home", "partners", "guide", "forum", "feedback")


def _no_horizontal_overflow(page) -> bool:
    return page.evaluate("() => document.documentElement.scrollWidth <= document.documentElement.clientWidth + 1")


@pytest.mark.parametrize("width", [1440, 834, 393])
@pytest.mark.parametrize("theme", ["light", "dark"])
def test_redesigned_pages_fit_every_width_and_theme(browser, live_server, width, theme) -> None:
    context = browser.new_context(viewport={"width": width, "height": 900})
    page = context.new_page()
    errors: list[str] = []
    page.on("pageerror", lambda error: errors.append(str(error)))
    page.add_init_script(f"window.localStorage.setItem('exchange-guide-theme', '{theme}')")
    try:
        for route in ROUTES:
            enter_public_site(page, live_server, route)
            expect(page.locator("html")).to_have_attribute("data-theme", theme)
            assert _no_horizontal_overflow(page), f"#{route} overflows at {width}px"
        assert not errors
    finally:
        context.close()


def test_home_landing_shows_the_product_story_without_login(page, live_server) -> None:
    enter_public_site(page, live_server, "home")
    expect(page.locator("#home-landing")).to_be_visible()
    expect(page.locator("#home-landing-title")).to_contain_text("你能去哪些交換學校")
    # The flat map outline (partner dots on a static SVG) is always built; it is what shows when WebGL is unavailable.
    expect(page.locator('[data-home-map="hero"] svg')).to_have_count(1)
    # Public pages never show the forum underneath another page.
    expect(page.locator("#community-hub")).to_be_hidden()


def _gaps_beside_the_rail(page, selector: str) -> tuple[float, float]:
    """Space between the rail-side edge of the content area and the page, and between the page and the window edge."""
    return page.evaluate(
        """(selector) => {
          const box = document.querySelector(selector).getBoundingClientRect();
          return [box.left - 112, innerWidth - 32 - box.right];
        }""",
        selector,
    )


@pytest.mark.parametrize("width", [1440, 1920, 2560])
def test_every_page_sits_in_the_middle_of_the_area_beside_the_rail(browser, live_server, width) -> None:
    context = browser.new_context(viewport={"width": width, "height": 900})
    page = context.new_page()
    try:
        for route, selector in (
            ("home", "#home-landing"),
            ("partners", "#partners"),
            ("guide", "#guide"),
            ("forum", "#community-hub"),
            ("feedback", "#feedback"),
        ):
            enter_public_site(page, live_server, route)
            expect(page.locator(selector)).to_be_visible()
            left, right = _gaps_beside_the_rail(page, selector)
            assert abs(left - right) <= 2, f"#{route} is off-centre at {width}px: {left:.0f}px left, {right:.0f}px right"
            # The back bar lines up with the page it belongs to.
            bar = page.locator(".page-back-bar:visible")
            if bar.count():
                bar_left, bar_right = _gaps_beside_the_rail(page, ".page-back-bar")
                assert abs(bar_left - left) <= 2, f"#{route} back bar does not line up with the page at {width}px"
    finally:
        context.close()


def test_home_has_no_decorative_guide_lines_or_sample_cards(page, live_server) -> None:
    enter_public_site(page, live_server, "home")
    expect(page.locator("#home-landing")).to_be_visible()
    assert page.locator(".pr-guide-grid").count() == 0
    borders = page.evaluate(
        "() => ['top', 'bottom'].map((side) => parseFloat(getComputedStyle(document.querySelector('.pr-supported'))[`border${side[0].toUpperCase()}${side.slice(1)}Width`]))"
    )
    assert borders == [0, 0]
    assert "示意" not in page.locator("#home-landing").inner_text()


def test_home_cards_show_the_visitors_real_schools_not_samples(browser, live_server) -> None:
    context = browser.new_context(viewport={"width": 1440, "height": 900})
    page = context.new_page()
    errors: list[str] = []
    page.on("pageerror", lambda error: errors.append(str(error)))
    page.add_init_script("window.localStorage.setItem('exchange-guide-home-school', '長庚大學')")
    try:
        enter_public_site(page, live_server, "home")
        rows = page.locator("#home-search-rows .pr-mini-row")
        expect(rows.first).to_be_visible(timeout=30_000)
        shown = [text.strip() for text in rows.locator("strong").all_inner_texts()]
        partners = page.evaluate("state.dashboard.partner_universities.map((item) => item.school_name)")
        assert shown and all(any(name in full for full in partners) for name in shown)
        # Every card says something about the visitor's school; none is left as an empty frame.
        for tile in ("#home-search-rows", "#home-tile-fit", "#home-tile-calendar", "#home-tile-documents", "#home-tile-budget"):
            assert page.locator(tile).inner_text().strip(), f"{tile} is empty"
        # Searching from the card carries the words to the explore page.
        page.locator("#home-search-input").fill("日本")
        page.locator("#home-search-form button[type=submit]").click()
        expect(page.locator("#partners")).to_be_visible()
        assert page.evaluate("new URLSearchParams(location.search).get('q')") == "日本"
        assert not errors
    finally:
        context.close()


# Headless browsers draw WebGL in software, which the globe deliberately declines; this makes one pretend to have a GPU.
PRETEND_GPU = """
for (const proto of [WebGLRenderingContext.prototype, WebGL2RenderingContext.prototype]) {
  const original = proto.getParameter;
  proto.getParameter = function (name) { return name === 0x9246 ? 'ANGLE (Test GPU)' : original.call(this, name); };
}
"""


@pytest.mark.parametrize("gpu", [False, True], ids=["as-is", "with-a-gpu"])
def test_home_hero_is_a_half_globe_that_fades_away_while_scrolling(browser, live_server, gpu) -> None:
    context = browser.new_context(viewport={"width": 1440, "height": 900})
    page = context.new_page()
    if gpu:
        page.add_init_script(PRETEND_GPU)
    try:
        enter_public_site(page, live_server, "home")
        globe = page.locator("[data-home-globe]")
        # Without WebGL, on a software renderer, or if frames come out slowly the hero keeps its flat map instead.
        page.wait_for_function(
            "() => ['ready', 'fallback'].includes(document.querySelector('[data-home-globe]').dataset.state)",
            timeout=15_000,
        )
        if not gpu:
            assert globe.get_attribute("data-state") in {"ready", "fallback"}
        if globe.get_attribute("data-state") == "ready":
            expect(globe.locator("canvas")).to_be_visible()
            # Only the top half of the sphere is drawn: the canvas is about twice as wide as it is tall.
            box = globe.bounding_box()
            assert 1.7 < box["width"] / box["height"] < 2.2
        else:
            expect(globe.locator('[data-home-map="hero"] svg')).to_be_visible()
        # The backdrop never takes clicks and is not read out; the caption link is the accessible way in.
        assert globe.evaluate("el => getComputedStyle(el).pointerEvents") == "none"
        assert globe.get_attribute("aria-hidden") == "true"
        expect(page.locator(".pr-globe-caption")).to_contain_text("合作校")
        assert float(globe.evaluate("el => el.style.getPropertyValue('--globe-progress') || '0'")) == 0

        page.evaluate("window.scrollTo({ top: 700, behavior: 'instant' })")
        page.wait_for_function(
            "() => parseFloat(document.querySelector('[data-home-globe]').style.getPropertyValue('--globe-progress')) > 0.9",
            timeout=5_000,
        )
        page.evaluate("window.scrollTo({ top: 0, behavior: 'instant' })")
        page.wait_for_function(
            "() => parseFloat(document.querySelector('[data-home-globe]').style.getPropertyValue('--globe-progress')) < 0.05",
            timeout=5_000,
        )
    finally:
        context.close()


def test_explore_sorts_and_compares_schools(page, live_server) -> None:
    enter_public_site(page, live_server, "partners")
    cards = page.locator("#partner-table .pr-school-card")
    expect(cards.first).to_be_visible(timeout=30_000)
    tab = page.locator('[data-partner-sort="quota"]')
    tab.click()
    expect(tab).to_have_attribute("aria-selected", "true")
    assert page.evaluate("state.partnerSort") == "quota"
    cards.nth(0).locator(".pr-compare").click()
    cards.nth(1).locator(".pr-compare").click()
    expect(page.locator("#partner-compare-tray")).to_be_visible()
    expect(page.locator("#partner-compare-tray [data-open-compare]")).to_be_enabled()


# A stand-in for COBE, so the globe's own pacing and its "can this machine keep up" verdict run without a real GPU.
FAKE_COBE = """
window.UniWayCobe = function (canvas, options) {
  window.__globeDraws = 0;
  return {
    toggle() {},
    destroy() {},
    render() {
      window.__globeDraws += 1;
      options.onRender({});
      const started = performance.now();
      while (performance.now() - started < (window.__globeCost || 0)) { /* a draw that takes this long */ }
    },
  };
};
"""


def _pretend_renderer(name: str) -> str:
    return (
        "for (const proto of [WebGLRenderingContext.prototype, WebGL2RenderingContext.prototype]) {"
        " const original = proto.getParameter;"
        f" proto.getParameter = function (name) {{ return name === 0x9246 ? {json.dumps(name)} : original.call(this, name); }}; }}"
    )


def _globe_page(browser, live_server, renderer: str, init: str = ""):
    context = browser.new_context(viewport={"width": 1440, "height": 900})
    page = context.new_page()
    page.add_init_script(_pretend_renderer(renderer))
    if init:
        page.add_init_script(init)
    page.route("**/static/vendor/cobe/**", lambda route: route.fulfill(body=FAKE_COBE, content_type="application/javascript"))
    enter_public_site(page, live_server, "home")
    return context, page


def test_the_globe_survives_stalls_while_the_page_boots(browser, live_server) -> None:
    # Long main-thread stalls at start-up (a page doing its first renders) must not be mistaken for a slow machine.
    stalls = "setTimeout(() => { const t = performance.now(); while (performance.now() - t < 1400); }, 300); setTimeout(() => { const t = performance.now(); while (performance.now() - t < 900); }, 2200);"
    context, page = _globe_page(browser, live_server, "ANGLE (NVIDIA, NVIDIA GeForce RTX 3060 Direct3D11)", stalls)
    try:
        page.wait_for_function("() => window.__globeDraws > 90", timeout=30_000)
        assert page.locator("[data-home-globe]").get_attribute("data-state") == "ready"
        assert page.locator("[data-home-globe]").get_attribute("data-reason") is None
    finally:
        context.close()


def test_the_globe_gives_way_to_the_flat_map_when_every_draw_is_slow(browser, live_server) -> None:
    context, page = _globe_page(browser, live_server, "ANGLE (Intel, Intel(R) UHD Graphics Direct3D11)", "window.__globeCost = 140;")
    try:
        page.wait_for_function("() => document.querySelector('[data-home-globe]').dataset.state === 'fallback'", timeout=60_000)
        assert page.locator("[data-home-globe]").get_attribute("data-reason").startswith("slow:")
        expect(page.locator('[data-home-globe] [data-home-map="hero"] svg')).to_be_visible()
    finally:
        context.close()


def test_the_globe_is_left_to_the_flat_map_on_a_software_renderer(browser, live_server) -> None:
    context, page = _globe_page(browser, live_server, "Google SwiftShader")
    try:
        page.wait_for_function("() => document.querySelector('[data-home-globe]').dataset.state === 'fallback'", timeout=30_000)
        assert page.locator("[data-home-globe]").get_attribute("data-reason").startswith("software:")
    finally:
        context.close()


def test_home_supported_schools_drift_left_and_can_be_paused(browser, live_server) -> None:
    context = browser.new_context(viewport={"width": 1440, "height": 900})
    page = context.new_page()
    try:
        enter_public_site(page, live_server, "home")
        track = page.locator("#home-supported-list")
        expect(track).to_have_class(re.compile(r"is-moving"), timeout=15_000)
        shown = page.evaluate("() => [...document.querySelectorAll('#home-supported-list > li:not([data-marquee-copy])')].map((li) => li.querySelector('strong').textContent)")
        assert shown and shown == page.evaluate("state.supportedUniversities.map((item) => item.school_name)")
        # Copies exist only to make the loop seamless and are hidden from assistive technology.
        assert page.evaluate("() => [...document.querySelectorAll('#home-supported-list > li[data-marquee-copy]')].every((li) => li.getAttribute('aria-hidden') === 'true')")
        assert page.evaluate("() => document.querySelectorAll('#home-supported-list > li[data-marquee-copy]').length") >= len(shown)

        def offset() -> float:
            return page.evaluate("() => new DOMMatrix(getComputedStyle(document.querySelector('#home-supported-list')).transform).m41")

        first = offset()
        page.wait_for_function(f"() => new DOMMatrix(getComputedStyle(document.querySelector('#home-supported-list')).transform).m41 < {first - 5}", timeout=10_000)
        toggle = page.locator("#home-supported-toggle")
        toggle.click()
        expect(toggle).to_have_attribute("aria-pressed", "true")
        assert page.evaluate("() => getComputedStyle(document.querySelector('#home-supported-list')).animationPlayState") == "paused"
        held = offset()
        page.wait_for_timeout(600)
        assert offset() == held
        toggle.click()
        expect(toggle).to_have_attribute("aria-pressed", "false")
        assert page.evaluate("() => getComputedStyle(document.querySelector('#home-supported-list')).animationPlayState") == "running"
    finally:
        context.close()


def test_home_supported_schools_stand_still_for_reduced_motion(browser, live_server) -> None:
    context = browser.new_context(viewport={"width": 1440, "height": 900}, reduced_motion="reduce")
    page = context.new_page()
    try:
        enter_public_site(page, live_server, "home")
        expect(page.locator("#home-supported-list > li").first).to_be_visible(timeout=15_000)
        assert page.evaluate("() => getComputedStyle(document.querySelector('#home-supported-list')).animationName") == "none"
        # Every school stays in view instead of sliding past.
        assert page.evaluate("() => [...document.querySelectorAll('#home-supported-list > li')].filter((li) => li.getClientRects().length).length") == len(
            page.evaluate("state.supportedUniversities")
        )
    finally:
        context.close()


def test_home_school_switcher_is_bigger_than_on_other_pages(browser, live_server) -> None:
    context = browser.new_context(viewport={"width": 1440, "height": 900})
    page = context.new_page()
    try:
        heights = {}
        for route in ("home", "partners"):
            enter_public_site(page, live_server, route)
            expect(page.locator("#school-switcher")).to_be_visible()
            heights[route] = page.locator("#school-switcher").bounding_box()["height"]
        assert heights["home"] >= 64
        assert heights["partners"] <= 58
        enter_public_site(page, live_server, "home")
        # With no school chosen yet it asks for one in words, not only with an arrow.
        expect(page.locator("body")).to_have_attribute("data-school-selected", "false")
        assert page.evaluate("() => getComputedStyle(document.querySelector('#school-switcher'), '::after').content") == '"請選擇"'
    finally:
        context.close()


def test_rail_logo_sits_on_the_rails_centre_line(page, live_server) -> None:
    page.set_viewport_size({"width": 1440, "height": 900})
    enter_public_site(page, live_server, "home")
    centres = page.evaluate(
        """() => {
          const centre = (element) => { const box = element.getBoundingClientRect(); return box.left + box.width / 2; };
          const rail = document.querySelector('#glass-navigation');
          return [centre(rail), centre(rail.querySelector('.uniway-header-brand .brand-mark')), centre(rail.querySelector('a[data-public-route]'))];
        }"""
    )
    assert abs(centres[1] - centres[0]) <= 1, f"the logo is {centres[1] - centres[0]:.1f}px off the rail's centre line"
    assert abs(centres[2] - centres[0]) <= 1


def test_application_workspace_pages_read_as_a_second_row_of_their_own(page, live_server) -> None:
    email = f"workspace-{uuid4().hex[:10]}@example.com"
    live_server.register(email)
    login_through_web(page, live_server, email)
    page.evaluate("location.hash = '#advisor'")
    tools = page.locator("#application-workspace-tools")
    expect(tools).to_have_attribute("data-sequence", "true")
    expect(tools.locator(".application-workspace-tools-label")).to_have_text("選校與確認的 3 個頁面")
    expect(tools.locator("a")).to_have_count(3)
    expect(tools.locator("a").nth(0)).to_have_attribute("aria-current", "page")
    assert [text.strip() for text in tools.locator(".application-workspace-tool-no").all_inner_texts()] == ["1", "2", "3"]
    # The numbers are decoration: the links are still named by their words alone.
    expect(page.get_by_role("link", name="候選與比較", exact=True)).to_be_visible()
    # A bordered track of its own, not loose text under the stage buttons.
    assert page.evaluate("() => parseFloat(getComputedStyle(document.querySelector('#application-workspace-tools')).borderTopWidth)") >= 1
    page.evaluate("location.hash = '#overview'")
    expect(tools.locator(".application-workspace-tools-label")).to_have_text("準備與時程的 5 個頁面")
    expect(tools.locator("a")).to_have_count(5)


def _card_names(page) -> list[str]:
    return page.evaluate("() => [...document.querySelectorAll('#partner-table .pr-school-card')].map((card) => card.dataset.schoolCard)")


def test_explore_language_and_term_dropdowns_change_the_school_list(page, live_server) -> None:
    enter_public_site(page, live_server, "partners")
    expect(page.locator("#partner-table .pr-school-card").first).to_be_visible(timeout=30_000)
    # Three schools that say something about tests and intakes, the rest say nothing.
    names = page.evaluate(
        """() => {
          const list = state.dashboard.partner_universities;
          list[0].eligibility = 'IELTS 6.0 overall';
          list[0].application_deadline = '秋季班：4月30日 春季班：10月30日';
          list[1].eligibility = 'JLPT N2';
          list[1].application_deadline = '春季班：10月30日';
          list[2].eligibility = 'TOEIC 700 或 TOEFL iBT 79';
          list[2].application_deadline = '秋季班：4月30日';
          renderPartnerTable();
          return list.slice(0, 3).map((item) => item.school_name);
        }"""
    )
    total = page.evaluate("state.dashboard.partner_universities.length")
    count = page.locator("#partner-result-count")
    expect(count).to_contain_text(f"共 {total} 所")

    # A test alone, with no score: schools that list only other tests drop out, and the one that lists it comes first.
    page.locator("#partner-test-tile").select_option("jlpt")
    expect(count).to_contain_text(f"共 {total - 2} 所")
    expect(count).to_contain_text("2 所不符已隱藏")
    assert _card_names(page)[0] == names[1]
    assert names[0] not in _card_names(page) and names[2] not in _card_names(page)
    expect(page.locator("#partner-applied")).to_contain_text("語言檢定：日檢 JLPT")
    expect(page.locator('[data-partner-sort="match"] span')).to_contain_text("1 間符合所選條件")

    page.locator("#partner-test-tile").select_option("ielts")
    expect(count).to_contain_text(f"共 {total - 2} 所")
    assert _card_names(page)[0] == names[0]
    assert names[1] not in _card_names(page)

    # A term: the schools whose schedule names only the other season drop out.
    page.locator("#partner-test-tile").select_option("")
    page.locator("#partner-term-tile").select_option("fall")
    expect(count).to_contain_text(f"共 {total - 1} 所")
    assert names[1] not in _card_names(page)
    assert _card_names(page)[:2] == [names[0], names[2]]
    expect(page.locator("#partner-applied")).to_contain_text("出發學期：秋季／上學期")

    # Clearing both brings every school back.
    page.locator("#partner-term-tile").select_option("")
    expect(count).not_to_contain_text("已隱藏")
    expect(count).to_contain_text(f"共 {total} 所")


def test_guide_has_a_table_of_contents_and_deep_links(page, live_server) -> None:
    enter_public_site(page, live_server, "guide")
    expect(page.locator("#guide-toc a").first).to_be_visible()
    assert page.locator("#guide-toc a").count() >= 10
    page.goto(f"{live_server.base_url}/#guide=eligibility")
    expect(page.locator("#guide-article h1")).to_contain_text("確認資格與排志願")
    expect(page.locator("#guide-outline")).to_be_visible()
    # A guide is public reading: it never asks for an account.
    expect(page.locator("#auth-dialog")).to_be_hidden()


def test_forum_modes_filter_stories_and_questions(page, live_server) -> None:
    enter_public_site(page, live_server, "forum")
    expect(page.locator("#community-hub")).to_be_visible()
    expect(page.locator("#community-hub-title")).to_have_text("學長姐心得")
    for mode in ("question", "boards", "story"):
        button = page.locator(f'button[data-forum-mode="{mode}"]')
        button.click()
        expect(page.locator("#community-hub")).to_have_attribute("data-forum-mode", mode)
        expect(button).to_have_attribute("aria-pressed", "true")


def test_tracker_lists_tasks_and_switches_views(page, live_server) -> None:
    email = f"tracker-{uuid4().hex[:10]}@example.com"
    live_server.register(email)
    login_through_web(page, live_server, email)
    page.evaluate("location.hash = '#overview'")
    expect(page.locator("#my-applications")).to_be_visible()
    expect(page.locator("#tracker-title")).to_have_text("我的申請")
    for view in ("board", "timeline", "list"):
        page.locator(f'[data-tracker-view="{view}"]').click()
        expect(page.locator(f'[data-tracker-view="{view}"]')).to_have_attribute("aria-pressed", "true")


def test_profile_page_replaces_the_dialog_and_saves_the_same_fields(page, live_server) -> None:
    email = f"profile-{uuid4().hex[:10]}@example.com"
    live_server.register(email)
    login_through_web(page, live_server, email)
    page.locator("#account-button:visible, #global-mobile-account-button:visible, #mobile-account-button:visible").first.click()
    expect(page.locator("#profile")).to_be_visible()
    assert page.evaluate("location.hash") == "#profile"
    assert page.title() == "個人中心 | UniWay"
    expect(page.locator("#profile-dialog")).to_have_count(0)

    # Target countries are chips; the hidden field keeps the form's existing 、-separated format.
    page.locator("#profile-country-add").click()
    page.locator("#profile-country-input").fill("日本")
    page.keyboard.press("Enter")
    page.locator("#profile-country-input").fill("韓國")
    page.keyboard.press("Enter")
    expect(page.locator("#profile-country-chips .pr-chip-item")).to_have_count(2)
    page.locator('[data-remove-country="韓國"]').click()
    expect(page.locator('#profile-form [name="target_countries"]')).to_have_value("日本")

    page.locator('#profile-form [name="email_notifications"]').check()
    page.locator('#profile-form [name="application_stage"]').select_option("documents")
    with page.expect_response(lambda response: response.url.endswith("/auth/me") and response.request.method == "PATCH") as saved:
        page.locator('#profile-form button[type="submit"]').click()
    payload = json.loads(saved.value.request.post_data)
    assert payload["target_countries"] == ["日本"]
    assert payload["application_stage"] == "documents"
    assert payload["notification_preferences"]["email_enabled"] is True
    assert payload["notification_preferences"]["push_enabled"] is False
    expect(page.locator("#profile-form .form-status")).to_have_text("已儲存")
    assert page.evaluate("location.hash") == "#profile"

    page.reload()
    expect(page.locator("#profile")).to_be_visible(timeout=30_000)
    expect(page.locator("#profile-country-chips")).to_contain_text("日本")
    expect(page.locator('#profile-form [name="application_stage"]')).to_have_value("documents")

    page.locator("#logout-button").click()
    expect(page.locator("#profile")).to_be_hidden(timeout=10_000)
    assert page.evaluate("location.hash") == "#home"


def test_profile_appearance_choice_includes_following_the_system(browser, live_server) -> None:
    email = f"theme-{uuid4().hex[:10]}@example.com"
    live_server.register(email)
    context = browser.new_context(viewport={"width": 1280, "height": 900}, color_scheme="dark")
    page = context.new_page()
    try:
        login_through_web(page, live_server, email)
        page.evaluate("location.hash = '#profile'")
        expect(page.locator("#profile")).to_be_visible()
        html = page.locator("html")
        page.locator('[data-theme-choice="light"]').click()
        expect(html).to_have_attribute("data-theme", "light")
        page.locator('[data-theme-choice="system"]').click()
        expect(html).to_have_attribute("data-theme", "dark")
        assert page.evaluate("window.localStorage.getItem('exchange-guide-theme')") == "system"
        expect(page.locator('[data-theme-choice="system"]')).to_have_attribute("aria-checked", "true")
        # While "system" is chosen the page follows the device when it changes.
        page.emulate_media(color_scheme="light")
        expect(html).to_have_attribute("data-theme", "light")
        # The rail's quick toggle still flips between the two explicit themes.
        page.locator("#theme-toggle").click()
        expect(html).to_have_attribute("data-theme", "dark")
        assert page.evaluate("window.localStorage.getItem('exchange-guide-theme')") == "dark"
    finally:
        context.close()


def test_profile_deep_link_asks_visitors_to_sign_in_and_stays_off_the_page(page, live_server) -> None:
    enter_public_site(page, live_server, "profile")
    expect(page.locator("#auth-dialog")).to_be_visible(timeout=10_000)
    expect(page.locator("#profile")).to_be_hidden()
    assert page.evaluate("location.hash") == "#home"
