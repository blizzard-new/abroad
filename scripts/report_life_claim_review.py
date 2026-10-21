"""Bind the inspected profile-to-life evidence promotion to original field values."""
from __future__ import annotations
import argparse
from collections import Counter
import gzip
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from exchange_info.generated_content_review import digest, load_manifest
from exchange_info.life_claim_review import profile_claim_key
from report_generated_content_review import report as report_generated
from university_review_ledger import append_decisions as append_review_decisions


def report(append_decisions=False, *, round_id=21):
    life_result = report_generated(append_decisions, round_id=round_id)
    manifest = load_manifest(ROOT, round_id=round_id)
    keys = set(manifest["runtime_index"]["profile_claim_keys"])
    decisions = {}
    with gzip.open(ROOT / "output/data-verification-20261021/baseline/records.jsonl.gz", "rt", encoding="utf8") as stream:
        for line in stream:
            record = json.loads(line)
            if record["kind"] != "destination" or record["home_id"] not in manifest["schools"]:
                continue
            scope = manifest["schools"][record["home_id"]]
            for field, locator in scope["reviewed_line_ranges"]["profile_fields"].items():
                value = record["data"].get(field, "")
                if profile_claim_key(record["data"], field, value) not in keys:
                    raise ValueError(f"Unbound profile claim: {record['record_id']} {field}")
                pointer = "/" + field
                rid = digest([f"life-profile-promotion-round{round_id}", record["record_id"], pointer, scope["code_sha256"]])[:28]
                decisions[rid] = {
                    "review_id": rid, "base_record_id": record["record_id"], "pointer": pointer,
                    "base_value": value, "base_value_sha256": digest(value), "base_status": "needs_confirmation",
                    "expected_value_or_interpretation": "原逐校摘要含範本、母校規則或未核對摘錄；不能僅依official_標記自動升格為生活證據。",
                    "reason": "已核對建置程式欄位資料流及原始runtime基準值；限制的是自動證據升格，不是宣告所有摘要內容為假。逐校原文仍須查核。",
                    "source_url": f"https://github.com/blizzard-new/abroad/blob/{manifest['base_commit']}/{scope['code_path']}",
                    "source_sha256": scope["code_sha256"], "source_locator": f"profile generation field lines {locator}",
                    "retrieved_at": manifest["reviewed_at"], "reviewed_at": manifest["reviewed_at"],
                    "source_type": "repository_implementation_at_original_baseline",
                    "method": "repository_data_flow_review_not_external_fact_verification",
                    "baseline_inventory": "output/data-verification-20261021/baseline",
                    "correction_scope": "Exact field-value gate in life_context._profile_evidence; destination display and other fields still require external review.",
                    "whole_record_verified": False,
                }
    added = append_review_decisions(ROOT / "docs/data-verification-20261021", decisions.values()) if append_decisions else 0
    return {"life": life_result, "profile_promotion": {"decisions": len(decisions), "added": added,
        "statuses": dict(Counter(row["base_status"] for row in decisions.values()))}}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--append-decisions", action="store_true")
    parser.add_argument("--round-id", type=int, choices=(21, 22), default=21)
    args = parser.parse_args()
    print(json.dumps(report(args.append_decisions, round_id=args.round_id), ensure_ascii=False))
