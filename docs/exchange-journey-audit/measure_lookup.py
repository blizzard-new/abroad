"""Measure retrieval of the same exchange shortlist facts from two public websites.

Run from the repository venv with pdftotext on PATH. Prints the three paired runs as JSON.
Both paths start at the term announcement or the home-school catalogue and follow real
links. No logins, browser state, submission, simulated delays, or local site mirror.
"""
import json
import re
import subprocess
import time
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

NOTICE = "https://new.ntpu.edu.tw/oia/news/6ab396bf7085cb4f0c81831f"
DIRECTORY = "https://app.uniway-tw.com/schools/ntpu"
CASES = {
    "saga": {
        "school": "佐賀大學", "programme": "SPACE-SAGA", "end": "山梨學院",
        "table": ["SPACESE-B", "2.8/4.0", "TOEIC785", "1學期或1學年"],
        "platform": ["SPACESE-B", "2.8/4.0", "TOEIC785", "1學期或1學年"],
    },
    "icla": {
        "school": "山梨學院", "programme": "iCLA", "end": "電氣通信",
        "table": ["2.5/4.0", "IELTS6.0", "限大學部", "1學期或1學年"],
        "platform": ["2.5/4.0", "IELTS6.0", "限大學部", "1學期或1學年"],
    },
}


def compact(text):
    return re.sub(r"\s+", "", text).replace("-", "").lower()


def contains(text, *terms):
    missing = [term for term in terms if compact(term) not in compact(text)]
    if missing:
        raise ValueError(f"Missing expected evidence: {missing}")


def link(page, origin, *terms):
    return next(urljoin(origin, a["href"]) for a in page.select("a[href]")
                if all(t in a.get_text(" ", strip=True) for t in terms))


def read(session, url, log, *, pdf=False):
    start = time.perf_counter()
    response = session.get(url, timeout=(8, 35))
    response.raise_for_status()
    if pdf:
        if not response.content.startswith(b"%PDF"):
            raise ValueError(f"Expected PDF: {url}")
        text = subprocess.run(["pdftotext", "-layout", "-", "-"], input=response.content,
                              stdout=subprocess.PIPE, check=True).stdout.decode()
    else:
        text = BeautifulSoup(response.content, "html.parser")
    log.append({"url": response.url, "seconds": round(time.perf_counter() - start, 3)})
    return text


def official(session, case, log):
    announcement = read(session, NOTICE, log)
    contains(announcement.get_text(" ", strip=True), "115年10月23日17時", "116學年度")
    guide = read(session, link(announcement, NOTICE, "臺北大學116學年度赴外交換生申請簡章"), log, pdf=True)
    contains(guide, "最多可選5個志願")
    table = read(session, link(announcement, NOTICE, "116學年度交換名額一覽表(英文組)"), log, pdf=True)
    # Physical PDF cells can extend upward, so include the full row up to the next school.
    line = table.index(case["school"])
    start = table.rfind("\n\n", 0, line)
    end = table.index(case["end"], line)
    contains(table[start:end], *case["table"])


def platform(session, case, log):
    directory = read(session, DIRECTORY, log)
    partner = read(session, link(directory, DIRECTORY, case["school"], case["programme"]), log)
    main = partner.select_one("main")
    part = main.get_text(" ", strip=True).split("延伸比較與申請準備")[0]
    contains(part, "116學年度校內申請", "10/2317:00", "最多填列5個志願", *case["platform"])


def run():
    result = []
    for index in range(3):
        for case_name, case in CASES.items():
            order = (official, platform) if index % 2 == 0 else (platform, official)
            for route in order:
                log = []
                with requests.Session() as session:
                    begin = time.perf_counter()
                    route(session, case, log)
                    result.append({"trial": index + 1, "school": case_name, "route": route.__name__,
                                   "seconds": round(time.perf_counter()-begin, 3), "pages": log})
    return result


if __name__ == "__main__":
    print(json.dumps(run(), ensure_ascii=False, indent=2))
