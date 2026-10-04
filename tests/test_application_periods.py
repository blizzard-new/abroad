from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient

from exchange_info.api import create_app
from exchange_info.application_periods import application_period_options
from exchange_info.content_governance import LocalContentGovernanceStore, stage_workflow_refresh
from exchange_info.models import ApplicationWorkflowSource, UniversityApplicationWorkflow, UserAccount
from exchange_info.repositories import JsonlAccountRepository
from test_notification_changes import session


@pytest.mark.parametrize("year,requested_round,source_rounds,expected",[
    ("115","秋季梯次",["秋季梯次","春季梯次"],True),
    ("115","第一梯次",["秋季梯次"],False),
    ("115","第一梯次",[],False),
    ("115",None,["秋季梯次"],False),
    ("116","秋季梯次",["秋季梯次"],False),
])
def test_confirmed_deadline_requires_exact_selected_period(year,requested_round,source_rounds,expected):
    from exchange_info.application_rules import _workflow_checklist, _workflow_context_checks, compose_application_workflow
    from exchange_info.models import ApplicationRuleContext, ApplicationStep, PersonalApplicationPlanRequest
    deadline=datetime(2027,2,1,tzinfo=timezone.utc)
    step=ApplicationStep(order=1,phase="申請",title="校內送件",summary="隔離測試步驟",responsible_party="學生",
        support_status="verified",deadline_status="verified_exact",deadline_at=deadline,
        deadline_checked_at=datetime(2026,10,1,tzinfo=timezone.utc),deadline_source_url="https://example.edu/notice")
    source=workflow(steps=[step],effective_application_rounds=source_rounds,
        review_status="published",published_at=datetime(2026,10,1,tzinfo=timezone.utc))
    composed=compose_application_workflow(source,ApplicationRuleContext(academic_year=year,application_round=requested_round))
    rows=_workflow_checklist(1,composed,"國際處")
    assert (rows[0].official_deadline_at==deadline)==expected
    assert source.applied_context is None
    request=PersonalApplicationPlanRequest(home_school="長庚大學",college="工學院",academic_year=year,
        application_round=requested_round,preferences=[{"rank":1,"school_name":source.school_name}])
    checks=_workflow_context_checks(request,composed,contact_unit="國際處")
    assert (next(row for row in checks if row.code=='application_round').status=='pass') == bool(requested_round and requested_round in source_rounds)


def workflow(school="測試交換校", **values):
    return UniversityApplicationWorkflow(
        home_university="長庚大學", school_name=school, academic_year="115",
        effective_application_rounds=["秋季梯次","春季梯次"],
        applicability_status="verified",
        sources=[ApplicationWorkflowSource(title="隔離測試來源",source_url="https://example.edu/notice",role="home_university")],
    ).model_copy(update=values)


def test_options_preserve_exact_year_round_without_aliases_or_missing_year_inference():
    rows=[workflow(),workflow(),workflow("第二校",applicability_status="needs_confirmation"),
          workflow("過去年度",academic_year="114",application_round="第一梯次",effective_application_rounds=[]),
          workflow("缺年度",academic_year=None),workflow("缺梯次",effective_application_rounds=[]),
          workflow("別校來源",home_university="國立臺北大學")]
    result=application_period_options("長庚大學",rows)
    assert result.workflows_without_period==2
    periods={(row.academic_year,row.application_round):row for row in result.periods}
    assert set(periods)=={("115","秋季梯次"),("115","春季梯次"),("114","第一梯次")}
    assert periods[("115","秋季梯次")].school_count==2
    assert periods[("115","秋季梯次")].needs_confirmation
    assert not periods[("114","第一梯次")].needs_confirmation
    assert periods[("115","春季梯次")].source_urls==["https://example.edu/notice"]
    assert application_period_options("長庚大學",[workflow(sources=[])]).periods[0].needs_confirmation


def test_period_api_is_public_for_every_school_and_excludes_pending(tmp_path):
    store=LocalContentGovernanceStore(tmp_path)
    published=workflow()
    store.publish_workflow(published,"isolated-fixture")
    stage_workflow_refresh(store,workflow(academic_year="117",effective_application_rounds=["未發布梯次"]))
    repository=JsonlAccountRepository(tmp_path)
    client=TestClient(create_app(tmp_path,account_repository=repository,content_governance_store=store))
    guest=client.get("/application-period-options")
    assert guest.status_code==200 and "no-store" not in guest.headers.get("cache-control","")
    assert client.get("/application-period-options",params={"home_school":"國立臺北大學"}).status_code==200
    unverified=session(repository,UserAccount(display_name="未驗證"),"period-unverified")
    assert client.get("/application-period-options",headers=unverified).status_code==200
    headers=session(repository,UserAccount(display_name="已驗證",student_status_verified=True,
        verified_university="長庚大學",verified_department="資訊工程學系"),"period-verified")
    assert client.get("/application-period-options",params={"home_school":"國立臺北大學"},headers=headers).status_code==200
    response=client.get("/application-period-options",headers=headers)
    assert response.status_code==200
    assert "no-store" in response.headers["cache-control"]
    assert response.json()["home_university"]=="長庚大學"
    assert {row["academic_year"] for row in response.json()["periods"]}=={"115"}
    assert {row["application_round"] for row in response.json()["periods"]}=={"秋季梯次","春季梯次"}


@pytest.mark.parametrize("rounds,expected",[([],False),(["第一梯次"],True)])
def test_real_plan_api_projects_deadline_only_for_selected_round(tmp_path,monkeypatch,rounds,expected):
    from exchange_info.models import ApplicationSubmissionDetails
    from exchange_info.storage import ensure_data_dirs, replace_application_workflow
    from test_application_plan_api import _verified_client, _partner, _payload, _workflow
    ensure_data_dirs(tmp_path)
    partner=_partner("隔離期限校")
    source=_workflow("長庚大學",partner.school_name)
    source.application_round=None
    source.effective_application_rounds=rounds
    source.applicability_status="verified"
    source.last_checked=datetime(2026,10,1,tzinfo=timezone.utc)
    source.sources=[ApplicationWorkflowSource(title="隔離當期來源",role="home_university",
        source_url="https://example.edu/notice",effective_academic_year="116",checked_at=source.last_checked)]
    for step in source.steps:
        step.checked_at=source.last_checked
        step.submission=ApplicationSubmissionDetails(method="online",portal_url="https://example.edu/submit")
        step.deadline_at=datetime(2027,2,1,tzinfo=timezone.utc)
        step.deadline_status="verified_exact"
        step.deadline_checked_at=datetime(2026,10,1,tzinfo=timezone.utc)
        step.deadline_source_url="https://example.edu/notice"
    replace_application_workflow(source,tmp_path)
    monkeypatch.setattr("exchange_info.api.fetch_partner_universities",lambda:[partner])
    client=_verified_client(tmp_path)
    response=client.post("/application-plan/evaluate",json=_payload("長庚大學",[partner.school_name],"資訊工程學系"))
    assert response.status_code==200
    plan=response.json()
    assert len(plan['tasks'])==1
    assert bool(plan['tasks'][0]['official_deadline_at'])==expected
    check=next(row for row in plan['choices'][0]['checks'] if row['code']=='application_round')
    assert (check['status']=='pass')==expected
