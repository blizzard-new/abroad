"""Preserve omitted raw life/story bundles at the original Git audit baseline.

This supplements, and never rewrites, the first runtime census. Raw records
overlap runtime records, so their counts must not be added as distinct facts.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import subprocess

from audit_university_data import Census, ROOT

BASE = "b662dced2607bc67c3354c95b7aaad202448bea7"
FILENAMES = {
    "student_life.jsonl", "student_experiences.jsonl",
    "student-experience-digests.json", "experience_sources.jsonl",
}


def inventory(output: Path):
    if (output / "records.jsonl.gz").exists():
        raise FileExistsError("Supplement already exists; preserve the original evidence.")
    files = subprocess.check_output([
        "git", "ls-tree", "-r", "--name-only", BASE, "src/exchange_info/official_data",
    ], cwd=ROOT).decode("utf8").splitlines()
    census = Census(output)
    counts, manifest = Counter(), []
    for name in files:
        path = Path(name)
        if path.name not in FILENAMES:
            continue
        raw = subprocess.check_output(["git", "show", f"{BASE}:{name}"], cwd=ROOT)
        home = path.parent.name
        if path.suffix == ".jsonl":
            rows = [json.loads(line) for line in raw.decode("utf-8-sig").splitlines() if line.strip()]
        else:
            payload = json.loads(raw)
            rows = [{"mapping_key": key, **value} for key, value in payload["digests"].items()]
        for index, row in enumerate(rows):
            key = f"{row.get('school_name', '')}|{index}"
            census.add(home, "raw:" + path.name, key, row, name)
            counts[home] += 1
        manifest.append({"path": name, "sha256": hashlib.sha256(raw).hexdigest(), "rows": len(rows)})
    census.school_stats = [{"home_id": home, "raw_supplement_records": count} for home, count in sorted(counts.items())]
    census.save()
    info = {
        "base_commit": BASE, "scope": sorted(FILENAMES), "files": manifest,
        "supplement_only": True, "overlaps_runtime_census": True,
        "whole_records_verified": 0,
        "remaining_inventory_gaps": ["Other omitted raw bundles and UI-generated claims require coverage reconciliation.",
            "This census does not prove production database parity."],
        "outputs": {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in output.iterdir() if p.is_file()},
    }
    (ROOT / "docs/data-verification-20261021/derived-content-baseline-manifest.json").write_text(
        json.dumps(info, ensure_ascii=False, indent=2) + "\n", encoding="utf8")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "output/data-verification-20261021/derived-baseline")
    inventory(parser.parse_args().output)
