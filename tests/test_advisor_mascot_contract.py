from __future__ import annotations

import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
STATIC_DIR = ROOT / "src" / "exchange_info" / "static"
MASCOT_PICTURE = STATIC_DIR / "assets" / "mascot" / "suitcase.webp"
HTML = (STATIC_DIR / "index.html").read_text(encoding="utf-8")
SCRIPT = (STATIC_DIR / "app.js").read_text(encoding="utf-8")
MASCOT_STYLES = STATIC_DIR / "advisor-mascot.css"


def _css_without_comments(source: str) -> str:
    return re.sub(r"/\*.*?\*/", "", source, flags=re.DOTALL)


def test_the_mascot_picture_is_a_small_transparent_webp_and_the_old_pictures_are_gone() -> None:
    payload = MASCOT_PICTURE.read_bytes()
    assert payload[:4] == b"RIFF" and payload[8:12] == b"WEBP"
    assert payload[12:16] == b"VP8X", "an extended WebP, so it can carry transparency"
    assert payload[20] & 0x10, "the alpha flag is set"
    width = int.from_bytes(payload[24:27], "little") + 1
    height = int.from_bytes(payload[27:30], "little") + 1
    assert (width, height) == (384, 460)
    assert len(payload) < 60 * 1024, "every visitor downloads it before the page shows"
    assert not (STATIC_DIR / "assets" / "advisor-mascot").exists(), "the old pictures are no longer shipped"
    assert "advisor-mascot/" not in HTML and "advisor-mascot-image" not in HTML


def test_advisor_markup_keeps_the_assistant_and_result_content_persistent() -> None:
    assert HTML.count('id="advisor-assistant"') == 1
    assert HTML.count('id="advisor-result-content"') == 1
    assert re.search(
        r'<link\b[^>]*href=["\'][^"\']*advisor-mascot\.css(?:\?[^"\']*)?["\']',
        HTML,
        flags=re.IGNORECASE,
    )

    assistant = HTML[HTML.index('id="advisor-assistant"'):HTML.index('id="advisor-result-content"')]
    assert assistant.count('class="uw-mascot"') == 1
    assert assistant.count('class="uw-mascot-eye"') == 2, "two eyes, drawn by the stylesheet"
    pictures = re.findall(r"<img\b[^>]*>", assistant)
    assert len(pictures) == 1 and "/static/assets/mascot/suitcase.webp" in pictures[0]
    assert HTML.index("mascot.css") < HTML.index("advisor-mascot.css"), "the card's rules build on the mascot's"

    assert re.search(r'\$\("#advisor-result-content"\)\.innerHTML\s*=', SCRIPT)
    assert not re.search(r'\$\("#advisor-result"\)\.innerHTML\s*=', SCRIPT)
    assert re.search(
        r'(?:const|let)\s+\w+\s*=\s*\$\("#advisor-result-content"\)',
        SCRIPT,
    )


def test_advisor_assistant_script_exposes_all_five_states() -> None:
    assert re.search(
        r"(?:function\s+setAdvisorAssistantState\s*\(|"
        r"(?:const|let)\s+setAdvisorAssistantState\s*=)",
        SCRIPT,
    )

    state_literals = set(
        re.findall(
            r'["\'](idle|loading|success|insufficient|error)["\']',
            SCRIPT,
        )
    )
    assert state_literals == {"idle", "loading", "success", "insufficient", "error"}
    assert "正在整理官方資料" in SCRIPT


def test_limited_and_not_found_evidence_select_the_insufficient_state() -> None:
    insufficient_occurrences = list(
        re.finditer(r'["\']insufficient["\']', SCRIPT)
    )
    assert insufficient_occurrences

    assert any(
        re.search(r'["\']limited["\']', SCRIPT[max(0, match.start() - 1200) : match.end() + 1200])
        and re.search(
            r'["\']not_found["\']',
            SCRIPT[max(0, match.start() - 1200) : match.end() + 1200],
        )
        for match in insufficient_occurrences
    ), "limited and not_found evidence must both resolve to the insufficient state"


def test_advisor_mascot_motion_is_loading_only_and_reduced_motion_safe() -> None:
    assert MASCOT_STYLES.is_file()
    styles = _css_without_comments(MASCOT_STYLES.read_text(encoding="utf-8"))

    infinite_selectors = [
        match.group(1).strip()
        for match in re.finditer(r"([^{}]+)\{([^{}]*\binfinite\b[^{}]*)\}", styles)
    ]
    assert infinite_selectors, "the loading pose should contain the only looping motion"
    assert all("loading" in selector.casefold() for selector in infinite_selectors)

    assert re.search(
        r"@media\s*\(\s*prefers-reduced-motion\s*:\s*reduce\s*\)",
        styles,
    )
    assert re.search(r"animation(?:-name)?\s*:\s*none\b", styles)

    size_property = r"(?:--[\w-]*(?:size|width|height)|(?:min-|max-)?(?:width|height)|inline-size|block-size)"
    assert re.search(rf"{size_property}\s*:\s*152px\b", styles)
    assert re.search(rf"{size_property}\s*:\s*128px\b", styles)
    assert re.search(
        r"@media\s*\([^)]*max-width[^)]*\)[\s\S]{0,3000}128px\b",
        styles,
    )


def test_advisor_lattice_loader_is_wired_with_orbit_configuration() -> None:
    react_dir = ROOT / "frontend" / "react-aria"
    loader_jsx = (react_dir / "LatticeLoader.jsx").read_text(encoding="utf-8")
    loader_css = (react_dir / "LatticeLoader.css").read_text(encoding="utf-8")
    picker_jsx = (react_dir / "school-picker.jsx").read_text(encoding="utf-8")
    bundle_js = (STATIC_DIR / "react-aria-school-picker.js").read_text(encoding="utf-8")
    bundle_css = (STATIC_DIR / "react-aria-school-picker.css").read_text(encoding="utf-8")

    assert "export default function LatticeLoader" in loader_jsx
    assert ".lattice-loader" in loader_css
    assert "import LatticeLoader from './LatticeLoader';" in picker_jsx
    for expected in (
        "status={isDone ? 'done' : 'working'}",
        'label="Thinking"',
        'doneLabel="Done in"',
        'errorLabel="Failed after"',
        'pattern="orbit"',
        "grid={3}",
        'shape="round"',
        'doneColor="#22c55e"',
        'errorColor="#ef4444"',
        "cellSize={6}",
        "gap={2}",
        "fontSize={14}",
        "step={90}",
        "idleOpacity={0.15}",
        "glow={false}",
        'glowColor=""',
        "showTimer",
    ):
        assert expected in picker_jsx

    assert 'id="advisor-lattice-loader"' in HTML
    assert "window.UniWayLatticeLoader?.setState(safeState);" in SCRIPT
    assert "UniWayLatticeLoader" in bundle_js
    assert ".lattice-loader" in bundle_css

