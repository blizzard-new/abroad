"""IG 設計師：把題目做成 4:5 輪播圖文，再做一張提醒大家去看新貼文的限時動態。"""

from __future__ import annotations

from datetime import timedelta

from ..brand import Briefing
from ..models import CarouselDraft, PlanItem
from ..rules import check_carousel, instagram_caption
from .base import Agent, Persona


class Designer(Agent):
    persona = Persona(
        id="designer",
        name="Mori",
        title="IG 設計師",
        duty="把題目做成值得收藏的 4:5 輪播圖文與限時動態，說明欄 hashtag 最多 5 個",
        hair="long",
        hair_color="#7a4b8c",
        shirt="#f2c14e",
        accessory="beret",
        decor="palette",
    )

    def produce(self, run_id: int, item: PlanItem, briefing: Briefing, slot) -> tuple[int, CarouselDraft]:
        office = self.office
        self.status("thinking", f"構圖中：{item.topic[:14]}")
        draft = office.writer.carousel(item, briefing)
        self.revise_view(draft)
        self.handoff("reviewer", "輪播文案")
        draft, review, passed = office.staff["reviewer"].review(
            "IG 輪播", draft, item, briefing, lambda d: check_carousel(d, briefing.facts, item.source_url), author=self
        )
        folder = office.day_media_dir(briefing.day) / f"carousel-{run_id}"
        media: dict = {}
        if office.settings.render_media:
            self.status("rendering", "輸出輪播圖…", screen={"type": "images", "images": [], "label": "0 / %d" % len(draft.slides)})
            done: list[str] = []

            def progress(index: int, total: int, path) -> None:
                done.append(office.media_ref(path))
                self.status("rendering", f"第 {index}/{total} 張", screen={"type": "images", "images": list(done), "label": f"{index} / {total}"})

            files = office.renderer.carousel(draft, folder, progress=progress)
            media = {"images": [office.media_ref(p) for p in files]}
        payload = {**draft.model_dump(), "caption_full": instagram_caption(draft.caption, draft.hashtags)}
        draft_id = office.queue(
            run_id, item, channel="instagram", format="carousel", title=draft.slides[0].title if draft.slides else item.topic,
            payload=payload, media=media, review=review, passed=passed, slot=slot, sender=self,
        )
        if office.settings.render_media and draft.slides:
            self.status("rendering", "做一張限動提醒…")
            story = office.renderer.story(draft.slides[0], folder / "story.jpg")
            office.queue(
                run_id, item, channel="instagram", format="story", title=f"限動：{draft.slides[0].title}",
                payload={"cover": draft.slides[0].model_dump()}, media={"image": office.media_ref(story)},
                review=review, passed=passed, slot=slot + timedelta(minutes=15), sender=self, parent_id=draft_id,
            )
        self.status("done", "輪播圖完成", screen={"type": "images", "images": media.get("images", []), "label": "完成"})
        return draft_id, draft

    def revise_view(self, draft: CarouselDraft) -> None:
        self.status(
            "working", "排版文案…",
            screen={"type": "lines", "title": "輪播分鏡", "lines": [f"{i + 1}. {s.title}" for i, s in enumerate(draft.slides)]},
        )
