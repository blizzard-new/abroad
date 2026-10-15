"""The lists of schools show every school (or say how many more there are), and a country the student chose is honoured."""
import re

import pytest
from playwright.sync_api import expect

from .conftest import enter_public_site

NTPU = "國立臺北大學"
PROFILE = {"college": "商學院", "degree_level": "大學部", "academic_score": 85, "language_test": "toeic", "language_score": 800}

FETCH_PLAN = """async ([school, profile]) => {
  const response = await fetch('/advisor/plan', {method: 'POST', headers: {'Content-Type': 'application/json'},
                                                 body: JSON.stringify({school_name: school, ...profile})});
  return await response.json();
}"""


def start(page, live_server, school, route):
    page.add_init_script(f"localStorage.setItem('exchange-guide-home-school', '{school}')")
    enter_public_site(page, live_server, route)
    page.wait_for_function("() => document.querySelector('#boot-splash') === null", timeout=60_000)


def advisor_plan(page, school, **extra):
    return page.evaluate(FETCH_PLAN, [school, {**PROFILE, **extra}])


def show(page, plan):
    page.evaluate("plan => { state.advisorPlan = plan; renderAdvisorResult(plan); }", plan)


def test_a_country_the_student_chose_gets_only_that_country_and_says_so(page, live_server):
    start(page, live_server, NTPU, "advisor")
    everywhere = advisor_plan(page, NTPU)
    assert len({row["country"] for row in everywhere["recommendations"]}) > 3, "without a choice, schools from many countries"
    plan = advisor_plan(page, NTPU, preferred_country="大陸地區")
    assert plan["recommendations"] and {row["country"] for row in plan["recommendations"]} == {"大陸地區"}
    assert plan["summary"].startswith("已依你選的「大陸地區」，只列出該地區的")
    show(page, plan)
    heading = page.locator("#advisor-result-content .advisor-summary-card h3")
    expect(heading).to_contain_text("只列出該地區")
    countries = page.locator("#advisor-result-content .advisor-school-copy > span:first-child").all_text_contents()
    assert countries and set(countries) == {"大陸地區"}, set(countries)
    assert "德國" not in page.locator("#advisor-result-content").inner_text()


def test_every_recommended_school_is_reachable_not_just_the_first_five(page, live_server):
    start(page, live_server, NTPU, "advisor")
    plan = advisor_plan(page, NTPU, preferred_country="日本")
    waiting = [row for row in plan["recommendations"] if row["eligibility_status"] == "needs_confirmation"]
    assert len(waiting) > 5, "this school has more than five Japanese schools to confirm"
    show(page, plan)
    group = page.locator('#advisor-result-content [data-match-group="needs_confirmation"]')
    assert group.locator(".advisor-school-card").count() == len(waiting), "all of them are on the page"
    visible = group.locator(".match-group-cards").first.locator(".advisor-school-card")
    expect(visible).to_have_count(5)
    more = group.locator(".match-more > summary")
    expect(more).to_be_visible()
    expect(more).to_contain_text(f"再看其他 {len(waiting) - 5} 所")
    assert more.bounding_box()["height"] >= 44
    expect(group.locator(".match-more .advisor-school-card").first).to_be_hidden()
    more.click()
    expect(more).to_contain_text("收合")
    expect(group.locator(".match-more .advisor-school-card").first).to_be_visible()
    expect(group.locator(".match-more .advisor-school-card").last).to_be_attached()


def test_a_small_group_has_no_show_more_button(page, live_server):
    start(page, live_server, NTPU, "advisor")
    plan = advisor_plan(page, NTPU)
    plan["recommendations"] = [row for row in plan["recommendations"] if row["eligibility_status"] == "needs_confirmation"][:4]
    show(page, plan)
    waiting = page.locator('#advisor-result-content [data-match-group="needs_confirmation"]')
    expect(waiting.locator(".advisor-school-card")).to_have_count(4)
    expect(page.locator("#advisor-result-content .match-more")).to_have_count(0)


def test_a_country_with_no_open_school_says_so_and_lists_the_others(page, live_server):
    start(page, live_server, NTPU, "advisor")
    plan = advisor_plan(page, NTPU, preferred_country="巴西")
    assert plan["summary"].startswith("目前沒有「巴西」的開放合作校")
    assert plan["recommendations"], "the student is not left with an empty page"


@pytest.mark.parametrize("width,first_page", [(390, 20), (1280, 30)])
def test_the_school_list_shows_a_full_page_and_the_count(page, live_server, width, first_page):
    page.set_viewport_size({"width": width, "height": 900})
    start(page, live_server, NTPU, "partners")
    count = page.locator("#partner-result-count")
    expect(count).to_have_text(re.compile(rf"^共 \d+ 所，先顯示 {first_page} 所$"))
    total = int(re.search(r"共 (\d+) 所", count.inner_text()).group(1))
    assert total > 100
    rows = "#partner-table .pr-school-card"
    expect(page.locator(rows)).to_have_count(first_page)
    page.locator("#show-more-partners").click()
    expect(count).to_have_text(f"共 {total} 所，先顯示 {first_page * 2} 所")
    expect(page.locator(rows)).to_have_count(first_page * 2)


def test_filtering_to_a_country_shows_all_of_its_schools_and_only_those(page, live_server):
    start(page, live_server, NTPU, "partners")
    page.select_option("#country-filter", "大陸地區")
    count = page.locator("#partner-result-count")
    expect(count).to_have_text(re.compile(r"^共 \d+ 所"))
    total = int(re.search(r"共 (\d+) 所", count.inner_text()).group(1))
    while page.locator("#show-more-partners").is_visible():
        page.locator("#show-more-partners").click()
    countries = [text.split("・")[0] for text in page.locator("#partner-table .pr-card-place").all_inner_texts()]
    assert len(countries) == total and set(countries) == {"大陸地區"}
    expect(count).to_have_text(f"共 {total} 所")
