"""Home is the product-story landing; the community feed lives at 論壇 (#forum) in the menu."""
from __future__ import annotations

import re
from pathlib import Path

STATIC = Path("src/exchange_info/static")
HTML = (STATIC / "index.html").read_text(encoding="utf-8")
SCRIPT = (STATIC / "app.js").read_text(encoding="utf-8")


def _menu_links() -> list[tuple[str, str, str]]:
    menu = re.search(r'<nav class="uniway-public-nav".*?</nav>', HTML, re.S).group(0)
    return re.findall(r'<a href="(#[^"]+)" data-public-route="([^"]+)"[^>]*>.*?<span>([^<]+)</span></a>', menu, re.S)


def test_the_menu_reads_home_search_forum_reviews_then_my_application() -> None:
    assert _menu_links() == [
        ("#home", "home", "首頁"),
        ("#partners", "partners", "學校搜尋"),
        ("#forum", "forum", "論壇"),
        ("#feedback", "feedback", "用戶評價"),
        ("#advisor", "overview", "我的申請"),
    ]
    assert "申請指南</span></a>" not in re.search(r'<nav class="uniway-public-nav".*?</nav>', HTML, re.S).group(0)


def test_every_link_to_the_all_posts_feed_goes_to_the_forum() -> None:
    links = re.findall(r'<a [^>]*data-community-route="all"[^>]*>', HTML)
    assert links and all('href="#forum"' in link for link in links), links


def test_the_home_address_shows_the_landing_and_the_forum_address_the_feed() -> None:
    assert '"#forum": "all"' in SCRIPT and '"#home": "all"' not in SCRIPT
    assert re.search(r'function isPublicExplorationRoute\(.*?\) \{\s*return hash === "#home"', SCRIPT, re.S)
    assert 'const sectionId = hash === "#home" ? "home"' in SCRIPT
    assert 'UNIVERSITY_PAGE_TITLES = {\n  home: "首頁"' in SCRIPT
    assert re.search(r'<section id="home-landing"[^>]*data-university-page="home"', HTML)


def test_the_guide_is_its_own_page_and_the_old_community_hub_address_still_opens_the_forum() -> None:
    assert re.search(r'const guideRoute = hash\.match\(/\^#guide\(\?:=\(\.\+\)\)\?\$/\)', SCRIPT)
    assert "window.UniWayGuide?.show(" in SCRIPT
    assert re.search(r'<section id="guide"[^>]*data-university-page="guide"', HTML)
    assert '"#forum" : "#home"' in SCRIPT, "the old #community-hub address opens the forum"


def test_the_brand_and_back_links_still_lead_to_the_new_home() -> None:
    assert 'class="uniway-header-brand" href="#home"' in HTML
    assert HTML.count('href="#home"') >= 5
