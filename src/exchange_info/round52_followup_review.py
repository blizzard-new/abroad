"""Round 52 follow-up data verification and consistency review.

Covers:
1. NTU & Multi-Plan preference capacity consistency (up to 30 preferences for NTU,
   <=2 for CGU, <=3 for CCU) across backend models, rule engine, OpenAPI schema,
   and frontend multi-plan UI.
2. NTUST 22 Mainland China exchange partner rows reconciled against the archived
   4-page official table `sources/ntust/reviewed_1152_mainland_schools_20261021.pdf`
   (sha256: 16e12225089fae278921e00a860c342b31385bce8934eb8ad512b2ee487a0ac6),
   plus cleanup of the 22 Mainland sister schools not listed in that 115-2 table.
3. TKU Round 1 Japanese guide (`earlier_round_programmes.jsonl`) surfacing
   `home_language` and `department_scope` (e.g., Waseda `N1（各系要求不同）；GPA依各系要求。`)
   in `tku_census.reference_partners` `PartnerProgramOption.eligibility` and marking
   `round42-followup-source-notes.json` findings `data_changed: true`.
4. NCKU Vytautas Magnus University (`vdu.lt`) and VSB Technical University of Ostrava
   (`vsb.cz` Fact Sheet PDF) live official host incoming exchange evidence attached via
   `partner_exchange_details` and `field_evidence["host_language_evidence"]` to document
   host `TOEIC 785` requirements alongside NCKU's mother-school `"TOEIC 讀寫785"` text.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from exchange_info.ntust_source_review import (
    ACADEMIC as NTUST_ACADEMIC,
    HISTORICAL as NTUST_HISTORICAL,
    LANGUAGE as NTUST_LANGUAGE,
    MAINLAND as NTUST_MAINLAND_URL,
    write_atomic,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
ROUND52_CHECKED_AT = "2026-10-22T00:30:00+00:00"
ROUND52_MANIFEST_REL = Path(
    "docs/data-verification-20261021/round52-ntust-tku-ncku-ntu-review.json"
)
NTUST_MAINLAND_SCHOOLS_PDF_REL = "sources/ntust/reviewed_1152_mainland_schools_20261021.pdf"
NTUST_MAINLAND_SCHOOLS_PDF_SHA256 = (
    "16e12225089fae278921e00a860c342b31385bce8934eb8ad512b2ee487a0ac6"
)

# Exact 22 schools in `sources/ntust/reviewed_1152_mainland_schools_20261021.pdf`
# (58 total seats across 4 pages)
NTUST_115_2_MAINLAND_REVIEWED: dict[str, dict[str, Any]] = {
    "同濟大學": {
        "row_no": 1,
        "page": 1,
        "quota": "3 名（含建築系所 1 名；115-2 大陸地區交換公告名額）",
        "colleges": "全校各學院（限大學部或碩士生；含建築系所 1 名）",
        "degree_levels": "學士班大二（含）以上（具一學年成績）、碩士班（具一學期成績）；限大學部或碩士生，不含博士班及在職專班",
        "raw_excerpt": "1 華東地區 上海市 同濟大學 985/211 工程 3(含建築系所 1 名) 限大學部或碩士生",
    },
    "電子科技大學": {
        "row_no": 2,
        "page": 1,
        "quota": "2 名（115-2 大陸地區交換公告名額）",
        "colleges": "全校各學院（電資學院優先；大學部、研究所）",
        "degree_levels": "學士班大二（含）以上（具一學年成績）、碩士班及博士班（具一學期成績）；電資學院優先，不含在職專班",
        "raw_excerpt": "2 西南地區 四川省 電子科技大學 985/211 工程 2 電資學院優先",
    },
    "廈門大學": {
        "row_no": 3,
        "page": 1,
        "quota": "3 名（115-2 大陸地區交換公告名額）",
        "colleges": "全校各學院（限大學部或碩士生）",
        "degree_levels": "學士班大二（含）以上（具一學年成績）、碩士班（具一學期成績）；限大學部或碩士生，不含博士班及在職專班",
        "raw_excerpt": "3 華東地區 福建省 廈門大學 985/211 工程 3 限大學部或碩士生",
    },
    "大連理工大學": {
        "row_no": 4,
        "page": 1,
        "quota": "2 名（115-2 大陸地區交換公告名額）",
        "colleges": "全校各學院（大學部、研究所）",
        "degree_levels": "學士班大二（含）以上（具一學年成績）、碩士班及博士班（具一學期成績）；不含在職專班",
        "raw_excerpt": "4 東北地區 遼寧省 大連理工大學 985/211 工程 2",
    },
    "北京科技大學": {
        "row_no": 5,
        "page": 1,
        "quota": "2 名（115-2 大陸地區交換公告名額）",
        "colleges": "全校各學院（大學部、研究所）",
        "degree_levels": "學士班大二（含）以上（具一學年成績）、碩士班及博士班（具一學期成績）；不含在職專班",
        "raw_excerpt": "5 華北地區 北京市 北京科技大學 211 工程 2",
    },
    "北京交通大學": {
        "row_no": 6,
        "page": 1,
        "quota": "2 名（115-2 大陸地區交換公告名額）",
        "colleges": "全校各學院（大學部、研究所）",
        "degree_levels": "學士班大二（含）以上（具一學年成績）、碩士班及博士班（具一學期成績）；不含在職專班",
        "raw_excerpt": "6 華北地區 北京市 北京交通大學 211 工程 2",
    },
    "浙江大學": {
        "row_no": 7,
        "page": 1,
        "quota": "3 名（115-2 大陸地區交換公告名額）",
        "colleges": "除醫學院外開放全校申請；管理學院不收碩士生（大學部限大二及大三生；研究所）",
        "degree_levels": "學士班限大二及大三生（具一學年成績）、碩士班（管理學院除外）及博士班（具一學期成績）；除醫學院外開放全校申請，不含在職專班",
        "raw_excerpt": "7 華東地區 浙江省 浙江大學 985/211 工程 3 1.除醫學院外，開放全校申請 2.管院不收碩士生 3.大學部僅收大二及大三生",
    },
    "武漢理工大學": {
        "row_no": 8,
        "page": 2,
        "quota": "2 名（115-2 大陸地區交換公告名額）",
        "colleges": "全校各學院（大學部、研究所）",
        "degree_levels": "學士班大二（含）以上（具一學年成績）、碩士班及博士班（具一學期成績）；不含在職專班",
        "raw_excerpt": "8 華中地區 湖北省 武漢理工大學 211 工程 2",
    },
    "華中科技大學": {
        "row_no": 9,
        "page": 2,
        "quota": "2 名（115-2 大陸地區交換公告名額）",
        "colleges": "全校各學院（大學部、研究所）",
        "degree_levels": "學士班大二（含）以上（具一學年成績）、碩士班及博士班（具一學期成績）；不含在職專班",
        "raw_excerpt": "9 華中地區 湖北省 華中科技大學 985/211 工程 2",
    },
    "四川大學": {
        "row_no": 10,
        "page": 2,
        "quota": "3 名（115-2 大陸地區交換公告名額）",
        "colleges": "全校各學院（大學部、研究所）",
        "degree_levels": "學士班大二（含）以上（具一學年成績）、碩士班及博士班（具一學期成績）；不含在職專班",
        "raw_excerpt": "10 西南地區 四川省 四川大學 985/211 工程 3",
    },
    "重慶大學": {
        "row_no": 11,
        "page": 2,
        "quota": "3 名（115-2 大陸地區交換公告名額）",
        "colleges": "全校各學院（大學部、研究所）",
        "degree_levels": "學士班大二（含）以上（具一學年成績）、碩士班及博士班（具一學期成績）；不含在職專班",
        "raw_excerpt": "11 西南地區 重慶市 重慶大學 985/211 工程 3",
    },
    "蘇州大學": {
        "row_no": 12,
        "page": 2,
        "quota": "3 名（115-2 大陸地區交換公告名額）",
        "colleges": "全校各學院（大學部、研究所）",
        "degree_levels": "學士班大二（含）以上（具一學年成績）、碩士班及博士班（具一學期成績）；不含在職專班",
        "raw_excerpt": "12 華東地區 江蘇省 蘇州大學 211 工程 3",
    },
    "合肥工業大學": {
        "row_no": 13,
        "page": 2,
        "quota": "3 名（115-2 大陸地區交換公告名額）",
        "colleges": "全校各學院（大學部、研究所）",
        "degree_levels": "學士班大二（含）以上（具一學年成績）、碩士班及博士班（具一學期成績）；不含在職專班",
        "raw_excerpt": "13 華東地區 安徽省 合肥工業大學 211 工程 3",
    },
    "蘭州大學": {
        "row_no": 14,
        "page": 3,
        "quota": "3 名（115-2 大陸地區交換公告名額）",
        "colleges": "全校各學院（大學部、研究所）",
        "degree_levels": "學士班大二（含）以上（具一學年成績）、碩士班及博士班（具一學期成績）；不含在職專班",
        "raw_excerpt": "14 西北地區 甘肅省 蘭州大學 985/211 工程 3",
    },
    "南京大學": {
        "row_no": 15,
        "page": 3,
        "quota": "2 名（115-2 大陸地區交換公告名額）",
        "colleges": "須為相對應系所（大學部、研究所；應屆畢業生不得在下學期提出申請）",
        "degree_levels": "學士班大二（含）以上（具一學年成績）、碩士班及博士班（具一學期成績）；須為相對應系所，應屆畢業生不得在下學期提出申請，不含在職專班",
        "raw_excerpt": "15 華東地區 江蘇省 南京大學 985/211 工程 2 1. 須為相對應系所 2. 應屆畢業生不得在下學期提出申請",
    },
    "西安交通大學": {
        "row_no": 16,
        "page": 3,
        "quota": "3 名（115-2 大陸地區交換公告名額）",
        "colleges": "全校各學院（大學部、研究所；應屆畢業生不得在下學期提出申請）",
        "degree_levels": "學士班大二（含）以上（具一學年成績）、碩士班及博士班（具一學期成績）；應屆畢業生不得在下學期提出申請，不含在職專班",
        "raw_excerpt": "16 西北地區 陝西省 西安交通大學 985/211 工程 3 應屆畢業生不得在下學期提出申請",
    },
    "上海大學": {
        "row_no": 17,
        "page": 3,
        "quota": "3 名（115-2 大陸地區交換公告名額）",
        "colleges": "全校各學院（大學部、研究所）",
        "degree_levels": "學士班大二（含）以上（具一學年成績）、碩士班及博士班（具一學期成績）；不含在職專班",
        "raw_excerpt": "17 華東地區 上海市 上海大學 211 工程 3",
    },
    "吉林大學": {
        "row_no": 18,
        "page": 3,
        "quota": "3 名（115-2 大陸地區交換公告名額）",
        "colleges": "全校各學院（大學部、研究所）",
        "degree_levels": "學士班大二（含）以上（具一學年成績）、碩士班及博士班（具一學期成績）；不含在職專班",
        "raw_excerpt": "18 東北地區 吉林省 吉林大學 985/211 工程 3",
    },
    "東南大學": {
        "row_no": 19,
        "page": 3,
        "quota": "2 名（115-2 大陸地區交換公告名額）",
        "colleges": "全校各學院（大學部、研究所；不接受大四及應屆畢業生申請）",
        "degree_levels": "學士班大二及大三（不接受大四申請）、碩士班及博士班（具一學期成績；不接受應屆畢業生申請）；不含在職專班",
        "raw_excerpt": "19 華東地區 江蘇省 東南大學 985/211 工程 2 不接受大四及應屆畢業生申請",
    },
    "華中師範大學": {
        "row_no": 20,
        "page": 3,
        "quota": "2 名（115-2 大陸地區交換公告名額）",
        "colleges": "全校各學院（大學部、研究所）",
        "degree_levels": "學士班大二（含）以上（具一學年成績）、碩士班及博士班（具一學期成績）；不含在職專班",
        "raw_excerpt": "20 華中地區 湖北省 華中師範大學 211 工程 2",
    },
    "福州大學": {
        "row_no": 21,
        "page": 4,
        "quota": "3 名（115-2 大陸地區交換公告名額）",
        "colleges": "全校各學院（大學部、研究所）",
        "degree_levels": "學士班大二（含）以上（具一學年成績）、碩士班及博士班（具一學期成績）；不含在職專班",
        "raw_excerpt": "21 華東地區 福建省 福州大學 211 工程 3",
    },
    "華東師範大學": {
        "row_no": 22,
        "page": 4,
        "quota": "3 名（115-2 大陸地區交換公告名額）",
        "colleges": "全校各學院（大學部、研究所；不接受大四及碩二生申請）",
        "degree_levels": "學士班大二及大三（不接受大四申請）、碩士班碩一（不接受碩二生申請）及博士班（具一學期成績）；不含在職專班",
        "raw_excerpt": "22 華東地區 上海市 華東師範大學 985/211 工程 3 不接受大四及碩二生申請",
    },
}

NCKU_HOST_LANGUAGE_REVIEWS: dict[str, dict[str, Any]] = {
    "維陶塔斯馬格努斯大學 Vytautas Magnus University": {
        "source_url": "https://www.vdu.lt/en/international-cooperation/for-students/vmu-bilateral-exchange-studies/incoming-exchange-students/",
        "source_sha256": "6070e1ac073303da94a83247f7daf60a7528f2eb8a406691e8f2fa7beafda7fd",
        "checked_at": ROUND52_CHECKED_AT,
        "host_language_value": (
            "接待校 VMU 雙邊交換生官方網頁明列：English language proficiency should be not lower than B2 level "
            "according to the European language levels (or equivalent: TOEFL - 65, TOEFL IBT - 72 "
            "(4 - on the new scale), TOEFL ITP - 543, IELTS - 5.5, TOEIC - 785, Duolingo - 100)。"
            "母校成大 116-1 一覽表第 6 頁寫作「TOEIC 讀寫785」，接待校官網原文則僅列「TOEIC - 785」作為 CEFR B2 等同分數；"
            "兩來源對 TOEIC 子項目表述不同，請同時參考母校表與接待校官網。"
        ),
        "host_language_excerpt": (
            "English language proficiency should be not lower than B2 level according to the European "
            "language levels (or equivalent: TOEFL - 65, TOEFL IBT - 72 (4 - on the new scale), "
            "TOEFL ITP - 543, IELTS - 5.5, TOEIC - 785, Duolingo - 100)"
        ),
        "host_academic_value": (
            "接待校 VMU 官方交換頁明列：candidate's GPA must be not lower than 70% of the maximum grade；"
            "申請時大學部須已完成 2 學期、研究所須已完成 1 學期；art/music 領域課程僅開放主修藝術／音樂之學生選修。"
        ),
        "host_academic_excerpt": (
            "candidate's GPA must be not lower than 70% of the maximum grade. during the application "
            "2 semesters must be completed by an undergraduate student/ 1 semester - by a graduate student "
            "art/music area courses are available only to the students majoring in art/music"
        ),
        "host_deadline_value": (
            "接待校 VMU 雙邊交換申請截止日（非成大校內截止日）：秋季／全學年為 4 月 17 日；春季／曆年為 10 月 17 日。"
        ),
        "host_deadline_excerpt": (
            "Application Deadlines: April 17 For 1st semester or full academic year studies / "
            "October 17 For 2nd semester or calendar year studies"
        ),
    },
    "俄斯特拉發技術大學 VSB Technical University of Ostrava": {
        "source_url": "https://www.vsb.cz/export/sites/vsb/mobility/.content/galerie-souboru/Fact_Sheet_WEB.pdf",
        "source_sha256": "e5440f5596286f548fa4e165c033b21102d49fc0005105a4b5a7ab0e7029310c",
        "source_pages": [1, 2],
        "checked_at": ROUND52_CHECKED_AT,
        "host_language_value": (
            "接待校 VSB-TUO 官方 Fact Sheet（p. 1）明列：IELTS score 5,0; TOEFL internet-based score 62; "
            "TOEIC 785 (possibly other certificates at the level B1 – B2)。母校成大 116-1 一覽表第 3 頁寫作"
            "「TOEIC聽說讀寫 785 / TOEFL iBT 72/ IELTS 5.5」，高於接待校 Fact Sheet 的 TOEFL 62 / IELTS 5.0 "
            "且將 TOEIC 標為「聽說讀寫 785」；校內甄選須先符合成大一覽表規定，接待校複審則依 Fact Sheet 辦理。"
        ),
        "host_language_excerpt": (
            "Language requirements for exchange students (TOEFL score, IELTS etc.): "
            "IELTS score 5,0; TOEFL internet-based score 62; TOEIC 785 (possibly other certificates at the level B1 – B2)"
        ),
        "host_credit_value": (
            "接待校 VSB-TUO 官方 Fact Sheet（p. 1）規定：交換生每學期建議修習 30 ECTS，最低須修習 20 ECTS credits。"
        ),
        "host_credit_excerpt": (
            "How many credits exchange students need to take per semester? "
            "30 ECTS credits recommended, 20 ECTS credits minimum"
        ),
        "host_deadline_value": (
            "接待校 VSB-TUO 官方 Fact Sheet（p. 2）提名與申請截止日（需簽證國家學生）："
            "冬季學期提名 4 月 15 日、申請 4 月 30 日；夏季學期提名 10 月 15 日、申請 10 月 31 日（非成大校內甄選截止日）。"
        ),
        "host_deadline_excerpt": (
            "Nomination deadlines for all Exchange students: April 30 for the winter semester or the whole academic year "
            "(April 15 for students from countries with the visa requirements); November 15 for the summer semester "
            "(October 15 for students from countries with the visa requirements)"
        ),
    },
}


def apply_ntust_mainland_22_review(root: Path = REPO_ROOT) -> int:
    pdf_path = root / NTUST_MAINLAND_SCHOOLS_PDF_REL
    if hashlib.sha256(pdf_path.read_bytes()).hexdigest() != NTUST_MAINLAND_SCHOOLS_PDF_SHA256:
        raise ValueError("NTUST 115-2 mainland schools PDF sha256 mismatch")

    folder = root / "src/exchange_info/official_data/ntust"
    partners_path = folder / "partners.jsonl"
    dest_path = folder / "destination_profiles.jsonl"

    partners = [json.loads(s) for s in partners_path.read_text("utf-8").splitlines() if s.strip()]
    destinations = [json.loads(s) for s in dest_path.read_text("utf-8").splitlines() if s.strip()]
    dest_by_name = {d["school_name"]: d for d in destinations}

    updated_count = 0
    matched_zh: set[str] = set()

    for p in partners:
        if p.get("country") not in {"中國大陸", "大陸地區"}:
            continue
        zh_name = p["school_name"].split()[0]
        reviewed = NTUST_115_2_MAINLAND_REVIEWED.get(zh_name)
        gpa_req = p.get(
            "gpa_requirement",
            "大學部歷年學業總平均達 75 分（含）以上；研究所歷年學業總平均達 80 分（含）以上",
        )
        if reviewed:
            matched_zh.add(zh_name)
            quota_str = reviewed["quota"]
            colleges_str = reviewed["colleges"]
            degree_str = reviewed["degree_levels"]
            factsheet_url = "https://www.oia.ntust.edu.tw/p/406-1060-143054,r1580.php?Lang=zh-tw"
            ev_note = (
                f"已核對臺科大115-2大陸地區受理申請交換學校一覽表（第{reviewed['page']}頁編號{reviewed['row_no']}）："
                f"「{reviewed['raw_excerpt']}」。該梯次已截止，116-1大陸組開放名單及條件仍須待新簡章確認。"
            )
            ev_pages = [reviewed["page"]]
            ev_excerpt = reviewed["raw_excerpt"]
        else:
            quota_str = "未列入 115-2 大陸地區交換學校一覽表（歷年姊妹校參考；當期是否開缺及名額依最新簡章公告為準）"
            colleges_str = "待確認（未列入 115-2 大陸地區受理申請交換學校一覽表；實際開放學院依當期簡章公告為準）"
            degree_str = "待確認（未列入 115-2 大陸地區受理申請交換學校一覽表；母校大陸交換通則為大學部大二以上、碩博士班具一學期成績且不含在職專班）"
            factsheet_url = None
            ev_note = (
                "已核對臺科大115-2大陸地區受理申請交換學校一覽表（共22校58名），本校未列入115-2大陸組開放一覽表；"
                "僅保留歷年姊妹校參考，不得標為115-2公告名額或推估每學期2–5名。"
            )
            ev_pages = [1, 2, 3, 4]
            ev_excerpt = None

        course_restr = f"開放院系：{colleges_str}｜名額：{quota_str}｜學業門檻：{gpa_req}"
        old_notes = p.get("notes") or ""
        exp_Lines = [line for line in old_notes.splitlines() if line.startswith("【歷年學長姐心得】")]
        notes_lines = [
            "【合作類別與期程】交換學生（赴中國大陸地區交換計畫）｜交換期間：一學期為原則",
            f"【當期公告名額】{quota_str}",
            f"【開放學院與學制】{colleges_str}｜{degree_str}",
            f"【申請條件明細】{course_restr}",
            *exp_Lines,
        ]

        p["quota"] = quota_str
        p["colleges"] = colleges_str
        p["degree_levels"] = degree_str
        p["factsheet_url"] = factsheet_url
        p["course_restrictions"] = course_restr
        p["notes"] = "\n".join(notes_lines)
        p["eligibility"] = (
            f"本筆115-2資料僅歷史參考，不能認定符合116-1；115-2大陸地區交換一覽表條件：{colleges_str}（{degree_str}）。"
            f"{NTUST_ACADEMIC} {NTUST_LANGUAGE}"
        )

        summary = p.setdefault("student_summary_zh", {})
        summary.update(
            quota=quota_str,
            colleges=colleges_str,
            degree_levels=degree_str,
            eligibility_points=[p["eligibility"]],
            application_deadline=NTUST_HISTORICAL,
            application_steps=[NTUST_HISTORICAL],
        )

        ev = p.setdefault("field_evidence", {})
        for key in ("quota", "colleges", "degree_levels", "language_requirement", "study_period"):
            entry: dict[str, Any] = {
                "source_url": NTUST_MAINLAND_URL,
                "academic_year": "115",
                "application_round": "115-2（歷史參考）",
                "checked_at": ROUND52_CHECKED_AT,
                "status": "reference_only",
                "source_pages": ev_pages,
                "note": ev_note,
            }
            if ev_excerpt:
                entry["excerpt"] = ev_excerpt
            ev[key] = entry

        dest = dest_by_name.get(p["school_name"])
        if dest is not None:
            campus_prefix = dest["campus_life_summary"].split("\n")[0]
            open_target_line = (
                f"開放對象：{colleges_str}（{degree_str}）｜依臺科大規定，領取交換獎學金者每學期至少須修習 3 門（含）"
                "以上專業科目並及格，自費交換生每學期至少須修習 2 門（含）以上專業科目並及格。"
            )
            dest["campus_life_summary"] = f"{campus_prefix}\n{open_target_line}"
            for sec in dest.get("student_guide_sections", []):
                if sec.get("key") == "courses":
                    sec["summary"] = open_target_line
                    sec["points"] = [
                        open_target_line,
                        f"姊妹校具體申請與選課要求：{course_restr}",
                    ]
            if not reviewed:
                dest["sources"] = [
                    s for s in dest.get("sources", []) if "交換簡章／課程資訊（Fact Sheet）" not in s.get("title", "")
                ]
            dest["last_checked"] = ROUND52_CHECKED_AT

        updated_count += 1

    if matched_zh != set(NTUST_115_2_MAINLAND_REVIEWED):
        missing = sorted(set(NTUST_115_2_MAINLAND_REVIEWED) - matched_zh)
        raise ValueError(f"Unmatched NTUST 115-2 mainland schools: {missing}")

    write_atomic(partners_path, partners, True)
    write_atomic(dest_path, destinations, True)
    return updated_count


def apply_ncku_host_language_reviews(root: Path = REPO_ROOT) -> int:
    partners_path = root / "src/exchange_info/official_data/ncku/partners.jsonl"
    partners = [json.loads(s) for s in partners_path.read_text("utf-8").splitlines() if s.strip()]
    updated = 0
    for p in partners:
        spec = NCKU_HOST_LANGUAGE_REVIEWS.get(p["school_name"])
        if not spec:
            continue
        ev_item: dict[str, Any] = {
            "source_url": spec["source_url"],
            "checked_at": spec["checked_at"],
            "status": "reference_only",
            "excerpt": spec["host_language_excerpt"],
            "note": spec["host_language_value"],
        }
        if "source_pages" in spec:
            ev_item["source_pages"] = spec["source_pages"]

        p.setdefault("field_evidence", {})["host_language_evidence"] = ev_item

        details: dict[str, Any] = dict(p.get("partner_exchange_details") or {})
        details["host_language_requirements"] = {
            "value": spec["host_language_value"],
            "status": "reference_only",
            "reason": "已核對接待校官方交換網頁／Fact Sheet 原文；母校成大116-1一覽表另有「TOEIC 讀寫785」表述，兩者並列呈現。",
            "evidence": [ev_item],
            "research_category": "unresolved_source_conflict",
        }
        if "host_academic_value" in spec:
            acad_ev = {
                "source_url": spec["source_url"],
                "checked_at": spec["checked_at"],
                "status": "reference_only",
                "excerpt": spec["host_academic_excerpt"],
                "note": spec["host_academic_value"],
            }
            details["host_academic_requirements"] = {
                "value": spec["host_academic_value"],
                "status": "reference_only",
                "reason": "接待校官方交換申請頁面所載 GPA 與已修畢學期數規定。",
                "evidence": [acad_ev],
                "research_category": "alternative_official_sources_not_fully_checked",
            }
        if "host_credit_value" in spec:
            credit_ev = {
                "source_url": spec["source_url"],
                "source_pages": spec.get("source_pages", [1]),
                "checked_at": spec["checked_at"],
                "status": "reference_only",
                "excerpt": spec["host_credit_excerpt"],
                "note": spec["host_credit_value"],
            }
            details["host_credit_load"] = {
                "value": spec["host_credit_value"],
                "status": "reference_only",
                "reason": "接待校官方 Fact Sheet 所載每學期建議與最低 ECTS 學分數。",
                "evidence": [credit_ev],
                "research_category": "alternative_official_sources_not_fully_checked",
            }
        if "host_deadline_value" in spec:
            dl_ev: dict[str, Any] = {
                "source_url": spec["source_url"],
                "checked_at": spec["checked_at"],
                "status": "reference_only",
                "excerpt": spec["host_deadline_excerpt"],
                "note": spec["host_deadline_value"],
            }
            if "source_pages" in spec:
                dl_ev["source_pages"] = spec["source_pages"]
            details["host_application_deadlines"] = {
                "value": spec["host_deadline_value"],
                "status": "reference_only",
                "reason": "接待校官方提名與申請截止日（非母校成大校內甄選截止日）。",
                "evidence": [dl_ev],
                "research_category": "alternative_official_sources_not_fully_checked",
            }

        p["partner_exchange_details"] = details
        updated += 1

    if updated != len(NCKU_HOST_LANGUAGE_REVIEWS):
        raise ValueError(f"Expected {len(NCKU_HOST_LANGUAGE_REVIEWS)} NCKU rows, updated {updated}")
    write_atomic(partners_path, partners, True)
    return updated


def write_round52_manifest(root: Path = REPO_ROOT) -> Path:
    manifest = {
        "round": 52,
        "recorded_at": ROUND52_CHECKED_AT,
        "summary": (
            "Round 52 gap closure: (1) NTU & multi-plan preference capacity consistency up to 30 preferences "
            "(with CGU <=2 and CCU <=3 home rules); (2) NTUST 44 Mainland China partner rows reconciled against "
            "the 22-school 115-2 table PDF (16e12225089fae278921e00a860c342b31385bce8934eb8ad512b2ee487a0ac6); "
            "(3) TKU Round 1 Japanese guide eligibility/language/department_scope surfaced in reference_partners "
            "and round42-followup-source-notes.json marked data_changed=true; (4) NCKU Vytautas Magnus University "
            "and VSB Technical University of Ostrava live official host TOEIC/language evidence attached."
        ),
        "ntu_preference_capacity": {
            "PersonalApplicationPlanRequest_max_preferences": 30,
            "ApplicationPlanPreference_max_rank": 30,
            "AccountApplicationWorkspace_max_schools": 30,
            "home_specific_limits": {"cgu": 2, "ccu": 3, "ntu": 30},
        },
        "ntust_mainland_review": {
            "source_file": NTUST_MAINLAND_SCHOOLS_PDF_REL,
            "source_sha256": NTUST_MAINLAND_SCHOOLS_PDF_SHA256,
            "reviewed_open_115_2_schools": len(NTUST_115_2_MAINLAND_REVIEWED),
            "reviewed_total_seats_115_2": 58,
            "unlisted_mainland_sister_schools": 22,
            "total_mainland_rows_reconciled": 44,
            "schools_115_2": NTUST_115_2_MAINLAND_REVIEWED,
        },
        "ncku_host_language_reviews": NCKU_HOST_LANGUAGE_REVIEWS,
        "tku_round1_japanese_guide": {
            "source_url": "https://oieie.tku.edu.tw/oieie/wp-content/uploads/2026/02/更新淡江大學學校財團法人淡江大學2027-2028赴日本姊妹校交換生聯合甄選作業簡章.pdf",
            "source_sha256": "bcfa995958cbe01905a20b109bd40c5789273cced8e1125dfbef7c3293b4cac2",
            "waseda_programme_id": "jp-2027-2028-round-1-29",
            "surfaced_in": "exchange_info.tku_census.reference_partners PartnerProgramOption.eligibility",
        },
        "whole_schools_verified": 0,
        "whole_partner_records_verified": 0,
    }
    out_path = root / ROUND52_MANIFEST_REL
    out_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return out_path


def apply_round52_all(root: Path = REPO_ROOT) -> dict[str, int]:
    ntust_count = apply_ntust_mainland_22_review(root)
    ncku_count = apply_ncku_host_language_reviews(root)
    write_round52_manifest(root)
    return {"ntust_mainland_rows": ntust_count, "ncku_host_rows": ncku_count}


if __name__ == "__main__":
    print(json.dumps(apply_round52_all(), ensure_ascii=False))
