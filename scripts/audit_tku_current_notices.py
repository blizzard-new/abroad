"""Record a reproducible, bounded negative audit without declaring unpublished data.

Read official entry pages and every public custom-news REST page since 2025-09-01.
Recheck reviewed current host pages; never promotes general forms or guesses a track.
"""
from __future__ import annotations

import argparse
import hashlib
import html
import json
import re
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
BUNDLE = ROOT / "src/exchange_info/official_data/tku"
BASE = "https://oieie.tku.edu.tw/oieie/"


def get(url, **params):
    response = requests.get(url, params=params or None, timeout=40)
    response.raise_for_status()
    return response, {"url":response.url, "final_url":response.url, "http_status":response.status_code,
                      "bytes":len(response.content), "sha256":hashlib.sha256(response.content).hexdigest(),
                      "checked_at":datetime.now(timezone.utc).isoformat()}


def page(url):
    response, record = get(url)
    rest = response.json() if "application/json" in response.headers.get("Content-Type", "") else None
    soup = BeautifulSoup(rest["content"]["rendered"] if rest and "content" in rest else response.content, "html.parser")
    record["title"] = html.unescape(rest["title"]["rendered"]) if rest and "title" in rest else soup.title.get_text(strip=True) if soup.title else ""
    links = []
    for anchor in soup.select("a[href]"):
        href = urljoin(response.url, anchor["href"])
        title = anchor.get_text(" ", strip=True)
        if "tkuisotope=" in href or any(word in title for word in ["英歐", "大陸", "金門", "中文組"]):
            links.append({"title":title, "url":href})
    record["notice_links"] = links
    record["pagination"] = [urljoin(response.url, anchor["href"]) for anchor in soup.select("a[href]")
                            if "paged=" in anchor["href"] or "page-numbers" in anchor.get("class", [])]
    content = soup.select_one("#content") or soup
    record["content_year_tokens"] = sorted(set(re.findall(r"202[5-8](?:[-–～~]202[6-9])?|11[56]學年度", content.get_text(" ", strip=True))))
    for element in soup.select("script,style,nav,header,footer"):
        element.decompose()
    record["extracted_text_sha256"] = hashlib.sha256(soup.get_text("\n",strip=True).encode()).hexdigest()
    return record


def audit(output):
    evidence = []
    with ThreadPoolExecutor(max_workers=4) as pool:
        evidence += list(pool.map(page, [BASE, BASE + "?page_id=55", BASE + "?page_id=19024",
                          *[BASE + "?post_type=tkuisotope&s=" + term for term in ["英歐", "中文", "大陸", "116", "2027"]]]))
    posts = []
    total_pages = 1
    number = 1
    while number <= total_pages:
        response, record = get(BASE, rest_route="/wp/v2/tkuisotope", per_page=100, page=number,
                               after="2025-09-01T00:00:00", before="2026-10-09T00:00:00",
                               _fields="id,date,modified,link,title")
        total_pages = int(response.headers["X-WP-TotalPages"])
        record.update(total_records=int(response.headers["X-WP-Total"]), total_pages=total_pages, page=number)
        record["entries"] = [{"id":item["id"], "published":item["date"], "modified":item["modified"],
                              "url":urljoin(BASE,item["link"]), "title":html.unescape(item["title"]["rendered"])} for item in response.json()]
        posts += record["entries"]
        evidence.append(record)
        number += 1
    sources = {row["id"]:row for row in json.loads((BUNDLE / "sources.json").read_text())}
    ids = ["english-115", "mainland-115", "english-second-115", "jp-revision",
           "nagasaki-nics-2027", "nagasaki-partners", "nagasaki-form-a-online", "uec-application-recheck",
           "uec-courses", "seikei-host", "ritsumeikan-howto-2027"]
    with ThreadPoolExecutor(max_workers=4) as pool:
        rechecks = list(pool.map(page, [sources[id]["source_url"] for id in ids]))
    for id, record in zip(ids, rechecks):
        record.update(source_id=id, reviewed_applicable_year=sources[id]["applicable_year"],
                      reviewed_role=sources[id]["role"], same_bytes_as_snapshot=record["sha256"] == sources[id]["sha256"])
        record["same_extracted_text_as_snapshot"] = record["extracted_text_sha256"] == hashlib.sha256(sources[id].get("text", "").encode()).hexdigest()
    evidence += rechecks
    first = page(BASE + "?rest_route=/wp/v2/tkuisotope/22353")
    first.update(scope="same-year earlier Japanese round; closed March 1 2026, not the September second-round school list",
                 content_review="公告內文：學生2026/2/23–3/1 17:00、系所3/2 17:00；指向2/23更新PDF與旧入口。是已結束前一梯，不加入四校最新二甄。")
    evidence.append(first)
    for url in ["https://www.oieie.tku.edu.tw/zh_tw/news/OverseasStudents", BASE + "wp-sitemap.xml"]:
        response = requests.get(url,timeout=40)
        evidence.append({"url":url,"final_url":response.url,"http_status":response.status_code,
                         "bytes":len(response.content),"sha256":hashlib.sha256(response.content).hexdigest(),
                         "checked_at":datetime.now(timezone.utc).isoformat(),"scope":"discovered prior-round legacy entrance / optional sitemap; failure is not evidence of unpublished data"})
    relevant = [post for post in posts if any(term in post["title"] for term in ["交換生", "Exchange Student", "exchange student"])]
    current_other_groups = [post for post in relevant if re.search(r"2027\s*[-–～~]\s*2028|116學年度",post["title"])
                            and any(term in post["title"] for term in ["英歐", "英語組", "中文組", "大陸", "金門", "澳門"])]
    report = {"checked_at":datetime.now(timezone.utc).isoformat(),
              "scope":"Public official TKU outbound entry pages, custom-news REST archive 2025-09-01 through 2026-10-08 (all returned pages), custom-news searches, and linked reviewed notices; no private/unpublished material.",
              "rest_total":len(posts), "rest_pages":total_pages, "rest_unique_ids":len({post["id"] for post in posts}),
              "evidence":evidence, "exchange_notice_metadata":relevant, "new_english_chinese_candidates":current_other_groups,
              "finding_status":"requires_content_review" if current_other_groups else "not_verified_new",
              "finding":("找到可能適用英歐／中文2027–2028的新公告，須人工查核內文及附件後才能更新當期資料。" if current_other_groups else
                  "查過的公開入口與完整日期範圍REST公告標題未找到英歐／中文2027–2028新甄選公告；既有英歐及中文簡章仍為115（2026–2027）。這是有界負面查核，不是官方明示尚未公告，也不證明所有網站或非公開檔案均無新版。"),
              "host_findings":[
                  {"source_ids":["nagasaki-nics-2027","nagasaki-partners","nagasaki-form-a-online"],"status":"needs_confirmation","finding":"NICS當期公告、2027表與淡江合作關係仍可查；公開頁未明示淡江這次提名必對應NICS或研究生適用，不提升映射狀態。"},
                  {"source_ids":["uec-application-recheck","uec-courses"],"status":"not_verified_new","finding":"一般JUSST申請頁仍為2025更新與一般表單；課表入口為2026，不當作2027專屬版。"}],
              "conflicts_checked":[{"id":row["id"],"status":row["status"],"basis":row["basis"],"source_ids":row.get("source_ids",[]),"source_urls":row["source_urls"],"checked_at":row["checked_at"]} for row in json.loads((BUNDLE/"conflicts.json").read_text())]}
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({"output":str(output),"sources_checked":len(evidence),"rest_records":len(posts),"rest_pages":total_pages,"new_candidates":current_other_groups,"changed_snapshots":[row["source_id"] for row in rechecks if not row["same_bytes_as_snapshot"]]}, ensure_ascii=False))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output",type=Path,required=True)
    audit(parser.parse_args().output)
