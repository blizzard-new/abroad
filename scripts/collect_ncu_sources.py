"""Snapshot NCU's public sources; preserve source text, dates and table cells.

Run --inventory to refresh public country folders. No credentials are used.
The quota PDF is explicitly 115, never a current 116 list.
"""

from __future__ import annotations
import argparse, concurrent.futures, gzip, hashlib, json, re, subprocess
from pathlib import Path
import xml.etree.ElementTree as ET
import requests
from bs4 import BeautifulSoup
from pypdf import PdfReader
from pypdf.generic import ContentStream

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "sources/ncu/2026-10-08"
CHECKED = "2026-10-08"


def write_json(name, value):
    (OUT / name).write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n")


def quota_rows():
    pdf = OUT / "list-115.pdf"
    bbox = OUT / "list-115-bbox.html"
    subprocess.run(["pdftotext", "-bbox-layout", str(pdf), str(bbox)], check=True)
    xml = ET.parse(bbox)
    ns = {"x": "http://www.w3.org/1999/xhtml"}
    r = PdfReader(pdf)
    rows = []
    for pi, (p, xp) in enumerate(zip(r.pages, xml.findall(".//x:page", ns)), 1):
        height = float(p.mediabox.height)
        borders = sorted(
            set(
                round(height - float(v[1]), 3)
                for v, op in ContentStream(p.get_contents(), r).operations
                if op == b"re"
                and abs(float(v[0]) - 13.944) < 0.1
                and float(v[2]) > 810
                and 0.7 < float(v[3]) < 1.0
            )
        )
        words = [
            (float(w.get("xMin")), float(w.get("yMin")), float(w.get("yMax")), w.text)
            for w in xp.findall(".//x:word", ns)
        ]
        for top, bottom in zip(borders, borders[1:]):
            cells = []
            for left, right in zip(
                [13, 50, 105, 223, 423, 470, 671], [50, 105, 223, 423, 470, 671, 830]
            ):
                selected = sorted(
                    [
                        w
                        for w in words
                        if left <= w[0] < right and top <= (w[1] + w[2]) / 2 < bottom
                    ],
                    key=lambda w: (round(w[1], 1), w[0]),
                )
                lines = {}
                for x, y, _, t in selected:
                    lines.setdefault(round(y, 0), []).append(t)
                cells.append([" ".join(v) for v in lines.values()])
            if not cells[2] or "學校(中文)" in cells[2][0]:
                continue
            zh = "".join(cells[2])
            en = " ".join(cells[3])
            url = None
            for a in p.get("/Annots", []):
                a = a.get_object()
                rect = a.get("/Rect", [])
                if (
                    rect
                    and top <= height - (float(rect[1]) + float(rect[3])) / 2 < bottom
                ):
                    url = a.get("/A", {}).get("/URI")
                    break
            rows.append(
                {
                    "id": f"ncu-{len(rows) + 1:03d}",
                    "page": pi,
                    "row_bounds": [top, bottom],
                    "country": cells[1][0] if cells[1] else None,
                    "name_zh": zh,
                    "name_en": en,
                    "quota_115": " ".join(cells[4]),
                    "language_115": "\n".join(cells[5]),
                    "notes_115": "\n".join(cells[6]),
                    "introduction_url": url,
                    "original_cells": cells,
                    "academic_year": "115",
                    "checked_at": CHECKED,
                }
            )
    write_json("quota-115-rows.json", rows)
    print(
        "rows",
        len(rows),
        "unlinked",
        sum(not x["introduction_url"] for x in rows),
        "empty-name",
        sum(not x["name_en"] for x in rows),
    )
    return rows


def folder_inventory():
    root = BeautifulSoup((OUT / "drive.html").read_text(), "html.parser")
    folders = {
        x["data-id"]: x.select_one("[data-tooltip]").get("data-tooltip")
        if x.select_one("[data-tooltip]")
        else x.get_text(" ", strip=True)
        for x in root.select("[data-id]")
        if len(x["data-id"]) > 15 and x.get_text(" ", strip=True)
    }

    def fetch(item):
        fid, label = item
        url = f"https://drive.google.com/drive/folders/{fid}"
        try:
            resp = requests.get(url, timeout=35)
            resp.raise_for_status()
            (OUT / "drive-folders").mkdir(exist_ok=True)
            (OUT / "drive-folders" / f"{fid}.html.gz").write_bytes(
                gzip.compress(resp.content, mtime=0)
            )
            soup = BeautifulSoup(resp.text, "html.parser")
            files = {}
            for x in soup.select("[data-id]"):
                title = x.get_text(" ", strip=True)
                if title and len(x["data-id"]) > 15 and x["data-id"] != fid:
                    files.setdefault(
                        x["data-id"],
                        {
                            "id": x["data-id"],
                            "display_text": title,
                            "url": f"https://drive.google.com/file/d/{x['data-id']}/view",
                        },
                    )
            return {
                "id": fid,
                "label": label,
                "url": url,
                "checked_at": CHECKED,
                "status": resp.status_code,
                "sha256": hashlib.sha256(resp.content).hexdigest(),
                "files": list(files.values()),
            }
        except requests.RequestException as e:
            return {"id": fid, "label": label, "url": url, "error": str(e), "files": []}

    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as pool:
        results = list(pool.map(fetch, folders.items()))
    write_json("drive-inventory.json", results)
    print(
        "folders",
        len(results),
        "files",
        sum(len(x["files"]) for x in results),
        "failures",
        sum("error" in x for x in results),
    )


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--inventory", action="store_true")
    a = p.parse_args()
    quota_rows()
    if a.inventory:
        folder_inventory()


if __name__ == "__main__":
    main()
