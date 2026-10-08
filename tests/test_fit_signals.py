from __future__ import annotations

from exchange_info import storage
from exchange_info.advisor import build_advisor_plan
from exchange_info.cost_estimates import budget_fit, extract_monthly_estimates, primary_estimate, twd_per_unit
from exchange_info.fit_signals import course_interest_fit, school_budget_fit, teaching_language_fit
from exchange_info.models import (
    AdvisorProfile,
    DestinationProfile,
    PartnerProgramOption,
    PartnerUniversity,
    SourceReference,
    StudentDashboard,
    StudentGuideSection,
)


def profile(text: str, name: str = "測試大學") -> DestinationProfile:
    return DestinationProfile(
        school_name=name, cost_summary=text, coverage_status="official_verified",
        sources=[SourceReference(title="官方費用頁", source_url="https://example.edu/cost")],
    )


def test_only_a_stated_monthly_living_total_is_extracted():
    estimate = primary_estimate(extract_monthly_estimates(profile("校方建議國際生每月生活費約 JPY 80,000–150,000；一般租金約 JPY 40,000–60,000。")))
    assert (estimate.currency, estimate.low, estimate.high, estimate.scope) == ("JPY", 80000, 150000, "total_living")
    assert "生活費" in estimate.evidence and estimate.source_urls == ("https://example.edu/cost",)


def test_single_cost_items_degree_students_and_per_period_figures_are_not_totals():
    for text in (
        "私人租屋租金約為每月 500–800 EUR。",
        "宿舍每月約 JPY 91,300–99,800，含平日早晚餐。",
        "一般國際學位生每月生活費約 RMB 1,000，不是交換預算。",
        "生活費每年約 EUR 10,000。",
        "官方網站未公開可可靠核對的交換生生活費金額。",
    ):
        assert primary_estimate(extract_monthly_estimates(profile(text))) is None, text


def test_housing_excluded_figure_is_partial_and_total_wins():
    estimates = extract_monthly_estimates(profile("校方估計每月不含住宿的生活費約 JPY 60,000–70,000。以校內宿舍估算，每月總預算約 JPY 98,000–118,000。"))
    assert [row.scope for row in estimates] == ["partial", "total_living"]
    assert primary_estimate(estimates).low == 98000


def test_spaced_thousands_and_historical_benchmarks():
    spaced = primary_estimate(extract_monthly_estimates(profile("每月總計約為 € 1 250 – € 1400。")))
    assert (spaced.low, spaced.high) == (1250, 1400)
    old = primary_estimate(extract_monthly_estimates(profile("舊版簡介曾以合計約 JPY 100,500／月作參考，但這是歷史基準。")))
    assert old.outdated
    stale = primary_estimate(extract_monthly_estimates(profile("現行生活費頁列平均 EUR 842／月，但底層來源是 2023 年調查。")))
    assert stale.outdated and stale.as_of_year == 2023


def test_budget_fit_statuses_use_reference_rates_and_never_hide_unknowns():
    estimates = extract_monthly_estimates(profile("官方建議每月生活費約 EUR 600–800。"))
    rate = twd_per_unit("EUR")
    assert rate and rate > 20
    low, high = 600 * rate, 800 * rate
    assert budget_fit(estimates, high + 1000)["status"] == "within"
    assert budget_fit(estimates, (low + high) / 2)["status"] == "partly_within"
    assert budget_fit(estimates, low - 1000)["status"] == "over"
    assert budget_fit(estimates, None)["status"] == "unknown"
    assert budget_fit([], 30000)["status"] == "unknown" and budget_fit([], 30000)["reason"]
    outdated = extract_monthly_estimates(profile("現行生活費頁列平均 EUR 842／月，但底層來源是 2023 年調查。"))
    assert budget_fit(outdated, 99999)["status"] == "unknown"


def test_school_budget_fit_adds_fx_caveat_and_exclusions():
    fit = school_budget_fit(profile("官方建議每月生活費約 EUR 600–800。"), 60000)
    assert fit.status == "within" and fit.low_twd and fit.high_twd
    assert "不是銀行即時牌價" in fit.fx_note and "學費" in fit.exclusions
    assert school_budget_fit(None, 30000).status == "unknown"
    assert school_budget_fit(profile("x"), None) is None


def partner(program_type="交換學生（英語組）", **kwargs):
    return PartnerUniversity(program_type=program_type, school_name="測試大學", country="日本",
                             source_url="https://example.edu/p", **kwargs)


def test_teaching_language_follows_the_official_track_then_requirement_text():
    english = partner()
    assert teaching_language_fit(english, "english").status == "listed"
    assert teaching_language_fit(english, "japanese").status == "not_listed"
    assert teaching_language_fit(english, None).status == "unknown"
    mixed = partner("交換學生（英語組）；交換學生（日語組）")
    assert teaching_language_fit(mixed, "japanese").status == "listed"
    text_only = partner("交換學生", eligibility="需具備 JLPT N2")
    fit = teaching_language_fit(text_only, "japanese")
    assert fit.status == "listed" and fit.basis == "requirement_text" and "不等於授課語言" in fit.detail
    assert teaching_language_fit(partner("交換學生"), "english") is None


def test_course_interest_is_only_mentioned_never_confirmed():
    school = partner(colleges="商學院、法律學院", eligibility="限商管相關學系")
    found = course_interest_fit(school, None, "法律, 會計")
    assert found.status == "mentioned" and found.matched_terms == ["法律"]
    assert "不代表該學期有開課" in found.detail
    guide = DestinationProfile(school_name="測試大學", student_guide_sections=[
        StudentGuideSection(key="courses_and_workload", title="課程", summary="資料科學課程多採英語授課", points=[])])
    assert course_interest_fit(partner(), guide, "資料科學").status == "mentioned"
    unknown = course_interest_fit(partner(), None, "海洋生物")
    assert unknown.status == "unknown" and "課程目錄" in unknown.detail
    assert course_interest_fit(partner(), None, "") is None


def test_options_on_the_partner_count_for_course_and_language():
    school = partner("交換學生", program_options=[PartnerProgramOption(
        program_type="交換學生（日語組）", eligibility="日本語 N2 以上，可選修設計課程", source_url="https://example.edu/p")])
    assert teaching_language_fit(school, "japanese").basis == "partner_track"
    assert course_interest_fit(school, None, "設計").status == "mentioned"


def test_bundled_destination_profiles_yield_honest_budget_results():
    profiles = storage.load_destination_profiles()
    assert len(profiles) == 571
    statuses = {}
    for row in profiles:
        fit = school_budget_fit(row, 40000)
        statuses[fit.status] = statuses.get(fit.status, 0) + 1
        if fit.status != "unknown":
            assert fit.estimate and fit.estimate.evidence and fit.estimate.source_urls
    assert statuses.get("unknown", 0) > 200, "most schools publish no comparable monthly total"
    assert sum(count for status, count in statuses.items() if status != "unknown") >= 15


def dashboard_with(partners: list[PartnerUniversity]) -> StudentDashboard:
    return StudentDashboard(school_name="長庚大學", academic_score_minimum=60, partner_universities=partners)


def test_advisor_uses_budget_language_and_courses_without_blocking_eligibility():
    cheap = partner(colleges="全校", degree_levels="大學部", eligibility="IELTS 6.0")
    cheap.school_name = "便宜大學"
    costly = partner(colleges="全校", degree_levels="大學部", eligibility="IELTS 6.0")
    costly.school_name = "昂貴大學"
    unknown = partner(colleges="全校", degree_levels="大學部", eligibility="IELTS 6.0")
    unknown.school_name = "未知大學"
    destinations = [
        profile("官方建議每月生活費約 EUR 500–600。", "便宜大學"),
        profile("官方建議每月生活費約 EUR 2000–2500。", "昂貴大學"),
    ]
    request = AdvisorProfile(college="工學院", degree_level="大學部", academic_score=80, language_test="ielts",
                             language_score=7, monthly_budget=40000, preferred_teaching_language="english",
                             course_interests="資料科學")
    plan = build_advisor_plan(request, dashboard_with([cheap, costly, unknown]), [], [], destinations)
    by_name = {row.school_name: row for row in plan.recommendations}
    assert by_name["便宜大學"].budget_fit.status == "within"
    assert by_name["昂貴大學"].budget_fit.status == "over"
    assert by_name["未知大學"].budget_fit.status == "unknown"
    assert any("無法比對預算" in gap for gap in by_name["未知大學"].gaps)
    assert any("高於你的預算" in gap for gap in by_name["昂貴大學"].gaps)
    assert by_name["便宜大學"].match_score > by_name["昂貴大學"].match_score
    assert by_name["昂貴大學"].eligibility_status == by_name["便宜大學"].eligibility_status
    assert all(row.teaching_language.status == "listed" for row in by_name.values())
    assert all(row.course_interest.status == "unknown" for row in by_name.values())


def test_advisor_without_new_fields_keeps_previous_shape():
    plan = build_advisor_plan(AdvisorProfile(), dashboard_with([partner()]), [], [], [])
    row = plan.recommendations[0]
    assert row.budget_fit is None and row.course_interest is None
