from pathlib import Path


STATIC_DIR = Path(__file__).resolve().parents[1] / "src" / "exchange_info" / "static"


def test_uniway_brand_and_public_discovery_are_present() -> None:
    html = (STATIC_DIR / "index.html").read_text(encoding="utf-8")

    assert "UniWay｜臺灣大學生留學與交換平台" in html
    assert 'class="uniway-header-brand"' in html
    assert 'class="uniway-public-nav"' in html
    assert 'class="uniway-global-discovery"' not in html
    assert "開啟你的國際未來" not in html
    assert 'id="uniway-global-search-form"' not in html
    assert 'class="uniway-quick-grid"' not in html
    assert 'class="uniway-destinations"' not in html
    assert 'id="travel-home"' not in html
    assert 'id="travel-search-form"' not in html


def test_personalized_routes_require_school_but_public_search_does_not() -> None:
    html = (STATIC_DIR / "index.html").read_text(encoding="utf-8")
    script = (STATIC_DIR / "app.js").read_text(encoding="utf-8")

    assert 'href="#partners" data-section="partners"' in html
    assert 'href="#advisor" data-section="advisor" data-requires-home-school' in html
    assert 'href="#application-center" data-section="application-center" data-requires-home-school' in html
    assert 'href="#documents" data-section="documents" data-requires-home-school' in html
    assert "function isPublicExplorationRoute" in script
    assert "function isPersonalizedRoute" in script
    assert 'document.body.classList.toggle("public-exploration-mode"' in script
    assert 'state.pendingPersonalizedHash = personalizedLink.getAttribute("href")' in script
    assert 'if (isPersonalizedRoute() && !state.homeSchool) initializeSchoolOnboarding();' in script


def test_mobile_navigation_has_the_five_approved_destinations() -> None:
    html = (STATIC_DIR / "index.html").read_text(encoding="utf-8")

    for nav_class in ("global-mobile-nav", "university-mobile-nav"):
        start = html.index(f'class="mobile-nav {nav_class}"')
        end = html.index("</nav>", start)
        nav = html[start:end]
        for label in ("首頁", "搜尋", "申請", "收藏", "我的"):
            assert f"<span>{label}</span>" in nav


def test_uniway_theme_supports_light_dark_mobile_and_reduced_motion() -> None:
    styles = (STATIC_DIR / "uniway.css").read_text(encoding="utf-8")

    assert 'html[data-theme="dark"]' in styles
    assert "@media (max-width: 820px)" in styles
    assert "grid-template-columns: repeat(5, minmax(0, 1fr));" in styles
    assert "@media (prefers-reduced-motion: reduce)" in styles
    assert ".public-exploration-mode .global-community-section" in styles
    assert "--uw-blue: #1769df" in styles
