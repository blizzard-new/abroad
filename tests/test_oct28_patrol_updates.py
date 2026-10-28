from __future__ import annotations

import json
from pathlib import Path

from exchange_info.application_documents import all_application_templates
from exchange_info.cmu_student_view import build_cmu_student_dashboard, cmu_exchange_info
from exchange_info.kmu_student_view import build_kmu_student_dashboard, kmu_exchange_info
from exchange_info.nknu_student_view import build_nknu_student_dashboard, nknu_exchange_info
from exchange_info.ntub_student_view import build_ntub_student_dashboard, ntub_exchange_info
from exchange_info.university_registry import CMU, KMU, NKNU, NTUB, WZU
from exchange_info.verified_window_deadlines import get_verified_school_window_card
from exchange_info.wzu_student_view import build_wzu_student_dashboard, wzu_exchange_info

ROOT = Path(__file__).resolve().parents[1]


def test_oct28_dora2_audit_manifest_records_all_16_schools() -> None:
    audit_path = ROOT / "sources" / "audit" / "2026-10-28-dora2-16-schools.json"
    assert audit_path.is_file()
    payload = json.loads(audit_path.read_text(encoding="utf-8"))
    assert payload["audit_date"] == "2026-10-28"
    assert payload["total_schools"] == 16
    assert payload["updated_school_count"] == 5
    assert payload["unchanged_school_count"] == 11
    ids = {item["school_id"] for item in payload["schools"]}
    assert ids == {
        "wzu",
        "nknu",
        "cmu",
        "kmu",
        "ntub",
        "ncku",
        "nycu",
        "nthu",
        "pccu",
        "nkust",
        "yuntech",
        "ntou",
        "ncue",
        "tmu",
        "csmu",
        "mcu",
    }


def test_wzu_oct28_new_announcements_and_round2_roster_clarification() -> None:
    assert "530925" in WZU.coverage_note
    assert "報名成功名單" in WZU.coverage_note
    assert "非錄取結果" in WZU.coverage_note
    assert "530756" in WZU.coverage_note
    assert "11/16" in WZU.coverage_note
    assert "531074" in WZU.coverage_note

    ex = wzu_exchange_info()
    combined_period = "\n".join(ex.application_period)
    assert "530925" in combined_period
    assert "非錄取結果" in combined_period
    assert "接待校決定是否錄取" in combined_period
    assert "530756" in "\n".join(ex.scholarship_info)

    card = get_verified_school_window_card("wzu")
    assert "530925" in card.online_deadline.value_text
    assert "530756" in card.online_deadline.value_text
    assert card.online_deadline.last_checked_at == "2026-10-28"


def test_nknu_oct28_mainland_list_and_exchange_programs_page_clarification() -> None:
    assert "1001更新" in NKNU.coverage_note
    assert "南京師範大學" in NKNU.coverage_note
    assert "南京大學" in NKNU.coverage_note
    assert "20251027" in NKNU.coverage_note
    assert "sister-schools.php" in NKNU.coverage_note

    dashboard = build_nknu_student_dashboard()
    p0 = dashboard.application_periods[0]
    p1 = dashboard.application_periods[1]
    assert "活動中心二樓演講廳" in "\n".join(p0.details)
    assert "寰宇大樓二樓會議室" in "\n".join(p0.details)
    assert "20251027" in "\n".join(p0.details)
    assert "1001更新" in p1.title
    assert "南京師範大學" in "\n".join(p1.details)
    assert "南京大學" in "\n".join(p1.details)

    ex = nknu_exchange_info()
    assert "1001更新" in "\n".join(ex.application_period)


def test_cmu_oct28_legacy_page_and_actual_source_alignment() -> None:
    assert CMU.official_url == "https://cmucia.cmu.edu.tw/s_exchange.html"
    assert "s_exchange.html" in CMU.coverage_note
    assert "2011–2018" in CMU.coverage_note
    assert "202212281100421.pdf" in CMU.coverage_note
    assert "sn=622" in CMU.coverage_note

    dashboard = build_cmu_student_dashboard()
    p0 = dashboard.application_periods[0]
    p1 = dashboard.application_periods[1]
    p2 = dashboard.application_periods[2]
    assert p0.date_status == "needs_confirmation"
    assert p0.deadline_at is None
    assert "202212281100421.pdf" in str(p0.source.source_url)
    assert p1.date_status == "needs_confirmation"
    assert "sn=616" in str(p1.source.source_url)
    assert p2.deadline_at is not None and "2026-10-12" in p2.deadline_at.isoformat()

    ex = cmu_exchange_info()
    assert "s_exchange.html" in "\n".join(ex.application_period)
    assert "202212281100421.pdf" in "\n".join(ex.application_period)

    templates = all_application_templates("cmu")
    assert all(t.source_url == "https://cmucia.cmu.edu.tw/s_exchange.html" for t in templates)


def test_kmu_oct28_homepage_new_announcements_and_teep_distinction() -> None:
    assert "2027 人文及社會科學領域海外研修人才培育計畫" in KMU.coverage_note
    assert "2027 臺灣與阿拉伯聯合大公國青年交流計畫" in KMU.coverage_note
    assert "TaiwanGPS" in KMU.coverage_note
    assert "TEEP" in KMU.coverage_note
    assert "cmed.kmu.edu.tw" in KMU.coverage_note

    dashboard = build_kmu_student_dashboard()
    all_periods_text = "\n".join("\n".join(p.details) for p in dashboard.application_periods)
    overview_text = "\n".join(dashboard.program_overview[0].details)
    assert "3259" in all_periods_text
    assert "3283" in all_periods_text
    assert "3279" in all_periods_text
    assert "3287" in all_periods_text
    assert "3261" in all_periods_text
    assert "3281" in all_periods_text
    assert "TEEP" in overview_text

    ex = kmu_exchange_info()
    assert "2027 人文及社會科學領域海外研修人才培育計畫" in "\n".join(ex.application_period)


def test_ntub_oct28_eligibility_scoring_and_departure_wording() -> None:
    assert NTUB.official_url == "https://oia.ntub.edu.tw/p/405-1006-57507,c3152.php?Lang=zh-tw"
    assert "80 分以上" in NTUB.coverage_note
    assert "前 70%" in NTUB.coverage_note
    assert "操行 80 分" not in NTUB.coverage_note
    assert "於申請之隔年度出國交換一學期或一學年" in NTUB.coverage_note
    assert "1081114" in NTUB.coverage_note
    assert "91803" in NTUB.coverage_note
    assert "峽谷學院" in NTUB.coverage_note
    assert "120031" in NTUB.coverage_note

    dashboard = build_ntub_student_dashboard()
    p0_text = "\n".join(dashboard.application_periods[0].details)
    assert "於申請之隔年度出國交換一學期或一學年" in p0_text
    assert "120272" in p0_text

    ex = ntub_exchange_info()
    assert "官網寫「於申請之隔年度出國」，未寫「8–9 月或 2 月出發」" in "\n".join(ex.semester)
    assert "1081114" in "\n".join(ex.application_period)

    templates = {t.id: t for t in all_application_templates("ntub")}
    assert templates["return-report"].writing_rules is not None
    assert templates["return-report"].writing_rules.min_chars == 1000
