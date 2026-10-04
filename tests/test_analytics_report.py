"""The analytics report on a small, hand-built set of visits where every number can be checked by eye."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from exchange_info.analytics import AnalyticsEvent, ApiMetricRow
from exchange_info.analytics_report import (
    TAIPEI,
    build_report,
    estimate_latency,
    events_to_csv_rows,
    quantile,
)

START = datetime(2026, 9, 27, tzinfo=TAIPEI).astimezone(timezone.utc)   # a 7-day window, Taipei days
END = datetime(2026, 10, 4, tzinfo=TAIPEI).astimezone(timezone.utc)


def at(day: int, hour: int, minute: int = 0, second: int = 0, month: int = 10) -> datetime:
    return datetime(2026, month, day, hour, minute, second, tzinfo=TAIPEI).astimezone(timezone.utc)


def ev(name, when, visitor, session, route="", **fields):
    props = fields.pop("props", {})
    base = dict(device_class="desktop", browser="Chrome", os="Windows", language="zh-TW", viewport="lg<1440",
                home_school="長庚大學", country="TW", timezone="Asia/Taipei")
    return AnalyticsEvent(occurred_at=when, visitor_id=visitor, session_id=session, name=name, route=route,
                          props=props, **{**base, **fields})


def dataset():
    events = [
        # V1: a new visitor from Google who searches, saves a school, signs up and starts planning.
        ev("session_start", at(1, 10), "v1", "s1", new_visitor=True, referrer_host="www.google.com"),
        ev("page_view", at(1, 10, 0), "v1", "s1", "home", new_visitor=True, referrer_host="www.google.com"),
        ev("page_view", at(1, 10, 1), "v1", "s1", "partners", new_visitor=True),
        ev("search", at(1, 10, 2), "v1", "s1", "partners", props={"q": "日本", "q_len": 2, "results": 12}),
        ev("school_open", at(1, 10, 3), "v1", "s1", "partners", props={"school": "明治大學", "surface": "list"}),
        ev("favorite_toggle", at(1, 10, 4), "v1", "s1", "school", props={"school": "明治大學", "saved": True}),
        ev("auth_dialog_open", at(1, 10, 5), "v1", "s1"),
        ev("auth_start", at(1, 10, 6), "v1", "s1", props={"provider": "google"}),
        ev("auth_success", at(1, 10, 7), "v1", "s1", signed_in=True,
           props={"new_account": True, "school_basis": "school_email", "provider": "google"}),
        ev("planning_action", at(1, 10, 8), "v1", "s1", signed_in=True, props={"action": "open-planning"}),
        ev("engagement", at(1, 10, 10), "v1", "s1", "partners", props={"active_ms": 30000, "max_scroll_pct": 80}),
        ev("web_vitals", at(1, 10, 10), "v1", "s1", "home", props={"metric": "lcp", "value": 2000}),
        # V1 comes back the next day.
        ev("page_view", at(2, 9, 0), "v1", "s1b", "home"),
        ev("engagement", at(2, 9, 0, 20), "v1", "s1b", "home", props={"active_ms": 15000, "max_scroll_pct": 30}),
        # V2: opened a link inside Line, looked at one page for three seconds.
        ev("page_view", at(1, 21, 0), "v2", "s2", "home", new_visitor=True, device_class="mobile",
           browser="Line (in-app)", os="iOS", viewport="xs<480"),
        ev("engagement", at(1, 21, 0, 5), "v2", "s2", "home", device_class="mobile", browser="Line (in-app)",
           props={"active_ms": 3000, "max_scroll_pct": 10}),
        # V3: a returning visitor from a campaign link whose search finds nothing.
        ev("page_view", at(2, 20, 0), "v3", "s3", "home", utm_source="dcard", utm_medium="social",
           utm_campaign="launch", home_school="國立臺北大學"),
        ev("page_view", at(2, 20, 1), "v3", "s3", "partners", home_school="國立臺北大學"),
        ev("search", at(2, 20, 2), "v3", "s3", "partners", home_school="國立臺北大學",
           props={"q": "xyzzy", "q_len": 5, "results": 0}),
        ev("search", at(2, 20, 3), "v3", "s3", "partners", home_school="國立臺北大學",
           props={"q_redacted": True, "q_len": 19}),
        ev("school_open", at(2, 20, 4), "v3", "s3", "partners", home_school="國立臺北大學",
           props={"school": "林肯大學", "surface": "map"}),
        ev("filter_change", at(2, 20, 4, 30), "v3", "s3", "partners", home_school="國立臺北大學",
           props={"filter": "country", "value": "日本"}),
        ev("click", at(2, 20, 5), "v3", "s3", "partners", home_school="國立臺北大學",
           props={"target": "theme-toggle", "label": "切換主題"}),
        ev("rage_click", at(2, 20, 5, 10), "v3", "s3", "partners", home_school="國立臺北大學",
           props={"target": "theme-toggle"}),
        ev("outbound_click", at(2, 20, 6), "v3", "s3", "school", home_school="國立臺北大學",
           props={"host": "www.lincoln.ac.nz", "school": "林肯大學"}),
        ev("js_error", at(2, 20, 1, 50), "v3", "s3", "partners", home_school="國立臺北大學",
           props={"message": "Cannot read x of undefined at 12"}),
        ev("web_vitals", at(2, 20, 0, 30), "v3", "s3", "home", home_school="國立臺北大學",
           props={"metric": "lcp", "value": 5000}),
        # A crawler: kept, but not counted unless asked for.
        ev("page_view", at(2, 3, 0), "bot", "sbot", "home", is_bot=True),
        # Server-written facts.
        ev("account_created", at(1, 10, 7), "server", "server", props={"provider": "google"},
           school_basis="school_email", signed_in=True),
        ev("post_created", at(2, 12), "server", "server", props={"board": "cgu", "identity_mode": "anonymous"},
           school_basis="self_declared"),
    ]
    # More LCP samples so the percentiles have something to chew on.
    events += [ev("web_vitals", at(1, 11, i), f"x{i}", f"sx{i}", "home", props={"metric": "lcp", "value": 1000 * v})
               for i, v in enumerate((1, 3, 4), start=1)]
    return events


PREVIOUS = [
    ev("page_view", at(25, 10, month=9), "old1", "so1", "home", new_visitor=True),
    ev("page_view", at(26, 10, month=9), "old2", "so2", "home"),
]
API_ROWS = [
    ApiMetricRow(bucket_hour=at(2, 10), route="/student-dashboard", method="GET", status_class="2xx",
                 request_count=10, total_ms=1500, max_ms=800, le_100=6, le_300=3, le_1000=1),
    ApiMetricRow(bucket_hour=at(2, 11), route="/student-dashboard", method="GET", status_class="5xx",
                 request_count=2, total_ms=8000, max_ms=5000, gt_3000=2),
]
COUNTRIES = {"明治大學": "日本", "林肯大學": "紐西蘭"}


@pytest.fixture(scope="module")
def report():
    return build_report(dataset(), API_ROWS, start=START, end=END, previous_events=PREVIOUS,
                        school_countries=COUNTRIES, now=END)


def test_overview_counts_people_sessions_and_bounces(report):
    current = report["overview"]["current"]
    # Crawler and server rows are excluded; the three LCP-only visitors (x1..x3) have a session each.
    assert current["sessions"] == 7 and current["visitors"] == 6
    assert current["pageviews"] == 6
    assert current["new_visitors"] == 2 and current["returning_visitors"] == 4
    assert current["bounce_rate"] > 0


def test_headline_numbers_without_the_speed_only_visitors():
    events = [e for e in dataset() if not e.visitor_id.startswith("x")]
    report = build_report(events, API_ROWS, start=START, end=END, previous_events=PREVIOUS, now=END)
    current, previous = report["overview"]["current"], report["overview"]["previous"]
    assert (current["visitors"], current["sessions"], current["pageviews"]) == (3, 4, 6)
    assert (current["new_visitors"], current["returning_visitors"]) == (2, 1)
    assert current["pages_per_session"] == 1.5
    # Sessions last 600 s (V1), 20 s (V1 again), 5 s (V2) and 360 s (V3).
    assert current["median_session_seconds"] == 190.0
    assert current["avg_session_seconds"] == pytest.approx(246.25, abs=0.1)
    assert current["bounce_rate"] == 25.0, "only the 3-second Line visit counts as a bounce"
    assert current["signed_in_session_share"] == 25.0
    assert (previous["visitors"], previous["pageviews"]) == (2, 2)
    assert report["overview"]["change_pct"]["visitors"] == 50.0
    assert report["overview"]["change_pct"]["pageviews"] == 200.0


def test_bots_are_excluded_unless_requested_and_counted_in_data_quality():
    quality = build_report(dataset(), [], start=START, end=END, now=END)["data_quality"]
    assert quality["bot_events_in_range"] == 1 and quality["bots_excluded"] is True
    with_bots = build_report(dataset(), [], start=START, end=END, include_bots=True, now=END)
    assert with_bots["overview"]["current"]["sessions"] == 8
    assert with_bots["data_quality"]["bots_excluded"] is False


def test_timeseries_covers_every_taipei_day_and_the_heatmap_uses_local_hours(report):
    series = report["timeseries"]
    assert series["days"] == ["2026-09-27", "2026-09-28", "2026-09-29", "2026-09-30", "2026-10-01",
                              "2026-10-02", "2026-10-03"]
    oct_1, oct_2 = series["days"].index("2026-10-01"), series["days"].index("2026-10-02")
    assert series["pageviews"][oct_1] == 3 and series["pageviews"][oct_2] == 3
    assert series["new_accounts"][oct_1] == 1
    assert series["school_opens"][oct_2] == 1 and series["school_opens"][oct_1] == 1
    assert sum(series["pageviews"]) == 6
    # Thursday 2026-10-01 10:00 Taipei is weekday 3, hour 10; the crawler's 03:00 visit is excluded.
    assert report["heatmap"][3][10] == 2
    assert report["heatmap"][4][3] == 0


def test_pages_report_entries_exits_and_engagement(report):
    pages = {row["route"]: row for row in report["pages"]}
    assert pages["home"]["views"] == 4 and pages["partners"]["views"] == 2
    assert pages["partners"]["avg_scroll_pct"] == 80.0
    assert pages["home"]["entries"] == 4 and pages["home"]["exits"] == 2 and pages["partners"]["exits"] == 2
    assert pages["home"]["avg_engaged_seconds"] == pytest.approx((15 + 3) / 2, abs=0.1)


def test_traffic_channels_use_referrer_campaign_and_in_app_browsers():
    events = [e for e in dataset() if not e.visitor_id.startswith("x")]
    traffic = build_report(events, [], start=START, end=END, now=END)["traffic"]
    channels = {row["channel"]: row for row in traffic["channels"]}
    assert set(channels) == {"search", "direct", "social", "campaign"}
    assert channels["search"]["signups"] == 1 and channels["search"]["signup_rate"] == 100.0
    assert channels["social"]["bounce_rate"] == 100.0, "the Line visitor left after one page"
    assert traffic["referrers"][0]["host"] == "www.google.com"
    assert traffic["utm_campaign"][0]["campaign"] == "launch"


def test_audience_tables(report):
    audience = report["audience"]
    assert {row["key"] for row in audience["device"]} == {"desktop", "mobile"}
    assert {row["key"]: row["count"] for row in audience["viewing_school"]}["國立臺北大學"] == 1
    assert {row["key"]: row["count"] for row in audience["new_vs_returning"]} == {"回訪": 5, "新訪客": 2}


def test_school_interest_favourites_countries_and_home_school_split(report):
    schools = report["schools"]
    top = {row["school"]: row for row in schools["top"]}
    assert top["明治大學"]["opens"] == 1 and top["明治大學"]["favorites_added"] == 1
    assert top["明治大學"]["favorite_rate"] == 100.0 and top["明治大學"]["country"] == "日本"
    assert top["林肯大學"]["outbound_clicks"] == 1 and top["林肯大學"]["country"] == "紐西蘭"
    assert top["林肯大學"]["from_home_school"] == {"國立臺北大學": 1}
    assert {row["country"] for row in schools["countries"]} == {"日本", "紐西蘭"}
    assert schools["by_home_school"]["長庚大學"][0]["school"] == "明治大學"


def test_search_reports_zero_results_redactions_and_conversion(report):
    search = report["search"]
    assert search["total"] == 3 and search["sessions_with_search"] == 2
    assert search["redacted"] == 1
    assert search["zero_result_rate"] == pytest.approx(33.3, abs=0.1)
    assert search["to_school_open_rate"] == 100.0
    assert {t["term"]: t["searches"] for t in search["top_terms"]} == {"日本": 1, "xyzzy": 1}
    assert [t["term"] for t in search["zero_result_terms"]] == ["xyzzy"]
    assert report["filters_used"]["values"]["country"][0]["value"] == "日本"


def test_feature_usage_clicks_and_rage_clicks(report):
    features = {row["feature"]: row for row in report["features"]["usage"]}
    assert features["school_open"]["count"] == 2 and features["search"]["visitors"] == 2
    assert report["features"]["top_clicks"][0] == {"target": "theme-toggle", "label": "切換主題", "clicks": 1, "visitors": 1}
    assert report["features"]["rage_clicks"][0]["target"] == "theme-toggle"


def test_funnel_follows_each_visitor_in_order():
    events = [e for e in dataset() if not e.visitor_id.startswith("x")]
    funnel = build_report(events, [], start=START, end=END, now=END)["funnel"]
    assert [row["visitors"] for row in funnel] == [3, 2, 1, 1, 1, 1]
    assert [row["pct_of_first"] for row in funnel] == [100.0, 66.7, 33.3, 33.3, 33.3, 33.3]
    assert funnel[2]["dropped"] == 1 and funnel[3]["pct_of_previous"] == 100.0


def test_funnel_ignores_steps_that_happen_before_the_previous_one():
    out_of_order = [
        ev("school_open", at(1, 10, 0), "z", "sz", props={"school": "A"}),
        ev("page_view", at(1, 10, 5), "z", "sz", "home"),
    ]
    funnel = build_report(out_of_order, [], start=START, end=END, now=END)["funnel"]
    assert [row["visitors"] for row in funnel][:2] == [1, 0]


def test_signup_section_combines_browser_and_server_facts(report):
    signup = report["signup"]
    assert (signup["dialog_opens"], signup["starts"], signup["successes"]) == (1, 1, 1)
    assert signup["starts_by_provider"][0]["provider"] == "google"
    assert signup["new_accounts_seen_by_browser"] == 1 and signup["start_to_success_rate"] == 100.0
    assert signup["accounts_created_by_server"] == 1
    assert signup["accounts_created_by_school_basis"][0]["basis"] == "school_email"
    assert signup["median_days_first_visit_to_signup"] == 0.0


def test_retention_counts_first_visit_cohorts_only():
    events = [e for e in dataset() if not e.visitor_id.startswith("x")]
    retention = build_report(events, [], start=START, end=END, now=END)["retention"]
    assert retention["summary"]["day_1"] == {"cohort": 2, "retained": 1, "rate": 50.0}
    assert retention["summary"]["day_7"]["cohort"] == 0 and retention["summary"]["day_7"]["rate"] is None
    assert retention["weekly"][0]["size"] == 2 and retention["weekly"][0]["day_1"] == 50.0


def test_engagement_buckets(report):
    engagement = report["engagement"]
    scroll = {row["key"]: row["count"] for row in engagement["scroll_depth"]}
    assert scroll["75–100%"] == 1 and scroll["25–50%"] == 1 and scroll["0–25%"] == 1
    assert sum(row["count"] for row in engagement["session_duration"]) == 7
    device = {row["device"]: row for row in engagement["engaged_seconds_by_device"]}
    assert device["mobile"]["avg_engaged_seconds"] == 3.0


def test_performance_percentiles_and_thresholds(report):
    lcp = next(row for row in report["performance"]["vitals"] if row["metric"] == "lcp")
    assert lcp["samples"] == 5
    assert (lcp["p50"], lcp["p75"]) == (3000.0, 4000.0)
    assert lcp["good_share"] == 40.0 and lcp["poor_share"] == 20.0
    assert quantile([1, 2, 3, 4], 0.5) == 2.5 and quantile([], 0.5) is None


def test_errors_group_messages_after_replacing_numbers(report):
    errors = report["errors"]
    assert errors["js_errors"] == 1 and errors["sessions_affected"] == 1
    assert errors["sessions_affected_share"] == pytest.approx(14.3, abs=0.1)
    assert errors["top_messages"][0]["message"] == "Cannot read x of undefined at N"
    assert errors["top_messages"][0]["top_route"] == "partners"


def test_api_health_estimates_latency_from_buckets(report):
    api = report["api"]
    route = api["routes"][0]
    assert route["route"] == "/student-dashboard" and route["requests"] == 12
    assert route["error_5xx"] == 2 and route["error_5xx_rate"] == pytest.approx(16.7, abs=0.1)
    assert route["avg_ms"] == pytest.approx(791.7, abs=0.1)
    assert (route["p50_ms_estimate"], route["p95_ms_estimate"]) == (100.0, 7900.0)
    assert route["slow_share"] == pytest.approx(16.7, abs=0.1)
    assert {row["status"]: row["count"] for row in api["status_classes"]} == {"2xx": 10, "5xx": 2}
    assert api["daily"]["errors_5xx"] == [2] and api["daily"]["days"] == ["2026-10-02"]
    assert estimate_latency([0, 0, 0, 0, 0], 0.5) is None


def test_community_section_counts_server_written_posts(report):
    community = report["community"]
    assert community["posts"] == 1 and community["posts_by_board"][0]["board"] == "cgu"
    assert community["posts_by_account_verification"][0]["basis"] == "self_declared"


def test_school_filter_and_truncation_flag():
    filtered = build_report(dataset(), [], start=START, end=END, home_school="國立臺北大學", now=END)
    assert filtered["overview"]["current"]["sessions"] == 1
    assert filtered["filters"]["home_school"] == "國立臺北大學"
    assert build_report([], [], start=START, end=END, truncated=True, now=END)["data_quality"]["truncated"] is True
    empty = build_report([], [], start=START, end=END, now=END)
    assert empty["overview"]["current"]["visitors"] == 0 and empty["funnel"][0]["visitors"] == 0
    assert empty["overview"]["change_pct"]["visitors"] is None


def test_csv_neutralises_spreadsheet_formulas():
    rows = events_to_csv_rows([ev("click", at(2, 20), "v", "s", "partners",
                                  props={"target": "=HYPERLINK(\"http://evil\")", "label": "+cmd"},
                                  home_school="=1+1")])
    assert rows[0][0] == "time_taipei" and rows[1][0] == "2026-10-02 20:00:00"
    assert rows[1][3] == "'=1+1", "a cell starting with = is prefixed so it cannot run as a formula"
