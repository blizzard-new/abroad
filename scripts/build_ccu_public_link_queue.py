"""Screen discovered CCU host hrefs offline; never auto-fetch or infer policy."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from collections import Counter
from pathlib import Path
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

ROOT = Path(__file__).resolve().parents[1]
BUNDLE = ROOT / "src/exchange_info/official_data/ccu"


def canonical_url(url):
    # Fragments do not change the fetched document. Preserve scheme, slash,
    # semantic queries and different language paths; they are not proven aliases.
    parts = urlsplit(url.strip())
    query = [(k, v) for k, v in parse_qsl(parts.query, keep_blank_values=True)
             if not k.casefold().startswith("utm_")]
    return urlunsplit((parts.scheme.casefold(), parts.netloc.casefold(),
                      parts.path.replace(" ", "%20"), urlencode(sorted(query)), ""))


def screen(page, url, labels):
    text = (url + " " + " ".join(labels)).casefold()
    path = urlsplit(url).path.casefold()
    if re.search(r"/login/?|/cas/?login|/identity/login|[?&]authtarget(?:=|&|$)", url, re.IGNORECASE):
        return "excluded_auth_navigation", "登入／CMS導覽，不是已取得的學生個人申請表；不登入或繞過。", []
    if ("/portlets/menurad" in path or re.search(r"/news/application/(?:date|page)/", path)
        or page == 33 and "/campus/affairs/applications/" in path):
        return "excluded_navigation", "選單portlet或歷史分頁導覽；不把索引当學生申請規定。", []
    if re.search(r"\.(?:jpg|jpeg|png|gif|svg|mp3)$", path):
        return "deferred_media", "圖片／音訊不是可直接解析的政策文本；必要生活內容另從文字指引核對。", ["campus_life"]
    if ("/institutes-centres/" in path and page == 103
        or re.search(r"research-publications|research-facilities|research-and-development|fraunhofer|research-at-epita", path)):
        return "excluded_research", "研究／技術application或exchange用語，與incoming學生申請及生活指引無關。", []
    if re.search(r"outgoing|incoming-staff|staff.exchange|海外派遣|海外파견|파견|海外인턴십|學分認列", text):
        return "excluded_other_recipient", "可辨識為host出國生、職員或其他對象；不投影為CCU學生incoming條件。", []
    if re.search(r"traineeship|tu research-oriented|deep-bridge|tujp|apru virtual|雙聯|복수학위|giss/giws|gissgiws|intense.master|research internship|international.credit.mobility", text):
        return "excluded_other_program", "短期、實習、雙學位或其他計畫；本次校級學期交換適用未有依據。", []
    if (re.search(r"students.voice|photo.gallery|/events?/|/news/meet-our-students|why.choose|/incoming-exchange-students/from-", text)
        or page == 35 and "/english/application/" in path
        or page == 68 and re.search(r"inti international|academic exchange program concludes|asean student connectivity", text)
        or page == 50 and re.search(r"lecture evaluation|holiday|office hours|office hour|광화문|gwanghwamun|construction work|초청 프로그램 간사", text)):
        return "excluded_events_stories", "活動、故事、舊假日或招募訊息，不是本期必要申請或服務規定。", []
    if (re.search(r"bachelors-degree-programmes/application|masters-degree-programme/application|ph.d..online.application|online.ph.d..applications|application.form.sale.outlets|mca-admission|application-with-a-foreign-school-leaving", text)
        or page == 74 and "library" not in text
        or page == 73 and path == "/engineering/"
        or page == 80 and "/program/" in path
        or page == 105 and urlsplit(url).hostname == "uo.asbu.edu.tr"
        or page == 23 and "/en/admission/" in path
        or page == 37 and "graduate-admissions" in path):
        return "excluded_degree_program", "一般學位招生／系所介紹，不當作incoming交換可申請學院或學制。", []
    if re.search(r"library.strategy|sustainable.library|editorial.board|writing.publishing|research.teaching|interlibrary|/giving", text):
        return "deferred_general_library", "一般圖書館研究／行政服務，優先度低於交換申請和基本學生使用指引。", ["campus_life"]
    if re.search(r"201[0-9]|202[0-5]|2324|2026s|2026f|fall 2026|spring 2026", text):
        return "reference_candidate", "href或標籤提示舊期；正文尚未重讀，不能升級2027春季適用或宣稱尚未公告。", ["documents", "application_forms"]
    fields = []
    topic = path.rsplit("/", 2)[-2:] if path.endswith("/") else [path.rsplit("/", 1)[-1]]
    leaf = " ".join(topic) + " " + " ".join(labels).casefold()
    if "library" not in leaf and re.search(r"application|apply|nomination|learning.agreement|required.documentation|fact.?sheet|timeline", leaf):
        fields.extend(["documents", "application_forms"])
    if re.search(r"course|curriculum|bachelor|master|colleges|majors|exchange.program|exchange.student|deep-u", leaf):
        fields.extend(["college_scope", "degree_scope"])
    if re.search(r"transport|arrival|getting.started|preparing.for.your.stay|your.arrival", leaf):
        fields.append("transport")
    if re.search(r"housing|accommod|dorm|buddy|library|student.services|campus|orientation|support", leaf):
        fields.append("campus_life")
    return "public_candidate_requires_content_review", "僅已查href與來源上下文；須取得全文後分年度／計畫／校區，不等於政策已核。", list(dict.fromkeys(fields))


def build(output):
    path = BUNDLE / "remaining-gaps.json"
    report = json.loads(path.read_text())
    requests = json.loads((BUNDLE / "overseas-source-requests.json").read_text())
    sources = {r["source_id"]: r for r in json.loads((BUNDLE / "overseas-source-registry.json").read_text())}
    requested = {canonical_url(r["url"]): r["source_id"] for r in requests}
    grouped = {}
    for row in report["schools"]:
        for link in row["unrequested_discovered_links"]:
            url = canonical_url(link["url"])
            grouped.setdefault(url, []).append(dict(link, ccu_page=row["ccu_page"]))
    candidates = []
    schools = []
    for url, occurrences in grouped.items():
        pages = sorted({o["ccu_page"] for o in occurrences})
        labels = list(dict.fromkeys(o["label"] for o in occurrences))
        disposition, reason, fields = screen(pages[0], url, labels)
        if url in requested:
            disposition, reason = "already_requested", "同一去fragment／tracking href已有取得紀錄；不重抓，結果與限制見source registry。"
        gaps = {r["ccu_page"]: r["gaps"] for r in report["schools"] if r["ccu_page"] in pages}
        target_fields = sorted({f for page in pages for f in fields if f in gaps[page]})
        priority = sum(5 if f in {"documents", "application_forms"} else 3 if "scope" in f else 1 for f in target_fields)
        if disposition != "public_candidate_requires_content_review":
            priority = 0
        candidates.append({
            "candidate_id": "ccu-link-" + hashlib.sha256(url.encode()).hexdigest()[:16],
            "url": url, "ccu_pages": pages, "labels": labels, "occurrences": occurrences,
            "disposition": disposition, "screening_reason": reason,
            "target_gap_fields": target_fields, "priority_score": priority,
            "source_content_read": None if url in requested else False,
            "source_availability": sources[requested[url]]["status"] if url in requested else "unrequested",
            "already_requested_source_id": requested.get(url),
        })
    candidates.sort(key=lambda c: (-c["priority_score"], c["ccu_pages"], c["url"]))
    for row in report["schools"]:
        related = [c for c in candidates if row["ccu_page"] in c["ccu_pages"]]
        schools.append({
            "ccu_page": row["ccu_page"], "school_name": row["school_name"],
            "gap_fields": list(row["gaps"]),
            "checked_source_ids": [s["source_id"] for s in row["checked_sources"]],
            "source_access_constraints": row["document_access_constraints"],
            "candidate_ids_by_disposition": {
                status: [c["candidate_id"] for c in related if c["disposition"] == status]
                for status in sorted({c["disposition"] for c in related})
            },
            "public_sources_exhausted": False,
        })
    result = {
        "checked_date": "2026-10-08", "scope": "CCU2027春季55校學生必要資料；候選href篩查非正文政策查核。",
        "input_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "canonicalization": "移除fragment/utm，排序query，空白path編碼；HTTP/HTTPS、尾slash、index及語言不同不當已證同頁。",
        "raw_href_count": sum(len(c["occurrences"]) for c in candidates),
        "unique_url_count": len(candidates),
        "collapsed_href_count": sum(len(c["occurrences"]) - 1 for c in candidates),
        "disposition_counts": dict(Counter(c["disposition"] for c in candidates)),
        "schools": schools, "candidates": candidates,
    }
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({k: result[k] for k in ["raw_href_count", "unique_url_count", "collapsed_href_count", "disposition_counts"]}))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=BUNDLE / "public-link-queue.json")
    build(parser.parse_args().output)
