"""影片剪輯：寫 30～45 秒腳本、逐格算圖、配樂，輸出 Reels／Shorts，週日再做一支橫式長影片。"""

from __future__ import annotations

from datetime import datetime

from ..brand import HASHTAGS, Briefing
from ..models import CarouselDraft, PlanItem, VideoScript
from ..rules import check_video, instagram_caption
from .base import Agent, Persona


class VideoEditor(Agent):
    persona = Persona(
        id="video",
        name="阿剪",
        title="影片剪輯",
        duty="寫鉤子在前 3 秒的腳本，逐格算出 Reels／Shorts 與每週長影片，配上自己合成的音樂",
        hair="short",
        hair_color="#14110f",
        shirt="#2f7de1",
        accessory="headphones",
        decor="clapper",
    )

    def reel(self, run_id: int, item: PlanItem, briefing: Briefing, ig_slot: datetime, yt_slot: datetime) -> int:
        """One vertical video, posted as an Instagram Reel and a YouTube Short."""
        self.status("thinking", f"寫腳本：{item.topic[:14]}")
        script = self.office.writer.video(item, briefing, "short")
        script, review, passed = self._review(script, item, briefing, "short")
        media = self._render(script, briefing, run_id, "portrait")
        reel_id = self.office.queue(
            run_id, item, channel="instagram", format="reel", title=script.title,
            payload={**script.model_dump(), "caption_full": instagram_caption(script.caption, script.hashtags)},
            media=media, review=review, passed=passed, slot=ig_slot, sender=self,
        )
        self.office.queue(
            run_id, item, channel="youtube", format="short", title=script.youtube_title,
            payload=_youtube_payload(script), media=media, review=review, passed=passed, slot=yt_slot, sender=self, parent_id=reel_id,
        )
        self.status("done", "Reels／Shorts 輸出完成", screen={"type": "video", "poster": media.get("poster"), "progress": 1, "label": "完成"})
        return reel_id

    def short_from_carousel(self, run_id: int, carousel: CarouselDraft, item: PlanItem, briefing: Briefing, slot: datetime, parent_id: int) -> int:
        self.status("thinking", "把今天的輪播改成 Shorts 腳本…")
        script = self.office.writer.video_from_carousel(carousel, item, briefing)
        script, review, passed = self._review(script, item, briefing, "short")
        media = self._render(script, briefing, run_id, "portrait")
        draft_id = self.office.queue(
            run_id, item, channel="youtube", format="short", title=script.youtube_title,
            payload=_youtube_payload(script), media=media, review=review, passed=passed, slot=slot, sender=self, parent_id=parent_id,
        )
        self.status("done", "Shorts 輸出完成", screen={"type": "video", "poster": media.get("poster"), "progress": 1, "label": "完成"})
        return draft_id

    def long(self, run_id: int, item: PlanItem, briefing: Briefing, slot: datetime) -> int:
        self.status("thinking", "整理本週懶人包腳本…")
        script = self.office.writer.video(item, briefing, "long")
        script, review, passed = self._review(script, item, briefing, "long")
        media = self._render(script, briefing, run_id, "landscape")
        draft_id = self.office.queue(
            run_id, item, channel="youtube", format="long", title=script.youtube_title,
            payload=_youtube_payload(script), media=media, review=review, passed=passed, slot=slot, sender=self,
        )
        self.status("done", "長影片輸出完成", screen={"type": "video", "poster": media.get("poster"), "progress": 1, "label": "完成"})
        return draft_id

    def revise_view(self, script: VideoScript) -> None:
        self.status(
            "working", "調整腳本…",
            screen={"type": "lines", "title": "分鏡", "lines": [f"{s.seconds:.0f}s {s.heading}" for s in script.scenes]},
        )

    def _review(self, script: VideoScript, item: PlanItem, briefing: Briefing, length: str):
        self.revise_view(script)
        self.handoff("reviewer", "影片腳本")
        return self.office.staff["reviewer"].review(
            "影片腳本", script, item, briefing, lambda s: check_video(s, briefing.facts, length, item.source_url), author=self
        )

    def _render(self, script: VideoScript, briefing: Briefing, run_id: int, orientation: str) -> dict:
        office = self.office
        if not office.settings.render_media:
            return {}
        name = "reel" if orientation == "portrait" else "long"
        path = office.day_media_dir(briefing.day) / f"{name}-{run_id}.mp4"
        poster_ref: dict[str, str | None] = {"poster": None}

        def progress(frame: int, total: int, _path) -> None:
            self.status(
                "rendering", f"算圖 {frame}/{total} 格",
                screen={"type": "video", "poster": poster_ref["poster"], "progress": frame / total, "label": f"{frame} / {total} 格"},
            )
            if poster_ref["poster"] is None and path.with_name(path.stem + "-poster.jpg").is_file():
                poster_ref["poster"] = office.media_ref(path.with_name(path.stem + "-poster.jpg"))

        self.status("rendering", "開始算圖…", screen={"type": "video", "poster": None, "progress": 0, "label": "準備中"})
        result = office.renderer.video(script, path, orientation=orientation, progress=progress)
        return {
            "video": office.media_ref(result["path"]),
            "poster": office.media_ref(result["poster"]),
            "duration": round(result["duration"], 1),
            "orientation": orientation,
        }


def _youtube_payload(script: VideoScript) -> dict:
    tags = [tag.lstrip("#") for tag in script.hashtags] or [tag.lstrip("#") for tag in HASHTAGS]
    return {"title": script.youtube_title, "description": script.youtube_description, "tags": tags, "script": script.model_dump()}
