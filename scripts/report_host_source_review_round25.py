"""Bind the scoped host review to original exposed fields, without full-record claims."""
from __future__ import annotations

import argparse
from collections import Counter
import gzip
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from exchange_info.generated_content_review import digest
from exchange_info.host_source_review_round25 import load_manifest, pointer_parent
from university_review_ledger import append_decisions


def report(append=False):
    manifest = load_manifest(ROOT)
    receipts = {r["url"]: r for r in manifest["sources"]}
    filenames = {"partner": "partners.jsonl", "workflow": "application_workflows.jsonl",
                 "destination": "destination_profiles.jsonl"}
    scopes = {(r["home_id"], r["school_name"], Path(r["file"]).name): r for r in manifest["rows"]}
    inventory = "output/data-verification-20261021/baseline"
    decisions, unbound = [], []
    with gzip.open(ROOT / inventory / "records.jsonl.gz", "rt", encoding="utf8") as stream:
        for line in stream:
            record = json.loads(line)
            scope = scopes.get((record["home_id"], record["data"].get("school_name"), filenames.get(record["kind"])))
            if scope is None:
                continue
            for patch in scope["patches"]:
                try:
                    parent, key = pointer_parent(record["data"], patch["pointer"])
                    value = parent[key]
                except (KeyError, IndexError, TypeError, ValueError):
                    unbound.append({"file": scope["file"], "pointer": patch["pointer"],
                        "reason": "New scoped field or raw-only field absent from original runtime census; no original value invented."})
                    continue
                receipt = receipts[patch["source_url"]]
                status = ("contradicted" if scope["home_id"] == "scu" and "日語密集課程" in str(value)
                          else "needs_confirmation")
                decisions.append({
                    "review_id": digest(["host-source-review-round25", record["record_id"], patch["pointer"]])[:28],
                    "base_record_id": record["record_id"], "pointer": patch["pointer"],
                    "base_value": value, "base_value_sha256": digest(value), "base_status": status,
                    "expected_value_or_interpretation": patch["value"], "reason": patch["reason"],
                    "source_url": receipt["url"], "source_sha256": receipt["sha256"],
                    "source_locator": patch["source_locator"], "retrieved_at": receipt["completed_at"],
                    "reviewed_at": manifest["reviewed_at"], "source_type": "official_host_and_mother_sources",
                    "method": "bounded_admission_scope_comparison", "baseline_inventory": inventory,
                    "whole_record_verified": False,
                    "additional_sources": [{"url": r["url"], "sha256": r["sha256"]} for r in manifest["sources"]],
                })
    added = append_decisions(ROOT / "docs/data-verification-20261021", decisions) if append else 0
    return {"decisions": len(decisions), "added": added,
            "statuses": dict(Counter(d["base_status"] for d in decisions)), "unbound_fields": unbound}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--append-decisions", action="store_true")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = report(args.append_decisions)
    if args.output:
        args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", "utf8")
    print(json.dumps({k: v if k != "unbound_fields" else len(v) for k, v in result.items()}, ensure_ascii=False))
