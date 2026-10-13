"""List CCU's remaining fields and every acquired readable source without retry loops.

This is an offline reading inventory, not an exhaustive search or a policy audit.
Mapped passages, explicit reading records, identical bodies and unrecorded reads
are kept separate. A source failure never makes a whole university inaccessible.
"""
from __future__ import annotations

import csv
import json
import re
from collections import Counter, defaultdict

from fetch_ccu_completion_sources import BUNDLE as B


def read(name):
    return json.loads((B / name).read_text())


def build():
    reviewed = read("completion-reviewed-fields.json")["schools"]
    assets = {r["ccu_page"]: r for r in read("campus-assets.json")["schools"]}
    mapped = defaultdict(list)
    for school in reviewed:
        for scope in ["host_fields", "profile_fields", "general_campus_fields"]:
            for key, field in school[scope].items():
                for ev in field["evidence"]:
                    if ev.get("source_id"):
                        mapped[ev["source_id"]].append({"ccu_page": school["ccu_page"], "field": scope + "." + key,
                                                       "status": field["status"], "source_pages": ev.get("source_pages", [])})
    explicit = defaultdict(list)
    reading_by_url = defaultdict(list)
    for filename in ["public-link-reviews.json", "completion-reference-document-reviews.json",
                     "completion-public-body-reviews.json"]:
        for item in read(filename):
            if item.get("source_content_read") or item.get("review_result") or item.get("body_read"):
                entry = {"ledger": filename, "review_note": item.get("review_note") or item.get("review_result"),
                         "applicability": item.get("applicability") or item.get("academic_year")}
                if item.get("source_id"):
                    explicit[item["source_id"]].append(entry)
                elif item.get("url"):
                    reading_by_url[item["url"]].append(entry)
    for school in read("semantic-review-ledger.json"):
        for key, field in school["fields"].items():
            for sid in field.get("readable_source_ids", []):
                explicit[sid].append({"ledger": "semantic-review-ledger.json", "field": key,
                                      "review_note": field["note"]})
    triage = {r["source_id"]: r for school in read("body-review-triage.json")["schools"] for r in school["sources"]}
    sources = []
    for record in read("overseas-source-registry.json"):
        raw = read("overseas_sources/" + record["source_id"] + ".json")
        metadata = {**raw, **record}
        text = " ".join(metadata.get("text_pages", []))
        attempts = metadata.get("attempts", [])
        http = metadata.get("http_status") or next((a.get("http_status") for a in reversed(attempts)
                                                    if a.get("http_status") is not None), None)
        state = triage.get(record["source_id"], {}).get("body_state", "")
        readable = bool(text.strip()) and metadata.get("current_use_allowed") is not False and state not in {
            "body_not_obtained", "access_limited_no_policy_body", "historical_insecure_acquisition_not_current_evidence"}
        sources.append({"source_id": metadata["source_id"], "ccu_page": metadata.get("ccu_page", metadata.get("page")),
                        "source_url": metadata["source_url"], "checked_at": metadata["checked_at"],
                        "http_status": http, "sha256": metadata.get("sha256"), "text_sha256": metadata.get("text_sha256"),
                        "source_collection": "overseas_sources", "readable_body_obtained": readable,
                        "acquisition_state": state or metadata.get("status"), "academic_year": metadata.get("content_academic_year"),
                        "title": metadata.get("title"), "content_type": metadata.get("content_type"),
                        "existing_review_note": metadata.get("content_review_note"),
                        "scope_disposition": state, "links": metadata.get("links", [])})
    for record in read("completion-public-source-screening.json")["sources"]:
        sid = record["source_id"]
        raw = read("completion_sources/" + sid + ".receipt.json")
        decision = record["decision"]
        readable = decision in {"acquired_not_policy_verified", "used_with_explicit_field_status"}
        sources.append({"source_id": sid, "ccu_page": record["ccu_page"], "source_url": record["source_url"],
                        "resolved_url": record.get("resolved_url"), "checked_at": record["checked_at"],
                        "http_status": record["http_status"], "sha256": record["original_sha256"],
                        "text_sha256": raw.get("text_sha256"), "source_collection": "completion_sources",
                        "readable_body_obtained": readable, "acquisition_state": decision,
                        "academic_year": None, "title": raw.get("title"), "content_type": raw.get("content_type"),
                        "bundled_file": record["bundled_file"], "scope_disposition": decision, "links": raw.get("links", [])})
    # Same source ID occurs in only one collection here; fail rather than discard a collision.
    assert len({r["source_id"] for r in sources}) == len(sources)
    for source in sources:
        explicit[source["source_id"]].extend(reading_by_url.get(source["source_url"], []))
        previous = triage.get(source["source_id"], {})
        state = previous.get("body_state", "")
        if state.startswith(("mapped_", "identical_body_to_mapped_", "reviewed_index_")):
            explicit[source["source_id"]].append({"ledger": "body-review-triage.json", "body_state": state,
                                                   "review_note": "既有逐段引用／索引閱讀紀錄；保留原範圍，不宣稱全文完成。"})
    known_hashes = defaultdict(set)
    for source in sources:
        if source["sha256"] and (mapped.get(source["source_id"]) or explicit.get(source["source_id"])):
            known_hashes[(source["ccu_page"], source["sha256"])].add(source["source_id"])
    for source in sources:
        sid = source["source_id"]
        hint = " ".join(str(source.get(k) or "") for k in ["source_id", "source_url", "title", "content_type"])
        metadata_only = bool(re.search(r"api\.ror\.org|wikidata\.org|commons\.wikimedia\.org|upload\.wikimedia|tour.*\.js|script.*\.js|gamma\.app/.*(?:chunks|manifest)", hint, re.IGNORECASE))
        same = sorted(known_hashes[(source["ccu_page"], source["sha256"])] - {sid}) if source["sha256"] else []
        source["same_bytes_as_recorded_read_sources"] = same
        source["mapped_field_sections"] = mapped.get(sid, [])
        source["explicit_reading_records"] = explicit.get(sid, [])
        source["review_state"] = (
            "source_failure_or_body_not_obtained" if not source["readable_body_obtained"] else
            "metadata_or_asset_candidate_not_policy_body" if metadata_only else
            "reviewed_scoped_exclusion" if source["scope_disposition"] == "reviewed_scoped_exclusion" else
            "mapped_passages_read_remaining_body_unclaimed" if mapped.get(sid) else
            "scoped_body_read_recorded" if explicit.get(sid) else
            "same_bytes_as_recorded_read_source" if same else
            "readable_body_without_recorded_review")
        source["policy_candidate_hint"] = bool(re.search(
            r"incoming|inbound|exchange|factsheet|fact.?sheet|mobility|application|housing|accommodation|insurance|visa|calendar|交換|交换|申請|申请|宿舍|住宿",
            hint, re.IGNORECASE)) and not metadata_only
        # Keyword-based priority is for reading only, never a policy/authority/year decision.
        source.pop("links")
    by_page = defaultdict(list)
    for source in sources:
        by_page[source["ccu_page"]].append(source)
    rows = []
    for school in reviewed:
        page = school["ccu_page"]
        pending = [{"field": key, "status": field["status"], "value": field["value"], "reason": field["reason"],
                    "classification": field.get("research_classification", "official_not_announced" if field["status"] == "explicit_not_announced" else "research_incomplete"),
                    "evidence": field["evidence"], "access_requirement_evidence": field.get("access_requirement_evidence", [])}
                   for key, field in school["host_fields"].items() if field["status"] != "verified_current"]
        gaps = [key for key in ["coordinates", "photo"] if assets[page][key]["status"] != "verified_current"]
        if school["profile_fields"]["website"]["status"] != "verified_current":
            gaps.append("website")
        school_sources = sorted(by_page[page], key=lambda r: r["source_id"])
        to_read = [s["source_id"] for s in school_sources if s["review_state"] == "readable_body_without_recorded_review"]
        priority = [s["source_id"] for s in school_sources if s["source_id"] in to_read and s["policy_candidate_hint"]]
        rows.append({"ccu_page": page, "school_name": school["school_name"], "country": school["country"],
                     "availability_status": school["availability_status"], "application_window_status": school["application_window_status"],
                     "asset_gaps": gaps, "pending_host_fields": pending,
                     "host_missing_count": sum(f["status"] == "missing" for f in school["host_fields"].values()),
                     "public_reading_record_missing_source_ids": to_read, "priority_policy_candidate_source_ids": priority,
                     "external_access_limited_steps": [f for f in pending if f["classification"] == "personal_access_required"],
                     "sources": school_sources})
    return {"checked_at": "2026-10-11", "scope": "104交換名冊校的既有來源閱讀清單；非全網搜尋窮盡、非全部協議校清單",
            "definitions": {"readable_body_without_recorded_review": "取得可讀正文但沒有逐段閱讀紀錄；待我閱讀／核計畫及年度，不能當外部限制。",
                            "mapped_passages_read_remaining_body_unclaimed": "只證明引用段已讀，沒有宣稱全文或所有剩餘欄完成；必要時續讀指定段。",
                            "scoped_body_read_recorded": "已有閱讀紀錄，保留原範圍／年度；無足夠當期資料並非未閱讀。",
                            "same_bytes_as_recorded_read_source": "同校SHA相同，保留網址與讀過來源ID；不重複計成新內容。",
                            "external_access_limited_steps": "僅有直接正文／登入依據的私有步驟；公開政策仍可繼續查。",
                            "source_failure_or_body_not_obtained": "僅此URL／當時取得失敗，未證明全校只供校方取得。",
                            "policy_candidate_hint": "標題／URL關鍵字僅用閱讀排序，不代表已核實官方、incoming、年度或政策。"},
            "counts": {"schools": len(rows), "sources": len(sources), "source_review_states": dict(Counter(s["review_state"] for s in sources)),
                       "coordinate_gaps": sum("coordinates" in r["asset_gaps"] for r in rows),
                       "photo_gaps": sum("photo" in r["asset_gaps"] for r in rows),
                       "website_gaps": sum("website" in r["asset_gaps"] for r in rows),
                       "host_missing_fields": sum(r["host_missing_count"] for r in rows),
                       "public_reading_record_missing_sources": sum(len(r["public_reading_record_missing_source_ids"]) for r in rows),
                       "priority_policy_candidates": sum(len(r["priority_policy_candidate_source_ids"]) for r in rows)},
            "schools": rows, "shared_and_global_sources": by_page.get(None, []) + by_page.get(0, [])}


def main():
    result = build()
    (B / "completion-remaining-public-worklist.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    with (B / "completion-remaining-public-worklist.csv").open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow(["ccu_page", "school_name", "availability_status", "host_missing_count", "asset_gaps", "source_id", "source_url", "checked_at", "academic_year", "review_state", "same_bytes_as_recorded_read_sources", "policy_candidate_hint"])
        for school in result["schools"]:
            for source in school["sources"]:
                writer.writerow([school["ccu_page"], school["school_name"], school["availability_status"], school["host_missing_count"],
                                 ";".join(school["asset_gaps"]), source["source_id"], source["source_url"], source["checked_at"], source["academic_year"],
                                 source["review_state"], ";".join(source["same_bytes_as_recorded_read_sources"]), source["policy_candidate_hint"]])
    print(json.dumps(result["counts"], ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
