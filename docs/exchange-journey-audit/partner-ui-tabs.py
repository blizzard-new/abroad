"""Exercise the production detail renderers in Chromium for every local catalogue row.

Requires a local server on the same checkout, with the bundled data and no private overrides.
    .venv/bin/python docs/exchange-journey-audit/partner-ui-tabs.py --base http://127.0.0.1:8819

The dashboard and destination profiles come from the running API. Workflow inputs for bulk
rendering use the bundled public baseline and the application's workflow selector. Each
home's first workflow is checked against its real HTTP response.
"""
import argparse
import csv
import gzip
import io
import json
from itertools import islice
from pathlib import Path
import shutil
import time
from urllib.parse import urlsplit

import requests
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from playwright.sync_api import sync_playwright

from exchange_info.application_rules import select_application_workflow
from exchange_info.discovery import localize_experience_digest
from exchange_info.experience_collector import build_experience_digest
from exchange_info.experience_digests import attach_digests, with_bundled_sources
from exchange_info.life_context import reference_student_sources
from exchange_info.models import ApplicationRuleContext, PartnerUniversity, UniversityApplicationWorkflow
from exchange_info.school_identity import school_program_identity_key
from exchange_info.storage import load_community_questions, load_public_chat_messages, load_student_experiences, read_jsonl
from exchange_info.workflow_structuring import structure_application_workflow


HERE = Path(__file__).resolve().parent
PACKAGE = HERE.parents[1] / "src" / "exchange_info"
DATA = PACKAGE / "official_data"
FIELDS = ("home_id", "partner", "panel_count", "workflow_steps", "application_source_links",
          "destination_status", "reviewed_campus", "prep_guide", "result")

RENDER = """async text => {
    const rows = JSON.parse(text);
    const result = [];
    for (const {index, workflow, profile} of rows) {
        const item = state.dashboard.partner_universities[index];
        const record = {partner: item.school_name, result: 'ok'};
        try {
            state.activeSchool = item.school_name;
            document.querySelector('#school-detail-content').innerHTML = renderUniversityOverview(item);
            const panels = [...document.querySelectorAll('#school-detail-content [role=tabpanel]')];
            record.panel_count = panels.length;
            if (panels.length !== 6 || panels.some(p => !document.querySelector('#detail-tab-'+p.id.replace('detail-','')))) {
                throw Error('panel linkage');
            }
            const overview = document.querySelector('#detail-overview');
            if (!overview.querySelector('.university-fact strong')?.textContent.trim()) throw Error('empty overview');
            renderApplicationWorkflow(workflow);
            document.querySelector('#detail-tab-application').click();
            const application = document.querySelector('#detail-application');
            if (application.hidden || document.querySelector('#workflow-content').getAttribute('aria-busy') !== 'false') {
                throw Error('application tab hidden or busy');
            }
            record.workflow_steps = application.querySelectorAll('.workflow-step').length;
            record.application_source_links = application.querySelectorAll('a[href^="https://"],a[href^="http://"]').length;
            if (!record.workflow_steps && !record.application_source_links) throw Error('no workflow steps or sourced guidance');
            if (record.workflow_steps !== workflow.steps.length) throw Error('workflow step count differs');
            renderDestinationProfile(item, profile);
            const destination = document.querySelector('#destination-official-content');
            if (destination.getAttribute('aria-busy') !== 'false' || !destination.textContent.trim()) throw Error('empty destination');
            if (profile.home_university === '國立中央大學' && profile.city?.includes('就讀校區依錄取通知')) {
                const renderedCity = [...destination.querySelectorAll('.destination-facts div')].find(
                    field => field.querySelector('span')?.textContent === '所在地')?.querySelector('strong')?.textContent;
                if (renderedCity !== profile.city) throw Error('reviewed campus or enrolment qualification missing');
                record.reviewed_campus = renderedCity;
            }
            const service = profile.student_guide_sections?.find(section => section.key === 'host_life_service');
            if (service) {
                const card = destination.querySelector('[data-ccu-life-field="host_life_service"]');
                const links = card ? [...card.querySelectorAll('a[href]')].map(a => a.getAttribute('href')) : [];
                if (!card || !card.textContent.includes(service.summary) ||
                    !service.points.every(point => card.textContent.includes(point)) ||
                    !service.source_urls.every(url => links.includes(url))) throw Error('host life service or its source missing');
            }
            record.destination_status = profile.coverage_status;
            await window.UniWayDestinationTips.load(item);
            document.querySelector('#detail-tab-prep').click();
            const prep = document.querySelector('#prep-content');
            if (document.querySelector('#detail-prep').hidden || prep.getAttribute('aria-busy') !== 'false' || !prep.textContent.trim()) {
                throw Error('empty departure panel');
            }
            record.prep_guide = prep.querySelector('.tips-topic') ? 'country-guide' : 'entry-advisory';
            if (record.prep_guide === 'entry-advisory' && !prep.querySelector('a[href^="https://www.boca.gov.tw/"]')) throw Error('missing consular source');
        } catch (e) { record.result = String(e); }
        result.push(record);
    }
    return result;
}"""


STUDENT_FIELDS = ("home_id", "partner", "sources", "stories", "other_sources", "community", "result")

RENDER_STUDENT = r"""text => JSON.parse(text).map(({index, digest}) => {
    const item = state.dashboard.partner_universities[index];
    const row = {partner: item.school_name, sources: digest.sources.length, result: 'ok'};
    try {
        state.activeSchool = item.school_name;
        document.querySelector('#school-detail-content').innerHTML = renderUniversityOverview(item);
        renderExperienceDigest(digest);
        document.querySelector('#detail-tab-experiences').click();
        const panel = document.querySelector('#experience-content');
        if (document.querySelector('#detail-experiences').hidden || panel.getAttribute('aria-busy') !== 'false') throw Error('experience tab');
        const counter = panel.querySelector('[data-experience-theme="all"]');
        if (!counter) throw Error('no experience state');
        row.stories = Number(counter.textContent.match(/\d+/)?.[0]);
        row.other_sources = panel.querySelectorAll('.discovery-other-sources li').length;
        if (row.stories + row.other_sources !== row.sources) throw Error('source count mismatch');
        if (!row.stories && !panel.querySelector('.discovery-empty p')?.textContent.trim()) throw Error('no empty-state explanation');
        const life = document.querySelector('#life-content');
        if (life.getAttribute('aria-busy') !== 'false' || !life.textContent.trim()) throw Error('empty student-life panel');
        renderCommunityThreads({questions: [], posts: [], chat: [], conversations: [], messages: {}});
        document.querySelector('#detail-tab-community').click();
        const community = document.querySelector('#community-content');
        if (document.querySelector('#detail-community').hidden || community.getAttribute('aria-busy') !== 'false'
            || !community.querySelector('.community-post-list')?.textContent.trim()
            || !document.querySelector('#community-title').textContent.includes(item.school_name)) throw Error('anonymous community panel');
        row.community = 'isolated-empty';
    } catch (e) {row.result = String(e);}
    return row;
})"""


def student_rows(parts, runtime):
    for index, data in enumerate(parts):
        item = PartnerUniversity.model_validate(data)
        sources = reference_student_sources(item)
        digest = build_experience_digest(item.school_name, item.country, sources)
        digest = with_bundled_sources(localize_experience_digest(digest, runtime), item.school_name)
        digest = digest.model_copy(update={"sources": attach_digests(digest.sources)})
        yield {"index": index, "digest": digest.model_dump(mode="json")}


def get(session, base, route, **params):
    response = session.get(base + route, params=params, timeout=150)
    response.raise_for_status()
    return response.json()


def select_rows(home, partners, profiles):
    workflows = read_jsonl(DATA / home["id"] / "application_workflows.jsonl",
                           UniversityApplicationWorkflow, transform=structure_application_workflow)
    by_name = {school_program_identity_key(row["school_name"]): row for row in profiles}
    for index, item in enumerate(partners):
        school = item["school_name"]
        context = ApplicationRuleContext(home_university=home["school_name"], partner_university=school)
        workflow = select_application_workflow(workflows, context)
        if workflow is None:
            workflow = UniversityApplicationWorkflow(home_university=home["school_name"], school_name=school,
                                                     partner_website=item["website"], country=item["country"],
                                                     program_type=item["program_type"])
        profile = by_name.get(school_program_identity_key(school), {
            "home_university": home["school_name"], "school_name": school,
            "country": item["country"], "coverage_status": "not_collected",
        })
        yield {"index": index, "workflow": workflow.model_dump(mode="json"), "profile": profile}


def mount_detail_renderers(page, base, homes):
    """Mount the shipped detail HTML, JS renderers and tab actions without the unrelated app shell."""
    static = PACKAGE / "static"
    detail = BeautifulSoup((static / "index.html").read_bytes(), "html.parser").select_one("#school-detail-view")
    fixture = "<!doctype html><meta charset=utf-8><body>" + str(detail) + "</body>"
    route_url = base + "/__partner_ui_audit"
    page.route(route_url, lambda route: route.fulfill(content_type="text/html", body=fixture))
    page.goto(route_url)
    for name in ("regions.js", "discovery-core.js", "discovery-ui.js", "ccu-partner-details.js",
                 "tku-partner-details.js", "destination-tips.js", "app.js", "platform-detail.js"):
        script = (static / name).read_text()
        if name == "app.js":
            script, marker, _ = script.partition("const appReady = boot()")
            if not marker:
                raise ValueError("The app bootstrap changed. Review the renderer harness.")
        page.add_script_tag(content=script)
    page.evaluate("""homes => {
        state.supportedUniversities = homes;
        document.querySelector('#school-detail-view').hidden = false;
        document.querySelector('.detail-tabs').addEventListener('click', event => {
            const tab = event.target.closest('[data-detail-target]');
            if (tab) activateDetailTab(tab.dataset.detailTarget);
        });
    }""", homes)


def run(args):
    base = args.base.rstrip("/")
    if urlsplit(base).hostname not in {"localhost", "127.0.0.1", "::1"}:
        raise ValueError("Use a local development server")
    session = requests.Session()
    session.mount('http://', HTTPAdapter(max_retries=Retry(total=6, backoff_factor=1, status_forcelist=(502, 503, 504))))
    homes = get(session, base, "/universities")
    if args.only:
        homes = [h for h in homes if h["id"] in args.only]
    student = args.student_runtime is not None
    if student:
        runtime = args.student_runtime
        if not runtime.is_dir() or load_community_questions(runtime) or load_public_chat_messages(runtime) or load_student_experiences(runtime):
            raise ValueError("Use the isolated local server’s data directory with no saved student content")
    suffix = "-student" if student else "-tabs"
    args.parts = args.parts or Path("/tmp/uniway-partner-ui" + suffix)
    args.out = args.out or HERE / ("partner-ui" + suffix + ".csv.gz")
    args.parts.mkdir(exist_ok=True, parents=True)
    with sync_playwright() as p:
        browser = p.chromium.launch(executable_path=shutil.which("chromium"), args=["--blink-settings=imagesEnabled=false"])
        page = browser.new_page(reduced_motion="reduce")
        mount_detail_renderers(page, base, homes)
        for home in homes:
            code = home["id"]
            part = args.parts / (code + ".json")
            if args.resume and part.exists():
                continue
            started = time.monotonic()
            dashboard = get(session, base, "/student-dashboard", school=home["school_name"])
            page.evaluate("""text => {
                const dashboard = JSON.parse(text);
                state.homeSchool = dashboard.school_name;
                state.dashboard = dashboard;
                state.applicationContext.school_name = dashboard.school_name;
                state.destinationCache.clear();
            }""", json.dumps(dashboard, ensure_ascii=False))
            partners = dashboard["partner_universities"]
            if student:
                entries = student_rows(partners, args.student_runtime)
                renderer = RENDER_STUDENT
            else:
                profiles = get(session, base, "/destination-profiles", home_school=home["school_name"])
                entries = select_rows(home, partners, profiles)
                renderer = RENDER
            records = []
            render_seconds = 0
            while batch := list(islice(entries, 20)):
                if not records:
                    params = {"home_school": home["school_name"], "school": partners[0]["school_name"]}
                    if student:
                        actual = get(session, base, "/student-experiences", **params)
                        if [r["source_url"] for r in actual["sources"]] != [r["source_url"] for r in batch[0]["digest"]["sources"]]:
                            raise ValueError(f"{code}: experience sources differ from the HTTP route")
                    else:
                        actual = get(session, base, "/application-workflow", **params)
                        if actual["steps"] != batch[0]["workflow"]["steps"]:
                            raise ValueError(f"{code}: workflow selection differs from the HTTP route")
                begin_render = time.monotonic()
                records.extend(page.evaluate(renderer, json.dumps(batch, ensure_ascii=False)))
                render_seconds += time.monotonic() - begin_render
            part.write_text(json.dumps([{"home_id": code, **r} for r in records], ensure_ascii=False))
            print(code, len(records), sum(r["result"] != "ok" for r in records),
                  f"{time.monotonic()-started:.1f}s incl. {render_seconds:.1f}s render batches", flush=True)
        browser.close()
    with args.out.open("wb") as file, gzip.GzipFile(fileobj=file, mode="wb", filename="", mtime=0) as packed:
        with io.TextIOWrapper(packed, encoding="utf-8", newline="") as data:
            writer = csv.DictWriter(data, fieldnames=STUDENT_FIELDS if student else FIELDS, lineterminator="\n")
            writer.writeheader()
            for home in homes:
                writer.writerows(json.loads((args.parts / (home["id"] + ".json")).read_text()))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", required=True)
    parser.add_argument("--parts", type=Path)
    parser.add_argument("--out", type=Path)
    parser.add_argument("--student-runtime", type=Path, help="Audit experience, student-life and anonymous community panels against an empty local runtime")
    parser.add_argument("--only", nargs="+")
    parser.add_argument("--resume", action="store_true", help="Resume parts only from the same checkout revision")
    run(parser.parse_args())
