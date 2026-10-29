"""The application map is the entry; existing tools remain reachable."""
from __future__ import annotations

import re

from exchange_info.api import STATIC_DIR

HTML = (STATIC_DIR / "index.html").read_text(encoding="utf-8")
SCRIPT = (STATIC_DIR / "app.js").read_text(encoding="utf-8")


def rail_entry() -> str:
    match = re.search(r'<a [^>]*data-public-route="overview"[^>]*>', HTML)
    assert match, "the left rail has no 我的申請 link"
    return match.group(0)


def test_the_rail_entry_opens_the_account_application_map():
    entry = rail_entry()
    assert 'href="#my-application"' in entry
    assert "data-requires-home-school" in entry, "a student with no school is asked for one, then lands on the same page"
    assert "我的申請" in HTML.split(entry, 1)[1].split("</a>", 1)[0]


def test_the_dropdown_keeps_the_existing_tools_after_the_map():
    panel = HTML.split('<nav class="application-tools-panel"', 1)[1].split("</nav>", 1)[0]
    stages = re.findall(r'<a href="(#[a-z-]+)" data-requires-home-school>([^<]+)</a>', panel)[:4]
    assert stages == [("#my-application", "申請地圖與進度"), ("#advisor", "選校與確認"), ("#overview", "準備與時程"), ("#application-center", "申請文件")]


def test_an_account_less_student_is_sent_to_the_same_page_after_choosing_a_school():
    # The school picker remembers the link that was clicked and replays it, so the entry above decides the page.
    assert 'state.pendingPersonalizedHash = personalizedLink.getAttribute("href") || "";' in SCRIPT
    assert "window.location.hash = pendingPersonalizedHash;" in SCRIPT


def test_the_rail_entry_stays_highlighted_on_every_application_page():
    function = SCRIPT.split("function isPersonalizedRoute", 1)[1].split("\n}\n", 1)[0]
    for route in ("#advisor", "#overview", "#application-center"):
        assert f'"{route}"' in function, route
    assert 'isPersonalizedRoute(hash) ? "overview"' in SCRIPT, "the link keeps its identity even though it opens #advisor"


def test_other_deliberate_links_into_preparation_are_unchanged():
    assert re.search(r'class="guide-plan-link" href="#overview"', HTML), "the guide page's 回到我的交換計畫 card"
    assert 'window.location.hash = "#overview";\n  announce("已設定目標學校' in SCRIPT, "choosing a target moves on to scheduling"
