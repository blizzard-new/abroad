"""Bounded WZU 115-2 review; host conditions remain individually unverified."""
from __future__ import annotations

from collections import Counter
import hashlib
import json
from pathlib import Path

from .ntust_source_review import write_atomic

CHECKED_AT = "2026-10-20T20:56:35+00:00"
SNAPSHOT = "sources/wzu/reviewed_20261021_sources.json"
SNAPSHOT_SHA = "20dd1346b2738b199b1d1054dc334383abc36e1d27ce2a47cdb74b187d2016fb"
FIRST = "https://d020.wzu.edu.tw/article/529354"
FIRST_LANG = "https://d020.wzu.edu.tw/article/529353"
SECOND = "https://d020.wzu.edu.tw/article/530752"
SECOND_LANG = "https://d020.wzu.edu.tw/article/530751"
GENERAL_PDF = "https://d020.wzu.edu.tw/datas/upload/Pictures/530752-115-2交換生簡章二招.pdf"
LANGUAGE_PDF = "https://d020.wzu.edu.tw/datas/upload/Pictures/530751-115-2交換生簡章-語言學習組二招.pdf"
GENERAL_FORM = "https://forms.gle/kAxtr8ojo2vRsLYu5"
LANGUAGE_FORM = "https://forms.gle/A4p1aAiEAz7S2F246"
ARCHIVE = "https://d020.wzu.edu.tw/category/147726"
ACADEMIC = "115-2一般組歷年學業總平均須達70分，語言學習組65分；分數取整數、不四捨五入。兩組操行總平均80分且不得有小過（含）以上紀錄。GPA及排名不能代替百分制門檻，交換資格不等於獎助資格。"
DEGREE = "申請時五專三下以上、四技及進修四技一下以上；二技本校五專直升三上以上、非直升三下以上。出訪時五專四年級、四技二年級以上；二技直升三下、非直升四上以上。研究生（不含在職專班）及轉學生須已在本校就讀滿一學期。日語組不收五專三年級（含）以下。"
LANGUAGE = "115-2初審英語及第二外語語檢各佔10%加分，未繳正式語檢正本掃描不影響報名資格。各接待校語檢及分發時證明另查，不能以共同TOEFL／IELTS／TOEIC／JLPT分數判定所有學校通過。語言學習組仍須具目標語言基本能力。"
PERIOD = "115-2一招2026/08/31 23:59、二招延期至2026/10/13 23:59線上截止，均已截止；一般組與語言學習組各有表單。116-1確切申請日期及時刻本輪未核實，不能按往年推算。"
ALLOCATION = "二招只可報一語組，一般組五語組不含德語，語言學習組只開法語與西語；報名時志願順序即分發依據，不另辦現場撕榜或重新選填。一招至多兩語組，語組數不等於志願校數。二招面試10/19–23、分發10/14–30均為暫訂，依各語組通知。"
DOCS = [
    "115-2初審採Google表單上傳，非校務系統列印後15:00紙本收件：學生證正面、身分證雙面（外籍／僑／陸生護照、居留證或入臺證）、教務處用印之中文歷年成績單含排名、履歷表。",
    "履歷表含自傳、學習計畫、國際活動與獲獎紀錄，以上合計A4五頁、12號字為限，不含附件；非單篇計畫500–1000字或單篇五頁。英文及華語暨東南亞語組用中文及英文，其他語組中文及目標語言。",
    "語檢與SOSA志工證明為加分資料；語檢須效期內正式正本掃描，初審不接受網路成績截圖。掃描須彩色、清楚、方向正確，不接受翻拍畫面。",
    "分發後依通知繳交換意願切結書或放棄聲明書；二招切結書須本人及家長簽名並蓋章。這是分發後程序，不是初審必備系主任核章。JLPT網路成績例外只限分發檢核。",
]
OBLIGATIONS = [
    "維持文藻學籍及繳全額學雜費，進修部以18學分計。語言學習組另繳接待校學費；一般組是否免學費須逐校逐方案核對。學期或學年出訪按名額表與接待校校曆。",
    "二招規定申請前一學期及當學期日間部至少10學分、進修部18學分；一招條文明列研究所例外，二招此段未列例外，研究所適用須承辦確認。",
    "出訪與申請須同一教育階段；同階段最多兩次、不同國家、合計不逾一學年。外籍／僑／陸生不得赴母國交換。",
    "行前參加說明會、填線上行前程序單，安排簽證、保險、修課與抵免；接待校不保證接機及住宿。修課及抵免依系科與接待校，不能從申請學分數推成海外必修學分。",
    "抵達接待校兩週內線上填報抵達國外報到單；交換結束返國兩週內線上繳返國報告、成績單或研修證明及指定資料，非一個月。",
]
AWARDS = [
    "115-2簡章：五專／四技／研究所每人1萬元為原則；二技最高5萬元。校方得核發，並非錄取即保證領取。",
    "進修部以每學期實際抵免學分費三分之一為原則、總額不超過1萬元；同教育階段本校獎助一次。不能把所有五專直升四技學生自動列5萬元。",
    "學海及日本交流協會等獎助須另查當期資格、公告與核定，不以學業75分或JLPT級數自動判定獲獎。",
    "教育部學海與其他本校／教育部／我國政府出國補助不得重複支領；UMAP與ACUCA名額、獎助及截止不由此份校級簡章推定。",
]


def load_snapshot(root):
    raw = (root / SNAPSHOT).read_bytes()
    if hashlib.sha256(raw).hexdigest() != SNAPSHOT_SHA:
        raise ValueError("WZU review snapshot hash mismatch")
    return json.loads(raw)


def item(title, details, url=SECOND):
    return {"title": title, "details": details, "source": {
        "title": title, "source_url": url, "category": "exchange_application",
        "summary": details[0] if details else title}}


def review_bundle(root: Path):
    snapshot = load_snapshot(root)
    folder = root / "src/exchange_info/official_data/wzu"
    read = lambda n: json.loads((folder / n).read_text("utf8"))
    rows = lambda n: [json.loads(s) for s in (folder / n).read_text("utf8").splitlines()]
    d = read("student_dashboard.json")
    d.update(academic_score_minimum=None, academic_gpa_minimum=None,
             academic_score_rule=ACADEMIC, maximum_preferences=None,
             language_score_minimums={}, last_checked=CHECKED_AT)
    d["selection_rules"].update(undergraduate_gpa_minimum=None,
        degree_score_minimums={}, excluded_undergraduate_years=[], exclude_in_service=True,
        pending_quota_planning=True, partner_requirements_need_confirmation=True,
        language_certificate_required=False)
    d["eligibility"] = [item("依組別及申請時學制核對", [ACADEMIC, DEGREE] + OBLIGATIONS[1:3])]
    d["language_requirements"] = [item("初審加分與接待校條件分開", [LANGUAGE])]
    d["required_documents"] = [item("115-2線上申請文件", DOCS)]
    d["scholarship_info"] = [item("115-2獎助條件", [a]) for a in AWARDS]
    d["program_overview"] = [item("文藻資料部分核對", [PERIOD, ALLOCATION,
        "128筆既有方案對上115-2官方表校名；僅確認來源校名對應，名額、學費、語檢及其他主張仍待逐校核實。"])]
    d["document_explanations"] = [{"title": "115-2履歷與初審文件", "summary": DOCS[0],
        "key_points": DOCS, "source": item("二招簡章", [], GENERAL_PDF)["source"],
        "document_url": GENERAL_PDF, "document_type": "official_document", "full_text_extracted": False}]
    d["rule_explanations"] = [{"title": "115-2資格及交換義務", "summary": ACADEMIC,
        "key_points": [DEGREE, LANGUAGE, ALLOCATION] + OBLIGATIONS,
        "source": item("二招簡章", [], GENERAL_PDF)["source"],
        "document_url": GENERAL_PDF, "document_type": "official_document", "full_text_extracted": False}]
    periods = []
    for label, url, deadline in [("一招一般組", FIRST, "2026-08-31T23:59:00+08:00"),
        ("一招語言學習組", FIRST_LANG, "2026-08-31T23:59:00+08:00"),
        ("二招一般組", SECOND, "2026-10-13T23:59:00+08:00"),
        ("二招語言學習組", SECOND_LANG, "2026-10-13T23:59:00+08:00")]:
        periods.append({**item("115-2" + label, [PERIOD, ALLOCATION], url),
            "scope": "home_application", "program_types": ["exchange"], "academic_year": "115",
            "application_round": "115-2" + label, "audience": "all_students", "opens_at": None,
            "deadline_at": deadline, "date_status": "verified_exact", "status": "closed",
            "status_note": "本梯已截止，不能用面試或分發期間當成仍可報名。", "deadline_note": DOCS[0],
            "reminder_eligible": False, "checked_at": CHECKED_AT})
    periods.append({**item("116-1申請日期待核實", [PERIOD], ARCHIVE),
        "scope": "home_application", "program_types": ["exchange"], "academic_year": "116",
        "application_round": "116-1", "audience": "all_students", "opens_at": None,
        "deadline_at": None, "date_status": "needs_confirmation", "status": "needs_confirmation",
        "status_note": PERIOD, "deadline_note": PERIOD, "reminder_eligible": False, "checked_at": CHECKED_AT})
    d["application_periods"] = periods
    write_atomic(folder / "student_dashboard.json", d)
    write_atomic(folder / "home_rules.json", {"school_id": "wzu", "school_name": d["school_name"],
        "eligibility": d["eligibility"], "application_periods": periods, "selection_rules": d["selection_rules"],
        "source_urls": [GENERAL_PDF, LANGUAGE_PDF], "verified_at": None, "checked_at": CHECKED_AT})
    x = read("exchange_info.json")
    x.update(application_period=[PERIOD, ALLOCATION], eligibility=[ACADEMIC, DEGREE],
        language_requirement=[LANGUAGE], required_documents=DOCS, scholarship_info=AWARDS, last_checked=CHECKED_AT)
    write_atomic(folder / "exchange_info.json", x)
    x = read("documents.json"); x.update(required_documents=DOCS, source_urls=[GENERAL_PDF, LANGUAGE_PDF])
    write_atomic(folder / "documents.json", x)
    x = read("scholarships.json"); x.setdefault("reference_data", x["scholarships"])
    x.update(scholarships=d["scholarship_info"], source_urls=[GENERAL_PDF, LANGUAGE_PDF])
    write_atomic(folder / "scholarships.json", x)
    pages = rows("pages.jsonl")
    specs = [("115-2期限與分發", [PERIOD, ALLOCATION]), ("115-2共同資格", [DEGREE, ACADEMIC, LANGUAGE]),
             ("初審文件與五頁履歷", DOCS), ("交換義務及返國兩週", OBLIGATIONS), ("獎助分學制核對", AWARDS)]
    for page, (title, points) in zip(pages, specs, strict=True):
        text = "\n".join(points)
        page.update(title=title, source_url=GENERAL_PDF, text=text, summary=text,
            crawled_at=CHECKED_AT, content_hash=hashlib.sha256(text.encode()).hexdigest())
    write_atomic(folder / "pages.jsonl", pages, True)
    partners = rows("partners.jsonl")
    for p in partners:
        ref = p.setdefault("reference_data", {})
        for key in ("quota", "eligibility", "gpa_requirement", "language_requirement", "application_round",
                    "application_deadline", "application_info", "tuition_info", "notes"):
            ref.setdefault(key, p.get(key, ""))
        matches = snapshot["table_matches"].get(p["school_name"], [])
        lang = "語言學習組" in p["program_type"]
        p.update(availability_status="reference_only" if matches else "needs_confirmation",
            availability_note="115-2已截止；對上校名不代表當期有名額、接待校條件或整筆已核實。",
            application_round="115-2歷史參考（逐校一招／二招分開）", application_window_status="closed",
            application_deadline=PERIOD, quota="逐校名額待核實；115-2表列為歷史資料，不合併一招與二招名額。",
            quota_status="not_published", eligibility=DEGREE + " " + ACADEMIC,
            gpa_requirement=("語言學習組歷年總平均65分。" if lang else "一般組歷年總平均70分。") + "接待校較高門檻另查；無GPA／排名替代。",
            language_requirement=LANGUAGE, tuition_info=OBLIGATIONS[0],
            application_info="\n".join([PERIOD, ALLOCATION] + DOCS + OBLIGATIONS),
            notes="本輪只核對指定母校條文與名單校名；學制、名額、當期語檢、校曆、住宿、圖片與心得仍待查證。")
        ref["official_1152_name_correspondence"] = json.dumps(matches, ensure_ascii=False)
        for key in ("quota", "colleges", "degree_levels", "language_requirement", "study_period"):
            p.setdefault("field_evidence", {})[key] = {"source_url": SECOND_LANG if lang else SECOND,
                "status": "needs_confirmation", "checked_at": CHECKED_AT, "note": p["notes"]}
        p["student_summary_zh"].update(quota=p["quota"], eligibility_points=[p["eligibility"]],
            application_deadline=PERIOD, application_steps=[p["application_info"]], tuition_points=[p["tuition_info"]])
    write_atomic(folder / "partners.jsonl", partners, True)
    by_name = {p["school_name"]: p for p in partners}
    workflows = rows("application_workflows.jsonl")
    for w in workflows:
        p = by_name[w["school_name"]]; lang = "語言學習組" in p["program_type"]
        url = SECOND_LANG if lang else SECOND
        w.update(application_round=p["application_round"], effective_application_rounds=[p["application_round"]],
            applicability_status="needs_confirmation", applicability_note="一招及二招分案；逐校當期條件待查。",
            coverage_status="official_partial", coverage_note=p["notes"], last_checked=CHECKED_AT)
        stages = [("確認申請資格及所選語組", [DEGREE, ACADEMIC, LANGUAGE]),
            ("按當期表單上傳初審資料", [PERIOD] + DOCS[:3]),
            ("面試、分發與交換意願切結書", [ALLOCATION, DOCS[3]]),
            ("接待校錄取、行前與獎助", ["母校提名不等於接待校錄取。"] + OBLIGATIONS[:4] + AWARDS),
            ("抵達及返國兩週內線上繳件", [OBLIGATIONS[4]])]
        for step, (title, details) in zip(w["steps"], stages, strict=True):
            step.update(title=title, summary=details[0], details=details, document_requirements=[],
                deadline_at=None, deadline_status="needs_confirmation", deadline_reminder_eligible=False,
                deadline_source_url=url, deadline_checked_at=CHECKED_AT, support_status="needs_confirmation",
                needs_confirmation=True, action_url=url, source_urls=[url], checked_at=CHECKED_AT,
                submission={"method": "unknown"})
            step["scope"].update(academic_years=["115"], application_rounds=[p["application_round"]])
        w["steps"][1]["submission"] = {"method": "online", "portal_url": url}
    write_atomic(folder / "application_workflows.jsonl", workflows, True)
    destinations = rows("destination_profiles.jsonl")
    for dest in destinations:
        dest.setdefault("reference_data", json.loads(json.dumps({"cost_summary": dest["cost_summary"],
            "student_guide_sections": dest["student_guide_sections"]})))
        dest.update(cost_summary="逐校生活費尚待查證；原國家預設估價不作官方核實費用。",
            coverage_status="official_partial", coverage_note="生活、住宿、簽證、校曆、圖片及心得仍待逐校核對。", last_checked=CHECKED_AT)
        for section in dest["student_guide_sections"]:
            if section["key"] in {"cost", "courses", "arrival"}:
                points = ([dest["cost_summary"], OBLIGATIONS[0]] + AWARDS if section["key"] == "cost"
                    else [OBLIGATIONS[3]] if section["key"] == "courses" else OBLIGATIONS[3:])
                section.update(summary=points[0], points=points, caution=dest["coverage_note"], source_urls=[GENERAL_PDF, LANGUAGE_PDF])
    write_atomic(folder / "destination_profiles.jsonl", destinations, True)
    counts = Counter(p["availability_status"] for p in partners)
    for name in ("catalog-completeness.json", "verification_status.json"):
        if (folder / name).exists():
            x = read(name); x.update(verified_at=None, checked_at=CHECKED_AT, whole_partner_records_verified=0,
                active_term=PERIOD, open_partners=0, reference_only_partners=counts["reference_only"],
                needs_confirmation_partners=counts["needs_confirmation"])
            write_atomic(folder / name, x)
    for name in ("import_provenance.json", "import-provenance.json"):
        x = read(name); x["active_cycle_note"] = PERIOD
        for file in [SNAPSHOT, "sources/wzu/reviewed_20261021_general_round2.pdf", "sources/wzu/reviewed_20261021_language_round2.pdf"]:
            if not any(s["file"] == file for s in x["sources"]):
                x["sources"].append({"file": file, "sha256": hashlib.sha256((root / file).read_bytes()).hexdigest(), "role": "bounded_source_review"})
        write_atomic(folder / name, x)
    from .generated_content_review import review_generated_content
    review_generated_content(root, "wzu")
    return dict(counts)
