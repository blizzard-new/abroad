from __future__ import annotations

import json
from pathlib import Path

from exchange_info.models import ExchangeInfo, PartnerUniversity, StudentDashboard
from exchange_info.university_registry import require_university
from exchange_info.verified_window_deadlines import get_verified_school_window_card

ROOT = Path(__file__).resolve().parents[1]


def _load_dashboard(school_id: str) -> StudentDashboard:
    path = ROOT / "src" / "exchange_info" / "official_data" / school_id / "student_dashboard.json"
    return StudentDashboard.model_validate_json(path.read_text(encoding="utf-8"))


def _load_exchange_info(school_id: str) -> ExchangeInfo:
    path = ROOT / "src" / "exchange_info" / "official_data" / school_id / "exchange_info.json"
    return ExchangeInfo.model_validate_json(path.read_text(encoding="utf-8"))


def test_oct26_daily_17_schools_audit_ledger() -> None:
    audit_path = ROOT / "sources" / "audit" / "2026-10-26-daily-17-schools.json"
    assert audit_path.exists()
    data = json.loads(audit_path.read_text(encoding="utf-8"))
    assert data["audit_id"] == "2026-10-26-daily-17-schools"
    assert data["checked_date"] == "2026-10-26"
    assert data["total_schools_audited"] == 17
    assert data["summary_counts"] == {
        "new_announcements": 5,
        "discrepancy_resolved": 2,
        "no_change": 10,
    }
    schools = {item["school_id"]: item for item in data["schools"]}
    assert len(schools) == 17
    for sid in ("ntpu", "ntu", "cycu", "ntust", "nsysu"):
        assert schools[sid]["category"] == "new_announcement"
    for sid in ("ncu", "nchu"):
        assert schools[sid]["category"] == "discrepancy_resolved"
    for sid in ("cgu", "ccu", "tku", "fju", "scu", "ntnu", "yzu", "fcu", "ntut", "nccu"):
        assert schools[sid]["category"] == "no_change"


def test_ntpu_oct26_xuehai_amendment_and_efrei_info_session() -> None:
    from exchange_info.ntpu_student_view import build_ntpu_student_dashboard, ntpu_exchange_info

    dash = build_ntpu_student_dashboard(partner_universities=[])
    info = ntpu_exchange_info(partners=[])

    scholarship_text = "\n".join(
        item.title + "\n" + "\n".join(item.details) + "\n" + (item.source.source_url if item.source else "")
        for item in dash.scholarship_info
    )
    assert "2026/10/22" in scholarship_text
    assert "6ad986a07085cb4f0c818c5e" in scholarship_text
    assert any("1151021_c627bfee0e.pdf" in u for u in info.source_urls)
    assert "刪除第三條第(三)款「且未獲得交換／訪問學校獎學金」限制" in scholarship_text

    overview_text = "\n".join(
        item.title + "\n" + "\n".join(item.details) + "\n" + (item.source.source_url if item.source else "")
        for item in (*dash.application_periods, *dash.program_overview)
    )
    assert "EFREI" in overview_text
    assert "6acc5d0d7085cb4f0c818840" in overview_text
    assert any("2026/10/22" in s for s in info.scholarship_info)


def test_ntu_oct26_timeline_goettingen_and_legacy_maintenance_note() -> None:
    dash = _load_dashboard("ntu")
    info = _load_exchange_info("ntu")

    period_text = "\n".join(item.title + "\n" + "\n".join(item.details) for item in dash.application_periods)
    overview_text = "\n".join(item.title + "\n" + "\n".join(item.details) for item in dash.program_overview)
    combined = period_text + "\n" + overview_text
    assert "sem1-20272028ay-selection-timeline" in combined
    assert "德國哥廷根大學交換學生計畫說明會" in combined
    assert "system_maintenance_20221030" in combined
    assert any("德國哥廷根大學交換學生計畫說明會" in p for p in info.application_period)


def test_ncu_oct26_1022_partner_list_diff_and_catalog() -> None:
    diff_path = ROOT / "sources" / "ncu" / "2026-10-22" / "diff-from-1013.json"
    rows_path = ROOT / "sources" / "ncu" / "2026-10-22" / "quota-116-1-rows.json"
    pdf_path = ROOT / "sources" / "ncu" / "2026-10-22" / "116exchangeschoollist-1022.pdf"
    assert diff_path.exists() and rows_path.exists() and pdf_path.exists()

    diff = json.loads(diff_path.read_text(encoding="utf-8"))
    assert diff["previous_version"]["row_count"] == 215
    assert diff["current_version"]["row_count"] == 214
    assert len(diff["removed_rows"]) == 1
    assert diff["removed_rows"][0]["name_zh"] == "北方高等商業學院"
    assert len(diff["modified_rows"]) == 1
    assert "UniLaSalle" in diff["modified_rows"][0]["name_en"]

    partners_path = ROOT / "src" / "exchange_info" / "official_data" / "ncu" / "partners.jsonl"
    partners = [
        PartnerUniversity.model_validate_json(line)
        for line in partners_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    edhec = next(p for p in partners if "EDHEC" in p.school_name)
    assert "已於2026/10/22版姐妹校列表中移除" in (edhec.eligibility or "")
    assert "116exchangeschoollist-1022.pdf" in (edhec.eligibility or "")

    unilasalle = next(p for p in partners if "UniLaSalle" in p.school_name)
    assert "B2 English" in (unilasalle.eligibility or "")


def test_cycu_oct26_url_fixed_and_115_2_round2_added() -> None:
    uni = require_university("cycu")
    assert uni.official_url == "https://oia.cycu.edu.tw/?p=6336"

    dash = _load_dashboard("cycu")
    info = _load_exchange_info("cycu")
    combined = "\n".join(
        item.title + "\n" + "\n".join(item.details)
        for item in (*dash.application_periods, *dash.program_overview)
    )
    assert "第二梯次" in combined
    assert "https://oia.cycu.edu.tw/?p=9903" in combined
    assert "20所姊妹校" in combined and "50個名額" in combined
    assert "https://oia.cycu.edu.tw/?page_id=2956&lang=zh" not in info.source_urls


def test_ntust_oct26_certificate_hostname_fixed_and_116_1_brochure_added() -> None:
    uni = require_university("ntust")
    assert uni.official_url == "https://oia.ntust.edu.tw/p/405-1060-62102,c9056.php?Lang=zh-tw"
    assert "www.oia.ntust.edu.tw" not in uni.official_url

    dash = _load_dashboard("ntust")
    info = _load_exchange_info("ntust")
    period_text = "\n".join(item.title + "\n" + "\n".join(item.details) for item in dash.application_periods)
    assert "_中文_20260915.pdf" in period_text
    assert "116-1" in period_text
    assert all("www.oia.ntust.edu.tw" not in u for u in info.source_urls)


def test_nsysu_oct26_timeline_info_sessions_and_provisional_notice() -> None:
    card = get_verified_school_window_card("nsysu")
    assert "384613" in card.online_deadline.source_url
    assert "10/27" in card.online_deadline.value_text

    dash = _load_dashboard("nsysu")
    combined = "\n".join(
        item.title + "\n" + "\n".join(item.details) + "\n" + (item.source.source_url if item.source else "")
        for item in (*dash.application_periods, *dash.program_overview)
    )
    assert "384613" in combined
    assert "20:00" in combined and "12:00" in combined
    assert "暫定版" in combined


def test_nchu_oct26_broken_url_replaced_and_step1_closed_note() -> None:
    uni = require_university("nchu")
    assert "154-1-1-exchange-info" not in uni.official_url
    assert "5-1-1-application-guildeline-tw" in uni.official_url

    dash = _load_dashboard("nchu")
    info = _load_exchange_info("nchu")
    assert all("154-1-1-exchange-info" not in u for u in info.source_urls)
    assert any("5-1-1-application-guildeline-en" in u for u in info.source_urls)
    overview_text = "\n".join(item.title + "\n" + "\n".join(item.details) for item in dash.program_overview)
    assert "5-1-1-application-guildeline-en" in overview_text
    assert "10/30" in overview_text
