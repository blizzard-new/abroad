"""Fill a throw-away data directory with made-up analytics so the dashboard can be previewed.

Everything here is invented. It refuses to write into a directory that already holds analytics, so it
cannot mix demo rows into real data:

    python scripts/seed_analytics_demo.py --data-dir C:/temp/analytics-demo
"""
from __future__ import annotations

import argparse
import random
import sys
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from exchange_info.analytics import AnalyticsEvent, ApiMetricRow, status_class  # noqa: E402
from exchange_info.analytics_repository import JsonlAnalyticsRepository  # noqa: E402

SCHOOLS = [
    ("明治大學 Meiji University", "日本"), ("佐賀大學", "日本"), ("林肯大學 Lincoln University", "紐西蘭"),
    ("里昂精英工程師學校", "法國"), ("柏林自由大學", "德國"), ("首爾大學", "韓國"), ("新加坡國立大學", "新加坡"),
    ("馬來亞大學 Universiti Malaya", "馬來西亞"), ("曼徹斯特大學", "英國"), ("昆士蘭大學", "澳洲"),
]
SEARCHES = [("日本", 40), ("英語授課", 22), ("學海惜珠", 12), ("德國", 11), ("法國", 9), ("韓國", 8), ("不扣學分", 0), ("便宜", 3)]
ROUTES = ["home", "partners:list", "partners:map", "school", "favorites", "overview", "guide", "advisor", "documents", "calendar"]
HOSTS = [("", "direct", 0.38), ("www.google.com", "search", 0.18), ("www.dcard.tw", "social", 0.14),
         ("l.instagram.com", "social", 0.09), ("www.ptt.cc", "social", 0.04), ("www.example.edu", "referral", 0.03)]
UAS = [("desktop", "Chrome", "Windows", 0.34), ("mobile", "Safari", "iOS", 0.30), ("mobile", "Chrome", "Android", 0.14),
       ("desktop", "Safari", "macOS", 0.09), ("mobile", "Line (in-app)", "iOS", 0.08), ("desktop", "Edge", "Windows", 0.05)]
HOURS = [0.2, 0.1, 0.05, 0.03, 0.03, 0.05, 0.1, 0.25, 0.4, 0.5, 0.55, 0.6, 0.7, 0.6, 0.55, 0.55, 0.6, 0.65, 0.75, 0.9, 1.0, 1.0, 0.7, 0.4]


def pick(rng: random.Random, rows):
    return rng.choices(rows, weights=[row[-1] for row in rows])[0]


def build(rng: random.Random, days: int, visitors: int, now: datetime) -> tuple[list[AnalyticsEvent], list[ApiMetricRow]]:
    events: list[AnalyticsEvent] = []
    first_seen: dict[str, datetime] = {}
    for index in range(visitors):
        vid = f"demo{index:05d}{uuid.uuid4().hex[:6]}"
        home = rng.choice(["長庚大學", "國立臺北大學"])
        host, _, _ = pick(rng, HOSTS)
        device, browser, os_name, _ = pick(rng, UAS)
        start_day = int(days * (1 - rng.random() ** 1.6))
        first = now - timedelta(days=start_day, hours=rng.choices(range(24), HOURS)[0], minutes=rng.randrange(60))
        first_seen[vid] = first
        returns = [first]
        for gap in (1, 3, 8, 20):
            if rng.random() < 0.22 / (1 + gap / 6) and first + timedelta(days=gap) < now:
                returns.append(first + timedelta(days=gap, hours=rng.randrange(-3, 3)))
        for visit, when in enumerate(returns):
            sid = f"s{uuid.uuid4().hex[:14]}"
            base = dict(visitor_id=vid, session_id=sid, device_class=device, browser=browser, os=os_name, country="TW",
                        language="zh-TW", timezone="Asia/Taipei", viewport="xs<480" if device == "mobile" else "lg<1440",
                        home_school=home, new_visitor=(visit == 0), referrer_host=host if visit == 0 else "",
                        utm_source="dcard" if host == "www.dcard.tw" and rng.random() < 0.3 else "",
                        utm_medium="social" if host == "www.dcard.tw" and rng.random() < 0.3 else "")
            clock = when

            def add(name, route="", seconds=0, **props):
                nonlocal clock
                clock = clock + timedelta(seconds=seconds)
                events.append(AnalyticsEvent(occurred_at=clock, name=name, route=route, props=props, **base))

            add("session_start")
            route = "home"
            add("page_view", route, entry=True)
            if rng.random() < 0.34:
                add("engagement", route, 4, active_ms=rng.randrange(1000, 8000), max_scroll_pct=rng.randrange(5, 40))
                continue
            for _ in range(rng.choice([1, 1, 2, 3, 4])):
                route = rng.choice(ROUTES)
                add("page_view", route, rng.randrange(8, 60))
                add("engagement", route, rng.randrange(5, 40), active_ms=rng.randrange(3000, 90000),
                    max_scroll_pct=rng.randrange(10, 100))
                if route.startswith("partners") and rng.random() < 0.5:
                    term, results = rng.choice(SEARCHES)
                    add("search", route, 6, q=term, q_len=len(term), results=results)
                    if rng.random() < 0.3:
                        add("filter_change", route, 3, filter=rng.choice(["country", "college", "degree"]), value="日本")
                if rng.random() < 0.5:
                    school, country = rng.choice(SCHOOLS[: rng.choice([3, 6, 10])])
                    add("school_open", "partners:list", 4, school=school, surface=rng.choice(["list", "map", "favorites"]))
                    if rng.random() < 0.28:
                        add("favorite_toggle", "school", 3, school=school, saved=True)
                    if rng.random() < 0.12:
                        add("outbound_click", "school", 5, host="www.example.edu", school=school)
            if rng.random() < 0.16:
                add("auth_dialog_open", route, 5)
                add("auth_start", route, 3, provider="google")
                if rng.random() < 0.8:
                    new = visit == 0 and rng.random() < 0.8
                    add("auth_success", "home", 8, new_account=new, school_basis=rng.choice(["school_email", "self_declared"]),
                        provider="google")
                    if new:
                        events.append(AnalyticsEvent(
                            occurred_at=clock, visitor_id="server", session_id="server", name="account_created",
                            props={"provider": "google"}, school_basis=rng.choice(["school_email", "self_declared"]),
                            signed_in=True, home_school=home))
                    if rng.random() < 0.6:
                        add("planning_action", "overview", 20, action="open-planning")
            if visit == 0:
                add("web_vitals", "home", 5, metric="lcp", value=rng.lognormvariate(7.7, 0.45))
                add("web_vitals", "home", 0, metric="ttfb", value=rng.lognormvariate(5.6, 0.5))
                add("web_vitals", "home", 0, metric="cls", value=round(rng.random() * 0.2, 3))
            if rng.random() < 0.03:
                add("js_error", route, 2, message=f"Cannot read properties of undefined (reading 'x{rng.randrange(3)}')")
    for _ in range(visitors // 25):
        events.append(AnalyticsEvent(
            occurred_at=now - timedelta(days=rng.random() * days), visitor_id="server", session_id="server",
            name="post_created", props={"board": rng.choice(["public-study-abroad", "cgu", "ntpu", "language-school"]),
                                        "identity_mode": rng.choice(["anonymous", "anonymous", "real_name"])},
            school_basis=rng.choice(["self_declared", "student_verified", "school_email"]), signed_in=True))
    metrics: dict[tuple, ApiMetricRow] = {}
    routes = [("/student-dashboard", 0.28), ("/destination-profiles", 0.16), ("/universities", 0.14), ("/coverage", 0.1),
              ("/community/posts", 0.1), ("/auth/session", 0.12), ("/product/entitlements", 0.06), ("(unmatched)", 0.04)]
    for hour in range(days * 24):
        stamp = (now - timedelta(hours=hour)).replace(minute=0, second=0, microsecond=0)
        load = HOURS[(stamp.hour + 8) % 24]
        for route, weight in routes:
            count = int(rng.random() * 40 * weight * load * 10)
            for _ in range(count):
                duration = rng.lognormvariate(4.8 if route != "/student-dashboard" else 5.8, 0.8)
                status = 500 if rng.random() < 0.004 else 404 if route == "(unmatched)" or rng.random() < 0.01 else 200
                key = (stamp, route, "GET", status_class(status))
                row = metrics.setdefault(key, ApiMetricRow(bucket_hour=stamp, route=route, method="GET", status_class=key[3]))
                row.request_count += 1
                row.total_ms += int(duration)
                row.max_ms = max(row.max_ms, int(duration))
                bucket = ("le_100" if duration < 100 else "le_300" if duration < 300 else "le_1000" if duration < 1000
                          else "le_3000" if duration < 3000 else "gt_3000")
                setattr(row, bucket, getattr(row, bucket) + 1)
    return events, list(metrics.values())


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, required=True)
    parser.add_argument("--days", type=int, default=45)
    parser.add_argument("--visitors", type=int, default=700)
    parser.add_argument("--seed", type=int, default=7)
    args = parser.parse_args()
    target = args.data_dir / "analytics"
    if target.exists() and any(target.iterdir()):
        print(f"{target} already holds analytics; refusing to add demo rows to it.", file=sys.stderr)
        return 1
    events, metrics = build(random.Random(args.seed), args.days, args.visitors, datetime.now(timezone.utc))
    repository = JsonlAnalyticsRepository(args.data_dir)
    for index in range(0, len(events), 5000):
        repository.record_events(events[index:index + 5000])
    repository.record_api_metrics(metrics)
    print(f"Wrote {len(events)} demo events and {len(metrics)} API rows to {target}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
