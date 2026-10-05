"""The UniWay logo: tab icons, the in-page brand mark and the script that builds them."""
from __future__ import annotations

import importlib.util
import io
import re
import shutil
import sys
from pathlib import Path

from fastapi.testclient import TestClient
from PIL import Image

from exchange_info.api import STATIC_DIR, create_app

BRAND_DIR = STATIC_DIR / "assets" / "brand"
PAGES = ("index.html", "content-review.html", "api-contract.html", "analytics-dashboard.html")
SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "build_brand_assets.py"


def load_builder():
    spec = importlib.util.spec_from_file_location("build_brand_assets", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    sys.modules["build_brand_assets"] = module
    spec.loader.exec_module(module)
    return module


def test_every_page_points_its_tab_icon_at_the_logo_files_that_exist():
    for page in PAGES:
        html = (STATIC_DIR / page).read_text(encoding="utf-8")
        assert "data:image/svg+xml" not in html, f"{page} still has the old inline icon"
        icons = re.findall(r'<link rel="(?:icon|apple-touch-icon)"[^>]*href="([^"?]+)', html)
        assert icons, f"{page} has no tab icon"
        for href in icons:
            assert href.startswith("/static/assets/brand/"), (page, href)
            assert (STATIC_DIR / href.removeprefix("/static/")).is_file(), (page, href)


def test_the_home_page_declares_every_icon_size_and_loads_the_brand_stylesheet_last():
    html = (STATIC_DIR / "index.html").read_text(encoding="utf-8")
    for fragment in ('sizes="any"', 'sizes="32x32"', 'sizes="16x16"', 'rel="apple-touch-icon" sizes="180x180"'):
        assert fragment in html
    assert html.rindex('href="/static/brand.css') > html.rindex('href="/static/document-workbench.css')
    assert (STATIC_DIR / "brand.css").is_file()


def test_every_brand_mark_shows_the_logo_instead_of_a_stock_icon():
    html = (STATIC_DIR / "index.html").read_text(encoding="utf-8")
    marks = re.findall(r'<span class="brand-mark"[^>]*>(.*?)</span>', html)
    assert len(marks) == 5, "side rail header, phone drawer header, phone top bar and the two sidebar brands"
    mobile_bar = html.split('<header class="glass-mobile-header">', 1)[1].split("</header>", 1)[0]
    assert "brand-mark" in mobile_bar and 'data-lucide="send"' not in mobile_bar
    for inner in marks:
        assert "uniway-mark.webp" in inner and "data-lucide" not in inner
        assert 'alt=""' in inner and 'width="40"' in inner and 'height="40"' in inner


def test_the_sign_in_and_school_dialogs_show_the_logo_not_a_compass():
    html = (STATIC_DIR / "index.html").read_text(encoding="utf-8")
    marks = re.findall(r'<span class="platform-mark"[^>]*>(.*?)</span>', html)
    assert len(marks) == 2, "school picker heading and sign-in dialog heading"
    assert all("uniway-mark.webp" in inner and "compass" not in inner for inner in marks)
    css = (STATIC_DIR / "brand.css").read_text(encoding="utf-8")
    assert "platform-mark img" in css and not re.search(r"!important\s*;", css)


def test_logo_images_have_the_sizes_browsers_expect():
    def size(name):
        with Image.open(BRAND_DIR / name) as image:
            return image.size, image.mode

    assert size("favicon-16.png") == ((16, 16), "RGBA")
    assert size("favicon-32.png") == ((32, 32), "RGBA")
    assert size("apple-touch-icon.png") == ((180, 180), "RGB")
    assert size("uniway-mark.webp") == ((160, 160), "RGBA")
    with Image.open(BRAND_DIR / "favicon.ico") as icon:
        assert {(16, 16), (32, 32), (48, 48)} <= set(icon.info["sizes"])
    with Image.open(BRAND_DIR / "uniway-logo.webp") as source:
        assert source.size == (1254, 1254) and source.mode == "RGBA", "the supplied logo, with a transparent background"
        assert source.getchannel("A").getextrema() == (0, 255)
    with Image.open(BRAND_DIR / "uniway-logo-glow.webp") as old:
        assert old.size == (1536, 1024), "the earlier glow-on-black version is kept for reference"
    assert all(path.stat().st_size < 160_000 for path in BRAND_DIR.glob("*"))


def test_icons_are_transparent_so_they_suit_light_and_dark_tab_bars():
    for name in ("favicon-16.png", "favicon-32.png", "uniway-mark.webp"):
        with Image.open(BRAND_DIR / name) as image:
            alpha = image.convert("RGBA").getchannel("A")
            assert alpha.getextrema() == (0, 255), name
            assert alpha.getpixel((0, 0)) == 0, f"{name}: the corner is see-through"
    with Image.open(BRAND_DIR / "apple-touch-icon.png") as touch:
        assert touch.getpixel((0, 0)) == (255, 255, 255), "iOS needs an opaque square, so it sits on white"


def test_the_favicon_route_serves_the_icon_even_for_pages_without_a_link(tmp_path):
    response = TestClient(create_app(tmp_path)).get("/favicon.ico")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("image/x-icon")
    assert response.headers["cache-control"] == "public, max-age=86400"
    assert response.content == (BRAND_DIR / "favicon.ico").read_bytes()
    assert "/favicon.ico" not in TestClient(create_app(tmp_path)).get("/openapi.json").json()["paths"]


def test_the_icon_and_mark_pass_the_content_security_policy(tmp_path):
    client = TestClient(create_app(tmp_path))
    policy = client.get("/").headers["content-security-policy"]
    assert "img-src 'self'" in policy
    for name in ("favicon-32.png", "uniway-mark.webp", "apple-touch-icon.png"):
        assert client.get(f"/static/assets/brand/{name}").status_code == 200
    assert client.get("/static/brand.css").headers["content-type"].startswith("text/css")


def test_the_build_script_regenerates_the_icon_set_from_the_source_logo(tmp_path):
    builder = load_builder()
    shutil.copy(BRAND_DIR / "uniway-logo.webp", tmp_path / "uniway-logo.webp")
    builder.BRAND_DIR, builder.SOURCE = tmp_path, tmp_path / "uniway-logo.webp"
    builder.main()
    committed = {path.name for path in BRAND_DIR.iterdir()} - {"uniway-logo-glow.webp"}  # kept for reference, never generated
    assert {path.name for path in tmp_path.iterdir()} == committed
    icon = Image.open(io.BytesIO((tmp_path / "favicon.ico").read_bytes()))
    assert icon.size == (64, 64) or (64, 64) in icon.info["sizes"]
    rebuilt = Image.open(tmp_path / "favicon-32.png")
    assert rebuilt.getpixel((0, 0))[3] == 0 and rebuilt.getchannel("A").getextrema()[1] == 255


def test_the_frame_centres_the_mark_on_a_transparent_square_of_any_margin():
    builder = load_builder()
    logo = Image.open(BRAND_DIR / "uniway-logo.webp").convert("RGBA")
    box = builder.mark_box(logo)
    left, top, right, bottom = box
    assert 60 < left < 110 and 50 < top < 110 and 1180 < right < 1250 and 1170 < bottom < 1254
    tight = builder.framed(logo, box, 1.0)
    assert tight.width == tight.height == max(right - left, bottom - top)
    roomy = builder.framed(logo, box, 1.5)
    assert roomy.width == roomy.height == round(tight.width * 1.5), "a margin larger than the picture still works"
    assert roomy.getpixel((0, 0))[3] == 0
    inner = builder.mark_box(roomy)
    assert abs(inner[0] - (roomy.width - inner[2])) <= 2, "centred left to right"


def test_a_fully_transparent_logo_is_refused():
    builder = load_builder()
    try:
        builder.mark_box(Image.new("RGBA", (10, 10), (0, 0, 0, 0)))
    except SystemExit as stop:
        assert "transparent" in str(stop)
    else:
        raise AssertionError("expected SystemExit")
