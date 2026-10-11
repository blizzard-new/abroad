"""Apply explicitly read CCU public passages and scoped eighth-round reviews.

The saved reading extent is authoritative: a screened introduction or index is
not a claim that every linked document or the whole source was read.
"""
from __future__ import annotations

import gzip
import json
import re

from bs4 import BeautifulSoup
from fetch_ccu_completion_sources import BUNDLE as B
from review_ccu_followup_batch import evidence, fact, receipt


def load(name):
    return json.loads((B / name).read_text())


def visible(record):
    path = B / record["bundled_file"]
    raw = path.read_bytes()
    raw = gzip.decompress(raw) if path.suffix == ".gz" else raw
    soup = BeautifulSoup(raw, "html.parser")
    for tag in soup(["script", "style", "nav", "header", "footer", "noscript"]):
        tag.decompose()
    return re.sub(r"\s+", " ", soup.get_text(" ", strip=True))


def main():
    manual = load("completion-manual-fields.json")
    fields = load("completion-eighth-field-input.json")
    # Check every quote before changing any manual policy fields.
    validated = []
    for item in fields:
        page, label = item["source_id"].split("-", 1)
        record = receipt(int(page[1:]), label)
        text = visible(record)
        assert item["quote"] in text, (item["field"], item["source_id"], item["quote"])
        if item.get("access_requirement_quote"):
            assert item["access_requirement_quote"] in text
        ev = evidence(item["ccu_page"], label, item["quote"], year=item["academic_year"])
        ev["application_round"] = item["academic_year"]
        ev["location_in_source"] = "HTML visible passage identified by exact excerpt; no PDF pagination asserted"
        value = fact(item["value"], [ev], status=item["status"], reason=item["reason"])
        if item.get("research_classification"):
            value["research_classification"] = item["research_classification"]
            access = evidence(item["ccu_page"], label, item["access_requirement_quote"], year=item["academic_year"])
            access["application_round"] = item["academic_year"]
            value["access_requirement_evidence"] = [access]
        validated.append((item, value))
    for item, value in validated:
        row = next((r for r in manual["schools"] if r["ccu_page"] == item["ccu_page"]), None)
        if row is None:
            row = {"ccu_page": item["ccu_page"], "host_fields": {}}
            manual["schools"].append(row)
        row["host_fields"][item["field"]] = value

    readings = load("completion-eighth-reading-input.json")
    for item in readings:
        record = receipt(item["ccu_page"], item["source_id"].split("-", 1)[1])
        assert item["content_hash"] == record["sha256"], item["source_id"]
        assert item["source_url"] == record["source_url"], item["source_id"]
    ledger = load("completion-public-body-reviews.json")
    ids = {r["source_id"] for r in readings}
    ledger = [r for r in ledger if r.get("source_id") not in ids] + readings
    (B / "completion-manual-fields.json").write_text(json.dumps(manual, ensure_ascii=False, indent=2) + "\n")
    (B / "completion-public-body-reviews.json").write_text(json.dumps(ledger, ensure_ascii=False, indent=2) + "\n")
    print(f"Eighth round: {len(readings)} scoped reading records, {len(fields)} policy fields")


if __name__ == "__main__":
    main()
