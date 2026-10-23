"""Renders real media. Needs Chromium for Playwright (CHROMIUM_PATH if the bundled one is missing) and ffmpeg."""

import os
import shutil
import subprocess
from datetime import date

import pytest

from office.brand import BrandFacts, Briefing
from office.llm import OfflineWriter
from office.models import PlanItem
from office.offline_bank import TOPICS
from office.render.renderer import Renderer


def chromium_available() -> bool:
    if os.environ.get("CHROMIUM_PATH"):
        return os.path.exists(os.environ["CHROMIUM_PATH"])
    try:
        from playwright.sync_api import sync_playwright

        with sync_playwright() as p:
            return os.path.exists(p.chromium.executable_path)
    except Exception:
        return False


pytestmark = pytest.mark.skipif(not (shutil.which("ffmpeg") and chromium_available()), reason="needs Chromium and ffmpeg")
FACTS = BrandFacts(university_count=33, partner_count=5730, universities=(), site_url="https://app.uniway-tw.com", source="test")


def test_carousel_story_and_short_video(settings, tmp_path):
    briefing = Briefing(day=date(2026, 10, 23), facts=FACTS)
    item = PlanItem(channel="instagram", format="reel", pillar="reach", angle="pain", topic=TOPICS[2].title, brief=TOPICS[2].key)
    writer, renderer = OfflineWriter(), Renderer(settings)

    slides = renderer.carousel(writer.carousel(item, briefing), tmp_path / "carousel")
    assert len(slides) == 6 and all(p.read_bytes()[:2] == b"\xff\xd8" for p in slides)  # JPEG, which Instagram requires

    story = renderer.story(writer.carousel(item, briefing).slides[0], tmp_path / "story.jpg")
    assert story.stat().st_size > 10_000

    result = renderer.video(writer.video(item, briefing, "short"), tmp_path / "reel.mp4", fps=2)
    probe = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "stream=codec_type,width,height", "-of", "csv=p=0", str(result["path"])],
        capture_output=True, text=True, check=True,
    ).stdout.split()
    assert "video,1080,1920" in probe and any(line.startswith("audio") for line in probe)
    assert result["poster"].is_file()
