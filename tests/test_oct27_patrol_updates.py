from __future__ import annotations

import json
from pathlib import Path

from exchange_info.models import ExchangeInfo, StudentDashboard
from exchange_info.ntpu_student_view import build_ntpu_student_dashboard, ntpu_exchange_info
from exchange_info.university_registry import require_university
from exchange_info.verified_window_deadlines import (
    CATALOG_LAST_CHECKED_AT,
    build_verified_window_deadline_catalog,
    get_verified_school_window_card,
)

ROOT = Path(__file__).resolve().parents[1]


def _load_dashboard(school_id: str) -> StudentDashboard:
    path = ROOT / "src" / "exchange_info" / "official_data" / school_id / "student_dashboard.json"
    return StudentDashboard.model_validate_json(path.read_text(encoding="utf-8"))


def _load_exchange_info(school_id: str) -> ExchangeInfo:
    path = ROOT / "src" / "exchange_info" / "official_data" / school_id / "exchange_info.json"
    return ExchangeInfo.model_validate_json(path.read_text(encoding="utf-8"))


def test_oct27_daily_22_schools_audit_ledger() -> None:
    audit_path = ROOT / "sources" / "audit" / "2026-10-27-daily-22-schools.json"
    assert audit_path.exists()
    data = json.loads(audit_path.read_text(encoding="utf-8"))
    assert data["audit_id"] == "2026-10-27-daily-22-schools"
    assert data["checked_date"] == "2026-10-27"
    assert data["total_schools_audited"] == 22
    assert data["summary_counts"] == {
        "verified_update": 0,
        "no_change_in_checked_scope": 16,
        "incomplete_or_baseline_only": 6,
    }
    schools = {item["school_id"]: item for item in data["schools"]}
    assert len(schools) == 22
    no_change_ids = {
        "cgu", "ccu", "ncu", "tku", "fju", "scu", "ntnu", "cycu",
        "fcu", "nsysu", "nchu", "nccu", "ncku", "nycu", "nthu", "wzu",
    }
    incomplete_ids = {"ntpu", "ntu", "ntust", "yzu", "ntut", "pccu"}
    assert {sid for sid, item in schools.items() if item["category"] == "no_change_in_checked_scope"} == no_change_ids
    assert {sid for sid, item in schools.items() if item["category"] == "incomplete_or_baseline_only"} == incomplete_ids


def test_oct27_catalog_last_checked_and_22_school_cards() -> None:
    assert CATALOG_LAST_CHECKED_AT == "2026-10-27"
    catalog = build_verified_window_deadline_catalog()
    assert catalog.last_checked_at == "2026-10-27"

    audited_22 = (
        "cgu", "ntpu", "ntu", "ccu", "ncu", "tku", "fju", "scu", "ntnu", "cycu", "ntust",
        "yzu", "fcu", "nsysu", "nchu", "ntut", "nccu", "ncku", "nycu", "nthu", "pccu", "wzu",
    )
    for sid in audited_22:
        card = get_verified_school_window_card(sid)
        assert card.online_deadline.last_checked_at == "2026-10-27", sid


def test_oct27_four_key_highlights_epistemic_boundaries() -> None:
    # 1. NSYSU: 10/27 10:04 check still links 2026/04/12 reference, do not claim published simply because 10/27 arrived
    nsysu_card = get_verified_school_window_card("nsysu")
    assert "10:04" in nsysu_card.online_deadline.value_text
    assert "不能因預定日期已到就宣稱已發布" in nsysu_card.online_deadline.value_text
    assert "384613,r4450.php" in str(nsysu_card.online_deadline.source_url)
    nsysu_dash = _load_dashboard("nsysu")
    nsysu_info = _load_exchange_info("nsysu")
    assert "10:04" in nsysu_dash.application_periods[1].details[0]
    assert "不能因預定日期已到就宣稱已發布" in nsysu_dash.application_periods[1].details[0]
    assert any("10:04" in p for p in nsysu_info.application_period)

    # 2. NTUST: stu88/fall2027 recovered and matches 10/22 baseline; formal quotas & language conflict still pending
    ntust_card = get_verified_school_window_card("ntust")
    assert "恢復讀取" in ntust_card.online_deadline.value_text
    assert "10/22" in ntust_card.online_deadline.value_text
    ntust_dash = _load_dashboard("ntust")
    assert any("151616,r1.php" in d for d in ntust_dash.program_overview[0].details)

    # 3. NTU: OIA school.list and 9 candidate pages still return error -> retain 10/22 baseline, 150 valid / 23 gaps
    ntu_card = get_verified_school_window_card("ntu")
    assert "不等於名額恢復" in ntu_card.online_deadline.value_text
    assert "150份有效" in ntu_card.online_deadline.value_text and "23份缺口" in ntu_card.online_deadline.value_text
    ntu_dash = _load_dashboard("ntu")
    ntu_overview = "\n".join(item.title + "\n" + "\n".join(item.details) for item in ntu_dash.program_overview)
    assert "2026-10-27 查核" in ntu_overview
    assert "不等於名額恢復" in ntu_overview and "150 份有效" in ntu_overview

    # 4. FCU: JTEA scholarship 10/27 10:00 deadline passed, removed from list -> retain 10/26 baseline, do not infer cancelled/rescheduled
    fcu_card = get_verified_school_window_card("fcu")
    assert "10/27 10:00" in fcu_card.online_deadline.value_text
    assert "不推論取消或改期" in fcu_card.online_deadline.value_text
    fcu_dash = _load_dashboard("fcu")
    fcu_schol = "\n".join(item.title + "\n" + "\n".join(item.details) for item in fcu_dash.scholarship_info)
    assert "2026/10/27 10:00 期限已到" in fcu_schol
    assert "不因期限後列表移除或詳頁變空而推論獎學金取消或改期" in fcu_schol


def test_oct27_remaining_school_boundary_refinements() -> None:
    # NTPU: College of Law 10/30 11:00 deadline applies only to Law College
    ntpu_dash = build_ntpu_student_dashboard(partner_universities=[])
    ntpu_info = ntpu_exchange_info(partners=[])
    ntpu_overview = "\n".join(item.title + "\n" + "\n".join(item.details) for item in ntpu_dash.program_overview)
    assert "j1p0rQCYhCHb" in ntpu_overview
    assert "僅適用法律學院" in ntpu_overview
    assert "20260707133939366861" in ntpu_overview
    assert any("10/30 11:00" in p for p in ntpu_info.application_period)

    # TKU: 11/06 info session full (waitlist open) is NOT exchange program quota full
    tku_uni = require_university("tku")
    assert "非交換名額額滿" in tku_uni.coverage_note
    tku_card = get_verified_school_window_card("tku")
    assert "不是交換名額額滿" in tku_card.online_deadline.value_text

    # NCU: Youth Dream exhibition is not an exchange selection change
    ncu_card = get_verified_school_window_card("ncu")
    assert "青年圓夢成果展" in ncu_card.online_deadline.value_text

    # NTNU: College-level truncated text not merged into school-level 285-entry quota list
    ntnu_uni = require_university("ntnu")
    assert "285條目" in ntnu_uni.coverage_note and "不將院級名額併入校級" in ntnu_uni.coverage_note

    # CYCU: ?page_id=99 consultation notice index date 10/27 is first baseline capture only
    cycu_card = get_verified_school_window_card("cycu")
    assert "page_id=99" in cycu_card.online_deadline.value_text and "首次建立基準" in cycu_card.online_deadline.value_text

    # YZU: Official Google quota sheet unreadable on 10/27, retains 10/21 baseline
    yzu_card = get_verified_school_window_card("yzu")
    assert "10/21" in yzu_card.online_deadline.value_text and "不推論今日名額無變更" in yzu_card.online_deadline.value_text

    # NTUT: 10/29 info session (r2255.php) and 116 formal brochure still pending
    ntut_card = get_verified_school_window_card("ntut")
    assert "r2255.php" in ntut_card.online_deadline.value_text

    # NCCU: post/118 interview notice unchanged, dynamic directory retains 10/25 39-item baseline
    nccu_card = get_verified_school_window_card("nccu")
    assert "post/118" in nccu_card.online_deadline.value_text and "39筆" in nccu_card.online_deadline.value_text

    # NTHU: 142-entry dynamic table (puid/11521) and Kyushu / Osaka Institute of Technology baseline
    nthu_card = get_verified_school_window_card("nthu")
    assert "puid/11521" in nthu_card.online_deadline.value_text
    assert "九州大學" in nthu_card.online_deadline.value_text and "大阪工業大學" in nthu_card.online_deadline.value_text

    # PCCU & WZU
    pccu_card = get_verified_school_window_card("pccu")
    assert "en/study-abroad-detail5.htm" in pccu_card.online_deadline.value_text
    wzu_card = get_verified_school_window_card("wzu")
    assert "530796" in wzu_card.online_deadline.value_text and "530797" in wzu_card.online_deadline.value_text
