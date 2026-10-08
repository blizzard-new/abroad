"""Snapshot explicit official host checks; preserve HTTP failures as failures.

Only public pages are read. A 403 is not evidence of a login requirement or an
unannounced programme. Web-page text has no PDF page number.
"""

from pathlib import Path
import posixpath
import concurrent.futures, gzip, hashlib, io, json, zipfile, os, subprocess, tempfile
from xml.etree import ElementTree
from urllib.parse import urlparse
import requests
from bs4 import BeautifulSoup
from pypdf import PdfReader

OUT = Path(__file__).resolve().parents[1] / "sources/ncu/2026-10-08"
SPEC = OUT / "host-web-checks.json"


def fetch(spec):
    url = spec["url"]
    result = {**spec, "label": spec["title"], "checked_at": "2026-10-08", "pages": []}
    try:
        response = requests.get(url, timeout=35)
        if (
            spec.get("expected_document_format") == "pdf"
            and urlparse(url).hostname == "drive.google.com"
            and response.ok
            and not response.content.startswith(b"%PDF")
        ):
            form = BeautifulSoup(response.content, "html.parser").select_one(
                "form#download-form"
            )
            if (
                form
                and urlparse(form.get("action", "")).hostname
                == "drive.usercontent.google.com"
            ):
                response = requests.get(
                    form["action"],
                    params={
                        node["name"]: node.get("value", "")
                        for node in form.select("input[name]")
                    },
                    timeout=35,
                )
        result.update(
            status=response.status_code,
            final_url=response.url,
            sha256=hashlib.sha256(response.content).hexdigest(),
            content_type=response.headers.get("content-type"),
        )
        response.raise_for_status()
        expected_format = spec.get("expected_document_format")
        if expected_format == "pdf" and not response.content.startswith(b"%PDF"):
            raise ValueError("公開下载回應不是PDF原件；不當成文件已取得或登入限定。")
        if expected_format == "docx" and not response.content.startswith(b"PK"):
            raise ValueError("公開下載回應不是Word原件；不當成文件已取得或登入限定。")
        if response.content.startswith(b"%PDF"):
            reader = PdfReader(io.BytesIO(response.content))
            result["pages"] = [
                {"page": i + 1, "text": p.extract_text()}
                for i, p in enumerate(reader.pages)
            ]
        elif response.content.startswith(b"PK"):
            archive = zipfile.ZipFile(io.BytesIO(response.content))
            if "word/document.xml" in archive.namelist():
                root = ElementTree.fromstring(archive.read("word/document.xml"))
                ns = {
                    "w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
                }
                mc = {
                    "mc": "http://schemas.openxmlformats.org/markup-compatibility/2006"
                }
                for alternate in root.findall(".//mc:AlternateContent", mc):
                    for fallback in list(alternate)[1:]:
                        alternate.remove(fallback)
                result["pages"] = [
                    {
                        "page": None,
                        "text": "\n".join(
                            node.text or "" for node in root.findall(".//w:t", ns)
                        ),
                    }
                ]
                result["document_format"] = "docx_no_fixed_pdf_pages"
            elif "xl/workbook.xml" in archive.namelist():
                ns = {"x": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
                strings = []
                if "xl/sharedStrings.xml" in archive.namelist():
                    root = ElementTree.fromstring(archive.read("xl/sharedStrings.xml"))
                    strings = ["".join(x.itertext()) for x in root.findall("x:si", ns)]
                result["pages"] = []
                for name in sorted(archive.namelist()):
                    if not name.startswith("xl/worksheets/sheet") or not name.endswith(
                        ".xml"
                    ):
                        continue
                    root = ElementTree.fromstring(archive.read(name))
                    rows = []
                    for row in root.findall(".//x:row", ns):
                        cells = []
                        for cell in row.findall("x:c", ns):
                            value = cell.find("x:v", ns)
                            raw = (
                                value.text
                                if value is not None
                                else "".join(cell.itertext())
                            )
                            cells.append(
                                strings[int(raw)]
                                if cell.get("t") == "s" and raw
                                else raw or ""
                            )
                        rows.append(" | ".join(cells))
                    result["pages"].append(
                        {"page": None, "sheet": name, "text": "\n".join(rows)}
                    )
                result["document_format"] = "xlsx_sheets_no_pdf_pages"
            elif "ppt/presentation.xml" in archive.namelist():
                ns = {"p": "http://schemas.openxmlformats.org/presentationml/2006/main",
                      "a": "http://schemas.openxmlformats.org/drawingml/2006/main",
                      "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships"}
                relationships = ElementTree.fromstring(archive.read("ppt/_rels/presentation.xml.rels"))
                targets = {node.attrib["Id"]: posixpath.normpath(posixpath.join("ppt", node.attrib["Target"]))
                           for node in relationships if node.attrib.get("TargetMode") != "External"}
                presentation = ElementTree.fromstring(archive.read("ppt/presentation.xml"))
                result["pages"] = []
                for number, node in enumerate(presentation.findall("p:sldIdLst/p:sldId", ns), start=1):
                    part = targets[node.attrib[f"{{{ns['r']}}}id"]]
                    slide = ElementTree.fromstring(archive.read(part))
                    text = "\n".join(p.text or "" for p in slide.findall(".//a:t", ns))
                    result["pages"].append({"page": None, "slide": number, "source_part": part, "text": text})
                result["document_format"] = "pptx_slides_no_pdf_pages"
            else:
                raise ValueError("Unsupported ZIP document; no extracted text")
            result["links"] = []
            if "word/_rels/document.xml.rels" in archive.namelist():
                relationships = ElementTree.fromstring(
                    archive.read("word/_rels/document.xml.rels")
                )
                result["links"] = [
                    {"label": "Word hyperlink", "href": x.attrib["Target"]}
                    for x in relationships
                    if x.attrib.get("TargetMode") == "External"
                ]
        elif response.content.startswith(b"{\\rtf"):
            conversion = json.loads((OUT / f"{spec['id']}-conversion.json").read_text())
            if conversion["source_sha256"] != result["sha256"]:
                raise ValueError("RTF原件已變更，既有轉檔抽取不套用。")
            result["pages"] = conversion["pages"]
            result["conversion_review"] = {k: v for k, v in conversion.items() if k != "pages"}
            result["document_format"] = "rtf_converted_docx_no_fixed_pdf_pages"
        elif response.content.startswith(bytes.fromhex("d0cf11e0a1b11ae1")):
            old_excel = expected_format == "xls"
            converted = None
            if not old_excel:
                antiword = os.environ.get("NCU_ANTIWORD_PATH", "antiword")
                with tempfile.NamedTemporaryFile(suffix=".doc") as handle:
                    handle.write(response.content)
                    handle.flush()
                    converted = subprocess.run(
                        [antiword, "-m", "UTF-8.txt", handle.name],
                        capture_output=True,
                        timeout=30,
                    )
            if converted and converted.returncode == 0:
                result["pages"] = [{"page": None, "text": converted.stdout.decode("utf-8")}]
                result["document_format"] = "doc_no_fixed_pdf_pages"
            else:
                # Some WPS/Word OLE files are rejected by antiword. A separately
                # reviewed conversion snapshot is bound to the original bytes;
                # never decode the OLE binary as text or reuse a changed source.
                snapshot = OUT / f"{spec['id']}-conversion.json"
                if not snapshot.exists():
                    if old_excel:
                        raise ValueError("舊Excel須先人工檢視SHA相符的XLSX轉檔；不以antiword解析。")
                    converted.check_returncode()
                conversion = json.loads(snapshot.read_text())
                if conversion["source_sha256"] != result["sha256"]:
                    raise ValueError("舊Office原件已變更，既有轉檔抽取不套用。")
                result["pages"] = conversion["pages"]
                result["conversion_review"] = {
                    k: v for k, v in conversion.items() if k != "pages"
                }
                result["document_format"] = (
                    "xls_converted_xlsx_no_pdf_pages" if old_excel
                    else "doc_converted_docx_no_fixed_pdf_pages"
                )
                result["extraction_attempts"] = [] if old_excel else [
                    {"method": "antiword", "status": "failed", "returncode": converted.returncode}
                ]
        elif response.headers.get("content-type", "").startswith("image/"):
            transcription = OUT / f"{spec['id']}-transcription.json"
            if transcription.exists():
                visual = json.loads(transcription.read_text())
                if visual["image_sha256"] != result["sha256"]:
                    raise ValueError(
                        "Image differs from manually inspected transcription"
                    )
                result["pages"] = [{"page": None, "text": visual["text"]}]
                result["document_format"] = "image_visual_transcription_no_pdf_pages"
            else:
                result["error"] = (
                    "Public image checklist requires visual transcription; not a text/PDF document."
                )
        elif "html" not in response.headers.get("content-type", "").lower() and not (
            expected_format == "html"
            and response.content.lstrip().lower().startswith((b"<!doctype html", b"<html"))
        ):
            raise ValueError("Unsupported content type; no HTML text inferred")
        else:
            soup = BeautifulSoup(response.content, "html.parser")
            for node in soup.select("script, style, nav, header, footer"):
                node.decompose()
            main = (
                soup.select_one(spec["html_content_selector"])
                if spec.get("html_content_selector")
                else None
            ) or soup.select_one("main") or soup.select_one('[role="main"]') or soup
            result["pages"] = [{"page": None, "text": main.get_text("\n", strip=True)}]
            result["links"] = [
                {"label": a.get_text(" ", strip=True), "href": a.get("href")}
                for a in main.select("a[href]")
            ]
        incomplete = [p["page"] for p in result["pages"] if "\x00" in p["text"]]
        if incomplete:
            result["text_quality_issues"] = [
                {
                    "pages": incomplete,
                    "reason": "原文字型映射含NUL，未修造缺字；仍須視覺核對。",
                }
            ]
        blank = [p["page"] for p in result["pages"] if not p["text"].strip()]
        if blank:
            result["non_text_pages"] = blank
        if spec.get("requires_public_field_excerpt"):
            excerpt_path = OUT / f"{spec['id']}-public-excerpt.json"
            excerpt = json.loads(excerpt_path.read_text())
            result["pages"] = []
            if excerpt["source_sha256"] != result["sha256"]:
                raise ValueError(
                    "已填範例原件已變更，須先重核必要欄位摘錄；不複製個資。"
                )
            result["pages"] = excerpt.get("public_pages") or [{"page": None, "text": excerpt["public_field_excerpt"]}]
            result["source_excerpt_only"] = True
            result["privacy_note"] = excerpt["note_zh"]
        visual_path = OUT / f"{spec['id']}-visual-review.json"
        if visual_path.exists():
            visual = json.loads(visual_path.read_text())
            if visual["source_sha256"] == result["sha256"]:
                result["visual_review"] = visual
            else:
                result["visual_review_note"] = (
                    "原件已變更，須重新視覺核對；既有視覺紀錄不套用。"
                )
        result["status_note"] = "public_source_extracted_scope_pending"
    except Exception as error:
        if spec.get("requires_public_field_excerpt"):
            result["pages"] = []
        result["error"] = str(error)
    return result


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--ids", nargs="+", help="Recheck these sources and retain other records"
    )
    selected = parser.parse_args().ids
    specs = [
        x for x in json.loads(SPEC.read_text()) if not selected or x["id"] in selected
    ]
    previous = (
        json.loads(gzip.decompress((OUT / "host-web-evidence.json.gz").read_bytes()))
        if (OUT / "host-web-evidence.json.gz").exists()
        else []
    )
    refreshed = {x["id"] for x in specs}
    retained = [x for x in previous if x["id"] not in refreshed]
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as pool:
        refreshed_records = list(pool.map(fetch, specs))
        by_id = {x["id"]: x for x in previous}
        for current in refreshed_records:
            old = by_id.get(current["id"])
            if old:
                current["previous_attempts"] = old.get("previous_attempts", []) + [
                    {
                        k: old.get(k)
                        for k in (
                            "checked_at",
                            "status",
                            "error",
                            "sha256",
                            "content_type",
                            "final_url",
                        )
                    }
                ]
        records = refreshed_records + retained
    (OUT / "host-web-evidence.json.gz").write_bytes(
        gzip.compress(json.dumps(records, ensure_ascii=False).encode(), mtime=0)
    )
    print(
        json.dumps(
            [
                {
                    "id": x["id"],
                    "status": x.get("status"),
                    "pages": len(x["pages"]),
                    "error": x.get("error"),
                }
                for x in records
            ],
            ensure_ascii=False,
            indent=2,
        )
    )
