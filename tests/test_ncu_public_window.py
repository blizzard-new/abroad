from datetime import datetime

from fastapi.testclient import TestClient

from exchange_info import ncu_student_view
from exchange_info.api import create_app
from exchange_info.models import PartnerUniversity
from exchange_info.seo import partner_path
from exchange_info.university_registry import NCU


def test_public_catalogue_and_planning_follow_ncu_online_and_paper_deadlines(tmp_path, monkeypatch):
    class Clock(datetime):
        @classmethod
        def now(cls, tz=None):
            return now.astimezone(tz)

    monkeypatch.setattr(ncu_student_view, "datetime", Clock)
    client = TestClient(create_app(tmp_path))
    # Keep one application alive; crossing a boundary must invalidate a freshly
    # warmed response even if it has a matching client's previous ETag.
    etag = None
    last_periods = None
    for instant, online, paper, text in [
        ("2026-11-16T08:59:59+08:00", "upcoming", "action_required", "尚未開始受理"),
        ("2026-11-16T09:00:00+08:00", "open", "action_required", "受理中（依來源時窗）"),
        ("2026-12-04T12:00:00+08:00", "open", "action_required", "受理中（依來源時窗）"),
        ("2026-12-04T12:00:01+08:00", "closed", "action_required", "已截止"),
        ("2026-12-11T17:00:01+08:00", "closed", "closed", "已截止"),
    ]:
        now = datetime.fromisoformat(instant)
        headers = {"If-None-Match": etag} if etag and (online, paper) != last_periods else {}
        response = client.get("/student-dashboard", params={"school": "ncu"}, headers=headers)
        assert response.status_code == 200
        dashboard = response.json()
        etag = response.headers["etag"]
        last_periods = (online, paper)
        assert [p["status"] for p in dashboard["application_periods"]] == [online, paper]
        listed = [p for p in dashboard["partner_universities"] if p["quota_status"] in {"published", "fee_paying"}]
        assert {p["application_window_status"] for p in listed} == {online}
        fee = next(p for p in listed if p["quota_status"] == "fee_paying")
        seo = client.get(partner_path(NCU, PartnerUniversity.model_validate(fee)))
        assert seo.status_code == 200 and text in seo.text
        if instant.endswith("08:59:59+08:00"):
            assert response.headers["cache-control"] == "public, max-age=1, stale-while-revalidate=0"
            assert seo.headers["cache-control"] == "public, max-age=1"
        if instant.endswith("12:00:00+08:00"):
            assert response.headers["cache-control"] == "public, max-age=0, stale-while-revalidate=0"
            assert seo.headers["cache-control"] == "public, max-age=0"

    profile = {"academic_year": "116", "application_round": "第一梯次", "college": "工學院", "degree_level": "大學部"}
    plan = client.post("/application-plan/evaluate", json={
        **profile, "home_school": NCU.school_name, "preferences": [{"rank": 1, "school_name": fee["school_name"]}],
    })
    assert plan.status_code == 200
    checks = {c["code"]: c for c in plan.json()["choices"][0]["checks"]}
    assert checks["availability"]["status"] == "pass"
    assert checks["home_deadline"]["status"] == "needs_confirmation"
    assert "線上新申請已截止" in checks["home_deadline"]["detail"]
    assert checks["home_deadline"]["source_url"] == ncu_student_view.NCU_GUIDELINES_URL

    advice = client.post("/advisor/plan", json={**profile, "school_name": NCU.school_name, "target_school": fee["school_name"]})
    assert advice.status_code == 200
    result = advice.json()
    assert "線上新申請已截止" in result["summary"]
    assert any("自費方案" in item for item in result["target_match"]["confirmation_items"])
    assert all("參考資料不代表當期可申請" not in item for item in result["target_match"]["confirmation_items"])
    assert any("線上新申請已截止" in item for item in result["target_match"]["confirmation_items"])
