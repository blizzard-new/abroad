"""The 出發前提醒 tab and the Chinese write-ups in the 學生心得 tab, against the real bundled data."""
from urllib.parse import urlencode

from playwright.sync_api import expect

CGU = "長庚大學"
# The browser-test server lists a fixed set of partner schools; Wuhan stands for 中國大陸 and Lincoln has curated stories.
WUHAN = "武漢大學 Wuhan University"
LINCOLN = "林肯大學 Lincoln University"
MEIJI = "明治大學 Meiji University"


SEARCH = {WUHAN: "Wuhan", LINCOLN: "Lincoln", MEIJI: "Meiji"}


def open_school(page, live_server, school, home):
    """Find the school in the partner list under the given home school and open its page."""
    query = urlencode({"home": home, "view": "list", "q": SEARCH[school]})
    page.add_init_script("window.sessionStorage.setItem('exchange-guide-browse-first', '1')")
    page.goto(f"{live_server.base_url}/?{query}#partners")
    trigger = page.locator(f'.desktop-partner-table .school-detail-trigger[data-school-name="{school}"]').first
    expect(trigger).to_be_visible(timeout=60_000)
    trigger.click()
    expect(page.locator("#school-detail-title")).to_have_text(school, timeout=60_000)
    page.wait_for_load_state("networkidle", timeout=60_000)


# ----------------------------------------------------------------------------- 出發前提醒


def test_the_departure_tab_shows_the_countrys_guide_with_its_draft_notice_and_sources(page, live_server):
    open_school(page, live_server, WUHAN, CGU)
    tab = page.locator("#detail-tab-prep")
    expect(tab).to_have_text("出發前提醒")
    tab.click()
    panel = page.locator("#detail-prep")
    expect(panel).to_be_visible()
    expect(page.locator("#destination-prep-title")).to_have_text("中國大陸　出發前提醒")
    expect(page.locator("#prep-content .tips-banner")).to_contain_text("尚待人工審核")
    expect(page.locator("#prep-content .tips-banner")).to_contain_text("共 30 項提醒")
    text = page.locator("#prep-content").inner_text()
    for needle in ("台胞證", "國際漫遊", "微信支付", "24 小時內", "備份"):
        assert needle in text, needle
    links = page.locator("#prep-content .tip-sources a")
    assert links.count() >= 30
    hrefs = links.evaluate_all("els => els.map(a => [a.href, a.target, a.rel])")
    assert all(href.startswith("https://") and target == "_blank" and "noreferrer" in rel for href, target, rel in hrefs)
    expect(page.locator("#prep-content .tip[data-importance='must']").first).to_be_visible()


def test_a_school_in_japan_shows_the_japan_guide_with_the_paperwork_and_bank_warnings(page, live_server):
    open_school(page, live_server, MEIJI, CGU)
    page.locator("#detail-tab-prep").click()
    expect(page.locator("#destination-prep-title")).to_have_text("日本　出發前提醒")
    expect(page.locator("#prep-content .tips-banner")).to_contain_text("共 21 項提醒")
    text = page.locator("#prep-content").inner_text()
    for needle in ("14 天內辦住民登錄", "My Number", "絕對不要賣或借出你的銀行帳戶", "080-1009-7179", "先知道駐外館處能幫什麼"):
        assert needle in text, needle
    expect(page.locator("#prep-content .tips-intro")).to_contain_text("手機門號與交通卡等細節還沒查到官方說明")
    assert page.locator(".tips-topic-nav [data-tips-topic]").count() == 6


def test_topic_chips_scroll_in_place_and_never_change_the_page_address(page, live_server):
    open_school(page, live_server, WUHAN, CGU)
    page.locator("#detail-tab-prep").click()
    before = page.evaluate("location.hash")
    chips = page.locator(".tips-topic-nav [data-tips-topic]")
    assert chips.count() == 8
    chips.filter(has_text="付款、銀行與換錢").click()
    assert page.evaluate("location.hash") == before, "the router must not see a chip click as navigation"
    expect(page.locator("#tips-topic-payment")).to_be_in_viewport()
    assert page.evaluate("document.activeElement && document.activeElement.id") == "tips-heading-payment"
    expect(page.locator("#school-detail-title")).to_have_text(WUHAN)


def test_a_country_without_a_guide_gets_a_polite_pointer_to_the_official_site(page, live_server):
    page.route("**/destination-tips?*", lambda route: route.fulfill(status=404, content_type="application/json", body='{"detail":"這個國家的出發前提醒還在整理中。"}'))
    open_school(page, live_server, WUHAN, CGU)
    page.locator("#detail-tab-prep").click()
    empty = page.locator("#prep-content .tips-empty")
    expect(empty).to_contain_text("還在整理中")
    expect(empty.locator("a")).to_have_attribute("href", "https://www.boca.gov.tw/sp-foof-countrylp-03-1.html")


def test_a_server_error_is_not_mistaken_for_a_missing_guide(page, live_server):
    page.route("**/destination-tips?*", lambda route: route.fulfill(status=500, content_type="application/json", body='{"detail":"boom"}'))
    open_school(page, live_server, WUHAN, CGU)
    page.locator("#detail-tab-prep").click()
    expect(page.locator("#prep-content")).to_contain_text("暫時讀不到出發前提醒")


# ----------------------------------------------------------------------------- 學生心得


def test_stories_with_a_chinese_write_up_lead_and_the_rest_are_filed_as_references(page, live_server):
    open_school(page, live_server, LINCOLN, CGU)
    page.locator("#detail-tab-experiences").click()
    cards = page.locator("#experience-content .discovery-experience-card")
    expect(cards.first).to_be_visible()
    assert cards.count() == page.locator("#experience-content .discovery-experience-card.has-digest").count() == 2
    expect(page.locator("#experience-content .discovery-digest-badge")).to_have_count(2)
    others = page.locator("#experience-content .discovery-other-sources")
    if others.count():  # present when the crawl data holds more pages for this school
        others.locator("summary").click()
        expect(others.locator("a").first).to_have_attribute("target", "_blank")
    body = page.locator("#experience-content").inner_text()
    assert "這個來源主要談到" not in body and "中文摘要待補" not in body, "filler sentences are never shown"


def test_opening_a_story_shows_the_chinese_write_up_and_how_it_was_made(page, live_server):
    open_school(page, live_server, LINCOLN, CGU)
    page.locator("#detail-tab-experiences").click()
    card = page.locator("#experience-content .discovery-experience-card.has-digest", has_text="兩學期")
    expect(card).to_have_count(1)
    card.locator("[data-read-experience]").click()
    reader = page.locator("#discovery-reader")
    expect(reader).to_be_visible()
    expect(reader.locator("h2")).to_contain_text("林肯大學交換兩學期")
    headings = reader.locator(".discovery-reader-themes h3").all_inner_texts()
    assert headings[:3] == ["申請與簽證", "課程", "住宿"] and "給之後要去的人" in headings
    assert reader.locator("li").count() >= 15
    expect(reader.locator(".discovery-reader-original")).to_contain_text("不是全文翻譯")
    expect(reader.locator("[data-experience-original]")).to_have_attribute("href", "https://nmbuutveksling.blogspot.com/2024/03/lincoln-university-new-zealand.html")
    page.keyboard.press("Escape")
    expect(reader).to_be_hidden()


def test_a_saved_story_still_opens_with_its_write_up(page, live_server):
    open_school(page, live_server, LINCOLN, CGU)
    page.locator("#detail-tab-experiences").click()
    page.locator("#experience-content .discovery-experience-card.has-digest", has_text="兩學期").locator("[data-save-experience]").click()
    page.goto(f"{live_server.base_url}/?home={CGU}#favorites")
    page.locator("[data-discovery-shelf='experiences']").click()
    saved = page.locator("#discovery-saved-experiences .discovery-experience-card")
    expect(saved).to_have_count(1)
    expect(saved).to_contain_text("中文整理")
    saved.locator("[data-read-experience]").click()
    expect(page.locator("#discovery-reader .discovery-reader-themes h3").first).to_have_text("申請與簽證")
