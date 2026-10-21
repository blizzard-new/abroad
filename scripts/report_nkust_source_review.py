"""Record bounded NKUST findings against the immutable baseline."""
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
from exchange_info.nkust_source_review import (
    ACADEMIC, AWARD, AWARDS, DOCS, GUIDELINES, INFO, LANGUAGE,
    OBLIGATIONS, PAGE, PERIOD, REGULATIONS, load_snapshot,
)
from audit_university_data import digest, leaves
from university_review_ledger import append_decisions as append_review_decisions

OUTPUT = ROOT / "docs/data-verification-20261021"


def report(append_decisions=False):
    s = load_snapshot(ROOT); checked = datetime.now(timezone.utc).isoformat()
    receipts = {r["url"]: r for r in s["sources"] if r["transport_result"] == "retrieved"}
    partners = {p["school_name"]: p for p in map(json.loads,
        (ROOT / "src/exchange_info/official_data/nkust/partners.jsonl").read_text("utf8").splitlines())}
    decisions, csv_rows = {}, []

    def decide(r, pointer, value, status, expected, url, locator, reason):
        receipt = receipts[url]
        rid = digest(["nkust-round16", r["record_id"], pointer, receipt["sha256"]])[:28]
        decisions[rid] = {"review_id": rid, "base_record_id": r["record_id"], "pointer": pointer,
            "base_value": value, "base_value_sha256": digest(value), "base_status": status,
            "expected_value_or_interpretation": expected, "reason": reason,
            "source_url": url, "source_sha256": receipt["sha256"], "source_locator": locator,
            "retrieved_at": receipt["completed_at"], "reviewed_at": checked,
            "method": "codex_bounded_official_pdf_review_and_dated_table_correspondence",
            "whole_record_verified": False}

    with gzip.open(ROOT / "output/data-verification-20261021/baseline/records.jsonl.gz", "rt", encoding="utf8") as f:
        for line in f:
            r = json.loads(line)
            if r["home_id"] != "nkust": continue
            data = r["data"]
            if r["kind"] == "partner":
                p = partners[data["school_name"]]; matches = s["table_matches"].get(p["school_name"], [])
                for url in sorted({m["source_url"] for m in matches}):
                    scoped = [m for m in matches if m["source_url"] == url]
                    decide(r, "/school_name", p["school_name"], "verified_reference", scoped, url,
                        "; ".join(f"gid={m['gid']} row={m['row']}" for m in scoped),
                        "確認115校級／2023院系表校名與原欄位；不驗證116當期名額或整筆。")
                for key in ("quota", "availability_status", "application_deadline", "application_info", "eligibility",
                            "gpa_requirement", "language_requirement", "tuition_info"):
                    decide(r, "/" + key, data.get(key), "needs_confirmation", p[key], GUIDELINES,
                        "115校級簡章及各管道適用範圍", "母校共同條文部分修正；逐校當期接待校證據仍待查。")
                csv_rows.append({"母校": "國立高雄科技大學", "合作方案": p["school_name"], "國家": p["country"],
                    "原始紀錄ID": r["record_id"], "管道": p["program_type"],
                    "來源對應": "；".join(f"{m['scope']}第{m['row']}列" for m in matches) or "本輪兩表未對上",
                    "參考名額": p["quota"], "目前狀態": p["availability_status"], "整筆核實": "否",
                    "主要缺口": "116當期接待校條件、名額、語檢、學制、課程、費用、校曆、住宿、圖片、心得"})
            if r["kind"] == "destination":
                decide(r, "/cost_summary", data["cost_summary"], "needs_confirmation",
                    "個別接待校生活費待核實；原國家預設估價不當官方金額。", GUIDELINES,
                    "第6頁個人生活安排", "共同規則不是逐校費用依據。")
            for pointer, value in leaves(data):
                if pointer in {"/academic_score_minimum", "/academic_gpa_minimum", "/selection_rules/undergraduate_gpa_minimum",
                    "/selection_rules/undergraduate_rank_maximum"} and value is not None:
                    decide(r, pointer, value, "contradicted", None, GUIDELINES, "第4頁甄選配分表",
                        "75是操行，不是學業通過門檻；通則未有共同GPA或排名替代。")
                if pointer.startswith("/language_score_minimums/") and value is not None:
                    decide(r, pointer, value, "contradicted", None, GUIDELINES, "第1–2頁語言資格",
                        "依接待校標準，不能把CEFR換算級距當共用資格。")
                if not isinstance(value, str): continue
                if any(x in value for x in ("2026-11-10", "2026-12-10", "2026-12-02", "2026/12/10", "2026/11/10")):
                    decide(r, pointer, value, "needs_confirmation", PERIOD, INFO, "116說明會公告不含交換申請期限",
                        "115申請在114年；不得順延一年當成116的已公告日期。")
                elif "學業" in value and "75" in value and any(x in value for x in ("GPA", "前 30", "前30")):
                    decide(r, pointer, value, "contradicted", ACADEMIC, GUIDELINES, "第4頁甄選配分表",
                        "操行與學業、各接待校GPA與獎助資格混用。")
                elif any(x in value for x in ("中英文自傳", "中英文讀書", "中、英文自傳")):
                    decide(r, pointer, value, "contradicted", DOCS[2], GUIDELINES, "第3頁應備文件第5項",
                        "一般交換免附計畫；約1000–1500字僅學海惜珠。")
                elif "中英文歷年成績單" in value:
                    decide(r, pointer, value, "contradicted", DOCS[1], GUIDELINES, "第2頁應備文件第2項",
                        "初審必繳中文歷年成績含名次百分比，不是所有申請人都須中英文。")
                elif any(x in value for x in ("院長核章", "家長簽章", "裝訂成冊")) and r["kind"] in {"workflow", "dashboard", "exchange_info"}:
                    decide(r, pointer, value, "contradicted", DOCS[0] + DOCS[4], GUIDELINES,
                        "第2頁簽章流程／第5頁錄取確認", "初審簽章後掃描線上上傳；家長同意在錄取確認階段。")
                elif "1,500" in value and "2,000" in value and ("心得" in value or "返國" in value):
                    decide(r, pointer, value, "needs_confirmation", OBLIGATIONS[3] + AWARDS[3], AWARD,
                        "第5點獎助請領文件", "校獎助可交心得或3–5分鐘短片，本輪未核實統一1500–2000字。")

    with (OUTPUT / "nkust-program-review.csv").open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(csv_rows[0])); writer.writeheader(); writer.writerows(csv_rows)
    gaps = {"school_id": "nkust", "whole_records_verified": 0, "matched_existing_records": len(s["table_matches"]),
        "unmatched_existing_records": [p["school_name"] for p in partners.values() if p["school_name"] not in s["table_matches"]],
        "source_conflicts_and_limits": s["source_conflicts"],
        "source_fields_not_currently_verified": "母校表格欄位只作帶日期的來源參考；須逐校核對116當期學制、名額、費用、語檢與其他條件。"}
    (OUTPUT / "round16-source-conflicts.json").write_text(json.dumps(gaps, ensure_ascii=False, indent=2) + "\n", "utf8")
    added = append_review_decisions(OUTPUT, decisions.values()) if append_decisions else 0
    return {"partner_rows": len(csv_rows), "decisions": len(decisions), "added": added,
        "statuses": dict(Counter(d["base_status"] for d in decisions.values()))}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__); parser.add_argument("--append-decisions", action="store_true")
    print(json.dumps(report(parser.parse_args().append_decisions), ensure_ascii=False))
