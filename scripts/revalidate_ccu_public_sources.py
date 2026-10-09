"""Read CCU's ten scoped public sources with certificate verification enabled.

Save new HTTP responses and extraction receipts outside the clone. These reads
do not assign policy years, answer forms, submit data, or fetch student responses.
An HTTP success alone never establishes that a rendered policy was reproduced.
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import io
import json
import re
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import urlsplit

import requests
from bs4 import BeautifulSoup
from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[1]
BUNDLE = ROOT / "src/exchange_info/official_data/ccu"
CALENDAR_TITLE = "College Academic Calendar Schedule A.Y. 2026-2027"
TAB_IDS = {"ilrad-contact": 230, "visa": 231, "application": 232,
           "dormitories": 233, "handbook": 427}


def write_json(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n")


def page_data(raw):
    node = BeautifulSoup(raw, "html.parser").find(attrs={"data-page": True})
    if node is None:
        raise ValueError("Official response lacks the structured data-page body")
    return json.loads(node["data-page"])


def calendar_entry(raw):
    props = page_data(raw)["props"]
    matches = [entry for frame in props["frames"]
               for entry in frame.get("modular_frame_accordion", [])
               if entry.get("title") == CALENDAR_TITLE]
    if len(matches) != 1:
        raise ValueError("Current college calendar must have one exact title")
    return matches[0]


def calendar_image(raw):
    image = BeautifulSoup(calendar_entry(raw)["content"], "html.parser").find("img")
    data = image["src"]
    if not data.startswith("data:image/jpeg;base64,"):
        raise ValueError("Current calendar is not the expected embedded JPEG")
    return base64.b64decode(data.split(",", 1)[1], validate=True)


def mapua_sections(raw, kind):
    props = page_data(raw)["props"]
    if kind == "root":
        return [props["cms_header"]["content_ticker_text"]]
    if kind == "calendar-index":
        return [calendar_entry(raw)["title"]]
    matches = [tab for frame in props["frames"]
               for tab in frame.get("modular_frame_tabs", [])
               if tab.get("id") == TAB_IDS[kind]
               and not tab.get("is_hidden") and not tab.get("deleted_at")]
    if len(matches) != 1:
        raise ValueError("Expected one publicly listed policy tab")
    tab = matches[0]
    sections = [tab["title"]]
    for block in tab["modular_frame_tab_lists"]:
        if block.get("title"):
            sections.append(block["title"])
        if block.get("content"):
            sections.append(BeautifulSoup(block["content"], "html.parser").get_text(" ", strip=True))
    return ["\n".join(sections)]


def public_question_endpoint(raw):
    html = raw.decode("utf-8")
    match = re.search(r"window\.OfficeFormServerInfo\s*=\s*", html)
    if match is None:
        raise ValueError("Public page lacks question-only prefetch configuration")
    config, _ = json.JSONDecoder().raw_decode(html[match.end():])
    url = config["prefetchFormUrl"]
    parts = urlsplit(url)
    if (parts.scheme != "https" or parts.hostname != "forms.cloud.microsoft"
            or "/light/runtimeForms(" not in parts.path
            or parts.query != "$expand=questions($expand=choices)"
            or "responses" in url.lower()):
        raise ValueError("Refuse endpoints other than public blank-form questions")
    return url


def question_metadata(raw):
    form = json.loads(raw)
    if form.get("runtimeResponses") or form.get("predefinedResponses"):
        raise ValueError("Public metadata unexpectedly contains response data")
    questions = sorted(form["questions"], key=lambda question: question["order"])
    sections = [form["title"], f"Public question metadata count: {len(questions)}"]
    for number, question in enumerate(questions, 1):
        sections.append(f"{number}. {question['title']}")
        sections.append(f"Metadata required: {question.get('required')}")
        for choice in question.get("choices", []):
            sections.append(json.dumps(choice, ensure_ascii=False))
    return ["\n".join(sections)]


def fetch(url, output, stem):
    if urlsplit(url).scheme != "https":
        raise ValueError("Only certificate-verified HTTPS URLs are accepted")
    proof = {"requested_url": url, "started_at": datetime.now(UTC).isoformat(),
             "tls_verify": True, "https_certificate_errors_ignored": False}
    try:
        response = requests.get(url, timeout=45, verify=True)
        proof.update({"final_url": response.url, "http_status": response.status_code,
                      "content_type": response.headers.get("Content-Type"),
                      "sha256": hashlib.sha256(response.content).hexdigest(),
                      "bytes": len(response.content)})
        response.raise_for_status()
        content_type = proof["content_type"] or ""
        extension = ".pdf" if "pdf" in content_type else ".json" if "json" in content_type else ".html"
        filename = stem + extension
        (output / filename).write_bytes(response.content)
        proof["response_file"] = filename
        return response.content, proof
    except requests.RequestException as error:
        proof["error"] = str(error)
        raise
    finally:
        proof["checked_at"] = datetime.now(UTC).isoformat()
        write_json(output / (stem + "-http-proof.json"), proof)


def acquire(output):
    review = json.loads((BUNDLE / "twentysixth-source-review.json").read_text())
    receipts = []
    for entry in review["source_reviews"]:
        sid = entry["source_id"]
        source = json.loads((BUNDLE / "overseas_sources" / (sid + ".json")).read_text())
        raw, proof = fetch(source["source_url"], output, sid)
        proof["historical_source_id"] = sid
        if sid == "p83-r26-international-handbook":
            pages = [page.extract_text() for page in PdfReader(io.BytesIO(raw)).pages]
            proof["extraction_method"] = "PDF text extraction; images require separate review"
        elif sid == "p83-r26-calendar-image":
            image = calendar_image(raw)
            filename = sid + "-normal-tls.jpg"
            (output / filename).write_bytes(image)
            proof.update({"extracted_image_file": filename,
                          "extracted_image_sha256": hashlib.sha256(image).hexdigest(),
                          "extraction_method": "Normal HTTPS data-page exact college title and embedded base64; dates require visual review"})
            pages = [calendar_entry(raw)["title"]]
        elif sid.startswith("p83-"):
            kind = sid.removeprefix("p83-r26-").removesuffix("-render")
            pages = mapua_sections(raw, kind)
            proof["extraction_method"] = "Decode official HTTP data-page JSON; select specified public policy section"
        else:
            endpoint = public_question_endpoint(raw)
            pages = ["Public blank-form question endpoint: " + endpoint]
            proof["extraction_method"] = "OfficeFormServerInfo.prefetchFormUrl only; no student response endpoint"
            api_raw, api_proof = fetch(endpoint, output, "uninter-public-question-metadata")
            api_proof.update({"historical_source_id": sid, "parent_response_file": proof["response_file"],
                              "text_pages": question_metadata(api_raw),
                              "extraction_method": "Public blank-form question metadata; not a rendered browser view",
                              "student_responses_requested": False})
            receipts.append(api_proof)
        proof["text_pages"] = pages
        receipts.append(proof)
        write_json(output / "normal-tls-receipts.json", receipts)
    return receipts


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    output = parser.parse_args().output.resolve()
    if output.is_relative_to(ROOT):
        parser.error("Save new acquisition evidence outside the clone")
    output.mkdir(parents=True, exist_ok=True)
    receipts = acquire(output)
    print(json.dumps({"normal_tls_reads": len(receipts), "output": str(output),
                      "certificate_errors_ignored": False}))


if __name__ == "__main__":
    main()
