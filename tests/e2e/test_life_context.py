import json
from urllib.parse import quote

from playwright.sync_api import expect

from exchange_info.life_context import LifeEvidence, LifeSource, _inference
from .conftest import enter_public_site


MEIJI = "明治大學 Meiji University"


def test_life_fallback_retains_evidence_on_refresh_failure(page, live_server):
    calls = []
    row = LifeEvidence(theme="food", kind="official", text="校內設有學生餐廳。", original_text="There is a student cafeteria on campus.", translation_status="machine",
                       sources=[LifeSource(title="Official dining", url="https://www.meiji.ac.jp/dining")])
    payload = {"school_name": MEIJI, "location_note": "校級代表座標，未必是你的交換校區。",
               "research_status": "not_collected", "checked_at": None, "can_refresh": True,
               "categories": [{"theme": "food", "evidence": [row.model_dump(mode="json")],
                 "inference": _inference("food", [row]).model_dump(), "next_step": "核對實際校區。",
                 "search_url": "https://www.google.com/search?q=Meiji+food"},
                 {"theme": "housing", "evidence": [row.model_copy(update={"theme": "housing", "text": "Dorm rooms are not guaranteed.", "original_text": "Dorm rooms are not guaranteed.", "translation_status": "pending"}).model_dump(mode="json")],
                  "inference": None, "next_step": "核對住宿資格。", "search_url": "https://www.google.com/search?q=Meiji+housing"}], "research_notes": []}
    def context_route(route):
        calls.append(route.request.method)
        if route.request.method == "POST":
            route.fulfill(status=503, content_type="application/json", body='{"detail":"unavailable"}')
        else:
            route.fulfill(content_type="application/json", body=json.dumps(payload))
    page.route("**/school-life-context**", context_route)
    errors = []
    page.on("pageerror", lambda error: errors.append(str(error)))
    enter_public_site(page, live_server, "school=" + quote(MEIJI))
    page.get_by_role("tab", name="生活情報", exact=True).click()
    food = page.locator('[data-life-theme="food"]')
    expect(food.get_by_text("校內設有學生餐廳。", exact=True)).to_be_visible()
    expect(food.get_by_text("There is a student cafeteria on campus.", exact=True)).not_to_be_visible()
    expect(food).to_contain_text("AI 推論")
    food.get_by_text("原文與來源", exact=True).click()
    expect(food.get_by_text("There is a student cafeteria on campus.", exact=True)).to_be_visible()
    expect(page.locator("#life-research-status")).to_contain_text("已保留可用資料")
    housing = page.locator('[data-life-theme="housing"]')
    expect(housing.get_by_text("中文翻譯尚未完成，可查看原文。", exact=True)).to_be_visible()
    expect(housing.get_by_text("Dorm rooms are not guaranteed.", exact=True)).not_to_be_visible()
    food.get_by_text("推論依據", exact=True).click()
    expect(food.get_by_role("link", name="推論依據 1")).to_have_attribute("href", "https://www.meiji.ac.jp/dining")
    assert calls == ["GET", "POST"]
    page.get_by_role("tab", name="快速了解", exact=True).click()
    page.get_by_role("tab", name="生活情報", exact=True).click()
    assert calls == ["GET", "POST"]
    page.set_viewport_size({"width": 393, "height": 852})
    expect(food).to_be_visible()
    assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
    assert not errors
