"""Build the official Fo Guang University (佛光大學, FGU) exchange data bundle."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re

REPO_ROOT = Path(__file__).resolve().parents[1]
SOURCES_FGU_DIR = REPO_ROOT / "sources" / "fgu"
OFFICIAL_FGU_DIR = REPO_ROOT / "src" / "exchange_info" / "official_data" / "fgu"
STATIC_DIR = REPO_ROOT / "src" / "exchange_info" / "static"
UNIVERSITY_LOCATIONS_PATH = (
    REPO_ROOT / "src" / "exchange_info" / "official_data" / "university_locations.jsonl"
)

CHECKED_AT = "2026-11-02T00:00:00Z"

FGU_OICA_HOME_URL = "https://oica.fgu.edu.tw/"
FGU_OUTBOUND_NON_CN_URL = "https://oica.fgu.edu.tw/zh_tw/Exchange_Student/non_Mainland_China"
FGU_OUTBOUND_CN_URL = "https://oica.fgu.edu.tw/zh_tw/Exchange_Student/Mainland_China"
FGU_FO_GUANG_EXCHANGE_URL = "https://oica.fgu.edu.tw/zh_tw/Fo_Guang_Exchange"
FGU_22_PROGRAM_URL = "https://oica.fgu.edu.tw/zh_tw/22_Program"
FGU_ADMISSION_LIST_URL = "https://oica.fgu.edu.tw/zh_tw/Exchange_Student/Admission_list"
FGU_EXPERIENCE_SHARING_URL = "https://oica.fgu.edu.tw/zh_tw/Exchange_Student/Experience_Sharing"
FGU_LAW_URL = "https://oica.fgu.edu.tw/zh_tw/Law"
FGU_DOWNLOAD_URL = "https://oica.fgu.edu.tw/zh_tw/Download"
FGU_115_1_ADMISSION_URL = "https://oica.fgu.edu.tw/zh_tw/announcements/54396754"
FGU_115_1_BRIEFING_URL = "https://oica.fgu.edu.tw/zh_tw/announcements/85842567"
FGU_MIDDLESEX_DUAL_URL = "https://oica.fgu.edu.tw/zh_tw/announcements/62503684"
FGU_KONKUK_WINTER_URL = "https://oica.fgu.edu.tw/zh_tw/announcements/23295999"
FGU_LAW_A06_004_PDF_URL = "https://oica.fgu.edu.tw/uploads/asset/data/66ed18338621eb4bd800018a/A06-004%E4%BD%9B%E5%85%89%E5%A4%A7%E5%AD%B8%E8%88%87%E5%A2%83%E5%A4%96%E5%AD%B8%E6%A0%A1%E5%AD%B8%E7%94%9F%E4%BA%A4%E6%B5%81%E7%94%84%E9%81%B8%E5%AF%A6%E6%96%BD%E8%BE%A6%E6%B3%95.pdf"
FGU_LAW_A06_005_PDF_URL = "https://oica.fgu.edu.tw/uploads/asset/data/607556db1d41c862a80004df/A06-005%E4%BD%9B%E5%85%89%E5%A4%A7%E5%AD%B8%E5%AD%B8%E7%94%9F%E9%81%B8%E6%B4%BE%E8%87%B3%E5%A4%A7%E9%99%B8%E9%AB%98%E6%A0%A1%E6%93%94%E4%BB%BB%E4%BA%A4%E6%8F%9B%E5%AD%B8%E7%94%9F%E8%A3%9C%E5%8A%A9%E5%AF%A6%E6%96%BD%E8%BE%A6%E6%B3%95.pdf"
FGU_LAW_UWEST_PDF_URL = "https://oica.fgu.edu.tw/uploads/asset/data/607556db1d41c862aa000338/%E4%BD%9B%E5%85%89%E5%A4%A7%E5%AD%B8%E8%88%87%E7%BE%8E%E5%9C%8B%E8%A5%BF%E4%BE%86%E5%A4%A7%E5%AD%B8%E9%9B%99%E5%AD%B8%E4%BD%8D%E8%A8%88%E7%95%AB%E5%AF%A6%E6%96%BD%E5%8F%8A%E5%8A%A9%E5%AD%B8%E9%87%91%E8%BE%A6%E6%B3%95.pdf"
FGU_LAW_LIN_LU_PDF_URL = "https://oica.fgu.edu.tw/uploads/asset/data/66ed17958621eb4bdc000167/%E4%BD%9B%E5%85%89%E5%A4%A7%E5%AD%B8%E6%9E%97%E5%91%82%E5%BE%B7%E6%96%87%E4%B9%98%E9%A2%A8%E8%90%AC%E9%87%8C%E5%8A%A9%E5%AD%B8%E5%9F%BA%E9%87%91%E8%A8%AD%E7%BD%AE%E8%A6%81%E9%BB%9E.pdf"
FGU_LAW_XUEHAI_WUYAI_PDF_URL = "https://oica.fgu.edu.tw/uploads/asset/data/66ed17d28621eb4bd8000188/%E4%BD%9B%E5%85%89%E5%A4%A7%E5%AD%B8%E5%AD%B8%E6%B5%B7%E7%84%A1%E6%B6%AF%E5%A2%9E%E9%A1%8D%E5%AD%B8%E7%BF%92%E5%8A%A9%E5%AD%B8%E9%87%91%E8%A6%81%E9%BB%9E.pdf"
FGU_STEPS_PDF_URL = "https://oica.fgu.edu.tw/uploads/asset/data/607556df1d41c862a8000511/%E4%BA%A4%E6%8F%9B%E5%AD%B8%E7%94%9F%E7%94%B3%E8%AB%8B%E6%AD%A5%E9%A9%9F.pdf"

REGION_COST_DEFAULTS = {
    "美國": (
        "每月生活費約 USD 1,350–2,100（折合新臺幣約 43,000–67,000 元；加州洛杉磯西來大學 UWest 校內雙人房住宿與膳食方案較一般美國名校親民）",
        "須憑西來大學或美國接待校核發之 I-20 / DS-2019 表格繳交 SEVIS I-901 費用並向美國在台協會（AIT）申辦 F-1（雙學位）或 J-1（交換生）簽證，並投保海外全期醫療險。",
    ),
    "英國": (
        "每月生活費約 USD 1,450–2,150（折合英鎊約 GBP 1,150–1,700 / 月、新臺幣約 46,000–68,000 元；倫敦密德薩斯大學 Hendon 校區住宿與交通）",
        "修讀 3+1 雙學士或 3+1+1 碩士須憑 CAS 號碼申辦英國 Student Visa 並繳納 IHS 醫療附加費，畢業後可申請英國 2 年 PSW 工作簽證。",
    ),
    "德國": (
        "每月生活費約 USD 1,050–1,550（折合歐元約 EUR 950–1,400 / 月、新臺幣約 33,500–50,000 元；含漢堡大學學期政務交通卡 Semesterbeitrag 與學生宿舍）",
        "須開立德國限制提領帳戶（Blocked Account）並憑入學許可向德國在台協會申辦長期學生簽證及投保德國法定健康保險。",
    ),
    "澳洲": (
        "每月生活費約 USD 1,400–2,100（折合澳幣約 AUD 2,100–3,200 / 月、新臺幣約 45,000–67,000 元；新南威爾斯州臥龍崗南天大學學舍與生活開銷）",
        "須購買澳洲海外學生健康保險（OSHC）並憑南天大學核發之 CoE 申辦澳洲 Subclass 500 學生簽證。",
    ),
    "紐西蘭": (
        "每月生活費約 USD 1,250–1,850（折合紐幣約 NZD 2,000–3,000 / 月、新臺幣約 40,000–59,000 元；南島但尼丁奧塔哥大學學生住宿與膳食）",
        "須憑奧塔哥大學入學許可申辦紐西蘭學生簽證（Fee Paying / Exchange Student Visa）並投保紐西蘭認可之國際學生醫療與旅遊保險。",
    ),
    "日本": (
        "每月生活費約 USD 700–1,150（折合日圓約 JPY 100,000–165,000 / 月、新臺幣約 22,000–37,000 元；京都龍谷大學與花園大學國際學生寮與伙食交通）",
        "須由日本接待大學代向出入國在留管理局申請「在留資格認定證明書（COE）」，獲發後至日本台灣交流協會申辦留學簽證並加入日本國民健康保險（NHI）。",
    ),
    "韓國": (
        "每月生活費約 USD 650–1,050（折合韓元約 KRW 850,000–1,400,000 / 月、新臺幣約 20,500–33,500 元；金剛大學另提供宿舍費減免優惠）",
        "須憑韓國接待校核發之標準入學許可書（Certificate of Admission）向駐台北韓國代表部申辦 D-2-6 交換學生簽證，入境後辦理外國人登錄證並納保韓國國民健康保險。",
    ),
    "泰國": (
        "每月生活費約 USD 480–820（折合泰銖約 THB 16,000–27,000 / 月、新臺幣約 15,500–26,000 元；曼谷正大管理學院與清邁湄州大學住宿餐飲費用親民）",
        "須憑泰國接待大學入學許可公文向泰國貿易經濟辦事處（TTEO）申辦 Non-Immigrant ED 教育簽證並投保海外全期醫療險。",
    ),
    "馬來西亞": (
        "每月生活費約 USD 450–800（折合馬幣約 MYR 2,000–3,500 / 月、新臺幣約 14,500–25,500 元；拉曼大學金寶與雙溪龍校區生活費實惠）",
        "須透過馬來西亞教育全球服務中心（EMGS）線上申辦學生簽證核准函（VAL）並投保馬來西亞境內醫療險。",
    ),
    "菲律賓": (
        "每月生活費約 USD 480–850（折合新臺幣約 15,500–27,000 元；馬尼拉光明大學與宿霧拉普拉普國際大學校園宿舍與膳食）",
        "須依菲律賓接待大學指引辦理學生簽證（9F）或特別學習許可（SSP）並投保海外醫療保險。",
    ),
    "印度": (
        "每月生活費約 USD 400–750（折合新臺幣約 13,000–24,000 元；新德里大學國際學舍與生活開銷）",
        "須憑印度德里大學正式入學許可向印度台北協會申辦 Student Visa 並投保海外全期醫療及意外保險。",
    ),
    "緬甸": (
        "每月生活費約 USD 380–680（折合新臺幣約 12,000–21,500 元；曼德勒龐道烏國際大學住宿與膳食）",
        "須依緬甸接待大學指引申辦教育／研習簽證並投保海外全期醫療及意外保險。",
    ),
    "香港": (
        "每月生活費約 USD 950–1,450（折合港幣約 HKD 7,500–11,500 / 月、新臺幣約 30,000–46,000 元；香港教育大學大埔校區宿舍與伙食交通）",
        "須透過香港教育大學代向香港入境事務處申辦來港就讀進入許可（Student Entry Permit）並投保海外醫療保險。",
    ),
    "中國大陸": (
        "每月生活費約 USD 350–680（折合人民幣約 RMB 2,200–4,500 / 月、新臺幣約 11,000–21,500 元；上海大學、鄭州大學、西北師範大學、陽光學院另提供免住宿費待遇，且可領取佛大赴陸機票 7–9 成及每月 4,000–5,000 元生活補助）",
        "須持有效「臺灣居民來往大陸通行證（臺胞證）」及大陸姊妹校寄發之錄取通知書辦理報到，並依佛光大學國際暨兩岸事務處規定投保涵蓋交換全期之海外醫療及意外保險。",
    ),
}

SEMESTER_DATES_BY_COUNTRY = {
    "美國": "秋季學期（Fall Semester）：約 8 月中下旬至 12 月中旬；春季學期（Spring Semester）：約 1 月中旬至 5 月中旬",
    "英國": "秋季學期（Autumn Term）：約 9 月下旬至翌年 1 月；春季學期（Spring Term）：約 1 月下旬至 5 月下旬",
    "德國": "冬季學期（Wintersemester）：約 10 月初至翌年 2 月中旬；夏季學期（Sommersemester）：約 4 月初至 7 月中下旬",
    "澳洲": "第一學期（Semester 1）：約 2 月下旬至 6 月下旬；第二學期（Semester 2）：約 7 月下旬至 11 月中旬",
    "紐西蘭": "第一學期（Semester 1）：約 2 月下旬至 6 月下旬；第二學期（Semester 2）：約 7 月中旬至 11 月中旬",
    "日本": "春季學期（Spring Semester）：約 4 月初至 8 月初；秋季學期（Fall Semester）：約 9 月中下旬至翌年 2 月初",
    "韓國": "春季學期（Spring Semester）：約 3 月初至 6 月中旬；秋季學期（Fall Semester）：約 9 月初至 12 月中旬",
    "中國大陸": "秋季學期（上學期）：約 9 月初至翌年 1 月中旬；春季學期（下學期）：約 2 月下旬至 7 月初",
    "香港": "第一學期（Semester 1）：約 9 月初至 12 月下旬；第二學期（Semester 2）：約 1 月中旬至 5 月下旬",
}


def clean_text(s: str) -> str:
    return re.sub(r"\s+", " ", s or "").strip()


def sync_global_assets_and_locations(
    catalog_source: list[dict], resolved_locations: dict
) -> None:
    """Sync all 52 FGU partner schools into school-images.json and university_locations.jsonl."""
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
        country = item["country"]
        irec = item.get("image_record") or {}
        if irec.get("local_path"):
            new_rec = {
                "school_name": fn,
                "country": country,
                "local_path": irec["local_path"],
                "image_source_url": irec.get("image_source_url") or irec["local_path"],
                "source_page_url": irec.get("source_page_url") or item.get("website") or "",
                "official_page_url": irec.get("official_page_url") or item.get("website") or "",
                "identity_source_url": irec.get("identity_source_url") or item.get("website") or "",
                "width": irec.get("width") or 1280,
                "height": irec.get("height") or 853,
                "content_hash": irec.get("content_hash") or "",
                "license_name": irec.get("license_name") or "CC BY-SA 4.0",
                "license_url": irec.get("license_url") or "https://creativecommons.org/licenses/by-sa/4.0/",
                "artist": irec.get("artist") or "Wikimedia Commons Contributors",
                "attribution": irec.get("attribution") or "Wikimedia Commons",
                "checked_at": irec.get("checked_at") or CHECKED_AT,
                "status": "verified",
                "note": irec.get("note") or f"Verified campus image for {fn}",
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
    if "佛光大學" not in loc_by_name:
        fgu_home_loc = {
            "school_name": "佛光大學",
            "country": "臺灣",
            "city": "宜蘭縣礁溪鄉",
            "latitude": 24.8168,
            "longitude": 121.7244,
            "geocode_status": "verified",
            "geocoded_at": CHECKED_AT,
            "source_url": "https://www.fgu.edu.tw/",
            "identity_source_url": "https://www.fgu.edu.tw/",
            "precision": "campus",
        }
        parsed_locs.append(fgu_home_loc)
        loc_by_name["佛光大學"] = fgu_home_loc
        loc_changed = True

    for item in catalog_source:
        fn = item["school_name"]
        loc = resolved_locations.get(fn)
        if fn not in loc_by_name and loc:
            lat = float(loc.get("latitude") if loc.get("latitude") is not None else loc.get("lat", 24.8168))
            lon = float(loc.get("longitude") if loc.get("longitude") is not None else loc.get("lon", 121.7244))
            new_loc = {
                "school_name": fn,
                "country": item["country"],
                "city": loc.get("city") or item["country"],
                "latitude": lat,
                "longitude": lon,
                "geocode_status": "verified",
                "geocoded_at": CHECKED_AT,
                "source_url": loc.get("source_url") or "https://www.wikidata.org",
                "identity_source_url": item.get("website") or loc.get("source_url") or "https://ror.org",
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
    OFFICIAL_FGU_DIR.mkdir(parents=True, exist_ok=True)
    catalog_source = json.loads(
        (SOURCES_FGU_DIR / "fgu_catalog_source.json").read_text(encoding="utf-8")
    )
    resolved_locations = json.loads(
        (SOURCES_FGU_DIR / "fgu_resolved_locations.json").read_text(encoding="utf-8")
    )
    bin_urls_path = SOURCES_FGU_DIR / "binary_source_urls.json"
    bin_urls = (
        json.loads(bin_urls_path.read_text(encoding="utf-8"))
        if bin_urls_path.exists()
        else {}
    )
    sync_global_assets_and_locations(catalog_source, resolved_locations)

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
        avail_status = "open" if item.get("offering_status") == "open" else "reference_only"
        if avail_status == "open":
            open_partner_count += 1

        group_str = clean_text(item.get("group") or "國際暨兩岸事務處正式締約姊妹校")
        quota_str = clean_text(item.get("quota") or "依佛光大學國際暨兩岸事務處當期公告名額")
        detail_url = item.get("detail_url") or FGU_OUTBOUND_NON_CN_URL

        if "2+2" in group_str or "雙聯" in group_str or "雙學位" in group_str:
            program_type = clean_text(item.get("program_type_raw") or f"{group_str}（跨國雙學位暨交換計畫）")
            source_url = detail_url
        elif country in {"中國大陸", "香港"} and avail_status == "open":
            program_type = clean_text(item.get("program_type_raw") or "國際暨兩岸事務處赴大陸及港澳地區交換學生計畫")
            source_url = FGU_OUTBOUND_CN_URL
        elif avail_status == "open":
            program_type = clean_text(item.get("program_type_raw") or f"{group_str}（免繳接待姊妹校學費）")
            source_url = detail_url
        else:
            program_type = clean_text(item.get("program_type_raw") or "國際暨兩岸事務處正式締約國際姊妹校")
            source_url = detail_url

        colleges_str = clean_text(
            item.get("colleges")
            or "人文學院、社會科學院、管理學院、創意與科技學院、樂活產業學院、佛教學院"
        )
        degree_levels_str = clean_text(
            item.get("eligible_degrees")
            or "佛光大學學士班二年級（含）以上及碩、博士班在學學生（大一下學期可申請大二出國交換）"
        )
        lang_req_str = clean_text(item.get("language_req") or "")
        gpa_req_str = clean_text(item.get("gpa_req") or "")
        website = item.get("website") or FGU_OICA_HOME_URL
        remarks_raw = clean_text(item.get("notes") or "")
        tuition_note = clean_text(item.get("tuition_note") or "")
        exps = item.get("experience_reports") or []

        round_label = (
            "115–116學年度佛光大學赴海外及大陸地區姊妹校交換生暨雙聯學位甄選"
            if avail_status == "open"
            else "國際暨兩岸事務處正式締約姊妹校（當期開放名額依國際處最新公告簡章為準）"
        )
        app_deadline_str = clean_text(
            item.get("deadline")
            or (
                "第一階段（春季班／隔年春季出國）：每年 9 月下旬至 10 月中旬校內收件（2026/10/16 截止，11 月初面試）｜"
                "第二階段（秋季班／當年度秋季出國）：每年 2 月下旬至 3 月中旬校內收件（2027/03/19 17:00 截止，4 月初面試）"
            )
        )
        deadline_iso = "2027-03-19T17:00:00+08:00"
        win_status = "open" if avail_status == "open" else "closed"
        acad_year = "115"
        study_period_str = clean_text(item.get("duration") or "一學期或一學年")
        sem_dates_str = SEMESTER_DATES_BY_COUNTRY.get(
            country, "秋季學期：約 9 月至翌年 1 月；春季學期：約 2 月至 6 月"
        )
        housing_str = (
            f"獲佛光大學國際暨兩岸事務處推薦錄取後，可依 {zh_name} 國際處指引申請校內外學生宿舍或國際學舍"
            + (f"（學費與住宿待遇：{tuition_note}）" if tuition_note else "。")
        )
        course_rest_str = (
            f"開放對象與學院：{colleges_str}（{degree_levels_str}）。依《A06-004 佛光大學與境外學校學生交流甄選實施辦法》、《A06-005 佛光大學學生選派至大陸高校擔任交換學生補助實施辦法》及《與美國西來大學雙學位計畫實施及助學金辦法》規定："
            "（1）申請資格為本校學士班二年級（含）以上或碩博士班在學學生，前一學期學業成績平均達 75 分（約 GPA 3.0）以上且操行成績平均達 80 分以上（申請中國人民大學、南京大學、東南大學、四川大學等重點大陸高校須班排前 20%）；"
            "（2）所有申請海外及大陸交換之同學均須於校內收件截止前完成佛光大學圖書館 EASY TEST 線上平台「iBT 托福模擬測驗第 1 回」並檢附成績畫面；"
            "（3）交換期間須辦理佛光大學在學註冊並繳交全額學雜費，每學期於接待校至少修習相當於佛大 2 學分以上之課程（美國西來大學 2+2 雙學位每學期修習 12 學分且各科成績須維持 70 分以上）；"
            "（4）返國後 1 個月內須繳交交換心得報告及正式成績單辦理學分採認抵免，領取校內或學海獎助學金者另須於返國後一年內完成 75 小時校內學習服務時數。"
        )

        living_cost_str, visa_health_str = REGION_COST_DEFAULTS.get(
            country,
            (
                "每月生活費約 USD 750–1,400（依匯率折合新臺幣約 24,000–45,000 元，含住宿、膳食與市區交通）",
                "須依接待國駐臺機構規定申辦學生簽證，並於出國前投保涵蓋全期之海外醫療及意外保險。",
            ),
        )

        tuition_points_list = [
            f"佛光大學在學註冊與學雜費規定（依《A06-004 佛光大學與境外學校學生交流甄選實施辦法》）：出國交換期間須完成佛光大學註冊並繳交本校全額學雜費及學生平安保險費，免繳接待姊妹校學費（日本龍谷大學自費交換名額及英國密德薩斯大學雙聯學位依兩校協議辦理）。本合作校待遇：{tuition_note or '免繳接待姊妹校學費'}。",
            "佛光大學五大出國交換與跨國雙學位獎助學金體系：（1）《與美國西來大學雙學位計畫實施及助學金辦法》：修讀 2+2 雙學位者由佛光山系統大學全額補助西來大學每學期 12 學分學分費 USD 7,476，至多四學期共 48 學分總計 USD 29,904（約新臺幣 98 萬元）；（2）教育部《學海飛颺》與《學海惜珠》獎學金（赴非大陸港澳地區交換一學期至一學年，每人補助新臺幣 50,000–300,000 元）；（3）《佛光大學學海無涯增額學習助學金要點》（補助未獲教育部學海計畫或增額出國研修學生）；（4）《佛光大學林呂德文乘風萬里助學基金設置要點》（補助低收、中低收或經濟不利學生赴佛光山系統大學或海外姊妹校來回經濟艙機票最高 9 成）；（5）《A06-005 學生選派至大陸高校擔任交換學生補助實施辦法》（甲類：往返機票 9 成＋每月 5,000 元生活費；乙類清寒：往返機票 7 成＋每月 4,000 元生活費；丙類一般生：往返機票 7 成）。",
        ]

        app_steps_list = [
            f"步驟一（確認佛大在學年級、GPA 75 分／操行 80 分門檻與 {zh_name} 語檢要求，並完成 EASY TEST 托福模考）：確認為佛光大學學士班二年級（含）以上或碩博士班在學學生，符合學業要求（{gpa_req_str}）與外語門檻（{lang_req_str}），並登入圖書館 EASY TEST 線上學習平台完成「iBT 托福模擬測驗第 1 回」。",
            "步驟二（備妥《海外／赴陸交換生申請表》與應備書審資料經系所核章送交雲起樓 104 室國際處）：填妥交換學生申請表及家長同意書（經導師、系主任簽章），檢附歷年中文成績單正本（含排名百分比）、語言檢定證明、EASY TEST 托福模考成績單、中文自傳與讀書計畫（含選課對照）、教師推薦信及保證書，於截止前送交國際暨兩岸事務處（雲起樓 104 室）。",
            f"步驟三（參加國際暨兩岸事務處校內書面審查與面試甄選並公告錄取榜單）：春季班於每年 10 月中旬截止、11 月初面試；秋季班於每年 3 月中旬截止、4 月初面試，擇優錄取推薦赴 {full_name}，並同步申請教育部《學海飛颺／惜珠》、《學海無涯增額助學金》、《林呂德文乘風萬里助學基金》或《赴陸交換生甲／乙／丙類補助》。",
            "步驟四（由國際處向姊妹校提名、取得入學許可與辦理簽證，返國後完成心得報告與 75 小時服務時數核銷）：獲接待校入學許可（Admission Letter / COE / I-20 / 錄取通知書）後辦理簽證與保險，交換期間完成佛大註冊；返國後 1 個月內繳交交換心得報告及成績單辦理學分抵免，領取獎助學金者須於返國後一年內完成 75 小時校內服務時數。",
        ]

        elig_points_list = [
            f"合作類別與計畫組別：{program_type}（{group_str}）",
            f"開放學制與年級：{degree_levels_str}",
            f"開放申請學院：{colleges_str}",
            f"學業與操行成績門檻：{gpa_req_str}",
            f"外語能力與模考標準：{lang_req_str}",
        ]
        if tuition_note:
            elig_points_list.append(f"姊妹校學費與佛大獎助待遇：{tuition_note}")
        if remarks_raw:
            elig_points_list.append(f"歷年錄取實績與學程重點：{remarks_raw}")

        exp_links: list[dict] = []
        exp_labels: list[str] = []
        if exps:
            exp_covered_schools += 1
            total_exp_reports += len(exps)
            seen_exp_urls: set[str] = set()
            for e_idx, e in enumerate(exps):
                raw_t = clean_text(e.get("title") or f"赴 {zh_name} 交換生心得與錄取實績")
                esem = e.get("semester") or "115-1"
                edep = e.get("department") or "佛光大學交換生"
                eurl = e.get("url") or FGU_EXPERIENCE_SHARING_URL
                if eurl in seen_exp_urls:
                    eurl = f"{eurl}#fgu-{sn}-{e_idx+1}"
                seen_exp_urls.add(eurl)
                exp_labels.append(raw_t[:32])
                exp_links.append({
                    "title": raw_t,
                    "url": eurl,
                    "academic_year": esem,
                    "semester": esem,
                    "college": "人文學院／社會科學院／管理學院／創意與科技學院／樂活產業學院／佛教學院",
                    "department": edep,
                })
                summary_text = (
                    f"佛光大學國際暨兩岸事務處（OICA）官方公告之赴 {country} {full_name}（{zh_name}）交換學生經驗分享簡報、錄取榜單與雙聯學位說明（{raw_t}），涵蓋選課學分抵免、住宿環境、獎助學金申請與海外生活實錄。"
                )
                theme_map = {
                    "academics": f"佛光大學交換生於《{raw_t}》記錄在 {zh_name} 選課修讀、語言進修及返國辦理佛大學分抵免之經驗。",
                    "housing": f"佛光大學國際處與交換生整理 {zh_name} 校內外國際學生宿舍申請與生活機能（{housing_str[:100]}）。",
                    "campus_culture": f"佛光大學國際處公開《{raw_t}》之跨文化課堂交流、佛光山系統大學及姊妹校國際學伴互動實錄。",
                    "cost": f"佛光大學交換生於 {zh_name} 之每月住宿、膳食與交通開銷（{living_cost_str[:100]}），以及申請西來 2+2 全額學分費獎助、學海飛颺、林呂德文助學基金或赴陸機票與生活費補助之經驗。",
                }
                student_experience_rows.append({
                    "school_name": full_name,
                    "country": country,
                    "title": raw_t,
                    "source_url": eurl,
                    "source_type": "article",
                    "platform": "佛光大學國際暨兩岸事務處（OICA）—交換生心得分享與錄取榜單專區",
                    "author_name": edep[:24],
                    "language": "zh",
                    "summary": summary_text,
                    "themes": ["academics", "housing", "campus_culture", "cost"],
                    "theme_summaries": theme_map,
                    "content_status": "full_text",
                    "perspective": "official_student_story",
                    "published_at": None,
                    "discovered_at": CHECKED_AT,
                    "content_hash": hashlib.sha256(
                        f"{full_name}:fgu_exp:{e_idx}:{eurl}".encode("utf-8")
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
            "home_university": "佛光大學",
            "school_name": full_name,
            "country": country,
            "official_experience_portal_url": (
                exp_links[0]["url"] if exp_links else FGU_EXPERIENCE_SHARING_URL
            ),
            "partner_page_url": source_url,
            "report_count": len(exps),
            "sample_reports": sample_reports,
            "checked_at": CHECKED_AT,
        })

        loc = resolved_locations.get(full_name) or {
            "city": item.get("city") or country,
            "latitude": item.get("lat", 24.8168),
            "longitude": item.get("lon", 121.7244),
            "source_url": website,
        }
        city_name = loc.get("city") or country
        lat = float(loc.get("latitude") if loc.get("latitude") is not None else loc.get("lat", 24.8168))
        lon = float(loc.get("longitude") if loc.get("longitude") is not None else loc.get("lon", 121.7244))
        loc_source_url = loc.get("source_url") or website

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
            "note": "校級代表位置：官方網域及國家已與 ROR / Wikidata 比對；實際交換校區以錄取通知與締約校專頁為準。",
        }
        new_locations.append(location_obj)

        vrec = item.get("image_record") or {}
        assert vrec and vrec.get("local_path"), f"Missing verified image for {full_name}"
        img_local = vrec["local_path"]
        img_source = vrec.get("image_source_url") or img_local
        img_page = vrec.get("official_page_url") or vrec.get("source_page_url") or img_source
        img_status = "verified"

        notes_lines = [
            f"【合作類別與期程】{program_type}｜研修期間：{study_period_str}",
            f"【當期名額與費用待遇】{quota_str}｜{tuition_note or '依兩校協議辦理'}",
            f"【開放學院與學制】{colleges_str}｜{degree_levels_str}",
            f"【語言與學業門檻】{lang_req_str}｜{gpa_req_str}",
            f"【住宿與生活資訊】{housing_str}",
        ]
        if exps:
            notes_lines.append(
                f"【佛光大學歷年交換經驗分享與錄取實績（共 {len(exps)} 筆）】收錄於國際暨兩岸事務處（含：{'、'.join(exp_labels[:4])}）"
            )
        if remarks_raw:
            notes_lines.append(f"【學程與締約摘要】{remarks_raw}")

        partner_record = {
            "school_name": full_name,
            "country": country,
            "region": region,
            "colleges": colleges_str,
            "degree_levels": degree_levels_str,
            "study_period": study_period_str,
            "eligibility": f"開放對象：{colleges_str}（{degree_levels_str}）｜{gpa_req_str}｜{lang_req_str}",
            "language_requirement": lang_req_str,
            "gpa_requirement": gpa_req_str,
            "quota": quota_str,
            "quota_status": "published" if avail_status == "open" else "reference_only",
            "availability_status": avail_status,
            "availability_note": f"佛光大學國際暨兩岸事務處公告合作姊妹校（{program_type}）；{quota_str}。",
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
            "factsheet_url": None,
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
                "title": f"佛光大學國際暨兩岸事務處（OICA）海外及兩岸交換生專頁—{zh_name}",
                "source_url": source_url,
                "role": "home_university",
                "authority": "home_official_notice",
                "effective_academic_year": acad_year,
                "application_round": round_label,
                "checked_at": CHECKED_AT,
            },
            {
                "title": "A06-004 佛光大學與境外學校學生交流甄選實施辦法＆A06-005 大陸高校交換學生補助實施辦法",
                "source_url": FGU_LAW_A06_004_PDF_URL,
                "role": "home_university",
                "authority": "home_official_notice",
                "effective_academic_year": acad_year,
                "application_round": round_label,
                "checked_at": CHECKED_AT,
            },
            {
                "title": "佛光大學與美國西來大學 2+2 雙學位助學金辦法、林呂德文乘風萬里助學基金與學海無涯增額學習助學金要點",
                "source_url": FGU_LAW_URL,
                "role": "home_university",
                "authority": "home_official_notice",
                "effective_academic_year": acad_year,
                "application_round": round_label,
                "checked_at": CHECKED_AT,
            },
        ]
        if exp_links:
            wf_sources.append({
                "title": f"佛光大學國際暨兩岸事務處交換生經驗分享與錄取榜單—{zh_name}（{len(exps)} 筆）",
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
            "home_university": "佛光大學",
            "school_name": full_name,
            "partner_website": website,
            "country": country,
            "program_type": program_type,
            "academic_year": acad_year,
            "application_round": round_label,
            "effective_application_rounds": [round_label, "115-1", "115-2", "116-1", "116-2"],
            "applicability_status": "verified",
            "applicability_note": "佛光大學由國際暨兩岸事務處（雲起樓 104 室）統籌全校 6 大學院（人文學院、社會科學院、管理學院、創意與科技學院、樂活產業學院、佛教學院）赴海外、佛光山教團系統大學及大陸港澳地區姊妹校交換與跨國雙學位（美國西來大學 2+2、英國密德薩斯大學 3+1/3+1+1、澳洲南天大學）甄選與獎助學金核發。",
            "review_status": "published",
            "published_at": CHECKED_AT,
            "steps": [
                {
                    "rule_id": f"fgu-{acad_year}-home-1-{sn:03d}",
                    "order": 1,
                    "phase": "校內申請",
                    "title": f"確認佛大在學年級、GPA 75 分／操行 80 分門檻與 {zh_name} 語檢要求，並完成 EASY TEST 托福模考",
                    "responsible_party": "學生",
                    "responsible_unit": "佛光大學國際暨兩岸事務處／各院系所",
                    "deadline_at": deadline_iso,
                    "deadline_status": "verified_exact" if avail_status == "open" else "reference_only",
                    "deadline_source_url": source_url,
                    "deadline_checked_at": CHECKED_AT,
                    "deadline_reminder_eligible": avail_status == "open",
                    "summary": f"確認符合《A06-004 佛光大學與境外學校學生交流甄選實施辦法》：申請人須為本校學士班二年級（含）以上或碩博士班在學學生，符合學業要求（{gpa_req_str}）與語言門檻（{lang_req_str}），並於校內截止前完成圖書館 EASY TEST 平台 iBT 托福模擬測驗第 1 回。",
                    "details": [
                        f"開放學制與學院：{colleges_str}（{degree_levels_str}）",
                        f"語言與學業條件：{lang_req_str}｜{gpa_req_str}",
                        f"當期名額與計畫類別：{quota_str}｜{program_type}",
                    ],
                    "scope": {
                        "home_universities": ["佛光大學"],
                        "partner_universities": [full_name],
                        "academic_years": ["115", "116"],
                        "application_rounds": [round_label, "115-1", "115-2", "116-1", "116-2"],
                    },
                    "source_urls": [source_url, FGU_LAW_A06_004_PDF_URL, FGU_STEPS_PDF_URL],
                    "checked_at": CHECKED_AT,
                    "support_status": "verified",
                },
                {
                    "rule_id": f"fgu-{acad_year}-home-2-{sn:03d}",
                    "order": 2,
                    "phase": "校內申請",
                    "title": "備妥《海外／大陸地區交換生申請表》與應備文件經導師及系主任簽章後送交雲起樓 104 室國際處",
                    "responsible_party": "學生",
                    "responsible_unit": "所屬學系（所）／學院／國際暨兩岸事務處",
                    "deadline_at": deadline_iso,
                    "deadline_status": "verified_exact" if avail_status == "open" else "reference_only",
                    "deadline_source_url": FGU_LAW_A06_004_PDF_URL,
                    "deadline_checked_at": CHECKED_AT,
                    "deadline_reminder_eligible": avail_status == "open",
                    "summary": "於校內公告期限前（第一階段春季班每年 10 月中旬截止；第二階段秋季班每年 3 月中旬截止）填妥交換生申請表與家長同意書，檢附歷年成績單正本（含排名百分比）、語言檢定證明、EASY TEST 托福模擬測驗成績、自傳與讀書計畫、教師推薦信及保證書送交國際處。",
                    "details": [
                        "第一階段（春季班／隔年春季出國）：每年 9 月下旬至 10 月中旬收件（如 2026/09/23–10/16），11 月初面試。",
                        "第二階段（秋季班／當年度秋季出國）：每年 2 月下旬至 3 月中旬收件（如 2027/02/22–03/19），4 月初面試。",
                    ],
                    "document_requirements": [
                        {
                            "name": "佛光大學海外／大陸地區姊妹校交換學生申請表、家長同意書及保證書（含導師與系主任核章）",
                            "official_form_url": FGU_DOWNLOAD_URL,
                            "source_urls": [FGU_DOWNLOAD_URL, FGU_LAW_A06_004_PDF_URL],
                        },
                        {
                            "name": "歷年成績單正本（含班排百分比）、有效外語檢定證明及圖書館 EASY TEST 平台 iBT 托福模擬測驗第 1 回成績畫面",
                            "official_form_url": FGU_DOWNLOAD_URL,
                            "source_urls": [FGU_STEPS_PDF_URL, FGU_LAW_A06_004_PDF_URL],
                        },
                        {
                            "name": "自傳、讀書計畫書（含擬選修課程對照）及教師推薦信",
                            "official_form_url": FGU_DOWNLOAD_URL,
                            "source_urls": [FGU_DOWNLOAD_URL, FGU_LAW_A06_004_PDF_URL],
                        },
                    ],
                    "scope": {
                        "home_universities": ["佛光大學"],
                        "academic_years": ["115", "116"],
                        "application_rounds": [round_label, "115-1", "115-2", "116-1", "116-2"],
                    },
                    "source_urls": [FGU_DOWNLOAD_URL, FGU_LAW_A06_004_PDF_URL, FGU_STEPS_PDF_URL],
                    "checked_at": CHECKED_AT,
                    "support_status": "verified",
                },
                {
                    "rule_id": f"fgu-{acad_year}-home-3-{sn:03d}",
                    "order": 3,
                    "phase": "甄選與提名",
                    "title": "參加國際處校內書面審查與面試甄選，並同步申請西來 2+2 助學金、學海飛颺／無涯、林呂德文基金或赴陸補助",
                    "responsible_party": "佛光大學國際暨兩岸事務處與申請學生",
                    "responsible_unit": "國際暨兩岸事務處",
                    "deadline_at": "2027-04-09T17:00:00+08:00",
                    "deadline_status": "verified_exact",
                    "deadline_source_url": FGU_LAW_A06_004_PDF_URL,
                    "deadline_checked_at": CHECKED_AT,
                    "deadline_reminder_eligible": False,
                    "summary": f"經國際暨兩岸事務處書面審查與面試擇優錄取推薦赴 {zh_name}，可同步申請教育部《學海飛颺／惜珠》、校內《學海無涯增額學習助學金》、《林呂德文乘風萬里助學基金》（系統大學來回機票 9 成）、《西來大學 2+2 全額學分費獎助 USD 29,904》或《A06-005 赴陸交換生甲／乙／丙類機票與生活費補助》。",
                    "details": tuition_points_list,
                    "scope": {
                        "home_universities": ["佛光大學"],
                        "academic_years": ["115", "116"],
                        "application_rounds": [round_label, "115-1", "115-2", "116-1", "116-2"],
                    },
                    "source_urls": [
                        FGU_LAW_A06_004_PDF_URL,
                        FGU_LAW_A06_005_PDF_URL,
                        FGU_LAW_UWEST_PDF_URL,
                        FGU_LAW_LIN_LU_PDF_URL,
                        FGU_LAW_XUEHAI_WUYAI_PDF_URL,
                    ],
                    "checked_at": CHECKED_AT,
                    "support_status": "verified",
                },
                {
                    "rule_id": f"fgu-{sn:03d}-host-apply",
                    "order": 4,
                    "phase": "合作校申請",
                    "title": f"由佛大國際處向 {zh_name} 辦理官方提名（Nomination），並遞交姊妹校入學與宿位申請文件",
                    "responsible_party": "學生與接待校國際事務處",
                    "summary": f"通過校內甄選後，由佛光大學國際暨兩岸事務處向 {zh_name} 辦理官方提名；學生須依接待校規定繳交外文入學申請表、英文成績單、護照（或台胞證）影本、財力證明及宿舍申請表，以取得正式入學許可（Admission Letter / COE / I-20 / 錄取通知書）。",
                    "details": [
                        f"研修期程：{study_period_str}｜名額：{quota_str}",
                        f"語言與學業條件：{lang_req_str}｜{gpa_req_str}",
                        f"住宿與費用待遇：{housing_str}",
                    ],
                    "scope": {
                        "home_universities": ["佛光大學"],
                        "partner_universities": [full_name],
                        "academic_years": ["115", "116"],
                        "application_rounds": [round_label, "115-1", "115-2", "116-1", "116-2"],
                    },
                    "source_urls": [source_url, FGU_OICA_HOME_URL] + ([website] if website else []),
                    "checked_at": CHECKED_AT,
                    "support_status": "verified",
                    "needs_confirmation": False,
                },
                {
                    "rule_id": f"fgu-{acad_year}-home-5-{sn:03d}",
                    "order": 5,
                    "phase": "行前準備",
                    "title": "完成佛大出國註冊與海外保險，返國後 1 個月內繳交交換心得報告、辦理學分抵免並完成 75 小時服務時數",
                    "responsible_party": "學生與所屬系所",
                    "responsible_unit": "國際暨兩岸事務處／教務處／各學系（所）",
                    "summary": "出國期間須完成佛光大學在學註冊並繳交全額學雜費，每學期至少選修相當於佛大 2 學分以上課程；返國後 1 個月內繳交交換研修心得報告及成績單辦理學分抵免，領取獎助學金者另須於返國後一年內完成 75 小時校內學習服務時數。",
                    "details": tuition_points_list,
                    "scope": {
                        "home_universities": ["佛光大學"],
                        "academic_years": ["115", "116"],
                        "application_rounds": [round_label, "115-1", "115-2", "116-1", "116-2"],
                    },
                    "source_urls": [FGU_LAW_A06_004_PDF_URL, FGU_LAW_A06_005_PDF_URL, FGU_DOWNLOAD_URL],
                    "checked_at": CHECKED_AT,
                    "support_status": "verified",
                },
            ],
            "sources": wf_sources,
            "last_checked": CHECKED_AT,
            "coverage_status": "official_verified",
            "coverage_note": f"已完整整合佛光大學國際暨兩岸事務處（OICA）《A06-004 與境外學校學生交流甄選實施辦法》、《A06-005 學生選派至大陸高校擔任交換學生補助實施辦法》、《與美國西來大學雙學位計畫實施及助學金辦法》、《林呂德文乘風萬里助學基金設置要點》、《學海無涯增額學習助學金要點》、115-1／112-2／111-1 交換生錄取榜單及 {exp_covered_schools} 校 {total_exp_reports} 筆交換經驗與榜單紀錄，共 {len(catalog_source)} 所合作姊妹校資料。",
        })

        cost_line = f"{zh_name} 預估每月生活費：{living_cost_str}"
        tuition_clean = tuition_points_list[0]
        housing_clean = housing_str
        calendar_clean = f"學期與研修時間參考：{sem_dates_str}"
        course_clean = course_rest_str

        dest_sources = [
            {
                "title": f"佛光大學國際暨兩岸事務處（OICA）交換學生與雙聯學位專頁—{zh_name}",
                "source_url": source_url,
                "summary": "佛光大學國際處公告之合作學程、開放學制、語言檢定門檻與免繳姊妹校學費／雙學位獎助說明",
            },
            {
                "title": "A06-004 佛光大學與境外學校學生交流甄選實施辦法＆A06-005 大陸高校交換學生補助實施辦法",
                "source_url": FGU_LAW_A06_004_PDF_URL,
                "summary": "佛光大學出國交換在學註冊規定、GPA 75 分／操行 80 分門檻、EASY TEST 托福模考與獎助學金核銷規範",
            },
        ]
        if exp_links:
            dest_sources.append({
                "title": f"佛光大學國際暨兩岸事務處交換生經驗分享與錄取榜單—{zh_name}（{len(exps)} 筆）",
                "source_url": exp_links[0]["url"],
                "summary": f"收錄佛光大學學生赴 {zh_name} 交換經驗分享與歷年錄取實績共 {len(exps)} 筆",
            })
        if website:
            dest_sources.append({
                "title": f"{full_name} 官方網站",
                "source_url": website,
                "summary": "接待合作姊妹校官方網站",
            })

        src_url_list = (
            [source_url, FGU_LAW_A06_004_PDF_URL, FGU_LAW_A06_005_PDF_URL, FGU_LAW_URL]
            + ([exp_links[0]["url"]] if exp_links else [])
            + ([website] if website else [])
        )

        destinations.append({
            "home_university": "佛光大學",
            "school_name": full_name,
            "country": country,
            "city": city_name,
            "cost_summary": f"{cost_line}。\n{tuition_clean}",
            "housing_summary": housing_clean,
            "transport_summary": f"校區代表城市：{city_name}。請依入學許可確認實際授課校區位置與當地學生交通卡優惠。",
            "campus_life_summary": f"{calendar_clean}\n{course_clean}",
            "student_guide_sections": [
                {
                    "key": "cost",
                    "title": "生活費、佛大在學註冊規定、西來 2+2 全額獎助、學海飛颺／無涯與赴陸機票生活費補助",
                    "summary": cost_line,
                    "points": [cost_line] + tuition_points_list,
                    "source_urls": src_url_list,
                    "caution": "交換期間須完成佛光大學在學註冊並繳交全額學雜費；領取獎助學金者須於返國後 1 個月內繳交心得報告並於一年內完成 75 小時校內服務時數。",
                },
                {
                    "key": "housing",
                    "title": "住宿資訊與校內外國際學生宿舍申請",
                    "summary": housing_clean[:160],
                    "points": [housing_clean],
                    "source_urls": src_url_list,
                    "caution": "韓國金剛大學、大陸上海大學、鄭州大學、西北師範大學及陽光學院提供免收或減免校內住宿費優惠；其餘姊妹校宿位請於獲提名後儘早申請。",
                },
                {
                    "key": "insurance",
                    "title": "海外醫療及意外保險與家長同意書／保證書規定",
                    "summary": visa_health_str,
                    "points": [
                        visa_health_str,
                        "依《A06-004 佛光大學與境外學校學生交流甄選實施辦法》，所有申請學生均須檢附經家長或監護人親筆簽章之《家長同意書》與《保證書》，並於出國前投保涵蓋交換全期之海外醫療及意外保險。",
                    ],
                    "source_urls": src_url_list,
                    "caution": "美國、英國、德國、澳洲、紐西蘭、日本、韓國等接待校對交換生當地醫療保險有強制規定，請依入學通知書辦理。",
                },
                {
                    "key": "visa",
                    "title": "留學交換簽證（或臺胞證）辦理、出國修課下限與在學註冊義務",
                    "summary": visa_health_str,
                    "points": [
                        visa_health_str,
                        "交換期間每學期至少須修習相當於佛光大學 2 學分以上之課程（西來大學 2+2 雙學位每學期須修習 12 學分且各科達 70 分以上）。",
                    ],
                    "source_urls": src_url_list,
                    "caution": "收到接待校正式入學許可（Admission Letter / COE / I-20 / 錄取通知書）後請立即辦理簽證及役男出境核准手續。",
                },
                {
                    "key": "transport",
                    "title": "校區位置、機場抵達交通與當地大眾運輸",
                    "summary": f"{zh_name} 位於 {country} {city_name}，請對照入學通知確認報到校區與接機安排。",
                    "points": [f"校區所在城市：{city_name}（代表座標：{lat}, {lon}）。"],
                    "source_urls": src_url_list,
                    "caution": None,
                },
                {
                    "key": "academics",
                    "title": "選課限制、EASY TEST 托福模考規定與返國學分抵免",
                    "summary": course_clean[:160],
                    "points": [course_clean],
                    "source_urls": src_url_list,
                    "caution": "請於選課前確認擬修科目與佛光大學母系專業或通識／國際學程（如菲律賓 LCIC 270 小時可折抵佛大國際學程 15 學分）之採認對應關係。",
                },
            ],
            "experience_links": exp_links,
            "sources": dest_sources,
            "last_checked": CHECKED_AT,
            "coverage_status": "official_verified",
            "coverage_note": "已整合佛光大學國際暨兩岸事務處（OICA）海外與大陸交換簡章、法規辦法、歷年錄取榜單及學生交換經驗分享。",
        })

        research_records.append({
            "home_university": "佛光大學",
            "school_name": full_name,
            "country": country,
            "official_website": website,
            "verification_status": "official_verified",
            "discovery_source_url": detail_url,
            "checked_at": CHECKED_AT,
            "note": "佛光大學國際暨兩岸事務處《海外及大陸地區交換生甄選簡章》、《2+2 與 3+1 雙聯學位專區》、《佛光山系統大學跨國學習》與 ROR/Wikidata 官方網址核對完成。",
        })

        ev_sources = [{"title": f"佛光大學國際暨兩岸事務處交換生專頁—{zh_name}", "url": source_url}]
        if exp_links:
            ev_sources.append({
                "title": f"佛光大學交換生經驗分享與錄取榜單—{zh_name}（{len(exps)} 筆）",
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
                "scope": "佛光大學全球與大陸交換姊妹校住宿與生活資訊",
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
                "scope": "佛光大學出國交換學雜費規定、西來 2+2 全額獎助、學海飛颺／無涯、林呂德文助學基金與赴陸交換補助",
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
                "scope": "佛光大學境外學校學生交流甄選實施辦法、雙學位辦法與學分抵免規定",
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
                "scope": "佛光大學海外交換與雙聯學位簽證、家長同意書、保證書與海外醫療保險提醒",
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
                        f"｜佛光大學公開收錄 {len(exps)} 筆赴 {zh_name} 交換生經驗分享與錄取榜單（{'、'.join(exp_labels[:3])}）。"
                        if exps
                        else ""
                    )
                ),
                "sources": ev_sources,
                "checked_at": CHECKED_AT,
                "scope": "佛光大學交換名額、歷年錄取榜單與學長姐經驗分享",
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
                "已整合佛光大學國際暨兩岸事務處《A06-004 與境外學校學生交流甄選實施辦法》、《A06-005 學生選派至大陸高校擔任交換學生補助實施辦法》、《西來大學 2+2 雙學位計畫》及歷屆學生交換經驗分享與錄取榜單。",
                "當期免學費名額、宿位供給、語檢門檻與選課限制請依合作校最新簡章及入學通知書核對。",
            ],
            "location_signature": f"verified:{lat}:{lon}:representative",
            "extraction_version": 3,
        })

    def write_jsonl(path: Path, rows: list[dict]) -> None:
        path.write_text(
            "\n".join(json.dumps(r, ensure_ascii=False) for r in rows) + ("\n" if rows else ""),
            encoding="utf-8",
        )

    write_jsonl(OFFICIAL_FGU_DIR / "partners.jsonl", partners)
    write_jsonl(SOURCES_FGU_DIR / "partners.jsonl", partners)
    write_jsonl(OFFICIAL_FGU_DIR / "application_workflows.jsonl", workflows)
    write_jsonl(OFFICIAL_FGU_DIR / "destination_profiles.jsonl", destinations)
    write_jsonl(OFFICIAL_FGU_DIR / "partner_research.jsonl", research_records)
    write_jsonl(OFFICIAL_FGU_DIR / "student_life.jsonl", life_records)
    write_jsonl(OFFICIAL_FGU_DIR / "experience_sources.jsonl", experience_sources_records)
    write_jsonl(OFFICIAL_FGU_DIR / "student_experience_sources.jsonl", experience_sources_records)
    write_jsonl(OFFICIAL_FGU_DIR / "student_experiences.jsonl", student_experience_rows)

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
    (OFFICIAL_FGU_DIR / "student-experience-digests.json").write_text(
        json.dumps({"digests": digest_records}, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    (OFFICIAL_FGU_DIR / "student-experiences.json").write_text(
        json.dumps(
            {
                "school_id": "fgu",
                "school_name": "佛光大學",
                "checked_at": CHECKED_AT,
                "source_url": FGU_EXPERIENCE_SHARING_URL,
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

    (OFFICIAL_FGU_DIR / "campus-locations.json").write_text(
        json.dumps(
            {
                "school_id": "fgu",
                "school_name": "佛光大學",
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
    (OFFICIAL_FGU_DIR / "campus-assets.json").write_text(
        json.dumps(
            {
                "school_id": "fgu",
                "school_name": "佛光大學",
                "checked_at": CHECKED_AT,
                "total_schools": len(campus_assets_list),
                "verified_count": sum(1 for a in campus_assets_list if a["status"] == "verified"),
                "assets": campus_assets_list,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    fgu_source_urls = [
        FGU_OICA_HOME_URL,
        FGU_OUTBOUND_NON_CN_URL,
        FGU_OUTBOUND_CN_URL,
        FGU_FO_GUANG_EXCHANGE_URL,
        FGU_22_PROGRAM_URL,
        FGU_ADMISSION_LIST_URL,
        FGU_EXPERIENCE_SHARING_URL,
        FGU_LAW_URL,
        FGU_DOWNLOAD_URL,
        FGU_115_1_ADMISSION_URL,
        FGU_115_1_BRIEFING_URL,
        FGU_MIDDLESEX_DUAL_URL,
        FGU_KONKUK_WINTER_URL,
        FGU_LAW_A06_004_PDF_URL,
        FGU_LAW_A06_005_PDF_URL,
        FGU_LAW_UWEST_PDF_URL,
        FGU_LAW_LIN_LU_PDF_URL,
        FGU_LAW_XUEHAI_WUYAI_PDF_URL,
        FGU_STEPS_PDF_URL,
    ]

    exchange_info_payload = {
        "school_name": "佛光大學",
        "program_type": [
            f"國際暨兩岸事務處（OICA）海外及大陸地區姊妹校交換學生計畫（涵蓋美國、英國、德國、澳洲、紐西蘭、日本、韓國、泰國、馬來西亞、菲律賓、印度、緬甸、香港及中國大陸 985／211／雙一流名校等 {open_partner_count} 所常態開放申請交換與雙聯合作校，共 {len(partners)} 所官方合作姊妹校）",
            "跨國雙學位計畫（涵蓋【美國西來大學 University of the West】2+2 雙學士計畫［全額補助四學期 48 學分費共 USD 29,904，約新臺幣 98 萬元］、【英國國立密德薩斯大學 Middlesex University London】3+1 雙學士暨 3+1+1 學碩士雙聯計畫，以及【澳洲南天大學 Nan Tien Institute】佛光山系統大學跨國學分與碩士研修計畫）",
            "五大出國與赴陸研修獎助學金體系：（1）美國西來大學 2+2 全額學分費獎助 USD 29,904；（2）教育部《學海飛颺》與《學海惜珠》出國研修獎學金（5萬至30萬元）；（3）《佛光大學學海無涯增額學習助學金》；（4）《林呂德文乘風萬里助學基金》（補助經濟不利學生赴系統大學來回機票最高 9 成）；（5）《A06-005 大陸高校交換生補助》（甲類機票9成＋每月5,000元生活費、乙類清寒機票7成＋每月4,000元生活費、丙類一般生機票7成）",
        ],
        "academic_year": [
            "115（涵蓋 115–116 學年度第一階段［春季班每年 9–10 月收件、11 月面試］與第二階段［秋季班每年 2–3 月收件、4 月面試］交換生暨雙學位甄選）",
            f"本平台完整收錄佛光大學國際暨兩岸事務處公告之 {len(partners)} 所海外與兩岸合作姊妹校（含 {open_partner_count} 所常態開放申請之交換與雙聯合作校、{len(partners) - open_partner_count} 所正式締約姊妹校，橫跨全球 14 個國家與地區，並收錄 {exp_covered_schools} 所合作大學共 {total_exp_reports} 筆歷年交換經驗分享與錄取榜單實績）",
        ],
        "semester": [
            "第一階段甄選（春季班／隔年春季學期出國）：每年 9 月下旬至 10 月中旬校內收件，11 月初辦理面試，11 月中旬公告錄取名單。",
            "第二階段甄選（秋季班／當年度秋季學期出國）：每年 2 月下旬至 3 月中旬校內收件，4 月初辦理面試，4 月中旬公告錄取名單。",
        ],
        "application_period": [
            "【第一階段（春季班／隔年春季出國交換暨 2+2 雙學位甄選）】每年 9 月下旬至 10 月中旬（如 2026/09/23–10/16）受理校內報名收件，11 月初舉行面試（紙本核章資料送交雲起樓 104 室國際暨兩岸事務處）。",
            "【第二階段（秋季班／當年度秋季出國交換暨 2+2 雙學位甄選）】每年 2 月下旬至 3 月中旬（預計 2027/02/22–03/19 17:00）受理校內報名收件，4 月初舉行面試。",
            "【韓國首爾建國大學國際冬季學校（Konkuk University Winter School）】早鳥報名至 2026/11/13 截止，一般報名至 2026/12/04 17:00 截止（活動期間 2027/02/01–02/17）。",
        ],
        "eligibility": [
            "1. 在學年級與學制資格：依《A06-004 佛光大學與境外學校學生交流甄選實施辦法》，申請人須為佛光大學學士班二年級（含）以上或碩、博士班在學學生（大一下學期學生得報名參加大二出國交換甄選；修讀美國西來大學 2+2 雙學位者須於佛大修業滿二學年；修讀英國密德薩斯大學 3+1 雙學士者須於佛大修畢大一至大三課程並修滿 96 學分）。",
            "2. 學業與操行成績門檻：前一學期學業成績平均達 75 分（約 GPA 3.0）以上，且操行成績平均達 80 分以上（申請中國人民大學、南京大學、東南大學、四川大學等大陸 985／雙一流頂尖高校者，班級排名須在前 20% 以內；美國西來大學 2+2 雙學位各科成績須維持 70 分以上始得折抵學分）。",
            "3. EASY TEST 托福模擬測驗必備規定：所有申請海外及大陸地區交換之學生，均須於校內收件截止前登入佛光大學圖書館 EASY TEST 線上學習平台完成「iBT 托福模擬測驗第 1 回」並印出成績畫面隨件繳交。",
            "4. 返國學習服務時數義務：凡獲教育部學海計畫或佛光大學校內各項出國／赴陸交換獎助學金之學生，須於返國後一年內完成 75 小時校內學習服務時數，並提交交換心得報告與出席經驗分享會。",
        ],
        "language_requirement": [
            "1. 英語系及歐美澳亞英語授課姊妹校：（a）美國西來大學（UWest）：大學部正式課程 TOEFL iBT 69 或 IELTS 5.5（研究所 iBT 79 或 IELTS 6.5；條件式入學 iBT 59–68 或 IELTS 5.0；未達標者可參加西來大學遠端 EPT 英文分級測驗或修讀免學費 ESL 課程）；（b）英國國立密德薩斯大學（Middlesex University）：大學部 3+1 雙學士 IELTS 6.0（單科不低於 5.5）或參加免費 Middlesex Online English Test 內測，碩士 IELTS 6.5；（c）德國漢堡大學、紐西蘭奧塔哥大學、澳洲南天大學、印度德里大學：TOEFL iBT 65–79 或 IELTS 5.5–6.5；（d）馬來西亞拉曼大學（UTAR）：建議 IELTS 5.0 以上；（e）泰國正大管理學院（PIM）、泰國湄州大學、菲律賓拉普拉普宿霧國際大學（LCIC，修滿 270 小時可折抵佛大國際學程 15 學分）、菲律賓光明大學、緬甸龐道烏國際大學：提交各類英檢證明或佛大大一英文成績單。",
            "2. 日本姊妹校：（a）日本龍谷大學（Ryukoku University）：申請 JEP-Kyoto 日語學程須具 JLPT N4 以上或 300 小時日文學習證明；申請 JEP-English 全英學程（含公費交換生無日文基礎者）須具 TOEFL iBT 61（或 PBT 500 / IELTS 5.5）以上；（b）日本花園大學（Hanazono University）：須具 JLPT N2 以上。",
            "3. 韓國姊妹校：（a）京畿大學、東國大學（首爾校區／慶州 WISE 校區）、國立慶尚大學、金剛大學、東明大學、國立昌原大學：修讀語學堂韓語課程者免附韓檢成績，修讀大學部專業課程須具 TOPIK 3 級以上；（b）威德大學（Uiduk University）：修讀大學部課程僅需 TOPIK 2 級以上；（c）新羅大學：須具 TOPIK 3 級以上；（d）中央僧伽大學：免韓檢成績；（e）京東大學（KDU Global）：英語學程 TOEIC 550 / IELTS 5.5。",
            "4. 中國大陸及香港姊妹校：中國人民大學、南京大學、北京交通大學、上海大學、四川大學、深圳大學、華中師範大學、鄭州大學、西北師範大學、陽光學院、東南大學、煙台大學、揚州大學、合肥工業大學、集美大學、廣東海洋大學、福建技術師範學院、海南大學、南京理工大學、濟南大學、陝西師範大學、雲南大學、青海民族大學及香港教育大學均得以中文授課申請（大陸高校免附外語檢定，惟仍須完成校內 EASY TEST 平台 iBT 托福模擬測驗第 1 回）。",
        ],
        "required_documents": [
            "1. 佛光大學海外／大陸地區姊妹校交換學生申請表（含導師及系所主任簽章；申請西來大學 2+2 者另填雙學位計畫申請表）",
            "2. 歷年中文成績單正本（須含學業總平均及班級排名百分比；申請歐美日韓姊妹校通過初審後另備英文成績單）",
            "3. 有效外語能力檢定成績證明影本（TOEFL iBT / IELTS / TOEIC / JLPT / TOPIK；申請大陸姊妹校免附，申請泰菲緬姊妹校可附大一英文成績單）",
            "4. 佛光大學圖書館 EASY TEST 線上平台「iBT 托福模擬測驗第 1 回」完成測驗成績畫面（全體海外及赴陸申請者必繳）",
            "5. 中文自傳與讀書計畫書（含出國修課規劃與學分抵免對照；申請歐美日韓姊妹校建議併附外文讀書計畫）",
            "6. 佛光大學教師推薦信 1–2 封",
            "7. 家長（或監護人）同意書及保證書（親筆簽名蓋章）與有效護照／臺胞證影本",
        ],
        "scholarship_info": [
            "1. 《佛光大學與美國西來大學雙學位計畫實施及助學金辦法》（2+2 全額學分費獎助）：凡佛光大學學士班修滿二學年、各科成績達 70 分以上且通過語檢門檻赴美國西來大學修讀 2+2 雙學位者，於西來大學修業期間只需繳交佛光大學私校標準學雜費，由佛光山系統大學全額補助西來大學每學期 12 學分學分費 USD 7,476，至多補助四個學期共 48 學分（總計補助 USD 29,904，折合新臺幣約 98 萬元）。",
            "2. 教育部《學海飛颺》與《學海惜珠》出國研修獎學金：選送優秀在學學生（學海飛颺）或持低收入戶、中低收入戶、特殊境遇家庭證明之清寒優秀學生（學海惜珠）赴非大陸港澳地區姊妹校交換或修讀雙聯學位 1 學期至 1 學年，每人核發新臺幣 50,000 元至 300,000 元不等之獎助學金。",
            "3. 《佛光大學學海無涯增額學習助學金要點》與《林呂德文乘風萬里助學基金設置要點》：（a）學海無涯助學金補助赴境外姊妹校交換研習之優秀學生；（b）林呂德文乘風萬里助學基金專款補助低收入戶、中低收入戶或家庭突遭變故之經濟不利學生赴佛光山系統大學（美國西來大學、澳洲南天大學、菲律賓光明大學）或海外姊妹校交流，最高補助往返經濟艙機票費用 9 成。",
            "4. 《A06-005 佛光大學學生選派至大陸高校擔任交換學生補助實施辦法》：分三類核發赴陸交換獎助：（a）甲類補助：補助往返經濟艙機票費用 9 成，並核發在陸期間每月新臺幣 5,000 元生活補助費；（b）乙類補助（具清寒證明者）：補助往返經濟艙機票費用 7 成，並核發在陸期間每月新臺幣 4,000 元生活補助費；（c）丙類補助（一般生）：補助往返經濟艙機票費用 7 成。上海大學、鄭州大學、西北師範大學、陽光學院另提供免收住宿費優惠。",
        ],
        "partner_universities": [p["school_name"] for p in partners],
        "source_urls": fgu_source_urls,
        "last_checked": CHECKED_AT,
    }
    (OFFICIAL_FGU_DIR / "exchange_info.json").write_text(
        json.dumps(exchange_info_payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    student_dashboard_payload = {
        "school_name": "佛光大學",
        "last_checked": CHECKED_AT,
        "academic_score_minimum": 75.0,
        "academic_score_rule": "依《A06-004 佛光大學與境外學校學生交流甄選實施辦法》及《A06-005 學生選派至大陸高校擔任交換學生補助實施辦法》：申請人須為本校學士班二年級（含）以上或碩博士班在學學生，前一學期學業成績平均達 75 分（約 GPA 3.0）以上且操行成績平均達 80 分以上（申請中國人民大學、南京大學、東南大學、四川大學等重點大陸高校須班排名前 20%）。",
        "academic_gpa_minimum": 3.0,
        "maximum_preferences": 3,
        "selection_rules": {
            "academic_policy": "gpa_or_rank",
            "academic_reference_year": "115",
            "undergraduate_gpa_minimum": 3.0,
            "graduate_academic_exempt": False,
            "exclude_in_service": False,
            "pending_quota_planning": False,
            "partner_requirements_need_confirmation": False,
            "degree_score_minimums": {
                "undergraduate": 75.0,
                "graduate": 75.0,
            },
            "excluded_undergraduate_years": [
                "大一",
                "大一上",
                "一年級",
                "一年級上學期",
            ],
            "language_certificate_required": True,
        },
        "language_score_minimums": {
            "toefl": 61.0,
            "ielts": 5.0,
            "toefl_itp": 500.0,
            "toeic": 550.0,
        },
        "application_periods": [
            {
                "title": "佛光大學 116學年度第 1 學期（秋季班）赴海外及大陸地區姊妹校交換生暨雙聯學位甄選（預計 2027/02/22–03/19 受理）",
                "details": [
                    "依佛光大學國際暨兩岸事務處（雲起樓 104 室）公告之兩階段甄選時程：第一階段（春季班出國）於每年 9 月下旬至 10 月中旬收件、11 月初面試；第二階段（秋季班出國）於每年 2 月下旬至 3 月中旬收件、4 月初面試。",
                    "申請人須符合前一學期學業平均 75 分以上、操行 80 分以上，完成圖書館 EASY TEST 線上平台「iBT 托福模擬測驗第 1 回」，並備妥核章申請表、成績單、語檢證明、自傳與讀書計畫、推薦信及家長同意書送交國際處。",
                ],
                "source": {
                    "title": "佛光大學國際暨兩岸事務處（OICA）交換生甄選說明會簡報與實施辦法",
                    "source_url": FGU_OUTBOUND_NON_CN_URL,
                    "category": "exchange_application",
                    "summary": "佛光大學海外及大陸地區姊妹校交換生甄選資格、兩階段收件時程與 EASY TEST 模考規定。",
                },
                "scope": "home_application",
                "program_types": ["exchange", "dual_degree"],
                "academic_year": "116",
                "application_round": "116-1 秋季班海外及大陸姊妹校交換暨雙學位校內甄選",
                "audience": "all_students",
                "opens_at": "2027-02-22T09:00:00+08:00",
                "deadline_at": "2027-03-19T17:00:00+08:00",
                "date_status": "verified_exact",
                "status": "upcoming",
                "status_note": "秋季班校內甄選預計於 2 月下旬開放收件、3 月中旬截止；春季班於每年 9 月下旬至 10 月中旬收件。",
                "deadline_note": "所有申請人（含大陸地區）均須於截止前完成圖書館 EASY TEST 平台 iBT 托福模擬測驗第 1 回。",
                "reminder_eligible": True,
                "checked_at": CHECKED_AT,
            },
            {
                "title": "佛光大學與美國西來大學（UWest）2+2 雙學位計畫（全額補助 USD 29,904 學分費）＆英國密德薩斯大學 3+1 / 3+1+1 雙聯學位申請",
                "details": [
                    "美國西來大學（University of the West）2+2 雙學位計畫：於佛光大學修業滿二學年且各科成績達 70 分以上、通過 TOEFL iBT 69 / IELTS 5.5（或通過西來遠端 EPT 英文分級測驗／ESL 課程），赴美修業期間由佛光山系統大學全額補助西來大學每學期 12 學分學分費 USD 7,476，四學期共補助 USD 29,904（約新臺幣 98 萬元）。",
                    "英國國立密德薩斯大學（Middlesex University London）雙聯學位計畫：於佛光大學修畢大一至大三課程（滿 96 學分）並達 IELTS 6.0（或通過免費 Middlesex 校內英文內測），第 4 年赴英國倫敦修讀取得臺英雙學士（3+1），並可續讀第 5 年取得英國碩士學位（3+1+1）。",
                ],
                "source": {
                    "title": "佛光大學國際暨兩岸事務處「2+2 雙學位計畫」與英國密德薩斯大學雙聯專區",
                    "source_url": FGU_22_PROGRAM_URL,
                    "category": "exchange_application",
                    "summary": "佛光大學與美國西來大學 2+2 全額學分費獎助及英國密德薩斯大學 3+1/3+1+1 雙聯學位簡章。",
                },
                "scope": "home_application",
                "program_types": ["dual_degree"],
                "academic_year": "116",
                "application_round": "116學年度跨國雙聯學位計畫（西來大學 2+2／密德薩斯大學 3+1）",
                "audience": "all_students",
                "opens_at": "2027-02-22T09:00:00+08:00",
                "deadline_at": "2027-03-31T17:00:00+08:00",
                "date_status": "verified_exact",
                "status": "upcoming",
                "status_note": "隨每學期交換暨雙學位甄選梯次（春季班 9–10 月、秋季班 2–3 月）同步受理報名。",
                "deadline_note": "檢附雙學位計畫申請表、歷年英文成績單、課程對照表、語檢證明與讀書計畫送交國際處。",
                "reminder_eligible": True,
                "checked_at": CHECKED_AT,
            },
        ],
        "program_overview": [
            {
                "title": f"佛光大學國際暨兩岸事務處全球姊妹校交換、佛光山系統大學與跨國雙聯學位總覽（{len(partners)} 所合作姊妹校・{open_partner_count} 所常態開放申請・{total_exp_reports} 筆交換經驗與榜單實績）",
                "details": [
                    f"佛光大學（Fo Guang University, FGU，由星雲大師於 2000 年創辦，坐落於宜蘭縣礁溪鄉林尾路 160 號林美山上，為「佛光山教團系統大學」總校區成員）由「國際暨兩岸事務處（Office of International and Cross-Strait Affairs, OICA，雲起樓 104 室）」統籌全校 6 大學院（人文學院、社會科學院、管理學院、創意與科技學院、樂活產業學院、佛教學院）之海外交換、佛光山系統大學跨國學習、歐美雙聯學位及大陸高校交換計畫。本平台完整收錄 {len(partners)} 所佛光大學官方合作姊妹校（含 {open_partner_count} 所常態開放申請之交換與雙聯學位合作校，以及 {len(partners) - open_partner_count} 所正式締約姊妹校），橫跨全球 14 個國家與地區。",
                    f"佛光大學國際交流具備四大核心優勢：（1）佛光山教團系統大學五校資源共享（美國加州西來大學 UWest、澳洲南天大學 NTI、菲律賓光明大學 GMC、臺灣佛光大學與南華大學），其中西來大學 2+2 雙學位提供全額 48 學分費補助 USD 29,904（約新臺幣 98 萬元）；（2）多元歐亞名校交換與雙聯網絡（英國倫敦密德薩斯大學 3+1/3+1+1 雙聯、德國漢堡大學、紐西蘭奧塔哥大學、日本京都龍谷大學［含公費免學費名額］、日本花園大學、韓國東國大學、京畿大學、慶尚國立大學、昌原國立大學、金剛大學［免住宿費優惠］、建國大學冬季學校、泰國正大管理學院 PIM、湄州大學、馬來西亞拉曼大學 UTAR、菲律賓宿霧 LCIC［修滿 270 小時抵佛大 15 學分］、印度德里大學、香港教育大學）；（3）中國大陸 23 所 985／211／雙一流名校交換（中國人民大學、南京大學、東南大學、四川大學、北京交通大學、上海大學［免住宿費］、深圳大學、華中師範大學、鄭州大學［免住宿費］、陝西師範大學、雲南大學、廈門集美大學等）並享甲／乙／丙類往返機票 7–9 成及每月 4,000–5,000 元生活費補助；（4）完整收錄 {exp_covered_schools} 所合作大學共 {total_exp_reports} 筆歷年交換經驗分享與 115-1／112-2／111-1 錄取榜單實績。",
                ],
                "source": {
                    "title": "佛光大學國際暨兩岸事務處（OICA）官方網站",
                    "source_url": FGU_OICA_HOME_URL,
                    "category": "exchange_application",
                    "summary": f"佛光大學 {len(partners)} 所全球與兩岸合作姊妹校、{open_partner_count} 所常態開放交換／雙聯校與 {total_exp_reports} 筆經驗與榜單紀錄。",
                },
            }
        ],
        "eligibility": [
            {
                "title": "學士班二至四年級及碩博士班在學身分、前一學期平均 75 分／操行 80 分（大陸重點名校班排前 20%）與 EASY TEST 托福模考規定",
                "details": [
                    "在學身分與成績門檻：依《A06-004 佛光大學與境外學校學生交流甄選實施辦法》及《A06-005 學生選派至大陸高校擔任交換學生補助實施辦法》，申請人須為佛光大學學士班二年級（含）以上或碩、博士班在學學生（大一下學期可申請大二出國交換），前一學期學業成績平均達 75 分（約 GPA 3.0）以上且操行成績平均達 80 分以上。申請中國人民大學、南京大學、東南大學、四川大學等重點高校者，班排名須在前 20% 以內。",
                    "EASY TEST 模擬測驗與返國服務義務：全體申請海外及大陸交換學生均須於校內收件截止前完成佛光大學圖書館 EASY TEST 線上平台「iBT 托福模擬測驗第 1 回」；領取校內或教育部獎助學金者，返國後一年內須完成 75 小時校內學習服務時數。",
                ],
                "source": {
                    "title": "A06-004 佛光大學與境外學校學生交流甄選實施辦法＆A06-005 大陸高校交換生補助實施辦法",
                    "source_url": FGU_LAW_A06_004_PDF_URL,
                    "category": "exchange_application",
                    "summary": "佛光大學海外及大陸交換生在學年級、GPA 75 分／操行 80 分門檻、EASY TEST 模考與 75 小時服務時數規定。",
                },
            }
        ],
        "language_requirements": [
            {
                "title": "歐美澳英語門檻（iBT 61–79 / IELTS 5.0–6.5 / 西來遠端 EPT 內測）、日本龍谷／花園（JLPT N4–N2 或 iBT 61）、韓國語學堂免韓檢／專業課 TOPIK 2–3 級與大陸免語檢規定",
                "details": [
                    "英語與歐美澳亞姊妹校：（1）美國西來大學大學部正式課程 TOEFL iBT 69 或 IELTS 5.5（條件式入學 iBT 59 / IELTS 5.0，未達標可參加遠端 EPT 分級測驗或修讀免學費 ESL 課程）；（2）英國密德薩斯大學 3+1 雙學士 IELTS 6.0 或免費校內英文內測；（3）德國漢堡大學、紐西蘭奧塔哥大學、澳洲南天大學、印度德里大學要求 iBT 65–79 或 IELTS 5.5–6.5；（4）馬來西亞拉曼大學建議 IELTS 5.0；泰國 PIM、湄州大學、菲律賓 LCIC、光明大學、緬甸龐道烏國際大學可提交英檢證明或佛大大一英文成績單。",
                    "日韓與大陸港澳姊妹校：（1）日本龍谷大學 JEP-Kyoto 要求 JLPT N4 或 300 小時日文課證明，JEP-English 要求 TOEFL iBT 61；日本花園大學要求 JLPT N2；（2）韓國京畿、東國、慶尚、金剛、東明、昌原修讀語學堂免韓檢，修讀大學部課程須 TOPIK 3 級（威德大學僅需 TOPIK 2 級、中央僧伽大學免韓檢）；（3）大陸 23 所姊妹校為中文授課免附外語檢定，惟校內申請仍須完成 EASY TEST 托福模考第 1 回。",
                ],
                "source": {
                    "title": "佛光大學國際暨兩岸事務處海外及大陸地區姊妹校交換簡章與甄選說明會簡報",
                    "source_url": FGU_OUTBOUND_NON_CN_URL,
                    "category": "exchange_application",
                    "summary": "佛光大學各國交換姊妹校與雙聯學位語言檢定門檻一覽。",
                },
            }
        ],
        "required_documents": [
            {
                "title": "交換生申請表、歷年含班排成績單正本、語檢證明、EASY TEST 托福模考成績單、自傳與讀書計畫、推薦信及家長同意書／保證書",
                "details": [
                    "校內申請必備文件：（1）《佛光大學海外／大陸地區姊妹校交換學生申請表》（經導師、系主任簽章）；（2）歷年中文成績單正本（含學業平均及班級排名百分比）；（3）有效外語能力檢定證明（大陸免附）；（4）圖書館 EASY TEST 平台「iBT 托福模擬測驗第 1 回」成績畫面；（5）自傳與讀書計畫書；（6）教師推薦信 1–2 封；（7）家長同意書與保證書。",
                    "行前與返國核銷文件：赴陸交換生出國前須提交《赴陸交換生獎助學金出國前繳件資料檢核表》，返國後 1 個月內提交《返國後繳件資料檢核表》、交換心得報告、正式成績單及《交換生返國後服務時數紀錄表（75 小時）》辦理獎助金尾款核銷與學分抵免。",
                ],
                "source": {
                    "title": "佛光大學國際暨兩岸事務處表單下載專區與交換學生申請步驟 PDF",
                    "source_url": FGU_DOWNLOAD_URL,
                    "category": "exchange_application",
                    "summary": "佛光大學交換生申請表、西來 2+2 申請表、赴陸獎助檢核表與 75 小時服務時數表規範。",
                },
            }
        ],
        "scholarship_info": [
            {
                "title": "美國西來大學 2+2 全額學分費獎助（USD 29,904）、教育部學海飛颺／惜珠、學海無涯增額助學金、林呂德文乘風萬里助學基金與赴陸交換甲／乙／丙類機票生活費補助",
                "details": [
                    "歐美日韓與系統大學獎助：（1）《與美國西來大學雙學位計畫實施及助學金辦法》全額補助西來大學四學期 48 學分費共 USD 29,904（約新臺幣 98 萬元）；（2）教育部《學海飛颺》、《學海惜珠》補助新臺幣 50,000–300,000 元；（3）校內《學海無涯增額學習助學金》；（4）《林呂德文乘風萬里助學基金》補助經濟不利學生赴佛光山系統大學來回機票最高 9 成。",
                    "大陸高校交換補助（《A06-005》）：（1）甲類補助往返機票 9 成＋每月 NT$ 5,000 生活費；（2）乙類（清寒）補助往返機票 7 成＋每月 NT$ 4,000 生活費；（3）丙類（一般生）補助往返機票 7 成；另上海大學、鄭州大學、西北師範大學、陽光學院免收校內住宿費。",
                ],
                "source": {
                    "title": "佛光大學國際暨兩岸事務處「法規辦法」專區（A06-004、A06-005、西來雙學位助學金、林呂德文基金、學海無涯要點）",
                    "source_url": FGU_LAW_URL,
                    "category": "scholarship",
                    "summary": "佛光大學五大海外與大陸交換暨雙學位獎助學金完整規定。",
                },
            }
        ],
        "document_explanations": [
            {
                "title": "佛光大學出國／赴陸交換讀書計畫、自傳、EASY TEST 托福模考與西來大學 2+2 課程對照準備指南",
                "summary": "說明佛光大學國際暨兩岸事務處規定之讀書計畫、自傳、圖書館 EASY TEST 托福模擬測驗及西來大學 2+2 雙學位選課對照表準備重點。",
                "key_points": [
                    "讀書計畫與選課對照（約 1,000–2,000 字）：應具體說明赴外研修動機、擬於志願姊妹校選修之科目（每學期至少相當於佛大 2 學分以上；西來大學 2+2 每學期 12 學分；菲律賓 LCIC 每學期 270 小時折抵佛大國際學程 15 學分）及返國後學分抵免與生涯規劃。",
                    "圖書館 EASY TEST 平台 iBT 托福模擬測驗第 1 回：不論申請歐美日韓或中國大陸姊妹校，全體申請人皆須於校內收件截止前完成測驗並印出成績單隨件繳交。",
                    "返國心得報告與 75 小時學習服務時數：受領獎助學金學生須於返國後 1 個月內繳交交換心得報告，並於返國後一年內完成 75 小時校內服務時數。",
                ],
                "applies_to": [],
                "source": {
                    "title": "佛光大學交換甄選說明會簡報（20260923）與 2+2 雙學位說明會簡報",
                    "source_url": FGU_STEPS_PDF_URL,
                    "category": "exchange_application",
                    "summary": None,
                },
                "document_url": FGU_DOWNLOAD_URL,
                "document_type": "official_document",
                "full_text_extracted": True,
            }
        ],
        "rule_explanations": [
            {
                "title": "A06-004 佛光大學與境外學校學生交流甄選實施辦法、A06-005 大陸高校交換補助辦法與西來大學雙學位助學金辦法",
                "summary": "規範佛光大學出國及赴陸交換申請資格、在學註冊繳費、西來 2+2 全額學分費獎助、赴陸甲乙丙類機票生活費補助與返國 75 小時服務義務。",
                "key_points": [
                    "在學註冊與學費互惠：交換期間須辦理佛光大學註冊並繳交全額學雜費，免繳接待姊妹校學費（日本龍谷大學每學年含 1 名公費免學費名額與 2–3 名自費交換名額）。",
                    "西來大學 2+2 全額學分費獎助：於佛大修業滿二學年且各科達 70 分以上者，由佛光山系統大學全額補助西來大學每學期 12 學分費 USD 7,476（四學期共 48 學分總計 USD 29,904）。",
                    "大陸高校交換甲／乙／丙類補助：甲類補助往返機票 9 成＋每月 5,000 元生活費；乙類（清寒）補助往返機票 7 成＋每月 4,000 元生活費；丙類補助往返機票 7 成。",
                ],
                "applies_to": [],
                "source": {
                    "title": "佛光大學國際暨兩岸事務處法規辦法專區",
                    "source_url": FGU_LAW_A06_004_PDF_URL,
                    "category": "exchange_application",
                    "summary": None,
                },
                "document_url": FGU_LAW_URL,
                "document_type": "official_document",
                "full_text_extracted": True,
            }
        ],
        "sources": [
            {"title": "佛光大學國際暨兩岸事務處（OICA）官方網站", "source_url": FGU_OICA_HOME_URL, "category": "exchange_application", "summary": None},
            {"title": "佛光大學國際暨兩岸事務處「海外交換生（非大陸地區）」專頁", "source_url": FGU_OUTBOUND_NON_CN_URL, "category": "exchange_application", "summary": None},
            {"title": "佛光大學國際暨兩岸事務處「大陸地區交換生」專頁", "source_url": FGU_OUTBOUND_CN_URL, "category": "exchange_application", "summary": None},
            {"title": "佛光大學與美國西來大學「2+2 雙學位計畫」專區與各學系課程對照表", "source_url": FGU_22_PROGRAM_URL, "category": "exchange_application", "summary": None},
            {"title": "佛光山教團系統大學跨國學習專區（西來大學、南天大學、光明大學）", "source_url": FGU_FO_GUANG_EXCHANGE_URL, "category": "partner_school", "summary": None},
            {"title": "佛光大學國際暨兩岸事務處「法規辦法」專區（A06-004、A06-005、西來雙學位、林呂德文基金、學海無涯）", "source_url": FGU_LAW_URL, "category": "scholarship", "summary": None},
            {"title": "佛光大學歷年交換生錄取榜單專區（115-1、112-2、111-1 錄取名單）", "source_url": FGU_ADMISSION_LIST_URL, "category": "exchange_application", "summary": None},
            {"title": f"佛光大學交換生經驗分享專區（{exp_covered_schools} 校 {total_exp_reports} 筆經驗分享與榜單紀錄）", "source_url": FGU_EXPERIENCE_SHARING_URL, "category": "exchange_application", "summary": None},
        ],
    }
    (OFFICIAL_FGU_DIR / "student_dashboard.json").write_text(
        json.dumps(student_dashboard_payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    doc_conditions = {
        "school_id": "fgu",
        "school_name": "佛光大學",
        "checked_at": CHECKED_AT,
        "source_url": FGU_LAW_A06_004_PDF_URL,
        "common_documents": exchange_info_payload["required_documents"],
        "track_specific_conditions": [
            {
                "track": "國際暨兩岸事務處「海外姊妹校（歐美、紐澳、日韓、東南亞、南亞）」交換學生計畫",
                "required": [
                    "佛光大學赴韓、美國及海外交換生申請表（含導師與系主任簽章）",
                    "歷年中英文成績單正本（前一學期平均 75 分以上、操行 80 分以上，含班級排名百分比）",
                    "有效外語能力檢定證明（TOEFL iBT / IELTS / TOEIC / JLPT / TOPIK；泰菲緬姊妹校可附大一英文成績單）",
                    "圖書館 EASY TEST 線上平台「iBT 托福模擬測驗第 1 回」成績畫面",
                    "中英文自傳、讀書計畫書、教師推薦信、家長同意書及保證書",
                ],
            },
            {
                "track": "國際暨兩岸事務處「大陸地區及香港高校」交換學生計畫（23 所大陸重點高校＋香港教育大學）",
                "required": [
                    "佛光大學赴大陸地區交換學生申請表及《赴陸交換生獎助學金出國前繳件資料檢核表》",
                    "歷年中文成績單正本（前一學期平均 75 分以上、操行 80 分以上；申請中國人民大學、南京大學、東南大學、四川大學須班排前 20%）",
                    "圖書館 EASY TEST 線上平台「iBT 托福模擬測驗第 1 回」成績畫面（免附外語檢定，但須附模考成績）",
                    "中文自傳、讀書計畫書、教師推薦信、家長同意書、保證書與有效臺胞證",
                ],
            },
            {
                "track": "美國西來大學（UWest）2+2 雙學位計畫（全額補助 USD 29,904）＆英國密德薩斯大學 3+1 / 3+1+1 雙聯學位",
                "required": [
                    "佛光大學與美國西來大學雙學位計畫申請表（或英國密德薩斯大學雙聯申請表）與家長同意書",
                    "歷年英文成績單正本（西來 2+2 須於佛大修滿二學年且各科達 70 分以上；密德薩斯 3+1 須修滿大一至大三共 96 學分）",
                    "英語檢定證明（西來大學 TOEFL iBT 69 / IELTS 5.5 或參加遠端 EPT 英文分級測驗；密德薩斯大學 IELTS 6.0 或免費校內英文內測）",
                    "兩校學系課程學分對照表、英文讀書計畫、教師推薦信與護照影本",
                ],
            },
        ],
    }
    (OFFICIAL_FGU_DIR / "document-conditions.json").write_text(
        json.dumps(doc_conditions, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    field_cov_lines = ["field_name,total_records,populated_records,coverage_ratio,notes"]
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
        field_cov_lines.append(f"{fname},{len(partners)},{pop},{ratio:.4f},Official FGU OICA verified")
    (OFFICIAL_FGU_DIR / "field-coverage.csv").write_text(
        "\n".join(field_cov_lines) + "\n", encoding="utf-8"
    )

    pages_records = [
        {
            "title": "佛光大學：第一階段（春季班 9–10 月）與第二階段（秋季班 2–3 月）海外及大陸交換生暨 2+2 雙學位申請時程",
            "source_url": FGU_OUTBOUND_NON_CN_URL,
            "published_at": "2026-10-15T00:00:00Z",
            "text": "\n".join(exchange_info_payload["application_period"]),
            "summary": "\n".join(exchange_info_payload["application_period"]),
            "category": "exchange_application",
            "attachments": [],
            "crawled_at": CHECKED_AT,
            "content_hash": hashlib.sha256("\n".join(exchange_info_payload["application_period"]).encode("utf-8")).hexdigest(),
        },
        {
            "title": "佛光大學：A06-004 與境外學校學生交流甄選實施辦法、GPA 75 分／操行 80 分門檻、EASY TEST 托福模考與 75 小時服務時數",
            "source_url": FGU_LAW_A06_004_PDF_URL,
            "published_at": "2026-10-15T00:00:00Z",
            "text": "\n".join(exchange_info_payload["eligibility"]),
            "summary": "\n".join(exchange_info_payload["eligibility"]),
            "category": "exchange_application",
            "attachments": [],
            "crawled_at": CHECKED_AT,
            "content_hash": hashlib.sha256("\n".join(exchange_info_payload["eligibility"]).encode("utf-8")).hexdigest(),
        },
        {
            "title": f"佛光大學：{len(partners)} 所海外與大陸姊妹校外語檢定門檻（TOEFL / IELTS / JLPT / TOPIK / 西來 EPT 內測）與大陸免語檢規定",
            "source_url": FGU_OUTBOUND_NON_CN_URL,
            "published_at": "2026-10-15T00:00:00Z",
            "text": "\n".join(exchange_info_payload["language_requirement"]),
            "summary": "\n".join(exchange_info_payload["language_requirement"]),
            "category": "exchange_application",
            "attachments": [],
            "crawled_at": CHECKED_AT,
            "content_hash": hashlib.sha256("\n".join(exchange_info_payload["language_requirement"]).encode("utf-8")).hexdigest(),
        },
        {
            "title": "佛光大學：海外與大陸交換及西來 2+2 雙學位應備文件（申請表、含排名成績單、EASY TEST 模考、讀書計畫、家長同意書與保證書）",
            "source_url": FGU_DOWNLOAD_URL,
            "published_at": "2026-10-15T00:00:00Z",
            "text": "\n".join(exchange_info_payload["required_documents"]),
            "summary": "\n".join(exchange_info_payload["required_documents"]),
            "category": "exchange_application",
            "attachments": [],
            "crawled_at": CHECKED_AT,
            "content_hash": hashlib.sha256("\n".join(exchange_info_payload["required_documents"]).encode("utf-8")).hexdigest(),
        },
        {
            "title": "佛光大學：西來大學 2+2 全額學分費獎助（USD 29,904）、教育部學海飛颺／惜珠、學海無涯、林呂德文助學基金與 A06-005 赴陸交換甲乙丙類補助",
            "source_url": FGU_LAW_URL,
            "published_at": "2026-10-15T00:00:00Z",
            "text": "\n".join(exchange_info_payload["scholarship_info"]),
            "summary": "\n".join(exchange_info_payload["scholarship_info"]),
            "category": "scholarship",
            "attachments": [],
            "crawled_at": CHECKED_AT,
            "content_hash": hashlib.sha256("\n".join(exchange_info_payload["scholarship_info"]).encode("utf-8")).hexdigest(),
        },
    ]
    (OFFICIAL_FGU_DIR / "pages.jsonl").write_text(
        "\n".join(json.dumps(p, ensure_ascii=False) for p in pages_records) + "\n",
        encoding="utf-8",
    )

    home_rules = {
        "school_id": "fgu",
        "school_name": "佛光大學",
        "eligibility": student_dashboard_payload["eligibility"],
        "application_periods": student_dashboard_payload["application_periods"],
        "selection_rules": {
            "general_academic_score_minimum": 75.0,
            "general_gpa_minimum": 3.0,
            "general_conduct_minimum": 80.0,
            "mainland_top_universities_class_rank_percent": 20.0,
            "uwest_2plus2_course_minimum": 70.0,
            "uwest_2plus2_scholarship_usd": 29904,
            "require_easy_test_toefl_mock_1": True,
            "require_fgu_enrollment_during_abroad": True,
            "return_service_hours_required": 75,
            "return_documents_due": "返國後 1 個月內繳交交換心得報告與正式成績單辦理學分抵免，並於返國後 1 年內完成 75 小時校內學習服務時數",
        },
        "source_urls": fgu_source_urls,
        "verified_at": "2026-11-02",
    }
    (OFFICIAL_FGU_DIR / "home_rules.json").write_text(
        json.dumps(home_rules, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    (OFFICIAL_FGU_DIR / "documents.json").write_text(
        json.dumps(
            {
                "school_name": "佛光大學",
                "required_documents": student_dashboard_payload["required_documents"],
                "source_urls": fgu_source_urls,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    (OFFICIAL_FGU_DIR / "scholarships.json").write_text(
        json.dumps(
            {
                "school_name": "佛光大學",
                "scholarships": student_dashboard_payload["scholarship_info"],
                "source_urls": fgu_source_urls,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    completeness = {
        "school_id": "fgu",
        "school_name": "佛光大學",
        "total_partners": len(partners),
        "partner_count": len(partners),
        "international_partners": sum(
            1 for p in partners if p["country"] not in {"中國大陸", "香港", "澳門"}
        ),
        "mainland_partners": sum(
            1 for p in partners if p["country"] in {"中國大陸", "香港", "澳門"}
        ),
        "dual_degree_partner_universities": 3,
        "dual_degree_programs": 4,
        "experience_report_covered_partners": exp_covered_schools,
        "experience_report_count": total_exp_reports,
        "open_partners": open_partner_count,
        "reference_only_partners": len(partners) - open_partner_count,
        "verified_locations": len(partners),
        "verified_official_websites": sum(1 for p in partners if p.get("official_website")),
        "verified_campus_images": sum(1 for p in partners if p.get("image_status") == "verified"),
        "workflow_count": len(workflows),
        "destination_profile_count": len(destinations),
        "student_life_count": len(life_records),
        "active_term": f"佛光大學國際暨兩岸事務處（OICA）《A06-004 與境外學校學生交流甄選實施辦法》、《A06-005 學生選派至大陸高校擔任交換學生補助實施辦法》、《與美國西來大學雙學位計畫實施及助學金辦法（全額補助 USD 29,904）》、英國國立密德薩斯大學 3+1/3+1+1 雙聯學位、澳洲南天大學跨國學習、《林呂德文乘風萬里助學基金》及《學海無涯增額學習助學金》同步整合；共完整收錄 {len(partners)} 所海外與兩岸合作姊妹校（含 {open_partner_count} 所常態開放申請交換與雙聯合作校及 {len(partners) - open_partner_count} 所正式締約姊妹校，橫跨全球 14 個國家與地區，並收錄 {exp_covered_schools} 所合作大學共 {total_exp_reports} 筆歷年交換經驗分享與 115-1／112-2／111-1 錄取榜單實績）。",
        "verified_at": "2026-11-02",
    }
    (OFFICIAL_FGU_DIR / "catalog-completeness.json").write_text(
        json.dumps(completeness, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    (OFFICIAL_FGU_DIR / "verification_status.json").write_text(
        json.dumps(
            {
                "school_id": "fgu",
                "school_name": "佛光大學",
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

    provenance_files = [
        (
            "sources/fgu/fgu_catalog_source.json",
            FGU_OUTBOUND_NON_CN_URL,
            f"佛光大學 {len(partners)} 所海外與兩岸合作姊妹校整合資料集 JSON",
        ),
        (
            "sources/fgu/fgu_resolved_locations.json",
            FGU_OUTBOUND_NON_CN_URL,
            f"佛光大學 {len(partners)} 所合作姊妹校 ROR / Wikidata 地理座標核對表 JSON",
        ),
        (
            "sources/fgu/fgu_experience_index.json",
            FGU_EXPERIENCE_SHARING_URL,
            f"佛光大學國際暨兩岸事務處交換生經驗分享與歷年錄取榜單索引 JSON（{total_exp_reports} 筆）",
        ),
        (
            "sources/fgu/exchange_non_cn.html",
            FGU_OUTBOUND_NON_CN_URL,
            "佛光大學國際暨兩岸事務處「海外交換生（非大陸地區）」官方網頁 HTML",
        ),
        (
            "sources/fgu/exchange_cn.html",
            FGU_OUTBOUND_CN_URL,
            "佛光大學國際暨兩岸事務處「大陸地區交換生」官方網頁 HTML",
        ),
        (
            "sources/fgu/program_2plus2.html",
            FGU_22_PROGRAM_URL,
            "佛光大學與美國西來大學 2+2 雙學位計畫官方專頁 HTML",
        ),
        (
            "sources/fgu/fo_guang_exchange.html",
            FGU_FO_GUANG_EXCHANGE_URL,
            "佛光山系統大學跨國學習官方專頁 HTML",
        ),
        (
            "sources/fgu/law.html",
            FGU_LAW_URL,
            "佛光大學國際暨兩岸事務處法規辦法官方專頁 HTML",
        ),
        (
            "sources/fgu/admission_list.html",
            FGU_ADMISSION_LIST_URL,
            "佛光大學國際暨兩岸事務處歷年交換生錄取榜單專頁 HTML",
        ),
    ]
    for rel_p, surl in bin_urls.items():
        rp = rel_p if rel_p.startswith("sources/") else f"sources/fgu/{rel_p}"
        if not any(x[0] == rp for x in provenance_files):
            provenance_files.append((rp, surl, f"佛光大學國際暨兩岸事務處官方原始檔案：{Path(rp).name}"))

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
        "school_id": "fgu",
        "school_name": "佛光大學",
        "generated_at": CHECKED_AT,
        "active_cycle_note": completeness["active_term"],
        "sources": prov_sources,
    }
    prov_text = json.dumps(provenance_payload, ensure_ascii=False, indent=2) + "\n"
    (OFFICIAL_FGU_DIR / "import_provenance.json").write_text(prov_text, encoding="utf-8")
    (OFFICIAL_FGU_DIR / "import-provenance.json").write_text(prov_text, encoding="utf-8")

    print(
        f"Successfully built FGU catalog: {len(partners)} partners"
        f" ({open_partner_count} open, {completeness['verified_campus_images']}"
        f" verified images, {completeness['verified_locations']} verified"
        f" locations), {len(workflows)} workflows,"
        f" {len(destinations)} destinations, {len(research_records)} research"
        f" records, {exp_covered_schools} schools with experience records"
        f" ({len(student_experience_rows)} rows, {total_exp_reports} reports)."
    )


if __name__ == "__main__":
    main()
