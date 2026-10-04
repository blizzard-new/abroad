"""A published change is mapped onto the student's own preparation tasks."""
from fastapi.testclient import TestClient

from exchange_info.api import create_app
from exchange_info.models import ApplicationPreparationTaskState
from exchange_info.repositories import JsonlAccountRepository
from test_notification_changes import session
from test_notifications import _content_account, _published_content_store


def _changes(tmp_path, mutate=None):
    store, _ = _published_content_store(tmp_path / "content")
    student = _content_account()
    student.application_workspaces[0].application_context.application_round = "第一梯次"
    if mutate:
        mutate(student)
    repository = JsonlAccountRepository(tmp_path / "accounts")
    headers = session(repository, student, "student-impact")
    client = TestClient(create_app(tmp_path / "app", account_repository=repository, content_governance_store=store))
    notification = client.get("/account/notifications", headers=headers).json()["items"][0]
    response = client.get(f"/account/notifications/{notification['id']}/changes", headers=headers)
    assert response.status_code == 200
    return response.json()


def test_changed_step_maps_to_old_and_new_task_without_touching_progress(tmp_path):
    result = _changes(tmp_path)
    assert result["affected_tasks"], result
    row = result["affected_tasks"][0]
    assert row["step_key"] == "eligibility" and row["change_type"] == "changed"
    assert row["previous_task_id"].startswith("application-task-")
    assert row["current_task_id"].startswith("application-task-")
    assert row["previous_task_id"] != row["current_task_id"]
    assert row["action"] == "review_progress"
    assert "標題" in row["changed_fields"]
    assert result["step_changes"][0]["step_key"] == "eligibility"


def test_completed_old_task_is_flagged_for_recheck_and_kept(tmp_path):
    first = _changes(tmp_path / "a")
    old_id = first["affected_tasks"][0]["previous_task_id"]

    def finish(student):
        workspace = student.application_workspaces[0]
        workspace.preparation_tasks[old_id] = ApplicationPreparationTaskState(
            status="ready", effort_hours=3, waiting_reason="等系辦回覆"
        )

    result = _changes(tmp_path / "b", finish)
    row = result["affected_tasks"][0]
    assert row["previous_status"] == "ready"
    assert row["action"] == "recheck_completed"
    assert row["has_personal_settings"] is True
    assert "不會被刪除" in row["guidance"]


def test_no_affected_tasks_when_plan_no_longer_matches(tmp_path):
    store, _ = _published_content_store(tmp_path / "content")
    student = _content_account()
    student.application_workspaces[0].application_context.application_round = "第一梯次"
    repository = JsonlAccountRepository(tmp_path / "accounts")
    headers = session(repository, student, "student-impact")
    client = TestClient(create_app(tmp_path / "app", account_repository=repository, content_governance_store=store))
    notification = client.get("/account/notifications", headers=headers).json()["items"][0]
    student.application_workspaces[0].application_context.academic_year = "117"
    repository.save_account(student)
    result = client.get(f"/account/notifications/{notification['id']}/changes", headers=headers).json()
    assert result["matches_current_plan"] is False
    assert result["affected_tasks"] == []
