"""Read-only post-deployment SEO smoke check (no Google credentials required)."""
from __future__ import annotations

import argparse
import json
import re
import time
from pathlib import Path
from datetime import datetime, timezone
from urllib.parse import urlsplit
from xml.etree import ElementTree

import requests
from bs4 import BeautifulSoup


def check_site(base: str, canonical: str, *, all_pages: bool = False, delay: float = 0.2) -> dict:
    session = requests.Session()
    session.headers["User-Agent"] = "UniWay-SEO-Check/1.0 (operator verification)"
    count = 0
    timings = []

    def fetch(path):
        nonlocal count
        if count:
            time.sleep(delay)
        count += 1
        started = time.monotonic()
        response = session.get(base + path, timeout=30, allow_redirects=False)
        timings.append({"path": path, "response_ms": round((time.monotonic() - started) * 1000, 1), "bytes": len(response.content)})
        if response.status_code != 200:
            raise ValueError(f"{path}: expected 200, got {response.status_code}")
        return response

    def path_for(url):
        if not url.startswith(canonical + "/") or urlsplit(url).query or urlsplit(url).fragment:
            raise ValueError(f"Unexpected sitemap URL: {url}")
        return url[len(canonical):]

    def sitemap(path, expected_root):
        response = fetch(path)
        if "application/xml" not in response.headers.get("content-type", ""):
            raise ValueError(f"{path}: XML Content-Type missing")
        root = ElementTree.fromstring(response.content)
        if root.tag != f"{{http://www.sitemaps.org/schemas/sitemap/0.9}}{expected_root}":
            raise ValueError(f"{path}: invalid sitemap root")
        urls = [node.text for node in root.findall(".//{*}loc")]
        if not urls or len(urls) != len(set(urls)):
            raise ValueError(f"{path}: empty sitemap or duplicate URLs")
        for node in root.findall(".//{*}lastmod"):
            try:
                stamp = datetime.fromisoformat((node.text or "").replace("Z", "+00:00"))
                if stamp.tzinfo is None:
                    stamp = stamp.replace(tzinfo=timezone.utc)
                if stamp > datetime.now(timezone.utc):
                    raise ValueError("future lastmod")
            except ValueError as error:
                raise ValueError(f"{path}: invalid lastmod {node.text!r}") from error
        return [path_for(url) for url in urls]

    def html(path):
        response = fetch(path)
        soup = BeautifulSoup(response.text, "html.parser")
        if "noindex" in response.headers.get("X-Robots-Tag", "").lower():
            raise ValueError(f"{path}: X-Robots-Tag prevents indexing")
        robots = soup.select_one('meta[name="robots"]')
        if robots and "noindex" in robots.get("content", "").lower():
            raise ValueError(f"{path}: meta robots prevents indexing")
        links = soup.select('link[rel="canonical"]')
        if len(links) != 1 or links[0].get("href") != canonical + path:
            raise ValueError(f"{path}: canonical does not match")
        if not soup.title or not soup.select_one('meta[name="description"]'):
            raise ValueError(f"{path}: title/description missing")
        if path.startswith(("/schools", "/destinations", "/guides", "/editorial-policy")) and (len(soup.select("h1")) != 1 or not soup.select_one("main a")):
            raise ValueError(f"{path}: server-rendered content missing")
        graph_types = set()
        for schema in soup.select('script[type="application/ld+json"]'):
            graph_types |= {node.get("@type") for node in json.loads(schema.string).get("@graph", [])}
        if path == "/" and not {"Organization", "WebSite"} <= graph_types:
            raise ValueError("/: Organization and WebSite structured data missing")

    def llms(page_paths):
        response = fetch("/llms.txt")
        if not response.headers.get("content-type", "").startswith("text/plain"):
            raise ValueError("/llms.txt: expected text/plain")
        if not response.text.startswith("# UniWay\n"):
            raise ValueError("/llms.txt: missing H1 title")
        links = re.findall(r"\]\((https?://[^)\s]+)\)", response.text)
        # Every page it advertises must be a public page the sitemap already lists.
        unlisted = [url for url in links if url != canonical + "/sitemap.xml" and url.removeprefix(canonical) not in page_paths]
        if not links or unlisted:
            raise ValueError(f"/llms.txt: links outside the sitemap: {unlisted[:3]}")
        return len(links)

    robots = fetch("/robots.txt").text
    # Only the "*" group decides whether ordinary crawlers are blocked; named AI-crawler groups may close "/" on purpose.
    wildcard = next((g.splitlines() for g in robots.split("\n\n") if "User-agent: *" in g.splitlines()), [])
    if f"Sitemap: {canonical}/sitemap.xml" not in robots or "Disallow: /" in wildcard:
        raise ValueError("robots.txt blocks crawling or does not advertise the canonical sitemap")
    children = sitemap("/sitemap.xml", "sitemapindex")
    inventory, sampled, page_paths = {}, [], set()
    for child in children:
        paths = sitemap(child, "urlset")
        inventory[child] = len(paths)
        if child == "/sitemaps/pages.xml":
            page_paths = set(paths)
        selected = paths if all_pages or child == "/sitemaps/pages.xml" else paths[:1]
        for path in selected:
            html(path)
            sampled.append(path)
        print(f"Checked {child}: {len(paths)} URLs; {len(selected)} HTML pages", flush=True)
    llms_links = llms(page_paths)
    return {"base_url": base, "canonical_origin": canonical, "sitemaps": inventory, "llms_txt_links": llms_links,
            "indexed_url_candidates": sum(inventory.values()), "html_pages_checked": len(sampled),
            "all_pages": all_pages, "requests": count, "result": "passed", "response_timings": timings,
            "scope": "HTTP and HTML checks; not evidence of Google indexing or rankings"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", default="https://app.uniway-tw.com")
    parser.add_argument("--canonical-origin", default="https://app.uniway-tw.com")
    parser.add_argument("--all-pages", action="store_true", help="Fetch every partner page; use on staging first")
    parser.add_argument("--delay", type=float, default=0.2, help="Seconds between requests; no parallel load")
    parser.add_argument("--json-output", type=Path, help="Save structured deployment evidence")
    args = parser.parse_args()
    if args.delay < 0:
        parser.error("--delay cannot be negative")
    try:
        report = check_site(args.base_url.rstrip("/"), args.canonical_origin.rstrip("/"), all_pages=args.all_pages, delay=args.delay)
    except (requests.RequestException, ValueError, ElementTree.ParseError) as error:
        parser.exit(1, f"SEO check failed: {error}\n")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if args.json_output:
        args.json_output.parent.mkdir(parents=True, exist_ok=True)
        args.json_output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
