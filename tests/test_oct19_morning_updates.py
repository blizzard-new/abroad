from __future__ import annotations

import json
import shutil
from pathlib import Path

from exchange_info.models import ExchangeInfo, ProcessedPage, StudentDashboard
from exchange_info.ntnu_student_view import fetch_ntnu_partner_universities
from exchange_info.ntu_oct19_updates import (
    BOARD_URL,
    DASHBOARD_CARD_TITLE,
    apply_oct19_updates,
    load_oct19_update,
)
from exchange_info.scu_student_view import fetch_scu_partner_universities, scu_processed_pages

ROOT = Path(__file__).resolve().parents[1]
NTU_BUNDLE = ROOT / "src/exchange_info/official_data/ntu"
NTNU_BUNDLE = ROOT / "src/exchange_info/official_data/ntnu"
SCU_BUNDLE = ROOT / "src/exchange_info/official_data/scu"
AUDIT_JSON = ROOT / "sources/audit/2026-10-19-morning-13-schools.json"
AUDIT_DOC = ROOT / "docs/announcement-updates-2026-10-19.md"


def test_ntu_oct19_scholarship_briefing_update_and_boundaries(tmp_path: Path) -> None:
    update = load_oct19_update()
    assert update["formal_quota_changed"] is False
    assert update["application_open_confirmed"] is False
    assert update["partner_details_and_list_unchanged"] is True
    assert update["unreadable_attachments_treated_as_no_update"] is False

    event = update["scholarship_briefing_event"]
    assert event["source_url"] == BOARD_URL
    assert event["registration_deadline"] == "2026-10-30T17:00:00+08:00"
    assert event["treated_as_application_deadline"] is False
    assert event["reminder_eligible"] is False
    assert event["northern_session"]["date"] == "2026-11-09"
    assert event["northern_session"]["time"] == "13:00–16:00"
    assert "國立臺灣科技大學國際大樓101會議室" in event["northern_session"]["location"]

    dashboard = StudentDashboard.model_validate_json((NTU_BUNDLE / "student_dashboard.json").read_text(encoding="utf-8"))
    # Application deadlines must NOT be altered by the scholarship briefing session
    assert all(p.source.source_url != BOARD_URL for p in dashboard.application_periods if p.source)
    sch_cards = [c for c in dashboard.scholarship_info if c.title == DASHBOARD_CARD_TITLE]
    assert len(sch_cards) == 1
    assert sch_cards[0].source.source_url == BOARD_URL
    assert any("2026-10-30 17:00" in d for d in sch_cards[0].details)
    assert any("2026-11-09" in d and "國際大樓101" in d for d in sch_cards[0].details)
    assert any("不是臺大校內交換申請期限變更" in d for d in sch_cards[0].details)

    info = ExchangeInfo.model_validate_json((NTU_BUNDLE / "exchange_info.json").read_text(encoding="utf-8"))
    assert any("116年度學海計畫補助要點說明會" in s and "不是交換申請期限變更" in s for s in info.scholarship_info)

    pages = [
        ProcessedPage.model_validate_json(line)
        for line in (NTU_BUNDLE / "pages.jsonl").read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    sn2336_pages = [p for p in pages if p.source_url == BOARD_URL]
    assert len(sn2336_pages) == 1
    assert sn2336_pages[0].category == "scholarship"

    for fname in ("catalog-completeness.json", "import_provenance.json"):
        payload = json.loads((NTU_BUNDLE / fname).read_text(encoding="utf-8"))
        meta = payload["source_update_20261019"]
        assert meta["announcement_url"] == BOARD_URL
        assert meta["treated_as_application_deadline"] is False
        assert meta["partner_detail_pages_checked"] == 289
        assert meta["partner_detail_pages_changed"] == 0
        assert meta["unreadable_attachments_treated_as_no_update"] is False

    # Verify byte idempotency of apply_oct19_updates
    work = tmp_path / "ntu"
    shutil.copytree(NTU_BUNDLE, work)
    before = {p.name: p.read_bytes() for p in work.iterdir() if p.is_file()}
    apply_oct19_updates(work)
    after = {p.name: p.read_bytes() for p in work.iterdir() if p.is_file()}
    assert before == after


def test_ntnu_oct19_three_partner_updates_and_282_unchanged() -> None:
    partners = {p.school_name: p for p in fetch_ntnu_partner_universities()}
    assert len(partners) == 236

    wuerzburg = partners["符茲堡大學 Julius-Maximilians-Universität Würzburg"]
    assert "校級 3 名" in (wuerzburg.quota or "")
    assert "院級・管理學院 2 名" in (wuerzburg.quota or "")
    assert "GPA 2.3" in (wuerzburg.eligibility or "")
    assert "德語授課課程" in (wuerzburg.language_requirement or "")
    assert "英語授課課程" in (wuerzburg.language_requirement or "")
    assert "名額公布不代表已開放報名" in (wuerzburg.availability_note or "")

    halmstad = partners["哈勒姆斯塔德大學 Halmstad University"]
    assert "2 名（116-1 公告名額：校級 2 名）" == halmstad.quota
    assert "GPA 3.22" in (halmstad.eligibility or "")
    assert "TOEFL iBT 90（寫20）" in (halmstad.language_requirement or "")
    assert "IELTS 6.5（聽5.5/說5.5/讀5.5/寫5.5）" in (halmstad.language_requirement or "")
    assert "名額公布不代表已開放報名" in (halmstad.availability_note or "")

    ut_austin = partners["德州大學奧斯汀校區 The University of Texas at Austin"]
    assert "2 名（116-1 公告名額：校級 2 名）" == ut_austin.quota
    assert "TOEFL iBT 79" in (ut_austin.language_requirement or "")
    assert "IELTS 6.5" in (ut_austin.language_requirement or "")
    assert "交換期限:一學期" in (ut_austin.course_restrictions or "")
    assert "碩博士生僅可修習學士班課程" in (ut_austin.course_restrictions or "")
    assert "Dell Medical School" in (ut_austin.course_restrictions or "")

    for fname in ("import_provenance.json", "catalog-completeness.json", "verification_status.json"):
        payload = json.loads((NTNU_BUNDLE / fname).read_text(encoding="utf-8"))
        meta = payload["source_update_20261019"]
        assert meta["total_contract_entries"] == 285
        assert meta["changed_contract_entries"] == 3
        assert meta["unchanged_contract_entries"] == 282
        assert meta["quota_published_implies_application_open"] is False
        assert meta["overseas_attachments_fully_audited"] is False


def test_scu_oct19_mainland_116_baseline_correction() -> None:
    partners = fetch_scu_partner_universities()
    mainland = [p for p in partners if p.country == "中國大陸"]
    assert len(mainland) == 62
    assert all(p.academic_year == "116" for p in mainland)
    assert all("2026年11月16日" in (p.application_deadline or "") for p in mainland)

    pages = scu_processed_pages()
    china_apply_pages = [
        p for p in pages if p.source_url == "https://icae.scu.edu.tw/zh-hant/outbound-exchange/china/apply"
    ]
    assert len(china_apply_pages) == 1
    page = china_apply_pages[0]
    assert "116 學年度" in page.text
    assert "2027 秋" in page.text and "2028 春" in page.text
    assert "不能斷言今日才更新" in page.text
    assert any("赴大陸協議學校交換動機及讀書計畫.docx" in a.filename for a in page.attachments)

    for fname in ("import_provenance.json", "catalog-completeness.json", "verification_status.json"):
        payload = json.loads((SCU_BUNDLE / fname).read_text(encoding="utf-8"))
        meta = payload["baseline_correction_20261019"]
        assert meta["verified_academic_year"] == "116"
        assert meta["mainland_partner_count"] == 62
        assert meta["asserted_updated_today"] is False
        assert meta["overseas_partner_table_changed_in_checked_scope"] is False


def test_oct19_morning_13_school_audit_record_and_doc() -> None:
    assert AUDIT_JSON.is_file()
    assert AUDIT_DOC.is_file()
    audit = json.loads(AUDIT_JSON.read_text(encoding="utf-8"))
    assert audit["total_schools_audited"] == 13
    assert audit["summary_counts"] == {
        "confirmed_updates": 2,
        "baseline_corrections": 1,
        "no_change_within_checked_scope": 7,
        "audit_incomplete": 3,
    }
    by_id = {s["school_id"]: s for s in audit["schools"]}
    assert set(by_id) == {
        "ntu",
        "ntnu",
        "scu",
        "cgu",
        "ccu",
        "ncu",
        "tku",
        "fju",
        "yzu",
        "cycu",
        "ntpu",
        "fcu",
        "ntust",
    }
    for sid in ("cgu", "ccu", "ncu", "tku", "fju", "yzu", "cycu"):
        assert by_id[sid]["category"] == "no_change_within_checked_scope"
        assert by_id[sid]["unreadable_attachments_treated_as_no_update"] is False
    for sid in ("ntpu", "fcu", "ntust"):
        assert by_id[sid]["category"] == "audit_incomplete"
        assert by_id[sid]["can_assert_no_update"] is False
    assert by_id["fcu"]["backread_oct14_scholarship_asserted_as_new_today"] is False
