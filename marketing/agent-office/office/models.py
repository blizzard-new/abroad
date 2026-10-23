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
