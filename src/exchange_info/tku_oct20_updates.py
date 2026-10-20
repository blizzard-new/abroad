"""Verified 2026-10-20 morning TKU official announcement updates.

Adds two newly captured official announcements on https://oieie.tku.edu.tw/ (published
2026-10-19, absent from the 2026-10-19 morning homepage snapshot, full body & attachments
verified on 2026-10-20):
1. 2027–2028 年赴姊妹校交換生聯合甄選說明會:
   - Event time: 2026/11/06 (Fri) 18:00–19:30 at 驚聲國際會議廳 (Ching-sheng International Conference Hall, cap 170)
   - Registration deadline: 2026/11/05 17:00 via https://enroll.tku.edu.tw/course.aspx?cid=auix1106
   - Scope boundary: Selection briefing event registration only, NOT an exchange application deadline.
2. 2027 年度第一期日本台灣交流協會獎學金（短期留學生）:
   - Internal TKU submission deadline: 2026/10/30 (to 國際處交流組 驚聲大樓 T1006 室)
   - Monthly stipend: JPY 80,000 (up to 12 months)
   - Scope boundary: Restricted to Taiwan nationals under age 35, Japan-related research,
     previous academic year evaluation coefficient >= 2.30, and exchange starting April–August 2027.
     Does NOT apply to all Japan-bound exchange students or dual-degree students.
   - Announcement + 4 official PDF attachments verified.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from .models import ProcessedPage, SourceReference, StudentInfoItem

ROOT = Path(__file__).resolve().parents[2]
UPDATE_JSON_PATH = ROOT / "sources" / "tku" / "2026-10-20-official-update.json"

CHECKED_DATE = "2026-10-20"
CHECKED_AT_ISO = "2026-10-20T02:26:00+00:00"
INFO_SESSION_URL = "https://enroll.tku.edu.tw/course.aspx?cid=auix1106"
OIEIE_HOME_URL = "https://oieie.tku.edu.tw/"


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def load_tku_oct20_update_payload(update_json_path: Path = UPDATE_JSON_PATH) -> dict[str, Any]:
    payload = json.loads(update_json_path.read_text(encoding="utf-8"))
    if payload.get("school_id") != "tku":
        raise ValueError("Invalid TKU Oct 20 update payload school_id")
    if payload.get("treated_as_exchange_application_deadline") is not False:
        raise ValueError("TKU Oct 20 updates must not be treated as exchange application deadlines")
    if payload.get("applies_to_all_japan_exchange_students") is not False:
        raise ValueError("JTEA short-term scholarship does not apply to all Japan-bound exchange students")
    return payload


def validate_tku_oct20_update_snapshot(update_json_path: Path = UPDATE_JSON_PATH) -> dict[str, Any]:
    payload = load_tku_oct20_update_payload(update_json_path)
    manifest = payload["source_manifest"]
    if len(manifest) != 8:
        raise ValueError(f"Expected 8 archived TKU Oct 20 source files, got {len(manifest)}")
    for key, meta in manifest.items():
        local_path = ROOT / meta["local_file"]
        if not local_path.exists():
            raise FileNotFoundError(f"Missing archived TKU Oct 20 source file for {key}: {local_path}")
        raw = local_path.read_bytes()
        if len(raw) != meta["bytes"]:
            raise ValueError(f"Byte count mismatch for {key}: expected {meta['bytes']}, got {len(raw)}")
        if _sha256_bytes(raw) != meta["sha256"]:
            raise ValueError(f"SHA256 mismatch for {key}: expected {meta['sha256']}")
    return payload


def tku_oct20_program_overview_item() -> StudentInfoItem:
    payload = load_tku_oct20_update_payload()
    info = payload["info_session"]
    return StudentInfoItem(
        title="2027–2028 年赴姊妹校交換生聯合甄選說明會（10/19 公告、10/20 核實）",
        details=[
            "舉辦時間與地點：2026/11/06（五）18:00–19:30，驚聲國際會議廳（正取 170 人）。",
            "報名期間與入口：即日起至 2026/11/05（四）17:00 止，於淡江活動報名系統線上報名（https://enroll.tku.edu.tw/course.aspx?cid=auix1106）。",
            "邊界聲明：此為交換甄選說明會報名截止，不是交換生出國申請截止日；其他語組及全體合作校新版簡章仍待後續查核。",
        ],
        source=SourceReference(
            title=info["title"],
            source_url=info["registration_url"],
            summary="查核2026-10-20；10/19公告、11/6 18:00–19:30舉辦、11/5 17:00報名截止（非交換申請期限）。",
        ),
    )


def tku_oct20_scholarship_item() -> StudentInfoItem:
    payload = load_tku_oct20_update_payload()
    jtea = payload["jtea_scholarship"]
    return StudentInfoItem(
        title="2027 年度第一期日本台灣交流協會獎學金（短期留學生，10/30 校內截止）",
        details=[
            "校內收件截止：2026/10/30（五）前備齊申請表件送至國際處交流組（驚聲大樓 T1006 室，陳靜 分機 3669），由學校統一推薦，個人直接申請不予受理。",
            "獎助內容：每月日幣 8 萬圓（最長一年，依日本交換大學最終留學期間為準）。",
            "適用條件限制：限具台灣籍且未滿 35 歲（1992/4/2 以後出生）、以日本作為研究對象、前一學年度成績評價係數達 2.30 以上，並於 2027 年 4 月至 8 月間開始赴日交換留學者；不是所有赴日交換生都適用，雙聯學位計畫亦非申請對象，且不得重複支領其他政府或機關團體獎學金。",
            "附件核實：已完整核對官方公告及 4 份附件（申請簡章、申請書表格 1、個人推薦書表格 3、成績評價係數換算方法附件 1）。",
        ],
        source=SourceReference(
            title=jtea["title"],
            source_url=jtea["announcement_url"],
            summary="查核2026-10-20；校內截止2026/10/30，每月8萬日圓；限符合國籍、日本相關研究及2027年4–8月開始交換等條件者，非所有赴日交換生皆適用。",
        ),
    )


def tku_oct20_sources() -> list[SourceReference]:
    payload = load_tku_oct20_update_payload()
    manifest = payload["source_manifest"]
    return [
        SourceReference(
            title=manifest["enroll_auix1106"]["title"],
            source_url=manifest["enroll_auix1106"]["url"],
            summary="查核2026-10-20；2027–2028赴姊妹校交換生聯合甄選說明會報名頁（11/6 18:00–19:30舉辦，11/5 17:00報名截止）。",
        ),
        SourceReference(
            title=manifest["oieie_info_session_2027_2028"]["title"],
            source_url=manifest["oieie_info_session_2027_2028"]["url"],
            summary="查核2026-10-20；國際處10/19發布之2027–2028交換甄選說明會公告正文。",
        ),
        SourceReference(
            title=manifest["oieie_jtea_scholarship_2027_1"]["title"],
            source_url=manifest["oieie_jtea_scholarship_2027_1"]["url"],
            summary="查核2026-10-20；2027第一期日本台灣交流協會短期獎學金校內公告（校內截止10/30，每月8萬日圓，附4份PDF附件）。",
        ),
        SourceReference(
            title=manifest["jtea_2027_1_guidelines"]["title"],
            source_url=manifest["jtea_2027_1_guidelines"]["url"],
            summary="查核2026-10-20；2027第一期日本台灣交流協會短期留學生獎學金申請簡章PDF（4頁）。",
        ),
    ]


def tku_oct20_processed_pages() -> list[ProcessedPage]:
    payload = load_tku_oct20_update_payload()
    manifest = payload["source_manifest"]
    info = payload["info_session"]
    jtea = payload["jtea_scholarship"]
    return [
        ProcessedPage(
            title=f"淡江 {info['title']}",
            source_url=info["registration_url"],
            text=(
                f"{info['title']}\n"
                f"公告日期：{info['published_date']}（2026-10-20 取得正文與報名頁核實）\n"
                "活動時間：2026/11/06（五）18:00–19:30\n"
                f"活動地點：{info['venue']}（正取 {info['capacity']} 人）\n"
                "報名期間：2026/10/16 08:00 至 2026/11/05 17:00\n"
                f"官方報名頁：{info['registration_url']}\n"
                f"官方公告頁：{info['announcement_url']}\n"
                "邊界聲明：本項為交換甄選說明會報名，不是交換申請截止日。"
            ),
            summary="2027–2028 交換甄選說明會：11/6 18:00–19:30，報名截止 11/5 17:00；查核2026-10-20。",
            category="info_session",
            crawled_at=CHECKED_DATE,
            content_hash=manifest["enroll_auix1106"]["sha256"],
        ),
        ProcessedPage(
            title=f"淡江 {jtea['title']}",
            source_url=jtea["announcement_url"],
            text=(
                f"{jtea['title']}\n"
                f"校內截止：{jtea['internal_deadline_date']}（送交 {jtea['submission_office']}）\n"
                f"獎學金金額：每月 {jtea['monthly_stipend_jpy']} 日圓（最長 {jtea['max_duration_months']} 個月）\n"
                "申請資格與條件限制：\n- "
                + "\n- ".join(jtea["eligibility_conditions"])
                + "\n邊界聲明：限符合國籍、日本相關研究、成績評價係數 2.30 以上及 2027 年 4–8 月開始交換等條件者，不是所有赴日交換生都適用。公告與四份附件已核對。"
            ),
            summary="2027 第一期日本台灣交流協會短期獎學金：校內截止 10/30，每月 8 萬日圓，限特定條件赴日交換生；查核2026-10-20。",
            category="scholarship",
            crawled_at=CHECKED_DATE,
            content_hash=manifest["oieie_jtea_scholarship_2027_1"]["sha256"],
        ),
    ]
