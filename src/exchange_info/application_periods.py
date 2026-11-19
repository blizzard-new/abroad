"""Published workflow periods and the application path labels used to select them."""
import unicodedata
from collections import defaultdict
from collections.abc import Iterable

from pydantic import BaseModel, Field

from .models import UniversityApplicationWorkflow


def _round_key(home: str | None, year: str | None, label: str) -> str:
    """Resolve the labels the CGU application path generates for a saved term."""
    label = " ".join(unicodedata.normalize("NFKC", label).strip().casefold().split())
    if home != "長庚大學" or not year or not year.isascii() or not year.isdigit() or len(year) > 3:
        return label
    fall = int(year) + 1911
    if label in (f"{year}-1", f"{year}-1({fall} 秋季出國)", f"{year}-1({fall} 秋季・全學年出國)"):
        return "秋季/全學年梯次"
    if label in (f"{year}-2", f"{year}-2({fall + 1} 春季出國)"):
        return "春季梯次"
    return label


def matching_workflow_round(
    home: str | None,
    year: str | None,
    requested: str | None,
    published: Iterable[str],
) -> str | None:
    """Return the original published label so clients can display and use its exact scope."""
    if not requested:
        return None
    key = _round_key(home, year, requested)
    return next((label for label in published if label and _round_key(home, year, label) == key), None)


class ApplicationPeriodOption(BaseModel):
    academic_year: str
    application_round: str
    school_count: int
    needs_confirmation: bool
    source_urls: list[str] = Field(default_factory=list)


class ApplicationPeriodOptions(BaseModel):
    home_university: str
    periods: list[ApplicationPeriodOption] = Field(default_factory=list)
    workflows_without_period: int = 0
    note: str = "選項取自已發布流程的原始年度與梯次，不代表當期仍開放；期限與適用條件請查看各校來源。"


def application_period_options(home: str, workflows: list[UniversityApplicationWorkflow]) -> ApplicationPeriodOptions:
    groups = defaultdict(list)
    missing = 0
    for workflow in workflows:
        if workflow.home_university != home:
            continue
        year = (workflow.academic_year or "").strip()
        rounds = list(dict.fromkeys(
            value.strip() for value in [*workflow.effective_application_rounds, workflow.application_round or ""]
            if value.strip()
        ))
        if not year or not rounds:
            missing += 1
            continue
        for application_round in rounds:
            groups[(year, application_round)].append(workflow)
    periods = [ApplicationPeriodOption(
        academic_year=year, application_round=application_round,
        school_count=len({row.school_name for row in rows}),
        needs_confirmation=any(row.applicability_status != "verified" or not row.sources for row in rows),
        source_urls=sorted({source.source_url for row in rows for source in row.sources if source.source_url}),
    ) for (year, application_round), rows in groups.items()]
    periods.sort(key=lambda row: (row.academic_year, row.application_round), reverse=True)
    return ApplicationPeriodOptions(home_university=home, periods=periods, workflows_without_period=missing)
