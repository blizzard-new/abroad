"""Read real bundled UI summaries and exact links; no injected policy data/state."""

import json
import re
from urllib.parse import quote

import pytest
from playwright.sync_api import expect

from exchange_info.ccu_sources import BUNDLE, HOME
from exchange_info.ccu_student_view import fetch_ccu_partner_universities

from .conftest import enter_public_site
from .test_ccu_candidate_acceptance import capture, choose_home, record_errors


@pytest.mark.parametrize("width", [390, 1440])
@pytest.mark.parametrize("source_page,key,sid,claim,pdf_page,medium", [
    (119, "application_forms", "p119-r27-form-metadata-normal-tls", "清單列48項", 5, "公開題目API原文"),
    (83, "academic_calendar", "p83-r27-calendar-image-normal-tls", "2027-02-01至04-24", 2, "官方校曆影像原文"),
])
def test_composite_claims_display_independent_source_dates_and_links(page, live_server, width, source_page, key, sid, claim, pdf_page, medium):
    page.set_viewport_size({"width": width, "height": 956})
    page.emulate_media(reduced_motion="reduce")
    errors = record_errors(page)
    partner = next(p for p in fetch_ccu_partner_universities() if p.source_pages[0] == source_page)
    fresh = json.loads((BUNDLE / "overseas_sources" / (sid + ".json")).read_text())
    old = next(e for e in partner.partner_exchange_details[key].evidence if e.source_url != fresh["source_url"])
    enter_public_site(page, live_server, "partners")
    choose_home(page, HOME)
    page.evaluate("hash => {location.hash=hash}", "#school=" + quote(partner.school_name))
    field = page.locator(f'#detail-overview [data-ccu-field="{key}"]')
    expect(field).to_be_visible(timeout=30_000)
    field.locator("> summary").click()
    expect(field).to_contain_text(claim)
    links = field.locator("a").all()
    normal = next(link for link in links if link.get_attribute("href") == fresh["source_url"])
    expect(normal).not_to_contain_text("PDF第")
    expect(normal.locator("xpath=following-sibling::p[1]")).to_contain_text("查核2026-10-09")
    original = next(link for link in links if link.get_attribute("href") == old.source_url.split("#")[0] + f"#page={pdf_page}")
    expect(original).to_contain_text(f"PDF第{pdf_page}頁")
    expect(original.locator("xpath=following-sibling::p[1]")).to_contain_text("查核2026-10-08")
    page.locator("#detail-tab-application").click()
    content = page.locator("#workflow-content")
    expect(content.locator("details.workflow-step")).not_to_have_count(0, timeout=30_000)
    step = content.locator("details.workflow-step").filter(has_text=claim)
    expect(step).to_have_count(1)
    step.locator("> summary").click()
    label = "合作校申請表取得方式" if source_page == 119 else "合作校校曆及考試"
    detail = step.locator("li").filter(has_text=re.compile("^" + label + " ·"))
    expect(detail).to_have_count(1)
    expect(detail).to_contain_text(f"PDF第{pdf_page}頁；查核2026-10-08")
    expect(detail).to_contain_text(medium + "；查核2026-10-09")
    source = next(link for link in content.locator(".workflow-sources a").all()
                  if link.get_attribute("href") == fresh["source_url"])
    expect(source).to_contain_text(medium)
    expect(source).to_contain_text("查核2026-10-09")
    if source_page == 119:
        document = step.locator("li").filter(has_text="線上學生申請 · 階段")
        expect(document).to_contain_text("PDF第5頁；查核2026-10-08")
        expect(document).to_contain_text("公開題目API原文；查核2026-10-09")
    capture(page, f"composite-source-{source_page}", width)
    assert not errors
