import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
STATIC = ROOT / "src" / "exchange_info" / "static"
HTML = (STATIC / "index.html").read_text(encoding="utf-8")
SCRIPT = (STATIC / "icon-motion.js").read_text(encoding="utf-8")
STYLES = (STATIC / "icon-motion.css").read_text(encoding="utf-8")


def test_icon_motion_assets_use_one_cache_version() -> None:
    css_version = re.search(r"icon-motion\.css\?v=([^\"']+)", HTML)
    js_version = re.search(r"icon-motion\.js\?v=([^\"']+)", HTML)

    assert css_version
    assert js_version
    assert css_version.group(1) == js_version.group(1)
    assert "/static/vendor/lucide/0.468.0/lucide.min.js" in HTML
    assert "https://unpkg.com/lucide" not in HTML


def test_global_motion_contract_covers_static_and_dynamic_lucide_icons() -> None:
    source = HTML + (STATIC / "app.js").read_text(encoding="utf-8")

    assert source.count("data-lucide") > 300
    assert 'const ICON_SELECTOR = "svg.lucide, svg[data-lucide]"' in SCRIPT
    assert "data-icon-motion" in SCRIPT
    assert ".icon-motion-enter" in STYLES
    assert ":hover" in STYLES
    assert ":focus-visible" in STYLES
    assert ":active" in STYLES


def test_mutation_observer_is_singleton_batched_and_idempotent() -> None:
    assert SCRIPT.count("new MutationObserver(") == 1
    assert "pendingRoots = new Set()" in SCRIPT
    assert "window.requestAnimationFrame" in SCRIPT
    assert "seenEntrances.has(key)" in SCRIPT
    assert 'icon.classList.remove("icon-motion-enter")' in SCRIPT
    assert "window[GLOBAL_KEY]" in SCRIPT


def test_reduced_motion_disables_css_and_morphing() -> None:
    assert '@media (prefers-reduced-motion: reduce)' in STYLES
    assert "animation: none !important" in STYLES
    assert 'matchMedia("(prefers-reduced-motion: reduce)")' in SCRIPT
    assert 'createMorph(path, previousNode || currentNode, { reducedMotion: "user" })' in SCRIPT


def test_only_loading_icons_can_repeat_infinitely() -> None:
    infinite_animations = re.findall(r"animation\s*:[^;{}]*\binfinite\b", STYLES)

    assert len(infinite_animations) == 1
    assert "[aria-busy=\"true\"]" in STYLES
    assert ".lucide-loader-circle" in STYLES
    assert ".lucide-refresh-cw" in STYLES
    assert 'icon.dataset.iconMotionLoop = "spin"' in SCRIPT


def test_morphicons_is_pinned_licensed_and_wired_to_real_state_pairs() -> None:
    manifest = json.loads((STATIC / "vendor" / "manifest.json").read_text(encoding="utf-8"))
    morph_root = STATIC / "vendor" / "morphicons" / "1.7.0"
    lucide_root = STATIC / "vendor" / "lucide" / "0.468.0"

    assert manifest["morphicons"]["version"] == "1.7.0"
    assert manifest["morphicons"]["license"] == "MIT"
    assert manifest["lucide"]["version"] == "0.468.0"
    assert manifest["lucide"]["license"] == "ISC"
    assert (morph_root / "dist" / "dom.js").is_file()
    assert (morph_root / "dist" / "spring-CFHloqPP.js").is_file()
    assert (morph_root / "dist" / "normalize-CYnN3Npw.js").is_file()
    assert (morph_root / "LICENSE").is_file()
    assert (lucide_root / "lucide.min.js").is_file()
    assert (lucide_root / "LICENSE").is_file()
    assert "import(MORPHICONS_URL)" in SCRIPT
    assert "createMorph(path" in SCRIPT
    assert '["sun", "moon"]' in SCRIPT
    assert '["bookmark", "bookmark-check"]' in SCRIPT
    assert '["plus", "check"]' in SCRIPT
    assert '["circle", "circle-check"]' in SCRIPT
    assert '["clipboard-plus", "clipboard-x", "badge-alert"]' in SCRIPT


def test_icon_motion_assets_match_packaging_and_ci_contracts() -> None:
    pyproject = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    workflow = (ROOT / ".github" / "workflows" / "quality.yml").read_text(encoding="utf-8")

    assert '"static/vendor/**/*"' in pyproject
    assert "node --check src/exchange_info/static/icon-motion.js" in workflow
    assert (ROOT / "THIRD_PARTY_NOTICES.md").is_file()
