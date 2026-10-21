"""Bounded PCCU source review, preserving separate selection routes and source conflicts."""
from __future__ import annotations

from collections import Counter
import hashlib
import json
from pathlib import Path

from .ntust_source_review import write_atomic

CHECKED_AT = "2026-10-20T21:19:36+00:00"
SNAPSHOT = "sources/pccu/reviewed_20261021_sources.json"
SNAPSHOT_SHA = "db103f4c83b8f796144c0680e4812d04e9bc769249c030ae28edd8ac149e1c72"
GUIDE = "https://oima.pccu.edu.tw/study-abroad-detail5.htm"
RULE = "https://oima.pccu.edu.tw/Upload/202607/learning_2026071112283508.pdf"
QUOTAS = "https://oima.pccu.edu.tw/Upload/202607/learning_2026071112283510.pdf"
JP = "https://japanese.pccu.edu.tw/p/406-1109-140489,r278.php?Lang=zh-tw"
KR = "https://kor.pccu.edu.tw/p/406-1112-143837,r11.php?Lang=zh-tw"
MAINLAND = "https://mccd.pccu.edu.tw/p/406-1300-148804,r2247.php?Lang=zh-tw"
MAINLAND_PORTAL = "https://recruit.sce.pccu.edu.tw/ExchangeStud/default.aspx?py=2026&pn=3&pt=50"
FR = "https://french.pccu.edu.tw/p/412-1115-7823.php"
RU = "https://crgarl.pccu.edu.tw/p/16-1113-110334.php?Lang=zh-tw"
AWARD = "https://oima.pccu.edu.tw/news-detail144.htm"
CONFLICT = "赴陸網頁公告為115-2（2027春季），附件首頁及第一節卻寫115-1，附件後文又寫115-2；期限與名單相同，但學期標示衝突須向承辦確認。"
PERIOD = "赴陸第二階段2026/11/03 17:00截止，只適用該階段公告名單；韓文系115-2已於2026/10/06 08:00截止。日文系115學年度第一階段為2025/11/17–28，不能推成2026年。國合組116學年度確切日期本輪未核實。"
ACADEMIC = "各管道分開：國合組依接待校條件，沒有全校共同70／80分、GPA2.5或排名前50%的替代門檻。日文系115簡章要求114-1平均大學部70／碩士80；韓文系按前學期韓文專業成績等甄選；赴陸公告要求前一學期學業60及歷年操行80，個別校另有更高條件。獎學金資格不能當交換資格。"
DEGREE = "國合組學士須在文大修業滿一年，轉學生及碩博士滿一學期；日文系碩士及轉學生須出發前在文大滿一年；韓文系研究生申請前須在文大修滿20學分；赴陸須在文大完成至少一學期。須逐管道確認在學身分及完成修業期間，單憑年級不足以判定通過。"
LANGUAGE = "語言條件依管道、接待校、學程及授課語言核對，不設全校共同TOEFL61／IELTS5／TOEIC575門檻。日文系初審公告說JLPT沒有可免繳；韓文系TOPIK初審可選附，接待校仍可能要求指定等級。不能把檢定有分數或名額表空白視為所有目標校通過。"
DOCS = {
    "oima": ["國合組依當期公告先完成線上申請再送紙本；要點列申請表、歷年成績及排名、接待校要求的有效語檢、其他指定資料、家長保證書、護照及存摺影本，在職者另附任職單位同意。116當期表單、簽章及截止待確認。", "本輪國合組來源不支持所有學生必繳中外文自傳與計畫各1000字、教師推薦信或每學期至少6學分／2門。"],
    "jp": ["日文系115歷史甄選：線上及紙本申請表、成績單（學生專區列印可）、學習計畫、學習服務表及JLPT證明；初審公告明列沒有JLPT可免繳。報名2025/11/17–28，後續成績及志願資料2026/02/23–24送大仁館349室。", "官方計畫範本：留學動機至少200字、計畫第1–3項合計至少500字、留學後生涯規劃至少300字；不是單篇1000字。範本列五個志願欄位。", "115簡章學業資格寫114-1，但甄選配分段寫11301學期，保留此衝突；錄取後有事務費及保證金，已讀簡章未載金額。"],
    "kr": ["韓文系115-2以一個PDF寄wyx11@ulive.pccu.edu.tw，檔名系級_姓名，非紙本。依序放申請表、114-2成績單、書審資料；2026/10/06上午08:00截止，15:00是未收到回信時聯繫承辦的時間。", "書審自傳及學韓文／赴韓動機可用中文或韓文，未見固定字數；TOPIK與活動證明依個人情況附上。志願不限數，韓文專業平均依科目加總除科目數取一位小數。", "韓文系115-2口試2026/10/07 14:10大仁館302；研究生須先在文大修滿20學分，母校分發不等於接待校錄取。"],
    "mainland": ["赴陸第二階段須線上填報並將紙本於2026/11/03 17:00前送大恩館3樓310室。系統產生WORD後調整列印，系主任簽名，研究生另需指導教授簽名；中文自傳格式自由、學習計畫300字以內、歷年成績單含班排名百分比。", "赴陸此階段最多五個志願；家長同意書屬後續外校申請程序。名單分可抵學分與不可抵學分，不能把所有赴陸交換都視為可抵免。", CONFLICT],
    "fr_ru": ["法文組頁面要求中法文自我推薦信，語言依個別校；家長同意與錄取後保證書、1萬元保證金分階段處理。俄文組概述區分交換、自費與雙聯，未提供當期統一文件、名額或確切期限。", "法俄管道逐校當期簡章仍待核對，不套用國合組、日文系、韓文系或赴陸的文件及截止規定。"],
}
OBLIGATIONS = ["出國期間維持文大在學註冊；交換、訪問自費及雙聯之接待校學費不同，名額表的公費欄不能直接視為現金獎學金。", "日文系短期留學一年至少修12學分；韓文系大學部每年最多抵30、研究所8學分是抵免上限，不是最低修課數。其他管道依系所及接待校確認。", "住宿、簽證、保險、學期日期及生活費須逐校確認；錄取與獎助不保證住宿或免全部費用。", "返國辦理成績及抵免、分享或報告依各管道。國際移動力獎學金要求返國一個月內800字心得及5張照片，不能套成所有交換生的統一期限。"]
AWARDS = ["2026/10/20國際移動力獎學金公告：115-2（2027/01–07出國）申請至2026/11/20，未載當日時刻。這是獎學金截止，非交換申請截止。", "新公告列一般生最低2萬元、經濟不利生最低5萬元，須符合資格及核定，不保證錄取交換即獲獎；舊版最高額不能沿用成新公告的上限。", "附件修正要點的通過日期仍印115.00.00、第0000次，正式核定版本須確認。獎助學業／操行條件及不得重複支領規定獨立核對，不用來決定交換資格。", "學海、移地學習及其他補助尚待核對當期規則，不承諾特定金額、排名門檻或自動得獎。"]


def load_snapshot(root: Path):
    raw = (root / SNAPSHOT).read_bytes()
    if hashlib.sha256(raw).hexdigest() != SNAPSHOT_SHA:
        raise ValueError("PCCU review snapshot hash mismatch")
    return json.loads(raw)


def route(program_type: str | None, country: str | None = None):
    text = program_type or ""
    if country == "中國大陸":
        return "mainland"
    if "雙軌" in text:
        return "dual"
    if "日本語文" in text:
        return "jp"
    if "韓國語文" in text:
        return "kr"
    if "法文" in text or "俄文" in text:
        return "fr_ru"
    return "oima"


def item(title, details, url=GUIDE):
    return {"title": title, "details": details, "source": {"title": title, "source_url": url,
        "category": "exchange_application", "summary": details[0] if details else title}}


def review_bundle(root: Path):
    snapshot = load_snapshot(root)
    folder = root / "src/exchange_info/official_data/pccu"
    read = lambda n: json.loads((folder / n).read_text("utf8"))
    rows = lambda n: [json.loads(s) for s in (folder / n).read_text("utf8").splitlines()]
    docs = [p for values in DOCS.values() for p in values]
    d = read("student_dashboard.json")
    d.update(academic_score_minimum=None, academic_gpa_minimum=None, academic_score_rule=ACADEMIC,
        maximum_preferences=None, language_score_minimums={}, last_checked=CHECKED_AT)
    d["selection_rules"].update(undergraduate_gpa_minimum=None, degree_score_minimums={},
        excluded_undergraduate_years=[], pending_quota_planning=True,
        partner_requirements_need_confirmation=True, language_certificate_required=False)
    d["eligibility"] = [item("分管道確認資格", [ACADEMIC, DEGREE])]
    d["language_requirements"] = [item("語言條件逐校核對", [LANGUAGE])]
    urls = {"oima": GUIDE, "jp": JP, "kr": KR, "mainland": MAINLAND, "fr_ru": FR}
    d["required_documents"] = [item("文件規定：" + key, values, urls[key]) for key, values in DOCS.items()]
    d["scholarship_info"] = [item("國際移動力獎學金與其他獎助", [a], AWARD) for a in AWARDS]
    d["program_overview"] = [item("文化大學資料部分核對", [PERIOD, CONFLICT,
        "47筆國合組表列名額僅作2026/04/29參考；日韓及赴陸名單依不同管道、梯次保存。逐校其他主張仍待核實。"])]
    d["document_explanations"] = [{"title": "依管道備件", "summary": PERIOD, "key_points": docs,
        "source": item("各管道當期及歷史公告", [], GUIDE)["source"],
        "document_url": GUIDE, "document_type": "official_document", "full_text_extracted": False}]
    d["rule_explanations"] = [{"title": "資格與義務分開核對", "summary": ACADEMIC,
        "key_points": [DEGREE, LANGUAGE] + OBLIGATIONS, "source": item("校級要點", [], RULE)["source"],
        "document_url": RULE, "document_type": "official_document", "full_text_extracted": False}]
    periods = []
    for title, url, deadline, status, note in [
        ("115-2赴陸第二階段（限公告名單）", MAINLAND, "2026-11-03T17:00:00+08:00", "open", CONFLICT),
        ("115-2韓文系", KR, "2026-10-06T08:00:00+08:00", "closed", DOCS["kr"][0]),
        ("115學年度日文系歷史甄選", JP, None, "closed", "2025/11/17–28，來源未載截止時刻；不推算116學年度日期。"),
        ("116國合組日期待確認", GUIDE, None, "needs_confirmation", "本輪未取得確切116學年度日期。"),
    ]:
        periods.append({**item(title, [note], url), "scope": "home_application", "program_types": ["exchange"],
            "academic_year": "116" if title.startswith("116") else "115", "application_round": title,
            "audience": "all_students", "opens_at": None, "deadline_at": deadline,
            "date_status": "verified_exact" if deadline else "needs_confirmation", "status": status,
            "status_note": note, "deadline_note": note, "reminder_eligible": status == "open",
            "checked_at": CHECKED_AT})
    d["application_periods"] = periods
    write_atomic(folder / "student_dashboard.json", d)
    write_atomic(folder / "home_rules.json", {"school_id": "pccu", "school_name": d["school_name"],
        "eligibility": d["eligibility"], "application_periods": periods, "selection_rules": d["selection_rules"],
        "source_urls": list(urls.values()), "verified_at": None, "checked_at": CHECKED_AT})
    x = read("exchange_info.json"); x.update(application_period=[PERIOD, CONFLICT], eligibility=[ACADEMIC, DEGREE],
        language_requirement=[LANGUAGE], required_documents=docs, scholarship_info=AWARDS, last_checked=CHECKED_AT)
    write_atomic(folder / "exchange_info.json", x)
    x = read("documents.json"); x.update(required_documents=docs, source_urls=list(urls.values()))
    write_atomic(folder / "documents.json", x)
    x = read("scholarships.json"); x.setdefault("reference_data", x["scholarships"])
    x.update(scholarships=d["scholarship_info"], source_urls=[AWARD]); write_atomic(folder / "scholarships.json", x)
    specs = [("各管道期限", [PERIOD, CONFLICT], MAINLAND), ("分管道資格", [DEGREE, ACADEMIC, LANGUAGE], RULE),
        ("分管道備件", docs, GUIDE), ("交換義務", OBLIGATIONS, RULE), ("國際移動力獎學金", AWARDS, AWARD)]
    pages = rows("pages.jsonl")
    for page, (title, points, url) in zip(pages, specs, strict=True):
        text = "\n".join(points); page.update(title=title, source_url=url, text=text, summary=text,
            crawled_at=CHECKED_AT, content_hash=hashlib.sha256(text.encode()).hexdigest())
    write_atomic(folder / "pages.jsonl", pages, True)
    quotas = {r["school_name"]: r for r in snapshot["oima_quota_reference"]}
    jp = {r["school_name"]: r for r in snapshot["japanese_name_matches"]}
    kr = {r["school_name"]: r for r in snapshot["korean_name_matches"] if r["school_name"]}
    mainland = {r["matched_school_name"]: r for r in snapshot["mainland_rows"]
        if r["stage"] == "mainland-second" and r["matched_school_name"]}
    partners = rows("partners.jsonl")
    for p in partners:
        name = p["school_name"]; kind = route(p["program_type"], p["country"])
        ref = p.setdefault("reference_data", {})
        for key in ("quota", "eligibility", "gpa_requirement", "language_requirement", "application_round",
                    "application_deadline", "application_info", "tuition_info", "notes"):
            ref.setdefault(key, p.get(key, ""))
        matches = [r for r in (quotas.get(name), jp.get(name), kr.get(name), mainland.get(name)) if r]
        ref["reviewed_route_correspondence"] = json.dumps(matches, ensure_ascii=False)
        current = name in mainland
        source = MAINLAND if current else urls.get(kind, GUIDE)
        route_docs = DOCS["oima"] + (DOCS["jp"] if p["country"] == "日本" else DOCS["fr_ru"]) if kind == "dual" else DOCS[kind]
        closed = kind in {"jp", "kr"}
        quota = "逐管道當期名額待核實；名單校名對應不代表名額開放。"
        if name in quotas:
            quota = "2026/04/29國合組表參考：" + quotas[name]["quota_reference"] + "；與院系管道不合併。"
        if current:
            quota = "115-2赴陸第二階段公告：" + mainland[name]["cells"][3] + "名；" + CONFLICT
        p.update(availability_status="open" if current else "reference_only" if matches else "needs_confirmation",
            availability_note=("僅確認母校第二階段公告列名及名額，接待校最終錄取另審。" + CONFLICT if current
                else "歷史或總表僅供參考；未確認此校當期可申請。"),
            application_round="115-2赴陸第二階段" if current else "115歷史資料／116當期依管道待確認",
            academic_year="115" if current or closed else None,
            application_window_status="open" if current else "closed" if closed else "needs_confirmation",
            application_deadline=DOCS["mainland"][0] if current else PERIOD,
            quota=quota, quota_status="published" if current else "reference_only" if name in quotas else "not_published",
            eligibility=DEGREE + " " + ACADEMIC, gpa_requirement=ACADEMIC, language_requirement=LANGUAGE,
            tuition_info=OBLIGATIONS[0], application_info="\n".join([PERIOD] + route_docs + OBLIGATIONS),
            notes="已部分核對母校來源；當期接待校條件、課程、校曆、費用、住宿、圖片與心得仍待逐項查證。")
        if current:
            p["gpa_requirement"] = "公告共同門檻：前一學期學業60、歷年操行80；個別校：" + mainland[name]["cells"][4]
        for key in ("quota", "colleges", "degree_levels", "language_requirement", "study_period"):
            p.setdefault("field_evidence", {})[key] = {"source_url": QUOTAS if key == "quota" and name in quotas else source,
                "status": "conflict" if current and key == "quota" else "reference_only" if key == "quota" and name in quotas else "needs_confirmation",
                "checked_at": CHECKED_AT, "note": CONFLICT if current else p["notes"]}
        p["student_summary_zh"].update(quota=quota, eligibility_points=[p["eligibility"], p["gpa_requirement"]],
            application_deadline=p["application_deadline"], application_steps=[p["application_info"]], tuition_points=[p["tuition_info"]])
    write_atomic(folder / "partners.jsonl", partners, True)
    by_name = {p["school_name"]: p for p in partners}
    workflows = rows("application_workflows.jsonl")
    for w in workflows:
        p = by_name[w["school_name"]]; kind = route(p["program_type"], p["country"])
        url = urls.get(kind, GUIDE); current = p["school_name"] in mainland
        route_docs = DOCS["oima"] + (DOCS["jp"] if p["country"] == "日本" else DOCS["fr_ru"]) if kind == "dual" else DOCS[kind]
        w.update(academic_year=p["academic_year"], application_round=p["application_round"],
            effective_application_rounds=[p["application_round"]], applicability_status="needs_confirmation",
            applicability_note=CONFLICT if current else "逐校當期條件待查，歷史或總表不能直接確認適用。",
            coverage_status="official_partial", coverage_note=p["notes"], last_checked=CHECKED_AT)
        stages = [("確認申請管道與資格", [DEGREE, p["gpa_requirement"], LANGUAGE]),
            ("依該管道備件及送件", route_docs), ("甄選、分發與錄取確認", ["母校分發與提名不等於接待校錄取；費用、保證金及後續簽署依管道。"]),
            ("接待校申請與行前", OBLIGATIONS[:3]), ("返國及抵免", [OBLIGATIONS[3]])]
        for step, (title, details) in zip(w["steps"], stages, strict=True):
            step.update(title=title, summary=details[0], details=details, document_requirements=[],
                deadline_at=None, deadline_status="needs_confirmation", deadline_reminder_eligible=False,
                deadline_source_url=url, deadline_checked_at=CHECKED_AT, support_status="needs_confirmation",
                needs_confirmation=True, action_url=url, source_urls=[url], checked_at=CHECKED_AT,
                submission={"method": "unknown"})
            step.pop("responsible_unit", None)
            step["scope"].update(academic_years=[p["academic_year"]] if p["academic_year"] else [],
                application_rounds=[p["application_round"]])
        if current:
            w["steps"][1].update(deadline_at="2026-11-03T17:00:00+08:00", deadline_status="verified_exact",
                deadline_reminder_eligible=True, submission={"method": "mixed", "portal_url": MAINLAND_PORTAL,
                    "address": "大恩館3樓310室", "deadline_note": CONFLICT})
        elif kind == "kr":
            w["steps"][1]["submission"] = {"method": "email", "email": "wyx11@ulive.pccu.edu.tw"}
    write_atomic(folder / "application_workflows.jsonl", workflows, True)
    destinations = rows("destination_profiles.jsonl")
    for dest in destinations:
        dest.setdefault("reference_data", {"cost_summary": dest["cost_summary"],
            "student_guide_sections": json.loads(json.dumps(dest["student_guide_sections"]))})
        dest.update(cost_summary="逐校生活費待查；國家預設估價不作官方核實費用。", coverage_status="official_partial",
            coverage_note="住宿、生活、課程、校曆、圖片與心得仍待逐項核對。", last_checked=CHECKED_AT)
        for section in dest["student_guide_sections"]:
            if section["key"] in {"cost", "courses", "arrival"}:
                points = [dest["cost_summary"], OBLIGATIONS[0]] if section["key"] == "cost" else OBLIGATIONS[1:]
                section.update(summary=points[0], points=points, caution=dest["coverage_note"], source_urls=[RULE])
    write_atomic(folder / "destination_profiles.jsonl", destinations, True)
    counts = Counter(p["availability_status"] for p in partners)
    for name in ("catalog-completeness.json", "verification_status.json"):
        x = read(name)
        for target in [x] + ([x["counts"]] if "counts" in x else []):
            target.update(verified_at=None, checked_at=CHECKED_AT, whole_partner_records_verified=0,
                active_term=PERIOD, open_partners=counts["open"], reference_only_partners=counts["reference_only"],
                needs_confirmation_partners=counts["needs_confirmation"])
        if name == "verification_status.json": x["status"] = "partial_review"
        write_atomic(folder / name, x)
    for name in ("import_provenance.json", "import-provenance.json"):
        x = read(name); x["active_cycle_note"] = PERIOD
        for file in sorted((root / "sources/pccu").glob("reviewed_20261021_*")):
            rel = file.relative_to(root).as_posix()
            if not any(s["file"] == rel for s in x["sources"]):
                x["sources"].append({"file": rel, "sha256": hashlib.sha256(file.read_bytes()).hexdigest(), "role": "bounded_source_review"})
        write_atomic(folder / name, x)
    from .generated_content_review import review_generated_content
    review_generated_content(root, "pccu")
    return dict(counts)
