from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass

from exchange_info.application_workflow_collector import collect_application_workflow
from exchange_info.experience_collector import normalize_school
from exchange_info.models import (
    CollectionAudit,
    DestinationProfile,
    PartnerUniversity,
    UniversityApplicationWorkflow,
    utc_now,
)
from exchange_info.ntpu_student_view import fetch_ntpu_partner_universities
from exchange_info.partner_research import (
    apply_partner_research,
    collect_destination_profile,
)
from exchange_info.storage import (
    load_application_workflows,
    load_destination_profiles,
    load_partner_research,
    replace_application_workflow,
    upsert_collection_audit,
    upsert_destination_profile,
)


NTPU_NAME = "國立臺北大學"


@dataclass
class ResearchResult:
    partner: PartnerUniversity
    workflow: UniversityApplicationWorkflow | None = None
    destination: DestinationProfile | None = None
    workflow_error: str | None = None
    destination_error: str | None = None


def _research_partner(
    partner: PartnerUniversity,
    *,
    need_workflow: bool,
    need_destination: bool,
    max_pages: int,
    timeout_seconds: float,
) -> ResearchResult:
    result = ResearchResult(partner=partner)
    if need_workflow:
        try:
            result.workflow = collect_application_workflow(
                partner,
                home_university=NTPU_NAME,
                max_partner_pages=max_pages,
                timeout_seconds=timeout_seconds,
                rate_limit_seconds=0.0,
            )
        except Exception as exc:  # keep the resumable batch moving
            result.workflow_error = str(exc)[:500]
    if need_destination:
        try:
            result.destination = collect_destination_profile(
                partner,
                max_pages=max_pages,
                timeout_seconds=timeout_seconds,
            )
        except Exception as exc:  # keep the resumable batch moving
            result.destination_error = str(exc)[:500]
    return result


def _save_result(result: ResearchResult) -> None:
    partner = result.partner
    if result.workflow is not None:
        replace_application_workflow(result.workflow)
        upsert_collection_audit(
            CollectionAudit(
                school_name=partner.school_name,
                collector="workflows",
                status=result.workflow.coverage_status,
                home_university=NTPU_NAME,
                result_count=len(result.workflow.steps),
                note=result.workflow.coverage_note,
                checked_at=result.workflow.last_checked,
            )
        )
    elif result.workflow_error:
        upsert_collection_audit(
            CollectionAudit(
                school_name=partner.school_name,
                collector="workflows",
                status="error",
                home_university=NTPU_NAME,
                note=result.workflow_error,
            )
        )

    if result.destination is not None:
        upsert_destination_profile(result.destination)
        upsert_collection_audit(
            CollectionAudit(
                school_name=partner.school_name,
                collector="destinations",
                status=result.destination.coverage_status,
                home_university=NTPU_NAME,
                result_count=len(result.destination.sources),
                note=result.destination.coverage_note,
                checked_at=result.destination.last_checked or utc_now(),
            )
        )
    elif result.destination_error:
        upsert_collection_audit(
            CollectionAudit(
                school_name=partner.school_name,
                collector="destinations",
                status="error",
                home_university=NTPU_NAME,
                note=result.destination_error,
            )
        )


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Resumably complete NTPU partner workflows and destination details."
    )
    parser.add_argument("--workers", type=int, default=6)
    parser.add_argument("--max-pages", type=int, default=3)
    parser.add_argument("--timeout", type=float, default=12.0)
    parser.add_argument("--refresh", action="store_true")
    args = parser.parse_args()

    partners = apply_partner_research(
        fetch_ntpu_partner_universities(),
        load_partner_research(),
        home_university=NTPU_NAME,
    )
    existing_workflows = {
        normalize_school(row.school_name)
        for row in load_application_workflows()
        if row.home_university == NTPU_NAME
    }
    partner_keys = {normalize_school(row.school_name) for row in partners}
    existing_destinations = {
        normalize_school(row.school_name)
        for row in load_destination_profiles()
        if normalize_school(row.school_name) in partner_keys
    }
    jobs = []
    for partner in partners:
        key = normalize_school(partner.school_name)
        need_workflow = args.refresh or key not in existing_workflows
        need_destination = args.refresh or key not in existing_destinations
        if need_workflow or need_destination:
            jobs.append((partner, need_workflow, need_destination))

    if not jobs:
        print("NTPU catalog already has a workflow and destination record for all schools.")
        return 0

    print(f"Researching {len(jobs)} incomplete NTPU schools with {args.workers} workers.")
    completed = 0
    failures = 0
    with ThreadPoolExecutor(max_workers=max(1, args.workers)) as executor:
        futures = {
            executor.submit(
                _research_partner,
                partner,
                need_workflow=need_workflow,
                need_destination=need_destination,
                max_pages=max(1, args.max_pages),
                timeout_seconds=max(4.0, args.timeout),
            ): partner.school_name
            for partner, need_workflow, need_destination in jobs
        }
        for future in as_completed(futures):
            result = future.result()
            _save_result(result)
            completed += 1
            if result.workflow_error or result.destination_error:
                failures += 1
            workflow_status = (
                result.workflow.coverage_status
                if result.workflow
                else "kept"
                if not result.workflow_error
                else "error"
            )
            destination_status = (
                result.destination.coverage_status
                if result.destination
                else "kept"
                if not result.destination_error
                else "error"
            )
            print(
                f"[{completed}/{len(jobs)}] {result.partner.school_name}: "
                f"workflow={workflow_status}, destination={destination_status}"
            )

    print(f"Completed {completed} schools; {failures} had at least one failed stage.")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
