"""Link official preparation steps to the document tools students can open.

The link is a deterministic rule over the step's own title, phase and required
document names. It never reads a student's answers and never decides whether a
document is complete or sufficient; it only says which preparation tool, if any,
matches an official step so the plan can open the right form.
"""
from __future__ import annotations

import re
from collections import Counter
from collections.abc import Iterable
from dataclasses import dataclass

from .models import (
    ApplicationStep,
    TaskDocumentLink,
    UniversityApplicationWorkflow,
)


@dataclass(frozen=True)
class _Rule:
    template_id: str
    documents: re.Pattern[str] | None = None
    title: re.Pattern[str] | None = None
    phase: re.Pattern[str] | None = None


def _rx(pattern: str) -> re.Pattern[str]:
    return re.compile(pattern, re.IGNORECASE)


# Order matters only for tie-breaking; a step's first matching required document
# decides which tool is offered first.
_RULES: tuple[_Rule, ...] = (
    _Rule(
        "exchange-application-data",
        # Home-school forms only; a partner's own application data stays a list item.
        documents=_rx(r"簽名申請表|研修申請表|出國研修申請表|報名表"),
        title=_rx(r"確認資格|選擇志願|最多\s*5\s*個志願|送出校內申請|線上申請"),
        phase=_rx(r"^校內(準備|申請)$"),
    ),
    _Rule(
        "study-plan",
        documents=_rx(r"讀書計畫|研修計畫|讀書與修課計畫|動機信|Statement of Purpose|自我介紹"),
        title=_rx(r"讀書計畫|研修計畫"),
    ),
    _Rule("guardian-consent", documents=_rx(r"家長|監護人")),
    _Rule(
        "selection-consent",
        documents=_rx(r"錄取確認|同意聲明"),
        title=_rx(r"接受.{0,6}錄取|錄取確認"),
    ),
    _Rule(
        "course-preapproval",
        documents=_rx(r"選課行前|預計修課|修課清單|Learning Agreement|修課協議|課程預審|學分抵免表"),
        title=_rx(r"選課"),
    ),
    _Rule("dual-enrollment", documents=_rx(r"雙重學籍"), title=_rx(r"雙重學籍")),
    _Rule("overseas-affidavit", documents=_rx(r"切結")),
    _Rule("military-service-overseas", documents=_rx(r"役男|兵役")),
    _Rule(
        "predeparture-notice",
        documents=_rx(r"出國通報|行前聯絡"),
        title=_rx(r"出國通報|行前通報"),
    ),
    _Rule("subsidy-receipt", documents=_rx(r"補助.*收據|收據")),
    _Rule(
        "administrative-contract",
        documents=_rx(r"行政契約"),
        title=_rx(r"行政契約"),
    ),
    _Rule(
        "arrival-checkin",
        documents=_rx(r"當地聯絡|抵達回報|報到"),
        title=_rx(r"抵達回報|抵達.*報到"),
    ),
    _Rule("semester-report", documents=_rx(r"學期報告|學季報告")),
    _Rule(
        "return-report",
        documents=_rx(r"交換心得|成果報告|返國心得|結案與心得"),
        title=_rx(r"交換心得|成果報告"),
    ),
    _Rule(
        "credit-transfer",
        documents=_rx(r"學分抵免資料|學分抵免申請|學分採認|課程大綱"),
        title=_rx(r"學分抵免|學分採認"),
    ),
)

_TEMPLATE_ORDER = {rule.template_id: index for index, rule in enumerate(_RULES)}


def document_link_for_step(step: ApplicationStep) -> TaskDocumentLink | None:
    """Return the tool and required-document summary for one official step."""

    names = [
        requirement.name.strip()
        for requirement in step.document_requirements
        if requirement.name.strip()
    ]
    positions: dict[str, tuple[int, int]] = {}
    covered: set[str] = set()
    basis: dict[str, str] = {}
    for rule in _RULES:
        document_hits = [
            index for index, name in enumerate(names)
            if rule.documents is not None and rule.documents.search(name)
        ]
        title_hit = bool(rule.title and rule.title.search(step.title))
        if not document_hits and not title_hit:
            continue
        covered.update(names[index] for index in document_hits)
        positions[rule.template_id] = (
            document_hits[0] if document_hits else len(names),
            _TEMPLATE_ORDER[rule.template_id],
        )
        basis[rule.template_id] = "document_name" if document_hits else "step_title"
    if not positions:
        # Stage-only matches are a last resort: the step belongs to the stage a
        # tool was built for, but nothing in its own text names that tool.
        for rule in _RULES:
            if rule.phase is not None and rule.phase.search(step.phase):
                positions[rule.template_id] = (len(names), _TEMPLATE_ORDER[rule.template_id])
                basis[rule.template_id] = "stage"
    template_ids = [
        template_id for template_id, _ in sorted(positions.items(), key=lambda item: item[1])
    ]
    if not template_ids and not names:
        return None
    strongest = (
        "document_name" if "document_name" in basis.values()
        else "step_title" if "step_title" in basis.values()
        else "stage" if basis else "none"
    )
    return TaskDocumentLink(
        template_ids=template_ids,
        requirement_names=names,
        unmapped_requirement_names=[name for name in names if name not in covered],
        basis=strongest,
    )


def audit_task_document_links(
    workflows: Iterable[UniversityApplicationWorkflow],
) -> dict[str, object]:
    """Summarize which official steps can open a tool, for release review."""

    totals: Counter[str] = Counter()
    unlinked: Counter[tuple[str, str, tuple[str, ...]]] = Counter()
    for workflow in workflows:
        for step in workflow.steps:
            totals["steps"] += 1
            link = document_link_for_step(step)
            if link is None:
                totals["no_documents"] += 1
            elif link.template_ids:
                totals["tool_linked"] += 1
                totals[f"basis_{link.basis}"] += 1
            else:
                totals["requirements_only"] += 1
                unlinked[
                    (workflow.home_university, step.title, tuple(link.requirement_names))
                ] += 1
    return {
        "steps": totals["steps"],
        "tool_linked": totals["tool_linked"],
        "requirements_only": totals["requirements_only"],
        "no_documents": totals["no_documents"],
        "linked_by_document_name": totals["basis_document_name"],
        "linked_by_step_title": totals["basis_step_title"],
        "linked_by_stage_only": totals["basis_stage"],
        "requirements_only_patterns": [
            {
                "home_university": key[0],
                "step_title": key[1],
                "required_documents": list(key[2]),
                "step_count": count,
            }
            for key, count in unlinked.most_common()
        ],
    }
