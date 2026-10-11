"""Apply explicitly read CCU public passages and scoped eighth-round reviews.

The saved reading extent is authoritative: a screened introduction or index is
not a claim that every linked document or the whole source was read.
"""
from __future__ import annotations

import gzip
import json
import re
from io import BytesIO

from bs4 import BeautifulSoup
from fetch_ccu_completion_sources import BUNDLE as B
from pypdf import PdfReader
from review_ccu_followup_batch import evidence, fact, receipt


def load(name):
    return json.loads((B / name).read_text())


def visible(record, pages=()):
    path = B / record["bundled_file"]
    raw = path.read_bytes()
    raw = gzip.decompress(raw) if path.suffix == ".gz" else raw
    if raw.startswith(b"%PDF-"):
        reader = PdfReader(BytesIO(raw))
        selected = pages or range(1, len(reader.pages) + 1)
        return re.sub(r"\s+", " ", " ".join(reader.pages[p - 1].extract_text() or "" for p in selected))
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
        pages = item.get("source_pages", [])
        text = visible(record, pages)
        assert item["quote"] in text, (item["field"], item["source_id"], item["quote"])
        if item.get("access_requirement_quote"):
            assert item["access_requirement_quote"] in text
        ev = evidence(item["ccu_page"], label, item["quote"], pages=pages, year=item["academic_year"])
        ev["application_round"] = item["academic_year"]
        ev["location_in_source"] = "PDF page(s) " + str(pages) if pages else "HTML visible passage identified by exact excerpt; no PDF pagination asserted"
        evidence_items = [ev]
        for supporting in item.get("supplemental_evidence", []):
            p, supporting_label = supporting["source_id"].split("-", 1)
            supporting_pages = supporting.get("source_pages", [])
            supporting_record = receipt(int(p[1:]), supporting_label)
            assert supporting["quote"] in visible(supporting_record, supporting_pages)
            support = evidence(int(p[1:]), supporting_label, supporting["quote"], pages=supporting_pages, year=supporting["academic_year"])
            support["application_round"] = supporting["academic_year"]
            support["location_in_source"] = "PDF page(s) " + str(supporting_pages) if supporting_pages else "HTML visible passage identified by exact excerpt"
            evidence_items.append(support)
        value = fact(item["value"], evidence_items, status=item["status"], reason=item["reason"])
        if item.get("preserve_baseline_evidence"):
            baseline = load("completion-eighth-baseline.json")["prior_fields"]
            before = next(r for r in baseline if r["ccu_page"] == item["ccu_page"])
            value["evidence"] = before["host_fields"][item["field"]]["evidence"] + value["evidence"]
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
