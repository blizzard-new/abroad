"""Collect public NCU Drive attachments, with cached text and original provenance.

Run after collect_ncu_sources.py --inventory. Pass --retry-errors to refresh
failed downloads. No credentials, student portal or private files are accessed.
"""

import argparse, concurrent.futures, gzip, hashlib, io, json, re, requests, time
from pathlib import Path
from bs4 import BeautifulSoup
from pypdf import PdfReader
import logging

logging.getLogger("pypdf").setLevel(logging.ERROR)
out = Path(__file__).resolve().parents[1] / "sources/ncu/2026-10-08"
parser = argparse.ArgumentParser()
parser.add_argument("--retry-errors", action="store_true")
args = parser.parse_args()


def inventory(fid):
    p = out / "drive-folders" / f"{fid}.html.gz"
    url = f"https://drive.google.com/drive/folders/{fid}"
    try:
        if p.exists():
            raw = gzip.decompress(p.read_bytes())
            status = 200
        else:
            r = requests.get(url, timeout=30)
            r.raise_for_status()
            raw = r.content
            status = r.status_code
            p.write_bytes(gzip.compress(raw, mtime=0))
        soup = BeautifulSoup(raw, "html.parser")
        items = []
        for x in soup.select("tr[data-id]"):
            label = x.select_one("[data-tooltip]")
            label = label.get("data-tooltip") if label else x.get_text(" ", strip=True)
            kind = "folder" if label.endswith("folder") else "file"
            items.append(
                {
                    "id": x["data-id"],
                    "label": label,
                    "kind": kind,
                    "url": f"https://drive.google.com/drive/folders/{x['data-id']}"
                    if kind == "folder"
                    else f"https://drive.google.com/file/d/{x['data-id']}/view",
                    "display_text": x.get_text(" ", strip=True),
                }
            )
        return {
            "id": fid,
            "url": url,
            "checked_at": "2026-10-08",
            "status": status,
            "sha256": hashlib.sha256(raw).hexdigest(),
            "items": items,
        }
    except Exception as e:
        return {"id": fid, "url": url, "error": str(e), "items": []}


initial = json.loads((out / "drive-inventory.json").read_text())
allfolders = {}
pending = [x["id"] for x in initial]
for depth in range(4):
    if not pending:
        break
    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
        for item in pool.map(inventory, pending):
            allfolders[item["id"]] = item
    pending = list(
        {
            x["id"]
            for f in allfolders.values()
            for x in f["items"]
            if x["kind"] == "folder"
        }
        - allfolders.keys()
    )
    print(
        "depth",
        depth,
        "folders",
        len(allfolders),
        "remaining",
        len(pending),
        flush=True,
    )
(out / "drive-tree.json").write_text(
    json.dumps(list(allfolders.values()), ensure_ascii=False, indent=2) + "\n"
)
files = {
    x["id"]: x for f in allfolders.values() for x in f["items"] if x["kind"] == "file"
}
print("files", len(files), flush=True)
cache = out / "drive-text"
cache.mkdir(exist_ok=True)


def document(item):
    fid = item["id"]
    p = cache / f"{fid}.json.gz"
    if p.exists():
        cached = json.loads(gzip.decompress(p.read_bytes()))
        if not args.retry_errors or not cached.get("error"):
            incomplete = [p["page"] for p in cached["pages"] if "\x00" in p["text"]]
            if incomplete:
                cached["text_quality_issues"] = [
                    {
                        "pages": incomplete,
                        "reason": "PDF字型映射含NUL，原文字元不完整；需逐頁視覺／OCR核對，未修造缺字。",
                    }
                ]
            blank = [p["page"] for p in cached["pages"] if not p["text"].strip()]
            if blank:
                cached["non_text_pages"] = blank
            return cached
    result = {**item, "checked_at": "2026-10-08", "pages": []}
    try:
        url = f"https://drive.google.com/uc?export=download&id={fid}"
        r = requests.get(url, timeout=40)
        result.update(
            status=r.status_code,
            download_url=url,
            final_url=r.url,
            sha256=hashlib.sha256(r.content).hexdigest(),
            content_type=r.headers.get("content-type"),
        )
        r.raise_for_status()
        if r.content.startswith(b"%PDF"):
            reader = PdfReader(io.BytesIO(r.content))
            result["pages"] = [
                {
                    "page": i + 1,
                    "text": page.extract_text(),
                    "urls": [
                        a.get_object().get("/A", {}).get("/URI")
                        for a in page.get("/Annots", [])
                        if a.get_object().get("/A", {}).get("/URI")
                    ],
                }
                for i, page in enumerate(reader.pages)
            ]
            result["status_note"] = (
                "text_extracted"
                if any(x["text"].strip() for x in result["pages"])
                else "image_pdf_requires_visual_review"
            )
            incomplete = [p["page"] for p in result["pages"] if "\x00" in p["text"]]
            if incomplete:
                result["text_quality_issues"] = [
                    {
                        "pages": incomplete,
                        "reason": "PDF字型映射含NUL，原文字元不完整；需逐頁視覺／OCR核對，未修造缺字。",
                    }
                ]
            blank = [p["page"] for p in result["pages"] if not p["text"].strip()]
            if blank:
                result["non_text_pages"] = blank
        elif r.content.startswith(b"PK"):
            import zipfile
            from lxml import etree

            z = zipfile.ZipFile(io.BytesIO(r.content))
            if "word/document.xml" in z.namelist():
                text = " ".join(
                    etree.fromstring(z.read("word/document.xml")).xpath(
                        "//w:t/text()",
                        namespaces={
                            "w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
                        },
                    )
                )
                kind = "docx"
            elif "content.xml" in z.namelist():
                text = " ".join(etree.fromstring(z.read("content.xml")).itertext())
                kind = "odf"
            elif "xl/workbook.xml" in z.namelist():
                strings = (
                    etree.fromstring(z.read("xl/sharedStrings.xml")).xpath(
                        '//*[local-name()="si"]'
                    )
                    if "xl/sharedStrings.xml" in z.namelist()
                    else []
                )
                values = ["".join(x.itertext()) for x in strings]
                lines = []
                for sheet in [
                    n
                    for n in z.namelist()
                    if re.fullmatch(r"xl/worksheets/sheet\d+\.xml", n)
                ]:
                    for row in etree.fromstring(z.read(sheet)).xpath(
                        '//*[local-name()="row"]'
                    ):
                        cells = []
                        for cell in row:
                            v = cell.find(
                                "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}v"
                            )
                            value = (
                                v.text if v is not None else "".join(cell.itertext())
                            )
                            cells.append(
                                values[int(value)]
                                if cell.get("t") == "s" and value
                                else value or ""
                            )
                        lines.append(" | ".join(cells))
                text = "\n".join(lines)
                kind = "xlsx"
            else:
                raise ValueError("Unsupported ZIP document format")
            result["pages"] = [{"page": None, "text": text}]
            result["status_note"] = kind + "_text_extracted_no_pagination"
        else:
            result["error"] = (
                "Public download returned non PDF/DOCX; inspect preview or export format."
            )
            result["preview_text"] = BeautifulSoup(r.text, "html.parser").get_text(
                " ", strip=True
            )[:1500]
    except Exception as e:
        result["error"] = str(e)
    p.write_bytes(
        gzip.compress(
            json.dumps(result, ensure_ascii=False, default=str).encode(), mtime=0
        )
    )
    return result


results = []
with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
    for i, result in enumerate(pool.map(document, files.values()), 1):
        results.append(result)
        if i % 30 == 0:
            print("read", i, "errors", sum("error" in x for x in results), flush=True)
(out / "drive-evidence.json.gz").write_bytes(
    gzip.compress(
        json.dumps(results, ensure_ascii=False, default=str).encode(), mtime=0
    )
)
print(
    "DONE",
    len(results),
    "errors",
    sum("error" in x for x in results),
    "pages",
    sum(len(x["pages"]) for x in results),
    flush=True,
)
