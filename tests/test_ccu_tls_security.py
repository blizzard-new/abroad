"""Normal-TLS source boundaries and failure paths remain independently auditable."""

import hashlib
import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest
import requests

from exchange_info.ccu_sources import require_usable_source, source_security_record

ROOT = Path(__file__).resolve().parents[1]
B = ROOT / "src/exchange_info/official_data/ccu"


def read(name):
    return json.loads((B / name).read_text())


def collector():
    spec = importlib.util.spec_from_file_location("ccu_normal_tls_collector", ROOT / "scripts/revalidate_ccu_public_sources.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_removed_browser_bypass_option_is_rejected_before_any_acquisition(tmp_path):
    result = subprocess.run([sys.executable, str(ROOT / "scripts/fetch_ccu_public_renders.py"),
                             "--output", str(tmp_path), "--diagnostic-ignore-https-errors"],
                            text=True, capture_output=True, check=False)
    assert result.returncode == 2
    assert "unrecognized arguments" in result.stderr
    assert not list(tmp_path.iterdir())


def test_certificate_failure_has_one_verified_attempt_and_no_fallback(tmp_path, monkeypatch):
    module = collector()
    calls = []

    def fail(url, **kwargs):
        calls.append((url, kwargs))
        raise requests.exceptions.SSLError("certificate verify failed")

    monkeypatch.setattr(module.requests, "get", fail)
    with pytest.raises(requests.exceptions.SSLError):
        module.fetch("https://www.mapua.edu.ph/", tmp_path, "failure")
    assert calls == [("https://www.mapua.edu.ph/", {"timeout": 45, "verify": True})]
    receipt = json.loads((tmp_path / "failure-http-proof.json").read_text())
    assert receipt["tls_verify"] and receipt["https_certificate_errors_ignored"] is False
    assert "certificate verify failed" in receipt["error"]
    assert not (tmp_path / "failure.html").exists()


def test_historical_insecure_sources_are_restricted_without_rewriting_raw_records():
    impact = read("tls-source-impact.json")
    blocked = [sid for sid, r in impact["historical_sources"].items() if not r["current_use_allowed"]]
    assert len(blocked) == 9
    for sid in blocked:
        raw = read("overseas_sources/" + sid + ".json")
        with pytest.raises(ValueError, match="Historical insecure"):
            require_usable_source(raw)
        effective = source_security_record(raw)
        assert effective["content_applicability"] == "needs_confirmation"
        assert effective["historical_content_applicability"] == raw["content_applicability"]
        assert effective["acquisition_method"] == raw["acquisition_method"]
    require_usable_source(read("overseas_sources/p83-r26-international-handbook.json"))
    for path, digest in impact["historical_raw_file_sha256"].items():
        assert hashlib.sha256((ROOT / path).read_bytes()).hexdigest() == digest


def test_active_field_and_document_evidence_never_uses_the_nine_restricted_sources():
    impact = read("tls-source-impact.json")
    blocked = {sid for sid, r in impact["historical_sources"].items() if not r["current_use_allowed"]}
    for name in ["overseas-reviewed-fields.json", "profile-reviewed-fields.json", "partner-document-requirements.json"]:
        for row in read(name):
            fields = row.get("fields", {}).values() if "fields" in row else row["requirements"]
            for field in fields:
                assert all(e["source_id"] not in blocked for e in field["evidence"])
    triage = read("body-review-triage.json")
    rows = [r for school in triage["schools"] for r in school["sources"] if r["source_id"] in blocked]
    assert len(rows) == 9
    assert all(r["body_state"] == "historical_insecure_acquisition_not_current_evidence" and not r["mapped_fields"] for r in rows)


def test_normal_tls_calendar_body_proves_the_exact_current_embedded_image():
    module = collector()
    source = read("overseas_sources/p83-r27-calendar-image-normal-tls.json")
    parent = (B / source["normal_tls_receipt"]["bundled_http_parent"]).read_bytes()
    assert hashlib.sha256(parent).hexdigest() == source["normal_tls_receipt"]["sha256"]
    assert module.calendar_image(parent) == (B / source["bundled_file"]).read_bytes()
    assert source["normal_tls_receipt"]["tls_verify"]
    assert source["normal_tls_receipt"]["https_certificate_errors_ignored"] is False


def test_each_revalidated_source_has_its_own_response_hash_and_semantic_quote():
    ledger = read("twentyseventh-source-review.json")
    assert ledger["new_source_count"] == 11
    assert len(ledger["source_reviews"]) == 12  # Plus the independently fetched historical PDF duplicate.
    for review in ledger["source_reviews"]:
        source = read("overseas_sources/" + review["source_id"] + ".json")
        require_usable_source(source)
        if review["disposition"] == "duplicate_mapped_body":
            fresh = read("overseas_sources/" + review["matched_mapped_sources"][0] + ".json")
            assert source["sha256"] == fresh["sha256"]
            assert source["text_pages"] == fresh["text_pages"]
            receipt = fresh["normal_tls_receipt"]
        else:
            receipt = source["normal_tls_receipt"]
        assert receipt["tls_verify"] and receipt["http_status"] == 200
        assert receipt["https_certificate_errors_ignored"] is False
        assert hashlib.sha256((B / source["bundled_file"]).read_bytes()).hexdigest() == review["sha256"]
        for quote in review["body_evidence"]:
            body = " ".join(" ".join(source["text_pages"][p - 1] for p in quote["source_pages"]).split())
            assert " ".join(quote["excerpt"].split()) in body


def test_public_form_metadata_and_rendered_questions_keep_separate_verification():
    module = collector()
    source = read("overseas_sources/p119-r27-form-metadata-normal-tls.json")
    raw = (B / source["bundled_file"]).read_bytes()
    form = json.loads(raw)
    assert len(form["questions"]) == 48
    assert form["runtimeResponses"] is form["predefinedResponses"] is None
    assert form["title"] == "Uninter Inbound Exchange Application Form - Autumn 2026 / Spring 2027"
    assert module.question_metadata(raw) == source["text_pages"]
    assert any(q["required"] is False for q in form["questions"])
    assert not read("tls-source-impact.json")["uninter_current_rendered_question_count_verified"]
    assert "渲染/分支" in source["content_review_note"]
    form["runtimeResponses"] = [{"unexpected": "student response"}]
    with pytest.raises(ValueError, match="response data"):
        module.question_metadata(json.dumps(form).encode())
