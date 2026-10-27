"""總管：你和大家之間的窗口。你用聊天交代事情，總管轉成固定的幾種工作分派下去，做完再回報。

總管能做的事：開工、重寫某則草稿、加做一則、改發文時間、退回、記給明天的企劃，
查看和調整每位同事用的 AI（工具、模型、思考強度），
以及新增同事、交代工作給新同事、請新同事離開。
不能核准、不能發文、不能改帳號或模擬模式——那些永遠由你在審核匣自己按。
"""

from __future__ import annotations

import json
import re
import threading
from secrets import token_hex
from datetime import date, datetime, time, timedelta, timezone

from .. import accounts, brains
from ..llm import WriterError
from ..models import CarouselDraft, ChiefAction, ChiefReply, PlanItem, ThreadsDraft, VideoScript
from ..rules import check_carousel, check_threads, check_video, instagram_caption
from .base import Agent, Persona
from .threads_writer import card_media

STATUS_WORD = {
    "pending_approval": "待審", "needs_changes": "需修改", "approved": "已核准", "publishing": "發佈中",
    "published": "已發佈", "failed": "失敗", "rejected": "已退回",
}
FORMAT_WORD = {"text": "貼文", "reply": "留言回覆", "carousel": "輪播", "reel": "Reels", "story": "限動", "short": "Shorts", "long": "長影片"}
CHANNEL_WORD = {"threads": "Threads", "instagram": "IG", "youtube": "YouTube"}
EDITABLE = {"pending_approval", "needs_changes", "approved", "failed", "rejected"}
MAX_ACTIONS = 10


class Chief(Agent):
    persona = Persona(
        id="chief",
        name="Leo",
        title="總管",
        duty="你和大家之間的窗口：聽你交代、分派工作、回報進度；不能替你核准或發文",
        hair="short",
        hair_color="#2d2a32",
        shirt="#0f766e",
        accessory="headphones",
        decor="walkie",
    )

    # ---- talking ----
    def say(self, text: str, **data) -> dict:
        return self.office.chat("chief", text, data)

    def handle(self, text: str) -> dict:
        """One message from the boss: understand it, hand out the work, answer."""
        office = self.office
        office.chat("boss", text)
        self.status("thinking", "聽懂老闆要什麼…", screen={"type": "chat", "messages": [{"from": "老闆", "text": text[:60]}]})
        try:
            plan = office.writer.chief(text, self.state_text(), self.history_text(), self.status_text())
        except WriterError as error:
            plan = ChiefReply(reply=f"我現在連不上 AI（{str(error)[:60]}）。\n\n{self.status_text()}", actions=[])
        results = [self.execute(action) for action in plan.actions[:MAX_ACTIONS]]
        answer = plan.reply.strip() + ("\n\n" + "\n".join(f"・{line}" for line in results) if results else "")
        self.status(
            "done" if results else "idle", "交代下去了" if results else "回覆老闆了",
            screen={"type": "chat", "messages": [{"from": "老闆", "text": text[:60]}, {"from": "我們", "text": plan.reply[:60]}]},
        )
        return self.say(answer, actions=[action.model_dump() for action in plan.actions[:MAX_ACTIONS]])

    def report_day(self, run_id: int) -> None:
        drafts = sorted((d for d in self.office.store.drafts(limit=80) if d["run_id"] == run_id), key=lambda d: d["id"])
        waiting = [d for d in drafts if d["status"] in {"pending_approval", "needs_changes"}]
        lines = [f"#{d['id']} {CHANNEL_WORD[d['channel']]} {FORMAT_WORD.get(d['format'], d['format'])}｜{d['title'][:24]}"
                 + ("（需修改）" if d["status"] == "needs_changes" else "") for d in waiting]
        if waiting:
            self.say("今天的草稿都好了，這些等你看：\n" + "\n".join(lines) + "\n\n要改哪一則直接跟我說，例如「#3 開頭再口語一點」。")
        else:
            self.say("今天的內容都排好了，沒有需要你審的。")

    # ---- what the chief knows ----
    def state_text(self) -> str:
        office = self.office
        run = office.store.latest_run()
        plan = (run or {}).get("plan") or {}
        drafts = office.store.drafts(limit=30)
        rows = []
        for d in drafts:
            when = self._local(d["scheduled_at"]).strftime("%m/%d %H:%M") if d["scheduled_at"] else "回覆"
            issues = (d.get("review") or {}).get("issues") or []
            rows.append(
                f"#{d['id']}｜{CHANNEL_WORD[d['channel']]} {FORMAT_WORD.get(d['format'], d['format'])}｜{STATUS_WORD[d['status']]}"
                f"｜{when}｜{d['title'][:40]}" + (f"｜問題：{issues[0][:40]}" if issues else "")
            )
        staff = "\n".join(f"- {a.persona.name}（{a.persona.title}）：{a.persona.duty}" for a in office.staff.values() if a.id != self.id)
        names = {a.id: a.persona.name for a in office.staff.values()}
        hires = [a for a in office.staff.values() if hasattr(a, "record")]
        daily = "\n".join(
            f"- {a.persona.name}（{a.persona.title}）：{a.record.get('daily') or '還沒有每天固定的工作'}"
            + (f"；每天 {'、'.join(office.hire_times(a))} 做" if a.record.get("daily_kind") else "")
            + (f"；負責 {len(a.record['schools'])} 所大學" if a.record.get("schools") else "")
            for a in hires
        )
        minds = "\n".join(
            f"- role={role}（{names.get("strategist" if role == "research" else role, role)}・{label}）：{office.describe_brain(role)}"
            for role, label in office.roles().items()
        )
        notes = json.loads(office.store.get("boss_notes") or "[]")
        settings = office.settings
        def account(key: str, word: str) -> str:
            if not accounts.connected(settings, office.store, key):
                return f"{word} 未連上"
            handle = office.store.get(f"handle:{key}")
            return f"{word} 已連上" + (f"（{handle}）" if handle else "")

        linked = "、".join(account(key, word) for key, word in (("threads", "Threads"), ("instagram", "IG"), ("youtube", "YouTube")))
        mode = (
            f"發文模式：{'模擬發佈（OFFICE_DRY_RUN=1）：核准的貼文只寫進 var/outbox/，不會真的送出' if settings.dry_run else '正式發佈：核准的貼文會真的送出'}；"
            f"{'審稿通過就自動排程（OFFICE_APPROVAL=auto）' if settings.approval == 'auto' else '每則都要老闆核准才會發'}。\n"
            f"社群帳號：{linked}。\n"
            "這些都寫在辦公室電腦的 .env 檔，網頁和審核匣上沒有開關。要改成正式發佈，老闆要在那台電腦打開 .env，"
            "把 OFFICE_DRY_RUN 改成 0，存檔後重新啟動 uv run office serve，再跑 uv run office check 確認第一行是「正式發文」；"
            "帳號用 uv run office auth threads／instagram／youtube 連上。\n"
        )
        return (
            mode +
            f"現在（台北）：{office.local_now():%Y-%m-%d %H:%M}；{'大家正在做今天的內容' if office.busy.locked() else '目前沒有在跑的工作'}\n"
            f"今天主軸：{plan.get('theme') or '還沒排'}\n"
            f"草稿（最新在前）：\n" + ("\n".join(rows) or "（還沒有草稿）") + "\n\n"
            f"記給明天的事：{'；'.join(notes) or '（無）'}\n\n同事：\n{staff}\n\n"
            f"每個工作現在用的 AI（role=後面是 set_brain 要填的值）：\n{minds}\n\n"
            f"新同事每天固定的工作：\n{daily or '（還沒有新同事）'}\n"
            f"平台目前支援 {office.facts().university_count} 所大學，清單在辦公室電腦上的專案裡，watch_schools 會直接讀，不用上 GitHub。"
        )

    def history_text(self) -> str:
        messages = self.office.store.chat(limit=9)[:-1]  # the newest is the message being answered
        return "\n".join(f"{'老闆' if m['sender'] == 'boss' else '總管'}：{m['text'][:200]}" for m in messages)

    def status_text(self) -> str:
        drafts = [d for d in self.office.store.drafts(limit=80) if d["day"] == self.office.today().isoformat()]
        if not drafts:
            return "今天還沒有草稿。說「開工」我就請大家開始。"
        counts: dict[str, int] = {}
        for d in drafts:
            counts[STATUS_WORD[d["status"]]] = counts.get(STATUS_WORD[d["status"]], 0) + 1
        return "今天的進度：" + "、".join(f"{word} {n} 則" for word, n in counts.items())

    # ---- handing out work ----
    def execute(self, action: ChiefAction) -> str:
        try:
            handler = getattr(self, f"_do_{action.type}")
            return handler(action)
        except (KeyError, ValueError) as error:
            return f"沒辦法做：{error}"

    def _draft(self, draft_id: int) -> dict:
        draft = self.office.store.draft(draft_id)
        if not draft:
            raise ValueError(f"找不到 #{draft_id}")
        if draft["status"] not in EDITABLE:
            raise ValueError(f"#{draft_id} 已經{STATUS_WORD[draft['status']]}，不能再改")
        return draft

    def _background(self, label: str, work) -> None:
        """Long work runs on its own thread; the chief reports back in the chat when it is done."""
        def run():
            try:
                message = work()
            except Exception as error:  # noqa: BLE001 - report every failure back in the chat
                message = f"{label}沒有完成：{str(error)[:120]}"
            if message:
                self.say(message)

        threading.Thread(target=run, daemon=True, name=f"chief-{label}").start()

    def _do_set_brain(self, action: ChiefAction) -> str:
        if not action.role:
            raise ValueError("要說是哪一位同事的哪個工作")
        if not (action.brain or action.model or action.effort):
            raise ValueError("要說改成哪個工具、模型或思考強度")
        self.office.tune(action.role, brain=action.brain, model=action.model, effort=action.effort)
        return f"{self.office.roles()[action.role]}改用 {self.office.describe_brain(action.role)}"

    def _do_hire(self, action: ChiefAction) -> str:
        agent = self.office.hire(action.name, action.title, action.instructions, brain=action.brain, model=action.model, effort=action.effort)
        return f"{agent.persona.name}（{agent.persona.title}）加入了，用 {self.office.describe_brain(agent.id)}"

    def _do_watch_schools(self, action: ChiefAction) -> str:
        shares = self.office.split_schools(action.names or ([action.name] if action.name else []))
        lines = [f"{name} 負責 {len(schools)} 所：{'、'.join(schools)}" for name, schools in shares.items()]
        return "大學分好了，從明天起每天開工時巡查：\n" + "\n".join(lines)

    def _do_set_schedule(self, action: ChiefAction) -> str:
        names = action.names or ([action.name] if action.name else [])
        if not names:
            raise ValueError("要設定哪幾位新同事的時間？")
        lines = []
        for name in names:
            times = self.office.set_hire_times(name, action.times)
            lines.append(f"{name} 每天 {'、'.join(times)} 做固定工作")
        return "；".join(lines)

    def _do_dismiss(self, action: ChiefAction) -> str:
        return f"{self.office.dismiss(action.name or action.role)}離開辦公室了"

    def _do_assign(self, action: ChiefAction) -> str:
        office = self.office
        colleague = office.colleague(action.name or action.role)
        if action.task_kind == "schools":
            if not colleague.record.get("schools"):
                raise ValueError(f"{colleague.persona.name}還沒分到學校，先用 watch_schools 分配")
            self.handoff(colleague.id, "巡查學校")
            self._background(f"{colleague.persona.name}的巡查", colleague.check_schools)
            return f"{colleague.persona.name}現在開始巡查 {len(colleague.record['schools'])} 所學校，查完會回報"
        request = action.instructions.strip()
        if not request:
            raise ValueError(f"要請 {colleague.persona.name} 做什麼？")
        self.handoff(colleague.id, "交代工作")
        if action.every_day:
            office.update_hire(colleague.id, daily=request[:300], daily_kind=action.task_kind or "report")
            return f"{colleague.persona.name}從明天起每天開工時都會做：「{request[:24]}」"
        if action.task_kind == "threads":
            slot = self._next_slot("threads")

            def work() -> str:
                draft_id = colleague.write_threads(request, slot)
                return f"{colleague.persona.name}寫好 Threads 了（#{draft_id}），在審核匣等你"

            self._background(f"{colleague.persona.name}的草稿", work)
            return f"已經請 {colleague.persona.name} 寫一則 Threads：「{request[:20]}」，寫好會放進審核匣"
        self._background(f"{colleague.persona.name}的任務", lambda: colleague.report(request))
        return f"已經交給 {colleague.persona.name}：「{request[:20]}」，做完會回報"

    def _do_start_day(self, action: ChiefAction) -> str:
        from ..pipeline import run_day

        if self.office.busy.locked():
            return "大家正在做今天的內容，做完我再跟你說"
        self.handoff("strategist", "開工")
        # The day's own summary arrives in the chat when the run finishes (report_day).
        self._background("開工", lambda: run_day(self.office, force=True) and None)
        return "已經請 Ivy 開工，草稿好了會送到審核匣"

    def _do_redo(self, action: ChiefAction) -> str:
        draft = self._draft(action.draft_id)
        if draft["format"] in {"story", "reply"}:
            raise ValueError("限動跟著輪播封面走、留言回覆請直接在審核匣改字")
        if not action.instructions.strip():
            raise ValueError(f"要怎麼改 #{draft['id']}？請說清楚")
        author = {"threads": "threads", "instagram": "designer" if draft["format"] == "carousel" else "video", "youtube": "video"}[draft["channel"]]
        self.handoff(author, "總管交代", draft_id=draft["id"])
        self._background(f"#{draft['id']} 重寫", lambda: self._rewrite(draft, author, action.instructions.strip()))
        return f"已經請 {self.office.staff[author].persona.name} 重寫 #{draft['id']}，改好會放回審核匣"

    def _rewrite(self, draft: dict, author_id: str, instructions: str) -> str:
        office = self.office
        author = office.staff[author_id]
        reviewer = office.staff["reviewer"]
        briefing = office.briefing_for_replies()
        payload, media = dict(draft["payload"]), dict(draft["media"] or {})
        item = PlanItem(
            channel=draft["channel"],
            format=draft["format"],
            pillar=draft["pillar"] or "value", angle=payload.get("angle", "pain"), topic=draft["title"], brief=instructions,
            source_url=payload.get("source_url", ""),
        )
        author.status("working", f"總管交代：{instructions[:16]}")
        if draft["format"] == "text":
            content = ThreadsDraft(**{k: payload[k] for k in ("text", "topic_tag", "first_reply", "card_title", "card_body") if k in payload})
            check = lambda d: check_threads(d, briefing.facts, item.source_url)  # noqa: E731
            kind = "Threads 貼文"
        elif draft["format"] == "carousel":
            content = CarouselDraft(**{k: payload[k] for k in ("slides", "caption", "hashtags") if k in payload}, art_prompt=payload.get("art_prompt", ""))
            check = lambda d: check_carousel(d, briefing.facts, item.source_url)  # noqa: E731
            kind = "IG 輪播"
        else:
            content = VideoScript(**(payload.get("script") or payload))
            length = "long" if draft["format"] == "long" else "short"
            check = lambda d: check_video(d, briefing.facts, length, item.source_url)  # noqa: E731
            kind = "影片腳本"
        content = office.writer.revise(content, [f"老闆的要求：{instructions}"], briefing)
        author.handoff(reviewer.id, "改好的稿")
        content, review, passed = reviewer.review(kind, content, item, briefing, check, author=author)

        if isinstance(content, ThreadsDraft):
            payload.update(content.model_dump())
            title = content.text.strip().splitlines()[0][:40]
            if media.get("image") or not draft["media"]:
                media = card_media(author, content, date.fromisoformat(draft["day"])) or media
        elif isinstance(content, CarouselDraft):
            payload.update(content.model_dump(), caption_full=instagram_caption(content.caption, content.hashtags))
            title = content.slides[0].title if content.slides else draft["title"]
            if office.settings.render_media:
                folder = office.day_media_dir(date.fromisoformat(draft["day"])) / f"carousel-{draft['id']}-{token_hex(3)}"
                art = office.media_file(media["art"]) if media.get("art") else None
                files = office.renderer.carousel(content, folder, art=art)
                media["images"] = [office.media_ref(p) for p in files]
        else:
            if draft["channel"] == "youtube":
                payload.update(title=content.youtube_title, description=content.youtube_description, script=content.model_dump())
                title = content.youtube_title
            else:
                payload.update(content.model_dump(), caption_full=instagram_caption(content.caption, content.hashtags))
                title = content.title
            if office.settings.render_media:
                orientation = "landscape" if draft["format"] == "long" else "portrait"
                media.update(office.staff["video"].render(content, date.fromisoformat(draft["day"]), orientation))
        status = "pending_approval" if passed else "needs_changes"
        office.store.update_draft(draft["id"], payload=payload, media=media, review=review, status=status, title=title)
        office.draft_changed(draft["id"])
        author.handoff("boss", f"#{draft['id']} 改好了", draft_id=draft["id"])
        author.status("done", f"#{draft['id']} 改好了")
        return f"#{draft['id']} 改好了，放回審核匣" + ("" if passed else f"（審稿還有意見：{review['issues'][0][:40]}）")

    def _do_new_post(self, action: ChiefAction) -> str:
        office = self.office
        channel = action.channel or "threads"
        fmt = action.format or ("text" if channel == "threads" else "carousel")
        if (channel, fmt) not in {("threads", "text"), ("instagram", "carousel"), ("instagram", "reel")}:
            raise ValueError("加做只支援 Threads 貼文、IG 輪播、IG Reels")
        topic = (action.topic or action.instructions).strip()
        if not topic:
            raise ValueError("要加做什麼題目？")
        item = PlanItem(channel=channel, format=fmt, pillar="reach" if fmt == "reel" else "value", angle=action.angle or "list",
                        topic=topic, brief=action.instructions or topic)
        slot = self._next_slot(channel)
        run_id = (office.store.latest_run() or {}).get("id")
        desk = {"text": "threads", "carousel": "designer", "reel": "video"}[fmt]
        self.handoff(desk, "加做一則")

        def work() -> str:
            briefing = office.briefing_for_replies(with_news=True)
            if fmt == "text":
                draft_id = office.staff["threads"].produce(run_id, item, briefing, slot)
            elif fmt == "carousel":
                draft_id, _ = office.staff["designer"].produce(run_id, item, briefing, slot)
            else:
                draft_id = office.staff["video"].reel(run_id, item, briefing, slot, slot + timedelta(minutes=30))
            return f"加做的「{topic[:20]}」好了（#{draft_id}），在審核匣等你"

        self._background("加做", work)
        return f"已經請 {office.staff[desk].persona.name} 加做「{topic[:20]}」，預計 {self._local(slot.isoformat()):%H:%M} 發"

    def _do_reschedule(self, action: ChiefAction) -> str:
        draft = self._draft(action.draft_id)
        match = re.fullmatch(r"\s*(\d{1,2})[:：](\d{2})\s*", action.time or "")
        if not match or int(match.group(1)) > 23 or int(match.group(2)) > 59:
            raise ValueError("時間請用 HH:MM，例如 20:30")
        when = self.office.at(date.fromisoformat(draft["day"]), time(int(match.group(1)), int(match.group(2))))
        self.office.store.update_draft(draft["id"], scheduled_at=when.astimezone(timezone.utc).isoformat(timespec="seconds"))
        self.office.draft_changed(draft["id"])
        late = "（這個時間已經過了，核准後會馬上發）" if when < datetime.now(timezone.utc) else ""
        return f"#{draft['id']} 改到 {when:%m/%d %H:%M}{late}"

    def _do_reject(self, action: ChiefAction) -> str:
        draft = self._draft(action.draft_id)
        self.office.reject(draft["id"], action.instructions)
        return f"#{draft['id']} 退回了"

    def _do_note_for_tomorrow(self, action: ChiefAction) -> str:
        text = action.instructions.strip()
        if not text:
            raise ValueError("要記什麼給明天的企劃？")
        notes = json.loads(self.office.store.get("boss_notes") or "[]")[-9:] + [text[:120]]
        self.office.store.set("boss_notes", json.dumps(notes, ensure_ascii=False))
        self.handoff("strategist", "明天的交代")
        return f"記下來了，明天 Ivy 排內容時會照做：{text[:30]}"

    # ---- helpers ----
    def _local(self, iso: str) -> datetime:
        return datetime.fromisoformat(iso).astimezone(self.office.settings.timezone)

    def _next_slot(self, channel: str) -> datetime:
        settings, now = self.office.settings, self.office.local_now()
        candidates = settings.threads_slots if channel == "threads" else (settings.instagram_slot,)
        for moment in candidates:
            slot = self.office.at(now.date(), moment)
            if slot > now + timedelta(minutes=30):
                return slot
        return (now + timedelta(hours=1)).replace(second=0, microsecond=0)
