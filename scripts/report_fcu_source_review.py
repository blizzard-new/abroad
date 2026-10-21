"""Export the bounded 2026-10-21 FCU review, never auto-approve a new source."""
from __future__ import annotations

import argparse
import collections
import csv
from datetime import datetime, timezone
import gzip
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from exchange_info.fcu_source_review import (
    SOURCE_SHA256, SOURCE_URL,
    load_reviewed_programs, matching_programs, review_common_text,
)
from audit_university_data import digest, leaves
from university_review_ledger import append_decisions as append_review_decisions

OUTPUT = ROOT / "docs/data-verification-20261021"
BASELINE = ROOT / "output/data-verification-20261021/baseline/records.jsonl.gz"


def report(*, append_decisions: bool = False) -> dict:
    reviewed_at = datetime.now(timezone.utc).isoformat()
    programs = load_reviewed_programs(ROOT)  # Reject a changed generation.
    raw = ROOT / "src/exchange_info/official_data/fcu/partners.jsonl"
    current = {r["school_name"]: r for r in map(json.loads, raw.read_text("utf8").splitlines())}
    with gzip.open(BASELINE, "rt", encoding="utf8") as stream:
        baseline = [r for line in stream if (r := json.loads(line))["home_id"] == "fcu"]
    receipts = [json.loads(line) for line in (OUTPUT / "manual-source-receipts.jsonl").read_text("utf8").splitlines()]
    source = next(r for r in receipts if r["url"] == SOURCE_URL and r.get("sha256") == SOURCE_SHA256)
    guideline = next(r for r in receipts if r.get("sha256") == "c26217ec7892338c0aec9dffcf96e57e0048907700f8d3ed0e17fe78b4ad9a68")
    rows, decisions = [], []

    def decide(record, pointer, value, status, expected, reason, receipt, locator):
        review_id = digest(["fcu-20261021-program-scopes", record["record_id"], pointer, receipt["sha256"]])[:28]
        decisions.append({
            "review_id": review_id, "base_record_id": record["record_id"],
            "pointer": pointer, "base_value": value, "base_value_sha256": digest(value),
            "base_status": status, "expected_value_or_interpretation": expected,
            "reason": reason, "source_url": receipt["url"],
            "source_sha256": receipt["sha256"], "source_locator": locator,
            "retrieved_at": receipt["completed_at"], "reviewed_at": reviewed_at,
            "method": "codex_official_source_column_reading_and_program_scope_review",
            "whole_record_verified": False,
        })

    for record in baseline:
        data = record["data"]
        # These are the specific common clauses reviewed against the PDF,
        # not an assertion that each containing paragraph is fully correct.
        for pointer, value in leaves(data):
            if not isinstance(value, str):
                continue
            corrected = review_common_text(value)
            if corrected != value:
                decide(record, pointer, value, "contradicted",
                    {"correction_of_reviewed_clauses": corrected, "other_claims": "pending_review"},
                    "僅更正固定排名獎助金額、畢業年級學分條文或未核實的下一梯精確期程；同欄其他主張尚待逐項查核。",
                    guideline, "PDF第6–9頁：獎助審核、返國義務與學分規定；未支持下一梯精確日期")
        if record["kind"] != "partner":
            continue
        school = data["school_name"]
        now = current[school]
        matched = matching_programs(school, programs)
        ids = [p["program_id"] for p in matched]
        locator = "data中program_id=" + ",".join(ids) if ids else "完整data陣列148列；以既存中英文全名及明列別名比對，未找到對應"
        for key in ("quota", "degree_levels", "colleges", "language_requirement", "study_period",
                    "availability_status", "application_window_status", "eligibility", "housing_info", "semester_dates"):
            if key not in data:
                continue
            status = "needs_confirmation"
            reason = "已核對115-1官方表列欄位，保留各方案身分及備註；僅作該梯次參考，不宣告現行接待校規則或整筆資訊正確。"
            if len(matched) == 1 and key == "degree_levels":
                listed = "、".join(x["study_level_name"] for x in matched[0]["study_levels"])
                if data[key] == listed:
                    status = "verified_reference"
                    reason = "原學制值與115-1來源study_levels欄一致；只證明表列學制，年級、院系、國籍與其他限制須另外核對。"
            if len(matched) == 1 and key == "quota" and matched[0]["program_type"] == "學期交換":
                expected = f"學期交換（學費{matched[0]['tuition_type']['name']}・1學期）：{matched[0]['quota']} 名"
                if data[key] == expected:
                    status = "verified_reference"
                    reason = "原名額文字與115-1官方該方案名額一致；僅限該來源梯次，不證明下期開放或個人可申請。"
            if key in {"housing_info", "semester_dates"}:
                reason = "原內容由共用敘述產生；本次來源尚不能證明個別接待校的住宿承諾或正式校曆，明列待補查。"
            elif not matched:
                reason = "本次115-1完整名單未對上既存紀錄，不能沿用既有名額或資格，也不能推論合作終止；保留原始參考並待補查。"
            decide(record, "/" + key, data[key], status, now.get(key), reason, source, locator)
        rows.append({
            "母校": "逢甲大學", "合作校": school, "原始紀錄ID": record["record_id"],
            "本輪狀態": "指定欄位依115-1來源核對；僅參考" if matched else "來源未對上；待補查",
            "官方方案編號": "；".join(ids), "官方方案數": len(ids),
            "名額逐方案": now["quota"], "學制逐方案": now["degree_levels"],
            "語言逐方案": now["language_requirement"],
            "主要缺口": "目前可申請梯次、接待校最終條件、校曆、住宿、生活費及其他未核實內容",
            "整筆核實": "否", "來源網址": SOURCE_URL, "來源SHA256": SOURCE_SHA256,
            "來源取得時間": source["completed_at"],
        })
    assert len(rows) == 161 and len({r["原始紀錄ID"] for r in rows}) == 161
    path = OUTPUT / "fcu-program-review.csv"
    with path.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    added = append_review_decisions(OUTPUT, decisions) if append_decisions else 0
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "partner_records": len(rows), "matched_partner_records": sum(r["官方方案數"] > 0 for r in rows),
        "source_programs_matched": sum(r["官方方案數"] for r in rows),
        "whole_record_verified": 0, "decision_status_counts": dict(collections.Counter(d["base_status"] for d in decisions)),
        "decisions_appended": added,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--append-decisions", action="store_true")
    args = parser.parse_args()
    print(json.dumps(report(append_decisions=args.append_decisions), ensure_ascii=False))
