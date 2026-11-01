"""Analytics collection: what is accepted, what is scrubbed, and how it is stored."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest
import requests
from pydantic import ValidationError

from exchange_info.analytics import (
    AnalyticsEvent,
    AnalyticsService,
    ApiMetricRow,
    ApiMetricsAggregator,
    ClientBatch,
    RateLimited,
    RateLimiter,
    clean_props,
    country_from_headers,
    fit_props,
    normalize_batch,
    normalize_route,
    parse_user_agent,
    sanitize_search_term,
)
from exchange_info.analytics_repository import (
    AnalyticsRepositoryError,
    JsonlAnalyticsRepository,
    SupabaseAnalyticsRepository,
    create_analytics_repository,
)

NOW = datetime(2026, 10, 3, 12, 0, tzinfo=timezone.utc)
CHROME = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
          "Chrome/126.0 Safari/537.36")
IPHONE = ("Mozilla/5.0 (iPhone; CPU iPhone OS 17_5 like Mac OS X) AppleWebKit/605.1.15 "
          "(KHTML, like Gecko) Version/17.5 Mobile/15E148 Safari/604.1")
LINE = IPHONE + " Line/14.2.0"


def batch(events, **context):
    base = {"visitor_id": "visitor-abcdef", "session_id": "session-abcdef", "school": "長庚大學"}
    return ClientBatch.model_validate({"v": 1, "context": {**base, **context}, "events": events})


def normalize(events, user_agent=CHROME, headers=None, **context):
    return normalize_batch(batch(events, **context), user_agent=user_agent, headers=headers or {}, now=NOW)


# ----------------------------------------------------------------------------- scrubbing


def test_only_allowlisted_client_events_are_kept_and_server_events_cannot_be_forged():
    events, dropped = normalize([
        {"n": "page_view", "r": "partners"},
        {"n": "account_created"},          # written only by the server
        {"n": "drop_table_users"},
        {"n": "school_open", "p": {"school": "明治大學"}},
    ])
    assert [e.name for e in events] == ["page_view", "school_open"]
    assert dropped == 2


def test_properties_are_scalars_scrubbed_and_bounded():
    props = clean_props({
        "school": "明治大學",
        "nested": {"a": 1}, "items": [1, 2], "Bad-Key": "x", "1bad": "x",
        "note": "寫信給 someone@example.com 或打 0912345678901",
        "flag": True, "count": 3, "ratio": 0.12345678, "nothing": None, "huge": "字" * 500,
    })
    assert "nested" not in props and "items" not in props and "Bad-Key" not in props and "1bad" not in props
    assert props["note"] == "寫信給 [email] 或打 [number]"
    assert props["flag"] is True and props["count"] == 3 and props["ratio"] == 0.123 and props["nothing"] is None
    assert len(props["huge"]) == 160
    assert len(clean_props({f"k{i}": i for i in range(40)})) == 16


@pytest.mark.parametrize("raw,kept", [
    ("日本", "日本"), ("  Meiji University ", "meiji university"), ("學海惜珠 補助", "學海惜珠 補助"),
    ("someone@example.com", ""), ("B1128003", ""), ("b1128003", ""), ("https://x.example/y", ""),
    ("www.example.com", ""), ("0912 345 678", ""), ("a", ""), ("字" * 61, ""),
])
def test_search_terms_are_kept_only_when_they_look_like_topics(raw, kept):
    assert sanitize_search_term(raw) == kept


def test_oversized_properties_are_trimmed_so_the_database_never_rejects_a_batch():
    heavy = {f"k{i}": "字" * 160 for i in range(16)}      # 7.7 KB of Chinese text
    fitted = fit_props(heavy)
    assert 0 < len(fitted) < 16
    import json
    assert len(json.dumps(fitted, ensure_ascii=False).encode("utf-8")) <= 3000
    events, _ = normalize([{"n": "click", "p": heavy}])
    assert len(json.dumps(events[0].props, ensure_ascii=False).encode("utf-8")) <= 3000


def test_search_event_keeps_the_term_or_a_redaction_never_the_personal_text():
    events, _ = normalize([
        {"n": "search", "p": {"q": "日本", "results": 12}},
        {"n": "search", "p": {"q": "b1128003@cgu.edu.tw", "results": 0}},
    ])
    assert events[0].props == {"results": 12, "q_len": 2, "q": "日本"}
    assert events[1].props["q_redacted"] is True and "q" not in events[1].props
    assert "cgu.edu.tw" not in events[1].model_dump_json()


def test_paths_lose_their_query_and_error_messages_lose_links():
    events, _ = normalize([
        {"n": "outbound_click", "p": {"host": "www.example.edu", "path": "/exchange?token=secret#top"}},
        {"n": "js_error", "p": {"message": "Failed to load https://x.example/a?token=1 at 12345"}},
    ])
    assert events[0].props["path"] == "/exchange"
    assert events[1].props["message"] == "Failed to load [url] at 12345"


def test_route_is_normalised_to_a_name_without_values():
    assert normalize_route("#school=明治大學") == "school"
    assert normalize_route("/partners?view=map") == "partners"
    assert normalize_route("") == ""


def test_batches_and_identifiers_are_validated():
    with pytest.raises(ValidationError):
        batch([{"n": "page_view"}] * 41)
    with pytest.raises(ValidationError):
        batch([{"n": "page_view"}], visitor_id="short")
    with pytest.raises(ValidationError):
        batch([{"n": "page_view"}], visitor_id="has spaces and <script>")


# ----------------------------------------------------------------------------- derived fields


def test_event_time_comes_from_the_server_clock_minus_the_reported_age():
    events, _ = normalize([{"n": "page_view", "a": 5000}, {"n": "page_view", "a": 10**12}])
    assert events[0].occurred_at == NOW - timedelta(seconds=5)
    assert events[1].occurred_at == NOW - timedelta(days=1), "an absurd age is clamped, not trusted"


@pytest.mark.parametrize("agent,expected", [
    (CHROME, ("desktop", "Chrome", "Windows", False)),
    (IPHONE, ("mobile", "Safari", "iOS", False)),
    (LINE, ("mobile", "Line (in-app)", "iOS", False)),
    ("Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)", ("desktop", "Other", "Other", True)),
    ("python-requests/2.32", ("desktop", "Other", "Other", True)),
    ("", ("desktop", "Other", "Other", True)),
])
def test_user_agents_are_reduced_to_coarse_classes(agent, expected):
    assert parse_user_agent(agent) == expected


def test_country_comes_only_from_a_cdn_header_never_from_the_ip():
    assert country_from_headers({"CF-IPCountry": "tw"}) == "TW"
    assert country_from_headers({"cloudfront-viewer-country": "JP"}) == "JP"
    assert country_from_headers({"CF-IPCountry": "XX"}) == ""
    assert country_from_headers({}) == ""


def test_context_is_copied_onto_every_event_and_automation_marks_bots():
    events, _ = normalize(
        [{"n": "page_view"}, {"n": "click", "p": {"target": "x"}}],
        user_agent=IPHONE, headers={"accept-language": "zh-TW,zh;q=0.9", "cf-ipcountry": "TW"},
        new_visitor=True, signed_in=True, school_basis="school_email", automated=True,
        utm={"source": "Dcard", "medium": "Social"}, referrer_host="www.dcard.tw", language="",
    )
    event = events[0]
    assert (event.device_class, event.os, event.country, event.language) == ("mobile", "iOS", "TW", "zh-TW")
    assert (event.utm_source, event.utm_medium, event.referrer_host) == ("dcard", "social", "www.dcard.tw")
    assert event.new_visitor and event.signed_in and event.school_basis == "school_email"
    assert event.home_school == "長庚大學" and event.is_bot is True
    assert all(e.visitor_id == "visitor-abcdef" for e in events)


# ----------------------------------------------------------------------------- limits and metrics


def test_rate_limiter_is_a_sliding_window_per_client():
    limiter = RateLimiter(max_batches=3, max_events=10, window_seconds=60)
    assert limiter.allow("a", 4, now=0) and limiter.allow("a", 4, now=1)
    assert not limiter.allow("a", 4, now=2), "event budget exceeded"
    assert limiter.allow("b", 4, now=2), "another client is unaffected"
    assert limiter.allow("a", 1, now=3)
    assert not limiter.allow("a", 1, now=4), "batch budget exceeded"
    assert limiter.allow("a", 1, now=70), "the window slides"


def test_api_metrics_bucket_latency_and_keep_counts_when_a_flush_fails():
    aggregator = ApiMetricsAggregator()
    for status, duration in [(200, 50), (200, 250), (200, 900), (200, 2500), (500, 4000), (404, 20)]:
        aggregator.record("/student-dashboard", "get", status, duration, now=NOW)
    rows = {row.status_class: row for row in aggregator.drain()}
    ok = rows["2xx"]
    assert (ok.request_count, ok.le_100, ok.le_300, ok.le_1000, ok.le_3000, ok.gt_3000) == (4, 1, 1, 1, 1, 0)
    assert (ok.total_ms, ok.max_ms, ok.method) == (3700, 2500, "GET")
    assert rows["5xx"].gt_3000 == 1 and rows["4xx"].le_100 == 1
    assert aggregator.drain() == []
    aggregator.restore(list(rows.values()))
    aggregator.record("/student-dashboard", "GET", 200, 60, now=NOW)
    again = {row.status_class: row for row in aggregator.drain()}
    assert again["2xx"].request_count == 5 and again["2xx"].le_100 == 2


# ----------------------------------------------------------------------------- service


class Boom:
    backend_name = "boom"

    def record_events(self, events):
        raise RuntimeError("database down")

    def record_api_metrics(self, rows):
        raise RuntimeError("database down")

    def purge(self, before):
        raise RuntimeError("database down")


def test_service_stores_events_and_reports_what_it_dropped(tmp_path):
    service = AnalyticsService(JsonlAnalyticsRepository(tmp_path), rate_limiter=RateLimiter())
    result = service.ingest(batch([{"n": "page_view"}, {"n": "nope"}]), user_agent=CHROME, headers={}, client_key="c")
    assert (result.accepted, result.dropped) == (1, 1)
    stored, truncated = service.repository.fetch_events(
        datetime.now(timezone.utc) - timedelta(hours=1), datetime.now(timezone.utc) + timedelta(hours=1), 100)
    assert [e.name for e in stored] == ["page_view"] and not truncated


def test_a_failing_database_never_breaks_collection_or_server_events():
    service = AnalyticsService(Boom())
    result = service.ingest(batch([{"n": "page_view"}]), user_agent=CHROME, headers={}, client_key="c")
    assert (result.accepted, result.dropped) == (0, 1)
    service.emit("post_created", props={"board": "cgu"})            # must not raise
    service.metrics.record("/x", "GET", 200, 5)
    assert service.flush_api_metrics() == 0
    assert service.metrics.drain(), "the counts survive for the next flush"


def test_service_rate_limits_and_can_be_switched_off(tmp_path):
    limited = AnalyticsService(JsonlAnalyticsRepository(tmp_path), rate_limiter=RateLimiter(max_batches=1))
    limited.ingest(batch([{"n": "page_view"}]), user_agent=CHROME, headers={}, client_key="c")
    with pytest.raises(RateLimited):
        limited.ingest(batch([{"n": "page_view"}]), user_agent=CHROME, headers={}, client_key="c")
    off = AnalyticsService.from_environment(JsonlAnalyticsRepository(tmp_path), {"EXCHANGE_ANALYTICS": "off"})
    assert off.enabled is False and off.backend_name == "disabled"
    assert off.ingest(batch([{"n": "page_view"}]), user_agent=CHROME, headers={}, client_key="c").accepted == 0
    assert AnalyticsService(None).enabled is False


def test_emit_writes_only_known_server_events_without_a_visitor(tmp_path):
    service = AnalyticsService(JsonlAnalyticsRepository(tmp_path))
    service.emit("post_created", route="community", props={"board": "cgu", "identity_mode": "anonymous"},
                 home_school="長庚大學", school_basis="self_declared")
    service.emit("page_view")        # a client event name: ignored when emitted by the server
    rows, _ = service.repository.fetch_events(
        datetime.now(timezone.utc) - timedelta(hours=1), datetime.now(timezone.utc) + timedelta(hours=1), 10)
    assert len(rows) == 1
    assert (rows[0].visitor_id, rows[0].is_server, rows[0].props["board"]) == ("server", True, "cgu")


# ----------------------------------------------------------------------------- JSONL repository


def event(name, when, **kwargs):
    return AnalyticsEvent(occurred_at=when, visitor_id=kwargs.pop("visitor_id", "visitor-abcdef"),
                          session_id=kwargs.pop("session_id", "session-abcdef"), name=name, **kwargs)


def test_jsonl_repository_partitions_by_month_and_filters_by_time(tmp_path):
    repository = JsonlAnalyticsRepository(tmp_path)
    assert not (tmp_path / "analytics").exists(), "nothing is created until something is written"
    assert repository.fetch_events(NOW - timedelta(days=1), NOW, 10) == ([], False)
    old = datetime(2026, 8, 20, tzinfo=timezone.utc)
    repository.record_events([event("page_view", old), event("page_view", NOW), event("click", NOW + timedelta(seconds=1))])
    assert sorted(path.name for path in (tmp_path / "analytics").glob("events-*.jsonl")) == [
        "events-202608.jsonl", "events-202610.jsonl"]
    rows, truncated = repository.fetch_events(datetime(2026, 8, 1, tzinfo=timezone.utc),
                                              datetime(2026, 11, 1, tzinfo=timezone.utc), 10)
    assert [e.name for e in rows] == ["page_view", "page_view", "click"] and not truncated
    rows, truncated = repository.fetch_events(datetime(2026, 8, 1, tzinfo=timezone.utc),
                                              datetime(2026, 11, 1, tzinfo=timezone.utc), 2)
    assert len(rows) == 2 and truncated
    only_october, _ = repository.fetch_events(NOW, NOW + timedelta(hours=1), 10)
    assert [e.name for e in only_october] == ["page_view", "click"]


def test_jsonl_api_metrics_accumulate_and_purge_removes_old_rows(tmp_path):
    repository = JsonlAnalyticsRepository(tmp_path)
    hour = NOW.replace(minute=0)
    row = ApiMetricRow(bucket_hour=hour, route="/x", method="GET", status_class="2xx",
                       request_count=2, total_ms=100, max_ms=70, le_100=2)
    repository.record_api_metrics([row])
    repository.record_api_metrics([row.model_copy(update={"max_ms": 90})])
    (merged,) = repository.fetch_api_metrics(hour - timedelta(hours=1), hour + timedelta(hours=1))
    assert (merged.request_count, merged.total_ms, merged.max_ms, merged.le_100) == (4, 200, 90, 4)
    old_hour = datetime(2025, 1, 1, tzinfo=timezone.utc)
    repository.record_api_metrics([row.model_copy(update={"bucket_hour": old_hour})])
    repository.record_events([event("page_view", old_hour), event("page_view", NOW)])
    removed = repository.purge(NOW - timedelta(days=30))
    assert removed == {"events": 1, "api_hourly": 1}
    assert repository.fetch_events(old_hour - timedelta(days=1), NOW + timedelta(days=1), 10)[0][0].occurred_at == NOW
    assert not (tmp_path / "analytics" / "events-202501.jsonl").exists()


# ----------------------------------------------------------------------------- Supabase repository


class FakeResponse:
    def __init__(self, payload=None, status=200):
        self.payload, self.status_code = payload, status

    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.HTTPError(str(self.status_code))

    def json(self):
        return self.payload


class Recorder:
    def __init__(self, *responses):
        self.calls, self.responses = [], list(responses)

    def __call__(self, method, url, **kwargs):
        self.calls.append((method, url, kwargs))
        return self.responses.pop(0) if self.responses else FakeResponse([])


def supabase(recorder):
    return SupabaseAnalyticsRepository("https://project.supabase.co/", "service-secret", request_func=recorder)


def test_supabase_repository_requires_https_and_keeps_the_secret_in_headers_only():
    with pytest.raises(AnalyticsRepositoryError):
        SupabaseAnalyticsRepository("http://project.supabase.co", "secret")
    recorder = Recorder()
    supabase(recorder).record_events([event("page_view", NOW)])
    method, url, kwargs = recorder.calls[0]
    assert (method, url) == ("POST", "https://project.supabase.co/rest/v1/exchange_analytics_events?on_conflict=id")
    assert kwargs["headers"]["Authorization"] == "Bearer service-secret"
    assert "service-secret" not in str(kwargs["json"]) and "ignore-duplicates" in kwargs["headers"]["Prefer"]


def test_supabase_inserts_in_chunks_and_maps_failures_to_a_repository_error():
    recorder = Recorder()
    supabase(recorder).record_events([event("page_view", NOW + timedelta(seconds=i)) for i in range(450)])
    assert [len(call[2]["json"]) for call in recorder.calls] == [200, 200, 50]
    with pytest.raises(AnalyticsRepositoryError):
        supabase(Recorder(FakeResponse(status=503))).record_events([event("page_view", NOW)])


def test_supabase_fetch_pages_through_results_and_reports_truncation():
    rows = [event("page_view", NOW + timedelta(seconds=i)).model_dump(mode="json") for i in range(1500)]
    recorder = Recorder(FakeResponse(rows[:1000]), FakeResponse(rows[1000:1500]))
    fetched, truncated = supabase(recorder).fetch_events(NOW, NOW + timedelta(days=1), 5000)
    assert len(fetched) == 1500 and not truncated
    first_params = dict(recorder.calls[0][2]["params"])
    assert first_params["limit"] == "1000" and first_params["offset"] == "0"
    assert dict(recorder.calls[1][2]["params"])["offset"] == "1000"
    assert ("occurred_at", f"gte.{NOW.isoformat()}") in recorder.calls[0][2]["params"]
    capped = Recorder(FakeResponse(rows[:1000]), FakeResponse(rows[1000:1010]))
    fetched, truncated = supabase(capped).fetch_events(NOW, NOW + timedelta(days=1), 1005)
    assert len(fetched) == 1005 and truncated


def test_supabase_metrics_and_purge_use_the_database_functions():
    recorder = Recorder(FakeResponse(None), FakeResponse({"events": 7, "api_hourly": 3}))
    repository = supabase(recorder)
    repository.record_api_metrics([ApiMetricRow(bucket_hour=NOW.replace(minute=0), route="/x", method="GET",
                                                status_class="2xx", request_count=1)])
    assert recorder.calls[0][1].endswith("/rest/v1/rpc/exchange_analytics_add_api_hourly")
    assert recorder.calls[0][2]["json"]["p_rows"][0]["route"] == "/x"
    assert repository.purge(NOW) == {"events": 7, "api_hourly": 3}
    assert recorder.calls[1][1].endswith("/rest/v1/rpc/exchange_analytics_purge")


# ----------------------------------------------------------------------------- factory


def test_backend_selection_and_the_production_guard(tmp_path):
    assert isinstance(create_analytics_repository(tmp_path, {}), JsonlAnalyticsRepository)
    configured = {"EXCHANGE_SUPABASE_URL": "https://project.supabase.co", "EXCHANGE_SUPABASE_SECRET_KEY": "k"}
    assert isinstance(create_analytics_repository(tmp_path, configured), SupabaseAnalyticsRepository)
    with pytest.raises(AnalyticsRepositoryError):
        create_analytics_repository(tmp_path, {"EXCHANGE_ENVIRONMENT": "production"})
    with pytest.raises(AnalyticsRepositoryError):
        create_analytics_repository(tmp_path, {"EXCHANGE_ANALYTICS_BACKEND": "supabase"})
    with pytest.raises(AnalyticsRepositoryError):
        create_analytics_repository(tmp_path, {"EXCHANGE_ANALYTICS_BACKEND": "mongo"})


def test_application_outcomes_exclude_drafts_identifiers_and_arbitrary_content():
    events, dropped = normalize([
        {"n": name, "p": {"result": "success", "kind": "write", "status": 200,
                            "draft": "私人內容", "plan_id": "private-plan", "file_name": "證明.pdf"}}
        for name in ("plan_create_result", "draft_save_result", "draft_resume_result")
    ])
    assert dropped == 0
    assert len(events) == 3
    assert all(event.props == {"result": "success", "kind": "write", "status": 200} for event in events)
