from datetime import datetime
import gzip
import json
from pathlib import Path
import subprocess
import sys

import pytest
from fastapi.testclient import TestClient

from exchange_info.api import create_app
from exchange_info import storage
from exchange_info.application_documents import all_application_templates
from exchange_info.application_rules import (
    build_personal_application_plan,
    select_application_workflow,
)
from exchange_info.models import ApplicationRuleContext, PersonalApplicationPlanRequest
from exchange_info.ncu_eligibility import ncu_academic_check
from exchange_info.ncu_student_view import (
    build_ncu_student_dashboard,
    fetch_ncu_partner_universities,
    ncu_field_audit,
)
from exchange_info.school_identity import school_identity_key
from exchange_info.university_registry import NCU, require_university

ROOT = Path(__file__).parents[1]
BUNDLE = ROOT / "src/exchange_info/official_data/ncu"


@pytest.mark.parametrize(
    "alias", ["中央", "中大", "國立中央大學", "NCU", "National Central University"]
)
def test_ncu_aliases(alias):
    assert require_university(alias) == NCU


@pytest.mark.parametrize(
    "degree,score,year,status",
    [
        ("大學部", 59.99, "大三", "fail"),
        ("大學部", 60, "大三", "pass"),
        ("研究所", 69.99, "碩一", "fail"),
        ("研究所", 70, "碩一", "pass"),
        ("在職碩士班", 70, None, "pass"),
        ("大學部", 99, "大五", "fail"),
        ("大六", 99, None, "fail"),
        ("大學部", 99, None, "needs_confirmation"),
        (None, 99, "大三", "needs_confirmation"),
        ("大學部", None, "大三", "needs_confirmation"),
    ],
)
def test_degree_grade_year_and_unknowns(degree, score, year, status):
    assert ncu_academic_check(degree, score, year)[0] == status


def test_reference_rows_never_become_current_quotas_and_tracks_stay_distinct(tmp_path):
    partners = fetch_ncu_partner_universities()
    assert (
        len(partners)
        == len({school_identity_key(p.school_name) for p in partners})
        == 214
    )
    assert all(
        p.quota is None and p.availability_status == "agreement_only" for p in partners
    )
    assert all(p.colleges is None and p.degree_levels is None for p in partners)
    hokkaido = [p for p in partners if "Hokkaido University" in p.school_name]
    assert len(hokkaido) == 2 and hokkaido[0].school_name != hokkaido[1].school_name
    nanyang = next(p for p in partners if "Nanyang Technological" in p.school_name)
    assert len(nanyang.program_options) == 2
    assert all(option.quota is None for option in nanyang.program_options)
    workflows = [
        w
        for w in storage.load_bundled_application_workflows()
        if w.home_university == NCU.school_name
    ]
    destinations = [
        d
        for d in storage.load_destination_profiles(
            tmp_path, include_bundled_baseline=True
        )
        if d.home_university == NCU.school_name
    ]
    assert len(workflows) == len(destinations) == 214
    assert all(
        w.review_status == "pending_review" and w.published_at is None
        for w in workflows
    )
    assert all(
        not step.deadline_reminder_eligible for w in workflows for step in w.steps
    )
    assert storage.load_application_workflows(tmp_path) == []


def test_home_deadlines_are_distinct_and_expire():
    before = build_ncu_student_dashboard(
        reference_time=datetime.fromisoformat("2026-10-08T12:00:00+08:00")
    )
    during = build_ncu_student_dashboard(
        reference_time=datetime.fromisoformat("2026-11-16T09:01:00+08:00")
    )
    after = build_ncu_student_dashboard(
        reference_time=datetime.fromisoformat("2026-12-12T09:00:00+08:00")
    )
    assert before.application_periods[0].status == "upcoming"
    assert during.application_periods[0].status == "open"
    assert all(
        p.status == "closed" and not p.reminder_eligible
        for p in after.application_periods
    )
    assert before.application_periods[0].deadline_at == datetime.fromisoformat(
        "2026-12-04T12:00:00+08:00"
    )
    assert before.application_periods[1].deadline_at == datetime.fromisoformat(
        "2026-12-11T17:00:00+08:00"
    )
    assert before.academic_score_minimum is None
    assert before.selection_rules.degree_score_minimums["大學部"] == 60
    assert before.selection_rules.degree_score_minimums["研究所"] == 70
    assert before.selection_rules.language_certificate_required


def test_different_year_workflow_is_not_current_and_home_host_documents_are_separate():
    workflows = storage.load_bundled_application_workflows()
    name = next(
        p.school_name
        for p in fetch_ncu_partner_universities()
        if "Manitoba" in p.school_name
    )
    current = select_application_workflow(
        workflows,
        ApplicationRuleContext(
            home_university=NCU.school_name,
            partner_university=name,
            academic_year="116",
            application_round="第一梯次",
        ),
    )
    assert current is not None
    assert (
        select_application_workflow(
            workflows,
            ApplicationRuleContext(
                home_university=NCU.school_name,
                partner_university=name,
                academic_year="115",
            ),
        )
        is None
    )
    home = current.steps[2]
    host = current.steps[4]
    assert len(home.document_requirements) == 7
    assert any("名次" in d.name for d in home.document_requirements)
    assert any("personal statement" in d.name for d in host.document_requirements)
    assert not any(
        "家長同意" in d.name or "名次" in d.name for d in host.document_requirements
    )
    assert all(
        "drive.google.com" in u
        for d in host.document_requirements
        for u in d.source_urls
    )
    assert host.deadline_at is None and not host.deadline_reminder_eligible


def test_new_document_old_price_track_scope_and_conflicts_are_visible():
    partners = fetch_ncu_partner_universities()
    strasbourg = next(p for p in partners if "Strasbourg" in p.school_name)
    assert "2025–26" in strasbourg.tuition_info and "201–550" in strasbourg.tuition_info
    assert "B1" in strasbourg.eligibility and "強烈建議" in strasbourg.eligibility
    shinshu = next(p for p in partners if "Shinshu" in p.school_name)
    assert "15,500" in shinshu.tuition_info and "5,200" in shinshu.tuition_info
    assert ncu_field_audit(shinshu.school_name)["fields"]["insurance"]["unresolved"]
    shibaura = next(p for p in partners if "shibaura" in p.school_name.casefold())
    assert "SDW" in shibaura.eligibility and "REP" in shibaura.eligibility
    assert "不接受母校B2函" in shibaura.eligibility


def test_plan_does_not_regex_reference_language_or_promote_pending_quota():
    partners = fetch_ncu_partner_universities()
    p = next(p for p in partners if "Strasbourg" in p.school_name)
    req = PersonalApplicationPlanRequest(
        home_school=NCU.school_name,
        degree_level="在職碩士班",
        academic_score=70,
        language_test="ielts",
        language_score=9,
        preferences=[{"rank": 1, "school_name": p.school_name}],
    )
    result = build_personal_application_plan(
        req,
        partners,
        storage.load_bundled_application_workflows(),
        academic_score_minimum=None,
    )
    checks = {c.code: c for c in result.choices[0].checks}
    assert result.choices[0].status == "needs_confirmation"
    assert checks["academic_score"].status == "pass"
    assert (
        checks["home_language_score"].status
        == checks["language_score"].status
        == "needs_confirmation"
    )


def test_api_reads_ncu_offline_and_exposes_page_evidence_and_life(
    monkeypatch, tmp_path
):
    def forbidden():
        raise AssertionError("NCU runtime must use its own offline catalogue")

    monkeypatch.setattr("exchange_info.api.fetch_partner_universities", forbidden)
    monkeypatch.setattr("exchange_info.api.fetch_ntpu_partner_universities", forbidden)
    client = TestClient(create_app(tmp_path))
    dashboard = client.get("/student-dashboard", params={"school": "NCU"})
    assert dashboard.status_code == 200
    assert len(dashboard.json()["partner_universities"]) == 214
    p = next(
        p
        for p in dashboard.json()["partner_universities"]
        if "Strasbourg" in p["school_name"]
    )
    params = {"home_school": "NCU", "school": p["school_name"]}
    audit = client.get("/partner-source-audit", params=params)
    assert audit.status_code == 200
    assert len(audit.json()["fields"]) == 15
    housing = audit.json()["fields"]["housing"]
    assert (
        housing["original_evidence"][0]["page"] == 2
        and "2025" in housing["original_evidence"][0]["text"]
    )
    assert audit.json()["source_evidence"]
    life = client.get("/destination-profile", params=params)
    assert life.status_code == 200 and "2025–26" in life.json()["housing_summary"]
    assert client.get("/school-data-completeness", params=params).status_code == 200
    assert (
        client.get(
            "/application-workflow", params={**params, "academic_year": "116"}
        ).status_code
        == 200
    )
    assert client.get("/documents", params={"school": "中央"}).json()
    assert client.get("/search", params={"school": "中央", "q": "70"}).json()


def test_tools_do_not_carry_cgu_forms_or_assert_official_status():
    templates = all_application_templates("NCU")
    assert len(templates) == 6
    for template in templates:
        assert not template.official_layout and not template.official_download_url
        assert not template.signatures and not template.stamps
        assert (
            "cgu.edu.tw" not in template.model_dump_json()
            and "長庚" not in template.model_dump_json()
        )
        assert "ncu.edu.tw" in template.source_url
    app = next(t for t in templates if t.id == "exchange-application-data")
    test = next(f for f in app.fields if f.id == "language_test")
    assert "IELTS Academic" in test.options and "TOEIC（聽讀）" in test.options


def test_new_host_track_year_and_document_conflicts_keep_original_evidence():
    import gzip

    records = json.loads((BUNDLE / "field-audit.json").read_text())
    turku = next(x for x in records if "University of Turku" in x["school_name"])
    assert "2027/8/15" in turku["fields"]["host_deadline"]["note"]
    assert "TOEIC" in turku["fields"]["language"]["note"]
    assert turku["fields"]["language"]["status"] == "needs_confirmation"
    ipsa = next(x for x in records if "IPSA" in x["school_name"])
    assert "Toulouse" in ipsa["fields"]["eligibility"]["note"]
    assert "recommended" in ipsa["fields"]["language"]["note"]
    sdu = next(x for x in records if "Demirel" in x["school_name"])
    assert "2008–09" in sdu["fields"]["host_documents"]["note"]
    raw = json.loads(gzip.decompress((BUNDLE / "source-evidence.json.gz").read_bytes()))
    for source in raw:
        for page in source.get("pages", []):
            assert not page["text"].startswith("PK\x03\x04")
    image = next(x for x in raw if x["id"] == "host-alku-checklist")
    assert image["pages"][0]["page"] is None
    assert "Learning Agreement" in image["pages"][0]["text"]
    word = next(x for x in raw if x["id"] == "host-alku-factsheet")
    assert word["document_format"] == "docx_no_fixed_pdf_pages"
    assert word["pages"][0]["page"] is None
    assert "\x00" not in word["pages"][0]["text"]
    for workflow in storage.load_bundled_application_workflows():
        if workflow.home_university == NCU.school_name:
            assert not any(
                any(
                    domain in s.source_url
                    for domain in ("service-public.gouv.fr", "migri.fi", "tys.fi")
                )
                for s in workflow.sources
            )


def test_new_mainland_scopes_and_tuaf_examples_cannot_become_current_requirements():
    partners = fetch_ncu_partner_universities()
    for name in ("Shanghai Jiao Tong", "Donghua", "Jiaotong-Liverpool"):
        partner = next(p for p in partners if name in p.school_name)
        audit = ncu_field_audit(partner.school_name)
        assert partner.quota is None and partner.degree_levels is None
        assert audit["fields"]["eligibility"]["status"] == "needs_confirmation"
        assert "臺灣籍" in partner.eligibility
    tuaf = next(p for p in partners if "THAI NGUYEN" in p.school_name)
    audit = ncu_field_audit(tuaf.school_name)
    assert "2026–27" in audit["fields"]["study_period"]["applicability"]
    assert "IELTS5.5" in audit["fields"]["language"]["note"]
    assert "不能拿畢業標準當exchange入學門檻" in audit["fields"]["language"]["note"]
    assert tuaf.quota is None
    assert "$70" in audit["fields"]["tuition"]["note"]
    assert audit["fields"]["host_documents"]["status"] == "needs_confirmation"
    raw = json.loads(gzip.decompress((BUNDLE / "source-evidence.json.gz").read_bytes()))
    example = next(x for x in raw if x["id"] == "host-tuaf-appform")
    assert example["source_excerpt_only"]
    assert "未複製姓名、生日、地址、證件號碼" in example["privacy_note"]
    assert "250 words" in example["pages"][0]["text"]
    assert "National identity number; Passport number" in example["pages"][0]["text"]
    handbook = next(x for x in raw if x["id"] == "host-tuaf-newhandbook")
    assert handbook["bytes"] == 207121010 and len(handbook["pages"]) == 40
    visual = next(x for x in raw if x["id"] == "host-turku-languageform")
    assert visual["visual_review"]["verified_levels"] == [
        "A1",
        "A2",
        "B1",
        "B2",
        "C1",
        "C2",
    ]
    assert visual["pages"][0]["page"] is None


@pytest.mark.parametrize("hash_matches", [True, False])
def test_filled_form_snapshot_uses_reviewed_excerpt_and_fails_closed_on_change(
    tmp_path, monkeypatch, hash_matches
):
    import hashlib
    import importlib.util
    import io
    import zipfile
    import requests

    spec = importlib.util.spec_from_file_location(
        "ncu_host_collector", ROOT / "scripts/collect_ncu_host_web.py"
    )
    collector = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(collector)
    monkeypatch.setattr(collector, "OUT", tmp_path)
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as z:
        z.writestr(
            "word/document.xml",
            '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:p><w:r><w:t>private-filled-example-value</w:t></w:r></w:p></w:document>',
        )
    response = requests.Response()
    response.status_code = 200
    response.url = "https://example.edu/form.docx"
    response._content = buffer.getvalue()
    monkeypatch.setattr(collector.requests, "get", lambda *args, **kwargs: response)
    (tmp_path / "example-public-excerpt.json").write_text(
        json.dumps(
            {
                "source_sha256": hashlib.sha256(response.content).hexdigest()
                if hash_matches
                else "changed",
                "public_field_excerpt": "Applicant signature; date",
                "note_zh": "只摘錄必要欄位，不複製個資",
            }
        )
    )
    result = collector.fetch(
        {
            "id": "example",
            "title": "Filled example",
            "url": response.url,
            "requires_public_field_excerpt": True,
        }
    )
    assert "private-filled-example-value" not in json.dumps(result)
    if hash_matches:
        assert result["source_excerpt_only"] and result["pages"][0]["page"] is None
    else:
        assert result["pages"] == [] and "原件已變更" in result["error"]


def test_unverified_ncu_costs_cannot_pass_a_current_budget():
    from exchange_info.cost_estimates import budget_fit, extract_monthly_estimates
    from exchange_info.models import DestinationProfile

    profile = DestinationProfile(
        home_university=NCU.school_name,
        school_name="來源年不同",
        coverage_status="official_partial",
        cost_summary="AY2026–27生活費EUR600–1000／月",
    )
    estimates = extract_monthly_estimates(profile)
    assert estimates and all(x.outdated for x in estimates)
    assert budget_fit(estimates, 100000)["status"] == "unknown"


def test_bundle_rebuilds_exactly_from_tracked_source_data(tmp_path):
    subprocess.run(
        [sys.executable, "scripts/build_ncu_catalog.py", "--output-dir", str(tmp_path)],
        cwd=ROOT,
        check=True,
        capture_output=True,
        timeout=40,
    )
    for item in BUNDLE.iterdir():
        if item.is_file():
            assert (tmp_path / item.name).read_bytes() == item.read_bytes(), item.name
    audit = json.loads((tmp_path / "field-audit.json").read_text())
    assert len(audit) == 214 and all(len(x["fields"]) == 15 for x in audit)
    sources = json.loads(
        gzip.decompress((tmp_path / "source-evidence.json.gz").read_bytes())
    )
    drive = [x for x in sources if not x["id"].startswith(("host-", "home-"))]
    assert len(drive) == 459 and not any(x.get("error") for x in drive)


@pytest.mark.parametrize(
    "test,date,error",
    [
        ("IELTS Academic", "2100-01-01", True),
        ("TOEIC（聽讀）", "2000-01-01", True),
        ("志願校接受之第三外語檢定", "2000-01-01", False),
        ("Duolingo", "2026-06-01", True),
        ("IELTS Academic", "2026-06-01", False),
    ],
)
def test_ncu_packet_rejects_future_expired_or_other_school_proof(test, date, error):
    from exchange_info.application_documents import build_packet_manifest
    from exchange_info.models import ApplicationPacketRequest

    request = ApplicationPacketRequest.model_validate(
        {
            "context": {"school_name": "國立中央大學"},
            "answers": {
                "exchange-application-data": {
                    "language_test": test,
                    "language_result_date": date,
                    "language_score": "B2",
                }
            },
            "selections": [{"template_id": "exchange-application-data"}],
        }
    )
    item = build_packet_manifest(request).items[0]
    assert (
        any(
            f.validation_error
            for f in item.preview_fields
            if f.field_id in {"language_test", "language_result_date"}
        )
        is error
    )
    assert all(
        f.required
        for f in item.preview_fields
        if f.field_id in {"language_test", "language_score", "language_result_date"}
    )
