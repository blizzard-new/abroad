"""Bind PCCU route findings to baseline fields, without asserting whole-record verification."""
from __future__ import annotations

import argparse
from collections import Counter
import csv
from datetime import datetime, timezone
import gzip
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from exchange_info.pccu_source_review import (
    ACADEMIC, AWARD, AWARDS, CONFLICT, DOCS, GUIDE, JP, KR, LANGUAGE,
    MAINLAND, OBLIGATIONS, PERIOD, QUOTAS, RULE, load_snapshot,
)
from audit_university_data import digest, leaves
from university_review_ledger import append_decisions as append_review_decisions

OUTPUT = ROOT / "docs/data-verification-20261021"


def report(append_decisions=False):
    s = load_snapshot(ROOT)
    receipts = {r["url"]: r for r in s["sources"] if r["transport_result"] == "retrieved"}
    checked = datetime.now(timezone.utc).isoformat()
    folder = ROOT / "src/exchange_info/official_data/pccu"
    partners = {p["school_name"]: p for p in map(json.loads, (folder / "partners.jsonl").read_text("utf8").splitlines())}
    quotas = {r["school_name"]: r for r in s["oima_quota_reference"]}
    jp = {r["school_name"]: r for r in s["japanese_name_matches"]}
    kr = {r["school_name"]: r for r in s["korean_name_matches"] if r["school_name"]}
    mainland = {r["matched_school_name"]: r for r in s["mainland_rows"]
        if r["stage"] == "mainland-second" and r["matched_school_name"]}
    decisions, csv_rows = {}, []

    def decide(r, pointer, value, status, expected, url, locator, reason):
        receipt = receipts[url]
        rid = digest(["pccu-round15", r["record_id"], pointer, receipt["sha256"]])[:28]
        decisions[rid] = {"review_id": rid, "base_record_id": r["record_id"], "pointer": pointer,
            "base_value": value, "base_value_sha256": digest(value), "base_status": status,
            "expected_value_or_interpretation": expected, "reason": reason,
            "source_url": url, "source_sha256": receipt["sha256"], "source_locator": locator,
            "retrieved_at": receipt["completed_at"], "reviewed_at": checked,
            "method": "codex_bounded_official_route_review_and_table_correspondence",
            "whole_record_verified": False}

    with gzip.open(ROOT / "output/data-verification-20261021/baseline/records.jsonl.gz", "rt", encoding="utf8") as f:
        for line in f:
            r = json.loads(line)
            if r["home_id"] != "pccu": continue
            data = r["data"]
            if r["kind"] == "partner":
                p = partners[data["school_name"]]; name = p["school_name"]
                matches = []
                for table, url, locator in [
                    (quotas, QUOTAS, "2026/04/29表第1–6頁；已逐頁視覺核對名額欄"),
                    (jp, s["source_urls"]["jp-table.pdf"], "115學年度表校名代碼；僅核對校名"),
                    (kr, s["source_urls"]["kr-notice.pdf"], "第1頁27校名單；視覺核對"),
                    (mainland, MAINLAND, "第二階段可抵學分表列名"),
                ]:
                    if name in table:
                        matches.append(table[name])
                        decide(r, "/school_name", name, "verified_reference", table[name], url, locator,
                            "僅驗證母校來源校名對應；不等於所有資料或接待校現行條件核實。")
                for key in ("availability_status", "quota", "application_deadline", "application_info",
                            "eligibility", "gpa_requirement", "language_requirement", "tuition_info"):
                    url = MAINLAND if name in mainland else QUOTAS if name in quotas and key == "quota" else RULE
                    decide(r, "/" + key, data.get(key), "needs_confirmation", p[key], url,
                        "依所選管道、名單日期與學期核對", "部分共同條文已修正；逐校當期條件及來源衝突仍待確認。")
                csv_rows.append({"母校": "中國文化大學", "合作校": name, "國家": p["country"],
                    "原始紀錄ID": r["record_id"], "原有申請管道": p["program_type"],
                    "國合組參考名額": quotas.get(name, {}).get("quota_reference", "未對上"),
                    "日文115表校名": "已對上" if name in jp else "未對上",
                    "韓文115-2表校名": "已對上" if name in kr else "未對上",
                    "赴陸第二階段": "列名；學期附件衝突待確認" if name in mainland else "未對上",
                    "目前狀態": p["availability_status"], "整筆核實": "否",
                    "主要缺口": "接待校當期名額、學制、語檢、費用、住宿、校曆、圖片、心得及其他主張"})
            if r["kind"] == "destination":
                decide(r, "/cost_summary", data["cost_summary"], "needs_confirmation",
                    "逐校官方生活費尚待核實，移除國家預設估價。", RULE, "校級要點不載各校生活費",
                    "母校一般規定不能作逐校生活費證據。")
            for pointer, value in leaves(data):
                if pointer in {"/academic_score_minimum", "/academic_gpa_minimum",
                    "/selection_rules/undergraduate_gpa_minimum"} and value is not None:
                    decide(r, pointer, value, "contradicted", None, RULE, "一頁校級甄選要點",
                        "通則沒有全校共同學業分數或GPA門檻，獎學金門檻不能替代。")
                if pointer.startswith("/language_score_minimums/") and value is not None:
                    decide(r, pointer, value, "contradicted", None, QUOTAS, "第1–6頁逐校語言欄",
                        "各接待校及學程要求不同，不能抽出最低分作全校共通自動通過。")
                if pointer == "/maximum_preferences" and value == 5:
                    decide(r, pointer, value, "contradicted", None, s["source_urls"]["kr-notice.pdf"],
                        "第2頁志願欄不限數", "五志願不能作全校統一限制。")
                if not isinstance(value, str): continue
                if any(t in value for t in ("2026-10-30T16:30", "2026/10/30", "2026-11-27", "2026/11/27", "2026/11/16")):
                    decide(r, pointer, value, "needs_confirmation", PERIOD, JP, "115公告及簡章第一階段年份",
                        "日文系來源是2025報名；未讀到支持116推估日期的當期公告。")
                elif any(t in value for t in ("各約 1,000 字", "各 1,000 字", "每份各約 1,000 字", "各約1,000字")):
                    decide(r, pointer, value, "contradicted", DOCS["mainland"][0], s["source_urls"]["mainland-second.pdf"],
                        "第1–2頁申請文件", "赴陸計畫300字內；不同管道不能共用各1000字。")
                elif "6 學分或 2 門" in value or "6學分或2門" in value:
                    decide(r, pointer, value, "contradicted", OBLIGATIONS[1], s["source_urls"]["jp-rule.pdf"],
                        "日文系115甄選簡章修課規定", "一年12學分不能換成每學期至少6或2門；韓文系上限也不是最低量。")
                elif any(t in value for t in ("每次核給 NT$20,000", "最高核給 NT$50,000", "最高補助 NT$50,000")):
                    decide(r, pointer, value, "contradicted", AWARDS, AWARD, "2026/10/20新公告金額與附件",
                        "新版公告最低額不同於舊版最高額，附件通過日期占位符仍待確認。")
                elif r["kind"] in {"workflow", "dashboard", "exchange_info"} and "返國後 1 個月" in value:
                    decide(r, pointer, value, "needs_confirmation", OBLIGATIONS[3], AWARD,
                        "國際移動力獎學金返國義務", "獎學金報告要求不可自動套用全部管道。")
                elif r["kind"] in {"workflow", "dashboard", "exchange_info"} and "TOEFL" in value and "575" in value:
                    decide(r, pointer, value, "needs_confirmation", LANGUAGE, QUOTAS,
                        "逐校語言欄", "某校最低門檻不是全校共同門檻。")

    with (OUTPUT / "pccu-program-review.csv").open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(csv_rows[0])); writer.writeheader(); writer.writerows(csv_rows)
    gaps = {"school_id": "pccu", "whole_records_verified": 0,
        "oima_reference_rows": 47, "japanese_name_matches": len(jp), "korean_name_matches": len(kr),
        "mainland_second_matches": len(mainland),
        "missing_mainland_second_rows": [r for r in s["mainland_rows"] if r["stage"] == "mainland-second" and not r["matched_school_name"]],
        "missing_korean_rows": [r for r in s["korean_name_matches"] if not r["school_name"]],
        "source_conflicts_and_limits": [CONFLICT,
            "日文系115簡章學業門檻114-1、配分段11301不同；留存衝突。",
            "日文系115表28校僅確認校名；既有關西、東京都立、芝浦工業未對上本表。",
            "韓文系115-2日程表標題與秋季截止日欄名不一致，東亞大學連結誤指建國；不直接轉作接待校當期期限。",
            "國際移動力新版附件115.00.00、第0000次通過日期為占位符，須確認正式版本。",
            "國合組與系所雙軌名額不相加；公費、訪問自費、雙聯不能一律視為免學費。",
            "國合組表Siena與Ferrara的語言建議為跨列合併格；空白不是免語檢。",
            "赴陸表分可抵與不可抵；已列名不保證接待校錄取、抵免或獎助。",
            "法俄組現行逐校規則及所有接待校生活資料尚待查證。"],
        "runtime_availability_counts": dict(Counter(p["availability_status"] for p in partners.values()))}
    (OUTPUT / "round15-source-conflicts.json").write_text(json.dumps(gaps, ensure_ascii=False, indent=2) + "\n", "utf8")
    added = append_review_decisions(OUTPUT, decisions.values()) if append_decisions else 0
    return {"partner_rows": len(csv_rows), "decisions": len(decisions), "added": added,
        "statuses": dict(Counter(d["base_status"] for d in decisions.values()))}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__); parser.add_argument("--append-decisions", action="store_true")
    print(json.dumps(report(parser.parse_args().append_decisions), ensure_ascii=False))
