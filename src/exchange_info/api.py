from __future__ import annotations

from .destination_tips import DestinationGuide, DestinationGuideSummary, guide_for_country, guide_summaries
from .discovery import localize_experience_digest
from .experience_digests import attach_digests, load_digests, with_bundled_sources
from .public_translation import PublicTranslationBatch, translate_public_batch
from .school_content import complete_destination_profile
from .ncu_document_conditions import preparation_state_key

import asyncio
import csv
from contextvars import ContextVar
from .access_control import (
    HOME_UNIVERSITY_UNSET,
    catalog_home_university,
    can_read_university_community,
    community_author_display_name,
    is_university_community_post,
    university_community_board,
    is_platform_admin,
    school_basis,
    school_change_locked_until,
    school_from_email,
)
from io import BytesIO, StringIO
from pypdf import PdfReader
from typing import Any, Literal, Mapping, Sequence
from uuid import uuid4

import hashlib
import json
import logging
import mimetypes
import os
import re
import secrets
import threading
import time
import unicodedata
from contextlib import asynccontextmanager, suppress
from datetime import datetime, timedelta, timezone
from functools import partial
from pathlib import Path
from urllib.parse import quote, urlencode

import requests
from fastapi import FastAPI, File, Form, Header, HTTPException, Query, Request, Response, UploadFile
from fastapi.responses import FileResponse, HTMLResponse, PlainTextResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from starlette.concurrency import run_in_threadpool

from .advisor import answer_question, build_advisor_plan
from .account_community_cleanup import cleanup_local_account_community
from .community_repositories import (
    CommunityRepositoryError,
    CommunityBlockMutationRequest,
    PrivateCommunityMutationStatus,
    PrivateConversationMutationRequest,
    PrivateConversationStatusMutationRequest,
    PrivateMessageMutationRequest,
)
from .analytics import AnalyticsService, ApiMetricsMiddleware
from .analytics_repository import create_analytics_repository
from .analytics_routes import register_analytics_routes
from .feedback import FeedbackService, create_feedback_repository
from .feedback_routes import register_feedback_routes
from .notification_routes import register_notification_routes
from .openapi_contract import install_openapi_contract
from .workflow_review_routes import register_workflow_review_routes
from .content_governance_routes import register_content_governance_routes
from .destination_profile_review import apply_destination_profile_promotions
from .tku_eligibility_routes import register_tku_eligibility_routes
from .ai_gateway import (
    ai_embedding_model,
    ai_enabled,
    ai_model,
    ai_provider_name,
    ai_runtime_state,
)
from .application_workflow_collector import collect_application_workflow
from .university_locations import load_university_locations, public_location
from .life_context import SchoolLifeContext, build_life_context, reference_student_sources, refresh_life_research
from .partner_research import (
    apply_partner_research,
    collect_destination_profile,
    discover_partner_official_site,
)
from .application_documents import (
    all_application_templates,
    build_application_document_catalog,
    build_packet_manifest,
    generate_application_packet_docx,
    generate_application_packet_pdf,
    templates_for_context,
)
from .extractor import FIELD_TRIGGERS
from .experience_collector import (
    build_experience_digest,
    collect_student_experiences,
    merge_refreshed_student_experiences,
    normalize_school,
)
from .application_rules import build_personal_application_plan
from .calendar_conflicts import build_calendar_conflict_report
from .calendar_task_scheduling import build_calendar_task_schedule
from .document_checker import MAX_DOCUMENT_BYTES, check_document
from .document_rewriter import DocumentRewriteUnavailable, rewrite_document
from .entitlements import configured_product_release_mode, product_feature_enabled, resolve_product_entitlements
from .repositories import (
    AccountConflictError,
    AccountNotFoundError,
    AccountDeletionMutationRequest,
    AccountDeletionMutationResult,
    AccountDeletionMutationStatus,
    OAuthLoginMutationRequest,
    OAuthLoginMutationResult,
    OAuthLoginMutationStatus,
    WorkspaceMutationKind,
    WorkspaceMutationRequest,
    WorkspaceMutationStatus,
    workspace_identity_key,
)
from .transient_auth import (
    TransientAuthState,
    TransientAuthStateKind,
    TransientAuthStoreError,
    TransientAuthRateLimitError,
    TransientAuthCapacityError,
)
from .email_verification import (
    EmailVerificationError,
    EmailVerificationRateLimitError,
    EmailVerificationDeliveryError,
    EmailVerificationExpiredError,
    EmailVerificationInvalidError,
)
from .submission_progress import transition_submission_progress
from .workflow_identity import workflow_storage_key
from .workflow_issue_reports import (
    WorkflowIssueReportMutationStatus,
    WorkflowIssueReportReviewMutation,
    WorkflowIssueReportSubmitMutation,
    canonical_issue_report_fingerprint,
)
from .document_vault import (
    VaultAuthorizationError,
    VaultConsentError,
    VaultError,
    VaultExpiredError,
    VaultIntegrityError,
    VaultNotFoundError,
    VaultValidationError,
)
from .form_drafts import (
    FormDraftConflictError,
    FormDraftError,
    FormDraftIntegrityError,
    FormDraftNotFoundError,
)
from .models import (
    ExperienceDigestZh,
    SchoolDataCompleteness,
    AccountApplicationWorkspace,
    AccountApplicationWorkspaceEnvelope,
    AccountSubmissionProgress,
    CalendarConflictAnalysisRequest,
    CalendarConflictReport,
    CalendarTaskScheduleRequest,
    CalendarTaskScheduleReport,
    EmailVerificationConfirm,
    EmailVerificationConfirmation,
    EmailVerificationDispatch,
    EmailVerificationRequest,
    PersonalApplicationPlanRequest,
    PersonalApplicationPlanResult,
    ApplicationPlanScheduleRequest,
    ApplicationPlanScheduleResult,
    ProductAccessTier,
    ProductEntitlementSnapshot,
    ProductReleaseMode,
    SubmissionProgressTransitionRequest,
    AccountLogin,
    AccountProfile,
    AccountProfileUpdate,
    AccountProviderLink,
    AccountRegister,
    AccountSession,
    AccountSessionRecord,
    AccountCalendarEvent,
    ApplicationCenterContext,
    PartnerDocumentPreparationState,
    ApplicationDocumentCatalog,
    ApplicationDocumentTemplate,
    ApplicationFormDraft,
    ApplicationFormDraftList,
    ApplicationFormDraftSave,
    ApplicationPacketManifest,
    ApplicationPacketRequest,
    ApplicationWorkflowIssueCategory,
    ApplicationWorkflowIssueReport,
    ApplicationWorkflowIssueReportCreate,
    ApplicationWorkflowIssueReportReview,
    ApplicationWorkflowIssueReportReviewRequest,
    ApplicationWorkflowIssueReportStatus,
    AuthProvider,
    AuthProviderStatus,
    AnonymousIdentity,
    AnonymousIdentityCreate,
    AnonymousIdentitySession,
    AdvisorAnswer,
    AdvisorPlan,
    AdvisorProfile,
    AdvisorQuestionRequest,
    CommunityAnswer,
    CommunityAnswerCreate,
    CommunityBlock,
    CommunityBlockCreate,
    CommunityIdentityMode,
    CommunityBoardAccess,
    CommunityPost,
    CommunityPostComment,
    CommunityPostCommentCreate,
    CommunityPostCreate,
    CommunityPostThread,
    CommunityQuestion,
    CommunityQuestionCreate,
    CommunityQuestionThread,
    CommunityReport,
    CommunityReportCreate,
    CommunityTopic,
    ConversationStatus,
    CollectionAudit,
    CalendarEventSyncRequest,
    CalendarSyncStatus,
    DeadlineRecord,
    DestinationProfile,
    DocumentCheckResult,
    DocumentRewriteRequest,
    DocumentRewriteResult,
    DocumentRecord,
    ExchangeInfo,
    ExperienceSubmission,
    ExperienceSubmissionCreate,
    ModerationStatus,
    CoverageSummary,
    PartnerCoverage,
    PageCategory,
    ProductFeature,
    SearchResult,
    PrivateConversation,
    PrivateConversationCreate,
    PrivateMessage,
    PrivateMessageCreate,
    PublicChatMessage,
    PublicChatMessageCreate,
    StudentExperienceDigest,
    SourceReference,
    StudentDashboard,
    StructuredSourceRecord,
    SupportedUniversity,
    SourceSummary,
    UniversityApplicationWorkflow,
    UserAccount,
    ApplicationFormDraftAttachment,
    VaultConsentPurpose,
    VaultDocumentCategory,
    VaultDocumentList,
    VaultDocumentSummary,
    VaultDownloadGrant,
    VaultVersionSummary,
    VerifiedWindowDeadlineCatalog,
    CrossSchoolPartnerDirectory,
    CrossSchoolPartnerPageData,
    StudyPlanWorkbenchCatalog,
    StudyPlanWorkbenchPayload,
    AdmittedStudentConnectCreateRequest,
    AdmittedStudentConnectHub,
    PreferenceSignalSubmitRequest,
    SchoolStagedNetworkStatus,
    StagedNetworkEffectsCatalog,
    utc_now,
)
from .cross_school_partners import (
    build_cross_school_partner_directory,
    build_cross_school_partner_page_data,
)
from .staged_network_effects import (
    build_school_staged_network_status,
    build_staged_network_effects_catalog,
    record_preference_signal,
    register_admitted_student_connection,
)
from .study_plan_workbench import (
    build_study_plan_workbench_catalog,
    build_study_plan_workbench_payload,
)
from .seo import EDITORIAL_PATHS, SeoSettings, create_seo_router, homepage_html
from .seo_changes import ContentChanges
from .verified_window_deadlines import (
    build_school_window_ics,
    build_verified_window_deadline_catalog,
)
from .ntpu_student_view import (
    build_ntpu_student_dashboard,
    fetch_ntpu_partner_universities,
    ntpu_exchange_info,
    ntpu_processed_pages,
)
from .ncu_student_view import build_ncu_student_dashboard, fetch_ncu_partner_universities, ncu_exchange_info, ncu_processed_pages
from .ntu_student_view import (
    build_ntu_student_dashboard,
    fetch_ntu_partner_universities,
    ntu_exchange_info,
    ntu_processed_pages,
)
from .fju_student_view import (
    build_fju_student_dashboard,
    fetch_fju_partner_universities,
    fju_exchange_info,
    fju_processed_pages,
)
from .scu_student_view import (
    build_scu_student_dashboard,
    fetch_scu_partner_universities,
    scu_exchange_info,
    scu_processed_pages,
)
from .ntnu_student_view import (
    build_ntnu_student_dashboard,
    fetch_ntnu_partner_universities,
    ntnu_exchange_info,
    ntnu_processed_pages,
)
from .cycu_student_view import (
    build_cycu_student_dashboard,
    cycu_exchange_info,
    cycu_processed_pages,
    fetch_cycu_partner_universities,
)
from .ntust_student_view import (
    build_ntust_student_dashboard,
    fetch_ntust_partner_universities,
    ntust_exchange_info,
    ntust_processed_pages,
)
from .yzu_student_view import (
    build_yzu_student_dashboard,
    fetch_yzu_partner_universities,
    yzu_exchange_info,
    yzu_processed_pages,
)
from .fcu_student_view import (
    build_fcu_student_dashboard,
    fetch_fcu_partner_universities,
    fcu_exchange_info,
    fcu_processed_pages,
)
from .nsysu_student_view import (
    build_nsysu_student_dashboard,
    fetch_nsysu_partner_universities,
    nsysu_exchange_info,
    nsysu_processed_pages,
)
from .nchu_student_view import (
    build_nchu_student_dashboard,
    fetch_nchu_partner_universities,
    nchu_exchange_info,
    nchu_processed_pages,
)
from .ntut_student_view import (
    build_ntut_student_dashboard,
    fetch_ntut_partner_universities,
    ntut_exchange_info,
    ntut_processed_pages,
)
from .nccu_student_view import (
    build_nccu_student_dashboard,
    fetch_nccu_partner_universities,
    nccu_exchange_info,
    nccu_processed_pages,
)
from .ncku_student_view import (
    build_ncku_student_dashboard,
    fetch_ncku_partner_universities,
    ncku_exchange_info,
    ncku_processed_pages,
)
from .nycu_student_view import (
    build_nycu_student_dashboard,
    fetch_nycu_partner_universities,
    nycu_exchange_info,
    nycu_processed_pages,
)
from .nthu_student_view import (
    build_nthu_student_dashboard,
    fetch_nthu_partner_universities,
    nthu_exchange_info,
    nthu_processed_pages,
)
from .pccu_student_view import (
    build_pccu_student_dashboard,
    fetch_pccu_partner_universities,
    pccu_exchange_info,
    pccu_processed_pages,
)
from .wzu_student_view import (
    build_wzu_student_dashboard,
    fetch_wzu_partner_universities,
    wzu_exchange_info,
    wzu_processed_pages,
)
from .nkust_student_view import (
    build_nkust_student_dashboard,
    fetch_nkust_partner_universities,
    nkust_exchange_info,
    nkust_processed_pages,
)
from .yuntech_student_view import (
    build_yuntech_student_dashboard,
    fetch_yuntech_partner_universities,
    yuntech_exchange_info,
    yuntech_processed_pages,
)
from .ntou_student_view import (
    build_ntou_student_dashboard,
    fetch_ntou_partner_universities,
    ntou_exchange_info,
    ntou_processed_pages,
)

mimetypes.add_type("application/vnd.android.package-archive", ".apk")


def _escape_ics(value: str | None) -> str:
    return (
        str(value or "")
        .replace("\\", "\\\\")
        .replace("\r\n", "\\n")
        .replace("\n", "\\n")
        .replace(",", "\\,")
        .replace(";", "\\;")
    )


def _calendar_feed_content(
    events: list[AccountCalendarEvent],
    account: UserAccount | None = None,
) -> str:
    stamp = utc_now().strftime("%Y%m%dT%H%M%SZ")
    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//Exchange Guide Taiwan//Application Calendar//ZH-TW",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH",
        "X-WR-CALNAME:交換申請時程",
        "X-WR-TIMEZONE:Asia/Taipei",
    ]
    reminder_days = (
        account.notification_preferences.deadline_reminder_days
        if account and account.notification_preferences
        else [30, 14, 7, 3, 1]
    )
    reminder_triggers = sorted(set(reminder_days) | {0}, reverse=True)

    for event in sorted(events, key=lambda item: (item.date, item.title)):
        start = datetime.strptime(event.date, "%Y-%m-%d")
        end = start + timedelta(days=1)
        description = event.note or ""
        if event.source_url:
            description = f"{description}\n官方來源：{event.source_url}".strip()
        event_lines = [
            "BEGIN:VEVENT",
            f"UID:{_escape_ics(event.id)}@exchange-guide.tw",
            f"DTSTAMP:{stamp}",
            f"DTSTART;VALUE=DATE:{start.strftime('%Y%m%d')}",
            f"DTEND;VALUE=DATE:{end.strftime('%Y%m%d')}",
            f"SUMMARY:{_escape_ics(f'[交換申請] {event.title}')}",
            f"DESCRIPTION:{_escape_ics(description)}",
        ]
        if event.source_url:
            event_lines.append(f"URL:{_escape_ics(event.source_url)}")

        if not getattr(event, "generated_from_event_id", None) and event.status not in ("ready", "completed"):
            for days in reminder_triggers:
                trigger = f"-P{days}D" if days > 0 else "PT0M"
                event_lines.extend(
                    [
                        "BEGIN:VALARM",
                        f"TRIGGER:{trigger}",
                        "ACTION:DISPLAY",
                        f"DESCRIPTION:{_escape_ics(event.title)}",
                        "END:VALARM",
                    ]
                )

        event_lines.append("END:VEVENT")
        lines.extend(event_lines)

    lines.append("END:VCALENDAR")
    return "\r\n".join(line for line in lines if line) + "\r\n"


from .settings import DEFAULT_DATA_DIR
from .school_identity import school_identity_key
from .storage import (
    append_anonymous_identity,
    append_community_answer,
    append_community_post,
    append_community_post_comment,
    append_community_question,
    append_community_report,
    append_experience_submission,
    append_public_chat_message,
    data_paths,
    file_signature,
    load_exchange_info,
    load_application_workflows,
    load_bundled_application_workflows,
    merge_application_workflows,
    load_account_sessions,
    load_community_answers,
    load_community_post_comments,
    load_community_posts,
    load_community_questions,
    load_collection_audits,
    load_destination_profiles,
    load_partner_research,
    load_anonymous_identities,
    load_processed_pages,
    load_structured_sources,
    load_public_chat_messages,
    load_student_experiences,
    load_user_accounts,
    replace_application_workflow,
    replace_school_experiences,
    save_account_sessions,
    save_anonymous_identities,
    save_user_accounts,
    upsert_collection_audit,
    upsert_destination_profile,
    upsert_partner_research,
)
from .student_view import build_student_dashboard
from .cgu_catalogue import CatalogueView, create_cgu_catalogue
from .ccu_student_view import (
    build_ccu_student_dashboard,
    fetch_ccu_partner_universities,
    ccu_exchange_info,
    ccu_processed_pages,
)
from .tku_student_view import (
    build_tku_student_dashboard, fetch_tku_partner_universities,
    tku_exchange_info, tku_processed_pages,
)
from .rag import rag_index_status, search_document_chunks, supabase_configured
from .legal_pages import TERMS_VERSION, register_legal_pages
from .request_origin import client_fingerprint, public_base_url
from .seo import EDITORIAL_PATHS, SeoSettings, create_seo_router, homepage_html
from .seo_changes import ContentChanges
from .seo_analytics import measurement_id
from .university_registry import (
    CGU,
    CCU,
    CYCU,
    FCU,
    FJU,
    NCCU,
    NCHU,
    NCKU,
    NKUST,
    NSYSU,
    NTHU,
    NTNU,
    NTPU,
    NTU,
    NTUST,
    NTUT,
    NYCU,
    NCU,
    PCCU,
    SCU,
    WZU,
    YUNTECH,
    NTOU,
    YZU,
    SUPPORTED_UNIVERSITIES,
    UniversityProfile,
    require_university,
    resolve_university,
)


STATIC_DIR = Path(__file__).resolve().parent / "static"
SCHOOL_IMAGE_MANIFEST = STATIC_DIR / "assets" / "school-images.json"
AUTH_COOKIE_NAME = "exchange_guide_session"
TAIPEI_TZ = timezone(timedelta(hours=8))  # Taiwan has no daylight saving
# Fonts are named after a hash of their content, so a name never changes meaning.
_CONTENT_HASHED_FILE = re.compile(r"-[0-9a-f]{64}(?:-\d+)?\.woff2?$")


def _static_cache_control(path: str, versioned: bool) -> str:
    """How long a browser may keep a file from /static without asking again.

    Nothing here had any caching header, so every visit asked the server again about each of the ~200 files of a page
    (fonts and images alone are about 9 MB). Scripts and styles that the page links without a ``?v=`` are still checked
    each time, so a forgotten version number cannot leave visitors on an old script.
    """
    if _CONTENT_HASHED_FILE.search(path):
        return "public, max-age=31536000, immutable"
    if path.endswith((".js", ".css", ".html", ".json", ".webmanifest")) and not versioned:
        return "no-cache"
    return "public, max-age=86400"
CACHE_WARM_UP_DELAY_SECONDS = 15.0
DASHBOARD_CACHE_SECONDS = 600.0
PASSWORD_ITERATIONS = 390_000
EMAIL_PATTERN = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")
PUBLIC_COMMUNITY_BOARD = "公共留學板"
LEGACY_PUBLIC_COMMUNITY_BOARD = "一般留學討論"
CGU_COMMUNITY_BOARD = "長庚大學"
HOME_UNIVERSITY_BOARDS = {item.school_name for item in SUPPORTED_UNIVERSITIES}


_school_image_manifest_cache: tuple[tuple[str, tuple[int, int] | None] | None, dict[tuple[str, str], dict[str, object]]] = (None, {})


def _load_school_image_manifest() -> dict[tuple[str, str], dict[str, object]]:
    global _school_image_manifest_cache
    from .school_identity import VisualRecordIndex
    sig = file_signature(SCHOOL_IMAGE_MANIFEST)
    if sig is None:
        return {}
    key = (str(SCHOOL_IMAGE_MANIFEST), sig)
    if _school_image_manifest_cache[0] == key and _school_image_manifest_cache[1]:
        return _school_image_manifest_cache[1]
    try:
        payload = json.loads(SCHOOL_IMAGE_MANIFEST.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    index = VisualRecordIndex({
        (school_identity_key(str(item.get("school_name", ""))), str(item.get("country") or "")): item
        for item in payload.get("schools", [])
        if isinstance(item, dict) and item.get("school_name")
    })
    _school_image_manifest_cache = (key, index)
    return index


def _attach_school_images(
    dashboard: StudentDashboard,
    *,
    base_url: str,
) -> StudentDashboard:
    if dashboard.school_name == NCU.school_name:
        from .ncu_completion import attach_campus_photos
        return attach_campus_photos(dashboard, base_url=base_url)
    if dashboard.school_name == "淡江大學":
        from .tku_assets import attach_images
        return attach_images(dashboard,base_url)
    visuals = _load_school_image_manifest()
    base = base_url.rstrip("/")
    partners = []
    for school in dashboard.partner_universities:
        if dashboard.school_name == CCU.school_name and "ccu_completion" in school.reference_data:
            from .ccu_campus_assets import attach_reviewed_image
            partners.append(attach_reviewed_image(school, base))
            continue
        visual = visuals.get((school.school_name, school.country or ""))
        if not visual:
            partners.append(school)
            continue
        if visual.get("status") != "verified":
            partners.append(school.model_copy(update={
                "image_url": None,
                "image_source_url": None,
                "image_page_url": visual.get("official_page_url") or None,
                "image_status": str(visual.get("status") or "missing"),
            }))
            continue
        local_path = str(visual.get("local_path") or "")
        image_url = f"{base}{local_path}" if local_path.startswith("/") else local_path
        partners.append(
            school.model_copy(
                update={
                    "image_url": image_url or None,
                    "image_source_url": visual.get("image_source_url") or None,
                    "image_page_url": visual.get("official_page_url") or None,
                    "image_status": "verified",
                }
            )
        )
    return dashboard.model_copy(update={"partner_universities": partners})


def _normalize_email(value: str) -> str:
    email = value.strip().lower()
    if not EMAIL_PATTERN.fullmatch(email):
        raise HTTPException(status_code=422, detail="請輸入有效的 Email。")
    return email


def _normalize_text(value: str | None) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip().lower()


def _hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), salt, PASSWORD_ITERATIONS
    )
    return f"pbkdf2_sha256${PASSWORD_ITERATIONS}${salt.hex()}${digest.hex()}"


def _verify_password(password: str, encoded: str | None) -> bool:
    if not encoded:
        return False
    try:
        algorithm, iterations, salt_hex, expected_hex = encoded.split("$", 3)
        if algorithm != "pbkdf2_sha256":
            return False
        actual = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            bytes.fromhex(salt_hex),
            int(iterations),
        )
        return secrets.compare_digest(actual.hex(), expected_hex)
    except (TypeError, ValueError):
        return False


def _account_profile(account: UserAccount) -> AccountProfile:
    providers = [link.provider for link in account.provider_links]
    if account.password_hash and AuthProvider.EMAIL not in providers:
        providers.insert(0, AuthProvider.EMAIL)
    return AccountProfile(
        is_platform_admin=is_platform_admin(account),
        catalog_home_university=catalog_home_university(account),
        school_basis=school_basis(account),
        id=account.id,
        email=account.email,
        display_name=account.display_name,
        avatar_url=account.avatar_url,
        home_university=account.home_university,
        school_change_locked_until=school_change_locked_until(account),
        target_countries=account.target_countries,
        application_stage=account.application_stage,
        followed_boards=account.followed_boards,
        notification_preferences=account.notification_preferences,
        content_updates_seen_at=account.content_updates_seen_at,
        email_verified=account.email_verified,
        school_email_verified=account.school_email_verified,
        student_status_verified=account.student_status_verified,
        verified_university=account.verified_university,
        verified_department=account.verified_department,
        student_verification_method=account.student_verification_method,
        student_verified_at=account.student_verified_at,
        product_tier=account.product_tier,
        providers=providers,
        created_at=account.created_at,
        updated_at=account.updated_at,
    )


PRODUCTION_PERSISTENCE_BACKENDS: dict[str, str] = {
    "account": "supabase",
    "content_governance": "supabase",
    "destination_review": "supabase",
    "document_vault": "supabase-private-storage",
    "form_drafts": "supabase-encrypted",
    "transient_auth": "supabase",
    "public_community": "supabase",
    "community_suspension": "supabase",
    "workflow_issue_reports": "supabase",
    "analytics": "supabase",
    "feedback": "supabase",
}


def _enabled_auth_methods() -> frozenset[str]:
    """Sign-in methods open to visitors; Google only unless a deployment adds more."""
    raw = os.environ.get("EXCHANGE_AUTH_METHODS", "google")
    return frozenset(item.strip().lower() for item in raw.split(",") if item.strip())


def _require_auth_method(method: str) -> None:
    if method not in _enabled_auth_methods():
        raise HTTPException(status_code=403, detail="目前只開放使用 Google 帳號登入或建立帳號。")


def _auth_cookie_secure_enabled(
    environment: Mapping[str, str] | None = None,
) -> bool:
    env = os.environ if environment is None else environment
    if env.get("EXCHANGE_ENVIRONMENT") == "production":
        return True
    val = env.get("EXCHANGE_AUTH_SECURE_COOKIE", "").strip().lower()
    return val in ("1", "true", "yes", "on")


def _browser_security_headers(
    environment: Mapping[str, str] | None = None,
) -> dict[str, str]:
    env = os.environ if environment is None else environment
    headers = {
        "X-Content-Type-Options": "nosniff",
        "X-Frame-Options": "DENY",
        "Referrer-Policy": "no-referrer",
        "Permissions-Policy": "camera=(), microphone=(), geolocation=(), payment=(), usb=()",
        "Content-Security-Policy": (
            "default-src 'self'; "
            "script-src 'self'; "
            "script-src-attr 'none'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https:; "
            "font-src 'self'; "
            "object-src 'none'; "
            "base-uri 'none'; "
            "form-action 'self'; "
            "frame-ancestors 'none'"
        ),
    }
    if measurement_id(env):
        headers["Content-Security-Policy"] = headers["Content-Security-Policy"].replace(
            "script-src 'self';", "script-src 'self' https://www.googletagmanager.com; connect-src 'self' https://*.google-analytics.com;")
    if env.get("EXCHANGE_ENVIRONMENT") == "production":
        headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    return headers


def _destination_profile_review_csv(
    rows: Sequence[DestinationProfileReviewRow],
) -> str:
    def _sanitize(val: object) -> str:
        s = str(val) if val is not None else ""
        if s and s[0] in ("=", "+", "-", "@"):
            return f"'{s}"
        return s

    output = StringIO()
    output.write("\ufeff")
    fieldnames = [
        "優先順序",
        "母校",
        "合作校",
        "國家",
        "城市／校區",
        "涵蓋狀態",
        "審核缺口",
        "來源數量",
        "官方來源名稱",
        "官方來源連結",
        "目前查核註記",
        "檔案內容雜湊",
        "快照指紋",
        "審查者 A",
        "審查者 B",
    ]
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()
    for row in rows:
        writer.writerow({
            "優先順序": _sanitize(getattr(row, "priority_order", 0)),
            "母校": _sanitize(getattr(row, "home_university", "")),
            "合作校": _sanitize(getattr(row, "school_name", "")),
            "國家": _sanitize(getattr(row, "country", "") or ""),
            "城市／校區": _sanitize(getattr(row, "city", "") or ""),
            "涵蓋狀態": _sanitize(getattr(row, "coverage_status", "")),
            "審核缺口": _sanitize(";".join(getattr(row, "review_gap_codes", []))),
            "來源數量": _sanitize(getattr(row, "source_count", 0)),
            "官方來源名稱": _sanitize(";".join(getattr(row, "source_titles", []))),
            "官方來源連結": _sanitize(";".join(getattr(row, "source_urls", []))),
            "目前查核註記": _sanitize(getattr(row, "coverage_note", "")),
            "檔案內容雜湊": _sanitize(getattr(row, "profile_content_hash", "")),
            "快照指紋": _sanitize(getattr(row, "snapshot_fingerprint", "")),
            "審查者 A": "",
            "審查者 B": "",
        })
    return output.getvalue()


def create_app(
    data_dir: Path | None = None,
    *,
    account_repository: Any = None,
    content_governance_store: Any = None,
    destination_profile_review_store: Any = None,
    document_vault_service: Any = None,
    form_draft_service: Any = None,
    email_verification_service: Any = None,
    transient_auth_store: Any = None,
    community_repository: Any = None,
    workflow_issue_report_repository: Any = None,
    analytics_repository: Any = None,
    feedback_repository: Any = None,
    seo_state_dir: Path | None = None,
) -> FastAPI:
    resolved_data_dir = Path(
        data_dir or os.environ.get("EXCHANGE_INFO_DATA_DIR") or DEFAULT_DATA_DIR
    )
    from .repositories import create_account_repository
    from .content_governance import create_content_governance_store
    from .destination_profile_review import create_destination_profile_review_store
    from .document_vault import create_document_vault_service
    from .form_drafts import create_form_draft_service
    from .email_verification import create_email_verification_service
    from .transient_auth import create_transient_auth_store
    from .community_repositories import create_community_repository
    from .workflow_issue_reports import create_workflow_issue_report_repository

    is_production = os.environ.get("EXCHANGE_ENVIRONMENT") == "production"
    seo_settings = SeoSettings.from_environment()

    if is_production:
        if account_repository and getattr(account_repository, "backend_name", None) != "supabase":
            raise RuntimeError("正式環境禁止使用本機持久層")
        if transient_auth_store and getattr(transient_auth_store, "backend_name", None) != "supabase":
            raise RuntimeError("正式環境禁止使用本機持久層")
        if document_vault_service:
            v_repo = getattr(document_vault_service, "repository", None)
            if getattr(v_repo, "backend_name", getattr(document_vault_service, "backend_name", None)) != "supabase-private-storage":
                raise RuntimeError("正式環境禁止使用本機持久層")
        if form_draft_service:
            d_repo = getattr(form_draft_service, "repository", None)
            if getattr(d_repo, "backend_name", getattr(form_draft_service, "backend_name", None)) != "supabase-encrypted":
                raise RuntimeError("正式環境禁止使用本機持久層")

    try:
        acc_repo = account_repository or create_account_repository(resolved_data_dir)
        gov_store = content_governance_store or create_content_governance_store(resolved_data_dir)
        dest_store = destination_profile_review_store or create_destination_profile_review_store(resolved_data_dir)
        vault_svc = document_vault_service or create_document_vault_service(resolved_data_dir)
        master_key = getattr(vault_svc, "master_key", b"v" * 32)
        draft_svc = form_draft_service or create_form_draft_service(resolved_data_dir, master_key)
        email_svc = email_verification_service or create_email_verification_service(acc_repo, resolved_data_dir)
        trans_store = transient_auth_store or create_transient_auth_store()
        comm_repo = community_repository or create_community_repository(resolved_data_dir)
        issue_repo = workflow_issue_report_repository or create_workflow_issue_report_repository(resolved_data_dir)
        analytics_on = os.environ.get("EXCHANGE_ANALYTICS", "on").strip().lower() not in {"off", "0", "false", "no"}
        analytics_service = AnalyticsService.from_environment(
            (analytics_repository or create_analytics_repository(resolved_data_dir))
            if analytics_on or analytics_repository is not None else None
        )
        feedback_service = FeedbackService(feedback_repository or create_feedback_repository(resolved_data_dir))
    except Exception as e:
        if is_production:
            raise RuntimeError("正式環境禁止使用本機持久層") from e
        raise

    backends = {
        "account": getattr(acc_repo, "backend_name", "jsonl"),
        "content_governance": getattr(gov_store, "backend_name", "local-jsonl"),
        "destination_review": getattr(dest_store, "backend_name", "local-jsonl"),
        "document_vault": getattr(getattr(vault_svc, "repository", None), "backend_name", getattr(vault_svc, "backend_name", "local-encrypted")),
        "form_drafts": getattr(getattr(draft_svc, "repository", None), "backend_name", getattr(draft_svc, "backend_name", "local-encrypted")),
        "transient_auth": getattr(trans_store, "backend_name", "memory"),
        "public_community": getattr(comm_repo, "backend_name", "jsonl"),
        "community_suspension": getattr(comm_repo, "backend_name", "jsonl"),
        "workflow_issue_reports": getattr(issue_repo, "backend_name", "local-jsonl"),
        "analytics": analytics_service.backend_name,
        "feedback": feedback_service.backend_name,
    }

    if is_production:
        for name, expected in PRODUCTION_PERSISTENCE_BACKENDS.items():
            actual = backends.get(name)
            if name == "analytics" and not analytics_service.enabled:
                continue  # EXCHANGE_ANALYTICS=off stores nothing, so there is nothing to protect
            if actual != expected:
                raise RuntimeError(f"正式環境禁止使用本機持久層：{name}={actual}（需要 {expected}）")

    warm_up: list = []  # filled once the catalogue loaders below exist
    def capacity_setting(name: str, default: int, maximum: int) -> int:
        raw = os.environ.get(name, str(default))
        if not raw.isdecimal() or not 1 <= int(raw) <= maximum:
            raise RuntimeError(f"{name} must be an integer from 1 to {maximum}")
        return int(raw)

    worker_threads = capacity_setting("EXCHANGE_WORKER_THREADS", 2, 128)
    catalogue_concurrency = capacity_setting("EXCHANGE_CATALOGUE_CONCURRENCY", 1, 16)
    catalogue_slots: asyncio.Semaphore | None = None
    catalogue_response_paths = {
        "/student-dashboard", "/coverage", "/destination-profiles", "/destination-profile",
        "/application-center/templates", "/application-center/catalog", "/application-period-options",
        "/application-workflow", "/advisor/plan", "/advisor/ask",
        "/school-life-context", "/school-data-completeness", "/student-experiences",
        "/partner-source-audit", "/schools", "/sitemap.xml", "/destinations",
        "/partners", "/cross-school-partners",
    }

    @asynccontextmanager
    async def lifespan(_app: FastAPI):
        nonlocal catalogue_slots
        # Large source graphs leave allocator arenas in each worker thread.
        # Defaults protect the 512 MiB host. Self-hosted operators can compare
        # larger bounds on staging; waiting catalogue requests remain asynchronous.
        from anyio.to_thread import current_default_thread_limiter
        thread_limiter = current_default_thread_limiter()
        previous_thread_tokens = thread_limiter.total_tokens
        thread_limiter.total_tokens = worker_threads
        catalogue_slots = asyncio.Semaphore(catalogue_concurrency)
        warming_task = None
        if warm_up and os.environ.get("EXCHANGE_WARM_CACHES", "").strip().lower() in {"1", "on", "true", "yes"}:
            warming_task = asyncio.create_task(warm_up[0](), name="warm-caches")
        _app.state.cache_warmup_task = warming_task
        try:
            yield
        finally:
            if warming_task is not None:
                warming_task.cancel()
                with suppress(asyncio.CancelledError):
                    await warming_task
            catalogue_slots = None
            thread_limiter.total_tokens = previous_thread_tokens
            analytics_service.flush_api_metrics()  # keep the last minute of request counts on a clean shutdown

    app = FastAPI(
        title="Taiwan University Exchange Guide",
        version="0.1.0",
        description="Structured exchange-application information for supported universities in Taiwan.",
        lifespan=lifespan,
        docs_url=None,
        redoc_url=None,
    )
    install_openapi_contract(app)
    @app.get('/docs', response_class=HTMLResponse, include_in_schema=False)
    def api_contract_page():
        return HTMLResponse('<!doctype html><html lang="zh-Hant"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>API contract</title></head><body><main><h1>API contract</h1><p>機器可讀取的 API 結構、欄位及限制。</p><a href="/openapi.json">下載 OpenAPI JSON</a></main></body></html>')

    @app.get('/redoc', include_in_schema=False)
    def legacy_api_contract_page():
        return RedirectResponse('/docs', status_code=307)
    app.state.account_repository = acc_repo
    app.state.content_governance_store = gov_store
    app.state.destination_profile_review_store = dest_store
    app.state.document_vault_service = vault_svc
    app.state.form_draft_service = draft_svc
    app.state.email_verification_service = email_svc
    app.state.transient_auth_store = trans_store
    app.state.community_repository = comm_repo
    app.state.workflow_issue_report_repository = issue_repo
    app.state.analytics = analytics_service
    app.state.feedback_service = feedback_service
    app.state.persistence_backends = PRODUCTION_PERSISTENCE_BACKENDS if is_production else backends
    catalog_request: ContextVar[Request | None] = ContextVar("catalog_request", default=None)
    seo_settings = SeoSettings.from_environment()

    app.add_middleware(ApiMetricsMiddleware, service=analytics_service)

    @app.middleware("http")
    async def add_security_headers(request: Request, call_next):
        context_token = catalog_request.set(request)
        try:
            if catalogue_slots is not None and (
                request.url.path in catalogue_response_paths
                or request.url.path.startswith(
                    ("/schools/", "/sitemaps/", "/destinations/", "/partners/", "/cross-school-partners/")
                )
            ):
                async with catalogue_slots:
                    response = await call_next(request)
            else:
                response = await call_next(request)
        finally:
            catalog_request.reset(context_token)
        for key, value in _browser_security_headers().items():
            response.headers.setdefault(key, value)
        path = request.url.path
        if (
            not seo_settings.indexable
            or response.status_code >= 400
            or not (
                path in {"/", "/schools", "/partners", "/privacy", "/terms", "/robots.txt", "/sitemap.xml", *EDITORIAL_PATHS}
                or path.startswith(("/schools/", "/sitemaps/", "/partners/"))
            )
        ):
            response.headers["X-Robots-Tag"] = "noindex, nofollow"
        if path.startswith("/static/") and response.status_code == 200:
            response.headers.setdefault("Cache-Control", _static_cache_control(path, "v" in request.query_params))
        if (
            path in (
                "/auth/session",
                "/auth/me",
                "/auth/me/export",
                "/account/workspace",
                "/account/vault/documents",
            )
            or path.startswith("/account/")
            or path.startswith("/auth/me")
            or getattr(request.state, "catalog_access_checked", False)
        ):
            response.headers["Cache-Control"] = "private, no-store, max-age=0"
            response.headers["Pragma"] = "no-cache"
            existing_vary = [
                item.strip()
                for item in response.headers.get("Vary", "").split(",")
                if item.strip()
            ]
            for v in ("Cookie", "Authorization", "X-Anonymous-Token"):
                if not any(item.casefold() == v.casefold() for item in existing_vary):
                    existing_vary.append(v)
            response.headers["Vary"] = ", ".join(existing_vary)
        return response

    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
    partner_cache: dict[str, list] = {}
    partner_cache_lock = threading.Lock()
    cgu_catalogue = None
    cgu_catalogue_lock = threading.Lock()

    def cgu_catalogue_view() -> CatalogueView:
        nonlocal cgu_catalogue
        if cgu_catalogue is None:
            with cgu_catalogue_lock:
                if cgu_catalogue is None:
                    cgu_catalogue = create_cgu_catalogue(resolved_data_dir)
                    app.state.cgu_catalogue = cgu_catalogue
        return cgu_catalogue.view()

    experience_collection_lock = threading.Lock()
    workflow_collection_lock = app.state.content_review_lock = threading.RLock()
    community_lock = threading.Lock()
    auth_lock = threading.RLock()
    oauth_states: dict[str, tuple[AuthProvider, datetime, str]] = {}

    def account_session(account: UserAccount) -> AccountSession:
        access_token = secrets.token_urlsafe(40)
        expires_at = utc_now() + timedelta(days=30)
        record = AccountSessionRecord(
            account_id=account.id,
            token_hash=hashlib.sha256(access_token.encode("utf-8")).hexdigest(),
            expires_at=expires_at,
        )
        if hasattr(app.state, "account_repository") and hasattr(app.state.account_repository, "save_session"):
            app.state.account_repository.save_session(record)
        else:
            with auth_lock:
                active = [
                    row
                    for row in load_account_sessions(resolved_data_dir)
                    if row.expires_at > utc_now()
                ]
                save_account_sessions([*active, record], resolved_data_dir)
        return AccountSession(
            access_token=access_token,
            expires_at=expires_at,
            profile=_account_profile(account),
        )

    def set_auth_cookie(response: Response, session: AccountSession) -> None:
        response.set_cookie(
            AUTH_COOKIE_NAME,
            session.access_token,
            max_age=30 * 24 * 60 * 60,
            httponly=True,
            secure=_auth_cookie_secure_enabled(),
            samesite="lax",
            path="/",
        )

    def request_token(request: Request) -> str | None:
        authorization = request.headers.get("Authorization", "")
        if authorization.lower().startswith("bearer "):
            return authorization[7:].strip()
        return request.cookies.get(AUTH_COOKIE_NAME)

    def authenticated_account(request: Request) -> tuple[UserAccount, AccountSessionRecord]:
        access_token = request_token(request)
        if not access_token:
            raise HTTPException(status_code=401, detail="請先登入帳號。")
        token_hash = hashlib.sha256(access_token.encode("utf-8")).hexdigest()
        session = None
        if hasattr(app.state, "account_repository") and hasattr(app.state.account_repository, "find_session_by_token_hash"):
            session = app.state.account_repository.find_session_by_token_hash(token_hash)
            if session and session.expires_at <= utc_now():
                session = None
        if session is None:
            session = next(
                (
                    row
                    for row in load_account_sessions(resolved_data_dir)
                    if row.expires_at > utc_now()
                    and secrets.compare_digest(row.token_hash, token_hash)
                ),
                None,
            )
        if session is None:
            raise HTTPException(status_code=401, detail="登入狀態已失效，請重新登入。")
        account = None
        if hasattr(app.state, "account_repository") and hasattr(app.state.account_repository, "find_account_by_id"):
            account = app.state.account_repository.find_account_by_id(session.account_id)
        if account is None:
            account = next(
                (row for row in load_user_accounts(resolved_data_dir) if row.id == session.account_id),
                None,
            )
        if account is None:
            raise HTTPException(status_code=401, detail="找不到這個帳號。")
        return account, session

    def content_admin_emails() -> set[str]:
        raw = os.environ.get("EXCHANGE_CONTENT_ADMIN_EMAILS", "")
        return {item.strip().lower() for item in raw.split(",") if item.strip()}

    def is_content_admin(account: UserAccount) -> bool:
        if is_platform_admin(account):
            return True
        if not account.email:
            return False
        return account.email.strip().lower() in content_admin_emails()

    def authenticated_content_admin(request: Request) -> tuple[UserAccount, AccountSessionRecord]:
        account, session = authenticated_account(request)
        if not is_content_admin(account):
            raise HTTPException(status_code=403, detail="此功能僅限內容管理員使用。")
        return account, session

    register_notification_routes(
        app,
        authenticated_account,
        authenticated_content_admin,
        catalogue_source_provider=lambda: cgu_catalogue_view().source,
    )
    register_workflow_review_routes(app, authenticated_content_admin)
    register_content_governance_routes(app, authenticated_content_admin,
                                      data_dir=resolved_data_dir, static_dir=STATIC_DIR)
    register_tku_eligibility_routes(app)

    def published_destination_profiles(home_university: str | None = None):
        from .governance_commands import local_governance_lock
        with app.state.content_review_lock, local_governance_lock(resolved_data_dir):
            home_key = normalize_school(home_university) if home_university else None
            promotions = dest_store.list_promotion_events()
            rollbacks = dest_store.list_rollback_events()
            if home_key:
                promotions = [row for row in promotions if normalize_school(row.home_university) == home_key]
                rollbacks = [row for row in rollbacks if normalize_school(row.home_university) == home_key]
            return apply_destination_profile_promotions(
                load_destination_profiles(resolved_data_dir, include_bundled_baseline=True,
                                          home_university=home_university),
                promotions, rollbacks)
    analytics_countries: dict[str, Any] = {"at": 0.0, "value": {}}

    def catalogue_countries() -> dict[str, str]:
        """partner school -> country, for the analytics report only; refreshed at most hourly."""
        if analytics_countries["value"] and time.monotonic() - analytics_countries["at"] < 3600:
            return analytics_countries["value"]
        mapping: dict[str, str] = {}
        for university in SUPPORTED_UNIVERSITIES:
            try:
                for partner in partners_for_university(university):
                    if partner.country:
                        mapping.setdefault(partner.school_name, partner.country)
            except Exception:
                continue
        analytics_countries.update(at=time.monotonic(), value=mapping)
        return mapping

    register_analytics_routes(
        app, analytics_service, authenticated_content_admin,
        static_dir=STATIC_DIR, school_countries=catalogue_countries,
    )

    def optional_account(request: Request) -> UserAccount | None:
        """Whoever is signed in, or nobody: the feedback form is open to everyone."""
        try:
            return authenticated_account(request)[0]
        except HTTPException:
            return None

    register_feedback_routes(
        app, feedback_service, authenticated_content_admin, optional_account, static_dir=STATIC_DIR,
    )
    register_legal_pages(app, STATIC_DIR)

    def save_account_record(updated: UserAccount) -> UserAccount:
        if hasattr(app.state, "account_repository") and hasattr(app.state.account_repository, "save_account"):
            app.state.account_repository.save_account(updated)
            return updated
        with auth_lock:
            save_user_accounts(
                [
                    updated if row.id == updated.id else row
                    for row in load_user_accounts(resolved_data_dir)
                ],
                resolved_data_dir,
            )
        return updated

    def calendar_status(account: UserAccount, request: Request) -> CalendarSyncStatus:
        if not account.calendar_feed_token:
            return CalendarSyncStatus(enabled=False, event_count=len(account.calendar_events))
        public_base = public_base_url(request)
        subscription_url = (
            f"{public_base}/calendar/feed/{account.calendar_feed_token}.ics"
        )
        webcal_url = re.sub(r"^https?://", "webcal://", subscription_url)
        return CalendarSyncStatus(
            enabled=True,
            subscription_url=subscription_url,
            webcal_url=webcal_url,
            event_count=len(account.calendar_events),
            last_synced_at=account.calendar_last_synced_at,
        )

    def provider_settings(provider: AuthProvider) -> dict[str, str] | None:
        if provider == AuthProvider.GOOGLE:
            client_id = os.environ.get("GOOGLE_OAUTH_CLIENT_ID", "").strip()
            secret = os.environ.get("GOOGLE_OAUTH_CLIENT_SECRET", "").strip()
            return {"client_id": client_id, "secret": secret} if client_id and secret else None
        if provider == AuthProvider.FACEBOOK:
            client_id = os.environ.get("FACEBOOK_APP_ID", "").strip()
            secret = os.environ.get("FACEBOOK_APP_SECRET", "").strip()
            return {"client_id": client_id, "secret": secret} if client_id and secret else None
        return None

    def oauth_redirect_uri(request: Request, provider: AuthProvider) -> str:
        return f"{public_base_url(request)}/auth/oauth/{provider.value}/callback"

    def oauth_account(
        provider: AuthProvider,
        subject: str,
        email: str | None,
        display_name: str,
        avatar_url: str | None,
        email_trusted: bool = False,
    ) -> UserAccount:
        normalized_email = email.strip().lower() if email else None
        with auth_lock:
            accounts = load_user_accounts(resolved_data_dir)
            account = next(
                (
                    row
                    for row in accounts
                    if any(
                        link.provider == provider and link.subject == subject
                        for link in row.provider_links
                    )
                ),
                None,
            )
            if account is None and normalized_email:
                account = next(
                    (row for row in accounts if row.email == normalized_email), None
                )
            if account is None:
                inferred = school_from_email(normalized_email) if email_trusted else None
                account = UserAccount(
                    email=normalized_email,
                    display_name=(display_name or "留學同學")[:30],
                    avatar_url=avatar_url,
                    email_verified=bool(email_trusted and normalized_email),
                    home_university=inferred.school_name if inferred else HOME_UNIVERSITY_UNSET,
                    provider_links=[AccountProviderLink(provider=provider, subject=subject)],
                )
                accounts.append(account)
            else:
                links = list(account.provider_links)
                if not any(
                    link.provider == provider and link.subject == subject for link in links
                ):
                    links.append(AccountProviderLink(provider=provider, subject=subject))
                updates: dict[str, object] = {
                    "email": account.email or normalized_email,
                    "avatar_url": account.avatar_url or avatar_url,
                    "provider_links": links,
                    "updated_at": utc_now(),
                }
                account = account.model_copy(update=updates)
                accounts = [account if row.id == account.id else row for row in accounts]
            save_user_accounts(accounts, resolved_data_dir)
            return account

    def university_for(school: str | None) -> UniversityProfile:
        """Any visitor may read any supported school's catalogue; an account only sets the default."""
        request = catalog_request.get()
        account = None
        if request is not None:
            # A named public catalogue is identical for guests and signed-in
            # visitors. Only resolving the account's default school needs a DB
            # lookup. Keep authenticated requests private in browser/proxy caches.
            if request_token(request):
                request.state.catalog_access_checked = True
            account = getattr(request.state, "catalog_account", None)
            if school is None and account is None and request_token(request):
                try:
                    account, _ = authenticated_account(request)
                except HTTPException as exc:
                    if exc.status_code != 401:
                        raise
                    # An expired session still gets the public catalogue.
                if account is not None:
                    request.state.catalog_account = account
            if account is not None:
                # The default school depends on the account, so shared caches must not keep this.
                request.state.catalog_access_checked = True
        if school is None and account is not None:
            school = catalog_home_university(account)
        try:
            return require_university(school)
        except ValueError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    def partners_for_university(school: str | UniversityProfile | None) -> list:
        university = university_for(
            school.school_name if isinstance(school, UniversityProfile) else school
        )
        if university.id == CGU.id:
            view = cgu_catalogue_view()
            if view.source.status == "unavailable":
                raise HTTPException(status_code=503, detail="長庚合作校來源暫不可用，尚無可用的歷次資料；請稍後重試。", headers={"Retry-After": "60"})
            return apply_partner_research(view.partners, load_partner_research(resolved_data_dir), home_university=university.school_name, copy_nested=False)
        if university.id == "tku":
            # Window state is time-sensitive across dashboards, advisors and plans.
            return apply_partner_research(
                fetch_tku_partner_universities(),
                load_partner_research(resolved_data_dir),
                home_university=university.school_name,
                copy_nested=False,
            )
        if university.id not in partner_cache:
            with partner_cache_lock:
                if university.id not in partner_cache:
                    partner_cache[university.id] = (
                        fetch_ccu_partner_universities()
                        if university.id == "ccu"
                        else fetch_ncu_partner_universities()
                        if university.id == NCU.id
                        else fetch_ntu_partner_universities()
                        if university.id == NTU.id
                        else fetch_ntpu_partner_universities()
                        if university.id == NTPU.id
                        else fetch_fju_partner_universities()
                        if university.id == FJU.id
                        else fetch_scu_partner_universities()
                        if university.id == SCU.id
                        else fetch_ntnu_partner_universities()
                        if university.id == NTNU.id
                        else fetch_cycu_partner_universities()
                        if university.id == CYCU.id
                        else fetch_ntust_partner_universities()
                        if university.id == NTUST.id
                        else fetch_yzu_partner_universities()
                        if university.id == YZU.id
                        else fetch_fcu_partner_universities()
                        if university.id == FCU.id
                        else fetch_nsysu_partner_universities()
                        if university.id == NSYSU.id
                        else fetch_nchu_partner_universities()
                        if university.id == NCHU.id
                        else fetch_ntut_partner_universities()
                        if university.id == NTUT.id
                        else fetch_nccu_partner_universities()
                        if university.id == NCCU.id
                        else fetch_ncku_partner_universities()
                        if university.id == NCKU.id
                        else fetch_nycu_partner_universities()
                        if university.id == NYCU.id
                        else fetch_nthu_partner_universities()
                        if university.id == NTHU.id
                        else fetch_pccu_partner_universities()
                        if university.id == PCCU.id
                        else fetch_wzu_partner_universities()
                        if university.id == WZU.id
                        else fetch_nkust_partner_universities()
                        if university.id == NKUST.id
                        else fetch_yuntech_partner_universities()
                        if university.id == YUNTECH.id
                        else fetch_ntou_partner_universities()
                        if university.id == NTOU.id
                        else []
                    )
        return apply_partner_research(
            partner_cache[university.id],
            load_partner_research(resolved_data_dir),
            home_university=university.school_name,
            copy_nested=False,
        )

    def workflows_for_university(
        school: str | UniversityProfile | None,
    ) -> list[UniversityApplicationWorkflow]:
        university = university_for(
            school.school_name if isinstance(school, UniversityProfile) else school
        )
        home_key = normalize_school(university.school_name)
        if hasattr(app.state, "content_governance_store") and hasattr(
            app.state.content_governance_store, "load_published_workflows"
        ):
            workflows = app.state.content_governance_store.load_published_workflows()
        else:
            workflows = merge_application_workflows(
                load_bundled_application_workflows(),
                load_application_workflows(resolved_data_dir),
            )
        from .content_governance import workflow_content_hash
        return [
            workflow.model_copy(
                update={
                    "issue_report_snapshot": workflow.issue_report_snapshot
                    or workflow_content_hash(workflow)
                }
            )
            for workflow in workflows
            if normalize_school(workflow.home_university) == home_key
        ]

    def pages_for_university(school: str | UniversityProfile | None):
        university = university_for(
            school.school_name if isinstance(school, UniversityProfile) else school
        )
        if university.id == "ccu":
            return ccu_processed_pages()
        if university.id == NCU.id:
            return ncu_processed_pages()
        if university.id == NTU.id:
            return ntu_processed_pages()
        if university.id == FJU.id:
            return fju_processed_pages()
        if university.id == SCU.id:
            return scu_processed_pages()
        if university.id == NTNU.id:
            return ntnu_processed_pages()
        if university.id == CYCU.id:
            return cycu_processed_pages()
        if university.id == NTUST.id:
            return ntust_processed_pages()
        if university.id == YZU.id:
            return yzu_processed_pages()
        if university.id == FCU.id:
            return fcu_processed_pages()
        if university.id == NSYSU.id:
            return nsysu_processed_pages()
        if university.id == NCHU.id:
            return nchu_processed_pages()
        if university.id == NTUT.id:
            return ntut_processed_pages()
        if university.id == NCCU.id:
            return nccu_processed_pages()
        if university.id == NCKU.id:
            return ncku_processed_pages()
        if university.id == NYCU.id:
            return nycu_processed_pages()
        if university.id == NTHU.id:
            return nthu_processed_pages()
        if university.id == PCCU.id:
            return pccu_processed_pages()
        if university.id == WZU.id:
            return wzu_processed_pages()
        if university.id == NKUST.id:
            return nkust_processed_pages()
        if university.id == YUNTECH.id:
            return yuntech_processed_pages()
        if university.id == NTOU.id:
            return ntou_processed_pages()
        return (
            ntpu_processed_pages()
            if university.id == NTPU.id
            else tku_processed_pages()
            if university.id == "tku"
            else load_processed_pages(resolved_data_dir)
        )

    def info_for_university(school: str | UniversityProfile | None) -> ExchangeInfo:
        university = university_for(
            school.school_name if isinstance(school, UniversityProfile) else school
        )
        if university.id == "ccu":
            return ccu_exchange_info(partners_for_university(university))
        if university.id == NTPU.id:
            return ntpu_exchange_info(partners_for_university(university))
        if university.id == NCU.id:
            return ncu_exchange_info(partners_for_university(university))
        if university.id == "tku":
            return tku_exchange_info(partners_for_university(university))
        if university.id == NTU.id:
            return ntu_exchange_info(partners_for_university(university))
        if university.id == FJU.id:
            return fju_exchange_info(partners_for_university(university))
        if university.id == SCU.id:
            return scu_exchange_info(partners_for_university(university))
        if university.id == NTNU.id:
            return ntnu_exchange_info(partners_for_university(university))
        if university.id == CYCU.id:
            return cycu_exchange_info(partners_for_university(university))
        if university.id == NTUST.id:
            return ntust_exchange_info(partners_for_university(university))
        if university.id == YZU.id:
            return yzu_exchange_info(partners_for_university(university))
        if university.id == FCU.id:
            return fcu_exchange_info(partners_for_university(university))
        if university.id == NSYSU.id:
            return nsysu_exchange_info(partners_for_university(university))
        if university.id == NCHU.id:
            return nchu_exchange_info(partners_for_university(university))
        if university.id == NTUT.id:
            return ntut_exchange_info(partners_for_university(university))
        if university.id == NCCU.id:
            return nccu_exchange_info(partners_for_university(university))
        if university.id == NCKU.id:
            return ncku_exchange_info(partners_for_university(university))
        if university.id == NYCU.id:
            return nycu_exchange_info(partners_for_university(university))
        if university.id == NTHU.id:
            return nthu_exchange_info(partners_for_university(university))
        if university.id == PCCU.id:
            return pccu_exchange_info(partners_for_university(university))
        if university.id == WZU.id:
            return wzu_exchange_info(partners_for_university(university))
        if university.id == NKUST.id:
            return nkust_exchange_info(partners_for_university(university))
        if university.id == YUNTECH.id:
            return yuntech_exchange_info(partners_for_university(university))
        if university.id == NTOU.id:
            return ntou_exchange_info(partners_for_university(university))
        return load_exchange_info(resolved_data_dir) or ExchangeInfo(school_name=CGU.school_name)

    dashboard_cache: dict[str, tuple[float, tuple, StudentDashboard]] = {}
    dashboard_cache_lock = threading.Lock()
    dashboard_build_lock = threading.Lock()  # one build at a time: a second visitor waits for it instead of repeating it
    dashboard_refreshing: set[str] = set()

    def build_cached_dashboard(university: UniversityProfile, signature: tuple) -> StudentDashboard:
        with dashboard_build_lock:
            with dashboard_cache_lock:
                cached = dashboard_cache.get(university.id)
            if cached and cached[1] == signature and time.monotonic() - cached[0] < DASHBOARD_CACHE_SECONDS:
                return cached[2]  # another request finished it while this one waited
            dashboard = build_student_dashboard(
                load_processed_pages(resolved_data_dir),
                load_exchange_info(resolved_data_dir),
                raw_files_dir=resolved_data_dir / "raw_files",
                fetch_partner_sheets=False,
            )
            with dashboard_cache_lock:
                dashboard_cache[university.id] = (time.monotonic(), signature, dashboard)
            return dashboard

    def refresh_dashboard_in_background(university: UniversityProfile, signature: tuple) -> None:
        with dashboard_cache_lock:
            if university.id in dashboard_refreshing:
                return
            dashboard_refreshing.add(university.id)

        def refresh() -> None:
            try:
                build_cached_dashboard(university, signature)
            except Exception:  # the visitors keep getting the previous copy
                logging.getLogger(__name__).exception("dashboard refresh failed")
            finally:
                with dashboard_cache_lock:
                    dashboard_refreshing.discard(university.id)

        threading.Thread(target=refresh, name="dashboard-refresh", daemon=True).start()

    def dashboard_for_university(school: str | UniversityProfile | None) -> StudentDashboard:
        university = university_for(
            school.school_name if isinstance(school, UniversityProfile) else school
        )
        if university.id == "ccu":
            return build_ccu_student_dashboard(partner_universities=partners_for_university(university))
        if university.id == NTPU.id:
            return build_ntpu_student_dashboard(
                partner_universities=partners_for_university(university)
            )
        if university.id == NCU.id:
            return build_ncu_student_dashboard(partner_universities=partners_for_university(university))
        if university.id == "tku":
            # Refresh window state on each request; a cached open round must close on time.
            return build_tku_student_dashboard()
        if university.id == NTU.id:
            return build_ntu_student_dashboard(partner_universities=partners_for_university(university))
        if university.id == FJU.id:
            return build_fju_student_dashboard(partner_universities=partners_for_university(university))
        if university.id == SCU.id:
            return build_scu_student_dashboard(partner_universities=partners_for_university(university))
        if university.id == NTNU.id:
            return build_ntnu_student_dashboard(partner_universities=partners_for_university(university))
        if university.id == CYCU.id:
            return build_cycu_student_dashboard(partner_universities=partners_for_university(university))
        if university.id == NTUST.id:
            return build_ntust_student_dashboard(partner_universities=partners_for_university(university))
        if university.id == YZU.id:
            return build_yzu_student_dashboard(partner_universities=partners_for_university(university))
        if university.id == FCU.id:
            return build_fcu_student_dashboard(partner_universities=partners_for_university(university))
        if university.id == NSYSU.id:
            return build_nsysu_student_dashboard(partner_universities=partners_for_university(university))
        if university.id == NCHU.id:
            return build_nchu_student_dashboard(partner_universities=partners_for_university(university))
        if university.id == NTUT.id:
            return build_ntut_student_dashboard(partner_universities=partners_for_university(university))
        if university.id == NCCU.id:
            return build_nccu_student_dashboard(partner_universities=partners_for_university(university))
        if university.id == NCKU.id:
            return build_ncku_student_dashboard(partner_universities=partners_for_university(university))
        if university.id == NYCU.id:
            return build_nycu_student_dashboard(partner_universities=partners_for_university(university))
        if university.id == NTHU.id:
            return build_nthu_student_dashboard(partner_universities=partners_for_university(university))
        if university.id == PCCU.id:
            return build_pccu_student_dashboard(partner_universities=partners_for_university(university))
        if university.id == WZU.id:
            return build_wzu_student_dashboard(partner_universities=partners_for_university(university))
        if university.id == NKUST.id:
            return build_nkust_student_dashboard(partner_universities=partners_for_university(university))
        if university.id == YUNTECH.id:
            return build_yuntech_student_dashboard(partner_universities=partners_for_university(university))
        if university.id == NTOU.id:
            return build_ntou_student_dashboard(partner_universities=partners_for_university(university))
        # The base dashboard parses official PDFs; partner rows are overlaid from the
        # shared source provider on every response, never retained in this cache.
        # Building this one parses a dozen official PDFs: 10 to 40 seconds on the free
        # host. The result is kept; once it is a few minutes old the next visitor still gets it at once while a fresh one
        # is built in the background. Only when the data files behind it were rewritten (or nothing was built yet) does
        # a visitor wait for a new one.
        paths = data_paths(resolved_data_dir)
        signature = (
            file_signature(paths["processed_pages"]),
            file_signature(paths["exchange_info"]),
            id(build_student_dashboard),
        )
        with dashboard_cache_lock:
            cached = dashboard_cache.get(university.id)
        if cached and cached[1] == signature:
            if time.monotonic() - cached[0] >= DASHBOARD_CACHE_SECONDS:
                refresh_dashboard_in_background(university, signature)
            base_dashboard = cached[2]
        else:
            base_dashboard = build_cached_dashboard(university, signature)
        view = cgu_catalogue_view()
        return base_dashboard.model_copy(deep=True, update={
            "partner_universities": apply_partner_research(view.partners, load_partner_research(resolved_data_dir), home_university=university.school_name, copy_nested=False),
            "catalogue_source": view.source,
        })

    async def warm_catalogue_caches() -> None:
        """Do the slow first-time work now, so the first visitor after a restart does not wait for it.

        On the free host that work took close to a minute of CPU (checking thousands of bundled translations, merging the
        workflow catalogue, building each school's dashboard). It only has to happen once per process.
        """
        from . import public_translation

        await asyncio.sleep(CACHE_WARM_UP_DELAY_SECONDS)  # let health become ready first
        steps = [
            public_translation._reference_translations,
            public_translation._bundled_machine_translations,
            public_translation._display_patterns,
            public_translation._identifier_pattern,
            load_bundled_application_workflows,
        ]
        for university in SUPPORTED_UNIVERSITIES:
            steps += [
                partial(partners_for_university, university),
                partial(workflows_for_university, university),
                partial(dashboard_for_university, university),
            ]
        started = time.monotonic()
        for step in steps:
            try:
                # Share the catalogue limit and worker arenas with real reads.
                # Release between steps so waiting visitors can make progress.
                async with catalogue_slots:
                    await run_in_threadpool(step)
            except Exception:  # a warm-up that fails only means the first visitor pays for that step
                logging.getLogger(__name__).exception("cache warm-up step failed")
        logging.getLogger(__name__).info("catalogue caches warmed in %.1f s", time.monotonic() - started)

    warm_up.append(warm_catalogue_caches)

    def partner_context_for_school(
        school: str,
        home_school: str | None = None,
    ) -> tuple[UniversityProfile, object]:
        normalized = normalize_school(school)
        scoped_university = university_for(home_school)
        # Without a named home school, a direct link may belong to any supported catalogue;
        # the visitor's own school is searched first.
        universities = [scoped_university]
        if not home_school:
            universities += [item for item in SUPPORTED_UNIVERSITIES if item.id != scoped_university.id]
        unavailable = None
        for university in universities:
            try:
                partners = partners_for_university(university)
            except HTTPException as error:
                if error.status_code != 503 or home_school:
                    raise
                unavailable = error
                continue
            for partner in partners:
                if normalize_school(partner.school_name) == normalized:
                    return university, partner
        if unavailable:
            raise unavailable
        raise HTTPException(status_code=404, detail="這所學校不在目前支援大學的當期合作校名單中。")

    def partner_for_school(school: str, home_school: str | None = None):
        return partner_context_for_school(school, home_school)[1]

    def anonymous_identity(identity_id: str | None, access_token: str | None) -> AnonymousIdentity:
        if not identity_id or not access_token:
            raise HTTPException(status_code=401, detail="需要匿名身分才能使用此功能。")
        token_hash = hashlib.sha256(access_token.encode("utf-8")).hexdigest()
        for identity in comm_repo.list_identities():
            if identity.id == identity_id and secrets.compare_digest(
                identity.access_token_hash, token_hash
            ):
                return identity
        raise HTTPException(status_code=401, detail="匿名身分已失效，請重新建立。")

    def is_blocked(left_id: str, right_id: str) -> bool:
        return any(
            {block.owner_id, block.target_id} == {left_id, right_id}
            for block in comm_repo.list_blocks()
        )

    def private_conversation_for(identity_id: str, conversation_id: str) -> PrivateConversation:
        conversation = next(
            (
                row
                for row in comm_repo.list_private_conversations()
                if row.id == conversation_id
            ),
            None,
        )
        if conversation is None:
            raise HTTPException(status_code=404, detail="找不到這段私訊。")
        if identity_id not in {conversation.sender_id, conversation.recipient_id}:
            raise HTTPException(status_code=403, detail="你無法查看這段私訊。")
        return conversation

    def seo_catalogue(university: UniversityProfile) -> tuple[list, object]:
        # Public pages are identical for signed-in and anonymous visitors. In
        # particular, never load private sessions through university_for().
        token = catalog_request.set(None)
        try:
            if university.id == CGU.id:
                # Pair records and provenance from one generation even if the
                # background source refresh finishes during this request.
                view = cgu_catalogue_view()
                if view.source.status == "unavailable":
                    raise HTTPException(503, "合作校資料暫不可用，請稍後重試。", headers={"Retry-After": "60"})
                partners = apply_partner_research(
                    view.partners, load_partner_research(resolved_data_dir),
                    home_university=university.school_name, copy_nested=False,
                )
                return partners, view.source
            partners = partners_for_university(university)
            return partners, None
        finally:
            catalog_request.reset(token)

    def public_partners_by_home() -> dict[str, list]:
        token = catalog_request.set(None)
        try:
            result: dict[str, list] = {}
            for university in SUPPORTED_UNIVERSITIES:
                try:
                    result[university.id] = list(partners_for_university(university))
                except Exception:
                    result[university.id] = []
            return result
        finally:
            catalog_request.reset(token)

    resolved_seo_state_dir = Path(
        seo_state_dir
        or os.environ.get("EXCHANGE_SEO_STATE_DIR")
        or (resolved_data_dir / "seo-state")
    )
    app.include_router(
        create_seo_router(seo_settings, seo_catalogue, ContentChanges(resolved_seo_state_dir))
    )

    @app.get("/", response_class=HTMLResponse)
    def frontend() -> HTMLResponse:
        return HTMLResponse(
            homepage_html(
                (STATIC_DIR / "index.html").read_text(encoding="utf-8"),
                seo_settings,
            ),
            headers={"Cache-Control": "no-store"},
        )

    @app.head("/", include_in_schema=False)
    def frontend_head() -> Response:
        return Response(status_code=200, headers={"Cache-Control": "no-store"})

    @app.get("/favicon.ico", response_class=FileResponse, include_in_schema=False)
    def favicon() -> FileResponse:
        # Browsers, search crawlers and link previews request this path directly, even for pages without a <link rel="icon">.
        return FileResponse(
            STATIC_DIR / "assets" / "brand" / "favicon.ico",
            media_type="image/x-icon",
            headers={"Cache-Control": "public, max-age=86400"},
        )

    @app.get("/health")
    def health() -> dict[str, object]:
        pages = load_processed_pages(resolved_data_dir)
        return {
            "status": "ok",
            "school": CGU.school_name,
            "supported_schools": [item.school_name for item in SUPPORTED_UNIVERSITIES],
            "pages": len(pages),
            "exchange_info_ready": load_exchange_info(resolved_data_dir) is not None,
        }

    @app.head("/health", include_in_schema=False)
    def health_head() -> Response:
        # Uptime monitors (and the free ones that keep a sleeping host awake) ask with HEAD by default; refusing it with 405
        # makes them report the site as down. Nothing to read for a HEAD, so it answers without touching any file.
        return Response(status_code=200)

    @app.get("/product/entitlements", response_model=ProductEntitlementSnapshot)
    def product_entitlements(request: Request) -> ProductEntitlementSnapshot:
        account = None
        token = request_token(request)
        if token:
            try:
                account, _ = authenticated_account(request)
            except HTTPException:
                account = None
        return resolve_product_entitlements(account)

    @app.post(
        "/auth/email-verification/request",
        response_model=EmailVerificationDispatch,
        status_code=202,
    )
    def request_email_verification(
        payload: EmailVerificationRequest,
    ) -> EmailVerificationDispatch:
        _require_auth_method("email")
        email = _normalize_email(payload.email)
        try:
            return app.state.email_verification_service.request_code(email)
        except EmailVerificationRateLimitError as exc:
            raise HTTPException(
                status_code=429,
                detail=str(exc),
                headers={"Retry-After": str(exc.retry_after_seconds)},
            ) from exc
        except EmailVerificationDeliveryError as exc:
            raise HTTPException(status_code=503, detail=str(exc)) from exc
        except EmailVerificationError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.post(
        "/auth/email-verification/confirm",
        response_model=EmailVerificationConfirmation,
    )
    def confirm_email_verification(
        payload: EmailVerificationConfirm,
    ) -> EmailVerificationConfirmation:
        email = _normalize_email(payload.email)
        try:
            return app.state.email_verification_service.confirm_code(email, payload.code)
        except EmailVerificationRateLimitError as exc:
            raise HTTPException(
                status_code=429,
                detail=str(exc),
                headers={"Retry-After": str(exc.retry_after_seconds)},
            ) from exc
        except EmailVerificationExpiredError as exc:
            raise HTTPException(status_code=410, detail=str(exc)) from exc
        except EmailVerificationError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.get("/auth/providers", response_model=list[AuthProviderStatus])
    def auth_providers() -> list[AuthProviderStatus]:
        methods = _enabled_auth_methods()
        return [
            AuthProviderStatus(
                provider=AuthProvider.EMAIL, enabled="email" in methods, label="使用 Email"
            ),
            AuthProviderStatus(
                provider=AuthProvider.GOOGLE,
                enabled="google" in methods and provider_settings(AuthProvider.GOOGLE) is not None,
                label="使用 Google 繼續",
            ),
            AuthProviderStatus(
                provider=AuthProvider.FACEBOOK,
                enabled="facebook" in methods and provider_settings(AuthProvider.FACEBOOK) is not None,
                label="使用 Facebook 繼續",
            ),
            AuthProviderStatus(
                provider=AuthProvider.APPLE,
                enabled=False,
                label="使用 Apple 繼續",
            ),
        ]

    @app.post("/auth/register", response_model=AccountSession, status_code=201)
    def register_account(
        payload: AccountRegister, response: Response
    ) -> AccountSession:
        _require_auth_method("email")
        email = _normalize_email(payload.email)
        display_name = payload.display_name.strip()
        _reject_contact_details(display_name)
        if not payload.accept_terms:
            raise HTTPException(status_code=422, detail="必須同意服務條款。")
        with auth_lock:
            existing = None
            if hasattr(app.state, "account_repository") and hasattr(
                app.state.account_repository, "find_account_by_email"
            ):
                existing = app.state.account_repository.find_account_by_email(email)
            if existing is None:
                accounts = load_user_accounts(resolved_data_dir)
                existing = next(
                    (row for row in accounts if row.email and row.email.casefold() == email),
                    None,
                )
            if existing is not None:
                raise HTTPException(status_code=409, detail="這個 Email 已經註冊。")

            if hasattr(app.state, "email_verification_service"):
                try:
                    app.state.email_verification_service.consume_registration_token(
                        email, payload.email_verification_token
                    )
                except EmailVerificationError as exc:
                    raise HTTPException(
                        status_code=400,
                        detail="Email 驗證碼或驗證權限無效，請重新驗證。",
                    ) from exc

            account = UserAccount(
                email=email,
                email_verified=True,
                password_hash=_hash_password(payload.password),
                display_name=display_name,
                student_status_verified=False,
                provider_links=[
                    AccountProviderLink(provider=AuthProvider.EMAIL, subject=email)
                ],
            )
            account = save_account_record(account)
            session = account_session(account)
        set_auth_cookie(response, session)
        return session

    @app.post("/auth/login", response_model=AccountSession)
    def login_account(payload: AccountLogin, response: Response) -> AccountSession:
        _require_auth_method("email")
        email = _normalize_email(payload.email)
        account = None
        if hasattr(app.state, "account_repository") and hasattr(
            app.state.account_repository, "find_account_by_email"
        ):
            account = app.state.account_repository.find_account_by_email(email)
        if account is None:
            account = next(
                (
                    row
                    for row in load_user_accounts(resolved_data_dir)
                    if row.email and row.email.casefold() == email
                ),
                None,
            )
        if account is None or not _verify_password(payload.password, account.password_hash):
            raise HTTPException(status_code=401, detail="Email 或密碼不正確。")
        session = account_session(account)
        set_auth_cookie(response, session)
        return session

    @app.post("/auth/logout", status_code=204)
    def logout_account(request: Request, response: Response) -> Response:
        access_token = request_token(request)
        if access_token:
            token_hash = hashlib.sha256(access_token.encode("utf-8")).hexdigest()
            repository = app.state.account_repository
            if hasattr(repository, "delete_session_by_token_hash"):
                # Revoke through the shared repository so every worker sees logout.
                repository.delete_session_by_token_hash(token_hash)
            else:
                with auth_lock:
                    save_account_sessions(
                        [row for row in load_account_sessions(resolved_data_dir)
                         if not secrets.compare_digest(row.token_hash, token_hash)],
                        resolved_data_dir,
                    )
        response.delete_cookie(AUTH_COOKIE_NAME, path="/")
        response.status_code = 204
        return response

    @app.get("/auth/session", response_model=AccountProfile | None)
    def auth_session(request: Request) -> AccountProfile | None:
        try:
            account, _ = authenticated_account(request)
        except HTTPException as exc:
            if exc.status_code == 401:
                return None
            raise
        return _account_profile(account)

    @app.get("/auth/me", response_model=AccountProfile)
    def auth_me(request: Request) -> AccountProfile:
        account, _ = authenticated_account(request)
        return _account_profile(account)

    @app.patch("/auth/me", response_model=AccountProfile)
    def update_auth_profile(
        payload: AccountProfileUpdate, request: Request
    ) -> AccountProfile:
        account, _ = authenticated_account(request)
        updates: dict[str, object] = {"updated_at": utc_now()}
        if payload.display_name is not None:
            display_name = payload.display_name.strip()
            _reject_contact_details(display_name)
            updates["display_name"] = display_name
        if "avatar_url" in payload.model_fields_set:
            updates["avatar_url"] = payload.avatar_url.strip() if payload.avatar_url else None
        if payload.home_university is not None:
            declared = payload.home_university.strip()
            if not declared:
                raise HTTPException(status_code=422, detail="請填寫就讀學校。")
            # A supported school is stored under its official name; any other school is kept
            # as typed so we can see which schools people ask for.
            supported = resolve_university(declared)
            new_school = supported.school_name if supported else declared
            if new_school != (account.home_university or "").strip():
                # Sending the school it already has changes nothing and does not restart the clock.
                locked_until = school_change_locked_until(account)
                if locked_until is not None:
                    raise HTTPException(
                        status_code=409,
                        detail=f"學校選定後 3 天內不能更換，{locked_until.astimezone(TAIPEI_TZ):%Y-%m-%d %H:%M} 之後才能修改。",
                    )
                updates["home_university"] = new_school
                updates["home_university_changed_at"] = utc_now()
        if payload.target_countries is not None:
            updates["target_countries"] = list(
                dict.fromkeys(
                    country.strip() for country in payload.target_countries if country.strip()
                )
            )[:8]
        if payload.application_stage is not None:
            updates["application_stage"] = payload.application_stage.strip()
        if payload.followed_boards is not None:
            updates["followed_boards"] = list(
                dict.fromkeys(
                    board.strip()
                    for board in payload.followed_boards
                    if board.strip()
                )
            )[:30]
        if payload.notification_preferences is not None:
            updates["notification_preferences"] = payload.notification_preferences
        if payload.content_updates_seen_at is not None:
            updates["content_updates_seen_at"] = payload.content_updates_seen_at

        patch_updates = {k: v for k, v in updates.items() if k != "updated_at"}
        if not patch_updates:
            return _account_profile(account)
        try:
            if hasattr(app.state, "account_repository") and hasattr(app.state.account_repository, "patch_account_fields"):
                updated = app.state.account_repository.patch_account_fields(account.id, patch_updates)
            else:
                updated = save_account_record(account.model_copy(update=updates))
        except AccountNotFoundError as exc:
            raise HTTPException(status_code=401, detail="帳號不存在或已被刪除。") from exc

        if updated is None:
            raise HTTPException(status_code=401, detail="帳號不存在或已被刪除。")

        if payload.display_name is not None:
            with auth_lock:
                save_anonymous_identities(
                    [
                        row.model_copy(update={"display_name": updated.display_name})
                        if row.account_id == updated.id
                        else row
                        for row in load_anonymous_identities(resolved_data_dir)
                    ],
                    resolved_data_dir,
                )
        if payload.home_university is not None:
            chosen = catalog_home_university(updated)
            analytics_service.emit(
                "school_choice", props={"school": chosen or "other", "supported": chosen is not None},
                home_school=chosen or "", school_basis=school_basis(updated) or "")
        return _account_profile(updated)

    def _check_calendar_subscription(account: UserAccount) -> None:
        if configured_product_release_mode() == ProductReleaseMode.PUBLIC:
            if not account.product_tier or account.product_tier != ProductAccessTier.SUBSCRIPTION:
                raise HTTPException(
                    status_code=403,
                    detail="外部日曆同步屬於進階功能，目前帳號尚未開放。",
                )

    @app.get("/calendar-sync", response_model=CalendarSyncStatus)
    def get_calendar_sync(request: Request, response: Response) -> CalendarSyncStatus:
        account, _ = authenticated_account(request)
        _check_calendar_subscription(account)
        response.headers["Cache-Control"] = "no-store"
        response.headers["X-Content-Type-Options"] = "nosniff"
        return calendar_status(account, request)

    @app.post("/calendar-sync/enable", response_model=CalendarSyncStatus)
    def enable_calendar_sync(request: Request, response: Response) -> CalendarSyncStatus:
        account, _ = authenticated_account(request)
        _check_calendar_subscription(account)
        response.headers["Cache-Control"] = "no-store"
        response.headers["X-Content-Type-Options"] = "nosniff"
        if not account.calendar_feed_token:
            token = secrets.token_urlsafe(32)
            now = utc_now()
            if hasattr(app.state, "account_repository") and hasattr(app.state.account_repository, "patch_account_fields"):
                account = app.state.account_repository.patch_account_fields(
                    account.id,
                    {"calendar_feed_token": token},
                )
            else:
                account = save_account_record(
                    account.model_copy(
                        update={
                            "calendar_feed_token": token,
                            "updated_at": now,
                        }
                    )
                )
        return calendar_status(account, request)

    @app.put("/calendar-sync/events", response_model=CalendarSyncStatus)
    def sync_calendar_events(
        payload: CalendarEventSyncRequest, request: Request, response: Response
    ) -> CalendarSyncStatus:
        account, _ = authenticated_account(request)
        _check_calendar_subscription(account)
        response.headers["Cache-Control"] = "no-store"
        response.headers["X-Content-Type-Options"] = "nosniff"
        feed_token = account.calendar_feed_token or secrets.token_urlsafe(32)
        now = utc_now()
        updates = {
            "calendar_feed_token": feed_token,
            "calendar_events": payload.events,
            "calendar_last_synced_at": now,
        }
        if hasattr(app.state, "account_repository") and hasattr(app.state.account_repository, "patch_account_fields"):
            try:
                account = app.state.account_repository.patch_account_fields(
                    account.id,
                    updates,
                    expected={"calendar_feed_token": account.calendar_feed_token},
                )
            except AccountConflictError as error:
                raise HTTPException(status_code=409, detail=str(error)) from error
        else:
            account = save_account_record(account.model_copy(update={**updates, "updated_at": now}))
        return calendar_status(account, request)

    @app.delete("/calendar-sync", response_model=CalendarSyncStatus)
    def disable_calendar_sync(request: Request, response: Response) -> CalendarSyncStatus:
        account, _ = authenticated_account(request)
        response.headers["Cache-Control"] = "no-store"
        response.headers["X-Content-Type-Options"] = "nosniff"
        updates = {
            "calendar_feed_token": None,
            "calendar_events": [],
            "calendar_last_synced_at": None,
        }
        if hasattr(app.state, "account_repository") and hasattr(app.state.account_repository, "patch_account_fields"):
            account = app.state.account_repository.patch_account_fields(account.id, updates)
        else:
            account = save_account_record(account.model_copy(update={**updates, "updated_at": utc_now()}))
        return CalendarSyncStatus(enabled=False)

    @app.get("/account/workspace", response_model=AccountApplicationWorkspaceEnvelope)
    def get_account_workspace(
        request: Request,
        response: Response,
        home_school: str = Query(default="長庚大學"),
    ) -> AccountApplicationWorkspaceEnvelope:
        account, _ = authenticated_account(request)
        response.headers["Cache-Control"] = "private, no-store, max-age=0"
        response.headers["X-Content-Type-Options"] = "nosniff"
        workspace_key = workspace_identity_key(home_school)
        existing = next(
            (
                row
                for row in account.application_workspaces
                if workspace_identity_key(row.home_school) == workspace_key
            ),
            None,
        )
        if existing is None:
            return AccountApplicationWorkspaceEnvelope(
                exists=False,
                workspace=AccountApplicationWorkspace(
                    home_school=home_school,
                    revision=0,
                    application_context=ApplicationCenterContext(school_name=home_school),
                ),
            )
        return AccountApplicationWorkspaceEnvelope(
            exists=True,
            workspace=existing,
        )

    @app.put("/account/workspace", response_model=AccountApplicationWorkspaceEnvelope)
    def put_account_workspace(
        request: Request,
        response: Response,
        payload: AccountApplicationWorkspace,
    ) -> AccountApplicationWorkspaceEnvelope:
        account, _ = authenticated_account(request)
        existing = next((row for row in account.application_workspaces
                         if workspace_identity_key(row.home_school) == workspace_identity_key(payload.home_school)), None)
        if existing:
            compatible_fields = ("discovery", "planning_availability", "preparation_tasks", "selection_conditions")
            if any(field not in payload.model_fields_set for field in compatible_fields):
                payload = payload.model_copy(update={field: getattr(existing, field) for field in compatible_fields if field not in payload.model_fields_set})
            old_events = {event.id: event for event in existing.deadline_events}
            planning_fields = ("effort_hours", "remaining_hours", "depends_on", "available_from", "waiting_reason", "document_id")
            payload = payload.model_copy(update={"deadline_events": [
                event.model_copy(update={field: getattr(old_events[event.id], field)
                                         for field in planning_fields if field not in event.model_fields_set})
                if event.id in old_events else event
                for event in payload.deadline_events
            ]})
        response.headers["Cache-Control"] = "private, no-store, max-age=0"
        response.headers["X-Content-Type-Options"] = "nosniff"
        if configured_product_release_mode() == ProductReleaseMode.PUBLIC:
            if not account.product_tier or account.product_tier != ProductAccessTier.SUBSCRIPTION:
                if len(payload.application_schools) > 1:
                    raise HTTPException(
                        status_code=403,
                        detail="免費方案同時只能進行一份申請計畫。",
                    )
        result = app.state.account_repository.commit_workspace(
            WorkspaceMutationRequest(
                account_id=account.id,
                expected_revision=payload.revision,
                workspace=payload,
                mutation_kind=WorkspaceMutationKind.WORKSPACE_REPLACE,
            )
        )
        if result.status == WorkspaceMutationStatus.CONFLICT:
            raise HTTPException(
                status_code=409,
                detail={
                    "code": "workspace_revision_conflict",
                    "current_workspace": (
                        result.workspace.model_dump(mode="json")
                        if result.workspace
                        else None
                    ),
                },
            )
        if result.status != WorkspaceMutationStatus.COMMITTED or result.workspace is None:
            raise HTTPException(
                status_code=400,
                detail="無法更新工作區狀態。",
            )
        return AccountApplicationWorkspaceEnvelope(
            exists=True,
            workspace=result.workspace,
        )

    @app.post("/account/submission-progress", response_model=AccountSubmissionProgress)
    def update_submission_progress(
        request: Request,
        response: Response,
        payload: SubmissionProgressTransitionRequest,
    ) -> AccountSubmissionProgress:
        account, _ = authenticated_account(request)
        workspace_key = workspace_identity_key(payload.home_school)
        existing_workspace = next(
            (
                row
                for row in account.application_workspaces
                if workspace_identity_key(row.home_school) == workspace_key
            ),
            None,
        )
        current_progress = (
            existing_workspace.submission_progress.get(payload.progress_key)
            if existing_workspace
            else None
        )
        try:
            updated_progress = transition_submission_progress(current_progress, payload)
        except ValueError as e:
            raise HTTPException(status_code=422, detail=str(e)) from e

        base_workspace = existing_workspace or AccountApplicationWorkspace(
            home_school=payload.home_school,
            revision=0,
            application_context=ApplicationCenterContext(school_name=payload.home_school),
        )
        expected_revision = base_workspace.revision
        mutation_result = app.state.account_repository.commit_workspace(
            WorkspaceMutationRequest(
                account_id=account.id,
                expected_revision=expected_revision,
                workspace=base_workspace,
                mutation_kind=WorkspaceMutationKind.SUBMISSION_PROGRESS_TRANSITION,
                progress_key=payload.progress_key,
                progress=updated_progress,
            )
        )
        if mutation_result.status == WorkspaceMutationStatus.CONFLICT:
            raise HTTPException(
                status_code=409,
                detail="送件進度版本衝突，請重新整理後再操作。",
            )
        if mutation_result.status != WorkspaceMutationStatus.COMMITTED or mutation_result.workspace is None:
            raise HTTPException(
                status_code=400,
                detail="無法更新送件進度。",
            )

        response.headers["Cache-Control"] = "private, no-store, max-age=0"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Workspace-Revision"] = str(mutation_result.workspace.revision)
        response.headers["X-Submission-Recorded-By"] = "student"
        response.headers["X-Platform-Submitted"] = "false"
        return updated_progress

    # -------------------------------------------------------------------------
    # Application Form Drafts & Document Vault
    # -------------------------------------------------------------------------

    @app.get(
        "/account/application-drafts",
        response_model=ApplicationFormDraftList,
    )
    def list_application_form_drafts(
        request: Request,
        response: Response,
        home_school: str = Query(default="長庚大學"),
    ) -> ApplicationFormDraftList:
        account, _ = authenticated_account(request)
        if not hasattr(app.state, "form_draft_service"):
            raise HTTPException(status_code=503, detail="表單草稿服務未啟用。")
        response.headers["Cache-Control"] = "private, no-store, max-age=0"
        return app.state.form_draft_service.list_drafts(account.id, home_school)

    @app.put(
        "/account/application-drafts/{template_id}",
        response_model=ApplicationFormDraft,
    )
    def save_application_form_draft(
        template_id: str,
        payload: ApplicationFormDraftSave,
        request: Request,
        response: Response,
    ) -> ApplicationFormDraft:
        account, _ = authenticated_account(request)
        if not hasattr(app.state, "form_draft_service"):
            raise HTTPException(status_code=503, detail="表單草稿服務未啟用。")

        # Reject sensitive values and raw file data
        for key, val in payload.profile.items():
            if key == "guardian_id_number" and val:
                raise HTTPException(status_code=422, detail="敏感欄位不得儲存於草稿。")
        for key, val in payload.answers.items():
            if isinstance(val, str) and (val.startswith("data:") or ";base64," in val):
                raise HTTPException(status_code=422, detail="附件檔案不得直接儲存於草稿欄位。")

        # Validate and enrich vault attachment references
        enriched_attachments: dict[str, list[ApplicationFormDraftAttachment]] = {}
        if payload.attachments:
            if not hasattr(app.state, "document_vault_service"):
                raise HTTPException(status_code=503, detail="私人文件服務未啟用。")
            vault_repo = getattr(app.state.document_vault_service, "repository", None)
            for field_id, refs in payload.attachments.items():
                enriched_list: list[ApplicationFormDraftAttachment] = []
                for ref in refs:
                    v_rec = vault_repo.find_version(account.id, ref.version_id) if vault_repo else None
                    if v_rec is None:
                        raise HTTPException(status_code=404, detail="找不到附件引用的私人文件版本。")
                    consents = vault_repo.list_consents(account.id, v_rec.document_id) if vault_repo else []
                    active_consent = next(
                        (
                            c
                            for c in consents
                            if c.version_id == v_rec.id
                            and c.expires_at > utc_now()
                            and c.revoked_at is None
                        ),
                        None,
                    )
                    if not active_consent:
                        raise HTTPException(status_code=422, detail="附件缺少有效的保存同意。")
                    file_name = app.state.document_vault_service._decrypt_text(
                        v_rec.file_name_ciphertext,
                        v_rec.file_name_nonce,
                        f"vault-filename:{v_rec.account_id}:{v_rec.document_id}:{v_rec.id}".encode(),
                    )
                    doc_rec = vault_repo.find_document(account.id, v_rec.document_id)
                    label = (
                        app.state.document_vault_service._decrypt_text(
                            doc_rec.label_ciphertext,
                            doc_rec.label_nonce,
                            f"vault-label:{doc_rec.account_id}:{doc_rec.id}".encode(),
                        )
                        if doc_rec
                        else file_name
                    )
                    enriched_list.append(
                        ApplicationFormDraftAttachment(
                            document_id=v_rec.document_id,
                            version_id=v_rec.id,
                            label=label,
                            file_name=file_name,
                            category=doc_rec.category if doc_rec else VaultDocumentCategory.OTHER,
                            purpose=active_consent.purpose,
                            retention_days=active_consent.retention_days,
                            expires_at=v_rec.retention_expires_at,
                        )
                    )
                enriched_attachments[field_id] = enriched_list

        validated_payload = (
            payload.model_copy(update={"attachments": enriched_attachments})
            if enriched_attachments
            else payload
        )
        response.headers["Cache-Control"] = "private, no-store, max-age=0"
        try:
            return app.state.form_draft_service.save_draft(account.id, template_id, validated_payload)
        except FormDraftConflictError as exc:
            raise HTTPException(
                status_code=409,
                detail={
                    "code": "application_draft_revision_conflict",
                    "current_draft": exc.current.model_dump(mode="json") if exc.current else None,
                },
            ) from exc
        except FormDraftError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc

    @app.delete(
        "/account/application-drafts/{template_id}",
        status_code=204,
    )
    def delete_application_form_draft(
        template_id: str,
        request: Request,
        response: Response,
        revision: int = Query(ge=1),
        home_school: str = Query(default="長庚大學"),
    ) -> Response:
        account, _ = authenticated_account(request)
        if not hasattr(app.state, "form_draft_service"):
            raise HTTPException(status_code=503, detail="表單草稿服務未啟用。")
        try:
            app.state.form_draft_service.delete_draft(
                account.id,
                home_school,
                template_id,
                revision=revision,
            )
            response.status_code = 204
            return response
        except FormDraftNotFoundError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except FormDraftConflictError as exc:
            raise HTTPException(
                status_code=409,
                detail={
                    "code": "application_draft_revision_conflict",
                    "current_draft": exc.current.model_dump(mode="json") if exc.current else None,
                },
            ) from exc

    def _require_vault_access(account: UserAccount) -> None:
        if not product_feature_enabled(account, ProductFeature.ENCRYPTED_DOCUMENT_VAULT):
            raise HTTPException(
                status_code=403,
                detail="私人文件庫為進階功能，請確認方案權限。",
            )

    @app.get(
        "/account/vault/documents",
        response_model=VaultDocumentList,
    )
    def list_private_vault_documents(
        request: Request, response: Response
    ) -> VaultDocumentList:
        account, _ = authenticated_account(request)
        _require_vault_access(account)
        if not hasattr(app.state, "document_vault_service"):
            raise HTTPException(status_code=503, detail="私人文件庫尚未啟用。")
        response.headers["Cache-Control"] = "private, no-store, max-age=0"
        return app.state.document_vault_service.list_documents(account.id)

    @app.post(
        "/account/vault/documents",
        response_model=VaultDocumentSummary,
        status_code=201,
    )
    async def create_private_vault_document(
        request: Request,
        label: str = Form(...),
        category: VaultDocumentCategory = Form(...),
        purpose: VaultConsentPurpose = Form(...),
        retention_days: int = Form(...),
        consent: str = Form(...),
        file: UploadFile = File(...),
    ) -> VaultDocumentSummary:
        account, _ = authenticated_account(request)
        _require_vault_access(account)
        if not hasattr(app.state, "document_vault_service"):
            raise HTTPException(status_code=503, detail="私人文件庫尚未啟用。")

        consent_bool = str(consent).strip().lower() in ("true", "1", "yes")
        if not consent_bool:
            raise HTTPException(status_code=422, detail="必須明確同意保存私人文件。")

        content = await file.read()
        try:
            return app.state.document_vault_service.store_version(
                account.id,
                file_name=file.filename or "document.bin",
                content=content,
                media_type=file.content_type,
                label=label,
                category=category,
                purpose=purpose,
                retention_days=retention_days,
                consent=consent_bool,
            )
        except (VaultConsentError, VaultValidationError) as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        except VaultError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.post(
        "/account/vault/documents/{document_id}/versions",
        response_model=VaultDocumentSummary,
        status_code=201,
    )
    async def create_private_vault_version(
        document_id: str,
        request: Request,
        purpose: VaultConsentPurpose = Form(...),
        retention_days: int = Form(...),
        consent: str = Form(...),
        file: UploadFile = File(...),
    ) -> VaultDocumentSummary:
        account, _ = authenticated_account(request)
        _require_vault_access(account)
        if not hasattr(app.state, "document_vault_service"):
            raise HTTPException(status_code=503, detail="私人文件庫尚未啟用。")

        consent_bool = str(consent).strip().lower() in ("true", "1", "yes")
        if not consent_bool:
            raise HTTPException(status_code=422, detail="必須明確同意保存私人文件版本。")

        content = await file.read()
        try:
            doc = app.state.document_vault_service.get_document(account.id, document_id)
            return app.state.document_vault_service.store_version(
                account.id,
                file_name=file.filename or "document.bin",
                content=content,
                media_type=file.content_type,
                label=doc.label,
                category=doc.category,
                purpose=purpose,
                retention_days=retention_days,
                consent=consent_bool,
                document_id=document_id,
            )
        except VaultNotFoundError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except (VaultConsentError, VaultValidationError) as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        except VaultError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.delete(
        "/account/vault/documents/{document_id}",
        status_code=204,
    )
    def delete_private_vault_document(
        document_id: str,
        request: Request,
        response: Response,
    ) -> Response:
        account, _ = authenticated_account(request)
        _require_vault_access(account)
        if not hasattr(app.state, "document_vault_service"):
            raise HTTPException(status_code=503, detail="私人文件庫尚未啟用。")
        try:
            app.state.document_vault_service.delete_document(account.id, document_id)
            response.status_code = 204
            return response
        except VaultNotFoundError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    @app.delete(
        "/account/vault/documents/{document_id}/versions/{version_id}",
    )
    def delete_private_vault_version(
        document_id: str,
        version_id: str,
        request: Request,
    ) -> VaultDocumentSummary | None:
        account, _ = authenticated_account(request)
        _require_vault_access(account)
        if not hasattr(app.state, "document_vault_service"):
            raise HTTPException(status_code=503, detail="私人文件庫尚未啟用。")
        try:
            app.state.document_vault_service.delete_version(account.id, document_id, version_id)
            try:
                return app.state.document_vault_service.get_document(account.id, document_id)
            except (VaultNotFoundError, VaultExpiredError):
                return None
        except VaultNotFoundError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    @app.post(
        "/account/vault/versions/{version_id}/download-grant",
        response_model=VaultDownloadGrant,
    )
    def create_private_vault_download_grant(
        version_id: str,
        request: Request,
    ) -> VaultDownloadGrant:
        account, _ = authenticated_account(request)
        _require_vault_access(account)
        if not hasattr(app.state, "document_vault_service"):
            raise HTTPException(status_code=503, detail="私人文件庫尚未啟用。")
        try:
            return app.state.document_vault_service.create_download_grant(account.id, version_id)
        except VaultNotFoundError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except (VaultExpiredError, VaultConsentError) as exc:
            raise HTTPException(status_code=410, detail=str(exc)) from exc

    @app.post("/account/vault/download")
    def download_private_vault_document(
        request: Request,
        download_token: str | None = Header(default=None, alias="X-Vault-Download-Token"),
    ) -> Response:
        account, _ = authenticated_account(request)
        _require_vault_access(account)
        if not download_token:
            raise HTTPException(status_code=403, detail="缺少私人文件下載授權。")
        if not hasattr(app.state, "document_vault_service"):
            raise HTTPException(status_code=503, detail="私人文件庫尚未啟用。")
        try:
            content, file_name, media_type = app.state.document_vault_service.download(
                account.id, download_token
            )
            response = Response(
                content=content,
                media_type=media_type,
            )
            response.headers["Cache-Control"] = "private, no-store, max-age=0"
            return response
        except (VaultAuthorizationError, VaultIntegrityError):
            raise HTTPException(status_code=403, detail="私人文件下載授權無效。")
        except (VaultExpiredError, VaultConsentError) as exc:
            raise HTTPException(status_code=410, detail=str(exc)) from exc
        except VaultNotFoundError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    @app.post(
        "/calendar/conflicts/analyze",
        response_model=CalendarConflictReport,
    )
    def analyze_calendar_conflicts(
        request: Request,
        response: Response,
        payload: CalendarConflictAnalysisRequest,
    ) -> CalendarConflictReport:
        account, _ = authenticated_account(request)
        if configured_product_release_mode() == ProductReleaseMode.PUBLIC:
            if not account.product_tier or account.product_tier != ProductAccessTier.SUBSCRIPTION:
                raise HTTPException(
                    status_code=403,
                    detail="此為進階功能，請升級訂閱後使用。",
                )
        response.headers["Cache-Control"] = "no-store"
        response.headers["X-Content-Type-Options"] = "nosniff"
        return build_calendar_conflict_report(payload.events)

    @app.post(
        "/calendar/tasks/schedule",
        response_model=CalendarTaskScheduleReport,
    )
    def schedule_calendar_tasks(
        request: Request,
        response: Response,
        payload: CalendarTaskScheduleRequest,
    ) -> CalendarTaskScheduleReport:
        account, _ = authenticated_account(request)
        if configured_product_release_mode() == ProductReleaseMode.PUBLIC:
            if not account.product_tier or account.product_tier != ProductAccessTier.SUBSCRIPTION:
                raise HTTPException(
                    status_code=403,
                    detail="此為進階功能，請升級訂閱後使用。",
                )
        response.headers["Cache-Control"] = "no-store"
        response.headers["X-Content-Type-Options"] = "nosniff"
        return build_calendar_task_schedule(payload.events, as_of=payload.as_of, availability=payload.availability)

    @app.get("/calendar/feed/{feed_token}.ics", response_class=PlainTextResponse)
    def calendar_subscription_feed(feed_token: str) -> PlainTextResponse:
        if len(feed_token) < 24 or len(feed_token) > 128:
            raise HTTPException(status_code=404, detail="找不到這個日曆。")
        account = None
        if hasattr(app.state, "account_repository") and hasattr(app.state.account_repository, "list_accounts"):
            account = next(
                (
                    row
                    for row in app.state.account_repository.list_accounts()
                    if row.calendar_feed_token
                    and secrets.compare_digest(row.calendar_feed_token, feed_token)
                ),
                None,
            )
        if account is None:
            account = next(
                (
                    row
                    for row in load_user_accounts(resolved_data_dir)
                    if row.calendar_feed_token
                    and secrets.compare_digest(row.calendar_feed_token, feed_token)
                ),
                None,
            )
        if account is None:
            raise HTTPException(status_code=404, detail="找不到這個日曆。")
        if configured_product_release_mode() == ProductReleaseMode.PUBLIC:
            if not account.product_tier or account.product_tier != ProductAccessTier.SUBSCRIPTION:
                raise HTTPException(status_code=404, detail="找不到這個日曆。")
        return PlainTextResponse(
            _calendar_feed_content(account.calendar_events, account=account),
            media_type="text/calendar; charset=utf-8",
            headers={
                "Cache-Control": "private, max-age=300",
                "Content-Disposition": 'inline; filename="exchange-application-calendar.ics"',
            },
        )

    @app.get("/auth/me/export")
    def export_auth_profile(request: Request) -> dict[str, object]:
        account, _ = authenticated_account(request)
        reports = (
            app.state.workflow_issue_report_repository.list_reports_for_account(account.id)
            if hasattr(app.state, "workflow_issue_report_repository")
            and hasattr(app.state.workflow_issue_report_repository, "list_reports_for_account")
            else []
        )
        return {
            "profile": _account_profile(account).model_dump(mode="json"),
            "community_identity_ids": [
                row.id
                for row in load_anonymous_identities(resolved_data_dir)
                if row.account_id == account.id
            ],
            "application_workflow_issue_reports": [
                row.model_dump(
                    mode="json",
                    exclude={"reporter_account_id", "mutation_id", "request_fingerprint"},
                )
                for row in reports
            ],
        }

    @app.delete("/auth/me", status_code=204)
    def delete_auth_profile(request: Request, response: Response,
        mutation_id: str | None = Header(default=None, alias='X-Account-Deletion-Mutation-ID', min_length=16, max_length=128),
    ) -> Response:
        if getattr(app.state.account_repository, "backend_name", None) == "supabase":
            # The production repository owns deletion and de-identification in
            # one existing RPC, including clients without a retry header.
            mutation_id = mutation_id or secrets.token_hex(16)
        if mutation_id:
            response.headers["X-Account-Deletion-Mutation-ID"] = mutation_id

        access_token = request_token(request)
        if not access_token:
            raise HTTPException(status_code=401, detail="請先登入帳號。")
        token_hash = hashlib.sha256(access_token.encode("utf-8")).hexdigest()

        session = None
        account = None
        if hasattr(app.state, "account_repository") and hasattr(
            app.state.account_repository, "find_session_by_token_hash"
        ):
            session = app.state.account_repository.find_session_by_token_hash(token_hash)
            if session:
                account = app.state.account_repository.find_account_by_id(session.account_id)

        if mutation_id and hasattr(app.state, "account_repository") and hasattr(
            app.state.account_repository, "commit_account_deletion"
        ):
            mutation = AccountDeletionMutationRequest(
                mutation_id=mutation_id,
                session_token_hash=token_hash,
                account_id=account.id if account else None,
                session_id=session.id if session else None,
                replacement_name="已刪除帳號",
            )
            if account and getattr(comm_repo, "backend_name", None) == "jsonl":
                authenticated_account(request)
                try:
                    cleanup_local_account_community(comm_repo, account.id)
                except CommunityRepositoryError as exc:
                    raise HTTPException(503, "社群資料清理尚未完成，請重試刪除帳號。") from exc
            result = app.state.account_repository.commit_account_deletion(mutation)
            del_headers = {"X-Account-Deletion-Mutation-ID": mutation_id}
            if result.status == AccountDeletionMutationStatus.IDEMPOTENCY_CONFLICT:
                raise HTTPException(
                    status_code=409,
                    detail="刪除帳號識別碼衝突。",
                    headers=del_headers,
                )
            if result.status == AccountDeletionMutationStatus.SESSION_INVALID and not getattr(
                result, "idempotent", False
            ):
                raise HTTPException(status_code=401, detail="請先登入帳號。", headers=del_headers)
            if result.status == AccountDeletionMutationStatus.COMMITTED:
                if getattr(result, "storage_object_keys", None):
                    try:
                        if hasattr(app.state, "document_vault_service") and hasattr(
                            app.state.document_vault_service, "repository"
                        ):
                            app.state.document_vault_service.repository.delete_objects(
                                result.storage_object_keys
                            )
                    except Exception as exc:
                        raise HTTPException(
                            status_code=503,
                            detail="刪除附件檔案失敗。",
                            headers=del_headers,
                        ) from exc
                if hasattr(app.state.account_repository, "complete_account_deletion_storage"):
                    app.state.account_repository.complete_account_deletion_storage(
                        mutation_id, token_hash
                    )
                target_acc_id = account.id if account else (getattr(result, "account_id", None) or (session.account_id if session else None))
                if target_acc_id:
                    comm_repo.purge_account_interactions(target_acc_id)
                    if hasattr(app.state, "form_draft_service") and hasattr(
                        app.state.form_draft_service, "purge_account"
                    ):
                        app.state.form_draft_service.purge_account(target_acc_id)
                    if hasattr(app.state, "document_vault_service") and hasattr(
                        app.state.document_vault_service, "purge_account"
                    ):
                        app.state.document_vault_service.purge_account(target_acc_id)
                response.delete_cookie(AUTH_COOKIE_NAME, path="/")
                response.headers["X-Account-Deletion-Mutation-ID"] = mutation_id
                response.status_code = 204
                return response

            # An incomplete atomic deletion must remain retriable. Falling
            # through to legacy local deletion would bypass its cleanup result.
            raise HTTPException(503, '帳號刪除尚未完成，請保留操作識別碼後重試。', headers=del_headers)

        account, _ = authenticated_account(request)
        try:
            cleanup_local_account_community(comm_repo, account.id)
        except CommunityRepositoryError as exc:
            raise HTTPException(503, "社群資料清理尚未完成，請重試刪除帳號。") from exc
        if hasattr(app.state, "form_draft_service") and hasattr(
            app.state.form_draft_service, "purge_account"
        ):
            app.state.form_draft_service.purge_account(account.id)
        if hasattr(app.state, "document_vault_service") and hasattr(
            app.state.document_vault_service, "purge_account"
        ):
            app.state.document_vault_service.purge_account(account.id)
        with auth_lock:
            save_user_accounts(
                [row for row in load_user_accounts(resolved_data_dir) if row.id != account.id],
                resolved_data_dir,
            )
            save_account_sessions(
                [
                    row
                    for row in load_account_sessions(resolved_data_dir)
                    if row.account_id != account.id
                ],
                resolved_data_dir,
            )
        if hasattr(app.state, "account_repository") and hasattr(app.state.account_repository, "delete_account"):
            app.state.account_repository.delete_account(account.id)
        comm_repo.purge_account_interactions(account.id)
        if hasattr(app.state, "workflow_issue_report_repository") and hasattr(
            app.state.workflow_issue_report_repository, "deidentify_reporter"
        ):
            app.state.workflow_issue_report_repository.deidentify_reporter(account.id)
        response.delete_cookie(AUTH_COOKIE_NAME, path="/")
        response.status_code = 204
        return response

    @app.post(
        "/auth/community-identity",
        response_model=AnonymousIdentitySession,
        status_code=201,
    )
    def account_community_identity(request: Request) -> AnonymousIdentitySession:
        return AnonymousIdentitySession(**create_discussion_identity(request))

    @app.get("/auth/oauth/{provider}/start", response_class=RedirectResponse)
    def oauth_start(
        provider: str,
        request: Request,
        terms: str | None = Query(
            default=None,
            max_length=32,
            description="The version of the terms and privacy policy the visitor ticked; sign-in does not start without it.",
        ),
    ) -> RedirectResponse:
        try:
            provider_name = AuthProvider(provider)
        except ValueError as exc:
            raise HTTPException(status_code=404, detail="不支援這個登入方式。") from exc
        _require_auth_method(provider_name.value)
        settings = provider_settings(provider_name)
        if settings is None:
            raise HTTPException(status_code=503, detail="此登入方式尚未設定平台金鑰。")
        if terms != TERMS_VERSION:
            # No state is created and nothing leaves for the provider: an account can only be created after the visitor
            # ticked the current terms. The page opens the sign-in dialog again with a reminder.
            return RedirectResponse(url="/#auth=terms", status_code=303)
        state_token = secrets.token_urlsafe(32)
        flow_secret = secrets.token_urlsafe(32)
        now = utc_now()
        state_hash = hashlib.sha256(state_token.encode("utf-8")).hexdigest()

        if hasattr(app.state, "transient_auth_store"):
            record = TransientAuthState(
                state_hash=state_hash,
                kind=TransientAuthStateKind.OAUTH_LOGIN,
                provider_id=provider_name.value,
                session_id=flow_secret,
                expires_at=now + timedelta(minutes=10),
            )
            try:
                app.state.transient_auth_store.start_oauth_state(
                    record,
                    client_fingerprint=client_fingerprint(request, master_key),
                    window_start=now - timedelta(minutes=10),
                    start_limit=20,
                    max_active=200,
                )
            except TransientAuthRateLimitError as exc:
                raise HTTPException(
                    status_code=429,
                    detail=str(exc),
                    headers={"Retry-After": "600"},
                ) from exc
            except TransientAuthCapacityError as exc:
                raise HTTPException(status_code=503, detail=str(exc)) from exc
        else:
            oauth_states[state_token] = (provider_name, now, flow_secret)

        redirect_uri = oauth_redirect_uri(request, provider_name)
        if provider_name == AuthProvider.GOOGLE:
            params = {
                "client_id": settings["client_id"],
                "redirect_uri": redirect_uri,
                "response_type": "code",
                "scope": "openid email profile",
                "state": state_token,
                "prompt": "select_account",
            }
            url = f"https://accounts.google.com/o/oauth2/v2/auth?{urlencode(params)}"
        elif provider_name == AuthProvider.FACEBOOK:
            params = {
                "client_id": settings["client_id"],
                "redirect_uri": redirect_uri,
                "response_type": "code",
                "scope": "email,public_profile",
                "state": state_token,
            }
            url = f"https://www.facebook.com/dialog/oauth?{urlencode(params)}"
        else:
            raise HTTPException(status_code=501, detail="此登入方式將於 App 版啟用。")

        response = RedirectResponse(url=url, status_code=302)
        response.headers["Cache-Control"] = "no-store"
        response.headers["Referrer-Policy"] = "no-referrer"
        flow_cookie_name = f"exchange_guide_oauth_flow_{provider_name.value}"
        response.set_cookie(
            flow_cookie_name,
            flow_secret,
            max_age=600,
            httponly=True,
            samesite="lax",
            path=f"/auth/oauth/{provider_name.value}/callback",
            secure=_auth_cookie_secure_enabled(),
        )
        return response

    @app.get("/auth/oauth/{provider}/callback")
    def oauth_callback(
        provider: str,
        request: Request,
        state: str = Query(min_length=8),
        code: str | None = Query(default=None),
        error: str | None = Query(default=None),
    ) -> Response:
        try:
            provider_name = AuthProvider(provider)
        except ValueError as exc:
            raise HTTPException(status_code=404, detail="不支援這個登入方式。") from exc

        flow_cookie_name = f"exchange_guide_oauth_flow_{provider_name.value}"
        flow_secret = request.cookies.get(flow_cookie_name)

        def _clear_flow_cookie(resp: Response) -> Response:
            resp.set_cookie(
                flow_cookie_name,
                "",
                max_age=0,
                httponly=True,
                samesite="lax",
                path=f"/auth/oauth/{provider_name.value}/callback",
                secure=_auth_cookie_secure_enabled(),
            )
            resp.headers["Cache-Control"] = "no-store"
            resp.headers["Referrer-Policy"] = "no-referrer"
            return resp

        state_hash = hashlib.sha256(state.encode("utf-8")).hexdigest()

        target_state = None
        if hasattr(app.state, "transient_auth_store"):
            target_state = app.state.transient_auth_store.get_state(
                state_hash,
                TransientAuthStateKind.OAUTH_LOGIN,
            )
        else:
            rec = oauth_states.get(state)
            if rec:
                target_state = rec

        if target_state is None:
            raise HTTPException(status_code=400, detail="登入驗證已失效，請重新操作。")

        state_provider = (
            target_state.provider_id
            if hasattr(target_state, "provider_id")
            else target_state[0].value
        )
        if state_provider != provider_name.value:
            raise HTTPException(status_code=400, detail="OAuth provider 不符。")

        expected_secret = (
            target_state.session_id
            if hasattr(target_state, "session_id")
            else (target_state[2] if len(target_state) > 2 else None)
        )
        if not flow_secret or (expected_secret and flow_secret != expected_secret):
            raise HTTPException(status_code=403, detail="瀏覽器驗證階段不相符。")

        if hasattr(app.state, "transient_auth_store"):
            app.state.transient_auth_store.consume_state(
                state_hash,
                TransientAuthStateKind.OAUTH_LOGIN,
                expected_provider_id=provider_name.value,
                expected_session_id=flow_secret,
            )
        else:
            oauth_states.pop(state, None)

        if error:
            if len(error) > 120:
                resp = Response(status_code=422)
                return _clear_flow_cookie(resp)
            resp = RedirectResponse(url="/#auth=cancelled", status_code=303)
            return _clear_flow_cookie(resp)

        if not code or len(code) < 4 or len(code) > 512:
            resp = Response(status_code=422)
            return _clear_flow_cookie(resp)

        settings = provider_settings(provider_name)
        if settings is None:
            resp = Response(status_code=503)
            return _clear_flow_cookie(resp)

        redirect_uri = oauth_redirect_uri(request, provider_name)
        try:
            if provider_name == AuthProvider.GOOGLE:
                token_response = requests.post(
                    "https://oauth2.googleapis.com/token",
                    data={
                        "code": code,
                        "client_id": settings["client_id"],
                        "client_secret": settings["secret"],
                        "redirect_uri": redirect_uri,
                        "grant_type": "authorization_code",
                    },
                    timeout=20,
                )
                token_response.raise_for_status()
                oauth_token = token_response.json()["access_token"]
                user_response = requests.get(
                    "https://openidconnect.googleapis.com/v1/userinfo",
                    headers={"Authorization": f"Bearer {oauth_token}"},
                    timeout=20,
                )
                user_response.raise_for_status()
                user = user_response.json()
                subject = str(user["sub"])
                email = user.get("email")
                display_name = user.get("name") or "留學同學"
                avatar_url = user.get("picture")
                trusted_email = email if user.get("email_verified") is True else None
            elif provider_name == AuthProvider.FACEBOOK:
                token_response = requests.get(
                    "https://graph.facebook.com/oauth/access_token",
                    params={
                        "client_id": settings["client_id"],
                        "client_secret": settings["secret"],
                        "redirect_uri": redirect_uri,
                        "code": code,
                    },
                    timeout=20,
                )
                token_response.raise_for_status()
                oauth_token = token_response.json()["access_token"]
                user_response = requests.get(
                    "https://graph.facebook.com/me",
                    params={
                        "fields": "id,name,email,picture.type(large)",
                        "access_token": oauth_token,
                    },
                    timeout=20,
                )
                user_response.raise_for_status()
                user = user_response.json()
                subject = str(user["id"])
                email = user.get("email")
                display_name = user.get("name") or "留學同學"
                avatar_url = (
                    user.get("picture", {}).get("data", {}).get("url")
                )
                trusted_email = None
            else:
                resp = Response(status_code=501)
                return _clear_flow_cookie(resp)
        except (KeyError, requests.RequestException):
            resp = Response(status_code=502)
            return _clear_flow_cookie(resp)

        access_token = secrets.token_urlsafe(40)
        session_token_hash = hashlib.sha256(access_token.encode("utf-8")).hexdigest()
        now = utc_now()
        inferred_school = school_from_email(trusted_email)
        mutation = OAuthLoginMutationRequest(
            provider=provider_name,
            subject=subject,
            trusted_email=trusted_email,
            display_name=(display_name or "留學同學")[:30],
            avatar_url=avatar_url,
            # Only a provider-verified school address names the school; everyone else picks one
            # after signing in. An existing account keeps whatever it already has.
            home_university=(
                inferred_school.school_name if inferred_school else HOME_UNIVERSITY_UNSET
            ),
            new_account_id=uuid4().hex,
            session_id=uuid4().hex,
            session_token_hash=session_token_hash,
            session_expires_at=now + timedelta(days=30),
            occurred_at=now,
        )
        if hasattr(app.state, "account_repository") and hasattr(
            app.state.account_repository, "commit_oauth_login"
        ):
            result = app.state.account_repository.commit_oauth_login(mutation)
            if result.status == OAuthLoginMutationStatus.COMMITTED and result.account:
                account = result.account
                session = AccountSession(
                    access_token=access_token,
                    expires_at=mutation.session_expires_at,
                    profile=_account_profile(account),
                )
                analytics_service.emit(
                    "account_created" if account.id == mutation.new_account_id else "account_login",
                    props={"provider": provider_name.value, "school_from_mail": inferred_school is not None},
                    home_school=catalog_home_university(account) or "", school_basis=school_basis(account) or "")
            elif result.status in (
                OAuthLoginMutationStatus.VERIFIED_EMAIL_CONFLICT,
                OAuthLoginMutationStatus.SAME_PROVIDER_CONFLICT,
                OAuthLoginMutationStatus.UNVERIFIED_EMAIL_CONFLICT,
                OAuthLoginMutationStatus.INTEGRITY_CONFLICT,
            ):
                raise HTTPException(status_code=409, detail="社群帳號或 Email 與現有帳號衝突。")
            else:
                raise HTTPException(status_code=400, detail="無法完成社群登入。")
        else:
            account = oauth_account(
                provider_name,
                subject,
                trusted_email or email,
                display_name,
                avatar_url,
                email_trusted=trusted_email is not None,
            )
            session = account_session(account)

        response = RedirectResponse(url="/#auth=success", status_code=303)
        _clear_flow_cookie(response)
        set_auth_cookie(response, session)
        return response

    @app.get("/universities", response_model=list[SupportedUniversity])
    def universities() -> list[SupportedUniversity]:
        locations = load_university_locations(resolved_data_dir)
        return [
            SupportedUniversity(
                id=university.id,
                school_name=university.school_name,
                short_name=university.short_name,
                english_name=university.english_name,
                aliases=list(university.aliases),
                hero_image=university.hero_image,
                official_url=university.official_url,
                support_level=university.support_level,
                partner_count=university.partner_count_hint,
                coverage_note=university.coverage_note,
                location=public_location(locations, university.school_name, "臺灣"),
                colleges=list(university.colleges),
            )
            for university in SUPPORTED_UNIVERSITIES
        ]

    @app.get("/coverage", response_model=CoverageSummary)
    def coverage(
        school: str | None = Query(default=None),
    ) -> CoverageSummary:
        university = university_for(school)
        partners = partners_for_university(university)
        experiences = load_student_experiences(resolved_data_dir)
        workflows = workflows_for_university(university)
        destination_profiles = published_destination_profiles(university.school_name)
        audits = load_collection_audits(resolved_data_dir)
        research = load_partner_research(resolved_data_dir, include_bundled_baseline=True)
        school_images = _load_school_image_manifest()
        home_key = normalize_school(university.school_name)
        experience_map: dict[str, list] = {}
        for source in experiences:
            experience_map.setdefault(normalize_school(source.school_name), []).append(source)
        workflow_map = {
            normalize_school(workflow.school_name): workflow for workflow in workflows
        }
        destination_map = {
            (
                normalize_school(profile.home_university or CGU.school_name),
                normalize_school(profile.school_name),
            ): profile
            for profile in destination_profiles
        }
        experience_audit_map = {
            normalize_school(audit.school_name): audit
            for audit in audits
            if audit.collector == "experiences"
            and normalize_school(audit.home_university or CGU.school_name) == home_key
        }
        destination_audit_map = {
            normalize_school(audit.school_name): audit
            for audit in audits
            if audit.collector == "destinations"
            and normalize_school(audit.home_university or CGU.school_name) == home_key
        }
        research_map = {
            normalize_school(record.school_name): record
            for record in research
            if normalize_school(record.home_university) == home_key
        }
        rows: list[PartnerCoverage] = []
        if university.id == "tku":
            from .tku_assets import campus_photos
            from .tku_census import school_identifier
        if university.id in {NTNU.id, CYCU.id, NTUST.id, YZU.id, FCU.id, NSYSU.id, NCHU.id, NTUT.id, NCCU.id, NCKU.id, NYCU.id, NTHU.id, PCCU.id, WZU.id, NKUST.id, YUNTECH.id, NTOU.id}:
            from .life_context import _bundled_ntnu_student_experiences
            ntnu_bundled_exps = _bundled_ntnu_student_experiences()
        for partner in partners:
            normalized = normalize_school(partner.school_name)
            visual = school_images.get((partner.school_name, partner.country or ""))
            if university.id == CCU.id and "ccu_completion" in partner.reference_data:
                from .ccu_campus_assets import reviewed_image_coverage
                visual = reviewed_image_coverage(partner)
            if university.id == NCU.id:
                from .ncu_completion import campus_photo
                visual = campus_photo(partner.school_name, partner.country)
            if university.id == "tku":
                identifier=school_identifier(partner.school_name)
                photo=campus_photos().get(identifier) if identifier else None
                visual={"status":"verified","checked_at":photo['checked_at']} if photo else None
            partner_experiences = list(experience_map.get(normalized, []))
            if university.id in {NTNU.id, CYCU.id, NTUST.id, YZU.id, FCU.id, NSYSU.id, NCHU.id, NTUT.id, NCCU.id, NCKU.id, NYCU.id, NTHU.id, PCCU.id, WZU.id, NKUST.id, YUNTECH.id, NTOU.id}:
                for b_exp in ntnu_bundled_exps.get((school_identity_key(partner.school_name), partner.country or ""), ()):
                    if all(x.source_url != b_exp.source_url for x in partner_experiences):
                        partner_experiences.append(b_exp)
            workflow = workflow_map.get(normalized)
            destination = destination_map.get((home_key, normalized))
            experience_audit = experience_audit_map.get(normalized)
            destination_audit = destination_audit_map.get(normalized)
            website_research = research_map.get(normalized)
            experience_status = (
                experience_audit.status
                if experience_audit
                else (
                    "completed"
                    if university.id in {CGU.id, NTNU.id, CYCU.id, NTUST.id, YZU.id, FCU.id, NSYSU.id, NCHU.id, NTUT.id, NCCU.id, NCKU.id, NYCU.id, NTHU.id, PCCU.id, WZU.id, NKUST.id, YUNTECH.id, NTOU.id} and partner_experiences
                    else "not_collected"
                )
            )
            visible_experiences = (
                partner_experiences
                if experience_audit or university.id in {CGU.id, NTNU.id, CYCU.id, NTUST.id, YZU.id, FCU.id, NSYSU.id, NCHU.id, NTUT.id, NCCU.id, NCKU.id, NYCU.id, NTHU.id, PCCU.id, WZU.id, NKUST.id, YUNTECH.id, NTOU.id}
                else []
            )
            destination_status = (
                destination_audit.status
                if destination_audit
                else (
                    destination.coverage_status
                    if destination and normalize_school(destination.home_university or CGU.school_name) == home_key
                    else "not_collected"
                )
            )
            rows.append(
                PartnerCoverage(
                    school_name=partner.school_name,
                    image_status=(
                        str(visual.get("status") or "not_collected")
                        if visual
                        else "not_collected"
                    ),
                    image_last_checked=(visual.get("checked_at") if visual else None),
                    official_website_status=(
                        "needs_confirmation"
                        if university.id == "tku" and partner.availability_status in {"agreement_only","reference_only"}
                        else website_research.verification_status
                        if website_research
                        else "official_verified" if partner.website else "not_collected"
                    ),
                    official_website_url=(
                        website_research.official_website
                        if website_research
                        else partner.website
                    ),
                    official_website_last_checked=(
                        website_research.checked_at if website_research else None
                    ),
                    experience_source_count=len(visible_experiences),
                    experience_status=experience_status,
                    experience_last_checked=max(
                        [source.discovered_at for source in visible_experiences]
                        + ([experience_audit.checked_at] if experience_audit else []),
                        default=None,
                    ),
                    workflow_status=workflow.coverage_status if workflow else "not_collected",
                    workflow_last_checked=workflow.last_checked if workflow else None,
                    destination_status=destination_status,
                    destination_last_checked=(
                        destination_audit.checked_at
                        if destination_audit
                        else destination.last_checked
                        if destination and normalize_school(destination.home_university or CGU.school_name) == home_key
                        else None
                    ),
                )
            )
        return CoverageSummary(
            total_partner_schools=len(partners),
            image_count=sum(row.image_status == "verified" for row in rows),
            official_website_count=sum(
                row.official_website_status == "official_verified" for row in rows
            ),
            experience_school_count=sum(row.experience_source_count > 0 for row in rows),
            experience_checked_count=sum(
                row.experience_status != "not_collected" for row in rows
            ),
            workflow_school_count=sum(row.workflow_status != "not_collected" for row in rows),
            destination_profile_count=sum(
                row.destination_status != "not_collected" for row in rows
            ),
            experience_source_count=sum(row.experience_source_count for row in rows),
            partners=rows,
        )

    @app.get("/sources", response_model=list[SourceSummary])
    def sources(
        school: str | None = Query(default=None),
        limit: int = Query(default=100, ge=1, le=500),
    ) -> list[SourceSummary]:
        pages = pages_for_university(school)
        return [
            SourceSummary(
                title=page.title,
                source_url=page.source_url,
                published_at=page.published_at,
                category=page.category,
                summary=page.summary,
                attachments=page.attachments,
                crawled_at=page.crawled_at,
                content_hash=page.content_hash,
            )
            for page in pages[:limit]
        ]

    @app.get("/exchange-info", response_model=ExchangeInfo)
    def exchange_info(school: str | None = Query(default=None)) -> ExchangeInfo:
        return info_for_university(school)

    @app.get("/student-dashboard", response_model=StudentDashboard)
    def student_dashboard(
        request: Request,
        school: str | None = Query(default=None),
    ) -> StudentDashboard:
        dashboard = _attach_school_images(
            dashboard_for_university(school),
            base_url=public_base_url(request),
        )
        locations = load_university_locations(resolved_data_dir)
        from .ccu_profile import school_location
        is_ccu = university_for(school).id == "ccu"
        is_ncu = university_for(school).id == NCU.id
        from .ncu_completion import campus_location
        is_tku = university_for(school).id == "tku"
        from .tku_assets import school_location as tku_school_location
        is_fju = university_for(school).id == FJU.id
        from .fju_student_view import fju_school_location
        is_scu = university_for(school).id == SCU.id
        from .scu_student_view import scu_school_location
        is_ntnu = university_for(school).id == NTNU.id
        from .ntnu_student_view import ntnu_school_location
        is_cycu = university_for(school).id == CYCU.id
        from .cycu_student_view import cycu_school_location
        is_ntust = university_for(school).id == NTUST.id
        from .ntust_student_view import ntust_school_location
        is_yzu = university_for(school).id == YZU.id
        from .yzu_student_view import yzu_school_location
        is_fcu = university_for(school).id == FCU.id
        from .fcu_student_view import fcu_school_location
        is_nsysu = university_for(school).id == NSYSU.id
        from .nsysu_student_view import nsysu_school_location
        is_nchu = university_for(school).id == NCHU.id
        from .nchu_student_view import nchu_school_location
        is_ntut = university_for(school).id == NTUT.id
        from .ntut_student_view import ntut_school_location
        is_nccu = university_for(school).id == NCCU.id
        from .nccu_student_view import nccu_school_location
        is_ncku = university_for(school).id == NCKU.id
        from .ncku_student_view import ncku_school_location
        is_nycu = university_for(school).id == NYCU.id
        from .nycu_student_view import nycu_school_location
        is_nthu = university_for(school).id == NTHU.id
        from .nthu_student_view import nthu_school_location
        is_pccu = university_for(school).id == PCCU.id
        from .pccu_student_view import pccu_school_location
        is_wzu = university_for(school).id == WZU.id
        from .wzu_student_view import wzu_school_location
        is_nkust = university_for(school).id == NKUST.id
        from .nkust_student_view import nkust_school_location
        is_yuntech = university_for(school).id == YUNTECH.id
        from .yuntech_student_view import yuntech_school_location
        is_ntou = university_for(school).id == NTOU.id
        from .ntou_student_view import ntou_school_location
        partners = []
        for partner in dashboard.partner_universities:
            location = public_location(locations, partner.school_name, partner.country)
            if is_ccu:
                location = school_location(partner, location, resolved_data_dir)
            elif is_ncu:
                location = campus_location(partner, location, resolved_data_dir)
            elif is_tku:
                location = tku_school_location(partner, resolved_data_dir)
            elif is_fju:
                location = fju_school_location(partner, location, resolved_data_dir)
            elif is_scu:
                location = scu_school_location(partner, location, resolved_data_dir)
            elif is_ntnu:
                location = ntnu_school_location(partner, location, resolved_data_dir)
            elif is_cycu:
                location = cycu_school_location(partner, location, resolved_data_dir)
            elif is_ntust:
                location = ntust_school_location(partner, location, resolved_data_dir)
            elif is_yzu:
                location = yzu_school_location(partner, location, resolved_data_dir)
            elif is_fcu:
                location = fcu_school_location(partner, location, resolved_data_dir)
            elif is_nsysu:
                location = nsysu_school_location(partner, location, resolved_data_dir)
            elif is_nchu:
                location = nchu_school_location(partner, location, resolved_data_dir)
            elif is_ntut:
                location = ntut_school_location(partner, location, resolved_data_dir)
            elif is_nccu:
                location = nccu_school_location(partner, location, resolved_data_dir)
            elif is_ncku:
                location = ncku_school_location(partner, location, resolved_data_dir)
            elif is_nycu:
                location = nycu_school_location(partner, location, resolved_data_dir)
            elif is_nthu:
                location = nthu_school_location(partner, location, resolved_data_dir)
            elif is_pccu:
                location = pccu_school_location(partner, location, resolved_data_dir)
            elif is_wzu:
                location = wzu_school_location(partner, location, resolved_data_dir)
            elif is_nkust:
                location = nkust_school_location(partner, location, resolved_data_dir)
            elif is_yuntech:
                location = yuntech_school_location(partner, location, resolved_data_dir)
            elif is_ntou:
                location = ntou_school_location(partner, location, resolved_data_dir)
            partners.append(partner.model_copy(update={"location": location}))
        return dashboard.model_copy(update={"partner_universities": partners})

    @app.post("/public-translations")
    def public_translations(payload: PublicTranslationBatch) -> dict:
        try:
            return translate_public_batch(payload, resolved_data_dir)
        except ValueError as error:
            raise HTTPException(status_code=422, detail=str(error)) from error

    status_metadata: dict[str, Any] = {}
    status_metadata_lock = threading.Lock()

    @app.get("/ai/status")
    @app.get("/advisor/status")
    def advisor_status() -> dict[str, object]:
        state = ai_runtime_state()
        is_paused = state == "paused"
        enabled = False if is_paused else ai_enabled()
        # Polling must not scan the source files for every browser. Runtime state below
        # remains live; only source/index metadata can lag by at most five seconds.
        with status_metadata_lock:
            now = time.monotonic()
            if not status_metadata or now >= status_metadata["expires_at"]:
                metadata = {
                    "rag_index": rag_index_status(resolved_data_dir).model_dump(mode="json"),
                    "structured_source_count": len(load_structured_sources(resolved_data_dir)),
                    "expires_at": now + 5.0,
                }
                status_metadata.update(metadata)
            index_metadata = status_metadata["rag_index"]
            source_count = status_metadata["structured_source_count"]
        payload: dict[str, object] = {
            "ai_enabled": enabled,
            "runtime_state": state,
            "provider": None if is_paused else ai_provider_name(),
            "model": None if is_paused else (ai_model("fast") if enabled else None),
            "fast_model": None if is_paused else (ai_model("fast") if enabled else None),
            "advanced_model": None if is_paused else (ai_model("advanced") if enabled else None),
            "embedding_model": None if is_paused else (ai_embedding_model() if enabled else None),
            "source_grounded_fallback": True,
            "document_upload_persisted": False,
            "structured_source_count": source_count,
            "rag_index": index_metadata,
            "supabase_pgvector_configured": supabase_configured(),
        }
        if is_paused:
            payload["paused_reason"] = "AI API 與本地 AI 目前暫緩啟用；系統已切換至官方資料庫直接查詢。"
        return payload

    @app.post("/advisor/plan", response_model=AdvisorPlan)
    def advisor_plan(request: Request, payload: AdvisorProfile) -> AdvisorPlan:
        university = university_for(payload.school_name)
        pages = pages_for_university(university)
        dashboard = _attach_school_images(
            dashboard_for_university(university),
            base_url=public_base_url(request),
        )
        retrieved_chunks = (
            search_document_chunks(
                payload.question,
                resolved_data_dir,
                pages=pages,
                limit=8,
            )
            if university.id == CGU.id and payload.question and payload.question.strip()
            else None
        )
        return build_advisor_plan(
            payload,
            dashboard,
            pages,
            workflows_for_university(university),
            published_destination_profiles(university.school_name),
            retrieved_chunks=retrieved_chunks,
        )

    @app.post("/ai/chat", response_model=AdvisorAnswer, deprecated=True)
    def ai_chat(payload: AdvisorQuestionRequest) -> AdvisorAnswer:
        if ai_runtime_state() == "paused":
            raise HTTPException(status_code=503, detail="AI API 與本地 AI 目前暫緩")
        return advisor_ask(payload)

    @app.post("/advisor/ask", response_model=AdvisorAnswer)
    def advisor_ask(payload: AdvisorQuestionRequest) -> AdvisorAnswer:
        profile = payload.profile or AdvisorProfile()
        university = university_for(profile.school_name)
        pages = pages_for_university(university)
        dashboard = dashboard_for_university(university)
        retrieved_chunks = (
            search_document_chunks(
                payload.question,
                resolved_data_dir,
                pages=pages,
                limit=8,
            )
            if university.id == CGU.id
            else None
        )
        return answer_question(
            payload.question,
            dashboard,
            pages,
            workflows_for_university(university),
            published_destination_profiles(university.school_name),
            retrieved_chunks=retrieved_chunks,
        )

    @app.get(
        "/ai/structured-sources",
        response_model=list[StructuredSourceRecord],
    )
    def ai_structured_sources(
        limit: int = Query(default=100, ge=1, le=500),
    ) -> list[StructuredSourceRecord]:
        university_for(CGU.school_name)
        rows = load_structured_sources(resolved_data_dir)
        rows.sort(key=lambda row: row.last_checked, reverse=True)
        return rows[:limit]

    @app.get("/deadlines", response_model=list[DeadlineRecord])
    def deadlines(
        school: str | None = Query(default=None),
    ) -> list[DeadlineRecord]:
        pages = pages_for_university(school)
        records: list[DeadlineRecord] = []
        triggers = FIELD_TRIGGERS["application_period"]
        for page in pages:
            if "非交換申請期限" in page.title or "不是交換申請期限變更" in page.text:
                continue
            snippets = _deadline_snippets(page.text, triggers)
            if page.category == PageCategory.DEADLINE or snippets:
                records.append(
                    DeadlineRecord(
                        title=page.title,
                        source_url=page.source_url,
                        published_at=page.published_at,
                        category=page.category,
                        snippets=snippets[:5],
                    )
                )
        return records

    @app.get(
        "/verified-window-deadlines",
        response_model=VerifiedWindowDeadlineCatalog,
    )
    def verified_window_deadlines(
        school: str | None = Query(default=None),
    ) -> VerifiedWindowDeadlineCatalog:
        if school is not None and school.strip():
            university = university_for(school)
            return build_verified_window_deadline_catalog(school=university.id)
        return build_verified_window_deadline_catalog()

    @app.get("/calendar/school-window.ics", response_class=PlainTextResponse)
    def calendar_school_window_ics(
        school: str | None = Query(default=None),
    ) -> PlainTextResponse:
        university = university_for(school)
        filename, ics_content = build_school_window_ics(university.id)
        return PlainTextResponse(
            ics_content,
            media_type="text/calendar; charset=utf-8",
            headers={
                "Cache-Control": "public, max-age=300",
                "Content-Disposition": f'attachment; filename="{filename}"',
            },
        )

    @app.get(
        "/cross-school-partners",
        response_model=CrossSchoolPartnerDirectory,
    )
    def cross_school_partners_directory(
        country: str | None = Query(default=None),
        q: str | None = Query(default=None),
        home: str | None = Query(default=None),
        limit: int = Query(default=120, ge=1, le=500),
    ) -> CrossSchoolPartnerDirectory:
        return build_cross_school_partner_directory(
            catalogue_loader=seo_catalogue,
            country=country,
            q=q,
            home=home,
            limit=limit,
        )

    @app.get(
        "/cross-school-partners/{country}/{institution}",
        response_model=CrossSchoolPartnerPageData,
    )
    def cross_school_partner_page(
        country: str,
        institution: str,
        home: str | None = Query(default=None),
        override_plan_count: int | None = Query(default=None, ge=0, le=5000),
    ) -> CrossSchoolPartnerPageData:
        page_data = build_cross_school_partner_page_data(
            country=country,
            institution=institution,
            selected_home=home,
            catalogue_loader=seo_catalogue,
            data_dir=resolved_data_dir,
            override_plan_count=override_plan_count,
        )
        if page_data is None:
            raise HTTPException(
                status_code=404,
                detail="找不到這所外國合作大學的跨校整理頁。",
            )
        return page_data

    @app.get(
        "/network-effects/status",
        response_model=SchoolStagedNetworkStatus,
    )
    def network_effects_status(
        school: str | None = Query(default=None),
        override_plan_count: int | None = Query(default=None, ge=0, le=5000),
    ) -> SchoolStagedNetworkStatus:
        university = university_for(school)
        return build_school_staged_network_status(
            university,
            data_dir=resolved_data_dir,
            override_plan_count=override_plan_count,
        )

    @app.get(
        "/network-effects/catalog",
        response_model=StagedNetworkEffectsCatalog,
    )
    def network_effects_catalog() -> StagedNetworkEffectsCatalog:
        return build_staged_network_effects_catalog(data_dir=resolved_data_dir)

    @app.post(
        "/network-effects/preference-signal",
        response_model=SchoolStagedNetworkStatus,
    )
    def submit_preference_signal(
        payload: PreferenceSignalSubmitRequest,
    ) -> SchoolStagedNetworkStatus:
        try:
            return record_preference_signal(payload, data_dir=resolved_data_dir)
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc

    @app.get(
        "/network-effects/admitted-connect/{country}/{institution}",
        response_model=AdmittedStudentConnectHub,
    )
    def get_admitted_student_connect(
        country: str,
        institution: str,
    ) -> AdmittedStudentConnectHub:
        page_data = build_cross_school_partner_page_data(
            country=country,
            institution=institution,
            selected_home=None,
            catalogue_loader=seo_catalogue,
            data_dir=resolved_data_dir,
        )
        if page_data is None or page_data.admitted_student_connect is None:
            raise HTTPException(
                status_code=404,
                detail="找不到這所外國合作大學的本屆錄取生跨校連線專區。",
            )
        return page_data.admitted_student_connect

    @app.post(
        "/network-effects/admitted-connect",
        response_model=AdmittedStudentConnectHub,
        status_code=201,
    )
    def create_admitted_student_connect(
        payload: AdmittedStudentConnectCreateRequest,
    ) -> AdmittedStudentConnectHub:
        page_data = build_cross_school_partner_page_data(
            country=payload.country,
            institution=payload.institution,
            selected_home=payload.home_school,
            catalogue_loader=seo_catalogue,
            data_dir=resolved_data_dir,
        )
        if page_data is None:
            raise HTTPException(
                status_code=404,
                detail="找不到對應的外國合作大學，無法建立跨校錄取生連線。",
            )
        try:
            return register_admitted_student_connection(
                payload,
                country_slug=page_data.country_slug,
                institution_slug=page_data.institution_slug,
                partner_name_zh=page_data.school_name_zh,
                partner_name_en=page_data.school_name_en,
                country_name_zh=page_data.country_name_zh,
                data_dir=resolved_data_dir,
            )
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc

    @app.get("/documents", response_model=list[DocumentRecord])
    def documents(
        school: str | None = Query(default=None),
    ) -> list[DocumentRecord]:
        pages = pages_for_university(school)
        records: list[DocumentRecord] = []
        seen: set[tuple[str, str]] = set()
        for page in pages:
            for attachment in page.attachments:
                key = (page.title, attachment.url)
                if key in seen:
                    continue
                seen.add(key)
                records.append(
                    DocumentRecord(
                        title=page.title,
                        source_url=page.source_url,
                        attachment=attachment,
                        document_url=attachment.url,
                        document_type=attachment.content_type or "attachment",
                    )
                )

        dashboard = dashboard_for_university(school)
        for document in dashboard.document_explanations:
            document_url = document.document_url or document.source.source_url
            key = (document.title, document_url)
            if key in seen:
                continue
            seen.add(key)
            records.append(
                DocumentRecord(
                    title=document.title,
                    source_url=document.source.source_url,
                    summary=document.summary,
                    key_points=document.key_points,
                    applies_to=document.applies_to,
                    document_url=document.document_url,
                    document_type=document.document_type,
                )
            )
        return records

    @app.post("/ai/review-document", response_model=DocumentCheckResult)
    @app.post("/document-check", response_model=DocumentCheckResult)
    async def document_check(response: Response, request: Request,
        file: UploadFile = File(...),
        document_type: str = Form(default="auto"),
        expected_word_limit: int | None = Form(default=None, ge=1, le=20_000),
        require_signature: bool = Form(default=False),
        use_ai: bool = Form(default=False),
        ai_consent_granted: bool = Form(default=False),
        consent: bool = Form(...),
    ) -> DocumentCheckResult:
        import os
        
        mode = os.environ.get("EXCHANGE_PRODUCT_RELEASE_MODE", "")
        if mode == "public":
            auth = request.headers.get("Authorization")
            if not auth:
                raise HTTPException(status_code=401, detail="Unauthorized")
            if "free" in auth:
                raise HTTPException(status_code=403, detail="需要進階功能")
                
        if request.url.path == "/ai/review-document" or use_ai:
            raise HTTPException(status_code=503, detail="AI 深度檢查目前暫緩")
        
        if consent is None or consent is False:
            raise HTTPException(status_code=422, detail="需要同意")
            
        content = await file.read(MAX_DOCUMENT_BYTES + 1)
        await file.close()
        try:
            result = await run_in_threadpool(
                partial(
                    check_document,
                    file_name=file.filename or "uploaded-document",
                    content=content,
                    document_type=document_type,
                    expected_word_limit=expected_word_limit,
                    require_signature=require_signature,
                    use_ai=use_ai,
                )
            )
            response.headers["Cache-Control"] = "no-store"
            response.headers["X-Content-Type-Options"] = "nosniff"
            return result
        except ValueError as error:
            raise HTTPException(status_code=422, detail=str(error)) from error

    @app.post("/ai/rewrite-document", response_model=DocumentRewriteResult, deprecated=True)
    def ai_rewrite_document(response: Response, payload: DocumentRewriteRequest) -> DocumentRewriteResult:
        if not getattr(payload, "ai_consent_granted", False):
            raise HTTPException(status_code=422, detail="AI consent required")
        if ai_runtime_state() == "paused":
            raise HTTPException(status_code=503, detail="AI API 與本地 AI 目前暫緩")
        try:
            result = rewrite_document(payload)
            response.headers["Cache-Control"] = "private, no-store"
            response.headers["X-Content-Type-Options"] = "nosniff"
            return result
        except DocumentRewriteUnavailable as error:
            raise HTTPException(status_code=503, detail=str(error)) from error

    @app.get(
        "/application-center/templates",
        response_model=list[ApplicationDocumentTemplate],
    )
    def application_center_templates(
        school: str | None = Query(default=None),
        program_type: str = Query(default="exchange"),
        flags: str = Query(default=""),
        academic_year: str | None = Query(default=None, max_length=40),
        application_round: str | None = Query(default=None, max_length=80),
        include_all: bool = Query(default=False),
    ) -> list[ApplicationDocumentTemplate]:
        university = university_for(school)
        if include_all:
            return all_application_templates(university.school_name)
        try:
            context = ApplicationCenterContext(
                school_name=university.school_name,
                program_type=program_type,
                flags=[value.strip() for value in flags.split(",") if value.strip()],
                academic_year=academic_year,
                application_round=application_round,
            )
        except ValueError as error:
            raise HTTPException(status_code=422, detail="不支援的申請計畫類型。") from error
        return templates_for_context(context)

    @app.get(
        "/application-center/study-plan-workbench",
        response_model=StudyPlanWorkbenchPayload,
    )
    def application_center_study_plan_workbench(
        school: str | None = Query(default=None),
        target_partner: str | None = Query(default=None, max_length=200),
    ) -> StudyPlanWorkbenchPayload:
        university = university_for(school)
        return build_study_plan_workbench_payload(
            university,
            target_partner=target_partner,
            catalogue_loader=seo_catalogue,
        )

    @app.get(
        "/application-center/study-plan-workbench/catalog",
        response_model=StudyPlanWorkbenchCatalog,
    )
    def application_center_study_plan_workbench_catalog(
        only_active_10_week_window: bool = Query(default=False),
    ) -> StudyPlanWorkbenchCatalog:
        return build_study_plan_workbench_catalog(
            only_active_10_week_window=only_active_10_week_window,
            catalogue_loader=seo_catalogue,
        )

    @app.get(
        "/application-center/catalog",
        response_model=ApplicationDocumentCatalog,
    )
    def application_center_catalog(
        school: str | None = Query(default=None),
        target_school: str = Query(min_length=2, max_length=200),
        college: str | None = Query(default=None, max_length=120),
        department: str | None = Query(default=None, max_length=120),
        degree_level: str | None = Query(default=None, max_length=80),
        program_type: str | None = Query(default=None, max_length=80),
        academic_year: str | None = Query(default=None, max_length=40),
        application_round: str | None = Query(default=None, max_length=80),
        host_admission_status: Literal["unknown", "not_accepted", "accepted"] = Query(default="unknown"),
        housing_choice: Literal["unknown", "on_campus", "off_campus"] = Query(default="unknown"),
        semester: str | None = Query(default=None, max_length=30),
    ) -> ApplicationDocumentCatalog:
        university, partner = partner_context_for_school(target_school, school)
        context = ApplicationCenterContext(
            school_name=university.school_name,
            target_school=partner.school_name,
            college=college,
            department=department,
            degree_level=degree_level,
            program_type=program_type or "exchange",
            academic_year=academic_year,
            application_round=application_round,
            semester=semester,
            partner_document_states={preparation_state_key(partner.school_name, academic_year, application_round, semester): PartnerDocumentPreparationState(
                host_admission_status=host_admission_status, housing_choice=housing_choice,
            )} if university.id == NCU.id else {},
        )
        workflows = workflows_for_university(university)
        return build_application_document_catalog(context, workflows)

    @app.post(
        "/application-center/manifest",
        response_model=ApplicationPacketManifest,
    )
    def application_center_manifest(
        payload: ApplicationPacketRequest,
        request: Request,
        response: Response,
    ) -> ApplicationPacketManifest:
        account, _ = authenticated_account(request)
        university_for(payload.context.school_name)
        if not product_feature_enabled(account, ProductFeature.APPLICATION_DOCUMENT_GENERATION):
            raise HTTPException(
                status_code=403,
                detail="申請文件產生為進階功能，請確認方案權限。",
            )
        response.headers["Cache-Control"] = "no-store"
        response.headers["X-Content-Type-Options"] = "nosniff"
        return build_packet_manifest(payload)

    @app.post("/application-center/pdf")
    async def application_center_pdf(
        payload: ApplicationPacketRequest,
        request: Request,
    ) -> Response:
        account, _ = authenticated_account(request)
        university_for(payload.context.school_name)
        if not product_feature_enabled(account, ProductFeature.APPLICATION_DOCUMENT_GENERATION):
            raise HTTPException(
                status_code=403,
                detail="申請文件產生為進階功能，請確認方案權限。",
            )
        try:
            pdf_bytes, manifest = await run_in_threadpool(
                partial(
                    generate_application_packet_pdf,
                    payload,
                    raw_files_dir=resolved_data_dir / "raw_files",
                )
            )
        except ValueError as error:
            raise HTTPException(status_code=422, detail=str(error)) from error
        target = re.sub(r"[^0-9A-Za-z\u4e00-\u9fff_-]+", "-", payload.context.target_school or "交換申請")
        filename = f"{target}-列印包-{manifest.total_printed_copies}份.pdf"
        encoded = quote(filename)
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename=exchange-application-packet.pdf; filename*=UTF-8''{encoded}",
                "Cache-Control": "no-store",
                "Pragma": "no-cache",
                "X-Content-Type-Options": "nosniff",
                "X-Application-Storage": "request-only",
                "X-Application-Packet-Documents": str(len(manifest.items)),
                "X-Application-Packet-Copies": str(manifest.total_printed_copies),
                "X-Application-Packet-Attachments": str(sum(len(item.attachments) for item in manifest.items)),
                "X-Application-Packet-Pages": str(len(PdfReader(BytesIO(pdf_bytes)).pages)),
            },
        )

    @app.post("/application-center/docx")
    async def application_center_docx(
        payload: ApplicationPacketRequest,
        request: Request,
    ) -> Response:
        account, _ = authenticated_account(request)
        university_for(payload.context.school_name)
        if not product_feature_enabled(account, ProductFeature.APPLICATION_DOCUMENT_GENERATION):
            raise HTTPException(
                status_code=403,
                detail="申請文件產生為進階功能，請確認方案權限。",
            )
        try:
            packet = await run_in_threadpool(
                partial(
                    generate_application_packet_docx,
                    payload,
                    raw_files_dir=resolved_data_dir / "raw_files",
                )
            )
        except ValueError as error:
            raise HTTPException(status_code=422, detail=str(error)) from error
        target = re.sub(r"[^0-9A-Za-z\u4e00-\u9fff_-]+", "-", payload.context.target_school or "交換申請")
        if packet.extension == "docx":
            title = re.sub(r"[^0-9A-Za-z\u4e00-\u9fff_-]+", "-", packet.manifest.items[0].title)
            filename = f"{target}-{title}.docx"
        else:
            filename = f"{target}-申請文件-Word.zip"
        encoded = quote(filename)
        return Response(
            content=packet.content,
            media_type=packet.media_type,
            headers={
                "Content-Disposition": f"attachment; filename=exchange-application-documents.{packet.extension}; filename*=UTF-8''{encoded}",
                "Cache-Control": "no-store",
                "Pragma": "no-cache",
                "X-Content-Type-Options": "nosniff",
                "X-Application-Storage": "request-only",
                "X-Application-Packet-Documents": str(len(packet.manifest.items)),
                "X-Application-Packet-Copies": str(packet.manifest.total_printed_copies),
                "X-Application-Packet-Attachments": str(sum(len(item.attachments) for item in packet.manifest.items)),
            },
        )

    @app.get("/student-experiences", response_model=StudentExperienceDigest)
    def student_experiences(
        school: str = Query(min_length=2),
        home_school: str | None = Query(default=None),
    ) -> StudentExperienceDigest:
        partner = partner_for_school(school, home_school)
        sources = load_student_experiences(resolved_data_dir)
        known_urls = {source.source_url for source in sources if source.school_name == partner.school_name}
        sources.extend(source for source in reference_student_sources(partner) if source.source_url not in known_urls)
        digest = localize_experience_digest(build_experience_digest(partner.school_name, partner.country, sources), resolved_data_dir)
        digest = with_bundled_sources(digest, partner.school_name)
        return digest.model_copy(update={"sources": attach_digests(digest.sources)})

    @app.post("/student-experiences/refresh", response_model=StudentExperienceDigest)
    def refresh_student_experiences(
        school: str = Query(min_length=2),
        home_school: str | None = Query(default=None),
        max_sources: int = Query(default=12, ge=3, le=20),
    ) -> StudentExperienceDigest:
        university, partner = partner_context_for_school(school, home_school)
        with experience_collection_lock:
            discovered = collect_student_experiences(
                partner,
                max_sources=max_sources,
            )
            existing = load_student_experiences(resolved_data_dir)
            collected = merge_refreshed_student_experiences(
                partner,
                existing,
                discovered,
                max_sources=max_sources,
            )
            all_sources = replace_school_experiences(
                partner.school_name,
                collected,
                resolved_data_dir,
            )
            upsert_collection_audit(
                CollectionAudit(
                    school_name=partner.school_name,
                    collector="experiences",
                    status="completed" if collected else "no_results",
                    home_university=university.school_name,
                    result_count=len(collected),
                    note=(
                        None
                        if discovered
                        else (
                            "No new source was found; previously accepted sources were retained."
                            if collected
                            else "No reliable public student experience source was found."
                        )
                    ),
                ),
                resolved_data_dir,
            )
        known_urls = {source.source_url for source in all_sources if source.school_name == partner.school_name}
        all_sources.extend(source for source in reference_student_sources(partner) if source.source_url not in known_urls)
        digest = localize_experience_digest(build_experience_digest(partner.school_name, partner.country, all_sources), resolved_data_dir, generate=True)
        digest = with_bundled_sources(digest, partner.school_name)
        return digest.model_copy(update={"sources": attach_digests(digest.sources)})

    @app.get("/experience-digest", response_model=ExperienceDigestZh)
    def experience_digest(source_url: str = Query(min_length=8, max_length=2000)) -> ExperienceDigestZh:
        digest = load_digests().get(source_url)
        if digest is None:
            raise HTTPException(status_code=404, detail="這篇心得還沒有中文整理。")
        return digest

    @app.get("/destination-tips/countries", response_model=list[DestinationGuideSummary])
    def destination_tip_countries() -> list[DestinationGuideSummary]:
        return guide_summaries()

    @app.get("/destination-tips", response_model=DestinationGuide)
    def destination_tips(country: str = Query(min_length=1, max_length=40)) -> DestinationGuide:
        guide = guide_for_country(country)
        if guide is None:
            raise HTTPException(status_code=404, detail="這個國家的出發前提醒還在整理中。")
        return guide

    from .application_periods import ApplicationPeriodOptions, application_period_options

    @app.get("/application-period-options", response_model=ApplicationPeriodOptions)
    def available_application_periods(home_school: str | None = Query(default=None)) -> ApplicationPeriodOptions:
        university = university_for(home_school)
        return application_period_options(university.school_name, workflows_for_university(university))

    @app.get("/application-workflow", response_model=UniversityApplicationWorkflow)
    def application_workflow(
        school: str = Query(min_length=2),
        home_school: str | None = Query(default=None),
        academic_year: str | None = Query(default=None),
        application_round: str | None = Query(default=None),
        college: str | None = Query(default=None, max_length=120),
        department: str | None = Query(default=None, max_length=120),
    ) -> UniversityApplicationWorkflow:
        from .application_rules import select_application_workflow
        from .models import ApplicationRuleContext

        university, partner = partner_context_for_school(school, home_school)
        matched = select_application_workflow(
            workflows_for_university(university),
            ApplicationRuleContext(
                home_university=university.school_name, partner_university=partner.school_name,
                academic_year=academic_year, application_round=application_round,
                college=college, department=department,
            ),
        )
        if matched is not None:
            return matched
        return UniversityApplicationWorkflow(
            home_university=university.school_name,
            school_name=partner.school_name,
            partner_website=partner.website,
            country=partner.country,
            program_type=partner.program_type,
        )

    @app.post(
        "/application-plan/evaluate",
        response_model=PersonalApplicationPlanResult,
    )
    def evaluate_application_plan(
        payload: PersonalApplicationPlanRequest,
    ) -> PersonalApplicationPlanResult:
        university = university_for(payload.home_school)
        partners = partners_for_university(university)
        workflows = workflows_for_university(university)
        dashboard = dashboard_for_university(university)
        academic_source_url = (
            dashboard.sources[0].source_url if dashboard.sources else None
        )
        try:
            return build_personal_application_plan(
                payload,
                partners,
                workflows,
                academic_score_minimum=dashboard.academic_score_minimum,
                academic_source_url=academic_source_url,
            )
        except ValueError as error:
            raise HTTPException(status_code=422, detail=str(error)) from error

    @app.post("/application-plan/schedule", response_model=ApplicationPlanScheduleResult)
    def schedule_personal_application_plan(
        request: Request, response: Response, payload: ApplicationPlanScheduleRequest,
    ) -> ApplicationPlanScheduleResult:
        from .application_plan_scheduling import schedule_application_plan
        from zoneinfo import ZoneInfo

        account, _ = authenticated_account(request)
        if resolve_university(payload.plan.home_school) is None:
            raise HTTPException(status_code=422, detail="目前只能為已支援的大學排程。")
        if configured_product_release_mode() == ProductReleaseMode.PUBLIC and account.product_tier != ProductAccessTier.SUBSCRIPTION:
            raise HTTPException(status_code=403, detail="此為進階功能，請升級訂閱後使用。")
        response.headers["Cache-Control"] = "no-store"
        response.headers["X-Content-Type-Options"] = "nosniff"
        plan = evaluate_application_plan(payload.plan)
        try:
            return schedule_application_plan(plan, payload, as_of=payload.as_of or utc_now().astimezone(ZoneInfo("Asia/Taipei")).date())
        except ValueError as error:
            raise HTTPException(status_code=422, detail=str(error)) from error

    @app.post(
        "/application-workflow-issue-reports",
        response_model=ApplicationWorkflowIssueReport,
        status_code=202,
    )
    def submit_application_workflow_issue_report(
        request: Request,
        response: Response,
        payload: ApplicationWorkflowIssueReportCreate,
        mutation_id: str = Header(alias='X-Content-Report-Mutation-ID', min_length=16, max_length=128),
    ) -> ApplicationWorkflowIssueReport:
        if not mutation_id or len(mutation_id) < 16 or len(mutation_id) > 128:
            raise HTTPException(status_code=422, detail="缺少有效操作識別碼。")
        account, _ = authenticated_account(request)
        if not catalog_home_university(account):
            raise HTTPException(status_code=403, detail="請先選擇學校後再回報問題。")
        _reject_contact_details(payload.description)

        university = university_for(payload.home_school)
        workflows = workflows_for_university(university)
        matched_workflow = next(
            (w for w in workflows if w.workflow_id == payload.workflow_id),
            None,
        )
        if matched_workflow is None:
            norm_name = normalize_school(payload.school_name)
            matched_workflow = next(
                (w for w in workflows if normalize_school(w.school_name) == norm_name),
                None,
            )
        if matched_workflow is None:
            raise HTTPException(status_code=404, detail="找不到對應的交換流程。")
        if matched_workflow.version != payload.workflow_version:
            raise HTTPException(status_code=409, detail="回報的流程版本與目前公開版本不一致。")
        if matched_workflow.issue_report_snapshot != payload.workflow_snapshot:
            raise HTTPException(status_code=409, detail="回報的流程快照不符。")
        step_title = None
        if payload.step_rule_id:
            step = next(
                (s for s in matched_workflow.steps if s.rule_id == payload.step_rule_id),
                None,
            )
            if step is None:
                raise HTTPException(status_code=422, detail="指定的步驟不存在。")
            step_title = step.title

        fingerprint = canonical_issue_report_fingerprint(
            payload.model_dump(mode="json")
        )
        report = ApplicationWorkflowIssueReport(
            workflow_key=workflow_storage_key(matched_workflow),
            workflow_id=matched_workflow.workflow_id,
            workflow_version=matched_workflow.version,
            workflow_snapshot=matched_workflow.issue_report_snapshot,
            home_school=payload.home_school,
            school_name=payload.school_name,
            step_rule_id=payload.step_rule_id,
            step_title=step_title,
            college=payload.college,
            department=payload.department,
            academic_year=payload.academic_year,
            application_round=payload.application_round,
            category=payload.category,
            description=payload.description,
            official_source_url=payload.official_source_url,
        )
        mutation = WorkflowIssueReportSubmitMutation(
            mutation_id=mutation_id,
            account_id=account.id,
            request_fingerprint=fingerprint,
            report=report,
        )
        result = app.state.workflow_issue_report_repository.submit_report(mutation)
        if result.status == WorkflowIssueReportMutationStatus.IDEMPOTENCY_CONFLICT:
            raise HTTPException(status_code=409, detail="操作識別碼衝突。")
        if result.status == WorkflowIssueReportMutationStatus.RATE_LIMITED:
            raise HTTPException(
                status_code=429,
                detail="回報次數已達上限，請稍後再試。",
                headers={"Retry-After": str(result.retry_after_seconds or 3600)},
            )
        if result.status != WorkflowIssueReportMutationStatus.COMMITTED or result.report is None:
            raise HTTPException(status_code=400, detail="無法提交回報。")

        response.status_code = 202
        response.headers["X-Idempotent-Replay"] = "true" if result.idempotent else "false"
        return result.report

    @app.get(
        "/admin/application-workflow-issue-reports",
        response_model=list[ApplicationWorkflowIssueReport],
    )
    def list_admin_workflow_issue_reports(
        request: Request,
        response: Response,
        status: ApplicationWorkflowIssueReportStatus | None = Query(default=None),
    ) -> list[ApplicationWorkflowIssueReport]:
        authenticated_content_admin(request)
        response.headers["Cache-Control"] = "no-store"
        rows = app.state.workflow_issue_report_repository.list_reports()
        return [row for row in rows if status is None or row.status == status]

    @app.patch(
        "/admin/application-workflow-issue-reports/{report_id}",
        response_model=ApplicationWorkflowIssueReport,
    )
    def review_application_workflow_issue_report(
        report_id: str,
        request: Request,
        response: Response,
        payload: ApplicationWorkflowIssueReportReviewRequest,
        mutation_id: str = Header(alias='X-Content-Report-Mutation-ID', min_length=16, max_length=128),
    ) -> ApplicationWorkflowIssueReport:
        if not mutation_id or len(mutation_id) < 16 or len(mutation_id) > 128:
            raise HTTPException(status_code=422, detail="缺少有效操作識別碼。")
        admin, _ = authenticated_content_admin(request)
        _reject_contact_details(payload.note)

        review = ApplicationWorkflowIssueReportReview(
            report_id=report_id,
            status=payload.status,
            note=payload.note,
            reviewer_display_name=admin.display_name,
        )
        fingerprint = canonical_issue_report_fingerprint(
            payload.model_dump(mode="json")
        )
        mutation = WorkflowIssueReportReviewMutation(
            mutation_id=mutation_id,
            reviewer_account_id=admin.id,
            request_fingerprint=fingerprint,
            review=review,
        )
        result = app.state.workflow_issue_report_repository.review_report(mutation)
        if result.status == WorkflowIssueReportMutationStatus.REPORT_MISSING:
            raise HTTPException(status_code=404, detail="找不到這個問題回報。")
        if result.status in (
            WorkflowIssueReportMutationStatus.STATUS_CONFLICT,
            WorkflowIssueReportMutationStatus.IDEMPOTENCY_CONFLICT,
        ):
            raise HTTPException(status_code=409, detail="無法審查已結案或衝突的回報。")
        if result.status != WorkflowIssueReportMutationStatus.COMMITTED or result.report is None:
            raise HTTPException(status_code=400, detail="審查回報失敗。")

        response.headers["X-Idempotent-Replay"] = "true" if result.idempotent else "false"
        return result.report

    @app.get("/destination-profile", response_model=DestinationProfile)
    def destination_profile(
        school: str = Query(min_length=2),
        home_school: str | None = Query(default=None),
    ) -> DestinationProfile:
        partner = partner_for_school(school, home_school)
        normalized = normalize_school(partner.school_name)
        canonical_home = university_for(home_school).school_name if home_school else None
        target_home = normalize_school(canonical_home) if canonical_home else None
        profiles = published_destination_profiles(canonical_home)
        if target_home:
            for profile in profiles:
                if (
                    normalize_school(profile.school_name) == normalized
                    and normalize_school(profile.home_university or "") == target_home
                ):
                    return complete_destination_profile(profile, resolved_data_dir)
        for profile in profiles:
            if normalize_school(profile.school_name) == normalized:
                if target_home:
                    if profile.home_university:
                        continue
                    return complete_destination_profile(profile.model_copy(update={"home_university": canonical_home}), resolved_data_dir)
                return complete_destination_profile(profile, resolved_data_dir)
        return DestinationProfile(
            home_university=canonical_home,
            school_name=partner.school_name,
            country=partner.country,
        )

    @app.get("/school-data-completeness", response_model=SchoolDataCompleteness)
    def school_data_completeness(
        school: str = Query(min_length=2),
        home_school: str | None = Query(default=None),
    ) -> SchoolDataCompleteness:
        from .application_rules import select_application_workflow
        from .models import ApplicationRuleContext
        from .school_completeness import build_school_completeness

        university, partner = partner_context_for_school(school, home_school)
        if university.id == 'tku':
            from .tku_completeness import build_tku_school_completeness
            return build_tku_school_completeness(partner)
        workflow = select_application_workflow(
            workflows_for_university(university),
            ApplicationRuleContext(
                home_university=university.school_name, partner_university=partner.school_name,
            ),
        )
        result = build_school_completeness(
            partner, destination_profile(school, home_school), workflow,
            home_university=university.school_name,
        )
        if university.id == "ccu":
            from .ccu_profile import align_completeness
            return align_completeness(result, partner)
        return result

    @app.get("/partner-source-audit", response_model=dict)
    def partner_source_audit(school: str = Query(min_length=2), home_school: str | None = Query(default=None)) -> dict:
        university, partner = partner_context_for_school(school, home_school)
        if university.id != NCU.id:
            raise HTTPException(status_code=404, detail="此校尚無逐欄來源查核記錄。")
        from .ncu_student_view import ncu_source_audit
        audit = ncu_source_audit(partner.school_name)
        if audit is None:
            raise HTTPException(status_code=404, detail="未找到此合作項目查核記錄。")
        return audit

    @app.get("/school-life-context", response_model=SchoolLifeContext)
    def school_life_context(
        school: str = Query(min_length=2),
        home_school: str | None = Query(default=None),
    ) -> SchoolLifeContext:
        university, partner = partner_context_for_school(school, home_school)
        location = public_location(load_university_locations(resolved_data_dir), partner.school_name, partner.country)
        if university.id == NCU.id:
            from .ncu_completion import campus_location
            location = campus_location(partner, location, resolved_data_dir)
        if university.id == "ccu":
            from .ccu_profile import school_location
            location = school_location(partner, location, resolved_data_dir)
        if university.id == "tku":
            from .tku_assets import school_location
            location = school_location(partner, resolved_data_dir)
        if university.id == FJU.id:
            from .fju_student_view import fju_school_location
            location = fju_school_location(partner, location, resolved_data_dir)
        if university.id == SCU.id:
            from .scu_student_view import scu_school_location
            location = scu_school_location(partner, location, resolved_data_dir)
        if university.id == NTNU.id:
            from .ntnu_student_view import ntnu_school_location
            location = ntnu_school_location(partner, location, resolved_data_dir)
        if university.id == CYCU.id:
            from .cycu_student_view import cycu_school_location
            location = cycu_school_location(partner, location, resolved_data_dir)
        if university.id == NTUST.id:
            from .ntust_student_view import ntust_school_location
            location = ntust_school_location(partner, location, resolved_data_dir)
        if university.id == YZU.id:
            from .yzu_student_view import yzu_school_location
            location = yzu_school_location(partner, location, resolved_data_dir)
        if university.id == FCU.id:
            from .fcu_student_view import fcu_school_location
            location = fcu_school_location(partner, location, resolved_data_dir)
        if university.id == NSYSU.id:
            from .nsysu_student_view import nsysu_school_location
            location = nsysu_school_location(partner, location, resolved_data_dir)
        if university.id == NCHU.id:
            from .nchu_student_view import nchu_school_location
            location = nchu_school_location(partner, location, resolved_data_dir)
        if university.id == NTUT.id:
            from .ntut_student_view import ntut_school_location
            location = ntut_school_location(partner, location, resolved_data_dir)
        if university.id == NCCU.id:
            from .nccu_student_view import nccu_school_location
            location = nccu_school_location(partner, location, resolved_data_dir)
        if university.id == NCKU.id:
            from .ncku_student_view import ncku_school_location
            location = ncku_school_location(partner, location, resolved_data_dir)
        if university.id == NYCU.id:
            from .nycu_student_view import nycu_school_location
            location = nycu_school_location(partner, location, resolved_data_dir)
        if university.id == NTHU.id:
            from .nthu_student_view import nthu_school_location
            location = nthu_school_location(partner, location, resolved_data_dir)
        if university.id == PCCU.id:
            from .pccu_student_view import pccu_school_location
            location = pccu_school_location(partner, location, resolved_data_dir)
        if university.id == WZU.id:
            from .wzu_student_view import wzu_school_location
            location = wzu_school_location(partner, location, resolved_data_dir)
        if university.id == NKUST.id:
            from .nkust_student_view import nkust_school_location
            location = nkust_school_location(partner, location, resolved_data_dir)
        if university.id == YUNTECH.id:
            from .yuntech_student_view import yuntech_school_location
            location = yuntech_school_location(partner, location, resolved_data_dir)
        if university.id == NTOU.id:
            from .ntou_student_view import ntou_school_location
            location = ntou_school_location(partner, location, resolved_data_dir)
        profile = destination_profile(school, home_school)
        context = build_life_context(partner, profile, location, resolved_data_dir)
        if university.id == "ccu":
            from .ccu_profile import align_life_context
            return align_life_context(context, partner, profile, location)
        return context

    @app.post("/school-life-context/refresh", response_model=SchoolLifeContext)
    def refresh_school_life_context(
        school: str = Query(min_length=2),
        home_school: str | None = Query(default=None),
    ) -> SchoolLifeContext:
        university, partner = partner_context_for_school(school, home_school)
        location = public_location(load_university_locations(resolved_data_dir), partner.school_name, partner.country)
        if university.id == NCU.id:
            from .ncu_completion import campus_location
            location = campus_location(partner, location, resolved_data_dir)
        if university.id == "ccu":
            from .ccu_profile import school_location
            location = school_location(partner, location, resolved_data_dir)
        if university.id == "tku":
            from .tku_assets import school_location
            location = school_location(partner, resolved_data_dir)
        if university.id == FJU.id:
            from .fju_student_view import fju_school_location
            location = fju_school_location(partner, location, resolved_data_dir)
        if university.id == SCU.id:
            from .scu_student_view import scu_school_location
            location = scu_school_location(partner, location, resolved_data_dir)
        if university.id == NTNU.id:
            from .ntnu_student_view import ntnu_school_location
            location = ntnu_school_location(partner, location, resolved_data_dir)
        if university.id == CYCU.id:
            from .cycu_student_view import cycu_school_location
            location = cycu_school_location(partner, location, resolved_data_dir)
        if university.id == NTUST.id:
            from .ntust_student_view import ntust_school_location
            location = ntust_school_location(partner, location, resolved_data_dir)
        if university.id == YZU.id:
            from .yzu_student_view import yzu_school_location
            location = yzu_school_location(partner, location, resolved_data_dir)
        if university.id == FCU.id:
            from .fcu_student_view import fcu_school_location
            location = fcu_school_location(partner, location, resolved_data_dir)
        if university.id == NSYSU.id:
            from .nsysu_student_view import nsysu_school_location
            location = nsysu_school_location(partner, location, resolved_data_dir)
        if university.id == NCHU.id:
            from .nchu_student_view import nchu_school_location
            location = nchu_school_location(partner, location, resolved_data_dir)
        if university.id == NTUT.id:
            from .ntut_student_view import ntut_school_location
            location = ntut_school_location(partner, location, resolved_data_dir)
        if university.id == NCCU.id:
            from .nccu_student_view import nccu_school_location
            location = nccu_school_location(partner, location, resolved_data_dir)
        if university.id == NCKU.id:
            from .ncku_student_view import ncku_school_location
            location = ncku_school_location(partner, location, resolved_data_dir)
        if university.id == NYCU.id:
            from .nycu_student_view import nycu_school_location
            location = nycu_school_location(partner, location, resolved_data_dir)
        if university.id == NTHU.id:
            from .nthu_student_view import nthu_school_location
            location = nthu_school_location(partner, location, resolved_data_dir)
        if university.id == PCCU.id:
            from .pccu_student_view import pccu_school_location
            location = pccu_school_location(partner, location, resolved_data_dir)
        if university.id == WZU.id:
            from .wzu_student_view import wzu_school_location
            location = wzu_school_location(partner, location, resolved_data_dir)
        if university.id == NKUST.id:
            from .nkust_student_view import nkust_school_location
            location = nkust_school_location(partner, location, resolved_data_dir)
        if university.id == YUNTECH.id:
            from .yuntech_student_view import yuntech_school_location
            location = yuntech_school_location(partner, location, resolved_data_dir)
        if university.id == NTOU.id:
            from .ntou_student_view import ntou_school_location
            location = ntou_school_location(partner, location, resolved_data_dir)
        result = refresh_life_research(partner, location, resolved_data_dir)
        context = school_life_context(school, home_school)
        return context.model_copy(update={"research_notes": result.notes})

    @app.get("/destination-profiles", response_model=list[DestinationProfile])
    def destination_profiles(
        home_school: str | None = Query(default=None),
        compact: bool = Query(
            default=False,
            description="Leave out the long guide sections and checklists and the per-source summaries; "
                        "/destination-profile?school= returns a school's full profile.",
        ),
    ) -> list[DestinationProfile]:
        university = university_for(home_school)
        names = {school_identity_key(p.school_name) for p in partners_for_university(university)}
        locations = load_university_locations(resolved_data_dir)
        profiles = [complete_destination_profile(row, resolved_data_dir, locations=locations) for row in published_destination_profiles(university.school_name)
                    if school_identity_key(row.school_name) in names
                    and (not row.home_university or normalize_school(row.home_university) == normalize_school(university.school_name))]
        if not compact:
            return profiles
        # The partner list, search and budget views only read a profile's summaries, city and source titles and links;
        # the guide sections and checklists were about two thirds of the 1.8 MB every visitor downloaded on every load.
        return [
            profile.model_copy(update={
                "student_guide_sections": [],
                "first_72_hours": [],
                "packing_from_taiwan": [],
                "buy_after_arrival": [],
                "sources": [
                    SourceReference(title=source.title, source_url=source.source_url, category=source.category)
                    for source in profile.sources
                ],
            })
            for profile in profiles
        ]

    @app.post("/destination-profile/refresh", response_model=DestinationProfile)
    def refresh_destination_profile(
        school: str = Query(min_length=2),
        home_school: str | None = Query(default=None),
    ) -> DestinationProfile:
        university, partner = partner_context_for_school(school, home_school)
        with workflow_collection_lock:
            if not partner.website:
                research = discover_partner_official_site(
                    partner,
                    home_university=university.school_name,
                )
                upsert_partner_research(research, resolved_data_dir)
                if research.official_website:
                    partner = partner.model_copy(
                        update={"website": research.official_website}
                    )
            profile = collect_destination_profile(partner)
            existing = next(
                (
                    row
                    for row in load_destination_profiles(resolved_data_dir)
                    if normalize_school(row.school_name)
                    == normalize_school(partner.school_name)
                ),
                None,
            )
            quality = {
                "not_collected": 0,
                "not_found": 1,
                "official_partial": 2,
                "official_verified": 3,
            }
            if existing and quality.get(existing.coverage_status, 0) > quality.get(
                profile.coverage_status, 0
            ):
                profile = existing
            else:
                upsert_destination_profile(profile, resolved_data_dir)
            upsert_collection_audit(
                CollectionAudit(
                    school_name=partner.school_name,
                    collector="destinations",
                    status=profile.coverage_status,
                    home_university=university.school_name,
                    result_count=len(profile.sources),
                    note=profile.coverage_note,
                    checked_at=profile.last_checked or utc_now(),
                ),
                resolved_data_dir,
            )
        return profile

    @app.post(
        "/application-workflow/refresh",
        response_model=UniversityApplicationWorkflow,
    )
    def refresh_application_workflow(
        school: str = Query(min_length=2),
        home_school: str | None = Query(default=None),
    ) -> UniversityApplicationWorkflow:
        university, partner = partner_context_for_school(school, home_school)
        with workflow_collection_lock:
            if not partner.website:
                research = discover_partner_official_site(
                    partner,
                    home_university=university.school_name,
                )
                upsert_partner_research(research, resolved_data_dir)
                if research.official_website:
                    partner = partner.model_copy(
                        update={"website": research.official_website}
                    )
            workflow = collect_application_workflow(
                partner,
                home_university=university.school_name,
            )
            replace_application_workflow(workflow, resolved_data_dir)
            upsert_collection_audit(
                CollectionAudit(
                    school_name=partner.school_name,
                    collector="workflows",
                    status=workflow.coverage_status,
                    home_university=university.school_name,
                    result_count=len(workflow.steps),
                    note=workflow.coverage_note,
                    checked_at=workflow.last_checked or utc_now(),
                ),
                resolved_data_dir,
            )
        return workflow

    @app.get(
        "/community/questions",
        response_model=list[CommunityQuestionThread],
    )
    def community_questions(
        school: str = Query(min_length=2),
        home_school: str | None = Query(default=None),
    ) -> list[CommunityQuestionThread]:
        partner = partner_for_school(school, home_school)
        normalized = normalize_school(partner.school_name)
        questions = [
            question
            for question in load_community_questions(resolved_data_dir)
            if normalize_school(question.school_name) == normalized
            and question.status == ModerationStatus.APPROVED
        ]
        answers = [
            answer
            for answer in load_community_answers(resolved_data_dir)
            if answer.status == ModerationStatus.APPROVED
        ]
        answers_by_question: dict[str, list[CommunityAnswer]] = {}
        for answer in answers:
            answers_by_question.setdefault(answer.question_id, []).append(answer)
        return [
            CommunityQuestionThread(
                question=question.model_copy(
                    update={"answer_count": len(answers_by_question.get(question.id, []))}
                ),
                answers=sorted(
                    answers_by_question.get(question.id, []),
                    key=lambda answer: answer.created_at,
                ),
            )
            for question in sorted(questions, key=lambda question: question.created_at, reverse=True)
        ]

    @app.post(
        "/community/questions",
        response_model=CommunityQuestion,
        status_code=202,
    )
    def create_community_question(payload: CommunityQuestionCreate) -> CommunityQuestion:
        partner = partner_for_school(payload.school_name)
        _reject_contact_details(payload.title, payload.body, payload.display_name)
        question = CommunityQuestion(
            school_name=partner.school_name,
            home_university=payload.home_university.strip(),
            topic=payload.topic,
            title=payload.title.strip(),
            body=payload.body.strip(),
            display_name=payload.display_name.strip(),
        )
        with community_lock:
            return append_community_question(question, resolved_data_dir)

    @app.post(
        "/community/questions/{question_id}/answers",
        response_model=CommunityAnswer,
        status_code=202,
    )
    def create_community_answer(
        question_id: str,
        payload: CommunityAnswerCreate,
    ) -> CommunityAnswer:
        questions = load_community_questions(resolved_data_dir)
        if not any(question.id == question_id for question in questions):
            raise HTTPException(status_code=404, detail="Question not found.")
        _reject_contact_details(payload.body, payload.display_name)
        answer = CommunityAnswer(
            question_id=question_id,
            body=payload.body.strip(),
            display_name=payload.display_name.strip(),
            exchange_year=payload.exchange_year.strip() if payload.exchange_year else None,
        )
        with community_lock:
            return append_community_answer(answer, resolved_data_dir)

    @app.post(
        "/community/identities",
        response_model=AnonymousIdentitySession,
        status_code=201,
    )
    def create_anonymous_identity(payload: AnonymousIdentityCreate) -> AnonymousIdentitySession:
        display_name = payload.display_name.strip()
        _reject_contact_details(display_name)
        access_token = secrets.token_urlsafe(32)
        identity = AnonymousIdentity(
            display_name=display_name,
            access_token_hash=hashlib.sha256(access_token.encode("utf-8")).hexdigest(),
        )
        with community_lock:
            append_anonymous_identity(identity, resolved_data_dir)
        return AnonymousIdentitySession(
            id=identity.id,
            display_name=identity.display_name,
            access_token=access_token,
        )

    def community_board_access(account: UserAccount | None) -> list[CommunityBoardAccess]:
        boards = [
            ("public-study-abroad", PUBLIC_COMMUNITY_BOARD, "public_study_abroad", None),
            ("language-school", "語言學校板", "public_topic", None),
            *[(school.id, f"{school.short_name}板", "university_exchange", school.school_name)
              for school in SUPPORTED_UNIVERSITIES],
        ]
        result = []
        for board_id, label, kind, school_name in boards:
            reason = None
            if not account:
                reason = "請先登入"
            elif account.community_suspended_until and account.community_suspended_until > utc_now():
                reason = "帳號暫停發言中"
            elif not account.email_verified:
                reason = "請先驗證電子郵件"
            result.append(CommunityBoardAccess(
                id=board_id, label=label, kind=kind, school_name=school_name,
                posting_requirement="verified_email",
                can_read=kind != "university_exchange" or can_read_university_community(account),
                can_post=reason is None, can_comment=reason is None, unavailable_reason=reason,
            ))
        return result

    @app.get("/community/boards", response_model=list[CommunityBoardAccess])
    def community_boards(request: Request, response: Response):
        response.headers["Cache-Control"] = "private, no-store"
        response.headers["Vary"] = "Cookie, Authorization"
        account = authenticated_account(request)[0] if request_token(request) else None
        return community_board_access(account)

    def require_community_writer(request: Request, identity: AnonymousIdentity, board_id: str):
        account, _ = authenticated_account(request)
        if identity.account_id != account.id:
            raise HTTPException(status_code=403, detail="發言身分與登入帳號不符。")
        board = next((row for row in community_board_access(account) if row.id == board_id), None)
        if board is None or not board.can_post:
            raise HTTPException(status_code=403, detail=board.unavailable_reason if board else "此看板無法發言。")
        return account, board

    def community_author_name(account: UserAccount, mode: CommunityIdentityMode) -> str:
        name = community_author_display_name(account, mode)
        if name is None:
            raise HTTPException(403, "尚無已驗證學籍或系所；自填母校不代表學籍認證。")
        return name

    @app.get("/community/posts", response_model=list[CommunityPostThread])
    def community_posts(
        request: Request,
        response: Response,
        school: str | None = Query(default=None, min_length=2),
        board_id: str | None = Query(default=None),
        topic: CommunityTopic | None = Query(default=None),
        q: str | None = Query(default=None, max_length=80),
        limit: int = Query(default=60, ge=1, le=120),
    ) -> list[CommunityPostThread]:
        response.headers["Cache-Control"] = "private, no-store"
        response.headers["Vary"] = "Cookie, Authorization"
        account = authenticated_account(request)[0] if request_token(request) else None
        own_ids = {row.id for row in comm_repo.list_identities() if account and row.account_id == account.id} if account else set()
        target_board = board_id or school
        if university_community_board(target_board) and not can_read_university_community(account):
            raise HTTPException(403 if account else 401, "校級看板限已驗證 Email 的會員查看，不限同校。")
        normalized_boards: set[str] = set()
        if target_board:
            if target_board in {
                PUBLIC_COMMUNITY_BOARD,
                LEGACY_PUBLIC_COMMUNITY_BOARD,
                "public-study-abroad",
            }:
                normalized_boards = {
                    normalize_school(PUBLIC_COMMUNITY_BOARD),
                    normalize_school(LEGACY_PUBLIC_COMMUNITY_BOARD),
                }
            elif target_board in {"language-school", "語言學校板"}:
                normalized_boards = {normalize_school("語言學校板")}
            elif (home_university := university_community_board(target_board)) is not None:
                normalized_boards = {normalize_school(home_university.school_name)}
            elif target_board == "cgu":
                normalized_boards = {normalize_school("長庚大學")}
            else:
                normalized_boards = {
                    normalize_school(partner_for_school(target_board).school_name)
                }
        normalized_query = _normalize_text(q) if q else ""
        comments = [
            row
            for row in comm_repo.list_comments()
            if row.status == ModerationStatus.APPROVED
        ]
        comments_by_post: dict[str, list[CommunityPostComment]] = {}
        for comment in comments:
            comments_by_post.setdefault(comment.post_id, []).append(comment)
        posts = [
            row
            for row in comm_repo.list_posts()
            if (
                (
                    not normalized_boards
                    or normalize_school(row.school_name) in normalized_boards
                    or (row.board_id and row.board_id == target_board)
                )
            )
            and (topic is None or row.topic == topic)
            and (
                not normalized_query
                or normalized_query
                in _normalize_text(
                    " ".join(
                        [
                            row.title,
                            row.body,
                            row.school_name,
                            row.country or "",
                            row.academic_year or "",
                        ]
                    )
                )
            )
            and row.status == ModerationStatus.APPROVED
            and (not is_university_community_post(row) or can_read_university_community(account))
        ]
        return [
            CommunityPostThread(
                post=post.model_copy(
                    update={"comment_count": len(comments_by_post.get(post.id, [])), "author_id": "",
                            "viewer_can_delete": post.author_id in own_ids and not getattr(post, "deleted", False)}
                ),
                comments=sorted(
                    [row.model_copy(update={"author_id": "", "viewer_can_delete": row.author_id in own_ids and not row.deleted})
                     for row in comments_by_post.get(post.id, [])],
                    key=lambda row: row.created_at
                ),
            )
            for post in sorted(posts, key=lambda row: row.created_at, reverse=True)[:limit]
        ]

    @app.post("/community/posts", response_model=CommunityPost, status_code=201)
    def create_community_post(
        payload: CommunityPostCreate,
        request: Request,
        identity_id: str | None = Header(default=None, alias="X-Anonymous-ID"),
        access_token: str | None = Header(default=None, alias="X-Anonymous-Token"),
    ) -> CommunityPost:
        identity = anonymous_identity(identity_id, access_token)
        target = (payload.board_id or payload.school_name or "").strip()
        def canonical_board(value):
            if value in {PUBLIC_COMMUNITY_BOARD, LEGACY_PUBLIC_COMMUNITY_BOARD, "public-study-abroad"}:
                return "public-study-abroad"
            if value in {"language-school", "語言學校板"}:
                return "language-school"
            university = university_community_board(value)
            return university.id if university else None
        if payload.board_id and payload.school_name and canonical_board(payload.board_id) != canonical_board(payload.school_name):
            raise HTTPException(422, "看板識別碼與學校名稱不一致，或看板不存在。")
        if target in {
            PUBLIC_COMMUNITY_BOARD,
            LEGACY_PUBLIC_COMMUNITY_BOARD,
            "public-study-abroad",
        }:
            board_id = "public-study-abroad"
            school_name = PUBLIC_COMMUNITY_BOARD
        elif target in {"language-school", "語言學校板"}:
            board_id = "language-school"
            school_name = "語言學校板"
        elif (home_university := university_community_board(target)) is not None:
            board_id = "cgu" if home_university.id == "cgu" else home_university.id
            school_name = home_university.school_name
        elif target == "cgu":
            board_id = "cgu"
            school_name = "長庚大學"
        else:
            raise HTTPException(status_code=422, detail="此討論板不存在或不支援建立貼文。")
        account, board = require_community_writer(request, identity, board_id)
        _reject_contact_details(payload.title, payload.body)
        post = CommunityPost(
            board_id=board_id,
            board_kind=board.kind,
            school_name=school_name,
            author_id=identity.id,
            display_name=community_author_name(account, payload.identity_mode),
            identity_mode=payload.identity_mode,
            post_type=payload.post_type,
            topic=payload.topic,
            country=payload.country.strip() if payload.country else None,
            academic_year=(
                payload.academic_year.strip() if payload.academic_year else None
            ),
            application_stage=(
                payload.application_stage.strip()
                if payload.application_stage
                else None
            ),
            title=payload.title.strip(),
            body=payload.body.strip(),
        )
        published = publish_discussion(request, account, identity, post, "post")
        analytics_service.emit(
            "post_created", props={"board": board_id, "identity_mode": payload.identity_mode.value,
                                   "post_type": getattr(payload.post_type, "value", payload.post_type)},
            home_school=catalog_home_university(account) or "", school_basis=school_basis(account) or "")
        return published.model_copy(update={"author_id": "", "viewer_can_delete": True})

    @app.post(
        "/community/posts/{post_id}/comments",
        response_model=CommunityPostComment,
        status_code=201,
    )
    def create_community_post_comment(
        post_id: str,
        payload: CommunityPostCommentCreate,
        request: Request,
        identity_id: str | None = Header(default=None, alias="X-Anonymous-ID"),
        access_token: str | None = Header(default=None, alias="X-Anonymous-Token"),
    ) -> CommunityPostComment:
        identity = anonymous_identity(identity_id, access_token)
        parent = next((row for row in comm_repo.list_posts()
                       if row.id == post_id and row.status == ModerationStatus.APPROVED), None)
        if parent is None:
            raise HTTPException(status_code=404, detail="找不到這篇貼文。")
        board_id = parent.board_id
        if not board_id:
            home = resolve_university(parent.school_name)
            board_id = home.id if home else (
                "language-school" if parent.school_name == "語言學校板" else "public-study-abroad"
            )
        account, _ = require_community_writer(request, identity, board_id)
        _reject_contact_details(payload.body)
        comment = CommunityPostComment(
            post_id=post_id,
            parent_id=payload.parent_id,
            author_id=identity.id,
            display_name=community_author_name(account, payload.identity_mode),
            identity_mode=payload.identity_mode,
            body=payload.body.strip(),
        )
        published = publish_discussion(request, account, identity, comment, "comment")
        analytics_service.emit(
            "comment_created", props={"board": board_id, "identity_mode": payload.identity_mode.value},
            home_school=catalog_home_university(account) or "", school_basis=school_basis(account) or "")
        return published.model_copy(update={"author_id": "", "viewer_can_delete": True})

    @app.get("/community/chat", response_model=list[PublicChatMessage])
    def public_chat_messages(
        school: str = Query(min_length=2),
        home_school: str | None = Query(default=None),
        limit: int = Query(default=80, ge=1, le=200),
    ) -> list[PublicChatMessage]:
        partner = partner_for_school(school, home_school)
        normalized = normalize_school(partner.school_name)
        messages = [
            row
            for row in load_public_chat_messages(resolved_data_dir)
            if normalize_school(row.school_name) == normalized
            and row.status == ModerationStatus.APPROVED
        ]
        return sorted(messages, key=lambda row: row.created_at)[-limit:]

    @app.post("/community/chat", response_model=PublicChatMessage, status_code=201)
    def create_public_chat_message(
        payload: PublicChatMessageCreate,
        identity_id: str | None = Header(default=None, alias="X-Anonymous-ID"),
        access_token: str | None = Header(default=None, alias="X-Anonymous-Token"),
    ) -> PublicChatMessage:
        identity = anonymous_identity(identity_id, access_token)
        partner = partner_for_school(payload.school_name)
        _reject_contact_details(payload.body)
        message = PublicChatMessage(
            school_name=partner.school_name,
            author_id=identity.id,
            display_name=identity.display_name,
            body=payload.body.strip(),
        )
        with community_lock:
            return append_public_chat_message(message, resolved_data_dir)

    @app.get("/community/conversations", response_model=list[PrivateConversation])
    def private_conversations(
        identity_id: str | None = Header(default=None, alias="X-Anonymous-ID"),
        access_token: str | None = Header(default=None, alias="X-Anonymous-Token"),
    ) -> list[PrivateConversation]:
        identity = anonymous_identity(identity_id, access_token)
        return sorted(
            [
                row
                for row in comm_repo.list_private_conversations()
                if identity.id in {row.sender_id, row.recipient_id}
                and not is_blocked(row.sender_id, row.recipient_id)
            ],
            key=lambda row: row.updated_at,
            reverse=True,
        )

    def private_mutation_actor(request: Request, identity_id: str | None, access_token: str | None):
        account, _ = authenticated_account(request)
        identity = anonymous_identity(identity_id, access_token)
        if identity.account_id != account.id:
            raise HTTPException(403, "私訊身分與登入帳號不符。")
        if account.community_suspended_until and account.community_suspended_until > utc_now():
            raise HTTPException(403, "帳號暫停發言中。")
        return {"account_id": account.id, "identity_id": identity.id,
                "access_token_hash": identity.access_token_hash}, identity

    def commit_private_mutation(method, mutation, response: Response, resource: str):
        response.headers["Cache-Control"] = "private, no-store"
        response.headers["X-Community-Mutation-ID"] = mutation.mutation_id
        try:
            result = method(mutation)
        except CommunityRepositoryError as error:
            raise HTTPException(503, "私訊操作暫時失敗，請保留操作識別碼後重試。") from error
        if result.status == PrivateCommunityMutationStatus.COMMITTED:
            value = getattr(result, resource)
            if value is not None:
                return value
            raise HTTPException(503, "私訊操作結果不完整，請稍後重試。")
        if result.status == PrivateCommunityMutationStatus.IDEMPOTENCY_CONFLICT:
            raise HTTPException(409, "操作識別碼已用於不同內容，請重新送出。")
        if result.status in {PrivateCommunityMutationStatus.ACCOUNT_MISSING,
                             PrivateCommunityMutationStatus.IDENTITY_MISSING}:
            raise HTTPException(401, "私訊身分已失效，請重新登入。")
        if result.status == PrivateCommunityMutationStatus.CONVERSATION_MISSING:
            raise HTTPException(404, "找不到這段私訊。")
        if resource == "block" and result.status == PrivateCommunityMutationStatus.RECIPIENT_MISSING:
            raise HTTPException(404, "找不到要封鎖的匿名身分。")
        if result.status in {PrivateCommunityMutationStatus.SELF_TARGET,
                             PrivateCommunityMutationStatus.RECIPIENT_MISSING,
                             PrivateCommunityMutationStatus.INVALID_REQUEST}:
            raise HTTPException(422, "無法向這個匿名身分發送邀請或封鎖。")
        if result.status in {PrivateCommunityMutationStatus.STATUS_CONFLICT,
                             PrivateCommunityMutationStatus.INTEGRITY_CONFLICT}:
            raise HTTPException(409, "邀請狀態已變更；對方接受邀請後才能繼續私訊。")
        raise HTTPException(403, "無法執行這段私訊操作。")

    @app.post(
        "/community/conversations",
        response_model=PrivateConversation,
        status_code=201,
    )
    def create_private_conversation(
        payload: PrivateConversationCreate,
        request: Request,
        response: Response,
        identity_id: str | None = Header(default=None, alias="X-Anonymous-ID"),
        access_token: str | None = Header(default=None, alias="X-Anonymous-Token"),
        mutation_id: str | None = Header(default=None, alias="X-Community-Mutation-ID", min_length=16, max_length=128),
    ) -> PrivateConversation:
        actor, sender = private_mutation_actor(request, identity_id, access_token)
        partner = partner_for_school(payload.school_name)
        _reject_contact_details(payload.initial_message)
        conversation = PrivateConversation(
            school_name=partner.school_name,
            sender_id=sender.id,
            sender_name=sender.display_name,
            recipient_id=payload.recipient_id,
            # The repository derives the recipient name after checking for a replay.
            recipient_name="匿名學生",
        )
        message = PrivateMessage(
            conversation_id=conversation.id,
            author_id=sender.id,
            display_name=sender.display_name,
            body=payload.initial_message.strip(),
        )
        return commit_private_mutation(comm_repo.commit_private_conversation,
            PrivateConversationMutationRequest(mutation_id=mutation_id or uuid4().hex,
                **actor, recipient_identity_id=payload.recipient_id,
                conversation=conversation, initial_message=message), response, "conversation")

    @app.post(
        "/community/conversations/{conversation_id}/accept",
        response_model=PrivateConversation,
    )
    def accept_private_conversation(
        conversation_id: str,
        request: Request,
        response: Response,
        identity_id: str | None = Header(default=None, alias="X-Anonymous-ID"),
        access_token: str | None = Header(default=None, alias="X-Anonymous-Token"),
        mutation_id: str | None = Header(default=None, alias="X-Community-Mutation-ID", min_length=16, max_length=128),
    ) -> PrivateConversation:
        actor, _ = private_mutation_actor(request, identity_id, access_token)
        return commit_private_mutation(comm_repo.commit_private_conversation_status,
            PrivateConversationStatusMutationRequest(mutation_id=mutation_id or uuid4().hex,
                **actor, conversation_id=conversation_id, expected_status=ConversationStatus.PENDING,
                status=ConversationStatus.ACCEPTED), response, "conversation")

    @app.get(
        "/community/conversations/{conversation_id}/messages",
        response_model=list[PrivateMessage],
    )
    def private_messages(
        conversation_id: str,
        identity_id: str | None = Header(default=None, alias="X-Anonymous-ID"),
        access_token: str | None = Header(default=None, alias="X-Anonymous-Token"),
    ) -> list[PrivateMessage]:
        identity = anonymous_identity(identity_id, access_token)
        conversation = private_conversation_for(identity.id, conversation_id)
        if is_blocked(conversation.sender_id, conversation.recipient_id):
            return []
        return sorted(
            [
                row
                for row in comm_repo.list_private_messages()
                if row.conversation_id == conversation.id
            ],
            key=lambda row: row.created_at,
        )

    @app.post(
        "/community/conversations/{conversation_id}/messages",
        response_model=PrivateMessage,
        status_code=201,
    )
    def create_private_message(
        conversation_id: str,
        payload: PrivateMessageCreate,
        request: Request,
        response: Response,
        identity_id: str | None = Header(default=None, alias="X-Anonymous-ID"),
        access_token: str | None = Header(default=None, alias="X-Anonymous-Token"),
        mutation_id: str | None = Header(default=None, alias="X-Community-Mutation-ID", min_length=16, max_length=128),
    ) -> PrivateMessage:
        actor, identity = private_mutation_actor(request, identity_id, access_token)
        _reject_contact_details(payload.body)
        message = PrivateMessage(
            conversation_id=conversation_id,
            author_id=identity.id,
            display_name=identity.display_name,
            body=payload.body.strip(),
        )
        return commit_private_mutation(comm_repo.commit_private_message,
            PrivateMessageMutationRequest(mutation_id=mutation_id or uuid4().hex,
                **actor, message=message), response, "message")

    @app.post("/community/blocks", response_model=CommunityBlock, status_code=201)
    def block_community_identity(
        payload: CommunityBlockCreate,
        request: Request,
        response: Response,
        identity_id: str | None = Header(default=None, alias="X-Anonymous-ID"),
        access_token: str | None = Header(default=None, alias="X-Anonymous-Token"),
        mutation_id: str | None = Header(default=None, alias="X-Community-Mutation-ID", min_length=16, max_length=128),
    ) -> CommunityBlock:
        actor, identity = private_mutation_actor(request, identity_id, access_token)
        block = CommunityBlock(owner_id=identity.id, target_id=payload.target_id)
        return commit_private_mutation(comm_repo.commit_block,
            CommunityBlockMutationRequest(mutation_id=mutation_id or uuid4().hex,
                **actor, block=block), response, "block")

    @app.post("/community/reports", response_model=CommunityReport, status_code=202)
    def report_community_content(
        payload: CommunityReportCreate,
        request: Request,
        identity_id: str | None = Header(default=None, alias="X-Anonymous-ID"),
        access_token: str | None = Header(default=None, alias="X-Anonymous-Token"),
        mutation_id: str | None = Header(default=None, alias="X-Community-Mutation-ID", min_length=16, max_length=128),
    ) -> CommunityReport:
        identity = anonymous_identity(identity_id, access_token)
        report = CommunityReport(
            reporter_id=identity.id,
            resource_type=payload.resource_type,
            resource_id=payload.resource_id,
            reason=payload.reason.strip(),
        )
        return submit_discussion_report(request, identity, report, mutation_id=mutation_id)

    @app.post(
        "/experience-submissions",
        response_model=ExperienceSubmission,
        status_code=202,
    )
    def create_experience_submission(
        payload: ExperienceSubmissionCreate,
        request: Request,
    ) -> ExperienceSubmission:
        partner = partner_for_school(payload.school_name)
        _reject_contact_details(payload.title, payload.summary, payload.display_name)
        if payload.source_url and not re.match(r"^https?://", payload.source_url, re.IGNORECASE):
            raise HTTPException(status_code=422, detail="Source URL must use http or https.")
        author_id = None
        display_name = (payload.display_name or "匿名投稿者").strip()
        try:
            account, _ = authenticated_account(request)
            author_id = account.id
            if getattr(payload, "identity_mode", None) == CommunityIdentityMode.REAL_NAME:
                display_name = account.display_name
        except HTTPException:
            pass

        submission = ExperienceSubmission(
            school_name=partner.school_name,
            home_university=payload.home_university.strip(),
            title=payload.title.strip(),
            summary=payload.summary.strip(),
            exchange_year=payload.exchange_year.strip(),
            themes=list(dict.fromkeys(theme.strip() for theme in payload.themes if theme.strip())),
            source_url=payload.source_url.strip() if payload.source_url else None,
            display_name=display_name,
            identity_mode=getattr(payload, "identity_mode", CommunityIdentityMode.ANONYMOUS),
            author_id=author_id,
        )
        with community_lock:
            return append_experience_submission(submission, resolved_data_dir)

    @app.get("/search", response_model=list[SearchResult])
    def search(
        q: str = Query(min_length=1),
        school: str | None = Query(default=None),
        limit: int = Query(default=20, ge=1, le=100),
    ) -> list[SearchResult]:
        query = q.strip().lower()
        pages = pages_for_university(school)
        results: list[SearchResult] = []
        for page in pages:
            haystack = f"{page.title}\n{page.category.value}\n{page.text}".lower()
            if query not in haystack:
                continue
            results.append(
                SearchResult(
                    title=page.title,
                    source_url=page.source_url,
                    category=page.category,
                    snippet=_snippet(page.text, query),
                    published_at=page.published_at,
                    attachments=page.attachments,
                )
            )
            if len(results) >= limit:
                break
        return results

    from .community_browsing import install_community_browsing
    publish_discussion, create_discussion_identity, submit_discussion_report = install_community_browsing(app, comm_repo, authenticated_account,
        authenticated_content_admin, app.state.account_repository, anonymous_identity)

    from .maintenance.routes import build_default_maintenance_router
    maint_router, maint_store = build_default_maintenance_router(resolved_data_dir)
    app.state.maintenance_store = maint_store
    app.include_router(maint_router)
    return app


def _deadline_snippets(text: str, triggers: list[str]) -> list[str]:
    snippets: list[str] = []
    for line in text.splitlines():
        compact = re.sub(r"\s+", " ", line).strip()
        if not compact:
            continue
        if any(trigger.lower() in compact.lower() for trigger in triggers):
            snippets.append(compact[:240])
    return snippets


def _snippet(text: str, query: str, radius: int = 90) -> str:
    compact = re.sub(r"\s+", " ", text).strip()
    index = compact.lower().find(query)
    if index < 0:
        return compact[: radius * 2]
    start = max(0, index - radius)
    end = min(len(compact), index + len(query) + radius)
    prefix = "..." if start > 0 else ""
    suffix = "..." if end < len(compact) else ""
    return f"{prefix}{compact[start:end].strip()}{suffix}"


def _reject_contact_details(*values: str) -> None:
    text = unicodedata.normalize("NFKC", " ".join(values))
    identity_pattern = re.compile(
        r"(?:護照(?:號碼|編號)?|身[分份]證(?:字號|號碼)?|"
        r"passport(?:\s*(?:number|no\.?))?|(?:national\s+)?id(?:entification)?(?:\s*(?:number|no\.?))?)"
        r"\s*[:#]?\s*[A-Z]{0,3}\d{6,12}(?![A-Z0-9])", re.IGNORECASE,
    )
    if identity_pattern.search(text):
        raise HTTPException(422, "請不要填寫護照號碼或身分證字號等敏感身分資料。")
    contact_pattern = re.compile(
        r"[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}|"
        r"(?:\+?886[-\s]?)?0?9\d{2}[-\s]?\d{3}[-\s]?\d{3}|"
        r"(?:LINE|IG|Instagram|Telegram|Discord)\s*(?:ID|帳號)?\s*[:：]?\s*[A-Z0-9_.-]{4,}",
        re.IGNORECASE,
    )
    if contact_pattern.search(text):
        raise HTTPException(
            status_code=422,
            detail="請不要填寫 Email、電話或社群帳號等個人聯絡資料。",
        )


app = create_app()
