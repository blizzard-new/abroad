from datetime import date
from types import SimpleNamespace

import pytest

from office.brand import BrandFacts, Briefing
from office.config import Settings
from office.llm import ClaudeWriter, WriterError
from office.models import PlanItem, ThreadsDraft

FACTS = BrandFacts(university_count=33, partner_count=5730, universities=(), site_url="https://app.uniway-tw.com", source="test")


class FakeMessages:
    def __init__(self, response):
        self.response = response
        self.kwargs = None

    def parse(self, **kwargs):
        self.kwargs = kwargs
        return self.response


def writer_with(response):
    messages = FakeMessages(response)
    client = SimpleNamespace(beta=SimpleNamespace(messages=messages))
    return ClaudeWriter(Settings.from_env(env={"OFFICE_HOME": "/tmp/office-test"}), client=client), messages


ITEM = PlanItem(channel="threads", format="text", pillar="value", angle="pain", topic="讀書計畫", brief="study-plan")


def test_requests_structured_output_with_fallback_and_cached_voice():
    draft = ThreadsDraft(text="t", topic_tag="交換學生", first_reply="app.uniway-tw.com")
    writer, messages = writer_with(SimpleNamespace(stop_reason="end_turn", parsed_output=draft))
    assert writer.threads(ITEM, Briefing(day=date(2026, 10, 23), facts=FACTS)) is draft
    sent = messages.kwargs
    assert sent["model"] == "claude-opus-5-5"
    assert sent["output_format"] is ThreadsDraft
    assert sent["fallbacks"] == "default" and sent["betas"] == ["server-side-fallback-2026-07-01"]
    assert sent["system"][0]["cache_control"] == {"type": "ephemeral"}
    assert "33 所大學" in sent["messages"][0]["content"]


def test_refusal_becomes_a_writer_error():
    writer, _ = writer_with(SimpleNamespace(stop_reason="refusal", parsed_output=None))
    with pytest.raises(WriterError):
        writer.threads(ITEM, Briefing(day=date(2026, 10, 23), facts=FACTS))
