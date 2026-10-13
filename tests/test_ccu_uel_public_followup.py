"""Year-stamped cells, undated policies, actual login and visually reviewed glyphs."""
import csv
import gzip
import hashlib
import json

from bs4 import BeautifulSoup
from pypdf import PdfReader

from exchange_info.ccu_sources import BUNDLE
from exchange_info.ccu_student_view import fetch_ccu_partner_universities


def fields():
    partner = next(p for p in fetch_ccu_partner_universities() if p.source_pages[0] == 66)
    assert partner.availability_status == "not_open"
    assert partner.language_requirement is None and partner.quota is None
    assert partner.application_window_status == "closed"
    return json.loads(partner.reference_data["ccu_completion"])["reference_host_fields"]


def read(name):
    return json.loads((BUNDLE / name).read_text())


def body(record):
    path = BUNDLE / record["bundled_file"]
    b = path.read_bytes()
    return gzip.decompress(b) if path.suffix == ".gz" else b


def test_uel_language_keeps_visual_glyphs_and_undated_vs_historical_scope():
    language = fields()["language"]
    assert language["status"] == "needs_confirmation"
    assert "IELTS ≥6.0" in language["value"] and "TOEIC ≥650" in language["value"]
    assert "IELTS ≥5.0" in language["value"] and "2023–2024" in language["value"]
    ev = next(e for e in language["evidence"] if e["source_id"] == "p66-official-factsheet-pdf" and "visual_review_file" in e)
    assert "≥" in ev["excerpt"] and ">" in ev["extracted_excerpt"]
    assert ev["source_pages"] == [1] and "未標學年度" in ev["academic_year"]
    assert hashlib.sha256((BUNDLE / ev["visual_review_file"]).read_bytes()).hexdigest() == ev["visual_review_sha256"]
    record = read("completion_sources/p66-official-factsheet-pdf.receipt.json")
    assert hashlib.sha256(body(record)).hexdigest() == record["sha256"]
    reader = PdfReader(BUNDLE / record["bundled_file"])
    assert len(reader.pages) == 4
    assert "IELTS > 6.0" in reader.pages[0].extract_text()  # Lossy extraction remains distinct.


def test_uel_calendar_conflict_comes_from_actual_current_tab_cells():
    record = read("completion_sources/p66-academic-calendar-csv.receipt.json")
    cells = list(csv.reader(body(record).decode().splitlines()))
    assert cells[0][8] == "2026-2027 ACADEMIC CALENDAR"
    assert cells[13][18] == "14/12/2026 - 27/03/2027"
    assert cells[13][26] == "15/03/2026 - 27/03/2027"
    assert cells[15][26] == "05/07/2027 - 24/07/2026"
    calendar = fields()["academic_calendar"]
    assert calendar["status"] == "conflict"
    assert "不替官方改年" in calendar["value"]
    assert calendar["evidence"][0]["source_pages"] == []
    assert "row12/14/16" in calendar["evidence"][0]["source_locator"]


def test_uel_housing_price_units_and_administration_fee_do_not_become_tuition():
    record = read("completion_sources/p66-accommodation-public-text.receipt.json")
    text = body(record).decode()
    assert "Updated to July 2026" in text and "USD 55 to USD 138 per 6 months" in text
    f = fields()
    assert f["housing"]["status"] == f["costs"]["status"] == "conflict"
    assert "monthly" in f["housing"]["value"] and "per6months" in f["housing"]["value"]
    assert "USD150/semester" in f["costs"]["value"]
    assert f["host_tuition"]["status"] == "needs_confirmation"
    assert "沒有新的tuition waiver條文" in f["host_tuition"]["value"]


def test_uel_actual_sign_in_message_does_not_claim_nomination_authorization():
    record = read("completion_sources/p66-official-ctp-application.receipt.json")
    assert record["http_status"] == 401
    assert "You must sign in to access this content" in BeautifulSoup(body(record), "html.parser").get_text(" ", strip=True)
    f = fields()["application_forms"]
    assert f["research_classification"] == "personal_access_required"
    assert "不宣稱只有提名者有權限" in f["value"] and "未讀题目／年度" in f["value"]
    assert all(ev["source_id"] != record["source_id"] for ev in f["evidence"])
    access = f["access_requirement_evidence"][0]
    assert access["source_id"] == record["source_id"]
    assert hashlib.sha256(body(record)).hexdigest() == access["content_hash"]
    audit = next(r for r in read("completion-public-source-screening.json")["sources"]
                 if r["source_id"] == record["source_id"])
    assert audit["decision"] == "used_access_requirement_evidence"
    assert audit["field_statuses"] == ["needs_confirmation"]
    queue = next(r for r in read("completion-followup-gap-research.json")["schools"] if r["ccu_page"] == 66)
    pending = next(r for r in queue["pending_host_policy_reviews"] if r["field"] == "application_forms")
    assert pending["access_requirement_evidence"][0]["content_hash"] == record["sha256"]


def test_uel_undated_deadlines_and_later_stage_documents_stay_separate():
    f = fields()
    assert f["nomination_deadline"]["status"] == f["application_deadline"]["status"] == "needs_confirmation"
    assert "September25" in f["nomination_deadline"]["value"]
    assert "不套舊年或自行推年" in f["application_deadline"]["value"]
    assert "錄取後才發Acceptance Letter" in f["documents"]["value"]
    assert "不混入初申" in f["documents"]["value"]
    assert f["housing_deadline"]["status"] == f["insurance"]["status"] == "missing"
