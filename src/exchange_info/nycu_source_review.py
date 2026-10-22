"""NYCU source-cycle boundaries and reproducible, partial catalog corrections."""
from __future__ import annotations

from collections import Counter
import hashlib
import json
from pathlib import Path

from .ntust_source_review import write_atomic
from .nycu_eligibility import (
    NYCU_115_1_GUIDELINES_PDF_URL as FIRST,
    NYCU_115_2_GUIDELINES_PDF_URL as SECOND,
    NYCU_OUTBOUND_URL as NOTICES,
    NYCU_PORTAL_URL as PORTAL,
    NYCU_QUOTA_SHEET_URL as TABLE,
    NYCU_REGULATIONS_PDF_URL as REGULATIONS,
    NYCU_SCHOLARSHIP_URL as SCHOLARSHIPS,
    NYCU_UST_NOTICE_PDF_URL as UST_PDF,
)

CHECKED_AT = "2026-10-20T20:36:03+00:00"
SNAPSHOT = "sources/nycu/reviewed_20261021_sources.json"
SNAPSHOT_SHA = "c7631c5dcabbff8e4635d878a7fd87743ffc7787345b0018ab448aa14778fbf5"
NOTICE = "https://oia.nycu.edu.tw/oia/ch/app/data/view?module=nycu0006&id=286&serno=1aa55bc9-92e8-4d5c-b5d2-4286ae7af98d"
UST = "https://oia.nycu.edu.tw/oia/ch/app/data/view?module=nycu0006&id=286&serno=8ee14cf9-321b-46af-9871-9d154c9e6647"
FORM = "https://oia.nycu.edu.tw/oia/ch/app/data/doc?module=nycu0006&detailNo=1501852894419226624&type=s"
TABLE_DATA = "https://docs.google.com/spreadsheets/d/1MjFpOfI77e4-yQWc3dHuukoR9MJB6ZndldtSFfXiyj4/gviz/tq?tqx=out:json&gid=1079257447"

ACADEMIC = "校級交換書面審查總分須達60分；這是綜合評分，不是平均成績60分。沒有共同平均70、GPA2.7或排名50%的替代通過條件；研究生亦不能自動通過。接待校條件另查。"
LANGUAGE = "校級赴國外及港澳須具語檢證明；沒有共同TOEFL79／IELTS6／TOEIC785門檻。TOEIC須含口說寫作，第三外語須為志願校接受；新制TOEFL換算依正式通知，不自行換算。"
DEGREE = "須保有陽明交大正式學籍；115-2簽核表排除大一新生，各校院系及年級另查。系統工程與科技學位學程由國防部專案處理。"
PERIOD = "已核實115-1校級申請為2025/12/01 09:00–2026/01/05 17:00，115-2為2026/06/01 09:00–07/10 17:00，均已截止。116校級確切時程尚待核實，不能把115簡章日期順延一年。"
UST_PERIOD = "116年度第一梯次台聯大UST：陽明交大學生須於2026/12/31 16:00前將完整PDF寄至ex-out@nycu.edu.tw，不接受事後補件。01/11為各校送UST薦送資料期限，不是本校學生期限；開放時刻未核實。"
UST_RULES = "台聯大116計畫要求前一學年平均GPA3.0或B；依各方案核對學制及兩年內語檢。學期與暑期各填一份表，各至多2志願；香港中文大學暑期免英檢。名額僅供參考且部分跨學期／暑期共用，不加總。"
DOCS = [
    "115校級流程為系統填報並上傳：中文歷年等第成績單（大學部含排名）、中文在學證明、中文研修計畫含擬修課列表、中文自傳、語檢及其他有利資料。",
    "115-2公告明列自傳／計畫中文撰寫，中文非母語者可用英文；不能要求所有人中英文各一份。本輪未核實計畫固定字數或頁數上限。",
    "115-2簽核表只有申請人、導師／指導教授、系主任／所長三處簽章；沒有家長或院長的五級核章。校級志願數未在本輪讀取的文件證實，不沿用5志願。",
    "以上是115校級歷史文件；116校級與台聯大不得共用年度、表格及推薦程序。接待校正式申請是後續階段。",
]
UST_DOCS = [
    UST_PERIOD,
    "台聯大資料包含簽名申請表、身分證及學生證正反面、護照照片頁、研修計畫、CV、一封教授英文推薦函、英文歷年成績單、TOEFL／IELTS及其他有利資料；香港中文大學暑期依簡章免英檢。",
    "台聯大計畫表列申請動機、短期與長期學習計畫，欄位不足可自行延伸；不是校級中文研修計畫的固定頁數規格。",
]
OBLIGATIONS = [
    "校級交換須維持本校學籍及繳全額學雜費；接待校收費、台聯大暑期費用與雙聯學位須依個別計畫，不一律保證免學費。",
    "112年修訂辦法第16條：大學部至少3門、研究所至少2門專業課；系所主管同意非專業課者有例外，亦須符合接待校規定。任一課程不及格即可能全額沒收保證金，不能只看最低門數已及格。",
    "校級115-2錄取後保證金10000元，低收入／中低收入及特殊境遇家庭依當期簡章免繳；通則與當期簡章免繳範圍文字不同，其他年度依公告。",
    "交換前繳切結書、簽證、入學許可、機票與保險資料。依每學期公告辦理課程登錄，並修習本校0學分海外學期交換課程。",
    "辦法列開學兩個月後一週內繳期中報告、結束後一個月內繳期末報告及3–5張照片，亦括註4/30、10/31、7/31、1/31；不同校曆的適用期限應向承辦確認，不把這些日期自動推成所有學生提醒。",
]
AWARDS = "交換錄取不保證獲獎；台聯大不提供其自身獎學金，得另向母校申請。校級115-2簡章預計10/31獎助收件，但本輪未核實當期獎助公告與A／B／C類個別門檻金額，不作保證或精確提醒。"


def item(title, details, url):
    return {"title": title, "details": details,
            "source": {"title": title, "source_url": url, "category": "exchange_application"}}


def load_snapshot(root):
    body = (root / SNAPSHOT).read_bytes()
    assert hashlib.sha256(body).hexdigest() == SNAPSHOT_SHA
    return json.loads(body)


def review_bundle(root: Path):
    snapshot = load_snapshot(root)
    folder = root / "src/exchange_info/official_data/nycu"
    read = lambda name: json.loads((folder / name).read_text("utf8"))
    rows = lambda name: [json.loads(s) for s in (folder / name).read_text("utf8").splitlines()]
    groups = {g["name"]: g for g in snapshot["table_groups"]}
    d = read("student_dashboard.json")
    d.update(academic_score_minimum=None, academic_gpa_minimum=None,
             academic_score_rule=ACADEMIC, maximum_preferences=None,
             language_score_minimums={}, last_checked=CHECKED_AT)
    d["selection_rules"].update(
        academic_policy="percentage", undergraduate_gpa_minimum=None,
        undergraduate_rank_maximum=None, degree_score_minimums={},
        pending_quota_planning=True, partner_requirements_need_confirmation=True)
    d["eligibility"] = [item("校級與台聯大資格分開核對", [DEGREE, ACADEMIC, UST_RULES], REGULATIONS)]
    d["language_requirements"] = [item("依計畫及接待校核對語檢", [LANGUAGE, UST_RULES], NOTICE)]
    d["required_documents"] = [
        item("115校級歷史文件參考", DOCS, NOTICE), item("116台聯大電子郵件收件", UST_DOCS, UST)]
    d["scholarship_info"] = [item("各項獎助資格與當期公告待核對", [AWARDS], SCHOLARSHIPS)]
    d["program_overview"] = [item("陽明交大交換資料部分查核", [
        PERIOD, UST_PERIOD,
        "243筆既有方案中182筆對上115-2官方名額表，仍屬已截止年度的來源參考；不代表接待校當期條件或整筆已核實。",
        "116台聯大PDF列伯恩、香港中文、香港城市、南洋理工、UC Santa Cruz；後者缺少既有獨立紀錄，尚待補齊。舊資料另含ETH、馬里蘭、UC San Diego、UNSW，不能把它們當本輪UST開放校。",
    ], NOTICES)]
    d["document_explanations"] = [{
        "title": "校級歷史文件與116台聯大文件", "summary": DOCS[0],
        "key_points": DOCS + UST_DOCS, "source": item("115-2公告", [], NOTICE)["source"],
        "document_url": SECOND, "document_type": "official_document", "full_text_extracted": False}]
    d["rule_explanations"] = [{
        "title": "學業評分及交換義務", "summary": ACADEMIC,
        "key_points": [LANGUAGE, UST_RULES] + OBLIGATIONS,
        "source": item("112年修訂實施辦法", [], REGULATIONS)["source"],
        "document_url": REGULATIONS, "document_type": "official_document", "full_text_extracted": False}]
    period_base = {"scope": "home_application", "program_types": ["exchange"], "academic_year": "116",
                   "audience": "all_students", "opens_at": None, "checked_at": CHECKED_AT}
    d["application_periods"] = [{
        **period_base, **item("116台聯大UST（電子郵件收件）", [UST_PERIOD, UST_RULES], UST),
        "application_round": "116台聯大第一梯次", "deadline_at": "2026-12-31T16:00:00+08:00",
        "date_status": "verified_exact", "status": "open", "reminder_eligible": True,
        "status_note": "僅適用116台聯大公告所列方案。", "deadline_note": UST_PERIOD,
    }]
    for round_name in ("第一梯次", "第二梯次"):
        d["application_periods"].append({
            **period_base, **item(f"116校級{round_name}待核實", [PERIOD], NOTICES),
            "application_round": f"116校級{round_name}", "deadline_at": None,
            "date_status": "needs_confirmation", "status": "needs_confirmation",
            "reminder_eligible": False, "status_note": PERIOD, "deadline_note": PERIOD})
    write_atomic(folder / "student_dashboard.json", d)
    write_atomic(folder / "home_rules.json", {
        "school_id": "nycu", "school_name": d["school_name"], "eligibility": d["eligibility"],
        "selection_rules": d["selection_rules"], "application_periods": d["application_periods"],
        "source_urls": [REGULATIONS, NOTICE, UST], "verified_at": None, "checked_at": CHECKED_AT})
    exchange = read("exchange_info.json")
    exchange.update(academic_year=["115校級歷史參考", "116台聯大分案"],
        application_period=[PERIOD, UST_PERIOD], eligibility=[DEGREE, ACADEMIC, UST_RULES],
        language_requirement=[LANGUAGE], required_documents=DOCS + UST_DOCS,
        scholarship_info=[AWARDS], last_checked=CHECKED_AT)
    write_atomic(folder / "exchange_info.json", exchange)
    documents = read("documents.json")
    documents.update(required_documents=DOCS + UST_DOCS, source_urls=[NOTICE, SECOND, FORM, UST])
    write_atomic(folder / "documents.json", documents)
    awards = read("scholarships.json")
    awards.setdefault("reference_data", awards["scholarships"])
    awards.update(scholarships=d["scholarship_info"], source_urls=[SCHOLARSHIPS])
    write_atomic(folder / "scholarships.json", awards)
    page_specs = [
        ("校級115歷史期限與台聯大116期限", [PERIOD, UST_PERIOD], NOTICES),
        ("校級評分與交換義務", [ACADEMIC] + OBLIGATIONS, REGULATIONS),
        ("依所選計畫確認語言文件", [LANGUAGE, UST_RULES], NOTICE),
        ("115校級簽核與116台聯大資料分開", DOCS + UST_DOCS, FORM),
        ("獎助條件待當期公告核對", [AWARDS], SCHOLARSHIPS),
    ]
    pages = rows("pages.jsonl")
    for page, (title, points, url) in zip(pages, page_specs, strict=True):
        text = "\n".join(points)
        page.update(title=title, source_url=url, text=text, summary=text,
                    crawled_at=CHECKED_AT, content_hash=hashlib.sha256(text.encode()).hexdigest())
    write_atomic(folder / "pages.jsonl", pages, True)
    partners = rows("partners.jsonl")
    for p in partners:
        ref = p.setdefault("reference_data", {})
        for key in ("program_type", "quota", "application_round", "application_deadline",
                    "application_info", "eligibility", "gpa_requirement", "language_requirement",
                    "tuition_info", "notes"):
            ref.setdefault(key, p.get(key, ""))
        match_name = snapshot["table_matches"].get(p["school_name"])
        is_ust = any(p["school_name"].endswith(" " + name) for name in snapshot["ust_hosts"])
        round_name = "116台聯大第一梯次" if is_ust else "115-2校級歷史參考" if match_name else "個別計畫待核對"
        p.update(academic_year="116" if is_ust else "115" if match_name else None,
                 program_type="台聯大交換（116計畫與校級歷史資料分開）" if is_ust else "交換合作（當期條件待核對）",
                 application_round=round_name,
                 availability_status="open" if is_ust else "reference_only" if match_name else "needs_confirmation",
                 availability_note="只核對母校名單與指定規則；接待校條件、細項方案、名額與整筆仍待核實。",
                 application_window_status="open" if is_ust else "closed" if match_name else "needs_confirmation",
                 application_deadline=UST_PERIOD if is_ust else PERIOD,
                 quota_status="not_published", quota="當期逐方案名額待確認；115-2表列內容僅作歷史參考。",
                 gpa_requirement=UST_RULES if is_ust else ACADEMIC + " " + "個別接待校成績條件尚待核對。",
                 language_requirement=LANGUAGE + " " + (UST_RULES if is_ust else "接待校當期語檢待核對。"),
                 eligibility=DEGREE + " " + (UST_RULES if is_ust else ACADEMIC),
                 tuition_info=OBLIGATIONS[0],
                 application_info="\n".join(UST_DOCS if is_ust else [PERIOD] + DOCS + OBLIGATIONS),
                 notes="本輪只核對指定母校規則與來源對應；個別院系、雙聯、拓荒者身分及接待校其他條件尚待查證。")
        if match_name:
            # Retain faculty-specific rows; never combine quotas or infer blank cells.
            ref["official_1152_table_rows"] = json.dumps(groups[match_name], ensure_ascii=False)
        if "雙聯" in ref["program_type"] and not is_ust:
            p["program_type"] = "交換暨雙聯合作（各計畫分開待核對）"
        for key in ("quota", "colleges", "degree_levels", "language_requirement", "study_period"):
            p.setdefault("field_evidence", {})[key] = {
                "source_url": UST_PDF if is_ust else TABLE if match_name else NOTICES,
                "status": "needs_confirmation", "checked_at": CHECKED_AT,
                "note": "校級115-2已截止；116台聯大名額亦為參考，逐校當期條件未完成核實。"}
        p["student_summary_zh"].update(
            quota=p["quota"], eligibility_points=[p["eligibility"]],
            application_deadline=p["application_deadline"], application_steps=[p["application_info"]],
            tuition_points=[p["tuition_info"]])
    write_atomic(folder / "partners.jsonl", partners, True)
    by_name = {p["school_name"]: p for p in partners}
    workflows = rows("application_workflows.jsonl")
    for w in workflows:
        p = by_name[w["school_name"]]
        is_ust = p["availability_status"] == "open"
        w.update(program_type=p["program_type"], academic_year=p["academic_year"],
                 application_round=p["application_round"], effective_application_rounds=[p["application_round"]],
                 applicability_status="needs_confirmation",
                 applicability_note="母校共用規則部分核對；院系、接待校、年度與具體方案須另確認。",
                 coverage_status="official_partial", coverage_note="不能把部分條文核對當作整筆驗證。",
                 last_checked=CHECKED_AT)
        stages = [
            ("確認所選計畫資格", [DEGREE, UST_RULES if is_ust else ACADEMIC, LANGUAGE], UST if is_ust else REGULATIONS),
            ("依所選計畫送件", UST_DOCS if is_ust else DOCS, UST if is_ust else NOTICE),
            ("依本校通知確認錄取與保證金", ["校內推薦不等於接待校錄取。", OBLIGATIONS[2]], SECOND),
            ("接待校申請及行前準備", [OBLIGATIONS[0], OBLIGATIONS[3], AWARDS], REGULATIONS),
            ("修課、成績登錄與報告", [OBLIGATIONS[1], OBLIGATIONS[4]], REGULATIONS),
        ]
        if is_ust:
            stages[2:] = [
                ("確認台聯大與接待校錄取通知",
                 ["後續確認、保證金及薦送依台聯大與本校通知；115校級10000元規則不能直接套用台聯大暑期方案。"], UST),
                ("依個別學期或暑期方案辦理行前與獎助",
                 ["學費、住宿、保險、簽證及獎助依個別方案核對，台聯大本身不提供獎學金。"], UST_PDF),
                ("依台聯大方案完成研修與繳件",
                 ["暑期研究與學期課程的要求不同；校級3／2門課、保證金及固定報告日期不能直接套所有台聯大方案。"], UST_PDF),
            ]
        for step, (title, details, url) in zip(w["steps"], stages, strict=True):
            step.update(title=title, summary=details[0], details=details,
                        document_requirements=[], deadline_at=None, deadline_status="needs_confirmation",
                        deadline_reminder_eligible=False, deadline_source_url=url,
                        deadline_checked_at=CHECKED_AT, support_status="needs_confirmation",
                        needs_confirmation=True, action_url=url, source_urls=[url], checked_at=CHECKED_AT,
                        submission={"method": "unknown"})
            step["scope"].update(academic_years=[p["academic_year"]] if p["academic_year"] else [],
                                 application_rounds=[p["application_round"]])
        submit = w["steps"][1]
        submit["submission"] = ({"method": "email", "email": "ex-out@nycu.edu.tw"}
                                if is_ust else {"method": "online", "portal_url": PORTAL})
        if is_ust:
            submit.update(deadline_at="2026-12-31T16:00:00+08:00",
                          deadline_status="verified_exact", deadline_reminder_eligible=True)
    write_atomic(folder / "application_workflows.jsonl", workflows, True)
    destinations = rows("destination_profiles.jsonl")
    for dest in destinations:
        dest.setdefault("reference_data", json.loads(json.dumps({
            "cost_summary": dest["cost_summary"], "student_guide_sections": dest["student_guide_sections"]})))
        dest.update(cost_summary="每月生活費未完成逐校查證；原國家預設金額不作官方核實費用。",
                    coverage_status="official_partial", coverage_note="住宿、簽證、校曆、圖片及心得等其餘主張仍待查證。",
                    last_checked=CHECKED_AT)
        for section in dest["student_guide_sections"]:
            if section["key"] in {"cost", "courses", "arrival"}:
                points = ([dest["cost_summary"], OBLIGATIONS[0], AWARDS] if section["key"] == "cost"
                          else [OBLIGATIONS[1]] if section["key"] == "courses" else OBLIGATIONS[3:])
                section.update(summary=points[0], points=points,
                               caution="以上校級規則與台聯大、暑期、雙聯須按計畫確認；接待校條件另查。",
                               source_urls=[REGULATIONS, SCHOLARSHIPS])
    write_atomic(folder / "destination_profiles.jsonl", destinations, True)
    counts = Counter(p["availability_status"] for p in partners)
    for name in ("catalog-completeness.json", "verification_status.json"):
        if not (folder / name).exists():
            continue
        status = read(name)
        status.update(verified_at=None, checked_at=CHECKED_AT, whole_partner_records_verified=0,
                      active_term=PERIOD + " " + UST_PERIOD,
                      open_partners=counts["open"], reference_only_partners=counts["reference_only"],
                      needs_confirmation_partners=counts["needs_confirmation"])
        write_atomic(folder / name, status)
    for name in ("import_provenance.json", "import-provenance.json"):
        provenance = read(name)
        provenance["active_cycle_note"] = PERIOD + " " + UST_PERIOD
        if not any(s["file"] == SNAPSHOT for s in provenance["sources"]):
            provenance["sources"].append({"file": SNAPSHOT, "sha256": SNAPSHOT_SHA,
                                          "role": "bounded_source_review"})
        write_atomic(folder / name, provenance)
    return dict(counts)
