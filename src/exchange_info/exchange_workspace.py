"""Student-owned work across the exchange journey, separate from official decisions.

Notice extraction is local and conservative: an explicit date is a candidate,
never a verified deadline. Imported tasks require the student's review.
"""
from __future__ import annotations

import copy
import hashlib
import re
import unicodedata
from datetime import date, time
from typing import Literal
from urllib.parse import urlsplit

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

STAGES = {
    "selection": "選校與探索", "home": "校內申請", "interview": "面試準備",
    "nomination": "錄取與提名", "host": "合作校申請", "departure": "出發準備",
    "arrival": "抵達與安頓", "abroad": "交換生活", "return": "返國與學分",
}
KINDS = {"task": "一般待辦", "document": "文件", "interview": "面試練習",
         "course": "課程", "life": "生活準備", "travel": "旅行", "internship": "實習", "community": "同梯交流"}


class Course(BaseModel):
    model_config = ConfigDict(extra="forbid")
    credits: float | None = Field(default=None, ge=0, le=60)
    weekday: int | None = Field(default=None, ge=1, le=7)
    start: time | None = None
    end: time | None = None
    recognition: Literal["unknown", "asking", "confirmed", "not_recognized"] = "unknown"

    @model_validator(mode="after")
    def times(self):
        if bool(self.start) != bool(self.end) or (self.start and not self.weekday):
            raise ValueError("課程時間請一併填寫星期、開始與結束時間。")
        if self.start and self.end <= self.start:
            raise ValueError("課程結束時間必須晚於開始時間。")
        return self


class WorkspaceTask(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    id: str = Field(pattern=r"^[a-zA-Z0-9_-]{8,64}$")
    title: str = Field(min_length=1, max_length=160)
    stage: Literal["selection", "home", "interview", "nomination", "host", "departure", "arrival", "abroad", "return"] = "departure"
    kind: Literal["task", "document", "interview", "course", "life", "travel", "internship", "community"] = "task"
    status: Literal["todo", "doing", "waiting", "done"] = "todo"
    action: Literal["prepare", "submit"] = "prepare"
    optional: bool = False
    notes: str = Field(default="", max_length=12000)
    due_date: date | None = None
    date_kind: Literal["unknown", "personal", "notice"] = "unknown"
    date_reviewed: bool = False
    recipient: str = Field(default="", max_length=200)
    batch: str = Field(default="", max_length=80)
    signers: str = Field(default="", max_length=200)
    waiting_for: str = Field(default="", max_length=300)
    depends_on: list[str] = Field(default_factory=list, max_length=30)
    source_label: str = Field(default="", max_length=200)
    source_url: str = Field(default="", max_length=2000)
    source_excerpt: str = Field(default="", max_length=6000)
    origin: Literal["manual", "notice", "guide", "template"] = "manual"
    file_version_id: str | None = Field(default=None, min_length=8, max_length=80)
    file_location: str = Field(default="", max_length=500)
    course: Course | None = None

    @field_validator("source_url")
    @classmethod
    def safe_link(cls, value):
        if value:
            url = urlsplit(value)
            if url.scheme not in {"http", "https"} or not url.hostname or url.username or url.password:
                raise ValueError("來源網址請使用完整的 http 或 https 網址。")
        return value

    @model_validator(mode="after")
    def dates_and_kind(self):
        if self.due_date and self.date_kind == "unknown":
            raise ValueError("填寫日期後，請選擇個人目標或通知期限。")
        if not self.due_date and self.date_kind != "unknown":
            raise ValueError("尚未確認日期時，請選擇日期待確認。")
        if self.date_kind == "notice" and not (self.date_reviewed and self.source_label and (self.source_url or self.source_excerpt)):
            raise ValueError("通知期限需要來源名稱、網址或原文，並由你核對日期。")
        if self.course and self.kind != "course":
            raise ValueError("課程欄位只能用於課程項目。")
        if self.file_version_id and self.kind != "document":
            raise ValueError("請將項目類型設為文件，再連結檔案。")
        if self.status == "done" and self.waiting_for:
            raise ValueError("尚有等待事項，請先清除等待原因再標記完成。")
        return self


class WorkspaceSave(BaseModel):
    model_config = ConfigDict(extra="forbid")
    revision: int = Field(ge=1)
    tasks: list[WorkspaceTask] = Field(max_length=250)
    credit_goal: float | None = Field(default=None, ge=0, le=120)


class NoticePreview(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    text: str = Field(min_length=1, max_length=80000)
    source_label: str = Field(min_length=1, max_length=200)
    source_url: str = Field(default="", max_length=2000)
    _url = field_validator("source_url")(WorkspaceTask.safe_link.__func__)


def task_id(*values):
    return hashlib.sha256("\n".join(values).encode()).hexdigest()[:24]


def validate_dependencies(tasks):
    by_id = {task.id: task for task in tasks}
    if len(by_id) != len(tasks):
        raise ValueError("任務識別碼重複，請重新載入。")
    visited, visiting = set(), set()

    def visit(key):
        if key in visiting:
            raise ValueError("前置任務不能形成循環。")
        if key in visited:
            return
        visiting.add(key)
        for dependency in by_id[key].depends_on:
            if dependency not in by_id:
                raise ValueError("前置任務不在這份計畫內；刪除前請先解除依賴。")
            visit(dependency)
        visiting.remove(key)
        visited.add(key)

    for key in by_id:
        visit(key)


def workspace_view(plan):
    """Completion of a submission is invalidated if a prerequisite is reopened."""
    saved = plan.get("workspace") or {"tasks": [], "credit_goal": None}
    tasks = copy.deepcopy(saved.get("tasks", []))
    by_id = {task["id"]: task for task in tasks}
    resolved = {}

    def done(key, seen=frozenset()):
        if key in resolved:
            return resolved[key]
        task = by_id.get(key)
        if not task or key in seen:
            return False
        result = task["status"] == "done" and not task.get("waiting_for") and not task.get("file_unavailable")
        if task.get("action") == "submit":
            result = result and all(done(dep, seen | {key}) for dep in task.get("depends_on", []))
        resolved[key] = result
        return result

    for task in tasks:
        task["blocked_by"] = [dep for dep in task.get("depends_on", []) if not done(dep)]
        task["effective_status"] = task["status"]
        if task.get("waiting_for") or (task.get("action") == "submit" and task["blocked_by"]) or (task["status"] == "done" and not done(task["id"])):
            task["effective_status"] = "waiting"
    courses = [t for t in tasks if t.get("kind") == "course" and t.get("course")]
    conflicts = []
    for i, a in enumerate(courses):
        for b in courses[i + 1:]:
            x, y = a["course"], b["course"]
            if x.get("weekday") and x.get("weekday") == y.get("weekday") and all(q.get("start") and q.get("end") for q in (x, y)):
                if x["start"] < y["end"] and y["start"] < x["end"]:
                    conflicts.append([a["id"], b["id"]])
    return {"tasks": tasks, "credit_goal": saved.get("credit_goal"),
            "credits": sum(t["course"].get("credits") or 0 for t in courses), "course_conflicts": conflicts}


DATE = re.compile(r"(?<!\d)(\d{3,4})\s*[年/.-]\s*(\d{1,2})\s*[月/.-]\s*(\d{1,2})(?:日)?(?!\d)")
ACTION = re.compile(r"請|需|繳|交|上傳|回傳|準備|申請|面試|簽|補|填|提交|submit|upload|complete|required|deadline", re.I)


def preview_notice(payload: NoticePreview):
    paragraphs = [re.sub(r"^\s*(?:[•●*\-]\s*|\d+[、)]\s*|\d+\.\s+)?", "", p).strip() for p in re.split(r"[\n；;。]+", unicodedata.normalize("NFKC", payload.text))]
    result, batch, header, inherited = [], "", "", None
    for paragraph in filter(None, paragraphs):
        batch_match = re.search(r"第[一二三四五六七八九十\d]+(?:批|階段)|first batch|second batch", paragraph, re.I)
        raw_dates = list(DATE.finditer(paragraph))
        candidates = []
        warnings = []
        for match in raw_dates:
            year, month, day = map(int, match.groups())
            if len(match.group(1)) == 3:
                year += 1911
            try:
                candidates.append(date(year, month, day).isoformat())
            except ValueError:
                warnings.append("日期無效，請查原文。")
        candidates = list(dict.fromkeys(candidates))
        if batch_match:
            batch = batch_match.group(0)
            header = paragraph
            inherited = candidates[0] if len(candidates) == 1 else None
        if not ACTION.search(paragraph):
            if not re.search(r"履歷|計畫|成績|同意書|體檢|保險|護照|文件|CV|resume|transcript", paragraph, re.I):
                continue
        if len(candidates) > 1:
            warnings.append("同一段有多個日期，請逐項確認，未自動指定截止日。")
        # A date without a year in this item must not silently inherit a different
        # batch-header date. Keep it for the student's review instead.
        partial_date = not raw_dates and re.search(r"\d{1,2}\s*[月/]\s*\d{1,2}", paragraph)
        candidate = candidates[0] if len(candidates) == 1 else (inherited if not raw_dates and not partial_date else None)
        if not candidate:
            warnings.append("截止日期待確認；不會以目前年份補上未載明的年份。")
        recipient = re.search(r"(?:交至|繳交至|回傳至|寄至|提交至|上傳至|send to|submit to)\s*([^，,：:\n]{2,100})", paragraph, re.I)
        stage = "interview" if "面試" in paragraph else "departure" if re.search(r"體檢|保險|簽證|宿舍", paragraph) else "host" if re.search(r"合作校|姊妹校|接收校", paragraph) else "home"
        excerpt = (header + "\n" if header and header != paragraph else "") + paragraph
        task = WorkspaceTask(id=task_id(payload.source_label, payload.source_url, excerpt), title=paragraph[:160], stage=stage,
            kind="document" if re.search(r"文件|報告|保險|履歷|申請書|同意書|成績|計畫書|CV|transcript", paragraph, re.I) else "task",
            action="submit" if re.search(r"繳交|提交|回傳|上傳|submit|upload", paragraph, re.I) else "prepare",
            batch=batch, recipient=recipient.group(1).strip() if recipient else "",
            signers="、".join(dict.fromkeys(re.findall(r"家長|監護人|本人|系主任|指導教授", paragraph))) if re.search(r"簽|sign", paragraph, re.I) else "",
            source_label=payload.source_label, source_url=payload.source_url, source_excerpt=excerpt[:6000], origin="notice")
        result.append({"task": task.model_dump(mode="json"), "candidate_date": candidate, "warnings": warnings})
        if len(result) >= 40:
            break
    return {"items": result, "requires_review": True,
            "message": "逐項核對原文後再加入。日期是候選值，平台未核實通知真偽、適用對象或截止日。" if result else "沒有找到明確待辦。可改貼條列內容，或直接新增任務。"}


def suggestion_packs(context, country=""):
    from .destination_tips import guide_for_country, load_guides

    target = context["target_school"]
    packs = []
    definitions = [
        ("interview", "面試準備", "interview", "interview", False, [
            ("核對面試通知", "記錄時間、地點、使用語言、報到方式與需攜帶資料；尚未公告的欄位留待確認。"),
            ("練習自我介紹", "寫下自己的經歷、交換目標與具體例子，再計時練習。"),
            ("為什麼選擇這所學校？", f"查核 {target} 的課程或資源，貼上來源，寫出與自己目標的連結。"),
            ("準備面試追問", "練習：計畫改變時如何處理？你做過什麼相關準備？請用真實例子回答。這些是練習題，不是校方真題。"),
            ("整理歷屆面試經驗", "保存來源、年份與適用組別；將學生經驗和校方公告分開記錄。"),
        ]),
        ("documents", "分批文件與送件", "host", "document", False, [
            ("核對本次需要的文件", "比較母校與合作校要求，記下表格版本、份數、簽名、收件單位和各批期限。"),
            ("檢查可沿用的舊文件", "選取自己的文件版本，核對姓名、學期、目標學校、格式與時效；需要修改的地方記在筆記。"),
            ("記錄正式送件與收件結果", "完成校方系統、親簽或郵寄程序後，記錄送件日期、回條編號與收件確認。"),
        ]),
        ("life", "出發與落地生活", "departure", "life", False, [
            ("設定通訊與校園服務", "核對目的地可用的通訊、地圖與校園 App 官方入口，完成登入及聯絡測試。"),
            ("確認付款與銀行安排", "核對當地支付、開戶所需文件與台灣帳戶的海外使用設定，記錄待詢問事項。"),
            ("確認住宿與用品", "查宿舍已提供物品、報到時間、收件地址與代收規則，再整理採買清單。"),
            ("確認證件、健康與保險", "依個人情況及校方通知核對文件、體檢與保障要求；不要把通用清單當作必繳規定。"),
            ("安排抵達與緊急聯絡", "記下第一晚住宿、交通、校方窗口與官方緊急聯絡來源。"),
            ("處理台灣門號與帳戶", "確認海外接收驗證訊息、帳戶聯絡方式與必要的服務設定。筆記不需填入密碼或驗證碼。"),
        ]),
        ("return", "返國與學分", "return", "task", False, [
            ("保存成績與課程證明", "核對成績單寄送方式，保存課程大綱與修課證明。"),
            ("核對學分抵免與結案", "依母校規定確認抵免程序、心得報告、補助或保證金結案與期限。"),
        ]),
        ("travel", "旅行目標（自選）", "abroad", "travel", True, [
            ("整理想去的地方", "記錄景點、交通、預算與來源，確認與課程、簽證及校方出缺席規定相容。"),
        ]),
        ("internship", "實習探索（自選）", "abroad", "internship", True, [
            ("收藏實習機會", "記錄校方職涯資源、職缺來源、申請期限、聯絡窗口與需要的材料。"),
            ("確認實習適用資格", "向接收學校與官方確認交換身分、工作許可及課程要求；未確認前先記錄待詢問事項。"),
        ]),
        ("community", "同梯交流（自選）", "departure", "community", True, [
            ("認識同校同學期交換生", "到同梯交流區查看或自願發布邀請，透過站內討論認識彼此。"),
        ]),
    ]
    for key, title, stage, kind, optional, rows in definitions:
        tasks = [WorkspaceTask(id=task_id("template", key, name), title=name, stage=stage, kind=kind, optional=optional,
                 notes=detail, origin="template", source_label="UniWay 準備建議（非校方規定）").model_dump(mode="json") for name, detail in rows]
        packs.append({"id": key, "title": title, "tasks": tasks})
    if country and (guide := guide_for_country(country)):
        tasks = []
        for topic in guide.topics:
            for tip in topic.tips:
                tasks.append(WorkspaceTask(id=task_id("guide", guide.country, topic.topic, tip.title), title=tip.title,
                    stage="departure", kind="life", notes=tip.detail, origin="guide",
                    source_label=f"{guide.display_name}行前提醒 · {'待人工審核' if guide.review_status != 'reviewed' else '已審核'} · 查證 {tip.checked_at}",
                    source_url=tip.sources[0].url if tip.sources else "",
                    source_excerpt="\n".join(s.name + " " + s.url for s in tip.sources)).model_dump(mode="json"))
        packs.insert(0, {"id": "destination", "title": guide.display_name + "行前提醒", "tasks": tasks})
    return {"packs": packs, "countries": [{"value": g.country, "label": g.display_name} for g in load_guides().values()],
            "stages": STAGES, "kinds": KINDS}
