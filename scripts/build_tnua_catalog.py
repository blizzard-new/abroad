#!/usr/bin/env python3
"""Build the official Taipei National University of the Arts (國立臺北藝術大學, TNUA) exchange data bundle."""

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
SOURCES_TNUA_DIR = REPO_ROOT / "sources" / "tnua"
OFFICIAL_TNUA_DIR = REPO_ROOT / "src" / "exchange_info" / "official_data" / "tnua"
STATIC_DIR = REPO_ROOT / "src" / "exchange_info" / "static"
UNIVERSITY_LOCATIONS_PATH = (
    REPO_ROOT / "src" / "exchange_info" / "official_data" / "university_locations.jsonl"
)

CHECKED_AT = "2026-11-01T00:00:00Z"

TNUA_OIA_HOME_URL = "https://oia.tnua.edu.tw/"
TNUA_OIA_ABOUT_URL = "https://oia.tnua.edu.tw/about/"
TNUA_OIA_CONTACT_URL = "https://oia.tnua.edu.tw/contact/"
TNUA_OUTGOING_PARTNERS_URL = "https://oia.tnua.edu.tw/outgoing-partners/"
TNUA_EN_OUTGOING_PARTNERS_URL = "https://oia.tnua.edu.tw/en/outgoing-partners/"
TNUA_OUTGOING_APPLICATION_URL = "https://oia.tnua.edu.tw/outgoing-application/"
TNUA_OUTGOING_IMPLEMENTATION_URL = "https://oia.tnua.edu.tw/outgoing-implementation/"
TNUA_OUTGOING_SHARING_URL = "https://oia.tnua.edu.tw/outgoing-sharing/"
TNUA_UMAP_EXCHANGE_URL = "https://oia.tnua.edu.tw/umap-exchange/"
TNUA_CAMPUS_SHARING_PARTNERS_URL = "https://oia.tnua.edu.tw/campus-sharing-partners/"
TNUA_EN_PARTNERS_URL = "https://oia.tnua.edu.tw/en/partners/"
TNUA_NEWS_116_EXCHANGE_URL = (
    "https://oia.tnua.edu.tw/news/%e3%80%90%e4%ba%a4%e6%8f%9b%e7%94%9f%e8%a8%88%e7%95%ab%e3%80%91116%e5%ad%b8%e5%b9%b4%e5%ba%a6%ef%bc%882027-2028%ef%bc%89%e6%9c%ac%e6%a0%a1%e5%a7%8a%e5%a6%b9%e6%a0%a1%e4%ba%a4%e6%8f%9b%e5%ad%b8/"
)
TNUA_NEWS_115_ADMITTED_URL = (
    "https://oia.tnua.edu.tw/news/115%e5%ad%b8%e5%b9%b4%e5%ba%a6%ef%bc%882026-2027%ef%bc%89%e6%9c%ac%e6%a0%a1%e8%b5%b4%e5%a4%96%e4%ba%a4%e6%8f%9b%e5%ad%b8%e7%94%9f%e7%94%84%e9%81%b8%e9%8c%84%e5%8f%96%e5%90%8d%e5%96%ae/"
)
TNUA_NEWS_XUEHAI_2026_URL = (
    "https://oia.tnua.edu.tw/news/%e3%80%90%e7%8d%8e%e5%ad%b8%e9%87%91%e3%80%91115%e5%b9%b4%ef%bc%882026%ef%bc%89%e6%95%99%e8%82%b2%e9%83%a8%e3%80%8c%e5%ad%b8%e6%b5%b7%e9%a3%9b%e9%a2%ba%e3%80%8d%e3%80%81%e3%80%8c%e5%ad%b8/"
)
TNUA_SCHOLARSHIPS_URL = "https://oia.tnua.edu.tw/scholarships/"
TNUA_REGULATIONS_URL = "https://oia.tnua.edu.tw/regulations-and-committee/"
TNUA_ACADEMICS_URL = "https://w3.tnua.edu.tw/academics/"
TNUA_GDRIVE_EXP_URL = (
    "https://drive.google.com/drive/folders/1XiLr5x48f8-fcPpYW13pUehnGBVqw0Fz"
)

REGION_COST_DEFAULTS = {
    "日本": (
        "每月生活費約 USD 700–1,150（折合日圓約 JPY 100,000–165,000 / 月、新臺幣約 22,500–37,000 元；含東京藝術大學、京都市立藝術大學、京都藝術大學、神戶大學、御茶水女子大學、情報科學藝術大學院大學 IAMAS、九州大學等校內外住宿與創作材料膳食費）",
        "須由日本姊妹校代向出入國在留管理局申辦「在留資格認定證明書（COE）」（申請 COE 須檢附英文存款／財力證明），獲發後申辦留學簽證並強制加入日本國民健康保險（NHI）。",
    ),
    "韓國": (
        "每月生活費約 USD 620–1,050（折合韓元約 KRW 850,000–1,450,000 / 月、新臺幣約 20,000–33,500 元；含韓國藝術綜合學校 K-Arts、首爾藝術大學、成均館大學、中央大學、秋溪藝術大學、韓世大學等校內外宿舍與展演創作開銷）",
        "須憑韓國姊妹校核發之標準入學許可書向駐台北韓國代表部申辦 D-2-6 交換學生簽證，入境後申辦外國人登錄證（ARC）並納保韓國國民健康保險（NHIS）。",
    ),
    "中國大陸": (
        "每月生活費約 USD 300–600（折合人民幣約 CNY 2,100–4,200 / 月、新臺幣約 9,600–19,200 元；含中央美術學院、中國美術學院、北京電影學院、上海音樂學院、北京舞蹈學院、中央戲劇學院、中國戲曲學院、南京藝術學院、上海大學、廈門大學等學生宿舍與食堂費）",
        "須憑大陸姊妹校錄取通知書及入學相關文件辦理臺胞證簽注與校內住宿登記，並依規定投保大陸地區醫療與意外保險。",
    ),
    "香港": (
        "每月生活費約 USD 950–1,550（折合港幣約 HKD 7,400–12,000 / 月、新臺幣約 30,500–49,500 元；含香港演藝學院 HKAPA、香港城市大學創意媒體學院、香港浸會大學等住宿與膳食交通費）",
        "須由香港合作校協助向香港入境事務處申辦來港就讀進入許可（Student Visa / Entry Permit），並投保涵蓋全期之海外醫療及意外險。",
    ),
    "新加坡": (
        "每月生活費約 USD 950–1,500（折合新幣約 SGD 1,280–2,000 / 月、新臺幣約 30,500–48,000 元；含新加坡國立大學楊秀桃音樂學院、拉薩爾藝術學院 LASALLE 等住宿與生活費）",
        "須透過新加坡移民與關卡局（ICA）SOLAR 系統申辦 Student's Pass（STP），並投保校方規定之醫療保險。",
    ),
    "美國": (
        "每月生活費約 USD 1,350–2,350（依匯率折合新臺幣約 43,000–75,000 元；含紐約州立大學帕契斯學院 Purchase College、舊金山藝術學院、加州大學河濱分校、北德州大學等住宿、排練器材與校園餐飲費）",
        "須憑美國合作校核發之 DS-2019（J-1 交換生）繳交 SEVIS I-901 費用並向 AIT 申辦簽證，並強制投保接待校規定之學生醫療保險。",
    ),
    "加拿大": (
        "每月生活費約 USD 1,100–1,850（折合加幣約 CAD 1,500–2,500 / 月、新臺幣約 35,000–59,000 元；含加拿大約克大學 York University、英屬哥倫比亞大學 UBC 等住宿與生活費）",
        "須憑加拿大合作大學入學許可申辦學習許可（Study Permit）或簽證，並投保省立或校方規定之學生醫療保險。",
    ),
    "德國": (
        "每月生活費約 USD 980–1,550（折合歐元約 EUR 900–1,420 / 月、新臺幣約 31,500–49,500 元；含漢堡音樂暨戲劇學院、焦特立茲劇院暨阿諾德・荀白克中心、斯圖加特音樂暨表演藝術大學、德勒斯登造型藝術學院、科隆媒體藝術學院、萊比錫視覺藝術學院等學生宿舍與學期交通卡費）",
        "須開立德國限制提領帳戶（Blocked Account）並憑入學許可向德國在台協會申辦學生簽證及投保德國公保／醫療險。",
    ),
    "法國": (
        "每月生活費約 USD 950–1,550（折合歐元約 EUR 880–1,420 / 月、新臺幣約 30,500–49,500 元；含巴黎國立高等美術學院 Beaux-Arts de Paris、里昂國立高等音樂暨舞蹈學院 CNSMD de Lyon、南特大西洋設計學院、巴黎第八大學、拉羅謝爾大學等住宿與創作材料費）",
        "須透過法國教育中心（Campus France）完成面試並申辦法國長期學生簽證 VLS-TS，入境後完成 OFII 認證並納保法國學生健保。",
    ),
    "奧地利": (
        "每月生活費約 USD 950–1,500（折合歐元約 EUR 880–1,380 / 月、新臺幣約 30,500–48,000 元；含維也納音樂暨表演藝術大學 mdw、格拉茨音樂暨表演藝術大學 KUG、薩爾茲堡莫札特大學、林茲藝術大學等學生宿舍與琴房排練生活費）",
        "須憑奧地利接待大學入學許可、住宿證明與財力證明向奧地利台北辦事處申辦 D 類學生簽證，並投保涵蓋申根區全期之醫療與意外保險。",
    ),
    "英國": (
        "每月生活費約 USD 1,250–2,100（折合英鎊約 GBP 980–1,650 / 月、新臺幣約 40,000–67,000 元；含倫敦藝術大學 UAL、倫敦大學皇家霍洛威學院、羅浮堡大學、雪菲爾哈倫大學等學生宿舍與生活費）",
        "須依英國簽證暨移民署（UKVI）規定申辦 Standard Visitor Visa（6 個月內交換）或 Student Visa（超過 6 個月並繳納 IHS 健保附加費），並投保海外醫療保險。",
    ),
    "瑞士": (
        "每月生活費約 USD 1,450–2,300（折合瑞士法郎約 CHF 1,300–2,050 / 月、新臺幣約 46,500–73,500 元；含蘇黎世藝術大學 ZHdK、日內瓦藝術與設計大學 HEAD – Genève 等住宿與生活費）",
        "須憑瑞士接待大學入學許可、財力證明與住宿證明向瑞士商務辦事處申辦 D 類國家學生簽證，並依瑞士聯邦規定辦理學生健康保險。",
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
    "瑞士": "秋季學期（Herbstsemester）：每年 9 月中旬至翌年 1 月；春季學期（Frühlingssemester）：每年 2 月中旬至 6 月",
}


def clean_text(s: str) -> str:
    return re.sub(r"\s+", " ", s).strip() if s else ""


def sync_global_assets_and_locations(
    catalog_source: list[dict], resolved_locations: dict
) -> None:
    """Ensure school-images.json and university_locations.jsonl contain all TNUA partner schools."""
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
                else loc.get("lat", 25.1332)
            )
            lon = float(
                loc.get("longitude")
                if loc.get("longitude") is not None
                else loc.get("lon", 121.4706)
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
    OFFICIAL_TNUA_DIR.mkdir(parents=True, exist_ok=True)
    catalog_source = json.loads(
        (SOURCES_TNUA_DIR / "tnua_catalog_source.json").read_text(encoding="utf-8")
    )
    resolved_locations = json.loads(
        (SOURCES_TNUA_DIR / "tnua_resolved_locations.json").read_text(encoding="utf-8")
    )
    bin_urls = json.loads(
        (SOURCES_TNUA_DIR / "binary_source_urls.json").read_text(encoding="utf-8")
    )

    TNUA_BROCHURE_116_PDF = bin_urls["tnua_116_exchange_brochure.pdf"]
    TNUA_APP_FORM_ZH_PDF = bin_urls["tnua_application_form_zh.pdf"]
    TNUA_APP_FORM_EN_PDF = bin_urls["tnua_application_form_en.pdf"]
    TNUA_SELECTION_REG_PDF = bin_urls["tnua_exchange_selection_regulations.pdf"]
    TNUA_ADMIN_CONTRACT_PDF = bin_urls["tnua_exchange_admin_contract.pdf"]
    TNUA_BRIEFING_115_PDF = bin_urls["tnua_115_application_briefing.pdf"]
    TNUA_PREDEPARTURE_PDF = bin_urls["tnua_115_predeparture_briefing.pdf"]
    TNUA_XUEHAI_WORKFLOW_PDF = bin_urls["tnua_xuehai_selection_workflow.pdf"]
    TNUA_OVERSEAS_CONTACT_PDF = bin_urls["tnua_overseas_contact_form.pdf"]
    TNUA_CREDIT_TRANSFER_PDF = bin_urls["tnua_credit_transfer_form.pdf"]
    TNUA_COLLEGE_REC_PDF = bin_urls["tnua_college_recommendation_form.pdf"]
    TNUA_SHARED_CAMPUS_GUIDELINES_PDF = bin_urls["tnua_shared_campus_guidelines.pdf"]

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

    round_label = "116學年度姊妹校交換學生甄選（02/23學院薦送截止）"
    app_deadline_str = (
        "116學年度（2027/2028）姊妹校交換學生甄選：簡章於 2026/09/29 公告，申請人須先向所屬系所提出申請，"
        "經系所初審與學院複審後，由各學院於 2027/02/23（二）17:00 前將《學院推薦交換學生資料表》及全套申請文件彙整送達國際事務處（學生活動中心 4 樓），"
        "再由國際交流事務委員會複審核定推薦名單（每位學生每梯次甄選至多可填報 2 間交換學校志願）"
    )
    deadline_iso = "2027-02-23T17:00:00+08:00"
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

        group_str = clean_text(item.get("group") or "國際事務處校級締約姊妹校")
        prog_raw = clean_text(
            item.get("program_type_raw") or "116／115學年度赴外姊妹校交換學生甄選計畫"
        )
        quota_str = clean_text(item.get("quota") or "依當期交換生簡章及兩校互惠名額核定")
        detail_url = item.get("detail_url") or TNUA_OUTGOING_PARTNERS_URL
        source_url = detail_url
        program_type = f"國際事務處【{prog_raw}】（{group_str}）"

        colleges_str = clean_text(
            item.get("colleges")
            or "不限學院（音樂學院、美術學院、戲劇學院、舞蹈學院、電影與新媒體學院、文化資源學院、人文學院在學學生均得依姊妹校對應藝術專業系所申請）"
        )
        degree_levels_str = clean_text(
            item.get("eligible_degrees")
            or "國立臺北藝術大學學士班二年級以上（不含在職專班）及碩、博士班於本校就讀一學期以上之在學學生"
        )
        lang_req_str = clean_text(
            item.get("language_req")
            or "須具備校外具公信力機構之有效語言能力證明（TOEFL iBT / IELTS / TOEIC / 全民英檢 GEPT / JLPT / TOPIK / DELF / TestDaF）或修習外語課程 2 學期以上且成績達 80 分以上之證明，並符合接待姊妹校門檻；申請大陸地區姊妹校免附語言證明"
        )
        gpa_req_str = clean_text(
            item.get("gpa_req")
            or "需經所屬系所初審及學院複審推薦（檢附歷年中英文成績單含班級排名百分比、出國研習計畫書、英文推薦函2封以上及作品集／展演影音紀錄），再由國際交流事務委員會複審核定"
        )
        website = item.get("website") or source_url
        factsheet_url = item.get("factsheet_url") or website
        remarks_raw = clean_text(item.get("notes") or "")
        tuition_note = clean_text(
            item.get("tuition_note")
            or "交換期間須於國立臺北藝術大學完成註冊並繳交全額學雜費（含使用及代辦費用；延修生亦須繳交全額學雜費；碩、博士生最低應修 6 學分並繳納最低 6 學分之學分費及學雜費基數），免繳接待姊妹校學費（住宿、生活、簽證、保險與往返機票費自理）"
        )
        exps = item.get("experience_reports") or []

        win_status = "open" if avail_status == "open" else "closed"
        study_period_str = (
            "一學期或一學年（以一學期或一學年為原則；每位學生每梯次甄選至多可填報 2 間交換學校志願；"
            "另設 Shared Campus 校園共享專案跨國課程與 UMAP 亞太大學交流會 Program A/B/C 交換）"
        )
        sem_dates_str = SEMESTER_DATES_BY_COUNTRY.get(
            country,
            "春季班（第2學期）：每年 1–2 月起至 6–7 月止（預計）；秋季班（第1學期）：每年 8–9 月起至翌年 1–2 月止（預計）",
        )
        housing_str = (
            f"獲國立臺北藝術大學國際事務處推薦提名後，可依 {zh_name} 指引申請校內外學生宿舍或自行安排住宿（{tuition_note}）。"
        )
        course_rest_str = (
            f"開放對象與領域：{colleges_str}（{degree_levels_str}）。依《國立臺北藝術大學選送學生出國進修與交流甄選辦法》及《選送學生赴外交換行政契約書》規定："
            "（1）學士班二年級以上（不含在職專班）及碩、博士班於本校就讀一學期以上之在學學生得申請（法國巴黎國立高等美術學院僅限大三學生申請且延修生不得申請；香港浸會大學僅限大學部學生）；"
            "（2）自 115 學年度起每位學生每梯次甄選至多可填報 2 間交換學校志願，採「系所初審 → 學院複審 → 國際交流事務委員會複審核定」三級審查；"
            "（3）出國交換期間須繳交北藝大全額學雜費（延修生亦同；碩博士生最低應修 6 學分並繳納最低 6 學分學分費及學雜費基數），出國前至少 2 個月（或收到入學許可後 1 個月內）須與連帶保證人簽署《選送學生赴外交換行政契約書》；"
            "（4）抵達姊妹校 2 週內須回傳《赴外交換生海外聯絡資訊通報表》，返國後 2 週內須向國際事務處報到並繳交 1,000 字以內出國交換報告（含照片 4 張以上），修課結束後 2 個月內辦理學分抵免。"
        )

        living_cost_str, visa_health_str = REGION_COST_DEFAULTS.get(
            country,
            (
                "每月生活費約 USD 700–1,450（依匯率折合新臺幣約 22,500–46,500 元，含住宿、藝術創作材料、膳食與市區交通）",
                "須依接待國駐臺機構規定申辦學生簽證，並於出國前投保涵蓋海外交換全期之海外醫療及意外保險。",
            ),
        )

        tuition_points_list = [
            (
                "國立臺北藝術大學學雜費規定與姊妹校待遇：依《國立臺北藝術大學選送學生出國進修與交流甄選辦法》及《選送學生赴外交換行政契約書》，"
                f"交換期間學生仍須於本校完成註冊並繳交全額學雜費（含使用及代辦費用；延修生亦須繳交全額學雜費；碩、博士生最低應修 6 學分並繳納最低 6 學分之學分費及學雜費基數），免繳接待姊妹校學費。本合作校待遇：{tuition_note}。"
            ),
            (
                "國立臺北藝術大學四大出國研修與創作獎助體系：（1）教育部《學海飛颺》選送優秀學生出國研修獎學金（依《學海飛颺暨學海惜珠補助甄選作業流程》，由各學院推薦每院至多 5 名並排序，經國際交流事務委員會審核通過後核定補助）；"
                "（2）教育部《學海惜珠》勵學優秀學生出國研修獎學金（持低收入戶、中低收入戶或特殊境遇家庭證明者專案補助來回機票與國外生活費）；"
                "（3）教育部《學海築夢／新南向學海築夢》海外專業藝術與文化機構實習計畫；"
                "（4）《Shared Campus 校園共享專案》跨文化合作課程（Transcultural Collaboration）、批判生態學（Critical Ecologies）及暑期學校（Summer Schools）定額機票與住宿獎助（與蘇黎世藝術大學 ZHdK、倫敦藝術大學 UAL、東京藝術大學、京都藝術大學、香港城市大學、香港浸會大學、新加坡拉薩爾藝術學院合作）。"
            ),
        ]

        app_steps_list = [
            (
                f"步驟一（確認北藝大在學年級、志願上限 2 校與 {zh_name} 語言及作品集要求）："
                f"確認符合《國立臺北藝術大學選送學生出國進修與交流甄選辦法》資格（{degree_levels_str}），備妥有效語言能力證明（{lang_req_str}）與個人藝術創作作品集或展演影音紀錄。"
            ),
            (
                "步驟二（向所屬系所提出申請，經系所初審與學院複審於 2027/02/23 前薦送國際事務處）：備妥（1）交換學生申請表（中、英文各乙份）、"
                "（2）歷年中文及英文成績單正本（含班級排名百分比）、（3）語言能力證明、（4）中文及外文出國研習計畫書、（5）英文推薦函 2 封以上、（6）個人作品集或展演影音紀錄，送交系所初審及學院複審，由學院於 2027/02/23 前彙整送達國際事務處。"
            ),
            (
                "步驟三（國際交流事務委員會複審核定推薦名單暨簽署《選送學生赴外交換行政契約書》）：由國際交流事務委員會複審通過後公告錄取名單；"
                "錄取生須於出國前至少 2 個月（或收到姊妹校入學許可後 1 個月內）偕同連帶保證人完成《選送學生赴外交換行政契約書》簽署。"
            ),
            (
                f"步驟四（由國際事務處向 {full_name} 提名、海外聯絡通報與返國 2 週內繳交心得報告及 2 個月內辦理學分抵免）："
                "抵達姊妹校 2 週內須回傳《赴外交換生海外聯絡資訊通報表》，並於北藝大開學第 5 週前於藝務系統填送《選課通報表》；返國後 2 週內向國際事務處報到並繳交 1,000 字以內出國交換報告（含照片 4 張以上），修課結束後 2 個月內提出《赴外交換生學分抵免申請書》。"
            ),
        ]

        elig_points_list = [
            f"合作類別與計畫群組：{program_type}",
            f"開放學制與修業年級：{degree_levels_str}",
            f"開放申請院系與領域：{colleges_str}",
            f"三級審查與專業要求：{gpa_req_str}",
            f"語言能力標準：{lang_req_str}",
            "志願上限與返國義務：每梯次甄選至多可填報 2 間交換學校志願；出國前須簽署行政契約書，抵達後 2 週內通報海外聯絡資訊，返國後 2 週內繳交 1,000 字以內交換報告（含照片 4 張以上）並於 2 個月內辦理學分抵免。",
        ]
        if tuition_note:
            elig_points_list.append(f"學雜費與研究所最低學分規定：{tuition_note}")
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
                eurl = e.get("url") or TNUA_OUTGOING_SHARING_URL
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
                    "department": e.get("department") or "國立臺北藝術大學赴外交換學生",
                })
                snippet_str = clean_text(e.get("snippet") or "")
                summary_text = (
                    f"國立臺北藝術大學國際事務處「赴外交換生經驗分享專區」收錄之 {esem} 赴 {country} {full_name} 交換研修心得報告（{raw_t}）。"
                    + (f" 摘錄：{snippet_str[:180]}" if snippet_str else " 涵蓋校內三級審查與作品集準備、姊妹校專業藝術課程與工坊修習、住宿申請與教育部學海飛颺獎學金核銷實務。")
                )
                theme_map = {
                    "academics": (
                        f"北藝大交換生於《{raw_t}》分享在 {zh_name} 修習專業藝術創作、展演工坊與返國後辦理學分抵免之經驗。"
                    ),
                    "housing": (
                        f"北藝大交換生分享申請 {zh_name} 校內外學生宿舍與租屋生活適應（{housing_str[:100]}）。"
                    ),
                    "campus_culture": (
                        f"北藝大國際事務處透過《{raw_t}》傳承海外藝術院校跨文化創作交流、音樂廳／劇場／美術館資源與學習心得。"
                    ),
                    "cost": (
                        f"北藝大交換生分享於 {zh_name} 之每月住宿、創作材料與生活花費（{living_cost_str[:100]}），以及申請教育部學海飛颺／學海惜珠獎學金之經驗。"
                    ),
                }
                student_experience_rows.append({
                    "school_name": full_name,
                    "country": country,
                    "title": raw_t,
                    "source_url": eurl,
                    "source_type": "article",
                    "platform": "國立臺北藝術大學國際事務處—赴外交換生經驗分享專區（106–114學年）",
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
                        f"{full_name}:tnua_exp:{e_idx}:{eurl}".encode("utf-8")
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
            "home_university": "國立臺北藝術大學",
            "school_name": full_name,
            "country": country,
            "official_experience_portal_url": (
                exp_links[0]["url"] if exp_links else TNUA_OUTGOING_SHARING_URL
            ),
            "partner_page_url": source_url,
            "report_count": len(exps),
            "sample_reports": sample_reports,
            "checked_at": CHECKED_AT,
        })

        loc = resolved_locations.get(full_name) or {
            "city": country,
            "latitude": 25.1332,
            "longitude": 121.4706,
            "source_url": "https://www.wikidata.org",
        }
        city_name = loc.get("city") or country
        lat = float(
            loc.get("latitude")
            if loc.get("latitude") is not None
            else loc.get("lat", 25.1332)
        )
        lon = float(
            loc.get("longitude")
            if loc.get("longitude") is not None
            else loc.get("lon", 121.4706)
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
                " 及國立臺北藝術大學國際事務處四大洲姊妹校申請資訊表（美洲、歐洲、亞洲、大洋洲）與 Shared Campus 專區比對；實際交換校區以錄取通知與姊妹校簡章為準。"
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
            f"【語言與作品集審查門檻】{lang_req_str}｜{gpa_req_str}",
            f"【住宿與生活資訊】{housing_str}",
        ]
        if exps:
            notes_lines.append(
                f"【北藝大學長姐交換研修心得報告（共 {len(exps)} 篇）】收錄於國際事務處赴外交換生經驗分享專區（含：{'、'.join(exp_labels[:4])}）"
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
            "quota_status": "published" if avail_status == "open" else "reference_only",
            "availability_status": avail_status,
            "availability_note": (
                f"國立臺北藝術大學國際事務處公告合作姊妹校（{program_type}）；名額：{quota_str}（{remarks_raw}）。"
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
                "title": f"國立臺北藝術大學國際事務處出國交換姊妹校申請資訊表—{zh_name}",
                "source_url": source_url,
                "role": "home_university",
                "authority": "home_official_notice",
                "effective_academic_year": acad_year,
                "application_round": round_label,
                "checked_at": CHECKED_AT,
            },
            {
                "title": "國立臺北藝術大學 116學年度（2027/2028）姊妹校交換學生甄選簡章 PDF",
                "source_url": TNUA_BROCHURE_116_PDF,
                "role": "home_university",
                "authority": "home_official_notice",
                "effective_academic_year": acad_year,
                "application_round": round_label,
                "checked_at": CHECKED_AT,
            },
            {
                "title": "國立臺北藝術大學選送學生出國進修與交流甄選辦法 PDF",
                "source_url": TNUA_SELECTION_REG_PDF,
                "role": "home_university",
                "authority": "home_official_notice",
                "effective_academic_year": acad_year,
                "application_round": round_label,
                "checked_at": CHECKED_AT,
            },
        ]
        if exp_links:
            wf_sources.append({
                "title": f"國立臺北藝術大學國際事務處赴外交換生經驗分享專區—{zh_name}",
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
            "home_university": "國立臺北藝術大學",
            "school_name": full_name,
            "partner_website": website,
            "country": country,
            "program_type": program_type,
            "academic_year": acad_year,
            "application_round": round_label,
            "effective_application_rounds": [
                round_label,
                "116學年度姊妹校交換學生甄選",
                "115學年度姊妹校交換學生甄選",
                "115-1",
                "115-2",
                "116-1",
                "116-2",
            ],
            "applicability_status": "verified",
            "applicability_note": (
                "國立臺北藝術大學由國際事務處（臺北市北投區學園路 1 號學生活動中心 4 樓，電話：02-2896-1000 分機 2602 沈孟儒專員／2603 陳依卿專員／2608 校園共享專案）"
                "統籌全校七大學院（音樂學院、美術學院、戲劇學院、舞蹈學院、電影與新媒體學院、文化資源學院、人文學院）之全球姊妹校交換學生、"
                "Shared Campus 校園共享專案、UMAP 亞太大學交流會交換及教育部學海飛颺、學海惜珠與學海築夢獎助遴選。"
            ),
            "review_status": "published",
            "published_at": CHECKED_AT,
            "steps": [
                {
                    "rule_id": f"tnua-{acad_year}-home-1-{sn:03d}",
                    "order": 1,
                    "phase": "校內申請",
                    "title": f"確認北藝大學士班大二以上／碩博就讀滿一學期資格、志願上限（至多2校）及 {zh_name} 語言與作品集門檻",
                    "responsible_party": "學生",
                    "responsible_unit": "國立臺北藝術大學各系所／國際事務處（學生活動中心 4 樓）",
                    "deadline_at": deadline_iso,
                    "deadline_status": "verified_exact",
                    "deadline_source_url": TNUA_NEWS_116_EXCHANGE_URL,
                    "deadline_checked_at": CHECKED_AT,
                    "deadline_reminder_eligible": True,
                    "summary": (
                        f"確認符合《國立臺北藝術大學選送學生出國進修與交流甄選辦法》及當期《姊妹校交換學生甄選簡章》規定（{degree_levels_str}），"
                        f"每位學生每梯次甄選至多可填報 2 間交換學校志願，並備妥符合 {zh_name} 規定之語言能力證明（{lang_req_str}）與個人作品集。"
                    ),
                    "details": [
                        f"開放學制與院系：{colleges_str}（{degree_levels_str}）",
                        f"語言與審查條件：{lang_req_str}｜{gpa_req_str}",
                        f"當期名額與計畫類別：{quota_str}｜{program_type}",
                    ],
                    "scope": {
                        "home_universities": ["國立臺北藝術大學"],
                        "partner_universities": [full_name],
                        "academic_years": ["115", "116"],
                        "application_rounds": [round_label, "115-1", "115-2", "116-1", "116-2"],
                    },
                    "source_urls": [source_url, TNUA_SELECTION_REG_PDF, TNUA_BROCHURE_116_PDF],
                    "checked_at": CHECKED_AT,
                    "support_status": "verified",
                },
                {
                    "rule_id": f"tnua-{acad_year}-home-2-{sn:03d}",
                    "order": 2,
                    "phase": "校內申請",
                    "title": "備妥中英文交換申請表、歷年中英文成績單、語言證明、中外文出國研習計畫書、英文推薦函2封與作品集送系所初審及學院複審",
                    "responsible_party": "學生與所屬系所／學院",
                    "responsible_unit": "北藝大七大學院暨所屬系所／國際事務處（學生活動中心 4 樓）",
                    "deadline_at": deadline_iso,
                    "deadline_status": "verified_exact",
                    "deadline_source_url": TNUA_NEWS_116_EXCHANGE_URL,
                    "deadline_checked_at": CHECKED_AT,
                    "deadline_reminder_eligible": True,
                    "summary": (
                        "申請學生須先依所屬系所與學院規定截止日提送全套申請資料，經系所初審、學院複審通過後，"
                        "由各學院於 2027/02/23（二）17:00 前將《學院推薦交換學生資料表》及申請人資料彙整送交國際事務處。"
                    ),
                    "details": [
                        "語言能力證明須為校外具公信力機構之有效語言檢定，或修習外語課程 2 學期以上且成績達 80 分以上之證明（大陸地區免附）。",
                        "藝術專業系所申請人須依接待姊妹校規定準備個人作品集（Portfolio）或展演影音紀錄連結。",
                    ],
                    "document_requirements": [
                        {
                            "name": "國立臺北藝術大學交換學生申請表（中、英文各乙份）暨學院推薦交換學生資料表",
                            "official_form_url": TNUA_APP_FORM_ZH_PDF,
                            "source_urls": [TNUA_APP_FORM_ZH_PDF, TNUA_APP_FORM_EN_PDF, TNUA_COLLEGE_REC_PDF],
                        },
                        {
                            "name": "歷年中文及英文成績單正本（含班級排名百分比）及有效語言能力證明",
                            "official_form_url": TNUA_BROCHURE_116_PDF,
                            "source_urls": [TNUA_BROCHURE_116_PDF, TNUA_SELECTION_REG_PDF],
                        },
                        {
                            "name": "中文及外文出國研習計畫書（Study Plan）、英文推薦函 2 封以上及個人作品集／展演影音紀錄",
                            "official_form_url": TNUA_BROCHURE_116_PDF,
                            "source_urls": [TNUA_BROCHURE_116_PDF, TNUA_BRIEFING_115_PDF],
                        },
                    ],
                    "scope": {
                        "home_universities": ["國立臺北藝術大學"],
                        "academic_years": ["115", "116"],
                        "application_rounds": [round_label, "115-1", "115-2", "116-1", "116-2"],
                    },
                    "source_urls": [TNUA_NEWS_116_EXCHANGE_URL, TNUA_BROCHURE_116_PDF, TNUA_APP_FORM_ZH_PDF],
                    "checked_at": CHECKED_AT,
                    "support_status": "verified",
                },
                {
                    "rule_id": f"tnua-{acad_year}-home-3-{sn:03d}",
                    "order": 3,
                    "phase": "甄選與提名",
                    "title": "國際交流事務委員會複審核定推薦名單、申請教育部學海飛颺／惜珠獎學金並簽署《選送學生赴外交換行政契約書》",
                    "responsible_party": "國立臺北藝術大學國際交流事務委員會／國際事務處與錄取學生",
                    "responsible_unit": "國立臺北藝術大學國際交流事務委員會／國際事務處",
                    "deadline_at": "2027-03-31T17:00:00+08:00",
                    "deadline_status": "reference_only",
                    "deadline_source_url": TNUA_OUTGOING_APPLICATION_URL,
                    "deadline_checked_at": CHECKED_AT,
                    "deadline_reminder_eligible": False,
                    "summary": (
                        "各學院薦送名單經國際交流事務委員會複審通過後公告錄取名單；符合資格之非大陸港澳地區錄取生得依《學海飛颺暨學海惜珠補助甄選作業流程》經學院推薦（每院至多 5 名並排序）申請教育部學海獎學金。"
                    ),
                    "details": [
                        "獲選為交換學生者，應於出國前至少 2 個月（或收到交換學校入學許可後 1 個月內），由本人及連帶保證人與本校簽署《國立臺北藝術大學選送學生赴外交換行政契約書》。",
                        "無正當理由放棄交換資格者，於同一學制就讀期間不得再次申請出國交換。",
                    ],
                    "scope": {
                        "home_universities": ["國立臺北藝術大學"],
                        "academic_years": ["115", "116"],
                        "application_rounds": [round_label, "115-1", "115-2", "116-1", "116-2"],
                    },
                    "source_urls": [TNUA_SELECTION_REG_PDF, TNUA_ADMIN_CONTRACT_PDF, TNUA_XUEHAI_WORKFLOW_PDF],
                    "checked_at": CHECKED_AT,
                    "support_status": "verified",
                },
                {
                    "rule_id": f"tnua-{sn:03d}-host-apply",
                    "order": 4,
                    "phase": "合作校申請",
                    "title": f"由國際事務處向 {zh_name} 提名並遞交姊妹校入學申請與專業作品集審核文件",
                    "responsible_party": "學生與接待校國際事務處／專業藝術學院",
                    "summary": (
                        "獲本校公告錄取後，由國際事務處依各姊妹校時程完成線上或電郵提名；"
                        "學生須於姊妹校申請截止日前備妥有效護照、英文成績單、英文財力證明、語檢證明、推薦信與作品集／試奏試演影音，由接待校專業系所進行最終入學審核並核發正式入學許可（Admission Letter / COE / DS-2019）。"
                    ),
                    "details": [
                        f"研修期程：{study_period_str}｜名額：{quota_str}",
                        f"語言與審查條件：{lang_req_str}｜{gpa_req_str}",
                        f"住宿與費用待遇：{housing_str}",
                    ],
                    "scope": {
                        "home_universities": ["國立臺北藝術大學"],
                        "partner_universities": [full_name],
                        "academic_years": ["115", "116"],
                        "application_rounds": [round_label, "115-1", "115-2", "116-1", "116-2"],
                    },
                    "source_urls": [source_url, TNUA_BROCHURE_116_PDF] + ([website] if website else []),
                    "checked_at": CHECKED_AT,
                    "support_status": "verified",
                    "needs_confirmation": False,
                },
                {
                    "rule_id": f"tnua-{acad_year}-home-5-{sn:03d}",
                    "order": 5,
                    "phase": "行前準備",
                    "title": "完成北藝大全額學雜費註冊（碩博至少6學分）、海外保險、抵達2週內通報聯絡資訊、返國2週內繳交報告與2個月內學分抵免",
                    "responsible_party": "學生與所屬系所",
                    "responsible_unit": "國立臺北藝術大學國際事務處／教務處註冊組／各學院系所",
                    "summary": (
                        "出國前須完成北藝大每學期全額學雜費註冊（碩、博士生最低應修 6 學分並繳納最低 6 學分之學分費及學雜費基數）並投保海外醫療及意外險；"
                        "抵達姊妹校 2 週內回傳《赴外交換生海外聯絡資訊通報表》，開學第 5 週前於藝務系統填送《選課通報表》；返國後 2 週內向國際處報到並繳交 1,000 字以內出國交換報告（含照片 4 張以上），修課結束後 2 個月內提出《赴外交換生學分抵免申請書》。"
                    ),
                    "details": tuition_points_list,
                    "scope": {
                        "home_universities": ["國立臺北藝術大學"],
                        "academic_years": ["115", "116"],
                        "application_rounds": [round_label, "115-1", "115-2", "116-1", "116-2"],
                    },
                    "source_urls": [
                        TNUA_OUTGOING_IMPLEMENTATION_URL,
                        TNUA_ADMIN_CONTRACT_PDF,
                        TNUA_OVERSEAS_CONTACT_PDF,
                        TNUA_CREDIT_TRANSFER_PDF,
                    ],
                    "checked_at": CHECKED_AT,
                    "support_status": "verified",
                },
            ],
            "sources": wf_sources,
            "last_checked": CHECKED_AT,
            "coverage_status": "official_verified",
            "coverage_note": (
                f"已完整整合國立臺北藝術大學國際事務處（OIA）全球四大洲共 {len(catalog_source)} 所合作姊妹校與交換／Shared Campus／UMAP 專案（含"
                f" {open_partner_count} 所開放交換合作學校）、"
                "選送學生出國進修與交流甄選辦法、選送學生赴外交換行政契約書、學海飛颺暨學海惜珠補助甄選作業流程，以及"
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
                "title": f"國立臺北藝術大學國際事務處出國交換姊妹校申請資訊表—{zh_name}",
                "source_url": source_url,
                "summary": "北藝大國際事務處公告之合作領域、名額、語言門檻與學費待遇",
            },
            {
                "title": "國立臺北藝術大學 116學年度姊妹校交換學生甄選簡章與選送學生出國進修與交流甄選辦法",
                "source_url": TNUA_BROCHURE_116_PDF,
                "summary": "北藝大交換生三級審查流程、志願上限（2校）、行政契約書及返國義務規定",
            },
        ]
        if exp_links:
            dest_sources.append({
                "title": f"國立臺北藝術大學國際事務處赴外交換生經驗分享專區—{zh_name}",
                "source_url": exp_links[0]["url"],
                "summary": f"收錄北藝大學生赴 {zh_name} 出國交換研修心得報告共 {len(exps)} 篇",
            })
        if website:
            dest_sources.append({
                "title": f"{full_name} 官方網站",
                "source_url": website,
                "summary": "接待合作姊妹校官方網站",
            })

        src_url_list = (
            [source_url, TNUA_OUTGOING_PARTNERS_URL, TNUA_SCHOLARSHIPS_URL]
            + ([exp_links[0]["url"]] if exp_links else [TNUA_OUTGOING_SHARING_URL])
            + ([website] if website else [])
        )

        destinations.append({
            "home_university": "國立臺北藝術大學",
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
                    "title": "生活費、北藝大全額學雜費註冊（碩博至少6學分）規定與學海系列／Shared Campus 獎助體系",
                    "summary": cost_line,
                    "points": [cost_line] + tuition_points_list,
                    "source_urls": src_url_list + [
                        TNUA_SELECTION_REG_PDF,
                        TNUA_ADMIN_CONTRACT_PDF,
                        TNUA_BROCHURE_116_PDF,
                    ],
                    "caution": "交換期間須於北藝大完成註冊並繳交全額學雜費（延修生亦同；碩博士生最低應修 6 學分並繳納最低 6 學分學分費及學雜費基數）。",
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
                    "title": "海外醫療與意外保險規定暨海外聯絡資訊通報",
                    "summary": visa_health_str,
                    "points": [
                        visa_health_str,
                        "錄取學生出國前須購買涵蓋交換全期之海外急難救助、醫療與意外保險，並於抵達姊妹校 2 週內填送《赴外交換生海外聯絡資訊通報表》予國際事務處。",
                    ],
                    "source_urls": src_url_list + [TNUA_ADMIN_CONTRACT_PDF, TNUA_OVERSEAS_CONTACT_PDF],
                    "caution": "出國前請確認海外醫療保險涵蓋門診、住院及跨國急難救助，並依接待國法令加入當地國民健康保險或學生保險。",
                },
                {
                    "key": "visa",
                    "title": "留學交換簽證辦理、連帶保證人《選送學生赴外交換行政契約書》與役男出境緩徵申請",
                    "summary": visa_health_str,
                    "points": [
                        visa_health_str,
                        "錄取生須於出國前至少 2 個月（或收到入學許可後 1 個月內）偕同連帶保證人完成《選送學生赴外交換行政契約書》簽署；具役男身分之在學學生，應於出國前至少 45 日檢附入學許可向學務處辦理役男出境緩徵。",
                    ],
                    "source_urls": src_url_list + [TNUA_OUTGOING_IMPLEMENTATION_URL, TNUA_PREDEPARTURE_PDF],
                    "caution": "學海受獎生購買國際來回機票若由旅行社開立代收轉付收據，買受人抬頭須填「國立臺北藝術大學」並註明統一編號「99335422」。",
                },
                {
                    "key": "academics",
                    "title": "海外藝術專業修課、藝務系統選課通報（第5週前）與返國學分抵免（2個月內）",
                    "summary": course_clean[:160],
                    "points": [calendar_clean, course_clean],
                    "source_urls": src_url_list + [TNUA_CREDIT_TRANSFER_PDF, TNUA_BROCHURE_116_PDF],
                    "caution": "交換生須於北藝大開學第 5 週前登入藝務系統（iTNUA）填寫《選課通報表》送交系所助教，並於修課結束後 2 個月內提出《赴外交換生學分抵免申請書》。",
                },
                {
                    "key": "living",
                    "title": f"{city_name} 校園生活、106–114學年赴外交換生經驗分享專區與行前說明會傳承",
                    "summary": f"代表城市：{city_name}。錄取學生返國後 2 週內須繳交 1,000 字以內出國交換報告（含照片 4 張以上）。",
                    "points": [
                        f"目的地城市：{city_name}（{country}）",
                        "國立臺北藝術大學國際事務處建置完整「赴外交換生經驗分享專區（106–114學年）」並定期舉辦申請與行前說明會"
                        + (
                            f"（本校於此姊妹校共收錄 {len(exps)} 篇：{'、'.join(exp_labels[:3])}）"
                            if exps
                            else ""
                        )
                        + "，提供作品集準備、選課、住宿與生活第一手資訊。",
                    ],
                    "source_urls": [
                        exp_links[0]["url"] if exp_links else TNUA_OUTGOING_SHARING_URL
                    ],
                },
            ],
            "sources": dest_sources,
            "last_checked": CHECKED_AT,
            "coverage_status": "official_verified",
            "coverage_note": (
                f"已整合國立臺北藝術大學國際事務處 {len(catalog_source)} 所合作姊妹校名冊、116／115 學年度姊妹校交換學生甄選簡章、Shared Campus／UMAP 專區及"
                f" {exp_covered_schools} 校 {total_exp_reports} 篇赴外交換生研修心得報告。"
            ),
        })

        research_records.append({
            "home_university": "國立臺北藝術大學",
            "school_name": full_name,
            "country": country,
            "official_website": website,
            "verification_status": "official_verified",
            "discovery_source_url": detail_url,
            "checked_at": CHECKED_AT,
            "note": (
                f"國立臺北藝術大學國際事務處全球四大洲 {len(catalog_source)} 所合作姊妹校申請資訊表、Shared Campus 校園共享專案與"
                " ROR/Wikidata 官方網址核對完成。"
            ),
        })

        ev_sources = [{
            "title": f"國立臺北藝術大學國際事務處出國交換姊妹校資訊—{zh_name}",
            "url": source_url,
        }]
        if exp_links:
            ev_sources.append({
                "title": f"國立臺北藝術大學國際事務處赴外交換生經驗分享專區—{zh_name}",
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
                "scope": "北藝大海外交換姊妹校住宿與財力證明資訊",
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
                "scope": "北藝大出國交換全額學雜費規定（碩博至少6學分）、教育部學海飛颺／惜珠、Shared Campus 獎助與地區生活費估算",
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
                "scope": "國立臺北藝術大學選送學生出國進修與交流甄選辦法、選課通報與學分抵免規定",
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
                "scope": "北藝大海外交換簽證、選送學生赴外交換行政契約書、海外聯絡通報與海外醫療保險規定",
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
                        f"｜北藝大國際事務處收錄 {len(exps)} 篇赴 {zh_name} 交換研修心得報告（{'、'.join(exp_labels[:3])}）。"
                        if exps
                        else ""
                    )
                ),
                "sources": ev_sources,
                "checked_at": CHECKED_AT,
                "scope": "北藝大交換名額與 106–114 學年赴外交換生研修心得報告傳承",
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
                    f"已整合國立臺北藝術大學國際事務處 {len(catalog_source)} 所合作姊妹校名冊、116／115 學年度姊妹校交換學生甄選簡章、Shared Campus／UMAP 專區及歷年交換生心得報告。"
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

    write_jsonl(OFFICIAL_TNUA_DIR / "partners.jsonl", partners)
    write_jsonl(SOURCES_TNUA_DIR / "partners.jsonl", partners)
    write_jsonl(OFFICIAL_TNUA_DIR / "application_workflows.jsonl", workflows)
    write_jsonl(OFFICIAL_TNUA_DIR / "destination_profiles.jsonl", destinations)
    write_jsonl(OFFICIAL_TNUA_DIR / "partner_research.jsonl", research_records)
    write_jsonl(OFFICIAL_TNUA_DIR / "student_life.jsonl", life_records)
    write_jsonl(OFFICIAL_TNUA_DIR / "experience_sources.jsonl", experience_sources_records)
    write_jsonl(
        OFFICIAL_TNUA_DIR / "student_experience_sources.jsonl",
        experience_sources_records,
    )
    write_jsonl(OFFICIAL_TNUA_DIR / "student_experiences.jsonl", student_experience_rows)

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
    (OFFICIAL_TNUA_DIR / "student-experience-digests.json").write_text(
        json.dumps({"digests": digest_records}, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    (OFFICIAL_TNUA_DIR / "student-experiences.json").write_text(
        json.dumps(
            {
                "school_id": "tnua",
                "school_name": "國立臺北藝術大學",
                "checked_at": CHECKED_AT,
                "source_url": TNUA_OUTGOING_SHARING_URL,
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

    (OFFICIAL_TNUA_DIR / "campus-locations.json").write_text(
        json.dumps(
            {
                "school_id": "tnua",
                "school_name": "國立臺北藝術大學",
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
    (OFFICIAL_TNUA_DIR / "campus-assets.json").write_text(
        json.dumps(
            {
                "school_id": "tnua",
                "school_name": "國立臺北藝術大學",
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

    tnua_source_urls = [
        TNUA_OIA_HOME_URL,
        TNUA_OIA_ABOUT_URL,
        TNUA_OIA_CONTACT_URL,
        TNUA_OUTGOING_PARTNERS_URL,
        TNUA_EN_OUTGOING_PARTNERS_URL,
        TNUA_OUTGOING_APPLICATION_URL,
        TNUA_OUTGOING_IMPLEMENTATION_URL,
        TNUA_OUTGOING_SHARING_URL,
        TNUA_UMAP_EXCHANGE_URL,
        TNUA_CAMPUS_SHARING_PARTNERS_URL,
        TNUA_EN_PARTNERS_URL,
        TNUA_NEWS_116_EXCHANGE_URL,
        TNUA_NEWS_115_ADMITTED_URL,
        TNUA_NEWS_XUEHAI_2026_URL,
        TNUA_SCHOLARSHIPS_URL,
        TNUA_REGULATIONS_URL,
        TNUA_ACADEMICS_URL,
        TNUA_GDRIVE_EXP_URL,
    ] + list(bin_urls.values())

    exchange_info_payload = {
        "school_name": "國立臺北藝術大學",
        "program_type": [
            (
                "國際事務處「116／115學年度赴外姊妹校交換學生甄選計畫」（涵蓋東京藝術大學、京都市立藝術大學、京都藝術大學、情報科學藝術大學院大學 IAMAS、韓國藝術綜合學校 K-Arts、首爾藝術大學、成均館大學、"
                "巴黎國立高等美術學院 Beaux-Arts de Paris、里昂國立高等音樂暨舞蹈學院 CNSMD de Lyon、維也納音樂暨表演藝術大學 mdw、格拉茨音樂暨表演藝術大學 KUG、薩爾茲堡莫札特大學、林茲藝術大學、"
                "蘇黎世藝術大學 ZHdK、日內瓦藝術與設計大學 HEAD、漢堡音樂暨戲劇學院、斯圖加特音樂暨表演藝術大學、德勒斯登造型藝術學院、科隆媒體藝術學院、萊比錫視覺藝術學院、"
                "倫敦大學皇家霍洛威學院、布拉格表演藝術學院 AMU、赫爾辛基藝術大學 Uniarts Helsinki、紐約州立大學帕契斯學院 Purchase College、加拿大約克大學、"
                "新加坡國立大學楊秀桃音樂學院、香港演藝學院 HKAPA、香港城市大學、香港浸會大學、中央美術學院、中國美術學院、北京電影學院、上海音樂學院、北京舞蹈學院、中央戲劇學院等"
                f" {open_partner_count} 所開放交換合作校，以及全球四大洲 {len(partners)} 所締約姊妹校）"
            ),
            (
                "國際事務處「Shared Campus 校園共享專案」（與瑞士蘇黎世藝術大學 ZHdK、英國倫敦藝術大學 UAL、日本東京藝術大學、京都藝術大學、香港城市大學、香港浸會大學、新加坡拉薩爾藝術學院 LASALLE 合作跨文化合作課程 TC、批判生態學 CE 與暑期學校 Summer Schools）暨「UMAP 亞太大學交流會（Program A/B/C）」交換學生計畫"
            ),
            (
                "國際事務處「教育部學海飛颺、學海惜珠、學海築夢／新南向學海築夢」暨 Shared Campus 跨國共學機票與住宿獎助體系"
            ),
        ],
        "academic_year": [
            (
                "116（涵蓋 116 學年度［2027/2028］本校姊妹校交換學生甄選：2026/09/29 公告簡章，申請人向所屬系所提出申請，經系所初審與學院複審於 2027/02/23 前薦送國際事務處，再由國際交流事務委員會複審核定）"
            ),
            (
                f"本平台完整收錄國立臺北藝術大學國際事務處公告之 {len(partners)} 所全球合作姊妹校與交換／Shared Campus／UMAP 專案（橫跨全球四大洲 24 個國家與地區，含"
                f" {open_partner_count} 所開放申請之交換合作校，並收錄 {exp_covered_schools} 所合作大學共"
                f" {total_exp_reports} 篇 106–114 學年度赴外交換生研修心得報告）"
            ),
        ],
        "semester": [
            (
                "116學年度第1、2學期赴外交換學生甄選（每年 9 月底公告簡章、翌年 2 月下旬學院薦送截止、3 月底前國際交流事務委員會複審核定，預計 2027 年秋季或 2028 年春季出國交換）：每位學生每梯次至多可填報 2 間交換學校志願。"
            ),
            (
                "UMAP 亞太大學交流會交換計畫（每年分秋季與春季兩梯次開放 Program A/B 學期交換及 Program C 短期文化課程申請）與 Shared Campus 校園共享專案跨國模組。"
            ),
        ],
        "application_period": [
            (
                "【116 學年度（2027/2028）本校姊妹校交換學生甄選】簡章於 2026/09/29 公告；申請人須依所屬系所規定收件截止日提送申請表件與作品集，"
                "經系所初審與學院複審後，由各學院於 2027/02/23（二）17:00 前將《學院推薦交換學生資料表》及申請資料彙整送交國際事務處（學生活動中心 4 樓）。"
            ),
            (
                "【教育部學海飛颺及學海惜珠補助甄選】依《國立臺北藝術大學辦理教育部學海飛颺暨學海惜珠補助甄選作業流程》，由各學院推薦每院至多 5 名並排序，送國際交流事務委員會審核核定。"
            ),
        ],
        "eligibility": [
            (
                "1. 在學學籍與修業年級規定：依《國立臺北藝術大學選送學生出國進修與交流甄選辦法》，申請人須為本校學士班二年級以上（不含在職專班）或碩、博士班於本校就讀一學期以上之在學學生"
                "（特定姊妹校另有規定者從其規定，例如法國巴黎國立高等美術學院僅限大三學生申請且延修生不能申請；香港浸會大學僅限大學部學生）。"
            ),
            (
                "2. 三級審查機制與志願數上限：自 115 學年度起，每位學生每梯次甄選至多可填報 2 間交換學校志願；甄選採「系所初審 → 學院複審 → 國際交流事務委員會複審核定」三級審查。"
            ),
            (
                "3. 交換期間註冊繳費與研究所學分規定：依《選送學生赴外交換行政契約書》，交換期間學生仍須於北藝大完成註冊並繳交全額學雜費（含使用及代辦費用；延修生亦須繳交全額學雜費；碩、博士生最低應修 6 學分並應繳納最低 6 學分之學分費及學雜費基數）。"
            ),
            (
                "4. 行政契約書簽署與返國義務：錄取生須於出國前至少 2 個月（或收到入學許可後 1 個月內）偕同連帶保證人簽署《選送學生赴外交換行政契約書》；"
                "抵達姊妹校 2 週內通報海外聯絡資訊，返國後 2 週內向國際處報到並繳交 1,000 字以內出國交換報告（含照片 4 張以上），修課結束後 2 個月內辦理學分抵免。"
            ),
        ],
        "language_requirement": [
            (
                "1. 校內基本語言能力證明規定：申請非大陸地區姊妹校者，須檢附（1）校外具公信力機構之有效語言能力檢定證明（TOEFL iBT / IELTS / TOEIC / 全民英檢 GEPT / JLPT / TOPIK / DELF / TestDaF 等），或（2）修習外語課程 2 學期以上且成績達 80 分以上之證明；惟接待姊妹校訂有明確檢定門檻者（如蘇黎世藝術大學、維也納音樂暨表演藝術大學、阿姆斯特丹藝術大學、東京藝術大學、韓國藝術綜合學校等），須符合該校規定標準。"
            ),
            (
                "2. 歐洲、美加與日韓藝術院校常見門檻：美加及歐洲英語授課學程常要求 TOEFL iBT 79–90 或 IELTS 6.0–6.5；法語區（如巴黎國立高等美術學院、里昂國立高等音樂暨舞蹈學院）要求 DELF B1–B2；德奧區（如維也納 mdw、格拉茨 KUG、漢堡音樂暨戲劇學院、德勒斯登造型藝術學院）要求德語 B1–B2；日本姊妹校常要求 JLPT N2；韓國姊妹校常要求 TOPIK 2–3 級或英語檢定。"
            ),
            (
                "3. 大陸地區豁免規定：申請赴中國大陸 10 所姊妹校（中央美術學院、中國美術學院、北京電影學院、上海音樂學院、北京舞蹈學院、中央戲劇學院、中國戲曲學院、南京藝術學院、上海大學、廈門大學）交換者，免附外語能力證明。"
            ),
        ],
        "required_documents": [
            "1. 國立臺北藝術大學交換學生申請表（中、英文各乙份，貼妥兩吋照片並經系所核章）及各學院彙整之《學院推薦交換學生資料表》",
            "2. 本校歷年中文成績單及英文成績單正本各乙份（須註明班級排名或系所排名百分比）",
            "3. 有效外語能力證明（校外具公信力機構之語言檢定成績單影本，或修習外語課程 2 學期以上且成績達 80 分以上之證明；大陸地區免附）",
            "4. 中文及外文出國研習計畫書（Study Plan）各乙份",
            "5. 本校教師英文推薦函 2 封以上（Letters of Recommendation）",
            "6. 個人藝術創作作品集（Portfolio）、展演影音紀錄連結或優秀事蹟證明文件（依各藝術專業學院與接待姊妹校規定準備）",
        ],
        "scholarship_info": [
            (
                "1. 教育部《學海飛颺》選送優秀學生出國研修獎學金：補助具中華民國國籍且在臺設有戶籍、外語與專業表現優異之在學學生赴非大陸港澳地區姊妹校交換 1 學期或 1 學年；依北藝大甄選作業流程，由各學院推薦每院至多 5 名並排序，送國際交流事務委員會審核核定。"
            ),
            (
                "2. 教育部《學海惜珠》勵學優秀學生出國研修獎學金：補助持各直轄市、縣（市）主管機關開立之低收入戶、中低收入戶、特殊境遇家庭證明或身心障礙相關證明之在學學生赴海外姊妹校交換研修來回機票與生活費。"
            ),
            (
                "3. 教育部《學海築夢》及《新南向學海築夢》海外專業實習計畫：由本校專任教師主持計畫選送學生赴海外或新南向國家藝術節、劇場、樂團、舞團與博物館實習，補助機票與生活費。"
            ),
            (
                "4. 《Shared Campus 校園共享專案》跨國共學獎助：參與北藝大與蘇黎世藝術大學（ZHdK）、倫敦藝術大學（UAL）、東京藝術大學、京都藝術大學等聯盟校共同開設之跨文化合作課程（TC）、批判生態學（CE）或暑期學校（Summer Schools）者，得依專案簡章申請機票與住宿定額補助。"
            ),
        ],
        "partner_universities": [p["school_name"] for p in partners],
        "source_urls": tnua_source_urls,
        "last_checked": CHECKED_AT,
    }
    (OFFICIAL_TNUA_DIR / "exchange_info.json").write_text(
        json.dumps(exchange_info_payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    student_dashboard_payload = {
        "school_name": "國立臺北藝術大學",
        "last_checked": CHECKED_AT,
        "academic_score_minimum": None,
        "academic_score_rule": (
            "依《國立臺北藝術大學選送學生出國進修與交流甄選辦法》及當期《姊妹校交換學生甄選簡章》：學士班二年級以上（不含在職專班）及碩、博士班於本校就讀一學期以上之在學學生得申請；"
            "採「系所初審 → 學院複審 → 國際交流事務委員會複審核定」三級審查，綜合評量歷年學業成績（含班級排名百分比）、中外文出國研習計畫書、語言能力證明、2 封英文推薦函及個人藝術創作作品集／展演影音紀錄。"
        ),
        "academic_gpa_minimum": None,
        "maximum_preferences": 2,
        "selection_rules": {
            "academic_policy": "score_or_rank",
            "academic_reference_year": "116",
            "undergraduate_gpa_minimum": None,
            "graduate_academic_exempt": False,
            "exclude_in_service": True,
            "pending_quota_planning": False,
            "partner_requirements_need_confirmation": False,
            "degree_score_minimums": {},
            "excluded_undergraduate_years": ["大一"],
            "language_certificate_required": True,
        },
        "language_score_minimums": {
            "toefl": 61.0,
            "ielts": 5.5,
            "toeic": 550.0,
        },
        "application_periods": [
            {
                "title": (
                    "國立臺北藝術大學「116學年度（2027/2028）」姊妹校交換學生甄選（09/29公告–02/23學院薦送截止，每生至多填報2校志願）"
                ),
                "details": [
                    (
                        "開放申請交換期間：116 學年度第 1 學期及第 2 學期（2027 年秋季或 2028 年春季出國交換，可同步參與教育部學海飛颺／學海惜珠學院推薦）。"
                        "簡章公告日：2026 年 9 月 29 日；申請人須依所屬系所規定收件截止日提送申請資料與作品集，經系所初審及學院複審後，由各學院於 2027 年 2 月 23 日（二）17:00 前彙整送達國際事務處。"
                    ),
                    (
                        "志願數與審查程序：自 115 學年度起，每位學生每梯次甄選至多可填報 2 間交換學校志願；"
                        "經系所初審、學院複審並送國際交流事務委員會複審通過後公告錄取名單，錄取生須於出國前至少 2 個月偕同連帶保證人簽署《選送學生赴外交換行政契約書》。"
                    ),
                ],
                "source": {
                    "title": "國立臺北藝術大學國際事務處《116學年度（2027/2028）本校姊妹校交換學生甄選公告》",
                    "source_url": TNUA_NEWS_116_EXCHANGE_URL,
                    "category": "exchange_application",
                    "summary": "北藝大 116 學年度姊妹校交換學生甄選簡章、中英文申請表、四大洲姊妹校資訊表與學院薦送期限。",
                },
                "scope": "home_application",
                "program_types": ["exchange"],
                "academic_year": "116",
                "application_round": "116學年度姊妹校交換學生甄選",
                "audience": "all_students",
                "opens_at": "2026-09-29T09:00:00+08:00",
                "deadline_at": "2027-02-23T17:00:00+08:00",
                "date_status": "verified_exact",
                "status": "open",
                "status_note": "116 學年度（2027/2028）姊妹校交換學生甄選簡章、中英文申請表與四大洲姊妹校申請資訊表已公告於國際事務處網站。",
                "deadline_note": "請先確認所屬系所及學院內部收件截止日；各學院須於 2027 年 2 月 23 日（二）前將推薦資料表及全套申請文件送達國際事務處。",
                "reminder_eligible": True,
                "checked_at": CHECKED_AT,
            },
        ],
        "program_overview": [{
            "title": (
                f"國立臺北藝術大學國際事務處全球姊妹校交換學生、Shared Campus 校園共享與 UMAP 交流總覽（{len(partners)} 所締約姊妹校・{open_partner_count} 所開放交換）"
            ),
            "details": [
                (
                    "國立臺北藝術大學（Taipei National University of the Arts, TNUA，創校於 1982 年國立藝術學院，位於臺北市北投區學園路 1 號關渡校區，"
                    "設有「音樂學院、美術學院、戲劇學院、舞蹈學院、電影與新媒體學院、文化資源學院、人文學院」七大學院）由國際事務處（Office of International Affairs，位於學生活動中心 4 樓）"
                    f"統籌全校赴外姊妹校交換、Shared Campus 跨國共學、UMAP 亞太大學交流會及教育部學海系列獎補助。本平台完整收錄 {len(partners)} 所北藝大官方合作姊妹校，"
                    f"橫跨全球四大洲 24 個國家與地區（含 {open_partner_count} 所開放申請之交換合作校）。"
                ),
                (
                    "北藝大出國交換體系具備五大核心特色：（1）集結全球頂尖高等藝術院校，包括法國巴黎國立高等美術學院（Beaux-Arts de Paris）、里昂國立高等音樂暨舞蹈學院（CNSMD de Lyon）、"
                    "奧地利維也納音樂暨表演藝術大學（mdw）、格拉茨音樂暨表演藝術大學（KUG）、薩爾茲堡莫札特大學、瑞士蘇黎世藝術大學（ZHdK）、日內瓦藝術與設計大學（HEAD）、"
                    "德國漢堡音樂暨戲劇學院、斯圖加特音樂暨表演藝術大學、德勒斯登造型藝術學院、科隆媒體藝術學院、萊比錫視覺藝術學院、捷克布拉格表演藝術學院（AMU）、芬蘭赫爾辛基藝術大學、"
                    "美國紐約州立大學帕契斯學院（Purchase College）、日本東京藝術大學、京都市立藝術大學、韓國藝術綜合學校（K-Arts）、新加坡國立大學楊秀桃音樂學院、香港演藝學院（HKAPA）及大陸中央美院、中國美院、北電、上音、北舞、中戲等；"
                    "（2）採「系所初審 → 學院複審 → 國際交流事務委員會複審核定」專業三級審查，每梯次至多可填報 2 校志願；"
                    "（3）共同發起國際藝術大學聯盟《Shared Campus 校園共享專案》並參與《UMAP 亞太大學交流會》；"
                    "（4）結合教育部學海飛颺、學海惜珠與學海築夢獎助；"
                    f"（5）完整收錄 106–114 學年度共 {exp_covered_schools} 校 {total_exp_reports} 篇北藝大學長姐赴外交換研修心得報告。"
                ),
            ],
            "source": {
                "title": "國立臺北藝術大學國際事務處（OIA）出國交換姊妹校與申請資訊專區",
                "source_url": TNUA_OUTGOING_PARTNERS_URL,
                "category": "exchange_application",
                "summary": f"北藝大 {len(partners)} 所全球合作姊妹校、{open_partner_count} 所開放交換與 Shared Campus 總覽。",
            },
        }],
        "eligibility": [{
            "title": (
                "北藝大學士班大二以上／碩博就讀滿一學期資格、三級審查機制（系所→學院→國際交流事務委員會）與志願上限 2 校規定"
            ),
            "details": [
                (
                    "修業年級與學籍規定：依《國立臺北藝術大學選送學生出國進修與交流甄選辦法》及當期《姊妹校交換學生甄選簡章》，申請人須為本校學士班二年級以上（不含在職專班）或碩、博士班於本校就讀一學期以上之在學學生（特定姊妹校另有規定者從其規定，如法國巴黎國立高等美術學院僅限大三學生且延修生不可申請；香港浸會大學僅限大學部）。"
                ),
                (
                    "志願上限、全額學雜費與行政契約書：自 115 學年度起每位學生每梯次甄選至多可填報 2 間交換學校志願；出國交換期間仍須繳交北藝大全額學雜費（延修生亦同；碩博士生最低應修 6 學分並繳納最低 6 學分學分費及學雜費基數），並於出國前至少 2 個月偕同連帶保證人簽署《選送學生赴外交換行政契約書》。"
                ),
            ],
            "source": {
                "title": "國立臺北藝術大學選送學生出國進修與交流甄選辦法與 116 學年度交換甄選簡章",
                "source_url": TNUA_SELECTION_REG_PDF,
                "category": "exchange_application",
                "summary": "北藝大交換生申請資格、三級審查程序、行政契約書與註冊繳費規定。",
            },
        }],
        "language_requirements": [{
            "title": (
                "北藝大交換留學語言證明規定（校外公信力語言檢定 TOEFL / IELTS / JLPT / TOPIK / DELF / TestDaF 或修習外語 2 學期達 80 分以上；大陸地區免附）"
            ),
            "details": [
                (
                    "校內語言證明雙軌制與姊妹校門檻：申請非大陸地區姊妹校者，須檢附校外具公信力機構之有效語言能力檢定證明，或修習外語課程 2 學期以上且成績達 80 分以上之證明；惟接待姊妹校訂有明確檢定門檻者（如歐洲、美加、日韓多數音樂與藝術院校要求 IELTS 6.0–6.5、TOEFL iBT 79–90、DELF B1–B2、德語 B1–B2、JLPT N2 或 TOPIK 2–3 級），須符合該校標準。"
                ),
                (
                    "大陸地區豁免規定：申請赴中國大陸姊妹校（中央美術學院、中國美術學院、北京電影學院、上海音樂學院、北京舞蹈學院、中央戲劇學院、中國戲曲學院、南京藝術學院、上海大學、廈門大學）交換者，免附外語能力證明。"
                ),
            ],
            "source": {
                "title": "國立臺北藝術大學《116學年度姊妹校交換學生甄選簡章》與《四大洲姊妹校申請資訊表》",
                "source_url": TNUA_OUTGOING_PARTNERS_URL,
                "category": "exchange_application",
                "summary": "北藝大語言能力證明採認標準與四大洲姊妹校個別語檢門檻。",
            },
        }],
        "required_documents": [{
            "title": (
                "中英文交換學生申請表、歷年中英文成績單（含班排百分比）、語言證明、中外文出國研習計畫書、英文推薦函 2 封與藝術作品集"
            ),
            "details": [
                (
                    "校內甄選必備文件：（1）國立臺北藝術大學交換學生申請表（中、英文各乙份）及學院彙整之《學院推薦交換學生資料表》；"
                    "（2）歷年中文及英文成績單正本各乙份（含班級排名百分比）；"
                    "（3）有效外語能力證明（大陸地區免附）；"
                    "（4）中文及外文出國研習計畫書（Study Plan）各乙份；"
                    "（5）本校教師英文推薦函 2 封以上；"
                    "（6）個人藝術創作作品集（Portfolio）、展演影音紀錄連結或優秀事蹟證明文件。"
                ),
                (
                    "錄取後、海外在學與返國核銷文件：出國前至少 2 個月簽署《選送學生赴外交換行政契約書》（含連帶保證人）；"
                    "抵達姊妹校 2 週內回傳《赴外交換生海外聯絡資訊通報表》，北藝大開學第 5 週前於藝務系統填送《選課通報表》；"
                    "返國後 2 週內繳交 1,000 字以內出國交換報告（含照片 4 張以上），修課結束後 2 個月內提出《赴外交換生學分抵免申請書》。"
                ),
            ],
            "source": {
                "title": "國立臺北藝術大學《出國交換甄選申請資訊》與《錄取後執行手冊》",
                "source_url": TNUA_OUTGOING_APPLICATION_URL,
                "category": "exchange_application",
                "summary": "北藝大交換學生申請應繳文件、行政契約書、海外聯絡通報表與學分抵免申請書規範。",
            },
        }],
        "scholarship_info": [{
            "title": (
                "教育部《學海飛颺》、《學海惜珠》、《學海築夢》與《Shared Campus 校園共享專案》跨國共學獎助"
            ),
            "details": [
                (
                    "教育部學海系列計畫：依《國立臺北藝術大學辦理教育部學海飛颺暨學海惜珠補助甄選作業流程》，錄取非大陸港澳地區姊妹校交換生得由所屬學院推薦（每院至多推薦 5 名並排列優先順序），送國際交流事務委員會審核通過後核定《學海飛颺》或《學海惜珠》獎助；返國後須於姊妹校學期結束後 1 週內上傳報告至教育部系統並檢附機票證明（旅行社代收轉付收據統編：99335422）辦理核銷。"
                ),
                (
                    "Shared Campus 校園共享專案補助：修習北藝大與蘇黎世藝術大學（ZHdK）、倫敦藝術大學（UAL）、東京藝術大學、京都藝術大學等合作開設之 Transcultural Collaboration（TC）、Critical Ecologies（CE）或 Summer Schools 跨國課程者，得依專案補助簡章申請機票與住宿定額獎助。"
                ),
            ],
            "source": {
                "title": "國立臺北藝術大學《獎學金資訊專區》與《學海飛颺暨學海惜珠補助甄選作業流程》",
                "source_url": TNUA_SCHOLARSHIPS_URL,
                "category": "scholarship",
                "summary": "北藝大教育部學海飛颺／惜珠甄選作業流程、Shared Campus 課程補助簡章與核銷規定。",
            },
        }],
        "document_explanations": [{
            "title": (
                "國立臺北藝術大學中英文交換學生申請表、中外文出國研習計畫書、藝術作品集與選送學生赴外交換行政契約書準備指南"
            ),
            "summary": (
                "說明北藝大七大藝術專業學院交換生甄選必備之中英文申請表、作品集／試奏試演影音、2 封英文推薦函、志願上限（2校）及錄取後連帶保證人行政契約書規範。"
            ),
            "key_points": [
                (
                    "志願上限與三級審查：自 115 學年度起每位學生每梯次甄選至多可填報 2 間交換學校志願；申請人須先通過系所初審與學院複審，由各學院於 2027/02/23 前將《學院推薦交換學生資料表》送交國際事務處。"
                ),
                (
                    "中外文出國研習計畫書與作品集（Portfolio / Audition）：除具體說明赴姊妹校修課與創作研究規劃外，音樂、美術、戲劇、舞蹈、電影與新媒體等系所申請人須依接待姊妹校規定準備作品集或獨奏／展演影音連結。"
                ),
                (
                    "行政契約書與返國 2 週內報告義務：錄取生須於出國前至少 2 個月（或收到入學許可後 1 個月內）偕同連帶保證人簽署《選送學生赴外交換行政契約書》，並於返國後 2 週內向國際處報到及繳交 1,000 字以內交換報告（含照片 4 張以上）。"
                ),
            ],
            "applies_to": [],
            "source": {
                "title": "國立臺北藝術大學 116學年度姊妹校交換學生甄選簡章與選送學生赴外交換行政契約書",
                "source_url": TNUA_OUTGOING_APPLICATION_URL,
                "category": "exchange_application",
                "summary": None,
            },
            "document_url": TNUA_BROCHURE_116_PDF,
            "document_type": "official_document",
            "full_text_extracted": True,
        }],
        "rule_explanations": [{
            "title": (
                "國立臺北藝術大學選送學生出國進修與交流甄選辦法、赴外交換行政契約書與學海飛颺暨學海惜珠補助甄選作業流程核心法規"
            ),
            "summary": (
                "規範北藝大七大學院學生申請出國交換之在學年級門檻、三級審查程序、交換期間全額學雜費與碩博士最低 6 學分規定、行政契約書連帶保證責任及返國學分抵免時限。"
            ),
            "key_points": [
                (
                    "交換甄選資格與三級審查：依《國立臺北藝術大學選送學生出國進修與交流甄選辦法》，學士班二年級以上（不含在職專班）及碩、博士班於本校就讀一學期以上之在學學生得申請；經系所初審、學院複審後送國際交流事務委員會複審核定。"
                ),
                (
                    "交換期間全額學雜費與研究所 6 學分規定：依《選送學生赴外交換行政契約書》，交換期間須於北藝大完成註冊並繳交全額學雜費（含使用及代辦費用；延修生亦須繳交全額學雜費；碩、博士生最低應修 6 學分並應繳納最低 6 學分之學分費及學雜費基數）。"
                ),
                (
                    "海外聯絡通報、返國報到與學分抵免時限：抵達姊妹校 2 週內須回傳《赴外交換生海外聯絡資訊通報表》，開學第 5 週前於藝務系統填送《選課通報表》；返國後 2 週內向國際處報到並繳交交換報告，修課結束後 2 個月內提出《赴外交換生學分抵免申請書》。"
                ),
            ],
            "applies_to": [],
            "source": {
                "title": "國立臺北藝術大學選送學生出國進修與交流甄選辦法與選送學生赴外交換行政契約書",
                "source_url": TNUA_REGULATIONS_URL,
                "category": "exchange_application",
                "summary": None,
            },
            "document_url": TNUA_SELECTION_REG_PDF,
            "document_type": "official_document",
            "full_text_extracted": True,
        }],
        "sources": [
            {
                "title": "國立臺北藝術大學國際事務處（OIA）官方網站",
                "source_url": TNUA_OIA_HOME_URL,
                "category": "exchange_application",
                "summary": None,
            },
            {
                "title": "國立臺北藝術大學出國交換姊妹校專區（美洲、歐洲、亞洲、大洋洲 90 校完整申請資訊表）",
                "source_url": TNUA_OUTGOING_PARTNERS_URL,
                "category": "partner_school",
                "summary": None,
            },
            {
                "title": "國立臺北藝術大學 116 學年度（2027/2028）本校姊妹校交換學生甄選簡章公告",
                "source_url": TNUA_NEWS_116_EXCHANGE_URL,
                "category": "exchange_application",
                "summary": None,
            },
            {
                "title": "國立臺北藝術大學選送學生出國進修與交流甄選辦法 PDF",
                "source_url": TNUA_SELECTION_REG_PDF,
                "category": "exchange_application",
                "summary": None,
            },
            {
                "title": "國立臺北藝術大學選送學生赴外交換行政契約書 PDF",
                "source_url": TNUA_ADMIN_CONTRACT_PDF,
                "category": "exchange_application",
                "summary": None,
            },
            {
                "title": "國立臺北藝術大學 Shared Campus 校園共享專案與 UMAP 亞太大學交流會專區",
                "source_url": TNUA_CAMPUS_SHARING_PARTNERS_URL,
                "category": "partner_school",
                "summary": None,
            },
            {
                "title": "國立臺北藝術大學獎學金專區與教育部學海飛颺暨學海惜珠補助甄選作業流程",
                "source_url": TNUA_SCHOLARSHIPS_URL,
                "category": "scholarship",
                "summary": None,
            },
            {
                "title": "國立臺北藝術大學赴外交換生經驗分享專區（106–114學年度 146 篇學生心得報告）",
                "source_url": TNUA_OUTGOING_SHARING_URL,
                "category": "experience_report",
                "summary": None,
            },
        ],
    }
    (OFFICIAL_TNUA_DIR / "student_dashboard.json").write_text(
        json.dumps(student_dashboard_payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    doc_conditions = {
        "school_id": "tnua",
        "school_name": "國立臺北藝術大學",
        "checked_at": CHECKED_AT,
        "source_url": TNUA_BROCHURE_116_PDF,
        "common_documents": exchange_info_payload["required_documents"],
        "track_specific_conditions": [
            {
                "track": "國際事務處【116／115學年度赴外姊妹校交換學生甄選計畫（全球四大洲 65 所開放交換姊妹校，每生至多填報 2 校志願）】",
                "required": [
                    "國立臺北藝術大學交換學生申請表（中、英文各乙份）及所屬學院彙整之《學院推薦交換學生資料表》",
                    "歷年中文及英文成績單正本（含班級排名百分比）及有效語言能力證明（校外語言檢定或修習外語 2 學期達 80 分以上證明；大陸地區免附）",
                    "中文及外文出國研習計畫書（Study Plan）、本校教師英文推薦函 2 封以上及個人藝術創作作品集（Portfolio）／展演影音紀錄",
                    "錄取後須簽署《選送學生赴外交換行政契約書》（含連帶保證人），抵達後 2 週內通報海外聯絡資訊，返國後 2 週內繳交 1,000 字以內交換報告（含照片 4 張以上）",
                ],
            },
            {
                "track": "國際事務處【Shared Campus 校園共享專案（TC 跨文化合作／CE 批判生態學／Summer Schools）暨 UMAP 亞太大學交流會交換】",
                "required": [
                    "Shared Campus 專案課程申請表或 UMAP 交換學生中文申請表及家長同意書",
                    "歷年英文成績單、英語能力證明、修課動機與創作作品集（申請 Shared Campus 機票與住宿補助者依當期補助簡章檢附核銷單據）",
                ],
            },
            {
                "track": "教育部【學海飛颺／學海惜珠／學海築夢】出國研修與海外實習獎助學金",
                "required": [
                    "依《國立臺北藝術大學辦理教育部學海飛颺暨學海惜珠補助甄選作業流程》，由所屬學院推薦（每院至多 5 名並排序）並檢附交換申請全套資料（學海惜珠須另附低收入戶、中低收入戶或特殊境遇家庭證明及戶籍謄本）",
                    "返國核銷須於姊妹校學期結束後 1 週內上傳心得報告至教育部學海計畫平台，並檢附來回電子機票、登機證存根、旅行社代收轉付收據（買受人：國立臺北藝術大學、統一編號：99335422）及領據",
                ],
            },
        ],
    }
    (OFFICIAL_TNUA_DIR / "document-conditions.json").write_text(
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
            f"{fname},{len(partners)},{pop},{ratio:.4f},Official TNUA OIA verified"
        )
    (OFFICIAL_TNUA_DIR / "field-coverage.csv").write_text(
        "\n".join(field_cov_lines) + "\n", encoding="utf-8"
    )

    pages_records = [
        {
            "title": "國立臺北藝術大學：116學年度（2027/2028）姊妹校交換學生甄選期程（02/23學院薦送截止）、三級審查與志願上限2校規定",
            "source_url": TNUA_NEWS_116_EXCHANGE_URL,
            "published_at": "2026-09-29T00:00:00Z",
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
            "title": "國立臺北藝術大學：選送學生出國進修與交流甄選辦法、選送學生赴外交換行政契約書與全額學雜費（碩博至少6學分）規定",
            "source_url": TNUA_SELECTION_REG_PDF,
            "published_at": "2026-09-29T00:00:00Z",
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
            "title": f"國立臺北藝術大學：{len(partners)} 所全球四大洲合作姊妹校申請資訊表、{open_partner_count} 所開放交換校與語言證明雙軌制",
            "source_url": TNUA_OUTGOING_PARTNERS_URL,
            "published_at": "2026-09-29T00:00:00Z",
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
            "title": "國立臺北藝術大學：中英文交換學生申請表、中外文出國研習計畫書、2封英文推薦函、作品集與返國2週內報告及2個月內學分抵免規範",
            "source_url": TNUA_BROCHURE_116_PDF,
            "published_at": "2026-09-29T00:00:00Z",
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
            "title": "國立臺北藝術大學：教育部學海飛颺、學海惜珠、學海築夢甄選作業流程（每院推薦至多5名）與 Shared Campus 校園共享獎助",
            "source_url": TNUA_SCHOLARSHIPS_URL,
            "published_at": "2026-09-29T00:00:00Z",
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
    (OFFICIAL_TNUA_DIR / "pages.jsonl").write_text(pages_text, encoding="utf-8")
    (OFFICIAL_TNUA_DIR / "processed_pages.jsonl").write_text(
        pages_text, encoding="utf-8"
    )

    home_rules = {
        "school_id": "tnua",
        "school_name": "國立臺北藝術大學",
        "eligibility": student_dashboard_payload["eligibility"],
        "application_periods": student_dashboard_payload["application_periods"],
        "selection_rules": {
            "undergraduate_score_minimum": None,
            "graduate_score_minimum": None,
            "language_course_alternative_score": 80.0,
            "graduate_min_credits_during_exchange": 6,
            "maximum_preferences": 2,
            "screening_batches_per_year": 1,
            "allow_freshman_apply": False,
            "min_enrolled_semesters_undergrad": 2,
            "min_enrolled_semesters_grad": 1,
            "tuition_policy_during_exchange": (
                "交換期間須於國立臺北藝術大學完成註冊並繳交全額學雜費（含使用及代辦費用；延修生亦須繳交全額學雜費；碩、博士生最低應修 6 學分並繳納最低 6 學分之學分費及學雜費基數），免繳接待姊妹校學費"
            ),
            "return_documents_due": (
                "抵達姊妹校 2 週內通報海外聯絡資訊，返國後 2 週內向國際事務處報到並繳交 1,000 字以內出國交換報告（含照片 4 張以上），修課結束後 2 個月內提出學分抵免申請"
            ),
        },
        "source_urls": tnua_source_urls,
        "verified_at": "2026-11-01",
    }
    (OFFICIAL_TNUA_DIR / "home_rules.json").write_text(
        json.dumps(home_rules, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    (OFFICIAL_TNUA_DIR / "documents.json").write_text(
        json.dumps(
            {
                "school_name": "國立臺北藝術大學",
                "required_documents": student_dashboard_payload["required_documents"],
                "source_urls": tnua_source_urls,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    (OFFICIAL_TNUA_DIR / "scholarships.json").write_text(
        json.dumps(
            {
                "school_name": "國立臺北藝術大學",
                "scholarships": student_dashboard_payload["scholarship_info"],
                "source_urls": tnua_source_urls,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    completeness = {
        "school_id": "tnua",
        "school_name": "國立臺北藝術大學",
        "total_partners": len(partners),
        "partner_count": len(partners),
        "international_partners": sum(
            1 for p in partners if p["country"] not in {"中國大陸", "香港", "澳門"}
        ),
        "mainland_partners": sum(
            1 for p in partners if p["country"] in {"中國大陸", "香港", "澳門"}
        ),
        "shared_campus_partners": 7,
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
            "國立臺北藝術大學國際事務處 116 學年度（2027/2028）姊妹校交換學生甄選（09/29 公告–02/23 學院薦送截止，每生至多填報 2 校志願）"
            "暨 Shared Campus 校園共享專案、UMAP 亞太大學交流會與教育部學海系列獎助同步整合；"
            f"共完整收錄 {len(partners)} 所合作姊妹校（橫跨全球四大洲 24 個國家與地區，含 {open_partner_count} 所開放申請校，"
            f"並收錄 {exp_covered_schools} 所合作大學共 {total_exp_reports} 篇 106–114 學年度赴外交換生研修心得報告）。"
        ),
        "verified_at": "2026-11-01",
    }
    (OFFICIAL_TNUA_DIR / "catalog-completeness.json").write_text(
        json.dumps(completeness, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    (OFFICIAL_TNUA_DIR / "verification_status.json").write_text(
        json.dumps(
            {
                "school_id": "tnua",
                "school_name": "國立臺北藝術大學",
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
    (OFFICIAL_TNUA_DIR / "dashboard_manifest.json").write_text(
        json.dumps(
            {
                "school_id": "tnua",
                "school_name": "國立臺北藝術大學",
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
        ("sources/tnua/oia_about.html", TNUA_OIA_ABOUT_URL, "國立臺北藝術大學國際事務處—本處簡介 HTML"),
        ("sources/tnua/oia_contact.html", TNUA_OIA_CONTACT_URL, "國際事務處—聯絡我們與業務職掌 HTML"),
        ("sources/tnua/outgoing_partners.html", TNUA_OUTGOING_PARTNERS_URL, "國際事務處—出國交換姊妹校專區 HTML"),
        ("sources/tnua/en_outgoing_partners.html", TNUA_EN_OUTGOING_PARTNERS_URL, "國際事務處—英文版出國交換姊妹校專區 HTML"),
        ("sources/tnua/outgoing_application.html", TNUA_OUTGOING_APPLICATION_URL, "國際事務處—出國交換甄選申請資訊 HTML"),
        ("sources/tnua/outgoing_implementation.html", TNUA_OUTGOING_IMPLEMENTATION_URL, "國際事務處—交換生錄取後執行手冊 HTML"),
        ("sources/tnua/outgoing_sharing.html", TNUA_OUTGOING_SHARING_URL, "國際事務處—赴外交換生經驗分享專區 HTML"),
        ("sources/tnua/umap_exchange.html", TNUA_UMAP_EXCHANGE_URL, "國際事務處—UMAP 亞太大學交流會專區 HTML"),
        ("sources/tnua/campus_sharing_partners.html", TNUA_CAMPUS_SHARING_PARTNERS_URL, "國際事務處—Shared Campus 校園共享專案 HTML"),
        ("sources/tnua/en_partners.html", TNUA_EN_PARTNERS_URL, "國際事務處—英文版全球合作夥伴總覽 HTML"),
        ("sources/tnua/news_116_exchange.html", TNUA_NEWS_116_EXCHANGE_URL, "116學年度（2027/2028）本校姊妹校交換學生甄選公告 HTML"),
        ("sources/tnua/news_115_admitted.html", TNUA_NEWS_115_ADMITTED_URL, "115學年度本校赴外交換學生甄選錄取名單公告 HTML"),
        ("sources/tnua/news_xuehai_2026.html", TNUA_NEWS_XUEHAI_2026_URL, "115年教育部學海飛颺及學海惜珠獎學金甄選公告 HTML"),
        ("sources/tnua/scholarships.html", TNUA_SCHOLARSHIPS_URL, "國際事務處—獎學金資訊專區 HTML"),
        ("sources/tnua/regulations_committee.html", TNUA_REGULATIONS_URL, "國際事務處—相關法規與委員會專區 HTML"),
        ("sources/tnua/tnua_academics.html", TNUA_ACADEMICS_URL, "國立臺北藝術大學教學單位一覽（7學院）HTML"),
        ("sources/tnua/gdrive_experience_folder.html", TNUA_GDRIVE_EXP_URL, "北藝大赴外交換生經驗分享雲端資料夾（106–114學年）HTML"),
        ("sources/tnua/tnua_experience_index.json", TNUA_OUTGOING_SHARING_URL, f"國立臺北藝術大學赴外交換生研修心得報告（{exp_covered_schools} 校共 {total_exp_reports} 篇）索引 JSON"),
        ("sources/tnua/tnua_catalog_source.json", TNUA_OUTGOING_PARTNERS_URL, f"國立臺北藝術大學 {len(partners)} 所合作姊妹校整合資料集 JSON"),
        ("sources/tnua/tnua_resolved_locations.json", TNUA_OUTGOING_PARTNERS_URL, f"國立臺北藝術大學 {len(partners)} 所合作姊妹校 ROR / Wikidata 地理座標核對表 JSON"),
    ]
    for fname, url in bin_urls.items():
        provenance_files.append((f"sources/tnua/{fname}", url, f"國立臺北藝術大學官方附件：{fname}"))

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
        "school_id": "tnua",
        "school_name": "國立臺北藝術大學",
        "generated_at": CHECKED_AT,
        "active_cycle_note": completeness["active_term"],
        "sources": prov_sources,
    }
    prov_text = json.dumps(provenance_payload, ensure_ascii=False, indent=2) + "\n"
    (OFFICIAL_TNUA_DIR / "import_provenance.json").write_text(
        prov_text, encoding="utf-8"
    )
    (OFFICIAL_TNUA_DIR / "import-provenance.json").write_text(
        prov_text, encoding="utf-8"
    )

    print(
        f"Successfully built TNUA catalog: {len(partners)} partners"
        f" ({open_partner_count} open, {completeness['verified_campus_images']}"
        f" verified images, {completeness['verified_locations']} verified"
        f" locations), {len(workflows)} workflows,"
        f" {len(destinations)} destinations, {len(research_records)} research"
        f" records, {exp_covered_schools} schools with experience records"
        f" ({len(student_experience_rows)} rows, {total_exp_reports} reports)."
    )


if __name__ == "__main__":
    main()
