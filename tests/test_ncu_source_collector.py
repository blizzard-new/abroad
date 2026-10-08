"""An old Word conversion can only be reused for the reviewed original bytes."""

import hashlib
import importlib.util
import json
import io
import zipfile
from pathlib import Path
from types import SimpleNamespace

import pytest


@pytest.mark.parametrize("changed", [False, True])
def test_public_partner_json_excerpt_is_validated_and_bound_to_original_bytes(tmp_path, monkeypatch, changed):
    path = Path(__file__).parents[1] / "scripts/collect_ncu_host_web.py"
    spec = importlib.util.spec_from_file_location("ncu_partner_json_collector_test", path)
    collector = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(collector)
    original = b'[{"name":"National Central University","exchange03":"t"}]'
    pages = [{"page": None, "text": original.decode()}]
    (tmp_path / "partner-data-public-excerpt.json").write_text(json.dumps({
        "source_sha256": hashlib.sha256(original).hexdigest(),
        "public_pages": pages,
        "note_zh": "Only the identified partner row is reviewed; no quota inferred.",
    }))
    monkeypatch.setattr(collector, "OUT", tmp_path)
    response = SimpleNamespace(status_code=200, ok=True,
        content=original + (b" " if changed else b""),
        url="https://example.edu/resultlist.json", headers={"content-type": "application/json"},
        raise_for_status=lambda: None)
    monkeypatch.setattr(collector.requests, "get", lambda *a, **k: response)
    result = collector.fetch({"id": "partner-data", "title": "Public partner data", "url": response.url,
        "expected_document_format": "json", "requires_public_field_excerpt": True})
    if changed:
        assert "原件已變更" in result["error"] and result["pages"] == []
    else:
        assert "error" not in result and result["source_excerpt_only"]
        assert result["pages"] == pages and result["document_format"] == "json_no_pdf_pages"


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


def test_rebuild_public_excerpt_cannot_reintroduce_full_example_or_reuse_changed_sha():
    from exchange_info.ncu_source_coverage import attach_public_field_excerpt
    public_pages = [{"page": None, "sheet": "sheet1", "text": "Name | Permit | Email"}, {"page": None, "sheet": "sheet2", "text": ""}]
    excerpt = {"source_sha256": "same-sha", "public_field_excerpt": public_pages[0]["text"], "public_pages": public_pages, "note_zh": "空白欄位、兩工作表；不複製示例"}
    source = {"sha256": "same-sha", "pages": [{"page": None, "text": "filled-example-private-data"}]}
    attach_public_field_excerpt(source, excerpt)
    assert source["pages"] == public_pages and source["source_excerpt_only"]
    assert "filled-example-private-data" not in str(source)
    source = {"sha256": "changed-sha", "pages": [{"page": None, "text": "changed-private-example"}]}
    attach_public_field_excerpt(source, excerpt)
    assert source["pages"] == [] and "原件已變更" in source["error"]
    failed = {"sha256": "same-sha", "error": "not the requested original", "pages": [{"page": None, "text": "response-body"}]}
    attach_public_field_excerpt(failed, excerpt)
    assert failed["pages"] == [] and failed["error"] == "not the requested original"


def test_presentation_uses_manifest_order_and_requires_each_slide_to_be_read(monkeypatch):
    path = Path(__file__).parents[1] / "scripts/collect_ncu_host_web.py"
    spec = importlib.util.spec_from_file_location("ncu_presentation_collector", path)
    collector = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(collector)
    data = io.BytesIO()
    with zipfile.ZipFile(data, "w") as archive:
        archive.writestr("ppt/presentation.xml", '<p:presentation xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><p:sldIdLst><p:sldId r:id="first"/><p:sldId r:id="second"/></p:sldIdLst></p:presentation>')
        archive.writestr("ppt/_rels/presentation.xml.rels", '<Relationships><Relationship Id="first" Target="slides/slide12.xml"/><Relationship Id="second" Target="slides/slide2.xml"/></Relationships>')
        for name, text in (("slide12", "2026-27 cover"), ("slide2", "Six application documents")):
            archive.writestr(f"ppt/slides/{name}.xml", f'<a:root xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"><a:t>{text}</a:t></a:root>')
    response = SimpleNamespace(status_code=200,ok=True,content=data.getvalue(),url="https://example.edu/guide.pptx",headers={"content-type":"application/vnd.openxmlformats-officedocument.presentationml.presentation"},raise_for_status=lambda:None)
    monkeypatch.setattr(collector.requests,"get",lambda *a,**k:response)
    result = collector.fetch({"id":"slides","title":"Guide","url":response.url})
    assert "error" not in result and result["document_format"] == "pptx_slides_no_pdf_pages"
    assert [p["text"] for p in result["pages"]] == ["2026-27 cover","Six application documents"]
    assert [p["slide"] for p in result["pages"]] == [1,2] and all(p["page"] is None for p in result["pages"])
    from exchange_info.ncu_source_coverage import source_content_status, indexable_source_text
    result["reading_review"]={"source_sha256":result["sha256"],"pages_reviewed":[None],"slides_reviewed":[1]}
    assert not source_content_status(result)["all_pages_read"]
    result["reading_review"]["slides_reviewed"]=[1,2]
    assert source_content_status(result)["all_pages_read"]
    assert "投影片2／無PDF頁碼" in indexable_source_text(result)
    result["sha256"]="changed-original"
    assert not source_content_status(result)["all_pages_read"]


@pytest.mark.parametrize("changed", [False,True])
def test_rtf_named_doc_conversion_is_bound_to_original_bytes(tmp_path,monkeypatch,changed):
    path=Path(__file__).parents[1]/"scripts/collect_ncu_host_web.py"
    spec=importlib.util.spec_from_file_location("ncu_rtf_collector",path)
    collector=importlib.util.module_from_spec(spec);spec.loader.exec_module(collector)
    original=b"{\\rtf1 reviewed blank health form}"
    conversion={"source_sha256":hashlib.sha256(original).hexdigest(),"converted_sha256":"converted-sha","pages":[{"page":None,"text":"Reciprocal exemption needs confirmation"}]}
    (tmp_path/"health-conversion.json").write_text(json.dumps(conversion))
    monkeypatch.setattr(collector,"OUT",tmp_path)
    response=SimpleNamespace(status_code=200,ok=True,content=original+(b"changed"if changed else b""),url="https://example.edu/health.doc",headers={"content-type":"application/octet-stream"},raise_for_status=lambda:None)
    monkeypatch.setattr(collector.requests,"get",lambda *a,**k:response)
    result=collector.fetch({"id":"health","title":"Blank health form","url":response.url})
    if changed:
        assert "RTF原件已變更" in result["error"] and result["pages"]==[]
    else:
        assert "error" not in result and result["pages"]==conversion["pages"]
        assert result["document_format"]=="rtf_converted_docx_no_fixed_pdf_pages"


def test_ncu_jsonl_serialization_preserves_source_line_separators(tmp_path):
    from exchange_info.models import ProcessedPage
    path = Path(__file__).parents[1]/'scripts/build_ncu_catalog.py'
    spec = importlib.util.spec_from_file_location('ncu_jsonl_writer_test',path)
    builder = importlib.util.module_from_spec(spec);spec.loader.exec_module(builder)
    text = '原文\u0085下一段\u2028不同換行\u2029結尾\n原PDF文字'
    root = Path(__file__).parents[1]
    row = (root/'src/exchange_info/official_data/ncu/pages.jsonl').read_text().splitlines()[0]
    source = ProcessedPage.model_validate_json(row).model_copy(update={'text':text})
    target = tmp_path/'pages.jsonl'
    builder.write_rows(target,[source.model_dump(mode='json')],ProcessedPage)
    rows = target.read_text().splitlines()
    assert len(rows) == 1
    assert ProcessedPage.model_validate_json(rows[0]).text == text


@pytest.mark.parametrize('changed', [False, True])
def test_native_xls_snapshot_does_not_reuse_different_original(tmp_path, monkeypatch, changed):
    path = Path(__file__).parents[1] / 'scripts/collect_ncu_host_web.py'
    spec = importlib.util.spec_from_file_location('ncu_native_xls_collector', path)
    collector = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(collector)
    original = bytes.fromhex('d0cf11e0a1b11ae1') + b'original-biff-workbook'
    pages = [{'page': None, 'sheet': '25-26学年第一学期', 'text': 'Course | Campus | Language'}]
    (tmp_path / 'courses-native-xls.json').write_text(json.dumps({'source_sha256': hashlib.sha256(original).hexdigest(), 'method': 'xlrd original BIFF extraction', 'pages': pages}))
    monkeypatch.setattr(collector, 'OUT', tmp_path)
    response = SimpleNamespace(status_code=200,ok=True,content=original+(b'changed' if changed else b''),url='https://example.edu/courses.xls',headers={'content-type':'application/octet-stream'},raise_for_status=lambda:None)
    monkeypatch.setattr(collector.requests,'get',lambda *a,**k:response)
    result=collector.fetch({'id':'courses','title':'Historical workbook','url':response.url,'expected_document_format':'xls'})
    if changed:
        assert result['pages'] == [] and 'XLS原件已變更' in result['error']
    else:
        assert 'error' not in result and result['pages'] == pages
        assert result['document_format'] == 'xls_native_sheets_no_pdf_pages'
        assert not result.get('conversion_review')


def test_image_reading_is_separate_from_html_text_and_changed_sha():
    from exchange_info.ncu_source_coverage import source_content_status,indexable_source_text
    source={'status':200,'sha256':'image-original','pages':[{'page':None,'image':1,'text':'Selected table rows'}], 'source_excerpt_only':True,'reading_review':{'source_sha256':'image-original','pages_reviewed':[None]}}
    assert not source_content_status(source)['all_pages_read']
    source['visual_review']={'source_sha256':'image-original','images_reviewed':[1],'ocr_status':'not_performed'}
    status=source_content_status(source)
    assert status['all_pages_read'] and status['visual_reviewed_image_count']==1
    assert status['visual_reviewed_page_count']==0 and not status['all_pages_have_text']
    assert '原文圖片1／無PDF頁碼' in indexable_source_text(source)
    source['sha256']='different-image'
    assert not source_content_status(source)['all_pages_read']
    assert source_content_status(source)['visual_reviewed_image_count']==0
