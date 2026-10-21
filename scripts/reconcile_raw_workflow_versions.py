"""Resolve original workflow census ambiguity by explicit source academic year.

This creates a separate overlay; neither immutable census is rewritten.
Matching identities proves structural coverage, not admission applicability.
"""
from collections import Counter, defaultdict
import gzip
import hashlib
import json
from pathlib import Path

from audit_university_data import ROOT, dump, leaves
from audit_university_raw_catalog import read_pointer


def reconcile():
    audit = ROOT / "output/data-verification-20261021"
    output = audit / "workflow-version-reconciliation"
    if output.exists():
        raise FileExistsError("Preserve an existing reconciliation overlay")
    output.mkdir()
    baseline, rawbase = audit / "baseline", audit / "raw-catalog-baseline"
    candidates = defaultdict(list)
    with gzip.open(baseline / "records.jsonl.gz", "rt", encoding="utf8") as stream:
        for line in stream:
            record = json.loads(line)
            if record["kind"] == "workflow" and record["home_id"] in {"cgu", "ntpu"}:
                row = record["data"]
                candidates[(record["home_id"], row.get("school_name"), row.get("country"))].append(record)
    rows, counts, homes = [], Counter(), Counter()
    with gzip.open(rawbase / "records.jsonl.gz", "rt", encoding="utf8") as stream, gzip.GzipFile(
            filename=str(output / "field-coverage.jsonl.gz"), mode="wb", mtime=0) as fields:
        for line in stream:
            record = json.loads(line)
            if record["kind"] != "raw:application_workflows.jsonl" or record["home_id"] not in {"cgu", "ntpu"}:
                continue
            row = record["data"]
            previous = candidates[(record["home_id"], row.get("school_name"), row.get("country"))]
            for qualifier in ("program_type", "source_url", "application_round"):
                if len(previous) > 1 and row.get(qualifier):
                    exact = [r for r in previous if r["data"].get(qualifier) == row[qualifier]]
                    if exact:
                        previous = exact
            if len(previous) <= 1:
                continue
            matched = [r for r in previous if row.get("academic_year")
                       and r["data"].get("academic_year") == row["academic_year"]]
            if len(matched) != 1:
                raise ValueError(f"Academic year does not uniquely resolve {record['record_id']}")
            target = matched[0]
            rows.append({"raw_record_id": record["record_id"], "runtime_record_id": target["record_id"],
                "home_id": record["home_id"], "school_name": row["school_name"],
                "academic_year": row["academic_year"], "previous_candidates": [r["record_id"] for r in previous],
                "method": "exact_name_country_program_round_and_explicit_academic_year", "fact_verified": False})
            homes[record["home_id"]] += 1
            for pointer, value in leaves(row):
                try:
                    actual = read_pointer(target["data"], pointer)
                except (KeyError, IndexError, TypeError, ValueError):
                    status = "absent_runtime_pointer"
                else:
                    status = "same_value_at_pointer" if type(actual) is type(value) and actual == value else "different_value_at_pointer"
                counts[status] += 1
                fields.write((dump({"raw_record_id": record["record_id"], "pointer": pointer,
                    "runtime_record_id": target["record_id"], "coverage": status}) + "\n").encode())
    (output / "record-links.jsonl").write_text("".join(dump(row) + "\n" for row in rows), "utf8")
    prior = json.loads((rawbase / "inventory-summary.json").read_text("utf8"))
    assert len(rows) == prior["record_matches"]["ambiguous"]
    assert sum(counts.values()) == prior["structural_coverage"]["ambiguous_runtime_record"]
    combined = Counter(prior["structural_coverage"])
    combined["ambiguous_runtime_record"] = 0
    combined.update(counts)
    summary = {"base_commit": "b662dced2607bc67c3354c95b7aaad202448bea7",
        "resolved_records": len(rows), "by_home": dict(homes), "resolved_field_coverage": dict(counts),
        "combined_structural_coverage": dict(combined), "remaining_ambiguous_records": 0,
        "facts_verified_by_reconciliation": 0, "preserves_historical_versions": True,
        "inputs": {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
                   for p in (baseline / "records.jsonl.gz", rawbase / "records.jsonl.gz")},
        "outputs": {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in output.iterdir()}}
    (ROOT / "docs/data-verification-20261021/round28-workflow-version-reconciliation.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n", "utf8")
    print(json.dumps({k: v for k, v in summary.items() if k not in {"inputs", "outputs"}}, ensure_ascii=False))


if __name__ == "__main__":
    reconcile()
