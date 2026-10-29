"""視覺設計師 Mori：全公司唯一做圖的人。

寫文案的同事（阿脆、新同事、Mori 自己的輪播）寫好、審稿通過之後，把「要做哪一張圖」交給她。
她先讀設計準則（brand.VISUAL_BRIEF），再讀這份需求和文案，排出整組規格與逐頁版面（邊距、字級、行距、重點色、
強調手法、每頁用重點／步驟／比較／大數字哪種版面），程式照她的設計出圖；封面插圖可以再交給 Codex 畫。
她只決定怎麼排，不改文案的字（見 visual.py）。
"""

from __future__ import annotations

from datetime import date, timedelta
from pathlib import Path
from secrets import token_hex

from .. import visual
from ..brains import BrainError
from ..brand import Briefing
from ..llm import WriterError
from ..models import CarouselDraft, PlanItem, Slide, ThreadsDraft, VisualPlan
from ..rules import check_carousel, instagram_caption
from .base import Agent, Persona


class Designer(Agent):
    persona = Persona(
        id="designer",
        name="Mori",
        title="視覺設計師",
        duty="全公司唯一做圖的人：寫文案的同事把「要做哪一張圖」交給她，她先讀設計準則再讀需求，排好版面才出圖；也寫 IG 輪播文案",
        hair="long",
        hair_color="#7a4b8c",
        shirt="#f2c14e",
        accessory="beret",
        decor="palette",
    )

    # ---- the design: read the brief, then the request, and plan the pages ----
    def plan(self, requester: Agent, topic: str, slides: list[Slide], request: str, what: str, art_prompt: str = "") -> tuple[VisualPlan, list[str]]:
        """Returns the plan to render (corrected to what the templates can draw) and notes for the boss about it."""
        office = self.office
        if requester.id != self.id:
            requester.handoff(self.id, "請做圖")
        self.status("thinking", f"讀 {requester.persona.name} 的需求：{topic[:10]}",
                    screen={"type": "lines", "title": "收到做圖需求", "lines": [f"來自：{requester.persona.name}", f"要做：{what}", f"主題：{topic[:24]}"]})
        raw, failure = None, ""
        ask = getattr(office.writer, "visual_plan", None)
        if ask is not None:
            try:
                raw = ask(request, slides)
            except WriterError as error:
                failure = str(error)[:120]
        plan, warnings = visual.normalize(raw, slides, art_prompt)
        notes = [f"設計排版沒有完成（{failure}），這次用預設版面"] if failure else []
        notes += [f"Mori 的設計備註：{warning}" for warning in warnings] + [f"Mori 的設計備註：{issue}" for issue in plan.issues]
        self.status("working", "排版中…", screen={"type": "lines", "title": "逐頁大綱", "lines": [f"{i + 1}. {line}" for i, line in enumerate(plan.outline[:7])]})
        return plan, notes

    # ---- IG carousels ----
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
        plan = None
        if office.settings.render_media:
            done: list[str] = []

            def progress(index: int, total: int, path) -> None:
                done.append(office.media_ref(path))
                self.status("rendering", f"第 {index}/{total} 張", screen={"type": "images", "images": list(done), "label": f"{index} / {total}"})

            files, plan, art, notes = self.render_carousel(
                self, draft, item.topic, folder, f"IG 輪播《{item.topic}》，由我（Mori）寫好文案、審稿通過。", progress=progress,
            )
            media["images"] = [office.media_ref(p) for p in files]
            if art:
                media["art"] = office.media_ref(art)
            review = {**review, "notes": [*review.get("notes", []), *notes]}
        payload = {**draft.model_dump(), "caption_full": instagram_caption(draft.caption, draft.hashtags)}
        if plan:
            payload["visual_plan"] = plan.model_dump()
        draft_id = office.queue(
            run_id, item, channel="instagram", format="carousel", title=draft.slides[0].title if draft.slides else item.topic,
            payload=payload, media=media, review=review, passed=passed, slot=slot, sender=self,
        )
        if office.settings.render_media and draft.slides:
            self.status("rendering", "做一張限動提醒…")
            story = office.renderer.story(draft.slides[0], folder / "story.jpg", art=office.media_file(media["art"]) if media.get("art") else None, plan=plan)
            office.queue(
                run_id, item, channel="instagram", format="story", title=f"限動：{draft.slides[0].title}",
                payload={"cover": draft.slides[0].model_dump()}, media={"image": office.media_ref(story)},
                review=review, passed=passed, slot=slot + timedelta(minutes=15), sender=self, parent_id=draft_id,
            )
        self.status("done", "輪播圖完成", screen={"type": "images", "images": media.get("images", []), "label": "完成"})
        return draft_id, draft

    def render_carousel(self, requester: Agent, draft: CarouselDraft, topic: str, folder: Path, request: str, *,
                        art: Path | None = None, new_art: bool = True, progress=None) -> tuple[list[Path], VisualPlan, Path | None, list[str]]:
        """Plan the pages, draw the cover illustration (when the image desk is on, and unless `new_art` is False and `art` is given), render."""
        office = self.office
        plan, notes = self.plan(requester, topic, draft.slides, request, "IG 輪播", draft.art_prompt)
        if new_art:
            art = self._cover_art(plan.art_prompt or draft.art_prompt, topic, folder)
        self.status("rendering", "輸出輪播圖…", screen={"type": "images", "images": [], "label": "0 / %d" % len(draft.slides)})
        files = office.renderer.carousel(draft, folder, progress=progress, art=art, plan=plan)
        return files, plan, art, notes

    # ---- the picture that goes with a Threads post ----
    def threads_card(self, requester: Agent, draft: ThreadsDraft, day: date, note: str = "") -> dict:
        """The 4:5 picture posted with a Threads post. Without one (images off, or the renderer failed) it goes out as text."""
        office = self.office
        if not (office.settings.render_media and office.settings.threads_images):
            return {}
        lines = [line.strip() for line in draft.text.splitlines() if line.strip()]
        slide = Slide(kind="cover", title=(draft.card_title or (lines[0] if lines else ""))[:40], body=draft.card_body[:60])
        request = (
            f"{requester.persona.name}寫好一則 Threads 貼文，需要一張 4:5 的單張配圖（只有這一頁，沒有輪播）。\n"
            f"貼文全文：\n{draft.text}\n圖上的大標題：{slide.title}\n圖上的補充：{slide.body or '（沒有）'}" + (f"\n另外的要求：{note}" if note else "")
        )
        plan, _ = self.plan(requester, slide.title, [slide], request, "Threads 配圖")
        self.status("rendering", "做 Threads 配圖…")
        try:
            path = office.renderer.card(slide, office.day_media_dir(day) / f"threads-{token_hex(4)}.jpg", plan=plan)
        except Exception as error:  # noqa: BLE001 - a missing browser should cost the picture, not the post
            self.log(f"Threads 配圖沒做成，這篇先發純文字：{error}")
            return {}
        return {"image": office.media_ref(path)}

    # ---- the boss asked for the pictures again ----
    def remake(self, draft: dict, note: str) -> str:
        """New layout and a new cover illustration for a draft; the words stay. Returns what to tell the boss."""
        office = self.office
        if not office.settings.render_media:
            raise ValueError("辦公室現在沒有開圖片輸出（OFFICE_RENDER_MEDIA=0）")
        chief = office.staff["chief"]
        payload, media = dict(draft["payload"]), dict(draft["media"] or {})
        day = date.fromisoformat(draft["day"])
        ask = f"老闆要重做這組圖：{note.strip() or '換一個設計'}。文字不要動，只重新設計版面（和封面插圖）。"
        if draft["format"] == "carousel":
            content = CarouselDraft(**{k: payload[k] for k in ("slides", "caption", "hashtags") if k in payload}, art_prompt=payload.get("art_prompt", ""))
            folder = office.day_media_dir(day) / f"carousel-{draft['id']}-{token_hex(3)}"
            files, plan, art, notes = self.render_carousel(chief, content, draft["title"], folder, ask)
            media["images"] = [office.media_ref(p) for p in files]
            media.pop("art", None)
            if art:
                media["art"] = office.media_ref(art)
            payload["visual_plan"] = plan.model_dump()
            review = {**(draft["review"] or {}), "notes": [*[n for n in (draft["review"] or {}).get("notes", []) if not n.startswith(("Mori 的設計備註", "設計排版"))], *notes]}
            office.store.update_draft(draft["id"], payload=payload, media=media, review=review, status="pending_approval")
            office.draft_changed(draft["id"])
            for story in (d for d in office.store.drafts(limit=200) if d["parent_id"] == draft["id"] and d["format"] == "story"):
                image = office.renderer.story(content.slides[0], folder / "story.jpg", art=art, plan=plan)
                office.store.update_draft(story["id"], media={"image": office.media_ref(image)}, status="pending_approval")
                office.draft_changed(story["id"])
            self.status("done", f"#{draft['id']} 的圖重做好了", screen={"type": "images", "images": media["images"], "label": "完成"})
            return f"#{draft['id']} 的 {len(files)} 張圖重新設計好了（版面{'和封面插圖' if art else ''}換過），放回審核匣"
        if draft["format"] == "text" and draft["channel"] == "threads":
            content = ThreadsDraft(**{k: payload[k] for k in ("text", "topic_tag", "first_reply", "card_title", "card_body") if k in payload})
            made = self.threads_card(chief, content, day, ask)
            if not made:
                raise ValueError("配圖沒有做成，請看工作紀錄")
            office.store.update_draft(draft["id"], media={**media, **made}, status="pending_approval")
            office.draft_changed(draft["id"])
            self.status("done", f"#{draft['id']} 的配圖重做好了")
            return f"#{draft['id']} 的配圖重新設計好了，放回審核匣"
        raise ValueError("只有輪播和 Threads 貼文有圖可以重做；影片請跟阿剪說")

    def _cover_art(self, prompt: str, topic: str, folder: Path) -> Path | None:
        """Ask the image generator (Codex) for a cover illustration; the pages still work without one."""
        images = self.office.images
        if images is None:
            return None
        self.office.bus.emit(self.id, "brain", "封面插圖：Codex", brain=images.key, label=images.label, role="designer", fallback=False)
        self.status("rendering", f"請 {images.label} 畫封面插圖…", screen={"type": "lines", "title": "插圖描述", "lines": [prompt or topic]})
        try:
            art = images.image(prompt or topic, folder / "art.png")
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
