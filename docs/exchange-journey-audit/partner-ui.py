"""Audit every public partner page linked by the local /schools directory in Chromium.

Run from the repository root with the development server already running:
    .venv/bin/python docs/exchange-journey-audit/partner-ui.py --base http://127.0.0.1:8819
The browser fetches the actual HTML and checks its DOM. No school website is contacted.
"""
import argparse
import asyncio
import csv
from collections import Counter
import gzip
import io
import json
from pathlib import Path
import shutil
from urllib.parse import urlsplit

from playwright.async_api import async_playwright


OUT = Path(__file__).resolve().parent
FIELDS = [
    "home_id", "path", "partner", "http", "programs", "official_links",
    "application_section", "application_tab_links", "result",
]
# The live student flow uses the SPA. Each public partner guide provides a deep
# link to that flow, with the relevant home and partner encoded independently.
BATCH = """async ({paths, home}) => Promise.all(paths.map(async path => {
    const res = await fetch(path);
    const doc = new DOMParser().parseFromString(await res.text(), 'text/html');
    const body = doc.querySelector('main');
    const h1 = body?.querySelector('h1')?.textContent || '';
    const link = body?.querySelector('a[href*="#school="]');
    const target = link && new URL(link.getAttribute('href'), location.origin);
    const partner = target && decodeURIComponent(target.hash.substring('#school='.length));
    const programs = Array.from(body?.querySelectorAll('section.programme') || []);
    const links = programs.flatMap(section => Array.from(section.querySelectorAll('a[data-official-source]')));
    const verdicts = [];
    if (!res.ok) verdicts.push('http-error');
    if (!partner || !h1.startsWith(partner)) verdicts.push('title-target-mismatch');
    if (target?.searchParams.get('home') !== home || !body?.querySelector('.lead')?.textContent.includes(home)) verdicts.push('home-mismatch');
    if (!programs.length || programs.some(section => !section.querySelector('h2')?.textContent.trim()
        || !section.querySelector('dd')?.textContent.trim())) verdicts.push('empty-program');
    if (!links.length) verdicts.push('no-program-source-link');
    const application = programs.some(section => Array.from(section.querySelectorAll('h3'))
        .some(title => /申請步驟|申請文件|申請程序/.test(title.textContent)));
    const targets = [];
    const tabLinks = programs.filter(section => {
        const a = section.querySelector('a[href$="&tab=application"]');
        if (!a) return false;
        const url = new URL(a.getAttribute('href'), location.origin);
        const args = new URLSearchParams(url.hash.slice(1));
        if (url.searchParams.get('home') !== home || !args.get('school') || args.get('tab') !== 'application') return false;
        targets.push(args.get('school'));
        return true;
    });
    if (!application || tabLinks.length !== programs.length) verdicts.push('missing-application-section-or-link');
    if (!targets.includes(partner)) verdicts.push('listed-partner-missing-from-application-links');
    return {path, partner, http: res.status, programs: programs.length, official_links: links.length,
        application_section: Number(application), application_tab_links: tabLinks.length, targets, result: verdicts.join('|') || 'ok'};
}))"""


async def run(args):
    base = args.base.rstrip("/")
    if urlsplit(base).hostname not in {"localhost", "127.0.0.1", "::1"}:
        raise ValueError("Use a local development server")
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(executable_path=shutil.which("chromium"))
        page = await browser.new_page()
        await page.goto(base + "/universities", wait_until="domcontentloaded", timeout=120000)
        registry = await page.evaluate("async () => (await fetch('/universities')).json()")
        if args.only:
            registry = [home for home in registry if home["id"] in args.only]
        args.parts.mkdir(exist_ok=True, parents=True)
        for home in registry:
            code = home["id"]
            part = args.parts / (code + ".json")
            if args.resume and part.exists():
                continue
            paths = await page.evaluate("""async id => {
                const res = await fetch('/schools/'+id);
                if (!res.ok) throw Error('directory HTTP '+res.status);
                const doc = new DOMParser().parseFromString(await res.text(), 'text/html');
                return [...new Set(Array.from(doc.querySelectorAll('a[href]'), a => a.getAttribute('href'))
                    .filter(url => url.startsWith('/schools/'+id+'/partners/')))];
            }""", code)
            if not paths:
                raise ValueError(f"Empty public directory for {code}")
            rows = []
            for start in range(0, len(paths), args.batch):
                rows.extend(await page.evaluate(BATCH, {"paths": paths[start:start+args.batch], "home": home["school_name"]}))
            expected = await page.evaluate("""async home => {
                const res = await fetch('/student-dashboard?' + new URLSearchParams({school: home, compact: 'true'}));
                if (!res.ok) throw Error('catalogue HTTP ' + res.status);
                return (await res.json()).partner_universities.map(row => row.school_name);
            }""", home["school_name"])
            targets = [name for row in rows for name in row.pop("targets")]
            if Counter(targets) != Counter(expected):
                raise ValueError(f"{code}: application links do not cover exactly the catalogue programmes")
            part.write_text(json.dumps([{"home_id": code, **row} for row in rows], ensure_ascii=False))
            print(code, len(rows), sum(row["result"] != "ok" for row in rows), flush=True)
        await browser.close()
    rows = [row for home in registry for row in json.loads((args.parts / (home["id"] + ".json")).read_text())]
    with args.out.open("wb") as file, gzip.GzipFile(fileobj=file, mode="wb", filename="", mtime=0) as packed:
        with io.TextIOWrapper(packed, encoding="utf-8", newline="") as data:
            writer = csv.DictWriter(data, fieldnames=FIELDS, lineterminator="\n")
            writer.writeheader()
            writer.writerows(rows)
    print(len(registry), "homes,", len(rows), "partner pages,", sum(row["result"] != "ok" for row in rows), "flagged")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", required=True)
    parser.add_argument("--parts", type=Path, default=Path("/tmp/uniway-partner-ui"))
    parser.add_argument("--out", type=Path, default=OUT / "partner-ui.csv.gz")
    parser.add_argument("--only", nargs="+", help="Audit the named home university IDs")
    parser.add_argument("--batch", type=int, default=4)
    parser.add_argument("--resume", action="store_true", help="Resume output parts only from the same revision and configuration")
    asyncio.run(run(parser.parse_args()))
