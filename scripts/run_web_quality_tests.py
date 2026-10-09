"""Run every collected test once, keeping browser module fixtures together.

Browser files are balanced by collected case count. Other tests run in shard 0.
No tests or skip markers are added or removed. Each case's elapsed time and
failure are printed immediately so a timeout retains useful evidence.
"""
from __future__ import annotations

import argparse
from collections import Counter
import json
import os
from pathlib import Path
import subprocess
import sys
import time

import pytest


def partition(shards: int) -> tuple[list[list[str]], dict]:
    collected = subprocess.run(
        [sys.executable, "-m", "pytest", "--collect-only", "-q"],
        text=True, capture_output=True,
    )
    if collected.returncode:
        print(collected.stdout, flush=True)
        print(collected.stderr, file=sys.stderr, flush=True)
        raise SystemExit(collected.returncode)
    nodeids = [line for line in collected.stdout.splitlines() if line.startswith("tests/") and "::" in line]
    if not nodeids or len(nodeids) != len(set(nodeids)):
        raise RuntimeError("Test collection is empty or contains duplicate node IDs")
    counts = Counter(node.split("::", 1)[0] for node in nodeids)
    groups: list[list[str]] = [[] for _ in range(shards)]
    browser_counts = [0] * shards
    browser_files = [path for path in counts if path.startswith("tests/e2e/")]
    for path in sorted(browser_files, key=lambda path: (-counts[path], path)):
        target = min(range(shards), key=lambda index: (browser_counts[index], index))
        groups[target].append(path)
        browser_counts[target] += counts[path]
    groups[0].extend(path for path in counts if path not in browser_files)
    for group in groups:
        group.sort()
    assigned = [path for group in groups for path in group]
    if len(assigned) != len(set(assigned)) or set(assigned) != set(counts):
        raise RuntimeError("Shard assignments omitted or duplicated a collected test file")
    return groups, dict(total_cases=len(nodeids), total_files=len(counts),
        browser_cases_per_shard=browser_counts,
        case_counts_per_shard=[sum(counts[path] for path in group) for group in groups],
        files_per_shard=groups, coverage="all collected files; no new exclusions")


class Progress:
    def pytest_runtest_logreport(self, report):
        if report.when == "call" or report.failed or report.skipped:
            print(f"WEB_CASE {report.nodeid} {report.when} {report.outcome} {report.duration:.3f}s", flush=True)
            if report.failed:
                print(str(report.longrepr), flush=True)


def use_blocking_output() -> None:
    """Long pytest failures must back-pressure the CI pipe instead of EAGAIN.

    Tee output can exceed the nonblocking pipe buffer. Preserve every byte and
    let the reader drain it; an evidence logger must not interrupt pytest.
    """
    for stream in (sys.stdout, sys.stderr):
        os.set_blocking(stream.fileno(), True)


def main() -> int:
    use_blocking_output()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--shard", type=int, required=True)
    parser.add_argument("--shards", type=int, default=4)
    parser.add_argument("--junitxml", type=Path)
    parser.add_argument("--list-only", action="store_true")
    parser.add_argument("--evidence-dir", type=Path)
    args = parser.parse_args()
    if args.shards < 1 or not 0 <= args.shard < args.shards:
        parser.error("shard must be within the requested shard count")
    groups, manifest = partition(args.shards)
    print(json.dumps(dict(shard=args.shard, **manifest), ensure_ascii=False), flush=True)
    if args.evidence_dir:
        args.evidence_dir.mkdir(parents=True, exist_ok=True)
        (args.evidence_dir / "partition.json").write_text(json.dumps(dict(shard=args.shard, **manifest), indent=2) + "\n")
        collected = subprocess.run([sys.executable, "-m", "pytest", *groups[args.shard], "--collect-only", "-q"], text=True, capture_output=True, check=True)
        nodes = [line for line in collected.stdout.splitlines() if line.startswith("tests/") and "::" in line]
        assert len(nodes) == manifest["case_counts_per_shard"][args.shard]
        (args.evidence_dir / "collect-nodeids.txt").write_text("\n".join(nodes) + "\n")
    if args.list_only:
        return 0
    command = [*groups[args.shard], "-vv", "--tb=short", "--durations=25", "--capture=tee-sys"]
    if args.junitxml:
        args.junitxml.parent.mkdir(parents=True, exist_ok=True)
        command.append(f"--junitxml={args.junitxml}")
    started = time.monotonic()
    code = pytest.main(command, plugins=[Progress()])
    print(f"WEB_SHARD {args.shard} exit={code} elapsed={time.monotonic()-started:.3f}s", flush=True)
    if args.evidence_dir:
        (args.evidence_dir / "result.json").write_text(json.dumps(dict(shard=args.shard, exit_code=int(code), elapsed_seconds=time.monotonic()-started, tested_commit=subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()), indent=2) + "\n")
    return int(code)


if __name__ == "__main__":
    raise SystemExit(main())
