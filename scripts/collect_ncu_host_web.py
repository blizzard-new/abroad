"""Snapshot explicit official host checks; preserve HTTP failures as failures.

Only public pages are read. A 403 is not evidence of a login requirement or an
unannounced programme. Web-page text has no PDF page number.
"""

from pathlib import Path
import concurrent.futures, gzip, hashlib, io, json, zipfile, os, subprocess, tempfile
from xml.etree import ElementTree
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
        result.update(
            status=response.status_code,
            final_url=response.url,
            sha256=hashlib.sha256(response.content).hexdigest(),
            content_type=response.headers.get("content-type"),
        )
        response.raise_for_status()
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
        elif response.content.startswith(bytes.fromhex("d0cf11e0a1b11ae1")):
            antiword = os.environ.get("NCU_ANTIWORD_PATH", "antiword")
            with tempfile.NamedTemporaryFile(suffix=".doc") as handle:
                handle.write(response.content)
                handle.flush()
                converted = subprocess.run(
                    [antiword, "-m", "UTF-8.txt", handle.name],
                    capture_output=True,
                    check=True,
                    timeout=30,
                )
            result["pages"] = [{"page": None, "text": converted.stdout.decode("utf-8")}]
            result["document_format"] = "doc_no_fixed_pdf_pages"
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
        elif "html" not in response.headers.get("content-type", ""):
            raise ValueError("Unsupported content type; no HTML text inferred")
        else:
            soup = BeautifulSoup(response.content, "html.parser")
            for node in soup.select("script, style, nav, header, footer"):
                node.decompose()
            main = soup.select_one("main") or soup.select_one('[role="main"]') or soup
            result["pages"] = [{"page": None, "text": main.get_text("\n", strip=True)}]
            result["links"] = [
                {"label": a.get_text(" ", strip=True), "href": a.get("href")}
                for a in main.select("a[href]")
            ]
        result["status_note"] = "public_source_extracted_scope_pending"
    except Exception as error:
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
