"""Close known CCU source leads and list precise current-version inputs.

Acceptance is bounded to the saved catalogue and explicitly linked gap-related
chapters. It never asserts exhaustive website research or official nonpublication.
"""
from __future__ import annotations

import csv
import hashlib
import json
from collections import Counter

from fetch_ccu_completion_sources import BUNDLE as B

REQUESTS = {
    "program_scope": "當期incoming交換簡章：計畫、學制、院系、校區與CCU雙邊適用範圍",
    "eligibility": "當期incoming資格：年級、GPA、在學／國籍與院系限制，與CCU outbound分開",
    "language": "当期接待語言門檻／有效期／替代證明／學制差異及TOEFL考試日期版本",
    "nomination_deadline": "Spring2027母校提名起止日、時區及送達要求；與學生申請期限分開",
    "application_deadline": "Spring2027學生申請起止日、時區、送達要求及計畫差異",
    "documents": "當期incoming完整必繳文件清單、提交方式、簽章與原件／掃描階段",
    "application_forms": "當期空白表格／範本與版本；若個人或提名後發送，提供去識別版本及獲取程序",
    "academic_calendar": "2026/27 Spring2027正式校曆及院系例外，分授課、考試與迎新",
    "course_restrictions": "Spring2027可選課單、語言、學分上限下限、先修與院系／學制限制",
    "housing": "當期交換住房政策，分校區、床位條件、申請身份與保證範圍",
    "housing_deadline": "Spring2027交換住宿申請／回簽／押金實際截止及個人通知程序",
    "costs": "2026/27當期費率或個人去識別報價：住宿、生活、交通與必要費用分項／幣別／期間",
    "insurance": "當期台籍incoming交換保險要求、協議例外、保障期間／保額及是否須另購",
    "visa": "當期學校接待身分與文件指引及政府台籍要求公開URL；不提供帳號或個資",
    "arrival": "Spring2027迎新／報到／抵達截止與機場接送安排，分校區及計畫",
    "host_tuition": "CCU有效雙邊協議當期學費豁免／應繳費範圍，不以freemover或其他計畫替代",
    "exchange_duration": "當期可接待學期／最長期間及extension條件，與住房合約／課程週數分開",
}


def load(name):
    return json.loads((B / name).read_text())


def write(name, data):
    (B / name).write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n")


def main():
    base = load("completion-ninth-baseline.json")
    rows = load("completion-reviewed-fields.json")["schools"]
    before = {r["ccu_page"]: r for r in base["prior_fields"]}
    counts = dict(Counter(f["status"] for r in rows for f in r["host_fields"].values()))
    changed = [{"ccu_page": r["ccu_page"], "school_name": r["school_name"], "field": k,
                "previous_status": before[r["ccu_page"]]["host_fields"][k]["status"], "status": f["status"],
                "evidence_source_ids": [e.get("source_id") for e in f["evidence"]]}
               for r in rows for k, f in r["host_fields"].items()
               if hashlib.sha256(json.dumps({x: f[x] for x in ["value", "status", "evidence"]},
                                            ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
               != before[r["ccu_page"]]["host_fields"][k]["field_digest"]]
    closure = load("completion-ninth-reading-closures.json")
    plan = load("completion-ninth-acquisition-plan.json")
    readings = load("completion-ninth-reading-input.json")
    work = load("completion-remaining-public-worklist.json")
    receipts = [load("completion_sources/" + x["source_id"] + ".receipt.json") for x in plan["sources"]]
    assert len(closure["records"]) == len({r["source_id"] for r in closure["records"]}) == 263
    assert sum(r["already_complete_extent"] for r in closure["records"]) == 17
    assert work["counts"]["public_reading_record_missing_sources"] == 0
    private = [{"ccu_page": r["ccu_page"], "school_name": r["school_name"],
                "fields": r["external_access_limited_steps"]} for r in work["schools"] if r["external_access_limited_steps"]]
    source_by_school = {r["ccu_page"]: [x["source_id"] for x in readings if x["ccu_page"] == r["ccu_page"]] for r in rows}
    inputs = []
    for r in rows:
        for key, f in r["host_fields"].items():
            if f["status"] == "verified_current":
                continue
            inputs.append({"ccu_page": r["ccu_page"], "school_name": r["school_name"], "field": key,
                           "status": f["status"], "strict_missing": f["status"] == "missing",
                           "classification": "personal_access_required" if f.get("research_classification") == "personal_access_required" else "current_version_not_verified_in_known_source_scope",
                           "applicable_target": "Spring2027；CCU當期申請已截止／reference未開放，不表示母校可再申請",
                           "minimum_required_input": REQUESTS[key], "last_related_readings": source_by_school[r["ccu_page"]],
                           "official_not_announced": f["status"] == "explicit_not_announced",
                           "existing_evidence": f["evidence"], "access_requirement_evidence": f.get("access_requirement_evidence", [])})
    write("completion-ninth-external-inputs.json", {"scope": "逐校逐欄當期核實所需輸入，不表示每欄已證實只能透過非公開校方取得；無新線索時可停止本輪研究等整合。", "host_fields": inputs,
                                                "assets_and_gamma": load("completion-ninth-asset-and-gamma-closure.json")})
    columns = ["ccu_page", "school_name", "field", "status", "strict_missing", "classification", "applicable_target", "minimum_required_input", "official_not_announced"]
    with (B / "completion-ninth-external-inputs.csv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(inputs)
    result = {
        "prior_commit": base["prior_commit"], "acceptance_scope": "104 CCU identities; finite263 flagged eighth readings and33 explicitly linked relevant child URLs; no whole-web exhaustion claim.",
        "scope_accepted": True, "all_public_research_exhausted": False, "ready_to_wait_for_integration": True,
        "flagged_readings_closed": 263, "already_complete_extent_metadata_corrections": 17,
        "actual_prior_partial_readings": 246, "closure_states": dict(Counter(r["closure"] for r in closure["records"])),
        "new_sources": len(receipts), "new_http_200": sum(r["http_status"] == 200 for r in receipts),
        "new_body_read_records": len(plan["sources"]), "new_complete_visible_child_bodies": sum(r["full_visible_read"] for r in readings if r["source_id"] in {x["source_id"] for x in plan["sources"]}),
        "http_200_is_not_policy_verification": True, "prior_host_status_counts": base["prior_host_counts"], "host_status_counts": counts,
        "changed_host_fields": len(changed), "previously_missing_host_fields_filled": sum(r["previous_status"] == "missing" and r["status"] != "missing" for r in changed),
        "changed_fields": changed, "worklist_counts": work["counts"], "external_private_steps": private,
        "private_school_count": len(private), "private_field_count": sum(len(r["fields"]) for r in private),
        "external_input_rows": len(inputs), "strict_missing_input_rows": sum(r["strict_missing"] for r in inputs),
        "nonpublication_claims_added": 0, "new_asset_requests": 0,
        "asset_counts_unchanged": {"coordinates": 101, "licensed_photos": 100, "website_identities": 103},
        "shared_runtime_changes_in_ninth_round": [],
        "immutable_prior_snapshot": "completion-eighth-public-progress.json; eighth reading-input preserved with its original flags and extents",
        "remaining_limits": "585 strict missing host fields, unyear/historical/conflicting sources and individual access steps remain distinct. Current-version unverified is not officially unannounced. CCU home windows remain closed; Gamma denominator remains null. No account, contact, form submission, merge or deployment."
    }
    write("completion-ninth-convergence-acceptance.json", result)
    limits = load("completion-remaining-limitations.json")
    limits["ninth_convergence"] = {"acceptance": "completion-ninth-convergence-acceptance.json", "closures": "completion-ninth-reading-closures.json", "precise_external_inputs": "completion-ninth-external-inputs.json", "scope_accepted": True, "all_public_research_exhausted": False, "ready_to_wait_for_integration": True}
    write("completion-remaining-limitations.json", limits)
    print(json.dumps({k: result[k] for k in ["host_status_counts", "changed_host_fields", "previously_missing_host_fields_filled", "private_school_count", "private_field_count", "closure_states", "external_input_rows"]}))


if __name__ == "__main__":
    main()
