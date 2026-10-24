"""Structured outputs the agents produce. The Claude writer asks for these schemas directly."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

Channel = Literal["threads", "instagram", "youtube"]
Format = Literal["text", "reply", "carousel", "reel", "story", "short", "long"]
Pillar = Literal["value", "reach", "trust", "story"]
Angle = Literal["pain", "choice", "list", "story", "news"]


class PlanItem(BaseModel):
    channel: Channel
    format: Format
    pillar: Pillar
    angle: Angle
    topic: str = Field(description="一句話的題目")
    brief: str = Field(description="給執行同事的重點：要講什麼、用哪些簡報裡的事實")
    source_url: str = Field(default="", description="引用公告時的官方來源網址，沒有就留空")


class DayPlan(BaseModel):
    theme: str = Field(description="今天的主軸，10 字左右")
    whiteboard: list[str] = Field(description="寫在辦公室白板上的 3～5 句重點，每句 20 字內")
    items: list[PlanItem]


class ThreadsDraft(BaseModel):
    text: str = Field(description="主文，不含任何網址")
    topic_tag: str = Field(description="一個主題標籤，不含 # 與句點")
    first_reply: str = Field(description="發文後自己留的第一則留言，放網址與補充")


class Slide(BaseModel):
    kind: Literal["cover", "point", "cta"]
    title: str
    body: str = ""


class CarouselDraft(BaseModel):
    slides: list[Slide]
    caption: str = Field(description="Instagram 說明欄，不含 hashtag")
    hashtags: list[str]
    art_prompt: str = Field(default="", description="封面插圖的畫面描述（給生圖用），不要包含任何文字或字母")


class Scene(BaseModel):
    kind: Literal["hook", "point", "stat", "cta"]
    heading: str = Field(description="畫面大標，12 字內")
    lines: list[str] = Field(description="依序出現的字幕，每行 12 字內")
    seconds: float


class VideoScript(BaseModel):
    title: str
    scenes: list[Scene]
    caption: str = Field(description="Reels 說明欄，不含 hashtag")
    hashtags: list[str]
    youtube_title: str
    youtube_description: str


class Review(BaseModel):
    approved: bool
    issues: list[str] = Field(description="必須修改的問題")
    notes: list[str] = Field(default_factory=list, description="不阻擋發佈的建議")


class ReplyDraft(BaseModel):
    comment_id: str
    text: str


class ReplyBatch(BaseModel):
    replies: list[ReplyDraft]


class Finding(BaseModel):
    topic: str = Field(description="學生在討論或關心的題目")
    insight: str = Field(description="一兩句重點，只寫查得到的內容")
    source_url: str = Field(description="可以點開核對的來源網址")


class ResearchNotes(BaseModel):
    findings: list[Finding]


class Preflight(BaseModel):
    go: bool = Field(description="可以發就 true；需要老闆再看一次就 false")
    reason: str = Field(description="判斷理由，一句話")


class Insights(BaseModel):
    notes: list[str] = Field(description="給企劃的 2～4 點建議，每點一句")


ChiefActionType = Literal["start_day", "redo", "new_post", "reschedule", "reject", "note_for_tomorrow", "set_brain"]
DeskRole = Literal["chief", "research", "strategist", "threads", "designer", "video", "reviewer", "community", "publisher", "analyst", ""]


class ChiefAction(BaseModel):
    type: ChiefActionType = Field(
        description=(
            "start_day：馬上開工做今天的內容；redo：請作者依 instructions 重寫 draft_id 那則草稿；"
            "new_post：今天加做一則（channel、format、topic、angle）；reschedule：把 draft_id 改到 time（HH:MM，台北時間）；"
            "reject：退回 draft_id，理由寫在 instructions；note_for_tomorrow：把 instructions 記給明天的企劃；"
            "set_brain：改某個工作（role）用的工具（brain）、模型（model）或思考強度（effort），沒要改的欄位留空，填 default 代表改回原本設定"
        )
    )
    draft_id: int = Field(default=0, description="草稿編號，沒有就填 0")
    instructions: str = Field(default="", description="要交代的內容")
    channel: Literal["threads", "instagram", ""] = ""
    format: Literal["text", "carousel", "reel", ""] = ""
    topic: str = ""
    angle: Literal["pain", "choice", "list", "story", "news", ""] = ""
    time: str = Field(default="", description="HH:MM")
    role: DeskRole = Field(default="", description="set_brain 用：要改的工作")
    brain: Literal["claude-code", "codex", "antigravity", "api", "offline", "default", ""] = ""
    model: str = Field(default="", description="set_brain 用：模型名稱，例如 sonnet、opus、claude-sonnet-5-5、gpt-5.5、Gemini 3.7 Pro")
    effort: Literal["low", "medium", "high", "xhigh", "max", "default", ""] = ""


class ChiefReply(BaseModel):
    reply: str = Field(description="用聊天的口吻回覆老闆，說明你安排了什麼、哪些事做不到")
    actions: list[ChiefAction]
