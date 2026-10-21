from __future__ import annotations

import json
import shutil
from pathlib import Path

from exchange_info.fju_oct21_updates import (
    DASHBOARD_OVERVIEW_TITLE as FJU_OCT21_OVERVIEW_TITLE,
    PARTNER_LIST_40_URL,
    apply_fju_oct21_partner_view,
    apply_fju_oct21_updates,
    validate_fju_oct21_update_snapshot,
)
from exchange_info.fju_student_view import (
    build_fju_student_dashboard,
    fetch_fju_partner_universities,
    fju_exchange_info,
    fju_processed_pages,
)
from exchange_info.models import ExchangeInfo, ProcessedPage, StudentDashboard
from exchange_info.ntu_oct21_updates import (
    AUSTRALIA_PENDING_IDS,
    DASHBOARD_OVERVIEW_TITLE as NTU_OCT21_OVERVIEW_TITLE,
    DETAIL_CHANGED_IDS,
    JAPAN_DETAIL_CHANGED_IDS,
    LIST_URL,
    QUOTA_PUBLISHED_IDS,
    TOEFL_4_0_IDS,
    TOEFL_4_5_IDS,
    apply_oct21_partner_view,
    apply_oct21_updates,
    load_oct21_update,
)
from exchange_info.ntu_student_view import fetch_ntu_partner_universities
from exchange_info.verified_window_deadlines import CATALOG_LAST_CHECKED_AT

ROOT = Path(__file__).resolve().parents[1]
AUDIT_LEDGER = ROOT / "sources" / "audit" / "2026-10-21-daily-22-schools.json"
AUDIT_DOC = ROOT / "docs" / "announcement-updates-2026-10-21.md"
NTU_BUNDLE = ROOT / "src" / "exchange_info" / "official_data" / "ntu"
FJU_BUNDLE = ROOT / "src" / "exchange_info" / "official_data" / "fju"


def test_oct21_22_school_audit_ledger_and_epistemic_boundaries() -> None:
    assert AUDIT_LEDGER.is_file()
    assert AUDIT_DOC.is_file()
    assert CATALOG_LAST_CHECKED_AT == "2026-10-21"

    ledger = json.loads(AUDIT_LEDGER.read_text(encoding="utf-8"))
    assert ledger["audit_id"] == "2026-10-21-daily-22-schools"
    assert ledger["checked_date"] == "2026-10-21"
    assert ledger["total_schools_audited"] == 22
    assert ledger["summary_counts"] == {
        "confirmed_updates": 2,
        "no_change_in_checked_scope": 9,
        "key_scope_incomplete": 2,
        "baseline_established_not_updated_today": 9,
    }

    by_id = {row["school_id"]: row for row in ledger["schools"]}
    assert len(by_id) == 22

    # 1. 2 confirmed updates
    assert {k for k, v in by_id.items() if v["category"] == "confirmed_update"} == {"ntu", "fju"}
    ntu = by_id["ntu"]
    assert ntu["partner_detail_pages_checked"] == 289
    assert ntu["partner_detail_pages_changed"] == 28
    assert ntu["partner_detail_pages_unchanged"] == 261
    assert ntu["list_newly_published_quota_schools"] == 6
    assert ntu["quotas_are_guaranteed_admission"] is False
    assert ntu["attachments_fully_reverieifed"] is False
    assert ntu["new_attachment_links_imply_content_verified"] is False
    assert ntu["japan_detail_changes_mean_list_quota_finalized"] is False
    assert ntu["australia_detail_changes_treated_as_formally_open"] is False
    assert ntu["hyogo_contradiction_resolved_to_sophomore_and_above"] is True
    assert ntu["application_window_unchanged"] == {
        "opens_at": "2026-11-03T10:00:00+08:00",
        "deadline_at": "2026-11-09T16:00:00+08:00",
    }

    fju = by_id["fju"]
    assert fju["general_partner_list_before"] == 234
    assert fju["general_partner_list_after"] == 207
    assert fju["removed_expired_or_suspended_entries"] == 27
    assert fju["removed_27_entries_are_newly_suspended_today"] is False
    assert fju["same_school_other_programs_may_remain"] is True
    assert fju["retained_conditions_and_four_116_1_pdfs_unchanged"] is True
    assert fju["continent_drive_contents_fully_audited"] is False
    assert fju["application_window_unchanged"] == {
        "opens_at": "2026-11-01T00:00:00+08:00",
        "deadline_at": "2026-12-24T16:30:00+08:00",
    }

    # 2. 9 no change in checked scope
    assert {k for k, v in by_id.items() if v["category"] == "no_change_in_checked_scope"} == {
        "cgu",
        "ccu",
        "ncu",
        "tku",
        "scu",
        "ntnu",
        "cycu",
        "yzu",
        "fcu",
    }
    assert by_id["ccu"]["attachments_truncated_or_timed_out_asserted_as_unchanged"] is False
    assert by_id["scu"]["legacy_year_text_contradiction_persists"] is True
    assert by_id["fcu"]["public_query_requires_login"] is False

    # 3. 2 key scope incomplete
    assert {k for k, v in by_id.items() if v["category"] == "key_scope_incomplete"} == {"ntpu", "ntust"}
    assert by_id["ntpu"]["key_scope_complete"] is False
    assert by_id["ntpu"]["preview_deadline_treated_as_final"] is False
    assert by_id["ntpu"]["asserted_as_no_update"] is False
    assert by_id["ntust"]["key_scope_complete"] is False
    assert by_id["ntust"]["asserted_as_no_update"] is False

    # 4. 9 newly established baseline schools (must not be marked updated today)
    baseline_ids = {
        "nsysu",
        "nchu",
        "ntut",
        "nccu",
        "ncku",
        "nycu",
        "nthu",
        "pccu",
        "wzu",
    }
    assert {k for k, v in by_id.items() if v["category"] == "baseline_established_not_updated_today"} == baseline_ids
    for sid in baseline_ids:
        assert by_id[sid]["baseline_expansion_asserted_as_updated_today"] is False
    assert by_id["nsysu"]["other_countries_formal_quotas_verified"] is False
    assert by_id["ntut"]["round_116_formal_guidelines_and_deadlines_verified"] is False
    assert by_id["nycu"]["school_level_115_2_relabeled_as_116"] is False
    assert by_id["nthu"]["ust_channel_conflated_with_nthu_general"] is False
    assert by_id["pccu"]["non_mainland_current_cycle_complete"] is False

    doc_text = AUDIT_DOC.read_text(encoding="utf-8")
    for keyword in (
        "巴黎高等師範學院",
        "里爾天主教大學",
        "巴黎第十大學",
        "特魯瓦科技大學",
        "科諾伯勒阿爾卑斯大學",
        "拉脫維亞大學",
        "橫濱國立大學",
        "金澤大學",
        "長崎大學",
        "一橋大學",
        "兵庫縣立大學",
        "立命館大學",
        "西門菲沙大學",
        "234 條整理為 207 條",
        "五洲別 Google Drive",
    ):
        assert keyword in doc_text


def test_ntu_oct21_quota_and_28_detail_updates_and_idempotency(tmp_path: Path) -> None:
    data = load_oct21_update()
    assert data["counts"] == {
        "partners": 289,
        "detail_pages_checked": 289,
        "detail_pages_changed": 28,
        "detail_pages_unchanged": 261,
        "list_newly_published_quota_schools": 6,
        "positive_quota_schools_total": 34,
        "blank_quota_schools_total": 248,
        "zero_quota_schools_total": 7,
        "academic_year_units_total": 69.5,
        "maximum_persons_total": 130,
    }
    assert {r["portal_id"] for r in data["newly_published_list_quotas"]} == QUOTA_PUBLISHED_IDS
    assert {r["portal_id"] for r in data["changed_detail_pages"]} == DETAIL_CHANGED_IDS

    dashboard = StudentDashboard.model_validate_json(
        (NTU_BUNDLE / "student_dashboard.json").read_text(encoding="utf-8")
    )
    overview_cards = [c for c in dashboard.program_overview if c.title == NTU_OCT21_OVERVIEW_TITLE]
    assert len(overview_cards) == 1
    assert overview_cards[0].source.source_url == LIST_URL

    partners = apply_oct21_partner_view(fetch_ntu_partner_universities())
    by_sn = {p.source_url.rsplit("/", 1)[-1]: p for p in partners}

    # 6 newly published list quotas on 2026-10-21
    expected_quotas = {
        "1301": "1 學年名額（最多 2 人次）",
        "392": "3 學年名額（最多 6 人次）",
        "601": "4 學年名額（最多 8 人次）",
        "67": "3 學年名額（最多 6 人次）",
        "63": "1 學年名額（最多 2 人次）",
        "535": "1 學年名額（最多 2 人次）",
    }
    for pid, q_str in expected_quotas.items():
        partner = by_sn[pid]
        assert partner.quota == q_str
        assert partner.quota_status == "published"
        assert partner.reference_data.get("not_guaranteed_admission") == "true"

    # Japan detail changes keep blank list quotas (quota is None, availability_status == "agreement_only")
    for jp_id in JAPAN_DETAIL_CHANGED_IDS:
        assert by_sn[jp_id].quota is None
        assert by_sn[jp_id].availability_status == "agreement_only"
        assert by_sn[jp_id].reference_data.get("japan_list_quota_finalized_20261021") == "false"

    # Hyogo (sn/978) resolved back to sophomore and above (本校大二學生), no longer conflict
    assert "本校大二學生" in (by_sn["978"].eligibility or "")
    assert "本校大一/大二學生" not in (by_sn["978"].eligibility or "")
    assert by_sn["978"].field_evidence["eligibility"].status == "reference_only"

    # Hitotsubashi (sn/1009) social sciences reserved quota + second exchange marker
    assert "依照合約，此名額保留予社會科學院學生" in by_sn["1009"].reference_data.get(
        "portal_detail_quota_reference_20261021", ""
    )
    assert "第二次出國交換" in (by_sn["1009"].eligibility or "")

    # Ritsumeikan (sn/809) RCE group + GPA 3.00
    assert "RCE" in (by_sn["809"].eligibility or "")
    assert "GPA 達3.00分以上" in (by_sn["809"].eligibility or "")

    # France detail updates
    assert "GPA 達2.95分以上" in (by_sn["392"].eligibility or "")
    assert "B2(中高級)" in (by_sn["601"].eligibility or "")
    assert "國際學院" in (by_sn["67"].eligibility or "")
    assert "GPA 達2.80分以上" in (by_sn["63"].eligibility or "")

    # New-scale TOEFL iBT 4.0 and 4.5
    for pid in TOEFL_4_0_IDS:
        assert "TOEFL iBT 4.0" in (by_sn[pid].eligibility or "")
    for pid in TOEFL_4_5_IDS:
        assert "TOEFL iBT 4.5" in (by_sn[pid].eligibility or "")

    # Australia 10 schools remain pending confirmation and not formally open
    for aus_id in AUSTRALIA_PENDING_IDS:
        aus_p = by_sn[aus_id]
        assert aus_p.quota is None
        assert aus_p.availability_status == "agreement_only"
        assert aus_p.reference_data.get("australia_pending_host_confirmation_20261021") == "true"
        assert "不能當成正式開放" in (aus_p.eligibility or "")
    assert "GPA 達3.30分以上" in (by_sn["313"].eligibility or "")
    assert "GPA 達3.30分以上" in (by_sn["1109"].eligibility or "")
    assert "歷年不得有不及格／不通過科目" in (by_sn["1307"].eligibility or "")

    # Canada SFU (sn/5)
    assert "11/4 00:00–01:00" in (by_sn["5"].eligibility or "")
    assert by_sn["5"].reference_data.get("new_attachment_links_content_verified_20261021") == "false"

    info = ExchangeInfo.model_validate_json((NTU_BUNDLE / "exchange_info.json").read_text(encoding="utf-8"))
    assert any("2026-10-21 查核更新" in s for s in info.eligibility)

    pages = [
        ProcessedPage.model_validate_json(line)
        for line in (NTU_BUNDLE / "pages.jsonl").read_text(encoding="utf-8")
        .splitlines()
        if line.strip()
    ]
    assert any(p.source_url == LIST_URL and "2026-10-21" in p.title for p in pages)

    # Byte idempotency of apply_oct21_updates
    work = tmp_path / "ntu"
    shutil.copytree(NTU_BUNDLE, work)
    before = {p.name: p.read_bytes() for p in work.iterdir() if p.is_file()}
    apply_oct21_updates(work)
    after = {p.name: p.read_bytes() for p in work.iterdir() if p.is_file()}
    assert before == after


def test_fju_oct21_partner_cleanup_and_continent_drives_and_idempotency(tmp_path: Path) -> None:
    payload = validate_fju_oct21_update_snapshot()
    assert payload["general_partner_list_before"] == 234
    assert payload["general_partner_list_after"] == 207
    assert payload["removed_expired_or_suspended_entries_count"] == 27
    assert payload["removed_27_entries_are_newly_suspended_today"] is False
    assert payload["same_school_other_programs_may_remain"] is True
    assert payload["retained_conditions_and_four_116_1_pdfs_unchanged"] is True
    assert payload["continent_drive_contents_fully_audited"] is False
    assert len(payload["continent_google_drive_portals"]) == 5

    all_partners = fetch_fju_partner_universities()
    assert len(all_partners) == 234
    assert sum(
        1 for p in all_partners if p.reference_data.get("label_40_status_20261021") == "retained_in_207"
    ) == 207
    assert sum(
        1
        for p in all_partners
        if p.reference_data.get("label_40_status_20261021")
        == "removed_expired_or_suspended_in_20261021_cleanup"
    ) == 27

    active_207 = apply_fju_oct21_partner_view(all_partners)
    assert len(active_207) == 207
    active_names = {p.school_name for p in active_207}
    # Same-school other programs remain in the 207 list (e.g., 聖心女子大學, 梅光學院大學)
    assert any("聖心女子大學" in name and "語言密集課程" not in name for name in active_names)
    assert any("梅光學院大學" in name and "自費" not in name for name in active_names)
    assert not any("聖愛德華大學" in name for name in active_names)

    dashboard = build_fju_student_dashboard()
    overview_cards = [c for c in dashboard.program_overview if c.title == FJU_OCT21_OVERVIEW_TITLE]
    assert len(overview_cards) == 1
    assert overview_cards[0].source.source_url == PARTNER_LIST_40_URL

    info = fju_exchange_info()
    assert PARTNER_LIST_40_URL in info.source_urls
    assert any("234 條整理為 207 條" in line for line in info.application_period)

    pages = fju_processed_pages()
    assert any(p.source_url == PARTNER_LIST_40_URL and "2026-10-21" in p.title for p in pages)

    # Byte idempotency of apply_fju_oct21_updates
    work = tmp_path / "fju"
    shutil.copytree(FJU_BUNDLE, work)
    before = {p.name: p.read_bytes() for p in work.iterdir() if p.is_file()}
    apply_fju_oct21_updates(work)
    after = {p.name: p.read_bytes() for p in work.iterdir() if p.is_file()}
    assert before == after
