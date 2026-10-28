"""Data-update proposals: what a colleague found on a school's official site, written up so the boss can approve it
and Pat can open it as a draft pull request.

The AI colleagues only produce the finding (a SchoolCheck). Everything here is plain code: it decides whether the
finding is worth a proposal, how it looks in the inbox, and exactly which file and text a pull request would contain.
What the AI read from a web page is treated as untrusted text all the way through: it is trimmed, kept out of
Markdown that could notify people or hide a link, and the source link has to sit on the school's own domain or the
proposal waits in the inbox marked for your attention instead of looking routine.

A proposal adds one file under sources/audit/proposals/. Merging it does not change any platform data; it is the
evidence and the to-do for whoever applies the change (you, or a Claude Code or Codex session on the pull request).
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import asdict, dataclass
from urllib.parse import urlsplit

from .platforms.github import PROPOSAL_DIR

CHANNEL = "github"
FORMAT = "data_update"
# What each flagged status is called, in the inbox and in the pull request.
KINDS = {"new_notice": "新公告", "mismatch": "和平台不一致"}
# A proposal that is still on its way: asking again about the same school would only pile up duplicates.
OPEN = {"pending_approval", "needs_changes", "approved", "publishing"}
SCHEMA = "uniway-office-proposal/1"

# Control characters, and the Unicode controls that make text read in another order than it is written.
HIDDEN = re.compile(r"[\x00-\x08\x0b-\x1f\x7f​-‏‪-‮⁦-⁩﻿]")
URL = re.compile(r"https?://[^\s`<>]+")
SECOND_LEVEL = {"edu", "ac", "com", "org", "gov", "net", "co"}


def clean(text, limit: int) -> str:
    text = HIDDEN.sub("", str(text or ""))
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text).strip()
    return text[:limit]


def web_host(url: str) -> str:
    """The host of an http(s) link with no embedded login, otherwise ""."""
    try:
        parts = urlsplit(url.strip())
        host = (parts.hostname or "").lower().rstrip(".")
    except ValueError:
        return ""
    if parts.scheme not in {"http", "https"} or parts.username or parts.password or any(ch.isspace() for ch in url.strip()):
        return ""
    return host


def base_domain(host: str) -> str:
    """oia.ntu.edu.tw → ntu.edu.tw, www.cgu.edu.tw → cgu.edu.tw."""
    labels = host.split(".")
    if len(labels) >= 3 and labels[-2] in SECOND_LEVEL and len(labels[-1]) == 2:
        return ".".join(labels[-3:])
    return ".".join(labels[-2:])


def on_school_site(source_url: str, official_url: str) -> bool:
    source, official = web_host(source_url), web_host(official_url)
    return bool(source and official and base_domain(source) == base_domain(official))


def markdown_quote(text: str) -> str:
    """Untrusted text as a block quote: no @mentions, HTML or link syntax, and any URL inside it is not clickable."""
    parts = re.split(f"({URL.pattern})", text.replace("`", "'"))
    safe = []
    for index, part in enumerate(parts):
        if index % 2:  # a URL: shown, but inside a code span it is not a link
            safe.append(f"`{part}`")
        else:
            safe.append(part.replace("<", "&lt;").replace(">", "&gt;").replace("@", "@​").replace("[", "\\[").replace("]", "\\]"))
    lines = "".join(safe).splitlines() or [""]
    return "\n".join(f"> {line}" if line.strip() else ">" for line in lines)


@dataclass(frozen=True)
class Proposal:
    school_id: str
    school_name: str
    status: str  # new_notice | mismatch
    detail: str
    suggested_update: str
    source_url: str
    official_url: str
    platform_note: str
    author: str
    day: str  # YYYY-MM-DD, the day the colleague found it

    # ---- building one ----
    @classmethod
    def from_check(cls, check, school, *, author: str, day: str) -> "Proposal":
        return cls(
            school_id=school.id, school_name=school.name, status=check.status,
            detail=clean(check.detail, 800), suggested_update=clean(getattr(check, "suggested_update", ""), 600),
            source_url=clean(check.source_url, 500), official_url=school.official_url,
            platform_note=clean(f"{school.note}（支援程度 {school.level}，合作校約 {school.partners} 所）", 300),
            author=clean(author, 12), day=day,
        )

    @classmethod
    def from_payload(cls, payload: dict) -> "Proposal":
        return cls(**{name: str(payload.get(name, "")) for name in cls.__dataclass_fields__})

    def payload(self) -> dict:
        return asdict(self)

    # ---- where it goes ----
    @property
    def slug(self) -> str:
        return re.sub(r"[^a-z0-9]+", "_", self.school_id.lower()).strip("_")[:40] or "school"

    @property
    def digest(self) -> str:
        text = "\n".join([self.school_id, self.status, self.source_url, self.detail, self.suggested_update])
        return hashlib.sha1(text.encode("utf-8")).hexdigest()[:8]

    @property
    def path(self) -> str:
        return f"{PROPOSAL_DIR}/{self.day}-{self.slug}-{self.digest}.json"

    @property
    def branch(self) -> str:
        return f"office/{self.day}-{self.slug}-{self.digest}"

    @property
    def kind(self) -> str:
        return KINDS.get(self.status, self.status)

    # ---- is it safe to look routine? ----
    def issues(self) -> list[str]:
        found = []
        if not self.source_url:
            found.append("沒有附官方來源網址：核准前請先請同事補上，或自己到官網確認")
        elif not on_school_site(self.source_url, self.official_url):
            found.append(f"來源網址不在學校官網網域（官網 {web_host(self.official_url) or '未知'}，來源 {web_host(self.source_url) or '不是網頁連結'}），請先自己點開確認")
        if len(self.detail) < 6:
            found.append("說明太短，看不出發現了什麼")
        return found

    # ---- what the pull request contains ----
    def record(self) -> dict:
        return {
            "schema": SCHEMA,
            "school_id": self.school_id, "school_name": self.school_name, "status": self.status,
            "detail": self.detail, "suggested_update": self.suggested_update,
            "source_url": self.source_url, "official_url": self.official_url, "platform_record": self.platform_note,
            "proposed_by": self.author, "proposed_on": self.day,
            "note": "AI 同事讀取學校官網後整理的提案，不是已核實的資料；合併前請人工對照官方來源。合併這個檔案不會自動更新平台資料。",
        }

    def content(self) -> str:
        return json.dumps(self.record(), ensure_ascii=False, indent=2, sort_keys=True) + "\n"

    def pr_title(self) -> str:
        return f"資料更新提案：{self.school_name}（{self.kind}）"[:120]

    def commit_message(self) -> str:
        return f"office: {self.school_name} {self.kind}提案（{self.day}）"

    def pr_body(self) -> str:
        suggestion = markdown_quote(self.suggested_update) if self.suggested_update else "> （巡查同事沒有提出具體欄位，請依官方來源人工確認要改什麼）"
        if self.source_url and on_school_site(self.source_url, self.official_url):
            source = f"- {self.source_url}"
        elif self.source_url:
            source = f"- `{self.source_url}`\n- ⚠️ 這個網址不在學校官網網域，沒有做成連結，請確認後再點。"
        else:
            source = "- ⚠️ 沒有附來源網址"
        return (
            f"## 資料更新提案：{self.school_name}\n\n"
            f"**{self.kind}**｜{self.author} 於 {self.day} 巡查發現｜UniWay 行銷辦公室依老闆核准開的 draft PR\n\n"
            f"### 發現\n{markdown_quote(self.detail)}\n\n"
            f"### 建議更新\n{suggestion}\n\n"
            f"### 官方來源\n{source}\n\n"
            f"### 平台目前的紀錄\n{markdown_quote(self.platform_note)}\n\n"
            "---\n"
            f"這個 PR 只新增提案檔 `{self.path}`，不會改動任何平台資料。內容是 AI 同事讀官網後整理的，**請先點開官方來源核對**；"
            "確認無誤後，在這個分支補上實際的資料更新再合併，或關閉不用。\n"
        )


def queue_from_checks(office, author, checks, schools_by_name: dict) -> tuple[list[tuple[int, str]], list[str]]:
    """Put a proposal in the boss's inbox for each school a colleague flagged: ([(draft id, school)], lines to report).

    Proposals always wait for the boss, whatever OFFICE_APPROVAL says; a school with a proposal already waiting (or
    one from the same page handled today) is not proposed again."""
    store, day = office.store, office.today().isoformat()
    existing = [d for d in store.drafts(limit=300) if d["format"] == FORMAT]
    queued, notes, seen = [], [], set()
    for check in checks:
        if check.status not in KINDS or check.school in seen:  # a colleague may repeat a school across batches
            continue
        seen.add(check.school)
        school = schools_by_name.get(check.school)
        if school is None:
            notes.append(f"{check.school}：不在這次負責的學校清單裡（名稱要照清單），沒有送審")
            continue
        proposal = Proposal.from_check(check, school, author=author.persona.name, day=day)
        if any(_same_school(d, proposal, day) for d in existing):
            notes.append(f"{school.name}：已經有提案在審核匣或今天處理過了")
            continue
        issues = proposal.issues()
        draft_id = store.add_draft(
            run_id=None, day=day, channel=CHANNEL, format=FORMAT, title=f"{school.name}｜{proposal.kind}",
            payload=proposal.payload(), status="needs_changes" if issues else "pending_approval",
            review={"approved": not issues, "issues": issues, "notes": []}, scheduled_at=None,
        )
        author.handoff("boss", "資料更新提案", draft_id=draft_id)
        office.draft_changed(draft_id)
        existing.append(store.draft(draft_id))
        queued.append((draft_id, school.name))
    return queued, notes


def _same_school(draft: dict, proposal: Proposal, day: str) -> bool:
    payload = draft["payload"] or {}
    if payload.get("school_id") != proposal.school_id:
        return False
    return draft["status"] in OPEN or (draft["day"] == day and payload.get("source_url") == proposal.source_url and draft["status"] != "failed")
