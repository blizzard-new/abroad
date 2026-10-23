"""數據分析：每晚抓各平台成效，找出互動最好的 Threads 貼文交給企劃重製成 IG 內容（雙平台閉環）。"""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone

from ..llm import WriterError
from ..platforms.base import PlatformError
from .base import Agent, Persona

# Threads ranks posts by conversation, so replies and quotes weigh more than likes.
WEIGHTS = {"likes": 1, "replies": 3, "quotes": 4, "reposts": 3, "shares": 2, "comments": 3, "saved": 4}


def score(metrics: dict) -> float:
    return float(sum(WEIGHTS.get(name, 0) * (value or 0) for name, value in metrics.items()))


class Analyst(Agent):
    persona = Persona(
        id="analyst",
        name="Nana",
        title="數據分析",
        duty="每晚抓 Threads／IG／YouTube 成效，挑出爆文給企劃重製成 IG 輪播或 Reels",
        hair="ponytail",
        hair_color="#8a5a2b",
        shirt="#17b5d8",
        accessory="none",
        decor="chart",
    )

    def collect(self) -> int:
        office = self.office
        since = (datetime.now(timezone.utc) - timedelta(days=7)).isoformat(timespec="seconds")
        drafts = [d for d in office.store.published_since(since) if d["remote_id"] and not d["remote_id"].startswith("dry-")]
        if not drafts:
            self.status("idle", "還沒有真實發佈的數據", screen=self.chart())
            return 0
        self.status("working", f"抓 {len(drafts)} 則貼文的成效…")
        clients = office.staff["publisher"].clients()
        collected = 0
        videos = [d for d in drafts if d["channel"] == "youtube"]
        try:
            stats = clients["youtube"].stats([d["remote_id"] for d in videos]) if videos else {}
        except PlatformError as error:
            self.log(f"YouTube 數據抓取失敗：{error}")
            stats = {}
        for draft in drafts:
            try:
                if draft["channel"] == "threads":
                    metrics = clients["threads"].insights(draft["remote_id"])
                elif draft["channel"] == "instagram" and draft["format"] in {"carousel", "reel"}:
                    metrics = clients["instagram"].insights(draft["remote_id"])
                elif draft["channel"] == "youtube":
                    metrics = stats.get(draft["remote_id"], {})
                else:
                    continue
            except PlatformError as error:
                self.log(f"{draft['title'][:16]} 數據抓取失敗：{error}")
                continue
            if metrics:
                office.store.add_metrics(draft["id"], metrics)
                collected += 1
        if collected:
            self._advise(drafts)
        self.status("done", f"更新了 {collected} 則成效", screen=self.chart())
        return collected

    def _advise(self, drafts: list[dict]) -> None:
        """Turn the week's numbers into a few notes the strategist reads tomorrow morning."""
        writer = self.office.writer
        if not writer.uses_model("analyst"):
            return
        metrics = self.office.store.latest_metrics()
        rows = [
            {"channel": d["channel"], "format": d["format"], "title": d["title"], "metrics": metrics[d["id"]]}
            for d in drafts if d["id"] in metrics
        ]
        self.status("thinking", "解讀這週的數據…")
        try:
            notes = writer.insights(rows, self.office.briefing_for_replies()).notes
        except WriterError as error:
            self.log(f"數據解讀沒有完成：{error}")
            return
        self.office.store.set("insights", json.dumps(notes[:4], ensure_ascii=False))
        self.status("working", notes[0][:24] if notes else "這週沒有特別的建議", screen={"type": "lines", "title": "給企劃的建議", "lines": notes[:4]})

    def winners(self, limit: int = 2) -> list[dict]:
        """Best Threads posts of the last week, for the strategist to remake on Instagram."""
        since = (datetime.now(timezone.utc) - timedelta(days=7)).isoformat(timespec="seconds")
        metrics = self.office.store.latest_metrics()
        ranked = [
            {"draft_id": d["id"], "title": d["title"], "score": score(metrics[d["id"]])}
            for d in self.office.store.published_since(since)
            if d["channel"] == "threads" and d["format"] == "text" and d["id"] in metrics
        ]
        ranked = [r for r in ranked if r["score"] > 0]
        return sorted(ranked, key=lambda r: r["score"], reverse=True)[:limit]

    def chart(self) -> dict:
        metrics = self.office.store.latest_metrics()
        bars = []
        for draft in self.office.store.drafts(status="published", limit=40):
            if draft["id"] in metrics:
                bars.append({"label": draft["title"][:10], "channel": draft["channel"], "value": score(metrics[draft["id"]])})
        return {"type": "chart", "bars": bars[:6]}
