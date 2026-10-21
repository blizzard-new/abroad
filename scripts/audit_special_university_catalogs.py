"""Preserve CGU, NTPU and TKU catalog inputs outside partners.jsonl.

PDF page extraction and literal-code inventories are evidence locations only;
neither extraction nor a pre-existing verified label proves factual accuracy.
"""
from __future__ import annotations

import argparse
import ast
from collections import Counter
from contextlib import redirect_stdout
import hashlib
import io
import json
from pathlib import Path
import re
import subprocess

from pypdf import PdfReader

from audit_university_data import Census, ROOT
from audit_university_derived_content import BASE


def inventory(output: Path):
    if output.exists() and any(output.iterdir()):
        raise FileExistsError("Preserve the special-format baseline")
    destination = ROOT / "docs/data-verification-20261021/round31-special-catalog-baseline-manifest.json"
    if destination.exists():
        raise FileExistsError(destination)
    census, manifest, counts = Census(output), [], Counter()

    def blob(path):
        raw = subprocess.check_output(["git", "show", f"{BASE}:{path}"], cwd=ROOT)
        manifest.append({"path": path, "sha256": hashlib.sha256(raw).hexdigest(), "bytes": len(raw)})
        return raw

    def add(home, kind, index, row, path):
        census.add(home, kind, f"{path}|{index}", row, path)
        counts[home] += 1

    folder = "src/exchange_info/official_data/cgu_catalogue"
    path = folder + "/snapshot.json"
    payload = json.loads(blob(path))
    for i, row in enumerate(payload["records"]):
        add("cgu", "raw:snapshot.json", i, row, path)
    add("cgu", "raw:snapshot_metadata", 0, {k: v for k, v in payload.items() if k != "records"}, path)
    receipts = {r["spreadsheet_id"]: r for r in payload["source_receipts"]}
    for spreadsheet, receipt in receipts.items():
        path = folder + f"/{spreadsheet}.gviz.json"
        raw = blob(path)
        # Parse the JSON argument, never execute the Google callback wrapper.
        match = re.fullmatch(rb"/\*O_o\*/\s*google\.visualization\.Query\.setResponse\((.*)\);?\s*", raw, re.S)
        if match is None:
            raise ValueError("Unexpected GViz wrapper")
        table = json.loads(match[1])["table"]
        for i, row in enumerate(table["rows"]):
            add("cgu", "raw:gviz_row", i, {"spreadsheet_id": spreadsheet, "source_url": receipt["url"],
                "column_definitions": table["cols"], "row": row}, path)

    folder = "src/exchange_info/official_data/tku"
    for name in ("partners_current.jsonl", "partners_reference.jsonl", "earlier_round_programmes.jsonl",
                 "sources.json", "rounds.json", "full_census_audit.json"):
        path = folder + "/" + name
        raw = blob(path)
        if name.endswith("jsonl"):
            rows = [json.loads(line) for line in raw.splitlines() if line.strip()]
        else:
            payload = json.loads(raw)
            if name == "full_census_audit.json":
                rows = payload["schools"]
                add("tku", "raw:full_census_metadata", 0, {k: v for k, v in payload.items() if k != "schools"}, path)
            else:
                rows = payload
        for i, row in enumerate(rows):
            add("tku", "raw:" + name, i, row, path)

    path = "src/exchange_info/ntpu_student_view.py"
    code = blob(path)
    values, nodes = {}, {}

    def literal(node):
        if isinstance(node, ast.Name):
            return values[node.id]
        if isinstance(node, (ast.List, ast.Tuple)):
            return [literal(item) for item in node.elts]
        return ast.literal_eval(node)

    for node in ast.parse(code).body:
        if not isinstance(node, ast.Assign) or len(node.targets) != 1 or not isinstance(node.targets[0], ast.Name):
            continue
        try:
            values[node.targets[0].id] = literal(node.value)
            nodes[node.targets[0].id] = node
        except (ValueError, TypeError, KeyError):
            continue
    source_names = {}
    for year in ("115", "116"):
        for language in ("ENGLISH", "JAPANESE", "CHINESE"):
            source_names[f"{year}-{language.lower()}-partners.pdf"] = values[f"NTPU_{year}_{language}_PARTNERS_URL"]
    source_names.update({"116-guidelines-zh.pdf": values["NTPU_116_GUIDELINES_URL"],
                         "116-guidelines-en.pdf": values["NTPU_116_GUIDELINES_EN_URL"]})
    for filename, url in source_names.items():
        pdf_path = "src/exchange_info/official_data/ntpu/" + filename
        raw = blob(pdf_path)
        for i, page in enumerate(PdfReader(io.BytesIO(raw)).pages, 1):
            add("ntpu", "raw:pdf_page", i, {"source_url": url, "source_file": pdf_path,
                "page": i, "text": page.extract_text() or "", "requires_visual_table_review": True}, pdf_path)
    for name, keys in [("NTPU_EXCHANGE_AGREEMENTS_WITHOUT_QUOTA", ["country", "school_name", "agreement_type", "agreement_level"]),
                       ("FALLBACK_PARTNERS", ["language_group", "country", "school_name"])]:
        node = nodes[name]
        for i, row in enumerate(values[name]):
            add("ntpu", "code:" + name, i, {**dict(zip(keys, row)),
                "original_lines": [node.lineno, node.end_lineno], "not_independently_verified": True}, path)
    census.school_stats = [{"home_id": home, "special_format_records": number} for home, number in sorted(counts.items())]
    with redirect_stdout(io.StringIO()):
        census.save()
    info = {"base_commit": BASE, "files": manifest, "scope": "Original special-format inputs for CGU, NTPU and TKU",
        "overlaps_existing_censuses": True, "facts_verified_by_extraction": 0,
        "limitations": ["PDF text alone does not verify table associations; visual and current-source comparison remain required.",
            "These inputs overlap earlier runtime, raw and supplementary records; counts are not distinct factual claims.",
            "This does not cover every root-level JSON, asset, UI-generated assertion or production database record."],
        "outputs": {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in output.iterdir() if p.is_file()}}
    destination.write_text(json.dumps(info, ensure_ascii=False, indent=2) + "\n", "utf8")
    summary = json.loads((output / "inventory-summary.json").read_text("utf8"))
    print(json.dumps({k: summary[k] for k in ("school_count", "record_counts", "leaf_counts", "candidate_source_count")}, ensure_ascii=False))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "output/data-verification-20261021/special-catalog-baseline")
    inventory(parser.parse_args().output)
