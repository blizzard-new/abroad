"""Record inspected template provenance separately from external fact checks."""
from __future__ import annotations

import argparse
from collections import Counter
import gzip
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from exchange_info.generated_content_review import digest, load_manifest
from university_review_ledger import append_decisions as append_review_decisions


def report(append_decisions=False, *, round_id=19):
    manifest = load_manifest(ROOT, round_id=round_id)
    decisions = {}
    with gzip.open(ROOT / "output/data-verification-20261021/derived-baseline/records.jsonl.gz", "rt", encoding="utf8") as stream:
        for line in stream:
            record = json.loads(line)
            school = record["home_id"]
            if school not in manifest["schools"]:
                continue
            scope = manifest["schools"][school]
            data = record["data"]
            fields = []
            if record["kind"] == "raw:student_experiences.jsonl":
                if not scope["stories"]:
                    continue
                if round_id == 20:
                    claims = {(r["school_name"], r["source_url"], r["claim_sha256"]): r
                        for r in scope["stories"]}
                    claim = claims.get((data["school_name"], data["source_url"],
                        digest({key: data.get(key) for key in manifest["story_fields"]})))
                    if claim is None:
                        raise ValueError(f"Unbound round-20 baseline story: {record['record_id']}")
                fields = [("/" + key, data.get(key), "contradicted" if key == "content_status" else "needs_confirmation")
                    for key in ("content_status", "summary", "summary_zh", "original_summary", "theme_summaries", "theme_summaries_zh", "author_name")]
                if round_id == 20 and data.get("content_status") == "metadata_only":
                    # Its existing classification was correct; review the claims inside it.
                    fields = [field for field in fields if field[0] != "/content_status"]
                locator = scope["reviewed_line_ranges"]["story"]
                if data["source_type"] == "pdf":
                    fields.append(("/source_type", "pdf", "contradicted"))
            elif record["kind"] == "raw:student-experience-digests.json":
                if not scope["digests"]:
                    continue
                fields = [("/" + key, data.get(key), "needs_confirmation") for key in ("summary_zh", "themes", "report_count")]
                locator = scope["reviewed_line_ranges"]["story"]
            elif record["kind"] == "raw:student_life.jsonl":
                if not scope["life"]:
                    continue
                if round_id in {21, 22}:
                    known = {(r["school_name"], r["country"], r["baseline_evidence_sha256"])
                        for r in scope["life"]}
                    if (data["school_name"], data.get("country"), digest(data["evidence"])) not in known:
                        raise ValueError(f"Unbound round-{round_id} life row: {record['record_id']}")
                fields = [("/status", data.get("status"), "needs_confirmation")]
                fields += [(f"/evidence/{i}/text", evidence["text"], "needs_confirmation") for i, evidence in enumerate(data["evidence"])]
                if round_id in {21, 22}:
                    fields += [(f"/evidence/{i}/kind", evidence["kind"], "contradicted")
                        for i, evidence in enumerate(data["evidence"])
                        if evidence["theme"] in {"cost", "safety"}]
                locator = scope["reviewed_line_ranges"]["life"]
            for pointer, value, status in fields:
                rid = digest([f"generated-content-round{round_id}", record["record_id"], pointer, scope["code_sha256"]])[:28]
                decisions[rid] = {
                    "review_id": rid, "base_record_id": record["record_id"], "pointer": pointer,
                    "base_value": value, "base_value_sha256": digest(value), "base_status": status,
                    "expected_value_or_interpretation": "article" if pointer == "/source_type" else "保留候選連結與原值，撤下未由原文支持的全文摘要及生活證據。",
                    "reason": "PDF是連結格式；模型使用article分類，原值被不支援的pdf列舉拒絕。" if pointer == "/source_type" else
                        "已檢視建置程式：摘要混入固定範本、國家預設或母校規則；不能以full_text或ready標記推定逐篇閱讀或逐校事實。",
                    "source_url": f"https://github.com/blizzard-new/abroad/blob/{manifest['base_commit']}/{scope['code_path']}",
                    "source_sha256": scope["code_sha256"], "source_locator": f"reviewed generation lines {locator}",
                    "retrieved_at": manifest["reviewed_at"], "reviewed_at": manifest["reviewed_at"],
                    "source_type": "repository_implementation_at_original_baseline",
                    "method": "repository_template_provenance_review_not_external_fact_verification",
                    "baseline_inventory": "output/data-verification-20261021/derived-baseline",
                    "whole_record_verified": False,
                }
                if round_id in {21, 22}:
                    decisions[rid]["expected_value_or_interpretation"] = "先保留原值與來源候選，未逐校核對的範本及母校專屬規則不作跨校共用生活證據。"
                    decisions[rid]["reason"] = "已檢視生成資料流：國家預設費用／簽證、母校修課與繳費規定及部分未複核摘錄混入逐校欄位；不能由程式生成或來源連結推定完整適用。"
                    decisions[rid]["method"] = "repository_data_flow_and_shared_host_applicability_review_not_external_fact_verification"
                if round_id == 20:
                    decisions[rid]["review_action"] = claim["action"]
                    if claim["action"] == "exclude_program_record":
                        decisions[rid]["expected_value_or_interpretation"] = "錄取或獎助紀錄須與學生心得分開；保留原始資料及連結供名單查核。"
                        decisions[rid]["reason"] = "建置程式以錄取／獎助名單生成此列；不能將名單的學生人數、科系或獎助推成學生生活經驗。名單事實本輪未逐筆核實。"
                    elif claim["action"] == "retain_official_excerpt":
                        decisions[rid]["expected_value_or_interpretation"] = claim["reviewed_excerpt"]
                        decisions[rid]["reason"] = "官方頁面確有學生短篇摘錄，可保留限於摘錄的改寫；原有修課、住宿和費用主題來自範本，沒有在該摘錄中提供。"
                        decisions[rid]["additional_evidence"] = claim["evidence"]
                        decisions[rid]["method"] = "repository_template_provenance_and_official_page_excerpt_review"
    added = append_review_decisions(ROOT / "docs/data-verification-20261021", decisions.values()) if append_decisions else 0
    return {"decisions": len(decisions), "added": added,
        "statuses": dict(Counter(r["base_status"] for r in decisions.values()))}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--append-decisions", action="store_true")
    parser.add_argument("--round-id", type=int, choices=(19, 20, 21, 22), default=19)
    args = parser.parse_args()
    print(json.dumps(report(args.append_decisions, round_id=args.round_id), ensure_ascii=False))
