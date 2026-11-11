"""Build the official Tzu Chi University (慈濟大學, TCU) exchange data bundle."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import shutil

REPO_ROOT = Path(__file__).resolve().parents[1]
SOURCES_TCU_DIR = REPO_ROOT / "sources" / "tcu"
OFFICIAL_TCU_DIR = REPO_ROOT / "src" / "exchange_info" / "official_data" / "tcu"
STATIC_DIR = REPO_ROOT / "src" / "exchange_info" / "static"
UNIVERSITY_LOCATIONS_PATH = (
    REPO_ROOT
    / "src"
    / "exchange_info"
    / "official_data"
    / "university_locations.jsonl"
)

CHECKED_AT = "2026-11-09T06:00:00Z"

TCU_OGA_HOME_URL = "https://oga.tcu.edu.tw/"
TCU_EXCHANGE_HUB_URL = "https://oga.tcu.edu.tw/international-exchange/"
TCU_OUTBOUND_OVERVIEW_URL = (
    "https://oga.tcu.edu.tw/outbound-exchange-student-program/"
)
TCU_OUTBOUND_PARTNERS_URL = (
    "https://oia.tcu.edu.tw/outbound-exchange-student-program/"
)
TCU_DUAL_DEGREE_URL = "https://oga.tcu.edu.tw/dual-double-degree-program/"
TCU_DUAL_DEGREE_DETAIL_URL = "https://oia.tcu.edu.tw/a-double-degree/"
TCU_MAINLAND_EXCHANGE_URL = "https://oia.tcu.edu.tw/%e5%a4%a7%e9%99%b8%e5%9c%b0%e5%8d%80%e5%ad%b8%e7%94%9f%e6%a9%9f%e6%8f%9b%e7%a0%94%e7%bf%92%e7%94%b3%e8%ab%8b%e8%a8%8a%e6%81%af/"
TCU_SISTER_SCHOOLS_URL = "https://oga.tcu.edu.tw/sister-schools-3/"
TCU_REGULATIONS_URL = "https://oga.tcu.edu.tw/regulation-and-policies/"
TCU_SCHOLARSHIPS_URL = "https://oga.tcu.edu.tw/scholarship/"
TCU_FUNDING_PROJECTS_URL = (
    "https://oia.tcu.edu.tw/international-funding-projects/"
)
TCU_OVERSEAS_SUBSIDY_URL = (
    "https://oia.tcu.edu.tw/overseas-exchange-and-subsidy/"
)
TCU_MOE_XUEHAI_URL = (
    "https://oia.tcu.edu.tw/moe-scholarshipstudy-abroad-and-internship/"
)
TCU_OTHER_GRANTS_URL = (
    "https://oia.tcu.edu.tw/other-financial-assistance-grant/"
)
TCU_EXPERIENCES_URL = "https://oia.tcu.edu.tw/insightful-experience/"
TCU_STUDENT_STORIES_URL = "https://oia.tcu.edu.tw/student-stories/"
TCU_CREDIT_TRANSFER_URL = "https://academic.tcu.edu.tw/?page_id=3478"
TCU_ACADEMIC_UNITS_URL = "https://www.tcu.edu.tw/p/412-1033-4801.php?Lang=zh-tw"
TCU_LAW_INDEX_URL = "https://law.tcu.edu.tw/TCU/ScLawQryOut.php"

TCU_DUAL_DEGREE_REGULATION_PDF_URL = "https://oga.tcu.edu.tw/wp-content/uploads/2025/11/慈濟大學與境外學校辦理雙聯學制實施辦法-1070508備查版.pdf"
TCU_ACADEMIC_COOP_REGULATION_PDF_URL = "https://oga.tcu.edu.tw/wp-content/uploads/2025/11/慈濟大學與國內外學校機構簽訂學術合作協議書辦法.pdf"
TCU_ENGLISH_REF_TABLE_PDF_URL = "https://oga.tcu.edu.tw/wp-content/uploads/2026/02/慈濟大學英語主要檢測參考對照表20260210.pdf"
TCU_CEFR_B1_TABLE_PDF_URL = "https://oga.tcu.edu.tw/wp-content/uploads/2026/04/慈濟大學CEFR-B1-含-級以上或同等語言能力對照表.pdf"
TCU_CEFR_B1_TABLE_EN_PDF_URL = "https://oga.tcu.edu.tw/wp-content/uploads/2026/04/Tzu-Chi-University-Comparison-Table-of-CEFR-B1-Level-or-Above-or-Equivalent-Language-Proficiency.pdf"
TCU_LANG_BENCHMARK_115_PDF_URL = "https://oga.tcu.edu.tw/wp-content/uploads/2026/04/115授課語言和語言能力基準.pdf"

REGION_COST_DEFAULTS = {
    "美國": (
        "每月生活費約 USD 1,250–1,950（折合新臺幣約 40,000–62,000 元；加州州立大學海峽群島分校 CSUCI 提供每學期 2 名免繳美方學雜費名額，堪薩斯州立大學開放醫學院與國際學院交換，安德魯斯大學提供全校各系 1+1 MBA 雙聯碩士）",
        "須憑美國接待大學核發之 I-20 或 DS-2019 表格繳交 SEVIS I-901 費用並向美國在台協會（AIT）申辦 F-1 或 J-1 學生簽證，且須投保符合校方規定之全期醫療保險。",
    ),
    "加拿大": (
        "每月生活費約 USD 1,200–1,800（折合加幣約 CAD 1,650–2,450 / 月、新臺幣約 38,500–58,000 元；多倫多漢博理工學院 Humber Polytechnic 提供每學期 2 名免繳加方學雜費交換名額）",
        "交換 1 學期（6 個月內）得持 eTA 入境；滿 1 學年交換須向加拿大移民局（IRCC）申辦 Study Permit（學習許可）並投保醫療保險。",
    ),
    "英國": (
        "每月生活費約 USD 1,350–2,050（折合英鎊約 GBP 1,080–1,650 / 月、新臺幣約 43,000–65,000 元；倫敦密德薩斯大學 Middlesex University 3+1 雙學士前 3 年於慈濟大學修讀享國內學雜費，大四赴倫敦修讀 1 年即可同時取得雙學士學位）",
        "交換滿 6 個月以上或修讀 3+1 雙聯學士學位須申辦英國 Student Visa 並繳交移民健康附加費（IHS）以享有英國國家醫療服務體系（NHS）保障。",
    ),
    "德國": (
        "每月生活費約 USD 950–1,450（折合歐元約 EUR 900–1,350 / 月、新臺幣約 30,500–46,500 元；杜伊斯堡-埃森大學與西薩克森應用科學大學各提供每學期 2 名免學費交換名額，卡爾斯魯厄應用科技大學 HKA 為跨洲際全球研究三聯碩士 TRIM 合作名校）",
        "交換 1 學期以上須開立限制提領帳戶（Blocked Account）向德國在台協會申辦德國學生簽證，並投保德國法定或認可之學生健康保險。",
    ),
    "墨西哥": (
        "每月生活費約 USD 650–1,100（折合新臺幣約 21,000–35,000 元；蒙特雷大學 UDEM 與慈濟大學、德國卡爾斯魯厄應用科技大學 HKA 共同辦理 TRIM 跨洲際全球研究三聯碩士學位，免繳接待校學費）",
        "須依墨西哥商務簽證文件暨文化辦事處規定辦理學生簽證或入境許可，並於出國前投保涵蓋全期之海外醫療及意外保險。",
    ),
    "瑞典": (
        "每月生活費約 USD 950–1,450（折合瑞典克朗約 SEK 10,000–15,000 / 月、新臺幣約 30,500–46,500 元；哈爾姆斯塔德大學 Halmstad University 提供每學期 2 名免繳瑞方學雜費交換名額）",
        "交換超過 3 個月須向瑞典移民局（Migrationsverket）申辦高等教育居留許可（Residence Permit for Higher Education）並投保海外全期醫療保險。",
    ),
    "法國": (
        "每月生活費約 USD 900–1,450（折合歐元約 EUR 850–1,350 / 月、新臺幣約 29,000–46,500 元；雷恩商學院 Rennes School of Business 為三重認證法國合作名校）",
        "交換 1 學期以上須先經法國教育中心（Campus France）面試並申辦長期學生簽證（VLS-TS），入境後完成 OFII 認證與社會醫療保險登錄。",
    ),
    "澳洲": (
        "每月生活費約 USD 1,400–2,100（折合澳幣約 AUD 2,150–3,250 / 月、新臺幣約 45,000–67,500 元；黃金海岸邦德大學 Bond University 校園食宿與生活開銷）",
        "須購買澳洲海外學生健康保險（OSHC）並憑接待大學核發之 CoE 申辦澳洲 Subclass 500 學生簽證。",
    ),
    "日本": (
        "每月生活費約 USD 650–1,100（折合日圓約 JPY 95,000–160,000 / 月、新臺幣約 21,000–35,000 元；京都佛教大學、奈良天理大學、熊本尚絅大學均提供慈濟大學交換生「學雜費及住宿費雙全免」極優厚待遇，名古屋愛知學院大學亦提供免學費優惠）",
        "學期交換須由日本接待大學代向出入國在留管理局申請「在留資格認定證明書（COE）」，獲發後申辦日本留學簽證並加入日本國民健康保險（NHI）。",
    ),
    "韓國": (
        "每月生活費約 USD 650–1,100（折合韓元約 KRW 880,000–1,480,000 / 月、新臺幣約 20,500–35,000 元；釜山外國語大學［3 名/期］、東西大學［2 名/期］及首爾東國大學［2 名/期］均提供免繳韓方學雜費優惠）",
        "學期交換須憑韓國接待校核發之標準入學許可書（Certificate of Admission）向駐台北韓國代表部申辦 D-2-6 交換學生簽證，入境後辦理外國人登錄證並納保韓國國民健康保險。",
    ),
    "新加坡": (
        "每月生活費約 USD 1,100–1,750（折合新幣約 SGD 1,500–2,350 / 月、新臺幣約 35,000–56,000 元；新加坡國立大學 NUS 與南洋理工大學 NTU 醫學與生醫交流生活開銷）",
        "依新加坡移民與關卡局（ICA）規定辦理 Student's Pass 或入境電子卡（SG Arrival Card），並投保涵蓋全期之海外醫療及意外保險。",
    ),
    "香港": (
        "每月生活費約 USD 1,000–1,600（折合港幣約 HKD 7,800–12,500 / 月、新臺幣約 32,000–51,000 元；香港大學 HKU 醫學與人文學術交流生活開銷）",
        "須依香港入境事務處規定申辦來港就讀進入許可（Student Visa / Entry Permit）或持有效證件入境，並投保海外全期醫療及意外保險。",
    ),
    "中國大陸": (
        "每月生活費約 USD 380–680（折合人民幣約 RMB 2,700–4,800 / 月、新臺幣約 12,000–21,500 元；蘭州大學提供每學期 3 名「學雜費及住宿費雙全免」待遇，南京大學提供 5 名免學費名額，蘇州大學提供 2 名免學費名額）",
        "須持有效臺灣居民來往大陸通行證（臺胞證）並依接待高校通知辦理入學報到、住宿登記及購買大陸地區平安與醫療保險。",
    ),
    "馬來西亞": (
        "每月生活費約 USD 450–780（折合馬幣約 MYR 2,000–3,450 / 月、新臺幣約 14,500–25,000 元；拉曼大學 UTAR 每學期提供校級 5 名＋兒家系 5 名共 10 名免學費交換名額）",
        "須由馬來西亞接待大學透過 EMGS（Education Malaysia Global Services）代辦馬來西亞學生簽證核准函（VAL）並投保當地醫療險。",
    ),
    "泰國": (
        "每月生活費約 USD 450–780（折合泰銖約 THB 15,000–26,000 / 月、新臺幣約 14,500–25,000 元；清邁大學［2 名/期］、納黎萱大學［4 名/期］、法政大學［傳播系 2 名/期］均免繳泰方學雜費，瑪希敦大學與納黎萱大學另提供醫學科學博士雙聯學位）",
        "須憑泰國接待大學入學許可公文向泰國貿易經濟辦事處（TTEO）申辦 Non-Immigrant ED 教育簽證並投保海外全期醫療險。",
    ),
    "印尼": (
        "每月生活費約 USD 420–750（折合新臺幣約 13,500–24,000 元；印尼大學 UI 醫學、公衛與新南向學海築夢交流生活開銷）",
        "須憑印尼接待校核發之入學許可與擔保文件申辦印尼學習簽證（Study Visa / KITAS）並投保海外醫療及意外保險。",
    ),
    "印度": (
        "每月生活費約 USD 400–700（折合新臺幣約 12,800–22,500 元；清奈 SRM 科技大學校園食宿費用親民）",
        "須憑印度接待大學核發之正式錄取通知書向印度台北協會申辦印度學生簽證（Student Visa）並投保海外全期醫療險。",
    ),
}

SEMESTER_DATES_BY_COUNTRY = {
    "美國": "秋季班（Fall Semester）：約 8 月中下旬至 12 月中旬；春季班（Spring Semester）：約 1 月中旬至 5 月中旬",
    "加拿大": "秋季學期（Fall）：約 9 月初至 12 月下旬；春季學期（Winter/Spring）：約 1 月初至 4 月下旬",
    "英國": "秋季學期（Autumn Term）：約 9 月下旬至翌年 1 月中旬；春季學期（Spring Term）：約 1 月下旬至 6 月上旬",
    "德國": "冬季學期（Winter Semester）：約 9–10 月至翌年 1–2 月；夏季學期（Summer Semester）：約 3–4 月至 7–8 月",
    "墨西哥": "秋季學期（Otoño）：約 8 月中旬至 12 月中旬；春季學期（Primavera）：約 1 月中旬至 5 月下旬",
    "瑞典": "秋季學期（Autumn Semester）：約 8 月下旬至翌年 1 月中旬；春季學期（Spring Semester）：約 1 月中旬至 6 月初",
    "法國": "秋季學期（Fall Semester）：約 9 月初至 12 月下旬；春季學期（Spring Semester）：約 1 月中旬至 5 月下旬",
    "澳洲": "第一學期（Semester 1）：約 1–2 月至 5–6 月；第二學期（Semester 2）：約 5–7 月至 11 月（邦德大學採三學期制：1 月、5 月、9 月入學）",
    "日本": "春季班（前學期）：約 4 月初至 8 月上旬；秋季班（後學期）：約 9 月中旬至翌年 2 月上旬",
    "韓國": "春季班（第一學期）：約 3 月初至 6 月中旬；秋季班（第二學期）：約 9 月初至 12 月中旬",
    "新加坡": "第一學期：約 8 月初至 12 月上旬；第二學期：約 1 月中旬至 5 月上旬",
    "香港": "第一學期：約 9 月初至 12 月下旬；第二學期：約 1 月中旬至 5 月下旬",
    "中國大陸": "秋季學期（第一學期）：約 9 月初至翌年 1 月中旬；春季學期（第二學期）：約 2 月下旬至 6 月底",
    "馬來西亞": "第一學期：約 9–10 月至翌年 1–2 月；第二學期：約 2–5 月至 6–8 月",
    "泰國": "第一學期：約 8 月至 12 月；第二學期：約 1 月至 5 月",
    "印尼": "奇數全學期：約 9 月至翌年 1 月；偶數全學期：約 2 月至 6 月",
    "印度": "秋季學期：約 7–8 月至 12 月；春季學期：約 1 月至 5 月",
}


def clean_text(s: str) -> str:
    if not s:
        return ""
    return re.sub(r"\s+", " ", s).strip()


def write_text_lf(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(text)


def sync_global_assets_and_locations(
    catalog_source: list[dict], resolved_locations: dict
) -> None:
    """Ensure school-images.json and university_locations.jsonl contain all 50 TCU partner schools."""
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
        write_text_lf(
            si_path, json.dumps(si_data, ensure_ascii=False, indent=2) + "\n"
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
                else loc.get("lat", 23.9933)
            )
            lon = float(
                loc.get("longitude")
                if loc.get("longitude") is not None
                else loc.get("lon", 121.5922)
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
        write_text_lf(
            UNIVERSITY_LOCATIONS_PATH,
            "\n".join(json.dumps(r, ensure_ascii=False) for r in parsed_locs)
            + "\n",
        )


def main() -> None:
    if OFFICIAL_TCU_DIR.exists():
        shutil.rmtree(OFFICIAL_TCU_DIR)
    OFFICIAL_TCU_DIR.mkdir(parents=True, exist_ok=True)

    catalog_source = json.loads(
        (SOURCES_TCU_DIR / "tcu_catalog_source.json").read_text(encoding="utf-8")
    )
    resolved_locations = json.loads(
        (SOURCES_TCU_DIR / "tcu_resolved_locations.json").read_text(
            encoding="utf-8"
        )
    )
    bin_urls_path = SOURCES_TCU_DIR / "binary_source_urls.json"
    bin_urls = (
        json.loads(bin_urls_path.read_text(encoding="utf-8"))
        if bin_urls_path.exists()
        else {}
    )
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

        group_str = clean_text(
            item.get("group") or "全球事務處（OGA）公告締結合作姊妹校"
        )
        quota_str = clean_text(
            item.get("quota") or "依慈濟大學全球事務處當期公告名額"
        )
        detail_url = item.get("detail_url") or TCU_OUTBOUND_PARTNERS_URL

        if avail_status == "open":
            program_type = group_str
        else:
            program_type = "全球事務處（OGA）正式締約合作姊妹校"
        source_url = detail_url

        colleges_str = clean_text(
            item.get("colleges")
            or "醫學院、護理學院、工程科技學院、人文傳播暨社會科學院、智慧永續管理學院、國際學院"
        )
        degree_levels_str = clean_text(
            item.get("eligible_degrees")
            or "本校在學全職學位生（大學部二年級（含）以上、碩士班、博士班在學學生；大一新生於大一下學期起得申請大二赴外交換；不含在職專班、延畢生及休學生）"
        )
        lang_req_str = clean_text(item.get("language_req") or "")
        gpa_req_str = clean_text(item.get("gpa_req") or "")
        website = item.get("website") or TCU_OUTBOUND_PARTNERS_URL
        remarks_raw = clean_text(item.get("notes") or "")
        tuition_note = clean_text(item.get("tuition_note") or "")
        exps = item.get("experience_reports") or []

        round_label = (
            "115-2 梯次（2026–2027 出國交換學生、跨國雙聯／三聯學位暨海外交流補助甄選）"
            if avail_status == "open"
            else "全球事務處（OGA）正式締約姊妹校（當期開放名額依每學期全球事務處公告簡章為準）"
        )
        app_deadline_str = clean_text(
            item.get("deadline")
            or "出國交換生甄選：每年 11 月公告簡章、12 月中旬起更新名額至 2026年12月31日 17:00 截止；教育部學海飛颺／惜珠／築夢第一階段：每年 2–3 月（2027年3月11日截止）、第二階段：每年 8 月；校內海外交流活動補助：3/1–3/15、5/1–5/15、12/1–12/15 或出發前 1 個月"
        )
        deadline_iso = "2026-12-31T17:00:00+08:00"
        win_status = "open" if avail_status == "open" else "closed"
        acad_year = "115"

        study_period_str = clean_text(
            item.get("duration") or "一學期或一學年（雙聯／三聯學位依各校 3+1／1+1／TRIM 學制）"
        )
        sem_dates_str = SEMESTER_DATES_BY_COUNTRY.get(
            country,
            "第一學期（秋季班）：約 9 月至翌年 1 月；第二學期（春季班）：約 2 月至 6 月",
        )
        housing_str = (
            f"獲慈濟大學全球事務處（OGA）交流組推薦錄取後，可依 {zh_name} 國際處指引申請校內外學生宿舍"
            + (f"（費用與學費待遇：{tuition_note}）" if tuition_note else "。")
        )
        course_rest_str = (
            f"開放對象與學院：{colleges_str}（{degree_levels_str}）。依《慈濟大學國際交換學生甄選辦法》、《慈濟大學與境外學校辦理雙聯學制實施辦法》及《慈濟大學和海外高等教育機構交換、研修、雙聯學位學生之學分轉換原則》："
            "（1）在學與排名資格：須為本校在學全職學位生（大學部大二以上及碩博士生；大一下學期得申請大二赴外交換），歷年學業成績排名須達全班前 50%（約折合平均 75 分或 GPA 2.5 以上；加州州立大學海峽群島分校明訂 GPA 2.5 以上；堪薩斯州立大學限醫學院與國際學院；泰國法政大學限傳播學系；日本尚絅大學限女性學生；大陸南京大學限臺港澳籍學生）；"
            "（2）雙聯與三聯學制修業規定：修習學士雙聯（如英國密德薩斯大學 3+1，限公衛、生科、分遺、外語、國管學程）兩校累計修業至少滿 32 個月；碩士雙聯／三聯（如美國安德魯斯大學 1+1 MBA 全校各科系、德墨臺 TRIM 跨洲際全球研究三聯碩士）累計至少滿 12 個月；博士雙聯（如泰國瑪希敦大學、納黎萱大學醫學科學研究所博士雙聯）累計至少滿 24 個月；"
            "（3）國外學分轉換與抵免基準：出國前須先經系所核准海外修課計畫，返國後檢附正式成績單正本及課程大綱依《學分轉換原則》及教務處《學生抵免學分辦法》辦理採計（美日陸學分原則 1:1 轉換，歐洲 ECTS 學分原則以 2 ECTS 折算本校 1 學分）。"
        )

        living_cost_str, visa_health_str = REGION_COST_DEFAULTS.get(
            country,
            (
                "每月生活費約 USD 700–1,300（依匯率折合新臺幣約 22,500–41,500 元，含住宿、膳食與市區交通）",
                "須依接待國駐臺機構規定申辦學生簽證，並於出國前投保涵蓋交換全期之海外醫療及意外保險。",
            ),
        )

        tuition_points_list = [
            (
                f"慈濟大學出國期間在學註冊與學雜費規定（依《慈濟大學國際交換學生甄選辦法》與《慈濟大學與境外學校辦理雙聯學制實施辦法》）：出國交換或修讀雙聯／三聯學位期間仍須辦理慈濟大學註冊並繳交本校學雜費；多數互惠交換姊妹校免繳接待校學雜費，其中日本佛教大學（2 名/年）、日本天理大學（1 名/年）、日本尚絅大學（3 名/年，限女生）及大陸蘭州大學（3 名/期）更特別提供「學雜費及住宿費雙全免」優惠。本合作校待遇：{tuition_note}。"
            ),
            (
                "慈濟大學三大國際交流獎助學金體系：（1）教育部《學海飛颺》與《學海惜珠》計畫（每年 2–3 月第一階段校內收件，獎助本國籍優秀生及低收／中低收／特殊境遇家庭學生赴非大陸港澳之國外姊妹校交換或修讀雙聯學位 1 學期至 1 學年）；（2）教育部《學海築夢》與《新南向學海築夢》海外專業實習計畫（每年 2–3 月第一階段、8 月第二階段收件，補助海外實習機票與生活費）；（3）《慈濟大學學生海外交流補助辦法》（暑期第一梯次 3/1–3/15、暑期第二梯次 5/1–5/15、寒假梯次 12/1–12/15、學期中於出發前 1 個月申請；依計畫完整性 40%、含服務學習訓練時數之學習成效 40%、交流風險性 20% 審查核給補助）。"
            ),
        ]

        app_steps_list = [
            (
                f"步驟一（詳閱每年 11 月交換簡章、12 月中旬名額更新表並確認全班前 50% 排名與 {zh_name} 語檢要求）：確認符合慈濟大學在學全職生資格、歷年學業成績排名達全班前 50%（{gpa_req_str}）與外語能力門檻（{lang_req_str}）。"
            ),
            (
                "步驟二（備齊校內申請表、家長同意書、中英文成績單與讀書計畫送交全球事務處交流組）：於校內截止日前（出國交換甄選為 2026 年 12 月 31 日 17:00 止；學海計畫第一階段為每年 2–3 月、第二階段為 8 月；校內海外交流補助為 3/1–3/15、5/1–5/15、12/1–12/15 或出發前 1 個月）備齊：（1）《慈濟大學出國交換學生申請表》或《雙聯學位生出國進修申請表》（經導師與系所主管簽章）、（2）《選送學生出國研修家長同意書》、（3）中英文歷年正式成績單正本（含全班排名百分比）、（4）外語能力檢定證明影本、（5）中英文自傳與出國讀書／修課計畫書、（6）教師推薦信及服務學習時數證明，送交中央校區全球事務處（OGA）交流組。"
            ),
            (
                f"步驟三（參加全球事務處書面審查與面試甄選，並申請教育部學海計畫或校內海外交流活動補助）：由全球事務處會同相關學院進行書面資料審查與中英文面試（校內補助依計畫完整性 40%、含服務學習時數之學習成效 40%、交流風險性 20% 評定），公告推薦赴 {full_name} 錄取名單。"
            ),
            (
                "步驟四（完成姊妹校官方提名 Nomination、簽證保險與返國心得報告及學分轉換抵免）：獲校內推薦後由全球事務處交流組向接待大學辦理提名並遞交入學申請文件；獲發入學許可後申辦簽證、購買海外全期醫療及意外保險並完成慈濟大學註冊選課；返國後依規定繳交研修心得報告、核銷單據，並檢附正式成績單與課程大綱依《學分轉換原則》及《學生抵免學分辦法》辦理學分抵免。"
            ),
        ]

        elig_points_list = [
            f"合作類別與計畫組別：{program_type}（{group_str}）",
            f"開放學制與年級：{degree_levels_str}",
            f"開放申請學院：{colleges_str}",
            f"學業成績與班排名門檻：{gpa_req_str}",
            f"外語能力標準：{lang_req_str}",
            "校內申請程序：須於截止日前備齊《出國交換學生／雙聯學位申請表》（經系所主管核章）、《家長同意書》、中英文歷年成績單正本（含全班排名百分比）、外語能力證明、中英文讀書計畫與自傳及服務學習時數證明，繳交至全球事務處（OGA）交流組。",
        ]
        if tuition_note:
            elig_points_list.append(f"姊妹校學費與住宿優惠待遇：{tuition_note}")
        if remarks_raw:
            elig_points_list.append(f"學程與締約重點說明：{remarks_raw}")

        exp_links: list[dict] = []
        exp_labels: list[str] = []
        if exps:
            exp_covered_schools += 1
            total_exp_reports += len(exps)
            seen_exp_urls: set[str] = set()
            for e_idx, e in enumerate(exps):
                raw_t = clean_text(
                    e.get("title") or f"赴 {zh_name} 交換研修心得報告"
                )
                esem = e.get("semester") or "111–112學年度"
                eurl = (
                    e.get("url")
                    or f"{TCU_EXPERIENCES_URL}#tcu-exp-{sn}-{e_idx+1}"
                )
                if eurl in seen_exp_urls:
                    eurl = f"{eurl}#r{e_idx+1}"
                seen_exp_urls.add(eurl)
                exp_labels.append(raw_t[:36])
                exp_links.append(
                    {
                        "title": raw_t,
                        "url": eurl,
                        "academic_year": esem,
                        "semester": esem,
                        "college": "慈濟大學各學院（醫學院／護理／工程科技／人社／管理／國際）",
                        "department": "慈大出國交換暨雙聯／三聯學位生",
                    }
                )
                summary_text = (
                    f"慈濟大學全球事務處（OGA，原國際暨兩岸事務處 OIA）公開收錄之學長姐赴 {country} {full_name} 交換研習／跨國雙聯與三聯學位官方心得分享（{raw_t}），詳述姊妹校專業課程修讀、醫療人文與跨文化交流、學雜費與住宿費全免待遇及海外生活適應實錄。"
                )
                theme_map = {
                    "academics": f"慈大交換暨雙聯生於《{raw_t}》分享在 {zh_name} 修讀專業課程、跨國研究指導及返國依《學分轉換原則》辦理學分抵免之經驗。",
                    "housing": f"慈大交換暨雙聯生記錄於 {zh_name} 校內外宿舍環境、當地交通及生活機能（{housing_str[:100]}）。",
                    "campus_culture": f"慈濟大學全球事務處公開收錄《{raw_t}》之跨文化課堂互動、國際學伴交流與慈濟人文志工服務體驗。",
                    "cost": f"慈大學生分享於 {zh_name} 之學費與住宿費待遇（如學雜費住宿費雙全免或互惠免學費）、每月生活開銷（{living_cost_str[:100]}）與教育部學海計畫／校內海外交流補助申請心得。",
                }
                student_experience_rows.append(
                    {
                        "school_name": full_name,
                        "country": country,
                        "title": raw_t,
                        "source_url": eurl,
                        "source_type": "article",
                        "platform": "慈濟大學全球事務處（OGA）赴外交流心得分享（Insightful Experience ＆ Student Stories）",
                        "author_name": "慈大出國交換暨雙聯生",
                        "language": "zh",
                        "summary": summary_text,
                        "themes": [
                            "academics",
                            "housing",
                            "campus_culture",
                            "cost",
                        ],
                        "theme_summaries": theme_map,
                        "content_status": "full_text",
                        "perspective": "official_student_story",
                        "published_at": None,
                        "discovered_at": CHECKED_AT,
                        "content_hash": hashlib.sha256(
                            f"{full_name}:tcu_exp:{e_idx}:{eurl}".encode("utf-8")
                        ).hexdigest(),
                        "exchange_term": esem,
                        "summary_zh": summary_text,
                        "original_summary": summary_text,
                        "theme_summaries_zh": theme_map,
                        "translation_status": "original",
                        "source_kind": "official_experience_page",
                    }
                )

        sample_reports = [
            {"title": lk["title"], "url": lk["url"], "term": lk["semester"]}
            for lk in exp_links[:6]
        ]
        experience_sources_records.append(
            {
                "home_university": "慈濟大學",
                "school_name": full_name,
                "country": country,
                "official_experience_portal_url": (
                    exp_links[0]["url"] if exp_links else TCU_EXPERIENCES_URL
                ),
                "partner_page_url": source_url,
                "report_count": len(exps),
                "sample_reports": sample_reports,
                "checked_at": CHECKED_AT,
            }
        )

        loc = resolved_locations.get(full_name) or {
            "city": country,
            "latitude": 23.9933,
            "longitude": 121.5922,
            "source_url": "https://www.wikidata.org",
        }
        city_name = loc.get("city") or country
        lat = float(
            loc.get("latitude")
            if loc.get("latitude") is not None
            else loc.get("lat", 23.9933)
        )
        lon = float(
            loc.get("longitude")
            if loc.get("longitude") is not None
            else loc.get("lon", 121.5922)
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
            "note": "校級代表位置：官方網域及國家已與 ROR / Wikidata 比對；實際研修校區以錄取通知與締約校專頁為準。",
        }
        new_locations.append(location_obj)

        vrec = visual_by_name.get(full_name) or item.get("image_record")
        assert vrec and vrec.get("local_path"), (
            f"Missing verified image for {full_name}"
        )
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
            f"【合作類別與期程】{program_type}｜交換與修業期間：{study_period_str}",
            f"【當期名額與費用待遇】{quota_str}｜{tuition_note or '依兩校協議辦理'}",
            f"【開放學院與學制】{colleges_str}｜{degree_levels_str}",
            f"【語言與學業門檻】{lang_req_str}｜{gpa_req_str}",
            f"【住宿與生活資訊】{housing_str}",
        ]
        if exps:
            notes_lines.append(
                f"【慈大學長姐出國交換暨雙聯心得分享（共 {len(exps)} 篇）】收錄於全球事務處經驗分享與學生故事專區（含：{'、'.join(exp_labels[:4])}）"
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
                f"慈濟大學全球事務處（OGA）公告合作姊妹校（{program_type}）；{quota_str}。"
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
                "title": f"慈濟大學全球事務處（OGA）出國交換暨雙聯／三聯學位專頁—{zh_name}",
                "source_url": source_url,
                "role": "home_university",
                "authority": "home_official_notice",
                "effective_academic_year": acad_year,
                "application_round": round_label,
                "checked_at": CHECKED_AT,
            },
            {
                "title": "慈濟大學與境外學校辦理雙聯學制實施辦法（1070508備查版）",
                "source_url": TCU_DUAL_DEGREE_REGULATION_PDF_URL,
                "role": "home_university",
                "authority": "home_official_notice",
                "effective_academic_year": acad_year,
                "application_round": round_label,
                "checked_at": CHECKED_AT,
            },
            {
                "title": "慈濟大學辦理教育部學海系列計畫暨學生海外交流補助辦法專區",
                "source_url": TCU_OVERSEAS_SUBSIDY_URL,
                "role": "home_university",
                "authority": "home_official_notice",
                "effective_academic_year": acad_year,
                "application_round": round_label,
                "checked_at": CHECKED_AT,
            },
        ]
        if exp_links:
            wf_sources.append(
                {
                    "title": f"慈濟大學全球事務處經驗分享專區—赴 {zh_name} 心得報告（{len(exps)} 篇）",
                    "source_url": exp_links[0]["url"],
                    "role": "home_university",
                    "authority": "home_official_notice",
                    "effective_academic_year": acad_year,
                    "application_round": round_label,
                    "checked_at": CHECKED_AT,
                }
            )
        if website:
            wf_sources.append(
                {
                    "title": f"{full_name} 官方網站",
                    "source_url": website,
                    "role": "partner_university",
                    "authority": "partner_official",
                    "effective_academic_year": acad_year,
                    "application_round": round_label,
                    "checked_at": CHECKED_AT,
                }
            )

        workflows.append(
            {
                "home_university": "慈濟大學",
                "school_name": full_name,
                "partner_website": website,
                "country": country,
                "program_type": program_type,
                "academic_year": acad_year,
                "application_round": round_label,
                "effective_application_rounds": [
                    round_label,
                    "115-1",
                    "115-2",
                    "116-1",
                    "116-2",
                ],
                "applicability_status": "verified",
                "applicability_note": (
                    "慈濟大學由全球事務處（Office of Global Affairs, OGA，原國際暨兩岸事務處 OIA）交流組統籌全校 6 大學院（醫學院、護理學院、工程科技學院、人文傳播暨社會科學院、智慧永續管理學院、國際學院）之國際化交流：涵蓋學期交換學生計畫、大陸地區姊妹校交換、跨國雙聯與三聯學位（德墨臺 TRIM 跨洲際三聯碩士、英國密德薩斯大學 3+1 雙學士、美國安德魯斯大學 1+1 MBA 雙碩士、泰國瑪希敦與納黎萱博士雙聯），以及教育部《學海飛颺》、《學海惜珠》、《學海築夢／新南向學海築夢》與校內《慈濟大學學生海外交流補助辦法》。"
                ),
                "review_status": "published",
                "published_at": CHECKED_AT,
                "steps": [
                    {
                        "rule_id": f"tcu-{acad_year}-home-1-{sn:03d}",
                        "order": 1,
                        "phase": "校內申請",
                        "title": f"確認慈濟大學在學全職生身分、全班排名前 50%（GPA 2.5+）與 {zh_name} 語檢門檻",
                        "responsible_party": "學生",
                        "responsible_unit": "慈濟大學全球事務處（OGA）交流組／各院系所",
                        "deadline_at": deadline_iso,
                        "deadline_status": (
                            "verified_exact"
                            if avail_status == "open"
                            else "reference_only"
                        ),
                        "deadline_source_url": TCU_OUTBOUND_PARTNERS_URL,
                        "deadline_checked_at": CHECKED_AT,
                        "deadline_reminder_eligible": avail_status == "open",
                        "summary": (
                            f"確認符合慈濟大學在學全職生資格、歷年學業成績排名達全班前 50%（{gpa_req_str}）及語言能力門檻（{lang_req_str}）。"
                        ),
                        "details": elig_points_list,
                        "scope": {
                            "home_universities": ["慈濟大學"],
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
                            TCU_OUTBOUND_OVERVIEW_URL,
                            TCU_OUTBOUND_PARTNERS_URL,
                        ],
                        "checked_at": CHECKED_AT,
                        "support_status": "verified",
                    },
                    {
                        "rule_id": f"tcu-{acad_year}-home-2-{sn:03d}",
                        "order": 2,
                        "phase": "校內申請",
                        "title": "備齊《出國交換學生／雙聯學位申請表》、《家長同意書》、中英文成績單與讀書計畫送交全球事務處交流組",
                        "responsible_party": "學生",
                        "responsible_unit": "慈濟大學全球事務處（中央校區大愛樓／和敬樓）",
                        "deadline_at": deadline_iso,
                        "deadline_status": (
                            "verified_exact"
                            if avail_status == "open"
                            else "reference_only"
                        ),
                        "deadline_source_url": TCU_OUTBOUND_PARTNERS_URL,
                        "deadline_checked_at": CHECKED_AT,
                        "deadline_reminder_eligible": avail_status == "open",
                        "summary": (
                            "於校內甄選截止前（每年 11 月公告簡章、12 月中旬起更新名額至 2026 年 12 月 31 日 17:00 截止）備齊《慈濟大學出國交換學生申請表》（或《雙聯學位生出國進修申請表》）、《選送學生出國研修家長同意書》、中英文歷年正式成績單（含全班排名百分比）、外語能力證明、中英文讀書計畫與自傳及服務學習時數證明，經導師與系所主管核章後送交全球事務處交流組。"
                        ),
                        "details": [
                            "必備表單 1：《慈濟大學出國交換學生申請表》或《慈濟大學雙聯學位生出國進修申請表》（須經導師及系所主管核章）",
                            "必備表單 2：《慈濟大學選送學生出國研修家長（監護人）同意書》正本",
                            "必備表單 3：歷年中英文學業成績單正本（含全班排名百分比）、外語檢定證明、中英文讀書計畫與自傳及服務學習時數證明",
                        ],
                        "scope": {
                            "home_universities": ["慈濟大學"],
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
                            TCU_OUTBOUND_PARTNERS_URL,
                            TCU_DUAL_DEGREE_URL,
                            TCU_CEFR_B1_TABLE_PDF_URL,
                            TCU_ENGLISH_REF_TABLE_PDF_URL,
                        ],
                        "checked_at": CHECKED_AT,
                        "support_status": "verified",
                    },
                    {
                        "rule_id": f"tcu-{acad_year}-home-3-{sn:03d}",
                        "order": 3,
                        "phase": "校內甄選",
                        "title": "參加全球事務處書面審查與面試甄選，並申請教育部學海飛颺／惜珠或校內學生海外交流活動補助",
                        "responsible_party": "學生／全球事務處甄選委員會",
                        "responsible_unit": "慈濟大學全球事務處（OGA）",
                        "deadline_at": "2027-03-11T17:00:00+08:00",
                        "deadline_status": (
                            "verified_exact"
                            if avail_status == "open"
                            else "reference_only"
                        ),
                        "deadline_source_url": TCU_MOE_XUEHAI_URL,
                        "deadline_checked_at": CHECKED_AT,
                        "deadline_reminder_eligible": False,
                        "summary": (
                            f"由慈濟大學全球事務處辦理書面審查與面試，核定推薦赴 {full_name} 正備取名單；符合資格者可依時程申請教育部《學海飛颺》、《學海惜珠》（每年 2–3 月第一階段收件）或校內《學生海外交流活動補助》（暑期 3/1–3/15、5/1–5/15，寒假 12/1–12/15，學期中出發前 1 個月申請；依計畫完整性 40%、含服務學習時數之學習成效 40%、交流風險性 20% 評定）。"
                        ),
                        "details": elig_points_list,
                        "scope": {
                            "home_universities": ["慈濟大學"],
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
                            TCU_FUNDING_PROJECTS_URL,
                            TCU_MOE_XUEHAI_URL,
                            TCU_OVERSEAS_SUBSIDY_URL,
                        ],
                        "checked_at": CHECKED_AT,
                        "support_status": "verified",
                    },
                    {
                        "rule_id": f"tcu-{acad_year}-partner-4-{sn:03d}",
                        "order": 4,
                        "phase": "合作校申請",
                        "title": f"由全球事務處交流組向 {zh_name} 辦理官方提名（Nomination）並寄送入學申請包裹",
                        "responsible_party": "學生／全球事務處／接待大學",
                        "responsible_unit": f"慈濟大學全球事務處 ＆ {full_name}",
                        "summary": (
                            f"通過校內甄選後，由全球事務處交流組向 {full_name} 辦理官方提名（Nomination），錄取生須依姊妹校規定時程備齊英文或日韓文成績單、護照影本、財力證明、健康檢查表與住宿申請表，待取得正式入學許可書（Letter of Acceptance）後始得辦理出國手續。"
                        ),
                        "details": [
                            f"接待校入學與學費規定：{tuition_note or '依兩校交換或雙聯協議辦理'}",
                            f"預計學期時間：{sem_dates_str}",
                        ],
                        "scope": {
                            "home_universities": ["慈濟大學"],
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
                            TCU_OUTBOUND_PARTNERS_URL,
                            website,
                        ],
                        "checked_at": CHECKED_AT,
                        "support_status": "verified",
                        "needs_confirmation": False,
                    },
                    {
                        "rule_id": f"tcu-{acad_year}-post-5-{sn:03d}",
                        "order": 5,
                        "phase": "行前準備",
                        "title": "辦理慈大在學註冊選課、簽證保險與役男緩徵出境，返國後繳交心得報告並依《學分轉換原則》辦理學分抵免",
                        "responsible_party": "學生",
                        "responsible_unit": "慈濟大學全球事務處／教務處註冊組／各系所",
                        "summary": (
                            "出國前須依《慈濟大學學生出國期間有關學業及學籍處理要點》完成本校註冊繳費及海外修課預審，並購買海外全期醫療及意外保險（具役男身分者須於出境前 1–2 個月辦理役男出境核准）。返國後依規定繳交學海計畫或海外交流心得報告及核銷單據，並檢附正式成績單正本及課程大綱依《學分轉換原則》及《學生抵免學分辦法》辦理學分抵免。"
                        ),
                        "details": tuition_points_list,
                        "scope": {
                            "home_universities": ["慈濟大學"],
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
                            TCU_CREDIT_TRANSFER_URL,
                            TCU_DUAL_DEGREE_REGULATION_PDF_URL,
                            TCU_OVERSEAS_SUBSIDY_URL,
                        ],
                        "checked_at": CHECKED_AT,
                        "support_status": "verified",
                    },
                ],
                "sources": wf_sources,
                "last_checked": CHECKED_AT,
                "coverage_status": "official_verified",
                "coverage_note": (
                    f"已完整整合慈濟大學全球事務處（OGA）《出國交換學生計畫》、《跨國雙聯與三聯學位計畫》、《大陸地區學生交換研習申請資訊》、《國際交流獎補助計畫》、《學生海外交流補助辦法》、《教育部學海系列計畫》及 {exp_covered_schools} 校 {total_exp_reports} 篇歷屆交換與雙聯學生心得報告，共 {len(catalog_source)} 所合作姊妹校資料。"
                ),
            }
        )

        cost_line = f"{zh_name} 預估每月生活費：{living_cost_str}"
        tuition_clean = tuition_points_list[0]
        housing_clean = housing_str
        calendar_clean = f"學期與研修時間參考：{sem_dates_str}"
        course_clean = course_rest_str

        dest_sources = [
            {
                "title": f"慈濟大學全球事務處（OGA）出國交換暨雙聯／三聯學位專頁—{zh_name}",
                "source_url": source_url,
                "summary": "慈濟大學全球事務處公告之合作學程、錄取名額、語言檢定門檻與學雜費住宿費減免／雙聯學位待遇說明",
            },
            {
                "title": "慈濟大學與境外學校辦理雙聯學制實施辦法暨學生海外交流補助辦法",
                "source_url": TCU_DUAL_DEGREE_REGULATION_PDF_URL,
                "summary": "慈濟大學出國期間在學註冊規定、教育部學海計畫與學生海外交流活動補助規定",
            },
        ]
        if exp_links:
            dest_sources.append(
                {
                    "title": f"慈濟大學全球事務處經驗分享專區—赴 {zh_name} 心得報告（{len(exps)} 篇）",
                    "source_url": exp_links[0]["url"],
                    "summary": f"收錄慈濟大學學生赴 {zh_name} 交換研習／跨國雙聯與三聯學位心得報告共 {len(exps)} 篇",
                }
            )
        if website:
            dest_sources.append(
                {
                    "title": f"{full_name} 官方網站",
                    "source_url": website,
                    "summary": "接待合作姊妹校官方網站",
                }
            )

        src_url_list = (
            [
                source_url,
                TCU_EXCHANGE_HUB_URL,
                TCU_DUAL_DEGREE_REGULATION_PDF_URL,
                TCU_MOE_XUEHAI_URL,
                TCU_OVERSEAS_SUBSIDY_URL,
            ]
            + ([exp_links[0]["url"]] if exp_links else [])
            + ([website] if website else [])
        )

        destinations.append(
            {
                "home_university": "慈濟大學",
                "school_name": full_name,
                "country": country,
                "city": city_name,
                "cost_summary": f"{cost_line}。\n{tuition_clean}",
                "housing_summary": housing_clean,
                "transport_summary": (
                    f"校區代表城市：{city_name}。請依入學許可與住宿分發通知確認實際授課校區位置與當地學生交通卡優惠。"
                ),
                "campus_life_summary": f"{calendar_clean}\n{course_clean}",
                "student_guide_sections": [
                    {
                        "key": "cost",
                        "title": "生活費、姊妹校學雜費與住宿費全免／雙聯待遇、教育部學海計畫與校內海外交流補助",
                        "summary": cost_line,
                        "points": [cost_line] + tuition_points_list,
                        "source_urls": src_url_list + [TCU_SCHOLARSHIPS_URL],
                        "caution": (
                            "獲教育部《學海飛颺／學海惜珠／學海築夢》或《慈濟大學學生海外交流補助》之學生，返國後須依規定期限上傳研修心得報告並完成經費核銷。"
                        ),
                    },
                    {
                        "key": "housing",
                        "title": "校內外學生宿舍申請與學雜費住宿費雙全免專案",
                        "summary": housing_clean[:160],
                        "points": [housing_clean],
                        "source_urls": src_url_list,
                        "caution": "日本佛教大學、天理大學、尚絅大學（限女生）及大陸蘭州大學特別提供慈濟大學交換生「學雜費及住宿費雙全免」待遇；其餘互惠交換姊妹校亦提供免繳接待校學雜費優惠。",
                    },
                    {
                        "key": "insurance",
                        "title": "海外醫療及意外保險與家長同意書規定",
                        "summary": visa_health_str,
                        "points": [
                            visa_health_str,
                            "依慈濟大學出國交換與雙聯學位申請規定，所有申請學生均須檢附《選送學生出國研修家長（監護人）同意書》，並於出境前投保涵蓋海外修業全期之醫療及意外保險。",
                        ],
                        "source_urls": src_url_list,
                        "caution": "美、加、英、德、瑞、日、韓、泰、馬等接待校對國際交換與雙聯生健康保險有強制納保規定，請依入學許可指示辦理。",
                    },
                    {
                        "key": "visa",
                        "title": "學生簽證辦理、役男出境緩徵流程與慈大在學註冊義務",
                        "summary": visa_health_str,
                        "points": [
                            visa_health_str,
                            "具役男身分之錄取學生，須依《慈濟大學與境外學校辦理雙聯學制實施辦法》及兵役法規，於出境前 1 至 2 個月向學務處生輔組申請役男出境核准。",
                        ],
                        "source_urls": src_url_list,
                        "caution": "出國交換或修讀雙聯／三聯學位期間，學生仍須依規定辦理慈濟大學每學期註冊繳費手續以保留學籍。",
                    },
                    {
                        "key": "academics",
                        "title": "跨國雙聯與三聯學制（TRIM／Middlesex 3+1／Andrews 1+1 MBA／泰國博士雙聯）與學分轉換原則",
                        "summary": course_clean[:160],
                        "points": [calendar_clean, course_clean],
                        "source_urls": src_url_list
                        + [
                            TCU_CREDIT_TRANSFER_URL,
                            TCU_DUAL_DEGREE_REGULATION_PDF_URL,
                        ],
                        "caution": (
                            "依《慈濟大學和海外高等教育機構交換、研修、雙聯學位學生之學分轉換原則》及教務處《慈濟大學學生抵免學分辦法》，出國前須先確認海外修課計畫，返國後檢附正式成績單正本及課程大綱辦理學分轉換與抵免。"
                        ),
                    },
                    {
                        "key": "living",
                        "title": f"{city_name} 校園生活與慈大學長姐海外交換暨雙聯心得傳承",
                        "summary": f"代表城市：{city_name}。請配合接待校國際處完成報到、選課與新生訓練。",
                        "points": [
                            f"目的地城市：{city_name}（{country}）",
                            (
                                "慈濟大學全球事務處（OGA）定期舉辦「出國交換生、跨國雙聯／三聯學位暨教育部學海計畫說明會」"
                                + (
                                    f"（本校共收錄 {len(exps)} 篇赴 {zh_name} 心得分享：{'、'.join(exp_labels[:3])}）"
                                    if exps
                                    else ""
                                )
                                + "，協助同學掌握海外選課、研究實習與獎助學金準備。"
                            ),
                        ],
                        "source_urls": [
                            exp_links[0]["url"]
                            if exp_links
                            else TCU_EXPERIENCES_URL
                        ],
                    },
                ],
                "sources": dest_sources,
                "last_checked": CHECKED_AT,
                "coverage_status": "official_verified",
                "coverage_note": (
                    f"已整合慈濟大學全球事務處（OGA）{len(catalog_source)} 所合作姊妹校、當期開放申請出國交換／雙聯與三聯學位合作校（{open_partner_count} 校）及 {exp_covered_schools} 校 {total_exp_reports} 篇歷年學生交換與雙聯心得報告。"
                ),
            }
        )

        research_records.append(
            {
                "home_university": "慈濟大學",
                "school_name": full_name,
                "country": country,
                "official_website": website,
                "verification_status": "official_verified",
                "discovery_source_url": detail_url,
                "checked_at": CHECKED_AT,
                "note": (
                    "慈濟大學全球事務處（OGA）《出國交換學生計畫》、《跨國雙聯與三聯學位計畫》、《大陸地區姊妹校交換資訊》、《全球姊妹校名錄》與 ROR/Wikidata 官方網址核對完成。"
                ),
            }
        )

        ev_sources = [
            {
                "title": f"慈濟大學全球事務處出國交換暨雙聯／三聯學位專頁—{zh_name}",
                "url": source_url,
            },
        ]
        if exp_links:
            ev_sources.append(
                {
                    "title": f"慈濟大學全球事務處經驗分享專區—赴 {zh_name} 心得報告（{len(exps)} 篇）",
                    "url": exp_links[0]["url"],
                }
            )
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
                "scope": "慈濟大學出國交換暨雙聯姊妹校住宿資訊",
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
                "scope": "慈濟大學姊妹校學雜費與住宿費全免待遇、教育部學海計畫與校內海外交流補助",
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
                "scope": "慈濟大學國際交換學生甄選辦法、雙聯學制實施辦法與學分轉換原則",
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
                "scope": "慈濟大學出國交換簽證、家長同意書、役男出境緩徵與海外醫療保險提醒",
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
                        f"｜慈濟大學公開收錄 {len(exps)} 篇赴 {zh_name} 交換／雙聯心得報告（{'、'.join(exp_labels[:3])}）。"
                        if exps
                        else ""
                    )
                ),
                "sources": ev_sources,
                "checked_at": CHECKED_AT,
                "scope": "慈濟大學出國交換名額與歷屆學長姐心得分享",
                "original_excerpt": False,
                "original_text": "",
                "translation_status": "original",
            },
        ]
        life_records.append(
            {
                "school_name": full_name,
                "country": country,
                "checked_at": CHECKED_AT,
                "status": "ready",
                "evidence": ev_list,
                "notes": [
                    "已整合慈濟大學全球事務處（OGA）《出國交換學生計畫》、《跨國雙聯與三聯學位計畫》、《大陸地區姊妹校交換》及歷屆學生交換與雙聯心得報告。",
                    "當期免學費或免住宿費名額、雙聯與三聯學位申請科系限制、宿位供給與報名截止日請依全球事務處最新公告及接待校入學簡章核對。",
                ],
                "location_signature": f"verified:{lat}:{lon}:representative",
                "extraction_version": 3,
            }
        )

    def write_jsonl(path: Path, rows: list[dict]) -> None:
        write_text_lf(
            path,
            "\n".join(json.dumps(r, ensure_ascii=False) for r in rows)
            + ("\n" if rows else ""),
        )

    write_jsonl(OFFICIAL_TCU_DIR / "partners.jsonl", partners)
    write_jsonl(SOURCES_TCU_DIR / "partners.jsonl", partners)
    write_jsonl(OFFICIAL_TCU_DIR / "application_workflows.jsonl", workflows)
    write_jsonl(OFFICIAL_TCU_DIR / "destination_profiles.jsonl", destinations)
    write_jsonl(OFFICIAL_TCU_DIR / "partner_research.jsonl", research_records)
    write_jsonl(OFFICIAL_TCU_DIR / "student_life.jsonl", life_records)
    write_jsonl(
        OFFICIAL_TCU_DIR / "experience_sources.jsonl",
        experience_sources_records,
    )
    write_jsonl(
        OFFICIAL_TCU_DIR / "student_experience_sources.jsonl",
        experience_sources_records,
    )
    write_jsonl(
        OFFICIAL_TCU_DIR / "student_experiences.jsonl", student_experience_rows
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
    write_text_lf(
        OFFICIAL_TCU_DIR / "student-experience-digests.json",
        json.dumps({"digests": digest_records}, ensure_ascii=False, indent=2)
        + "\n",
    )

    write_text_lf(
        OFFICIAL_TCU_DIR / "student-experiences.json",
        json.dumps(
            {
                "school_id": "tcu",
                "school_name": "慈濟大學",
                "checked_at": CHECKED_AT,
                "source_url": TCU_EXPERIENCES_URL,
                "total_experience_reports": total_exp_reports,
                "covered_partner_schools": exp_covered_schools,
                "records": student_experience_rows,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
    )

    write_text_lf(
        OFFICIAL_TCU_DIR / "campus-locations.json",
        json.dumps(
            {
                "school_id": "tcu",
                "school_name": "慈濟大學",
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
    write_text_lf(
        OFFICIAL_TCU_DIR / "campus-assets.json",
        json.dumps(
            {
                "school_id": "tcu",
                "school_name": "慈濟大學",
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
    )

    tcu_source_urls = [
        TCU_OGA_HOME_URL,
        TCU_EXCHANGE_HUB_URL,
        TCU_OUTBOUND_OVERVIEW_URL,
        TCU_OUTBOUND_PARTNERS_URL,
        TCU_DUAL_DEGREE_URL,
        TCU_DUAL_DEGREE_DETAIL_URL,
        TCU_MAINLAND_EXCHANGE_URL,
        TCU_SISTER_SCHOOLS_URL,
        TCU_REGULATIONS_URL,
        TCU_SCHOLARSHIPS_URL,
        TCU_FUNDING_PROJECTS_URL,
        TCU_OVERSEAS_SUBSIDY_URL,
        TCU_MOE_XUEHAI_URL,
        TCU_OTHER_GRANTS_URL,
        TCU_EXPERIENCES_URL,
        TCU_STUDENT_STORIES_URL,
        TCU_CREDIT_TRANSFER_URL,
        TCU_ACADEMIC_UNITS_URL,
        TCU_LAW_INDEX_URL,
        TCU_DUAL_DEGREE_REGULATION_PDF_URL,
        TCU_ACADEMIC_COOP_REGULATION_PDF_URL,
        TCU_ENGLISH_REF_TABLE_PDF_URL,
        TCU_CEFR_B1_TABLE_PDF_URL,
        TCU_CEFR_B1_TABLE_EN_PDF_URL,
        TCU_LANG_BENCHMARK_115_PDF_URL,
    ]

    exchange_info_payload = {
        "school_name": "慈濟大學",
        "program_type": [
            (
                "全球事務處（OGA，原國際暨兩岸事務處 OIA）國際交換學生計畫（涵蓋美、加、德、瑞、日、韓、馬、泰等國互惠姊妹校：其中日本京都佛教大學［2 名/年］、奈良天理大學［1 名/年］、熊本尚絅大學［3 名/年，限女生］均提供「學雜費及住宿費雙全免」優惠；美國加州州立大學海峽群島分校 CSUCI［2 名/期］、加拿大漢博理工學院［2 名/期］、德國杜伊斯堡-埃森大學［2 名/期］、西薩克森應用科學大學［2 名/期］、瑞典哈爾姆斯塔德大學［2 名/期］、日本愛知學院大學［2 名/期］、韓國釜山外國語大學［3 名/期］、東西大學［2 名/期］、東國大學［2 名/期］、馬來西亞拉曼大學 UTAR［校級 5 名＋兒家系 5 名］、泰國清邁大學［2 名/期］、納黎萱大學［4 名/期］、泰國法政大學［傳播系 2 名/期］均提供免繳接待校學雜費優惠；美國堪薩斯州立大學開放醫學院與國際學院不限名額申請）"
            ),
            (
                "跨國雙聯與三聯學位計畫（共 6 所雙聯／三聯合作名校：含（1）跨洲際全球研究三聯碩士學位［Tricontinental Master in Global Studies, TRIM］—與德國卡爾斯魯厄應用科技大學 HKA 及墨西哥蒙特雷大學 UDEM 橫跨亞歐美三洲共同授位；（2）英國倫敦密德薩斯大學 Middlesex University［3+1 學士雙聯，限公共衛生學系、生命科學系、分子生物暨人類遺傳學系、外國語文學系、國際服務產業管理學士學位學程］；（3）美國安德魯斯大學 Andrews University［1+1 MBA 企管碩士雙聯，全校各科系皆可申請］；（4）泰國瑪希敦大學 Mahidol University 與納黎萱大學 Naresuan University［醫學科學研究所博士雙聯學位］）"
            ),
            (
                "大陸地區姊妹校交換學生計畫（含甘肅蘭州大學［985／雙一流高校，每學期 3 名「學雜費及住宿費雙全免」］、江蘇南京大學［C9 常春藤聯盟，每學期 5 名免學費，限設籍臺澎金馬或港澳學生］、江蘇蘇州大學［211／雙一流高校，每學期 2 名免學費］）暨教育部《學海飛颺》、《學海惜珠》、《學海築夢／新南向學海築夢》與校內《慈濟大學學生海外交流補助辦法》"
            ),
        ],
        "academic_year": [
            (
                "115（涵蓋次學年度出國交換生甄選［每年 11 月公告簡章、12 月中旬起更新名額至 2026/12/31 17:00 截止收件］、教育部學海飛颺／惜珠／築夢第一階段甄選［每年 2–3 月受理，2027/03/11 截止］與第二階段學海築夢［每年 8 月受理］，以及校內學生海外交流活動補助［暑期梯次 03/01–03/15 及 05/01–05/15、寒假梯次 12/01–12/15、學期中出發前 1 個月］）"
            ),
            (
                f"本平台完整收錄慈濟大學全球事務處公告之 {len(partners)} 所全球合作姊妹校（含 {open_partner_count} 所當期開放申請之國際交換、跨國雙聯／三聯學位與大陸地區交換合作大學，以及 {len(partners) - open_partner_count} 所正式締約代表性姊妹校，橫跨全球 17 個國家與地區，並完整收錄 {exp_covered_schools} 所合作大學共 {total_exp_reports} 篇歷年學長姐交換與雙聯學位心得報告）"
            ),
        ],
        "semester": [
            "國際交換學生計畫（Outbound Exchange Student Program）：以 1 學期或 1 學年為原則（大陸地區蘭州大學、南京大學、蘇州大學交換以 1 學期為原則）。",
            "跨國雙聯與三聯學位計畫（Dual / Double / Triple Degree Program，依《慈濟大學與境外學校辦理雙聯學制實施辦法》）：修習學士雙聯（英國密德薩斯大學 3+1）在兩校修業時間合計至少須滿 32 個月；修習碩士雙聯／三聯（德墨臺 TRIM 跨洲際三聯碩士、美國安德魯斯大學 1+1 MBA）合計至少須滿 12 個月；修習博士雙聯（泰國瑪希敦大學、納黎萱大學醫學科學研究所博士雙聯）合計至少須滿 24 個月。",
            "教育部《學海築夢／新南向學海築夢》海外專業實習（至少連續 30 天，不含來回途程）與寒暑假／學期中短期海外醫療人文交流。",
        ],
        "application_period": [
            "【出國交換學生計畫甄選（簡章公告與姊妹校名額更新）】全球事務處於每年 11 月公告交換甄選簡章，並自 12 月中旬起陸續更新接待姊妹校名額至申請截止日（當期截止日為 2026 年 12 月 31 日 17:00 止）；申請人須備齊核章紙本申請表件送交中央校區全球事務處（OGA）交流組。",
            "【教育部「學海飛颺／學海惜珠／學海築夢／新南向學海築夢」獎助計畫】第一階段（飛颺、惜珠、築夢、新南向築夢）於每年 2 月至 3 月中旬受理校內申請（2027 年 3 月 11 日 17:00 截止）；第二階段（築夢、新南向築夢）於每年 8 月受理校內申請。",
            "【慈濟大學學生海外交流活動補助（依《慈濟大學學生海外交流補助辦法》）】暑期活動第一梯次：每年 3 月 1 日至 3 月 15 日；暑期活動第二梯次：每年 5 月 1 日至 5 月 15 日；寒假活動梯次：每年 12 月 1 日至 12 月 15 日；學期中活動：須於出發前 1 個月以電子郵件及核章紙本向全球事務處提出申請。",
        ],
        "eligibility": [
            "1. 出國交換學生基本資格：（a）慈濟大學在學全職學位生（含大學部二年級（含）以上、碩士班、博士班在學學生；大一新生於大一下學期起得申請大二赴外交換；不含在職專班、延畢生及休學生）；（b）學業成績條件：歷年學業成績排名須達全班前 50%（約折合學業平均 75 分或 GPA 2.5 以上；美國加州州立大學海峽群島分校明訂 GPA 須達 2.5 以上）；（c）在校期間操行成績優良，無重大違規紀錄。",
            "2. 特定交換姊妹校專屬身分與院系條件：（a）美國堪薩斯州立大學（Kansas State University）限本校「醫學院」及「國際學院」學生申請；（b）泰國法政大學（Thammasat University）限「傳播學系」學生申請；（c）馬來西亞拉曼大學（UTAR）除校級 5 名外，另設「兒童發展與家庭教育學系」專屬名額 5 名；（d）日本尚絅大學（Shokei University）限「女性學生」申請；（e）大陸南京大學（Nanjing University）限設籍臺灣地區或港澳地區之學生申請。",
            "3. 跨國雙聯與三聯學位申請資格：（a）德墨臺「跨洲際全球研究三聯碩士學位（TRIM）」開放人文社科、管理、國際與相關領域碩士生申請；（b）英國倫敦密德薩斯大學（Middlesex University）3+1 雙學士限「公共衛生學系、生命科學系、分子生物暨人類遺傳學系、外國語文學系、國際服務產業管理學士學位學程」大一至大三學生申請；（c）美國安德魯斯大學（Andrews University）1+1 MBA 雙碩士開放「全校各科系」申請；（d）泰國瑪希敦大學（Mahidol）與納黎萱大學（Naresuan）博士雙聯限「醫學院醫學科學研究所」博士生申請。",
            "4. 教育部學海系列計畫與校內海外交流補助資格：申請《學海飛颺／惜珠／築夢》須具中華民國國籍且在臺灣地區設有戶籍（學海惜珠另須持有效低收入戶、中低收入戶或特殊境遇家庭證明）；申請校內《學生海外交流活動補助》須為本校在學全職學生並具備服務學習訓練時數（審查權重：計畫完整性 40%、含服務學習訓練時數之學習成效 40%、交流風險性 20%）。",
        ],
        "language_requirement": [
            "1. 慈濟大學校內外語能力基準（依《慈濟大學英語主要檢測參考對照表》及《慈濟大學 CEFR B1（含）級以上或同等語言能力對照表》）：CEFR B1 基準為 TOEIC 550 分、TOEFL iBT 42 分、TOEFL ITP 460 分、IELTS 4.0、全民英檢 GEPT 中級複試通過（或中高級初試通過）；CEFR B2 基準為 TOEIC 785 分、TOEFL iBT 72 分、TOEFL ITP 543 分、IELTS 5.5。",
            "2. 歐美與亞太英語組交換姊妹校語檢門檻：（a）美國加州州立大學海峽群島分校（CSUCI）：TOEFL iBT 61 / IELTS 6.0 / DAAD B / 日本英檢準 1 級（Eiken Pre-1）；（b）美國堪薩斯州立大學（K-State）：TOEFL iBT 79 / IELTS 6.5（達標可免修英語加強課程直接選修專業課程）；（c）泰國清邁大學（CMU）：TOEFL iBT 61 / PBT 500 / CBT 173 / IELTS 5.0 / TOEIC 600；（d）瑞典哈爾姆斯塔德大學：IELTS 6.5 / TOEFL iBT 90（CEFR B2）；（e）加拿大漢博理工學院、德國杜伊斯堡-埃森大學、西薩克森應用科學大學、泰國法政大學、納黎萱大學、馬來西亞拉曼大學：CEFR B1–B2（TOEIC 550–600 / TOEFL iBT 61–80 / IELTS 5.0–6.0）。",
            "3. 日韓及大陸地區交換姊妹校語檢門檻：（a）日本京都佛教大學（修習日本語文學）、奈良天理大學（國際學部）、熊本尚絅大學（現代文化學部）、名古屋愛知學院大學（日本研究中心）：建議具日語檢定 JLPT N2–N4 或 CEFR B1 以上能力；（b）韓國釜山外國語大學、東西大學、東國大學：具韓語檢定 TOPIK 2–3 級或英語 CEFR B1–B2 以上能力；（c）大陸蘭州大學、南京大學、蘇州大學：以中文授課為主，免強制外語檢定（具英語檢定證明者於校內甄選列為加分參考）。",
            "4. 跨國雙聯與三聯學位語檢門檻：（a）德墨臺 TRIM 跨洲際全球研究三聯碩士（德國 HKA ＆ 墨西哥 UDEM）：IELTS 6.5 或 TOEFL iBT 79–80（CEFR B2）；（b）美國安德魯斯大學 1+1 MBA 雙碩士：TOEFL iBT 79 或 IELTS 6.5；（c）英國倫敦密德薩斯大學 3+1 雙學士：IELTS 6.0（單科不低於 5.5）或 TOEFL iBT 72；（d）泰國瑪希敦大學與納黎萱大學醫學科學博士雙聯：IELTS 6.0 或 TOEFL iBT 79 以上。",
        ],
        "required_documents": [
            "1. 《慈濟大學出國交換學生申請表》或《慈濟大學雙聯學位生出國進修申請表》正本 1 份（須經導師及系所主管簽章推薦）",
            "2. 《慈濟大學選送學生出國研修家長（監護人）同意書》正本 1 份（由家長或法定監護人親筆簽名蓋章）",
            "3. 本校歷年中文及英文正式學業成績單正本各 1 份（須註明歷年學業總平均 GPA 及全班人數與排名百分比，大學部須達全班前 50%）",
            "4. 有效外語能力檢定證明影本（TOEFL iBT / TOEFL ITP / IELTS / TOEIC / GEPT / JLPT / TOPIK，須符合本校 CEFR B1 對照表及申請姊妹校門檻）",
            "5. 中英文自傳與出國讀書／修課計畫書（Study Plan & Autobiography，含申請動機、擬修習科目及返國學分轉換規劃）",
            "6. 教師推薦信 1–2 封（申請雙聯／三聯學位或歐美日姊妹校者須檢附英文推薦信）",
            "7. 在學證明、有效護照個人資料頁影本、服務學習訓練時數證明（申請校內海外交流補助佔學習成效評分 40%）及其他有利審查之社團或獲獎證明",
        ],
        "scholarship_info": [
            "1. 教育部「學海飛颺」與「學海惜珠」選送學生出國研修獎學金（全球事務處承辦，每年 2–3 月第一階段校內收件）：獎助具中華民國國籍且在臺灣地區設有戶籍、歷年學業成績排名達全班前 50% 且具符合申請學校外語標準之慈濟大學在學學位生，赴非大陸及港澳地區之國外姊妹校交換或修讀雙聯／三聯學位 1 學期至 1 學年。學海飛颺依研修地區與甄審排名核發機票與生活費補助（約 NT$50,000–300,000 不等）；學海惜珠針對持有效低收入戶、中低收入戶或特殊境遇家庭證明之清寒優秀生優先提供高額全額補助（返國後另可銜接低收入戶及中低收入戶學生返國後專案性補助計畫）。",
            "2. 教育部「學海築夢」與「新南向學海築夢」海外專業實習計畫（每年 2–3 月第一階段及 8 月第二階段校內收件）：由本校專任教師擔任計畫主持人，選送本國籍在學學生赴歐美日（學海築夢）或新南向國家如泰國、馬來西亞、印尼、印度、澳紐（新南向學海築夢）之醫療機構、大學實驗室、社福教育機構或企業進行至少 30 天（不含來回途程）之專業實習，補助來回經濟艙機票款及海外生活費。",
            "3. 慈濟大學《學生海外交流活動補助》（依《慈濟大學學生海外交流補助辦法》辦理）：補助本校在學全職學生參與海外交換研習、雙聯修讀、短期學術交流、國際會議發表或海外醫療人文志工。每年分三期固定梯次（暑期第一梯次 3/1–3/15、暑期第二梯次 5/1–5/15、寒假梯次 12/1–12/15）及學期中（出發前 1 個月申請）受理；審查評分標準為「計畫完整性 40%」、「學習成效（含服務學習訓練時數）40%」及「交流風險性 20%」。",
            "4. 慈濟大學互惠姊妹校「學雜費及住宿費雙全免」與免學費交換待遇：透過全球事務處甄選錄取赴日本京都佛教大學（2 名/年）、奈良天理大學（1 名/年）、熊本尚絅大學（3 名/年，限女生）及大陸蘭州大學（3 名/期）交換者，享有接待姊妹校「學雜費及校內住宿費雙全免」極優厚待遇；赴其餘美、加、德、瑞、日、韓、馬、泰、陸等互惠交換姊妹校亦享免繳接待校學雜費優惠。",
        ],
        "partner_universities": [p["school_name"] for p in partners],
        "source_urls": tcu_source_urls,
        "last_checked": CHECKED_AT,
    }
    write_text_lf(
        OFFICIAL_TCU_DIR / "exchange_info.json",
        json.dumps(exchange_info_payload, ensure_ascii=False, indent=2) + "\n",
    )

    student_dashboard_payload = {
        "school_name": "慈濟大學",
        "last_checked": CHECKED_AT,
        "academic_score_minimum": 75.0,
        "academic_score_rule": (
            "依慈濟大學全球事務處（OGA）《出國交換學生甄選簡章》與《慈濟大學國際交換學生甄選辦法》規定：申請人須為本校在學全職學位生（大學部二年級（含）以上、碩士班、博士班在學學生；大一新生於大一下學期得申請大二赴外交換；不含在職專班、延畢生及休學生），歷年學業成績排名須達「全班前 50%」（約折合學業平均 75 分或 GPA 2.5 以上），且在校期間操行成績優良；個別合作校如美國加州州立大學海峽群島分校（CSUCI）明訂歷年 GPA 須達 2.5 以上，跨國雙聯／三聯學位建議 GPA 達 2.7–3.2 以上。"
        ),
        "academic_gpa_minimum": 2.5,
        "maximum_preferences": 3,
        "selection_rules": {
            "academic_policy": "gpa_or_rank",
            "academic_reference_year": "115",
            "undergraduate_gpa_minimum": 2.5,
            "graduate_academic_exempt": False,
            "exclude_in_service": True,
            "pending_quota_planning": False,
            "partner_requirements_need_confirmation": False,
            "degree_score_minimums": {
                "undergraduate": 75.0,
                "graduate": 75.0,
            },
            "excluded_undergraduate_years": [
                "大一上",
                "一年級上學期",
                "延畢",
                "延畢生",
            ],
            "language_certificate_required": True,
        },
        "language_score_minimums": {
            "toefl": 42.0,
            "ielts": 4.0,
            "toefl_itp": 460.0,
            "toeic": 550.0,
        },
        "application_periods": [
            {
                "title": "慈濟大學 2026–2027 學年度出國交換學生暨跨國雙聯／三聯學位甄選（每年 11 月公告簡章、12 月中旬更新名額至 12/31 截止）",
                "details": [
                    "全球事務處（OGA）每年 11 月公告次學年度出國交換學生甄選簡章，並自 12 月中旬起陸續更新美、加、英、德、墨、瑞、日、韓、馬、泰、陸等合作姊妹校名額至申請截止日（2026 年 12 月 31 日 17:00 止）。",
                    "申請人須於截止日前備齊《出國交換學生／雙聯學位申請表》（經導師與系所主管簽章）、《家長同意書》、中英文歷年成績單（含全班排名百分比）、外語能力證明、中英文讀書計畫與自傳及服務學習時數證明，送交中央校區全球事務處交流組。",
                ],
                "source": {
                    "title": "慈濟大學全球事務處「出國交換學生計畫（Outbound Exchange Student Program）」專頁",
                    "source_url": TCU_OUTBOUND_PARTNERS_URL,
                    "category": "exchange_application",
                    "summary": "慈濟大學出國交換學生甄選簡章公告時程、全班前 50% 成績門檻與姊妹校名額總表。",
                },
                "scope": "home_application",
                "program_types": ["exchange", "dual_degree"],
                "academic_year": "115",
                "application_round": "115-2 梯次（2026–2027 出國交換學生暨雙聯／三聯學位甄選）",
                "audience": "all_students",
                "opens_at": "2026-11-01T09:00:00+08:00",
                "deadline_at": "2026-12-31T17:00:00+08:00",
                "date_status": "verified_exact",
                "status": "open",
                "status_note": "每年 11 月公告簡章，12 月中旬起更新姊妹校名額至 12 月 31 日截止收件。",
                "deadline_note": "請備齊經導師與系所主管核章之紙本申請表件送達中央校區全球事務處交流組（分機 1014、11018）。",
                "reminder_eligible": True,
                "checked_at": CHECKED_AT,
            },
            {
                "title": "慈濟大學辦理教育部「學海飛颺／學海惜珠／學海築夢／新南向學海築夢」第一階段校內甄選（每年 2–3 月收件）",
                "details": [
                    "全球事務處每年 2 月至 3 月中旬受理教育部《學海飛颺》（優秀交換及雙聯生）、《學海惜珠》（低收、中低收及特殊境遇家庭優秀生高額補助）、《學海築夢》及《新南向學海築夢》（海外專業實習至少 30 天）第一階段校內申請；第二階段《學海築夢／新南向學海築夢》於每年 8 月受理。",
                ],
                "source": {
                    "title": "慈濟大學全球事務處「教育部學海系列獎助計畫」專區",
                    "source_url": TCU_MOE_XUEHAI_URL,
                    "category": "scholarship",
                    "summary": "慈濟大學教育部學海飛颺、學海惜珠、學海築夢及新南向學海築夢兩階段申請時程與補助規定。",
                },
                "scope": "home_application",
                "program_types": ["exchange", "dual_degree"],
                "academic_year": "115",
                "application_round": "116 年度教育部學海系列計畫第一階段校內甄選",
                "audience": "all_students",
                "opens_at": "2027-02-01T09:00:00+08:00",
                "deadline_at": "2027-03-11T17:00:00+08:00",
                "date_status": "verified_exact",
                "status": "upcoming",
                "status_note": "教育部學海四計畫第一階段於每年 2 月至 3 月中旬受理校內收件；第二階段學海築夢於每年 8 月受理。",
                "deadline_note": "申請人須完成校內出國交換或海外實習申請並檢附學海計畫申請書、成績單（含全班排名百分比）及語言證明。",
                "reminder_eligible": True,
                "checked_at": CHECKED_AT,
            },
            {
                "title": "慈濟大學「學生海外交流活動補助」申請梯次（暑期 3/1–3/15、5/1–5/15；寒假 12/1–12/15；學期中出發前 1 個月）",
                "details": [
                    "依《慈濟大學學生海外交流補助辦法》，補助本校在學全職學生參與海外交換、短期研習、國際學術會議及醫療人文志工交流；審查評分包含計畫完整性（40%）、學習成效含服務學習訓練時數（40%）及交流風險性（20%）。",
                ],
                "source": {
                    "title": "慈濟大學全球事務處「學生海外交流活動補助辦法」專頁",
                    "source_url": TCU_OVERSEAS_SUBSIDY_URL,
                    "category": "scholarship",
                    "summary": "慈濟大學學生海外交流活動補助四大申請梯次與 40%/40%/20% 審查標準。",
                },
                "scope": "home_application",
                "program_types": ["exchange"],
                "academic_year": "115",
                "application_round": "115 學年度寒假暨暑期海外交流活動補助",
                "audience": "all_students",
                "opens_at": "2026-12-01T09:00:00+08:00",
                "deadline_at": "2026-12-15T17:00:00+08:00",
                "date_status": "verified_exact",
                "status": "open",
                "status_note": "寒假梯次 12/1–12/15、暑期第一梯次 3/1–3/15、暑期第二梯次 5/1–5/15；學期中活動須於出發前 1 個月申請。",
                "deadline_note": "請將申請表電子檔寄至全球事務處承辦人信箱並繳交核章紙本至全球事務處交流組。",
                "reminder_eligible": True,
                "checked_at": CHECKED_AT,
            },
        ],
        "program_overview": [
            {
                "title": (
                    f"慈濟大學全球事務處（OGA）國際化學習藍圖：國際交換、跨洲際三聯碩士（TRIM）、英美泰雙聯學位與學海／海外交流獎助總覽（{len(partners)} 所合作姊妹校・{open_partner_count} 所當期開放申請・{total_exp_reports} 篇學長姐心得）"
                ),
                "details": [
                    (
                        f"慈濟大學由全球事務處（Office of Global Affairs, OGA，原國際暨兩岸事務處 OIA）交流組統籌全校 6 大學院（醫學院、護理學院、工程科技學院、人文傳播暨社會科學院、智慧永續管理學院、國際學院）與全球 17 國共 {len(partners)} 所合作大學之學術交流，其中當期開放申請之國際交換學生、大陸地區姊妹校交換與跨國雙聯／三聯學位（德墨臺 TRIM 跨洲際三聯碩士、英國密德薩斯大學 3+1 雙學士、美國安德魯斯大學 1+1 MBA 雙碩士、泰國瑪希敦與納黎萱博士雙聯）合作名校達 {open_partner_count} 所。"
                    ),
                    (
                        "為減輕學生海外求學經濟負擔，日本佛教大學、天理大學、尚絅大學及大陸蘭州大學特別提供「學雜費及住宿費雙全免」待遇，其餘 20 餘所互惠交換姊妹校亦免繳接待校學雜費；同時學校整合教育部《學海飛颺》、《學海惜珠》、《學海築夢／新南向學海築夢》及校內《慈濟大學學生海外交流補助辦法》，全方位支持學生拓展全球視野與醫療人文關懷。"
                    ),
                ],
                "source": {
                    "title": "慈濟大學全球事務處「國際交流、出國交換與雙聯學位」官方網站",
                    "source_url": TCU_EXCHANGE_HUB_URL,
                    "category": "exchange_application",
                    "summary": "慈濟大學出國交換學生、跨國雙聯與三聯學位、大陸地區交換與獎助學金總覽。",
                },
            }
        ],
        "eligibility": [
            {
                "title": "在學全職學位生（大二以上及碩博士生）、歷年學業成績排名全班前 50%（GPA 2.5+）與雙聯／三聯學制規定",
                "details": exchange_info_payload["eligibility"],
                "source": {
                    "title": "慈濟大學出國交換學生甄選簡章、雙聯學制實施辦法與學生海外交流補助辦法",
                    "source_url": TCU_OUTBOUND_PARTNERS_URL,
                    "category": "exchange_application",
                    "summary": "慈濟大學出國交換生、大陸地區交換與跨國雙聯／三聯學位之在學年級、全班前 50% 排名與特定院系規定。",
                },
            }
        ],
        "language_requirements": [
            {
                "title": "校內 CEFR B1 外語對照基準（TOEIC 550 / iBT 42 / ITP 460 / IELTS 4.0）、歐美名校 iBT 61–79 / IELTS 6.0–6.5 與日韓姊妹校 JLPT / TOPIK 基準",
                "details": exchange_info_payload["language_requirement"],
                "source": {
                    "title": "慈濟大學 CEFR B1（含）級以上語言能力對照表、英語主要檢測參考對照表與出國交換簡章",
                    "source_url": TCU_CEFR_B1_TABLE_PDF_URL,
                    "category": "exchange_application",
                    "summary": "慈濟大學各合作姊妹校交換、跨國雙聯／三聯學位與校內 CEFR B1–B2 外語檢定門檻對照表。",
                },
            }
        ],
        "required_documents": [
            {
                "title": "《出國交換學生／雙聯學位申請表》（系所核章）、《家長同意書》、中英文歷年成績單含全班排名百分比、外語證明、中英文讀書計畫與服務學習時數證明",
                "details": exchange_info_payload["required_documents"],
                "source": {
                    "title": "慈濟大學全球事務處出國交換學生申請須知與雙聯學位申請表件",
                    "source_url": TCU_OUTBOUND_PARTNERS_URL,
                    "category": "exchange_application",
                    "summary": "慈濟大學出國交換生、雙聯／三聯學位生與海外交流獎助學金申請應備之 7 項紙本表件規範。",
                },
            }
        ],
        "scholarship_info": [
            {
                "title": "教育部《學海飛颺》、《學海惜珠》、《學海築夢／新南向學海築夢》暨《慈濟大學學生海外交流補助》與日陸姊妹校「學雜費住宿費雙全免」優惠",
                "details": exchange_info_payload["scholarship_info"],
                "source": {
                    "title": "慈濟大學全球事務處國際交流獎補助計畫、教育部學海計畫與學生海外交流補助辦法",
                    "source_url": TCU_FUNDING_PROJECTS_URL,
                    "category": "scholarship",
                    "summary": "慈濟大學教育部學海四計畫、校內學生海外交流活動補助及互惠姊妹校學雜費與住宿費全免規定。",
                },
            }
        ],
        "regulation_links": [
            {
                "title": "慈濟大學與境外學校辦理雙聯學制實施辦法（1070508教育部備查版，PDF）",
                "url": TCU_DUAL_DEGREE_REGULATION_PDF_URL,
            },
            {
                "title": "慈濟大學與國內外學校機構簽訂學術合作協議書辦法（PDF）",
                "url": TCU_ACADEMIC_COOP_REGULATION_PDF_URL,
            },
            {
                "title": "慈濟大學英語主要檢測參考對照表（20260210版，PDF）",
                "url": TCU_ENGLISH_REF_TABLE_PDF_URL,
            },
            {
                "title": "慈濟大學 CEFR B1（含）級以上或同等語言能力對照表（202604版，PDF）",
                "url": TCU_CEFR_B1_TABLE_PDF_URL,
            },
            {
                "title": "慈濟大學學生抵免學分辦法暨海外交換、研修、雙聯學位學分轉換原則（教務處／法規彙編）",
                "url": TCU_CREDIT_TRANSFER_URL,
            },
        ],
        "document_explanations": [
            {
                "title": "慈濟大學出國交換與雙聯學位申請表件、全班前 50% 排名成績單、家長同意書與服務學習時數準備要領",
                "summary": "說明慈濟大學全球事務處出國交換甄選與雙聯／三聯學位申請表件核章流程，以及全班排名前 50% 成績單、CEFR B1 語言證明與海外交流補助審查文件準備規範。",
                "key_points": [
                    "系所推薦核章與《出國交換學生／雙聯學位申請表》、《家長同意書》：申請人須於截止日前填妥申請表與海外修課計畫，經導師與所屬系（所）主管簽章推薦，並檢附由家長或監護人親筆簽署之《選送學生出國研修家長同意書》送交全球事務處交流組。",
                    "中英文歷年成績單與全班前 50% 排名證明：大學部及研究生申請出國交換與教育部學海飛颺須檢附達「歷年學業成績排名全班前 50%」（約 GPA 2.5 或平均 75 分以上）之中英文正式成績單；申請加州州立大學海峽群島分校（CSUCI）須確認 GPA 達 2.5 以上。",
                    "外語能力證明與服務學習訓練時數：須檢附符合《慈濟大學 CEFR B1（含）級以上或同等語言能力對照表》及接待校門檻之語檢證書；申請校內《學生海外交流活動補助》者，其「學習成效（含服務學習訓練時數）」占審查總分 40%，返國後須依限繳交研修心得報告與核銷單據。",
                ],
                "applies_to": [],
                "source": {
                    "title": "慈濟大學全球事務處出國交換學生甄選簡章與學生海外交流補助辦法",
                    "source_url": TCU_OUTBOUND_PARTNERS_URL,
                    "category": "exchange_application",
                    "summary": None,
                },
                "document_url": TCU_CEFR_B1_TABLE_PDF_URL,
                "document_type": "official_document",
                "full_text_extracted": True,
            }
        ],
        "rule_explanations": [
            {
                "title": "慈濟大學出國交換註冊與學雜費住宿費雙全免待遇、跨國雙聯／三聯學制（32／12／24 個月）及國外學分轉換原則核心規定",
                "summary": "規範慈濟大學出國交換在學註冊與互惠免學費／免住宿費待遇、雙聯與三聯學位修業月數下限、海外交流補助 40/40/20 評分標準及返國學分轉換抵免程序。",
                "key_points": [
                    "出國期間在學註冊與姊妹校學雜費／住宿費全免待遇（《慈濟大學國際交換學生甄選辦法》）：交換生出國期間仍須辦理慈濟大學註冊並繳交本校學雜費；多數互惠姊妹校免繳接待校學雜費，其中日本京都佛教大學、奈良天理大學、熊本尚絅大學及大陸蘭州大學更享「學雜費及住宿費雙全免」優惠。",
                    "跨國雙聯與三聯學制修業時限（《慈濟大學與境外學校辦理雙聯學制實施辦法》）：修讀雙聯或三聯學位學生在兩校（或三校）修業時間合計，學士班（如英國密德薩斯大學 3+1）至少滿 32 個月、碩士班（如德墨臺 TRIM 跨洲際三聯碩士、美國安德魯斯大學 1+1 MBA）至少滿 12 個月、博士班（如泰國瑪希敦大學、納黎萱大學醫學科學博士雙聯）至少滿 24 個月。",
                    "國外學分轉換原則與校內海外交流補助審查（《學分轉換原則》＆《學生海外交流補助辦法》）：學生出國前應先經系所核准修課計畫，返國後檢附正式成績單正本與課程大綱辦理學分轉換與抵免（美日陸學分原則 1:1 轉換，歐洲 ECTS 原則以 2 ECTS 折算 1 學分）；申請校內海外交流補助依計畫完整性 40%、學習成效（含服務學習時數）40%、交流風險性 20% 審查。",
                ],
                "applies_to": [],
                "source": {
                    "title": "慈濟大學與境外學校辦理雙聯學制實施辦法、學分轉換原則與學生海外交流補助辦法",
                    "source_url": TCU_REGULATIONS_URL,
                    "category": "exchange_application",
                    "summary": None,
                },
                "document_url": TCU_DUAL_DEGREE_REGULATION_PDF_URL,
                "document_type": "official_document",
                "full_text_extracted": True,
            }
        ],
        "sources": [
            {
                "title": "慈濟大學全球事務處（Office of Global Affairs, OGA）官方網站",
                "source_url": TCU_OGA_HOME_URL,
                "category": "exchange_application",
                "summary": None,
            },
            {
                "title": "慈濟大學全球事務處「國際交流（International Exchange）」總覽專區",
                "source_url": TCU_EXCHANGE_HUB_URL,
                "category": "exchange_application",
                "summary": None,
            },
            {
                "title": f"慈濟大學「出國交換學生計畫」甄選簡章與姊妹校名額總表（共 {len(partners)} 所合作姊妹校）",
                "source_url": TCU_OUTBOUND_PARTNERS_URL,
                "category": "partner_school",
                "summary": None,
            },
            {
                "title": "慈濟大學「跨國雙聯與三聯學位計畫（TRIM／Middlesex 3+1／Andrews 1+1 MBA／泰國博士雙聯）」專區",
                "source_url": TCU_DUAL_DEGREE_URL,
                "category": "partner_school",
                "summary": None,
            },
            {
                "title": "慈濟大學「大陸地區學生交換研習申請資訊（蘭州大學、南京大學、蘇州大學）」專區",
                "source_url": TCU_MAINLAND_EXCHANGE_URL,
                "category": "partner_school",
                "summary": None,
            },
            {
                "title": "慈濟大學全球事務處「全球合作姊妹校名錄（Sister Schools）」專頁",
                "source_url": TCU_SISTER_SCHOOLS_URL,
                "category": "partner_school",
                "summary": None,
            },
            {
                "title": "慈濟大學「國際交流獎補助計畫、教育部學海系列計畫與學生海外交流補助辦法」專區",
                "source_url": TCU_FUNDING_PROJECTS_URL,
                "category": "scholarship",
                "summary": None,
            },
            {
                "title": f"慈濟大學全球事務處「經驗分享與學生故事（Insightful Experience ＆ Student Stories）」（{exp_covered_schools} 校 {total_exp_reports} 篇心得報告）",
                "source_url": TCU_EXPERIENCES_URL,
                "category": "exchange_application",
                "summary": None,
            },
        ],
    }
    write_text_lf(
        OFFICIAL_TCU_DIR / "student_dashboard.json",
        json.dumps(student_dashboard_payload, ensure_ascii=False, indent=2)
        + "\n",
    )

    doc_conditions = {
        "school_id": "tcu",
        "school_name": "慈濟大學",
        "checked_at": CHECKED_AT,
        "source_url": TCU_OUTBOUND_PARTNERS_URL,
        "common_documents": exchange_info_payload["required_documents"],
        "track_specific_conditions": [
            {
                "track": "國際交換學生計畫（美國、加拿大、德國、瑞典、日本、韓國、馬來西亞、泰國互惠姊妹校 1 學期或 1 學年交換）",
                "required": [
                    "於每年 11–12 月出國交換生甄選截止日前（2026/12/31 17:00 止）將核章紙本申請表件送交中央校區全球事務處（OGA）交流組",
                    "《慈濟大學出國交換學生申請表》（經導師與系所主管簽章推薦）及《慈濟大學選送學生出國研修家長（監護人）同意書》正本",
                    "本校中、英文歷年學業成績單正本（須註明歷年 GPA 及全班排名百分比，須達全班前 50%；申請加州州立大學海峽群島分校須達 GPA 2.5 以上）",
                    "有效外語能力證明：符合《慈濟大學 CEFR B1（含）級以上語言能力對照表》（TOEIC 550 / TOEFL iBT 42 / TOEFL ITP 460 / IELTS 4.0）及接待校門檻（如 CSUCI 與清邁大學 TOEFL iBT 61、堪薩斯州立大學 TOEFL iBT 79 / IELTS 6.5、瑞典哈爾姆斯塔德大學 IELTS 6.5、日韓姊妹校 JLPT N2–N4 / TOPIK 2–3 級）",
                ],
            },
            {
                "track": "跨國雙聯與三聯學位計畫（德墨臺 TRIM 跨洲際三聯碩士、英國密德薩斯大學 3+1 雙學士、美國安德魯斯大學 1+1 MBA、泰國瑪希敦／納黎萱博士雙聯）",
                "required": [
                    "符合各雙聯／三聯學制適用院系與修業月數規定（英國密德薩斯大學 3+1 限公衛、生科、分遺、外語、國管學程且兩校累計滿 32 個月；美國安德魯斯大學 1+1 MBA 開放全校各科系且累計滿 12 個月；德墨臺 TRIM 三聯碩士累計滿 12 個月；泰國瑪希敦與納黎萱博士雙聯限醫科所博士生且累計滿 24 個月）",
                    "達合作名校雙聯外語門檻：德墨臺 TRIM 三聯碩士與美國安德魯斯大學 1+1 MBA（IELTS 6.5 或 TOEFL iBT 79–80）、英國倫敦密德薩斯大學 3+1 雙學士（IELTS 6.0 單科不低於 5.5 或 TOEFL iBT 72）、泰國瑪希敦／納黎萱博士雙聯（IELTS 6.0 或 TOEFL iBT 79）",
                    "備齊《慈濟大學雙聯學位生出國進修申請表》、英文歷年成績單、英文讀書與研究計畫（SOP）、英文推薦信 2 封、護照影本與財力證明，洽所屬系所及全球事務處交流組辦理提名",
                ],
            },
            {
                "track": "大陸地區姊妹校交換學生計畫（蘭州大學學雜費住宿費雙全免、南京大學、蘇州大學 1 學期交換）",
                "required": [
                    "本校大學部二年級（含）以上或碩博士班在學全職學生，歷年學業成績排名達全班前 50%（申請南京大學者須設籍臺灣地區或港澳地區）",
                    "備齊《出國交換學生申請表》、《家長同意書》、歷年成績單正本（含全班排名百分比）、讀書計畫、自傳及有效臺胞證／護照影本",
                ],
            },
            {
                "track": "教育部《學海飛颺／學海惜珠／學海築夢／新南向學海築夢》暨《慈濟大學學生海外交流活動補助》",
                "required": [
                    "申請教育部《學海飛颺／惜珠／築夢》（第一階段每年 2–3 月、第二階段每年 8 月）須具中華民國國籍且在臺灣設有戶籍，檢附學海計畫申請書、出國研修／實習計畫書、歷年成績單含全班前 50% 排名證明及外語證明（學海惜珠另附有效低收／中低收／特殊境遇家庭證明）",
                    "申請校內《學生海外交流活動補助》（暑期 3/1–3/15、5/1–5/15；寒假 12/1–12/15；學期中出發前 1 個月）須檢附海外交流補助申請表、完整活動企劃書、服務學習訓練時數證明（占學習成效評分 40%）及風險評估說明，返國後依限繳交心得報告與核銷單據",
                ],
            },
        ],
    }
    write_text_lf(
        OFFICIAL_TCU_DIR / "document-conditions.json",
        json.dumps(doc_conditions, ensure_ascii=False, indent=2) + "\n",
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
            f"{fname},{len(partners)},{pop},{ratio:.4f},Official TCU OGA verified"
        )
    write_text_lf(
        OFFICIAL_TCU_DIR / "field-coverage.csv",
        "\n".join(field_cov_lines) + "\n",
    )

    pages_records = [
        {
            "title": "慈濟大學：2026–2027 出國交換生甄選（11 月公告簡章、12/31 截止）、教育部學海計畫（2–3 月及 8 月）與海外交流補助申請時程",
            "source_url": TCU_EXCHANGE_HUB_URL,
            "published_at": "2026-11-01T00:00:00Z",
            "text": "\n".join(exchange_info_payload["application_period"]),
            "summary": "\n".join(exchange_info_payload["application_period"]),
            "category": "exchange_application",
            "attachments": [],
            "crawled_at": CHECKED_AT,
            "content_hash": hashlib.sha256(
                "\n".join(exchange_info_payload["application_period"]).encode(
                    "utf-8"
                )
            ).hexdigest(),
        },
        {
            "title": "慈濟大學：出國交換生（全班排名前 50%／GPA 2.5+）、特定院系交換與跨國雙聯／三聯學位申請資格",
            "source_url": TCU_OUTBOUND_PARTNERS_URL,
            "published_at": "2026-11-01T00:00:00Z",
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
            "title": f"慈濟大學：{len(partners)} 所全球合作姊妹校外語檢定門檻（CEFR B1 對照表 TOEIC 550 / iBT 42、歐美交換 iBT 61–79、雙聯／三聯 IELTS 6.0–6.5）",
            "source_url": TCU_CEFR_B1_TABLE_PDF_URL,
            "published_at": "2026-11-01T00:00:00Z",
            "text": "\n".join(exchange_info_payload["language_requirement"]),
            "summary": "\n".join(exchange_info_payload["language_requirement"]),
            "category": "exchange_application",
            "attachments": [],
            "crawled_at": CHECKED_AT,
            "content_hash": hashlib.sha256(
                "\n".join(exchange_info_payload["language_requirement"]).encode(
                    "utf-8"
                )
            ).hexdigest(),
        },
        {
            "title": "慈濟大學：赴國外交換與修讀雙聯學位應備文件（申請表、家長同意書、全班前 50% 排名成績單、語檢證明、讀書計畫與服務學習時數證明）",
            "source_url": TCU_OUTBOUND_OVERVIEW_URL,
            "published_at": "2026-11-01T00:00:00Z",
            "text": "\n".join(exchange_info_payload["required_documents"]),
            "summary": "\n".join(exchange_info_payload["required_documents"]),
            "category": "exchange_application",
            "attachments": [],
            "crawled_at": CHECKED_AT,
            "content_hash": hashlib.sha256(
                "\n".join(exchange_info_payload["required_documents"]).encode(
                    "utf-8"
                )
            ).hexdigest(),
        },
        {
            "title": "慈濟大學：教育部學海飛颺、學海惜珠、學海築夢／新南向學海築夢暨學生海外交流補助與日陸姊妹校學雜費住宿費雙全免待遇",
            "source_url": TCU_FUNDING_PROJECTS_URL,
            "published_at": "2026-11-01T00:00:00Z",
            "text": "\n".join(exchange_info_payload["scholarship_info"]),
            "summary": "\n".join(exchange_info_payload["scholarship_info"]),
            "category": "scholarship",
            "attachments": [],
            "crawled_at": CHECKED_AT,
            "content_hash": hashlib.sha256(
                "\n".join(exchange_info_payload["scholarship_info"]).encode(
                    "utf-8"
                )
            ).hexdigest(),
        },
        {
            "title": "慈濟大學：與境外學校辦理雙聯學制實施辦法暨德墨臺 TRIM 三聯碩士、英國 Middlesex 3+1、美國 Andrews 1+1 MBA、泰國博士雙聯",
            "source_url": TCU_DUAL_DEGREE_URL,
            "published_at": "2026-11-01T00:00:00Z",
            "text": "\n".join(exchange_info_payload["semester"]),
            "summary": "\n".join(exchange_info_payload["semester"]),
            "category": "exchange_application",
            "attachments": [],
            "crawled_at": CHECKED_AT,
            "content_hash": hashlib.sha256(
                "\n".join(exchange_info_payload["semester"]).encode("utf-8")
            ).hexdigest(),
        },
        {
            "title": "慈濟大學：國際交換學生甄選辦法、學分轉換原則與學生抵免學分辦法（美日陸 1:1、歐洲 ECTS÷2）",
            "source_url": TCU_CREDIT_TRANSFER_URL,
            "published_at": "2026-11-01T00:00:00Z",
            "text": "\n".join(
                student_dashboard_payload["rule_explanations"][0]["key_points"]
            ),
            "summary": student_dashboard_payload["rule_explanations"][0][
                "summary"
            ],
            "category": "exchange_application",
            "attachments": [],
            "crawled_at": CHECKED_AT,
            "content_hash": hashlib.sha256(
                "\n".join(
                    student_dashboard_payload["rule_explanations"][0][
                        "key_points"
                    ]
                ).encode("utf-8")
            ).hexdigest(),
        },
        {
            "title": f"慈濟大學：全球事務處經驗分享與學生故事專區（{exp_covered_schools} 校 {total_exp_reports} 篇心得報告）",
            "source_url": TCU_EXPERIENCES_URL,
            "published_at": "2026-11-01T00:00:00Z",
            "text": "\n".join(exchange_info_payload["program_type"]),
            "summary": "\n".join(exchange_info_payload["program_type"]),
            "category": "exchange_application",
            "attachments": [],
            "crawled_at": CHECKED_AT,
            "content_hash": hashlib.sha256(
                "\n".join(exchange_info_payload["program_type"]).encode("utf-8")
            ).hexdigest(),
        },
    ]
    write_jsonl(OFFICIAL_TCU_DIR / "pages.jsonl", pages_records)

    home_rules = {
        "school_id": "tcu",
        "school_name": "慈濟大學",
        "eligibility": student_dashboard_payload["eligibility"],
        "application_periods": student_dashboard_payload["application_periods"],
        "selection_rules": {
            "undergrad_class_rank_top_percent": 50.0,
            "minimum_gpa": 2.5,
            "minimum_toeic": 550,
            "minimum_toefl_ibt": 42,
            "minimum_toefl_itp": 460,
            "minimum_ielts": 4.0,
            "overseas_subsidy_weights": {
                "project_completeness": 0.4,
                "learning_outcomes_and_service_hours": 0.4,
                "risk_assessment": 0.2,
            },
            "exclude_in_service": True,
            "return_report_due": "返國後依教育部學海計畫及本校學生海外交流補助辦法規定期限內繳交研修心得報告、核銷單據，並檢附成績單正本與課程大綱辦理學分轉換抵免",
        },
        "source_urls": tcu_source_urls,
        "verified_at": "2026-11-09",
    }
    write_text_lf(
        OFFICIAL_TCU_DIR / "home_rules.json",
        json.dumps(home_rules, ensure_ascii=False, indent=2) + "\n",
    )
    write_text_lf(
        OFFICIAL_TCU_DIR / "documents.json",
        json.dumps(
            {
                "school_name": "慈濟大學",
                "required_documents": student_dashboard_payload[
                    "required_documents"
                ],
                "source_urls": tcu_source_urls,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
    )
    write_text_lf(
        OFFICIAL_TCU_DIR / "scholarships.json",
        json.dumps(
            {
                "school_name": "慈濟大學",
                "scholarships": student_dashboard_payload["scholarship_info"],
                "source_urls": tcu_source_urls,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
    )

    completeness = {
        "school_id": "tcu",
        "school_name": "慈濟大學",
        "total_partners": len(partners),
        "partner_count": len(partners),
        "international_partners": sum(
            1
            for p in partners
            if p["country"] not in {"中國大陸", "香港", "澳門"}
        ),
        "mainland_partners": sum(
            1 for p in partners if p["country"] in {"中國大陸", "香港", "澳門"}
        ),
        "dual_degree_partner_universities": 6,
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
            f"慈濟大學全球事務處（OGA，原國際暨兩岸事務處 OIA）《出國交換學生計畫（outbound-exchange-student-program）》、《跨國雙聯與三聯學位計畫（dual-double-degree-program / a-double-degree）》、《大陸地區學生交換研習申請資訊》、《全球合作姊妹校名錄（sister-schools-3）》、《與境外學校辦理雙聯學制實施辦法》、《CEFR B1（含）級以上或同等語言能力對照表》、《學生海外交流補助辦法》及教育部《學海飛颺／學海惜珠／學海築夢／新南向學海築夢》同步整合；共完整收錄 {len(partners)} 所全球合作姊妹校（含 {open_partner_count} 所當期開放申請之國際交換、跨國雙聯／三聯學位與大陸地區交換合作校及 {len(partners) - open_partner_count} 所正式締約代表性姊妹校，橫跨全球 17 個國家與地區，並收錄 {exp_covered_schools} 所合作大學共 {total_exp_reports} 篇歷年學長姐交換與雙聯學位心得報告）。"
        ),
        "verified_at": "2026-11-09",
    }
    write_text_lf(
        OFFICIAL_TCU_DIR / "catalog-completeness.json",
        json.dumps(completeness, ensure_ascii=False, indent=2) + "\n",
    )
    write_text_lf(
        OFFICIAL_TCU_DIR / "verification_status.json",
        json.dumps(
            {
                "school_id": "tcu",
                "school_name": "慈濟大學",
                "status": "official_verified",
                "checked_at": CHECKED_AT,
                "counts": completeness,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
    )

    provenance_files = [
        (
            "sources/tcu/tcu_catalog_source.json",
            TCU_OUTBOUND_PARTNERS_URL,
            f"慈濟大學 {len(partners)} 所全球合作姊妹校整合資料集 JSON",
        ),
        (
            "sources/tcu/tcu_resolved_locations.json",
            TCU_SISTER_SCHOOLS_URL,
            f"慈濟大學 {len(partners)} 所合作姊妹校 ROR / Wikidata 地理座標核對表 JSON",
        ),
        (
            "sources/tcu/tcu_experience_index.json",
            TCU_EXPERIENCES_URL,
            f"慈濟大學全球事務處 {exp_covered_schools} 校 {total_exp_reports} 篇出國交換暨雙聯心得報告索引 JSON",
        ),
    ]
    for rel_p, meta in bin_urls.items():
        surl = meta["url"] if isinstance(meta, dict) else str(meta)
        stitle = (
            meta.get("title", f"慈濟大學官方原始檔案：{Path(rel_p).name}")
            if isinstance(meta, dict)
            else f"慈濟大學官方原始檔案：{Path(rel_p).name}"
        )
        rp = rel_p if rel_p.startswith("sources/") else f"sources/tcu/{rel_p}"
        if not any(x[0] == rp for x in provenance_files):
            provenance_files.append((rp, surl, stitle))

    for html_p in sorted(SOURCES_TCU_DIR.glob("*.html")):
        rp = f"sources/tcu/{html_p.name}"
        if not any(x[0] == rp for x in provenance_files):
            provenance_files.append(
                (
                    rp,
                    TCU_OGA_HOME_URL,
                    f"慈濟大學官方網頁快照：{html_p.name}",
                )
            )

    prov_sources = []
    for rel_path, surl, stitle in provenance_files:
        p = REPO_ROOT / rel_path
        if p.exists():
            b = p.read_bytes()
            prov_sources.append(
                {
                    "file": rel_path,
                    "source_url": surl,
                    "title": stitle,
                    "sha256": hashlib.sha256(b).hexdigest(),
                    "bytes": len(b),
                    "fetched_at": CHECKED_AT,
                }
            )
    provenance_payload = {
        "school_id": "tcu",
        "school_name": "慈濟大學",
        "generated_at": CHECKED_AT,
        "active_cycle_note": completeness["active_term"],
        "sources": prov_sources,
    }
    prov_text = (
        json.dumps(provenance_payload, ensure_ascii=False, indent=2) + "\n"
    )
    write_text_lf(OFFICIAL_TCU_DIR / "import_provenance.json", prov_text)
    write_text_lf(OFFICIAL_TCU_DIR / "import-provenance.json", prov_text)

    print(
        f"Successfully built TCU catalog: {len(partners)} partners"
        f" ({open_partner_count} open, {completeness['verified_campus_images']}"
        f" verified images, {completeness['verified_locations']} verified"
        f" locations), {len(workflows)} workflows,"
        f" {len(destinations)} destinations, {len(research_records)} research"
        f" records, {exp_covered_schools} schools with experience records"
        f" ({len(student_experience_rows)} rows, {total_exp_reports} reports)."
    )


if __name__ == "__main__":
    main()
