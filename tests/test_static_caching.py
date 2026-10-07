"""Static files had no caching header, so each visit asked again about every one of the ~200 files of a page."""
from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from exchange_info.api import create_app

STATIC = Path(__file__).resolve().parents[1] / "src" / "exchange_info" / "static"


def _client() -> TestClient:
    return TestClient(create_app())


def test_a_versioned_script_may_be_kept_for_a_day_and_an_unversioned_one_is_always_checked() -> None:
    client = _client()
    assert client.get("/static/app.js", params={"v": "20261007-school-2"}).headers["cache-control"] == "public, max-age=86400"
    assert client.get("/static/app.js").headers["cache-control"] == "no-cache"
    assert client.get("/static/product-v2.css").headers["cache-control"] == "no-cache"


def test_fonts_named_after_their_content_are_kept_for_good() -> None:
    client = _client()
    font = next((STATIC / "assets" / "fonts" / "genjyuu").glob("*.woff2"))
    response = client.get(f"/static/assets/fonts/genjyuu/{font.name}")
    assert response.status_code == 200
    assert response.headers["cache-control"] == "public, max-age=31536000, immutable"


def test_pictures_are_kept_for_a_day() -> None:
    client = _client()
    assert client.get("/static/assets/ntpu-campus.jpg").headers["cache-control"] == "public, max-age=86400"


def test_only_successful_static_answers_get_the_header_and_nothing_else_changes() -> None:
    client = _client()
    missing = client.get("/static/assets/does-not-exist.png")
    assert missing.status_code == 404 and "max-age" not in missing.headers.get("cache-control", "")
    health = client.get("/health")
    assert "max-age=86400" not in health.headers.get("cache-control", "")


def test_the_advisor_card_picture_waits_for_its_page_but_the_loading_screen_picture_does_not() -> None:
    html = (STATIC / "index.html").read_text(encoding="utf-8")
    tags = [line for line in html.splitlines() if 'class="uw-mascot-picture"' in line]
    assert len(tags) == 2
    loading_screen, advisor_card = tags
    assert 'loading="lazy"' not in loading_screen and 'fetchpriority="high"' in loading_screen
    assert 'loading="lazy"' in advisor_card


def test_the_pictures_every_visitor_downloads_first_stay_small() -> None:
    """The CGU campus photo was a 1.9 MB, 1920px file shown as a thumbnail and a card picture."""
    assets = STATIC / "assets"
    for name, limit_kb in (("cgu-campus.jpg", 400), ("ntpu-campus.jpg", 400), ("journey/explorer.webp", 400), ("mascot/suitcase.webp", 60)):
        assert (assets / name).stat().st_size < limit_kb * 1024, name
