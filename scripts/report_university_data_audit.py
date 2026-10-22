"""Export per-partner audit progress; coverage is never factual verification."""
from __future__ import annotations

import argparse
import collections
import csv
from datetime import datetime, timezone
import gzip
import json
from pathlib import Path

from audit_university_data import GAP_RE, PARTNER_REQUIRED, is_empty
from university_review_ledger import iter_decisions

ROOT = Path(__file__).resolve().parents[1]


def report(inventory: Path, output: Path) -> dict:
    output.mkdir(parents=True, exist_ok=True)
    decisions = collections.defaultdict(list)
    for row in iter_decisions(output):
        decisions[row["base_record_id"]].append(row)
    receipts = {}
    for name in ("source-receipts.jsonl", "manual-source-receipts.jsonl", "derived-source-receipts.jsonl", "raw-source-receipts.jsonl", "special-source-receipts.jsonl"):
        path = output / name
        if not path.exists():
            continue
        for line in path.read_text("utf-8").splitlines():
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                # A live acquisition process can still be writing its last line.
                continue
            old = receipts.get(row["url"])
            if old is None or row["completed_at"] > old["completed_at"]:
                receipts[row["url"]] = row
    rows = []
    homes = collections.defaultdict(collections.Counter)
    with gzip.open(inventory / "records.jsonl.gz", "rt", encoding="utf-8") as stream:
        for line in stream:
            record = json.loads(line)
            if record["kind"] != "partner":
                continue
            data = record["data"]
            missing = [key for key in PARTNER_REQUIRED if is_empty(data.get(key))]
            provisional = [
                key for key in PARTNER_REQUIRED
                if isinstance(data.get(key), str) and GAP_RE.search(data[key])
            ]
            urls = record["candidate_urls"]
            available = sum(receipts.get(url, {}).get("transport_result") == "retrieved" for url in urls)
            failed = sum(url in receipts and receipts[url]["transport_result"] != "retrieved" for url in urls)
            reviewed = decisions.get(record["record_id"], [])
            status = "partially_reviewed" if reviewed else "pending_review"
            rows.append({
                "母校代碼": record["home_id"],
                "合作校": data.get("school_name"),
                "國家地區": data.get("country"),
                "方案": data.get("program_type"),
                "原始紀錄ID": record["record_id"],
                "本輪處理狀態": status,
                "已完成整筆事實查核": "否",
                "缺少的必要欄位": "；".join(missing),
                "含待確認文字的欄位": "；".join(provisional),
                "已有欄位查核紀錄數": len(reviewed),
                "原值與來源不符數": sum(x["base_status"] == "contradicted" for x in reviewed),
                "候選來源數": len(urls),
                "已取得來源內容數": available,
                "讀取失敗來源數": failed,
                "尚未讀取來源數": len(urls) - available - failed,
                "原始資料來源": data.get("source_url"),
            })
            count = homes[record["home_id"]]
            count["partner_rows"] += 1
            count[status] += 1
            count["rows_with_missing_required_fields"] += bool(missing)
            count["rows_with_provisional_text"] += bool(provisional)
            count["populated_required_fields_only"] += not missing
    with (output / "partner-review-progress.csv").open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]) if rows else [])
        writer.writeheader()
        writer.writerows(rows)
    summary = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "inventory": str(inventory.relative_to(ROOT)) if inventory.is_relative_to(ROOT) else str(inventory),
        "status": "in_progress",
        "partner_rows": len(rows),
        "fully_fact_verified_partner_rows": 0,
        "fully_fact_verified_schools": 0,
        "field_decisions": sum(len(items) for items in decisions.values()),
        "source_transport_counts": dict(collections.Counter(row["transport_result"] for row in receipts.values())),
        "schools": dict(homes),
        "limitations": [
            "Required-field population measures coverage only; it does not establish truth or current applicability.",
            "A candidate URL can be an image, calendar link, or unrelated source; transport success does not verify a claim.",
            "Multiple field decisions may apply the same reviewed rule to explicitly identified records.",
            "The CSV describes the preserved baseline, not an assertion that corrections are deployed.",
            "Some decisions inspect repository-generated text; their method explicitly distinguishes this from external factual verification.",
        ],
    }
    supplement_path = ROOT / "output/data-verification-20261021/derived-baseline/inventory-summary.json"
    if supplement_path.exists():
        supplement = json.loads(supplement_path.read_text("utf8"))
        summary["supplementary_raw_inventory"] = {
            "path": str(supplement_path.parent.relative_to(ROOT)),
            "school_count": supplement["school_count"],
            "record_counts": supplement["record_counts"],
            "leaf_counts": supplement["leaf_counts"],
            "candidate_source_count": supplement["candidate_source_count"],
            "overlaps_runtime_census": True,
            "facts_verified_by_extraction": 0,
        }
    raw_path = ROOT / "output/data-verification-20261021/raw-catalog-baseline/inventory-summary.json"
    if raw_path.exists():
        raw = json.loads(raw_path.read_text("utf8"))
        summary["supplementary_raw_catalog_inventory"] = {
            "path": str(raw_path.parent.relative_to(ROOT)),
            **{key: raw[key] for key in ("school_count", "record_counts", "leaf_counts", "candidate_source_count", "structural_coverage", "record_matches")},
            "overlaps_runtime_census": True, "facts_verified_by_extraction": 0,
        }
        overlay = output / "round28-workflow-version-reconciliation.json"
        if overlay.exists():
            linked = json.loads(overlay.read_text("utf8"))
            summary["supplementary_raw_catalog_inventory"]["version_reconciliation"] = {
                key: linked[key] for key in ("resolved_records", "by_home", "combined_structural_coverage",
                    "remaining_ambiguous_records", "facts_verified_by_reconciliation")}
    for key, folder in (
        ("supplementary_special_catalog_inventory", "special-catalog-baseline"),
        ("runtime_review_snapshot", "runtime-review-20261021"),
    ):
        path = ROOT / "output/data-verification-20261021" / folder / "inventory-summary.json"
        if path.exists():
            inventory_summary = json.loads(path.read_text("utf8"))
            summary[key] = {
                "path": str(path.parent.relative_to(ROOT)),
                **{name: inventory_summary[name] for name in (
                    "extracted_at", "school_count", "record_counts", "leaf_counts", "candidate_source_count", "extraction_errors"
                )},
                "overlaps_other_inventories": True,
                "facts_verified_by_extraction": 0,
            }
            if key == "runtime_review_snapshot":
                summary[key]["live_current_state"] = False
                summary[key]["captured_before_reviews"] = list(range(32, 46))
    program_review = output / "round38-ntnu-program-year-review.json"
    if program_review.exists():
        reviewed = json.loads(program_review.read_text("utf8"))
        summary["ntnu_program_year_review"] = {
            "reviewed_at": reviewed["reviewed_at"],
            "program_year_counts": reviewed["program_year_counts"],
            "patch_count": reviewed["patch_count"],
            "api_data_available_at_round38": reviewed["latest_api_check"]["data_available"],
            "facts_verified_by_provenance_counts": 0,
        }
    quota_review = output / "round39-ntnu-live-quota-review.json"
    if quota_review.exists():
        reviewed = json.loads(quota_review.read_text("utf8"))
        summary["ntnu_live_quota_review"] = {
            "reviewed_at": reviewed["reviewed_at"], "pages": len(reviewed["all_pages"]),
            "contracts": reviewed["contracts"], "schools": len(reviewed["schools"]),
            "archive_equals_live": reviewed["archive_equals_live_including_program_fields"],
            "school_categories": reviewed["school_categories"], "patch_count": reviewed["patch_count"],
            "whole_schools_verified": 0,
        }
    graduate_review = output / "round40-waseda-graduate-review.json"
    if graduate_review.exists():
        reviewed = json.loads(graduate_review.read_text("utf8"))
        summary["waseda_graduate_review"] = {
            "reviewed_at": reviewed["reviewed_at"], "school_track_rows": len(reviewed["school_rows"]),
            "visually_reviewed_pages": reviewed["visually_reviewed_pages"],
            "whole_schools_verified": 0, "home_agreement_mapping_complete": False,
        }
    for key, name in (
        ("waseda_gsaps_supplement_review", "round41-waseda-gsaps-review.json"),
        ("ntut_waseda_ips_review", "round42-ntut-waseda-ips-review.json"),
    ):
        path = output / name
        if path.exists():
            reviewed = json.loads(path.read_text("utf8"))
            summary[key] = {
                "reviewed_at": reviewed["reviewed_at"],
                "visually_reviewed_pages": reviewed["visually_reviewed_pages"],
                "patch_count": reviewed.get("patch_count"),
                "source_conflicts": reviewed.get("source_conflicts", []),
                "whole_schools_verified": 0,
                "home_agreement_mapping_complete": False,
            }
    display_followup = output / "round42-ntut-ips-display-followup.json"
    if display_followup.exists():
        followup = json.loads(display_followup.read_text("utf8"))
        summary["ntut_waseda_ips_review"]["display_followup_patch_count"] = followup["patch_count"]
    ncku_table = output / "round43-ncku-partner-table-review.json"
    if ncku_table.exists():
        reviewed = json.loads(ncku_table.read_text("utf8"))
        summary["ncku_mother_partner_table_review"] = {
            "reviewed_at": reviewed["reviewed_at"],
            "source_rows": len(reviewed["source_rows"]),
            "pages_visually_reviewed": reviewed["pages_visually_reviewed"],
            "patch_count": reviewed["patch_count"],
            "follow_up": reviewed["follow_up"],
            "whole_records_verified": 0, "whole_schools_verified": 0,
            "host_verification_complete": False,
        }
    ncku_guide = output / "round44-ncku-guidelines-review.json"
    if ncku_guide.exists():
        reviewed = json.loads(ncku_guide.read_text("utf8"))
        followup = json.loads((output / "round44-ncku-display-followup.json").read_text("utf8"))
        summary["ncku_mother_guidelines_review"] = {
            "reviewed_at": reviewed["reviewed_at"],
            "pages_text_and_visually_read": reviewed["pages_text_and_visually_read"],
            "current_partners": 97, "main_patches": reviewed["patch_count"],
            "singleton_patches": reviewed["singleton_patch_count"],
            "duplicate_display_patches": followup["patch_count"],
            "whole_records_verified": 0, "whole_schools_verified": 0,
            "host_verification_complete": False,
            "limitations": reviewed["known_limitations"],
        }
    host_review = output / "round45-vilnius-akita-review.json"
    if host_review.exists():
        reviewed = json.loads(host_review.read_text("utf8"))
        cost_followup = json.loads((output / "round45-cost-applicability-followup.json").read_text("utf8"))
        summary["vilnius_akita_host_review"] = {
            "reviewed_at": reviewed["reviewed_at"],
            "mother_schools": len({row["home_id"] for row in reviewed["school_audit"]}),
            "partner_records": len(reviewed["school_audit"]),
            "patched_rows": len(reviewed["rows"]),
            "patches": sum(len(row["patches"]) for row in reviewed["rows"]),
            "cost_applicability_patches": sum(len(row["patches"]) for row in cost_followup["rows"]),
            "sources": reviewed["sources"],
            "whole_records_verified": 0, "whole_schools_verified": 0,
            "limitations": [row["unresolved"] for row in reviewed["school_audit"]],
            "excluded_identities": reviewed["excluded_identities"],
            "not_reviewed_sources": reviewed["not_reviewed_sources"],
        }
    fju_review = output / "round46-fju-route-source-review.json"
    if fju_review.exists():
        reviewed = json.loads(fju_review.read_text("utf8"))
        links = json.loads((output / "round46-fju-attachment-link-review.json").read_text("utf8"))
        after = output / "round46-route-identities-after.json"
        identity = json.loads(after.read_text("utf8")) if after.exists() else None
        summary["fju_route_source_review"] = {
            "reviewed_at": reviewed["reviewed_at"],
            "source_table_rows": len(reviewed["table_transcription"]),
            "reviewed_existing_routes": len(reviewed["school_audit"]),
            "missing_distinct_source_routes": reviewed["unmatched_source_routes"],
            "source_review_patches": sum(len(row["patches"]) for row in reviewed["rows"]),
            "attachment_url_patches": sum(len(row["patches"]) for row in links["rows"]),
            "identity_audit_mother_count": identity["home_count"] if identity else None,
            "remaining_storage_collisions": len(identity["collisions"]) if identity else None,
            "whole_records_verified": 0, "whole_schools_verified": 0,
            "limitations": reviewed["limitations"],
        }
    fju_form = output / "round47-fju-form-review.json"
    fju_added = output / "round47-fju-missing-routes.json"
    if fju_form.exists() and fju_added.exists():
        form = json.loads(fju_form.read_text("utf8"))
        added = json.loads(fju_added.read_text("utf8"))
        bundle = ROOT / "src/exchange_info/official_data/fju/partners.jsonl"
        present = {json.loads(line)["school_name"] for line in bundle.read_text("utf8").splitlines() if line.strip()}
        new_names = [row["school_name"] for row in added["records"] if row["file"].endswith("/partners.jsonl")]
        included = [name for name in new_names if name in present]
        additional_rows = [
            {"母校代碼": "fju", "合作方案": row["school_name"],
             "母校附表頁次": row["source_page"],
             "已核對母校欄位": "；".join(row["reviewed_mother_fields"]),
             "尚未核實": "；".join(row["not_verified"]),
             "原始盤點紀錄ID": "", "已完成整筆事實查核": "否",
             "證據紀錄": "round47-fju-missing-routes.json"}
            for row in added["school_audit"]
        ]
        with (output / "additional-partner-review-progress.csv").open("w", encoding="utf-8-sig", newline="") as stream:
            writer = csv.DictWriter(stream, fieldnames=list(additional_rows[0]))
            writer.writeheader()
            writer.writerows(additional_rows)
        summary["scope_reconciliation"] = {
            "original_inventory_partner_plans": len(rows),
            "additional_source_discovered_partner_plans": len(new_names),
            "additional_plans_present_in_bundle": len(included),
            "current_scope_partner_plans": len(rows) + len(included),
            "additional_plan_names": new_names,
            "additional_plan_report": "additional-partner-review-progress.csv",
            "original_inventory_unchanged": True,
            "note": "Counts are mother-school/program rows, not unique overseas institutions. Added rows have separate source manifests and are not fabricated original-inventory bindings.",
        }
        summary["fju_form_and_added_routes_review"] = {
            "reviewed_at": form["reviewed_at"],
            "form_pages_text_and_visual_reviewed": form["form_pages_text_and_visual_reviewed"],
            "form_patches": sum(len(row["patches"]) for row in form["rows"] + form["singletons"]),
            "added_partner_plans": len(included),
            "added_data_rows": added["new_rows"],
            "source_audit": added["school_audit"],
            "whole_records_verified": 0, "whole_schools_verified": 0,
            "limitations": form["limitations"],
        }
        if "fju_route_source_review" in summary:
            summary["fju_route_source_review"]["distinct_self_funded_routes_added_in_round47"] = included
            summary["fju_route_source_review"]["missing_routes_note"] = "The round46 missing-route list is historical. Round47 added the named rows with reference-only evidence; host verification remains incomplete."
    fju_nonjp = output / "round48-fju-nonjp-review.json"
    fju_briefing = output / "round48-fju-briefing-review.json"
    fju_process = output / "round48-fju-process-review.json"
    if all(path.exists() for path in (fju_nonjp, fju_briefing, fju_process)):
        nonjp = json.loads(fju_nonjp.read_text("utf8"))
        briefing = json.loads(fju_briefing.read_text("utf8"))
        process = json.loads(fju_process.read_text("utf8"))
        summary["fju_nonjp_and_briefing_review"] = {
            "reviewed_at": process["reviewed_at"],
            "nonjapanese_source_table_rows": len(nonjp["table_transcription"]),
            "nonjapanese_table_patches": sum(len(r["patches"]) for r in nonjp["rows"]),
            "briefing_scoring_patches": sum(len(r["patches"]) for r in briefing["rows"] + briefing["singletons"]),
            "selection_process_patches": sum(len(r["patches"]) for r in process["rows"] + process["singletons"]),
            "nonjapanese_sources": nonjp["sources"], "briefing_sources": process["sources"],
            "source_conflicts_and_followups": briefing["source_conflicts_and_followups"],
            "latest_visual_review_note": "The earlier scoring manifest recorded pages 13-20. The subsequent process review also inspected pages 10, 21 and 36; 28 pages remain without visual review.",
            "nonjapanese_audit_csv": "round48-fju-nonjp-audit.csv",
            "whole_records_verified": 0, "whole_schools_verified": 0,
        }
        completion_path = output / "round48-fju-source-review-completion.json"
        if completion_path.exists():
            completion = json.loads(completion_path.read_text("utf8"))
            review = summary["fju_nonjp_and_briefing_review"]
            review["reviewed_at"] = completion["reviewed_at"]
            review["source_review_completion"] = completion_path.name
            review["completed_source_page_review"] = {
                item["source_id"]: {
                    "text_pages_read": item["text_pages_read"],
                    "visual_pages_read": item["visual_pages_read"],
                }
                for item in completion["sources"]
            }
            review["latest_visual_review_note"] = completion["scope_note"]
            review["additional_source_followups"] = completion["followups"]
    round49_path = output / "round49-fju-host-and-cost-review.json"
    if round49_path.exists():
        r49 = json.loads(round49_path.read_text("utf8"))
        summary["fju_host_and_cost_review_round49"] = {
            "reviewed_at": r49["reviewed_at"],
            "patched_row_scopes": len(r49["rows"]),
            "patched_singletons": len(r49["singletons"]),
            "patch_count": sum(len(r["patches"]) for r in r49["rows"] + r49["singletons"]),
            "host_schools_reviewed": [
                "天普大學 Temple University",
                "蒙特雷大學 Universidad de Monterrey",
                "普福爾茨海姆大學 Pforzheim University",
                "香港浸會大學 Hong Kong Baptist University",
            ],
            "sources": r49["sources"],
            "whole_records_verified": 0,
            "whole_schools_verified": 0,
        }
    round50_path = output / "round50-ncku-waseda-followup-review.json"
    if round50_path.exists():
        r50 = json.loads(round50_path.read_text("utf8"))
        summary["ncku_waseda_followup_review_round50"] = {
            "reviewed_at": r50["reviewed_at"],
            "patched_row_scopes": len(r50["rows"]),
            "patch_count": sum(len(r["patches"]) for r in r50["rows"]),
            "sources": r50["sources"],
            "whole_records_verified": 0,
            "whole_schools_verified": 0,
        }
    round51_path = output / "round51-main6-provenance-review.json"
    if round51_path.exists():
        r51 = json.loads(round51_path.read_text("utf8"))
        summary["main6_provenance_and_template_review_round51"] = {
            "reviewed_at": r51["reviewed_at"],
            "schools": list(r51["schools"].keys()),
            "partner_rows_bound": sum(len(s["partners"]) for s in r51["schools"].values()),
            "destination_profiles_cost_bounded": sum(len(s["destinations"]) for s in r51["schools"].values()),
            "student_life_snapshots_reviewed": sum(len(s["life"]) for s in r51["schools"].values()),
            "student_experience_rows_reviewed": sum(len(s["stories"]) for s in r51["schools"].values()),
            "whole_records_verified": 0,
            "whole_schools_verified": 0,
            "note": "Main's 6 newly onboarded schools (ncue, nknu, tmu, csmu, cmu, kmu) are audited for mother-school field provenance and template withdrawal without inflating the original 25-school baseline census.",
        }
    (output / "review-progress.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    return summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--inventory", type=Path, default=ROOT / "output/data-verification-20261021/baseline")
    parser.add_argument("--output", type=Path, default=ROOT / "docs/data-verification-20261021")
    args = parser.parse_args()
    summary = report(args.inventory.resolve(), args.output.resolve())
    print(json.dumps({key: value for key, value in summary.items() if key not in {"schools", "limitations"}}, ensure_ascii=False))
