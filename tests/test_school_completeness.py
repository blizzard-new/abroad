from __future__ import annotations

import hashlib
from collections import Counter
from datetime import timedelta

from fastapi.testclient import TestClient

from exchange_info import storage
from exchange_info.api import create_app
from exchange_info.application_rules import select_application_workflow
from exchange_info.models import (
    AccountSessionRecord,
    UserAccount,
    utc_now,
    ApplicationRuleContext,
    DestinationProfile,
    PartnerUniversity,
    SourceReference,
)
from exchange_info.school_completeness import build_school_completeness
from exchange_info.storage import save_account_sessions, save_user_accounts

SOURCE = "https://example.edu/source"


def by_key(result):
    return {row.key: row for row in result.items}


def partner(**kwargs):
    return PartnerUniversity(program_type="交換", school_name="測試大學", country="日本", source_url=SOURCE, **kwargs)


def test_empty_school_reports_every_gap_without_filling_any():
    result = build_school_completeness(partner(), None, None)
    rows = by_key(result)
    assert result.available_count == 0 and result.score < 0.2
    assert rows["workflow"].status == "missing" and rows["cost"].status == "missing"
    assert result.priority_gaps[:2] == ["申請資格與範圍", "申請期限"]
    assert "不代表學校沒有公開" in result.disclaimer


def test_available_partial_and_unpublished_statuses_are_distinguished():
    profile = DestinationProfile(
        school_name="測試大學", city="東京",
        cost_summary="校方建議國際生每月生活費約 JPY 80,000–150,000。",
        housing_summary="官方網站未公開可核對的住宿費用。",
        transport_summary="車站步行 10 分鐘，可搭乘地鐵。",
        campus_life_summary="Student clubs are listed on the official page.",
        sources=[SourceReference(title="官方", source_url=SOURCE)],
    )
    rows = by_key(build_school_completeness(partner(colleges="商學院", degree_levels="大學部", eligibility="IELTS 6.0"), profile, None))
    assert rows["eligibility"].status == "available"
    assert rows["cost"].status == "available"
    assert rows["housing"].status == "missing" and "需向學校確認" in rows["housing"].note
    assert rows["transport"].status == "available" and rows["city"].status == "available"
    assert rows["chinese"].status == "partial"


def test_bundled_ntpu_school_has_workflow_documents_but_no_exact_deadline():
    workflows = [row for row in storage.load_bundled_application_workflows() if row.home_university == "國立臺北大學"]
    workflow = select_application_workflow(workflows, ApplicationRuleContext(
        home_university="國立臺北大學", partner_university=workflows[0].school_name))
    rows = by_key(build_school_completeness(partner(), None, workflow))
    assert rows["workflow"].status in {"available", "needs_confirmation"}
    assert rows["documents"].status in {"available", "partial"}
    assert rows["deadline"].status in {"needs_confirmation", "available"}


def test_every_bundled_destination_profile_scores_and_never_claims_more_than_it_has():
    profiles = storage.load_destination_profiles()
    scores = []
    for profile in profiles:
        result = build_school_completeness(
            PartnerUniversity(program_type="交換", school_name=profile.school_name, source_url=SOURCE), profile, None)
        expected_fields = 17 if profile.home_university == "國立中央大學" else 10
        assert 0 <= result.score <= 1 and result.total_count == len(result.items) == expected_fields
        if profile.home_university == "國立中央大學":
            assert by_key(result)["quota"].status == "needs_confirmation"
        else:
            assert by_key(result)["workflow"].status == "missing"
        scores.append(result.score)
    # New schools add profiles; explicitly preserve all existing home scopes.
    # Preserve FJU program identities alongside the six schools added on main.
    assert Counter(p.home_university for p in profiles)=={'長庚大學':77,'國立臺北大學':206,'國立臺灣大學':289,'國立中央大學':214,'國立中正大學':104,'淡江大學':287,'天主教輔仁大學':237,'東吳大學':191,'國立臺灣師範大學':236,'中原大學':89,'國立臺灣科技大學':237,'元智大學':90,'逢甲大學':161,'國立中山大學':218,'國立中興大學':226,'國立臺北科技大學':206,'國立政治大學':266,'國立成功大學':211,'國立陽明交通大學':243,'國立清華大學':176,'中國文化大學':135,'文藻外語大學':147,'國立高雄科技大學':107,'國立雲林科技大學':112,'國立臺灣海洋大學':123,'國立彰化師範大學':108,'國立高雄師範大學':143,'臺北醫學大學':201,'中山醫學大學':124,'中國醫藥大學':174,'高雄醫學大學':188,'銘傳大學':202,'國立臺北商業大學':93,'國立暨南國際大學':212,'國立東華大學':163,'東海大學':274,'世新大學':177,'靜宜大學':275,'實踐大學':125,'國立高雄大學':280,'國立嘉義大學':140,'國立臺中科技大學':140,'國立虎尾科技大學':152,'臺北市立大學':226,'國立臺中教育大學':263,'國立臺北藝術大學':90,'國立臺灣藝術大學':102,'國立臺北教育大學':143,'國立勤益科技大學':134,'國立屏東科技大學':309,'國立金門大學':64}
    assert len(scores) == 9090 and max(scores) < 1


def test_endpoint_returns_completeness_for_a_supported_partner(tmp_path):
    account = UserAccount(display_name="北大學生", student_status_verified=True,
                          verified_university="國立臺北大學", school_email_verified=True)
    save_user_accounts([account], tmp_path)
    save_account_sessions([AccountSessionRecord(
        account_id=account.id, token_hash=hashlib.sha256(b"completeness-token").hexdigest(),
        expires_at=utc_now() + timedelta(days=1))], tmp_path)
    client = TestClient(create_app(tmp_path))
    client.headers.update({"Authorization": "Bearer completeness-token"})
    assert client.get("/school-data-completeness", params={"school": "x大學"}, headers={"Authorization": ""}).status_code == 404
    partners = client.get("/student-dashboard", params={"school": "國立臺北大學"}).json()["partner_universities"]
    name = next(row["school_name"] for row in partners if row.get("availability_status", "open") == "open")
    response = client.get("/school-data-completeness", params={"school": name, "home_school": "國立臺北大學"})
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["school_name"] == name and body["total_count"] == 10
    assert {row["key"] for row in body["items"]} >= {"eligibility", "deadline", "workflow", "documents", "cost"}
    assert client.get("/school-data-completeness", params={"school": "不存在大學", "home_school": "國立臺北大學"}).status_code == 404


def test_pdf_extraction_noise_does_not_hide_a_schools_workflow():
    from exchange_info.ntpu_student_view import fetch_ntpu_partner_universities
    from exchange_info.school_identity import same_school

    workflows = [row for row in storage.load_bundled_application_workflows() if row.home_university == "國立臺北大學"]
    context_home = "國立臺北大學"
    missing = [
        partner.school_name for partner in fetch_ntpu_partner_universities()
        if select_application_workflow(workflows, ApplicationRuleContext(
            home_university=context_home, partner_university=partner.school_name)) is None
    ]
    assert missing == []
    assert same_school("弗羅茨瓦夫大學(University of Wroc ław)", "弗羅茨瓦夫大學(University of Wrocław)")
    assert same_school("圖里巴大學(Tur ība University)", "圖里巴大學(Turība University)")
    assert not same_school("越南胡志明市國際大學 Vietnam National University, Ho Chi Minh City",
                           "越南胡志明市經濟與法律大學(University of Economics and Law)")
    assert not same_school("University of Economics", "University of Economics and Law")
