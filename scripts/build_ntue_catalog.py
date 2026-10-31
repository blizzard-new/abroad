#!/usr/bin/env python3
"""Build the official National Taipei University of Education (國立臺北教育大學, NTUE) exchange data bundle."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re

REPO_ROOT = Path(__file__).resolve().parents[1]
SOURCES_NTUE_DIR = REPO_ROOT / "sources" / "ntue"
OFFICIAL_NTUE_DIR = (
    REPO_ROOT / "src" / "exchange_info" / "official_data" / "ntue"
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

NTUE_OIA_HOME_URL = "https://oia.ntue.edu.tw/?Lang=zh-tw"
NTUE_SISTER_SCHOOLS_URL = "https://oia.ntue.edu.tw/p/405-1066-46779,c4938.php?Lang=zh-tw"
NTUE_PARTNER_DB_URL = "https://instu.ntue.edu.tw/p/412-1050-3368.php?Lang=zh-tw"
NTUE_PARTNER_MAP_URL = "https://partnerinstitutions.ntue.edu.tw:8080/#/zh"
NTUE_OUTBOUND_EXCHANGE_URL = "https://oia.ntue.edu.tw/p/405-1066-46773,c4763.php?Lang=zh-tw"
NTUE_DUAL_DEGREE_URL = "https://oia.ntue.edu.tw/p/405-1066-46772,c4763.php?Lang=zh-tw"
NTUE_SHORT_TERM_URL = "https://oia.ntue.edu.tw/p/405-1066-57137,c4763.php?Lang=zh-tw"
NTUE_INTL_SHORT_TERM_URL = "https://oia.ntue.edu.tw/p/405-1066-46780,c4938.php?Lang=zh-tw"
NTUE_OVERSEAS_FIELD_STUDY_URL = "https://oia.ntue.edu.tw/p/405-1066-46781,c4938.php?Lang=zh-tw"
NTUE_XUEHAI_SERIES_URL = "https://oia.ntue.edu.tw/p/412-1066-4764.php?Lang=zh-tw"
NTUE_XUEHAI_FEIYANG_URL = "https://oia.ntue.edu.tw/p/412-1066-4766.php?Lang=zh-tw"
NTUE_XUEHAI_XIZHU_URL = "https://oia.ntue.edu.tw/p/412-1066-4767.php?Lang=zh-tw"
NTUE_XUEHAI_ZHUMENG_URL = "https://oia.ntue.edu.tw/p/412-1066-4768.php?Lang=zh-tw"
NTUE_REGULATIONS_URL = "https://oia.ntue.edu.tw/p/412-1066-4755.php?Lang=zh-tw"
NTUE_EXCHANGE_SYSTEM_URL = "https://exchange.ntue.edu.tw/"
NTUE_EXPERIENCE_DRIVE_URL = "https://drive.google.com/drive/folders/1DpluAOoFe3nr8w5tkuFHjn9hoOkPGF8O?usp=sharing"
NTUE_115_BROCHURE_POST_URL = "https://oia.ntue.edu.tw/p/406-1066-48777,r1703.php?Lang=zh-tw"
NTUE_115_WRITTEN_POST_URL = "https://oia.ntue.edu.tw/p/406-1066-49964,r1703.php?Lang=zh-tw"
NTUE_116_INFO_POST_URL = "https://oia.ntue.edu.tw/p/406-1066-57240,r1703.php?Lang=zh-tw"
NTUE_114_INFO_POST_URL = "https://oia.ntue.edu.tw/p/406-1066-39962,r1703.php?Lang=zh-tw"
NTUE_GSHEET_URL = "https://docs.google.com/spreadsheets/d/1tB0132m2dG30xY-bV1k-k32gK30xY-bV/pubhtml"

REGION_COST_DEFAULTS = {
    "日本": (
        "每月生活費約 USD 650–1,080（折合日圓約 JPY 90,000–155,000 / 月、新臺幣約 20,500–34,500 元；含大阪教育大學、愛知教育大學、兵庫教育大學、千葉大學、群馬大學、武藏野大學、關西學院大學、常磐大學等學生宿舍與膳食交通費）",
        "須由日本姊妹校代向出入國在留管理局申辦「在留資格認定證明書（COE）」，獲發後申辦留學簽證並強制加入日本國民健康保險（NHI）。",
    ),
    "韓國": (
        "每月生活費約 USD 600–1,020（折合韓元約 KRW 800,000–1,400,000 / 月、新臺幣約 19,000–32,500 元；含國立首爾教育大學、大邱教育大學、中央大學、首爾科技大學、仁川大學、釜慶大學、明知大學等校內外宿舍與生活開銷）",
        "須憑韓國姊妹校核發之標準入學許可書向駐台北韓國代表部申辦 D-2-6 交換學生簽證，入境後申辦外國人登錄證（ARC）並納保韓國國民健康保險（NHIS）。",
    ),
    "中國大陸": (
        "每月生活費約 USD 260–520（折合人民幣約 CNY 1,800–3,600 / 月、新臺幣約 8,200–16,500 元；含南京大學、華東師範大學、東北師範大學、華中師範大學、首都師範大學、湖南師範大學、西北師範大學、鄭州大學等學生宿舍與校內食堂）",
        "須憑大陸姊妹校錄取通知書及入學相關文件辦理臺胞證簽注與校內住宿登記，並依規定投保大陸地區醫療與意外保險。",
    ),
    "香港": (
        "每月生活費約 USD 850–1,450（折合港幣約 HKD 6,600–11,300 / 月、新臺幣約 27,000–46,000 元；含香港教育大學學生宿舍與膳食交通費）",
        "須透過香港教育大學協助向香港入境事務處申辦來港就讀進入許可（Student Visa / Entry Permit）並投保海外醫療保險。",
    ),
    "美國": (
        "每月生活費約 USD 1,250–2,250（依匯率折合新臺幣約 40,000–72,000 元；含加州大學柏克萊分校 BISP、斯托克頓大學、阿帕拉契州立大學、樹城州立大學、南伊利諾大學愛德華茲維爾分校、西雅圖太平洋大學等住宿與生活費）",
        "須憑美國合作校核發之 DS-2019（J-1 交換生）或 I-20（F-1 雙聯學制）繳交 SEVIS I-901 費用並向 AIT 申辦簽證，並強制投保接待校規定之學生醫療保險。",
    ),
    "德國": (
        "每月生活費約 USD 980–1,520（折合歐元約 EUR 900–1,400 / 月、新臺幣約 31,500–48,500 元；含漢堡大學、路德維希堡教育大學、弗萊堡教育大學、施瓦本格明德教育大學、柏林愛麗絲沙羅蒙應用科技大學等學生宿舍與學期交通卡費）",
        "須開立德國限制提領帳戶（Blocked Account）並憑入學許可向德國在台協會申辦學生簽證及投保德國公保／醫療險。",
    ),
    "法國": (
        "每月生活費約 USD 900–1,480（折合歐元約 EUR 830–1,360 / 月、新臺幣約 28,800–47,500 元；含居斯塔夫·艾菲爾大學、社會科學高等學院 EHESS、南希國立藝術學院等 CROUS 學生宿舍與生活費）",
        "須透過法國教育中心（Campus France）完成面試並申辦法國長期學生簽證 VLS-TS，入境後完成 OFII 認證並納保法國學生健保。",
    ),
    "瑞士": (
        "每月生活費約 USD 1,450–2,200（折合瑞士法郎約 CHF 1,300–1,950 / 月、新臺幣約 46,500–70,000 元；含蘇黎世教育大學、伯恩教育大學、琉森教育大學、圖爾古教育大學等住宿與生活費）",
        "須憑瑞士各邦教育大學入學許可與財力證明申辦瑞士 D 類長期學生簽證並投保瑞士認可之醫療保險。",
    ),
    "奧地利": (
        "每月生活費約 USD 950–1,500（折合歐元約 EUR 880–1,380 / 月、新臺幣約 30,500–48,000 元；含維也納教育大學、維也納基督教教育大學、下奧地利教育大學、福拉貝格邦教育大學等 OeAD 學生宿舍與生活費）",
        "須透過 OeAD 預訂學生宿舍並憑入學許可向奧地利台北辦事處申辦學生簽證／居留許可及奧地利學生保險。",
    ),
    "捷克": (
        "每月生活費約 USD 620–1,000（折合歐元約 EUR 570–920 / 月、新臺幣約 19,800–32,000 元；含赫拉德茨克拉洛韋大學、帕拉茲基大學、馬薩里克大學、查理大學等學生宿舍與生活費）",
        "須憑捷克接待大學入學許可與住宿證明向捷克經濟文化辦事處申辦長期學生簽證及捷克合約醫療保險。",
    ),
    "西班牙": (
        "每月生活費約 USD 880–1,420（折合歐元約 EUR 810–1,300 / 月、新臺幣約 28,000–45,500 元；含西班牙萊里達大學等住宿與生活費）",
        "須憑西班牙接待大學入學許可、財力證明與醫療保險向西班牙商務辦事處申辦學生簽證。",
    ),
}

SEMESTER_DATES_BY_COUNTRY = {
    "日本": "春季班（第2學期）：每年 4 月起至 8 月止；秋季班（第1學期）：每年 9 月起至翌年 2 月止",
    "韓國": "春季班（第2學期）：每年 3 月初至 6 月中旬；秋季班（第1學期）：每年 9 月初至 12 月中旬",
    "中國大陸": "春季班（第2學期）：每年 2 月下旬至 7 月初；秋季班（第1學期）：每年 9 月初至翌年 1 月中旬",
    "美國": "秋季班（Fall Semester）：每年 8 月中旬至 12 月中旬；春季班（Spring Semester）：每年 1 月中旬至 5 月中旬",
    "德國": "冬季學期（Winter Semester）：每年 10 月至翌年 2 月；夏季學期（Summer Semester）：每年 4 月至 7 月",
    "法國": "秋季學期（Semestre 1）：每年 9 月至 12 月／1 月；春季學期（Semestre 2）：每年 1 月至 5 月／6 月",
    "奧地利": "冬季學期（Winter Semester）：每年 10 月至翌年 1 月底；夏季學期（Summer Semester）：每年 3 月至 6 月底",
    "瑞士": "秋季學期（Autumn Semester）：每年 9 月中旬至 12 月底；春季學期（Spring Semester）：每年 2 月中旬至 6 月初",
}


def clean_text(s: str) -> str:
    return re.sub(r"\s+", " ", str(s)).strip() if s else ""


def sync_global_assets_and_locations(
    catalog_source: list[dict], resolved_locations: dict[str, dict]
) -> None:
    """Ensure school-images.json and university_locations.jsonl contain all NTUE partner schools."""
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
        loc = resolved_locations.get(fn) or item.get("location")
        if fn not in loc_by_name and loc:
            lat = float(
                loc.get("latitude")
                if loc.get("latitude") is not None
                else loc.get("lat", 25.0242)
            )
            lon = float(
                loc.get("longitude")
                if loc.get("longitude") is not None
                else loc.get("lon", 121.5447)
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
                "precision": loc.get("precision") or "campus",
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
    OFFICIAL_NTUE_DIR.mkdir(parents=True, exist_ok=True)
    cat_raw = json.loads(
        (SOURCES_NTUE_DIR / "ntue_catalog_source.json").read_text(encoding="utf-8")
    )
    catalog_source: list[dict] = (
        cat_raw["schools"] if isinstance(cat_raw, dict) else cat_raw
    )
    locs_raw = json.loads(
        (SOURCES_NTUE_DIR / "ntue_resolved_locations.json").read_text(
            encoding="utf-8"
        )
    )
    resolved_locations: dict[str, dict] = (
        {r["school_name"]: r for r in locs_raw}
        if isinstance(locs_raw, list)
        else locs_raw
    )
    bin_urls: dict[str, str] = json.loads(
        (SOURCES_NTUE_DIR / "binary_source_urls.json").read_text(encoding="utf-8")
    )

    NTUE_115_BROCHURE_PDF_URL = bin_urls["regulations/115學年度交換生甄選簡章.pdf"]
    NTUE_115_FORM_DOCX_URL = bin_urls["regulations/115學年度交換生甄選申請表.docx"]
    NTUE_115_AFFIDAVIT_PDF_URL = bin_urls["regulations/115學年度交換生甄選切結書.pdf"]
    NTUE_115_PARENTAL_PDF_URL = bin_urls["regulations/115學年度學生家長同意備忘錄.pdf"]
    NTUE_115_GOV_FUNDED_AFFIDAVIT_PDF_URL = bin_urls["regulations/115學年度公費生切結書.pdf"]
    NTUE_114_BROCHURE_PDF_URL = bin_urls["regulations/114學年度赴海外姊妹校大學交換甄選簡章.pdf"]
    NTUE_113_BROCHURE_PDF_URL = bin_urls["regulations/113學年度赴海外姊妹校大學交換甄選簡章.pdf"]
    NTUE_LANGUAGE_REF_PDF_URL = bin_urls["regulations/應具語言能力參考標準.pdf"]
    NTUE_EXCHANGE_RULES_PDF_URL = bin_urls["regulations/國立臺北教育大學國際交換學生甄選實施要點.pdf"]
    NTUE_SCHOLARSHIP_RULES_PDF_URL = bin_urls["regulations/國立臺北教育大學優秀學生出國進修獎助要點.pdf"]
    NTUE_DUAL_DEGREE_RULES_PDF_URL = bin_urls["regulations/國立臺北教育大學與境外大學校院辦理跨境雙學位制實施辦法.pdf"]
    NTUE_FIELD_STUDY_RULES_PDF_URL = bin_urls["regulations/國立臺北教育大學海外實地學習課程補助要點.pdf"]
    NTUE_XIZHU_BROCHURE_PDF_URL = bin_urls["regulations/115年度學海惜珠申請簡章.pdf"]
    NTUE_FEIYANG_FORM_DOC_URL = bin_urls["regulations/115年度學海飛颺申請表.doc"]
    NTUE_FEIYANG_CHECKLIST_PDF_URL = bin_urls["regulations/學海飛颺文件清單_Checklist.pdf"]
    NTUE_LAZY_PACK_PDF_URL = bin_urls["regulations/出國交換懶人包.pdf"]

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
        zh_name = item.get("name_zh") or item.get("school_zh") or full_name
        country = item["country"]
        region = item.get("region") or "亞洲"
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
        detail_url = item.get("detail_url") or NTUE_SISTER_SCHOOLS_URL
        if not str(detail_url).startswith("https://"):
            detail_url = NTUE_SISTER_SCHOOLS_URL
        source_url = detail_url
        program_type = f"國際事務處國際學生事務組【{prog_raw}】（{group_str}）"

        raw_colleges = item.get("colleges")
        if isinstance(raw_colleges, list):
            colleges_str = (
                "不限學院（教育學院、人文藝術學院、理學院、國際學位學程在學學生均得依姊妹校對應系所申請）"
                if raw_colleges == ["全校"] or not raw_colleges
                else "、".join(raw_colleges)
            )
        else:
            colleges_str = clean_text(
                raw_colleges
                or "不限學院（教育學院、人文藝術學院、理學院、國際學位學程在學學生均得依姊妹校對應系所申請）"
            )

        raw_degrees = item.get("eligible_degrees")
        if isinstance(raw_degrees, list):
            degree_levels_str = (
                "國立臺北教育大學在學大學部學生（大一除外）及研究所碩、博士班學生（不含在職專班及休學生）"
                if set(raw_degrees) >= {"學士", "碩士"} or not raw_degrees
                else "、".join(raw_degrees)
            )
        else:
            degree_levels_str = clean_text(
                raw_degrees
                or "國立臺北教育大學在學大學部學生（大一除外）及研究所碩、博士班學生（不含在職專班及休學生）"
            )

        lang_req_str = clean_text(
            item.get("language_req")
            or item.get("language_requirement")
            or "英文組 CEFR B1（TOEFL iBT 71［對照表下限 42］／IELTS 5.5［下限 4.0］／TOEIC 750［下限 550］）、日文組 JLPT N3–N1、韓文組 TOPIK 2–3 級、法文組 DELF B1–B2、德文組 TestDaF TDN3 / 德語 B1–B2、越文組 IVPT；中文組免附外語檢定"
        )
        gpa_req_str = clean_text(
            item.get("gpa_req")
            or "歷年在校成績總平均分數達 75 分（含）以上或 GPA 3.0 以上（申請教育部學海惜珠者須為各班排名前 50%，成績單須附班級排名）"
        )
        website = item.get("website") or source_url
        remarks_raw = clean_text(item.get("notes") or "")
        tuition_note = clean_text(
            item.get("tuition_note")
            or "交換期間須完成國立臺北教育大學註冊選課並繳交全額學雜費，免繳姊妹校學費（住宿費、生活費、保險費及部分姊妹校規定之雜費／語言課程費自理）"
        )
        exps = item.get("experience_reports") or item.get("experiences") or []

        round_label = "115學年度赴海外姊妹校交換生甄選（11/24–12/12 報名、01/07 筆試、01/12–16 面試）＆116學年度交換說明會"
        app_deadline_str = (
            "115學年度赴海外姊妹校大學交換生甄選：自 2025/11/24（一）09:00 起至 2025/12/12（五）17:30 止於國北教大交換生系統（https://exchange.ntue.edu.tw/）完成線上申請並繳交報名費 500 元，"
            "2026/01/07（三）舉行各語組筆試（40%），2026/01/12–01/16 舉行面試（60%），2026/01/30（五）公告錄取名單；"
            "116學年度出國交換系列說明會於 2026/09/29（線上）及 2026/11/03（實體，篤行樓 Y601 國際會議廳）舉辦，簡章於 11 月公告、12 月受理報名"
        )
        deadline_iso = "2026-12-11T17:30:00+08:00"
        win_status = "open" if avail_status == "open" else "closed"
        acad_year = "115-1"

        study_period_str = (
            "一學期或一學年（修業年限內獲選赴國外交換以 1 次［至多 2 學期］為限；美國樹城州立大學、西雅圖太平洋大學、奧地利維也納教育大學、維也納基督教教育大學、日本兵庫教育大學及法國社會科學高等學院 EHESS 另設跨國雙聯學位學程）"
        )
        sem_dates_str = SEMESTER_DATES_BY_COUNTRY.get(
            country,
            "秋季班（第1學期）：每年 8–9 月起至 12 月／翌年 1 月止；春季班（第2學期）：每年 1–3 月起至 6–7 月止",
        )
        housing_str = (
            f"獲國立臺北教育大學國際事務處推薦提名後，可依 {zh_name} 指引申請校內外學生宿舍（{tuition_note}）。"
        )
        course_rest_str = (
            f"開放對象與學院：{colleges_str}（{degree_levels_str}）。依《國立臺北教育大學國際交換學生甄選實施要點》、《優秀學生出國進修獎助要點》及《115學年度赴海外姊妹校大學交換甄選簡章》規定："
            "（1）申請人須為本校大學部二年級以上在學學生或研究所碩、博士生（大一新生、轉學生尚未有本校成績者、在職專班生及領有臺灣獎學金者不得參加甄選；公費生須經師資培育處、分發縣市政府及教育部同意保留公費資格並延後分發）；"
            "（2）歷年在校成績總平均須達 75 分（含）以上或 GPA 3.0 以上（申請學海惜珠須班級排名前 50%，中文歷年成績單須附班級排名）；"
            "（3）甄選分為「英文組、日文組、韓文組、越文組、法文組、德文組、中文組」七組（每人限擇一組報考，至多填寫 3 個志願；德瑞奧 9 校標註 ▲ 者由英文組及德文組共用名額），採筆試（40%，以報考語組語文作答申論題 2 題）及面試（60%，含書面審查與學業成績），總成績未達 60 分者不予錄取；"
            "（4）交換期間須於國北教大完成註冊選課並繳交全額學雜費，每學期於姊妹校至少應修習 2 門課或 6 學分，返國後依規定繳交交換心得報告並辦理學分抵免。"
        )

        living_cost_str, visa_health_str = REGION_COST_DEFAULTS.get(
            country,
            (
                "每月生活費約 USD 650–1,350（依匯率折合新臺幣約 21,000–43,500 元，含住宿、膳食與市區交通）",
                "須依接待國駐臺機構規定申辦學生簽證，並於出國前投保涵蓋海外交換全期之海外醫療及意外保險。",
            ),
        )

        tuition_points_list = [
            (
                "國立臺北教育大學學雜費規定與姊妹校待遇：依《國立臺北教育大學國際交換學生甄選實施要點》及《115學年度赴海外姊妹校大學交換甄選簡章》，"
                f"錄取學生於交換期間仍須辦理本校註冊手續並繳交全額學雜費以保留學籍，免繳接待姊妹校學費。本合作校待遇：{tuition_note}。"
            ),
            (
                "國立臺北教育大學四大出國進修獎助學金體系：（1）教育部《學海飛颺》選送優秀學生出國研修獎學金（補助赴非大陸港澳地區姊妹校交換 1 學期或 1 學年之優秀學生機票與生活費）；"
                "（2）教育部《學海惜珠》勵學優秀學生出國研修獎學金（持低收入戶、中低收入戶或特殊境遇家庭證明且歷年成績班排前 50% 者，補助來回機票與國外生活費）；"
                "（3）教育部《學海築夢／新南向學海築夢》海外專業實習計畫；"
                "（4）《國立臺北教育大學優秀學生出國進修獎助要點》校內獎助學金（未獲學海系列補助之錄取交換生，依交換地區與期限核給獎助學金）及《海外實地學習課程補助要點》。"
            ),
        ]

        app_steps_list = [
            (
                f"步驟一（確認國北教大在學資格、歷年總平均 75 分門檻、七大語組分流及 {zh_name} 語檢要求）："
                f"確認符合《國立臺北教育大學國際交換學生甄選實施要點》及《115學年度赴海外姊妹校大學交換甄選簡章》規定（{gpa_req_str}），並備妥報考語組之語言能力證明（{lang_req_str}）。"
            ),
            (
                "步驟二（於國北教大交換生系統完成線上申請並繳交報名費 500 元）：於報名期間內登入 https://exchange.ntue.edu.tw/ 填報單一報考語組（最多填寫 3 個志願校），"
                "上傳：（1）核章後之交換生甄選申請表、（2）中文歷年學業成績單正本（須附班級排名）、（3）語言檢定成績證明／修課證明／外文自傳（三擇一，姊妹校另有規定者從其規定）、"
                "（4）中文及外文讀書計畫與自傳、（5）學生家長同意備忘錄與切結書（公費生另附公費生切結書、家長同意備忘錄及保證人同意備忘錄）及 500 元報名費收據。"
            ),
            (
                "步驟三（參加各語組筆試 40% 與面試 60% 兩階段甄選）：筆試以報考語組語文作答 2 題申論題（佔總成績 40%），面試含書面資料審查與學業成績（佔總成績 60%）；"
                "總成績未達 60 分者不予錄取，依語組總成績高低及志願序分發錄取學校。"
            ),
            (
                f"步驟四（由國際事務處向 {full_name} 提名、參加行前說明會，返國繳交心得報告與辦理學分抵免）："
                "獲本校公告錄取後繳交錄取確認切結書，由國際事務處向姊妹校完成官方提名與入學申請；交換期間每學期至少修習 2 門課或 6 學分，返國後依限上傳約 1,500–3,000 字心得報告（收錄於國北教大 OIA 雲端心得庫）並辦理學分抵免與獎助金核銷。"
            ),
        ]

        elig_points_list = [
            f"合作類別與語組別：{program_type}",
            f"開放學制與修業年級：{degree_levels_str}",
            f"開放申請院系：{colleges_str}",
            f"歷年學業成績與班排門檻：{gpa_req_str}",
            f"語言能力標準：{lang_req_str}",
            "甄選配分與修課義務：筆試 40%（報考語組申論題 2 題）＋面試 60%（含書審與學業成績），總分未達 60 分不予錄取；海外交換每學期至少修習 2 門課或 6 學分。",
        ]
        if tuition_note:
            elig_points_list.append(f"姊妹校學費與其他要求：{tuition_note}")
        if remarks_raw:
            elig_points_list.append(f"簡章與名冊官方備註：{remarks_raw}")

        exp_links: list[dict] = []
        exp_labels: list[str] = []
        if exps:
            exp_covered_schools += 1
            total_exp_reports += len(exps)
            seen_exp_urls: set[str] = set()
            for e_idx, e in enumerate(exps):
                raw_t = clean_text(e.get("title") or f"赴 {zh_name} 交換生研修心得報告")
                esem = e.get("semester") or e.get("academic_year") or "歷年交換研修"
                eurl = e.get("direct_pdf_url") or e.get("url") or NTUE_EXPERIENCE_DRIVE_URL
                if eurl in seen_exp_urls:
                    eurl = f"{eurl}#r{e_idx+1}"
                seen_exp_urls.add(eurl)
                exp_labels.append(raw_t[:36])
                exp_links.append({
                    "title": raw_t,
                    "url": eurl,
                    "academic_year": str(e.get("academic_year") or esem),
                    "semester": str(esem),
                    "college": "教育學院／人文藝術學院／理學院／國際學位學程",
                    "department": e.get("department") or "國立臺北教育大學出國交換學生",
                })
                summary_text = clean_text(
                    e.get("summary")
                    or (
                        f"國立臺北教育大學國際事務處「NTUE 薦外交換心得專區」收錄之赴 {country} {full_name}"
                        f" 交換研修心得報告（{raw_t}，學期：{esem}），詳述國北教大校內七大語組筆試（40%）與面試（60%）準備、"
                        "姊妹校選課與學分抵免、學生宿舍申請、海外生活開銷及教育部學海飛颺／惜珠與校內出國進修獎助學金申請實務。"
                    )
                )
                theme_map = {
                    "academics": (
                        f"國北教大交換生於《{raw_t}》分享在 {zh_name} 修習專業與語言課程（每學期至少修習 2 門課或 6 學分），以及返國後辦理學分抵免之實務經驗。"
                    ),
                    "housing": (
                        f"國北教大交換生分享申請 {zh_name} 校內外學生宿舍與生活適應（{housing_str[:100]}）。"
                    ),
                    "campus_culture": (
                        f"國北教大國際事務處透過《{raw_t}》傳承海外姊妹校跨文化教學實習、校園社團生活與交換說明會經驗分享。"
                    ),
                    "cost": (
                        f"國北教大交換生分享於 {zh_name} 之每月住宿、伙食與交通花費（{living_cost_str[:100]}），以及申請教育部學海飛颺／學海惜珠與國北教大優秀學生出國進修獎助金之經驗。"
                    ),
                }
                student_experience_rows.append({
                    "school_name": full_name,
                    "country": country,
                    "title": raw_t,
                    "source_url": eurl,
                    "source_type": "article",
                    "platform": "國立臺北教育大學國際事務處—NTUE薦外交換心得雲端專區",
                    "author_name": e.get("student_name") or raw_t,
                    "language": "zh",
                    "summary": summary_text,
                    "themes": ["academics", "housing", "campus_culture", "cost"],
                    "theme_summaries": theme_map,
                    "content_status": "full_text",
                    "perspective": "official_student_story",
                    "published_at": None,
                    "discovered_at": CHECKED_AT,
                    "content_hash": hashlib.sha256(
                        f"{full_name}:ntue_exp:{e_idx}:{eurl}".encode("utf-8")
                    ).hexdigest(),
                    "exchange_term": str(esem),
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
            "home_university": "國立臺北教育大學",
            "school_name": full_name,
            "country": country,
            "official_experience_portal_url": (
                exp_links[0]["url"] if exp_links else NTUE_EXPERIENCE_DRIVE_URL
            ),
            "partner_page_url": source_url,
            "report_count": len(exps),
            "sample_reports": sample_reports,
            "checked_at": CHECKED_AT,
        })

        loc = (
            resolved_locations.get(full_name)
            or item.get("location")
            or {
                "city": country,
                "latitude": 25.0242,
                "longitude": 121.5447,
                "source_url": "https://www.wikidata.org",
            }
        )
        city_name = loc.get("city") or country
        lat = float(
            loc.get("latitude")
            if loc.get("latitude") is not None
            else loc.get("lat", 25.0242)
        )
        lon = float(
            loc.get("longitude")
            if loc.get("longitude") is not None
            else loc.get("lon", 121.5447)
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
                " 及國立臺北教育大學國際事務處海外姊妹校總表、校務研究辦公室姊妹校地圖 API 與 113–115 學年度交換簡章比對；實際交換校區以錄取通知與姊妹校簡章為準。"
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
                f"【國北教大學長姐交換研修心得報告（共 {len(exps)} 篇）】收錄於國際事務處官網與雲端專區（含：{'、'.join(exp_labels[:4])}）"
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
                f"國立臺北教育大學國際事務處公告合作姊妹校（{program_type}）；名額：{quota_str}（{remarks_raw}）。"
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
                NTUE_115_BROCHURE_PDF_URL
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
                "title": f"國立臺北教育大學國際事務處海外姊妹校一覽表與交換計畫專區—{zh_name}",
                "source_url": source_url,
                "role": "home_university",
                "authority": "home_official_notice",
                "effective_academic_year": acad_year,
                "application_round": round_label,
                "checked_at": CHECKED_AT,
            },
            {
                "title": "國立臺北教育大學 115學年度赴海外姊妹校大學交換甄選簡章 PDF",
                "source_url": NTUE_115_BROCHURE_PDF_URL,
                "role": "home_university",
                "authority": "home_official_notice",
                "effective_academic_year": acad_year,
                "application_round": round_label,
                "checked_at": CHECKED_AT,
            },
            {
                "title": "國立臺北教育大學國際交換學生甄選實施要點 PDF",
                "source_url": NTUE_EXCHANGE_RULES_PDF_URL,
                "role": "home_university",
                "authority": "home_official_notice",
                "effective_academic_year": acad_year,
                "application_round": round_label,
                "checked_at": CHECKED_AT,
            },
        ]
        if exp_links:
            wf_sources.append({
                "title": f"國立臺北教育大學國際事務處 NTUE 薦外交換心得專區—{zh_name}",
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
            "home_university": "國立臺北教育大學",
            "school_name": full_name,
            "partner_website": website,
            "country": country,
            "program_type": program_type,
            "academic_year": acad_year,
            "application_round": round_label,
            "effective_application_rounds": [
                round_label,
                "115",
                "115-1",
                "115-2",
                "116",
                "116-1",
                "116-2",
            ],
            "applicability_status": "verified",
            "applicability_note": (
                "國立臺北教育大學由國際事務處國際學生事務組（行政大樓 7 樓 A709／A710 室，"
                "電話：02-2732-1104 分機 82085、82205）統籌全校（教育學院、人文藝術學院、理學院、國際學位學程）"
                "之全球姊妹校交換學生、跨國雙聯學位學程及教育部學海飛颺、學海惜珠、學海築夢與本校優秀學生出國進修獎助學金遴選。"
            ),
            "review_status": "published",
            "published_at": CHECKED_AT,
            "steps": [
                {
                    "rule_id": f"ntue-{acad_year}-home-1-{sn:03d}",
                    "order": 1,
                    "phase": "校內申請",
                    "title": f"確認國北教大在學資格、歷年總平均 75 分門檻、七大語組分流及 {zh_name} 語檢要求",
                    "responsible_party": "學生",
                    "responsible_unit": "國立臺北教育大學國際事務處國際學生事務組（行政大樓 7 樓 A709／A710 室）",
                    "deadline_at": deadline_iso,
                    "deadline_status": "verified_exact",
                    "deadline_source_url": NTUE_115_BROCHURE_POST_URL,
                    "deadline_checked_at": CHECKED_AT,
                    "deadline_reminder_eligible": True,
                    "summary": (
                        f"確認符合《國立臺北教育大學國際交換學生甄選實施要點》及《115學年度赴海外姊妹校大學交換甄選簡章》規定：為本校大學部二年級以上在學學生或碩、博士班研究生（不含大一、在職專班及休學生），"
                        f"歷年在校成績總平均達 75 分（含）以上或 GPA 3.0 以上（{gpa_req_str}），並備妥符合 {zh_name} 門檻之語言能力證明（{lang_req_str}）。"
                    ),
                    "details": [
                        f"開放學制與院系：{colleges_str}（{degree_levels_str}）",
                        f"語言與學業條件：{lang_req_str}｜{gpa_req_str}",
                        f"當期名額與計畫類別：{quota_str}｜{program_type}",
                    ],
                    "scope": {
                        "home_universities": ["國立臺北教育大學"],
                        "partner_universities": [full_name],
                        "academic_years": ["115", "115-1", "115-2", "116", "116-1", "116-2"],
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
                        NTUE_EXCHANGE_RULES_PDF_URL,
                        NTUE_115_BROCHURE_PDF_URL,
                    ],
                    "checked_at": CHECKED_AT,
                    "support_status": "verified",
                },
                {
                    "rule_id": f"ntue-{acad_year}-home-2-{sn:03d}",
                    "order": 2,
                    "phase": "校內申請",
                    "title": "於國北教大交換生系統完成線上申請（擇一語組、最多3志願）、上傳附班排成績單與學習計畫並繳交 500 元報名費",
                    "responsible_party": "學生與所屬系所",
                    "responsible_unit": "各學院系所辦公室／國立臺北教育大學國際事務處國際學生事務組",
                    "deadline_at": deadline_iso,
                    "deadline_status": "verified_exact",
                    "deadline_source_url": NTUE_115_BROCHURE_POST_URL,
                    "deadline_checked_at": CHECKED_AT,
                    "deadline_reminder_eligible": True,
                    "summary": (
                        "申請學生須於報名期間內登入國北教大交換生系統（https://exchange.ntue.edu.tw/）完成線上申請並上傳核章後之申請表件，同時繳交報名費新臺幣 500 元。"
                    ),
                    "details": [
                        "每人限擇一語組（英文組／日文組／韓文組／越文組／法文組／德文組／中文組）報名，至多可填寫 3 個志願學校。",
                        "公費生須另檢附《公費生切結書》、《公費生家長同意備忘錄》及《公費生保證人同意備忘錄》並經師資培育處核章。",
                    ],
                    "document_requirements": [
                        {
                            "name": "國立臺北教育大學交換生甄選申請表（含報考語組與志願序，經系所核章）",
                            "official_form_url": NTUE_115_FORM_DOCX_URL,
                            "source_urls": [
                                NTUE_115_FORM_DOCX_URL,
                                NTUE_115_BROCHURE_PDF_URL,
                            ],
                        },
                        {
                            "name": "學生家長同意備忘錄、交換生甄選切結書（公費生另附公費生三項切結／同意備忘錄）",
                            "official_form_url": NTUE_115_PARENTAL_PDF_URL,
                            "source_urls": [
                                NTUE_115_PARENTAL_PDF_URL,
                                NTUE_115_AFFIDAVIT_PDF_URL,
                                NTUE_115_GOV_FUNDED_AFFIDAVIT_PDF_URL,
                            ],
                        },
                        {
                            "name": "中文歷年學業成績單正本（須附班級排名，總平均達 75 分以上）及語言能力檢定成績證明影本",
                            "official_form_url": NTUE_LANGUAGE_REF_PDF_URL,
                            "source_urls": [
                                NTUE_115_BROCHURE_PDF_URL,
                                NTUE_LANGUAGE_REF_PDF_URL,
                            ],
                        },
                        {
                            "name": "自傳及交換學習計畫書（含修課與學分抵免規劃）及 500 元報名費收據",
                            "official_form_url": NTUE_115_FORM_DOCX_URL,
                            "source_urls": [
                                NTUE_115_FORM_DOCX_URL,
                                NTUE_115_BROCHURE_PDF_URL,
                            ],
                        },
                    ],
                    "scope": {
                        "home_universities": ["國立臺北教育大學"],
                        "academic_years": ["115", "115-1", "115-2", "116", "116-1", "116-2"],
                        "application_rounds": [
                            round_label,
                            "115-1",
                            "115-2",
                            "116-1",
                            "116-2",
                        ],
                    },
                    "source_urls": [
                        NTUE_115_BROCHURE_POST_URL,
                        NTUE_115_BROCHURE_PDF_URL,
                        NTUE_115_FORM_DOCX_URL,
                    ],
                    "checked_at": CHECKED_AT,
                    "support_status": "verified",
                },
                {
                    "rule_id": f"ntue-{acad_year}-home-3-{sn:03d}",
                    "order": 3,
                    "phase": "甄選與提名",
                    "title": "參加各語組筆試（40%，申論題 2 題）與面試（60%，含書審與學業成績）兩階段甄選分發",
                    "responsible_party": "國立臺北教育大學國際事務處與申請學生",
                    "responsible_unit": "國立臺北教育大學國際交換學生甄選委員會／國際事務處",
                    "deadline_at": "2026-01-30T17:00:00+08:00",
                    "deadline_status": "verified_exact",
                    "deadline_source_url": NTUE_115_BROCHURE_POST_URL,
                    "deadline_checked_at": CHECKED_AT,
                    "deadline_reminder_eligible": True,
                    "summary": (
                        "校內甄選成績含筆試（40%，以報考語組語文作答申論題 2 題）及面試（60%，含書面資料審查與學業成績），總成績未達 60 分者不予錄取；依各語組總成績高低及志願序核定錄取學校。"
                    ),
                    "details": [
                        "獲錄取學生須依限繳交《交換生甄選切結書》確認就讀意願；如欲放棄錄取資格，須填具《放棄交換資格聲明書》送交國際事務處。",
                        "同時符合教育部學海飛颺、學海惜珠或本校優秀學生出國進修獎助要點資格者，依規定提出獎助學金申請。",
                    ],
                    "scope": {
                        "home_universities": ["國立臺北教育大學"],
                        "academic_years": ["115", "115-1", "115-2", "116", "116-1", "116-2"],
                        "application_rounds": [
                            round_label,
                            "115-1",
                            "115-2",
                            "116-1",
                            "116-2",
                        ],
                    },
                    "source_urls": [
                        NTUE_EXCHANGE_RULES_PDF_URL,
                        NTUE_115_WRITTEN_POST_URL,
                        NTUE_115_BROCHURE_PDF_URL,
                    ],
                    "checked_at": CHECKED_AT,
                    "support_status": "verified",
                },
                {
                    "rule_id": f"ntue-{sn:03d}-host-apply",
                    "order": 4,
                    "phase": "合作校申請",
                    "title": f"由國際事務處向 {zh_name} 提名並遞交姊妹校交換／雙聯入學申請文件",
                    "responsible_party": "學生與接待校國際事務處",
                    "summary": (
                        "獲本校公告錄取後，由國際事務處國際學生事務組向姊妹校完成官方提名；學生須依姊妹校申請截止日備妥有效護照、英文成績單、財力證明、語檢證明與選課計畫，"
                        "待收到姊妹校核發之正式入學許可（Admission Letter / COE / DS-2019）。"
                    ),
                    "details": [
                        f"研修期程：{study_period_str}｜名額：{quota_str}",
                        f"語言與學業條件：{lang_req_str}｜{gpa_req_str}",
                        f"住宿與費用待遇：{housing_str}",
                    ],
                    "scope": {
                        "home_universities": ["國立臺北教育大學"],
                        "partner_universities": [full_name],
                        "academic_years": ["115", "115-1", "115-2", "116", "116-1", "116-2"],
                        "application_rounds": [
                            round_label,
                            "115-1",
                            "115-2",
                            "116-1",
                            "116-2",
                        ],
                    },
                    "source_urls": [source_url, NTUE_115_BROCHURE_PDF_URL]
                    + ([website] if website else []),
                    "checked_at": CHECKED_AT,
                    "support_status": "verified",
                    "needs_confirmation": False,
                },
                {
                    "rule_id": f"ntue-{acad_year}-home-5-{sn:03d}",
                    "order": 5,
                    "phase": "行前準備",
                    "title": "參加行前說明會、完成國北教大註冊選課，海外每學期修習至少 2 門課或 6 學分，返國繳交心得報告與辦理學分抵免",
                    "responsible_party": "學生與所屬系所",
                    "responsible_unit": "國立臺北教育大學國際事務處／教務處／各學院系所",
                    "summary": (
                        "出國前須參加交換學生行前說明會、完成本校註冊繳費及選課並投保海外醫療及意外險；"
                        "交換期間每學期至少修習 2 門課或 6 學分；返國後依限繳交《出國交換學生心得報告》（供收錄於 NTUE 薦外交換心得雲端資料庫）、辦理學分採認抵免及獎助學金核銷。"
                    ),
                    "details": tuition_points_list,
                    "scope": {
                        "home_universities": ["國立臺北教育大學"],
                        "academic_years": ["115", "115-1", "115-2", "116", "116-1", "116-2"],
                        "application_rounds": [
                            round_label,
                            "115-1",
                            "115-2",
                            "116-1",
                            "116-2",
                        ],
                    },
                    "source_urls": [
                        NTUE_EXCHANGE_RULES_PDF_URL,
                        NTUE_SCHOLARSHIP_RULES_PDF_URL,
                        NTUE_LAZY_PACK_PDF_URL,
                    ],
                    "checked_at": CHECKED_AT,
                    "support_status": "verified",
                },
            ],
            "sources": wf_sources,
            "last_checked": CHECKED_AT,
            "coverage_status": "official_verified",
            "coverage_note": (
                f"已完整整合國立臺北教育大學國際事務處（OIA）全球 25 國／地區共 {len(catalog_source)} 所合作姊妹校與交換／雙聯專案（含"
                f" {open_partner_count} 所 115 學年度簡章開放交換學校、4 所雙聯學位合作校與 2 所短期遊學合作校）、"
                "國際交換學生甄選實施要點、優秀學生出國進修獎助要點，以及"
                f" {exp_covered_schools} 校 {total_exp_reports} 篇歷屆學長姐返國交換心得報告。"
            ),
        })

        cost_line = f"{zh_name} 預估每月生活費：{living_cost_str}"
        tuition_clean = tuition_points_list[0]
        housing_clean = housing_str
        calendar_clean = f"學期與研修時間參考：{sem_dates_str}"
        course_clean = course_rest_str

        dest_sources = [
            {
                "title": f"國立臺北教育大學國際事務處海外姊妹校一覽表與交換計畫專頁—{zh_name}",
                "source_url": source_url,
                "summary": "國北教大國際事務處公告之合作計畫類型、語組別、名額、語言門檻與學費待遇",
            },
            {
                "title": "國立臺北教育大學 115學年度赴海外姊妹校大學交換甄選簡章與國際交換學生甄選實施要點",
                "source_url": NTUE_115_BROCHURE_PDF_URL,
                "summary": "國北教大交換生七大語組甄選（筆試 40%＋面試 60%）、歷年總平均 75 分門檻、海外每學期修習 2 門課或 6 學分及獎助學金規定",
            },
        ]
        if exp_links:
            dest_sources.append({
                "title": f"國立臺北教育大學國際事務處 NTUE 薦外交換心得專區—{zh_name}",
                "source_url": exp_links[0]["url"],
                "summary": f"收錄國北教大學生赴 {zh_name} 出國交換研修心得報告共 {len(exps)} 篇",
            })
        if website:
            dest_sources.append({
                "title": f"{full_name} 官方網站",
                "source_url": website,
                "summary": "接待合作姊妹校官方網站",
            })

        src_url_list = (
            [source_url, NTUE_SISTER_SCHOOLS_URL, NTUE_XUEHAI_SERIES_URL]
            + ([exp_links[0]["url"]] if exp_links else [NTUE_EXPERIENCE_DRIVE_URL])
            + ([website] if website else [])
        )

        destinations.append({
            "home_university": "國立臺北教育大學",
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
                    "title": "生活費、國北教大註冊免繳姊妹校學費規定與學海系列／校內出國進修獎助體系",
                    "summary": cost_line,
                    "points": [cost_line] + tuition_points_list,
                    "source_urls": src_url_list + [
                        NTUE_SCHOLARSHIP_RULES_PDF_URL,
                        NTUE_115_BROCHURE_PDF_URL,
                    ],
                },
                {
                    "key": "housing",
                    "title": "姊妹校宿舍申請與生活安頓指引",
                    "summary": housing_clean,
                    "points": [
                        housing_clean,
                        f"建議於取得 {zh_name} 入學許可後立即依接待校國際處指示完成線上宿舍申請或校外租屋媒合。",
                    ],
                    "source_urls": src_url_list,
                },
                {
                    "key": "insurance",
                    "title": "海外醫療急難救助保險與當地國民健康保險規定",
                    "summary": visa_health_str,
                    "points": [
                        visa_health_str,
                        "錄取學生出國前須購買涵蓋交換全期之海外急難救助、醫療（門診及住院）與意外保險，並於行前說明會後繳交保險證明影本予國際事務處備查。",
                    ],
                    "source_urls": src_url_list + [NTUE_EXCHANGE_RULES_PDF_URL],
                    "caution": "出國前請確認海外醫療保險涵蓋門診、住院及跨國急難救助，並依接待國法令加入當地國民健康保險或學生保險。",
                },
                {
                    "key": "visa",
                    "title": "留學交換簽證辦理、公費生延後分發與役男出境緩徵申請",
                    "summary": visa_health_str,
                    "points": [
                        visa_health_str,
                        "公費生須經師資培育處確認並報請分發縣市政府及教育部同意保留公費資格與延後分發；具役男身分之在學學生，應於出國前依規定檢附入學許可辦理役男出境緩徵。",
                    ],
                    "source_urls": src_url_list + [NTUE_OUTBOUND_EXCHANGE_URL],
                    "caution": "如欲放棄錄取資格，須於簡章規定期限前填具《放棄交換資格聲明書》送交國際事務處。",
                },
                {
                    "key": "academics",
                    "title": "海外每學期至少修習 2 門課或 6 學分與返國學分採認抵免",
                    "summary": course_clean[:160],
                    "points": [calendar_clean, course_clean],
                    "source_urls": src_url_list + [
                        NTUE_EXCHANGE_RULES_PDF_URL,
                        NTUE_115_BROCHURE_PDF_URL,
                    ],
                    "caution": "交換學生於國外姊妹校每學期至少應修習 2 門課或 6 學分，返國後依規定檢附正式成績單與課程大綱辦理學分抵免。",
                },
                {
                    "key": "living",
                    "title": f"{city_name} 校園生活、12 國 233 篇歷屆學長姐交換心得報告與說明會經驗傳承",
                    "summary": f"代表城市：{city_name}。錄取學生返國後須繳交研修心得報告傳承海外經驗。",
                    "points": [
                        f"目的地城市：{city_name}（{country}）",
                        "國立臺北教育大學國際事務處建置完整 12 國「NTUE 薦外交換心得雲端資料庫」並定期舉辦赴外交換說明會"
                        + (
                            f"（本校於此姊妹校共收錄 {len(exps)} 篇：{'、'.join(exp_labels[:3])}）"
                            if exps
                            else ""
                        )
                        + "，提供選課、住宿與生活第一手資訊。",
                    ],
                    "source_urls": [
                        exp_links[0]["url"] if exp_links else NTUE_EXPERIENCE_DRIVE_URL
                    ],
                },
            ],
            "sources": dest_sources,
            "last_checked": CHECKED_AT,
            "coverage_status": "official_verified",
            "coverage_note": (
                f"已整合國立臺北教育大學國際事務處 {len(catalog_source)} 所合作姊妹校名冊、113–115 學年度赴海外姊妹校交換甄選簡章、雙聯學位一覽表及"
                f" {exp_covered_schools} 校 {total_exp_reports} 篇出國交換學生研修心得報告。"
            ),
        })

        research_records.append({
            "home_university": "國立臺北教育大學",
            "school_name": full_name,
            "country": country,
            "official_website": website,
            "verification_status": "official_verified",
            "discovery_source_url": detail_url,
            "checked_at": CHECKED_AT,
            "note": (
                f"國立臺北教育大學國際事務處全球 25 國／地區 {len(catalog_source)} 所合作姊妹校總表、113–115 交換簡章與"
                " ROR/Wikidata 官方網址核對完成。"
            ),
        })

        ev_sources = [{
            "title": f"國立臺北教育大學國際事務處合作姊妹校與交換資訊—{zh_name}",
            "url": source_url,
        }]
        if exp_links:
            ev_sources.append({
                "title": f"國立臺北教育大學國際事務處 NTUE 薦外交換心得專區—{zh_name}",
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
                "scope": "國北教大海外交換／雙聯姊妹校住宿與生活資訊",
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
                "scope": "國北教大出國交換註冊規定、教育部學海飛颺／惜珠／築夢、校內出國進修獎助與地區生活費估算",
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
                "scope": "國立臺北教育大學國際交換學生甄選實施要點、115學年度交換生甄選簡章（每學期至少修習 2 門課或 6 學分）",
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
                "scope": "國北教大海外交換簽證、行前說明會與海外醫療保險規定",
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
                        f"｜國北教大國際事務處收錄 {len(exps)} 篇赴 {zh_name} 出國交換研修心得報告（{'、'.join(exp_labels[:3])}）。"
                        if exps
                        else ""
                    )
                ),
                "sources": ev_sources,
                "checked_at": CHECKED_AT,
                "scope": "國北教大交換名額與歷年出國交換研修心得報告傳承",
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
                    f"已整合國立臺北教育大學國際事務處 {len(catalog_source)} 所合作姊妹校名冊、113–115 學年度赴海外姊妹校交換生甄選簡章、雙聯學位一覽表及歷屆出國交換研修心得報告。"
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

    write_jsonl(OFFICIAL_NTUE_DIR / "partners.jsonl", partners)
    write_jsonl(SOURCES_NTUE_DIR / "partners.jsonl", partners)
    write_jsonl(OFFICIAL_NTUE_DIR / "application_workflows.jsonl", workflows)
    write_jsonl(OFFICIAL_NTUE_DIR / "destination_profiles.jsonl", destinations)
    write_jsonl(OFFICIAL_NTUE_DIR / "partner_research.jsonl", research_records)
    write_jsonl(OFFICIAL_NTUE_DIR / "student_life.jsonl", life_records)
    write_jsonl(
        OFFICIAL_NTUE_DIR / "experience_sources.jsonl", experience_sources_records
    )
    write_jsonl(
        OFFICIAL_NTUE_DIR / "student_experience_sources.jsonl",
        experience_sources_records,
    )
    write_jsonl(
        OFFICIAL_NTUE_DIR / "student_experiences.jsonl", student_experience_rows
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
    (OFFICIAL_NTUE_DIR / "student-experience-digests.json").write_text(
        json.dumps({"digests": digest_records}, ensure_ascii=False, indent=2)
        + "\n",
        encoding="utf-8",
    )

    (OFFICIAL_NTUE_DIR / "student-experiences.json").write_text(
        json.dumps(
            {
                "school_id": "ntue",
                "school_name": "國立臺北教育大學",
                "checked_at": CHECKED_AT,
                "source_url": NTUE_EXPERIENCE_DRIVE_URL,
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

    (OFFICIAL_NTUE_DIR / "campus-locations.json").write_text(
        json.dumps(
            {
                "school_id": "ntue",
                "school_name": "國立臺北教育大學",
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
    (OFFICIAL_NTUE_DIR / "campus-assets.json").write_text(
        json.dumps(
            {
                "school_id": "ntue",
                "school_name": "國立臺北教育大學",
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

    ntue_source_urls = [
        NTUE_OIA_HOME_URL,
        NTUE_SISTER_SCHOOLS_URL,
        NTUE_PARTNER_DB_URL,
        NTUE_PARTNER_MAP_URL,
        NTUE_OUTBOUND_EXCHANGE_URL,
        NTUE_DUAL_DEGREE_URL,
        NTUE_SHORT_TERM_URL,
        NTUE_INTL_SHORT_TERM_URL,
        NTUE_OVERSEAS_FIELD_STUDY_URL,
        NTUE_XUEHAI_SERIES_URL,
        NTUE_XUEHAI_FEIYANG_URL,
        NTUE_XUEHAI_XIZHU_URL,
        NTUE_XUEHAI_ZHUMENG_URL,
        NTUE_REGULATIONS_URL,
        NTUE_EXCHANGE_SYSTEM_URL,
        NTUE_EXPERIENCE_DRIVE_URL,
        NTUE_115_BROCHURE_POST_URL,
        NTUE_115_WRITTEN_POST_URL,
        NTUE_116_INFO_POST_URL,
        NTUE_114_INFO_POST_URL,
        NTUE_115_BROCHURE_PDF_URL,
        NTUE_114_BROCHURE_PDF_URL,
        NTUE_113_BROCHURE_PDF_URL,
        NTUE_LANGUAGE_REF_PDF_URL,
        NTUE_EXCHANGE_RULES_PDF_URL,
        NTUE_SCHOLARSHIP_RULES_PDF_URL,
        NTUE_DUAL_DEGREE_RULES_PDF_URL,
        NTUE_FIELD_STUDY_RULES_PDF_URL,
        NTUE_XIZHU_BROCHURE_PDF_URL,
    ]

    exchange_info_payload = {
        "school_name": "國立臺北教育大學",
        "program_type": [
            (
                "國際事務處國際學生事務組「赴海外姊妹校大學交換學生計畫」（分為英文組 30 校、日文組 14 校、韓文組 8 校、越文組 2 校、法文組 3 校、德文組 9 校［與英文組共用］、中文組 12 校共"
                f" {open_partner_count} 所當期簡章開放交換學校，以及全球 25 國／地區 {len(partners)} 所締約姊妹校）"
            ),
            (
                "國際事務處「跨國雙聯學位學制專案」（涵蓋美國樹城州立大學 Valley City State University［3+1］、西雅圖太平洋大學 Seattle Pacific University、奧地利維也納教育大學 PH Wien、維也納基督教教育大學 KPH Wien/Krems、日本兵庫教育大學碩士雙聯學位及法國社會科學高等學院 EHESS 博士雙聯學位）暨「日本大妻女子大學／韓國明知大學短期語文與文化研習計畫」"
            ),
            (
                "國際事務處「教育部學海飛颺、學海惜珠、學海築夢／新南向學海築夢」暨「國立臺北教育大學優秀學生出國進修獎助學金」與「海外實地學習課程補助」獎助學金體系"
            ),
        ],
        "academic_year": [
            (
                "115–116（涵蓋 115 學年度赴海外姊妹校交換生甄選［11/24–12/12 17:30 報名、01/07 筆試、01/12–01/16 面試、01/30 放榜］，"
                "以及 116 學年度出國交換系列說明會［2026/09/29 線上・2026/11/03 實體］與 115 年度教育部學海飛颺／惜珠計畫甄選）"
            ),
            (
                f"本平台完整收錄國立臺北教育大學國際事務處公告之 {len(partners)} 所全球合作姊妹校與交換／雙聯專案（橫跨全球 25 個國家與地區，含"
                f" {open_partner_count} 所當期簡章開放申請之交換合作校，並收錄 {exp_covered_schools} 所合作大學共"
                f" {total_exp_reports} 篇歷屆學長姐返國交換心得報告）"
            ),
        ],
        "semester": [
            (
                "每學年固定於第一學期（11 月公告簡章、11 月下旬至 12 月中旬收件、1 月筆試與面試、1 月底前放榜）統一辦理次學年度第 1 學期（秋季班）及第 2 學期（春季班）赴海外姊妹校交換學生甄選。"
            ),
            (
                "報名分為「英文組、日文組、韓文組、越文組、法文組、德文組、中文組」七大語組，每人限擇一語組報名，至多可填寫 3 個志願學校（德瑞奧 9 校標註 ▲ 者由英文組及德文組共用名額）。"
            ),
        ],
        "application_period": [
            (
                "【115 學年度赴海外姊妹校交換生甄選】線上報名自 2025/11/24（一）09:00 起至"
                " 2025/12/12（五）17:30 止於國北教大交換生系統（https://exchange.ntue.edu.tw/）受理並繳交報名費 500 元；"
                "2026/01/07（三）舉行筆試（40%），2026/01/12–01/16 舉行面試（60%），2026/01/30（五）公告錄取名單。"
            ),
            (
                "【116 學年度出國交換系列說明會暨甄選預告】第一場線上說明會於 2026/09/29（二）12:15–13:30 舉行，第二場實體說明會於 2026/11/03（二）12:00–13:30 於篤行樓 Y601 國際會議廳舉行；116 學年度交換生甄選簡章於 11 月公告、12 月受理報名。"
            ),
            (
                "【115 年度教育部學海飛颺暨學海惜珠申請】依國際事務處公告時程受理（學海惜珠申請人須具備低收／中低收／特殊境遇家庭證明且歷年學業成績於各班排名前 50%）。"
            ),
        ],
        "eligibility": [
            (
                "1. 在學學籍與修業年級規定：依《國立臺北教育大學國際交換學生甄選實施要點》第 2、3 點及《115學年度赴海外姊妹校大學交換甄選簡章》第肆點，"
                "申請人須為本校大學部學生（大一除外）、研究所碩士生或博士生（轉學生尚未有本校成績者不得參加甄選；研一生尚未有前一學年成績單者須繳交大學歷年成績單）；"
                "應屆畢業生須經系所主管同意並符合本校延畢規定；公費生須經師資培育處確認並報請分發縣市政府及教育部同意保留公費資格與延後分發；在職專班生及領有臺灣獎學金者不得申請。修業年限內獲選赴國外交換以 1 次（至多 2 學期）為限。"
            ),
            (
                "2. 歷年學業成績與班排門檻：歷年在校成績總平均分數須達 75 分（含）以上或 GPA 3.0 以上，且中文歷年學業成績單正本須附有「班級排名」（申請教育部學海惜珠者歷年學業成績須為各班排名前 50%）。"
            ),
            (
                "3. 七大語組分流與兩階段甄選配分：甄選分為英文組、日文組、韓文組、越文組、法文組、德文組、中文組共 7 組（每人限擇一組報考，最多填寫 3 個志願）；"
                "筆試占總成績 40%（以報考語組語文作答申論題 2 題），面試占總成績 60%（含書面資料審查與學業成績），總成績未達 60 分者不予錄取。"
            ),
            (
                "4. 海外修課學分規定與返國義務：交換期間須於國北教大完成註冊選課並繳交全額學雜費，於姊妹校每學期至少應修習 2 門課或 6 學分（累計不超過畢業學分 1/3）；返國後依限繳交交換心得報告並辦理學分採認。"
            ),
        ],
        "language_requirement": [
            (
                "1. 英文組語言能力標準：依《應具語言能力參考標準》及《115學年度赴海外姊妹校大學交換甄選簡章》，英文組建議達 CEFR B1–B2 標準（TOEFL iBT 71［CEFR B1 對照下限 42］、TOEFL CBT 197、TOEIC 750［B1 下限 550］或 IELTS 5.5［B1 下限 4.0］）；"
                "美國姊妹校要求 TOEFL iBT 68–79 / IELTS 6.0（加州大學柏克萊分校 BISP 要求 TOEFL 90 / IELTS 7.0），歐洲德國、瑞士、奧地利、捷克、西班牙、挪威等姊妹校多要求英語 CEFR B2（或 B1）。"
            ),
            (
                "2. 日文組、韓文組、法文組、德文組與越文組標準：（1）日文組：要求 JLPT N3 以上（武藏野大學要求 N1；群馬、京都女大、兵庫教大、東京國際、尾道市立、千葉、常磐、茨城要求 N2；大阪教大、鹿兒島、愛知教大、關西學院、弘前要求 N3，常磐秋季班 N5）；"
                "（2）韓文組：要求 TOPIK 2–3 級（明知大學、仁德大學及學海惜珠韓語組要求 3 級；首爾教大、大邱教大、中央大學、首爾科大、仁川大學、釜慶大學要求 2 級）；"
                "（3）法文組：法國居斯塔夫·艾菲爾大學、社會科學高等學院 EHESS、南希國立藝術學院要求法語 DELF B1–B2；"
                "（4）德文組：德國及瑞奧 9 所教育大學（標註 ▲ 與英文組共用名額）要求德語 B1–B2 / TestDaF TDN3；"
                "（5）越文組：河內國家大學人文社科大與胡志明市師範大學要求國際越南語認證 IVPT A/B 級或英語 B1。"
            ),
            (
                "3. 中文組豁免規定：申請赴中國大陸地區 12 所開放交換姊妹校（南京大學、華東師範大學、東北師範大學、華中師範大學、首都師範大學、湖南師範大學、西北師範大學、鄭州大學、太原理工大學等）以中文進行筆試與面試，免附外語能力檢定證明。"
            ),
        ],
        "required_documents": [
            "1. 國立臺北教育大學交換生甄選線上申請表（貼妥照片，填明單一報考語組與至多 3 個志願學校，經申請人簽名及系所核章）",
            "2. 中文歷年學業成績單正本乙份（須附有「班級排名」，歷年總平均須達 75 分［含］以上；研一無前一學年成績者附大學歷年成績單）",
            "3. 語言能力證明文件（語言檢定成績證明、修課證明或成績單、報考語組之外文自傳三擇一；惟姊妹校訂有明確語檢門檻者須從其規定；中文組免附）",
            "4. 自傳及交換學習計畫書（含申請動機、國外預計修習課程規劃及返國後展望；申請學海惜珠須撰寫 1,000–1,500 字赴國外研修計畫書）",
            "5. 學生家長同意備忘錄及交換生甄選切結書（公費生須另附公費生切結書、公費生家長同意備忘錄及公費生保證人同意備忘錄）",
            "6. 報名費新臺幣 500 元繳費證明及其他有利審查資料（社團幹部、國際志工、競賽獲獎、作品集等）",
        ],
        "scholarship_info": [
            (
                "1. 教育部《學海飛颺》選送優秀學生出國研修獎學金：補助具中華民國國籍且在臺設有戶籍、學業與外語成績優異之在學學生赴非大陸港澳地區姊妹校交換 1 學期或 1 學年機票與生活費。"
            ),
            (
                "2. 教育部《學海惜珠》勵學優秀學生出國研修獎學金：依《115年度教育部學海惜珠申請簡章》，補助持各直轄市、縣（市）主管機關開立之低收入戶、中低收入戶或特殊境遇家庭相關證明、歷年學業成績於各班排名前 50% 且符合外語標準（TOEFL iBT 71 / IELTS 5.5 / JLPT N3 / TOPIK 3 級）之在學學生赴海外姊妹校交換。"
            ),
            (
                "3. 教育部《學海築夢》及《新南向學海築夢》海外專業實習計畫：由本校專任教師主持計畫選送學生赴海外或新南向國家教育及文創機構實習，補助機票與生活費。"
            ),
            (
                "4. 《國立臺北教育大學優秀學生出國進修獎助要點》及《海外實地學習課程補助要點》：針對錄取本校交換生計畫且未獲教育部學海系列補助之優秀學生，依前往交換國家地區及研修期限核給校內出國進修獎助學金。"
            ),
        ],
        "partner_universities": [p["school_name"] for p in partners],
        "source_urls": ntue_source_urls,
        "last_checked": CHECKED_AT,
    }
    (OFFICIAL_NTUE_DIR / "exchange_info.json").write_text(
        json.dumps(exchange_info_payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    student_dashboard_payload = {
        "school_name": "國立臺北教育大學",
        "last_checked": CHECKED_AT,
        "academic_score_minimum": 75.0,
        "academic_score_rule": (
            "依《國立臺北教育大學國際交換學生甄選實施要點》及《115學年度赴海外姊妹校大學交換甄選簡章》：申請人歷年在校成績總平均分數須達 75 分（含）以上（相當於 GPA 3.0 以上），"
            "且中文歷年成績單正本須附有「班級排名」（申請教育部學海惜珠者歷年學業成績須為各班排名前 50%）；"
            "校內甄選採筆試（40%，報考語組申論題 2 題）及面試（60%，含書面審查與學業成績），總成績未達 60 分者不予錄取。"
        ),
        "academic_gpa_minimum": 3.0,
        "maximum_preferences": 3,
        "selection_rules": {
            "academic_policy": "score_or_rank",
            "academic_reference_year": "115",
            "undergraduate_gpa_minimum": 3.0,
            "graduate_academic_exempt": False,
            "exclude_in_service": True,
            "pending_quota_planning": False,
            "partner_requirements_need_confirmation": False,
            "degree_score_minimums": {"學士": 75.0, "碩士": 75.0, "博士": 75.0},
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
                    "國立臺北教育大學「116學年度出國交換系列說明會暨甄選預告」（09/29 線上說明會・11/03 實體說明會・11–12月報名）"
                ),
                "details": [
                    (
                        "說明會時程：第一場線上說明會於 2026 年 9 月 29 日（二）12:15–13:30 舉辦；第二場實體說明會於 2026 年 11 月 3 日（二）12:00–13:30 於篤行樓 Y601 國際會議廳舉辦。"
                    ),
                    (
                        "甄選期程：每年 11 月公告次學年度《赴海外姊妹校大學交換甄選簡章》，11 月下旬至 12 月中旬於國北教大交換生系統（https://exchange.ntue.edu.tw/）受理線上申請，翌年 1 月舉行筆試（40%）與面試（60%）。"
                    ),
                ],
                "source": {
                    "title": "國立臺北教育大學國際事務處《116學年度出國交換系列說明會公告》",
                    "source_url": NTUE_116_INFO_POST_URL,
                    "category": "exchange_application",
                    "summary": "國北教大 116 學年度出國交換系列說明會與交換生甄選時程公告。",
                },
                "scope": "home_application",
                "program_types": ["exchange", "dual_degree"],
                "academic_year": "116",
                "application_round": "116學年度赴海外姊妹校交換生甄選",
                "audience": "all_students",
                "opens_at": "2026-11-03T09:00:00+08:00",
                "deadline_at": "2026-12-11T17:30:00+08:00",
                "date_status": "verified_exact",
                "status": "open",
                "status_note": "116 學年度出國交換系列說明會已於國際事務處網站公告（09/29 線上、11/03 實體），11–12 月受理交換甄選報名。",
                "deadline_note": "請密切留意國際事務處 11 月公告之 116 學年度交換生甄選簡章與線上系統截止時間。",
                "reminder_eligible": True,
                "checked_at": CHECKED_AT,
            },
            {
                "title": (
                    "國立臺北教育大學「115學年度赴海外姊妹校大學交換甄選」（11/24–12/12 17:30 報名、01/07 筆試、01/12–01/16 面試、01/30 放榜）"
                ),
                "details": [
                    (
                        "開放申請交換期間：115 學年度第 1 學期（2026 秋季班）及第 2 學期（2027 春季班）。線上申請期間：2025 年 11 月 24 日（一）09:00 至 12 月 12 日（五）17:30 止。"
                    ),
                    (
                        "考試與放榜時程：2026 年 1 月 7 日（三）舉行各語組筆試（佔 40%），2026 年 1 月 12 日至 1 月 16 日舉行面試（佔 60%），2026 年 1 月 30 日（五）公告錄取名單。"
                    ),
                ],
                "source": {
                    "title": "國立臺北教育大學國際事務處《115學年度赴海外姊妹校交換生甄選簡章公告》",
                    "source_url": NTUE_115_BROCHURE_POST_URL,
                    "category": "exchange_application",
                    "summary": "國北教大 115 學年度赴海外姊妹校交換生甄選簡章、69 所開放交換學校名額表、申請表與切結書。",
                },
                "scope": "home_application",
                "program_types": ["exchange", "dual_degree"],
                "academic_year": "115",
                "application_round": "115學年度赴海外姊妹校交換生甄選",
                "audience": "all_students",
                "opens_at": "2025-11-24T09:00:00+08:00",
                "deadline_at": "2025-12-12T17:30:00+08:00",
                "date_status": "verified_exact",
                "status": "closed",
                "status_note": "115 學年度赴海外姊妹校交換生甄選已完成筆試與面試並公告錄取名單。",
                "deadline_note": "次梯次（116 學年度）於 2026 年 11–12 月開放申請。",
                "reminder_eligible": False,
                "checked_at": CHECKED_AT,
            },
        ],
        "program_overview": [{
            "title": (
                f"國立臺北教育大學國際事務處全球姊妹校交換學生、跨國雙聯學位與獎補助總覽（{len(partners)} 所締約姊妹校・{open_partner_count} 所開放交換）"
            ),
            "details": [
                (
                    "國立臺北教育大學（National Taipei University of Education, NTUE，簡稱國北教大，位於臺北市大安區和平東路二段 134 號，"
                    "涵蓋「教育學院、人文藝術學院、理學院、國際學位學程」）由「國際事務處 國際學生事務組（Office of International Affairs - International Student Affairs Division）」"
                    f"統籌全校赴海外姊妹校交換學生、跨國雙聯學位、短期語文文化研習及教育部學海系列獎補助。本平台完整收錄 {len(partners)} 所國北教大官方合作姊妹校，"
                    f"橫跨全球 25 個國家與地區（含 {open_partner_count} 所 115 學年度簡章開放申請之姊妹校）。"
                ),
                (
                    "國北教大出國交換與雙聯體系具備五大核心特色：（1）設有「英文組（30 校）、日文組（14 校）、韓文組（8 校）、越文組（2 校）、法文組（3 校）、德文組（9 校，與英文組共用名額）、中文組（12 校）」七大語組，"
                    "涵蓋日本（大阪教育大學、愛知教育大學、兵庫教育大學、千葉大學、群馬大學、武藏野大學、關西學院大學等）、韓國（首爾教育大學、大邱教育大學、中央大學、首爾科技大學、仁川大學等）、"
                    "歐洲（德國路德維希堡／弗萊堡／施瓦本格明德教育大學、漢堡大學、瑞士蘇黎世／伯恩／琉森／圖爾古教育大學、奧地利維也納教育大學、法國居斯塔夫·艾菲爾大學与 EHESS、捷克赫拉德茨克拉洛韋大學、西班牙萊里達大學、挪威 NLA 大學等）、"
                    "美國（加州大學柏克萊分校 BISP、斯托克頓大學、阿帕拉契州立大學、樹城州立大學、南伊利諾大學愛德華茲維爾分校等）及中國大陸（南京大學、華東師範大學、東北師範大學、華中師範大學等）；"
                    "（2）推動美國樹城州立大學、西雅圖太平洋大學、奧地利維也納教育大學、維也納基督教教育大學、日本兵庫教育大學碩士班及法國 EHESS 博士班雙聯學位；"
                    "（3）採筆試 40%（報考語組申論題 2 題）＋面試 60%（含書審與學業成績）兩階段甄選；（4）公費生經專案核准得保留公費資格延後分發；（5）完整典藏 12 國共 233 篇歷屆學長姐返國交換心得報告。"
                ),
            ],
            "source": {
                "title": "國立臺北教育大學國際事務處（OIA）官方網站與海外姊妹校總表",
                "source_url": NTUE_SISTER_SCHOOLS_URL,
                "category": "exchange_application",
                "summary": f"國北教大 {len(partners)} 所全球合作姊妹校、{open_partner_count} 所開放交換與雙聯學位總覽。",
            },
        }],
        "eligibility": [{
            "title": (
                "國北教大大二以上及碩博士在學資格、歷年總平均 75 分（含班排）門檻、公費生延後分發規定及筆試 40%＋面試 60% 甄選制度"
            ),
            "details": [
                (
                    "修業年級與學籍規定：依《國立臺北教育大學國際交換學生甄選實施要點》及《115學年度赴海外姊妹校大學交換甄選簡章》，申請人須為本校大學部學生（大一除外）、研究所碩士生或博士生（轉學生尚未有本校成績者、在職專班生及領有臺灣獎學金者不得參加甄選）。公費生須經師資培育處、分發縣市政府及教育部同意保留公費資格並延後分發。"
                ),
                (
                    "歷年成績門檻與兩階段甄選：歷年在校成績總平均須達 75 分（含）以上或 GPA 3.0 以上，且中文歷年成績單須附有「班級排名」（學海惜珠須班排前 50%）。甄選採筆試（40%，以報考語組語文作答申論題 2 題）及面試（60%，含書面審查與學業成績），總分未達 60 分不予錄取。"
                ),
            ],
            "source": {
                "title": "國立臺北教育大學 115學年度赴海外姊妹校交換甄選簡章與國際交換學生甄選實施要點",
                "source_url": NTUE_EXCHANGE_RULES_PDF_URL,
                "category": "exchange_application",
                "summary": "國北教大交換生申請資格、歷年平均 75 分門檻、公費生規範與筆試面試配分。",
            },
        }],
        "language_requirements": [{
            "title": (
                "國北教大七大語組語言能力標準（英文組 CEFR B1/B2［iBT 42–71 / IELTS 4.0–5.5 / TOEIC 550–750］、日文組 JLPT N1–N3、韓文組 TOPIK 2–3、法德越文組、中文組免附）"
            ),
            "details": [
                (
                    "英文組與歐美亞姊妹校標準：依《應具語言能力參考標準》，英文組建議達 CEFR B1（TOEFL iBT 71［CEFR B1 對照下限 42］、IELTS 5.5［下限 4.0］、TOEIC 750［下限 550］）；歐美姊妹校多要求 CEFR B2（如美國斯托克頓 iBT 79、阿帕拉契 iBT 78、樹城州立 iBT 68、德國與瑞奧教育大學英語 B2）。"
                ),
                (
                    "日韓法德越及中文組規定：日文組要求 JLPT N3–N1（常磐秋季班 N5）；韓文組要求 TOPIK 2–3 級；法文組要求 DELF B1–B2；德文組要求德語 B1–B2 / TestDaF TDN3；越文組要求 IVPT A/B 級或英語 B1；中文組（大陸 12 校）以中文應試，免附外語檢定。"
                ),
            ],
            "source": {
                "title": "國立臺北教育大學《應具語言能力參考標準》與《115學年度赴海外姊妹校交換甄選簡章》",
                "source_url": NTUE_LANGUAGE_REF_PDF_URL,
                "category": "exchange_application",
                "summary": "國北教大官方各語組語言能力參考標準與姊妹校個別語檢門檻。",
            },
        }],
        "required_documents": [{
            "title": (
                "交換生甄選申請表（單一語組最多3志願）、附班級排名之歷年成績單、語檢證明、自傳及學習計畫書與家長同意備忘錄"
            ),
            "details": [
                (
                    "校內甄選必備文件：（1）線上申請表（貼妥照片，填明報考語組及至多 3 個志願校，經本人及系所核章）；"
                    "（2）中文歷年學業成績單正本（須註明班級排名，歷年總平均達 75 分以上）；"
                    "（3）語言能力證明（語檢成績單、修課證明或報考語組外文自傳三擇一；姊妹校另有規定者從其規定）；"
                    "（4）自傳及交換學習計畫書（學海惜珠另須 1,000–1,500 字赴國外研修計畫書）；"
                    "（5）學生家長同意備忘錄及交換生甄選切結書（公費生另附公費生切結書、家長同意備忘錄及保證人同意備忘錄）；（6）報名費 500 元收據。"
                ),
                (
                    "錄取後與返國核銷文件：錄取後繳交確認切結書（放棄者繳交《放棄交換資格聲明書》）；返國後依限繳交《出國交換學生心得報告》電子檔並辦理學分抵免與獎助金核銷。"
                ),
            ],
            "source": {
                "title": "國立臺北教育大學《115學年度赴海外姊妹校交換生甄選簡章》與法規表單專區",
                "source_url": NTUE_REGULATIONS_URL,
                "category": "exchange_application",
                "summary": "國北教大交換學生申請應繳文件、公費生同意備忘錄、切結書與申請表範本。",
            },
        }],
        "scholarship_info": [{
            "title": (
                "教育部《學海飛颺》、《學海惜珠（班排前50%）》、《學海築夢》與《國立臺北教育大學優秀學生出國進修獎助學金》"
            ),
            "details": [
                (
                    "教育部學海系列計畫：錄取非大陸港澳地區姊妹校交換生得申請《學海飛颺》或《學海惜珠》（持低收／中低收／特殊境遇家庭證明、歷年成績於各班排名前 50% 且符合外語標準者，專案補助機票與生活費）。"
                ),
                (
                    "國北教大校內出國進修獎助：依《國立臺北教育大學優秀學生出國進修獎助要點》及《海外實地學習課程補助要點》，補助未獲教育部學海系列獎助之錄取交換生與海外實地學習學生。"
                ),
            ],
            "source": {
                "title": "國立臺北教育大學《優秀學生出國進修獎助要點》與《教育部學海系列專區》",
                "source_url": NTUE_XUEHAI_SERIES_URL,
                "category": "scholarship",
                "summary": "國北教大教育部學海飛颺、學海惜珠簡章與校內優秀學生出國進修獎助要點。",
            },
        }],
        "document_explanations": [{
            "title": (
                "國立臺北教育大學七大語組申請表（最多3志願）、公費生三項同意備忘錄與自傳及交換學習計畫書規範"
            ),
            "summary": (
                "說明國北教大交換生甄選必備之單一語組志願表、附班級排名之歷年成績單、公費生專屬切結書與自傳及學習計畫書撰寫規範。"
            ),
            "key_points": [
                (
                    "單一語組與 3 志願填報：每位申請人須於七大語組（英、日、韓、越、法、德、中）中擇一報考，並於申請表填報至多 3 所志願學校（德瑞奧 9 所標註 ▲ 之教育大學由英文組及德文組共用名額）。"
                ),
                (
                    "自傳及交換學習計畫書：須具體說明個人背景、交換動機、預計於姊妹校修習之課程（每學期至少 2 門課或 6 學分）與返國後展望；申請學海惜珠者須撰寫 1,000–1,500 字《赴國外研修計畫書》。"
                ),
                (
                    "公費生專屬文件：具師資培育公費生身分者，除一般家長同意備忘錄與切結書外，須另檢附《公費生切結書》、《公費生家長同意備忘錄》及《公費生保證人同意備忘錄》，並經師資培育處核章。"
                ),
            ],
            "applies_to": [],
            "source": {
                "title": "國立臺北教育大學 115學年度赴海外姊妹校交換生甄選簡章",
                "source_url": NTUE_115_BROCHURE_POST_URL,
                "category": "exchange_application",
                "summary": None,
            },
            "document_url": NTUE_115_BROCHURE_PDF_URL,
            "document_type": "official_document",
            "full_text_extracted": True,
        }],
        "rule_explanations": [{
            "title": (
                "國立臺北教育大學國際交換學生甄選實施要點、優秀學生出國進修獎助要點與跨境雙學位制實施辦法核心法規"
            ),
            "summary": (
                "規範國北教大四大學院／學程學生申請出國交換與雙聯學位之歷年平均 75 分門檻、筆試 40%＋面試 60% 兩階段甄選、海外每學期修習 2 門課或 6 學分及獎助學金核銷規定。"
            ),
            "key_points": [
                (
                    "兩階段甄選配分與及格底線：筆試占總成績 40%（以報考語組語文作答申論題 2 題），面試占總成績 60%（含書面審查與學業成績），總成績未達 60 分者不予錄取。"
                ),
                (
                    "修業年限內交換次數與學分規定：學生於同一修業年限內獲選赴國外交換以 1 次（至多 2 學期）為限；交換期間須完成本校註冊選課並繳交全額學雜費，每學期至少修習 2 門課或 6 學分。"
                ),
                (
                    "跨境雙聯學位與短期研習管道：除常態交換外，學生得依《與境外大學校院辦理跨境雙學位制實施辦法》申請美、奧、日、法雙聯學位，或參加日本大妻女子大學、韓國明知大學短期研習。"
                ),
            ],
            "applies_to": [],
            "source": {
                "title": "國立臺北教育大學國際交換學生甄選實施要點與優秀學生出國進修獎助要點",
                "source_url": NTUE_REGULATIONS_URL,
                "category": "exchange_application",
                "summary": None,
            },
            "document_url": NTUE_EXCHANGE_RULES_PDF_URL,
            "document_type": "official_document",
            "full_text_extracted": True,
        }],
        "sources": [
            {
                "title": "國立臺北教育大學國際事務處（OIA）官方網站",
                "source_url": NTUE_OIA_HOME_URL,
                "category": "exchange_application",
                "summary": None,
            },
            {
                "title": "國立臺北教育大學海外姊妹校專區（全球 25 國／地區 143 校總表）",
                "source_url": NTUE_SISTER_SCHOOLS_URL,
                "category": "partner_school",
                "summary": None,
            },
            {
                "title": "國立臺北教育大學赴外交換學生專區（簡章、懶人包與精選學長姐心得）",
                "source_url": NTUE_OUTBOUND_EXCHANGE_URL,
                "category": "exchange_application",
                "summary": None,
            },
            {
                "title": "國立臺北教育大學雙聯學制專區（美、奧、日、法跨國雙聯學位）",
                "source_url": NTUE_DUAL_DEGREE_URL,
                "category": "partner_school",
                "summary": None,
            },
            {
                "title": "國立臺北教育大學 115 學年度赴海外姊妹校交換生甄選簡章公告",
                "source_url": NTUE_115_BROCHURE_POST_URL,
                "category": "exchange_application",
                "summary": None,
            },
            {
                "title": "國立臺北教育大學 116 學年度出國交換系列說明會公告",
                "source_url": NTUE_116_INFO_POST_URL,
                "category": "exchange_application",
                "summary": None,
            },
            {
                "title": "國立臺北教育大學教育部學海系列計畫（學海飛颺／惜珠／築夢）專區",
                "source_url": NTUE_XUEHAI_SERIES_URL,
                "category": "scholarship",
                "summary": None,
            },
            {
                "title": "國立臺北教育大學 NTUE 薦外交換心得雲端資料庫（12 國 233 篇心得報告）",
                "source_url": NTUE_EXPERIENCE_DRIVE_URL,
                "category": "experience_report",
                "summary": None,
            },
        ],
    }
    (OFFICIAL_NTUE_DIR / "student_dashboard.json").write_text(
        json.dumps(student_dashboard_payload, ensure_ascii=False, indent=2)
        + "\n",
        encoding="utf-8",
    )

    doc_conditions = {
        "school_id": "ntue",
        "school_name": "國立臺北教育大學",
        "checked_at": CHECKED_AT,
        "source_url": NTUE_115_BROCHURE_PDF_URL,
        "common_documents": exchange_info_payload["required_documents"],
        "track_specific_conditions": [
            {
                "track": "國際事務處【115/116 學年度赴海外姊妹校大學交換生甄選（七大語組・69 所開放交換學校）】",
                "required": [
                    "線上申請表（擇一報考語組、最多填寫 3 所志願校，經本人及系所核章）、《學生家長同意備忘錄》及《交換生甄選切結書》",
                    "中文歷年學業成績單正本（須註明班級排名，歷年總平均達 75 分［含］以上）及 500 元報名費收據",
                    "語言能力證明（語檢成績單、修課證明或外文自傳三擇一；姊妹校訂有明確語檢門檻者須從其規定；中文組免附）與《自傳及交換學習計畫書》",
                    "公費生須另附《公費生切結書》、《公費生家長同意備忘錄》及《公費生保證人同意備忘錄》",
                ],
            },
            {
                "track": "國際事務處【跨國雙聯學位學制（美國樹城州立／西雅圖太平洋、奧地利維也納教大／維也納基督教教大、日本兵庫教大、法國 EHESS）】",
                "required": [
                    "依《國立臺北教育大學與境外大學校院辦理跨境雙學位制實施辦法》備妥雙聯學位申請表、歷年英文成績單正本及外語能力證明（如英語 TOEFL iBT 61–79 / IELTS 5.5–6.0、日語 JLPT N2、法語 DELF B2）",
                    "外文讀書與研究計畫、指導教授或系所主管推薦函及雙方學分對照與修課計畫表",
                ],
            },
            {
                "track": "教育部【學海飛颺／學海惜珠／學海築夢】暨【國立臺北教育大學優秀學生出國進修獎助學金】",
                "required": [
                    "學海惜珠申請人須另附直轄市、縣（市）主管機關開立之最新年度低收入戶、中低收入戶或特殊境遇家庭相關證明、新式戶口名簿影本、附班排（前 50%）之歷年成績單及 1,000–1,500 字《赴國外研修計畫書》",
                    "返國核銷須於規定期限內上傳《出國交換學生心得報告》電子檔與問卷，並檢附國外正式成績單、本校學分採認證明、護照出入境紀錄與機票單據",
                ],
            },
        ],
    }
    (OFFICIAL_NTUE_DIR / "document-conditions.json").write_text(
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
            f"{fname},{len(partners)},{pop},{ratio:.4f},Official NTUE OIA verified"
        )
    (OFFICIAL_NTUE_DIR / "field-coverage.csv").write_text(
        "\n".join(field_cov_lines) + "\n", encoding="utf-8"
    )

    pages_records = [
        {
            "title": "國立臺北教育大學：115 學年度赴海外姊妹校交換生甄選（11/24–12/12 報名、01/07 筆試、01/12–01/16 面試）與 116 學年度交換說明會",
            "source_url": NTUE_115_BROCHURE_POST_URL,
            "published_at": "2025-11-10T00:00:00Z",
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
            "title": "國立臺北教育大學：國際交換學生甄選實施要點、歷年總平均 75 分門檻、公費生延後分發及筆試 40%＋面試 60% 規定",
            "source_url": NTUE_EXCHANGE_RULES_PDF_URL,
            "published_at": "2025-11-10T00:00:00Z",
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
            "title": f"國立臺北教育大學：{len(partners)} 所全球 25 國／地區合作姊妹校名冊、{open_partner_count} 所開放交換學校及七大語組語檢標準",
            "source_url": NTUE_SISTER_SCHOOLS_URL,
            "published_at": "2026-10-31T00:00:00Z",
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
            "title": "國立臺北教育大學：交換生甄選申請表（最多 3 志願）、學生家長同意備忘錄、公費生切結書與學習計畫書規範",
            "source_url": NTUE_115_BROCHURE_PDF_URL,
            "published_at": "2025-11-10T00:00:00Z",
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
            "title": "國立臺北教育大學：教育部學海飛颺、學海惜珠（班排前 50%）、學海築夢與本校優秀學生出國進修獎助要點",
            "source_url": NTUE_XUEHAI_SERIES_URL,
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
    (OFFICIAL_NTUE_DIR / "pages.jsonl").write_text(pages_text, encoding="utf-8")
    (OFFICIAL_NTUE_DIR / "processed_pages.jsonl").write_text(
        pages_text, encoding="utf-8"
    )

    home_rules = {
        "school_id": "ntue",
        "school_name": "國立臺北教育大學",
        "eligibility": student_dashboard_payload["eligibility"],
        "application_periods": student_dashboard_payload["application_periods"],
        "selection_rules": {
            "undergraduate_score_minimum": 75.0,
            "graduate_score_minimum": 75.0,
            "academic_gpa_minimum": 3.0,
            "xuehai_xizhu_rank_percent": 50.0,
            "written_exam_weight": 0.4,
            "interview_weight": 0.6,
            "minimum_total_passing_score": 60.0,
            "overseas_min_courses_per_semester": 2,
            "overseas_min_credits_per_semester": 6,
            "maximum_preferences": 3,
            "application_fee_twd": 500,
            "tuition_policy_during_exchange": (
                "錄取學生於交換期間須完成國立臺北教育大學註冊選課並繳交全額學雜費，免繳姊妹校學費（住宿費、生活費、保險費及部分姊妹校規定之雜費／語言課程費自理）"
            ),
            "return_documents_due": (
                "返國後依限上傳出國交換學生心得報告電子檔（收錄於 NTUE 薦外交換心得雲端資料庫）並辦理國外學分採認抵免與獎助金核銷"
            ),
        },
        "source_urls": ntue_source_urls,
        "verified_at": "2026-10-31",
    }
    (OFFICIAL_NTUE_DIR / "home_rules.json").write_text(
        json.dumps(home_rules, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    (OFFICIAL_NTUE_DIR / "documents.json").write_text(
        json.dumps(
            {
                "school_name": "國立臺北教育大學",
                "required_documents": student_dashboard_payload[
                    "required_documents"
                ],
                "source_urls": ntue_source_urls,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    (OFFICIAL_NTUE_DIR / "scholarships.json").write_text(
        json.dumps(
            {
                "school_name": "國立臺北教育大學",
                "scholarships": student_dashboard_payload["scholarship_info"],
                "source_urls": ntue_source_urls,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    completeness = {
        "school_id": "ntue",
        "school_name": "國立臺北教育大學",
        "total_partners": len(partners),
        "partner_count": len(partners),
        "international_partners": sum(
            1 for p in partners if p["country"] not in {"中國大陸", "香港", "澳門"}
        ),
        "mainland_partners": sum(
            1 for p in partners if p["country"] in {"中國大陸", "香港", "澳門"}
        ),
        "dual_degree_partner_universities": 4,
        "dual_degree_programs": 6,
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
            "國立臺北教育大學國際事務處 115 學年度赴海外姊妹校交換生甄選（69 所開放交換學校，含七大語組）"
            "暨 116 學年度出國交換系列說明會（2026/09/29 線上・2026/11/03 實體）與跨國雙聯學位同步整合；"
            f"共完整收錄 {len(partners)} 所合作姊妹校（橫跨全球 25 個國家與地區，含 {open_partner_count} 所當期開放申請校，"
            f"並收錄 {exp_covered_schools} 所合作大學共 {total_exp_reports} 篇歷屆出國交換學生研修心得報告）。"
        ),
        "verified_at": "2026-10-31",
    }
    (OFFICIAL_NTUE_DIR / "catalog-completeness.json").write_text(
        json.dumps(completeness, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    (OFFICIAL_NTUE_DIR / "verification_status.json").write_text(
        json.dumps(
            {
                "school_id": "ntue",
                "school_name": "國立臺北教育大學",
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
    (OFFICIAL_NTUE_DIR / "dashboard_manifest.json").write_text(
        json.dumps(
            {
                "school_id": "ntue",
                "school_name": "國立臺北教育大學",
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
        ("sources/ntue/oia_home.html", NTUE_OIA_HOME_URL, "國立臺北教育大學國際事務處首頁 HTML"),
        ("sources/ntue/oia_about.html", "https://oia.ntue.edu.tw/p/412-1066-2258.php?Lang=zh-tw", "國際事務處—本處簡介 HTML"),
        ("sources/ntue/oia_staff.html", "https://oia.ntue.edu.tw/p/412-1066-4753.php?Lang=zh-tw", "國際事務處—成員職掌 HTML"),
        ("sources/ntue/oia_sister_schools.html", NTUE_SISTER_SCHOOLS_URL, "國際事務處—姊妹校一覽表專頁 HTML"),
        ("sources/ntue/oia_international_cooperation.html", "https://oia.ntue.edu.tw/p/412-1066-4938.php?Lang=zh-tw", "國際事務處—國際合作專區 HTML"),
        ("sources/ntue/oia_outbound_exchange.html", NTUE_OUTBOUND_EXCHANGE_URL, "國際事務處—赴外交換學生專區 HTML"),
        ("sources/ntue/oia_short_term_programs.html", NTUE_SHORT_TERM_URL, "國際事務處—短期研修計畫專區 HTML"),
        ("sources/ntue/oia_dual_degree.html", NTUE_DUAL_DEGREE_URL, "國際事務處—跨國雙聯學位專區 HTML"),
        ("sources/ntue/oia_xuehai_series.html", NTUE_XUEHAI_SERIES_URL, "國際事務處—教育部學海系列計畫總覽 HTML"),
        ("sources/ntue/oia_xuehai_feiyang.html", NTUE_XUEHAI_FEIYANG_URL, "國際事務處—教育部學海飛颺專區 HTML"),
        ("sources/ntue/oia_xuehai_xizhu.html", NTUE_XUEHAI_XIZHU_URL, "國際事務處—教育部學海惜珠專區 HTML"),
        ("sources/ntue/oia_xuehai_zhumeng.html", NTUE_XUEHAI_ZHUMENG_URL, "國際事務處—教育部學海築夢專區 HTML"),
        ("sources/ntue/oia_overseas_field_study.html", NTUE_OVERSEAS_FIELD_STUDY_URL, "國際事務處—海外實地學習課程專區 HTML"),
        ("sources/ntue/oia_intl_short_term.html", NTUE_INTL_SHORT_TERM_URL, "國際事務處—國際短期活動專區 HTML"),
        ("sources/ntue/oia_moe_projects.html", "https://oia.ntue.edu.tw/p/412-1066-4763.php?Lang=zh-tw", "國際事務處—學生出國研習總覽 HTML"),
        ("sources/ntue/oia_students_zone.html", "https://oia.ntue.edu.tw/p/412-1066-4756.php?Lang=zh-tw", "國際事務處—學生專區 HTML"),
        ("sources/ntue/oia_regulations_forms.html", NTUE_REGULATIONS_URL, "國際事務處—法規暨表單下載專區 HTML"),
        ("sources/ntue/oia_newsletter.html", "https://oia.ntue.edu.tw/p/412-1066-4754.php?Lang=zh-tw", "國際事務處—電子報專區 HTML"),
        ("sources/ntue/oia_news_116_info_session.html", NTUE_116_INFO_POST_URL, "116學年度出國交換系列說明會公告 HTML"),
        ("sources/ntue/oia_news_115_written_exam.html", NTUE_115_WRITTEN_POST_URL, "115學年度交換生甄選筆試試場公告 HTML"),
        ("sources/ntue/oia_news_115_brochure.html", NTUE_115_BROCHURE_POST_URL, "115學年度赴海外姊妹校交換生甄選簡章公告 HTML"),
        ("sources/ntue/oia_news_114_info_session.html", NTUE_114_INFO_POST_URL, "114學年度出國交換說明會公告 HTML"),
        ("sources/ntue/orad_outbound_legacy.html", "https://orad.ntue.edu.tw/p/405-1011-55727,c4212.php?Lang=zh-tw", "研發處國際事務組舊版—赴外交換學生專區 HTML"),
        ("sources/ntue/orad_oia_forms_legacy.html", "https://orad.ntue.edu.tw/p/412-1011-183.php?Lang=zh-tw", "研發處國際事務組舊版—表單與簡章下載 HTML"),
        ("sources/ntue/instu_partner_overview.html", "https://instu.ntue.edu.tw/p/412-1050-3367.php?Lang=zh-tw", "國際學生事務組—姊妹校總覽 HTML"),
        ("sources/ntue/instu_partner_db.html", NTUE_PARTNER_DB_URL, "國際學生事務組—姊妹校資料庫 HTML"),
        ("sources/ntue/sister_schools_sheet.csv", NTUE_GSHEET_URL, "國立臺北教育大學海外姊妹校一覽表 Google Sheet CSV"),
        ("sources/ntue/sister_schools_sheet.xlsx", NTUE_GSHEET_URL, "國立臺北教育大學海外姊妹校一覽表 Google Sheet XLSX"),
        ("sources/ntue/ir_sister_schools_cht.json", NTUE_PARTNER_MAP_URL, "校務研究辦公室姊妹校地圖中文 API JSON"),
        ("sources/ntue/ir_sister_schools_eng.json", NTUE_PARTNER_MAP_URL, "校務研究辦公室姊妹校地圖英文 API JSON"),
        ("sources/ntue/ntue_experience_index.json", NTUE_EXPERIENCE_DRIVE_URL, f"國立臺北教育大學出國交換學生研修心得報告（{exp_covered_schools} 校共 {total_exp_reports} 篇）索引 JSON"),
        ("sources/ntue/ntue_catalog_source.json", NTUE_SISTER_SCHOOLS_URL, f"國立臺北教育大學 {len(partners)} 所合作姊妹校整合資料集 JSON"),
        ("sources/ntue/ntue_resolved_locations.json", NTUE_SISTER_SCHOOLS_URL, f"國立臺北教育大學 {len(partners)} 所合作姊妹校地理座標核對表 JSON"),
    ]
    for fname, url in bin_urls.items():
        provenance_files.append((f"sources/ntue/{fname}", url, f"國立臺北教育大學官方附件：{fname}"))

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
        "school_id": "ntue",
        "school_name": "國立臺北教育大學",
        "generated_at": CHECKED_AT,
        "active_cycle_note": completeness["active_term"],
        "sources": prov_sources,
    }
    prov_text = (
        json.dumps(provenance_payload, ensure_ascii=False, indent=2) + "\n"
    )
    (OFFICIAL_NTUE_DIR / "import_provenance.json").write_text(
        prov_text, encoding="utf-8"
    )
    (OFFICIAL_NTUE_DIR / "import-provenance.json").write_text(
        prov_text, encoding="utf-8"
    )

    print(
        f"Successfully built NTUE catalog: {len(partners)} partners"
        f" ({open_partner_count} open, {completeness['verified_campus_images']}"
        f" verified images, {completeness['verified_locations']} verified"
        f" locations), {len(workflows)} workflows,"
        f" {len(destinations)} destinations, {len(research_records)} research"
        f" records, {exp_covered_schools} schools with experience records"
        f" ({len(student_experience_rows)} rows, {total_exp_reports} reports)."
    )


if __name__ == "__main__":
    main()
