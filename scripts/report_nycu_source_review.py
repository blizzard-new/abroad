"""Record bounded NYCU source findings without marking any whole record verified."""
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
from exchange_info.nycu_source_review import (
    ACADEMIC, DOCS, FIRST, FORM, LANGUAGE, NOTICE, PERIOD, REGULATIONS,
    SECOND, TABLE_DATA, UST, UST_DOCS, UST_PDF, UST_PERIOD, load_snapshot,
)
from audit_university_data import digest, leaves
from university_review_ledger import append_decisions as append_review_decisions

OUTPUT = ROOT / "docs/data-verification-20261021"


def report(append_decisions=False):
    snapshot = load_snapshot(ROOT)
    receipts = {r["url"]: r for r in snapshot["sources"]}
    reviewed_at = datetime.now(timezone.utc).isoformat()
    partners = {p["school_name"]: p for p in map(json.loads, (
        ROOT / "src/exchange_info/official_data/nycu/partners.jsonl").read_text("utf8").splitlines())}
    decisions, csv_rows = {}, []

    def decide(record, pointer, value, status, expected, url, locator, reason):
        receipt = receipts[url]
        rid = digest(["nycu-round13", record["record_id"], pointer, receipt["sha256"]])[:28]
        decisions[rid] = {
            "review_id": rid, "base_record_id": record["record_id"], "pointer": pointer,
            "base_value": value, "base_value_sha256": digest(value), "base_status": status,
            "expected_value_or_interpretation": expected, "reason": reason,
            "source_url": url, "source_sha256": receipt["sha256"], "source_locator": locator,
            "retrieved_at": receipt["completed_at"], "reviewed_at": reviewed_at,
            "method": "codex_bounded_official_pdf_review_and_table_identity_correspondence",
            "whole_record_verified": False,
        }

    with gzip.open(ROOT / "output/data-verification-20261021/baseline/records.jsonl.gz", "rt", encoding="utf8") as f:
        for line in f:
            r = json.loads(line)
            if r["home_id"] != "nycu":
                continue
            data = r["data"]
            if r["kind"] == "partner":
                p = partners[data["school_name"]]
                matched = snapshot["table_matches"].get(p["school_name"])
                if matched:
                    decide(r, "/school_name", p["school_name"], "verified_reference", matched,
                           TABLE_DATA, f"115-2名額表B欄：{matched}",
                           "只確認母校115-2表列校名對應，非接待校當期開放、顏色標記、名額或整筆驗證。")
                for key in ("availability_status", "quota", "application_deadline", "application_info",
                            "eligibility", "gpa_requirement", "language_requirement", "tuition_info"):
                    decide(r, "/" + key, data.get(key), "needs_confirmation", p[key],
                           UST_PDF if p["availability_status"] == "open" else TABLE_DATA,
                           "台聯大第1–2頁參考名額與個別方案" if p["availability_status"] == "open" else "115-2名額表及接待校條件優先聲明",
                           "歷年校級與116台聯大分開；母校來源不能核實接待校全部現行條件。")
                csv_rows.append({
                    "母校": "國立陽明交通大學", "合作校": p["school_name"], "國家": p["country"],
                    "原始紀錄ID": r["record_id"], "115-2官方表對應": matched or "未對上，需補查",
                    "目前狀態": p["availability_status"], "適用計畫": p["application_round"],
                    "整筆核實": "否", "主要缺口": "逐校當期語言、學制、名額、學費、住宿、校曆、圖片、心得及其他主張",
                    "來源": TABLE_DATA if matched else UST_PDF if p["availability_status"] == "open" else NOTICE,
                })
            for pointer, value in leaves(data):
                if pointer in {"/academic_score_minimum", "/academic_gpa_minimum",
                               "/selection_rules/undergraduate_gpa_minimum", "/selection_rules/undergraduate_rank_maximum"} and value is not None:
                    decide(r, pointer, value, "contradicted", None, REGULATIONS, "第5條綜合書審評分",
                           "綜合書審60分不能代換成平均70、GPA2.7或排名50%的通過門檻。")
                if pointer == "/maximum_preferences" and value == 5:
                    decide(r, pointer, value, "needs_confirmation", None, SECOND, "第1–2頁申請文件及程序",
                           "本輪校級文件未證實5志願；台聯大每類2志願不能套所有校級計畫。")
                if not isinstance(value, str):
                    continue
                if any(s in value for s in ("2027-01-05T17", "2026-12-01T09", "2027-06-01T09", "2027-07-10T17")):
                    decide(r, pointer, value, "contradicted", PERIOD,
                           SECOND if "07-10" in value or "06-01" in value else FIRST, "第1頁學年度與申請日期",
                           "來源簡章是115學年度，不能順延一年產生116精確期限。")
                elif "2026-10-06T09" in value:
                    decide(r, pointer, value, "needs_confirmation", None, UST, "116台聯大公告申請期限",
                           "公告提供12/31 16:00截止，未核實10/06 09:00開放。")
                elif "五級核章" in value or "五級簽核" in value:
                    decide(r, pointer, value, "contradicted", DOCS[2], FORM, "唯一頁三處簽名欄",
                           "校級115-2簽核表只有本人、導師／指導教授、系主任／所長。")
                elif "每年" in value and ("1月5日" in value or "7月10日" in value or "12/01" in value):
                    decide(r, pointer, value, "needs_confirmation", PERIOD, REGULATIONS, "第4條日期依各梯公告",
                           "已讀單一期簡章的時間不能變成每年固定期限與時刻。")
                elif r["kind"] in {"workflow", "deadline_card"} and (
                    "英文歷年成績單" in value or "中英文自傳" in value
                ) and "UST" not in value and "台聯大" not in value and "臺灣聯" not in value:
                    decide(r, pointer, value, "contradicted", DOCS[0], SECOND, "第2頁第3條應備資料",
                           "校級中文文件與台聯大英文資料混用；中文非母語者英文例外另依公告。")
                elif "116" in value and "UST" in value and any(s in value for s in ("馬里蘭", "UNSW", "ETH Zurich", "UC San Diego")):
                    decide(r, pointer, value, "contradicted",
                           "116台聯大PDF列伯恩、香港中文、香港城市、南洋理工及UC Santa Cruz；其他學校本輪未列。",
                           UST_PDF, "第1頁方案表", "不能將其他年度UST合作校併入本期開放清單。")
                elif pointer.endswith("/deadline_note") and "12/31" in value and "國際處" in value:
                    decide(r, pointer, value, "needs_confirmation", UST_DOCS[0], UST, "申請方式／電子郵件完整PDF",
                           "承辦窗口不等於紙本送件，須保留明確電子郵件送件方式。")
            if r["kind"] == "destination":
                decide(r, "/cost_summary", data["cost_summary"], "needs_confirmation",
                       "每校費用另查；原國家預設金額撤出已核實生活費。",
                       TABLE_DATA, "逐校資料來源及名額表範圍",
                       "原產製程式的國家預設估價不是該校官方生活費證據。")

    with (OUTPUT / "nycu-program-review.csv").open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(csv_rows[0]))
        writer.writeheader()
        writer.writerows(csv_rows)
    gaps = {
        "school_id": "nycu", "whole_records_verified": 0,
        "missing_partner_record": {
            "name": "University of California, Santa Cruz", "scope": "116台聯大暑期研究",
            "source_url": UST_PDF, "source_sha256": receipts[UST_PDF]["sha256"],
            "note": "官方第1頁列出，既有243筆沒有獨立學校紀錄；不可因本輪核對而臆造地址、照片、費用等欄位。"},
        "source_conflicts_and_limits": [
            "舊名額連結gid114872685仍是2024更新內容；115-2公告指定gid1079257447。",
            "GViz不保留綠底／紫字，不能推斷待定合作或拓荒者標記。",
            "巴黎薩克雷與CentraleSupelec、雷恩與ENSSAT不能僅憑母體名稱合併；後者未自動匹配。",
            "校級通則保證金免繳列低收／中低收，115-2簡章另列特殊境遇家庭，依當期範圍。",
            "期中／期末報告同列相對期間及固定日曆日期，不同接待校校曆需承辦確認。",
            "長安大學兩個既有圖片紀錄證據不同，覆蓋API維持不採用歧義圖片；本輪未完成照片核實。",
            "182筆只有官方歷史表校名對應；個別欄位及接待校來源未宣告完整驗證。",
        ],
    }
    (OUTPUT / "round13-source-conflicts.json").write_text(
        json.dumps(gaps, ensure_ascii=False, indent=2) + "\n", encoding="utf8")
    added = append_review_decisions(OUTPUT, decisions.values()) if append_decisions else 0
    return {"partner_rows": len(csv_rows), "table_name_matches": len(snapshot["table_matches"]),
            "decisions": len(decisions), "added": added,
            "statuses": dict(Counter(d["base_status"] for d in decisions.values()))}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--append-decisions", action="store_true")
    print(json.dumps(report(parser.parse_args().append_decisions), ensure_ascii=False))
