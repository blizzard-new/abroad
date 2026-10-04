"""Research missing public school details on each school's existing official host.

Search results are discovery only. Store exact, complete page-body sentences,
their final URL and read time. Never generate facts or publication approvals.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from exchange_info.life_context import OFFICIAL_THEME_PATTERNS, _on_official_host
from exchange_info.life_sources import read_life_page
from exchange_info.web_search import search_text

FIELDS = {"housing_summary": "housing", "cost_summary": "cost",
    "transport_summary": "transport", "campus_life_summary": "social"}
GAPS = re.compile(r"未公開|尚未|未取得|待補|未提供|未完成|無法.*核對")
NAV = re.compile(r"cookie|subscribe|privacy policy|copyright|read more|click here|skip to|"
    r"graduation ceremony|memorial lecture|inauguration|anniversary|consent", re.I)


def sentences(text: str) -> list[str]:
    values = []
    for line in text.splitlines():
        # Avoid splitting decimal prices, abbreviations or URLs mid-sentence.
        parts = re.split(r"(?<=[。！？])|(?<=[.!?])\s+(?=[A-Z])", line)
        for part in parts:
            part = part.strip()
            if (35 <= len(part) <= 850 and re.search(r"[.!?。！？][\"')）]?$", part)
                    and not NAV.search(part)):
                values.append(part)
    return list(dict.fromkeys(values))


def research(item: dict, archive: Path) -> dict:
    profile, partner = item["profile"], item["partner"]
    host = (urlsplit(partner.get("website") or "").hostname or "").removeprefix("www.")
    output = {"home_university": profile.get("home_university"), "school_name": profile["school_name"],
        "country": profile.get("country"), "missing_fields": item["fields"], "evidence": [], "pages": [],
        "method": "official_page_body_excerpts", "human_reviewed": False}
    if not host:
        output["status"] = "official_host_missing"
        return output
    known = [s["source_url"] for s in profile["sources"] if _on_official_host(s["source_url"], host)]
    found = search_text(f"site:{host} international exchange student accommodation living costs campus transport services",
        max_results=7, timeout_seconds=6)
    urls = list(dict.fromkeys([*known, *(r.get("href") or r.get("url") or "" for r in found)]))
    urls = [u for u in urls if _on_official_host(u, host)][:7]
    if not urls and partner.get("website"):
        urls = [partner["website"]]
    now = datetime.now(timezone.utc).isoformat()
    with ThreadPoolExecutor(max_workers=2) as pool:
        pages = list(pool.map(read_life_page, urls))
    for page in pages:
        if not page or not _on_official_host(page.final_url, host):
            continue
        output["pages"].append({"url": page.final_url, "title": page.title, "read_at": now})
        body = sentences(page.text)
        for field in item["fields"]:
            theme = FIELDS[field]
            patterns = [OFFICIAL_THEME_PATTERNS[theme]]
            if theme == "social":
                patterns.append(OFFICIAL_THEME_PATTERNS["campus_culture"])
            matches = [s for s in body if any(re.search(p, s, re.I) for p in patterns)]
            if theme == "cost":
                # Tuition, application fees and scholarship totals are not a living budget.
                matches = [s for s in matches if re.search(
                    r"living|rent|accommodation|housing|monthly|生活費|住宿費|房租|생활비|家賃", s, re.I)]
            for value in matches[:2]:
                output["evidence"].append({"field": field, "theme": theme, "text": value,
                    "url": page.final_url, "title": page.title, "read_at": now})
    output["status"] = "partial" if output["evidence"] else "no_usable_body_excerpt"
    key = re.sub(r"[^a-zA-Z0-9]", "_", host)
    (archive / f"{key}.json").write_text(json.dumps(output, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return output


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    objects = json.loads(args.input.read_text(encoding="utf-8"))
    partners = {(r["home"], r["data"]["school_name"]): r["data"] for r in objects if r["kind"] == "partner"}
    tasks = []
    for obj in objects:
        if obj["kind"] != "profile":
            continue
        profile = obj["data"]
        fields = [f for f in FIELDS if not profile.get(f) or GAPS.search(profile[f])]
        if fields:
            partner = partners.get((profile.get("home_university"), profile["school_name"]), {})
            tasks.append({"profile": profile, "partner": partner, "fields": fields})
    previous = json.loads(args.output.read_text(encoding="utf-8")) if args.output.exists() else []
    done = {(r["home_university"], r["school_name"]) for r in previous}
    tasks = [t for t in tasks if (t["profile"].get("home_university"), t["profile"]["school_name"]) not in done]
    archive = args.output.with_suffix("")
    archive.mkdir(parents=True, exist_ok=True)
    print(f"research schools: {len(tasks)}", flush=True)
    with ThreadPoolExecutor(max_workers=3) as pool:
        futures = [pool.submit(research, task, archive) for task in tasks]
        for future in as_completed(futures):
            try:
                row = future.result()
            except Exception as error:
                print(f"research error: {type(error).__name__}", flush=True)
                continue
            previous.append(row)
            temp = args.output.with_suffix(".tmp")
            temp.write_text(json.dumps(previous, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            temp.replace(args.output)
            print(f"{len(previous)} completed: {row['school_name']}; excerpts {len(row['evidence'])}", flush=True)


if __name__ == "__main__":
    main()
