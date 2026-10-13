"""Real Chromium + real MapLibre; failure/scale inputs are isolated test fixtures."""
from __future__ import annotations

import json
from pathlib import Path
from urllib.parse import urlencode

import pytest
from playwright.sync_api import Page, expect

from .conftest import LiveServer

LINCOLN = "林肯大學 Lincoln University"
MEIJI = "明治大學 Meiji University"
ARTIFACTS = Path(__file__).resolve().parents[2] / "output/partner-globe"

# Capture the real engine solely inside the browser test context, for assertions
# about visible clusters/camera; production exposes no debug map globals.
INSTRUMENT = """(() => {
  let library;
  Object.defineProperty(window, 'maplibregl', {configurable:true,get:()=>library,set:value=>{
    let CapturedMap;
    Object.defineProperty(value,'Map',{configurable:true,get:()=>CapturedMap,set:Original=>{
      CapturedMap=class extends Original {constructor(options){super(options);window.__testedMap=this;}};
    }});
    library=value;
  }});
  localStorage.setItem('exchange-guide-home-school','長庚大學');
  sessionStorage.setItem('exchange-guide-browse-first','1');
})();"""


def open_partners(page: Page, live_server: LiveServer, query=None):
    page.add_init_script(INSTRUMENT)
    page.goto(f"{live_server.base_url}/?{urlencode(query or {'view':'map'})}#partners")
    expect(page.locator("#partner-table")).to_have_attribute("aria-busy", "false", timeout=30000)


def ready(page: Page):
    try:
        expect(page.locator("#partner-globe")).to_have_attribute("data-ready", "true", timeout=30000)
        page.wait_for_function("() => window.__testedMap && !window.__testedMap.isMoving() && window.__testedMap.isSourceLoaded('schools')")
    except Exception:
        ARTIFACTS.mkdir(parents=True, exist_ok=True)
        page.screenshot(path=str(ARTIFACTS / "test-failure.png"), full_page=True)
        print("Map status:", page.locator("#partner-map-status").inner_text())
        print("Map diagnostics:", page.evaluate("({captured:!!window.__testedMap, engine:!!window.maplibregl, ready:document.querySelector('#partner-globe').dataset.ready})"))
        raise


def map_data(page: Page):
    return page.evaluate("async () => await window.__testedMap.getSource('schools').getData()")


def inject_dashboard(page: Page, transform):
    def handler(route):
        response = route.fetch()
        payload = response.json()
        transform(payload)
        route.fulfill(response=response, json=payload)
    page.route("**/student-dashboard?*", handler)


def test_list_lazy_load_and_roundtrip_filters(page, live_server):
    requests = []
    page.on("request", lambda r: requests.append(r.url))
    open_partners(page, live_server, {"view": "list"})
    expect(page.locator("#partner-table")).to_be_visible()
    assert not any("maplibre" in url or "partner-map.js" in url or "countries.geojson" in url for url in requests)
    page.locator("#partner-search").fill("Lincoln")
    page.locator("#country-filter").select_option("紐西蘭")
    before = sum("/student-dashboard?" in url for url in requests)
    page.locator('[data-partner-view="map"]').click()
    ready(page)
    assert [f["properties"]["name"] for f in map_data(page)["features"]] == [LINCOLN]
    expect(page.locator("#partner-table")).to_be_hidden()
    page.locator('[data-partner-view="list"]').click()
    expect(page.locator("#partner-search")).to_have_value("Lincoln")
    expect(page.locator("#country-filter")).to_have_value("紐西蘭")
    expect(page.locator("#partner-table tbody tr")).to_have_count(1)
    assert sum("/student-dashboard?" in url for url in requests) == before
    page.go_back()
    expect(page.locator('[data-partner-view="map"]')).to_have_attribute("aria-pressed", "true")


@pytest.mark.parametrize("size", [(1440, 1000), (834, 1112), (393, 852)])
def test_responsive_marker_preview_detail_and_back(page, live_server, size):
    page.set_viewport_size({"width": size[0], "height": size[1]})
    page.emulate_media(reduced_motion="reduce")
    errors = []
    page.on("pageerror", lambda error: errors.append(str(error)))
    open_partners(page, live_server, {"view": "map", "country": "紐西蘭"})
    ready(page)
    assert map_data(page)["features"][0]["properties"]["name"] == LINCOLN
    # Click the actual rendered marker, not a mock callback.
    page.locator("#partner-globe").scroll_into_view_if_needed()
    pos = page.evaluate("""() => {const map=window.__testedMap; const f=map.queryRenderedFeatures({layers:['school-points']})[0]; const p=map.project(f.geometry.coordinates); return {x:p.x,y:p.y};}""")
    page.locator("#partner-globe canvas").click(position=pos)
    expect(page.locator("#partner-map-preview")).to_be_visible()
    expect(page.locator("#partner-map-preview h4")).to_have_text(LINCOLN)
    page.wait_for_function("() => !window.__testedMap.isMoving()")
    original_center = page.evaluate("window.__testedMap.getCenter().toArray()")
    stage = page.locator(".partner-map-stage").bounding_box()
    card = page.locator("#partner-map-preview").bounding_box()
    if size[0] < 700:
        assert abs(card["y"] + card["height"] - stage["y"] - stage["height"]) < 3
        assert card["height"] < stage["height"] * .6
        marker_y = page.evaluate("""() => { const map=window.__testedMap;const f=map.queryRenderedFeatures({layers:['selected-school']})[0];return map.project(f.geometry.coordinates).y; }""")
        assert stage["y"] + marker_y < card["y"] - 8
    assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
    ARTIFACTS.mkdir(parents=True, exist_ok=True)
    page.screenshot(path=str(ARTIFACTS / f"preview-{size[0]}.png"), full_page=True)
    page.locator("#partner-map-preview .favorite-toggle").click()
    expect(page.locator("#partner-map-preview .favorite-toggle")).to_have_attribute("aria-pressed", "true")
    expect(page.locator("#partner-map-preview .favorite-toggle")).to_be_focused()
    page.locator("#partner-map-preview .school-detail-trigger").click()
    expect(page.locator("#school-detail-title")).to_have_text(LINCOLN)
    assert "#school=" in page.url
    page.go_back()
    expect(page.locator("#partner-map-panel")).to_be_visible()
    expect(page.locator("#country-filter")).to_have_value("紐西蘭")
    expect(page.locator('[data-partner-view="map"]')).to_have_attribute("aria-pressed", "true")
    page.locator("[data-close-map-preview]").click()
    assert page.evaluate("window.__testedMap.getCenter().toArray()") == original_center
    assert not errors


def test_refresh_direct_url_and_missing_empty_states(page, live_server):
    open_partners(page, live_server, {"view": "map", "q": "Lincoln", "country": "紐西蘭"})
    ready(page)
    page.reload()
    ready(page)
    expect(page.locator("#partner-search")).to_have_value("Lincoln")
    expect(page.locator("#country-filter")).to_have_value("紐西蘭")
    page.locator("#partner-search").fill("no-such-university-9837")
    expect(page.locator("#partner-map-status")).to_contain_text("沒有符合條件")
    page.locator("#clear-partner-filters").click()
    expect(page.locator("#partner-map-status")).to_be_hidden()
    expect(page.locator("#partner-map-missing")).to_contain_text("座標待確認")


def test_missing_coordinates_do_not_create_false_points(page, live_server):
    inject_dashboard(page, lambda payload: [p.update(location=None) for p in payload["partner_universities"]])
    open_partners(page, live_server)
    ready(page)
    expect(page.locator("#partner-map-status")).to_contain_text("位置還在確認")
    assert map_data(page)["features"] == []
    page.get_by_role("button", name="返回列表", exact=True).click()
    expect(page.locator("#partner-table tbody tr").first).to_be_visible()


def test_empty_catalog(page, live_server):
    inject_dashboard(page, lambda payload: payload.update(partner_universities=[]))
    open_partners(page, live_server)
    ready(page)
    expect(page.locator("#partner-map-status")).to_contain_text("沒有符合條件")


@pytest.mark.parametrize("resource", ["api", "module", "engine", "worker", "basemap"])
def test_failures_are_recoverable_without_losing_filters(page, live_server, resource):
    patterns = {
        "api": "**/student-dashboard?*", "module": "**/partner-map.js?*",
        "engine": "**/maplibre-gl-csp.js", "worker": "**/maplibre-gl-csp-worker.js", "basemap": "**/countries.geojson",
    }
    pattern = patterns[resource]
    page.route(pattern, lambda route: route.fulfill(status=503, content_type="text/plain", body="Isolated test failure"))
    if resource == "api":
        page.add_init_script(INSTRUMENT)
        page.goto(f"{live_server.base_url}/?view=map&q=Lincoln#partners")
    else:
        open_partners(page, live_server, {"view": "map", "q": "Lincoln"})
    expect(page.locator("#partner-map-status")).to_contain_text("無法", timeout=30000)
    expect(page.locator("#partner-search")).to_have_value("Lincoln")
    page.unroute(pattern)
    page.locator("#partner-map-status").get_by_role("button", name="重新", exact=False).click()
    ready(page)
    expect(page.locator("#partner-map-status")).to_be_hidden()
    assert len(map_data(page)["features"]) == 1


def test_thousand_points_cluster_expand_and_keyboard(page, live_server):
    def thousand(payload):
        base = next(p for p in payload["partner_universities"] if p["school_name"] == LINCOLN)
        payload["partner_universities"] = [dict(base, school_name=f"Isolated cluster fixture {i}", country="日本", location=dict(base["location"], latitude=35.6+(i%25)*.006, longitude=139.6+(i//25)*.006)) for i in range(1000)]
    inject_dashboard(page, thousand)
    open_partners(page, live_server, {"view": "map", "country": "日本"})
    ready(page)
    assert len(map_data(page)["features"]) == 1000
    page.wait_for_function("() => window.__testedMap.queryRenderedFeatures({layers:['clusters']}).length > 0")
    before = page.evaluate("window.__testedMap.getZoom()")
    page.locator("#partner-globe").scroll_into_view_if_needed()
    pos = page.evaluate("""() => {const m=window.__testedMap;const f=m.queryRenderedFeatures({layers:['clusters']})[0];const p=m.project(f.geometry.coordinates);return {x:p.x,y:p.y}}""")
    page.locator("#partner-globe canvas").click(position=pos)
    page.wait_for_function("old => !window.__testedMap.isMoving() && window.__testedMap.getZoom()>old", arg=before)
    expect(page.locator("#map-connections")).to_have_count(0)
    assert page.evaluate("window.__testedMap.getStyle().layers.every(layer => !layer.id.startsWith('connection-'))")
    page.locator("#map-school-select").focus()
    page.locator("#map-school-select").press("ArrowDown")
    page.locator("#map-school-select").press("Enter")
    expect(page.locator("#partner-map-preview")).to_be_visible()
    page.locator("[data-close-map-preview]").press("Escape")
    expect(page.locator("#partner-map-preview")).to_be_hidden()


def test_dynamic_home_school_real_japan_filter_and_shared_url(page, live_server):
    open_partners(page, live_server)
    ready(page)
    expect(page.get_by_role("button", name="我的大學：長庚大學", exact=True)).to_be_attached()
    page.locator("#school-switcher").click()
    page.locator('[data-home-school="國立臺北大學"]').click()
    expect(page.locator("#partner-map-context")).to_contain_text("國立臺北大學", timeout=30000)
    expect(page.locator("#partner-map-status")).to_be_hidden()
    page.locator("#country-filter").select_option("日本")
    ready(page)
    features = map_data(page)["features"]
    assert features and all(f["properties"]["country"] == "日本" for f in features)
    expect(page.get_by_role("button", name="我的大學：國立臺北大學", exact=True)).to_be_attached()
    page.reload()
    ready(page)
    expect(page.locator("#partner-map-context")).to_contain_text("國立臺北大學")
    expect(page.locator("#country-filter")).to_have_value("日本")


def test_direct_query_without_hash_and_all_shared_filters(page, live_server):
    page.add_init_script(INSTRUMENT)
    page.goto(f"{live_server.base_url}/?view=map")
    ready(page)
    assert "#partners" in page.url
    page.locator("#college-filter").select_option("管理學院")
    page.locator("#degree-filter").select_option("大學部")
    page.locator("#availability-filter").select_option("open")
    page.locator('[data-partner-view="list"]').click()
    page.locator('[data-partner-view="map"]').click()
    expect(page.locator("#college-filter")).to_have_value("管理學院")
    expect(page.locator("#degree-filter")).to_have_value("大學部")
    expect(page.locator("#availability-filter")).to_have_value("open")
    page.reload()
    ready(page)
    expect(page.locator("#college-filter")).to_have_value("管理學院")
    expect(page.locator("#degree-filter")).to_have_value("大學部")
    expect(page.locator("#availability-filter")).to_have_value("open")


def test_mobile_list_expansion_and_camera_survive_view_switch(page, live_server):
    page.set_viewport_size({"width": 393, "height": 852})
    open_partners(page, live_server, {"view": "list"})
    first_card = page.locator("#partner-table .partner-card").first
    first_card.locator("summary").click()
    expect(first_card).to_have_attribute("open", "")
    page.locator('[data-partner-view="map"]').click()
    ready(page)
    page.locator("#map-school-select").select_option(LINCOLN)
    page.wait_for_function("() => !window.__testedMap.isMoving()")
    center = page.evaluate("window.__testedMap.getCenter().toArray()")
    page.locator('[data-partner-view="list"]').click()
    expect(first_card).to_have_attribute("open", "")
    page.locator('[data-partner-view="map"]').click()
    assert page.evaluate("window.__testedMap.getCenter().toArray()") == center


def test_mobile_touch_drag_and_pinch(browser, live_server):
    context = browser.new_context(viewport={"width": 393, "height": 852}, is_mobile=True, has_touch=True)
    page = context.new_page()
    try:
        open_partners(page, live_server)
        ready(page)
        page.locator("#partner-globe").scroll_into_view_if_needed()
        box = page.locator("#partner-globe").bounding_box()
        x, y = box["x"] + box["width"] / 2, box["y"] + box["height"] / 2
        session = context.new_cdp_session(page)
        before = page.evaluate("window.__testedMap.getZoom()")
        def pinch_points(distance):
            return [{"x": x-distance, "y": y, "id": 1}, {"x": x+distance, "y": y, "id": 2}]
        session.send("Input.dispatchTouchEvent", {"type": "touchStart", "touchPoints": pinch_points(35)})
        for distance in [45, 60, 80, 105]:
            session.send("Input.dispatchTouchEvent", {"type": "touchMove", "touchPoints": pinch_points(distance)})
        session.send("Input.dispatchTouchEvent", {"type": "touchEnd", "touchPoints": []})
        page.wait_for_function("old => !window.__testedMap.isMoving() && window.__testedMap.getZoom() > old + .3", arg=before)
        original = page.evaluate("window.__testedMap.getCenter().toArray()")
        session.send("Input.dispatchTouchEvent", {"type": "touchStart", "touchPoints": [{"x": x, "y": y, "id": 1}]})
        for distance in [10, 25, 45, 65]:
            session.send("Input.dispatchTouchEvent", {"type": "touchMove", "touchPoints": [{"x": x+distance, "y": y, "id": 1}]})
        session.send("Input.dispatchTouchEvent", {"type": "touchEnd", "touchPoints": []})
        page.wait_for_function("() => !window.__testedMap.isMoving()")
        assert page.evaluate("window.__testedMap.getCenter().toArray()") != original
    finally:
        context.close()


def test_coincident_locations_offer_each_school(page, live_server):
    def coincident(payload):
        base = next(p for p in payload["partner_universities"] if p["school_name"] == LINCOLN)
        payload["partner_universities"] = [dict(base, school_name=f"共址測試 {letter}") for letter in ["A", "B"]]
    inject_dashboard(page, coincident)
    open_partners(page, live_server, {"view": "map", "country": "紐西蘭"})
    ready(page)
    page.locator("#partner-globe").scroll_into_view_if_needed()
    def position(layer):
        return page.evaluate("""layer => { const map=window.__testedMap;const f=map.queryRenderedFeatures({layers:[layer]})[0];const p=map.project(f.geometry.coordinates);return {x:p.x,y:p.y}; }""", layer)
    page.locator("#partner-globe canvas").click(position=position("clusters"))
    page.wait_for_function("() => !window.__testedMap.isMoving() && window.__testedMap.queryRenderedFeatures({layers:['school-points']}).length>0")
    page.locator("#partner-globe canvas").click(position=position("school-points"))
    expect(page.locator("#partner-map-preview h4")).to_have_text("附近有 2 所學校")
    page.locator("#partner-map-preview").get_by_role("button", name="共址測試 B", exact=True).click()
    expect(page.locator("#partner-map-preview h4")).to_have_text("共址測試 B")


def test_selection_motion_pauses_without_moving_camera_and_respects_preferences(page, live_server):
    errors = []
    page.on("pageerror", lambda error: errors.append(str(error)))
    open_partners(page, live_server, {"view": "map", "country": "紐西蘭"})
    ready(page)
    page.locator("#map-school-select").select_option(LINCOLN)
    page.wait_for_function("() => !window.__testedMap.isMoving()")
    page.locator("#partner-globe").scroll_into_view_if_needed()
    active = "() => Math.abs(window.__testedMap.getPaintProperty('selected-halo','circle-radius') - 17) > .1"
    empty = "() => window.__testedMap.getPaintProperty('selected-halo','circle-radius') === 17"
    page.wait_for_function(active)
    center = page.evaluate("window.__testedMap.getCenter().toArray()")
    page.locator("#map-motion").click()
    page.wait_for_function(empty)
    expect(page.locator("#map-motion")).to_have_attribute("aria-pressed", "false")
    assert page.evaluate("window.__testedMap.getCenter().toArray()") == center
    page.locator("#map-motion").click()
    page.wait_for_function(active)
    page.locator('[data-partner-view="list"]').click()
    page.wait_for_function(empty)
    page.locator('[data-partner-view="map"]').click()
    page.locator("#partner-globe").scroll_into_view_if_needed()
    page.wait_for_function(active)
    page.emulate_media(reduced_motion="reduce")
    page.wait_for_function(empty)
    expect(page.locator("#map-motion")).to_be_disabled()
    expect(page.locator("#map-motion")).to_have_attribute("aria-pressed", "false")
    page.emulate_media(reduced_motion="no-preference")
    page.wait_for_function(active)
    assert errors == []
