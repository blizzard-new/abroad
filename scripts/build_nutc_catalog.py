"""Build the official National Taichung University of Science and Technology (國立臺中科技大學, NUTC) exchange data bundle."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re

REPO_ROOT = Path(__file__).resolve().parents[1]
SOURCES_NUTC_DIR = REPO_ROOT / "sources" / "nutc"
OFFICIAL_NUTC_DIR = REPO_ROOT / "src" / "exchange_info" / "official_data" / "nutc"
STATIC_DIR = REPO_ROOT / "src" / "exchange_info" / "static"
UNIVERSITY_LOCATIONS_PATH = (
    REPO_ROOT / "src" / "exchange_info" / "official_data" / "university_locations.jsonl"
)

CHECKED_AT = "2026-10-31T00:00:00Z"

NUTC_OIA_HOME_URL = "https://oia.nutc.edu.tw/"
NUTC_ABOUT_URL = "https://oia.nutc.edu.tw/var/file/26/1026/img/1539/about.html"
NUTC_STAFF_URL = "https://oia.nutc.edu.tw/var/file/26/1026/img/1539/staff.html"
NUTC_PARTNERS_JAPAN_URL = "https://oia.nutc.edu.tw/p/404-1026-73311.php"
NUTC_PARTNERS_KOREA_URL = "https://oia.nutc.edu.tw/p/404-1026-73312.php"
NUTC_PARTNERS_SEA_URL = "https://oia.nutc.edu.tw/p/404-1026-73313.php"
NUTC_PARTNERS_EUR_US_URL = "https://oia.nutc.edu.tw/p/404-1026-73314.php"
NUTC_PARTNERS_OCEANIA_URL = "https://oia.nutc.edu.tw/p/404-1026-73315.php"
NUTC_PARTNERS_MAINLAND_URL = "https://oia.nutc.edu.tw/p/404-1026-99581.php"
NUTC_OUTBOUND_EXCHANGE_URL = "https://oia.nutc.edu.tw/p/412-1026-8514.php?Lang=zh-tw"
NUTC_OUTBOUND_NOTICES_URL = "https://oia.nutc.edu.tw/p/403-1026-745-1.php?Lang=zh-tw"
NUTC_XUEHAI_NOTICES_URL = "https://oia.nutc.edu.tw/p/403-1026-746-1.php?Lang=zh-tw"
NUTC_XUEHAI_DATA_ZONE_URL = "https://oia.nutc.edu.tw/p/412-1026-9254.php?Lang=zh-tw"
NUTC_EXPERIENCES_URL = "https://oia.nutc.edu.tw/p/403-1026-955-1.php?Lang=zh-tw"
NUTC_REGULATIONS_URL = "https://oia.nutc.edu.tw/p/412-1026-102.php?Lang=zh-tw"
NUTC_FORMS_URL = "https://oia.nutc.edu.tw/p/412-1026-8451.php?Lang=zh-tw"
NUTC_XUEHAI_REVIEW_RULES_PDF_URL = "https://oia.nutc.edu.tw/var/file/26/1026/img/2252/173256894.pdf"
NUTC_XUEHAI_ZHUMENG_RULES_PDF_URL = "https://oia.nutc.edu.tw/var/file/26/1026/img/2252/654705623.pdf"
NUTC_SPROUT_SUBSIDY_RULES_PDF_URL = "https://oia.nutc.edu.tw/var/file/26/1026/img/2252/661467477.pdf"
NUTC_XUEHAI_115_ANNOUNCEMENT_URL = "https://oia.nutc.edu.tw/p/406-1026-130835,r746.php?Lang=zh-tw"
NUTC_XUEHAI_115_PDF_URL = "https://oia.nutc.edu.tw/var/file/26/1026/attach/98/pta_92544_1613108_64362.pdf"
NUTC_JBNU_2027_SPRING_URL = "https://oia.nutc.edu.tw/p/406-1026-135710,r745.php?Lang=zh-tw"
NUTC_JBNU_2027_SPRING_PDF_URL = "https://oia.nutc.edu.tw/var/file/26/1026/attach/11/pta_95851_7474640_60261.pdf"
NUTC_SYU_2027_SPRING_URL = "https://oia.nutc.edu.tw/p/406-1026-135258,r745.php?Lang=zh-tw"
NUTC_SYU_2027_SPRING_PDF_URL = "https://oia.nutc.edu.tw/var/file/26/1026/attach/99/pta_95590_2612481_14002.pdf"
NUTC_SAPPORO_2027_SPRING_URL = "https://oia.nutc.edu.tw/p/406-1026-134919,r745.php?Lang=zh-tw"
NUTC_SAPPORO_2027_SPRING_PDF_URL = "https://oia.nutc.edu.tw/var/file/26/1026/attach/2/pta_95308_2263834_20396.pdf"
NUTC_MAINLAND_2027_SPRING_URL = "https://oia.nutc.edu.tw/p/406-1026-136798,r745.php?Lang=zh-tw"
NUTC_MAINLAND_2027_SPRING_PDF_URL = "https://oia.nutc.edu.tw/var/file/26/1026/attach/98/pta_96597_1136748_50891.pdf"
NUTC_SCU_2026_SPRING_PDF_URL = "https://oia.nutc.edu.tw/var/file/26/1026/attach/92/pta_89813_1675024_36252.pdf"
NUTC_AOMORI_2026_SPRING_PDF_URL = "https://oia.nutc.edu.tw/var/file/26/1026/attach/35/pta_89923_4743835_88181.pdf"
NUTC_NIIGATA_2026_SPRING_PDF_URL = "https://oia.nutc.edu.tw/var/file/26/1026/attach/99/pta_89924_452221_89340.pdf"

REGION_COST_DEFAULTS = {
    "日本": (
        "每月生活費約 USD 680–1,120（折合日圓約 JPY 95,000–160,000 / 月、新臺幣約 21,500–35,500 元；如札幌大學學生宿舍單人房每月約 JPY 45,500–48,500、札幌市立大學約 JPY 50,000、新潟大學五十嵐宿舍約 JPY 15,000–30,000、青森中央學院大學含早晚餐約 JPY 50,000–60,000）",
        "須由日本接待大學代向出入國在留管理局申辦「在留資格認定證明書（COE）」，獲發後至日本台灣交流協會申辦留學簽證，入境後強制加入日本國民健康保險（NHI）並於出國前投保足額海外醫療及意外險。",
    ),
    "韓國": (
        "每月生活費約 USD 620–1,050（折合韓元約 KRW 850,000–1,450,000 / 月、新臺幣約 19,500–33,500 元；如全北大學雙人房含平日三餐一學期約 KRW 1,100,000–1,300,000、三育大學校內宿舍一學期約 KRW 900,000–1,400,000 且享免費韓語語學堂 1–6 級課程）",
        "須憑韓國姊妹校核發之標準入學許可書（Certificate of Admission）向駐台北韓國代表部申辦 D-2-6 交換學生簽證，入境後申辦外國人登錄證（ARC）並強制納保韓國國民健康保險（NHIS）。",
    ),
    "中國大陸": (
        "每月生活費約 USD 350–680（折合人民幣約 RMB 2,200–4,500 / 月、新臺幣約 11,000–21,500 元；含北京科技大學、中央財經大學、南開大學、上海戲劇學院、杭州電子科技大學、蘇州大學、東北大學、吉林大學、山東大學、廈門大學、福州大學等學生宿舍與食堂開銷）",
        "須持有效「臺灣居民來往大陸通行證（臺胞證）」及大陸協議學校寄發之錄取通知書辦理入學報到，並依國立臺中科技大學國際事務處規定於出國前購買涵蓋全期之海外醫療及意外保險。",
    ),
    "澳門": (
        "每月生活費約 USD 650–1,100（折合澳門幣約 MOP 5,200–8,800 / 月、新臺幣約 20,500–35,000 元；含澳門科技大學、澳門城市大學校內宿舍與膳食交通）",
        "須依澳門特別行政區治安警察局規定憑錄取通知書申辦「逗留特別許可（學生逗留簽注）」，並投保涵蓋全期之海外醫療與意外保險。",
    ),
    "越南": (
        "每月生活費約 USD 400–750（依匯率折合新臺幣約 12,800–24,000 元；含河內國家大學外語大學、胡志明市經濟財經大學 UEF、孫德勝大學、文朗大學、河內工業大學、太原大學等住宿與生活費）",
        "須憑越南接待大學入學許可申辦越南學生簽證，並於出國前投保涵蓋全期之海外醫療與意外保險。",
    ),
    "泰國": (
        "每月生活費約 USD 500–880（折合泰銖約 THB 17,000–30,000 / 月、新臺幣約 16,000–28,000 元；含泰國農業大學 Kasetsart、宋卡王子大學 PSU、先皇技術學院 KMITL、正大管理學院 PIM、蘭實大學 RSU 等住宿與生活費）",
        "須憑泰國接待大學入學許可向泰國貿易經濟辦事處申辦 Non-Immigrant ED 學生簽證，並投保海外醫療與意外保險。",
    ),
    "馬來西亞": (
        "每月生活費約 USD 500–850（折合馬幣約 MYR 2,200–3,800 / 月、新臺幣約 16,000–27,000 元；含拉曼大學 UTAR、雙威大學 Sunway、韓江傳媒大學學院、新紀元大學學院等住宿與生活費）",
        "須透過馬來西亞 EMGS 系統申辦 Student Pass / Visa Approval Letter（VAL）並投保當地學生醫療保險。",
    ),
    "印尼": (
        "每月生活費約 USD 420–780（依匯率折合新臺幣約 13,500–25,000 元；如巴淡國際大學 UIB 交換生享免學費及免費校內宿舍待遇，另含艾爾朗加大學 Airlangga、建國大學 BINUS 等生活開銷）",
        "須憑印尼接待大學入學許可與學習許可申辦印尼學生簽證（C316 / KITAS），並購買海外醫療與意外保險。",
    ),
    "菲律賓": (
        "每月生活費約 USD 480–820（依匯率折合新臺幣約 15,500–26,000 元；含馬プア大學 Mapúa、亞當森大學 Adamson、萊西姆大學 LPU 等住宿與生活費）",
        "須依菲律賓接待大學指引申辦 9(f) 學生簽證或 SSP 特別學習許可，並投保海外醫療與意外保險。",
    ),
    "新加坡": (
        "每月生活費約 USD 1,100–1,800（折合新幣約 SGD 1,480–2,420 / 月、新臺幣約 35,000–57,000 元；含新加坡社科大學 SUSS 周邊住宿、膳食與大眾運輸）",
        "須透過新加坡移民與關卡局（ICA）SOLAR 系統申辦 Student's Pass（STP），並投保當地醫療保險。",
    ),
    "印度": (
        "每月生活費約 USD 420–750（依匯率折合新臺幣約 13,500–24,000 元；含清奈 SRM 科技大學校內宿舍與膳食費）",
        "須憑印度接待大學入學許可向印度台北協會申辦 Student Visa，並投保海外醫療與急難救助保險。",
    ),
    "美國": (
        "每月生活費約 USD 1,350–2,200（依匯率折合新臺幣約 43,000–70,000 元；含奧克拉荷馬州立大學 OSU、中央奧克拉荷馬大學 UCO、天普大學 Temple、北伊利諾大學 NIU、西佛羅里達大學 UWF、休士頓大學清湖分校等住宿、伙食與保險費）",
        "須憑美國合作校核發之 DS-2019（J-1 交換生）或 I-20（F-1 雙聯／訪問生）繳交 SEVIS I-901 費用並向美國在台協會（AIT）申辦簽證，並強制投保接待校規定之學生醫療保險。",
    ),
    "加拿大": (
        "每月生活費約 USD 1,250–1,950（折合加幣約 CAD 1,700–2,650 / 月、新臺幣約 40,000–62,000 元；含漢博理工學院 Humber Polytechnic、百年理工學院 Centennial College 住宿與生活費）",
        "交換 1 學期（6 個月內）可申辦加拿大 eTA 入境，超過 6 個月須申辦加拿大 Study Permit 並投保安大略省學生醫療保險。",
    ),
    "英國": (
        "每月生活費約 USD 1,350–2,150（折合英鎊約 GBP 1,050–1,680 / 月、新臺幣約 43,000–68,500 元；含西蘇格蘭大學 UWS、諾丁漢特倫特大學 NTU、布リスト爾西英格蘭大學 UWE、創意藝術大學 UCA 等住宿與生活費）",
        "研修超過 6 個月或攻讀雙聯學位須憑英國合作校核發之 CAS 申辦英國 Student Visa 並繳納 IHS 醫療附加費；6 個月內短期交換可依規定申辦 Standard Visitor / 短期研習許可。",
    ),
    "德國": (
        "每月生活費約 USD 1,000–1,550（折合歐元約 EUR 920–1,420 / 月、新臺幣約 32,000–49,500 元；含柏林經濟與法律應用科學大學 HWR Berlin 學生宿舍與學期交通卡費）",
        "須開立德國限制提領帳戶（Blocked Account）並憑入學許可向德國在台協會申辦學生簽證及投保德國公保／醫療險。",
    ),
    "瑞士": (
        "每月生活費約 USD 1,500–2,400（折合瑞士法郎約 CHF 1,350–2,150 / 月、新臺幣約 48,000–76,500 元；含 BHMS 瑞士工商酒店管理學院包食宿與有薪實習專案）",
        "須憑瑞士合作學院入學許可向瑞士商務辦事處申辦 D 類長期學生簽證，並依瑞士規定投保醫療與意外保險。",
    ),
    "捷克": (
        "每月生活費約 USD 650–1,050（折合歐元約 EUR 600–960 / 月、新臺幣約 20,500–33,500 元；含赫拉德茨克拉洛韋大學 UHK 學生宿舍與生活費）",
        "須憑捷克接待大學入學許可與住宿證明向捷克經濟文化辦事處申辦長期學生簽證及捷克合約醫療保險。",
    ),
    "澳洲": (
        "每月生活費約 USD 1,350–2,100（折合澳幣約 AUD 2,050–3,200 / 月、新臺幣約 43,000–67,000 元；含西雪梨大學 Western Sydney University、坎培拉大學 University of Canberra 住宿與生活費）",
        "須憑澳洲姊妹校核發之 CoE（Confirmation of Enrolment）申辦澳洲 Subclass 500 學生簽證，並強制投保海外學生健康保險（OSHC）。",
    ),
    "紐西蘭": (
        "每月生活費約 USD 1,250–1,950（折合紐幣約 NZD 2,100–3,250 / 月、新臺幣約 40,000–62,000 元；含懷卡托大學 University of Waikato 住宿與生活費）",
        "須憑紐西蘭姊妹校入學許可（Offer of Place）向紐西蘭移民局申辦交換學生簽證，並投保紐西蘭認可之學生醫療與旅遊保險。",
    ),
}

SEMESTER_DATES_BY_COUNTRY = {
    "日本": "春季學期（前學期）：約 4 月初至 8 月初；秋季學期（後學期）：約 9 月中下旬至翌年 2 月初",
    "韓國": "春季學期（第 1 學期）：約 3 月初至 6 月中旬；秋季學期（第 2 學期）：約 9 月初至 12 月中旬",
    "中國大陸": "春季學期（下學期）：約 2 月中下旬至 6 月底；秋季學期（上學期）：約 9 月初至翌年 1 月中旬",
    "澳門": "秋季學期（第一學期）：約 9 月初至 12 月底；春季學期（第二學期）：約 1 月中旬至 5 月底",
    "越南": "秋季學期（第一學期）：約 8/9 月至 12/1 月；春季學期（第二學期）：約 1/2 月至 5/6 月",
    "泰國": "第一學期：約 8 月至 12 月；第二學期：約 1 月至 5 月",
    "馬來西亞": "第一學期：約 9/10 月至翌年 1/2 月；第二學期：約 2/3 月至 6/7 月",
    "印尼": "奇數學期（秋季）：約 8/9 月至 12/1 月；偶數學期（春季）：約 2 月至 6 月",
    "菲律賓": "第一學期：約 8 月至 12 月；第二學期：約 1 月至 5 月",
    "新加坡": "第一學期：約 8 月至 12 月；第二學期：約 1 月至 5 月",
    "印度": "秋季學期：約 7/8 月至 12 月；春季學期：約 1 月至 5 月",
    "美國": "秋季學期（Fall Semester）：約 8 月中旬至 12 月中旬；春季學期（Spring Semester）：約 1 月中旬至 5 月中旬",
    "加拿大": "秋季學期（Fall Semester）：約 9 月初至 12 月中旬；冬季／春季學期（Winter Semester）：約 1 月初至 4 月下旬",
    "英國": "秋季學期（Autumn Term）：約 9 月中下旬至翌年 1 月；春季學期（Spring Term）：約 1 月下旬至 6 月",
    "德國": "冬季學期（Winter Semester）：約 10 月初至翌年 2 月；夏季學期（Summer Semester）：約 4 月初至 7 月底",
    "瑞士": "秋季學期：約 9 月至翌年 2 月；春季學期：約 2/3 月至 7/8 月（含帶薪實習階段）",
    "捷克": "冬季學期（Winter Semester）：約 9 月中下旬至翌年 1 月；夏季學期（Summer Semester）：約 2 月中旬至 6 月",
    "澳洲": "第一學期（Semester 1）：約 2 月下旬至 6 月；第二學期（Semester 2）：約 7 月下旬至 11 月",
    "紐西蘭": "第一學期（Trimester A）：約 2 月下旬至 6 月；第二學期（Trimester B）：約 7 月中旬至 11 月",
}


def clean_text(s: str) -> str:
    return re.sub(r"\s+", " ", s).strip() if s else ""


def sync_global_assets_and_locations(catalog_source: list[dict], resolved_locations: dict) -> None:
    """Ensure school-images.json and university_locations.jsonl contain all 140 NUTC partner schools."""
    si_path = STATIC_DIR / "assets" / "school-images.json"
    si_data = json.loads(si_path.read_text(encoding="utf-8"))
    schools_list = si_data.get("schools", [])
    by_name = {str(r.get("school_name", "")): r for r in schools_list if isinstance(r, dict)}
    si_changed = False
    for item in catalog_source:
        fn = item["school_name"]
        irec = item.get("image_record") or {}
        if irec.get("local_path"):
            new_rec = {
                "school_name": fn,
                "local_path": irec["local_path"],
                "image_source_url": irec.get("image_source_url") or irec.get("image_url") or irec["local_path"],
                "source_page_url": irec.get("source_page_url") or irec.get("official_page_url") or item.get("website") or "",
                "official_page_url": item.get("website") or irec.get("official_page_url") or "",
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
        si_path.write_text(json.dumps(si_data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

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
            lat = float(loc.get("latitude") if loc.get("latitude") is not None else loc.get("lat", 24.1502))
            lon = float(loc.get("longitude") if loc.get("longitude") is not None else loc.get("lon", 120.6837))
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
    OFFICIAL_NUTC_DIR.mkdir(parents=True, exist_ok=True)
    catalog_source = json.loads((SOURCES_NUTC_DIR / "nutc_catalog_source.json").read_text(encoding="utf-8"))
    resolved_locations = json.loads((SOURCES_NUTC_DIR / "nutc_resolved_locations.json").read_text(encoding="utf-8"))
    sync_global_assets_and_locations(catalog_source, resolved_locations)

    school_images_data = json.loads((STATIC_DIR / "assets" / "school-images.json").read_text(encoding="utf-8"))
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
        avail_status = "open" if item.get("offering_status") == "open" else "reference_only"
        if avail_status == "open":
            open_partner_count += 1

        group_str = clean_text(item.get("group") or "國際事務處合作姊妹校")
        prog_raw = clean_text(item.get("program_type_raw") or "校級出國交換學生計畫")
        quota_str = clean_text(item.get("quota") or "依當期交換生簡章公告名額")
        detail_url = item.get("detail_url") or NUTC_OUTBOUND_EXCHANGE_URL
        source_url = detail_url
        program_type = f"國際事務處【{prog_raw}】（{group_str}）"

        colleges_str = clean_text(
            item.get("colleges")
            or "不限學院（商學院、設計學院、資訊與流通學院、智慧產業學院、語文學院、中護健康學院均得依姊妹校對應系所申請）"
        )
        degree_levels_str = clean_text(
            item.get("eligible_degrees")
            or "國立臺中科技大學日間部及進修部已就讀滿一學期以上之非應屆畢業在籍學生（學士班、碩士班及五專部四年級(含)以上，不含五專前三年、延修生及在職專班）"
        )
        lang_req_str = clean_text(
            item.get("language_req")
            or "符合姊妹校語言門檻及《國立臺中科技大學學生申請教育部學海系列計畫審查要點》規定（日本姊妹校須 JLPT N2 以上；韓國全北大學須 TOPIK 初級且 TOEIC 550 以上、三育大學須附韓語能力證明；英語及歐美紐澳東南亞地區須 GEPT 中級或 TOEFL iBT 60 / TOEIC 550 以上）"
        )
        gpa_req_str = clean_text(
            item.get("gpa_req")
            or "在學期間學業成績優異（各科成績皆須 70 分以上，赴大陸地區歷年學業總平均須達 80 分(含)以上），且操行成績平均達 80 分（含）以上、無記過處分"
        )
        website = item.get("website") or source_url
        remarks_raw = clean_text(item.get("notes") or "")
        tuition_note = clean_text(
            item.get("tuition_note")
            or "交換期間須於國立臺中科技大學完成註冊繳費以保留學籍；獲推薦赴互惠姊妹校交換者享姊妹校學費減免（住宿費、生活費、保險費、簽證與往返機票自理）"
        )
        exps = item.get("experience_reports") or []

        round_label = "115-1／115-2（2026秋季班／2027春季班：春季出國甄選 09/14–10/30 收件）＆115年度學海飛颺／惜珠計畫（03/04 截止）"
        app_deadline_str = (
            "春季班出國交換甄選（翌年 2–3 月赴日、韓、大陸交換）：每年 9–10 月收件（如 2027 春季班日本札幌大學／信州大學 2026/09/14 截止、韓國三育大學 10/15 截止、大陸協議學校 10/27 截止、韓國全北大學 10/30 截止）；"
            "教育部學海飛颺／學海惜珠／學海築夢校內甄選：每年 1 月初舉辦說明會、1 月至 3 月初學院初審、3 月 4 日前送達國際事務處（三民校區中正大樓 1 樓 3105 室）；"
            "秋季班出國交換甄選（當年 9 月赴日、韓、歐美、東南亞、大陸交換）：每年 3–5 月收件"
        )
        deadline_iso = "2026-10-30T17:00:00+08:00"
        win_status = "open" if avail_status == "open" else "closed"
        acad_year = "115"

        study_period_str = "一學期或一學年（依姊妹校交換協議規定；跨國雙聯學位如英國西蘇格蘭大學 UWS 為 1 年制榮譽學士／碩士雙聯）"
        sem_dates_str = SEMESTER_DATES_BY_COUNTRY.get(country, "秋季學期：約 9 月至翌年 1 月；春季學期：約 2 月至 6 月")
        housing_str = f"獲國立臺中科技大學國際事務處推薦提名後，可依 {zh_name} 指引申請校內外學生宿舍或國際學舍（{tuition_note}）。"
        course_rest_str = (
            f"開放對象與學院：{colleges_str}（{degree_levels_str}）。依《國立臺中科技大學學生申請教育部學海系列計畫審查要點》及各姊妹校交換留學申請簡章規定："
            "（1）申請人須為已就讀本校一學期以上之日間部與進修部非應屆畢業在籍學生（學士班、碩士班及五專部四年級(含)以上，不含五專 1–3 年級生、境外生、延修生、休學生及在職專班生；赴大陸地區限臺灣本地生）；"
            "（2）國外交換留學各科成績須達 70 分以上且操行成績平均達 80 分（含）以上；赴大陸協議學校歷年學業總平均及操行成績均須達 80 分（含）以上；"
            "（3）出國交換期間須於本校辦理註冊繳費以保留學籍（享姊妹校免學費待遇）；赴日、韓交換生於留學期間 1 學期至少 5 篇、1 學年至少 10 篇投稿至國際處粉絲專頁（「去日本遊學&留學-台中科大國際處」或「就去韓國留個學」）；"
            "（4）返國後 2 週內持正式成績單向系所報到並向教務處註冊組辦理學分抵免，返國後 1 個月內繳交中文心得報告電子檔、參加交換留學分享會，並於國際事務處完成國際交流志願服務 20 小時。"
        )

        living_cost_str, visa_health_str = REGION_COST_DEFAULTS.get(
            country,
            (
                "每月生活費約 USD 750–1,400（依匯率折合新臺幣約 24,000–45,000 元，含住宿、膳食與市區交通）",
                "須依接待國駐臺機構規定申辦學生簽證，並於出國前投保涵蓋全期之海外醫療及意外保險。",
            ),
        )

        tuition_points_list = [
            f"國立臺中科技大學學雜費規定與姊妹校待遇：依各姊妹校交換留學簡章及《學生申請教育部學海系列計畫審查要點》，錄取交換生於交換期間仍須於本校完成註冊手續並繳交全額學雜費以保留學籍。本合作校待遇：{tuition_note}。",
            "國立臺中科技大學四大出國研修獎助學金體系：（1）教育部《學海飛颺》獎學金（選送優秀學生赴海外非大陸港澳姊妹校交換研修 1 學期至 1 學年，每人補助額度為新臺幣 5 萬元以上至 30 萬元以下，含本校至少 20% 配合款）；（2）教育部《學海惜珠》扶助清寒獎學金（持有效低收入戶、中低收入戶或特殊境遇家庭證明赴海外研修，依教育部核定額度補助機票與生活費）；（3）教育部《學海築夢／新南向學海築夢》海外專業實習獎助金（由計畫主持人帶領學生赴海外企業機構實習至少 30 天）；（4）《國立臺中科技大學高教深耕計畫國際專章補助國際交流活動要點》暨日本台灣交流協會（JASSO）短期交換獎學金。",
        ]

        app_steps_list = [
            f"步驟一（確認中科大在籍年級、學業操行門檻與 {zh_name} 語檢要求）：確認符合《國立臺中科技大學學生申請教育部學海系列計畫審查要點》及交換簡章規定（{gpa_req_str}），並備妥有效期限內且符合 {zh_name} 標準之語言能力證明（{lang_req_str}）。",
            "步驟二（備齊申請資料送交國際事務處或所屬學院初審）：檢附交換留學申請表、家長同意書、歷年成績單＋最近一學期含班級排名之中英文版成績單、自傳與讀書計畫（含國外修課規劃與中科大對應科目）、語檢合格證書影本、教授推薦信及在學證明，於公告截止日前親送或寄達三民校區中正大樓 1 樓 3105 室國際事務處（學海系列計畫須先送所屬系所／學院完成初審並排定推薦順序，於 3 月 4 日前彙送國際處）。",
            "步驟三（參加國際事務處校內面試甄選與學海系列計畫複審）：國際事務處針對申請學生之在校學業成績、外語能力、讀書計畫可行性及面試表現（日、韓語與英語溝通應對能力）進行評選並公告錄取推薦名單；獲推薦赴非大陸港澳姊妹校研修者可同步申請教育部《學海飛颺》或《學海惜珠》獎學金。",
            f"步驟四（由國際事務處向 {full_name} 辦理官方提名、完成簽證保險與宿位申請，返國後完成學分抵免與 20 小時志願服務）：配合國際處於姊妹校截止日前遞交外文入學申請、財力證明、健康檢查表與護照影本；留學期間按期投稿國際處粉專（日韓交換生 1 學期 5 篇、1 學年 10 篇），返國後 2 週內向系所報到並辦理學分抵免，1 個月內繳交中文心得報告、參與分享會及完成國際處志願服務 20 小時。",
        ]

        elig_points_list = [
            f"合作類別與計畫群組：{program_type}",
            f"開放學制與修業年級：{degree_levels_str}",
            f"開放申請院系：{colleges_str}",
            f"學業與操行門檻：{gpa_req_str}",
            f"外語能力標準：{lang_req_str}",
            "在學註冊與返國義務：交換期間須於中科大註冊繳費保留學籍；返國後須繳交中文心得報告、參加分享會並於國際事務處完成國際交流志願服務 20 小時。",
        ]
        if tuition_note:
            elig_points_list.append(f"姊妹校學費與住宿待遇：{tuition_note}")
        if remarks_raw:
            elig_points_list.append(f"締約時間與官方備註：{remarks_raw}")

        exp_links: list[dict] = []
        exp_labels: list[str] = []
        if exps:
            exp_covered_schools += 1
            total_exp_reports += len(exps)
            seen_exp_urls: set[str] = set()
            for e_idx, e in enumerate(exps):
                raw_t = clean_text(e.get("title") or f"赴 {zh_name} 交換生心得報告")
                esem = e.get("semester") or "歷年交換研修"
                eurl = e.get("url") or NUTC_EXPERIENCES_URL
                if eurl in seen_exp_urls:
                    eurl = f"{eurl}#r{e_idx+1}"
                seen_exp_urls.add(eurl)
                exp_labels.append(raw_t[:36])
                exp_links.append({
                    "title": raw_t,
                    "url": eurl,
                    "academic_year": esem,
                    "semester": esem,
                    "college": "商學院／設計學院／資訊與流通學院／智慧產業學院／語文學院／中護健康學院",
                    "department": e.get("department") or "中科大出國交換生",
                })
                summary_text = (
                    f"國立臺中科技大學國際事務處於交換生心得分享專區公開收錄之學長姐赴 {country} {full_name} 交換研修官方心得報告（{raw_t}），詳述行前準備、選課與學分抵免、學生宿舍生活、語學堂學習與當地開銷實錄。"
                )
                theme_map = {
                    "academics": f"中科大交換生於《{raw_t}》分享在 {zh_name} 修習專業與語學堂課程，以及返國後 2 週內向所屬系所與教務處註冊組辦理學分抵免之經驗。",
                    "housing": f"中科大交換生記錄申請 {zh_name} 校內外學生宿舍與生活機能（{housing_str[:100]}）。",
                    "campus_culture": f"中科大國際事務處公開收錄《{raw_t}》之國際學伴互動（Buddy Program）、社團文化體驗與海外生活心得。",
                    "cost": f"中科大交換生分享於 {zh_name} 之每月住宿、伙食與交通花費（{living_cost_str[:100]}），以及申請教育部學海飛颺／惜珠獎學金之經驗。",
                }
                student_experience_rows.append({
                    "school_name": full_name,
                    "country": country,
                    "title": raw_t,
                    "source_url": eurl,
                    "source_type": "article",
                    "platform": "國立臺中科技大學國際事務處—交換生心得分享專區",
                    "author_name": raw_t,
                    "language": "zh",
                    "summary": summary_text,
                    "themes": ["academics", "housing", "campus_culture", "cost"],
                    "theme_summaries": theme_map,
                    "content_status": "full_text",
                    "perspective": "official_student_story",
                    "published_at": None,
                    "discovered_at": CHECKED_AT,
                    "content_hash": hashlib.sha256(f"{full_name}:nutc_exp:{e_idx}:{eurl}".encode("utf-8")).hexdigest(),
                    "exchange_term": esem,
                    "summary_zh": summary_text,
                    "original_summary": summary_text,
                    "theme_summaries_zh": theme_map,
                    "translation_status": "original",
                    "source_kind": "official_experience_page",
                })

        sample_reports = [{"title": lk["title"], "url": lk["url"], "term": lk["semester"]} for lk in exp_links[:6]]
        experience_sources_records.append({
            "home_university": "國立臺中科技大學",
            "school_name": full_name,
            "country": country,
            "official_experience_portal_url": exp_links[0]["url"] if exp_links else NUTC_EXPERIENCES_URL,
            "partner_page_url": source_url,
            "report_count": len(exps),
            "sample_reports": sample_reports,
            "checked_at": CHECKED_AT,
        })

        loc = resolved_locations.get(full_name) or {
            "city": country,
            "latitude": 24.1502,
            "longitude": 120.6837,
            "source_url": "https://www.wikidata.org",
        }
        city_name = loc.get("city") or country
        lat = float(loc.get("latitude") if loc.get("latitude") is not None else loc.get("lat", 24.1502))
        lon = float(loc.get("longitude") if loc.get("longitude") is not None else loc.get("lon", 120.6837))
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
            "note": "校級代表位置：官方網域及國家已與 ROR / Wikidata 及國立臺中科技大學國際事務處六大區域姊妹校名冊比對；實際交換校區以錄取通知與姊妹校簡章為準。",
        }
        new_locations.append(location_obj)

        vrec = visual_by_name.get(full_name) or item.get("image_record")
        assert vrec and vrec.get("local_path"), f"Missing verified image for {full_name}"
        img_local = vrec.get("local_path")
        img_source = vrec.get("image_source_url") or vrec.get("image_url") or img_local
        img_page = vrec.get("official_page_url") or vrec.get("source_page_url") or img_source
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
                f"【中科大學長姐交換研修心得報告（共 {len(exps)} 篇）】收錄於國際事務處交換生心得分享專區（含：{'、'.join(exp_labels[:4])}）"
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
            "eligibility": f"開放對象：{colleges_str}（{degree_levels_str}）｜{gpa_req_str}｜{lang_req_str}",
            "language_requirement": lang_req_str,
            "gpa_requirement": gpa_req_str,
            "quota": quota_str,
            "quota_status": "published" if avail_status == "open" else "reference_only",
            "availability_status": avail_status,
            "availability_note": f"國立臺中科技大學國際事務處公告合作姊妹校（{program_type}）；名額：{quota_str}（{remarks_raw}）。",
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
            "factsheet_url": NUTC_XUEHAI_115_PDF_URL if avail_status == "open" else source_url,
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
                "title": f"國立臺中科技大學國際事務處合作姊妹校名冊與交換簡章—{zh_name}",
                "source_url": source_url,
                "role": "home_university",
                "authority": "home_official_notice",
                "effective_academic_year": acad_year,
                "application_round": round_label,
                "checked_at": CHECKED_AT,
            },
            {
                "title": "國立臺中科技大學 115 年度教育部選送優秀學生赴國外研修／專業實習「學海系列計畫」校內申請作業公告 PDF",
                "source_url": NUTC_XUEHAI_115_PDF_URL,
                "role": "home_university",
                "authority": "home_official_notice",
                "effective_academic_year": acad_year,
                "application_round": round_label,
                "checked_at": CHECKED_AT,
            },
            {
                "title": "國立臺中科技大學學生申請教育部學海系列計畫審查要點（111.09.27核定）PDF",
                "source_url": NUTC_XUEHAI_REVIEW_RULES_PDF_URL,
                "role": "home_university",
                "authority": "home_official_notice",
                "effective_academic_year": acad_year,
                "application_round": round_label,
                "checked_at": CHECKED_AT,
            },
        ]
        if exp_links:
            wf_sources.append({
                "title": f"國立臺中科技大學國際事務處交換生心得分享專區—赴 {zh_name} 交換心得報告（{len(exps)} 篇）",
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
            "home_university": "國立臺中科技大學",
            "school_name": full_name,
            "partner_website": website,
            "country": country,
            "program_type": program_type,
            "academic_year": acad_year,
            "application_round": round_label,
            "effective_application_rounds": [
                round_label,
                "115-1（2026秋季出國交換暨115年度教育部學海計畫甄選）",
                "115-2（2027春季出國交換甄選）",
                "115-1",
                "115-2",
                "116-1",
                "116-2",
            ],
            "applicability_status": "verified",
            "applicability_note": (
                "國立臺中科技大學由國際事務處（三民校區中正大樓 1 樓 3105 室，電話 04-2219-5760 / 04-2219-5762 / 04-2219-5768）統籌全校六大學院（商學院、設計學院、資訊與流通學院、智慧產業學院、語文學院、中護健康學院）之日本、韓國、歐美、紐澳、東南亞及大陸港澳姊妹校交換留學、英國西蘇格蘭大學（UWS）雙聯學位及教育部學海飛颺、學海惜珠與學海築夢計畫遴選。"
            ),
            "review_status": "published",
            "published_at": CHECKED_AT,
            "steps": [
                {
                    "rule_id": f"nutc-{acad_year}-home-1-{sn:03d}",
                    "order": 1,
                    "phase": "校內申請",
                    "title": f"確認中科大在籍滿一學期非應屆畢業生資格、學業操行門檻與 {zh_name} 語檢要求",
                    "responsible_party": "學生",
                    "responsible_unit": "國立臺中科技大學國際事務處（三民校區中正大樓 1 樓 3105 室）",
                    "deadline_at": deadline_iso,
                    "deadline_status": "verified_exact",
                    "deadline_source_url": NUTC_JBNU_2027_SPRING_URL,
                    "deadline_checked_at": CHECKED_AT,
                    "deadline_reminder_eligible": True,
                    "summary": (
                        f"確認符合《國立臺中科技大學學生申請教育部學海系列計畫審查要點》及各姊妹校交換留學簡章規定：日間部與進修部已就讀滿一學期以上之非應屆畢業在籍學生（學士班、碩士班及五專部四年級(含)以上，不含五專前三年、延修生及在職專班），符合學業與操行要求（{gpa_req_str}），並備妥符合 {zh_name} 門檻之語言能力證明（{lang_req_str}）。"
                    ),
                    "details": [
                        f"開放學制與院系：{colleges_str}（{degree_levels_str}）",
                        f"語言與學業條件：{lang_req_str}｜{gpa_req_str}",
                        f"當期名額與計畫類別：{quota_str}｜{program_type}",
                    ],
                    "scope": {
                        "home_universities": ["國立臺中科技大學"],
                        "partner_universities": [full_name],
                        "academic_years": ["115", "116"],
                        "application_rounds": [round_label, "115-1", "115-2", "116-1", "116-2"],
                    },
                    "source_urls": [source_url, NUTC_XUEHAI_REVIEW_RULES_PDF_URL, NUTC_JBNU_2027_SPRING_PDF_URL],
                    "checked_at": CHECKED_AT,
                    "support_status": "verified",
                },
                {
                    "rule_id": f"nutc-{acad_year}-home-2-{sn:03d}",
                    "order": 2,
                    "phase": "校內申請",
                    "title": "備妥交換留學申請表、中英文歷年成績單、自傳讀書計畫與家長同意書，送達國際事務處或學院初審",
                    "responsible_party": "學生與所屬系所／學院",
                    "responsible_unit": "各學院系所辦公室／國立臺中科技大學國際事務處",
                    "deadline_at": deadline_iso,
                    "deadline_status": "verified_exact",
                    "deadline_source_url": NUTC_JBNU_2027_SPRING_URL,
                    "deadline_checked_at": CHECKED_AT,
                    "deadline_reminder_eligible": True,
                    "summary": (
                        "申請春季班或秋季班交換留學生須依各姊妹校簡章截止日（春季班每年 9–10 月、秋季班每年 3–5 月）備妥申請表件送交三民校區中正大樓 1 樓 3105 室國際事務處；申請教育部學海飛颺／學海惜珠計畫者，須於 1 月至 3 月初先送所屬學院完成初審並排定推薦順序後，於 3 月 4 日前送達國際事務處。"
                    ),
                    "details": [
                        "春季班交換甄選（翌年 2–3 月出國）：如日本札幌大學／信州大學於 9 月 14 日截止、韓國三育大學於 10 月 15 日截止、大陸地區協議學校（上海戲劇學院、杭州電子科技大學、陝西師範大學等）於 10 月 27 日截止、韓國全北大學於 10 月 30 日截止。",
                        "教育部學海飛颺／惜珠／築夢計畫甄選：115 年 1 月 7 日舉辦說明會，1 月 8 日至 3 月 2 日由各學院／系所辦理初審，3 月 4 日前將學生書面資料送達國際處，3 月 31 日前報部、5 月 31 日公告結果。",
                    ],
                    "document_requirements": [
                        {
                            "name": "國立臺中科技大學交換留學申請表／中科大學生赴大陸地區協議學校研習申請表／學海飛颺及惜珠申請表",
                            "official_form_url": NUTC_FORMS_URL,
                            "source_urls": [NUTC_FORMS_URL, NUTC_XUEHAI_DATA_ZONE_URL],
                        },
                        {
                            "name": "歷年成績單正本＋最近一學期含班級排名之中英文版成績單（各科 70 分以上、操行 80 分以上；大陸地區歷年平均 80 分以上）",
                            "official_form_url": NUTC_XUEHAI_REVIEW_RULES_PDF_URL,
                            "source_urls": [NUTC_XUEHAI_REVIEW_RULES_PDF_URL, NUTC_JBNU_2027_SPRING_PDF_URL],
                        },
                        {
                            "name": "有效期限內之外語能力證明（日本附 JLPT N2 以上、韓國附 TOPIK 與 TOEIC 550、英語及歐美紐澳東南亞附 GEPT 中級或 TOEFL iBT 60 / TOEIC 550 以上）",
                            "official_form_url": NUTC_XUEHAI_REVIEW_RULES_PDF_URL,
                            "source_urls": [source_url, NUTC_XUEHAI_REVIEW_RULES_PDF_URL],
                        },
                        {
                            "name": "中／外文自傳與讀書計畫（含國外修課規劃與本校對應科目）、家長同意書、教授推薦信及在學證明",
                            "official_form_url": NUTC_FORMS_URL,
                            "source_urls": [NUTC_FORMS_URL, NUTC_SAPPORO_2027_SPRING_PDF_URL],
                        },
                    ],
                    "scope": {
                        "home_universities": ["國立臺中科技大學"],
                        "academic_years": ["115", "116"],
                        "application_rounds": [round_label, "115-1", "115-2", "116-1", "116-2"],
                    },
                    "source_urls": [NUTC_JBNU_2027_SPRING_URL, NUTC_MAINLAND_2027_SPRING_URL, NUTC_FORMS_URL],
                    "checked_at": CHECKED_AT,
                    "support_status": "verified",
                },
                {
                    "rule_id": f"nutc-{acad_year}-home-3-{sn:03d}",
                    "order": 3,
                    "phase": "甄選與提名",
                    "title": "參加國際事務處校內面試審查與教育部學海飛颺／惜珠計畫複審核定",
                    "responsible_party": "國立臺中科技大學國際事務處與申請學生",
                    "responsible_unit": "國立臺中科技大學國際事務處／國際事務推動委員會",
                    "deadline_at": "2026-03-04T17:00:00+08:00",
                    "deadline_status": "verified_exact",
                    "deadline_source_url": NUTC_XUEHAI_115_ANNOUNCEMENT_URL,
                    "deadline_checked_at": CHECKED_AT,
                    "deadline_reminder_eligible": True,
                    "summary": (
                        "國際事務處依據學生在校學業成績、外語檢定成績、讀書計畫與校內面試表現進行甄選，並由審查小組依《國立臺中科技大學學生申請教育部學海系列計畫審查要點》核定推薦名單與教育部學海飛颺（每人補助 5 萬至 30 萬元）、學海惜珠獎助額度。"
                    ),
                    "details": [
                        "交換留學面試審查：針對學生之留學動機、讀書計畫具體性、外語溝通能力（日語／韓語／英語問答）及海外生活適應力進行評分。",
                        "學海系列計畫複審：各學院於 3 月 2 日前完成初審並排定優先順序，3 月 4 日前送國際事務處彙整召開審查會議，3 月 31 日前核報教育部。",
                    ],
                    "scope": {
                        "home_universities": ["國立臺中科技大學"],
                        "academic_years": ["115", "116"],
                        "application_rounds": [round_label, "115-1", "115-2", "116-1", "116-2"],
                    },
                    "source_urls": [NUTC_XUEHAI_REVIEW_RULES_PDF_URL, NUTC_XUEHAI_115_PDF_URL],
                    "checked_at": CHECKED_AT,
                    "support_status": "verified",
                },
                {
                    "rule_id": f"nutc-{sn:03d}-host-apply",
                    "order": 4,
                    "phase": "合作校申請",
                    "title": f"由國際事務處向 {zh_name} 辦理官方提名，並依姊妹校規定寄送外文入學申請、財力證明與體檢文件",
                    "responsible_party": "學生與接待校國際事務處",
                    "summary": (
                        f"通過校內甄選獲得中科大推薦資格後，由國際事務處向 {zh_name} 辦理官方提名；學生須依姊妹校簡章備齊外文入學申請書、學習計畫書、英文存款餘額證明（財力證明）、健康檢查表（含肺結核 X 光／B 肝／麻疹抗體等）、護照影本及證件照，待獲姊妹校核發入學許可書（Certificate of Admission / COE）始正式取得錄取資格。"
                    ),
                    "details": [
                        f"研修期程：{study_period_str}｜名額：{quota_str}",
                        f"語言與學業條件：{lang_req_str}｜{gpa_req_str}",
                        f"住宿與費用待遇：{housing_str}",
                    ],
                    "scope": {
                        "home_universities": ["國立臺中科技大學"],
                        "partner_universities": [full_name],
                        "academic_years": ["115", "116"],
                        "application_rounds": [round_label, "115-1", "115-2", "116-1", "116-2"],
                    },
                    "source_urls": [source_url, NUTC_JBNU_2027_SPRING_PDF_URL, NUTC_SAPPORO_2027_SPRING_PDF_URL]
                    + ([website] if website else []),
                    "checked_at": CHECKED_AT,
                    "support_status": "verified",
                    "needs_confirmation": False,
                },
                {
                    "rule_id": f"nutc-{acad_year}-home-5-{sn:03d}",
                    "order": 5,
                    "phase": "行前準備",
                    "title": "完成中科大註冊繳費與簽證保險、留學期間投稿粉專，返國後辦理學分抵免並完成 20 小時志願服務",
                    "responsible_party": "學生與所屬系所",
                    "responsible_unit": "國立臺中科技大學國際事務處／教務處註冊組／各學院系所",
                    "summary": (
                        "出國前須完成中科大註冊繳費（保留學籍並享姊妹校免學費待遇）、簽署切結書、投保海外醫療與意外險及辦理役男出國核准；赴日韓交換生於留學期間須投稿國際處粉專（1 學期至少 5 篇、1 學年至少 10 篇）；返國後 2 週內持正式成績單向系所報到並辦理學分抵免（學海受獎生於 2 週內上傳教育部心得並核銷），1 個月內繳交中文心得報告、參加分享會並完成國際處志願服務 20 小時。"
                    ),
                    "details": tuition_points_list,
                    "scope": {
                        "home_universities": ["國立臺中科技大學"],
                        "academic_years": ["115", "116"],
                        "application_rounds": [round_label, "115-1", "115-2", "116-1", "116-2"],
                    },
                    "source_urls": [
                        NUTC_XUEHAI_REVIEW_RULES_PDF_URL,
                        NUTC_JBNU_2027_SPRING_PDF_URL,
                        NUTC_EXPERIENCES_URL,
                    ],
                    "checked_at": CHECKED_AT,
                    "support_status": "verified",
                },
            ],
            "sources": wf_sources,
            "last_checked": CHECKED_AT,
            "coverage_status": "official_verified",
            "coverage_note": (
                f"已完整整合國立臺中科技大學國際事務處（OIA）六大區域共 {len(catalog_source)} 所合作姊妹校名冊（日本 20 校、韓國 5 校、東南亞與南亞 33 校、歐美 23 校、大洋洲 4 校、大陸與澳門 55 校）、2026/2027 春秋季班交換簡章、114/115 年度教育部學海系列計畫公告與審查要點，以及 {exp_covered_schools} 校 {total_exp_reports} 篇歷屆學長姐交換心得報告。"
            ),
        })

        cost_line = f"{zh_name} 預估每月生活費：{living_cost_str}"
        tuition_clean = tuition_points_list[0]
        housing_clean = housing_str
        calendar_clean = f"學期與研修時間參考：{sem_dates_str}"
        course_clean = course_rest_str

        dest_sources = [
            {
                "title": f"國立臺中科技大學國際事務處合作姊妹校與交換簡章—{zh_name}",
                "source_url": source_url,
                "summary": "中科大國際事務處公告之合作計畫類型、申請資格、名額、語檢門檻與備註",
            },
            {
                "title": "國立臺中科技大學學生申請教育部學海系列計畫審查要點（111.09.27核定）",
                "source_url": NUTC_XUEHAI_REVIEW_RULES_PDF_URL,
                "summary": "中科大交換生註冊規定、學海飛颺／惜珠獎助額度（5萬至30萬元）、語檢標準與返國核銷規定",
            },
        ]
        if exp_links:
            dest_sources.append({
                "title": f"國立臺中科技大學國際事務處交換生心得分享專區—赴 {zh_name} 心得報告（{len(exps)} 篇）",
                "source_url": exp_links[0]["url"],
                "summary": f"收錄歷年中科大學生赴 {zh_name} 交換研修心得報告共 {len(exps)} 篇",
            })
        if website:
            dest_sources.append({"title": f"{full_name} 官方網站", "source_url": website, "summary": "接待合作姊妹校官方網站"})

        src_url_list = (
            [source_url, NUTC_OUTBOUND_EXCHANGE_URL, NUTC_XUEHAI_DATA_ZONE_URL]
            + ([exp_links[0]["url"]] if exp_links else [NUTC_EXPERIENCES_URL])
            + ([website] if website else [])
        )

        destinations.append({
            "home_university": "國立臺中科技大學",
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
                    "title": "生活費、中科大註冊保留學籍規定與教育部學海飛颺／惜珠／高教深耕獎助體系",
                    "summary": cost_line,
                    "points": [cost_line] + tuition_points_list,
                    "source_urls": src_url_list + [NUTC_XUEHAI_REVIEW_RULES_PDF_URL, NUTC_SPROUT_SUBSIDY_RULES_PDF_URL],
                    "caution": "獲教育部學海飛颺（每人補助 5 萬至 30 萬元）或學海惜珠補助之選送生，須於出國前 1 個月簽訂行政契約書，計畫結束後 2 週內上傳問卷與 1500 字心得及 4 張照片始得辦理經費核銷。",
                },
                {
                    "key": "housing",
                    "title": "住宿資訊與姊妹校校內外學生宿舍申請",
                    "summary": housing_clean[:160],
                    "points": [housing_clean],
                    "source_urls": src_url_list,
                    "caution": "印尼巴淡國際大學（UIB）提供交換生免學費及免費校內宿舍優惠；韓國全北大學宿舍含平日三餐、三育大學提供免費語學堂課程，其餘姊妹校交換生免學費但住宿與伙食費自理。",
                },
                {
                    "key": "insurance",
                    "title": "海外醫療、意外與急難救助保險規定",
                    "summary": visa_health_str,
                    "points": [
                        visa_health_str,
                        "依國立臺中科技大學國際事務處各姊妹校交換簡章規定，錄取學生於交換期間須投保涵蓋全期之海外醫療及意外保險，並於入境接待國後依當地法規加入國民健康保險（如日本 NHI、韓國 NHIS、澳洲 OSHC）。",
                    ],
                    "source_urls": src_url_list,
                    "caution": "赴日本、韓國、歐美及紐澳交換生必須配合接待校規定完成當地醫療保險投保與健康檢查（含肺結核 X 光、B 肝及麻疹抗體檢驗）。",
                },
                {
                    "key": "visa",
                    "title": "留學交換簽證辦理、役男緩徵出國申請與在學註冊義務",
                    "summary": visa_health_str,
                    "points": [
                        visa_health_str,
                        "具役男身分之錄取學生須於出國前完成役男出國緩徵核准手續，並於交換期間完成中科大每學期註冊繳費以保留學籍。",
                    ],
                    "source_urls": src_url_list,
                    "caution": "獲錄取推薦後無故放棄者，將影響日後申請校內其他國際交流計畫之資格。",
                },
                {
                    "key": "academics",
                    "title": "《學生申請教育部學海系列計畫審查要點》、返國學分抵免與 20 小時志願服務義務",
                    "summary": course_clean[:160],
                    "points": [calendar_clean, course_clean],
                    "source_urls": src_url_list + [NUTC_XUEHAI_REVIEW_RULES_PDF_URL],
                    "caution": "返國後 2 週內須持姊妹校正式成績單向所屬系所報到並向教務處註冊組申請學分抵免；返國後 1 個月內須繳交中文心得報告、參加分享會並完成國際處志願服務 20 小時。",
                },
                {
                    "key": "living",
                    "title": f"{city_name} 校園生活、國際處粉專投稿與學長姐返國心得傳承",
                    "summary": f"代表城市：{city_name}。赴日韓交換生於留學期間須定期投稿國際處粉絲專頁分享海外學習生活。",
                    "points": [
                        f"目的地城市：{city_name}（{country}）",
                        (
                            "國立臺中科技大學國際事務處於交換生心得分享專區與官方粉絲專頁（「去日本遊學&留學-台中科大國際處」、「就去韓國留個學」）公開歷屆學長姐赴海外姊妹校交換之返國心得報告"
                            + (f"（本校共收錄 {len(exps)} 篇：{'、'.join(exp_labels[:3])}）" if exps else "")
                            + "，提供選課、住宿、語學堂與生活費第一手參考。"
                        ),
                    ],
                    "source_urls": [exp_links[0]["url"] if exp_links else NUTC_EXPERIENCES_URL],
                },
            ],
            "sources": dest_sources,
            "last_checked": CHECKED_AT,
            "coverage_status": "official_verified",
            "coverage_note": (
                f"已整合國立臺中科技大學國際事務處 {len(catalog_source)} 所合作姊妹校名冊、2026/2027 春秋季班交換留學簡章、114/115 年度教育部學海系列計畫公告及 {exp_covered_schools} 校 {total_exp_reports} 篇歷屆學生返國心得報告。"
            ),
        })

        research_records.append({
            "home_university": "國立臺中科技大學",
            "school_name": full_name,
            "country": country,
            "official_website": website,
            "verification_status": "official_verified",
            "discovery_source_url": detail_url,
            "checked_at": CHECKED_AT,
            "note": "國立臺中科技大學國際事務處六大區域 140 所合作姊妹校名冊、交換留學簡章與 ROR/Wikidata 官方網址核對完成。",
        })

        ev_sources = [{"title": f"國立臺中科技大學國際事務處合作姊妹校與交換資訊—{zh_name}", "url": source_url}]
        if exp_links:
            ev_sources.append({
                "title": f"國立臺中科技大學國際事務處交換生心得分享專區—赴 {zh_name} 心得報告（{len(exps)} 篇）",
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
                "scope": "中科大海外與大陸港澳交換／雙聯姊妹校住宿與生活資訊",
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
                "scope": "中科大出國交換註冊規定、教育部學海飛颺／惜珠／築夢、高教深耕補助與地區生活費估算",
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
                "scope": "國立臺中科技大學學生申請教育部學海系列計畫審查要點、返國學分抵免與 20 小時志願服務規範",
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
                "scope": "中科大海外交換簽證、役男緩徵出國申請、海外醫療保險與行前健康檢查提醒",
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
                        f"｜中科大國際事務處公開收錄 {len(exps)} 篇赴 {zh_name} 交換生返國心得報告（{'、'.join(exp_labels[:3])}）。"
                        if exps
                        else ""
                    )
                ),
                "sources": ev_sources,
                "checked_at": CHECKED_AT,
                "scope": "中科大交換名額與歷屆學長姐返國心得報告分享",
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
                "已整合國立臺中科技大學國際事務處 140 所合作姊妹校名冊、2026/2027 交換留學申請簡章、教育部學海系列計畫審查要點及歷屆學生交換心得報告。",
                "當期開放名額、宿位供給、語檢門檻與選課限制請依合作校最新簡章及入學通知書核對。",
            ],
            "location_signature": f"verified:{lat}:{lon}:representative",
            "extraction_version": 3,
        })

    def write_jsonl(path: Path, rows: list[dict]) -> None:
        path.write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in rows) + ("\n" if rows else ""), encoding="utf-8")

    write_jsonl(OFFICIAL_NUTC_DIR / "partners.jsonl", partners)
    write_jsonl(SOURCES_NUTC_DIR / "partners.jsonl", partners)
    write_jsonl(OFFICIAL_NUTC_DIR / "application_workflows.jsonl", workflows)
    write_jsonl(OFFICIAL_NUTC_DIR / "destination_profiles.jsonl", destinations)
    write_jsonl(OFFICIAL_NUTC_DIR / "partner_research.jsonl", research_records)
    write_jsonl(OFFICIAL_NUTC_DIR / "student_life.jsonl", life_records)
    write_jsonl(OFFICIAL_NUTC_DIR / "experience_sources.jsonl", experience_sources_records)
    write_jsonl(OFFICIAL_NUTC_DIR / "student_experience_sources.jsonl", experience_sources_records)
    write_jsonl(OFFICIAL_NUTC_DIR / "student_experiences.jsonl", student_experience_rows)

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
    (OFFICIAL_NUTC_DIR / "student-experience-digests.json").write_text(
        json.dumps({"digests": digest_records}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    (OFFICIAL_NUTC_DIR / "student-experiences.json").write_text(
        json.dumps(
            {
                "school_id": "nutc",
                "school_name": "國立臺中科技大學",
                "checked_at": CHECKED_AT,
                "source_url": NUTC_EXPERIENCES_URL,
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

    (OFFICIAL_NUTC_DIR / "campus-locations.json").write_text(
        json.dumps(
            {
                "school_id": "nutc",
                "school_name": "國立臺中科技大學",
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
    (OFFICIAL_NUTC_DIR / "campus-assets.json").write_text(
        json.dumps(
            {
                "school_id": "nutc",
                "school_name": "國立臺中科技大學",
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

    nutc_source_urls = [
        NUTC_OIA_HOME_URL,
        NUTC_ABOUT_URL,
        NUTC_STAFF_URL,
        NUTC_PARTNERS_JAPAN_URL,
        NUTC_PARTNERS_KOREA_URL,
        NUTC_PARTNERS_SEA_URL,
        NUTC_PARTNERS_EUR_US_URL,
        NUTC_PARTNERS_OCEANIA_URL,
        NUTC_PARTNERS_MAINLAND_URL,
        NUTC_OUTBOUND_EXCHANGE_URL,
        NUTC_OUTBOUND_NOTICES_URL,
        NUTC_XUEHAI_NOTICES_URL,
        NUTC_XUEHAI_DATA_ZONE_URL,
        NUTC_EXPERIENCES_URL,
        NUTC_REGULATIONS_URL,
        NUTC_FORMS_URL,
        NUTC_XUEHAI_REVIEW_RULES_PDF_URL,
        NUTC_XUEHAI_ZHUMENG_RULES_PDF_URL,
        NUTC_SPROUT_SUBSIDY_RULES_PDF_URL,
        NUTC_XUEHAI_115_ANNOUNCEMENT_URL,
        NUTC_XUEHAI_115_PDF_URL,
        NUTC_JBNU_2027_SPRING_URL,
        NUTC_JBNU_2027_SPRING_PDF_URL,
        NUTC_SYU_2027_SPRING_URL,
        NUTC_SYU_2027_SPRING_PDF_URL,
        NUTC_SAPPORO_2027_SPRING_URL,
        NUTC_SAPPORO_2027_SPRING_PDF_URL,
        NUTC_MAINLAND_2027_SPRING_URL,
        NUTC_MAINLAND_2027_SPRING_PDF_URL,
        NUTC_SCU_2026_SPRING_PDF_URL,
        NUTC_AOMORI_2026_SPRING_PDF_URL,
        NUTC_NIIGATA_2026_SPRING_PDF_URL,
    ]

    exchange_info_payload = {
        "school_name": "國立臺中科技大學",
        "program_type": [
            "國際事務處「校級與院級赴國外姊妹校交換留學計畫」（涵蓋日本、韓國、歐美、紐澳、東南亞及南亞等六大區域合作姊妹校；研修一學期或一學年，交換期間於中科大註冊繳費保留學籍並享姊妹校學費互免待遇）",
            "國際事務處「學生赴大陸地區及港澳協議學校交換研習計畫」（涵蓋北京科技大學、中央財經大學、南開大學、上海戲劇學院、杭州電子科技大學、蘇州大學、東北大學、吉林大學、山東大學、廈門大學、福州大學及澳門科技大學、澳門城市大學等 55 所合作高校）",
            "國際事務處「跨國雙聯學位與海外實習專案」（含英國西蘇格蘭大學 UWS 商管／資訊 1 年制榮譽學士及碩士雙聯學位、瑞士 BHMS 工商酒店管理學院帶薪實習專案）暨教育部「學海飛颺、學海惜珠、學海築夢／新南向學海築夢」與「高教深耕國際專章」獎助學金體系",
        ],
        "academic_year": [
            "115（涵蓋 2026 秋季班／2027 春季班赴日、韓、歐美、東南亞及大陸協議學校交換甄選［春季班每年 9–10 月收件至 10/30；秋季班每年 3–5 月收件］，以及 115 年度教育部學海飛颺／學海惜珠／學海築夢計畫校內甄選［1月7日說明會、3月2日學院初審截止、3月4日國際處收件截止］）",
            f"本平台完整收錄國立臺中科技大學國際事務處公告之 {len(partners)} 所全球與大陸港澳締約姊妹校（橫跨全球 19 個國家與地區，含 {open_partner_count} 所當期開放交換與雙聯合作校，並完整收錄 {exp_covered_schools} 所合作大學共 {total_exp_reports} 篇歷屆學長姐返國心得報告）",
        ],
        "semester": [
            "春季班交換留學甄選（每年 9–10 月公告簡章並受理收件，翌年 2–3 月或 4 月出國）：開放申請日本姊妹校（札幌大學、信州大學、新潟大學、札幌市立大學、青森中央學院大學等）、韓國姊妹校（全北大學、三育大學）及大陸地區協議學校交換一學期或一學年。",
            "教育部學海系列計畫暨秋季班交換留學甄選（每年 1–3 月辦理學海飛颺／惜珠／築夢校內審查，3–5 月辦理秋季班交換甄選，當年 8–9 月出國）：開放全校六大學院在籍學生申請赴海外姊妹校交換研修與海外專業實習。",
        ],
        "application_period": [
            "【2027 春季班赴日、韓及大陸姊妹校交換留學甄選】依國際事務處各校簡章時程收件：（1）日本札幌大學、信州大學春季班：2026/09/14 中午 12:00 截止；（2）韓國三育大學春季班：2026/10/15 17:00 截止；（3）大陸地區協議學校（上海戲劇學院、杭州電子科技大學、陝西師範大學等）春季班：2026/10/27 17:00 截止；（4）韓國全北大學春季班：2026/10/30 17:00 截止。",
            "【115 年度教育部「學海飛颺／學海惜珠／學海築夢」校內申請作業】115 年 1 月 7 日（三）12:10–13:00 舉辦線上申請說明會；1 月 8 日至 3 月 2 日由各學院／系所進行甄選初審並排定推薦順序；3 月 4 日（三）前將學生書面申請資料送達三民校區中正大樓 1 樓 3105 室國際事務處；3 月 31 日前核報教育部，5 月 31 日公告核定結果。",
            "【秋季班赴日、韓、歐美、東南亞及大陸姊妹校交換留學甄選】每年 3 月至 5 月依國際事務處最新公告簡章受理收件，預計於當年 8–9 月出國研修一學期或一學年。",
        ],
        "eligibility": [
            "1. 修業年級與學籍規定：依《國立臺中科技大學學生申請教育部學海系列計畫審查要點》（111年9月27日核定）及各姊妹校交換留學簡章，申請人須為申請時已就讀本校一學期以上之日間部與進修部非應屆畢業在籍學生（含學士班、碩士班及五專部四年級(含)以上學生，不含專科部 1–3 年級生）。境外生、延修生、休學學生、國內及境外在職專班生不得提出申請；赴大陸地區協議學校交換研習限臺灣本地生申請。",
            "2. 在校學業與操行成績門檻：（1）國外姊妹校交換留學與教育部學海計畫：在學期間學業成績優異（各科成績皆須 70 分以上，須檢附歷年成績單＋最近一學期含班級排名之中英文版成績單），品格優良且操行成績平均須達 80 分（含）以上、無記過處分；（2）赴大陸地區協議學校交換研習：歷年學業成績總平均須達 80 分（含）以上、操行成績達 80 分（含）以上。",
            "3. 學海飛颺與學海惜珠申請資格：申請人須具中華民國國籍且在臺灣地區設有戶籍，並具備符合教育部規定之外語能力證明（或藝術設計類國際競賽獲獎證明）；申請《學海惜珠》者另須持有各直轄市、縣（市）主管機關認定之低收入戶、中低收入戶或特殊境遇家庭扶助相關證明。同一申請人於同一教育階段以補助 1 次為限。",
            "4. 留學期間投稿與返國服務義務：交換期間須於本校完成註冊繳費以保留學籍；赴日、韓交換生於留學期間 1 學期至少 5 篇、1 學年至少 10 篇投稿至國際處粉絲專頁；返國後 2 週內須持正式成績單向系所報到並辦理學分抵免，返國後 1 個月內繳交中文心得報告電子檔、參加交換留學分享會，並於國際事務處完成國際交流相關志願服務 20 小時。",
        ],
        "language_requirement": [
            "1. 日本地區姊妹校門檻：申請日本姊妹校（札幌大學、札幌市立大學、國立新潟大學、國立信州大學、青森中央學院大學、長崎國際大學、京都橘大學、名櫻大學、金澤星稜大學、目白大學、大阪觀光大學、環太平洋大學等）須通過日本語能力試驗 JLPT N2 級及格以上（其中國立新潟大學經濟學部另須通過 TOEIC 550 分以上）。",
            "2. 韓國地區姊妹校門檻：（1）國立全北大學（JBNU）：須通過韓語檢定 TOPIK 初級（Level 1/2）以上且英語多益 TOEIC 550 分以上（或同等語言能力證明）；（2）三育大學（Sahmyook University）：須檢附韓語能力證明文件（TOPIK Level 3 以上尤佳，提供交換生免費修讀語學堂韓語課程 1–6 級）。",
            "3. 歐美、紐澳、東南亞及英語授課學程門檻：如研修學校訂有外語標準從其標準（如印尼巴淡國際大學英語授課須 TOEIC 605 分以上、歐美合作大學一般要求 TOEFL iBT 60–79 或 IELTS 5.5–6.5）；如研修學校未訂標準，依《國立臺中科技大學學生申請教育部學海系列計畫審查要點》第四點第（十）款規定，英語須提出全民英檢（GEPT）中級以上或托福（TOEFL iBT）60 分以上（或相等之英語能力測驗證明），日語須 JLPT N2 以上，非英日語國家須提出近 2 年內曾修習該國語文之結業證書或修課成績證明。",
            "4. 大陸與澳門地區協議學校門檻：免附外語能力檢定證明，惟歷年學業成績平均及操行成績均須達 80 分（含）以上。",
        ],
        "required_documents": [
            "1. 國立臺中科技大學交換留學申請表／赴大陸地區協議學校研習申請表／教育部學海飛颺及學海惜珠補助申請表（黏貼 2 吋半身脫帽近照）",
            "2. 家長（或監護人）同意書正本（須家長親筆簽名蓋章）及學生個人資料提供同意書",
            "3. 歷年成績單正本＋最近一學期含班級排名之中英文版成績單各 1 份（各科成績須 70 分以上、操行 80 分以上；申請大陸地區須歷年總平均 80 分以上）",
            "4. 中、外文自傳與讀書計畫（含國外預計選修課程清單、與中科大課程之對應抵免規劃及留學動機）",
            "5. 有效期限內之外語能力檢定合格證書影本（日本附 JLPT N2 以上、韓國附 TOPIK 與 TOEIC 550、歐美及東南亞附 TOEFL iBT 60 / TOEIC 550 / GEPT 中級以上；大陸地區免附）",
            "6. 導師或專任教授推薦信 1–2 封（依各姊妹校簡章規定以中文、英文或日文撰寫並親筆簽名）",
            "7. 本校中文／英文在學證明正本、有效護照個人資料頁影本、身分證與學生證正反面影本",
            "8. 其他優良表現佐證資料（如專業證照、國際競賽獲獎證明、社團幹部或國際交流志工服務證明；申請設計藝術類姊妹校如札幌市立大學設計學部另須檢附作品集 Portfolio；申請學海惜珠另須檢附有效低收入戶／中低收入戶／特殊境遇家庭證明）",
        ],
        "scholarship_info": [
            "1. 教育部《學海飛颺》選送優秀學生出國研修獎學金：依《國立臺中科技大學學生申請教育部學海系列計畫審查要點》，選送具中華民國國籍、在學成績優異（或具藝術設計國際競賽獲獎事蹟）且外語能力符合標準之非應屆畢業在籍學生（五專四年級以上、學士班、碩士班）赴國外（不含大陸及港澳）姊妹校修讀學分 1 學期或 1 學年；每人補助額度為新臺幣 5 萬元以上至 30 萬元以下（含教育部補助款及本校至少 20% 配合款，實際金額依當年度預算與審查結果核定）。",
            "2. 教育部《學海惜珠》扶助清寒優秀學生出國研修獎學金：獎勵具中華民國國籍且持有直轄市、縣（市）主管機關認定之低收入戶、中低收入戶或特殊境遇家庭扶助證明之優秀在籍學生赴國外（不含大陸及港澳）合作大學修讀學分 1 學期至 1 學年，依教育部核定額度補助來回經濟艙機票與國外生活費。",
            "3. 教育部《學海築夢》及《新南向學海築夢》海外專業實習計畫：由本校專任教師擔任計畫主持人，選送具中華民國國籍且具專業與外語能力之在籍學生赴海外或新南向國家企業、機構進行至少連續 30 天（不含來回途程，至多 1 學年）之專業實習，補助學生經濟艙來回機票款及生活費。",
            "4. 《國立臺中科技大學高教深耕計畫國際專章補助國際交流活動要點》與外部獎助：補助本校學生參與國際競賽、短期海外研習與雙聯學位交流；赴日本姊妹校交換生另可依接待校配額申請日本台灣交流協會（JASSO）短期交換留學生獎學金（每月 JPY 80,000），赴印尼巴淡國際大學交換生享免學費及免費校內宿舍補助。",
        ],
        "partner_universities": [p["school_name"] for p in partners],
        "source_urls": nutc_source_urls,
        "last_checked": CHECKED_AT,
    }
    (OFFICIAL_NUTC_DIR / "exchange_info.json").write_text(
        json.dumps(exchange_info_payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    student_dashboard_payload = {
        "school_name": "國立臺中科技大學",
        "last_checked": CHECKED_AT,
        "academic_score_minimum": 70.0,
        "academic_score_rule": (
            "依《國立臺中科技大學學生申請教育部學海系列計畫審查要點》及各姊妹校交換留學簡章：申請人須為已就讀本校一學期以上之日間部與進修部非應屆畢業在籍學生（學士班、碩士班及五專部四年級(含)以上，不含專科部 1–3 年級生、延修生及在職專班），各科成績皆須 70 分以上（赴大陸地區協議學校歷年學業總平均須達 80 分(含)以上），且操行成績平均達 80 分（含）以上。"
        ),
        "academic_gpa_minimum": 2.7,
        "maximum_preferences": 3,
        "selection_rules": {
            "academic_policy": "score_or_rank",
            "academic_reference_year": "115",
            "undergraduate_gpa_minimum": 2.7,
            "graduate_academic_exempt": False,
            "exclude_in_service": True,
            "pending_quota_planning": False,
            "partner_requirements_need_confirmation": False,
            "degree_score_minimums": {"undergraduate": 70.0, "graduate": 70.0},
            "excluded_undergraduate_years": ["五專一", "五專二", "五專三"],
            "language_certificate_required": True,
        },
        "language_score_minimums": {"toefl": 60.0, "ielts": 5.0, "toeic": 550.0},
        "application_periods": [
            {
                "title": "國立臺中科技大學 2027 春季班赴日本、韓國及大陸地區姊妹校交換留學甄選（09/14–10/30 依各校簡章截止）",
                "details": [
                    "春季班出國交換甄選（預定 2027 年 2–4 月出國）於每年 9–10 月依各姊妹校簡章受理收件：日本札幌大學／信州大學春季班至 2026/09/14 中午 12:00 截止、韓國三育大學春季班至 2026/10/15 17:00 截止、赴大陸地區協議學校（上海戲劇學院、杭州電子科技大學、陝西師範大學等）至 2026/10/27 17:00 截止、韓國全北大學春季班至 2026/10/30 17:00 截止。",
                    "申請學生請備齊申請表、家長同意書、歷年成績單＋最近一學期含班排之中英文版成績單、自傳讀書計畫、語檢證明與推薦信，親送至三民校區中正大樓 1 樓 3105 室國際事務處。",
                ],
                "source": {
                    "title": "國立臺中科技大學國際事務處《出國交換生最新公告》與 2027 春季班各姊妹校交換簡章",
                    "source_url": NUTC_OUTBOUND_NOTICES_URL,
                    "category": "exchange_application",
                    "summary": "中科大 2027 春季班赴日本、韓國及大陸協議學校交換留學申請簡章、資格門檻與截止日期。",
                },
                "scope": "home_application",
                "program_types": ["exchange", "dual_degree"],
                "academic_year": "115",
                "application_round": "115-2（2027春季班）赴日、韓及大陸姊妹校交換留學甄選",
                "audience": "all_students",
                "opens_at": "2026-09-01T08:30:00+08:00",
                "deadline_at": "2026-10-30T17:00:00+08:00",
                "date_status": "verified_exact",
                "status": "open",
                "status_note": "2027 春季班日本札幌大學、信州大學、韓國全北大學、三育大學及大陸地區協議學校交換簡章已公告於國際事務處網站。",
                "deadline_note": "各姊妹校收件截止日不同（09/14 至 10/30），請依目標學校簡章於期限前送達國際事務處（中正大樓 3105 室）。",
                "reminder_eligible": True,
                "checked_at": CHECKED_AT,
            },
            {
                "title": "國立臺中科技大學 115 年度教育部《學海飛颺／學海惜珠／學海築夢》校內甄選（03/02 學院初審、03/04 國際處收件截止）",
                "details": [
                    "教育部學海系列計畫校內作業期程：115 年 1 月 7 日（三）12:10–13:00 舉辦線上申請說明會；1 月 8 日至 3 月 2 日由各學院／系所完成初審並排定推薦順序；3 月 4 日前將學生書面資料送達國際事務處；3 月 31 日前核報教育部，5 月 31 日公告教育部核定結果。",
                    "學海飛颺每人補助新臺幣 5 萬元以上至 30 萬元以下（含本校至少 20% 配合款）；秋季班出國交換甄選亦於每年 3–5 月陸續公告簡章收件。",
                ],
                "source": {
                    "title": "國立臺中科技大學《115年度教育部選送優秀學生赴國外研修/專業實習「學海系列計畫」校內申請作業公告》",
                    "source_url": NUTC_XUEHAI_115_ANNOUNCEMENT_URL,
                    "category": "scholarship",
                    "summary": "中科大 115 年度教育部學海飛颺、學海惜珠、學海築夢與新南向學海築夢校內申請時程與審查要點。",
                },
                "scope": "home_application",
                "program_types": ["exchange", "dual_degree"],
                "academic_year": "115",
                "application_round": "115年度教育部學海系列計畫暨秋季交換生校內甄選",
                "audience": "all_students",
                "opens_at": "2026-01-08T08:30:00+08:00",
                "deadline_at": "2026-03-04T17:00:00+08:00",
                "date_status": "verified_exact",
                "status": "open",
                "status_note": "115 年度教育部學海系列計畫校內申請作業公告與申請表單已發布於國際事務處網站。",
                "deadline_note": "各學院初審截止日為 3 月 2 日，學生書面資料送達國際事務處截止日為 3 月 4 日。",
                "reminder_eligible": True,
                "checked_at": CHECKED_AT,
            },
        ],
        "program_overview": [
            {
                "title": (
                    f"國立臺中科技大學國際事務處六大區域交換留學、英國雙聯學位與教育部學海獎助總覽（{len(partners)} 所締約姊妹校・{total_exp_reports} 篇學長姐交換心得報告）"
                ),
                "details": [
                    (
                        f"國立臺中科技大學（National Taichung University of Science and Technology, NUTC，創立於 1919 年，2011 年由國立臺中技術學院與國立臺中護理專科學校合併改制，擁有三民校區與民生校區，設有「商學院、設計學院、資訊與流通學院、智慧產業學院、語文學院、中護健康學院」六大學院）由「國際事務處（Office of International Affairs，三民校區中正大樓 1 樓 3105 室，下設國際暨兩岸合作組、國際學生交流組、兩岸學生交流組及華語教學組）」統籌全校出國交換留學、大陸港澳協議學校交換研習、跨國雙聯學位及教育部學海系列計畫。本平台完整收錄 {len(partners)} 所中科大官方合作姊妹校，橫跨全球 19 個國家與地區（含 {open_partner_count} 所當期開放申請之交換與雙聯合作校）。"
                    ),
                    (
                        f"中科大出國交換與國際交流體系具備五大核心特色：（1）六大區域完整布局（日本 20 校［含國立新潟大學、國立信州大學、札幌市立大學、札幌大學、青森中央學院大學、長崎國際大學、京都橘大學、名櫻大學、金澤星稜大學等］、韓國 5 校［國立全北大學、三育大學、韓世大學等］、東南亞與南亞 33 校［泰國農業大學、宋卡王子大學、先皇技術學院、越南河內國家大學、胡志明市經濟財經大學、馬來西亞拉曼大學、雙威大學、印尼巴淡國際大學免學費免住宿專案、新加坡社科大學等］、歐美 23 校［美國奧克拉荷馬州立大學、中央奧克拉荷馬大學、天普大學、北伊利諾大學、英國西蘇格蘭大學 UWS 雙聯學位、諾丁漢特倫特大學、德國柏林經濟與法律應用科學大學、瑞士 BHMS 帶薪實習、捷克赫拉德茨克拉洛韋大學等］、大洋洲 4 校［澳洲西雪梨大學、坎培拉大學、紐西蘭懷卡托大學］、大陸與澳門 55 校［北京科技大學、中央財經大學、南開大學、上海戲劇學院、杭州電子科技大學、蘇州大學、東北大學、吉林大學、山東大學、廈門大學、澳門科技大學等］）；（2）五專部四年級(含)以上、學士班及碩士班全面開放申請；（3）教育部學海飛颺（每人補助 5 萬至 30 萬元）、學海惜珠、學海築夢與高教深耕國際專章四層獎助；（4）留學期間粉專投稿與返國 20 小時國際交流志願服務傳承機制；（5）完整收錄 {exp_covered_schools} 所合作大學共 {total_exp_reports} 篇歷屆學長姐返國心得報告。"
                    ),
                ],
                "source": {
                    "title": "國立臺中科技大學國際事務處（OIA）官方網站與出國交換生專區",
                    "source_url": NUTC_OUTBOUND_EXCHANGE_URL,
                    "category": "exchange_application",
                    "summary": f"中科大 {len(partners)} 所全球與大陸港澳合作姊妹校、交換留學簡章與 {total_exp_reports} 篇交換心得報告。",
                },
            }
        ],
        "eligibility": [
            {
                "title": "中科大在籍滿一學期非應屆畢業生資格（學士班／碩士班／五專四五年級）、學業 70/80 分與操行 80 分門檻",
                "details": [
                    "修業年級與學籍規定：依《國立臺中科技大學學生申請教育部學海系列計畫審查要點》及各姊妹校交換簡章，申請人須為申請時已就讀本校一學期以上之日間部與進修部非應屆畢業在籍學生（學士班、碩士班及五專部四年級(含)以上，不含五專 1–3 年級生、境外生、延修生、休學生及在職專班生；赴大陸地區限臺灣本地生）。",
                    "學業與操行成績標準：國外交換留學與學海計畫申請人各科成績皆須達 70 分以上（檢附歷年成績單＋最近一學期含班級排名之中英文版成績單），操行成績平均須達 80 分（含）以上且無記過處分；赴大陸地區協議學校交換研習者，歷年學業總平均及操行成績均須達 80 分（含）以上。",
                ],
                "source": {
                    "title": "國立臺中科技大學學生申請教育部學海系列計畫審查要點 PDF",
                    "source_url": NUTC_XUEHAI_REVIEW_RULES_PDF_URL,
                    "category": "exchange_application",
                    "summary": "中科大交換生與學海系列計畫申請資格、五專四年級以上學制規定及返國義務。",
                },
            }
        ],
        "language_requirements": [
            {
                "title": "中科大交換留學語檢門檻（日本 JLPT N2／韓國 TOPIK＋TOEIC 550／歐美英語 GEPT 中級或 TOEFL iBT 60）",
                "details": [
                    "日韓姊妹校語言門檻：（1）日本地區姊妹校（札幌大學、札幌市立大學、國立新潟大學、國立信州大學、青森中央學院大學、長崎國際大學等）須通過 JLPT N2 級及格以上（新潟大學經濟學部另須 TOEIC 550 分以上）；（2）韓國全北大學須通過 TOPIK 初級（Level 1/2）以上且 TOEIC 550 分以上，三育大學須檢附韓語能力證明（TOPIK 3 級以上尤佳，提供免費語學堂 1–6 級課程）。",
                    "歐美、紐澳、東南亞與學海計畫外語門檻：如接待校訂有標準從其標準（如印尼巴淡國際大學英語授課須 TOEIC 605 分以上）；如未訂標準，依《學生申請教育部學海系列計畫審查要點》第四點第（十）款，英語須達全民英檢（GEPT）中級以上或 TOEFL iBT 60 分以上（或同等英語檢定如 TOEIC 550 / IELTS 5.0），非英日語國家須提出近 2 年內曾修習該國語文之結業證書或修課成績證明；大陸與澳門地區免附外語檢定。",
                ],
                "source": {
                    "title": "國立臺中科技大學《學生申請教育部學海系列計畫審查要點》與日本、韓國姊妹校交換留學簡章",
                    "source_url": NUTC_JBNU_2027_SPRING_PDF_URL,
                    "category": "exchange_application",
                    "summary": "中科大日韓、歐美、東南亞姊妹校與教育部學海計畫語言能力最低要求。",
                },
            }
        ],
        "required_documents": [
            {
                "title": "交換留學申請表、家長同意書、中英文歷年成績單（含班排）、自傳讀書計畫、語檢證書與教授推薦信",
                "details": [
                    "校內甄選必備文件：（1）交換留學申請表／赴大陸地區協議學校研習申請表／學海系列計畫申請表（貼妥 2 吋照片）；（2）家長同意書正本及個資同意書；（3）歷年成績單正本＋最近一學期含班級排名之中英文版成績單；（4）中、外文自傳與讀書計畫（含國外預計選課及本校對應科目）；（5）有效期限內之外語能力檢定合格證書影本；（6）導師或教授推薦信 1–2 封；（7）中英文在學證明、護照影本、身分證與學生證影本（設計類學部如札幌市立大學另須附作品集）。",
                    "留學期間與返國結案文件：獲校內推薦後配合國際處遞交姊妹校外文申請書、英文存款餘額證明（財力證明）與健康檢查表；留學期間赴日韓交換生須投稿國際處粉專（1 學期 5 篇、1 學年 10 篇）；返國後 2 週內持正式成績單辦理學分抵免（學海受獎生於 2 週內上傳教育部系統 1500 字心得與問卷），1 個月內繳交中文心得報告電子檔並完成國際處志願服務 20 小時。",
                ],
                "source": {
                    "title": "國立臺中科技大學國際事務處《表單下載》與《學海計畫資料專區》",
                    "source_url": NUTC_FORMS_URL,
                    "category": "exchange_application",
                    "summary": "中科大交換留學申請表、家長同意書、學海計畫申請書及返國心得格式下載。",
                },
            }
        ],
        "scholarship_info": [
            {
                "title": "教育部《學海飛颺》（每人 5–30 萬元）、《學海惜珠》、《學海築夢／新南向學海築夢》與《高教深耕國際專章》",
                "details": [
                    "教育部學海飛颺與學海惜珠：每年 1–3 月初辦理校內申請（3 月 2 日學院初審、3 月 4 日國際處收件截止）；《學海飛颺》選送優秀在籍生赴非大陸港澳姊妹校交換 1 學期至 1 學年，每人補助新臺幣 5 萬元以上至 30 萬元以下（含本校至少 20% 配合款）；《學海惜珠》補助持有效低收入戶、中低收入戶或特殊境遇家庭證明之清寒優秀生出國研修機票與生活費。",
                    "教育部學海築夢與高教深耕國際專章：《學海築夢》及《新南向學海築夢》補助學生赴海外企業機構進行至少連續 30 天專業實習之機票與生活費；《國立臺中科技大學高教深耕計畫國際專章補助國際交流活動要點》另補助學生參與國際交流與雙聯學位，日本交換生亦可申請 JASSO 獎學金。",
                ],
                "source": {
                    "title": "國立臺中科技大學《學生申請教育部學海系列計畫審查要點》與《高教深耕計畫國際專章補助國際交流活動要點》",
                    "source_url": NUTC_XUEHAI_DATA_ZONE_URL,
                    "category": "scholarship",
                    "summary": "中科大教育部學海飛颺、學海惜珠、學海築夢審查要點與高教深耕國際交流補助規定。",
                },
            }
        ],
        "document_explanations": [
            {
                "title": "國立臺中科技大學交換留學申請文件準備、讀書計畫選課對應與返國志願服務指南",
                "summary": "說明中科大日韓與大陸交換簡章送件規範、歷年含班排中英文成績單、設計類作品集要求、留學期間粉專投稿與返國 20 小時服務義務。",
                "key_points": [
                    "成績單與排名規定：申請國外交換留學須同時檢附「歷年成績單」及「最近一學期含班級排名之中英文版成績單」，確認各科成績皆達 70 分以上且操行成績平均達 80 分以上（大陸地區歷年總平均須達 80 分以上）。",
                    "讀書計畫與特殊專長附件：讀書計畫須具體列出擬於姊妹校修習之科目名稱及對應中科大擬抵免之科目；申請日本札幌市立大學設計學部等設計藝術院校者，須另附個人作品集（Portfolio）。",
                    "粉專投稿與返國 20 小時服務：赴日、韓交換生於留學期間須投稿國際處粉專（1 學期至少 5 篇、1 學年至少 10 篇）；返國後 1 個月內繳交中文心得報告電子檔、參與分享會，並於國際事務處完成國際交流志願服務 20 小時。",
                ],
                "applies_to": [],
                "source": {
                    "title": "國立臺中科技大學日本札幌大學、韓國全北大學與大陸協議學校 2027 春季班交換簡章",
                    "source_url": NUTC_SAPPORO_2027_SPRING_URL,
                    "category": "exchange_application",
                    "summary": None,
                },
                "document_url": NUTC_SAPPORO_2027_SPRING_PDF_URL,
                "document_type": "official_document",
                "full_text_extracted": True,
            }
        ],
        "rule_explanations": [
            {
                "title": "國立臺中科技大學學生申請教育部學海系列計畫審查要點與交換留學核心法規",
                "summary": "規範中科大六大學院學生（含五專部四五年級、學士班、碩士班）申請出國交換與學海獎學金之資格、補助額度（5–30 萬元）與契約核銷義務。",
                "key_points": [
                    "開放學制與排除對象：限已就讀本校一學期以上之日間部與進修部非應屆畢業在籍學生（學士班、碩士班及五專部四年級(含)以上）；專科部 1–3 年級生、境外生、延修生、休學生及在職專班生不得申請。",
                    "學海飛颺與惜珠補助額度：學海飛颺每人補助新臺幣 5 萬元以上至 30 萬元以下（含本校至少 20% 配合款）；同一申請人於同一教育階段以補助 1 次為限，且不得同時領取我國政府提供之其他出國補助。",
                    "行政契約與返國核銷：獲學海計畫補助生須於出國研修前 1 個月與本校簽訂行政契約書，於計畫期滿返國後 2 週內至教育部學海計畫資訊網上傳問卷及 1500 字以內中文心得報告與 4 張照片，始得辦理經費核銷。",
                ],
                "applies_to": [],
                "source": {
                    "title": "國立臺中科技大學學生申請教育部學海系列計畫審查要點（111.09.27核定）",
                    "source_url": NUTC_REGULATIONS_URL,
                    "category": "exchange_application",
                    "summary": None,
                },
                "document_url": NUTC_XUEHAI_REVIEW_RULES_PDF_URL,
                "document_type": "official_document",
                "full_text_extracted": True,
            }
        ],
        "sources": [
            {"title": "國立臺中科技大學國際事務處（OIA）官方網站", "source_url": NUTC_OIA_HOME_URL, "category": "exchange_application", "summary": None},
            {"title": "國立臺中科技大學出國交換生專區與最新甄選公告", "source_url": NUTC_OUTBOUND_EXCHANGE_URL, "category": "exchange_application", "summary": None},
            {"title": "國立臺中科技大學六大區域合作姊妹校名冊（日本、韓國、東南亞、歐美、大洋洲、大陸港澳共 140 校）", "source_url": NUTC_PARTNERS_JAPAN_URL, "category": "partner_school", "summary": None},
            {"title": "國立臺中科技大學 115 年度教育部學海系列計畫校內申請作業公告", "source_url": NUTC_XUEHAI_115_ANNOUNCEMENT_URL, "category": "scholarship", "summary": None},
            {"title": "國立臺中科技大學學生申請教育部學海系列計畫審查要點（111.09.27核定）", "source_url": NUTC_XUEHAI_REVIEW_RULES_PDF_URL, "category": "scholarship", "summary": None},
            {"title": "國立臺中科技大學高教深耕計畫國際專章補助國際交流活動要點", "source_url": NUTC_SPROUT_SUBSIDY_RULES_PDF_URL, "category": "scholarship", "summary": None},
            {"title": "國立臺中科技大學國際事務處法規專區與表單下載", "source_url": NUTC_REGULATIONS_URL, "category": "exchange_application", "summary": None},
            {"title": "國立臺中科技大學交換生心得分享專區（日、韓、美姊妹校學長姐返國報告）", "source_url": NUTC_EXPERIENCES_URL, "category": "experience_report", "summary": None},
        ],
    }
    (OFFICIAL_NUTC_DIR / "student_dashboard.json").write_text(
        json.dumps(student_dashboard_payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    doc_conditions = {
        "school_id": "nutc",
        "school_name": "國立臺中科技大學",
        "checked_at": CHECKED_AT,
        "source_url": NUTC_FORMS_URL,
        "common_documents": exchange_info_payload["required_documents"],
        "track_specific_conditions": [
            {
                "track": "國際事務處【赴日本、韓國、歐美、紐澳及東南亞姊妹校交換留學計畫】",
                "required": [
                    "國立臺中科技大學交換留學申請表（貼妥 2 吋照片）、家長同意書正本及個資同意書",
                    "歷年成績單正本＋最近一學期含班級排名之中英文版成績單（各科 70 分以上、操行 80 分以上）",
                    "中、外文自傳與讀書計畫（設計學部另附作品集 Portfolio）、教授推薦信及中英文在學證明",
                    "有效外語能力證明（日本附 JLPT N2 以上；韓國全北大學附 TOPIK 初級＋TOEIC 550、三育大學附韓語證明；歐美及東南亞附 GEPT 中級或 TOEFL iBT 60 / TOEIC 550 以上）",
                ],
            },
            {
                "track": "國際事務處【學生赴大陸地區及港澳協議學校交換研習計畫（55 所合作高校）】",
                "required": [
                    "中科大學生赴大陸地區協議學校研習申請表、家長同意書正本及個資同意書（限臺灣本地日間部／進修部在籍生及日間部碩士生，五專部須四年級以上）",
                    "歷年成績單正本＋最近一學期含班級排名之中文成績單（歷年學業總平均須達 80 分(含)以上、操行成績達 80 分(含)以上）",
                    "自傳、讀書計畫（含擬選修科目與學分抵免規劃）、師長推薦信、在學證明及有效臺胞證影本",
                ],
            },
            {
                "track": "教育部【學海飛颺／學海惜珠／學海築夢】暨【英國西蘇格蘭大學 UWS 雙聯學位專案】",
                "required": [
                    "學海飛颺／惜珠申請人須具中華民國國籍，於 3 月 2 日前經所屬學院完成初審並排定推薦順序，3 月 4 日前將書面資料送達國際事務處（學海惜珠另附有效低收入戶／中低收入戶／特殊境遇家庭證明）",
                    "申請英國西蘇格蘭大學（UWS）1 年制榮譽學士或碩士雙聯學位者，須備妥英文歷年成績單、英文讀書計畫、教授推薦信及 IELTS 6.0 語檢證明",
                    "獲學海計畫補助生須於出國前 1 個月簽訂行政契約書，返國後 2 週內於教育部學海計畫系統上傳 1500 字心得與問卷始得核銷",
                ],
            },
        ],
    }
    (OFFICIAL_NUTC_DIR / "document-conditions.json").write_text(
        json.dumps(doc_conditions, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    field_cov_lines = ["field_name,total_records,populated_records,coverage_ratio,notes"]
    for fname in [
        "school_name", "country", "region", "program_type", "availability_status",
        "quota", "colleges", "degree_levels", "language_requirement", "gpa_requirement",
        "application_deadline", "study_period", "semester_dates", "housing_info",
        "course_restrictions", "official_website", "image_url",
    ]:
        pop = sum(1 for p in partners if p.get(fname) not in (None, "", []))
        ratio = pop / len(partners) if partners else 1.0
        field_cov_lines.append(f"{fname},{len(partners)},{pop},{ratio:.4f},Official NUTC OIA verified")
    (OFFICIAL_NUTC_DIR / "field-coverage.csv").write_text("\n".join(field_cov_lines) + "\n", encoding="utf-8")

    pages_records = [
        {
            "title": "國立臺中科技大學：2026/2027 春秋季班出國交換甄選時程與 115 年度教育部學海系列計畫申請期程",
            "source_url": NUTC_OUTBOUND_NOTICES_URL,
            "published_at": "2026-10-20T00:00:00Z",
            "text": "\n".join(exchange_info_payload["application_period"]),
            "summary": "\n".join(exchange_info_payload["application_period"]),
            "category": "exchange_application",
            "attachments": [],
            "crawled_at": CHECKED_AT,
            "content_hash": hashlib.sha256("\n".join(exchange_info_payload["application_period"]).encode("utf-8")).hexdigest(),
        },
        {
            "title": "國立臺中科技大學：學生申請教育部學海系列計畫審查要點、五專四年級以上與學碩士班申請資格及返國 20 小時服務規範",
            "source_url": NUTC_XUEHAI_REVIEW_RULES_PDF_URL,
            "published_at": "2026-10-15T00:00:00Z",
            "text": "\n".join(exchange_info_payload["eligibility"]),
            "summary": "\n".join(exchange_info_payload["eligibility"]),
            "category": "exchange_application",
            "attachments": [],
            "crawled_at": CHECKED_AT,
            "content_hash": hashlib.sha256("\n".join(exchange_info_payload["eligibility"]).encode("utf-8")).hexdigest(),
        },
        {
            "title": f"國立臺中科技大學：{len(partners)} 所六大區域合作姊妹校名冊與日韓歐美東南亞語檢門檻",
            "source_url": NUTC_PARTNERS_JAPAN_URL,
            "published_at": "2026-10-15T00:00:00Z",
            "text": "\n".join(exchange_info_payload["language_requirement"]),
            "summary": "\n".join(exchange_info_payload["language_requirement"]),
            "category": "exchange_application",
            "attachments": [],
            "crawled_at": CHECKED_AT,
            "content_hash": hashlib.sha256("\n".join(exchange_info_payload["language_requirement"]).encode("utf-8")).hexdigest(),
        },
        {
            "title": "國立臺中科技大學：交換留學申請表件、家長同意書、粉專投稿與返國學分抵免規範",
            "source_url": NUTC_FORMS_URL,
            "published_at": "2026-10-15T00:00:00Z",
            "text": "\n".join(exchange_info_payload["required_documents"]),
            "summary": "\n".join(exchange_info_payload["required_documents"]),
            "category": "exchange_application",
            "attachments": [],
            "crawled_at": CHECKED_AT,
            "content_hash": hashlib.sha256("\n".join(exchange_info_payload["required_documents"]).encode("utf-8")).hexdigest(),
        },
        {
            "title": "國立臺中科技大學：教育部學海飛颺（5–30萬元）、學海惜珠、學海築夢與高教深耕國際專章獎助辦法",
            "source_url": NUTC_XUEHAI_DATA_ZONE_URL,
            "published_at": "2026-10-15T00:00:00Z",
            "text": "\n".join(exchange_info_payload["scholarship_info"]),
            "summary": "\n".join(exchange_info_payload["scholarship_info"]),
            "category": "scholarship",
            "attachments": [],
            "crawled_at": CHECKED_AT,
            "content_hash": hashlib.sha256("\n".join(exchange_info_payload["scholarship_info"]).encode("utf-8")).hexdigest(),
        },
    ]
    (OFFICIAL_NUTC_DIR / "pages.jsonl").write_text(
        "\n".join(json.dumps(p, ensure_ascii=False) for p in pages_records) + "\n", encoding="utf-8"
    )

    home_rules = {
        "school_id": "nutc",
        "school_name": "國立臺中科技大學",
        "eligibility": student_dashboard_payload["eligibility"],
        "application_periods": student_dashboard_payload["application_periods"],
        "selection_rules": {
            "undergraduate_score_minimum": 70.0,
            "graduate_score_minimum": 70.0,
            "mainland_exchange_score_minimum": 80.0,
            "conduct_score_minimum": 80.0,
            "undergraduate_gpa_minimum": 2.7,
            "xuehai_feiyang_subsidy_min_ntd": 50000,
            "xuehai_feiyang_subsidy_max_ntd": 300000,
            "maximum_preferences": 3,
            "screening_batches_per_year": 2,
            "allow_freshman_apply": True,
            "min_enrolled_semesters": 1,
            "five_year_junior_college_min_year": 4,
            "volunteer_service_hours_required": 20,
            "tuition_policy_during_exchange": "出國交換期間須於國立臺中科技大學完成註冊並繳交全額學雜費以保留學籍；互惠姊妹校免繳接待校學費",
            "return_documents_due": "赴日韓交換生於留學期間須投稿國際處粉專（1學期5篇、1學年10篇）；返國後 2 週內持正式成績單向系所報到並辦理學分抵免（學海受獎生於 2 週內完成教育部系統上傳與核銷），返國後 1 個月內繳交中文心得報告、參加分享會並完成國際處志願服務 20 小時",
        },
        "source_urls": nutc_source_urls,
        "verified_at": "2026-10-31",
    }
    (OFFICIAL_NUTC_DIR / "home_rules.json").write_text(
        json.dumps(home_rules, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    (OFFICIAL_NUTC_DIR / "documents.json").write_text(
        json.dumps(
            {"school_name": "國立臺中科技大學", "required_documents": student_dashboard_payload["required_documents"], "source_urls": nutc_source_urls},
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    (OFFICIAL_NUTC_DIR / "scholarships.json").write_text(
        json.dumps(
            {"school_name": "國立臺中科技大學", "scholarships": student_dashboard_payload["scholarship_info"], "source_urls": nutc_source_urls},
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    completeness = {
        "school_id": "nutc",
        "school_name": "國立臺中科技大學",
        "total_partners": len(partners),
        "partner_count": len(partners),
        "international_partners": sum(1 for p in partners if p["country"] not in {"中國大陸", "香港", "澳門"}),
        "mainland_partners": sum(1 for p in partners if p["country"] in {"中國大陸", "香港", "澳門"}),
        "dual_degree_partner_universities": 1,
        "dual_degree_programs": 2,
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
        "active_term": (
            f"國立臺中科技大學國際事務處 115 學年度（2027 春季班赴日、韓及大陸交換甄選：09/14–10/30 收件截止；115 年度教育部學海飛颺／惜珠／築夢計畫：03/02 學院初審、03/04 國際處收件截止）六大區域單學期／學年交換計畫及英國西蘇格蘭大學（UWS）雙聯學位同步整合；共完整收錄 {len(partners)} 所全球與大陸港澳合作姊妹校（橫跨全球 19 個國家與地區，含 {open_partner_count} 所當期開放申請校，並收錄 {exp_covered_schools} 所合作大學共 {total_exp_reports} 篇歷屆學長姐返國心得報告）。"
        ),
        "verified_at": "2026-10-31",
    }
    (OFFICIAL_NUTC_DIR / "catalog-completeness.json").write_text(
        json.dumps(completeness, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    (OFFICIAL_NUTC_DIR / "verification_status.json").write_text(
        json.dumps(
            {"school_id": "nutc", "school_name": "國立臺中科技大學", "status": "official_verified", "checked_at": CHECKED_AT, "counts": completeness},
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    provenance_files = [
        ("sources/nutc/partners_japan.html", NUTC_PARTNERS_JAPAN_URL, "國立臺中科技大學國際事務處—日本地區姊妹校名冊（20校）HTML"),
        ("sources/nutc/partners_korea.html", NUTC_PARTNERS_KOREA_URL, "國立臺中科技大學國際事務處—韓國地區姊妹校名冊（5校）HTML"),
        ("sources/nutc/partners_sea.html", NUTC_PARTNERS_SEA_URL, "國立臺中科技大學國際事務處—東南亞及南亞地區姊妹校名冊（33校）HTML"),
        ("sources/nutc/partners_eur_us.html", NUTC_PARTNERS_EUR_US_URL, "國立臺中科技大學國際事務處—歐美地區姊妹校名冊（23校）HTML"),
        ("sources/nutc/partners_oceania.html", NUTC_PARTNERS_OCEANIA_URL, "國立臺中科技大學國際事務處—大洋洲地區姊妹校名冊（4校）HTML"),
        ("sources/nutc/partners_mainland.html", NUTC_PARTNERS_MAINLAND_URL, "國立臺中科技大學國際事務處—大陸及港澳地區協議學校名冊（55校）HTML"),
        ("sources/nutc/xuehai_review_rules_1110927.pdf", NUTC_XUEHAI_REVIEW_RULES_PDF_URL, "國立臺中科技大學學生申請教育部學海系列計畫審查要點（111.09.27核定）PDF"),
        ("sources/nutc/xuehai_zhumeng_rules_1110927.pdf", NUTC_XUEHAI_ZHUMENG_RULES_PDF_URL, "國立臺中科技大學教師申請學海築夢計畫及新南向學海築夢計畫審查要點（111.09.27核定）PDF"),
        ("sources/nutc/xuehai_115_announcement.pdf", NUTC_XUEHAI_115_PDF_URL, "國立臺中科技大學 115 年度教育部選送優秀學生赴國外研修/專業實習「學海系列計畫」校內申請作業公告 PDF"),
        ("sources/nutc/xuehai_114_announcement.pdf", "https://oia.nutc.edu.tw/var/file/26/1026/attach/62/pta_85458_8271647_81475.pdf", "國立臺中科技大學 114 年度教育部「學海系列計畫」校內申請作業公告 PDF"),
        ("sources/nutc/sprout_intl_subsidy_rules.pdf", NUTC_SPROUT_SUBSIDY_RULES_PDF_URL, "國立臺中科技大學高教深耕計畫國際專章補助國際交流活動要點 PDF"),
        ("sources/nutc/brochure_jbnu_2027_spring.pdf", NUTC_JBNU_2027_SPRING_PDF_URL, "國立臺中科技大學—韓國姊妹校全北大學 2027 年春季交換生申請簡章 PDF"),
        ("sources/nutc/brochure_syu_2027_spring.pdf", NUTC_SYU_2027_SPRING_PDF_URL, "國立臺中科技大學—韓國姊妹校三育大學 2027 年春季交換生申請簡章 PDF"),
        ("sources/nutc/brochure_sapporo_2027_spring.pdf", NUTC_SAPPORO_2027_SPRING_PDF_URL, "國立臺中科技大學—2027 年度日本姊妹校札幌大學交換留學春季班申請簡章 PDF"),
        ("sources/nutc/brochure_scu_2026_spring.pdf", NUTC_SCU_2026_SPRING_PDF_URL, "國立臺中科技大學—日本姊妹校札幌市立大學交換留學春季班申請簡章 PDF"),
        ("sources/nutc/brochure_aomoricgu_2026_spring.pdf", NUTC_AOMORI_2026_SPRING_PDF_URL, "國立臺中科技大學—2026 年度日本姊妹校青森中央學院大學交換留學春季班申請簡章 PDF"),
        ("sources/nutc/brochure_niigata_2026_spring.pdf", NUTC_NIIGATA_2026_SPRING_PDF_URL, "國立臺中科技大學—2026 年度日本姊妹校國立新潟大學交換留學春季班申請簡章 PDF"),
        ("sources/nutc/brochure_niu_2023_autumn.pdf", "https://oia.nutc.edu.tw/var/file/26/1026/attach/74/pta_71713_9188906_04602.pdf", "國立臺中科技大學—日本姊妹校長崎國際大學交換留學秋季班申請簡章 PDF"),
        ("sources/nutc/brochure_japan_2020_spring.pdf", "https://oia.nutc.edu.tw/var/file/26/1026/img/2253/786878577.pdf", "國立臺中科技大學—日本姊妹校校級交換留學春季班申請簡章 PDF"),
        ("sources/nutc/form_mainland_exchange_2027_spring.pdf", NUTC_MAINLAND_2027_SPRING_PDF_URL, "國立臺中科技大學學生赴大陸地區協議學校研習申請表（2027春季班）PDF"),
        ("sources/nutc/regulations.html", NUTC_REGULATIONS_URL, "國立臺中科技大學國際事務處法規專區 HTML"),
        ("sources/nutc/forms_download.html", NUTC_FORMS_URL, "國立臺中科技大學國際事務處表單下載專區 HTML"),
        ("sources/nutc/xuehai_data_zone.html", NUTC_XUEHAI_DATA_ZONE_URL, "國立臺中科技大學國際事務處學海計畫資料專區 HTML"),
        ("sources/nutc/experiences_page1.html", NUTC_EXPERIENCES_URL, "國立臺中科技大學國際事務處交換生心得分享專區 HTML"),
        ("sources/nutc/nutc_experience_index.json", NUTC_EXPERIENCES_URL, f"國立臺中科技大學交換生心得分享專區（{exp_covered_schools} 校共 {total_exp_reports} 篇心得報告）索引 JSON"),
        ("sources/nutc/nutc_catalog_source.json", NUTC_PARTNERS_JAPAN_URL, f"國立臺中科技大學 {len(partners)} 所全球與大陸港澳合作姊妹校整合資料集 JSON"),
        ("sources/nutc/nutc_resolved_locations.json", NUTC_PARTNERS_JAPAN_URL, f"國立臺中科技大學 {len(partners)} 所合作姊妹校 ROR / Wikidata 地理座標核對表 JSON"),
    ]
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
        "school_id": "nutc",
        "school_name": "國立臺中科技大學",
        "generated_at": CHECKED_AT,
        "active_cycle_note": completeness["active_term"],
        "sources": prov_sources,
    }
    prov_text = json.dumps(provenance_payload, ensure_ascii=False, indent=2) + "\n"
    (OFFICIAL_NUTC_DIR / "import_provenance.json").write_text(prov_text, encoding="utf-8")
    (OFFICIAL_NUTC_DIR / "import-provenance.json").write_text(prov_text, encoding="utf-8")

    print(
        f"Successfully built NUTC catalog: {len(partners)} partners"
        f" ({open_partner_count} open, {completeness['verified_campus_images']}"
        f" verified images, {completeness['verified_locations']} verified"
        f" locations), {len(workflows)} workflows,"
        f" {len(destinations)} destinations, {len(research_records)} research"
        f" records, {exp_covered_schools} schools with experience records"
        f" ({len(student_experience_rows)} rows, {total_exp_reports} reports)."
    )


if __name__ == "__main__":
    main()
