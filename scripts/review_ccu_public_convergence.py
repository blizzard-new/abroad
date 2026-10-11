"""Apply the finite ninth CCU reading pass without rewriting earlier snapshots."""
from __future__ import annotations

import json

from fetch_ccu_completion_sources import BUNDLE as B
from review_ccu_followup_batch import evidence, fact, receipt
from review_ccu_public_round8 import visible


def load(name):
    return json.loads((B / name).read_text())


def main():
    manual = load("completion-manual-fields.json")
    baseline = {r["ccu_page"]: r for r in load("completion-ninth-baseline.json")["prior_fields"]}
    validated = []
    for item in load("completion-ninth-field-input.json"):
        label = item["source_id"].split("-", 1)[1]
        record = receipt(item["ccu_page"], label)
        assert item["quote"] in visible(record, item.get("source_pages", [])), item["source_id"]
        ev = evidence(item["ccu_page"], label, item["quote"],
                      pages=item.get("source_pages", []), year=item["academic_year"])
        ev["application_round"] = item["academic_year"]
        ev["location_in_source"] = ("PDF page(s): " + str(item["source_pages"]) if item["source_pages"]
                                    else "HTML passage located by exact excerpt")
        evidence_items = [ev]
        for support in item.get("supplemental_evidence", []):
            support_label = support["source_id"].split("-", 1)[1]
            support_record = receipt(item["ccu_page"], support_label)
            assert support["quote"] in visible(support_record)
            evidence_items.append(evidence(item["ccu_page"], support_label, support["quote"],
                                           year=support["academic_year"]))
        value = fact(item["value"], evidence_items, status=item["status"], reason=item["reason"])
        if item.get("preserve_baseline_evidence"):
            value["evidence"] = baseline[item["ccu_page"]]["host_fields"][item["field"]]["evidence"] + value["evidence"]
        if item.get("research_classification"):
            assert item["access_requirement_quote"] in visible(record)
            value["research_classification"] = item["research_classification"]
            value["access_requirement_evidence"] = [evidence(
                item["ccu_page"], label, item["access_requirement_quote"], year=item["academic_year"])]
        validated.append((item, value))
    for item, value in validated:
        row = next((r for r in manual["schools"] if r["ccu_page"] == item["ccu_page"]), None)
        if row is None:
            row = {"ccu_page": item["ccu_page"], "host_fields": {}}
            manual["schools"].append(row)
        row["host_fields"][item["field"]] = value
    readings = load("completion-ninth-reading-input.json")
    for item in readings:
        record = receipt(item["ccu_page"], item["source_id"].split("-", 1)[1])
        assert item["content_hash"] == record["sha256"]
        assert item["source_url"] == record["source_url"]
    ids = {r["source_id"] for r in readings}
    ledger = [r for r in load("completion-public-body-reviews.json") if r["source_id"] not in ids] + readings
    for name, data in [("completion-manual-fields.json", manual), ("completion-public-body-reviews.json", ledger)]:
        (B / name).write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n")
    print(f"Ninth finite pass: {len(validated)} host fields; {len(readings)} precise reading records")


if __name__ == "__main__":
    main()
