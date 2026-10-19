"""Synthetic GA4 integration tests: Google requests are intercepted, never delivered."""
from pathlib import Path
from playwright.sync_api import expect

STATIC = Path(__file__).resolve().parents[2] / "src" / "exchange_info" / "static"


def setup(page, live_server, *, privacy=False):
    requests = []
    page.route("https://www.googletagmanager.com/**", lambda route: (requests.append(route.request.url), route.fulfill(status=200, body="/* intercepted */")))
    page.route("https://**.google-analytics.com/**", lambda route: route.abort())
    page.route("**/seo-ga4-test*", lambda route: route.fulfill(content_type="text/html", body='''<!doctype html><html><head><meta name="uniway-ga4-id" content="G-TEST123456"></head><body>
<a id="planner" href="/?home=private#school=secret">選校</a><a id="source" href="https://official.example/notice?private=secret" data-official-source>來源</a><footer></footer></body></html>'''))
    if privacy:
        page.add_init_script("Object.defineProperty(navigator, 'globalPrivacyControl', {get: () => true})")
    page.goto(live_server.base_url + "/seo-ga4-test?email=secret@example.com#token=private")
    page.evaluate("document.addEventListener('click', e => { if(e.target.closest('a')) e.preventDefault() })")
    page.add_script_tag(path=str(STATIC / "seo-analytics.js"))
    return requests


def test_ga4_is_opt_in_sanitizes_events_and_stops_after_revocation(page, live_server):
    requests = setup(page, live_server)
    assert requests == [] and page.evaluate("typeof window.dataLayer") == "undefined"
    page.get_by_role("button", name="允許 Google 使用分析", exact=True).click()
    page.wait_for_function("window.dataLayer && window.dataLayer.length >= 4")
    expect(page.locator("[data-ga-status]")).to_contain_text("你已允許")
    page.locator("#planner").click()
    page.locator("#source").click()
    page.evaluate("document.dispatchEvent(new CustomEvent('uniway:compare', {detail: {school_count: 2, email: 'secret@example.com'}}))")
    events = page.evaluate("Array.from(dataLayer, x => Array.from(x))")
    assert "secret@example.com" not in str(events) and "token=private" not in str(events) and "home=private" not in str(events)
    assert {e[1] for e in events if e[0] == "event"} >= {"open_school_planner", "compare_universities", "click_official_source"}
    assert len(requests) == 1
    page.get_by_role("button", name="不允許／撤回同意").click()
    assert page.evaluate("window['ga-disable-G-TEST123456']") is True
    page.locator("#planner").click()
    assert page.evaluate("dataLayer.length") == 0


def test_global_privacy_control_blocks_google_even_after_click(page, live_server):
    requests = setup(page, live_server, privacy=True)
    expect(page.get_by_role("button", name="允許 Google 使用分析", exact=True)).to_be_disabled()
    assert requests == [] and page.evaluate("typeof window.dataLayer") == "undefined"


def test_saved_rejection_does_not_load_google(page, live_server):
    page.add_init_script("localStorage.setItem('uniway-ga4-consent-v1', JSON.stringify({allowed:false, at:Date.now()}))")
    requests = setup(page, live_server)
    assert requests == []
    page.get_by_role("button", name="不允許／撤回同意").click()
    assert page.evaluate("JSON.parse(localStorage.getItem('uniway-ga4-consent-v1')).allowed") is False
