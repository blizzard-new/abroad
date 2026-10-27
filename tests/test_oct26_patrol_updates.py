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


def test_oct26_dora2_16_schools_audit_ledger() -> None:
    audit_path = ROOT / "sources" / "audit" / "2026-10-26-dora2-16-schools.json"
    assert audit_path.exists()
    data = json.loads(audit_path.read_text(encoding="utf-8"))
    assert data["audit_id"] == "2026-10-26-dora2-16-schools"
    assert data["checked_date"] == "2026-10-26"
    assert data["total_schools_audited"] == 16
    assert data["summary_counts"] == {
        "new_announcements": 7,
        "discrepancy_resolved": 2,
        "url_or_portal_fixed": 2,
        "no_change": 5,
    }
    schools = {item["school_id"]: item for item in data["schools"]}
    assert len(schools) == 16
    for sid in ("ncku", "nycu", "wzu", "nkust", "csmu", "kmu", "mcu"):
        assert schools[sid]["category"] == "new_announcement"
    for sid in ("tmu", "ntub"):
        assert schools[sid]["category"] == "discrepancy_resolved"
    for sid in ("pccu", "ncue"):
        assert schools[sid]["category"] == "url_or_portal_fixed"
    for sid in ("nthu", "yuntech", "ntou", "nknu", "cmu"):
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


def test_ncku_nycu_wzu_nkust_dora2_updates() -> None:
    # NCKU
    ncku = require_university("ncku")
    assert ncku.official_url == "https://oia.ncku.edu.tw/p/404-1032-229870.php?Lang=zh-tw"
    assert "306703" in ncku.coverage_note and "2026/10/16" in ncku.coverage_note
    ncku_card = get_verified_school_window_card("ncku")
    assert "306703" in str(ncku_card.online_deadline.source_url)
    assert "圖爾庫" in ncku_card.online_deadline.value_text

    # NYCU
    nycu = require_university("nycu")
    assert nycu.official_url == "https://oia.nycu.edu.tw/oia/ch/app/data/list?module=nycu0006&id=286"
    assert "2026/10/07" in nycu.coverage_note and "青年交流計畫" in nycu.coverage_note
    nycu_card = get_verified_school_window_card("nycu")
    assert "2026-10-07" in nycu_card.online_deadline.value_text
    assert "台灣–阿聯青年交流計畫" in nycu_card.online_deadline.value_text

    # WZU
    wzu = require_university("wzu")
    assert wzu.official_url == "https://d020.wzu.edu.tw/article/530752"
    assert "布達佩斯城市大學" in wzu.coverage_note and "啟明大學" in wzu.coverage_note
    wzu_partners = [
        PartnerUniversity.model_validate_json(line)
        for line in (ROOT / "src/exchange_info/official_data/wzu/partners.jsonl").read_text("utf-8").splitlines()
        if line.strip()
    ]
    bmu = next(p for p in wzu_partners if "Budapest Metropolitan University" in p.school_name)
    assert "CEFR B2" in (bmu.availability_note or "") and "80分" in (bmu.availability_note or "")
    kmu_kr = next(p for p in wzu_partners if "Keimyung University" in p.school_name)
    assert "TOEIC 785" in (kmu_kr.availability_note or "") and "TOPIK 4級" in (kmu_kr.availability_note or "")

    # NKUST
    nkust = require_university("nkust")
    assert "2026/11/09 12:00" in nkust.coverage_note and "12/01 16:00" in nkust.coverage_note
    nkust_card = get_verified_school_window_card("nkust")
    assert "unit-4-374-21.html" in str(nkust_card.online_deadline.source_url)
    assert "115/12/01 16:00" in nkust_card.online_deadline.value_text
    assert "建工校區" in nkust_card.online_deadline.value_text


def test_tmu_csmu_kmu_mcu_ntub_pccu_ncue_dora2_updates() -> None:
    # TMU
    tmu = require_university("tmu")
    assert "1 月 15 日" in tmu.coverage_note and "三個月以上" in tmu.coverage_note
    tmu_dash = _load_dashboard("tmu")
    tmu_text = "\n".join(item.title + "\n" + "\n".join(item.details) for item in (*tmu_dash.application_periods, *tmu_dash.program_overview))
    assert "tmu-student-outbound-exchange" in tmu_text
    assert "至少 3 個月" in tmu_text and "1 個月以上" in tmu_text

    # CSMU
    csmu_dash = _load_dashboard("csmu")
    assert csmu_dash.application_periods[0].status == "closed"
    csmu_text = "\n".join(item.title + "\n" + "\n".join(item.details) for item in csmu_dash.program_overview)
    assert "2026 海外交換生研修心得分享座談會" in csmu_text
    assert "Young 飛全球行動計畫培訓營" in csmu_text

    # KMU
    kmu = require_university("kmu")
    assert kmu.official_url == "https://ciae2.kmu.edu.tw/index.php/zh-tw"
    kmu_dash = _load_dashboard("kmu")
    kmu_text = "\n".join(item.title + "\n" + "\n".join(item.details) for item in (*kmu_dash.application_periods, *kmu_dash.program_overview))
    assert "2027 日本台灣交流協會獎學金（短期生）" in kmu_text
    assert "青年百億海外圓夢基金" in kmu_text
    assert "EMJM" in kmu_text

    # MCU
    mcu = require_university("mcu")
    assert mcu.official_url == "https://iee.mcu.edu.tw/"
    assert "/zh-hant/" not in mcu.official_url
    mcu_dash = _load_dashboard("mcu")
    assert mcu_dash.application_periods[0].status == "closed"
    mcu_text = "\n".join(item.title + "\n" + "\n".join(item.details) for item in (*mcu_dash.application_periods, *mcu_dash.program_overview))
    assert "海外留學說明會" in mcu_text
    assert "嘉泉大學冬季韓語營" in mcu_text

    # NTUB
    ntub = require_university("ntub")
    assert ntub.official_url == "https://oia.ntub.edu.tw/p/412-1006-3152.php?Lang=zh-tw"
    assert "120272" in ntub.coverage_note and "峽谷學院" in ntub.coverage_note
    ntub_dash = _load_dashboard("ntub")
    ntub_text = "\n".join(item.title + "\n" + "\n".join(item.details) for item in (*ntub_dash.application_periods, *ntub_dash.program_overview))
    assert "120272" in ntub_text and "峽谷學院" in ntub_text

    # PCCU & NCUE
    pccu = require_university("pccu")
    assert pccu.official_url == "https://mccd.pccu.edu.tw/p/406-1300-148804,r2247.php?Lang=zh-tw"
    ncue = require_university("ncue")
    assert ncue.official_url == "https://oicaweb.ncue.edu.tw/p/412-1019-1171.php?Lang=zh-tw"
    assert "-1002-" not in ncue.official_url
