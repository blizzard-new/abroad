"""CCU full catalogue inventory; coverage is never an eligibility decision.

The 104 exchange-list identities and the broader Gamma agreement catalogue are
separate denominators. All reference identities stay outside current selection.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BUNDLE = ROOT / "src/exchange_info/official_data/ccu"
BASE_COMMIT = "59a20f27fcee00fb597abc79e75ec11778317422"


def read(name):
    return json.loads((BUNDLE / name).read_text(encoding="utf-8"))


def build():
    partners = [json.loads(line) for line in (BUNDLE / "partners.jsonl").read_text().splitlines()]
    overseas = {row["ccu_page"]: row for row in read("overseas-reviewed-fields.json")}
    profiles = {row["ccu_page"]: row for row in read("profile-reviewed-fields.json")}
    documents = {row["ccu_page"]: row for row in read("partner-document-requirements.json")}
    home = read("home-rules.json")
    assets_path = BUNDLE / "campus-assets.json"
    assets = {row["ccu_page"]: row for row in json.loads(assets_path.read_text())["schools"]} if assets_path.exists() else {}
    completion_path = BUNDLE / "completion-reviewed-fields.json"
    completion = {row["ccu_page"]: row for row in json.loads(completion_path.read_text())["schools"]} if completion_path.exists() else {}
    rows = []
    for partner in partners:
        page = partner["source_pages"][0]
        fields = {}
        for scope, matrix in [("host", overseas), ("profile", profiles)]:
            for key in next(iter(matrix.values()))["fields"]:
                supplement = completion.get(page, {}).get("host_fields" if scope == "host" else "profile_fields", {})
                if key in supplement:
                    fields[f"{scope}.{key}"] = supplement[key]
                elif page in matrix:
                    field = matrix[page]["fields"][key]
                    fields[f"{scope}.{key}"] = field
                else:
                    fields[f"{scope}.{key}"] = {
                        "status": "outside_previous_55_review", "value": None,
                        "reason": "本期未開放參考校，先前55校逐欄查核未涵蓋；不能以旧年度條件作當期申請依據。",
                        "evidence": [],
                    }
        for key, field in home["fields"].items():
            fields[f"home.{key}"] = {
                "status": field["status"] if partner["availability_status"] != "not_open" else "reference_identity_not_current_choice",
                "value": field["value"], "reason": field.get("note") or "母校出國甄選規定；接待校另有條件。",
                "evidence": [{k: field.get(k) for k in ["official_url", "source_pages", "original_excerpt", "academic_year", "application_round", "checked_at"]}],
            }
        for key in ["quota", "language_requirement", "eligibility", "application_deadline", "study_period"]:
            ev = partner.get("field_evidence", {}).get(key)
            fields[f"mother_list.{key}"] = {
                "status": (ev or {}).get("status", "missing"), "value": partner.get(key),
                "reason": (ev or {}).get("note") or partner.get("availability_note") or "母校交換名冊欄位，接待校適用梯次須另核。",
                "evidence": [ev] if ev else [],
            }
        requirements = documents.get(page, {})
        fields["host.document_set_completeness"] = {
            "status": requirements.get("list_completeness", "unverified"),
            "value": len(requirements.get("requirements", [])),
            "reason": "已取得部分文件要求不代表完整當期申請文件集；動態／提名後個人表另核。",
            "evidence": requirements.get("evidence", []),
        }
        asset = assets.get(page, {})
        for key in ["coordinates", "photo"]:
            fields[f"campus.{key}"] = asset.get(key) or {
                "status": "missing", "value": None, "evidence": [],
                "reason": "未取得與本名冊校名、國家、校區相符的座標證據。" if key == "coordinates" else "未取得與校園相符且可用授權明確的照片；不能用官方圖片直接推定可重用。",
            }
        rows.append({
            "ccu_page": page, "school_name": partner["school_name"], "country": partner["country"],
            "availability_status": partner["availability_status"], "quota_status": partner["quota_status"],
            "application_window_status": partner["application_window_status"],
            "academic_year": partner["academic_year"], "application_round": partner["application_round"],
            "identity_source_url": partner["source_url"], "source_pages": partner["source_pages"],
            "fields": fields,
            "gaps": [key for key, field in fields.items() if field["status"] != "verified_current"],
        })
    keys = list(rows[0]["fields"])
    return {
        "checked_at": "2026-10-11", "baseline_commit": BASE_COMMIT,
        "denominators": {
            "exchange_list": len(rows), "published_nonzero_quota": 52, "unknown_quota": 3,
            "published_numeric_positive_quota": 49, "published_unlimited_quota": 3,
            "not_open_reference": 49, "previous_host_field_review": len(overseas),
            "broader_global_agreements": None,
            "global_agreement_note": "官方全球姊妹校頁連至Gamma；公開HTML只回傳應用殼，正常TLS Chromium失敗ERR_CERT_AUTHORITY_INVALID；匿名公開snapshot亦回FORBIDDEN，未嘗試登入或繞過。尚未取得全量內容，不能將104交換校宣稱為全部協議校。",
        },
        "field_counts": {key: dict(Counter(row["fields"][key]["status"] for row in rows)) for key in keys},
        "per_school": rows,
        "limitations": [
            "missing與outside_previous_55_review表示未核實，不表示官方明示尚未公告。",
            "目前所有母校線上與紙本甄選梯次已截止；名冊open表示公布非零交換名額，不代表今日可開始申請。",
            "一般官方生活／校園資料可補為查核日參考；不能升格為2027春季incoming適用政策。",
        ],
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--baseline", action="store_true", help="Write the immutable initial inventory once")
    args = parser.parse_args()
    result = build()
    stem = "completion-baseline" if args.baseline else "completion-inventory"
    path = BUNDLE / (stem + ".json")
    if args.baseline and path.exists():
        raise SystemExit("Baseline exists; preserve the initial denominator and gaps")
    path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    with (BUNDLE / (stem + ".csv")).open("w", encoding="utf-8-sig", newline="") as output:
        writer = csv.writer(output)
        keys = list(result["field_counts"])
        writer.writerow(["ccu_page", "school_name", "country", "availability_status", "quota_status", *keys])
        for row in result["per_school"]:
            writer.writerow([*[row[key] for key in ["ccu_page", "school_name", "country", "availability_status", "quota_status"]], *[row["fields"][key]["status"] for key in keys]])
    print(json.dumps({"denominators": result["denominators"], "field_counts": result["field_counts"], "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
