"""Bind YZU's partial source review to the preserved baseline."""
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
from exchange_info.yzu_source_review import (
    ACADEMIC, GENERAL, MAINLAND, MANAGEMENT, NOTICE, FORM, SCHOLARSHIP,
    OBLIGATIONS, TABLE, load_tables, matching_rows,
)
from audit_university_data import digest, leaves
from university_review_ledger import append_decisions as append_review_decisions

OUTPUT = ROOT / "docs/data-verification-20261021"


def report(append_decisions=False):
    tables = load_tables(ROOT)
    receipts = {r["url"]: r for r in tables["sources"]}
    partners = {r["school_name"]: r for r in map(
        json.loads, (ROOT / "src/exchange_info/official_data/yzu/partners.jsonl").read_text("utf8").splitlines()
    )}
    with gzip.open(ROOT / "output/data-verification-20261021/baseline/records.jsonl.gz", "rt", encoding="utf8") as stream:
        records = [r for line in stream if (r := json.loads(line))["home_id"] == "yzu"]
    decisions, rows = {}, []
    reviewed = datetime.now(timezone.utc).isoformat()

    def decide(record, pointer, value, status, expected, url, locator, reason):
        receipt = receipts[url]
        rid = digest(["yzu-20261021-round11", record["record_id"], pointer, receipt["sha256"]])[:28]
        decisions[rid] = {
            "review_id": rid, "base_record_id": record["record_id"], "pointer": pointer,
            "base_value": value, "base_value_sha256": digest(value), "base_status": status,
            "expected_value_or_interpretation": expected, "reason": reason,
            "source_url": url, "source_sha256": receipt["sha256"], "source_locator": locator,
            "retrieved_at": receipt["completed_at"], "reviewed_at": reviewed,
            "method": "codex_official_table_scope_and_pdf_visual_review",
            "whole_record_verified": False,
        }

    for r in records:
        data = r["data"]
        p = partners.get(data.get("school_name", ""))
        if r["kind"] == "partner":
            group, matches = matching_rows(p, tables)
            url = TABLE if group == "international" else MAINLAND if group == "mainland" else MANAGEMENT if group == "management" else GENERAL
            locator = f"表格第{matches[0]['sheet_row']}列" if group == "international" else f"{group}對應列；有無同名多列均保留"
            for key in ("application_deadline", "application_info", "quota", "gpa_requirement",
                        "language_requirement", "eligibility", "tuition_info", "semester_dates",
                        "availability_status", "availability_note"):
                if data.get(key) is None:
                    continue
                decide(r, "/" + key, data[key], "needs_confirmation", p[key], url, locator,
                       "母校表列及適用階段部分比對；接待校現行證據與整筆其餘內容尚未完成。")
            if group == "international":
                c = matches[0]["cells"]
                if c["H"] is None:
                    decide(r, "/quota", data["quota"], "contradicted", p["quota"], TABLE, locator + " H欄",
                           "原表名額空白，不能自行填為兩名。")
                if c["E"] == "美國俄亥俄州立大學":
                    decide(r, "/tuition_info", data["tuition_info"], "contradicted", p["tuition_info"], TABLE, locator + " Y欄",
                           "母校表格明列該協議不免學費；不能套用其他學校免學費規則。")
            rows.append({
                "母校": "元智大學", "合作校": p["school_name"], "國家": p["country"],
                "原始紀錄ID": r["record_id"], "申請管道": group,
                "當期來源對應": "指定列已對上" if matches else "逐校資料待核對",
                "初審與後續日期": p["application_deadline"], "名額": p["quota"],
                "主要缺口": "接待校現行資格、費用、住宿、校曆、圖片、心得與其餘主張；母校來源矛盾另列",
                "整筆核實": "否", "來源網址": url, "來源SHA256": receipts[url]["sha256"],
            })
        for pointer, value in leaves(data):
            if not isinstance(value, str):
                continue
            if ("前 50%" in value or "前50%" in value) and ("管理學院" in value or "管院" in value):
                decide(r, pointer, value, "contradicted", ACADEMIC, MANAGEMENT, "申請資格第2點（頁面渲染資料Item.app_qualify）",
                       "管院為GPA3.0以上為原則，不能用班排50%替代；校級評分50%亦非名次上限。")
            elif "500 字" in value or "500字" in value:
                # Avoid matching the unrelated 1,500-character return-report text.
                if "1,500" not in value and "1500" not in value:
                    decide(r, pointer, value, "needs_confirmation", "CF02赴陸免英文自傳、計畫及推薦信；未列共同500字中文計畫規格。", FORM, "檢附文件5、6項",
                           "接待校可另要求文件，不能把未核實規格當共同校內門檻。")
            elif "11-01T17" in value or "11/01 17" in value:
                decide(r, pointer, value, "contradicted", "11/01為西南學校資料繳交，未列時刻；初審10/20。", MAINLAND, "西南大學列兩種繳交日期",
                       "後續送件不得作為所有學校共同初審截止，17:00無來源支持。")
            elif "1500" in value or "1,500" in value or "6 張照片" in value or "六張照片" in value:
                decide(r, pointer, value, "needs_confirmation", "保證金及返國繳件依切結書及通知；赴陸另列2000字附圖，國際1500字六張照片未核實。", OBLIGATIONS, "第6及17點",
                       "保證金退還、獎助核銷與學分採認是不同程序，不得拼成未核實的共同退費條件。")
            elif ("12 ECTS" in value or "12 學分（ECTS）" in value) and ("第 5 條" in value or "1-51" in value):
                decide(r, pointer, value, "contradicted", "四門課或12學分在選送生義務；簡報註ECTS但義務頁未註，單位須確認。教務辦法第5條為成績換算。", OBLIGATIONS, "第15、16點與教務辦法第5條交叉閱讀",
                       "原引用法規與條文適用錯誤，不能作交換申請成績門檻。")
            elif ("／月" in value or "/月" in value) and ("12,000" in value or "8,000–10,000" in value) and ("補助" in value or "獎" in value):
                decide(r, pointer, value, "needs_confirmation", "依115年度標準及個別計畫核定，千人計畫兩類上限45,000／35,000元；未核實固定每月給付。", SCHOLARSHIP, "補助辦法與115千人出國計畫金額",
                       "不得把地區生活費估計當作普遍可領的獎學金。")
            elif "2027年1月" in value or "2027 年 1 月" in value or value.startswith("2026-08-26T09"):
                decide(r, pointer, value, "needs_confirmation", "115-2為08/26開始、09/22中午截止；未公告09:00及下一期精確時間。", NOTICE, "申請日期",
                       "一般季節指引不是下一期確定申請時程。")
        if r["kind"] == "university" and data.get("academic_score_minimum") == 70:
            decide(r, "/academic_score_minimum", 70, "contradicted", None, GENERAL, "校內甄選評分標準",
                   "50%系排＋50%英檢是計分配比，70／80是交換後成績規定。")
        if r["kind"] == "destination" and data.get("cost_summary"):
            decide(r, "/cost_summary", data["cost_summary"], "needs_confirmation",
                   "個別接待校當期生活費待查；不採國別預設價格作校方每月估計。",
                   GENERAL, "交換費用依個別接待校及協議核對",
                   "來源表欄位可能是整學期、網址或空白，不能直接套用共同月費；原值留存供續查。")
        if r["kind"] == "deadline_card":
            limit = data.get("study_plan_limit", {})
            if limit.get("min_chars") == 500:
                decide(r, "/study_plan_limit/min_chars", 500, "needs_confirmation", None, FORM, "檢附文件5項",
                       "表單未列赴陸共同500字中文計畫；個別接待校要求仍須另查。")
    with (OUTPUT / "yzu-program-review.csv").open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    added = append_review_decisions(OUTPUT, decisions.values()) if append_decisions else 0
    return {"partner_rows": len(rows), "decisions": len(decisions), "added": added,
            "statuses": dict(collections.Counter(x["base_status"] for x in decisions.values()))}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--append-decisions", action="store_true")
    args = parser.parse_args()
    print(json.dumps(report(args.append_decisions), ensure_ascii=False))
