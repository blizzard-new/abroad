"""Reopen institutional handoff screens for the exact targets from the student audit."""

import argparse
import json
import shutil
import time
from pathlib import Path
from urllib.parse import urlencode, urlsplit

from playwright.sync_api import Error as PlaywrightError
from playwright.sync_api import expect, sync_playwright
from run_student_journeys import capture_plan, enroll


def replay(browser, base, case):
    context = browser.new_context(reduced_motion="reduce", locale="zh-TW")
    home = case["home"]
    page = context.new_page()
    errors = []
    page.on("pageerror", lambda error: errors.append(str(error)))
    started = time.monotonic()
    try:
        enroll(context, base, home)
        response = context.request.post(
            base + "/account/application-paths",
            data={
                "home_school": home,
                "target_school": case["target"],
                "academic_year": "116",
                "application_round": "116-1（2027 秋季出國）"
                if case["id"] == "cgu"
                else "",
                "departure_year": "2027",
                "semester": "fall",
                "college": "管理學院",
                "department": "資訊管理學系",
                "degree_level": "大學部",
                "revision": 0,
            },
            timeout=120000,
        )
        assert response.ok, f"plan HTTP {response.status}: {response.text()[:200]}"
        data = response.json()
        plan_id = data["plan"]["id"]
        levels = [level for stage in data["stages"] for level in stage["levels"]]
        handoffs = [level for level in levels if level["kind"] == "submission"]
        assert handoffs, "No school handoff in this plan"
        page.add_init_script(
            "localStorage.setItem('exchange-guide-home-school',"
            + json.dumps(home)
            + ");sessionStorage.setItem('exchange-guide-browse-first','1')"
        )
        recorded = []
        for level in handoffs:
            route = urlencode({"plan": plan_id, "view": "level", "level": level["id"]})
            page.goto(
                base + "/?" + urlencode({"home": home}) + "#my-application?" + route,
                wait_until="domcontentloaded",
                timeout=120000,
            )
            page.locator("#boot-splash").wait_for(state="hidden", timeout=120000)
            pane = page.locator("#level-view")
            expect(pane.locator("#level-title")).to_be_visible(timeout=120000)
            expect(pane.locator("#level-title")).to_have_text(
                level["title"], timeout=120000
            )
            expect(pane.locator("#confirm-step")).to_have_text("我已送件")
            expect(
                pane.get_by_text("請依校方當期公告送件。完成官方送件後，再回來記錄。")
            ).to_be_visible(timeout=120000)
            links = pane.locator(".level-support a[href^=http]:visible").evaluate_all(
                "nodes => nodes.map(node => ({label:node.innerText.trim(),url:node.href}))"
            )
            assert links, f"No visible institutional source for {level['title']}"
            recorded.append(
                {
                    "title": level["title"],
                    "instructions": pane.locator(".task-question").inner_text(),
                    "source_links_displayed": links,
                    "warning": pane.locator(".ap-warning").all_inner_texts(),
                    "confirmation_button": "我已送件",
                }
            )
        saved = capture_plan(page, base, home, plan_id)
        assert all(
            not saved["plan"]["steps"].get(level["id"], {}).get("confirmed")
            for level in handoffs
        )
        assert not errors, errors
        return {
            "id": case["id"],
            "target": case["target"],
            "visible_handoffs": recorded,
            "submission_recorded_after_view": False,
            "page_errors": errors,
            "seconds": round(time.monotonic() - started, 2),
        }
    finally:
        context.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", default="http://127.0.0.1:8819")
    parser.add_argument(
        "--cases", type=Path, default=Path(__file__).with_name("student-journeys.jsonl")
    )
    parser.add_argument("--schools", nargs="*")
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    if urlsplit(args.base).hostname not in {"localhost", "127.0.0.1", "::1"}:
        parser.error(
            "Use a disposable loopback development server for synthetic students"
        )
    requested = set(args.schools or [])
    cases = [
        row
        for row in map(json.loads, args.cases.read_text().splitlines())
        if row["outcome"] == "prepared_sample_files"
        and (not requested or row["id"] in requested)
    ]
    if requested and requested != {row["id"] for row in cases}:
        parser.error("Requested a home without a preparable test case")
    failed = []
    complete = set()
    if args.out.exists():
        complete = {
            row["id"]
            for row in map(json.loads, args.out.read_text().splitlines())
            if "visible_handoffs" in row
        }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with (
        sync_playwright() as pw,
        args.out.open("a", encoding="utf-8", buffering=1) as out,
    ):
        browser = pw.chromium.launch(
            executable_path=shutil.which("chromium"),
            args=[
                "--disable-dev-shm-usage",
                "--blink-settings=imagesEnabled=false,webFontsEnabled=false",
                "--host-resolver-rules=MAP * ~NOTFOUND, EXCLUDE localhost, EXCLUDE 127.0.0.1, EXCLUDE [::1]",
            ],
        )
        for case in cases:
            if case["id"] in complete:
                continue
            try:
                row = replay(browser, args.base, case)
            except (AssertionError, PlaywrightError) as error:
                failed.append(case["id"])
                row = {"id": case["id"], "error": str(error)}
            print(json.dumps(row, ensure_ascii=False, separators=(",", ":")), file=out)
            print(row["id"], row.get("seconds", row.get("error")), flush=True)
        browser.close()
    if failed:
        raise SystemExit("Could not verify handoff for " + ", ".join(failed))


if __name__ == "__main__":
    main()
