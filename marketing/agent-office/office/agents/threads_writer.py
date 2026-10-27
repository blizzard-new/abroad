"""Threads 小編：用真人口吻寫 Threads，連結放第一則留言。"""

from __future__ import annotations

from datetime import date
from secrets import token_hex

from ..brand import Briefing
from ..models import PlanItem, Slide, ThreadsDraft
from ..rules import check_threads
from .base import Agent, Persona


class ThreadsWriter(Agent):
    persona = Persona(
        id="threads",
        name="阿脆",
        title="Threads 小編",
        duty="拿掉官腔、用真人口吻寫 Threads，每篇附一張 4:5 圖卡；主文不放連結，連結留在第一則留言",
        hair="messy",
        hair_color="#5a3a22",
        shirt="#1f2937",
        accessory="hoodie",
        decor="tea",
    )

    def produce(self, run_id: int, item: PlanItem, briefing: Briefing, slot) -> int:
        self.status("thinking", f"想開頭第一句：{item.topic[:14]}")
        draft = self.office.writer.threads(item, briefing)
        self._show(draft, "寫好了，交給審稿")
        self.handoff("reviewer", "Threads 草稿")
        draft, review, passed = self.office.staff["reviewer"].review(
            "Threads 貼文", draft, item, briefing, lambda d: check_threads(d, briefing.facts, item.source_url), author=self
        )
        title = draft.text.strip().splitlines()[0][:40]
        payload = {**draft.model_dump(), "source_url": item.source_url, "angle": item.angle}
        media = card_media(self, draft, briefing.day)
        draft_id = self.office.queue(
            run_id, item, channel="threads", format="text", title=title, payload=payload, media=media,
            review=review, passed=passed, slot=slot, sender=self,
        )
        self.status("done", "這篇排進審核匣了", screen=self._screen(draft))
        return draft_id

    def revise_view(self, draft: ThreadsDraft) -> None:
        self._show(draft, "改好了，再看一次")

    def _show(self, draft: ThreadsDraft, message: str) -> None:
        self.status("working", message, screen=self._screen(draft))

    def _screen(self, draft: ThreadsDraft) -> dict:
        return {"type": "compose", "text": draft.text, "reply": draft.first_reply, "tag": draft.topic_tag}


def card_media(agent: Agent, draft: ThreadsDraft, day: date) -> dict:
    """The 4:5 picture posted with a Threads post. Without one (images off, or the renderer failed) it goes out as text."""
    office = agent.office
    if not (office.settings.render_media and office.settings.threads_images):
        return {}
    lines = [line.strip() for line in draft.text.splitlines() if line.strip()]
    slide = Slide(kind="cover", title=(draft.card_title or (lines[0] if lines else ""))[:40], body=draft.card_body[:60])
    agent.status("rendering", "做 Threads 配圖…")
    try:
        path = office.renderer.card(slide, office.day_media_dir(day) / f"threads-{token_hex(4)}.jpg")
    except Exception as error:  # noqa: BLE001 - a missing browser should cost the picture, not the post
        agent.log(f"Threads 配圖沒做成，這篇先發純文字：{error}")
        return {}
    return {"image": office.media_ref(path)}
