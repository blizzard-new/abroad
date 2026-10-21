"""Apply the bounded CYCU source review without approving unreviewed claims."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import re

SOURCE_FILE = "sources/cycu/reviewed_20261021_tables.json"
SOURCE_SHA256 = "945fdd4f08b18b24367c86fa1fad1ed412e04cf70f6774005d9494a7e82b803e"
CHECKED_AT = "2026-10-20T19:36:00+00:00"
INTRO = "https://oia.cycu.edu.tw/?p=6336"
DOCS = "https://oia.cycu.edu.tw/?p=6338"
INTERNATIONAL = "https://oia.cycu.edu.tw/?p=9903"
MAINLAND = "https://oia.cycu.edu.tw/?p=6340"
SCHOLARSHIP = "https://oia.cycu.edu.tw/?p=6353"
ACADEMIC = (
    "當期國際第二梯次與大陸公告將GPA3.0列為必備；一般介紹及文件頁則列GPA3.0或歷年系排名前30%。"
    "僅靠排名能否替代GPA須向國際處確認，不能以百分制75分換算。"
    "國際公告另列建築系須系排名前50%及建築設計一至六全數及格。"
)
INTL_PERIOD = "115-2國際第二梯次於2026/09/24開放CYCU表單，10/07中午12:00截止，10/14面試（時段另通知），本梯已截止。"
MAINLAND_PERIOD = "2027春季大陸交換依各校校內截止日送件，表列日期介於2026/09/24至11/30，未列共同開始日或截止時刻；部分校名及空白日期仍待確認。"
INTL_SUBMIT = "完成CYCU表單，將本人及系所簽章的申請表正本送維澈樓701B，其他紙本自行留存，待國際處通知面試時繳交。"
MAINLAND_SUBMIT = "先完成CYCU表單及申請表正本送維澈樓701B；通過校內甄選後，於各校校內截止日前將該校文件寄至outgoing_exchange@cycu.edu.tw，經承辦確認後送出。"
DOCUMENTS = [
    "申請表須本人簽名、照片及系所主管核章；國際組一封外文教師推薦信（簽名、免彌封），大陸組兩封教師推薦信。",
    "中文歷年成績單須含GPA及系排名；中文個人履歷限一張A4。",
    "自傳及讀書計畫合計至少1000字：大陸組中文，國際組外文。文件頁同時出現英文必備與可用當地語言的說法，國際組語言版本須確認。",
    "國際組須依申請校條件提供有效正式語檢影本，面試帶正本驗證；大陸組母校文件清單未列語檢，接待校條件另核。",
    "在學證明及有利審查資料依文件清單辦理；不得把出國或接待校階段的護照、財力、保險、家長同意書一律提前為母校初審必繳。",
]
SCHOLAR_DETAILS = [
    "頁面上方列115-2（2027春季）國際組2026/11/04 17:00截止，大陸組另行個別通知；但頁面標題寫秋季、內文表單段落仍寫日期待定，須確認適用梯次及各補助期限。",
    "學海飛颺須GPA3.0以上且歷年總平均系排名前30%；學海惜珠須GPA3.0及弱勢身分資格。兩者語言依姊妹校，不是共用英語分數。",
    "學海補助對象為具中華民國國籍及臺灣戶籍、在校就讀一學年以上學生，不含在職專班；研修地不含大陸、香港與澳門。",
    "學海文件合併一份PDF，以學海飛颺或學海惜珠_姓名_科系班級_學號命名；研修計畫約1000至1500字。寄outgoing_exchange@cycu.edu.tw，五個工作天未收確認須聯絡。",
    "校內交換助學金適用國際及大陸交換，另填校內表單、成績單及語檢或有利資料，合併一份PDF寄送。",
    "學海飛颺與校內交換助學金依頁面分80%及20%撥款；出國前提供去程電子機票，返國兩週內交報到單、心得及登機證等。適用補助與個別獲獎通知另核。",
]


def load_tables(root: Path) -> dict:
    body = (root / SOURCE_FILE).read_bytes()
    if hashlib.sha256(body).hexdigest() != SOURCE_SHA256:
        raise ValueError("CYCU reviewed table generation changed; review is required")
    return json.loads(body)


def source_rows(tables: dict, group: str) -> list[list[str]]:
    return [r for r in tables[group]["tables"][0][1:] if r and r[0].strip()]


def match_row(partner: dict, tables: dict) -> tuple[str, list[str] | None]:
    mainland = partner["country"] in {"中國大陸", "大陸地區"}
    group = "mainland" if mainland else "international"
    zh = partner["school_name"].split(" ", 1)[0]
    for row in source_rows(tables, group):
        if mainland:
            name = "北京清華大學" if row[0] == "清華大學" and row[2] == "北京市" else row[0]
        else:
            if row[1] != partner["country"]:
                continue
            name = "".join(x for x in row[0].splitlines() if not re.search("[A-Za-z]", x))
        if name == zh:
            return group, row
    # 大連理工學院 in the source is not silently equated with 大連理工大學.
    return group, None


def deadline_text(group: str, row: list[str] | None) -> str:
    if row is None:
        return "本輪公告未對上此紀錄，尚不能確認當期開放或期限；不能推論合作已終止。"
    if group == "international":
        return INTL_PERIOD
    if not row[4]:
        return "2027春季公告列此校，但校內截止日期空白，須向中原國際處確認。"
    return f"2027春季赴此校的中原校內截止日為2026年{row[4]}；公告未列時刻，不得自行補17:00。"


def evidence(url: str, status: str, note: str) -> dict:
    return {
        "source_url": url, "academic_year": "115",
        "application_round": "115-2（2027春季）", "checked_at": CHECKED_AT,
        "status": status, "note": note,
    }


def review_partner(p: dict, tables: dict) -> None:
    group, row = match_row(p, tables)
    url = MAINLAND if group == "mainland" else INTERNATIONAL
    old = p.setdefault("reference_data", {})
    fields = ("quota", "language_requirement", "study_period", "colleges", "degree_levels",
              "eligibility", "gpa_requirement", "application_deadline", "application_info",
              "housing_info", "semester_dates", "course_restrictions", "notes")
    for key in fields:
        if p.get(key):
            old.setdefault(key, p[key])
    note = deadline_text(group, row)
    p.update(
        availability_status="reference_only" if group == "international" and row else "needs_confirmation",
        quota_status="reference_only",
        availability_note=note,
        application_window_status="closed" if group == "international" and row else "needs_confirmation",
        application_deadline=note,
        application_round="115-2（2027春季）來源核對，其他梯次待確認",
        academic_year="115",
        checked_at=CHECKED_AT,
        gpa_requirement=ACADEMIC,
        housing_info="尚未逐校確認住宿資格、名額、費用與申請方式；原共用敘述不能視為宿舍保證。",
        semester_dates="須查接待校適用學年正式校曆；不能套用國別的一般月份。",
        colleges="母校當期表格未完整列可申請院系；須連同各校備註及接待校規定確認。",
        degree_levels="母校一般資格不等於各接待校開放學制，須按方案及年級確認。",
    )
    p["application_info"] = MAINLAND_SUBMIT if group == "mainland" else INTL_SUBMIT
    if group == "international" and row:
        p["quota"] = f"115-2國際第二梯次表列{row[3]}名（本梯已截止）"
        p["study_period"] = row[2] + ("；研究生僅一學期" if row[0].startswith("匹茲堡州立大學") else "")
        p["language_requirement"] = row[4]
        p["course_restrictions"] = row[5] or "該表備註空白，不代表沒有院系或課程限制。"
        p["eligibility"] = f"{ACADEMIC}\n當期表列申請資格：{row[4]}\n備註：{row[5] or '未列'}"
        if row[0].startswith(("加州州立大學溪口分校", "夏威夷大學希羅校區")):
            p["tuition_info"] = row[5] + "；金額為該梯次母校表列參考，費用範圍及接待校最新帳單仍須確認。"
    else:
        p["quota"] = "本輪所讀當期表格未證實此校交換名額，待確認。"
        p["study_period"] = "2027春季計畫；個別可交換學期數仍待確認。"
        p["language_requirement"] = (
            "大陸組母校文件清單未列語檢；接待校或特定課程要求仍待確認。"
            if group == "mainland" else "本輪公告未對上，既有語檢僅保留歷史參考，須重新核實。"
        )
        p["course_restrictions"] = "所讀來源不足以確認個別院系、學制及課程限制。"
        p["eligibility"] = ACADEMIC + (" 大陸交換限具中華民國國籍學生。" if group == "mainland" else "")
    p["notes"] = f"{note}\n{p['eligibility']}\n{p['course_restrictions']}"
    ev = p.setdefault("field_evidence", {})
    for key in ("quota", "study_period", "colleges", "degree_levels", "language_requirement", "housing_info", "semester_dates"):
        status = "reference_only" if group == "international" and row and key in {"quota", "study_period", "language_requirement"} else "needs_confirmation"
        ev[key] = evidence(url, status, "僅核對母校表列內容及適用梯次，未完成接待校全部條件查核。")
    ev["application_deadline"] = evidence(url, "reference_only" if row and group == "international" else "needs_confirmation", note)
    ev["gpa_requirement"] = evidence(url, "conflict", ACADEMIC)
    p["source_review"] = {
        "source_url": url, "source_sha256": tables[group]["source_sha256"],
        "matched": row is not None, "source_row": row,
        "whole_record_verified": False,
    }
    summary = p.setdefault("student_summary_zh", {})
    for key in ("quota", "study_period", "colleges", "degree_levels", "application_deadline"):
        summary[key] = p[key]
    summary["eligibility_points"] = [p["eligibility"]]
    summary["application_steps"] = [note, p["application_info"]]


def review_workflow(w: dict, partner: dict, tables: dict) -> None:
    group, row = match_row(partner, tables)
    url = MAINLAND if group == "mainland" else INTERNATIONAL
    note = deadline_text(group, row)
    w.update(
        applicability_status="needs_confirmation", applicability_note=note + " " + ACADEMIC,
        effective_application_rounds=["115-2"], coverage_status="official_partial",
        coverage_note="僅核對當期母校公告與文件清單；資格衝突、接待校要求及其餘內容仍待核實。",
        last_checked=CHECKED_AT,
    )
    for s in w["steps"]:
        s.update(
            deadline_at=None, deadline_status="needs_confirmation", deadline_reminder_eligible=False,
            deadline_source_url=url, deadline_checked_at=CHECKED_AT, checked_at=CHECKED_AT,
            support_status="needs_confirmation", needs_confirmation=True,
        )
        s["scope"]["academic_years"] = ["115"]
        s["scope"]["application_rounds"] = ["115-2"]
        s["source_urls"] = list(dict.fromkeys([url, DOCS, *s.get("source_urls", [])]))
    first, submit, interview, host, travel = w["steps"]
    first.update(title="確認當期母校資格與接待校條件", summary=ACADEMIC, details=[partner["eligibility"], note])
    submit.update(
        title="完成CYCU表單及繳交申請表正本至維澈樓701B",
        summary=MAINLAND_SUBMIT if group == "mainland" else INTL_SUBMIT,
        details=DOCUMENTS + [note],
        document_requirements=[{"name": text, "source_urls": [DOCS], "needs_confirmation": True} for text in DOCUMENTS],
        submission={"method": "mixed", "office": "中原大學國際暨兩岸教育處（維澈樓701B）", "portal_url": url},
        action_url=url,
    )
    first["responsible_unit"] = "中原大學國際暨兩岸教育處（維澈樓701B）"
    if group == "international" and row:
        submit.update(deadline_at="2026-10-07T12:00:00+08:00", deadline_status="verified_exact")
        interview.update(summary="115-2國際第二梯次面試為2026/10/14，時段另行通知；不能作10/01 17:00截止事件。",
                         details=["2026/10/08 17:00前通知書面審核結果；面試時間依通知。"], timing="2026/10/14（時段另通知）")
    else:
        interview.update(summary="依個別通知參加甄選；未取得此校本梯次確切面試時間。", details=[note], timing=None)
    host.update(summary="通過母校甄選後，依此校適用學年文件與期限申請；最終錄取仍由接待校審查。",
                details=[partner["language_requirement"], partner["course_restrictions"]])
    if group == "mainland" and row:
        host["details"] += [f"母校表列本校應備文件：{row[3] or '未列，須洽承辦'}", note]
    travel.update(summary="依適用研修規定及錄取通知辦理選課、學分抵免、簽證、保險與獎助。", details=[
        "一般頁面對每學期至少6學分與2門課的描述有差異，應向系所及國際處確認；不得僅以2門課自動認定合規。",
        *SCHOLAR_DETAILS[:2],
    ])


def review_destination(d: dict, p: dict) -> None:
    reference = d.setdefault("reference_data", {})
    for key in ("housing_summary", "campus_life_summary", "student_guide_sections", "first_72_hours"):
        if key not in reference:
            reference[key] = json.loads(json.dumps(d.get(key), ensure_ascii=False))
    d["housing_summary"] = p["housing_info"]
    d["campus_life_summary"] = p["semester_dates"] + " " + p["course_restrictions"]
    for section in d.get("student_guide_sections", []):
        key = section.get("key")
        if key in {"housing", "courses", "arrival"}:
            text = p["housing_info"] if key == "housing" else p["semester_dates"] if key == "arrival" else p["course_restrictions"]
            section.update(summary=text, points=[text], caution="此部分須再核對接待校適用學年的正式資訊。")
    if d.get("first_72_hours"):
        d["first_72_hours"][0]["detail"] = p["semester_dates"]
    d.update(coverage_status="official_partial", coverage_note="本輪只核對母校公告及指定共同敘述；生活費、簽證、個別接待校資訊及其餘內容尚未全部查證。")


def item(title: str, details: list[str], url: str, category: str = "exchange_application") -> dict:
    return {"title": title, "details": details, "source": {"title": title, "source_url": url, "category": category}}


def write_atomic(path: Path, data: object, *, lines: bool = False) -> None:
    text = ("\n".join(json.dumps(r, ensure_ascii=False) for r in data) if lines
            else json.dumps(data, ensure_ascii=False, indent=2)) + "\n"
    previous = path.read_bytes() if path.exists() else b""
    encoded = text.replace("\n", "\r\n").encode("utf8") if b"\r\n" in previous else text.encode("utf8")
    if previous == encoded:
        return
    temp = path.with_name(path.name + ".audit-tmp")
    assert not temp.exists(), temp
    temp.write_bytes(encoded)
    os.replace(temp, path)


def review_bundle(root: Path) -> None:
    tables = load_tables(root)
    folder = root / "src/exchange_info/official_data/cycu"
    partners = [json.loads(x) for x in (folder / "partners.jsonl").read_text("utf8").splitlines()]
    for partner in partners:
        review_partner(partner, tables)
    by_name = {p["school_name"]: p for p in partners}
    workflows = [json.loads(x) for x in (folder / "application_workflows.jsonl").read_text("utf8").splitlines()]
    for w in workflows:
        review_workflow(w, by_name[w["school_name"]], tables)
    destinations = [json.loads(x) for x in (folder / "destination_profiles.jsonl").read_text("utf8").splitlines()]
    for d in destinations:
        review_destination(d, by_name[d["school_name"]])
    write_atomic(folder / "destination_profiles.jsonl", destinations, lines=True)
    dashboard = json.loads((folder / "student_dashboard.json").read_text("utf8"))
    dashboard.update(last_checked=CHECKED_AT, academic_score_minimum=None, academic_score_rule=ACADEMIC, language_score_minimums={})
    dashboard["selection_rules"].update(undergraduate_rank_maximum=None, partner_requirements_need_confirmation=True)
    dashboard["eligibility"] = [item("母校資格與官方說法差異", [
        ACADEMIC, "當期公告排除大一新生、轉學未滿一年及已提出當學期提前畢業者；大陸組限中華民國國籍。",
        "一般介紹要求就讀兩學期，研究所新生適用性及其他特殊身分仍須確認。"], INTRO)]
    dashboard["language_requirements"] = [item("依申請校核對語言資格", [
        "沒有已核實的全校共用TOEFL、IELTS或TOEIC最低分數；語檢效期、版本、學制及課程須逐校確認。",
        "大陸組母校文件清單未列語檢，不能推論接待校全部課程免語言條件。"], DOCS)]
    dashboard["required_documents"] = [item("當期送件與文件清單", [INTL_SUBMIT, MAINLAND_SUBMIT, *DOCUMENTS], DOCS)]
    dashboard["scholarship_info"] = [item("獎助申請期限與適用差異", [detail], SCHOLARSHIP, "scholarship") for detail in SCHOLAR_DETAILS]
    periods = dashboard["application_periods"]
    periods[0]["source"]["summary"] = "115-2第二梯次10/07中午截止、10/14面試，20所學校表列50個名額。"
    periods[1]["audience"] = "conditional_applicants"
    periods[2]["audience"] = "selected_applicants"
    periods[0].update(details=[INTL_PERIOD, INTL_SUBMIT, "當期表列20所、50個名額；此為表列加總，不能視為下一梯可用名額。"],
        opens_at=None, deadline_at="2026-10-07T12:00:00+08:00", date_status="verified_exact", status="closed",
        status_note=INTL_PERIOD, deadline_note=INTL_SUBMIT, reminder_eligible=False, checked_at=CHECKED_AT)
    periods[1].update(details=[MAINLAND_PERIOD, MAINLAND_SUBMIT, "大陸組限具中華民國國籍學生；表列22列，蘭州期限空白，大連校名尚待確認。"],
        opens_at=None, deadline_at=None, date_status="needs_confirmation", status="needs_confirmation",
        status_note=MAINLAND_PERIOD, deadline_note=MAINLAND_SUBMIT, reminder_eligible=False, checked_at=CHECKED_AT)
    periods[2].update(details=SCHOLAR_DETAILS[:1], opens_at=None, deadline_at=None, date_status="needs_confirmation",
        status="needs_confirmation", status_note=SCHOLAR_DETAILS[0],
        deadline_note="國際組公告11/04 17:00與表單日期待定並存，大陸組個別通知；確認前不建立精確提醒。",
        reminder_eligible=False, checked_at=CHECKED_AT)
    # Summaries must not repeat obsolete instructions after the structured update.
    dashboard["document_explanations"] = [{"title": "申請文件及送件階段", "summary": INTL_SUBMIT, "key_points": DOCUMENTS, "source": {"title": "申請應繳文件", "source_url": DOCS, "category": "exchange_application"}}]
    dashboard["rule_explanations"] = [{"title": "資格差異仍須確認", "summary": ACADEMIC, "key_points": [ACADEMIC], "source": {"title": "交換生計畫介紹", "source_url": INTRO, "category": "exchange_application"}}]
    dashboard["program_overview"] = [item("115-2資料適用範圍", [INTL_PERIOD, MAINLAND_PERIOD, "下一梯次開放日期尚待正式公告核實。"], INTERNATIONAL)]
    home = json.loads((folder / "home_rules.json").read_text("utf8"))
    home.update(eligibility=dashboard["eligibility"], application_periods=periods, verified_at=None,
                review_status="partial_review", checked_at=CHECKED_AT)
    exchange = json.loads((folder / "exchange_info.json").read_text("utf8"))
    exchange.update(
        application_period=[INTL_PERIOD, MAINLAND_PERIOD, SCHOLAR_DETAILS[0]],
        eligibility=dashboard["eligibility"][0]["details"],
        language_requirement=dashboard["language_requirements"][0]["details"],
        required_documents=[INTL_SUBMIT, MAINLAND_SUBMIT, *DOCUMENTS],
        scholarship_info=SCHOLAR_DETAILS, partner_universities=[p["school_name"] for p in partners], last_checked=CHECKED_AT,
    )
    for filename, data, lines in [
        ("partners.jsonl", partners, True), ("application_workflows.jsonl", workflows, True),
        ("student_dashboard.json", dashboard, False), ("home_rules.json", home, False),
        ("exchange_info.json", exchange, False),
        ("documents.json", {"school_name": "中原大學", "required_documents": dashboard["required_documents"], "source_urls": [DOCS, INTERNATIONAL, MAINLAND]}, False),
        ("scholarships.json", {"school_name": "中原大學", "scholarships": dashboard["scholarship_info"], "source_urls": [SCHOLARSHIP]}, False),
    ]:
        write_atomic(folder / filename, data, lines=lines)
    pages = [json.loads(x) for x in (folder / "pages.jsonl").read_text("utf8").splitlines()]
    values = [exchange["application_period"], exchange["eligibility"], exchange["language_requirement"], exchange["required_documents"], exchange["scholarship_info"]]
    for page, details in zip(pages, values, strict=True):
        page.update(text="\n".join(details), summary="\n".join(details), published_at=None, crawled_at=CHECKED_AT)
        page["content_hash"] = hashlib.sha256(page["text"].encode("utf8")).hexdigest()
    pages[1]["title"] = "中原大學：申請資格與GPA及排名規定差異"
    pages[2]["source_url"] = DOCS
    write_atomic(folder / "pages.jsonl", pages, lines=True)
    counts = json.loads((folder / "catalog-completeness.json").read_text("utf8"))
    counts.update(open_partners=0, reference_only_partners=20, needs_confirmation_partners=69,
                  reviewed_international_table_rows=20, reviewed_mainland_table_rows=22,
                  whole_partner_records_verified=0, active_term=INTL_PERIOD + MAINLAND_PERIOD,
                  verified_at=None, checked_at=CHECKED_AT)
    write_atomic(folder / "catalog-completeness.json", counts)
    write_atomic(folder / "verification_status.json", {
        "school_id": "cycu", "school_name": "中原大學", "status": "partial_review",
        "checked_at": CHECKED_AT, "counts": counts,
        "note": "僅核對指定母校公告及表格欄位，接待校、費用、住宿、圖片及其他內容尚未完成全部查證。",
    })
    provenance = json.loads((folder / "import_provenance.json").read_text("utf8"))
    if not any(s["file"] == SOURCE_FILE for s in provenance["sources"]):
        provenance["sources"].append({"file": SOURCE_FILE, "sha256": SOURCE_SHA256, "role": "reviewed_source_tables"})
    write_atomic(folder / "import_provenance.json", provenance)
    from .host_source_review_round25 import apply_host_source_review
    apply_host_source_review(root, "cycu")
