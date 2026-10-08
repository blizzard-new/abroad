"""Build an evidence ledger and read-only integration comparison for TKU acceptance.

Uses existing captures; does not recrawl the 293-entry announcement audit, merge
another school's branch, or infer an unannounced/private status from a failed URL.
"""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from exchange_info import storage
from exchange_info.application_documents import all_application_templates, templates_for_context
from exchange_info.models import ApplicationCenterContext
from exchange_info.tku_data import BUNDLE, load_tku_sources


def git(*args):
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()


def write(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n")


def build():
    sources = {s["id"]: s for s in load_tku_sources()}
    matrix = json.loads((BUNDLE / "completeness_matrix.json").read_text())
    documents = json.loads((BUNDLE / "host_documents.json").read_text())
    access_rules = []

    def rule(key, source, locator, quote, status, page=None):
        s = sources[source]
        text = s.get("text", "") if page is None else next(p["text"] for p in s["pages"] if p["page"] == page)
        assert " ".join(quote.split()) in " ".join(text.split()), (key, quote)
        access_rules.append(dict(id=key, status=status, source_id=source, source_url=s["source_url"],
            locator=locator, quote=quote, applicable_year=s["applicable_year"], checked_at=s["checked_at"],
            limitation="提供方式已核實不代表實際表單內容已取得，也不代表本學生符合資格。"))

    rule("rit-account", "ritsumeikan-howto-2027", "Application Period / account details paragraph",
        "Once nominations have been approved", "official_nomination_gate")
    rule("rit-housing", "ritsumeikan-2027-guide", "PDF p.18 Housing Application Process",
        "official housing application must be submitted after", "official_post_offer_gate", 18)
    rule("rit-health", "ritsumeikan-2027-guide", "PDF p.21 Submission deadline / instructions",
        "provided separately to admitted students", "official_post_offer_gate", 21)
    rule("rit-coe", "ritsumeikan-2027-guide", "PDF p.20 Student Visa Applicants",
        "provided separately", "official_separate_instructions", 20)
    rule("rit-coe-schedule", "ritsumeikan-2027-guide", "PDF p.2 COE Application Procedure / Application Results",
        "Early November to Early December", "official_pre_offer_coe_window", 2)
    rule("seikei-materials", "seikei-host", "Program / application details and materials",
        "Please contact your home university international office exchange coordinator for application details and materials.",
        "official_contact_route_private_restriction_not_verified")
    rule("seikei-coe", "seikei-2027-sheet", "PDF p.2 COE / financial proof paragraph",
        "More information will be announced to nominated students.", "official_nominee_information_gate", 2)
    by_key = {r["id"]: r for r in access_rules}
    document_access = []
    for school in documents:
        for doc in school["documents"]:
            access = doc["form_access"]
            rule_id = {
                "nomination_then_account_by_email": "rit-account",
                "separately_sent_to_applicant": "rit-coe",
                "contact_home_coordinator": "seikei-materials",
                "provided_to_nominated_students": "seikei-coe",
            }.get(access)
            if access == "after_admission_separately_provided":
                rule_id = "rit-housing" if doc["key"] == "housing" else "rit-health"
            assert not rule_id or rule_id in by_key
            form = sources.get(doc["form_source_id"])
            document_access.append(dict(school_name=school["school_name"], key=doc["key"], name=doc["name"],
                phase=doc["phase"], condition=doc["condition"], status=doc["status"], form_access=access,
                stage=doc['stage'], timing=doc['timing'],
                timing_rule='rit-coe-schedule' if school['partner_id'].endswith('ritsumeikan') and doc['key']=='coe' else None,
                official_restriction_rule=rule_id, original_form_contents_verified=bool(form and form.get("open_status") == "verified_open"),
                current_host_notice_form_link_verified=bool(form and doc["status"] == "verified" and doc["applicable_year"] == "2027 Spring"),
                applicability_caution=school["programme_mapping"], evidence=doc["evidence"],
                form_source_evidence={k:form.get(k) for k in ["source_url","applicable_year","checked_at","open_status","sha256","review_note"]} if form else None))
    gaps = []
    for school in matrix["schools"]:
        if school["selection_status"] != "listed":
            continue
        for field in school["fields"]:
            if field["status"] == "verified":
                continue
            next_step = "取得該年度官方新版內容後逐欄核對；目前不推定尚未公告。" if field["status"] == "not_verified_new" else "依所列來源／原文位置向承辦核對；缺值、條件或矛盾仍保留。"
            if field["key"] == "latest_forms":
                next_step = "逐表取得並讀取原檔；僅已具官方提供方式證據的項目可標提名／錄取後提供。"
            gaps.append(dict(school_name=school["school_name"], **field, next_step=next_step))
    assert len(gaps) == 67 and len(document_access) == 53
    audit = dict(checked_at="2026-10-08", scope="本批針對缺口；沿用已讀內容，不重跑公告全索引。",
        field_gap_count=len(gaps), field_gap_states=dict(Counter(g["status"] for g in gaps)),
        official_not_announced_claims=[], access_rules=access_rules, documents=document_access, field_gaps=gaps,
        targeted_public_searches=[
            dict(query='site.fedu.uec.ac.jp/en "JUSST" "2027"', checked_at="2026-10-08", result="本次索引搜尋無結果；不足以證明官方尚未公告。"),
            dict(query='site.nagasaki-gaigo.ac.jp "NICS" "大学院" "2027"', checked_at="2026-10-08", result="本次索引搜尋無結果；不提升淡江NICS／研究生映射。"),
            dict(query='site.seikei.ac.jp/gakuen/siis "Exchange Student Application" "2027"', checked_at="2026-10-08", result="未取得校方公開當期空白表；其他母校副本與MEXT健康表不作本輪申請表。"),
        ],
        new_directory_sources=dict(file="academic_sources.json", source_count=3, scope="學籍單位；不是交換開放系所。"),
        department_candidate=dict(source_url="https://calligraphy.tku.edu.tw/bf/", locator="最新消息 matched link / 2026-09-09",
            original_title="【國際處】2027-2028年赴日本姊妹校(日語組) 交換生第二次聯合甄選作業簡章，收件至115年9月16日(三)12時止",
            department="財務金融學系", applicable_year="2027-2028日語二甄／9月9日原時程轉知", checked_at="2026-10-08",
            index_read_status="HTTP 200；僅擷取相符連結標題，不是公告全文核實。",
            detail_source_url="https://calligraphy.tku.edu.tw/bf/?tkuisotope=【國際處】027-2028年赴日本姊妹校日語組-交換生第二次",
            detail_http_status=502, detail_error="502 Server Error: Bad Gateway", status="needs_confirmation",
            promoted_to_field=False, reason="內文未讀到；標題日期早於校級9/16更正公告，不當作更正後當期期限，不外推到所有系所。"),
        excluded_new_hits=[dict(url="https://www.seikei.ac.jp/gakuen/siis/intl/mext_scholarship.html", reason="MEXT 2027健康表／大使館推薦流程不能當交換申請表。")],
        unresolved_exchange_conflict_count=len(json.loads((BUNDLE / "conflicts.json").read_text())))
    write(BUNDLE / "acceptance_gap_audit.json", audit)

    comparison = []
    workflows = storage.load_bundled_application_workflows()
    profiles = storage.load_destination_profiles()
    for home, year in [("長庚大學", "116"), ("淡江大學", "2027-2028")]:
        ws = [w for w in workflows if w.home_university == home and w.academic_year == year]
        ds = [p for p in profiles if p.home_university == home]
        templates = all_application_templates(home)
        current_templates = templates_for_context(ApplicationCenterContext(school_name=home, academic_year=year, program_type="exchange"))
        comparison.append(dict(home_university=home, native_year=year, workflow_count=len(ws),
            workflow_steps=sum(len(w.steps) for w in ws), phases=dict(Counter(s.phase for w in ws for s in w.steps)),
            document_requirements=sum(len(s.document_requirements) for w in ws for s in w.steps),
            official_form_link_occurrences=sum(bool(r.official_form_url) for w in ws for s in w.steps for r in s.document_requirements),
            published_workflows=sum(w.review_status == "published" for w in ws),
            deadline_reminders=sum(s.deadline_reminder_eligible for w in ws for s in w.steps),
            all_programme_templates=len(templates), exchange_templates=len(current_templates),
            templates=[dict(id=t.id, official_layout=t.official_layout, programmes=t.program_types) for t in templates],
            destinations=len(ds), actual_destination_statuses=dict(Counter(p.coverage_status for p in ds))))
    cgu_report = json.loads((storage.BUNDLED_CGU_DIR / "catalog-completeness.json").read_text())
    write(ROOT / "docs/tku-cgu-acceptance-comparison-2026-10-08.json", dict(
        measured_at="2026-10-08", integration_main=git("rev-parse", "origin/main"), comparison=comparison,
        methodology="實際讀 bundled workflows／destinations／templates；CGU 77校，不以E2E替身20校宣稱全目錄驗收。年度標籤不是新版核實。",
        cgu_list_scope=dict(central_current=75, departmental_reference=2, source_urls=cgu_report["partner_list_source_urls"], checked_at=cgu_report["partner_list_checked_at"]),
        inherited_cgu_report_discrepancies=dict(snapshot_document_count=cgu_report["workflow_structure"]["document_count"], actual_current_document_count=comparison[0]["document_requirements"],
            snapshot_destination_statuses=cgu_report["destination_profile_status"], actual_destination_statuses=comparison[0]["actual_destination_statuses"],
            note="既有摘要與實際資料不一致，本批未覆寫CGU資料／審查狀態；不能以official_verified標籤聲稱當期完整。"),
        tku_acceptance_scope="4個已截止日語二甄校的瀏覽、既有提名者文件查核與準備稿；0個可新申請，124舊列尚非當期完整。",
        tku_unresolved="無JLPT專用UI自動比對；系所提前截止、13矛盾、長崎track／研究生、UEC2027等逐項見缺口表。"))

    shared = {"docs/api/openapi.json", "pyproject.toml", "src/exchange_info/api.py", "src/exchange_info/application_documents.py",
        "src/exchange_info/models.py", "src/exchange_info/static/app.js", "src/exchange_info/static/index.html",
        "src/exchange_info/storage.py", "src/exchange_info/university_registry.py", "tests/test_fit_signals.py",
        "tests/test_ntu_integration.py", "tests/test_school_completeness.py", "tests/test_task_documents_and_reference_plan.py", "tests/e2e/test_ntu_school.py"}
    own = set(git("diff", "--name-only", "origin/main").splitlines())
    branches = []
    for name in ["ncu", "ccu"]:
        ref = f"origin/data/{name}-exchange-20261008"
        paths = set(git("diff", "--name-only", "origin/main", ref).splitlines())
        branches.append(dict(branch=ref, commit=git("rev-parse", ref), changed_files=len(paths),
            shared_overlap=sorted(shared & paths & own)))
    protected = ["src/exchange_info/official_data/cgu", "src/exchange_info/official_data/ntpu", "src/exchange_info/official_data/ntu",
        "src/exchange_info/cgu*.py", "src/exchange_info/ntpu*.py", "src/exchange_info/ntu*.py", "src/exchange_info/static/application-journey.js", "src/exchange_info/static/document-workbench.js"]
    unchanged = git("diff", "--name-only", "origin/main", "--", *protected).splitlines()
    assert not unchanged
    write(ROOT / "docs/tku-shared-integration-risks-2026-10-08.json", dict(checked_at="2026-10-08", main=git("rev-parse","origin/main"),
        read_only_other_branches=True, other_branches_merged=False, branches=branches,
        own_shared_files=sorted(shared & own), protected_files_changed=unchanged,
        rules=["registry/API/storage/templates的各校dispatch必須合併保留，不能取單一分支覆蓋。",
            "TKU stage/conditional/condition/official_form_verified/applicability_*欄位逐名對齊CCU；NCU新增applicability可加並存。",
            "官方原檔可開啟與流程發布／資格核實分離；合併CCU＋TKU的公開原表例外，預設其他母校仍受既有審查條件。",
            "保留TKU目標確認／請求ID／未知年度清空修正；與NCU/CCU語言、科系、工作區handler需人工對照。",
            "TKU原生2027-2028年度／日語第二次甄選不能被ROC115/116或generic梯次覆蓋。",
            "NTU新增journey/workbench不修改；選校卡片總數、workflows與destination總数要按合併後實際catalog更新。",
            "OpenAPI待所有欄位合併完成後重產；pyproject學校附件包裝項合併保留；不改uv.lock掩蓋既有失敗。"],
        protected_bundle_workflows=dict(Counter(w.home_university for w in workflows)),
        protected_bundle_destinations=dict(Counter(p.home_university for p in profiles))))
    print(json.dumps(dict(gaps=len(gaps), documents=len(document_access), access_rules=len(access_rules), branch_overlaps=branches), ensure_ascii=False))


if __name__ == "__main__":
    build()
