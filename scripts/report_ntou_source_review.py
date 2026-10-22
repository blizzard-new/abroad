"""Bind bounded NTOU findings to the immutable audit baseline."""
from __future__ import annotations

import argparse
from collections import Counter
import csv
from datetime import datetime, timezone
import gzip
import json
from pathlib import Path
import sys
import subprocess

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from exchange_info.ntou_source_review import (
    ACADEMIC, AWARDS, BROCHURE, DEGREE, DOCS, ENFORCEMENT, LANGUAGE,
    MAINLAND, OBLIGATIONS, PERIOD, REGULATIONS, load_snapshot,
)
from audit_university_data import digest, leaves
from university_review_ledger import append_decisions as append_review_decisions

OUTPUT = ROOT / "docs/data-verification-20261021"


def report(append_decisions=False):
    snapshot = load_snapshot(ROOT)
    checked = datetime.now(timezone.utc).isoformat()
    receipts = {r["url"]: r for r in snapshot["sources"] if r["transport_result"] == "retrieved"}
    base = "b662dced2607bc67c3354c95b7aaad202448bea7"
    code_path = "scripts/build_ntou_catalog.py"
    code = subprocess.check_output(["git", "show", f"{base}:{code_path}"], cwd=ROOT)
    code_url = f"https://github.com/blizzard-new/abroad/blob/{base}/{code_path}"
    import hashlib
    receipts[code_url] = {"sha256": hashlib.sha256(code).hexdigest(), "completed_at": checked}
    folder = ROOT / "src/exchange_info/official_data/ntou"
    partners = {p["school_name"]: p for p in map(json.loads, (folder / "partners.jsonl").read_text("utf8").splitlines())}
    workflows = {p["school_name"]: p for p in map(json.loads, (folder / "application_workflows.jsonl").read_text("utf8").splitlines())}
    decisions, csv_rows = {}, []

    def decide(record, pointer, value, status, expected, url, locator, reason):
        receipt = receipts[url]
        rid = digest(["ntou-round18", record["record_id"], pointer, receipt["sha256"]])[:28]
        decisions[rid] = {
            "review_id": rid, "base_record_id": record["record_id"], "pointer": pointer,
            "base_value": value, "base_value_sha256": digest(value), "base_status": status,
            "expected_value_or_interpretation": expected, "reason": reason,
            "source_url": url, "source_sha256": receipt["sha256"], "source_locator": locator,
            "retrieved_at": receipt["completed_at"], "reviewed_at": checked,
            "method": "codex_bounded_official_rule_review_and_chinese_roster_name_correspondence",
            "whole_record_verified": False,
        }

    baseline = ROOT / "output/data-verification-20261021/baseline/records.jsonl.gz"
    with gzip.open(baseline, "rt", encoding="utf8") as stream:
        for line in stream:
            record = json.loads(line)
            if record["home_id"] != "ntou":
                continue
            data = record["data"]
            if record["kind"] == "partner":
                partner = partners[data["school_name"]]
                mainland = partner["country"] == "中國大陸"
                match = snapshot["mainland_matches" if mainland else "table_matches"].get(partner["school_name"])
                if match:
                    decide(record, "/school_name", data["school_name"], "verified_reference", match,
                        MAINLAND if mainland else BROCHURE,
                        "公告明列六校" if mainland else f"PDF實體頁 {match['pages']}",
                        "僅中文校名對應；不驗證英文校名、接待校當期條件或整筆資料。")
                for key in ("quota", "availability_status", "application_deadline", "application_info", "eligibility",
                    "gpa_requirement", "language_requirement", "tuition_info", "colleges", "degree_levels", "study_period"):
                    contradicted = key == "availability_status" and data.get(key) == "open" and bool(match)
                    decide(record, "/" + key, data.get(key), "contradicted" if contradicted else "needs_confirmation",
                        partner[key], MAINLAND if mainland else BROCHURE,
                        "115-2赴陸公告" if mainland else "2027非大陸簡章及當期適用範圍",
                        "所讀梯次均已截止；母校共同條文與逐校個別條件分開，未對上名單不代表永久停辦。")
                decide(record, "/course_restrictions", data.get("course_restrictions"), "contradicted",
                    OBLIGATIONS[1], ENFORCEMENT, "第9點第3款",
                    "至少一門專業課程僅在接待校無特殊規定時適用，來源未訂全員每學期6學分。")
                csv_rows.append({"母校": "國立臺灣海洋大學", "合作方案": partner["school_name"], "國家": partner["country"],
                    "原始紀錄ID": record["record_id"], "來源對應": json.dumps(match, ensure_ascii=False) if match else "本輪兩名單未對上",
                    "名額參考": partner["quota"], "目前狀態": partner["availability_status"], "整筆核實": "否",
                    "待補查": "英文校名、接待校當期條件、全部表格名額與合併格、語檢、文件、課程、費用、住宿、校曆、圖片及心得"})
            elif record["kind"] == "workflow":
                current = workflows[data["school_name"]]
                for i, step in enumerate(data["steps"]):
                    for key in ("title", "summary", "details", "document_requirements"):
                        if key in step:
                            decide(record, f"/steps/{i}/{key}", step[key], "needs_confirmation", current["steps"][i].get(key),
                                MAINLAND if data.get("country") == "中國大陸" else BROCHURE,
                                "不同管道初審及一般交換／受獎義務", "赴陸與非大陸表單、期限、承辦窗口分開；受獎核銷不套全員。")
            elif record["kind"] == "destination":
                decide(record, "/cost_summary", data.get("cost_summary"), "needs_confirmation", "個別接待校生活費待核實",
                    BROCHURE, "注意事項及逐校費用", "國家預設估價不等於官方逐校生活費。")

            for pointer, value in leaves(data):
                if pointer == "/academic_gpa_minimum" and value is not None:
                    decide(record, pointer, value, "contradicted", None, ENFORCEMENT, "第3點第3款", "前一學期及格不能由累計GPA替代。")
                if pointer.startswith("/language_score_minimums/") and value is not None:
                    decide(record, pointer, value, "needs_confirmation", LANGUAGE, REGULATIONS, "附表一",
                        "須選授課語言並核對分制、效期及接待校門檻；不能單一分數自動通過。")
                if not isinstance(value, str):
                    continue
                if "單一 PDF" in value or "單一PDF" in value:
                    decide(record, pointer, value, "contradicted", DOCS[0], BROCHURE, "實體頁3–5申請程序及文件清單",
                        "官方要求指定文件PDF及紙本，未要求所有文件合併成一個PDF。")
                elif ("1,000" in value and "1,500" in value) or ("1000" in value and "1500" in value and "計畫" in value):
                    decide(record, pointer, value, "contradicted", DOCS[3], BROCHURE, "實體頁5自傳及讀書計畫",
                        "範例僅供參考；已讀來源未支持每篇1000–1500字硬性要求。")
                elif "6 學分" in value or "6學分" in value:
                    decide(record, pointer, value, "contradicted", OBLIGATIONS[1], ENFORCEMENT, "第9點第3款",
                        "未訂全員6學分；接待校無特殊規定時至少一門專業課程。")
                elif ("1 個月" in value or "一個月" in value) and any(w in value for w in ("心得", "核銷")):
                    decide(record, pointer, value, "contradicted", AWARDS[3], ENFORCEMENT, "第9點第5款及簡章實體頁7",
                        "受獎生返國兩週心得、四週核銷；研修結束一個月內返國是另一規定。")
                elif "DELF B1" in value:
                    decide(record, pointer, value, "needs_confirmation", LANGUAGE, REGULATIONS, "附表一法文欄",
                        "舊表DELF1不能自動等同CEFR B1；接待校要求另查。")
                elif "2027/02/25" in value or "2027/05/07" in value:
                    decide(record, pointer, value, "needs_confirmation", PERIOD, BROCHURE, "實體頁3報名截止",
                        "2027春秋研修的申請是2026/05/08；未核實未來梯次確切日期，不能順延。")

    with (OUTPUT / "ntou-program-review.csv").open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(csv_rows[0]))
        writer.writeheader(); writer.writerows(csv_rows)
    supplement = ROOT / "output/data-verification-20261021/derived-baseline/records.jsonl.gz"
    with gzip.open(supplement, "rt", encoding="utf8") as stream:
        for line in stream:
            record = json.loads(line)
            if record["home_id"] != "ntou":
                continue
            data = record["data"]
            if record["kind"] == "raw:student_experiences.jsonl":
                for key in ("content_status", "summary", "summary_zh", "original_summary", "theme_summaries", "theme_summaries_zh", "author_name"):
                    decide(record, "/" + key, data.get(key), "contradicted" if key == "content_status" else "needs_confirmation",
                        "只保留候選連結；原文待逐篇讀取，無已驗證的學生經驗摘要。", code_url,
                        "基準版本build_ntou_catalog.py 1032–1082：summary_text與theme_map由固定範本、校名及國家費用組成",
                        "程式並未以學生報告正文生成這些摘要；full_text標記不能作讀過原文的證據。")
            elif record["kind"] == "raw:student-experience-digests.json":
                for key in ("summary_zh", "themes", "report_count"):
                    decide(record, "/" + key, data.get(key), "needs_confirmation", "移除未經原文支持的摘要；保留連結待查。",
                        code_url, "1129–1139：複製上述範本至digest", "這些內容不是逐篇心得閱讀結論。")
            elif record["kind"] == "raw:student_life.jsonl":
                decide(record, "/status", data.get("status"), "needs_confirmation", "partial", code_url,
                    "life_records生成段落", "共用範本與國家預設不能當逐校官方生活證據。")
                for i, evidence in enumerate(data["evidence"]):
                    decide(record, f"/evidence/{i}/text", evidence["text"], "needs_confirmation", "原值存參考區，逐校原文查核前不作生活證據。",
                        code_url, "life_records及ev_list生成段落", "母校規則、國家預設及學校資訊須逐項驗證適用範圍。")
    for decision in decisions.values():
        if decision["source_url"] == code_url:
            decision["method"] = "repository_template_provenance_review_not_external_fact_verification"
            decision["source_type"] = "repository_implementation_at_original_baseline"
            decision["baseline_inventory"] = "output/data-verification-20261021/derived-baseline"
    matches = snapshot["table_matches"] | snapshot["mainland_matches"]
    gaps = {"school_id": "ntou", "whole_records_verified": 0, "matched_existing_records": len(matches),
        "unmatched_existing_records": [p["school_name"] for p in partners.values() if p["school_name"] not in matches],
        "source_conflicts_and_limits": snapshot["source_conflicts"]}
    (OUTPUT / "round18-source-conflicts.json").write_text(json.dumps(gaps, ensure_ascii=False, indent=2) + "\n", "utf8")
    added = append_review_decisions(OUTPUT, decisions.values()) if append_decisions else 0
    return {"partner_rows": len(csv_rows), "decisions": len(decisions), "added": added,
        "statuses": dict(Counter(d["base_status"] for d in decisions.values()))}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--append-decisions", action="store_true")
    print(json.dumps(report(parser.parse_args().append_decisions), ensure_ascii=False))
