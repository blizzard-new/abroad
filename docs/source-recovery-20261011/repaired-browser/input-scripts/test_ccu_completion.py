"""Real CCU reference-school screens, licensed image requests and mobile layout."""
import json
import os
from pathlib import Path
from urllib.parse import quote

import pytest
from playwright.sync_api import expect

from exchange_info.ccu_student_view import fetch_ccu_partner_universities

HOME = "國立中正大學"


@pytest.mark.parametrize("width", [390, 1440])
def test_closed_reference_school_shows_separate_current_host_tracks_and_credited_campus(page, live_server, width):
    partner = next(p for p in fetch_ccu_partner_universities() if p.source_pages[0] == 81)
    page.set_viewport_size({"width": width, "height": 956})
    page.emulate_media(reduced_motion="reduce")
    errors = []
    page.on("pageerror", lambda error: errors.append(str(error)))
    page.add_init_script("localStorage.setItem('exchange-guide-home-school','國立中正大學')")
    page.goto(live_server.base_url + "/?school=" + quote(HOME) + "#school=" + quote(partner.school_name))
    attribution = page.locator("#detail-overview .ccu-campus-attribution")
    expect(attribution).to_be_visible(timeout=30_000)
    expect(attribution).to_contain_text("Patrick")
    expect(attribution).to_contain_text("CC BY-SA 4.0")
    expect(attribution).to_contain_text("Loyola")
    expect(attribution.locator("p").first).not_to_contain_text("Grade School")
    assert page.request.get(live_server.base_url + partner.image_url).status == 200
    assert page.locator("#school-detail-photo img").get_attribute("src").endswith(partner.image_url)
    reference = page.locator("#detail-overview .ccu-reference-host")
    expect(reference).to_contain_text("中正本期未開放")
    expect(reference.locator("[data-ccu-reference-field]")).to_have_count(17)
    deadline = reference.locator('[data-ccu-reference-field="application_deadline"]')
    deadline.locator("> summary").click()
    expect(deadline).to_contain_text("本科2026-09-30")
    expect(deadline).to_contain_text("研究所2026-09-01")
    language = reference.locator('[data-ccu-reference-field="language"]')
    language.locator("> summary").click()
    expect(language).to_contain_text("iBT79")
    expect(language).to_contain_text("iBT80")
    assert len({a.get_attribute("href") for a in deadline.locator("a").all()}) >= 2
    assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
    output = Path(os.environ.get("VISUAL_EVIDENCE_DIR", "output/ccu-completion-browser"))
    output.mkdir(exist_ok=True)
    deadline.scroll_into_view_if_needed()
    page.screenshot(path=str(output / f"ateneo-reference-{width}.png"))
    assert not errors


@pytest.mark.parametrize("width", [390, 1440])
def test_current_partner_has_correct_school_of_engineering_photo_and_primary_coordinate(page, live_server, width):
    partner = next(p for p in fetch_ccu_partner_universities() if p.source_pages[0] == 103)
    page.set_viewport_size({"width": width, "height": 956})
    page.emulate_media(reduced_motion="reduce")
    page.add_init_script("localStorage.setItem('exchange-guide-home-school','國立中正大學')")
    page.goto(live_server.base_url + "/?school=" + quote(HOME) + "#school=" + quote(partner.school_name))
    attribution = page.locator("#detail-overview .ccu-campus-attribution")
    expect(attribution).to_be_visible(timeout=30_000)
    expect(attribution).to_contain_text("School of Engineering")
    expect(attribution).to_contain_text("Technikumstrasse 9")
    expect(attribution).to_contain_text("CC BY-SA 4.0")
    assert partner.location.latitude == 47.4972243
    assert json.loads(partner.reference_data["ccu_campus_assets"])["photo"]["artist"]
    assert page.request.get(live_server.base_url + partner.image_url).status == 200
    assert page.locator("#school-detail-photo img").get_attribute("src").endswith(partner.image_url)
    expect(page.locator("#detail-overview .ccu-receiving-school-details [data-ccu-field]")).to_have_count(17)
    assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
