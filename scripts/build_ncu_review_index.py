#!/usr/bin/env python3
"""Small review indexes of an immutable NCU candidate; never rebuild the catalog."""
from __future__ import annotations

import argparse
import copy
import gzip
import hashlib
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BUNDLE = "src/exchange_info/official_data/ncu"
MANUAL = "sources/ncu/2026-10-08/reviewed-host-records.json"
INPUTS = [MANUAL, f"{BUNDLE}/field-audit.json", f"{BUNDLE}/application_workflows.jsonl",
          f"{BUNDLE}/document-conditions.json", f"{BUNDLE}/source-evidence.json.gz",
          f"{BUNDLE}/catalog-completeness.json"]


def digest(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def git_bytes(sha: str, path: str) -> bytes:
    return subprocess.check_output(["git", "show", f"{sha}:{path}"], cwd=ROOT)


def write(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n")


def load_candidate(sha: str):
    raw = {p: git_bytes(sha, p) for p in INPUTS}
    return (raw, json.loads(raw[MANUAL]), json.loads(raw[f"{BUNDLE}/field-audit.json"]),
            [json.loads(x) for x in raw[f"{BUNDLE}/application_workflows.jsonl"].splitlines()],
            json.loads(raw[f"{BUNDLE}/document-conditions.json"]),
            json.loads(gzip.decompress(raw[f"{BUNDLE}/source-evidence.json.gz"])))


def field_index(field, audit_i: int, key: str):
    result = copy.deepcopy(field)
    for i, evidence in enumerate(result.get("original_evidence", [])):
        text = evidence.pop("text")
        evidence["original_text_locator"] = {
            "path": f"{BUNDLE}/field-audit.json", "audit_array_index": audit_i,
            "field": key, "evidence_array_index": i,
            "text_sha256": digest(text.encode()), "char_count": len(text),
        }
    return result


def build(sha: str, out: Path):
    raw, manual, audit, workflows, policies, sources = load_candidate(sha)
    records = []
    used_sources = set()
    for i, row in enumerate(audit):
        reviewed_ids = [r for r in row["source_rows"] if r in manual]
        if not reviewed_ids:
            continue
        ident = reviewed_ids[0]
        school = out / "schools" / ident
        fields = {k: f"fields/{k}.json" for k in row["fields"]}
        assert len(fields) == 17
        for key, value in row["fields"].items():
            write(school / fields[key], field_index(value, i, key))
        workflow = next(w for w in workflows if w["school_name"] == row["school_name"])
        steps = []
        for n, step in enumerate(workflow["steps"]):
            # Exact authored rule namespace; do not infer conditions from prose.
            role = "home" if step["rule_id"].startswith("ncu-116-1-home-") else "host"
            path = f"documents/{n+1:02d}-{step['rule_id']}.json"
            related = [p for p in policies if p["school_name"] == row["school_name"] and p["rule_id"] == step["rule_id"]]
            write(school / path, {"document_owner": role, "step": step, "policies": related})
            steps.append({"path": path, "owner": role, "rule_id": step["rule_id"],
                          "phase": step["phase"], "title": step["title"],
                          "document_count": len(step.get("document_requirements", []))})
        write(school / "documents.json", {**{k: v for k, v in workflow.items() if k != "steps"}, "steps": steps})
        source_ids = {x["id"] for x in row["read_sources"] + row["unretrieved_sources"]}
        source_ids.update(e["source_id"] for f in row["fields"].values() for e in f["original_evidence"] if e.get("source_id"))
        known = {s["id"] for s in sources}
        used_sources.update(source_ids & known)
        mappings = {}
        for group in ["read_sources", "unretrieved_sources"]:
            mappings[group] = []
            for n, mapping in enumerate(row[group]):
                path = f"source-mappings/{group}-{n:03d}.json"
                write(school / path, mapping)
                mappings[group].append({"id": mapping["id"], "path": path})
        write(school / "sources.json", {
            **mappings,
            "source_metadata": [{"id": s, "path": f"../../sources/{s}.json"} for s in sorted(source_ids & known)],
            "unresolved_source_ids": sorted(source_ids - known),
            "note_zh": "逐來源status與閱讀範圍照原件保留；提取／來源映射不等於全文閱讀或116核准。",
        })
        gaps = [{"field": key, "status": f["status"], "unresolved": f.get("unresolved")}
                for key, f in row["fields"].items()]
        write(school / "gaps.json", {"fields": gaps, "unretrieved_sources": row["unretrieved_sources"]})
        entry = {"id": ident, "school_name": row["school_name"], "country": row["country"],
                 "source_rows": row["source_rows"], "manual_record_ids": reviewed_ids,
                 "historical_rows_without_separate_manual_record": [r for r in row["source_rows"] if r not in manual],
                 "checked_at": row["checked_at"], "coverage": "partial", "current_116_verified": False,
                 "fields": fields, "documents": "documents.json", "sources": "sources.json", "gaps": "gaps.json"}
        write(school / "index.json", entry)
        records.append({"id": ident, "school_name": row["school_name"], "path": f"schools/{ident}/index.json"})
    assert len(records) == len(manual) == 71
    for source_i, source in enumerate(sources):
        if source["id"] not in used_sources:
            continue
        metadata = {k: v for k, v in source.items() if k not in {"pages", "links", "public_excerpt"}}
        # Large native page text stays in the immutable gzip original.
        metadata["original_source_locator"] = {"path": f"{BUNDLE}/source-evidence.json.gz",
                                               "source_array_index": source_i, "source_id": source["id"]}
        metadata["pages"] = []
        for j, p in enumerate(source.get("pages", [])):
            page_path = f"{source['id']}/pages/{j:03d}.json"
            write(out / "sources" / page_path, {
                **{k: v for k, v in p.items() if k != "text"},
                "original_text_locator": {"page_array_index": j,
                                          "text_sha256": digest(p.get("text", "").encode()),
                                          "char_count": len(p.get("text", ""))}})
            metadata["pages"].append({"page": p.get("page"), "path": page_path})
        write(out / "sources" / f"{source['id']}.json", metadata)
    write(out / "manifest.json", {
        "candidate_sha": sha, "baseline_data_sha": "224284f1460a792daf0015a6ab4342d83968ab8f",
        "exception_corrections": ["ncu-122", "ncu-128", "ncu-129"],
        "input_sha256": {p: digest(b) for p, b in raw.items()},
        "catalog_coverage": json.loads(raw[f"{BUNDLE}/catalog-completeness.json"]),
        "school_count": len(records), "fields_per_school": 17,
        "indexed_source_count": len(used_sources), "schools": records,
        "note_zh": "原始大檔保留。索引不修改資料／補核當期；共享來源去重，原文由不可變Git候選與精確位置／hash讀回。",
    })
    return validate(out)


def validate(out: Path):
    manifest = json.loads((out / "manifest.json").read_text())
    raw, manual, audit, workflows, policies, sources = load_candidate(manifest["candidate_sha"])
    assert manifest["input_sha256"] == {p: digest(b) for p, b in raw.items()}
    originals = 0
    for entry in manifest["schools"]:
        school = out / "schools" / entry["id"]
        idx = json.loads((school / "index.json").read_text())
        row_i = next(i for i, r in enumerate(audit) if r["school_name"] == entry["school_name"])
        row = audit[row_i]
        assert len(idx["fields"]) == 17
        assert idx["source_rows"] == row["source_rows"]
        assert idx["manual_record_ids"] == [r for r in row["source_rows"] if r in manual]
        assert json.loads((school / "gaps.json").read_text()) == {
            "fields": [{"field": key, "status": f["status"], "unresolved": f.get("unresolved")}
                       for key, f in row["fields"].items()],
            "unretrieved_sources": row["unretrieved_sources"],
        }
        for key, path in idx["fields"].items():
            field = json.loads((school / path).read_text())
            assert field == field_index(row["fields"][key], row_i, key)
            originals += len(field["original_evidence"])
        workflow = next(w for w in workflows if w["school_name"] == entry["school_name"])
        docs = json.loads((school / "documents.json").read_text())
        assert {k: v for k, v in docs.items() if k != "steps"} == {k: v for k, v in workflow.items() if k != "steps"}
        assert len(docs["steps"]) == len(workflow["steps"])
        for link, step in zip(docs["steps"], workflow["steps"]):
            data = json.loads((school / link["path"]).read_text())
            assert data["step"] == step
            assert data["policies"] == [p for p in policies if p["school_name"] == entry["school_name"] and p["rule_id"] == step["rule_id"]]
        source_index = json.loads((school / "sources.json").read_text())
        for group in ["read_sources", "unretrieved_sources"]:
            assert [json.loads((school / link["path"]).read_text()) for link in source_index[group]] == row[group]
        for link in source_index["source_metadata"]:
            source = json.loads((school / link["path"]).read_text())
            loc = source["original_source_locator"]
            original = sources[loc["source_array_index"]]
            assert original["id"] == loc["source_id"] == link["id"]
            assert {k: v for k, v in source.items() if k not in {"pages", "original_source_locator"}} == {k: v for k, v in original.items() if k not in {"pages", "links", "public_excerpt"}}
            assert len(source["pages"]) == len(original.get("pages", []))
            for page_i, (page_link, original_page) in enumerate(zip(source["pages"], original.get("pages", []))):
                page = json.loads((out / "sources" / page_link["path"]).read_text())
                assert {k: v for k, v in page.items() if k != "original_text_locator"} == {k: v for k, v in original_page.items() if k != "text"}
                assert page["original_text_locator"]["page_array_index"] == page_i
                assert page["original_text_locator"]["text_sha256"] == digest(original_page.get("text", "").encode())
    sizes = [p.stat().st_size for p in out.rglob("*.json")]
    result = {"candidate_sha": manifest["candidate_sha"], "schools": len(manifest["schools"]),
              "field_files": 17 * len(manifest["schools"]), "original_text_locators_verified": originals,
              "json_files": len(sizes), "largest_json_bytes": max(sizes), "input_hashes_verified": True}
    print(json.dumps(result, ensure_ascii=False))
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidate-sha")
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--school")
    parser.add_argument("--field")
    parser.add_argument("--original", action="store_true")
    args = parser.parse_args()
    if args.check:
        validate(args.output_dir)
    elif args.school and args.field:
        manifest = json.loads((args.output_dir / "manifest.json").read_text())
        field = json.loads((args.output_dir / "schools" / args.school / "fields" / f"{args.field}.json").read_text())
        if args.original:
            audit = json.loads(git_bytes(manifest["candidate_sha"], f"{BUNDLE}/field-audit.json"))
            for evidence in field["original_evidence"]:
                loc = evidence.pop("original_text_locator")
                text = audit[loc["audit_array_index"]]["fields"][loc["field"]]["original_evidence"][loc["evidence_array_index"]]["text"]
                assert digest(text.encode()) == loc["text_sha256"]
                evidence["text"] = text
        print(json.dumps(field, ensure_ascii=False, indent=2))
    else:
        if not args.candidate_sha:
            parser.error("--candidate-sha is required to build an immutable index")
        sha = subprocess.check_output(["git", "rev-parse", args.candidate_sha], cwd=ROOT, text=True).strip()
        build(sha, args.output_dir)


if __name__ == "__main__":
    main()
