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
    assert len(audit.json()["fields"]) == 17
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


def test_record_year_and_track_limits_override_empty_field_gaps_and_scores():
    from exchange_info.school_completeness import build_school_completeness

    records = json.loads((BUNDLE / "field-audit.json").read_text())
    for record in records:
        verified = {
            key
            for key, field in record["fields"].items()
            if field["status"] == "available"
        }
        assert verified == {"home_documents", "home_deadline"}
        assert {"city", "transport"} <= record["fields"].keys()
    for name, field_key in (("Pukyong", "courses"), ("Strasbourg", "arrival")):
        partner = next(
            p for p in fetch_ncu_partner_universities() if name in p.school_name
        )
        audit = ncu_field_audit(partner.school_name)
        field = audit["fields"][field_key]
        assert field["status"] == "needs_confirmation"
        assert field["current_applicability_status"] == "unconfirmed"
        assert field["reference_status"] == "reviewed_partial_reference"
        result = build_school_completeness(
            partner, None, None, home_university=NCU.school_name
        )
        assert result.available_count == 2 and result.total_count == 17
        assert result.score == round(2 / 17, 3)


@pytest.mark.parametrize(
    "texts,any_text,all_text",
    [
        (["", ""], False, False),
        (["body", ""], True, False),
        (["body", "body"], True, True),
    ],
)
def test_downloaded_pdf_pages_are_not_text_or_human_reading(texts, any_text, all_text):
    from exchange_info.ncu_source_coverage import source_content_status

    document = {
        "status": 200,
        "sha256": "original",
        "pages": [{"page": i + 1, "text": text} for i, text in enumerate(texts)],
    }
    result = source_content_status(document)
    assert result["downloaded"] and result["any_text"] == any_text
    assert result["all_pages_have_text"] == all_text
    assert not result["all_pages_read"] and not result["visual_reviewed"]
    document["visual_review"] = {
        "source_sha256": "changed",
        "pdf_pages_reviewed": [1, 2],
    }
    assert not source_content_status(document)["visual_reviewed"]
    document["visual_review"]["source_sha256"] = "original"
    verified = source_content_status(document)
    assert verified["all_pages_read"] and verified["visual_reviewed_page_count"] == 2
    assert verified["any_text"] == any_text


def test_catalog_content_metrics_exclude_all_image_documents_and_never_claim_full_reading():
    metrics = json.loads((BUNDLE / "catalog-completeness.json").read_text())
    assert metrics["source_documents_downloaded"] == 459
    assert metrics["source_documents_any_text"] == 454
    assert metrics["source_documents_all_pages_have_text"] == 423
    raw = json.loads(gzip.decompress((BUNDLE / "source-evidence.json.gz").read_bytes()))
    drive_ids = {d["id"] for d in json.loads(gzip.decompress(
        (ROOT / "sources/ncu/2026-10-08/drive-evidence.json.gz").read_bytes()
    ))}
    drive = [d for d in raw if d["id"] in drive_ids]
    images = [d for d in drive if not d["content_status"]["any_text"]]
    assert len(images) == 5 and sum(len(d["pages"]) for d in images) == 33
    uos = next(d for d in drive if d["id"] == "1YTU2HTNgu80it9DHNHy-2OVZSFu7tEqd")
    assert len(uos["pages"]) == 11 and not uos["content_status"]["any_text"]


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
    assert len(audit) == 214 and all(len(x["fields"]) == 17 for x in audit)
    sources = json.loads(
        gzip.decompress((tmp_path / "source-evidence.json.gz").read_bytes())
    )
    drive_ids = {d["id"] for d in json.loads(gzip.decompress(
        (ROOT / "sources/ncu/2026-10-08/drive-evidence.json.gz").read_bytes()
    ))}
    drive = [x for x in sources if x["id"] in drive_ids]
    assert len(drive) == 459 and not any(x.get("error") for x in drive)


def test_visual_review_preserves_native_empty_pages_and_expires_with_sha():
    from exchange_info.ncu_source_coverage import attach_visual_review, source_content_status

    raw = json.loads(gzip.decompress((BUNDLE / "source-evidence.json.gz").read_bytes()))
    old = next(d for d in raw if d["id"] == "1YTU2HTNgu80it9DHNHy-2OVZSFu7tEqd")
    assert all(not p["text"] for p in old["pages"])
    assert old["content_status"]["all_pages_read"]
    assert old["content_status"]["visual_reviewed_page_count"] == 11
    assert old["content_status"]["ocr_status"] == "performed_selected_passages_verified"
    assert "2023" in old["page_transcriptions"][2]["text"]
    old["sha256"] = "changed-original"
    attach_visual_review(old, old["visual_review"])
    assert not old.get("page_transcriptions") and not old.get("visual_review")
    assert source_content_status(old)["ocr_status"] == "not_performed"
    assert not source_content_status(old)["all_pages_read"]


def test_tuaf_visual_sidecar_reaches_offline_audit_and_rejects_changed_sha():
    from exchange_info.ncu_source_coverage import attach_visual_review, source_content_status

    raw = json.loads(gzip.decompress((BUNDLE / "source-evidence.json.gz").read_bytes()))
    source = next(d for d in raw if d["id"] == "host-tuaf-2026")
    sidecar = json.loads((ROOT / "sources/ncu/2026-10-08/host-tuaf-2026-visual-review.json").read_text())
    assert source["visual_review"] == sidecar
    assert sidecar["pdf_page"] == 2 and source["content_status"]["page_count"] == 2
    assert source["content_status"]["visual_reviewed_page_count"] == 1
    assert source["content_status"]["visual_reviewed"]
    partner = next(p for p in fetch_ncu_partner_universities() if "太原農林" in p.school_name)
    audit = ncu_field_audit(partner.school_name)
    row = next(s for s in audit["read_sources"] if s["id"] == "host-tuaf-2026")
    assert row["content_status"]["visual_reviewed_page_count"] == 1
    source["sha256"] = "different-original"
    attach_visual_review(source, sidecar)
    assert not source_content_status(source)["visual_reviewed"]
    assert not source.get("visual_review")
    source["sha256"] = sidecar["source_sha256"]
    attach_visual_review(source, {**sidecar, "pdf_page": 99})
    assert not source_content_status(source)["visual_reviewed"]


def test_uos_current_calendar_conflicts_and_post_admission_files_stay_scoped(tmp_path):
    partner = next(p for p in fetch_ncu_partner_universities() if "University of Seoul" in p.school_name)
    audit = ncu_field_audit(partner.school_name)
    assert "2027/3/1–4/15" in partner.application_deadline
    assert "Spring2028" in audit["fields"]["host_deadline"]["unresolved"]
    assert "preferred" in audit["fields"]["eligibility"]["note"]
    assert "TOPIK4" in audit["fields"]["language"]["note"]
    assert "不是全校" in audit["fields"]["language"]["note"]
    workflow = next(w for w in storage.load_bundled_application_workflows() if w.home_university == NCU.school_name and w.school_name == partner.school_name)
    assert len(workflow.steps[2].document_requirements) == 7
    assert not any("MMR" in d.name for d in workflow.steps[4].document_requirements)
    post = next(s for s in workflow.steps if s.rule_id.endswith("host-predeparture-documents"))
    assert post.phase == "行前準備" and post.needs_confirmation
    assert len(post.document_requirements) == 2
    assert any("MMR" in d.name for d in post.document_requirements)
    assert any(d.official_form_url and "d373b899" in d.official_form_url for d in post.document_requirements)
    assert len({s.order for s in workflow.steps}) == len(workflow.steps)
    assert not any(s.deadline_reminder_eligible for s in workflow.steps)
    destination = next(d for d in storage.load_destination_profiles(tmp_path, include_bundled_baseline=True) if d.home_university == NCU.school_name and d.school_name == partner.school_name)
    assert destination.city == "首爾" and "6002" in destination.transport_summary
    assert any(s.key == "transport" for s in destination.student_guide_sections)


def test_hust_taiwan_track_historical_dates_and_conditional_health_do_not_mix():
    partner = next(p for p in fetch_ncu_partner_universities() if "Huazhong University" in p.school_name)
    audit = ncu_field_audit(partner.school_name)
    assert "2027/5/5" in partner.application_deadline
    assert "不能推定2027" in audit["fields"]["eligibility"]["note"]
    assert "舊年度" in audit["fields"]["study_period"]["applicability"]
    assert "不套" in audit["fields"]["insurance"]["note"]
    workflow = next(w for w in storage.load_bundled_application_workflows() if w.home_university == NCU.school_name and w.school_name == partner.school_name)
    assert not any("健康" in d.name for d in workflow.steps[4].document_requirements)
    post = next(s for s in workflow.steps if s.rule_id.endswith("host-predeparture-documents"))
    assert post.document_requirements[0].name.startswith("錄取後才繳")
    assert not any("hkbu.edu.hk" in s.source_url for s in workflow.sources)
    legacy = next(p for p in fetch_ncu_partner_universities() if "International University, Viet Nam" in p.school_name)
    report = ncu_field_audit(legacy.school_name)
    assert "2018" in report["fields"]["host_documents"]["applicability"]
    raw = json.loads(gzip.decompress((BUNDLE / "source-evidence.json.gz").read_bytes()))
    assert "完整當期" in next(d for d in raw if d["id"] == "host-hcm-iex-2018-browser")["excerpt_note_zh"]


def test_shanghai_visual_versions_and_taiwan_track_do_not_become_current():
    raw = json.loads(gzip.decompress((BUNDLE / "source-evidence.json.gz").read_bytes()))
    sufe_source = next(d for d in raw if d["id"] == "1JSkQxNHeCgPkLeFtT5BtTbLXU_dfv1fN")
    shu_source = next(d for d in raw if d["id"] == "1p6fLyiZOpX7RjEyF_QW6UBPp2-PFV99e")
    for source in (sufe_source, shu_source):
        assert source["content_status"]["all_pages_read"]
        assert source["content_status"]["visual_reviewed_page_count"] == 8
    assert "2026--2027" in sufe_source["page_transcriptions"][0]["text"]
    assert "2025--2026" in sufe_source["page_transcriptions"][-1]["text"]
    assert not shu_source["pages"][7]["text"].strip()
    assert "2020" in shu_source["page_transcriptions"][-1]["text"]
    partners = fetch_ncu_partner_universities()
    sufe = next(p for p in partners if p.school_name.startswith("上海財經大學 "))
    shu = next(p for p in partners if p.school_name.endswith("Shanghai University"))
    assert "不是中央116" in ncu_field_audit(sufe.school_name)["fields"]["study_period"]["note"]
    assert "下限" in ncu_field_audit(sufe.school_name)["fields"]["courses"]["note"]
    workflows = storage.load_bundled_application_workflows()
    sw = next(w for w in workflows if w.home_university == NCU.school_name and w.school_name == sufe.school_name)
    assert len(sw.steps[4].document_requirements) == 4
    assert not any(s.deadline_at and s.rule_id.endswith("host-application") for s in sw.steps)
    assert not next(w for w in workflows if w.home_university == NCU.school_name and w.school_name == shu.school_name).steps[4].document_requirements


def test_uny_degree_and_dual_degree_are_not_exchange_and_government_form_is_scoped():
    partners = fetch_ncu_partner_universities()
    uny = next(p for p in partners if "Universitas Negeri Yogyakarta" in p.school_name)
    audit = ncu_field_audit(uny.school_name)
    assert "2021" in audit["fields"]["host_deadline"]["note"]
    assert "雙聯不是" in audit["fields"]["eligibility"]["note"]
    assert "USD4000" in audit["fields"]["host_documents"]["note"]
    assert "不能套" in audit["fields"]["eligibility"]["note"]
    workflow = next(w for w in storage.load_bundled_application_workflows() if w.home_university == NCU.school_name and w.school_name == uny.school_name)
    assert not workflow.steps[4].document_requirements
    assert all(not s.deadline_reminder_eligible for s in workflow.steps)
    sources = json.loads(gzip.decompress((BUNDLE / "source-evidence.json.gz").read_bytes()))
    form = next(d for d in sources if d["id"] == "gov-kr-taipei-visa-form")
    assert form["authority_kind"] == "government"
    assert form["content_status"]["page_count"] == 5
    assert form["content_status"]["all_pages_read"]
    assert not form["content_status"]["visual_reviewed"]
    assert "SIGNATURE OF APPLICANT" in form["pages"][4]["text"]
    uos = next(p for p in partners if "University of Seoul" in p.school_name)
    assert "親筆簽名" in ncu_field_audit(uos.school_name)["fields"]["visa"]["note"]
    host = next(w for w in storage.load_bundled_application_workflows() if w.home_university == NCU.school_name and w.school_name == uos.school_name)
    assert not any("VISA APPLICATION" in d.name for d in host.steps[4].document_requirements)


def test_uos_known_broken_layers_stay_in_audit_and_out_of_rag(tmp_path, monkeypatch):
    from copy import deepcopy
    from exchange_info.models import ProcessedPage
    from exchange_info.ncu_source_coverage import indexable_source_text
    from exchange_info.rag import build_document_chunks, build_rag_index, search_document_chunks

    raw = json.loads(gzip.decompress((BUNDLE / "source-evidence.json.gz").read_bytes()))
    source = next(d for d in raw if d["id"] == "host-uos-partner-current")
    broken = "".join(source["pages"][6]["text"].split())
    assert "6,000KRW/semester+100,000KRWdeposit=7000KRW" in broken
    assert "33000KRW" in broken
    indexed = next(ProcessedPage.model_validate_json(line) for line in (BUNDLE / "pages.jsonl").read_text().splitlines() if json.loads(line)["source_url"] == source["url"])
    assert indexed.text == indexable_source_text(source)
    compact = "".join(indexed.text.split())
    assert "6,000KRW/semester+100,000KRWdeposit=7000KRW" not in compact
    assert "33000KRW" not in compact
    assert "764,000KRW/semester" in compact and "382,000KRW" in compact
    chunks = build_document_chunks([indexed])
    housing = next(c for c in chunks if "764,000" in c.text and "382,000" in c.text)
    assert "2025房價參考" in housing.text and "2027–2028價格未核實" in housing.text
    monkeypatch.setattr("exchange_info.rag.ai_enabled", lambda: False)
    build_rag_index([indexed], tmp_path, use_embeddings=False, sync_supabase=False)
    hits = search_document_chunks("Residence Hall 764,000 382,000 KRW 住宿", tmp_path, limit=8)
    assert hits and any("764,000" in hit.chunk.text for hit in hits)
    assert all("33000KRW" not in "".join(hit.chunk.text.split()) for hit in hits)
    stale = deepcopy(source)
    stale["sha256"] = "changed-original"
    changed = indexable_source_text(stale)
    page7 = changed.split("【第7頁】", 1)[1].split("【第8頁】", 1)[0]
    assert "已隔離" in page7 and "764,000" not in page7 and "33000" not in page7
    wrong_page = deepcopy(source)
    wrong_page["visual_review"]["pdf_pages_reviewed"] = [1]
    page7 = indexable_source_text(wrong_page).split("【第7頁】", 1)[1].split("【第8頁】", 1)[0]
    assert "已隔離" in page7 and "764,000" not in page7


def test_undip_2027_partial_dates_degree_conflict_and_government_sources_stay_scoped():
    partners = fetch_ncu_partner_universities()
    undip = next(p for p in partners if "Universitas Diponegoro" in p.school_name)
    audit = ncu_field_audit(undip.school_name)
    assert "to be announce" in audit["fields"]["host_deadline"]["note"]
    assert "不能套用" in audit["fields"]["host_deadline"]["note"]
    assert "硬封研究生" in audit["fields"]["eligibility"]["note"]
    assert "IDR2.5000.000" in audit["fields"]["cost"]["note"]
    assert "不能抵扣預算" in audit["fields"]["cost"]["note"]
    workflows = storage.load_bundled_application_workflows()
    workflow = next(w for w in workflows if w.home_university == NCU.school_name and w.school_name == undip.school_name)
    assert len(workflow.steps[4].document_requirements) == 10
    visa = [d for d in workflow.steps[4].document_requirements if d.name.startswith("Visa類附件")]
    assert len(visa) == 5 and any("財力" in d.name for d in visa)
    assert all(d.needs_confirmation for d in visa)
    assert not any(s.rule_id.endswith("host-predeparture-documents") for s in workflow.steps)
    assert all(not s.deadline_reminder_eligible for s in workflow.steps)
    hust = next(w for w in workflows if w.home_university == NCU.school_name and "Huazhong University" in w.school_name)
    study = next(d for d in hust.steps[4].document_requirements if "學習計畫" in d.name)
    assert "3–6" in study.name and any(url.endswith("#page=7") for url in study.source_urls)
    assert "1YJlEpEjBgZVRrzPDVAxvIH7V6-Vm5GIV" in study.source_urls[0]
    raw = json.loads(gzip.decompress((BUNDLE / "source-evidence.json.gz").read_bytes()))
    booklet = next(d for d in raw if d["id"] == "host-undip-booklet")
    assert booklet["content_status"]["all_pages_read"]
    assert not booklet["content_status"]["all_pages_have_text"]
    assert booklet["content_status"]["visual_reviewed_page_count"] == 4
    courses = next(d for d in raw if d["id"] == "host-undip-courses-spring")
    assert len(courses["pages"]) == 146 and not courses["content_status"]["all_pages_read"]
    metrics = json.loads((BUNDLE / "catalog-completeness.json").read_text())
    rows = json.loads((BUNDLE / "field-audit.json").read_text())
    host_rows = [row for row in rows if any(s["authority_kind"] == "partner_university" for s in row["read_sources"])]
    assert metrics["host_source_mapped_entries"] == len(host_rows)
    assert metrics["source_mapped_entries"] > metrics["host_source_mapped_entries"]
    for row in rows:
        if set(row["source_rows"]) & {"ncu-206", "ncu-211"}:
            assert any(s["authority_kind"] == "government" for s in row["read_sources"])
            assert any(s["authority_kind"] == "partner_university" for s in row["read_sources"])
    assert all(d["authority_kind"] == "government" for d in raw if d["id"].startswith("gov-indonesia-"))


def test_tju_insurance_is_an_arrival_file_and_hong_kong_dates_do_not_activate_taiwan():
    workflows = storage.load_bundled_application_workflows()
    workflow = next(w for w in workflows if w.home_university == NCU.school_name and "Tianjin University" in w.school_name)
    host = next(s for s in workflow.steps if s.rule_id.endswith("host-apply"))
    arrival = next(s for s in workflow.steps if s.rule_id.endswith("host-arrival-documents"))
    assert len(host.document_requirements) == 7
    assert not any("保險" in d.name for d in host.document_requirements)
    assert arrival.phase == "抵達後" and arrival.order > host.order
    assert len(arrival.document_requirements) == 1
    assert "報到後" in arrival.document_requirements[0].name
    assert arrival.document_requirements[0].needs_confirmation
    assert [s.order for s in workflow.steps] == sorted({s.order for s in workflow.steps})
    assert all(not s.deadline_reminder_eligible for s in workflow.steps)
    audit = ncu_field_audit(workflow.school_name)
    assert "港澳" in audit["fields"]["host_deadline"]["note"]
    assert "2025" in audit["fields"]["host_documents"]["note"]
    assert all(audit["fields"][k]["status"] == "needs_confirmation" for k in ("eligibility", "host_documents", "host_deadline", "insurance"))


def test_dut_xjtu_forms_keep_track_signature_and_strict_gpa_scope():
    workflows = storage.load_bundled_application_workflows()
    dut = next(w for w in workflows if w.home_university == NCU.school_name and "Dalian University of Technology" in w.school_name)
    dut_host = next(s for s in dut.steps if s.rule_id.endswith("host-apply"))
    assert len(dut_host.document_requirements) == 7
    recommendations = [d for d in dut_host.document_requirements if "推薦信" in d.name]
    assert len(recommendations) == 1 and "不套國際版兩封" in recommendations[0].name
    assert "母校聯絡老師簽名" in dut_host.document_requirements[0].signatures
    audit = ncu_field_audit(dut.school_name)
    assert "2022" in audit["fields"]["language"]["note"]
    assert "400–600" in audit["fields"]["housing"]["note"]
    xjtu = next(w for w in workflows if w.home_university == NCU.school_name and "Xian Jiaotong University" in w.school_name)
    xjtu_host = next(s for s in xjtu.steps if s.rule_id.endswith("host-apply"))
    assert len(xjtu_host.document_requirements) == 5
    nomination = next(s for s in xjtu.steps if s.rule_id.endswith("host-nomination-documents"))
    assert nomination.responsible_party == "母校國際事務處" and nomination.phase == "甄選與提名"
    assert len(nomination.document_requirements) == 1
    assert "學生不用自行代填" in nomination.document_requirements[0].name
    assert "母校派出交換承辦老師手寫簽名" in xjtu_host.document_requirements[0].signatures
    audit = ncu_field_audit(xjtu.school_name)
    assert "GPA>2.8" in audit["fields"]["eligibility"]["note"]
    assert "不能改≥2.8" in audit["fields"]["eligibility"]["note"]
    assert "不得少于9学分或少于4门课程" in audit["fields"]["courses"]["note"]
    assert xjtu.review_status == "pending_review" and xjtu.published_at is None


def test_itera_domestic_housing_and_hcmus_blank_form_do_not_become_exchange_requirements():
    workflows = storage.load_bundled_application_workflows()
    itera = next(w for w in workflows if w.home_university == NCU.school_name and "Institut Teknologi Sumatera" in w.school_name)
    assert not next(s for s in itera.steps if s.rule_id.endswith("host-apply")).document_requirements
    audit = ncu_field_audit(itera.school_name)
    assert "200.000" in audit["fields"]["housing"]["note"]
    assert "2000.000" in audit["fields"]["housing"]["note"]
    assert "2021" in audit["fields"]["housing"]["note"]
    assert "DIM" in audit["fields"]["host_documents"]["note"]
    hcmus = next(w for w in workflows if w.home_university == NCU.school_name and "(HCMUS)" in w.school_name)
    host = next(s for s in hcmus.steps if s.rule_id.endswith("host-apply"))
    assert len(host.document_requirements) == 1
    assert "手寫簽名" in host.document_requirements[0].name
    assert "未列緊急聯絡" in ncu_field_audit(hcmus.school_name)["fields"]["host_documents"]["note"]
    evidence = ncu_field_audit(hcmus.school_name)["fields"]["host_documents"]["original_evidence"]
    assert {e["page"] for e in evidence} == {1, 2}


def test_reviewed_old_word_conversion_retains_original_sha_and_has_no_fixed_pdf_pages():
    raw = json.loads(gzip.decompress((BUNDLE / "source-evidence.json.gz").read_bytes()))
    for source_id in ("host-tju-application-2025", "host-xjtu-application-2025"):
        source = next(d for d in raw if d["id"] == source_id)
        assert source["conversion_review"]["source_sha256"] == source["sha256"]
        assert source["conversion_review"]["converted_sha256"]
        assert source["extraction_attempts"][0]["status"] == "failed"
        assert source["document_format"] == "doc_converted_docx_no_fixed_pdf_pages"
        assert all(p["page"] is None and "\x00" not in p["text"] for p in source["pages"])
        assert source["content_status"]["all_pages_read"]
        assert not source["content_status"]["visual_reviewed"]


def test_chd_old_pickup_conflict_and_three_document_stages_remain_visible():
    workflow = next(w for w in storage.load_bundled_application_workflows() if w.home_university == NCU.school_name and "Changan University" in w.school_name)
    initial = next(s for s in workflow.steps if s.rule_id.endswith("host-apply"))
    predeparture = next(s for s in workflow.steps if s.rule_id.endswith("host-predeparture-documents"))
    arrival = next(s for s in workflow.steps if s.rule_id.endswith("host-arrival-documents"))
    assert len(initial.document_requirements) == 6
    assert any("保險" in d.name for d in initial.document_requirements)
    assert initial.document_requirements[0].signatures == ["母校兩岸事務處負責人簽名、日期"]
    assert "母校單位公章" in initial.document_requirements[0].stamps
    assert not any("接機" in d.name for d in initial.document_requirements)
    assert "2020／2023" in predeparture.document_requirements[0].name
    assert arrival.phase == "抵達後" and "紙本" in arrival.document_requirements[0].name
    assert initial.order < predeparture.order < arrival.order
    audit = ncu_field_audit(workflow.school_name)
    assert "2020/8/20" in audit["fields"]["transport"]["note"]
    assert "2023/8/28" in audit["fields"]["transport"]["note"]
    assert all(not s.deadline_reminder_eligible for s in workflow.steps)


def test_nefu_foreigner_and_whu_hong_kong_macau_do_not_become_taiwan_host_files():
    workflows = storage.load_bundled_application_workflows()
    for name in ("NORTHEAST FORESTRY UNIVERSITY", "Wuhan University"):
        workflow = next(w for w in workflows if w.home_university == NCU.school_name and name in w.school_name)
        assert not next(s for s in workflow.steps if s.rule_id.endswith("host-apply")).document_requirements
        audit = ncu_field_audit(workflow.school_name)
        assert audit["fields"]["host_documents"]["status"] == "needs_confirmation"
        assert "116" in audit["fields"]["host_documents"]["note"]
    raw = json.loads(gzip.decompress((BUNDLE / "source-evidence.json.gz").read_bytes()))
    for i in ("host-nefu-health-form", "host-nefu-application-form"):
        source = next(s for s in raw if s["id"] == i)
        assert source["status"] == 200 and source["error"]
        assert not source["pages"] and not source["content_status"]["all_pages_read"]
        assert source["content_status"]["response_bytes_received"]
        assert not source["content_status"]["downloaded"]
    nomination = next(s for s in raw if s["id"] == "host-chd-nomination-2023")
    assert len(nomination["pages"]) == 2 and nomination["pages"][1]["text"] == ""
    assert nomination["content_status"]["all_pages_read"]
    assert not nomination["content_status"]["all_pages_have_text"]


@pytest.mark.parametrize("name", ["Zhengzhou University", "Guizhou University", "University of Jinan"])
def test_new_mainland_sources_do_not_fill_current_taiwan_exchange_documents(name):
    partner = next(p for p in fetch_ncu_partner_universities() if name in p.school_name)
    audit = ncu_field_audit(partner.school_name)
    assert all(audit["fields"][k]["status"] == "needs_confirmation" for k in ("eligibility", "host_documents", "host_deadline", "housing", "visa"))
    workflow = next(w for w in storage.load_bundled_application_workflows() if w.home_university == NCU.school_name and w.school_name == partner.school_name)
    assert not next(s for s in workflow.steps if s.rule_id.endswith("host-apply")).document_requirements
    assert workflow.review_status == "pending_review" and workflow.published_at is None
    assert not any(s.deadline_reminder_eligible for s in workflow.steps)


def test_nuist_language_versions_and_ujn_hong_kong_scope_stay_distinct():
    partners = fetch_ncu_partner_universities()
    nuist = next(p for p in partners if "Nanjing University of Information" in p.school_name)
    audit = ncu_field_audit(nuist.school_name)
    assert "2500–3000" in audit["fields"]["housing"]["note"]
    assert "2000–2500" in audit["fields"]["housing"]["note"]
    assert "僅限" in audit["fields"]["housing"]["note"] and "部分保留" in audit["fields"]["housing"]["note"]
    assert "報到圖" in audit["fields"]["arrival"]["unresolved"]
    ujn = next(p for p in partners if "University of Jinan" in p.school_name)
    audit = ncu_field_audit(ujn.school_name)
    assert "2024" in audit["fields"]["host_deadline"]["note"] and "2026" in audit["fields"]["host_deadline"]["note"]
    assert "香港版" in audit["fields"]["housing"]["note"]
    assert "不能住國際生宿舍" in audit["fields"]["housing"]["note"]
    assert "廣州暨南" in audit["fields"]["city"]["note"]
    assert "抵達後" in audit["fields"]["insurance"]["note"]
    raw = json.loads(gzip.decompress((BUNDLE / "source-evidence.json.gz").read_bytes()))
    dormitory = next(s for s in raw if s["id"] == "host-ujn-dormitory")
    assert not dormitory["content_status"]["all_pages_read"]
    attachment = next(s for s in raw if s["id"] == "host-ujn-registration-pdf")
    assert attachment["status"] == 200 and attachment["error"] and not attachment["pages"]
    assert attachment["content_status"]["response_bytes_received"]
    assert not attachment["content_status"]["downloaded"]
    assert attachment["url"] in audit["fields"]["host_documents"]["source_urls"]
    assert any(s["id"] == attachment["id"] and s["reason"] for s in audit["unretrieved_sources"])
    assert all(e["source_url"] != attachment["url"] for e in audit["fields"]["host_documents"]["original_evidence"])


def test_zzu_offer_dates_are_not_deadlines_and_selected_pdf_is_not_fully_read():
    partner = next(p for p in fetch_ncu_partner_universities() if "Zhengzhou University" in p.school_name)
    audit = ncu_field_audit(partner.school_name)
    assert "不是學生申請截止" in audit["fields"]["host_deadline"]["note"]
    assert "2026/7" in audit["fields"]["cost"]["note"]
    raw = json.loads(gzip.decompress((BUNDLE / "source-evidence.json.gz").read_bytes()))
    source = next(s for s in raw if s["id"] == "host-zzu-taiwan-reference")
    assert len(source["pages"]) == 51 and source["authority_kind"] == "home_university"
    assert source["content_status"]["any_text"] and not source["content_status"]["all_pages_read"]
    assert source["content_status"]["visual_reviewed_page_count"] == 1
    assert source["visual_review"]["pdf_pages_reviewed"] == [6]


def test_gzu_old_visa_text_remains_in_audit_but_is_quarantined_from_rag():
    from exchange_info.models import ProcessedPage
    from exchange_info.ncu_source_coverage import indexable_source_text
    from exchange_info.rag import build_document_chunks

    raw = json.loads(gzip.decompress((BUNDLE / "source-evidence.json.gz").read_bytes()))
    source = next(s for s in raw if s["id"] == "host-gzu-international-application")
    assert "tourist visa" in source["pages"][0]["text"]
    assert source["content_status"]["all_pages_read"]
    indexed = next(ProcessedPage.model_validate_json(line) for line in (BUNDLE / "pages.jsonl").read_text().splitlines() if json.loads(line)["source_url"] == source["url"])
    assert indexed.text == indexable_source_text(source)
    assert "tourist visa" not in indexed.text and "已隔離" in indexed.text
    assert "過時" in indexed.text and "破損文字層" not in indexed.text
    assert all("tourist visa" not in c.text for c in build_document_chunks([indexed]))
    stale = json.loads(json.dumps(source))
    stale["sha256"] = "0" * 64
    assert "tourist visa" not in indexable_source_text(stale)


def test_actual_ncu_document_catalog_keeps_initial_and_arrival_phases_pending(tmp_path):
    client = TestClient(create_app(tmp_path))
    partner = next(p for p in client.get("/student-dashboard", params={"school": "NCU"}).json()["partner_universities"] if "Tianjin University" in p["school_name"])
    response = client.get("/application-center/catalog", params={"school": "NCU", "target_school": partner["school_name"], "academic_year": "116"})
    assert response.status_code == 200
    catalog = response.json()
    assert catalog["workflow_found"] and catalog["workflow_review_status"] == "pending_review"
    assert len([d for d in catalog["items"] if d["phase"] == "合作校申請"]) == 7
    insurance = next(d for d in catalog["items"] if "2027春臺灣參考：保險" in d["name"])
    assert insurance["phase"] == "抵達後" and insurance["needs_confirmation"]
    assert all(d["needs_confirmation"] and not d["download_available"] for d in catalog["items"])
    assert "cgu.edu.tw" not in response.text


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


def test_nju_second_batch_precedes_invitation_and_keeps_conflicting_sources():
    workflow = next(w for w in storage.load_bundled_application_workflows() if w.home_university == NCU.school_name and "Nanjing University" in w.school_name and "Information" not in w.school_name)
    initial = next(s for s in workflow.steps if s.rule_id.endswith("host-apply"))
    followup = next(s for s in workflow.steps if s.rule_id.endswith("host-followup-documents"))
    assert len(initial.document_requirements) == 7
    assert not any("體檢" in d.name or "保險" in d.name for d in initial.document_requirements)
    assert len(followup.document_requirements) == 3 and followup.phase == "合作校申請"
    assert initial.order < followup.order < next(s.order for s in workflow.steps if s.phase == "行前準備")
    assert [s.order for s in workflow.steps] == sorted({s.order for s in workflow.steps})
    assert not any("第二批" in d.name for s in workflow.steps if s.phase == "抵達後" for d in s.document_requirements)
    health = next(d for d in followup.document_requirements if "體檢" in d.name)
    assert health.official_form_url and "胸透" in health.name
    assert "貼照醫院騎縫章" in health.stamps
    audit = ncu_field_audit(workflow.school_name)
    assert all(x in audit["fields"]["host_deadline"]["note"] for x in ("10/20", "11/20", "12/10", "差異"))
    assert "港澳通行證" in audit["fields"]["eligibility"]["note"]
    assert "2026秋" in audit["fields"]["host_documents"]["note"]
    assert "1500字以上" in audit["fields"]["arrival"]["note"]
    assert "10元封頂" in audit["fields"]["cost"]["note"] and "最多20元" in audit["fields"]["cost"]["note"]
    assert all(not s.deadline_reminder_eligible for s in workflow.steps)
    assert workflow.review_status == "pending_review" and workflow.published_at is None


def test_tongji_new_taiwan_packet_replaces_old_learning_plan_without_creating_current_rules():
    workflow = next(w for w in storage.load_bundled_application_workflows() if w.home_university == NCU.school_name and "Tongji University" in w.school_name)
    initial = next(s for s in workflow.steps if s.rule_id.endswith("host-apply"))
    assert len(initial.document_requirements) == 7
    assert any("通行證" in d.name or "台胞證" in d.name for d in initial.document_requirements)
    assert not any("學習計畫" in d.name for d in initial.document_requirements)
    assert not any(d.official_form_url for d in initial.document_requirements)
    audit = ncu_field_audit(workflow.school_name)
    assert "2026春" in audit["fields"]["host_documents"]["note"]
    assert "2027春" in audit["fields"]["host_documents"]["note"]
    assert "英授工商碩士在新版未列" in audit["fields"]["courses"]["note"]
    assert "不跨校區選課" in audit["fields"]["courses"]["note"]
    partner = next(p for p in fetch_ncu_partner_universities() if p.school_name == workflow.school_name)
    assert partner.quota is None and partner.colleges is None and partner.degree_levels is None
    assert all(audit["fields"][key]["status"] == "needs_confirmation" for key in ("eligibility", "language", "host_documents", "host_deadline", "housing"))


def test_fudan_initial_insurance_paper_translation_and_old_platform_are_distinct():
    from exchange_info.ncu_source_coverage import indexable_source_text
    workflow = next(w for w in storage.load_bundled_application_workflows() if w.home_university == NCU.school_name and "Fudan University" in w.school_name)
    initial = next(s for s in workflow.steps if s.rule_id.endswith("host-apply"))
    assert len(initial.document_requirements) == 6
    assert any("初次電子件" in d.name for d in initial.document_requirements)
    assert any("學習計畫單獨附頁" in d.name for d in initial.document_requirements)
    assert any("認證英文＋自行中譯" in d.name for d in initial.document_requirements)
    assert not any("保單" in d.name for s in workflow.steps if s.phase == "抵達後" for d in s.document_requirements)
    audit = ncu_field_audit(workflow.school_name)
    assert "6／8人套間、2人一房" in audit["fields"]["housing"]["note"]
    assert "新聞學院" in audit["fields"]["city"]["note"]
    raw = json.loads(gzip.decompress((BUNDLE / "source-evidence.json.gz").read_bytes()))
    guide = next(s for s in raw if s["id"] == "host-fudan-nccu-attachment-1rCxNqeHb7l5WBolmzfJyxB4Njorv4c4W")
    assert "2022 年秋季" in guide["pages"][1]["text"]
    assert guide["content_status"]["visual_reviewed_page_count"] == 2
    assert "2022 年秋季" not in indexable_source_text(guide) and "已隔離" in indexable_source_text(guide)
    courses = next(s for s in raw if s["id"] == "host-fudan-nccu-attachment-1sjQ2AhMo0ZpJCf8N6zVsoG4qqPwGrXgQ")
    assert len(courses["pages"]) == 318 and not courses["content_status"]["all_pages_read"]
    for source_id, forbidden in (("host-fudan-nccu-attachment-1KXECul-C7ZG7i76as6qDHnxcjapOKkFm", "H12345678"), ("host-nju-mcu2027-1wX-kZ1wHakbnlyLMfAeYNsIm0bhRcBut", "zhaoyiyi@gmail.com")):
        sheet = next(s for s in raw if s["id"] == source_id)
        assert sheet["source_excerpt_only"] and forbidden not in "\n".join(p["text"] for p in sheet["pages"])
        assert all(p["page"] is None for p in sheet["pages"])


def test_jlu_failed_2026_attachment_does_not_become_read_evidence():
    workflow = next(w for w in storage.load_bundled_application_workflows() if w.home_university == NCU.school_name and "Jilin University" in w.school_name)
    audit = ncu_field_audit(workflow.school_name)
    assert "未標年" in audit["fields"]["host_documents"]["note"]
    failed = next(s for s in audit["unretrieved_sources"] if s["id"] == "host-jlu-exchange-2026")
    assert "404" in failed["reason"]
    assert all(e["source_url"] != failed["url"] for e in audit["fields"]["host_documents"]["original_evidence"])
    assert all(d.needs_confirmation for s in workflow.steps for d in s.document_requirements if "吉林" in d.name)


def test_nju_document_catalog_preserves_separate_pending_second_batch(tmp_path):
    workflow = next(w for w in storage.load_bundled_application_workflows() if w.home_university == NCU.school_name and "Nanjing University" in w.school_name and "Information" not in w.school_name)
    client = TestClient(create_app(tmp_path))
    response = client.get("/application-center/catalog", params={"school": "NCU", "target_school": workflow.school_name, "academic_year": "116"})
    assert response.status_code == 200
    items = response.json()["items"]
    assert len([d for d in items if "第二批" in d["name"]]) == 3
    assert all(d["phase"] == "合作校申請" for d in items if "第二批" in d["name"])
    assert not any(d["phase"] == "抵達後" and "第二批" in d["name"] for d in items)
    assert all(not d["download_available"] and d["needs_confirmation"] for d in items)


@pytest.mark.parametrize("reverse", [False, True])
def test_ncu_same_url_failed_attempt_never_replaces_successful_excerpt(reverse):
    import importlib.util
    spec = importlib.util.spec_from_file_location("ncu_builder_dedup", ROOT / "scripts/build_ncu_catalog.py")
    builder = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(builder)
    url = "https://gjy.nuist.edu.cn/2832/list.htm"
    success = {"id": "browser", "url": url, "label": "成功摘錄", "pages": [{"page": None, "text": "Twin Room 2,500–3,000 CNY per year; eligibility remains track specific."}]}
    failure = {"id": "local", "url": url, "label": "失敗讀取", "error": "403 Forbidden", "pages": []}
    attempts = [failure, success] if reverse else [success, failure]
    indexed = builder.indexed_source_pages(attempts, "南京信息工程")
    assert len(indexed) == 1 and "Twin Room" in indexed[0]["text"]
    assert indexed[0]["source_url"] == url and "成功摘錄" in indexed[0]["title"]
    # The final bundle boundary also protects a nonempty page from empty input.
    empty = {**indexed[0], "text": "", "title": "空來源"}
    candidates = [empty, indexed[0]] if reverse else [indexed[0], empty]
    assert builder.deduplicate_index_pages(candidates) == indexed
    assert builder.indexed_source_pages([failure], "南京信息工程") == []
    blank = {**success, "pages": [{"page": 1, "text": ""}]}
    assert builder.indexed_source_pages([blank], "南京信息工程") == []


def test_actual_nuist_fee_excerpts_survive_url_dedup_and_are_retrievable(tmp_path, monkeypatch):
    from exchange_info.models import ProcessedPage
    from exchange_info.rag import build_rag_index, search_document_chunks
    raw = json.loads(gzip.decompress((BUNDLE / "source-evidence.json.gz").read_bytes()))
    pages = [ProcessedPage.model_validate_json(line) for line in (BUNDLE / "pages.jsonl").read_text().splitlines()]
    for name, phrase in (("cn", "3000"), ("en", "2,000—2,500")):
        success = next(d for d in raw if d["id"] == f"host-nuist-fees-{name}-browser")
        failure = next(d for d in raw if d["id"] == f"host-nuist-fees-{name}")
        assert success["url"] == failure["url"] and failure["error"] and not failure["pages"]
        matching = [p for p in pages if p.source_url == success["url"]]
        assert len(matching) == 1 and phrase in matching[0].text
        monkeypatch.setattr("exchange_info.rag.ai_enabled", lambda: False)
        build_rag_index(matching, tmp_path / name, use_embeddings=False, sync_supabase=False)
        hits = search_document_chunks(f"南京信息工程 住宿 {phrase}", tmp_path / name)
        assert hits and any(phrase in h.chunk.text for h in hits)
        assert all(h.chunk.source_url == success["url"] for h in hits)


def test_nuist_taiwan_2027_packet_is_visual_reference_and_not_current_116():
    raw = json.loads(gzip.decompress((BUNDLE / "source-evidence.json.gz").read_bytes()))
    source = next(s for s in raw if s["id"].startswith("host-nuist-mcu2027-1e_"))
    assert len(source["pages"]) == 8 and all(not p["text"].strip() for p in source["pages"])
    assert source["content_status"]["all_pages_read"] and not source["content_status"]["any_text"]
    assert source["visual_review"]["pdf_pages_reviewed"] == list(range(1, 9))
    assert source["visual_review"]["source_sha256"] == source["sha256"]
    workflow = next(w for w in storage.load_bundled_application_workflows() if w.home_university == NCU.school_name and "Nanjing University of Information" in w.school_name)
    docs = next(s for s in workflow.steps if s.rule_id.endswith("host-apply")).document_requirements
    assert len(docs) == 8 and not any("保險" in d.name for d in docs)
    assert any("三個月內" in d.name for d in docs)
    assert len([d for d in docs if d.official_form_url]) == 2
    assert all(d.needs_confirmation for d in docs)
    audit = ncu_field_audit(workflow.school_name)
    assert "750" in audit["fields"]["housing"]["note"]
    assert "學校" in audit["fields"]["insurance"]["note"] and "購買" in audit["fields"]["insurance"]["note"]
    assert "膳食費" in audit["fields"]["cost"]["note"]
    assert all(audit["fields"][k]["status"] == "needs_confirmation" for k in ("host_documents", "host_deadline", "housing", "insurance"))
    assert workflow.published_at is None and not any(s.deadline_reminder_eligible for s in workflow.steps)


def test_new_mainland_2027_packets_keep_date_examples_track_and_document_stages():
    partners = fetch_ncu_partner_universities()
    workflows = storage.load_bundled_application_workflows()
    xjtu = next(p for p in partners if "Xian Jiaotong University" in p.school_name or "Xi’an Jiaotong University" in p.school_name or "Xi'an Jiaotong University" in p.school_name)
    audit = ncu_field_audit(xjtu.school_name)
    assert "2025/9–2026/1" in audit["fields"]["host_documents"]["note"]
    assert ">2.8" in audit["fields"]["eligibility"]["note"]
    assert "2026/10/30" in audit["fields"]["host_deadline"]["note"]
    hust = next(p for p in partners if "Huazhong University of Science" in p.school_name)
    audit = ncu_field_audit(hust.school_name)
    assert "集成電路" in audit["fields"]["courses"]["note"] and "計算機" in audit["fields"]["courses"]["note"]
    assert "2026/11/3" in audit["fields"]["host_deadline"]["note"]
    workflow = next(w for w in workflows if w.home_university == NCU.school_name and w.school_name == hust.school_name)
    initial = next(s for s in workflow.steps if s.rule_id.endswith("host-apply"))
    assert not any("健康" in d.name for d in initial.document_requirements)
    assert any("錄取後" in d.name for s in workflow.steps if s.phase == "行前準備" for d in s.document_requirements)
    raw = json.loads(gzip.decompress((BUNDLE / "source-evidence.json.gz").read_bytes()))
    flyer = next(s for s in raw if s["id"].startswith("host-hust-mcu2027-1TS"))
    assert flyer["content_status"]["all_pages_read"] and flyer["content_status"]["visual_reviewed"]
    assert not flyer["content_status"]["any_text"]
    assert "upcoming campus" in next(p["text"] for p in flyer["page_transcriptions"] if p["page"] == 7)
    tju = next(p for p in partners if "Tianjin University" in p.school_name)
    audit = ncu_field_audit(tju.school_name)
    assert "秋季" in audit["fields"]["host_deadline"]["note"] and "2026/11/15" in audit["fields"]["host_deadline"]["note"]
    workflow = next(w for w in workflows if w.home_university == NCU.school_name and w.school_name == tju.school_name)
    arrival = [d for s in workflow.steps if s.phase == "抵達後" for d in s.document_requirements]
    assert len(arrival) == 1 and "2027春臺灣" in arrival[0].name and "保險" in arrival[0].name


def test_xjtu_mother_nomination_and_hust_insurance_are_real_catalog_and_task_requirements(tmp_path):
    from exchange_info.application_rules import build_personal_application_plan
    from exchange_info.models import PersonalApplicationPlanRequest

    workflows = storage.load_bundled_application_workflows()
    partners = fetch_ncu_partner_universities()
    xjtu = next(p for p in partners if "Xian Jiaotong University" in p.school_name)
    hust = next(p for p in partners if "Huazhong University" in p.school_name)
    client = TestClient(create_app(tmp_path))
    for partner in (xjtu, hust):
        workflow = next(w for w in workflows if w.home_university == NCU.school_name and w.school_name == partner.school_name)
        assert len({s.order for s in workflow.steps}) == len(workflow.steps)
        assert workflow.review_status == "pending_review" and workflow.published_at is None
        assert not any(s.deadline_reminder_eligible for s in workflow.steps)
        catalog = client.get("/application-center/catalog", params={"school":"NCU","target_school":partner.school_name,"academic_year":"116"}).json()
        plan = build_personal_application_plan(PersonalApplicationPlanRequest(home_school=NCU.school_name, academic_year="116", application_round="第一梯次", preferences=[{"rank":1,"school_name":partner.school_name}]), partners, workflows, academic_score_minimum=None)
        if partner == xjtu:
            item = next(d for d in catalog["items"] if "母校填送" in d["name"])
            assert item["phase"] == "甄選與提名" and "學生不用自行代填" in item["name"]
            assert "1FPQvfD47cwrtkzk0_QwN4XnZtrt-RGI5" in item["official_form_url"]
            task = next(t for t in plan.tasks if "由母校填送" in t.title)
            assert task.responsible_unit == "中央國際事務處" and "不自行代填" in task.detail
        else:
            initial = next(s for s in workflow.steps if s.rule_id.endswith("host-apply"))
            assert not any("保單" in d.name for d in initial.document_requirements)
            insurance = [d for s in workflow.steps for d in s.document_requirements if "境外保單證明" in d.name]
            assert len(insurance) == 1 and "擇一" in insurance[0].name
            item = next(d for d in catalog["items"] if "境外保單證明" in d["name"])
            assert item["phase"] == "行前準備" and "電子版寄送或到校繳交擇一" in item["name"]
            assert any(u.endswith("#page=7") for u in item["source_urls"])
            task = next(t for t in plan.tasks if "擇一提交證明" in t.title)
            assert "不要求電子與到校兩次皆交" in task.detail
            assert len(task.document_link.requirement_names) == 1 and "境外保單證明" in task.document_link.requirement_names[0]
            report = ncu_field_audit(partner.school_name)
            assert "2024 flyer八頁逐頁視覺已讀" in report["fields"]["city"]["applicability"]
            assert "影像未讀" not in report["fields"]["city"]["applicability"]
        assert item["needs_confirmation"] and not item["download_available"] and task.needs_confirmation
        assert task.official_deadline_at is None
        assert "Spring2027" in item["name"]


@pytest.mark.parametrize("needle,count", [("Beijing Normal University",6),("Southeast University",3),("Zhejiang University",7),("Chongqing University",9)])
def test_four_new_packets_reach_summary_workflow_catalog_and_keep_current_year_unconfirmed(tmp_path,needle,count):
    partner = next(p for p in fetch_ncu_partner_universities() if needle in p.school_name)
    assert partner.quota is None and partner.degree_levels is None
    client = TestClient(create_app(tmp_path))
    params = dict(school="NCU",target_school=partner.school_name,academic_year="116")
    workflow = client.get("/application-workflow",params={"home_school":"NCU","school":partner.school_name,"academic_year":"116"})
    assert workflow.status_code == 200
    workflow = workflow.json()
    assert workflow["review_status"] == "pending_review" and workflow["published_at"] is None
    host = next(s for s in workflow["steps"] if s["rule_id"].endswith("host-apply"))
    assert len(host["document_requirements"]) == count
    assert all(s.get("deadline_at") is None for s in workflow["steps"] if "-host-" in (s.get("rule_id")or""))
    assert len({s["order"] for s in workflow["steps"]}) == len(workflow["steps"])
    assert [s["order"] for s in workflow["steps"]] == sorted(s["order"] for s in workflow["steps"])
    catalog = client.get("/application-center/catalog",params=params).json()
    assert all(d["needs_confirmation"] and not d["download_available"] for d in catalog["items"] if not d["name"].startswith(("系統申請表","家長同意書","學生個人","校內必繳","中文版","國際移動力")))
    home = next(s for s in workflow["steps"] if s["rule_id"] == "ncu-116-1-home-3")
    assert len(home["document_requirements"]) == 7
    audit = ncu_field_audit(partner.school_name)
    assert len(audit["fields"]) == 17
    assert all(f["unresolved"] for k,f in audit["fields"].items() if not k.startswith("home_") and k != "quota")
    assert all(f["current_applicability_status"] == "unconfirmed" for k,f in audit["fields"].items() if not k.startswith("home_"))
    if "Beijing" in needle:
        language = audit["fields"]["language"]["note"]
        assert "港澳臺籍語言要求列「無」" in language and "HSK5另軌" in language
        evidence = audit["fields"]["housing"]["original_evidence"][0]
        assert evidence["page"] is None and "原投影片3" in evidence["source_title"] and "60-80" in evidence["text"]
        stage = next(s for s in workflow["steps"] if s["rule_id"].endswith("purchase-insurance"))
        assert not stage["document_requirements"] and stage["source_urls"]
    elif "Southeast" in needle:
        assert "所有原件未標適用學年" in host["summary"]
        assert "10個工作日" in audit["fields"]["transport"]["note"] and "不需接機也勾否" in audit["fields"]["transport"]["note"]
        assert all(d["copies"] == 2 for d in catalog["items"] if "宿舍入住申請表" in d["name"])
        assert "年度學費均免" in audit["fields"]["tuition"]["note"] and "上網「要交費（校園網免費）」" in audit["fields"]["cost"]["note"]
    elif "Zhejiang" in needle:
        assert "2027/2–6" in audit["fields"]["study_period"]["note"] and "2–7月相異" in audit["fields"]["study_period"]["note"]
        assert "1280／1600 RMB／年" in audit["fields"]["housing"]["note"] and "跨校區" in audit["fields"]["housing"]["note"]
        assert "2026/11/20" in audit["fields"]["host_deadline"]["note"] and "10/23" in audit["fields"]["host_deadline"]["note"]
        assert len([d for d in catalog["items"] if "保單（可錄取後補" in d["name"]]) == 1
        assert len([d for d in catalog["items"] if "母校匯總表" in d["name"]]) == 1
        application_form = next(d for d in catalog["items"] if "交換申請表（依本科／研究生" in d["name"])
        original_requirement = next(d for d in host["document_requirements"] if d["name"] == application_form["name"])
        assert application_form["source_urls"] == original_requirement["source_urls"]
        assert len(application_form["source_urls"]) == 3
    else:
        assert "不一定能提供校內宿舍" in audit["fields"]["housing"]["note"] and "800–1200 RMB／學年" in audit["fields"]["housing"]["note"]
        assert "2026/10/30" in audit["fields"]["host_deadline"]["note"]
        later = next(s for s in workflow["steps"] if s["rule_id"].endswith("latest-registration-files"))
        assert later["phase"] == "行前準備" and "亦可提早" in later["timing"] and len(later["document_requirements"]) == 2
        recommendation = next(d for d in host["document_requirements"] if "推薦函" in d["name"])
        assert recommendation["copies"] is None and "1–2" in recommendation["name"]


def test_new_originals_keep_slide_sheet_identity_public_excerpts_and_government_scope():
    raw = json.loads(gzip.decompress((BUNDLE/"source-evidence.json.gz").read_bytes()))
    bnu = next(x for x in raw if x["id"].startswith("host-bnu-mcu2027-1PX"))
    assert [p["slide"]for p in bnu["pages"]] == [1,2,3] and all(p["page"] is None for p in bnu["pages"])
    assert bnu["content_status"]["all_pages_read"]
    cqu = next(x for x in raw if x["id"].startswith("host-cqu-mcu2027-1a-X"))
    assert cqu["pages"][0]["text"].strip() == "" and cqu["visual_review"]["pdf_pages_reviewed"] == list(range(1,11))
    assert "2026年10月30日" in str(cqu["page_transcriptions"])
    workbook = next(x for x in raw if x["id"].startswith("host-cqu-mcu2027-1ZQ"))
    assert len(workbook["pages"]) == 3 and sum(not p["text"].strip() for p in workbook["pages"]) == 2
    assert workbook["content_status"]["all_pages_read"] and not workbook["content_status"]["all_pages_have_text"]
    for prefix in ("host-seu-mcu2027-11h","host-zju-mcu2027-1YR"):
        source = next(x for x in raw if x["id"].startswith(prefix))
        assert source["source_excerpt_only"] and "移除" in source["privacy_note"]
        excerpt_path = ROOT/"sources/ncu/2026-10-08"/f"{source['id']}-public-excerpt.json"
        excerpt = json.loads(excerpt_path.read_text())
        assert excerpt["source_sha256"] == source["sha256"]
        from exchange_info.ncu_source_coverage import attach_public_field_excerpt
        changed = {"sha256":"changed-original","pages":[{"page":None,"text":"private example"}]}
        attach_public_field_excerpt(changed,excerpt)
        assert changed["pages"] == [] and "原件已變更" in changed["error"]
    share = next(x for x in raw if x["id"] == "host-zju-partner-course-share")
    assert "Invalid share" in share["pages"][0]["text"]
    from exchange_info.ncu_source_coverage import indexable_source_text
    guide = next(x for x in raw if x["id"] == "government-taiwan-permit-guide")
    assert "200元" in guide["pages"][0]["text"]
    assert "不可用舊200／40" in indexable_source_text(guide) and "首次申请、换发、补发200元" not in indexable_source_text(guide)
    for needle in ("Beijing Normal University","Southeast University","Zhejiang University","Chongqing University"):
        partner = next(p for p in fetch_ncu_partner_universities()if needle in p.school_name)
        audit = ncu_field_audit(partner.school_name)
        assert "親友家" in audit["fields"]["visa"]["note"] and "24小時" in audit["fields"]["visa"]["note"]
        assert "不足6個月是五年證可換發條件" in audit["fields"]["visa"]["note"]
        assert "2027/12/31" in audit["fields"]["cost"]["note"] and "2028" in audit["fields"]["cost"]["note"]


@pytest.mark.parametrize('needle,rowid,initial_count', [('Xiamen University','ncu-192',4),('SOUTHWEST UNIVERSITY','ncu-179',6),('Central China Normal University','ncu-189',8)])
def test_xmu_swu_ccnu_new_packets_keep_stage_scope_and_current_year_unknown(tmp_path,needle,rowid,initial_count):
    partner=next(p for p in fetch_ncu_partner_universities() if needle in p.school_name)
    assert partner.quota is None and partner.degree_levels is None
    assert partner.availability_status=='agreement_only'
    client=TestClient(create_app(tmp_path))
    response=client.get('/application-workflow',params={'home_school':'NCU','school':partner.school_name,'academic_year':'116'})
    assert response.status_code==200
    workflow=response.json()
    initial=next(s for s in workflow['steps'] if s['rule_id']==rowid+'-host-apply')
    assert len(initial['document_requirements'])==initial_count
    assert len(next(s for s in workflow['steps']if s['rule_id']=='ncu-116-1-home-3')['document_requirements'])==7
    assert workflow['review_status']=='pending_review' and workflow['published_at'] is None
    assert len({s['order']for s in workflow['steps']})==len(workflow['steps'])
    assert [s['order']for s in workflow['steps']]==sorted(s['order']for s in workflow['steps'])
    assert all(not s['deadline_reminder_eligible']for s in workflow['steps'])
    audit=ncu_field_audit(partner.school_name)
    assert len(audit['fields'])==17
    assert all(x['unresolved'] and x['current_applicability_status']=='unconfirmed'for k,x in audit['fields'].items()if not k.startswith('home_')and k!='quota')
    catalog=client.get('/application-center/catalog',params={'school':'NCU','target_school':partner.school_name,'academic_year':'116','host_admission_status':'accepted','housing_choice':'on_campus'}).json()
    for item in catalog['items']:
        if item['name'] in [d['name']for s in workflow['steps'] if '-host-'in(s.get('rule_id')or'')for d in s['document_requirements']]:
            assert item['needs_confirmation'] and not item['download_available']
    assert '2028' in audit['fields']['cost']['note'] and '親友' in audit['fields']['visa']['note']
    if rowid=='ncu-192':
        assert '漳州' in audit['fields']['city']['note'] and '600' in audit['fields']['cost']['note']
        assert '8296列' in audit['fields']['courses']['unresolved']
        assert '本科4／5／6年' in audit['fields']['study_period']['note']
        assert not any('保單'in d['name'] or '護照'in d['name']for d in initial['document_requirements'])
        health=next(d for d in initial['document_requirements']if '健康狀況'in d['name'])
        assert 'DOCX' in health['name'] and health['signatures']==['申請人本人簽名','日期']
        insurance=next(s for s in workflow['steps']if s['rule_id'].endswith('registration-insurance'))
        assert insurance['phase']=='行前準備' and '入學報到' in insurance['timing']
        assert len(insurance['document_requirements'])==1
        assert not next(s for s in workflow['steps']if s['rule_id'].endswith('health-confirmation'))['document_requirements']
        image_evidence=[x for x in audit['fields']['city']['original_evidence']if '原文圖片'in x['source_title']]
        assert len(image_evidence)==6 and all(x['page'] is None and x['text_method']=='human_visual_selected_passages'for x in image_evidence)
    elif rowid=='ncu-179':
        assert '不能硬排' in audit['fields']['eligibility']['note'] and '至少4門' in audit['fields']['courses']['note']
        assert '第2頁' in audit['fields']['host_documents']['note'] and '第三頁' in audit['fields']['host_documents']['note']
        assert '500–600' in audit['fields']['housing']['note'] and 'PG2人' in audit['fields']['housing']['unresolved']
        portfolio=next(d for d in catalog['items']if '作品集'in d['name'])
        assert portfolio['phase']=='合作校申請' and portfolio['applicability']['status']=='needs_confirmation'
        assert '接收單位通知確認是否適用' in portfolio['applicability']['note']
        insurance=next(s for s in workflow['steps']if s['rule_id'].endswith('insurance-timing-unconfirmed'))
        assert '未載' in insurance['timing'] and len(insurance['document_requirements'])==1
        assert not any('保險'in d['name']for d in initial['document_requirements'])
    else:
        assert '2026/11/2' in audit['fields']['host_deadline']['note'] and '12/15' in audit['fields']['host_deadline']['note']
        assert '本科線上' in audit['fields']['courses']['note'] and '研究生線下' in audit['fields']['courses']['note']
        assert '6月內' in next(d for d in initial['document_requirements']if '體檢'in d['name'])['name']
        assert len([d for d in initial['document_requirements']if '申報表'in d['name']])==1
        assert not any('獨立'in d['name'] or '保單'in d['name']for d in initial['document_requirements'])
        later=next(s for s in workflow['steps']if s['rule_id'].endswith('host-arrival-documents'))
        assert later['phase']=='抵達後' and len(later['document_requirements'])==1
        assert '行前購買'in later['document_requirements'][0]['name']
        assert '房型' in audit['fields']['housing']['note'] and '不保证' in audit['fields']['housing']['note']


def test_xmu_actual_2027_images_old_unreviewed_workbook_and_captcha_are_distinct():
    raw=json.loads(gzip.decompress((BUNDLE/'source-evidence.json.gz').read_bytes()));byid={x['id']:x for x in raw}
    for code in ['cn_ba','en_ba','cn_ma','en_ma','cn_dr','en_dr']:
        html=byid['host-xmu-majors-'+code]
        assert '2027' in html['pages'][0]['text']
        image=byid['host-xmu-majors-'+code+'-image']
        assert image['source_excerpt_only'] and image['pages'][0]['image']==1 and image['pages'][0]['page'] is None
        assert image['content_status']['all_pages_read'] and image['content_status']['visual_reviewed_image_count']==1
        assert not image['content_status']['all_pages_have_text']
    workbook=byid['host-xmu-course-reference-2025-26']
    assert len(workbook['pages'])==2 and 'native_sheets' in workbook['document_format']
    assert workbook['content_status']['all_pages_have_text'] and not workbook['content_status']['all_pages_read']
    assert len(workbook['pages'][0]['text'].splitlines())==4124 and len(workbook['pages'][1]['text'].splitlines())==4174
    from exchange_info.ncu_source_coverage import indexable_source_text
    assert '未全文逐列核對' in indexable_source_text(workbook)
    assert 'Introduction to Flexible Electronics' not in indexable_source_text(workbook)
    captcha=byid['host-xmu-health-captcha']
    assert captcha['status']==200 and captcha['content_status']['response_bytes_received']
    assert not captcha['content_status']['downloaded'] and not captcha['pages'] and '驗證碼' in captcha['error']
    health=byid['host-xmu-health-declaration']
    assert health['document_format']=='docx_no_fixed_pdf_pages' and health['content_status']['all_pages_read']
    assert health['previous_attempts'] and all(p['page'] is None for p in health['pages'])
    swu=byid['host-swu-mcu2027-1iA5iSLdiHw1hVu0c-UbvSbR9e8rqMZ2Y']
    assert len(swu['pages'])==11 and swu['visual_review']['pdf_pages_reviewed']==list(range(1,12))
    assert swu['pages'][6]['text']==swu['pages'][7]['text'] and not swu.get('index_review')
    ccnu=byid['host-ccnu-mcu2027-16lfKolTxlgxK7TPFF7JcvzsLzOSRE7uY']
    assert len(ccnu['pages'])==22 and ccnu['content_status']['all_pages_read']
    assert ccnu['visual_review']['pdf_pages_reviewed']==[5]
    browser=byid['host-ccnu-procedure-browser-excerpt']
    assert browser['local_http_status']==403 and not browser.get('sha256')
    assert not browser['content_status']['downloaded'] and not browser['content_status']['all_pages_read']


@pytest.mark.parametrize('needle,rowid,initial_count',[
    ('Beijing University of Posts and Telecommunications','ncu-176',6),
    ('South China University of Technology','ncu-191',5),
    ('Guangxi University','ncu-193',6),
])
def test_bupt_scut_gxu_reference_packets_keep_missing_forms_and_unknown_116(tmp_path,needle,rowid,initial_count):
    partner=next(p for p in fetch_ncu_partner_universities() if needle in p.school_name)
    assert partner.quota is None and partner.degree_levels is None
    assert partner.availability_status=='agreement_only'
    client=TestClient(create_app(tmp_path))
    workflow=client.get('/application-workflow',params={'home_school':'NCU','school':partner.school_name,'academic_year':'116'}).json()
    initial=next(s for s in workflow['steps']if s['rule_id']==rowid+'-host-apply')
    assert len(initial['document_requirements'])==initial_count
    assert all(d['needs_confirmation'] and not d.get('official_form_url')for d in initial['document_requirements'])
    assert len(next(s for s in workflow['steps']if s['rule_id']=='ncu-116-1-home-3')['document_requirements'])==7
    assert workflow['review_status']=='pending_review' and workflow['published_at'] is None
    assert all(not s['deadline_reminder_eligible']for s in workflow['steps'])
    catalog=client.get('/application-center/catalog',params={'school':'NCU','target_school':partner.school_name,'academic_year':'116'}).json()
    host_names={d['name']for d in initial['document_requirements']}
    host_items=[d for d in catalog['items']if d['name']in host_names]
    assert len(host_items)==initial_count and all(not d['download_available'] and d['needs_confirmation']for d in host_items)
    audit=ncu_field_audit(partner.school_name)
    assert len(audit['fields'])==17
    assert all(f['unresolved'] and f['current_applicability_status']=='unconfirmed'for k,f in audit['fields'].items()if k!='quota'and not k.startswith('home_'))
    if rowid=='ncu-176':
        assert '藍底' in audit['fields']['host_documents']['note'] and '白底' in audit['fields']['host_documents']['note']
        assert '刪掉申請截止' in audit['fields']['host_deadline']['note'] and '2025/10/31' in audit['fields']['host_deadline']['note']
        assert '碩博另需' in audit['fields']['host_documents']['note']
        assert not any('保單' in d['name']for d in initial['document_requirements'])
    elif rowid=='ncu-191':
        assert '480×640' in audit['fields']['host_documents']['note']
        assert '無空白表' in audit['fields']['host_documents']['note']
        assert 'outgoing' in audit['fields']['arrival']['note']
        assert '600–1500' in audit['fields']['housing']['note']
    else:
        assert '每年3月至次年7月' in audit['fields']['study_period']['note']
        assert '未自行改' in audit['fields']['study_period']['note']
        assert '2021免試' in audit['fields']['host_documents']['note']
        assert '普通疾病' in audit['fields']['insurance']['note']
        step=next(s for s in workflow['steps']if s['rule_id'].endswith('gxu-local-accident-insurance'))
        assert step['phase']=='抵達後' and not step['document_requirements']
        assert '原件未列保单提交義務' in step['summary']
        evidence=next(x for x in audit['fields']['study_period']['original_evidence']if x['page']==2)
        assert '每年 3 月至次年 7 月' in evidence['text']


def test_gxu_visual_photos_scut_outgoing_and_browser_excerpts_are_not_new_host_forms():
    raw=json.loads(gzip.decompress((BUNDLE/'source-evidence.json.gz').read_bytes()));byid={s['id']:s for s in raw}
    gxu=byid['1ZXdTqdujPenTWqBuJf1p8uCNixT0e6Gy']
    assert len(gxu['pages'])==16 and gxu['visual_review']['pdf_pages_reviewed']==list(range(1,17))
    assert gxu['content_status']['all_pages_read'] and not gxu['content_status']['all_pages_have_text']
    assert gxu['pages'][3]['text']==''
    guide=byid['host-scut-hmt-guide-2018-pdf']
    assert guide['visual_review']['pdf_pages_reviewed']==list(range(1,8))
    assert not any(p['text']for p in guide['pages'])
    from exchange_info.ncu_source_coverage import indexable_source_text
    text=indexable_source_text(guide)
    assert '不借用' in text and 'Student Handbook' not in text
    browser=byid['host-gxu-degree-form-entry-browser-excerpt']
    assert '2021版' in browser['pages'][0]['text'] and not browser.get('sha256')
    assert not browser['content_status']['all_pages_read'] and not browser['content_status']['downloaded']
    broken=byid['host-scut-ccu-broken-short-link']
    assert broken['status']==200 and '轉址失敗' in broken['error']
    assert broken['content_status']['response_bytes_received'] and not broken['content_status']['downloaded']


def test_hiroshima_current_forms_do_not_expand_home_degree_scope_or_expired_round(tmp_path):
    partner=next(p for p in fetch_ncu_partner_universities() if 'Hiroshima University' in p.school_name)
    assert partner.quota is None and partner.degree_levels is None
    client=TestClient(create_app(tmp_path))
    workflow=client.get('/application-workflow',params={'home_school':'NCU','school':partner.school_name,'academic_year':'116'}).json()
    steps={s['rule_id']:s for s in workflow['steps']}
    initial=steps['ncu-115-host-apply']
    assert len(initial['document_requirements'])==8
    assert len(steps['ncu-116-1-home-3']['document_requirements'])==7
    assert not any('銀行' in d['name'] or '簽證申請' in d['name'] or '退居' in d['name']for d in initial['document_requirements'])
    assert len(steps['ncu-115-host-coe-financial']['document_requirements'])==1
    assert len(steps['ncu-115-host-japan-student-visa']['document_requirements'])==5
    assert not steps['ncu-115-host-local-health-insurance']['document_requirements']
    assert not steps['ncu-115-host-medicine-import']['document_requirements']
    arrival=steps['ncu-116-1-home-8']['order'];returned=steps['ncu-116-1-home-9']['order']
    for suffix in ['local-health-insurance','temporary-travel','ikenoue-departure']:
        assert arrival < steps['ncu-115-host-'+suffix]['order'] < returned
    assert steps['ncu-115-host-ikenoue-departure']['phase']=='離校準備'
    assert steps['ncu-115-host-research-hours-petition']['order']<steps['ncu-116-1-home-6']['order']
    assert workflow['review_status']=='pending_review' and workflow['published_at'] is None
    assert not any(s['deadline_reminder_eligible']for s in workflow['steps'])
    audit=ncu_field_audit(partner.school_name)
    assert '中央115表另限大學部' in audit['fields']['eligibility']['note']
    assert '61+' in audit['fields']['language']['note'] and 'above' in audit['fields']['language']['note']
    assert '中央home正式語檢必繳' in audit['fields']['language']['note']
    assert '2028/2/9' in audit['fields']['study_period']['note']
    assert '2027春提名8/15' in audit['fields']['host_deadline']['note']
    assert '2027秋或2028春提醒' in audit['fields']['host_deadline']['note']
    assert '3120TWD' in audit['fields']['cost']['note']
    assert '未標年' in audit['fields']['housing']['unresolved'] or '116' in audit['fields']['housing']['unresolved']
    catalog=client.get('/application-center/catalog',params={'school':'NCU','target_school':partner.school_name,'academic_year':'116'}).json()
    initial_names={d['name']for d in initial['document_requirements']}
    documents=[d for d in catalog['items']if d['name']in initial_names]
    assert len(documents)==8 and all(not d['download_available']for d in documents)
    forms=[d for d in documents if d.get('official_form_url')]
    assert len(forms)==2 and all(d['source_urls']for d in forms)


def test_hiroshima_source_years_visual_fee_and_selected_old_guide_are_auditable():
    raw=json.loads(gzip.decompress((BUNDLE/'source-evidence.json.gz').read_bytes()));sources={s['id']:s for s in raw}
    from exchange_info.ncu_source_coverage import indexable_source_text
    calendar=sources['host-hiro-calendar2027']
    assert len(calendar['pages'])==1 and calendar['visual_review']['pdf_pages_reviewed']==[1]
    assert '2027' in calendar['pages'][0]['text'] and '10/4' in calendar['pages'][0]['text']
    fee=sources['government-japan-koryu-fee-image-1']
    assert fee['pages'][0]['page'] is None and fee['pages'][0]['image']==1
    assert fee['content_status']['visual_reviewed_image_count']==1
    assert fee['visual_review']['source_sha256']==fee['sha256']
    assert '3,120' in fee['pages'][0]['text'] and '印度' in fee['pages'][0]['text']
    old=sources['host-hiro-ikenoue-guide2023']
    assert len(old['pages'])==33 and len(old['reading_review']['pages_reviewed'])==9
    assert not old['content_status']['all_pages_read']
    assert '7,500 yen' in old['pages'][28]['text']
    assert '7,500 yen' not in indexable_source_text(old)
    pre=sources['host-hiro-prearrival']
    assert "a year's supply" in pre['pages'][0]['text']
    assert "a year's supply" not in indexable_source_text(pre)
    qa=sources['government-japan-mhlw-medicine-qa']
    assert 'Adults：1 tablet' in qa['pages'][8]['text']
    assert 'Adults：1 tablet' not in indexable_source_text(qa)
    for ident in ['government-japan-koryu-visa-mandarin-blank','government-japan-koryu-visa-english-blank']:
        assert len(sources[ident]['pages'])==2 and sources[ident]['content_status']['all_pages_read']
    assert sources['host-hiro-dorm-guide2025']['error']
    assert not sources['host-hiro-dorm-guide2025']['content_status']['downloaded']


def test_science_tokyo_tracks_precede_common_application_and_do_not_reuse_hiroshima_coe(tmp_path):
    partner=next(p for p in fetch_ncu_partner_universities() if 'Institute of Science Tokyo' in p.school_name)
    client=TestClient(create_app(tmp_path))
    workflow=client.get('/application-workflow',params={'home_school':'NCU','school':partner.school_name,'academic_year':'116'}).json()
    steps={s['rule_id']:s for s in workflow['steps']}
    initial=steps['ncu-133-host-apply']
    assert len(initial['document_requirements'])==8
    assert any('COE申請Excel' in d['name']for d in initial['document_requirements'])
    assert not any('銀行' in d['name']or'Part I' in d['name']or'TIEC' in d['name']or'指導同意' in d['name']for d in initial['document_requirements'])
    preceding=['acap-nomination-course','ysep-prior-consent','track-documents']
    assert [steps['ncu-133-host-'+x]['order']for x in preceding]==[5,6,7]
    assert initial['order']==8
    assert len(steps['ncu-133-host-track-documents']['document_requirements'])==2
    assert '建築及ACAP由校方安排' in steps['ncu-133-host-ysep-prior-consent']['summary']
    assert len(steps['ncu-133-host-pre-enrollment-health']['document_requirements'])==2
    assert len(steps['ncu-133-host-tiec-conditional']['document_requirements'])==8
    assert len(steps['ncu-133-host-requested-financial']['document_requirements'])==1
    assert len(steps['ncu-116-1-home-3']['document_requirements'])==7
    orders=[s['order']for s in workflow['steps']]
    assert orders==list(range(1,len(orders)+1))
    arrival=steps['ncu-116-1-home-8']['order'];returned=steps['ncu-116-1-home-9']['order']
    for suffix in ['local-insurance','temporary-travel']:
        assert arrival<steps['ncu-133-host-'+suffix]['order']<returned
        assert not steps['ncu-133-host-'+suffix]['document_requirements']
    assert workflow['review_status']=='pending_review' and workflow['published_at']is None
    assert partner.quota is None and not any(s['deadline_reminder_eligible']for s in workflow['steps'])
    audit=ncu_field_audit(partner.school_name)
    assert '限115-2' in audit['fields']['eligibility']['note']
    assert 'JLPT N1' in audit['fields']['language']['note'] and '不能自動' in audit['fields']['language']['note']
    assert '2027/3/1' in audit['fields']['cost']['note'] and 'A48000' in audit['fields']['cost']['note']
    assert '2027秋或2028春提醒' in audit['fields']['host_deadline']['note']
    assert '每週六堂600分鐘' in audit['fields']['courses']['note']
    assert '醫療／醫學不是被排除的醫學院身分' in audit['fields']['courses']['note']
    assert 'All students' in audit['fields']['arrival']['note']
    assert '2023 FAQ強烈建議與現行必須分開' in audit['fields']['insurance']['note']
    catalog=client.get('/application-center/catalog',params={'school':'NCU','target_school':partner.school_name,'academic_year':'116'}).json()
    scoped=[d for d in catalog['items']if d['applicability']]
    assert len(scoped)==16
    assert all(d['applicability']['status']=='needs_confirmation' and not d['download_available']for d in scoped)
    assert any('共用參考：COE申請Excel' in d['name'] and d['official_form_url'].endswith('2026-v3.xlsx')for d in catalog['items'])


def test_science_tokyo_original_forms_examples_years_and_partial_guide_read_are_distinct():
    sources={s['id']:s for s in json.loads(gzip.decompress((BUNDLE/'source-evidence.json.gz').read_bytes()))}
    from exchange_info.ncu_source_coverage import indexable_source_text
    coe=sources['host-science-coe2026-blank']
    assert len(coe['pages'])==5 and coe['source_excerpt_only']
    assert '非全空白' in coe['privacy_note'] and '學生三sheet' in coe['privacy_note']
    assert 'SMITH' not in json.dumps(coe['pages']) and '120000' not in indexable_source_text(coe)
    for ident in ['host-science-tiec-form1','host-science-tiec-form3']:
        assert len(sources[ident]['pages'])==1 and sources[ident]['source_excerpt_only']
        assert '第二張記入例' in sources[ident]['privacy_note']
    health=sources['host-science-health-part1']
    assert health['visual_review']['pdf_pages_reviewed']==[1,2]
    assert 'All student' in health['pages'][0]['text'] and '2026. 10' in health['pages'][0]['text']
    vaccine=sources['host-science-health-part2']
    assert vaccine['visual_review']['pdf_pages_reviewed']==[1,2]
    assert 'partial combination of BOTH' in vaccine['pages'][0]['text']
    tb=sources['host-science-tb-country-list']
    assert tb['content_status']['visual_reviewed_page_count']==1 and len(tb['pages'][0]['text'])<100
    assert 'n=129' in tb['page_transcriptions'][0]['text']
    guide=sources['host-science-current-guide']
    assert not guide['content_status']['all_pages_read'] and guide['reading_review']['selected_passages_reviewed']
    old=sources['host-science-exchange-faq']
    assert 'No, but there are recommended courses' in old['pages'][0]['text']
    assert 'No, but there are recommended courses' not in indexable_source_text(old)
    comparison=sources['1_jNWLlS-y-ndrAXwzLiScNbhrcN6I7Hh']
    assert comparison['content_status']['all_pages_read'] and 'contact an ACAP' in comparison['pages'][1]['text']
    assert 'contact an ACAP' not in indexable_source_text(comparison)
    schedule=sources['host-science-tiec-schedule2025']
    assert all('2026/01/15' in p['text']for p in schedule['pages'])
    assert '2026/01/15' in schedule['title']
    course=sources['host-science-course-ug2026']
    assert course['content_status']['all_pages_read'] and len(course['pages'])==5
    assert 'Medical and Welfare' in course['pages'][0]['text']


def test_chiba_initial_health_language_alternatives_and_later_coe_are_separate(tmp_path):
    partner = next(p for p in fetch_ncu_partner_universities() if 'Chiba University' in p.school_name)
    assert partner.quota is None and partner.degree_levels is None
    client = TestClient(create_app(tmp_path))
    workflow = client.get('/application-workflow', params={'home_school': 'NCU', 'school': partner.school_name, 'academic_year': '116'}).json()
    steps = {s['rule_id']: s for s in workflow['steps']}
    initial = steps['ncu-127-host-apply']
    assert len(initial['document_requirements']) == 8
    health = next(d for d in initial['document_requirements'] if '健康' in d['name'])
    assert '初次申請即繳' in health['name'] and health['signatures'] == ['醫師']
    assert health['official_form_url'].endswith('04-7.Certificate-of-Health.docx')
    assert not any('COE' in d['name'] or '租屋' in d['name'] or 'checklist' in d['name'] for d in initial['document_requirements'])
    assert len(steps['ncu-116-1-home-3']['document_requirements']) == 7
    assert steps['ncu-127-host-mother-nomination']['order'] < steps['ncu-127-host-language-branches']['order'] < initial['order']
    language = steps['ncu-127-host-language-branches']
    assert len(language['document_requirements']) == 3 and '英或日擇一' in language['summary']
    later = steps['ncu-127-host-post-selection-coe']
    assert later['order'] > initial['order'] and len(later['document_requirements']) == 1
    assert '未取得' in later['summary'] and not later['document_requirements'][0]['official_form_url']
    guarantee = steps['ncu-127-host-institutional-guarantor']['document_requirements'][0]
    assert guarantee['signatures'] == ['學術指導教師'] and guarantee['stamps'] == ['學術指導教師']
    arrival = steps['ncu-116-1-home-8']['order']; returned = steps['ncu-116-1-home-9']['order']
    for suffix in ['local-registration-insurance', 'temporary-travel', 'final-departure']:
        step = steps['ncu-127-host-' + suffix]
        assert arrival < step['order'] < returned and not step['document_requirements']
    assert [s['order'] for s in workflow['steps']] == list(range(1, len(steps) + 1))
    assert workflow['review_status'] == 'pending_review' and workflow['published_at'] is None
    assert not any(s['deadline_reminder_eligible'] for s in workflow['steps'])
    audit = ncu_field_audit(partner.school_name)
    assert '4名上2／下2' in audit['fields']['eligibility']['note'] and 'Graduate checkbox' in audit['fields']['eligibility']['note']
    assert '50小時與英日擇一' in audit['fields']['language']['note']
    assert '母校英語教師' in audit['fields']['language']['note'] and '中央home正式語檢' in audit['fields']['language']['note']
    assert '春2026/8/28' in audit['fields']['host_deadline']['note'] and '皆已過' in audit['fields']['host_deadline']['note']
    assert '2027秋／2028春' in audit['fields']['host_deadline']['unresolved']
    assert 'Term6' in audit['fields']['courses']['note'] and '每semester兩個連續terms' in audit['fields']['courses']['note']
    assert '含租金' in audit['fields']['cost']['note'] and '17920' in audit['fields']['cost']['note']
    assert '已2025/9關閉' in audit['fields']['housing']['note'] and '校區附近公寓' in audit['fields']['housing']['note']
    assert 'A沒有傷病醫療費' in audit['fields']['insurance']['note'] and 'B一年11500' in audit['fields']['insurance']['note']
    assert 'self-check明寫不需提交' in audit['fields']['arrival']['note']
    catalog = client.get('/application-center/catalog', params={'school': 'NCU', 'target_school': partner.school_name, 'academic_year': '116'}).json()
    scoped = [d for d in catalog['items'] if d['applicability']]
    assert len(scoped) == 6 and all(d['applicability']['status'] == 'needs_confirmation' and not d['download_available'] for d in scoped)
    assert all(not d['download_available'] for d in catalog['items'] if d['name'] in {x['name'] for x in initial['document_requirements']})


def test_chiba_native_years_partial_read_and_complete_insurance_visual_evidence():
    from exchange_info.ncu_source_coverage import indexable_source_text
    sources = {s['id']: s for s in json.loads(gzip.decompress((BUNDLE / 'source-evidence.json.gz').read_bytes()))}
    current = sources['host-chiba-outline2026-host']
    assert len(current['pages']) == 33 and current['content_status']['all_pages_read']
    assert current['content_status']['visual_reviewed_page_count'] == 2
    assert current['visual_review']['pdf_pages_reviewed'] == [16, 31]
    assert sources['host-chiba-outline2026-cau']['sha256'] == current['sha256']
    assert 'YES' in current['pages'][15]['text'] and 'Are you a native' not in indexable_source_text(current)
    old = sources['host-chiba-outline2026-host-alternate']
    assert '2024' in old['pages'][0]['text'] and old['reading_review']['pages_reviewed'] == [1]
    assert not old['content_status']['all_pages_read']
    handbook = sources['host-chiba-student-handbook2025']
    assert len(handbook['pages']) == 92 and len(handbook['reading_review']['pages_reviewed']) == 18
    assert not handbook['content_status']['all_pages_read']
    insurance = sources['host-chiba-insurance-pamphlet']
    assert len(insurance['pages']) == 15 and insurance['content_status']['text_page_count'] == 1
    assert insurance['content_status']['all_pages_read'] and insurance['content_status']['visual_reviewed_page_count'] == 15
    assert insurance['content_status']['ocr_status'] == 'not_performed'
    assert len(insurance['visual_review']['artifacts']) == 15
    for ident in ['host-chiba-health2026-ugm', 'host-chiba-en-certificate2026-ugm', 'host-chiba-ja-certificate2026-ugm']:
        form = sources[ident]
        assert form['pages'][0]['page'] is None and form['content_status']['all_pages_read']
        assert form['document_format'] == 'docx_no_fixed_pdf_pages'
    assert sources['host-chiba-course2026-cie-probe']['status'] == 404
    assert sources['government-japan-isa-special-reentry-new']['status'] == 403
    assert not sources['government-japan-isa-special-reentry-new']['pages']
    assert sources['government-japan-isa-special-reentry-pdf']['status'] == 403
    assert not sources['government-japan-isa-special-reentry-pdf']['content_status']['downloaded']
    partner = sources['host-science-partner-resultlist']
    assert partner['pages'][0]['page'] is None and partner['source_excerpt_only']
    assert partner['document_format'] == 'json_no_pdf_pages' and not partner['content_status']['all_pages_read']
    row = json.loads(partner['pages'][0]['text'])
    assert row['name'] == 'National Central University' and row['exchange02'] == row['exchange03'] == 't'
    science = ncu_field_audit('東京科學大學 Institute of Science Tokyo')
    assert '未核對中央這列' not in science['fields']['eligibility']['unresolved']
    assert '不是262伙伴全文已讀' in science['fields']['tuition']['note']


def test_omu_2027_spring_optional_documents_and_later_housing_keep_116_blocked(tmp_path):
    partner = next(p for p in fetch_ncu_partner_universities() if 'Osaka Metropolitan' in p.school_name)
    assert partner.quota is None and partner.degree_levels is None
    client = TestClient(create_app(tmp_path))
    workflow = client.get('/application-workflow', params={'home_school': 'NCU', 'school': partner.school_name, 'academic_year': '116'}).json()
    steps = {s['rule_id']: s for s in workflow['steps']}
    initial = steps['ncu-132-host-apply']
    assert len(initial['document_requirements']) == 8
    assert len(steps['ncu-116-1-home-3']['document_requirements']) == 7
    assert sum(d['name'].startswith('母校承辦另出') for d in initial['document_requirements']) == 3
    assert not any(any(word in d['name'] for word in ['COE指定', '住宿健康', '英文能力']) for d in initial['document_requirements'])
    photo = next(d for d in initial['document_requirements'] if 'JPG' in d['name'])
    assert '不同於護照照片' in photo['name'] and '近三月' in photo['name']
    assert 'COE／學生證' in photo['name'] and '尺寸待核' in photo['name']
    assert '近三個月拍攝、彩色脫帽清晰' in '\n'.join(initial['details'])
    assert not set(photo) & {'photo_specs', 'copies_required', 'notes'}
    pledge = next(d for d in initial['document_requirements'] if '誓約' in d['name'])
    assert pledge['signatures'] == ['申請人']
    enrollment = next(d for d in initial['document_requirements'] if '指定英文在籍' in d['name'])
    assert not enrollment['signatures'] and not enrollment['stamps']
    for suffix in ['mother-nomination', 'degree-specific-plan', 'english-if-held', 'consideration-if-requested']:
        assert steps['ncu-132-host-' + suffix]['order'] < initial['order']
    assert len(steps['ncu-132-host-degree-specific-plan']['document_requirements']) == 2
    assert '不是兩件都交' in steps['ncu-132-host-degree-specific-plan']['summary']
    assert '持有才交' in steps['ncu-132-host-english-if-held']['summary']
    for suffix in ['post-selection-coe', 'i-wing-health']:
        step = steps['ncu-132-host-' + suffix]
        assert initial['order'] < step['order'] and len(step['document_requirements']) == 1
        assert not step['document_requirements'][0]['official_form_url']
    assert '日本籍含雙重' in steps['ncu-132-host-post-selection-coe']['summary']
    assert workflow['review_status'] == 'pending_review' and workflow['published_at'] is None
    assert not any(s['deadline_reminder_eligible'] for s in workflow['steps'])
    audit = ncu_field_audit(partner.school_name)
    assert '不因外校申請未到' in audit['fields']['host_deadline']['note']
    assert '不能以Graduate' in audit['fields']['eligibility']['note']
    assert '創藥科學碩士明列' in audit['fields']['eligibility']['note']
    assert 'N2總分90–111對應B1' in audit['fields']['language']['note']
    assert '112以上B2' in audit['fields']['language']['note']
    assert '每semester至少兩門且一專業' in audit['fields']['courses']['note']
    assert '不能忽略或regex直接不合格' in audit['fields']['courses']['note']
    assert '全系自動通過' in audit['fields']['eligibility']['unresolved']
    assert '不強制普通臺灣交換生' in audit['fields']['visa']['note']
    assert '資格資訊通知書單獨不能看診' in audit['fields']['insurance']['note']
    summary = json.dumps(partner.student_summary_zh.model_dump(mode='json'), ensure_ascii=False)
    assert '專業課' in summary and '46000' in summary and '健康診斷書' in summary
    catalog = client.get('/application-center/catalog', params={'school': 'NCU', 'target_school': partner.school_name, 'academic_year': '116'}).json()
    scoped = [d for d in catalog['items'] if d['applicability']]
    assert len(scoped) == 7 and all(d['applicability']['status'] == 'needs_confirmation' for d in scoped)
    assert all(not d['download_available'] for d in scoped)


def test_existing_ncu_document_counts_and_scope_notes_reach_workflow_api(tmp_path):
    client = TestClient(create_app(tmp_path))
    for english, count in [('Chiba University', 8), ('Institute of Science Tokyo', 1)]:
        partner = next(p for p in fetch_ncu_partner_universities() if english in p.school_name)
        workflow = client.get('/application-workflow', params={
            'home_school': 'NCU', 'school': partner.school_name, 'academic_year': '116',
        }).json()
        initial = next(s for s in workflow['steps'] if s['rule_id'].endswith('-host-apply'))
        assert sum(d['copies'] == 1 for d in initial['document_requirements']) == count
        visa = next(s for s in workflow['steps'] if s['rule_id'].endswith('-host-japan-student-visa'))
        assert next(d for d in visa['document_requirements'] if d['name'] == '臺灣護照持COE：六個月內2吋白底照一張')['copies'] == 1
    for english, note in [
        ('University of Manitoba', '由exchange coordinator或supervisor提供；僅研究所適用。'),
        ('Shinshu University', '原文if available，非全體強制JLPT。'),
        ('Shibaura Institute of Technology', 'track限定規定；本附件未列全部申請文件。'),
    ]:
        partner = next(p for p in fetch_ncu_partner_universities() if english.casefold() in p.school_name.casefold())
        workflow = client.get('/application-workflow', params={
            'home_school': 'NCU', 'school': partner.school_name, 'academic_year': '116',
        }).json()
        initial = next(s for s in workflow['steps'] if s['rule_id'].endswith('-host-apply'))
        assert note in '\n'.join(initial['details'])


def test_omu_originals_optional_rows_old_sheet_isolation_and_outage_provenance():
    from exchange_info.ncu_source_coverage import indexable_source_text
    sources = {s['id']: s for s in json.loads(gzip.decompress((BUNDLE / 'source-evidence.json.gz').read_bytes()))}
    for ident in ['host-science-tiec-form1', 'host-science-tiec-form3']:
        form = sources[ident]
        assert form['source_excerpt_only'] and not form['content_status']['all_pages_read']
        assert form['excerpt_original_scope']['sheet_count'] == 2
        assert len(form['excerpt_original_scope']['sheets_reviewed']) == 1
    for official, copy in [('host-omu-form-8', '10cGEuPHH8cAUUOVXLpymWpIPpRNeWvso'), ('host-omu-form-1', '1zGwlUemomIiix-oI9B4d11Kj_sdO-QjN')]:
        assert sources[official]['sha256'] == sources[copy]['sha256']
        assert len(sources[official]['pages']) == 4 and sources[official]['content_status']['all_pages_read']
    checklist = sources['host-omu-form-5']
    assert checklist['content_status']['all_pages_read'] and checklist['content_status']['visual_reviewed_page_count'] == 1
    assert 'Please submit if you have one' in checklist['pages'][0]['text']
    assert 'Please do NOT convert Word or Excel' in checklist['pages'][0]['text']
    assert len(checklist['visual_review']['artifacts']) == 1
    blank = sources['host-omu-form-2']
    assert blank['source_excerpt_only'] and not blank['content_status']['all_pages_have_text']
    assert len(blank['pages']) == 1 and blank['pages'][0]['sheet'] == 'xl/worksheets/sheet1.xml'
    assert blank['reading_review']['original_sheet_count'] == 3
    text = '\n'.join(p['text'] for p in blank['pages'])
    assert 'OSAKA' not in text and 'xxxx@xxx.ac.jp' not in text and '37,800' not in text
    assert '37800' in blank['privacy_note'] and '37,800' not in indexable_source_text(blank)
    ja = sources['host-omu-form-9']
    assert len(ja['pages']) == 2 and ja['content_status']['all_pages_read']
    assert all(p['page'] is None and p['sheet'] for p in ja['pages'])
    course = sources['host-omu-course-list2026']
    assert course['content_status']['all_pages_read'] and len(course['pages']) == 1
    assert '2026' in course['pages'][0]['text'] and '文学部専門科目' in course['pages'][0]['text']
    assert '文学部専門科目' not in indexable_source_text(course)
    old = sources['18V9vNjSgs4HCh9YSLlzmQYs_qXvLn9yK']
    assert old['reading_review']['pages_reviewed'] == [1, 2, 3] and not old['content_status']['all_pages_read']
    assert 'by April 10, 2025' not in indexable_source_text(old)
    for sid in ['host-omu-exchangeprogram', 'host-omu-i-wing', 'host-omu-housing-index', 'host-omu-campus-access', 'host-omu-graduate-timetable']:
        outage = sources[sid]
        assert outage['status'] == 200 and outage['final_url'] == 'https://www.omu.moe'
        assert outage['content_status']['response_bytes_received'] and not outage['content_status']['downloaded']
        assert not outage['content_status']['any_text'] and not outage['content_status']['all_pages_read']
        assert '公式ウェブサイトが復旧' in outage['pages'][0]['text']
    assert sources['host-omu-syllabus-search']['status'] == 503
    assert not sources['host-omu-temporary-course-catalog']['content_status']['any_text']
    assert sources['test-jlpt-japanese-cefr-reference']['authority_kind'] == 'official_language_test_provider'
    assert sources['government-sakai-nhi-current-card']['authority_kind'] == 'government'
    assert sources['host-omu-i-dorm-provider']['authority_kind'] == 'official_housing_provider'
    assert sources['host-chiba-outline2026-cau']['authority_kind'] == 'official_other_home_university'
    assert sources['government-chiba-city-nhi2026-card']['authority_kind'] == 'government'


def test_niigata_iec_grad_finance_and_initial_coe_reach_real_api(tmp_path):
    partner = next(p for p in fetch_ncu_partner_universities() if 'Niigata' in p.school_name)
    assert partner.quota is None and partner.degree_levels is None
    client = TestClient(create_app(tmp_path))
    response = client.get('/application-workflow', params={
        'home_school': 'NCU', 'school': partner.school_name, 'academic_year': '116',
    })
    assert response.status_code == 200
    workflow = response.json(); steps = {s['rule_id']: s for s in workflow['steps']}
    assert len(steps['ncu-116-1-home-3']['document_requirements']) == 7
    assert not steps['ncu-131-host-apply']['document_requirements']
    iec = steps['ncu-131-host-iec-original-application']
    assert len(iec['document_requirements']) == 6
    assert all(d['copies'] == 1 for d in iec['document_requirements'])
    assert any('COE' in d['name'] and '初次' in d['name'] for d in iec['document_requirements'])
    health = next(d for d in iec['document_requirements'] if '胸部X光' in d['name'])
    assert health['signatures'] == ['檢查醫師'] and '半年' in health['name']
    grad = steps['ncu-131-host-graduate-basic-info']
    assert len(grad['document_requirements']) == 1 and '非入學申請書' in grad['document_requirements'][0]['name']
    assert '只交此表' in grad['summary']
    assert len(steps['ncu-131-host-iec-self-finance']['document_requirements']) == 1
    assert len(steps['ncu-131-host-iec-sponsor-finance']['document_requirements']) == 4
    mother = steps['ncu-131-host-mother-iec-nomination']['document_requirements'][0]
    assert '簽名或公印擇一' in mother['name'] and not mother['signatures'] and not mother['stamps']
    assert '網站成功不用此表' in steps['ncu-131-host-iec-web-failure']['summary']
    assert '電子COE' in steps['ncu-131-host-after-acceptance-travel']['summary']
    assert workflow['review_status'] == 'pending_review' and workflow['published_at'] is None
    assert not any(s['deadline_reminder_eligible'] for s in workflow['steps'])
    catalog = client.get('/application-center/catalog', params={
        'school': 'NCU', 'target_school': partner.school_name, 'academic_year': '116',
        'host_admission_status': 'accepted', 'housing_choice': 'off_campus',
    }).json()
    conditional = [d for d in catalog['items'] if d['applicability']]
    assert len(conditional) == 19
    assert all(d['applicability']['status'] == 'needs_confirmation' for d in conditional)
    assert all(d['needs_confirmation'] and not d['download_available'] for d in conditional)
    audit = ncu_field_audit(partner.school_name)
    assert '不是一般GPA2.3' in audit['fields']['eligibility']['note']
    assert '不能推固定5/10' in audit['fields']['host_deadline']['note']
    assert '2028閏日' in audit['fields']['study_period']['note']
    assert '臺灣國籍不是所列對象' in audit['fields']['host_documents']['note']
    assert '2027/1/4' in audit['fields']['host_documents']['note']
    assert '家屬' in audit['fields']['housing']['note'] and '不能覆蓋2027春IEC' in audit['fields']['housing']['note']
    summary = json.dumps(partner.student_summary_zh.model_dump(mode='json'), ensure_ascii=False)
    assert '89000' in summary and '67500' in summary and 'to be announced' in summary
    assert 'login' not in audit['fields']['transport']['note']


def test_niigata_original_sheet_scope_blank_forms_and_year_isolation():
    from exchange_info.ncu_source_coverage import indexable_source_text
    sources = {s['id']: s for s in json.loads(gzip.decompress((BUNDLE / 'source-evidence.json.gz').read_bytes()))}
    blank = sources['host-niigata-application2027']
    assert blank['source_excerpt_only'] and not blank['content_status']['all_pages_read']
    assert blank['excerpt_original_scope']['sheet_count'] == 4
    assert len(blank['excerpt_original_scope']['sheets_reviewed']) == 3
    assert len(blank['pages']) == 1 and '2027年度春期' in blank['pages'][0]['text']
    assert '6th year / 6年ネン' not in blank['pages'][0]['text']
    mother = sources['host-niigata-recommendation2027']
    assert mother['content_status']['all_pages_read']
    assert 'NIIGATA Taro' not in mother['pages'][0]['text'] and 'IKARASHI Jiro' not in mother['pages'][0]['text']
    assert 'Signature or' in mother['pages'][0]['text']
    assert len(sources['host-niigata-coe-blank']['pages']) == 3
    assert sources['host-niigata-coe-blank']['content_status']['all_pages_read']
    calendar = sources['host-niigata-calendar2027']
    assert calendar['content_status']['all_pages_read'] and calendar['content_status']['visual_reviewed_page_count'] == 1
    gate = sources['host-niigata-guidebook-gate']
    assert gate['status'] == 401 and gate['error'] and not gate['content_status']['all_pages_read']
    for ident in ['host-niigata-foreign-courses2026', 'host-niigata-spring-courses2026', 'host-niigata-fall-courses2026-guideurl']:
        source = sources[ident]
        assert len(source['pages']) == 3 and source['content_status']['all_pages_read']
        assert '2026' in source['pages'][0]['text'] and 'Courses' not in indexable_source_text(source)
    jpets = sources['host-niigata-government-jpets']
    assert jpets['authority_kind'] == 'government' and not jpets['content_status']['all_pages_read']
    assert 'January 4, 2027' in jpets['pages'][0]['text']
    old = sources['1DsvER9HIqXMnQZ0ukT0cGFQwKqWHiBw2']
    assert 'Fall) Semester of 2026 (beginning October of 2025)' in old['pages'][0]['text']
    assert 'November 10, 2024' not in indexable_source_text(old)


def test_ncu_runtime_preserves_all_explicit_document_unknowns_and_alternatives():
    from exchange_info.models import UniversityApplicationWorkflow
    raw = [UniversityApplicationWorkflow.model_validate(json.loads(line))
           for line in (BUNDLE / 'application_workflows.jsonl').read_text().splitlines()]
    runtime = {w.school_name: w for w in storage.load_bundled_application_workflows()
               if w.home_university == '國立中央大學'}
    for workflow in raw:
        actual_steps = {step.rule_id: step for step in runtime[workflow.school_name].steps}
        for step in workflow.steps:
            actual = actual_steps[step.rule_id]
            assert actual.submission.method == step.submission.method
            assert actual.scope.application_rounds == step.scope.application_rounds
            assert len(actual.document_requirements) == len(step.document_requirements)
            for source, document in zip(step.document_requirements, actual.document_requirements):
                for key in ['name', 'copies', 'copy_type', 'signatures', 'stamps', 'official_form_url']:
                    assert getattr(document, key) == getattr(source, key), (workflow.school_name, source.name, key)
