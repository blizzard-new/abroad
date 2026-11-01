"""企劃：每天早上讀平台數字、官方公告、上網查到的討論與上週成效，排出今天要發的內容。"""

from __future__ import annotations

import json
from datetime import date, datetime, timedelta, timezone

from ..brand import PILLAR_FORMAT, Briefing, load_facts, load_news, pillar_for
from ..llm import WriterError
from ..models import DayPlan, PlanItem
from .base import Agent, Persona

CHANNEL_LABEL = {"threads": "Threads", "instagram": "IG", "youtube": "YouTube"}
FORMAT_LABEL = {"text": "貼文", "carousel": "輪播", "reel": "Reels", "short": "Shorts", "long": "長影片", "story": "限動"}


class Strategist(Agent):
    persona = Persona(
        id="strategist",
        name="Ivy",
        title="企劃總監",
        duty="讀官方公告、平台數字與上週成效，排出今天的內容與發文時間",
        hair="bob",
        hair_color="#2b1d16",
        shirt="#e2574a",
        accessory="none",
        decor="notes",
    )

    def briefing(self, day: date) -> Briefing:
        self.status("thinking", "翻今天的官方公告…", screen={"type": "lines", "title": "資料來源", "lines": ["讀取支援大學清單", "讀取每日公告查核帳本"]})
        facts = load_facts(self.office.settings)
        news = load_news(self.office.settings)
        since = (datetime.now(timezone.utc) - timedelta(days=7)).isoformat(timespec="seconds")
        recent = [d["title"] for d in self.office.store.drafts(limit=60) if d["created_at"] >= since and d["channel"] != "github"]
        winners = self.office.staff["analyst"].winners()
        research = self._research(Briefing(day=day, facts=facts, news=news, recent_titles=recent, winners=winners))
        insights = json.loads(self.office.store.get("insights") or "[]")
        # What the boss asked the chief to pass on ("note_for_tomorrow"), used once.
        notes = json.loads(self.office.store.get("boss_notes") or "[]")
        if notes:
            insights = [f"老闆交代：{note}" for note in notes] + insights
            self.office.store.set("boss_notes", "[]")
        self.status(
            "thinking",
            f"今天有 {len(news)} 則已核實公告",
            screen={
                "type": "lines",
                "title": "今日簡報",
                "lines": [
                    f"支援 {facts.university_count} 所大學",
                    f"{facts.partner_count:,} 筆合作校資料",
                    *[f"📮 {n.school}" for n in news[:3]],
                    *[f"🔥 {w['title'][:16]}" for w in winners[:2]],
                    *[f"🔎 {f.topic[:16]}" for f in research[:3]],
                ],
            },
        )
        return Briefing(day=day, facts=facts, news=news, recent_titles=recent, winners=winners, research=research, insights=insights)

    def _research(self, briefing: Briefing) -> list:
        """Web research before planning, only when the research desk has a brain that can browse."""
        writer = self.office.writer
        if not writer.uses_model("research", need_web=True):
            return []
        self.status("thinking", "上網查這兩週大家在討論什麼", screen={"type": "lines", "title": "研究中", "lines": ["Dcard／PTT／Threads", "各校國際處公告"]})
        try:
            notes = writer.research(briefing)
        except WriterError as error:
            self.status("error", f"查資料沒有完成：{str(error)[:30]}")
            return []
        findings = [f for f in notes.findings if f.source_url.startswith(("http://", "https://"))]
        self.status("working", f"查到 {len(findings)} 條線索", screen={"type": "lines", "title": "研究筆記", "lines": [f"🔎 {f.topic}" for f in findings[:6]]})
        return findings

    def slots(self, day: date) -> list[PlanItem]:
        settings = self.office.settings
        blank = dict(topic="", brief="")
        # The latest Threads posts of the day are the multi-image ones (the first is often the day's news).
        # A multi-image post needs the pictures drawn and, when it is really going out, a public address Threads can fetch them
        # from; without those the slot stays a plain post (a single picture falls back to text the same way).
        can_draw = settings.render_media and (settings.media_host != "none" or settings.dry_run)
        albums = min(settings.threads_albums, len(settings.threads_slots)) if can_draw else 0
        slots = [
            PlanItem(channel="threads", format="carousel" if index >= len(settings.threads_slots) - albums else "text", pillar="value", angle="pain", **blank)
            for index in range(len(settings.threads_slots))
        ]
        pillar = pillar_for(day)
        slots.append(PlanItem(channel="instagram", format=PILLAR_FORMAT[pillar], pillar=pillar, angle="list", **blank))
        if day.weekday() == settings.long_video_weekday:
            slots.append(PlanItem(channel="youtube", format="long", pillar="value", angle="news", **blank))
        return slots

    def plan(self, briefing: Briefing) -> DayPlan:
        self.status("working", "排今天的內容…", screen={"type": "lines", "title": "排程中", "lines": ["Threads × IG 雙平台", "內容比例 3:3:3:1"]})
        plan = self.office.writer.plan_day(briefing, self.slots(briefing.day))
        lines = [f"{CHANNEL_LABEL[i.channel]} {FORMAT_LABEL.get(i.format, i.format)}｜{i.topic}" for i in plan.items]
        self.office.bus.emit(self.id, "whiteboard", plan.theme, notes=plan.whiteboard, items=[i.model_dump() for i in plan.items])
        self.status("done", f"今天主軸：{plan.theme}", screen={"type": "lines", "title": "今日企劃", "lines": lines})
        return plan
