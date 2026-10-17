"""Guards on the browser tracker's privacy promises, so a later edit cannot quietly widen what it collects."""
import re
from pathlib import Path

STATIC = Path(__file__).resolve().parents[1] / "src" / "exchange_info" / "static"
TRACKER = (STATIC / "analytics.js").read_text(encoding="utf-8")
HTML = (STATIC / "index.html").read_text(encoding="utf-8")
APP = (STATIC / "app.js").read_text(encoding="utf-8")


def test_tracker_uses_no_cookies_and_posts_only_to_its_own_endpoint():
    assert "document.cookie" not in TRACKER
    assert re.findall(r'(?:fetch|sendBeacon)\(\s*([A-Za-z_"/]+)', TRACKER).count("ENDPOINT") >= 2
    assert 'var ENDPOINT = "/analytics/events";' in TRACKER
    assert 'credentials: "omit"' in TRACKER
    assert "XMLHttpRequest" not in TRACKER and "googletagmanager" not in TRACKER and "gtag(" not in TRACKER


def test_tracker_respects_browser_privacy_signals_and_offers_an_opt_out():
    for token in ("doNotTrack", "globalPrivacyControl", "uniway-analytics-optout", "data-analytics-ignore",
                  "data-analytics-toggle", "navigator.webdriver"):
        assert token in TRACKER, token
    assert "?analytics=off" in TRACKER or "analytics=off" in TRACKER


def test_tracker_reads_form_values_only_for_the_search_box_and_the_filters():
    reads = re.findall(r"\bel\.value\b", TRACKER)
    assert len(reads) == 2, "only #partner-search and the four filter selects may be read"
    assert "SAFE_VALUE_KEYS" in TRACKER, "data-attribute values (record ids) are kept only for an allowlist"
    assert 'el.id !== "partner-search"' in TRACKER
    assert "availability|country|college|degree" in TRACKER
    assert "password" in TRACKER.split("onClick")[1][:600], "clicks inside password fields are ignored"
    for forbidden in ("localStorage.getItem(\"exchange", "state.account", "email"):
        assert forbidden not in TRACKER, forbidden


def test_page_loads_the_tracker_before_the_app_and_links_the_opt_out():
    assert HTML.index("/static/analytics.js") < HTML.index("/static/app.js")
    assert 'data-analytics-toggle' in HTML and "不使用 cookie" in HTML


def test_app_gives_the_tracker_only_coarse_context_and_never_the_account_id():
    block = APP.split("window.UniWayAnalytics?.setContextProvider(")[1].split("}));")[0]
    assert "school: activeHomeSchool()" in block and "signedIn: Boolean(state.account)" in block
    assert "schoolBasis" in block and ".id" not in block and "email" not in block
    for call in APP.split("window.UniWayAnalytics?.track(")[1:]:
        body = call.split(");")[0]
        assert "email" not in body and "display_name" not in body and "account.id" not in body, body


def test_navigation_debounces_scroll_history_updates_and_tracker_filters_opaque_script_errors():
    navigation = (STATIC / "navigation.js").read_text(encoding="utf-8")
    assert 'window.addEventListener("scroll", saveScroll' not in navigation
    assert 'window.addEventListener("scroll", onScroll, { passive: true })' in navigation
    assert "function safeReplaceState(" in navigation and "function safePushState(" in navigation
    assert "window.setTimeout(saveScroll, 180)" in navigation
    assert "scheduleRouteChanged" in TRACKER
    assert r"/^Script error\.?$/i.test(event.message) && !source && !event.lineno" in TRACKER
