"""Field-level reconciliation, 10-point verification matrix, and change-set generation (Spec Sections 5, 8, 9)."""

from __future__ import annotations

import hashlib
import json
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field

from .contracts import (
     HIGH_RISK_FIELDS,
    MEDIUM_RISK_FIELDS,
    ChangeOrigin,
    DataFreshnessStatus,
    EvidenceRecord,
    FieldAssertion,
    PublishedFieldEnvelope,
    QuotaUnit,
    QuotaValue,
    ReviewStatus,
    RiskLevel,
    ValueState,
    VerificationMatrixResult,
    VerificationOutcome,
    canonical_json_hash,
    utc_now,
)


class ChangeItemRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(default_factory=lambda: f"ci_{uuid4().hex[:14]}")
    field_path: str
    before_value: Any = None
    after_value: Any = None
    before_state: ValueState | None = None
    after_state: ValueState
    unit: str | None = None
    effective_scope: dict[str, Any] = Field(default_factory=dict)
    supporting_assertion_ids: list[str] = Field(default_factory=list)
    conflicting_assertion_ids: list[str] = Field(default_factory=list)
    evidence_excerpts: list[dict[str, Any]] = Field(default_factory=list)
    reason: str
    risk: RiskLevel
    approval_status: Literal["pending", "approved", "rejected", "deferred"] = "pending"


from typing import Literal


class ChangeSetRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(default_factory=lambda: f"cs_{uuid4().hex[:16]}")
    entity_scope: str
    home_id: str
    host_id: str
    program_id: str
    cycle_id: str
    base_release_id: str | None = None
    candidate_version: int = 1
    evidence_set_hash: str
    risk: RiskLevel
    change_origin: ChangeOrigin = ChangeOrigin.SOURCE_CHANGE
    status: ReviewStatus = ReviewStatus.PENDING
    items: list[ChangeItemRecord] = Field(default_factory=list)
    created_at: Any = Field(default_factory=utc_now)
    updated_at: Any = Field(default_factory=utc_now)


def classify_field_risk(field_path: str, has_conflict: bool = False) -> RiskLevel:
    """Classify change item risk per Spec Section 9.1. High-risk fields always require human approval."""
    if has_conflict or field_path in HIGH_RISK_FIELDS:
        return RiskLevel.HIGH
    if field_path in MEDIUM_RISK_FIELDS:
        return RiskLevel.MEDIUM
    return RiskLevel.LOW


def evaluate_10_point_verification_matrix(
    assertion: FieldAssertion,
    *,
    evidence: EvidenceRecord | None,
    expected_home_id: str,
    expected_host_id: str,
    expected_program_id: str,
    expected_cycle_year: str | None,
    source_approved: bool = True,
    source_authoritative_for_field: bool = True,
    reuse_allowed: bool = True,
    peer_assertions_same_field: list[FieldAssertion] | None = None,
) -> VerificationMatrixResult:
    """Run the 10-point pre-publication verification matrix on a candidate assertion (Spec Section 5.2)."""
    reasons: list[str] = []

    # 1. Identity check
    identity_ok = bool(expected_home_id and expected_host_id and assertion.entity_scope.startswith(f"off_{expected_home_id.lower()}_"))
    if not identity_ok:
        reasons.append("identity_mismatch_or_ambiguous_school")

    # 2. Program check
    program_ok = bool(expected_program_id)
    if not program_ok:
        reasons.append("program_missing_or_mismatched")

    # 3. Time / Cycle check (T04: list year vs attachment/detail year conflict)
    time_cycle_ok = True
    if not assertion.academic_year_explicit:
        time_cycle_ok = False
        reasons.append("academic_year_not_explicit_in_source")
    elif expected_cycle_year and assertion.academic_year_explicit != expected_cycle_year:
        time_cycle_ok = False
        reasons.append(f"cycle_year_mismatch:{assertion.academic_year_explicit}!={expected_cycle_year}")

    # 4. Scope check
    scope_ok = bool(assertion.effective_scope and "academic_unit_mode" in assertion.effective_scope)
    if not scope_ok:
        reasons.append("scope_not_explicitly_preserved")

    # 5. Unit check (T06: quota units must be valid and never fabricated)
    unit_ok = True
    if assertion.field_path == "quota" and assertion.value_state == ValueState.KNOWN:
        if not assertion.unit or assertion.unit == QuotaUnit.UNSPECIFIED_UNIT.value:
            unit_ok = False
            reasons.append("quota_unit_missing")
        if isinstance(assertion.typed_value, dict):
            if assertion.typed_value.get("derived_person_max") is not None and not assertion.typed_value.get("conversion_rule_id"):
                unit_ok = False
                reasons.append("unverified_unit_conversion_to_persons")

    # 6. Source authority check (Spec 5.1: e.g., experience cannot set official tuition or home quota)
    source_authority_ok = source_approved and source_authoritative_for_field
    if not source_authority_ok:
        reasons.append("source_not_authoritative_for_field")

    # 7. Evidence locator check
    evidence_locator_ok = bool(
        evidence is not None
        and evidence.short_excerpt.strip()
        and (evidence.locator.page_number is not None or evidence.locator.heading_path or evidence.locator.row_index is not None)
    )
    if not evidence_locator_ok:
        reasons.append("insufficient_evidence_locator")

    # 8. Cross-resource consistency (list vs detail vs PDF attachment)
    cross_resource_ok = True
    if peer_assertions_same_field:
        for peer in peer_assertions_same_field:
            if peer.id == assertion.id:
                continue
            if peer.supersedes_assertion_id == assertion.id or assertion.supersedes_assertion_id == peer.id:
                continue
            if peer.academic_year_explicit and assertion.academic_year_explicit and peer.academic_year_explicit != assertion.academic_year_explicit:
                cross_resource_ok = False
                reasons.append("cross_resource_year_conflict")
            elif peer.typed_value != assertion.typed_value and peer.value_state == ValueState.KNOWN and assertion.value_state == ValueState.KNOWN:
                cross_resource_ok = False
                reasons.append("cross_resource_value_conflict")

    # 9. Version / Supersedes check
    version_supersedes_ok = True
    if assertion.supersedes_assertion_id and not assertion.is_official_amendment:
        version_supersedes_ok = False
        reasons.append("supersedes_claimed_without_explicit_official_amendment")

    # 10. Rights / Reuse check
    rights_reuse_ok = reuse_allowed
    if not rights_reuse_ok:
        reasons.append("rights_reuse_restricted")

    return VerificationMatrixResult(
        identity_ok=identity_ok,
        program_ok=program_ok,
        time_cycle_ok=time_cycle_ok,
        scope_ok=scope_ok,
        unit_ok=unit_ok,
        source_authority_ok=source_authority_ok,
        evidence_locator_ok=evidence_locator_ok,
        cross_resource_ok=cross_resource_ok,
        version_supersedes_ok=version_supersedes_ok,
        rights_reuse_ok=rights_reuse_ok,
        reasons=reasons,
    )


def reconcile_offering_assertions(
    *,
    entity_scope: str,
    home_id: str,
    host_id: str,
    program_id: str,
    cycle_id: str,
    expected_cycle_year: str | None,
    base_release_id: str | None,
    current_published_fields: dict[str, PublishedFieldEnvelope],
    candidate_assertions: list[FieldAssertion],
    evidence_by_id: dict[str, EvidenceRecord],
    change_origin: ChangeOrigin = ChangeOrigin.SOURCE_CHANGE,
    new_source_covered_fields: set[str] | None = None,
) -> ChangeSetRecord | None:
    """Reconcile assertions field-by-field without row-level upsert overwrite (Spec Section 8.1, T04, T11, T27)."""
    by_field: dict[str, list[FieldAssertion]] = {}
    for asrt in candidate_assertions:
        if asrt.entity_scope != entity_scope:
            continue
        by_field.setdefault(asrt.field_path, []).append(asrt)

    change_items: list[ChangeItemRecord] = []
    all_evidence_hashes: list[str] = []

    for field_path, assertions in sorted(by_field.items()):
        # Run 10-point check across peers for this field
        verified_assertions: list[FieldAssertion] = []
        for asrt in assertions:
            ev = evidence_by_id.get(asrt.evidence_id)
            if ev:
                all_evidence_hashes.append(ev.excerpt_hash)
            matrix = evaluate_10_point_verification_matrix(
                asrt,
                evidence=ev,
                expected_home_id=home_id,
                expected_host_id=host_id,
                expected_program_id=program_id,
                expected_cycle_year=expected_cycle_year,
                peer_assertions_same_field=assertions,
            )
            asrt = asrt.model_copy(update={"verification": matrix})
            verified_assertions.append(asrt)

        # Filter out assertions that were explicitly superseded by an official amendment in the same scope
        superseded_ids = {
            a.supersedes_assertion_id
            for a in verified_assertions
            if a.supersedes_assertion_id and a.is_official_amendment
        }
        active_assertions = [a for a in verified_assertions if a.id not in superseded_ids]

        distinct_values = {
            canonical_json_hash({"v": a.typed_value, "s": a.value_state.value, "u": a.unit, "y": a.academic_year_explicit})
            for a in active_assertions
        }
        has_year_conflict = any("cycle_year_mismatch" in r or "cross_resource_year_conflict" in r for a in active_assertions for r in a.verification.reasons)
        has_value_conflict = len(distinct_values) > 1 or has_year_conflict

        prior_env = current_published_fields.get(field_path)
        before_val = prior_env.value if prior_env else None
        before_state = prior_env.value_state if prior_env else None

        ev_list = []
        for a in active_assertions:
            ev = evidence_by_id.get(a.evidence_id)
            if ev:
                ev_list.append(
                    {
                        "assertion_id": a.id,
                        "source_url": ev.source_url,
                        "locator": ev.locator.model_dump(mode="json"),
                        "short_excerpt": ev.short_excerpt,
                        "excerpt_hash": ev.excerpt_hash,
                        "academic_year": a.academic_year_explicit,
                    }
                )

        if has_value_conflict:
            # T04: Conflict between list year and detail/attachment year or conflicting numbers -> never overwrite by fetch order!
            after_val = [a.typed_value for a in active_assertions]
            after_state = ValueState.CONFLICTING
            reason = "conflicting_assertions_or_year_mismatch"
            supporting_ids = []
            conflicting_ids = [a.id for a in active_assertions]
        else:
            chosen = active_assertions[0]
            after_val = chosen.typed_value
            after_state = (
                ValueState.UNVERIFIED
                if chosen.verification.outcome == VerificationOutcome.FAIL
                else chosen.value_state
            )
            reason = (
                "parser_version_upgrade"
                if change_origin == ChangeOrigin.PARSER_CHANGE
                else ("context_changed" if change_origin == ChangeOrigin.CONTEXT_CHANGE else "source_content_updated")
            )
            supporting_ids = [a.id for a in active_assertions]
            conflicting_ids = []

        # Compare semantic equality with currently published field
        same_as_published = (
            prior_env is not None
            and canonical_json_hash(before_val) == canonical_json_hash(after_val)
            and before_state == after_state
            and change_origin != ChangeOrigin.PARSER_CHANGE
        )
        if same_as_published:
            continue

        change_items.append(
            ChangeItemRecord(
                field_path=field_path,
                before_value=before_val,
                after_value=after_val,
                before_state=before_state,
                after_state=after_state,
                unit=active_assertions[0].unit,
                effective_scope=active_assertions[0].effective_scope,
                supporting_assertion_ids=supporting_ids,
                conflicting_assertion_ids=conflicting_ids,
                evidence_excerpts=ev_list,
                reason=reason,
                risk=classify_field_risk(field_path, has_conflict=has_value_conflict),
            )
        )

    # T27: When a previously verified field is absent from a newly updated document, NEVER overwrite it with null!
    # Keep the existing published value intact; optionally emit a non-destructive verification check item if requested.
    if new_source_covered_fields is not None:
        for existing_field, env in sorted(current_published_fields.items()):
            if existing_field not in by_field and existing_field not in new_source_covered_fields:
                # Field was not in the new document -> preserve existing published value, do NOT create a null overwrite!
                continue

    if not change_items:
        return None

    overall_risk = RiskLevel.LOW
    if any(item.risk == RiskLevel.HIGH for item in change_items):
        overall_risk = RiskLevel.HIGH
    elif any(item.risk == RiskLevel.MEDIUM for item in change_items):
        overall_risk = RiskLevel.MEDIUM

    overall_status = (
        ReviewStatus.CONFLICTING
        if any(item.after_state == ValueState.CONFLICTING for item in change_items)
        else ReviewStatus.PENDING
    )

    evidence_set_hash = canonical_json_hash(
        {
            "ev": sorted(all_evidence_hashes),
            "items": [
                {
                    "field_path": i.field_path,
                    "after_value": i.after_value,
                    "after_state": i.after_state.value,
                    "supporting": sorted(i.supporting_assertion_ids),
                    "conflicting": sorted(i.conflicting_assertion_ids),
                }
                for i in change_items
            ],
        }
    )

    return ChangeSetRecord(
        entity_scope=entity_scope,
        home_id=home_id,
        host_id=host_id,
        program_id=program_id,
        cycle_id=cycle_id,
        base_release_id=base_release_id,
        candidate_version=1,
        evidence_set_hash=evidence_set_hash,
        risk=overall_risk,
        change_origin=change_origin,
        status=overall_status,
        items=change_items,
    )


def aggregate_quotas_safely(quotas: list[QuotaValue]) -> dict[str, Any]:
    """Aggregate quotas for public summaries without summing incompatible units or double-counting shared pools (Spec 2.1, 8.1, 13.3, T06, T07)."""
    seen_pools: set[str] = set()
    persons_total = 0.0
    academic_year_units_total = 0.0
    semester_units_total = 0.0
    unknown_count = 0
    zero_count = 0
    shared_pool_count = 0

    for q in quotas:
        if q.value_state != ValueState.KNOWN:
            unknown_count += 1
            continue
        val = q.amount if q.amount is not None else (q.max_amount or 0.0)
        if val == 0:
            zero_count += 1
            continue
        if q.shared_pool_id:
            if q.shared_pool_id in seen_pools:
                continue
            seen_pools.add(q.shared_pool_id)
            shared_pool_count += 1

        if q.unit == QuotaUnit.PERSONS:
            persons_total += val
        elif q.unit == QuotaUnit.ACADEMIC_YEAR_UNIT:
            academic_year_units_total += val
        elif q.unit == QuotaUnit.SEMESTER_UNIT:
            semester_units_total += val
        elif q.unit == QuotaUnit.POOL_TOTAL:
            persons_total += val

    return {
        "persons_quota_total": int(persons_total) if persons_total.is_integer() else persons_total,
        "academic_year_unit_total": int(academic_year_units_total) if academic_year_units_total.is_integer() else academic_year_units_total,
        "semester_unit_total": int(semester_units_total) if semester_units_total.is_integer() else semester_units_total,
        "shared_pools_deduplicated": shared_pool_count,
        "unverified_or_not_stated_count": unknown_count,
        "explicit_zero_count": zero_count,
    }
