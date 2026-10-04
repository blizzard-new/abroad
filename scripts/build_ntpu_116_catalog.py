"""Move the bundled NTPU catalogue to the 116 academic-year quota sheets.

What it does (idempotent, offline):

* reads the 116 partner list from the bundled official PDFs;
* matches each school to its 115 record and renames the research and
  destination rows to the 116 display name (the same school, new spelling);
* clones each school's 115 workflow into a 116 workflow, re-pointing the home
  school's own steps at the 116 announcement and guideline and recording the
  announced deadline (2026-10-23 17:00) in the step text. Partner-side steps are copied as they
  were and keep their old check date, because partner pages were not re-read;
* keeps every 115 workflow, so saved 115 plans keep working.

Cloned workflows stay ``legacy``: nothing is published, and the dual human
review that publishing requires still has to happen.
Schools with no 115 record (new in 116) are skipped here; collect them with
``exchange-info research-partners`` and merge with ``--merge-collected DIR``.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import unicodedata
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from exchange_info import ntpu_student_view as nv  # noqa: E402
from exchange_info.experience_collector import normalize_school  # noqa: E402
from exchange_info.models import (  # noqa: E402
    ApplicationWorkflowReviewStatus,
    DestinationProfile,
    PartnerResearchRecord,
    PartnerUniversity,
    UniversityApplicationWorkflow,
)
from exchange_info.school_identity import same_school, school_identity_key  # noqa: E402
from exchange_info.storage import read_jsonl, write_jsonl  # noqa: E402
from exchange_info.workflow_structuring import (  # noqa: E402
    structure_application_workflow,
    workflow_structure_issues,
    workflow_structure_summary,
)

NTPU_NAME = "國立臺北大學"
BUNDLE = ROOT / "src" / "exchange_info" / "official_data" / "ntpu"
IMAGES = ROOT / "src" / "exchange_info" / "static" / "assets" / "school-images.json"
TAIPEI = timezone(timedelta(hours=8))
CHECKED_AT = nv.NTPU_116_CHECKED_AT
ROUND = "秋季／全學年梯次"

# 116 name -> 115 name for the same school where the spelling differs too much
# for automatic matching (checked by hand against the two official sheets).
MANUAL_MATCH = {
    "德國霍夫應用科學大學(Hof University of Applied Sciences)": "霍夫應用科技大學",
    "法國里爾政治學院(Sciences Po Lille)": "里爾政治大學",
    "布拉提斯拉瓦斯洛伐克科技大學(Slovak University of Technology in Bratislava)": "布拉提斯拉瓦斯洛伐克工業大學",
    "埃斯特爾哈齊·卡羅伊天主教大學 Eszterházy Károly Catholic University": "埃斯特哈茲天主教大學",
    "維陶塔斯·馬格努斯大學(Vytautas Magnus University, VMU)": "立陶宛維塔斯．馬格努斯大學",
}

URL_MAP = {
    nv.NTPU_115_ANNOUNCEMENT_URL: nv.NTPU_116_ANNOUNCEMENT_URL,
    nv.NTPU_115_GUIDELINES_URL: nv.NTPU_116_GUIDELINES_URL,
    nv.NTPU_115_ENGLISH_PARTNERS_URL: nv.NTPU_116_ENGLISH_PARTNERS_URL,
    nv.NTPU_115_JAPANESE_PARTNERS_URL: nv.NTPU_116_JAPANESE_PARTNERS_URL,
    nv.NTPU_115_CHINESE_PARTNERS_URL: nv.NTPU_116_CHINESE_PARTNERS_URL,
}
STEP_TIMING = {
    "確認資格、語組與最多 5 個志願": "116 學年度：2026/10/01–2026/10/23 17:00",
    "完成臺北大學線上申請與文件上傳": "2026/10/23 17:00 前完成線上申請並上傳簽名申請表",
    "完成書審、研修計畫及語組面試": "秋季梯次通常 11 月下旬面試、12 月下旬公告；以國際處公告為準",
    "依提名信完成合作校申請": "校內申請 2026/10/23 17:00 截止；之後依提名信與合作校個別期限",
}
HOME_VERIFIED_TITLES = set(list(STEP_TIMING)[:3]) | {"完成抵達回報、交換心得與學分採認"}
APPLICATION_STEP = "完成臺北大學線上申請與文件上傳"


def _zh(name: str) -> str:
    return re.sub(r"[^一-鿿]", "", unicodedata.normalize("NFKC", name))


def match_old(name: str, old_names: list[str]) -> str | None:
    if name in MANUAL_MATCH and MANUAL_MATCH[name] in old_names:
        return MANUAL_MATCH[name]
    for old in old_names:
        if normalize_school(old) == normalize_school(name):
            return old
    for old in old_names:
        if same_school(name, old):
            return old
    key = _zh(name)
    for old in old_names:
        other = _zh(old)
        if len(key) >= 4 and len(other) >= 4 and (key in other or other in key):
            return old
    return None


def swap(url: str | None) -> str | None:
    return URL_MAP.get(url, url) if url else url


def unique(values):
    return list(dict.fromkeys(v for v in values if v))


def to_116(old: UniversityApplicationWorkflow, partner: PartnerUniversity) -> UniversityApplicationWorkflow:
    steps = []
    for step in old.steps:
        details = []
        for line in step.details:
            if line.startswith("本校表列名額："):
                line = f"本校表列名額：{partner.quota or '依 116 學年度官方名額表'}。"
            details.append(line.replace("115 學年度", "116 學年度"))
        update = {
            "rule_id": None,
            "overrides_rule_id": None,
            "details": details,
            "title": step.title.replace("115 學年度", "116 學年度"),
            "summary": step.summary.replace("115 學年度", "116 學年度"),
            "source_urls": unique(swap(u) for u in step.source_urls),
            "official_form_urls": unique(swap(u) for u in step.official_form_urls),
            "action_url": swap(step.action_url),
            "deadline_source_url": swap(step.deadline_source_url),
            "scope": step.scope.model_copy(update={
                "academic_years": [("116" if y == "115" else y) for y in step.scope.academic_years],
                "application_rounds": [ROUND] if step.scope.application_rounds else [],
                # A step scoped to the school must follow the school's 116 spelling.
                "partner_universities": [
                    partner.school_name if normalize_school(name) == normalize_school(old.school_name) else name
                    for name in step.scope.partner_universities
                ],
            }),
        }
        if step.title in STEP_TIMING:
            update["timing"] = STEP_TIMING[step.title]
        if step.title in HOME_VERIFIED_TITLES:
            update["checked_at"] = CHECKED_AT
        if step.title == APPLICATION_STEP:
            # The date is recorded in the text only. The bundled baseline is unreviewed, so
            # it carries no exact (reminder-capable) deadline; the 116 period item on the
            # dashboard shows it, and a human-reviewed publication can promote it.
            update["details"] = [
                *details,
                "簡章載明：線上申請送出後，須於 2026/10/23 下午 5 時前將簽名申請表上傳至指定 Google 表單，逾期視為申請未完成。",
            ]
        steps.append(step.model_copy(update=update))
    sources = []
    for source in old.sources:
        if source.source_url == nv.NTPU_115_ANNOUNCEMENT_URL:
            source = source.model_copy(update={"title": "國立臺北大學 116 學年度赴外交換公告", "source_url": nv.NTPU_116_ANNOUNCEMENT_URL, "checked_at": CHECKED_AT})
        elif source.source_url == nv.NTPU_115_GUIDELINES_URL:
            source = source.model_copy(update={"title": "國立臺北大學 116 學年度赴外交換簡章", "source_url": nv.NTPU_116_GUIDELINES_URL, "checked_at": CHECKED_AT})
        sources.append(source)
    clone = old.model_copy(update={
        "workflow_id": None,
        "governance_key": None,
        "issue_report_snapshot": None,
        "school_name": partner.school_name,
        "academic_year": "116",
        "application_round": None,
        "effective_application_rounds": [ROUND],
        "steps": steps,
        "sources": sources,
        "last_checked": CHECKED_AT,
        # Never carry a published or pending state over: 116 flows start unreviewed.
        "review_status": ApplicationWorkflowReviewStatus.LEGACY,
        "published_at": None,
        "supersedes_version": None,
        "version": 1,
    })
    return structure_application_workflow(clone)


def completeness(partners, workflows, destinations, research, images):
    from exchange_info.partner_research import apply_partner_research

    partners = apply_partner_research(partners, research, home_university=NTPU_NAME)
    image_map = {school_identity_key(str(r.get("school_name") or "")): r for r in images}
    wf_map = {school_identity_key(w.school_name): w for w in workflows}
    dest_map = {school_identity_key(d.school_name): d for d in destinations}
    rows = []
    for p in partners:
        key = school_identity_key(p.school_name)
        w, d = wf_map.get(key), dest_map.get(key)
        rows.append({
            "school_name": p.school_name, "availability_status": p.availability_status,
            "official_website": bool(p.website),
            "image_status": str((image_map.get(key) or {}).get("status") or "not_collected"),
            "language_and_eligibility": bool(p.eligibility),
            "academic_restrictions": bool(p.colleges and p.degree_levels), "quota": bool(p.quota),
            "study_period": bool(p.study_period), "ranking": bool(p.ranking_info and p.ranking_source_url),
            "workflow_steps": len(w.steps) if w else 0,
            "structured_workflow": bool(w and not workflow_structure_issues(w)),
            "housing": bool(d and d.housing_summary), "cost": bool(d and d.cost_summary),
            "transport": bool(d and d.transport_summary), "campus_life": bool(d and d.campus_life_summary),
            "destination_source_count": len(d.sources) if d else 0,
        })
    return rows


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--merge-collected", type=Path, help="Data dir holding research-partners output for schools new in 116.")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    partners = nv.fetch_ntpu_partner_universities()
    research = read_jsonl(BUNDLE / "partner_research.jsonl", PartnerResearchRecord)
    destinations = read_jsonl(BUNDLE / "destination_profiles.jsonl", DestinationProfile)
    workflows = read_jsonl(BUNDLE / "application_workflows.jsonl", UniversityApplicationWorkflow)
    old_workflows = [w for w in workflows if w.academic_year != "116"]
    old_names = sorted({w.school_name for w in old_workflows})

    mapping: dict[str, str] = {}
    unmatched: list[str] = []
    for partner in partners:
        old = match_old(partner.school_name, old_names)
        if old is None:
            unmatched.append(partner.school_name)
        else:
            mapping[partner.school_name] = old
    if len(set(mapping.values())) != len(mapping):
        raise SystemExit("two 116 schools matched the same 115 school: " + str(
            {v for v in mapping.values() if list(mapping.values()).count(v) > 1}))
    reverse = {old: new for new, old in mapping.items()}

    # Rename the year-independent rows (research, destination) to the 116 spelling.
    research = [r.model_copy(update={"school_name": reverse.get(r.school_name, r.school_name)}) for r in research]
    destinations = [d.model_copy(update={"school_name": reverse.get(d.school_name, d.school_name)}) for d in destinations]

    partner_by_name = {p.school_name: p for p in partners}
    new_workflows: list[UniversityApplicationWorkflow] = []
    for new_name, old_name in mapping.items():
        old = next(w for w in old_workflows if w.school_name == old_name)
        new_workflows.append(to_116(old, partner_by_name[new_name]))

    if args.merge_collected:
        from exchange_info.storage import (
            load_application_workflow_revisions,
            load_application_workflows,
            load_destination_profiles,
            load_partner_research,
        )
        for name in unmatched:
            for row in load_partner_research(args.merge_collected):
                if row.home_university == NTPU_NAME and same_school(row.school_name, name):
                    research.append(row.model_copy(update={"school_name": name}))
            for row in load_destination_profiles(args.merge_collected):
                if same_school(row.school_name, name):
                    destinations.append(row.model_copy(update={"school_name": name, "home_university": NTPU_NAME}))
            # Newly collected workflows are staged as pending revisions; they join the
            # bundle as legacy rows like the cloned ones, so nothing is published.
            for revision in load_application_workflow_revisions(args.merge_collected):
                row = revision.workflow
                if row.home_university == NTPU_NAME and same_school(row.school_name, name):
                    new_workflows.append(to_116(row, partner_by_name[name]))
                    break
            else:
                for row in load_application_workflows(args.merge_collected):
                    if row.home_university == NTPU_NAME and same_school(row.school_name, name):
                        new_workflows.append(to_116(row, partner_by_name[name]))
        covered = {w.school_name for w in new_workflows}
        unmatched = [name for name in unmatched if name not in covered]

    research = list({(r.home_university, r.school_name): r for r in research}.values())
    destinations = list({d.school_name: d for d in destinations}.values())
    final_workflows = old_workflows + new_workflows
    print(json.dumps({
        "partners_116": len(partners),
        "open": sum(p.availability_status == "open" for p in partners),
        "agreement_only": sum(p.availability_status != "open" for p in partners),
        "matched_to_115": len(mapping),
        "renamed": sum(1 for new, old in mapping.items() if normalize_school(new) != normalize_school(old)),
        "workflows_115_kept": len(old_workflows),
        "workflows_116_built": len(new_workflows),
        "needs_collection": unmatched,
    }, ensure_ascii=False, indent=2))
    if args.dry_run:
        return 0

    write_jsonl(BUNDLE / "partner_research.jsonl", research)
    write_jsonl(BUNDLE / "destination_profiles.jsonl", destinations)
    write_jsonl(BUNDLE / "application_workflows.jsonl", final_workflows)

    # Image manifest: let a renamed school keep the picture it already had.
    manifest = json.loads(IMAGES.read_text(encoding="utf-8"))
    rows = manifest["schools"]
    known = {school_identity_key(str(r.get("school_name") or "")) for r in rows}
    for new_name, old_name in mapping.items():
        if school_identity_key(new_name) in known or normalize_school(new_name) == normalize_school(old_name):
            continue
        source = next((r for r in rows if school_identity_key(str(r.get("school_name") or "")) == school_identity_key(old_name)), None)
        if source:
            rows.append({**source, "school_name": new_name})
            known.add(school_identity_key(new_name))
    IMAGES.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    current = [w for w in final_workflows if w.academic_year == "116"]
    rows = completeness(partners, current, destinations, research, manifest["schools"])
    summary = {
        "home_university": NTPU_NAME,
        "academic_year": "116",
        "partner_count": len(partners),
        "open_count": sum(p.availability_status == "open" for p in partners),
        "agreement_only_count": sum(p.availability_status != "open" for p in partners),
        "fields": {f: sum(bool(r[f]) for r in rows) for f in (
            "official_website", "language_and_eligibility", "academic_restrictions", "quota",
            "study_period", "ranking", "housing", "cost", "transport", "campus_life", "structured_workflow")},
        "verified_image_count": sum(r["image_status"] == "verified" for r in rows),
        "workflow_count": sum(r["workflow_steps"] > 0 for r in rows),
        "workflow_structure": workflow_structure_summary(current),
        "destination_count": sum(r["housing"] and r["cost"] for r in rows),
        "schools": rows,
    }
    (BUNDLE / "catalog-completeness.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("wrote bundle files")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
