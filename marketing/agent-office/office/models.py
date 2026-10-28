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
    card_title: str = Field(default="", description="附圖上的大標題，10～18 字，抓住主文重點，不含網址")
    card_body: str = Field(default="", description="附圖上的一句補充，30 字以內，不含網址；可以留空")


class Slide(BaseModel):
    kind: Literal["cover", "point", "cta"]
    title: str
    body: str = ""


class CarouselDraft(BaseModel):
    slides: list[Slide]
    caption: str = Field(description="Instagram 說明欄，不含 hashtag")
    hashtags: list[str]
    art_prompt: str = Field(default="", description="封面插圖的畫面描述（給生圖用），不要包含任何文字或字母；有吉祥物時要寫出牠的眼睛")


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


class Report(BaseModel):
    """What a new colleague hands back for an assignment that is not a post."""

    summary: str = Field(description="兩三句話的結論")
    points: list[str] = Field(description="3～8 個重點，每點一句")
    sources: list[str] = Field(description="查到的來源網址；沒有就留空，不要捏造")


class SchoolCheck(BaseModel):
    school: str = Field(description="學校名稱，照抄清單上的名字")
    status: Literal["no_change", "new_notice", "mismatch", "unreachable"] = Field(
        description="no_change 沒有新公告也和平台一致；new_notice 有新的交換公告或規定；mismatch 官網和平台資料不一致；unreachable 官網打不開或找不到交換頁"
    )
    detail: str = Field(description="一兩句說明看到什麼；沒變化就寫已確認的頁面")
    source_url: str = Field(description="實際看的官網頁面網址")
    suggested_update: str = Field(
        default="", description="new_notice 或 mismatch 時，建議平台更新哪個欄位、改成什麼（例如「校內截止日改為 2026-11-03 17:00」）；"
                                "只寫官網上真的看到的，不確定就留空；其他狀態留空")


class SchoolReport(BaseModel):
    checks: list[SchoolCheck]


class Preflight(BaseModel):
    go: bool = Field(description="可以發就 true；需要老闆再看一次就 false")
    reason: str = Field(description="判斷理由，一句話")


class Insights(BaseModel):
    notes: list[str] = Field(description="給企劃的 2～4 點建議，每點一句")


ChiefActionType = Literal["start_day", "redo", "new_post", "reschedule", "reject", "note_for_tomorrow", "set_brain", "hire", "assign", "dismiss",
                          "watch_schools", "set_schedule", "set_office_times", "add_routine", "remove_routine"]


class ChiefAction(BaseModel):
    type: ChiefActionType = Field(
        description=(
            "start_day：馬上開工做今天的內容；redo：請作者依 instructions 重寫 draft_id 那則草稿；"
            "new_post：今天加做一則（channel、format、topic、angle）；reschedule：把 draft_id 改到 time（HH:MM，台北時間）；"
            "reject：退回 draft_id，理由寫在 instructions；note_for_tomorrow：把 instructions 記給明天的企劃；"
            "set_brain：改某個工作（role）用的工具（brain）、模型（model）或思考強度（effort），沒要改的欄位留空，填 default 代表改回原本設定；"
            "hire：新增一位同事（name、title、instructions 寫他負責什麼，可一起給 brain、model、effort）；"
            "assign：交代工作給新同事（name 填他的名字，instructions 寫要做什麼，task_kind 選 report 或 threads）；"
            "dismiss：請新同事離開（name）；"
            "watch_schools：把平台支援的大學平均分給 names 裡的新同事，之後每天巡查各校官網的交換公告與規定是否有變、和平台資料是否一致；"
            "set_schedule：設定 names 裡的新同事每天做固定工作的時間（times，HH:MM，可以多個）；"
            "set_office_times：改每天的時間表，which 選 start（開工）、threads（Threads 發文，幾個時間就每天幾篇）、instagram、youtube，"
            "times 填新時間，填 [\"default\"] 代表改回原本設定；"
            "add_routine：新增每天固定時間做的事（times、task_kind、instructions 寫題目或工作，name 填新同事名字，原本的同事可留空）；"
            "remove_routine：刪掉編號 routine_id 的固定排程"
        )
    )
    draft_id: int = Field(default=0, description="草稿編號，沒有就填 0")
    instructions: str = Field(default="", description="要交代的內容")
    channel: Literal["threads", "instagram", ""] = ""
    format: Literal["text", "carousel", "reel", ""] = ""
    topic: str = ""
    angle: Literal["pain", "choice", "list", "story", "news", ""] = ""
    time: str = Field(default="", description="HH:MM")
    role: str = Field(default="", description="set_brain 用：要改的工作（狀態裡 role= 後面的值）")
    name: str = Field(default="", description="hire／assign／dismiss 用：同事的名字")
    title: str = Field(default="", description="hire 用：職稱，例如 Dcard 研究員")
    task_kind: Literal["report", "threads", "schools", "carousel", "reel", ""] = Field(
        default="", description="assign／add_routine 用：report 查資料或分析後回報；threads 寫一則 Threads 草稿；schools 巡查分到的學校；"
                                "carousel、reel 只給 add_routine：請 Mori 做 IG 輪播、阿剪做 Reels")
    every_day: bool = Field(default=False, description="assign 用：true 代表從明天起每天開工時都做這件事")
    names: list[str] = Field(default_factory=list, description="watch_schools／set_schedule 用：新同事名字，watch_schools 依序分前段、後段")
    times: list[str] = Field(default_factory=list, description="set_schedule／set_office_times／add_routine 用：每天幾點，例如 [\"10:00\", \"17:00\"]")
    which: Literal["start", "threads", "instagram", "youtube", ""] = Field(default="", description="set_office_times 用：要改哪一個時間")
    routine_id: int = Field(default=0, description="remove_routine 用：固定排程編號（R 後面的數字）")
    brain: Literal["claude-code", "codex", "antigravity", "api", "offline", "default", ""] = ""
    model: str = Field(default="", description="set_brain 用：模型名稱，例如 sonnet、opus、claude-sonnet-5-5、gpt-5.5、Gemini 3.7 Pro")
    effort: Literal["low", "medium", "high", "xhigh", "max", "default", ""] = ""


class ChiefReply(BaseModel):
    reply: str = Field(description="用聊天的口吻回覆老闆，說明你安排了什麼、哪些事做不到")
    actions: list[ChiefAction]
