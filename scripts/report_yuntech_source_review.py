"""Bind bounded YunTech findings to the immutable audit baseline."""
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
from exchange_info.yuntech_source_review import (
    ACADEMIC, AWARD, AWARDS, DOCS, GUIDELINES, LANGUAGE, MAINLAND, MAINLAND_DOCS,
    OBLIGATIONS, PERIOD, PORTAL, TABLE, WANG, load_snapshot,
)
from audit_university_data import digest, leaves
from university_review_ledger import append_decisions as append_review_decisions

OUTPUT = ROOT / "docs/data-verification-20261021"


def report(append_decisions=False):
    s = load_snapshot(ROOT); checked = datetime.now(timezone.utc).isoformat()
    receipts = {r["url"]: r for r in s["sources"] if r["transport_result"] == "retrieved"}
    folder = ROOT / "src/exchange_info/official_data/yuntech"
    partners = {p["school_name"]: p for p in map(json.loads, (folder / "partners.jsonl").read_text("utf8").splitlines())}
    workflows = {p["school_name"]: p for p in map(json.loads, (folder / "application_workflows.jsonl").read_text("utf8").splitlines())}
    decisions, csv_rows = {}, []

    def decide(r, pointer, value, status, expected, url, locator, reason):
        receipt = receipts[url]
        rid = digest(["yuntech-round17", r["record_id"], pointer, receipt["sha256"]])[:28]
        decisions[rid] = {"review_id": rid, "base_record_id": r["record_id"], "pointer": pointer,
            "base_value": value, "base_value_sha256": digest(value), "base_status": status,
            "expected_value_or_interpretation": expected, "reason": reason,
            "source_url": url, "source_sha256": receipt["sha256"], "source_locator": locator,
            "retrieved_at": receipt["completed_at"], "reviewed_at": checked,
            "method": "codex_bounded_official_rule_review_and_1152_roster_correspondence",
            "whole_record_verified": False}

    with gzip.open(ROOT / "output/data-verification-20261021/baseline/records.jsonl.gz", "rt", encoding="utf8") as stream:
        for line in stream:
            r = json.loads(line)
            if r["home_id"] != "yuntech": continue
            data = r["data"]
            if r["kind"] == "partner":
                p = partners[data["school_name"]]; match = s["table_matches"].get(p["school_name"])
                if match:
                    decide(r, "/school_name", data["school_name"], "verified_reference", match, TABLE,
                        f"self.school school_sn={match['school_sn']}, sn={match['sn']}",
                        "既有來源ID及中英文校名對應；不等於當期開放或整筆核實。")
                for key in ("quota", "availability_status", "application_deadline", "application_info", "eligibility",
                    "gpa_requirement", "language_requirement", "tuition_info", "colleges", "degree_levels", "study_period"):
                    bad_date = key == "application_deadline" and p["country"] == "中國大陸" and "10/16" in str(data.get(key))
                    decide(r, "/" + key, data.get(key), "contradicted" if bad_date else "needs_confirmation", p[key],
                        MAINLAND if bad_date else GUIDELINES, "115-2赴陸公告10/01中午" if bad_date else "113校級要點及115-2管道範圍",
                        "母校共同條文部分修正；接待校個別條件尚待逐一核對。")
                csv_rows.append({"母校": "國立雲林科技大學", "合作方案": p["school_name"], "國家": p["country"],
                    "原始紀錄ID": r["record_id"], "來源對應": f"115-2 school_sn={match['school_sn']}" if match else "本輪系統表未對上",
                    "名額參考": p["quota"], "目前狀態": p["availability_status"], "整筆核實": "否",
                    "待補查": "接待校當期條件與完整文件、學制、語言、課程、費用、住宿、校曆、圖片及心得"})
            if r["kind"] == "workflow":
                current = workflows[data["school_name"]]
                for i, step in enumerate(data["steps"]):
                    for key in ("title", "summary", "details", "document_requirements"):
                        if key in step:
                            decide(r, f"/steps/{i}/{key}", step[key], "needs_confirmation", current["steps"][i].get(key),
                                MAINLAND if data.get("country") == "中國大陸" else PORTAL,
                                "115-2管道流程；通則及獎助須分開適用", "初審、接待校錄取、一般交換及受獎義務不能混成單一通用流程。")
            if r["kind"] == "destination":
                decide(r, "/cost_summary", data.get("cost_summary"), "needs_confirmation", "個別接待校生活費待核實",
                    GUIDELINES, "第7點自行負擔費用", "國家預設估價不等於官方逐校生活費。")
            for pointer, value in leaves(data):
                if pointer in {"/academic_gpa_minimum", "/selection_rules/undergraduate_gpa_minimum"} and value is not None:
                    decide(r, pointer, value, "contradicted", None, GUIDELINES, "第2點第6款", "無GPA2.5／2.75替代條文。")
                if pointer.startswith("/language_score_minimums/") and value is not None:
                    decide(r, pointer, value, "needs_confirmation", LANGUAGE, GUIDELINES, "第2點第5、7、8款", "授課語言、地區、接待校與效期均須核對。")
                if not isinstance(value, str): continue
                if "中英文" in value and any(w in value for w in ("讀書計畫", "自傳", "學習計畫")):
                    decide(r, pointer, value, "contradicted", DOCS[2], GUIDELINES, "第3點第8–10款及中文譯本說明", "非大陸英文或接待國語言，赴陸中文；非所有人每篇均中英各一份。")
                elif "3,000" in value and "保證金" in value:
                    decide(r, pointer, value, "needs_confirmation", DOCS[3], PORTAL, "115-2首頁收件公告", "本輪已讀來源未核實保證金金額及退還條件。")
                elif "1,500" in value and "2,000" in value and "心得" in value:
                    decide(r, pointer, value, "needs_confirmation", OBLIGATIONS[3] + AWARDS[5], WANG, "發放作業規定第7點", "一般報告與王秋雄受獎生文字5頁分開，未核實全員1500–2000字。")
                elif "一學年最高 30 萬" in value or "一學年最高30萬" in value:
                    decide(r, pointer, value, "contradicted", AWARDS[3], WANG, "發放作業規定第6點", "按地區每學期最高額、依預算核定，未列美國全年固定30萬上限。")
                elif "2027" in value and ("2月下旬" in value or "3月下旬" in value or "3月26" in value):
                    decide(r, pointer, value, "needs_confirmation", PERIOD, PORTAL, "115-2系統日程", "歷史梯次不能順延作116確定日期。")

    with (OUTPUT / "yuntech-program-review.csv").open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(csv_rows[0])); writer.writeheader(); writer.writerows(csv_rows)
    gaps = {"school_id": "yuntech", "whole_records_verified": 0, "matched_existing_records": len(s["table_matches"]),
        "unmatched_existing_records": [p["school_name"] for p in partners.values() if p["school_name"] not in s["table_matches"]],
        "unmatched_source_rows": s["unmatched_source_rows"], "source_conflicts_and_limits": s["source_conflicts"]}
    (OUTPUT / "round17-source-conflicts.json").write_text(json.dumps(gaps, ensure_ascii=False, indent=2) + "\n", "utf8")
    added = append_review_decisions(OUTPUT, decisions.values()) if append_decisions else 0
    return {"partner_rows": len(csv_rows), "decisions": len(decisions), "added": added,
        "statuses": dict(Counter(d["base_status"] for d in decisions.values()))}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__); parser.add_argument("--append-decisions", action="store_true")
    print(json.dumps(report(parser.parse_args().append_decisions), ensure_ascii=False))
