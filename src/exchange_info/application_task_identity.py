"""Stable preparation identities; merging never changes publication status.

Legacy partner-scoped rules remain separate unless their shared home process is
explicitly established. The narrow NTPU exceptions below refer to the published
2026-2027 guideline, pages 3-4. They are not evidence of a current deadline.
"""
from __future__ import annotations

import hashlib
import json

from .models import ApplicationStep, UniversityApplicationWorkflow

NTPU_GUIDELINE = (
    "https://cms-carrier.ntpu.edu.tw/uploads/"
    "2026_2027_Academic_Year_Outbound_Exchange_Program_Guidelines_1e5870e83d.pdf"
)
NTPU_GUIDELINE_116 = "https://cms-carrier.ntpu.edu.tw/uploads/116_16e535159d.pdf"
_NTPU_GUIDELINES_BY_YEAR = {"115": NTPU_GUIDELINE, "116": NTPU_GUIDELINE_116}
_NTPU_COMMON_TITLES = {
    "完成臺北大學線上申請與報名表": "ntpu-home-submit",
    "參加書審、讀書計畫與語言面試": "ntpu-home-review",
}


def preparation_identity(
    workflow: UniversityApplicationWorkflow, step: ApplicationStep, index: int,
) -> tuple[str, str, str]:
    """Return ID, scope and signature, independent of preference rank.

    Different instructions/deadlines never share completion. A reviewed change
    gets a new signature, leaving prior personal progress recoverable.
    """
    scope = step.scope
    home_key = None
    if (step.rule_id and scope.home_universities
            and workflow.home_university in scope.home_universities
            and not scope.partner_universities):
        home_key = step.overrides_rule_id or step.rule_id
    home_sources = {
        source.source_url for source in workflow.sources
        if source.role.value == "home_university"
    }
    if (workflow.home_university == "國立臺北大學"
            and workflow.academic_year in _NTPU_GUIDELINES_BY_YEAR
            and step.title in _NTPU_COMMON_TITLES
            and _NTPU_GUIDELINES_BY_YEAR[workflow.academic_year] in step.source_urls
            and set(step.source_urls).issubset(
                home_sources | {_NTPU_GUIDELINES_BY_YEAR[workflow.academic_year]}
            )
            and not scope.colleges and not scope.departments
            and step.phase in {"校內申請", "甄選與分發"}):
        home_key = _NTPU_COMMON_TITLES[step.title]
    task_scope = "home" if home_key else "partner"
    rule_identity = home_key or step.overrides_rule_id or step.rule_id or f"legacy-{index}"
    instructions = step.model_dump(mode="json", exclude={
        "rule_id", "overrides_rule_id", "scope", "checked_at", "deadline_checked_at",
    })
    # An absent optional dependency annotation is not a source change. Keep
    # pre-existing task IDs so this model extension cannot erase saved progress.
    if not step.depends_on_rule_ids:
        instructions.pop("depends_on_rule_ids", None)
    # Only metadata ordering is insignificant; document/instruction order stays.
    instructions["source_urls"] = sorted(set(step.source_urls))
    instructions["official_form_urls"] = sorted(set(step.official_form_urls))
    instructions["scope"] = scope.model_dump(exclude={"partner_universities"})
    signature = _digest(instructions)
    context = workflow.applied_context
    identity = {
        "home": workflow.home_university,
        "partner": None if home_key else workflow.school_name,
        "program": workflow.program_type,
        "year": (context.academic_year if context else None) or workflow.academic_year,
        "round": (context.application_round if context else None) or workflow.application_round,
        "college": context.college if context else None,
        "department": context.department if context else None,
        "rule": rule_identity,
        "signature": signature,
    }
    return f"application-task-{_digest(identity)[:32]}", task_scope, signature


def _digest(value: object) -> str:
    encoded = json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()
