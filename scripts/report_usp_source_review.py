"""Bind the partial USP review to original runtime and raw-life records."""
from __future__ import annotations

import argparse
from collections import Counter
import gzip
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from exchange_info.generated_content_review import digest
from exchange_info.usp_source_review import load_manifest, pointer_parent
from university_review_ledger import append_decisions as append_review_decisions


def report(append_decisions=False):
    manifest = load_manifest(ROOT)
    sources = {r["url"]: r for r in manifest["sources"]}
    main, ug, guide, gov, wrong = [r["url"] for r in manifest["sources"]]
    decisions, unbound = {}, []

    def add(record, pointer, value, status, interpretation, url, locator, reason, inventory):
        rid = digest(["usp-source-review-round23", record["record_id"], pointer])[:28]
        receipt = sources[url]
        decisions[rid] = {
            "review_id": rid, "base_record_id": record["record_id"], "pointer": pointer,
            "base_value": value, "base_value_sha256": digest(value), "base_status": status,
            "expected_value_or_interpretation": interpretation, "reason": reason,
            "source_url": url, "source_sha256": receipt["sha256"], "source_locator": locator,
            "retrieved_at": receipt["completed_at"], "reviewed_at": manifest["reviewed_at"],
            "source_type": "official_host_or_competent_government_source",
            "method": "scoped_source_comparison_and_dom_navigation_review",
            "baseline_inventory": inventory, "whole_record_verified": False,
            "additional_sources": [{"url": s, "sha256": sources[s]["sha256"]} for s in (main, ug, gov, wrong)],
        }

    inventory = "output/data-verification-20261021/baseline"
    with gzip.open(ROOT / inventory / "records.jsonl.gz", "rt", encoding="utf8") as stream:
        for line in stream:
            record = json.loads(line)
            if record["home_id"] != "nthu" or record["kind"] not in {"partner", "workflow", "destination"}:
                continue
            scope = next((r for r in manifest["rows"] if r["home_id"] == "nthu"
                and {"partner": "partners.jsonl", "workflow": "application_workflows.jsonl",
                     "destination": "destination_profiles.jsonl"}[record["kind"]] == r["file"].split("/")[-1]
                and r["school_name"] == record["data"].get("school_name")), None)
            if scope is None:
                continue
            for patch in scope["patches"]:
                try:
                    parent, key = pointer_parent(record["data"], patch["pointer"])
                    value = parent[key]
                except (KeyError, IndexError, TypeError, ValueError):
                    unbound.append({"file": scope["file"], "pointer": patch["pointer"],
                        "reason": "Not exposed by original runtime model; raw correction retained in source-review manifest."})
                    continue
                if value not in patch["expected_values"]:
                    unbound.append({"file": scope["file"], "pointer": patch["pointer"],
                        "reason": "Original runtime value differs from reviewed raw variants; needs separate binding."})
                    continue
                has_wrong = "international.umontreal.ca" in str(value)
                add(record, patch["pointer"], value, "contradicted" if has_wrong else "needs_confirmation",
                    patch["value"], wrong if has_wrong else ug,
                    "HTML title and university identity; USP Undergraduate exchange and Housing options sections",
                    "該網址屬蒙特婁大學，不是聖保羅大學。僅修正指定連結及被污染文字；原母校名額、當期資格仍未全部核實。"
                    if has_wrong else "原學期概括不能代替USP大學部一般學期及當期院系確認；頁面無指定年度。", inventory)

    inventory = "output/data-verification-20261021/derived-baseline"
    with gzip.open(ROOT / inventory / "records.jsonl.gz", "rt", encoding="utf8") as stream:
        for line in stream:
            record = json.loads(line)
            if (record["home_id"], record["kind"], record["data"].get("school_name")) != (
                    "ntu", "raw:student_life.jsonl", "聖保羅大學"):
                continue
            scope = next(s for s in manifest["rows"] if s["home_id"] == "ntu")
            assert record["data"]["evidence"] in scope["patches"][0]["expected_values"]
            for i, evidence in enumerate(record["data"]["evidence"]):
                nav = i in manifest["life_source_findings"]["navigation_indexes"]
                health = i == manifest["life_source_findings"]["public_health_index"]
                url = guide if nav else gov if health else ug if i in {10, 11} else main
                status = "needs_confirmation" if nav or i == 10 else "contradicted" if health else "verified_reference"
                interpretation = ("網站選單，不屬於生活或課程事實。" if nav else
                    "依衛生部，境內人士使用SUS不因國籍或移民身分被排除；不能概括為僅限急診。" if health else
                    "中央辦公室與接待院系的Free Mover程序須分開；仍須提名及院系審核。" if i == 10 else
                    "原頁支持此項有限內容；適用校區、學制及未指定年度的限制保留，不代表當期整筆核實。")
                locator = manifest["life_source_findings"]["navigation_locator"] if nav else (
                    "Main content, second paragraph: universal SUS access" if health else
                    "Exchange Programme for Undergraduate Students" if i in {10, 11} else
                    "Housing options and campus life / Medical Insurance / Course of Portuguese as a Foreign Language")
                add(record, f"/evidence/{i}/text", evidence["text"], status, interpretation, url, locator, interpretation, inventory)
                if nav:
                    add(record, f"/evidence/{i}/kind", evidence["kind"], "contradicted",
                        "Remove navigation from substantive life evidence.", url, locator,
                        "原文確在官方頁，但DOM位於導覽選單；來源官方不代表該文字是生活證據。", inventory)
    added = append_review_decisions(ROOT / "docs/data-verification-20261021", decisions.values()) if append_decisions else 0
    return {"decisions": len(decisions), "added": added,
        "statuses": dict(Counter(r["base_status"] for r in decisions.values())), "unbound_raw_fields": unbound}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--append-decisions", action="store_true")
    print(json.dumps(report(parser.parse_args().append_decisions), ensure_ascii=False))
