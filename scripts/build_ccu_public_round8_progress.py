"""Compare the scoped eighth public-source round to its immutable seventh head."""
from __future__ import annotations

import json
from collections import Counter

from fetch_ccu_completion_sources import BUNDLE as B


def read(name):
    return json.loads((B / name).read_text())


def main():
    baseline = read("completion-eighth-baseline.json")
    current = read("completion-reviewed-fields.json")["schools"]
    before = {r["ccu_page"]: r for r in baseline["prior_fields"]}
    readings = read("completion-eighth-reading-input.json")
    queue = read("completion-remaining-public-worklist.json")
    acquisition = read("completion-eighth-acquisition-plan.json")["sources"]
    extra_ids = {r["source_id"] for r in acquisition}
    original = [r for r in readings if r["source_id"] not in extra_ids]
    assert len(original) == baseline["source_input_count"] == 370
    assert len({r["source_id"] for r in original}) == 370
    assert len({(r["ccu_page"], r["content_hash"]) for r in original}) == 369
    changed = []
    for row in current:
        for scope in ["host_fields", "profile_fields", "general_campus_fields"]:
            for key, field in row[scope].items():
                old = before[row["ccu_page"]][scope][key]
                if any(field[k] != old[k] for k in ["value", "status", "evidence"]):
                    changed.append({"ccu_page": row["ccu_page"], "school_name": row["school_name"],
                                    "scope": scope, "field": key, "previous_status": old["status"],
                                    "status": field["status"], "value": field["value"],
                                    "evidence_source_ids": [e.get("source_id") for e in field["evidence"]]})
    pending = [s for r in queue["schools"] for s in r["sources"] if s["review_state"] == "readable_body_without_recorded_review"]
    receipts = [read("completion_sources/" + s["source_id"] + ".receipt.json") for s in acquisition]
    result = {
        "checked_at": "2026-10-11", "prior_commit": baseline["prior_commit"],
        "scope": "The 370 school URLs queued at the seventh handoff, with 369 distinct same-school raw bodies, plus directly discovered priority official children.",
        "original_urls_with_recorded_reading_extent": len(original),
        "original_distinct_raw_bodies": 369,
        "original_all_visible_read_records": sum(r.get("full_visible_read", False) for r in original),
        "original_partially_screened_records": sum(not r.get("full_visible_read", False) for r in original),
        "all_reading_records": len(readings),
        "all_visible_read_records": sum(r.get("full_visible_read", False) for r in readings),
        "all_visible_read_note": "Includes complete short indices, empty shells, error/sign-in messages and one visually inspected campus map; this is not a count of complete policy reviews.",
        "reading_dispositions": dict(Counter(r["disposition"] for r in readings)),
        "new_acquisition_count": len(receipts),
        "new_http_200_count": sum(r.get("http_status") == 200 and not r.get("error") for r in receipts),
        "new_technical_failures": [{k: r.get(k) for k in ["source_id", "source_url", "resolved_url", "http_status", "error", "checked_at", "sha256"]} for r in receipts if r.get("error")],
        "prior_counts": baseline["prior_counts"], "current_counts": queue["counts"],
        "remaining_school_urls_without_recorded_reading": len(pending),
        "remaining_global_urls_without_recorded_reading": sum(s["review_state"] == "readable_body_without_recorded_review" for s in queue["shared_and_global_sources"]),
        "changed_fields": changed, "changed_host_fields": sum(r["scope"] == "host_fields" for r in changed),
        "previously_missing_host_fields_filled": sum(r["scope"] == "host_fields" and r["previous_status"] == "missing" and r["status"] != "missing" for r in changed),
        "all_public_policy_research_exhausted": False,
        "reading_record_is_not_policy_verification": True,
        "external_private_steps": [{"ccu_page": r["ccu_page"], "fields": [f["field"] for f in r["external_access_limited_steps"]]} for r in queue["schools"] if r["external_access_limited_steps"]],
        "current_rule_limits": "BFSU2022 dates remain reference_only. Oneonta/HWG unyear eligibility and recurring deadlines remain needs_confirmation. USJ annual ticket and exchange semester approximation remain conflicting scoped evidence. No new home choice, quota or application deadline is inferred."
    }
    assert not pending
    (B / "completion-eighth-public-progress.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    limits = read("completion-remaining-limitations.json")
    limits["public_reading_remains"] = {
        "worklist": "completion-remaining-public-worklist.json", "round8_scope": result["scope"],
        "reading_record_missing_sources": len(pending), "independent_bodies": 0,
        "priority_policy_candidates": queue["counts"]["priority_policy_candidates"],
        "remaining_global_urls_without_recorded_reading": result["remaining_global_urls_without_recorded_reading"],
        "partial_body_and_linked_children_unclaimed": True,
        "external_cannot_solve_scope": "Only explicit personal/nomination procedures, server failures/challenges and licensed-image requirements are limited. Saved partial reading is not an exhaustive website review or an official claim that a newer document is unannounced."
    }
    limits["eighth_result"] = {"progress": "completion-eighth-public-progress.json", "assets_unchanged": True,
                               "original_six_school_seven_private_steps_preserved": True,
                               "new_private_step": "Oneonta application_forms: after mother nomination, OGE account sign-in; only public instructions read, no account or submission."}
    (B / "completion-remaining-limitations.json").write_text(json.dumps(limits, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({k: result[k] for k in ["original_urls_with_recorded_reading_extent", "all_reading_records", "all_visible_read_records", "changed_host_fields", "previously_missing_host_fields_filled", "remaining_school_urls_without_recorded_reading"]}))


if __name__ == "__main__":
    main()
