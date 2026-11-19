"""Replay CGU Lincoln 116-1 preparation using the same six sample files and stopwatch.

Usage: python measure_preflight.py --base http://127.0.0.1:8819 > preflight-runs.json
To replay a captured run, pass --snapshots DIR containing notice.html, guide.html
and platform.html (the expanded 116-1 home submission step). No form is submitted.
"""
import argparse
import hashlib
import json
import re
import shutil
import tempfile
import time
from pathlib import Path
from urllib.parse import quote, urlencode

import requests
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright
from pypdf import PdfReader
from reportlab.pdfgen.canvas import Canvas

NOTICE = "https://www.cgu.edu.tw/oia-ch/Subject/Detail/85785?nodeId=15817"
GUIDE = "https://www.cgu.edu.tw/oia-ch/Contents?nodeId=15656"
SCHOOL = "林肯大學 Lincoln University"
# Each input has an opaque filename and a typed test marker in its PDF content.
FILES = {
    "adviser-signed-application": ("出國研修申請表", "導師或指導教授"),
    "guardian-signed-consent": ("同意書", "家長或監護人簽名"),
    "ranked-chinese-transcript": ("中文歷年成績單正本", "班級排名百分比"),
    "enrolment-certificate": ("在學證明", "icgu"),
    "language-certificate": ("外國語文能力證明",),
    "study-plan": ("讀書計畫", "一頁即可"),
}
FORMS = ["https://forms.gle/JbdGkA9i7wkNdtvX8", "https://forms.gle/VzHD2wPxQHDZvfQ37"]


def fetch_snapshots(folder, base, browser):
    for filename, url in (("notice", NOTICE), ("guide", GUIDE)):
        response = requests.get(url, timeout=35)
        response.raise_for_status()
        (folder / f"{filename}.html").write_bytes(response.content)
    ctx = browser.new_context(locale="zh-TW")
    page = ctx.new_page()
    page.add_init_script("sessionStorage.setItem('exchange-guide-browse-first','1');"
                         "localStorage.setItem('exchange-guide-home-school','長庚大學')")
    route = "/?" + urlencode({"view": "list", "home": "長庚大學"}) + "#school=" + quote(SCHOOL)
    page.goto(base + route, wait_until="domcontentloaded", timeout=120000)
    page.locator("#detail-tab-application").click(timeout=120000)
    step = page.locator("#workflow-content .workflow-timeline > :nth-child(2)")
    step.locator("summary").click(timeout=120000)
    assert "在學證明" in step.inner_text()
    (folder / "platform.html").write_text(step.evaluate("el => el.outerHTML"))
    ctx.close()


def readable_pages(folder):
    pages, hashes = {}, {}
    for key in ("notice", "guide", "platform"):
        data = (folder / f"{key}.html").read_bytes()
        hashes[key] = hashlib.sha256(data).hexdigest()
        soup = BeautifulSoup(data, "html.parser")
        if key == "platform":
            item = soup.select_one("details.workflow-step")
        else:
            item = next(a for a in soup.select("article") if "PDF" in a.get_text())
        for node in item.select("script, style, img, video, audio, svg, iframe, link"):
            node.decompose()
        pages[key] = str(item)
    return pages, hashes


def sample_inputs(path):
    for i, key in enumerate(reversed(FILES)):
        pdf = Canvas(str(path / f"scan-{i+1}.pdf"), invariant=1)
        pdf.drawString(50, 770, f"SYNTHETIC ONLY / type={key}")
        pdf.showPage()
        pdf.save()


def observe(page, html):
    page.set_content(html, wait_until="domcontentloaded")
    return re.sub(r"\s+", "", page.locator("body").inner_text()).lower()


def preflight(page, arm, html, inputs, out):
    started = time.perf_counter_ns()
    entry = observe(page, html["notice" if arm == "official" else "platform"])
    # Preserve URL case by extracting the original strings, without opening either form.
    original = page.locator("body").inner_text()
    urls = list(dict.fromkeys(re.findall(r"https://forms\.gle/[a-zA-Z0-9]+", original)))
    assert urls == FORMS, (arm, urls)
    links = page.locator("a[href]").evaluate_all("anchors => anchors.map(a => a.href)")
    assert set(FORMS).issubset(links), (arm, "missing official action link")
    date_match = re.search(r"(2026)[/年](12)[/月](21)", entry)
    assert date_match and ("17:00" in entry or "下午5點" in entry)
    assert "pdf" in entry and ("上傳" in entry or "逐項" in entry)
    instructions = observe(page, html["guide"]) if arm == "official" else entry
    for key, words in FILES.items():
        assert all(word in instructions for word in words), (arm, key)
    # Identical output and checks on both arms; real school signatures are prerequisites.
    out.mkdir()
    files = {}
    for f in sorted(inputs.glob("*.pdf")):
        tag = re.search(r"type=([a-z-]+)", PdfReader(f).pages[0].extract_text()).group(1)
        assert tag in FILES and tag not in files
        target = out / f"{tag}.pdf"
        shutil.copyfile(f, target)
        files[tag] = hashlib.sha256(target.read_bytes()).hexdigest()
    assert set(files) == set(FILES)
    packet = {"applicant": "synthetic CGU undergraduate; 116-1; Lincoln; no EMI/optional attachments",
              "deadline": "-".join(date_match.groups()) + "T17:00:00+08:00",
              "application_url": urls[0], "upload_url": urls[1], "files": files}
    index = out / "handoff.json"
    index.write_text(json.dumps(packet, ensure_ascii=False, sort_keys=True))
    assert len(list(out.iterdir())) == 7 and json.loads(index.read_text()) == packet
    elapsed = (time.perf_counter_ns() - started) / 1e6
    return {"milliseconds": round(elapsed, 3), "packet_sha256": hashlib.sha256(index.read_bytes()).hexdigest()}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", default="http://127.0.0.1:8819")
    parser.add_argument("--snapshots", type=Path)
    args = parser.parse_args()
    with tempfile.TemporaryDirectory() as temp, sync_playwright() as p:
        root = Path(temp)
        inputs = root / "inputs"
        inputs.mkdir()
        sample_inputs(inputs)
        browser = p.chromium.launch(executable_path=shutil.which("chromium"), args=["--no-sandbox"])
        if args.snapshots is None:
            fetch_snapshots(root, args.base, browser)
        html, hashes = readable_pages(args.snapshots or root)
        runs = []
        for trial in range(6):
            arms = ("official", "platform") if trial % 2 == 0 else ("platform", "official")
            for arm in arms:
                context = browser.new_context()
                page = context.new_page()
                page.route("**/*", lambda r: r.abort())
                runs.append({"trial": trial + 1, "arm": arm,
                             **preflight(page, arm, html, inputs, root / f"{trial}-{arm}")})
                context.close()
        browser.close()
        assert len({result["packet_sha256"] for result in runs}) == 1
        print(json.dumps({"source_sha256": hashes, "sources": {"notice": NOTICE, "guide": GUIDE,
                         "platform": "CGU / Lincoln / 116 / 秋季／全學年梯次 / 申請方式 / 在長庚期限內送出校內申請"},
                          "runs": runs}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
