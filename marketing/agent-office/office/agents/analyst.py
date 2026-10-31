"""數據分析：每晚抓各平台成效，找出互動最好的 Threads 貼文交給企劃重製成 IG 內容（雙平台閉環）。"""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from statistics import median

from ..llm import WriterError
from ..platforms.base import PlatformError
from .base import Agent, Persona

# Threads ranks posts by conversation, so replies and quotes weigh more than likes.
WEIGHTS = {"likes": 1, "replies": 3, "quotes": 4, "reposts": 3, "shares": 2, "comments": 3, "saved": 4}


def score(metrics: dict) -> float:
    return float(sum(WEIGHTS.get(name, 0) * (value or 0) for name, value in metrics.items()))


# A post is judged against what the same kind of post (same platform, same format) usually gets on this account, over this
# many days. A Reel with 400 interactions may be a flop where a Threads post with 40 is a hit.
BASELINE_DAYS = 30
MIN_PEERS = 3  # fewer than this and "usual" is a guess; the post is shown with its raw score only
WIN = 1.5  # at least this many times the usual score is a hit worth remaking; below FLOP is a miss
FLOP = 0.6


def rank(posts: list[dict], metrics: dict[int, dict]) -> list[dict]:
    """Posts with their score and how many times the usual score of their kind it is, best first.

    "Usual" is the median of the other posts of the same platform and format; a post with fewer than MIN_PEERS others has no
    multiple (None) and sorts after those that do.
    """
    scores = {d["id"]: score(metrics[d["id"]]) for d in posts if d["id"] in metrics}
    rows = []
    for d in posts:
        if d["id"] not in scores:
            continue
        peers = [scores[o["id"]] for o in posts if o["id"] != d["id"] and o["id"] in scores and (o["channel"], o["format"]) == (d["channel"], d["format"])]
        usual = median(peers) if len(peers) >= MIN_PEERS else 0
        rows.append({
            "draft_id": d["id"], "title": d["title"], "channel": d["channel"], "format": d["format"], "score": scores[d["id"]],
            "usual": usual or None, "multiple": round(scores[d["id"]] / usual, 1) if usual else None,
        })
    return sorted(rows, key=lambda r: (r["multiple"] is not None, r["multiple"] or 0, r["score"]), reverse=True)


CHANNEL_WORD = {"threads": "Threads", "instagram": "IG", "youtube": "YouTube"}
FORMAT_WORD = {"text": "貼文", "carousel": "輪播", "reel": "Reels", "video": "影片", "short": "Shorts"}


def verdict(row: dict) -> str:
    """One line about how a post did against its own kind."""
    if row["multiple"] is None:
        return f"互動分數 {row['score']:.0f}，同類貼文還太少，沒辦法比較"
    if row["multiple"] >= WIN:
        return f"互動分數 {row['score']:.0f}，是同類平常的 {row['multiple']} 倍 ↑"
    if row["multiple"] <= FLOP:
        return f"互動分數 {row['score']:.0f}，只有同類平常的 {row['multiple']} 倍 ↓"
    return f"互動分數 {row['score']:.0f}，和同類平常差不多（{row['multiple']} 倍）"


def audit_lines(rows: list[dict]) -> list[str]:
    return [
        f"{CHANNEL_WORD.get(r['channel'], r['channel'])}{FORMAT_WORD.get(r['format'], r['format'])}｜{r['title'][:30]}｜{verdict(r)}"
        for r in rows
    ]


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
        multiple = {r["draft_id"]: r["multiple"] for r in self.standings()}
        rows = [
            {"channel": d["channel"], "format": d["format"], "title": d["title"], "metrics": metrics[d["id"]], "multiple": multiple.get(d["id"])}
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

    def standings(self) -> list[dict]:
        """Every post of the last BASELINE_DAYS days that has numbers, ranked against its own kind."""
        since = (datetime.now(timezone.utc) - timedelta(days=BASELINE_DAYS)).isoformat(timespec="seconds")
        return rank(self.office.store.published_since(since), self.office.store.latest_metrics())

    def audit(self, days: int = 7) -> list[dict]:
        """The last `days` days' posts, best against their own kind first: the boss's review of what really worked."""
        since = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat(timespec="seconds")
        recent = {d["id"] for d in self.office.store.published_since(since)}
        return [r for r in self.standings() if r["draft_id"] in recent]

    def winners(self, limit: int = 2) -> list[dict]:
        """Threads posts of the last week that beat their kind, for the strategist to remake on Instagram.

        With enough history a post must clearly beat its usual (WIN times); before that, any post with interactions can."""
        picks = [
            r for r in self.audit(7)
            if r["channel"] == "threads" and r["format"] == "text" and r["score"] > 0 and (r["multiple"] is None or r["multiple"] >= WIN)
        ]
        return [{k: r[k] for k in ("draft_id", "title", "score", "multiple")} for r in picks[:limit]]

    def review_text(self, days: int = 7) -> str:
        """The audit in a few lines for the chief to answer "what worked last week?" with: the best three and the weakest two."""
        rows = self.audit(days)
        if not rows:
            return "（最近沒有發出去又有數據的貼文）"
        shown = rows[:3] + [r for r in rows[3:][-2:] if r["multiple"] is not None and r["multiple"] <= FLOP]
        return "\n".join(audit_lines(shown))

    def chart(self) -> dict:
        metrics = self.office.store.latest_metrics()
        bars = []
        for draft in self.office.store.drafts(status="published", limit=40):
            if draft["id"] in metrics:
                bars.append({"label": draft["title"][:10], "channel": draft["channel"], "value": score(metrics[draft["id"]])})
        return {"type": "chart", "bars": bars[:6]}
