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
