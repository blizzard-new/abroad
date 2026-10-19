"""Apply the reviewed October 19 NTU OIA board announcement without altering selection deadlines or partner rows."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from bs4 import BeautifulSoup

from .models import ExchangeInfo, ProcessedPage, StudentDashboard

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "sources/ntu/2026-10-19-official-update.json"
BOARD_URL = "https://oia.ntu.edu.tw/board/detail/sn/2336"
DASHBOARD_CARD_TITLE = "116年度學海計畫補助要點說明會（非交換申請期限變更）"
PAGE_TITLE = "國立臺灣大學：" + DASHBOARD_CARD_TITLE
EXCHANGE_INFO_BULLET = (
    "116年度學海計畫補助要點說明會（2026-10-19公告，學生與相關系所教授可參加）："
    "報名截止 2026-10-30 17:00，北區場 2026-11-09 13:00–16:00 於國立臺灣科技大學國際大樓 101 會議室"
    "（此為補助說明會，不是交換申請期限變更）。"
)


def load_oct19_update(path: Path = SOURCE) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    if (
        data.get("format_version") != 1
        or data.get("target_round") != "116-1"
        or data.get("target_academic_year") != "2027/2028"
        or any(
            data.get(key) is not False
            for key in (
                "formal_quota_changed",
                "application_open_confirmed",
                "all_current_cycle_fields_verified",
                "unreadable_attachments_treated_as_no_update",
            )
        )
        or data.get("partner_details_and_list_unchanged") is not True
    ):
        raise ValueError("October 19 NTU announcement cannot alter formal quotas or mark unread attachments as unchanged")

    manifest = data.get("source_manifest", {})
    if set(manifest) != {"ntu_board_sn_2336"}:
        raise ValueError("Unexpected October 19 source manifest")
    src = manifest["ntu_board_sn_2336"]
    target = (ROOT / src["local_file"]).resolve()
    if (
        not target.is_relative_to((ROOT / "sources/ntu/2026-10-19-official").resolve())
        or src.get("source_id") != "ntu_board_sn_2336"
        or src.get("url") != BOARD_URL
        or src.get("http_status") != 200
        or not src.get("checked_at")
    ):
        raise ValueError("Invalid October 19 dated source archive")
    raw = target.read_bytes()
    if hashlib.sha256(raw).hexdigest() != src["sha256"]:
        raise ValueError("October 19 original source hash changed")

    text = BeautifulSoup(raw, "html.parser").get_text("", strip=True)
    event = data.get("scholarship_briefing_event", {})
    if (
        event.get("source_id") != "ntu_board_sn_2336"
        or event.get("source_url") != BOARD_URL
        or event.get("registration_deadline") != "2026-10-30T17:00:00+08:00"
        or event.get("treated_as_application_deadline") is not False
        or event.get("reminder_eligible") is not False
        or event.get("home_selection_rule_changed") is not False
        or event.get("northern_session", {}).get("date") != "2026-11-09"
        or event.get("northern_session", {}).get("time") != "13:00–16:00"
        or "國際大樓" not in event.get("northern_session", {}).get("location", "")
        or "101" not in event.get("northern_session", {}).get("location", "")
        or "116年度學海要點說明會開放報名" not in text
        or "國立臺灣科技大學國際大樓" not in text
        or "101" not in text
        or "10月30日" not in text
    ):
        raise ValueError("Scholarship briefing session must remain a non-deadline announcement backed by sn/2336")
    return data


def apply_oct19_updates(bundle: Path, path: Path = SOURCE) -> dict:
    data = load_oct19_update(path)
    event = data["scholarship_briefing_event"]
    card_details = [
        "臺大國際處2026-10-19公告「116年度學海要點說明會開放報名」，歡迎有意出國研修或實習之學生及參與執行選送國外實習計畫之系所教授參加。",
        "報名截止：2026-10-30 17:00（115年10月30日下午5:00前，場地空間有限，依報名先後次序為準；報名連結：https://reurl.cc/dObR0k）。",
        "北區場次：2026-11-09（一）13:00–16:00，地點為國立臺灣科技大學國際大樓101會議室（中區場11/12於僑光科大、南區場11/13於高雄醫大）。",
        "重要提醒：此為學海計畫補助要點說明會，不是臺大校內交換申請期限變更（不啟用交換申請截止提醒）；289所合作校詳細頁及交換列表與昨日一致，部分附件仍無法讀取。",
    ]

    # 1. scholarships.json
    sch_path = bundle / "scholarships.json"
    if sch_path.exists():
        sch = json.loads(sch_path.read_text(encoding="utf-8"))
        other = [
            item
            for item in sch.get("other_scholarship_sources", [])
            if item.get("source_url") != BOARD_URL
        ]
        other.append(
            {
                "name": DASHBOARD_CARD_TITLE,
                "status": "briefing_registration_open",
                "eligibility_cycle": "116年度教育部學海計畫補助要點說明會（學生與相關系所教授可參加；非交換申請期限變更）",
                "registration_deadline": event["registration_deadline"],
                "northern_session": "2026-11-09 13:00–16:00（國立臺灣科技大學國際大樓101會議室）",
                "treated_as_application_deadline": False,
                "reminder_eligible": False,
                "source_url": BOARD_URL,
            }
        )
        sch["other_scholarship_sources"] = other
        sch["briefing_session_20261019"] = event
        sch_path.write_text(json.dumps(sch, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")

    # 2. student_dashboard.json
    sd_path = bundle / "student_dashboard.json"
    if sd_path.exists():
        sd = json.loads(sd_path.read_text(encoding="utf-8"))
        sch_info = [
            item
            for item in sd.get("scholarship_info", [])
            if item.get("title") != DASHBOARD_CARD_TITLE and item.get("source", {}).get("source_url") != BOARD_URL
        ]
        sch_info.append(
            {
                "title": DASHBOARD_CARD_TITLE,
                "details": card_details,
                "source": {
                    "title": event["title"],
                    "source_url": BOARD_URL,
                    "category": "scholarship",
                    "summary": event["note_zh"],
                },
            }
        )
        sd["scholarship_info"] = sch_info
        StudentDashboard.model_validate(sd)
        sd_path.write_text(json.dumps(sd, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")

    # 3. exchange_info.json
    ei_path = bundle / "exchange_info.json"
    if ei_path.exists():
        ei = json.loads(ei_path.read_text(encoding="utf-8"))
        sch_lines = [line for line in ei.get("scholarship_info", []) if line != EXCHANGE_INFO_BULLET and "sn/2336" not in line]
        sch_lines.append(EXCHANGE_INFO_BULLET)
        ei["scholarship_info"] = sch_lines
        src_urls = list(ei.get("source_urls", []))
        if BOARD_URL not in src_urls:
            src_urls.append(BOARD_URL)
        ei["source_urls"] = src_urls
        ExchangeInfo.model_validate(ei)
        ei_path.write_text(json.dumps(ei, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")

    # 4. pages.jsonl
    pages_path = bundle / "pages.jsonl"
    if pages_path.exists():
        existing_pages = [
            ProcessedPage.model_validate_json(line)
            for line in pages_path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
        kept_pages = [p for p in existing_pages if p.source_url != BOARD_URL and p.title != PAGE_TITLE]
        body_text = "\n".join(card_details)
        new_page = ProcessedPage(
            title=PAGE_TITLE,
            source_url=BOARD_URL,
            published_at="2026-10-19T00:00:00Z",
            text=body_text,
            summary=body_text,
            category="scholarship",
            attachments=[],
            crawled_at=data["checked_at"],
            content_hash=hashlib.sha256(body_text.encode("utf-8")).hexdigest(),
        )
        kept_pages.append(new_page)
        pages_path.write_text(
            "".join(p.model_dump_json() + "\n" for p in kept_pages),
            encoding="utf-8",
            newline="\n",
        )

    # 5. catalog-completeness.json & import_provenance.json
    meta = {
        "source_snapshot": path.name,
        "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "checked_at": data["checked_at"],
        "announcement_url": BOARD_URL,
        "board_announcement_url": BOARD_URL,
        "board_announcement_sha256": data["source_manifest"]["ntu_board_sn_2336"]["sha256"],
        "formal_quota_changed": False,
        "treated_as_application_deadline": False,
        "partner_detail_pages_checked": 289,
        "partner_detail_pages_changed": 0,
        "partner_details_and_list_unchanged": True,
        "unreadable_attachments_treated_as_no_update": False,
    }
    for filename in ("catalog-completeness.json", "import_provenance.json"):
        target_file = bundle / filename
        if target_file.exists():
            payload = json.loads(target_file.read_text(encoding="utf-8"))
            payload["source_update_20261019"] = meta
            target_file.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")

    for item in bundle.iterdir():
        if item.is_file():
            raw_bytes = item.read_bytes()
            if b"\r\n" in raw_bytes:
                item.write_bytes(raw_bytes.replace(b"\r\n", b"\n"))

    return {
        "scholarship_briefing_sessions": 1,
        "treated_as_application_deadline": False,
        "formal_quota_changed": False,
    }
