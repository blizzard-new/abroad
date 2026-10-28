"""Renders real media. Needs Chromium for Playwright (CHROMIUM_PATH if the bundled one is missing)."""

import os
import re
import subprocess
from datetime import date

import pytest

from office.brand import BrandFacts, Briefing
from office.llm import OfflineWriter
from office.models import PlanItem
from office.offline_bank import TOPICS
from office.render.renderer import Renderer, ffmpeg_exe


def chromium_available() -> bool:
    if os.environ.get("CHROMIUM_PATH"):
        return os.path.exists(os.environ["CHROMIUM_PATH"])
    try:
        from playwright.sync_api import sync_playwright

        with sync_playwright() as p:
            return os.path.exists(p.chromium.executable_path)
    except Exception:
        return False


pytestmark = pytest.mark.skipif(not chromium_available(), reason="needs Chromium")
FACTS = BrandFacts(university_count=33, partner_count=5730, universities=(), site_url="https://app.uniway-tw.com", source="test")


def test_carousel_story_and_short_video(settings, tmp_path):
    briefing = Briefing(day=date(2026, 10, 23), facts=FACTS)
    item = PlanItem(channel="instagram", format="reel", pillar="reach", angle="pain", topic=TOPICS[2].title, brief=TOPICS[2].key)
    writer, renderer = OfflineWriter(), Renderer(settings)

    slides = renderer.carousel(writer.carousel(item, briefing), tmp_path / "carousel")
    assert len(slides) == 6 and all(p.read_bytes()[:2] == b"\xff\xd8" for p in slides)  # JPEG, which Instagram requires

    story = renderer.story(writer.carousel(item, briefing).slides[0], tmp_path / "story.jpg")
    assert story.stat().st_size > 10_000

    card = renderer.card(writer.carousel(item, briefing).slides[0], tmp_path / "threads.jpg")  # the picture for a Threads post
    assert card.read_bytes()[:2] == b"\xff\xd8" and card.stat().st_size > 10_000

    result = renderer.video(writer.video(item, briefing, "short"), tmp_path / "reel.mp4", fps=2)
    # ffmpeg with only an input prints the streams it found (and exits 1 because there is no output).
    streams = subprocess.run([ffmpeg_exe(), "-hide_banner", "-i", str(result["path"])], capture_output=True, text=True).stderr
    assert re.search(r"Video: h264 .*1080x1920", streams) and "Audio: aac" in streams
    assert result["poster"].is_file()


def test_the_mascot_always_has_its_eyes(settings, tmp_path):
    """suitcase.webp is the body only (the website draws the eyes), so every use of it must carry the face."""
    renderer = Renderer(settings)
    briefing = Briefing(day=date(2026, 10, 23), facts=FACTS)
    item = PlanItem(channel="instagram", format="carousel", pillar="value", angle="list", topic=TOPICS[2].title, brief=TOPICS[2].key)
    slides = OfflineWriter().carousel(item, briefing).slides
    with renderer._page(1080, 1920) as page:
        page.goto("https://render.office/template/carousel.html", wait_until="load")
        for story in (False, True):
            for index, slide in enumerate(slides):  # the cover, the points (the mascot peeks in on every other one) and the last slide
                page.evaluate("(args) => window.renderSlide(args)",
                              {"slide": slide.model_dump(), "index": index, "total": len(slides), "site": "app.uniway-tw.com", "story": story and index == 0, "art": None})
                bodies = page.locator('img[src$="suitcase.webp"]')
                for i in range(bodies.count()):
                    face = bodies.nth(i).locator("xpath=..")
                    assert "mascot-face" in face.get_attribute("class"), f"slide {index + 1}: a mascot without a face"
                    assert face.locator(".eye").count() == 2 and face.locator(".cheek").count() == 2
                    box = face.locator(".eye").first.bounding_box()
                    assert box and box["width"] > 5 and box["height"] > 5  # actually drawn, not collapsed
        page.goto("https://render.office/template/video.html", wait_until="load")
        page.evaluate("([s, o]) => window.setup(s, o)", [OfflineWriter().video(item, briefing, "short").model_dump(), "portrait"])
        page.evaluate("(t) => window.render(t)", 1.4)
        mascot = page.locator("#mascot .mascot-face")
        assert mascot.count() == 1 and mascot.locator(".eye").count() == 2
        open_eye = mascot.locator(".eye").first.bounding_box()
        page.evaluate("(t) => window.render(t)", 2.48)  # in the middle of a blink
        shut_eye = mascot.locator(".eye").first.evaluate("(el) => getComputedStyle(el, '::before').transform")
        assert open_eye["height"] > 5 and shut_eye.startswith("matrix(1, 0, 0, 0.")  # the eye is squashed flat while it blinks
