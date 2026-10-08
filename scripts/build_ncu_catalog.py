"""Build a conservative NCU catalogue from preserved official sources.

The 115 rows and undated introductions remain reference material. No numerical
host eligibility, current quota or host deadline is inferred from text.
"""

from __future__ import annotations
import argparse, gzip, hashlib, json, re, sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from exchange_info.models import (
    PartnerUniversity,
    PartnerStudentSummary,
    PartnerProgramOption,
    StudentDashboard,
    ExchangeInfo,
    ProcessedPage,
    UniversityApplicationWorkflow,
    DestinationProfile,
    PartnerResearchRecord,
)
from exchange_info.ncu_eligibility import SCORE_MINIMUMS, EXCLUDED_YEARS
from exchange_info.ncu_student_view import (
    NCU_GUIDELINES_URL as NOTICE,
    NCU_INDEX_URL as INDEX,
    NCU_LIST_115_URL as LIST,
    NCU_FORMS_URL as FORMS,
)

ROOT = Path(__file__).resolve().parents[1]
SOURCES = ROOT / "sources/ncu/2026-10-08"
CHECKED = "2026-10-08T00:00:00+00:00"
HOME = "國立中央大學"
ROUND = "第一梯次"
FIELDS = {
    "quota": "116年度名額",
    "eligibility": "學制／校區／track範圍",
    "language": "強制與建議語言",
    "home_documents": "校內甄選文件",
    "host_documents": "外校申請文件／最新表格",
    "home_deadline": "校內線上與紙本期限",
    "host_deadline": "提名與外校申請期限",
    "study_period": "交換期間／校曆",
    "courses": "課程限制與選課",
    "tuition": "兩校學費／其他校方收費",
    "cost": "生活費",
    "housing": "住宿與申請期限",
    "insurance": "保險",
    "visa": "簽證／居留",
    "arrival": "到校與行前準備",
}
HOME_DOCS = [
    {
        "name": "系統申請表（列印完成簽核）",
        "signatures": ["依表格完成簽核"],
        "source_urls": [NOTICE],
    },
    {
        "name": "家長同意書",
        "signatures": ["家長本人親筆簽名", "學生簽名（現行表格第2頁）"],
        "official_form_url": FORMS + "#page=2",
        "source_urls": [NOTICE, FORMS],
    },
    {
        "name": "學生個人資料提供同意書",
        "signatures": ["申請人簽名並勾選同意"],
        "official_form_url": FORMS + "#page=1",
        "source_urls": [NOTICE, FORMS],
    },
    {
        "name": "校內必繳正式語言檢定成績單影本（不接受網路截圖或補繳）",
        "copy_type": "copy",
        "source_urls": [NOTICE],
    },
    {"name": "中文版歷年成績單（碩一另附大學歷年成績）", "source_urls": [NOTICE]},
    {"name": "中文版成績名次證明書", "source_urls": [NOTICE]},
    {
        "name": "國際移動力完成證明書",
        "stamps": ["右下方國際處章戳"],
        "source_urls": [NOTICE],
    },
]
HOME_POINTS = [
    "校內線上申請2026/11/16 09:00至12/4 12:00（臺灣時間）。紙本資料另須12/11 17:00前交系所；系所12/18 17:00前送國際處，不能把系所送件日當學生截止日。",
    "校內初審只取得推薦資格；須由外校另行審查並核發入學許可，且取得簽證。",
    "校內必繳正式外語檢定，不限級數；英檢須兩年內有效，線上關閉前須備妥並上傳，不接受網路截圖或補繳。外校要求之語檢分開查核。",
    "校內必繳：簽核申請表、家長同意書、個資同意書、正式語檢影本、中文歷年成績、中文名次證明、加蓋國際處章戳之國際移動力證明。",
    "簡章第4頁允許外校語檢至外校截止前補繳，第7頁規定提名前取得；請依較早的提名時點準備並向國際處確認。",
]
HEADINGS = [
    "地點",
    "申請資格",
    "開放申請科系",
    "語言限制",
    "語言要求",
    "課程介紹",
    "課程資訊",
    "交換期間",
    "申請截止日期",
    "申請截止日",
    "申請文件",
    "所需文件",
    "申請方式",
    "住宿",
    "生活費",
    "學費",
    "保險",
    "簽證",
    "學校網址",
    "網站",
]


def load_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path, value):
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


def write_rows(path, values, model):
    path.write_text(
        "".join(
            model.model_validate(v).model_dump_json(exclude_defaults=True) + "\n"
            for v in values
        ),
        encoding="utf-8",
    )


def source(title, url=NOTICE, summary=None):
    return dict(title=title, source_url=url, summary=summary)


def intro_sections(text):
    # Only copies source sections; these strings never produce admission predicates.
    pattern = re.compile(
        r"(?m)(?:^|\n)[ \t]*("
        + "|".join(map(re.escape, HEADINGS))
        + r")[ \t]*(?:\n|[:：]|[ \t])"
    )
    matches = list(pattern.finditer(text))
    return {
        m.group(1): text[
            m.end() : matches[i + 1].start() if i + 1 < len(matches) else len(text)
        ].strip()
        for i, m in enumerate(matches)
    }


def make_home_step(order, title, summary, **kw):
    return dict(
        order=order,
        rule_id=f"ncu-116-1-home-{order}",
        phase=kw.pop("phase", "校內申請"),
        title=title,
        responsible_party="學生",
        responsible_unit="中央國際事務處／所屬系所",
        summary=summary,
        source_urls=[NOTICE],
        checked_at=CHECKED,
        support_status="verified",
        scope={
            "home_universities": [HOME],
            "academic_years": ["116"],
            "application_rounds": [ROUND],
        },
        **kw,
    )


def build(output):
    output.mkdir(parents=True, exist_ok=True)
    rows = load_json(SOURCES / "quota-115-rows.json")
    mapping = {
        x["row_id"]: x for x in load_json(SOURCES / "source-map-candidates.json")
    }
    evidence = json.loads(
        gzip.decompress((SOURCES / "drive-evidence.json.gz").read_bytes())
    )
    web_evidence = json.loads(
        gzip.decompress((SOURCES / "host-web-evidence.json.gz").read_bytes())
    )
    docs = {x["id"]: x for x in evidence + web_evidence}
    reviewed = load_json(SOURCES / "reviewed-host-records.json")
    from pypdf import PdfReader

    home_pages = {
        filename: [
            page.extract_text() for page in PdfReader(SOURCES / f"{filename}.pdf").pages
        ]
        for filename in ("notice", "forms")
    }

    def home_evidence(filename, page, url):
        return {
            "text": home_pages[filename][page - 1],
            "page": page,
            "source_url": url,
            "source_title": "中央116-1簡章"
            if filename == "notice"
            else "首頁現行同意書（檔名2022）",
            "applicability": "116母校公告／首頁現行表格，非外校文件包",
            "checked_at": CHECKED,
        }

    groups = defaultdict(list)
    for r in rows:
        groups[(r["name_zh"], r["name_en"])].append(r)
    partners = []
    workflows = []
    destinations = []
    audit = []
    pages = []
    research = []
    for (zh, en), rs in groups.items():
        track = (
            "（院級）"
            if zh.endswith("(院級)")
            else "（校級）"
            if zh.endswith("(校級)")
            else "（自費）"
            if zh.endswith("（自費）")
            else ""
        )
        name = f"{zh} {en}{track}"
        country = {
            "美國U.S.A.": "美國",
            "香港地區": "香港",
            "大陸地區": "中國",
            "Philippines": "菲律賓",
        }.get(rs[0]["country"], rs[0]["country"])
        rowids = [r["id"] for r in rs]
        review = next((reviewed[r["id"]] for r in rs if r["id"] in reviewed), None)
        research.append(
            dict(
                home_university=HOME,
                school_name=name,
                country=country,
                verification_status="needs_review",
                checked_at=CHECKED,
                discovery_source_url=LIST + f"#page={rs[0]['page']}",
                note="115歷史表／公開附件的身份、年度、校區與track待逐項核對；不以網址存在宣稱官方已核准。",
            )
        )
        related = list(
            dict.fromkeys(
                [
                    *(fid for r in rs for fid in mapping[r["id"]]["files"]),
                    *(review["source_ids"] if review else []),
                    *(
                        x["id"]
                        for x in web_evidence
                        if set(x["row_ids"]).intersection(rowids)
                    ),
                ]
            )
        )
        selected = [
            docs[fid] for fid in related if fid in docs and docs[fid].get("pages")
        ]
        # The NCU-produced introduction has these literal labels. Selection is by
        # file content, not an inference of publication year or current applicability.
        introductions = [
            d
            for d in selected
            if any(
                "地點" in p["text"]
                and (
                    "學校網址" in p["text"]
                    or "語言要求" in p["text"]
                    or "語言限制" in p["text"]
                )
                for p in d["pages"]
            )
        ]
        fields = defaultdict(list)
        for d in introductions:
            for p in d["pages"]:
                for key, text in intro_sections(p["text"]).items():
                    fields[key].append(
                        {
                            "text": text,
                            "source_url": d["url"],
                            "page": p["page"],
                            "source_title": d["label"],
                            "applicability": "source_version_unconfirmed",
                            "checked_at": CHECKED,
                        }
                    )

        def excerpts(keys):
            return [
                f"【中央公開介紹參考；年份／116適用性未確認】{key}：{x['text']}（{x['source_title']}，第{x['page']}頁；{x['source_url']}）"
                for key in keys
                for x in fields[key]
                if x["text"]
            ]

        language = [
            f"【115年度第{r['page']}頁，非116門檻】{r['language_115'] or '本列無語言文字，不代表免語檢'}"
            for r in rs
        ]
        notes = [
            f"【115年度第{r['page']}頁，列{r['id']}】{r['notes_115'] or '本列沒有範圍備註，學制／科系與校區仍須查核'}"
            for r in rs
        ]
        previous = [
            f"115年度列{r['id']}名額原文：{r['quota_115']}（PDF第{r['page']}頁）。這是歷史額度，未填入116名額。"
            for r in rs
        ]
        paid = rs[0]["id"] in ["ncu-039", *[f"ncu-{i:03}" for i in range(108, 115)]]
        fee = (
            ["115表註明此方案全額自費，須繳中央及外校學雜費；116費用另核對。"]
            if paid
            else [
                "中央交換期間仍須註冊及繳本校學雜費；外校是否免學費與其他校方收費須逐方案核對，不保證一律免繳。"
            ]
        )
        website = None
        for item in fields["學校網址"] + fields["網站"]:
            urls = re.findall(r"https?://[^\s<>]+", item["text"])
            if urls:
                website = urls[0].rstrip(".,;)")
                break
        research[-1]["official_website"] = website
        period = "116母校方案：2027/9–2028/2一學期、2027/9–2028/6一學年、2028/2–6一學期；實際依外校校曆與可提名學期確認。"
        deadline = "中央線上2026/12/4 12:00、系所紙本12/11 17:00（臺灣時間）；外校116當期提名／申請期限尚未取得核對。"
        host_docs = excerpts(["申請文件", "所需文件", "申請方式"])
        summary = dict(
            study_period=period,
            application_deadline=deadline,
            eligibility_points=[
                "116-1名額預定2026/10/12公告，目前只有115名單；不能據此判定當期開放。",
                *previous,
                *language,
                *notes,
                *excerpts(["申請資格", "開放申請科系", "語言限制", "語言要求"]),
            ],
            application_steps=[
                *HOME_POINTS,
                *(
                    host_docs
                    or [
                        "外校文件／表格尚未取得並完成116適用性核對；中央通用提名流程不是外校文件清單。"
                    ]
                ),
                *excerpts(["申請截止日期", "申請截止日"]),
            ],
            tuition_points=[
                *fee,
                *excerpts(["學費", "生活費", "住宿", "保險", "簽證"]),
            ],
            translated_from_english=False,
        )
        partner = dict(
            program_type="自費訪問（歷史方案）" if paid else "交換學生",
            availability_status="agreement_only",
            availability_note="116學年度第一梯次名額與校別名單預定2026/10/12公告（簡章第2、6頁）；目前僅有115表列參考。外校當期名額、track及全部申請條件仍須核對。",
            country=country,
            school_name=name,
            website=website,
            colleges=None,
            degree_levels=None,
            quota=None,
            study_period=period,
            eligibility="\n".join(
                language
                + notes
                + excerpts(["申請資格", "開放申請科系", "語言限制", "語言要求"])
            ),
            application_deadline=deadline,
            application_info="\n\n".join(summary["application_steps"]),
            tuition_info="\n\n".join(summary["tuition_points"]),
            source_url=LIST + f"#page={rs[0]['page']}",
            student_summary_zh=summary,
        )
        if len(rs) > 1:
            partner["program_options"] = [
                dict(
                    program_type=f"115參考列{r['id']}（範圍不同，名額不相加）",
                    quota=None,
                    colleges=r["notes_115"],
                    eligibility=r["language_115"],
                    source_url=LIST + f"#page={r['page']}",
                    student_summary_zh={
                        "eligibility_points": [
                            f"115年度額度原文{r['quota_115']}；116名額未知。",
                            r["notes_115"],
                            r["language_115"],
                        ]
                    },
                )
                for r in rs
            ]

        def reviewed_points(key):
            return (
                [
                    f"【{review['applicability']}】{text}"
                    for text in review["fields"].get(key, {}).get("points", [])
                ]
                if review
                else []
            )

        if review:
            summary["eligibility_points"] = [
                summary["eligibility_points"][0],
                *reviewed_points("language"),
                *reviewed_points("eligibility"),
                *reviewed_points("courses"),
                *summary["eligibility_points"][1:],
            ]
            summary["application_steps"].extend(
                reviewed_points("host_documents")
                + reviewed_points("host_deadline")
                + reviewed_points("arrival")
            )
            summary["tuition_points"].extend(
                sum(
                    (
                        reviewed_points(k)
                        for k in ["tuition", "cost", "housing", "insurance", "visa"]
                    ),
                    [],
                )
            )
            summary["study_period"] = (
                period + " " + " ".join(reviewed_points("study_period"))
            )
            summary["application_deadline"] = (
                deadline + " " + " ".join(reviewed_points("host_deadline"))
            )
            partner.update(
                student_summary_zh=summary,
                study_period=summary["study_period"],
                application_deadline=summary["application_deadline"],
                eligibility="\n".join(summary["eligibility_points"]),
                application_info="\n\n".join(summary["application_steps"]),
                tuition_info="\n\n".join(summary["tuition_points"]),
            )
        partners.append(partner)
        home_steps = [
            make_home_step(
                1,
                "核對中央116-1資格與當期名額",
                "大學部平均60、研究生70；至少一學年在學成績，碩一可附大學成績；在職專班可申請但無研修獎學金。",
                details=[
                    "目前大五／大六不具資格；須導師或指導教授與系所同意。",
                    "陸生不得申請大陸、僑生不得申請原僑居地；雙重國籍勿選擇所持國籍國家。",
                    "前一年錄取後自願放棄者原則上不得申請；交換期间須保有學籍並以甄選身分出國。",
                    "116名額預定2026/10/12公告；115名單僅參考。",
                ],
            ),
            make_home_step(
                2,
                "完成中央線上申請並列印簽核",
                "2026/11/16 09:00開放；2026/12/4 12:00關閉（臺灣時間）。正式必繳語檢须先備妥上傳。",
                deadline_at="2026-12-04T12:00:00+08:00",
                deadline_status="verified_exact",
                deadline_source_url=NOTICE,
                deadline_checked_at=CHECKED,
                deadline_reminder_eligible=False,
                action_url="https://abroad.oia.ncu.edu.tw/student/",
                submission={
                    "method": "online",
                    "portal_url": "https://abroad.oia.ncu.edu.tw/student/",
                },
            ),
            make_home_step(
                3,
                "繳交中央校內紙本甄選文件至系所",
                "學生2026/12/11 17:00前繳至系所；系所彙整12/18 17:00前送國際處。",
                deadline_at="2026-12-11T17:00:00+08:00",
                deadline_status="verified_exact",
                deadline_source_url=NOTICE,
                deadline_checked_at=CHECKED,
                deadline_reminder_eligible=False,
                document_requirements=HOME_DOCS,
                official_form_urls=[FORMS + "#page=1", FORMS + "#page=2"],
                submission={
                    "method": "paper",
                    "office": "所屬系所",
                    "arrival_deadline_at": "2026-12-11T17:00:00+08:00",
                },
                details=[
                    "其他能力證明／作品及外校語檢為選繳；外校語檢仍須提名前取得。正式份數簡章未列，須核對系所通知。"
                ],
            ),
            make_home_step(
                4,
                "核對校內錄取並準備提名",
                "2027/1/11 09:00公告校內錄取；國際處再通知外校申請方式。校內錄取不代表外校錄取。",
                phase="甄選與提名",
                details=[HOME_POINTS[-1]],
            ),
        ]
        host_step = dict(
            order=5,
            rule_id=f"{rowids[0]}-host-apply",
            phase="合作校申請",
            title="核對外校當期文件並依通知申請",
            responsible_party="學生與兩校國際處",
            summary="外校當期文件、提名／申請期限與portal须逐校核對；下列公開介紹只供參考。",
            details=host_docs or ["尚未取得並核對外校完整文件清單。"],
            document_requirements=[],
            source_urls=[d["url"] for d in introductions],
            checked_at=CHECKED,
            support_status="needs_confirmation",
            needs_confirmation=True,
            scope={
                "home_universities": [HOME],
                "partner_universities": [name],
                "academic_years": ["116"],
            },
        )
        if review:
            host_step.update(
                summary=review["applicability"],
                details=reviewed_points("host_documents")
                + reviewed_points("host_deadline")
                + reviewed_points("language"),
                document_requirements=review["host_documents"],
                source_urls=[docs[fid]["url"] for fid in review["source_ids"]],
            )
            host_step["official_form_urls"] = [
                d["official_form_url"]
                for d in review["host_documents"]
                if d.get("official_form_url")
            ]
        tail = [
            make_home_step(
                6,
                "確認課程、學分與中央註冊繳費",
                "依外校修課規定；無規定時至少兩門課且一門專業課。學則另要求兩門或六學分，採認由系所審定。",
                phase="行前準備",
                details=[
                    "中央仍須保有學籍、完成註冊及繳學雜費；延畢生另按轉換學分及兩階段程序處理。"
                ],
            ),
            make_home_step(
                7,
                "出國前兩週完成中央行前程序",
                "完成中央交換及雙聯行前程序單，自行辦理護照、簽證、足額醫療／意外／急難救助保險及役男出國許可。",
                phase="行前準備",
                timing="出國前兩週",
                document_requirements=[
                    {
                        "name": "中央交換及雙聯計畫學生行前程序單（最新表格須向國際處取得）",
                        "source_urls": [NOTICE],
                        "needs_confirmation": True,
                    }
                ],
                details=[
                    "須依外校建議抵達日到校；本校宿舍先辦保留或退宿。",
                    "外校住宿申請、住宿保證及截止另核對，不推定有保證宿舍。",
                ],
            ),
            make_home_step(
                8,
                "到校註冊並回報當地聯絡方式",
                "依外校完成報到、選課；中央國際處調查國外地址及聯絡方式，保持聯繫。",
                phase="抵達後",
            ),
            make_home_step(
                9,
                "返國後一週完成中央返校程序",
                "填中央返校程序單並繳心得WORD電子檔（800–1500字、至少四張照片）；取得外校成績並在畢業前完成採認。",
                phase="返國後",
                timing="返國後一週內",
                document_requirements=[
                    {
                        "name": "中央交換及雙聯計畫學生返校程序單（最新表格須向國際處取得）",
                        "source_urls": [NOTICE],
                        "needs_confirmation": True,
                    },
                    {
                        "name": "心得WORD電子檔（800–1500字、至少四張照片）",
                        "source_urls": [NOTICE],
                    },
                ],
            ),
        ]
        workflows.append(
            dict(
                home_university=HOME,
                school_name=name,
                country=country,
                program_type=partner["program_type"],
                academic_year="116",
                application_round=ROUND,
                effective_application_rounds=[ROUND],
                applicability_status="needs_confirmation",
                applicability_note="中央母校116-1已公告；外校當期名額、track與文件未完整查核，流程仅供準備參考。",
                review_status="pending_review",
                published_at=None,
                steps=[*home_steps, host_step, *tail],
                sources=[
                    {
                        "title": "中央116-1甄選簡章",
                        "source_url": NOTICE,
                        "role": "home_university",
                        "authority": "home_official_notice",
                        "effective_academic_year": "116",
                        "application_round": ROUND,
                        "checked_at": CHECKED,
                    },
                    {
                        "title": "中央115名額表（歷史參考）",
                        "source_url": LIST,
                        "role": "home_university",
                        "authority": "home_official_notice",
                        "effective_academic_year": "115",
                        "checked_at": CHECKED,
                    },
                ],
                last_checked=CHECKED,
                coverage_status="official_partial",
                coverage_note=f"已核對母校116-1；相關公開附件{len(related)}份，個別外校原文與當期適用性另核對。",
            )
        )
        destination_sections = []
        for key, title, labels in [
            ("cost", "費用參考", ["學費", "生活費"]),
            ("housing", "住宿參考", ["住宿"]),
            ("insurance", "保險", ["保險"]),
            ("visa", "簽證與居留", ["簽證"]),
            ("courses", "課程與交換期間", ["課程介紹", "課程資訊", "交換期間"]),
        ]:
            points = excerpts(labels)
            destination_sections.append(
                dict(
                    key=key,
                    title=title,
                    summary="中央公開介紹之歷史或未標年參考；116適用性、金額與全部期限尚待核對。"
                    if points
                    else "尚未取得並核對此校的完整官方內容；不表示官方未公告。",
                    points=points,
                    source_urls=list(
                        dict.fromkeys(
                            x["source_url"] for label in labels for x in fields[label]
                        )
                    ),
                    caution="不要用舊金額／未標年文件作為2027–2028保證；請看原始來源的方案、校區與日期。",
                )
            )
        if review:
            for key in ["cost", "housing", "insurance", "visa", "courses", "arrival"]:
                keys = (
                    ["tuition", "cost"]
                    if key == "cost"
                    else ["courses", "study_period"]
                    if key == "courses"
                    else [key]
                )
                pts = sum((reviewed_points(k) for k in keys), [])
                if pts:
                    section = next(
                        (x for x in destination_sections if x["key"] == key), None
                    )
                    value = dict(
                        key=key,
                        title=FIELDS.get(key, key),
                        summary=review["applicability"],
                        points=pts,
                        source_urls=[docs[fid]["url"] for fid in review["source_ids"]],
                        caution="中央當期提名及各項未解問題仍須確認；新版文件內的舊金額及版本矛盾已分列。",
                    )
                    if section:
                        section.update(value)
                    else:
                        destination_sections.append(value)
        destinations.append(
            dict(
                home_university=HOME,
                school_name=name,
                country=country,
                cost_summary="\n".join(excerpts(["學費", "生活費"]))
                or "尚未取得並核對外校生活費與收費。",
                housing_summary="\n".join(excerpts(["住宿"]))
                or "尚未取得並核對住宿與申請期限。",
                campus_life_summary="\n".join(
                    excerpts(["課程介紹", "課程資訊", "交換期間"])
                )
                or "尚未取得並核對校園與到校資訊。",
                student_guide_sections=destination_sections,
                first_72_hours=[
                    {
                        "title": "依外校建議抵達日期與報到程序",
                        "detail": "中央簡章第8頁規定依外校開學建議抵達日期前往；本校錄取不代表外校已核發入學許可。外校orientation／宿舍入住日期另核對。",
                        "source_urls": [NOTICE],
                    },
                    {
                        "title": "備妥足額保險並回報當地聯絡方式",
                        "detail": "中央簡章第7頁須足額醫療、意外、海外急難救助保險；外校另有保險時可依規定到當地購買。國際處調查當地地址及聯絡方式。",
                        "source_urls": [NOTICE],
                    },
                ],
                sources=[
                    source("中央116-1行前與返校規定", NOTICE),
                    *[
                        source(
                            d["label"],
                            d["url"],
                            "官方公開介紹附件，年份／116適用性未確認",
                        )
                        for d in introductions
                    ],
                ],
                last_checked=CHECKED,
                coverage_status="official_partial",
                coverage_note="母校行前義務已核對；外校生活內容為有標示來源的參考，尚未完成116與校區／track確認。",
            )
        )
        if review:
            dest = destinations[-1]
            for name_key, keys in [
                ("cost_summary", ["tuition", "cost"]),
                ("housing_summary", ["housing"]),
                ("campus_life_summary", ["arrival", "courses", "study_period"]),
            ]:
                pts = sum((reviewed_points(k) for k in keys), [])
                if pts:
                    dest[name_key] = "\n".join(pts)
            dest["sources"].extend(
                source(docs[fid]["label"], docs[fid]["url"], review["applicability"])
                for fid in review["source_ids"]
            )
            dest["coverage_note"] = (
                review["applicability"] + " 各欄缺口見逐欄查核，不表示完整核准。"
            )
            dest["first_72_hours"].extend(
                {
                    "title": "外校到校程序",
                    "detail": p,
                    "source_urls": [docs[fid]["url"] for fid in review["source_ids"]],
                }
                for p in reviewed_points("arrival")
            )
        byfield = {}
        categories = {
            "eligibility": ["申請資格", "開放申請科系"],
            "language": ["語言限制", "語言要求"],
            "host_documents": ["申請文件", "所需文件", "申請方式"],
            "host_deadline": ["申請截止日期", "申請截止日"],
            "study_period": ["交換期間"],
            "courses": ["課程介紹", "課程資訊"],
            "tuition": ["學費"],
            "cost": ["生活費"],
            "housing": ["住宿"],
            "insurance": ["保險"],
            "visa": ["簽證"],
            "arrival": [],
        }
        for key, label in FIELDS.items():
            found = [x for k in categories.get(key, []) for x in fields[k]]
            status = (
                "available"
                if key in ["home_documents", "home_deadline"]
                else "needs_confirmation"
                if key == "quota" or found or key in ["language", "eligibility"]
                else "missing"
            )
            note = (
                "116母校簡章第4頁及首頁現行下載表格；home文件不代表host清單完整。"
                if key == "home_documents"
                else "116線上12/4中午12時、系所紙本12/11下午5時（臺灣時間）；系所12/18送件不屬學生期限。"
                if key == "home_deadline"
                else "116名額官方預定2026/10/12公告；115額度僅參考，未填入當期。"
                if key == "quota"
                else "已取得官方公開參考原文；年度、校區／track及116適用性仍須核對。"
                if found
                else "已有115表列文字；不是116當期資格與語言核准。"
                if key in ["eligibility", "language"]
                else "尚未取得並核對完整外校內容；不表示官方未公告。"
            )
            byfield[key] = dict(
                key=key,
                label=label,
                status=status,
                note=note,
                source_urls=list(
                    dict.fromkeys(
                        [NOTICE]
                        if key.startswith("home_") or key == "quota"
                        else [LIST + f"#page={rs[0]['page']}"]
                        if key in ["eligibility", "language"]
                        else [x["source_url"] for x in found]
                    )
                ),
                original_evidence=found,
                unresolved="核對2027–2028的官方方案、年度、文件及期限。"
                if key not in ["home_documents", "home_deadline", "quota"]
                else None,
            )
        if review:
            for key, value in review["fields"].items():
                ev = []
                for ref in value["sources"]:
                    d = docs[ref["id"]]
                    p = next(p for p in d["pages"] if p["page"] == ref["page"])
                    ev.append(
                        {
                            "text": p["text"],
                            "source_url": d["url"],
                            "page": p["page"],
                            "source_title": d["label"],
                            "applicability": review["applicability"],
                            "checked_at": CHECKED,
                        }
                    )
                byfield[key].update(
                    status="needs_confirmation"
                    if value.get("unresolved")
                    else "available",
                    note=" ".join(value["points"]),
                    source_urls=list(dict.fromkeys(x["source_url"] for x in ev)),
                    original_evidence=ev,
                    unresolved=value.get("unresolved"),
                    applicability=review["applicability"],
                )
        byfield["home_documents"]["original_evidence"] = [
            home_evidence("notice", 4, NOTICE),
            home_evidence("forms", 1, FORMS),
            home_evidence("forms", 2, FORMS),
        ]
        byfield["home_documents"]["source_urls"] = [
            NOTICE + "#page=4",
            FORMS + "#page=1",
            FORMS + "#page=2",
        ]
        byfield["home_deadline"]["original_evidence"] = [
            home_evidence("notice", 2, NOTICE)
        ]
        byfield["quota"]["original_evidence"] = [home_evidence("notice", 2, NOTICE)]
        audit.append(
            dict(
                school_name=name,
                country=country,
                source_rows=rowids,
                checked_at=CHECKED,
                fields=byfield,
                read_sources=[
                    dict(
                        id=d["id"],
                        url=d["url"],
                        title=d["label"],
                        sha256=d.get("sha256"),
                        pages=len(d["pages"]),
                        text_quality_issues=d.get("text_quality_issues", []),
                        non_text_pages=d.get("non_text_pages", []),
                        status="reviewed_partial_scope"
                        if review and d["id"] in review["source_ids"]
                        else "extracted_not_cycle_approved",
                        applicability=review["applicability"]
                        if review and d["id"] in review["source_ids"]
                        else "年度、校區與track適用性待核對",
                    )
                    for d in selected
                ],
                unretrieved_sources=[
                    {
                        "id": fid,
                        "url": docs.get(fid, {}).get(
                            "url", f"https://drive.google.com/file/d/{fid}/view"
                        ),
                        "reason": docs.get(fid, {}).get("error", "not_downloaded"),
                    }
                    for fid in related
                    if fid not in docs or docs[fid].get("error")
                ],
            )
        )
        if review:
            workflows[-1]["sources"].extend(
                {
                    "title": docs[fid]["label"],
                    "source_url": docs[fid]["url"],
                    "role": "partner_university",
                    "authority": "partner_official",
                    "checked_at": CHECKED,
                }
                for fid in review["source_ids"]
                if docs[fid].get("authority_kind", "partner_university")
                == "partner_university"
                and fid != "host-fr-housing"
            )
        for d in {
            d["id"]: d
            for d in [
                *introductions,
                *([docs[fid] for fid in review["source_ids"]] if review else []),
            ]
        }.values():
            text = "\n\n".join(
                (
                    f"【第{p['page']}頁】"
                    if p["page"] is not None
                    else "【網頁／無PDF頁碼】"
                )
                + f"\n{p['text']}"
                for p in d["pages"]
            )
            pages.append(
                dict(
                    title=f"{zh}：{d['label']}（116適用性待查）",
                    source_url=d["url"],
                    text=text,
                    summary="中央公開參考附件，原始年份／方案與116年度適用性尚待確認。",
                    category="partner_school",
                    crawled_at=CHECKED,
                    content_hash=hashlib.sha256(text.encode()).hexdigest(),
                )
            )
    # Home pages retain exact source text and original page markers.
    from pypdf import PdfReader

    for name, link, title in [
        ("notice", NOTICE, "中央116學年度第一梯次甄選簡章"),
        ("forms", FORMS, "中央首頁現行同意書下載（檔名2022）"),
        (
            "qa",
            "https://oia.ncu.edu.tw/static/file/26/1026/img/272/QA-20241202.pdf",
            "中央FAQ（2024參考，與116差異分列）",
        ),
    ]:
        reader = PdfReader(SOURCES / f"{name}.pdf")
        text = "\n\n".join(
            f"【第{i + 1}頁】\n{p.extract_text()}" for i, p in enumerate(reader.pages)
        )
        pages.append(
            dict(
                title=title,
                source_url=link,
                text=text,
                summary=title,
                category="exchange_application",
                crawled_at=CHECKED,
                content_hash=hashlib.sha256(text.encode()).hexdigest(),
            )
        )
    periods = [
        dict(
            title="中央116-1線上甄選申請",
            details=HOME_POINTS[:1],
            scope="home_application",
            program_types=["exchange"],
            academic_year="116",
            application_round=ROUND,
            opens_at="2026-11-16T09:00:00+08:00",
            deadline_at="2026-12-04T12:00:00+08:00",
            date_status="verified_exact",
            status="upcoming",
            status_note="簡章第2頁：臺灣時間；線上及紙本皆須完成。",
            source=source("116-1簡章第2頁"),
            checked_at=CHECKED,
        ),
        dict(
            title="學生紙本資料繳至系所",
            details=[
                "完成簽核後於2026/12/11 17:00前交系所；系所12/18 17:00送國際處，兩者不可混淆。"
            ],
            scope="home_application",
            program_types=["exchange"],
            academic_year="116",
            application_round=ROUND,
            deadline_at="2026-12-11T17:00:00+08:00",
            date_status="verified_exact",
            status="action_required",
            status_note="简章第2頁：學生紙本送件期限，臺灣時間。",
            source=source("116-1簡章第2頁"),
            checked_at=CHECKED,
        ),
    ]
    dashboard = dict(
        school_name=HOME,
        last_checked=CHECKED,
        academic_score_minimum=None,
        academic_score_rule="中央116-1：大學部已修業學年平均60分、研究生70分；在職專班可申請但无研修獎學金。目前大學部五／六年級不具資格。",
        selection_rules={
            "academic_policy": "percentage",
            "academic_reference_year": "116",
            "pending_quota_planning": True,
            "partner_requirements_need_confirmation": True,
            "degree_score_minimums": SCORE_MINIMUMS,
            "excluded_undergraduate_years": EXCLUDED_YEARS,
            "language_certificate_required": True,
        },
        application_periods=periods,
        program_overview=[
            dict(
                title="116-1最新公告與名額狀態",
                details=[
                    "116-1甄選簡章於2026/9/5公告，AY2027–2028。名額預定2026/10/12公布；首頁截至2026/10/8仍連115表。",
                    "216歷史表列逐列保存；靜岡、南洋理工不同列項保留方案，名額不相加。",
                    "2027/9–2028/2一學期、2027/9–2028/6一學年、2028/2–6一學期；实际依外校校曆。",
                ],
                source=source("中央官方交換計畫與116-1簡章", INDEX),
            )
        ],
        eligibility=[
            dict(
                title="中央校內資格",
                details=[
                    "須系所、導師（大學部）／指導教授（研究所）同意；至少一學年在學成績，碩一可附大學歷年成績。",
                    "大學部平均60、研究生70；具本校學籍（含在職專班及境外生），交換期间仍須保有學籍。",
                    "目前大五／大六不具申請資格；前一年獲錄取后自願放棄者原則上一年不得申請。",
                    "陸生不可申請大陸、僑生不可申請原僑居地、雙重國籍勿選所持國籍國家。",
                    "校內錄取是推薦資格；不得改變甄選學制、延至下一學年或保留錄取。",
                ],
                source=source("116-1簡章第6–7頁"),
            )
        ],
        language_requirements=[
            dict(
                title="校內正式語檢與外校門檻分開",
                details=[
                    HOME_POINTS[2],
                    HOME_POINTS[-1],
                    "第4頁列TOEFL iBT/ITP、IELTS Academic、GEPT複試、TOEIC聽讀、領思實用組、培力及志願校接受第三外語；第6頁寫iBT/PBT及未重列IELTS組別，差異保留待國際處確認。",
                    "FAQ檔為2024版本：補繳說明舉2023例，不作116當期截止；以116简章與当期通知核對。",
                ],
                source=source("116-1簡章第4、6、7頁"),
            )
        ],
        required_documents=[
            dict(
                title="中央校內必繳文件（home）",
                details=[d["name"] for d in HOME_DOCS],
                source=source("116-1簡章第4頁"),
            ),
            dict(
                title="選繳與外校文件（host）",
                details=[
                    "外校規定語檢、其他能力／作品為校內選繳；外校要求仍須依通知完成。",
                    "每校host文件、表格、份數、簽章及期限另查，不以母校文件清單代替。",
                ],
                source=source("116-1簡章第4–5頁"),
            ),
        ],
        scholarship_info=[
            dict(
                title="研修獎學金／學費與限制",
                details=[
                    "符合資格者擇優獎勵，不需另繳申請表；金額視年度預算調整，不保證補助。",
                    "校內補助核准後出國前80%，返國一週內檢附規定文件後核發剩餘款。",
                    "學海限非大陸含港澳地区；在職專班不具研修獎學金受領資格。",
                    "境外生受領教育部／本校／政府獎學金者，出國期間不支領，僅保留原學雜費減免。",
                    "交換期間本校仍須註冊繳費；自費訪問方案可能須繳兩校學費，逐track確認。",
                ],
                source=source("116-1簡章第6–8頁"),
            )
        ],
        document_explanations=[
            dict(
                title="家長與個資同意書",
                summary="首頁目前提供forms-2022.pdf：第1頁個資同意書、第2頁家長同意書、第3頁填寫範例。檔名2022不表示新116版表格；使用前核對當期通知。",
                key_points=[
                    "家長本人親筆簽名，學生亦簽名。",
                    "個資同意書學生勾選並簽名。",
                ],
                source=source("中央交換計畫表單下載", FORMS),
                document_url=FORMS,
                full_text_extracted=True,
            )
        ],
        rule_explanations=[
            dict(
                title="行前、修課與返校",
                summary="出國前兩週完成行前程序單；返國一週內填返校程序單，心得WORD 800–1500字及至少四張照片。外校修課限制与母校採認分別核對。",
                key_points=[
                    "足額醫療、意外、海外急難救助保險；自行簽證及役男許可。",
                    "最低修課兩門且一門專業課，學則另列兩門或六學分。",
                    "延畢生學分費、平安保險、網絡費及兩階段校際選課另查。",
                ],
                source=source("116-1簡章第7–9頁"),
                document_url=NOTICE,
                full_text_extracted=True,
            )
        ],
        sources=[
            source("中央116-1甄選簡章"),
            source("中央官方交換生計畫", INDEX),
            source("115年度名額表（歷史）", LIST),
        ],
        partner_universities=partners,
    )
    dashboard = StudentDashboard.model_validate(dashboard)
    write_json(
        output / "student_dashboard.json",
        dashboard.model_dump(mode="json", exclude={"partner_universities"}),
    )
    info = ExchangeInfo(
        school_name=HOME,
        program_type=["交換學生"],
        academic_year=["116（AY2027–2028）"],
        semester=["第一梯次"],
        application_period=[HOME_POINTS[0]],
        eligibility=dashboard.eligibility[0].details,
        language_requirement=dashboard.language_requirements[0].details,
        required_documents=[d["name"] for d in HOME_DOCS],
        scholarship_info=dashboard.scholarship_info[0].details,
        source_urls=[NOTICE, INDEX, FORMS],
        last_checked=CHECKED,
    )
    write_json(output / "exchange_info.json", info.model_dump(mode="json"))
    write_rows(output / "partners.jsonl", partners, PartnerUniversity)
    write_rows(
        output / "application_workflows.jsonl", workflows, UniversityApplicationWorkflow
    )
    write_rows(output / "destination_profiles.jsonl", destinations, DestinationProfile)
    write_rows(output / "partner_research.jsonl", research, PartnerResearchRecord)
    write_rows(
        output / "pages.jsonl",
        list({p["source_url"]: p for p in pages}.values()),
        ProcessedPage,
    )
    write_json(output / "field-audit.json", audit)
    import csv

    with (output / "field-coverage.csv").open(
        "w", encoding="utf-8", newline=""
    ) as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(
            [
                "學校／track",
                "國家",
                "115來源列",
                "已讀host來源數",
                *FIELDS.values(),
                "未解問題",
            ]
        )
        for row in audit:
            writer.writerow(
                [
                    row["school_name"],
                    row["country"],
                    ";".join(row["source_rows"]),
                    len(row["read_sources"]),
                    *(row["fields"][k]["status"] for k in FIELDS),
                    "；".join(
                        f"{f['label']}：{f['unresolved']}"
                        for f in row["fields"].values()
                        if f.get("unresolved")
                    ),
                ]
            )
    write_json(
        output / "import-provenance.json",
        {
            "checked_at": CHECKED,
            "builder": "scripts/build_ncu_catalog.py",
            "base_commit": "f6ad1b8",
            "input_sha256": {
                path.name: hashlib.sha256(path.read_bytes()).hexdigest()
                for path in sorted(SOURCES.iterdir())
                if path.is_file() and path.suffix in {".json", ".gz", ".pdf", ".jpg"}
            },
            "table_year": "115",
            "home_year": "116",
            "current_host_coverage": "partial",
            "automatic_eligibility_inference": False,
            "home_deadline_timezone": "Asia/Taipei",
            "host_deadline_reminders": False,
        },
    )
    (output / "source-evidence.json.gz").write_bytes(
        gzip.compress(
            json.dumps(evidence + web_evidence, ensure_ascii=False).encode(), mtime=0
        )
    )
    write_json(
        output / "catalog-completeness.json",
        {
            "checked_at": CHECKED,
            "academic_year": "116",
            "home_notice_confirmed": True,
            "current_list_status": "scheduled_not_yet_announced",
            "current_list_expected_date": "2026-10-12",
            "historical_rows": len(rows),
            "catalog_entries": len(partners),
            "source_documents_attempted": len(evidence),
            "source_documents_extracted": sum(
                bool(d.get("pages")) and not d.get("error") for d in evidence
            ),
            "source_documents_with_errors": sum(bool(d.get("error")) for d in evidence),
            "source_documents_with_text_quality_gaps": sum(
                bool(d.get("text_quality_issues")) for d in evidence
            ),
            "source_documents_with_non_text_pages": sum(
                bool(d.get("non_text_pages")) for d in evidence
            ),
            "source_non_text_page_count": sum(
                len(d.get("non_text_pages", [])) for d in evidence
            ),
            "host_web_checks": len(web_evidence),
            "host_web_checks_with_errors": sum(
                bool(d.get("error")) for d in web_evidence
            ),
            "source_mapped_entries": sum(bool(x["read_sources"]) for x in audit),
            "reviewed_host_records": len(reviewed),
            "host_full_116_verification_count": 0,
            "pending_workflows": len(workflows),
            "provenance_note": "提取不是當期資格核准；逐欄缺口與原文分列於field-audit.json。",
        },
    )
    print(
        json.dumps(load_json(output / "catalog-completeness.json"), ensure_ascii=False)
    )


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument(
        "--output-dir", type=Path, default=ROOT / "src/exchange_info/official_data/ncu"
    )
    build(p.parse_args().output_dir)
