"""Small mobile lab sample of public SEO pages; never labels it field Core Web Vitals."""
import argparse
import json
import os
from pathlib import Path

from playwright.sync_api import sync_playwright


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", default="https://app.uniway-tw.com")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    rows = []
    with sync_playwright() as runtime:
        executable = os.environ.get("PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH")
        browser = runtime.chromium.launch(headless=True, **({"executable_path": executable} if executable else {}))
        context = browser.new_context(viewport={"width": 390, "height": 844}, device_scale_factor=1, reduced_motion="reduce")
        page = context.new_page()
        for path in ("/schools", "/schools/ntpu", "/guides/exchange-budget", "/destinations/japan"):
            response = page.goto(args.base_url.rstrip("/") + path, wait_until="load")
            if response.status != 200:
                raise SystemExit(f"{path}: HTTP {response.status}")
            page.locator("h1").wait_for()
            metrics = page.evaluate("""() => {
              const n = performance.getEntriesByType('navigation')[0];
              const resources = performance.getEntriesByType('resource');
              return {ttfb_ms:n.responseStart-n.requestStart,dom_ready_ms:n.domContentLoadedEventEnd,
                html_bytes:n.decodedBodySize,resource_count:resources.length,
                js_bytes:resources.filter(r=>r.initiatorType==='script').reduce((n,r)=>n+r.decodedBodySize,0),
                horizontal_overflow:document.documentElement.scrollWidth>innerWidth};
            }""")
            rows.append({"path": path, **metrics})
        context.close()
        browser.close()
    result = {"mode": "mobile_lab_snapshot", "viewport": "390x844", "pages": rows,
              "limitation": "Single execution environment; not production p75, LCP/INP/CLS or a Google ranking result. Use field web-vitals samples and Search Console for those."}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False))
    if any(row["horizontal_overflow"] for row in rows):
        raise SystemExit("Horizontal overflow detected")


if __name__ == "__main__":
    main()
