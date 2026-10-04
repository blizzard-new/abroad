from __future__ import annotations

import json
from pathlib import Path

from exchange_info.experience_collector import normalize_school
from exchange_info.ntpu_student_view import fetch_ntpu_partner_universities
from exchange_info.partner_research import apply_partner_research
from exchange_info.school_identity import school_identity_key
from exchange_info.storage import (
    load_application_workflows,
    load_destination_profiles,
    load_partner_research,
    write_jsonl,
)
from exchange_info.workflow_structuring import (
    structure_application_workflow,
    workflow_structure_issues,
    workflow_structure_summary,
)


NTPU_NAME = "國立臺北大學"
BUNDLE_DIR = (
    Path(__file__).resolve().parents[1]
    / "src"
    / "exchange_info"
    / "official_data"
    / "ntpu"
)
IMAGE_MANIFEST = (
    Path(__file__).resolve().parents[1]
    / "src"
    / "exchange_info"
    / "static"
    / "assets"
    / "school-images.json"
)


def main() -> int:
    BUNDLE_DIR.mkdir(parents=True, exist_ok=True)
    research = [
        row for row in load_partner_research() if row.home_university == NTPU_NAME
    ]
    partners = apply_partner_research(
        fetch_ntpu_partner_universities(), research, home_university=NTPU_NAME
    )
    partner_names = {normalize_school(row.school_name) for row in partners}
    partner_identities = {school_identity_key(row.school_name) for row in partners}
    workflows = [
        structure_application_workflow(row)
        for row in load_application_workflows()
        if row.home_university == NTPU_NAME
        and normalize_school(row.school_name) in partner_names
    ]
    destinations = [
        row.model_copy(update={"home_university": NTPU_NAME})
        for row in load_destination_profiles()
        if normalize_school(row.home_university or "長庚大學")
        == normalize_school(NTPU_NAME)
        if school_identity_key(row.school_name) in partner_identities
    ]

    write_jsonl(BUNDLE_DIR / "partner_research.jsonl", research)
    write_jsonl(BUNDLE_DIR / "application_workflows.jsonl", workflows)
    write_jsonl(BUNDLE_DIR / "destination_profiles.jsonl", destinations)

    images = json.loads(IMAGE_MANIFEST.read_text(encoding="utf-8"))
    image_rows = images.get("schools", images) if isinstance(images, dict) else images
    image_map = {
        school_identity_key(str(row.get("school_name") or "")): row
        for row in image_rows
        if isinstance(row, dict)
    }
    workflow_map = {school_identity_key(row.school_name): row for row in workflows}
    destination_map = {
        school_identity_key(row.school_name): row for row in destinations
    }
    rows = []
    for partner in partners:
        key = school_identity_key(partner.school_name)
        workflow = workflow_map.get(key)
        destination = destination_map.get(key)
        image = image_map.get(key)
        rows.append(
            {
                "school_name": partner.school_name,
                "availability_status": partner.availability_status,
                "official_website": bool(partner.website),
                "image_status": str((image or {}).get("status") or "not_collected"),
                "language_and_eligibility": bool(partner.eligibility),
                "academic_restrictions": bool(
                    partner.colleges and partner.degree_levels
                ),
                "quota": bool(partner.quota),
                "study_period": bool(partner.study_period),
                "ranking": bool(
                    partner.ranking_info and partner.ranking_source_url
                ),
                "workflow_steps": len(workflow.steps) if workflow else 0,
                "structured_workflow": bool(
                    workflow and not workflow_structure_issues(workflow)
                ),
                "housing": bool(destination and destination.housing_summary),
                "cost": bool(destination and destination.cost_summary),
                "transport": bool(destination and destination.transport_summary),
                "campus_life": bool(
                    destination and destination.campus_life_summary
                ),
                "destination_source_count": len(destination.sources)
                if destination
                else 0,
            }
        )
    summary = {
        "home_university": NTPU_NAME,
        "partner_count": len(partners),
        "open_count": sum(
            row.availability_status == "open" for row in partners
        ),
        "agreement_only_count": sum(
            row.availability_status == "agreement_only" for row in partners
        ),
        "fields": {
            field: sum(bool(row[field]) for row in rows)
            for field in (
                "official_website",
                "language_and_eligibility",
                "academic_restrictions",
                "quota",
                "study_period",
                "ranking",
                "housing",
                "cost",
                "transport",
                "campus_life",
                "structured_workflow",
            )
        },
        "verified_image_count": sum(
            row["image_status"] == "verified" for row in rows
        ),
        "workflow_count": sum(row["workflow_steps"] > 0 for row in rows),
        "workflow_structure": workflow_structure_summary(workflows),
        "destination_count": sum(
            row["housing"] and row["cost"] for row in rows
        ),
        "schools": rows,
    }
    (BUNDLE_DIR / "catalog-completeness.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({key: value for key, value in summary.items() if key != "schools"}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
