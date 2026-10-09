"""Save CCU's public Mapua/UNINTER dynamic pages without answering any form.

This acquisition script writes outside the repository. It does not decide
policy applicability or overwrite saved source records. Calendar images need
visual review, and PDF/DOM bodies need separate semantic and year checks.
"""

import argparse
import asyncio
import base64
import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path

import requests
from playwright.async_api import async_playwright

MAPUA = "https://www.mapua.edu.ph/"
ILRAD = MAPUA + "pages/about-mapua/partners-and-linkages/international-linkages-relations-and-development-cooperation-ilrad"
CALENDAR = MAPUA + "pages/academics/academic-calendar-and-handbook"
FORM = "https://forms.office.com/r/dBVPQn8y5n"
ROOT = Path(__file__).resolve().parents[1]


async def acquire(output):
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()

        async def save(name, action):
            html = (await page.content()).encode()
            text = await page.locator("body").inner_text()
            (output / (name + ".html")).write_bytes(html)
            (output / (name + ".txt")).write_text(text)
            proof = {
                "checked_at": datetime.now(UTC).isoformat(),
                "url": page.url, "title": await page.title(), "action": action,
                "sha256": hashlib.sha256(html).hexdigest(),
                "https_certificate_errors_ignored": False,
                "answers_entered": False, "submitted": False,
                "links": await page.locator("a[href]").evaluate_all(
                    "as => as.map(a => ({text: a.innerText, url: a.href}))"
                ),
            }
            (output / (name + ".json")).write_text(json.dumps(proof, ensure_ascii=False, indent=2))

        try:
            for name, url in [("mapua-root", MAPUA), ("uninter-form", FORM)]:
                # A successful HTTP read does not verify the browser-rendered
                # body. Certificate failures stop this path without bypass.
                response = await asyncio.to_thread(requests.get, url, timeout=30, verify=True)
                response.raise_for_status()
                (output / (name + "-verified-tls.html")).write_bytes(response.content)
                await page.goto(url, wait_until="domcontentloaded", timeout=30000)
                await page.wait_for_timeout(4000)
                await save(name, "Public page read only")
                if name == "uninter-form":
                    await page.get_by_role("button", name="Start now", exact=True).click()
                    await page.get_by_role("button", name="Submit", exact=True).wait_for(timeout=30000)
                    await save("uninter-questions", "Start now opens questions; no answers or Submit click")
            await page.goto(ILRAD, wait_until="domcontentloaded", timeout=30000)
            await page.wait_for_timeout(2000)
            await save("mapua-ilrad", "Public contact tab")
            for name, label, expected in [
                ("visa", "Visa Requirements", "What type of visa I need"),
                ("application", "Application Process for Degree and Non-Degree Seeking Students", "Lead time for application of non-degree"),
                ("dormitories", "Dormitories", "USD500 per month"),
                ("handbook", "International Handbook & Programs", "International HandBook Online"),
            ]:
                await page.get_by_role("button", name=label, exact=True).click()
                await page.get_by_text(expected, exact=False).first.wait_for(state="visible", timeout=15000)
                await page.wait_for_timeout(1500)
                await save("mapua-" + name, "Public tab: " + label)
                if name == "handbook":
                    link = page.get_by_role("link", name="International HandBook Online", exact=False)
                    url = await link.get_attribute("href")
                    response = await asyncio.to_thread(requests.get, url, timeout=30, verify=True)
                    response.raise_for_status()
                    (output / "mapua-international-handbook.pdf").write_bytes(response.content)
            await page.goto(CALENDAR, wait_until="domcontentloaded", timeout=30000)
            await page.get_by_text("College Academic Calendar Schedule A.Y. 2026-2027", exact=True).click()
            await page.wait_for_timeout(1500)
            await save("mapua-calendar", "Open current college calendar; other academic levels remain separate")
            box = page.locator("h3").filter(has_text="College Academic Calendar Schedule A.Y. 2026-2027").locator("..").locator("..")
            data = await box.locator("img").first.get_attribute("src")
            if data and data.startswith("data:image/jpeg;base64,"):
                (output / "mapua-calendar.jpg").write_bytes(base64.b64decode(data.split(",", 1)[1]))
        finally:
            await browser.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    output = args.output.resolve()
    if output.is_relative_to(ROOT):
        parser.error("Save research evidence outside the clone")
    output.mkdir(parents=True, exist_ok=True)
    asyncio.run(acquire(output))


if __name__ == "__main__":
    main()
