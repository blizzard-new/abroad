"""Transparent planning defaults for tasks the student has not sized yet.

Everything here is a system suggestion, not a school rule: effort hours are a
coarse estimate that the student can overwrite, and stage gating only holds back
tasks that have no official deadline until earlier stages are marked done.
"""
from __future__ import annotations

import re
from collections.abc import Iterable

from .models import ApplicationStep, TaskDocumentLink

# Rough hours to gather or write one required document. They size the work of
# *preparing* the item, not the time a school or a test centre needs.
_DOCUMENT_HOURS: tuple[tuple[re.Pattern[str], float], ...] = (
    (re.compile(r"讀書計畫|研修計畫|讀書與修課計畫|動機信|Statement of Purpose", re.I), 8.0),
    (re.compile(r"履歷|自我介紹"), 3.0),
    (re.compile(r"Learning Agreement|修課協議|預計修課|選課行前|修課清單|課程預審"), 4.0),
    (re.compile(r"簽證"), 6.0),
    (re.compile(r"保險"), 2.0),
    (re.compile(r"住宿"), 4.0),
    (re.compile(r"語言|IELTS|TOEFL|多益|TOEIC|英文能力|B1"), 2.0),
    (re.compile(r"家長|監護人|同意|切結"), 1.5),
    (re.compile(r"申請表|申請資料|報名表"), 2.0),
    (re.compile(r"成績單|排名"), 1.0),
    (re.compile(r"護照|證件照"), 1.0),
    (re.compile(r"學分抵免|課程大綱|心得|成果報告|報告"), 3.0),
    (re.compile(r"錄取|Offer"), 1.0),
)
_BASE_STEP_HOURS = 1.5
_MAX_STEP_HOURS = 30.0


def suggest_effort_hours(
    step: ApplicationStep, link: TaskDocumentLink | None
) -> float:
    """Return a labelled estimate in 0.5-hour units for preparing one step."""

    names = list(link.requirement_names) if link else [
        requirement.name for requirement in step.document_requirements
    ]
    total = _BASE_STEP_HOURS
    for name in names:
        for pattern, hours in _DOCUMENT_HOURS:
            if pattern.search(name):
                total += hours
                break
        else:
            total += 1.0
    total = min(total, _MAX_STEP_HOURS)
    return round(total * 2) / 2


# A phase's rank is where it sits in the usual exchange journey. Ranks only
# gate undated work; they are never presented as a rule from the school.
PHASE_RANK: dict[str, int] = {
    "校內準備": 0,
    "校內申請": 1,
    "甄選與分發": 2,
    "甄選與提名": 2,
    "合作校提名": 2,
    "合作校提名與申請": 3,
    "合作校申請": 3,
    "錄取與行前": 4,
    "課程與錄取": 4,
    "行前安排": 4,
    "長庚行前行政": 4,
    "抵達與返國": 5,
    "返國結案": 5,
}
# Undated tasks from rank 3 on cannot start until every task of the same
# school branch at a lower rank has been marked done by the student.
_GATE_RANKS = frozenset({3, 4, 5})
_GATE_REASON = {
    3: "要等校內甄選與正式提名結果確定後才能開始；前面的準備工作標示完成後會自動開放。",
    4: "要等合作校申請與錄取結果確定後才能開始；前面的準備工作標示完成後會自動開放。",
    5: "要等錄取、行前與出國階段完成後才能開始；前面的工作標示完成後會自動開放。",
}


def phase_rank(phase: str) -> int | None:
    return PHASE_RANK.get(phase.strip())


def stage_gate_reason(
    rank: int | None, earlier_ranks_open: Iterable[int]
) -> str | None:
    """Return the waiting reason when an undated task is still gated.

    ``earlier_ranks_open`` holds the ranks of the unfinished tasks that share a
    school branch with the task being checked.
    """

    if rank is None or rank not in _GATE_RANKS:
        return None
    if any(open_rank < rank for open_rank in earlier_ranks_open):
        return _GATE_REASON[rank]
    return None
