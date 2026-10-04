from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

from .application_workflow_collector import collect_application_workflow
from .ai_gateway import ai_enabled
from .cleaner import process_pages
from .content_governance import (
    create_content_governance_store,
    stage_workflow_refresh,
)
from .document_vault import create_document_vault_service
from .destination_profile_review import create_destination_profile_review_store
from .crawler import CguOiaCrawler, CrawlerConfig
from .experience_collector import (
    collect_student_experiences,
    merge_refreshed_student_experiences,
    normalize_school,
)
from .extractor import build_exchange_info
from .models import CollectionAudit, ProcessedPage, utc_now
from .notifications import NotificationService, email_sender_from_env
from .ntpu_student_view import fetch_ntpu_partner_universities
from .partner_research import (
    apply_partner_research,
    collect_destination_profile,
    discover_partner_official_site,
    enrich_partner_ranking,
)
from .release_readiness import build_web_release_readiness
from .rag import build_rag_index
from .repositories import create_account_repository
from .school_image_collector import (
    DEFAULT_IMAGE_MANIFEST,
    DEFAULT_IMAGE_OUTPUT_DIR,
    collect_school_images,
)
from .settings import CGU_START_URL, DEFAULT_DATA_DIR
from .storage import (
    ensure_data_dirs,
    load_collection_audits,
    load_application_workflows,
    load_destination_profiles,
    load_partner_research,
    load_student_experiences,
    load_raw_pages,
    load_processed_pages,
    replace_school_experiences,
    save_exchange_info,
    save_processed_pages,
    save_raw_pages,
    upsert_collection_audit,
    upsert_destination_profile,
    upsert_partner_research,
)
from .structured_sources import build_structured_source_index
from .student_view import fetch_partner_universities
from .university_registry import CGU, NTPU, require_university


def main(argv: list[str] | None = None) -> int:
    _configure_console_encoding()
    parser = argparse.ArgumentParser(
        prog="exchange-info",
        description="Crawl and serve public exchange application information.",
    )
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=DEFAULT_DATA_DIR,
        help="Data directory. Defaults to ./data in this project.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    crawl_parser = subparsers.add_parser("crawl", help="Crawl CGU OIA and build processed outputs.")
    crawl_parser.add_argument("--start-url", default=CGU_START_URL)
    crawl_parser.add_argument("--max-pages", type=int, default=60)
    crawl_parser.add_argument("--rate-limit", type=float, default=1.0)
    crawl_parser.add_argument("--timeout", type=float, default=20.0)
    crawl_parser.add_argument("--use-playwright", action="store_true")
    crawl_parser.add_argument(
        "--rules-only",
        action="store_true",
        help="Skip AI source extraction and embeddings even when an API key is configured.",
    )
    crawl_parser.set_defaults(func=cmd_crawl)

    build_parser = subparsers.add_parser(
        "build-index", help="Build processed files from data/raw/pages.jsonl."
    )
    build_parser.add_argument("--rules-only", action="store_true")
    build_parser.set_defaults(func=cmd_build_index)

    ai_index_parser = subparsers.add_parser(
        "build-ai-index",
        help="Rebuild structured source records and the RAG document index.",
    )
    ai_index_parser.add_argument("--rules-only", action="store_true")
    ai_index_parser.set_defaults(func=cmd_build_ai_index)

    experience_parser = subparsers.add_parser(
        "collect-experiences",
        help="Collect public student articles and videos for a supported home university's partners.",
    )
    experience_parser.add_argument(
        "--school",
        action="append",
        default=[],
        help="Exact partner-school name. Repeat to collect more than one school.",
    )
    experience_parser.add_argument("--max-schools", type=int, default=1)
    experience_parser.add_argument("--max-sources", type=int, default=12)
    experience_parser.add_argument("--school-delay", type=float, default=1.0)
    experience_parser.add_argument("--refresh", action="store_true")
    experience_parser.add_argument("--home-school", default="長庚大學")
    experience_parser.set_defaults(func=cmd_collect_experiences)

    workflow_parser = subparsers.add_parser(
        "collect-workflows",
        help="Collect official application workflows for a supported home university's partners.",
    )
    workflow_parser.add_argument(
        "--school",
        action="append",
        default=[],
        help="Exact partner-school name. Repeat to collect more than one school.",
    )
    workflow_parser.add_argument("--max-schools", type=int, default=1)
    workflow_parser.add_argument("--school-delay", type=float, default=1.0)
    workflow_parser.add_argument("--refresh", action="store_true")
    workflow_parser.add_argument("--home-school", default="長庚大學")
    workflow_parser.set_defaults(func=cmd_collect_workflows)

    research_parser = subparsers.add_parser(
        "research-partners",
        help="Research official sites, workflows, living information, and experiences for partner universities.",
    )
    research_parser.add_argument("--home-school", default="長庚大學")
    research_parser.add_argument("--school", action="append", default=[])
    research_parser.add_argument("--max-schools", type=int, default=1)
    research_parser.add_argument("--max-sources", type=int, default=12)
    research_parser.add_argument("--school-delay", type=float, default=1.0)
    research_parser.add_argument("--refresh", action="store_true")
    research_parser.add_argument(
        "--site-only",
        action="store_true",
        help="Only verify the official website and comparable ranking status.",
    )
    research_parser.set_defaults(func=cmd_research_partners)

    notification_parser = subparsers.add_parser(
        "run-notifications",
        help="Create due Web reminders and dispatch opted-in Email reminders.",
    )
    notification_parser.set_defaults(func=cmd_run_notifications)

    release_audit_parser = subparsers.add_parser(
        "audit-web-release",
        help="Read workflows and destination profiles, then fail closed while any Web release blocker remains.",
    )
    release_audit_parser.set_defaults(func=cmd_audit_web_release)

    completeness_parser = subparsers.add_parser(
        "audit-data-completeness",
        help="Report which public facts are still missing per partner school; reads stored data only.",
    )
    completeness_parser.add_argument("--csv", type=Path, help="Also write one row per school to this CSV file.")
    completeness_parser.set_defaults(func=cmd_audit_data_completeness)

    task_documents_parser = subparsers.add_parser(
        "audit-task-documents",
        help="Report which official steps open a preparation tool and which only list required documents.",
    )
    task_documents_parser.set_defaults(func=cmd_audit_task_documents)

    vault_cleanup_parser = subparsers.add_parser(
        "cleanup-document-vault",
        help="Permanently remove expired encrypted versions and orphaned vault objects.",
    )
    vault_cleanup_parser.set_defaults(func=cmd_cleanup_document_vault)

    analytics_parser = subparsers.add_parser(
        "analytics-report",
        help="Print a text summary of the anonymous usage analytics (the dashboard shows the full report).",
    )
    analytics_parser.add_argument("--days", type=int, default=30, help="Window length in Taipei days, ending today.")
    analytics_parser.add_argument("--include-bots", action="store_true", help="Count automated traffic too.")
    analytics_parser.add_argument("--json", action="store_true", help="Print the whole report as JSON instead.")
    analytics_parser.set_defaults(func=cmd_analytics_report)

    analytics_purge_parser = subparsers.add_parser(
        "purge-analytics",
        help="Delete analytics rows older than the given number of days (minimum 30).",
    )
    analytics_purge_parser.add_argument("--days", type=int, required=True)
    analytics_purge_parser.set_defaults(func=cmd_purge_analytics)

    args = parser.parse_args(argv)
    return args.func(args)


def _configure_console_encoding() -> None:
    """Keep international university names printable on Windows consoles."""
    for stream_name in ("stdout", "stderr"):
        stream = getattr(sys, stream_name, None)
        reconfigure = getattr(stream, "reconfigure", None)
        if not callable(reconfigure):
            continue
        try:
            reconfigure(encoding="utf-8", errors="replace")
        except (OSError, TypeError, ValueError):
            pass


def cmd_crawl(args: argparse.Namespace) -> int:
    ensure_data_dirs(args.data_dir)
    config = CrawlerConfig(
        start_url=args.start_url,
        max_pages=args.max_pages,
        rate_limit_seconds=args.rate_limit,
        timeout_seconds=args.timeout,
        use_playwright=args.use_playwright,
        data_dir=args.data_dir,
    )
    crawler = CguOiaCrawler(config)
    raw_pages = crawler.crawl()
    save_raw_pages(raw_pages, args.data_dir)
    processed_pages = process_pages(raw_pages)
    save_processed_pages(processed_pages, args.data_dir)
    info = build_exchange_info(processed_pages)
    save_exchange_info(info, args.data_dir)
    _build_ai_indexes(processed_pages, args.data_dir, rules_only=args.rules_only)
    print(f"Crawled {len(raw_pages)} pages.")
    print(f"Wrote {args.data_dir / 'raw' / 'pages.jsonl'}")
    print(f"Wrote {args.data_dir / 'processed' / 'pages.jsonl'}")
    print(f"Wrote {args.data_dir / 'processed' / 'exchange_info.json'}")
    return 0


def cmd_build_index(args: argparse.Namespace) -> int:
    ensure_data_dirs(args.data_dir)
    raw_pages = load_raw_pages(args.data_dir)
    processed_pages = process_pages(raw_pages)
    save_processed_pages(processed_pages, args.data_dir)
    info = build_exchange_info(processed_pages)
    save_exchange_info(info, args.data_dir)
    _build_ai_indexes(processed_pages, args.data_dir, rules_only=args.rules_only)
    print(f"Processed {len(processed_pages)} pages.")
    print(f"Wrote {args.data_dir / 'processed' / 'pages.jsonl'}")
    print(f"Wrote {args.data_dir / 'processed' / 'exchange_info.json'}")
    return 0


def cmd_build_ai_index(args: argparse.Namespace) -> int:
    ensure_data_dirs(args.data_dir)
    pages = load_processed_pages(args.data_dir)
    if not pages:
        print("No processed pages found. Run crawl or build-index first.")
        return 2
    _build_ai_indexes(pages, args.data_dir, rules_only=args.rules_only)
    return 0


def cmd_run_notifications(args: argparse.Namespace) -> int:
    repository = create_account_repository(args.data_dir)
    service = NotificationService(
        repository,
        email_sender=email_sender_from_env(),
        content_store=create_content_governance_store(args.data_dir),
    )
    result = service.run_due()
    print(result.model_dump_json())
    return 0


def cmd_audit_web_release(args: argparse.Namespace) -> int:
    report = build_web_release_readiness(
        create_content_governance_store(args.data_dir),
        load_destination_profiles(
            args.data_dir,
            include_bundled_baseline=True,
        ),
        create_destination_profile_review_store(args.data_dir),
    )
    print(report.model_dump_json())
    return 0 if report.release_ready else 2


def cmd_audit_task_documents(args: argparse.Namespace) -> int:
    import json

    from .storage import load_application_workflows
    from .task_documents import audit_task_document_links

    report = audit_task_document_links(load_application_workflows(args.data_dir))
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


def cmd_audit_data_completeness(args: argparse.Namespace) -> int:
    import csv
    import json
    from collections import Counter

    from .application_rules import select_application_workflow
    from .models import ApplicationRuleContext, PartnerUniversity
    from .ntpu_student_view import fetch_ntpu_partner_universities
    from .school_completeness import build_school_completeness
    from .school_content import complete_destination_profile
    from .school_identity import school_identity_key
    from .storage import load_application_workflows
    from .university_registry import NTPU as NTPU_PROFILE

    workflows = load_application_workflows(args.data_dir)
    profiles = load_destination_profiles(args.data_dir, include_bundled_baseline=True)
    # CGU's partner list is a live crawl, so this offline audit covers it through the
    # stored destination profiles; NTPU's list is read from the bundled official PDFs.
    homes = {
        CGU.school_name: [],
        NTPU_PROFILE.school_name: fetch_ntpu_partner_universities(),
    }
    rows: list[dict[str, str]] = []
    totals: Counter[tuple[str, str]] = Counter()
    schools = 0
    for home, partners in homes.items():
        known = {school_identity_key(row.school_name) for row in partners}
        partners = list(partners) + [
            PartnerUniversity(program_type="交換", school_name=row.school_name, country=row.country, source_url="")
            for row in profiles
            if normalize_school(row.home_university or "") == normalize_school(home)
            and school_identity_key(row.school_name) not in known
        ]
        scoped = [row for row in workflows if normalize_school(row.home_university) == normalize_school(home)]
        for partner in partners:
            profile = next((row for row in profiles if school_identity_key(row.school_name) == school_identity_key(partner.school_name)
                            and normalize_school(row.home_university or home) == normalize_school(home)), None)
            profile = complete_destination_profile(profile, args.data_dir) if profile else None
            workflow = select_application_workflow(scoped, ApplicationRuleContext(
                home_university=home, partner_university=partner.school_name))
            result = build_school_completeness(
                partner, profile, workflow, home_university=home,
                include_eligibility=bool(partner.source_url),
            )
            schools += 1
            row = {"母校": home, "合作校": partner.school_name, "國家": partner.country or "",
                   "完整項目": f"{result.available_count}/{result.total_count}",
                   "優先缺口": "、".join(result.priority_gaps)}
            for item in result.items:
                totals[(item.label, item.status)] += 1
                row[item.label] = {"available": "完整", "partial": "部分", "needs_confirmation": "待確認", "missing": "缺"}[item.status]
            rows.append(row)
    summary = {
        "schools": schools,
        "by_item": {
            label: {status: totals[(label, status)] for status in ("available", "partial", "needs_confirmation", "missing")}
            for label in dict.fromkeys(label for label, _ in totals)
        },
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    if args.csv and rows:
        args.csv.parent.mkdir(parents=True, exist_ok=True)
        with args.csv.open("w", encoding="utf-8-sig", newline="") as handle:
            fieldnames = list(dict.fromkeys(key for row in rows for key in row))
            writer = csv.DictWriter(handle, fieldnames=fieldnames, restval="")
            writer.writeheader()
            writer.writerows(rows)
    return 0


def cmd_cleanup_document_vault(args: argparse.Namespace) -> int:
    service = create_document_vault_service(args.data_dir)
    result = service.cleanup()
    print(result.model_dump_json())
    return 0


def cmd_analytics_report(args: argparse.Namespace) -> int:
    import json
    from datetime import datetime, timezone

    from .analytics_report import build_report
    from .analytics_repository import MAX_FETCH_ROWS, create_analytics_repository
    from .analytics_routes import resolve_window

    repository = create_analytics_repository(args.data_dir)
    start_at, end_at = resolve_window(max(1, min(args.days, 400)), None, None)
    span = end_at - start_at
    events, truncated = repository.fetch_events(start_at - span, end_at, MAX_FETCH_ROWS)
    report = build_report(
        [e for e in events if e.occurred_at >= start_at], repository.fetch_api_metrics(start_at, end_at),
        start=start_at, end=end_at, previous_events=[e for e in events if e.occurred_at < start_at],
        include_bots=args.include_bots, truncated=truncated, now=datetime.now(timezone.utc),
    )
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 0
    current = report["overview"]["current"]
    change = report["overview"]["change_pct"]
    print(f"UniWay usage, last {report['range']['days']} days (Taipei time), backend={repository.backend_name}")
    print(f"  visitors {current['visitors']} ({change['visitors']}% vs previous), sessions {current['sessions']}, "
          f"pageviews {current['pageviews']}, bounce {current['bounce_rate']}%")
    print("  funnel: " + " > ".join(f"{row['step']} {row['visitors']}" for row in report["funnel"]))
    print("  top pages: " + ", ".join(f"{row['route']} {row['views']}" for row in report["pages"][:5]))
    print("  top schools: " + ", ".join(f"{row['school']} {row['opens']}" for row in report["schools"]["top"][:5]))
    print("  top searches: " + ", ".join(f"{row['term']} {row['searches']}" for row in report["search"]["top_terms"][:5]))
    print(f"  new accounts (server): {report['signup']['accounts_created_by_server']}, "
          f"posts: {report['community']['posts']}, js errors: {report['errors']['js_errors']}")
    if truncated:
        print("  note: more events exist than were read; numbers are low.")
    return 0


def cmd_purge_analytics(args: argparse.Namespace) -> int:
    from datetime import timedelta

    from .analytics_repository import create_analytics_repository

    if args.days < 30:
        print("Refusing to purge data newer than 30 days.", file=sys.stderr)
        return 2
    removed = create_analytics_repository(args.data_dir).purge(utc_now() - timedelta(days=args.days))
    print(removed)
    return 0


def _build_ai_indexes(
    pages: list[ProcessedPage],
    data_dir: Path,
    *,
    rules_only: bool,
) -> None:
    use_ai = ai_enabled() and not rules_only
    records = build_structured_source_index(pages, data_dir, use_ai=use_ai)
    status = build_rag_index(
        pages,
        data_dir,
        use_embeddings=use_ai,
        sync_supabase=True,
    )
    method = "AI + rules" if use_ai else "rules"
    print(f"Structured {len(records)} sources ({method}).")
    print(
        f"Indexed {status.chunk_count} source passages "
        f"({status.embedded_count} with embeddings)."
    )


def _partners_for_home_school(home_school: str, data_dir: Path):
    home = require_university(home_school)
    partners = (
        fetch_ntpu_partner_universities()
        if home.id == NTPU.id
        else fetch_partner_universities()
    )
    return home, apply_partner_research(
        partners,
        load_partner_research(data_dir),
        home_university=home.school_name,
    )


def _select_requested_partners(partners, requested_names: list[str]):
    if not requested_names:
        return partners, set()
    requested = {normalize_school(name) for name in requested_names}
    selected = [
        partner
        for partner in partners
        if normalize_school(partner.school_name) in requested
    ]
    missing = requested - {
        normalize_school(partner.school_name) for partner in selected
    }
    return selected, missing


def cmd_collect_experiences(args: argparse.Namespace) -> int:
    ensure_data_dirs(args.data_dir)
    home, partners = _partners_for_home_school(args.home_school, args.data_dir)
    if args.school:
        selected, missing = _select_requested_partners(partners, args.school)
        if missing:
            print(f"Partner schools not found: {', '.join(sorted(missing))}")
            return 2
    else:
        audited = {
            normalize_school(row.school_name)
            for row in load_collection_audits(args.data_dir)
            if row.collector == "experiences"
            and normalize_school(row.home_university or "長庚大學")
            == normalize_school(home.school_name)
            and row.status in {"completed", "no_results"}
        }
        candidates = [
            partner
            for partner in partners
            if args.refresh
            or normalize_school(partner.school_name) not in audited
        ]
        selected = candidates[: max(1, args.max_schools)]

    collected_count = 0
    failed_count = 0
    for index, partner in enumerate(selected):
        if index:
            time.sleep(max(0.0, args.school_delay))
        try:
            discovered = collect_student_experiences(
                partner,
                max_sources=max(3, args.max_sources),
            )
            rows = merge_refreshed_student_experiences(
                partner,
                load_student_experiences(args.data_dir),
                discovered,
                max_sources=max(3, args.max_sources),
            )
            replace_school_experiences(partner.school_name, rows, args.data_dir)
            status = "completed" if rows else "no_results"
            if discovered:
                note = None
            elif rows:
                note = "No new source was found; previously accepted sources were retained."
            else:
                note = "No reliable public student experience source was found."
            upsert_collection_audit(
                CollectionAudit(
                    school_name=partner.school_name,
                    collector="experiences",
                    status=status,
                    home_university=home.school_name,
                    result_count=len(rows),
                    note=note,
                ),
                args.data_dir,
            )
            collected_count += len(rows)
            print(f"{partner.school_name}: {len(rows)} public experience sources")
        except Exception as exc:
            failed_count += 1
            upsert_collection_audit(
                CollectionAudit(
                    school_name=partner.school_name,
                    collector="experiences",
                    status="error",
                    home_university=home.school_name,
                    note=str(exc)[:500],
                ),
                args.data_dir,
            )
            print(f"{partner.school_name}: collection failed ({exc})")

    print(
        f"Collected {collected_count} sources for {len(selected)} partner schools "
        f"({failed_count} failed)."
    )
    print(f"Wrote {args.data_dir / 'processed' / 'student_experiences.jsonl'}")
    return 1 if selected and failed_count == len(selected) else 0


def cmd_collect_workflows(args: argparse.Namespace) -> int:
    ensure_data_dirs(args.data_dir)
    content_store = create_content_governance_store(args.data_dir)
    home, partners = _partners_for_home_school(args.home_school, args.data_dir)
    if args.school:
        selected, missing = _select_requested_partners(partners, args.school)
        if missing:
            print(f"Partner schools not found: {', '.join(sorted(missing))}")
            return 2
    else:
        cached = {
            normalize_school(row.school_name)
            for row in load_application_workflows(args.data_dir)
            if normalize_school(row.home_university) == normalize_school(home.school_name)
        }
        candidates = [
            partner
            for partner in partners
            if args.refresh or normalize_school(partner.school_name) not in cached
        ]
        selected = candidates[: max(1, args.max_schools)]

    for index, partner in enumerate(selected):
        if index:
            time.sleep(max(0.0, args.school_delay))
        try:
            if not partner.website:
                research = discover_partner_official_site(
                    partner,
                    home_university=home.school_name,
                )
                upsert_partner_research(research, args.data_dir)
                if research.official_website:
                    partner = partner.model_copy(
                        update={"website": research.official_website}
                    )
            workflow = collect_application_workflow(
                partner,
                home_university=home.school_name,
            )
            result = stage_workflow_refresh(content_store, workflow, detected_by="cli")
            upsert_collection_audit(
                CollectionAudit(
                    school_name=partner.school_name,
                    collector="workflows",
                    status=("pending_review" if result.change_detected else "unchanged"),
                    home_university=home.school_name,
                    result_count=len(workflow.steps),
                ),
                args.data_dir,
            )
            state = "pending review" if result.change_detected else "unchanged"
            print(
                f"{partner.school_name}: {len(workflow.steps)} official application "
                f"steps ({state})"
            )
        except Exception as exc:
            upsert_collection_audit(
                CollectionAudit(
                    school_name=partner.school_name,
                    collector="workflows",
                    status="error",
                    home_university=home.school_name,
                    note=str(exc)[:500],
                ),
                args.data_dir,
            )
            print(f"{partner.school_name}: workflow collection failed ({exc})")

    print(f"Collected workflows for {len(selected)} partner schools.")
    print(
        "Wrote review candidates to "
        f"{args.data_dir / 'processed' / 'application_workflow_revisions.jsonl'}"
    )
    return 0


def _destination_quality(status: str) -> int:
    return {
        "not_collected": 0,
        "not_found": 1,
        "official_partial": 2,
        "official_verified": 3,
    }.get(status, 0)


def cmd_research_partners(args: argparse.Namespace) -> int:
    """Run the complete, resumable research pass for selected partner schools."""
    ensure_data_dirs(args.data_dir)
    content_store = create_content_governance_store(args.data_dir)
    home, partners = _partners_for_home_school(args.home_school, args.data_dir)
    home_key = normalize_school(home.school_name)
    current_research = {
        normalize_school(row.school_name): row
        for row in load_partner_research(args.data_dir)
        if normalize_school(row.home_university) == home_key
    }
    if args.school:
        selected, missing = _select_requested_partners(partners, args.school)
        if missing:
            print(f"Partner schools not found: {', '.join(sorted(missing))}")
            return 2
    else:
        research_keys = {
            key
            for key, row in current_research.items()
            if row.verification_status != "error"
        }
        workflow_keys = {
            normalize_school(row.school_name)
            for row in load_application_workflows(args.data_dir)
            if normalize_school(row.home_university) == home_key
        }
        audits = load_collection_audits(args.data_dir)
        destination_keys = {
            normalize_school(row.school_name)
            for row in audits
            if row.collector == "destinations"
            and normalize_school(row.home_university or "長庚大學") == home_key
            and row.status != "error"
        }
        experience_keys = {
            normalize_school(row.school_name)
            for row in audits
            if row.collector == "experiences"
            and normalize_school(row.home_university or "長庚大學") == home_key
            and row.status != "error"
        }
        image_keys = {
            normalize_school(row.school_name)
            for row in audits
            if row.collector == "images"
            and normalize_school(row.home_university or "長庚大學") == home_key
            and row.status == "verified"
        }
        candidates = [
            partner
            for partner in partners
            if args.refresh
            or normalize_school(partner.school_name)
            not in research_keys
            & workflow_keys
            & destination_keys
            & experience_keys
            & image_keys
        ]
        selected = candidates[: max(1, args.max_schools)]

    if not selected:
        print(f"{home.school_name}: no incomplete partner-school research was found.")
        return 0

    existing_destinations = {
        normalize_school(row.school_name): row
        for row in load_destination_profiles(args.data_dir)
        if normalize_school(row.home_university or CGU.school_name) == home_key
    }
    stage_successes = 0
    stage_failures = 0
    for index, original_partner in enumerate(selected):
        if index:
            time.sleep(max(0.0, args.school_delay))
        partner = original_partner.model_copy(deep=True)
        print(f"[{index + 1}/{len(selected)}] {partner.school_name}")

        try:
            cached_research = current_research.get(normalize_school(partner.school_name))
            if cached_research is not None and not args.refresh:
                research = cached_research
            else:
                research_input = (
                    partner.model_copy(update={"website": None})
                    if args.refresh
                    else partner
                )
                research = discover_partner_official_site(
                    research_input,
                    home_university=home.school_name,
                )
            if args.refresh or not research.ranking_info:
                research = enrich_partner_ranking(partner, research)
            upsert_partner_research(research, args.data_dir)
            upsert_collection_audit(
                CollectionAudit(
                    school_name=partner.school_name,
                    collector="official_website",
                    status=research.verification_status,
                    home_university=home.school_name,
                    result_count=1 if research.official_website else 0,
                    note=research.note,
                    checked_at=research.checked_at,
                ),
                args.data_dir,
            )
            if research.official_website:
                partner = partner.model_copy(
                    update={"website": research.official_website}
                )
            print(
                f"  official website: {research.verification_status}"
                + (f" ({research.official_domain})" if research.official_domain else "")
            )
            print(f"  ranking: {research.ranking_info}")
            stage_successes += 1
        except Exception as exc:
            stage_failures += 1
            upsert_collection_audit(
                CollectionAudit(
                    school_name=partner.school_name,
                    collector="official_website",
                    status="error",
                    home_university=home.school_name,
                    note=str(exc)[:500],
                ),
                args.data_dir,
            )
            print(f"  official website: failed ({exc})")

        if args.site_only:
            continue

        try:
            image_records = collect_school_images(
                output_dir=DEFAULT_IMAGE_OUTPUT_DIR,
                manifest_path=DEFAULT_IMAGE_MANIFEST,
                timeout_seconds=18.0,
                delay_seconds=0.0,
                missing_only=not args.refresh,
                refresh_overrides=args.refresh,
                partners=[partner],
            )
            image_record = image_records[0]
            upsert_collection_audit(
                CollectionAudit(
                    school_name=partner.school_name,
                    collector="images",
                    status=image_record.status,
                    home_university=home.school_name,
                    result_count=1 if image_record.status == "verified" else 0,
                    note=image_record.note,
                ),
                args.data_dir,
            )
            print(f"  image: {image_record.status}")
            if image_record.status == "verified":
                stage_successes += 1
            else:
                stage_failures += 1
        except Exception as exc:
            stage_failures += 1
            upsert_collection_audit(
                CollectionAudit(
                    school_name=partner.school_name,
                    collector="images",
                    status="error",
                    home_university=home.school_name,
                    note=str(exc)[:500],
                ),
                args.data_dir,
            )
            print(f"  image: failed ({exc})")

        try:
            workflow = collect_application_workflow(
                partner,
                home_university=home.school_name,
            )
            result = stage_workflow_refresh(content_store, workflow, detected_by="cli")
            upsert_collection_audit(
                CollectionAudit(
                    school_name=partner.school_name,
                    collector="workflows",
                    status=("pending_review" if result.change_detected else "unchanged"),
                    home_university=home.school_name,
                    result_count=len(workflow.steps),
                    note=workflow.coverage_note,
                    checked_at=workflow.last_checked,
                ),
                args.data_dir,
            )
            state = "pending review" if result.change_detected else "unchanged"
            print(f"  workflow: {state} ({len(workflow.steps)} steps)")
            stage_successes += 1
        except Exception as exc:
            stage_failures += 1
            upsert_collection_audit(
                CollectionAudit(
                    school_name=partner.school_name,
                    collector="workflows",
                    status="error",
                    home_university=home.school_name,
                    note=str(exc)[:500],
                ),
                args.data_dir,
            )
            print(f"  workflow: failed ({exc})")

        try:
            profile = collect_destination_profile(
                partner,
                home_university=home.school_name,
            )
            previous = existing_destinations.get(normalize_school(partner.school_name))
            if previous and _destination_quality(previous.coverage_status) > _destination_quality(
                profile.coverage_status
            ):
                profile = previous
                note = "A previously verified destination profile was retained."
            else:
                upsert_destination_profile(profile, args.data_dir)
                existing_destinations[normalize_school(partner.school_name)] = profile
                note = profile.coverage_note
            upsert_collection_audit(
                CollectionAudit(
                    school_name=partner.school_name,
                    collector="destinations",
                    status=profile.coverage_status,
                    home_university=home.school_name,
                    result_count=len(profile.sources),
                    note=note,
                    checked_at=profile.last_checked or utc_now(),
                ),
                args.data_dir,
            )
            print(
                f"  destination: {profile.coverage_status} "
                f"({len(profile.sources)} official sources)"
            )
            stage_successes += 1
        except Exception as exc:
            stage_failures += 1
            upsert_collection_audit(
                CollectionAudit(
                    school_name=partner.school_name,
                    collector="destinations",
                    status="error",
                    home_university=home.school_name,
                    note=str(exc)[:500],
                ),
                args.data_dir,
            )
            print(f"  destination: failed ({exc})")

        try:
            discovered = collect_student_experiences(
                partner,
                max_sources=max(3, args.max_sources),
            )
            experiences = merge_refreshed_student_experiences(
                partner,
                load_student_experiences(args.data_dir),
                discovered,
                max_sources=max(3, args.max_sources),
            )
            replace_school_experiences(
                partner.school_name,
                experiences,
                args.data_dir,
            )
            experience_status = "completed" if experiences else "no_results"
            upsert_collection_audit(
                CollectionAudit(
                    school_name=partner.school_name,
                    collector="experiences",
                    status=experience_status,
                    home_university=home.school_name,
                    result_count=len(experiences),
                    note=(
                        None
                        if discovered
                        else "No reliable new public student experience source was found."
                    ),
                ),
                args.data_dir,
            )
            print(f"  experiences: {experience_status} ({len(experiences)} sources)")
            stage_successes += 1
        except Exception as exc:
            stage_failures += 1
            upsert_collection_audit(
                CollectionAudit(
                    school_name=partner.school_name,
                    collector="experiences",
                    status="error",
                    home_university=home.school_name,
                    note=str(exc)[:500],
                ),
                args.data_dir,
            )
            print(f"  experiences: failed ({exc})")

    print(
        f"Research pass finished for {len(selected)} {home.short_name} partner schools: "
        f"{stage_successes} stages completed, {stage_failures} failed."
    )
    print(f"Wrote resumable research data under {args.data_dir / 'processed'}")
    return 1 if stage_successes == 0 and stage_failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
