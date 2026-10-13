"""Keep programme years and source conflicts visible in the public NTU summary."""
import os
from pathlib import Path

import pytest
from playwright.sync_api import expect

from .conftest import enter_public_site, open_navigation
from .test_open_catalog import wait_until


@pytest.mark.parametrize("width", [390, 1440])
@pytest.mark.parametrize("school,markers", [
    ("東京外國語大學", ["2027/3/15", "Spring2027", "AY2026", "Early February2027"]),
    ("關西學院大學", ["2027春", "2026/11/15", "2026–27", "Tentative"]),
])
def test_new_reference_scope_is_readable_without_approving_home_selection(
    page, live_server, width, school, markers,
):
    page.set_viewport_size({"width": width, "height": 956})
    page.emulate_media(reduced_motion="reduce")
    errors = []
    page.on("pageerror", lambda error: errors.append(str(error)))
    enter_public_site(page, live_server, "partners")
    open_navigation(page)
    page.locator("#school-switcher").click()
    page.locator('[data-home-school="國立臺灣大學"]').click()
    if width < 700 and page.locator("#glass-menu-toggle").get_attribute("aria-expanded") == "true":
        page.locator("#glass-menu-toggle").click()
    wait_until(page, "state.dashboard?.school_name === '國立臺灣大學'")
    page.locator('[data-partner-view="list"]').click()
    page.locator("#partner-search").fill(school)
    expect(page.locator("#partner-table")).to_contain_text("本期名額待核實")
    if width < 700:
        page.locator("#partner-table .partner-card > summary").first.click()
    page.locator("#partner-table .school-detail-trigger:visible").first.click()
    detail = page.locator("#school-detail-view")
    expect(detail).to_be_visible()
    for marker in markers:
        expect(detail.locator(".partner-student-summary")).to_contain_text(marker)
        point = detail.locator(".partner-student-summary li").filter(has_text=marker).last
        point.scroll_into_view_if_needed()
        expect(point).to_be_visible()
    expect(detail.locator(".partner-student-summary")).to_contain_text("不能視為116-1最終甄選資格")
    assert page.evaluate(
        "(name) => state.dashboard.partner_universities.find(p => p.school_name === name).quota",
        school,
    ) is None
    assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
    assert not errors
    destination = Path(os.environ.get("NTU_REFERENCE_SCREENSHOTS", "/tmp/ntu-reference-browser"))
    destination.mkdir(parents=True, exist_ok=True)
    page.screenshot(path=str(destination / f"{school}-{width}.png"))
