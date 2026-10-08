import json
import copy
import gzip
import importlib.util
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from exchange_info import storage
from exchange_info.api import create_app
from exchange_info.application_documents import build_application_document_catalog
from exchange_info.application_rules import build_personal_application_plan
from exchange_info.models import ApplicationCenterContext, PartnerDocumentPreparationState, PersonalApplicationPlanRequest
from exchange_info.ncu_document_conditions import document_applicability, preparation_state_key
from exchange_info.ncu_student_view import fetch_ncu_partner_universities

NCU = "國立中央大學"
UOS = "首爾市立大學 University of Seoul"
HUST = "華中科技大學 Huazhong University of Science and Technology"


def _conditional_documents(school):
    workflow = next(w for w in storage.load_bundled_application_workflows() if w.home_university == NCU and w.school_name == school)
    step = next(s for s in workflow.steps if s.rule_id.endswith("host-predeparture-documents"))
    return workflow, step.document_requirements


@pytest.mark.parametrize("school", [UOS, HUST])
@pytest.mark.parametrize("admission", ["unknown", "not_accepted", "accepted"])
@pytest.mark.parametrize("housing", ["unknown", "on_campus", "off_campus"])
def test_explicit_document_conditions_cover_known_unknown_and_deferred(school, admission, housing):
    workflow, docs = _conditional_documents(school)
    state = PartnerDocumentPreparationState(host_admission_status=admission, housing_choice=housing)
    if school == UOS and housing == "off_campus":
        expected = "not_applicable"
    elif admission == "not_accepted":
        expected = "deferred"
    elif admission == "unknown" or (school == UOS and housing == "unknown"):
        expected = "needs_confirmation"
    else:
        expected = "applicable"
    for doc in docs:
        result = document_applicability(NCU, school, doc, state)
        assert result.status == expected
        assert not result.current_applicability_verified and result.source_urls
        assert "116當期" in result.note
        assert doc.needs_confirmation
    assert workflow.review_status == "pending_review" and workflow.published_at is None
    assert not any(s.deadline_reminder_eligible for s in workflow.steps)


def test_actual_catalog_conditions_do_not_approve_downloads_or_initial_files(tmp_path):
    client = TestClient(create_app(tmp_path))
    for school, expected_count in ((UOS, 2), (HUST, 1)):
        params = dict(school="NCU",target_school=school,academic_year="116",host_admission_status="accepted",housing_choice="on_campus")
        response = client.get("/application-center/catalog",params=params)
        assert response.status_code == 200
        catalog = response.json()
        conditional = [d for d in catalog["items"] if d["applicability"]]
        assert len(conditional) == expected_count
        assert all(d["phase"] == "行前準備" and d["applicability"]["status"] == "applicable" for d in conditional)
        assert all(d["needs_confirmation"] and not d["download_available"] for d in conditional)
        params["host_admission_status"] = "not_accepted"
        delayed = client.get("/application-center/catalog",params=params).json()
        assert all(d["applicability"]["status"] == "deferred" for d in delayed["items"] if d["applicability"])
    invalid = client.get("/application-center/catalog",params={**params,"housing_choice":"maybe"})
    assert invalid.status_code == 422


def test_saved_condition_scope_never_carries_to_other_year_school_or_semester():
    state = PartnerDocumentPreparationState(host_admission_status="accepted",housing_choice="on_campus")
    key = preparation_state_key(UOS,"116","第一梯次","第一學期")
    context = ApplicationCenterContext(school_name=NCU,target_school=UOS,academic_year="116",application_round="第一梯次",semester="第一學期",partner_document_states={key:state})
    catalog = build_application_document_catalog(context,storage.load_bundled_application_workflows())
    assert {d.applicability.status for d in catalog.items if d.applicability} == {"applicable"}
    for change in ({"semester":"第二學期"},{"application_round":None},{"academic_year":None},{"target_school":HUST}):
        changed = context.model_copy(update=change)
        results = [d.applicability for d in build_application_document_catalog(changed,storage.load_bundled_application_workflows()).items if d.applicability]
        assert results and all(r.status == "needs_confirmation" for r in results)
    # 117 has no selected current workflow; old conditions cannot enable it.
    assert not build_application_document_catalog(context.model_copy(update={"academic_year":"117"}),storage.load_bundled_application_workflows()).workflow_found


@pytest.mark.parametrize("admission,housing,status", [("unknown","unknown","needs_confirmation"),("not_accepted","on_campus","deferred"),("accepted","off_campus","not_applicable"),("accepted","on_campus","applicable")])
def test_personal_and_unified_task_conditions_match_catalog_and_keep_workflow_unchanged(admission,housing,status):
    workflows = storage.load_bundled_application_workflows()
    before = [w.model_dump_json() for w in workflows]
    request = PersonalApplicationPlanRequest(home_school=NCU,academic_year="116",application_round="第一梯次",preferences=[{"rank":1,"school_name":UOS,"document_preparation_state":{"host_admission_status":admission,"housing_choice":housing}}])
    plan = build_personal_application_plan(request,fetch_ncu_partner_universities(),workflows,academic_score_minimum=None)
    task = next(t for t in plan.tasks if t.document_applicability)
    assert len(task.document_applicability) == 2 and {r.status for r in task.document_applicability} == {status}
    assert task.needs_confirmation and task.official_deadline_at is None
    assert not task.document_link.requirement_names if status != "applicable" else len(task.document_link.requirement_names) == 2
    assert [w.model_dump_json() for w in workflows] == before
    choice = next(t for t in plan.choices[0].checklist if t.document_applicability)
    assert choice.document_applicability == task.document_applicability


def test_explicit_policy_does_not_guess_from_similar_names_or_other_home_school():
    workflow, docs = _conditional_documents(UOS)
    renamed = docs[0].model_copy(update={"name":"MMR類似字樣但尚未核實文件"})
    assert document_applicability(NCU,UOS,renamed) is None
    for home in ("長庚大學","國立臺北大學","國立臺灣大學"):
        assert document_applicability(home,UOS,docs[0]) is None


@pytest.mark.parametrize("change", ["changed_original", "failed_original", "missing_version", "wrong_url"])
def test_changed_condition_source_cannot_reuse_a_reviewed_policy(change):
    root = Path(__file__).resolve().parents[1]
    bundle = root / "src/exchange_info/official_data/ncu"
    spec = importlib.util.spec_from_file_location("ncu_condition_builder", root / "scripts/build_ncu_catalog.py")
    builder = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(builder)
    policies = json.loads((bundle / "document-conditions.json").read_text())
    sources = {d["id"]: d for d in json.loads(gzip.decompress((bundle / "source-evidence.json.gz").read_bytes()))}
    workflows = [w.model_dump(mode="json") for w in storage.load_bundled_application_workflows() if w.home_university == NCU]
    builder.validate_document_conditions(policies, workflows, sources)
    changed = copy.deepcopy(policies)
    version = changed[0]["source_versions"][0]
    if change == "changed_original":
        sources[version["source_id"]]["sha256"] = "a-new-original-has-not-been-reviewed"
    elif change == "failed_original":
        sources[version["source_id"]]["error"] = "HTTP 403"
    elif change == "missing_version":
        changed[0]["source_versions"].pop(0)
    else:
        version["url"] = "https://eng.uos.ac.kr/a-different-form"
    with pytest.raises(ValueError, match="NCU條件文件"):
        builder.validate_document_conditions(changed, workflows, sources)
