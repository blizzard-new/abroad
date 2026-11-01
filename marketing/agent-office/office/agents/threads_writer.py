"""Threads 小編：用真人口吻寫 Threads，連結放第一則留言。"""

from __future__ import annotations

from datetime import date
from secrets import token_hex

from ..brand import Briefing
from ..models import CarouselDraft, PlanItem, ThreadsAlbumDraft, ThreadsDraft
from ..rules import check_threads, check_threads_album
from .base import Agent, Persona


class ThreadsWriter(Agent):
    persona = Persona(
        id="threads",
        name="阿脆",
        title="Threads 小編",
        duty="拿掉官腔、用真人口吻寫 Threads，每篇附一張 4:5 圖卡，也寫帶多張圖的輪播貼文；主文不放連結，連結留在第一則留言",
        hair="messy",
        hair_color="#5a3a22",
        shirt="#1f2937",
        accessory="hoodie",
        decor="tea",
    )

    def produce(self, run_id: int, item: PlanItem, briefing: Briefing, slot) -> int:
        if item.format == "carousel":
            return self.produce_album(run_id, item, briefing, slot)
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

    def produce_album(self, run_id: int, item: PlanItem, briefing: Briefing, slot) -> int:
        """A Threads post with several pictures that swipe, like an Instagram carousel: the words are hers, the pages are Mori's."""
        office = self.office
        self.status("thinking", f"想一組多張圖的貼文：{item.topic[:12]}")
        draft = office.writer.threads_album(item, briefing)
        self._show(draft, "寫好了，交給審稿")
        self.handoff("reviewer", "Threads 多圖貼文")
        draft, review, passed = office.staff["reviewer"].review(
            "Threads 多圖貼文", draft, item, briefing, lambda d: check_threads_album(d, briefing.facts, item.source_url), author=self
        )
        media, plan, notes = album_media(self, draft, item.topic, briefing.day, f"Threads 多圖貼文《{item.topic}》，由{self.persona.name}寫好文案、審稿通過。")
        payload = {**draft.model_dump(), "source_url": item.source_url, "angle": item.angle}
        if plan:
            payload["visual_plan"] = plan.model_dump()
        draft_id = office.queue(
            run_id, item, channel="threads", format="carousel", title=draft.text.strip().splitlines()[0][:40], payload=payload, media=media,
            review={**review, "notes": [*review.get("notes", []), *notes]}, passed=passed, slot=slot, sender=self,
        )
        self.status("done", "這篇多圖貼文排進審核匣了", screen=self._screen(draft))
        return draft_id

    def revise_view(self, draft: ThreadsDraft) -> None:
        self._show(draft, "改好了，再看一次")

    def _show(self, draft: ThreadsDraft, message: str) -> None:
        self.status("working", message, screen=self._screen(draft))

    def _screen(self, draft: ThreadsDraft) -> dict:
        return {"type": "compose", "text": draft.text, "reply": draft.first_reply, "tag": draft.topic_tag}


def card_media(agent: Agent, draft: ThreadsDraft, day: date, note: str = "") -> dict:
    """The 4:5 picture posted with a Threads post. Every picture is Mori's work: whoever wrote the post hands her the request."""
    return agent.office.staff["designer"].threads_card(agent, draft, day, note)


def album_media(agent: Agent, album: ThreadsAlbumDraft, topic: str, day: date, request: str, *, art=None, new_art: bool = True) -> tuple[dict, object, list[str]]:
    """The pictures of a Threads post: Mori plans and draws the pages, exactly as she does for an Instagram carousel.
    Returns (media for the draft, her plan, notes for the boss); with picture output off there are no pictures."""
    office = agent.office
    if not office.settings.render_media:
        return {}, None, []
    pages = CarouselDraft(slides=album.slides, caption=album.text, hashtags=[], art_prompt="")
    folder = office.day_media_dir(day) / f"threads-album-{token_hex(3)}"
    files, plan, art, notes = office.staff["designer"].render_carousel(agent, pages, topic, folder, request, art=art, new_art=new_art)
    media = {"images": [office.media_ref(p) for p in files]}
    if art:
        media["art"] = office.media_ref(art)
    return media, plan, notes
