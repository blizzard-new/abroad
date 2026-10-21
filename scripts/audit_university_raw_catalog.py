"""Preserve original raw catalog fields omitted or transformed by runtime models.

Coverage reconciliation is structural, never independent fact verification.
The immutable raw and runtime censuses overlap and must not be added together.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from contextlib import redirect_stdout
import gzip
import hashlib
import io
import json
from pathlib import Path
import re
import subprocess

from audit_university_data import Census, ROOT, dump, leaves
from audit_university_derived_content import BASE

KINDS = {"partners.jsonl": "partner", "application_workflows.jsonl": "workflow",
         "destination_profiles.jsonl": "destination"}


def read_pointer(value, pointer):
    for part in pointer.split("/")[1:]:
        part = part.replace("~1", "/").replace("~0", "~")
        value = value[int(part)] if isinstance(value, list) else value[part]
    return value


def inventory(output: Path):
    if output.exists() and any(output.iterdir()):
        raise FileExistsError("Raw baseline output must be empty; never overwrite preserved evidence.")
    runtime = defaultdict(list)
    baseline = ROOT / "output/data-verification-20261021/baseline"
    with gzip.open(baseline / "records.jsonl.gz", "rt", encoding="utf8") as stream:
        for line in stream:
            record = json.loads(line)
            if record["kind"] in KINDS.values():
                row = record["data"]
                runtime[(record["home_id"], record["kind"], row.get("school_name"), row.get("country"))].append(record)
    files = subprocess.check_output(["git", "ls-tree", "-r", "--name-only", BASE,
        "src/exchange_info/official_data"], cwd=ROOT).decode("utf8").splitlines()
    census = Census(output)
    manifest, homes, coverage, top_absent = [], Counter(), Counter(), Counter()
    matches, unmatched, ambiguous = 0, 0, 0
    with gzip.GzipFile(filename=str(output / "runtime-field-coverage.jsonl.gz"), mode="wb", mtime=0) as coverage_stream:
        for name in files:
            path = Path(name)
            if path.name not in KINDS:
                continue
            raw = subprocess.check_output(["git", "show", f"{BASE}:{name}"], cwd=ROOT)
            source_rows = [json.loads(line) for line in raw.decode("utf-8-sig").splitlines() if line.strip()]
            home, file_coverage = path.parent.name, Counter()
            for index, row in enumerate(source_rows):
                record = census.add(home, "raw:" + path.name, f"{row.get('school_name', '')}|{index}", row, name)
                homes[home] += 1
                candidates = runtime.get((home, KINDS[path.name], row.get("school_name"), row.get("country")), [])
                # A more specific exact qualifier may disambiguate multiple plans.
                for qualifier in ("program_type", "source_url", "application_round"):
                    if len(candidates) > 1 and row.get(qualifier):
                        exact = [r for r in candidates if r["data"].get(qualifier) == row[qualifier]]
                        if exact:
                            candidates = exact
                linked = candidates[0] if len(candidates) == 1 else None
                matches += linked is not None
                unmatched += len(candidates) == 0
                ambiguous += len(candidates) > 1
                for pointer, value in leaves(row):
                    if linked is None:
                        status = "ambiguous_runtime_record" if candidates else "no_runtime_record_match"
                    else:
                        try:
                            runtime_value = read_pointer(linked["data"], pointer)
                        except (KeyError, IndexError, TypeError, ValueError):
                            status = "absent_runtime_pointer"
                            top_absent[re.sub(r"/\d+(?=/|$)", "/*", pointer)] += 1
                        else:
                            status = "same_value_at_pointer" if type(value) is type(runtime_value) and value == runtime_value else "different_value_at_pointer"
                    coverage[status] += 1
                    file_coverage[status] += 1
                    item = {"raw_record_id": record["record_id"], "pointer": pointer, "coverage": status,
                            "runtime_record_id": linked["record_id"] if linked else None}
                    coverage_stream.write((dump(item) + "\n").encode("utf8"))
            manifest.append({"path": name, "sha256": hashlib.sha256(raw).hexdigest(),
                             "rows": len(source_rows), "coverage": dict(file_coverage)})
    census.school_stats = [{"home_id": h, "raw_catalog_records": n} for h, n in sorted(homes.items())]
    with redirect_stdout(io.StringIO()):
        census.save()
    summary_path = output / "inventory-summary.json"
    summary = json.loads(summary_path.read_text("utf8"))
    summary.update(source_base_commit=BASE, runtime_baseline_sha256=hashlib.sha256((baseline / "records.jsonl.gz").read_bytes()).hexdigest(),
                   overlaps_runtime_census=True, structural_coverage=dict(coverage),
                   record_matches={"unique": matches, "missing": unmatched, "ambiguous": ambiguous})
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", "utf8")
    info = {"base_commit": BASE, "scope": sorted(KINDS), "files": manifest,
            "overlaps_runtime_census": True, "facts_verified_by_extraction": 0,
            "record_matches": summary["record_matches"], "structural_coverage": dict(coverage),
            "most_common_absent_paths": top_absent.most_common(30),
            "remaining_inventory_gaps": [
                "Schools without partners.jsonl use other catalog formats that still require raw reconciliation.",
                "Other source-controlled data, UI-generated claims and production parity remain separate work.",
                "Different or absent runtime pointers can reflect intended schema filtering or ordering; not automatically defects.",
                "Raw snapshots overlap earlier censuses and are not additional distinct facts."],
            "outputs": {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in output.iterdir() if p.is_file()}}
    destination = ROOT / "docs/data-verification-20261021/raw-catalog-baseline-manifest.json"
    if destination.exists():
        raise FileExistsError("Raw catalog manifest already exists")
    destination.write_text(json.dumps(info, ensure_ascii=False, indent=2) + "\n", "utf8")
    print(json.dumps({k: summary[k] for k in ["school_count", "record_counts", "leaf_counts",
        "candidate_source_count", "structural_coverage", "record_matches"]}, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "output/data-verification-20261021/raw-catalog-baseline")
    inventory(parser.parse_args().output)
