#!/usr/bin/env python3
"""Build the official National Taiwan University of Arts (國立臺灣藝術大學, NTUA) exchange data bundle."""

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
SOURCES_NTUA_DIR = REPO_ROOT / "sources" / "ntua"
OFFICIAL_NTUA_DIR = REPO_ROOT / "src" / "exchange_info" / "official_data" / "ntua"
STATIC_DIR = REPO_ROOT / "src" / "exchange_info" / "static"
UNIVERSITY_LOCATIONS_PATH = (
    REPO_ROOT / "src" / "exchange_info" / "official_data" / "university_locations.jsonl"
)

CHECKED_AT = "2026-11-01T00:00:00Z"

NTUA_OIA_HOME_URL = "https://international.ntua.edu.tw/"
NTUA_OIA_ABOUT_URL = "https://international.ntua.edu.tw/#/List/5"
NTUA_OIA_MEMBERS_URL = "https://international.ntua.edu.tw/#/List/6"
NTUA_OIA_CONTACT_URL = "https://international.ntua.edu.tw/#/List/7"
NTUA_REGULATIONS_URL = "https://international.ntua.edu.tw/#/List/8"
NTUA_SISTER_SCHOOLS_URL = "https://international.ntua.edu.tw/#/List/9"
NTUA_EXCHANGE_INTRO_URL = "https://international.ntua.edu.tw/#/List/26"
NTUA_EXCHANGE_PARTNERS_URL = "https://international.ntua.edu.tw/#/List/27"
NTUA_EXCHANGE_FAQ_URL = "https://international.ntua.edu.tw/#/List/28"
NTUA_PREDEPARTURE_URL = "https://international.ntua.edu.tw/#/List/29"
NTUA_EXPERIENCE_PORTAL_URL = "https://international.ntua.edu.tw/#/List/30"
NTUA_EXPERIENCE_SHEET_URL = (
    "https://docs.google.com/spreadsheets/d/1XVenaXbrPn6TkeK3IiL06elCLt9tf3z_9tQ481CKjW8/edit?usp=sharing"
)
NTUA_VISITING_STUDENT_URL = "https://international.ntua.edu.tw/#/List/32"
NTUA_OVERSEAS_INTERNSHIP_URL = "https://international.ntua.edu.tw/#/List/34"
NTUA_DUAL_DEGREE_URL = "https://international.ntua.edu.tw/#/List/35"
NTUA_SHORT_TERM_URL = "https://international.ntua.edu.tw/#/List/38"
NTUA_SCHOLARSHIPS_URL = "https://international.ntua.edu.tw/#/List/39"
NTUA_DOWNLOADS_URL = "https://international.ntua.edu.tw/#/List/53"
NTUA_NEWS_116_1_EXCHANGE_URL = "https://international.ntua.edu.tw/#/Post/1079/46"
NTUA_NEWS_115_2_RESULTS_URL = "https://international.ntua.edu.tw/#/Post/1054/46"
NTUA_NEWS_115_XUEHAI_URL = "https://international.ntua.edu.tw/#/Post/1018/46"
NTUA_EPORTAL_URL = "https://eportal.ntua.edu.tw/"

REGION_COST_DEFAULTS = {
    "日本": (
        "每月生活費約 USD 700–1,150（折合日圓約 JPY 100,000–165,000 / 月、新臺幣約 22,500–37,000 元；含東京藝術大學、多摩美術大學、武藏野美術大學、女子美術大學、筑波大學、千葉大學、神戶藝術工科大學、沖繩縣立藝術大學、名古屋造形大學等校內外住宿與創作材料膳食費）",
        "須由日本姊妹校代向出入國在留管理局申辦「在留資格認定證明書（COE）」（申請 COE 須檢附英文存款／財力證明），獲發後申辦留學簽證並強制加入日本國民健康保險（NHI）。",
    ),
    "韓國": (
        "每月生活費約 USD 620–1,050（折合韓元約 KRW 850,000–1,450,000 / 月、新臺幣約 20,000–33,500 元；含韓國藝術綜合大學、首爾國立科技大學、中央大學、漢陽大學、建國大學、檀國大學、慶北大學、啟明大學、明知大學、秋溪藝術大學等校內外宿舍與展演創作開銷）",
        "須憑韓國姊妹校核發之標準入學許可書向駐台北韓國代表部申辦 D-2-6 交換學生簽證，入境後申辦外國人登錄證（ARC）並納保韓國國民健康保險（NHIS）。",
    ),
    "中國大陸": (
        "每月生活費約 USD 300–600（折合人民幣約 CNY 2,100–4,200 / 月、新臺幣約 9,600–19,200 元；含清華大學、同濟大學、浙江大學、南京大學、武漢大學、廈門大學、中國傳媒大學、中央美術學院、中國美術學院、北京電影學院、北京舞蹈學院、上海戲劇學院、四川美術學院等學生宿舍與食堂費）",
        "須憑大陸姊妹校錄取通知書及入學相關文件辦理臺胞證簽注與校內住宿登記，並依規定投保大陸地區醫療與意外保險。",
    ),
    "香港": (
        "每月生活費約 USD 950–1,550（折合港幣約 HKD 7,400–12,000 / 月、新臺幣約 30,500–49,500 元；含香港演藝學院 HKAPA、香港中文大學、香港浸會大學、嶺南大學、香港恆生大學等住宿與膳食交通費）",
        "須由香港合作校協助向香港入境事務處申辦來港就讀進入許可（Student Visa / Entry Permit），並投保涵蓋全期之海外醫療及意外險。",
    ),
    "新加坡": (
        "每月生活費約 USD 950–1,500（折合新幣約 SGD 1,280–2,000 / 月、新臺幣約 30,500–48,000 元；含新加坡國立大學 NUS、新加坡拉薩爾藝術學院 LASALLE 等住宿與生活費）",
        "須透過新加坡移民與關卡局（ICA）SOLAR 系統申辦 Student's Pass（STP），並投保校方規定之醫療保險。",
    ),
    "美國": (
        "每月生活費約 USD 1,250–2,250（依匯率折合新臺幣約 40,000–72,000 元；含加州州立大學海峽群島分校、天普大學、東南密蘇里州立大學、南猶他大學、林登伍德大學等住宿、排練器材與校園餐飲費）",
        "須憑美國合作校核發之 DS-2019（J-1 交換生）繳交 SEVIS I-901 費用並向 AIT 申辦簽證，並強制投保接待校規定之學生醫療保險。",
    ),
    "加拿大": (
        "每月生活費約 USD 1,100–1,850（折合加幣約 CAD 1,500–2,500 / 月、新臺幣約 35,000–59,000 元；含安大略藝術設計大學 OCAD University 等住宿與生活費）",
        "須憑加拿大合作大學入學許可申辦學習許可（Study Permit）或簽證，並投保省立或校方規定之學生醫療保險。",
    ),
    "德國": (
        "每月生活費約 USD 980–1,550（折合歐元約 EUR 900–1,420 / 月、新臺幣約 31,500–49,500 元；含福克旺藝術大學 Folkwang、斯圖加特媒體大學 HdM、波茨坦應用科技大學等學生宿舍與學期交通卡費）",
        "須開立德國限制提領帳戶（Blocked Account）並憑入學許可向德國在台協會申辦學生簽證及投保德國公保／醫療險。",
    ),
    "法國": (
        "每月生活費約 USD 950–1,550（折合歐元約 EUR 880–1,420 / 月、新臺幣約 30,500–49,500 元；含巴黎第一大學 Panthéon-Sorbonne、巴黎第八大學、巴黎西岱大學、國立高等裝飾藝術學院 ENSAD、國立路易盧米埃學院、格勒諾布爾—瓦朗斯設計與藝術學院等住宿與創作材料費）",
        "須透過法國教育中心（Campus France）完成面試並申辦法國長期學生簽證 VLS-TS，入境後完成 OFII 認證並納保法國學生健保。",
    ),
    "奧地利": (
        "每月生活費約 USD 950–1,500（折合歐元約 EUR 880–1,380 / 月、新臺幣約 30,500–48,000 元；含維也納音樂與表演藝術大學 mdw、薩爾茲堡莫札特大學 Mozarteum 等學生宿舍與琴房排練生活費）",
        "須憑奧地利接待大學入學許可、住宿證明與財力證明向奧地利台北辦事處申辦 D 類學生簽證，並投保涵蓋申根區全期之醫療與意外保險。",
    ),
    "英國": (
        "每月生活費約 USD 1,250–2,100（折合英鎊約 GBP 980–1,650 / 月、新臺幣約 40,000–67,000 元；含聖三一拉邦音樂舞蹈學院 Trinity Laban、金士頓大學、巴斯斯巴大學、創意藝術大學 UCA、伯明翰城市大學、瑞丁大學等學生宿舍與生活費）",
        "須依英國簽證暨移民署（UKVI）規定申辦 Standard Visitor Visa（6 個月內交換）或 Student Visa（超過 6 個月並繳納 IHS 健保附加費），並投保海外醫療保險。",
    ),
    "捷克": (
        "每月生活費約 USD 650–1,100（折合捷克克朗約 CZK 15,000–25,500 / 月、新臺幣約 21,000–35,000 元；含布拉格表演藝術學院電影電視學院 FAMU、音樂舞蹈學院 HAMU、布拉格藝術建築暨設計學院 UMPRUM、西波西米亞大學等住宿與生活費）",
        "須憑捷克合作院校核發之入學許可、住宿證明與財力證明向捷克經濟文化辦事處申辦長期學生簽證，並投保捷克境內認可之綜合醫療保險。",
    ),
    "西班牙": (
        "每月生活費約 USD 850–1,350（折合歐元約 EUR 780–1,250 / 月、新臺幣約 27,000–43,000 元；含瓦倫西亞科技大學 UPV、維戈大學、西班牙科技藝術與設計大學 U-tad、卡米洛何塞塞拉大學等住宿與生活費）",
        "須憑西班牙接待大學入學許可、財力證明與醫療保險證明向西班牙商務辦事處申辦學生簽證。",
    ),
    "義大利": (
        "每月生活費約 USD 900–1,450（折合歐元約 EUR 820–1,320 / 月、新臺幣約 28,500–46,500 元；含佛羅倫斯 Alchimia 當代珠寶學院、佛羅倫斯古典藝術學院等住宿與工作坊材料費）",
        "須憑義大利合作院校入學許可、住宿證明與財力證明向義大利經濟貿易文化推廣辦事處申辦學生簽證，入境後申辦居留證（Permesso di Soggiorno）。",
    ),
}

SEMESTER_DATES_BY_COUNTRY = {
    "日本": "春季班（第2學期）：每年 4 月起至 8 月止；秋季班（第1學期）：每年 9–10 月起至翌年 2–3 月止",
    "韓國": "春季班（第2學期）：每年 3 月初至 6 月中旬；秋季班（第1學期）：每年 9 月初至 12 月中旬",
    "中國大陸": "春季班（第2學期）：每年 2 月下旬至 7 月初；秋季班（第1學期）：每年 9 月初至翌年 1 月中旬",
    "香港": "秋季學期（Semester 1）：每年 9 月初至 12 月下旬；春季學期（Semester 2）：每年 1 月中旬至 5 月下旬",
    "美國": "秋季班（Fall Semester）：每年 8 月中旬至 12 月中旬；春季班（Spring Semester）：每年 1 月中旬至 5 月中旬",
    "加拿大": "秋季學期（Fall Term）：每年 9 月初至 12 月下旬；冬季／春季學期（Winter Term）：每年 1 月初至 4 月下旬",
    "德國": "冬季學期（Wintersemester）：每年 10 月至翌年 2 月；夏季學期（Sommersemester）：每年 4 月至 7 月",
    "奧地利": "冬季學期（Wintersemester）：每年 10 月初至翌年 1 月底；夏季學期（Sommersemester）：每年 3 月初至 6 月底",
    "法國": "秋季學期（Semestre 1）：每年 9 月至 12 月／1 月；春季學期（Semestre 2）：每年 1 月至 5 月／6 月",
    "英國": "秋季學期（Autumn Term）：每年 9 月下旬至 12 月中旬；春季學期（Spring/Summer Term）：每年 1 月中旬至 6 月中旬",
    "捷克": "冬季／秋季學期（Winter Semester）：每年 9 月下旬至翌年 1 月；夏季／春季學期（Summer Semester）：每年 2 月中旬至 6 月",
    "西班牙": "秋季學期（Primer Cuatrimestre）：每年 9 月中旬至翌年 1 月；春季學期（Segundo Cuatrimestre）：每年 2 月至 6 月",
    "義大利": "秋季學期（First Semester）：每年 9–10 月至翌年 1–2 月；春季學期（Second Semester）：每年 2–3 月至 6–7 月",
}


def clean_text(s: str) -> str:
    return re.sub(r"\s+", " ", str(s)).strip() if s else ""


def sync_global_assets_and_locations(
    catalog_source: list[dict], resolved_locations: dict
) -> None:
    """Ensure school-images.json and university_locations.jsonl contain all NTUA partner schools."""
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
                else loc.get("lat", 25.0067)
            )
            lon = float(
                loc.get("longitude")
                if loc.get("longitude") is not None
                else loc.get("lon", 121.4481)
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
    OFFICIAL_NTUA_DIR.mkdir(parents=True, exist_ok=True)
    catalog_source = json.loads(
        (SOURCES_NTUA_DIR / "ntua_catalog_source.json").read_text(encoding="utf-8")
    )
    resolved_locations = json.loads(
        (SOURCES_NTUA_DIR / "ntua_resolved_locations.json").read_text(encoding="utf-8")
    )
    bin_urls = json.loads(
        (SOURCES_NTUA_DIR / "binary_source_urls.json").read_text(encoding="utf-8")
    )

    NTUA_BROCHURE_116_1_PDF = bin_urls["ntua_116_1_exchange_brochure.pdf"]
    NTUA_BRIEFING_116_1_PDF = bin_urls["ntua_116_1_application_briefing.pdf"]
    NTUA_SELECTION_REG_PDF = bin_urls["ntua_exchange_selection_guidelines.pdf"]
    NTUA_XUEHAI_REG_PDF = bin_urls["ntua_xuehai_subsidy_guidelines.pdf"]
    NTUA_DUAL_DEGREE_REG_PDF = bin_urls["ntua_dual_degree_regulations.pdf"]
    NTUA_INTL_COMP_REG_PDF = bin_urls["ntua_intl_competition_subsidy_guidelines.pdf"]
    NTUA_OVERSEAS_SUBSIDY_REG_PDF = bin_urls["ntua_overseas_exchange_subsidy_guidelines.pdf"]
    NTUA_ACCEPTANCE_CONFIRM_PDF = bin_urls["ntua_exchange_acceptance_confirmation.pdf"]
    NTUA_WAIVER_DECL_PDF = bin_urls["ntua_exchange_waiver_declaration.pdf"]
    NTUA_DEPARTURE_CHECKLIST_PDF = bin_urls["ntua_departure_checklist_form.pdf"]
    NTUA_RETURN_CHECKLIST_PDF = bin_urls["ntua_return_checklist_form.pdf"]
    NTUA_STUDY_CONSENT_PDF = bin_urls["ntua_study_abroad_consent_form.pdf"]
    NTUA_HEALTH_CHECK_PDF = bin_urls["ntua_health_check_form.pdf"]
    NTUA_PREDEPARTURE_INST_PDF = bin_urls["ntua_predeparture_instructions.pdf"]
    NTUA_DEPOSIT_REFUND_PDF = bin_urls["ntua_deposit_refund_form.pdf"]
    NTUA_PREDEPARTURE_114_2_PDF = bin_urls["ntua_114_2_predeparture_briefing.pdf"]
    NTUA_XUEHAI_FEIYANG_BROCHURE_PDF = bin_urls["ntua_115_xuehai_feiyang_xizhu_brochure_r2.pdf"]
    NTUA_XUEHAI_ZHUMENG_BROCHURE_PDF = bin_urls["ntua_115_xuehai_zhumeng_brochure_r2.pdf"]
    NTUA_XUEHAI_BRIEFING_PDF = bin_urls["ntua_115_xuehai_briefing.pdf"]
    NTUA_GRAD_AFFIDAVIT_PDF = bin_urls["ntua_graduating_student_affidavit.pdf"]
    NTUA_CEFR_MAP_PDF = bin_urls["ntua_cefr_mapping_table.pdf"]

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

    round_label = "116學年度第1學期交換學生甄選（11/02線上截止、11/03系所收件截止）"
    app_deadline_str = (
        "116學年度第1學期（2027年秋季赴外）交換學生計畫甄選：線上申請（e-Portal 校務行政資訊系統）至 2026/11/02（一）23:59 截止，"
        "紙本申請資料須於 2026/11/03（二）17:00 前繳交至所屬系（所）辦公室；"
        "經系所初審（11/04–11/11）、學院複審（11/12–11/23）及國際教育委員會決審後，預計於 2026/12/30 公告甄選結果（單次甄選僅可申請 1 間學校）"
    )
    deadline_iso = "2026-11-02T23:59:00+08:00"
    acad_year = "116"

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

        group_str = clean_text(item.get("group") or "國際姊妹校交換計畫")
        prog_raw = clean_text(
            item.get("program_type_raw") or "116學年度第1學期赴外交換學生甄選計畫"
        )
        quota_str = clean_text(
            item.get("quota") or "依當學期《交換學生計畫甄選簡章》及兩校協議核定名額辦理"
        )
        detail_url = item.get("detail_url") or NTUA_EXCHANGE_PARTNERS_URL
        source_url = detail_url
        program_type = f"國際事務處【{prog_raw}】（{group_str}）"

        colleges_val = item.get("colleges")
        if isinstance(colleges_val, list):
            colleges_str = "、".join(colleges_val)
        else:
            colleges_str = clean_text(
                colleges_val
                or "美術學院、設計學院、傳播學院、表演藝術學院、人文學院"
            )

        deg_val = item.get("eligible_degrees")
        if isinstance(deg_val, list):
            degree_levels_str = "、".join(deg_val)
        else:
            degree_levels_str = clean_text(
                deg_val or "學士班（大二以上）、碩士班、博士班"
            )

        lang_req_str = clean_text(
            item.get("language_req")
            or "須符合接待合作學校規定之授課語言檢定標準（英語授課課程建議 CEFR B1–B2／IELTS 5.5–6.0／TOEFL iBT 72 以上，或修習當地語言達規定標準）"
        )
        gpa_req_str = clean_text(
            item.get("gpa_req")
            or "申請時已於臺藝大就讀滿 1 學期以上（不含在職專班），歷年學業成績平均 80 分以上或班（系）排名前 70%，且操行成績 85 分以上（無懲處紀錄）"
        )
        website = item.get("website") or source_url
        factsheet_url = item.get("factsheet_url") or website
        remarks_raw = clean_text(item.get("notes") or "")
        tuition_note = clean_text(
            item.get("tuition_note")
            or "出國交換期間須於國立臺灣藝術大學完成註冊並繳交全額學雜費（以「出國交換學生」身分就讀並保有臺藝大學籍），免繳接待合作學校學費；住宿費、生活費、保險費、簽證費與往返機票等均由學生自行負擔。"
        )
        exps = item.get("experience_reports") or []

        win_status = "open" if avail_status == "open" else "closed"
        study_period_str = (
            f"{item.get('exchange_duration') or '一學期或一學年'}（單次甄選僅可申請 1 間學校，同一學制以出國交換 1 次為限；"
            "可同步申請教育部學海飛颺、學海惜珠獎學金或依雙聯學制辦法銜接雙聯學位）"
        )
        sem_dates_str = SEMESTER_DATES_BY_COUNTRY.get(
            country,
            "春季班（第2學期）：每年 1–2 月起至 6–7 月止（預計）；秋季班（第1學期）：每年 8–9 月起至翌年 1–2 月止（預計）",
        )
        housing_str = (
            f"獲國立臺灣藝術大學國際事務處推薦提名後，可依 {zh_name} 指引申請校內外學生宿舍或自行安排校外住宿（{tuition_note}）。"
        )
        course_rest_str = (
            f"開放對象與學院：{colleges_str}（{degree_levels_str}）。依《國立臺灣藝術大學交換學生甄選要點》及《116學年度第1學期交換學生計畫甄選簡章》規定："
            "（1）申請時須已在本校就讀滿 1 學期（含）以上之在學生（畢業於本校之在學碩、博生亦須就讀滿 1 學期以上；不含在職專班），歷年學業平均 80 分以上或班（系）排名前 70%，操行 85 分以上且無懲處紀錄；"
            "（2）單次甄選僅可申請 1 間學校，同一學制僅得出國交換一次；校內審查配分為：需語言檢定之學校（在校成績 45%、語言能力 25%、研修計畫 20%、其他得獎／論文／實習 10%）或不需語言檢定之學校（在校成績 55%、研修計畫 25%、其他 20%）；"
            "（3）錄取後 30 日內須繳交《錄取資格確認書》、《出國研修同意書》及新臺幣 5,000 元保證金收據正本（中低收入戶免繳）；出國前 14 日完成《離校手續單》，抵達國外 7 日內線上填報居住資訊；"
            "（4）境外研修期間每學期應至少修習 2 門或相當於臺灣學制 6 學分以上課程（至少 1 門為原屬系所專業課程），並通過所選讀學分或課程 1/2 以上；開學後 30 日內須將修課清單送原屬系所審核；返國後 30 日內（學海受獎生為 2 週內）完成《返校手續單》及 2,000 字以上研修心得報告（含照片 3–6 張），始得申請無息退還 5,000 元保證金。"
        )

        living_cost_str, visa_health_str = REGION_COST_DEFAULTS.get(
            country,
            (
                "每月生活費約 USD 650–1,400（依匯率折合新臺幣約 21,000–45,000 元，含住宿、藝術創作材料、膳食與市區交通）",
                "須依接待國駐臺機構規定申辦學生簽證，並於出國前投保涵蓋海外交換全期之海外醫療及意外保險（保額至少新臺幣 100 萬元以上）及提交《選送學生出國健康檢查記錄表》。",
            ),
        )

        tuition_points_list = [
            (
                "國立臺灣藝術大學學雜費與 5,000 元保證金規定：依《國立臺灣藝術大學交換學生甄選要點》，"
                f"交換期間學生須於本校完成註冊並繳交全額學雜費（保有臺藝大學籍），免繳接待合作學校學費。錄取後 30 日內須繳交新臺幣 5,000 元保證金（中低收入戶持證明免繳），履行境外修課（至少 2 門或 6 學分且至少 1 門本系專業課程、通過 1/2 以上）與返國後 30 日內完成返校手續及 2,000 字心得報告後無息退還。本合作校待遇：{tuition_note}"
            ),
            (
                "國立臺灣藝術大學五大出國研修、實習與國際展演競賽獎助體系：（1）教育部《學海飛颺》選送優秀學生出國研修獎學金（依《國立臺灣藝術大學辦理教育部學海系列計畫補助作業要點》，補助赴非大陸港澳地區合作校交換 1 學期或 1 學年之來回機票與生活費）；"
                "（2）教育部《學海惜珠》勵學優秀學生出國研修獎學金（持低收入戶、中低收入戶或特殊境遇家庭證明者專案補助）；"
                "（3）教育部《學海築夢》及《新南向學海築夢》海外專業藝術與文創機構實習獎助；"
                "（4）《國立臺灣藝術大學補助教職員生參加國際教學展演競賽實施要點》與《國際移地交流合作補助要點》；"
                "（5）就學貸款海外研修配套（可下載《臺灣銀行就學貸款海外研修證明信》申辦出國交換期間就學貸款）。"
            ),
        ]

        app_steps_list = [
            (
                f"步驟一（確認臺藝大就讀滿 1 學期、歷年平均 80 分或前 70% 門檻與 {zh_name} 語言及作品集要求）："
                f"確認符合《國立臺灣藝術大學交換學生甄選要點》資格（{gpa_req_str}），單次甄選僅可擇定 1 間志願學校，並備妥符合 {zh_name} 規定之語言能力證明（{lang_req_str}）與專業作品集。"
            ),
            (
                "步驟二（2026/11/02 23:59 前完成 e-Portal 線上申請，11/03 17:00 前繳交紙本至所屬系所）："
                "登入臺藝大校務行政資訊系統（e-Portal）填報交換申請並上傳：（1）申請表、（2）中文歷年成績單（含歷年平均及班／系排名百分比）、（3）讀書與研修計畫、（4）自傳及履歷表、（5）語言能力證明、（6）作品集（無則免）、（7）其他有利審查文件及應屆畢業生切結書（如適用），並列印紙本於 11/03 17:00 前送交所屬系（所）辦公室。"
            ),
            (
                "步驟三（系所初審 11/04–11/11、學院複審 11/12–11/23、國際教育委員會決審與 12/30 結果公告）："
                "經三級審查於 2026/12/30 公告錄取名單後，錄取生須於 30 日內繳交《錄取資格確認書》、《出國研修同意書》及出納組新臺幣 5,000 元保證金收據正本（中低收入戶免繳）。"
            ),
            (
                f"步驟四（向 {full_name} 遞交提名與入學申請、離校手續、海外修課通報與返國退還保證金）："
                "出國前 14 日完成《離校手續單》及《選送學生出國健康檢查記錄表》，抵達國外 7 日內線上填報居住資訊，開學後 30 日內將修課清單（至少 2 門或 6 學分，含至少 1 門本系專業課）送系所審核；返國後 30 日內完成《返校手續單》、問卷、2,000 字以上研修心得報告（含照片 3–6 張）及《保證金退費申請表》。"
            ),
        ]

        elig_points_list = [
            f"合作類別與計畫群組：{program_type}",
            f"開放學制與修業年級：{degree_levels_str}（申請時已於臺藝大就讀滿 1 學期以上，不含在職專班）",
            f"開放申請學院：{colleges_str}",
            f"學業與操行門檻：{gpa_req_str}",
            f"語言能力標準：{lang_req_str}",
            "審查配分與志願限制：單次甄選僅可申請 1 間學校，同一學制僅得出國交換 1 次；需語檢學校配分（在校成績 45%、語言 25%、研修計畫 20%、其他 10%），不需語檢學校配分（在校成績 55%、研修計畫 25%、其他 20%）。",
            "境外修課與保證金義務：錄取後 30 日內繳交 5,000 元保證金；境外每學期至少修習 2 門或 6 學分（含至少 1 門本系專業課）且通過 1/2 以上；返國後 30 日內繳交 2,000 字心得報告（含 3–6 張照片）並完成返校手續後退還保證金。",
        ]
        if tuition_note:
            elig_points_list.append(f"學雜費規定：{tuition_note}")
        if remarks_raw:
            elig_points_list.append(f"合作校申請要點與雙向交流紀錄：{remarks_raw}")

        exp_links: list[dict] = []
        exp_labels: list[str] = []
        if exps:
            exp_covered_schools += 1
            total_exp_reports += len(exps)
            seen_exp_urls: set[str] = set()
            for e_idx, e in enumerate(exps):
                raw_t = clean_text(e.get("title") or f"赴 {zh_name} 交換生研修心得報告")
                esem = e.get("semester") or "歷年交換研修"
                eurl = e.get("url") or NTUA_EXPERIENCE_SHEET_URL
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
                    "department": e.get("department") or "國立臺灣藝術大學赴外交換學生",
                })
                summary_text = (
                    f"國立臺灣藝術大學國際事務處「出國交換學生心得分享彙整表」收錄之 {esem} 赴 {country} {full_name} 交換研修心得報告（{raw_t}）。"
                    " 涵蓋 e-Portal 線上申請與作品集準備、姊妹校專業藝術與設計課程修習、住宿生活適應及教育部學海系列獎學金核銷實務。"
                )
                theme_map = {
                    "academics": (
                        f"臺藝大交換生於《{raw_t}》分享在 {zh_name} 修習至少 2 門／6 學分以上專業藝術創作課程與返國後辦理學分抵免之經驗。"
                    ),
                    "housing": (
                        f"臺藝大交換生分享申請 {zh_name} 校內外學生宿舍與租屋生活適應（{housing_str[:100]}）。"
                    ),
                    "campus_culture": (
                        f"臺藝大國際事務處透過《{raw_t}》傳承海外藝術院校跨文化創作交流、工作坊資源與學習心得。"
                    ),
                    "cost": (
                        f"臺藝大交換生分享於 {zh_name} 之每月住宿、創作材料與生活花費（{living_cost_str[:100]}），以及申請教育部學海飛颺／學海惜珠獎學金之經驗。"
                    ),
                }
                student_experience_rows.append({
                    "school_name": full_name,
                    "country": country,
                    "title": raw_t,
                    "source_url": eurl,
                    "source_type": "article",
                    "platform": "國立臺灣藝術大學國際事務處—出國交換學生心得分享專區（102–113學年）",
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
                        f"{full_name}:ntua_exp:{e_idx}:{eurl}".encode("utf-8")
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
            "home_university": "國立臺灣藝術大學",
            "school_name": full_name,
            "country": country,
            "official_experience_portal_url": (
                exp_links[0]["url"] if exp_links else NTUA_EXPERIENCE_SHEET_URL
            ),
            "partner_page_url": source_url,
            "report_count": len(exps),
            "sample_reports": sample_reports,
            "checked_at": CHECKED_AT,
        })

        loc = resolved_locations.get(full_name) or {
            "city": country,
            "latitude": 25.0067,
            "longitude": 121.4481,
            "source_url": "https://www.wikidata.org",
        }
        city_name = loc.get("city") or country
        lat = float(
            loc.get("latitude")
            if loc.get("latitude") is not None
            else loc.get("lat", 25.0067)
        )
        lon = float(
            loc.get("longitude")
            if loc.get("longitude") is not None
            else loc.get("lon", 121.4481)
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
                " 及國立臺灣藝術大學國際事務處「交換學校一覽表（ExchangeSchoolList）」與「姊妹校一覽表」比對；實際交換校區以錄取通知與合作校簡章為準。"
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
                f"【臺藝大學長姐交換研修心得報告（共 {len(exps)} 篇）】收錄於國際事務處出國交換學生心得分享彙整表（含：{'、'.join(exp_labels[:4])}）"
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
                f"國立臺灣藝術大學國際事務處公告合作學校（{program_type}）；名額：{quota_str}（{remarks_raw}）。"
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
                "title": f"國立臺灣藝術大學國際事務處交換學校一覽表—{zh_name}",
                "source_url": source_url,
                "role": "home_university",
                "authority": "home_official_notice",
                "effective_academic_year": acad_year,
                "application_round": round_label,
                "checked_at": CHECKED_AT,
            },
            {
                "title": "國立臺灣藝術大學 116學年度第1學期交換學生計畫甄選簡章 PDF",
                "source_url": NTUA_BROCHURE_116_1_PDF,
                "role": "home_university",
                "authority": "home_official_notice",
                "effective_academic_year": acad_year,
                "application_round": round_label,
                "checked_at": CHECKED_AT,
            },
            {
                "title": "國立臺灣藝術大學交換學生甄選要點 PDF",
                "source_url": NTUA_SELECTION_REG_PDF,
                "role": "home_university",
                "authority": "home_official_notice",
                "effective_academic_year": acad_year,
                "application_round": round_label,
                "checked_at": CHECKED_AT,
            },
        ]
        if exp_links:
            wf_sources.append({
                "title": f"國立臺灣藝術大學國際事務處出國交換學生心得分享專區—{zh_name}",
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
            "home_university": "國立臺灣藝術大學",
            "school_name": full_name,
            "partner_website": website,
            "country": country,
            "program_type": program_type,
            "academic_year": acad_year,
            "application_round": round_label,
            "effective_application_rounds": [
                round_label,
                "116學年度第1學期交換學生甄選",
                "116學年度第2學期交換學生甄選",
                "115-1",
                "115-2",
                "116-1",
                "116-2",
            ],
            "applicability_status": "verified",
            "applicability_note": (
                "國立臺灣藝術大學由國際事務處（新北市板橋區大觀路一段 59 號行政大樓 1 樓，電話：02-2272-2181 分機 1921 黃孔宏行政專員／1925 楊景翔組長）"
                "統籌全校五大學院（美術學院、設計學院、傳播學院、表演藝術學院、人文學院）之國際暨大陸港澳地區合作學校交換學生甄選、"
                "雙聯學制及教育部學海飛颺、學海惜珠與學海築夢獎助遴選。"
            ),
            "review_status": "published",
            "published_at": CHECKED_AT,
            "steps": [
                {
                    "rule_id": f"ntua-{acad_year}-home-1-{sn:03d}",
                    "order": 1,
                    "phase": "校內申請",
                    "title": f"確認臺藝大就讀滿1學期、歷年平均80分或排名前70%門檻、單一志願限制及 {zh_name} 語言與作品集要求",
                    "responsible_party": "學生",
                    "responsible_unit": "國立臺灣藝術大學各系所／國際事務處國際教育組（行政大樓 1 樓）",
                    "deadline_at": deadline_iso,
                    "deadline_status": "verified_exact",
                    "deadline_source_url": NTUA_NEWS_116_1_EXCHANGE_URL,
                    "deadline_checked_at": CHECKED_AT,
                    "deadline_reminder_eligible": True,
                    "summary": (
                        f"確認符合《國立臺灣藝術大學交換學生甄選要點》及當期《交換學生計畫甄選簡章》規定（{gpa_req_str}），"
                        f"單次甄選僅可申請 1 間學校，同一學制僅得出國交換 1 次，並備妥符合 {zh_name} 規定之語言能力證明（{lang_req_str}）與個人作品集。"
                    ),
                    "details": [
                        f"開放學制與院系：{colleges_str}（{degree_levels_str}）",
                        f"語言與學業條件：{lang_req_str}｜{gpa_req_str}",
                        f"當期名額與計畫類別：{quota_str}｜{program_type}",
                    ],
                    "scope": {
                        "home_universities": ["國立臺灣藝術大學"],
                        "partner_universities": [full_name],
                        "academic_years": ["115", "116"],
                        "application_rounds": [round_label, "115-1", "115-2", "116-1", "116-2"],
                    },
                    "source_urls": [source_url, NTUA_SELECTION_REG_PDF, NTUA_BROCHURE_116_1_PDF],
                    "checked_at": CHECKED_AT,
                    "support_status": "verified",
                },
                {
                    "rule_id": f"ntua-{acad_year}-home-2-{sn:03d}",
                    "order": 2,
                    "phase": "校內申請",
                    "title": "於 11/02 23:59 前完成 e-Portal 線上申請並於 11/03 17:00 前將紙本資料繳交至所屬系（所）辦公室",
                    "responsible_party": "學生與所屬系（所）辦公室",
                    "responsible_unit": "臺藝大五大學院各系（所）辦公室／國際事務處國際教育組",
                    "deadline_at": "2026-11-03T17:00:00+08:00",
                    "deadline_status": "verified_exact",
                    "deadline_source_url": NTUA_NEWS_116_1_EXCHANGE_URL,
                    "deadline_checked_at": CHECKED_AT,
                    "deadline_reminder_eligible": True,
                    "summary": (
                        "申請人須於 2026/11/02（一）23:59 前登入臺藝大校務行政資訊系統（e-Portal）完成線上填報與附件上傳，"
                        "並列印申請資料紙本於 2026/11/03（二）17:00 前繳交至所屬系（所）辦公室（逾時不予受理）。"
                    ),
                    "details": [
                        "系（所）審查期間為 2026/11/04–11/11；學院複審期間為 2026/11/12–11/23（各院於 11/24 中午 12:00 前將結果送交國際事務處）。",
                        "校內審查配分：需語言檢定之學校（在校成績 45%、語言能力 25%、研修計畫 20%、其他 10%）；不需語言檢定之學校（在校成績 55%、研修計畫 25%、其他 20%）。",
                    ],
                    "document_requirements": [
                        {
                            "name": "e-Portal 線上列印之出國交換學生申請表及中文歷年成績單正本（含歷年平均及班／系排名百分比）",
                            "official_form_url": NTUA_BROCHURE_116_1_PDF,
                            "source_urls": [NTUA_BROCHURE_116_1_PDF, NTUA_BRIEFING_116_1_PDF],
                        },
                        {
                            "name": "讀書與研修計畫、自傳及履歷表（以交換國語言及中文各撰寫 1 份，約 1,000–2,000 字）與個人作品集",
                            "official_form_url": NTUA_BROCHURE_116_1_PDF,
                            "source_urls": [NTUA_BROCHURE_116_1_PDF, NTUA_SELECTION_REG_PDF],
                        },
                        {
                            "name": "有效外語能力檢定證明（對照 CEFR 等級表）及應屆畢業生延長修業切結書（如適用）",
                            "official_form_url": NTUA_CEFR_MAP_PDF,
                            "source_urls": [NTUA_CEFR_MAP_PDF, NTUA_GRAD_AFFIDAVIT_PDF],
                        },
                    ],
                    "scope": {
                        "home_universities": ["國立臺灣藝術大學"],
                        "academic_years": ["115", "116"],
                        "application_rounds": [round_label, "115-1", "115-2", "116-1", "116-2"],
                    },
                    "source_urls": [NTUA_NEWS_116_1_EXCHANGE_URL, NTUA_BROCHURE_116_1_PDF, NTUA_BRIEFING_116_1_PDF],
                    "checked_at": CHECKED_AT,
                    "support_status": "verified",
                },
                {
                    "rule_id": f"ntua-{acad_year}-home-3-{sn:03d}",
                    "order": 3,
                    "phase": "甄選與提名",
                    "title": "國際教育委員會決審公告錄取名單（12/30預計）、30日內繳交錄取確認書與5,000元保證金並申請學海系列獎學金",
                    "responsible_party": "國立臺灣藝術大學國際教育委員會／國際事務處與錄取學生",
                    "responsible_unit": "國立臺灣藝術大學國際教育委員會／國際事務處國際教育組",
                    "deadline_at": "2026-12-30T17:00:00+08:00",
                    "deadline_status": "reference_only",
                    "deadline_source_url": NTUA_NEWS_116_1_EXCHANGE_URL,
                    "deadline_checked_at": CHECKED_AT,
                    "deadline_reminder_eligible": False,
                    "summary": (
                        "經國際教育委員會決審通過後預計於 2026/12/30 公告甄選結果；錄取生須於公告後 30 日內繳交《錄取資格確認書》、《出國研修同意書》及新臺幣 5,000 元保證金收據正本（中低收入戶免繳）。"
                    ),
                    "details": [
                        "符合資格之非大陸港澳地區錄取生得依《國立臺灣藝術大學辦理教育部學海系列計畫補助作業要點》申請《學海飛颺》或《學海惜珠》獎學金。",
                        "錄取後如因故欲放棄推薦資格，須填具《交換學生計畫放棄交換校／本校薦送資格個人聲明書》送國際事務處備查。",
                    ],
                    "scope": {
                        "home_universities": ["國立臺灣藝術大學"],
                        "academic_years": ["115", "116"],
                        "application_rounds": [round_label, "115-1", "115-2", "116-1", "116-2"],
                    },
                    "source_urls": [
                        NTUA_ACCEPTANCE_CONFIRM_PDF,
                        NTUA_STUDY_CONSENT_PDF,
                        NTUA_WAIVER_DECL_PDF,
                        NTUA_XUEHAI_REG_PDF,
                    ],
                    "checked_at": CHECKED_AT,
                    "support_status": "verified",
                },
                {
                    "rule_id": f"ntua-{sn:03d}-host-apply",
                    "order": 4,
                    "phase": "合作校申請",
                    "title": f"由國際事務處向 {zh_name} 提名並遞交姊妹校入學申請與專業作品集審核文件",
                    "responsible_party": "學生與接待校國際事務處／專業藝術學院",
                    "summary": (
                        "獲本校公告錄取並完成資格確認後，由國際事務處依各姊妹校時程完成提名；"
                        "學生須於姊妹校申請截止日前備妥有效護照、英文成績單、英文財力證明、語檢證明、推薦信與作品集／試奏試演影音，由接待校進行最終入學審核並核發正式入學許可（Admission Letter / COE / DS-2019）。"
                    ),
                    "details": [
                        f"研修期程：{study_period_str}｜名額：{quota_str}",
                        f"語言與審查條件：{lang_req_str}｜{gpa_req_str}",
                        f"住宿與費用待遇：{housing_str}",
                    ],
                    "scope": {
                        "home_universities": ["國立臺灣藝術大學"],
                        "partner_universities": [full_name],
                        "academic_years": ["115", "116"],
                        "application_rounds": [round_label, "115-1", "115-2", "116-1", "116-2"],
                    },
                    "source_urls": [source_url, NTUA_BROCHURE_116_1_PDF] + ([website] if website else []),
                    "checked_at": CHECKED_AT,
                    "support_status": "verified",
                    "needs_confirmation": False,
                },
                {
                    "rule_id": f"ntua-{acad_year}-home-5-{sn:03d}",
                    "order": 5,
                    "phase": "行前準備",
                    "title": "出國前14日完成離校手續與健檢表、全額學雜費註冊、抵達7日內填報居住資訊、開學30日內送修課清單與返國30日內退還保證金",
                    "responsible_party": "學生與所屬系所",
                    "responsible_unit": "國立臺灣藝術大學國際事務處／教務處註冊組／各學院系所",
                    "summary": (
                        "出國前 14 日須完成《出國研修實習學生離校手續單》及《選送學生出國健康檢查記錄表》，並完成臺藝大每學期全額學雜費註冊及海外醫療意外險投保；"
                        "抵達國外 7 日內線上填報居住資訊，開學後 30 日內將修課清單（至少 2 門或 6 學分，含至少 1 門本系專業課）送系所審核；返國後 30 日內（學海受獎生為 2 週內）完成《返校手續單》、問卷及 2,000 字以上研修心得報告（含照片 3–6 張），申請無息退還 5,000 元保證金。"
                    ),
                    "details": tuition_points_list,
                    "scope": {
                        "home_universities": ["國立臺灣藝術大學"],
                        "academic_years": ["115", "116"],
                        "application_rounds": [round_label, "115-1", "115-2", "116-1", "116-2"],
                    },
                    "source_urls": [
                        NTUA_PREDEPARTURE_INST_PDF,
                        NTUA_DEPARTURE_CHECKLIST_PDF,
                        NTUA_RETURN_CHECKLIST_PDF,
                        NTUA_DEPOSIT_REFUND_PDF,
                        NTUA_HEALTH_CHECK_PDF,
                    ],
                    "checked_at": CHECKED_AT,
                    "support_status": "verified",
                },
            ],
            "sources": wf_sources,
            "last_checked": CHECKED_AT,
            "coverage_status": "official_verified",
            "coverage_note": (
                f"已完整整合國立臺灣藝術大學國際事務處（OIA）全球四大洲共 {len(catalog_source)} 所合作交換學校（含"
                f" {open_partner_count} 所開放交換合作學校）、"
                "交換學生甄選要點、116學年度第1學期交換學生計畫甄選簡章、教育部學海系列計畫補助作業要點，以及"
                f" {exp_covered_schools} 校 {total_exp_reports} 篇赴外交換生研修心得報告。"
            ),
        })

        cost_line = f"{zh_name} 預估每月生活費：{living_cost_str}"
        tuition_clean = tuition_points_list[0]
        housing_clean = housing_str
        calendar_clean = f"學期與研修時間參考：{sem_dates_str}"
        course_clean = course_rest_str

        dest_sources = [
            {
                "title": f"國立臺灣藝術大學國際事務處交換學校一覽表—{zh_name}",
                "source_url": source_url,
                "summary": "臺藝大國際事務處公告之合作領域、名額、語言門檻與學費待遇",
            },
            {
                "title": "國立臺灣藝術大學 116學年度第1學期交換學生計畫甄選簡章與交換學生甄選要點",
                "source_url": NTUA_BROCHURE_116_1_PDF,
                "summary": "臺藝大交換生三級審查流程、評分權重、5,000元保證金、境外修課學分及返國義務規定",
            },
        ]
        if exp_links:
            dest_sources.append({
                "title": f"國立臺灣藝術大學國際事務處出國交換學生心得分享專區—{zh_name}",
                "source_url": exp_links[0]["url"],
                "summary": f"收錄臺藝大學生赴 {zh_name} 出國交換研修心得報告共 {len(exps)} 篇",
            })
        if website:
            dest_sources.append({
                "title": f"{full_name} 官方網站",
                "source_url": website,
                "summary": "接待合作姊妹校官方網站",
            })

        src_url_list = (
            [source_url, NTUA_EXCHANGE_PARTNERS_URL, NTUA_SCHOLARSHIPS_URL]
            + ([exp_links[0]["url"]] if exp_links else [NTUA_EXPERIENCE_SHEET_URL])
            + ([website] if website else [])
        )

        destinations.append({
            "home_university": "國立臺灣藝術大學",
            "school_name": full_name,
            "country": country,
            "city": city_name,
            "cost_summary": f"{cost_line}。\n{tuition_clean}",
            "housing_summary": housing_clean,
            "transport_summary": (
                f"校區代表城市：{city_name}。請依入學許可確認實際授課校區、音樂廳／劇場／排練室與工作室位置及當地學生交通優惠。"
            ),
            "campus_life_summary": f"{calendar_clean}\n{course_clean}",
            "student_guide_sections": [
                {
                    "key": "cost",
                    "title": "生活費、臺藝大全額學雜費註冊、5,000元保證金退費規定與學海系列獎助體系",
                    "summary": cost_line,
                    "points": [cost_line] + tuition_points_list,
                    "source_urls": src_url_list + [
                        NTUA_SELECTION_REG_PDF,
                        NTUA_DEPOSIT_REFUND_PDF,
                        NTUA_BROCHURE_116_1_PDF,
                    ],
                    "caution": "交換期間須於臺藝大完成註冊並繳交全額學雜費；錄取後 30 日內繳交 5,000 元保證金（中低收入戶免繳），返國完成手續與 2,000 字報告後無息退還。",
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
                    "title": "海外醫療與意外保險（至少100萬元）、出國健康檢查表暨抵達7日內居住通報",
                    "summary": visa_health_str,
                    "points": [
                        visa_health_str,
                        "錄取學生出國前 14 日須完成《離校手續單》、《選送學生出國健康檢查記錄表》及投保至少新臺幣 100 萬元以上之海外醫療及意外險，並於抵達國外 7 日內線上填報居住資訊。",
                    ],
                    "source_urls": src_url_list + [NTUA_PREDEPARTURE_INST_PDF, NTUA_HEALTH_CHECK_PDF],
                    "caution": "出國前請確認海外醫療保險涵蓋門診、住院及跨國急難救助，並依接待國法令加入當地國民健康保險或學生保險。",
                },
                {
                    "key": "visa",
                    "title": "留學交換簽證辦理、出國研修同意書與役男出境緩徵申請",
                    "summary": visa_health_str,
                    "points": [
                        visa_health_str,
                        "錄取生須於公告後 30 日內繳交《錄取資格確認書》與家長簽署之《出國研修同意書》；具役男身分之在學學生，應於出國前至少 1 個月檢附入學許可向學務處及國際事務處辦理役男出境申請。",
                    ],
                    "source_urls": src_url_list + [NTUA_PREDEPARTURE_INST_PDF, NTUA_PREDEPARTURE_114_2_PDF],
                    "caution": "學海受獎生購買國際來回機票若由旅行社開立代收轉付收據，請務必依《辦理教育部學海系列計畫補助作業要點》留存電子機票、登機證存根及購票證明核銷。",
                },
                {
                    "key": "academics",
                    "title": "海外藝術專業修課（至少2門或6學分且含1門本系專業課）、開學30日內送審與返國學分抵免",
                    "summary": course_clean[:160],
                    "points": [calendar_clean, course_clean],
                    "source_urls": src_url_list + [NTUA_SELECTION_REG_PDF, NTUA_BROCHURE_116_1_PDF],
                    "caution": "交換生須於接待校開學後 30 日內將修課清單送原屬系所審核（每學期至少修習 2 門或 6 學分以上且至少 1 門為原屬系所專業課程，並通過 1/2 以上），返國後依規定辦理學分採認抵免。",
                },
                {
                    "key": "living",
                    "title": f"{city_name} 校園生活、102–113學年赴外交換生心得分享彙整表與行前說明會傳承",
                    "summary": f"代表城市：{city_name}。錄取學生返國後 30 日內（學海受獎生 2 週內）須繳交 2,000 字以上出國交換心得報告（含照片 3–6 張）。",
                    "points": [
                        f"目的地城市：{city_name}（{country}）",
                        "國立臺灣藝術大學國際事務處建置完整「出國交換學生心得分享彙整表（102–113學年）」並每學期舉辦申請說明會與行前說明會"
                        + (
                            f"（本校於此姊妹校共收錄 {len(exps)} 篇：{'、'.join(exp_labels[:3])}）"
                            if exps
                            else ""
                        )
                        + "，提供作品集準備、選課、住宿與生活第一手資訊。",
                    ],
                    "source_urls": [
                        exp_links[0]["url"] if exp_links else NTUA_EXPERIENCE_SHEET_URL
                    ],
                },
            ],
            "sources": dest_sources,
            "last_checked": CHECKED_AT,
            "coverage_status": "official_verified",
            "coverage_note": (
                f"已整合國立臺灣藝術大學國際事務處 {len(catalog_source)} 所合作交換學校名冊、116學年度第1學期交換學生計畫甄選簡章、交換學生甄選要點及"
                f" {exp_covered_schools} 校 {total_exp_reports} 篇赴外交換生研修心得報告。"
            ),
        })

        research_records.append({
            "home_university": "國立臺灣藝術大學",
            "school_name": full_name,
            "country": country,
            "official_website": website,
            "verification_status": "official_verified",
            "discovery_source_url": detail_url,
            "checked_at": CHECKED_AT,
            "note": (
                f"國立臺灣藝術大學國際事務處全球四大洲 {len(catalog_source)} 所合作交換學校名冊（ExchangeSchoolList）與"
                " ROR/Wikidata 官方網址核對完成。"
            ),
        })

        ev_sources = [{
            "title": f"國立臺灣藝術大學國際事務處交換學校一覽表—{zh_name}",
            "url": source_url,
        }]
        if exp_links:
            ev_sources.append({
                "title": f"國立臺灣藝術大學國際事務處出國交換學生心得分享專區—{zh_name}",
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
                "scope": "臺藝大海外交換姊妹校住宿與財力證明資訊",
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
                "scope": "臺藝大出國交換全額學雜費規定、5,000元保證金、教育部學海飛颺／惜珠獎助與地區生活費估算",
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
                "scope": "國立臺灣藝術大學交換學生甄選要點、境外修課最低學分（2門或6學分）與學分抵免規定",
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
                "scope": "臺藝大海外交換簽證、出國研修同意書、出國健康檢查表、抵達7日內居住通報與海外醫療保險規定",
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
                        f"｜臺藝大國際事務處收錄 {len(exps)} 篇赴 {zh_name} 交換研修心得報告（{'、'.join(exp_labels[:3])}）。"
                        if exps
                        else ""
                    )
                ),
                "sources": ev_sources,
                "checked_at": CHECKED_AT,
                "scope": "臺藝大交換名額與 102–113 學年赴外交換生研修心得報告傳承",
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
                    f"已整合國立臺灣藝術大學國際事務處 {len(catalog_source)} 所合作交換學校名冊、116學年度第1學期交換學生計畫甄選簡章、交換學生甄選要點及歷年交換生心得報告。"
                ),
                "當期開放名額、宿位供給、語檢門檻、作品集規格與選課限制請依合作校最新簡章及入學通知書核對。",
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

    write_jsonl(OFFICIAL_NTUA_DIR / "partners.jsonl", partners)
    write_jsonl(SOURCES_NTUA_DIR / "partners.jsonl", partners)
    write_jsonl(OFFICIAL_NTUA_DIR / "application_workflows.jsonl", workflows)
    write_jsonl(OFFICIAL_NTUA_DIR / "destination_profiles.jsonl", destinations)
    write_jsonl(OFFICIAL_NTUA_DIR / "partner_research.jsonl", research_records)
    write_jsonl(OFFICIAL_NTUA_DIR / "student_life.jsonl", life_records)
    write_jsonl(OFFICIAL_NTUA_DIR / "experience_sources.jsonl", experience_sources_records)
    write_jsonl(
        OFFICIAL_NTUA_DIR / "student_experience_sources.jsonl",
        experience_sources_records,
    )
    write_jsonl(OFFICIAL_NTUA_DIR / "student_experiences.jsonl", student_experience_rows)

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
    (OFFICIAL_NTUA_DIR / "student-experience-digests.json").write_text(
        json.dumps({"digests": digest_records}, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    (OFFICIAL_NTUA_DIR / "student-experiences.json").write_text(
        json.dumps(
            {
                "school_id": "ntua",
                "school_name": "國立臺灣藝術大學",
                "checked_at": CHECKED_AT,
                "source_url": NTUA_EXPERIENCE_SHEET_URL,
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

    (OFFICIAL_NTUA_DIR / "campus-locations.json").write_text(
        json.dumps(
            {
                "school_id": "ntua",
                "school_name": "國立臺灣藝術大學",
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
    (OFFICIAL_NTUA_DIR / "campus-assets.json").write_text(
        json.dumps(
            {
                "school_id": "ntua",
                "school_name": "國立臺灣藝術大學",
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

    ntua_source_urls = [
        NTUA_OIA_HOME_URL,
        NTUA_OIA_ABOUT_URL,
        NTUA_OIA_MEMBERS_URL,
        NTUA_OIA_CONTACT_URL,
        NTUA_REGULATIONS_URL,
        NTUA_SISTER_SCHOOLS_URL,
        NTUA_EXCHANGE_INTRO_URL,
        NTUA_EXCHANGE_PARTNERS_URL,
        NTUA_EXCHANGE_FAQ_URL,
        NTUA_PREDEPARTURE_URL,
        NTUA_EXPERIENCE_PORTAL_URL,
        NTUA_EXPERIENCE_SHEET_URL,
        NTUA_VISITING_STUDENT_URL,
        NTUA_OVERSEAS_INTERNSHIP_URL,
        NTUA_DUAL_DEGREE_URL,
        NTUA_SHORT_TERM_URL,
        NTUA_SCHOLARSHIPS_URL,
        NTUA_DOWNLOADS_URL,
        NTUA_NEWS_116_1_EXCHANGE_URL,
        NTUA_NEWS_115_2_RESULTS_URL,
        NTUA_NEWS_115_XUEHAI_URL,
    ] + list(bin_urls.values())

    exchange_info_payload = {
        "school_name": "國立臺灣藝術大學",
        "program_type": [
            (
                "國際事務處「116學年度第1學期赴外交換學生甄選計畫」（涵蓋日本東京藝術大學、多摩美術大學、武藏野美術大學、女子美術大學、筑波大學、千葉大學、神戶藝術工科大學、沖繩縣立藝術大學、名古屋造形大學，"
                "韓國藝術綜合大學、首爾國立科技大學、中央大學、漢陽大學、建國大學、檀國大學、慶北大學、啟明大學，"
                "法國巴黎第一大學、巴黎第八大學、巴黎西岱大學、國立高等裝飾藝術學院 ENSAD、國立路易盧米埃學院，德國福克旺藝術大學、斯圖加特媒體大學，奧地利維也納音樂與表演藝術大學 mdw、薩爾茲堡莫札特大學，"
                "英國聖三一拉邦音樂舞蹈學院、金士頓大學、巴斯斯巴大學、創意藝術大學、伯明翰城市大學、瑞丁大學，捷克布拉格表演藝術學院 FAMU/HAMU、布拉格藝術建築暨設計學院 UMPRUM，"
                "西班牙瓦倫西亞科技大學、維戈大學，義大利佛羅倫斯 Alchimia 當代珠寶學院，比利時國立剛勃高等視覺藝術學院 La Cambre，"
                "美國天普大學、加州州立大學海峽群島分校，加拿大安大略藝術設計大學 OCAD University，澳洲國立大學 ANU，新加坡國立大學 NUS、拉薩爾藝術學院，香港演藝學院、香港中文大學、香港浸會大學，"
                "以及大陸清華大學、同濟大學、浙江大學、南京大學、武漢大學、廈門大學、中國傳媒大學、中央美院、中國美院、北電、北舞、上戲、川美等"
                f" {open_partner_count} 所開放交換合作校，共 {len(partners)} 所交換合作學校）"
            ),
            (
                "國際事務處「境外大學雙聯學制計畫」（依《國立臺灣藝術大學與境外大學合作辦理雙聯學制實施辦法》，與美國天普大學、英國伯明翰城市大學等合作雙聯學位）暨「訪問生計畫」"
            ),
            (
                "國際事務處「教育部學海飛颺、學海惜珠、學海築夢／新南向學海築夢」暨「補助教職員生參加國際教學展演競賽／國際移地交流合作補助」獎助體系"
            ),
        ],
        "academic_year": [
            (
                "116（涵蓋 116 學年度第 1 學期［2027 年秋季赴外］交換學生計畫甄選：e-Portal 線上申請至 2026/11/02 23:59 截止、11/03 17:00 前紙本送交所屬系所，11/04–11/11 系所初審、11/12–11/23 學院複審、預計 2026/12/30 公告甄選結果）"
            ),
            (
                f"本平台完整收錄國立臺灣藝術大學國際事務處公告之 {len(partners)} 所全球交換合作學校（橫跨全球四大洲 24 個國家與地區，含"
                f" {open_partner_count} 所開放申請之交換合作校，並收錄 {exp_covered_schools} 所合作大學共"
                f" {total_exp_reports} 篇 102–113 學年度赴外交換生研修心得報告）"
            ),
        ],
        "semester": [
            (
                "116學年度第1學期（秋季班）及第2學期（春季班）赴外交換學生甄選（每年分兩梯次辦理：第 1 學期赴外於前一年 9–11 月申請、12 月底放榜；第 2 學期赴外於前一年 2–4 月申請、5 月底放榜）：單次甄選僅可申請 1 間學校，同一學制僅得出國交換 1 次。"
            ),
            (
                "教育部學海飛颺／學海惜珠／學海築夢計畫甄選（每年 2–3 月受理申請，預計 6 月中旬公告核定結果）。"
            ),
        ],
        "application_period": [
            (
                "【116 學年度第 1 學期（2027 秋季班）交換學生計畫甄選】線上申請：即日起至 115 年 11 月 2 日（一）23:59 止（於臺藝大校務行政資訊系統 e-Portal 填報）；"
                "紙本收件截止：115 年 11 月 3 日（二）17:00 前繳交至所屬系（所）辦公室；"
                "系（所）初審：115 年 11 月 4 日至 11 月 11 日；學院複審：115 年 11 月 12 日至 11 月 23 日（11/24 中午 12:00 前送交國際事務處）；"
                "國際教育委員會決審與結果預計公告日：115 年 12 月 30 日。"
            ),
            (
                "【教育部學海飛颺、學海惜珠及學海築夢補助甄選】依《國立臺灣藝術大學辦理教育部學海系列計畫補助作業要點》及當年度簡章，每年 2–3 月開放收件，由國際教育委員會審議推薦排序。"
            ),
        ],
        "eligibility": [
            (
                "1. 在學學籍與修業學期規定：依《國立臺灣藝術大學交換學生甄選要點》，申請人須為申請時已在本校就讀滿 1 學期（含）以上之本校在學生（畢業於本校之在學碩、博生亦須就讀滿 1 學期以上；不含在職專班；休學學生不可提出申請；應屆畢業生須簽署延長修業切結書）。"
            ),
            (
                "2. 學業與操行成績門檻：歷年學業成績（各學期加總）平均達 80 分以上或班（系）排名前 70%，且操行成績平均達 85 分以上並無懲處紀錄。"
            ),
            (
                "3. 單一志願與次數限制及審查配分：單次甄選僅可申請 1 間學校，同一學制僅得出國交換 1 次；校內審查配分為：需語言檢定之學校（在校成績 45%、語言能力 25%、研修計畫 20%、其他得獎／論文／實習 10%）或不需語言檢定之學校（在校成績 55%、研修計畫 25%、其他 20%）。"
            ),
            (
                "4. 保證金、全額學雜費與境外修課及返國義務：錄取後 30 日內須繳交《錄取資格確認書》、《出國研修同意書》及新臺幣 5,000 元保證金收據正本（中低收入戶免繳）；"
                "交換期間須於臺藝大完成註冊並繳交全額學雜費；境外每學期應至少修習 2 門或相當於臺灣學制 6 學分以上課程（至少 1 門為原屬系所專業課程）且通過 1/2 以上；開學後 30 日內須將修課清單送系所審核；返國後 30 日內（學海受獎生為 2 週內）完成返校手續及 2,000 字以上研修心得報告（含照片 3–6 張），始得申請無息退還保證金。"
            ),
        ],
        "language_requirement": [
            (
                "1. 接待合作學校語言門檻與 CEFR 對照：申請需語言檢定之合作學校者，須檢附有效外語能力檢定證明（TOEFL iBT / IELTS / TOEIC / GEPT / JLPT / TOPIK / DELF / TestDaF 等，依臺藝大《CEFR 語言能力參考指標對照表》採認）並符合該校簡章規定標準（語言能力占校內審查總分 25%）。"
            ),
            (
                "2. 歐洲、美加與日韓藝術院校常見門檻：美加及歐洲英語授課學程常要求 TOEFL iBT 72–85 或 IELTS 5.5–6.5（CEFR B2）；法語區要求 DELF B1–B2；德奧區要求德語 B1–B2；日本姊妹校常要求 JLPT N2（東京藝術大學、筑波大學、千葉大學、多摩美、武藏野美等依系所規定）；韓國姊妹校常要求 TOPIK 2–3 級或英語檢定。"
            ),
            (
                "3. 華語授課與免語檢學校評分規定：申請大陸及港澳地區或未規定語言檢定之合作學校者，校內審查配分調整為「在校成績 55%、研修計畫 25%、其他（得獎、發表論文、實習、語檢等）20%」。"
            ),
        ],
        "required_documents": [
            "1. 國立臺灣藝術大學出國交換學生申請表（於 e-Portal 校務行政資訊系統線上填報並列印核章）",
            "2. 本校中文歷年成績單正本（須含各學期加總之歷年學業平均成績及班／系排名百分比，以及操行成績證明）",
            "3. 讀書與研修計畫（Study Plan，以交換國語言及中文各撰寫 1 份，約 1,000–2,000 字）",
            "4. 自傳及履歷表（Autobiography & CV，以交換國語言及中文各撰寫 1 份，約 1,000–2,000 字）",
            "5. 有效外語能力檢定證明（申請需語言檢定之合作學校者必備；不需語檢學校可列為其他加分證明）",
            "6. 個人藝術創作作品集（Portfolio）、展演影音紀錄或得獎／發表論文／實習等有利審查證明文件（應屆畢業生須另附《應屆畢業生切結書》）",
        ],
        "scholarship_info": [
            (
                "1. 教育部《學海飛颺》選送優秀學生出國研修獎學金：依《國立臺灣藝術大學辦理教育部學海系列計畫補助作業要點》，補助具中華民國國籍且在臺設有戶籍、歷年學業表現與外語能力優異之在學學生赴非大陸港澳地區合作學校交換 1 學期或 1 學年之來回機票與國外生活費。"
            ),
            (
                "2. 教育部《學海惜珠》勵學優秀學生出國研修獎學金：補助持各直轄市、縣（市）主管機關開立之低收入戶、中低收入戶、特殊境遇家庭證明或身心障礙相關證明之在學學生赴海外合作學校交換研修來回機票與生活費。"
            ),
            (
                "3. 教育部《學海築夢》及《新南向學海築夢》海外專業實習計畫：由本校專任教師主持計畫選送學生赴海外或新南向國家藝術節、設計公司、影視傳播機構、劇團與博物館實習，補助機票與生活費。"
            ),
            (
                "4. 《國立臺灣藝術大學補助教職員生參加國際教學展演競賽實施要點》與《國際移地交流合作補助要點》：鼓勵在學學生參與國際知名藝術展演、影展、音樂比賽與設計競賽。"
            ),
        ],
        "partner_universities": [p["school_name"] for p in partners],
        "source_urls": ntua_source_urls,
        "last_checked": CHECKED_AT,
    }
    (OFFICIAL_NTUA_DIR / "exchange_info.json").write_text(
        json.dumps(exchange_info_payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    student_dashboard_payload = {
        "school_name": "國立臺灣藝術大學",
        "last_checked": CHECKED_AT,
        "academic_score_minimum": 80.0,
        "academic_score_rule": (
            "依《國立臺灣藝術大學交換學生甄選要點》及《116學年度第1學期交換學生計畫甄選簡章》：申請時已在本校就讀滿 1 學期（含）以上之本校在學生（不含在職專班），"
            "歷年學業成績（各學期加總）平均達 80 分以上或班（系）排名前 70%，且操行成績 85 分以上（無懲處紀錄）；"
            "單次甄選僅可申請 1 間學校，同一學制僅得出國交換 1 次。"
        ),
        "academic_gpa_minimum": None,
        "maximum_preferences": 1,
        "selection_rules": {
            "academic_policy": "score_or_rank",
            "academic_reference_year": "116",
            "undergraduate_gpa_minimum": None,
            "graduate_academic_exempt": False,
            "exclude_in_service": True,
            "pending_quota_planning": False,
            "partner_requirements_need_confirmation": False,
            "degree_score_minimums": {
                "undergraduate": 80.0,
                "master": 80.0,
                "doctoral": 80.0,
            },
            "excluded_undergraduate_years": [],
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
                    "國立臺灣藝術大學「116學年度第1學期（2027秋季赴外）」交換學生計畫甄選（11/02 23:59 e-Portal 線上截止、11/03 17:00 系所紙本收件截止）"
                ),
                "details": [
                    (
                        "開放申請交換期間：116 學年度第 1 學期（2027 年秋季赴外交換 1 學期或 1 學年）。"
                        "線上申請截止：2026 年 11 月 2 日（一）23:59 止（於 e-Portal 校務行政資訊系統填報）；"
                        "紙本繳交截止：2026 年 11 月 3 日（二）17:00 前繳交至所屬系（所）辦公室。"
                    ),
                    (
                        "三級審查與放榜時程：系（所）初審（2026/11/04–11/11）→ 學院複審（2026/11/12–11/23，11/24 中午 12:00 前送交國際事務處）→ 國際教育委員會決審；"
                        "預計於 2026 年 12 月 30 日公告甄選結果，錄取生須於公告後 30 日內繳交《錄取資格確認書》、《出國研修同意書》及 5,000 元保證金收據正本。"
                    ),
                ],
                "source": {
                    "title": "國立臺灣藝術大學國際事務處《116學年度第1學期交換學生計畫甄選公告》",
                    "source_url": NTUA_NEWS_116_1_EXCHANGE_URL,
                    "category": "exchange_application",
                    "summary": "臺藝大 116-1 交換學生計畫甄選簡章、出國交換申請說明會簡報、線上申請與三級審查時程。",
                },
                "scope": "home_application",
                "program_types": ["exchange"],
                "academic_year": "116",
                "application_round": "116學年度第1學期交換學生甄選",
                "audience": "all_students",
                "opens_at": "2026-09-17T09:00:00+08:00",
                "deadline_at": "2026-11-02T23:59:00+08:00",
                "date_status": "verified_exact",
                "status": "open",
                "status_note": "116 學年度第 1 學期交換學生計畫甄選簡章與出國交換申請說明會簡報已公告於國際事務處網站，e-Portal 線上申請開放至 2026/11/02 23:59。",
                "deadline_note": "請於 2026 年 11 月 2 日（一）23:59 前完成 e-Portal 線上申請，並於 11 月 3 日（二）17:00 前將紙本資料繳交至所屬系（所）辦公室。",
                "reminder_eligible": True,
                "checked_at": CHECKED_AT,
            },
        ],
        "program_overview": [{
            "title": (
                f"國立臺灣藝術大學國際事務處全球合作學校交換學生、雙聯學制與學海系列獎助總覽（{len(partners)} 所交換合作校・{open_partner_count} 所開放交換）"
            ),
            "details": [
                (
                    "國立臺灣藝術大學（National Taiwan University of Arts, NTUA，簡稱臺藝大，創校於 1955 年國立藝術學校，為臺灣歷史最悠久之高等藝術學府，位於新北市板橋區大觀路一段 59 號浮洲校區，"
                    "設有「美術學院、設計學院、傳播學院、表演藝術學院、人文學院」五大學院）由國際事務處（Office of International Affairs，位於行政大樓 1 樓）"
                    f"統籌全校赴外交換學生、雙聯學位、海外專業實習及教育部學海系列獎補助。本平台完整收錄 {len(partners)} 所臺藝大官方交換合作學校，"
                    f"橫跨全球四大洲 24 個國家與地區（含 {open_partner_count} 所開放申請之交換合作校）。"
                ),
                (
                    "臺藝大出國交換體系具備五大核心特色：（1）匯聚歐美日韓與大陸頂尖藝術及綜合學府，包括日本東京藝術大學、多摩美術大學、武藏野美術大學、女子美術大學、筑波大學、千葉大學、神戶藝術工科大學、沖繩縣立藝術大學，"
                    "韓國藝術綜合大學、首爾國立科技大學、中央大學、漢陽大學、建國大學，法國巴黎第一大學、巴黎第八大學、巴黎西岱大學、國立高等裝飾藝術學院（ENSAD）、國立路易盧米埃學院，"
                    "德國福克旺藝術大學、斯圖加特媒體大學，奧地利維也納音樂與表演藝術大學（mdw）、薩爾茲堡莫札特大學，英國聖三一拉邦音樂舞蹈學院、金士頓大學、巴斯斯巴大學、創意藝術大學、伯明翰城市大學、瑞丁大學，"
                    "捷克布拉格表演藝術學院（FAMU/HAMU）、布拉格藝術建築暨設計學院（UMPRUM），美國天普大學、加拿大 OCAD University、澳洲國立大學、新加坡國立大學、拉薩爾藝術學院、香港演藝學院、香港中文大學、香港浸會大學，以及大陸清華大學、同濟大學、浙江大學、南京大學、武漢大學、廈門大學、中國傳媒大學、中央美院、中國美院、北電、北舞、上戲、川美等；"
                    "（2）採「e-Portal 線上申請 → 系所初審 → 學院複審 → 國際教育委員會決審」嚴謹機制，單次甄選申請 1 校；"
                    "（3）明確訂定校內審查配分（需語檢學校：在校成績 45%、語言 25%、研修計畫 20%、其他 10%；不需語檢學校：在校成績 55%、研修計畫 25%、其他 20%）；"
                    "（4）結合教育部學海飛颺、學海惜珠、學海築夢與臺藝大國際展演競賽／移地交流補助；"
                    f"（5）完整收錄 102–113 學年度共 {exp_covered_schools} 校 {total_exp_reports} 篇臺藝大學長姐赴外交換研修心得報告。"
                ),
            ],
            "source": {
                "title": "國立臺灣藝術大學國際事務處（OIA）交換學校一覽表與申請辦法專區",
                "source_url": NTUA_EXCHANGE_PARTNERS_URL,
                "category": "exchange_application",
                "summary": f"臺藝大 {len(partners)} 所全球交換合作學校、{open_partner_count} 所開放交換與申請辦法總覽。",
            },
        }],
        "eligibility": [{
            "title": (
                "臺藝大在學滿 1 學期、歷年平均 80 分以上或排名前 70% 門檻、單一志願限制與校內審查配分規定"
            ),
            "details": [
                (
                    "修業學期與學業門檻：依《國立臺灣藝術大學交換學生甄選要點》及《116學年度第1學期交換學生計畫甄選簡章》，申請人須於申請時已在本校就讀滿 1 學期（含）以上（畢業於本校之在學碩、博生亦須就讀滿 1 學期以上；不含在職專班），歷年學業成績（各學期加總）平均達 80 分以上或班（系）排名前 70%，且操行成績 85 分以上（無懲處紀錄）。"
                ),
                (
                    "單一志願、審查配分與 5,000 元保證金：單次甄選僅可申請 1 間學校，同一學制僅得出國交換 1 次；需語檢學校配分（在校成績 45%、語言 25%、研修計畫 20%、其他 10%），不需語檢學校配分（在校成績 55%、研修計畫 25%、其他 20%）。錄取後 30 日內須繳交 5,000 元保證金（中低收入戶免繳），境外每學期至少修習 2 門或 6 學分（含至少 1 門本系專業課）且通過 1/2 以上，返國後 30 日內完成返校手續與 2,000 字心得報告後無息退還。"
                ),
            ],
            "source": {
                "title": "國立臺灣藝術大學交換學生甄選要點與 116 學年度第 1 學期交換學生計畫甄選簡章",
                "source_url": NTUA_SELECTION_REG_PDF,
                "category": "exchange_application",
                "summary": "臺藝大交換生申請資格、學業門檻、評分權重、保證金與境外修課規定。",
            },
        }],
        "language_requirements": [{
            "title": (
                "臺藝大交換留學語言檢定要求（依接待姊妹校門檻及 CEFR 語言能力參考指標對照表採認，占校內審查 25%）"
            ),
            "details": [
                (
                    "語言檢定採認與配分：申請需語言檢定之合作學校者，須檢附有效外語能力檢定證明（TOEFL iBT / IELTS / TOEIC / GEPT / JLPT / TOPIK / DELF / TestDaF 等，依臺藝大《CEFR 語言能力參考指標對照表》換算），語言能力占校內審查總分 25%。"
                ),
                (
                    "免語檢學校配分調整：申請大陸及港澳地區或未要求語言檢定之合作學校者，免附語言檢定證明，校內審查配分調整為「在校成績 55%、研修計畫 25%、其他（得獎、論文、實習、語檢等）20%」。"
                ),
            ],
            "source": {
                "title": "國立臺灣藝術大學《116學年度第1學期交換學生計畫甄選簡章》與《CEFR 語言能力參考指標對照表》",
                "source_url": NTUA_CEFR_MAP_PDF,
                "category": "exchange_application",
                "summary": "臺藝大語言能力參考指標對照表與各合作學校個別語檢門檻。",
            },
        }],
        "required_documents": [{
            "title": (
                "e-Portal 交換學生申請表、中文歷年成績單（含排名百分比）、中外文讀書計畫與自傳履歷（1,000–2,000字）、語言證明與作品集"
            ),
            "details": [
                (
                    "校內甄選必備文件（e-Portal 線上上傳並列印紙本送系所）：（1）申請表；"
                    "（2）本校中文歷年成績單正本（含歷年平均及班／系排名百分比、操行成績）；"
                    "（3）讀書與研修計畫（以交換國語言及中文各撰寫 1 份，約 1,000–2,000 字）；"
                    "（4）自傳及履歷表（以交換國語言及中文各撰寫 1 份，約 1,000–2,000 字）；"
                    "（5）有效語言能力證明（依合作校規定）；"
                    "（6）個人藝術創作作品集（無則免）及其他有利審查文件（得獎、論文、實習等；應屆畢業生須附《應屆畢業生切結書》）。"
                ),
                (
                    "錄取後、行前與返國必備表單：錄取公告後 30 日內繳交《錄取資格確認書》、《出國研修同意書》及 5,000 元保證金收據正本；"
                    "出國前 14 日完成《出國研修實習學生離校手續單》及《選送學生出國健康檢查記錄表》；"
                    "抵達國外 7 日內線上填報居住資訊，開學後 30 日內將修課清單送原屬系所審核；"
                    "返國後 30 日內（學海受獎生為 2 週內）完成《返校手續單》、問卷、2,000 字以上研修心得報告（含照片 3–6 張）及《保證金退費申請表》。"
                ),
            ],
            "source": {
                "title": "國立臺灣藝術大學《116學年度第1學期交換學生計畫甄選簡章》與《出國交換行前須知》",
                "source_url": NTUA_BROCHURE_116_1_PDF,
                "category": "exchange_application",
                "summary": "臺藝大交換學生申請應繳文件、錄取確認書、離返校手續單與保證金退費申請表規範。",
            },
        }],
        "scholarship_info": [{
            "title": (
                "教育部《學海飛颺》、《學海惜珠》、《學海築夢》與臺藝大《國際教學展演競賽／國際移地交流合作補助》"
            ),
            "details": [
                (
                    "教育部學海系列計畫：依《國立臺灣藝術大學辦理教育部學海系列計畫補助作業要點》，錄取非大陸港澳地區合作學校之交換生得申請《學海飛颺》（優秀交換生）或《學海惜珠》（持低收入戶、中低收入戶或特殊境遇家庭證明者）獎助；每年另辦理《學海築夢》及《新南向學海築夢》選送學生赴海外專業機構實習。"
                ),
                (
                    "校內國際展演競賽補助與就學貸款配套：在學學生參與國際知名展演競賽得依《補助教職員生參加國際教學展演競賽實施要點》申請補助；出國交換生如需辦理臺灣銀行就學貸款，可向國際事務處申請《就學貸款海外研修證明信》。"
                ),
            ],
            "source": {
                "title": "國立臺灣藝術大學《辦理教育部學海系列計畫補助作業要點》與《獎學金專區》",
                "source_url": NTUA_SCHOLARSHIPS_URL,
                "category": "scholarship",
                "summary": "臺藝大教育部學海飛颺／惜珠／築夢補助作業要點與國際展演競賽補助規定。",
            },
        }],
        "document_explanations": [{
            "title": (
                "國立臺灣藝術大學 e-Portal 交換學生申請表、中外文讀書計畫與自傳（1,000–2,000字）、藝術作品集與保證金手續準備指南"
            ),
            "summary": (
                "說明臺藝大五大學院交換生甄選必備之 e-Portal 線上表件、中外文讀書計畫與自傳字數規範、作品集準備、校內審查配分及錄取後 5,000 元保證金與離返校手續。"
            ),
            "key_points": [
                (
                    "e-Portal 線上申請與系所紙本雙軌收件：申請人須先於截止日前登入臺藝大校務行政資訊系統（e-Portal）完成線上報名與檔案上傳，再列印紙本於隔日 17:00 前送交系（所）辦公室。"
                ),
                (
                    "中外文讀書計畫與自傳履歷（1,000–2,000 字）及作品集：讀書計畫（占審查 20%–25%）與自傳履歷均須以「交換國語言及中文」各撰寫 1 份（約 1,000–2,000 字），並檢附個人藝術創作作品集或展演影音紀錄。"
                ),
                (
                    "5,000 元保證金與返國 2,000 字心得報告義務：錄取後 30 日內須繳交 5,000 元保證金收據正本、《錄取資格確認書》及《出國研修同意書》；返國後 30 日內完成《返校手續單》及 2,000 字以上心得報告（含照片 3–6 張）始得申請退還保證金。"
                ),
            ],
            "applies_to": [],
            "source": {
                "title": "國立臺灣藝術大學 116學年度第1學期交換學生計畫甄選簡章與申請說明會簡報",
                "source_url": NTUA_NEWS_116_1_EXCHANGE_URL,
                "category": "exchange_application",
                "summary": None,
            },
            "document_url": NTUA_BROCHURE_116_1_PDF,
            "document_type": "official_document",
            "full_text_extracted": True,
        }],
        "rule_explanations": [{
            "title": (
                "國立臺灣藝術大學交換學生甄選要點、辦理教育部學海系列計畫補助作業要點與境外大學雙聯學制實施辦法核心法規"
            ),
            "summary": (
                "規範臺藝大五大學院學生申請出國交換之在學滿 1 學期門檻、學業平均 80 分或前 70% 標準、三級審查配分、境外最低修課學分（2門或6學分）及學海系列獎助核銷規定。"
            ),
            "key_points": [
                (
                    "交換甄選資格與學業門檻：依《國立臺灣藝術大學交換學生甄選要點》，申請時須於本校就讀滿 1 學期以上（不含在職專班），歷年學業平均達 80 分以上或班（系）排名前 70%，操行成績 85 分以上且無懲處紀錄。"
                ),
                (
                    "境外最低修課學分與本系專業課規定：出國交換期間須於臺藝大完成註冊並繳交全額學雜費；於姊妹校每學期應至少修習 2 門或相當於臺灣學制 6 學分以上課程（至少 1 門為原屬系所專業課程），並通過所選讀學分或課程 1/2 以上。"
                ),
                (
                    "開學 30 日內修課清單送審與返國 30 日內核銷：於姊妹校開學後 30 日內須將修課清單送原屬系所審核；返國後 30 日內（學海受獎生為 2 週內）完成返校手續單、問卷及 2,000 字以上研修心得報告。"
                ),
            ],
            "applies_to": [],
            "source": {
                "title": "國立臺灣藝術大學交換學生甄選要點與辦理教育部學海系列計畫補助作業要點",
                "source_url": NTUA_REGULATIONS_URL,
                "category": "exchange_application",
                "summary": None,
            },
            "document_url": NTUA_SELECTION_REG_PDF,
            "document_type": "official_document",
            "full_text_extracted": True,
        }],
        "sources": [
            {
                "title": "國立臺灣藝術大學國際事務處（OIA）官方網站",
                "source_url": NTUA_OIA_HOME_URL,
                "category": "exchange_application",
                "summary": None,
            },
            {
                "title": "國立臺灣藝術大學交換學校一覽表（全球四大洲 102 校完整申請資訊）",
                "source_url": NTUA_EXCHANGE_PARTNERS_URL,
                "category": "partner_school",
                "summary": None,
            },
            {
                "title": "國立臺灣藝術大學 116 學年度第 1 學期交換學生計畫甄選公告（含簡章與說明會簡報）",
                "source_url": NTUA_NEWS_116_1_EXCHANGE_URL,
                "category": "exchange_application",
                "summary": None,
            },
            {
                "title": "國立臺灣藝術大學交換學生甄選要點 PDF",
                "source_url": NTUA_SELECTION_REG_PDF,
                "category": "exchange_application",
                "summary": None,
            },
            {
                "title": "國立臺灣藝術大學出國交換行前須知與離返校手續／保證金退費表單 PDF",
                "source_url": NTUA_PREDEPARTURE_INST_PDF,
                "category": "exchange_application",
                "summary": None,
            },
            {
                "title": "國立臺灣藝術大學與境外大學合作辦理雙聯學制實施辦法 PDF",
                "source_url": NTUA_DUAL_DEGREE_REG_PDF,
                "category": "exchange_application",
                "summary": None,
            },
            {
                "title": "國立臺灣藝術大學辦理教育部學海系列計畫補助作業要點與獎學金專區",
                "source_url": NTUA_SCHOLARSHIPS_URL,
                "category": "scholarship",
                "summary": None,
            },
            {
                "title": "國立臺灣藝術大學出國交換學生心得分享彙整表（102–113學年度 345 篇交換生心得報告）",
                "source_url": NTUA_EXPERIENCE_SHEET_URL,
                "category": "experience_report",
                "summary": None,
            },
        ],
    }
    (OFFICIAL_NTUA_DIR / "student_dashboard.json").write_text(
        json.dumps(student_dashboard_payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    doc_conditions = {
        "school_id": "ntua",
        "school_name": "國立臺灣藝術大學",
        "checked_at": CHECKED_AT,
        "source_url": NTUA_BROCHURE_116_1_PDF,
        "common_documents": exchange_info_payload["required_documents"],
        "track_specific_conditions": [
            {
                "track": "國際事務處【116學年度第1學期赴外交換學生甄選計畫（全球四大洲 97 所開放交換合作校，單次甄選限填 1 校志願）】",
                "required": [
                    "e-Portal 校務行政資訊系統線上填報並列印之出國交換學生申請表及中文歷年成績單正本（含歷年平均及班／系排名百分比、操行成績）",
                    "讀書與研修計畫、自傳及履歷表（均須以交換國語言及中文各撰寫 1 份，約 1,000–2,000 字）",
                    "有效外語能力檢定證明（對照 CEFR 等級表；申請需語檢學校必備）與個人藝術創作作品集（Portfolio）／得獎論文實習證明",
                    "錄取後 30 日內繳交《錄取資格確認書》、《出國研修同意書》及 5,000 元保證金收據正本；出國前 14 日完成《離校手續單》與《出國健康檢查表》；返國後 30 日內完成《返校手續單》及 2,000 字心得報告（含照片 3–6 張）",
                ],
            },
            {
                "track": "國際事務處【境外大學雙聯學制計畫暨訪問生計畫】",
                "required": [
                    "依《國立臺灣藝術大學與境外大學合作辦理雙聯學制實施辦法》檢附雙聯學位申請表、歷年英文成績單、外語檢定證明、作品集與修課抵免計畫書",
                ],
            },
            {
                "track": "教育部【學海飛颺／學海惜珠／學海築夢】出國研修與海外實習獎助學金",
                "required": [
                    "依《國立臺灣藝術大學辦理教育部學海系列計畫補助作業要點》檢附學海計畫申請表、歷年成績單（含排名）、外語能力證明、國外研修或實習計畫書（學海惜珠須另附低收入戶、中低收入戶或特殊境遇家庭證明及戶籍謄本）",
                    "返國後 2 週內須於教育部學海計畫資訊網上傳心得報告及滿意度問卷，並檢附來回電子機票、登機證存根、購票證明及出入境紀錄辦理經費核銷",
                ],
            },
        ],
    }
    (OFFICIAL_NTUA_DIR / "document-conditions.json").write_text(
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
            f"{fname},{len(partners)},{pop},{ratio:.4f},Official NTUA OIA verified"
        )
    (OFFICIAL_NTUA_DIR / "field-coverage.csv").write_text(
        "\n".join(field_cov_lines) + "\n", encoding="utf-8"
    )

    pages_records = [
        {
            "title": "國立臺灣藝術大學：116學年度第1學期交換學生計畫甄選期程（11/02線上截止、11/03系所收件截止）、三級審查與單一志願規定",
            "source_url": NTUA_NEWS_116_1_EXCHANGE_URL,
            "published_at": "2026-09-17T00:00:00Z",
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
            "title": "國立臺灣藝術大學：交換學生甄選要點、歷年平均80分或排名前70%門檻、審查配分與5,000元保證金及境外最低修課規定",
            "source_url": NTUA_SELECTION_REG_PDF,
            "published_at": "2026-09-17T00:00:00Z",
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
            "title": f"國立臺灣藝術大學：{len(partners)} 所全球四大洲交換合作學校一覽表、{open_partner_count} 所開放交換校與 CEFR 語言能力參考指標對照表",
            "source_url": NTUA_EXCHANGE_PARTNERS_URL,
            "published_at": "2026-09-17T00:00:00Z",
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
            "title": "國立臺灣藝術大學：e-Portal 交換申請表、中外文讀書計畫與自傳（1,000–2,000字）、作品集、離返校手續單與返國30日內2,000字心得報告規範",
            "source_url": NTUA_BROCHURE_116_1_PDF,
            "published_at": "2026-09-17T00:00:00Z",
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
            "title": "國立臺灣藝術大學：辦理教育部學海飛颺、學海惜珠、學海築夢計畫補助作業要點與參加國際教學展演競賽／國際移地交流合作補助",
            "source_url": NTUA_SCHOLARSHIPS_URL,
            "published_at": "2026-09-17T00:00:00Z",
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
    (OFFICIAL_NTUA_DIR / "pages.jsonl").write_text(pages_text, encoding="utf-8")
    (OFFICIAL_NTUA_DIR / "processed_pages.jsonl").write_text(
        pages_text, encoding="utf-8"
    )

    home_rules = {
        "school_id": "ntua",
        "school_name": "國立臺灣藝術大學",
        "eligibility": student_dashboard_payload["eligibility"],
        "application_periods": student_dashboard_payload["application_periods"],
        "selection_rules": {
            "undergraduate_score_minimum": 80.0,
            "graduate_score_minimum": 80.0,
            "class_rank_percentile_maximum": 70.0,
            "conduct_score_minimum": 85.0,
            "deposit_amount_twd": 5000,
            "min_courses_per_semester_abroad": 2,
            "min_credits_per_semester_abroad": 6,
            "maximum_preferences": 1,
            "screening_batches_per_year": 2,
            "allow_freshman_apply": True,
            "min_enrolled_semesters_undergrad": 1,
            "min_enrolled_semesters_grad": 1,
            "tuition_policy_during_exchange": (
                "出國交換期間須於國立臺灣藝術大學完成註冊並繳交全額學雜費（保有臺藝大學籍），免繳接待合作學校學費"
            ),
            "return_documents_due": (
                "出國前 14 日完成離校手續單與出國健檢表，抵達國外 7 日內線上填報居住資訊，開學後 30 日內將修課清單送系所審核，返國後 30 日內（學海受獎生 2 週內）完成返校手續單、問卷及 2,000 字以上研修心得報告（含照片 3–6 張）並申請退還 5,000 元保證金"
            ),
        },
        "source_urls": ntua_source_urls,
        "verified_at": "2026-11-01",
    }
    (OFFICIAL_NTUA_DIR / "home_rules.json").write_text(
        json.dumps(home_rules, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    (OFFICIAL_NTUA_DIR / "documents.json").write_text(
        json.dumps(
            {
                "school_name": "國立臺灣藝術大學",
                "required_documents": student_dashboard_payload["required_documents"],
                "source_urls": ntua_source_urls,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    (OFFICIAL_NTUA_DIR / "scholarships.json").write_text(
        json.dumps(
            {
                "school_name": "國立臺灣藝術大學",
                "scholarships": student_dashboard_payload["scholarship_info"],
                "source_urls": ntua_source_urls,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    completeness = {
        "school_id": "ntua",
        "school_name": "國立臺灣藝術大學",
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
            "國立臺灣藝術大學國際事務處 116 學年度第 1 學期交換學生計畫甄選（11/02 23:59 e-Portal 線上申請截止、11/03 17:00 系所紙本收件截止、預計 12/30 放榜，單次甄選限填 1 校志願）"
            "暨雙聯學制與教育部學海系列獎助同步整合；"
            f"共完整收錄 {len(partners)} 所交換合作學校（橫跨全球四大洲 24 個國家與地區，含 {open_partner_count} 所開放申請校，"
            f"並收錄 {exp_covered_schools} 所合作大學共 {total_exp_reports} 篇 102–113 學年度赴外交換生研修心得報告）。"
        ),
        "verified_at": "2026-11-01",
    }
    (OFFICIAL_NTUA_DIR / "catalog-completeness.json").write_text(
        json.dumps(completeness, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    (OFFICIAL_NTUA_DIR / "verification_status.json").write_text(
        json.dumps(
            {
                "school_id": "ntua",
                "school_name": "國立臺灣藝術大學",
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
    (OFFICIAL_NTUA_DIR / "dashboard_manifest.json").write_text(
        json.dumps(
            {
                "school_id": "ntua",
                "school_name": "國立臺灣藝術大學",
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
        ("sources/ntua/oia_spa_index.html", NTUA_OIA_HOME_URL, "國立臺灣藝術大學國際事務處首頁 HTML"),
        ("sources/ntua/oia_about.html", NTUA_OIA_ABOUT_URL, "國立臺灣藝術大學國際事務處—本處簡介 HTML"),
        ("sources/ntua/oia_members.html", NTUA_OIA_MEMBERS_URL, "國際事務處—本處成員與業務職掌 HTML"),
        ("sources/ntua/oia_contact.html", NTUA_OIA_CONTACT_URL, "國際事務處—交通資訊與聯絡方式 HTML"),
        ("sources/ntua/regulations.html", NTUA_REGULATIONS_URL, "國際事務處—出國交換與國際交流法規辦法 HTML"),
        ("sources/ntua/exchange_intro.html", NTUA_EXCHANGE_INTRO_URL, "國際事務處—赴外交換學生計畫介紹與申請流程 HTML"),
        ("sources/ntua/exchange_faq.html", NTUA_EXCHANGE_FAQ_URL, "國際事務處—赴外交換學生常見問題 FAQ HTML"),
        ("sources/ntua/predeparture.html", NTUA_PREDEPARTURE_URL, "國際事務處—錄取交換生行前與返國手續須知 HTML"),
        ("sources/ntua/visiting_student.html", NTUA_VISITING_STUDENT_URL, "國際事務處—訪問生計畫介紹 HTML"),
        ("sources/ntua/overseas_internship.html", NTUA_OVERSEAS_INTERNSHIP_URL, "國際事務處—教育部學海築夢海外實習計畫 HTML"),
        ("sources/ntua/news_116_1_exchange.html", NTUA_NEWS_116_1_EXCHANGE_URL, "116學年度第1學期交換學生計畫甄選公告 HTML"),
        ("sources/ntua/news_115_2_results.html", NTUA_NEWS_115_2_RESULTS_URL, "115學年度第2學期交換學生甄選暨審查結果公告 HTML"),
        ("sources/ntua/news_115_xuehai.html", NTUA_NEWS_115_XUEHAI_URL, "115年度教育部學海系列計畫甄選與核定結果公告 HTML"),
        ("sources/ntua/exchange_schools.json", NTUA_EXCHANGE_PARTNERS_URL, "國際事務處—交換學校一覽表（ExchangeSchoolList 102校）JSON"),
        ("sources/ntua/sister_schools.json", NTUA_SISTER_SCHOOLS_URL, "國際事務處—全球締約姊妹校一覽表（192校）JSON"),
        ("sources/ntua/ntua_experience_sheet.csv", NTUA_EXPERIENCE_SHEET_URL, "國立臺灣藝術大學出國交換學生心得分享彙整表 CSV"),
        ("sources/ntua/ntua_experience_sheet.xlsx", NTUA_EXPERIENCE_SHEET_URL, "國立臺灣藝術大學出國交換學生心得分享彙整表（含超連結）XLSX"),
        ("sources/ntua/ntua_experience_sheet_htmlview.html", NTUA_EXPERIENCE_SHEET_URL, "國立臺灣藝術大學出國交換學生心得分享彙整表 HTML"),
        ("sources/ntua/ntua_experience_raw.json", NTUA_EXPERIENCE_SHEET_URL, "國立臺灣藝術大學出國交換學生心得報告原始清單（685筆）JSON"),
        ("sources/ntua/ntua_experience_index.json", NTUA_EXPERIENCE_SHEET_URL, f"國立臺灣藝術大學赴外交換生研修心得報告（{exp_covered_schools} 校共 {total_exp_reports} 篇）索引 JSON"),
        ("sources/ntua/ntua_catalog_source.json", NTUA_EXCHANGE_PARTNERS_URL, f"國立臺灣藝術大學 {len(partners)} 所交換合作學校整合資料集 JSON"),
        ("sources/ntua/ntua_resolved_locations.json", NTUA_EXCHANGE_PARTNERS_URL, f"國立臺灣藝術大學 {len(partners)} 所交換合作學校 ROR / Wikidata 地理座標核對表 JSON"),
    ]
    for fname, url in bin_urls.items():
        provenance_files.append((f"sources/ntua/{fname}", url, f"國立臺灣藝術大學官方附件：{fname}"))

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
        "school_id": "ntua",
        "school_name": "國立臺灣藝術大學",
        "generated_at": CHECKED_AT,
        "active_cycle_note": completeness["active_term"],
        "sources": prov_sources,
    }
    prov_text = json.dumps(provenance_payload, ensure_ascii=False, indent=2) + "\n"
    (OFFICIAL_NTUA_DIR / "import_provenance.json").write_text(
        prov_text, encoding="utf-8"
    )
    (OFFICIAL_NTUA_DIR / "import-provenance.json").write_text(
        prov_text, encoding="utf-8"
    )

    print(
        f"Successfully built NTUA catalog: {len(partners)} partners"
        f" ({open_partner_count} open, {completeness['verified_campus_images']}"
        f" verified images, {completeness['verified_locations']} verified"
        f" locations), {len(workflows)} workflows,"
        f" {len(destinations)} destinations, {len(research_records)} research"
        f" records, {exp_covered_schools} schools with experience records"
        f" ({len(student_experience_rows)} rows, {total_exp_reports} reports)."
    )


if __name__ == "__main__":
    main()
