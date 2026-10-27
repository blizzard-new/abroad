"""NKUST bounded historical-rule review; current host conditions remain separate."""
from __future__ import annotations

from collections import Counter
import hashlib
import json
from pathlib import Path

from .ntust_source_review import write_atomic
from .nkust_eligibility import (
    NKUST_115_GUIDELINES_URL as GUIDELINES, NKUST_115_PREF_FORM_URL as FORM,
    NKUST_REGULATIONS_URL as REGULATIONS, NKUST_SCHOLARSHIP_REG_URL as AWARD,
)

CHECKED_AT = "2026-10-20T21:37:47+00:00"
SNAPSHOT = "sources/nkust/reviewed_20261021_sources.json"
SNAPSHOT_SHA = "18218f9ce3d376dd02aa9bf075972f88945ceaa9a7dba7016bbe07ecc676291b"
PAGE = "https://oia.nkust.edu.tw/unit-4-374-21.html"
INFO = "https://oia.nkust.edu.tw/news_det-980.html"
GENERAL_FORM = "https://forms.gle/w2SySyjpa63Zip5z9"
DISADVANTAGED_FORM = "https://forms.gle/MrMh5TmCXfzCD9pC8"
PERIOD = "官網交換頁（unit-4-374-21.html）已公布「116學年度校級出國交換甄選」時程：線上申請115/11/09 12:00開放、115/12/01 16:00截止；正式外語成績115/12/27 16:00前繳交；116/02/01–02/12審查、116/02/22 16:00公告結果；官網首頁行事曆另載2026-10-28「116學年度出國研修說明會_建工校區」（news_det-980.html另載五校區場次），學海飛颺名額視當年經費而定，請以學校官方公告為準。115校級交換已截止（申請2025/11/10 12:00–12/10 16:00、語檢補件2025/12/19 16:00、錄取確認2026/02/27 16:00）。院系級及雙聯依各自公告。"
ACADEMIC = "通則要求在目前學制有至少一學期成績且成績良好，接待校另定條件。115簡章75分是操行要求，不是學業平均；沒有全校共同學業75、GPA2.5或排名前30%的替代門檻。學業成績20%、語檢30%、領域契合度50%是甄選權重，不是資格最低分。"
DEGREE = "115校級簡章：大學部二年級以上、研究所（含在職專班）、五專四年級以上，申請及出國期間保有在學學籍；須在目前學制已有一學期成績。通則未將大學部限二年級，院系級另依其甄選；不能把115校級條文自動套到116或所有管道。僑外生不得回原國籍國家交換。"
LANGUAGE = "115校級語檢依接待校條件，未達者經本校分發仍可能提名，接待校保留審核權。不能用CEFR對照表最低級距當全校英語門檻。非英語檢定可依接待校要求替代英檢；赴陸只有接待校無外語要求才可免附，志願混合大陸與其他國家仍須附外語證明。"
DOCS = [
    "115校級一律線上申請：打字填志願表、列印完成申請人及導師／指導教授與系所簽章，再掃描PDF上傳；不可用翻拍。研究生未有指導教授可請系所主管代簽。最多三個校級志願，不是所有院系級／雙聯的共同上限。",
    "初審必繳中文歷年成績單（含名次及百分比）與適用語檢；研究生若尚無本學制歷年排名，可採前學制畢業成績。一般交換無須附研修計畫，不列中英文成績單、在學證明、推薦信、家長或院長簽章為全員初審必繳。",
    "只有符合學海惜珠資格者須交約1000–1500字赴國外研修計畫（含自傳、目標、課程相關性及未來展望），並依身分附中低收入／相關補助證明及戶口名簿等文件。一般交換與惜珠使用不同Google表單。",
    "115正文要求2023/07/01後取得語檢，流程圖仍寫2022/07/01，效期文字衝突須確認。初審可附網頁成績暫代，正式成績須2025/12/19 16:00前補交；不能把這個歷史補件日期推成下一梯。",
    "錄取確認階段才上傳錄取聲明書及家長同意書。初審各檔以學號_文件名稱命名；來源只說上傳容量有限，未支持通用固定MB或頁數上限。",
]
OBLIGATIONS = [
    "交換以一學期為原則、通則至多兩學期；期間維持高科大學籍並繳本校學雜費。接待校學費依一般交換、自費或個別管道，不一律免繳。",
    "115簡章明列赴外期間無本校最低選課學分，仍須遵守接待校修課規定，並事先向系所確認抵免。名額表的舊學校認可註記須另核當期主管機關及校內抵免規定。",
    "115延長交換須先取得接待校同意，於接待校延長申請截止前兩週將核章正本送國際處；通則另有原學期結束前兩個月規定，兩項均應確認。母校提名不等於接待校錄取。",
    "115返國一個月內交心得、登錄e-portfolio並辦理適用獎助請領／核銷；本輪未核實所有心得必須1500–2000字。行前住宿、保險、簽證、接送及課程安排依個別接待校核對。",
]
AWARDS = [
    "本校113/12修正獎助要點：亞洲（不含陸港澳）交換6萬元、非亞洲8萬元、雙聯（不含陸港澳）12萬元為原則；學海飛颺名額視當年度補助經費而定，沒有固定名額，按年度預算及委員會核定，不是保證補助。",
    "本校此獎助限中華民國籍在學生且排除在職專班；交換資格可含在職專班，不能混用。須先向國際處申請而未獲學海飛颺／惜珠，且研修期間未受領國內外政府出國補助。",
    "同學制獎助一次，符合本校經濟不利條件且有證明者得再加最高2萬元；是否獲獎仍依審查與核定。",
    "本校獎助行前交行政契約，返國一個月內交成績影本、心得或3–5分鐘短片及領據；學海獎助核銷另依其計畫辦理，不能把全部單據一律要求每位交換生交。",
]


def load_snapshot(root):
    raw = (root / SNAPSHOT).read_bytes()
    if hashlib.sha256(raw).hexdigest() != SNAPSHOT_SHA:
        raise ValueError("NKUST source snapshot hash mismatch")
    return json.loads(raw)


def item(title, details, url=GUIDELINES):
    return {"title": title, "details": details, "source": {"title": title, "source_url": url,
        "category": "exchange_application", "summary": details[0] if details else title}}


def review_bundle(root: Path):
    s = load_snapshot(root); folder = root / "src/exchange_info/official_data/nkust"
    read = lambda n: json.loads((folder / n).read_text("utf8"))
    rows = lambda n: [json.loads(x) for x in (folder / n).read_text("utf8").splitlines()]
    d = read("student_dashboard.json")
    d.update(academic_score_minimum=None, academic_gpa_minimum=None, academic_score_rule=ACADEMIC,
        maximum_preferences=None, language_score_minimums={}, last_checked=CHECKED_AT)
    d["selection_rules"].update(undergraduate_gpa_minimum=None, undergraduate_rank_maximum=None,
        degree_score_minimums={}, excluded_undergraduate_years=[], pending_quota_planning=True,
        partner_requirements_need_confirmation=True, language_certificate_required=False)
    d["eligibility"] = [item("115校級與通則範圍分開", [DEGREE, ACADEMIC])]
    d["language_requirements"] = [item("語檢依個別校與證明效期", [LANGUAGE, DOCS[3]])]
    d["required_documents"] = [item("115校級初審及後續文件", DOCS)]
    d["scholarship_info"] = [item("本校獎助條件", [a], AWARD) for a in AWARDS]
    d["program_overview"] = [item("資料部分核對", [PERIOD,
        "97筆既有方案對上115校級或2023院系表；僅核對該表校名與參考欄位，不是116開放名額或整筆核實。"])]
    d["document_explanations"] = [{"title": "115校級文件與惜珠專用計畫", "summary": DOCS[0],
        "key_points": DOCS, "source": item("115簡章", [], GUIDELINES)["source"],
        "document_url": GUIDELINES, "document_type": "official_document", "full_text_extracted": False}]
    d["rule_explanations"] = [{"title": "成績、語言、甄選與義務", "summary": ACADEMIC,
        "key_points": [DEGREE, LANGUAGE] + OBLIGATIONS, "source": item("通則", [], REGULATIONS)["source"],
        "document_url": REGULATIONS, "document_type": "official_document", "full_text_extracted": False}]
    periods = []
    for title, year, deadline, note in [("115校級交換歷史初審", "115", "2025-12-10T16:00:00+08:00", PERIOD),
        ("116學年度校級出國交換甄選（官網時程11/09 12:00–12/01 16:00；以學校官方公告為準）", "116", None, "官網交換頁（unit-4-374-21.html）公布116學年度校級出國交換甄選時程：線上申請115/11/09 12:00開放、115/12/01 16:00截止，正式外語成績115/12/27 16:00前繳交，116/02/01–02/12審查、116/02/22 16:00公告結果；官網首頁行事曆另載2026-10-28「116學年度出國研修說明會_建工校區」，學海飛颺名額視當年經費而定，請以學校官方公告為準。"),
        ("院系級與雙聯另依管道公告", None, None, "2023院系表不是當期招生公告，不能套校級截止。")]:
        periods.append({**item(title, [note], PAGE if year == "115" else INFO if year == "116" else PAGE),
            "scope": "home_application", "program_types": ["exchange"], "academic_year": year,
            "application_round": title, "audience": "all_students", "opens_at": "2025-11-10T12:00:00+08:00" if deadline else None,
            "deadline_at": deadline, "date_status": "verified_exact" if deadline else "needs_confirmation",
            "status": "closed" if deadline else "needs_confirmation", "status_note": note, "deadline_note": note,
            "reminder_eligible": False, "checked_at": CHECKED_AT})
    d["application_periods"] = periods; write_atomic(folder / "student_dashboard.json", d)
    write_atomic(folder / "home_rules.json", {"school_id": "nkust", "school_name": d["school_name"],
        "eligibility": d["eligibility"], "application_periods": periods, "selection_rules": d["selection_rules"],
        "source_urls": [GUIDELINES, REGULATIONS], "verified_at": None, "checked_at": CHECKED_AT})
    x = read("exchange_info.json"); x.update(application_period=[PERIOD], eligibility=[DEGREE, ACADEMIC],
        language_requirement=[LANGUAGE], required_documents=DOCS, scholarship_info=AWARDS, last_checked=CHECKED_AT)
    write_atomic(folder / "exchange_info.json", x)
    x = read("documents.json"); x.update(required_documents=DOCS, source_urls=[GUIDELINES, FORM]); write_atomic(folder / "documents.json", x)
    x = read("scholarships.json"); x.setdefault("reference_data", x["scholarships"])
    x.update(scholarships=d["scholarship_info"], source_urls=[AWARD]); write_atomic(folder / "scholarships.json", x)
    pages = rows("pages.jsonl")
    specs = [("115校級與116待確認期限", [PERIOD]), ("申請資格與甄選權重", [DEGREE, ACADEMIC, LANGUAGE]),
        ("初審文件與惜珠計畫", DOCS), ("行前與返國義務", OBLIGATIONS), ("本校獎助條件", AWARDS)]
    for page, (title, points) in zip(pages, specs, strict=True):
        text = "\n".join(points); page.update(title=title, text=text, summary=text, source_url=AWARD if points is AWARDS else GUIDELINES,
            crawled_at=CHECKED_AT, content_hash=hashlib.sha256(text.encode()).hexdigest())
    write_atomic(folder / "pages.jsonl", pages, True)
    partners = rows("partners.jsonl")
    for p in partners:
        ref = p.setdefault("reference_data", {})
        for key in ("quota", "eligibility", "gpa_requirement", "language_requirement", "application_round",
                    "application_deadline", "application_info", "tuition_info", "notes"):
            ref.setdefault(key, p.get(key, ""))
        matches = s["table_matches"].get(p["school_name"], [])
        ref["reviewed_historical_rows"] = json.dumps(matches, ensure_ascii=False)
        school_only = p["program_type"] == "校級交換學生計畫"
        quota_parts = [f"115校級表第{m['row']}列：上學期{m['cells'][5]}、下學期{m['cells'][6]}；{m['cells'][7]}"
            for m in matches if m["gid"] == "142150725"]
        if any(m["gid"] == "1014746314" for m in matches): quota_parts.append("2023院系級表未列統一名額，須按系所查詢。")
        quota = "；".join(quota_parts) if quota_parts else "本輪兩張表未對上此方案，當期名額待核實。"
        p.update(availability_status="reference_only" if matches else "needs_confirmation",
            availability_note="115校級已截止，2023院系級僅為歷史資料；不代表116開放。",
            academic_year="115" if school_only else None, application_round="115校級／2023院系級歷史參考；116待確認",
            application_window_status="closed" if school_only else "needs_confirmation", application_deadline=PERIOD,
            quota=quota, quota_status="reference_only" if quota_parts else "not_published",
            eligibility=DEGREE + " " + ACADEMIC, gpa_requirement=ACADEMIC, language_requirement=LANGUAGE,
            tuition_info="逐管道參考：" + "；".join(dict.fromkeys(m["cells"][7 if m["gid"] == "142150725" else 5] for m in matches))
                + "。歷史表不保證當期減免；其他費用及接待校規則另查。" if matches else OBLIGATIONS[0],
            application_info="\n".join([PERIOD, "以下115校級規則不直接套用院系級或雙聯。"] + DOCS + OBLIGATIONS),
            notes="母校歷史來源部分核對；個別接待校當期條件、名額、課程、校曆、住宿、費用、圖片與心得仍待查證。")
        for key in ("quota", "colleges", "degree_levels", "language_requirement", "study_period"):
            p.setdefault("field_evidence", {})[key] = {"source_url": matches[0]["source_url"] if matches else PAGE,
                "status": "reference_only" if key == "quota" and quota_parts else "needs_confirmation",
                "checked_at": CHECKED_AT, "note": p["notes"]}
        p["student_summary_zh"].update(quota=quota, eligibility_points=[p["eligibility"]],
            application_deadline=PERIOD, application_steps=[p["application_info"]], tuition_points=[p["tuition_info"]])
    write_atomic(folder / "partners.jsonl", partners, True)
    by_name = {p["school_name"]: p for p in partners}; workflows = rows("application_workflows.jsonl")
    for w in workflows:
        p = by_name[w["school_name"]]
        w.update(academic_year=p["academic_year"], application_round=p["application_round"],
            effective_application_rounds=[p["application_round"]], applicability_status="needs_confirmation",
            applicability_note="115校級與院系級另分；116當期及逐校適用條件尚待確認。",
            coverage_status="official_partial", coverage_note=p["notes"], last_checked=CHECKED_AT)
        stages = [("確認管道與資格", [PERIOD, DEGREE, ACADEMIC, LANGUAGE]), ("115校級初審文件參考", DOCS[:4]),
            ("錄取確認及接待校審核", [DOCS[4], OBLIGATIONS[2]]), ("行前與適用獎助", OBLIGATIONS[:3] + AWARDS),
            ("返國及核銷", [OBLIGATIONS[3], AWARDS[3]])]
        for step, (title, details) in zip(w["steps"], stages, strict=True):
            step.update(title=title, summary=details[0], details=details, document_requirements=[],
                deadline_at=None, deadline_status="needs_confirmation", deadline_reminder_eligible=False,
                deadline_source_url=GUIDELINES, deadline_checked_at=CHECKED_AT, support_status="needs_confirmation",
                needs_confirmation=True, action_url=PAGE, source_urls=[GUIDELINES, REGULATIONS], checked_at=CHECKED_AT,
                submission={"method": "unknown"})
            step.pop("responsible_unit", None)
            step["scope"].update(academic_years=["115"] if p["academic_year"] else [], application_rounds=[p["application_round"]])
        if p["program_type"] == "校級交換學生計畫":
            w["steps"][1]["submission"] = {"method": "online", "portal_url": PAGE,
                "deadline_note": "115歷史流程：一般與惜珠各用不同表單；116待公告。"}
    write_atomic(folder / "application_workflows.jsonl", workflows, True)
    destinations = rows("destination_profiles.jsonl")
    for dest in destinations:
        dest.setdefault("reference_data", {"cost_summary": dest["cost_summary"],
            "student_guide_sections": json.loads(json.dumps(dest["student_guide_sections"]))})
        dest.update(cost_summary="逐校生活費尚待查證；原國家預設費用不作官方核實金額。",
            coverage_status="official_partial", coverage_note="個別校生活、住宿、簽證、圖片及心得仍待查。", last_checked=CHECKED_AT)
        for section in dest["student_guide_sections"]:
            if section["key"] in {"cost", "courses", "arrival"}:
                points = [dest["cost_summary"], OBLIGATIONS[0]] if section["key"] == "cost" else OBLIGATIONS[1:]
                section.update(summary=points[0], points=points, caution=dest["coverage_note"], source_urls=[GUIDELINES])
    write_atomic(folder / "destination_profiles.jsonl", destinations, True)
    counts = Counter(p["availability_status"] for p in partners)
    for name in ("catalog-completeness.json", "verification_status.json"):
        x = read(name)
        for target in [x] + ([x["counts"]] if "counts" in x else []):
            target.update(verified_at=None, checked_at=CHECKED_AT, whole_partner_records_verified=0, active_term=PERIOD,
                open_partners=0, reference_only_partners=counts["reference_only"], needs_confirmation_partners=counts["needs_confirmation"])
        if name == "verification_status.json": x["status"] = "partial_review"
        write_atomic(folder / name, x)
    for name in ("import_provenance.json", "import-provenance.json"):
        x = read(name); x["active_cycle_note"] = PERIOD
        if not any(r["file"] == SNAPSHOT for r in x["sources"]):
            x["sources"].append({"file": SNAPSHOT, "sha256": SNAPSHOT_SHA, "role": "bounded_source_review"})
        write_atomic(folder / name, x)
    from .generated_content_review import review_generated_content
    review_generated_content(root, "nkust")
    return dict(counts)
