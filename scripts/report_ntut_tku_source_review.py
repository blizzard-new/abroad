"""Bind round 12's bounded NTUT/TKU findings to the immutable baseline."""
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
from exchange_info.ntut_source_review import (
    ACADEMIC, DOCS, GENERAL, INFO, LANDING, LANGUAGE, OBLIGATIONS,
    PARTNERS, PERIOD, PLAN, QA, SCHOLARSHIP, SCHOLARSHIPS, SNAPSHOT,
    STEP1, STEP3, SUPPLEMENT,
)
from audit_university_data import digest, leaves
from university_review_ledger import append_decisions as append_review_decisions

OUTPUT = ROOT / "docs/data-verification-20261021"
TKU_PDF_SHA = "62911b08dcd592c4fbb33bebfa4df84f09949099ee5dbec792b21896565109b3"
TKU_TABLE_SHA = "16931e4290fcbcddf846b9b5c68a6efbd5ebb51ff9e051e1098b3b9c1bfa1128"


def report(append_decisions=False):
    receipts = {r["url"]: r for r in json.loads((ROOT / SNAPSHOT).read_text("utf8"))["sources"]}
    manual = [json.loads(s) for s in (OUTPUT / "manual-source-receipts.jsonl").read_text("utf8").splitlines()]
    tku_pdf = next(r for r in reversed(manual) if r.get("sha256") == TKU_PDF_SHA)
    tku_table = next(r for r in reversed(manual) if r.get("sha256") == TKU_TABLE_SHA)
    receipts.update({r["url"]: r for r in (tku_pdf, tku_table)})
    partners = {r["school_name"]: r for r in map(json.loads, (
        ROOT / "src/exchange_info/official_data/ntut/partners.jsonl").read_text("utf8").splitlines())}
    decisions, csv_rows = {}, []
    reviewed_at = datetime.now(timezone.utc).isoformat()

    def decide(record, pointer, value, status, expected, url, locator, reason):
        receipt = receipts[url]
        rid = digest(["ntut-tku-round12", record["record_id"], pointer, receipt["sha256"]])[:28]
        decisions[rid] = {
            "review_id": rid, "base_record_id": record["record_id"], "pointer": pointer,
            "base_value": value, "base_value_sha256": digest(value), "base_status": status,
            "expected_value_or_interpretation": expected, "reason": reason,
            "source_url": url, "source_sha256": receipt["sha256"], "source_locator": locator,
            "retrieved_at": receipt["completed_at"], "reviewed_at": reviewed_at,
            "method": "codex_bounded_official_page_and_pdf_layout_review",
            "whole_record_verified": False,
        }

    with gzip.open(ROOT / "output/data-verification-20261021/baseline/records.jsonl.gz", "rt", encoding="utf8") as f:
        for line in f:
            r = json.loads(line)
            if r["home_id"] not in {"ntut", "tku"}:
                continue
            data = r["data"]
            if r["home_id"] == "tku":
                if r["kind"] == "deadline_card":
                    for key, expected, status, locator in [
                        ("/study_plan_limit/max_pages", None, "contradicted", "第4頁全部資料16頁"),
                        ("/paper_deadline/exact_deadline_at", None, "needs_confirmation", "第3頁各系所指定期限"),
                    ]:
                        value = data
                        for token in key.strip("/").split("/"):
                            value = value[token]
                        decide(r, key, value, status, expected, tku_pdf["url"], locator,
                               "全套資料與單篇計畫、線上截止與紙本系所收件必須分開。")
                if r["kind"] == "partner":
                    quotas = {"立命館大學 ": "1", "長崎外國語大學 ": "2", "成蹊大學 ": "1", "電氣通信大學 ": "3"}
                    for name, quota in quotas.items():
                        if data["school_name"].startswith(name):
                            assert data["quota"] == quota
                            decide(r, "/quota", quota, "verified_reference", quota, tku_table["url"],
                                   f"唯一頁{name.strip()}列名額欄",
                                   "支持2027–2028日語二甄已截止梯次名額；接待校當期條件與整筆未核實。")
                continue
            if r["kind"] == "partner":
                p = partners[data["school_name"]]
                for key in ("availability_status", "quota", "application_deadline", "application_info",
                            "eligibility", "gpa_requirement", "language_requirement", "tuition_info"):
                    if data.get(key) is not None:
                        decide(r, "/" + key, data[key], "needs_confirmation", p[key], PARTNERS,
                               "名單頁首的參考性聲明與當期條件依接待校說明",
                               "母校共用規則不能驗證逐校現行資格、協議、費用或名額。")
                if p["availability_status"] == "not_open":
                    decide(r, "/availability_status", data["availability_status"], "contradicted",
                           "not_open", PARTNERS, "美洲／瓜地馬拉兩校列",
                           "母校名單明列未開放申請，原資料卻顯示open。")
                csv_rows.append({
                    "母校": "國立臺北科技大學", "合作校": p["school_name"], "國家": p["country"],
                    "原始紀錄ID": r["record_id"], "當期狀態": p["availability_status"],
                    "本輪範圍": "母校資格與申請程序部分核對；個別合作與接待校條件待查",
                    "主要缺口": "當期名額、接待校語檢與學制、學費、住宿、校曆、圖片、心得及其餘主張",
                    "整筆核實": "否", "主要來源": PARTNERS, "來源SHA256": receipts[PARTNERS]["sha256"],
                })
            for pointer, value in leaves(data):
                if pointer in {"/academic_score_minimum", "/academic_gpa_minimum",
                               "/selection_rules/undergraduate_gpa_minimum", "/selection_rules/undergraduate_rank_maximum"} and value is not None:
                    decide(r, pointer, value, "contradicted", None, GENERAL, "申請資格／學業成績門檻：無",
                           "不得把獎學金成績門檻或自創換算當一般交換門檻。")
                elif pointer == "/maximum_preferences" and value == 5:
                    decide(r, pointer, value, "contradicted", 10, PLAN, "選擇學校／十個志願",
                           "官方事前規劃與Q&A第11題均為十個志願。")
                if not isinstance(value, str):
                    continue
                if "10/19" in value or "2026-10-19T13" in value or "2026年10月19" in value:
                    decide(r, pointer, value, "contradicted", "2026/10/29 12:00–13:00，科技大樓B2國際會議廳。", INFO,
                           "活動資訊", "原日期、時刻及地點不符公告；活動不是申請截止。")
                elif "2026-12-10T17" in value or "2026/12/10" in value or "2026/12/01" in value:
                    decide(r, pointer, value, "needs_confirmation", PERIOD, LANDING,
                           "115學年度申請期間", "年度慣例未支持116學年度精確時刻與提醒。")
                elif ("70 分" in value or "70分" in value) and "scholarship" not in pointer and any(k in value for k in ("總平均須", "總平均達", "總平均 70", "校內門檻", "學業門檻")):
                    decide(r, pointer, value, "contradicted", ACADEMIC, GENERAL,
                           "申請資格第3項", "一般交換無共同成績門檻；獎助要求必須分開。")
                elif ("iBT 68" in value or "TOEIC 700" in value) and ("基本門檻" in value or "校內" in value or "學海" in value):
                    decide(r, pointer, value, "contradicted", LANGUAGE, PLAN,
                           "語言門檻", "不能用不存在的校級共同分數自動判定接待校通過。")
                elif "大陸" in value and ("免檢附外語" in value or "免繳" in value and "語檢" in value):
                    decide(r, pointer, value, "needs_confirmation", LANGUAGE, STEP1,
                           "語文能力檢定證明", "本輪來源沒有支持所有赴陸計畫共同豁免。")
                elif "2 週" in value and ("補申請" in value or "轉換學校" in value):
                    decide(r, pointer, value, "needs_confirmation", SUPPLEMENT, STEP1,
                           "補申請／轉換學校；對照現行Q&A第7題", "四週薦送期限與兩週申請期限使用不同基準，不擅自合併。")
                elif ("1,500" in value or "1500" in value) and ("返國" in value or "心得" in value):
                    decide(r, pointer, value, "contradicted", OBLIGATIONS[2], STEP3,
                           "返國後／一般生與獲獎生", "一般生2000字、指定獎助3000字及返國兩週，非一律1500字一個月。")
                elif "紙本" in value and ("校內甄選" in value or "申請表" in value) and ("送交" in value or "繳交" in value):
                    decide(r, pointer, value, "contradicted", DOCS[0], STEP1,
                           "交換及獎學金申請文件第1項", "校級初審不收紙本；行前核章與返國核銷是其他階段。")
                elif ("7.5 萬" in value or "75,000" in value) and "學海" in value:
                    decide(r, pointer, value, "needs_confirmation", SCHOLARSHIPS[2], SCHOLARSHIP,
                           "學海補助備註三", "專頁只支持至少60000元，未支持固定非亞洲75000元。")
            if r["kind"] == "destination":
                decide(r, "/cost_summary", data["cost_summary"], "needs_confirmation",
                       "國家預設估計撤出已核實費用，逐校費用待查。", PARTNERS,
                       "各校當期資格與官方來源需分別核對",
                       "原產製程式使用國家預設金額，不能當該校現行生活費證據。")
    with (OUTPUT / "ntut-program-review.csv").open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(csv_rows[0]))
        writer.writeheader()
        writer.writerows(csv_rows)
    added = append_review_decisions(OUTPUT, decisions.values()) if append_decisions else 0
    return {"partner_rows": len(csv_rows), "decisions": len(decisions), "added": added,
            "statuses": dict(Counter(d["base_status"] for d in decisions.values()))}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--append-decisions", action="store_true")
    print(json.dumps(report(parser.parse_args().append_decisions), ensure_ascii=False))
