"""Exercise one real student browser session per home on an isolated development server.

Run with a disposable local server, real catalogue and development email codes.
Synthetic sample files exercise storage, never the validity of an official document.
"""

import argparse
import json
import re
import shutil
import time
from collections import Counter
from pathlib import Path
from urllib.parse import quote, urlencode, urlsplit
from uuid import uuid4

import requests
from playwright.sync_api import Error as PlaywrightError
from playwright.sync_api import expect, sync_playwright

expect.set_options(timeout=30000)

PROFILE = {
    "college": "管理學院",
    "department": "資訊管理學系",
    "degree_level": "大學部",
    "current_year": "大二",
    "academic_score": "88",
    "academic_gpa": "3.7",
    "class_rank_percent": "15",
    "language_test": "ielts",
    "language_score": "7",
    "jlpt_level": "N2",
    "application_round": "第一梯次",
}


def enroll(context, base, home):
    # Only account setup uses the API. All actions measured below are on student pages.
    email = f"journey-{uuid4().hex[:12]}@example.com"
    api = context.request

    def post(path, data):
        response = api.post(base + path, data=data)
        assert response.ok, f"{path} HTTP {response.status}"
        return response.json()

    code = post("/auth/email-verification/request", {"email": email})[
        "development_code"
    ]
    token = post("/auth/email-verification/confirm", {"email": email, "code": code})[
        "verification_token"
    ]
    post(
        "/auth/register",
        {
            "email": email,
            "password": uuid4().hex + "Q!",
            "display_name": "交換準備測試生",
            "email_verification_token": token,
            "accept_terms": True,
        },
    )
    response = api.patch(base + "/auth/me", data={"home_university": home})
    assert response.ok, f"home school setup HTTP {response.status}"
    assert response.json()["catalog_home_university"] == home


def record_tabs(page):
    texts = {}
    for key in ("overview", "application", "life", "prep", "experiences", "community"):
        page.locator(f"#detail-tab-{key}").click()
        panel = page.locator(f"#detail-{key}")
        expect(panel).to_be_visible()
        texts[key] = len(panel.inner_text().strip())
    return texts


def capture_plan(page, base, home, plan_id):
    response = page.request.get(
        base + "/account/application-paths/" + plan_id,
        params={"home_school": home},
        timeout=120000,
    )
    assert response.ok, f"reread plan HTTP {response.status}"
    return response.json()


def upload_to_level(page, school_id, level):
    label = level["title"]
    contents = f"合成測試文件，僅供檔案傳遞驗證。\n{school_id} · {label}\n".encode()
    page.locator(".ap-upload summary").click()
    page.locator("#path-file").set_input_files(
        {
            "name": f"{school_id}-{level['number']}.txt",
            "mimeType": "text/plain",
            "buffer": contents,
        }
    )
    page.locator("#file-consent").check()
    with page.expect_response(
        lambda r: (
            r.request.method == "POST" and r.url.endswith("/account/vault/documents")
        )
    ) as saved:
        page.locator("#upload-file").click()
    assert saved.value.ok, f"vault upload HTTP {saved.value.status}"
    expected_version = saved.value.json()["versions"][-1]["id"]
    expect(page.locator("#file-version")).to_have_value(
        expected_version, timeout=120000
    )
    expect(page.locator("#save-note")).to_have_text("已儲存", timeout=120000)
    return contents


def read_saved_document(page, base, doc, expected):
    response = page.request.get(base + "/account/vault/documents")
    assert response.ok
    item = next(
        item
        for item in response.json()["items"]
        if any(v["id"] == doc for v in item["versions"])
    )
    version = next(v for v in item["versions"] if v["id"] == doc)
    path = f"/account/vault/versions/{version['id']}"
    grant = page.request.post(base + path + "/download-grant")
    assert grant.ok, f"download grant HTTP {grant.status}"
    download = page.request.post(
        base + grant.json()["download_url"],
        headers={"X-Vault-Download-Token": grant.json()["token"]},
    )
    assert download.ok and download.body() == expected, (
        f"download bytes HTTP {download.status}"
    )


def open_task(page, title, step_id):
    encoded = quote(step_id, safe="")
    row = page.locator(f'#overview-stages a.task-row[href*="level={encoded}&"]').first
    group = row.locator("xpath=ancestor::details[1]")
    if group.get_attribute("open") is None:
        group.locator("summary").click()
    row.click()
    expect(page.locator("#level-title")).to_have_text(title)


def evaluate_eligibility(page):
    open_task(page, "申請資格", "checks")
    fields = page.locator("#gate-inputs[data-state=missing] [name]")
    for control in fields.all():
        key = control.get_attribute("name")
        if key not in PROFILE or control.input_value():
            continue
        if control.evaluate("e => e.tagName") == "SELECT":
            control.select_option(PROFILE[key])
        else:
            control.fill(PROFILE[key])
    if fields.count():
        page.locator("#gate-save").click()
        expect(page.locator("#gate-inputs[data-state=missing]")).to_have_count(
            0, timeout=30000
        )
    checks = page.locator("#level-view [data-check]").evaluate_all(
        "es => es.map(e => ({rule:e.dataset.check,status:e.querySelector('b').textContent}))"
    )
    # Acknowledge reading the judgement, including any unknowns, without claiming acceptance.
    confirm = page.locator("#confirm-step")
    if confirm.is_visible():
        confirm.click()
    else:
        page.locator("#level-view a.back-link").click()
    expect(page.locator("#today-view")).to_be_visible(timeout=120000)
    return checks


def run_student(browser, base, school, *, sample=False, target=None):
    home, code = school["school_name"], school["id"]
    result = {
        "file_scope": "one plan item"
        if sample
        else "all unconditional preparation items",
        "id": code,
        "home": home,
        "actions": [],
        "documents": [],
        "deferred": [],
        "writing_sections": 0,
        "page_errors": [],
    }
    ctx = browser.new_context(
        viewport={"width": 1400, "height": 930},
        reduced_motion="reduce",
        accept_downloads=True,
        locale="zh-TW",
        timezone_id="Asia/Taipei",
    )
    page = ctx.new_page()
    # The separate visual census captures images. Avoid hundreds of campus photos and
    # CJK font shards per isolated account when evaluating document persistence.
    net = ctx.new_cdp_session(page)
    net.send("Network.enable")
    net.send(
        "Network.setBlockedURLs",
        {
            "urls": [
                "*.woff2*",
                "*.woff*",
                "*.webp*",
                "*.jpg*",
                "*.png*",
                "*.avif*",
                "*.jpeg*",
                "*.mp4*",
            ]
        },
    )
    page.set_default_timeout(45000)
    page.set_default_navigation_timeout(120000)
    page.on("pageerror", lambda e: result["page_errors"].append(str(e)))
    # The audit visits platform pages. Photos and third-party analytics are outside the measured task.
    # Count actual page input events across reloads; file choice, fill and select changes count once.
    page.add_init_script("""(() => {
      function count(key) { const k = "audit-" + key; sessionStorage.setItem(k, String(1 + Number(sessionStorage.getItem(k)))); }
      document.addEventListener("click", e => { if (e.isTrusted && e.target.closest("a,button,summary,label,input[type=radio],input[type=checkbox]")) count("clicks"); }, true);
      document.addEventListener("change", e => { if (e.isTrusted && e.target.matches("textarea,select,input:not([type=radio]):not([type=checkbox])")) count("field_changes"); }, true);
    })()""")
    started = time.monotonic()

    def log(action):
        result["actions"].append(action)
        print(code, action, round(time.monotonic() - started, 2), flush=True)

    try:
        enroll(ctx, base, home)
        # Start as a returning student with the same preselected home in account and browser.
        page.add_init_script(
            "localStorage.setItem('exchange-guide-home-school',"
            + json.dumps(home)
            + ");"
            "sessionStorage.setItem('exchange-guide-browse-first','1')"
        )
        # Follow the public search link for a known target. The student still uses the
        # real results, catalogue eligibility policy and school page controls.
        catalogue_query = {"view": "list", "home": home}
        if sample:
            compact = ctx.request.get(
                base + "/student-dashboard",
                params={"school": home, "compact": "true"},
                timeout=120000,
            )
            assert compact.ok, f"catalogue setup HTTP {compact.status}"
            rows = compact.json()["partner_universities"]
            if rows:
                interest = next(
                    (r for r in rows if r.get("availability_status") == "open"), rows[0]
                )
                catalogue_query["q"] = target or interest["school_name"]
        started = time.monotonic()
        page.goto(
            base + "/?" + urlencode(catalogue_query) + "#partners",
            wait_until="domcontentloaded",
        )
        print(
            code,
            "loaded",
            page.locator("#school-switcher-label").inner_text(),
            page.url,
            flush=True,
        )
        expect(page.locator("#school-switcher-label")).to_have_text(
            home, timeout=120000
        )
        page.wait_for_function(
            "home => state.dashboard?.school_name === home && !state.homeSchoolLoading",
            arg=home,
            timeout=120000,
        )
        page.locator("#boot-splash").wait_for(state="hidden", timeout=120000)
        if not page.locator("#partners").is_visible():
            page.locator('#glass-navigation a[data-public-route="partners"]').click()
        log("open_school_catalogue")
        candidates = page.evaluate("""() => state.dashboard.partner_universities.map(p=>({
            name:p.school_name, country:p.country, ...partnerAvailabilityMeta(p)}))""")
        result["catalogue_rows"] = len(candidates)
        open_rows = [row for row in candidates if not row["blocked"]]
        result["can_start_rows"] = len(open_rows)
        if not candidates:
            result["outcome"] = "empty_catalogue"
            return result
        # Prefer currently usable status, then keep official catalogue order.
        selected = next(
            (row for row in open_rows if not row.get("pending")),
            (open_rows or candidates)[0],
        )
        if target:
            selected = next(row for row in candidates if row["name"] == target)
        name = selected["name"]
        result.update(
            {
                "target": name,
                "country": selected["country"],
                "availability": selected["status"],
            }
        )
        list_button = page.locator('[data-partner-view="list"]')
        if (
            list_button.is_visible()
            and list_button.get_attribute("aria-pressed") != "true"
        ):
            list_button.click()
        page.locator("#partner-search").fill(name)
        name_literal = json.dumps(name, ensure_ascii=False)
        page.locator(
            f"#partner-table .school-detail-trigger[data-school-name={name_literal}]:visible"
        ).first.click()
        expect(page.locator("#school-detail-title")).to_have_text(name, timeout=30000)
        log("search_and_open_partner")
        page.locator("#detail-favorite-button").click()
        expect(page.locator("#detail-favorite-button")).to_have_attribute(
            "aria-pressed", "true"
        )
        log("save_favorite")
        if sample:
            page.locator("#detail-tab-application").click()
            expect(page.locator("#detail-application")).to_be_visible()
            log("read_application_method")
        else:
            result["tab_visible_characters"] = record_tabs(page)
            log("read_six_partner_tabs")
        if selected["blocked"]:
            expect(page.locator("#detail-application-button")).to_be_disabled()
            result["reason"] = page.locator("#detail-application-button").get_attribute(
                "title"
            )
            result["outcome"] = (
                "target_blocked" if open_rows else "catalogue_has_no_eligible_start"
            )
            return result
        page.locator("#detail-application-button").click()
        expect(page.locator("#detail-application-button")).to_have_attribute(
            "aria-pressed", "true"
        )
        page.locator("#detail-prepare-plan-button").click()
        expect(page.locator("#plan-dialog")).to_be_visible(timeout=120000)
        expect(page.locator("#create-target")).to_have_value(name)
        log("add_preference_and_open_my_application")
        page.locator('#create-semesters input[value^="fall:"]').first.locator(
            ".."
        ).click()
        if not page.locator("#create-college").is_visible():
            page.locator(".ap-academic-fields summary").click()
        for key in ["college", "department", "degree"]:
            page.locator("#create-" + key).fill(
                PROFILE.get(key, PROFILE["degree_level"])
            )
        with page.expect_response(
            lambda r: (
                r.request.method == "POST"
                and r.url.endswith("/account/application-paths")
            ),
            timeout=120000,
        ) as response:
            page.locator("#plan-form button[type=submit]").click()
        saved = response.value
        assert saved.ok, f"create plan HTTP {saved.status} {saved.text()[:160]}"
        plan_id = saved.json()["plan"]["id"]
        expect(page.locator("#today-view")).to_be_visible(timeout=120000)
        log("create_targeted_plan")
        plan = saved.json()
        levels = [item for stage in plan["stages"] for item in stage["levels"]]
        result["plan_levels"] = dict(Counter(item["kind"] for item in levels))
        result["step_checks"] = dict(
            Counter(
                item.get("check_status") for item in levels if item.get("check_status")
            )
        )
        if result["step_checks"] and not sample:
            result["eligibility"] = evaluate_eligibility(page)
            log("review_eligibility")
        if not sample:
            plan = capture_plan(page, base, home, plan_id)
        levels = [item for stage in plan["stages"] for item in stage["levels"]]
        result["post_eligibility_level_types"] = dict(
            Counter(item["kind"] for item in levels)
        )
        files = [item for item in levels if item["kind"] == "file"]
        result["plan_file_basis"] = dict(
            Counter(item.get("document_basis", "catalogued") for item in files)
        )
        version_files = {}
        for level in levels:
            if sample and (
                level["kind"] in {"write", "assemble"}
                or (level["kind"] == "file" and version_files)
            ):
                continue
            if level["kind"] not in {
                "file",
                "write",
                "assemble",
                "submission",
                "notice",
            }:
                continue
            if level["kind"] == "notice" or level.get("external"):
                result["deferred"].append(
                    {"title": level["title"], "reason": "awaiting_school"}
                )
                continue
            if level["kind"] == "submission":
                result["deferred"].append(
                    {"title": level["title"], "reason": "official_submission"}
                )
                continue
            if level["kind"] == "file" and (
                (
                    level.get("conditional")
                    and not level.get("document_basis")
                    in {"reference_year", "personal"}
                )
                or re.search(
                    r"返國|出發|行前|入學後|抵達|歸國|回國|錄取後|提名後",
                    level.get("stage_key", ""),
                )
            ):
                result["deferred"].append(
                    {"title": level["title"], "reason": "conditional_or_later_stage"}
                )
                continue
            open_task(page, level["title"], level["id"])
            if level["kind"] == "file":
                if level.get("conditional"):
                    page.locator("#file-applicable").select_option("yes")
                    expect(page.locator("#save-note")).to_have_text(
                        "已儲存", timeout=120000
                    )
                content = upload_to_level(page, code, level)
                version = page.locator("#file-version").input_value()
                assert version
                version_files[level["id"]] = (version, content)
            elif level["kind"] == "write":
                page.locator("#level-input").fill(
                    "模擬學生的交換研修計畫。"
                    + level["title"]
                    + "：希望研習跨國課程，返國後完成成果分享。"
                )
            elif level["kind"] == "assemble":
                with page.expect_download() as artifact:
                    page.locator("#download-writing").click()
                assert "模擬學生" in Path(artifact.value.path()).read_text()
                log("download_written_plan")
            page.locator("#confirm-step").click()
            expect(page.locator("#today-view")).to_be_visible(timeout=30000)
            if level["kind"] == "file":
                result["documents"].append(level["title"])
                result.setdefault("uploaded_file_basis", []).append(
                    level.get("document_basis", "catalogued")
                )
            elif level["kind"] == "write":
                result["writing_sections"] += 1
        if not sample:
            page.reload(wait_until="domcontentloaded")
            expect(page.locator("#today-view")).to_be_visible(timeout=120000)
        latest = capture_plan(page, base, home, plan_id)
        for id_, (version, content) in version_files.items():
            entry = latest["plan"]["steps"][id_]
            assert entry["version_id"] == version and entry["confirmed"]
            if not sample:
                read_saved_document(page, base, version, content)
        result["verified_saved_files"] = len(version_files)
        if sample and version_files:
            first_id = next(iter(version_files))
            item = next(item for item in levels if item["id"] == first_id)
            open_task(page, item["title"], item["id"])
            with page.expect_download() as download:
                page.locator("#download-path-file").click()
            assert (
                Path(download.value.path()).read_bytes() == version_files[first_id][1]
            )
            log("download_saved_plan_attachment")
            handoff = next((l for l in levels if l["kind"] == "submission"), None)
            if handoff:
                page.locator("#level-view a.back-link").click()
                open_task(page, handoff["title"], handoff["id"])
                expect(page.locator("#confirm-step")).to_be_visible()
                result["handoff"] = {
                    "title": handoff["title"],
                    "button": page.locator("#confirm-step").inner_text().strip(),
                    "source_urls": handoff.get("source_urls", []),
                    "unresolved_dependencies": handoff.get("blocked_by", []),
                    "availability_note": handoff.get("warning", ""),
                }
                log("inspect_handoff_before_confirmation")
            result["outcome"] = "prepared_sample_files"
            return result
        page.locator('#application-path [data-tab="workspace"]').click()
        page.locator("[data-ex-new]").click()
        form = page.locator("#exchange-task-form")
        form.locator("[name=title]").fill("交換申請文件交接測試")
        form.locator("[name=kind]").select_option("document")
        form.locator("[data-ex-file-fields] summary").click()
        payload = f"測試學生的準備紀錄：{home} → {name}".encode()
        form.locator("#exchange-upload").set_input_files(
            {"name": "student-notes.txt", "mimeType": "text/plain", "buffer": payload}
        )
        form.locator("#exchange-upload-consent").check()
        with page.expect_response(
            lambda r: (
                r.request.method == "POST"
                and r.url.endswith("/account/vault/documents")
            )
        ) as uploaded:
            form.locator("[data-ex-upload]").click()
        assert uploaded.value.ok, f"workspace vault HTTP {uploaded.value.status}"
        expect(form.locator("#exchange-file-status")).to_contain_text("檔案已保存")
        form.locator("button[type=submit]").click()
        row = page.locator(".ex-task").filter(has_text="交換申請文件交接測試")
        expect(row).to_be_visible(timeout=30000)
        page.reload(wait_until="domcontentloaded")
        row.get_by_role("button", name="開啟任務").click(timeout=120000)
        form.locator("[data-ex-file-fields] summary").click()
        with page.expect_download() as restored:
            form.locator("[data-ex-download-file]").click()
        assert Path(restored.value.path()).read_bytes() == payload
        form.locator("[data-ex-close]").click()
        log("upload_reload_download_identical_personal_attachment")
        with page.expect_download() as notes:
            page.locator('[data-ex-export="text"]').click()
        assert Path(notes.value.path()).stat().st_size > 0
        log("download_preparation_notes")
        result["outcome"] = (
            "prepared_sample_files"
            if version_files
            else "no_unconditional_files_in_plan"
        )
    except (PlaywrightError, AssertionError, KeyError, OSError, StopIteration) as error:
        result["outcome"] = "error"
        result["error"] = str(error)[:850]
        result["visible_message"] = [
            page.locator(s).inner_text()[:150]
            for s in ("#level-error", "#create-error", "#save-note")
            if page.locator(s).is_visible()
        ]
        result["route"] = urlsplit(page.url).fragment.split("?", 1)[0]
        print(code, "screen", page.locator("body").inner_text()[:300], flush=True)
        print(
            code,
            "debug:",
            result["error"],
            page.locator("#application-path").inner_text()[:600]
            if page.locator("#application-path").is_visible()
            else "",
            flush=True,
        )
    finally:
        result["browser_seconds"] = round(time.monotonic() - started, 2)
        if page.url.startswith(base):
            result["interaction_counts"] = page.evaluate(
                "() => Object.fromEntries(['clicks','field_changes'].map(k=>[k,Number(sessionStorage.getItem('audit-'+k))]))"
            )
        ctx.close()
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--sample",
        action="store_true",
        help="Upload and download one eligible plan document per school",
    )
    parser.add_argument("--base", default="http://127.0.0.1:8819")
    parser.add_argument("--schools", nargs="*")
    parser.add_argument("--target", help="Single exact partner for a one-home scenario")
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--browser", default=shutil.which("chromium"))
    args = parser.parse_args()
    if args.target and len(args.schools or []) != 1:
        parser.error("Supply one --schools id with --target")
    if urlsplit(args.base).hostname not in {"127.0.0.1", "localhost", "::1"}:
        parser.error(
            "This synthetic account workflow requires a loopback development server."
        )
    entries = requests.get(args.base + "/universities", timeout=30)
    entries.raise_for_status()
    schools = entries.json()
    if args.schools:
        selected = set(args.schools)
        schools = [school for school in schools if school["id"] in selected]
        if len(schools) != len(selected):
            parser.error("Unknown school id")
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with (
        sync_playwright() as pw,
        args.out.open("a", encoding="utf-8", buffering=1) as report,
    ):
        browser = pw.chromium.launch(
            executable_path=args.browser,
            args=[
                "--no-sandbox",
                "--disable-dev-shm-usage",
                "--blink-settings=imagesEnabled=false,webFontsEnabled=false",
                "--host-resolver-rules=MAP * ~NOTFOUND, EXCLUDE localhost, EXCLUDE 127.0.0.1, EXCLUDE [::1]",
            ],
        )
        completed = {
            row["id"]
            for row in map(json.loads, args.out.read_text().splitlines())
            if row["outcome"] != "error"
        }
        for school in schools:
            if school["id"] in completed:
                continue
            for attempt in range(2):
                row = run_student(
                    browser, args.base, school, sample=args.sample, target=args.target
                )
                if row["outcome"] != "error" or attempt:
                    break
                if not re.search(
                    "Timeout|ERR_CONNECTION|ECONNREFUSED|net::|HTTP 50[234]",
                    row.get("error", ""),
                ):
                    break
                print(
                    school["id"],
                    "retry fresh context after temporary interruption",
                    flush=True,
                )
                for _ in range(20):
                    try:
                        if requests.get(args.base + "/health", timeout=5).ok:
                            break
                    except requests.ConnectionError:
                        pass
                    time.sleep(2)
            print(json.dumps(row, ensure_ascii=False), file=report)
            print(
                school["id"],
                row["outcome"],
                row["browser_seconds"],
                row.get("error", "")[:160],
                flush=True,
            )
        browser.close()


if __name__ == "__main__":
    main()
