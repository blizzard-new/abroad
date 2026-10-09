"""Capture TKU's public academic directory and build school-only form options.

This is a registration directory, never an exchange eligibility whitelist.
The live pages and 115 organization table were read before adding this adapter.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import unicodedata
from datetime import datetime, timezone
from pathlib import Path

import requests
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
BUNDLE = ROOT / "src/exchange_info/official_data/tku"
SOURCES = [("academic-directory", "https://www.tku.edu.tw/acad.asp"),
           ("academic-directory-modern", "https://www.tku.edu.tw/tku/?page_id=4807"),
           ("organization-115", "https://www.ac.tku.edu.tw/ac/?page_id=18269")]


def canonical(text):
    return unicodedata.normalize("NFKC", text).strip()


def build(capture=False):
    if capture:
        sources = []
        for key, url in SOURCES:
            response = requests.get(url, timeout=40)
            response.raise_for_status()
            response.encoding = response.apparent_encoding
            sources.append(dict(id=key, source_url=url, final_url=response.url,
                http_status=response.status_code, checked_at=datetime.now(timezone.utc).isoformat(),
                applicable_year="115／2026–2027組織名稱" if key == "organization-115" else "2026-10-08公開學籍單位目錄；非2027交換資格",
                role="directory_reference", sha256=hashlib.sha256(response.content).hexdigest(),
                html=response.text))
        (BUNDLE / "academic_sources.json").write_text(json.dumps(sources, ensure_ascii=False, indent=2) + "\n")
    sources = json.loads((BUNDLE / "academic_sources.json").read_text())
    classic = BeautifulSoup(sources[0]["html"], "html.parser")
    modern_text = canonical(BeautifulSoup(sources[1]["html"], "html.parser").get_text(" ", strip=True))
    organization = BeautifulSoup(sources[2]["html"], "html.parser")
    organization_names = {canonical(cells[2].get_text(" ", strip=True))
        for row in organization.select("table tr") if len(cells := row.select("td")) >= 3}
    colleges = {}
    evidence = []
    for heading in classic.select("h3"):
        anchor = heading.select_one(".col1 a")
        if not anchor or not canonical(anchor.get_text()).endswith("學院"):
            continue
        college = canonical(anchor.get_text())
        assert college in modern_text and college in organization_names, college
        units = []
        for link in heading.parent.select("ul .dept a"):
            raw = link.get_text(" ", strip=True)
            name = canonical(re.sub(r"[（(]115學年度更名[）)]", "", raw))
            if not re.search(r"學系|研究所|學位學程|博士班|在職專班", name):
                continue
            variant = "理學院尖端材料科學學士學位學程 (113學年度停招)" if name == "尖端材料科學學士學位學程" else name
            assert variant in organization_names, name
            units.append(name)
            evidence.append(dict(college=college, unit=name, original_text=raw,
                source_ids=["academic-directory", "organization-115"],
                organization_name=variant,
                modern_page_text_agrees=name in modern_text,
                locator=f"學術單位 h3 {college} 下 .dept；115組織名稱表 單位名稱={name}",
                checked_at=sources[0]["checked_at"], status="verified_directory",
                scope="僅學籍填寫；不得推定該系所、學制或在職生可申請交換"))
        assert units and len(units) == len(set(units)), college
        colleges[college] = units
    assert len(colleges) == 9 and sum(map(len, colleges.values())) == 44
    directory = dict(home_university="淡江大學", source_url=SOURCES[0][1],
        checked_at=sources[0]["checked_at"], applicable_year="115／現行學籍單位；非交換學年度",
        scope="9學院44學籍單位；排除研究中心、行政單位與網路校園重列。交換資格依本期簡章另查。",
        source_discrepancies=[dict(unit=row['unit'], source_id="academic-directory-modern",
            status="needs_confirmation", reason="另一官方頁取得的HTML未含同名單位；採115組織表與學術單位頁一致名稱，保留頁面差異。")
            for row in evidence if not row['modern_page_text_agrees']],
        colleges=colleges, evidence=evidence)
    (BUNDLE / "academic_units.json").write_text(json.dumps(directory, ensure_ascii=False, indent=2) + "\n")
    js = {"sourceUrl":SOURCES[0][1], "checkedAt":sources[0]["checked_at"], "colleges":colleges}
    script = """// TKU registration directory; programme eligibility is checked separately.
window.UniWayAcademicUnits ||= {};
window.UniWayAcademicUnits["淡江大學"] = DIRECTORY;
window.UniWayTKU = {
  applicationYears(periods) {
    const years = periods.map(row => Number(String(row.academic_year || '').split('-')[0])).filter(year => year >= 2000);
    const first = years.length ? Math.max(...years) : new Date().getFullYear() + 1;
    return [first, first + 1, first + 2].map(year => `${year}-${year + 1}`);
  }
};
""".replace("DIRECTORY", json.dumps(js, ensure_ascii=False, indent=2))
    (ROOT / "src/exchange_info/static/tku-academic-units.js").write_text(script)
    print(json.dumps(dict(colleges=len(colleges), units=len(evidence), sources=len(sources)), ensure_ascii=False))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--capture", action="store_true")
    build(parser.parse_args().capture)
