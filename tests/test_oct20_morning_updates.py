from __future__ import annotations

import json
import shutil
from pathlib import Path

from exchange_info.application_writing_guidance import WRITING_RULES
from exchange_info.fju_oct20_updates import (
    NEWS_1062_URL,
    ONLINE_PORTAL_URL,
    apply_fju_oct20_updates,
    validate_fju_oct20_update_snapshot,
)
from exchange_info.fju_student_view import (
    build_fju_student_dashboard,
    fetch_fju_partner_universities,
    fju_exchange_info,
    fju_processed_pages,
)
from exchange_info.models import ExchangeInfo, ProcessedPage, StudentDashboard
from exchange_info.ntu_oct20_updates import (
    DASHBOARD_OVERVIEW_TITLE,
    DETAIL_CHANGED_IDS,
    LIST_URL,
    QUOTA_PUBLISHED_IDS,
    UK_QUOTA_ONLY_IDS,
    apply_oct20_partner_view,
    apply_oct20_updates,
    load_oct20_update,
)
from exchange_info.ntu_student_view import fetch_ntu_partner_universities
from exchange_info.tku_oct20_updates import (
    INFO_SESSION_URL,
    validate_tku_oct20_update_snapshot,
)
from exchange_info.tku_student_view import (
    build_tku_student_dashboard,
    tku_processed_pages,
)
from exchange_info.verified_window_deadlines import get_verified_school_window_card

ROOT = Path(__file__).resolve().parents[1]
AUDIT_LEDGER = ROOT / "sources" / "audit" / "2026-10-20-morning-13-schools.json"
AUDIT_DOC = ROOT / "docs" / "announcement-updates-2026-10-20.md"
NTU_BUNDLE = ROOT / "src" / "exchange_info" / "official_data" / "ntu"
FJU_BUNDLE = ROOT / "src" / "exchange_info" / "official_data" / "fju"


def test_oct20_13_school_audit_ledger_and_epistemic_boundaries() -> None:
    assert AUDIT_LEDGER.is_file()
    assert AUDIT_DOC.is_file()

    ledger = json.loads(AUDIT_LEDGER.read_text(encoding="utf-8"))
    assert ledger["audit_id"] == "2026-10-20-morning-13-schools"
    assert ledger["checked_date"] == "2026-10-20"
    assert ledger["total_schools_audited"] == 13
    assert ledger["summary_counts"] == {
        "confirmed_updates": 3,
        "no_change_or_baseline_expanded": 8,
        "key_scope_incomplete": 2,
    }

    by_id = {row["school_id"]: row for row in ledger["schools"]}
    assert set(by_id) == {
        "ntu",
        "tku",
        "fju",
        "cgu",
        "ncu",
        "ccu",
        "scu",
        "yzu",
        "cycu",
        "ntnu",
        "fcu",
        "ntpu",
        "ntust",
    }

    # 3 confirmed updates
    assert {k for k, v in by_id.items() if v["category"] == "confirmed_update"} == {"ntu", "tku", "fju"}
    assert by_id["ntu"]["partner_detail_pages_checked"] == 289
    assert by_id["ntu"]["partner_detail_pages_changed"] == 6
    assert by_id["ntu"]["partner_detail_pages_unchanged"] == 283
    assert by_id["ntu"]["list_newly_published_quota_schools"] == 8
    assert by_id["ntu"]["hyogo_freshman_eligibility_accepted"] is False

    assert by_id["tku"]["treated_as_exchange_application_deadline"] is False
    assert by_id["tku"]["applies_to_all_japan_exchange_students"] is False
    assert by_id["tku"]["attachments_verified"] == 4

    assert by_id["fju"]["title_says_immediate_open"] is True
    assert by_id["fju"]["actual_opens_at"] == "2026-11-01T00:00:00+08:00"
    assert by_id["fju"]["actual_deadline_at"] == "2026-12-24T16:30:00+08:00"
    assert by_id["fju"]["online_system_campus_network_only"] is True
    assert by_id["fju"]["final_partner_list_and_quotas_confirmed"] is False
    assert by_id["fju"]["pdfs_verified"] == 4
    assert by_id["fju"]["m365_login_required_partner_sheets_audited"] is False

    # 8 no change / baseline expanded
    assert {k for k, v in by_id.items() if v["category"] == "no_change_or_baseline_expanded"} == {
        "cgu",
        "ncu",
        "ccu",
        "scu",
        "yzu",
        "cycu",
        "ntnu",
        "fcu",
    }
    assert by_id["cgu"]["form_closed_asserted_as_changed_today"] is False
    for sid in ("ncu", "yzu", "ntnu", "fcu"):
        assert by_id[sid]["baseline_expansion_asserted_as_updated_today"] is False

    # 2 key scope incomplete
    assert {k for k, v in by_id.items() if v["category"] == "key_scope_incomplete"} == {"ntpu", "ntust"}
    for sid in ("ntpu", "ntust"):
        assert by_id[sid]["can_assert_no_update"] is False

    doc_text = AUDIT_DOC.read_text(encoding="utf-8")
    for keyword in (
        "拉德堡",
        "阿姆斯特丹自由",
        "烏特列支",
        "奧斯陸",
        "杜倫",
        "肯特",
        "愛丁堡",
        "南安普頓",
        "近畿",
        "兵庫縣立",
        "auix1106",
        "日本台灣交流協會",
        "newsID=1062",
        "2026/11/01",
        "12/24 16:30",
    ):
        assert keyword in doc_text


def test_ntu_oct20_quota_and_detail_updates_and_idempotency(tmp_path: Path) -> None:
    data = load_oct20_update()
    assert data["counts"]["partners"] == 289
    assert data["counts"]["detail_pages_checked"] == 289
    assert data["counts"]["detail_pages_changed"] == 6
    assert data["counts"]["detail_pages_unchanged"] == 283
    assert data["counts"]["list_newly_published_quota_schools"] == 8
    assert set(data["uk_quota_only_unchanged_detail_ids"]) == UK_QUOTA_ONLY_IDS
    assert {r["portal_id"] for r in data["newly_published_list_quotas"]} == QUOTA_PUBLISHED_IDS
    assert {r["portal_id"] for r in data["changed_detail_pages"]} == DETAIL_CHANGED_IDS

    dashboard = StudentDashboard.model_validate_json(
        (NTU_BUNDLE / "student_dashboard.json").read_text(encoding="utf-8")
    )
    overview_cards = [c for c in dashboard.program_overview if c.title == DASHBOARD_OVERVIEW_TITLE]
    assert len(overview_cards) == 1
    assert overview_cards[0].source.source_url == LIST_URL

    partners = apply_oct20_partner_view(fetch_ntu_partner_universities())
    by_sn = {p.source_url.rsplit("/", 1)[-1]: p for p in partners}

    # 8 schools with newly published list quotas
    expected_quotas = {
        "1092": "1 學年名額（最多 2 人次）",
        "187": "3 學年名額（最多 4 人次）",
        "80": "3 學年名額（最多 6 人次）",
        "82": "2 學年名額（最多 4 人次）",
        "1291": "2 學年名額（最多 2 人次）",
        "1093": "1 學年名額（最多 2 人次）",
        "604": "0.5 學年名額（最多 1 人次）",
        "90": "1 學年名額（最多 2 人次）",
    }
    for pid, q_str in expected_quotas.items():
        partner = by_sn[pid]
        assert partner.quota == q_str
        assert partner.quota_status == "published"

    # Detail page specific checks
    assert "第二次出國交換" in (by_sn["1092"].eligibility or "")
    assert "TOEFL iBT 4.0" in (by_sn["1092"].eligibility or "")
    assert "不接受法律學院之學生申請" in (by_sn["1092"].eligibility or "")

    assert "TOEFL iBT 5.0" in (by_sn["187"].eligibility or "")
    assert "全學年3名" in by_sn["187"].reference_data.get("portal_detail_quota_reference_20261020", "")

    assert "TOEFL iBT 4.0" in (by_sn["82"].eligibility or "")
    assert "TOEFL iBT 4.5" in (by_sn["82"].eligibility or "")

    assert "讀 4.5 聽 4.5 說 4.5 寫 4.5" in (by_sn["80"].eligibility or "")

    # Kindai and Hyogo keep blank list quotas (quota is None, availability_status == "agreement_only")
    assert by_sn["1187"].quota is None
    assert by_sn["1187"].availability_status == "agreement_only"
    assert "TOEFL iBT 4.5" in (by_sn["1187"].eligibility or "")

    assert by_sn["978"].quota is None
    assert by_sn["978"].availability_status == "agreement_only"
    assert "不能據此認定大一可申請" in (by_sn["978"].eligibility or "")
    assert by_sn["978"].field_evidence["eligibility"].status == "conflict"

    info = ExchangeInfo.model_validate_json((NTU_BUNDLE / "exchange_info.json").read_text(encoding="utf-8"))
    assert any("2026-10-20 查核更新" in s for s in info.eligibility)

    pages = [
        ProcessedPage.model_validate_json(line)
        for line in (NTU_BUNDLE / "pages.jsonl").read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    assert any(p.source_url == LIST_URL and "2026-10-20" in p.title for p in pages)

    # Byte idempotency of apply_oct20_updates
    work = tmp_path / "ntu"
    shutil.copytree(NTU_BUNDLE, work)
    before = {p.name: p.read_bytes() for p in work.iterdir() if p.is_file()}
    apply_oct20_updates(work)
    after = {p.name: p.read_bytes() for p in work.iterdir() if p.is_file()}
    assert before == after


def test_tku_oct20_info_session_and_jtea_scholarship_updates() -> None:
    payload = validate_tku_oct20_update_snapshot()
    assert payload["treated_as_exchange_application_deadline"] is False
    assert payload["applies_to_all_japan_exchange_students"] is False
    assert payload["jtea_scholarship"]["attachments_verified"] == 4

    dashboard = build_tku_student_dashboard()
    overview_titles = [item.title for item in dashboard.program_overview]
    assert any("2027–2028 年赴姊妹校交換生聯合甄選說明會" in t for t in overview_titles)

    sch_titles = [item.title for item in dashboard.scholarship_info]
    assert any("2027 年度第一期日本台灣交流協會獎學金" in t for t in sch_titles)
    jtea_card = next(item for item in dashboard.scholarship_info if "日本台灣交流協會" in item.title)
    jtea_text = " ".join(jtea_card.details)
    assert "2026/10/30" in jtea_text
    assert "8 萬" in jtea_text
    assert "不是所有赴日交換生都適用" in jtea_text

    source_urls = {s.source_url for s in dashboard.sources}
    assert INFO_SESSION_URL in source_urls

    pages = tku_processed_pages()
    assert any(p.source_url == INFO_SESSION_URL and p.category == "info_session" for p in pages)
    assert any("日本台灣交流協會" in p.title and p.category == "scholarship" for p in pages)


def test_fju_oct20_116_1_announcement_and_idempotency(tmp_path: Path) -> None:
    payload = validate_fju_oct20_update_snapshot()
    assert payload["title_says_immediate_open"] is True
    assert payload["actual_system_and_submission_opens_at"] == "2026-11-01T00:00:00+08:00"
    assert payload["actual_system_and_submission_deadline_at"] == "2026-12-24T16:30:00+08:00"
    assert payload["online_system_campus_network_only"] is True
    assert payload["final_partner_list_and_quotas_confirmed"] is False

    dashboard = build_fju_student_dashboard()
    round_116 = next(
        p for p in dashboard.application_periods if p.academic_year == "116" and "說明會" not in (p.application_round or "")
    )
    assert round_116.date_status == "verified_exact"
    assert round_116.opens_at.isoformat() == "2026-11-01T00:00:00+08:00"
    assert round_116.deadline_at.isoformat() == "2026-12-24T16:30:00+08:00"
    assert round_116.source.source_url == NEWS_1062_URL
    assert any(ONLINE_PORTAL_URL in d for d in round_116.details)
    assert any("11 月陸續" in d and "不能當成最終版" in d for d in round_116.details)

    info = fju_exchange_info()
    assert NEWS_1062_URL in info.source_urls
    assert any("至少 500 字" in d and "不需繳交英文版" in d for d in info.required_documents)

    pages = fju_processed_pages()
    news_pages = [p for p in pages if p.source_url == NEWS_1062_URL]
    assert len(news_pages) == 1
    assert len(news_pages[0].attachments) == 4

    # Partners remain reference_only / agreement_only because Nov list is non-final
    partners = fetch_fju_partner_universities()
    assert len(partners) == 234
    assert all(p.quota_status == "reference_only" for p in partners)
    assert all(p.availability_status == "agreement_only" for p in partners)
    assert all("2026/11/01 至 2026/12/24 16:30" in (p.application_deadline or "") for p in partners)

    # Writing guidance and verified window deadline card
    fju_study_plan_rule = WRITING_RULES[("fju", "study-plan")]
    assert fju_study_plan_rule.min_chars == 500
    assert fju_study_plan_rule.source_url == NEWS_1062_URL
    assert fju_study_plan_rule.last_checked_at == "2026-10-20"

    fju_card = get_verified_school_window_card("fju")
    assert fju_card.window_status == "upcoming"
    assert fju_card.primary_deadline_date == "2026-12-24"
    assert fju_card.online_deadline.exact_deadline_at.isoformat() == "2026-12-24T16:30:00+08:00"
    assert fju_card.study_plan_limit.min_chars == 500

    # Byte idempotency of apply_fju_oct20_updates
    work = tmp_path / "fju"
    shutil.copytree(FJU_BUNDLE, work)
    before = {p.name: p.read_bytes() for p in work.iterdir() if p.is_file()}
    apply_fju_oct20_updates(work)
    after = {p.name: p.read_bytes() for p in work.iterdir() if p.is_file()}
    assert before == after
