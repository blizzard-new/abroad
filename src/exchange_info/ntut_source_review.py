"""Bounded NTUT review; mother-school rules do not verify a host record."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from .ntust_source_review import write_atomic

CHECKED_AT = "2026-10-20T20:17:12+00:00"
SNAPSHOT = "sources/ntut/reviewed_20261021_sources.json"
SNAPSHOT_SHA = "ef1904cb1860c5f88315284b24105c5cb34c8dbaea97ec678e1363d0d2132d63"
GENERAL = "https://oia.ntut.edu.tw/p/412-1032-9409-1.php"
PLAN = "https://oia.ntut.edu.tw/p/412-1032-9237-1.php"
LANDING = "https://oia.ntut.edu.tw/p/412-1032-9312.php?Lang=zh-tw"
STEP1 = "https://oia.ntut.edu.tw/p/412-1032-9238.php?Lang=zh-tw"
STEP2 = "https://oia.ntut.edu.tw/p/412-1032-9239.php?Lang=zh-tw"
STEP3 = "https://oia.ntut.edu.tw/p/412-1032-9240.php?Lang=zh-tw"
SCHOLARSHIP = "https://oia.ntut.edu.tw/p/412-1032-9313.php?Lang=zh-tw"
PARTNERS = "https://oia.ntut.edu.tw/p/412-1032-9243.php?Lang=zh-tw"
MAINLAND = "https://oia.ntut.edu.tw/p/412-1032-10190.php?Lang=zh-tw"
QA = "https://oia.ntut.edu.tw/var/file/32/1032/img/646523997.pdf"
INFO = "https://oia.ntut.edu.tw/p/406-1032-157886,r1149.php?Lang=zh-tw"

ACADEMIC = "校級交換須知明列學業成績門檻為無；歷年平均70分是學海獎助條件，不能變成一般交換門檻，也不能用GPA2.7或班排50%代換。接待校仍可另訂成績要求。"
LANGUAGE = "校級交換語言須符合接待校要求，沒有本輪可核實的共同TOEFL68／IELTS5.5／TOEIC700門檻；學海獎助另有門檻。赴陸也不能只憑國家推定免語檢。"
DEGREE = "校級一般交換須在北科學士／碩博士班修滿一學期並維持在學；新生及轉學生須確認已完成北科學期。五專須另確認，Q&A僅建議專四／專五。赴陸六校須大二以上或研究生，並具北科一學年成績。院系及雙聯學位另依各計畫。"
PERIOD = "現行流程頁仍列115學年度2025/12/01–12/10及2026/06/01–06/14；Step1一般期程列每年12/01–12/10、06/01–06/14，假日順延。116學年度確切公告、時刻及逐校開放條件待確認，不由年度慣例產生精確提醒。"
SUPPLEMENT = "補申請／轉校期限有官方來源差異：Step1為接待校薦送截止前4週，Q&A第7題為接待校申請截止前2週。兩者基準日期不同，須由承辦確認；轉校限一次且須有餘額。"
DOCS = [
    "校級交換先使用Step1所連結的平台填報，至信箱取得系統申請表及指定上傳連結；申請表簽名後與文件上傳。初審不收紙本，也不收直接寄至公用信箱的申請件。",
    "成績單規格有中英文頁面差異：中文列英文成績單含系所名次百分比、GPA及EMI學分，英文段卻列中文排名證明；送件前向承辦確認，不擅自合併為單一必備版本。",
    "語檢證明、研修計畫、行政契約書、其他有利文件、身分證或居留證、適用者特殊身分證明。頁面稱第2–9文件但實際列項與英文段亦有差異，項數待承辦確認。",
    "一般交換研修計畫限一頁A4，格式不拘，說明目的與預期效益，不必逐校撰寫，建議英文；學海惜珠另有中文1–2頁動機與1000–1500字計畫，不能套所有申請人。",
    "設計學院申請日本千葉大學另依院級流程送院辦；雙聯學位、其他院系級交換與接待校入學文件不可套用校級初審規則。",
]
OBLIGATIONS = [
    "出國前一個月準備離校申請、錄取信、行政契約、簽證及機票等；紙本辦理核章後依Step3上傳PDF，和初審不收紙本是不同階段。",
    "研修須成功通過至少兩門課並符合接待校最低學分；事前規劃頁另列當學期不得有不及格科目，學分抵免依系所認定。",
    "返國後兩週內繳件：一般生心得至少2000字，學海及臺奧受獎生至少3000字；另附本人入鏡的五張照片ZIP、成績單、研修證明及北科繳費證明。獎助核銷另有文件與兩份紙本。",
    "學海受獎生須於研修結束後兩週內上傳教育部心得及問卷；臺奧另依專用Word及核銷文件。返國繳件、獎助申請及學分抵免期限分開處理。",
]
SCHOLARSHIPS = [
    "學海飛颺／惜珠與北科出國研修獎學金分開審核，依預算與資格核定，不保證交換錄取即獲獎。學海限本國籍，排除大陸港澳等限制依專頁。",
    "學海基本條件為歷年平均70分及語檢門檻；英語表列IELTS5、舊制TOEFL iBT60、TOEIC聽讀600等，不能當作每所接待校門檻。新版TOEFL分制未由該表說明，須確認。",
    "學海專頁列補助至少新臺幣60000元，並非普遍固定亞洲60000／非亞洲75000；重複領取、交換資格及課程條件另依核定。",
    "校內出國研修獎學金表列非亞洲40000、亞洲20000、大陸港澳10000，以一學年為基準；短於一學年按實際天數調整，各區每學年原則20人，依預算審查。返國後申請，一般每年2/25截止，當年安排仍待確認。",
]


def item(title, details, url):
    return {"title": title, "details": details,
            "source": {"title": title, "source_url": url, "category": "exchange_application"}}


def review_bundle(root: Path):
    assert hashlib.sha256((root / SNAPSHOT).read_bytes()).hexdigest() == SNAPSHOT_SHA
    folder = root / "src/exchange_info/official_data/ntut"

    def read(name):
        return json.loads((folder / name).read_text("utf8"))

    def rows(name):
        return [json.loads(s) for s in (folder / name).read_text("utf8").splitlines()]

    d = read("student_dashboard.json")
    d.update(academic_score_minimum=None, academic_gpa_minimum=None,
             academic_score_rule=ACADEMIC, language_score_minimums={},
             maximum_preferences=10, last_checked=CHECKED_AT)
    d["selection_rules"].update(
        academic_policy="percentage", undergraduate_gpa_minimum=None,
        undergraduate_rank_maximum=None, degree_score_minimums={},
        pending_quota_planning=True, partner_requirements_need_confirmation=True)
    d["eligibility"] = [item("校級交換資格與接待校條件", [DEGREE, ACADEMIC, LANGUAGE], GENERAL)]
    d["language_requirements"] = [item("依接待校語檢與課程規定", [LANGUAGE], PLAN)]
    d["required_documents"] = [item("校級初審線上送件", DOCS, STEP1)]
    d["scholarship_info"] = [item("交換與獎助資格分開", SCHOLARSHIPS, SCHOLARSHIP)]
    d["program_overview"] = [item("臺北科大赴外研修資料查核中",
        ["既存206筆合作方案尚未完成逐校核實；不能把合作關係、歷年媒合名額當作當期開放。",
         PERIOD, "校級交換志願至多10項；交換原則每次一學期、總計不超過兩學期。"], PLAN)]
    d["document_explanations"] = [{
        "title": "校級交換初審與行前／返國文件", "summary": DOCS[0],
        "key_points": DOCS + OBLIGATIONS, "source": item("官方流程", [], STEP1)["source"],
        "document_url": STEP1, "document_type": "official_document", "full_text_extracted": False,
    }]
    d["rule_explanations"] = [{
        "title": "學業、語言與期限適用範圍", "summary": ACADEMIC,
        "key_points": [LANGUAGE, SUPPLEMENT] + SCHOLARSHIPS,
        "source": item("校級交換須知", [], GENERAL)["source"],
        "document_url": GENERAL, "document_type": "official_document", "full_text_extracted": False,
    }]
    base = {"scope": "home_application", "program_types": ["exchange"], "academic_year": "116",
            "audience": "all_students", "opens_at": None, "deadline_at": None,
            "date_status": "needs_confirmation", "status": "needs_confirmation",
            "reminder_eligible": False, "checked_at": CHECKED_AT}
    d["application_periods"] = [
        {**base, **item("2027交換招募說明會（活動，非申請截止）",
            ["2026/10/29 12:00–13:00，科技大樓B2國際會議廳；依公告海報QR碼報名，未列報名截止。"], INFO),
         "application_round": "116學年度說明會", "status_note": "活動時間已公告；不是交換申請截止。",
         "deadline_note": "無已核實報名截止，不從活動結束時間建立申請提醒。"},
        {**base, **item("116學年度交換申請期程待確認", [PERIOD, SUPPLEMENT], STEP1),
         "application_round": "116學年度待確認", "status_note": PERIOD, "deadline_note": DOCS[0]},
        {**base, **item("雙聯學位與留學獎學金另案查核", ["不能套用校級交換日期、文件或資格。"], GENERAL),
         "program_types": ["dual_degree"], "application_round": "個別雙聯計畫待確認",
         "status_note": "本輪尚未核實雙聯學位個別條件。", "deadline_note": "依個別計畫公告。"},
    ]
    write_atomic(folder / "student_dashboard.json", d)
    h = read("home_rules.json")
    h.update(eligibility=d["eligibility"], application_periods=d["application_periods"],
             selection_rules=d["selection_rules"], verified_at=None, review_status="partial_review",
             checked_at=CHECKED_AT, source_urls=[GENERAL, STEP1, SCHOLARSHIP])
    write_atomic(folder / "home_rules.json", h)
    x = read("exchange_info.json")
    x.update(application_period=[PERIOD, SUPPLEMENT],
             eligibility=[DEGREE, ACADEMIC], language_requirement=[LANGUAGE],
             required_documents=DOCS, scholarship_info=SCHOLARSHIPS, last_checked=CHECKED_AT)
    write_atomic(folder / "exchange_info.json", x)
    write_atomic(folder / "documents.json", {"school_name": d["school_name"], "required_documents": d["required_documents"], "source_urls": [STEP1, STEP3]})
    write_atomic(folder / "scholarships.json", {"school_name": d["school_name"], "scholarships": d["scholarship_info"], "source_urls": [SCHOLARSHIP]})
    pages = rows("pages.jsonl")
    contents = [x["application_period"], x["eligibility"], x["language_requirement"], DOCS, SCHOLARSHIPS]
    assert len(pages) == len(contents)
    for p, values, url in zip(pages, contents, [STEP1, GENERAL, PLAN, STEP1, SCHOLARSHIP], strict=True):
        p.update(text="\n".join(values), summary="\n".join(values), published_at=None,
                 crawled_at=CHECKED_AT, source_url=url)
        p["content_hash"] = hashlib.sha256(p["text"].encode()).hexdigest()
    write_atomic(folder / "pages.jsonl", pages, True)
    partners = rows("partners.jsonl")
    for p in partners:
        if {"source_review_round42", "source_review_round45"} & p.get("reference_data", {}).keys():
            continue
        ref = p.setdefault("reference_data", {})
        keys = ("eligibility", "gpa_requirement", "language_requirement", "application_info",
                "application_deadline", "quota", "tuition_info", "program_type", "student_summary_zh")
        for key in keys:
            ref.setdefault(key, json.dumps(p[key], ensure_ascii=False) if isinstance(p[key], dict) else p[key])
        dual_only = str(ref["program_type"]).startswith("雙聯")
        p.update(availability_status="needs_confirmation", application_window_status="needs_confirmation",
                 quota_status="not_published",
                 availability_note="當期逐校開放、名額及條件尚未核實；歷年名單不可自動沿用為116學年度。",
                 application_deadline=PERIOD if not dual_only else "雙聯學位依個別計畫公告，本輪未核實確切期限。",
                 quota="當期名額待核實；舊名額及解釋保留為參考。",
                 program_type="雙聯學位（個別計畫待核對）" if dual_only else "交換學生暨雙聯學位合作（分別核對）" if "雙聯" in ref["program_type"] else "交換學生（當期條件待核對）",
                 tuition_info="須在北科維持註冊並繳學雜費；接待校是否另收學費依協議和計畫，不能一律宣稱免學費。")
        if not dual_only:
            p.update(gpa_requirement=ACADEMIC, language_requirement=LANGUAGE,
                     eligibility=DEGREE + " " + ACADEMIC + " " + LANGUAGE,
                     application_info="\n".join([PERIOD, DOCS[0], SUPPLEMENT] + OBLIGATIONS))
        else:
            p.update(gpa_requirement="雙聯學位成績依個別計畫，不能套用校級交換或學海獎助條件。",
                     language_requirement="雙聯學位語檢須逐計畫核對。",
                     eligibility="雙聯學位申請資格尚待逐項核對。",
                     application_info="雙聯學位申請流程、文件與接待校條件尚待逐項核對。")
        # Two entries explicitly appear as unavailable on the retrieved list.
        if any(n in p["school_name"] for n in ("Universidad del Istmo Guatemala", "Universidad del Valle de Guatemala")):
            p.update(availability_status="not_open", application_window_status="closed",
                     availability_note="母校現行推薦學校名單明列未開放申請；後續是否重開待公告。")
        for key in ("quota", "colleges", "degree_levels", "language_requirement", "study_period"):
            p.setdefault("field_evidence", {})[key] = {
                "source_url": PARTNERS, "status": "needs_confirmation", "checked_at": CHECKED_AT,
                "note": "母校名單明示僅供參考，接待校當期條件與名額尚未核實。"}
        p["student_summary_zh"].update(eligibility_points=[p["eligibility"]],
            application_deadline=p["application_deadline"], application_steps=[p["application_info"]],
            quota=p["quota"], tuition_points=[p["tuition_info"]])
    write_atomic(folder / "partners.jsonl", partners, True)
    by_name = {p["school_name"]: p for p in partners}
    workflows = rows("application_workflows.jsonl")
    for w in workflows:
        if {"source_review_round42", "source_review_round45"} & w.get("reference_data", {}).keys():
            continue
        p = by_name[w["school_name"]]
        dual_only = p["program_type"].startswith("雙聯")
        w.update(program_type=p["program_type"], applicability_status="needs_confirmation",
                 applicability_note="母校共用規則部分核對；個別接待校、年度與計畫未核實。",
                 coverage_status="official_partial", coverage_note="本輪不能證明整筆或全部116學年度流程已核實。",
                 last_checked=CHECKED_AT)
        for s in w["steps"]:
            s.update(deadline_at=None, deadline_status="needs_confirmation",
                     deadline_reminder_eligible=False, support_status="needs_confirmation", needs_confirmation=True)
        if dual_only:
            for s in w["steps"]:
                s.update(summary="雙聯學位此步驟尚待個別計畫核對。", details=[],
                         document_requirements=[], submission={"method": "unknown"})
            continue
        stages = [
            ("確認校級與接待校資格", [DEGREE, ACADEMIC, LANGUAGE], GENERAL),
            ("校級申請表簽名後上傳指定連結", DOCS, STEP1),
            ("確認媒合與補申請條件", [SUPPLEMENT, "校內推薦不等於接待校錄取。"], STEP2),
            ("依接待校通知申請並準備行前文件", [OBLIGATIONS[0], "接待校線上、紙本或電子送件依個別通知。"], STEP2),
            ("完成修課、返國繳件及獎助核銷", OBLIGATIONS[1:], STEP3),
        ]
        assert len(w["steps"]) == len(stages)
        for s, (title, details, url) in zip(w["steps"], stages, strict=True):
            s.update(title=title, summary=details[0], details=details, document_requirements=[],
                     action_url=url, source_urls=[url], checked_at=CHECKED_AT,
                     submission={"method": "online", "portal_url": STEP1} if url == STEP1 else {"method": "mixed"})
    write_atomic(folder / "application_workflows.jsonl", workflows, True)
    destinations = rows("destination_profiles.jsonl")
    for dest in destinations:
        if {"source_review_round42", "source_review_round45"} & dest.get("reference_data", {}).keys():
            continue
        p = by_name[dest["school_name"]]
        dest.setdefault("reference_data", json.loads(json.dumps({
            "cost_summary": dest["cost_summary"],
            "student_guide_sections": dest["student_guide_sections"],
        }, ensure_ascii=False)))
        dest.update(cost_summary="本校當期每月生活費尚未核實；原國家預設金額不能視為該校官方費用。",
                    coverage_status="official_partial",
                    coverage_note="母校指定條文部分查核；接待校費用、住宿、簽證及其他生活主張仍待逐項核對。",
                    last_checked=CHECKED_AT)
        for section in dest["student_guide_sections"]:
            if section["key"] == "cost":
                section.update(summary=dest["cost_summary"],
                    points=[dest["cost_summary"], p["tuition_info"]] + SCHOLARSHIPS,
                    caution="獎助條件與核定金額不能當每位學生可領的預算。",
                    source_urls=[SCHOLARSHIP, STEP2])
            elif section["key"] == "courses":
                section.update(summary=OBLIGATIONS[1], points=[OBLIGATIONS[1]],
                    caution="以上為校級交換；雙聯及院系級計畫另查。接待校課程與採認須逐校確認。",
                    source_urls=[PLAN, STEP2])
            elif section["key"] == "arrival":
                section.update(title="行前與返國程序按階段辦理",
                    summary=OBLIGATIONS[2], points=OBLIGATIONS,
                    caution="以上為校級交換共用說明；雙聯及院系級計畫另查。",
                    source_urls=[STEP3])
    write_atomic(folder / "destination_profiles.jsonl", destinations, True)
    for name in ("catalog-completeness.json", "verification_status.json"):
        value = read(name)
        value.update(verified_at=None, checked_at=CHECKED_AT, whole_partner_records_verified=0)
        if name.startswith("catalog"):
            value.update(open_partners=0, reference_only_partners=0, needs_confirmation_partners=204,
                         not_open_partners=2, active_term=PERIOD)
        else:
            value.update(status="partial_review", note="母校指定條文部分核對，0筆整筆核實。")
        write_atomic(folder / name, value)
    provenance = read("import_provenance.json")
    if not any(s["file"] == SNAPSHOT for s in provenance["sources"]):
        provenance["sources"].append({"file": SNAPSHOT, "sha256": SNAPSHOT_SHA, "role": "bounded_source_review"})
    write_atomic(folder / "import_provenance.json", provenance)
    from .ntut_ips_review import apply_ntut_ips_review
    apply_ntut_ips_review(root)
    from .vilnius_akita_review import apply_vilnius_akita_review
    apply_vilnius_akita_review(root, "ntut")
