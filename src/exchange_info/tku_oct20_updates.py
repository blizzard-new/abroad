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

DEFAULT_TKU_OCT20_UPDATE_PAYLOAD: dict[str, Any] = {
    "format_version": 1,
    "checked_at": "2026-10-20T02:26:00+00:00",
    "school_id": "tku",
    "school_name": "淡江大學",
    "treated_as_exchange_application_deadline": False,
    "applies_to_all_japan_exchange_students": False,
    "other_language_groups_and_all_partners_fully_audited": False,
    "info_session": {
        "title": "2027–2028 年赴姊妹校交換生聯合甄選說明會",
        "published_date": "2026-10-19",
        "captured_date": "2026-10-20",
        "event_start_at": "2026-11-06T18:00:00+08:00",
        "event_end_at": "2026-11-06T19:30:00+08:00",
        "registration_opens_at": "2026-10-16T08:00:00+08:00",
        "registration_deadline_at": "2026-11-05T17:00:00+08:00",
        "venue": "驚聲國際會議廳（Ching-sheng International Conference Hall）",
        "capacity": 170,
        "registration_url": "https://enroll.tku.edu.tw/course.aspx?cid=auix1106",
        "announcement_url": "https://oieie.tku.edu.tw/oieie/?tkuisotope=%e5%9c%8b%e9%9a%9b%e8%99%95%e6%96%bc115%e5%b9%b411%e6%9c%886%e6%97%a5%ef%bc%88%e4%ba%94%ef%bc%89%e8%88%89%e8%be%a6%e3%80%8c2027-2028%e5%b9%b4%e8%b5%b4%e5%a7%8a%e5%a6%b9%e6%a0%a1%e4%ba%a4%e6%8f%9b",
        "treated_as_exchange_application_deadline": False,
    },
    "jtea_scholarship": {
        "title": "2027 年度第一期日本台灣交流協會獎學金（短期留學生）",
        "published_date": "2026-10-19",
        "captured_date": "2026-10-20",
        "internal_deadline_date": "2026-10-30",
        "submission_office": "淡江大學國際處交流組（驚聲大樓 T1006 室，陳靜 分機 3669）",
        "monthly_stipend_jpy": 80000,
        "max_duration_months": 12,
        "enrollment_start_window": "2027-04 to 2027-08",
        "eligibility_conditions": [
            "具台灣籍之台灣各大學院校正規課程在學學生，且 1992 年 4 月 2 日以後出生（未滿 35 歲）。",
            "以日本作為研究對象（人文、社會科學領域於交換結束後以日本研究撰寫畢業論文並取得學位，或自然科學領域以日本為研究對象／與日本研究機關共同研究）。",
            "於 2027 年 4 月至 2027 年 8 月間進入日本交換大學開始交換留學。",
            "前一學年度成績評價係數達 2.30 以上（滿分 3.00）。",
            "支領期間不得重複領取其他政府單位或機關團體獎學金（雙聯學位計畫亦非申請對象）。",
        ],
        "applies_to_all_japan_exchange_students": False,
        "announcement_url": "https://oieie.tku.edu.tw/oieie/?tkuisotope=%e6%aa%a2%e9%80%81%e3%80%8c2027%e5%b9%b4%e5%ba%a6%e7%ac%ac%e4%b8%80%e6%9c%9f%e6%97%a5%e6%9c%ac%e5%8f%b0%e7%81%a3%e4%ba%a4%e6%b5%81%e5%8d%94%e6%9c%83%e7%8d%8e%e5%ad%b8%e9%87%91%ef%bc%88%e7%9f%ad",
        "attachments_verified": 4,
    },
    "source_manifest": {
        "oieie_home_20261020": {
            "source_id": "oieie_home_20261020",
            "title": "淡江大學國際暨兩岸事務處首頁（2026-10-20 查核）",
            "url": "https://oieie.tku.edu.tw/",
            "http_status": 200,
            "checked_at": "2026-10-20T02:26:00+00:00",
            "sha256": "a0ac98a82ec22f29502d12f846ce1151040d5d25f49107eea3ec5a2e48449dcc",
            "bytes": 156289,
            "local_file": "sources/tku/2026-10-20-official/oieie_home_20261020.html",
        },
        "enroll_auix1106": {
            "source_id": "enroll_auix1106",
            "title": "淡江大學活動報名系統：2027-2028年赴姊妹校交換生聯合甄選說明會（cid=auix1106）",
            "url": "https://enroll.tku.edu.tw/course.aspx?cid=auix1106",
            "http_status": 200,
            "checked_at": "2026-10-20T02:26:00+00:00",
            "sha256": "4ee1edcf107f18432301b035998d3573e274072856d95fec623c8000d7027dd2",
            "bytes": 11547,
            "local_file": "sources/tku/2026-10-20-official/enroll_auix1106.html",
        },
        "oieie_info_session_2027_2028": {
            "source_id": "oieie_info_session_2027_2028",
            "title": "國際處於115年11月6日（五）舉辦「2027-2028年赴姊妹校交換生聯合甄選說明會」",
            "url": "https://oieie.tku.edu.tw/oieie/?tkuisotope=%e5%9c%8b%e9%9a%9b%e8%99%95%e6%96%bc115%e5%b9%b411%e6%9c%886%e6%97%a5%ef%bc%88%e4%ba%94%ef%bc%89%e8%88%89%e8%be%a6%e3%80%8c2027-2028%e5%b9%b4%e8%b5%b4%e5%a7%8a%e5%a6%b9%e6%a0%a1%e4%ba%a4%e6%8f%9b",
            "http_status": 200,
            "checked_at": "2026-10-20T02:26:00+00:00",
            "sha256": "28ba3668153ae887430574cddd8fb25bf8c09379f8147c20bb70afade8d765df",
            "bytes": 78146,
            "local_file": "sources/tku/2026-10-20-official/oieie_info_session_2027_2028.html",
        },
        "oieie_jtea_scholarship_2027_1": {
            "source_id": "oieie_jtea_scholarship_2027_1",
            "title": "檢送「2027年度第一期日本台灣交流協會獎學金（短期留學生）」申請簡章及相關表件",
            "url": "https://oieie.tku.edu.tw/oieie/?tkuisotope=%e6%aa%a2%e9%80%81%e3%80%8c2027%e5%b9%b4%e5%ba%a6%e7%ac%ac%e4%b8%80%e6%9c%9f%e6%97%a5%e6%9c%ac%e5%8f%b0%e7%81%a3%e4%ba%a4%e6%b5%81%e5%8d%94%e6%9c%83%e7%8d%8e%e5%ad%b8%e9%87%91%ef%bc%88%e7%9f%ad",
            "http_status": 200,
            "checked_at": "2026-10-20T02:26:00+00:00",
            "sha256": "e8690c4718139936a01c1ff1f6f9ad7331456397b6f189f5c083afaa7b0bc564",
            "bytes": 80078,
            "local_file": "sources/tku/2026-10-20-official/oieie_jtea_scholarship_2027_1.html",
        },
        "jtea_2027_1_guidelines": {
            "source_id": "jtea_2027_1_guidelines",
            "title": "2027年度第一期日本台灣交流協會獎學金(短期留學生)申請簡章",
            "url": "https://oieie.tku.edu.tw/oieie/wp-content/uploads/2026/10/2027年度第一期日本台灣交流協會獎學金短期留學生-簡章.pdf",
            "http_status": 200,
            "checked_at": "2026-10-20T02:26:00+00:00",
            "sha256": "6433617680fc72a98603a02b9c8280413d76cf300b977c2f82a47a2516e5b7ca",
            "bytes": 336140,
            "local_file": "sources/tku/2026-10-20-official/jtea_2027_1_guidelines.pdf",
        },
        "jtea_2027_1_form1_application": {
            "source_id": "jtea_2027_1_form1_application",
            "title": "2027年度第一期日本台灣交流協會獎學金（短期留學生）申請書〔表格1〕",
            "url": "https://oieie.tku.edu.tw/oieie/wp-content/uploads/2026/10/申請書_表格1.pdf",
            "http_status": 200,
            "checked_at": "2026-10-20T02:26:00+00:00",
            "sha256": "f4025e7c6f29d9c81e60aef62e71464cb36e80c47e26daacaf347ede32d22991",
            "bytes": 191932,
            "local_file": "sources/tku/2026-10-20-official/jtea_2027_1_form1_application.pdf",
        },
        "jtea_2027_1_form3_recommendation": {
            "source_id": "jtea_2027_1_form3_recommendation",
            "title": "2027年度第一期日本台灣交流協會獎學金(短期留學生)個人推薦書〔表格3〕",
            "url": "https://oieie.tku.edu.tw/oieie/wp-content/uploads/2026/10/個人推薦書_表格3.pdf",
            "http_status": 200,
            "checked_at": "2026-10-20T02:26:00+00:00",
            "sha256": "d07ba1ac729e7d0074223e19f5d40dfd4ded79bad0d89652a382b7b891126da4",
            "bytes": 81157,
            "local_file": "sources/tku/2026-10-20-official/jtea_2027_1_form3_recommendation.pdf",
        },
        "jtea_2027_1_gpa_calculation": {
            "source_id": "jtea_2027_1_gpa_calculation",
            "title": "成績評價係數換算方法〔附件1〕",
            "url": "https://oieie.tku.edu.tw/oieie/wp-content/uploads/2026/10/成績評價係數換算方法.pdf",
            "http_status": 200,
            "checked_at": "2026-10-20T02:26:00+00:00",
            "sha256": "0ecedbd0df1a337e47aeb242c6307ae5422a25355c4685b5e090a2627c18ac4e",
            "bytes": 101459,
            "local_file": "sources/tku/2026-10-20-official/jtea_2027_1_gpa_calculation.pdf",
        },
    },
}


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def load_tku_oct20_update_payload(update_json_path: Path = UPDATE_JSON_PATH) -> dict[str, Any]:
    if update_json_path.exists():
        payload = json.loads(update_json_path.read_text(encoding="utf-8"))
    else:
        payload = DEFAULT_TKU_OCT20_UPDATE_PAYLOAD
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
