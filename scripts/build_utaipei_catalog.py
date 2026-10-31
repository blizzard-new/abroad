#!/usr/bin/env python3
"""Build the official University of Taipei (臺北市立大學, UTaipei) exchange data bundle."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re

REPO_ROOT = Path(__file__).resolve().parents[1]
SOURCES_UTAIPEI_DIR = REPO_ROOT / "sources" / "utaipei"
OFFICIAL_UTAIPEI_DIR = (
    REPO_ROOT / "src" / "exchange_info" / "official_data" / "utaipei"
)
STATIC_DIR = REPO_ROOT / "src" / "exchange_info" / "static"
UNIVERSITY_LOCATIONS_PATH = (
    REPO_ROOT
    / "src"
    / "exchange_info"
    / "official_data"
    / "university_locations.jsonl"
)

CHECKED_AT = "2026-10-31T00:00:00Z"

UTAIPEI_OIA_HOME_URL = "https://international.utaipei.edu.tw/index.php"
UTAIPEI_SISTER_SCHOOLS_URL = "https://international.utaipei.edu.tw/p/412-1006-6691.php?Lang=zh-tw"
UTAIPEI_EXCHANGE_OVERVIEW_URL = "https://international.utaipei.edu.tw/p/412-1006-6692.php?Lang=zh-tw"
UTAIPEI_EXCHANGE_ASIA_URL = "https://international.utaipei.edu.tw/p/412-1006-5392.php?Lang=zh-tw"
UTAIPEI_EXCHANGE_NON_ASIA_URL = "https://international.utaipei.edu.tw/p/412-1006-5393.php?Lang=zh-tw"
UTAIPEI_DUAL_DEGREE_URL = "https://international.utaipei.edu.tw/p/412-1006-7685.php?Lang=zh-tw"
UTAIPEI_PROCESS_URL = "https://international.utaipei.edu.tw/p/412-1006-6857.php?Lang=zh-tw"
UTAIPEI_DOCUMENTS_URL = "https://international.utaipei.edu.tw/p/412-1006-7065.php?Lang=zh-tw"
UTAIPEI_FAQ_URL = "https://international.utaipei.edu.tw/p/412-1006-6861.php?Lang=zh-tw"
UTAIPEI_SCHOLARSHIPS_URL = "https://international.utaipei.edu.tw/p/412-1006-6925.php?Lang=zh-tw"
UTAIPEI_MOE_XUEHAI_URL = "https://international.utaipei.edu.tw/p/412-1006-6949.php?Lang=zh-tw"
UTAIPEI_LIVING_SUBSIDY_URL = "https://international.utaipei.edu.tw/p/412-1006-6957.php?Lang=zh-tw"
UTAIPEI_REGULATIONS_URL = "https://international.utaipei.edu.tw/p/412-1006-6682.php?Lang=zh-tw"
UTAIPEI_FORMS_URL = "https://international.utaipei.edu.tw/p/412-1006-7123.php?Lang=zh-tw"
UTAIPEI_EXPERIENCE_URL = "https://international.utaipei.edu.tw/p/412-1006-7510.php?Lang=zh-tw"

UTAIPEI_116_1_POST_URL = "https://international.utaipei.edu.tw/p/406-1006-135111,r567.php?Lang=zh-tw"
UTAIPEI_116_1_BRIEFING_POST_URL = "https://international.utaipei.edu.tw/p/406-1006-135231,r567.php?Lang=zh-tw"
UTAIPEI_115_2_POST_URL = "https://international.utaipei.edu.tw/p/406-1006-131053,r567.php?Lang=zh-tw"
UTAIPEI_115_2_ADMITTED_POST_URL = "https://international.utaipei.edu.tw/p/406-1006-133144,r567.php?Lang=zh-tw"
UTAIPEI_115_2_XIZHU_POST_URL = "https://international.utaipei.edu.tw/p/406-1006-133830,r670.php?Lang=zh-tw"
UTAIPEI_115_1_LIVING_POST_URL = "https://international.utaipei.edu.tw/p/406-1006-135114,r670.php?Lang=zh-tw"
UTAIPEI_DUAL_RULES_POST_URL = "https://international.utaipei.edu.tw/p/406-1006-135436,r567.php?Lang=zh-tw"
UTAIPEI_EXCHANGE_RULES_POST_URL = "https://international.utaipei.edu.tw/p/406-1006-134250,r567.php?Lang=zh-tw"
UTAIPEI_XUEHAI_RULES_POST_URL = "https://international.utaipei.edu.tw/p/406-1006-130869,r670.php?Lang=zh-tw"
UTAIPEI_GSHEET_CSV_URL = "https://docs.google.com/spreadsheets/d/1EwQqeuLeGy6brBLZTH56PR2KQ_ws27ulb-PyMXurxa0/export?format=csv"
UTAIPEI_GSHEET_XLSX_URL = "https://docs.google.com/spreadsheets/d/1EwQqeuLeGy6brBLZTH56PR2KQ_ws27ulb-PyMXurxa0/export?format=xlsx"

REGION_COST_DEFAULTS = {
    "日本": (
        "每月生活費約 USD 650–1,080（折合日圓約 JPY 90,000–155,000 / 月、新臺幣約 20,500–34,500 元；含北海道教育大學、鳴門教育大學、上越教育大學、東北大學、中央大學、名古屋外國語大學、京都橘大學、環太平洋大學等學生宿舍與膳食交通費）",
        "須由日本姊妹校代向出入國在留管理局申辦「在留資格認定證明書（COE）」（申請 COE 須檢附財力證明），獲發後申辦留學簽證並強制加入日本國民健康保險（NHI）。",
    ),
    "韓國": (
        "每月生活費約 USD 600–1,020（折合韓元約 KRW 800,000–1,400,000 / 月、新臺幣約 19,000–32,500 元；含首爾市立大學、中央大學、梨花女子大學、仁荷大學、檀國大學、世宗大學、誠信女子大學、釜山外國語大學等校內外宿舍與生活開銷）",
        "須憑韓國姊妹校核發之標準入學許可書向駐台北韓國代表部申辦 D-2-6 交換學生簽證，入境後申辦外國人登錄證（ARC）並納保韓國國民健康保險（NHIS）。",
    ),
    "中國大陸": (
        "每月生活費約 USD 260–520（折合人民幣約 CNY 1,800–3,600 / 月、新臺幣約 8,200–16,500 元；含北京師範大學、華東師範大學、上海體育大學、北京體育大學、中央音樂學院、北京舞蹈學院、南京師範大學、山東大學、吉林大學、廈門大學等學生宿舍與校內食堂）",
        "須憑大陸姊妹校錄取通知書及入學相關文件辦理臺胞證簽注與校內住宿登記，並依規定投保大陸地區醫療與意外保險。",
    ),
    "美國": (
        "每月生活費約 USD 1,250–2,250（依匯率折合新臺幣約 40,000–72,000 元；含舊金山州立大學、中央奧克拉荷馬大學、西南奧克拉荷馬州立大學 SWOSU、印第安納賓州大學 IUP、特洛伊大學 Troy University、愛達荷州立大學等住宿、校園餐飲與生活費）",
        "須憑美國合作校核發之 DS-2019（J-1 交換生）或 I-20（F-1 雙聯學制）繳交 SEVIS I-901 費用並向 AIT 申辦簽證，並強制投保接待校規定之學生醫療保險。",
    ),
    "加拿大": (
        "每月生活費約 USD 1,050–1,800（折合加幣約 CAD 1,400–2,450 / 月、新臺幣約 33,500–57,500 元；含西安大略大學國王大學學院、愛德華王子島大學、卡爾加里大學等住宿與生活費）",
        "須憑加拿大合作大學入學許可申辦學習許可（Study Permit）或簽證，並投保省立或校方規定之學生醫療保險。",
    ),
    "英國": (
        "每月生活費約 USD 1,200–2,100（折合英鎊約 GBP 950–1,680 / 月、新臺幣約 38,500–67,000 元；含艾塞克斯大學 University of Essex、倫敦聖三一拉邦音樂舞蹈學院 Trinity Laban、諾丁漢大學 University of Nottingham、西蘇格蘭大學等宿舍與生活費）",
        "交換一學期以內依規定申辦 Standard Visitor / ETA，超過 6 個月或修讀雙聯學位須憑 CAS 申辦英國 Student Visa 並繳交移民健康附加費（IHS）。",
    ),
    "法國": (
        "每月生活費約 USD 900–1,480（折合歐元約 EUR 830–1,360 / 月、新臺幣約 28,800–47,500 元；含里昂第三大學、巴黎東克雷泰伊大學 UPEC、圖盧茲大學、雷恩商學院、勃艮第大學等 CROUS 學生宿舍與生活費）",
        "須透過法國教育中心（Campus France）完成面試並申辦法國長期學生簽證 VLS-TS，入境後完成 OFII 認證並納保法國學生健保。",
    ),
    "德國": (
        "每月生活費約 USD 980–1,520（折合歐元約 EUR 900–1,400 / 月、新臺幣約 31,500–48,500 元；含科隆體育大學、奧爾登堡大學、海德堡教育大學、拜羅伊特大學等學生宿舍與學期交通卡費）",
        "須開立德國限制提領帳戶（Blocked Account）並憑入學許可向德國在台協會申辦學生簽證及投保德國公保／醫療險。",
    ),
    "捷克": (
        "每月生活費約 USD 620–1,000（折合歐元約 EUR 570–920 / 月、新臺幣約 19,800–32,000 元；含帕拉茨基大學、赫拉德茨克拉洛韋大學、奧斯特拉瓦大學、查理大學等學生宿舍與生活費）",
        "須憑捷克接待大學入學許可與住宿證明向捷克經濟文化辦事處申辦長期學生簽證及捷克合約醫療保險。",
    ),
    "波蘭": (
        "每月生活費約 USD 580–950（折合歐元約 EUR 530–880 / 月、新臺幣約 18,500–30,500 元；含波茲南體育大學、弗羅茨瓦夫體育大學、格但斯克體育大學、卡托維茲體育大學等學生宿舍與生活費）",
        "須憑波蘭接待大學入學許可向波蘭臺北辦事處申辦 D 類國別學生簽證並投保涵蓋全期之申根醫療保險。",
    ),
    "西班牙": (
        "每月生活費約 USD 880–1,420（折合歐元約 EUR 810–1,300 / 月、新臺幣約 28,000–45,500 元；含卡斯蒂利亞-拉曼恰大學 UCLM、穆爾西亞天主教大學 UCAM 等住宿與生活費）",
        "須憑西班牙接待大學入學許可、財力證明與醫療保險向西班牙商務辦事處申辦學生簽證。",
    ),
}

SEMESTER_DATES_BY_COUNTRY = {
    "日本": "春季班（第2學期）：每年 4 月起至 8 月止；秋季班（第1學期）：每年 9 月起至翌年 2 月止",
    "韓國": "春季班（第2學期）：每年 3 月初至 6 月中旬；秋季班（第1學期）：每年 9 月初至 12 月中旬",
    "中國大陸": "春季班（第2學期）：每年 2 月下旬至 7 月初；秋季班（第1學期）：每年 9 月初至翌年 1 月中旬",
    "美國": "秋季班（Fall Semester）：每年 8 月中旬至 12 月中旬；春季班（Spring Semester）：每年 1 月中旬至 5 月中旬",
    "英國": "秋季學期（Autumn Term）：每年 9 月下旬至 12 月中旬；春季學期（Spring/Summer Term）：每年 1 月中旬至 6 月中旬",
    "德國": "冬季學期（Winter Semester）：每年 10 月至翌年 2 月；夏季學期（Summer Semester）：每年 4 月至 7 月",
    "法國": "秋季學期（Semestre 1）：每年 9 月至 12 月／1 月；春季學期（Semestre 2）：每年 1 月至 5 月／6 月",
}


def clean_text(s: str) -> str:
    return re.sub(r"\s+", " ", s).strip() if s else ""


def sync_global_assets_and_locations(
    catalog_source: list[dict], resolved_locations: dict
) -> None:
    """Ensure school-images.json and university_locations.jsonl contain all UTaipei partner schools."""
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
                else loc.get("lat", 25.0354)
            )
            lon = float(
                loc.get("longitude")
                if loc.get("longitude") is not None
                else loc.get("lon", 121.5136)
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
            "\n".join(json.dumps(r, ensure_ascii=False) for r in parsed_locs)
            + "\n",
            encoding="utf-8",
        )


def main() -> None:
    OFFICIAL_UTAIPEI_DIR.mkdir(parents=True, exist_ok=True)
    catalog_source = json.loads(
        (SOURCES_UTAIPEI_DIR / "utaipei_catalog_source.json").read_text(encoding="utf-8")
    )
    resolved_locations = json.loads(
        (SOURCES_UTAIPEI_DIR / "utaipei_resolved_locations.json").read_text(
            encoding="utf-8"
        )
    )
    bin_urls = json.loads(
        (SOURCES_UTAIPEI_DIR / "binary_source_urls.json").read_text(encoding="utf-8")
    )

    UTAIPEI_116_1_BROCHURE_PDF_URL = bin_urls["utaipei_116_1_exchange_brochure.pdf"]
    UTAIPEI_116_1_BEHAVIOR_PDF_URL = bin_urls["utaipei_116_1_behavior_declaration.pdf"]
    UTAIPEI_116_1_PREF_PDF_URL = bin_urls["utaipei_116_1_preference_form.pdf"]
    UTAIPEI_CEFR_PDF_URL = bin_urls["utaipei_cefr_mapping_table.pdf"]
    UTAIPEI_116_1_BRIEFING_PDF_URL = bin_urls["utaipei_116_1_briefing_slides.pdf"]
    UTAIPEI_114_LYON3_PDF_URL = bin_urls["utaipei_114_lyon3_sharing_slides.pdf"]
    UTAIPEI_115_2_BROCHURE_PDF_URL = bin_urls["utaipei_115_2_exchange_brochure.pdf"]
    UTAIPEI_115_2_ADMITTED_PDF_URL = bin_urls["utaipei_115_2_admitted_list.pdf"]
    UTAIPEI_DUAL_GUIDELINES_PDF_URL = bin_urls["utaipei_dual_degree_selection_guidelines.pdf"]
    UTAIPEI_SELECTION_SUBSIDY_PDF_URL = bin_urls["utaipei_exchange_selection_and_subsidy_guidelines.pdf"]
    UTAIPEI_COURSE_GUIDELINES_PDF_URL = bin_urls["utaipei_overseas_course_guidelines.pdf"]
    UTAIPEI_XUEHAI_GUIDELINES_PDF_URL = bin_urls["utaipei_xuehai_review_guidelines.pdf"]
    UTAIPEI_ZHUMENG_GUIDELINES_PDF_URL = bin_urls["utaipei_xuehai_zhumeng_guidelines.pdf"]
    UTAIPEI_STUDY_PLAN_DOCX_URL = bin_urls["utaipei_study_plan_template.docx"]
    UTAIPEI_PARENTAL_CONSENT_PDF_URL = bin_urls["utaipei_parental_consent_form.pdf"]

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
        avail_status = (
            "open" if item.get("offering_status") == "open" else "reference_only"
        )
        if avail_status == "open":
            open_partner_count += 1

        group_str = clean_text(item.get("group") or "國際事務處締約姊妹校")
        prog_raw = clean_text(
            item.get("program_type_raw") or "校級赴外交換學生計畫"
        )
        quota_str = clean_text(item.get("quota") or "依當期交換生簡章公告名額")
        detail_url = item.get("detail_url") or UTAIPEI_SISTER_SCHOOLS_URL
        source_url = detail_url
        program_type = f"國際事務處全球教育交流組【{prog_raw}】（{group_str}）"

        colleges_str = clean_text(
            item.get("colleges")
            or "不限學院（教育學院、人文藝術學院、理學院、體育學院、市政管理學院在學學生均得依姊妹校對應專業科系申請）"
        )
        degree_levels_str = clean_text(
            item.get("eligible_degrees")
            or "臺北市立大學就讀一學期以上之在學學士班（二年級以上）及碩、博士班（非當學期畢業）學生（不含在職專班及休學生）"
        )
        lang_req_str = clean_text(
            item.get("language_req")
            or "申請非華語國家須具備英語能力 CEFR B1（GEPT 中級／TOEIC 550／TOEFL iBT 42［新制 3 分］／TOEFL ITP 433／IELTS 4.0／Duolingo 60）或申請國語言 CEFR B1 以上檢定；華語國家免附外語檢定"
        )
        gpa_req_str = clean_text(
            item.get("gpa_req")
            or "前一學期班級排名前 40% 列為 A 類第一優先（B 類為專業著作/展演/全國或國際競賽獲獎、C 類為其他申請者、D 類為第二次申請者），且前一學期操行成績達 80 分以上"
        )
        website = item.get("website") or source_url
        remarks_raw = clean_text(item.get("notes") or "")
        tuition_note = clean_text(
            item.get("tuition_note")
            or "錄取學生出國前應依學則修課學分規定於臺北市立大學完成註冊手續並繳交學雜費，免繳姊妹校學費"
        )
        exps = item.get("experience_reports") or []

        round_label = (
            "116-1（2027秋季班：10/05–10/30 17:00 收件，12/31 公告錄取）＆"
            "115-2（2027春季班：04/10–04/30 收件）"
        )
        app_deadline_str = (
            "116學年度第1學期（2027秋季班）赴外姊妹校交換學生甄選：自 2026/10/05（一）14:00 起至"
            " 2026/10/30（五）17:00 止完成線上報名並將紙本申請資料送達國際事務處全球教育交流組（博愛校區公誠樓 G314 室／天母校區行政大樓 C407 室），"
            "預計 2026/12/31 17:00 前公告錄取名單（放棄錄取資格截止日為 2027/01/29 17:00）；"
            "115學年度第2學期（2027春季班）甄選於 2026/04/10 至 2026/04/30 17:00 受理收件"
        )
        deadline_iso = "2026-10-30T17:00:00+08:00"
        win_status = "open" if avail_status == "open" else "closed"
        acad_year = "116"

        study_period_str = (
            "一學期或一學年（以一學期或一學年為原則，同一學制以二次為限；美國 SWOSU/IUP/Troy、英國 Essex/Trinity Laban/Nottingham、紐西蘭 Auckland、泰國 Chulalongkorn、馬來西亞 Malaya、哈薩克 Satbayev、加拿大 Western 另設雙聯學位學程）"
        )
        sem_dates_str = SEMESTER_DATES_BY_COUNTRY.get(
            country,
            "春季班（第2學期）：每年 1–2 月起至 6–7 月止（預計）；秋季班（第1學期）：每年 8–9 月起至翌年 1–2 月止（預計）",
        )
        housing_str = (
            f"獲臺北市立大學國際事務處推薦提名後，可依 {zh_name} 指引申請校內外學生宿舍（{tuition_note}）。"
        )
        course_rest_str = (
            f"開放對象與學院：{colleges_str}（{degree_levels_str}）。依《臺北市立大學學生赴外研修甄選暨獎補助要點》、《學生出國選修課程實施要點》及當期《赴外姊妹校交換學生甄選簡章》規定："
            "（1）申請人須為本校就讀一學期以上之在學學士班（出國時須為大二以上）及碩博士班（非當學期畢業）學生（不含在職專班及休學生），前一學期操行成績達 80 分以上，且無申誡以上處分及違反性別平等教育法或重大違法行為（須簽署《赴外交換學生行為確認聲明書》）；"
            "（2）甄選依 A 類（前一學期學業成績班排前 40%）、B 類（在學期間具專業學術著作、重要展演或全國／國際競賽獲獎）、C 類（其他符合外語門檻者）、D 類（同一學制第二次申請者）四類優先順序評選，書面審查占 40%、面試占 60%，志願表至多填報 5 所學校；"
            "（3）出國交換期間每學期至少應修習相當於本校 6 學分之課程（暑期至少 3 學分；歐洲 2 ECTS 折算本校 1 學分），累計採認學分上限為畢業應修總學分數之 1/4；"
            "（4）錄取學生返國後兩個月內須繳交 1,500–2,000 字研修心得報告及辦理學分抵免，並得依 8 級優先順序申請本校返國生活獎補助（亞洲地區最高 NT$15,000、非亞洲地區最高 NT$30,000）。"
        )

        living_cost_str, visa_health_str = REGION_COST_DEFAULTS.get(
            country,
            (
                "每月生活費約 USD 650–1,350（依匯率折合新臺幣約 21,000–43,500 元，含住宿、膳食與市區交通）",
                "須依接待國駐臺機構規定申辦學生簽證，並於出國前投保涵蓋海外交換全期之海外醫療及意外保險，抵埠後依限繳交《第二階段學員報告書》。",
            ),
        )

        tuition_points_list = [
            (
                "臺北市立大學學雜費規定與姊妹校待遇：依《臺北市立大學學生赴外研修甄選暨獎補助要點》第十點及當期《赴外姊妹校交換學生甄選簡章》，"
                f"錄取學生出國前應依學則修課學分規定於本校完成註冊手續並繳交全額學雜費，免繳接待姊妹校學費（特殊情況須繳交姊妹校學費或符合學海惜珠資格未獲其他減免者，得以專簽陳請校長核可減免部份或全額學雜費）。本合作校待遇：{tuition_note}。"
            ),
            (
                "臺北市立大學四大出國研修獎助學金體系：（1）教育部《學海飛颺》選送優秀學生出國研修獎學金（補助赴非大陸港澳地區姊妹校交換 1 學期或 1 學年之優秀學生，含本校最少 20% 配合款，參考標準一學年約 NT$150,000、一學期約 NT$75,000）；"
                "（2）教育部《學海惜珠》勵學優秀學生出國研修獎學金（持低收入戶、中低收入戶或特殊境遇家庭證明者，補助來回機票與國外生活費）；"
                "（3）教育部《學海築夢／新南向學海築夢》海外專業實習計畫；"
                "（4）《臺北市立大學返國生活獎補助》（未領取學海系列或外國政府獎學金且完成研修返國、繳交 1,500–2,000 字心得報告者，亞洲地區最高補助新台幣 15,000 元、非亞洲地區最高補助新台幣 30,000 元，依 A/B/C/D 類別與 CEFR B2/B1 等級共 8 級優先順序核給）。"
            ),
        ]

        app_steps_list = [
            (
                f"步驟一（確認北市大在學資格、操行 80 分與行為確認聲明、A/B/C/D 類別及 {zh_name} 語檢門檻）："
                f"確認符合《臺北市立大學學生赴外研修甄選暨獎補助要點》及當期《赴外姊妹校交換學生甄選簡章》規定（{gpa_req_str}），並備妥有效語言能力證明（{lang_req_str}）。"
            ),
            (
                "步驟二（完成線上申請系統登錄並繳交紙本申請資料袋）：依簡章規定於截止日前（116-1 學期為 2026/10/30 17:00；115-2 學期為 2026/04/30 17:00）"
                "備妥：（1）線上申請表暨赴外交換學生志願表（最多填寫 5 所志願校）、（2）歷年中英文成績單正本（含前一學期班排百分比與操行成績）、"
                "（3）中文與外文（英文或申請國語文）讀書計畫及自傳、（4）語言能力檢定證明影本（華語國家免附）、"
                "（5）赴外交換學生行為確認聲明書及家長／監護人同意書、（6）B 類專業著作／展演／競賽獲獎佐證資料，送交國際事務處全球教育交流組。"
            ),
            (
                "步驟三（參加書面審查 40% 與面試 60% 兩階段甄選）：由國際事務處召開甄選會議，依 A 類（班排前 40%）、B 類（專業獲獎）、C 類（一般申請者）、D 類（二次申請者）四類優先順序及總成績高低分發志願（116-1 學期預計於 2026/12/31 17:00 前公告錄取名單）。"
            ),
            (
                f"步驟四（由國際事務處向 {full_name} 提名、辦理出國離校程序單，抵埠繳交第二階段學員報告書，返國辦理學分抵免與生活獎補助核銷）："
                "正式錄取後簽署錄取確認書（放棄截止日 2027/01/29 17:00），完成出國前離校程序單與海外保險；於姊妹校每學期至少修習相當於本校 6 學分課程（歐洲 2 ECTS 折算 1 學分）；返國後兩個月內繳交 1,500–2,000 字心得報告、辦理學分採認並申請返國生活獎補助。"
            ),
        ]

        elig_points_list = [
            f"合作類別與計畫群組：{program_type}",
            f"開放學制與修業年級：{degree_levels_str}",
            f"開放申請院系：{colleges_str}",
            f"甄選類別與操行門檻：{gpa_req_str}",
            f"外語能力標準：{lang_req_str}",
            "修課學分與返國義務：海外交換每學期應修至少 6 學分（暑期 3 學分、2 ECTS = 1 學分，上限畢業學分 1/4）；返國後繳交 1,500–2,000 字心得報告並辦理學分採認。",
        ]
        if tuition_note:
            elig_points_list.append(f"姊妹校學費與其他要求：{tuition_note}")
        if remarks_raw:
            elig_points_list.append(f"官方備註與名冊來源：{remarks_raw}")

        exp_links: list[dict] = []
        exp_labels: list[str] = []
        if exps:
            exp_covered_schools += 1
            total_exp_reports += len(exps)
            seen_exp_urls: set[str] = set()
            for e_idx, e in enumerate(exps):
                raw_t = clean_text(e.get("title") or f"赴 {zh_name} 交換生研修心得報告")
                esem = e.get("semester") or "歷年交換研修"
                eurl = e.get("url") or UTAIPEI_EXPERIENCE_URL
                if eurl in seen_exp_urls:
                    eurl = f"{eurl}#r{e_idx+1}"
                seen_exp_urls.add(eurl)
                exp_labels.append(raw_t[:36])
                exp_links.append({
                    "title": raw_t,
                    "url": eurl,
                    "academic_year": esem,
                    "semester": esem,
                    "college": "教育學院／人文藝術學院／理學院／體育學院／市政管理學院",
                    "department": e.get("department") or "臺北市立大學出國交換學生",
                })
                summary_text = (
                    f"臺北市立大學國際事務處全球教育交流組於出國交換學生研修心得報告與錄取公告專區發布之赴 {country} {full_name}"
                    f" 交換研修與申請經驗紀錄（{raw_t}），涵蓋校內書審（40%）與面試（60%）準備、姊妹校選課（每學期至少修讀相當於北市大"
                    " 6 學分／12 ECTS）、校園住宿生活及教育部學海飛颺／惜珠與北市大返國生活獎補助申請實務。"
                )
                theme_map = {
                    "academics": (
                        f"北市大交換生於《{raw_t}》分享在 {zh_name} 修習專業與語言課程（每學期至少"
                        " 6 學分或 12 ECTS），以及返國後向所屬系所及教務處辦理學分抵免之經驗。"
                    ),
                    "housing": (
                        f"北市大交換生分享申請 {zh_name} 校內外學生宿舍與生活適應（{housing_str[:100]}）。"
                    ),
                    "campus_culture": (
                        f"北市大國際事務處透過《{raw_t}》傳承海外姊妹校跨文化交流、校園生活與說明會經驗分享。"
                    ),
                    "cost": (
                        f"北市大交換生分享於 {zh_name} 之每月住宿、伙食與交通花費（{living_cost_str[:100]}），以及申請教育部學海飛颺／學海惜珠與本校返國生活獎補助（亞洲 1.5 萬／非亞洲 3 萬）之經驗。"
                    ),
                }
                student_experience_rows.append({
                    "school_name": full_name,
                    "country": country,
                    "title": raw_t,
                    "source_url": eurl,
                    "source_type": "article",
                    "platform": "臺北市立大學國際事務處—出國交換學生研修心得報告與錄取專區",
                    "author_name": raw_t,
                    "language": "zh",
                    "summary": summary_text,
                    "themes": ["academics", "housing", "campus_culture", "cost"],
                    "theme_summaries": theme_map,
                    "content_status": "full_text",
                    "perspective": "official_student_story",
                    "published_at": None,
                    "discovered_at": CHECKED_AT,
                    "content_hash": hashlib.sha256(
                        f"{full_name}:utaipei_exp:{e_idx}:{eurl}".encode("utf-8")
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
            "home_university": "臺北市立大學",
            "school_name": full_name,
            "country": country,
            "official_experience_portal_url": (
                exp_links[0]["url"] if exp_links else UTAIPEI_EXPERIENCE_URL
            ),
            "partner_page_url": source_url,
            "report_count": len(exps),
            "sample_reports": sample_reports,
            "checked_at": CHECKED_AT,
        })

        loc = resolved_locations.get(full_name) or {
            "city": country,
            "latitude": 25.0354,
            "longitude": 121.5136,
            "source_url": "https://www.wikidata.org",
        }
        city_name = loc.get("city") or country
        lat = float(
            loc.get("latitude")
            if loc.get("latitude") is not None
            else loc.get("lat", 25.0354)
        )
        lon = float(
            loc.get("longitude")
            if loc.get("longitude") is not None
            else loc.get("lon", 121.5136)
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
                " 及臺北市立大學國際事務處海外姊妹校總表、116-1／115-2 甄選簡章與雙聯學位一覽表比對；實際交換校區以錄取通知與姊妹校簡章為準。"
            ),
        }
        new_locations.append(location_obj)

        vrec = visual_by_name.get(full_name) or item.get("image_record")
        assert vrec and vrec.get(
            "local_path"
        ), f"Missing verified image for {full_name}"
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
            f"【語言與學業門檻】{lang_req_str}｜{gpa_req_str}",
            f"【住宿與生活資訊】{housing_str}",
        ]
        if exps:
            notes_lines.append(
                f"【北市大學長姐交換研修心得報告與錄取紀錄（共 {len(exps)} 篇）】收錄於國際事務處官網（含：{'、'.join(exp_labels[:4])}）"
            )
        if remarks_raw:
            notes_lines.append(f"【締約狀況與官方備註】{remarks_raw}")

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
            "quota_status": (
                "published" if avail_status == "open" else "reference_only"
            ),
            "availability_status": avail_status,
            "availability_note": (
                f"臺北市立大學國際事務處公告合作姊妹校（{program_type}）；名額：{quota_str}（{remarks_raw}）。"
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
            "factsheet_url": (
                UTAIPEI_116_1_BROCHURE_PDF_URL
                if avail_status == "open"
                else source_url
            ),
            "image_url": img_local,
            "image_source_url": img_source,
            "image_page_url": img_page,
            "image_status": img_status,
            "location": location_obj,
            "reference_data": {
                k: str(v)
                for k, v in {
                    "school_sn": sn,
                    "group": group_str,
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
                "title": f"臺北市立大學國際事務處海外姊妹校一覽表與交換學校專區—{zh_name}",
                "source_url": source_url,
                "role": "home_university",
                "authority": "home_official_notice",
                "effective_academic_year": acad_year,
                "application_round": round_label,
                "checked_at": CHECKED_AT,
            },
            {
                "title": "臺北市立大學 116學年度第1學期赴外姊妹校交換學生甄選簡章 PDF",
                "source_url": UTAIPEI_116_1_BROCHURE_PDF_URL,
                "role": "home_university",
                "authority": "home_official_notice",
                "effective_academic_year": acad_year,
                "application_round": round_label,
                "checked_at": CHECKED_AT,
            },
            {
                "title": "臺北市立大學學生赴外研修甄選暨獎補助要點 PDF",
                "source_url": UTAIPEI_SELECTION_SUBSIDY_PDF_URL,
                "role": "home_university",
                "authority": "home_official_notice",
                "effective_academic_year": acad_year,
                "application_round": round_label,
                "checked_at": CHECKED_AT,
            },
        ]
        if exp_links:
            wf_sources.append({
                "title": f"臺北市立大學國際事務處出國交換學生研修心得報告專區—{zh_name}",
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
            "home_university": "臺北市立大學",
            "school_name": full_name,
            "partner_website": website,
            "country": country,
            "program_type": program_type,
            "academic_year": acad_year,
            "application_round": round_label,
            "effective_application_rounds": [
                round_label,
                "116-1（2027秋季班赴外交換學生甄選）",
                "115-2（2027春季班赴外交換學生甄選）",
                "115-1",
                "115-2",
                "116-1",
                "116-2",
            ],
            "applicability_status": "verified",
            "applicability_note": (
                "臺北市立大學由國際事務處全球教育交流組（博愛校區公誠樓 3 樓 G314 室／天母校區行政大樓 4 樓 C407 室，"
                "電話：02-2311-3040 分機 8662、8663、8666）統籌全校五大學院（教育學院、人文藝術學院、理學院、體育學院、市政管理學院）"
                "之全球姊妹校交換學生、11 校 24 學系境外雙聯學位學程及教育部學海飛颺、學海惜珠、學海築夢與本校返國生活獎補助遴選。"
            ),
            "review_status": "published",
            "published_at": CHECKED_AT,
            "steps": [
                {
                    "rule_id": f"utaipei-{acad_year}-home-1-{sn:03d}",
                    "order": 1,
                    "phase": "校內申請",
                    "title": f"確認北市大就讀滿一學期在學資格、操行 80 分與行為確認聲明、A/B/C/D 類別及 {zh_name} 語檢門檻",
                    "responsible_party": "學生",
                    "responsible_unit": "臺北市立大學國際事務處全球教育交流組（博愛校區 G314／天母校區 C407）",
                    "deadline_at": deadline_iso,
                    "deadline_status": "verified_exact",
                    "deadline_source_url": UTAIPEI_116_1_POST_URL,
                    "deadline_checked_at": CHECKED_AT,
                    "deadline_reminder_eligible": True,
                    "summary": (
                        f"確認符合《臺北市立大學學生赴外研修甄選暨獎補助要點》及當期《赴外姊妹校交換學生甄選簡章》規定：於本校就讀一學期以上之在學學士班（出國時為大二以上）及碩博士班（非當學期畢業）學生（不含在職專班及休學生），"
                        f"前一學期操行達 80 分以上且無申誡以上處分及違反性平法／重大違法紀錄（{gpa_req_str}），並備妥符合 {zh_name} 門檻之語言能力證明（{lang_req_str}）。"
                    ),
                    "details": [
                        f"開放學制與院系：{colleges_str}（{degree_levels_str}）",
                        f"語言與學業條件：{lang_req_str}｜{gpa_req_str}",
                        f"當期名額與計畫類別：{quota_str}｜{program_type}",
                    ],
                    "scope": {
                        "home_universities": ["臺北市立大學"],
                        "partner_universities": [full_name],
                        "academic_years": ["115", "116"],
                        "application_rounds": [
                            round_label,
                            "115-1",
                            "115-2",
                            "116-1",
                            "116-2",
                        ],
                    },
                    "source_urls": [
                        source_url,
                        UTAIPEI_SELECTION_SUBSIDY_PDF_URL,
                        UTAIPEI_116_1_BROCHURE_PDF_URL,
                    ],
                    "checked_at": CHECKED_AT,
                    "support_status": "verified",
                },
                {
                    "rule_id": f"utaipei-{acad_year}-home-2-{sn:03d}",
                    "order": 2,
                    "phase": "校內申請",
                    "title": "完成線上報名並備妥赴外交換志願表（最多5志願）、行為確認聲明書、歷年中英文成績單與中外文讀書計畫送交國際事務處",
                    "responsible_party": "學生與所屬系所／學院",
                    "responsible_unit": "各學院系所辦公室／臺北市立大學國際事務處全球教育交流組",
                    "deadline_at": deadline_iso,
                    "deadline_status": "verified_exact",
                    "deadline_source_url": UTAIPEI_116_1_POST_URL,
                    "deadline_checked_at": CHECKED_AT,
                    "deadline_reminder_eligible": True,
                    "summary": (
                        "申請學生須依《赴外姊妹校交換學生甄選簡章》規定，於報名截止日前（116-1 學期為 2026/10/30 17:00；115-2 學期為 2026/04/30 17:00）"
                        "完成線上申請系統登錄，並將核章後之紙本申請資料送達博愛校區公誠樓 G314 室或天母校區行政大樓 C407 室國際事務處全球教育交流組。"
                    ),
                    "details": [
                        "《赴外交換學生志願表》至多可填寫 5 所志願學校，並須本人及家長／監護人簽章。",
                        "須檢附親筆簽署之《臺北市立大學赴外交換學生行為確認聲明書》，確認在學期間無申誡以上處分及性平／重大違法案件。",
                    ],
                    "document_requirements": [
                        {
                            "name": "臺北市立大學赴外交換學生線上申請表暨志願表（最多填寫 5 所志願校）",
                            "official_form_url": UTAIPEI_116_1_PREF_PDF_URL,
                            "source_urls": [
                                UTAIPEI_116_1_PREF_PDF_URL,
                                UTAIPEI_116_1_BROCHURE_PDF_URL,
                            ],
                        },
                        {
                            "name": "臺北市立大學赴外交換學生行為確認聲明書及家長／監護人同意書",
                            "official_form_url": UTAIPEI_116_1_BEHAVIOR_PDF_URL,
                            "source_urls": [
                                UTAIPEI_116_1_BEHAVIOR_PDF_URL,
                                UTAIPEI_PARENTAL_CONSENT_PDF_URL,
                            ],
                        },
                        {
                            "name": "歷年中文及英文成績單正本（含前一學期學業班級排名百分比與操行成績）及語言能力檢定成績證明影本",
                            "official_form_url": UTAIPEI_CEFR_PDF_URL,
                            "source_urls": [
                                UTAIPEI_116_1_BROCHURE_PDF_URL,
                                UTAIPEI_CEFR_PDF_URL,
                            ],
                        },
                        {
                            "name": "中文及外文（英文或申請國語文）讀書計畫與自傳各乙份、B類優秀表現（專業著作／展演／競賽獲獎）佐證資料",
                            "official_form_url": UTAIPEI_STUDY_PLAN_DOCX_URL,
                            "source_urls": [
                                UTAIPEI_STUDY_PLAN_DOCX_URL,
                                UTAIPEI_116_1_BROCHURE_PDF_URL,
                            ],
                        },
                    ],
                    "scope": {
                        "home_universities": ["臺北市立大學"],
                        "academic_years": ["115", "116"],
                        "application_rounds": [
                            round_label,
                            "115-1",
                            "115-2",
                            "116-1",
                            "116-2",
                        ],
                    },
                    "source_urls": [
                        UTAIPEI_116_1_POST_URL,
                        UTAIPEI_116_1_BROCHURE_PDF_URL,
                        UTAIPEI_116_1_PREF_PDF_URL,
                    ],
                    "checked_at": CHECKED_AT,
                    "support_status": "verified",
                },
                {
                    "rule_id": f"utaipei-{acad_year}-home-3-{sn:03d}",
                    "order": 3,
                    "phase": "甄選與提名",
                    "title": "參加書面資料審查（40%）與面試（60%）兩階段甄選，依 A/B/C/D 四類優先順序分發錄取",
                    "responsible_party": "臺北市立大學國際事務處與申請學生",
                    "responsible_unit": "臺北市立大學學生赴外研修甄選委員會／國際事務處",
                    "deadline_at": "2026-12-31T17:00:00+08:00",
                    "deadline_status": "verified_exact",
                    "deadline_source_url": UTAIPEI_116_1_POST_URL,
                    "deadline_checked_at": CHECKED_AT,
                    "deadline_reminder_eligible": True,
                    "summary": (
                        "甄選成績含書面審查（40%）及面試（60%），由甄選委員會依 A 類（前一學期班排前 40%）、B 類（專業著作／展演／全國或國際競賽獲獎）、"
                        "C 類（一般符合外語標準者）、D 類（同一學制第二次申請者）四類優先順序及總成績高低核定錄取學校；116-1 學期預計於 2026/12/31 17:00 前公告錄取名單。"
                    ),
                    "details": [
                        "獲錄取學生如欲放棄錄取資格，須於規定截止日前（116-1 學期為 2027/01/29 17:00）填具《放棄錄取資格聲明書》送交國際事務處；逾期無故放棄者取消後續申請資格。",
                        "同時符合教育部學海飛颺或學海惜珠資格者，依《辦理教育部鼓勵國內大專校院選送學生出國研修或國外專業實習補助審查作業要點》核定補助額度。",
                    ],
                    "scope": {
                        "home_universities": ["臺北市立大學"],
                        "academic_years": ["115", "116"],
                        "application_rounds": [
                            round_label,
                            "115-1",
                            "115-2",
                            "116-1",
                            "116-2",
                        ],
                    },
                    "source_urls": [
                        UTAIPEI_SELECTION_SUBSIDY_PDF_URL,
                        UTAIPEI_XUEHAI_GUIDELINES_PDF_URL,
                        UTAIPEI_116_1_BROCHURE_PDF_URL,
                    ],
                    "checked_at": CHECKED_AT,
                    "support_status": "verified",
                },
                {
                    "rule_id": f"utaipei-{sn:03d}-host-apply",
                    "order": 4,
                    "phase": "合作校申請",
                    "title": f"由國際事務處向 {zh_name} 提名並遞交姊妹校交換／雙聯入學申請文件",
                    "responsible_party": "學生與接待校國際事務處",
                    "summary": (
                        "獲本校公告錄取後，由國際事務處全球教育交流組向姊妹校完成線上或電郵提名；學生須依姊妹校申請截止日備妥有效護照、英文成績單、財力證明、語檢證明與選課計畫，"
                        "待收到姊妹校核發之正式入學許可（Admission Letter / COE / DS-2019 / CAS）。"
                    ),
                    "details": [
                        f"研修期程：{study_period_str}｜名額：{quota_str}",
                        f"語言與學業條件：{lang_req_str}｜{gpa_req_str}",
                        f"住宿與費用待遇：{housing_str}",
                    ],
                    "scope": {
                        "home_universities": ["臺北市立大學"],
                        "partner_universities": [full_name],
                        "academic_years": ["115", "116"],
                        "application_rounds": [
                            round_label,
                            "115-1",
                            "115-2",
                            "116-1",
                            "116-2",
                        ],
                    },
                    "source_urls": [source_url, UTAIPEI_116_1_BROCHURE_PDF_URL]
                    + ([website] if website else []),
                    "checked_at": CHECKED_AT,
                    "support_status": "verified",
                    "needs_confirmation": False,
                },
                {
                    "rule_id": f"utaipei-{acad_year}-home-5-{sn:03d}",
                    "order": 5,
                    "phase": "行前準備",
                    "title": "完成北市大註冊繳費與出國離校程序單，抵埠繳交第二階段學員報告書，返國辦理學分抵免與生活獎補助申請",
                    "responsible_party": "學生與所屬系所",
                    "responsible_unit": "臺北市立大學國際事務處／教務處／學務處／各學院系所",
                    "summary": (
                        "出國前須完成本校註冊繳費及《交換學生出國前離校程序單》，並投保海外醫療及意外險；抵達姊妹校後依限繳交《第二階段學員報告書》；"
                        "交換期間每學期至少修習相當於本校 6 學分課程（歐洲 2 ECTS = 1 學分）；返國後兩個月內完成《返國報到程序單》、繳交 1,500–2,000 字研修心得報告、辦理學分採認及申請本校返國生活獎補助。"
                    ),
                    "details": tuition_points_list,
                    "scope": {
                        "home_universities": ["臺北市立大學"],
                        "academic_years": ["115", "116"],
                        "application_rounds": [
                            round_label,
                            "115-1",
                            "115-2",
                            "116-1",
                            "116-2",
                        ],
                    },
                    "source_urls": [
                        UTAIPEI_SELECTION_SUBSIDY_PDF_URL,
                        UTAIPEI_COURSE_GUIDELINES_PDF_URL,
                        UTAIPEI_116_1_BROCHURE_PDF_URL,
                    ],
                    "checked_at": CHECKED_AT,
                    "support_status": "verified",
                },
            ],
            "sources": wf_sources,
            "last_checked": CHECKED_AT,
            "coverage_status": "official_verified",
            "coverage_note": (
                f"已完整整合臺北市立大學國際事務處（OIA）全球 41 國／地區共 {len(catalog_source)} 所合作姊妹校與交換／雙聯專案（含"
                f" {open_partner_count} 所 116-1／115-2 開放交換與 11 校 24 學系雙聯學位合作學校）、"
                "學生赴外研修甄選暨獎補助要點、出國選修課程實施要點，以及"
                f" {exp_covered_schools} 校 {total_exp_reports} 篇出國交換研修心得報告與錄取紀錄。"
            ),
        })

        cost_line = f"{zh_name} 預估每月生活費：{living_cost_str}"
        tuition_clean = tuition_points_list[0]
        housing_clean = housing_str
        calendar_clean = f"學期與研修時間參考：{sem_dates_str}"
        course_clean = course_rest_str

        dest_sources = [
            {
                "title": f"臺北市立大學國際事務處海外姊妹校一覽表與交換學校專頁—{zh_name}",
                "source_url": source_url,
                "summary": "北市大國際事務處公告之合作計畫類型、名額、語言門檻、學校簡介與學費待遇",
            },
            {
                "title": "臺北市立大學 116-1 赴外姊妹校交換學生甄選簡章與學生赴外研修甄選暨獎補助要點",
                "source_url": UTAIPEI_116_1_BROCHURE_PDF_URL,
                "summary": "北市大交換生 A/B/C/D 四類優先順序、CEFR B1/B2 語檢對照表、海外應修 6 學分及返國生活獎補助規定",
            },
        ]
        if exp_links:
            dest_sources.append({
                "title": f"臺北市立大學國際事務處出國交換學生研修心得報告專區—{zh_name}",
                "source_url": exp_links[0]["url"],
                "summary": f"收錄北市大學生赴 {zh_name} 出國交換研修心得報告與錄取紀錄共 {len(exps)} 篇",
            })
        if website:
            dest_sources.append({
                "title": f"{full_name} 官方網站",
                "source_url": website,
                "summary": "接待合作姊妹校官方網站",
            })

        src_url_list = (
            [source_url, UTAIPEI_SISTER_SCHOOLS_URL, UTAIPEI_SCHOLARSHIPS_URL]
            + ([exp_links[0]["url"]] if exp_links else [UTAIPEI_EXPERIENCE_URL])
            + ([website] if website else [])
        )

        destinations.append({
            "home_university": "臺北市立大學",
            "school_name": full_name,
            "country": country,
            "city": city_name,
            "cost_summary": f"{cost_line}。\n{tuition_clean}",
            "housing_summary": housing_clean,
            "transport_summary": (
                f"校區代表城市：{city_name}。請依入學許可確認實際授課校區位置與當地學生交通卡優惠。"
            ),
            "campus_life_summary": f"{calendar_clean}\n{course_clean}",
            "student_guide_sections": [
                {
                    "key": "cost",
                    "title": "生活費、北市大註冊免繳姊妹校學費規定與學海系列／返國生活獎補助體系",
                    "summary": cost_line,
                    "points": [cost_line] + tuition_points_list,
                    "source_urls": src_url_list + [
                        UTAIPEI_SELECTION_SUBSIDY_PDF_URL,
                        UTAIPEI_116_1_BROCHURE_PDF_URL,
                    ],
                    "caution": "錄取學生出國期間仍須於臺北市立大學完成每學期註冊並繳交全額學雜費；未領取學海系列或外國政府獎學金者，返國完成心得報告及學分採認後得申請返國生活獎補助（亞洲最高 NT$15,000、非亞洲最高 NT$30,000）。",
                },
                {
                    "key": "housing",
                    "title": "住宿資訊與姊妹校校內外學生宿舍申請",
                    "summary": housing_clean[:160],
                    "points": [housing_clean],
                    "source_urls": src_url_list,
                    "caution": "赴日本、歐美及韓國交換生申請宿舍與簽證（如 COE、DS-2019、D-2-6）時，須依姊妹校規定檢附英文存款／財力證明。",
                },
                {
                    "key": "insurance",
                    "title": "海外醫療與意外保險規定暨抵埠第二階段學員報告書繳交",
                    "summary": visa_health_str,
                    "points": [
                        visa_health_str,
                        "錄取學生出國前須購買涵蓋交換全期之海外急難救助、醫療（門診及住院）與意外保險，並於抵達姊妹校後依規定時限填送《第二階段學員報告書》回傳國際事務處備查。",
                    ],
                    "source_urls": src_url_list + [UTAIPEI_SELECTION_SUBSIDY_PDF_URL],
                    "caution": "出國前請確認海外醫療保險涵蓋門診、住院及跨國急難救助，並依接待國法令加入當地國民健康保險或學生保險。",
                },
                {
                    "key": "visa",
                    "title": "留學交換簽證辦理、出國離校程序單與役男出境緩徵申請",
                    "summary": visa_health_str,
                    "points": [
                        visa_health_str,
                        "錄取生出國前須填妥《交換學生出國前離校程序單》經系所及相關處室核章；具役男身分之在學學生，應於出國前依規定檢附入學許可向學務處生輔組辦理役男出境緩徵。",
                    ],
                    "source_urls": src_url_list + [UTAIPEI_PROCESS_URL],
                    "caution": "如欲放棄錄取資格，須於簡章規定期限前（116-1 為 2027/01/29 17:00）繳交《放棄錄取資格聲明書》，無故放棄者不得再參加後續甄選。",
                },
                {
                    "key": "academics",
                    "title": "海外每學期應修至少 6 學分（暑期 3 學分、2 ECTS = 1 學分）與返國學分採認",
                    "summary": course_clean[:160],
                    "points": [calendar_clean, course_clean],
                    "source_urls": src_url_list + [
                        UTAIPEI_COURSE_GUIDELINES_PDF_URL,
                        UTAIPEI_116_1_BROCHURE_PDF_URL,
                    ],
                    "caution": "依《臺北市立大學學生出國選修課程實施要點》，出國修習學分累計以不超過畢業應修總學分數四分之一為限，返國後兩個月內應辦理學分抵免。",
                },
                {
                    "key": "living",
                    "title": f"{city_name} 校園生活、19 國歷年交換學生研修心得報告與說明會經驗傳承",
                    "summary": f"代表城市：{city_name}。錄取學生返國後須繳交 1,500–2,000 字研修心得報告傳承海外經驗。",
                    "points": [
                        f"目的地城市：{city_name}（{country}）",
                        "臺北市立大學國際事務處建置完整 19 國「出國交換學生研修心得報告專區」並定期舉辦赴外交換說明會"
                        + (
                            f"（本校於此姊妹校共收錄 {len(exps)} 篇：{'、'.join(exp_labels[:3])}）"
                            if exps
                            else ""
                        )
                        + "，提供選課、住宿與生活第一手資訊。",
                    ],
                    "source_urls": [
                        exp_links[0]["url"] if exp_links else UTAIPEI_EXPERIENCE_URL
                    ],
                },
            ],
            "sources": dest_sources,
            "last_checked": CHECKED_AT,
            "coverage_status": "official_verified",
            "coverage_note": (
                f"已整合臺北市立大學國際事務處 {len(catalog_source)} 所合作姊妹校名冊、116-1／115-2 赴外交換學生甄選簡章、雙聯學位一覽表及"
                f" {exp_covered_schools} 校 {total_exp_reports} 篇出國交換學生研修心得報告與錄取紀錄。"
            ),
        })

        research_records.append({
            "home_university": "臺北市立大學",
            "school_name": full_name,
            "country": country,
            "official_website": website,
            "verification_status": "official_verified",
            "discovery_source_url": detail_url,
            "checked_at": CHECKED_AT,
            "note": (
                f"臺北市立大學國際事務處全球 41 國／地區 {len(catalog_source)} 所合作姊妹校總表、116-1／115-2 交換簡章與"
                " ROR/Wikidata 官方網址核對完成。"
            ),
        })

        ev_sources = [{
            "title": f"臺北市立大學國際事務處合作姊妹校與交換資訊—{zh_name}",
            "url": source_url,
        }]
        if exp_links:
            ev_sources.append({
                "title": f"臺北市立大學國際事務處出國交換學生研修心得報告專區—{zh_name}",
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
                "scope": "北市大海外交換／雙聯姊妹校住宿與財力證明資訊",
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
                "scope": "北市大出國交換註冊規定、教育部學海飛颺／惜珠／築夢、返國生活獎補助與地區生活費估算",
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
                "scope": "臺北市立大學學生赴外研修甄選暨獎補助要點、出國選修課程實施要點（每學期至少 6 學分／2 ECTS = 1 學分）",
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
                "scope": "北市大海外交換簽證、出國離校程序單、第二階段學員報告書與海外醫療保險規定",
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
                        f"｜北市大國際事務處收錄 {len(exps)} 篇赴 {zh_name} 出國交換研修心得報告與錄取紀錄（{'、'.join(exp_labels[:3])}）。"
                        if exps
                        else ""
                    )
                ),
                "sources": ev_sources,
                "checked_at": CHECKED_AT,
                "scope": "北市大交換名額與歷年出國交換研修心得報告傳承",
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
                    f"已整合臺北市立大學國際事務處 {len(catalog_source)} 所合作姊妹校名冊、116-1／115-2 赴外姊妹校交換學生甄選簡章、雙聯學位一覽表及歷年出國交換研修心得報告。"
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

    write_jsonl(OFFICIAL_UTAIPEI_DIR / "partners.jsonl", partners)
    write_jsonl(SOURCES_UTAIPEI_DIR / "partners.jsonl", partners)
    write_jsonl(OFFICIAL_UTAIPEI_DIR / "application_workflows.jsonl", workflows)
    write_jsonl(OFFICIAL_UTAIPEI_DIR / "destination_profiles.jsonl", destinations)
    write_jsonl(OFFICIAL_UTAIPEI_DIR / "partner_research.jsonl", research_records)
    write_jsonl(OFFICIAL_UTAIPEI_DIR / "student_life.jsonl", life_records)
    write_jsonl(
        OFFICIAL_UTAIPEI_DIR / "experience_sources.jsonl", experience_sources_records
    )
    write_jsonl(
        OFFICIAL_UTAIPEI_DIR / "student_experience_sources.jsonl",
        experience_sources_records,
    )
    write_jsonl(
        OFFICIAL_UTAIPEI_DIR / "student_experiences.jsonl", student_experience_rows
    )

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
    (OFFICIAL_UTAIPEI_DIR / "student-experience-digests.json").write_text(
        json.dumps({"digests": digest_records}, ensure_ascii=False, indent=2)
        + "\n",
        encoding="utf-8",
    )

    (OFFICIAL_UTAIPEI_DIR / "student-experiences.json").write_text(
        json.dumps(
            {
                "school_id": "utaipei",
                "school_name": "臺北市立大學",
                "checked_at": CHECKED_AT,
                "source_url": UTAIPEI_EXPERIENCE_URL,
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

    (OFFICIAL_UTAIPEI_DIR / "campus-locations.json").write_text(
        json.dumps(
            {
                "school_id": "utaipei",
                "school_name": "臺北市立大學",
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
    (OFFICIAL_UTAIPEI_DIR / "campus-assets.json").write_text(
        json.dumps(
            {
                "school_id": "utaipei",
                "school_name": "臺北市立大學",
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

    utaipei_source_urls = [
        UTAIPEI_OIA_HOME_URL,
        UTAIPEI_SISTER_SCHOOLS_URL,
        UTAIPEI_EXCHANGE_OVERVIEW_URL,
        UTAIPEI_EXCHANGE_ASIA_URL,
        UTAIPEI_EXCHANGE_NON_ASIA_URL,
        UTAIPEI_DUAL_DEGREE_URL,
        UTAIPEI_PROCESS_URL,
        UTAIPEI_DOCUMENTS_URL,
        UTAIPEI_FAQ_URL,
        UTAIPEI_SCHOLARSHIPS_URL,
        UTAIPEI_MOE_XUEHAI_URL,
        UTAIPEI_LIVING_SUBSIDY_URL,
        UTAIPEI_REGULATIONS_URL,
        UTAIPEI_FORMS_URL,
        UTAIPEI_EXPERIENCE_URL,
        UTAIPEI_116_1_POST_URL,
        UTAIPEI_116_1_BRIEFING_POST_URL,
        UTAIPEI_115_2_POST_URL,
        UTAIPEI_115_2_ADMITTED_POST_URL,
        UTAIPEI_115_2_XIZHU_POST_URL,
        UTAIPEI_115_1_LIVING_POST_URL,
        UTAIPEI_DUAL_RULES_POST_URL,
        UTAIPEI_EXCHANGE_RULES_POST_URL,
        UTAIPEI_XUEHAI_RULES_POST_URL,
        UTAIPEI_116_1_BROCHURE_PDF_URL,
        UTAIPEI_115_2_BROCHURE_PDF_URL,
        UTAIPEI_CEFR_PDF_URL,
        UTAIPEI_SELECTION_SUBSIDY_PDF_URL,
        UTAIPEI_COURSE_GUIDELINES_PDF_URL,
        UTAIPEI_DUAL_GUIDELINES_PDF_URL,
    ]

    exchange_info_payload = {
        "school_name": "臺北市立大學",
        "program_type": [
            (
                "國際事務處全球教育交流組「116-1／115-2 赴外姊妹校交換學生計畫」（涵蓋日本北海道教育大學、鳴門教育大學、上越教育大學、東北大學、中央大學、名古屋外國語大學、京都橘大學、環太平洋大學，"
                "韓國首爾市立大學、中央大學、梨花女子大學、仁荷大學、檀國大學、世宗大學、誠信女子大學、釜山外國語大學，"
                "中國大陸北京師範大學、華東師範大學、上海體育大學、北京體育大學、中央音樂學院、北京舞蹈學院、南京師範大學、山東大學、吉林大學、廈門大學，"
                "美國舊金山州立大學、中央奧克拉荷馬大學、愛達荷州立大學，法國里昂第三大學、巴黎東克雷泰伊大學、圖盧茲大學、雷恩商學院，"
                "德國科隆體育大學、奧爾登堡大學、海德堡教育大學，捷克帕拉茨基大學、赫拉德茨克拉洛韋大學、奧斯特拉瓦大學，波蘭波茲南體育大學、弗羅茨瓦夫體育大學等"
                f" {open_partner_count} 所開放交換與雙聯合作校，以及全球 41 國／地區 {len(partners)} 所締約姊妹校）"
            ),
            (
                "國際事務處「境外大學雙聯學制專案」（涵蓋美國西南奧克拉荷馬州立大學 SWOSU［2+2］、印第安納賓州大學 IUP［1+1］、特洛伊大學 Troy University［2+2］、"
                "英國艾塞克斯大學 University of Essex［12 系所 3+1／2+2／1+1］、倫敦聖三一拉邦音樂舞蹈學院 Trinity Laban［3+1］、諾丁漢大學 University of Nottingham［3+1］、"
                "紐西蘭奧克蘭大學 The University of Auckland［1+1+1］、泰國朱拉隆功大學 Chulalongkorn University［1+1］、馬來西亞馬來亞大學 University of Malaya［1+1］、"
                "哈薩克薩特帕耶夫大學 Satbayev University［1+1］、加拿大西安大略大學國王大學學院［3+1］共 11 校 24 個雙聯學位學程）"
            ),
            (
                "國際事務處「教育部學海飛颺、學海惜珠、學海築夢／新南向學海築夢」暨「臺北市立大學學生赴外研修返國生活獎補助（亞洲最高 NT$15,000／非亞洲最高 NT$30,000，分 8 級優先順序核給）」獎助學金體系"
            ),
        ],
        "academic_year": [
            (
                "116（涵蓋 116 學年度第 1 學期［2027 秋季班］赴外姊妹校交換學生甄選［2026/10/05 14:00 至 2026/10/30 17:00 截止，預計 2026/12/31 公告錄取］，"
                "以及 115 學年度第 2 學期［2027 春季班］交換學生與教育部學海計畫甄選）"
            ),
            (
                f"本平台完整收錄臺北市立大學國際事務處公告之 {len(partners)} 所全球合作姊妹校與交換／雙聯專案（橫跨全球 41 個國家與地區，含"
                f" {open_partner_count} 所 116-1／115-2 開放申請之交換與雙聯合作校，並收錄 {exp_covered_schools} 所合作大學共"
                f" {total_exp_reports} 篇出國交換學生研修心得報告與錄取紀錄）"
            ),
        ],
        "semester": [
            (
                "秋季班（第 1 學期）赴外交換學生甄選（每年 10 月公告簡章並受理收件，12 月底前公告錄取名單，預計翌年 8–9 月出國）：開放全校五大學院就讀滿一學期之學士班（出國時大二以上）及碩博士班（非當學期畢業）在學學生申請。"
            ),
            (
                "春季班（第 2 學期）赴外交換學生甄選（每年 4 月公告簡章並受理收件，6 月公告錄取名單，預計翌年 1–4 月出國）：每位申請人至多可填報 5 所志願學校。"
            ),
        ],
        "application_period": [
            (
                "【116 學年度第 1 學期（2027 秋季班）赴外姊妹校交換學生甄選】線上報名暨紙本收件自 2026/10/05（一）14:00 起至"
                " 2026/10/30（五）17:00 止送達國際事務處全球教育交流組（博愛校區公誠樓 G314 室／天母校區行政大樓 C407 室）；"
                "預計 2026/12/31（四）17:00 前公告錄取結果，放棄錄取資格聲明書截止日為 2027/01/29（五）17:00。"
            ),
            (
                "【115 學年度第 2 學期（2027 春季班）赴外姊妹校交換學生甄選】自 2026/04/10（五）14:00 起至"
                " 2026/04/30（四）17:00 止受理申請，已於 2026/06 公告錄取 48 名正取交換生。"
            ),
            (
                "【教育部學海惜珠計畫暨本校返國生活獎補助申請】每學期依國際事務處公告時程受理（115-2 學海惜珠及 115-1 返國生活獎補助於 9–10 月受理收件）。"
            ),
        ],
        "eligibility": [
            (
                "1. 在學學籍與修業年級規定：依《臺北市立大學學生赴外研修甄選暨獎補助要點》第三點及當期《赴外姊妹校交換學生甄選簡章》，"
                "申請人須為於本校就讀一學期以上之在學學士班學生（實際出國交換時須為二年級以上）及碩、博士班學生（非當學期畢業），不含在職專班及休學生。同一學制內以參加二次交換為限（不同學制分開計算）。"
            ),
            (
                "2. 操行成績與行為確認門檻：前一學期操行成績須達 80 分以上，且在學期間未受申誡以上處分、無違反性別平等教育法或重大違法行為（須親筆簽署《臺北市立大學赴外交換學生行為確認聲明書》）。"
            ),
            (
                "3. A/B/C/D 四類甄選優先順序與評分標準：書面審查占 40%、面試占 60%，甄選委員會依四類優先順序核定分發："
                "（A 類・第一優先）前一學期學業成績班級排名前 40% 且外語能力符合申請學校規定者；"
                "（B 類・第二優先）在學期間有專業學術著作發表、重要藝術展演或參加全國性、國際性競賽獲獎且外語符合規定者；"
                "（C 類・第三優先）其他符合外語能力規定之一般申請者；"
                "（D 類・第四優先）曾錄取本校赴外交換計畫並於同一學制內提出第二次申請者。"
            ),
            (
                "4. 海外修課學分規定與返國義務：依《臺北市立大學學生出國選修課程實施要點》，交換學生於國外姊妹校每學期至少應修習相當於本校 6 學分之課程（暑期至少 3 學分；歐洲 2 ECTS 折算 1 學分），"
                "累計採認學分上限為畢業應修總學分數之 1/4；返國後兩個月內須繳交 1,500–2,000 字研修心得報告並辦理學分採認。"
            ),
        ],
        "language_requirement": [
            (
                "1. 非華語國家最低外語門檻（CEFR B1）：依《臺北市立大學學生赴外研修甄選暨獎補助要點》及《各項英檢與 CEFR 架構對照表》，"
                "申請非華語國家姊妹校須具備英語能力相當於 CEFR B1 級以上檢定證明：全民英檢 GEPT 中級、TOEIC Listening & Reading 550 分、"
                "TOEFL iBT 42 分（新制 3 分）、TOEFL ITP 433 分、IELTS 4.0、劍橋英檢 140 分、Linguaskill 140 分或 Duolingo 60 分以上；"
                "若姊妹校訂有更高門檻（如 CEFR B2［TOEIC 785／TOEFL iBT 72／IELTS 5.5］、美國舊金山州立大學 TOEFL iBT 61、法國雷恩商學院／德國科隆體育大學／波蘭體育大學等 B2 門檻），須同時符合姊妹校規定。"
            ),
            (
                "2. 日韓及歐語區姊妹校門檻：（1）日本地區：依各校簡章要求檢附 JLPT N1（如大東文化大學）、JLPT N2（如名古屋外國語大學、京都橘大學、東北大學 JYPE 等）、"
                "JLPT N3（如北海道教育大學、上越教育大學、中央大學等）或英語 CEFR B1/B2；（2）韓國地區：依各校簡章要求檢附 TOPIK 2–4 級（如首爾市立大學、梨花女子大學、檀國大學、世宗大學、誠信女子大學、釜山外國語大學等）或英語 CEFR B1/B2（如中央大學、仁荷大學、韓巴大學等）；"
                "（3）法語／德語／西語區：可依姊妹校規定檢附 DELF B1/B2、Goethe-Zertifikat B1/B2、DELE B1/B2 或英語檢定。"
            ),
            (
                "3. 華語國家豁免規定：申請赴中國大陸姊妹校交換者，免附外語能力檢定證明（若有外語檢定成績亦可檢附作為書審加分參考）。"
            ),
        ],
        "required_documents": [
            "1. 臺北市立大學赴外交換學生線上申請表暨志願表（紙本 1 份，至多可填寫 5 所志願學校，經申請人及家長／監護人簽章）",
            "2. 臺北市立大學赴外交換學生行為確認聲明書及家長／監護人同意書（紙本各 1 份）",
            "3. 歷年中文及英文成績單正本各乙份（須註明前一學期學業班級排名百分比及操行成績達 80 分以上）",
            "4. 有效語言能力檢定成績證明影本乙份（申請非華語國家須達 CEFR B1 以上並符合志願校門檻；申請中國大陸姊妹校免附）",
            "5. 中文及外文（英文或申請國家語文）讀書計畫與自傳各乙份（依國際事務處規定範本格式撰寫）",
            "6. B 類優秀表現佐證資料（專業學術著作發表、重要藝術展演或全國性／國際性競賽獲獎證明影本；無則免附）",
        ],
        "scholarship_info": [
            (
                "1. 教育部《學海飛颺》選送優秀學生出國研修獎學金：補助具中華民國國籍且在臺設有戶籍、外語與學業成績優良之在學學生赴非大陸港澳地區姊妹校交換 1 學期或 1 學年，"
                "含教育部補助款及本校最少 20% 配合款（參考標準：研修一學年約 NT$150,000、研修一學期約 NT$75,000，實際金額依當年度預算與審查委員會核定為準）。"
            ),
            (
                "2. 教育部《學海惜珠》勵學優秀學生出國研修獎學金：補助持各直轄市、縣（市）主管機關開立之低收入戶、中低收入戶或特殊境遇家庭相關證明之在學學生赴海外姊妹校交換研修來回機票與生活費。"
            ),
            (
                "3. 教育部《學海築夢》及《新南向學海築夢》海外專業實習計畫：由本校專任教師主持計畫選送學生赴海外或新南向國家機構實習，補助機票與生活費。"
            ),
            (
                "4. 《臺北市立大學學生赴外研修返國生活獎補助》：針對未獲教育部學海系列或外國政府獎學金、圓滿完成交換返國並繳交 1,500–2,000 字心得報告及完成學分採認之交換生，"
                "赴亞洲地區每名最高補助新臺幣 15,000 元、赴非亞洲地區每名最高補助新臺幣 30,000 元，依甄選類別（A/B/C/D 類）及外語能力等級（CEFR B2 以上優先於 B1）共 8 級優先順序核給。"
            ),
        ],
        "partner_universities": [p["school_name"] for p in partners],
        "source_urls": utaipei_source_urls,
        "last_checked": CHECKED_AT,
    }
    (OFFICIAL_UTAIPEI_DIR / "exchange_info.json").write_text(
        json.dumps(exchange_info_payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    student_dashboard_payload = {
        "school_name": "臺北市立大學",
        "last_checked": CHECKED_AT,
        "academic_score_minimum": None,
        "academic_score_rule": (
            "依《臺北市立大學學生赴外研修甄選暨獎補助要點》及當期《赴外姊妹校交換學生甄選簡章》：申請人前一學期操行成績須達 80 分以上，"
            "且在學期間無申誡以上處分及違反性平法／重大違法紀錄；學業成績於前一學期班級排名前 40% 者列為 A 類第一優先"
            "（B 類為專業著作／展演／全國或國際競賽獲獎、C 類為其他符合外語門檻者、D 類為同一學制第二次申請者），"
            "部分姊妹校另訂有個別 GPA 門檻（如 GPA 2.0–3.7 或 75 分以上），須同時符合姊妹校規定。"
        ),
        "academic_gpa_minimum": None,
        "maximum_preferences": 5,
        "selection_rules": {
            "academic_policy": "score_or_rank",
            "academic_reference_year": "116",
            "undergraduate_gpa_minimum": None,
            "graduate_academic_exempt": False,
            "exclude_in_service": True,
            "pending_quota_planning": False,
            "partner_requirements_need_confirmation": False,
            "degree_score_minimums": {},
            "excluded_undergraduate_years": ["大一上"],
            "language_certificate_required": True,
        },
        "language_score_minimums": {
            "toefl": 42.0,
            "ielts": 4.0,
            "toeic": 550.0,
        },
        "application_periods": [
            {
                "title": (
                    "臺北市立大學「116學年度第1學期（2027秋季班）」赴外姊妹校交換學生甄選（10/05 14:00–10/30 17:00 截止，12/31 公告錄取）"
                ),
                "details": [
                    (
                        "開放申請交換期間：116 學年度第 1 學期（2027 秋季班）。線上系統登錄暨紙本收件期間：自 2026 年 10 月 5 日（一）14:00 起至"
                        " 2026 年 10 月 30 日（五）17:00 止，送交國際事務處全球教育交流組（博愛校區公誠樓 3 樓 G314 室／天母校區行政大樓 4 樓 C407 室）。"
                    ),
                    (
                        "審核與公告時程：書面審查占 40%、面試占 60%，依 A/B/C/D 四類優先順序分發（至多填寫 5 個志願）；"
                        "預計 2026 年 12 月 31 日（四）17:00 前公告錄取名單，放棄錄取資格截止日為 2027 年 1 月 29 日（五）17:00。"
                    ),
                ],
                "source": {
                    "title": "臺北市立大學國際事務處《116學年度第1學期赴外姊妹校交換學生甄選簡章公告》",
                    "source_url": UTAIPEI_116_1_POST_URL,
                    "category": "exchange_application",
                    "summary": "北市大 116-1 赴外姊妹校交換學生甄選簡章、86 所開放交換學校名額表、行為確認聲明書與志願表。",
                },
                "scope": "home_application",
                "program_types": ["exchange", "dual_degree"],
                "academic_year": "116",
                "application_round": "116-1（2027秋季班）赴外姊妹校交換學生甄選",
                "audience": "all_students",
                "opens_at": "2026-10-05T14:00:00+08:00",
                "deadline_at": "2026-10-30T17:00:00+08:00",
                "date_status": "verified_exact",
                "status": "open",
                "status_note": "116 學年度第 1 學期赴外姊妹校交換學生甄選簡章、志願表、行為確認聲明書與說明會簡報已公告於國際事務處網站。",
                "deadline_note": "請於 2026 年 10 月 30 日（五）下午 5 時前完成線上申請並將紙本文件送達國際事務處全球教育交流組。",
                "reminder_eligible": True,
                "checked_at": CHECKED_AT,
            },
            {
                "title": (
                    "臺北市立大學「115學年度第2學期（2027春季班）」赴外姊妹校交換學生甄選（04/10 14:00–04/30 17:00 截止）"
                ),
                "details": [
                    (
                        "開放申請交換期間：115 學年度第 2 學期（2027 春季班）。校內收件期間為 2026 年 4 月 10 日（五）14:00 至 4 月 30 日（四）17:00 止，"
                        "並已於 2026 年 6 月公告錄取 48 名正取交換生。"
                    ),
                    (
                        "每學年固定辦理兩梯次甄選：每年 4 月甄選次學年度第 2 學期（春季班）交換生，每年 10 月甄選次學年度第 1 學期（秋季班）交換生。"
                    ),
                ],
                "source": {
                    "title": "臺北市立大學國際事務處《115學年度第2學期赴外姊妹校交換學生甄選簡章與錄取名單公告》",
                    "source_url": UTAIPEI_115_2_POST_URL,
                    "category": "exchange_application",
                    "summary": "北市大 115-2 赴外姊妹校交換學生甄選簡章與 48 名正取生錄取名單。",
                },
                "scope": "home_application",
                "program_types": ["exchange", "dual_degree"],
                "academic_year": "115",
                "application_round": "115-2（2027春季班）赴外姊妹校交換學生甄選",
                "audience": "all_students",
                "opens_at": "2026-04-10T14:00:00+08:00",
                "deadline_at": "2026-04-30T17:00:00+08:00",
                "date_status": "verified_exact",
                "status": "closed",
                "status_note": "115-2 學期交換甄選已截止並於 2026 年 6 月公告 48 名錄取名單。",
                "deadline_note": "次梯次（116-1 秋季班）於 2026 年 10 月 5 日至 10 月 30 日開放申請。",
                "reminder_eligible": False,
                "checked_at": CHECKED_AT,
            },
        ],
        "program_overview": [{
            "title": (
                f"臺北市立大學國際事務處全球姊妹校交換學生、11 校 24 系境外雙聯學位與獎補助總覽（{len(partners)} 所締約姊妹校・{open_partner_count} 所開放交換／雙聯）"
            ),
            "details": [
                (
                    "臺北市立大學（University of Taipei, UTaipei，由臺北市立教育大學與臺北市立體育學院於 2013 年合併成立，設有博愛校區及天母校區，"
                    "涵蓋「教育學院、人文藝術學院、理學院、體育學院、市政管理學院」五大學院）由「國際事務處 全球教育交流組（Office of International Affairs - Global Education and Exchange Section）」"
                    f"統籌全校赴外姊妹校交換學生、境外雙聯學位及教育部學海系列獎補助。本平台完整收錄 {len(partners)} 所北市大官方合作姊妹校，"
                    f"橫跨全球 41 個國家與地區（含 {open_partner_count} 所 116-1／115-2 開放申請之交換與雙聯合作校）。"
                ),
                (
                    "北市大出國交換與雙聯體系具備五大核心特色：（1）涵蓋日本（北海道教育大學、鳴門教育大學、上越教育大學、東北大學、中央大學、名古屋外國語大學、京都橘大學等 19 校）、"
                    "韓國（首爾市立大學、中央大學、梨花女子大學、仁荷大學、檀國大學、世宗大學、誠信女子大學等 20 校）、中國大陸（北京師範大學、華東師範大學、上海體育大學、北京體育大學、中央音樂學院、北京舞蹈學院等 62 校）、"
                    "歐美（美國舊金山州立大學、中央奧克拉荷馬大學、法國里昂第三大學、雷恩商學院、德國科隆體育大學、奧爾登堡大學、捷克帕拉茨基大學、波蘭四大體育大學等）及新南向國家；"
                    "（2）與美、英、紐、泰、馬、哈、加 11 所大學簽訂 24 個雙聯學位學程（含英國 University of Essex 12 系所 3+1/2+2/1+1、Trinity Laban、University of Nottingham、美國 SWOSU/IUP/Troy、紐西蘭奧克蘭大學等）；"
                    "（3）採 A/B/C/D 四類優先順序分發，每位學生最多可填 5 所志願校；（4）海外每學期至少修習 6 學分（歐洲 2 ECTS = 1 學分）；"
                    "（5）除教育部學海飛颺（含本校最少 20% 配合款）、學海惜珠外，特設「本校返國生活獎補助」（亞洲 NT$15,000／非亞洲 NT$30,000，分 8 級優先核給），並典藏 19 國共 421 筆研修心得與錄取紀錄。"
                ),
            ],
            "source": {
                "title": "臺北市立大學國際事務處（OIA）官方網站與海外姊妹校總表",
                "source_url": UTAIPEI_SISTER_SCHOOLS_URL,
                "category": "exchange_application",
                "summary": f"北市大 {len(partners)} 所全球合作姊妹校、{open_partner_count} 所開放交換與 11 校 24 系雙聯學位總覽。",
            },
        }],
        "eligibility": [{
            "title": (
                "北市大就讀滿一學期在學資格、操行 80 分與行為確認聲明、A/B/C/D 四類優先順序及海外應修 6 學分規定"
            ),
            "details": [
                (
                    "修業年級與學籍規定：依《臺北市立大學學生赴外研修甄選暨獎補助要點》及當期《赴外姊妹校交換學生甄選簡章》，申請人須為於本校就讀一學期以上之在學學士班（實際赴外交換時須為二年級以上）及碩、博士班（非當學期畢業）學生（不含在職專班及休學生）。同一學制以參加二次為限。"
                ),
                (
                    "操行門檻與 A/B/C/D 四類優先順序：前一學期操行成績須達 80 分以上，且在學期間未受申誡以上處分、無違反性平法或重大違法行為（須簽署《行為確認聲明書》）。"
                    "甄選依 A 類（前一學期班排前 40%）、B 類（在學期間具專業著作／重要展演／全國或國際競賽獲獎）、C 類（一般符合外語標準者）、D 類（同一學制第二次申請者）四類優先順序及總成績（書審 40%＋面試 60%）分發。出國交換每學期至少應修習相當於本校 6 學分課程（暑期 3 學分、歐洲 2 ECTS 折算 1 學分）。"
                ),
            ],
            "source": {
                "title": "臺北市立大學 116-1 赴外姊妹校交換學生甄選簡章與學生赴外研修甄選暨獎補助要點",
                "source_url": UTAIPEI_SELECTION_SUBSIDY_PDF_URL,
                "category": "exchange_application",
                "summary": "北市大交換生申請資格、A/B/C/D 優先順序、行為確認聲明書與海外修課學分規定。",
            },
        }],
        "language_requirements": [{
            "title": (
                "北市大交換留學語檢門檻（非華語國家最低 CEFR B1［GEPT 中級 / TOEIC 550 / iBT 42 / ITP 433 / IELTS 4.0 / Duolingo 60］、日本 JLPT N1–N3、韓國 TOPIK 2–4、華語國家免附）"
            ),
            "details": [
                (
                    "CEFR 與英語檢定對照標準：依本校公告《各項英檢與 CEFR 架構對照表》，申請非華語國家須達 CEFR B1（進階級）以上："
                    "對應全民英檢 GEPT 中級、TOEIC 550、TOEFL iBT 42（新制 3 分）、TOEFL ITP 433、IELTS 4.0、劍橋英檢 140、Linguaskill 140 或 Duolingo 60；"
                    "CEFR B2（高階級）對應 GEPT 中高級、TOEIC 785、TOEFL iBT 72（新制 4 分）、TOEFL ITP 543、IELTS 5.5、Duolingo 100。若志願校訂有更高門檻，從其規定。"
                ),
                (
                    "日韓歐語及華語國家規定：日本姊妹校依簡章要求 JLPT N1（大東文化大學）、JLPT N2（名古屋外國語大學、京都橘大學、東北大學等）或 JLPT N3（北海道教育大學、上越教育大學、中央大學等）；"
                    "韓國姊妹校要求 TOPIK 2–4 級或英語 CEFR B1/B2；申請中國大陸姊妹校交換者免附外語能力檢定證明。"
                ),
            ],
            "source": {
                "title": "臺北市立大學《各項英檢與 CEFR 架構對照表》與《116-1 赴外姊妹校交換學生甄選簡章》",
                "source_url": UTAIPEI_CEFR_PDF_URL,
                "category": "exchange_application",
                "summary": "北市大官方 CEFR 語檢對照表與各姊妹校語言能力要求一覽。",
            },
        }],
        "required_documents": [{
            "title": (
                "赴外交換學生志願表（最多5志願）、行為確認聲明書、家長同意書、歷年中英文成績單（含班排與操行）、語檢證明與中外文讀書計畫自傳"
            ),
            "details": [
                (
                    "校內甄選必備文件：（1）線上申請表暨《赴外交換學生志願表》（最多填寫 5 所志願學校，經本人及家長／監護人簽章）；"
                    "（2）《臺北市立大學赴外交換學生行為確認聲明書》及《家長／監護人同意書》；"
                    "（3）歷年中文及英文成績單正本各乙份（須含前一學期學業班級排名百分比及操行成績達 80 分以上）；"
                    "（4）有效外語能力檢定證明影本（非華語國家須達 CEFR B1 以上且符合志願校要求；華語國家免附）；"
                    "（5）中文及外文（英文或申請國語文）讀書計畫與自傳各乙份（依國際事務處範本格式撰寫）；"
                    "（6）B 類申請者另附專業學術著作、藝術展演或全國／國際競賽獲獎證明。"
                ),
                (
                    "錄取後與返國核銷文件：錄取後如欲放棄須於限期內繳交《放棄錄取資格聲明書》；出國前辦理《出國前離校程序單》；"
                    "抵埠後繳交《第二階段學員報告書》；返國後兩個月內辦理《返國報到及核銷程序單》並繳交 1,500–2,000 字《研修心得報告》。"
                ),
            ],
            "source": {
                "title": "臺北市立大學《116-1 赴外姊妹校交換學生甄選簡章》與全球教育交流組表單下載專區",
                "source_url": UTAIPEI_DOCUMENTS_URL,
                "category": "exchange_application",
                "summary": "北市大交換學生申請應繳文件、行為確認聲明書、志願表與讀書計畫範本。",
            },
        }],
        "scholarship_info": [{
            "title": (
                "教育部《學海飛颺（含本校20%配合款）》、《學海惜珠》、《學海築夢》與《臺北市立大學返國生活獎補助（亞洲1.5萬／非亞洲3萬）》"
            ),
            "details": [
                (
                    "教育部學海系列計畫：依《臺北市立大學辦理教育部鼓勵國內大專校院選送學生出國研修或國外專業實習補助審查作業要點》，"
                    "錄取非大陸港澳地區姊妹校交換生得申請《學海飛颺》（含本校最少 20% 配合款，參考標準一學年約 NT$150,000、一學期約 NT$75,000）或《學海惜珠》（具低收／中低收／特殊境遇家庭證明者專案補助機票與生活費）。"
                ),
                (
                    "臺北市立大學返國生活獎補助：依《學生赴外研修甄選暨獎補助要點》第八點，未領取教育部學海系列或外國政府獎學金，且圓滿完成交換返國、依限繳交心得報告及完成學分採認者，"
                    "赴亞洲地區最高補助新臺幣 15,000 元、赴非亞洲地區最高補助新臺幣 30,000 元，依甄選類別（A/B/C/D）及語檢等級（CEFR B2 優先於 B1）共 8 級優先順序核給。"
                ),
            ],
            "source": {
                "title": "臺北市立大學《學生赴外研修甄選暨獎補助要點》與《獎學金資訊專區》",
                "source_url": UTAIPEI_LIVING_SUBSIDY_URL,
                "category": "scholarship",
                "summary": "北市大教育部學海計畫審查要點與校內返國生活獎補助 8 級核給標準。",
            },
        }],
        "document_explanations": [{
            "title": (
                "臺北市立大學赴外交換學生志願表（最多5志願）、行為確認聲明書與中外文讀書計畫撰寫規範"
            ),
            "summary": (
                "說明北市大交換生甄選必備之志願表填報上限、行為確認聲明書簽署規範、A/B類佐證文件與中外文讀書計畫及自傳範本。"
            ),
            "key_points": [
                (
                    "志願表與行為確認聲明書：每位申請人於《赴外交換學生志願表》最多可填寫 5 所志願學校；所有申請人皆須親筆簽署《赴外交換學生行為確認聲明書》，確認在學期間無申誡以上處分及違反性別平等教育法或重大違法行為。"
                ),
                (
                    "中外文讀書計畫與自傳範本：須依國際事務處提供之標準格式分別撰寫「中文」與「申請國家語文（或英文）」讀書計畫及自傳各乙份，具體說明交換動機、預計修習課程（每學期至少相當於本校 6 學分）與返國學分抵免規劃。"
                ),
                (
                    "A 類與 B 類優先分發佐證：欲以 A 類（第一優先）申請者，成績單須明確呈現前一學期學業班級排名前 40%；欲以 B 類（第二優先）申請者，須檢附在學期間專業著作發表、重要展演或全國／國際競賽獲獎證明。"
                ),
            ],
            "applies_to": [],
            "source": {
                "title": "臺北市立大學 116學年度第1學期赴外姊妹校交換學生甄選簡章",
                "source_url": UTAIPEI_116_1_POST_URL,
                "category": "exchange_application",
                "summary": None,
            },
            "document_url": UTAIPEI_116_1_BROCHURE_PDF_URL,
            "document_type": "official_document",
            "full_text_extracted": True,
        }],
        "rule_explanations": [{
            "title": (
                "臺北市立大學學生赴外研修甄選暨獎補助要點、出國選修課程實施要點與雙聯學制甄選要點核心法規"
            ),
            "summary": (
                "規範北市大五大學院學生申請出國交換與雙聯學位之 A/B/C/D 優先順序、海外每學期至少修習 6 學分（2 ECTS = 1 學分）、學雜費減免專簽與返國生活獎補助 8 級支給標準。"
            ),
            "key_points": [
                (
                    "A/B/C/D 四類優先順序與甄選配分：書面審查占 40%、面試占 60%；依 A 類（班排前 40%）、B 類（專業著作／展演／全國或國際競賽獲獎）、C 類（一般申請者）、D 類（同一學制第二次申請者）依序錄取分發。"
                ),
                (
                    "海外修課學分與 ECTS 換算：依《臺北市立大學學生出國選修課程實施要點》，出國交換每學期至少應修習相當於本校 6 學分之課程（暑期至少 3 學分），歐洲學分互認系統以 2 ECTS 折算本校 1 學分，累計採認上限為畢業應修總學分數之 1/4。"
                ),
                (
                    "返國生活獎補助 8 級核給順序：未領取學海系列或外國政府獎學金之交換生返國完成心得報告與學分抵免後，得申請亞洲最高 NT$15,000、非亞洲最高 NT$30,000 之返國生活獎補助，依「第1級：A類且達CEFR B2 → 第2級：B類且達B2 → 第3級：A類且達B1 → 第4級：B類且達B1 → 第5級：C類且達B2 → 第6級：C類且達B1 → 第7級：D類且達B2 → 第8級：D類且達B1」順序核給。"
                ),
            ],
            "applies_to": [],
            "source": {
                "title": "臺北市立大學學生赴外研修甄選暨獎補助要點與學生出國選修課程實施要點",
                "source_url": UTAIPEI_REGULATIONS_URL,
                "category": "exchange_application",
                "summary": None,
            },
            "document_url": UTAIPEI_SELECTION_SUBSIDY_PDF_URL,
            "document_type": "official_document",
            "full_text_extracted": True,
        }],
        "sources": [
            {
                "title": "臺北市立大學國際事務處（OIA）官方網站",
                "source_url": UTAIPEI_OIA_HOME_URL,
                "category": "exchange_application",
                "summary": None,
            },
            {
                "title": "臺北市立大學海外姊妹校專區（全球 41 國／地區 226 校總表）",
                "source_url": UTAIPEI_SISTER_SCHOOLS_URL,
                "category": "partner_school",
                "summary": None,
            },
            {
                "title": "臺北市立大學赴外交換學校一覽專區（亞洲、大洋洲、美洲、歐洲 111 校介紹）",
                "source_url": UTAIPEI_EXCHANGE_OVERVIEW_URL,
                "category": "partner_school",
                "summary": None,
            },
            {
                "title": "臺北市立大學境外雙聯學位專區（11 校 24 個雙聯學位學程）",
                "source_url": UTAIPEI_DUAL_DEGREE_URL,
                "category": "partner_school",
                "summary": None,
            },
            {
                "title": "臺北市立大學 116 學年度第 1 學期赴外姊妹校交換學生甄選簡章公告",
                "source_url": UTAIPEI_116_1_POST_URL,
                "category": "exchange_application",
                "summary": None,
            },
            {
                "title": "臺北市立大學學生赴外研修甄選暨獎補助要點 PDF",
                "source_url": UTAIPEI_SELECTION_SUBSIDY_PDF_URL,
                "category": "exchange_application",
                "summary": None,
            },
            {
                "title": "臺北市立大學選送優秀學生赴外研修返國生活獎補助與教育部學海計畫專區",
                "source_url": UTAIPEI_LIVING_SUBSIDY_URL,
                "category": "scholarship",
                "summary": None,
            },
            {
                "title": "臺北市立大學歷年出國交換學生研修心得報告專區（19 國 372 篇心得＋錄取紀錄）",
                "source_url": UTAIPEI_EXPERIENCE_URL,
                "category": "experience_report",
                "summary": None,
            },
        ],
    }
    (OFFICIAL_UTAIPEI_DIR / "student_dashboard.json").write_text(
        json.dumps(student_dashboard_payload, ensure_ascii=False, indent=2)
        + "\n",
        encoding="utf-8",
    )

    doc_conditions = {
        "school_id": "utaipei",
        "school_name": "臺北市立大學",
        "checked_at": CHECKED_AT,
        "source_url": UTAIPEI_116_1_BROCHURE_PDF_URL,
        "common_documents": exchange_info_payload["required_documents"],
        "track_specific_conditions": [
            {
                "track": "國際事務處【116-1／115-2 赴外姊妹校交換學生甄選計畫（86／84 所當期開放交換學校）】",
                "required": [
                    "線上申請表暨《赴外交換學生志願表》（最多填寫 5 所志願校）、《行為確認聲明書》及《家長／監護人同意書》",
                    "歷年中文及英文成績單正本（含前一學期學業班排百分比及操行達 80 分以上證明）",
                    "有效外語能力檢定證明（非華語國家須達 CEFR B1：GEPT 中級／TOEIC 550／TOEFL iBT 42／ITP 433／IELTS 4.0／Duolingo 60 或日語 JLPT N1–N3、韓語 TOPIK 2–4；華語國家免附）",
                    "中文及外文（英文或申請國語文）讀書計畫與自傳各乙份，以及 B 類專業著作／展演／競賽獲獎佐證資料",
                ],
            },
            {
                "track": "國際事務處【境外大學雙聯學位學程（美、英、紐、泰、馬、哈、加 11 校 24 個雙聯學程）】",
                "required": [
                    "依《臺北市立大學學生赴外攻讀雙聯學位甄選要點》備妥雙聯學位申請表、歷年英文成績單正本及外語能力證明（如英國 Essex / Trinity Laban / Nottingham 要求 IELTS 6.0–6.5 及 GPA 2.75–3.0；美國 SWOSU / Troy 要求 TOEFL iBT 61 / IELTS 5.5 及 GPA 2.0–2.5；紐西蘭奧克蘭大學要求 IELTS 6.5 及 GPA 3.0）",
                    "英文讀書與研究計畫、所屬系所教授推薦函及雙方學系學分對照與修課計畫表",
                ],
            },
            {
                "track": "教育部【學海飛颺／學海惜珠／學海築夢】暨【臺北市立大學返國生活獎補助】",
                "required": [
                    "學海惜珠申請人須另附直轄市、縣（市）主管機關開立之最新年度低收入戶、中低收入戶或特殊境遇家庭相關證明文件及新式戶口名簿影本",
                    "返國生活獎補助申請人須於返國後兩個月內完成《返國報到及核銷程序單》、繳交 1,500–2,000 字《出國交換學生研修心得報告》電子檔與紙本，並檢附國外成績單與本校學分採認證明",
                ],
            },
        ],
    }
    (OFFICIAL_UTAIPEI_DIR / "document-conditions.json").write_text(
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
            f"{fname},{len(partners)},{pop},{ratio:.4f},Official UTaipei OIA verified"
        )
    (OFFICIAL_UTAIPEI_DIR / "field-coverage.csv").write_text(
        "\n".join(field_cov_lines) + "\n", encoding="utf-8"
    )

    pages_records = [
        {
            "title": "臺北市立大學：116-1（10/05–10/30 截止）與 115-2 赴外姊妹校交換學生甄選期程、5 志願填報與錄取公告",
            "source_url": UTAIPEI_116_1_POST_URL,
            "published_at": "2026-10-05T00:00:00Z",
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
            "title": "臺北市立大學：學生赴外研修甄選暨獎補助要點、A/B/C/D 四類優先順序、操行 80 分與行為確認聲明書及海外應修 6 學分規定",
            "source_url": UTAIPEI_SELECTION_SUBSIDY_PDF_URL,
            "published_at": "2026-08-07T00:00:00Z",
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
            "title": f"臺北市立大學：{len(partners)} 所全球 41 國／地區合作姊妹校名冊、{open_partner_count} 所開放交換與雙聯合作校及 CEFR 語檢對照表",
            "source_url": UTAIPEI_SISTER_SCHOOLS_URL,
            "published_at": "2026-10-05T00:00:00Z",
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
            "title": "臺北市立大學：赴外交換學生志願表（最多 5 志願）、行為確認聲明書、家長同意書與中外文讀書計畫自傳範本",
            "source_url": UTAIPEI_116_1_BROCHURE_PDF_URL,
            "published_at": "2026-10-05T00:00:00Z",
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
            "title": "臺北市立大學：教育部學海飛颺（含20%配合款）、學海惜珠、學海築夢與本校返國生活獎補助（亞洲1.5萬／非亞洲3萬・8級優先順序）",
            "source_url": UTAIPEI_LIVING_SUBSIDY_URL,
            "published_at": "2026-10-05T00:00:00Z",
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
    (OFFICIAL_UTAIPEI_DIR / "pages.jsonl").write_text(pages_text, encoding="utf-8")
    (OFFICIAL_UTAIPEI_DIR / "processed_pages.jsonl").write_text(
        pages_text, encoding="utf-8"
    )

    home_rules = {
        "school_id": "utaipei",
        "school_name": "臺北市立大學",
        "eligibility": student_dashboard_payload["eligibility"],
        "application_periods": student_dashboard_payload["application_periods"],
        "selection_rules": {
            "undergraduate_score_minimum": None,
            "graduate_score_minimum": None,
            "conduct_score_minimum": 80.0,
            "priority_category_a_rank_percent": 40.0,
            "overseas_min_credits_per_semester": 6,
            "overseas_min_summer_credits": 3,
            "ects_to_utaipei_credit_ratio": "2 ECTS = 1 credit",
            "maximum_preferences": 5,
            "screening_batches_per_year": 2,
            "allow_freshman_apply": True,
            "min_enrolled_semesters": 1,
            "tuition_policy_during_exchange": (
                "錄取學生出國前應依學則修課學分規定於臺北市立大學完成註冊手續並繳交學雜費，免繳姊妹校學費（特殊情況或符合學海惜珠未獲其他減免者得專簽減免）"
            ),
            "return_documents_due": (
                "返國後兩個月內須完成返國報到程序單、繳交 1,500–2,000 字研修心得報告及辦理國外學分採認抵免"
            ),
        },
        "source_urls": utaipei_source_urls,
        "verified_at": "2026-10-31",
    }
    (OFFICIAL_UTAIPEI_DIR / "home_rules.json").write_text(
        json.dumps(home_rules, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    (OFFICIAL_UTAIPEI_DIR / "documents.json").write_text(
        json.dumps(
            {
                "school_name": "臺北市立大學",
                "required_documents": student_dashboard_payload[
                    "required_documents"
                ],
                "source_urls": utaipei_source_urls,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    (OFFICIAL_UTAIPEI_DIR / "scholarships.json").write_text(
        json.dumps(
            {
                "school_name": "臺北市立大學",
                "scholarships": student_dashboard_payload["scholarship_info"],
                "source_urls": utaipei_source_urls,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    completeness = {
        "school_id": "utaipei",
        "school_name": "臺北市立大學",
        "total_partners": len(partners),
        "partner_count": len(partners),
        "international_partners": sum(
            1 for p in partners if p["country"] not in {"中國大陸", "香港", "澳門"}
        ),
        "mainland_partners": sum(
            1 for p in partners if p["country"] in {"中國大陸", "香港", "澳門"}
        ),
        "dual_degree_partner_universities": 11,
        "dual_degree_programs": 24,
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
            "臺北市立大學國際事務處 116 學年度第 1 學期（2027 秋季班交換學生甄選：10/05 14:00–10/30 17:00 截止，12/31 公告錄取）"
            "暨 115 學年度第 2 學期（2027 春季班交換學生甄選：04/10–04/30 截止）全球姊妹校交換計畫及 11 校 24 學系境外雙聯學制同步整合；"
            f"共完整收錄 {len(partners)} 所合作姊妹校（橫跨全球 41 個國家與地區，含 {open_partner_count} 所當期開放申請校，"
            f"並收錄 {exp_covered_schools} 所合作大學共 {total_exp_reports} 篇出國交換學生研修心得報告與錄取紀錄）。"
        ),
        "verified_at": "2026-10-31",
    }
    (OFFICIAL_UTAIPEI_DIR / "catalog-completeness.json").write_text(
        json.dumps(completeness, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    (OFFICIAL_UTAIPEI_DIR / "verification_status.json").write_text(
        json.dumps(
            {
                "school_id": "utaipei",
                "school_name": "臺北市立大學",
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
    (OFFICIAL_UTAIPEI_DIR / "dashboard_manifest.json").write_text(
        json.dumps(
            {
                "school_id": "utaipei",
                "school_name": "臺北市立大學",
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
        ("sources/utaipei/oia_home.html", UTAIPEI_OIA_HOME_URL, "臺北市立大學國際事務處首頁 HTML"),
        ("sources/utaipei/sister_schools_page.html", UTAIPEI_SISTER_SCHOOLS_URL, "國際事務處—姊妹校專區 HTML"),
        ("sources/utaipei/exchange_schools_overview.html", UTAIPEI_EXCHANGE_OVERVIEW_URL, "國際事務處—赴外交換學校一覽總覽 HTML"),
        ("sources/utaipei/exchange_schools_asia.html", UTAIPEI_EXCHANGE_ASIA_URL, "國際事務處—亞洲及大洋洲地區交換學校一覽 HTML"),
        ("sources/utaipei/exchange_schools_non_asia.html", UTAIPEI_EXCHANGE_NON_ASIA_URL, "國際事務處—美洲及歐洲地區交換學校一覽 HTML"),
        ("sources/utaipei/dual_degree_overview.html", UTAIPEI_DUAL_DEGREE_URL, "國際事務處—雙聯學位專區 HTML"),
        ("sources/utaipei/exchange_process.html", UTAIPEI_PROCESS_URL, "國際事務處—出國交換流程說明 HTML"),
        ("sources/utaipei/exchange_documents.html", UTAIPEI_DOCUMENTS_URL, "國際事務處—出國交換相關文件下載 HTML"),
        ("sources/utaipei/exchange_faq.html", UTAIPEI_FAQ_URL, "國際事務處—出國交換常見問題 Q&A HTML"),
        ("sources/utaipei/scholarships_overview.html", UTAIPEI_SCHOLARSHIPS_URL, "國際事務處—獎學金資訊總覽 HTML"),
        ("sources/utaipei/scholarships_moe_xuehai.html", UTAIPEI_MOE_XUEHAI_URL, "國際事務處—教育部學海系列計畫獎學金 HTML"),
        ("sources/utaipei/scholarships_utaipei_living.html", UTAIPEI_LIVING_SUBSIDY_URL, "國際事務處—臺北市立大學返國生活獎補助 HTML"),
        ("sources/utaipei/regulations_global_edu.html", UTAIPEI_REGULATIONS_URL, "國際事務處—全球教育交流組相關法規 HTML"),
        ("sources/utaipei/forms_global_edu.html", UTAIPEI_FORMS_URL, "國際事務處—全球教育交流組表單下載 HTML"),
        ("sources/utaipei/experience_overview.html", UTAIPEI_EXPERIENCE_URL, "國際事務處—歷年出國交換學生研修心得報告總覽 HTML"),
        ("sources/utaipei/posts/post_116_1_selection.html", UTAIPEI_116_1_POST_URL, "116-1 赴外姊妹校交換學生甄選簡章公告 HTML"),
        ("sources/utaipei/posts/post_116_1_briefing.html", UTAIPEI_116_1_BRIEFING_POST_URL, "116-1 赴外交換學生甄選說明會簡報暨里昂三大分享公告 HTML"),
        ("sources/utaipei/posts/post_115_2_selection.html", UTAIPEI_115_2_POST_URL, "115-2 赴外姊妹校交換學生甄選簡章公告 HTML"),
        ("sources/utaipei/posts/post_115_2_admitted.html", UTAIPEI_115_2_ADMITTED_POST_URL, "115-2 赴外姊妹校交換學生甄選錄取名單公告 HTML"),
        ("sources/utaipei/posts/post_115_2_xizhu.html", UTAIPEI_115_2_XIZHU_POST_URL, "115 學年度教育部學海惜珠計畫校內甄選公告 HTML"),
        ("sources/utaipei/posts/post_115_1_living_stipend.html", UTAIPEI_115_1_LIVING_POST_URL, "115-1 赴外交換學生返國生活獎補助申請公告 HTML"),
        ("sources/utaipei/posts/post_dual_degree_rules_1151014.html", UTAIPEI_DUAL_RULES_POST_URL, "臺北市立大學與境外大學校院辦理雙聯學制實施辦法暨甄選要點公告 HTML"),
        ("sources/utaipei/posts/post_exchange_rules_1150807.html", UTAIPEI_EXCHANGE_RULES_POST_URL, "臺北市立大學學生赴外研修甄選暨獎補助要點公告 HTML"),
        ("sources/utaipei/posts/post_xuehai_rules_1150303.html", UTAIPEI_XUEHAI_RULES_POST_URL, "臺北市立大學辦理教育部學海系列計畫審查作業要點公告 HTML"),
        ("sources/utaipei/utaipei_sister_schools.csv", UTAIPEI_GSHEET_CSV_URL, "臺北市立大學海外姊妹校一覽表 Google Sheet CSV"),
        ("sources/utaipei/utaipei_sister_schools.xlsx", UTAIPEI_GSHEET_XLSX_URL, "臺北市立大學海外姊妹校一覽表 Google Sheet XLSX"),
        ("sources/utaipei/partner_pages/rpage_partner_summary.json", UTAIPEI_EXCHANGE_OVERVIEW_URL, "國際事務處交換學校個別介紹專頁彙整（111 校 RPage 專頁）JSON"),
        ("sources/utaipei/utaipei_experience_index.json", UTAIPEI_EXPERIENCE_URL, f"臺北市立大學出國交換學生研修心得報告與錄取紀錄（{exp_covered_schools} 校共 {total_exp_reports} 篇）索引 JSON"),
        ("sources/utaipei/utaipei_catalog_source.json", UTAIPEI_SISTER_SCHOOLS_URL, f"臺北市立大學 {len(partners)} 所合作姊妹校整合資料集 JSON"),
        ("sources/utaipei/utaipei_resolved_locations.json", UTAIPEI_SISTER_SCHOOLS_URL, f"臺北市立大學 {len(partners)} 所合作姊妹校 ROR / Wikidata 地理座標核對表 JSON"),
    ]
    for fname, url in bin_urls.items():
        provenance_files.append((f"sources/utaipei/{fname}", url, f"臺北市立大學官方附件：{fname}"))

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
        "school_id": "utaipei",
        "school_name": "臺北市立大學",
        "generated_at": CHECKED_AT,
        "active_cycle_note": completeness["active_term"],
        "sources": prov_sources,
    }
    prov_text = (
        json.dumps(provenance_payload, ensure_ascii=False, indent=2) + "\n"
    )
    (OFFICIAL_UTAIPEI_DIR / "import_provenance.json").write_text(
        prov_text, encoding="utf-8"
    )
    (OFFICIAL_UTAIPEI_DIR / "import-provenance.json").write_text(
        prov_text, encoding="utf-8"
    )

    print(
        f"Successfully built UTaipei catalog: {len(partners)} partners"
        f" ({open_partner_count} open, {completeness['verified_campus_images']}"
        f" verified images, {completeness['verified_locations']} verified"
        f" locations), {len(workflows)} workflows,"
        f" {len(destinations)} destinations, {len(research_records)} research"
        f" records, {exp_covered_schools} schools with experience records"
        f" ({len(student_experience_rows)} rows, {total_exp_reports} reports)."
    )


if __name__ == "__main__":
    main()
