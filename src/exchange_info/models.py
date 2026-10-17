from __future__ import annotations

from datetime import date as PlanningDate

import ipaddress
from datetime import date, datetime, timezone
from enum import Enum
from typing import Any, Literal
from urllib.parse import urlsplit
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator, model_serializer

from .source_url_policy import canonical_source_url_identity
from .university_locations import UniversityLocation
from .discovery import DiscoveryWorkspace


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class PageCategory(str, Enum):
    EXCHANGE_APPLICATION = "exchange_application"
    SCHOLARSHIP = "scholarship"
    PARTNER_SCHOOL = "partner_school"
    EXPERIENCE_REPORT = "experience_report"
    FAQ = "faq"
    INFO_SESSION = "info_session"
    DEADLINE = "deadline"
    OTHER = "other"


class Attachment(BaseModel):
    url: str
    filename: str | None = None
    local_path: str | None = None
    content_type: str | None = None


class RawPage(BaseModel):
    title: str
    source_url: str
    published_at: str | None = None
    raw_text: str
    attachments: list[Attachment] = Field(default_factory=list)
    crawled_at: datetime = Field(default_factory=utc_now)
    content_hash: str


class ProcessedPage(BaseModel):
    title: str
    source_url: str
    published_at: str | None = None
    text: str
    summary: str
    category: PageCategory
    attachments: list[Attachment] = Field(default_factory=list)
    crawled_at: datetime = Field(default_factory=utc_now)
    content_hash: str


class DocumentChunk(BaseModel):
    id: str
    school_name: str = "長庚大學"
    source_url: str
    source_title: str
    section: str
    text: str
    published_at: str | None = None
    last_checked: datetime
    category: PageCategory
    content_hash: str
    embedding: list[float] | None = None
    embedding_model: str | None = None


class RagSearchHit(BaseModel):
    chunk: DocumentChunk
    score: float = Field(ge=0, le=1)
    match_type: Literal["hybrid", "semantic", "keyword"]


class RagIndexStatus(BaseModel):
    store: Literal["local_jsonl", "supabase_pgvector"] = "local_jsonl"
    chunk_count: int = Field(default=0, ge=0)
    embedded_count: int = Field(default=0, ge=0)
    source_count: int = Field(default=0, ge=0)
    built_at: datetime | None = None
    embedding_model: str | None = None
    provider: str | None = None


class StructuredSourceRecord(BaseModel):
    source_url: str
    title: str
    school_name: str = "長庚大學"
    category: PageCategory
    published_at: str | None = None
    last_checked: datetime
    content_hash: str
    program_type: list[str] = Field(default_factory=list)
    academic_year: list[str] = Field(default_factory=list)
    semester: list[str] = Field(default_factory=list)
    application_start: str | None = None
    application_end: str | None = None
    application_period: list[str] = Field(default_factory=list)
    eligibility: list[str] = Field(default_factory=list)
    language_requirements: list[str] = Field(default_factory=list)
    required_documents: list[str] = Field(default_factory=list)
    scholarship_info: list[str] = Field(default_factory=list)
    extraction_method: Literal["rules", "ai"] = "rules"
    needs_review: bool = True


class ExchangeInfo(BaseModel):
    school_name: str = "長庚大學"
    program_type: list[str] = Field(default_factory=list)
    academic_year: list[str] = Field(default_factory=list)
    semester: list[str] = Field(default_factory=list)
    application_period: list[str] = Field(default_factory=list)
    eligibility: list[str] = Field(default_factory=list)
    language_requirement: list[str] = Field(default_factory=list)
    required_documents: list[str] = Field(default_factory=list)
    scholarship_info: list[str] = Field(default_factory=list)
    partner_universities: list[str] = Field(default_factory=list)
    source_urls: list[str] = Field(default_factory=list)
    last_checked: datetime | None = None


class SourceSummary(BaseModel):
    title: str
    source_url: str
    published_at: str | None = None
    category: PageCategory
    summary: str
    attachments: list[Attachment] = Field(default_factory=list)
    crawled_at: datetime
    content_hash: str


class DeadlineRecord(BaseModel):
    title: str
    source_url: str
    published_at: str | None = None
    category: PageCategory
    snippets: list[str] = Field(default_factory=list)


class DocumentRecord(BaseModel):
    title: str
    source_url: str
    attachment: Attachment | None = None
    summary: str | None = None
    key_points: list[str] = Field(default_factory=list)
    applies_to: list[str] = Field(default_factory=list)
    document_url: str | None = None
    document_type: str | None = None


class ApplicationFieldType(str, Enum):
    TEXT = "text"
    EMAIL = "email"
    TEL = "tel"
    DATE = "date"
    NUMBER = "number"
    TEXTAREA = "textarea"
    SELECT = "select"
    CHECKBOX = "checkbox"
    FILES = "files"


class ApplicationFieldGuidance(BaseModel):
    """Plain-language help shown beside a form field so students know what to write."""

    summary: str = Field(max_length=300)
    tips: list[str] = Field(default_factory=list, max_length=6)
    outline: list[str] = Field(default_factory=list, max_length=6)
    example: str | None = Field(default=None, max_length=400)
    format_note: str | None = Field(default=None, max_length=200)
    # System writing advice only; a school's own limit lives in ApplicationWritingRules.
    recommended_min_chars: int | None = Field(default=None, ge=1, le=12000)
    recommended_max_chars: int | None = Field(default=None, ge=1, le=12000)


class ApplicationWritingRules(BaseModel):
    """School-published length and format rules for one document, with an optional total counter."""

    rules: list[str] = Field(min_length=1, max_length=8)
    min_chars: int | None = Field(default=None, ge=1, le=100000)
    max_chars: int | None = Field(default=None, ge=1, le=100000)
    count_field_ids: list[str] = Field(default_factory=list, max_length=12)
    # Set when the school's count covers more than the fields this form can total.
    count_note: str | None = Field(default=None, max_length=200)
    # The official document the rules were checked against.
    evidence: str | None = Field(default=None, max_length=200)
    # False means no published rule has been checked for this school yet.
    verified: bool = True


class ApplicationFormField(BaseModel):
    id: str = Field(pattern=r"^[a-z][a-z0-9_]*$")
    label: str
    field_type: ApplicationFieldType = ApplicationFieldType.TEXT
    required: bool = False
    # OR between clauses; AND between the field/value tests in each clause.
    required_when: list[dict[str, list[str]]] = Field(default_factory=list)
    options_by_field: dict[str, dict[str, list[str]]] = Field(default_factory=dict)
    reusable_profile_key: str | None = None
    placeholder: str | None = None
    help_text: str | None = None
    options: list[str] = Field(default_factory=list)
    sensitive: bool = False
    max_length: int | None = Field(default=None, ge=1, le=12000)
    min_files: int = Field(default=0, ge=0, le=12)
    max_files: int = Field(default=6, ge=1, le=12)
    guidance: ApplicationFieldGuidance | None = None


class ApplicationDocumentTemplate(BaseModel):
    id: str = Field(pattern=r"^[a-z0-9][a-z0-9-]*$")
    title: str
    short_title: str
    category: str
    stage: str
    description: str
    fields: list[ApplicationFormField] = Field(default_factory=list)
    default_copies: int = Field(default=1, ge=1, le=10)
    destinations: list[str] = Field(default_factory=list)
    signatures: list[str] = Field(default_factory=list)
    stamps: list[str] = Field(default_factory=list)
    program_types: list[str] = Field(default_factory=list)
    condition_flags: list[str] = Field(default_factory=list)
    conditional_note: str | None = None
    official_layout: bool = False
    official_form_number: str | None = None
    official_file_name: str | None = None
    official_download_url: str | None = None
    paper_size: str = Field(default="A4", min_length=1, max_length=20)
    print_sides: Literal["single_sided", "double_sided", "confirm_official"] = (
        "confirm_official"
    )
    print_note: str | None = Field(default=None, max_length=500)
    attachment_field_order: list[str] = Field(default_factory=list, max_length=20)
    writing_rules: ApplicationWritingRules | None = None
    source_url: str
    source_checked_at: datetime
    version: str


class PartnerDocumentPreparationState(BaseModel):
    model_config = ConfigDict(extra="forbid")

    host_admission_status: Literal["unknown", "not_accepted", "accepted"] = "unknown"
    housing_choice: Literal["unknown", "on_campus", "off_campus"] = "unknown"


class DocumentApplicability(BaseModel):
    requirement_name: str
    status: Literal["applicable", "not_applicable", "deferred", "needs_confirmation"]
    note: str
    source_urls: list[str] = Field(default_factory=list)
    # Matching a personal condition never approves a source's academic year.
    current_applicability_verified: bool = False


class ApplicationCenterContext(BaseModel):
    school_name: str = "長庚大學"
    target_school: str | None = Field(default=None, max_length=200)
    target_country: str | None = Field(default=None, max_length=80)
    program_type: Literal["exchange", "dual_degree", "internship", "short_term_credit"] = "exchange"
    college: str | None = Field(default=None, max_length=120)
    department: str | None = Field(default=None, max_length=120)
    degree_level: str | None = Field(default=None, max_length=80)
    academic_year: str | None = Field(default=None, max_length=20)
    application_round: str | None = Field(default=None, max_length=80)
    semester: str | None = Field(default=None, max_length=30)
    flags: list[str] = Field(default_factory=list, max_length=20)
    partner_document_states: dict[str, PartnerDocumentPreparationState] = Field(default_factory=dict, max_length=214)


ApplicationDraftScalar = str | bool | int | float | None


class ApplicationFormDraftAttachment(BaseModel):
    model_config = ConfigDict(extra="forbid")

    document_id: str = Field(min_length=8, max_length=80)
    version_id: str = Field(min_length=8, max_length=80)
    label: str = Field(min_length=2, max_length=100)
    file_name: str = Field(min_length=1, max_length=255)
    category: str = Field(min_length=2, max_length=40)
    purpose: str = Field(min_length=2, max_length=80)
    retention_days: int = Field(ge=1, le=365)
    expires_at: datetime


class ApplicationFormDraftSave(BaseModel):
    model_config = ConfigDict(extra="forbid")

    home_school: str = Field(min_length=2, max_length=80)
    template_version: str = Field(min_length=1, max_length=80)
    revision: int = Field(default=0, ge=0)
    profile: dict[str, ApplicationDraftScalar] = Field(default_factory=dict, max_length=80)
    answers: dict[str, ApplicationDraftScalar] = Field(default_factory=dict, max_length=120)
    attachments: dict[str, list[ApplicationFormDraftAttachment]] = Field(
        default_factory=dict,
        max_length=30,
    )


class ApplicationFormDraft(BaseModel):
    model_config = ConfigDict(extra="forbid")

    home_school: str
    template_id: str
    template_version: str
    revision: int = Field(ge=1)
    profile: dict[str, ApplicationDraftScalar] = Field(default_factory=dict)
    answers: dict[str, ApplicationDraftScalar] = Field(default_factory=dict)
    attachments: dict[str, list[ApplicationFormDraftAttachment]] = Field(default_factory=dict)
    updated_at: datetime


class ApplicationFormDraftList(BaseModel):
    items: list[ApplicationFormDraft] = Field(default_factory=list)


class ApplicationFormDraftRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")

    account_id: str = Field(min_length=1, max_length=80)
    home_school_key: str = Field(min_length=1, max_length=160)
    home_school: str = Field(min_length=2, max_length=80)
    template_id: str = Field(pattern=r"^[a-z0-9][a-z0-9-]*$")
    template_version: str = Field(min_length=1, max_length=80)
    revision: int = Field(ge=1)
    ciphertext: str = Field(min_length=1)
    nonce: str = Field(min_length=1, max_length=80)
    plaintext_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    updated_at: datetime = Field(default_factory=utc_now)


class ApplicationDocumentSelection(BaseModel):
    template_id: str
    copies: int = Field(default=1, ge=1, le=10)
    reviewed_version: str | None = Field(default=None, max_length=80)
    reviewed_content_sha256: str | None = Field(
        default=None,
        pattern=r"^[0-9a-f]{64}$",
    )
    reviewed_at: datetime | None = None


class ApplicationPacketRequest(BaseModel):
    context: ApplicationCenterContext
    profile: dict[str, Any] = Field(default_factory=dict)
    answers: dict[str, dict[str, Any]] = Field(default_factory=dict)
    selections: list[ApplicationDocumentSelection] = Field(default_factory=list, max_length=30)


class ApplicationFieldPreviewItem(BaseModel):
    field_id: str
    label: str
    field_type: ApplicationFieldType
    required: bool = False
    sensitive: bool = False
    display_value: str = ""
    is_blank: bool = True
    validation_error: str | None = None


class ApplicationPacketAttachmentItem(BaseModel):
    order: int = Field(ge=1)
    field_id: str
    field_label: str
    file_name: str
    media_type: Literal["application/pdf", "image/jpeg", "image/png"]
    page_count: int | None = Field(default=None, ge=1)
    placement: Literal["after_document", "inside_document"]


class ApplicationPacketManifestItem(BaseModel):
    template_id: str
    title: str
    copies: int
    template_version: str
    review_content_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    reviewed: bool = False
    preview_fields: list[ApplicationFieldPreviewItem] = Field(default_factory=list)
    destinations: list[str] = Field(default_factory=list)
    signatures: list[str] = Field(default_factory=list)
    stamps: list[str] = Field(default_factory=list)
    paper_size: str = "A4"
    print_sides: Literal["single_sided", "double_sided", "confirm_official"] = (
        "confirm_official"
    )
    print_note: str | None = None
    attachment_order: list[str] = Field(default_factory=list)
    attachments: list[ApplicationPacketAttachmentItem] = Field(default_factory=list)
    invalid_attachment_fields: list[str] = Field(default_factory=list)
    source_url: str
    official_layout: bool = False
    missing_required_fields: list[str] = Field(default_factory=list)


class ApplicationPacketManifest(BaseModel):
    school_name: str
    target_school: str | None = None
    items: list[ApplicationPacketManifestItem] = Field(default_factory=list)
    total_printed_copies: int = 0
    ready_to_generate: bool = False
    source_checked_at: datetime


class SearchResult(BaseModel):
    title: str
    source_url: str
    category: PageCategory
    snippet: str
    published_at: str | None = None
    attachments: list[Attachment] = Field(default_factory=list)


class SupportedUniversity(BaseModel):
    id: str
    school_name: str
    short_name: str
    english_name: str | None = None
    aliases: list[str] = Field(default_factory=list)
    hero_image: str | None = None
    official_url: str | None = None
    supported: bool = True
    support_level: Literal["full", "basic", "pending"] = "pending"
    partner_count: int = 0
    coverage_note: str
    location: UniversityLocation | None = None
    colleges: list[str] = Field(default_factory=list)


class PartnerCoverage(BaseModel):
    school_name: str
    image_status: str = "not_collected"
    image_last_checked: datetime | None = None
    official_website_status: str = "not_collected"
    official_website_url: str | None = None
    official_website_last_checked: datetime | None = None
    experience_source_count: int = 0
    experience_status: str = "not_collected"
    experience_last_checked: datetime | None = None
    workflow_status: str = "not_collected"
    workflow_last_checked: datetime | None = None
    destination_status: str = "not_collected"
    destination_last_checked: datetime | None = None


class CoverageSummary(BaseModel):
    total_partner_schools: int = 0
    image_count: int = 0
    official_website_count: int = 0
    experience_school_count: int = 0
    experience_checked_count: int = 0
    workflow_school_count: int = 0
    destination_profile_count: int = 0
    experience_source_count: int = 0
    partners: list[PartnerCoverage] = Field(default_factory=list)


class CollectionAudit(BaseModel):
    school_name: str
    collector: str
    status: str
    home_university: str | None = None
    result_count: int = 0
    note: str | None = None
    checked_at: datetime = Field(default_factory=utc_now)


class SourceReference(BaseModel):
    title: str
    source_url: str
    category: PageCategory | None = None
    summary: str | None = None


class StudentInfoItem(BaseModel):
    title: str
    details: list[str] = Field(default_factory=list)
    source: SourceReference | None = None


class ApplicationPeriodStatus(str, Enum):
    UPCOMING = "upcoming"
    OPEN = "open"
    CLOSED = "closed"
    ACTION_REQUIRED = "action_required"
    REFERENCE_ONLY = "reference_only"
    NEEDS_CONFIRMATION = "needs_confirmation"


class ApplicationPeriodDateStatus(str, Enum):
    VERIFIED_EXACT = "verified_exact"
    REFERENCE_ONLY = "reference_only"
    NEEDS_CONFIRMATION = "needs_confirmation"
    NOT_APPLICABLE = "not_applicable"


class ApplicationPeriodAudience(str, Enum):
    ALL_STUDENTS = "all_students"
    APPLICANTS = "applicants"
    SELECTED_APPLICANTS = "selected_applicants"
    CONDITIONAL_APPLICANTS = "conditional_applicants"


class ApplicationPeriodItem(StudentInfoItem):
    scope: Literal[
        "home_application",
        "post_selection",
        "recurring_reference",
        "short_course",
    ]
    program_types: list[
        Literal["exchange", "dual_degree", "internship", "short_term_credit"]
    ] = Field(default_factory=list)
    academic_year: str | None = Field(default=None, max_length=20)
    application_round: str | None = Field(default=None, max_length=80)
    audience: ApplicationPeriodAudience = ApplicationPeriodAudience.ALL_STUDENTS
    opens_at: datetime | None = None
    deadline_at: datetime | None = None
    date_status: ApplicationPeriodDateStatus
    status: ApplicationPeriodStatus
    status_note: str = Field(min_length=1, max_length=500)
    deadline_note: str | None = Field(default=None, max_length=500)
    reminder_eligible: bool = False
    checked_at: datetime | None = None

    @model_validator(mode="after")
    def validate_deadline_provenance(self) -> ApplicationPeriodItem:
        for field_name, value in (
            ("opens_at", self.opens_at),
            ("deadline_at", self.deadline_at),
            ("checked_at", self.checked_at),
        ):
            if value is not None and value.utcoffset() is None:
                raise ValueError(f"{field_name} must include a timezone")
        if self.date_status == ApplicationPeriodDateStatus.VERIFIED_EXACT:
            if self.deadline_at is None or self.source is None or self.checked_at is None:
                raise ValueError(
                    "verified_exact application periods require deadline_at, source, and checked_at"
                )
        if self.reminder_eligible:
            if self.date_status != ApplicationPeriodDateStatus.VERIFIED_EXACT:
                raise ValueError("reminders require a verified_exact application period")
            if self.status not in {
                ApplicationPeriodStatus.UPCOMING,
                ApplicationPeriodStatus.OPEN,
                ApplicationPeriodStatus.ACTION_REQUIRED,
            }:
                raise ValueError("reminders require an active or upcoming application period")
        if self.status in {
            ApplicationPeriodStatus.CLOSED,
            ApplicationPeriodStatus.REFERENCE_ONLY,
            ApplicationPeriodStatus.NEEDS_CONFIRMATION,
        } and self.reminder_eligible:
            raise ValueError("closed or unverified application periods cannot create reminders")
        return self


class RuleExplanation(BaseModel):
    title: str
    summary: str
    key_points: list[str] = Field(default_factory=list)
    applies_to: list[str] = Field(default_factory=list)
    source: SourceReference
    document_url: str | None = None
    document_type: str = "official_document"
    full_text_extracted: bool = False


class PartnerStudentSummary(BaseModel):
    study_period: str | None = None
    application_deadline: str | None = None
    eligibility_points: list[str] = Field(default_factory=list)
    application_steps: list[str] = Field(default_factory=list)
    tuition_points: list[str] = Field(default_factory=list)
    translated_from_english: bool = False


class PartnerProgramOption(BaseModel):
    program_type: str
    colleges: str | None = None
    degree_levels: str | None = None
    study_period: str | None = None
    quota: str | None = None
    eligibility: str | None = None
    application_deadline: str | None = None
    application_info: str | None = None
    tuition_info: str | None = None
    source_url: str
    student_summary_zh: PartnerStudentSummary = Field(default_factory=PartnerStudentSummary)


class ExchangeFieldEvidence(BaseModel):
    source_url: str
    source_pages: list[int] = Field(default_factory=list)
    academic_year: str | None = None
    application_round: str | None = None
    checked_at: datetime
    status: Literal["verified_current", "reference_only", "missing", "needs_confirmation", "conflict", "explicit_not_announced"]
    excerpt: str | None = None
    reference_excerpt: str | None = None
    note: str | None = None


class PartnerLanguageCondition(BaseModel):
    """A reviewed condition, separate from unparsed source text or CEFR ranges."""

    test: str
    test_variant: str | None = None
    minimum_score: float | None = None
    requirement_level: Literal["required", "recommended", "no_score_minimum", "needs_confirmation", "conflict"]
    degree_levels: list[str] = Field(default_factory=list)
    track: str | None = None
    host_faculties: list[str] = Field(default_factory=list)
    teaching_language: str | None = None
    scope_choice_required: bool = False
    additional_conditions: list[str] = Field(default_factory=list)
    evidence: ExchangeFieldEvidence


class ExchangeSourceCheck(BaseModel):
    source_id: str
    source_url: str
    checked_at: datetime
    result: str
    timestamp_precision: Literal["date", "datetime"] = "datetime"


class PartnerExchangeDetailField(BaseModel):
    """Receiving-school facts retain their own year, scope and source evidence."""

    value: str | None = None
    status: Literal["verified_current", "reference_only", "missing", "needs_confirmation", "conflict", "explicit_not_announced"]
    reason: str
    evidence: list[ExchangeFieldEvidence] = Field(default_factory=list)
    research_category: Literal[
        "verified_supported", "official_not_announced",
        "unresolved_source_conflict",
        "login_or_school_confirmation", "source_technical_failure",
        "alternative_official_sources_not_fully_checked",
    ] | None = None
    research_note: str | None = None
    source_checks: list[ExchangeSourceCheck] = Field(default_factory=list)


class PartnerUniversity(BaseModel):
    program_type: str
    availability_status: Literal[
        "open", "agreement_only", "departmental_reference", "not_open", "needs_confirmation", "zero_quota", "fee_paying", "closed", "reference_only", "quota_unconfirmed"
    ] = "open"
    availability_note: str | None = None
    agreement_type: str | None = None
    agreement_level: str | None = None
    country: str | None = None
    school_name: str
    academic_year: str | None = None
    application_round: str | None = None
    checked_at: datetime | None = None
    source_pages: list[int] = Field(default_factory=list)
    quota_status: Literal["published", "zero", "not_published", "reference_only", "fee_paying"] | None = None
    application_window_status: Literal["open", "closed", "needs_confirmation"] | None = None
    field_evidence: dict[str, ExchangeFieldEvidence] = Field(default_factory=dict)
    reference_data: dict[str, str] = Field(default_factory=dict)
    language_requirement: str | None = None
    language_conditions: list[PartnerLanguageCondition] = Field(default_factory=list)
    language_review_note: str | None = None
    partner_application_prerequisite: str | None = None
    partner_exchange_details: dict[str, PartnerExchangeDetailField] = Field(default_factory=dict)
    partner_application_deadline: str | None = None
    nomination_deadline: str | None = None
    semester_dates: str | None = None
    housing_info: str | None = None
    course_restrictions: str | None = None
    location: UniversityLocation | None = None
    website: str | None = None
    colleges: str | None = None
    degree_levels: str | None = None
    study_period: str | None = None
    quota: str | None = None
    eligibility: str | None = None
    application_deadline: str | None = None
    application_info: str | None = None
    tuition_info: str | None = None
    ranking_info: str | None = None
    ranking_source_url: str | None = None
    source_url: str
    image_url: str | None = None
    image_source_url: str | None = None
    image_page_url: str | None = None
    image_status: str = "missing"
    program_options: list[PartnerProgramOption] = Field(default_factory=list)
    student_summary_zh: PartnerStudentSummary = Field(default_factory=PartnerStudentSummary)

    @model_serializer(mode="wrap")
    def serialize_source_details(self, handler):
        payload = handler(self)
        # Older school bundles have no structured source evidence. Keep their
        # tracked serialization stable while allowing populated optional fields.
        optional_source_fields = (
            "academic_year", "application_round", "checked_at", "source_pages",
            "quota_status", "application_window_status", "field_evidence",
            "reference_data", "language_requirement", "language_conditions",
            "language_review_note", "partner_application_prerequisite",
            "partner_exchange_details", "partner_application_deadline",
            "nomination_deadline", "semester_dates", "housing_info",
            "course_restrictions",
        )
        if not self.field_evidence and not self.source_pages:
            for key in optional_source_fields:
                if payload.get(key) in (None, [], {}):
                    payload.pop(key, None)
        return payload


class SchoolCompletenessItem(BaseModel):
    key: str
    label: str
    status: Literal["available", "partial", "needs_confirmation", "missing"]
    note: str
    source_urls: list[str] = Field(default_factory=list)


class SchoolDataCompleteness(BaseModel):
    """What the platform has and lacks for one partner school; never fills a gap."""

    school_name: str
    country: str | None = None
    home_university: str | None = None
    items: list[SchoolCompletenessItem] = Field(default_factory=list)
    available_count: int = Field(default=0, ge=0)
    total_count: int = Field(default=0, ge=0)
    score: float = Field(default=0, ge=0, le=1)
    priority_gaps: list[str] = Field(default_factory=list)
    disclaimer: str


class StudentGuidePhoto(BaseModel):
    image_url: str
    source_url: str
    alt: str
    caption: str
    category: Literal["campus", "housing", "neighborhood", "classroom"] = "housing"


class StudentGuideSection(BaseModel):
    key: str
    title: str
    summary: str
    points: list[str] = Field(default_factory=list)
    source_urls: list[str] = Field(default_factory=list)
    evidence_type: Literal["official", "student_experience", "mixed", "practical_inference"] = "official"
    caution: str | None = None


class StudentGuideChecklistItem(BaseModel):
    title: str
    detail: str
    source_urls: list[str] = Field(default_factory=list)
    timing: str | None = None
    evidence_type: Literal["official", "student_experience", "mixed", "practical_inference"] = "official"


class DestinationProfile(BaseModel):
    home_university: str | None = None
    school_name: str
    country: str | None = None
    city: str | None = None
    cost_summary: str | None = None
    housing_summary: str | None = None
    transport_summary: str | None = None
    campus_life_summary: str | None = None
    guide_photos: list[StudentGuidePhoto] = Field(default_factory=list)
    student_guide_sections: list[StudentGuideSection] = Field(default_factory=list)
    first_72_hours: list[StudentGuideChecklistItem] = Field(default_factory=list)
    packing_from_taiwan: list[StudentGuideChecklistItem] = Field(default_factory=list)
    buy_after_arrival: list[StudentGuideChecklistItem] = Field(default_factory=list)
    sources: list[SourceReference] = Field(default_factory=list)
    last_checked: datetime | None = None
    coverage_status: str = "not_collected"
    coverage_note: str = "尚未完成官方生活資訊查核。"


class DestinationProfileReviewDecision(str, Enum):
    APPROVE = "approve"
    CHANGES_REQUIRED = "changes_required"


class DestinationProfileReviewSection(BaseModel):
    key: str = Field(min_length=1, max_length=100)
    label: str = Field(min_length=1, max_length=100)
    description: str = Field(min_length=1, max_length=300)


class DestinationProfileReviewEvent(BaseModel):
    """Append-only evidence produced by one authenticated content reviewer."""

    id: str = Field(default_factory=lambda: str(uuid4()))
    home_university: str = Field(min_length=1, max_length=200)
    school_name: str = Field(min_length=1, max_length=300)
    profile_content_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    snapshot_fingerprint: str = Field(pattern=r"^[0-9a-f]{64}$")
    reviewer_id: str = Field(min_length=1, max_length=200)
    reviewer_display_name: str = Field(min_length=1, max_length=200)
    decision: DestinationProfileReviewDecision
    note: str = Field(min_length=10, max_length=2000)
    reviewed_source_urls: list[str] = Field(default_factory=list, max_length=50)
    reviewed_section_keys: list[str] = Field(min_length=1, max_length=30)
    reviewed_at: datetime = Field(default_factory=utc_now)
    supersedes_event_id: str | None = None

    @model_validator(mode="after")
    def validate_review_evidence(self) -> "DestinationProfileReviewEvent":
        source_urls = [value.strip() for value in self.reviewed_source_urls]
        if (
            self.decision == DestinationProfileReviewDecision.APPROVE
            and any(not value.casefold().startswith("https://") for value in source_urls)
        ):
            raise ValueError("生活情報審查證據中的官方來源必須全部使用 HTTPS。")
        source_keys = [value.casefold() for value in source_urls]
        if len(source_keys) != len(set(source_keys)):
            raise ValueError("生活情報審查證據中的官方來源不可重複。")
        section_keys = [value.strip() for value in self.reviewed_section_keys]
        if any(not value for value in section_keys):
            raise ValueError("生活情報審查項目不可為空白。")
        if len(section_keys) != len(set(section_keys)):
            raise ValueError("生活情報審查項目不可重複。")
        if self.reviewed_at.tzinfo is None:
            raise ValueError("生活情報審查時間必須包含時區。")
        self.home_university = self.home_university.strip()
        self.school_name = self.school_name.strip()
        self.reviewer_id = self.reviewer_id.strip()
        self.reviewer_display_name = self.reviewer_display_name.strip()
        self.note = self.note.strip()
        if len(self.note) < 10:
            raise ValueError("生活情報審查說明至少需要 10 個字。")
        self.reviewed_source_urls = source_urls
        self.reviewed_section_keys = section_keys
        return self


class DestinationProfileReviewSubmitRequest(BaseModel):
    home_university: str = Field(min_length=1, max_length=200)
    school_name: str = Field(min_length=1, max_length=300)
    expected_snapshot: str = Field(pattern=r"^[0-9a-f]{64}$")
    expected_profile_content_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    decision: DestinationProfileReviewDecision
    note: str = Field(min_length=10, max_length=2000)
    reviewed_source_urls: list[str] = Field(default_factory=list, max_length=50)
    reviewed_section_keys: list[str] = Field(min_length=1, max_length=30)


class DestinationProfilePromotionRequest(BaseModel):
    home_university: str = Field(min_length=1, max_length=200)
    school_name: str = Field(min_length=1, max_length=300)
    expected_snapshot: str = Field(pattern=r"^[0-9a-f]{64}$")
    expected_profile_content_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    note: str = Field(min_length=10, max_length=2000)


class DestinationProfilePromotionEvent(BaseModel):
    """Append-only publication evidence for one independently reviewed profile."""

    id: str = Field(default_factory=lambda: str(uuid4()))
    home_university: str = Field(min_length=1, max_length=200)
    school_name: str = Field(min_length=1, max_length=300)
    source_profile_content_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    promoted_profile_content_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    snapshot_fingerprint: str = Field(pattern=r"^[0-9a-f]{64}$")
    review_event_ids: list[str] = Field(min_length=2, max_length=10)
    reviewer_ids: list[str] = Field(min_length=2, max_length=10)
    promoted_by_id: str = Field(min_length=1, max_length=200)
    promoted_by_display_name: str = Field(min_length=1, max_length=200)
    note: str = Field(min_length=10, max_length=2000)
    promoted_at: datetime = Field(default_factory=utc_now)
    promoted_profile: DestinationProfile

    @model_validator(mode="after")
    def validate_promotion_evidence(self) -> "DestinationProfilePromotionEvent":
        event_ids = [value.strip() for value in self.review_event_ids]
        reviewer_ids = [value.strip() for value in self.reviewer_ids]
        if len(event_ids) != len(set(event_ids)):
            raise ValueError("生活情報升級所依據的審查事件不可重複。")
        if len({value.casefold() for value in reviewer_ids}) < 2:
            raise ValueError("生活情報升級必須由兩位不同審查者核可。")
        if self.promoted_at.tzinfo is None:
            raise ValueError("生活情報升級時間必須包含時區。")
        if self.promoted_profile.coverage_status != "official_verified":
            raise ValueError("升級後的生活情報必須標記為 official_verified。")
        if self.promoted_profile.home_university != self.home_university:
            raise ValueError("升級事件與生活情報的母校不一致。")
        if self.promoted_profile.school_name != self.school_name:
            raise ValueError("升級事件與生活情報的合作校不一致。")
        self.home_university = self.home_university.strip()
        self.school_name = self.school_name.strip()
        self.review_event_ids = event_ids
        self.reviewer_ids = reviewer_ids
        self.promoted_by_id = self.promoted_by_id.strip()
        self.promoted_by_display_name = self.promoted_by_display_name.strip()
        self.note = self.note.strip()
        if len(self.note) < 10:
            raise ValueError("生活情報升級說明至少需要 10 個字。")
        return self


class DestinationProfileRollbackRequest(BaseModel):
    home_university: str = Field(min_length=1, max_length=200)
    school_name: str = Field(min_length=1, max_length=300)
    expected_active_promotion_event_id: str = Field(min_length=1, max_length=200)
    expected_latest_publication_event_id: str = Field(min_length=1, max_length=200)
    expected_public_profile_content_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    note: str = Field(min_length=10, max_length=2000)


class DestinationProfileRollbackEvent(BaseModel):
    """Append-only restoration of the public profile that preceded a promotion."""

    id: str = Field(default_factory=lambda: str(uuid4()))
    home_university: str = Field(min_length=1, max_length=200)
    school_name: str = Field(min_length=1, max_length=300)
    rolled_back_from_event_id: str = Field(min_length=1, max_length=200)
    rolled_back_promotion_event_id: str = Field(min_length=1, max_length=200)
    restored_promotion_event_id: str | None = Field(default=None, max_length=200)
    previous_profile_content_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    restored_profile_content_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    rolled_back_by_id: str = Field(min_length=1, max_length=200)
    rolled_back_by_display_name: str = Field(min_length=1, max_length=200)
    note: str = Field(min_length=10, max_length=2000)
    rolled_back_at: datetime = Field(default_factory=utc_now)
    restored_profile: DestinationProfile

    @model_validator(mode="after")
    def validate_rollback_evidence(self) -> "DestinationProfileRollbackEvent":
        if self.rolled_back_at.tzinfo is None:
            raise ValueError("生活情報復原時間必須包含時區。")
        if self.restored_profile.home_university != self.home_university:
            raise ValueError("復原事件與生活情報的母校不一致。")
        if self.restored_profile.school_name != self.school_name:
            raise ValueError("復原事件與生活情報的合作校不一致。")
        self.home_university = self.home_university.strip()
        self.school_name = self.school_name.strip()
        self.rolled_back_promotion_event_id = (
            self.rolled_back_promotion_event_id.strip()
        )
        self.rolled_back_from_event_id = self.rolled_back_from_event_id.strip()
        if self.restored_promotion_event_id:
            self.restored_promotion_event_id = (
                self.restored_promotion_event_id.strip()
            )
        self.rolled_back_by_id = self.rolled_back_by_id.strip()
        self.rolled_back_by_display_name = (
            self.rolled_back_by_display_name.strip()
        )
        self.note = self.note.strip()
        if len(self.note) < 10:
            raise ValueError("生活情報復原說明至少需要 10 個字。")
        return self


class DestinationProfilePublicationState(BaseModel):
    home_university: str
    school_name: str
    current_candidate_content_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    current_public_profile_content_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    current_public_profile: DestinationProfile
    active_promotion_event_id: str | None = None
    latest_event_id: str | None = None
    latest_event_type: Literal["promotion", "rollback"] | None = None
    latest_actor_display_name: str | None = None
    latest_event_at: datetime | None = None
    candidate_changed_since_publication: bool = False
    can_rollback: bool = False
    promotion_history: list[DestinationProfilePromotionEvent] = Field(
        default_factory=list
    )
    rollback_history: list[DestinationProfileRollbackEvent] = Field(
        default_factory=list
    )


class DestinationProfilePublicationHistory(BaseModel):
    home_university: str | None = None
    profile_with_history_count: int = Field(default=0, ge=0)
    active_promotion_count: int = Field(default=0, ge=0)
    promotion_event_count: int = Field(default=0, ge=0)
    rollback_event_count: int = Field(default=0, ge=0)
    items: list[DestinationProfilePublicationState] = Field(default_factory=list)


class DestinationProfileReviewRow(BaseModel):
    """Read-only destination profile row awaiting independent human review."""

    snapshot_fingerprint: str = Field(pattern=r"^[0-9a-f]{64}$")
    priority_order: int = Field(ge=1)
    home_university: str
    school_name: str
    country: str | None = None
    city: str | None = None
    coverage_status: str
    review_gap_codes: list[
        Literal[
            "coverage_not_verified",
            "second_review_required",
            "missing_sources",
            "insecure_sources",
            "missing_last_checked",
        ]
    ] = Field(default_factory=list)
    last_checked: datetime | None = None
    source_count: int = Field(default=0, ge=0)
    source_titles: list[str] = Field(default_factory=list)
    source_urls: list[str] = Field(default_factory=list)
    coverage_note: str
    profile_content_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    profile: DestinationProfile
    review_history: list[DestinationProfileReviewEvent] = Field(default_factory=list)
    current_reviews: list[DestinationProfileReviewEvent] = Field(default_factory=list)
    review_approval_count: int = Field(default=0, ge=0)
    review_change_request_count: int = Field(default=0, ge=0)
    required_review_count: int = Field(default=2, ge=2, le=10)
    review_progress: Literal[
        "unstarted",
        "partial",
        "ready_for_promotion",
        "changes_required",
    ] = "unstarted"
    current_reviewer_decision: DestinationProfileReviewDecision | None = None
    ready_for_promotion: bool = False
    student_view_path: str = "/#partners"


class DestinationProfileReviewQueue(BaseModel):
    """Snapshot-bound, read-only queue for destination profile reviewers."""

    snapshot_fingerprint: str = Field(pattern=r"^[0-9a-f]{64}$")
    home_university: str | None = None
    home_universities: list[str] = Field(default_factory=list)
    total_profile_count: int = Field(default=0, ge=0)
    verified_profile_count: int = Field(default=0, ge=0)
    pending_review_count: int = Field(default=0, ge=0)
    explicit_second_review_required_count: int = Field(default=0, ge=0)
    total_source_count: int = Field(default=0, ge=0)
    pending_source_count: int = Field(default=0, ge=0)
    review_started_profile_count: int = Field(default=0, ge=0)
    ready_for_promotion_count: int = Field(default=0, ge=0)
    change_requested_profile_count: int = Field(default=0, ge=0)
    current_review_event_count: int = Field(default=0, ge=0)
    review_sections: list[DestinationProfileReviewSection] = Field(default_factory=list)
    items: list[DestinationProfileReviewRow] = Field(default_factory=list)


class DestinationProfileReviewBatchRow(BaseModel):
    """One snapshot-bound assignment row in a destination review batch."""

    queue_snapshot_fingerprint: str = Field(pattern=r"^[0-9a-f]{64}$")
    review_content_fingerprint: str = Field(pattern=r"^[0-9a-f]{64}$")
    batch_id: str = Field(
        pattern=r"^destination-[0-9a-f]{12}-\d{3}-\d{3}$"
    )
    batch_number: int = Field(ge=1)
    batch_profile_count: int = Field(ge=1)
    batch_position: int = Field(ge=1)
    priority_order: int = Field(ge=1)
    home_university: str
    school_name: str
    country: str | None = None
    city: str | None = None
    coverage_status: str
    review_gap_codes: list[
        Literal[
            "coverage_not_verified",
            "second_review_required",
            "missing_sources",
            "insecure_sources",
            "missing_last_checked",
        ]
    ] = Field(default_factory=list)
    source_count: int = Field(default=0, ge=0)
    source_titles: list[str] = Field(default_factory=list)
    source_urls: list[str] = Field(default_factory=list)
    coverage_note: str
    profile_content_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    review_approval_count: int = Field(default=0, ge=0)
    review_change_request_count: int = Field(default=0, ge=0)
    required_review_count: int = Field(default=2, ge=2, le=10)
    review_progress: Literal[
        "unstarted",
        "partial",
        "ready_for_promotion",
        "changes_required",
    ] = "unstarted"
    ready_for_promotion: bool = False
    batch_workbench_path: str
    batch_checklist_path: str
    student_view_path: str = "/#partners"


class DestinationProfileReviewBatchChecklistRow(BaseModel):
    """One source or content-section item reviewers must verify in a batch."""

    queue_snapshot_fingerprint: str = Field(pattern=r"^[0-9a-f]{64}$")
    review_content_fingerprint: str = Field(pattern=r"^[0-9a-f]{64}$")
    batch_id: str = Field(
        pattern=r"^destination-[0-9a-f]{12}-\d{3}-\d{3}$"
    )
    batch_number: int = Field(ge=1)
    batch_position: int = Field(ge=1)
    checklist_position: int = Field(ge=1)
    home_university: str
    school_name: str
    country: str | None = None
    city: str | None = None
    profile_content_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    item_type: Literal["official_source", "content_section"]
    item_key: str = Field(min_length=1, max_length=200)
    item_label: str = Field(min_length=1, max_length=300)
    item_description: str = Field(min_length=1, max_length=1000)
    candidate_content: str = Field(min_length=1)
    source_urls: list[str] = Field(default_factory=list)
    batch_workbench_path: str
    student_view_path: str = "/#partners"


class PartnerResearchRecord(BaseModel):
    home_university: str
    school_name: str
    country: str | None = None
    research_name: str | None = None
    official_website: str | None = None
    official_domain: str | None = None
    wikidata_url: str | None = None
    ranking_info: str | None = None
    ranking_source_url: str | None = None
    ranking_checked_at: datetime | None = None
    verification_status: str = "not_collected"
    candidate_title: str | None = None
    discovery_source_url: str | None = None
    checked_at: datetime = Field(default_factory=utc_now)
    note: str | None = None


class ExperienceSourceType(str, Enum):
    ARTICLE = "article"
    VIDEO = "video"
    COMMUNITY = "community"


class ExperienceDigestSection(BaseModel):
    heading: str
    points: list[str] = Field(default_factory=list)


class ExperienceDigestZh(BaseModel):
    """A Traditional Chinese write-up of what one source says, in our own words; never a full translation."""

    title_zh: str
    overview: str
    sections: list[ExperienceDigestSection] = Field(default_factory=list)
    tips: list[str] = Field(default_factory=list)
    basis: str = "依原文內容用繁體中文整理，不是全文翻譯，可能有遺漏；請以原文為準。"
    written_at: str = ""


class StudentExperienceSource(BaseModel):
    school_name: str
    country: str | None = None
    title: str
    source_url: str
    source_type: ExperienceSourceType
    platform: str
    author_name: str | None = None
    language: str = "unknown"
    summary: str
    themes: list[str] = Field(default_factory=list)
    theme_summaries: dict[str, str] = Field(default_factory=dict)
    content_status: Literal["full_text", "metadata_only", "unavailable"] = "metadata_only"
    perspective: str = "independent"
    published_at: str | None = None
    discovered_at: datetime = Field(default_factory=utc_now)
    content_hash: str
    exchange_term: str | None = None
    summary_zh: str = ""
    original_summary: str = ""
    theme_summaries_zh: dict[str, str] = Field(default_factory=dict)
    translation_status: str = "original"
    source_kind: str = "other"
    digest_zh: ExperienceDigestZh | None = None


class ExperienceHighlight(BaseModel):
    theme: str
    title: str
    summary: str
    source_count: int
    key_points: list[str] = Field(default_factory=list)
    source_urls: list[str] = Field(default_factory=list)


class ExperienceInsight(BaseModel):
    title: str
    summary: str
    source_count: int
    source_urls: list[str] = Field(default_factory=list)


class StudentExperienceDigest(BaseModel):
    school_name: str
    country: str | None = None
    total_sources: int = 0
    article_count: int = 0
    video_count: int = 0
    community_count: int = 0
    highlights: list[ExperienceHighlight] = Field(default_factory=list)
    common_strengths: list[ExperienceInsight] = Field(default_factory=list)
    common_challenges: list[ExperienceInsight] = Field(default_factory=list)
    mixed_opinions: list[ExperienceInsight] = Field(default_factory=list)
    source_years: list[int] = Field(default_factory=list)
    sources: list[StudentExperienceSource] = Field(default_factory=list)
    last_checked: datetime | None = None
    coverage_note: str = "目前尚未找到足夠的公開學生心得。"
    disclaimer: str = "學生心得屬個人經驗，可能因科系、年份與住宿方式不同；申請條件仍以校方公告為準。"


class ApplicationSourceRole(str, Enum):
    HOME_UNIVERSITY = "home_university"
    PARTNER_UNIVERSITY = "partner_university"


class ApplicationSourceAuthority(str, Enum):
    HOME_OFFICIAL_NOTICE = "home_official_notice"
    HOME_ACADEMIC_UNIT = "home_academic_unit"
    NOMINATION_NOTICE = "nomination_notice"
    PARTNER_OFFICIAL = "partner_official"
    COMMUNITY_EXPERIENCE = "community_experience"


class ApplicationSubmissionMethod(str, Enum):
    PAPER = "paper"
    ONLINE = "online"
    EMAIL = "email"
    IN_PERSON = "in_person"
    MIXED = "mixed"
    UNKNOWN = "unknown"


class ApplicationCopyType(str, Enum):
    ORIGINAL = "original"
    COPY = "copy"
    ORIGINAL_AND_COPY = "original_and_copy"
    DIGITAL = "digital"
    UNSPECIFIED = "unspecified"


class ApplicationSupportStatus(str, Enum):
    VERIFIED = "verified"
    NEEDS_CONFIRMATION = "needs_confirmation"
    UNVERIFIED = "unverified"
    LEGACY_UNCLASSIFIED = "legacy_unclassified"
    NOT_APPLICABLE = "not_applicable"


class ApplicationDeadlineStatus(str, Enum):
    VERIFIED_EXACT = "verified_exact"
    REFERENCE_ONLY = "reference_only"
    NEEDS_CONFIRMATION = "needs_confirmation"
    NOT_APPLICABLE = "not_applicable"


class ApplicationApplicabilityStatus(str, Enum):
    VERIFIED = "verified"
    NEEDS_CONFIRMATION = "needs_confirmation"


class ApplicationWorkflowReviewStatus(str, Enum):
    LEGACY = "legacy"
    DRAFT = "draft"
    PENDING_REVIEW = "pending_review"
    PUBLISHED = "published"
    REJECTED = "rejected"
    SUPERSEDED = "superseded"


class ApplicationWorkflowPublicationAction(str, Enum):
    STANDARD = "standard"
    ROLLBACK = "rollback"


class ApplicationWorkflowReviewGapCode(str, Enum):
    MISSING_ACADEMIC_YEAR = "missing_academic_year"
    MISSING_EFFECTIVE_ROUND = "missing_effective_round"
    NO_VERIFIED_EXACT_DEADLINE = "no_verified_exact_deadline"
    SOURCE_YEAR_MISSING = "source_year_missing"
    SOURCE_METADATA_MISSING = "source_metadata_missing"
    REVIEW_TIMESTAMP_MISSING = "review_timestamp_missing"
    CRITICAL_RULE_SOURCE_MISSING = "critical_rule_source_missing"
    INSECURE_OFFICIAL_SOURCE = "insecure_official_source"
    NEEDS_CONFIRMATION = "needs_confirmation"


class ApplicationRuleContext(BaseModel):
    home_university: str | None = None
    partner_university: str | None = None
    college: str | None = None
    department: str | None = None
    academic_year: str | None = None
    application_round: str | None = None


class ApplicationRuleScope(BaseModel):
    home_universities: list[str] = Field(default_factory=list)
    partner_universities: list[str] = Field(default_factory=list)
    colleges: list[str] = Field(default_factory=list)
    departments: list[str] = Field(default_factory=list)
    academic_years: list[str] = Field(default_factory=list)
    application_rounds: list[str] = Field(default_factory=list)


class ApplicationSubmissionDetails(BaseModel):
    method: ApplicationSubmissionMethod = ApplicationSubmissionMethod.UNKNOWN
    address: str | None = None
    office: str | None = None
    receiving_hours: str | None = None
    email: str | None = None
    portal_url: str | None = None
    send_by_at: datetime | None = None
    arrival_deadline_at: datetime | None = None
    deadline_note: str | None = None


class ApplicationDocumentRequirement(BaseModel):
    name: str = Field(min_length=1, max_length=240)
    copies: int | None = Field(default=None, ge=1, le=100)
    copy_type: ApplicationCopyType = ApplicationCopyType.UNSPECIFIED
    signatures: list[str] = Field(default_factory=list)
    stamps: list[str] = Field(default_factory=list)
    official_form_url: str | None = None
    source_urls: list[str] = Field(default_factory=list)
    needs_confirmation: bool = False
    stage: Literal["nomination", "student_application", "after_application", "second_submission", "post_offer", "after_dorm_assignment", "conditional_program"] | None = None
    conditional: bool = False
    condition: str | None = None
    official_form_verified: bool = False
    applicability_status: Literal["verified_current", "needs_confirmation", "reference_only"] | None = None
    applicability_year: str | None = None
    applicability_note: str | None = None

    @model_serializer(mode="wrap")
    def serialize_applicability(self, handler):
        payload = handler(self)
        fields = ("stage", "conditional", "condition", "official_form_verified",
            "applicability_status", "applicability_year", "applicability_note")
        # An additive school adapter must not invalidate old published snapshots.
        # Omitted legacy metadata stays omitted; explicitly supplied null/false
        # metadata remains part of the newer school's API and stored payload.
        if not any(getattr(self, name) for name in fields) and not self.model_fields_set.intersection(fields):
            for name in fields:
                payload.pop(name, None)
        return payload


class ApplicationWorkflowSource(BaseModel):
    title: str
    source_url: str
    role: ApplicationSourceRole
    authority: ApplicationSourceAuthority | None = None
    priority: int | None = Field(default=None, ge=1, le=5)
    effective_academic_year: str | None = None
    application_round: str | None = None
    content_hash: str | None = None
    checked_at: datetime | None = None


class ApplicationStep(BaseModel):
    rule_id: str | None = None
    depends_on_rule_ids: list[str] = Field(default_factory=list, max_length=30)
    overrides_rule_id: str | None = None
    order: int = Field(ge=1)
    phase: str
    title: str
    responsible_party: str
    responsible_unit: str | None = None
    timing: str | None = None
    deadline_at: datetime | None = None
    deadline_status: ApplicationDeadlineStatus = (
        ApplicationDeadlineStatus.NEEDS_CONFIRMATION
    )
    deadline_source_url: str | None = None
    deadline_checked_at: datetime | None = None
    deadline_reminder_eligible: bool = False
    summary: str
    details: list[str] = Field(default_factory=list)
    required_documents: list[str] = Field(default_factory=list)
    document_requirements: list[ApplicationDocumentRequirement] = Field(
        default_factory=list
    )
    signature_requirements: list[str] = Field(default_factory=list)
    official_form_urls: list[str] = Field(default_factory=list)
    scope: ApplicationRuleScope = Field(default_factory=ApplicationRuleScope)
    submission: ApplicationSubmissionDetails = Field(
        default_factory=ApplicationSubmissionDetails
    )
    action_url: str | None = None
    source_urls: list[str] = Field(default_factory=list)
    checked_at: datetime | None = None
    support_status: ApplicationSupportStatus = (
        ApplicationSupportStatus.LEGACY_UNCLASSIFIED
    )
    confirmation_contact: str | None = None
    needs_confirmation: bool = False

    @model_serializer(mode="wrap")
    def serialize_dependencies(self, handler):
        payload = handler(self)
        # Extending the model must not change hashes of existing publications.
        if not self.depends_on_rule_ids:
            payload.pop("depends_on_rule_ids", None)
        return payload

    @model_validator(mode="after")
    def populate_structured_legacy_fields(self) -> ApplicationStep:
        if not self.document_requirements and self.required_documents:
            self.document_requirements = [
                ApplicationDocumentRequirement(name=name)
                for name in self.required_documents
                if name.strip()
            ]
        if (
            self.needs_confirmation
            and self.support_status == ApplicationSupportStatus.LEGACY_UNCLASSIFIED
        ):
            self.support_status = ApplicationSupportStatus.NEEDS_CONFIRMATION
        return self


class UniversityApplicationWorkflow(BaseModel):
    workflow_id: str | None = None
    governance_key: str | None = Field(default=None, max_length=64)
    issue_report_snapshot: str | None = Field(
        default=None,
        pattern=r"^[0-9a-f]{64}$",
    )
    home_university: str = "長庚大學"
    school_name: str
    partner_website: str | None = None
    country: str | None = None
    program_type: str | None = None
    academic_year: str | None = None
    application_round: str | None = None
    effective_application_rounds: list[str] = Field(default_factory=list)
    applicability_status: ApplicationApplicabilityStatus = (
        ApplicationApplicabilityStatus.NEEDS_CONFIRMATION
    )
    applicability_note: str = (
        "適用學年度或申請梯次尚未完成官方來源確認。"
    )
    version: int = Field(default=1, ge=1)
    review_status: ApplicationWorkflowReviewStatus = (
        ApplicationWorkflowReviewStatus.LEGACY
    )
    published_at: datetime | None = None
    supersedes_version: int | None = Field(default=None, ge=1)
    applied_context: ApplicationRuleContext | None = None
    steps: list[ApplicationStep] = Field(default_factory=list)
    sources: list[ApplicationWorkflowSource] = Field(default_factory=list)
    last_checked: datetime | None = None
    coverage_status: str = "not_collected"
    coverage_note: str = "尚未查核合作校官方申請流程。"
    disclaimer: str = "截止日與申請方式可能調整；送件前請再核對母校國際處、合作校通知信與官方申請頁。"


class ApplicationPlanEligibilityStatus(str, Enum):
    ELIGIBLE = "eligible"
    NEEDS_CONFIRMATION = "needs_confirmation"
    INELIGIBLE = "ineligible"
    UNAVAILABLE = "unavailable"


class ApplicationPlanPreference(BaseModel):
    rank: int = Field(ge=1, le=5)
    school_name: str = Field(min_length=2, max_length=200)
    document_preparation_state: PartnerDocumentPreparationState | None = None


class ApplicationPlanEligibilityCheck(BaseModel):
    code: Literal[
        "availability",
        "college",
        "degree_level",
        "academic_score",
        "academic_gpa",
        "home_year",
        "home_deadline",
        "source_cycle",
        "language_score",
        "home_language_score",
        "academic_year",
        "application_round",
        "workflow",
    ]
    status: Literal["pass", "fail", "needs_confirmation"]
    title: str
    detail: str
    source_url: str | None = None
    contact_unit: str | None = None


class TaskDocumentLink(BaseModel):
    """Which preparation tool matches an official step; never a completeness claim."""

    template_ids: list[str] = Field(default_factory=list, max_length=12)
    requirement_names: list[str] = Field(default_factory=list, max_length=40)
    unmapped_requirement_names: list[str] = Field(default_factory=list, max_length=40)
    basis: Literal["document_name", "step_title", "stage", "none"] = "none"


class ApplicationPlanChecklistItem(BaseModel):
    id: str
    order: int = Field(ge=1)
    phase: str
    title: str
    detail: str
    responsible_unit: str
    support_status: ApplicationSupportStatus
    needs_confirmation: bool = False
    confirmation_contact: str | None = None
    source_urls: list[str] = Field(default_factory=list)
    task_scope: Literal["home", "partner"] = "partner"
    source_signature: str = ""
    official_deadline_at: datetime | None = None
    deadline_source_url: str | None = None
    dependency_ids: list[str] = Field(default_factory=list)
    document_link: TaskDocumentLink | None = None
    # "reference_year" tasks borrow the structure of an earlier published
    # workflow so preparation can start; they carry no official deadline.
    task_origin: Literal["official", "reference_year"] = "official"
    reference_academic_year: str | None = None
    suggested_effort_hours: float | None = Field(default=None, gt=0, le=1000)
    document_applicability: list[DocumentApplicability] = Field(default_factory=list)


class UnifiedApplicationTask(ApplicationPlanChecklistItem):
    school_names: list[str] = Field(default_factory=list)


class PersonalApplicationPlanRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    home_school: str = Field(min_length=2, max_length=80)
    college: str | None = Field(default=None, max_length=120)
    department: str | None = Field(default=None, max_length=120)
    degree_level: str | None = Field(default=None, max_length=80)
    current_year: str | None = Field(default=None, max_length=40)
    academic_score: float | None = Field(default=None, ge=0, le=100)
    academic_gpa: float | None = Field(default=None, ge=0, le=4.3)
    class_rank_percent: float | None = Field(default=None, gt=0, le=100)
    language_test: Literal["toeic", "ielts", "toefl", "toefl_new", "duolingo", "other"] | None = None
    language_score: float | None = Field(default=None, ge=0, le=1000)
    jlpt_level: Literal['N1', 'N2', 'N3', 'N4', 'N5'] | None = None
    academic_year: str | None = Field(default=None, max_length=20)
    application_round: str | None = Field(default=None, max_length=80)
    preferences: list[ApplicationPlanPreference] = Field(min_length=1, max_length=5)

    @model_validator(mode="after")
    def validate_unique_preferences(self) -> PersonalApplicationPlanRequest:
        ranks = [preference.rank for preference in self.preferences]
        schools = [
            " ".join(preference.school_name.strip().casefold().split())
            for preference in self.preferences
        ]
        if len(ranks) != len(set(ranks)):
            raise ValueError("志願序不可重複。")
        if len(schools) != len(set(schools)):
            raise ValueError("同一所學校不可重複列為志願。")
        return self


class PersonalApplicationPlanChoice(BaseModel):
    rank: int
    school_name: str
    country: str | None = None
    status: ApplicationPlanEligibilityStatus
    summary: str
    checks: list[ApplicationPlanEligibilityCheck] = Field(default_factory=list)
    checklist: list[ApplicationPlanChecklistItem] = Field(default_factory=list)
    workflow_coverage_status: str
    workflow_review_status: ApplicationWorkflowReviewStatus | None = None
    # Set when the checklist is an estimate borrowed from another period.
    reference_academic_year: str | None = None
    source_urls: list[str] = Field(default_factory=list)


class PersonalApplicationPlanResult(BaseModel):
    home_school: str
    generated_at: datetime = Field(default_factory=utc_now)
    choices: list[PersonalApplicationPlanChoice]
    contact_unit: str
    tasks: list[UnifiedApplicationTask] = Field(default_factory=list)
    disclaimer: str = "這是依已查核結構化規則產生的準備清單，不是錄取或校方資格認定；標示待確認的項目必須向指定單位確認。"


class ApplicationDocumentCatalogItem(BaseModel):
    id: str
    sequence: int = Field(ge=1)
    phase: str
    step_title: str
    name: str
    copies: int | None = Field(default=None, ge=1, le=100)
    copy_type: ApplicationCopyType = ApplicationCopyType.UNSPECIFIED
    signatures: list[str] = Field(default_factory=list)
    stamps: list[str] = Field(default_factory=list)
    official_form_url: str | None = None
    source_urls: list[str] = Field(default_factory=list)
    source_checked_at: datetime | None = None
    support_status: ApplicationSupportStatus
    needs_confirmation: bool = False
    download_available: bool = False
    contact_unit: str | None = None
    stage: Literal["nomination", "student_application", "after_application", "second_submission", "post_offer", "after_dorm_assignment", "conditional_program"] | None = None
    conditional: bool = False
    condition: str | None = None
    official_form_verified: bool = False
    applicability_status: Literal["verified_current", "needs_confirmation", "reference_only"] | None = None
    applicability_year: str | None = None
    applicability_note: str | None = None
    applicability: DocumentApplicability | None = None


class ApplicationDocumentCatalog(BaseModel):
    context: ApplicationCenterContext
    workflow_found: bool = False
    workflow_coverage_status: str = "not_collected"
    workflow_review_status: ApplicationWorkflowReviewStatus | None = None
    academic_year: str | None = None
    application_round: str | None = None
    items: list[ApplicationDocumentCatalogItem] = Field(default_factory=list)
    contact_unit: str
    disclaimer: str = "只有標示可下載的連結可視為已確認官方表格；待確認文件請依當期公告或聯絡指定單位。"


class ApplicationWorkflowReviewApproval(BaseModel):
    reviewer_id: str = Field(min_length=1, max_length=200)
    reviewed_at: datetime = Field(default_factory=utc_now)
    note: str = Field(min_length=1, max_length=1000)
    reviewed_content_hash: str | None = Field(
        default=None,
        pattern=r"^[0-9a-f]{64}$",
    )
    reviewed_source_urls: list[str] = Field(default_factory=list, max_length=200)
    reviewed_rule_keys: list[str] = Field(default_factory=list, max_length=500)

    @model_validator(mode="after")
    def validate_approval(self) -> "ApplicationWorkflowReviewApproval":
        reviewer_id = self.reviewer_id.strip()
        note = self.note.strip()
        if not reviewer_id:
            raise ValueError("審查者識別不可為空白。")
        if not note:
            raise ValueError("核准說明不可為空白。")
        if self.reviewed_at.tzinfo is None:
            raise ValueError("核准時間必須包含時區。")
        source_urls = [url.strip() for url in self.reviewed_source_urls]
        if any(not url.casefold().startswith("https://") for url in source_urls):
            raise ValueError("審查證明中的官方來源必須使用 HTTPS。")
        source_keys = [
            canonical_source_url_identity(url) for url in source_urls
        ]
        if len(source_keys) != len(set(source_keys)):
            raise ValueError("審查證明中的官方來源不可重複。")
        rule_keys = [key.strip() for key in self.reviewed_rule_keys]
        if any(not key or len(key) > 200 for key in rule_keys):
            raise ValueError("審查證明中的關鍵規定識別無效。")
        if len(rule_keys) != len(set(rule_keys)):
            raise ValueError("審查證明中的關鍵規定不可重複。")
        self.reviewer_id = reviewer_id
        self.note = note
        self.reviewed_source_urls = source_urls
        self.reviewed_rule_keys = rule_keys
        return self


class ApplicationWorkflowRevisionEdit(BaseModel):
    edited_by: str = Field(min_length=1, max_length=200)
    edited_at: datetime = Field(default_factory=utc_now)
    note: str = Field(min_length=1, max_length=1000)
    previous_content_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    content_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    invalidated_review_approvals: list[ApplicationWorkflowReviewApproval] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_edit(self) -> "ApplicationWorkflowRevisionEdit":
        self.edited_by = self.edited_by.strip()
        self.note = self.note.strip()
        if not self.edited_by:
            raise ValueError("編輯者識別不可為空白。")
        if not self.note:
            raise ValueError("修正說明不可為空白。")
        if self.edited_at.tzinfo is None:
            raise ValueError("修正時間必須包含時區。")
        if self.previous_content_hash == self.content_hash:
            raise ValueError("修正前後內容雜湊不可相同。")
        return self


class ApplicationWorkflowSourceApplicabilityUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source_url: str = Field(min_length=8, max_length=2000)
    replacement_source_url: str | None = Field(
        default=None,
        min_length=8,
        max_length=2000,
    )
    effective_academic_year: str = Field(pattern=r"^\d{3}$")
    application_round: str | None = Field(default=None, max_length=80)
    title: str | None = Field(default=None, min_length=1, max_length=240)
    role: ApplicationSourceRole | None = None
    authority: ApplicationSourceAuthority | None = None

    @model_validator(mode="after")
    def validate_source_update(self) -> "ApplicationWorkflowSourceApplicabilityUpdate":
        self.source_url = self.source_url.strip()
        if not self.source_url.casefold().startswith(("http://", "https://")):
            raise ValueError("原官方來源識別必須使用 HTTP 或 HTTPS。")
        if self.replacement_source_url is not None:
            self.replacement_source_url = self.replacement_source_url.strip() or None
        if self.replacement_source_url is not None and not (
            self.replacement_source_url.casefold().startswith("https://")
        ):
            raise ValueError("替代官方來源必須使用 HTTPS。")
        if self.application_round is not None:
            self.application_round = self.application_round.strip() or None
        if self.title is not None:
            self.title = self.title.strip() or None
        return self


class ApplicationWorkflowApplicabilityUpdateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    expected_content_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    academic_year: str = Field(pattern=r"^\d{3}$")
    application_round: str | None = Field(default=None, max_length=80)
    source_updates: list[ApplicationWorkflowSourceApplicabilityUpdate] = Field(
        default_factory=list,
        max_length=50,
    )
    note: str = Field(min_length=1, max_length=1000)

    @model_validator(mode="after")
    def validate_update(self) -> "ApplicationWorkflowApplicabilityUpdateRequest":
        self.note = self.note.strip()
        if not self.note:
            raise ValueError("修正說明不可為空白。")
        if self.application_round is not None:
            self.application_round = self.application_round.strip() or None
        urls = [
            canonical_source_url_identity(row.source_url)
            for row in self.source_updates
        ]
        if len(urls) != len(set(urls)):
            raise ValueError("同一個官方來源不可重複更新。")
        return self


class ApplicationWorkflowRevision(BaseModel):
    id: str = Field(default_factory=lambda: uuid4().hex)
    workflow_key: str
    version: int = Field(ge=1)
    base_version: int | None = Field(default=None, ge=1)
    status: ApplicationWorkflowReviewStatus = (
        ApplicationWorkflowReviewStatus.PENDING_REVIEW
    )
    content_hash: str
    change_summary: list[str] = Field(default_factory=list)
    workflow: UniversityApplicationWorkflow
    detected_by: str = "automated_refresh"
    detected_at: datetime = Field(default_factory=utc_now)
    required_review_count: int = Field(default=2, ge=2, le=10)
    review_approvals: list[ApplicationWorkflowReviewApproval] = Field(
        default_factory=list
    )
    edit_history: list[ApplicationWorkflowRevisionEdit] = Field(default_factory=list)
    reviewed_by: str | None = None
    reviewed_at: datetime | None = None
    review_note: str | None = None
    publication_action: ApplicationWorkflowPublicationAction = (
        ApplicationWorkflowPublicationAction.STANDARD
    )
    rolled_back_from_revision_id: str | None = Field(default=None, max_length=200)
    restored_revision_id: str | None = Field(default=None, max_length=200)

    @model_validator(mode="after")
    def validate_independent_approvals(self) -> "ApplicationWorkflowRevision":
        reviewer_ids = [row.reviewer_id.casefold() for row in self.review_approvals]
        if len(reviewer_ids) != len(set(reviewer_ids)):
            raise ValueError("同一位審查者不能重複核准同一版本。")
        if self.publication_action == ApplicationWorkflowPublicationAction.ROLLBACK:
            if not self.rolled_back_from_revision_id or not self.restored_revision_id:
                raise ValueError("申請流程復原版本必須記錄撤回與恢復的版本。")
            if self.rolled_back_from_revision_id == self.restored_revision_id:
                raise ValueError("申請流程復原不能把目前版本當成恢復目標。")
        elif self.rolled_back_from_revision_id or self.restored_revision_id:
            raise ValueError("一般申請流程版本不能帶有復原版本識別。")
        return self


class ApplicationWorkflowRollbackRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    workflow_key: str = Field(min_length=1, max_length=500)
    expected_current_revision_id: str = Field(min_length=1, max_length=200)
    expected_current_version: int = Field(ge=1)
    expected_current_content_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    restore_revision_id: str = Field(min_length=1, max_length=200)
    note: str = Field(min_length=10, max_length=2000)

    @model_validator(mode="after")
    def normalize_rollback_request(self) -> "ApplicationWorkflowRollbackRequest":
        self.workflow_key = self.workflow_key.strip()
        self.expected_current_revision_id = (
            self.expected_current_revision_id.strip()
        )
        self.restore_revision_id = self.restore_revision_id.strip()
        self.note = self.note.strip()
        if self.expected_current_revision_id == self.restore_revision_id:
            raise ValueError("申請流程復原目標不能是目前公開版本。")
        return self


class ApplicationWorkflowPublicationRevisionSummary(BaseModel):
    revision_id: str
    version: int = Field(ge=1)
    content_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    status: ApplicationWorkflowReviewStatus
    publication_action: ApplicationWorkflowPublicationAction
    published_at: datetime
    published_by: str
    note: str | None = None
    rolled_back_from_revision_id: str | None = None
    restored_revision_id: str | None = None
    source_count: int = Field(default=0, ge=0)
    step_count: int = Field(default=0, ge=0)
    is_current: bool = False


class ApplicationWorkflowPublicationState(BaseModel):
    workflow_key: str
    home_university: str
    school_name: str
    program_type: str | None = None
    current_revision_id: str
    current_version: int = Field(ge=1)
    current_content_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    current_published_at: datetime
    current_publication_action: ApplicationWorkflowPublicationAction
    pending_revision_id: str | None = None
    can_rollback: bool = False
    rollback_block_reason: str | None = None
    rollback_targets: list[ApplicationWorkflowPublicationRevisionSummary] = Field(
        default_factory=list
    )
    publication_history: list[ApplicationWorkflowPublicationRevisionSummary] = Field(
        default_factory=list
    )


class ApplicationWorkflowPublicationHistory(BaseModel):
    home_university: str | None = None
    workflow_count: int = Field(default=0, ge=0)
    rollback_ready_count: int = Field(default=0, ge=0)
    publication_revision_count: int = Field(default=0, ge=0)
    rollback_revision_count: int = Field(default=0, ge=0)
    items: list[ApplicationWorkflowPublicationState] = Field(default_factory=list)


class ApplicationWorkflowRefreshResult(BaseModel):
    change_detected: bool
    current_version: int | None = None
    revision: ApplicationWorkflowRevision | None = None
    workflow: UniversityApplicationWorkflow


class ApplicationWorkflowReviewRequest(BaseModel):
    note: str | None = Field(default=None, max_length=1000)


class ApplicationWorkflowApprovalRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    expected_content_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    reviewed_source_urls: list[str] = Field(min_length=1, max_length=200)
    reviewed_rule_keys: list[str] = Field(min_length=1, max_length=500)
    note: str = Field(min_length=1, max_length=1000)

    @model_validator(mode="after")
    def validate_note(self) -> "ApplicationWorkflowApprovalRequest":
        self.note = self.note.strip()
        if not self.note:
            raise ValueError("核准說明不可為空白。")
        self.reviewed_source_urls = [
            url.strip() for url in self.reviewed_source_urls
        ]
        if any(
            not url.casefold().startswith("https://")
            for url in self.reviewed_source_urls
        ):
            raise ValueError("逐頁確認的官方來源必須使用 HTTPS。")
        source_keys = [
            canonical_source_url_identity(url)
            for url in self.reviewed_source_urls
        ]
        if len(source_keys) != len(set(source_keys)):
            raise ValueError("逐頁確認的官方來源不可重複。")
        self.reviewed_rule_keys = [key.strip() for key in self.reviewed_rule_keys]
        if any(
            not key or len(key) > 200 for key in self.reviewed_rule_keys
        ):
            raise ValueError("逐項確認的關鍵規定識別無效。")
        if len(self.reviewed_rule_keys) != len(set(self.reviewed_rule_keys)):
            raise ValueError("逐項確認的關鍵規定不可重複。")
        return self


class ApplicationWorkflowValueChange(BaseModel):
    field: str
    label: str
    change_type: Literal["added", "removed", "changed"]
    before: str | None = None
    after: str | None = None


class ApplicationWorkflowStepChange(BaseModel):
    step_key: str
    change_type: Literal["added", "removed", "changed"]
    title: str
    before_title: str | None = None
    after_title: str | None = None
    changes: list[ApplicationWorkflowValueChange] = Field(default_factory=list)


class ApplicationWorkflowSourceChange(BaseModel):
    source_url: str
    change_type: Literal["added", "removed", "changed"]
    title: str
    changes: list[ApplicationWorkflowValueChange] = Field(default_factory=list)


class ApplicationWorkflowComparison(BaseModel):
    revision: ApplicationWorkflowRevision
    base_workflow: UniversityApplicationWorkflow | None = None
    has_base: bool = False
    workflow_changes: list[ApplicationWorkflowValueChange] = Field(
        default_factory=list
    )
    step_changes: list[ApplicationWorkflowStepChange] = Field(default_factory=list)
    source_changes: list[ApplicationWorkflowSourceChange] = Field(
        default_factory=list
    )
    unchanged_step_count: int = Field(default=0, ge=0)


class AffectedTaskImpact(BaseModel):
    """How one changed official step touches the student's own preparation work."""

    step_key: str
    step_title: str
    change_type: Literal["added", "removed", "changed"]
    changed_fields: list[str] = Field(default_factory=list)
    deadline_changed: bool = False
    documents_changed: bool = False
    previous_task_id: str | None = None
    current_task_id: str | None = None
    previous_status: Literal["todo", "preparing", "ready"] | None = None
    has_personal_settings: bool = False
    action: Literal["recheck_completed", "review_progress", "new_task", "retired_task"]
    guidance: str
    document_template_ids: list[str] = Field(default_factory=list)


class AccountNotificationChanges(BaseModel):
    """Student-visible source differences, without internal review identities."""

    revision_id: str
    home_university: str
    school_name: str
    academic_year: str | None = None
    application_round: str | None = None
    from_version: int | None = None
    to_version: int
    has_base: bool = False
    matches_current_plan: bool = False
    action_url: str
    workflow_changes: list[ApplicationWorkflowValueChange] = Field(default_factory=list)
    step_changes: list[ApplicationWorkflowStepChange] = Field(default_factory=list)
    source_changes: list[ApplicationWorkflowSourceChange] = Field(default_factory=list)
    affected_tasks: list[AffectedTaskImpact] = Field(default_factory=list)


class ApplicationWorkflowReviewBacklogItem(BaseModel):
    workflow_key: str
    home_university: str
    school_name: str
    country: str | None = None
    program_type: str | None = None
    academic_year: str | None = None
    application_round: str | None = None
    effective_application_rounds: list[str] = Field(default_factory=list)
    version: int = Field(ge=1)
    review_status: ApplicationWorkflowReviewStatus
    step_count: int = Field(default=0, ge=0)
    source_count: int = Field(default=0, ge=0)
    critical_rule_count: int = Field(default=0, ge=0)
    critical_rule_source_gap_count: int = Field(default=0, ge=0)
    insecure_source_count: int = Field(default=0, ge=0)
    source_replacement_candidate_count: int = Field(default=0, ge=0)
    strong_source_replacement_candidate_count: int = Field(default=0, ge=0)
    conditional_source_replacement_candidate_count: int = Field(default=0, ge=0)
    transport_blocked_source_replacement_candidate_count: int = Field(
        default=0,
        ge=0,
    )
    needs_confirmation_count: int = Field(default=0, ge=0)
    academic_year_ready: bool = False
    effective_round_ready: bool = False
    verified_exact_deadline_count: int = Field(default=0, ge=0)
    reference_deadline_count: int = Field(default=0, ge=0)
    source_year_missing_count: int = Field(default=0, ge=0)
    source_metadata_missing_count: int = Field(default=0, ge=0)
    review_timestamp_missing_count: int = Field(default=0, ge=0)
    review_gap_codes: list[ApplicationWorkflowReviewGapCode] = Field(
        default_factory=list
    )
    review_gap_count: int = Field(default=0, ge=0)
    has_pending_revision: bool = False
    pending_revision_id: str | None = None
    review_approval_count: int = Field(default=0, ge=0)
    required_review_count: int = Field(default=2, ge=2, le=10)
    review_ready_to_publish: bool = False


class ApplicationWorkflowSourceEvidenceGapGroup(BaseModel):
    source_url: str
    source_evidence_snapshot_fingerprint: str = Field(pattern=r"^[0-9a-f]{64}$")
    workflow_count: int = Field(default=0, ge=0)
    critical_rule_reference_count: int = Field(default=0, ge=0)
    home_universities: list[str] = Field(default_factory=list)
    school_names: list[str] = Field(default_factory=list)
    workflow_keys: list[str] = Field(default_factory=list)
    research_candidate: "ApplicationWorkflowSourceMetadataResearchCandidate | None" = None


class ApplicationWorkflowSourceEvidenceReviewRow(BaseModel):
    source_url: str
    source_evidence_snapshot_fingerprint: str = Field(pattern=r"^[0-9a-f]{64}$")
    home_university: str
    school_name: str
    workflow_key: str
    workflow_version: int = Field(ge=1)
    academic_year: str | None = None
    application_rounds: list[str] = Field(default_factory=list)
    referenced_rule_keys: list[str] = Field(default_factory=list)
    referenced_rule_labels: list[str] = Field(default_factory=list)
    reference_contexts: list[str] = Field(default_factory=list)
    has_pending_revision: bool = False
    pending_revision_id: str | None = None
    current_source_title: str | None = None
    current_source_role: ApplicationSourceRole | None = None
    current_source_authority: ApplicationSourceAuthority | None = None
    current_effective_academic_year: str | None = None
    current_application_round: str | None = None
    current_checked_at: datetime | None = None
    research_candidate: "ApplicationWorkflowSourceMetadataResearchCandidate | None" = None


class ApplicationWorkflowSourceResearchLead(BaseModel):
    """Safe official lead that is useful for research but not an equivalent source."""

    model_config = ConfigDict(extra="forbid")

    label: str = Field(min_length=1, max_length=200)
    url: str = Field(min_length=8, max_length=2000)
    relationship: Literal[
        "official_context",
        "adjacent_program",
        "application_system",
    ]
    transport_status: Literal["verified_https"] = "verified_https"
    transport_checked_at: date
    transport_final_url: str = Field(min_length=8, max_length=2000)
    transport_http_status: int = Field(ge=200, lt=300)
    eligible_as_replacement: Literal[False] = False
    reason_not_equivalent: str = Field(min_length=10, max_length=2000)

    @model_validator(mode="after")
    def validate_research_lead(self) -> "ApplicationWorkflowSourceResearchLead":
        self.label = self.label.strip()
        self.url = self.url.strip()
        self.transport_final_url = self.transport_final_url.strip()
        self.reason_not_equivalent = self.reason_not_equivalent.strip()
        if not self.label or not self.reason_not_equivalent:
            raise ValueError("安全研究線索必須保留名稱與不可替代原因。")
        if not self.url.casefold().startswith("https://"):
            raise ValueError("安全研究線索網址必須使用 HTTPS。")
        if not self.transport_final_url.casefold().startswith("https://"):
            raise ValueError("安全研究線索的最終網址必須維持 HTTPS。")
        return self


class ApplicationWorkflowSourceMetadataResearchCandidate(BaseModel):
    """Read-only research for one exact URL that is missing source metadata."""

    model_config = ConfigDict(extra="forbid")

    batch_id: str = Field(pattern=r"^DATA-\d{3}-BATCH-\d{3}$")
    checked_at: date
    source_url: str = Field(min_length=8, max_length=2000)
    research_status: Literal["verified_exact_source", "source_unavailable"]
    application_level_status: Literal["content_available", "not_found_page"]
    transport_checked_at: date
    transport_final_url: str = Field(min_length=8, max_length=2000)
    transport_http_status: int = Field(ge=200, lt=300)
    proposed_title: str | None = Field(default=None, max_length=300)
    proposed_role: ApplicationSourceRole | None = None
    proposed_authority: ApplicationSourceAuthority | None = None
    proposed_priority: int | None = Field(default=None, ge=1, le=5)
    proposed_effective_academic_year: str | None = Field(default=None, max_length=40)
    proposed_application_round: str | None = Field(default=None, max_length=120)
    can_prefill: Literal[False] = False
    automated_evidence: list[str] = Field(min_length=1, max_length=10)
    required_human_checks: list[str] = Field(min_length=1, max_length=10)
    reason_not_ready: str = Field(min_length=10, max_length=2000)
    research_leads: list[ApplicationWorkflowSourceResearchLead] = Field(
        default_factory=list,
        max_length=5,
    )
    review_status: Literal["human_review_required"] = "human_review_required"
    publication_effect: Literal["none"] = "none"
    approvals_created: Literal[False] = False
    public_student_data_changed: Literal[False] = False

    @model_validator(mode="after")
    def validate_source_metadata_candidate(
        self,
    ) -> "ApplicationWorkflowSourceMetadataResearchCandidate":
        self.source_url = self.source_url.strip()
        self.transport_final_url = self.transport_final_url.strip()
        if not self.source_url.casefold().startswith("https://"):
            raise ValueError("來源中繼資料研究候選必須指向 HTTPS 原網址。")
        if not self.transport_final_url.casefold().startswith("https://"):
            raise ValueError("來源中繼資料研究候選的最終網址必須維持 HTTPS。")
        self.automated_evidence = [
            value.strip() for value in self.automated_evidence if value.strip()
        ]
        self.required_human_checks = [
            value.strip() for value in self.required_human_checks if value.strip()
        ]
        self.reason_not_ready = self.reason_not_ready.strip()
        if not self.automated_evidence or not self.required_human_checks:
            raise ValueError("來源中繼資料研究候選必須保留證據與人工檢查事項。")
        if not self.reason_not_ready:
            raise ValueError("來源中繼資料研究候選必須說明尚不可採用的原因。")
        if self.proposed_title is not None:
            self.proposed_title = self.proposed_title.strip() or None
        if self.proposed_effective_academic_year is not None:
            self.proposed_effective_academic_year = (
                self.proposed_effective_academic_year.strip() or None
            )
        if self.proposed_application_round is not None:
            self.proposed_application_round = (
                self.proposed_application_round.strip() or None
            )

        if self.research_status == "verified_exact_source":
            if self.application_level_status != "content_available":
                raise ValueError("已核對原始來源必須標示內容可讀取。")
            if (
                self.proposed_title is None
                or self.proposed_role is None
                or self.proposed_authority is None
                or self.proposed_priority is None
            ):
                raise ValueError("已核對原始來源必須保留完整的候選基本中繼資料。")
        else:
            if self.application_level_status != "not_found_page":
                raise ValueError("失效來源必須明確標示應用層找不到頁面。")
            proposed_values = (
                self.proposed_title,
                self.proposed_role,
                self.proposed_authority,
                self.proposed_priority,
                self.proposed_effective_academic_year,
                self.proposed_application_round,
            )
            if any(value is not None for value in proposed_values):
                raise ValueError("失效來源不得提供可誤用的中繼資料候選值。")
            if not self.research_leads:
                raise ValueError("失效來源至少要保留一筆不可直接替代的安全研究線索。")

        research_keys = [
            canonical_source_url_identity(lead.url)
            for lead in self.research_leads
        ]
        if len(research_keys) != len(set(research_keys)):
            raise ValueError("來源中繼資料的安全研究線索不可重複。")
        if canonical_source_url_identity(self.source_url) in research_keys:
            raise ValueError("安全研究線索不可與失效原網址相同。")
        return self


class ApplicationWorkflowSourceReplacementCandidateDefinition(BaseModel):
    """Research evidence that may be applied only through human review."""

    model_config = ConfigDict(extra="forbid")

    batch_id: str = Field(pattern=r"^DATA-\d{3}-BATCH-\d{3}$")
    checked_at: date
    workflow_id: str = Field(pattern=r"^workflow-[0-9a-z]+$")
    current_url: str = Field(min_length=8, max_length=2000)
    candidate_url: str = Field(min_length=8, max_length=2000)
    candidate_status: Literal["strong_candidate", "conditional_candidate"]
    transport_status: Literal[
        "verified_https",
        "downgrades_to_http",
        "unverified",
    ]
    transport_checked_at: date | None = None
    transport_final_url: str | None = Field(default=None, min_length=8, max_length=2000)
    transport_http_status: int | None = Field(default=None, ge=100, le=599)
    can_prefill: bool = False
    automated_evidence: list[str] = Field(min_length=1, max_length=10)
    required_human_checks: list[str] = Field(min_length=1, max_length=10)
    supporting_urls: list[str] = Field(default_factory=list, max_length=10)
    research_leads: list[ApplicationWorkflowSourceResearchLead] = Field(
        default_factory=list,
        max_length=10,
    )
    review_status: Literal["human_review_required"] = "human_review_required"
    publication_effect: Literal["none"] = "none"
    approvals_created: Literal[False] = False
    public_student_data_changed: Literal[False] = False

    @model_validator(mode="after")
    def validate_candidate_definition(
        self,
    ) -> "ApplicationWorkflowSourceReplacementCandidateDefinition":
        self.current_url = self.current_url.strip()
        self.candidate_url = self.candidate_url.strip()
        if not self.current_url.casefold().startswith(("http://", "https://")):
            raise ValueError("候選來源的原網址必須使用 HTTP 或 HTTPS。")
        if not self.candidate_url.casefold().startswith("https://"):
            raise ValueError("候選替代網址必須使用 HTTPS。")
        if self.current_url.casefold() == self.candidate_url.casefold():
            raise ValueError("候選替代網址不可與原網址相同。")
        if self.transport_final_url is not None:
            self.transport_final_url = self.transport_final_url.strip()
        if self.transport_status == "verified_https":
            if self.transport_checked_at is None:
                raise ValueError("已驗證 HTTPS 的候選必須記錄傳輸查核日。")
            if not (self.transport_final_url or "").casefold().startswith(
                "https://"
            ):
                raise ValueError("已驗證 HTTPS 的候選最終網址必須仍為 HTTPS。")
            if self.transport_http_status is None or not (
                200 <= self.transport_http_status < 300
            ):
                raise ValueError("已驗證 HTTPS 的候選必須記錄 2xx HTTP 狀態。")
        elif self.transport_status == "downgrades_to_http":
            if self.transport_checked_at is None:
                raise ValueError("會降級為 HTTP 的候選必須記錄傳輸查核日。")
            if not (self.transport_final_url or "").casefold().startswith("http://"):
                raise ValueError("HTTP 降級候選的最終網址必須使用 HTTP。")
            if self.transport_http_status is None:
                raise ValueError("HTTP 降級候選必須記錄 HTTP 狀態。")
        self.can_prefill = self.transport_status == "verified_https"
        self.automated_evidence = [
            value.strip() for value in self.automated_evidence if value.strip()
        ]
        self.required_human_checks = [
            value.strip() for value in self.required_human_checks if value.strip()
        ]
        if not self.automated_evidence or not self.required_human_checks:
            raise ValueError("候選來源必須保留研究證據與人工檢查事項。")
        self.supporting_urls = [
            value.strip() for value in self.supporting_urls if value.strip()
        ]
        if any(
            not value.casefold().startswith("https://")
            for value in self.supporting_urls
        ):
            raise ValueError("候選來源的輔助連結必須使用 HTTPS。")
        supporting_keys = [value.casefold() for value in self.supporting_urls]
        if len(supporting_keys) != len(set(supporting_keys)):
            raise ValueError("候選來源的輔助連結不可重複。")
        research_keys = [lead.url.casefold() for lead in self.research_leads]
        if len(research_keys) != len(set(research_keys)):
            raise ValueError("安全研究線索網址不可重複。")
        reserved_keys = {
            self.current_url.casefold(),
            self.candidate_url.casefold(),
            *supporting_keys,
        }
        if any(key in reserved_keys for key in research_keys):
            raise ValueError("安全研究線索不可與目前、候選或輔助網址重複。")
        return self


class ApplicationWorkflowSourceReplacementCandidate(
    ApplicationWorkflowSourceReplacementCandidateDefinition
):
    revision_id: str = Field(min_length=1, max_length=200)
    workflow_key: str = Field(min_length=1, max_length=500)


class ApplicationWorkflowSourceReplacementReviewRow(
    ApplicationWorkflowSourceReplacementCandidateDefinition
):
    """Read-only review queue row for staged or unstaged workflows."""

    review_content_fingerprint: str = Field(pattern=r"^[0-9a-f]{64}$")
    workflow_key: str = Field(min_length=1, max_length=500)
    home_university: str
    school_name: str
    country: str | None = None
    program_type: str | None = None
    workflow_version: int = Field(ge=1)
    academic_year: str | None = None
    application_rounds: list[str] = Field(default_factory=list)
    has_pending_revision: bool = False
    pending_revision_id: str | None = None
    workbench_path: str = Field(min_length=1, max_length=2000)


class ApplicationWorkflowReviewBacklog(BaseModel):
    items: list[ApplicationWorkflowReviewBacklogItem] = Field(default_factory=list)
    total_count: int = Field(default=0, ge=0)
    unstaged_count: int = Field(default=0, ge=0)
    staged_count: int = Field(default=0, ge=0)
    review_unstarted_count: int = Field(default=0, ge=0)
    review_partially_approved_count: int = Field(default=0, ge=0)
    review_ready_count: int = Field(default=0, ge=0)
    critical_rule_count: int = Field(default=0, ge=0)
    workflows_with_critical_rule_source_gaps: int = Field(default=0, ge=0)
    workflows_with_insecure_sources: int = Field(default=0, ge=0)
    workflows_with_source_replacement_candidates: int = Field(default=0, ge=0)
    source_replacement_candidate_count: int = Field(default=0, ge=0)
    transport_blocked_source_replacement_candidate_count: int = Field(
        default=0,
        ge=0,
    )
    missing_academic_year_count: int = Field(default=0, ge=0)
    missing_effective_round_count: int = Field(default=0, ge=0)
    no_verified_exact_deadline_count: int = Field(default=0, ge=0)
    workflows_with_source_year_gaps: int = Field(default=0, ge=0)
    workflows_with_source_metadata_gaps: int = Field(default=0, ge=0)
    source_metadata_gap_reference_count: int = Field(default=0, ge=0)
    distinct_source_metadata_gap_url_count: int = Field(default=0, ge=0)
    source_metadata_gap_groups: list[
        ApplicationWorkflowSourceEvidenceGapGroup
    ] = Field(default_factory=list)
    workflows_with_review_timestamp_gaps: int = Field(default=0, ge=0)
    needs_confirmation_workflow_count: int = Field(default=0, ge=0)
    home_universities: list[str] = Field(default_factory=list)


class ApplicationWorkflowReleaseGateCheck(BaseModel):
    code: str = Field(pattern=r"^[a-z0-9_]+$")
    label: str
    passed: bool
    actual_count: int = Field(ge=0)
    required_count: int = Field(ge=0)
    comparison: Literal["equal", "at_least"] = "equal"
    detail: str


class ApplicationWorkflowReleaseReadinessReport(BaseModel):
    generated_at: datetime = Field(default_factory=utc_now)
    snapshot_fingerprint: str = Field(pattern=r"^[0-9a-f]{64}$")
    release_ready: bool = False
    blocking_check_count: int = Field(default=0, ge=0)
    total_workflow_count: int = Field(default=0, ge=0)
    published_workflow_count: int = Field(default=0, ge=0)
    unpublished_workflow_count: int = Field(default=0, ge=0)
    published_without_dual_review_evidence_count: int = Field(default=0, ge=0)
    publication_history_integrity_gap_count: int = Field(default=0, ge=0)
    pending_revision_count: int = Field(default=0, ge=0)
    critical_rule_count: int = Field(default=0, ge=0)
    critical_rule_source_gap_count: int = Field(default=0, ge=0)
    missing_academic_year_workflow_count: int = Field(default=0, ge=0)
    missing_effective_round_workflow_count: int = Field(default=0, ge=0)
    no_verified_exact_deadline_workflow_count: int = Field(default=0, ge=0)
    source_metadata_gap_count: int = Field(default=0, ge=0)
    source_year_gap_count: int = Field(default=0, ge=0)
    review_timestamp_gap_count: int = Field(default=0, ge=0)
    insecure_source_url_count: int = Field(default=0, ge=0)
    needs_confirmation_rule_count: int = Field(default=0, ge=0)
    checks: list[ApplicationWorkflowReleaseGateCheck] = Field(default_factory=list)


class WebReleaseReadinessReport(ApplicationWorkflowReleaseReadinessReport):
    application_workflow_snapshot_fingerprint: str = Field(
        pattern=r"^[0-9a-f]{64}$"
    )
    application_workflow_blocking_check_count: int = Field(default=0, ge=0)
    destination_profile_snapshot_fingerprint: str = Field(
        pattern=r"^[0-9a-f]{64}$"
    )
    destination_profile_blocking_check_count: int = Field(default=0, ge=0)
    total_destination_profile_count: int = Field(default=0, ge=0)
    verified_destination_profile_count: int = Field(default=0, ge=0)
    pending_destination_profile_review_count: int = Field(default=0, ge=0)
    pending_destination_profile_source_count: int = Field(default=0, ge=0)
    destination_profile_review_started_count: int = Field(default=0, ge=0)
    destination_profile_ready_for_promotion_count: int = Field(default=0, ge=0)
    destination_profile_change_requested_count: int = Field(default=0, ge=0)
    destination_profile_review_event_count: int = Field(default=0, ge=0)
    destination_profile_promotion_event_count: int = Field(default=0, ge=0)
    destination_profile_rollback_event_count: int = Field(default=0, ge=0)
    destination_profile_publication_integrity_gap_count: int = Field(
        default=0,
        ge=0,
    )


class ApplicationWorkflowIssueCategory(str, Enum):
    ELIGIBILITY = "eligibility"
    DEADLINE = "deadline"
    DOCUMENT = "document"
    SUBMISSION = "submission"
    SOURCE = "source"
    OTHER = "other"


class ApplicationWorkflowIssueReportStatus(str, Enum):
    PENDING = "pending"
    RESOLVED = "resolved"
    DISMISSED = "dismissed"


def _validated_public_https_source_url(value: str) -> str:
    source_url = value.strip()
    parsed = urlsplit(source_url)
    hostname = (parsed.hostname or "").strip().casefold().rstrip(".")
    unsafe_hostname = hostname == "localhost" or hostname.endswith(".localhost")
    if parsed.scheme.casefold() != "https" or not hostname:
        raise ValueError("回報附上的官方來源必須是完整 HTTPS 網址。")
    if parsed.username is not None or parsed.password is not None:
        raise ValueError("官方來源網址不得包含帳號、密碼或其他登入憑證。")
    if unsafe_hostname:
        raise ValueError("官方來源網址必須指向公開網站。")
    try:
        address = ipaddress.ip_address(hostname)
    except ValueError:
        address = None
    if address is not None and (
        address.is_private
        or address.is_loopback
        or address.is_link_local
        or address.is_reserved
        or address.is_unspecified
        or address.is_multicast
    ):
        raise ValueError("官方來源網址必須指向公開網站。")
    if any(ord(character) < 32 for character in source_url):
        raise ValueError("官方來源網址含有不安全字元。")
    return source_url


class ApplicationWorkflowIssueReportCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    home_school: str = Field(min_length=2, max_length=80)
    school_name: str = Field(min_length=2, max_length=200)
    workflow_id: str = Field(min_length=8, max_length=128)
    workflow_version: int = Field(ge=1)
    workflow_snapshot: str = Field(pattern=r"^[0-9a-f]{64}$")
    step_rule_id: str | None = Field(default=None, min_length=1, max_length=240)
    college: str | None = Field(default=None, max_length=120)
    department: str | None = Field(default=None, max_length=120)
    academic_year: str | None = Field(default=None, max_length=40)
    application_round: str | None = Field(default=None, max_length=80)
    category: ApplicationWorkflowIssueCategory
    description: str = Field(min_length=10, max_length=1000)
    official_source_url: str = Field(min_length=12, max_length=2000)

    @model_validator(mode="after")
    def normalize_issue_report(self) -> ApplicationWorkflowIssueReportCreate:
        self.home_school = self.home_school.strip()
        self.school_name = self.school_name.strip()
        self.workflow_id = self.workflow_id.strip()
        self.step_rule_id = (self.step_rule_id or "").strip() or None
        self.college = (self.college or "").strip() or None
        self.department = (self.department or "").strip() or None
        self.academic_year = (self.academic_year or "").strip() or None
        self.application_round = (self.application_round or "").strip() or None
        self.description = self.description.strip()
        self.official_source_url = _validated_public_https_source_url(
            self.official_source_url
        )
        return self


class ApplicationWorkflowIssueReportReviewRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: Literal[
        ApplicationWorkflowIssueReportStatus.RESOLVED,
        ApplicationWorkflowIssueReportStatus.DISMISSED,
    ]
    note: str = Field(min_length=10, max_length=1000)

    @field_validator("note")
    @classmethod
    def normalize_review_note(cls, value: str) -> str:
        return value.strip()


class ApplicationWorkflowIssueReportReview(BaseModel):
    id: str = Field(default_factory=lambda: uuid4().hex)
    report_id: str
    status: Literal[
        ApplicationWorkflowIssueReportStatus.RESOLVED,
        ApplicationWorkflowIssueReportStatus.DISMISSED,
    ]
    note: str
    reviewer_display_name: str
    reviewed_at: datetime = Field(default_factory=utc_now)


class ApplicationWorkflowIssueReport(BaseModel):
    id: str = Field(default_factory=lambda: uuid4().hex)
    workflow_key: str = Field(min_length=1, max_length=500)
    workflow_id: str = Field(min_length=8, max_length=128)
    workflow_version: int = Field(ge=1)
    workflow_snapshot: str = Field(pattern=r"^[0-9a-f]{64}$")
    home_school: str
    school_name: str
    step_rule_id: str | None = None
    step_title: str | None = None
    college: str | None = None
    department: str | None = None
    academic_year: str | None = None
    application_round: str | None = None
    category: ApplicationWorkflowIssueCategory
    description: str
    official_source_url: str
    status: ApplicationWorkflowIssueReportStatus = (
        ApplicationWorkflowIssueReportStatus.PENDING
    )
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)
    review: ApplicationWorkflowIssueReportReview | None = None


class ApplicationWorkflowReviewBatchRow(BaseModel):
    snapshot_fingerprint: str = Field(pattern=r"^[0-9a-f]{64}$")
    review_content_fingerprint: str = Field(pattern=r"^[0-9a-f]{64}$")
    batch_id: str = Field(pattern=r"^review-[0-9a-f]{12}-\d{3}-\d{3}$")
    batch_number: int = Field(ge=1)
    batch_workflow_count: int = Field(ge=1)
    batch_position: int = Field(ge=1)
    priority_order: int = Field(ge=1)
    workflow_key: str
    home_university: str
    school_name: str
    country: str | None = None
    program_type: str | None = None
    academic_year: str | None = None
    application_rounds: list[str] = Field(default_factory=list)
    review_gap_codes: list[ApplicationWorkflowReviewGapCode] = Field(
        default_factory=list
    )
    review_gap_count: int = Field(default=0, ge=0)
    critical_rule_count: int = Field(default=0, ge=0)
    source_count: int = Field(default=0, ge=0)
    source_metadata_missing_count: int = Field(default=0, ge=0)
    source_year_missing_count: int = Field(default=0, ge=0)
    review_timestamp_missing_count: int = Field(default=0, ge=0)
    critical_rule_source_gap_count: int = Field(default=0, ge=0)
    insecure_source_count: int = Field(default=0, ge=0)
    needs_confirmation_count: int = Field(default=0, ge=0)
    verified_exact_deadline_count: int = Field(default=0, ge=0)
    has_pending_revision: bool = False
    pending_revision_id: str | None = None
    review_approval_count: int = Field(default=0, ge=0)
    required_review_count: int = Field(default=2, ge=2, le=10)
    review_ready_to_publish: bool = False
    workbench_path: str
    batch_workbench_path: str
    batch_rule_checklist_path: str


class ApplicationWorkflowReviewBatchStageRequest(BaseModel):
    expected_snapshot: str = Field(pattern=r"^[0-9a-f]{64}$")
    batch_size: int = Field(default=10, ge=1, le=50)


class ApplicationWorkflowReviewBatchStageItem(BaseModel):
    workflow_key: str
    revision_id: str
    created: bool = False


class ApplicationWorkflowReviewBatchStageResult(BaseModel):
    batch_id: str = Field(pattern=r"^review-[0-9a-f]{12}-\d{3}-\d{3}$")
    review_content_fingerprint: str = Field(pattern=r"^[0-9a-f]{64}$")
    batch_size: int = Field(ge=1, le=50)
    workflow_count: int = Field(ge=1)
    created_count: int = Field(default=0, ge=0)
    existing_count: int = Field(default=0, ge=0)
    items: list[ApplicationWorkflowReviewBatchStageItem] = Field(
        default_factory=list
    )
    approvals_created: Literal[False] = False
    workflows_published: Literal[False] = False
    public_student_data_changed: Literal[False] = False


class ApplicationWorkflowReviewBatchRuleRow(BaseModel):
    snapshot_fingerprint: str = Field(pattern=r"^[0-9a-f]{64}$")
    review_content_fingerprint: str = Field(pattern=r"^[0-9a-f]{64}$")
    batch_id: str = Field(pattern=r"^review-[0-9a-f]{12}-\d{3}-\d{3}$")
    batch_number: int = Field(ge=1)
    batch_position: int = Field(ge=1)
    workflow_key: str
    home_university: str
    school_name: str
    academic_year: str | None = None
    application_rounds: list[str] = Field(default_factory=list)
    rule_key: str
    rule_label: str
    rule_detail: str
    source_urls: list[str] = Field(default_factory=list)
    source_titles: list[str] = Field(default_factory=list)
    source_roles: list[str] = Field(default_factory=list)
    source_authorities: list[str] = Field(default_factory=list)
    source_academic_years: list[str] = Field(default_factory=list)
    source_checked_at: list[str] = Field(default_factory=list)
    source_metadata_missing_count: int = Field(default=0, ge=0)
    source_year_missing_count: int = Field(default=0, ge=0)
    review_timestamp_missing_count: int = Field(default=0, ge=0)
    insecure_source_count: int = Field(default=0, ge=0)
    needs_confirmation: bool = False
    blocked: bool = False
    workbench_path: str


class HomeSelectionRules(BaseModel):
    academic_policy: Literal["percentage", "gpa_or_rank"] = "percentage"
    academic_reference_year: str | None = None
    undergraduate_gpa_minimum: float | None = None
    undergraduate_rank_maximum: float | None = None
    graduate_academic_exempt: bool = False
    exclude_in_service: bool = False
    pending_quota_planning: bool = False
    partner_requirements_need_confirmation: bool = False
    degree_score_minimums: dict[str, float] = Field(default_factory=dict)
    excluded_undergraduate_years: list[str] = Field(default_factory=list)
    language_certificate_required: bool = False


class CatalogueSourceStatus(BaseModel):
    status: Literal["retrieved", "saved_reference", "unavailable"]
    last_success_at: datetime | None = None
    last_attempt_at: datetime | None = None
    last_attempt_result: Literal["success", "failed"] | None = None
    failure_reason: str | None = None
    snapshot_hash: str | None = None
    source_urls: list[str] = Field(default_factory=list)
    # Retrieval time does not establish the academic year or current publication status.
    current_cycle_verified: bool = False


class StudentDashboard(BaseModel):
    catalogue_source: CatalogueSourceStatus | None = None
    school_name: str = "長庚大學"
    last_checked: datetime | None = None
    academic_score_minimum: float | None = None
    academic_score_rule: str | None = None
    academic_gpa_minimum: float | None = None
    maximum_preferences: int = 5
    selection_rules: HomeSelectionRules = Field(default_factory=HomeSelectionRules)
    language_score_minimums: dict[str, float] = Field(default_factory=dict)
    application_periods: list[ApplicationPeriodItem] = Field(default_factory=list)
    program_overview: list[StudentInfoItem] = Field(default_factory=list)
    eligibility: list[StudentInfoItem] = Field(default_factory=list)
    language_requirements: list[StudentInfoItem] = Field(default_factory=list)
    required_documents: list[StudentInfoItem] = Field(default_factory=list)
    scholarship_info: list[StudentInfoItem] = Field(default_factory=list)
    document_explanations: list[RuleExplanation] = Field(default_factory=list)
    rule_explanations: list[RuleExplanation] = Field(default_factory=list)
    partner_universities: list[PartnerUniversity] = Field(default_factory=list)
    sources: list[SourceReference] = Field(default_factory=list)

    @model_serializer(mode="wrap")
    def serialize_catalogue_source(self, handler):
        payload = handler(self)
        # Preserve the byte-stable non-CGU bundles; source metadata is additive
        # only for a dashboard with an actual catalogue source provider.
        if self.catalogue_source is None:
            payload.pop("catalogue_source", None)
        return payload


TeachingLanguage = Literal["english", "japanese", "chinese", "other"]


class BudgetFitEstimate(BaseModel):
    currency: str
    low: float
    high: float
    includes: list[str] = Field(default_factory=list)
    as_of_year: int | None = None
    evidence: str
    source_urls: list[str] = Field(default_factory=list)
    twd_per_unit: float | None = None


class BudgetFit(BaseModel):
    """Sourced monthly living cost against the student's monthly budget (TWD)."""

    status: Literal["within", "partly_within", "over", "unknown"]
    reason: str | None = None
    estimate: BudgetFitEstimate | None = None
    low_twd: int | None = None
    high_twd: int | None = None
    exclusions: str = "不含學費、機票、簽證、保險與抵達初期費用。"
    fx_note: str | None = None


class TeachingLanguageFit(BaseModel):
    status: Literal["listed", "not_listed", "unknown"]
    languages: list[str] = Field(default_factory=list)
    basis: Literal["partner_track", "requirement_text", "none"] = "none"
    detail: str


class CourseInterestFit(BaseModel):
    status: Literal["mentioned", "unknown"]
    matched_terms: list[str] = Field(default_factory=list)
    evidence: list[str] = Field(default_factory=list)
    detail: str


class AdvisorProfile(BaseModel):
    target_school: str | None = Field(default=None, max_length=1000)
    school_name: str = "長庚大學"
    college: str | None = Field(default=None, max_length=120)
    department: str | None = Field(default=None, max_length=120)
    current_year: str | None = Field(default=None, max_length=40)
    degree_level: str | None = Field(default=None, max_length=80)
    academic_score: float | None = Field(default=None, ge=0, le=100)
    academic_gpa: float | None = Field(default=None, ge=0, le=4.3)
    class_rank_percent: float | None = Field(default=None, gt=0, le=100)
    language_test: Literal["toeic", "ielts", "toefl", "toefl_new", "duolingo", "other"] | None = None
    language_score: float | None = Field(default=None, ge=0, le=1000)
    jlpt_level: Literal['N1', 'N2', 'N3', 'N4', 'N5'] | None = None
    academic_year: str | None = Field(default=None, max_length=20)
    application_round: str | None = Field(default=None, max_length=80)
    target_term: str | None = Field(default=None, max_length=40)
    preferred_country: str | None = Field(default=None, max_length=80)
    monthly_budget: float | None = Field(default=None, ge=0, le=10_000_000)
    needs_scholarship: bool = False
    preferred_teaching_language: TeachingLanguage | None = None
    course_interests: str | None = Field(default=None, max_length=120)
    question: str | None = Field(default=None, max_length=500)


class AdvisorQuestionRequest(BaseModel):
    question: str = Field(min_length=2, max_length=500)
    profile: AdvisorProfile | None = None


class AdvisorCitation(BaseModel):
    title: str
    source_url: str
    section: str | None = None
    published_at: str | None = None
    last_checked: datetime | None = None


class AdvisorSchoolMatch(BaseModel):
    school_name: str
    country: str | None = None
    match_score: int = Field(ge=0, le=100)
    fit_label: str
    eligibility_status: Literal["matches_known", "needs_confirmation", "does_not_match"] = "needs_confirmation"
    blocking_reasons: list[str] = Field(default_factory=list)
    confirmation_items: list[str] = Field(default_factory=list)
    reasons: list[str] = Field(default_factory=list)
    gaps: list[str] = Field(default_factory=list)
    source_urls: list[str] = Field(default_factory=list)
    image_url: str | None = None
    budget_fit: BudgetFit | None = None
    teaching_language: TeachingLanguageFit | None = None
    course_interest: CourseInterestFit | None = None


class AdvisorTask(BaseModel):
    id: str
    title: str
    detail: str
    category: str
    priority: Literal["high", "medium", "low"] = "medium"
    due_date: str | None = None
    days_remaining: int | None = None
    source_url: str | None = None


class AdvisorAnswer(BaseModel):
    question: str
    answer: str
    key_points: list[str] = Field(default_factory=list)
    sources: list[AdvisorCitation] = Field(default_factory=list)
    evidence_status: Literal["grounded", "limited", "not_found"] = "not_found"
    ai_enhanced: bool = False


class AdvisorPlan(BaseModel):
    school_name: str = "長庚大學"
    generated_at: datetime = Field(default_factory=utc_now)
    mode: Literal["source_grounded", "ai_enhanced"] = "source_grounded"
    summary: str
    qualification: list[str] = Field(default_factory=list)
    recommendations: list[AdvisorSchoolMatch] = Field(default_factory=list)
    target_match: AdvisorSchoolMatch | None = None
    tasks: list[AdvisorTask] = Field(default_factory=list)
    answer: AdvisorAnswer | None = None
    disclaimer: str = "符合度是依公開條件計算的整理結果，不是錄取機率；正式資格與期限仍以校方最新公告為準。"


class DocumentCheckIssue(BaseModel):
    severity: Literal["error", "warning", "info"]
    code: str
    title: str
    detail: str


class DocumentCheckResult(BaseModel):
    file_name: str
    document_type: str
    summary: str
    page_count: int = Field(default=1, ge=0)
    character_count: int = Field(default=0, ge=0)
    word_count: int = Field(default=0, ge=0)
    completeness_score: int = Field(default=0, ge=0, le=100)
    checks_passed: list[str] = Field(default_factory=list)
    issues: list[DocumentCheckIssue] = Field(default_factory=list)
    suggestions: list[str] = Field(default_factory=list)
    extracted_preview: str = ""
    ai_enhanced: bool = False
    privacy_note: str = "檔案只在本次請求的記憶體中檢查，不會保存原檔。"


class DocumentRewriteRequest(BaseModel):
    text: str = Field(min_length=20, max_length=16_000)
    action: Literal["formalize", "translate_en", "shorten", "grammar"]
    document_type: str = Field(default="study_plan", max_length=80)
    target_word_limit: int | None = Field(default=None, ge=20, le=5000)
    ai_consent_granted: bool = False
    ai_consent_timestamp: datetime | None = None
    school_context: str | None = Field(default=None, max_length=500)


class DocumentRewriteResult(BaseModel):
    action: Literal["formalize", "translate_en", "shorten", "grammar"]
    draft: str
    changes: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    ai_enhanced: bool = True
    disclaimer: str = "AI 建議稿，送出前請自行確認內容真實性。"


class CommunityTopic(str, Enum):
    APPLICATION = "application"
    HOUSING = "housing"
    ACADEMICS = "academics"
    LIFE = "life"
    PRE_DEPARTURE = "pre_departure"
    SCHOLARSHIP = "scholarship"
    VISA = "visa"
    COST = "cost"
    CAREER = "career"
    WARNING = "warning"


class CommunityBoardKind(str, Enum):
    PUBLIC_STUDY_ABROAD = "public_study_abroad"
    PUBLIC_TOPIC = "public_topic"
    UNIVERSITY_EXCHANGE = "university_exchange"


class CommunityBoardPostingRequirement(str, Enum):
    VERIFIED_EMAIL = "verified_email"
    VERIFIED_UNIVERSITY = "verified_university"


class CommunityBoardAccess(BaseModel):
    id: str
    label: str
    kind: CommunityBoardKind
    school_name: str | None = None
    posting_requirement: CommunityBoardPostingRequirement
    can_read: bool = True
    can_post: bool = False
    can_comment: bool = False
    unavailable_reason: str | None = None


class ModerationStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    HIDDEN = "hidden"


class CommunityIdentityMode(str, Enum):
    ANONYMOUS = "anonymous"
    REAL_NAME = "real_name"
    VERIFIED_SCHOOL = "verified_school"
    VERIFIED_DEPARTMENT = "verified_department"


class CommunityIdentityOption(BaseModel):
    mode: CommunityIdentityMode
    label: str
    enabled: bool = True
    unavailable_reason: str | None = None


class CommunityIdentityOptions(BaseModel):
    default_mode: CommunityIdentityMode = CommunityIdentityMode.ANONYMOUS
    options: list[CommunityIdentityOption] = Field(default_factory=list)


class CommunityModerationRequest(BaseModel):
    status: Literal[ModerationStatus.APPROVED, ModerationStatus.HIDDEN]
    expected_status: ModerationStatus | None = None
    note: str = Field(min_length=2, max_length=500)


class CommunitySuspensionRequest(BaseModel):
    suspended_until: datetime
    reason: str = Field(min_length=2, max_length=500)

    @field_validator("suspended_until")
    @classmethod
    def require_timezone(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("停權期限必須包含時區。")
        return value

    @field_validator("reason")
    @classmethod
    def normalize_reason(cls, value: str) -> str:
        reason = value.strip()
        if len(reason) < 2:
            raise ValueError("停權原因至少需要 2 個字。")
        return reason


class CommunityPublishEvent(BaseModel):
    id: str = Field(default_factory=lambda: uuid4().hex)
    account_id: str
    created_at: datetime = Field(default_factory=utc_now)


class CommunityModerationAudit(BaseModel):
    id: str = Field(default_factory=lambda: uuid4().hex)
    resource_type: str
    resource_id: str
    previous_status: str
    new_status: str
    moderator_id: str
    note: str
    previous_suspended_until: datetime | None = None
    new_suspended_until: datetime | None = None
    retained_until: datetime | None = None
    created_at: datetime = Field(default_factory=utc_now)


class CommunityQuestionCreate(BaseModel):
    school_name: str = Field(min_length=2, max_length=200)
    home_university: str = Field(default="長庚大學", min_length=2, max_length=80)
    topic: CommunityTopic
    title: str = Field(min_length=4, max_length=120)
    body: str = Field(min_length=10, max_length=1000)
    display_name: str = Field(default="匿名學生", min_length=2, max_length=30)
    identity_mode: CommunityIdentityMode = CommunityIdentityMode.ANONYMOUS
    accept_rules: Literal[True]


class CommunityQuestion(BaseModel):
    id: str = Field(default_factory=lambda: uuid4().hex)
    author_id: str | None = None
    school_name: str
    home_university: str
    topic: CommunityTopic
    title: str
    body: str
    display_name: str = "匿名學生"
    identity_mode: CommunityIdentityMode = CommunityIdentityMode.ANONYMOUS
    status: ModerationStatus = ModerationStatus.PENDING
    answer_count: int = 0
    created_at: datetime = Field(default_factory=utc_now)


class CommunityAnswerCreate(BaseModel):
    body: str = Field(min_length=10, max_length=1500)
    display_name: str = Field(default="匿名學長姐", min_length=2, max_length=30)
    identity_mode: CommunityIdentityMode = CommunityIdentityMode.ANONYMOUS
    exchange_year: str | None = Field(default=None, max_length=20)
    accept_rules: Literal[True]


class CommunityAnswer(BaseModel):
    id: str = Field(default_factory=lambda: uuid4().hex)
    author_id: str | None = None
    question_id: str
    body: str
    display_name: str = "匿名學長姐"
    identity_mode: CommunityIdentityMode = CommunityIdentityMode.ANONYMOUS
    exchange_year: str | None = None
    verified_experience: bool = False
    status: ModerationStatus = ModerationStatus.PENDING
    created_at: datetime = Field(default_factory=utc_now)


class CommunityQuestionThread(BaseModel):
    question: CommunityQuestion
    answers: list[CommunityAnswer] = Field(default_factory=list)


class AnonymousIdentityCreate(BaseModel):
    display_name: str = Field(default="匿名學生", min_length=2, max_length=30)


class AnonymousIdentity(BaseModel):
    id: str = Field(default_factory=lambda: uuid4().hex)
    display_name: str
    access_token_hash: str
    account_id: str | None = None
    created_at: datetime = Field(default_factory=utc_now)


class AnonymousIdentitySession(BaseModel):
    id: str
    display_name: str
    access_token: str


class CommunityPostType(str, Enum):
    DISCUSSION = "discussion"
    QUESTION = "question"
    EXPERIENCE = "experience"


class CommunityPostCreate(BaseModel):
    board_id: str | None = Field(default=None, min_length=2, max_length=120)
    school_name: str | None = Field(default=None, min_length=2, max_length=200)
    post_type: CommunityPostType = CommunityPostType.DISCUSSION
    topic: CommunityTopic = CommunityTopic.APPLICATION
    country: str | None = Field(default=None, max_length=80)
    academic_year: str | None = Field(default=None, max_length=20)
    application_stage: str | None = Field(default=None, max_length=40)
    title: str = Field(min_length=4, max_length=120)
    body: str = Field(min_length=10, max_length=1600)
    identity_mode: CommunityIdentityMode = CommunityIdentityMode.ANONYMOUS

    @model_validator(mode="after")
    def require_board_reference(self) -> "CommunityPostCreate":
        if not (self.board_id or self.school_name):
            raise ValueError("必須指定社群看板。")
        return self


class CommunityPost(BaseModel):
    id: str = Field(default_factory=lambda: uuid4().hex)
    board_id: str | None = None
    board_kind: CommunityBoardKind | None = None
    school_name: str
    author_id: str
    display_name: str
    identity_mode: CommunityIdentityMode = CommunityIdentityMode.ANONYMOUS
    post_type: CommunityPostType = CommunityPostType.DISCUSSION
    topic: CommunityTopic = CommunityTopic.APPLICATION
    country: str | None = None
    academic_year: str | None = None
    application_stage: str | None = None
    title: str
    body: str
    status: ModerationStatus = ModerationStatus.APPROVED
    comment_count: int = 0
    viewer_can_delete: bool = False
    created_at: datetime = Field(default_factory=utc_now)


class CommunityPostCommentCreate(BaseModel):
    body: str = Field(min_length=2, max_length=800)
    parent_id: str | None = Field(default=None, min_length=1, max_length=128)
    identity_mode: CommunityIdentityMode = CommunityIdentityMode.ANONYMOUS


class CommunityPostComment(BaseModel):
    id: str = Field(default_factory=lambda: uuid4().hex)
    post_id: str
    parent_id: str | None = None
    deleted: bool = False
    author_id: str
    display_name: str
    identity_mode: CommunityIdentityMode = CommunityIdentityMode.ANONYMOUS
    body: str
    status: ModerationStatus = ModerationStatus.APPROVED
    viewer_can_delete: bool = False
    created_at: datetime = Field(default_factory=utc_now)


class CommunityPostThread(BaseModel):
    post: CommunityPost
    comments: list[CommunityPostComment] = Field(default_factory=list)


class CommunityReaction(BaseModel):
    account_id: str
    resource_type: Literal["post", "comment"]
    resource_id: str
    reaction: Literal["helpful", "thanks"]


class CommunityReactionUpdate(BaseModel):
    reaction: Literal["helpful", "thanks"] | None = None


class CommunityBookmark(BaseModel):
    account_id: str
    post_id: str


class CommunityBookmarkUpdate(BaseModel):
    saved: bool


class PublicChatMessageCreate(BaseModel):
    school_name: str = Field(min_length=2, max_length=200)
    body: str = Field(min_length=2, max_length=500)
    identity_mode: CommunityIdentityMode = CommunityIdentityMode.ANONYMOUS


class PublicChatMessage(BaseModel):
    id: str = Field(default_factory=lambda: uuid4().hex)
    school_name: str
    author_id: str
    display_name: str
    identity_mode: CommunityIdentityMode = CommunityIdentityMode.ANONYMOUS
    body: str
    status: ModerationStatus = ModerationStatus.APPROVED
    created_at: datetime = Field(default_factory=utc_now)


class ConversationStatus(str, Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    DECLINED = "declined"


class PrivateConversationCreate(BaseModel):
    school_name: str = Field(min_length=2, max_length=200)
    recipient_id: str = Field(min_length=8, max_length=64)
    initial_message: str = Field(min_length=5, max_length=500)


class PrivateConversation(BaseModel):
    id: str = Field(default_factory=lambda: uuid4().hex)
    school_name: str
    sender_id: str
    sender_name: str
    recipient_id: str
    recipient_name: str
    status: ConversationStatus = ConversationStatus.PENDING
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)


class PrivateMessageCreate(BaseModel):
    body: str = Field(min_length=2, max_length=1000)


class PrivateMessage(BaseModel):
    id: str = Field(default_factory=lambda: uuid4().hex)
    conversation_id: str
    author_id: str
    display_name: str
    body: str
    created_at: datetime = Field(default_factory=utc_now)


class CommunityBlockCreate(BaseModel):
    target_id: str = Field(min_length=8, max_length=64)


class CommunityBlock(BaseModel):
    id: str = Field(default_factory=lambda: uuid4().hex)
    owner_id: str
    target_id: str
    created_at: datetime = Field(default_factory=utc_now)


class CommunityReportCreate(BaseModel):
    resource_type: Literal["post", "comment", "chat", "message"]
    resource_id: str = Field(min_length=8, max_length=64)
    reason: str = Field(min_length=4, max_length=300)


class CommunityReportStatus(str, Enum):
    PENDING = "pending"
    RESOLVED = "resolved"
    DISMISSED = "dismissed"


class CommunityReportReviewRequest(BaseModel):
    status: Literal[CommunityReportStatus.RESOLVED, CommunityReportStatus.DISMISSED]
    note: str = Field(min_length=2, max_length=500)


class CommunityReport(BaseModel):
    id: str = Field(default_factory=lambda: uuid4().hex)
    reporter_id: str
    resource_type: str
    resource_id: str
    reason: str
    status: CommunityReportStatus = CommunityReportStatus.PENDING
    reviewed_by: str | None = None
    reviewed_at: datetime | None = None
    resolution_note: str | None = None
    retained_until: datetime | None = None
    created_at: datetime = Field(default_factory=utc_now)


class AuthProvider(str, Enum):
    EMAIL = "email"
    GOOGLE = "google"
    FACEBOOK = "facebook"
    APPLE = "apple"


class StudentVerificationMethod(str, Enum):
    ADMIN_APPROVAL = "admin_approval"
    STUDENT_CARD = "student_card"
    SCHOOL_EMAIL = "school_email"
    GOOGLE_WORKSPACE = "google_workspace"
    MICROSOFT_ENTRA = "microsoft_entra"
    SCHOOL_SSO = "school_sso"


class StudentVerificationProviderAvailability(str, Enum):
    AVAILABLE = "available"
    CONFIGURATION_REQUIRED = "configuration_required"
    SCHOOL_PARTNERSHIP_REQUIRED = "school_partnership_required"
    SUPPORTING_ONLY = "supporting_only"


class StudentVerificationProviderStatus(BaseModel):
    id: str = Field(pattern=r"^[a-z0-9][a-z0-9-]{2,80}$")
    school_name: str
    method: StudentVerificationMethod
    label: str
    enabled: bool = False
    availability: StudentVerificationProviderAvailability
    reason: str
    redirect_based: bool = False
    accepts_school_password: Literal[False] = False
    allowed_email_domains: list[str] = Field(default_factory=list)
    source_urls: list[str] = Field(default_factory=list)


class AccountProviderLink(BaseModel):
    provider: AuthProvider
    subject: str


class AccountRegister(BaseModel):
    email: str = Field(min_length=5, max_length=254)
    password: str = Field(min_length=8, max_length=128)
    display_name: str = Field(min_length=2, max_length=30)
    email_verification_token: str = Field(min_length=24, max_length=256)
    accept_terms: Literal[True]


class AccountLogin(BaseModel):
    email: str = Field(min_length=5, max_length=254)
    password: str = Field(min_length=8, max_length=128)


class EmailVerificationRequest(BaseModel):
    email: str = Field(min_length=5, max_length=254)


class EmailVerificationDispatch(BaseModel):
    email_hint: str
    expires_at: datetime
    resend_available_at: datetime
    development_code: str | None = None


class EmailVerificationConfirm(BaseModel):
    email: str = Field(min_length=5, max_length=254)
    code: str = Field(pattern=r"^\d{6}$")


class EmailVerificationConfirmation(BaseModel):
    verification_token: str
    expires_at: datetime
    account_verified: bool = False


class EmailVerificationChallenge(BaseModel):
    id: str = Field(default_factory=lambda: uuid4().hex)
    email_fingerprint: str = Field(min_length=64, max_length=64)
    code_hash: str = Field(min_length=64, max_length=64)
    confirmation_token_hash: str | None = Field(default=None, min_length=64, max_length=64)
    attempt_count: int = Field(default=0, ge=0, le=10)
    requested_at: datetime = Field(default_factory=utc_now)
    resend_available_at: datetime
    expires_at: datetime
    confirmed_at: datetime | None = None
    consumed_at: datetime | None = None


class StudentVerificationConfirm(BaseModel):
    verification_token: str = Field(min_length=24, max_length=256)


class AccountNotificationPreferences(BaseModel):
    deadline_reminder_days: list[int] = Field(
        default_factory=lambda: [30, 14, 7, 3, 1], max_length=10
    )
    web_enabled: bool = True
    email_enabled: bool = False
    push_enabled: bool = False
    content_updates_enabled: bool = True

    @model_validator(mode="after")
    def normalize_reminder_days(self) -> "AccountNotificationPreferences":
        self.deadline_reminder_days = sorted(
            {
                int(day)
                for day in self.deadline_reminder_days
                if 0 <= int(day) <= 90
            },
            reverse=True,
        )
        return self


class AccountNotification(BaseModel):
    id: str = Field(default_factory=lambda: uuid4().hex)
    account_id: str = Field(min_length=1, max_length=80)
    dedupe_key: str = Field(min_length=1, max_length=500)
    kind: Literal["deadline", "content_update", "catalogue_update"] = "deadline"
    channels: list[Literal["web", "email"]] = Field(default_factory=list, max_length=2)
    title: str = Field(min_length=1, max_length=180)
    body: str = Field(min_length=1, max_length=1000)
    action_url: str | None = Field(default=None, max_length=1000)
    source_key: str = Field(min_length=1, max_length=300)
    source_url: str | None = Field(default=None, max_length=1000)
    deadline_at: datetime | None = None
    reminder_days: int | None = Field(default=None, ge=0, le=90)
    scheduled_for: datetime = Field(default_factory=utc_now)
    read_at: datetime | None = None
    deleted_at: datetime | None = None
    created_at: datetime = Field(default_factory=utc_now)


class NotificationDelivery(BaseModel):
    id: str = Field(default_factory=lambda: uuid4().hex)
    notification_id: str = Field(min_length=1, max_length=80)
    account_id: str = Field(min_length=1, max_length=80)
    channel: Literal["email"] = "email"
    status: Literal["pending", "retrying", "sent", "failed", "cancelled"] = "pending"
    attempt_count: int = Field(default=0, ge=0, le=20)
    next_attempt_at: datetime = Field(default_factory=utc_now)
    sent_at: datetime | None = None
    last_error_code: str | None = Field(default=None, max_length=120)
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)


class NotificationCenterEnvelope(BaseModel):
    items: list[AccountNotification] = Field(default_factory=list)
    unread_count: int = 0


class NotificationRunResult(BaseModel):
    account_count: int = 0
    created_count: int = 0
    queued_email_count: int = 0
    sent_count: int = 0
    retry_count: int = 0
    failed_count: int = 0
    email_delivery_enabled: bool = False
    ran_at: datetime = Field(default_factory=utc_now)


class VaultDocumentCategory(str, Enum):
    APPLICATION_FORM = "application_form"
    GENERATED_PACKET = "generated_packet"
    PASSPORT = "passport"
    TRANSCRIPT = "transcript"
    STUDENT_ID = "student_id"
    FINANCIAL_PROOF = "financial_proof"
    RECOMMENDATION = "recommendation"
    STUDY_PLAN = "study_plan"
    OTHER = "other"


class VaultConsentPurpose(str, Enum):
    APPLICATION_PREPARATION = "application_preparation"
    CROSS_DEVICE_ACCESS = "cross_device_access"
    GENERATED_PACKET_BACKUP = "generated_packet_backup"


class VaultAuditAction(str, Enum):
    VERSION_STORED = "version_stored"
    DOWNLOAD_GRANTED = "download_granted"
    DOWNLOADED = "downloaded"
    VERSION_DELETED = "version_deleted"
    DOCUMENT_DELETED = "document_deleted"
    RETENTION_EXPIRED = "retention_expired"
    ORPHAN_REMOVED = "orphan_removed"


class VaultDocumentRecord(BaseModel):
    id: str = Field(default_factory=lambda: uuid4().hex)
    account_id: str = Field(min_length=1, max_length=80)
    label_ciphertext: str = Field(min_length=1)
    label_nonce: str = Field(min_length=1, max_length=80)
    category: VaultDocumentCategory
    latest_version: int = Field(default=1, ge=1)
    version_count: int = Field(default=1, ge=1)
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)


class VaultDocumentVersionRecord(BaseModel):
    id: str = Field(default_factory=lambda: uuid4().hex)
    document_id: str = Field(min_length=1, max_length=80)
    account_id: str = Field(min_length=1, max_length=80)
    version_number: int = Field(ge=1)
    file_name_ciphertext: str = Field(min_length=1)
    file_name_nonce: str = Field(min_length=1, max_length=80)
    media_type: str = Field(min_length=1, max_length=120)
    plaintext_size: int = Field(ge=1, le=20 * 1024 * 1024)
    plaintext_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    ciphertext_size: int = Field(ge=1)
    ciphertext_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    object_key: str = Field(min_length=1, max_length=500)
    encryption_algorithm: Literal["AES-256-GCM"] = "AES-256-GCM"
    wrapped_data_key: str = Field(min_length=1)
    wrap_nonce: str = Field(min_length=1, max_length=80)
    content_nonce: str = Field(min_length=1, max_length=80)
    consent_id: str = Field(min_length=1, max_length=80)
    retention_expires_at: datetime
    created_at: datetime = Field(default_factory=utc_now)


class VaultConsentRecord(BaseModel):
    id: str = Field(default_factory=lambda: uuid4().hex)
    account_id: str = Field(min_length=1, max_length=80)
    document_id: str = Field(min_length=1, max_length=80)
    version_id: str = Field(min_length=1, max_length=80)
    purpose: VaultConsentPurpose
    retention_days: int = Field(ge=1, le=365)
    terms_version: str = Field(default="2026-07-28", min_length=1, max_length=40)
    granted_at: datetime = Field(default_factory=utc_now)
    expires_at: datetime
    revoked_at: datetime | None = None


class VaultAuditRecord(BaseModel):
    id: str = Field(default_factory=lambda: uuid4().hex)
    subject_fingerprint: str = Field(pattern=r"^[0-9a-f]{32}$")
    document_id: str | None = Field(default=None, max_length=80)
    version_id: str | None = Field(default=None, max_length=80)
    action: VaultAuditAction
    created_at: datetime = Field(default_factory=utc_now)


class VaultVersionSummary(BaseModel):
    id: str
    version_number: int
    file_name: str
    media_type: str
    size_bytes: int
    sha256: str
    purpose: VaultConsentPurpose
    retention_days: int
    consented_at: datetime
    expires_at: datetime
    created_at: datetime


class VaultDocumentSummary(BaseModel):
    id: str
    label: str
    category: VaultDocumentCategory
    latest_version: int
    versions: list[VaultVersionSummary] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime


class VaultDocumentList(BaseModel):
    items: list[VaultDocumentSummary] = Field(default_factory=list)
    total_bytes: int = Field(default=0, ge=0)
    max_file_bytes: int = 20 * 1024 * 1024


class VaultDownloadGrant(BaseModel):
    download_url: str = "/account/vault/download"
    token: str
    expires_at: datetime


class VaultCleanupResult(BaseModel):
    expired_version_count: int = 0
    removed_document_count: int = 0
    orphan_object_count: int = 0
    ran_at: datetime = Field(default_factory=utc_now)


class AccountProfileUpdate(BaseModel):
    display_name: str | None = Field(default=None, min_length=2, max_length=30)
    avatar_url: str | None = Field(default=None, max_length=500)
    home_university: str | None = Field(default=None, max_length=80)
    target_countries: list[str] | None = Field(default=None, max_length=8)
    application_stage: str | None = Field(default=None, max_length=40)
    followed_boards: list[str] | None = Field(default=None, max_length=30)
    notification_preferences: AccountNotificationPreferences | None = None
    content_updates_seen_at: datetime | None = None


class AccountCalendarEvent(BaseModel):
    id: str = Field(min_length=1, max_length=180)
    title: str = Field(min_length=1, max_length=120)
    date: str = Field(pattern=r"^\d{4}-\d{2}-\d{2}$")
    category: str = Field(default="other", max_length=40)
    reminder_days: int = Field(default=7, ge=0, le=90)
    note: str = Field(default="", max_length=1000)
    source_url: str | None = Field(default=None, max_length=1000)
    origin: Literal["official", "personal"] = "personal"
    school_name: str | None = Field(default=None, min_length=2, max_length=200)
    preparation_days: int = Field(default=0, ge=0, le=90)
    status: Literal["todo", "preparing", "ready"] = "todo"
    effort_hours: float | None = Field(default=None, gt=0, le=1000)
    remaining_hours: float | None = Field(default=None, ge=0, le=1000)
    depends_on: list[str] = Field(default_factory=list, max_length=30)
    available_from: PlanningDate | None = None
    waiting_reason: str | None = Field(default=None, max_length=240)
    document_id: str | None = Field(default=None, max_length=180)
    generated_from_event_id: str | None = Field(
        default=None,
        min_length=1,
        max_length=180,
    )


class CalendarEventSyncRequest(BaseModel):
    events: list[AccountCalendarEvent] = Field(default_factory=list, max_length=500)


class CalendarSyncStatus(BaseModel):
    enabled: bool
    subscription_url: str | None = None
    webcal_url: str | None = None
    event_count: int = 0
    last_synced_at: datetime | None = None


class CalendarConflictKind(str, Enum):
    SAME_DAY = "same_day"
    TIGHT_WINDOW = "tight_window"


class CalendarConflictAnalysisRequest(BaseModel):
    events: list[AccountCalendarEvent] = Field(default_factory=list, max_length=500)


class CalendarConflictGroup(BaseModel):
    id: str = Field(pattern=r"^calendar-conflict-[0-9a-f]{16}$")
    kind: CalendarConflictKind
    start_date: str = Field(pattern=r"^\d{4}-\d{2}-\d{2}$")
    end_date: str = Field(pattern=r"^\d{4}-\d{2}-\d{2}$")
    day_gap: int = Field(ge=0, le=3)
    school_names: list[str] = Field(min_length=2, max_length=30)
    events: list[AccountCalendarEvent] = Field(min_length=2, max_length=500)
    resolution_hint: str


class CalendarConflictReport(BaseModel):
    analyzed_event_count: int = Field(default=0, ge=0)
    plan_count: int = Field(default=0, ge=0)
    conflict_count: int = Field(default=0, ge=0)
    conflicting_event_count: int = Field(default=0, ge=0)
    same_day_conflict_count: int = Field(default=0, ge=0)
    tight_window_conflict_count: int = Field(default=0, ge=0)
    groups: list[CalendarConflictGroup] = Field(default_factory=list)


class CalendarTaskUrgency(str, Enum):
    SCHEDULED = "scheduled"
    START_NOW = "start_now"
    DUE_SOON = "due_soon"
    OVERDUE = "overdue"
    COMPLETED = "completed"
    BLOCKED = "blocked"


class PlanningAvailability(BaseModel):
    model_config = ConfigDict(extra="forbid")

    weekly_hours: float = Field(default=6, ge=0.5, le=60)
    weekdays: list[int] = Field(default_factory=lambda: [1, 3, 6], min_length=1, max_length=7)
    horizon_days: int = Field(default=180, ge=1, le=365)

    @model_validator(mode="after")
    def validate_weekdays(self) -> "PlanningAvailability":
        if any(day < 1 or day > 7 for day in self.weekdays):
            raise ValueError("可準備星期必須介於 1 到 7。")
        self.weekdays = sorted(set(self.weekdays))
        return self


class CalendarTaskScheduleRequest(BaseModel):
    events: list[AccountCalendarEvent] = Field(default_factory=list, max_length=500)
    as_of: date | None = None
    availability: PlanningAvailability | None = None


class CalendarTaskScheduleItem(BaseModel):
    event_id: str
    title: str
    school_name: str | None = None
    deadline_date: date | None
    deadline_kind: Literal["official", "personal", "unspecified"] = "personal"
    suggested_start_date: date | None
    preparation_days: int = Field(ge=1, le=90)
    status: Literal["todo", "preparing", "ready"]
    urgency: CalendarTaskUrgency
    days_until_start: int
    days_until_deadline: int | None
    recommended_reminder_days: list[int] = Field(default_factory=list)
    reason: str
    effort_hours: float | None = None
    remaining_hours: float | None = None
    scheduled_hours: float = 0
    unscheduled_hours: float = 0
    suggested_finish_date: date | None = None
    dependency_ids: list[str] = Field(default_factory=list)
    document_id: str | None = None


class PlanningWorkSession(BaseModel):
    event_id: str
    date: PlanningDate
    hours: float = Field(gt=0)
    sequence: int = Field(ge=1)


class PlanningScheduleIssue(BaseModel):
    event_id: str
    code: Literal["invalid_date", "missing_deadline", "missing_dependency", "dependency_cycle", "waiting", "missing_effort", "suggested_effort", "deadline_passed", "capacity", "blocked_dependency", "outside_horizon", "confirm_completion"]
    detail: str
    blocking: bool = True


class CalendarTaskScheduleReport(BaseModel):
    as_of: date
    analyzed_event_count: int = Field(default=0, ge=0)
    incomplete_count: int = Field(default=0, ge=0)
    scheduled_count: int = Field(default=0, ge=0)
    start_now_count: int = Field(default=0, ge=0)
    due_soon_count: int = Field(default=0, ge=0)
    overdue_count: int = Field(default=0, ge=0)
    completed_count: int = Field(default=0, ge=0)
    items: list[CalendarTaskScheduleItem] = Field(default_factory=list)
    mode: Literal["preparation_window", "workload"] = "preparation_window"
    availability: PlanningAvailability | None = None
    work_sessions: list[PlanningWorkSession] = Field(default_factory=list)
    issues: list[PlanningScheduleIssue] = Field(default_factory=list)
    blocked_count: int = 0


class ApplicationPreparationTaskState(BaseModel):
    """Student settings only. Published instructions are recomputed separately."""
    model_config = ConfigDict(extra="forbid")

    status: Literal["todo", "preparing", "ready"] = "todo"
    effort_hours: float | None = Field(default=None, gt=0, le=1000)
    remaining_hours: float | None = Field(default=None, ge=0, le=1000)
    depends_on: list[str] | None = Field(default=None, max_length=30)
    available_from: PlanningDate | None = None
    personal_due_date: PlanningDate | None = None
    waiting_reason: str | None = Field(default=None, max_length=240)
    document_id: str | None = Field(default=None, max_length=180)
    document_target_school: str | None = Field(default=None, max_length=200)


class PreparationWorkItem(AccountCalendarEvent):
    date: str | None = Field(default=None, pattern=r"^\d{4}-\d{2}-\d{2}$")
    deadline_kind: Literal["official", "personal", "unspecified"] = "unspecified"
    # Position in the usual process; only breaks ties between undated tasks.
    process_order: int | None = Field(default=None, ge=0, le=100000)
    effort_is_suggested: bool = False


class ApplicationPlanScheduleRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    plan: PersonalApplicationPlanRequest
    task_settings: dict[str, ApplicationPreparationTaskState] = Field(default_factory=dict, max_length=500)
    personal_events: list[AccountCalendarEvent] = Field(default_factory=list, max_length=500)
    availability: PlanningAvailability
    as_of: date | None = None


class ApplicationPlanScheduleResult(BaseModel):
    plan: PersonalApplicationPlanResult
    schedule: CalendarTaskScheduleReport


class ProductReleaseMode(str, Enum):
    CLOSED_BETA = "closed_beta"
    PUBLIC = "public"


class ProductAccessTier(str, Enum):
    GUEST = "guest"
    FREE = "free"
    SUBSCRIPTION = "subscription"


class ProductFeature(str, Enum):
    OFFICIAL_APPLICATION_INFORMATION = "official_application_information"
    ELIGIBILITY_AND_REQUIREMENTS = "eligibility_and_requirements"
    BASIC_SEARCH_AND_COMPARE = "basic_search_and_compare"
    SINGLE_APPLICATION_PLAN = "single_application_plan"
    OFFICIAL_FORM_DOWNLOADS = "official_form_downloads"
    BASIC_DEADLINE_REMINDERS = "basic_deadline_reminders"
    COMMUNITY_ACCESS = "community_access"
    MULTIPLE_APPLICATION_PLANS = "multiple_application_plans"
    AI_SCHOOL_MATCHING = "ai_school_matching"
    PERSONALIZED_APPLICATION_ROUTE = "personalized_application_route"
    APPLICATION_DOCUMENT_GENERATION = "application_document_generation"
    DOCUMENT_COMPLETENESS_REVIEW = "document_completeness_review"
    DOCUMENT_REWRITE_AND_TRANSLATION = "document_rewrite_and_translation"
    SMART_REMINDERS = "smart_reminders"
    APPLICATION_PLAN_CONFLICTS = "application_plan_conflicts"
    EXTERNAL_CALENDAR_SYNC = "external_calendar_sync"
    ENCRYPTED_DOCUMENT_VAULT = "encrypted_document_vault"
    DOCUMENT_VERSION_HISTORY = "document_version_history"
    PRIORITY_SUPPORT = "priority_support"


class ProductEntitlementReason(str, Enum):
    PUBLIC = "public"
    FREE = "free"
    CLOSED_BETA = "closed_beta"
    SUBSCRIPTION = "subscription"
    LOGIN_REQUIRED = "login_required"
    UPGRADE_REQUIRED = "upgrade_required"


class ProductFeatureEntitlement(BaseModel):
    feature: ProductFeature
    required_tier: Literal["public", "free", "subscription"]
    enabled: bool
    requires_login: bool
    reason: ProductEntitlementReason


class ProductEntitlementSnapshot(BaseModel):
    release_mode: ProductReleaseMode
    account_tier: ProductAccessTier
    effective_tier: ProductAccessTier
    billing_enabled: bool = False
    features: list[ProductFeatureEntitlement] = Field(default_factory=list)


class AccountApplicationSelection(BaseModel):
    selected: bool = False
    copies: int = Field(default=1, ge=1, le=10)
    status: Literal[
        "draft",
        "ready_to_print",
        "pending_signature",
        "pending_department_stamp",
        "pending_submission",
        "completed",
    ] = "draft"
    reviewed_version: str | None = Field(default=None, max_length=80)
    reviewed_content_sha256: str | None = Field(
        default=None,
        pattern=r"^[0-9a-f]{64}$",
    )
    reviewed_at: datetime | None = None


class SubmissionProofMetadata(BaseModel):
    model_config = ConfigDict(extra="forbid")

    kind: Literal[
        "tracking",
        "submission_receipt",
        "confirmation_email",
        "in_person_receipt",
        "other",
    ]
    reference: str | None = Field(default=None, max_length=200)
    file_name: str | None = Field(default=None, max_length=255)
    content_type: str | None = Field(default=None, max_length=100)
    source: Literal["student_reported"] = "student_reported"
    original_file_stored: Literal[False] = False
    recorded_at: datetime = Field(default_factory=utc_now)


class AccountSubmissionProgress(BaseModel):
    title: str = Field(min_length=1, max_length=240)
    method: ApplicationSubmissionMethod
    status: Literal[
        "not_started",
        "preparing",
        "submitted",
        "receipt_confirmed",
        "completed",
    ] = "not_started"
    responsible_unit: str | None = Field(default=None, max_length=240)
    send_by_at: datetime | None = None
    arrival_deadline_at: datetime | None = None
    proof_metadata: SubmissionProofMetadata | None = None
    recorded_by: Literal["student"] = "student"
    platform_submitted: Literal[False] = False
    note: str | None = Field(default=None, max_length=1000)
    started_at: datetime | None = None
    submitted_at: datetime | None = None
    receipt_confirmed_at: datetime | None = None
    completed_at: datetime | None = None
    updated_at: datetime = Field(default_factory=utc_now)


class SubmissionProgressTransitionRequest(BaseModel):
    home_school: str = Field(min_length=2, max_length=80)
    progress_key: str = Field(min_length=3, max_length=240)
    action: Literal["start", "submit", "confirm_receipt", "complete", "revert"]
    method: ApplicationSubmissionMethod
    title: str = Field(min_length=1, max_length=240)
    responsible_unit: str | None = Field(default=None, max_length=240)
    send_by_at: datetime | None = None
    arrival_deadline_at: datetime | None = None
    proof_metadata: SubmissionProofMetadata | None = None
    note: str | None = Field(default=None, max_length=1000)


class AccountBudgetPlan(BaseModel):
    model_config = ConfigDict(extra="forbid")

    currency: str = Field(default="TWD", pattern=r"^[A-Z]{3}$")
    months: int = Field(default=5, ge=1, le=24)
    housing: float = Field(default=0, ge=0, le=1_000_000_000)
    food: float = Field(default=0, ge=0, le=1_000_000_000)
    transport: float = Field(default=0, ge=0, le=1_000_000_000)
    other: float = Field(default=0, ge=0, le=1_000_000_000)
    one_time: float = Field(default=0, ge=0, le=1_000_000_000)
    scholarship: float = Field(default=0, ge=0, le=1_000_000_000)
    saved_at: datetime


class AccountSelectionProfile(BaseModel):
    """Student supplied conditions, separate from admission or source verification."""

    model_config = ConfigDict(extra="forbid")

    college: str = Field(default="", max_length=120)
    department: str = Field(default="", max_length=120)
    current_year: str = Field(default="", max_length=40)
    degree_level: str = Field(default="", max_length=80)
    academic_score: float | None = Field(default=None, ge=0, le=100)
    academic_gpa: float | None = Field(default=None, ge=0, le=4.3)
    class_rank_percent: float | None = Field(default=None, gt=0, le=100)
    language_test: Literal["toeic", "ielts", "toefl", "toefl_new", "duolingo", "other"] | None = None
    language_score: float | None = Field(default=None, ge=0, le=1000)
    jlpt_level: Literal['N1', 'N2', 'N3', 'N4', 'N5'] | None = None
    target_term: str = Field(default="", max_length=40)
    preferred_country: str = Field(default="", max_length=80)
    monthly_budget: float | None = Field(default=None, ge=0, le=10_000_000)
    needs_scholarship: bool = False
    academic_year: str = Field(default="", max_length=20)
    application_round: str = Field(default="", max_length=80)
    preferred_teaching_language: TeachingLanguage | None = None
    course_interests: str = Field(default="", max_length=120)

class AccountSelectionConditions(BaseModel):
    model_config = ConfigDict(extra="forbid")

    # Absent wrapper denotes legacy data; a wrapper with null profile is an explicit clear.
    profile: AccountSelectionProfile | None = None


class AccountApplicationWorkspace(BaseModel):
    model_config = ConfigDict(extra="forbid")

    home_school: str = Field(min_length=2, max_length=80)
    revision: int = Field(default=0, ge=0)
    favorite_schools: list[str] = Field(default_factory=list, max_length=500)
    discovery: DiscoveryWorkspace = Field(default_factory=DiscoveryWorkspace)
    application_schools: list[str] = Field(default_factory=list, max_length=30)
    application_progress: dict[str, dict[str, bool]] = Field(default_factory=dict, max_length=30)
    document_readiness: dict[str, Literal["todo", "preparing", "ready"]] = Field(
        default_factory=dict,
        max_length=500,
    )
    application_context: ApplicationCenterContext
    selection_conditions: AccountSelectionConditions | None = None
    application_selections: dict[str, AccountApplicationSelection] = Field(
        default_factory=dict,
        max_length=100,
    )
    submission_progress: dict[str, AccountSubmissionProgress] = Field(
        default_factory=dict,
        max_length=500,
    )
    budget_plans: dict[str, AccountBudgetPlan] = Field(default_factory=dict, max_length=500)
    deadline_events: list[AccountCalendarEvent] = Field(default_factory=list, max_length=500)
    planning_availability: PlanningAvailability | None = None
    preparation_tasks: dict[str, ApplicationPreparationTaskState] = Field(default_factory=dict, max_length=500)
    updated_at: datetime = Field(default_factory=utc_now)

    @model_validator(mode="after")
    def normalize_workspace(self) -> AccountApplicationWorkspace:
        self.favorite_schools = list(
            dict.fromkeys(value.strip() for value in self.favorite_schools if value.strip())
        )
        self.application_schools = list(
            dict.fromkeys(value.strip() for value in self.application_schools if value.strip())
        )
        self.application_progress = {
            school.strip(): {
                step.strip(): bool(completed)
                for step, completed in steps.items()
                if step.strip()
            }
            for school, steps in self.application_progress.items()
            if school.strip()
        }
        self.document_readiness = {
            document_id.strip(): status
            for document_id, status in self.document_readiness.items()
            if document_id.strip()
        }
        self.application_selections = {
            template_id.strip(): selection
            for template_id, selection in self.application_selections.items()
            if template_id.strip()
        }
        self.submission_progress = {
            progress_key.strip(): progress
            for progress_key, progress in self.submission_progress.items()
            if progress_key.strip()
        }
        self.budget_plans = {
            school_name.strip(): plan
            for school_name, plan in self.budget_plans.items()
            if school_name.strip()
        }
        return self


class AccountApplicationWorkspaceEnvelope(BaseModel):
    exists: bool
    workspace: AccountApplicationWorkspace


class UserAccount(BaseModel):
    id: str = Field(default_factory=lambda: uuid4().hex)
    email: str | None = None
    password_hash: str | None = None
    display_name: str
    avatar_url: str | None = None
    home_university: str = "長庚大學"
    # When the school was last picked; the school cannot be changed again for SCHOOL_CHANGE_LOCK after that.
    home_university_changed_at: datetime | None = None
    target_countries: list[str] = Field(default_factory=list)
    application_stage: str = "exploring"
    followed_boards: list[str] = Field(default_factory=list)
    notification_preferences: AccountNotificationPreferences = Field(
        default_factory=AccountNotificationPreferences
    )
    content_updates_seen_at: datetime | None = None
    community_suspended_until: datetime | None = None
    email_verified: bool = False
    school_email_verified: bool = False
    student_status_verified: bool = False
    verified_university: str | None = None
    verified_department: str | None = None
    student_verification_method: StudentVerificationMethod | None = None
    student_verified_at: datetime | None = None
    provider_links: list[AccountProviderLink] = Field(default_factory=list)
    calendar_feed_token: str | None = None
    calendar_events: list[AccountCalendarEvent] = Field(default_factory=list)
    calendar_last_synced_at: datetime | None = None
    product_tier: ProductAccessTier = ProductAccessTier.FREE
    application_workspaces: list[AccountApplicationWorkspace] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)


class AccountProfile(BaseModel):
    is_platform_admin: bool = False
    catalog_home_university: str | None = None
    # Why catalog_home_university is that school: proved by student verification, inferred
    # from a provider-verified school mail domain, or simply chosen by the account holder.
    school_basis: Literal["student_verified", "school_email", "self_declared"] | None = None
    id: str
    email: str | None = None
    display_name: str
    avatar_url: str | None = None
    home_university: str
    # Until when the school cannot be changed; None when it can be changed now.
    school_change_locked_until: datetime | None = None
    target_countries: list[str] = Field(default_factory=list)
    application_stage: str
    followed_boards: list[str] = Field(default_factory=list)
    notification_preferences: AccountNotificationPreferences = Field(
        default_factory=AccountNotificationPreferences
    )
    content_updates_seen_at: datetime | None = None
    email_verified: bool = False
    school_email_verified: bool
    student_status_verified: bool = False
    verified_university: str | None = None
    verified_department: str | None = None
    student_verification_method: StudentVerificationMethod | None = None
    student_verified_at: datetime | None = None
    product_tier: ProductAccessTier = ProductAccessTier.FREE
    providers: list[AuthProvider] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime


class ContentAdminSession(BaseModel):
    id: str
    email: str
    display_name: str
    is_content_admin: Literal[True] = True


class AccountSessionRecord(BaseModel):
    id: str = Field(default_factory=lambda: uuid4().hex)
    account_id: str
    token_hash: str
    expires_at: datetime
    created_at: datetime = Field(default_factory=utc_now)


class AccountSession(BaseModel):
    access_token: str
    expires_at: datetime
    profile: AccountProfile


class AuthProviderStatus(BaseModel):
    provider: AuthProvider
    enabled: bool
    label: str


class StudentVerificationResult(BaseModel):
    verification_token: str
    school_name: str
    department_name: str | None = None
    verification_method: StudentVerificationMethod = StudentVerificationMethod.STUDENT_CARD
    checks: list[str] = Field(default_factory=list)
    expires_at: datetime
    expires_in_minutes: int = 15
    images_retained: Literal[False] = False
    ocr_text_retained: Literal[False] = False
    student_number_retained: Literal[False] = False


class ExperienceSubmissionCreate(BaseModel):
    school_name: str = Field(min_length=2, max_length=200)
    home_university: str = Field(default="長庚大學", min_length=2, max_length=80)
    title: str = Field(min_length=4, max_length=120)
    summary: str = Field(min_length=20, max_length=2000)
    exchange_year: str = Field(min_length=4, max_length=20)
    themes: list[str] = Field(default_factory=list, max_length=8)
    source_url: str | None = Field(default=None, max_length=500)
    display_name: str | None = Field(default=None, max_length=50)
    identity_mode: CommunityIdentityMode = CommunityIdentityMode.ANONYMOUS
    consent_to_publish: Literal[True]


class ExperienceSubmission(BaseModel):
    id: str = Field(default_factory=lambda: uuid4().hex)
    author_id: str | None = None
    school_name: str
    home_university: str
    title: str
    summary: str
    exchange_year: str
    themes: list[str] = Field(default_factory=list)
    source_url: str | None = None
    display_name: str = "匿名投稿者"
    identity_mode: CommunityIdentityMode = CommunityIdentityMode.ANONYMOUS
    status: ModerationStatus = ModerationStatus.PENDING
    created_at: datetime = Field(default_factory=utc_now)


JsonDict = dict[str, Any]
