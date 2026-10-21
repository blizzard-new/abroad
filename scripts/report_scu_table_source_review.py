"""Bind SCU source-table corrections to original runtime and raw catalog values."""
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
from exchange_info.host_source_review_round25 import pointer_parent
from exchange_info.scu_table_source_review import load_manifest
from university_review_ledger import append_decisions


def report(append=False, *, round_id=27):
    if round_id == 29:
        from exchange_info.scu_degree_source_review import load_manifest as load_degree_manifest
        manifest = load_degree_manifest(ROOT)
    elif round_id == 30:
        from exchange_info.scu_template_source_review import load_manifest as load_template_manifest
        manifest = load_template_manifest(ROOT)
    elif round_id == 27:
        manifest = load_manifest(ROOT)
    else:
        raise ValueError("Unsupported SCU source-review round")
    receipt = manifest["sources"][0]
    scopes = {(r["school_name"], Path(r["file"]).name): r for r in manifest["rows"]}
    kinds = {"partner": "partners.jsonl", "workflow": "application_workflows.jsonl", "destination": "destination_profiles.jsonl"}
    decisions, unbound = [], []
    for folder in ("baseline", "raw-catalog-baseline"):
        inventory = f"output/data-verification-20261021/{folder}"
        with gzip.open(ROOT / inventory / "records.jsonl.gz", "rt", encoding="utf8") as stream:
            for line in stream:
                record = json.loads(line)
                if record["home_id"] != "scu":
                    continue
                filename = record["kind"].removeprefix("raw:") if folder != "baseline" else kinds.get(record["kind"])
                scope = scopes.get((record["data"].get("school_name"), filename))
                if scope is None:
                    continue
                for patch in scope["patches"]:
                    try:
                        parent, key = pointer_parent(record["data"], patch["pointer"])
                        value = parent[key]
                    except (KeyError, IndexError, TypeError, ValueError):
                        unbound.append({"inventory": folder, "file": scope["file"], "pointer": patch["pointer"]})
                        continue
                    decisions.append({
                        "review_id": digest([f"scu-table-source-review-round{round_id}", record["record_id"], patch["pointer"]])[:28],
                        "base_record_id": record["record_id"], "pointer": patch["pointer"],
                        "base_value": value, "base_value_sha256": digest(value),
                        "base_status": patch["base_status"] if value in patch["expected_values"] else "needs_confirmation",
                        "expected_value_or_interpretation": patch["value"], "reason": patch["reason"],
                        "source_url": receipt["url"], "source_sha256": receipt["sha256"],
                        "source_locator": patch["source_locator"], "retrieved_at": receipt["completed_at"],
                        "reviewed_at": manifest["reviewed_at"],
                        "source_type": "original_repository_generator" if round_id == 30 else "official_mother_university_roster",
                        "method": {27: "manual_roster_scale_and_term_comparison", 29: "scoped_mother_roster_degree_line_comparison",
                                   30: "implementation_provenance_review"}[round_id],
                        "baseline_inventory": inventory,
                        "overlaps_runtime_census": folder != "baseline", "whole_record_verified": False,
                    })
    added = append_decisions(ROOT / "docs/data-verification-20261021", decisions) if append else 0
    return {"decisions": len(decisions), "added": added, "statuses": dict(Counter(d["base_status"] for d in decisions)),
            "unbound_fields": unbound, "inventories_overlap": True}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--append-decisions", action="store_true")
    parser.add_argument("--round-id", choices=(27, 29, 30), type=int, default=27)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = report(args.append_decisions, round_id=args.round_id)
    if args.output:
        args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", "utf8")
    print(json.dumps({k: v if k != "unbound_fields" else len(v) for k, v in result.items()}, ensure_ascii=False))
