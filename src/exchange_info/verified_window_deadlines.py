"""Verified 10-week window deadlines, submission rules, study-plan limits, and retention hooks.

Every school card exposes three verified rules side-by-side:
1. 校內線上報名截止日 (online_deadline)
2. 紙本繳件截止日／送件規定 (paper_deadline)
3. 讀書計畫字數／頁數上限 (study_plan_limit)

Each rule carries a mandatory official HTTPS source URL and last checked date (YYYY-MM-DD).
When an official notice has not announced an exact date or closing hour, ``exact_deadline_at``
remains ``None`` rather than fabricating ``23:59``.
"""

from __future__ import annotations

import os
from datetime import date, datetime, timedelta, timezone
from typing import Any
from urllib.parse import quote, urlencode

from .models import (
    VerifiedRuleFact,
    VerifiedSchoolWindowCard,
    VerifiedWindowDeadlineCatalog,
    VerifiedWindowSubtask,
)
from .university_registry import SUPPORTED_UNIVERSITIES, require_university

TAIPEI_TZ = timezone(timedelta(hours=8))
WINDOW_START_DATE = "2026-10-19"
WINDOW_END_DATE = "2026-12-31"
CATALOG_LAST_CHECKED_AT = "2026-10-20"
DEFAULT_LINE_OA_ID = "@uniway"


def _dt(
    year: int,
    month: int,
    day: int,
    hour: int,
    minute: int = 0,
    second: int = 0,
) -> datetime:
    return datetime(year, month, day, hour, minute, second, tzinfo=TAIPEI_TZ)


def _google_calendar_template_url(
    *,
    title: str,
    due_date: str,
    details: str,
    source_url: str,
) -> str:
    start = datetime.strptime(due_date, "%Y-%m-%d").date()
    end = start + timedelta(days=1)
    dates = f"{start.strftime('%Y%m%d')}/{end.strftime('%Y%m%d')}"
    compact_details = details if len(details) <= 140 else f"{details[:137]}..."
    query = urlencode(
        {
            "action": "TEMPLATE",
            "text": title,
            "dates": dates,
            "details": f"{compact_details}\n官方來源：{source_url}",
            "sprop": f"website:{source_url}",
        }
    )
    return f"https://calendar.google.com/calendar/render?{query}"


def _line_oa_url(message: str) -> str:
    oa_id = os.environ.get("EXCHANGE_LINE_OA_ID", DEFAULT_LINE_OA_ID).strip() or DEFAULT_LINE_OA_ID
    if not oa_id.startswith("@"):
        oa_id = f"@{oa_id}"
    compact_msg = message if len(message) <= 160 else f"{message[:157]}..."
    return f"https://line.me/R/oaMessage/{quote(oa_id, safe='@')}/?{quote(compact_msg)}"


def _escape_ics(value: str | None) -> str:
    return (
        str(value or "")
        .replace("\\", "\\\\")
        .replace("\r\n", "\\n")
        .replace("\n", "\\n")
        .replace(",", "\\,")
        .replace(";", "\\;")
    )


def _build_subtasks(
    *,
    school_id: str,
    short_name: str,
    anchor_date: date,
    online_rule: VerifiedRuleFact,
    paper_rule: VerifiedRuleFact,
    study_plan_rule: VerifiedRuleFact,
    extra_milestones: list[tuple[str, str, str, str, str, str, str]] | None = None,
) -> list[VerifiedWindowSubtask]:
    """Generate preparation sub-tasks leading up to the school's deadline."""
    floor_date = date(2026, 10, 19)

    def _clamped(days_before: int) -> str:
        target = anchor_date - timedelta(days=days_before)
        if target < floor_date and anchor_date >= floor_date:
            target = floor_date
        return target.strftime("%Y-%m-%d")

    raw_tasks: list[tuple[str, str, str, str, str, str, str, str]] = [
        (
            f"{school_id}-subtask-study-plan",
            f"[{short_name}交換] 完成讀書計畫與自傳初稿（核對字數／頁數規定）",
            _clamped(14),
            "截止前 14 天",
            "documents",
            f"規定摘要：{study_plan_rule.value_text}（最後查核：{study_plan_rule.last_checked_at}）",
            study_plan_rule.source_title,
            study_plan_rule.source_url,
        ),
        (
            f"{school_id}-subtask-signatures",
            f"[{short_name}交換] 申請歷年成績單、核對語檢效期並送請師長／系所核章",
            _clamped(7),
            "截止前 7 天",
            "documents",
            f"紙本／核章規定：{paper_rule.value_text}（最後查核：{paper_rule.last_checked_at}）",
            paper_rule.source_title,
            paper_rule.source_url,
        ),
        (
            f"{school_id}-subtask-final-check",
            f"[{short_name}交換] 線上系統填報與 PDF 檔案規格最終檢查",
            _clamped(3),
            "截止前 3 天",
            "home",
            f"線上報名規定：{online_rule.value_text}（最後查核：{online_rule.last_checked_at}）",
            online_rule.source_title,
            online_rule.source_url,
        ),
        (
            f"{school_id}-subtask-deadline",
            f"[{short_name}交換] 校內申請正式截止日（防漏最後確認）",
            anchor_date.strftime("%Y-%m-%d"),
            "正式截止日",
            "home",
            f"線上：{online_rule.value_text}｜紙本／送件：{paper_rule.value_text}",
            online_rule.source_title,
            online_rule.source_url,
        ),
    ]
    if extra_milestones:
        for item_id, title, due_date_str, offset_label, category, note, src_url in extra_milestones:
            raw_tasks.append(
                (
                    item_id,
                    title,
                    due_date_str,
                    offset_label,
                    category,
                    note,
                    online_rule.source_title,
                    src_url,
                )
            )

    subtasks: list[VerifiedWindowSubtask] = []
    for (
        task_id,
        title,
        due_date_str,
        offset_label,
        category,
        note,
        source_title,
        source_url,
    ) in raw_tasks:
        checked_at = (
            study_plan_rule.last_checked_at
            if "study-plan" in task_id
            else paper_rule.last_checked_at
            if "signatures" in task_id
            else online_rule.last_checked_at
        )
        subtasks.append(
            VerifiedWindowSubtask(
                id=task_id,
                title=title,
                due_date=due_date_str,
                offset_label=offset_label,
                category=category,  # type: ignore[arg-type]
                note=note,
                source_title=source_title,
                source_url=source_url,
                last_checked_at=checked_at,
                google_calendar_url=_google_calendar_template_url(
                    title=title,
                    due_date=due_date_str,
                    details=f"{note}\n查核依據：{source_title}（最後查核：{checked_at}）",
                    source_url=source_url,
                ),
            )
        )
    return subtasks


_RAW_SPECS: list[dict[str, Any]] = [
    {
        "school_id": "yzu",
        "in_ten_week_window": True,
        "window_status": "open",
        "window_badge": "10 週窗口進行中 · 10/20 赴陸收件・11/01 提名截止",
        "cycle_label": "115-2（2027 春季班）赴大陸地區姊妹校交換甄選（國際組已於 09/22 截止）",
        "primary_deadline_date": "2026-10-20",
        "primary_deadline_at": _dt(2026, 11, 1, 17, 0),
        "anchor_date": date(2026, 10, 20),
        "online_deadline": VerifiedRuleFact(
            rule_key="online_deadline",
            label="校內線上報名截止日",
            value_text="赴大陸交換校內收件至 2026/10/20（官方未公告截止時刻，請於上班時間送件）、姊妹校提名至 2026/11/01 17:00 止（赴國際姊妹校已於 2026/09/22 12:00 截止）",
            exact_deadline_at=_dt(2026, 11, 1, 17, 0),
            submission_mode="online",
            source_title="元智大學全球事務處—115-2 赴大陸地區姊妹校交換生甄選簡章",
            source_url="https://gao.yzu.edu.tw/index.php/tw/2016-03-04-08-13-53/2019-07-04-06-31-37",
            last_checked_at="2026-10-17",
        ),
        "paper_deadline": VerifiedRuleFact(
            rule_key="paper_deadline",
            label="紙本繳件截止日／送件規定",
            value_text="須繳交紙本申請表、家長同意書、切結書、中文歷年成績單與讀書計畫至全球事務處（赴陸校內收件至 2026/10/20；錄取生須繳交 NT$5,000 保證金）",
            exact_deadline_at=None,
            submission_mode="paper_required",
            source_title="元智大學出國交換第一階段校內甄選與第二階段姊妹校送件文件規範",
            source_url="https://gao.yzu.edu.tw/index.php/tw/2016-03-04-08-13-53/2016-03-07-08-52-41",
            last_checked_at="2026-10-17",
        ),
        "study_plan_limit": VerifiedRuleFact(
            rule_key="study_plan_limit",
            label="讀書計畫字數／頁數上限",
            value_text="赴大陸地區須含 500 字以上中文讀書計畫；赴國際姊妹校須繳中、英文讀書計畫（官方未設字數上限；返國後 2 週內須繳 1,500 字以上心得報告與 6 張照片）",
            min_chars=500,
            source_title="元智大學出國交換應繳文件規範與保證金退還規定",
            source_url="https://gao.yzu.edu.tw/index.php/tw/2016-03-04-08-13-53/2016-03-07-08-52-41",
            last_checked_at="2026-10-17",
        ),
        "extra_milestones": [
            (
                "yzu-subtask-nomination",
                "[元智交換] 115-2 赴大陸姊妹校交換提名截止（17:00）",
                "2026-11-01",
                "提名截止日",
                "home",
                "元智大學 115-2 赴大陸地區姊妹校交換提名與二階資料確認截止（2026/11/01 17:00）",
                "https://gao.yzu.edu.tw/index.php/tw/2016-03-04-08-13-53/2019-07-04-06-31-37",
            )
        ],
    },
    {
        "school_id": "ntpu",
        "in_ten_week_window": True,
        "window_status": "open",
        "window_badge": "10 週窗口進行中 · 10/23 17:00 截止",
        "cycle_label": "116 學年度（2027 秋／2028 春）校級赴外交換學生甄選",
        "primary_deadline_date": "2026-10-23",
        "primary_deadline_at": _dt(2026, 10, 23, 17, 0),
        "anchor_date": date(2026, 10, 23),
        "online_deadline": VerifiedRuleFact(
            rule_key="online_deadline",
            label="校內線上報名截止日",
            value_text="線上申請與文件上傳至 2026/10/23（五）17:00 止（逾時系統關閉不受理；2026/11/04 公告面試名單、11/11 舉行面試）",
            exact_deadline_at=_dt(2026, 10, 23, 17, 0),
            submission_mode="online",
            source_title="國立臺北大學國際事務處—116 學年度赴外交換學生甄選公告",
            source_url="https://new.ntpu.edu.tw/oia/news/6ab396bf7085cb4f0c81831f",
            last_checked_at="2026-10-03",
        ),
        "paper_deadline": VerifiedRuleFact(
            rule_key="paper_deadline",
            label="紙本繳件截止日／送件規定",
            value_text="免繳實體紙本至國際處；惟須列印系統產出之申請表完成本人親簽與系所核章後，於 2026/10/23（五）17:00 前掃描上傳至申請系統",
            exact_deadline_at=_dt(2026, 10, 23, 17, 0),
            submission_mode="signed_scan_upload",
            source_title="國立臺北大學 116 學年度赴外交換學生甄選簡章 PDF",
            source_url="https://cms-carrier.ntpu.edu.tw/uploads/116_16e535159d.pdf",
            last_checked_at="2026-10-03",
        ),
        "study_plan_limit": VerifiedRuleFact(
            rule_key="study_plan_limit",
            label="讀書計畫字數／頁數上限",
            value_text="出國學習計畫書以 A4 紙直式橫書，合計 5,000 字以內，格式自訂（英文組繳英文、日文組繳日文、中文組繳中文計畫書）",
            max_chars=5000,
            source_title="國立臺北大學 116 學年度赴外交換學生甄選簡章（申請步驟及應繳文件）",
            source_url="https://cms-carrier.ntpu.edu.tw/uploads/116_16e535159d.pdf",
            last_checked_at="2026-10-03",
        ),
    },
    {
        "school_id": "nchu",
        "in_ten_week_window": True,
        "window_status": "open",
        "window_badge": "10 週窗口進行中 · 10/23 12:00 截止",
        "cycle_label": "116 學年度第 1 學期（2027 秋季班）出國暨赴大陸交換學生甄選",
        "primary_deadline_date": "2026-10-23",
        "primary_deadline_at": _dt(2026, 10, 23, 12, 0),
        "anchor_date": date(2026, 10, 23),
        "online_deadline": VerifiedRuleFact(
            rule_key="online_deadline",
            label="校內線上報名截止日",
            value_text="學生線上申請至 2026/10/23（五）12:00（中午）止；線上教師推薦函至 2026/10/30（五）12:00 止；退補件至 2026/11/06（五）23:59 止",
            exact_deadline_at=_dt(2026, 10, 23, 12, 0),
            submission_mode="online",
            source_title="國立中興大學 2027 秋季班（116-1）出國交換學生甄選簡章 PDF",
            source_url="https://oia.nchu.edu.tw/images/File/02_Exchange_Program/5-1-1/Exchange_Program_Guidelines_for_Fall_Semester_2027_TW.pdf",
            last_checked_at="2026-10-18",
        ),
        "paper_deadline": VerifiedRuleFact(
            rule_key="paper_deadline",
            label="紙本繳件截止日／送件規定",
            value_text="採出國計畫線上申請系統（oiawp.nchu.edu.tw）全線上送件，免繳紙本至國際處；惟須由所屬系所於 2026/10/23（五）17:00 前完成線上資格審查與推薦",
            exact_deadline_at=_dt(2026, 10, 23, 17, 0),
            submission_mode="paperless",
            source_title="國立中興大學 2027 秋季班（116-1）出國交換學生甄選簡章 PDF",
            source_url="https://oia.nchu.edu.tw/images/File/02_Exchange_Program/5-1-1/Exchange_Program_Guidelines_for_Fall_Semester_2027_TW.pdf",
            last_checked_at="2026-10-18",
        ),
        "study_plan_limit": VerifiedRuleFact(
            rule_key="study_plan_limit",
            label="讀書計畫字數／頁數上限",
            value_text="《自傳及讀書計畫》格式不拘，至多 A4 大小三面（以第一志願為目標；填海外學校者須繳英文版，僅申請大陸者中英文皆可；獎學金研修計畫書建議中文 1,000–1,500 字、單檔 2MB 內）",
            max_pages=3,
            source_title="國立中興大學 2027 秋季班出國交換學生甄選簡章與獎學金申請說明",
            source_url="https://oia.nchu.edu.tw/images/File/02_Exchange_Program/5-1-1/Exchange_Program_Guidelines_for_Fall_Semester_2027_TW.pdf",
            last_checked_at="2026-10-18",
        ),
        "extra_milestones": [
            (
                "nchu-subtask-recommendation",
                "[中興交換] 線上教師推薦函上傳截止（12:00 中午）",
                "2026-10-30",
                "推薦函截止",
                "documents",
                "指導教授或授課教師須於 2026/10/30 12:00 前透過系統連結完成線上推薦函上傳",
                "https://oia.nchu.edu.tw/images/File/02_Exchange_Program/5-1-1/Exchange_Program_Guidelines_for_Fall_Semester_2027_TW.pdf",
            ),
            (
                "nchu-subtask-supplement",
                "[中興交換] 初審退補件最後截止日（23:59）",
                "2026-11-06",
                "補件截止",
                "documents",
                "接獲國際處退補件通知者，須於 2026/11/06 23:59 前於系統完成補件",
                "https://oia.nchu.edu.tw/images/File/02_Exchange_Program/5-1-1/Exchange_Program_Guidelines_for_Fall_Semester_2027_TW.pdf",
            ),
        ],
    },
    {
        "school_id": "wzu",
        "in_ten_week_window": True,
        "window_status": "open",
        "window_badge": "10 週窗口進行中 · 10/19–10/23 面試・10/30 志願分發",
        "cycle_label": "115-2（2027 春季出國）出國暨赴大陸交換甄試（二招面試與線上志願分發）",
        "primary_deadline_date": "2026-10-30",
        "primary_deadline_at": None,
        "anchor_date": date(2026, 10, 30),
        "online_deadline": VerifiedRuleFact(
            rule_key="online_deadline",
            label="校內線上報名截止日",
            value_text="115-2 二招外語面試為 2026/10/19–10/23，線上志願分發為 2026/10/27–10/30（官方未公告分發截止時刻；116-1 秋季出國一招預計 2027/02/22–03/02 15:00 收件）",
            exact_deadline_at=None,
            submission_mode="online",
            source_title="文藻外語大學國際暨兩岸合作處—115-2 出國暨赴大陸交換學生二招甄試簡章",
            source_url="https://d020.wzu.edu.tw/article/529354",
            last_checked_at="2026-10-19",
        ),
        "paper_deadline": VerifiedRuleFact(
            rule_key="paper_deadline",
            label="紙本繳件截止日／送件規定",
            value_text="校務資訊系統線上申請後須列印紙本（經系主任核章、附家長同意書及六大必繳文件）於截止日 15:00 前送交國合處（115-2 二招紙本已於 2026/10/13 15:00 截止；分發錄取後須繳交確認書與 NT$10,000 保證金）",
            exact_deadline_at=_dt(2026, 10, 13, 15, 0),
            submission_mode="paper_required",
            source_title="文藻外語大學出國暨赴大陸交換學生校內甄試簡章與應繳文件專區",
            source_url="https://d020.wzu.edu.tw/category/152182",
            last_checked_at="2026-10-19",
        ),
        "study_plan_limit": VerifiedRuleFact(
            rule_key="study_plan_limit",
            label="讀書計畫字數／頁數上限",
            value_text="須繳交中文讀書計畫（含留學動機，約 1,000 字）與外文讀書計畫（以第一志願語組撰寫，約 1,000 字）各乙份；返國後 1 個月內須繳約 1,000 字研修心得報告",
            min_chars=1000,
            source_title="文藻外語大學 115-2 出國暨赴大陸地區交換學生校內甄試簡章",
            source_url="https://d020.wzu.edu.tw/article/529354",
            last_checked_at="2026-10-19",
        ),
    },
    {
        "school_id": "pccu",
        "in_ten_week_window": True,
        "window_status": "open",
        "window_badge": "10 週窗口進行中 · 國合處 10/30・日文系 11/27 截止",
        "cycle_label": "115/116 學年度國合處赴外暨赴陸交換（10/30 截止）＆日文系赴日交換（11/16–11/27）",
        "primary_deadline_date": "2026-10-30",
        "primary_deadline_at": _dt(2026, 10, 30, 16, 30),
        "anchor_date": date(2026, 10, 30),
        "online_deadline": VerifiedRuleFact(
            rule_key="online_deadline",
            label="校內線上報名截止日",
            value_text="國合處秋季梯次申請收件至 2026/10/30（五）16:30 止；日本語文學系一階報名為 2026/11/16（一）至 2026/11/27（五）16:00 止",
            exact_deadline_at=_dt(2026, 10, 30, 16, 30),
            submission_mode="online",
            source_title="中國文化大學國際暨兩岸事務處—赴國外暨大陸地區姊妹校交換學生申請簡章 PDF",
            source_url="https://oima.pccu.edu.tw/Upload/202607/learning_2026071112283508.pdf",
            last_checked_at="2026-10-19",
        ),
        "paper_deadline": VerifiedRuleFact(
            rule_key="paper_deadline",
            label="紙本繳件截止日／送件規定",
            value_text="紙本申請表與六大應繳文件須先經系所主任核章推薦後，於 2026/10/30（五）16:30 前送達國合處菲華樓 202 室（日文系赴日交換紙本於 2026/11/27 16:00 前送交日文系辦）",
            exact_deadline_at=_dt(2026, 10, 30, 16, 30),
            submission_mode="paper_required",
            source_title="中國文化大學日本語文學系赴日本短期交換留學生甄選公告與國合處簡章",
            source_url="https://japanese.pccu.edu.tw/p/406-1109-140489,r278.php?Lang=zh-tw",
            last_checked_at="2026-10-19",
        ),
        "study_plan_limit": VerifiedRuleFact(
            rule_key="study_plan_limit",
            label="讀書計畫字數／頁數上限",
            value_text="須繳交中、外文讀書計畫（Study Plan）與中、外文自傳（Autobiography）各乙份，每份各約 1,000 字（交換期間每學期至少須修讀 6 學分或 2 門以上課程）",
            min_chars=1000,
            source_title="中國文化大學出國交換生申請簡章（應繳文件與修課規定）PDF",
            source_url="https://oima.pccu.edu.tw/Upload/202607/learning_2026071112283509.pdf",
            last_checked_at="2026-10-19",
        ),
        "extra_milestones": [
            (
                "pccu-subtask-japanese-dept",
                "[文大交換] 日文系赴日本交換留學生一階收件截止（16:00）",
                "2026-11-27",
                "日文系截止",
                "home",
                "文大日本語文學系赴日本姊妹校交換留學生第一階段報名與系辦收件至 2026/11/27 16:00 止",
                "https://japanese.pccu.edu.tw/p/406-1109-140489,r278.php?Lang=zh-tw",
            )
        ],
    },
    {
        "school_id": "nccu",
        "in_ten_week_window": True,
        "window_status": "open",
        "window_badge": "10 週窗口進行中 · 國際組語檢 11/02・大陸組 11/06 截止",
        "cycle_label": "115-1 校級國際薦外交換（語檢上傳至 11/02 16:00）＆薦外大陸交換甄試（11/05–11/06 17:00）",
        "primary_deadline_date": "2026-11-02",
        "primary_deadline_at": _dt(2026, 11, 2, 16, 0),
        "anchor_date": date(2026, 11, 2),
        "online_deadline": VerifiedRuleFact(
            rule_key="online_deadline",
            label="校內線上報名截止日",
            value_text="校級國際薦外交換：外語檢定成績上傳至 2026/11/02（一）16:00 止、志願選填 11/10–12/08 16:00；校級赴大陸交換：線上報名 2026/11/05–11/06（五）17:00 止",
            exact_deadline_at=_dt(2026, 11, 2, 16, 0),
            submission_mode="online",
            source_title="國立政治大學 115-1 校級國際薦外交換生甄試簡章 PDF",
            source_url="https://outbound.nccu.edu.tw/media/files/f353edca-d805-48ac-a6c9-9f66cf925c9e",
            last_checked_at="2026-10-18",
        ),
        "paper_deadline": VerifiedRuleFact(
            rule_key="paper_deadline",
            label="紙本繳件截止日／送件規定",
            value_text="赴大陸地區交換須於 2026/11/06（五）17:00 前將紙本申請表與備審資料親送或委託送達國合處大陸事務組（逾時不受理）；國際薦外交換初審採全線上送件免交紙本",
            exact_deadline_at=_dt(2026, 11, 6, 17, 0),
            submission_mode="paper_required",
            source_title="國立政治大學 115-1 校級薦外大陸交換生甄試簡章 PDF",
            source_url="https://oic.nccu.edu.tw/Home/Download?FileId=AC94A5C6-1ED6-421D-AD29-F673F2418670",
            last_checked_at="2026-10-18",
        ),
        "study_plan_limit": VerifiedRuleFact(
            rule_key="study_plan_limit",
            label="讀書計畫字數／頁數上限",
            value_text="國際薦外：交換計畫書與履歷表分為 2 份，電腦繕打 A4 直式橫書，每份各至少 500 字、以 2 頁為限（超出 2 頁不予計分）；赴大陸交換：自傳 1,000 字以內、研究／學習計畫 3,000 字以內（超字數不受理）",
            min_chars=500,
            max_chars=3000,
            max_pages=2,
            source_title="國立政治大學 115-1 校級國際薦外交換生甄試簡章與赴大陸交換生甄試簡章",
            source_url="https://outbound.nccu.edu.tw/media/files/f353edca-d805-48ac-a6c9-9f66cf925c9e",
            last_checked_at="2026-10-18",
        ),
        "extra_milestones": [
            (
                "nccu-subtask-mainland-paper",
                "[政大交換] 校級赴大陸交換線上報名暨紙本送件截止（17:00）",
                "2026-11-06",
                "赴陸截止日",
                "home",
                "政大 115-1 校級薦外大陸交換生線上報名與國合處紙本收件於 2026/11/06 17:00 截止",
                "https://oic.nccu.edu.tw/Home/Download?FileId=AC94A5C6-1ED6-421D-AD29-F673F2418670",
            )
        ],
    },
    {
        "school_id": "ntu",
        "in_ten_week_window": True,
        "window_status": "upcoming",
        "window_badge": "10 週窗口即將開放 · 11/03 10:00–11/09 16:00",
        "cycle_label": "116 學年度第 1 學期（2027 秋／2028 春）校級出國交換學生甄選",
        "primary_deadline_date": "2026-11-09",
        "primary_deadline_at": _dt(2026, 11, 9, 16, 0),
        "anchor_date": date(2026, 11, 9),
        "online_deadline": VerifiedRuleFact(
            rule_key="online_deadline",
            label="校內線上報名截止日",
            value_text="2026/11/03（二）10:00 至 2026/11/09（一）16:00 止完成線上報名、繳交報名費 NT$1,000 與文件上傳；文件初審退補件至 2026/11/12（四）16:00 止",
            exact_deadline_at=_dt(2026, 11, 9, 16, 0),
            submission_mode="online",
            source_title="國立臺灣大學 116 學年度第 1 學期校級出國交換學生甄選簡章 PDF",
            source_url="https://studyabroad.ntu.edu.tw/wp-content/uploads/2026/07/116-1-Selection-Guidelines_CH.pdf",
            last_checked_at="2026-10-07",
        ),
        "paper_deadline": VerifiedRuleFact(
            rule_key="paper_deadline",
            label="紙本繳件截止日／送件規定",
            value_text="校內甄選採全線上上傳 PDF 電子檔，免繳交紙本文件至國際事務處（惟須於 2026/11/09 16:00 前完成線上確認送出與報名費入帳）",
            exact_deadline_at=_dt(2026, 11, 9, 16, 0),
            submission_mode="paperless",
            source_title="國立臺灣大學 116 學年度第 1 學期校級出國交換學生甄選簡章 PDF",
            source_url="https://studyabroad.ntu.edu.tw/wp-content/uploads/2026/07/116-1-Selection-Guidelines_CH.pdf",
            last_checked_at="2026-10-07",
        ),
        "study_plan_limit": VerifiedRuleFact(
            rule_key="study_plan_limit",
            label="讀書計畫字數／頁數上限",
            value_text="出國交換計畫書：A4 兩面，至少 500 字，中文或英文撰寫；履歷表另備：A4 兩面，中文或英文，無標準格式",
            min_chars=500,
            max_pages=2,
            source_title="國立臺灣大學 116 學年度第 1 學期校級出國交換學生甄選簡章（應繳文件）",
            source_url="https://studyabroad.ntu.edu.tw/wp-content/uploads/2026/07/116-1-Selection-Guidelines_CH.pdf",
            last_checked_at="2026-10-07",
        ),
    },
    {
        "school_id": "nthu",
        "in_ten_week_window": True,
        "window_status": "upcoming",
        "window_badge": "10 週窗口即將開放 · 11/03–11/10 16:00 二階志願",
        "cycle_label": "2027 秋／2028 春校級交換二階線上志願選填（11/03–11/10 16:00）＆ 116 台聯大 UST 交換",
        "primary_deadline_date": "2026-11-10",
        "primary_deadline_at": _dt(2026, 11, 10, 16, 0),
        "anchor_date": date(2026, 11, 10),
        "online_deadline": VerifiedRuleFact(
            rule_key="online_deadline",
            label="校內線上報名截止日",
            value_text="2027 秋／2028 春第一梯次二階線上志願選填：2026/11/03（二）至 2026/11/10（二）16:00 止（錄取報到至 2026/12/11 16:00；另 116 台聯大 UST 交換收件至 2027/01/04 16:00 止）",
            exact_deadline_at=_dt(2026, 11, 10, 16, 0),
            submission_mode="online",
            source_title="國立清華大學 2027 秋／2028 春（116 學年度）出國交換生甄選簡章 PDF",
            source_url="https://oga.site.nthu.edu.tw/var/file/524/1524/img/2027F2028Sapplicationguideline-CH.pdf",
            last_checked_at="2026-10-19",
        ),
        "paper_deadline": VerifiedRuleFact(
            rule_key="paper_deadline",
            label="紙本繳件截止日／送件規定",
            value_text="初審採線上系統上傳經系所核章之申請表與 7 項必繳文件；錄取生須於 2026/12/11（五）16:00 前繳交錄取確認書與 NT$8,000 保證金至全球事務處（台聯大 UST 交換於 2027/01/04 16:00 前送件）",
            exact_deadline_at=_dt(2026, 12, 11, 16, 0),
            submission_mode="signed_scan_upload",
            source_title="國立清華大學全球事務處—出國交換申請文件與保證金規定 PDF",
            source_url="https://oga.site.nthu.edu.tw/var/file/524/1524/img/4536/966105147.pdf",
            last_checked_at="2026-10-19",
        ),
        "study_plan_limit": VerifiedRuleFact(
            rule_key="study_plan_limit",
            label="讀書計畫字數／頁數上限",
            value_text="須同時繳交「中文及外文（英文或交換國語言）」之讀書計畫與自傳，並具體列出擬於目標姊妹校修讀之課程規劃列表（官方簡章未設固定字數上限）",
            source_title="國立清華大學 2027 秋／2028 春出國交換生甄選簡章 PDF",
            source_url="https://oga.site.nthu.edu.tw/var/file/524/1524/img/2027F2028Sapplicationguideline-CH.pdf",
            last_checked_at="2026-10-19",
        ),
    },
    {
        "school_id": "ntnu",
        "in_ten_week_window": True,
        "window_status": "upcoming",
        "window_badge": "10 週窗口即將開放 · 11/01–11/15 23:59:59",
        "cycle_label": "116 學年度第 1 學期（2027 秋季班）校級赴外交換生甄選",
        "primary_deadline_date": "2026-11-15",
        "primary_deadline_at": _dt(2026, 11, 15, 23, 59, 59),
        "anchor_date": date(2026, 11, 15),
        "online_deadline": VerifiedRuleFact(
            rule_key="online_deadline",
            label="校內線上報名截止日",
            value_text="線上申請 2026/11/01 至 2026/11/15（日）23:59:59 止；補件與繳交報名費收據至 2026/11/16（一）23:59:59 止（運動與休閒學院院級交換至 2026/12/18 17:00 止）",
            exact_deadline_at=_dt(2026, 11, 15, 23, 59, 59),
            submission_mode="online",
            source_title="國立臺灣師範大學 116-1 赴外交換生甄選簡章 PDF",
            source_url="https://bds.oia.ntnu.edu.tw/api/v1/pt/dl?f=/pt/contents/2014100104/doc_OE116-1%20SPRING2027-1013.pdf",
            last_checked_at="2026-10-16",
        ),
        "paper_deadline": VerifiedRuleFact(
            rule_key="paper_deadline",
            label="紙本繳件截止日／送件規定",
            value_text="校內初審採臺師大赴外交換生系統全線上上傳電子備審文件與報名費繳費證明，免繳交紙本至國際事務處",
            exact_deadline_at=_dt(2026, 11, 16, 23, 59, 59),
            submission_mode="paperless",
            source_title="國立臺灣師範大學國際事務處—赴外交換生系統申請規範",
            source_url="https://bds.oia.ntnu.edu.tw/bds/web/outgoing-apply",
            last_checked_at="2026-10-16",
        ),
        "study_plan_limit": VerifiedRuleFact(
            rule_key="study_plan_limit",
            label="讀書計畫字數／頁數上限",
            value_text="自傳與出國學習計畫（占甄選評分 20%）：格式不限，中英文合計須介於 500 至 5,000 字之間；建議另附外文版本約 500 至 2,500 字",
            min_chars=500,
            max_chars=5000,
            source_title="國立臺灣師範大學赴外交換生系統應備文件規範",
            source_url="https://bds.oia.ntnu.edu.tw/bds/web/outgoing-apply",
            last_checked_at="2026-10-16",
        ),
    },
    {
        "school_id": "scu",
        "in_ten_week_window": True,
        "window_status": "open",
        "window_badge": "10 週窗口進行中 · 11/16 12:00（中午）截止",
        "cycle_label": "116 學年度校級赴境外（國外／大陸／港澳）交換暨自費研修甄選",
        "primary_deadline_date": "2026-11-16",
        "primary_deadline_at": _dt(2026, 11, 16, 12, 0),
        "anchor_date": date(2026, 11, 16),
        "online_deadline": VerifiedRuleFact(
            rule_key="online_deadline",
            label="校內線上報名截止日",
            value_text="線上申請與電子備審上傳至 2026/11/16（一）12:00（中午）止（逾時系統關閉不受理；預計 2026 年 12 月底公告錄取結果）",
            exact_deadline_at=_dt(2026, 11, 16, 12, 0),
            submission_mode="online",
            source_title="東吳大學國際及兩岸學術交流處—116 學年度赴境外交換申請專頁",
            source_url="https://icae.scu.edu.tw/zh-hant/outbound-exchange/itnl/AYapply",
            last_checked_at="2026-10-16",
        ),
        "paper_deadline": VerifiedRuleFact(
            rule_key="paper_deadline",
            label="紙本繳件截止日／送件規定",
            value_text="全面採線上申請系統上傳 PDF 電子檔（單一檔案上限 5MB），免繳交紙本文件至國際及兩岸學術交流處",
            exact_deadline_at=_dt(2026, 11, 16, 12, 0),
            submission_mode="paperless",
            source_title="東吳大學國際及兩岸學術交流處—線上申請系統備審文件規範",
            source_url="https://icae.scu.edu.tw/zh-hant/outbound-exchange/itnl/AYapply",
            last_checked_at="2026-10-16",
        ),
        "study_plan_limit": VerifiedRuleFact(
            rule_key="study_plan_limit",
            label="讀書計畫字數／頁數上限",
            value_text="自傳或履歷 1 份約 2,000 字；交換研修動機及讀書計畫一校一份，各約 2,000 字以內（赴外須同時撰寫中文 Form A 與外文 Form B 合併為單一 PDF 上限 5MB；返國報告 1,500–2,000 字）",
            max_chars=2000,
            source_title="東吳大學國際及兩岸學術交流處—線上申請系統備審文件規範",
            source_url="https://icae.scu.edu.tw/zh-hant/outbound-exchange/itnl/AYapply",
            last_checked_at="2026-10-16",
        ),
    },
    {
        "school_id": "nsysu",
        "in_ten_week_window": True,
        "window_status": "upcoming",
        "window_badge": "10 週窗口即將開放 · 11/03 09:00–11/17 17:00",
        "cycle_label": "第 55 屆（2027–2028）赴其他國家與地區學生出國交換計畫（第一次甄選）",
        "primary_deadline_date": "2026-11-17",
        "primary_deadline_at": _dt(2026, 11, 17, 17, 0),
        "anchor_date": date(2026, 11, 17),
        "online_deadline": VerifiedRuleFact(
            rule_key="online_deadline",
            label="校內線上報名截止日",
            value_text="2026/11/03（二）09:00 至 2026/11/17（二）17:00 止於出國交換甄選系統（partners.oia.nsysu.edu.tw）完成線上申請與上傳；補正至 2026/11/20 17:00 止（赴中國第一次甄選另於 2027/01/12–01/26 17:00 受理）",
            exact_deadline_at=_dt(2026, 11, 17, 17, 0),
            submission_mode="online",
            source_title="國立中山大學國際事務處—第 55 屆出國交換學生甄選簡章專頁",
            source_url="https://oia.nsysu.edu.tw/p/412-1308-20730.php?Lang=zh-tw",
            last_checked_at="2026-10-18",
        ),
        "paper_deadline": VerifiedRuleFact(
            rule_key="paper_deadline",
            label="紙本繳件截止日／送件規定",
            value_text="採線上甄選系統上傳 PDF 備審文件，免繳紙本至國際處；惟申請表須先經系所主管核章後掃描上傳，且報名費 NT$1,000 須於 2026/11/17 17:00 前完成繳納",
            exact_deadline_at=_dt(2026, 11, 17, 17, 0),
            submission_mode="signed_scan_upload",
            source_title="國立中山大學國際事務處—第 55 屆出國交換學生甄選簡章專頁",
            source_url="https://oia.nsysu.edu.tw/p/412-1308-20730.php?Lang=zh-tw",
            last_checked_at="2026-10-18",
        ),
        "study_plan_limit": VerifiedRuleFact(
            rule_key="study_plan_limit",
            label="讀書計畫字數／頁數上限",
            value_text="須下載國際處「研修計畫書空白表格」填寫（占總分 20%）：赴其他國家須含中、英文各以 1 頁 A4 為限；赴日本須含中、日文各 1 頁 A4；赴中國以中文 1–2 頁 A4 撰寫（返國報告中文 1,500–2,000 字＋英文 1,000–1,500 字）",
            max_pages=2,
            source_title="國立中山大學第 55 屆出國交換學生甄選簡章（應繳文件與計分）",
            source_url="https://oia.nsysu.edu.tw/p/412-1308-20730.php?Lang=zh-tw",
            last_checked_at="2026-10-18",
        ),
    },
    {
        "school_id": "ncku",
        "in_ten_week_window": True,
        "window_status": "upcoming",
        "window_badge": "10 週窗口即將開放 · 10/30 09:00–11/19 16:00",
        "cycle_label": "116 學年度第 1 學期（2027 秋季班）校級薦外交換學生計畫甄選",
        "primary_deadline_date": "2026-11-19",
        "primary_deadline_at": _dt(2026, 11, 19, 16, 0),
        "anchor_date": date(2026, 11, 19),
        "online_deadline": VerifiedRuleFact(
            rule_key="online_deadline",
            label="校內線上報名截止日",
            value_text="2026/10/30（五）09:00 至 2026/11/19（四）16:00 止於成大國際處線上系統完成報名、繳交報名費 NT$1,000 及上傳單一 PDF（跨國雙向研修獎助學金另於 2026/10/31 17:00 截止）",
            exact_deadline_at=_dt(2026, 11, 19, 16, 0),
            submission_mode="online",
            source_title="國立成功大學 116 學年第 1 學期校級薦外交換學生計畫簡章 PDF",
            source_url="https://oia.ncku.edu.tw/var/file/32/1032/img/107138261.pdf",
            last_checked_at="2026-10-18",
        ),
        "paper_deadline": VerifiedRuleFact(
            rule_key="paper_deadline",
            label="紙本繳件截止日／送件規定",
            value_text="免繳交紙本文件至國際事務處；惟線上產出之申請表須先經系所核章，並與志願表、成績單、語檢、中英文讀書計畫及自傳依序合併為單一 PDF（上限 50MB）於 2026/11/19 16:00 前上傳",
            exact_deadline_at=_dt(2026, 11, 19, 16, 0),
            submission_mode="signed_scan_upload",
            source_title="國立成功大學 116 學年第 1 學期校級薦外交換學生計畫簡章 PDF",
            source_url="https://oia.ncku.edu.tw/var/file/32/1032/img/107138261.pdf",
            last_checked_at="2026-10-18",
        ),
        "study_plan_limit": VerifiedRuleFact(
            rule_key="study_plan_limit",
            label="讀書計畫字數／頁數上限",
            value_text="須就「第一志願」學校分別擬訂中文及英文讀書或研究計畫（占總成績 25%）與中英文自傳（占 25%）；官方簡章未設固定字數或頁數上限，全數文件合併單一 PDF 上限 50MB",
            source_title="國立成功大學 116 學年第 1 學期校級薦外交換學生計畫簡章（申請資料與審查方式）",
            source_url="https://oia.ncku.edu.tw/var/file/32/1032/img/107138261.pdf",
            last_checked_at="2026-10-18",
        ),
    },
    {
        "school_id": "cycu",
        "in_ten_week_window": True,
        "window_status": "open",
        "window_badge": "10 週窗口進行中 · 11/20 17:00 赴陸交換截止",
        "cycle_label": "2027 春季班（115-2）赴大陸地區姊妹校交換申請（國際姊妹校二梯已於 09/25 截止）",
        "primary_deadline_date": "2026-11-20",
        "primary_deadline_at": _dt(2026, 11, 20, 17, 0),
        "anchor_date": date(2026, 11, 20),
        "online_deadline": VerifiedRuleFact(
            rule_key="online_deadline",
            label="校內線上報名截止日",
            value_text="赴大陸地區姊妹校交換申請與電子備審寄送至 2026/11/20（五）17:00 止（115-2 赴國際姊妹校第二梯次已於 2026/09/25 12:00 截止）",
            exact_deadline_at=_dt(2026, 11, 20, 17, 0),
            submission_mode="online",
            source_title="中原大學國際暨兩岸教育處—赴大陸地區姊妹校交換申請公告",
            source_url="https://oia.cycu.edu.tw/?p=6340",
            last_checked_at="2026-10-16",
        ),
        "paper_deadline": VerifiedRuleFact(
            rule_key="paper_deadline",
            label="紙本繳件截止日／送件規定",
            value_text="紙本申請表（須經系主任核章）及紙本備審資料須於 2026/11/20（五）17:00 前送交國際暨兩岸教育處（維澈樓 704 室），並同步依規定格式寄送電子檔",
            exact_deadline_at=_dt(2026, 11, 20, 17, 0),
            submission_mode="paper_required",
            source_title="中原大學出國交換甄選紙本與電子備審文件規範",
            source_url="https://oia.cycu.edu.tw/?p=6338",
            last_checked_at="2026-10-16",
        ),
        "study_plan_limit": VerifiedRuleFact(
            rule_key="study_plan_limit",
            label="讀書計畫字數／頁數上限",
            value_text="須繳交中、英文讀書計畫（Study Plan）與中、英文自傳（Autobiography），電子檔依國際處規定格式寄送；官方簡章未公布固定字數或頁數上限",
            source_title="中原大學出國交換甄選紙本與電子備審文件規範",
            source_url="https://oia.cycu.edu.tw/?p=6338",
            last_checked_at="2026-10-16",
        ),
    },
    {
        "school_id": "ncu",
        "in_ten_week_window": True,
        "window_status": "upcoming",
        "window_badge": "10 週窗口即將開放 · 線上 12/04 12:00・紙本 12/11 17:00",
        "cycle_label": "116 學年度第 1 梯次（赴 116-1／116-2）校級出國交換學生甄選",
        "primary_deadline_date": "2026-12-04",
        "primary_deadline_at": _dt(2026, 12, 4, 12, 0),
        "anchor_date": date(2026, 12, 4),
        "online_deadline": VerifiedRuleFact(
            rule_key="online_deadline",
            label="校內線上報名截止日",
            value_text="2026/11/16（一）09:00 至 2026/12/04（五）12:00（中午）止於新版國際處出國交換申請系統完成線上報名",
            exact_deadline_at=_dt(2026, 12, 4, 12, 0),
            submission_mode="online",
            source_title="國立中央大學 116 學年度第 1 梯次交換學生甄選簡章 PDF",
            source_url="https://oia.ncu.edu.tw/static/file/26/1026/img/277/116exchangenotice.pdf",
            last_checked_at="2026-10-15",
        ),
        "paper_deadline": VerifiedRuleFact(
            rule_key="paper_deadline",
            label="紙本繳件截止日／送件規定",
            value_text="學生須於 2026/12/11（五）17:00 前將紙本申請資料繳交至所屬系所辦公室（各系所若有更早收件日依系辦公告為準）；系所彙整後於 2026/12/16 17:00 前送達國際處",
            exact_deadline_at=_dt(2026, 12, 11, 17, 0),
            submission_mode="paper_required",
            source_title="國立中央大學 116 學年度第 1 梯次交換學生甄選簡章 PDF",
            source_url="https://oia.ncu.edu.tw/static/file/26/1026/img/277/116exchangenotice.pdf",
            last_checked_at="2026-10-15",
        ),
        "study_plan_limit": VerifiedRuleFact(
            rule_key="study_plan_limit",
            label="讀書計畫字數／頁數上限",
            value_text="校內必繳「讀書計畫」與「自傳」官方簡章未規定字數或頁數上限（返校手續時繳交之交換心得報告規定「至少 800-1500 字」並附至少 4 張照片）",
            source_title="國立中央大學 116 學年度第 1 梯次交換學生甄選簡章 PDF",
            source_url="https://oia.ncu.edu.tw/static/file/26/1026/img/277/116exchangenotice.pdf",
            last_checked_at="2026-10-15",
        ),
        "extra_milestones": [
            (
                "ncu-subtask-paper-dept",
                "[中央交換] 學生紙本申請資料繳交至所屬系所辦公室截止（17:00）",
                "2026-12-11",
                "系所紙本截止",
                "home",
                "中央 116-1 線上報名（12/04 12:00 截止）後，學生須於 2026/12/11 17:00 前將紙本資料送達所屬系辦",
                "https://oia.ncu.edu.tw/static/file/26/1026/img/277/116exchangenotice.pdf",
            )
        ],
    },
    {
        "school_id": "ntut",
        "in_ten_week_window": True,
        "window_status": "upcoming",
        "window_badge": "10 週窗口即將開放 · 12/01 09:00–12/10 17:00",
        "cycle_label": "116 學年度第 1、2 學期（2027 秋／2028 春）赴外研修計畫校內甄選",
        "primary_deadline_date": "2026-12-10",
        "primary_deadline_at": _dt(2026, 12, 10, 17, 0),
        "anchor_date": date(2026, 12, 10),
        "online_deadline": VerifiedRuleFact(
            rule_key="online_deadline",
            label="校內線上報名截止日",
            value_text="2026/12/01（二）09:00 至 2026/12/10（四）17:00 止完成線上表單填報（雙聯學位留學獎學金秋季班另於 2026/11/01 17:00 截止）",
            exact_deadline_at=_dt(2026, 12, 10, 17, 0),
            submission_mode="online",
            source_title="國立臺北科技大學 116 學年度赴外研修計畫校內甄選簡章 PDF",
            source_url="https://oia.ntut.edu.tw/var/file/32/1032/img/2933/169590471.pdf",
            last_checked_at="2026-10-18",
        ),
        "paper_deadline": VerifiedRuleFact(
            rule_key="paper_deadline",
            label="紙本繳件截止日／送件規定",
            value_text="紙本申請表（須經系所主任及院長核章）與 9 項應繳文件須於 2026/12/01 09:00 至 2026/12/10（四）17:00 前送交國際事務處（逾期不予受理）",
            exact_deadline_at=_dt(2026, 12, 10, 17, 0),
            submission_mode="paper_required",
            source_title="國立臺北科技大學國際事務處「出國交換 STEP 1 校內甄選」規範",
            source_url="https://oia.ntut.edu.tw/p/412-1032-9238.php?Lang=zh-tw",
            last_checked_at="2026-10-18",
        ),
        "study_plan_limit": VerifiedRuleFact(
            rule_key="study_plan_limit",
            label="讀書計畫字數／頁數上限",
            value_text="校內甄選《研修計畫》格式不拘，限於 1 頁 A4 內簡述申請目的與預期效益（非大陸地區建議以英文撰寫；另申請學海惜珠者須加附中文 1–2 頁動機與 1,000–1,500 字研修計劃書；返國報告 2,000–3,000 字以上）",
            max_pages=1,
            source_title="國立臺北科技大學國際事務處「出國交換 STEP 1 校內甄選」規範",
            source_url="https://oia.ntut.edu.tw/p/412-1032-9238.php?Lang=zh-tw",
            last_checked_at="2026-10-18",
        ),
    },
    {
        "school_id": "nycu",
        "in_ten_week_window": True,
        "window_status": "open",
        "window_badge": "10 週窗口進行中 · UST 12/31 16:00・校級一梯 12/01–01/05",
        "cycle_label": "116 學年度台聯大 UST 交換（12/31 16:00 截止）＆校級出國交換第一梯次（12/01–01/05 17:00）",
        "primary_deadline_date": "2026-12-31",
        "primary_deadline_at": _dt(2026, 12, 31, 16, 0),
        "anchor_date": date(2026, 12, 31),
        "online_deadline": VerifiedRuleFact(
            rule_key="online_deadline",
            label="校內線上報名截止日",
            value_text="116 台聯大 UST 交換：收件至 2026/12/31（四）16:00 止；校級出國交換第一梯次：2026/12/01（二）09:00 至 2027/01/05（二）17:00 止於出國交換申請系統（oia-sys.nycu.edu.tw/outgoing）線上申請",
            exact_deadline_at=_dt(2026, 12, 31, 16, 0),
            submission_mode="online",
            source_title="國立陽明交通大學國際事務處—116 學年度台聯大交換公告與校級第一梯次簡章",
            source_url="https://oia.nycu.edu.tw/oia/ch/app/data/view?module=nycu0006&id=286&serno=8ee14cf9-321b-46af-9871-9d154c9e6647",
            last_checked_at="2026-10-19",
        ),
        "paper_deadline": VerifiedRuleFact(
            rule_key="paper_deadline",
            label="紙本繳件截止日／送件規定",
            value_text="116 台聯大 UST 交換須於 2026/12/31 16:00 前將申請資料送達國際處（劉小姐 ext. 50665）；校級出國交換採線上系統上傳五級核章《學生出國交換申請簽核表》（本人、家長、導師／指導教授、系主任、院長核章）與備審 PDF，免另交紙本",
            exact_deadline_at=_dt(2026, 12, 31, 16, 0),
            submission_mode="signed_scan_upload",
            source_title="國立陽明交通大學學生出國交換申請簽核表與第一梯次申請簡章 PDF",
            source_url="https://oia.nycu.edu.tw/oia/ch/app/data/doc?module=nycu0006&detailNo=1501852894419226624&type=s",
            last_checked_at="2026-10-19",
        ),
        "study_plan_limit": VerifiedRuleFact(
            rule_key="study_plan_limit",
            label="讀書計畫字數／頁數上限",
            value_text="須繳交中英文自傳（占 10%–25%）與中英文讀書計畫（占 15%–30%，同分參酌第二順位）；須具體規劃擬修讀之專業課程（大學部每學期至少 3 門、研究所至少 2 門且全數及格，否則沒收 NT$10,000 保證金；官方未設固定字數上限）",
            source_title="國立陽明交通大學出國交換計畫第一梯次申請簡章 PDF",
            source_url="https://oia.nycu.edu.tw/oia/ch/app/data/doc?module=nycu0006&detailNo=1442785684455690240&type=s",
            last_checked_at="2026-10-19",
        ),
        "extra_milestones": [
            (
                "nycu-subtask-round1-close",
                "[陽明交大交換] 校級出國交換第一梯次線上申請截止（17:00）",
                "2027-01-05",
                "校級一梯截止",
                "home",
                "陽明交大校級出國交換第一梯次線上申請與五級核章簽核表上傳於 2027/01/05 17:00 截止",
                "https://oia.nycu.edu.tw/oia/ch/app/data/doc?module=nycu0006&detailNo=1442785684455690240&type=s",
            )
        ],
    },
    {
        "school_id": "fju",
        "in_ten_week_window": True,
        "window_status": "upcoming",
        "window_badge": "10 週窗口即將開放 · 11/01–12/24 16:30（限校內網路）",
        "cycle_label": "116-1（2027 秋季班）校級赴姊妹校交換學生申請（系統開放及紙本收件 11/01–12/24 16:30；名額於 11 月陸續更新）",
        "primary_deadline_date": "2026-12-24",
        "primary_deadline_at": _dt(2026, 12, 24, 16, 30),
        "anchor_date": date(2026, 12, 24),
        "online_deadline": VerifiedRuleFact(
            rule_key="online_deadline",
            label="校內線上報名截止日",
            value_text="2026/11/01 至 2026/12/24（四）16:30 止（雖公告標題寫即日起，正文載明系統開放及收件為 11/1–12/24 16:30；線上系統 http://outgoing.oie.fju.edu.tw/ 限校內網路使用，名額及開放學校將於 11 月陸續更新，不能當成最終版）",
            exact_deadline_at=_dt(2026, 12, 24, 16, 30),
            submission_mode="online",
            source_title="天主教輔仁大學 116 學年度第 1 學期（2027 秋季班）赴姊妹校交換學生申請公告（newsID=1062）",
            source_url="https://iscoie.fju.edu.tw/newsDetail.jsp?newsID=1062&newsClassID=14",
            last_checked_at="2026-10-20",
        ),
        "paper_deadline": VerifiedRuleFact(
            rule_key="paper_deadline",
            label="紙本繳件截止日／送件規定",
            value_text="紙本僅須繳交「赴姐妹校交換生申請表（A4 雙面列印、電腦打字輸入）」，完成家長簽章與系所／院／雙主修輔系學程核章後，於 2026/11/01 至 2026/12/24（四）16:30 前送交耕莘樓 A113 室（其餘書審、成績單、語測證明均上傳 PDF 電子檔）",
            exact_deadline_at=_dt(2026, 12, 24, 16, 30),
            submission_mode="paper_required",
            source_title="天主教輔仁大學 116 學年度第 1 學期（2027 秋季班）赴姊妹校交換學生申請公告与申請表（newsID=1062、file=1345）",
            source_url="https://iscoie.fju.edu.tw/newsDetail.jsp?newsID=1062&newsClassID=14",
            last_checked_at="2026-10-20",
        ),
        "study_plan_limit": VerifiedRuleFact(
            rule_key="study_plan_limit",
            label="讀書計畫字數／頁數上限",
            value_text="116-1 書審資料（合併單一 PDF <=20MB 上傳）：中文讀書計畫（只需繳交一份中文版、不需繳交英文版，至少 500 字，格式不拘，兩頁為限）與中文簡歷（兩頁為限）；返國後 1 個月內繳交 2,000 字以上心得報告",
            min_chars=500,
            max_pages=2,
            source_title="天主教輔仁大學 116 學年度第 1 學期（2027 秋季班）赴姊妹校交換學生申請公告（newsID=1062）",
            source_url="https://iscoie.fju.edu.tw/newsDetail.jsp?newsID=1062&newsClassID=14",
            last_checked_at="2026-10-20",
        ),
    },
    {
        "school_id": "cgu",
        "in_ten_week_window": True,
        "window_status": "pending_exact_date",
        "window_badge": "10 週窗口預告（11/01–12/20・待當期公告確切時刻）",
        "cycle_label": "116-1（2027 秋季班）出國交換學生甄選（11/01–12/20 預告申請期間）",
        "primary_deadline_date": "2026-12-20",
        "primary_deadline_at": None,
        "anchor_date": date(2026, 12, 20),
        "online_deadline": VerifiedRuleFact(
            rule_key="online_deadline",
            label="校內線上報名截止日",
            value_text="國際處甄選流程頁預告秋季班交換於 11/01–12/20 開放申請；當期專屬公告與確切截止時刻尚未發布（絕不自行推定為 23:59，送件前請核對國際處最新公告）",
            exact_deadline_at=None,
            submission_mode="pending_notice",
            source_title="長庚大學國際事務處—交換學生甄選流程與時程說明",
            source_url="https://www.cgu.edu.tw/oia-ch/Contents?nodeId=15656",
            last_checked_at="2026-10-03",
        ),
        "paper_deadline": VerifiedRuleFact(
            rule_key="paper_deadline",
            label="紙本繳件截止日／送件規定",
            value_text="依長庚國際處當期交換甄選公告辦理（須完成申請表、系所與院長簽章及備審文件送件；確切紙本收件截止時刻待當期專屬公告確認）",
            exact_deadline_at=None,
            submission_mode="pending_notice",
            source_title="長庚大學國際事務處—交換學生甄選流程與作業要點",
            source_url="https://www.cgu.edu.tw/oia-ch/Contents?nodeId=15656",
            last_checked_at="2026-10-03",
        ),
        "study_plan_limit": VerifiedRuleFact(
            rule_key="study_plan_limit",
            label="讀書計畫字數／頁數上限",
            value_text="官方公開作業要點與甄選頁未設定全校統一之讀書計畫字數或頁數上限；請依當期甄選公告與目標合作校規定準備",
            source_title="長庚大學學生赴境外學校進修交流作業要點與甄選說明",
            source_url="https://www.cgu.edu.tw/oia-ch/Contents?nodeId=15656",
            last_checked_at="2026-10-03",
        ),
    },
    {
        "school_id": "fcu",
        "in_ten_week_window": True,
        "window_status": "pending_exact_date",
        "window_badge": "10 週窗口預告（11/16–11/20 說明會・12 月中旬公告簡章）",
        "cycle_label": "115-1 國際研習週說明會（11/16–11/20）＆ 115-2 選送學生出國研修（12 月中旬公告簡章）",
        "primary_deadline_date": "2026-12-15",
        "primary_deadline_at": None,
        "anchor_date": date(2026, 12, 15),
        "online_deadline": VerifiedRuleFact(
            rule_key="online_deadline",
            label="校內線上報名截止日",
            value_text="2026/11/16–11/20 舉辦國際研習週說明會，預計 2026 年 12 月中旬公告當期簡章、翌年 1 月中旬截止 oiasap 系統線上申請（確切截止日待 12 月中旬簡章公布）",
            exact_deadline_at=None,
            submission_mode="pending_notice",
            source_title="逢甲大學國際事務處「選送學生出國研修」介紹與申請時程",
            source_url="https://oia.fcu.edu.tw/sap/introduction/",
            last_checked_at="2026-10-17",
        ),
        "paper_deadline": VerifiedRuleFact(
            rule_key="paper_deadline",
            label="紙本繳件截止日／送件規定",
            value_text="採逢甲大學 oiasap 系統全線上無紙化申請，免繳交紙本文件至國際事務處（家長同意書簽名後掃描上傳即可）",
            exact_deadline_at=None,
            submission_mode="paperless",
            source_title="逢甲大學國際事務處「選送學生出國研修」無紙化申請規範",
            source_url="https://oia.fcu.edu.tw/sap/introduction/",
            last_checked_at="2026-10-17",
        ),
        "study_plan_limit": VerifiedRuleFact(
            rule_key="study_plan_limit",
            label="讀書計畫字數／頁數上限",
            value_text="研修計畫（簡章附件二）中文或英文均可，字數至少 1,000 字（含動機、修課規劃與預期效益；返國後 1 個月內繳交 2,000 字以上研習報告書）",
            min_chars=1000,
            source_title="逢甲大學國際事務處「選送學生出國研修」簡章附件說明",
            source_url="https://oia.fcu.edu.tw/sap/introduction/",
            last_checked_at="2026-10-17",
        ),
        "extra_milestones": [
            (
                "fcu-subtask-info-week",
                "[逢甲交換] 115-1 國際研習週出國交換說明會（11/16–11/20）",
                "2026-11-16",
                "說明會週",
                "home",
                "逢甲大學國際事務處於 2026/11/16–11/20 舉辦國際研習週說明會，說明 12 月中旬公告之選送簡章",
                "https://oia.fcu.edu.tw/sap/introduction/",
            )
        ],
    },
    {
        "school_id": "ccu",
        "in_ten_week_window": False,
        "window_status": "closed_current_round",
        "window_badge": "本期已於 09/21 截止 · 下期預計春季開放",
        "cycle_label": "2027 春季班（115-2）校級薦外交換（三梯次已於 09/21 截止；2027 秋季班待春季公告）",
        "primary_deadline_date": "2026-09-21",
        "primary_deadline_at": _dt(2026, 9, 21, 17, 0),
        "anchor_date": date(2026, 11, 30),
        "online_deadline": VerifiedRuleFact(
            rule_key="online_deadline",
            label="校內線上報名截止日",
            value_text="2027 春季班第 1–3 梯次線上申請已分別於 2026/08/26、09/06、09/20 23:59 截止；2027 秋季班新版簡章尚未公告",
            exact_deadline_at=_dt(2026, 9, 20, 23, 59),
            submission_mode="online",
            source_title="國立中正大學國際事務處—2027 春季校級薦外交換公告",
            source_url="https://oia.ccu.edu.tw/p/406-1008-93586,r1714.php?Lang=zh-tw",
            last_checked_at="2026-10-08",
        ),
        "paper_deadline": VerifiedRuleFact(
            rule_key="paper_deadline",
            label="紙本繳件截止日／送件規定",
            value_text="線上申請與紙本送件兩項均須完成（2027 春季班第 1–3 梯次紙本已分別於 2026/08/27、09/07、09/21 17:00 截止）",
            exact_deadline_at=_dt(2026, 9, 21, 17, 0),
            submission_mode="paper_required",
            source_title="國立中正大學 2027 春季出國交換甄選簡章 PDF",
            source_url="https://oia.ccu.edu.tw/var/file/8/1008/attach/78/pta_54384_797227_45763.pdf",
            last_checked_at="2026-10-08",
        ),
        "study_plan_limit": VerifiedRuleFact(
            rule_key="study_plan_limit",
            label="讀書計畫字數／頁數上限",
            value_text="研修計畫書每個志願一份，中文或英文皆可，須包含自傳、讀書計畫與申請動機，不限格式，每項約 A4 一頁",
            max_pages=3,
            source_title="國立中正大學 2027 春季出國交換甄選簡章（申請文件）",
            source_url="https://oia.ccu.edu.tw/var/file/8/1008/attach/78/pta_54384_797227_45763.pdf",
            last_checked_at="2026-10-08",
        ),
    },
    {
        "school_id": "tku",
        "in_ten_week_window": False,
        "window_status": "closed_current_round",
        "window_badge": "日語二甄已於 09/30 截止 · 其他語組待新版公告",
        "cycle_label": "2027–2028 年赴日本姊妹校（日語組）第二次聯合甄選（09/30 12:00 已截止；英歐／中文組新版待查核）",
        "primary_deadline_date": "2026-09-30",
        "primary_deadline_at": _dt(2026, 9, 30, 12, 0),
        "anchor_date": date(2026, 11, 30),
        "online_deadline": VerifiedRuleFact(
            rule_key="online_deadline",
            label="校內線上報名截止日",
            value_text="2027–2028 日語組第二次聯合甄選已於 2026/09/30 12:00 截止；2027–2028 英歐語組與赴大陸／港澳交換新版簡章尚未發布",
            exact_deadline_at=_dt(2026, 9, 30, 12, 0),
            submission_mode="online",
            source_title="淡江大學國際暨兩岸事務處—最新交換生計畫公告列表",
            source_url="https://oieie.tku.edu.tw/oieie/?page_id=55",
            last_checked_at="2026-10-08",
        ),
        "paper_deadline": VerifiedRuleFact(
            rule_key="paper_deadline",
            label="紙本繳件截止日／送件規定",
            value_text="須經系所、學院初選推薦後送交國際處（系所截止日早於校級截止日，請向系辦確認；日語二甄校級收件已於 2026/09/30 12:00 截止）",
            exact_deadline_at=_dt(2026, 9, 30, 12, 0),
            submission_mode="paper_required",
            source_title="淡江大學 2027–2028 年赴日本姊妹校（日語組）第二次聯合甄選更正公告",
            source_url="https://oieie.tku.edu.tw/oieie/?tkuisotope=%e6%9b%b4%e6%ad%a32027-2028%e5%b9%b4%e8%b5%b4%e6%97%a5%e6%9c%ac%e5%a7%8a%e5%a6%b9%e6%a0%a1%e6%97%a5%e8%aa%9e%e7%b5%84-%e4%ba%a4%e6%8f%9b%e7%94%9f%e7%ac%ac%e4%ba%8c%e6%ac%a1%e8%81%af%e5%90%88",
            last_checked_at="2026-10-08",
        ),
        "study_plan_limit": VerifiedRuleFact(
            rule_key="study_plan_limit",
            label="讀書計畫字數／頁數上限",
            value_text="申請表、成績單、語言證明、推薦函、中日文自傳與研習計畫、切結書及其他證明，以 A4 單面列印總計不超過 16 頁",
            max_pages=16,
            source_title="淡江大學 2027–2028 年赴日本姊妹校（日語組）第二次聯合甄選作業簡章",
            source_url="https://oieie.tku.edu.tw/oieie/?tkuisotope=%e6%aa%a2%e9%80%812027-2028%e5%b9%b4%e8%b5%b4%e6%97%a5%e6%9c%ac%e5%a7%8a%e5%a6%b9%e6%a0%a1%e6%97%a5%e8%aa%9e%e7%b5%84-%e4%ba%a4%e6%8f%9b%e7%94%9f%e7%ac%ac%e4%ba%8c%e6%ac%a1%e8%81%af%e5%90%88",
            last_checked_at="2026-10-08",
        ),
        "extra_milestones": [
            (
                "tku-subtask-jtea-2027-1",
                "[淡江獎學金] 2027 第一期日本台灣交流協會短期留學生獎學金校內收件截止（限符合特定條件赴日交換生）",
                "2026-10-30",
                "獎學金校內截止",
                "other",
                "每月 8 萬日圓；限具台灣籍、日本相關研究、評價係數 2.30 以上且於 2027 年 4–8 月開始交換者（非所有赴日交換生皆適用），送國際處 T1006 室",
                "https://oieie.tku.edu.tw/",
            ),
            (
                "tku-subtask-info-session-2027-2028",
                "[淡江交換] 2027–2028 赴姊妹校交換生聯合甄選說明會報名截止（17:00；11/06 18:00–19:30 舉辦）",
                "2026-11-05",
                "說明會報名截止",
                "home",
                "2027–2028 交換甄選說明會於 2026/11/06 18:00–19:30 在驚聲國際會議廳舉行，11/05 17:00 報名截止（非交換申請截止）",
                "https://enroll.tku.edu.tw/course.aspx?cid=auix1106",
            ),
        ],
    },
    {
        "school_id": "ntust",
        "in_ten_week_window": False,
        "window_status": "closed_current_round",
        "window_badge": "115-2 已於 10/01 截止 · 116-1 預計春季開放",
        "cycle_label": "115-2（2027 春季班）赴歐美亞澳及大陸地區交換甄選（已於 06/17 及 10/01 截止；116-1 待春季公告）",
        "primary_deadline_date": "2026-10-01",
        "primary_deadline_at": _dt(2026, 10, 1, 17, 0),
        "anchor_date": date(2026, 11, 30),
        "online_deadline": VerifiedRuleFact(
            rule_key="online_deadline",
            label="校內線上報名截止日",
            value_text="115-2 赴歐美亞澳已於 2026/06/17 17:00 截止、赴大陸地區已於 2026/10/01 17:00 截止；116-1（2027 秋季班）簡章待國際處公告",
            exact_deadline_at=_dt(2026, 10, 1, 17, 0),
            submission_mode="online",
            source_title="國立臺灣科技大學國際事務處—115-2 赴大陸地區交換學生甄選簡章",
            source_url="https://www.oia.ntust.edu.tw/p/406-1060-143054,r1580.php?Lang=zh-tw",
            last_checked_at="2026-10-16",
        ),
        "paper_deadline": VerifiedRuleFact(
            rule_key="paper_deadline",
            label="紙本繳件截止日／送件規定",
            value_text="須於學生資訊系統完成線上填報並上傳電子檔後，列印紙本申請表完成本人及系所簽章，於截止日 17:00 前送達國際事務處",
            exact_deadline_at=_dt(2026, 10, 1, 17, 0),
            submission_mode="paper_required",
            source_title="國立臺灣科技大學國際事務處—交換生申請流程與應備文件",
            source_url="https://www.oia.ntust.edu.tw/p/405-1060-60620,c9035.php?Lang=zh-tw",
            last_checked_at="2026-10-16",
        ),
        "study_plan_limit": VerifiedRuleFact(
            rule_key="study_plan_limit",
            label="讀書計畫字數／頁數上限",
            value_text="歐美亞澳交換須繳交中、英文讀書計畫各一份及中、英文自傳各一份，格式不拘，每份篇幅約 1–2 頁，分別將中、英文版合併為 PDF 上傳（不另計分）",
            max_pages=2,
            source_title="國立臺灣科技大學 115-2 歐美亞澳交換學生甄選簡章 PDF",
            source_url="https://www.oia.ntust.edu.tw/var/file/60/1060/img/2204/20260317.pdf",
            last_checked_at="2026-10-16",
        ),
    },
]


def _build_card(spec: dict[str, Any]) -> VerifiedSchoolWindowCard:
    profile = require_university(spec["school_id"])
    online_rule: VerifiedRuleFact = spec["online_deadline"]
    paper_rule: VerifiedRuleFact = spec["paper_deadline"]
    study_plan_rule: VerifiedRuleFact = spec["study_plan_limit"]
    subtasks = _build_subtasks(
        school_id=profile.id,
        short_name=profile.short_name,
        anchor_date=spec["anchor_date"],
        online_rule=online_rule,
        paper_rule=paper_rule,
        study_plan_rule=study_plan_rule,
        extra_milestones=spec.get("extra_milestones"),
    )
    primary_date = spec["primary_deadline_date"] or spec["anchor_date"].strftime("%Y-%m-%d")
    gcal_title = f"[{profile.short_name}交換] 校內申請截止與備審防漏提醒"
    gcal_details = (
        f"【{profile.school_name}】{spec['cycle_label']}\n"
        f"1. 校內線上報名截止日：{online_rule.value_text}（來源：{online_rule.source_url}｜查核：{online_rule.last_checked_at}）\n"
        f"2. 紙本繳件截止日／規定：{paper_rule.value_text}（來源：{paper_rule.source_url}｜查核：{paper_rule.last_checked_at}）\n"
        f"3. 讀書計畫字數／頁數上限：{study_plan_rule.value_text}（來源：{study_plan_rule.source_url}｜查核：{study_plan_rule.last_checked_at}）"
    )
    google_calendar_url = _google_calendar_template_url(
        title=gcal_title,
        due_date=primary_date,
        details=gcal_details,
        source_url=online_rule.source_url,
    )
    line_msg = (
        f"訂閱【{profile.school_name}】交換截止日與支線任務倒數推播\n"
        f"・梯次：{spec['cycle_label']}\n"
        f"・線上截止：{online_rule.value_text}\n"
        f"・紙本規定：{paper_rule.value_text}\n"
        f"・讀書計畫：{study_plan_rule.value_text}\n"
        f"・官方來源：{online_rule.source_url}（最後查核：{online_rule.last_checked_at}）"
    )
    return VerifiedSchoolWindowCard(
        school_id=profile.id,
        school_name=profile.school_name,
        short_name=profile.short_name,
        in_ten_week_window=bool(spec["in_ten_week_window"]),
        window_status=spec["window_status"],
        window_badge=spec["window_badge"],
        cycle_label=spec["cycle_label"],
        primary_deadline_date=spec["primary_deadline_date"],
        primary_deadline_at=spec["primary_deadline_at"],
        online_deadline=online_rule,
        paper_deadline=paper_rule,
        study_plan_limit=study_plan_rule,
        subtasks=subtasks,
        ics_download_url=f"/calendar/school-window.ics?school={profile.id}",
        google_calendar_url=google_calendar_url,
        line_oa_url=_line_oa_url(line_msg),
        line_copy_summary=line_msg,
    )


_CARDS_BY_ID: dict[str, VerifiedSchoolWindowCard] = {
    spec["school_id"]: _build_card(spec) for spec in _RAW_SPECS
}


def get_verified_school_window_card(school: str) -> VerifiedSchoolWindowCard:
    profile = require_university(school)
    card = _CARDS_BY_ID.get(profile.id)
    if card is None:
        raise KeyError(f"Missing verified window card for {profile.id}")
    return card


def build_verified_window_deadline_catalog(
    school: str | None = None,
) -> VerifiedWindowDeadlineCatalog:
    if school:
        items = [get_verified_school_window_card(school)]
    else:
        items = [_CARDS_BY_ID[spec["school_id"]] for spec in _RAW_SPECS]
    ten_week_count = sum(1 for item in _CARDS_BY_ID.values() if item.in_ten_week_window)
    return VerifiedWindowDeadlineCatalog(
        window_start_date=WINDOW_START_DATE,
        window_end_date=WINDOW_END_DATE,
        ten_week_school_count=ten_week_count,
        total_supported_school_count=len(SUPPORTED_UNIVERSITIES),
        last_checked_at=CATALOG_LAST_CHECKED_AT,
        items=items,
    )


def build_school_window_ics(school: str) -> tuple[str, str]:
    """Build a public, zero-login iCalendar (.ics) file with deadlines, sub-tasks, and VALARM."""
    card = get_verified_school_window_card(school)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//UniWay Taiwan//Verified Exchange Window Deadlines//ZH-TW",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH",
        f"X-WR-CALNAME:{_escape_ics(f'UniWay {card.short_name} 交換截止日與防漏支線任務')}",
        "X-WR-TIMEZONE:Asia/Taipei",
    ]
    reminder_days = (14, 7, 3, 1, 0)

    for subtask in card.subtasks:
        start = datetime.strptime(subtask.due_date, "%Y-%m-%d").date()
        end = start + timedelta(days=1)
        description = (
            f"{subtask.note}\n"
            f"校內線上報名截止日：{card.online_deadline.value_text}\n"
            f"紙本繳件截止日／規定：{card.paper_deadline.value_text}\n"
            f"讀書計畫字數／頁數上限：{card.study_plan_limit.value_text}\n"
            f"官方來源：{subtask.source_url}\n"
            f"最後查核日期：{subtask.last_checked_at}"
        )
        lines.extend(
            [
                "BEGIN:VEVENT",
                f"UID:{_escape_ics(subtask.id)}@uniway.tw",
                f"DTSTAMP:{stamp}",
                f"DTSTART;VALUE=DATE:{start.strftime('%Y%m%d')}",
                f"DTEND;VALUE=DATE:{end.strftime('%Y%m%d')}",
                f"SUMMARY:{_escape_ics(subtask.title)}",
                f"DESCRIPTION:{_escape_ics(description)}",
                f"URL:{_escape_ics(subtask.source_url)}",
            ]
        )
        for days in reminder_days:
            trigger = f"-P{days}D" if days > 0 else "PT0M"
            lines.extend(
                [
                    "BEGIN:VALARM",
                    f"TRIGGER:{trigger}",
                    "ACTION:DISPLAY",
                    f"DESCRIPTION:{_escape_ics(subtask.title)}",
                    "END:VALARM",
                ]
            )
        lines.append("END:VEVENT")

    lines.append("END:VCALENDAR")
    filename = f"uniway-{card.school_id}-exchange-deadlines.ics"
    content = "\r\n".join(lines) + "\r\n"
    return filename, content
