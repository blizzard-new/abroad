"""The browser tracker end to end: what it records, what it refuses to record, and how to opt out."""
import json
import time

from playwright.sync_api import expect

FORCE = "localStorage.setItem('uniway-analytics-force', '1')"
BROWSE_FIRST = "window.sessionStorage.setItem('exchange-guide-browse-first', '1')"


def open_partners(page, live_server):
    page.add_init_script(BROWSE_FIRST)
    page.goto(f"{live_server.base_url}/#partners")
    expect(page.locator("#partner-table .school-detail-trigger").first).to_be_visible(timeout=30_000)


def recorded(live_server) -> list[dict]:
    rows = []
    folder = live_server.data_dir / "analytics"
    for path in sorted(folder.glob("events-*.jsonl")) if folder.exists() else []:
        rows += [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    return [row for row in rows if row["visitor_id"] != "server"]


def wait_for(live_server, predicate, timeout=15.0):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        rows = recorded(live_server)
        if predicate(rows):
            return rows
        time.sleep(0.3)
    raise AssertionError(f"analytics never recorded the expected events; saw {[r['name'] for r in recorded(live_server)]}")


def flush(page):
    page.evaluate("window.UniWayAnalytics.flush()")


def test_a_visit_is_recorded_with_pages_searches_and_school_opens(page, live_server):
    page.add_init_script(FORCE)
    open_partners(page, live_server)
    page.locator("#partner-search").fill("日本")
    page.wait_for_timeout(1500)
    page.locator("#partner-search").fill("b1128003@cgu.edu.tw")
    page.wait_for_timeout(1500)
    page.locator("#partner-search").fill("")
    page.locator("#country-filter").select_option(index=1)
    trigger = page.locator("#partner-table .school-detail-trigger").first
    school = trigger.get_attribute("data-school-name")
    trigger.click()
    expect(page.locator("#school-detail-title")).to_be_visible()
    flush(page)
    visitor = page.evaluate("localStorage.getItem('uniway-analytics-visitor')")  # created with the first batch
    rows = wait_for(live_server, lambda r: {"school_open", "filter_change"} <= {x["name"] for x in r if x["visitor_id"] == visitor})
    rows = [row for row in rows if row["visitor_id"] == visitor]

    names = [row["name"] for row in rows]
    assert names[0] == "session_start" and "page_view" in names
    views = [row for row in rows if row["name"] == "page_view"]
    assert views[0]["route"] == "partners" and views[0]["props"]["entry"] is True
    searches = [row for row in rows if row["name"] == "search"]
    assert searches[0]["props"]["q"] == "日本" and searches[0]["props"]["results"] is not None
    assert searches[1]["props"].get("q_redacted") is True and "q" not in searches[1]["props"]
    opened = next(row for row in rows if row["name"] == "school_open")
    assert opened["props"]["school"] == school and opened["props"]["surface"] == "list"
    assert next(row for row in rows if row["name"] == "filter_change")["props"]["filter"] == "country"
    assert len({row["visitor_id"] for row in rows}) == 1 and len({row["session_id"] for row in rows}) == 1
    # An automated browser is recorded only on request, and is flagged so reports leave it out.
    assert all(row["is_bot"] is True for row in rows)
    text = json.dumps(rows, ensure_ascii=False)
    assert "cgu.edu.tw" not in text and "b1128003" not in text


def test_automated_browsers_are_not_tracked_unless_asked(page, live_server):
    open_partners(page, live_server)
    before = len(recorded(live_server))
    page.locator("#partner-table .school-detail-trigger").first.click()
    flush(page)
    page.wait_for_timeout(1500)
    assert len(recorded(live_server)) == before
    assert page.evaluate("window.UniWayAnalytics.enabled()") is False


def test_do_not_track_and_opt_out_stop_everything(page, live_server):
    page.add_init_script(FORCE)
    page.add_init_script("Object.defineProperty(navigator, 'doNotTrack', {get: () => '1'})")
    open_partners(page, live_server)
    before = len(recorded(live_server))
    page.locator("#partner-table .school-detail-trigger").first.click()
    flush(page)
    page.wait_for_timeout(1500)
    assert len(recorded(live_server)) == before
    assert page.evaluate("window.UniWayAnalytics.enabled()") is False


def test_the_footer_button_opts_out_and_back_in(page, live_server):
    page.add_init_script(FORCE)
    open_partners(page, live_server)
    page.wait_for_timeout(1000)
    flush(page)
    toggle = page.locator("[data-analytics-toggle]")
    expect(toggle).to_have_text("停用匿名使用統計")
    toggle.click()
    expect(toggle).to_have_text("已停用匿名使用統計，點此重新啟用")
    assert page.evaluate("localStorage.getItem('uniway-analytics-optout')") == "1"
    before = len(recorded(live_server))
    page.locator("#partner-table .school-detail-trigger").first.click()
    flush(page)
    page.wait_for_timeout(1500)
    assert len(recorded(live_server)) == before and page.evaluate("window.UniWayAnalytics.enabled()") is False
    page.reload()
    page.wait_for_load_state("networkidle")
    expect(page.locator("[data-analytics-toggle]")).to_have_text("已停用匿名使用統計，點此重新啟用")
    page.locator("[data-analytics-toggle]").click()
    assert page.evaluate("window.UniWayAnalytics.enabled()") is True


def test_the_address_bar_switch_excludes_your_own_browser(page, live_server):
    page.add_init_script(FORCE)
    page.goto(f"{live_server.base_url}/?analytics=off#partners")
    page.wait_for_function("window.UniWayAnalytics && !window.UniWayAnalytics.enabled()")
    assert page.evaluate("window.UniWayAnalytics.enabled()") is False
    page.goto(f"{live_server.base_url}/?analytics=on#partners")
    page.wait_for_function("window.UniWayAnalytics && window.UniWayAnalytics.enabled()")
    assert page.evaluate("window.UniWayAnalytics.enabled()") is True
