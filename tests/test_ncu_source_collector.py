"""An old Word conversion can only be reused for the reviewed original bytes."""

import hashlib
import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace

import pytest


@pytest.mark.parametrize("changed", [False, True])
@pytest.mark.parametrize("old_excel", [False, True])
def test_old_office_conversion_is_bound_to_original_bytes(tmp_path, monkeypatch, changed, old_excel):
    path = Path(__file__).parents[1] / "scripts/collect_ncu_host_web.py"
    spec = importlib.util.spec_from_file_location("ncu_host_collector_test", path)
    collector = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(collector)
    original = bytes.fromhex("d0cf11e0a1b11ae1") + b"reviewed-ole-original"
    conversion = {
        "source_sha256": hashlib.sha256(original).hexdigest(),
        "converted_sha256": "reviewed-converted-document",
        "method": "LibreOffice DOCX XML extraction",
        "pages": [{"page": None, "text": "Applicant handwritten signature"}],
    }
    (tmp_path / "old-form-conversion.json").write_text(json.dumps(conversion))
    monkeypatch.setattr(collector, "OUT", tmp_path)
    response = SimpleNamespace(
        status_code=200,
        ok=True,
        content=original + (b"changed" if changed else b""),
        url="https://example.edu/old-form.doc",
        headers={"content-type": "application/msword"},
        raise_for_status=lambda: None,
    )
    monkeypatch.setattr(collector.requests, "get", lambda *a, **k: response)
    monkeypatch.setattr(
        collector.subprocess, "run", lambda *a, **k: SimpleNamespace(returncode=1)
    )
    result = collector.fetch({"id": "old-form", "title": "Old blank form", "url": response.url, "expected_document_format": "xls" if old_excel else "doc"})
    if changed:
        assert "原件已變更" in result["error"]
        assert result["pages"] == [] and "conversion_review" not in result
    else:
        assert "error" not in result
        assert result["pages"] == conversion["pages"]
        assert result["sha256"] == conversion["source_sha256"]
        assert result["document_format"] == ("xls_converted_xlsx_no_pdf_pages" if old_excel else "doc_converted_docx_no_fixed_pdf_pages")
        assert result["extraction_attempts"] == ([] if old_excel else [{"method": "antiword", "status": "failed", "returncode": 1}])


def test_spreadsheet_reading_requires_each_sheet_and_matching_original_sha():
    from exchange_info.ncu_source_coverage import source_content_status

    source = {
        "sha256": "original-sha",
        "status": 200,
        "pages": [{"page": None, "sheet": "sheet1", "text": "Blank nomination form"}, {"page": None, "sheet": "sheet2", "text": ""}],
        "reading_review": {"source_sha256": "original-sha", "pages_reviewed": [None]},
    }
    assert not source_content_status(source)["all_pages_read"]
    source["reading_review"]["sheets_reviewed"] = ["sheet1"]
    assert not source_content_status(source)["all_pages_read"]
    source["reading_review"]["sheets_reviewed"] = ["sheet1", "sheet2"]
    assert source_content_status(source)["all_pages_read"]
    assert not source_content_status(source)["all_pages_have_text"]
    source["sha256"] = "changed-original"
    assert not source_content_status(source)["all_pages_read"]
