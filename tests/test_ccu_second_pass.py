"""Use real bundled rows to protect cross-source deadlines and research status."""

import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess

import pytest
import requests
from pypdf import PdfReader

from exchange_info.ccu_sources import BUNDLE
from exchange_info.ccu_student_view import fetch_ccu_partner_universities
from exchange_info.models import UniversityApplicationWorkflow
from exchange_info.storage import read_jsonl


def at(page):
    return next(
        p for p in fetch_ccu_partner_universities() if p.source_pages[0] == page
    )


@pytest.mark.parametrize("page", [27, 67, 73, 86, 114])
def test_real_deadline_conflict_reaches_all_student_projections(page):
    partner = at(page)
    field = partner.partner_exchange_details["application_deadline"]
    assert field.status == "conflict" and len(field.evidence) >= 2
    assert partner.partner_application_deadline == field.value
    assert partner.student_summary_zh.application_deadline == field.value
    assert partner.field_evidence["partner_application_deadline"].status == "conflict"
    assert partner.reference_data["partner_application_deadline"]
    flow = next(
        f
        for f in read_jsonl(
            BUNDLE / "application_workflows.jsonl", UniversityApplicationWorkflow
        )
        if f.school_name == partner.school_name
    )
    assert field.value in flow.steps[4].timing
    assert (
        flow.steps[4].deadline_at is None
        and not flow.steps[4].deadline_reminder_eligible
    )
    script = r"""
    const assert=require('node:assert/strict'),fs=require('node:fs');
    const partnerStudentSummary=i=>i.student_summary_zh||{};
    eval(fs.readFileSync('src/exchange_info/static/app.js','utf8').match(/^function partnerDeadlineReference\([^]*?^}/m)[0]);
    const item=JSON.parse(fs.readFileSync(0,'utf8'));
    assert.ok(partnerDeadlineReference(item).value.includes('來源矛盾'));
    assert.ok(partnerDeadlineReference(item).value.includes(item.partner_exchange_details.application_deadline.value));
    """
    result = subprocess.run(
        ["node", "-e", script],
        input=partner.model_dump_json(),
        text=True,
        capture_output=True,
    )
    assert result.returncode == 0, result.stderr
    if page == 67:
        assert "2026/10/15" in partner.reference_data["partner_application_deadline"]
        assert "10" in field.value and "01" in field.value
        nomination = partner.partner_exchange_details["nomination_deadline"]
        assert nomination.status == "verified_current" and "09" in nomination.value


def test_acquired_forms_and_approximate_arrival_are_mapped():
    pusan = at(43).partner_exchange_details["application_forms"]
    assert pusan.status == "verified_current"
    assert {14, 15}.issubset({p for e in pusan.evidence for p in e.source_pages})
    file = BUNDLE / "partner_forms/p43-factsheet-with-forms-2026-2027.pdf"
    reader = PdfReader(file)
    assert "STUDY PLAN" in reader.pages[13].extract_text()
    assert "Signature" in reader.pages[14].extract_text()
    assert "family relationship document" in reader.pages[14].extract_text()
    arrival = at(67).partner_exchange_details["arrival"]
    assert (
        arrival.status == "verified_current"
        and "下旬" in arrival.value
        and "確切日期" in arrival.value
    )
    form = json.loads((BUNDLE / "overseas_sources/p114-r2-form.json").read_text())
    assert (
        hashlib.sha256((BUNDLE / form["bundled_file"]).read_bytes()).hexdigest()
        == form["sha256"]
    )
    assert (
        "20__/20__" in form["text_pages"][0]
        and "November 15th" in form["text_pages"][0]
    )
    assert (
        at(114).partner_exchange_details["application_forms"].status
        == "verified_current"
    )
    assert at(114).partner_exchange_details["insurance"].status == "needs_confirmation"
    assert (
        at(100).partner_exchange_details["academic_calendar"].status
        == "verified_current"
    )
    assert at(26).partner_exchange_details["visa"].status == "needs_confirmation"
    assert at(39).partner_exchange_details["documents"].status == "reference_only"


def test_each_gap_has_real_acquisition_checks_without_inventing_nonpublication():
    audit = json.loads((BUNDLE / "research-gap-audit.json").read_text())
    assert audit["school_count"] == 55 and audit["field_count"] == 935
    assert sum(audit["category_counts"].values()) == 935
    for row in audit["schools"]:
        for field in row["fields"].values():
            assert field["source_checks"]
            for check in field["source_checks"]:
                source = json.loads(
                    (
                        BUNDLE / "overseas_sources" / f"{check['source_id']}.json"
                    ).read_text()
                )
                assert check["source_url"] == source["source_url"]
                assert check["checked_at"] == source["checked_at"] and check["result"]
            if field["category"] == "official_not_announced":
                assert (
                    row["ccu_page"] == 47
                    and field["status"] == "explicit_not_announced"
                )
    followup = json.loads((BUNDLE / "source-failure-followup.json").read_text())
    assert followup["original_failed_source_count"] == len(followup["sources"])
    retried = [x for x in followup["sources"] if x["retry"]]
    assert len(retried) == 14
    for item in followup["sources"]:
        source = json.loads(
            (
                BUNDLE / "overseas_sources" / (item["original"]["source_id"] + ".json")
            ).read_text()
        )
        assert source["status"] == "fetch_failed"
        if not item["retry"]:
            assert "尚無同入口重試" in item["conclusion"]
    assert len([x for x in retried if "失敗" not in x["retry"]["result"]]) == 1


def test_fetcher_keeps_legacy_word_binary_and_relative_official_links(tmp_path):
    spec = importlib.util.spec_from_file_location(
        "ccu_fetch", "scripts/fetch_ccu_overseas_sources.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    class Session:
        def __init__(self, body):
            self.body = body

        def get(self, url, **kwargs):
            response = requests.Response()
            response.url = url
            response.status_code = 200
            response._content = self.body
            return response

    item = dict(
        url="https://official.example.edu/Admission/index.htm",
        source_id="test",
        authority="partner_official_public_page",
    )
    raw = b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1" + b"not html"
    doc = module.fetch_public_source(item, tmp_path, Session(raw))
    assert doc["status"] == "downloaded_doc_unextracted" and doc["text_pages"] == []
    assert (tmp_path / "test.doc").read_bytes() == raw
    page = module.fetch_public_source(
        item,
        tmp_path,
        Session(
            b'<a href="../form.doc">Form</a><a href="mailto:office@example.edu">Email</a>'
        ),
    )
    assert page["links"] == [
        dict(label="Form", url="https://official.example.edu/form.doc")
    ]
