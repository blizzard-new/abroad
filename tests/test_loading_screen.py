"""The loading screen with the mascot: it is the first thing in the page, it cannot get stuck, and the page tells it when to go."""
from __future__ import annotations

import re
from pathlib import Path

STATIC = Path("src/exchange_info/static")
HTML = (STATIC / "index.html").read_text(encoding="utf-8")
CSS = (STATIC / "mascot.css").read_text(encoding="utf-8")
MASCOT_JS = (STATIC / "mascot.js").read_text(encoding="utf-8")
APP_JS = (STATIC / "app.js").read_text(encoding="utf-8")
BODY = HTML[HTML.index("<body"):]


def test_the_loading_screen_is_the_first_thing_in_the_body_and_is_announced_politely() -> None:
    assert re.match(r'<body[^>]*>\s*<div id="boot-splash" class="boot-splash" role="status" aria-live="polite">', BODY)
    screen = BODY[:BODY.index("</div>")]
    assert "正在載入中" in screen
    assert 'class="uw-mascot" data-mood="busy" data-play aria-hidden="true"' in screen
    assert screen.count('class="uw-mascot-eye"') == 2
    assert 'src="/static/assets/mascot/suitcase.webp?v=' in screen and 'fetchpriority="high"' in screen


def test_its_script_is_an_external_file_because_the_page_forbids_inline_scripts() -> None:
    assert "script-src 'self'" in Path("src/exchange_info/api.py").read_text(encoding="utf-8")
    scripts = re.findall(r"<script\b([^>]*)>", HTML)
    assert scripts and all("src=" in attrs for attrs in scripts), "an inline script would be blocked"
    screen_end = BODY.index("</div>") + len("</div>")
    assert re.match(r'\s*<script src="/static/mascot\.js\?v=[^"]+"></script>', BODY[screen_end:]), "plain, not deferred"


def test_with_scripts_turned_off_the_screen_is_hidden_instead_of_covering_the_page() -> None:
    assert "<noscript><style>.boot-splash { display: none !important; }</style></noscript>" in HTML


def test_it_hides_itself_even_if_the_page_script_never_finishes() -> None:
    life = re.search(r"\.splash-on \.boot-splash \{[^}]*animation: boot-splash-life (\d+)s linear both", CSS)
    assert life, "a CSS animation, not the page script, is the last resort"
    give_up = int(re.search(r"GIVE_UP_MS = (\d+)", MASCOT_JS).group(1))
    assert int(life.group(1)) * 1000 == give_up, "the script and the stylesheet give up together"
    keyframes = re.search(r"@keyframes boot-splash-life \{(.*?)\n\}\n", CSS, re.S).group(1)
    assert re.search(r"100% \{\s*opacity: 0;\s*visibility: hidden;", keyframes)
    reduced = CSS[CSS.index("@media (prefers-reduced-motion: reduce)"):]
    assert ".splash-on .boot-splash {" in reduced and "opacity: 1;" in reduced, "with no motion it is simply shown"


def test_a_fast_load_never_shows_it_and_a_shown_one_does_not_flicker() -> None:
    show_after = int(re.search(r"SHOW_AFTER_MS = (\d+)", MASCOT_JS).group(1))
    life_seconds = int(re.search(r"animation: boot-splash-life (\d+)s", CSS).group(1))
    invisible = re.search(r"0%,\s*(\d+(?:\.\d+)?)% \{\s*opacity: 0;", CSS).group(1)
    assert abs(float(invisible) / 100 * life_seconds * 1000 - show_after) < 40, "the CSS delay equals the script's"
    assert int(re.search(r"SHOW_FOR_MS = (\d+)", MASCOT_JS).group(1)) >= 500


def test_the_page_tells_it_to_go_only_when_everything_is_loaded_and_whatever_happens() -> None:
    boot = APP_JS[APP_JS.index("async function boot()"):]
    assert APP_JS.count("UniWaySplash") == 1, "one place, after the whole start-up, takes it away"
    assert APP_JS.rstrip().endswith("boot().finally(() => window.UniWaySplash?.done());")
    # the last four loads of the start-up are awaited together before it ends: nothing is left "loading" behind the screen
    assert "await Promise.allSettled([loadGlobalCommunity(), loadCoverage(), loadDestinationProfiles(), state.periodOptionsReady]);" in boot
    assert boot.index("await loadDashboard()") < boot.index("Promise.allSettled")
    assert "state.periodOptionsReady = loadApplicationPeriodOptions();" in APP_JS
    assert "window.UniWaySplash = { done };" in MASCOT_JS
    give_up = int(re.search(r"GIVE_UP_MS = (\d+)", MASCOT_JS).group(1))
    assert give_up >= 45_000, "a server that has just woken up can take most of a minute"


def test_the_motion_includes_blinking_hopping_and_turning_and_stops_for_reduced_motion() -> None:
    for name in ("uw-mascot-blink", "uw-mascot-hop", "uw-mascot-spin", "uw-mascot-wink", "uw-mascot-busy", "uw-mascot-look"):
        assert f"@keyframes {name}" in CSS
    assert "rotateY(360deg)" in CSS, "a full turn"
    reduced = CSS[CSS.index("@media (prefers-reduced-motion: reduce)"):]
    assert ".uw-mascot *" in reduced and "animation: none !important" in reduced
    assert "reduced()" in MASCOT_JS, "the tap moves are skipped as well"


def test_tapping_the_mascot_cycles_hop_spin_wink() -> None:
    assert 'const MOVES = ["hop", "spin", "wink"];' in MASCOT_JS
    assert ".uw-mascot[data-play]" in MASCOT_JS and "pointer-events: auto" in CSS


def test_the_script_and_style_versions_are_in_the_page() -> None:
    assert re.search(r'/static/mascot\.css\?v=\S+"', HTML) and re.search(r'/static/mascot\.js\?v=\S+"', HTML)
    versions = set(re.findall(r"/static/(?:mascot\.css|mascot\.js|advisor-mascot\.css|assets/mascot/suitcase\.webp)\?v=([\w-]+)", HTML))
    assert versions == {"20261007-ready-1"}, "bumped together so nobody keeps an old copy"


def test_it_cannot_show_before_the_saved_theme_is_applied() -> None:
    base = re.search(r"^\.boot-splash \{(.*?)^\}", CSS, re.S | re.M).group(1)
    assert "opacity: 0;" in base and "visibility: hidden;" in base and "animation" not in base
    theme = MASCOT_JS.index('dataset.theme = "dark"')
    assert theme < MASCOT_JS.index('classList.add("splash-on")'), "the colours first, then the screen may appear"
    assert ".splash-on .boot-splash.is-leaving" in CSS
    reduced = CSS[CSS.index("@media (prefers-reduced-motion: reduce)"):]
    assert ".splash-on .boot-splash {" in reduced and "opacity: 1;" in reduced, "with no motion it is simply shown"
