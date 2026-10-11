"""Actual dynamic public bodies keep field, year and attachment scopes apart."""

import hashlib
import json
from pathlib import Path

from fastapi.testclient import TestClient

from exchange_info.api import create_app
from exchange_info.ccu_student_view import fetch_ccu_partner_universities

B = Path(__file__).resolve().parents[1] / "src/exchange_info/official_data/ccu"


def read(name):
    return json.loads((B / name).read_text())


def test_ten_historical_render_bodies_remain_preserved_with_actual_read_proof():
    reviews = read("twentysixth-source-review.json")
    assert reviews["new_source_count"] == len(reviews["source_reviews"]) == 10
    assert not reviews["public_sources_exhausted"]
    for entry in reviews["source_reviews"]:
        source = read("overseas_sources/" + entry["source_id"] + ".json")
        assert source["sha256"] == entry["sha256"] == hashlib.sha256((B / source["bundled_file"]).read_bytes()).hexdigest()
        assert source["text_sha256"] == entry["text_sha256"] == hashlib.sha256(json.dumps(source["text_pages"], ensure_ascii=False).encode()).hexdigest()
        assert entry["checked_at"] and entry["academic_year"] and entry["source_url"]
        for proof in entry["body_evidence"]:
            body = " ".join(" ".join(source["text_pages"][p - 1] for p in proof["source_pages"]).split())
            assert proof["excerpt"] in body
        assert not entry["all_policy_review_complete"]
        assert entry["security_revalidation"]


def test_mapua_calendar_dates_do_not_repair_nomination_or_old_costs():
    partner = next(p for p in fetch_ccu_partner_universities() if p.source_pages[0] == 83)
    fields = partner.partner_exchange_details
    assert fields["academic_calendar"].status == "verified_current"
    assert "2027-02-01" in fields["academic_calendar"].value
    assert "2027-05-03" in fields["academic_calendar"].value
    assert fields["application_deadline"].status == fields["costs"].status == "conflict"
    assert fields["nomination_deadline"].status == fields["insurance"].status == "needs_confirmation"
    assert "2026-10-31" not in fields["nomination_deadline"].value
    assert any(e.source_url == "https://fs2.mapua.edu.ph/MapuaWebsite7/ILRAD/Handbook/International%20Hand%20Book.pdf" and e.source_pages == [32] for e in fields["insurance"].evidence)
    amu = next(p for p in fetch_ccu_partner_universities() if p.source_pages[0] == 95)
    assert amu.partner_exchange_details["insurance"].status == "needs_confirmation"
    assert all(e.source_url != read("overseas_sources/p95-r5-healthcare.json")["source_url"] for e in amu.partner_exchange_details["insurance"].evidence)
    hcmute = next(p for p in fetch_ccu_partner_universities() if p.source_pages[0] == 68)
    assert hcmute.partner_exchange_details["arrival"].status == "missing"
    assert any(e["source_id"] == "p68-r17-support-flow" and e["status"] == "needs_confirmation" for r in read("overseas-reviewed-fields.json") if r["ccu_page"] == 68 for e in r["fields"]["program_scope"]["evidence"])


def test_normal_tls_uninter_metadata_reaches_api_without_claiming_rendered_question_count(tmp_path):
    partner = next(p for p in fetch_ccu_partner_universities() if p.source_pages[0] == 119)
    field = partner.partner_exchange_details["application_forms"]
    assert field.status == "needs_confirmation"
    assert "48" in field.value and "題目清單" in field.value and "LearningAgreement" in field.value
    assert "顯示/分支/必填" in field.value
    assert all(e.source_url != read("overseas_sources/p119-r26-current-form-render.json")["source_url"] for e in field.evidence)
    client = TestClient(create_app(tmp_path))
    response = client.get("/application-center/catalog", params={"school": "國立中正大學", "target_school": partner.school_name})
    assert response.status_code == 200
    form = next(item for item in response.json()["items"] if item["name"] == "線上學生申請")
    assert form["official_form_url"] == "https://forms.cloud.microsoft/pages/responsepage.aspx?id=gWd1pYkTdUCPx8y846u5dfSkBbb_y55OpNehuuGtgkFURFVLRVpXRk5SV05CMDJYNkNBVVE5NkFLTy4u&route=shorturl"
    assert form["applicability_status"] == "verified_current"
    assert form["official_form_verified"] is False  # This flag checks downloaded attachment hashes.
    assert "48" in form["applicability_note"] and "仍待核" in form["applicability_note"]
