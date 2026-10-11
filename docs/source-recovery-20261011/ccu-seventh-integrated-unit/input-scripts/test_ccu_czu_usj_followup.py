"""Current term, bilateral paths, actual tables and incomplete personal forms."""
import gzip
import hashlib
import json
from xml.etree import ElementTree as ET
from zipfile import ZipFile

from bs4 import BeautifulSoup
from fastapi.testclient import TestClient

from exchange_info.api import create_app
from exchange_info.ccu_sources import BUNDLE, HOME
from exchange_info.ccu_student_view import fetch_ccu_partner_universities


def at(page):
    return next(p for p in fetch_ccu_partner_universities() if p.source_pages[0] == page)


def fields(page):
    partner = at(page)
    assert partner.availability_status == "not_open"
    assert partner.quota is None and partner.eligibility is None and partner.language_requirement is None
    assert partner.application_window_status == "closed"
    return json.loads(partner.reference_data["ccu_completion"])["reference_host_fields"]


def test_czu_summer_nomination_does_not_invent_a_spring_application_deadline():
    f = fields(112)
    assert f["nomination_deadline"]["status"] == "verified_current"
    assert "2026-10-15" in f["nomination_deadline"]["value"]
    assert "email／EWP均不受理" in f["nomination_deadline"]["value"]
    assert f["application_deadline"]["status"] == "needs_confirmation"
    assert "2026-06-12" in f["application_deadline"]["value"]
    assert "不能直接複用" in f["application_deadline"]["value"]
    assert any("first (winter)" in e["excerpt"] for e in f["application_deadline"]["evidence"])


def test_czu_non_erasmus_form_and_documents_are_separate_from_ola():
    f = fields(112)
    assert f["application_forms"]["status"] == "needs_confirmation"
    assert "non-Erasmus專用" in f["application_forms"]["value"]
    assert "email寄送" in f["application_forms"]["value"]
    assert f["documents"]["status"] == "verified_current"
    assert "Master另附Bachelor成績" in f["documents"]["value"]
    assert "不推定需護照掃描" in f["documents"]["value"]
    assert "不能自行" in f["language"]["value"] and "B2" in f["language"]["value"]


def test_czu_current_calendar_exposes_only_the_officially_unspecified_exam_component():
    f = fields(112)
    calendar = f["academic_calendar"]
    assert calendar["status"] == "needs_confirmation"
    assert "2027-02-01至06-30" in calendar["value"]
    assert "To be specified" in calendar["value"] and "僅該段" in calendar["value"]
    queue = json.loads((BUNDLE / "completion-followup-gap-research.json").read_text())
    row = next(r for r in queue["schools"] if r["ccu_page"] == 112)
    pending = next(f for f in row["pending_host_policy_reviews"] if f["field"] == "academic_calendar")
    assert pending["classification"] == "official_not_announced"
    assert pending["official_not_announced"] and "不把整份" in pending["reason"]
    assert "第二學期" in f["exchange_duration"]["value"]
    assert "2026-12-05" in f["exchange_duration"]["value"]
    assert "不推定Spring2027" in f["exchange_duration"]["value"]


def test_czu_course_rules_do_not_promote_degree_catalogue_or_thesis_admission():
    f = fields(112)
    value = f["course_restrictions"]["value"]
    assert f["course_restrictions"]["status"] == "verified_current"
    for expected in ["最多30ECTS", "主要faculty至少50%", "IVP", "不保證"]:
        assert expected in value
    assert any("at least in the second year of their Bachelor studies" in e["excerpt"]
               for e in fields(112)["eligibility"]["evidence"])
    assert "Erasmus與non-Erasmus" in f["program_scope"]["value"]
    assert f["host_tuition"]["status"] == "missing" and f["host_tuition"]["value"] is None


def test_czu_hloubetin_prices_use_the_dated_column_and_do_not_move_the_campus():
    f = fields(112)
    assert f["costs"]["status"] == "needs_confirmation"
    assert "14700" in f["costs"]["value"] and "10500" in f["costs"]["value"]
    assert "而非總生活費" in f["costs"]["value"] and "2027個人合約費率待核" in f["costs"]["value"]
    receipt = json.loads((BUNDLE / "completion_sources/p112-public-linked-hloubetin.receipt.json").read_text())
    body = (BUNDLE / receipt["bundled_file"]).read_bytes()
    if receipt["bundled_file"].endswith(".gz"):
        body = gzip.decompress(body)
    table = next(t for t in BeautifulSoup(body, "html.parser").find_all("table") if "14,700" in t.get_text())
    cells = [[c.get_text(" ", strip=True) for c in row.find_all("td")] for row in table.find_all("tr")]
    assert cells[0][2] == "From 1 st January, 2026"
    assert cells[1][2] == "14,700 CZK / month" and cells[2][2] == "10,500 CZK / person / month"
    assert "10日內" in f["housing_deadline"]["value"]
    assert "不是CZU全校Spring" in f["housing_deadline"]["value"]
    assert at(112).location.latitude == 50.129976
    assert at(112).location.longitude == 14.373707


def test_usj_recommended_b1_and_conditional_mandatory_b2_are_distinct():
    f = fields(92)
    value = f["language"]["value"]
    for expected in ["recommended B1", "不是全員", "Health Sciences", "Translation", "mandatory", "EnglishB2"]:
        assert expected in value
    assert f["language"]["status"] == "verified_current"
    assert f["nomination_deadline"]["status"] == "verified_current"
    assert "2026-11-15" in f["nomination_deadline"]["value"]
    assert f["application_deadline"]["status"] == "needs_confirmation"
    assert "2026-12-15" in f["application_deadline"]["value"]


def test_usj_spring_resit_conflict_retains_pdf_and_current_web_calendar():
    f = fields(92)
    calendar = f["academic_calendar"]
    assert calendar["status"] == "conflict"
    assert "07-03" in calendar["value"] and "07-02" in calendar["value"]
    assert any(e["source_pages"] == [2] and "3 July" in e["excerpt"] for e in calendar["evidence"])
    assert any(not e["source_pages"] and "2nd of July 2027" in e["excerpt"] for e in calendar["evidence"])
    assert "2027-01-27" in f["arrival"]["value"]


def test_usj_non_european_docx_is_openable_and_unversioned():
    forms = fields(92)["application_forms"]
    assert forms["status"] == "needs_confirmation"
    ev = next(e for e in forms["evidence"] if e.get("bundled_attachment"))
    path = BUNDLE / ev["bundled_attachment"]
    assert path.suffix == ".docx" and hashlib.sha256(path.read_bytes()).hexdigest() == ev["content_hash"]
    with ZipFile(path) as archive:
        text = " ".join(ET.fromstring(archive.read("word/document.xml")).itertext())
    assert "Universidad San Jorge" in text and "Before the mobility" in text
    assert "2026" not in text and "2027" not in text
    assert not ev["source_pages"] and "无年度" in forms["value"]
    assert "不是全部" in fields(92)["documents"]["value"]


def test_qut_sia_scope_and_technical_failures_do_not_require_personal_permissions():
    f = fields(120)
    assert f["housing"]["status"] == "needs_confirmation"
    assert "不把其utilities" in f["housing"]["value"] and "2026-08-14" in f["housing"]["value"]
    queue = json.loads((BUNDLE / "completion-followup-gap-research.json").read_text())
    rows = {r["ccu_page"]: r for r in queue["schools"]}
    form = next(f for f in rows[112]["pending_host_policy_reviews"] if f["field"] == "application_forms")
    assert form["classification"] == "personal_access_required"
    assert any("UIS login credentials" in e["excerpt"] for e in form["evidence"])
    # A promise to send further instructions after nomination does not by itself
    # prove that public forms require a personal authenticated account.
    usj = next(f for f in rows[92]["pending_host_policy_reviews"] if f["field"] == "application_forms")
    assert usj["classification"] == "research_incomplete"
    assert usj["personal_access_required"] is None
    karvina = [a for a in rows[111]["attempted_sources"] if a["source_id"].startswith("p111-public-")]
    assert len(karvina) == 2 and all(a["http_status"] == 200 and a["classification"] == "source_failure" for a in karvina)


def test_real_api_keeps_both_new_receiving_matrices_as_closed_reference_tracks(tmp_path):
    client = TestClient(create_app(tmp_path))
    response = client.get("student-dashboard", params={"school": HOME})
    assert response.status_code == 200
    partners = {p["source_pages"][0]: p for p in response.json()["partner_universities"]}
    for page in [92, 112]:
        p = partners[page]
        assert p["availability_status"] == "not_open" and p["quota"] is None
        assert not p["partner_exchange_details"]
        assert len(json.loads(p["reference_data"]["ccu_completion"])["reference_host_fields"]) == 17
    assert len(partners) == 104
