import pytest

from exchange_info.advisor import build_advisor_plan
from exchange_info.application_rules import build_personal_application_plan
from exchange_info.models import AdvisorProfile, PartnerUniversity, PersonalApplicationPlanRequest, StudentDashboard


@pytest.mark.parametrize("colleges,degrees,college,degree,code,expected",[
    ("大學部","大學部","法律學院","大學部","college","needs_confirmation"),
    ("依當期協議確認","大學部","工學院","大學部","college","needs_confirmation"),
    ("all except engineering","大學部","工學院","大學部","college","needs_confirmation"),
    ("無","大學部","工學院","大學部","college","needs_confirmation"),
    ("四院皆可","大學部","工學院","大學部","college","pass"),
    ("Law","大學部","法律學院","大學部","college","pass"),
    ("工學院","undergraduate","工學院","研究所","degree_level","fail"),
    ("工學院","2","工學院","大學部","degree_level","needs_confirmation"),
    ("工學院","【跨期資料待核對】115-2 歷年學士班","工學院","大學部","degree_level","needs_confirmation"),
    ("工學院","【跨期資料待核對】115-2 歷年學士班","工學院","研究所","degree_level","needs_confirmation"),
])
def test_recommendation_and_preference_check_use_same_scope_evidence(colleges,degrees,college,degree,code,expected):
    partner=PartnerUniversity(school_name="合作校",program_type="交換",colleges=colleges,
        degree_levels=degrees,eligibility="IELTS 6.0",source_url="https://home.edu/notice")
    dashboard=StudentDashboard(school_name="國立臺北大學",partner_universities=[partner],academic_score_minimum=75)
    advisor=build_advisor_plan(AdvisorProfile(college=college,degree_level=degree,academic_score=85,
        language_test="ielts",language_score=7),dashboard,[],[],[]).recommendations[0]
    request=PersonalApplicationPlanRequest(home_school=dashboard.school_name,college=college,degree_level=degree,
        academic_score=85,language_test="ielts",language_score=7,preferences=[{"rank":1,"school_name":partner.school_name}])
    plan=build_personal_application_plan(request,[partner],[],academic_score_minimum=75)
    check=next(row for row in plan.choices[0].checks if row.code == code)
    assert check.status == expected
    if expected == "fail":
        assert advisor.eligibility_status == "does_not_match"
    else:
        assert not advisor.blocking_reasons
        known_reason = "符合學院範圍" if code == "college" else "符合目前學制"
        assert (known_reason in advisor.reasons) == (expected == "pass")
        scope_word = "學院範圍" if code == "college" else "學制範圍"
        assert any(scope_word in row for row in advisor.confirmation_items) == (expected == "needs_confirmation")
