"""Check that the official source links of the bundled 116 workflows still resolve.

Read-only: it requests each distinct URL once (HEAD, then GET when HEAD is refused) and
writes a CSV. A failure does not mean a rule changed; it means a human should open the
link before the workflow is reviewed. Some schools block automated requests, so a 403 or
a timeout is reported as "blocked/slow", not "broken".
"""
from __future__ import annotations

import argparse
import csv
import sys
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from exchange_info.storage import load_bundled_application_workflows  # noqa: E402

HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; exchange-info-link-check/1.0)"}


def check(url: str, timeout: float) -> tuple[str, str]:
    try:
        response = requests.head(url, headers=HEADERS, timeout=timeout, allow_redirects=True)
        if response.status_code in (403, 405, 501) or response.status_code >= 500:
            response = requests.get(url, headers=HEADERS, timeout=timeout, allow_redirects=True, stream=True)
            response.close()
        code = response.status_code
    except requests.exceptions.SSLError:
        return "ssl_error", "certificate problem"
    except requests.exceptions.ConnectionError as exc:
        return "unreachable", type(exc).__name__
    except requests.exceptions.Timeout:
        return "slow", "timeout"
    except requests.exceptions.RequestException as exc:
        return "error", type(exc).__name__
    if code < 400:
        return "ok", str(code)
    if code in (401, 403, 429):
        return "blocked", str(code)
    return "broken", str(code)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--home", default="長庚大學")
    parser.add_argument("--year", default="116")
    parser.add_argument("--csv", type=Path, required=True)
    parser.add_argument("--workers", type=int, default=16)
    parser.add_argument("--timeout", type=float, default=10.0)
    args = parser.parse_args()

    users: dict[str, set[str]] = defaultdict(set)
    for workflow in load_bundled_application_workflows():
        if workflow.home_university != args.home or workflow.academic_year != args.year:
            continue
        urls = [source.source_url for source in workflow.sources]
        for step in workflow.steps:
            urls += [*step.source_urls, *step.official_form_urls]
            urls += [value for value in (step.action_url, step.deadline_source_url) if value]
        for url in urls:
            if url.startswith(("http://", "https://")):
                users[url].add(workflow.school_name)
    print(f"{len(users)} distinct URLs from {len({s for v in users.values() for s in v})} schools")

    results: dict[str, tuple[str, str]] = {}
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = {pool.submit(check, url, args.timeout): url for url in users}
        for done, future in enumerate(as_completed(futures), start=1):
            results[futures[future]] = future.result()
            if done % 100 == 0:
                print(f"  checked {done}/{len(users)}")
    args.csv.parent.mkdir(parents=True, exist_ok=True)
    with args.csv.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["結果", "代碼", "網址", "使用的學校數", "學校（最多 3 所）"])
        for url, (status, detail) in sorted(results.items(), key=lambda item: (item[1][0] == "ok", item[1][0], item[0])):
            schools = sorted(users[url])
            writer.writerow([status, detail, url, len(schools), "；".join(schools[:3])])
    tally: dict[str, int] = defaultdict(int)
    for status, _ in results.values():
        tally[status] += 1
    print(dict(tally))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
