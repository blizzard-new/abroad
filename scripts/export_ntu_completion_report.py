"""Export the complete review grain without promoting discovered paragraphs.

Run with a Python installation providing openpyxl for the optional Excel export.
"""
from __future__ import annotations

from collections import Counter
import argparse
import csv
import gzip
import json
from pathlib import Path
from urllib.parse import urlsplit

from scripts.audit_ntu_completion import audit
from exchange_info.ntu_field_review import FIELD_OUTCOMES

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "docs/ntu-completion-20261011"


def classify_review_axes(row, observations, sources, decision=None, more_public_leads=False):
    """Keep publication, transport and unfinished reading as separate questions."""
    decision = decision or {}
    reviewed_hashes = {s.get("sha256") for s in decision.get("sources", []) if s.get("sha256")}
    reviewed_hashes |= {s.get("sha256") for s in observations if s.get("sha256")}
    candidates = [s["source"] for s in sources if s.get("field_candidate_counts", {}).get(row["field"], 0)]
    readable = [s for s in candidates if s["access_status"] == "content_available"]
    unread = [s for s in readable if s.get("sha256") not in reviewed_hashes]
    publication = "not_determined_for_target_cycle"
    if row["field"] == "home_selection" and row["target_requirement_confirmed"]:
        publication = "official_NTU_shared_current_cycle_rule"
    elif row["field"] == "quota":
        publication = "official_zero_not_open" if row["target_requirement_confirmed"] else "official_NTU_selection_cell_blank"
    elif any(o["applicability_status"] == "explicitly_pending_announcement" for o in observations):
        publication = "official_statement_future_details_pending"
    elif any(o["applicability_status"] == "target_year_explicit" for o in observations):
        publication = "official_host_target_cycle_partial_fact"
    elif observations:
        publication = "public_reference_in_original_scope"
    elif row["reference_present"]:
        publication = "prior_reference_current_cycle_unconfirmed"
    access = "readable_field_candidate_body" if readable else "reviewed_public_reference_body" if observations or decision else "no_readable_field_candidate_obtained"
    progress = "pending_public_body_read" if unread else "additional_discovery_outside_frozen_review_scope" if more_public_leads else "bounded_field_search_no_verified_text"
    if decision:
        progress = "manual_semantic_review_partial_more_bodies" if unread else decision["outcome"]
        if decision.get("bounded_field_conclusion_complete") and not unread:
            progress = decision["outcome"]
    elif observations:
        progress = "reviewed_reference_partial_more_bodies" if unread else "reviewed_reference_partial_scope"
    elif row["reference_present"]:
        progress = "prior_reference_with_unread_public_candidates" if unread else "prior_reference_target_scope_not_rechecked"
    legacy_context = {"readable_scanned_PDF_not_yet_reviewed": "scanned_context_only_no_verified_life_text",
        "readable_index_details_not_yet_read": "existing_index_insufficient_field_evidence"}
    progress = legacy_context.get(progress, progress)
    return {"publication_status": publication, "field_access_status": access,
            "review_progress": progress, "manual_review_outcome": decision.get("outcome", ""),
            "manual_review_note_zh": decision.get("note_zh", ""),
            "field_final_conclusion": decision.get("outcome", "") if decision.get("bounded_field_conclusion_complete") else "",
            "field_final_conclusion_zh": FIELD_OUTCOMES.get(decision.get("outcome"), "") if decision.get("bounded_field_conclusion_complete") else "",
            "bounded_field_conclusion_complete": bool(decision.get("bounded_field_conclusion_complete")) and not unread,
            "missing_current_cycle_items": decision.get("missing_current_cycle_items", []),
            "necessary_public_links_not_fetched": decision.get("necessary_public_links_not_fetched", []),
            "candidate_field_fitness": decision.get("sources", []) if decision.get("bounded_field_conclusion_complete") else [],
            "readable_candidate_source_ids": sorted({s["source_id"] for s in readable}),
            "unread_candidate_source_ids": sorted({s["source_id"] for s in unread}),
            "unread_candidate_body_count": len({s.get("sha256") or s["source_id"] for s in unread}),
            "external_blocker_exclusive": not (row["reference_present"] or row["target_requirement_confirmed"] or readable or observations or decision) and bool(sources) and all(s["source"]["access_status"] != "content_available" for s in sources)}


def export(output=OUTPUT, access_path=None):
    records, summary = audit(ROOT)
    snapshot = json.loads((ROOT / "sources/ntu/completion-2026-10-11.json").read_text())
    access_path = access_path or ROOT / "sources/ntu/host-access-current-2026-10-11.json.gz"
    if not access_path.exists():
        access_path = ROOT / "sources/ntu/host-access-2026-10-11.json.gz"
    access = json.loads(gzip.decompress(access_path.read_bytes()))
    schools = {r["portal_id"]: r for r in snapshot["schools"]}
    manual_path = ROOT / "sources/ntu/semantic-review-current-2026-10-11.json"
    manual = {(r["portal_id"], r["field"]): r for r in json.loads(manual_path.read_text())} if manual_path.exists() else {}
    progress_path = ROOT / "sources/ntu/priority-review-progress-current-2026-10-11.json"
    progress = json.loads(progress_path.read_text()) if progress_path.exists() else None
    original_sets = {(r["portal_id"], r["field"]): r for r in progress["fields"]} if progress else {}
    full_body_path = ROOT / "sources/ntu/full-body-review-current-2026-10-11.json"
    full_body = json.loads(full_body_path.read_text()) if full_body_path.exists() else []
    attempts = {r["portal_id"]: r for r in access["schools"]}
    robots = {urlsplit(r["url"]).netloc: r for r in access["robots_receipts"]}
    issues = []
    for row in records:
        school = schools[row["portal_id"]]
        observations = [r for r in school["observations"] if r["field"] == row["field"]]
        query = attempts[row["portal_id"]]
        if row["field"] == "photos" and not row["reference_present"]:
            rejected = [r for r in snapshot.get("photo_rejections", []) if r["school_name"] == row["school_name"]]
            if rejected:
                row["note"] = "本輪候選已拒絕：" + "；".join(r["reason"] for r in rejected) + "。仍須取得符合校區與授權的校園照片。"
            if school.get("photo_candidate_pending_download"):
                row["note"] = "已有具名校區與授權候選；下載受代理503影響，未完成影像視覺核對，不作已核可照片展示。"
        sources = [r for r in query["sources"] if "mac.gov.tw" not in r["source"]["url"]]
        reasons = set()
        for source in sources:
            detail = source["source"]
            status = detail["access_status"]
            robot = robots.get(urlsplit(detail["url"]).netloc, {})
            if status == "robots_disallowed_or_unavailable":
                code = robot.get("http_status")
                reasons.add("transport_proxy_503" if code == 503 else
                            "robots_unavailable_403" if code == 403 else
                            "rate_limited_429" if code == 429 else "robots_policy_or_receipt_unresolved")
            elif status != "content_available":
                reasons.add("http_503" if detail.get("http_status") == 503 else status)
        if query.get("unfetched_seeds") or query.get("queued_discovery_leads"):
            reasons.add("additional_public_leads_not_yet_read")
        periods = {r["applicability_status"] for r in observations}
        enriched = [{**o, "sha256": snapshot["public_source_reviews"][o["source_id"]]["sha256"]} for o in observations]
        decision = manual.get((row["portal_id"], row["field"]))
        axes = classify_review_axes(row, enriched, sources, decision,
            bool(query.get("unfetched_seeds") or query.get("queued_discovery_leads")))
        issue = "target_scope_unconfirmed"
        if row["target_requirement_confirmed"]:
            issue = "asset_or_home_fact_checked_exchange_assignment_still_separate"
        elif row["field"] == "quota":
            issue = "official_list_blank_as_of_check"
        elif "version_conflict" in periods or row["status"] == "conflict":
            issue = "version_conflict_requires_confirmation"
        elif "explicitly_pending_announcement" in periods:
            issue = "officially_stated_future_update_pending"
        elif observations:
            issue = "reviewed_fact_in_original_scope"
        elif row["reference_present"]:
            issue = "prior_reference_target_year_or_subfields_unconfirmed"
        elif row["field"] in {"coordinates", "photos"}:
            issue = "campus_identity_or_licensed_asset_unresolved"
        elif decision:
            issue = "manual_semantic_review_partial_scope" if observations else decision["outcome"]
        elif any(r["source"]["access_status"] == "content_available" and
                 r.get("field_candidate_counts", {}).get(row["field"], 0) for r in sources):
            issue = "discovery_lead_requires_semantic_review"
        elif any(r["source"]["access_status"] == "content_available" for r in sources):
            issue = "no_field_specific_candidate_or_verified_text_in_frozen_inventory"
        elif "transport_proxy_503" in reasons:
            issue = "technical_transport_failure_prevents_check"
        elif reasons:
            issue = "access_limited_no_verified_field_text"
        else:
            issue = "not_found_in_bounded_search_not_proof_unannounced"
        fact = "\n".join(r["text_zh"] for r in observations)
        dependencies = sorted({r["access_dependency"] for r in observations if r.get("access_dependency")})
        if dependencies:
            issue = "public_reference_details_after_acceptance"
        if axes["bounded_field_conclusion_complete"]:
            issue = decision["outcome"]
            reasons.discard("additional_public_leads_not_yet_read")
        issue = {"readable_scanned_PDF_not_yet_reviewed": "scanned_context_only_no_verified_life_text",
                 "readable_index_details_not_yet_read": "existing_index_insufficient_field_evidence"}.get(issue, issue)
        issue_row = {**row, **axes, "issue_code": issue, "access_reasons": sorted(reasons),
            "reviewed_fact_zh": fact, "applicability": " | ".join(dict.fromkeys(r["scope"] for r in observations)),
            "pdf_pages": " | ".join(str(r["pdf_page"]) for r in observations if r.get("pdf_page")),
            "source_quote_ids": sorted({r["quote_source_id"] for r in observations}),
            "access_dependencies": dependencies,
            "source_attempt_count": len(query["sources"]),
            "unfetched_lead_count": len(query.get("unfetched_seeds", [])) + len(query.get("queued_discovery_leads", [])),
            "reviewer_reply": "", "verified_source_url": "", "verified_scope": "", "verified_quote_or_page": ""}
        original_set = original_sets.get((row["portal_id"], row["field"]))
        issue_row.update(
            fixed_priority_original_body_set_complete=original_set["all_original_cached_candidates_read"] if original_set else None,
            original_cached_candidate_count=original_set["original_cached_candidate_body_count"] if original_set else None,
            original_cached_read_count=original_set["read_count"] if original_set else None,
            original_cached_remaining_source_ids=original_set["remaining_source_ids"] if original_set else [])
        issues.append(issue_row)
    summary.update(access_attempts=access["counts"], new_observations=sum(len(r["observations"]) for r in schools.values()),
        reviewed_host_schools=sum(bool(r["observations"]) for r in schools.values()),
        new_life_evidence=sum(len(r.get("life_evidence", [])) for r in schools.values()),
        issue_codes=dict(Counter(r["issue_code"] for r in issues)),
        publication_statuses=dict(Counter(r["publication_status"] for r in issues)),
        review_progresses=dict(Counter(r["review_progress"] for r in issues)),
        readable_unread_rows=sum(bool(r["unread_candidate_body_count"]) for r in issues),
        exclusive_external_blocker_rows=sum(r["external_blocker_exclusive"] for r in issues),
        fixed429_final_conclusion_rows=sum(r["bounded_field_conclusion_complete"] for r in issues),
        fixed429_outcomes=dict(Counter(r["field_final_conclusion"] for r in issues if r["bounded_field_conclusion_complete"])),
        original_handoff_comparison={"original_workbook_retrieved": False, "reported_previous_denominator": 282,
            "rebuilt_denominator": 288, "pending_selection_denominator": 282, "zero_selection_denominator": 6,
            "comparison_method": "Rebuilt using the current official portal IDs. The old workbook was not obtained; neither cell equality nor exact school membership overlap is claimed.",
            "coverage": "All 282 currently pending schools × original ten fields are retained; 6 zero-quota schools and four extra field groups are also included."})
    if progress:
        summary["full_body_priority_progress"] = {k: v for k, v in progress.items() if k != "fields"}
    output.mkdir(exist_ok=True, parents=True)
    (output / "review-summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n")
    (output / "all-school-review.json").write_text(json.dumps(issues, ensure_ascii=False, indent=2) + "\n")
    with (output / "all-school-review.csv").open("w", newline="", encoding="utf-8-sig") as file:
        writer = csv.DictWriter(file, fieldnames=list(issues[0]), lineterminator="\n")
        writer.writeheader()
        def csv_value(value):
            if isinstance(value, list):
                value = " | ".join(map(str, value))
            if isinstance(value, str):
                value = "\n".join(line.rstrip() for line in value.split("\n"))
            return value

        writer.writerows({k: csv_value(v) for k, v in r.items()} for r in issues)
    from openpyxl import Workbook
    from openpyxl.styles import Font, PatternFill, Alignment
    from openpyxl.worksheet.datavalidation import DataValidation
    book = Workbook()
    book.remove(book.active)
    source_index = list(snapshot["public_source_reviews"].values())
    home_path = ROOT / "sources/ntu/home-selection-current-2026-10-11.json"
    home = json.loads(home_path.read_text()) if home_path.exists() else None
    if home:
        source_index.append({"source_id": home["source_id"], "url": home["source_url"],
            "title": "臺大116-1正式甄選簡章", "checked_at": home["checked_at"],
            "sha256": home["sha256"], "original_quote": home["original_quote"],
            "quote_pdf_page": home["quote_pdf_page"], "official_authority": home["authority"]})
    sheets = [("288校逐欄回填", issues), ("來源原文索引", source_index),
              ("當日臺大來源", [snapshot["list_receipt"] | {"rows": "288筆；完整收據見候選JSON"}, *snapshot["home_source_checks"]])]
    if home:
        sheets.append(("臺大116-1正式共通規則", [{**fact, "source_url": home["source_url"],
            "checked_at": home["checked_at"], "quote_source_id": home["source_id"]}
            for fact in home["facts"]]))
    if manual:
        sheets.append(("候選段落語意分類", list(manual.values())))
    if progress:
        sheets.append(("固定501項正文進度", progress["fields"]))
    if full_body:
        sheets.append(("逐源全文閱讀紀錄", full_body))
    closed = [r for r in manual.values() if r.get("bounded_field_conclusion_complete")]
    if closed:
        sheets.append(("429欄最終結論", closed))
    for title, items in sheets:
        ws = book.create_sheet(title)
        keys = list(dict.fromkeys(k for item in items for k in item))
        ws.append(keys)
        for item in items:
            values = []
            for key in keys:
                value = item.get(key)
                if isinstance(value, (dict, list)):
                    value = json.dumps(value, ensure_ascii=False)
                if isinstance(value, str) and value[:1] in {"=", "+", "-", "@"}:
                    value = "'" + value
                values.append(value)
            ws.append(values)
        ws.freeze_panes = "D2" if title == "288校逐欄回填" else "A2"
        ws.auto_filter.ref = ws.dimensions
        for cell in ws[1]:
            cell.font = Font(color="FFFFFF", bold=True)
            cell.fill = PatternFill("solid", fgColor="163D53")
        for col in ws.columns:
            ws.column_dimensions[col[0].column_letter].width = 24
            for cell in col[1:]:
                cell.alignment = Alignment(vertical="top", wrap_text=True)
        if title == "288校逐欄回填":
            for key in ("reviewed_fact_zh", "source_urls", "note", "applicability"):
                ws.column_dimensions[ws.cell(1, keys.index(key) + 1).column_letter].width = 60
            validation = DataValidation(type="list", formula1='"已核實,待確認,版本矛盾,未找到,官方表示待公告,提名後取得,訪問受限"')
            ws.add_data_validation(validation)
            letter = ws.cell(1, keys.index("reviewer_reply") + 1).column_letter
            validation.add(f"{letter}2:{letter}{len(items)+1}")
    book.save(output / "288校逐欄查核_可回填.xlsx")
    print(json.dumps({"rows": len(issues), "sources": len(source_index),
        "observations": summary["new_observations"], "issue_codes": summary["issue_codes"]}, ensure_ascii=False))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=OUTPUT)
    parser.add_argument("--access", type=Path)
    args = parser.parse_args()
    export(args.output, args.access)
