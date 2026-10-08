"""Library services and other-year orientation never become application rules."""

import json

from fastapi.testclient import TestClient

from exchange_info.api import create_app
from exchange_info.ccu_profile import reviewed_profiles
from exchange_info.ccu_sources import BUNDLE, HOME
from exchange_info.ccu_student_view import fetch_ccu_partner_universities


def at(page):
    return next(
        p for p in fetch_ccu_partner_universities() if p.source_pages[0] == page
    )


def test_library_activation_is_life_information_and_new_student_guide_is_reference(
    tmp_path,
):
    profiles = reviewed_profiles()
    library = profiles[23]["fields"]["campus_life"]
    assert library["status"] == "needs_confirmation"
    assert "院方簽名／蓋章" in library["value"]
    assert "不是交換申請附件" in library["value"]
    welcome = profiles[24]["fields"]["campus_life"]
    assert welcome["status"] == "reference_only" and "2026年9月" in welcome["value"]
    client = TestClient(create_app(tmp_path))
    result = client.get(
        "/destination-profile",
        params={"home_school": HOME, "school": at(23).school_name},
    )
    assert result.status_code == 200
    assert "圖書館" in result.json()["campus_life_summary"]
    flow = client.get(
        "/application-workflow",
        params={"home_school": HOME, "school": at(23).school_name},
    ).json()
    host_names = [
        r["name"]
        for s in flow["steps"]
        for r in s["document_requirements"]
        if r["stage"]
    ]
    assert not any("借閱" in n or "圖書館" in n for n in host_names)


def test_javascript_shell_is_recorded_without_using_search_snippets_as_policy():
    source = json.loads(
        (
            BUNDLE / "overseas_sources/p67-r15-international-exchange-support.json"
        ).read_text()
    )
    assert source["http_status"] == 200 and source["access_result"] == "empty_response"
    assert "JavaScript外殼" in source["content_review_note"]
    field = reviewed_profiles()[67]["fields"]["campus_life"]
    assert field["status"] == "missing" and field["value"] is None
    ledger = json.loads((BUNDLE / "fifteenth-life-changes.json").read_text())
    assert not ledger["complete_research_claimed"]
    assert ledger["overseas_17_field_policy_changes"] == 0
