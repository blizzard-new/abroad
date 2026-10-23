"""IG 設計師：把題目做成 4:5 輪播圖文（封面插圖可以交給 Codex 畫），再做一張提醒大家去看新貼文的限時動態。"""

from __future__ import annotations

from datetime import timedelta
from pathlib import Path
from secrets import token_hex

from ..brains import BrainError
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
        folder = office.day_media_dir(briefing.day) / f"carousel-{run_id}-{token_hex(3)}"
        media: dict = {}
        art = self._cover_art(draft, item, folder) if office.settings.render_media else None
        if art:
            media["art"] = office.media_ref(art)
        if office.settings.render_media:
            self.status("rendering", "輸出輪播圖…", screen={"type": "images", "images": [], "label": "0 / %d" % len(draft.slides)})
            done: list[str] = []

            def progress(index: int, total: int, path) -> None:
                done.append(office.media_ref(path))
                self.status("rendering", f"第 {index}/{total} 張", screen={"type": "images", "images": list(done), "label": f"{index} / {total}"})

            files = office.renderer.carousel(draft, folder, progress=progress, art=art)
            media["images"] = [office.media_ref(p) for p in files]
        payload = {**draft.model_dump(), "caption_full": instagram_caption(draft.caption, draft.hashtags)}
        draft_id = office.queue(
            run_id, item, channel="instagram", format="carousel", title=draft.slides[0].title if draft.slides else item.topic,
            payload=payload, media=media, review=review, passed=passed, slot=slot, sender=self,
        )
        if office.settings.render_media and draft.slides:
            self.status("rendering", "做一張限動提醒…")
            story = office.renderer.story(draft.slides[0], folder / "story.jpg", art=art)
            office.queue(
                run_id, item, channel="instagram", format="story", title=f"限動：{draft.slides[0].title}",
                payload={"cover": draft.slides[0].model_dump()}, media={"image": office.media_ref(story)},
                review=review, passed=passed, slot=slot + timedelta(minutes=15), sender=self, parent_id=draft_id,
            )
        self.status("done", "輪播圖完成", screen={"type": "images", "images": media.get("images", []), "label": "完成"})
        return draft_id, draft

    def _cover_art(self, draft: CarouselDraft, item: PlanItem, folder: Path) -> Path | None:
        """Ask the image desk (Codex) for a cover illustration; the slides still work without one."""
        images = self.office.images
        if images is None:
            return None
        self.office.bus.emit(self.id, "brain", "封面插圖：Codex", brain=images.key, label=images.label, role="designer", fallback=False)
        self.status("rendering", f"請 {images.label} 畫封面插圖…", screen={"type": "lines", "title": "插圖描述", "lines": [draft.art_prompt or item.topic]})
        try:
            art = images.image(draft.art_prompt or item.topic, folder / "art.png")
        except BrainError as error:
            self.status("working", f"插圖沒畫成，用原本版型（{str(error)[:20]}）")
            return None
        self.status("rendering", "插圖完成", screen={"type": "images", "images": [self.office.media_ref(art)], "label": "封面插圖"})
        return art

    def revise_view(self, draft: CarouselDraft) -> None:
        self.status(
            "working", "排版文案…",
            screen={"type": "lines", "title": "輪播分鏡", "lines": [f"{i + 1}. {s.title}" for i, s in enumerate(draft.slides)]},
        )
