"""Contract tests for the 3D WebGL interactive globe stage, GLSL shaders, and 3D depth card system."""
from __future__ import annotations

import re
from pathlib import Path

from static_asset_contract import assert_versioned_static_assets

STATIC = Path(__file__).resolve().parents[1] / "src" / "exchange_info" / "static"
HTML = (STATIC / "index.html").read_text(encoding="utf-8")
CSS = (STATIC / "uniway-3d.css").read_text(encoding="utf-8")
JS = (STATIC / "uniway-3d.js").read_text(encoding="utf-8")


def test_uniway_3d_assets_are_versioned_and_csp_safe() -> None:
    versions = assert_versioned_static_assets(HTML, ("uniway-3d.css", "uniway-3d.js"))
    assert versions["uniway-3d.css"] == versions["uniway-3d.js"]
    assert 'id="uw-hero-webgl-canvas"' in HTML
    assert 'id="uw-3d-active-hub-card"' in HTML
    assert 'id="uw-3d-tour-toggle"' in HTML
    assert len(re.findall(r'class="uw-3d-hub-pill"', HTML)) == 6


def test_uniway_3d_engine_includes_custom_glsl_shaders_and_card_tilt() -> None:
    assert "GLOBE_VERT" in JS and "GLOBE_FRAG" in JS
    assert "ARC_VERT" in JS and "ARC_FRAG" in JS
    assert "PARTICLE_VERT" in JS and "PARTICLE_FRAG" in JS
    assert "slerp3(" in JS and "buildFlightRibbonGeometry(" in JS
    assert "init3DCards(" in JS
    assert "prefers-reduced-motion: reduce" in JS


def test_uniway_3d_styles_define_perspective_and_reduced_motion_rules() -> None:
    assert "transform-style: preserve-3d" in CSS
    assert "perspective(" in CSS or "perspective:" in CSS
    assert "@media (prefers-reduced-motion: reduce)" in CSS
