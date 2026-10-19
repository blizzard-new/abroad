"""Explainable editorial audit. Grades never change public indexing automatically."""
from __future__ import annotations

import hashlib
import json
import re
from collections import Counter, defaultdict
from collections.abc import Sequence
from urllib.parse import urlsplit

from .models import PartnerUniversity

# Only facts presented to readers; scrape/check times and decorative assets are not content changes.
MATERIAL_FIELDS = (
    "program_type", "country", "school_name", "academic_year", "application_round",
    "availability_status", "availability_note", "agreement_type", "agreement_level",
    "quota_status", "application_window_status", "colleges", "degree_levels", "study_period",
    "quota", "eligibility", "language_requirement", "language_review_note", "application_deadline",
    "application_info", "tuition_info", "source_url", "website", "field_evidence", "reference_data",
    "program_options", "partner_application_prerequisite", "partner_application_deadline",
    "nomination_deadline", "semester_dates", "housing_info", "course_restrictions",
    "partner_exchange_details", "language_conditions",
)
FACT_FIELDS = ("eligibility", "language_requirement", "study_period", "application_deadline",
               "tuition_info", "housing_info", "course_restrictions", "application_info")
VOLATILE_FIELDS = {"checked_at", "last_checked", "last_success_at", "fetched_at", "source_checks", "student_summary_zh"}


def stable_value(value):
    if isinstance(value, dict):
        return {k: stable_value(v) for k, v in sorted(value.items()) if k not in VOLATILE_FIELDS}
    if isinstance(value, list):
        return [stable_value(v) for v in value]
    if isinstance(value, str):
        return re.sub(r"\s+", " ", value).strip()
    return value


def digest(value) -> str:
    return hashlib.sha256(json.dumps(stable_value(value), ensure_ascii=False, sort_keys=True,
                                     separators=(",", ":")).encode()).hexdigest()


def material_content(rows: Sequence[PartnerUniversity]) -> list[dict]:
    values = []
    for row in rows:
        data = row.model_dump(mode="json")
        values.append(stable_value({k: data.get(k) for k in MATERIAL_FIELDS}))
    # Source record ordering is not a substantive edit.
    return sorted(values, key=digest)


def source_is_home_official(url: str, official_url: str) -> bool:
    """Conservative home-school domain check, not a proof that the facts are current."""
    try:
        source, home = urlsplit(url), urlsplit(official_url)
        host = (home.hostname or "").lower()
        # Taiwanese university registries identify one institution at *.edu.tw.
        institution = ".".join(host.split(".")[-3:]) if host.endswith(".edu.tw") else host
        return bool(institution and source.scheme in {"https", "http"} and not source.username
                    and not source.password and (source.hostname == institution
                    or (source.hostname or "").endswith("." + institution)))
    except ValueError:
        return False


def assess(rows: Sequence[PartnerUniversity], official_url: str) -> dict:
    fields = sorted({name for row in rows for name in FACT_FIELDS
                     if getattr(row, name, None) and len(str(getattr(row, name)).strip()) >= 8})
    evidenced = sorted({name for row in rows for name, evidence in row.field_evidence.items()
                        if evidence.status == "verified_current" and source_is_home_official(evidence.source_url, official_url)})
    official = any(source_is_home_official(row.source_url, official_url) for row in rows)
    tier = "A" if official and len(fields) >= 4 and len(evidenced) >= 2 else "B" if official and len(fields) >= 2 else "C"
    reasons = []
    if not official:
        reasons.append("母校官方網域來源待人工核對")
    if len(fields) < 2:
        reasons.append("具體申請資訊不足，優先補強")
    if any(row.quota_status in {None, "not_published", "reference_only"} for row in rows):
        reasons.append("名額未確認不會單獨觸發取消索引")
    if len(evidenced) < 2:
        reasons.append("本期欄位查核證據不足；保留參考價值，逐頁審閱")
    return {"tier": tier, "fact_fields": fields, "verified_fields": evidenced,
            "home_official_source": official, "reasons": reasons,
            "index_action": "keep_existing_pending_review"}


def audit_catalogues(catalogues) -> dict:
    from .seo import group_partners, partner_path
    pages, duplicates = [], defaultdict(list)
    for university, partners in catalogues:
        for rows in group_partners(partners).values():
            path = partner_path(university, rows[0])
            assessment = assess(rows, university.official_url)
            facts = [{key: getattr(row, key) for key in FACT_FIELDS} for row in rows]
            fingerprint = digest(sorted(facts, key=digest))
            # Common mother-school rules may be legitimate: candidates require human review.
            duplicates[fingerprint].append(path)
            pages.append({"path": path, "home": university.id, "school": rows[0].school_name,
                          **assessment, "content_hash": digest(material_content(rows)),
                          "similarity_hash": fingerprint})
    groups = [paths for paths in duplicates.values() if len(paths) > 1]
    return {"policy_version": 1, "mode": "audit_only", "page_count": len(pages),
            "tiers": dict(sorted(Counter(p["tier"] for p in pages).items())),
            "duplicate_candidate_groups": groups, "pages": pages,
            "limitations": "Internal heuristic, not a Google score or indexing evidence. Shared rules may be valid. No noindex/canonical changes are applied."}
