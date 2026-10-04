import hashlib
from datetime import datetime, timezone, timedelta

from fastapi.testclient import TestClient

from exchange_info.api import create_app
from exchange_info.models import (
    ApplicationRuleScope,
    ApplicationStep,
    ApplicationSupportStatus,
    ApplicationWorkflowReviewStatus,
    PartnerUniversity,
    UniversityApplicationWorkflow,
    UserAccount,
    AccountSessionRecord,
    utc_now,
)
from exchange_info.storage import (
    ensure_data_dirs,
    load_application_workflows,
    load_bundled_application_workflows,
    replace_application_workflow,
    save_user_accounts,
    save_account_sessions,
)


def _verified_client(data_dir, home_school="長庚大學"):
    account = UserAccount(id="plan-student", display_name="清單測試學生", email_verified=True,
        student_status_verified=True, verified_university=home_school, home_university=home_school)
    token = "isolated-plan-test-token"
    save_user_accounts([account], data_dir)
    save_account_sessions([AccountSessionRecord(account_id=account.id,
        token_hash=hashlib.sha256(token.encode()).hexdigest(), expires_at=utc_now()+timedelta(days=1))], data_dir)
    return TestClient(create_app(data_dir), headers={"Authorization":f"Bearer {token}"})


def _partner(
    school_name: str,
    *,
    availability_status: str = "open",
) -> PartnerUniversity:
    return PartnerUniversity(
        program_type="交換學生",
        availability_status=availability_status,
        availability_note=(
            "只有合作備查，本期未公告名額。"
            if availability_status == "agreement_only"
            else None
        ),
        country="日本",
        school_name=school_name,
        colleges="工學院、法律學系",
        degree_levels="大學部",
        eligibility="IELTS 6.0",
        source_url="https://example.edu/official-partners",
    )


def _workflow(home_school: str, school_name: str) -> UniversityApplicationWorkflow:
    checked_at = datetime(2026, 7, 29, tzinfo=timezone.utc)
    return UniversityApplicationWorkflow(
        workflow_id=f"{home_school}-{school_name}",
        home_university=home_school,
        school_name=school_name,
        academic_year="116",
        application_round="第一梯次",
        review_status=ApplicationWorkflowReviewStatus.PUBLISHED,
        published_at=checked_at,
        coverage_status="official_verified",
        steps=[
            ApplicationStep(
                rule_id="submit",
                order=1,
                phase="校內申請",
                title="依校級流程送件",
                responsible_party="學生",
                responsible_unit=f"{home_school}國際事務處",
                summary="依校級公告送件。",
                support_status=ApplicationSupportStatus.VERIFIED,
                source_urls=["https://example.edu/official-flow"],
            ),
            ApplicationStep(
                overrides_rule_id="submit",
                order=1,
                phase="校內申請",
                title="資工系紙本送件",
                responsible_party="學生",
                responsible_unit="資訊工程學系系辦",
                summary="列印後交給資訊工程學系系辦。",
                support_status=ApplicationSupportStatus.VERIFIED,
                scope=ApplicationRuleScope(departments=["資訊工程學系"]),
                source_urls=["https://example.edu/cs-flow"],
            ),
            ApplicationStep(
                overrides_rule_id="submit",
                order=1,
                phase="校內申請",
                title="法律系親送系辦",
                responsible_party="學生",
                responsible_unit="法律學系系辦",
                summary="親送法律學系系辦。",
                support_status=ApplicationSupportStatus.VERIFIED,
                scope=ApplicationRuleScope(departments=["法律學系"]),
                source_urls=["https://example.edu/law-flow"],
            ),
        ],
    )


def _payload(home_school: str, school_names: list[str], department: str) -> dict:
    return {
        "home_school": home_school,
        "college": "工學院" if department == "資訊工程學系" else "法律學院",
        "department": department,
        "degree_level": "大學部",
        "academic_score": 85,
        "language_test": "ielts",
        "language_score": 6.5,
        "academic_year": "116",
        "application_round": "第一梯次",
        "preferences": [
            {"rank": rank, "school_name": school_name}
            for rank, school_name in enumerate(school_names, start=1)
        ],
    }


def test_application_plan_api_applies_department_override_and_multiple_preferences(
    tmp_path,
    monkeypatch,
) -> None:
    ensure_data_dirs(tmp_path)
    open_partner = _partner("開放合作校")
    closed_partner = _partner("備查合作校", availability_status="agreement_only")
    replace_application_workflow(_workflow("長庚大學", open_partner.school_name), tmp_path)
    monkeypatch.setattr(
        "exchange_info.api.fetch_partner_universities",
        lambda: [open_partner, closed_partner],
    )
    client = _verified_client(tmp_path)

    response = client.post(
        "/application-plan/evaluate",
        json=_payload(
            "長庚大學",
            [open_partner.school_name, closed_partner.school_name],
            "資訊工程學系",
        ),
    )

    assert response.status_code == 200
    choices = response.json()["choices"]
    assert [choice["rank"] for choice in choices] == [1, 2]
    assert choices[0]["checklist"][0]["title"] == "資工系紙本送件"
    assert choices[1]["status"] == "unavailable"
    assert choices[1]["checklist"] == []
    assert response.json()["contact_unit"] == "長庚大學國際事務處／所屬系所"


def test_application_plan_api_uses_the_other_department_rule(tmp_path, monkeypatch) -> None:
    ensure_data_dirs(tmp_path)
    partner = _partner("共同合作校")
    replace_application_workflow(_workflow("長庚大學", partner.school_name), tmp_path)
    monkeypatch.setattr("exchange_info.api.fetch_partner_universities", lambda: [partner])
    client = _verified_client(tmp_path)

    response = client.post(
        "/application-plan/evaluate",
        json=_payload("長庚大學", [partner.school_name], "法律學系"),
    )

    assert response.status_code == 200
    assert response.json()["choices"][0]["checklist"][0]["title"] == "法律系親送系辦"


def test_application_plan_api_supports_ntpu_and_marks_missing_values_for_confirmation(
    tmp_path,
    monkeypatch,
) -> None:
    ensure_data_dirs(tmp_path)
    partner = _partner("臺北大學合作校")
    replace_application_workflow(_workflow("國立臺北大學", partner.school_name), tmp_path)
    monkeypatch.setattr(
        "exchange_info.api.fetch_ntpu_partner_universities",
        lambda: [partner],
    )
    client = _verified_client(tmp_path, "國立臺北大學")

    response = client.post(
        "/application-plan/evaluate",
        json={
            "home_school": "國立臺北大學",
            "academic_year": "116",
            "application_round": "第一梯次",
            "preferences": [{"rank": 1, "school_name": partner.school_name}],
        },
    )

    assert response.status_code == 200
    choice = response.json()["choices"][0]
    assert choice["status"] == "needs_confirmation"
    confirmation_checks = [
        check for check in choice["checks"] if check["status"] == "needs_confirmation"
    ]
    assert {check["code"] for check in confirmation_checks} >= {
        "college",
        "degree_level",
        "academic_score",
        "language_score",
    }
    assert all(check["contact_unit"] for check in confirmation_checks)


def test_application_plan_api_rejects_duplicate_or_unknown_preferences(
    tmp_path,
    monkeypatch,
) -> None:
    ensure_data_dirs(tmp_path)
    partner = _partner("唯一合作校")
    monkeypatch.setattr("exchange_info.api.fetch_partner_universities", lambda: [partner])
    client = _verified_client(tmp_path)
    payload = _payload("長庚大學", [partner.school_name], "資訊工程學系")
    payload["preferences"] = [
        {"rank": 1, "school_name": partner.school_name},
        {"rank": 2, "school_name": partner.school_name},
    ]

    duplicate = client.post("/application-plan/evaluate", json=payload)
    assert duplicate.status_code == 422

    payload["preferences"] = [{"rank": 1, "school_name": "不存在的學校"}]
    unknown = client.post("/application-plan/evaluate", json=payload)
    assert unknown.status_code == 422
    assert "目前支援的合作校名單" in unknown.json()["detail"]


def test_application_plan_api_uses_bundled_workflow_with_isolated_runtime_data(
    tmp_path,
    monkeypatch,
) -> None:
    ensure_data_dirs(tmp_path)
    workflow = next(
        row
        for row in load_bundled_application_workflows()
        if row.home_university == "長庚大學" and row.steps
    )
    partner = _partner(workflow.school_name)
    monkeypatch.setattr("exchange_info.api.fetch_partner_universities", lambda: [partner])
    client = _verified_client(tmp_path)

    payload = _payload("長庚大學", [partner.school_name], "資訊工程學系")
    payload["academic_year"] = workflow.academic_year
    payload["application_round"] = workflow.application_round
    response = client.post(
        "/application-plan/evaluate",
        json=payload,
    )

    assert response.status_code == 200
    choice = response.json()["choices"][0]
    assert choice["workflow_coverage_status"] != "not_collected"
    assert choice["checklist"]
    assert load_application_workflows(tmp_path) == []
