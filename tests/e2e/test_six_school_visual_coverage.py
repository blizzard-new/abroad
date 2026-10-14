"""Real six-school catalogues and MapLibre; no dashboard/asset interception."""
import json
import os
from pathlib import Path
import socket
import threading
import time

import pytest
import uvicorn
from playwright.sync_api import expect

from exchange_info.api import create_app
from exchange_info.university_registry import SUPPORTED_UNIVERSITIES
from scripts.audit_visual_coverage import marker_available
from .conftest import LiveServer, open_navigation
from .test_partner_globe import INSTRUMENT

ARTIFACTS = Path(os.environ.get("VISUAL_EVIDENCE_DIR", "output/six-school-visual-coverage"))


@pytest.fixture(scope="module")
def visual_server(tmp_path_factory):
    data = tmp_path_factory.mktemp("six-real-school-visuals")
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        port = sock.getsockname()[1]
    server = uvicorn.Server(uvicorn.Config(create_app(data), host="127.0.0.1", port=port, log_level="error"))
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()
    for _ in range(120):
        if server.started:
            break
        time.sleep(.1)
    assert server.started
    try:
        yield LiveServer(f"http://127.0.0.1:{port}", data)
    finally:
        server.should_exit = True
        thread.join(timeout=30)


def ready(page):
    expect(page.locator("#partner-globe")).to_have_attribute("data-ready", "true", timeout=60000)
    page.wait_for_function("() => window.__testedMap && !window.__testedMap.isMoving() && window.__testedMap.isSourceLoaded('schools')", timeout=60000)


def assert_same_filtered_dataset(page):
    snapshot = page.evaluate("""async () => ({partners:filteredPartners().map(p=>({school_name:p.school_name,country:p.country,location:p.location})),features:(await window.__testedMap.getSource('schools').getData()).features})""")
    expected = sorted((p["school_name"], p["country"]) for p in snapshot["partners"] if marker_available(p.get("location")))
    actual = sorted((f["properties"]["name"], f["properties"]["country"]) for f in snapshot["features"])
    assert actual == expected
    return snapshot


@pytest.mark.parametrize("width", [1440, 390])
@pytest.mark.parametrize("university", SUPPORTED_UNIVERSITIES, ids=lambda u:u.id)
def test_real_six_school_map_home_gaps_filters_photos_and_detail(page, visual_server, university, width):
    ARTIFACTS.mkdir(parents=True, exist_ok=True)
    page.set_viewport_size({"width": width, "height": 1000 if width == 1440 else 844})
    page.emulate_media(reduced_motion="reduce")
    page.add_init_script(INSTRUMENT.replace("長庚大學", university.school_name))
    errors = []
    page.on("pageerror", lambda error:errors.append(str(error)))
    page.goto(visual_server.base_url + "/?view=map#partners", wait_until="domcontentloaded")
    expect(page.locator("#boot-splash")).to_be_hidden(timeout=90000)
    ready(page)
    snapshot = assert_same_filtered_dataset(page)
    assert snapshot["partners"]
    expect(page.locator(".map-home-marker")).to_have_count(1)
    expect(page.locator(".map-home-marker")).to_have_attribute("aria-label", "我的大學：" + university.school_name)
    expect(page.locator("#partner-map-home-status")).to_contain_text(university.school_name)
    page.locator("#map-home").click(no_wait_after=True)
    ready(page)
    assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
    page.locator("#partner-map-panel").scroll_into_view_if_needed()
    page.screenshot(path=str(ARTIFACTS/f"{university.id}-home-{width}.png"), full_page=True)
    page.locator("#map-global").click(no_wait_after=True)
    ready(page)
    page.screenshot(path=str(ARTIFACTS/f"{university.id}-map-{width}.png"), full_page=True)

    missing = [p for p in snapshot["partners"] if not marker_available(p.get("location"))]
    if missing:
        page.locator("#partner-map-gaps summary").click()
        expect(page.locator("#partner-map-gaps li")).to_have_count(len(missing))
        expect(page.locator("#partner-map-gaps li").first).to_contain_text(missing[0]["school_name"])
        page.locator("#partner-map-gaps .school-detail-trigger").first.click(no_wait_after=True)
        expect(page.locator("#school-detail-title")).to_have_text(missing[0]["school_name"])
        page.go_back(wait_until="domcontentloaded")
        ready(page)

    located = [p for p in snapshot["partners"] if marker_available(p.get("location"))]
    if located:
        selected = located[0]
        page.locator("#partner-search").fill(selected["school_name"])
        page.wait_for_function("() => !window.__testedMap.isMoving()")
        page.wait_for_timeout(100)
        filtered = assert_same_filtered_dataset(page)
        assert any(p["school_name"] == selected["school_name"] for p in filtered["partners"])
        page.locator("#map-school-select").select_option(selected["school_name"])
        expect(page.locator("#partner-map-preview h4")).to_have_text(selected["school_name"])
        expect(page.locator("#partner-map-preview .school-photo")).to_have_count(1)
        page.locator("#partner-map-preview .school-detail-trigger").click(no_wait_after=True)
        expect(page.locator("#school-detail-title")).to_have_text(selected["school_name"])
        page.go_back(wait_until="domcontentloaded")
        ready(page)
        page.locator("#clear-partner-filters").click(no_wait_after=True)
        ready(page)
    country = snapshot["partners"][0]["country"]
    page.locator("#country-filter").select_option(country)
    ready(page)
    filtered = assert_same_filtered_dataset(page)
    assert filtered["partners"] and all(p["country"] == country for p in filtered["partners"])
    expect(page.locator(".map-home-marker")).to_have_count(1)
    page.locator('[data-partner-view="list"]').click(no_wait_after=True)
    expect(page.locator("#country-filter")).to_have_value(country)
    expect(page.locator("#partner-table")).to_be_visible()
    page.locator("#clear-partner-filters").click(no_wait_after=True)
    photos = page.evaluate("state.dashboard.partner_universities.map(p=>({school_name:p.school_name,image_status:p.image_status,image_url:p.image_url}))")
    for status in ("verified", "needs_review", "missing"):
        photo = next((p for p in photos if p["image_status"] == status), None)
        if not photo:
            continue
        page.locator("#partner-search").fill(photo["school_name"])
        # Both layouts are in the DOM; only the viewport's table/card is visible.
        image = page.locator("#partner-table .school-photo img:visible").first
        if status == "verified":
            expect(image).to_be_attached()
            image.scroll_into_view_if_needed()
            expect(image).to_be_visible()
            page.wait_for_function("() => [...document.querySelectorAll('#partner-table .school-photo img')].some(i=>i.complete&&i.naturalWidth>0)")
        else:
            expect(page.locator("#partner-table .school-photo-fallback:visible").first).to_contain_text("照片待")
        page.screenshot(path=str(ARTIFACTS/f"{university.id}-photo-{status}-{width}.png"), full_page=True)
    (ARTIFACTS/f"{university.id}-{width}.json").write_text(json.dumps({"school":university.school_name,"width":width,"catalog_count":len(snapshot["partners"]),"geojson_feature_count":len(snapshot["features"]),"home_marker_count":1,"unlocated":len(missing),"page_errors":errors},ensure_ascii=False,indent=2))
    assert not errors


def test_home_marker_and_catalogue_follow_all_six_school_switches(page, visual_server):
    page.add_init_script(INSTRUMENT)
    page.emulate_media(reduced_motion="reduce")
    page.goto(visual_server.base_url + "/?view=map#partners", wait_until="domcontentloaded")
    expect(page.locator("#boot-splash")).to_be_hidden(timeout=90000)
    for university in SUPPORTED_UNIVERSITIES:
        open_navigation(page)
        page.locator("#school-switcher").click(no_wait_after=True)
        page.locator(f'[data-home-school="{university.school_name}"]').click(no_wait_after=True)
        page.wait_for_function("school=>state.dashboard?.school_name===school&&!state.partnerDataLoading",arg=university.school_name,timeout=90000)
        page.locator('[data-partner-view="map"]').click(no_wait_after=True)
        ready(page)
        assert_same_filtered_dataset(page)
        expect(page.locator(".map-home-marker")).to_have_count(1)
        expect(page.locator(".map-home-marker")).to_have_attribute("aria-label", "我的大學：" + university.school_name)
