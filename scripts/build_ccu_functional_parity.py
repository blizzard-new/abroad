"""Compare real bundled/runtime CGU capabilities with the CCU evidence matrix.

Read-only local API calls; no collection, authentication or workflow publication.
Nonempty output is a rendering check, not verified-current policy coverage.
"""

from __future__ import annotations

import argparse
import json
import sys
import tempfile
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from fastapi.testclient import TestClient

from exchange_info.api import create_app
from exchange_info.ccu_sources import BUNDLE, HOME
from exchange_info.qualification_scopes import (
    college_scope_needs_confirmation,
    degree_scope_needs_confirmation,
)


def load_jsonl(path):
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def current_field(field):
    return {
        "status": field["status"],
        "value": field["value"],
        "reason": field["reason"],
        "evidence": field["evidence"],
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output", type=Path, default=BUNDLE / "functional-parity.json"
    )
    args = parser.parse_args()
    profile_reviews = {
        r["ccu_page"]: r
        for r in json.loads((BUNDLE / "profile-reviewed-fields.json").read_text())
    }
    overseas = {
        r["ccu_page"]: r
        for r in json.loads((BUNDLE / "overseas-reviewed-fields.json").read_text())
    }
    documents = {
        r["ccu_page"]: r
        for r in json.loads((BUNDLE / "partner-document-requirements.json").read_text())
    }
    cgu_bundle = BUNDLE.parent / "cgu"
    raw_cgu = load_jsonl(cgu_bundle / "application_workflows.jsonl")
    raw_ccu = load_jsonl(BUNDLE / "application_workflows.jsonl")
    report = {
        "checked_at": datetime.now(UTC).isoformat(),
        "definition": "逐校讀取本機公開API。nonempty是呈現／功能覆蓋，不等於當期規定完整；每個中正欄位另存來源、年度與查核狀態。",
        "baseline": {
            "cgu_raw_workflows": len(raw_cgu),
            "cgu_raw_review_statuses": dict(
                Counter(r["review_status"] for r in raw_cgu)
            ),
            "ccu_raw_workflows": len(raw_ccu),
            "ccu_raw_review_statuses": dict(
                Counter(r["review_status"] for r in raw_ccu)
            ),
            "cgu_year_scope_note": "CGU原始published為115、legacy為116；無年度API選取與指定115已發布基準分開量測，不改原資料。",
        },
        "runtime": {},
        "home_outbound_rules": json.loads((BUNDLE / "home-rules.json").read_text()),
        "ccu_per_school": [],
    }
    with (
        tempfile.TemporaryDirectory(prefix="ccu-functional-parity-") as temporary,
        TestClient(create_app(Path(temporary))) as client,
    ):
        for home, code in [("長庚大學", "cgu"), (HOME, "ccu")]:
            response = client.get("/student-dashboard", params={"school": home})
            response.raise_for_status()
            dashboard = response.json()
            response = client.get("/destination-profiles", params={"home_school": home})
            response.raise_for_status()
            guides = {r["school_name"]: r for r in response.json()}
            partners = {r["school_name"]: r for r in dashboard["partner_universities"]}
            assert len(guides) == (77 if code == "cgu" else 55)
            aggregate = {
                "dashboard_partner_count": len(partners),
                "destination_profile_count": len(guides),
                "preferred_workflow_statuses": Counter(),
                "cgu_explicit_115_workflow_statuses": Counter(),
                "workflow_http_ok": 0,
                "guide_nonempty": Counter(),
                "partner_nonempty": Counter(),
                "structured_scope_known": Counter(),
                "documents": Counter(),
                "workflow_rows": [],
            }
            for index, (name, guide) in enumerate(guides.items(), 1):
                partner = partners[name]
                response = client.get(
                    "/application-workflow",
                    params={"home_school": home, "school": name},
                )
                response.raise_for_status()
                flow = response.json()
                aggregate["workflow_http_ok"] += 1
                aggregate["preferred_workflow_statuses"][flow["review_status"]] += 1
                if code == "cgu":
                    response = client.get(
                        "/application-workflow",
                        params={
                            "home_school": home,
                            "school": name,
                            "academic_year": "115",
                        },
                    )
                    response.raise_for_status()
                    aggregate["cgu_explicit_115_workflow_statuses"][
                        response.json()["review_status"]
                    ] += 1
                for key in [
                    "city",
                    "housing_summary",
                    "cost_summary",
                    "transport_summary",
                    "campus_life_summary",
                    "guide_photos",
                    "first_72_hours",
                    "packing_from_taiwan",
                    "buy_after_arrival",
                ]:
                    aggregate["guide_nonempty"][key] += bool(guide.get(key))
                for key in ["website", "location", "colleges", "degree_levels"]:
                    aggregate["partner_nonempty"][key] += bool(partner.get(key))
                aggregate["partner_nonempty"]["location_with_city"] += bool(
                    (partner.get("location") or {}).get("city")
                )
                aggregate["partner_nonempty"]["location_with_source"] += bool(
                    (partner.get("location") or {}).get("source_url")
                )
                aggregate["structured_scope_known"]["colleges"] += bool(
                    partner.get("colleges")
                ) and not college_scope_needs_confirmation(partner["colleges"])
                aggregate["structured_scope_known"]["degree_levels"] += bool(
                    partner.get("degree_levels")
                ) and not degree_scope_needs_confirmation(partner["degree_levels"])
                req = [
                    r for step in flow["steps"] for r in step["document_requirements"]
                ]
                aggregate["documents"]["requirements"] += len(req)
                aggregate["documents"]["requirements_with_form"] += sum(
                    bool(r["official_form_url"]) for r in req
                )
                aggregate["documents"]["schools_with_requirements"] += bool(req)
                aggregate["documents"]["schools_with_signature_detail"] += any(
                    r["signatures"] or r["stamps"] for r in req
                )
                aggregate["workflow_rows"].append(
                    {
                        "school_name": name,
                        "review_status": flow["review_status"],
                        "step_count": len(flow["steps"]),
                        "requirement_count": len(req),
                    }
                )
                if code == "ccu":
                    page = partner["source_pages"][0]
                    response = client.get(
                        "/school-data-completeness",
                        params={"home_school": home, "school": name},
                    )
                    response.raise_for_status()
                    complete = response.json()
                    response = client.get(
                        "/school-life-context",
                        params={"home_school": home, "school": name},
                    )
                    response.raise_for_status()
                    life_context = response.json()
                    home_fields = {
                        k: partner["field_evidence"][k]
                        for k in [
                            "quota",
                            "eligibility",
                            "language_requirement",
                            "application_deadline",
                            "partner_documents",
                        ]
                        if k in partner["field_evidence"]
                    }
                    doc = documents.get(page)
                    report["ccu_per_school"].append(
                        {
                            "ccu_page": page,
                            "school_name": name,
                            "quota_status": partner["quota_status"],
                            "availability_status": partner["availability_status"],
                            "application_window_status": partner[
                                "application_window_status"
                            ],
                            "home_outbound_rules_ref": "home_outbound_rules",
                            "mother_document_partner_fields": home_fields,
                            "scope_note": "母校逐校表的eligibility/language仍是外校接收條件；CCU outbound GPA、年級、兩年證明、校內期限另見home_outbound_rules及校內步驟。",
                            "host_fields": {
                                k: current_field(f)
                                for k, f in overseas[page]["fields"].items()
                            },
                            "profile_fields": profile_reviews[page]["fields"],
                            "academic_filter_scope": {
                                "colleges_known": bool(partner.get("colleges"))
                                and not college_scope_needs_confirmation(
                                    partner["colleges"]
                                ),
                                "degree_levels_known": bool(
                                    partner.get("degree_levels")
                                )
                                and not degree_scope_needs_confirmation(
                                    partner["degree_levels"]
                                ),
                            },
                            "documents": {
                                "home_individual_requirements": len(
                                    flow["steps"][2]["document_requirements"]
                                ),
                                "mother_per_school_notes_retained": bool(
                                    flow["steps"][3]["details"]
                                ),
                                "host_individual_requirements": len(doc["requirements"])
                                if doc
                                else 0,
                                "host_stages": dict(
                                    Counter(r["stage"] for r in doc["requirements"])
                                )
                                if doc
                                else {},
                                "host_list_completeness": doc["list_completeness"]
                                if doc
                                else "unverified",
                                "requirements": doc["requirements"] if doc else [],
                            },
                            "runtime": {
                                "workflow_http": 200,
                                "guide_present": True,
                                "review_status": flow["review_status"],
                                "step_count": len(flow["steps"]),
                                "guide_section_keys": [
                                    s["key"] for s in guide["student_guide_sections"]
                                ],
                                "completeness_items": complete["items"],
                                "city": guide["city"],
                                "transport_present": bool(guide["transport_summary"]),
                                "campus_life_present": bool(
                                    guide["campus_life_summary"]
                                ),
                                "life_location_note": life_context["location_note"],
                                "life_categories": life_context["categories"],
                            },
                        }
                    )
                if index % 10 == 0:
                    print(
                        f"{code}: checked {index}/{len(guides)} runtime workflows",
                        flush=True,
                    )
            report["runtime"][code] = aggregate
    assert len(report["ccu_per_school"]) == 55
    assert report["runtime"]["cgu"]["cgu_explicit_115_workflow_statuses"] == {
        "published": 77
    }
    report["status_summary"] = {
        "host_17_fields": dict(
            Counter(
                f["status"] for r in overseas.values() for f in r["fields"].values()
            )
        ),
        "profile_7_fields": {
            k: dict(Counter(r["fields"][k]["status"] for r in profile_reviews.values()))
            for k in next(iter(profile_reviews.values()))["fields"]
        },
        "complete_host_application_sets": 0,
        "complete_17_field_schools": sum(
            all(f["status"] == "verified_current" for f in r["fields"].values())
            for r in overseas.values()
        ),
        "functional_parity_complete": False,
        "remaining_public_research": "公開交通／生活、學院／學制及政策年度仍有缺口。另有登入／提名後個人表、反爬、矛盾與Taiwan適用範圍未明；各校清單保留真實缺值，不把缺資料都當作只能聯絡學校。",
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print(
        json.dumps(
            {
                "output": str(args.output),
                "baseline": report["baseline"],
                "runtime": {
                    code: {k: v for k, v in row.items() if k != "workflow_rows"}
                    for code, row in report["runtime"].items()
                },
                "status_summary": report["status_summary"],
            },
            ensure_ascii=False,
        ),
        flush=True,
    )


if __name__ == "__main__":
    main()
