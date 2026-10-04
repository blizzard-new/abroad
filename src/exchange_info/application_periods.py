"""Expose the exact periods present in published workflow data, without aliases."""
from collections import defaultdict

from pydantic import BaseModel, Field

from .models import UniversityApplicationWorkflow


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
