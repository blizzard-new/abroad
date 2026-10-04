"""Budget, language and course signals and per-school data gaps are shown without over-claiming."""
import pytest
from playwright.sync_api import expect

from .test_glass_theme import verified_login


def test_new_condition_fields_round_trip_through_the_saved_conditions_payload(page, live_server):
    verified_login(page, live_server)
    page.evaluate("location.hash='#advisor'")
    expect(page.locator('#advisor-teaching-language')).to_have_count(1)
    expect(page.locator('#advisor-course-interests')).to_have_count(1)
    payload = page.evaluate("""() => selectionConditionsPayload({
        college:'工學院', department:'資訊工程學系', currentYear:'大三', degree:'大學部', academicScore:88,
        languageTest:'ielts', languageScore:7, targetTerm:'', preferredCountry:'', monthlyBudget:40000,
        scholarshipNeeded:false, academicYear:'116', applicationRound:'第一梯次',
        teachingLanguage:'english', courseInterests:'資料科學、國際法' })""")
    assert payload['profile']['preferred_teaching_language'] == 'english'
    assert payload['profile']['course_interests'] == '資料科學、國際法'
    restored = page.evaluate("(payload) => selectionProfileFromWorkspace(payload)", payload)
    assert restored['teachingLanguage'] == 'english' and restored['courseInterests'] == '資料科學、國際法'
    invalid = page.evaluate("() => sanitizeSelectionConditions({profile:{preferred_teaching_language:'klingon', course_interests:'x'.repeat(500)}}).profile")
    assert invalid['preferred_teaching_language'] is None and len(invalid['course_interests']) == 120


def test_fit_details_state_reasons_and_never_say_affordable(page, live_server):
    verified_login(page, live_server)
    html = page.evaluate("""() => advisorFitDetails({
        budget_fit:{status:'within', low_twd:18000, high_twd:25000, exclusions:'不含學費、機票、簽證、保險與抵達初期費用。',
            fx_note:'以參考匯率概估。', estimate:{currency:'JPY', low:80000, high:115000, evidence:'每月總生活費約 JPY 80,000–115,000',
            source_urls:['https://example.edu/cost']}},
        teaching_language:{status:'listed', detail:'名額表列在英語組。'},
        course_interest:{status:'unknown', detail:'公開資料沒有逐校課程目錄可比對你填的領域。', evidence:[]}})""")
    assert '在你的預算內' in html and 'NT$18,000–25,000' in html and '不含學費' in html and '概估' in html
    assert '負擔得起' not in html and '足夠' not in html
    assert 'https://example.edu/cost' in html and '費用來源 1' in html
    unknown = page.evaluate("""() => advisorFitDetails({budget_fit:{status:'unknown', reason:'來源沒有可比對的每月生活費金額，請查官方費用頁。'}})""")
    assert '無法比對預算' in unknown and '請查官方費用頁' in unknown
    over = page.evaluate("""() => advisorFitDetails({budget_fit:{status:'over', low_twd:90000, high_twd:120000, exclusions:'x', estimate:{currency:'EUR', low:2500, high:3300, evidence:'e', source_urls:[]}}})""")
    assert '高於你的預算' in over
    assert page.evaluate("() => advisorFitDetails({})") == ''


@pytest.mark.parametrize('width', [390, 1754])
def test_school_page_lists_what_data_is_missing(page, live_server, width):
    page.set_viewport_size({'width': width, 'height': 956})
    page.emulate_media(reduced_motion='reduce')
    errors = []
    page.on('pageerror', lambda error: errors.append(str(error)))
    verified_login(page, live_server)
    page.wait_for_function("() => state.dashboard && state.dashboard.partner_universities.length > 0", timeout=30_000)
    name = page.evaluate("() => state.dashboard.partner_universities[0].school_name")
    page.evaluate("(school) => { location.hash = '#school=' + encodeURIComponent(school); }", name)
    panel = page.locator('details.school-data-completeness')
    expect(panel).to_have_count(1, timeout=15_000)
    panel.locator('summary').click()
    items = page.locator('#school-data-completeness-body .school-completeness-list li')
    expect(items).to_have_count(10, timeout=15_000)
    body = page.locator('#school-data-completeness-body')
    expect(body).to_contain_text('項資料完整')
    expect(body).to_contain_text('不代表學校沒有公開')
    statuses = items.evaluate_all("rows => rows.map(row => row.dataset.completenessStatus)")
    assert set(statuses) <= {'available', 'partial', 'needs_confirmation', 'missing'}
    assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
    assert errors == []
