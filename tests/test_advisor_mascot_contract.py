from __future__ import annotations

import re
import struct
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
STATIC_DIR = ROOT / "src" / "exchange_info" / "static"
ASSET_DIR = STATIC_DIR / "assets" / "advisor-mascot"
HTML = (STATIC_DIR / "index.html").read_text(encoding="utf-8")
SCRIPT = (STATIC_DIR / "app.js").read_text(encoding="utf-8")
MASCOT_STYLES = STATIC_DIR / "advisor-mascot.css"

POSE_ASSETS = {
    "idle": ASSET_DIR / "idle.png",
    "loading": ASSET_DIR / "researching.png",
    "success": ASSET_DIR / "complete.png",
    "insufficient": ASSET_DIR / "insufficient.png",
}


def _png_ihdr(path: Path) -> bytes:
    payload = path.read_bytes()
    assert payload.startswith(b"\x89PNG\r\n\x1a\n"), f"{path.name} is not a PNG"

    chunk_length = struct.unpack(">I", payload[8:12])[0]
    assert payload[12:16] == b"IHDR", f"{path.name} does not start with IHDR"
    ihdr = payload[16 : 16 + chunk_length]
    assert len(ihdr) == 13, f"{path.name} has an invalid IHDR"
    return ihdr


def _css_without_comments(source: str) -> str:
    return re.sub(r"/\*.*?\*/", "", source, flags=re.DOTALL)


def test_advisor_mascot_assets_are_rgba_pngs_with_transparency_support() -> None:
    for pose, path in POSE_ASSETS.items():
        assert path.is_file(), f"missing {pose} pose: {path}"
        ihdr = _png_ihdr(path)
        width, height = struct.unpack(">II", ihdr[:8])
        color_type = ihdr[9]

        assert width > 0 and height > 0
        assert color_type == 6, f"{path.name} must be an RGBA PNG (color type 6)"


def test_advisor_markup_keeps_the_assistant_and_result_content_persistent() -> None:
    assert HTML.count('id="advisor-assistant"') == 1
    assert HTML.count('id="advisor-result-content"') == 1
    assert re.search(
        r'<link\b[^>]*href=["\'][^"\']*advisor-mascot\.css(?:\?[^"\']*)?["\']',
        HTML,
        flags=re.IGNORECASE,
    )

    image_tags = re.findall(r"<img\b[^>]*>", HTML, flags=re.IGNORECASE)
    expected_sources = {
        f"/static/assets/advisor-mascot/{path.name}" for path in POSE_ASSETS.values()
    }
    rendered_sources = {
        match.group(1).split("?", 1)[0]
        for tag in image_tags
        if (match := re.search(r'src=["\']([^"\']+)["\']', tag, flags=re.IGNORECASE))
    }
    assert expected_sources <= rendered_sources

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
