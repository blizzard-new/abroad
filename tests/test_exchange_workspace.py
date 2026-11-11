"""Personal preparation must not become a school decision or cross plan owners."""
from io import BytesIO

import pytest
from docx import Document
from pydantic import ValidationError

from exchange_info.exchange_workspace import NoticePreview, preview_notice, suggestion_packs
from test_application_path import CONTEXT, client, create


def task(name="準備文件", **changes):
    return {"id": "task_abcdefgh", "title": name, **changes}


def save(client, plan, tasks, **changes):
    return client.put(f'/account/application-paths/{plan["plan"]["id"]}/workspace',
        params={"home_school": CONTEXT["home_school"]}, headers={"Authorization": "alice"},
        json={"revision": plan["revision"], "tasks": tasks, **changes})


def url(plan, suffix=""):
    return f'/account/application-paths/{plan["plan"]["id"]}/workspace{suffix}'


def test_two_batches_keep_their_own_dates_sources_and_signers():
    preview = preview_notice(NoticePreview(source_label="接收校通知", text=
        "第一批：2027/1/10 前請回傳家長簽名同意書至國際處。\n第二批：2027/2/10 前請上傳體檢報告。"))
    assert [row["candidate_date"] for row in preview["items"]] == ["2027-01-10", "2027-02-10"]
    first, second = [row["task"] for row in preview["items"]]
    assert (first["batch"], second["batch"]) == ("第一批", "第二批")
    assert first["signers"] == "家長"
    assert first["date_kind"] == "unknown" and first["due_date"] is None
    assert "2027/1/10" in first["source_excerpt"] and preview["requires_review"]


@pytest.mark.parametrize("text,expected", [
    ("2027/1/9 前請繳交申請書", "2027-01-09"),
    ("116年1月9日前請繳交申請書", "2027-01-09"),
    ("1. 請於 2027-01-09 前提交文件", "2027-01-09"),
    ("1/9 前請繳交申請書", None),
    ("明天請繳交申請書", None),
    ("請於2027/2/30前提交", None),
    ("請於2027/1/9或2027/2/9繳交申請書", None),
])
def test_notice_dates_are_candidates_without_guessing_years(text, expected):
    row = preview_notice(NoticePreview(text=text, source_label="通知"))["items"][0]
    assert row["candidate_date"] == expected
    assert row["task"]["due_date"] is None
    if expected is None:
        assert row["warnings"]


def test_batch_header_date_applies_only_with_its_original_excerpt():
    rows = preview_notice(NoticePreview(source_label="通知", text="第一批 2027/1/10\n請上傳履歷\n第二批日期另行通知\n請上傳體檢報告"))["items"]
    assert len(rows) == 2
    cv = next(r for r in rows if "履歷" in r["task"]["title"])
    health = next(r for r in rows if "體檢" in r["task"]["title"])
    assert cv["candidate_date"] == "2027-01-10" and "第一批" in cv["task"]["source_excerpt"]
    assert health["candidate_date"] is None
    rows = preview_notice(NoticePreview(source_label="通知", text="第一批 2027/1/10\n請於2/10補交體檢報告"))["items"]
    assert rows[0]["candidate_date"] is None


def test_link_validation_rejects_executable_and_credential_urls():
    for value in ["javascript:alert(1)", "data:text/html,test", "https://user:pass@example.com/"]:
        with pytest.raises(ValidationError):
            NoticePreview(text="請提交資料", source_label="通知", source_url=value)


def test_saved_work_is_owner_and_semester_bound_and_does_not_change_official_progress(client):
    first = create(client).json()
    saved = save(client, first, [task(optional=True, kind="travel", notes="我的行程構想", status="done")]).json()
    assert saved["progress"] == first["progress"]
    assert saved["workspace"]["tasks"][0]["optional"]
    private = client.get(f'/account/application-paths/{first["plan"]["id"]}', params={"home_school": CONTEXT["home_school"]}, headers={"Authorization":"bob"})
    assert private.status_code == 404
    other = create(client, semester="spring", revision=saved["revision"]).json()
    assert other["workspace"]["tasks"] == []
    original = client.get(f'/account/application-paths/{first["plan"]["id"]}', params={"home_school": CONTEXT["home_school"]}, headers={"Authorization":"alice"}).json()
    assert original["workspace"]["tasks"][0]["notes"] == "我的行程構想"


def test_conflict_and_archived_plan_do_not_accept_writes(client):
    plan = create(client).json()
    saved = save(client, plan, [task()]).json()
    assert save(client, plan, [task("過時內容")]).status_code == 409
    archived = client.put(f'/account/application-paths/{plan["plan"]["id"]}/archive', params={"home_school":CONTEXT["home_school"]}, headers={"Authorization":"alice"}, json={"revision":saved["revision"],"archived":True}).json()
    assert save(client, archived, []).status_code == 409


def test_notice_deadline_requires_a_reviewed_source_and_personal_dates_stay_personal(client):
    plan = create(client).json()
    t = task(due_date="2027-01-10", date_kind="notice")
    assert save(client, plan, [t]).status_code == 422
    t.update(source_label="老師來信", source_excerpt="請於 2027/1/10 繳交", date_reviewed=True)
    saved = save(client, plan, [t]).json()
    assert saved["workspace"]["tasks"][0]["date_kind"] == "notice"
    assert all(not level.get("deadline_confirmed") for s in saved["stages"] for level in s["levels"])
    t.update(date_kind="personal", date_reviewed=False, source_excerpt="", source_label="")
    assert save(client, saved, [t]).json()["workspace"]["tasks"][0]["date_kind"] == "personal"


def test_preparation_can_start_but_submission_waits_and_reopening_invalidates_completion(client):
    plan = create(client).json()
    a = task("等待提名", id="task_parent1")
    b = task("先準備文件", id="task_prepare", depends_on=[a["id"]], action="prepare", status="doing")
    c = task("正式送件", id="task_submit1", depends_on=[a["id"]], action="submit", status="done")
    assert save(client, plan, [a,b,c]).status_code == 422
    c["status"] = "todo"
    saved = save(client, plan, [a,b,c]).json()
    assert saved["workspace"]["tasks"][1]["effective_status"] == "doing"
    a["status"] = c["status"] = "done"
    saved = save(client, saved, [a,b,c]).json()
    assert saved["workspace"]["tasks"][2]["effective_status"] == "done"
    a["status"] = "todo"
    saved = save(client, saved, [a,b,c]).json()
    assert saved["workspace"]["tasks"][2]["effective_status"] == "waiting"


def test_cycles_missing_dependencies_and_waiting_completion_are_rejected(client):
    plan = create(client).json()
    a = task(id="task_parent1", depends_on=["task_child01"])
    b = task(id="task_child01", depends_on=["task_parent1"])
    for rows in ([a], [a,b], [task(status="done", waiting_for="還在等老師")], [task(),task()]):
        assert save(client, plan, rows).status_code == 422


def test_course_planning_totals_credits_and_reports_only_actual_time_overlaps(client):
    plan = create(client).json()
    def course(id, day, start, end):
        return task(id=id, kind="course", stage="abroad", course={"credits":3,"weekday":day,"start":start,"end":end})
    rows = [course("course_aaaa",1,"09:00","11:00"),course("course_bbbb",1,"10:00","12:00"),course("course_cccc",2,"10:00","12:00")]
    saved = save(client, plan, rows, credit_goal=9).json()["workspace"]
    assert saved["credits"] == 9 and saved["credit_goal"] == 9
    assert saved["course_conflicts"] == [["course_aaaa","course_bbbb"]]
    assert save(client, plan, [course("course_dddd",1,"12:00","10:00")]).status_code == 422


def test_notice_preview_and_extraction_do_not_save_tasks_or_original_files(client):
    plan = create(client).json()
    kwargs={"params":{"home_school":CONTEXT["home_school"]},"headers":{"Authorization":"alice"}}
    result = client.post(url(plan,"/preview"), json={"text":"請交申請書","source_label":"老師通知"}, **kwargs)
    assert result.status_code == 200
    assert client.post(url(plan,"/extract"), files={"file":("note.txt","請交申請書".encode(),"text/plain")}, **kwargs).status_code == 422
    doc=Document();doc.add_paragraph("請於2027年1月10日回傳家長同意書");content=BytesIO();doc.save(content)
    result=client.post(url(plan,"/extract"), data={"consent":"true"},files={"file":("notice.docx",content.getvalue(),"application/octet-stream")},**kwargs)
    assert result.status_code == 200 and "家長同意書" in result.json()["text"] and not result.json()["file_stored"]
    saved=client.get(f'/account/application-paths/{plan["plan"]["id"]}',**kwargs).json()
    assert saved["workspace"]["tasks"] == [] and saved["revision"] == plan["revision"]
    assert client.post(url(plan,"/extract"), data={"consent":"true"},files={"file":("bad.docx",b"broken","application/octet-stream")},**kwargs).status_code == 422


def test_general_packs_follow_the_target_and_keep_optional_goals_optional():
    result=suggestion_packs({**CONTEXT,"target_school":"目標大學乙"},"日本")
    packs={p["id"]:p for p in result["packs"]}
    assert packs["destination"]["title"].startswith("日本")
    assert all(t["due_date"] is None for p in result["packs"] for t in p["tasks"])
    assert any("目標大學乙" in t["notes"] for t in packs["interview"]["tasks"])
    assert all(t["optional"] for k in ("travel","internship","community") for t in packs[k]["tasks"])
    assert all("待人工審核" in t["source_label"] for t in packs["destination"]["tasks"])


@pytest.mark.parametrize("invalidity", ["removed", "expired"])
def test_document_links_check_owner_expiry_and_dependent_completion(client, tmp_path, monkeypatch, invalidity):
    from datetime import timedelta
    from exchange_info.document_vault import DocumentVaultService, LocalDocumentVaultRepository
    from exchange_info.models import VaultConsentPurpose, VaultDocumentCategory, utc_now
    vault = DocumentVaultService(LocalDocumentVaultRepository(tmp_path / "vault"), b"v" * 32)
    client.app.state.document_vault_service = vault
    client.app.state.path_feature = True
    def upload(owner):
        return vault.store_version(owner, file_name="draft.txt", content=b"synthetic test only",
            media_type="text/plain", label="測試文件", category=VaultDocumentCategory.OTHER,
            purpose=VaultConsentPurpose.APPLICATION_PREPARATION, retention_days=30, consent=True)
    foreign, owned = upload("bob"), upload("alice")
    plan = create(client).json()
    document = task(kind="document", file_version_id=foreign.versions[0].id, status="done")
    assert save(client, plan, [document]).status_code == 404
    document["file_version_id"] = owned.versions[0].id
    submission = task("送件紀錄", id="task_submit1", action="submit", status="done", depends_on=[document["id"]])
    saved = save(client, plan, [document, submission]).json()
    if invalidity == "removed":
        vault.delete_document("alice", owned.id)
    else:
        future = utc_now() + timedelta(days=31)
        monkeypatch.setattr("exchange_info.application_path.utc_now", lambda: future)
    loaded = client.get(f'/account/application-paths/{plan["plan"]["id"]}',
        params={"home_school":CONTEXT["home_school"]}, headers={"Authorization":"alice"}).json()
    assert loaded["workspace"]["tasks"][0]["file_unavailable"]
    assert all(t["effective_status"] == "waiting" for t in loaded["workspace"]["tasks"])
    assert save(client, saved, [document, submission]).status_code == 404


def test_workspace_routes_require_the_plan_owner(client):
    plan = create(client).json()
    for token, expected in [(None, 401), ("bob", 404)]:
        kwargs = {"params":{"home_school":CONTEXT["home_school"]}, "headers":{"Authorization":token} if token else {}}
        assert client.put(url(plan), json={"revision":plan["revision"],"tasks":[]}, **kwargs).status_code == expected
        assert client.post(url(plan,"/preview"), json={"source_label":"通知","text":"請交文件"}, **kwargs).status_code == expected
        assert client.get(url(plan,"/suggestions"), **kwargs).status_code == expected
