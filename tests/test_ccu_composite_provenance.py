"""New API/image claims keep their own provenance alongside older factsheets."""

import json

import pytest
from fastapi.testclient import TestClient

from exchange_info.api import create_app
from exchange_info.ccu_sources import BUNDLE, HOME
from exchange_info.ccu_student_view import fetch_ccu_partner_universities


@pytest.mark.parametrize("source_page,key,sid,claim,pdf_page,medium", [
    (119, "application_forms", "p119-r27-form-metadata-normal-tls", "清單列48項", 5, "公開題目API原文"),
    (83, "academic_calendar", "p83-r27-calendar-image-normal-tls", "2027-02-01至04-24", 2, "官方校曆影像原文"),
])
def test_bundled_artifacts_and_real_api_keep_both_source_dates(tmp_path, source_page, key, sid, claim, pdf_page, medium):
    partner = next(p for p in fetch_ccu_partner_universities() if p.source_pages[0] == source_page)
    raw = json.loads((BUNDLE / "overseas_sources" / (sid + ".json")).read_text())
    field = partner.partner_exchange_details[key]
    fresh = next(e for e in field.evidence if e.source_url == raw["source_url"])
    assert fresh.source_pages == [] and fresh.checked_at.isoformat().startswith("2026-10-09")
    old = next(e for e in field.evidence if e.source_url != fresh.source_url)
    assert old.source_pages == [pdf_page] and old.checked_at.isoformat().startswith("2026-10-08")
    client = TestClient(create_app(tmp_path))
    response = client.get("/application-workflow", params={"home_school": HOME, "school": partner.school_name})
    assert response.status_code == 200
    actual = response.json()
    bundled = next(json.loads(line) for line in (BUNDLE / "application_workflows.jsonl").read_text().splitlines()
                   if json.loads(line)["school_name"] == partner.school_name)
    for workflow in [bundled, actual]:
        detail = next(text for step in workflow["steps"] for text in step["details"] if claim in text)
        assert f"PDF第{pdf_page}頁；查核2026-10-08" in detail
        assert f"{medium}；查核2026-10-09" in detail
        assert "依據1：" in detail and "依據2：" in detail
        sources = [s for s in workflow["sources"] if s["source_url"] == fresh.source_url]
        assert any(medium in s["title"] and "查核2026-10-09" in s["title"] for s in sources)
        if source_page == 119:
            document = next(text for step in workflow["steps"] for text in step["details"]
                            if text.startswith("線上學生申請 · 階段"))
            assert "PDF第5頁；查核2026-10-08" in document
            assert "公開題目API原文；查核2026-10-09" in document
    profile = next(json.loads(line) for line in (BUNDLE / "destination_profiles.jsonl").read_text().splitlines()
                   if json.loads(line)["school_name"] == partner.school_name)
    if source_page == 83:
        section = next(s for s in profile["student_guide_sections"] if s["key"] == key)
        assert "官方校曆影像原文；查核2026-10-09" in section["points"][0]
        assert "PDF第2頁；查核2026-10-08" in section["points"][0]
