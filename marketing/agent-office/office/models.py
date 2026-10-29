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


class FieldEdit(BaseModel):
    target: str = Field(description="要改的地方：檔案 → 學校 id → 欄位，優先用「平台現有紀錄」裡出現的欄位名稱（例如 verified_window_deadlines.py → cgu → online_deadline.value_text）")
    current: str = Field(description="平台現在寫的內容，照抄；平台沒有這一項就寫「沒有」")
    proposed: str = Field(description="建議改成什麼；只寫官網上真的看到的，不要捏造日期、名額或網址")
    basis: str = Field(description="官網依據：頁面上的原文摘錄（50 字內）或所在位置")


class Verdict(BaseModel):
    school: str = Field(description="學校名稱，照抄清單上的名字")
    verdict: Literal["confirmed_update", "already_current", "not_exchange", "not_confirmed", "unreachable"] = Field(
        description=(
            "confirmed_update 官網確實有校級交換相關的新公告或規定異動，而且平台現有紀錄沒有反映或寫法不一致；"
            "already_current 官網確有此事但平台已經是最新；"
            "not_exchange 內容不屬於校級交換（例如雙聯學位、外部活動、其他校際競賽）；"
            "not_confirmed 官網上看不到或無法證實；"
            "unreachable 頁面打不開"
        )
    )
    reason: str = Field(description="判斷理由，一兩句，寫你在官網上看到什麼")
    source_url: str = Field(description="你實際打開核對的官網頁面網址")
    edits: list[FieldEdit] = Field(default_factory=list, description="只有 confirmed_update 才填：要改平台哪些欄位、改成什麼；沒把握就不要寫，改判 not_confirmed")


class VerificationReport(BaseModel):
    verdicts: list[Verdict]


class VisualSpec(BaseModel):
    """The one set of rules every page of a set shares."""

    margin: int = Field(default=80, description="左右安全邊距（px），60～100，整組一致")
    title_size: int = Field(default=88, description="主標題字級（px），72～96")
    body_size: int = Field(default=44, description="正文字級（px），36～44")
    line_height: float = Field(default=1.5, description="正文行高，是字級的 1.4～1.6 倍")
    accent: Literal["blue", "teal", "coral"] = Field(default="blue", description="整組的重點色：blue 藍（品牌色，預設）、teal 青綠、coral 珊瑚紅")
    emphasis: Literal["color", "chip", "size"] = Field(default="color", description="整組唯一的主要強調手法：color 換色、chip 色塊底、size 放大")
    page_number: Literal["top", "foot"] = Field(default="top", description="頁碼位置，整組固定：top 右上角、foot 頁尾")


class VisualSlide(BaseModel):
    layout: Literal["cover", "focus", "steps", "compare", "stat", "cta"] = Field(
        description=(
            "這一頁的版面：cover 封面（只給第一頁）、cta 結尾行動頁（只給最後一頁）；中間頁選 focus 一個重點加說明卡、"
            "steps 2～5 個步驟、compare 兩邊比較、stat 一個大數字或關鍵詞配說明"
        )
    )
    title_lines: list[str] = Field(default_factory=list, description="主標題依語意斷行（最多 3 行）；合起來必須和原本的主標題一字不差，只能決定在哪裡斷行，不能改字")
    emphasis: list[str] = Field(default_factory=list, description="這一頁要突出的關鍵詞（最多 2 個），必須是主標題或內文裡原本就有的字")
    items: list[str] = Field(default_factory=list, description="steps 的各步驟、compare 的兩邊、stat 的第一項是大數字或關鍵詞；每一項必須是內文裡原本就有的字，不能改寫")
    labels: list[str] = Field(default_factory=list, description="compare 兩邊的標籤（各 6 字內），必須是標題或內文裡原本就有的字；沒有就留空")
    picture: str = Field(default="", description="這一頁的示意圖或視覺需求，一句話（例如「兩欄比較」「三個步驟」）")


class VisualPlan(BaseModel):
    outline: list[str] = Field(description="逐頁大綱：每頁一句話，只說這一頁要傳達的一個主要訊息")
    spec: VisualSpec
    slides: list[VisualSlide] = Field(description="和提供的頁面一一對應：順序相同、頁數相同")
    art_prompt: str = Field(default="", description="封面插圖的畫面描述（只畫插圖，不含任何文字或字母）；有吉祥物時要寫出牠的眼睛；不需要插圖就留空")
    issues: list[str] = Field(default_factory=list, description="你發現的內容問題（例如某頁資訊太多、建議刪減或拆頁）；不要自己改字，寫在這裡給作者和老闆看")


class Preflight(BaseModel):
    go: bool = Field(description="可以發就 true；需要老闆再看一次就 false")
    reason: str = Field(description="判斷理由，一句話")


class Insights(BaseModel):
    notes: list[str] = Field(description="給企劃的 2～4 點建議，每點一句")


ChiefActionType = Literal["start_day", "redo", "new_post", "reschedule", "reject", "note_for_tomorrow", "set_brain", "hire", "assign", "dismiss",
                          "watch_schools", "set_schedule", "set_office_times", "add_routine", "remove_routine", "set_verifier", "redo_image"]


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
            "remove_routine：刪掉編號 routine_id 的固定排程；"
            "redo_image：請 Mori 重新做 draft_id 那則的圖（版面重新設計、封面插圖重畫），instructions 寫對圖的要求；文字不變，要改文字用 redo；"
            "set_verifier：指定 name 的新同事當驗證員，巡查同事發現新公告或不一致後，先交給她重新打開官網驗證，確認要更新平台的才送進審核匣；name 留空代表取消驗證員"
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
    name: str = Field(default="", description="hire／assign／dismiss／set_verifier 用：同事的名字")
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
