"""Acquire the reviewed seventh CCU batch through normal public HTTPS.

Existing receipts are preserved. Use an empty --output-dir to independently
reacquire public sources; response dates/content may differ from the snapshot.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import fetch_ccu_completion_sources as collector


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path)
    args = parser.parse_args()
    plan = json.loads((collector.BUNDLE / "completion-seventh-acquisition-plan.json").read_text())
    if args.output_dir:
        collector.BUNDLE = args.output_dir.resolve()
        collector.OUT = collector.BUNDLE / "completion_sources"
        collector.OUT.mkdir(parents=True, exist_ok=True)
    for source in plan["sources"]:
        sid = source["source_id"]
        if (collector.OUT / (sid + ".receipt.json")).exists():
            print(sid + " existing receipt preserved", flush=True)
            continue
        label = sid.split("-", 1)[1]
        record = collector.fetch(source["ccu_page"], label, source["source_url"])
        print(json.dumps({k: record.get(k) for k in ["source_id", "http_status", "error", "checked_at"]}), flush=True)


if __name__ == "__main__":
    main()
