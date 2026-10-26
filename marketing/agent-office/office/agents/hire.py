"""新同事：總管 Leo 依老闆的要求開的一張新桌子。

每位新同事有自己的名字、職稱、負責的事，以及用哪個工具、模型和思考強度（存在辦公室資料庫，Leo 可以再調整）。
他們能做兩種工作：查資料或分析後回報給老闆，或寫一則 Threads 草稿交給 Kiki 審稿、再放進審核匣。
跟其他人一樣不能自己發文。
"""

from __future__ import annotations

from datetime import datetime

from ..brand import load_news, load_schools
from ..llm import WriterError
from ..models import PlanItem, Report, SchoolCheck, ThreadsDraft
from ..rules import check_threads
from .base import Agent, Persona

SCHOOLS_PER_CALL = 5

# How new colleagues look: picked in turn so two hires never come out identical.
HAIR = ("short", "bob", "curly", "ponytail", "bun", "long", "messy", "cap")
HAIR_COLOR = ("#2b1d14", "#6b3e26", "#14110f", "#a0522d", "#3b2a20", "#d9a066", "#4a2c5e", "#1f3a5f")
SHIRT = ("#00a884", "#ff7a59", "#7b61ff", "#f4b400", "#e84393", "#00a3e0", "#8e44ad", "#16a085")
ACCESSORY = ("none", "glasses", "headphones", "none", "beret", "none", "hoodie", "glasses")
DECOR = ("notes", "tea", "palette", "magnifier", "chart", "heart", "rocket", "clapper")


def look(index: int) -> dict[str, str]:
    pick = lambda options, step: options[(index * step) % len(options)]  # noqa: E731 - a tiny local helper
    return {"hair": pick(HAIR, 3), "hair_color": pick(HAIR_COLOR, 5), "shirt": pick(SHIRT, 1),
            "accessory": pick(ACCESSORY, 3), "decor": pick(DECOR, 5)}


class Hire(Agent):
    def __init__(self, office, record: dict):
        super().__init__(office)
        self.record = record
        self.persona = Persona(
            id=record["id"], name=record["name"], title=record["title"], duty=record["duty"],
            **{key: record[key] for key in ("hair", "hair_color", "shirt", "accessory", "decor")},
        )

    @property
    def who(self) -> str:
        return f"{self.persona.title}「{self.persona.name}」，負責：{self.persona.duty}"

    def report(self, request: str) -> str:
        """Research or analysis, answered in the chat."""
        self.status("thinking", f"接到任務：{request[:16]}", screen={"type": "lines", "title": "任務", "lines": [request[:60]]})
        try:
            result: Report = self.office.writer.assignment(self.id, self.who, request, self.office.briefing_for_replies(with_news=True))
        except WriterError as error:
            self.status("error", f"做不出來：{str(error)[:20]}")
            return f"{self.persona.name}沒辦法完成「{request[:20]}」：{str(error)[:120]}"
        lines = [result.summary] + [f"・{point}" for point in result.points]
        if result.sources:
            lines += ["", "來源："] + [f"- {url}" for url in result.sources[:8]]
        self.status("done", "回報給老闆了", screen={"type": "lines", "title": "回報", "lines": result.points[:6] or [result.summary[:60]]})
        return f"{self.persona.name}回報「{request[:20]}」：\n" + "\n".join(lines)

    def write_threads(self, request: str, slot: datetime) -> int:
        """One Threads draft, through Kiki's review and into the boss's inbox like any other."""
        office = self.office
        item = PlanItem(channel="threads", format="text", pillar="value", angle="list", topic=request[:60], brief=request)
        briefing = office.briefing_for_replies(with_news=True)
        self.status("thinking", f"想開頭第一句：{request[:14]}")
        draft = office.writer.threads(item, briefing, role=self.id, who=self.who)
        self.revise_view(draft)
        self.handoff("reviewer", "Threads 草稿")
        draft, review, passed = office.staff["reviewer"].review(
            "Threads 貼文", draft, item, briefing, lambda d: check_threads(d, briefing.facts, item.source_url), author=self
        )
        run_id = (office.store.latest_run() or {}).get("id")
        draft_id = office.queue(
            run_id, item, channel="threads", format="text", title=draft.text.strip().splitlines()[0][:40],
            payload={**draft.model_dump(), "source_url": "", "angle": item.angle, "author": self.persona.name},
            review=review, passed=passed, slot=slot, sender=self,
        )
        self.status("done", "這篇排進審核匣了", screen={"type": "compose", "text": draft.text, "reply": draft.first_reply})
        return draft_id

    def check_schools(self) -> str:
        """The daily round of the schools assigned to this colleague, a few at a time."""
        office = self.office
        mine = [school for school in load_schools(office.settings) if school.id in set(self.record.get("schools") or [])]
        if not mine:
            return f"{self.persona.name}還沒有分到要巡查的學校"
        news = {item.school: item for item in load_news(office.settings, limit=100)}
        briefing = office.briefing_for_replies(with_news=True)
        checks: list[SchoolCheck] = []
        failures: list[str] = []
        for start in range(0, len(mine), SCHOOLS_PER_CALL):
            batch = mine[start:start + SCHOOLS_PER_CALL]
            self.status("working", f"巡查 {batch[0].name} 等 {len(batch)} 所（{start + len(batch)}/{len(mine)}）",
                        screen=_school_screen(checks, mine))
            listing = "\n".join(
                f"- {school.name}\n  官網：{school.official_url}\n  平台資料：{school.note}（支援程度 {school.level}，合作校約 {school.partners} 所）"
                + (f"\n  平台最近核實的公告（{news[school.name].checked_date}）：{news[school.name].summary}" if school.name in news else "")
                for school in batch
            )
            try:
                checks += office.writer.school_check(self.id, self.who, listing, briefing).checks
            except WriterError as error:
                failures.append(f"{batch[0].name} 等 {len(batch)} 所沒查完：{str(error)[:120]}")
        flagged = [c for c in checks if c.status in {"new_notice", "mismatch"}]
        unreachable = [c for c in checks if c.status == "unreachable"]
        calm = [c.school for c in checks if c.status == "no_change"]
        self.status("waiting" if flagged else "done", f"巡查完 {len(checks)} 所，{len(flagged)} 所要注意", screen=_school_screen(checks, mine))
        lines = [f"{self.persona.name}今天巡查了 {len(checks)}／{len(mine)} 所學校："]
        label = {"new_notice": "🆕 新公告", "mismatch": "⚠️ 和平台不一致"}
        lines += [f"{label[c.status]}｜{c.school}：{c.detail}\n  {c.source_url}" for c in flagged]
        if unreachable:
            lines.append("❓ 打不開或找不到交換頁：" + "、".join(c.school for c in unreachable))
        if calm:
            lines.append("✅ 沒有變化：" + "、".join(calm))
        lines += [f"❌ {line}" for line in failures]
        return "\n".join(lines)

    def revise_view(self, draft: ThreadsDraft) -> None:
        self.status("working", "寫草稿…", screen={"type": "compose", "text": draft.text, "reply": draft.first_reply})


def _school_screen(checks: list[SchoolCheck], schools) -> dict:
    done = {c.school: c.status for c in checks}
    return {"type": "checklist", "items": [
        {"label": school.name, "ok": None if school.name not in done else done[school.name] == "no_change"} for school in schools[:8]
    ]}
