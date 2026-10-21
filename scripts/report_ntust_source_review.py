"""Record the bounded NTUST notice review against immutable baseline fields."""
from __future__ import annotations

import argparse
import collections
from datetime import datetime, timezone
import gzip
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from exchange_info.ntust_source_review import ACADEMIC, DOCS, HISTORICAL, LANGUAGE, PERIOD
from audit_university_data import digest, leaves
from university_review_ledger import append_decisions as append_review_decisions

OUTPUT = ROOT / "docs/data-verification-20261021"
OVERSEAS_SHA = "406ab94ad4708ba603606afafe25ccfd7f3b5fa74afeb64ecd41a9aca3d01cd4"
MAINLAND_SHA = "2732e75acb1577e21bf6f5956b9f6e2011cd496ca62028d252c15bb94282e912"


def report(append_decisions=False):
    receipts = {}
    for line in (OUTPUT / "manual-source-receipts.jsonl").read_text("utf8").splitlines():
        r = json.loads(line)
        if r.get("sha256") in {OVERSEAS_SHA, MAINLAND_SHA}:
            receipts[r["sha256"]] = r
    assert len(receipts) == 2
    for name, sha in [("reviewed_1161_overseas_20261021.pdf", OVERSEAS_SHA),
                      ("reviewed_1152_mainland_20261021.pdf", MAINLAND_SHA)]:
        import hashlib
        assert hashlib.sha256((ROOT / "sources/ntust" / name).read_bytes()).hexdigest() == sha
    with gzip.open(ROOT / "output/data-verification-20261021/baseline/records.jsonl.gz", "rt", encoding="utf8") as stream:
        records = [r for line in stream if (r := json.loads(line))["home_id"] == "ntust"]
    reviewed = datetime.now(timezone.utc).isoformat()
    decisions = {}

    def decide(r, pointer, value, status, expected, sha, locator, reason):
        receipt = receipts[sha]
        rid = digest(["ntust-20261021-round10", r["record_id"], pointer, sha])[:28]
        decisions[rid] = {
            "review_id": rid, "base_record_id": r["record_id"], "pointer": pointer,
            "base_value": value, "base_value_sha256": digest(value),
            "base_status": status, "expected_value_or_interpretation": expected,
            "reason": reason, "source_url": receipt["url"], "source_sha256": sha,
            "source_locator": locator, "retrieved_at": receipt["completed_at"],
            "reviewed_at": reviewed, "method": "codex_official_pdf_reading_with_visual_layout_check",
            "whole_record_verified": False,
        }

    for r in records:
        data = r["data"]
        mainland = data.get("country") in {"中國大陸", "大陸地區"}
        sha = MAINLAND_SHA if mainland else OVERSEAS_SHA
        if r["kind"] == "partner":
            for key in ("availability_status", "application_window_status", "application_deadline", "application_info"):
                decide(r, "/" + key, data[key], "contradicted" if key in {"application_deadline", "application_info"} else "needs_confirmation",
                       HISTORICAL if mainland else PERIOD, sha,
                       "大陸簡章第2頁申請期限" if mainland else "116-1簡章第2–3頁期程與名單開放範圍",
                       "既有115-2資料不能視為仍開放，亦不能自動移植成116-1逐校可申請方案。")
        if r["kind"] == "university":
            decide(r, "/academic_score_minimum", data["academic_score_minimum"], "contradicted", None,
                   OVERSEAS_SHA, "第1頁資格表", "不支持共用百分制65分，不能轉換成指定學期班排名。")
        if r["kind"] == "deadline_card":
            decide(r, "/study_plan_limit/max_pages", data["study_plan_limit"]["max_pages"], "contradicted", None,
                   OVERSEAS_SHA, "第3頁應上傳文件第4項", "約1–2頁是篇幅指引，不是硬性最多兩頁。")
        if r["kind"] == "dashboard":
            decide(r, "/academic_score_minimum", data["academic_score_minimum"], "contradicted", None,
                   OVERSEAS_SHA, "第1頁資格表", "不支持共用百分制60分或65分門檻。")
            for i, period in enumerate(data["application_periods"]):
                mainland_period = "大陸" in period["title"]
                decide(r, f"/application_periods/{i}", period, "contradicted",
                       HISTORICAL if mainland_period else PERIOD,
                       MAINLAND_SHA if mainland_period else OVERSEAS_SHA,
                       "第2頁申請時程", "原始申請起迄、紙本收件及後續公告時間不符所讀正式簡章；不同梯次分開呈現。")
        for pointer, value in leaves(data):
            if not isinstance(value, str):
                continue
            if "免附外語" in value or "大陸交換免語檢" in value:
                decide(r, pointer, value, "contradicted", LANGUAGE, MAINLAND_SHA,
                       "第1頁：大學部及研究所學業與英語條件",
                       "大陸簡章明列英語門檻，不能因中文授課或地區而推定免語檢；同欄其他主張未全部核實。")
            elif ("列印" in value and "申請表" in value and ("17:00" in value or "紙本" in value)) or "紙本送件" in value:
                decide(r, pointer, value, "contradicted" if not mainland else "needs_confirmation",
                       DOCS[0] if not mainland else "115-2大陸初審為線上填報；錄取資格確認、家長同意及接待校表件屬後續階段，依通知辦理。",
                       sha, "歐美亞澳第2–3頁；大陸第2–3頁",
                       "不得把後續接待校表件與母校初審混為同一紙本截止。")
            elif ("2026/05/19" in value or "06/17" in value or "2026年10月1日" in value or value.startswith("2026-10-01")):
                decide(r, pointer, value, "contradicted", HISTORICAL if mainland else PERIOD, sha,
                       "第2頁正式線上期程", "原有精確日期缺少適用來源支持，不能持續產生提醒。")
            elif "每份篇幅約 1–2 頁" in value or "每份篇幅約 1-2 頁" in value:
                decide(r, pointer, value, "needs_confirmation", "兩語各約1–2頁屬篇幅指引，不設硬性max_pages；自傳與讀書計畫各自合併兩語為一檔。",
                       OVERSEAS_SHA, "第3頁應上傳文件第3、4項", "只確認篇幅指引及檔案組合，不代表同欄其他文件條件全部正確。")
            elif "班排名前 70%" in value or "全班前 70%" in value:
                decide(r, pointer, value, "needs_confirmation", ACADEMIC, OVERSEAS_SHA,
                       "第1頁指定114-2學期及系所審查例外",
                       "必須保留指定學期與例外，不能由歷年平均或GPA自動替代。")
    added = append_review_decisions(OUTPUT, decisions.values()) if append_decisions else 0
    return {"partner_records": sum(r["kind"] == "partner" for r in records), "whole_record_verified": 0,
            "decision_status_counts": dict(collections.Counter(d["base_status"] for d in decisions.values())),
            "decisions_appended": added}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--append-decisions", action="store_true")
    args = parser.parse_args()
    print(json.dumps(report(args.append_decisions), ensure_ascii=False))
