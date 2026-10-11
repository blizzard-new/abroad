"""Measure mapped fields and remaining public reads against the sixth handoff."""
from __future__ import annotations

import json
from collections import Counter

from fetch_ccu_completion_sources import BUNDLE as B


def read(name):
    return json.loads((B / name).read_text())


def main():
    baseline = read("completion-seventh-baseline.json")
    current = read("completion-reviewed-fields.json")["schools"]
    queue = read("completion-remaining-public-worklist.json")
    sources = [s for r in queue["schools"] for s in r["sources"]] + queue["shared_and_global_sources"]
    by_id = {s["source_id"]: s for s in sources}
    ledger = [r for r in read("completion-public-body-reviews.json") if r.get("batch") == 7]
    changed = []
    for row in current:
        old = baseline["prior_fields"][str(row["ccu_page"])]
        for scope in ["host_fields", "profile_fields", "general_campus_fields"]:
            for key, field in row[scope].items():
                before = old[scope][key]
                now = {"status": field["status"], "value": field["value"], "evidence_source_ids": [e.get("source_id") for e in field["evidence"]]}
                if now != before:
                    changed.append({"ccu_page": row["ccu_page"], "school_name": row["school_name"], "scope": scope, "field": key,
                                    "previous_status": before["status"], "status": field["status"], "value": field["value"],
                                    "new_source_ids": sorted(set(now["evidence_source_ids"]) - set(before["evidence_source_ids"]))})
    priority = read("completion-seventh-reading-input.json")
    # Same-school same-byte deduplication never discards an acquired URL.
    pending = [s for r in queue["schools"] for s in r["sources"] if s["review_state"] == "readable_body_without_recorded_review"]
    keys = [(s["ccu_page"], s["sha256"] or s["source_id"]) for s in pending]
    report = {"prior_commit": baseline["prior_commit"], "checked_at": "2026-10-11",
              "priority_urls_processed": len(priority), "priority_distinct_bodies_processed": len({(s["ccu_page"], s["sha256"]) for s in priority}),
              "priority_disposition_counts": dict(Counter(r.get("disposition", "additional_source") for r in ledger)),
              "new_scoped_reading_records": len(ledger), "new_scoped_reading_independent_bodies": len({(r["ccu_page"], r["content_hash"]) for r in ledger}),
              "reading_record_is_not_policy_verification": True,
              "old_priority_still_without_recorded_read": [s["source_id"] for s in priority if by_id[s["source_id"]]["review_state"] == "readable_body_without_recorded_review"],
              "prior_counts": baseline["prior_counts"], "current_counts": queue["counts"],
              "remaining_school_public_source_urls": len(pending), "remaining_school_public_independent_bodies": len(set(keys)),
              "remaining_public_sources_exhausted": False,
              "changed_platform_fields": len(changed), "changed_host_fields": sum(r["scope"] == "host_fields" for r in changed),
              "previously_missing_host_fields_filled": sum(r["scope"] == "host_fields" and r["previous_status"] == "missing" and r["status"] != "missing" for r in changed),
              "changed_fields": changed,
              "external_private_steps": [{"ccu_page": r["ccu_page"], "fields": [f["field"] for f in r["external_access_limited_steps"]]} for r in queue["schools"] if r["external_access_limited_steps"]]}
    assert not report["old_priority_still_without_recorded_read"]
    (B / "completion-seventh-public-progress.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    limits = read("completion-remaining-limitations.json")
    old = {r["ccu_page"]: r for r in limits["schools"]}
    updated = []
    for row in queue["schools"]:
        if not row["asset_gaps"]:
            continue
        item = old[row["ccu_page"]]
        item["asset_gaps"] = row["asset_gaps"]
        item["attempted_source_ids"] = sorted(set(item["attempted_source_ids"]) | {s["source_id"] for s in row["sources"] if "-seventh-" in s["source_id"]})
        if row["ccu_page"] == 44:
            item["seventh_result"] = "官方calendar、campusmap及Adams Bluebook新路徑均503；沒有可讀正文核網站身份，非校方帳號限制。"
        if row["ccu_page"] == 71:
            item["seventh_result"] = "公開360 bus新入口為Javascript容器；無institution marker或影像重用授權，不由viewer位置推GPS。"
        if row["ccu_page"] == 111:
            item["seventh_result"] = "官方opf.slu.cz新路徑HTTP200為Anubis挑戰；未繞過。opakarvina.cz為另一中學，已排除身份，非大學校園座標。"
        updated.append(item)
    limits["schools"] = updated
    limits["seventh_leti_resolution"] = {"ccu_page": 96, "website": "https://etu.ru/en/university/", "identity_source_id": "p96-seventh-official-rafu", "main_url_source_id": "p96-seventh-linked-university", "main_url_http_status": 503, "reason": "官方子站LETI正文與主站anchor核身份；主URL取得503另記，不宣稱網站正文取得成功。"}
    limits["gamma"]["seventh_result"] = {"source_id": "p0-seventh-gamma-public-doc", "public_doc_url": "https://gamma.app/docs/hdozbiaaek5nkn0", "http_status": 200, "body_result": "空pageProps、無全卡片正文或公開export链接", "normal_tls_browser_error": "ERR_CERT_AUTHORITY_INVALID", "exclusive_access_proven": False, "complete_public_export_obtained": False}
    limits["public_reading_remains"] = {"worklist": "completion-remaining-public-worklist.json", "reading_record_missing_sources": len(pending), "independent_bodies": len(set(keys)), "priority_policy_candidates": queue["counts"]["priority_policy_candidates"], "external_cannot_solve_scope": "僅實際個人帳號／提名步驟及權利持有人圖授權；其他未讀來源繼續查，並非終止清單。"}
    (B / "completion-remaining-limitations.json").write_text(json.dumps(limits, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({k: report[k] for k in ["new_scoped_reading_records", "new_scoped_reading_independent_bodies", "changed_platform_fields", "changed_host_fields", "previously_missing_host_fields_filled", "remaining_school_public_source_urls", "remaining_school_public_independent_bodies"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
