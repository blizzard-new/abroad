"""Bounded source review; school-wide rules never verify an entire partner."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path

CHECKED_AT = "2026-10-20T19:59:08+00:00"
SNAPSHOT = "sources/yzu/reviewed_20261021_tables.json"
SNAPSHOT_SHA = "3e3c4351e9a42a4d505aaf39e3d4a83b9a601a751b765c5b51425a4dddf3f95f"
NOTICE = "https://gao.yzu.edu.tw/index.php/tw/component/content/article/gao-202608261000-1?Itemid=105&catid=8"
GENERAL = "https://gao.yzu.edu.tw/index.php/tw/guo-ji-jiao-liu2/fu-wai-jiao-huan"
MAINLAND = "https://gao.yzu.edu.tw/index.php/tw/guo-ji-jiao-liu2/fu-lu-jiao-huan"
MANAGEMENT = "https://oip.cm.yzu.edu.tw/app_qualify/abrd_es"
TABLE = "https://docs.google.com/spreadsheets/d/1V3j0hkY-MbBEdcy_PUbqUz4pw7fwOvlk/gviz/tq?tqx=out:json"
WISH = "https://gao.yzu.edu.tw/files/Outgoing_Students/IA-CP-05-CF01R1.pdf"
FORM = "https://gao.yzu.edu.tw/files/Outgoing_Students/IA-CP-05-CF02R3.pdf"
OBLIGATIONS = "https://gao.yzu.edu.tw/index.php/tw/?option=com_sppagebuilder&view=page&id=29"
SCHOLARSHIP = "https://gao.yzu.edu.tw/index.php/tw/scholarships/ex-scholarships"
PORTAL = "https://forms.cloud.microsoft/Pages/ResponsePage.aspx?id=rN2entCs_UmzXNvyGVYOL7DT7pQOyW9NrMFvA0vlbZxUM1ZYTTNSMzJGQ0YzWDdMVERaWlhSTERKMC4u"
ACADEMIC = "校級國際交換採系排名與英檢各50%評比分發，未列共同GPA或平均分數門檻；70／80分是境外成績採認或交換後獎助條件，不是申請資格。管理學院另以歷年平均GPA3.0以上為原則，不能改為班排前50%。"
DEGREE = "校級簡報列學士二年級以上、研究生不限年級但須就讀滿一學期；赴陸頁另寫二年級以上學位生，研究生適用仍須確認。管院只列本院學士二至四年級、碩士一至二年級一般生。"
LANGUAGE = "校級初審依當期公告繳兩年內英檢，未列全校共同61／5.5／650門檻；未附英檢公告寫以零分計。一般流程與FAQ對第三外語可否替代英檢說法不同，須確認。接待校語言、版本、單項及授課語言條件逐校核對。赴陸志願表免附英檢，不代表所有接待校免語言要求。"
PERIOD = "115-2校級國際交換2026/08/26開始、09/22中午截止，Early Nomination公告09/11中午；表格部分學校另列日期且有早於公告的日期，須逐校確認。開放日未列09:00，下一梯次尚未核實精確日期。"
MAINLAND_PERIOD = "赴陸初審依各校：同濟10/14、南京10/16、西南／重慶／蘇州／西安交大10/20；武漢同頁並列03/31與10/20須確認。11/01是西南後續學校資料繳交日，未列17:00，不是全組初審截止。其他列寫本次未公告。"
INITIAL_DOCS = [
    "校級國際初審須完成線上表單，並依序裝訂四項紙本送全球處R70208：貼照片並由申請人簽章的志願表、含排名中文歷年成績單、含GPA英文歷年成績單、兩年內英檢影本。",
    "國際初審至多兩志願，線上與紙本志願須一致；語檢正式成績尚未收到可先交含姓名的網路截圖，最晚各校提名前補正式影本。",
    "自傳、學習計畫、推薦信與CF02申請表屬複審階段，不可一律列成校級初審必繳；管院申請另依其表單及R60403A送件規定。",
]
MAINLAND_DOCS = [
    "赴陸初審先交成績單、志願表、台胞證影本（如果已有），通過後才準備各姊妹校資料；已列日期未公告截止時刻。",
    "赴陸志願表可填三校，免附英檢；須列印並簽名送全球處R70208。台胞證部分學校可於出發前一個月補，不可寫成初審一律必須持有。",
    "赴陸頁列二年級以上學位生、操行至少85分，表格限台灣學生；特殊學制及接待校條件仍須確認。",
]
SECOND_DOCS = [
    "國際複審CF02：申請人簽章、系／班主任及院長推薦簽章；非導師／指導教授簽章欄。",
    "複審包含切結書、長期獎助申請、境外選課申請、英文自傳與英文學習計畫各一份、教授英文推薦信、接待校表件、入學證明及個資同意書；選課及入學證明得依表單條件補交。",
    "CF02明列赴陸免英文自傳、英文學習計畫及教授英文推薦信；已核對表單未列共同500字中文計畫要求，個別接待校可另要求。",
]
OBLIGATION_DETAILS = [
    "同意由全球處提名後，併同切結書繳保證金5,000元，完成交換返國後依規定退還；不得自行加上1500字、六張照片或無息等未核實條件。",
    "交流期間持續註冊並繳元智全額學費；最低四門課或12學分、至少一半專業課。簡報把12學分註為ECTS，義務頁未註明換算，實際學分單位須確認。",
    "義務頁規定交換後平均未達大學部70／研究所80、單科不及格或未修滿最低課程時取消獎助，不能當作申請階段GPA門檻。",
    "返國14日內依通知交機票、登機證等獎助文件；學分採認依教務辦法於返國兩個月內提出，兩種期限分開。",
    "大陸頁另列返國報告2000字以上附圖、簡報與學習影片；國際組不得套用未核實的1500字六張照片規格。",
]
SCHOLARSHIPS = [
    "國際與兩岸交流獎助申請經系院審核後最遲出國前三週送全球處，依當年度標準及核定辦理；未核實按地區每月5,000至12,000元的固定給付說法。",
    "115千人出國計畫頁列英語密集課程上限45,000元、姐妹校學分課程上限35,000元，須具其計畫資格，不能視為所有交換生自動獲獎。",
    "學海及其他獎助另依當期方案審查；核銷文件原則返國14日內繳交，補助金額與重複領取限制仍須按各計畫核定。",
]


def load_tables(root: Path) -> dict:
    body = (root / SNAPSHOT).read_bytes()
    if hashlib.sha256(body).hexdigest() != SNAPSHOT_SHA:
        raise ValueError("YZU source generation changed; repeat review")
    return json.loads(body)


def matching_rows(partner: dict, tables: dict) -> tuple[str, list]:
    matches = [r for r in tables["international"] if r["record_name"] == partner["school_name"]]
    if matches:
        return "international", matches
    if partner["country"] == "中國大陸":
        name = partner["school_name"].split(" ", 1)[0]
        return "mainland", [r for r in tables["mainland"][0][1:] if r[0] == name]
    if "管理學院" in partner["program_type"]:
        return "management", []
    return "unmatched", []


def deadline_text(group: str, rows: list) -> str:
    if group == "international":
        c = rows[0]["cells"]
        early = c["B"]
        home = "2026/09/22中午（一般初審，已截止）"
        if early:
            home = f"表格Early Nomination列{early}；總公告列09/11中午，其他日期的適用及時刻須確認（均已過）"
        return f"校內：{home}；表列接待校提名{c['V'] or '未填'}、申請{c['W'] or '未填'}，未列時刻。"
    if group == "mainland" and rows:
        text = "；".join(f"初審{r[1]}、學校資料{r[2]}" for r in rows)
        return text + ("；同校兩列不同日期並存，適用期別須確認。" if len(rows) > 1 else "；未公告截止時刻。")
    return "當期適用期限尚待確認；不得沿用校級國際或大陸組的日期。"


def write_atomic(path: Path, value, lines=False):
    old = path.read_bytes()
    text = ("\n".join(json.dumps(v, ensure_ascii=False) for v in value) if lines else json.dumps(value, ensure_ascii=False, indent=2)) + "\n"
    body = text.replace("\n", "\r\n").encode("utf8") if b"\r\n" in old else text.encode("utf8")
    if body != old:
        temp = path.with_name(path.name + ".audit-tmp")
        assert not temp.exists()
        temp.write_bytes(body)
        os.replace(temp, path)


def item(title, details, url=GENERAL, category="exchange_application"):
    return {"title": title, "details": details, "source": {"title": title, "source_url": url, "category": category}}


def review_bundle(root: Path):
    tables = load_tables(root)
    folder = root / "src/exchange_info/official_data/yzu"
    read = lambda name: json.loads((folder / name).read_text("utf8"))
    d = read("student_dashboard.json")
    d.update(last_checked=CHECKED_AT, academic_score_minimum=None, academic_gpa_minimum=None,
             academic_score_rule=ACADEMIC, language_score_minimums={})
    d["selection_rules"].update(partner_requirements_need_confirmation=True, undergraduate_rank_maximum=None)
    d["program_overview"] = [item("三種申請管道分開核對", [PERIOD, MAINLAND_PERIOD, "既有90校紀錄尚未全部核實；管理學院與全球處名額不得直接相加。"])]
    d["eligibility"] = [item("學業與學制", [ACADEMIC, DEGREE])]
    d["language_requirements"] = [item("語言證明及接待校規定", [LANGUAGE])]
    d["required_documents"] = [
        item("校級國際初審", INITIAL_DOCS, NOTICE),
        item("赴陸初審", MAINLAND_DOCS, MAINLAND),
        item("通過初審後複審", SECOND_DOCS, FORM),
    ]
    d["scholarship_info"] = [item("獎助條件", [s], SCHOLARSHIP, "scholarship") for s in SCHOLARSHIPS]
    d["document_explanations"] = [{"title": "初審與複審分開", "summary": INITIAL_DOCS[0],
                                  "key_points": INITIAL_DOCS + SECOND_DOCS, "source": item("表件", [], FORM)["source"]}]
    d["rule_explanations"] = [{"title": "交換後義務", "summary": OBLIGATION_DETAILS[0],
                              "key_points": OBLIGATION_DETAILS, "source": item("選送生義務", [], OBLIGATIONS)["source"]}]
    base = {"scope": "home_application", "program_types": ["exchange"], "academic_year": "115",
            "audience": "applicants", "opens_at": None, "checked_at": CHECKED_AT, "reminder_eligible": False}
    d["application_periods"] = [
        {**base, **item("115-2校級國際初審（已截止）", [PERIOD], NOTICE, "deadline"),
         "application_round": "115-2 國際交換", "deadline_at": "2026-09-22T12:00:00+08:00",
         "date_status": "verified_exact", "status": "closed", "status_note": PERIOD, "deadline_note": INITIAL_DOCS[0]},
        {**base, **item("赴陸初審與學校資料分別辦理", [MAINLAND_PERIOD], MAINLAND, "deadline"),
         "application_round": "依各校公告", "deadline_at": None, "date_status": "needs_confirmation",
         "status": "needs_confirmation", "status_note": MAINLAND_PERIOD, "deadline_note": MAINLAND_DOCS[0]},
    ]
    write_atomic(folder / "student_dashboard.json", d)
    h = read("home_rules.json")
    h.update(eligibility=d["eligibility"], application_periods=d["application_periods"],
             verified_at=None, review_status="partial_review", checked_at=CHECKED_AT)
    h["selection_weights"]["management_oip"] = {"academic_gpa_minimum_in_principle": 3.0, "source_url": MANAGEMENT}
    write_atomic(folder / "home_rules.json", h)
    x = read("exchange_info.json")
    x.update(academic_year=["115"], application_period=[PERIOD, MAINLAND_PERIOD],
             eligibility=[ACADEMIC, DEGREE] + OBLIGATION_DETAILS, language_requirement=[LANGUAGE],
             required_documents=INITIAL_DOCS + MAINLAND_DOCS + SECOND_DOCS,
             scholarship_info=SCHOLARSHIPS, last_checked=CHECKED_AT)
    write_atomic(folder / "exchange_info.json", x)
    write_atomic(folder / "documents.json", {"school_name": d["school_name"], "required_documents": d["required_documents"], "source_urls": [NOTICE, MAINLAND, FORM]})
    write_atomic(folder / "scholarships.json", {"school_name": d["school_name"], "scholarships": d["scholarship_info"], "source_urls": [SCHOLARSHIP]})
    pages = [json.loads(s) for s in (folder / "pages.jsonl").read_text("utf8").splitlines()]
    values = [x["application_period"], x["eligibility"], x["language_requirement"], x["required_documents"], x["scholarship_info"]]
    assert len(pages) == len(values)
    for p, vals in zip(pages, values, strict=True):
        p.update(text="\n".join(vals), summary="\n".join(vals), source_url=GENERAL,
                 published_at=None, crawled_at=CHECKED_AT)
        p["content_hash"] = hashlib.sha256(p["text"].encode()).hexdigest()
    write_atomic(folder / "pages.jsonl", pages, True)
    partners = [json.loads(s) for s in (folder / "partners.jsonl").read_text("utf8").splitlines()]
    for p in partners:
        group, rows = matching_rows(p, tables)
        ref = p.setdefault("reference_data", {})
        keys = ("application_deadline", "application_info", "eligibility", "language_requirement",
                "gpa_requirement", "quota", "tuition_info", "notes", "student_summary_zh", "semester_dates")
        for k in keys:
            old_value = p.get(k)
            ref.setdefault(k, json.dumps(old_value, ensure_ascii=False) if isinstance(old_value, dict) else old_value or "")
        p.update(availability_status="reference_only" if group == "international" else "needs_confirmation",
                 quota_status="reference_only", application_window_status="closed" if group == "international" else "needs_confirmation",
                 availability_note="僅核對指定母校公告與表格；初審已過或期別待確認，不代表新一期開放。",
                 application_deadline=deadline_text(group, rows), eligibility=DEGREE + " " + ACADEMIC,
                 language_requirement=LANGUAGE, gpa_requirement=ACADEMIC,
                 application_info=" ".join(MAINLAND_DOCS if group == "mainland" else INITIAL_DOCS) if group in {"mainland", "international"} else "院級或歷史方案的當期送件資料須另核，不套用校級初審文件。",
                 tuition_info="交換期間繳元智全額學費；接待校學費與住宿費須依各協議確認，不能保證所有方案免學費或免住宿。")
        source = MAINLAND if group == "mainland" else TABLE if group == "international" else MANAGEMENT if group == "management" else GENERAL
        if group == "international":
            c = rows[0]["cells"]
            p.update(source_url=NOTICE, quota=f"115-2校級表列{c['H']}名（初審已截止）" if c["H"] is not None else "115-2校級表格名額空白，待確認",
                     gpa_requirement=ACADEMIC + f" 校級表P欄原文：{c['P'] if c['P'] is not None else '空白，待確認'}",
                     language_requirement=LANGUAGE + f" 校級表Q欄原文：{c['Q'] or '空白，待確認'}",
                     course_restrictions=f"115-2校級表O欄原文：{c['O'] or '空白，待確認'}",
                     semester_dates=f"115-2校級表U欄原文：{c['U'] or '空白，待確認'}")
            if c["E"] == "越南胡志明市外語資訊大學":
                p["semester_dates"] += "；原表結束年份早於開始，須確認，不自行改年。"
            if c["E"] == "美國俄亥俄州立大學":
                p["tuition_info"] = "115-2校級表Y欄明列本協議不免學費（tuition not waived），總費用估計USD33,964；實際收費及當期可申請性須向接待校確認。"
            if "管理學院" in p["program_type"]:
                p["quota"] += "；管理學院另有獨立方案，名額與條件另核，不加總。"
        elif group == "mainland" and rows:
            p.update(source_url=MAINLAND, quota="；".join(dict.fromkeys(r[3] for r in rows)) + "（頁面表列，非新期保證名額）",
                     language_requirement="母校赴陸志願表免附英檢；接待校及授課語言個別要求仍待確認。",
                     eligibility=" ".join(MAINLAND_DOCS[2:]) + " " + DEGREE)
        elif group == "management":
            p["gpa_requirement"] = "管院院級交換原則要求歷年平均GPA3.0以上；班排50%不能替代。接待校個別要求另核。"
        ev = p.setdefault("field_evidence", {})
        for key in ("quota", "colleges", "degree_levels", "language_requirement", "study_period", "gpa_requirement"):
            ev[key] = {"source_url": source, "academic_year": "115", "checked_at": CHECKED_AT,
                       "status": "reference_only" if group == "international" else "needs_confirmation",
                       "note": "僅母校表列內容對照；接待校現行規定與整筆其餘內容尚未核實。"}
        p["notes"] = "指定母校來源部分查核，其他生活、費用、校曆、照片與心得仍待確認。"
        p["student_summary_zh"].update(quota=p["quota"], application_deadline=p["application_deadline"],
                                      eligibility_points=[p["eligibility"], p["gpa_requirement"], p["language_requirement"]],
                                      application_steps=[p["application_info"], " ".join(SECOND_DOCS)],
                                      tuition_points=[p["tuition_info"]] + OBLIGATION_DETAILS[:2])
    write_atomic(folder / "partners.jsonl", partners, True)
    by_name = {p["school_name"]: p for p in partners}
    workflows = [json.loads(s) for s in (folder / "application_workflows.jsonl").read_text("utf8").splitlines()]
    for w in workflows:
        p = by_name[w["school_name"]]
        group, _ = matching_rows(p, tables)
        w.update(applicability_status="needs_confirmation", effective_application_rounds=["115-2"],
                 applicability_note=p["availability_note"], coverage_status="official_partial",
                 coverage_note="指定母校條文已對照；接待校當期申請與全部其餘內容未完成查核。")
        for s in w["steps"]:
            s.update(deadline_at=None, deadline_status="needs_confirmation", deadline_reminder_eligible=False,
                     support_status="needs_confirmation", needs_confirmation=True)
            s["scope"].update(academic_years=["115"], application_rounds=["115-2"])
        w["steps"][0].update(title="確認申請管道與當期資格", summary=p["eligibility"], details=[p["language_requirement"], p["application_deadline"]])
        w["steps"][1].update(title="依適用管道繳交初審資料", summary=p["application_info"],
                             details=MAINLAND_DOCS if group == "mainland" else INITIAL_DOCS if group == "international" else [p["application_info"]],
                             document_requirements=[], submission={"method": "mixed" if group == "international" else "paper",
                             "portal_url": PORTAL if group == "international" else p["source_url"]})
        w["steps"][2].update(title="依通知確認提名並完成複審", summary=OBLIGATION_DETAILS[0], details=SECOND_DOCS)
        w["steps"][3].update(summary="接待校入學文件、送件方式與住宿申請依個別通知，不能把範例清單當作每校必繳。", details=[p["application_deadline"]])
        w["steps"][4].update(title="完成行前選課與返國獎助、學分採認程序", summary=OBLIGATION_DETAILS[3], details=OBLIGATION_DETAILS)
    write_atomic(folder / "application_workflows.jsonl", workflows, True)
    destinations = [json.loads(s) for s in (folder / "destination_profiles.jsonl").read_text("utf8").splitlines()]
    for dest in destinations:
        p = by_name[dest["school_name"]]
        dest.setdefault("reference_data", json.loads(json.dumps({
            k: dest[k] for k in ("cost_summary", "student_guide_sections", "housing_summary")
        }, ensure_ascii=False)))
        # The builder used country-wide default amounts, even where the table
        # supplied only a semester amount or a link. Do not turn these into a
        # school's verified monthly budget.
        dest["cost_summary"] = "該校當期每月生活費尚未核實；原國別預設估計不能視為校方費用。"
        dest.update(coverage_status="official_partial",
                    coverage_note="母校指定條文部分核對；生活費、住宿、交通、保險與簽證等仍待逐項查證。",
                    last_checked=CHECKED_AT)
        for section in dest["student_guide_sections"]:
            if section["key"] == "cost":
                section.update(summary=dest["cost_summary"],
                               points=[dest["cost_summary"], p["tuition_info"], OBLIGATION_DETAILS[0]],
                               caution=SCHOLARSHIPS[0], source_urls=[GENERAL, SCHOLARSHIP, OBLIGATIONS])
            elif section["key"] == "courses":
                section.update(title="修課要求與學分採認", summary=OBLIGATION_DETAILS[1],
                               points=OBLIGATION_DETAILS[1:4],
                               caution="學分單位及接待校個別課程條件仍待確認。",
                               source_urls=[OBLIGATIONS, GENERAL])
            elif section["key"] == "arrival":
                section.update(summary=p["semester_dates"], points=[p["semester_dates"]] + OBLIGATION_DETAILS[3:],
                               caution="接待校現行校曆與個別繳件通知仍待確認。",
                               source_urls=[TABLE if p["country"] != "中國大陸" else MAINLAND, OBLIGATIONS])
    write_atomic(folder / "destination_profiles.jsonl", destinations, True)
    counts = read("catalog-completeness.json")
    counts.update(open_partners=0, reference_only_partners=53, needs_confirmation_partners=37,
                  whole_partner_records_verified=0, verified_at=None, checked_at=CHECKED_AT,
                  active_term=PERIOD + " " + MAINLAND_PERIOD)
    write_atomic(folder / "catalog-completeness.json", counts)
    status = read("verification_status.json")
    status.update(status="partial_review", checked_at=CHECKED_AT, counts=counts,
                  note="校級53列、赴陸13列及指定共用規則部分對照；0筆整筆核實。")
    write_atomic(folder / "verification_status.json", status)
    provenance = read("import_provenance.json")
    if not any(s["file"] == SNAPSHOT for s in provenance["sources"]):
        provenance["sources"].append({"file": SNAPSHOT, "sha256": SNAPSHOT_SHA, "role": "reviewed_table_snapshot"})
    write_atomic(folder / "import_provenance.json", provenance)
