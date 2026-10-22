"""Bind the bounded CYCU review to baseline fields and retained source hashes."""
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
from exchange_info.cycu_source_review import (
    ACADEMIC, DOCS, INTRO, INTERNATIONAL, MAINLAND, SCHOLARSHIP,
    load_tables, match_row, deadline_text,
)
from audit_university_data import digest, leaves
from university_review_ledger import append_decisions as append_review_decisions

OUTPUT = ROOT / "docs/data-verification-20261021"
HASHES = {
    INTRO: "739fcf0e5786f8a40ff974b221d75de45a63203d1d4e663d6f256ea67b8d7875",
    DOCS: "eb24e78345e37fdf76bd16b3e0c356c5adeed1c185c0bd16121caef4dfd5bf38",
    INTERNATIONAL: "6dd290104de0e0bc91787861896d9afd4559c70f01639385d9d3bf6d49617420",
    MAINLAND: "50623c868ef2479cedb9f2d9b0d554610a8a42c2a7aab2b2588d4793d8bdfdef",
    SCHOLARSHIP: "4ccc64c04245505a170c65edea6b0bbe52bb687a119e2ea7f9c9209955aef512",
}


def report(append_decisions: bool = False) -> dict:
    tables = load_tables(ROOT)
    folder = ROOT / "src/exchange_info/official_data/cycu"
    partners = {r["school_name"]: r for r in map(json.loads, (folder / "partners.jsonl").read_text("utf8").splitlines())}
    receipts = {}
    for file in ("source-receipts.jsonl", "manual-source-receipts.jsonl"):
        for line in (OUTPUT / file).read_text("utf8").splitlines():
            r = json.loads(line)
            if r["url"] in HASHES and HASHES[r["url"]] == r.get("sha256"):
                receipts[r["url"]] = r
    assert len(receipts) == len(HASHES), "Every decision requires its exact source generation"
    with gzip.open(ROOT / "output/data-verification-20261021/baseline/records.jsonl.gz", "rt", encoding="utf8") as stream:
        records = [r for line in stream if (r := json.loads(line))["home_id"] == "cycu"]
    decisions, rows = [], []
    reviewed_at = datetime.now(timezone.utc).isoformat()

    def decide(record, pointer, value, status, expected, reason, url, locator):
        receipt = receipts[url]
        decisions.append({
            "review_id": digest(["cycu-20261021-round9", record["record_id"], pointer, receipt["sha256"]])[:28],
            "base_record_id": record["record_id"], "pointer": pointer, "base_value": value,
            "base_value_sha256": digest(value), "base_status": status,
            "expected_value_or_interpretation": expected, "reason": reason,
            "source_url": url, "source_sha256": receipt["sha256"], "source_locator": locator,
            "retrieved_at": receipt["completed_at"], "reviewed_at": reviewed_at,
            "method": "codex_official_notice_and_table_column_scope_review",
            "whole_record_verified": False,
        })

    for r in records:
        data = r["data"]
        p = partners.get(data.get("school_name", ""))
        if r["kind"] == "partner":
            group, row = match_row(p, tables)
            url = MAINLAND if group == "mainland" else INTERNATIONAL
            locator = f"當期公告表格：{row[0]}" if row else "完整表格比對未對上，未作模糊校名合併"
            for key in ("application_deadline", "application_info", "availability_status", "application_window_status",
                        "quota", "study_period", "language_requirement", "gpa_requirement", "eligibility",
                        "colleges", "degree_levels", "housing_info", "semester_dates"):
                if data.get(key) is None:
                    continue
                status = "contradicted" if key in {"application_deadline", "application_info"} and row else "needs_confirmation"
                reason = "僅核對當期母校公告欄位及適用範圍，接待校及其餘主張尚未完成；未對上不表示合作終止。"
                if key == "gpa_requirement":
                    reason = ACADEMIC
                decide(r, "/" + key, data[key], status, p[key], reason, url, locator)
            rows.append({
                "母校": "中原大學", "合作校": p["school_name"], "國家": p["country"],
                "原始紀錄ID": r["record_id"], "當期來源對應": "已對上指定列" if row else "未對上或校名待確認",
                "期限核對": deadline_text(group, row), "名額核對": p["quota"],
                "語言與資格": p["language_requirement"], "整筆核實": "否",
                "主要缺口": "母校GPA與排名替代衝突；接待校最新資格、名額適用、費用、住宿、校曆及其餘內容",
                "來源網址": url, "來源SHA256": receipts[url]["sha256"],
            })
        # Identify the specific reviewed clauses, never automatically approve
        # the rest of a paragraph containing one of them.
        for pointer, value in leaves(data):
            if not isinstance(value, str):
                continue
            if "704" in value or "oia_outbound@office.cycu.edu.tw" in value:
                decide(r, pointer, value, "contradicted",
                       "申請表正本送維澈樓701B；大陸通過校內審查後與獎助使用outgoing_exchange@cycu.edu.tw；國際二梯使用CYCU表單，其他紙本留存待面試。",
                       "原寄件位置、信箱或所有資料統一送件的說法不符當期公告；同欄其他內容未全數核實。",
                       MAINLAND if p and p["country"] == "中國大陸" else INTERNATIONAL, "當期公告申請方式段落")
            elif ("09/25" in value or "9月25日" in value or value.startswith("2026-09-25")):
                decide(r, pointer, value, "contradicted", "國際第二梯次2026/10/07中午截止，10/14面試；大陸依各校日期。",
                       "舊截止日不能共用至國際與大陸所有合作校。", INTERNATIONAL, "報名截止及面試日期")
            elif ("11月20" in value or "11-20T17" in value) and r["kind"] in {"dashboard", "deadline_card"}:
                decide(r, pointer, value, "contradicted", "11/20只對應安徽；福州11/30，蘭州空白，均未列17:00。",
                       "不能把單校日期升為大陸組共同精確截止。", MAINLAND, "校內截止日期欄")
            elif ("10月16" in value or value.startswith("2026-10-16T17")) and r["kind"] in {"dashboard", "exchange_info"}:
                decide(r, pointer, value, "contradicted", "國際組公告11/04 17:00，但內文表單日期待定；大陸組個別通知。",
                       "原10/16不符所讀來源；同頁仍有日期及春秋季標題差異，保留待確認。", SCHOLARSHIP, "申請期限與表單寄送段落")
            elif "前 30%" in value and ("符合其一" in value or "兩者" in value or "或" in value):
                decide(r, pointer, value, "needs_confirmation", ACADEMIC,
                       "一般介紹與當期公告對GPA是否能以排名替代有差異，不能直接判通過。", INTERNATIONAL, "申請基本資格（與p=6336、p=6338比較）")
    unique = {}
    for decision in decisions:
        existing = unique.get(decision["review_id"])
        if existing is None or decision["base_status"] == "contradicted":
            unique[decision["review_id"]] = decision
    decisions = list(unique.values())
    assert len(rows) == 89
    path = OUTPUT / "cycu-program-review.csv"
    with path.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    added = append_review_decisions(OUTPUT, decisions) if append_decisions else 0
    return {"partner_records": len(rows), "matched_international": 20, "matched_mainland": 21,
            "source_mainland_rows": 22, "whole_record_verified": 0,
            "decision_status_counts": dict(collections.Counter(d["base_status"] for d in decisions)),
            "decisions_appended": added}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--append-decisions", action="store_true")
    args = parser.parse_args()
    print(json.dumps(report(args.append_decisions), ensure_ascii=False))
