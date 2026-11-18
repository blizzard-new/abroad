import hashlib
from datetime import timedelta

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from exchange_info.api import create_app
from exchange_info.application_path import REGISTRY_ID, build_levels, register_application_path
from exchange_info.form_drafts import FormDraftService, LocalFormDraftRepository
from exchange_info.models import (AccountSessionRecord, ApplicationDocumentCatalog,
    ApplicationCenterContext, PersonalApplicationPlanResult, ProductReleaseMode,
    UserAccount, utc_now)
from exchange_info.storage import save_account_sessions, save_user_accounts


CONTEXT = dict(home_school="國立臺北大學", target_school="合作學校甲", academic_year="116",
               application_round="第一梯次", departure_year="2027", semester="fall")


def result(target="合作學校甲"):
    return PersonalApplicationPlanResult.model_validate(dict(home_school="國立臺北大學", contact_unit="國際處",
        choices=[dict(rank=1, school_name=target, status="needs_confirmation", summary="待確認",
            workflow_coverage_status="partial", checks=[dict(code="college", status="needs_confirmation", title="院系資格", detail="請確認院系")],
            checklist=[dict(id="task-one", order=1, phase="校內準備", title="核對資料", detail="先核對內容", responsible_unit="國際處", support_status="needs_confirmation"),
                       dict(id="task-two", order=2, phase="校內申請", title="提交申請", detail="前往官方系統", responsible_unit="國際處", support_status="needs_confirmation", dependency_ids=["task-one"]),
                       dict(id="notice", order=3, phase="審查", title="記錄提名通知", detail="收到通知再填寫", responsible_unit="國際處", support_status="needs_confirmation")])]))


@pytest.fixture
def client(tmp_path):
    app = FastAPI()
    app.state.form_draft_service = FormDraftService(LocalFormDraftRepository(tmp_path), b"k"*32)
    accounts = {key:UserAccount(id=key, display_name=key) for key in ("alice", "bob")}
    def authenticate(request):
        from fastapi import HTTPException
        key = request.headers.get("Authorization")
        if key not in accounts:
            raise HTTPException(401)
        return accounts[key], None
    app.state.path_catalog = ApplicationDocumentCatalog(context=ApplicationCenterContext(school_name=CONTEXT["home_school"]), contact_unit="國際處")
    app.state.path_feature = False
    app.state.path_evaluate = lambda request:result(request.preferences[0].school_name)
    register_application_path(app, authenticate=authenticate,
        university_for=lambda home:type("University", (), {"school_name":home})(),
        evaluate=lambda request:app.state.path_evaluate(request),
        catalog_for=lambda **kwargs:app.state.path_catalog,
        release_mode=lambda:ProductReleaseMode.PUBLIC, feature_enabled=lambda *args:app.state.path_feature)
    app.state.test_accounts = accounts
    return TestClient(app)


def create(client, **changes):
    return client.post("/account/application-paths", headers={"Authorization":"alice"},
                       json={**CONTEXT, "revision":0, **changes})


def update(client, plan, step, data, revision=None, owner="alice"):
    return client.put(f'/account/application-paths/{plan["plan"]["id"]}/steps/{step}',
        params={"home_school":CONTEXT["home_school"]}, headers={"Authorization":owner},
        json={"revision":revision or plan["revision"], "step":data})


def test_auth_owner_persistence_and_compare_and_set(client):
    assert client.get("/account/application-paths", params={"home_school":CONTEXT["home_school"]}).status_code == 401
    created = create(client)
    assert created.status_code == 201, created.text
    p = created.json()
    assert update(client, p, "home", {"confirmed":True}, owner="bob").status_code == 404
    saved = update(client, p, "home", {"confirmed":True})
    assert saved.status_code == 200, saved.text
    assert saved.json()["progress"]["value"] == 0
    assert update(client, p, "target", {"confirmed":True}).status_code == 409
    loaded = client.get(f'/account/application-paths/{p["plan"]["id"]}', params={"home_school":CONTEXT["home_school"]}, headers={"Authorization":"alice"}).json()
    assert loaded["plan"]["steps"]["home"]["confirmed"]
    assert loaded["revision"] == 2
    assert client.app.state.form_draft_service.list_drafts("alice", CONTEXT["home_school"]).items == []
    raw = client.app.state.form_draft_service.repository.find_record("alice", CONTEXT["home_school"], REGISTRY_ID)
    assert "合作學校甲" not in raw.ciphertext


def test_terms_isolated_and_duplicate_create_is_idempotent(client):
    a = create(client).json()
    b = create(client, revision=1, semester="spring").json()
    assert a["plan"]["id"] != b["plan"]["id"]
    saved = update(client, a, "home", {"confirmed":True}, revision=2).json()
    again = create(client).json()
    assert again["plan"]["id"] == a["plan"]["id"]
    assert again["revision"] == saved["revision"]
    other = client.get(f'/account/application-paths/{b["plan"]["id"]}', params={"home_school":CONTEXT["home_school"]}, headers={"Authorization":"alice"}).json()
    assert other["plan"]["steps"] == {}
    assert create(client, revision=3, target_school="合作學校乙").status_code == 403


def test_dependencies_and_official_status_cannot_be_forged(client):
    p = create(client).json()
    assert update(client, p, "task-two", {"value":"已送件", "confirmed":True}).status_code == 422
    assert update(client, p, "notice", {"value":"通知", "confirmed":True}).status_code == 422
    assert update(client, p, "unknown", {"confirmed":True}).status_code == 422
    assert update(client, p, "home", {"official_status":"accepted"}).status_code == 422
    p = update(client, p, "task-one", {"value":"已核對", "confirmed":True}).json()
    p = update(client, p, "task-two", {"value":"已送件", "confirmed":True}).json()
    previous = p["progress"]
    p = update(client, p, "notice", {"value":"收到提名信"}).json()
    assert p["progress"] == previous
    assert p["recorded_by"] == "student" and p["platform_submitted"] is False


def test_archive_keeps_data_and_blocks_accidental_writes(client):
    p = create(client).json()
    response = client.put(f'/account/application-paths/{p["plan"]["id"]}/archive',
        params={"home_school":CONTEXT["home_school"]}, headers={"Authorization":"alice"},
        json={"revision":1,"archived":True})
    assert response.status_code == 200
    p = response.json()
    assert update(client, p, "home", {"confirmed":True}).status_code == 409
    assert create(client, revision=2, target_school="合作學校乙").status_code == 201


@pytest.mark.parametrize("origin,uncertain,confirmed", [
    ("official", False, True), ("official", True, False), ("reference_year", False, False),
])
def test_only_confirmed_current_rules_can_drive_deadline_priority(origin, uncertain, confirmed):
    evaluated = result()
    task = evaluated.choices[0].checklist[0]
    task.official_deadline_at = utc_now() + timedelta(days=3)
    task.task_origin = origin
    task.needs_confirmation = uncertain
    catalog = ApplicationDocumentCatalog(context=ApplicationCenterContext(school_name=CONTEXT["home_school"]), contact_unit="國際處")
    stages = build_levels(CONTEXT, evaluated, catalog)
    item = next(l for s in stages for l in s['levels'] if l['id'] == task.id)
    assert item['deadline_confirmed'] is confirmed
    assert item['official_deadline_at'] == task.official_deadline_at.isoformat()


def test_real_app_uses_existing_sessions_and_protects_internal_storage(tmp_path):
    account = UserAccount(display_name="隔離測試")
    token = "application-path-test-session"
    save_user_accounts([account], tmp_path)
    save_account_sessions([AccountSessionRecord(account_id=account.id,
        token_hash=hashlib.sha256(token.encode()).hexdigest(), expires_at=utc_now()+timedelta(days=1))], tmp_path)
    c = TestClient(create_app(tmp_path))
    headers = {"Authorization":"Bearer "+token}
    response = c.get("/account/application-paths", params={"home_school":"國立臺北大學"}, headers=headers)
    assert response.status_code == 200, response.text
    assert "no-store" in response.headers["cache-control"]
    assert response.json()["items"] == []
    assert c.put(f"/account/application-drafts/{REGISTRY_ID}", headers=headers,
                 json={"home_school":"國立臺北大學","template_version":"1"}).status_code == 422
    assert c.delete(f"/account/application-drafts/{REGISTRY_ID}", headers=headers,
                    params={"home_school":"國立臺北大學","revision":1}).status_code == 422


def doc_catalog(client, *, conditional=False):
    from exchange_info.models import ApplicationDocumentCatalogItem
    client.app.state.path_catalog.items = [ApplicationDocumentCatalogItem(
        id="study-plan", sequence=1, phase="文件準備", step_title="核對文件", name="研修計畫書",
        support_status="needs_confirmation", conditional=conditional,
        source_urls=["https://example.edu/requirements"])]


def test_undoing_prerequisite_invalidates_dependent_completion(client):
    p = create(client).json()
    p = update(client, p, "task-one", {"value":"核對", "confirmed":True}).json()
    p = update(client, p, "task-two", {"value":"送件", "confirmed":True}).json()
    p = update(client, p, "task-one", {"value":"需重新檢查", "confirmed":False}).json()
    item = next(l for s in p["stages"] for l in s["levels"] if l["id"] == "task-two")
    assert item["blocked_by"] == ["task-one"]
    assert item["progress"] == {"value":1,"total":2}
    assert p["plan"]["steps"]["task-two"]["value"] == "送件"


def test_conditional_documents_and_saved_word_export(client):
    import io
    from docx import Document
    doc_catalog(client, conditional=True)
    p = create(client).json()
    item = next(l for s in p["stages"] for l in s["levels"] if l["kind"] == "file")
    initial = p["progress"]["total"]
    assert item["counted"] is False
    assert update(client, p, item["id"], {"value":"文件", "confirmed":True}).status_code == 422
    p = update(client, p, item["id"], {"applicable":False}).json()
    assert p["progress"]["total"] == initial
    p = update(client, p, item["id"], {"applicable":True,"value":"自行保管", "confirmed":True}).json()
    assert p["progress"]["total"] == initial + 2
    p = update(client, p, "motivation", {"value":"我的獨立研修草稿", "confirmed":True}).json()
    url = f'/account/application-paths/{p["plan"]["id"]}/writing.docx'
    params = {"home_school":CONTEXT["home_school"]}
    assert client.get(url, params=params, headers={"Authorization":"bob"}).status_code == 404
    exported = client.get(url, params=params, headers={"Authorization":"alice"})
    assert exported.status_code == 200
    assert "我的獨立研修草稿" in "\n".join(p.text for p in Document(io.BytesIO(exported.content)).paragraphs)


@pytest.mark.parametrize("invalidity", ["removed", "expired"])
def test_linked_vault_owner_expiry_and_removal(client, tmp_path, monkeypatch, invalidity):
    from exchange_info.document_vault import DocumentVaultService, LocalDocumentVaultRepository
    from exchange_info.models import VaultConsentPurpose, VaultDocumentCategory
    doc_catalog(client)
    client.app.state.path_feature = True
    vault = DocumentVaultService(LocalDocumentVaultRepository(tmp_path / "vault"), b"v"*32)
    client.app.state.document_vault_service = vault
    def upload(owner):
        return vault.store_version(owner, file_name="draft.txt", content=b"synthetic review only",
            media_type="text/plain", label="測試文件", category=VaultDocumentCategory.OTHER,
            purpose=VaultConsentPurpose.APPLICATION_PREPARATION, retention_days=30, consent=True)
    foreign = upload("bob")
    owned = upload("alice")
    p = create(client).json()
    step = next(l["id"] for s in p["stages"] for l in s["levels"] if l["kind"] == "file")
    assert update(client, p, step, {"version_id":foreign.versions[0].id,"confirmed":True}).status_code == 404
    p = update(client, p, step, {"version_id":owned.versions[0].id,"confirmed":True}).json()
    before = p["progress"]["value"]
    if invalidity == "removed":
        vault.delete_document("alice", owned.id)
    else:
        future = utc_now() + timedelta(days=31)
        monkeypatch.setattr("exchange_info.application_path.utc_now", lambda:future)
    loaded = client.get(f'/account/application-paths/{p["plan"]["id"]}', params={"home_school":CONTEXT["home_school"]}, headers={"Authorization":"alice"}).json()
    item = next(l for s in loaded["stages"] for l in s["levels"] if l["id"] == step)
    assert item["file_unavailable"]
    assert loaded["progress"]["value"] == before - 2
    assert loaded["plan"]["steps"][step]["version_id"] == owned.versions[0].id


def test_legacy_import_requires_exact_context_and_does_not_overwrite(client):
    from exchange_info.models import AccountApplicationWorkspace
    old = AccountApplicationWorkspace(home_school=CONTEXT["home_school"], revision=7,
        application_context=ApplicationCenterContext(school_name=CONTEXT["home_school"], **{k:v for k,v in CONTEXT.items() if k not in {"home_school","departure_year"}}),
        preparation_tasks={"task-one":{"status":"ready"},"notice":{"status":"ready"}})
    client.app.state.test_accounts["alice"].application_workspaces = [old]
    assert create(client, semester="spring", import_existing=True).status_code == 422
    p = create(client, import_existing=True).json()
    assert p["plan"]["steps"]["task-one"]["confirmed"]
    assert "notice" not in p["plan"]["steps"]
    assert old.revision == 7
    assert old.preparation_tasks["task-one"].status == "ready"


def test_failed_persistence_does_not_report_completion(client, monkeypatch):
    from exchange_info.form_drafts import FormDraftError
    p = create(client).json()
    def unavailable(*args, **kwargs):
        raise FormDraftError("storage unavailable")
    monkeypatch.setattr(client.app.state.form_draft_service, "save_draft", unavailable)
    response = update(client, p, "home", {"confirmed":True})
    assert response.status_code == 503
    loaded = client.get(f'/account/application-paths/{p["plan"]["id"]}', params={"home_school":CONTEXT["home_school"]}, headers={"Authorization":"alice"}).json()
    assert loaded["plan"]["steps"] == {}
    assert loaded["progress"]["value"] == 0


def test_rule_check_levels_expose_the_status_the_student_must_see(client):
    plan = create(client).json()
    levels = {l["id"]: l for s in plan["stages"] for l in s["levels"]}
    assert levels["check-college"]["check_status"] == "needs_confirmation"
    assert all("check_status" not in l for key, l in levels.items() if not key.startswith("check-"))


def gated_result(request):
    """Judges the way the real rules do: a gate stays open until the student has supplied what it reads."""
    checks = [
        dict(code="college", status="pass" if request.college and request.department else "needs_confirmation",
             title="學院／學系範圍", detail="尚未提供學院或學系，無法套用合作校範圍。"),
        dict(code="home_language_score", title="語言成績",
             status=("pass" if (request.language_score or 0) >= 600 else "fail") if request.language_test and request.language_score is not None else "needs_confirmation",
             detail="校內語言門檻：多益 600。" if request.language_score is not None else "尚未填寫語言檢定成績。校內語言門檻：多益 600。"),
        dict(code="academic_score", title="學業成績",
             status="pass" if request.academic_score is not None else "needs_confirmation",
             detail="尚未提供學業平均；公開基本門檻為 70 分。"),
        dict(code="degree_level", title="學制與學籍", status="needs_confirmation",
             detail="須確認在學身分、實際就讀學期，僅有學制不足以判定。"),
        dict(code="home_deadline", status="needs_confirmation", title="校內截止日", detail="待校方公告"),
    ]
    base = result(request.preferences[0].school_name).model_dump()
    base["choices"][0]["checks"] = checks
    return PersonalApplicationPlanResult.model_validate(base)


def gate_levels(plan):
    return {l["id"]: l for s in plan["stages"] for l in s["levels"]}


def save_profile(client, plan, revision=None, owner="alice", **fields):
    return client.put(f'/account/application-paths/{plan["plan"]["id"]}/profile',
        params={"home_school":CONTEXT["home_school"]}, headers={"Authorization":owner},
        json={"revision":revision or plan["revision"], **fields})


def test_a_gate_asks_for_the_data_it_lacks_and_is_judged_again_once_the_student_fills_it_in(client):
    client.app.state.path_evaluate = gated_result
    plan = create(client).json()
    gates = gate_levels(plan)
    college = gates["check-college"]
    assert college["check_status"] == "needs_confirmation"
    assert college["input_fields"] == ["college", "department"]
    assert college["missing_inputs"] == ["college", "department"]
    assert gates["check-home_language_score"]["missing_inputs"] == ["language_test", "language_score"]
    assert gates["check-academic_score"]["input_fields"]
    # A gate about a date, or one the school has not settled, is not waiting for the student: nothing to type, nothing blocks it.
    assert "input_fields" not in gates["check-home_deadline"]
    assert "input_fields" not in gates["check-degree_level"] and "missing_inputs" not in gates["check-degree_level"]
    # The score gate reads the average alone here: it does not ask for a GPA or a rank its text never mentions.
    assert gates["check-academic_score"]["input_fields"] == ["academic_score"]

    saved = save_profile(client, plan, college="管理學院", department="資訊管理學系")
    assert saved.status_code == 200, saved.text
    body = saved.json()
    after = gate_levels(body)["check-college"]
    assert after["check_status"] == "pass"
    assert after["missing_inputs"] == []
    assert after["input_values"] == {"college": "管理學院", "department": "資訊管理學系"}
    assert body["revision"] == plan["revision"] + 1
    # The plan is the same plan: what the student filled in does not create a second one.
    assert body["plan"]["id"] == plan["plan"]["id"]
    loaded = client.get(f'/account/application-paths/{plan["plan"]["id"]}', params={"home_school":CONTEXT["home_school"]},
                        headers={"Authorization":"alice"}).json()
    assert gate_levels(loaded)["check-college"]["check_status"] == "pass"
    assert len(client.get("/account/application-paths", params={"home_school":CONTEXT["home_school"]},
                          headers={"Authorization":"alice"}).json()["items"]) == 1


def test_a_language_score_is_judged_against_the_test_it_belongs_to(client):
    client.app.state.path_evaluate = gated_result
    plan = create(client).json()
    failing = save_profile(client, plan, language_test="toeic", language_score=450).json()
    gate = gate_levels(failing)["check-home_language_score"]
    assert gate["check_status"] == "fail" and gate["missing_inputs"] == []
    passing = save_profile(client, failing, language_test="toeic", language_score=720).json()
    assert gate_levels(passing)["check-home_language_score"]["check_status"] == "pass"


def test_clearing_a_value_opens_the_gate_again(client):
    client.app.state.path_evaluate = gated_result
    plan = create(client).json()
    filled = save_profile(client, plan, academic_score=82.5).json()
    assert gate_levels(filled)["check-academic_score"]["check_status"] == "pass"
    cleared = save_profile(client, filled, academic_score="")
    assert cleared.status_code == 200, cleared.text
    assert gate_levels(cleared.json())["check-academic_score"]["missing_inputs"]


def test_a_field_left_out_of_the_request_keeps_its_saved_value(client):
    client.app.state.path_evaluate = gated_result
    plan = create(client).json()
    first = save_profile(client, plan, college="管理學院", department="資訊管理學系").json()
    second = save_profile(client, first, academic_score=80).json()
    gates = gate_levels(second)
    assert gates["check-college"]["check_status"] == "pass"
    assert gates["check-academic_score"]["check_status"] == "pass"


@pytest.mark.parametrize("fields", [
    {"academic_score": 120}, {"academic_gpa": 5}, {"class_rank_percent": 0}, {"language_test": "klingon"},
    {"language_test": "toeic", "language_score": 1200}, {"language_test": "ielts", "language_score": 90},
    {"language_score": 600}, {"unknown_field": 1},
])
def test_an_impossible_value_is_refused_and_nothing_is_saved(client, fields):
    client.app.state.path_evaluate = gated_result
    plan = create(client).json()
    response = save_profile(client, plan, **fields)
    assert response.status_code == 422, response.text
    loaded = client.get(f'/account/application-paths/{plan["plan"]["id"]}', params={"home_school":CONTEXT["home_school"]},
                        headers={"Authorization":"alice"}).json()
    assert loaded["revision"] == plan["revision"]
    assert gate_levels(loaded)["check-academic_score"]["missing_inputs"]


def test_profile_is_owner_only_revision_checked_and_blocked_on_archived_plans(client):
    client.app.state.path_evaluate = gated_result
    plan = create(client).json()
    assert save_profile(client, plan, owner="bob", college="管理學院").status_code == 404
    assert client.put(f'/account/application-paths/{plan["plan"]["id"]}/profile',
        params={"home_school":CONTEXT["home_school"]}, json={"revision":plan["revision"], "college":"x"}).status_code == 401
    saved = save_profile(client, plan, college="管理學院")
    assert saved.status_code == 200
    stale = save_profile(client, plan, department="資訊管理學系")
    assert stale.status_code == 409
    archived = client.put(f'/account/application-paths/{plan["plan"]["id"]}/archive',
        params={"home_school":CONTEXT["home_school"]}, headers={"Authorization":"alice"},
        json={"revision":saved.json()["revision"], "archived":True}).json()
    assert save_profile(client, archived, department="資訊管理學系").status_code == 409


def test_a_round_chosen_at_the_gate_is_what_the_plan_is_judged_with(client):
    seen = []

    def evaluate(request):
        seen.append(request.application_round)
        base = result(request.preferences[0].school_name).model_dump()
        base["choices"][0]["checks"] = [dict(
            code="application_round", title="申請梯次", status="pass" if request.application_round else "needs_confirmation",
            detail="已套用結構化流程。" if request.application_round else "尚未選擇申請梯次，不能確認這份流程是否適用。")]
        return PersonalApplicationPlanResult.model_validate(base)

    client.app.state.path_evaluate = evaluate
    plan = create(client, application_round="").json()
    assert gate_levels(plan)["check-application_round"]["missing_inputs"] == ["application_round"]
    saved = save_profile(client, plan, application_round="第一梯次").json()
    assert gate_levels(saved)["check-application_round"]["check_status"] == "pass"
    assert seen[-1] == "第一梯次"
    assert saved["plan"]["id"] == plan["plan"]["id"]


def test_setup_steps_auto_completed_and_uncounted(client):
    plan = create(client).json()
    stage0 = plan["stages"][0]["levels"]
    assert [lvl["id"] for lvl in stage0[:3]] == ["home", "term", "target"]
    for lvl in stage0[:3]:
        assert lvl["counted"] is False
        assert lvl["progress"] == {"value": 1, "total": 1}
    assert plan["progress"]["value"] == 0


def test_round_consistency_validation_rejects_mismatched_year_or_semester(client):
    bad_year = create(
        client,
        academic_year="117",
        departure_year="2028",
        semester="fall",
        application_round="115-2（2027 春季出國）",
    )
    assert bad_year.status_code == 422

    bad_sem = create(
        client,
        academic_year="116",
        departure_year="2027",
        semester="spring",
        application_round="116-1（2027 秋季出國）",
    )
    assert bad_sem.status_code == 422

    ok_117 = create(
        client,
        academic_year="117",
        departure_year="2028",
        semester="fall",
        application_round="117-1（2028 秋季出國）",
    )
    assert ok_117.status_code == 201, ok_117.text

    ok_115 = create(
        client,
        revision=ok_117.json()["revision"],
        academic_year="115",
        departure_year="2027",
        semester="spring",
        application_round="115-2（2027 春季出國）",
    )
    assert ok_115.status_code == 201, ok_115.text



@pytest.mark.parametrize(("title", "kind"), [
    ("確認：完成臺北大學線上申請與文件上傳", "submission"),
    ("確認：完成合作校線上申請", "submission"),
    ("在長庚期限內送出校內申請", "submission"),
    ("準備申請表及成績單送達國際事務處", "submission"),
    ("於校內系統選填志願並上傳電子備審", "submission"),
    ("確認線上申請需要的文件", "note"),
    ("完成線上申請前的文件準備", "note"),
])
def test_online_application_handoff_is_distinct_from_file_preparation(title, kind):
    evaluated = result()
    evaluated.choices[0].checklist[0].title = title
    evaluated.choices[0].checklist[0].phase = "校內申請"
    catalog = ApplicationDocumentCatalog(
        context=ApplicationCenterContext(school_name=CONTEXT["home_school"]), contact_unit="國際處",
    )
    stages = build_levels(CONTEXT, evaluated, catalog)
    task = next(item for stage in stages for item in stage["levels"] if item["id"] == "task-one")
    assert task["kind"] == kind


def test_unpublished_cycle_files_keep_reference_year_and_unlisted_files_stay_personal(client):
    from exchange_info.models import TaskDocumentLink

    evaluated = result()
    prior = evaluated.choices[0].checklist[0]
    prior.task_origin = "reference_year"
    prior.reference_academic_year = "115"
    prior.source_urls = ["https://example.edu/archive/115"]
    prior.document_link = TaskDocumentLink(requirement_names=["歷年成績單", "歷年成績單"])
    client.app.state.path_evaluate = lambda _: evaluated

    def file_steps():
        data = create(client).json()
        return [item for stage in data["stages"] for item in stage["levels"] if item["kind"] == "file"]

    reference, = file_steps()
    assert reference["document_basis"] == "reference_year"
    assert "115 學年度" in reference["title"] and "歷年成績單" in reference["title"]
    assert reference["source_urls"] == prior.source_urls
    assert reference["counted"] is False

    prior.document_link = None
    personal, = file_steps()
    assert personal["document_basis"] == "personal" and personal["counted"] is False
    assert personal["source_urls"] == prior.source_urls
    assert personal["id"] != reference["id"]


@pytest.mark.parametrize(('title', 'actor', 'expected'), [
    ('預估：完成系主任、院長、註冊組與生輔組審查流程表核章，於收件截止前送交申請表件', '學生、所屬系所與學院、教務處註冊組、國際暨兩岸事務處', 'submission'),
    ('於中山大學出國交換學生甄選系統完成線上填報與審查文件上傳', '學生', 'submission'),
    ('取得導師／指導教授與系所主管核章並於出國計畫線上申請系統上傳應繳文件', '學生與系所主管', 'submission'),
    ('完成線上報名（09/16–09/24）並於 10/05–11/02 上傳 iNCCU 全人系統登錄截圖暨語言檢定證明', '學生', 'submission'),
    ('登入出國交換學生申請系統填報志願並送系所初審', '學生與所屬系科所辦公室', 'submission'),
    ('於校內截止日前備妥甄選申請表與積分自評表送系所及學院初審排序', '學生與所屬系所／學院辦公室', 'submission'),
    ('備妥交換申請表、歷年成績單及作品集送系所初審及學院複審', '學生與所屬系所／學院', 'submission'),
    ('備妥《交換生計畫申請表》、專業作品集與應備文件送所屬系所進行第一階段書面初審', '學生與所屬系所', 'submission'),
    ('等待校方審查已上傳的文件', '學生', 'notice'),
    ('審查學生送交的申請文件', '系所甄選委員會', 'notice'),
    ('由國際暨兩岸事務處提名並遞交入學文件', '國際暨兩岸事務處與學生', 'notice'),
    ('於系統上傳簽證補件', '學生', 'note'),
    ('核對應上傳文件的格式', '學生', 'note'),
])
def test_student_home_handoffs_separate_delivery_from_review(title, actor, expected):
    from exchange_info.application_path import checklist_kind

    task = result().choices[0].checklist[0].model_copy(update={
        'title': title, 'responsible_party': actor, 'phase': '校內申請',
    })
    assert checklist_kind(task) == expected


def test_ready_note_does_not_become_student_confirmed_submission(client):
    plan = create(client).json()
    saved = update(client, plan, 'task-one', {'value': '已備齊申請表', 'confirmed': True}).json()
    evolved = result()
    task = evolved.choices[0].checklist[0]
    task.title = '備妥交換申請表與作品集送系所初審'
    task.phase = '校內申請'
    task.responsible_party = '學生與所屬系所'
    client.app.state.path_evaluate = lambda _: evolved
    current = client.get(f'/account/application-paths/{plan["plan"]["id"]}', params={'home_school': CONTEXT['home_school']}, headers={'Authorization':'alice'}).json()
    handoff = next(x for stage in current['stages'] for x in stage['levels'] if x['id'] == 'task-one')
    assert handoff['kind'] == 'submission' and handoff['progress']['value'] < handoff['progress']['total']
    assert current['plan']['steps']['task-one']['value'] == '已備齊申請表'
    assert current['plan']['steps']['task-one']['confirmed'] is False
    confirmed = update(client, current, 'task-one', {'value':'已依校方指示送交', 'confirmed':True}, revision=saved['revision']).json()
    handoff = next(x for stage in confirmed['stages'] for x in stage['levels'] if x['id'] == 'task-one')
    assert handoff['progress']['value'] == handoff['progress']['total']
