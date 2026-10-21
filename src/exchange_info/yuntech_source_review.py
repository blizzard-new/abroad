"""Bounded YunTech home-rule review; host facts remain separately unverified."""
from __future__ import annotations

from collections import Counter
import hashlib
import json
from pathlib import Path

from .ntust_source_review import write_atomic

CHECKED_AT = "2026-10-20T21:50:10+00:00"
SNAPSHOT = "sources/yuntech/reviewed_20261021_sources.json"
SNAPSHOT_SHA = "26a852cb4d343ecb8639511078c35d42fef9b4521abb469326d7fd250b7b0804"
BASE = "https://tdx.yuntech.edu.tw/index.php/2020-02-26-09-23-21"
PAGE = BASE + "/item/1144-2021-12-09-06-40-33"
GUIDELINES = BASE + "/item/download/2710_976089c1dacc28aecc1f4d7a4caf699c"
SCORING = BASE + "/item/download/2711_51d8afaa5fcc22bf6ef55a9ed56db372"
AWARD = BASE + "/item/download/3204_a8f4eca3ef03d9b08d78596d65c23b71"
WANG = BASE + "/item/download/2123_8e3e890c9bc3db3084498d98540b43b9"
WANG_PAGE = BASE + "/item/300-2021-07-28-07-27-14"
PORTAL = "https://admissions-oia.yuntech.edu.tw/oe/index/index/puid/115-2/lang/zh_TW"
TABLE = "https://admissions-oia.yuntech.edu.tw/oe/index/intro.school/puid/115-2"
MAINLAND = "https://tdx.yuntech.edu.tw/index.php/newsclass/2020-03-05-07-13-34/item/1432-2026-114-2"
PERIOD = "115-2非大陸：2026/07/27 08:00–09/24 12:00線上及紙本，已截止；系統列10/20 17:00放榜不是申請截止。115-2赴陸：09/01–10/01 12:00，公告只明列東南、四川、同濟、南京四校，已截止。116確切甄選日期尚未核實，不順延舊年度。"
ACADEMIC = "113/04/22校級要點：學業75分（含）以上或班級排名前50%，且操行80分（含）以上，另有其他優秀表現例外。沒有GPA2.75或2.5替代條文；須核對操行、特例及接待校條件。非大陸甄選學業／排名40%、語言40%、優秀表現20%是評分權重，不是資格最低分。"
DEGREE = "校級交換適用研究所在學生，或入學一學期以上大學部；在職專班可甄選但不得申請本校獎學金。應屆畢業生須本校核准並獲交換校同意延長修業，最長一年，核准後不得撤銷；外籍生不得赴原屬國家。院系級另依院系規定。"
LANGUAGE = "須符合接待校語言標準；英語授課校級交換為TOEIC650或同等能力，大陸及東南亞不受此底線，但東南亞並非免接待校語檢。評分表不能推出共同TOEFL61、IELTS5.0、東南亞TOEIC550或JLPT任意級數通過。赴陸通則免外語，但115-2公告清單仍列語言證明，須向承辦確認。"
DOCS = [
    "115-2非大陸先完成線上登錄並列印申請表；申請表及已彌封推薦信須於09/24中午前送國際園地，逾時或資料不全不接受補件。通則申請表經指導老師或導師、系、院主管簽核；本科生也有導師簽核。",
    "通則初審包括家長或監護人同意書、學生證及身分證或居留證雙面影本、英文在學證明、中英文歷年成績含班排名、兩年內有效語檢；志願有日本學校才須英文財力證明。赴陸在學及成績可中文，當期清單另查。",
    "非大陸簡歷、自傳、出國學習計畫用英文或接待國語言；非中文或英文文件另附中文譯本，不是一律每篇中英文各一份。本輪未核實固定字數或頁數上限，不等於不限篇幅。",
    "優秀表現證明一般兩年內，大四可採大學期間得獎。推薦函積分以3分為上限，不等於所有人限交3封；不能將評分加分項全部當必交。3,000元保證金及其退還條件尚未核實。",
]
MAINLAND_DOCS = [
    "115-2赴陸須在2026/10/01中午12:00前把完整紙本送國際園地1F；繳件前先寄赴大陸地區出國研修申請資料Excel表給公告承辦。不能套非大陸線上系統或10/16 17:00。",
    "赴陸公告列檢核表、申請表、證件雙面、家長同意、中文履歷／自傳／計畫／在學／歷年成績及入口查詢平均與排名列印、中文財力、接待校文件、兩年內其他有利文件及Excel表。語言能力證明與通則免附條文有差異，請確認適用。",
]
OBLIGATIONS = [
    "通則第6點：每學期維持本校註冊；大學部全額學雜費、研究生學雜費基數、延畢生9學分學雜費。接待校原則免學雜費但有特定學校／專案例外，不能把雙聯或自費方案一律列免學費。",
    "出國前與系所及教務處確認抵免，返國後一學期內附課程時間、學分、大綱及成績正本辦理；原則18小時換一學分、一門最高3學分。通則未訂所有交換生每學期2門或6學分；王秋雄獎助另有要求。",
    "校級交換以一學期或一學年為原則、修業年限內一次；行前須參加說明會。通則要求役男於預訂出國前40日辦校內程序，實際行政要求仍向承辦確認。",
    "一般服務頁及SOP要求抵達一週內回傳到達單，返國一個月內回國報到、銷假、返抵通知及研習報告；離校前至少完成2次經驗分享或國際事務服務。受獎生另依獎助文件與期限，未核實全員1500–2000字。",
]
AWARDS = [
    "本校114/06/13補助要點：交換或雙聯至少一學期，亞洲每人每學期最高11萬元、非亞洲最高15萬元，依預算及審查，經費不足可不補助；不是保證實領。一般在學生排除陸港澳，雙聯另限具中華民國國籍及戶籍；在職專班不得申請本校交換獎學金。",
    "本校補助交換／雙聯：行前兩週備經費核撥文件，出國後兩週交到達通知，返國一個月交機票、登機或出入境證明、成績影本及指導教授審核之報告；核定年度完成核銷。同一學制原則一次，重複不同事由由審議小組裁量。",
    "王秋雄113/09/23交換獎助：班排前50%、操行80、接待校語言及錄取條件；中華民國國籍且在臺設籍，排除在職及同時或重複其他留學獎助。一般交換的75分替代不能直接套此獎助。",
    "王秋雄每人每學期上限：德國柏林15萬、阿亨14萬、其他12萬；日本10萬；美國紐約或舊金山18萬、洛杉磯17萬、華盛頓或波士頓16萬、其他15萬。依年度預算審查，未支持美國一年合計固定最高30萬。",
    "王秋雄交換受獎生：學士每學期3門或等同6–9學分（18 ECTS）且各科B以上；研究所2門或4–8學分（12 ECTS）及格，或參與至少一位校內教授研究計畫。只適用此獎助，非全員修課門檻。",
    "王秋雄受獎生返國30天內交文字至少5頁（不含照片）心得及適用核銷文件；抵達30天交課表／註冊等資料，與一般到達一週通知不同。學海飛颺／惜珠當期細節與個人核定金額尚待核實，不沿用舊錄取名單當通用補助。",
]


def load_snapshot(root):
    raw = (root / SNAPSHOT).read_bytes()
    if hashlib.sha256(raw).hexdigest() != SNAPSHOT_SHA:
        raise ValueError("YunTech source snapshot hash mismatch")
    return json.loads(raw)


def item(title, details, url=GUIDELINES):
    return {"title": title, "details": details, "source": {"title": title, "source_url": url,
        "category": "exchange_application", "summary": details[0] if details else title}}


def review_bundle(root: Path):
    s = load_snapshot(root); folder = root / "src/exchange_info/official_data/yuntech"
    read = lambda n: json.loads((folder / n).read_text("utf8"))
    rows = lambda n: [json.loads(x) for x in (folder / n).read_text("utf8").splitlines()]
    d = read("student_dashboard.json")
    d.update(academic_score_minimum=None, academic_gpa_minimum=None, academic_score_rule=ACADEMIC,
        maximum_preferences=None, language_score_minimums={}, last_checked=CHECKED_AT)
    d["selection_rules"].update(academic_policy="percentage", undergraduate_gpa_minimum=None,
        undergraduate_rank_maximum=50, degree_score_minimums={}, pending_quota_planning=True,
        partner_requirements_need_confirmation=True, language_certificate_required=False)
    d["eligibility"] = [item("校級資格與特例", [DEGREE, ACADEMIC])]
    d["language_requirements"] = [item("語言依授課及接待校，非評分級距", [LANGUAGE])]
    d["required_documents"] = [item("非大陸初審", DOCS, PORTAL), item("115-2赴陸", MAINLAND_DOCS, MAINLAND)]
    d["scholarship_info"] = [item("本校／王秋雄獎助各自適用", [a], AWARD if i < 2 else WANG) for i, a in enumerate(AWARDS)]
    d["program_overview"] = [item("來源部分核對", [PERIOD, "108筆對上115-2系統校名，4筆待補查；不代表整筆或目前開放。"], PORTAL)]
    d["document_explanations"] = [{"title": "語言、格式及管道", "summary": DOCS[2], "key_points": DOCS + MAINLAND_DOCS,
        "source": item("113校級要點", [], GUIDELINES)["source"], "document_url": GUIDELINES,
        "document_type": "official_document", "full_text_extracted": False}]
    d["rule_explanations"] = [{"title": "資格與返國義務", "summary": ACADEMIC, "key_points": [DEGREE, LANGUAGE] + OBLIGATIONS,
        "source": item("113校級要點", [], GUIDELINES)["source"], "document_url": GUIDELINES,
        "document_type": "official_document", "full_text_extracted": False}]
    periods = []
    for title, url, opens, deadline in [("115-2非大陸已截止", PORTAL, "2026-07-27T08:00:00+08:00", "2026-09-24T12:00:00+08:00"),
        ("115-2赴陸四校已截止", MAINLAND, None, "2026-10-01T12:00:00+08:00"), ("116確切期限待核實", PAGE, None, None)]:
        periods.append({**item(title, [PERIOD], url), "scope": "home_application", "program_types": ["exchange"],
            "academic_year": "115" if deadline else "116", "application_round": title, "audience": "all_students",
            "opens_at": opens, "deadline_at": deadline, "date_status": "verified_exact" if deadline else "needs_confirmation",
            "status": "closed" if deadline else "needs_confirmation", "status_note": PERIOD, "deadline_note": PERIOD,
            "reminder_eligible": False, "checked_at": CHECKED_AT})
    d["application_periods"] = periods; write_atomic(folder / "student_dashboard.json", d)
    write_atomic(folder / "home_rules.json", {"school_id": "yuntech", "school_name": d["school_name"], "eligibility": d["eligibility"],
        "selection_rules": d["selection_rules"], "application_periods": periods, "source_urls": [GUIDELINES, PORTAL, MAINLAND],
        "verified_at": None, "checked_at": CHECKED_AT})
    x = read("exchange_info.json"); x.update(application_period=[PERIOD], eligibility=[DEGREE, ACADEMIC],
        language_requirement=[LANGUAGE], required_documents=DOCS + MAINLAND_DOCS, scholarship_info=AWARDS, last_checked=CHECKED_AT)
    write_atomic(folder / "exchange_info.json", x)
    x = read("documents.json"); x.update(required_documents=DOCS + MAINLAND_DOCS, source_urls=[GUIDELINES, PORTAL, MAINLAND]); write_atomic(folder / "documents.json", x)
    x = read("scholarships.json"); x.setdefault("reference_data", x["scholarships"])
    x.update(scholarships=d["scholarship_info"], source_urls=[AWARD, WANG]); write_atomic(folder / "scholarships.json", x)
    pages = rows("pages.jsonl")
    for page, (title, details, url) in zip(pages, [("115-2期限／116待查", [PERIOD], PORTAL),
        ("校級資格與例外", [DEGREE, ACADEMIC], GUIDELINES), ("語言與接待校", [LANGUAGE], GUIDELINES),
        ("文件與返國義務", DOCS + MAINLAND_DOCS + OBLIGATIONS, GUIDELINES), ("補助各自適用", AWARDS, WANG)], strict=True):
        text = "\n".join(details); page.update(title=title, text=text, summary=text, source_url=url, crawled_at=CHECKED_AT,
            content_hash=hashlib.sha256(text.encode()).hexdigest())
    write_atomic(folder / "pages.jsonl", pages, True)
    partners = rows("partners.jsonl")
    for p in partners:
        ref = p.setdefault("reference_data", {})
        for key in ("quota", "colleges", "degree_levels", "study_period", "eligibility", "gpa_requirement", "language_requirement",
            "application_round", "application_deadline", "application_info", "tuition_info", "notes"):
            ref.setdefault(key, p.get(key, ""))
        match = s["table_matches"].get(p["school_name"])
        ref["reviewed_1152_source_row"] = json.dumps(match, ensure_ascii=False)
        mainland = p["country"] == "中國大陸"
        announced = s["mainland_announced_quotas"].get(match["school_name"]) if match and mainland else None
        positive = bool(match and (match["quota_share_semester"] or match["quota_share_year"]))
        quota = (f"115-2赴陸公告{announced}名，2026/10/01已截止；不代表下一梯。" if announced else
            f"115-2系統歷史參考：一學期{match['quota_share_semester']}、一學年{match['quota_share_year']}，分開欄位不相加；已截止。" if positive else
            "115-2系統兩個名額欄為0、前台呈空白，不能推為當期開放或永久停止合作。" if match else "本輪115-2表未對上；當期名額待核實。")
        docs = MAINLAND_DOCS if mainland else DOCS
        p.update(availability_status="reference_only" if match else "needs_confirmation", availability_note="115-2已截止；名單對應不等於當期開放。",
            academic_year="115" if match else None, application_round="115-2歷史參考；116待確認", application_window_status="closed" if match else "needs_confirmation",
            application_deadline=PERIOD, quota=quota, quota_status="reference_only" if positive or announced else "not_published",
            colleges="接待校可申請院系尚待逐校核實；不能以母校全校名單當不限學院。",
            degree_levels=DEGREE, study_period="校級一學期或一學年；個別校與雙聯學制期限另查。",
            eligibility=DEGREE + " " + ACADEMIC, gpa_requirement=ACADEMIC, language_requirement=LANGUAGE,
            tuition_info=OBLIGATIONS[0] + " " + " ".join(AWARDS), application_info="\n".join([PERIOD] + docs + OBLIGATIONS),
            notes="部分母校條文與系統校名已核對；接待校個別語檢、資格、課程、費用、住宿、校曆、圖片及心得尚待查證。")
        if match and match["school_sn"] == 781: p["colleges"] = "115-2表列釜山大學管理學院，不能寫不限學院；當期資格另查。"
        for key in ("quota", "colleges", "degree_levels", "language_requirement", "study_period"):
            p.setdefault("field_evidence", {})[key] = {"source_url": MAINLAND if announced else TABLE,
                "status": "reference_only" if key == "quota" and (positive or announced) else "needs_confirmation", "checked_at": CHECKED_AT, "note": p["notes"]}
        p["student_summary_zh"].update(quota=quota, colleges=p["colleges"], degree_levels=DEGREE, study_period=p["study_period"],
            eligibility_points=[DEGREE, ACADEMIC, LANGUAGE], application_deadline=PERIOD, application_steps=docs + OBLIGATIONS, tuition_points=[OBLIGATIONS[0]] + AWARDS)
    write_atomic(folder / "partners.jsonl", partners, True)
    by_name = {p["school_name"]: p for p in partners}; workflows = rows("application_workflows.jsonl")
    for w in workflows:
        p = by_name[w["school_name"]]; mainland = p["country"] == "中國大陸"; docs = MAINLAND_DOCS if mainland else DOCS
        w.update(academic_year=p["academic_year"], application_round=p["application_round"], effective_application_rounds=[p["application_round"]],
            applicability_status="needs_confirmation", applicability_note=p["notes"], coverage_status="official_partial", coverage_note=p["notes"], last_checked=CHECKED_AT)
        stages = [("確認校級或其他管道", [PERIOD, DEGREE, ACADEMIC, LANGUAGE]), ("115-2初審文件參考", docs),
            ("審查及錄取確認", ["母校推薦後仍須接待校審查；3,000元保證金尚待核實。"]),
            ("行前與適用獎助", OBLIGATIONS[:3] + AWARDS), ("返國與抵免", [OBLIGATIONS[1], OBLIGATIONS[3], AWARDS[5]])]
        for step, (title, details) in zip(w["steps"], stages, strict=True):
            step.update(title=title, summary=details[0], details=details, document_requirements=[], deadline_at=None,
                deadline_status="needs_confirmation", deadline_reminder_eligible=False, deadline_source_url=MAINLAND if mainland else PORTAL,
                deadline_checked_at=CHECKED_AT, support_status="needs_confirmation", needs_confirmation=True,
                action_url=MAINLAND if mainland else PORTAL, source_urls=[GUIDELINES, MAINLAND if mainland else PORTAL], checked_at=CHECKED_AT,
                submission={"method": "unknown"})
            step.pop("responsible_unit", None)
            step["scope"].update(academic_years=["115"] if p["academic_year"] else [], application_rounds=[p["application_round"]])
    write_atomic(folder / "application_workflows.jsonl", workflows, True)
    destinations = rows("destination_profiles.jsonl")
    for dest in destinations:
        dest.setdefault("reference_data", {"cost_summary": dest["cost_summary"], "student_guide_sections": json.loads(json.dumps(dest["student_guide_sections"]))})
        dest.update(cost_summary="逐校生活費尚待核實；國家預設估價不作官方金額。", coverage_status="official_partial",
            coverage_note="生活、費用、住宿、簽證、圖片及心得仍待逐項查證。", last_checked=CHECKED_AT)
        for section in dest["student_guide_sections"]:
            if section["key"] in {"cost", "academics"}:
                details = [dest["cost_summary"], OBLIGATIONS[0]] if section["key"] == "cost" else [OBLIGATIONS[1], AWARDS[4]]
                section.update(summary=details[0], points=details, caution=dest["coverage_note"], source_urls=[GUIDELINES, WANG])
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
        for entry in x["sources"]:
            doc = s["documents"].get(Path(entry["file"]).name)
            if doc and entry["sha256"] == doc["sha256"]:
                entry.setdefault("previous_source_url", entry["source_url"]); entry["source_url"] = doc["source_urls"][0]
                entry["source_binding_checked_at"] = CHECKED_AT
        if not any(e["file"] == SNAPSHOT for e in x["sources"]):
            x["sources"].append({"file": SNAPSHOT, "sha256": SNAPSHOT_SHA, "role": "bounded_source_review"})
        write_atomic(folder / name, x)
    from .generated_content_review import review_generated_content
    review_generated_content(root, "yuntech")
    from .host_source_review_round25 import apply_host_source_review
    apply_host_source_review(root, "yuntech")
    return dict(counts)
