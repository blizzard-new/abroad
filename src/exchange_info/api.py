from __future__ import annotations

import hashlib
import json
import mimetypes
import os
import re
import secrets
import threading
from datetime import datetime, timedelta
from functools import partial
from pathlib import Path
from urllib.parse import quote, urlencode

import requests
from fastapi import FastAPI, File, Form, Header, HTTPException, Query, Request, Response, UploadFile
from fastapi.responses import FileResponse, PlainTextResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from starlette.concurrency import run_in_threadpool

from .advisor import answer_question, build_advisor_plan
from .ai_gateway import (
    ai_embedding_model,
    ai_enabled,
    ai_model,
    ai_provider_name,
)
from .application_workflow_collector import collect_application_workflow
from .partner_research import (
    apply_partner_research,
    collect_destination_profile,
    discover_partner_official_site,
)
from .application_documents import (
    all_application_templates,
    build_packet_manifest,
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
from .document_checker import MAX_DOCUMENT_BYTES, check_document
from .document_rewriter import DocumentRewriteUnavailable, rewrite_document
from .models import (
    AccountLogin,
    AccountProfile,
    AccountProfileUpdate,
    AccountProviderLink,
    AccountRegister,
    AccountSession,
    AccountSessionRecord,
    AccountCalendarEvent,
    ApplicationCenterContext,
    ApplicationDocumentTemplate,
    ApplicationPacketManifest,
    ApplicationPacketRequest,
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
    SearchResult,
    PrivateConversation,
    PrivateConversationCreate,
    PrivateMessage,
    PrivateMessageCreate,
    PublicChatMessage,
    PublicChatMessageCreate,
    StudentExperienceDigest,
    StudentDashboard,
    StudentVerificationResult,
    StructuredSourceRecord,
    SupportedUniversity,
    SourceSummary,
    UniversityApplicationWorkflow,
    UserAccount,
    utc_now,
)
from .ntpu_student_view import (
    build_ntpu_student_dashboard,
    fetch_ntpu_partner_universities,
    ntpu_exchange_info,
    ntpu_processed_pages,
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


def _calendar_feed_content(events: list[AccountCalendarEvent]) -> str:
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
    for event in sorted(events, key=lambda item: (item.date, item.title)):
        start = datetime.strptime(event.date, "%Y-%m-%d")
        end = start + timedelta(days=1)
        description = event.note
        if event.source_url:
            description = f"{description}\n官方來源：{event.source_url}".strip()
        lines.extend(
            [
                "BEGIN:VEVENT",
                f"UID:{_escape_ics(event.id)}@exchange-guide.tw",
                f"DTSTAMP:{stamp}",
                f"DTSTART;VALUE=DATE:{start.strftime('%Y%m%d')}",
                f"DTEND;VALUE=DATE:{end.strftime('%Y%m%d')}",
                f"SUMMARY:{_escape_ics(f'[交換申請] {event.title}')}",
                f"DESCRIPTION:{_escape_ics(description)}",
                f"URL:{_escape_ics(event.source_url)}" if event.source_url else "",
                "END:VEVENT",
            ]
        )
    lines.append("END:VCALENDAR")
    return "\r\n".join(line for line in lines if line) + "\r\n"


from .settings import DEFAULT_DATA_DIR
from .school_identity import school_identity_key
from .storage import (
    append_anonymous_identity,
    append_community_answer,
    append_community_block,
    append_community_post,
    append_community_post_comment,
    append_community_question,
    append_community_report,
    append_experience_submission,
    append_private_conversation,
    append_private_message,
    append_public_chat_message,
    load_exchange_info,
    load_application_workflows,
    load_account_sessions,
    load_community_answers,
    load_community_blocks,
    load_community_post_comments,
    load_community_posts,
    load_community_questions,
    load_collection_audits,
    load_destination_profiles,
    load_partner_research,
    load_anonymous_identities,
    load_processed_pages,
    load_structured_sources,
    load_private_conversations,
    load_private_messages,
    load_public_chat_messages,
    load_student_experiences,
    load_user_accounts,
    replace_application_workflow,
    replace_school_experiences,
    save_private_conversations,
    save_account_sessions,
    save_anonymous_identities,
    save_user_accounts,
    upsert_collection_audit,
    upsert_destination_profile,
    upsert_partner_research,
)
from .student_view import build_student_dashboard, fetch_partner_universities
from .student_verification import StudentCardVerificationError, verify_student_cards
from .rag import rag_index_status, search_document_chunks, supabase_configured
from .university_registry import (
    CGU,
    NTPU,
    SUPPORTED_UNIVERSITIES,
    UniversityProfile,
    require_university,
    resolve_university,
)


STATIC_DIR = Path(__file__).resolve().parent / "static"
SCHOOL_IMAGE_MANIFEST = STATIC_DIR / "assets" / "school-images.json"
AUTH_COOKIE_NAME = "exchange_guide_session"
PASSWORD_ITERATIONS = 390_000
EMAIL_PATTERN = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")
PUBLIC_COMMUNITY_BOARD = "公共留學板"
LEGACY_PUBLIC_COMMUNITY_BOARD = "一般留學討論"
CGU_COMMUNITY_BOARD = "長庚大學"
HOME_UNIVERSITY_BOARDS = {item.school_name for item in SUPPORTED_UNIVERSITIES}
MAX_STUDENT_CARD_BYTES = 8 * 1024 * 1024
STUDENT_VERIFICATION_TTL = timedelta(minutes=15)


def _load_school_image_manifest() -> dict[str, dict[str, object]]:
    if not SCHOOL_IMAGE_MANIFEST.exists():
        return {}
    try:
        payload = json.loads(SCHOOL_IMAGE_MANIFEST.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return {
        school_identity_key(str(item.get("school_name", ""))): item
        for item in payload.get("schools", [])
        if isinstance(item, dict) and item.get("school_name")
    }


def _attach_school_images(
    dashboard: StudentDashboard,
    *,
    base_url: str,
) -> StudentDashboard:
    visuals = _load_school_image_manifest()
    base = base_url.rstrip("/")
    partners = []
    for school in dashboard.partner_universities:
        visual = visuals.get(school_identity_key(school.school_name))
        if not visual or visual.get("status") != "verified":
            partners.append(school)
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
        id=account.id,
        email=account.email,
        display_name=account.display_name,
        avatar_url=account.avatar_url,
        home_university=account.home_university,
        target_countries=account.target_countries,
        application_stage=account.application_stage,
        followed_boards=account.followed_boards,
        school_email_verified=account.school_email_verified,
        student_status_verified=account.student_status_verified,
        verified_university=account.verified_university,
        student_verified_at=account.student_verified_at,
        providers=providers,
        created_at=account.created_at,
        updated_at=account.updated_at,
    )


def create_app(data_dir: Path | None = None) -> FastAPI:
    resolved_data_dir = Path(
        data_dir or os.environ.get("EXCHANGE_INFO_DATA_DIR") or DEFAULT_DATA_DIR
    )
    app = FastAPI(
        title="Taiwan University Exchange Guide",
        version="0.1.0",
        description="Structured exchange-application information for supported universities in Taiwan.",
    )
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
    partner_cache: dict[str, list] = {}
    partner_cache_lock = threading.Lock()
    experience_collection_lock = threading.Lock()
    workflow_collection_lock = threading.Lock()
    community_lock = threading.Lock()
    auth_lock = threading.RLock()
    verification_lock = threading.Lock()
    oauth_states: dict[str, tuple[AuthProvider, datetime, str | None]] = {}
    student_verification_sessions: dict[str, dict[str, object]] = {}

    def student_verification_record(
        token: str | None,
        *,
        consume: bool,
    ) -> dict[str, object]:
        if not token:
            raise HTTPException(status_code=403, detail="請先完成學生證正反面驗證。")
        now = utc_now()
        token_hash = hashlib.sha256(token.encode("utf-8")).hexdigest()
        with verification_lock:
            expired = [
                key
                for key, row in student_verification_sessions.items()
                if row["expires_at"] <= now
            ]
            for key in expired:
                student_verification_sessions.pop(key, None)
            record = student_verification_sessions.get(token_hash)
            if record is None:
                raise HTTPException(status_code=403, detail="學生身分驗證已失效，請重新驗證。")
            if consume:
                student_verification_sessions.pop(token_hash, None)
        return record

    def account_session(account: UserAccount) -> AccountSession:
        access_token = secrets.token_urlsafe(40)
        expires_at = utc_now() + timedelta(days=30)
        record = AccountSessionRecord(
            account_id=account.id,
            token_hash=hashlib.sha256(access_token.encode("utf-8")).hexdigest(),
            expires_at=expires_at,
        )
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
            secure=os.environ.get("EXCHANGE_AUTH_SECURE_COOKIE", "0") == "1",
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
        account = next(
            (row for row in load_user_accounts(resolved_data_dir) if row.id == session.account_id),
            None,
        )
        if account is None:
            raise HTTPException(status_code=401, detail="找不到這個帳號。")
        return account, session

    def save_account_record(updated: UserAccount) -> UserAccount:
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
        public_base = os.environ.get("EXCHANGE_PUBLIC_BASE_URL", "").strip().rstrip("/")
        if not public_base:
            public_base = str(request.base_url).rstrip("/")
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
        public_base = os.environ.get("EXCHANGE_PUBLIC_BASE_URL", "").strip().rstrip("/")
        if not public_base:
            public_base = str(request.base_url).rstrip("/")
        return f"{public_base}/auth/oauth/{provider.value}/callback"

    def oauth_account(
        provider: AuthProvider,
        subject: str,
        email: str | None,
        display_name: str,
        avatar_url: str | None,
        student_verification_token: str | None = None,
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
                verification = student_verification_record(
                    student_verification_token,
                    consume=True,
                )
                account = UserAccount(
                    email=normalized_email,
                    display_name=(display_name or "留學同學")[:30],
                    avatar_url=avatar_url,
                    student_status_verified=True,
                    verified_university=str(verification["school_name"]),
                    student_verified_at=utc_now(),
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
                if student_verification_token and not account.student_status_verified:
                    verification = student_verification_record(
                        student_verification_token,
                        consume=True,
                    )
                    updates.update(
                        student_status_verified=True,
                        verified_university=str(verification["school_name"]),
                        student_verified_at=utc_now(),
                    )
                account = account.model_copy(update=updates)
                accounts = [account if row.id == account.id else row for row in accounts]
            save_user_accounts(accounts, resolved_data_dir)
            return account

    def university_for(school: str | None) -> UniversityProfile:
        try:
            return require_university(school)
        except ValueError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    def partners_for_university(school: str | UniversityProfile) -> list:
        university = school if isinstance(school, UniversityProfile) else university_for(school)
        if university.id not in partner_cache:
            with partner_cache_lock:
                if university.id not in partner_cache:
                    partner_cache[university.id] = (
                        fetch_ntpu_partner_universities()
                        if university.id == NTPU.id
                        else fetch_partner_universities()
                    )
        return apply_partner_research(
            partner_cache[university.id],
            load_partner_research(resolved_data_dir),
            home_university=university.school_name,
        )

    def workflows_for_university(
        school: str | UniversityProfile,
    ) -> list[UniversityApplicationWorkflow]:
        university = school if isinstance(school, UniversityProfile) else university_for(school)
        home_key = normalize_school(university.school_name)
        return [
            workflow
            for workflow in load_application_workflows(resolved_data_dir)
            if normalize_school(workflow.home_university) == home_key
        ]

    def pages_for_university(school: str | UniversityProfile):
        university = school if isinstance(school, UniversityProfile) else university_for(school)
        return (
            ntpu_processed_pages()
            if university.id == NTPU.id
            else load_processed_pages(resolved_data_dir)
        )

    def info_for_university(school: str | UniversityProfile) -> ExchangeInfo:
        university = school if isinstance(school, UniversityProfile) else university_for(school)
        if university.id == NTPU.id:
            return ntpu_exchange_info(partners_for_university(university))
        return load_exchange_info(resolved_data_dir) or ExchangeInfo(school_name=CGU.school_name)

    def dashboard_for_university(school: str | UniversityProfile) -> StudentDashboard:
        university = school if isinstance(school, UniversityProfile) else university_for(school)
        if university.id == NTPU.id:
            return build_ntpu_student_dashboard(
                partner_universities=partners_for_university(university)
            )
        return build_student_dashboard(
            load_processed_pages(resolved_data_dir),
            load_exchange_info(resolved_data_dir),
            raw_files_dir=resolved_data_dir / "raw_files",
        )

    def partner_context_for_school(
        school: str,
        home_school: str | None = None,
    ) -> tuple[UniversityProfile, object]:
        normalized = normalize_school(school)
        universities = (
            [university_for(home_school)]
            if home_school
            else list(SUPPORTED_UNIVERSITIES)
        )
        for university in universities:
            for partner in partners_for_university(university):
                if normalize_school(partner.school_name) == normalized:
                    return university, partner
        raise HTTPException(status_code=404, detail="這所學校不在目前支援大學的當期合作校名單中。")

    def partner_for_school(school: str, home_school: str | None = None):
        return partner_context_for_school(school, home_school)[1]

    def anonymous_identity(identity_id: str | None, access_token: str | None) -> AnonymousIdentity:
        if not identity_id or not access_token:
            raise HTTPException(status_code=401, detail="需要匿名身分才能使用此功能。")
        token_hash = hashlib.sha256(access_token.encode("utf-8")).hexdigest()
        for identity in load_anonymous_identities(resolved_data_dir):
            if identity.id == identity_id and secrets.compare_digest(
                identity.access_token_hash, token_hash
            ):
                return identity
        raise HTTPException(status_code=401, detail="匿名身分已失效，請重新建立。")

    def is_blocked(left_id: str, right_id: str) -> bool:
        return any(
            {block.owner_id, block.target_id} == {left_id, right_id}
            for block in load_community_blocks(resolved_data_dir)
        )

    def private_conversation_for(identity_id: str, conversation_id: str) -> PrivateConversation:
        conversation = next(
            (
                row
                for row in load_private_conversations(resolved_data_dir)
                if row.id == conversation_id
            ),
            None,
        )
        if conversation is None:
            raise HTTPException(status_code=404, detail="找不到這段私訊。")
        if identity_id not in {conversation.sender_id, conversation.recipient_id}:
            raise HTTPException(status_code=403, detail="你無法查看這段私訊。")
        return conversation

    @app.get("/", response_class=FileResponse)
    def frontend() -> FileResponse:
        return FileResponse(
            STATIC_DIR / "index.html",
            headers={"Cache-Control": "no-store"},
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

    @app.post(
        "/auth/student-verification",
        response_model=StudentVerificationResult,
        status_code=201,
    )
    async def verify_student_identity(
        front: UploadFile = File(...),
        back: UploadFile = File(...),
        school_name: str = Form(default="長庚大學"),
        consent: bool = Form(...),
    ) -> StudentVerificationResult:
        if not consent:
            raise HTTPException(status_code=422, detail="請先同意一次性學生證辨識說明。")
        university = resolve_university(school_name)
        if university is None:
            raise HTTPException(status_code=422, detail="目前無法驗證這所學校的學生證。")
        normalized_school = university.school_name
        allowed_types = {"image/jpeg", "image/png", "image/webp"}
        if front.content_type not in allowed_types or back.content_type not in allowed_types:
            raise HTTPException(status_code=415, detail="學生證照片只支援 JPG、PNG 或 WebP。")
        try:
            front_bytes = await front.read(MAX_STUDENT_CARD_BYTES + 1)
            back_bytes = await back.read(MAX_STUDENT_CARD_BYTES + 1)
        finally:
            await front.close()
            await back.close()
        if not front_bytes or not back_bytes:
            raise HTTPException(status_code=422, detail="請上傳學生證正面與反面。")
        if len(front_bytes) > MAX_STUDENT_CARD_BYTES or len(back_bytes) > MAX_STUDENT_CARD_BYTES:
            raise HTTPException(status_code=413, detail="每張學生證照片不可超過 8 MB。")
        try:
            verification = await run_in_threadpool(
                partial(
                    verify_student_cards,
                    front_bytes,
                    back_bytes,
                    expected_school=normalized_school,
                    school_signals=university.student_card_signals,
                )
            )
        except StudentCardVerificationError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc

        token = secrets.token_urlsafe(40)
        expires_at = utc_now() + STUDENT_VERIFICATION_TTL
        token_hash = hashlib.sha256(token.encode("utf-8")).hexdigest()
        with verification_lock:
            student_verification_sessions[token_hash] = {
                "school_name": verification.school_name,
                "checks": list(verification.checks),
                "expires_at": expires_at,
            }
        return StudentVerificationResult(
            verification_token=token,
            school_name=verification.school_name,
            checks=list(verification.checks),
            expires_at=expires_at,
        )

    @app.get("/auth/providers", response_model=list[AuthProviderStatus])
    def auth_providers() -> list[AuthProviderStatus]:
        return [
            AuthProviderStatus(provider=AuthProvider.EMAIL, enabled=True, label="使用 Email"),
            AuthProviderStatus(
                provider=AuthProvider.GOOGLE,
                enabled=provider_settings(AuthProvider.GOOGLE) is not None,
                label="使用 Google 繼續",
            ),
            AuthProviderStatus(
                provider=AuthProvider.FACEBOOK,
                enabled=provider_settings(AuthProvider.FACEBOOK) is not None,
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
        email = _normalize_email(payload.email)
        display_name = payload.display_name.strip()
        _reject_contact_details(display_name)
        with auth_lock:
            accounts = load_user_accounts(resolved_data_dir)
            if any(row.email == email for row in accounts):
                raise HTTPException(status_code=409, detail="這個 Email 已經註冊。")
            verification = student_verification_record(
                payload.student_verification_token,
                consume=True,
            )
            account = UserAccount(
                email=email,
                password_hash=_hash_password(payload.password),
                display_name=display_name,
                student_status_verified=True,
                verified_university=str(verification["school_name"]),
                student_verified_at=utc_now(),
                provider_links=[
                    AccountProviderLink(provider=AuthProvider.EMAIL, subject=email)
                ],
            )
            save_user_accounts([*accounts, account], resolved_data_dir)
            session = account_session(account)
        set_auth_cookie(response, session)
        return session

    @app.post("/auth/login", response_model=AccountSession)
    def login_account(payload: AccountLogin, response: Response) -> AccountSession:
        email = _normalize_email(payload.email)
        account = next(
            (row for row in load_user_accounts(resolved_data_dir) if row.email == email),
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
            with auth_lock:
                save_account_sessions(
                    [
                        row
                        for row in load_account_sessions(resolved_data_dir)
                        if not secrets.compare_digest(row.token_hash, token_hash)
                    ],
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
            updates["home_university"] = payload.home_university.strip()
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
        updated = account.model_copy(update=updates)
        with auth_lock:
            save_user_accounts(
                [
                    updated if row.id == account.id else row
                    for row in load_user_accounts(resolved_data_dir)
                ],
                resolved_data_dir,
            )
            if payload.display_name is not None:
                save_anonymous_identities(
                    [
                        row.model_copy(update={"display_name": updated.display_name})
                        if row.account_id == updated.id
                        else row
                        for row in load_anonymous_identities(resolved_data_dir)
                    ],
                    resolved_data_dir,
                )
        return _account_profile(updated)

    @app.get("/calendar-sync", response_model=CalendarSyncStatus)
    def get_calendar_sync(request: Request) -> CalendarSyncStatus:
        account, _ = authenticated_account(request)
        return calendar_status(account, request)

    @app.post("/calendar-sync/enable", response_model=CalendarSyncStatus)
    def enable_calendar_sync(request: Request) -> CalendarSyncStatus:
        account, _ = authenticated_account(request)
        if not account.calendar_feed_token:
            account = save_account_record(
                account.model_copy(
                    update={
                        "calendar_feed_token": secrets.token_urlsafe(32),
                        "updated_at": utc_now(),
                    }
                )
            )
        return calendar_status(account, request)

    @app.put("/calendar-sync/events", response_model=CalendarSyncStatus)
    def sync_calendar_events(
        payload: CalendarEventSyncRequest, request: Request
    ) -> CalendarSyncStatus:
        account, _ = authenticated_account(request)
        updated = account.model_copy(
            update={
                "calendar_feed_token": account.calendar_feed_token
                or secrets.token_urlsafe(32),
                "calendar_events": payload.events,
                "calendar_last_synced_at": utc_now(),
                "updated_at": utc_now(),
            }
        )
        save_account_record(updated)
        return calendar_status(updated, request)

    @app.delete("/calendar-sync", response_model=CalendarSyncStatus)
    def disable_calendar_sync(request: Request) -> CalendarSyncStatus:
        account, _ = authenticated_account(request)
        updated = account.model_copy(
            update={
                "calendar_feed_token": None,
                "calendar_events": [],
                "calendar_last_synced_at": None,
                "updated_at": utc_now(),
            }
        )
        save_account_record(updated)
        return CalendarSyncStatus(enabled=False)

    @app.get("/calendar/feed/{feed_token}.ics", response_class=PlainTextResponse)
    def calendar_subscription_feed(feed_token: str) -> PlainTextResponse:
        if len(feed_token) < 24 or len(feed_token) > 128:
            raise HTTPException(status_code=404, detail="找不到這個日曆。")
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
        return PlainTextResponse(
            _calendar_feed_content(account.calendar_events),
            media_type="text/calendar; charset=utf-8",
            headers={
                "Cache-Control": "private, max-age=300",
                "Content-Disposition": 'inline; filename="exchange-application-calendar.ics"',
            },
        )

    @app.get("/auth/me/export")
    def export_auth_profile(request: Request) -> dict[str, object]:
        account, _ = authenticated_account(request)
        return {
            "profile": _account_profile(account).model_dump(mode="json"),
            "community_identity_ids": [
                row.id
                for row in load_anonymous_identities(resolved_data_dir)
                if row.account_id == account.id
            ],
        }

    @app.delete("/auth/me", status_code=204)
    def delete_auth_profile(request: Request, response: Response) -> Response:
        account, _ = authenticated_account(request)
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
            save_anonymous_identities(
                [
                    row.model_copy(update={"account_id": None})
                    if row.account_id == account.id
                    else row
                    for row in load_anonymous_identities(resolved_data_dir)
                ],
                resolved_data_dir,
            )
        response.delete_cookie(AUTH_COOKIE_NAME, path="/")
        response.status_code = 204
        return response

    @app.post(
        "/auth/community-identity",
        response_model=AnonymousIdentitySession,
        status_code=201,
    )
    def account_community_identity(request: Request) -> AnonymousIdentitySession:
        account, _ = authenticated_account(request)
        access_token = secrets.token_urlsafe(32)
        token_hash = hashlib.sha256(access_token.encode("utf-8")).hexdigest()
        with community_lock:
            identities = load_anonymous_identities(resolved_data_dir)
            identity = next(
                (row for row in identities if row.account_id == account.id), None
            )
            if identity is None:
                identity = AnonymousIdentity(
                    display_name=account.display_name,
                    access_token_hash=token_hash,
                    account_id=account.id,
                )
                identities.append(identity)
            else:
                identity = identity.model_copy(
                    update={
                        "display_name": account.display_name,
                        "access_token_hash": token_hash,
                    }
                )
                identities = [
                    identity if row.id == identity.id else row for row in identities
                ]
            save_anonymous_identities(identities, resolved_data_dir)
        return AnonymousIdentitySession(
            id=identity.id,
            display_name=identity.display_name,
            access_token=access_token,
        )

    @app.get("/auth/oauth/{provider}/start", response_class=RedirectResponse)
    def oauth_start(
        provider: str,
        request: Request,
        student_verification_token: str | None = Query(default=None),
    ) -> RedirectResponse:
        try:
            provider_name = AuthProvider(provider)
        except ValueError as exc:
            raise HTTPException(status_code=404, detail="不支援這個登入方式。") from exc
        settings = provider_settings(provider_name)
        if settings is None:
            raise HTTPException(status_code=503, detail="此登入方式尚未設定平台金鑰。")
        if student_verification_token:
            student_verification_record(student_verification_token, consume=False)
        state_token = secrets.token_urlsafe(32)
        oauth_states[state_token] = (
            provider_name,
            utc_now(),
            student_verification_token,
        )
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
        return RedirectResponse(url=url, status_code=302)

    @app.get("/auth/oauth/{provider}/callback", response_class=RedirectResponse)
    def oauth_callback(
        provider: str,
        request: Request,
        code: str = Query(min_length=4),
        state: str = Query(min_length=8),
    ) -> RedirectResponse:
        try:
            provider_name = AuthProvider(provider)
        except ValueError as exc:
            raise HTTPException(status_code=404, detail="不支援這個登入方式。") from exc
        state_record = oauth_states.pop(state, None)
        if (
            state_record is None
            or state_record[0] != provider_name
            or utc_now() - state_record[1] > timedelta(minutes=10)
        ):
            raise HTTPException(status_code=400, detail="登入驗證已失效，請重新操作。")
        settings = provider_settings(provider_name)
        if settings is None:
            raise HTTPException(status_code=503, detail="此登入方式尚未設定平台金鑰。")
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
            else:
                raise HTTPException(status_code=501, detail="此登入方式尚未啟用。")
        except (KeyError, requests.RequestException) as exc:
            raise HTTPException(status_code=502, detail="社群登入暫時無法完成。") from exc
        account = oauth_account(
            provider_name,
            subject,
            email,
            display_name,
            avatar_url,
            state_record[2],
        )
        session = account_session(account)
        response = RedirectResponse(url="/#auth=success", status_code=303)
        set_auth_cookie(response, session)
        return response

    @app.get("/universities", response_model=list[SupportedUniversity])
    def universities() -> list[SupportedUniversity]:
        return [
            SupportedUniversity(
                id=university.id,
                school_name=university.school_name,
                short_name=university.short_name,
                english_name=university.english_name,
                hero_image=university.hero_image,
                official_url=university.official_url,
                partner_count=(
                    len(partners_for_university(university))
                    if university.id == CGU.id or university.id in partner_cache
                    else university.partner_count_hint
                ),
                coverage_note=university.coverage_note,
            )
            for university in SUPPORTED_UNIVERSITIES
        ]

    @app.get("/coverage", response_model=CoverageSummary)
    def coverage(
        school: str = Query(default="長庚大學"),
    ) -> CoverageSummary:
        university = university_for(school)
        partners = partners_for_university(university)
        experiences = load_student_experiences(resolved_data_dir)
        workflows = workflows_for_university(university)
        destination_profiles = load_destination_profiles(resolved_data_dir)
        audits = load_collection_audits(resolved_data_dir)
        research = load_partner_research(resolved_data_dir)
        school_images = _load_school_image_manifest()
        home_key = normalize_school(university.school_name)
        experience_map: dict[str, list] = {}
        for source in experiences:
            experience_map.setdefault(normalize_school(source.school_name), []).append(source)
        workflow_map = {
            normalize_school(workflow.school_name): workflow for workflow in workflows
        }
        destination_map = {
            normalize_school(profile.school_name): profile
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
        for partner in partners:
            normalized = normalize_school(partner.school_name)
            visual = school_images.get(school_identity_key(partner.school_name))
            partner_experiences = experience_map.get(normalized, [])
            workflow = workflow_map.get(normalized)
            destination = destination_map.get(normalized)
            experience_audit = experience_audit_map.get(normalized)
            destination_audit = destination_audit_map.get(normalized)
            website_research = research_map.get(normalized)
            experience_status = (
                experience_audit.status
                if experience_audit
                else (
                    "completed"
                    if university.id == CGU.id and partner_experiences
                    else "not_collected"
                )
            )
            visible_experiences = (
                partner_experiences
                if experience_audit or university.id == CGU.id
                else []
            )
            destination_status = (
                destination_audit.status
                if destination_audit
                else (
                    destination.coverage_status
                    if university.id == CGU.id and destination
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
                        website_research.verification_status
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
                        if university.id == CGU.id and destination
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
        school: str = Query(default="長庚大學"),
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
    def exchange_info(school: str = Query(default="長庚大學")) -> ExchangeInfo:
        return info_for_university(school)

    @app.get("/student-dashboard", response_model=StudentDashboard)
    def student_dashboard(
        request: Request,
        school: str = Query(default="長庚大學"),
    ) -> StudentDashboard:
        return _attach_school_images(
            dashboard_for_university(school),
            base_url=str(request.base_url),
        )

    @app.get("/ai/status")
    @app.get("/advisor/status")
    def advisor_status() -> dict[str, object]:
        enabled = ai_enabled()
        index = rag_index_status(resolved_data_dir)
        return {
            "ai_enabled": enabled,
            "provider": ai_provider_name(),
            "model": ai_model("fast") if enabled else None,
            "fast_model": ai_model("fast") if enabled else None,
            "advanced_model": ai_model("advanced") if enabled else None,
            "embedding_model": ai_embedding_model() if enabled else None,
            "source_grounded_fallback": True,
            "document_upload_persisted": False,
            "structured_source_count": len(load_structured_sources(resolved_data_dir)),
            "rag_index": index.model_dump(mode="json"),
            "supabase_pgvector_configured": supabase_configured(),
        }

    @app.post("/advisor/plan", response_model=AdvisorPlan)
    def advisor_plan(request: Request, payload: AdvisorProfile) -> AdvisorPlan:
        university = university_for(payload.school_name)
        pages = pages_for_university(university)
        dashboard = _attach_school_images(
            dashboard_for_university(university),
            base_url=str(request.base_url),
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
            load_destination_profiles(resolved_data_dir),
            retrieved_chunks=retrieved_chunks,
        )

    @app.post("/ai/chat", response_model=AdvisorAnswer)
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
            load_destination_profiles(resolved_data_dir),
            retrieved_chunks=retrieved_chunks,
        )

    @app.get(
        "/ai/structured-sources",
        response_model=list[StructuredSourceRecord],
    )
    def ai_structured_sources(
        limit: int = Query(default=100, ge=1, le=500),
    ) -> list[StructuredSourceRecord]:
        rows = load_structured_sources(resolved_data_dir)
        rows.sort(key=lambda row: row.last_checked, reverse=True)
        return rows[:limit]

    @app.get("/deadlines", response_model=list[DeadlineRecord])
    def deadlines(
        school: str = Query(default="長庚大學"),
    ) -> list[DeadlineRecord]:
        pages = pages_for_university(school)
        records: list[DeadlineRecord] = []
        triggers = FIELD_TRIGGERS["application_period"]
        for page in pages:
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

    @app.get("/documents", response_model=list[DocumentRecord])
    def documents(
        school: str = Query(default="長庚大學"),
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
    async def document_check(
        file: UploadFile = File(...),
        document_type: str = Form(default="auto"),
        expected_word_limit: int | None = Form(default=None, ge=1, le=20_000),
        require_signature: bool = Form(default=False),
        use_ai: bool = Form(default=False),
    ) -> DocumentCheckResult:
        content = await file.read(MAX_DOCUMENT_BYTES + 1)
        await file.close()
        try:
            return await run_in_threadpool(
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
        except ValueError as error:
            raise HTTPException(status_code=422, detail=str(error)) from error

    @app.post("/ai/rewrite-document", response_model=DocumentRewriteResult)
    def ai_rewrite_document(payload: DocumentRewriteRequest) -> DocumentRewriteResult:
        try:
            return rewrite_document(payload)
        except DocumentRewriteUnavailable as error:
            raise HTTPException(status_code=503, detail=str(error)) from error

    @app.get(
        "/application-center/templates",
        response_model=list[ApplicationDocumentTemplate],
    )
    def application_center_templates(
        school: str = Query(default="長庚大學"),
        program_type: str = Query(default="exchange"),
        flags: str = Query(default=""),
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
            )
        except ValueError as error:
            raise HTTPException(status_code=422, detail="不支援的申請計畫類型。") from error
        return templates_for_context(context)

    @app.post(
        "/application-center/manifest",
        response_model=ApplicationPacketManifest,
    )
    def application_center_manifest(
        payload: ApplicationPacketRequest,
    ) -> ApplicationPacketManifest:
        return build_packet_manifest(payload)

    @app.post("/application-center/pdf")
    async def application_center_pdf(payload: ApplicationPacketRequest) -> Response:
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
                "X-Content-Type-Options": "nosniff",
            },
        )

    @app.get("/student-experiences", response_model=StudentExperienceDigest)
    def student_experiences(
        school: str = Query(min_length=2),
        home_school: str | None = Query(default=None),
    ) -> StudentExperienceDigest:
        partner = partner_for_school(school, home_school)
        sources = load_student_experiences(resolved_data_dir)
        return build_experience_digest(partner.school_name, partner.country, sources)

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
        return build_experience_digest(partner.school_name, partner.country, all_sources)

    @app.get("/application-workflow", response_model=UniversityApplicationWorkflow)
    def application_workflow(
        school: str = Query(min_length=2),
        home_school: str | None = Query(default=None),
    ) -> UniversityApplicationWorkflow:
        university, partner = partner_context_for_school(school, home_school)
        normalized = normalize_school(partner.school_name)
        for workflow in workflows_for_university(university):
            if normalize_school(workflow.school_name) == normalized:
                return workflow
        return UniversityApplicationWorkflow(
            home_university=university.school_name,
            school_name=partner.school_name,
            partner_website=partner.website,
            country=partner.country,
            program_type=partner.program_type,
        )

    @app.get("/destination-profile", response_model=DestinationProfile)
    def destination_profile(
        school: str = Query(min_length=2),
        home_school: str | None = Query(default=None),
    ) -> DestinationProfile:
        partner = partner_for_school(school, home_school)
        normalized = normalize_school(partner.school_name)
        for profile in load_destination_profiles(resolved_data_dir):
            if normalize_school(profile.school_name) == normalized:
                return profile
        return DestinationProfile(
            school_name=partner.school_name,
            country=partner.country,
        )

    @app.get("/destination-profiles", response_model=list[DestinationProfile])
    def destination_profiles() -> list[DestinationProfile]:
        return load_destination_profiles(resolved_data_dir)

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

    @app.get("/community/posts", response_model=list[CommunityPostThread])
    def community_posts(
        school: str | None = Query(default=None, min_length=2),
        topic: CommunityTopic | None = Query(default=None),
        q: str | None = Query(default=None, max_length=80),
        limit: int = Query(default=60, ge=1, le=120),
    ) -> list[CommunityPostThread]:
        normalized_boards: set[str] = set()
        if school:
            if school in {PUBLIC_COMMUNITY_BOARD, LEGACY_PUBLIC_COMMUNITY_BOARD}:
                normalized_boards = {
                    normalize_school(PUBLIC_COMMUNITY_BOARD),
                    normalize_school(LEGACY_PUBLIC_COMMUNITY_BOARD),
                }
            elif (home_university := resolve_university(school)) is not None:
                normalized_boards = {normalize_school(home_university.school_name)}
            else:
                normalized_boards = {
                    normalize_school(partner_for_school(school).school_name)
                }
        normalized_query = _normalize_text(q) if q else ""
        comments = [
            row
            for row in load_community_post_comments(resolved_data_dir)
            if row.status == ModerationStatus.APPROVED
        ]
        comments_by_post: dict[str, list[CommunityPostComment]] = {}
        for comment in comments:
            comments_by_post.setdefault(comment.post_id, []).append(comment)
        posts = [
            row
            for row in load_community_posts(resolved_data_dir)
            if (
                not normalized_boards
                or normalize_school(row.school_name) in normalized_boards
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
        ]
        return [
            CommunityPostThread(
                post=post.model_copy(
                    update={"comment_count": len(comments_by_post.get(post.id, []))}
                ),
                comments=sorted(
                    comments_by_post.get(post.id, []), key=lambda row: row.created_at
                ),
            )
            for post in sorted(posts, key=lambda row: row.created_at, reverse=True)[:limit]
        ]

    @app.post("/community/posts", response_model=CommunityPost, status_code=201)
    def create_community_post(
        payload: CommunityPostCreate,
        identity_id: str | None = Header(default=None, alias="X-Anonymous-ID"),
        access_token: str | None = Header(default=None, alias="X-Anonymous-Token"),
    ) -> CommunityPost:
        identity = anonymous_identity(identity_id, access_token)
        if payload.school_name in {
            PUBLIC_COMMUNITY_BOARD,
            LEGACY_PUBLIC_COMMUNITY_BOARD,
        }:
            school_name = PUBLIC_COMMUNITY_BOARD
        elif (home_university := resolve_university(payload.school_name)) is not None:
            school_name = home_university.school_name
        else:
            school_name = partner_for_school(payload.school_name).school_name
        _reject_contact_details(payload.title, payload.body)
        post = CommunityPost(
            school_name=school_name,
            author_id=identity.id,
            display_name=identity.display_name,
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
        with community_lock:
            return append_community_post(post, resolved_data_dir)

    @app.post(
        "/community/posts/{post_id}/comments",
        response_model=CommunityPostComment,
        status_code=201,
    )
    def create_community_post_comment(
        post_id: str,
        payload: CommunityPostCommentCreate,
        identity_id: str | None = Header(default=None, alias="X-Anonymous-ID"),
        access_token: str | None = Header(default=None, alias="X-Anonymous-Token"),
    ) -> CommunityPostComment:
        identity = anonymous_identity(identity_id, access_token)
        if not any(row.id == post_id for row in load_community_posts(resolved_data_dir)):
            raise HTTPException(status_code=404, detail="找不到這篇貼文。")
        _reject_contact_details(payload.body)
        comment = CommunityPostComment(
            post_id=post_id,
            author_id=identity.id,
            display_name=identity.display_name,
            body=payload.body.strip(),
        )
        with community_lock:
            return append_community_post_comment(comment, resolved_data_dir)

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
                for row in load_private_conversations(resolved_data_dir)
                if identity.id in {row.sender_id, row.recipient_id}
                and not is_blocked(row.sender_id, row.recipient_id)
            ],
            key=lambda row: row.updated_at,
            reverse=True,
        )

    @app.post(
        "/community/conversations",
        response_model=PrivateConversation,
        status_code=201,
    )
    def create_private_conversation(
        payload: PrivateConversationCreate,
        identity_id: str | None = Header(default=None, alias="X-Anonymous-ID"),
        access_token: str | None = Header(default=None, alias="X-Anonymous-Token"),
    ) -> PrivateConversation:
        sender = anonymous_identity(identity_id, access_token)
        partner = partner_for_school(payload.school_name)
        recipient = next(
            (
                row
                for row in load_anonymous_identities(resolved_data_dir)
                if row.id == payload.recipient_id
            ),
            None,
        )
        if recipient is None or recipient.id == sender.id:
            raise HTTPException(status_code=422, detail="無法向這個匿名身分發送邀請。")
        if is_blocked(sender.id, recipient.id):
            raise HTTPException(status_code=403, detail="無法建立這段私訊。")
        _reject_contact_details(payload.initial_message)
        conversation = PrivateConversation(
            school_name=partner.school_name,
            sender_id=sender.id,
            sender_name=sender.display_name,
            recipient_id=recipient.id,
            recipient_name=recipient.display_name,
        )
        message = PrivateMessage(
            conversation_id=conversation.id,
            author_id=sender.id,
            display_name=sender.display_name,
            body=payload.initial_message.strip(),
        )
        with community_lock:
            append_private_conversation(conversation, resolved_data_dir)
            append_private_message(message, resolved_data_dir)
        return conversation

    @app.post(
        "/community/conversations/{conversation_id}/accept",
        response_model=PrivateConversation,
    )
    def accept_private_conversation(
        conversation_id: str,
        identity_id: str | None = Header(default=None, alias="X-Anonymous-ID"),
        access_token: str | None = Header(default=None, alias="X-Anonymous-Token"),
    ) -> PrivateConversation:
        identity = anonymous_identity(identity_id, access_token)
        conversation = private_conversation_for(identity.id, conversation_id)
        if conversation.recipient_id != identity.id:
            raise HTTPException(status_code=403, detail="只有收件者可以接受邀請。")
        updated = conversation.model_copy(
            update={"status": ConversationStatus.ACCEPTED, "updated_at": utc_now()}
        )
        with community_lock:
            rows = [
                updated if row.id == conversation.id else row
                for row in load_private_conversations(resolved_data_dir)
            ]
            save_private_conversations(rows, resolved_data_dir)
        return updated

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
                for row in load_private_messages(resolved_data_dir)
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
        identity_id: str | None = Header(default=None, alias="X-Anonymous-ID"),
        access_token: str | None = Header(default=None, alias="X-Anonymous-Token"),
    ) -> PrivateMessage:
        identity = anonymous_identity(identity_id, access_token)
        conversation = private_conversation_for(identity.id, conversation_id)
        if conversation.status != ConversationStatus.ACCEPTED:
            raise HTTPException(status_code=409, detail="對方接受邀請後才能繼續私訊。")
        if is_blocked(conversation.sender_id, conversation.recipient_id):
            raise HTTPException(status_code=403, detail="無法傳送訊息。")
        _reject_contact_details(payload.body)
        message = PrivateMessage(
            conversation_id=conversation.id,
            author_id=identity.id,
            display_name=identity.display_name,
            body=payload.body.strip(),
        )
        with community_lock:
            return append_private_message(message, resolved_data_dir)

    @app.post("/community/blocks", response_model=CommunityBlock, status_code=201)
    def block_community_identity(
        payload: CommunityBlockCreate,
        identity_id: str | None = Header(default=None, alias="X-Anonymous-ID"),
        access_token: str | None = Header(default=None, alias="X-Anonymous-Token"),
    ) -> CommunityBlock:
        identity = anonymous_identity(identity_id, access_token)
        if payload.target_id == identity.id:
            raise HTTPException(status_code=422, detail="無法封鎖自己。")
        existing = next(
            (
                row
                for row in load_community_blocks(resolved_data_dir)
                if row.owner_id == identity.id and row.target_id == payload.target_id
            ),
            None,
        )
        if existing:
            return existing
        block = CommunityBlock(owner_id=identity.id, target_id=payload.target_id)
        with community_lock:
            return append_community_block(block, resolved_data_dir)

    @app.post("/community/reports", response_model=CommunityReport, status_code=202)
    def report_community_content(
        payload: CommunityReportCreate,
        identity_id: str | None = Header(default=None, alias="X-Anonymous-ID"),
        access_token: str | None = Header(default=None, alias="X-Anonymous-Token"),
    ) -> CommunityReport:
        identity = anonymous_identity(identity_id, access_token)
        report = CommunityReport(
            reporter_id=identity.id,
            resource_type=payload.resource_type,
            resource_id=payload.resource_id,
            reason=payload.reason.strip(),
        )
        with community_lock:
            return append_community_report(report, resolved_data_dir)

    @app.post(
        "/experience-submissions",
        response_model=ExperienceSubmission,
        status_code=202,
    )
    def create_experience_submission(
        payload: ExperienceSubmissionCreate,
    ) -> ExperienceSubmission:
        partner = partner_for_school(payload.school_name)
        _reject_contact_details(payload.title, payload.summary, payload.display_name)
        if payload.source_url and not re.match(r"^https?://", payload.source_url, re.IGNORECASE):
            raise HTTPException(status_code=422, detail="Source URL must use http or https.")
        submission = ExperienceSubmission(
            school_name=partner.school_name,
            home_university=payload.home_university.strip(),
            title=payload.title.strip(),
            summary=payload.summary.strip(),
            exchange_year=payload.exchange_year.strip(),
            themes=list(dict.fromkeys(theme.strip() for theme in payload.themes if theme.strip())),
            source_url=payload.source_url.strip() if payload.source_url else None,
            display_name=payload.display_name.strip(),
        )
        with community_lock:
            return append_experience_submission(submission, resolved_data_dir)

    @app.get("/search", response_model=list[SearchResult])
    def search(
        q: str = Query(min_length=1),
        school: str = Query(default="長庚大學"),
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
    text = " ".join(values)
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
