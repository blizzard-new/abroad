"""Newest host versions, visible PDF policy and anonymous public JSON evidence."""

import hashlib
import importlib.util
import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from exchange_info.api import create_app
from exchange_info.ccu_documents import reviewed_documents
from exchange_info.ccu_overseas import reviewed_rows
from exchange_info.ccu_profile import reviewed_profiles
from exchange_info.ccu_sources import BUNDLE, HOME
from exchange_info.ccu_student_view import fetch_ccu_partner_universities


def at(page):
    return next(p for p in fetch_ccu_partner_universities() if p.source_pages[0] == page)


def test_updated_hcmut_dates_replace_march_and_old_year_is_reference(tmp_path):
    fields = reviewed_rows()[67]["fields"]
    assert fields["nomination_deadline"]["status"] == "verified_current"
    assert "2026-09-30" in fields["nomination_deadline"]["value"]
    assert fields["application_deadline"]["status"] == "verified_current"
    assert "2026-10-15" in fields["application_deadline"]["value"]
    assert "2027-01-08" in fields["arrival"]["value"]
    assert "2027-01-11" in fields["academic_calendar"]["value"]
    assert "2027-06-07" in fields["academic_calendar"]["value"]
    client = TestClient(create_app(tmp_path))
    flow = client.get(
        "/application-workflow", params={"home_school": HOME, "school": at(67).school_name}
    ).json()
    assert "2026-10-15" in flow["steps"][4]["timing"]
    assert flow["review_status"] == "legacy"
    for sid in ["p67-mirror", "p67-hostw1", "p67-r16-old-news-public-api"]:
        source = json.loads((BUNDLE / "overseas_sources" / f"{sid}.json").read_text())
        assert source["content_applicability"] == "reference_only"
    changes = json.loads((BUNDLE / "sixteenth-pass-changes.json").read_text())
    previous = {r["field"]: r["before"] for r in changes["changes"]}
    assert previous["application_deadline"]["status"] == "conflict"
    assert not changes["complete_research_claimed"]


def test_visible_visa_policy_excludes_hidden_pdf_extraction_residue():
    new = json.loads(
        (BUNDLE / "overseas_sources/p67-r16-factsheet-updated2027.json").read_text()
    )
    old = json.loads(
        (BUNDLE / "overseas_sources/p67-r16-march-factsheet-reference.json").read_text()
    )
    assert "Kyoto" in new["text_pages"][3] and "Kyoto" in old["text_pages"][3]
    assert new["render_review"]["physical_pages"] == [1, 4]
    assert old["render_review"]["physical_pages"] == [4]
    root = Path(__file__).resolve().parents[1]
    for source in [new, old]:
        for path in source["render_review"]["screenshots"]:
            assert (root / path).is_file()
    visa = reviewed_rows()[67]["fields"]["visa"]
    assert visa["status"] == "verified_current"
    assert "Vietnam Immigration" in visa["value"]
    assert "Kyoto" not in visa["value"] and "CoE" not in visa["value"]
    assert all("Kyoto" not in e["excerpt"] for e in visa["evidence"])


def test_current_hcmut_templates_stages_and_unread_online_form(tmp_path):
    row = reviewed_documents()[67]
    assert len(row["requirements"]) == 9
    nomination = next(r for r in row["requirements"] if r["stage"] == "nomination")
    assert nomination["requirement"]["signatures"] == ["母校負責人"]
    assert "Seal" in nomination["requirement"]["stamps"][0]
    insurance = next(r for r in row["requirements"] if r["stage"] == "post_offer")
    assert "到校前一週" in insurance["requirement"]["name"]
    for r in row["requirements"]:
        if r["requirement"]["name"] == "護照copy":
            assert r["requirement"]["copies"] == 1
            assert r["requirement"]["copy_type"] == "copy"
    forms = reviewed_rows()[67]["fields"]["application_forms"]
    assert forms["status"] == "needs_confirmation" and "HTTP401" in forms["value"]
    for sid in ["p67-r16-current-application", "p67-r16-pdf-online-application"]:
        source = json.loads((BUNDLE / "overseas_sources" / f"{sid}.json").read_text())
        assert source["status"] == "fetch_failed" and source["http_status"] == 401
    client = TestClient(create_app(tmp_path))
    catalog = client.get(
        "/application-center/catalog",
        params={"school": HOME, "target_school": at(67).school_name},
    ).json()
    linked = [r for r in catalog["items"] if r["official_form_verified"]]
    assert len(linked) == 2 and all(r["download_available"] for r in linked)
    assert {r["stage"] for r in linked} == {"nomination", "student_application"}
    assert all("1YAxkAQ" not in r["official_form_url"] for r in linked)


def test_public_json_parser_reads_real_response_and_rejects_internal_article(tmp_path):
    spec = importlib.util.spec_from_file_location(
        "ccu_fetcher", Path(__file__).resolve().parents[1] / "scripts/fetch_ccu_overseas_sources.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    source = json.loads(
        (BUNDLE / "overseas_sources/p67-r16-current-news-public-api.json").read_text()
    )
    body = (BUNDLE / source["bundled_file"]).read_bytes()
    assert hashlib.sha256(body).hexdigest() == source["sha256"]
    soup, metadata = module.public_hcmut_article(body, source["source_url"])
    text = soup.get_text(" ", strip=True)
    assert "Academic Year 2026/2027" in text and "15 October 2026" in text
    assert metadata["public_article_id"] == 24702
    assert any(a.get("href") == "https://ioffice.hcmut.edu.vn/url/s/vdT5yxx" for a in soup.select("a[href]"))
    internal = json.loads(body)
    internal["item"]["noiBo"] = 1
    with pytest.raises(ValueError, match="not marked public"):
        module.public_hcmut_article(json.dumps(internal).encode(), source["source_url"])
    assert module.public_hcmut_article(b"{}", "https://example.com/api/home/tt-tin-tuc/item") is None


def test_transport_and_life_references_do_not_promote_year_or_anomalous_page(tmp_path):
    rows = reviewed_profiles()
    for page in [48, 100, 106]:
        assert rows[page]["fields"]["transport"]["status"] == "needs_confirmation"
    assert rows[16]["fields"]["campus_life"]["status"] == "reference_only"
    assert rows[68]["fields"]["campus_life"]["status"] == "reference_only"
    assert rows[26]["fields"]["campus_life"]["status"] == "needs_confirmation"
    assert rows[71]["fields"]["campus_life"]["value"] is None
    anomaly = json.loads((BUNDLE / "overseas_sources/p71-r16-campus2026.json").read_text())
    assert anomaly["access_result"] == "unrelated_content_anomaly"
    for profile in rows.values():
        assert all(e["source_id"] != anomaly["source_id"] for f in profile["fields"].values() for e in f["evidence"])
    client = TestClient(create_app(tmp_path))
    guide = client.get(
        "/destination-profile", params={"home_school": HOME, "school": at(48).school_name}
    ).json()
    assert "Gongreung" in guide["transport_summary"]
    assert "2027" in guide["transport_summary"]


def test_seoultech_bank_authentication_does_not_inherit_other_document_rules(tmp_path):
    partner = at(48)
    fields = reviewed_rows()[48]["fields"]
    assert "未列銀行認證" in fields["documents"]["value"]
    assert "銀行只列USD6000一期／12000一年資金證明，未列認證" in fields["visa"]["value"]
    assert {3, 7} <= {
        page
        for key in ["documents", "visa"]
        for ev in fields[key]["evidence"]
        for page in ev["source_pages"]
    }
    client = TestClient(create_app(tmp_path))
    for endpoint, params in [
        ("/student-dashboard", {"school": HOME}),
        ("/application-workflow", {"home_school": HOME, "school": partner.school_name}),
        ("/destination-profile", {"home_school": HOME, "school": partner.school_name}),
        ("/application-center/catalog", {"school": HOME, "target_school": partner.school_name}),
    ]:
        response = client.get(endpoint, params=params)
        assert response.status_code == 200
        assert "非OECD在學／成績及銀行正本另需條件認證" not in response.text
        assert "非OECD學籍及銀行另需正本／認證" not in response.text
    catalog = client.get(
        "/application-center/catalog",
        params={"school": HOME, "target_school": partner.school_name},
    ).json()["items"]
    bank = next(r for r in catalog if r["stage"] == "second_submission" and "銀行" in r["name"])
    assert bank["stamps"] == []
    assert "USD6000" in bank["name"] and "非OECD正本" in bank["name"]
    for name in ["在學證明", "正式成績"]:
        authenticated = next(r for r in catalog if r["stage"] == "student_application" and name in r["name"])
        assert "Apostille" in authenticated["stamps"][0]
    for page in [47, 53]:
        flow = client.get(
            "/application-workflow", params={"home_school": HOME, "school": at(page).school_name}
        ).json()
        after = next(s for s in flow["steps"] if "不等錄取" in s["phase"])
        assert all(r["stage"] == "after_application" for r in after["document_requirements"])
