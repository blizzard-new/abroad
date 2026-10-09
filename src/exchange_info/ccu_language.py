"""Resolve only reviewed CCU conditions; other home schools keep their own parser."""

from dataclasses import dataclass
from .ccu_sources import PARTNERS_URL
from .models import PartnerUniversity
from .qualification_scopes import degree_scope_matches


@dataclass(frozen=True)
class CcuLanguageAssessment:
    threshold: float | None
    note: str


def is_ccu_partner(partner: PartnerUniversity) -> bool:
    return partner.source_url == PARTNERS_URL


def assess_ccu_language(
    partner: PartnerUniversity, test: str | None, degree_level: str | None = None
) -> CcuLanguageAssessment:
    note = partner.language_review_note or "中正當期語言條件尚未完成結構化核對。"
    evidence = partner.field_evidence.get("language_requirement")
    if not evidence or evidence.status != "verified_current":
        return CcuLanguageAssessment(None, note)
    rules = [rule for rule in partner.language_conditions if rule.test == test]
    if any(rule.degree_levels for rule in rules):
        if not degree_level:
            return CcuLanguageAssessment(None, note)
        rules = [
            rule
            for rule in rules
            if not rule.degree_levels
            or degree_scope_matches("、".join(rule.degree_levels), degree_level)
        ]
    if len(rules) != 1:
        return CcuLanguageAssessment(None, note)
    rule = rules[0]
    if (
        rule.requirement_level != "required"
        or rule.minimum_score is None
        or rule.scope_choice_required
        or rule.additional_conditions
    ):
        return CcuLanguageAssessment(None, note)
    if rule.track or rule.host_faculties or rule.teaching_language:
        return CcuLanguageAssessment(None, note)
    return CcuLanguageAssessment(rule.minimum_score, note)
