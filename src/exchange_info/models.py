from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Literal
from uuid import uuid4

from pydantic import BaseModel, Field


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


class ApplicationFormField(BaseModel):
    id: str = Field(pattern=r"^[a-z][a-z0-9_]*$")
    label: str
    field_type: ApplicationFieldType = ApplicationFieldType.TEXT
    required: bool = False
    reusable_profile_key: str | None = None
    placeholder: str | None = None
    help_text: str | None = None
    options: list[str] = Field(default_factory=list)
    sensitive: bool = False
    max_length: int | None = Field(default=None, ge=1, le=12000)
    min_files: int = Field(default=0, ge=0, le=12)
    max_files: int = Field(default=6, ge=1, le=12)


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
    source_url: str
    source_checked_at: datetime
    version: str


class ApplicationCenterContext(BaseModel):
    school_name: str = "長庚大學"
    target_school: str | None = Field(default=None, max_length=200)
    target_country: str | None = Field(default=None, max_length=80)
    program_type: Literal["exchange", "dual_degree", "internship", "short_term_credit"] = "exchange"
    academic_year: str | None = Field(default=None, max_length=20)
    semester: str | None = Field(default=None, max_length=30)
    flags: list[str] = Field(default_factory=list, max_length=20)


class ApplicationDocumentSelection(BaseModel):
    template_id: str
    copies: int = Field(default=1, ge=1, le=10)


class ApplicationPacketRequest(BaseModel):
    context: ApplicationCenterContext
    profile: dict[str, Any] = Field(default_factory=dict)
    answers: dict[str, dict[str, Any]] = Field(default_factory=dict)
    selections: list[ApplicationDocumentSelection] = Field(default_factory=list, max_length=30)


class ApplicationPacketManifestItem(BaseModel):
    template_id: str
    title: str
    copies: int
    destinations: list[str] = Field(default_factory=list)
    signatures: list[str] = Field(default_factory=list)
    stamps: list[str] = Field(default_factory=list)
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
    hero_image: str | None = None
    official_url: str | None = None
    supported: bool = True
    partner_count: int = 0
    coverage_note: str


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


class PartnerUniversity(BaseModel):
    program_type: str
    availability_status: Literal["open", "agreement_only"] = "open"
    availability_note: str | None = None
    agreement_type: str | None = None
    agreement_level: str | None = None
    country: str | None = None
    school_name: str
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


class ApplicationWorkflowSource(BaseModel):
    title: str
    source_url: str
    role: ApplicationSourceRole
    checked_at: datetime = Field(default_factory=utc_now)


class ApplicationStep(BaseModel):
    order: int = Field(ge=1)
    phase: str
    title: str
    responsible_party: str
    timing: str | None = None
    summary: str
    details: list[str] = Field(default_factory=list)
    required_documents: list[str] = Field(default_factory=list)
    action_url: str | None = None
    source_urls: list[str] = Field(default_factory=list)
    needs_confirmation: bool = False


class UniversityApplicationWorkflow(BaseModel):
    home_university: str = "長庚大學"
    school_name: str
    partner_website: str | None = None
    country: str | None = None
    program_type: str | None = None
    steps: list[ApplicationStep] = Field(default_factory=list)
    sources: list[ApplicationWorkflowSource] = Field(default_factory=list)
    last_checked: datetime | None = None
    coverage_status: str = "not_collected"
    coverage_note: str = "尚未查核合作校官方申請流程。"
    disclaimer: str = "截止日與申請方式可能調整；送件前請再核對母校國際處、合作校通知信與官方申請頁。"


class StudentDashboard(BaseModel):
    school_name: str = "長庚大學"
    last_checked: datetime | None = None
    academic_score_minimum: float | None = None
    academic_score_rule: str | None = None
    language_score_minimums: dict[str, float] = Field(default_factory=dict)
    application_periods: list[StudentInfoItem] = Field(default_factory=list)
    program_overview: list[StudentInfoItem] = Field(default_factory=list)
    eligibility: list[StudentInfoItem] = Field(default_factory=list)
    language_requirements: list[StudentInfoItem] = Field(default_factory=list)
    required_documents: list[StudentInfoItem] = Field(default_factory=list)
    scholarship_info: list[StudentInfoItem] = Field(default_factory=list)
    document_explanations: list[RuleExplanation] = Field(default_factory=list)
    rule_explanations: list[RuleExplanation] = Field(default_factory=list)
    partner_universities: list[PartnerUniversity] = Field(default_factory=list)
    sources: list[SourceReference] = Field(default_factory=list)


class AdvisorProfile(BaseModel):
    school_name: str = "長庚大學"
    college: str | None = Field(default=None, max_length=120)
    department: str | None = Field(default=None, max_length=120)
    current_year: str | None = Field(default=None, max_length=40)
    degree_level: str | None = Field(default=None, max_length=80)
    academic_score: float | None = Field(default=None, ge=0, le=100)
    language_test: Literal["toeic", "ielts", "toefl", "duolingo", "other"] | None = None
    language_score: float | None = Field(default=None, ge=0, le=1000)
    target_term: str | None = Field(default=None, max_length=40)
    preferred_country: str | None = Field(default=None, max_length=80)
    monthly_budget: float | None = Field(default=None, ge=0, le=10_000_000)
    needs_scholarship: bool = False
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
    reasons: list[str] = Field(default_factory=list)
    gaps: list[str] = Field(default_factory=list)
    source_urls: list[str] = Field(default_factory=list)
    image_url: str | None = None


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


class ModerationStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    HIDDEN = "hidden"


class CommunityQuestionCreate(BaseModel):
    school_name: str = Field(min_length=2, max_length=200)
    home_university: str = Field(default="長庚大學", min_length=2, max_length=80)
    topic: CommunityTopic
    title: str = Field(min_length=4, max_length=120)
    body: str = Field(min_length=10, max_length=1000)
    display_name: str = Field(default="匿名學生", min_length=2, max_length=30)
    accept_rules: Literal[True]


class CommunityQuestion(BaseModel):
    id: str = Field(default_factory=lambda: uuid4().hex)
    school_name: str
    home_university: str
    topic: CommunityTopic
    title: str
    body: str
    display_name: str = "匿名學生"
    status: ModerationStatus = ModerationStatus.PENDING
    answer_count: int = 0
    created_at: datetime = Field(default_factory=utc_now)


class CommunityAnswerCreate(BaseModel):
    body: str = Field(min_length=10, max_length=1500)
    display_name: str = Field(default="匿名學長姐", min_length=2, max_length=30)
    exchange_year: str | None = Field(default=None, max_length=20)
    accept_rules: Literal[True]


class CommunityAnswer(BaseModel):
    id: str = Field(default_factory=lambda: uuid4().hex)
    question_id: str
    body: str
    display_name: str = "匿名學長姐"
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
    school_name: str = Field(min_length=2, max_length=200)
    post_type: CommunityPostType = CommunityPostType.DISCUSSION
    topic: CommunityTopic = CommunityTopic.APPLICATION
    country: str | None = Field(default=None, max_length=80)
    academic_year: str | None = Field(default=None, max_length=20)
    application_stage: str | None = Field(default=None, max_length=40)
    title: str = Field(min_length=4, max_length=120)
    body: str = Field(min_length=10, max_length=1600)


class CommunityPost(BaseModel):
    id: str = Field(default_factory=lambda: uuid4().hex)
    school_name: str
    author_id: str
    display_name: str
    post_type: CommunityPostType = CommunityPostType.DISCUSSION
    topic: CommunityTopic = CommunityTopic.APPLICATION
    country: str | None = None
    academic_year: str | None = None
    application_stage: str | None = None
    title: str
    body: str
    status: ModerationStatus = ModerationStatus.APPROVED
    comment_count: int = 0
    created_at: datetime = Field(default_factory=utc_now)


class CommunityPostCommentCreate(BaseModel):
    body: str = Field(min_length=2, max_length=800)


class CommunityPostComment(BaseModel):
    id: str = Field(default_factory=lambda: uuid4().hex)
    post_id: str
    author_id: str
    display_name: str
    body: str
    status: ModerationStatus = ModerationStatus.APPROVED
    created_at: datetime = Field(default_factory=utc_now)


class CommunityPostThread(BaseModel):
    post: CommunityPost
    comments: list[CommunityPostComment] = Field(default_factory=list)


class PublicChatMessageCreate(BaseModel):
    school_name: str = Field(min_length=2, max_length=200)
    body: str = Field(min_length=2, max_length=500)


class PublicChatMessage(BaseModel):
    id: str = Field(default_factory=lambda: uuid4().hex)
    school_name: str
    author_id: str
    display_name: str
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


class CommunityReport(BaseModel):
    id: str = Field(default_factory=lambda: uuid4().hex)
    reporter_id: str
    resource_type: str
    resource_id: str
    reason: str
    created_at: datetime = Field(default_factory=utc_now)


class AuthProvider(str, Enum):
    EMAIL = "email"
    GOOGLE = "google"
    FACEBOOK = "facebook"
    APPLE = "apple"


class AccountProviderLink(BaseModel):
    provider: AuthProvider
    subject: str


class AccountRegister(BaseModel):
    email: str = Field(min_length=5, max_length=254)
    password: str = Field(min_length=8, max_length=128)
    display_name: str = Field(min_length=2, max_length=30)
    student_verification_token: str = Field(min_length=24, max_length=256)
    accept_terms: Literal[True]


class AccountLogin(BaseModel):
    email: str = Field(min_length=5, max_length=254)
    password: str = Field(min_length=8, max_length=128)


class AccountProfileUpdate(BaseModel):
    display_name: str | None = Field(default=None, min_length=2, max_length=30)
    avatar_url: str | None = Field(default=None, max_length=500)
    home_university: str | None = Field(default=None, max_length=80)
    target_countries: list[str] | None = Field(default=None, max_length=8)
    application_stage: str | None = Field(default=None, max_length=40)
    followed_boards: list[str] | None = Field(default=None, max_length=30)


class AccountCalendarEvent(BaseModel):
    id: str = Field(min_length=1, max_length=180)
    title: str = Field(min_length=1, max_length=120)
    date: str = Field(pattern=r"^\d{4}-\d{2}-\d{2}$")
    category: str = Field(default="other", max_length=40)
    reminder_days: int = Field(default=7, ge=0, le=90)
    note: str = Field(default="", max_length=1000)
    source_url: str | None = Field(default=None, max_length=1000)
    origin: Literal["official", "personal"] = "personal"


class CalendarEventSyncRequest(BaseModel):
    events: list[AccountCalendarEvent] = Field(default_factory=list, max_length=500)


class CalendarSyncStatus(BaseModel):
    enabled: bool
    subscription_url: str | None = None
    webcal_url: str | None = None
    event_count: int = 0
    last_synced_at: datetime | None = None


class UserAccount(BaseModel):
    id: str = Field(default_factory=lambda: uuid4().hex)
    email: str | None = None
    password_hash: str | None = None
    display_name: str
    avatar_url: str | None = None
    home_university: str = "長庚大學"
    target_countries: list[str] = Field(default_factory=list)
    application_stage: str = "exploring"
    followed_boards: list[str] = Field(default_factory=list)
    school_email_verified: bool = False
    student_status_verified: bool = False
    verified_university: str | None = None
    student_verified_at: datetime | None = None
    provider_links: list[AccountProviderLink] = Field(default_factory=list)
    calendar_feed_token: str | None = None
    calendar_events: list[AccountCalendarEvent] = Field(default_factory=list)
    calendar_last_synced_at: datetime | None = None
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)


class AccountProfile(BaseModel):
    id: str
    email: str | None = None
    display_name: str
    avatar_url: str | None = None
    home_university: str
    target_countries: list[str] = Field(default_factory=list)
    application_stage: str
    followed_boards: list[str] = Field(default_factory=list)
    school_email_verified: bool
    student_status_verified: bool = False
    verified_university: str | None = None
    student_verified_at: datetime | None = None
    providers: list[AuthProvider] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime


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
    checks: list[str] = Field(default_factory=list)
    expires_at: datetime
    expires_in_minutes: int = 15
    images_retained: Literal[False] = False


class ExperienceSubmissionCreate(BaseModel):
    school_name: str = Field(min_length=2, max_length=200)
    home_university: str = Field(default="長庚大學", min_length=2, max_length=80)
    title: str = Field(min_length=4, max_length=120)
    summary: str = Field(min_length=20, max_length=2000)
    exchange_year: str = Field(min_length=4, max_length=20)
    themes: list[str] = Field(default_factory=list, max_length=8)
    source_url: str | None = Field(default=None, max_length=500)
    display_name: str = Field(default="匿名投稿者", min_length=2, max_length=30)
    consent_to_publish: Literal[True]


class ExperienceSubmission(BaseModel):
    id: str = Field(default_factory=lambda: uuid4().hex)
    school_name: str
    home_university: str
    title: str
    summary: str
    exchange_year: str
    themes: list[str] = Field(default_factory=list)
    source_url: str | None = None
    display_name: str = "匿名投稿者"
    status: ModerationStatus = ModerationStatus.PENDING
    created_at: datetime = Field(default_factory=utc_now)


JsonDict = dict[str, Any]
