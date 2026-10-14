"""Core data models, scope keys, and value contracts for Uniway maintenance (Spec Sections 2, 4, 5, 8)."""

from __future__ import annotations

import hashlib
import json
import re
from datetime import date, datetime, timezone
from enum import Enum
from typing import Any, Literal
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field, model_validator


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def canonical_json_hash(payload: Any) -> str:
    serialized = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


class ScopeMode(str, Enum):
    ALL = "all"
    EXPLICIT = "explicit"
    UNSPECIFIED = "unspecified"
    NOT_APPLICABLE = "not_applicable"


class ScopeDimension(str, Enum):
    CAMPUS = "campus"
    ACADEMIC_UNIT = "academic_unit"
    DEGREE_LEVEL = "degree_level"


class ValueState(str, Enum):
    KNOWN = "known"
    NOT_STATED = "not_stated"
    NOT_APPLICABLE = "not_applicable"
    CONFLICTING = "conflicting"
    UNVERIFIED = "unverified"
    LEGACY_UNVERIFIED = "legacy_unverified"


class QuotaUnit(str, Enum):
    PERSONS = "persons"
    ACADEMIC_YEAR_UNIT = "academic_year_unit"
    SEMESTER_UNIT = "semester_unit"
    POOL_TOTAL = "pool_total"
    UNSPECIFIED_UNIT = "unspecified_unit"


class DeadlineType(str, Enum):
    HOME_INTERNAL = "home_internal"
    NOMINATION = "nomination"
    PARTNER_APPLICATION = "partner_application"


class SourceHealthStatus(str, Enum):
    HEALTHY = "healthy"
    TEMPORARY_ERROR = "temporary_error"
    BLOCKED = "blocked"
    MISSING = "missing"


class DataFreshnessStatus(str, Enum):
    CURRENT = "current"
    STALE = "stale"
    YEAR_UNVERIFIED = "year_unverified"
    SUPERSEDED = "superseded"
    LEGACY_UNVERIFIED = "legacy_unverified"


class ReviewStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    PARTIALLY_APPROVED = "partially_approved"
    REJECTED = "rejected"
    DEFERRED = "deferred"
    CONFLICTING = "conflicting"
    PUBLISHED = "published"
    SUPERSEDED = "superseded"


class OfferingLifecycleStatus(str, Enum):
    ANNOUNCED = "announced"
    OPEN = "open"
    CLOSED = "closed"
    WITHDRAWN = "withdrawn"
    AGREEMENT_ONLY = "agreement_only"
    UNKNOWN = "unknown"


class RiskLevel(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class ChangeOrigin(str, Enum):
    SOURCE_CHANGE = "source_change"
    PARSER_CHANGE = "parser_change"
    CONTEXT_CHANGE = "context_change"
    MANUAL_CORRECTION = "manual_correction"
    UNCHANGED = "unchanged"


class VerificationOutcome(str, Enum):
    PASS = "pass"
    FAIL = "fail"
    NEEDS_REVIEW = "needs_review"


HIGH_RISK_FIELDS = frozenset(
    {
        "quota",
        "home_deadline",
        "nomination_deadline",
        "partner_deadline",
        "home_eligibility",
        "host_eligibility",
        "home_language_requirement",
        "host_language_requirement",
        "tuition_fee",
        "lifecycle_status",
        "academic_year",
        "scope",
    }
)

MEDIUM_RISK_FIELDS = frozenset(
    {
        "experience_summary",
        "personal_expense",
        "housing_info",
        "course_restrictions",
    }
)


class ScopeEntry(BaseModel):
    model_config = ConfigDict(extra="forbid")

    dimension: ScopeDimension
    mode: ScopeMode
    target_ids: tuple[str, ...] = ()
    target_labels: tuple[str, ...] = ()

    @model_validator(mode="after")
    def validate_scope_entry(self) -> "ScopeEntry":
        if self.mode == ScopeMode.EXPLICIT:
            if not self.target_ids:
                raise ValueError(f"{self.dimension.value} explicit scope requires canonical target_ids")
            sorted_pairs = sorted(
                zip(self.target_ids, self.target_labels or self.target_ids),
                key=lambda item: item[0],
            )
            self.target_ids = tuple(item[0].strip() for item in sorted_pairs if item[0].strip())
            self.target_labels = tuple(item[1].strip() for item in sorted_pairs if item[0].strip())
            if not self.target_ids:
                raise ValueError(f"{self.dimension.value} explicit scope target_ids cannot be blank")
        else:
            if self.target_ids or self.target_labels:
                raise ValueError(f"{self.dimension.value} with mode={self.mode.value} must not carry explicit target_ids")
        return self


def build_scope_key(
    *,
    home_id: str,
    host_id: str,
    program_id: str,
    cycle_id: str,
    campus_scope: ScopeEntry,
    academic_unit_scope: ScopeEntry,
    degree_level_scope: ScopeEntry,
) -> str:
    """Build deterministic scope_key from canonical IDs only (Spec Section 2.2)."""
    for label, val in (
        ("home_id", home_id),
        ("host_id", host_id),
        ("program_id", program_id),
        ("cycle_id", cycle_id),
    ):
        if not val or not val.strip():
            raise ValueError(f"{label} is required for scope_key")

    def _fmt(entry: ScopeEntry) -> str:
        if entry.mode == ScopeMode.EXPLICIT:
            return f"{entry.dimension.value}:explicit:{','.join(sorted(set(entry.target_ids)))}"
        return f"{entry.dimension.value}:{entry.mode.value}"

    canonical_parts = [
        f"home:{home_id.strip().lower()}",
        f"host:{host_id.strip().lower()}",
        f"program:{program_id.strip().lower()}",
        f"cycle:{cycle_id.strip().lower()}",
        _fmt(campus_scope),
        _fmt(academic_unit_scope),
        _fmt(degree_level_scope),
    ]
    digest = hashlib.sha256("|".join(canonical_parts).encode("utf-8")).hexdigest()[:32]
    return f"off_{home_id.strip().lower()}_{digest}"


class CycleSpec(BaseModel):
    """Application cycle preserving original label and explicit-only Minguo conversion (Spec 2.2)."""

    model_config = ConfigDict(extra="forbid")

    id: str
    program_id: str
    cycle_label_original: str
    application_year: int | None = None
    target_year_start: int | None = None
    target_year_end: int | None = None
    term_scope: Literal["fall", "spring", "full_year", "both_semesters", "summer", "unspecified"] = "unspecified"
    conversion_rule: str | None = None
    year_verified: bool = False

    @classmethod
    def from_explicit_label(cls, *, program_id: str, label: str | None) -> "CycleSpec":
        raw = (label or "").strip()
        if not raw or raw in {"未註明", "待確認", "unknown", "unspecified"}:
            cid = f"{program_id}_cycle_unverified"
            return cls(
                id=cid,
                program_id=program_id,
                cycle_label_original=raw or "未註明",
                term_scope="unspecified",
                year_verified=False,
            )

        term: Literal["fall", "spring", "full_year", "both_semesters", "summer", "unspecified"] = "unspecified"
        if any(tok in raw for tok in ("第一學期", "上學期", "秋季", "Fall", "Autumn", "-1")):
            term = "fall"
        elif any(tok in raw for tok in ("第二學期", "下學期", "春季", "Spring", "-2")):
            term = "spring"
        elif any(tok in raw for tok in ("全學年", "一學年", "Full Year")):
            term = "full_year"

        # Explicit Minguo academic year (e.g., 115, 116學年度, 116-1)
        minguo_match = re.search(r"(?<!\d)(11[0-9]|12[0-9])\s*(?:學年度|學年|-[12])?", raw)
        western_range = re.search(r"(202[0-9])\s*[/\-~～]\s*(?:20)?(2[0-9])", raw)
        western_single = re.search(r"(202[0-9])\s*(?:春季|秋季|學年|Spring|Fall)?", raw)

        if western_range:
            y_start = int(western_range.group(1))
            y_end = 2000 + int(western_range.group(2))
            cid = f"{program_id}_{y_start}_{y_end}_{term}"
            return cls(
                id=cid,
                program_id=program_id,
                cycle_label_original=raw,
                target_year_start=y_start,
                target_year_end=y_end,
                term_scope=term,
                conversion_rule="explicit_western_range",
                year_verified=True,
            )
        if minguo_match and not western_single:
            roc_year = int(minguo_match.group(1))
            y_start = roc_year + 1911
            y_end = y_start + 1
            cid = f"{program_id}_roc{roc_year}_{term}"
            return cls(
                id=cid,
                program_id=program_id,
                cycle_label_original=raw,
                target_year_start=y_start,
                target_year_end=y_end,
                term_scope=term,
                conversion_rule="explicit_roc_academic_year_plus_1911",
                year_verified=True,
            )
        if western_single:
            y_val = int(western_single.group(1))
            cid = f"{program_id}_{y_val}_{term}"
            return cls(
                id=cid,
                program_id=program_id,
                cycle_label_original=raw,
                target_year_start=y_val if term != "spring" else y_val - 1,
                target_year_end=y_val if term == "spring" else y_val + 1,
                term_scope=term,
                conversion_rule="explicit_western_term_year",
                year_verified=True,
            )

        slug = hashlib.sha256(raw.encode("utf-8")).hexdigest()[:10]
        return cls(
            id=f"{program_id}_unverified_{slug}",
            program_id=program_id,
            cycle_label_original=raw,
            term_scope=term,
            year_verified=False,
        )


class QuotaValue(BaseModel):
    """Structured quota value contract (Spec Section 2.1 & 4.5). Never fills unknown with zero."""

    model_config = ConfigDict(extra="forbid")

    value_state: ValueState
    amount: float | None = None
    min_amount: float | None = None
    max_amount: float | None = None
    unit: QuotaUnit = QuotaUnit.UNSPECIFIED_UNIT
    period: str | None = None
    shared_pool_id: str | None = None
    original_text: str | None = None
    conversion_rule_id: str | None = None
    derived_person_max: int | None = None

    @model_validator(mode="after")
    def validate_quota_semantics(self) -> "QuotaValue":
        if self.value_state in {
            ValueState.NOT_STATED,
            ValueState.UNVERIFIED,
            ValueState.LEGACY_UNVERIFIED,
            ValueState.NOT_APPLICABLE,
        }:
            if self.amount is not None:
                raise ValueError(f"Quota with state={self.value_state.value} must not carry a fabricated numeric amount")
        if self.value_state == ValueState.KNOWN:
            if self.amount is None and self.min_amount is None and self.max_amount is None:
                raise ValueError("Known quota requires amount or min/max range")
        if self.derived_person_max is not None and not self.conversion_rule_id:
            raise ValueError("Converting academic_year_unit to person count requires an explicit conversion_rule_id")
        return self


class DeadlineValue(BaseModel):
    """Structured deadline contract (Spec Section 4.5). Never fabricates 23:59 when time is omitted."""

    model_config = ConfigDict(extra="forbid")

    value_state: ValueState
    date_str: str | None = None
    has_time: bool = False
    time_str: str | None = None
    timezone_name: str = "Asia/Taipei"
    deadline_type: DeadlineType = DeadlineType.HOME_INTERNAL
    cycle_id: str | None = None
    original_text: str | None = None

    @property
    def display_label(self) -> str:
        if self.value_state != ValueState.KNOWN or not self.date_str:
            return "待確認（未公告確切日期）"
        if self.has_time and self.time_str:
            return f"{self.date_str} {self.time_str} ({self.timezone_name})"
        return f"{self.date_str}（日期已知，確切時間未公告）"

    @model_validator(mode="after")
    def validate_deadline_semantics(self) -> "DeadlineValue":
        if not self.has_time and self.time_str is not None:
            raise ValueError("time_str must be None when has_time is False (do not fabricate 23:59)")
        return self


class MoneyValue(BaseModel):
    """Structured monetary value separating official fees from student experience expenses (Spec 4.5)."""

    model_config = ConfigDict(extra="forbid")

    value_state: ValueState
    amount: float | None = None
    min_amount: float | None = None
    max_amount: float | None = None
    currency: str | None = None
    period: Literal["semester", "academic_year", "month", "one_time", "unspecified"] = "unspecified"
    price_date: str | None = None
    included_items: list[str] = Field(default_factory=list)
    source_kind: Literal["official", "experience"] = "official"
    original_text: str | None = None


class EvidenceLocator(BaseModel):
    """Stable locator for PDF pages/tables/cells or HTML heading paths (Spec 4.2)."""

    model_config = ConfigDict(extra="forbid")

    kind: Literal["html_section", "html_table_row", "pdf_table_cell", "pdf_paragraph", "official_api_field"]
    page_number: int | None = None
    table_index: int | None = None
    row_index: int | None = None
    cell_index: int | None = None
    heading_path: list[str] = Field(default_factory=list)
    anchor_text: str | None = None


class EvidenceRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(default_factory=lambda: f"ev_{uuid4().hex[:16]}")
    snapshot_id: str
    source_url: str
    locator: EvidenceLocator
    short_excerpt: str
    excerpt_hash: str
    access_class: Literal["private_snapshot", "link_only", "suppressed"] = "private_snapshot"
    created_at: datetime = Field(default_factory=utc_now)

    @classmethod
    def create(
        cls,
        *,
        snapshot_id: str,
        source_url: str,
        locator: EvidenceLocator,
        short_excerpt: str,
        access_class: Literal["private_snapshot", "link_only", "suppressed"] = "private_snapshot",
    ) -> "EvidenceRecord":
        clean_excerpt = short_excerpt.strip()[:500]
        return cls(
            snapshot_id=snapshot_id,
            source_url=source_url,
            locator=locator,
            short_excerpt=clean_excerpt,
            excerpt_hash=hashlib.sha256(clean_excerpt.encode("utf-8")).hexdigest(),
            access_class=access_class,
        )


class VerificationMatrixResult(BaseModel):
    """10-point pre-publication verification matrix per candidate assertion (Spec Section 5.2)."""

    model_config = ConfigDict(extra="forbid")

    identity_ok: bool = True
    program_ok: bool = True
    time_cycle_ok: bool = True
    scope_ok: bool = True
    unit_ok: bool = True
    source_authority_ok: bool = True
    evidence_locator_ok: bool = True
    cross_resource_ok: bool = True
    version_supersedes_ok: bool = True
    rights_reuse_ok: bool = True
    reasons: list[str] = Field(default_factory=list)

    @property
    def outcome(self) -> VerificationOutcome:
        critical_fails = (
            not self.identity_ok
            or not self.program_ok
            or not self.unit_ok
            or not self.source_authority_ok
            or not self.rights_reuse_ok
        )
        if critical_fails:
            return VerificationOutcome.FAIL
        if not (
            self.time_cycle_ok
            and self.scope_ok
            and self.evidence_locator_ok
            and self.cross_resource_ok
            and self.version_supersedes_ok
        ):
            return VerificationOutcome.NEEDS_REVIEW
        return VerificationOutcome.PASS


class FieldAssertion(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(default_factory=lambda: f"asrt_{uuid4().hex[:16]}")
    entity_scope: str
    field_path: str
    typed_value: Any = None
    value_state: ValueState
    unit: str | None = None
    effective_scope: dict[str, Any] = Field(default_factory=dict)
    evidence_id: str
    source_url: str
    source_id: str
    resource_kind: str = "html_detail"
    extraction_run_id: str
    academic_year_explicit: str | None = None
    supersedes_assertion_id: str | None = None
    is_official_amendment: bool = False
    verification: VerificationMatrixResult = Field(default_factory=VerificationMatrixResult)
    created_at: datetime = Field(default_factory=utc_now)


class PublishedFieldEnvelope(BaseModel):
    """Required contract for every published key field returned by Public API (Spec Section 4.5)."""

    model_config = ConfigDict(extra="forbid")

    value: Any = None
    value_state: ValueState
    unit: str | None = None
    effective_scope: dict[str, Any] = Field(default_factory=dict)
    evidence_refs: list[dict[str, Any]] = Field(default_factory=list)
    last_verified_at: datetime | None = None
    freshness_status: DataFreshnessStatus = DataFreshnessStatus.CURRENT
    note: str | None = None
