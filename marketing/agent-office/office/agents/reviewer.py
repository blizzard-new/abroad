"""審稿查核：對平台數字、官方公告與各平台規則，不合格就退回作者修改。"""

from __future__ import annotations

from typing import Callable, TypeVar

from pydantic import BaseModel

from ..brand import Briefing
from ..llm import WriterError
from ..models import PlanItem
from .base import Agent, Persona

Draft = TypeVar("Draft", bound=BaseModel)
MAX_REVISIONS = 1


class Reviewer(Agent):
    persona = Persona(
        id="reviewer",
        name="Kiki",
        title="審稿查核",
        duty="核對平台數字、官方公告、字數與連結規則，也擋 AI 口頭禪；不合格就退回重寫",
        hair="bun",
        hair_color="#1c1c1c",
        shirt="#3f7f6e",
        accessory="glasses",
        decor="magnifier",
    )

    def review(
        self,
        kind: str,
        draft: Draft,
        item: PlanItem,
        briefing: Briefing,
        check: Callable[[Draft], list[str]],
        author: Agent,
    ) -> tuple[Draft, dict, bool]:
        writer = self.office.writer
        rounds = 0
        while True:
            self.status("reviewing", f"檢查{kind}…", screen=_checklist([("字數與格式", None), ("事實與數字", None), ("平台規則", None), ("像真人寫的", None)]))
            issues = check(draft)
            try:
                verdict = writer.review(kind, draft, item, issues, briefing)
                notes = list(verdict.notes)
                issues = list(dict.fromkeys(issues + list(verdict.issues)))
            except WriterError as error:
                notes = [f"AI 審稿沒有完成（{error}），只做了規則檢查"]
            screen = _checklist([(issue, False) for issue in issues] or [("字數與格式", True), ("事實與數字", True), ("平台規則", True), ("像真人寫的", True)])
            if not issues:
                self.status("done", f"{kind}通過 ✓", screen=screen)
                return draft, {"issues": [], "notes": notes, "revisions": rounds}, True
            if rounds >= MAX_REVISIONS:
                self.status("waiting", f"{kind}還有 {len(issues)} 個問題，請老闆看", screen=screen)
                return draft, {"issues": issues, "notes": notes, "revisions": rounds}, False
            rounds += 1
            self.status("reviewing", f"退回修改：{issues[0][:18]}", screen=screen)
            self.handoff(author.id, "退回修改")
            author.status("working", "收到審稿意見，修改中…")
            try:
                draft = writer.revise(draft, issues, briefing)
            except WriterError as error:
                author.status("error", f"改不動：{error}")
                return draft, {"issues": issues, "notes": notes, "revisions": rounds}, False
            if hasattr(author, "revise_view"):
                author.revise_view(draft)
            author.handoff(self.id, "修改版")


def _checklist(rows: list[tuple[str, bool | None]]) -> dict:
    return {"type": "checklist", "items": [{"label": label, "ok": ok} for label, ok in rows]}
