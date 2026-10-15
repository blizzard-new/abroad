"""Official capacity, receiving-school references and notices have separate scope."""
import copy
import hashlib
import json
from pathlib import Path
import shutil
import subprocess

from fastapi.testclient import TestClient
import pytest

from exchange_info.api import create_app
from exchange_info.models import PartnerUniversity
from exchange_info.ntu_current_updates import SOURCE, apply_current_updates, load_update
from exchange_info.ntu_student_view import fetch_ntu_partner_universities
from scripts.audit_ntu_completion import audit
from scripts.export_ntu_completion_report import classify_review_axes

BUNDLE = Path("src/exchange_info/official_data/ntu")
EXPECTED = {
    "998": (1, 2), "1302": (2, 4), "1103": (1, 2), "1194": (1, 2),
    "71": (2, 4), "72": (3, 6), "74": (2, 4), "69": (1, 2),
    "1286": (2, 4), "1200": (2, 4), "98": (4, 8), "380": (1, 2),
    "391": (4, 5), "247": (5, 10), "1040": (1, 2), "606": (1, 2),
    "375": (1, 2), "85": (3, 6), "371": (2, 4), "89": (4, 6),
}


def test_all_eight_capacities_are_source_backed_without_opening_registration(tmp_path):
    source = load_update()
    assert {q["portal_id"]: (q["quota_academic_years"], q["maximum_persons"]) for q in source["quota_updates"]} == EXPECTED
    partners = fetch_ntu_partner_universities()
    assert len(partners) == 288
    assert sum(p.quota is None for p in partners) == 261
    assert sum(p.quota == "0 名" for p in partners) == 7
    assert all(p.availability_status != "open" for p in partners)
    selected = {p.source_url.rsplit("/", 1)[-1]: p for p in partners if p.quota_status == "published"}
    assert set(selected) == set(EXPECTED)
    for pid, (years, maximum) in EXPECTED.items():
        partner = selected[pid]
        assert partner.quota == f"{years} 學年名額（最多 {maximum} 人次）"
        assert partner.application_window_status == "needs_confirmation"
        assert partner.field_evidence["quota"].status == "verified_current"
        assert partner.field_evidence["quota"].source_url == "https://oia.ntu.edu.tw/outgoing/school.list"
        assert partner.reference_data["selection_maximum_persons"] == str(maximum)
        assert "不保證錄取" in partner.availability_note
        assert "限本校第一學期出國" in partner.availability_note
    client = TestClient(create_app(tmp_path))
    dashboard = client.get("/student-dashboard", params={"school": "NTU"}).json()
    assert sum(p.get("quota_status") == "published" for p in dashboard["partner_universities"]) == 20
    for partner in selected.values():
        workflow = client.get("/application-workflow", params={"home_school": "NTU", "school": partner.school_name, "academic_year": "116"}).json()
        assert workflow["published_at"] is None
        assert all(not step["deadline_reminder_eligible"] for step in workflow["steps"])


def test_australia_notice_is_attributed_and_does_not_supply_a_quota(tmp_path):
    source = load_update()
    partners = {p.school_name: p for p in fetch_ntu_partner_universities()}
    client = TestClient(create_app(tmp_path))
    assert len(source["visa_reminders"]) == 11
    for reminder in source["visa_reminders"]:
        assert not reminder["legal_rule_independently_verified"]
        partner = partners[reminder["school_name"]]
        assert partner.quota is None
        assert "臺大新增簽證提醒" in partner.application_info
        assert "未獨立核實為新法律或一律禁止" in partner.application_info
        guide = client.get("/destination-profile", params={"home_school": "NTU", "school": partner.school_name}).json()
        section = next(s for s in guide["student_guide_sections"] if s["key"] == "ntu-current-source-update-20261014")
        assert reminder["text_zh"] in section["points"]
        assert reminder["source_url"] in section["source_urls"]


def test_ubc_new_document_resolves_year_without_rewriting_historical_fee_discovery(tmp_path):
    source = load_update()
    old = json.loads(Path("sources/ntu/completion-2026-10-11.json").read_text())
    historic = next(s for s in old["schools"] if s["portal_id"] == "1")
    partner = next(p for p in fetch_ntu_partner_universities() if p.source_url.endswith("/sn/1"))
    assert partner.quota is None
    assert source["ubc_update"]["new_fee_amount_first_discovery"] is False
    for obs in historic["observations"]:
        assert obs["text_zh"] in partner.application_info
    details = partner.partner_exchange_details
    assert all(d.status == "reference_only" for d in details.values())
    assert all(d.evidence[0].academic_year == "2027/2028" for d in details.values())
    assert "2027/4/1" in details["deadlines"].value and "2027/9/15" in details["deadlines"].value
    assert "非臺大校內報名期限" in details["deadlines"].value
    assert "暫定" in details["calendar"].value and "2028/1/5" in details["calendar"].value
    assert all(s in details["cost"].value for s in ["295.10", "11.15", "204.30", "191.40", "費用可調整", "不重複計"])
    assert "移除Full year students" in details["housing"].value
    assert "未在該學期可退課且不記W" in details["cost"].value
    assert "2026-11-09" in partner.application_deadline


@pytest.mark.parametrize("failure", ["amount", "maximum", "open", "legal", "inventory", "archive_hash", "year"])
def test_changed_or_unscoped_source_fails_before_writing(tmp_path, failure):
    data = json.loads(SOURCE.read_text())
    if failure == "amount": data["quota_updates"][0]["quota_academic_years"] = 99
    elif failure == "maximum": data["quota_updates"][0]["maximum_persons"] = 99
    elif failure == "open": data["application_open_confirmed"] = True
    elif failure == "legal": data["visa_reminders"][0]["legal_rule_independently_verified"] = True
    elif failure == "inventory": data["list_receipt"]["rows"][0]["quota"] = "1 名"
    elif failure == "archive_hash": next(iter(data["source_manifest"].values()))["sha256"] = "0" * 64
    else: data["source_academic_year"] = "2028/2029"
    path = tmp_path / "changed.json"
    path.write_text(json.dumps(data))
    bundle = tmp_path / "bundle"
    shutil.copytree(BUNDLE, bundle)
    before = {p.name: p.read_bytes() for p in bundle.iterdir() if p.is_file()}
    with pytest.raises(ValueError):
        apply_current_updates(bundle, path)
    assert before == {p.name: p.read_bytes() for p in bundle.iterdir() if p.is_file()}


def test_published_capacity_has_its_own_matrix_state_and_unchanged_full_cycle_guard():
    records, summary = audit()
    quota = [r for r in records if r["field"] == "quota"]
    assert len(records) == 4032
    published = [r for r in quota if r["status"] == "verified_current_home_selection_quota"]
    assert {r["portal_id"] for r in published} == set(EXPECTED)
    assert all(r["target_requirement_confirmed"] for r in published)
    assert all(classify_review_axes(r, [], [])["publication_status"] == "official_NTU_positive_selection_quota_published" for r in published)
    assert sum(r["status"] == "pending_official_selection_list" for r in quota) == 261
    completeness = json.loads((BUNDLE / "catalog-completeness.json").read_text())
    assert completeness["fully_verified_current_cycle_count"] == 0
    assert completeness["confirmed_open_count"] == 0


def test_source_backed_capacity_label_stays_pending_and_other_schools_keep_semantics():
    script = r'''
    const assert = require('node:assert/strict');
    const source = require('node:fs').readFileSync(process.argv[1], 'utf8');
    let home = '國立臺灣大學';
    const activeHomeSchool = () => home;
    const homeSelectionRules = () => ({pending_quota_planning:true});
    eval(source.match(/^function partnerAvailabilityMeta\([^]*?^}/m)[0]);
    const current = {availability_status:'agreement_only',quota:'3 學年名額（最多 6 人次）',quota_status:'published',
      availability_note:'名額不保證錄取',field_evidence:{quota:{status:'verified_current',academic_year:'116',
      application_round:'116-1',source_url:'https://oia.ntu.edu.tw/outgoing/school.list'}}};
    const meta = partnerAvailabilityMeta(current);
    assert.match(meta.cardLabel,/名額已公告/); assert.match(meta.cardLabel,/選填狀態待確認/);
    assert.equal(meta.pending,true); assert.equal(meta.blocked,false); assert.notEqual(meta.status,'open');
    assert.equal(partnerAvailabilityMeta({...current,field_evidence:{}}).blocked,true);
    home = '國立中央大學'; assert.equal(partnerAvailabilityMeta(current).blocked,true);
    assert.equal(partnerAvailabilityMeta({availability_status:'agreement_only',quota:null}).pending,true);
    assert.equal(partnerAvailabilityMeta({availability_status:'agreement_only',quota:'0 名'}).blocked,true);
    '''
    result = subprocess.run(["node", "-e", script, str(Path("src/exchange_info/static/app.js").resolve())], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr


def test_published_quota_remains_plannable_without_claiming_current_eligibility():
    from exchange_info.advisor import build_advisor_plan
    from exchange_info.application_rules import build_personal_application_plan
    from exchange_info.models import AdvisorProfile, PersonalApplicationPlanRequest
    from exchange_info.ntu_student_view import build_ntu_student_dashboard
    dashboard = build_ntu_student_dashboard()
    target = next(p for p in dashboard.partner_universities if p.source_url.endswith('/sn/72'))
    profile = AdvisorProfile(school_name='國立臺灣大學', college='工學院', department='機械工程學系',
        degree_level='大學部', academic_gpa=3.5, class_rank_percent=20, language_test='toefl', language_score=100,
        target_school=target.school_name)
    plan = build_advisor_plan(profile, dashboard, [], [], [])
    assert plan.target_match is not None and plan.target_match.eligibility_status == 'needs_confirmation'
    request = PersonalApplicationPlanRequest(home_school='國立臺灣大學', college=profile.college,
        department=profile.department, degree_level=profile.degree_level, academic_gpa=3.5,
        class_rank_percent=20, language_test='toefl', language_score=100,
        preferences=[{'rank':1,'school_name':target.school_name}])
    evaluation = build_personal_application_plan(request, dashboard.partner_universities, [], academic_score_minimum=None)
    assert evaluation.choices[0].status == 'needs_confirmation'
    check = next(c for c in evaluation.choices[0].checks if c.code == 'availability')
    assert check.status == 'needs_confirmation' and '已公告' in check.detail
