"""Turn raw analytics events into the numbers a product owner reads (see docs/analytics.md for definitions).

All days and hours are Asia/Taipei. Every function works on plain lists, so the same report is produced
whichever repository (JSONL or Supabase) supplied the events.
"""
from __future__ import annotations

import re
import statistics
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta, timezone
from typing import Any, Iterable, Mapping, Sequence
from zoneinfo import ZoneInfo

from .analytics import AnalyticsEvent, ApiMetricRow

TAIPEI = ZoneInfo("Asia/Taipei")
BOUNCE_ENGAGED_MS = 10_000
TOP = 20

INTERACTIVE_EVENTS = frozenset({
    "click", "school_open", "favorite_toggle", "search", "filter_change", "view_switch", "auth_dialog_open",
    "auth_start", "auth_success", "school_pick", "school_choose", "advisor_submit", "document_action",
    "calendar_action", "planning_action", "community_composer_open", "community_topic", "board_follow",
    "outbound_click", "file_download", "theme_toggle",
})
COMMIT_EVENTS = frozenset({"planning_action", "document_action", "advisor_submit", "calendar_action"})
FEATURE_EVENTS = (
    "school_open", "favorite_toggle", "search", "filter_change", "view_switch", "advisor_submit",
    "planning_action", "document_action", "calendar_action", "outbound_click", "file_download",
    "community_composer_open", "community_topic", "board_follow", "school_pick", "theme_toggle",
)
SEARCH_HOSTS = ("google.", "bing.", "yahoo.", "duckduckgo.", "baidu.", "naver.", "ecosia.", "yandex.")
SOCIAL_HOSTS = (
    "facebook.", "fb.", "instagram.", "line.me", "lin.ee", "t.co", "twitter.", "x.com", "threads.",
    "dcard.", "ptt.", "reddit.", "youtube.", "youtu.be", "linkedin.", "tiktok.", "pinterest.", "telegram.",
    "discord.",
)
PAID_MEDIUMS = {"cpc", "ppc", "paid", "paidsocial", "paid_social", "display"}
VITAL_THRESHOLDS = {  # (good up to, poor from) — web.dev
    "lcp": (2500, 4000), "fcp": (1800, 3000), "ttfb": (800, 1800), "cls": (0.1, 0.25), "inp": (200, 500),
}
LATENCY_BOUNDS = ((0, 100), (100, 300), (300, 1000), (1000, 3000), (3000, 10000))
DURATION_BUCKETS = ((10, "0–10 秒"), (30, "10–30 秒"), (60, "30–60 秒"), (180, "1–3 分"), (600, "3–10 分"))
PAGES_BUCKETS = ((1, "1 頁"), (2, "2 頁"), (4, "3–4 頁"), (9, "5–9 頁"))


# --------------------------------------------------------------------------- small helpers


def pct(part: float, whole: float) -> float:
    return round(part / whole * 100, 1) if whole else 0.0


def change_pct(current: float, previous: float) -> float | None:
    return round((current - previous) / previous * 100, 1) if previous else None


def quantile(values: Sequence[float], q: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    position = (len(ordered) - 1) * q
    low, high = int(position), min(int(position) + 1, len(ordered) - 1)
    return round(ordered[low] + (ordered[high] - ordered[low]) * (position - low), 3)


def local(moment: datetime) -> datetime:
    return moment.astimezone(TAIPEI)


def prop(event: AnalyticsEvent, key: str, default: Any = None) -> Any:
    value = event.props.get(key, default)
    return default if value is None else value


def number(event: AnalyticsEvent, key: str) -> float | None:
    value = event.props.get(key)
    return float(value) if isinstance(value, (int, float)) and not isinstance(value, bool) else None


def table(counter: Mapping[str, int], total: int | None = None, limit: int = TOP,
          label: str = "key") -> list[dict[str, Any]]:
    whole = total if total is not None else sum(counter.values())
    return [{label: key or "(未提供)", "count": count, "share": pct(count, whole)}
            for key, count in sorted(counter.items(), key=lambda item: (-item[1], item[0]))[:limit]]


def bucketed(values: Iterable[float], buckets: Sequence[tuple[float, str]], last_label: str) -> list[dict[str, Any]]:
    counts: Counter[str] = Counter()
    total = 0
    for value in values:
        total += 1
        label = next((name for bound, name in buckets if value <= bound), last_label)
        counts[label] += 1
    order = [name for _, name in buckets] + [last_label]
    return [{"key": name, "count": counts[name], "share": pct(counts[name], total)} for name in order]


# --------------------------------------------------------------------------- sessions


@dataclass
class Session:
    session_id: str
    visitor_id: str
    events: list[AnalyticsEvent] = field(default_factory=list)

    @property
    def first(self) -> AnalyticsEvent:
        return self.events[0]

    @property
    def last(self) -> AnalyticsEvent:
        return self.events[-1]

    @property
    def page_views(self) -> list[AnalyticsEvent]:
        return [e for e in self.events if e.name == "page_view"]

    @property
    def duration_s(self) -> float:
        return (self.last.occurred_at - self.first.occurred_at).total_seconds()

    @property
    def engaged_ms(self) -> float:
        return sum(number(e, "active_ms") or 0 for e in self.events if e.name == "engagement")

    @property
    def interactive(self) -> bool:
        return any(e.name in INTERACTIVE_EVENTS for e in self.events)

    @property
    def bounced(self) -> bool:
        return len(self.page_views) <= 1 and not self.interactive and self.engaged_ms < BOUNCE_ENGAGED_MS

    @property
    def signed_in(self) -> bool:
        return any(e.signed_in for e in self.events)

    @property
    def new_visitor(self) -> bool:
        return any(e.new_visitor for e in self.events)

    @property
    def home_school(self) -> str:
        schools = Counter(e.home_school for e in self.events if e.home_school)
        return schools.most_common(1)[0][0] if schools else ""


def build_sessions(events: Iterable[AnalyticsEvent]) -> list[Session]:
    grouped: dict[str, Session] = {}
    for event in sorted(events, key=lambda e: (e.occurred_at, e.id)):
        session = grouped.get(event.session_id)
        if session is None:
            session = grouped[event.session_id] = Session(event.session_id, event.visitor_id)
        session.events.append(event)
    return sorted(grouped.values(), key=lambda s: s.first.occurred_at)


def classify_channel(session: Session) -> str:
    first = next((e for e in session.events if e.referrer_host or e.utm_source or e.utm_medium or e.utm_campaign),
                 session.first)
    medium = first.utm_medium
    host = first.referrer_host
    if medium in PAID_MEDIUMS:
        return "paid"
    if first.utm_source or medium or first.utm_campaign:
        return "campaign"
    if host:
        if any(token in host for token in SEARCH_HOSTS):
            return "search"
        if any(host == token.rstrip(".") or token in host for token in SOCIAL_HOSTS):
            return "social"
        return "referral"
    if first.browser.endswith("(in-app)"):
        return "social"  # links opened inside Line / Instagram / Facebook arrive without a referrer
    return "direct"


# --------------------------------------------------------------------------- sections


def overview(sessions: Sequence[Session]) -> dict[str, Any]:
    visitors = {s.visitor_id for s in sessions}
    page_views = sum(len(s.page_views) for s in sessions)
    durations = [s.duration_s for s in sessions]
    new = {s.visitor_id for s in sessions if s.new_visitor}
    return {
        "visitors": len(visitors),
        "sessions": len(sessions),
        "pageviews": page_views,
        "events": sum(len(s.events) for s in sessions),
        "new_visitors": len(new),
        "returning_visitors": len(visitors - new),
        "pages_per_session": round(page_views / len(sessions), 2) if sessions else 0.0,
        "avg_session_seconds": round(statistics.fmean(durations), 1) if durations else 0.0,
        "median_session_seconds": round(statistics.median(durations), 1) if durations else 0.0,
        "avg_engaged_seconds": round(statistics.fmean(s.engaged_ms for s in sessions) / 1000, 1) if sessions else 0.0,
        "bounce_rate": pct(sum(s.bounced for s in sessions), len(sessions)),
        "signed_in_session_share": pct(sum(s.signed_in for s in sessions), len(sessions)),
        "interactions_per_session": round(
            sum(1 for s in sessions for e in s.events if e.name in INTERACTIVE_EVENTS) / len(sessions), 2
        ) if sessions else 0.0,
    }


def overview_change(current: Mapping[str, Any], previous: Mapping[str, Any]) -> dict[str, float | None]:
    keys = ("visitors", "sessions", "pageviews", "pages_per_session", "avg_session_seconds",
            "avg_engaged_seconds", "bounce_rate")
    return {key: change_pct(current[key], previous[key]) for key in keys}


def local_days(start: datetime, end: datetime) -> list[date]:
    first, last = local(start).date(), local(end - timedelta(microseconds=1)).date()
    return [first + timedelta(days=offset) for offset in range((last - first).days + 1)]


def timeseries(sessions: Sequence[Session], server: Sequence[AnalyticsEvent], start: datetime,
               end: datetime) -> dict[str, Any]:
    days = local_days(start, end)
    visitors: dict[date, set[str]] = defaultdict(set)
    sessions_by_day: Counter[date] = Counter()
    views: Counter[date] = Counter()
    opens: Counter[date] = Counter()
    new_visitors: dict[date, set[str]] = defaultdict(set)
    for session in sessions:
        sessions_by_day[local(session.first.occurred_at).date()] += 1
        for event in session.events:
            day = local(event.occurred_at).date()
            visitors[day].add(event.visitor_id)
            if event.new_visitor:
                new_visitors[day].add(event.visitor_id)
            if event.name == "page_view":
                views[day] += 1
            elif event.name == "school_open":
                opens[day] += 1
    accounts: Counter[date] = Counter(local(e.occurred_at).date() for e in server if e.name == "account_created")
    return {
        "days": [day.isoformat() for day in days],
        "visitors": [len(visitors[day]) for day in days],
        "new_visitors": [len(new_visitors[day]) for day in days],
        "sessions": [sessions_by_day[day] for day in days],
        "pageviews": [views[day] for day in days],
        "school_opens": [opens[day] for day in days],
        "new_accounts": [accounts[day] for day in days],
    }


def heatmap(events: Iterable[AnalyticsEvent]) -> list[list[int]]:
    grid = [[0] * 24 for _ in range(7)]
    for event in events:
        if event.name == "page_view":
            moment = local(event.occurred_at)
            grid[moment.weekday()][moment.hour] += 1
    return grid


def pages(sessions: Sequence[Session]) -> list[dict[str, Any]]:
    views: Counter[str] = Counter()
    visitors: dict[str, set[str]] = defaultdict(set)
    entries: Counter[str] = Counter()
    exits: Counter[str] = Counter()
    bounces: Counter[str] = Counter()
    engaged: dict[str, list[float]] = defaultdict(list)
    scroll: dict[str, list[float]] = defaultdict(list)
    for session in sessions:
        route_views = session.page_views
        for event in route_views:
            route = event.route or "home"
            views[route] += 1
            visitors[route].add(event.visitor_id)
        if route_views:
            entries[route_views[0].route or "home"] += 1
            exits[route_views[-1].route or "home"] += 1
            if session.bounced:
                bounces[route_views[0].route or "home"] += 1
        for event in session.events:
            if event.name == "engagement":
                route = event.route or "home"
                if (active := number(event, "active_ms")) is not None:
                    engaged[route].append(active / 1000)
                if (depth := number(event, "max_scroll_pct")) is not None:
                    scroll[route].append(depth)
    rows = []
    for route, count in views.most_common(TOP * 2):
        rows.append({
            "route": route, "views": count, "visitors": len(visitors[route]),
            "entries": entries[route], "exits": exits[route], "bounces": bounces[route],
            "bounce_rate": pct(bounces[route], entries[route]),
            "exit_rate": pct(exits[route], count),
            "avg_engaged_seconds": round(statistics.fmean(engaged[route]), 1) if engaged[route] else None,
            "avg_scroll_pct": round(statistics.fmean(scroll[route]), 1) if scroll[route] else None,
        })
    return rows


def traffic(sessions: Sequence[Session]) -> dict[str, Any]:
    channels: dict[str, list[Session]] = defaultdict(list)
    for session in sessions:
        channels[classify_channel(session)].append(session)
    rows = []
    for channel, group in sorted(channels.items(), key=lambda item: -len(item[1])):
        signups = sum(1 for s in group if any(e.name == "auth_success" and prop(e, "new_account") is True
                                                for e in s.events))
        rows.append({
            "channel": channel, "sessions": len(group), "visitors": len({s.visitor_id for s in group}),
            "share": pct(len(group), len(sessions)),
            "pages_per_session": round(sum(len(s.page_views) for s in group) / len(group), 2),
            "bounce_rate": pct(sum(s.bounced for s in group), len(group)),
            "signups": signups, "signup_rate": pct(signups, len(group)),
        })

    def first_value(session: Session, attr: str) -> str:
        return next((getattr(e, attr) for e in session.events if getattr(e, attr)), "")

    return {
        "channels": rows,
        "referrers": table(Counter(first_value(s, "referrer_host") for s in sessions if first_value(s, "referrer_host")),
                           len(sessions), label="host"),
        "utm_source": table(Counter(first_value(s, "utm_source") for s in sessions if first_value(s, "utm_source")),
                            len(sessions), label="source"),
        "utm_medium": table(Counter(first_value(s, "utm_medium") for s in sessions if first_value(s, "utm_medium")),
                            len(sessions), label="medium"),
        "utm_campaign": table(Counter(first_value(s, "utm_campaign") for s in sessions if first_value(s, "utm_campaign")),
                              len(sessions), label="campaign"),
    }


def audience(sessions: Sequence[Session]) -> dict[str, Any]:
    def by(attr: str, transform=lambda v: v) -> list[dict[str, Any]]:
        return table(Counter(transform(getattr(s.first, attr)) for s in sessions), len(sessions))

    return {
        "device": by("device_class"),
        "browser": by("browser"),
        "os": by("os"),
        "viewport": by("viewport"),
        "language": by("language", lambda v: v.split("-")[0] if v else v),
        "country": by("country"),
        "timezone": by("timezone"),
        "display_mode": by("display_mode"),
        "connection": by("connection"),
        "viewing_school": table(Counter(s.home_school for s in sessions), len(sessions)),
        "new_vs_returning": table(Counter("新訪客" if s.new_visitor else "回訪" for s in sessions), len(sessions)),
        "signed_in": table(Counter("已登入" if s.signed_in else "訪客" for s in sessions), len(sessions)),
    }


def schools(events: Sequence[AnalyticsEvent], countries: Mapping[str, str]) -> dict[str, Any]:
    rows: dict[str, dict[str, Any]] = {}

    def row(name: str) -> dict[str, Any]:
        return rows.setdefault(name, {
            "school": name, "country": countries.get(name, ""), "opens": 0, "visitors": set(),
            "favorites_added": 0, "favorites_removed": 0, "outbound_clicks": 0, "downloads": 0,
            "from_home_school": Counter(),
        })

    for event in events:
        name = prop(event, "school", "")
        if not name or event.name not in {"school_open", "favorite_toggle", "outbound_click", "file_download"}:
            continue
        item = row(str(name))
        item["visitors"].add(event.visitor_id)
        if event.name == "school_open":
            item["opens"] += 1
            item["from_home_school"][event.home_school or "(未選)"] += 1
        elif event.name == "favorite_toggle":
            item["favorites_added" if prop(event, "saved") is True else "favorites_removed"] += 1
        elif event.name == "outbound_click":
            item["outbound_clicks"] += 1
        else:
            item["downloads"] += 1
    ranked = sorted(rows.values(), key=lambda r: (-r["opens"], -r["favorites_added"], r["school"]))
    out = []
    for item in ranked[:50]:
        opens = item["opens"]
        out.append({
            **{k: v for k, v in item.items() if k not in {"visitors", "from_home_school"}},
            "visitors": len(item["visitors"]),
            "favorite_rate": pct(item["favorites_added"], opens),
            "from_home_school": dict(item["from_home_school"]),
        })
    by_country: dict[str, dict[str, Any]] = {}
    for item in rows.values():
        country = item["country"] or "(未知)"
        entry = by_country.setdefault(country, {"country": country, "opens": 0, "visitors": set()})
        entry["opens"] += item["opens"]
        entry["visitors"] |= item["visitors"]
    by_home: dict[str, Counter[str]] = defaultdict(Counter)
    for event in events:
        if event.name == "school_open" and prop(event, "school"):
            by_home[event.home_school or "(未選)"][str(prop(event, "school"))] += 1
    return {
        "top": out,
        "countries": [
            {"country": c["country"], "opens": c["opens"], "visitors": len(c["visitors"])}
            for c in sorted(by_country.values(), key=lambda c: -c["opens"])[:TOP] if c["opens"]
        ],
        "by_home_school": {home: table(counter, limit=10, label="school") for home, counter in by_home.items()},
        "opens_total": sum(r["opens"] for r in rows.values()),
        "favorites_total": sum(r["favorites_added"] for r in rows.values()),
    }


def search(sessions: Sequence[Session]) -> dict[str, Any]:
    searches = [(s, e) for s in sessions for e in s.events if e.name == "search"]
    terms: dict[str, dict[str, Any]] = {}
    redacted = zero = 0
    for _, event in searches:
        results = number(event, "results")
        if results == 0:
            zero += 1
        term = prop(event, "q", "")
        if not term:
            redacted += 1
            continue
        entry = terms.setdefault(str(term), {"term": str(term), "searches": 0, "visitors": set(), "results": [],
                                             "zero_results": 0})
        entry["searches"] += 1
        entry["visitors"].add(event.visitor_id)
        if results is not None:
            entry["results"].append(results)
            entry["zero_results"] += results == 0
    searching = {s.session_id for s, _ in searches}
    converted = 0
    for session in sessions:
        if session.session_id not in searching:
            continue
        first_search = next(e.occurred_at for e in session.events if e.name == "search")
        converted += any(e.name == "school_open" and e.occurred_at >= first_search for e in session.events)
    ranked = sorted(terms.values(), key=lambda t: (-t["searches"], t["term"]))

    def render(entry: dict[str, Any]) -> dict[str, Any]:
        return {"term": entry["term"], "searches": entry["searches"], "visitors": len(entry["visitors"]),
                "avg_results": round(statistics.fmean(entry["results"]), 1) if entry["results"] else None,
                "zero_results": entry["zero_results"]}

    return {
        "total": len(searches), "sessions_with_search": len(searching),
        "searches_per_searching_session": round(len(searches) / len(searching), 2) if searching else 0.0,
        "zero_result_rate": pct(zero, len(searches)), "redacted": redacted,
        "to_school_open_rate": pct(converted, len(searching)),
        "top_terms": [render(t) for t in ranked[:TOP]],
        "zero_result_terms": [render(t) for t in ranked if t["zero_results"]][:TOP],
    }


def filters(events: Iterable[AnalyticsEvent]) -> dict[str, Any]:
    names: Counter[str] = Counter()
    values: dict[str, Counter[str]] = defaultdict(Counter)
    for event in events:
        if event.name == "filter_change":
            name = str(prop(event, "filter", "?"))
            names[name] += 1
            values[name][str(prop(event, "value", "all"))] += 1
    return {"usage": table(names, label="filter"),
            "values": {name: table(counter, limit=10, label="value") for name, counter in values.items()}}


def features(events: Sequence[AnalyticsEvent]) -> dict[str, Any]:
    counts: Counter[str] = Counter()
    visitors: dict[str, set[str]] = defaultdict(set)
    clicks: dict[tuple[str, str], dict[str, Any]] = {}
    rage: Counter[str] = Counter()
    for event in events:
        if event.name in FEATURE_EVENTS:
            counts[event.name] += 1
            visitors[event.name].add(event.visitor_id)
        elif event.name == "click":
            key = (str(prop(event, "target", "?")), str(prop(event, "label", "")))
            entry = clicks.setdefault(key, {"target": key[0], "label": key[1], "clicks": 0, "visitors": set()})
            entry["clicks"] += 1
            entry["visitors"].add(event.visitor_id)
        elif event.name == "rage_click":
            rage[str(prop(event, "target", "?"))] += 1
    top_clicks = sorted(clicks.values(), key=lambda c: -c["clicks"])[:TOP]
    return {
        "usage": [{"feature": name, "count": counts[name], "visitors": len(visitors[name])}
                  for name in sorted(counts, key=lambda n: -counts[n])],
        "top_clicks": [{"target": c["target"], "label": c["label"], "clicks": c["clicks"],
                        "visitors": len(c["visitors"])} for c in top_clicks],
        "rage_clicks": table(rage, label="target", limit=10),
    }


FUNNEL_STEPS = (
    ("visit", "進站", lambda e: e.name == "page_view"),
    ("school_open", "打開學校頁", lambda e: e.name == "school_open"),
    ("commit", "開始規劃（收藏、規劃、文件、顧問、日曆）",
     lambda e: (e.name == "favorite_toggle" and prop(e, "saved") is True) or e.name in COMMIT_EVENTS),
    ("auth_start", "開始登入", lambda e: e.name == "auth_start"),
    ("auth_success", "登入成功", lambda e: e.name == "auth_success"),
    ("activated", "登入後開始規劃",
     lambda e: (e.name == "favorite_toggle" and prop(e, "saved") is True) or e.name in COMMIT_EVENTS),
)


def funnel(events: Sequence[AnalyticsEvent]) -> list[dict[str, Any]]:
    by_visitor: dict[str, list[AnalyticsEvent]] = defaultdict(list)
    for event in events:
        by_visitor[event.visitor_id].append(event)
    reached = [0] * len(FUNNEL_STEPS)
    for visitor_events in by_visitor.values():
        cursor: datetime | None = None
        for index, (_, _, matches) in enumerate(FUNNEL_STEPS):
            found = next((e.occurred_at for e in visitor_events
                          if matches(e) and (cursor is None or e.occurred_at >= cursor)), None)
            if found is None:
                break
            reached[index] += 1
            cursor = found
    rows = []
    for index, (key, label, _) in enumerate(FUNNEL_STEPS):
        previous = reached[index - 1] if index else reached[0]
        rows.append({"step": key, "label": label, "visitors": reached[index],
                     "pct_of_first": pct(reached[index], reached[0]),
                     "pct_of_previous": pct(reached[index], previous) if index else 100.0 if reached[0] else 0.0,
                     "dropped": (previous - reached[index]) if index else 0})
    return rows


def signup(events: Sequence[AnalyticsEvent], server: Sequence[AnalyticsEvent],
           sessions: Sequence[Session]) -> dict[str, Any]:
    started = [e for e in events if e.name == "auth_start"]
    succeeded = [e for e in events if e.name == "auth_success"]
    new_accounts = [e for e in succeeded if prop(e, "new_account") is True]
    first_seen: dict[str, datetime] = {}
    for session in sessions:
        first_seen.setdefault(session.visitor_id, session.first.occurred_at)
    days_to_signup = [
        (e.occurred_at - first_seen[e.visitor_id]).total_seconds() / 86400
        for e in new_accounts if e.visitor_id in first_seen
    ]
    created = [e for e in server if e.name == "account_created"]
    return {
        "dialog_opens": sum(e.name == "auth_dialog_open" for e in events),
        "starts": len(started),
        "starts_by_provider": table(Counter(str(prop(e, "provider", "?")) for e in started), label="provider"),
        "successes": len(succeeded),
        "new_accounts_seen_by_browser": len(new_accounts),
        "start_to_success_rate": pct(len(succeeded), len(started)),
        "median_days_first_visit_to_signup": round(statistics.median(days_to_signup), 2) if days_to_signup else None,
        "school_chosen": table(Counter(str(prop(e, "school", "?")) for e in events if e.name == "school_choose"),
                               label="school"),
        "accounts_created_by_server": len(created),
        "accounts_created_by_school_basis": table(Counter(e.school_basis or "none" for e in created), label="basis"),
        "accounts_created_by_provider": table(Counter(str(prop(e, "provider", "?")) for e in created),
                                              label="provider"),
        "logins_by_server": sum(e.name == "account_login" for e in server),
    }


def retention(events: Sequence[AnalyticsEvent], end: datetime) -> dict[str, Any]:
    active: dict[str, set[date]] = defaultdict(set)
    cohort: dict[str, date] = {}
    for event in events:
        day = local(event.occurred_at).date()
        active[event.visitor_id].add(day)
        if event.new_visitor:
            cohort[event.visitor_id] = min(day, cohort.get(event.visitor_id, day))
    last_day = local(end - timedelta(microseconds=1)).date()
    summary = {}
    for n in (1, 7, 14, 30):
        eligible = [v for v, first in cohort.items() if first + timedelta(days=n) <= last_day]
        kept = [v for v in eligible if cohort[v] + timedelta(days=n) in active[v]]
        summary[f"day_{n}"] = {"cohort": len(eligible), "retained": len(kept), "rate": pct(len(kept), len(eligible))
                               if eligible else None}
    weeks: dict[date, list[str]] = defaultdict(list)
    for visitor, first in cohort.items():
        weeks[first - timedelta(days=first.weekday())].append(visitor)
    weekly = []
    for week_start in sorted(weeks):
        members = weeks[week_start]
        row: dict[str, Any] = {"week_start": week_start.isoformat(), "size": len(members)}
        for n in (1, 7, 30):
            eligible = [v for v in members if cohort[v] + timedelta(days=n) <= last_day]
            kept = sum(cohort[v] + timedelta(days=n) in active[v] for v in eligible)
            row[f"day_{n}"] = pct(kept, len(eligible)) if eligible else None
        weekly.append(row)
    return {"summary": summary, "weekly": weekly,
            "note": "只計算「首次造訪」的訪客；樣本天數不足的欄位顯示為空。"}


def engagement(sessions: Sequence[Session]) -> dict[str, Any]:
    scroll = [number(e, "max_scroll_pct") for s in sessions for e in s.events if e.name == "engagement"]
    scroll = [value for value in scroll if value is not None]
    by_device: dict[str, list[float]] = defaultdict(list)
    for session in sessions:
        by_device[session.first.device_class or "(未知)"].append(session.engaged_ms / 1000)
    return {
        "session_duration": bucketed((s.duration_s for s in sessions), DURATION_BUCKETS, "10 分以上"),
        "pages_per_session": bucketed((len(s.page_views) for s in sessions), PAGES_BUCKETS, "10 頁以上"),
        "scroll_depth": bucketed(scroll, ((25, "0–25%"), (50, "25–50%"), (75, "50–75%")), "75–100%"),
        "engaged_seconds_by_device": [
            {"device": device, "avg_engaged_seconds": round(statistics.fmean(values), 1), "sessions": len(values)}
            for device, values in sorted(by_device.items())
        ],
    }


def performance(events: Sequence[AnalyticsEvent]) -> dict[str, Any]:
    values: dict[str, list[float]] = defaultdict(list)
    by_device_lcp: dict[str, list[float]] = defaultdict(list)
    by_route_lcp: dict[str, list[float]] = defaultdict(list)
    for event in events:
        if event.name != "web_vitals":
            continue
        metric = str(prop(event, "metric", "")).lower()
        value = number(event, "value")
        if not metric or value is None:
            continue
        values[metric].append(value)
        if metric == "lcp":
            by_device_lcp[event.device_class or "(未知)"].append(value)
            by_route_lcp[event.route or "home"].append(value)
    rows = []
    for metric in sorted(values):
        data = values[metric]
        good, poor = VITAL_THRESHOLDS.get(metric, (None, None))
        rows.append({
            "metric": metric, "samples": len(data), "p50": quantile(data, 0.5), "p75": quantile(data, 0.75),
            "p95": quantile(data, 0.95),
            "good_share": pct(sum(v <= good for v in data), len(data)) if good is not None else None,
            "poor_share": pct(sum(v > poor for v in data), len(data)) if poor is not None else None,
        })
    return {
        "vitals": rows,
        "lcp_p75_by_device": [{"device": d, "samples": len(v), "p75": quantile(v, 0.75)}
                              for d, v in sorted(by_device_lcp.items())],
        "slowest_routes_lcp_p75": sorted(
            ({"route": r, "samples": len(v), "p75": quantile(v, 0.75)} for r, v in by_route_lcp.items() if len(v) >= 3),
            key=lambda row: -(row["p75"] or 0))[:10],
    }


def normalize_message(message: str) -> str:
    return re.sub(r"\d+", "N", message)[:120]


def errors(events: Sequence[AnalyticsEvent], sessions: Sequence[Session]) -> dict[str, Any]:
    js = [e for e in events if e.name in {"js_error", "unhandled_rejection"}]
    api = [e for e in events if e.name == "api_error"]
    affected = {e.session_id for e in js}
    messages: dict[str, dict[str, Any]] = {}
    for event in js:
        key = normalize_message(str(prop(event, "message", "")))
        entry = messages.setdefault(key, {"message": key, "count": 0, "sessions": set(), "routes": Counter()})
        entry["count"] += 1
        entry["sessions"].add(event.session_id)
        entry["routes"][event.route or "home"] += 1
    return {
        "js_errors": len(js),
        "sessions_affected": len(affected),
        "sessions_affected_share": pct(len(affected), len(sessions)),
        "top_messages": [
            {"message": m["message"], "count": m["count"], "sessions": len(m["sessions"]),
             "top_route": m["routes"].most_common(1)[0][0]}
            for m in sorted(messages.values(), key=lambda m: -m["count"])[:TOP]
        ],
        "by_route": table(Counter(e.route or "home" for e in js), label="route", limit=10),
        "failing_requests_seen_by_browser": table(
            Counter(f"{prop(e, 'status', 'network')} {prop(e, 'path', '?')}" for e in api), label="request", limit=10),
    }


def estimate_latency(row_buckets: Sequence[int], q: float) -> float | None:
    total = sum(row_buckets)
    if not total:
        return None
    target = total * q
    seen = 0
    for count, (low, high) in zip(row_buckets, LATENCY_BOUNDS):
        if seen + count >= target and count:
            return round(low + (high - low) * ((target - seen) / count), 1)
        seen += count
    return float(LATENCY_BOUNDS[-1][1])


def api_health(rows: Sequence[ApiMetricRow]) -> dict[str, Any]:
    per_route: dict[str, dict[str, Any]] = {}
    per_day: dict[date, Counter[str]] = defaultdict(Counter)
    classes: Counter[str] = Counter()
    for row in rows:
        entry = per_route.setdefault(row.route, {
            "route": row.route, "requests": 0, "total_ms": 0, "max_ms": 0, "e5xx": 0, "e4xx": 0,
            "buckets": [0, 0, 0, 0, 0]})
        entry["requests"] += row.request_count
        entry["total_ms"] += row.total_ms
        entry["max_ms"] = max(entry["max_ms"], row.max_ms)
        entry["e5xx"] += row.request_count if row.status_class == "5xx" else 0
        entry["e4xx"] += row.request_count if row.status_class == "4xx" else 0
        for index, value in enumerate((row.le_100, row.le_300, row.le_1000, row.le_3000, row.gt_3000)):
            entry["buckets"][index] += value
        classes[row.status_class] += row.request_count
        day = local(row.bucket_hour).date()
        per_day[day]["requests"] += row.request_count
        per_day[day]["errors_5xx"] += row.request_count if row.status_class == "5xx" else 0
    total_requests = sum(e["requests"] for e in per_route.values())
    rendered = []
    for entry in per_route.values():
        buckets = entry["buckets"]
        rendered.append({
            "route": entry["route"], "requests": entry["requests"],
            "avg_ms": round(entry["total_ms"] / entry["requests"], 1) if entry["requests"] else None,
            "p50_ms_estimate": estimate_latency(buckets, 0.5), "p95_ms_estimate": estimate_latency(buckets, 0.95),
            "max_ms": entry["max_ms"], "slow_share": pct(buckets[3] + buckets[4], entry["requests"]),
            "error_5xx": entry["e5xx"], "error_4xx": entry["e4xx"],
            "error_5xx_rate": pct(entry["e5xx"], entry["requests"]),
        })
    rendered.sort(key=lambda r: -r["requests"])
    days = sorted(per_day)
    return {
        "total_requests": total_requests,
        "status_classes": table(classes, total_requests, label="status"),
        "routes": rendered[:30],
        "slowest_routes": sorted((r for r in rendered if r["requests"] >= 5),
                                 key=lambda r: -(r["p95_ms_estimate"] or 0))[:10],
        "daily": {"days": [d.isoformat() for d in days],
                  "requests": [per_day[d]["requests"] for d in days],
                  "errors_5xx": [per_day[d]["errors_5xx"] for d in days]},
        "note": "延遲百分位數由區間計數推估（<100、<300、<1000、<3000、≥3000 毫秒），僅供比較。",
    }


def community(server: Sequence[AnalyticsEvent]) -> dict[str, Any]:
    posts = [e for e in server if e.name == "post_created"]
    comments = [e for e in server if e.name == "comment_created"]
    return {
        "posts": len(posts), "comments": len(comments),
        "posts_by_board": table(Counter(str(prop(e, "board", "?")) for e in posts), label="board"),
        "comments_by_board": table(Counter(str(prop(e, "board", "?")) for e in comments), label="board"),
        "posts_by_identity": table(Counter(str(prop(e, "identity_mode", "?")) for e in posts), label="identity"),
        "posts_by_account_verification": table(Counter(e.school_basis or "none" for e in posts), label="basis"),
    }


# --------------------------------------------------------------------------- entry point


def build_report(
    events: Sequence[AnalyticsEvent],
    api_rows: Sequence[ApiMetricRow],
    *,
    start: datetime,
    end: datetime,
    previous_events: Sequence[AnalyticsEvent] = (),
    include_bots: bool = False,
    home_school: str | None = None,
    school_countries: Mapping[str, str] | None = None,
    truncated: bool = False,
    now: datetime | None = None,
) -> dict[str, Any]:
    def visible(rows: Iterable[AnalyticsEvent]) -> list[AnalyticsEvent]:
        return [e for e in rows if not e.is_server and (include_bots or not e.is_bot)
                and (not home_school or e.home_school == home_school)]

    client = visible(events)
    server = [e for e in events if e.is_server]
    sessions = build_sessions(client)
    current = overview(sessions)
    previous = overview(build_sessions(visible(previous_events)))
    bots = sum(1 for e in events if not e.is_server and e.is_bot)
    times = [e.occurred_at for e in client]
    return {
        "generated_at": (now or datetime.now(timezone.utc)).isoformat(),
        "range": {"start": start.isoformat(), "end": end.isoformat(), "timezone": "Asia/Taipei",
                  "days": max(1, round((end - start).total_seconds() / 86400))},
        "filters": {"include_bots": include_bots, "home_school": home_school or ""},
        "data_quality": {
            "client_events": len(client), "server_events": len(server),
            "bot_events_in_range": bots, "bots_excluded": not include_bots,
            "truncated": truncated,
            "first_event_at": min(times).isoformat() if times else None,
            "last_event_at": max(times).isoformat() if times else None,
        },
        "overview": {"current": current, "previous": previous, "change_pct": overview_change(current, previous)},
        "timeseries": timeseries(sessions, server, start, end),
        "heatmap": heatmap(client),
        "pages": pages(sessions),
        "traffic": traffic(sessions),
        "audience": audience(sessions),
        "schools": schools(client, school_countries or {}),
        "search": search(sessions),
        "filters_used": filters(client),
        "features": features(client),
        "funnel": funnel(client),
        "signup": signup(client, server, sessions),
        "retention": retention(client, end),
        "engagement": engagement(sessions),
        "performance": performance(client),
        "errors": errors(client, sessions),
        "api": api_health(api_rows),
        "community": community(server),
    }


def events_to_csv_rows(events: Iterable[AnalyticsEvent]) -> list[list[str]]:
    """Rows for the raw export. Cells that a spreadsheet would run as a formula are neutralised."""
    import json

    def safe(value: Any) -> str:
        text = "" if value is None else str(value)
        return "'" + text if text[:1] in {"=", "+", "-", "@", "\t", "\r"} else text

    header = ["time_taipei", "name", "route", "viewing_school", "visitor_id", "session_id", "device", "browser",
              "os", "country", "language", "referrer_host", "utm_source", "utm_medium", "utm_campaign",
              "signed_in", "new_visitor", "is_bot", "props_json"]
    rows = [header]
    for e in events:
        rows.append([safe(v) for v in (
            local(e.occurred_at).strftime("%Y-%m-%d %H:%M:%S"), e.name, e.route, e.home_school, e.visitor_id,
            e.session_id, e.device_class, e.browser, e.os, e.country, e.language, e.referrer_host, e.utm_source,
            e.utm_medium, e.utm_campaign, e.signed_in, e.new_visitor, e.is_bot,
            json.dumps(e.props, ensure_ascii=False, sort_keys=True))])
    return rows
