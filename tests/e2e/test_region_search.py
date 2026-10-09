"""A student can look for a region ("東歐", "Europe") and not only for one country; the lists say what they hold."""
import re

from playwright.sync_api import expect

from .conftest import enter_public_site

NTPU = "國立臺北大學"
EASTERN_EUROPE = ["波蘭", "捷克", "斯洛伐克", "匈牙利", "羅馬尼亞", "立陶宛", "拉脫維亞", "俄羅斯", "阿爾巴尼亞"]


def start(page, live_server, route="partners", school=NTPU):
    page.add_init_script(f"localStorage.setItem('exchange-guide-home-school', '{school}')")
    enter_public_site(page, live_server, route)
    page.wait_for_function("() => document.querySelector('#boot-splash') === null", timeout=60_000)
    page.wait_for_function("() => state.dashboard && state.dashboard.partner_universities.length > 100", timeout=60_000)


def schools_in(page, countries):
    return page.evaluate("countries => state.dashboard.partner_universities.filter(p => countries.includes(p.country)).length", countries)


def shown_total(page):
    return int(page.locator("#partner-table").get_attribute("data-result-count"))


def search(page, text):
    page.locator("#partner-search").fill(text)
    page.wait_for_timeout(300)


def test_searching_for_eastern_europe_finds_every_school_of_those_countries(page, live_server):
    start(page, live_server)
    expected = schools_in(page, EASTERN_EUROPE)
    assert expected >= 28, "NTPU has these schools; the test is only meaningful if they are in the list"
    for word in ("東歐", "中歐", "eastern europe", "Eastern Europe"):
        search(page, word)
        assert shown_total(page) >= expected, word
    search(page, "東歐")
    assert shown_total(page) == expected
    expect(page.locator("#partner-result-count")).to_contain_text(f"共 {expected} 所")


def test_english_country_names_and_europe_work_as_search_words(page, live_server):
    start(page, live_server)
    search(page, "Poland")
    assert shown_total(page) == schools_in(page, ["波蘭"]) >= 8
    search(page, "Czech")
    assert shown_total(page) == schools_in(page, ["捷克"]) == 5
    search(page, "歐洲")
    europe = page.evaluate("() => state.dashboard.partner_universities.filter(p => UniWayRegions.inRegion(p.country, 'europe')).length")
    assert europe > 60 and shown_total(page) >= europe
    search(page, "波羅的海")
    assert shown_total(page) >= schools_in(page, ["立陶宛", "拉脫維亞"])
    search(page, "完全不存在的字串")
    expect(page.locator("#partner-table")).to_contain_text("沒有符合的學校")


def test_the_region_filter_narrows_the_countries_and_clears(page, live_server):
    start(page, live_server)
    region = page.locator("#region-filter")
    expect(region.locator('optgroup[label="歐洲"] option[value="eastern-europe"]')).to_have_count(1)
    assert region.locator('option[value=""]').text_content() == "全部地區"
    region.select_option("eastern-europe")
    assert shown_total(page) == schools_in(page, EASTERN_EUROPE)
    countries = page.locator("#country-filter option").all_text_contents()
    assert countries[0] == "全部國家" and set(countries[1:]) == set(EASTERN_EUROPE), countries
    page.locator("#country-filter").select_option("捷克")
    assert shown_total(page) == 5
    assert "region=eastern-europe" in page.evaluate("location.search") and "country=" in page.evaluate("location.search")
    region.select_option("east-asia")
    expect(page.locator("#country-filter")).to_have_value("")
    assert shown_total(page) == page.evaluate("() => state.dashboard.partner_universities.filter(p => UniWayRegions.inRegion(p.country, 'east-asia')).length")
    region.select_option("europe")
    assert "東歐／中歐" in page.locator("#region-filter option").all_text_contents()
    assert shown_total(page) > schools_in(page, EASTERN_EUROPE)
    page.locator("#clear-partner-filters").click()
    expect(region).to_have_value("")
    expect(page.locator("#country-filter")).to_have_value("")
    assert shown_total(page) == page.evaluate("state.dashboard.partner_universities.length")


def test_the_country_list_is_grouped_by_region_and_a_country_filter_alone_still_works(page, live_server):
    start(page, live_server)
    groups = page.locator("#country-filter optgroup").evaluate_all("els => els.map(e => [e.label, [...e.querySelectorAll('option')].map(o => o.value)])")
    by_label = dict(groups)
    assert set(by_label["東歐／中歐"]) == set(EASTERN_EUROPE)
    assert "日本" in by_label["東亞"] and "法國" in by_label["西歐"]
    page.locator("#country-filter").select_option("波蘭")
    assert shown_total(page) == schools_in(page, ["波蘭"])


def test_a_region_in_the_address_is_applied_and_a_made_up_one_is_dropped(page, live_server):
    start(page, live_server)
    page.goto(f"{live_server.base_url}/?view=list&region=eastern-europe#partners")
    page.wait_for_function("() => document.querySelector('#boot-splash') === null", timeout=60_000)
    page.wait_for_function("() => state.dashboard && document.querySelector('#region-filter').value === 'eastern-europe'", timeout=30_000)
    assert shown_total(page) == schools_in(page, EASTERN_EUROPE)
    page.goto(f"{live_server.base_url}/?view=list&region=atlantis#partners")
    page.wait_for_function("() => state.dashboard && document.querySelector('#region-filter').options.length > 1", timeout=30_000)
    expect(page.locator("#region-filter")).to_have_value("")
    assert shown_total(page) == page.evaluate("state.dashboard.partner_universities.length")


def test_the_czech_schools_have_no_stray_republic_in_their_names(page, live_server):
    start(page, live_server)
    page.locator("#country-filter").select_option("捷克")
    names = page.evaluate("() => state.dashboard.partner_universities.filter(p => p.country === '捷克').map(p => p.school_name)")
    assert len(names) == 5 and not any(name.startswith("Republic") for name in names), names
    assert "布拉格生命科學大學 (Czech University of Life Sciences Prague)" in names
    text = page.locator("#partner-table").inner_text()
    assert "Republic" not in text
    everywhere = page.evaluate("() => state.dashboard.partner_universities.filter(p => /^Republic /.test(p.school_name)).length")
    assert everywhere == 0


def test_the_quota_filter_says_this_period_and_a_signed_school_without_places_is_explained(page, live_server):
    start(page, live_server)
    labels = page.locator("#availability-filter option").all_text_contents()
    assert "當期名額已列" in labels and not any("115" in label for label in labels), labels
    assert {"名額尚未核實", "零名額", "當期名額或期間待確認"} <= set(labels), labels
    page.locator("#availability-filter").select_option("agreement_only")
    signed = shown_total(page)
    assert signed >= 30
    cards = page.locator("#partner-table .mobile-partner-list .partner-card")
    page.set_viewport_size({"width": 390, "height": 844})
    page.wait_for_timeout(200)
    first = cards.first
    card_head = first.locator("summary").first
    expect(card_head).to_contain_text("已簽約・本期沒開放名額")
    card_head.click()
    expect(first.locator(".partner-availability-notice")).to_contain_text("簽有交換合約")
    expect(first.locator(".partner-availability-notice")).to_contain_text("所以現在不能申請")
    page.set_viewport_size({"width": 1280, "height": 900})
    page.wait_for_timeout(200)
    hint = page.locator("#partner-table .desktop-partner-table .availability-hint").first
    expect(hint).to_be_visible()
    expect(hint).to_contain_text("已簽有交換合約，只是這一期沒有開放名額")


def test_the_region_filter_fits_on_a_phone_and_on_a_desktop(page, live_server):
    for width, height in ((390, 844), (1280, 900)):
        page.set_viewport_size({"width": width, "height": height})
        start(page, live_server)
        panel = page.locator(".filter-panel")
        box = panel.bounding_box()
        assert box["x"] >= 0 and box["x"] + box["width"] <= width + 1, (width, box)
        labels = page.locator(".filter-panel > label")
        assert labels.count() == 5
        for index in range(5):
            item = labels.nth(index).bounding_box()
            assert item["width"] > 100 and item["x"] + item["width"] <= width + 1, (width, index, item)
        assert page.evaluate("document.documentElement.scrollWidth") <= width + 1


def test_the_reviews_page_invites_people_who_have_been_on_exchange(page, live_server):
    start(page, live_server, "feedback")
    invite = page.locator("#feedback-invite")
    expect(invite).to_be_visible()
    for word in ("進修部", "東歐", "不具名", "先問過你同意"):
        expect(invite).to_contain_text(word)
    assert re.search(r"成功申請過交換", invite.inner_text())
