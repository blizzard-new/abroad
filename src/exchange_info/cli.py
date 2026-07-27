from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

from .application_workflow_collector import collect_application_workflow
from .ai_gateway import ai_enabled
from .cleaner import process_pages
from .crawler import CguOiaCrawler, CrawlerConfig
from .experience_collector import (
    collect_student_experiences,
    merge_refreshed_student_experiences,
    normalize_school,
)
from .extractor import build_exchange_info
from .models import CollectionAudit, ProcessedPage, utc_now
from .ntpu_student_view import fetch_ntpu_partner_universities
from .partner_research import (
    apply_partner_research,
    collect_destination_profile,
    discover_partner_official_site,
    enrich_partner_ranking,
)
from .rag import build_rag_index
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
    replace_application_workflow,
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
from .university_registry import NTPU, require_university


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
            replace_application_workflow(workflow, args.data_dir)
            upsert_collection_audit(
                CollectionAudit(
                    school_name=partner.school_name,
                    collector="workflows",
                    status=workflow.coverage_status,
                    home_university=home.school_name,
                    result_count=len(workflow.steps),
                ),
                args.data_dir,
            )
            print(f"{partner.school_name}: {len(workflow.steps)} official application steps")
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
    print(f"Wrote {args.data_dir / 'processed' / 'application_workflows.jsonl'}")
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
            replace_application_workflow(workflow, args.data_dir)
            upsert_collection_audit(
                CollectionAudit(
                    school_name=partner.school_name,
                    collector="workflows",
                    status=workflow.coverage_status,
                    home_university=home.school_name,
                    result_count=len(workflow.steps),
                    note=workflow.coverage_note,
                    checked_at=workflow.last_checked,
                ),
                args.data_dir,
            )
            print(f"  workflow: {workflow.coverage_status} ({len(workflow.steps)} steps)")
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
            profile = collect_destination_profile(partner)
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
