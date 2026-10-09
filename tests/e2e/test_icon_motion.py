from __future__ import annotations

from playwright.sync_api import Browser, Page, expect

from .conftest import LiveServer, enter_public_site


def _wait_for_icon_motion(page: Page) -> None:
    page.wait_for_function(
        """
        () => window.IconMotion
          && document.documentElement.dataset.iconMotionEngine === 'morphicons@1.7.0'
          && document.querySelectorAll('svg.lucide').length > 0
          && document.querySelectorAll('svg.lucide').length
             === document.querySelectorAll('svg.lucide.icon-motion-ready').length
        """,
        timeout=15_000,
    )


def test_all_rendered_icons_are_enhanced_and_theme_uses_true_path_morph(
    page: Page,
    live_server: LiveServer,
) -> None:
    enter_public_site(page, live_server)
    _wait_for_icon_motion(page)

    icons = page.locator("svg.lucide")
    assert icons.count() > 100
    expect(page.locator("i[data-lucide]")).to_have_count(0)

    theme = page.locator("#theme-toggle")
    path = theme.locator("svg path")
    start = path.get_attribute("d")
    # Observe real SVG mutations, including intermediate paths, instead of
    # assuming a busy runner presents a frame exactly 35 ms after the click.
    theme.evaluate("""el => {
      window.__themePaths = [el.querySelector('svg path').getAttribute('d')];
      window.__themeObserver = new MutationObserver(() => {
        const d = el.querySelector('svg path')?.getAttribute('d');
        if (d && d !== __themePaths.at(-1)) __themePaths.push(d);
      });
      __themeObserver.observe(el, {subtree:true, childList:true, attributes:true, attributeFilter:['d']});
    }""")
    theme.click()
    page.wait_for_function("() => new Set(__themePaths).size >= 3")
    page.wait_for_timeout(650)
    end = theme.locator("svg path").get_attribute("d")
    paths = page.evaluate("() => { __themeObserver.disconnect(); return __themePaths; }")
    middle = next(d for d in paths if d not in {start, end})

    assert theme.locator("svg").get_attribute("data-icon-motion-engine") == "morphicons"
    assert start != middle
    assert middle != end
    assert start != end


def test_reduced_motion_switches_morphicons_to_an_immediate_final_state(
    browser: Browser,
    live_server: LiveServer,
) -> None:
    context = browser.new_context(
        viewport={"width": 1280, "height": 900},
        reduced_motion="reduce",
    )
    page = context.new_page()
    try:
        page.add_init_script(
            "window.sessionStorage.setItem('exchange-guide-browse-first', '1')"
        )
        page.goto(f"{live_server.base_url}/#home")
        page.locator("#school-onboarding").wait_for(state="hidden")
        page.wait_for_load_state("networkidle", timeout=60_000)
        _wait_for_icon_motion(page)

        theme = page.locator("#theme-toggle")
        path = theme.locator("svg path")
        start = path.get_attribute("d")
        theme.click()
        page.wait_for_timeout(1)
        immediate = theme.locator("svg path").get_attribute("d")
        page.wait_for_timeout(80)
        later = theme.locator("svg path").get_attribute("d")
        computed = theme.locator("svg").evaluate(
            """icon => ({
                animationName: getComputedStyle(icon).animationName,
                transitionDuration: getComputedStyle(icon).transitionDuration,
            })"""
        )

        assert start != immediate
        assert immediate == later
        assert computed["animationName"] == "none"
        assert computed["transitionDuration"] in {"0s", "1e-05s", "0.00001s"}
    finally:
        context.close()
