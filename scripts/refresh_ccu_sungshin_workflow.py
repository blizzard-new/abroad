"""Refresh only the source-reviewed CCU/Sungshin published workflow row."""
from __future__ import annotations

from exchange_info.ccu_sources import BUNDLE
from exchange_info.ccu_student_view import (
    build_ccu_workflow,
    fetch_ccu_partner_universities,
)
from exchange_info.models import UniversityApplicationWorkflow
from exchange_info.workflow_structuring import (
    structure_application_workflow,
    workflow_structure_issues,
)


def main():
    partner = next(row for row in fetch_ccu_partner_universities() if row.source_pages == [49])
    current = structure_application_workflow(build_ccu_workflow(partner))
    if issues := workflow_structure_issues(current):
        raise ValueError(f"Sungshin workflow structure failed: {issues}")
    path = BUNDLE / "application_workflows.jsonl"
    lines = path.read_text().splitlines(keepends=True)
    matches = [i for i, line in enumerate(lines)
               if UniversityApplicationWorkflow.model_validate_json(line).workflow_id == current.workflow_id]
    if len(matches) != 1:
        raise ValueError("Expected exactly one existing Sungshin workflow")
    index = matches[0]
    old = UniversityApplicationWorkflow.model_validate_json(lines[index])
    if old.model_dump(mode="json") != current.model_dump(mode="json"):
        lines[index] = current.model_dump_json() + "\n"
        path.write_text("".join(lines))
    print(f"CCU/Sungshin refreshed; {len(lines) - 1} other workflow rows preserved byte-for-byte")


if __name__ == "__main__":
    main()
