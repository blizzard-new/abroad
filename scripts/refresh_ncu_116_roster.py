"""Apply the NCU 116 first-round home nomination table to the bundled catalogue."""
from collections import defaultdict
from copy import deepcopy
import csv
import hashlib
import json
from pathlib import Path
import re
import unicodedata

ROOT = Path(__file__).resolve().parents[1]
SNAPSHOT = ROOT / "sources/ncu/2026-11-17"
LIST = "https://oia.ncu.edu.tw/static/file/26/1026/img/277/116exchangeschoollist-1117.pdf"
INDEX = "https://oia.ncu.edu.tw/p/412-1026-1872.php?Lang=zh-tw"
NOTICE = "https://oia.ncu.edu.tw/static/file/26/1026/img/277/116exchangenotice.pdf"
PORTAL = "https://beta.abroad.oia.ncu.edu.tw/"
CHECKED = "2026-11-19T00:00:00+08:00"
HOME = "國立中央大學"
DEADLINES = "中央校內線上申請為 2026/11/16 09:00 至 12/04 中午 12:00。學生須在 12/11 17:00 前將簽核紙本繳交系所，系所在 12/18 17:00 前彙送國際處（臺灣時間）。"
HOST = "中央提名後，接待校另行通知申請入口、文件、期限及審查結果。"
LABEL = "中央 116 學年度第一梯次姐妹校名單（2026/11/17）"
MISSING = "本項目未列入116-1最新出國交換姐妹校列表（2026/11/17）。可查看往年資料，當期請選名單上的校別與方案。"
OVERVIEW = "2026/11/17 公告的中央 116 學年度第一梯次名單（AY 2027–2028）共有 215 個具名列項。南洋理工大學分列兩種適用範圍，名額分別查閱。第 2 頁另有一列德國 NEW!，未印校名與名額。"
COUNTRIES = {"美國U.S.A.": "美國", "香港地區": "香港", "大陸地區": "中國", "Philippines": "菲律賓"}

# Reviewed cells that specify a faculty, programme, department or degree.
# A blank cell means the roster supplies no such condition. Keep whole notes
# because several rows distinguish advice, restrictions and faculty quotas.
FACULTY_NAMES = set("""克萊蒙高等商學院 巴黎市立工程師學校 國立高等應用電子學院 諾曼第高等管理學院 EDC巴黎商學院
IDRAC商業學院 航太工程高等學院 諾歐商學院 雷恩商學院 蒙佩利爾大學 索邦北巴黎大學 貝爾福-蒙貝利亞技術大學 魏瑪包豪斯大學
奧斯特法利爾應用科技大學 符茲堡大學 霍恩海姆大學 魯汶天主教大學 列日大學 芒斯大學 日內瓦大學 盧森應用科學與藝術大學 蘇黎世應用科學大學
摩納哥國際大學 布拉提斯拉瓦經濟大學 林雪坪大學 斯德哥爾摩經濟學院 漢斯應用科技大學 歐洲大學 加泰隆尼亞理工大學 科米利亞斯主教大學
安兹耶因大學 佛羅里達大學 威斯康辛大學麥迪遜分校 北海道大學(院級) 高知工科大學 靜岡大學 熊本大學 瑪希敦大學 南洋理工商管學院
香港城市大學 香港科技大學 上海交通大學 復旦大學 南京大學 沃瑪德瓦大學 迪波內戈羅大學""".split())
DEGREE_NAMES = set("""ECE巴黎工程學院 國立高等應用電子學院 國立土盧斯應用科學學院 博爾頓大學 霍恩海姆大學 蘇黎世應用科學大學
阿利坎特大學 安兹耶因大學 紐約州立大學奧斯威格分校 夏威夷大學馬諾阿分校 加州大學戴維斯分校（自費） 加州大學爾灣分校（自費）
廣島大學 千葉大學 筑波大學 釜山外國語大學 南洋理工商管學院 香港城市大學 香港浸會大學 香港科技大學 香港中文大學 香港教育大學 復旦大學 北京師範大學 浙江大學""".split())


def key(name):
    return re.sub(r"[^\w]", "", unicodedata.normalize("NFKC", name).casefold())


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def write(path, value):
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def read_lines(path):
    with path.open(encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def write_lines(path, rows, *, compact=False):
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            line = json.dumps(row, ensure_ascii=False, separators=(",", ":") if compact else None)
            for char in ("\u0085", "\u2028", "\u2029"):
                line = line.replace(char, f"\\u{ord(char):04x}")
            handle.write(line + "\n")


def page_link(row):
    return f"{LIST}#page={row['page']}"


def wording(row):
    return (f"第 {row['page']} 頁第 {row['table_row']} 列，名額：{row['quota']}。"
            f"語言：{row['language'] or '該列表欄位留白，請向合作校確認'}。"
            + (f"適用範圍／備註：{row['notes']}。" if row["notes"] else ""))


def add_roster(partners, rows):
    by_identity = {}
    for p in partners:
        name = p["school_name"]
        # Earlier catalogue duplicates the Chinese scope at the end of the English name.
        for tag in ("自費", "院級", "校級"):
            if name.endswith(f"（{tag}）") and tag in name.split(" ", 1)[0]:
                name = name.removesuffix(f"（{tag}）")
        identity = (p["country"], key(name))
        if identity in by_identity:
            raise ValueError(f"Ambiguous NCU catalogue identity: {identity}")
        by_identity[identity] = p
    by_school = defaultdict(list)
    for row in rows:
        country = COUNTRIES.get(row["country"], row["country"])
        name = " ".join(filter(None, [row["name_zh"], row["name_en"]]))
        identity = (country, key(name))
        if identity not in by_identity:
            partner = dict(school_name=name, country=country, program_type="交換學生",
                           student_summary_zh={"application_steps": [DEADLINES, HOST]})
            partners.append(partner)
            by_identity[identity] = partner
        by_school[by_identity[identity]["school_name"]].append(row)
    return by_school


def update_partner(p, rows):
    url = page_link(rows[0]) if rows else LIST
    detail = [wording(row) for row in rows]
    fee = any("自費" in (r["name_zh"] + r["notes"]).replace("\n", "") for r in rows)
    note = (f"{LABEL}，" + " ".join(detail) + " " + HOST) if rows else MISSING
    summary = p.setdefault("student_summary_zh", {})
    old = summary.get("eligibility_points", [])
    rest = [x for x in old if not x.startswith(("【116-1最新姐妹校列表", LABEL, MISSING))]
    if p["school_name"].startswith("北方高等商業學院"):
        history = "歷史變更：EDHEC 已於2026/10/22版姐妹校列表中移除（https://oia.ncu.edu.tw/static/file/26/1026/img/277/116exchangeschoollist-1022.pdf）。"
        if history not in rest:
            rest.insert(0, history)
    summary["eligibility_points"] = [note, *rest]
    p.update(availability_note=note, eligibility="\n".join(summary["eligibility_points"]),
             availability_status="fee_paying" if fee else "open" if rows else "not_open",
             quota_status="fee_paying" if fee else "published" if rows else "reference_only",
             academic_year="116", application_round="第一梯次", source_url=url,
             source_pages=list(dict.fromkeys(r["page"] for r in rows)), checked_at=CHECKED)
    p.setdefault("application_info", "\n\n".join(summary.get("application_steps", [DEADLINES, HOST])))
    p.setdefault("application_deadline", DEADLINES)
    if rows:
        p["quota"] = rows[0]["quota"] if len(rows) == 1 else "、".join(
            f"第{r['table_row']}列 {r['quota']} 名" for r in rows) + "（兩列分列，不合計）"
        language = list(dict.fromkeys(r["language"] for r in rows if r["language"]))
        if language:
            p["language_requirement"] = "\n".join(language)
        if fee:
            cost = "中央 116-1 名單註明此方案為自費。依該列備註與接待校當期收費規定準備學雜費。"
            tuition = [x for x in summary.get("tuition_points", []) if x != cost]
            summary["tuition_points"] = [cost, *tuition]
            p["tuition_info"] = "\n\n".join(summary["tuition_points"])
    evidence = dict(source_url=url, source_pages=p["source_pages"], academic_year="116",
                    application_round="第一梯次", checked_at=CHECKED, status="verified_current")
    p.setdefault("field_evidence", {})["quota"] = dict(evidence, excerpt=p.get("quota") or MISSING, note=note)
    if rows and p.get("language_requirement"):
        p["field_evidence"]["language_requirement"] = dict(evidence, excerpt=p["language_requirement"],
                                                note="中央名單所列，分項及適用學制以該列原文為準。")
    for field, names in (("colleges", FACULTY_NAMES), ("degree_levels", DEGREE_NAMES)):
        applicable = [r for r in rows if r["name_zh"] in names or (field == "colleges" and
                      (r["name_en"] == "Romanian-American University" or (r["name_zh"] == "南洋理工大學" and "電機系" in r["notes"])))]
        if applicable:
            p[field] = "\n".join((f"第 {r['page']} 頁第 {r['table_row']} 列：" if len(rows) > 1 else "")
                                 + r["notes"] for r in applicable)
            p["field_evidence"][field] = dict(evidence, excerpt=p[field], note="中央名單備註原文，含適合對象、限制及方案例外，請逐項核對。")
    # Earlier multi-row controls describe 115; show the current options in their place.
    if p.get("program_options") or len(rows) > 1:
        p["program_options"] = [dict(program_type=f"116-1 交換（第 {r['page']} 頁第 {r['table_row']} 列）",
                                     quota=r["quota"], eligibility=r["language"], colleges=r["notes"],
                                     source_url=page_link(r)) for r in rows]


# These are editorial notes attached to earlier host-source reviews. Keep the
# original source passages intact, and date the previous verification finding.
OLDER_REVIEW = re.compile(r"(校別／名額／track|校別、名額、方案[及與]實際校區|校別、名額與個人適用|名額、梯次與個人適用性|校別、名額與track|校別、名額與本人可提名方案|名額與指定梯次|校別／名額與接收梯次)(仍未|尚未|仍待|未核)")


def date_older_review(value):
    if isinstance(value, str):
        return OLDER_REVIEW.sub(lambda match: match[1] + "於查核該附件時" + match[2], value)
    if isinstance(value, list):
        return [date_older_review(item) for item in value]
    if isinstance(value, dict):
        return {k: date_older_review(v) for k, v in value.items()}
    return value


def add_reviewed_campus_cities(guides):
    with (SNAPSHOT / "reviewed-campus-cities.csv").open(encoding="utf-8", newline="") as handle:
        reviewed = {row["school_name"]: row for row in csv.DictReader(handle) if row["result"] == "named_location"}
    for guide in guides:
        row = reviewed.get(guide["school_name"])
        if not row:
            continue
        city = row["city_label"] + "（就讀校區依錄取通知）"
        if guide.get("city") and guide["city"] != city:
            continue
        guide["city"] = city
        sources = guide.setdefault("sources", [])
        for url in filter(None, (row["source_url"], row["other_source"])):
            if all(source["source_url"] != url for source in sources):
                sources.append(dict(title="校區位置查核：" + row["city_label"], source_url=url,
                                    summary=row["scope"]))


def apply_roster(output):
    rows = load(SNAPSHOT / "quota-116-1-rows.json")
    partners = read_lines(output / "partners.jsonl")
    by_school = add_roster(partners, rows)
    living = load(SNAPSHOT / "incoming-resources.json")
    for p in partners:
        update_partner(p, by_school.get(p["school_name"], []))
        if p["school_name"] in living:
            p["website"] = living[p["school_name"]]["url"]
    write_lines(output / "partners.jsonl", map(date_older_review, partners), compact=True)
    flows = read_lines(output / "application_workflows.jsonl")
    by_name = {w["school_name"]: w for w in flows}
    common = [s for s in flows[0]["steps"] if s["rule_id"].startswith("ncu-116-1-home-")]
    common_sources = [s for s in flows[0]["sources"] if s["source_url"] in (NOTICE, INDEX)]
    guides = read_lines(output / "destination_profiles.jsonl")
    guides = [g for g in guides if g["school_name"] not in living]
    for p in partners:
        name = p["school_name"]
        rows_for_school = by_school.get(name, [])
        url = p["source_url"]
        if name not in by_name:
            flow = dict(home_university=HOME, school_name=name, country=p["country"], program_type="交換學生",
                        academic_year="116", application_round="第一梯次", effective_application_rounds=["第一梯次"],
                        review_status="pending_review", coverage_status="official_partial", sources=deepcopy(common_sources),
                        steps=deepcopy(common))
            host_ref = "ncu-116-1-" + hashlib.sha256(name.encode()).hexdigest()[:10]
            flow["steps"].insert(4, dict(rule_id=host_ref + "-host", order=5, phase="合作校申請",
                                         title="收到中央提名通知後核對接待校送件要求", summary=HOST,
                                         responsible_party="學生與兩校國際處", source_urls=[url, NOTICE],
                                         scope={"partner_universities": [name], "home_universities": [HOME], "academic_years": ["116"]},
                                         support_status="needs_confirmation", needs_confirmation=True, checked_at=CHECKED))
            flows.append(flow)
            by_name[name] = flow
        flow = by_name[name]
        flow.update(applicability_note=p["availability_note"], last_checked=CHECKED)
        source = dict(title=LABEL, source_url=url, role="home_university", authority="home_official_notice",
                      effective_academic_year="116", application_round="第一梯次", checked_at=CHECKED)
        flow["sources"] = [source, *[s for s in flow["sources"] if s["source_url"] != url]]
        for step in flow["steps"]:
            if step["rule_id"] == "ncu-116-1-home-1":
                step["details"] = [x for x in step["details"] if not x.startswith(("116名額預定", LABEL, MISSING))]
                step["details"].append(p["availability_note"])
                step.update(action_url=url, checked_at=CHECKED, source_urls=[NOTICE, url])
            elif step["rule_id"] == "ncu-116-1-home-2":
                step.update(action_url=PORTAL, source_urls=[NOTICE, INDEX], checked_at=CHECKED)
                step["submission"]["portal_url"] = PORTAL
        if name in living:
            g = living[name]
            guides.append(dict(home_university=HOME, school_name=name, country=p["country"], last_checked=CHECKED,
                               coverage_status="official_partial", coverage_note=g["scope"],
                               student_guide_sections=[dict(key="arrival", title=g["title"], summary=g["detail"],
                                                            source_urls=[g["url"]], caution=g["scope"])],
                               sources=[dict(title=g["title"], source_url=g["url"]), dict(title=LABEL, source_url=url),
                                        *g.get("other_sources", [])],
                               **{k: g[k] for k in ("city", "cost_summary", "housing_summary", "transport_summary",
                                                    "campus_life_summary") if k in g}))

    write_lines(output / "application_workflows.jsonl", map(date_older_review, flows))
    add_reviewed_campus_cities(guides)
    write_lines(output / "destination_profiles.jsonl", map(date_older_review, guides))

    ex = load(output / "exchange_info.json")
    ex.update(application_period=[DEADLINES, OVERVIEW, f"校內線上申請入口：{PORTAL}"], last_checked=CHECKED,
              partner_universities=[p["school_name"] for p in partners])
    ex["source_urls"] = list(dict.fromkeys([INDEX, NOTICE, LIST, PORTAL, *ex["source_urls"]]))
    write(output / "exchange_info.json", ex)
    dash = load(output / "student_dashboard.json")
    dash["last_checked"] = CHECKED
    dash["selection_rules"]["pending_quota_planning"] = False
    period = dash["application_periods"][0]
    period.update(details=[DEADLINES, f"由中央國際處交換生計畫頁進入出國申請系統：{PORTAL}"], checked_at=CHECKED,
                  status="open")
    overview = dash["program_overview"][0]
    overview.update(details=[OVERVIEW, HOST, *[s for s in overview["details"] if s.startswith("2027/9")]],
                    source=dict(title=LABEL, source_url=LIST))
    dash["sources"] = [dict(title=LABEL, source_url=LIST), *[s for s in dash["sources"] if s["source_url"] != LIST]]
    write(output / "student_dashboard.json", dash)
    pages = read_lines(output / "pages.jsonl")
    roster_text = OVERVIEW + "\n" + DEADLINES + "\n" + "\n".join(
        f"{r['name_zh']} {r['name_en']} — {wording(r)}" for r in rows)
    page = dict(title=LABEL, source_url=LIST, published_at="2026-11-17T00:00:00+08:00",
                category="partner_school", text=roster_text, summary=OVERVIEW, crawled_at=CHECKED,
                content_hash=hashlib.sha256(roster_text.encode()).hexdigest())
    write_lines(output / "pages.jsonl", [page, *[p for p in pages if p["source_url"] != LIST]])
    comp = load(output / "catalog-completeness.json")
    comp.update(checked_at=CHECKED, current_list_status="published_2026_11_17", current_list_published_date="2026-11-17",
                current_list_url=LIST, current_list_sha256=hashlib.sha256((SNAPSHOT / LIST.split("/")[-1]).read_bytes()).hexdigest(),
                current_list_rows=len(rows), current_list_distinct_entries=len(by_school), unnamed_rows=1,
                catalog_entries=len(partners), pending_workflows=len(flows), previous_116_list_rows=214,
                previous_116_list_url=LIST.replace("1117", "1022"),
                previous_116_list_sha256="cb248b65a4a6533732d2afa26d83cd968df70528091646e4461869090e5299db",
                current_list_added_schools=[name for name in living if name.startswith("魁北克大學三河分校")],
                current_list_removed_schools=[], catalog_added_schools=list(living),
                catalog_reference_only_schools=[p["school_name"] for p in partners if p["school_name"] not in by_school])
    write(output / "catalog-completeness.json", comp)
    provenance = load(output / "import-provenance.json")
    provenance["roster_116_1_20261117"] = {
        "official_url": LIST,
        "checked_at": CHECKED,
        "input_sha256": {f.name: hashlib.sha256(f.read_bytes()).hexdigest()
                         for f in sorted(SNAPSHOT.iterdir()) if f.suffix in {".json", ".pdf", ".csv"}},
    }
    write(output / "import-provenance.json", provenance)

    # Field audits also feed the student-facing completeness panel. Preserve the
    # original 115/October passages as historical corroboration after the new quote.
    audits = load(output / "field-audit.json")
    by_partner = {p["school_name"]: p for p in partners}
    for audit in audits:
        p = by_partner[audit["school_name"]]
        f = audit["fields"]["quota"]
        evidence = dict(text=p["availability_note"], page=p["source_pages"][0] if p["source_pages"] else None,
                        source_url=p["source_url"], source_title=LABEL, applicability="中央 116 第一梯次校內名單",
                        checked_at=CHECKED)
        f.update(status="available", unresolved=None, current_applicability_status="verified", note=p["availability_note"], source_urls=[p["source_url"]],
                 original_evidence=[evidence, *[o for o in f["original_evidence"] if o.get("source_title") != LABEL]])
    write(output / "field-audit.json", audits)

    coverage_path = output / "field-coverage.csv"
    with coverage_path.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        headings = reader.fieldnames
        coverage = list(reader)
    by_audit = {a["school_name"]: a for a in audits}
    for record in coverage:
        fields = by_audit[record["學校／track"]]["fields"]
        record["116年度名額"] = fields["quota"]["status"]
        record["未解問題"] = "；".join(f"{f['label']}：{f['unresolved']}" for f in fields.values() if f.get("unresolved"))
    with coverage_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=headings, lineterminator="\n")
        writer.writeheader()
        writer.writerows(coverage)
