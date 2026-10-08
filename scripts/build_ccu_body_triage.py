"""Reconcile saved bodies, actual read ledgers and field mappings per CCU host.

Acquisition and keyword matches never establish semantic review or currency.
"""

from __future__ import annotations

import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BUNDLE = ROOT / "src/exchange_info/official_data/ccu"
LIMITS = {"empty_response", "challenge_page", "captcha_required", "unrelated_content_anomaly", "password_protected"}


def read(name):
    return json.loads((BUNDLE / name).read_text())


def main():
    registry = read("overseas-source-registry.json")
    raw = {s["source_id"]: read("overseas_sources/" + s["source_id"] + ".json") for s in registry}
    hosts = read("overseas-reviewed-fields.json")
    profiles = {s["ccu_page"]: s for s in read("profile-reviewed-fields.json")}
    mapped = defaultdict(list)
    for kind, rows in [("host", hosts), ("profile", profiles.values())]:
        for row in rows:
            for key, field in row["fields"].items():
                for evidence in field["evidence"]:
                    if evidence.get("source_id"):
                        mapped[evidence["source_id"]].append({"kind": kind, "field": key, "status": field["status"], "source_pages": evidence.get("source_pages", [])})
    reviews = defaultdict(list)
    ledger = read("semantic-review-ledger.json")
    for school in ledger:
        for key, field in school["fields"].items():
            for sid in field.get("readable_source_ids", []):
                reviews[sid].append({"ledger": "semantic-review-ledger.json", "extent": "specified_field_sections", "field": key, "checked_at": field.get("reviewed_at"), "result": field.get("result")})
    review_files = sorted(BUNDLE.glob("*source-review.json"))
    for path in review_files:
        for entry in read(path.name).get("source_reviews", []):
            sid = entry.get("source_id")
            # Preserve the exact saved body relation. Same URL can return a
            # different year or a challenge page; it is insufficient alone.
            if sid not in raw or not entry.get("source_content_read"):
                continue
            if entry.get("sha256") and entry["sha256"] != raw[sid].get("sha256"):
                continue
            reviews[sid].append({"ledger": path.name, "extent": entry.get("review_extent", "necessary_sections"), "checked_at": entry.get("checked_at"), "note": entry.get("review_note"), "sha256": entry.get("sha256")})
    schools = []
    for host in hosts:
        page = host["ccu_page"]
        sources = []
        for source in registry:
            if source.get("ccu_page", source.get("page")) != page:
                continue
            sid = source["source_id"]
            body = raw[sid]
            readable = any(str(text).strip() for text in body.get("text_pages", []))
            limited = body.get("access_result") in LIMITS
            state = (
                "access_limited_no_policy_body" if limited else
                "mapped_sections_remaining_body_unclaimed" if mapped[sid] else
                "read_body_not_mapped" if reviews[sid] else
                "readable_body_not_semantically_reviewed" if readable else
                "fetched_binary_not_extracted" if body.get("bundled_file") else
                "body_not_obtained"
            )
            sources.append({
                "source_id": sid, "source_url": source["source_url"],
                "source_pages": list(range(1, len(body.get("text_pages", [])) + 1)),
                "academic_year": source.get("content_academic_year"),
                "applicability": source.get("content_applicability"),
                "checked_at": source.get("checked_at"),
                "sha256": source.get("sha256"), "text_sha256": source.get("text_sha256"),
                "body_state": state, "read_evidence": reviews[sid],
                "mapped_fields": mapped[sid],
                "full_saved_body_read": any(r["extent"] == "complete_saved_text_body" for r in reviews[sid]),
                "all_policy_review_complete": False,
            })
        unannounced = [
            {"field": key, "value": field["value"], "evidence": field["evidence"]}
            for key, field in host["fields"].items() if field["status"] == "explicit_not_announced"
        ]
        schools.append({
            "ccu_page": page, "school_name": host["school_name"],
            "source_state_counts": dict(Counter(s["body_state"] for s in sources)),
            "sources": sources,
            "official_explicit_unannounced_fields": unannounced,
            "unresolved_fields": [{"field": key, "status": field["status"], "reason": field["reason"], "evidence": field["evidence"]} for key, field in host["fields"].items() if field["status"] != "verified_current"],
            "public_sources_exhausted": False,
            "next_action": "先讀可讀但尚無語意查核紀錄的正文；已讀未映射逐欄核對計畫、年度、身分與校區。只把明示未公告的具體項目列為未公告。",
        })
    inputs = ["overseas-source-registry.json", "overseas-reviewed-fields.json", "profile-reviewed-fields.json", "semantic-review-ledger.json", *(p.name for p in review_files)]
    school_pages = {s["ccu_page"] for s in schools}
    shared = [{
        "source_id": source["source_id"], "source_url": source["source_url"],
        "academic_year": source.get("content_academic_year"), "checked_at": source.get("checked_at"),
        "sha256": source.get("sha256"), "text_sha256": source.get("text_sha256"),
        "body_state": "mapped_shared_home_source", "mapped_fields": mapped[source["source_id"]],
        "scope": "母校共同PDF，不將一份共用文件重複計為55校不同來源；逐校適用頁碼在field evidence。",
    } for source in registry if source.get("ccu_page", source.get("page")) not in school_pages]
    report = {
        "checked_date": "2026-10-08", "applicable_round": "2027春季",
        "school_count": len(schools), "source_count": sum(len(s["sources"]) for s in schools) + len(shared),
        "state_counts": dict(Counter(r["body_state"] for r in [*(r for s in schools for r in s["sources"]), *shared])),
        "shared_home_sources": shared,
        "input_sha256": {name: hashlib.sha256((BUNDLE / name).read_bytes()).hexdigest() for name in inputs},
        "definition": "逐來源互斥分類；mapped只證明所列欄位段落，未推整份讀完。read_body_not_mapped須有實際閱讀紀錄。沒有閱讀紀錄不表示已證實他人未讀；表示本交接尚無可核查語意查核。未核實新版不等於官方未公告。",
        "explicit_unannounced_subclaims": read("twentyfourth-source-review.json")["explicit_unannounced_subclaims"],
        "schools": schools,
    }
    assert len(schools) == len({s["ccu_page"] for s in schools}) == 55
    assert report["source_count"] == len(registry)
    (BUNDLE / "body-review-triage.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({key: report[key] for key in ["school_count", "source_count", "state_counts"]}))


if __name__ == "__main__":
    main()
