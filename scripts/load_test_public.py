"""Paced public API traffic. Run on a separate machine against a staging site.

No login credentials, writes, uploads, PDFs, or static assets are exercised. This
is a public API capacity check, not proof that 1,000 students can finish applying.
Requires httpx (included in the project's dev dependencies).
"""
from __future__ import annotations

import argparse
import asyncio
from collections import Counter
import json
import math
from pathlib import Path
import time
from urllib.parse import quote, urlsplit

import httpx


def percentile(values: list[float], fraction: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    return round(ordered[max(0, math.ceil(len(ordered) * fraction) - 1)], 2)


async def run(args: argparse.Namespace, *, transport=None) -> dict:
    started = time.perf_counter()
    deadline = started + args.duration
    routes: dict[str, dict] = {}
    latencies: list[float] = []
    started_users = 0
    transferred = 0
    schools = args.school or ["長庚大學"]
    # No login credentials are supplied. This profile stays public.
    async with httpx.AsyncClient(
        timeout=args.timeout,
        limits=httpx.Limits(max_connections=args.users, max_keepalive_connections=args.users),
        transport=transport,
        headers={"User-Agent": "UniWay-Capacity-Check/1.0"},
    ) as client:
        async def fetch(path: str, *, html: bool = False) -> None:
            nonlocal transferred
            route = path.split("?", 1)[0]
            row = routes.setdefault(route, {"requests": 0, "errors": 0, "statuses": Counter(), "latencies": []})
            request_started = time.perf_counter()
            try:
                response = await client.get(args.base_url.rstrip("/") + path)
                transferred += len(response.content)
                expected_type = "text/html" if html else "application/json"
                error = response.status_code != 200 or expected_type not in response.headers.get("content-type", "")
                outcome = str(response.status_code) if not error else f"{response.status_code}/unexpected"
            except httpx.HTTPError as exc:
                error, outcome = True, type(exc).__name__
            elapsed_ms = (time.perf_counter() - request_started) * 1000
            row["requests"] += 1
            row["errors"] += int(error)
            row["statuses"][outcome] += 1
            row["latencies"].append(elapsed_ms)
            latencies.append(elapsed_ms)

        async def visitor(index: int) -> None:
            nonlocal started_users
            await asyncio.sleep(index * args.ramp_seconds / args.users)
            if time.perf_counter() >= deadline:
                return
            started_users += 1
            school = quote(schools[index % len(schools)], safe="")
            for path in ("/", "/universities", "/ai/status"):
                if time.perf_counter() >= deadline:
                    return
                await fetch(path, html=path == "/")
            while time.perf_counter() < deadline:
                # A simulated action makes three requests, then the student reads.
                for path in ("/student-dashboard", "/documents", "/deadlines"):
                    if time.perf_counter() >= deadline:
                        return
                    await fetch(f"{path}?school={school}")
                remaining = deadline - time.perf_counter()
                if remaining > 0:
                    await asyncio.sleep(min(args.think_seconds, remaining))

        await asyncio.gather(*(visitor(index) for index in range(args.users)))

    elapsed = time.perf_counter() - started
    errors = sum(row["errors"] for row in routes.values())
    requests = len(latencies)
    p95 = percentile(latencies, 0.95)
    checks = {
        "all_users_started": started_users == args.users,
        "received_responses": requests > 0,
        "error_rate": requests > 0 and errors / requests <= args.max_error_rate,
        "p95_latency": p95 is not None and p95 <= args.p95_ms,
        "route_p95_latency": bool(routes) and all(
            percentile(row["latencies"], 0.95) <= args.p95_ms for row in routes.values()
        ),
    }
    return {
        "profile": "public APIs only; excludes assets, login, writes, uploads and document generation",
        "target": args.base_url,
        "users": args.users,
        "started_users": started_users,
        "schools": schools,
        "duration_seconds": args.duration,
        "elapsed_seconds_including_drain": round(elapsed, 2),
        "ramp_seconds": args.ramp_seconds,
        "think_seconds": args.think_seconds,
        "requests": requests,
        "requests_per_second": round(requests / elapsed, 2),
        "errors": errors,
        "error_rate": round(errors / requests, 6) if requests else None,
        "response_body_bytes": transferred,
        "p50_ms": percentile(latencies, 0.5),
        "p95_ms": p95,
        "p99_ms": percentile(latencies, 0.99),
        "thresholds": {"p95_ms": args.p95_ms, "max_error_rate": args.max_error_rate},
        "checks": checks,
        "passed": all(checks.values()),
        "routes": {route: {
            "requests": row["requests"], "errors": row["errors"], "statuses": dict(row["statuses"]),
            "p95_ms": percentile(row["latencies"], 0.95),
        } for route, row in routes.items()},
    }


def arguments(argv=None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", required=True, help="Staging URL; includes no credentials or query string")
    parser.add_argument("--users", type=int, default=10)
    parser.add_argument("--duration", type=float, default=60)
    parser.add_argument("--ramp-seconds", type=float, default=10)
    parser.add_argument("--think-seconds", type=float, default=10)
    parser.add_argument("--timeout", type=float, default=15)
    parser.add_argument("--school", action="append", help="Repeat to distribute visitors across home universities")
    parser.add_argument("--p95-ms", type=float, default=2000)
    parser.add_argument("--max-error-rate", type=float, default=0.01)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    url = urlsplit(args.base_url)
    if url.scheme not in {"http", "https"} or not url.hostname or url.username or url.password or url.query or url.fragment:
        parser.error("--base-url must be an http(s) URL without credentials, query or fragment")
    for name in ("duration", "think_seconds", "timeout", "p95_ms"):
        value = getattr(args, name)
        if not math.isfinite(value) or value <= 0:
            parser.error(f"--{name.replace('_', '-')} must be finite and positive")
    if not 1 <= args.users <= 2000:
        parser.error("--users must be between 1 and 2000")
    if not math.isfinite(args.ramp_seconds) or not 0 <= args.ramp_seconds < args.duration:
        parser.error("--ramp-seconds must be nonnegative and smaller than --duration")
    if not math.isfinite(args.max_error_rate) or not 0 <= args.max_error_rate <= 1:
        parser.error("--max-error-rate must be between 0 and 1")
    return args


def main() -> int:
    args = arguments()
    report = asyncio.run(run(args))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({key: report[key] for key in ("users", "requests", "requests_per_second", "error_rate", "p95_ms", "passed")}, ensure_ascii=False))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
