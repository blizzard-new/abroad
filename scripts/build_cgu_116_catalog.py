"""Add the 116 academic-year (fall 2027 departure) workflows to the bundled CGU catalogue.

Idempotent. It rebuilds the 116 rows from the 115 rows each run and never changes a
115 row, so saved 115 plans keep working. What changes in the clones comes from the
official pages re-read on 2026-10-03:

* the selection guide's current schedule (fall: apply 11/01-12/20; the page names no
  year or cut-off time for this round, so no exact deadline is stored);
* the guide's current list of required documents (parent/guardian consent, language
  proof, Chinese transcript original with ranking, a one-page study plan, optional
  extras) and its online application form;
* the review timetable (initial review within two weeks after the semester, results in
  week three) and the note that subsidies need no separate application;
* each partner's recurring dates from CGU's own partner sheet, added where the old
  text only said "see the nomination letter".

Clones are ``legacy``: nothing is published and no deadline can create a reminder.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from exchange_info.models import (  # noqa: E402
    ApplicationDocumentRequirement,
    ApplicationSourceRole,
    ApplicationWorkflowReviewStatus,
    ApplicationWorkflowSource,
    PartnerUniversity,
    UniversityApplicationWorkflow,
)
from exchange_info.school_identity import same_school  # noqa: E402
from exchange_info.storage import read_jsonl, write_jsonl  # noqa: E402
from exchange_info.student_view import fetch_partner_universities  # noqa: E402
from exchange_info.workflow_structuring import (  # noqa: E402
    structure_application_workflow,
    workflow_structure_issues,
    workflow_structure_summary,
)

BUNDLE = ROOT / "src" / "exchange_info" / "official_data" / "cgu"
CHECKED_AT = datetime(2026, 10, 3, tzinfo=timezone.utc)
ROUND = "秋季／全學年梯次"
GUIDE = "https://www.cgu.edu.tw/oia-ch/Contents?nodeId=15656"
STAGES = "https://www.cgu.edu.tw/oia-ch/Subject?nodeId=15680"
SUBSIDY_LOW_INCOME = "https://www.cgu.edu.tw/oia-ch/Contents?nodeId=15725"
FORM = "https://forms.gle/diGWyV9gVUtGmmM87"
VERIFIED_PAGES = (
    "nodeId=15656", "nodeId=17554", "nodeId=17533", "nodeId=15724", "nodeId=15725", "nodeId=15680",
)
# oia.cgu.edu.tw no longer answers; the office's pages live under www.cgu.edu.tw/oia-ch.
DEAD_HOSTS = {"https://oia.cgu.edu.tw/": "https://www.cgu.edu.tw/oia-ch"}
GENERIC_TIMING = re.compile(r"^以(?:長庚)?提名信與合作校(?:當期通知|入口)為準$")

STEP_TIMING = {
    "確認資格並選擇志願學校": "秋季班（8–9 月出國）11/01–12/20；116 學年度第 1 學期，須知未標示年度與截止時刻，以國際處本梯次公告為準",
    "在長庚期限內送出校內申請": "務必在國際處本梯次公告的截止日前完成（預告自 2026/11/01 開放；須知列 12/20）",
    "等待校內甄選結果與長庚正式提名": "申請當學期（第一學期）結束後 2 週內初審，第 3 週公告初審結果",
}
STEP2_DOCUMENTS = [
    ("線上申請表（Google 表單）", FORM, False),
    ("家長／監護人同意書（填妥線上申請表後寄至你留的電子信箱）", None, False),
    ("外國語文能力證明", None, False),
    ("中文歷年成績單正本（含在校平均分數；大學部含班級排名百分比）", None, False),
    ("讀書計畫（中文即可，格式不限，1 頁）", None, False),
    ("國外學校申請／許可紀錄（僅申請非本校國外合作大學者）", None, True),
    ("其他有利審查的資料（非必要，例如表揚與獲獎紀錄）", None, True),
]
STEP2_DETAILS = [
    "請線上填寫申請表；申請表上選擇最適合的交換學校 2 所。尚未取得語文成績者，請在申請表註明預計取得日期。",
    "通過校內初審後，這些文件須與國外學校的申請資料一起提交。",
    "未在截止日前繳交文件者，無法進入審查階段。校級交換由國際長召集審查會議；院級交換由各學院審查。",
]
SUBSIDY_NOTE = "補助不需另外申請：校內初審通過、獲國外學校錄取且符合補助資格者，國際處會直接送補助審查；實際名額與額度視教育部核定經費、本校預算及申請人數而定。"


def live_url(url):
    return DEAD_HOSTS.get(url, url) if url else url


def sources_for(old_sources):
    sources = []
    seen = set()
    for source in old_sources:
        if source.source_url in DEAD_HOSTS:
            source = source.model_copy(update={"source_url": DEAD_HOSTS[source.source_url], "checked_at": CHECKED_AT})
        if any(key in source.source_url for key in VERIFIED_PAGES):
            source = source.model_copy(update={"checked_at": CHECKED_AT})
        sources.append(source)
        seen.add(source.source_url)
    for title, url in (
        ("長庚大學各階段作業流程", STAGES),
        ("長庚大學出國研修補助（限勵學生／學海惜珠）", SUBSIDY_LOW_INCOME),
    ):
        if url not in seen:
            sources.append(ApplicationWorkflowSource(
                title=title, source_url=url, role=ApplicationSourceRole.HOME_UNIVERSITY,
                checked_at=CHECKED_AT,
            ))
    return sources


def to_116(old: UniversityApplicationWorkflow, partner: PartnerUniversity) -> UniversityApplicationWorkflow:
    steps = []
    live_dates = (partner.application_deadline or "").strip()
    for step in old.steps:
        update = {
            "rule_id": None,
            "overrides_rule_id": None,
            "source_urls": list(dict.fromkeys(live_url(u) for u in step.source_urls)),
            "action_url": live_url(step.action_url),
            # The copied exact dates belonged to an earlier round; none is carried over.
            "deadline_at": None,
            "deadline_checked_at": None,
            "deadline_reminder_eligible": False,
            "scope": step.scope.model_copy(update={
                "academic_years": ["116" if y == "115" else y for y in step.scope.academic_years],
                # Always explicit: otherwise the structurer infers "春季" from partner date text
                # and the workflow would claim a spring 116 round that has not been announced.
                "application_rounds": [ROUND],
            }),
        }
        if step.title in STEP_TIMING:
            update["timing"] = STEP_TIMING[step.title]
            update["checked_at"] = CHECKED_AT
        if step.title == "確認資格並選擇志願學校":
            update["official_form_urls"] = [FORM]
            update["source_urls"] = list(dict.fromkeys([*step.source_urls, GUIDE]))
        if step.title == "在長庚期限內送出校內申請":
            update["summary"] = "先完成長庚校內甄選，不要直接向合作校送件；線上填寫申請表後，依官方清單準備並繳交文件。"
            update["details"] = STEP2_DETAILS
            update["required_documents"] = [name for name, _, _ in STEP2_DOCUMENTS]
            update["document_requirements"] = [
                ApplicationDocumentRequirement(
                    name=name, official_form_url=url, needs_confirmation=optional,
                    source_urls=[GUIDE],
                )
                for name, url, optional in STEP2_DOCUMENTS
            ]
            update["official_form_urls"] = [FORM]
            update["source_urls"] = list(dict.fromkeys([GUIDE, *step.source_urls]))
        if step.title == "辦理學分抵免與補助結案":
            update["details"] = list(dict.fromkeys([*step.details, SUBSIDY_NOTE]))
            update["source_urls"] = list(dict.fromkeys([*step.source_urls, GUIDE]))
        if step.title != "在長庚期限內送出校內申請":
            # Copied document lists were not re-read for this round: confirmation stays open.
            update["document_requirements"] = [
                requirement.model_copy(update={"needs_confirmation": True})
                for requirement in step.document_requirements
            ]
        is_partner_step = step.title.startswith("依提名信") or step.title.startswith("依 ") and "信件" in step.title
        if (
            is_partner_step and live_dates and partner.availability_status == "open"
            and (not step.timing or GENERIC_TIMING.match(step.timing.strip()))
        ):
            update["timing"] = f"合作校資料表列：{live_dates}（未附年度；個人期限以提名信為準）"
        steps.append(step.model_copy(update=update))
    clone = old.model_copy(update={
        "workflow_id": None,
        "governance_key": None,
        "issue_report_snapshot": None,
        "program_type": partner.program_type if partner.availability_status != "open" else old.program_type,
        "academic_year": "116",
        "application_round": None,
        "effective_application_rounds": [ROUND],
        "steps": steps,
        "sources": sources_for(old.sources),
        "last_checked": CHECKED_AT,
        "review_status": ApplicationWorkflowReviewStatus.LEGACY,
        "published_at": None,
        "supersedes_version": None,
        "version": 1,
    })
    return structure_application_workflow(clone)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--partners-json", type=Path, help="Use a saved live partner list instead of fetching.")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    if args.partners_json:
        live = [PartnerUniversity.model_validate(r) for r in json.loads(args.partners_json.read_text(encoding="utf-8"))]
    else:
        live = fetch_partner_universities(timeout_seconds=20)
    rows = read_jsonl(BUNDLE / "application_workflows.jsonl", UniversityApplicationWorkflow)
    old = [w for w in rows if w.academic_year != "116"]
    built, missing = [], []
    for partner in live:
        match = next((w for w in old if same_school(w.school_name, partner.school_name)), None)
        if match is None:
            missing.append(partner.school_name)
        else:
            built.append(to_116(match, partner))
    unused = [w.school_name for w in old if not any(same_school(w.school_name, p.school_name) for p in live)]
    print(json.dumps({
        "live_partners": len(live), "workflows_115_kept": len(old), "workflows_116_built": len(built),
        "live_partners_without_115_workflow": missing, "115_workflows_without_live_partner": unused,
        "issues": sum(bool(workflow_structure_issues(w)) for w in built),
        "summary_116": workflow_structure_summary(built),
    }, ensure_ascii=False, indent=2))
    if args.dry_run or missing:
        return 0 if not missing else 1
    write_jsonl(BUNDLE / "application_workflows.jsonl", old + built)
    print("wrote", BUNDLE / "application_workflows.jsonl")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
