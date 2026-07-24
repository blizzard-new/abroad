from pathlib import Path


STATIC_DIR = Path(__file__).resolve().parents[1] / "src" / "exchange_info" / "static"


def test_university_sidebar_features_have_independent_pages() -> None:
    html = (STATIC_DIR / "index.html").read_text(encoding="utf-8")

    for route in (
        "overview",
        "advisor",
        "partners",
        "calendar",
        "deadlines",
        "scholarships",
        "budget",
        "eligibility",
        "application-center",
        "document-check",
        "writing-assistant",
        "documents",
        "favorites",
    ):
        assert f'data-section="{route}"' in html
        assert f'data-university-page="{route}"' in html

    assert '<div class="two-column-layout">' not in html


def test_hash_router_shows_one_feature_page_without_scroll_spying() -> None:
    script = (STATIC_DIR / "app.js").read_text(encoding="utf-8")

    assert "const UNIVERSITY_PAGE_ROUTES" in script
    assert "function showUniversityPage" in script
    assert 'document.querySelectorAll("[data-university-page]")' in script
    assert "node.hidden = !activePage" in script
    assert "document.body.dataset.activeUniversityPage" in script
    assert "document.body.dataset.universityPage" not in script
    assert 'window.location.hash = "#partners"' in script
    assert 'window.location.hash = "#search"' in script
    assert "IntersectionObserver" not in script


def test_route_assets_are_cache_busted_together() -> None:
    html = (STATIC_DIR / "index.html").read_text(encoding="utf-8")
    script = (STATIC_DIR / "app.js").read_text(encoding="utf-8")

    assert "product-v2.css?v=20260721-student-survival-5" in html
    assert "app.js?v=20260721-student-survival-5" in html
    assert "function resetRouteScroll()" in script
    assert "window.requestAnimationFrame(scrollToTop)" in script
