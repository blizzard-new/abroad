"""The phone and tablet fixes live in one stylesheet that must load after all the others."""
from __future__ import annotations

import re
from pathlib import Path

STATIC = Path(__file__).resolve().parents[1] / "src" / "exchange_info" / "static"


def test_the_responsive_stylesheet_is_the_last_one_the_page_loads() -> None:
    html = (STATIC / "index.html").read_text(encoding="utf-8")
    sheets = re.findall(r'<link rel="stylesheet" href="(/static/[^"?]+\.css)', html)
    assert sheets[-1] == "/static/responsive.css", sheets[-3:]
    assert (STATIC / "responsive.css").is_file()


def test_it_carries_the_fixes_found_by_looking_at_the_site_on_phones() -> None:
    css = (STATIC / "responsive.css").read_text(encoding="utf-8")
    # Fields under 16px make iOS zoom the page when tapped.
    assert re.search(r"@media \(max-width: 820px\), \(pointer: coarse\)\s*\{[^}]*select,[^}]*textarea\s*\{\s*font-size: 16px !important", css, re.S)
    # The compose button was squeezed to a 48px box with its words spilling out between 561 and 820px.
    assert "@media (min-width: 561px) and (max-width: 820px)" in css and "#global-community-compose" in css
    # Cards whose text column shrank to a sliver on a 320px phone.
    assert ".planning-target-summary > div" in css and ".planning-documents > div" in css
    assert "overflow-wrap: break-word" in css and "text-size-adjust: 100%" in css


def test_the_page_still_declares_a_viewport_and_does_not_block_zooming() -> None:
    html = (STATIC / "index.html").read_text(encoding="utf-8")
    viewport = re.search(r'<meta name="viewport" content="([^"]+)"', html).group(1)
    assert "width=device-width" in viewport and "initial-scale=1" in viewport
    assert "maximum-scale" not in viewport and "user-scalable=no" not in viewport.replace(" ", "")
