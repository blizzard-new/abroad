"""Bounded NTOU home-rule and dated roster review, not host verification."""
from __future__ import annotations

from collections import Counter
import hashlib
import json
from pathlib import Path

from .ntust_source_review import write_atomic

CHECKED_AT = "2026-10-20T22:01:23+00:00"
SNAPSHOT = "sources/ntou/reviewed_20261021_sources.json"
SNAPSHOT_SHA = "79526f85a4977e6b25d458f60f32c9ede7f0175cde3b4891d08cbdc3d6fdda37"
PAGE = "https://oia.ntou.edu.tw/p/412-1022-6958.php?Lang=zh-tw"
BROCHURE = "https://oia.ntou.edu.tw/var/file/22/1022/img/1029/779655790.pdf"
REGULATIONS = "https://oia.ntou.edu.tw/var/file/22/1022/img/1029/854516693.pdf"
ENFORCEMENT = "https://oia.ntou.edu.tw/var/file/22/1022/img/1029/777268759.pdf"
MAINLAND = "https://oia.ntou.edu.tw/p/406-1022-70577,r11.php?Lang=zh-tw"
FORM = "https://forms.gle/DVEtoLngQpVgubj9A"
MAINLAND_FORM = "https://forms.gle/tabQqSXfzzPsnJzV7"
PERIOD = "2027春／秋非大陸交換：2026/05/08中午12:00校內送件已截止，非2027年5月；115-2赴陸2027年2–6月交換：2026/09/30中午12:00已截止，公告明列六校。後續梯次確切申請日期尚未核實。"
ACADEMIC = "111/11/28施行細則第3點及2027簡章要求申請之前一學期學業平均及格，另須符合接待校標準；不能以未標期間的累計GPA2.5／3.0或班排替代。非大陸學業30%、外語30%、書面及面試40%，赴陸學業45%、計畫及其他55%是評分權重，不是資格最低分。"
DEGREE = "111/11/07要點第4點：申請及赴外期間均為海大註冊生，不得為大一上新生或申請當學期畢業生；學士須系所同意，研究生另須指導教授同意。當期申請表還須學院核章；學海獎助排除在職不能直接當所有交換計畫排除條件。"
LANGUAGE = "2027非大陸簡章列TOEFL iBT60、IELTS學術組5.0、TOEIC600擇一，日語JLPT N3以上、韓語TOPIK3以上；須符合選定授課語言與兩校要求。TOEFL分制及效期需核對，不把舊表60套新制6分；通則舊DELF1、DELE Nivel Inicial不自動換成CEFR B1。赴陸依通則得免語檢，接待校另有規定仍須核對。"
DOCS = [
    "2027非大陸：先將指定電子文件PDF寄marberthsu@email.ntou.edu.tw，同信預約親送紙本，主旨OO系-OOO-申請交換學生/獎學金計畫。紙本A4單面、無須裝訂、單層L型資料夾；未支持全部合併單一PDF。辦公9–17時不是截止時刻，未事先溝通不收郵寄或掛號。",
    "文件依第一志願，可選中文或英文一種，不是所有文件均中英各份。申請文件確認單、申請表、歷年成績正本及志願表交紙本；指定電子項目交PDF。表單送出後一天內email申請表PDF，列印本人簽名、系所及學院核章；研究生加指導教授，大學部指導教授欄留白。",
    "歷年成績含原始分數、名次、百分比；學士交大一至前一學期，研究生交大學部及研究所全學年，轉學生加原校成績。語檢須在截止前已應考且有結果，可先附網路結果，正式證明後補；未考或尚無結果不能視為可補。",
    "自傳及讀書計畫範例只供參考，不限定依範例格式；本輪未核實每篇1000–1500字、固定頁數或全部中文。經費分析表是申請獎助必備，未交視為放棄校內一切獎學金；其他佐證依身分及方案。",
    "非大陸最多5個志願，同一學校只能選一個計畫或一個系所，不可把同校多方案重複列志願；母校推薦不等於接待校錄取。雙聯、院級及赴陸不能直接套非大陸同一名單、表單與期限。",
]
MAINLAND_DOCS = [
    "115-2赴陸在2026/09/30中午12:00前交海大指定資料；另用赴陸公告表單。表單PDF列印本人簽名、系所及學院核章，研究生另指導教授；經費來源選自費及其他。勿直接套非大陸承辦信箱。",
    "赴陸清單含確認單、申請表、歷年成績含排名正本、自傳、計畫、經費分析、身分證雙面同張A4及適用佐證。自傳及計畫格式範例非強制；未交經費分析視為放棄校內獎學金。",
    "該公告明列上海海洋、上海海事、中國海洋、江南、廈門、福州六校；上海海事僅商船及交通運輸學院。其他校仍未收到資訊，不能把全體赴陸姊妹校當本梯開放。公告的學分採認註記須另比對現行主管機關與教務規範。",
]
OBLIGATIONS = [
    "交換期間維持海大註冊並繳全額學雜費，接待校依合約免繳、半額或個別費用，不是一律免費。住宿不保證；生活、交通、保險及簽證依個別官方資訊另查。",
    "依接待校修課規定；如接待校無特殊規定，至少一門專業課程，非全員每學期6學分或2門。事前與開課單位確認抵免；研究型、語言型及研究生降修等方案可能無法抵免或不適用學海。",
    "交換結束一個月內返國；延長須於接待校開學後一個月內向海大提出，非返國前才申請。提前終止須兩校同意；無故放棄同一學制不得再申請同計畫。",
    "依簡章行前購買涵蓋出國至返國的醫療、意外及海外急難救助保險並交影本；役男在取得錄取時聯繫國際處辦理出境程序。實際保險及行政要求另依當期通知確認。",
]
AWARDS = [
    "2027簡章結合交換及學海飛颺；赴中國大陸、香港、澳門以外地區研修、具中華民國國籍及臺灣戶籍，排除在職專班。須另符合獎助資格，同一赴外計畫不重複受領政府或本校出國補助；交換錄取不等於獲獎。",
    "111/11/28研修施行細則：機票、適用學費及生活費依審查與計畫；已獲接待校學費減免不再補該學費。非大陸學費原則50%且最高8萬元；赴陸學費全額但不得高於海大學費80%。不能當作每人固定或保證金額。",
    "學海飛颺／惜珠補助機票、學費及生活費，惜珠按個案核定；111校內學海細則要求出國前兩個月簽行政契約，計畫變更另依期限。當期教育部要點及核定金額尚須另查，不能只靠舊校內規則推上限。",
    "2027簡章獎學金受獎生返國兩週內交1500–2000字心得（含至少4張照片）、3分鐘心得影片、另5張研修照片及問卷；非學海受獎生可免影片。四週內完成核銷。這不是全員返國一個月心得規則。赴陸公告受獎生同為兩週心得／照片／問卷、四週核銷。",
    "2027表內部分研究型、語言型或降修方案不適用學海，例如北海道HUSTEP及SRS、琉球部分語言方案、紐芬蘭語言橋接等；須依選定計畫與實際修課核對，不能只按合作校名判斷。",
]


def load_snapshot(root):
    raw = (root / SNAPSHOT).read_bytes()
    if hashlib.sha256(raw).hexdigest() != SNAPSHOT_SHA:
        raise ValueError("NTOU source snapshot hash mismatch")
    return json.loads(raw)


def item(title, details, url=BROCHURE):
    return {"title": title, "details": details, "source": {"title": title, "source_url": url,
        "category": "exchange_application", "summary": details[0] if details else title}}


def review_bundle(root: Path):
    s = load_snapshot(root); folder = root / "src/exchange_info/official_data/ntou"
    read = lambda n: json.loads((folder / n).read_text("utf8"))
    rows = lambda n: [json.loads(x) for x in (folder / n).read_text("utf8").splitlines()]
    d = read("student_dashboard.json")
    d.update(academic_score_minimum=None, academic_gpa_minimum=None, academic_score_rule=ACADEMIC,
        maximum_preferences=None, language_score_minimums={}, last_checked=CHECKED_AT)
    d["selection_rules"].update(undergraduate_gpa_minimum=None, degree_score_minimums={},
        pending_quota_planning=True, partner_requirements_need_confirmation=True, language_certificate_required=False)
    d["eligibility"] = [item("學籍與前一學期及格", [DEGREE, ACADEMIC])]
    d["language_requirements"] = [item("母校附表與接待校另查", [LANGUAGE])]
    d["required_documents"] = [item("非大陸初審", DOCS), item("115-2赴陸", MAINLAND_DOCS, MAINLAND)]
    d["scholarship_info"] = [item("交換與受獎條件分開", [a]) for a in AWARDS]
    d["program_overview"] = [item("部分來源對應", [PERIOD, "39筆對上2027非大陸簡章中文校名、6筆對上赴陸公告；其餘78筆未在本輪兩名單對上，不代表永久終止合作。"])]
    d["document_explanations"] = [{"title": "初審及受獎文件", "summary": DOCS[0], "key_points": DOCS + MAINLAND_DOCS,
        "source": item("2027簡章", [], BROCHURE)["source"], "document_url": BROCHURE,
        "document_type": "official_document", "full_text_extracted": False}]
    d["rule_explanations"] = [{"title": "研修資格及義務", "summary": ACADEMIC, "key_points": [DEGREE, LANGUAGE] + OBLIGATIONS,
        "source": item("研修施行細則", [], ENFORCEMENT)["source"], "document_url": ENFORCEMENT,
        "document_type": "official_document", "full_text_extracted": False}]
    periods = []
    for title, url, deadline in [("2027非大陸交換已截止", BROCHURE, "2026-05-08T12:00:00+08:00"),
        ("115-2赴陸六校已截止", MAINLAND, "2026-09-30T12:00:00+08:00"), ("後續梯次確切日期待核實", PAGE, None)]:
        periods.append({**item(title, [PERIOD], url), "scope": "home_application", "program_types": ["exchange"],
            "academic_year": "115" if "赴陸" in title else None, "application_round": title, "audience": "all_students",
            "opens_at": None, "deadline_at": deadline, "date_status": "verified_exact" if deadline else "needs_confirmation",
            "status": "closed" if deadline else "needs_confirmation", "status_note": PERIOD, "deadline_note": PERIOD,
            "reminder_eligible": False, "checked_at": CHECKED_AT})
    d["application_periods"] = periods; write_atomic(folder / "student_dashboard.json", d)
    write_atomic(folder / "home_rules.json", {"school_id": "ntou", "school_name": d["school_name"], "eligibility": d["eligibility"],
        "selection_rules": d["selection_rules"], "application_periods": periods, "source_urls": [BROCHURE, MAINLAND, REGULATIONS, ENFORCEMENT],
        "verified_at": None, "checked_at": CHECKED_AT})
    x = read("exchange_info.json"); x.update(application_period=[PERIOD], eligibility=[DEGREE, ACADEMIC], language_requirement=[LANGUAGE],
        required_documents=DOCS + MAINLAND_DOCS, scholarship_info=AWARDS, last_checked=CHECKED_AT); write_atomic(folder / "exchange_info.json", x)
    x = read("documents.json"); x.update(required_documents=DOCS + MAINLAND_DOCS, source_urls=[BROCHURE, MAINLAND]); write_atomic(folder / "documents.json", x)
    x = read("scholarships.json"); x.setdefault("reference_data", x["scholarships"])
    x.update(scholarships=d["scholarship_info"], source_urls=[BROCHURE, ENFORCEMENT]); write_atomic(folder / "scholarships.json", x)
    pages = rows("pages.jsonl")
    for page, (title, details) in zip(pages, [("已截止梯次與後續待查", [PERIOD]), ("學籍、成績與語言", [DEGREE, ACADEMIC, LANGUAGE]),
        ("初審文件與不同管道", DOCS + MAINLAND_DOCS), ("行前、修課及返國", OBLIGATIONS), ("獎助條件與期限", AWARDS)], strict=True):
        text = "\n".join(details); page.update(title=title, text=text, summary=text, source_url=BROCHURE, crawled_at=CHECKED_AT,
            content_hash=hashlib.sha256(text.encode()).hexdigest())
    write_atomic(folder / "pages.jsonl", pages, True)
    partners = rows("partners.jsonl")
    for p in partners:
        ref = p.setdefault("reference_data", {})
        for key in ("quota", "colleges", "degree_levels", "study_period", "eligibility", "gpa_requirement", "language_requirement",
            "application_round", "application_deadline", "application_info", "tuition_info", "notes", "semester_dates", "course_restrictions"):
            ref.setdefault(key, p.get(key, ""))
        mainland = p["country"] == "中國大陸"
        match = s["mainland_matches" if mainland else "table_matches"].get(p["school_name"])
        ref["reviewed_source_correspondence"] = json.dumps(match, ensure_ascii=False)
        note = "中文校名對應不驗證英文名稱或接待校當期條件；學制、名額、課程、費用、住宿、圖片及心得仍待查。"
        quota = "2027簡章已截止名額；多計畫合併儲存格須按方案核對，不能直接相加或套下期。" if match and not mainland else "當期名額尚待個別接待校或完整公告核實。"
        tuition = OBLIGATIONS[0]
        if match and match["source_name"] == "西來大學":
            tuition += "2027已截止簡章第28–29頁：學術及IEP方案學雜費減免50%，以4堂課為限，非全免；接待校當期費用另查。"
        if match and match["source_name"] == "素羅娜麗科技大學":
            tuition += "2027已截止簡章第24頁：只減免4學分，額外學分學士550／研究生1650泰銖；當期費用另查。"
        if match and match["source_name"] == "紐芬蘭紀念大學":
            quota = "2027表：一般交換6名兩校區合計、單校區單學期最多4名；橋接語言另有6名合併列，不能逐列相加。當期名額待核實。"
            tuition += "2027表橋接Level1先付加幣2930、開課後退500；Level2先付2250、退400。語言與一般交換分開，當期費用另查。"
        p.update(availability_status="reference_only" if match else "needs_confirmation", availability_note="所核對兩梯均已截止；未對上不等於永久停辦。",
            academic_year="115" if mainland and match else None, application_round="115-2赴陸歷史參考" if mainland else "2027春秋非大陸歷史參考",
            application_window_status="closed" if match else "needs_confirmation", application_deadline=PERIOD,
            quota=quota, quota_status="reference_only" if match and not mainland else "not_published",
            colleges="接待校院系與所選計畫須另核，不將所有母校系所當全部可申請。", degree_levels=DEGREE,
            study_period="校級交換原則一學期以上；2027表依校／計畫限定一或兩學期，雙聯與院級另查。",
            eligibility=DEGREE + " " + ACADEMIC, gpa_requirement=ACADEMIC, language_requirement=LANGUAGE,
            tuition_info=tuition, course_restrictions=OBLIGATIONS[1], semester_dates="國別學期區間只供參考，實際起迄及迎新考試須核接待校校曆。",
            application_info="\n".join([PERIOD] + (MAINLAND_DOCS if mainland else DOCS) + OBLIGATIONS), notes=note)
        if match and match["source_name"] == "上海海事大學": p["colleges"] = "115-2赴陸公告僅商船學院與交通運輸學院；其他學院未列本次開放。"
        for key in ("quota", "colleges", "degree_levels", "language_requirement", "study_period", "semester_dates"):
            p.setdefault("field_evidence", {})[key] = {"source_url": MAINLAND if mainland else BROCHURE,
                "status": "needs_confirmation", "checked_at": CHECKED_AT, "note": note}
        p["student_summary_zh"].update(quota=quota, colleges=p["colleges"], degree_levels=DEGREE, study_period=p["study_period"],
            eligibility_points=[DEGREE, ACADEMIC, LANGUAGE], application_deadline=PERIOD,
            application_steps=(MAINLAND_DOCS if mainland else DOCS) + OBLIGATIONS, tuition_points=[tuition])
    write_atomic(folder / "partners.jsonl", partners, True)
    by_name = {p["school_name"]: p for p in partners}; workflows = rows("application_workflows.jsonl")
    for w in workflows:
        p = by_name[w["school_name"]]; mainland = p["country"] == "中國大陸"; docs = MAINLAND_DOCS if mainland else DOCS
        w.update(academic_year=p["academic_year"], application_round=p["application_round"], effective_application_rounds=[p["application_round"]],
            applicability_status="needs_confirmation", applicability_note=p["notes"], coverage_status="official_partial", coverage_note=p["notes"], last_checked=CHECKED_AT)
        stages = [("確認管道與適用學制", [PERIOD, DEGREE, ACADEMIC, LANGUAGE]), ("初審文件歷史參考", docs),
            ("甄選、志願與接待校錄取", [DOCS[4], "院級及雙聯另依規定；不以此母校表保證接待校錄取。"]),
            ("行前、修課及獎助", OBLIGATIONS + AWARDS[:3]), ("返國及受獎核銷", [OBLIGATIONS[2], AWARDS[3]])]
        for step, (title, details) in zip(w["steps"], stages, strict=True):
            step.update(title=title, summary=details[0], details=details, document_requirements=[], deadline_at=None,
                deadline_status="needs_confirmation", deadline_reminder_eligible=False, deadline_source_url=MAINLAND if mainland else BROCHURE,
                deadline_checked_at=CHECKED_AT, support_status="needs_confirmation", needs_confirmation=True,
                action_url=MAINLAND if mainland else PAGE, source_urls=[BROCHURE, MAINLAND if mainland else ENFORCEMENT], checked_at=CHECKED_AT,
                submission={"method": "unknown"})
            step.pop("responsible_unit", None)
            step["scope"].update(academic_years=["115"] if p["academic_year"] else [], application_rounds=[p["application_round"]])
    write_atomic(folder / "application_workflows.jsonl", workflows, True)
    destinations = rows("destination_profiles.jsonl")
    for dest in destinations:
        dest.setdefault("reference_data", {"cost_summary": dest["cost_summary"], "student_guide_sections": json.loads(json.dumps(dest["student_guide_sections"]))})
        dest["reference_data"].setdefault("campus_life_summary", dest["campus_life_summary"])
        dest["reference_data"].setdefault("sources", json.loads(json.dumps(dest["sources"])))
        dest.update(cost_summary="逐校生活費尚待核實；國家預設估價不作官方金額。", coverage_status="official_partial",
            campus_life_summary=OBLIGATIONS[1] + " 實際課程、校曆及校園生活須核對接待校當期資訊。",
            coverage_note="生活、費用、住宿、簽證、圖片及心得仍待逐項查證。", last_checked=CHECKED_AT)
        for source in dest["sources"]:
            if source["source_url"] == ENFORCEMENT:
                source["summary"] = OBLIGATIONS[1]
        for section in dest["student_guide_sections"]:
            if section["key"] in {"cost", "academics"}:
                details = [dest["cost_summary"], by_name[dest["school_name"]]["tuition_info"]] if section["key"] == "cost" else [OBLIGATIONS[1], AWARDS[4]]
                section.update(title="費用待逐校核對" if section["key"] == "cost" else "修課規定與抵免另核",
                    summary=details[0], points=details, caution=dest["coverage_note"], source_urls=[BROCHURE])
    write_atomic(folder / "destination_profiles.jsonl", destinations, True)
    # The builder generated these texts from templates and country defaults;
    # they are not extracts from the linked students' reports. Keep candidates
    # for later reading, without presenting generated text as personal testimony.
    pending_story = "原有心得連結保留待查；尚未逐篇讀取原文，不提供學長姐經驗摘要或已讀全文的主張。"
    stories = rows("student_experiences.jsonl")
    for story in stories:
        story.setdefault("reference_data", json.loads(json.dumps(story)))
        story.update(title=f"{story['school_name']}：原有心得連結待核對", author_name=None,
            summary=pending_story, summary_zh=pending_story, original_summary="", themes=[],
            theme_summaries={}, theme_summaries_zh={}, content_status="metadata_only",
            perspective="official_directory", source_kind="other", exchange_term=None)
        story["content_hash"] = hashlib.sha256((story["source_url"] + "|metadata_only|" + pending_story).encode()).hexdigest()
    write_atomic(folder / "student_experiences.jsonl", stories, True)
    digests = read("student-experience-digests.json")
    for digest in digests["digests"].values():
        digest.setdefault("reference_data", json.loads(json.dumps(digest)))
        digest.update(report_count=0, summary_zh=pending_story, themes={}, status="needs_confirmation", updated_at=CHECKED_AT)
    write_atomic(folder / "student-experience-digests.json", digests)
    life = rows("student_life.jsonl")
    for entry in life:
        entry.setdefault("reference_data", json.loads(json.dumps(entry)))
        entry.update(evidence=[], status="partial", checked_at=CHECKED_AT,
            notes=["原有文字由共用範本、母校規則及國家預設費用產生，未完成逐校生活原文查核；暫不作生活證據。"])
    write_atomic(folder / "student_life.jsonl", life, True)
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
        if not any(e["file"] == SNAPSHOT for e in x["sources"]):
            x["sources"].append({"file": SNAPSHOT, "sha256": SNAPSHOT_SHA, "role": "bounded_source_review"})
        write_atomic(folder / name, x)
    return dict(counts)
