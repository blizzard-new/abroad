"""The mascot has eyes: say so wherever an AI describes or draws it."""

from datetime import date

from office.brand import MASCOT, VOICE_GUIDE, BrandFacts, Briefing
from office.llm import OfflineWriter
from office.models import CarouselDraft, PlanItem
from office.offline_bank import TOPICS

FACTS = BrandFacts(university_count=33, partner_count=5730, universities=(), site_url="https://app.uniway-tw.com", source="test")


def test_every_ai_is_told_the_mascot_has_eyes():
    assert "眼睛" in MASCOT and "沒有嘴巴" in MASCOT
    assert MASCOT in VOICE_GUIDE  # the shared guide every desk reads, including the cover illustrator's prompt writer
    assert "眼睛" in CarouselDraft.model_json_schema()["properties"]["art_prompt"]["description"]


def test_the_offline_cover_description_has_the_eyes():
    item = PlanItem(channel="instagram", format="carousel", pillar="value", angle="list", topic=TOPICS[0].title, brief=TOPICS[0].key)
    art = OfflineWriter().carousel(item, Briefing(day=date(2026, 10, 28), facts=FACTS)).art_prompt
    assert "吉祥物" in art and "眼睛" in art
