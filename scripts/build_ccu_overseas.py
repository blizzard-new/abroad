"""Validate reviewed CCU overseas evidence and regenerate field-by-field handoff.

Run build_ccu_catalog.py first. This offline audit never promotes unknown years,
blank quotas, historical attachments, or download successes to current facts.
"""

from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from exchange_info.ccu_overseas import LABELS, reviewed_rows
from exchange_info.ccu_sources import BUNDLE, HOME, ROUND
from exchange_info.ccu_student_view import fetch_ccu_partner_universities


def write(name, value):
    (BUNDLE / name).write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n")


def main():
    reviews = reviewed_rows()
    partners = fetch_ccu_partner_universities()
    snapshots = {
        p.stem: json.loads(p.read_text())
        for p in (BUNDLE / "overseas_sources").glob("*.json")
    }
    counts = {key: Counter() for key in LABELS}
    questions, matrix, conflicts = [], [], []
    for partner in partners:
        page = partner.source_pages[0]
        review = reviews.get(page)
        row = {
            "school_name": partner.school_name,
            "home_university": HOME,
            "home_application_round": ROUND,
            "checked_at": "2026-10-08",
            "quota_status": partner.quota_status,
            "availability_status": partner.availability_status,
            "home_fields": {
                k: v.model_dump(mode="json") for k, v in partner.field_evidence.items()
            },
            "overseas_review_status": "not_open_reference_not_prioritized"
            if not review
            else review["review_status"],
            "overseas_fields": {},
            "source_acquisition": [],
        }
        if review:
            row["overseas_review_note"] = review["review_note"]
            row["overseas_fields"] = review["fields"]
            if set(partner.partner_exchange_details) != set(LABELS):
                raise ValueError(
                    "Rebuild catalogue before audit: receiving fields missing"
                )
            row["source_acquisition"] = [
                {
                    k: s[k]
                    for k in [
                        "source_id",
                        "source_url",
                        "status",
                        "access_result",
                        "http_status",
                        "error",
                        "browser_check_error",
                        "content_academic_year",
                        "content_review_note",
                        "checked_at",
                    ]
                    if k in s
                }
                for sid in review["sources"]
                for s in [snapshots[sid]]
            ]
            gaps = []
            for key, field in review["fields"].items():
                counts[key][field["status"]] += 1
                if field["status"] != "verified_current":
                    gaps.append(
                        {
                            "field": key,
                            "label": LABELS[key],
                            "status": field["status"],
                            "question": f"請確認{partner.school_name}中正{ROUND}的{LABELS[key]}，提供明載年度／計畫的官方文件或提名通知。",
                            "reason": field["reason"],
                            "reference_value": field["value"],
                            "evidence": field["evidence"],
                        }
                    )
                if field["status"] == "conflict":
                    conflicts.append(
                        {
                            "school_name": partner.school_name,
                            "ccu_page": page,
                            "field": key,
                            **field,
                        }
                    )
            questions.append(
                {
                    "school_name": partner.school_name,
                    "ccu_page": page,
                    "quota_status": partner.quota_status,
                    "review_note": review["review_note"],
                    "questions": gaps,
                    "source_acquisition": row["source_acquisition"],
                }
            )
        matrix.append(row)
    current_school_count = sum(
        any(f["status"] == "verified_current" for f in r["fields"].values())
        for r in reviews.values()
    )
    overall = Counter(
        f["status"] for r in reviews.values() for f in r["fields"].values()
    )
    report = {
        "home_university": HOME,
        "application_round": ROUND,
        "checked_at": "2026-10-08",
        "catalogue_count": len(partners),
        "reviewed_current_or_unknown_quota_schools": len(reviews),
        "overseas_field_count_per_school": len(LABELS),
        "overseas_field_status_counts": dict(overall),
        "schools_with_at_least_one_current_overseas_fact": current_school_count,
        "schools_with_all_overseas_fields_current": sum(
            all(f["status"] == "verified_current" for f in r["fields"].values())
            for r in reviews.values()
        ),
        "field_counts": {key: dict(value) for key, value in counts.items()},
        "source_count": len(snapshots),
        "source_acquisition_statuses": dict(
            Counter(s["status"] for s in snapshots.values())
        ),
        "source_access_limitations": dict(
            Counter(
                s["access_result"]
                for s in snapshots.values()
                if s.get("access_result")
                in {
                    "challenge_page",
                    "captcha_required",
                    "empty_response",
                    "unrelated_content_anomaly", "password_protected",
                }
            )
        ),
        "semantic_review_ledger": "semantic-review-ledger.json",
        "research_gap_audit": "research-gap-audit.json",
        "acquired_content_review_queue": "acquired-content-review.json",
        "source_failure_followup": "source-failure-followup.json",
        "definition": "只計內容、年度及計畫已核實之欄位；下載成功、一般現行未標年網頁、灰字、舊年度及只載提名前提不算當期完整。",
        "remaining_work": "缺值及已取得未映射段落繼續查官方替代來源；逐欄進度見research-gap-audit.json。矛盾／個別通知另見confirmation-questions.json，不把整體缺值當作承辦阻塞。未聯絡學校或登入校方帳號。新版未核實不等同官方尚未公告。",
    }
    write("field-completeness-matrix.json", matrix)
    write("confirmation-questions.json", questions)
    write("overseas-conflicts.json", conflicts)
    write("overseas-completeness.json", report)
    print(json.dumps(report, ensure_ascii=False))


if __name__ == "__main__":
    main()
