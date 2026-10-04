from __future__ import annotations

import argparse
import json
from pathlib import Path

from exchange_info.models import UniversityApplicationWorkflow
from exchange_info.storage import read_jsonl, write_jsonl
from exchange_info.workflow_structuring import (
    clear_derived_source_applicability,
    workflow_structure_summary,
)


ROOT = Path(__file__).resolve().parents[1]
OFFICIAL_DATA = ROOT / "src" / "exchange_info" / "official_data"
BUNDLE_PATHS = (
    OFFICIAL_DATA / "ntpu" / "application_workflows.jsonl",
    OFFICIAL_DATA / "cgu" / "application_workflows.jsonl",
)


def process_bundle(path: Path, *, apply: bool) -> dict[str, object]:
    workflows = read_jsonl(path, UniversityApplicationWorkflow)
    cleaned: list[UniversityApplicationWorkflow] = []
    cleared_source_count = 0
    changed_workflow_count = 0
    for workflow in workflows:
        updated, cleared = clear_derived_source_applicability(workflow)
        cleaned.append(updated)
        cleared_source_count += cleared
        changed_workflow_count += bool(cleared)

    if apply and cleared_source_count:
        write_jsonl(path, cleaned)
        completeness_path = path.with_name("catalog-completeness.json")
        if completeness_path.exists():
            report = json.loads(completeness_path.read_text(encoding="utf-8"))
            report["workflow_structure"] = workflow_structure_summary(cleaned)
            completeness_path.write_text(
                json.dumps(report, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )

    return {
        "path": str(path.relative_to(ROOT)),
        "workflow_count": len(workflows),
        "changed_workflow_count": changed_workflow_count,
        "cleared_source_count": cleared_source_count,
        "applied": apply,
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Remove source applicability values derived before the formal "
            "source-by-source review trail. Dry-run unless --apply is supplied."
        )
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="rewrite tracked workflow bundles and their completeness summaries",
    )
    args = parser.parse_args()
    result = [process_bundle(path, apply=args.apply) for path in BUNDLE_PATHS]
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
