"""Read published PDF hyperlinks for all 49 closed CCU reference identities.

An attachment's content year is reviewed separately. Fresh retrieval does not
make a gray historical document a current application requirement.
"""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
import gzip
from io import BytesIO
import json
import re
from xml.etree import ElementTree
from zipfile import ZipFile
from urllib.parse import parse_qs, urlsplit

from pypdf import PdfReader
from bs4 import BeautifulSoup

from fetch_ccu_completion_sources import BUNDLE, OUT, fetch


def response_bytes(receipt):
    payload = (BUNDLE / receipt["bundled_file"]).read_bytes()
    return gzip.decompress(payload) if receipt["bundled_file"].endswith(".gz") else payload


def parse_document(receipt):
    if receipt.get("error") or receipt.get("http_status") != 200 or not receipt.get("bundled_file"):
        return
    payload = response_bytes(receipt)
    physical_pages = payload.startswith(b"%PDF-")
    if physical_pages:
        pages = [page.extract_text() or "" for page in PdfReader(BytesIO(payload)).pages]
    elif payload.startswith(b"PK"):
        with ZipFile(BytesIO(payload)) as archive:
            if "word/document.xml" not in archive.namelist():
                return
            root = ElementTree.fromstring(archive.read("word/document.xml"))
            namespace = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
            pages = ["\n".join("".join(p.itertext()) for p in root.iter(namespace + "p"))]
    else:
        return
    result = {"source_id": receipt["source_id"], "source_url": receipt["source_url"],
              "checked_at": receipt["checked_at"], "content_hash": receipt["sha256"],
              "text_pages": pages, "attachment_file": receipt["bundled_file"] if physical_pages else None,
              "review_status": "content_year_and_program_not_yet_reviewed"}
    (OUT / (receipt["source_id"] + ".parsed.json")).write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")


def public_folder_children(manifest):
    children = []
    for parent in manifest:
        if "/drive/folders/" not in parent["official_link_url"]:
            continue
        receipt = json.loads((OUT / (parent["source_id"] + ".receipt.json")).read_text())
        if receipt.get("error") or receipt.get("http_status") != 200:
            continue
        soup = BeautifulSoup(response_bytes(receipt), "html.parser")
        seen = set()
        for tag in soup.select('[role="row"][data-id]'):
            file_id = tag["data-id"]
            if not re.fullmatch(r"[A-Za-z0-9_-]+", file_id) or file_id in seen:
                continue
            seen.add(file_id)
            label = tag.select_one('[data-tooltip]')
            children.append({"ccu_page": parent["ccu_page"],
                "source_id": parent["source_id"] + f"-file-{len(seen)}",
                "public_folder_url": parent["official_link_url"],
                "public_file_label": label.get("data-tooltip") if label else tag.get_text(" ", strip=True),
                "official_link_url": "https://drive.google.com/file/d/" + file_id + "/view",
                "requested_url": "https://drive.usercontent.google.com/download?id=" + file_id + "&export=download",
                "parent_source_id": parent["source_id"], "source_year": "檔名年份只作候選；以正文確認"})
    return children


def main():
    pdf = PdfReader(BUNDLE / "completion_sources/partners.pdf")
    rows = [json.loads(line) for line in (BUNDLE / "partners.jsonl").read_text().splitlines()]
    jobs = []
    manifest = []
    for row in rows:
        if row["availability_status"] != "not_open":
            continue
        urls = []
        for page in row["source_pages"]:
            for annotation in pdf.pages[page - 1].get("/Annots", []):
                url = annotation.get_object().get("/A", {}).get("/URI")
                if url and any(domain in url for domain in ["drive.google.com", "reurl.cc", "gatxs.bfsu.edu.cn/f/view-", "czu-prague-fact-sheet"]):
                    urls.append((str(url), page))
        seen = set()
        for url, physical_page in urls:
            if url in seen:
                continue
            seen.add(url)
            target = url
            match = re.search(r"drive\.google\.com/file/d/([A-Za-z0-9_-]+)", url)
            if match:
                target = "https://drive.usercontent.google.com/download?id=" + match[1] + "&export=download"
            elif urlsplit(url).hostname == "drive.google.com" and urlsplit(url).path == "/open":
                target = "https://drive.usercontent.google.com/download?id=" + parse_qs(urlsplit(url).query)["id"][0] + "&export=download"
            number = len(seen)
            label = f"reference-link-{number}"
            record = {"ccu_page": row["source_pages"][0], "school_name": row["school_name"],
                      "source_id": f"p{row['source_pages'][0]}-{label}", "official_link_url": url,
                      "requested_url": target, "mother_source_url": row["source_url"],
                      "mother_source_pages": [physical_page], "mother_applicability": "灰字歷史參考；本期未開放",
                      "extraction_method": "Exact PDF URI annotation; no reconstructed identifier"}
            manifest.append(record)
            jobs.append((record["ccu_page"], label, target))
    (BUNDLE / "completion-reference-document-links.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
    with ThreadPoolExecutor(max_workers=4) as pool:
        for receipt in pool.map(lambda args: fetch(*args), jobs):
            parse_document(receipt)
            print(receipt["source_id"], receipt.get("http_status"), receipt.get("content_type"), receipt.get("error"), flush=True)
    children = public_folder_children(manifest)
    (BUNDLE / "completion-public-folder-file-links.json").write_text(json.dumps(children, ensure_ascii=False, indent=2) + "\n")
    with ThreadPoolExecutor(max_workers=4) as pool:
        for receipt in pool.map(lambda row: fetch(row["ccu_page"], row["source_id"].split("-", 1)[1], row["requested_url"]), children):
            parse_document(receipt)
            print(receipt["source_id"], receipt.get("http_status"), receipt.get("error"), flush=True)


if __name__ == "__main__":
    main()
