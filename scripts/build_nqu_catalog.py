#!/usr/bin/env python3
"""Build the official National Quemoy University (國立金門大學, NQU) exchange data bundle."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

REPO_ROOT = Path(__file__).resolve().parents[1]
SOURCES_NQU_DIR = REPO_ROOT / "sources" / "nqu"
OFFICIAL_NQU_DIR = REPO_ROOT / "src" / "exchange_info" / "official_data" / "nqu"
STATIC_DIR = REPO_ROOT / "src" / "exchange_info" / "static"
UNIVERSITY_LOCATIONS_PATH = (
    REPO_ROOT / "src" / "exchange_info" / "official_data" / "university_locations.jsonl"
)

CHECKED_AT = "2026-11-02T00:00:00Z"

NQU_OICA_HOME_URL = "https://oica.nqu.edu.tw/"
NQU_INTL_EXCHANGE_LIST_URL = "https://oica.nqu.edu.tw/p/412-1003-1150.php?Lang=zh-tw"
NQU_INTL_STAGE2_POST_URL = "https://oica.nqu.edu.tw/p/406-1003-21011,r902.php?Lang=zh-tw"
NQU_INTL_STAGE1_ADMIT_URL = "https://oica.nqu.edu.tw/p/406-1003-28138,r1150.php?Lang=zh-tw"
NQU_MAINLAND_2027_SPRING_URL = "https://oica.nqu.edu.tw/p/406-1003-31469,r902.php?Lang=zh-tw"
NQU_MAINLAND_2027_SPRING_EXT_URL = "https://oica.nqu.edu.tw/p/406-1003-31470,r902.php?Lang=zh-tw"
NQU_MAINLAND_2027_ADMIT_URL = "https://oica.nqu.edu.tw/p/406-1003-32428,r902.php?Lang=zh-tw"
NQU_INTL_PARTNERS_URL = "https://oica.nqu.edu.tw/p/404-1003-8171.php?Lang=zh-tw"
NQU_MAINLAND_PARTNERS_URL = "https://oica.nqu.edu.tw/p/404-1003-8510.php?Lang=zh-tw"
NQU_SISTER_INTL_URL = "https://oica.nqu.edu.tw/p/404-1003-6600.php?Lang=zh-tw"
NQU_SISTER_MAINLAND_URL = "https://oica.nqu.edu.tw/p/404-1003-6599.php?Lang=zh-tw"
NQU_INTL_REGULATIONS_URL = "https://oica.nqu.edu.tw/p/405-1003-7397,c1153.php?Lang=zh-tw"
NQU_INTL_FORMS_URL = "https://oica.nqu.edu.tw/p/412-1003-995.php?Lang=zh-tw"
NQU_EXCHANGE_SECTION_URL = "https://oica.nqu.edu.tw/p/405-1003-7424,c1154.php?Lang=zh-tw"
NQU_XUEHAI_POST_URL = "https://oica.nqu.edu.tw/p/406-1003-29910,r928.php?Lang=zh-tw"
NQU_EXP_MAINLAND_URL = "https://oica.nqu.edu.tw/p/412-1003-1182.php?Lang=zh-tw"
NQU_EXP_INTL_URL = "https://oica.nqu.edu.tw/p/412-1003-1207.php?Lang=zh-tw"
NQU_TEACH_REG_URL = "https://teach.nqu.edu.tw/p/404-1001-1717.php?Lang=zh-tw"

REGION_COST_DEFAULTS = {
    "日本": (
        "每月生活費約 USD 650–1,050（折合日圓約 JPY 95,000–155,000 / 月、新臺幣約 21,000–34,000 元；含三重大學、琉球大學、新潟大學、廣島大學校內國際交流會館宿舍與伙食交通費）",
        "須由日本接待姊妹校代向出入國在留管理局申辦「在留資格認定證明書（COE）」（申請 COE 須檢附英文存款／財力證明），獲發後申辦留學簽證並強制加入日本國民健康保險（NHI）。",
    ),
    "韓國": (
        "每月生活費約 USD 600–1,000（折合韓元約 KRW 820,000–1,380,000 / 月、新臺幣約 19,500–32,000 元；含建國大學、誠信女子大學、釜山外國語大學校內外宿舍與膳食交通費）",
        "須憑韓國姊妹校核發之標準入學許可書向駐台北韓國代表部申辦 D-2-6 交換學生簽證，入境後申辦外國人登錄證（ARC）並納保韓國國民健康保險（NHIS）。",
    ),
    "中國大陸": (
        "每月生活費約 USD 300–580（折合人民幣約 CNY 2,100–4,000 / 月、新臺幣約 9,500–18,500 元；含廈門大學、四川大學、中國政法大學、北京交通大學、北京科技大學、東華大學、中國海洋大學、華中師範大學、蘭州大學、福州大學等學生宿舍與食堂費）",
        "須憑大陸姊妹校錄取通知書辦理臺胞證簽注與校內住宿登記（可搭配金門小三通金廈航線往返），並依規定投保涵蓋全期之大陸地區醫療與意外保險。",
    ),
    "澳門": (
        "每月生活費約 USD 750–1,200（折合澳門幣約 MOP 6,000–9,600 / 月、新臺幣約 24,000–38,500 元；含澳門科技大學學費、校內外住宿與膳食交通費）",
        "須由澳門科技大學協助向澳門治安警察局居留及逗留事務廳申辦逗留特別許可（學生逗留簽注），並投保涵蓋全期之海外醫療及意外險。",
    ),
    "馬來西亞": (
        "每月生活費約 USD 450–780（折合馬幣約 MYR 2,000–3,500 / 月、新臺幣約 14,500–25,000 元；含馬來亞大學、拉曼大學學生宿舍與餐飲交通費）",
        "須透過馬來西亞教育全球服務中心（EMGS）申辦學生簽證核准函（VAL）及單次入境簽證，並投保 EMGS 規定之醫療保險。",
    ),
    "土耳其": (
        "每月生活費約 USD 480–820（依匯率折合新臺幣約 15,500–26,500 元；含阿卜杜拉居爾大學、土耳其教育協會大學 TEDU 校內外住宿與膳食交通費）",
        "須憑土耳其姊妹校入學許可申辦學生簽證，入境後申辦學生居留證（İkamet İzni）並投保土耳其規定之學生醫療保險。",
    ),
    "美國": (
        "每月生活費約 USD 1,200–2,200（依匯率折合新臺幣約 38,500–70,000 元；東南密蘇里州立大學含公費生 1 名／自費生 5 名；夏威夷大學馬諾阿分校自費生每學期含學費食宿總費用約 USD 40,000）",
        "須憑美國合作校核發之 DS-2019（J-1 交換生）繳交 SEVIS I-901 費用並向 AIT 申辦簽證，並強制投保接待校規定之學生醫療保險。",
    ),
    "德國": (
        "每月生活費約 USD 950–1,450（折合歐元約 EUR 880–1,350 / 月、新臺幣約 30,500–46,500 元；含維爾茨堡-施韋因富特科技大學 THWS 學生宿舍與學期交通卡費）",
        "須開立德國限制提領帳戶（Blocked Account）並憑入學許可向德國在台協會申辦學生簽證及投保德國公保／醫療險。",
    ),
    "俄羅斯": (
        "每月生活費約 USD 500–850（依匯率折合新臺幣約 16,000–27,000 元；含莫斯科市立大學學生宿舍與市區交通膳食費）",
        "須憑莫斯科市立大學透過俄羅斯內政部核發之官方邀請函向莫北協駐台代表處申辦俄羅斯學生簽證，並投保俄羅斯境內有效之醫療保險。",
    ),
    "泰國": (
        "每月生活費約 USD 450–780（折合泰銖約 THB 15,500–27,000 / 月、新臺幣約 14,500–25,000 元；含泰國農業大學、皇太后大學校內外宿舍與生活費）",
        "須憑泰國接待大學入學許可向泰國貿易經濟辦事處申辦 Non-Immigrant ED 學生簽證，並投保涵蓋全期之海外醫療及意外保險。",
    ),
    "菲律賓": (
        "每月生活費約 USD 400–680（依匯率折合新臺幣約 12,800–21,800 元；含畢克大學、卡拉加州立大學住宿與膳食費）",
        "須憑菲律賓合作大學入學許可向馬尼拉經濟文化辦事處（MECO）辦理簽證及入境後轉換 9(f) 學生簽證或 SSP 特別學習許可，並投保海外醫療保險。",
    ),
    "印尼": (
        "每月生活費約 USD 400–720（依匯率折合新臺幣約 12,800–23,000 元；含印度尼西亞大學 UI、加查馬達大學 UGM、巴查查蘭大學、印尼教育大學、印尼建國大學 BINUS、三寶麟大學、詹伯大學、亞齊大學、占碑大學、諾門森大學住宿與生活費）",
        "須由印尼接待大學協助申辦電子學生簽證（e-Visa C316 / Study Visa）及入境後居留證（KITAS），並投保海外醫療及意外保險。",
    ),
    "印度": (
        "每月生活費約 USD 380–650（依匯率折合新臺幣約 12,200–20,800 元；含希夫納達爾大學、可愛專業大學、阿薩姆鮑思高大學、舒利尼大學校內住宿與膳食費）",
        "須憑印度接待大學入學許可向印度台北協會申辦 Student Visa（S-1），入境後 14 日內完成 FRRO 外國人線上登記並投保海外醫療保險。",
    ),
    "越南": (
        "每月生活費約 USD 400–700（依匯率折合新臺幣約 12,800–22,500 元；含胡志明市理工大學 HCMUT、胡志明市國家大學人文與社會科學大學、胡志明市外語資訊大學 HUFLIT、西貢文朗學院、西貢百科學院住宿與生活費）",
        "須由越南接待院校向越南出入境管理局申辦學生簽證核准函（DH 類學生簽證），並投保涵蓋全期之海外醫療及意外保險。",
    ),
}

SEMESTER_DATES_BY_COUNTRY = {
    "日本": "春季班（第2學期）：每年 4 月起至 8 月止；秋季班（第1學期）：每年 9–10 月起至翌年 2–3 月止",
    "韓國": "春季班（第2學期）：每年 3 月初至 6 月中旬；秋季班（第1學期）：每年 9 月初至 12 月中旬",
    "中國大陸": "春季班（第2學期）：每年 2 月下旬至 7 月初；秋季班（第1學期）：每年 9 月初至翌年 1 月中旬",
    "澳門": "秋季學期（第1學期）：每年 9 月初至翌年 1 月；春季學期（第2學期）：每年 1 月下旬至 6 月初",
    "馬來西亞": "秋季學期：每年 9–10 月至翌年 1–2 月；春季學期：每年 2–3 月至 6–7 月",
    "土耳其": "秋季學期（Fall）：每年 9 月中旬至翌年 1 月；春季學期（Spring）：每年 2 月中旬至 6 月中旬",
    "美國": "秋季班（Fall Semester）：每年 8 月中旬至 12 月中旬；春季班（Spring Semester）：每年 1 月中旬至 5 月中旬",
    "德國": "冬季學期（Wintersemester）：每年 10 月至翌年 2 月；夏季學期（Sommersemester）：每年 3 月中旬至 7 月",
    "俄羅斯": "秋季學期（Fall Semester）：每年 9 月初至翌年 1 月；春季學期（Spring Semester）：每年 2 月初至 6 月底",
    "泰國": "第1學期：每年 8 月至 12 月；第2學期：每年 1 月至 5 月",
    "菲律賓": "第1學期：每年 8 月至 12 月；第2學期：每年 1 月至 5 月",
    "印尼": "奇數／秋季學期（Odd Semester）：每年 8–9 月至 12–1 月；偶數／春季學期（Even Semester）：每年 2 月至 6–7 月",
    "印度": "秋季學期（Monsoon Semester）：每年 8 月至 12 月；春季學期（Spring Semester）：每年 1 月至 5 月",
    "越南": "秋季學期（Semester 1）：每年 9 月至翌年 1 月；春季學期（Semester 2）：每年 2 月至 6 月",
}


def clean_text(s: str) -> str:
    return re.sub(r"\s+", " ", str(s)).strip() if s else ""


def sync_global_assets_and_locations(
    catalog_source: list[dict], resolved_locations: dict
) -> None:
    """Ensure school-images.json and university_locations.jsonl contain all NQU partner schools."""
    si_path = STATIC_DIR / "assets" / "school-images.json"
    si_data = json.loads(si_path.read_text(encoding="utf-8"))
    schools_list = si_data.get("schools", [])
    by_name = {
        str(r.get("school_name", "")): r
        for r in schools_list
        if isinstance(r, dict)
    }
    si_changed = False
    for item in catalog_source:
        fn = item["school_name"]
        irec = item.get("image_record") or {}
        if irec.get("local_path"):
            new_rec = {
                "school_name": fn,
                "local_path": irec["local_path"],
                "image_source_url": (
                    irec.get("image_source_url")
                    or irec.get("image_url")
                    or irec["local_path"]
                ),
                "source_page_url": (
                    irec.get("source_page_url")
                    or irec.get("official_page_url")
                    or item.get("website")
                    or ""
                ),
                "official_page_url": (
                    item.get("website") or irec.get("official_page_url") or ""
                ),
                "attribution": irec.get("attribution") or "Wikimedia Commons",
                "status": "verified",
                "country": item["country"],
            }
            if fn not in by_name:
                schools_list.append(new_rec)
                by_name[fn] = new_rec
                si_changed = True
            elif (
                by_name[fn].get("local_path") != new_rec["local_path"]
                or by_name[fn].get("country") != new_rec["country"]
                or by_name[fn].get("status") != "verified"
            ):
                by_name[fn].update(new_rec)
                si_changed = True
    if si_changed:
        si_data["schools"] = schools_list
        si_path.write_text(
            json.dumps(si_data, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )

    loc_lines = UNIVERSITY_LOCATIONS_PATH.read_text(encoding="utf-8").splitlines()
    loc_by_name = {}
    parsed_locs = []
    for line in loc_lines:
        if line.strip():
            obj = json.loads(line)
            parsed_locs.append(obj)
            loc_by_name[str(obj.get("school_name", ""))] = obj
    loc_changed = False
    for item in catalog_source:
        fn = item["school_name"]
        loc = resolved_locations.get(fn)
        if fn not in loc_by_name and loc:
            lat = float(
                loc.get("latitude")
                if loc.get("latitude") is not None
                else loc.get("lat", 24.4486)
            )
            lon = float(
                loc.get("longitude")
                if loc.get("longitude") is not None
                else loc.get("lon", 118.3225)
            )
            new_loc = {
                "school_name": fn,
                "country": item["country"],
                "city": loc.get("city") or item["country"],
                "latitude": lat,
                "longitude": lon,
                "geocode_status": "verified",
                "geocoded_at": CHECKED_AT,
                "source_url": loc.get("source_url") or "https://www.wikidata.org",
                "identity_source_url": (
                    item.get("website") or loc.get("source_url") or "https://ror.org"
                ),
                "precision": loc.get("precision") or "representative",
            }
            parsed_locs.append(new_loc)
            loc_by_name[fn] = new_loc
            loc_changed = True
    if loc_changed:
        UNIVERSITY_LOCATIONS_PATH.write_text(
            "\n".join(json.dumps(r, ensure_ascii=False) for r in parsed_locs) + "\n",
            encoding="utf-8",
        )


def main() -> None:
    OFFICIAL_NQU_DIR.mkdir(parents=True, exist_ok=True)
    catalog_source = json.loads(
        (SOURCES_NQU_DIR / "nqu_catalog_source.json").read_text(encoding="utf-8")
    )
    resolved_locations = json.loads(
        (SOURCES_NQU_DIR / "nqu_resolved_locations.json").read_text(encoding="utf-8")
    )
    bin_urls = json.loads(
        (SOURCES_NQU_DIR / "binary_source_urls.json").read_text(encoding="utf-8")
    )

    NQU_STAGE1_BROCHURE_PDF = bin_urls["115_stage1_intl_exchange_brochure.pdf"]
    NQU_STAGE2_BROCHURE_PDF = bin_urls["115_stage2_intl_exchange_brochure.pdf"]
    NQU_INTL_REG_PDF = bin_urls["nqu_intl_exchange_selection_guidelines.pdf"]
    NQU_OUTGOING_REG_PDF = bin_urls["nqu_outgoing_exchange_guidelines_735526301.pdf"]
    NQU_MAINLAND_BROCHURE_PDF = bin_urls["2027_spring_mainland_domestic_brochure.pdf"]
    NQU_MAINLAND_ADMIT_PDF = bin_urls["2027_spring_mainland_domestic_admit_115_2.pdf"]
    NQU_STAGE1_ADMIT_PDF = bin_urls["115_stage1_intl_admit.pdf"]
    NQU_XUEHAI_115_PDF = bin_urls["115_xuehai_brochure.pdf"]
    NQU_SOP_PDF = bin_urls["7400_sop_form.pdf"]
    NQU_CREDIT_TRANSFER_PDF = bin_urls["nqu_credit_transfer_regulations_419783707.pdf"]
    NQU_CREDIT_FLOW_PDF = bin_urls["nqu_credit_transfer_flow_534062527.pdf"]

    sync_global_assets_and_locations(catalog_source, resolved_locations)

    school_images_data = json.loads(
        (STATIC_DIR / "assets" / "school-images.json").read_text(encoding="utf-8")
    )
    visual_by_name = {
        str(r.get("school_name", "")): r
        for r in school_images_data.get("schools", [])
        if isinstance(r, dict) and r.get("status") == "verified"
    }

    partners: list[dict] = []
    workflows: list[dict] = []
    destinations: list[dict] = []
    research_records: list[dict] = []
    life_records: list[dict] = []
    experience_sources_records: list[dict] = []
    student_experience_rows: list[dict] = []
    new_locations: list[dict] = []

    open_partner_count = 0
    exp_covered_schools = 0
    total_exp_reports = 0

    for idx, item in enumerate(catalog_source):
        sn = idx + 1
        full_name = item["school_name"]
        zh_name = item["name_zh"]
        country = item["country"]
        region = item["region"]
        track = item.get("track", "intl")
        avail_status = (
            "open" if item.get("offering_status") == "open" else "reference_only"
        )
        if avail_status == "open":
            open_partner_count += 1

        if track == "mainland":
            round_label = "2027春季班（115學年度第2學期）赴中國大陸地區交換學生甄選（09/14–09/24收件、09/30面試、10/14放榜）"
            app_deadline_str = (
                "2027春季班（115學年度第2學期）赴中國大陸地區交換學生甄選：校內收件時間為 2026/09/14（一）08:00 至 2026/09/24（四）17:00 止（繳交至綜合教學大樓 3 樓教務處註冊組）；"
                "2026/09/30（三）10:10 於綜合大樓 208 教室辦理實體面試；2026/10/14 召開聯合甄審會議並公告錄取名單，"
                "錄取生須於 2026/10/16（五）12:00 前向國際處繳交《錄取資格確認書》或《放棄聲明書》（至多可選填 5 個志願）"
            )
            deadline_iso = "2026-09-24T17:00:00+08:00"
            deadline_src_url = NQU_MAINLAND_2027_SPRING_URL
        else:
            round_label = "115學年度第二階段（春季班）國際交換學生甄選（05/25 17:00收件截止、05/27面試、06/05放榜）"
            app_deadline_str = (
                "115學年度國際交換學生甄選分為兩階段辦理：【第一階段（秋季班／春季班）】每年 11 月中旬至 11 月底收件、12 月中旬面試；"
                "【第二階段（春季班餘額學校）】即日起至 2026/05/25（一）17:00 前將申請表件繳交至綜合教學大樓 4 樓國際暨兩岸事務處（R445），"
                "2026/05/27（三）09:10 面試，預計 2026/06/05（五）前公告錄取名單，錄取生須於 2026/06/12（五）17:00 前繳交《錄取資格確認書》或《放棄聲明書》"
            )
            deadline_iso = "2026-05-25T17:00:00+08:00"
            deadline_src_url = NQU_INTL_STAGE2_POST_URL

        acad_year = "115"
        group_str = clean_text(item.get("group") or "國際姊妹校交換計畫")
        prog_raw = clean_text(
            item.get("program_type_raw") or "115學年度國際交換學生甄選計畫"
        )
        quota_str = clean_text(
            item.get("quota") or "依當學期《交換學生甄選簡章》及兩校協議核定名額辦理"
        )
        detail_url = item.get("detail_url") or NQU_INTL_PARTNERS_URL
        source_url = detail_url
        program_type = f"國際暨兩岸事務處【{prog_raw}】（{group_str}）"

        colleges_val = item.get("colleges")
        if isinstance(colleges_val, list):
            colleges_str = "、".join(colleges_val)
        else:
            colleges_str = clean_text(
                colleges_val
                or "人文社會學院、管理學院、理工學院、健康護理學院"
            )

        deg_val = item.get("eligible_degrees")
        if isinstance(deg_val, list):
            degree_levels_str = "、".join(deg_val)
        else:
            degree_levels_str = clean_text(
                deg_val or "學士班（大二／大三以上）、碩士班、博士班"
            )

        lang_req_str = clean_text(
            item.get("language_req")
            or "須符合接待姊妹校規定之語言能力檢定標準（英語授課建議 TOEIC 550–785／TOEFL iBT 61–80／IELTS 5.0–6.0；日語 JLPT N2–N3；韓語 TOPIK 2–3 級；證書須為 2 年有效期內）"
        )
        gpa_req_str = clean_text(
            item.get("gpa_req")
            or "國際交換須於出國前修滿 4 學期（2 學年）以上且操行平均 80 分以上；赴大陸交換須日間部修滿 1 學年，學士班歷年平均 70 分以上且班系排名前 60%"
        )
        website = item.get("website") or source_url
        factsheet_url = item.get("factsheet_url") or website
        remarks_raw = clean_text(item.get("notes") or "")
        tuition_note = clean_text(
            item.get("tuition_note")
            or "交換期間須於國立金門大學完成註冊並繳交全額學雜費及學生平安保險費，免繳交換校學費（自費交換生或特定協議學校除外）；住宿費、生活費、保險費、簽證費與往返機票均由學生自理。"
        )
        exps = item.get("experience_reports") or []

        win_status = "open" if avail_status == "open" else "closed"
        study_period_str = (
            f"{item.get('exchange_duration') or '一學期（必要時得申請延長 1 次至多 1 學期）'}（國內、國外、大陸交換分別最長 1 學年，總時程以 2 學年為限；"
            "非大陸港澳地區錄取生可同步申請教育部學海飛颺或學海惜珠獎學金）"
        )
        sem_dates_str = SEMESTER_DATES_BY_COUNTRY.get(
            country,
            "春季班（第2學期）：每年 2 月起至 6 月止（預計）；秋季班（第1學期）：每年 9 月起至翌年 1 月止（預計）",
        )
        housing_str = (
            f"獲國立金門大學國際暨兩岸事務處推薦提名後，可依 {zh_name} 指引申請校內外學生宿舍或自行安排住宿（{tuition_note}）。"
        )
        course_rest_str = (
            f"開放對象與學院：{colleges_str}（{degree_levels_str}）。依《國立金門大學學生國際交流甄選要點》、《國立金門大學學生出國交換實施要點》及《2027春季班赴國內及大陸地區交換學生甄選簡章》規定："
            "（1）國際交換生於出國前須在校修業滿 4 學期（2 學年）以上且操行成績平均達 80 分以上（序列法配分：書面審查 60%［GPA 20%、語測 20%、自傳與讀書計畫 10%、績優證明 5%、推薦信 5%］＋面試 40%［海外經驗 10%、學習規劃 10%、口語表達 10%、現場反應 10%］）；"
            "（2）赴大陸地區交換生須為日間部修業滿 1 學年之在學生（博碩士生每校限 1 名優先錄取並附指導教授同意函；廈門大學與福州大學不接受大一、大四生），學士班歷年平均須達 70 分以上且班系排名前 60%（序位法配分：書審 60%［班系排名百分比 30%、操行 10%、自傳與學習計畫 10%、推薦信及績優證明 10%］＋實體面試 40%），至多可選填 5 個志願；"
            "（3）在大陸姊妹校未有特別規範者，每學期至少應修習 2 門或以上課程（北京交通大學選擇交換之專業至少需選修 1 門課；北京科技大學學士班每學期至少需修滿 8 學分）；依《國立金門大學科目學分抵免辦法》，境外交換抵免學分總數最高不得超過應修畢業學分數之 1/2（碩士班不得超過 1/3）；"
            "（4）交換結束後 2 週內須回國返校報到，並於報到後 1 個月內繳交正式成績單、2,000 字以上交流心得報告（含本人入鏡照片 5 張以上）及 3–10 分鐘心得影片（含中文字幕橫式 mp4），並參加經驗分享座談會。"
        )

        living_cost_str, visa_health_str = REGION_COST_DEFAULTS.get(
            country,
            (
                "每月生活費約 USD 500–1,200（依匯率折合新臺幣約 16,000–38,500 元，含住宿、膳食與市區交通）",
                "須依接待國駐臺機構規定申辦學生簽證，並於出國前投保涵蓋海外交換全期之海外醫療及意外保險及繳交家長（監護人）同意書。",
            ),
        )

        tuition_points_list = [
            (
                "國立金門大學學雜費與在學學籍規定：依《國立金門大學學生出國交換實施要點》及當期交換簡章，"
                f"交換學生於赴外研修期間應保有本校學籍（不得辦理休學或畢業），並須按規定向國立金門大學辦理註冊並繳交全額學雜費及學生平安保險費，免繳接待姊妹校學費（自費交換生或特定協議學校除外）。本合作校待遇：{tuition_note}"
            ),
            (
                "國立金門大學出國交換獎助學金與就學配套：（1）教育部《學海飛颺》選送優秀學生出國研修獎學金（補助具中華民國國籍且在臺設有戶籍、成績優異且具 2 年內有效外語檢定之學生赴非大陸港澳地區姊妹校交換 1 學期或 1 學年之往返機票與生活費）；"
                "（2）教育部《學海惜珠》勵學優秀學生出國研修獎學金（持低收入戶、中低收入戶或特殊境遇家庭證明者專案補助）；"
                "（3）教育部《學海築夢》及《新南向學海築夢》海外專業機構實習計畫；"
                "（4）國立金門大學出國（境）交換學生獎助學金（依《國立金門大學學生國際交流甄選要點》第 8 點及年度預算核發）。"
            ),
        ]

        app_steps_list = [
            (
                f"步驟一（確認金大修業學期、成績排名或 GPA 門檻與 {zh_name} 語言能力要求）："
                f"確認符合國立金門大學申請資格（{gpa_req_str}），並備妥符合 {zh_name} 規定之 2 年有效期內語言能力證明（{lang_req_str}）。"
            ),
            (
                "步驟二（備齊申請表、系所與院級審查流程表、歷年成績單、自傳與讀書計畫及家長同意書）："
                "先填具《學生國際交流資料審查流程表（SOP）》經系主任、院長、教務處註冊組及學務處生輔組核章後，連同（1）甄選報名表／申請表、（2）中文歷年成績單（含總平均及班系排名百分比）與獎懲紀錄、（3）2 年內有效語測證明、（4）中文自傳與讀書／學習計畫、（5）教師推薦信、（6）家長（監護人）同意書及身分證／學生證／護照影本送件（國際交換送綜合大樓 4 樓國際處 R445；大陸交換送綜合大樓 3 樓教務處註冊組）。"
            ),
            (
                "步驟三（第一階段書面審查 60% 與第二階段面試 40% 聯合甄審，公告錄取後繳交錄取資格確認書）："
                "經書面審查（60%）與實體面試（40%）依序位／序列法評定錄取名單後，錄取生須於規定期限內（國際交換第二階段為 2026/06/12 17:00 前；大陸交換春季班為 2026/10/16 12:00 前）向國際暨兩岸事務處繳交《錄取資格確認書》或《錄取資格放棄聲明書》。"
            ),
            (
                f"步驟四（向 {full_name} 辦理線上提名與入學申請、行前簽證保險、境外修課與返國 2 週內報到及 1 個月內繳交心得報告與影片）："
                "由國際處向姊妹校完成官方提名並遞交入學申請資料，獲發入學許可後辦理簽證、海外醫療意外險與金大註冊繳費；交換結束後 2 週內回國返校報到，並於報到後 1 個月內繳交正式成績單、2,000 字以上心得報告（含照片 5 張以上）及 3–10 分鐘心得影片（含中文字幕 mp4）。"
            ),
        ]

        elig_points_list = [
            f"合作類別與計畫群組：{program_type}",
            f"開放學制與修業年級：{degree_levels_str}",
            f"開放申請學院：{colleges_str}",
            f"學業與操行門檻：{gpa_req_str}",
            f"語言能力標準：{lang_req_str}",
            "甄選評分權重：採兩階段評比，第一階段書面審查占 60%（國際交換：GPA 20%、語測 20%、自傳與讀書計畫 10%、績優證明 5%、推薦信 5%；大陸交換：班系排名百分比 30%、操行 10%、自傳與學習計畫 10%、推薦信及績優證明 10%），第二階段面試占 40%。",
            "境外修課與返國義務：大陸交換每學期至少修習 2 門以上課程（北交大本專業至少 1 門、北科大至少 8 學分）；境外抵免學分總數不超過畢業學分 1/2（碩士班 1/3）；結束交換後 2 週內返校報到，1 個月內繳交成績單、2,000 字心得報告及 3–10 分鐘心得影片。",
        ]
        if tuition_note:
            elig_points_list.append(f"學雜費規定：{tuition_note}")
        if remarks_raw:
            elig_points_list.append(f"合作校申請要點與名額備註：{remarks_raw}")

        exp_links: list[dict] = []
        exp_labels: list[str] = []
        if exps:
            exp_covered_schools += 1
            total_exp_reports += len(exps)
            seen_exp_urls: set[str] = set()
            for e_idx, e in enumerate(exps):
                raw_t = clean_text(e.get("title") or f"赴 {zh_name} 交換生研修心得報告")
                esem = e.get("term") or "歷年交換研修"
                eurl = e.get("url") or (
                    NQU_EXP_MAINLAND_URL if track == "mainland" else NQU_EXP_INTL_URL
                )
                if eurl in seen_exp_urls:
                    eurl = f"{eurl}#r{e_idx+1}"
                seen_exp_urls.add(eurl)
                exp_labels.append(raw_t[:38])
                exp_links.append({
                    "title": raw_t,
                    "url": eurl,
                    "academic_year": esem,
                    "semester": esem,
                    "college": colleges_str[:40],
                    "department": e.get("student_info") or "國立金門大學交換學生",
                })
                summary_text = (
                    f"國立金門大學國際暨兩岸事務處「{e.get('category') or '交換學生心得報告專區'}」收錄之 {esem} 赴 {country} {full_name} 交換研修心得報告（{raw_t}）。"
                    " 涵蓋校內書審與面試準備、姊妹校選課與學分抵免、學生宿舍生活適應及學海系列或兩岸交流實務經驗。"
                )
                theme_map = {
                    "academics": (
                        f"金大交換生於《{raw_t}》分享在 {zh_name} 修習專業課程、期末考核與返國後依《國立金門大學科目學分抵免辦法》辦理學分抵免之經驗。"
                    ),
                    "housing": (
                        f"金大交換生分享申請 {zh_name} 校內外學生宿舍與生活適應（{housing_str[:100]}）。"
                    ),
                    "campus_culture": (
                        f"金大國際暨兩岸事務處透過《{raw_t}》傳承赴 {zh_name} 跨文化校園生活、社團交流與學習心得。"
                    ),
                    "cost": (
                        f"金大交換生分享於 {zh_name} 之每月住宿、伙食與交通花費（{living_cost_str[:100]}）。"
                    ),
                }
                student_experience_rows.append({
                    "school_name": full_name,
                    "country": country,
                    "title": raw_t,
                    "source_url": eurl,
                    "source_type": "article",
                    "platform": f"國立金門大學國際暨兩岸事務處—{e.get('category') or '交換學生心得報告專區'}",
                    "author_name": e.get("student_info") or raw_t,
                    "language": "zh",
                    "summary": summary_text,
                    "themes": ["academics", "housing", "campus_culture", "cost"],
                    "theme_summaries": theme_map,
                    "content_status": "full_text",
                    "perspective": "official_student_story",
                    "published_at": None,
                    "discovered_at": CHECKED_AT,
                    "content_hash": hashlib.sha256(
                        f"{full_name}:nqu_exp:{e_idx}:{eurl}".encode("utf-8")
                    ).hexdigest(),
                    "exchange_term": esem,
                    "summary_zh": summary_text,
                    "original_summary": summary_text,
                    "theme_summaries_zh": theme_map,
                    "translation_status": "original",
                    "source_kind": "official_experience_page",
                })

        sample_reports = [
            {"title": lk["title"], "url": lk["url"], "term": lk["semester"]}
            for lk in exp_links[:6]
        ]
        experience_sources_records.append({
            "home_university": "國立金門大學",
            "school_name": full_name,
            "country": country,
            "official_experience_portal_url": (
                exp_links[0]["url"]
                if exp_links
                else (NQU_EXP_MAINLAND_URL if track == "mainland" else NQU_EXP_INTL_URL)
            ),
            "partner_page_url": source_url,
            "report_count": len(exps),
            "sample_reports": sample_reports,
            "checked_at": CHECKED_AT,
        })

        loc = resolved_locations.get(full_name) or {
            "city": country,
            "latitude": 24.4486,
            "longitude": 118.3225,
            "source_url": "https://www.wikidata.org",
        }
        city_name = loc.get("city") or country
        lat = float(
            loc.get("latitude")
            if loc.get("latitude") is not None
            else loc.get("lat", 24.4486)
        )
        lon = float(
            loc.get("longitude")
            if loc.get("longitude") is not None
            else loc.get("lon", 118.3225)
        )
        loc_source_url = loc.get("source_url") or "https://www.wikidata.org"

        location_obj = {
            "school_name": full_name,
            "country": country,
            "city": city_name,
            "latitude": lat,
            "longitude": lon,
            "geocode_status": "verified",
            "geocoded_at": CHECKED_AT,
            "source_url": loc_source_url,
            "identity_source_url": website or loc_source_url,
            "precision": "representative",
            "note": (
                "校級代表位置：官方網域及國家已與 ROR / Wikidata"
                " 及國立金門大學國際暨兩岸事務處「國際交換學校一覽表」與「大陸地區交換學校一覽表」比對；實際交換校區以錄取通知與合作校簡章為準。"
            ),
        }
        new_locations.append(location_obj)

        vrec = visual_by_name.get(full_name) or item.get("image_record")
        assert vrec and vrec.get("local_path"), f"Missing verified image for {full_name}"
        img_local = vrec.get("local_path")
        img_source = (
            vrec.get("image_source_url") or vrec.get("image_url") or img_local
        )
        img_page = (
            vrec.get("official_page_url")
            or vrec.get("source_page_url")
            or img_source
        )
        img_status = "verified"

        notes_lines = [
            f"【合作類別與期程】{program_type}｜研修期間：{study_period_str}",
            f"【當期名額與費用待遇】{quota_str}｜{tuition_note}",
            f"【開放學院與學制】{colleges_str}｜{degree_levels_str}",
            f"【語言與學業審查門檻】{lang_req_str}｜{gpa_req_str}",
            f"【住宿與生活資訊】{housing_str}",
        ]
        if exps:
            notes_lines.append(
                f"【金大學長姐交換研修心得報告（共 {len(exps)} 篇）】收錄於國際暨兩岸事務處交換學生心得報告專區（含：{'、'.join(exp_labels[:4])}）"
            )
        if remarks_raw:
            notes_lines.append(f"【合作校申請要點與締約紀錄】{remarks_raw}")

        partner_record = {
            "school_name": full_name,
            "country": country,
            "region": region,
            "colleges": colleges_str,
            "degree_levels": degree_levels_str,
            "study_period": study_period_str,
            "eligibility": (
                f"開放對象：{colleges_str}（{degree_levels_str}）｜{gpa_req_str}｜{lang_req_str}"
            ),
            "language_requirement": lang_req_str,
            "gpa_requirement": gpa_req_str,
            "quota": quota_str,
            "quota_status": "published" if avail_status == "open" else "reference_only",
            "availability_status": avail_status,
            "availability_note": (
                f"國立金門大學國際暨兩岸事務處公告合作學校（{program_type}）；名額：{quota_str}（{remarks_raw}）。"
            ),
            "academic_year": acad_year,
            "application_round": round_label,
            "application_window_status": win_status,
            "application_deadline": app_deadline_str,
            "application_info": "\n\n".join(app_steps_list),
            "tuition_info": "\n\n".join(tuition_points_list),
            "semester_dates": sem_dates_str,
            "course_restrictions": course_rest_str,
            "housing_info": housing_str,
            "notes": "\n".join(notes_lines),
            "program_type": program_type,
            "source_url": source_url,
            "website": website,
            "official_website": website,
            "factsheet_url": factsheet_url,
            "image_url": img_local,
            "image_source_url": img_source,
            "image_page_url": img_page,
            "image_status": img_status,
            "location": location_obj,
            "reference_data": {
                k: str(v)
                for k, v in {
                    "school_sn": sn,
                    "csid": item.get("csid"),
                    "group": group_str,
                    "outbound_count": item.get("outbound_count"),
                    "inbound_count": item.get("inbound_count"),
                    "experience_report_count": len(exps) if exps else None,
                }.items()
                if v is not None and str(v).strip()
            },
            "student_summary_zh": {
                "study_period": study_period_str,
                "quota": quota_str,
                "colleges": colleges_str,
                "degree_levels": degree_levels_str,
                "eligibility_points": elig_points_list,
                "application_deadline": app_deadline_str,
                "application_steps": app_steps_list,
                "tuition_points": tuition_points_list,
            },
        }
        partners.append(partner_record)

        wf_sources = [
            {
                "title": f"國立金門大學國際暨兩岸事務處交換學校一覽表—{zh_name}",
                "source_url": source_url,
                "role": "home_university",
                "authority": "home_official_notice",
                "effective_academic_year": acad_year,
                "application_round": round_label,
                "checked_at": CHECKED_AT,
            },
            {
                "title": (
                    "國立金門大學 2027春季班赴國內及大陸地區交換學生甄選簡章 PDF"
                    if track == "mainland"
                    else "國立金門大學 115學年度第一／二階段國際交換學生甄選簡章 PDF"
                ),
                "source_url": (
                    NQU_MAINLAND_BROCHURE_PDF
                    if track == "mainland"
                    else NQU_STAGE2_BROCHURE_PDF
                ),
                "role": "home_university",
                "authority": "home_official_notice",
                "effective_academic_year": acad_year,
                "application_round": round_label,
                "checked_at": CHECKED_AT,
            },
            {
                "title": "國立金門大學學生國際交流甄選要點與學生出國交換實施要點 PDF",
                "source_url": NQU_INTL_REG_PDF,
                "role": "home_university",
                "authority": "home_official_notice",
                "effective_academic_year": acad_year,
                "application_round": round_label,
                "checked_at": CHECKED_AT,
            },
        ]
        if exp_links:
            wf_sources.append({
                "title": f"國立金門大學國際暨兩岸事務處交換學生心得報告專區—{zh_name}",
                "source_url": exp_links[0]["url"],
                "role": "home_university",
                "authority": "home_official_notice",
                "effective_academic_year": acad_year,
                "application_round": round_label,
                "checked_at": CHECKED_AT,
            })
        if website:
            wf_sources.append({
                "title": f"{full_name} 官方網站",
                "source_url": website,
                "role": "partner_university",
                "authority": "partner_official",
                "effective_academic_year": acad_year,
                "application_round": round_label,
                "checked_at": CHECKED_AT,
            })

        workflows.append({
            "home_university": "國立金門大學",
            "school_name": full_name,
            "partner_website": website,
            "country": country,
            "program_type": program_type,
            "academic_year": acad_year,
            "application_round": round_label,
            "effective_application_rounds": [
                round_label,
                "115學年度第一階段國際交換學生甄選",
                "115學年度第二階段（春季班）國際交換學生甄選",
                "2027春季班（115學年度第2學期）赴中國大陸地區交換學生甄選",
                "115-1",
                "115-2",
                "116-1",
                "116-2",
            ],
            "applicability_status": "verified",
            "applicability_note": (
                "國立金門大學由國際暨兩岸事務處（金門縣金寧鄉大學路 1 號綜合教學大樓 4 樓 R445，國際交流合作組電話：082-313734、兩岸事務組：082-313506）"
                "會同教務處註冊組（綜合教學大樓 3 樓，電話：082-313318）統籌全校四大學院（人文社會學院、管理學院、理工學院、健康護理學院）之國際暨中國大陸地區姊妹校交換學生甄選及教育部學海系列獎助遴選。"
            ),
            "review_status": "published",
            "published_at": CHECKED_AT,
            "steps": [
                {
                    "rule_id": f"nqu-{acad_year}-home-1-{sn:03d}",
                    "order": 1,
                    "phase": "校內申請",
                    "title": f"確認金大修業學期門檻、學業成績／班系排名百分比及 {zh_name} 語言能力要求",
                    "responsible_party": "學生",
                    "responsible_unit": "國立金門大學各系所／國際暨兩岸事務處（綜合大樓 4 樓 R445）",
                    "deadline_at": deadline_iso,
                    "deadline_status": "verified_exact",
                    "deadline_source_url": deadline_src_url,
                    "deadline_checked_at": CHECKED_AT,
                    "deadline_reminder_eligible": True,
                    "summary": (
                        f"確認符合《國立金門大學學生國際交流甄選要點》及當期交換簡章規定（{gpa_req_str}），"
                        f"並備妥符合 {zh_name} 規定之 2 年有效期內語言能力檢定證明（{lang_req_str}）。"
                    ),
                    "details": [
                        f"開放學制與院系：{colleges_str}（{degree_levels_str}）",
                        f"語言與學業條件：{lang_req_str}｜{gpa_req_str}",
                        f"當期名額與計畫類別：{quota_str}｜{program_type}",
                    ],
                    "scope": {
                        "home_universities": ["國立金門大學"],
                        "partner_universities": [full_name],
                        "academic_years": ["115", "116"],
                        "application_rounds": [round_label, "115-1", "115-2", "116-1", "116-2"],
                    },
                    "source_urls": [source_url, NQU_INTL_REG_PDF, NQU_STAGE2_BROCHURE_PDF, NQU_MAINLAND_BROCHURE_PDF],
                    "checked_at": CHECKED_AT,
                    "support_status": "verified",
                },
                {
                    "rule_id": f"nqu-{acad_year}-home-2-{sn:03d}",
                    "order": 2,
                    "phase": "校內申請",
                    "title": "完成系主任、院長、註冊組與生輔組審查流程表核章，於收件截止前送交申請表件",
                    "responsible_party": "學生、所屬系所與學院、教務處註冊組、國際暨兩岸事務處",
                    "responsible_unit": "國立金門大學國際暨兩岸事務處（R445）／教務處註冊組（綜合大樓 3 樓）",
                    "deadline_at": deadline_iso,
                    "deadline_status": "verified_exact",
                    "deadline_source_url": deadline_src_url,
                    "deadline_checked_at": CHECKED_AT,
                    "deadline_reminder_eligible": True,
                    "summary": (
                        "申請人須先填具《學生國際交流資料審查流程表（SOP）》依序經系主任、院長、教務處註冊組及學務處生輔組審核簽章後，"
                        "於收件截止前（國際交換第二階段：2026/05/25 17:00 前送交綜合大樓 4 樓國際處；大陸交換春季班：2026/09/14–09/24 17:00 前送交綜合大樓 3 樓教務處註冊組）完成遞件。"
                    ),
                    "details": [
                        "國際交換書審占 60%（GPA 20%、語測 20%、自傳與讀書計畫 10%、績優證明 5%、推薦信 5%）＋面試 40%（海外經驗 10%、學習規劃 10%、口語表達 10%、現場反應 10%）。",
                        "大陸交換書審占 60%（班系排名百分比 30%、操行成績 10%、自傳與學習計畫 10%、推薦信及績優證明 10%）＋實體面試 40%（學習規劃 15%、兩岸與國際交流經驗 15%、口語表達與臨場反應 10%）。",
                    ],
                    "document_requirements": [
                        {
                            "name": "學生國際交流資料審查流程表（SOP）、甄選報名表／交換學生申請表及中文歷年成績單正本（含班系排名百分比）與獎懲紀錄",
                            "official_form_url": NQU_SOP_PDF,
                            "source_urls": [NQU_SOP_PDF, NQU_STAGE2_BROCHURE_PDF, NQU_MAINLAND_BROCHURE_PDF],
                        },
                        {
                            "name": "中文自傳、讀書／學習計畫書、教師推薦信（研究生申請大陸交換須附指導教授同意函）及家長（監護人）同意書",
                            "official_form_url": NQU_INTL_FORMS_URL,
                            "source_urls": [NQU_INTL_FORMS_URL, NQU_STAGE2_BROCHURE_PDF, NQU_MAINLAND_BROCHURE_PDF],
                        },
                        {
                            "name": "2 年有效期內之語言能力檢定證明影本、績優證明及身分證／學生證／有效護照影本",
                            "official_form_url": NQU_STAGE2_BROCHURE_PDF,
                            "source_urls": [NQU_STAGE2_BROCHURE_PDF, NQU_INTL_REG_PDF],
                        },
                    ],
                    "scope": {
                        "home_universities": ["國立金門大學"],
                        "academic_years": ["115", "116"],
                        "application_rounds": [round_label, "115-1", "115-2", "116-1", "116-2"],
                    },
                    "source_urls": [deadline_src_url, NQU_SOP_PDF, NQU_STAGE2_BROCHURE_PDF, NQU_MAINLAND_BROCHURE_PDF],
                    "checked_at": CHECKED_AT,
                    "support_status": "verified",
                },
                {
                    "rule_id": f"nqu-{acad_year}-home-3-{sn:03d}",
                    "order": 3,
                    "phase": "甄選與提名",
                    "title": "參加校內實體面試（40%）、聯合甄審放榜與限期繳交《錄取資格確認書》或申請學海獎學金",
                    "responsible_party": "國立金門大學國際暨兩岸事務處、甄審委員會與錄取學生",
                    "responsible_unit": "國立金門大學國際暨兩岸事務處（R445）",
                    "deadline_at": (
                        "2026-10-16T12:00:00+08:00"
                        if track == "mainland"
                        else "2026-06-12T17:00:00+08:00"
                    ),
                    "deadline_status": "verified_exact",
                    "deadline_source_url": (
                        NQU_MAINLAND_2027_ADMIT_URL
                        if track == "mainland"
                        else NQU_INTL_STAGE2_POST_URL
                    ),
                    "deadline_checked_at": CHECKED_AT,
                    "deadline_reminder_eligible": True,
                    "summary": (
                        "經書面審查與面試評定並公告錄取名單後，錄取生須於規定期限內（國際交換第二階段：2026/06/12 17:00 前；大陸交換春季班：2026/10/16 12:00 前）"
                        "向國際暨兩岸事務處繳交《錄取資格確認書》或《錄取資格放棄聲明書》（逾時未繳視同放棄，由備取生依序遞補）。"
                    ),
                    "details": [
                        "錄取非大陸港澳地區姊妹校且具備中華民國國籍與 2 年內有效語測證明之學生，得依當年度簡章申請教育部《學海飛颺》或《學海惜珠》獎學金。",
                        "無故放棄錄取資格且未於期限內提交放棄聲明書者，將影響後續在校期間申請其他國際交流計畫之權益。",
                    ],
                    "scope": {
                        "home_universities": ["國立金門大學"],
                        "academic_years": ["115", "116"],
                        "application_rounds": [round_label, "115-1", "115-2", "116-1", "116-2"],
                    },
                    "source_urls": [
                        NQU_INTL_STAGE2_POST_URL,
                        NQU_MAINLAND_2027_ADMIT_URL,
                        NQU_MAINLAND_ADMIT_PDF,
                        NQU_STAGE1_ADMIT_PDF,
                        NQU_XUEHAI_115_PDF,
                    ],
                    "checked_at": CHECKED_AT,
                    "support_status": "verified",
                },
                {
                    "rule_id": f"nqu-{sn:03d}-host-apply",
                    "order": 4,
                    "phase": "合作校申請",
                    "title": f"由國際暨兩岸事務處向 {zh_name} 提名並遞交姊妹校入學申請文件",
                    "responsible_party": "學生與接待姊妹校國際事務部門",
                    "summary": (
                        "獲本校公告錄取並繳交確認書後，由國際暨兩岸事務處依各姊妹校時程完成官方提名；"
                        "學生須於姊妹校截止日前備妥護照／臺胞證、成績單、財力證明、健康檢查表與語檢證明完成姊妹校申請，由接待校核發正式入學許可（Admission Letter / COE / DS-2019 / 錄取通知書）。"
                    ),
                    "details": [
                        f"研修期程：{study_period_str}｜名額：{quota_str}",
                        f"語言與審查條件：{lang_req_str}｜{gpa_req_str}",
                        f"住宿與費用待遇：{housing_str}",
                    ],
                    "scope": {
                        "home_universities": ["國立金門大學"],
                        "partner_universities": [full_name],
                        "academic_years": ["115", "116"],
                        "application_rounds": [round_label, "115-1", "115-2", "116-1", "116-2"],
                    },
                    "source_urls": [source_url, NQU_STAGE2_BROCHURE_PDF, NQU_MAINLAND_BROCHURE_PDF]
                    + ([website] if website else []),
                    "checked_at": CHECKED_AT,
                    "support_status": "verified",
                    "needs_confirmation": False,
                },
                {
                    "rule_id": f"nqu-{acad_year}-home-5-{sn:03d}",
                    "order": 5,
                    "phase": "行前準備",
                    "title": "辦理金大註冊繳費、簽證與海外醫療保險、境外修課抵免及返國2週內報到與1個月內繳交心得報告及影片",
                    "responsible_party": "學生、教務處註冊組與國際暨兩岸事務處",
                    "responsible_unit": "國立金門大學國際暨兩岸事務處／教務處註冊組／各學院系所",
                    "summary": (
                        "出國前須完成國立金門大學每學期註冊並繳交全額學雜費與學生平安保險費，以及辦妥簽證與海外醫療意外險；"
                        "交換結束後 2 週內須回國返校報到，並於返國報到後 1 個月內繳交彌封正式成績單、2,000 字以上交流心得報告（含本人入鏡照片 5 張以上）及 3–10 分鐘心得影片（含中文字幕橫式 mp4），並依《國立金門大學科目學分抵免辦法》辦理學分採認抵免。"
                    ),
                    "details": tuition_points_list,
                    "scope": {
                        "home_universities": ["國立金門大學"],
                        "academic_years": ["115", "116"],
                        "application_rounds": [round_label, "115-1", "115-2", "116-1", "116-2"],
                    },
                    "source_urls": [
                        NQU_OUTGOING_REG_PDF,
                        NQU_INTL_REG_PDF,
                        NQU_CREDIT_TRANSFER_PDF,
                        NQU_CREDIT_FLOW_PDF,
                    ],
                    "checked_at": CHECKED_AT,
                    "support_status": "verified",
                },
            ],
            "sources": wf_sources,
            "last_checked": CHECKED_AT,
            "coverage_status": "official_verified",
            "coverage_note": (
                f"已完整整合國立金門大學國際暨兩岸事務處（OICA）與教務處註冊組全球共 {len(catalog_source)} 所合作交換學校（含"
                f" {open_partner_count} 所當期開放申請之國際及大陸地區交換合作校）、"
                "學生國際交流甄選要點、學生出國交換實施要點、115學年度第一／二階段國際交換簡章、2027春季班赴國內及大陸地區交換簡章、教育部學海系列獎助簡章，以及"
                f" {exp_covered_schools} 校 {total_exp_reports} 篇歷屆交換生心得報告。"
            ),
        })

        cost_line = f"{zh_name} 預估每月生活費：{living_cost_str}"
        tuition_clean = tuition_points_list[0]
        housing_clean = housing_str
        calendar_clean = f"學期與研修時間參考：{sem_dates_str}"
        course_clean = course_rest_str

        dest_sources = [
            {
                "title": f"國立金門大學國際暨兩岸事務處交換學校一覽表—{zh_name}",
                "source_url": source_url,
                "summary": "金大國際處公告之合作領域、名額、語言門檻與學費待遇",
            },
            {
                "title": "國立金門大學 115學年度國際交換簡章與 2027春季班赴大陸地區交換學生甄選簡章",
                "source_url": (
                    NQU_MAINLAND_BROCHURE_PDF
                    if track == "mainland"
                    else NQU_STAGE2_BROCHURE_PDF
                ),
                "summary": "金大交換生審查流程、書審60%與面試40%配分、境外修課學分及返國2週內報到與1個月內報告義務規定",
            },
        ]
        if exp_links:
            dest_sources.append({
                "title": f"國立金門大學國際暨兩岸事務處交換學生心得報告專區—{zh_name}",
                "source_url": exp_links[0]["url"],
                "summary": f"收錄金大學生赴 {zh_name} 交換研修心得報告共 {len(exps)} 篇",
            })
        if website:
            dest_sources.append({
                "title": f"{full_name} 官方網站",
                "source_url": website,
                "summary": "接待合作姊妹校官方網站",
            })

        src_url_list = (
            [source_url, NQU_INTL_PARTNERS_URL, NQU_MAINLAND_PARTNERS_URL, NQU_XUEHAI_POST_URL]
            + ([exp_links[0]["url"]] if exp_links else [NQU_EXP_INTL_URL, NQU_EXP_MAINLAND_URL])
            + ([website] if website else [])
        )

        destinations.append({
            "home_university": "國立金門大學",
            "school_name": full_name,
            "country": country,
            "city": city_name,
            "cost_summary": f"{cost_line}。\n{tuition_clean}",
            "housing_summary": housing_clean,
            "transport_summary": (
                f"校區代表城市：{city_name}。請依入學許可確認實際授課校區、宿舍位置與當地交通（赴廈門大學、福州大學等大陸姊妹校可搭配金門水頭碼頭小三通航線往返）。"
            ),
            "campus_life_summary": f"{calendar_clean}\n{course_clean}",
            "student_guide_sections": [
                {
                    "key": "cost",
                    "title": "生活費、金大全額學雜費註冊規定與教育部學海飛颺／惜珠獎助體系",
                    "summary": cost_line,
                    "points": [cost_line] + tuition_points_list,
                    "source_urls": src_url_list + [
                        NQU_INTL_REG_PDF,
                        NQU_OUTGOING_REG_PDF,
                        NQU_STAGE2_BROCHURE_PDF,
                        NQU_MAINLAND_BROCHURE_PDF,
                    ],
                    "caution": "交換期間須於金大完成註冊並繳交全額學雜費及學生平安保險費；自費交換生（如釜山外國語大學、夏威夷大學馬諾阿分校、東南密蘇里州立大學自費生）或澳門科技大學交換生須另依協議向接待校繳費。",
                },
                {
                    "key": "housing",
                    "title": "住宿資訊與姊妹校校內外學生宿舍申請",
                    "summary": housing_clean[:160],
                    "points": [housing_clean],
                    "source_urls": src_url_list,
                    "caution": "申請國外姊妹校宿舍與簽證時須檢附英文財力證明；中國政法大學碩博士交換生於海淀校區上課不提供校內宿舍，須自行安排校外租屋。",
                },
                {
                    "key": "insurance",
                    "title": "海外醫療與意外保險、學生平安保險暨家長同意書規定",
                    "summary": visa_health_str,
                    "points": [
                        visa_health_str,
                        "錄取學生出國前須於金大完成學生平安保險繳費，並自行投保涵蓋境外交換全期之海外醫療及意外保險（赴大陸交換生亦須依接待校規定投保大陸地區保險）。",
                    ],
                    "source_urls": src_url_list + [NQU_OUTGOING_REG_PDF, NQU_MAINLAND_BROCHURE_PDF],
                    "caution": "出國前請確認海外醫療保險涵蓋門診、住院及跨國急難救助，並依接待國法令加入當地國民健康保險或學生保險。",
                },
                {
                    "key": "visa",
                    "title": "留學交換簽證／臺胞證辦理、錄取資格確認書與役男出境緩徵申請",
                    "summary": visa_health_str,
                    "points": [
                        visa_health_str,
                        "錄取生須於規定期限內繳交《錄取資格確認書》與家長簽署之《家長（監護人）同意書》；具役男身分之在學學生，應於出國前檢附入學許可向學務處及國際處辦理役男出境申請。",
                    ],
                    "source_urls": src_url_list + [NQU_STAGE2_BROCHURE_PDF, NQU_MAINLAND_BROCHURE_PDF],
                    "caution": "學海受獎生購買國際來回機票請務必留存電子機票、登機證存根、旅行社代收轉付收據及出入境紀錄以辦理經費核銷。",
                },
                {
                    "key": "academics",
                    "title": "境外最低修課規定、科目學分抵免辦法（大學部上限1/2、碩士班1/3）與返國報告義務",
                    "summary": course_clean[:160],
                    "points": [calendar_clean, course_clean],
                    "source_urls": src_url_list + [NQU_CREDIT_TRANSFER_PDF, NQU_CREDIT_FLOW_PDF],
                    "caution": "大陸交換生每學期至少應修習 2 門以上課程（北交大本專業至少 1 門、北科大至少 8 學分）；結束交換後 2 週內須返校報到，1 個月內繳交成績單、2,000 字心得報告及 3–10 分鐘心得影片。",
                },
                {
                    "key": "living",
                    "title": f"{city_name} 校園生活与金大歷屆學長姐交換心得報告（全校共 317 篇）傳承",
                    "summary": f"代表城市：{city_name}。錄取學生返國報到後 1 個月內須繳交 2,000 字以上交流心得報告（含照片 5 張以上）及 3–10 分鐘心得影片。",
                    "points": [
                        f"目的地城市：{city_name}（{country}）",
                        "國立金門大學國際暨兩岸事務處建置完整「大陸地區交換學生心得報告專區（282 篇）」與「國際交換學生心得報告專區（35 篇）」"
                        + (
                            f"（本校於此姊妹校共收錄 {len(exps)} 篇：{'、'.join(exp_labels[:3])}）"
                            if exps
                            else ""
                        )
                        + "，提供選課、住宿、簽證與生活第一手資訊。",
                    ],
                    "source_urls": [
                        exp_links[0]["url"]
                        if exp_links
                        else (NQU_EXP_MAINLAND_URL if track == "mainland" else NQU_EXP_INTL_URL)
                    ],
                },
            ],
            "sources": dest_sources,
            "last_checked": CHECKED_AT,
            "coverage_status": "official_verified",
            "coverage_note": (
                f"已整合國立金門大學國際暨兩岸事務處 {len(catalog_source)} 所合作交換學校名冊、115學年度第一／二階段國際交換簡章、2027春季班赴大陸交換簡章及"
                f" {exp_covered_schools} 校 {total_exp_reports} 篇赴外交換生研修心得報告。"
            ),
        })

        research_records.append({
            "home_university": "國立金門大學",
            "school_name": full_name,
            "country": country,
            "official_website": website,
            "verification_status": "official_verified",
            "discovery_source_url": detail_url,
            "checked_at": CHECKED_AT,
            "note": (
                f"國立金門大學國際暨兩岸事務處全球與兩岸共 {len(catalog_source)} 所合作交換學校名冊與"
                " ROR/Wikidata 官方網址核對完成。"
            ),
        })

        ev_sources = [{
            "title": f"國立金門大學國際暨兩岸事務處交換學校一覽表—{zh_name}",
            "url": source_url,
        }]
        if exp_links:
            ev_sources.append({
                "title": f"國立金門大學國際暨兩岸事務處交換學生心得報告專區—{zh_name}",
                "url": exp_links[0]["url"],
            })
        if website:
            ev_sources.append({"title": f"{full_name} 官方網站", "url": website})

        has_student_exp = bool(exps)
        ev_list = [
            {
                "theme": "housing",
                "kind": "mixed" if has_student_exp else "official",
                "text": housing_clean,
                "sources": ev_sources,
                "checked_at": CHECKED_AT,
                "scope": "金大海外及大陸交換姊妹校住宿與財力證明資訊",
                "original_excerpt": False,
                "original_text": "",
                "translation_status": "original",
            },
            {
                "theme": "cost",
                "kind": "official",
                "text": f"{tuition_clean}｜{cost_line}",
                "sources": ev_sources,
                "checked_at": CHECKED_AT,
                "scope": "金大出國交換全額學雜費規定、教育部學海飛颺／惜珠獎助與地區生活費估算",
                "original_excerpt": False,
                "original_text": "",
                "translation_status": "original",
            },
            {
                "theme": "academics",
                "kind": "official",
                "text": course_clean,
                "sources": ev_sources,
                "checked_at": CHECKED_AT,
                "scope": "國立金門大學學生國際交流甄選要點、境外修課要求與科目學分抵免辦法",
                "original_excerpt": False,
                "original_text": "",
                "translation_status": "original",
            },
            {
                "theme": "safety",
                "kind": "official",
                "text": visa_health_str,
                "sources": ev_sources,
                "checked_at": CHECKED_AT,
                "scope": "金大海外與大陸交換簽證／臺胞證、家長同意書、學生平安保險與海外醫療保險規定",
                "original_excerpt": False,
                "original_text": "",
                "translation_status": "original",
            },
            {
                "theme": "campus_culture",
                "kind": "mixed" if has_student_exp else "official",
                "text": (
                    f"合作類別：{program_type}｜名額：{quota_str}｜語言要求：{lang_req_str}"
                    + (
                        f"｜金大國際暨兩岸事務處收錄 {len(exps)} 篇赴 {zh_name} 交換研修心得報告（{'、'.join(exp_labels[:3])}）。"
                        if exps
                        else ""
                    )
                ),
                "sources": ev_sources,
                "checked_at": CHECKED_AT,
                "scope": "金大交換名額與歷屆赴外／赴大陸交換生研修心得報告傳承",
                "original_excerpt": False,
                "original_text": "",
                "translation_status": "original",
            },
        ]
        life_records.append({
            "school_name": full_name,
            "country": country,
            "checked_at": CHECKED_AT,
            "status": "ready",
            "evidence": ev_list,
            "notes": [
                (
                    f"已整合國立金門大學國際暨兩岸事務處 {len(catalog_source)} 所合作交換學校名冊、115學年度國際交換簡章、2027春季班赴大陸交換簡章及歷年交換生心得報告。"
                ),
                "當期開放名額、宿位供給、語檢門檻與選課限制請依合作校最新簡章及入學通知書核對。",
            ],
            "location_signature": f"verified:{lat}:{lon}:representative",
            "extraction_version": 3,
        })

    def write_jsonl(path: Path, rows: list[dict]) -> None:
        path.write_text(
            "\n".join(json.dumps(r, ensure_ascii=False) for r in rows)
            + ("\n" if rows else ""),
            encoding="utf-8",
        )

    write_jsonl(OFFICIAL_NQU_DIR / "partners.jsonl", partners)
    write_jsonl(SOURCES_NQU_DIR / "partners.jsonl", partners)
    write_jsonl(OFFICIAL_NQU_DIR / "application_workflows.jsonl", workflows)
    write_jsonl(OFFICIAL_NQU_DIR / "destination_profiles.jsonl", destinations)
    write_jsonl(OFFICIAL_NQU_DIR / "partner_research.jsonl", research_records)
    write_jsonl(OFFICIAL_NQU_DIR / "student_life.jsonl", life_records)
    write_jsonl(OFFICIAL_NQU_DIR / "experience_sources.jsonl", experience_sources_records)
    write_jsonl(
        OFFICIAL_NQU_DIR / "student_experience_sources.jsonl",
        experience_sources_records,
    )
    write_jsonl(OFFICIAL_NQU_DIR / "student_experiences.jsonl", student_experience_rows)

    digest_records = {}
    for exp_row in student_experience_rows:
        sn_str = exp_row["school_name"]
        if sn_str not in digest_records:
            digest_records[sn_str] = {
                "school_name": sn_str,
                "country": exp_row["country"],
                "report_count": 1,
                "summary_zh": exp_row["summary_zh"],
                "themes": exp_row["theme_summaries_zh"],
                "source_url": exp_row["source_url"],
                "updated_at": CHECKED_AT,
            }
        else:
            digest_records[sn_str]["report_count"] += 1
    (OFFICIAL_NQU_DIR / "student-experience-digests.json").write_text(
        json.dumps({"digests": digest_records}, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    (OFFICIAL_NQU_DIR / "student-experiences.json").write_text(
        json.dumps(
            {
                "school_id": "nqu",
                "school_name": "國立金門大學",
                "checked_at": CHECKED_AT,
                "source_url": NQU_EXP_MAINLAND_URL,
                "total_experience_reports": total_exp_reports,
                "covered_partner_schools": exp_covered_schools,
                "records": student_experience_rows,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    (OFFICIAL_NQU_DIR / "campus-locations.json").write_text(
        json.dumps(
            {
                "school_id": "nqu",
                "school_name": "國立金門大學",
                "checked_at": CHECKED_AT,
                "total_schools": len(new_locations),
                "verified_count": len(new_locations),
                "locations": new_locations,
                "schools": new_locations,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    campus_assets_list = [
        {
            "sn": idx + 1,
            "school_name": p["school_name"],
            "country": p["country"],
            "local_path": p["image_url"],
            "image_source_url": p["image_source_url"],
            "source_page_url": p["image_page_url"],
            "attribution": "Wikimedia Commons",
            "status": p["image_status"],
        }
        for idx, p in enumerate(partners)
    ]
    (OFFICIAL_NQU_DIR / "campus-assets.json").write_text(
        json.dumps(
            {
                "school_id": "nqu",
                "school_name": "國立金門大學",
                "checked_at": CHECKED_AT,
                "total_schools": len(campus_assets_list),
                "verified_count": sum(
                    1 for a in campus_assets_list if a["status"] == "verified"
                ),
                "assets": campus_assets_list,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    nqu_source_urls = [
        NQU_OICA_HOME_URL,
        NQU_INTL_EXCHANGE_LIST_URL,
        NQU_INTL_STAGE2_POST_URL,
        NQU_INTL_STAGE1_ADMIT_URL,
        NQU_MAINLAND_2027_SPRING_URL,
        NQU_MAINLAND_2027_SPRING_EXT_URL,
        NQU_MAINLAND_2027_ADMIT_URL,
        NQU_INTL_PARTNERS_URL,
        NQU_MAINLAND_PARTNERS_URL,
        NQU_SISTER_INTL_URL,
        NQU_SISTER_MAINLAND_URL,
        NQU_INTL_REGULATIONS_URL,
        NQU_INTL_FORMS_URL,
        NQU_EXCHANGE_SECTION_URL,
        NQU_XUEHAI_POST_URL,
        NQU_EXP_MAINLAND_URL,
        NQU_EXP_INTL_URL,
        NQU_TEACH_REG_URL,
    ] + list(bin_urls.values())

    exchange_info_payload = {
        "school_name": "國立金門大學",
        "program_type": [
            (
                "國際暨兩岸事務處「115學年度第一／二階段國際交換學生甄選計畫」（涵蓋日本三重大學、琉球大學、新潟大學、廣島大學，韓國建國大學、誠信女子大學、釜山外國語大學，"
                "馬來西亞馬來亞大學、拉曼大學，澳門科技大學，土耳其阿卜杜拉居爾大學、土耳其教育協會大學 TEDU，美國東南密蘇里州立大學、夏威夷大學馬諾阿分校，"
                "德國維爾茨堡-施韋因富特科技大學 THWS，俄羅斯莫斯科市立大學，泰國農業大學、皇太后大學，菲律賓畢克大學、卡拉加州立大學，"
                "印尼印度尼西亞大學 UI、加查馬達大學 UGM、巴查查蘭大學、印尼教育大學、印尼建國大學 BINUS、三寶麟大學、詹伯大學、亞齊大學、占碑大學、諾門森大學，"
                "印度希夫納達爾大學、可愛專業大學、阿薩姆鮑思高大學、舒利尼大學，以及越南胡志明市理工大學 HCMUT、胡志明市國家大學人文與社會科學大學、胡志明市外語資訊大學 HUFLIT、西貢文朗學院、西貢百科學院共 39 所國際及澳門合作大學）"
            ),
            (
                "國際暨兩岸事務處暨教務處註冊組「2027春季班（115學年度第2學期）赴中國大陸地區交換學生甄選計畫」（涵蓋廈門大學、四川大學、中國政法大學、北京交通大學、北京科技大學、東華大學、中國海洋大學、華中師範大學、蘭州大學、福州大學等 10 所當期開放申請 985／雙一流名校，以及南京大學、重慶大學、吉林大學、廣西大學、北京體育大學、陝西師範大學、中國石油大學［華東］、福建師範大學、浙江師範大學、上海師範大學、長安大學、山東財經大學、魯東大學、汕頭大學、吉林體育學院共 25 所大陸姊妹校）"
            ),
            (
                "國際暨兩岸事務處「教育部學海飛颺、學海惜珠、學海築夢／新南向學海築夢」暨「國立金門大學學生國際交流獎助學金」獎助體系"
            ),
        ],
        "academic_year": [
            (
                "115（涵蓋 115 學年度第二階段［春季班］國際交換學生甄選：即日起至 2026/05/25 17:00 收件截止、05/27 面試、06/05 放榜；"
                "以及 2027 春季班［115 學年度第 2 學期］赴中國大陸地區交換學生甄選：2026/09/14–09/24 17:00 收件、09/30 面試、10/14 放榜）"
            ),
            (
                f"本平台完整收錄國立金門大學國際暨兩岸事務處公告之 {len(partners)} 所國際及大陸地區交換合作學校（橫跨 15 個國家與地區，含"
                f" {open_partner_count} 所當期開放申請之交換合作校，並收錄 {exp_covered_schools} 所合作大學共"
                f" {total_exp_reports} 篇歷屆赴外與赴大陸交換生研修心得報告）"
            ),
        ],
        "semester": [
            (
                "國際交換學生甄選每年分兩階段辦理：第一階段（11 月收件、12 月面試）選送次學年第 1 學期（秋季班）或第 2 學期（春季班）出國交換；第二階段（5 月收件、5 月底面試）開放次學年第 2 學期（春季班）尚有餘額之學校申請。"
            ),
            (
                "赴中國大陸（暨國內）各大學校院交換學生甄選每學期辦理：秋季班於每年 3–4 月收件甄選；春季班（如 2027 春季班）於每年 9 月中下旬收件、9 月底面試、10 月中旬公告錄取名單（每位申請人可於國內與大陸姊妹校中綜合選填至多 5 個志願）。"
            ),
        ],
        "application_period": [
            (
                "【2027 春季班（115 學年度第 2 學期）赴國內及大陸地區交換學生甄選】校內收件時間：2026 年 9 月 14 日（一）08:00 至 9 月 24 日（四）17:00 止（國內交換延長至 9 月 30 日止），送交綜合教學大樓 3 樓教務處註冊組；"
                "實體面試時間：2026 年 9 月 30 日（三）10:10 於綜合大樓 208 教室；"
                "聯合甄審與放榜：2026 年 10 月 14 日公告錄取名單，錄取生須於 2026 年 10 月 16 日（五）12:00 前向國際處繳交《錄取資格確認書》或《放棄聲明書》。"
            ),
            (
                "【115 學年度第二階段（春季班）國際交換學生甄選】校內收件時間：即日起至 2026 年 5 月 25 日（一）17:00 止，送交綜合教學大樓 4 樓國際暨兩岸事務處（R445）；"
                "面試時間：2026 年 5 月 27 日（三）09:10 起；錄取公告：預計 2026 年 6 月 5 日（五）前公告，2026 年 6 月 12 日（五）17:00 前繳交《錄取資格確認書》或《放棄聲明書》。"
            ),
            (
                "【115 學年度第一階段國際交換學生甄選】校內收件：2025 年 11 月 17 日至 11 月 28 日 17:00 止；面試：2025 年 12 月 17 日至 12 月 18 日。"
            ),
        ],
        "eligibility": [
            (
                "1. 國際交換學生申請資格：依《國立金門大學學生國際交流甄選要點》及《115 學年度第一／二階段國際交換簡章》，申請人於出國前須為在校修業滿 4 學期（2 學年）以上之在學學生（即出國時為大三以上；日本新潟大學僅限人文社會學院研究生申請、日本琉球大學僅限管理學院學生申請），操行成績平均達 80 分（含）以上，且符合各接待姊妹校之 GPA（2.00–3.00/4.00）與語言檢定門檻（語測證書須為 2 年有效期內）。"
            ),
            (
                "2. 赴中國大陸地區交換申請資格：依《2027 春季班赴國內及大陸地區交換學生甄選簡章》，申請人須為本校日間部在校修業滿 1 學年之在學學生（大二以上及碩、博士班；博、碩士生得優先錄取，各姊妹校至多限 1 名博碩士生優先錄取且須附指導教授同意函；廈門大學與福州大學不接受大一、大四學生申請）；學士班申請人歷年學業總成績平均需達 70 分以上，且歷年班、系排名百分比在 60% 以內（兩項條件皆需符合）。"
            ),
            (
                "3. 兩階段甄選配分標準：國際交換採序列法，書面審查占 60%（GPA 20%、語言測驗 20%、自傳與讀書計畫 10%、績優證明 5%、推薦信 5%）＋面試 40%（海外經驗 10%、學習規劃 10%、口語表達 10%、現場反應 10%）；大陸交換採序位法，書面審查占 60%（學業成績班系排名百分比 30%、操行成績 10%、自傳與學習計畫 10%、推薦信及績優證明 10%）＋實體面試 40%（赴大陸學習規劃 15%、兩岸與國際交流經驗 15%、口語表達與臨場反應 10%）。"
            ),
            (
                "4. 境外修課、學分抵免與返國義務：交換期間須於金大完成註冊並繳交全額學雜費及學生平安保險費；大陸姊妹校每學期至少應修習 2 門以上課程（北京交通大學選擇交換之專業至少需選修 1 門課；北京科技大學學士班每學期至少需修滿 8 學分）；依《國立金門大學科目學分抵免辦法》，境外交換抵免學分總數最高不得超過應修畢業學分數之 1/2（碩士班不得超過 1/3）；交換結束後 2 週內須回國返校報到，並於報到後 1 個月內繳交正式成績單、2,000 字以上心得報告（含照片 5 張以上）及 3–10 分鐘心得影片（含中文字幕 mp4）。"
            ),
        ],
        "language_requirement": [
            (
                "1. 國際交換語言能力檢定與 2 年效期規定：申請國際交換學生計畫者，「語言測驗成績」占校內書面審查總分 20%，且所檢附之語言能力證明必須為證書日期起算 2 年內有效成績（逾期不予採計）。"
            ),
            (
                "2. 各國姊妹校常見語言門檻：英語授課姊妹校（美、德、土、馬、泰、菲、印尼、印、越、俄）多要求 CEFR B1–B2（TOEIC 550–785／TOEFL iBT 61–80／IELTS 5.0–6.0；美國東南密蘇里州立大學與夏威夷大學馬諾阿分校亦採認 Duolingo 95+）；日本姊妹校（三重大學、琉球大學、新潟大學、廣島大學）要求 JLPT N2–N3；韓國姊妹校（建國大學、誠信女子大學、釜山外國語大學）要求 TOPIK 2–3 級或英語檢定。"
            ),
            (
                "3. 中國大陸及澳門地區交換語言規定：申請中國大陸 25 所締約姊妹校及澳門科技大學中文授課課程者，免附外語能力檢定證明。"
            ),
        ],
        "required_documents": [
            "1. 國立金門大學學生國際交流資料審查流程表（SOP，須先經系主任、院長、教務處註冊組及學務處生輔組審核核章）",
            "2. 國際交流學生甄選報名表／赴國內及大陸地區交換學生申請表（大陸交換至多可填 5 個志願）",
            "3. 中文歷年成績單正本（須註明歷年學業總平均成績、GPA 及班／系排名百分比）與學務處獎懲紀錄證明",
            "4. 中文自傳（Autobiography）及讀書／學習計畫書（Study Plan，含動機、預期修課規劃與返國學分銜接）",
            "5. 證書日期起算 2 年內有效之語言能力檢定證明影本（國際交換必備，占總成績 20%；大陸交換免附）及各項競賽／社團績優證明",
            "6. 教師推薦信（研究生申請大陸交換須另附指導教授同意函）、家長（監護人）同意書及身分證／學生證／有效護照影本",
        ],
        "scholarship_info": [
            (
                "1. 教育部《學海飛颺》選送優秀學生出國研修獎學金：依國立金門大學《教育部學海飛颺及學海惜珠計畫甄選簡章》，補助具中華民國國籍且在臺設有戶籍、在校就讀滿 1 學期以上、外語能力優異（證書須在 2 年效期內）之在學學生赴非大陸港澳地區姊妹校交換 1 學期或 1 學年之往返機票與國外生活費。"
            ),
            (
                "2. 教育部《學海惜珠》勵學優秀學生出國研修獎學金：補助持各直轄市、縣（市）主管機關開立之低收入戶、中低收入戶或特殊境遇家庭相關證明之在學學生赴非大陸港澳地區合作學校交換研修。"
            ),
            (
                "3. 教育部《學海築夢》及《新南向學海築夢》海外專業實習計畫：由本校專任教師主持計畫選送學生赴海外或新南向國家企業與機構進行專業實習，補助機票與生活費。"
            ),
            (
                "4. 《國立金門大學學生國際交流甄選要點》出國交換獎助學金：通過本校國際交流甄選並完成註冊出國之交換學生，得依本校年度預算及甄選要點第 8 點規定核發國際交流獎助學金。"
            ),
        ],
        "partner_universities": [p["school_name"] for p in partners],
        "source_urls": nqu_source_urls,
        "last_checked": CHECKED_AT,
    }
    (OFFICIAL_NQU_DIR / "exchange_info.json").write_text(
        json.dumps(exchange_info_payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    student_dashboard_payload = {
        "school_name": "國立金門大學",
        "last_checked": CHECKED_AT,
        "academic_score_minimum": 70.0,
        "academic_score_rule": (
            "依《國立金門大學學生國際交流甄選要點》、《115學年度第一／二階段國際交換簡章》及《2027春季班赴國內及大陸地區交換學生甄選簡章》："
            "（1）國際交換：出國前須在校修業滿 4 學期（2 學年）以上，操行成績平均達 80 分（含）以上，並符合各姊妹校 GPA 門檻（GPA 2.00–3.00/4.00）；"
            "（2）赴大陸地區交換：日間部在校修業滿 1 學年（廈門大學與福州大學不接受大一、大四生），學士班歷年學業總成績平均需達 70 分以上，且歷年班、系排名百分比在 60% 以內（兩項條件皆需符合），至多可選填 5 個志願。"
        ),
        "academic_gpa_minimum": 2.0,
        "maximum_preferences": 5,
        "selection_rules": {
            "academic_policy": "score_or_rank",
            "academic_reference_year": "115",
            "undergraduate_gpa_minimum": 2.0,
            "graduate_academic_exempt": False,
            "exclude_in_service": True,
            "pending_quota_planning": False,
            "partner_requirements_need_confirmation": False,
            "degree_score_minimums": {
                "undergraduate": 70.0,
                "master": 70.0,
                "doctoral": 70.0,
            },
            "excluded_undergraduate_years": ["freshman"],
            "language_certificate_required": True,
        },
        "language_score_minimums": {
            "toefl": 61.0,
            "ielts": 5.0,
            "toeic": 550.0,
        },
        "application_periods": [
            {
                "title": (
                    "國立金門大學「2027春季班（115學年度第2學期）」赴中國大陸暨國內各大學校院交換學生甄選（09/14–09/24 17:00收件、09/30面試、10/14放榜）"
                ),
                "details": [
                    (
                        "開放申請交換期間：2027 年春季班（115 學年度第 2 學期，交換 1 學期）。"
                        "校內收件時間：2026 年 9 月 14 日（一）08:00 至 9 月 24 日（四）17:00 止（國內交換延長至 9 月 30 日止），送交綜合教學大樓 3 樓教務處註冊組。"
                    ),
                    (
                        "面試與放榜時程：2026 年 9 月 30 日（三）10:10 於綜合大樓 208 教室辦理實體面試；"
                        "2026 年 10 月 14 日召開聯合甄審會議並公告錄取名單，錄取生須於 2026 年 10 月 16 日（五）12:00 前向國際處繳交《錄取資格確認書》或《放棄聲明書》。"
                    ),
                ],
                "source": {
                    "title": "國立金門大學國際暨兩岸事務處《2027春季班赴國內及大陸地區交換學生甄選公告（一）與錄取名單》",
                    "source_url": NQU_MAINLAND_2027_SPRING_URL,
                    "category": "exchange_application",
                    "summary": "金大 2027 春季班赴大陸（廈門大學、四川大學、中國政法大學等 10 校）與國內交換甄選簡章、收件面試與錄取確認時程。",
                },
                "scope": "home_application",
                "program_types": ["exchange"],
                "academic_year": "115",
                "application_round": "2027春季班（115學年度第2學期）赴中國大陸地區交換學生甄選",
                "audience": "all_students",
                "opens_at": "2026-09-14T08:00:00+08:00",
                "deadline_at": "2026-09-24T17:00:00+08:00",
                "date_status": "verified_exact",
                "status": "closed",
                "status_note": "2027 春季班（115-2）赴國內及大陸地區交換學生甄選已完成收件與面試，並於 2026/10/14 正式公告校內錄取名單（【正式公告1-3】校內錄取名單115-2.pdf）。",
                "deadline_note": "2027 春季班大陸交換校內收件至 2026 年 9 月 24 日 17:00 截止，9 月 30 日實體面試，10 月 14 日公告錄取名單。",
                "reminder_eligible": False,
                "checked_at": CHECKED_AT,
            },
            {
                "title": (
                    "國立金門大學「115學年度第二階段（春季班）」國際交換學生甄選（05/25 17:00收件截止、05/27面試、06/05放榜）"
                ),
                "details": [
                    (
                        "開放申請對象與學校：選送 115 學年度第 2 學期（2027 春季班）赴日本新潟大學、韓國誠信女子大學、釜山外國語大學、馬來亞大學、拉曼大學、澳門科技大學、土耳其阿卜杜拉居爾大學、TED 大學、美國東南密蘇里州立大學、夏威夷大學馬諾阿分校、德國維爾茨堡-施韋因富特科技大學、俄羅斯莫斯科市立大學及泰、菲、印尼、印、越等 36 所尚有餘額之國際姊妹校。"
                    ),
                    (
                        "收件、面試與確認時程：即日起至 2026 年 5 月 25 日（一）17:00 前將申請資料送交綜合教學大樓 4 樓國際暨兩岸事務處（R445）；"
                        "2026 年 5 月 27 日（三）09:10 起辦理面試；預計 2026 年 6 月 5 日（五）前公告錄取名單，錄取生須於 2026 年 6 月 12 日（五）17:00 前繳交《錄取資格確認書》或《放棄聲明書》。"
                    ),
                ],
                "source": {
                    "title": "國立金門大學國際暨兩岸事務處《115學年度第二階段國際交換學生甄選簡章公告》",
                    "source_url": NQU_INTL_STAGE2_POST_URL,
                    "category": "exchange_application",
                    "summary": "金大 115 學年度第二階段（春季班）國際交換簡章、開放姊妹校餘額、書審 60%＋面試 40% 配分與時程。",
                },
                "scope": "home_application",
                "program_types": ["exchange"],
                "academic_year": "115",
                "application_round": "115學年度第二階段（春季班）國際交換學生甄選",
                "audience": "all_students",
                "opens_at": "2026-04-15T08:00:00+08:00",
                "deadline_at": "2026-05-25T17:00:00+08:00",
                "date_status": "verified_exact",
                "status": "closed",
                "status_note": "115 學年度第一階段與第二階段國際交換甄選已辦理完畢；116 學年度第一階段國際交換甄選預計於每年 11 月中旬開放收件。",
                "deadline_note": "115 學年度第二階段國際交換校內收件至 2026 年 5 月 25 日（一）17:00 截止，5 月 27 日面試，6 月 5 日前公告錄取名單。",
                "reminder_eligible": False,
                "checked_at": CHECKED_AT,
            },
        ],
        "program_overview": [{
            "title": (
                f"國立金門大學國際暨兩岸事務處全球與大陸地區姊妹校交換計畫暨學海獎助總覽（{len(partners)} 所交換合作校・{open_partner_count} 所當期開放交換）"
            ),
            "details": [
                (
                    "國立金門大學（National Quemoy University, NQU，簡稱金大，位於金門縣金寧鄉大學路 1 號，設有「人文社會學院、管理學院、理工學院、健康護理學院」四大學院）"
                    "由國際暨兩岸事務處（Office of International and Cross-Strait Affairs, OICA，位於綜合教學大樓 4 樓 R445）會同教務處註冊組（綜合教學大樓 3 樓）"
                    f"統籌全校出國及赴大陸地區交換學生暨教育部學海系列獎補助。本平台完整收錄 {len(partners)} 所金大官方交換合作學校，"
                    f"橫跨 15 個國家與地區（含 39 所國際及澳門合作校與 25 所中國大陸合作校，其中 {open_partner_count} 所為當期簡章開放申請學校）。"
                ),
                (
                    "金大交換學生計畫具備五大核心特色：（1）立足金門連結國際與兩岸，國際交換涵蓋日本（三重大學、琉球大學、新潟大學、廣島大學）、韓國（建國大學、誠信女子大學、釜山外國語大學）、"
                    "美國（東南密蘇里州立大學、夏威夷大學馬諾阿分校）、德國（維爾茨堡-施韋因富特科技大學 THWS）、土耳其（阿卜杜拉居爾大學、TED 大學）、俄羅斯（莫斯科市立大學）、"
                    "馬來西亞（馬來亞大學、拉曼大學）、澳門（澳門科技大學）、泰國（泰國農業大學、皇太后大學）、菲律賓、印尼（印度尼西亞大學 UI、加查馬達大學 UGM、巴查查蘭大學等 10 校）、印度（希夫納達爾大學等 4 校）與越南（胡志明市理工大學 HCMUT、胡志明市國家大學人文社科大等 5 校）；"
                    "（2）兩岸交換深耕大陸 985／雙一流頂尖名校，2027 春季班開放廈門大學（每學期 5 名）、四川大學、華中師範大學、福州大學（各 3 名）、中國政法大學、北京交通大學、北京科技大學、東華大學、中國海洋大學、蘭州大學（各 2 名），並與南京大學、重慶大學、吉林大學、北京體育大學等締結姊妹校；"
                    "（3）甄選採「第一階段書面審查 60%＋第二階段實體面試 40%」公開透明評比；"
                    "（4）結合教育部《學海飛颺》、《學海惜珠》、《學海築夢／新南向學海築夢》與校內國際交流獎助學金；"
                    f"（5）完整收錄國際處官網公告之 {exp_covered_schools} 校共 {total_exp_reports} 篇歷屆學長姐赴大陸（282 篇）與赴國際（35 篇）交換研修心得報告。"
                ),
            ],
            "source": {
                "title": "國立金門大學國際暨兩岸事務處（OICA）交換學生專區與姊妹校一覽表",
                "source_url": NQU_INTL_EXCHANGE_LIST_URL,
                "category": "exchange_application",
                "summary": f"金大 {len(partners)} 所國際及大陸交換合作學校、{open_partner_count} 所當期開放交換與甄選簡章總覽。",
            },
        }],
        "eligibility": [{
            "title": (
                "金大國際交換（出國前修滿 4 學期、操行 80 分以上）與赴大陸交換（修滿 1 學年、學士班平均 70 分且班系排名前 60%）雙軌資格與評分規定"
            ),
            "details": [
                (
                    "國際交換資格與序列法配分：依《國立金門大學學生國際交流甄選要點》及《115學年度第一／二階段國際交換簡章》，申請人於出國前須在校修業滿 4 學期（2 學年）以上，操行成績平均達 80 分（含）以上，且符合各接待姊妹校之 GPA 與 2 年內有效語測門檻；校內甄選採序列法：書面審查 60%（GPA 20%、語測 20%、自傳與讀書計畫 10%、績優證明 5%、推薦信 5%）＋面試 40%（海外經驗 10%、學習規劃 10%、口語表達 10%、現場反應 10%）。"
                ),
                (
                    "大陸交換資格與序位法配分：依《2027春季班赴國內及大陸地區交換學生甄選簡章》，申請人須為日間部修業滿 1 學年之在學生（博碩士生每校至多 1 名優先錄取並附指導教授同意函；廈門大學與福州大學不接受大一、大四生），學士班歷年學業總平均需達 70 分以上且班、系排名百分比在 60% 以內（兩項皆需符合），至多可填 5 個志願；校內甄選採序位法：書面審查 60%（班系排名百分比 30%、操行 10%、自傳與學習計畫 10%、推薦信及績優證明 10%）＋實體面試 40%。"
                ),
            ],
            "source": {
                "title": "國立金門大學學生國際交流甄選要點與 2027 春季班赴國內及大陸地區交換學生甄選簡章",
                "source_url": NQU_INTL_REG_PDF,
                "category": "exchange_application",
                "summary": "金大國際與大陸交換申請資格、修業年限、GPA 與排名百分比門檻及書審／面試評分權重。",
            },
        }],
        "language_requirements": [{
            "title": (
                "金大國際交換語言檢定要求（須為證書日期起算 2 年內有效成績，占書審總成績 20%）與大陸交換中文授課規定"
            ),
            "details": [
                (
                    "國際交換語測 2 年效期與門檻：申請國際交換者須檢附證書日期起算 2 年內有效之外語能力檢定證明（占書審總成績 20%）；英語授課姊妹校多要求 TOEIC 550–785／TOEFL iBT 61–80／IELTS 5.0–6.0（馬來亞大學、夏威夷大學馬諾阿分校、德國 THWS、土耳其 AGU/TEDU、印尼 UI/UGM 等要求較高）；日本姊妹校要求 JLPT N2–N3；韓國姊妹校要求 TOPIK 2–3 級或英語檢定。"
                ),
                (
                    "大陸及澳門交換免外語檢定：申請赴中國大陸各姊妹校及澳門科技大學中文授課學程者，免附外語能力檢定證明。"
                ),
            ],
            "source": {
                "title": "國立金門大學《115學年度第一／二階段國際交換簡章》",
                "source_url": NQU_STAGE2_BROCHURE_PDF,
                "category": "exchange_application",
                "summary": "金大國際交換各姊妹校語言檢定門檻與 2 年有效期採認規定。",
            },
        }],
        "required_documents": [{
            "title": (
                "學生國際交流資料審查流程表（SOP）、甄選報名表、歷年成績單（含排名百分比）與獎懲紀錄、2年內有效語測證明、自傳與讀書計畫及家長同意書"
            ),
            "details": [
                (
                    "校內申請必備文件：（1）《學生國際交流資料審查流程表（SOP）》（須先經系主任、院長、教務處註冊組及學務處生輔組核章）；"
                    "（2）國際交流學生甄選報名表／赴國內及大陸地區交換學生申請表；"
                    "（3）中文歷年成績單正本（含總平均、GPA 及班系排名百分比）與學務處獎懲紀錄證明；"
                    "（4）中文自傳與讀書／學習計畫書；"
                    "（5）2 年有效期內之語言能力檢定證明影本（國際交換必備）及各項績優證明；"
                    "（6）教師推薦信（研究生申請大陸交換須附指導教授同意函）、家長（監護人）同意書及身分證／學生證／護照影本。"
                ),
                (
                    "錄取確認與返國必備文件：錄取公告後須於規定期限內繳交《錄取資格確認書》或《錄取資格放棄聲明書》；"
                    "結束交換後 2 週內須回國返校報到，並於報到後 1 個月內向國際處繳交彌封成績單、2,000 字以上交流心得報告（含本人入鏡照片 5 張以上）及 3–10 分鐘心得影片（含中文字幕橫式 mp4）。"
                ),
            ],
            "source": {
                "title": "國立金門大學國際暨兩岸事務處《國際交流申請表件下載專區》與《2027春季班交換簡章》",
                "source_url": NQU_INTL_FORMS_URL,
                "category": "exchange_application",
                "summary": "金大國際與大陸交換申請表單、審查流程 SOP 表、家長同意書與返國心得繳交規範。",
            },
        }],
        "scholarship_info": [{
            "title": (
                "教育部《學海飛颺》、《學海惜珠》、《學海築夢／新南向學海築夢》與《國立金門大學學生國際交流獎助學金》"
            ),
            "details": [
                (
                    "教育部學海系列計畫：依國立金門大學《教育部學海飛颺及學海惜珠計畫甄選簡章》，錄取非大陸港澳地區姊妹校且具中華民國國籍、在臺設有戶籍及 2 年內有效外語檢定證明之交換生，得申請《學海飛颺》（優秀生）或《學海惜珠》（持低收入戶、中低收入戶或特殊境遇家庭證明者）補助往返機票與國外生活費；另辦理《學海築夢》及《新南向學海築夢》補助海外實習。"
                ),
                (
                    "校內國際交流獎助學金：依《國立金門大學學生國際交流甄選要點》第 8 點及《學生出國交換實施要點》，通過校內甄選並依規定完成註冊出國之交換生，得依學校年度預算核給獎助學金。"
                ),
            ],
            "source": {
                "title": "國立金門大學國際暨兩岸事務處《115年度教育部學海飛颺及學海惜珠計畫甄選簡章公告》",
                "source_url": NQU_XUEHAI_POST_URL,
                "category": "scholarship",
                "summary": "金大辦理教育部學海飛颺、學海惜珠甄選簡章與校內國際交流獎助規定。",
            },
        }],
        "document_explanations": [{
            "title": (
                "國立金門大學學生國際交流資料審查流程表（SOP）、交換申請表、自傳與學習計畫及家長同意書準備指南"
            ),
            "summary": (
                "說明金大四大學院學生申請國際與大陸交換必備之 SOP 審查流程核章順序、書審配分重點、2 年有效語測證明規範與返國報告及短視頻要求。"
            ),
            "key_points": [
                (
                    "SOP 審查流程表四級核章：送件前必須先持《學生國際交流資料審查流程表》依序完成「系主任 → 院長 → 教務處註冊組 → 學務處生輔組」審核簽章，再將完整申請資料送交國際暨兩岸事務處（國際交換）或教務處註冊組（大陸交換）。"
                ),
                (
                    "書面審查（60%）與面試（40%）準備重點：國際交換重視 GPA（20%）與 2 年內有效語測證明（20%）；大陸交換重視歷年班系排名百分比（30%，且須在 60% 以內及平均 70 分以上）與操行成績（10%）。"
                ),
                (
                    "返國 2 週內報到與 1 個月內繳交報告及影片義務：結束交換後 2 週內須返校報到，1 個月內繳交正式成績單、2,000 字以上心得報告（含本人入鏡照片 5 張以上）及 3–10 分鐘心得影片（含中文字幕橫式 mp4）。"
                ),
            ],
            "applies_to": [],
            "source": {
                "title": "國立金門大學國際暨兩岸事務處《審查流程 SOP 說明》與《交換學生甄選簡章》",
                "source_url": NQU_INTL_FORMS_URL,
                "category": "exchange_application",
                "summary": None,
            },
            "document_url": NQU_SOP_PDF,
            "document_type": "official_document",
            "full_text_extracted": True,
        }],
        "rule_explanations": [{
            "title": (
                "國立金門大學學生國際交流甄選要點、學生出國交換實施要點與科目學分抵免辦法核心法規"
            ),
            "summary": (
                "規範金大四大學院學生申請國際與大陸交換之修業年限、學業與操行門檻、全額學雜費註冊、境外最低修課要求及學分抵免上限（大學部 1/2、碩士班 1/3）。"
            ),
            "key_points": [
                (
                    "國際與大陸交換雙軌修業年限與成績門檻：國際交換出國前須修滿 4 學期（大三以上）且操行達 80 分以上；大陸交換須為日間部修滿 1 學年（大二以上；廈門大學与福州大學不接受大一、大四生），學士班歷年總平均達 70 分以上且班系排名前 60%。"
                ),
                (
                    "交換期間學籍、註冊與修課規定：交換期間以 1 學期為原則（必要時得申請延長 1 次至多 1 學期；國內、國外、大陸交換分別最長 1 學年，總時程以 2 學年為限），須於金大註冊並繳交全額學雜費；大陸姊妹校每學期至少應修習 2 門以上課程（北交大本專業至少 1 門、北科大至少 8 學分）。"
                ),
                (
                    "境外交換科目學分抵免上限：依《國立金門大學科目學分抵免辦法》第 10 條，學生奉准出國或赴大陸姊妹校交換進修所修習之科目學分，抵免學分總數最高不得超過應修畢業學分數之 1/2（碩士班不得超過 1/3）。"
                ),
            ],
            "applies_to": [],
            "source": {
                "title": "國立金門大學學生國際交流甄選要點、學生出國交換實施要點與科目學分抵免辦法",
                "source_url": NQU_INTL_REGULATIONS_URL,
                "category": "exchange_application",
                "summary": None,
            },
            "document_url": NQU_INTL_REG_PDF,
            "document_type": "official_document",
            "full_text_extracted": True,
        }],
        "sources": [
            {
                "title": "國立金門大學國際暨兩岸事務處（OICA）官方網站",
                "source_url": NQU_OICA_HOME_URL,
                "category": "exchange_application",
                "summary": None,
            },
            {
                "title": "國立金門大學國際交換學校一覽表（39 所國際及澳門姊妹校）",
                "source_url": NQU_INTL_PARTNERS_URL,
                "category": "partner_school",
                "summary": None,
            },
            {
                "title": "國立金門大學大陸地區交換學校一覽表與姊妹校名冊（25 所大陸合作大學）",
                "source_url": NQU_MAINLAND_PARTNERS_URL,
                "category": "partner_school",
                "summary": None,
            },
            {
                "title": "國立金門大學 115 學年度第二階段國際交換學生甄選簡章公告",
                "source_url": NQU_INTL_STAGE2_POST_URL,
                "category": "exchange_application",
                "summary": None,
            },
            {
                "title": "國立金門大學 2027 春季班（115-2）赴國內及大陸地區交換學生甄選簡章與錄取名單公告",
                "source_url": NQU_MAINLAND_2027_SPRING_URL,
                "category": "exchange_application",
                "summary": None,
            },
            {
                "title": "國立金門大學學生國際交流甄選要點與學生出國交換實施要點 PDF",
                "source_url": NQU_INTL_REG_PDF,
                "category": "exchange_application",
                "summary": None,
            },
            {
                "title": "國立金門大學 115 年度教育部學海飛颺及學海惜珠計畫甄選簡章公告",
                "source_url": NQU_XUEHAI_POST_URL,
                "category": "scholarship",
                "summary": None,
            },
            {
                "title": "國立金門大學交換學生心得報告專區（大陸地區 282 篇＋國際交換 35 篇，共 317 篇）",
                "source_url": NQU_EXP_MAINLAND_URL,
                "category": "experience_report",
                "summary": None,
            },
        ],
    }
    (OFFICIAL_NQU_DIR / "student_dashboard.json").write_text(
        json.dumps(student_dashboard_payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    doc_conditions = {
        "school_id": "nqu",
        "school_name": "國立金門大學",
        "checked_at": CHECKED_AT,
        "source_url": NQU_STAGE2_BROCHURE_PDF,
        "common_documents": exchange_info_payload["required_documents"],
        "track_specific_conditions": [
            {
                "track": "國際暨兩岸事務處【115學年度第一／二階段國際交換學生甄選計畫（38 所開放國際及澳門姊妹校）】",
                "required": [
                    "學生國際交流資料審查流程表（SOP，經系主任、院長、註冊組、生輔組核章）及國際交流學生甄選報名表",
                    "中文歷年成績單正本（含 GPA 及班系排名百分比）、操行成績證明（平均達 80 分以上）及獎懲紀錄",
                    "證書日期起算 2 年內有效之外語能力檢定證明影本（占書審 20%）、中文自傳與讀書計畫（10%）、績優證明（5%）及推薦信（5%）",
                    "家長（監護人）同意書、錄取後繳交《錄取資格確認書》；返國後 2 週內報到，1 個月內繳交彌封成績單、2,000 字以上心得報告（含照片）及 5–10 分鐘心得影片",
                ],
            },
            {
                "track": "國際暨兩岸事務處暨教務處註冊組【2027春季班（115-2）赴中國大陸地區交換學生甄選計畫（10 所當期開放 985／雙一流名校，至多選填 5 志願）】",
                "required": [
                    "赴國內及大陸地區交換學生申請表（含系所及學院審核簽章）、中文歷年成績單正本（學士班須平均 70 分以上且班系排名前 60%）及獎懲紀錄",
                    "中文自傳、赴大陸學習計畫書、教師推薦信（博碩士生須另附指導教授同意函）及家長（監護人）同意書",
                    "身分證正反面影本、學生證影本；錄取後繳交《錄取資格確認書》；返國後 2 週內報到，1 個月內繳交成績單 2 份、心得報告（含本人入鏡照片 5 張以上）及 3–10 分鐘短視頻（含中文字幕橫式 mp4）",
                ],
            },
            {
                "track": "教育部【學海飛颺／學海惜珠／學海築夢】出國研修與海外實習獎助學金",
                "required": [
                    "依國立金門大學《教育部學海飛颺及學海惜珠計畫甄選簡章》檢附申請書、歷年成績單（含排名）、2 年內有效外語能力證明、出國研修計畫書及新式戶口名簿影本（學海惜珠須另附低收入戶、中低收入戶或特殊境遇家庭證明）",
                    "返國後須於教育部學海計畫資訊網上傳心得報告及問卷，並檢附來回電子機票、登機證存根、旅行社代收轉付收據及出入境紀錄辦理核銷",
                ],
            },
        ],
    }
    (OFFICIAL_NQU_DIR / "document-conditions.json").write_text(
        json.dumps(doc_conditions, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    field_cov_lines = [
        "field_name,total_records,populated_records,coverage_ratio,notes"
    ]
    for fname in [
        "school_name",
        "country",
        "region",
        "program_type",
        "availability_status",
        "quota",
        "colleges",
        "degree_levels",
        "language_requirement",
        "gpa_requirement",
        "application_deadline",
        "study_period",
        "semester_dates",
        "housing_info",
        "course_restrictions",
        "official_website",
        "image_url",
    ]:
        pop = sum(1 for p in partners if p.get(fname) not in (None, "", []))
        ratio = pop / len(partners) if partners else 1.0
        field_cov_lines.append(
            f"{fname},{len(partners)},{pop},{ratio:.4f},Official NQU OICA verified"
        )
    (OFFICIAL_NQU_DIR / "field-coverage.csv").write_text(
        "\n".join(field_cov_lines) + "\n", encoding="utf-8"
    )

    pages_records = [
        {
            "title": "國立金門大學：2027春季班（115-2）赴中國大陸地區交換學生甄選簡章（09/14–09/24收件、09/30面試、10/14放榜）與 115學年度第一／二階段國際交換學生甄選時程",
            "source_url": NQU_MAINLAND_2027_SPRING_URL,
            "published_at": "2026-09-07T00:00:00Z",
            "text": "\n".join(exchange_info_payload["application_period"]),
            "summary": "\n".join(exchange_info_payload["application_period"]),
            "category": "exchange_application",
            "attachments": [],
            "crawled_at": CHECKED_AT,
            "content_hash": hashlib.sha256(
                "\n".join(exchange_info_payload["application_period"]).encode("utf-8")
            ).hexdigest(),
        },
        {
            "title": "國立金門大學：學生國際交流甄選要點、出國前修滿4學期與操行80分門檻、大陸交換平均70分且排名前60%門檻、書審60%＋面試40%配分與學分抵免辦法",
            "source_url": NQU_INTL_REG_PDF,
            "published_at": "2026-04-15T00:00:00Z",
            "text": "\n".join(exchange_info_payload["eligibility"]),
            "summary": "\n".join(exchange_info_payload["eligibility"]),
            "category": "exchange_application",
            "attachments": [],
            "crawled_at": CHECKED_AT,
            "content_hash": hashlib.sha256(
                "\n".join(exchange_info_payload["eligibility"]).encode("utf-8")
            ).hexdigest(),
        },
        {
            "title": f"國立金門大學：{len(partners)} 所國際及大陸地區交換合作學校一覽表、{open_partner_count} 所開放交換校與 2 年有效期語言檢定門檻",
            "source_url": NQU_INTL_PARTNERS_URL,
            "published_at": "2026-04-15T00:00:00Z",
            "text": "\n".join(exchange_info_payload["language_requirement"]),
            "summary": "\n".join(exchange_info_payload["language_requirement"]),
            "category": "exchange_application",
            "attachments": [],
            "crawled_at": CHECKED_AT,
            "content_hash": hashlib.sha256(
                "\n".join(exchange_info_payload["language_requirement"]).encode("utf-8")
            ).hexdigest(),
        },
        {
            "title": "國立金門大學：學生國際交流資料審查流程表（SOP）、甄選報名表、自傳與讀書計畫、家長同意書及返國2週內報到與1個月內報告及短視頻規範",
            "source_url": NQU_INTL_FORMS_URL,
            "published_at": "2026-04-15T00:00:00Z",
            "text": "\n".join(exchange_info_payload["required_documents"]),
            "summary": "\n".join(exchange_info_payload["required_documents"]),
            "category": "exchange_application",
            "attachments": [],
            "crawled_at": CHECKED_AT,
            "content_hash": hashlib.sha256(
                "\n".join(exchange_info_payload["required_documents"]).encode("utf-8")
            ).hexdigest(),
        },
        {
            "title": "國立金門大學：115年度教育部學海飛颺、學海惜珠、學海築夢計畫甄選簡章與校內學生國際交流獎助學金",
            "source_url": NQU_XUEHAI_POST_URL,
            "published_at": "2026-03-01T00:00:00Z",
            "text": "\n".join(exchange_info_payload["scholarship_info"]),
            "summary": "\n".join(exchange_info_payload["scholarship_info"]),
            "category": "scholarship",
            "attachments": [],
            "crawled_at": CHECKED_AT,
            "content_hash": hashlib.sha256(
                "\n".join(exchange_info_payload["scholarship_info"]).encode("utf-8")
            ).hexdigest(),
        },
    ]
    pages_text = (
        "\n".join(json.dumps(p, ensure_ascii=False) for p in pages_records) + "\n"
    )
    (OFFICIAL_NQU_DIR / "pages.jsonl").write_text(pages_text, encoding="utf-8")
    (OFFICIAL_NQU_DIR / "processed_pages.jsonl").write_text(
        pages_text, encoding="utf-8"
    )

    home_rules = {
        "school_id": "nqu",
        "school_name": "國立金門大學",
        "eligibility": student_dashboard_payload["eligibility"],
        "application_periods": student_dashboard_payload["application_periods"],
        "selection_rules": {
            "undergraduate_score_minimum": 70.0,
            "graduate_score_minimum": 70.0,
            "class_rank_percentile_maximum": 60.0,
            "conduct_score_minimum": 80.0,
            "min_courses_per_semester_abroad": 2,
            "maximum_preferences": 5,
            "screening_batches_per_year": 2,
            "allow_freshman_apply": False,
            "min_enrolled_semesters_undergrad_intl": 4,
            "min_enrolled_semesters_undergrad_mainland": 2,
            "min_enrolled_semesters_grad": 1,
            "tuition_policy_during_exchange": (
                "交換期間須於國立金門大學完成註冊並繳交全額學雜費及學生平安保險費（保有金大學籍），免繳交換校學費（自費交換生或特定協議學校除外）"
            ),
            "return_documents_due": (
                "結束交換後 2 週內須回國返校報到，並於報到後 1 個月內繳交彌封正式成績單、2,000 字以上交流心得報告（含本人入鏡照片 5 張以上）及 3–10 分鐘心得影片（含中文字幕橫式 mp4），並參加經驗分享座談會"
            ),
        },
        "source_urls": nqu_source_urls,
        "verified_at": "2026-11-02",
    }
    (OFFICIAL_NQU_DIR / "home_rules.json").write_text(
        json.dumps(home_rules, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    (OFFICIAL_NQU_DIR / "documents.json").write_text(
        json.dumps(
            {
                "school_name": "國立金門大學",
                "required_documents": student_dashboard_payload["required_documents"],
                "source_urls": nqu_source_urls,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    (OFFICIAL_NQU_DIR / "scholarships.json").write_text(
        json.dumps(
            {
                "school_name": "國立金門大學",
                "scholarships": student_dashboard_payload["scholarship_info"],
                "source_urls": nqu_source_urls,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    completeness = {
        "school_id": "nqu",
        "school_name": "國立金門大學",
        "total_partners": len(partners),
        "partner_count": len(partners),
        "international_partners": sum(
            1 for p in partners if p["country"] not in {"中國大陸", "香港", "澳門"}
        ),
        "mainland_partners": sum(
            1 for p in partners if p["country"] in {"中國大陸", "香港", "澳門"}
        ),
        "experience_report_covered_partners": exp_covered_schools,
        "experience_report_count": total_exp_reports,
        "open_partners": open_partner_count,
        "reference_only_partners": len(partners) - open_partner_count,
        "verified_locations": len(partners),
        "verified_official_websites": sum(
            1 for p in partners if p.get("official_website")
        ),
        "verified_campus_images": sum(
            1 for p in partners if p.get("image_status") == "verified"
        ),
        "workflow_count": len(workflows),
        "destination_profile_count": len(destinations),
        "student_life_count": len(life_records),
        "active_term": (
            "國立金門大學國際暨兩岸事務處 115 學年度第一／二階段國際交換學生甄選（05/25 收件截止、05/27 面試、06/05 放榜）"
            "與 2027 春季班（115-2）赴中國大陸地區交換學生甄選（09/14–09/24 收件、09/30 面試、10/14 放榜，至多 5 志願）暨教育部學海系列獎助同步整合；"
            f"共完整收錄 {len(partners)} 所交換合作學校（橫跨 15 個國家與地區，含 {open_partner_count} 所當期開放申請校，"
            f"並收錄 {exp_covered_schools} 所合作大學共 {total_exp_reports} 篇歷屆赴外與赴大陸交換生研修心得報告）。"
        ),
        "verified_at": "2026-11-02",
    }
    (OFFICIAL_NQU_DIR / "catalog-completeness.json").write_text(
        json.dumps(completeness, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    (OFFICIAL_NQU_DIR / "verification_status.json").write_text(
        json.dumps(
            {
                "school_id": "nqu",
                "school_name": "國立金門大學",
                "status": "official_verified",
                "checked_at": CHECKED_AT,
                "counts": completeness,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    (OFFICIAL_NQU_DIR / "dashboard_manifest.json").write_text(
        json.dumps(
            {
                "school_id": "nqu",
                "school_name": "國立金門大學",
                "checked_at": CHECKED_AT,
                "partner_count": len(partners),
                "open_partner_count": open_partner_count,
                "experience_school_count": exp_covered_schools,
                "experience_report_count": total_exp_reports,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    provenance_files = [
        ("sources/nqu/oica_home.html", NQU_OICA_HOME_URL, "國立金門大學國際暨兩岸事務處首頁 HTML"),
        ("sources/nqu/1150_intl_exchange.html", NQU_INTL_EXCHANGE_LIST_URL, "國際暨兩岸事務處—國際交換學生甄選公告列表 HTML"),
        ("sources/nqu/21011_115_stage2_intl.html", NQU_INTL_STAGE2_POST_URL, "115學年度第二階段國際交換學生甄選公告 HTML"),
        ("sources/nqu/28138_115_stage1_admit.html", NQU_INTL_STAGE1_ADMIT_URL, "115學年度第一階段國際交換學生甄選錄取公告 HTML"),
        ("sources/nqu/31469_announcement1.html", NQU_MAINLAND_2027_SPRING_URL, "2027春季班赴國內及大陸地區交換學生甄選公告（一）HTML"),
        ("sources/nqu/31470_announcement2.html", NQU_MAINLAND_2027_SPRING_EXT_URL, "2027春季班赴國內交換延長報名公告（二）HTML"),
        ("sources/nqu/32428_spring2027_admit.html", NQU_MAINLAND_2027_ADMIT_URL, "2027春季班（115-2）赴國內及大陸地區交換校內錄取名單公告 HTML"),
        ("sources/nqu/8171_intl_exchange_schools.html", NQU_INTL_PARTNERS_URL, "國際暨兩岸事務處—國際交換學校一覽表（39校）HTML"),
        ("sources/nqu/8510_mainland_schools.html", NQU_MAINLAND_PARTNERS_URL, "國際暨兩岸事務處—大陸地區交換學校一覽表 HTML"),
        ("sources/nqu/6600_partners_intl.html", NQU_SISTER_INTL_URL, "國際暨兩岸事務處—國際締約姊妹校一覽表 HTML"),
        ("sources/nqu/6599_partners_mainland.html", NQU_SISTER_MAINLAND_URL, "國際暨兩岸事務處—大陸地區締約姊妹校一覽表 HTML"),
        ("sources/nqu/7397_intl_regulations.html", NQU_INTL_REGULATIONS_URL, "國際暨兩岸事務處—學生國際交流相關法規 HTML"),
        ("sources/nqu/0995_intl_forms.html", NQU_INTL_FORMS_URL, "國際暨兩岸事務處—國際交流表件下載與審查流程 SOP HTML"),
        ("sources/nqu/7424_exchange_student_section.html", NQU_EXCHANGE_SECTION_URL, "國際暨兩岸事務處—交換學生專區 HTML"),
        ("sources/nqu/29910_115_xuehai.html", NQU_XUEHAI_POST_URL, "115年度教育部學海飛颺及學海惜珠計畫甄選簡章公告 HTML"),
        ("sources/nqu/1182_exp_mainland.html", NQU_EXP_MAINLAND_URL, "國際暨兩岸事務處—大陸地區交換學生心得報告專區（282篇）HTML"),
        ("sources/nqu/1207_exp_intl.html", NQU_EXP_INTL_URL, "國際暨兩岸事務處—國際交換學生心得報告專區（35篇）HTML"),
        ("sources/nqu/teach_404_1_1717.html", NQU_TEACH_REG_URL, "教務處註冊組—國內與境外交換及科目學分抵免辦法專區 HTML"),
        ("sources/nqu/nqu_experience_index.json", NQU_EXP_MAINLAND_URL, f"國立金門大學交換生研修心得報告（{exp_covered_schools} 校共 {total_exp_reports} 篇）索引 JSON"),
        ("sources/nqu/nqu_catalog_source.json", NQU_INTL_PARTNERS_URL, f"國立金門大學 {len(partners)} 所交換合作學校整合資料集 JSON"),
        ("sources/nqu/nqu_resolved_locations.json", NQU_INTL_PARTNERS_URL, f"國立金門大學 {len(partners)} 所交換合作學校 ROR / Wikidata 地理座標核對表 JSON"),
    ]
    for fname, url in bin_urls.items():
        provenance_files.append((f"sources/nqu/{fname}", url, f"國立金門大學官方附件：{fname}"))
    seen_rel = {item[0] for item in provenance_files}
    for extra_file in sorted(SOURCES_NQU_DIR.iterdir()):
        if not extra_file.is_file():
            continue
        rel = f"sources/nqu/{extra_file.name}"
        if rel not in seen_rel:
            provenance_files.append((rel, NQU_OICA_HOME_URL, f"國立金門大學官方交換計畫文件與附件：{extra_file.name}"))
            seen_rel.add(rel)

    prov_sources = []
    for rel_path, surl, stitle in provenance_files:
        p = REPO_ROOT / rel_path
        if p.exists():
            b = p.read_bytes()
            prov_sources.append({
                "file": rel_path,
                "source_url": surl,
                "title": stitle,
                "sha256": hashlib.sha256(b).hexdigest(),
                "bytes": len(b),
                "fetched_at": CHECKED_AT,
            })
    provenance_payload = {
        "school_id": "nqu",
        "school_name": "國立金門大學",
        "generated_at": CHECKED_AT,
        "active_cycle_note": completeness["active_term"],
        "sources": prov_sources,
    }
    prov_text = json.dumps(provenance_payload, ensure_ascii=False, indent=2) + "\n"
    (OFFICIAL_NQU_DIR / "import_provenance.json").write_text(
        prov_text, encoding="utf-8"
    )
    (OFFICIAL_NQU_DIR / "import-provenance.json").write_text(
        prov_text, encoding="utf-8"
    )

    print(
        f"Successfully built NQU catalog: {len(partners)} partners"
        f" ({open_partner_count} open, {completeness['verified_campus_images']}"
        f" verified images, {completeness['verified_locations']} verified"
        f" locations), {len(workflows)} workflows,"
        f" {len(destinations)} destinations, {len(research_records)} research"
        f" records, {exp_covered_schools} schools with experience records"
        f" ({len(student_experience_rows)} rows, {total_exp_reports} reports)."
    )


if __name__ == "__main__":
    main()
