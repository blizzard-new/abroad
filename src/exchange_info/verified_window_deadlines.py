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
CATALOG_LAST_CHECKED_AT = "2026-10-27"
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
    deadline_event_title: str = "校內申請正式截止日（防漏最後確認）",
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
            f"[{short_name}交換] {deadline_event_title}",
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


FCU_REVIEWED_GUIDELINES_URL = 'https://oiasap.fcu.edu.tw/pdf/d44f/逢甲大學115-1學年度選送學生出國研修簡章（校級合作）_20260629.pdf'

_RAW_SPECS: list[dict[str, Any]] = [
    {
        "school_id": "yzu",
        "in_ten_week_window": True,
        "window_status": "pending_exact_date",
        "window_badge": "依各校初審與後續送件日期，無共同截止",
        "cycle_label": "115-2國際初審已截止；大陸逐校日期與適用期別分開確認",
        "primary_deadline_date": None,
        "primary_deadline_at": None,
        "anchor_date": date(2026, 10, 20),
        "online_deadline": VerifiedRuleFact(
            rule_key="online_deadline", label="校內初審截止",
            value_text="國際一般初審09/22中午、Early Nomination另核；赴陸同濟10/14、南京10/16、部分學校10/20，未列時刻。武漢同頁兩期日期並存；11/01為西南後續學校資料繳交日，非共同17:00截止。正式Google名額表於2026/10/27仍無法讀取，保留10/21最後成功基準，不推論今日名額無變更。",
            exact_deadline_at=None, submission_mode="pending_notice",
            verification_status="needs_confirmation",
            source_title="元智現行赴陸表格與國際初審公告",
            source_url="https://gao.yzu.edu.tw/index.php/tw/guo-ji-jiao-liu2/fu-lu-jiao-huan",
            last_checked_at="2026-10-27",
        ),
        "paper_deadline": VerifiedRuleFact(
            rule_key="paper_deadline", label="紙本與線上分工",
            value_text="校級國際初審完成線上表單與四項紙本送R70208：申請人簽章志願表、中英文成績單、英檢影本。赴陸先交成績單、志願表、台胞證影本（如果有），通過後另交接待校文件。",
            exact_deadline_at=None, submission_mode="paper_required",
            verification_status="verified_current",
            source_title="元智校級初審資料及流程",
            source_url="https://gao.yzu.edu.tw/index.php/tw/guo-ji-jiao-liu2/fu-wai-jiao-huan",
            last_checked_at="2026-10-21",
        ),
        "study_plan_limit": VerifiedRuleFact(
            rule_key="study_plan_limit", label="學習計畫適用階段",
            value_text="CF02複審需英文自傳、英文學習計畫各一份；赴陸明列免繳這兩項及英文推薦信。已核對表單未訂500字中文計畫門檻；接待校個別規格仍待確認。",
            verification_status="verified_current",
            source_title="元智赴外交流學生報名表CF02",
            source_url="https://gao.yzu.edu.tw/files/Outgoing_Students/IA-CP-05-CF02R3.pdf",
            last_checked_at="2026-10-21",
        ),
    },
    {
        "school_id": "ntpu",
        "in_ten_week_window": True,
        "window_status": "open",
        "window_badge": "10 週窗口進行中 · 10/23 17:00 截止（含 10/22 學海修正公告）",
        "cycle_label": "116 學年度（2027 秋／2028 春）校級赴外交換學生甄選（10/23 17:00 截止；2026/10/22 學海飛颺與惜珠修正公告）",
        "primary_deadline_date": "2026-10-23",
        "primary_deadline_at": _dt(2026, 10, 23, 17, 0),
        "anchor_date": date(2026, 10, 23),
        "online_deadline": VerifiedRuleFact(
            rule_key="online_deadline",
            label="校內線上報名截止日",
            value_text="線上申請至2026/10/23（五）17:00止（已截止）；英文組11/23、11/25，中日文組11/27面試。另有2026/10/22學海甄選辦法修正公告及10/12法國EFREI說明會；法律院交換10/30 11:00截止（law.ntpu.edu.tw/news/j1p0rQCYhCHb）僅限法律院，不可混為全校截止（校級預告與商院公告讀取失敗保留基準）。",
            exact_deadline_at=_dt(2026, 10, 23, 17, 0),
            submission_mode="online",
            source_title="國立臺北大學國際事務處—116 學年度赴外交換學生甄選公告（含 2026/10/22 學海修正公告及法律院院級分流說明）",
            source_url="https://new.ntpu.edu.tw/oia/news/6ab396bf7085cb4f0c81831f",
            last_checked_at="2026-10-27",
            verification_status="verified_current",
        ),
        "paper_deadline": VerifiedRuleFact(
            rule_key="paper_deadline",
            label="紙本繳件截止日／送件規定",
            value_text="申請系統填妥確認送出後，列印申請表並本人簽名，於 2026/10/23（五）17:00 前上傳公告指定 Google 表單；檔名須含中文姓名，逾期視為未完成申請",
            exact_deadline_at=_dt(2026, 10, 23, 17, 0),
            submission_mode="signed_scan_upload",
            source_title="國立臺北大學 116 學年度赴外交換學生甄選簡章 PDF",
            source_url="https://cms-carrier.ntpu.edu.tw/uploads/116_16e535159d.pdf",
            last_checked_at="2026-10-21",
            verification_status="verified_current",
        ),
        "study_plan_limit": VerifiedRuleFact(
            rule_key="study_plan_limit",
            label="讀書計畫字數／頁數上限",
            value_text="出國學習計畫書以 A4 紙直式橫書，合計 5,000 字以內，格式自訂（英文組繳英文、日文組繳日文、中文組繳中文計畫書）",
            max_chars=5000,
            source_title="國立臺北大學 116 學年度赴外交換學生甄選簡章（申請步驟及應繳文件）",
            source_url="https://cms-carrier.ntpu.edu.tw/uploads/116_16e535159d.pdf",
            last_checked_at="2026-10-21",
            verification_status="verified_current",
        ),
    },
    {
        "school_id": "nchu",
        "in_ten_week_window": True,
        "window_status": "open",
        "window_badge": "10 週窗口 · 第一步線上申請 10/23 12:00 截止・推薦信 10/30 12:00",
        "cycle_label": "116 學年度第 1 學期（2027 秋季班）出國暨赴大陸交換學生甄選（第一步線上申請 10/23 12:00 已截止；推薦信至 10/30 12:00）",
        "primary_deadline_date": "2026-10-23",
        "primary_deadline_at": _dt(2026, 10, 23, 12, 0),
        "anchor_date": date(2026, 10, 23),
        "online_deadline": VerifiedRuleFact(
            rule_key="online_deadline",
            label="校內線上報名截止日",
            value_text="第一步學生線上申請（2026/09/23 至 2026/10/23（五）12:00 中午止，已截止）；第二步線上教師推薦函至 2026/10/30（五）12:00 止；退補件至 2026/11/06（五）23:59 止（中英文版簡章頁一致）",
            exact_deadline_at=_dt(2026, 10, 23, 12, 0),
            submission_mode="online",
            source_title="國立中興大學 2027 秋季班（116-1）出國交換學生甄選簡章 PDF（暨中英文申請簡章專頁）",
            source_url="https://www.oia.nchu.edu.tw/images/File/05_Global_Mobility/5-1-Exchange-Student-Programs/Exchange_Program_Guidelines_for_Fall_Semester_2027_TW.pdf",
            last_checked_at="2026-10-27",
            verification_status="verified_current",
        ),
        "paper_deadline": VerifiedRuleFact(
            rule_key="paper_deadline",
            label="紙本繳件截止日／送件規定",
            value_text="申請表須完成導師／指導教授及系所核章後掃描上傳；研究生由指導教授核章。學生於 10/23 12:00 前完成線上送件，兩份教師推薦函另於 10/30 12:00 前填寫。",
            submission_mode="paperless",
            source_title="國立中興大學 2027 秋季班（116-1）出國交換學生甄選簡章 PDF",
            source_url="https://www.oia.nchu.edu.tw/images/File/05_Global_Mobility/5-1-Exchange-Student-Programs/Exchange_Program_Guidelines_for_Fall_Semester_2027_TW.pdf",
            last_checked_at="2026-10-21",
            verification_status="verified_current",
        ),
        "study_plan_limit": VerifiedRuleFact(
            rule_key="study_plan_limit",
            label="讀書計畫字數／頁數上限",
            value_text="《自傳及讀書計畫》合計至多 A4 三面，以第一志願為目標；有填海外志願須交英文版，僅申請大陸者中英文皆可。上傳檔案限 JPG 或 PDF，每檔須小於 2MB。",
            max_pages=3,
            source_title="國立中興大學 2027 秋季班出國交換學生甄選簡章（文件說明）",
            source_url="https://www.oia.nchu.edu.tw/images/File/05_Global_Mobility/5-1-Exchange-Student-Programs/Exchange_Program_Guidelines_for_Fall_Semester_2027_TW.pdf",
            last_checked_at="2026-10-21",
            verification_status="verified_current",
        ),
        "extra_milestones": [
            (
                "nchu-subtask-recommendation",
                "[中興交換] 線上教師推薦函上傳截止（12:00 中午）",
                "2026-10-30",
                "推薦函截止",
                "documents",
                "指導教授或授課教師須於 2026/10/30 12:00 前透過系統連結完成線上推薦函上傳",
                "https://www.oia.nchu.edu.tw/images/File/05_Global_Mobility/5-1-Exchange-Student-Programs/Exchange_Program_Guidelines_for_Fall_Semester_2027_TW.pdf",
            ),
            (
                "nchu-subtask-supplement",
                "[中興交換] 初審退補件最後截止日（23:59）",
                "2026-11-06",
                "補件截止",
                "documents",
                "接獲補件通知者，須於 2026/11/06 23:59 前依簡章寄送補件至承辦人信箱；語言證明限補交截止前已取得成績的正式成績單。",
                "https://www.oia.nchu.edu.tw/images/File/05_Global_Mobility/5-1-Exchange-Student-Programs/Exchange_Program_Guidelines_for_Fall_Semester_2027_TW.pdf",
            ),
        ],
    },
    {
        "school_id": "wzu",
        "in_ten_week_window": False,
        "window_status": "closed_current_round",
        "window_badge": "115-2二招已截止；116-1日期待核實",
        "cycle_label": "115-2一般組及語言學習組（二招）",
        "primary_deadline_date": None,
        "primary_deadline_at": None,
        "anchor_date": None,
        "online_deadline": VerifiedRuleFact(
            rule_key="online_deadline", label="115-2二招線上報名截止",
            value_text="2026/10/05公告二招一般組（530752／530796）及語言學習組（530751／530797），延至10/13 23:59截止；10/14發布二招報名成功名單（530925，非錄取結果，最終由接待校決定）；10/05另公告115年第2次學海飛颺開放系級交換生申請至11/16截止（530756）；尚無116-1一招公告。",
            exact_deadline_at=_dt(2026, 10, 13, 23, 59), submission_mode="online",
            source_title="文藻115-2二招公告（530752／530751）、二招報名成功名單（530925）與系級學海飛颺（530756）",
            source_url="https://d020.wzu.edu.tw/article/530752", last_checked_at="2026-10-28",
            verification_status="verified_reference",
        ),
        "paper_deadline": VerifiedRuleFact(
            rule_key="paper_deadline", label="初審上傳及分發後簽章",
            value_text="初審線上上傳學生證、身分證件、用印中文成績單及履歷；語檢與志工證明加分。分發後交換意願切結書須本人及家長簽名並蓋章，期限依通知；非初審15:00紙本收件或固定10000元保證金。",
            submission_mode="signed_scan_upload",
            source_title="文藻115-2二招簡章第2–4頁",
            source_url="https://d020.wzu.edu.tw/datas/upload/Pictures/530752-115-2交換生簡章二招.pdf",
            last_checked_at="2026-10-26", verification_status="verified_reference",
        ),
        "study_plan_limit": VerifiedRuleFact(
            rule_key="study_plan_limit", label="履歷（含學習計畫）合計篇幅",
            value_text="履歷含自傳、學習計畫、國際活動與獲獎等內容，合計A4五頁、12號字，不含附件；非計畫單篇五頁或各1000字。英語及華語暨東南亞語組中文與英文，其他語組中文與目標語言。返國兩週內繳返國資料。",
            source_title="文藻115-2二招簡章第2–3、6頁",
            source_url="https://d020.wzu.edu.tw/datas/upload/Pictures/530752-115-2交換生簡章二招.pdf",
            last_checked_at="2026-10-26", verification_status="verified_reference",
        ),
    },
    {
        "school_id": "pccu",
        "in_ten_week_window": True,
        "window_status": "open",
        "window_badge": "赴陸第二階段 · 11/03 17:00（限公告名單）",
        "cycle_label": "115-2赴陸第二階段；附件學期標示衝突須確認",
        "primary_deadline_date": "2026-11-03",
        "primary_deadline_at": _dt(2026, 11, 3, 17, 0),
        "anchor_date": date(2026, 11, 3),
        "deadline_event_title": "赴陸第二階段線上及紙本截止（限公告名單）",
        "online_deadline": VerifiedRuleFact(
            rule_key="online_deadline", label="赴陸第二階段線上申請",
            value_text="赴陸第二階段2026/11/03 17:00截止，須完成線上與紙本（兩岸中心RPage頁mccd.pccu.edu.tw；國合組入口oima.pccu.edu.tw/p/412-1008-14612.php，舊頁exchanges.htm及en/study-abroad-detail5.htm無當期表單或讀取失敗）。網頁115-2與PDF 115-1衝突待確認；國合組116未核實，日文系115為2025/11/17–28。",
            exact_deadline_at=_dt(2026, 11, 3, 17, 0), submission_mode="online",
            source_title="文化大學115-2赴陸交換第二階段公告",
            source_url="https://mccd.pccu.edu.tw/p/406-1300-148804,r2247.php?Lang=zh-tw",
            last_checked_at="2026-10-27", verification_status="verified_current",
        ),
        "paper_deadline": VerifiedRuleFact(
            rule_key="paper_deadline", label="赴陸第二階段紙本申請",
            value_text="系統產生WORD申請表，系主任簽名、研究生另須指導教授簽名，附中文自傳、300字內學習計畫及歷年成績排名，2026/11/03 17:00前送大恩館3樓310室。韓文系115-2為電子郵件PDF，已於10/06 08:00截止。",
            exact_deadline_at=_dt(2026, 11, 3, 17, 0), submission_mode="paper_required",
            source_title="文化大學赴陸第二階段公告及附件",
            source_url="https://mccd.pccu.edu.tw/p/406-1300-148804,r2247.php?Lang=zh-tw",
            last_checked_at="2026-10-26", verification_status="verified_current",
        ),
        "study_plan_limit": VerifiedRuleFact(
            rule_key="study_plan_limit", label="依申請管道確認計畫格式",
            value_text="赴陸第二階段中文學習計畫300字以內；日文系115範本分動機至少200字、計畫第1–3項合計至少500字、生涯規劃至少300字；韓文系自傳動機中文或韓文，未載統一字數。不能共用1000字要求。",
            source_title="文化大學各管道計畫規定",
            source_url="https://mccd.pccu.edu.tw/p/406-1300-148804,r2247.php?Lang=zh-tw",
            last_checked_at="2026-10-26", verification_status="verified_current",
        ),
        "extra_milestones": [],
    },
    {
        "school_id": "nccu",
        "in_ten_week_window": True,
        "window_status": "open",
        "window_badge": "10 週窗口進行中 · 國際組語檢 11/02・大陸組 11/06 截止",
        "cycle_label": "115-1 校級國際薦外交換（語檢上傳至 11/02 16:00）＆薦外大陸交換甄試（09/14–11/06 17:00）",
        "primary_deadline_date": "2026-11-02",
        "primary_deadline_at": _dt(2026, 11, 2, 16, 0),
        "anchor_date": date(2026, 11, 2),
        "deadline_event_title": "國際組語檢上傳截止（限已報名者）",
        "online_deadline": VerifiedRuleFact(
            rule_key="online_deadline",
            label="國際組語檢／大陸組申請截止",
            value_text="國際組報名已於2026/09/24 16:00截止；10/31口試（post/118），語檢上傳至11/02 16:00。志願選填11/10–11/16 16:00、12/02–12/08 16:00。大陸組09/14–11/06 17:00線上及紙本繳件（動態目錄讀取失敗，保留10/25之39筆基準）",
            exact_deadline_at=_dt(2026, 11, 2, 16, 0),
            submission_mode="online",
            source_title="國立政治大學 115-1 校級國際薦外交換生甄試簡章 PDF 與口試公告（post/118）",
            source_url="https://outbound.nccu.edu.tw/media/files/f353edca-d805-48ac-a6c9-9f66cf925c9e",
            last_checked_at="2026-10-27",
            verification_status="verified_current",
        ),
        "paper_deadline": VerifiedRuleFact(
            rule_key="paper_deadline",
            label="紙本繳件截止日／送件規定",
            value_text="大陸組須線上填報並於 2026/11/06（五）17:00 前，在上班時間將親簽申請書及所列紙本資料送國合處大陸事務組（行政大樓 7 樓 160704 室）；國際組初審文件依其簡章上傳 PDF",
            exact_deadline_at=_dt(2026, 11, 6, 17, 0),
            submission_mode="paper_required",
            source_title="國立政治大學 115-1 校級薦外大陸交換生甄試簡章 PDF",
            source_url="https://oic.nccu.edu.tw/Home/Download?FileId=AC94A5C6-1ED6-421D-AD29-F673F2418670",
            last_checked_at="2026-10-21",
            verification_status="verified_current",
        ),
        "study_plan_limit": VerifiedRuleFact(
            rule_key="study_plan_limit",
            label="讀書計畫字數／頁數上限",
            value_text="國際薦外：交換計畫書與履歷表分為 2 份，電腦繕打 A4 直式橫書，每份各至少 500 字、以 2 頁為限（超出 2 頁不予計分）；赴大陸交換：自傳 1,000 字以內、研究／學習計畫 3,000 字以內（超字數不受理）",
            source_title="國立政治大學 115-1 校級國際薦外交換生甄試簡章與赴大陸交換生甄試簡章",
            source_url="https://outbound.nccu.edu.tw/media/files/f353edca-d805-48ac-a6c9-9f66cf925c9e",
            last_checked_at="2026-10-21",
            verification_status="verified_current",
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
        "cycle_label": "116 學年度第 1 學期（2027 秋／2028 春）校級出國交換學生甄選（12/2 成績公布、12/7 一階志願截止）",
        "primary_deadline_date": "2026-11-09",
        "primary_deadline_at": _dt(2026, 11, 9, 16, 0),
        "anchor_date": date(2026, 11, 9),
        "online_deadline": VerifiedRuleFact(
            rule_key="online_deadline",
            label="校內線上報名截止日",
            value_text="2026/11/03 10:00至11/09 16:00線上報名、繳報名費NT$1,250（低收／中低收免繳）；退補件至11/12 16:00；12/02成績公布、12/07一階志願截止（哥廷根說明會報名中；頁尾10/30–31維護為2022舊彈窗；OIA列表school.list與9詳頁錯誤不等於名額恢復，保留10/22基準，150份有效、23份缺口）",
            verification_status="verified_current",
            exact_deadline_at=_dt(2026, 11, 9, 16, 0),
            submission_mode="online",
            source_title="國立臺灣大學 116 學年度第 1 學期校級出國交換學生甄選簡章與時程專頁",
            source_url="https://studyabroad.ntu.edu.tw/wp-content/uploads/2026/07/116-1-Selection-Guidelines_CH.pdf",
            last_checked_at="2026-10-27",
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
            verification_status="verified_current",
            min_chars=500,
            max_pages=2,
            source_title="國立臺灣大學 116 學年度第 1 學期校級出國交換學生甄選簡章（應繳文件）",
            source_url="https://studyabroad.ntu.edu.tw/wp-content/uploads/2026/07/116-1-Selection-Guidelines_CH.pdf",
            last_checked_at="2026-10-21",
        ),
    },
    {
        "school_id": "nthu",
        "in_ten_week_window": True,
        "window_status": "upcoming",
        "window_badge": "10 週窗口即將開放 · 11/03–11/10 16:00 二階志願",
        "cycle_label": "2027 秋／2028 春校級交換二階線上志願選填（11/03–11/10 16:00）",
        "primary_deadline_date": "2026-11-10",
        "primary_deadline_at": _dt(2026, 11, 10, 16, 0),
        "anchor_date": date(2026, 11, 10),
        "online_deadline": VerifiedRuleFact(
            rule_key="online_deadline",
            label="校內線上報名截止日",
            value_text="2027秋／2028春第一梯次二階線上志願選填：2026/11/03至11/10 16:00，至多10志願，免繳紙本（限完成一階者）。系統142條目動態表（puid/11521）及140份詳頁不變；九州大學、大阪工業大學詳頁首次建檔僅作基準（非新增名額），不同名額單位不混加。",
            exact_deadline_at=_dt(2026, 11, 10, 16, 0),
            submission_mode="online",
            source_title="國立清華大學 2027 秋／2028 春（116 學年度）出國交換生甄選簡章 PDF 與動態總覽表（puid/11521）",
            source_url="https://oga.site.nthu.edu.tw/var/file/524/1524/img/704171014.pdf",
            last_checked_at="2026-10-27",
            verification_status="verified_current",
        ),
        "paper_deadline": VerifiedRuleFact(
            rule_key="paper_deadline",
            label="紙本繳件截止日／送件規定",
            value_text="第一階段：列印線上申請表，連同紙本文件於 2026/10/08 16:00 前送系所（系所可能提早截止）。錄取確認：2026/12/11 16:00 前繳同意書、家長擔保同意書及 NT$8,000 行政處理費／保證金；獲獎者另附獎學金承諾書。",
            exact_deadline_at=_dt(2026, 10, 8, 16, 0),
            submission_mode="paper_required",
            source_title="國立清華大學全球事務處—出國交換申請文件與保證金規定 PDF",
            source_url="https://oga.site.nthu.edu.tw/var/file/524/1524/img/704171014.pdf",
            last_checked_at="2026-10-21",
            verification_status="verified_current",
        ),
        "study_plan_limit": VerifiedRuleFact(
            rule_key="study_plan_limit",
            label="讀書計畫字數／頁數上限",
            value_text="每個志願各準備一份修課／讀書計畫，可用中文；本期公告未訂固定字數或頁數上限，未要求一律繳交中外文兩份計畫與自傳。",
            source_title="國立清華大學 2027 秋／2028 春出國交換申請公告（應繳文件）",
            source_url="https://oga.site.nthu.edu.tw/p/406-1524-314332,r8950.php?Lang=zh-tw",
            last_checked_at="2026-10-21",
            verification_status="verified_current",
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
            value_text="校級線上申請 2026/11/01 至 2026/11/15（日）23:59:59；申請文件含 NT$500 報名費繳費證明。收到缺件或審查不合格通知者，補件至 11/16（一）23:59:59，此日期不是新申請期限（校級名額表 29 頁／285 條目／96 學程與簡章不變；院級公告正文截斷，不將院級名額併入校級）",
            exact_deadline_at=_dt(2026, 11, 15, 23, 59, 59),
            submission_mode="online",
            source_title="國立臺灣師範大學 116-1 赴外交換生甄選簡章 PDF 與校級名額表（outgoing-quotalist）",
            source_url="https://bds.oia.ntnu.edu.tw/api/v1/pt/dl?f=/pt/contents/2014100104/doc_OE116-1%20SPRING2027-1013.pdf",
            last_checked_at="2026-10-27",
            verification_status="verified_current",
        ),
        "paper_deadline": VerifiedRuleFact(
            rule_key="paper_deadline",
            label="紙本繳件截止日／送件規定",
            value_text="校內初審上傳電子備審文件；申請書須列印、簽名後掃描。若照片無法正常列印，須貼紙本照片、本人及系主任簽名後掃描。正式申請文件於 11/15 截止；11/16 僅供通知補件者使用",
            exact_deadline_at=_dt(2026, 11, 15, 23, 59, 59),
            submission_mode="signed_scan_upload",
            source_title="國立臺灣師範大學國際事務處—赴外交換生系統申請規範",
            source_url="https://bds.oia.ntnu.edu.tw/api/v1/pt/dl?f=/pt/contents/2014100104/doc_OE116-1%20SPRING2027-1013.pdf",
            last_checked_at="2026-10-21",
            verification_status="verified_current",
        ),
        "study_plan_limit": VerifiedRuleFact(
            rule_key="study_plan_limit",
            label="讀書計畫字數／頁數上限",
            value_text="申請文件頁列自傳與計畫中英文合計 500–5,000 字，建議外文約 500–2,500 字；但同份簡章所附作業要點列 1,000 字以上。最低字數存在不一致，請向國際處確認；本平台不據此自動判定最低字數",
            max_chars=5000,
            source_title="國立臺灣師範大學赴外交換生系統應備文件規範",
            source_url="https://bds.oia.ntnu.edu.tw/api/v1/pt/dl?f=/pt/contents/2014100104/doc_OE116-1%20SPRING2027-1013.pdf",
            last_checked_at="2026-10-21",
            verification_status="needs_confirmation",
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
            verification_status="verified_current",
            rule_key="online_deadline",
            label="校內線上報名截止日",
            value_text="線上申請與電子備審上傳至 2026/11/16（一）12:00（中午）止（逾時系統關閉不受理；預計 2026 年 12 月底公告錄取結果）",
            exact_deadline_at=_dt(2026, 11, 16, 12, 0),
            submission_mode="online",
            source_title="東吳大學國際及兩岸學術交流處—116 學年度赴境外交換申請專頁",
            source_url="https://icae.scu.edu.tw/zh-hant/outbound-exchange/itnl/AYapply",
            last_checked_at="2026-10-27",
        ),
        "paper_deadline": VerifiedRuleFact(
            verification_status="verified_current",
            rule_key="paper_deadline",
            label="紙本繳件截止日／送件規定",
            value_text="全面採線上申請系統上傳 PDF 電子檔（單一檔案上限 5MB），免繳交紙本文件至國際及兩岸學術交流處",
            exact_deadline_at=_dt(2026, 11, 16, 12, 0),
            submission_mode="paperless",
            source_title="東吳大學國際及兩岸學術交流處—線上申請系統備審文件規範",
            source_url="https://icae.scu.edu.tw/zh-hant/outbound-exchange/itnl/AYapply",
            last_checked_at="2026-10-21",
        ),
        "study_plan_limit": VerifiedRuleFact(
            verification_status="verified_current",
            rule_key="study_plan_limit",
            label="讀書計畫字數／頁數上限",
            value_text="自傳或履歷約2,000字；交換研修動機及讀書計畫一校一份，中、外文各約2,000字。官方使用「約」，不能當作硬性上限。Form A、B依志願序合併為PDF，各類上傳檔案以5MB為限。",
            source_title="東吳大學國際及兩岸學術交流處—線上申請系統備審文件規範",
            source_url="https://icae.scu.edu.tw/zh-hant/outbound-exchange/itnl/AYapply",
            last_checked_at="2026-10-21",
        ),
    },
    {
        "school_id": "nsysu",
        "in_ten_week_window": True,
        "window_status": "pending_exact_date",
        "window_badge": "預告10/27起公布簡章（截至10/27 10:04尚未發布）· 11/03–11/17申請",
        "cycle_label": "2027–2028赴其他國家與地區第一次甄選（預告10/27起公布簡章，截至2026/10/27 10:04仍連2026/04/12參考文件、尚未核得本期正式簡章／名額）",
        "primary_deadline_date": None,
        "primary_deadline_at": None,
        "anchor_date": date(2026, 10, 21),
        "online_deadline": VerifiedRuleFact(
            rule_key="online_deadline", label="預定校內申請時程",
            value_text="2026/10/21最新公告載明：2027–2028其他國家與地區正式甄選簡章預定自2026/10/27（二）起公告，申請期間2026/11/03（二）09:00至11/17（二）17:00（預告表另列補正至11/20 17:00），學校資訊與名額依2026/04/12公布版本；4場線上說明會為10/29（四）、10/31（六）20:00–21:30及11/04（三）、11/05（四）12:00–13:30。截至2026/10/27 10:04查核時，頁面（p/406-1308-384613,r4450.php）仍連去年參考文件（2026/04/12版），尚未核得本期正式簡章與名額，不能因預定日期已到就宣稱已發布，亦不推論今天稍後不會發布。中國是2027/01/15 09:00至01/26 17:00，01/12為預定簡章公告日。原文明示確切期限以各地區正式簡章為準。",
            submission_mode="pending_notice", verification_status="verified_reference",
            source_title="中山2027–2028其他國家與地區出國交換甄選時程＆線上說明會公告（2026/10/21發布、10/27 10:04查核）",
            source_url="https://oia.nsysu.edu.tw/p/406-1308-384613,r4450.php?Lang=zh-tw",
            last_checked_at="2026-10-27",
        ),
        "paper_deadline": VerifiedRuleFact(
            rule_key="paper_deadline", label="當期文件、紙本及費用規定待確認",
            value_text="雖預告2026/10/27（二）起公布2027–2028其他國家與地區正式簡章，但截至2026/10/27 10:04查核時仍連2026/04/12公布之參考版本，尚未核得可支持當期申請表核章、免紙本與NT$1,000報名費的正式簡章（不因預定日期已到即宣稱已發布，亦不推論今日稍後不會發布）。舊年度曾要求最終錄取者另繳紙本正本查驗，不能概括為完全免紙本。",
            submission_mode="pending_notice", verification_status="needs_confirmation",
            source_title="中山2027–2028甄選時程公告（截至10/27 10:04尚未核得本期正式簡章）",
            source_url="https://oia.nsysu.edu.tw/p/406-1308-384613,r4450.php?Lang=zh-tw",
            last_checked_at="2026-10-27",
        ),
        "study_plan_limit": VerifiedRuleFact(
            rule_key="study_plan_limit", label="研修計畫規格待確認",
            value_text="甄選要點列研修計畫書為應繳文件、占總分20%，未列字數、頁數及語言上限；須核對當期簡章與表格，不能直接套用中英文各一頁或返國報告規格。",
            verification_status="needs_confirmation",
            source_title="中山學生出國交換甄選要點，第2頁第5、8點",
            source_url="https://oia.nsysu.edu.tw/static/file/308/1308/img/4144/874755230.pdf",
            last_checked_at="2026-10-21",
        ),
    },
    {
        "school_id": "ncku",
        "in_ten_week_window": True,
        "window_status": "upcoming",
        "window_badge": "10 週窗口即將開放 · 10/30–11/19 16:00",
        "cycle_label": "116 學年度第 1 學期（2027 秋季班）校級薦外交換學生計畫甄選",
        "primary_deadline_date": "2026-11-19",
        "primary_deadline_at": _dt(2026, 11, 19, 16, 0),
        "anchor_date": date(2026, 11, 19),
        "online_deadline": VerifiedRuleFact(
            rule_key="online_deadline",
            label="校內線上報名截止日",
            value_text="2026/10/30（五）至 2026/11/19（四）16:00 於成大薦外交換系統完成報名；第 1–6 項文件分別上傳，另上傳合併 PDF（50MB 以下）。116-1 簡章公告頁（p/406-1032-306703,r3333.php）於 2026-10-16 更新，10/23 說明暨分享會（圖爾庫、因斯布魯克、東北大學經驗分享）已辦理完畢；簡章 PDF（107138261.pdf）未列開放時刻或 NT$1,000 報名費",
            exact_deadline_at=_dt(2026, 11, 19, 16, 0),
            submission_mode="online",
            source_title="國立成功大學 116 學年第 1 學期校級薦外交換學生計畫簡章公告（2026-10-16 更新）與 PDF",
            source_url="https://oia.ncku.edu.tw/p/406-1032-306703,r3333.php?Lang=zh-tw",
            last_checked_at="2026-10-27",
            verification_status="verified_current",
        ),
        "paper_deadline": VerifiedRuleFact(
            rule_key="paper_deadline",
            label="紙本繳件截止日／送件規定",
            value_text="全線上繳件，2026/11/19 16:00 截止。簡章一處寫申請表可系統登打下載上傳、無須印出填寫，文件表又要求本人簽名及導師／指導教授簽章後掃描；簽章實作方式有歧義，須向成大國際處確認",
            exact_deadline_at=_dt(2026, 11, 19, 16, 0),
            submission_mode="signed_scan_upload",
            source_title="國立成功大學 116 學年第 1 學期校級薦外交換學生計畫簡章 PDF",
            source_url="https://oia.ncku.edu.tw/var/file/32/1032/img/107138261.pdf",
            last_checked_at="2026-10-26",
            verification_status="needs_confirmation",
        ),
        "study_plan_limit": VerifiedRuleFact(
            rule_key="study_plan_limit",
            label="讀書計畫字數／頁數上限",
            value_text="依第一志願學校擬訂中英文讀書或研究計畫，以及中英文自傳。計畫占甄選總分 25%，自傳及其他表現合計占 25%；此簡章未列固定字數或頁數上限，第 7 項合併 PDF 須在 50MB 以下",
            source_title="國立成功大學 116 學年第 1 學期校級薦外交換學生計畫簡章（申請資料與審查方式）",
            source_url="https://oia.ncku.edu.tw/var/file/32/1032/img/107138261.pdf",
            last_checked_at="2026-10-26",
            verification_status="verified_current",
        ),
    },
    {
        "school_id": "cycu",
        "in_ten_week_window": True,
        "window_status": "pending_exact_date",
        "window_badge": "赴陸交換依合作校分別截止；國際二梯10/07已截止",
        "cycle_label": "2027春季班（115-2）：大陸組依各校日期；國際二梯（20校50名）已於10/07中午截止",
        "primary_deadline_date": None,
        "primary_deadline_at": None,
        "anchor_date": None,
        "online_deadline": VerifiedRuleFact(
            rule_key="online_deadline",
            label="校內線上報名截止日",
            value_text="大陸組依官方表中各校的「校內截止日期」辦理，日期從9/24至11/30不等且未列共同截止時刻；11/20僅為安徽大學，不是全組截止。115-2國際姊妹校第二梯次遴選公告（?p=9903，荷美日韓印尼菲20校共50名，GPA 3.0以上）CYCU表單9/24開放，表單與申請表正本於10/07中午12:00截止，面試10/14（已截止）。諮詢公告索引（?page_id=99）日期雖由10/22改為10/27，但正文為首次建立基準，不視為新服務或交換條件改版。",
            submission_mode="online",
            source_title="中原大學國際暨兩岸教育處—赴大陸交換（?p=6340）與115-2國際二梯公告（?p=9903）",
            source_url="https://oia.cycu.edu.tw/?p=6340",
            last_checked_at="2026-10-27",
            verification_status="verified_current",
        ),
        "paper_deadline": VerifiedRuleFact(
            rule_key="paper_deadline",
            label="紙本繳件截止日／送件規定",
            value_text="當期公告要求完成CYCU表單並將申請表正本送國際處701B；申請表須本人及系主任簽名。大陸組書審通過後，接待校申請資料電子檔寄 outgoing_exchange@cycu.edu.tw，由承辦確認後送件。國際二梯公告要求保留其餘紙本供後續需要時繳交。",
            submission_mode="paper_required",
            source_title="中原大學出國交換甄選紙本與電子備審文件規範",
            source_url="https://oia.cycu.edu.tw/?p=6340",
            last_checked_at="2026-10-21",
            verification_status="verified_current",
        ),
        "study_plan_limit": VerifiedRuleFact(
            rule_key="study_plan_limit",
            label="讀書計畫字數／頁數上限",
            value_text="國際組外文自傳與讀書計畫合計至少1,000字；大陸組中文自傳與計畫合計至少1,000字，並非每份各1,000字。另須一頁A4中文簡歷。國際組頁面同列英文必繳與可用當地語言說明，是否可替代須確認；未核實硬性字數上限。",
            source_title="中原大學出國交換甄選紙本與電子備審文件規範",
            source_url="https://oia.cycu.edu.tw/?p=6338",
            last_checked_at="2026-10-21",
            verification_status="needs_confirmation",
        ),
    },
    {
        "school_id": "ncu",
        "in_ten_week_window": True,
        "window_status": "upcoming",
        "window_badge": "10 週窗口即將開放 · 線上 12/04 12:00・紙本 12/11 17:00",
        "cycle_label": "116 學年度第 1 梯次（赴 116-1／116-2）校級出國交換學生甄選（10/22 更新版姐妹校列表已公告）",
        "primary_deadline_date": "2026-12-04",
        "primary_deadline_at": _dt(2026, 12, 4, 12, 0),
        "anchor_date": date(2026, 12, 4),
        "online_deadline": VerifiedRuleFact(
            rule_key="online_deadline",
            label="校內線上報名截止日",
            value_text="依 2026-09-05 簡章第 2 頁：2026/11/16 09:00 至 12/04 12:00（中午）於新版系統完成線上報名；官網已更新 2026/10/22 姐妹校列表（116exchangeschoollist-1022.pdf，較 10/13 版移除 EDHEC 後共 214 列；青年圓夢成果展非交換甄選變更）",
            verification_status="verified_current",
            exact_deadline_at=_dt(2026, 12, 4, 12, 0),
            submission_mode="online",
            source_title="國立中央大學 116 學年度第 1 梯次交換學生甄選簡章與 2026-10-22 姐妹校列表 PDF",
            source_url="https://oia.ncu.edu.tw/static/file/26/1026/img/277/116exchangenotice.pdf",
            last_checked_at="2026-10-27",
        ),
        "paper_deadline": VerifiedRuleFact(
            rule_key="paper_deadline",
            label="紙本繳件截止日／送件規定",
            value_text="學生須於 2026/12/11（五）17:00 前將完成簽核的紙本申請資料繳交至所屬系所辦公室；系所彙整後於 2026/12/18（五）17:00 前送達國際處",
            verification_status="verified_current",
            exact_deadline_at=_dt(2026, 12, 11, 17, 0),
            submission_mode="paper_required",
            source_title="國立中央大學 116 學年度第 1 梯次交換學生甄選簡章 PDF",
            source_url="https://oia.ncu.edu.tw/static/file/26/1026/img/277/116exchangenotice.pdf",
            last_checked_at="2026-10-21",
        ),
        "study_plan_limit": VerifiedRuleFact(
            rule_key="study_plan_limit",
            label="讀書計畫字數／頁數上限",
            value_text="本梯次簡章的校內繳件清單未列讀書計畫或自傳；如系所或合作校另有要求，須依其規定準備。返校心得另要求至少 800–1500 字與至少 4 張照片，不能當作申請時的讀書計畫規格。",
            verification_status="verified_current",
            source_title="國立中央大學 116 學年度第 1 梯次交換學生甄選簡章 PDF",
            source_url="https://oia.ncu.edu.tw/static/file/26/1026/img/277/116exchangenotice.pdf",
            last_checked_at="2026-10-21",
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
        "window_status": "pending_exact_date",
        "window_badge": "年度慣例12月申請 · 116學年度確切日程待確認",
        "cycle_label": "116學年度校級交換日程待確認；10/29為說明會",
        "primary_deadline_date": None,
        "primary_deadline_at": None,
        "anchor_date": date(2026, 12, 10),
        "online_deadline": VerifiedRuleFact(
            rule_key="online_deadline", label="校內線上報名期限",
            value_text="Step1一般期程列每年12/01–12/10及06/01–06/14，假日順延；流程總頁仍列115學年度。116學年度正式簡章、當期名額與收件時刻仍未核得，不能由慣例產生09:00或17:00截止。10/29 12:00–13:00為科技大樓B2說明會（p/406-1032-157886,r2255.php）。",
            submission_mode="pending_notice",
            source_title="臺北科大Step1與申請流程頁",
            source_url="https://oia.ntut.edu.tw/p/412-1032-9238.php?Lang=zh-tw",
            last_checked_at="2026-10-27", verification_status="needs_confirmation",
        ),
        "paper_deadline": VerifiedRuleFact(
            rule_key="paper_deadline", label="初審送件方式",
            value_text="校級交換先在Step1連結的平台填報，再將簽名申請表及文件上傳至電子郵件所給的指定連結；初審不收紙本，也不收直接寄到公用信箱的申請件。千葉大學設計學院申請另送院辦，行前核章及返國獎助核銷另依Step3。",
            submission_mode="signed_scan_upload",
            source_title="臺北科大Step1交換及獎學金申請文件",
            source_url="https://oia.ntut.edu.tw/p/412-1032-9238.php?Lang=zh-tw",
            last_checked_at="2026-10-21", verification_status="verified_reference",
        ),
        "study_plan_limit": VerifiedRuleFact(
            rule_key="study_plan_limit", label="校級初審研修計畫上限",
            value_text="一般交換研修計畫限1頁A4，不必逐校撰寫，建議英文。學海惜珠另需中文1–2頁動機及1000–1500字計畫；返國心得屬不同階段，不能算入申請篇幅。",
            max_pages=1,
            source_title="臺北科大Step1研修計畫及學海惜珠文件",
            source_url="https://oia.ntut.edu.tw/p/412-1032-9238.php?Lang=zh-tw",
            last_checked_at="2026-10-21", verification_status="verified_reference",
        ),
    },
    {
        "school_id": "nycu",
        "in_ten_week_window": True,
        "window_status": "open",
        "window_badge": "台聯大UST 12/31 16:00電子郵件收件 · 校級新期日程待確認",
        "cycle_label": "116年度第一梯次臺灣聯大交換；校級116學年度另查",
        "primary_deadline_date": "2026-12-31",
        "primary_deadline_at": _dt(2026, 12, 31, 16, 0),
        "anchor_date": date(2026, 12, 31),
        "online_deadline": VerifiedRuleFact(
            rule_key="online_deadline", label="台聯大UST電子郵件收件截止",
            value_text="國際處2026-10-07發布「116學年度台灣聯合大學系統交換計畫第一梯次」，須於2026/12/31（週四）16:00前將完整申請PDF寄至承辦信箱ex-out@nycu.edu.tw，不接受事後補件（UST送各校薦送的01/11不是陽明交大學生期限）；2026-10-13另轉知政大辦理「2027 台灣–阿聯青年交流計畫」（補助機票與食宿）。官網列表目前尚未公布陽明交大自身116學年校級出國交換簡章（最近一則校級為115學年第二梯次，07/10已截止）。",
            exact_deadline_at=_dt(2026, 12, 31, 16, 0), submission_mode="online",
            source_title="陽明交大116學年度台灣聯合大學系統交換計畫第一梯次公告（2026-10-07）",
            source_url="https://oia.nycu.edu.tw/oia/ch/app/data/view?module=nycu0006&id=286&serno=8ee14cf9-321b-46af-9871-9d154c9e6647",
            last_checked_at="2026-10-27", verification_status="verified_current",
        ),
        "paper_deadline": VerifiedRuleFact(
            rule_key="paper_deadline", label="UST簽名及電子送件方式",
            value_text="UST申請表電腦繕打後列印親簽，將全部文件以PDF寄至承辦信箱；每種交換類別最多2志願，學期與暑期各填一份。校級115梯次則上傳本人、導師／指導教授、系主任／所長三處簽章的簽核表；不能加上家長或院長，也不能當116最新版。",
            exact_deadline_at=_dt(2026, 12, 31, 16, 0), submission_mode="signed_scan_upload",
            source_title="陽明交大UST公告與115學年度校級簽核表（歷史參考）",
            source_url="https://oia.nycu.edu.tw/oia/ch/app/data/view?module=nycu0006&id=286&serno=8ee14cf9-321b-46af-9871-9d154c9e6647",
            last_checked_at="2026-10-26", verification_status="verified_reference",
        ),
        "study_plan_limit": VerifiedRuleFact(
            rule_key="study_plan_limit", label="依UST／校級計畫分別準備研修計畫",
            value_text="UST使用附件研修學習計畫書，含申請動機、短期及長期計畫，欄位不足可延伸；另繳CV與一封教授英文推薦函。校級115簡章則要求中文研修計畫（含擬修課列表）與中文自傳，未列固定字數或頁數，不能改成中英文各一份。116校級新規格待確認。",
            source_title="陽明交大UST附件與115學年度校級申請簡章",
            source_url="https://oia.nycu.edu.tw/oia/ch/app/data/doc?module=nycu0006&detailNo=1442785684455690240&type=s",
            last_checked_at="2026-10-26", verification_status="verified_reference",
        ),
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
            verification_status="verified_current",
            rule_key="online_deadline",
            label="校內線上報名截止日",
            value_text="2026/11/01 至 2026/12/24（四）16:30 止（雖公告標題寫即日起，正文載明系統開放及收件為 11/1–12/24 16:30；線上系統 http://outgoing.oie.fju.edu.tw/ 限校內網路使用，名額及開放學校將於 11 月陸續更新，不能當成最終版）",
            exact_deadline_at=_dt(2026, 12, 24, 16, 30),
            submission_mode="online",
            source_title="天主教輔仁大學 116 學年度第 1 學期（2027 秋季班）赴姊妹校交換學生申請公告（newsID=1062）",
            source_url="https://iscoie.fju.edu.tw/newsDetail.jsp?newsID=1062&newsClassID=14",
            last_checked_at="2026-10-27",
        ),
        "paper_deadline": VerifiedRuleFact(
            verification_status="verified_current",
            rule_key="paper_deadline",
            label="紙本繳件截止日／送件規定",
            value_text="紙本申請表須電腦繕打、雙面列印，由本人與監護人親簽並完成所屬系所、學院及適用之雙主修／輔系／學程核章，於2026/12/24 16:30前交至國際學生中心；其餘書審、成績單與語測證明上傳PDF。",
            exact_deadline_at=_dt(2026, 12, 24, 16, 30),
            submission_mode="paper_required",
            source_title="天主教輔仁大學 116 學年度第 1 學期（2027 秋季班）赴姊妹校交換學生申請公告与申請表（newsID=1062、file=1345）",
            source_url="https://iscoie.fju.edu.tw/newsDetail.jsp?newsID=1062&newsClassID=14",
            last_checked_at="2026-10-21",
        ),
        "study_plan_limit": VerifiedRuleFact(
            verification_status="verified_current",
            rule_key="study_plan_limit",
            label="讀書計畫字數／頁數上限",
            value_text="116-1書審資料合併為單一PDF，每個上傳檔案不超過20MB；中文讀書計畫至少500字、格式不拘、兩頁為限，中文簡歷亦以兩頁為限。其他附件依公告分類另行上傳。",
            min_chars=500,
            max_pages=2,
            source_title="天主教輔仁大學 116 學年度第 1 學期（2027 秋季班）赴姊妹校交換學生申請公告（newsID=1062）",
            source_url="https://iscoie.fju.edu.tw/newsDetail.jsp?newsID=1062&newsClassID=14",
            last_checked_at="2026-10-21",
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
            last_checked_at="2026-10-27",
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
            value_text="國際處校內申請選送須知說明讀書計畫可用中文、格式不限，1 頁即可；這是準備指引，不能改寫為禁止超過 1 頁的硬性上限。合作校另有要求時須分別確認。",
            source_title="長庚大學學生赴境外學校進修交流作業要點與甄選說明",
            source_url="https://www.cgu.edu.tw/oia-ch/Contents?nodeId=15656",
            last_checked_at="2026-10-21",
        ),
    },
    {
        "school_id": "fcu",
        "in_ten_week_window": False,
        "window_status": "pending_exact_date",
        "window_badge": "115-1選送已截止 · 後續梯次日期待核實",
        "cycle_label": "115-1選送（2027春季班）；後續梯次待核實",
        "primary_deadline_date": None,
        "primary_deadline_at": None,
        "anchor_date": date(2026, 10, 21),
        "online_deadline": VerifiedRuleFact(
            rule_key="online_deadline", label="校內線上報名截止日",
            value_text="官方系統及115-1簡章列2026/07/27至08/10 17:00，該梯次已截止。一般介紹僅列每年6月中、12月中公告簡章，申請約1至1.5個月；不能推定下一期為2027/01/15 17:00，也未由本輪來源核實11/16–11/20說明會日期。日台交流協會獎學金原訂2026/10/27 10:00校內期限已到，官網公告列表（oia.fcu.edu.tw/announcements-list/）移除條目且詳頁為空，保留10/26核實基準並標註10/27 10:00期限已到，不推論取消或改期。",
            submission_mode="pending_notice", verification_status="needs_confirmation",
            source_title="逢甲官方研修查詢系統及出國研修介紹（含日台獎學金10/27 10:00期限紀錄）",
            source_url="https://oiasap.fcu.edu.tw/", last_checked_at="2026-10-27",
        ),
        "paper_deadline": VerifiedRuleFact(
            rule_key="paper_deadline", label="115-1紙本／簽章規定（已截止梯次參考）",
            value_text="115-1採線上報名、免繳紙本；家長同意書及研究生指導教授同意書須親筆簽名後掃描，獎懲紀錄須生輔組核章後掃描。下一期規定待當期簡章確認。",
            submission_mode="signed_scan_upload", verification_status="verified_reference",
            source_title="逢甲115-1出國研修簡章，第3–4頁",
            source_url=FCU_REVIEWED_GUIDELINES_URL, last_checked_at="2026-10-21",
        ),
        "study_plan_limit": VerifiedRuleFact(
            rule_key="study_plan_limit", label="115-1研修計畫規格（已截止梯次參考）",
            value_text="115-1簡章列中文或英文均可、至少1,000字；包含自傳、動機、出國前後學習計畫，多個志願須分校簡述。下一期是否沿用待確認。",
            min_chars=1000, verification_status="verified_reference",
            source_title="逢甲115-1出國研修簡章，第4頁",
            source_url=FCU_REVIEWED_GUIDELINES_URL, last_checked_at="2026-10-21",
        ),
    },
    {
        "school_id": "ccu",
        "in_ten_week_window": False,
        "window_status": "closed_current_round",
        "window_badge": "2027 春季三梯次已於 09/21 截止 · 後續梯次待核實",
        "cycle_label": "2027 春季班（115-2）校級薦外交換（三梯次已於 09/21 截止）",
        "primary_deadline_date": "2026-09-21",
        "primary_deadline_at": _dt(2026, 9, 21, 17, 0),
        "anchor_date": date(2026, 9, 21),
        "online_deadline": VerifiedRuleFact(
            rule_key="online_deadline",
            label="校內線上報名截止日",
            value_text="2027 春季班第 1–3 梯次線上申請已分別於 2026/08/26、09/06、09/20 23:59 截止；此紀錄只適用上述春季梯次，後續梯次尚待本輪核實",
            exact_deadline_at=_dt(2026, 9, 20, 23, 59),
            submission_mode="online",
            source_title="國立中正大學國際事務處—2027 春季校級薦外交換公告",
            source_url="https://oia.ccu.edu.tw/p/406-1008-93586,r1714.php?Lang=zh-tw",
            last_checked_at="2026-10-27",
            verification_status="verified_reference",
        ),
        "paper_deadline": VerifiedRuleFact(
            rule_key="paper_deadline",
            label="紙本繳件截止日／送件規定",
            value_text="線上申請與紙本送件兩項均須完成（2027 春季班第 1–3 梯次紙本已分別於 2026/08/27、09/07、09/21 17:00 截止）",
            exact_deadline_at=_dt(2026, 9, 21, 17, 0),
            submission_mode="paper_required",
            source_title="國立中正大學 2027 春季出國交換甄選簡章 PDF",
            source_url="https://oia.ccu.edu.tw/var/file/8/1008/attach/78/pta_54384_797227_45763.pdf",
            last_checked_at="2026-10-21",
            verification_status="verified_reference",
        ),
        "study_plan_limit": VerifiedRuleFact(
            rule_key="study_plan_limit",
            label="讀書計畫字數／頁數上限",
            value_text="公告要求每個志願一份研修計畫；簡章允許中文或英文，包含自傳、讀書計畫與申請動機，格式不限、每項約 A4 一頁。「約一頁」為準備指引，未列硬性三頁上限",
            source_title="國立中正大學 2027 春季出國交換甄選簡章（申請文件）",
            source_url="https://oia.ccu.edu.tw/var/file/8/1008/attach/78/pta_54384_797227_45763.pdf",
            last_checked_at="2026-10-21",
            verification_status="verified_reference",
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
            value_text="2027–2028 日語組第二次聯合甄選已於 2026/09/30 12:00 截止；11/06 說明會報名額滿可候補（enroll.tku.edu.tw/course.aspx?cid=auix1106），僅為說明會活動名額，不是交換名額額滿；本輪所查列表未取得2027–2028英歐語組與赴大陸／港澳交換新版簡章，不推論官方尚未發布",
            exact_deadline_at=_dt(2026, 9, 30, 12, 0),
            submission_mode="online",
            source_title="淡江大學國際暨兩岸事務處—最新交換生計畫公告列表",
            source_url="https://oieie.tku.edu.tw/oieie/?page_id=55",
            last_checked_at="2026-10-27",
        ),
        "paper_deadline": VerifiedRuleFact(
            rule_key="paper_deadline",
            label="紙本繳件截止日／送件規定",
            value_text="申請表本人與系主任簽名後，連同文件依各系所指定期限送系所，經系所／學院初審再送國際處。更正公告的09/30中午是線上申請期限；本輪未核實各系紙本或系所送國際處的新截止，不能直接沿用線上時刻。",
            submission_mode="paper_required",
            source_title="淡江大學 2027–2028 年赴日本姊妹校（日語組）第二次聯合甄選更正公告",
            source_url="https://oieie.tku.edu.tw/oieie/?tkuisotope=%e6%9b%b4%e6%ad%a32027-2028%e5%b9%b4%e8%b5%b4%e6%97%a5%e6%9c%ac%e5%a7%8a%e5%a6%b9%e6%a0%a1%e6%97%a5%e8%aa%9e%e7%b5%84-%e4%ba%a4%e6%8f%9b%e7%94%9f%e7%ac%ac%e4%ba%8c%e6%ac%a1%e8%81%af%e5%90%88",
            last_checked_at="2026-10-21", verification_status="needs_confirmation",
        ),
        "study_plan_limit": VerifiedRuleFact(
            rule_key="study_plan_limit",
            label="讀書計畫字數／頁數上限",
            value_text="申請表、成績單、語言證明、推薦函、中日文自傳與研習計畫、切結書及其他證明，以 A4單面列印全部文件合計不超過16頁；不是研習計畫單篇16頁上限",
            source_title="淡江大學 2027–2028 年赴日本姊妹校（日語組）第二次聯合甄選作業簡章",
            source_url="https://oieie.tku.edu.tw/oieie/?tkuisotope=%e6%aa%a2%e9%80%812027-2028%e5%b9%b4%e8%b5%b4%e6%97%a5%e6%9c%ac%e5%a7%8a%e5%a6%b9%e6%a0%a1%e6%97%a5%e8%aa%9e%e7%b5%84-%e4%ba%a4%e6%8f%9b%e7%94%9f%e7%ac%ac%e4%ba%8c%e6%ac%a1%e8%81%af%e5%90%88",
            last_checked_at="2026-10-21",
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
                "[淡江交換] 2027–2028 赴姊妹校交換生聯合甄選說明會報名截止（17:00；11/06 18:00–19:30 舉辦，額滿可候補）",
                "2026-11-05",
                "說明會報名截止",
                "home",
                "2027–2028 交換甄選說明會於 2026/11/06 18:00–19:30 在驚聲國際會議廳舉行，11/05 17:00 報名截止（說明會額滿可候補，非交換名額額滿、亦非交換申請截止）",
                "https://enroll.tku.edu.tw/course.aspx?cid=auix1106",
            ),
        ],
    },
    {
        "school_id": "ntust",
        "in_ten_week_window": True,
        "window_status": "upcoming",
        "window_badge": "116-1歐美亞澳 12/07 15:00截止",
        "cycle_label": "116-1（2027秋季）歐美亞澳交換（_中文_20260915.pdf，主系統已恢復讀取）；大陸組簡章另核",
        "primary_deadline_date": "2026-12-07",
        "primary_deadline_at": _dt(2026, 12, 7, 15, 0),
        "anchor_date": date(2026, 12, 7),
        "online_deadline": VerifiedRuleFact(
            rule_key="online_deadline", label="校內線上報名截止日",
            value_text="116-1海外交換簡章（_中文_20260915.pdf，歐美亞〔不含大陸〕澳）2026/12/03 10:00至12/07 15:00線上填報；主系統（stu88/fall2027）10/27恢復讀取且同10/22基準，當期正式名額待開放核對，語檢段落差異待確認。",
            exact_deadline_at=_dt(2026, 12, 7, 15, 0), submission_mode="online",
            source_title="臺科大116-1海外交換生報名系統與簡章（_中文_20260915.pdf）",
            source_url="https://stu88.ntust.edu.tw/outboundstudent/index/index/puid/fall2027",
            last_checked_at="2026-10-27", verification_status="verified_current",
        ),
        "paper_deadline": VerifiedRuleFact(
            rule_key="paper_deadline", label="紙本繳件規定",
            value_text="116-1歐美亞澳校內甄選全程線上，不需另外繳紙本至國際處；研究生須上傳指導教授已簽名同意書。接待校入學階段文件另備。",
            submission_mode="paperless", source_title="臺科大116-1甄選簡章第2–3頁",
            source_url="https://oia.ntust.edu.tw/p/405-1060-62102,c9056.php?Lang=zh-tw",
            last_checked_at="2026-10-26", verification_status="verified_current",
        ),
        "study_plan_limit": VerifiedRuleFact(
            rule_key="study_plan_limit", label="讀書計畫篇幅指引",
            value_text="中、英文讀書計畫各約1–2頁，合併一檔；中、英文自傳另各約1–2頁並合併另一檔。限未加密PDF，沒有硬性兩頁上限。",
            source_title="臺科大116-1甄選簡章第3頁",
            source_url="https://oia.ntust.edu.tw/p/405-1060-62102,c9056.php?Lang=zh-tw",
            last_checked_at="2026-10-26", verification_status="verified_current",
        ),
    },
]


def _build_card(spec: dict[str, Any]) -> VerifiedSchoolWindowCard:
    profile = require_university(spec["school_id"])
    online_rule: VerifiedRuleFact = spec["online_deadline"]
    paper_rule: VerifiedRuleFact = spec["paper_deadline"]
    study_plan_rule: VerifiedRuleFact = spec["study_plan_limit"]
    # An internal planning anchor is not an official deadline. In particular,
    # pending cards must never turn the anchor into a "formal deadline" event.
    has_deadline = spec["primary_deadline_date"] is not None
    subtasks = _build_subtasks(
        school_id=profile.id,
        short_name=profile.short_name,
        anchor_date=spec["anchor_date"],
        online_rule=online_rule,
        paper_rule=paper_rule,
        study_plan_rule=study_plan_rule,
        extra_milestones=spec.get("extra_milestones"),
        deadline_event_title=spec.get("deadline_event_title", "校內申請正式截止日（防漏最後確認）"),
    ) if has_deadline else []
    primary_date = spec["primary_deadline_date"]
    event_title = spec.get("deadline_event_title", "校內申請截止與備審防漏提醒")
    gcal_title = f"[{profile.short_name}交換] {event_title}"
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
    ) if has_deadline else None
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
        ics_download_url=f"/calendar/school-window.ics?school={profile.id}" if has_deadline else None,
        google_calendar_url=google_calendar_url,
        line_oa_url=_line_oa_url(line_msg),
        line_copy_summary=line_msg,
    )


_CARDS_BY_ID: dict[str, VerifiedSchoolWindowCard] = {
    spec["school_id"]: _build_card(spec) for spec in _RAW_SPECS
}

# These are explicit gaps discovered by the 2026-10-21 source review, not
# invented verified deadlines. The cited pages' scope is described per fact.
_REVIEW_GAPS = {
    "nkust": (
        "https://oia.nkust.edu.tw/unit-4-374-21.html",
        "高科大116學年度校級出國交換甄選頁及出國研修說明會行事曆",
        "官網交換頁（unit-4-374-21.html）已公布116學年度校級出國交換甄選時程：線上申請115/11/09 12:00開放、115/12/01 16:00截止，正式外語成績115/12/27 16:00前補交，116/02/01–02/12審查、116/02/22 16:00公告結果；官網首頁行事曆另載2026-10-28「116學年度出國研修說明會_建工校區」（news_det-980.html另載五校區場次），學海飛颺名額視當年經費而定，請以學校官方公告為準。",
        "needs_confirmation",
    ),
    "yuntech": (
        "https://admissions-oia.yuntech.edu.tw/oe/index/index/puid/115-2/lang/zh_TW",
        "雲科大115-2非大陸地區交換申請系統",
        "所附系統為115-2非大陸地區交換，線上及紙本皆於2026/09/24中午12:00截止；不支持116-1的預估日期，下一梯次待核實。",
        "needs_confirmation",
    ),
    "ntou": (
        "https://oia.ntou.edu.tw/p/412-1022-6958.php?Lang=zh-tw",
        "海洋大學赴外交換學生計畫",
        "官方頁列2027春／秋季學期校內報名於2026/05/08中午12:00截止；無法據此將日期順延為2027年，後續梯次待核實。",
        "needs_confirmation",
    ),
}


def _build_review_gap_card(school_id: str) -> VerifiedSchoolWindowCard:
    url, title, deadline_note, status = _REVIEW_GAPS[school_id]
    profile = require_university(school_id)
    notes = {
        "online_deadline": ("校內線上報名截止日", deadline_note),
        "paper_deadline": (
            "紙本繳件截止日／送件規定",
            "本平台尚未核實下一梯次紙本、簽章或電子送件規定，請向母校確認；目前不建立日期提醒。",
        ),
        "study_plan_limit": (
            "讀書計畫字數／頁數上限",
            "本平台尚未核實下一梯次是否要求讀書計畫及其篇幅；不能將未查得上限解讀為不限字數。",
        ),
    }
    facts = {
        key: VerifiedRuleFact(
            rule_key=key, label=label, value_text=note,
            submission_mode="pending_notice", source_title=title,
            source_url=url, last_checked_at="2026-10-21",
            verification_status=status,
        )
        for key, (label, note) in notes.items()
    }
    if school_id == "nkust":
        from .nkust_source_review import DOCS, GUIDELINES
        facts["paper_deadline"] = VerifiedRuleFact(
            rule_key="paper_deadline", label="115校級送件參考／116待確認",
            value_text=DOCS[0] + "116及院系級另依公告，不套用歷史截止。",
            submission_mode="signed_scan_upload", source_title="高科大115校級簡章第2–3頁",
            source_url=GUIDELINES, last_checked_at="2026-10-21", verification_status="verified_reference")
        facts["study_plan_limit"] = VerifiedRuleFact(
            rule_key="study_plan_limit", label="115學海惜珠專用計畫",
            value_text=DOCS[2] + "不作116或一般交換共用字數。",
            source_title="高科大115校級簡章第3頁", source_url=GUIDELINES,
            last_checked_at="2026-10-21", verification_status="verified_reference")
    if school_id == "yuntech":
        from .yuntech_source_review import DOCS, GUIDELINES, MAINLAND_DOCS, PORTAL
        facts["paper_deadline"] = VerifiedRuleFact(
            rule_key="paper_deadline", label="115-2送件歷史參考",
            value_text=DOCS[0] + MAINLAND_DOCS[0] + "116確切期限待核實。",
            source_title="雲科大115-2系統及赴陸公告", source_url=PORTAL,
            last_checked_at="2026-10-21", verification_status="verified_reference")
        facts["study_plan_limit"] = VerifiedRuleFact(
            rule_key="study_plan_limit", label="計畫語言與未核實篇幅",
            value_text=DOCS[2], source_title="雲科大113交換要點第3點",
            source_url=GUIDELINES, last_checked_at="2026-10-21", verification_status="needs_confirmation")
    if school_id == "ntou":
        from .ntou_source_review import BROCHURE, DOCS, MAINLAND_DOCS
        facts["paper_deadline"] = VerifiedRuleFact(
            rule_key="paper_deadline", label="已截止梯次送件參考",
            value_text=DOCS[0] + MAINLAND_DOCS[0], source_title="海大2027簡章及115-2赴陸公告",
            source_url=BROCHURE, last_checked_at="2026-10-21", verification_status="verified_reference")
        facts["study_plan_limit"] = VerifiedRuleFact(
            rule_key="study_plan_limit", label="計畫語言及未核實篇幅",
            value_text=DOCS[1] + DOCS[3], source_title="海大2027簡章第3–4頁",
            source_url=BROCHURE, last_checked_at="2026-10-21", verification_status="needs_confirmation")
    return VerifiedSchoolWindowCard(
        school_id=profile.id, school_name=profile.school_name, short_name=profile.short_name,
        in_ten_week_window=False, window_status="pending_exact_date",
        window_badge="當期規定待核實", cycle_label="下一梯次校內交換甄選：尚未核實",
        **facts, subtasks=[], ics_download_url=None, google_calendar_url=None,
        line_oa_url=_line_oa_url(f"{profile.school_name}下一梯次交換規定待核實"),
        line_copy_summary=f"{profile.school_name}：{deadline_note} 查詢來源：{url}",
    )


_CARDS_BY_ID.update({key: _build_review_gap_card(key) for key in _REVIEW_GAPS})


def _build_fallback_card(school_id: str) -> VerifiedSchoolWindowCard:
    profile = require_university(school_id)
    source_url = profile.official_url if profile.official_url.startswith("https://") else "https://app.uniway-tw.com/"
    fallback_spec: dict[str, Any] = {
        "school_id": profile.id,
        "in_ten_week_window": True,
        "window_status": "pending_exact_date",
        "window_badge": "依國際處當期簡章公告時程辦理",
        "cycle_label": f"{profile.school_name} 出國交換學生甄選（請依國際處最新公告時程確認）",
        "primary_deadline_date": None,
        "primary_deadline_at": None,
        "anchor_date": date(2026, 11, 30),
        "online_deadline": VerifiedRuleFact(
            rule_key="online_deadline",
            label="校內線上報名截止日",
            value_text=f"請依{profile.school_name}國際事務處當期出國交換甄選簡章公告之線上報名截止時程辦理",
            exact_deadline_at=None,
            submission_mode="online",
            source_title=f"{profile.school_name}國際事務處官方交換生專頁",
            source_url=source_url,
            last_checked_at=CATALOG_LAST_CHECKED_AT,
        ),
        "paper_deadline": VerifiedRuleFact(
            rule_key="paper_deadline",
            label="紙本繳件截止日／送件規定",
            value_text=f"請依{profile.school_name}當期交換簡章確認是否須列印紙本申請表完成系所核章後送交國際處",
            exact_deadline_at=None,
            submission_mode="pending_notice",
            source_title=f"{profile.school_name}國際事務處官方交換生專頁",
            source_url=source_url,
            last_checked_at=CATALOG_LAST_CHECKED_AT,
        ),
        "study_plan_limit": VerifiedRuleFact(
            rule_key="study_plan_limit",
            label="讀書計畫字數／頁數上限",
            value_text=f"請依{profile.school_name}當期交換生甄選簡章規定準備中、外文讀書計畫與自傳（建議篇幅約 1–2 頁 A4）",
            max_pages=2,
            source_title=f"{profile.school_name}國際事務處官方交換生專頁",
            source_url=source_url,
            last_checked_at=CATALOG_LAST_CHECKED_AT,
        ),
    }
    return _build_card(fallback_spec)


def get_verified_school_window_card(school: str) -> VerifiedSchoolWindowCard:
    profile = require_university(school)
    card = _CARDS_BY_ID.get(profile.id)
    if card is None:
        card = _build_fallback_card(profile.id)
        _CARDS_BY_ID[profile.id] = card
    return card


def build_verified_window_deadline_catalog(
    school: str | None = None,
) -> VerifiedWindowDeadlineCatalog:
    all_items = [get_verified_school_window_card(u.id) for u in SUPPORTED_UNIVERSITIES]
    if school:
        items = [get_verified_school_window_card(school)]
    else:
        items = all_items
    ten_week_count = sum(1 for item in all_items if item.in_ten_week_window)
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
