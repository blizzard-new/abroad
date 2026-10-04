from __future__ import annotations

import json
from pathlib import Path

from exchange_info.models import (
    PartnerUniversity,
    UniversityApplicationWorkflow,
    utc_now,
)
from exchange_info.school_identity import school_identity_key
from exchange_info.storage import data_paths, read_jsonl, write_jsonl
from exchange_info.student_view import (
    CGU_MANAGEMENT_2026_REFERENCE_URL,
    CGU_MANAGEMENT_RENNES_REFERENCE_URL,
    DOUBLE_DEGREE_SOURCE_URL,
    EXCHANGE_SOURCE_URL,
    fetch_partner_universities,
)
from exchange_info.workflow_structuring import (
    structure_application_workflow,
    workflow_structure_issues,
    workflow_structure_summary,
)


ROOT = Path(__file__).resolve().parents[1]
OFFICIAL_DATA = ROOT / "src" / "exchange_info" / "official_data"
NTPU_NAME = "國立臺北大學"
CGU_NAME = "長庚大學"


def main() -> int:
    ntpu_dir = OFFICIAL_DATA / "ntpu"
    cgu_dir = OFFICIAL_DATA / "cgu"
    cgu_dir.mkdir(parents=True, exist_ok=True)

    ntpu = _structured_rows(ntpu_dir / "application_workflows.jsonl", NTPU_NAME)
    local = read_jsonl(
        data_paths()["application_workflows"],
        UniversityApplicationWorkflow,
    )
    cgu = sorted(
        (
            structure_application_workflow(row)
            for row in local
            if row.home_university == CGU_NAME
        ),
        key=lambda row: row.school_name.casefold(),
    )
    if not cgu:
        raise RuntimeError(
            "找不到長庚工作流；請先在 data/processed/application_workflows.jsonl "
            "準備已查核資料。"
        )
    cgu_partners = fetch_partner_universities()
    if not cgu_partners:
        raise RuntimeError(
            "無法讀取長庚目前合作校清單；為避免把舊 workflow 數量誤寫成"
            "目前合作校數，本次不更新 completeness report。"
        )

    write_jsonl(ntpu_dir / "application_workflows.jsonl", ntpu)
    write_jsonl(cgu_dir / "application_workflows.jsonl", cgu)
    _update_ntpu_completeness(ntpu_dir / "catalog-completeness.json", ntpu)
    _write_cgu_completeness(
        cgu_dir / "catalog-completeness.json",
        cgu,
        cgu_partners,
    )

    result = {
        "ntpu": workflow_structure_summary(ntpu),
        "cgu": workflow_structure_summary(cgu),
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if all(not value["structure_issue_count"] for value in result.values()) else 1


def _structured_rows(path: Path, home_university: str) -> list[UniversityApplicationWorkflow]:
    return sorted(
        (
            structure_application_workflow(row)
            for row in read_jsonl(path, UniversityApplicationWorkflow)
            if row.home_university == home_university
        ),
        key=lambda row: row.school_name.casefold(),
    )


def _update_ntpu_completeness(
    path: Path,
    workflows: list[UniversityApplicationWorkflow],
) -> None:
    report = json.loads(path.read_text(encoding="utf-8"))
    workflow_map = {school_identity_key(row.school_name): row for row in workflows}
    for school in report.get("schools", []):
        workflow = workflow_map.get(
            school_identity_key(str(school.get("school_name") or ""))
        )
        school["structured_workflow"] = bool(
            workflow and not workflow_structure_issues(workflow)
        )
    report.setdefault("fields", {})["structured_workflow"] = sum(
        bool(row.get("structured_workflow")) for row in report.get("schools", [])
    )
    report["workflow_structure"] = workflow_structure_summary(workflows)
    path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def _write_cgu_completeness(
    path: Path,
    workflows: list[UniversityApplicationWorkflow],
    current_partners: list[PartnerUniversity],
) -> None:
    workflow_map = {
        school_identity_key(row.school_name): row
        for row in workflows
    }
    partner_map = {
        school_identity_key(row.school_name): row
        for row in current_partners
    }
    matched_keys = workflow_map.keys() & partner_map.keys()
    missing_keys = partner_map.keys() - workflow_map.keys()
    orphan_keys = workflow_map.keys() - partner_map.keys()
    current_statuses = [
        workflow_map[key].coverage_status if key in workflow_map else "not_collected"
        for key in partner_map
    ]
    partner_availability_status = {
        status: sum(
            (partner.availability_status or "open") == status
            for partner in current_partners
        )
        for status in sorted(
            {partner.availability_status or "open" for partner in current_partners}
        )
    }
    report = {
        "home_university": CGU_NAME,
        "partner_count": len(current_partners),
        "partner_count_semantics": (
            "Web 可瀏覽合作校；包含中央當期名單與院級官方參考，"
            "不等同全部可建立正式申請計畫。"
        ),
        "central_current_partner_count": sum(
            (partner.availability_status or "open") == "open"
            for partner in current_partners
        ),
        "departmental_reference_partner_count": sum(
            partner.availability_status == "departmental_reference"
            for partner in current_partners
        ),
        "partner_availability_status": partner_availability_status,
        "workflow_catalog_count": len(workflows),
        "workflow_partner_match_count": len(matched_keys),
        "partners_without_workflow_count": len(missing_keys),
        "workflows_without_visible_partner_count": len(orphan_keys),
        "workflows_without_current_partner_count": len(orphan_keys),
        "partner_list_source_urls": [
            EXCHANGE_SOURCE_URL,
            DOUBLE_DEGREE_SOURCE_URL,
            CGU_MANAGEMENT_2026_REFERENCE_URL,
            CGU_MANAGEMENT_RENNES_REFERENCE_URL,
        ],
        "partner_list_checked_at": utc_now().isoformat().replace("+00:00", "Z"),
        "workflow_structure": workflow_structure_summary(workflows),
        "coverage_status": {
            status: current_statuses.count(status)
            for status in sorted(set(current_statuses))
        },
        "schools": [
            {
                "school_name": partner.school_name,
                "program_type": partner.program_type,
                "availability_status": partner.availability_status,
                "availability_note": partner.availability_note,
                "partner_source_url": partner.source_url,
                "workflow_steps": len(workflow.steps) if workflow else 0,
                "source_count": len(workflow.sources) if workflow else 0,
                "coverage_status": (
                    workflow.coverage_status if workflow else "not_collected"
                ),
                "structured_workflow": bool(
                    workflow and not workflow_structure_issues(workflow)
                ),
            }
            for key, partner in sorted(
                partner_map.items(),
                key=lambda item: item[1].school_name.casefold(),
            )
            for workflow in [workflow_map.get(key)]
        ],
        "workflow_catalog_orphans": [
            {
                "school_name": workflow_map[key].school_name,
                "coverage_status": workflow_map[key].coverage_status,
                "last_checked": (
                    workflow_map[key].last_checked.isoformat().replace("+00:00", "Z")
                    if workflow_map[key].last_checked
                    else None
                ),
            }
            for key in sorted(
                orphan_keys,
                key=lambda item: workflow_map[item].school_name.casefold(),
            )
        ],
    }
    path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    raise SystemExit(main())
