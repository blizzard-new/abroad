import hashlib
import importlib.util
import json
import subprocess
from collections import Counter
from pathlib import Path

import pytest
import requests
from docx import Document
from fastapi.testclient import TestClient

from exchange_info.api import create_app
from exchange_info.ccu_overseas import LABELS, reviewed_rows
from exchange_info.ccu_sources import BUNDLE, HOME
from exchange_info.ccu_student_view import fetch_ccu_partner_universities
from exchange_info.models import UniversityApplicationWorkflow
from exchange_info.storage import load_destination_profiles, read_jsonl


def at(page):
    return next(
        row for row in fetch_ccu_partner_universities() if row.source_pages[0] == page
    )


def test_every_current_or_unknown_identity_has_explicit_receiving_fields():
    reviews = reviewed_rows()
    partners = fetch_ccu_partner_universities()
    assert len(reviews) == 55
    for partner in partners:
        if partner.availability_status == "not_open":
            assert not partner.partner_exchange_details
            continue
        fields = partner.partner_exchange_details
        assert set(fields) == set(LABELS)
        assert reviews[partner.source_pages[0]]["school_name"] == partner.school_name
        for field in fields.values():
            assert field.reason
            if field.status == "missing":
                assert field.value is None
            else:
                assert field.value and field.evidence
                assert all(
                    ev.academic_year and ev.checked_at and ev.excerpt
                    for ev in field.evidence
                )
        if partner.quota_status == "not_published":
            assert (
                partner.quota is None
                and partner.availability_status == "needs_confirmation"
            )


def test_overseas_counts_do_not_claim_full_coverage_or_turn_fetches_into_current_data():
    report = json.loads((BUNDLE / "overseas-completeness.json").read_text())
    reviews = reviewed_rows()
    counts = Counter(
        f["status"] for row in reviews.values() for f in row["fields"].values()
    )
    assert report["overseas_field_status_counts"] == counts
    assert sum(counts.values()) == 55 * 17
    assert report["schools_with_all_overseas_fields_current"] == 0
    assert report["schools_with_at_least_one_current_overseas_fact"] == 29
    assert counts["verified_current"] >= 237 and counts["conflict"] >= 31
    questions = json.loads((BUNDLE / "confirmation-questions.json").read_text())
    assert len(questions) == 55 and all(row["questions"] for row in questions)
    matrix = json.loads((BUNDLE / "field-completeness-matrix.json").read_text())
    assert (
        len(matrix) == 104 and sum(bool(row["overseas_fields"]) for row in matrix) == 55
    )
    assert all(row["source_acquisition"] for row in matrix if row["overseas_fields"])
    for page in (26, 33, 68, 71, 74, 100):
        assert (
            at(page).partner_exchange_details["documents"].status != "verified_current"
        )
    # A misleading file name is not an academic-year check.
    assert (
        "2027-28"
        in reviewed_rows()[58]["fields"]["documents"]["evidence"][0]["source_url"]
    )
    assert at(58).partner_exchange_details["documents"].status == "needs_confirmation"
    assert at(43).partner_exchange_details["documents"].status == "verified_current"
    assert (
        "2026Fall"
        in at(43).partner_exchange_details["documents"].evidence[0].source_url
    )


@pytest.mark.parametrize(
    "page,field",
    [
        (24, "nomination_deadline"),
        (47, "academic_calendar"),
        (49, "academic_calendar"),
        (54, "housing"),
        (58, "costs"),
        (67, "visa"),
        (83, "application_deadline"),
        (103, "academic_calendar"),
        (104, "costs"),
        (106, "visa"),
        (108, "costs"),
        (111, "application_deadline"),
        (119, "arrival"),
    ],
)
def test_source_contradictions_are_visible_and_do_not_make_reminders(page, field):
    partner = at(page)
    detail = partner.partner_exchange_details[field]
    assert detail.status == "conflict" and detail.evidence
    workflow = next(
        row
        for row in read_jsonl(
            BUNDLE / "application_workflows.jsonl", UniversityApplicationWorkflow
        )
        if row.school_name == partner.school_name
    )
    assert workflow.steps[4].deadline_at is None
    assert not workflow.steps[4].deadline_reminder_eligible
    assert any("來源矛盾" in text for step in workflow.steps for text in step.details)


def test_hokkaido_program_evidence_and_old_documents_stay_separate():
    fields = at(37).partner_exchange_details
    assert {p for e in fields["documents"].evidence for p in e.source_pages} == {
        1,
        2,
        3,
        4,
        5,
    }
    assert "不授予學分" in fields["course_restrictions"].value
    flows = read_jsonl(
        BUNDLE / "application_workflows.jsonl", UniversityApplicationWorkflow
    )
    for page in (16, 23, 32, 42, 80, 95, 99, 105):
        partner = at(page)
        flow = next(f for f in flows if f.school_name == partner.school_name)
        assert not flow.steps[4].required_documents
    assert at(47).partner_exchange_details["arrival"].status == "explicit_not_announced"
    assert (
        at(47).partner_exchange_details["housing_deadline"].status
        == "needs_confirmation"
    )


def test_hcmut_student_form_is_readable_and_bound_to_current_link():
    source = json.loads((BUNDLE / "overseas_sources/p67-hostw1.json").read_text())
    form = BUNDLE / source["bundled_file"]
    assert hashlib.sha256(form.read_bytes()).hexdigest() == source["sha256"]
    doc = Document(form)
    text = " ".join(p.text for p in doc.paragraphs)
    assert "ACADEMIC EXCHANGE FORM" in text and "Nomination letter" in text
    assert at(67).partner_exchange_details["documents"].status == "verified_current"
    assert "學生" in at(67).partner_exchange_details["application_forms"].value


def test_changed_source_requires_semantic_recheck(tmp_path, monkeypatch):
    import exchange_info.ccu_overseas as module

    reviews = json.loads((BUNDLE / "overseas-reviewed-fields.json").read_text())
    ev = next(f["evidence"][0] for f in reviews[0]["fields"].values() if f["evidence"])
    (tmp_path / "overseas-reviewed-fields.json").write_text(json.dumps(reviews))
    directory = tmp_path / "overseas_sources"
    directory.mkdir()
    source = json.loads(
        (BUNDLE / "overseas_sources" / (ev["source_id"] + ".json")).read_text()
    )
    source["text_pages"][0] += " changed requirements"
    (directory / (ev["source_id"] + ".json")).write_text(json.dumps(source))
    monkeypatch.setattr(module, "BUNDLE", tmp_path)
    module.reviewed_rows.cache_clear()
    try:
        with pytest.raises(ValueError, match="Changed CCU overseas source"):
            module.reviewed_rows()
    finally:
        module.reviewed_rows.cache_clear()


def test_api_and_storage_deliver_life_guides_without_changing_cgu(tmp_path):
    profiles = load_destination_profiles(tmp_path, include_bundled_baseline=True)
    assert sum(p.home_university == HOME for p in profiles) == 55
    assert sum(p.home_university == "長庚大學" for p in profiles) == 77
    client = TestClient(create_app(tmp_path))
    response = client.get("/destination-profiles", params={"home_school": HOME})
    assert response.status_code == 200 and len(response.json()) == 55
    partner = at(43)
    response = client.get(
        "/destination-profile",
        params={"home_school": HOME, "school": partner.school_name},
    )
    data = response.json()
    assert response.status_code == 200 and data["home_university"] == HOME
    assert len(data["student_guide_sections"]) == 8
    assert "2026/2027" in json.dumps(data, ensure_ascii=False)
    partner = at(71)
    data = client.get(
        "/destination-profile",
        params={"home_school": HOME, "school": partner.school_name},
    ).json()
    assert "未核實" in data["housing_summary"]
    assert "官方網站未公開" not in data["housing_summary"]
    assert client.get("/static/ccu-partner-details.js").status_code == 200
    schema = client.get("/openapi.json").json()["components"]["schemas"]
    assert "PartnerExchangeDetailField" in schema
    assert "partner_exchange_details" in schema["PartnerUniversity"]["properties"]


def test_production_renderer_shows_years_conflicts_gaps_and_escapes_source_text():
    data = at(83).model_dump(mode="json")
    data["partner_exchange_details"]["costs"]["value"] += "<script>unsafe()</script>"
    script = r"""
    const assert=require('node:assert/strict'), fs=require('node:fs');
    const window={};eval(fs.readFileSync(process.argv[1],'utf8'));
    const escapeHtml=s=>String(s).replaceAll('&','&amp;').replaceAll('<','&lt;').replaceAll('>','&gt;').replaceAll('"','&quot;');
    const html=window.UniWayCcuDetails.render(JSON.parse(process.argv[2]),escapeHtml);
    assert.ok(html.includes('來源矛盾，待確認'));
    assert.ok(html.includes('2026–2027'));
    assert.ok(html.includes('2026-10-08'));
    assert.ok(html.includes('PDF第5頁'));
    assert.ok(html.includes('本期未核實／來源未載'));
    assert.ok(!html.includes('<script>unsafe'));
    assert.ok(html.includes('&lt;script&gt;unsafe'));
    assert.equal(window.UniWayCcuDetails.render({school_name:'legacy'},escapeHtml),'');
    """
    result = subprocess.run(
        [
            "node",
            "-e",
            script,
            str(Path("src/exchange_info/static/ccu-partner-details.js").resolve()),
            json.dumps(data, ensure_ascii=False),
        ],
        capture_output=True,
        check=False,
        text=True,
    )
    assert result.returncode == 0, result.stderr


def test_fetcher_records_real_failure_and_never_promotes_download_success(tmp_path):
    spec = importlib.util.spec_from_file_location(
        "ccu_public_fetch", "scripts/fetch_ccu_overseas_sources.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    class Session:
        def __init__(self, code):
            self.code = code

        def get(self, url, **kwargs):
            response = requests.Response()
            response.url = url
            response.status_code = self.code
            response._content = b"<html><main>Application form, no year</main></html>"
            response.headers["Content-Type"] = "text/html"
            return response

    item = {
        "url": "https://official.example.edu/form",
        "source_id": "candidate",
        "authority": "partner_official_public_page",
    }
    failed = module.fetch_public_source(item, tmp_path, Session(404))
    assert failed["status"] == "fetch_failed" and failed["http_status"] == 404
    assert "HTTPError" in failed["error"] and failed["checked_at"]
    fetched = module.fetch_public_source(item, tmp_path, Session(200))
    assert fetched["status"] == "html" and fetched["text_pages"]
    assert fetched["content_applicability"] == "needs_confirmation"


def test_life_renderer_keeps_ccu_reference_and_missing_fields_visible():
    script = r"""
    const assert=require('node:assert/strict'),fs=require('node:fs');
    const window={}; eval(fs.readFileSync(process.argv[1],'utf8'));
    const app=fs.readFileSync(process.argv[2],'utf8');
    const container={innerHTML:'',setAttribute:()=>{}};
    const $=selector=>selector.includes('travel-stamp-city')?null:container;
    const escapeHtml=s=>String(s||'').replaceAll('<','&lt;'),formatDate=s=>s,renderPrimaryFacts=()=>'',initIcons=()=>{};
    eval(app.match(/^function renderDestinationProfile\([^]*?^}/m)[0]);
    const item=JSON.parse(fs.readFileSync(0,'utf8'));
    renderDestinationProfile(item,{coverage_status:'needs_confirmation',coverage_note:'未核實2027版',last_checked:'2026-10-08'});
    assert.ok(container.innerHTML.includes('合作校生活資料仍待確認'));
    assert.ok(container.innerHTML.includes('其他年度／梯次參考，不能作本期申請依據'));
    assert.ok(container.innerHTML.includes('2025'));
    assert.ok(container.innerHTML.includes('本期未核實／來源未載'));
    assert.equal((container.innerHTML.match(/data-ccu-field=/g)||[]).length,8);
    """
    result = subprocess.run(
        [
            "node",
            "-e",
            script,
            str(Path("src/exchange_info/static/ccu-partner-details.js").resolve()),
            str(Path("src/exchange_info/static/app.js").resolve()),
        ],
        input=at(16).model_dump_json(),
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
