from __future__ import annotations

import json
import shutil
from pathlib import Path

from exchange_info.models import ExchangeInfo, ProcessedPage, StudentDashboard
from exchange_info.ntu_oct22_updates import (
    BLANK_LIST_DETAIL_CHANGED_IDS,
    DASHBOARD_OVERVIEW_TITLE,
    DETAIL_CHANGED_IDS,
    JAPAN_TRANSCRIPT_REMINDER_IDS,
    LIST_URL,
    NORTH_AMERICA_PENDING_OR_ZERO_IDS,
    QUOTA_PUBLISHED_IDS,
    apply_oct22_partner_view,
    apply_oct22_updates,
    load_oct22_update,
)
from exchange_info.ntu_student_view import fetch_ntu_partner_universities
from exchange_info.tku_oct22_updates import (
    DASHBOARD_OVERVIEW_TITLE as TKU_OCT22_OVERVIEW_TITLE,
    INFO_SESSION_URL,
    validate_tku_oct22_update_snapshot,
)
from exchange_info.tku_student_view import build_tku_student_dashboard, tku_processed_pages
from exchange_info.verified_window_deadlines import CATALOG_LAST_CHECKED_AT

ROOT = Path(__file__).resolve().parents[1]
AUDIT_LEDGER = ROOT / "sources" / "audit" / "2026-10-22-daily-22-schools.json"
AUDIT_DOC = ROOT / "docs" / "announcement-updates-2026-10-22.md"
NTU_BUNDLE = ROOT / "src" / "exchange_info" / "official_data" / "ntu"


def test_oct22_22_school_audit_ledger_and_epistemic_boundaries() -> None:
    assert AUDIT_LEDGER.is_file()
    assert AUDIT_DOC.is_file()
    assert CATALOG_LAST_CHECKED_AT == "2026-10-22"

    ledger = json.loads(AUDIT_LEDGER.read_text(encoding="utf-8"))
    assert ledger["audit_id"] == "2026-10-22-daily-22-schools"
    assert ledger["checked_date"] == "2026-10-22"
    assert ledger["total_schools_audited"] == 22
    assert ledger["summary_counts"] == {
        "confirmed_updates": 2,
        "no_change_in_checked_scope": 15,
        "key_scope_incomplete": 5,
    }

    by_id = {row["school_id"]: row for row in ledger["schools"]}
    assert len(by_id) == 22

    # 2 confirmed updates: ntu, tku
    assert {k for k, v in by_id.items() if v["category"] == "confirmed_update"} == {"ntu", "tku"}
    assert by_id["ntu"]["partner_detail_pages_checked"] == 289
    assert by_id["ntu"]["list_newly_published_quota_schools"] == 5
    assert by_id["ntu"]["positive_quota_schools_total"] == 39
    assert by_id["ntu"]["blank_quota_schools_total"] == 243
    assert by_id["ntu"]["zero_quota_schools_total"] == 7
    assert by_id["ntu"]["academic_year_units_total"] == 76.5
    assert by_id["ntu"]["maximum_persons_total"] == 144
    assert by_id["ntu"]["japan_transcript_reminder_schools"] == 38
    assert by_id["ntu"]["blank_list_detail_quotas_treated_as_finalized"] is False
    assert by_id["ntu"]["uc_toefl_home_edition_contradiction_resolved"] is False
    assert by_id["ntu"]["uic_and_ncsu_pdf_relabeled_as_new_year"] is False
    assert by_id["ntu"]["new_fact_sheet_links_claimed_as_content_updated_today"] is False
    assert by_id["ntu"]["attachment_counts"] == {
        "total": 173,
        "succeeded": 95,
        "incomplete": 78,
        "superseded_previous_counts": {
            "total": 150,
            "succeeded": 94,
            "incomplete": 56,
        },
    }

    assert by_id["tku"]["info_session_capacity"] == 170
    assert by_id["tku"]["info_session_registered_before"] == 168
    assert by_id["tku"]["info_session_registered_after"] == 170
    assert by_id["tku"]["info_session_status"] == "full"
    assert by_id["tku"]["walk_in_standby_allowed"] is True
    assert by_id["tku"]["treated_as_exchange_program_quota_full"] is False
    assert by_id["tku"]["treated_as_exchange_application_deadline"] is False
    assert by_id["tku"]["english_and_european_new_quotas_confirmed"] is False

    # 15 no change in checked scope
    expected_no_change = {
        "cgu",
        "ccu",
        "ncu",
        "fju",
        "scu",
        "ntnu",
        "cycu",
        "fcu",
        "nsysu",
        "nchu",
        "nccu",
        "ncku",
        "nycu",
        "nthu",
        "wzu",
    }
    assert {k for k, v in by_id.items() if v["category"] == "no_change_in_checked_scope"} == expected_no_change
    assert by_id["cgu"]["treated_as_new_academic_year_guidelines"] is False
    assert by_id["ccu"]["doc_first_fetch_treated_as_updated_today"] is False
    assert by_id["fju"]["yesterday_list_cleanup_re_reported_as_new_suspension"] is False
    assert by_id["scu"]["baseline_expansion_asserted_as_updated_today"] is False
    assert by_id["cycu"]["xuehai_info_session_treated_as_new_selection"] is False
    assert by_id["fcu"]["temple_and_sjsu_baseline_claimed_as_published_today"] is False
    assert by_id["nchu"]["existing_deadline_reminder_claimed_as_new_announcement"] is False
    assert by_id["nccu"]["baseline_expansion_asserted_as_updated_today"] is False
    assert by_id["nycu"]["ust_conflated_with_school_level_115_2"] is False
    assert by_id["nycu"]["cached_fallback_disclosed"] is True
    assert by_id["nthu"]["empty_shell_pages_counted_as_checked"] is False
    assert by_id["wzu"]["view_count_change_treated_as_rule_update"] is False

    # 5 key scope incomplete
    expected_incomplete = {"ntpu", "ntust", "yzu", "ntut", "pccu"}
    assert {k for k, v in by_id.items() if v["category"] == "key_scope_incomplete"} == expected_incomplete
    for sid in expected_incomplete:
        assert by_id[sid]["key_scope_complete"] is False
        assert by_id[sid]["asserted_as_no_update"] is False
    assert by_id["ntpu"]["preview_deadline_treated_as_final"] is False
    assert by_id["ntpu"]["college_of_business_treated_as_university_wide"] is False
    assert by_id["yzu"]["yesterday_sheet_used_to_claim_unchanged_today"] is False
    assert by_id["ntut"]["info_session_treated_as_formal_guidelines"] is False
    assert by_id["pccu"]["historical_2013_rules_treated_as_current_update"] is False
    assert by_id["pccu"]["attachment_year_consistent_with_body"] is False

    doc_text = AUDIT_DOC.read_text(encoding="utf-8")
    for keyword in (
        "馬薩里克大學",
        "哥本哈根大學",
        "薩拉曼卡大學",
        "華沙大學",
        "華沙理工大學",
        "查理大學",
        "38 校",
        "4 週",
        "岡山大學",
        "一橋大學",
        "UT Austin",
        "Temple",
        "UIC",
        "Cornell",
        "UConn",
        "NCSU",
        "加州大學",
        "Queen's",
        "青山學院大學",
        "同志社大學",
        "康斯坦茨大學",
        "173 份",
        "95 份",
        "78 份",
        "150／94／56",
        "168 人",
        "170 人",
        "不是交換名額額滿",
        "18:10",
    ):
        assert keyword in doc_text


def test_ntu_oct22_quota_detail_and_attachment_updates_and_idempotency(tmp_path: Path) -> None:
    data = load_oct22_update()
    assert data["counts"] == {
        "partners": 289,
        "detail_pages_checked": 289,
        "detail_pages_changed_key_sampled": 21,
        "japan_transcript_reminder_schools": 38,
        "list_newly_published_quota_schools": 5,
        "positive_quota_schools_total": 39,
        "blank_quota_schools_total": 243,
        "zero_quota_schools_total": 7,
        "academic_year_units_total": 76.5,
        "maximum_persons_total": 144,
    }
    assert {r["portal_id"] for r in data["newly_published_list_quotas"]} == QUOTA_PUBLISHED_IDS
    assert {r["portal_id"] for r in data["changed_detail_pages"]} == DETAIL_CHANGED_IDS
    assert set(data["japan_transcript_reminder_pids"]) == JAPAN_TRANSCRIPT_REMINDER_IDS
    assert len(JAPAN_TRANSCRIPT_REMINDER_IDS) == 38

    dashboard = StudentDashboard.model_validate_json(
        (NTU_BUNDLE / "student_dashboard.json").read_text(encoding="utf-8")
    )
    overview_cards = [c for c in dashboard.program_overview if c.title == DASHBOARD_OVERVIEW_TITLE]
    assert len(overview_cards) == 1
    assert overview_cards[0].source.source_url == LIST_URL

    partners = apply_oct22_partner_view(fetch_ntu_partner_universities())
    assert len(partners) == 289
    assert sum(p.quota_status == "published" for p in partners) == 39
    by_sn = {p.source_url.rsplit("/", 1)[-1]: p for p in partners}

    # 5 newly published list quotas on 2026-10-22
    expected_quotas = {
        "387": "1 學年名額（最多 2 人次）",
        "61": "3 學年名額（最多 6 人次）",
        "921": "1 學年名額（最多 2 人次）",
        "1042": "1 學年名額（最多 2 人次）",
        "1206": "1 學年名額（最多 2 人次）",
    }
    for pid, q_str in expected_quotas.items():
        partner = by_sn[pid]
        assert partner.quota == q_str
        assert partner.quota_status == "published"

    # Detail checks for published list schools
    assert "TOEFL iBT 4.0" in (by_sn["387"].eligibility or "")
    assert "TOEFL iBT 83" in (by_sn["61"].eligibility or "")
    assert "TOEFL iBT 4.5" in (by_sn["61"].eligibility or "")
    assert "IELTS 6.5" in (by_sn["61"].eligibility or "")
    assert "GPA 達3.30分以上" in (by_sn["968"].eligibility or "")
    assert "第二次出國交換" not in (by_sn["1042"].eligibility or "")
    assert "TOEFL iBT 4.0" in (by_sn["1042"].eligibility or "")
    assert "第二次出國交換" in (by_sn["1206"].eligibility or "")
    assert "不含博士生" in (by_sn["1206"].eligibility or "")
    assert "TOEFL iBT 4.0" in (by_sn["1206"].eligibility or "")
    assert "碩一以上" in (by_sn["921"].eligibility or "")

    # All 38 Japan schools have the 4-week transcript reminder
    for pid in JAPAN_TRANSCRIPT_REMINDER_IDS:
        assert "4 週後核發" in (by_sn[pid].eligibility or "")

    # Blank-list detail-changed schools MUST remain quota=None and not formally open
    for pid in BLANK_LIST_DETAIL_CHANGED_IDS:
        assert by_sn[pid].quota is None
        assert by_sn[pid].availability_status == "agreement_only"
        assert by_sn[pid].reference_data.get("list_quota_finalized_20261022") == "false"

    # North America and UC internal contradiction checks
    for pid in NORTH_AMERICA_PENDING_OR_ZERO_IDS - {"599", "9"}:
        assert "不能當成定案甄選名額" in (by_sn[pid].eligibility or "")
    assert by_sn["9"].field_evidence["eligibility"].status == "conflict"
    assert "頁內矛盾待釐清" in (by_sn["9"].eligibility or "")
    assert by_sn["19"].reference_data.get("linked_pdf_academic_year_20261022") == "2026/2027"
    assert by_sn["13"].reference_data.get("linked_pdf_academic_year_20261022") == "2026/2027"

    # Queen's (sn/599) remains 0 quota with new Smith & CoM restrictions
    assert by_sn["599"].quota == "0 名"
    assert "不開放 Smith School of Business 課程" in (by_sn["599"].eligibility or "")
    assert "管理學院" in (by_sn["599"].eligibility or "")

    info = ExchangeInfo.model_validate_json((NTU_BUNDLE / "exchange_info.json").read_text(encoding="utf-8"))
    assert any("2026-10-22 查核更新" in s for s in info.eligibility)

    pages = [
        ProcessedPage.model_validate_json(line)
        for line in (NTU_BUNDLE / "pages.jsonl").read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    assert any(p.source_url == LIST_URL and "2026-10-22" in p.title for p in pages)

    completeness = json.loads((NTU_BUNDLE / "catalog-completeness.json").read_text(encoding="utf-8"))
    assert "source_update_20261022" in completeness
    assert completeness["source_update_20261022"]["attachment_coverage"]["total_linked_documents"] == 173
    assert completeness["source_update_20261022"]["attachment_coverage"]["read_succeeded"] == 95
    assert completeness["source_update_20261022"]["attachment_coverage"]["incomplete_or_unreadable"] == 78

    # Byte idempotency of apply_oct22_updates
    work = tmp_path / "ntu"
    shutil.copytree(NTU_BUNDLE, work)
    before = {p.name: p.read_bytes() for p in work.iterdir() if p.is_file()}
    apply_oct22_updates(work)
    after = {p.name: p.read_bytes() for p in work.iterdir() if p.is_file()}
    assert before == after


def test_tku_oct22_info_session_full_and_standby_boundaries() -> None:
    payload = validate_tku_oct22_update_snapshot()
    assert payload["treated_as_exchange_application_deadline"] is False
    assert payload["treated_as_exchange_program_quota_full"] is False
    assert payload["english_and_european_new_quotas_confirmed"] is False
    info = payload["info_session_registration_update"]
    assert info["registered_count_before_20261021"] == 168
    assert info["registered_count_after_20261022"] == 170
    assert info["capacity"] == 170
    assert info["registration_status"] == "full"
    assert info["walk_in_standby_allowed"] is True

    dashboard = build_tku_student_dashboard()
    cards = [c for c in dashboard.program_overview if c.title == TKU_OCT22_OVERVIEW_TITLE]
    assert len(cards) == 1
    card_text = " ".join(cards[0].details)
    assert "168 人" in card_text
    assert "170 名 (額滿)" in card_text
    assert "18:10" in card_text
    assert "不是交換名額額滿" in card_text

    pages = tku_processed_pages()
    assert any(
        p.source_url == INFO_SESSION_URL and "2026-10-22" in p.title and "不是交換名額額滿" in p.text
        for p in pages
    )
