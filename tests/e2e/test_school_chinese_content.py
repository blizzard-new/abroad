"""The source remains usable when translations are available or unavailable."""
import json
from urllib.parse import quote

import pytest
from playwright.sync_api import expect

from .test_glass_theme import verified_login
from .conftest import enter_public_site


@pytest.mark.parametrize("width", [390, 1754])
def test_school_life_uses_offline_chinese_and_retains_original(page, live_server, width):
    page.set_viewport_size({"width": width, "height": 956})
    url = "https://www.meiji.ac.jp/cip/english/admissions/finding_accommodation_in_tokyo.html"
    original = "Rent in central Tokyo is high, so many students commute from outside the city."
    payload = {"school_name": "明治大學 Meiji University", "research_status": "ready", "can_refresh": False,
        "location_note": "僅適用來源提及校區。", "categories": [{"theme": "housing", "evidence": [
            {"theme": "housing", "kind": "official", "text": original, "original_text": original,
             "translation_status": "pending", "scope": "住宿資訊", "sources": [{"title": "住宿資訊", "url": url}]}],
            "next_step": "核對住宿資格。", "search_url": "https://www.meiji.ac.jp/"}], "research_notes": []}
    page.route("**/school-life-context?**", lambda route: route.fulfill(content_type="application/json", body=json.dumps(payload)))
    errors = []
    page.on("pageerror", lambda error: errors.append(str(error)))
    verified_login(page, live_server)
    enter_public_site(page, live_server, "partners")
    page.locator('[data-partner-view="list"]').click()
    page.locator('#partner-search').fill("Meiji")
    if width < 700:
        page.locator("#partner-table .partner-card > summary").first.click()
    page.locator("#partner-table .school-detail-trigger:visible").first.click()
    page.get_by_role("tab", name="生活情報", exact=True).click()
    evidence = page.locator('.life-evidence-item').filter(has_text="東京市中心租金較高").first
    expect(evidence.locator(".life-evidence-text")).to_have_text("東京市中心租金較高，因此許多學生從市區以外通勤。")
    expect(evidence.locator(".life-evidence-source p")).not_to_be_visible()
    evidence.get_by_text("資料來源", exact=True).click()
    expect(evidence.locator(".life-evidence-source p")).to_have_text(original)
    expect(evidence.get_by_role("link")).to_have_attribute("href", url)
    assert "中文翻譯待補" not in page.locator("#life-content").inner_text()
    assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
    assert not errors
