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
    register_application_path(app, authenticate=authenticate,
        university_for=lambda home:type("University", (), {"school_name":home})(),
        evaluate=lambda request:result(request.preferences[0].school_name),
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
    assert saved.json()["progress"]["value"] == 1
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
