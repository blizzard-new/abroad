from cgu_catalogue_fixture import fixed_cgu_catalogue
import hashlib
import json
import subprocess
from collections import Counter
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from pypdf import PdfReader

from exchange_info.advisor import build_advisor_plan
from exchange_info.api import create_app
from exchange_info.application_documents import all_application_templates
from exchange_info.application_rules import (
    _partner_language_threshold,
    build_personal_application_plan,
)
from exchange_info.ccu_sources import BUNDLE, CHECKED_AT, HOME, ROUND, YEAR, home_round
from exchange_info.ccu_student_view import (
    build_ccu_student_dashboard,
    fetch_ccu_partner_universities,
)
from exchange_info.models import (
    AdvisorProfile,
    PersonalApplicationPlanRequest,
    UniversityApplicationWorkflow,
)
from exchange_info.storage import read_jsonl
from exchange_info.university_registry import CCU, resolve_university
from exchange_info.workflow_structuring import workflow_structure_issues


def rows():
    return fetch_ccu_partner_universities()


def at(page):
    return next(row for row in rows() if row.source_pages[0] == page)


def workflows():
    return read_jsonl(
        BUNDLE / "application_workflows.jsonl", UniversityApplicationWorkflow
    )


def test_ccu_aliases_and_colleges_are_school_specific():
    assert all(
        resolve_university(value) == CCU
        for value in ("CCU", "中正", HOME, CCU.english_name)
    )
    assert len(CCU.colleges) == 7
    assert CCU.support_level == "basic"
    assert CCU.hero_image == ""


def test_ccu_counts_unique_and_quota_states():
    partners = rows()
    assert len(partners) == len({row.school_name for row in partners}) == 104
    assert Counter(row.availability_status for row in partners) == {
        "open": 52,
        "not_open": 49,
        "needs_confirmation": 3,
    }
    assert Counter(row.quota_status for row in partners) == {
        "published": 52,
        "reference_only": 49,
        "not_published": 3,
    }
    assert {
        row.source_pages[0] for row in partners if row.quota_status == "not_published"
    } == {71, 80, 107}
    for row in partners:
        assert row.academic_year == YEAR and row.application_round == ROUND
        assert row.checked_at == CHECKED_AT and row.source_pages and row.country
        assert row.application_window_status == "closed"
        if row.availability_status == "not_open":
            assert (
                row.quota is None
                and row.eligibility is None
                and row.language_requirement is None
            )
            assert row.reference_data


def test_ccu_provenance_and_explicit_old_attachments():
    for row in rows():
        for key, evidence in row.field_evidence.items():
            if row.source_pages == [49] and key in {"semester_dates", "partner_application_deadline"}:
                urls = {
                    "semester_dates": "https://www.sungshin.ac.kr/bbs/int/3828/113855/download.do",
                    "partner_application_deadline": "https://www.sungshin.ac.kr/bbs/int/3828/159720/artclView.do",
                }
                assert evidence.source_url == urls[key]
                assert evidence.checked_at.date().isoformat() == "2026-10-11"
                assert evidence.status == "verified_current" and evidence.excerpt
                assert "Spring2027" in evidence.academic_year
                assert evidence.application_round.startswith("Spring2027接待Exchange")
                assert "ccu_sungshin_superseded_summary" in row.reference_data
                continue
            if key in {"website", "city", "location", "colleges", "degree_levels"}:
                assert evidence.source_url.startswith("https://")
                expected_date = "2026-10-11" if row.availability_status == "not_open" and key == "website" else CHECKED_AT.date().isoformat()
                assert evidence.checked_at.date().isoformat() == expected_date
                assert evidence.excerpt and evidence.academic_year
                continue
            assert evidence.source_url.startswith("https://oia.ccu.edu.tw/")
            assert evidence.checked_at.date() == CHECKED_AT.date()
            assert evidence.source_pages or evidence.excerpt
            if evidence.status == "verified_current":
                assert (
                    evidence.excerpt
                    and evidence.application_round == ROUND
                    and evidence.academic_year == YEAR
                )
            if evidence.status == "reference_only":
                assert evidence.reference_excerpt
    for page in (23, 80, 105):
        assert at(page).field_evidence["fact_sheet"].status == "reference_only"
        assert "舊簡章" in at(page).reference_data["fact_sheet"]
    assert at(10).field_evidence["additional_info"].status == "needs_confirmation"


def test_ccu_conflicts_do_not_invent_values():
    chungnam = at(53)
    assert chungnam.semester_dates is None
    assert chungnam.field_evidence["semester_dates"].status == "conflict"
    assert "2026/06/18" in chungnam.reference_data["semester_dates"]
    assert at(119).field_evidence["language_requirement"].status == "conflict"
    assert "B2" in at(119).language_requirement and "B1" in at(119).application_info


def test_ccu_home_and_partner_deadlines_and_programs_stay_separate():
    assert home_round(at(58).school_name) == 1
    assert home_round(at(37).school_name) == 2
    assert home_round(at(80).school_name) == 2
    assert home_round(at(95).school_name) == 3
    hokkaido = at(37)
    options = {option.program_type: option for option in hokkaido.program_options}
    assert set(options) == {"HUSTEP", "SA", "SRS"}
    assert "2026/10/23" in options["HUSTEP"].application_deadline
    assert "2026/11/13" in options["SA"].application_deadline
    assert "N2" in options["SA"].eligibility and "6.5" in options["HUSTEP"].eligibility
    assert _partner_language_threshold(hokkaido, "ielts") is None
    assert "accommodation" not in at(89).partner_application_deadline
    assert "11/1/2026" in at(89).housing_info
    assert "2026/10/01" in at(89).partner_application_deadline
    assert (
        "春季適用待承辦確認"
        in next(
            o for o in at(35).program_options if o.program_type == "JYPE"
        ).study_period
    )


def test_ccu_closed_rounds_and_unverified_new_round():
    dashboard = build_ccu_student_dashboard(reference_time=CHECKED_AT)
    assert (
        dashboard.academic_score_minimum == 70 and dashboard.academic_gpa_minimum == 3
    )
    assert dashboard.maximum_preferences == 3
    exact = [p for p in dashboard.application_periods if p.scope == "home_application"]
    assert len(exact) == 6 and all(p.status == "closed" for p in exact)
    assert all(
        p.deadline_at.utcoffset().total_seconds() == 8 * 3600 and p.opens_at is None
        for p in exact
    )
    new = dashboard.application_periods[-1]
    assert new.date_status == "needs_confirmation"
    assert "尚未核實" in new.status_note and "明示尚未公告" in new.status_note
    assert all(not p.reminder_eligible for p in dashboard.application_periods)


@pytest.mark.parametrize(
    "gpa,average,expected",
    [
        (2.9, 85, "fail"),
        (3.0, 70, "pass"),
        (None, 80, "needs_confirmation"),
        (3.6, 69, "pass"),
    ],
)
def test_ccu_gpa_and_average_are_both_required(gpa, average, expected):
    partner = at(103)
    request = PersonalApplicationPlanRequest(
        home_school=HOME,
        academic_gpa=gpa,
        academic_score=average,
        college="工學院",
        degree_level="大學部",
        preferences=[{"rank": 1, "school_name": partner.school_name}],
    )
    result = build_personal_application_plan(
        request, [partner], workflows(), academic_score_minimum=70
    )
    checks = {check.code: check for check in result.choices[0].checks}
    assert checks["academic_gpa"].status == expected
    if average < 70:
        assert checks["academic_score"].status == "fail"
    assert (
        result.choices[0].status != "eligible"
    )  # Closed home window cannot promise a new application.


def test_ccu_preference_limit_and_unknown_quota():
    partners = [p for p in rows() if p.availability_status == "open"][:4]
    request = PersonalApplicationPlanRequest(
        home_school=HOME,
        preferences=[
            {"rank": i + 1, "school_name": p.school_name} for i, p in enumerate(partners)
        ],
    )
    with pytest.raises(ValueError, match="最多3"):
        build_personal_application_plan(
            request, partners, [], academic_score_minimum=70
        )
    unknown = at(71)
    request = PersonalApplicationPlanRequest(
        home_school=HOME, preferences=[{"rank": 1, "school_name": unknown.school_name}]
    )
    result = build_personal_application_plan(
        request, [unknown], [], academic_score_minimum=70
    )
    assert result.choices[0].status == "needs_confirmation"


def test_ccu_workflows_are_complete_structurally_but_not_published():
    flows = workflows()
    assert len(flows) == 55
    for workflow in flows:
        assert workflow.home_university == HOME and workflow.application_round == ROUND
        extra = any(
            r.stage in {"after_application", "second_submission"}
            for s in workflow.steps
            for r in s.document_requirements
        )
        assert len(workflow.steps) == (8 if extra else 7) and not workflow_structure_issues(workflow)
        assert workflow.review_status == "legacy" and workflow.published_at is None
        assert all(not step.deadline_reminder_eligible for step in workflow.steps)
        assert (
            "長庚" not in workflow.model_dump_json()
            and "臺北大學" not in workflow.model_dump_json()
        )
        paper = workflow.steps[2]
        assert len(paper.document_requirements) == 9
        assert "院長" in paper.document_requirements[0].signatures


def test_ccu_attachment_signatures_contents_and_hashes():
    manifest = json.loads((BUNDLE / "source-manifest.json").read_text())
    assert len(manifest["sources"]) == 5
    for source in manifest["sources"]:
        content = (BUNDLE / source["filename"]).read_bytes()
        assert hashlib.sha256(content).hexdigest() == source["sha256"]
        if source["page_count"]:
            assert (
                len(PdfReader(BUNDLE / source["filename"]).pages)
                == source["page_count"]
            )
    templates = all_application_templates(HOME)
    assert len(templates) == 8
    assert "長庚" not in str(templates) and "臺北大學" not in str(templates)
    assert all(
        not t.official_layout and t.source_checked_at == CHECKED_AT for t in templates
    )
    assert next(
        t for t in templates if t.id == "exchange-application-data"
    ).official_download_url.endswith(".doc")


def test_ccu_api_dispatch_and_workflow(tmp_path, monkeypatch):
    def no_cgu(*args, **kwargs):
        raise AssertionError("CCU must not use CGU live retrieval")

    monkeypatch.setattr('exchange_info.api.create_cgu_catalogue', fixed_cgu_catalogue(no_cgu))
    client = TestClient(create_app(tmp_path))
    universities = client.get("/universities").json()
    assert next(u for u in universities if u["id"] == "ccu")["colleges"] == list(
        CCU.colleges
    )
    dashboard = client.get("/student-dashboard", params={"school": "CCU"})
    assert (
        dashboard.status_code == 200
        and len(dashboard.json()["partner_universities"]) == 104
    )
    info = client.get("/exchange-info", params={"school": "CCU"})
    assert info.status_code == 200 and info.json()["school_name"] == HOME
    assert client.get("/search", params={"school": "CCU", "q": "GPA"}).json()
    templates = client.get(
        "/application-center/templates",
        params={"school": "CCU", "program_type": "exchange"},
    )
    assert templates.status_code == 200 and len(templates.json()) == 8
    partner = at(103)
    flow = client.get(
        "/application-workflow",
        params={"home_school": "CCU", "school": partner.school_name},
    )
    assert flow.status_code == 200 and len(flow.json()["steps"]) == 7
    assert client.get("/static/ccu-academic-units.js").status_code == 200


def test_ccu_advisor_gpa_is_not_replaced_by_high_average():
    dashboard = build_ccu_student_dashboard(partner_universities=[at(103)])
    profile = AdvisorProfile(
        school_name=HOME,
        college="工學院",
        degree_level="大學部",
        academic_score=90,
        academic_gpa=2.5,
    )
    plan = build_advisor_plan(profile, dashboard, [], workflows(), [])
    assert plan.recommendations[0].eligibility_status == "does_not_match"
    assert any("GPA" in item for item in plan.recommendations[0].blocking_reasons)


def test_ccu_frontend_preferences_gpa_and_legacy_restoration():
    script = r"""
    const assert = require('node:assert/strict'), fs = require('node:fs');
    const source = fs.readFileSync(process.argv[1], 'utf8');
    const state = {homeSchool:'國立中正大學',account:null,applications:[],dashboard:{maximum_preferences:3,academic_gpa_minimum:3,partner_universities:[]}};
    const elements = new Map(), calls = new Map();
    const $ = selector => {
      if (!elements.has(selector)) { const label={hidden:false};elements.set(selector,{id:selector.slice(1),value:'old',dataset:{},closest:()=>label,querySelectorAll:()=>[]}); }
      return elements.get(selector);
    };
    const activeHomeSchool = () => state.homeSchool;
    const fillSelect = (selector,values,placeholder,selected) => calls.set(selector,values);
    const document={querySelectorAll:()=>[]};
    const homeSelectionRules=()=>state.dashboard.selection_rules || {};
    eval(source.match(/^function renderAcademicFields\([^]*?^}/m)[0]);
    eval(source.match(/^function renderEligibilityOptions\([^]*?^}/m)[0]);
    renderEligibilityOptions();
    assert.equal($('#advisor-gpa-field').hidden,false);
    assert.equal($('#eligibility-preference-4').closest().hidden,true);
    assert.equal($('#eligibility-preference-4').value,'');
    assert.equal(calls.size,3);
    state.dashboard={maximum_preferences:5,academic_gpa_minimum:null,partner_universities:[]};
    renderEligibilityOptions();
    assert.equal($('#advisor-gpa-field').hidden,true);
    assert.equal($('#eligibility-preference-4').closest().hidden,false);
    assert.equal(calls.size,5);
    """
    result = subprocess.run(
        ["node", "-e", script, str(Path("src/exchange_info/static/app.js").resolve())],
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
