import hashlib
import json
import subprocess
from datetime import timedelta
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from exchange_info.advisor import _partner_language_threshold as advisor_threshold
from exchange_info.api import create_app
from exchange_info.application_rules import (
    _partner_language_threshold as plan_threshold,
)
from exchange_info.ccu_sources import BUNDLE, HOME
from exchange_info.ccu_student_view import fetch_ccu_partner_universities
from exchange_info.models import (
    AccountSessionRecord,
    PartnerUniversity,
    UserAccount,
    utc_now,
)
from exchange_info.storage import save_account_sessions, save_user_accounts


def at(page):
    return next(
        row for row in fetch_ccu_partner_universities() if row.source_pages[0] == page
    )


def client_for(tmp_path):
    token = "ccu-semantic-isolated-test"
    save_user_accounts(
        [
            UserAccount(
                id="ccu-semantics",
                display_name="測試",
                email_verified=True,
                student_status_verified=True,
                verified_university=HOME,
                home_university=HOME,
            )
        ],
        tmp_path,
    )
    save_account_sessions(
        [
            AccountSessionRecord(
                account_id="ccu-semantics",
                token_hash=hashlib.sha256(token.encode()).hexdigest(),
                expires_at=utc_now() + timedelta(days=1),
            )
        ],
        tmp_path,
    )
    return TestClient(
        create_app(tmp_path), headers={"Authorization": f"Bearer {token}"}
    )


@pytest.mark.parametrize(
    "page,test",
    [
        (45, "ielts"),
        (45, "toefl"),
        (50, "ielts"),
        (58, "ielts"),
        (58, "toefl"),
        (74, "toefl"),
        (49, "ielts"),
        (100, "ielts"),
        (101, "toefl"),
        (103, "ielts"),
        (80, "ielts"),
        (65, "toefl"),
        (86, "ielts"),
        (89, "ielts"),
        (95, "ielts"),
        (95, "other"),
    ],
)
def test_reviewed_uncertainty_never_becomes_a_scalar_threshold(page, test):
    partner = at(page)
    assert advisor_threshold(partner, test, "大學部") is None
    assert plan_threshold(partner, test, "大學部") is None
    assert partner.language_conditions and partner.language_review_note
    assert all(
        rule.evidence.source_pages and rule.evidence.checked_at
        for rule in partner.language_conditions
    )


def test_reviewed_mandatory_scores_remain_comparable():
    assert advisor_threshold(at(68), "ielts", "大學部") == 6.0
    assert plan_threshold(at(67), "ielts", "大學部") == 6.0
    assert plan_threshold(at(102), "toefl", "大學部") == 72
    assert (
        plan_threshold(at(67), "toeic", "大學部") is None
    )  # L&R AND S&W cannot be flattened.


@pytest.mark.parametrize(
    "page,status",
    [
        (26, "missing"),
        (32, "reference_only"),
        (33, "reference_only"),
        (39, "reference_only"),
        (71, "missing"),
        (103, "missing"),
        (104, "missing"),
        (74, "missing"),
        (105, "reference_only"),
        (34, "needs_confirmation"),
        (37, "needs_confirmation"),
        (61, "needs_confirmation"),
        (88, "needs_confirmation"),
        (111, "needs_confirmation"),
        (23, "needs_confirmation"),
        (109, "needs_confirmation"),
    ],
)
def test_nomination_and_historical_or_linked_documents_are_separate(page, status):
    partner = at(page)
    assert partner.field_evidence["partner_documents"].status == status
    assert partner.partner_application_prerequisite
    assert (
        partner.field_evidence["partner_application_prerequisite"].status
        == "verified_current"
    )
    if status in {"missing", "reference_only"}:
        assert partner.application_info is None
        assert not partner.student_summary_zh.application_steps
    if status == "reference_only":
        assert partner.reference_data["partner_documents"]
    if page == 105:
        assert partner.tuition_info is None


def test_document_coverage_means_actual_listed_requirements_not_complete_overseas_verification():
    rows = [
        row
        for row in fetch_ccu_partner_universities()
        if row.availability_status != "not_open"
    ]
    actual = [
        row
        for row in rows
        if row.field_evidence["partner_documents"].status == "verified_current"
    ]
    assert len(rows) == 55 and len(actual) == 37
    assert all(
        row.application_info
        and "未宣稱" in row.field_evidence["partner_documents"].note
        for row in actual
    )
    stats = json.loads((BUNDLE / "completeness.json").read_text())
    assert stats["current_field_counts"]["partner_documents"] == 37


@pytest.mark.parametrize(
    "page,test,score",
    [
        (45, "ielts", 6.0),
        (45, "ielts", 7.0),
        (58, "ielts", 5.0),
        (58, "ielts", 7.0),
        (74, "toefl", 85),
        (74, "toefl", 100),
        (95, "ielts", 5.0),
        (95, "ielts", 7.0),
        (95, "other", None),
    ],
)
def test_api_plan_and_advisor_return_language_confirmation(page, test, score, tmp_path):
    client = client_for(tmp_path)
    partner = at(page)
    common = {
        "college": "工學院",
        "department": "資訊工程學系",
        "degree_level": "大學部",
        "academic_score": 85,
        "academic_gpa": 3.5,
        "language_test": test,
        "language_score": score,
    }
    response = client.post(
        "/application-plan/evaluate",
        json=dict(
            home_school=HOME,
            **common,
            preferences=[{"rank": 1, "school_name": partner.school_name}],
        ),
    )
    assert response.status_code == 200, response.text
    checks = {check["code"]: check for check in response.json()["choices"][0]["checks"]}
    assert checks["language_score"]["status"] == "needs_confirmation"
    if test == "other":
        assert HOME in checks["language_score"]["detail"]
    else:
        assert checks["language_score"]["detail"] == partner.language_review_note
    response = client.post(
        "/advisor/plan",
        json=dict(
            school_name=HOME,
            target_school=partner.school_name,
            question="持有母校Coordinator英語B2確認函" if page == 95 else None,
            **common,
        ),
    )
    assert response.status_code == 200, response.text
    target = response.json()["target_match"]
    assert target["eligibility_status"] == "needs_confirmation"
    assert not any(
        "IELTS" in text or "TOEFL" in text for text in target["blocking_reasons"]
    )
    if test != "other":
        assert partner.language_review_note in target["confirmation_items"]


def test_other_homes_keep_the_original_language_parser():
    partner = PartnerUniversity(
        program_type="交換",
        school_name="其他母校合作校",
        source_url="https://example.edu/official",
        eligibility="IELTS 6.0",
        program_options=[
            {"program_type": "A", "source_url": "https://example.edu/a"},
            {"program_type": "B", "source_url": "https://example.edu/b"},
        ],
    )
    assert advisor_threshold(partner, "ielts") == 6
    assert plan_threshold(partner, "ielts") == 6


def test_frontend_matches_structured_language_and_document_statuses():
    cases = [
        {"partner": at(p).model_dump(mode="json"), "test": t, "score": s}
        for p, t, s in [
            (45, "ielts", 6),
            (58, "ielts", 5),
            (74, "toefl", 85),
            (50, "ielts", 5),
            (103, "ielts", 6),
            (65, "toefl", 70),
            (86, "ielts", 6.5),
            (89, "ielts", 7),
            (95, "ielts", 5),
            (95, "ielts", 7),
            (95, "other", None),
        ]
    ]
    script = r"""
    const assert=require('node:assert/strict'),fs=require('node:fs');
    const window={};
    eval(fs.readFileSync(process.argv[2],'utf8'));
    const source=fs.readFileSync(process.argv[1],'utf8');
    const payload=JSON.parse(fs.readFileSync(0,'utf8'));
    const cases=payload.cases;
    const state={homeSchool:'國立中正大學',dashboard:{academic_gpa_minimum:3,academic_score_minimum:70}};
    const homeSelectionRules=()=>state.dashboard.selection_rules || {};
    const homeAcademicPass=profile=>profile.academicScore>=70 && profile.academicGpa>=3;
    const partnerSummaryPoints=(item)=>item.student_summary_zh.eligibility_points;
    const homeCollegeValue=value=>value,normalize=value=>String(value||''),academicMinimum=()=>70;
    const collegeMatches=()=>true,degreeMatches=()=>true,coverageForSchool=()=>null,destinationProfileForSchool=()=>null;
    const escapeHtml=value=>String(value),highlightHtml=value=>String(value);
    for(const name of ['activeHomeSchool','academicScopeNeedsConfirmation','coupledAcademicScopeOptions','coupledAcademicScopeMatches','resolvedDegreeLevel','partnerDegreeScopeMatches','languageThresholdFromPartner','partnerAvailabilityMeta','partnerMatch','renderPartnerFieldEvidence']) {
      eval(source.match(new RegExp('^function '+name+'\\([^]*?^}','m'))[0]);
    }
    for(const test of cases) {
      assert.equal(languageThresholdFromPartner(test.partner,test.test,'大學部'),null);
      const profile={college:'工學院',degree:'大學部',academicGpa:3.5,academicScore:85,languageTest:test.test,languageScore:test.score};
      const match=partnerMatch(test.partner,profile);
      assert.equal(match.tone,'review');
      assert.ok(!match.risks.some(text=>text.includes('語言分數未達')));
      if (test.test !== 'other') assert.ok(match.risks.includes(test.partner.language_review_note));
    }
    const direct=payload.direct;
    assert.equal(languageThresholdFromPartner(direct,'ielts','大學部'),6.0);
    const legacy={source_url:'https://example.edu',student_summary_zh:{eligibility_points:['IELTS 6.0']},program_options:[{},{}]};
    assert.equal(languageThresholdFromPartner(legacy,'ielts'),6);
    for(const item of payload.document_cases) {
      const html=renderPartnerFieldEvidence(item);
      assert.ok(html.includes('母校甄選／提名前提（非文件清單）'));
      assert.ok(!html.includes('合作校申請文件要求（未聲稱完整） · 當期已核實'));
    }
    """
    result = subprocess.run(
        [
            "node",
            "-e",
            script,
            str(Path("src/exchange_info/static/app.js").resolve()),
            str(Path("src/exchange_info/static/ccu-language-conditions.js").resolve()),
        ],
        input=json.dumps(
            {
                "cases": cases,
                "direct": at(67).model_dump(mode="json"),
                "document_cases": [
                    at(p).model_dump(mode="json")
                    for p in (26, 32, 33, 39, 71, 103, 104, 74)
                ],
            },
            ensure_ascii=False,
        ),
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr


def test_openapi_exposes_reviewed_ccu_conditions(tmp_path):
    schemas = (
        TestClient(create_app(tmp_path))
        .get("/openapi.json")
        .json()["components"]["schemas"]
    )
    assert "PartnerLanguageCondition" in schemas and "ExchangeFieldEvidence" in schemas
    assert {
        "language_conditions",
        "language_review_note",
        "partner_application_prerequisite",
    } <= schemas["PartnerUniversity"]["properties"].keys()
    assert "academic_gpa" in schemas["AdvisorProfile"]["properties"]
