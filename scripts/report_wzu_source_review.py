"""Bind bounded WZU findings to immutable baseline records; never verify whole records."""
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
from exchange_info.wzu_source_review import (
    ACADEMIC, ALLOCATION, DOCS, GENERAL_PDF, LANGUAGE, LANGUAGE_PDF,
    OBLIGATIONS, PERIOD, SECOND, load_snapshot,
)
from audit_university_data import digest, leaves
from university_review_ledger import append_decisions as append_review_decisions

OUTPUT = ROOT / "docs/data-verification-20261021"


def report(append_decisions=False):
    snapshot = load_snapshot(ROOT)
    receipts = {r["url"]: r for r in snapshot["sources"]}
    checked = datetime.now(timezone.utc).isoformat()
    folder = ROOT / "src/exchange_info/official_data/wzu"
    partners = {p["school_name"]: p for p in map(json.loads, (folder / "partners.jsonl").read_text("utf8").splitlines())}
    decisions, csv_rows = {}, []

    def decide(r, pointer, value, status, expected, url, locator, reason):
        receipt = receipts[url]
        rid = digest(["wzu-round14", r["record_id"], pointer, receipt["sha256"]])[:28]
        decisions[rid] = {"review_id": rid, "base_record_id": r["record_id"], "pointer": pointer,
            "base_value": value, "base_value_sha256": digest(value), "base_status": status,
            "expected_value_or_interpretation": expected, "reason": reason,
            "source_url": url, "source_sha256": receipt["sha256"], "source_locator": locator,
            "retrieved_at": receipt["completed_at"], "reviewed_at": checked,
            "method": "codex_bounded_official_pdf_review_and_table_name_correspondence",
            "whole_record_verified": False}

    with gzip.open(ROOT / "output/data-verification-20261021/baseline/records.jsonl.gz", "rt", encoding="utf8") as f:
        for line in f:
            r = json.loads(line)
            if r["home_id"] != "wzu":
                continue
            data = r["data"]
            if r["kind"] == "partner":
                p = partners[data["school_name"]]
                matches = snapshot["table_matches"].get(p["school_name"], [])
                if matches:
                    first = matches[0]
                    url = "https://d020.wzu.edu.tw/datas/upload/Pictures/" + first["file"]
                    decide(r, "/school_name", p["school_name"], "verified_reference", matches, url,
                        f"{first['sheet']}!{first['name_cell']}",
                        "僅確認母校115-2歷史表校名對應；不驗證名額、學費、語檢、是否開放或整筆。")
                for key in ("availability_status", "quota", "application_deadline", "application_info",
                            "eligibility", "gpa_requirement", "language_requirement", "tuition_info"):
                    decide(r, "/" + key, data.get(key), "needs_confirmation", p[key], GENERAL_PDF,
                        "第1–6頁共同規則及逐校條件優先聲明", "共用條文部分修正；各語組與接待校個別條件尚待逐項核實。")
                csv_rows.append({"母校": "文藻外語大學", "合作校": p["school_name"], "國家": p["country"],
                    "原始紀錄ID": r["record_id"], "115-2表校名對應": "；".join(
                        f"{m['file']}：{m['sheet']}!{m['name_cell']}" for m in matches) or "未對上，需補查",
                    "目前狀態": p["availability_status"], "整筆核實": "否",
                    "主要缺口": "逐校當期名額、語檢、學制、費用、住宿、校曆、圖片、心得及其他主張",
                    "來源": SECOND})
            if r["kind"] == "destination":
                decide(r, "/cost_summary", data["cost_summary"], "needs_confirmation",
                    "逐校官方生活費待核實；移除未經核實之國家預設估價。", GENERAL_PDF,
                    "第5頁接待校與個人生活安排", "母校簡章不是逐校生活費證據。")
            for pointer, value in leaves(data):
                if pointer == "/maximum_preferences" and value == 5:
                    decide(r, pointer, value, "needs_confirmation", None, GENERAL_PDF, "第2頁語組規定",
                        "一招最多兩語組、二招一語組，不等於志願學校數。")
                if not isinstance(value, str):
                    continue
                if "2026-10-13T15" in value or "10/13 15:00" in value or "08/31 15:00" in value:
                    decide(r, pointer, value, "contradicted", PERIOD, GENERAL_PDF, "第2頁申請程序",
                        "二招延期23:59線上截止，不能作15:00紙本截止。")
                elif "2027-03-02" in value or "2027-02-15" in value or "2027/02/22" in value:
                    decide(r, pointer, value, "needs_confirmation", PERIOD, SECOND, "115-2延期公告的適用學期",
                        "已讀來源不支持116-1推估日期；移除確定日期及提醒。")
                elif any(t in value for t in ("各 500–1,000", "各500–1,000", "各 1,000 字", "各約 1,000 字")):
                    decide(r, pointer, value, "contradicted", DOCS[1], GENERAL_PDF, "第2–3頁履歷表",
                        "五頁限制涵蓋自傳、計畫等全部履歷內容，不是單篇字數。")
                elif any(t in value for t in ("返國後 1 個月", "返國後1個月", "返國後一個月")):
                    decide(r, pointer, value, "contradicted", OBLIGATIONS[4], GENERAL_PDF, "第6頁返國義務",
                        "本期要求返國後兩週內線上交報告及相關資料。")
                elif "2026-10-30" in value and r["kind"] == "deadline_card":
                    decide(r, pointer, value, "contradicted", ALLOCATION, GENERAL_PDF, "第3頁暫訂分發作業期間",
                        "暫訂分發日期不是校內報名截止，不生成報名提醒。")
                elif r["kind"] in {"workflow", "dashboard", "exchange_info"} and "中英文歷年成績單" in value:
                    decide(r, pointer, value, "contradicted", DOCS[0], GENERAL_PDF, "第2頁線上應備文件",
                        "初審需用印中文歷年成績單含排名；英文成績單不得無依據列作全員必繳。")

    with (OUTPUT / "wzu-program-review.csv").open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(csv_rows[0])); writer.writeheader(); writer.writerows(csv_rows)
    gaps = {"school_id": "wzu", "whole_records_verified": 0,
        "name_match_count": len(snapshot["table_matches"]), "unmatched_official_rows": snapshot["unmatched_table_names"],
        "source_conflicts_and_limits": [
            "529152目前顯示文章已超過時間；529354是一招一般組，不能當二招來源。",
            "一招一般組公告Google表單PKM2i5VSfciz9QsN6與PDF的CNEtGEdvk4V35Jfi8不同，保留衝突。",
            "二招公告泛稱撕榜，但簡章明列不辦現場撕榜／不重選志願，依報名順序分發；第4頁仍有現場檢核字樣，實際檢核安排須依通知。",
            "二招日間10／進修18學分條文未列研究所例外，一招列研究所除外，研究生適用需確認。",
            "一招及二招語組數不同；不能把語組數當校級志願學校上限。",
            "語言組表包含聖地牙哥-德孔波斯特拉大學但未對上既有同組紀錄；加州爾灣在官方一般組表，既有分類與名額需逐案核對。",
            "二招日語表包含暫停交流的佐賀及若干未對上學校；列入名單不等於有開放名額。",
            "美因茲母體與翻譯學院、里爾各學院、越南校名別稱需保留不同方案，不自動合併。",
            "官方表逐格名額、費用、語檢、樣式標記及接待校現行資料仍待核對，128筆只驗證校名對應。",
            "SOSA加分表的1–10與10–19小時邊界重疊，未據此自動計分；官方CV範本尚未取得。",
        ]}
    (OUTPUT / "round14-source-conflicts.json").write_text(json.dumps(gaps, ensure_ascii=False, indent=2) + "\n", "utf8")
    added = append_review_decisions(OUTPUT, decisions.values()) if append_decisions else 0
    return {"partner_rows": len(csv_rows), "decisions": len(decisions), "added": added,
            "statuses": dict(Counter(d["base_status"] for d in decisions.values()))}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--append-decisions", action="store_true")
    print(json.dumps(report(parser.parse_args().append_decisions), ensure_ascii=False))
