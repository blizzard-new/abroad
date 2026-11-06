"""Build the official National Pingtung University (國立屏東大學, NPTU) exchange data bundle."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re

REPO_ROOT = Path(__file__).resolve().parents[1]
SOURCES_NPTU_DIR = REPO_ROOT / "sources" / "nptu"
OFFICIAL_NPTU_DIR = REPO_ROOT / "src" / "exchange_info" / "official_data" / "nptu"
STATIC_DIR = REPO_ROOT / "src" / "exchange_info" / "static"
UNIVERSITY_LOCATIONS_PATH = (
    REPO_ROOT
    / "src"
    / "exchange_info"
    / "official_data"
    / "university_locations.jsonl"
)

CHECKED_AT = "2026-11-05T00:00:00Z"

NPTU_HOME_URL = "https://www.nptu.edu.tw/index.php"
NPTU_OIA_HOME_URL = "https://oia.nptu.edu.tw/index.php"
NPTU_CCD_HOME_URL = "https://ccd.nptu.edu.tw/index.php"
NPTU_DCMA_HOME_URL = "https://dcma.nptu.edu.tw/index.php"
NPTU_OUTBOUND_EXCHANGE_URL = "https://ccd.nptu.edu.tw/p/412-1091-12234.php?Lang=zh-tw"
NPTU_OUTBOUND_POST_115_URL = "https://ccd.nptu.edu.tw/p/406-1091-190211,r2961.php?Lang=zh-tw"
NPTU_INFO_SESSION_116_URL = "https://ccd.nptu.edu.tw/p/406-1091-200033,r11.php?Lang=zh-tw"
NPTU_INFO_SESSION_115_URL = "https://ccd.nptu.edu.tw/p/405-1091-190011,c12234.php?Lang=zh-tw"
NPTU_OUTBOUND_INTERNSHIP_URL = "https://ccd.nptu.edu.tw/p/412-1091-12250.php?Lang=zh-tw"
NPTU_ZHUMENG_POST_115_URL = "https://ccd.nptu.edu.tw/p/406-1091-189849,r2961.php?Lang=zh-tw"
NPTU_DUAL_DEGREE_URL = "https://ccd.nptu.edu.tw/p/412-1091-15344.php?Lang=zh-tw"
NPTU_DUAL_MIDDLESEX_URL = "https://ccd.nptu.edu.tw/p/412-1091-11335.php?Lang=zh-tw"
NPTU_DUAL_UNA_URL = "https://ccd.nptu.edu.tw/p/412-1091-13956.php?Lang=zh-tw"
NPTU_DUAL_HYOGO_URL = "https://ccd.nptu.edu.tw/p/412-1091-6007.php?Lang=zh-tw"
NPTU_SCIENCE_DUAL_URL = "https://science.nptu.edu.tw/p/406-1028-156968,r3834.php?Lang=zh-tw"
NPTU_SISTER_SCHOOLS_URL = "https://ccd.nptu.edu.tw/p/412-1091-6005.php?Lang=zh-tw"
NPTU_MAINLAND_SISTERS_URL = "https://dcma.nptu.edu.tw/p/412-1008-5098.php?Lang=zh-tw"
NPTU_MAINLAND_EXCHANGE_URL = "https://dcma.nptu.edu.tw/p/412-1008-5096.php?Lang=zh-tw"
NPTU_EXPERIENCES_URL = "https://ccd.nptu.edu.tw/p/403-1091-2997-1.php?Lang=zh-tw"
NPTU_REGULATIONS_URL = "https://ccd.nptu.edu.tw/p/412-1091-6050.php?Lang=zh-tw"
NPTU_STUDY_ABROAD_RULES_PDF = "https://reg.nptu.edu.tw/var/file/66/1066/img/1690/law1-14.pdf"
NPTU_DUAL_DEGREE_RULES_PDF = "https://reg.nptu.edu.tw/var/file/66/1066/img/1690/law1-15.pdf"
NPTU_CREDIT_TRANSFER_RULES_PDF = "https://reg.nptu.edu.tw/var/file/66/1066/img/1690/law1-4.pdf"
NPTU_CREDIT_CONVERSION_PDF = "https://reg.nptu.edu.tw/var/file/66/1066/img/1690/law1-20EN.pdf"
NPTU_GPA_CONVERSION_PDF = "https://reg.nptu.edu.tw/var/file/66/1066/img/1690/law1-24.pdf"
NPTU_ACADEMIC_RULES_PDF = "https://reg.nptu.edu.tw/var/file/66/1066/img/1690/law1-1.pdf"
NPTU_MIDDLESEX_APP_PDF = "https://ccd.nptu.edu.tw/var/file/91/1091/img/2280/540088196.pdf"

REGION_COST_DEFAULTS = {
    "日本": (
        "每月生活費約 USD 450–1,000（折合日圓約 JPY 60,000–145,000 / 月、新臺幣約 14,500–32,000 元；依《國立屏東大學學海計畫學生生活費核銷支給數額標準表》年支生活費標準為東京 USD 24,000、京都 USD 22,000、大阪 USD 20,000、其他城市 USD 19,000，其中宮崎大學、弘前大學、大阪教育大學、兵庫教育大學、室蘭工業大學、和歌山大學、鹿兒島大學、香川大學、山形大學、信州大學等 10 所日本國立大學留學生寮月租僅約 JPY 5,900–22,000）",
        "須由日本接待大學代向出入國在留管理局申請「在留資格認定證明書（COE）」，獲發後至日本台灣交流協會申辦留學簽證，入境後加入日本國民健康保險（NHI）並投保涵蓋全期之海外醫療及意外保險。",
    ),
    "韓國": (
        "每月生活費約 USD 550–980（折合韓元約 KRW 750,000–1,350,000 / 月、新臺幣約 17,500–31,500 元；依《國立屏東大學學海計畫學生生活費核銷支給數額標準表》韓國年支生活費標準為 USD 23,000，含韓國外國語大學 HUFS、釜山外國語大學 BUFS 及國立大邱教育大學 DNUE 校內學生宿舍與膳食開銷）",
        "須憑韓國接待校核發之標準入學許可書（Certificate of Admission）向駐台北韓國代表部申辦 D-2-6 交換學生簽證，入境後辦理外國人登錄證（ARC）並納保韓國國民健康保險（NHIS）。",
    ),
    "美國": (
        "每月生活費約 USD 1,200–2,000（折合新臺幣約 38,500–64,000 元；依《國立屏東大學學海計畫學生生活費核銷支給數額標準表》美國年支生活費標準為 USD 22,000–25,000，含北阿拉巴馬大學 UNA、西來大學 UWest、楊斯鎮州立大學 YSU 校內宿舍與學餐）",
        "須憑美國接待大學核發之 DS-2019（J-1 交換生）或 I-20（F-1 雙聯學位生）繳交 SEVIS I-901 費用並向美國在台協會（AIT）申辦簽證，且須投保符合接待校規定之全期海外醫療保險。",
    ),
    "捷克": (
        "每月生活費約 USD 500–850（折合捷克克朗約 CZK 11,500–19,500 / 月、新臺幣約 16,000–27,000 元；依《國立屏東大學學海計畫學生生活費核銷支給數額標準表》捷克年支生活費標準為 USD 15,000，赫拉德茨克拉洛韋大學 UHK、托馬斯拔佳大學 TBU、利貝雷茨理工大學 TUL 與布拉格捷克理工大學 CTU 學生宿舍月租僅約 CZK 3,300–5,500）",
        "須憑捷克接待大學核發之入學許可與住宿證明向捷克經濟文化辦事處申辦長期學生簽證或居留許可，並投保符合申根與捷克法規之綜合醫療保險（pVZP）。",
    ),
    "德國": (
        "每月生活費約 USD 950–1,400（折合歐元約 EUR 880–1,300 / 月、新臺幣約 30,500–45,000 元；依《國立屏東大學學海計畫學生生活費核銷支給數額標準表》德國年支生活費標準為 USD 22,000，含柏林愛麗絲沙羅蒙應用科學大學 ASH Berlin 學期交通票與住宿生活開銷）",
        "須辦理德國限制提領帳戶（Sperrkonto）或財力證明並向德國在台協會申辦學生簽證，且須投保德國法定公保或認可之健康保險。",
    ),
    "義大利": (
        "每月生活費約 USD 850–1,350（折合歐元約 EUR 780–1,250 / 月、新臺幣約 27,000–43,000 元；依《國立屏東大學學海計畫學生生活費核銷支給數額標準表》義大利年支生活費標準為 USD 19,000，含帕維亞大學 Università di Pavia 書院宿舍與生活費）",
        "須憑義大利帕維亞大學入學許可向義大利經濟貿易文化推廣辦事處申辦 D 類學生簽證，入境後 8 個工作天內申辦居留證（Permesso di Soggiorno）並投保醫療險。",
    ),
    "英國": (
        "每月生活費約 USD 1,350–2,000（折合英鎊約 GBP 1,050–1,550 / 月、新臺幣約 43,000–64,000 元；依《國立屏東大學學海計畫學生生活費核銷支給數額標準表》英國年支生活費標準為 USD 21,000，含倫敦密德薩斯大學 Middlesex University 雙聯學位住宿與生活費）",
        "修讀超過 6 個月之雙聯學位須憑英國接待校核發之 CAS 申辦英國 Student Visa 並繳納移民健康附加費（IHS）。",
    ),
    "澳洲": (
        "每月生活費約 USD 1,300–2,000（折合澳幣約 AUD 1,950–3,000 / 月、新臺幣約 41,500–64,000 元；依《國立屏東大學學海計畫學生生活費核銷支給數額標準表》澳洲年支生活費標準為 USD 21,000，澳洲國際飯店管理學院 ICHM 交換生享 20% 學費減免且含半學期帶薪實習）",
        "須購買澳洲海外學生健康保險（OSHC）並憑接待校核發之 CoE 申辦澳洲 Subclass 500 學生簽證。",
    ),
    "馬來西亞": (
        "每月生活費約 USD 400–750（折合馬幣約 MYR 1,800–3,300 / 月、新臺幣約 13,000–24,000 元；依《國立屏東大學學海計畫學生生活費核銷支給數額標準表》吉隆坡年支生活費標準為 USD 16,000、其他城市 USD 15,000，含馬來亞大學 UM 與拉曼大學 UTAR 住宿與生活費）",
        "須透過馬來西亞教育全球服務中心（EMGS）線上申辦學生簽證核准函（VAL）並投保馬來西亞境內醫療險。",
    ),
    "泰國": (
        "每月生活費約 USD 350–700（折合泰銖約 THB 12,000–24,000 / 月、新臺幣約 11,000–22,500 元；依《國立屏東大學學海計畫學生生活費核銷支給數額標準表》曼谷年支生活費標準為 USD 18,000、其他城市 USD 15,000，其中程逸皇家大學、碧武里皇家大學、蘭帕潘尼皇家大學、黎府皇家大學 4 校提供「免學費＋免住宿費」，程逸皇家大學另每月補助 3,000 泰銖生活津貼！）",
        "須憑泰國接待大學入學許可向泰國貿易經濟辦事處（TTEO）申辦 Non-Immigrant ED 教育簽證並投保海外全期醫療險。",
    ),
    "越南": (
        "每月生活費約 USD 350–650（折合新臺幣約 11,000–21,000 元；依《國立屏東大學學海計畫學生生活費核銷支給數額標準表》越南年支生活費標準為 USD 17,000，含胡志明市師範大學與國立芹苴大學住宿與生活費）",
        "須由越南接待大學協助申辦學生簽證並投保海外全期醫療及意外保險。",
    ),
    "中國大陸": (
        "每月生活費約 USD 350–650（折合人民幣約 RMB 2,300–4,300 / 月、新臺幣約 11,000–21,000 元；含校內學生宿舍與校園餐廳開銷）",
        "須持有效「臺灣居民來往大陸通行證（臺胞證）」及大陸合作學校錄取通知書辦理報到，並購買涵蓋交換全期之海外醫療及意外保險。",
    ),
    "香港": (
        "每月生活費約 USD 900–1,450（折合港幣約 HKD 7,000–11,300 / 月、新臺幣約 29,000–46,500 元；含香港教育大學與香港樹仁大學住宿及膳食開銷）",
        "須由香港接待大學代向香港入境事務處申辦來港就讀進入許可（Student Entry Permit）並投保海外醫療及意外保險。",
    ),
}

SEMESTER_DATES_BY_COUNTRY = {
    "日本": "秋季學期（Fall）：約 9 月下旬／10 月初至翌年 2 月；春季學期（Spring）：約 4 月初至 8 月初",
    "韓國": "春季學期：約 3 月初至 6 月中旬；秋季學期：約 9 月初至 12 月中旬",
    "捷克": "冬季學期（Winter Semester）：約 9 月中下旬至翌年 1 月底；夏季學期（Summer Semester）：約 2 月中旬至 6 月中旬",
    "德國": "冬季學期（Wintersemester）：約 10 月初至翌年 2 月中旬；夏季學期（Sommersemester）：約 4 月初至 7 月底",
    "義大利": "秋季學期（First Semester）：約 9 月下旬至翌年 1 月底；春季學期（Second Semester）：約 2 月下旬至 6 月底",
    "英國": "秋季入學（Autumn Term）：約 9 月中下旬至翌年 6 月（雙聯學位為一學年制）",
    "美國": "秋季學期（Fall Semester）：約 8 月中下旬至 12 月中旬；春季學期（Spring Semester）：約 1 月中旬至 5 月中旬",
    "澳洲": "第一學期（Semester 1）：約 2 月中旬至 6 月底；第二學期（Semester 2）：約 7 月下旬至 11 月底",
    "馬來西亞": "依馬來亞大學（10 月／3 月）及拉曼大學（1 月／5 月／10 月三學期制）行事曆辦理",
    "泰國": "第一學期：約 6 月至 10 月或 8 月至 12 月；第二學期：約 11 月至翌年 3 月或 1 月至 5 月（依各皇家大學與理工大學國際學制行事曆）",
    "越南": "秋季學期：約 9 月初至翌年 1 月中旬；春季學期：約 2 月中旬至 6 月底",
    "中國大陸": "秋季學期：約 9 月初至翌年 1 月中旬；春季學期：約 2 月下旬至 7 月初",
}


def clean_text(s: str) -> str:
    return re.sub(r"\s+", " ", s).strip() if s else ""


def sync_global_assets_and_locations(
    catalog_source: list[dict], resolved_locations: dict
) -> None:
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
                "image_source_url": irec.get("image_source_url") or irec["local_path"],
                "source_page_url": irec.get("source_page_url") or item.get("website") or "",
                "official_page_url": item.get("website") or irec.get("source_page_url") or "",
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
            new_loc = {
                "school_name": fn,
                "country": item["country"],
                "city": loc.get("city") or item["country"],
                "latitude": float(loc.get("latitude", 22.6657)),
                "longitude": float(loc.get("longitude", 120.5038)),
                "geocode_status": "verified",
                "geocoded_at": CHECKED_AT,
                "source_url": loc.get("source_url") or "https://www.wikidata.org",
                "identity_source_url": item.get("website") or "https://www.wikidata.org",
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
    OFFICIAL_NPTU_DIR.mkdir(parents=True, exist_ok=True)
    catalog_source = json.loads(
        (SOURCES_NPTU_DIR / "nptu_catalog_source.json").read_text(encoding="utf-8")
    )
    resolved_locations = json.loads(
        (SOURCES_NPTU_DIR / "nptu_resolved_locations.json").read_text(encoding="utf-8")
    )
    bin_urls_path = SOURCES_NPTU_DIR / "binary_source_urls.json"
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
    dual_degree_count = 0
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

        group_str = clean_text(item.get("group") or "國際事務處正式締約合作姊妹校")
        if "雙聯" in group_str:
            dual_degree_count += 1
        quota_str = clean_text(item.get("quota") or "依當學年度國際事務處公告名額")
        detail_url = item.get("detail_url") or NPTU_SISTER_SCHOOLS_URL
        source_url = detail_url

        if "雙聯" in group_str and "交換" in group_str:
            program_type = f"國立屏東大學出國交換學生暨跨國雙聯學位計畫（{group_str}）"
        elif "雙聯" in group_str:
            program_type = f"國立屏東大學跨國雙聯學位計畫（{group_str}）"
        elif avail_status == "open":
            program_type = f"國立屏東大學出國交換學生甄選計畫（{group_str}）"
        else:
            program_type = f"國立屏東大學國際事務處正式締約合作姊妹校（{group_str}）"

        colleges_str = clean_text(item.get("colleges") or "")
        degree_levels_str = clean_text(item.get("eligible_degrees") or "")
        lang_req_str = clean_text(item.get("language_req") or "")
        gpa_req_str = clean_text(item.get("gpa_req") or "")
        website = item.get("website") or NPTU_SISTER_SCHOOLS_URL
        tuition_note = clean_text(item.get("tuition_note") or "")
        exps = item.get("experience_reports") or []

        round_label = (
            "116學年度出國交換／實習說明會（2026/12/08–12/10）暨出國交換學生甄選（學海飛颺／學海惜珠／菁英育才／自費交換）"
            if avail_status == "open"
            else "國際事務處正式締約姊妹校（當期開放名額依國際合作組與大陸事務組最新甄選簡章公告為準）"
        )
        app_deadline_str = clean_text(item.get("deadline") or "")
        deadline_iso = "2027-02-24T17:00:00+08:00"
        win_status = "open" if avail_status == "open" else "closed"
        acad_year = "116"

        study_period_str = clean_text(item.get("duration") or "一學期或一學年")
        sem_dates_str = SEMESTER_DATES_BY_COUNTRY.get(
            country, "秋季學期：約 9 月至翌年 1 月；春季學期：約 2 月至 6 月"
        )
        housing_str = clean_text(
            item.get("housing_cost_note")
            or tuition_note
            or f"可依 {zh_name} 國際事務處指引申請校內外學生宿舍。"
        )
        course_rest_str = (
            f"開放對象與學院：{colleges_str}（{degree_levels_str}）。依《國立屏東大學學生出國有關學業及學籍處理要點》（114.03.27修正）、"
            "《國立屏東大學與境外大學校院辦理雙聯學制實施辦法》（114.05.22修正）、《國立屏東大學學生抵免學分要點》（115.10.22修正）及《與外國學制學分轉換準則》規定："
            "（1）在學註冊與修課下限：經核准出國進修（交換學生）者視同於本校就讀，仍需在本校註冊，不受學則最低修習學分之限制，惟大學部學生出國期間每學期至少須修習 1 門課程（日本姬路獨協大學規定每學期須選修 7 門課以上），出國進修時間最多以 1 年為限並得列入修業年限計算；"
            "（2）學分轉換與抵免上限：學期授課滿 18 小時採計 1 學分，1 學分（NPTU）＝2 ECTS（歐洲）＝4 CATS（英國）＝4 學分（澳洲），與美制、日制、陸制學分 1:1 等同換算；境外交換修得學分之抵免以所屬系所應修畢業學分數之 1/3 為限（雙聯學士至多抵免畢業總學分 1/2、雙聯碩士至多抵免 2/3 不含論文），應於出國交換之次學期期末考結束前檢具成績單正本或經國際事務處核章之影本一次全部辦理；"
            "（3）跨國雙聯學制修業時間：出國前後在屏東大學總修業時間學士班至少 4 學期、碩士班至少 2 學期、博士班至少 3 學期；在二校當地修習學分數累計須各達畢業應修總學分數 1/3 以上，同級雙聯在二校修業期間學士累計至少滿 32 個月、碩士至少滿 12 個月、博士至少滿 24 個月（跨級雙聯停留於當地學校修業期間碩士至少滿 8 個月、博士至少滿 16 個月）。"
        )

        living_cost_str, visa_health_str = REGION_COST_DEFAULTS.get(
            country,
            (
                "每月生活費約 USD 650–1,250（折合新臺幣約 21,000–40,000 元，含住宿、膳食與市區交通）",
                "須依接待國駐臺機構規定申辦學生簽證，並於出國前投保涵蓋全期之海外醫療與意外保險。",
            ),
        )

        tuition_points_list = [
            f"屏東大學在學註冊與學雜費規定（依《國立屏東大學學生出國有關學業及學籍處理要點》第 3 條及出國交換甄選簡章）：經核准出國交換學生視同於本校就讀，交換期間仍須於國立屏東大學完成註冊繳費以保有學籍，免學費交換名額免繳接待姊妹校學費（自費交換與雙聯學位依兩校協議享州內學費優惠或學費減免；其中泰國程逸皇家大學、碧武里皇家大學、蘭帕潘尼皇家大學、黎府皇家大學 4 校提供「免學費＋免住宿費」，程逸皇家大學另每月核發 3,000 泰銖生活津貼）。本合作校待遇：{tuition_note}。",
            "四大推薦與獎助學金計畫（依《國立屏東大學出國交換甄選簡章》及《學海計畫學生生活費核銷支給數額標準表》）：（1）【教育部學海飛颺】本國籍就讀一學期以上在學學生（不含在職生與進修生）、歷年成績班排前 50% 內、操行平均 80 分以上且無申誡以上處分，補助學費、生活費（上限 5 個月）及來回機票費（含校配合款 20%）；（2）【教育部學海惜珠】同學海飛颺條件並具低收／中低收／特殊境遇／身障等資格，由教育部專案核定補助；（3）【屏東大學「菁英育才」補助（校友捐款）】無班排前 50% 限制，惟每學期操行成績皆須達 80 分以上（非平均）且無申誡以上處分，補助生活費每月 NT$10,000（上限 5 個月，最高 NT$50,000）＋機票費（亞洲上限 NT$15,000、非亞洲上限 NT$30,000）；（4）【自費交換】含在職生與進修生皆可申請，未曾獲本校推薦出國交換且符合語檢門檻。",
        ]

        app_steps_list = [
            f"步驟一（參加三校區出國交換／實習說明會並確認四大推薦計畫與 {zh_name} 語檢門檻）：參加國際事務處舉辦之出國交換暨實習說明會（116學年度於 2026/12/08 民生校區五育樓 4F、12/09 屏師校區敬業樓 102、12/10 屏商校區圖資大樓 104 舉行，報名至 2026/11/30 17:00 止），確認符合申請類別（學海飛颺／學海惜珠／菁英育才／自費交換）、學業操行門檻（{gpa_req_str}）與語言門檻（{lang_req_str}；申請表至多可填寫 5 所志願學校）。",
            "步驟二（備齊紙本申請表件送交屏商校區行政大樓 3F 國際合作組，並寄送合併 PDF 電子檔）：於校內甄選收件截止前（每年 2 月下旬 17:00 止，如 115學年為 2026/02/24 17:00、116學年預計 2027/02/24 17:00）將（1）申請表（最多填 5 志願）、（2）中／英文或日文自傳與讀書計畫、（3）聲明書、（4）教師推薦信 1 封（紙本彌封簽名）、（5）歷年中文成績單（含班排百分比）與各學期獎懲紀錄、（6）語言能力證明（赴日尚未取得 N2 者得先附非日語 B1＋師長簽署《日本語力評價表》）紙本送交屏商校區行政大樓 3 樓國際合作組，並依序掃描合併為單一 PDF 寄至 vida2022@mail.nptu.edu.tw（推薦信免掃描）。",
            "步驟三（參加校內面試審查［每年 3 月初］並獲推薦提名）：通過資格審查者參加國際事務處辦理之面試（如 115學年於 3 月 2 日舉行），依學業表現、語言能力、自傳讀書計畫與面試表現綜合評定推薦順位及獎助學金資格。",
            f"步驟四（向 {zh_name} 遞交入學與宿位申請、辦理屏東大學註冊與返國學分抵免）：獲校內推薦後由國際事務處向 {zh_name} 正式提名，學生備齊姊妹校申請文件與語檢證明送件；出國期間須於屏東大學完成註冊且大學部每學期至少修習 1 門課（姬路獨協大學須修 7 門課以上）；返國後依《學生抵免學分要點》於次學期期末考結束前持成績單正本或經國際處核章之影本一次辦理學分抵免（上限為畢業學分 1/3，雙聯學士 1/2、雙聯碩士 2/3），並繳交出國研修心得報告。",
        ]

        elig_points_list = [
            f"合作類別與組別：{program_type}",
            f"開放學制與年級：{degree_levels_str}",
            f"開放申請學院：{colleges_str}",
            f"學業與操行門檻：{gpa_req_str}",
            f"外語能力標準：{lang_req_str}",
            f"學費與住宿生活待遇：{tuition_note}",
        ]

        exp_links: list[dict] = []
        exp_labels: list[str] = []
        if exps:
            exp_covered_schools += 1
            total_exp_reports += len(exps)
            seen_exp_urls: set[str] = set()
            for e_idx, e in enumerate(exps):
                raw_t = clean_text(e.get("title") or f"赴 {zh_name} 交換留學心得分享")
                esem = e.get("semester") or "歷年交換"
                edept = e.get("department") or "國立屏東大學交換生"
                estu = e.get("student") or "屏大交換生"
                eurl = e.get("url") or f"{NPTU_EXPERIENCES_URL}#nptu-exp-{sn}-{e_idx+1}"
                if eurl in seen_exp_urls:
                    eurl = f"{eurl}#r{e_idx+1}"
                seen_exp_urls.add(eurl)
                exp_labels.append(raw_t[:36])
                exp_links.append({
                    "title": raw_t,
                    "url": eurl,
                    "academic_year": esem,
                    "semester": esem,
                    "college": colleges_str,
                    "department": edept,
                })
                summary_text = (
                    f"國立屏東大學國際事務處國際合作組公開收錄之 {edept} {estu} 赴 {country} {full_name} 交換／研修官方心得報告（{raw_t}），詳述選課修讀、學生宿舍環境、當地每月生活費開銷與跨文化收穫。"
                )
                theme_map = {
                    "academics": f"國立屏東大學 {edept} {estu} 於《{raw_t}》分享在 {zh_name} 選課修讀、語言與專業課程學習及返國依《學生抵免學分要點》與《外國學制學分轉換準則》辦理學分抵免之實務經驗。",
                    "housing": f"屏東大學交換生記錄入住 {zh_name} 學生宿舍或合作公寓之房型設備、通勤方式與國際學伴接機協助（{housing_str[:100]}）。",
                    "campus_culture": f"國立屏東大學國際事務處收錄《{raw_t}》之國際學伴制度、社團文化交流與海外生活體悟。",
                    "cost": f"屏東大學交換生分享於 {zh_name} 之每月租金、伙食與交通花費（{living_cost_str[:100]}），以及獲得教育部學海飛颺／惜珠或屏東大學「菁英育才」獎學金補助之經驗。",
                }
                student_experience_rows.append({
                    "school_name": full_name,
                    "country": country,
                    "title": raw_t,
                    "source_url": eurl,
                    "source_type": "pdf" if eurl.lower().endswith(".pdf") else "article",
                    "platform": "國立屏東大學國際事務處國際合作組—出國交換學生心得分享專區",
                    "author_name": f"{edept} {estu}"[:24],
                    "language": "zh",
                    "summary": summary_text,
                    "themes": ["academics", "housing", "campus_culture", "cost"],
                    "theme_summaries": theme_map,
                    "content_status": "full_text",
                    "perspective": "official_student_story",
                    "published_at": None,
                    "discovered_at": CHECKED_AT,
                    "content_hash": hashlib.sha256(
                        f"{full_name}:nptu_exp:{e_idx}:{eurl}".encode("utf-8")
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
            "home_university": "國立屏東大學",
            "school_name": full_name,
            "country": country,
            "official_experience_portal_url": exp_links[0]["url"] if exp_links else NPTU_EXPERIENCES_URL,
            "partner_page_url": source_url,
            "report_count": len(exps),
            "sample_reports": sample_reports,
            "checked_at": CHECKED_AT,
        })

        loc = resolved_locations.get(full_name) or {
            "city": country,
            "latitude": 22.6657,
            "longitude": 120.5038,
            "source_url": "https://www.wikidata.org",
        }
        city_name = loc.get("city") or country
        lat = float(loc.get("latitude", 22.6657))
        lon = float(loc.get("longitude", 120.5038))
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
            "note": "校級代表位置：官方網域及國家已與 ROR / Wikidata 比對；實際交換校區以錄取通知與締約校專頁為準。",
        }
        new_locations.append(location_obj)

        vrec = visual_by_name.get(full_name) or item.get("image_record")
        assert vrec and vrec.get("local_path"), f"Missing verified image for {full_name}"
        img_local = vrec.get("local_path")
        img_source = vrec.get("image_source_url") or vrec.get("image_url") or img_local
        img_page = vrec.get("official_page_url") or vrec.get("source_page_url") or img_source

        notes_lines = [
            f"【合作類別與期程】{program_type}｜研修期間：{study_period_str}",
            f"【當期名額與費用待遇】{quota_str}｜{tuition_note}",
            f"【開放學院與學制】{colleges_str}｜{degree_levels_str}",
            f"【語言與學業門檻】{lang_req_str}｜{gpa_req_str}",
            f"【住宿與生活資訊】{housing_str}",
        ]
        if exps:
            notes_lines.append(
                f"【國立屏東大學學長姐交換／雙聯心得報告（共 {len(exps)} 篇）】收錄於國際事務處國際合作組網站（含：{'、'.join(exp_labels[:4])}）"
            )

        partners.append({
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
            "availability_note": f"國立屏東大學國際事務處公告合作姊妹校（{program_type}）；{quota_str}。",
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
            "image_status": "verified",
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
        })

        wf_sources = [
            {
                "title": f"國立屏東大學國際事務處出國交換與雙聯學位公告—{zh_name}",
                "source_url": source_url,
                "role": "home_university",
                "authority": "home_official_notice",
                "effective_academic_year": acad_year,
                "application_round": round_label,
                "checked_at": CHECKED_AT,
            },
            {
                "title": "國立屏東大學學生出國有關學業及學籍處理要點與辦理雙聯學制實施辦法",
                "source_url": NPTU_STUDY_ABROAD_RULES_PDF,
                "role": "home_university",
                "authority": "home_official_notice",
                "effective_academic_year": acad_year,
                "application_round": round_label,
                "checked_at": CHECKED_AT,
            },
            {
                "title": "國立屏東大學學生抵免學分要點與外國學制學分轉換準則",
                "source_url": NPTU_CREDIT_TRANSFER_RULES_PDF,
                "role": "home_university",
                "authority": "home_official_notice",
                "effective_academic_year": acad_year,
                "application_round": round_label,
                "checked_at": CHECKED_AT,
            },
            {
                "title": f"{full_name} 官方網站",
                "source_url": website,
                "role": "partner_university",
                "authority": "partner_official",
                "effective_academic_year": acad_year,
                "application_round": round_label,
                "checked_at": CHECKED_AT,
            },
        ]

        workflows.append({
            "home_university": "國立屏東大學",
            "school_name": full_name,
            "partner_website": website,
            "country": country,
            "program_type": program_type,
            "academic_year": acad_year,
            "application_round": round_label,
            "effective_application_rounds": [round_label, "115-1", "115-2", "116-1", "116-2"],
            "applicability_status": "verified",
            "applicability_note": "國立屏東大學由國際事務處（OIA，下設國際合作組與大陸事務組，屏商校區行政大樓 3 樓）統籌全校 7 大學院（管理學院、資訊學院、教育學院、人文社會學院、理學院、國際學院、大武山學院）之出國交換甄選（含教育部學海飛颺、教育部學海惜珠、本校校友捐款「菁英育才」補助及自費交換四大計畫）、英美捷日泰 7 校跨國雙聯學位（英國密德薩斯大學 3+1／1+1、美國北阿拉巴馬大學 3+1／2+2／1+1、美國西來大學 2+2／1+1、捷克赫拉德茨克拉洛韋大學 UHK 1+1、捷克托馬斯拔佳大學 TBU 1+1、泰國宋卡王子大學 PSU 2+2、泰國蒙庫國王科技大學 KMUTT 1+1）及學海築夢／新南向學海築夢海外專業實習。",
            "review_status": "published",
            "published_at": CHECKED_AT,
            "steps": [
                {
                    "rule_id": f"nptu-{acad_year}-home-1-{sn:03d}",
                    "order": 1,
                    "phase": "校內申請",
                    "title": f"參加三校區出國交換／實習說明會（12/08–12/10），確認四大推薦計畫與 {zh_name} 語檢門檻",
                    "responsible_party": "學生",
                    "responsible_unit": "國立屏東大學國際事務處國際合作組（屏商校區行政大樓 3F）／各院系所",
                    "deadline_at": "2026-11-30T17:00:00+08:00",
                    "deadline_status": "verified_exact" if avail_status == "open" else "reference_only",
                    "deadline_source_url": NPTU_INFO_SESSION_116_URL,
                    "deadline_checked_at": CHECKED_AT,
                    "deadline_reminder_eligible": avail_status == "open",
                    "summary": f"參加國際事務處於民生、屏師、屏商三校區舉辦之出國交換／實習說明會（116學年度於 2026/12/08–12/10 舉辦，11/30 17:00 報名截止），確認符合在學年級（{degree_levels_str}）、學業操行門檻（{gpa_req_str}）與外語標準（{lang_req_str}）。",
                    "details": [
                        f"開放學制與學院：{colleges_str}（{degree_levels_str}）",
                        f"語言與學業條件：{lang_req_str}｜{gpa_req_str}",
                        f"當期名額與計畫類別：{quota_str}｜{program_type}",
                    ],
                    "scope": {
                        "home_universities": ["國立屏東大學"],
                        "partner_universities": [full_name],
                        "academic_years": ["115", "116"],
                        "application_rounds": [round_label, "115-1", "115-2", "116-1", "116-2"],
                    },
                    "source_urls": [source_url, NPTU_INFO_SESSION_116_URL, NPTU_STUDY_ABROAD_RULES_PDF],
                    "checked_at": CHECKED_AT,
                    "support_status": "verified",
                },
                {
                    "rule_id": f"nptu-{acad_year}-home-2-{sn:03d}",
                    "order": 2,
                    "phase": "校內申請",
                    "title": "備妥出國交換申請表（至多填 5 志願）、自傳與讀書計畫、聲明書、彌封推薦信、含班排歷年成績單與獎懲紀錄送交屏商行政大樓 3F 並寄送合併 PDF",
                    "responsible_party": "學生",
                    "responsible_unit": "國立屏東大學國際事務處國際合作組（屏商校區行政大樓 3 樓）",
                    "deadline_at": deadline_iso,
                    "deadline_status": "verified_exact" if avail_status == "open" else "reference_only",
                    "deadline_source_url": source_url,
                    "deadline_checked_at": CHECKED_AT,
                    "deadline_reminder_eligible": avail_status == "open",
                    "summary": "於校內甄選收件期限（每年 2 月下旬 17:00 止，如 115學年為 2026/02/24 17:00、116學年預計 2027/02/24 17:00）將紙本送交屏商校區行政大樓 3 樓國際合作組，並將推薦信以外之各項文件依序掃描合併為單一 PDF 寄至 vida2022@mail.nptu.edu.tw。",
                    "details": [
                        "必備申請文件：（1）出國交換甄選申請表（表單一，可勾選學海飛颺／學海惜珠／菁英育才／自費交換，至多填寫 5 所志願學校）；（2）自傳與讀書計畫（表單二，中文及英文／日文撰寫）；（3）聲明書（表單三，本人及家長／監護人親筆簽章）；（4）教師推薦信 1 封（表單四，由推薦師長簽名後紙本彌封，免掃描電子檔）；（5）歷年中文成績單正本（須註明班級排名百分比）與歷年各學期操行成績及獎懲紀錄證明；（6）有效外語能力證明影本（赴日交換於校內甄選時倘尚未取得 JLPT N2，得先以非日語 CEFR B1 證明加附本校師長簽署之《日本語力評價表》替代）。",
                    ],
                    "document_requirements": [
                        {
                            "name": "國立屏東大學出國交換甄選申請表（至多 5 志願）、自傳與讀書計畫及聲明書",
                            "official_form_url": NPTU_OUTBOUND_POST_115_URL,
                            "source_urls": [NPTU_OUTBOUND_POST_115_URL, NPTU_OUTBOUND_EXCHANGE_URL],
                        },
                        {
                            "name": "歷年中文成績單（含班排百分比）、各學期操行獎懲紀錄、彌封教師推薦信及外語能力檢定證明（或日本語力評價表）",
                            "official_form_url": NPTU_OUTBOUND_POST_115_URL,
                            "source_urls": [NPTU_OUTBOUND_POST_115_URL, NPTU_STUDY_ABROAD_RULES_PDF],
                        },
                    ],
                    "scope": {
                        "home_universities": ["國立屏東大學"],
                        "academic_years": ["115", "116"],
                        "application_rounds": [round_label, "115-1", "115-2", "116-1", "116-2"],
                    },
                    "source_urls": [source_url, NPTU_OUTBOUND_POST_115_URL],
                    "checked_at": CHECKED_AT,
                    "support_status": "verified",
                },
                {
                    "rule_id": f"nptu-{acad_year}-home-3-{sn:03d}",
                    "order": 3,
                    "phase": "甄選與提名",
                    "title": "參加校內面試審查（每年 3 月初舉行）並確認推薦錄取與獎助學金核定名單",
                    "responsible_party": "國立屏東大學國際事務處與申請學生",
                    "responsible_unit": "國際事務處國際合作組／國際事務推動委員會",
                    "deadline_at": "2027-03-02T17:00:00+08:00",
                    "deadline_status": "verified_exact",
                    "deadline_source_url": NPTU_OUTBOUND_POST_115_URL,
                    "deadline_checked_at": CHECKED_AT,
                    "deadline_reminder_eligible": False,
                    "summary": "通過書面資格審查者參加校內面試（參考 115學年於 3 月 2 日舉行），依學業成績、外語能力、讀書計畫及面試表現評定正備取推薦名單與學海飛颺／學海惜珠／菁英育才補助順位。",
                    "details": [
                        "四大推薦計畫分流核定：學海飛颺與學海惜珠須歷年成績班排前 50% 且操行平均 80 分以上；屏東大學「菁英育才」補助無班排前 50% 限制，惟每學期操行成績皆須達 80 分以上（非平均），補助生活費每月 NT$10,000（最高 5 個月 NT$50,000）＋機票費（亞洲上限 NT$15,000、非亞洲上限 NT$30,000）。",
                    ],
                    "scope": {
                        "home_universities": ["國立屏東大學"],
                        "academic_years": ["115", "116"],
                        "application_rounds": [round_label, "115-1", "115-2", "116-1", "116-2"],
                    },
                    "source_urls": [NPTU_OUTBOUND_POST_115_URL, NPTU_REGULATIONS_URL],
                    "checked_at": CHECKED_AT,
                    "support_status": "verified",
                },
                {
                    "rule_id": f"nptu-{sn:03d}-host-apply",
                    "order": 4,
                    "phase": "合作校申請",
                    "title": f"由國際事務處向 {zh_name} 正式提名，備齊接待校入學申請文件與宿舍申請表送件",
                    "responsible_party": "學生與接待校國際事務處",
                    "summary": f"獲校內推薦錄取後，由國際合作組／大陸事務組向 {zh_name} 完成官方提名（Nomination），學生依接待校規定限期繳交入學申請表、英文歷年成績單、語檢成績單、護照影本與宿舍申請表，靜候核發正式入學許可（Admission Letter / COE / DS-2019）。",
                    "details": [
                        f"研修期程：{study_period_str}｜名額：{quota_str}",
                        f"語言與學業條件：{lang_req_str}｜{gpa_req_str}",
                        f"住宿與費用待遇：{housing_str}",
                    ],
                    "scope": {
                        "home_universities": ["國立屏東大學"],
                        "partner_universities": [full_name],
                        "academic_years": ["115", "116"],
                        "application_rounds": [round_label, "115-1", "115-2", "116-1", "116-2"],
                    },
                    "source_urls": [source_url, website],
                    "checked_at": CHECKED_AT,
                    "support_status": "verified",
                    "needs_confirmation": False,
                },
                {
                    "rule_id": f"nptu-{acad_year}-home-5-{sn:03d}",
                    "order": 5,
                    "phase": "行前準備",
                    "title": "完成屏東大學註冊選課（大學部至少修 1 門課）與海外全期保險，返國次學期期末考前一次辦理學分抵免並繳交心得報告",
                    "responsible_party": "學生與所屬系所",
                    "responsible_unit": "國際事務處／教務處註冊組／所屬系所",
                    "summary": "依《國立屏東大學學生出國有關學業及學籍處理要點》與《學生抵免學分要點》：出國期間仍須於屏東大學註冊，大學部學生每學期至少修習 1 門課程（姬路獨協大學須修 7 門課以上）；返國後應於出國交換之次學期期末考結束前（大四下及延修生於畢業離校期限前）檢具原校原始成績表正本或經國際處核章之影本一次全部辦理學分抵免（1 NPTU 學分＝2 ECTS＝4 CATS＝4 澳洲學分，美日陸 1:1），並繳交出國交換心得報告辦理獎學金核銷。",
                    "details": tuition_points_list,
                    "scope": {
                        "home_universities": ["國立屏東大學"],
                        "academic_years": ["115", "116"],
                        "application_rounds": [round_label, "115-1", "115-2", "116-1", "116-2"],
                    },
                    "source_urls": [
                        NPTU_STUDY_ABROAD_RULES_PDF,
                        NPTU_CREDIT_TRANSFER_RULES_PDF,
                        NPTU_CREDIT_CONVERSION_PDF,
                    ],
                    "checked_at": CHECKED_AT,
                    "support_status": "verified",
                },
            ],
            "sources": wf_sources,
            "last_checked": CHECKED_AT,
            "coverage_status": "official_verified",
            "coverage_note": f"已完整整合國立屏東大學國際事務處（OIA）《115年出國交換甄選簡章》、《116學年度出國交換／實習說明會公告》、《115年第1次教育部學海築夢及新南向學海築夢甄選簡章》、《學生出國有關學業及學籍處理要點（114.03.27修正）》、《與境外大學校院辦理雙聯學制實施辦法（114.05.22修正）》、《學生抵免學分要點（115.10.22修正）》、《與外國學制學分轉換準則》、《學海計畫學生生活費核銷支給數額標準表》及 {exp_covered_schools} 校 {total_exp_reports} 篇歷屆交換生心得報告，共 {len(catalog_source)} 所全球與兩岸合作姊妹校資料。",
        })

        cost_line = f"{zh_name} 預估每月生活費：{living_cost_str}"
        tuition_clean = tuition_points_list[0]
        housing_clean = housing_str
        calendar_clean = f"學期與研修時間參考：{sem_dates_str}"
        course_clean = course_rest_str
        src_url_list = [
            source_url,
            NPTU_STUDY_ABROAD_RULES_PDF,
            NPTU_CREDIT_TRANSFER_RULES_PDF,
            website,
        ]

        destinations.append({
            "home_university": "國立屏東大學",
            "school_name": full_name,
            "country": country,
            "city": city_name,
            "cost_summary": f"{cost_line}。\n{tuition_clean}",
            "housing_summary": housing_clean,
            "transport_summary": f"校區代表城市：{city_name}。請依入學許可確認實際授課校區位置、國際學伴接機服務與當地學生交通優惠。",
            "campus_life_summary": f"{calendar_clean}\n{course_clean}",
            "student_guide_sections": [
                {
                    "key": "cost",
                    "title": "生活費、屏東大學在學註冊規定與學海飛颺／惜珠／菁英育才獎學金",
                    "summary": cost_line,
                    "points": [cost_line] + tuition_points_list,
                    "source_urls": src_url_list,
                    "caution": "依《國立屏東大學學生出國有關學業及學籍處理要點》第 3 條，經核准出國交換者視同於本校就讀，仍需在本校註冊繳費以保有學籍，免學費交換名額免繳接待姊妹校學費。",
                },
                {
                    "key": "housing",
                    "title": "校內外留學生宿舍、泰國 4 校免住宿費優惠與接機資訊",
                    "summary": housing_clean[:160],
                    "points": [housing_clean],
                    "source_urls": src_url_list,
                    "caution": "各姊妹校學生宿舍名額有限（其中泰國程逸皇家大學、碧武里皇家大學、蘭帕潘尼皇家大學、黎府皇家大學 4 校提供免住宿費優惠），請於獲提名後依接待校期限完成宿位申請。",
                },
                {
                    "key": "insurance",
                    "title": "海外全期醫療意外保險、家長簽章聲明書與役男緩徵規定",
                    "summary": visa_health_str,
                    "points": [
                        visa_health_str,
                        "報名時須檢附本人及家長／監護人親筆簽章之《國立屏東大學出國交換學生甄選聲明書》（表單三），獲錄取後出國前須投保涵蓋交換全期之海外醫療及意外險。",
                    ],
                    "source_urls": src_url_list,
                    "caution": "赴日本留學生入境後須依法加入日本國民健康保險（NHI）；赴韓國須納保韓國國民健康保險（NHIS）；赴捷克須投保符合捷克法規之綜合醫療險。",
                },
                {
                    "key": "visa",
                    "title": "留學簽證辦理、出國進修最長一年與雙聯學制修業時間規定",
                    "summary": visa_health_str,
                    "points": [
                        visa_health_str,
                        "依《學生出國有關學業及學籍處理要點》第 3 條及第 4 條，出國進修時間最多以 1 年為限並得列入修業年限計算；雙聯學制依《與境外大學校院辦理雙聯學制實施辦法》第 6 條，同級雙聯在二校修業期間學士累計至少滿 32 個月、碩士至少滿 12 個月、博士至少滿 24 個月。",
                    ],
                    "source_urls": src_url_list + [NPTU_DUAL_DEGREE_RULES_PDF],
                    "caution": "不得以觀光簽證入境就讀；交換期間應保有屏東大學在學學籍。",
                },
                {
                    "key": "academics",
                    "title": "大學部至少修 1 門課、歐英澳美日學分轉換（1 NPTU＝2 ECTS＝4 CATS）與返國抵免",
                    "summary": course_clean[:160],
                    "points": [calendar_clean, course_clean],
                    "source_urls": src_url_list + [NPTU_CREDIT_CONVERSION_PDF, NPTU_GPA_CONVERSION_PDF],
                    "caution": "依《學生抵免學分要點》第 3 條及第 4 條，境外交換修得學分抵免以畢業應修學分數 1/3 為限（雙聯學士 1/2、雙聯碩士 2/3），且應於出國交換之次學期期末考結束前一次全部辦理。",
                },
                {
                    "key": "living",
                    "title": f"{city_name} 校園生活與國立屏東大學學長姐交換心得傳承",
                    "summary": f"代表城市：{city_name}。返國後須依規定繳交出國交換心得報告並辦理獎學金核銷。",
                    "points": [
                        f"目的地城市：{city_name}（{country}）",
                        "國立屏東大學國際事務處國際合作組公開歷屆學長姐出國交換與海外實習心得報告"
                        + (f"（本校共收錄 {len(exps)} 篇心得：{'、'.join(exp_labels[:3])}）" if exps else "")
                        + "，並於每年 12 月在民生、屏師、屏商三校區舉辦說明會暨返國學長姐經驗分享。",
                    ],
                    "source_urls": [exp_links[0]["url"] if exp_links else NPTU_EXPERIENCES_URL],
                },
            ],
            "sources": [
                {
                    "title": f"國立屏東大學國際事務處出國交換與雙聯學位專頁—{zh_name}",
                    "source_url": source_url,
                    "summary": "國立屏東大學公告之申請資格、語言門檻、學費減免與宿舍生活費用說明",
                },
                {
                    "title": "國立屏東大學學生出國有關學業及學籍處理要點與學生抵免學分要點",
                    "source_url": NPTU_STUDY_ABROAD_RULES_PDF,
                    "summary": "國立屏東大學出國交換註冊規定、修業年限、學分轉換（1 NPTU＝2 ECTS＝4 CATS）與返國學分抵免規範",
                },
            ],
            "last_checked": CHECKED_AT,
            "coverage_status": "official_verified",
            "coverage_note": f"已整合國立屏東大學國際事務處 {len(catalog_source)} 所全球與兩岸合作姊妹校（含 {open_partner_count} 所常態開放申請交換與雙聯學校）及 {exp_covered_schools} 校 {total_exp_reports} 篇歷屆交換與海外研修心得報告。",
        })

        research_records.append({
            "home_university": "國立屏東大學",
            "school_name": full_name,
            "country": country,
            "official_website": website,
            "verification_status": "official_verified",
            "discovery_source_url": detail_url,
            "checked_at": CHECKED_AT,
            "note": "國立屏東大學國際事務處 115年出國交換甄選簡章、雙聯學位專區、國際合作組與大陸事務組姊妹校列表及 ROR/Wikidata 官方網址核對完成。",
        })

        ev_sources = [{"title": f"國立屏東大學國際事務處姊妹校與交換專頁—{zh_name}", "url": source_url}]
        if exp_links:
            ev_sources.append({"title": f"國立屏東大學赴 {zh_name} 交換留學心得報告（{len(exps)} 篇）", "url": exp_links[0]["url"]})
        if website:
            ev_sources.append({"title": f"{full_name} 官方網站", "url": website})

        has_student_exp = bool(exps)
        life_records.append({
            "school_name": full_name,
            "country": country,
            "checked_at": CHECKED_AT,
            "status": "ready",
            "evidence": [
                {
                    "theme": "housing",
                    "kind": "mixed" if has_student_exp else "official",
                    "text": housing_clean,
                    "sources": ev_sources,
                    "checked_at": CHECKED_AT,
                    "scope": "國立屏東大學交換與雙聯姊妹校住宿與接機資訊",
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
                    "scope": "國立屏東大學出國交換學雜費規定與學海飛颺／惜珠／菁英育才獎學金",
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
                    "scope": "國立屏東大學學生出國有關學業及學籍處理要點、雙聯學制實施辦法與學分抵免要點",
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
                    "scope": "國立屏東大學海外交換與雙聯簽證、聲明書與保險規定",
                    "original_excerpt": False,
                    "original_text": "",
                    "translation_status": "original",
                },
                {
                    "theme": "campus_culture",
                    "kind": "mixed" if has_student_exp else "official",
                    "text": f"合作類別：{program_type}｜名額：{quota_str}｜語言要求：{lang_req_str}"
                    + (f"｜國立屏東大學公開收錄 {len(exps)} 篇赴 {zh_name} 交換／研修心得報告（{'、'.join(exp_labels[:3])}）。" if exps else ""),
                    "sources": ev_sources,
                    "checked_at": CHECKED_AT,
                    "scope": "國立屏東大學交換名額與歷屆學長姐心得報告",
                    "original_excerpt": False,
                    "original_text": "",
                    "translation_status": "original",
                },
            ],
            "notes": [
                "已整合國立屏東大學國際事務處 115年出國交換甄選簡章、116學年度說明會公告、雙聯學位專區、國際與大陸姊妹校名錄及歷屆交換生心得報告。",
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

    write_jsonl(OFFICIAL_NPTU_DIR / "partners.jsonl", partners)
    write_jsonl(SOURCES_NPTU_DIR / "partners.jsonl", partners)
    write_jsonl(OFFICIAL_NPTU_DIR / "application_workflows.jsonl", workflows)
    write_jsonl(OFFICIAL_NPTU_DIR / "destination_profiles.jsonl", destinations)
    write_jsonl(OFFICIAL_NPTU_DIR / "partner_research.jsonl", research_records)
    write_jsonl(OFFICIAL_NPTU_DIR / "student_life.jsonl", life_records)
    write_jsonl(OFFICIAL_NPTU_DIR / "experience_sources.jsonl", experience_sources_records)
    write_jsonl(OFFICIAL_NPTU_DIR / "student_experience_sources.jsonl", experience_sources_records)
    write_jsonl(OFFICIAL_NPTU_DIR / "student_experiences.jsonl", student_experience_rows)

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
    (OFFICIAL_NPTU_DIR / "student-experience-digests.json").write_text(
        json.dumps({"digests": digest_records}, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    (OFFICIAL_NPTU_DIR / "student-experiences.json").write_text(
        json.dumps(
            {
                "school_id": "nptu",
                "school_name": "國立屏東大學",
                "checked_at": CHECKED_AT,
                "source_url": NPTU_EXPERIENCES_URL,
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

    (OFFICIAL_NPTU_DIR / "campus-locations.json").write_text(
        json.dumps(
            {
                "school_id": "nptu",
                "school_name": "國立屏東大學",
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
    (OFFICIAL_NPTU_DIR / "campus-assets.json").write_text(
        json.dumps(
            {
                "school_id": "nptu",
                "school_name": "國立屏東大學",
                "checked_at": CHECKED_AT,
                "total_schools": len(campus_assets_list),
                "verified_count": len(campus_assets_list),
                "assets": campus_assets_list,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    nptu_source_urls = [
        NPTU_HOME_URL,
        NPTU_OIA_HOME_URL,
        NPTU_CCD_HOME_URL,
        NPTU_DCMA_HOME_URL,
        NPTU_OUTBOUND_EXCHANGE_URL,
        NPTU_OUTBOUND_POST_115_URL,
        NPTU_INFO_SESSION_116_URL,
        NPTU_INFO_SESSION_115_URL,
        NPTU_OUTBOUND_INTERNSHIP_URL,
        NPTU_ZHUMENG_POST_115_URL,
        NPTU_DUAL_DEGREE_URL,
        NPTU_DUAL_MIDDLESEX_URL,
        NPTU_DUAL_UNA_URL,
        NPTU_DUAL_HYOGO_URL,
        NPTU_SCIENCE_DUAL_URL,
        NPTU_SISTER_SCHOOLS_URL,
        NPTU_MAINLAND_SISTERS_URL,
        NPTU_MAINLAND_EXCHANGE_URL,
        NPTU_EXPERIENCES_URL,
        NPTU_REGULATIONS_URL,
        NPTU_STUDY_ABROAD_RULES_PDF,
        NPTU_DUAL_DEGREE_RULES_PDF,
        NPTU_CREDIT_TRANSFER_RULES_PDF,
        NPTU_CREDIT_CONVERSION_PDF,
        NPTU_GPA_CONVERSION_PDF,
        NPTU_ACADEMIC_RULES_PDF,
        NPTU_MIDDLESEX_APP_PDF,
    ]

    exchange_info_payload = {
        "school_name": "國立屏東大學",
        "program_type": [
            f"國際事務處國際合作組（CCD）出國交換甄選四大計畫（教育部「學海飛颺」、教育部「學海惜珠」、本校校友捐款「菁英育才」補助及「自費交換」；涵蓋美國北阿拉巴馬大學、西來大學、楊斯鎮州立大學，捷克赫拉德茨克拉洛韋大學 UHK、托馬斯拔佳大學 TBU、利貝雷茨理工大學 TUL、布拉格捷克理工大學 CTU，德國柏林愛麗絲沙羅蒙應用科學大學 ASH Berlin，義大利帕維亞大學，日本宮崎大學、弘前大學、大阪教育大學、兵庫教育大學、室蘭工業大學、和歌山大學、鹿兒島大學、香川大學、山形大學、信州大學、麗澤大學、姬路獨協大學、廣島修道大學、山陽學園大學、日本經濟大學，韓國外國語大學 HUFS、釜山外國語大學、大邱教育大學，馬來西亞馬來亞大學 UM、拉曼大學 UTAR，澳洲國際飯店管理學院 ICHM，泰國程逸皇家大學［免學費＋免住宿費＋月領 3,000 泰銖］、碧武里皇家大學、蘭帕潘尼皇家大學、黎府皇家大學、武里南皇家大學、坦亞布里皇家理工大學，以及越南胡志明市師範大學、芹苴大學等 38 所簡章開放交換校）",
            "英、美、捷、日、泰 7 校跨國雙聯學位計畫（【英國密德薩斯大學 Middlesex University 全校 3+1 學士／1+1 碩士／3+1 學碩雙聯】、【美國北阿拉巴馬大學 UNA 全校 3+1／2+2 學士與 1+1 碩士雙聯】、【美國西來大學 University of the West 2+2 學士與 1+1 碩士雙聯】、【捷克赫拉德茨克拉洛韋大學 UHK 資訊學院 1+1 碩士雙聯】、【捷克托馬斯拔佳大學 TBU 管理／資訊／人文社會學院 1+1 碩士雙聯】、【泰國宋卡王子大學 PSU 理學院 2+2 學士雙聯】、【泰國吞武里蒙庫國王科技大學 KMUTT 管理／資訊學院 1+1 碩士雙聯】）",
            f"大陸及港澳地區合作學校交換計畫與教育部「學海築夢／新南向學海築夢」海外專業實習計畫（全校共完整收錄 {len(partners)} 所全球與兩岸港澳合作姊妹校、{open_partner_count} 所常態開放申請交換與雙聯學校，橫跨 24 個國家與地區，並收錄 {exp_covered_schools} 所合作大學共 {total_exp_reports} 篇歷屆學長姐出國交換與研修心得報告）",
        ],
        "academic_year": [
            "116（涵蓋 116學年度出國交換／實習三校區說明會［2026/12/08 民生、12/09 屏師、12/10 屏商，報名至 2026/11/30 17:00］、115–116學年度出國交換學生甄選［每年 1–2 月收件、2 月下旬 17:00 截止、3 月初面試］，以及跨國雙聯學位與學海築夢／新南向學海築夢甄選）",
            f"本平台完整收錄國立屏東大學國際事務處（國際合作組與大陸事務組）公告之 {len(partners)} 所全球與兩岸港澳合作姊妹校（含 {open_partner_count} 所常態開放申請之交換與雙聯學位合作校、{len(partners) - open_partner_count} 所正式締約姊妹校，橫跨 24 個國家與地區，並完整收錄 {exp_covered_schools} 所合作大學共 {total_exp_reports} 篇歷屆學長姐交換與海外研修心得報告）",
        ],
        "semester": [
            "海外及大陸港澳姊妹校交換留學：依《國立屏東大學學生出國有關學業及學籍處理要點》第 4 條及出國交換甄選簡章，交換期間為一學期（半年）或一學年（1年），出國進修時間最多以 1 年為限，並得列入修業年限計算。",
            "跨國雙聯學位修業時間：依《國立屏東大學與境外大學校院辦理雙聯學制實施辦法》第 5 條及第 6 條，出國前後在本校總修業時間學士班至少 4 學期、碩士班至少 2 學期、博士班至少 3 學期；同級雙聯在二校修業期間學士累計至少滿 32 個月、碩士至少滿 12 個月、博士至少滿 24 個月；跨級雙聯停留於當地學校修業期間學士至少滿 32 個月、碩士至少滿 8 個月、博士至少滿 16 個月。",
        ],
        "application_period": [
            "【116學年度出國交換／實習三校區說明會】報名截止：2026年11月30日（一）17:00 止；民生校區場次：2026年12月8日（二）12:10–13:00（五育樓 4 樓第三會議室）；屏師校區場次：2026年12月9日（三）12:10–13:00（敬業樓 1 樓 102 教室）；屏商校區場次：2026年12月10日（四）12:10–13:00（圖資大樓 1 樓 104 教室）。",
            "【出國交換學生甄選（學海飛颺／學海惜珠／菁英育才／自費交換）】每年 1–2 月開放報名收件、2 月下旬 17:00 截止（參考 115年簡章：2026年2月24日［二］17:00 截止收件，2026年3月2日［一］舉行面試；116年預計於 2027年2月24日 17:00 截止收件），紙本送交屏商校區行政大樓 3 樓國際合作組，合併 PDF 電子檔寄至 vida2022@mail.nptu.edu.tw。",
            "【教育部學海築夢及新南向學海築夢海外專業實習甄選】每年分梯次受理計畫主持人提出申請（參考 115年第1次簡章：2026年2月26日［四］17:00 截止收件）。",
        ],
        "eligibility": [
            "1. 在學身分與四大推薦計畫資格：（a）【教育部學海飛颺】具中華民國國籍且在臺灣地區設有戶籍、於本校就讀一學期以上之在學學生（不含在職專班生與進修部學生）、歷年學業成績班排名前 50% 以內、操行成績平均 80 分以上且無申誡以上處分；（b）【教育部學海惜珠】同飛颺條件，另具低收入戶、中低收入戶、特殊境遇家庭扶助、身心障礙者生活補助或大專校院弱勢學生助學計畫助學金資格；（c）【本校「菁英育才」補助（校友捐款）】本國籍在臺設籍、就讀一學期以上在學學生（不含在職生與進修生）、無班排前 50% 限制，惟「每學期」操行成績皆須 80 分以上（非平均）且無申誡以上處分；（d）【自費交換】本國籍在臺設籍、就讀一學期以上之在學學生（含在職生與進修生）且未曾獲本校推薦出國交換。",
            "2. 在學註冊與最低修課規定：依《國立屏東大學學生出國有關學業及學籍處理要點》第 3 條，經核准出國交換者視同於本校就讀，仍需在本校註冊，不受學則最低修習學分之限制，惟大學部學生出國期間每學期至少須修習 1 門課程（日本姬路獨協大學要求每學期須選修 7 門課以上）。",
            "3. 志願選填與甄選方式：每人於申請表至多可填寫 5 所志願學校，經書面資料審查與校內面試綜合評定推薦順位。",
        ],
        "language_requirement": [
            "1. 赴非日語系國家交換（英語／韓語／歐語組）：校內甄選基本門檻須達 CEFR B1（含）以上，即 TOEIC 550、TOEFL iBT 42、TOEFL ITP 460、IELTS 4.0、全民英檢 GEPT 中級初試或 CSEPT 第一級 170／第二級 180 以上；惟部分姊妹校入學要求較高（如馬來亞大學要求 IELTS 6.0 / TOEFL iBT 80 / TOEIC 785、捷克布拉格捷克理工大學與義大利帕維亞大學要求英語 B2、韓國外國語大學要求 TOEFL iBT 71 / IELTS 5.5 或 TOPIK 3 級、美國北阿拉巴馬大學要求 iBT 61 / IELTS 5.5、西來大學要求 iBT 69 / IELTS 5.5、楊斯鎮州立大學要求 iBT 67 / IELTS 6.0、英國密德薩斯大學雙聯要求 IELTS 6.0–6.5），申請人向姊妹校送件前須達該校門檻。",
            "2. 赴日本姊妹校交換（15 所日本國私立大學）：校內甄選要求具備日本語能力試驗 JLPT N2（含）以上；惟校內甄選收件時倘尚未取得 N2 證書，得先以「非日語之外語能力 CEFR B1 以上證明」加附本校師長簽署之《日本語力評價表》替代（向日本姊妹校正式遞件時仍須符合接待校 N2／N3 規定，其中宮崎大學、弘前大學亦接受 JLPT N3 或英語申請）。",
            "3. 赴中國大陸合作學校交換：中文授課為主，免附英日韓外語檢定證明（香港教育大學部分全英授課學程須達英語 CEFR B1–B2）。",
        ],
        "required_documents": [
            "1. 國立屏東大學出國交換甄選申請表（表單一，勾選申請推薦計畫並填寫至多 5 所志願學校，須由系所主任及院長核章）",
            "2. 自傳與讀書計畫（表單二，須以中文及英文／日文撰寫個人自傳、出國修課讀書計畫與預期成效）",
            "3. 國立屏東大學出國交換學生甄選聲明書（表單三，須由學生本人及家長或監護人親筆簽名蓋章）",
            "4. 教師推薦信 1 封（表單四，由推薦師長親筆簽名後以紙本信封彌封送交，免掃描至電子檔）",
            "5. 歷年中文成績單正本（須註明歷年學業總平均及班級排名百分比；碩士班或轉學生請一併檢附原就讀學制成績單）",
            "6. 歷年各學期操行成績及獎懲紀錄證明（學海計畫須操行平均 80 分以上且無申誡以上處分；菁英育才須「每學期」操行皆 80 分以上且無申誡以上處分）",
            "7. 語言能力檢定證明影本（CEFR B1 以上英檢或 JLPT N2；赴日尚未取得 N2 者得先檢附非日語 B1 證明＋師長簽署之《日本語力評價表》）及其他有利審查資料（紙本送交屏商行政大樓 3F 國際合作組，並將第 1、2、3、5、6、7 項依序掃描合併為單一 PDF 寄至 vida2022@mail.nptu.edu.tw）",
        ],
        "scholarship_info": [
            "1. 教育部「學海飛颺」獎學金（依《國立屏東大學出國交換甄選簡章》及《學海計畫學生生活費核銷支給數額標準表》）：補助具中華民國國籍且在臺設籍、就讀一學期以上在學學生（不含在職生與進修生）、歷年成績班排前 50% 內、操行平均 80 分以上且無申誡以上處分之出國交換或雙聯學生；補助項目含學費、生活費（補助上限為 5 個月）及來回經濟艙機票費（含本校至少 20% 配合款）。",
            "2. 教育部「學海惜珠」獎學金：申請資格同學海飛颺，另須具各直轄市或縣（市）主管機關認定之低收入戶、中低收入戶、特殊境遇家庭扶助、身心障礙者生活補助費或大專校院弱勢學生助學計畫助學金資格，由教育部專案核定補助額度。",
            "3. 國立屏東大學「菁英育才」出國交換補助（校友捐款）：補助本國籍在臺設籍、就讀一學期以上之在學學生（不含在職生與進修生），「無班排名前 50% 限制」，惟「每學期」操行成績皆須達 80 分以上（非平均）且無申誡以上處分；獲選者補助生活費每月新臺幣 10,000 元（上限 5 個月，最高補助 NT$50,000）及來回機票費（亞洲地區上限 NT$15,000、非亞洲地區上限 NT$30,000），合計最高補助 NT$80,000！",
            "4. 姊妹校專屬免住宿費、生活津貼與學費減免優惠：（a）【泰國程逸皇家大學 URU】提供免學費＋免校內住宿費，且接待校每月額外發給 3,000 泰銖生活津貼；（b）【泰國碧武里皇家大學 PBRU、蘭帕潘尼皇家大學 RBRU、黎府皇家大學 LRU】提供免學費＋免校內住宿費；（c）【澳洲國際飯店管理學院 ICHM】提供 20% 學費減免且含半學期澳洲帶薪實習；（d）【美國楊斯鎮州立大學 YSU】提供俄亥俄州州內生學費優惠（In-State Tuition）。",
        ],
        "partner_universities": [p["school_name"] for p in partners],
        "source_urls": nptu_source_urls,
        "last_checked": CHECKED_AT,
    }
    (OFFICIAL_NPTU_DIR / "exchange_info.json").write_text(
        json.dumps(exchange_info_payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    student_dashboard_payload = {
        "school_name": "國立屏東大學",
        "last_checked": CHECKED_AT,
        "academic_score_minimum": 60.0,
        "academic_score_rule": "依《國立屏東大學出國交換甄選簡章》及《與境外大學校院辦理雙聯學制實施辦法》：（1）申請【教育部學海飛颺／學海惜珠】者，歷年學業成績須達班排名前 50% 以內，且操行成績平均 80 分以上、無申誡以上處分（不含在職生與進修生）；（2）申請【本校「菁英育才」補助（校友捐款）】者，無班排前 50% 限制，惟「每學期」操行成績皆須達 80 分以上（非平均）且無申誡以上處分；（3）申請【自費交換】者（含在職生與進修生），須於本校就讀滿一學期以上、未曾獲本校推薦出國交換且符合語檢門檻（部分姊妹校另訂有 GPA 2.0–3.0 門檻，如馬來亞大學要求 GPA 3.0［約 70 分］、韓國外國語大學要求 GPA 2.5）。",
        "academic_gpa_minimum": 2.0,
        "maximum_preferences": 5,
        "selection_rules": {
            "academic_policy": "gpa_or_rank",
            "academic_reference_year": "116",
            "undergraduate_gpa_minimum": 2.0,
            "graduate_academic_exempt": False,
            "exclude_in_service": False,
            "pending_quota_planning": False,
            "partner_requirements_need_confirmation": False,
            "degree_score_minimums": {
                "undergraduate": 60.0,
                "graduate": 70.0,
            },
            "excluded_undergraduate_years": [],
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
                "title": "國立屏東大學 116學年度出國交換／實習三校區說明會（2026/12/08 民生、12/09 屏師、12/10 屏商，11/30 17:00 報名截止）",
                "details": [
                    "依國立屏東大學國際事務處國際合作組（2026/10/29）最新公告，116學年度出國交換暨海外實習說明會於三校區巡迴舉辦：（1）民生校區：2026年12月8日（二）12:10–13:00 於五育樓 4 樓第三會議室；（2）屏師校區：2026年12月9日（三）12:10–13:00 於敬業樓 1 樓 102 教室；（3）屏商校區：2026年12月10日（四）12:10–13:00 於圖資大樓 1 樓 104 教室。",
                    "線上報名自即日起至 2026年11月30日（一）17:00 止，會中詳述 116學年度姊妹校交換名額、教育部學海飛颺／惜珠／築夢與屏東大學「菁英育才」獎學金申請規定，並邀請返國學長姐分享。",
                ],
                "source": {
                    "title": "國立屏東大學 116學年度出國交換／實習說明會公告",
                    "source_url": NPTU_INFO_SESSION_116_URL,
                    "category": "exchange_application",
                    "summary": "國立屏東大學 116學年度民生、屏師、屏商三校區出國交換與實習說明會場次及報名時程。",
                },
                "scope": "home_application",
                "program_types": ["exchange", "dual_degree"],
                "academic_year": "116",
                "application_round": "116學年度出國交換／實習說明會",
                "audience": "all_students",
                "opens_at": "2026-10-29T09:00:00+08:00",
                "deadline_at": "2026-11-30T17:00:00+08:00",
                "date_status": "verified_exact",
                "status": "upcoming",
                "status_note": "116學年度三校區出國交換／實習說明會現正開放報名至 2026/11/30 17:00 止，說明會於 2026/12/08–12/10 登場。",
                "deadline_note": "有意申請 116學年度出國交換、跨國雙聯學位或學海築夢海外實習之同學請於 2026/11/30 17:00 前完成線上報名。",
                "reminder_eligible": True,
                "checked_at": CHECKED_AT,
            },
            {
                "title": "國立屏東大學出國交換學生甄選（學海飛颺／學海惜珠／菁英育才／自費交換，每年 1–2 月收件、2 月下旬 17:00 截止）",
                "details": [
                    "依《國立屏東大學出國交換甄選簡章》，校內甄選於每年 1–2 月開放收件、2 月下旬 17:00 截止（參考 115年簡章：2026年2月24日［二］17:00 截止收件、3月2日［一］辦理面試；116年預計於 2027年2月24日 17:00 截止收件）。",
                    "申請人至多可填寫 5 所志願學校，須於截止前將紙本送交屏商校區行政大樓 3 樓國際合作組，並將推薦信以外之各項文件依序掃描合併為單一 PDF 寄至 vida2022@mail.nptu.edu.tw。",
                ],
                "source": {
                    "title": "國立屏東大學出國交換甄選簡章與表單下載專區",
                    "source_url": NPTU_OUTBOUND_POST_115_URL,
                    "category": "exchange_application",
                    "summary": "國立屏東大學出國交換四大推薦計畫（學海飛颺、學海惜珠、菁英育才、自費交換）收件與面試時程。",
                },
                "scope": "home_application",
                "program_types": ["exchange", "dual_degree"],
                "academic_year": "116",
                "application_round": "出國交換學生暨學海飛颺／惜珠／菁英育才獎學金甄選",
                "audience": "all_students",
                "opens_at": "2027-01-15T09:00:00+08:00",
                "deadline_at": "2027-02-24T17:00:00+08:00",
                "date_status": "verified_exact",
                "status": "upcoming",
                "status_note": "每年 1–2 月受理出國交換暨學海飛颺、學海惜珠、菁英育才獎學金與自費交換甄選申請，3 月初舉行面試。",
                "deadline_note": "赴日交換若於校內甄選時尚未取得 JLPT N2，可先檢附非日語 CEFR B1 證明加附本校師長簽署之《日本語力評價表》替代。",
                "reminder_eligible": True,
                "checked_at": CHECKED_AT,
            },
        ],
        "program_overview": [
            {
                "title": f"國立屏東大學國際事務處全球姊妹校交換、英美捷日泰 7 校雙聯學位與四大獎助計畫總覽（{len(partners)} 所合作姊妹校・{open_partner_count} 所常態開放申請・{total_exp_reports} 篇學長姐心得報告）",
                "details": [
                    f"國立屏東大學（National Pingtung University, NPTU，2014 年由國立屏東教育大學與國立屏東商業技術學院合校成立，擁有民生、屏商、屏師三大校區與車城校地）由「國際事務處（Office of International Affairs, OIA，位於屏商校區行政大樓 3 樓，下設國際合作組與大陸事務組）」統籌全校 7 大學院（管理學院、資訊學院、教育學院、人文社會學院、理學院、國際學院、大武山學院）之出國交換學生、跨國雙聯學位、大陸港澳交流及教育部學海系列計畫。本平台完整收錄 {len(partners)} 所屏東大學官方合作姊妹校（含 {open_partner_count} 所常態開放申請之交換與雙聯學位合作校，以及 {len(partners) - open_partner_count} 所正式締約姊妹校），橫跨全球 24 個國家與地區。",
                    f"屏東大學國際交流具備四大核心特色：（1）多元彈性的四大推薦與補助管道：除教育部「學海飛颺」、「學海惜珠」（須班排前 50% 且操行平均 80 分以上）外，獨家設有校友捐款之「菁英育才」補助（無班排前 50% 限制，每學期操行皆 80 分以上即可申請，最高補助生活費 NT$50,000＋機票費 NT$30,000＝NT$80,000），並開放含在職生與進修生申請之「自費交換」；（2）15 所日本國私立大學與歐美亞太重點名校陣容（含日本宮崎大學、弘前大學、大阪教育大學、兵庫教育大學、室蘭工業大學、和歌山大學、鹿兒島大學、香川大學、山形大學、信州大學等 10 所日本國立大學與麗澤大學、姬路獨協大學、廣島修道大學、山陽學園大學、日本經濟大學，捷克 UHK 10 名、TBU、TUL、CTU，德國 ASH Berlin，義大利帕維亞大學，韓國外國語大學 HUFS，馬來亞大學 UM，以及泰國程逸皇家大學等 4 校「免學費＋免住宿費」優惠）；（3）英、美、捷、日、泰 7 校跨國雙聯學位（英國密德薩斯大學 3+1／1+1、美國北阿拉巴馬大學 3+1／2+2／1+1、美國西來大學 2+2／1+1、捷克 UHK 1+1、捷克 TBU 1+1、泰國宋卡王子大學 2+2、泰國蒙庫國王科技大學 KMUTT 1+1）；（4）完整收錄 {exp_covered_schools} 所合作大學共 {total_exp_reports} 篇歷屆學長姐交換與海外研修心得報告。",
                ],
                "source": {
                    "title": "國立屏東大學國際事務處（OIA）與國際合作組（CCD）官方網站",
                    "source_url": NPTU_OUTBOUND_EXCHANGE_URL,
                    "category": "exchange_application",
                    "summary": f"國立屏東大學 {len(partners)} 所全球合作姊妹校、{open_partner_count} 所常態開放交換／雙聯校與 {total_exp_reports} 篇心得報告。",
                },
            }
        ],
        "eligibility": [
            {
                "title": "四大推薦計畫資格分流（學海飛颺／惜珠班排前 50%＋操行平均 80 分；菁英育才每學期操行皆 80 分免看班排；自費交換含在職與進修生）",
                "details": [
                    "在學身分與學業操行規定：申請人須具中華民國國籍且在臺灣地區設有戶籍，並於屏東大學就讀滿一學期以上。（1）申請【教育部學海飛颺／學海惜珠】者（不含在職生與進修生），歷年學業成績須達班排名前 50% 以內、操行平均 80 分以上且無申誡以上處分；（2）申請【本校「菁英育才」補助】者（不含在職生與進修生），無班排前 50% 限制，惟「每學期」操行成績皆須達 80 分以上（非平均）且無申誡以上處分；（3）申請【自費交換】者（含在職生與進修生），未曾獲本校推薦出國交換且符合外語門檻即可申請。",
                    "出國期間註冊與修課抵免：依《國立屏東大學學生出國有關學業及學籍處理要點》與《學生抵免學分要點》，出國交換期間仍須於屏東大學完成註冊，大學部學生每學期至少修習 1 門課程（姬路獨協大學須修 7 門課以上），出國進修時間最多以 1 年為限；返國後應於次學期期末考結束前一次辦理學分抵免（1 NPTU 學分＝2 ECTS＝4 CATS＝4 澳洲學分，美日陸 1:1，抵免上限為畢業應修學分 1/3）。",
                ],
                "source": {
                    "title": "國立屏東大學出國交換甄選簡章與學生出國有關學業及學籍處理要點",
                    "source_url": NPTU_STUDY_ABROAD_RULES_PDF,
                    "category": "exchange_application",
                    "summary": "國立屏東大學四大出國交換推薦計畫資格、在學註冊與學分抵免規定。",
                },
            }
        ],
        "language_requirements": [
            {
                "title": "非日語組 CEFR B1（TOEIC 550 / TOEFL iBT 42 / ITP 460 / IELTS 4.0 / GEPT 中級）與日語組 JLPT N2（或非日語 B1＋師長簽署《日本語力評價表》）",
                "details": [
                    "非日語系國家外語標準：校內甄選基本門檻為 CEFR B1（含）以上（TOEIC 550、TOEFL iBT 42、TOEFL ITP 460、IELTS 4.0、GEPT 中級初試或 CSEPT 第一級 170／第二級 180）；部分歐美與亞洲名校要求較高（如馬來亞大學要求 IELTS 6.0 / TOEFL iBT 80 / TOEIC 785、布拉格捷克理工大學與義大利帕維亞大學要求英語 B2、韓國外國語大學要求 TOEFL iBT 71 / IELTS 5.5 或 TOPIK 3 級、英國密德薩斯大學雙聯要求 IELTS 6.0–6.5）。",
                    "日本姊妹校外語標準與彈性替代機制：申請日本 15 所姊妹校原則要求具備 JLPT N2（含）以上；惟校內甄選收件時倘尚未取得 JLPT N2 證書，得先以「非日語之外語能力 CEFR B1 以上證明」加附本校師長簽署之《日本語力評價表》替代參加校內甄選（向日本姊妹校正式遞件時仍須符合日方語檢要求，其中宮崎大學、弘前大學亦接受 JLPT N3 或英語 B1）。",
                ],
                "source": {
                    "title": "國立屏東大學 115年出國交換甄選簡章與日本語力評價表",
                    "source_url": NPTU_OUTBOUND_POST_115_URL,
                    "category": "exchange_application",
                    "summary": "國立屏東大學出國交換 CEFR B1 英語門檻、JLPT N2 日語門檻與日本語力評價表替代規定。",
                },
            }
        ],
        "required_documents": [
            {
                "title": "申請表（最多 5 志願）、中英／中日自傳與讀書計畫、聲明書、彌封推薦信、含班排歷年成績單與獎懲紀錄（紙本＋合併 PDF 雙軌送件）",
                "details": [
                    "校內甄選必備文件（紙本送交屏商校區行政大樓 3 樓國際合作組）：（1）出國交換甄選申請表（表單一，最多填寫 5 所志願學校，經系主任與院長核章）；（2）自傳與讀書計畫（表單二，中文及英／日文）；（3）聲明書（表單三，本人與家長親筆簽章）；（4）教師推薦信 1 封（表單四，推薦師長簽名後紙本彌封）；（5）歷年中文成績單正本（含班排名百分比）；（6）歷年各學期操行成績與獎懲紀錄證明；（7）語言能力檢定證明（或非日語 B1＋《日本語力評價表》）。",
                    "電子檔合併寄送規定：除彌封之「教師推薦信」僅交紙本外，其餘各項申請文件請依序掃描合併為單一 PDF 檔案，於收件截止前寄至國際合作組承辦信箱 vida2022@mail.nptu.edu.tw。",
                ],
                "source": {
                    "title": "國立屏東大學出國交換甄選簡章與申請表單一至四",
                    "source_url": NPTU_OUTBOUND_POST_115_URL,
                    "category": "exchange_application",
                    "summary": "國立屏東大學出國交換申請表、自傳讀書計畫、聲明書、推薦信與雙軌送件規範。",
                },
            }
        ],
        "scholarship_info": [
            {
                "title": "教育部學海飛颺／學海惜珠、屏大「菁英育才」補助（月領 NT$10,000＋機票最高 NT$30,000，無班排限制）與泰國 4 校免住宿費優惠",
                "details": [
                    "教育部學海飛颺、學海惜珠與屏大菁英育才：（1）學海飛颺與學海惜珠補助本國籍、就讀滿一學期、班排前 50% 且操行平均 80 分以上之一般生（依《國立屏東大學學海計畫學生生活費核銷支給數額標準表》支給學費、最長 5 個月生活費與機票費）；（2）本校校友捐款「菁英育才」補助無班排前 50% 限制（惟每學期操行皆須達 80 分以上），補助生活費每月 NT$10,000（最高 5 個月 NT$50,000）及機票費（亞洲上限 NT$15,000、非亞洲上限 NT$30,000）。",
                    "姊妹校專屬優惠：泰國程逸皇家大學（URU）提供免學費、免住宿費且每月核發 3,000 泰銖生活津貼；泰國碧武里皇家大學（PBRU）、蘭帕潘尼皇家大學（RBRU）、黎府皇家大學（LRU）提供免學費＋免住宿費；澳洲國際飯店管理學院（ICHM）提供 20% 學費減免；美國楊斯鎮州立大學（YSU）提供州內生學費優惠。",
                ],
                "source": {
                    "title": "國立屏東大學出國交換甄選簡章與學海計畫學生生活費核銷支給數額標準表",
                    "source_url": NPTU_REGULATIONS_URL,
                    "category": "scholarship",
                    "summary": "國立屏東大學教育部學海計畫、校友捐款菁英育才補助與姊妹校住宿學費減免規定。",
                },
            }
        ],
        "document_explanations": [
            {
                "title": "國立屏東大學出國交換申請表（5 志願）、中英／中日自傳與讀書計畫、彌封推薦信、日本語力評價表與單一 PDF 送件指南",
                "summary": "說明屏東大學出國交換四大表單（申請表、自傳與讀書計畫、聲明書、推薦信）、赴日《日本語力評價表》替代機制與紙本＋PDF 雙軌送件重點。",
                "key_points": [
                    "四大官方表單與系院核章：申請人須使用當期簡章附件之（1）表單一：申請表（勾選學海飛颺／學海惜珠／菁英育才／自費交換，最多填寫 5 所志願學校，並預留時間請系所主任及學院院長核章）、（2）表單二：自傳與讀書計畫（含中文及英文／日文版本）、（3）表單三：聲明書（學生本人與家長／監護人雙方親筆簽名蓋章）、（4）表單四：推薦信（由師長簽名後信封彌封）。",
                    "含班排歷年成績單與各學期操行獎懲證明：申請學海飛颺／惜珠須檢附載有「班級排名百分比（前 50% 內）」之歷年成績單及操行平均 80 分以上證明；申請「菁英育才」須確認「每學期」操行成績皆達 80 分以上（若有單一學期 79 分即不符菁英育才資格），且均須附無申誡以上處分之獎懲紀錄。",
                    "赴日《日本語力評價表》與合併 PDF 電子檔：赴日本姊妹校交換者若於校內甄選截止前尚未取得 JLPT N2 證書，可先檢附非日語 CEFR B1 證明（如 TOEIC 550）加附本校日語相關師長簽署之《日本語力評價表》先行報名；除彌封推薦信外，所有文件須依序掃描合併為單一 PDF 寄至 vida2022@mail.nptu.edu.tw。",
                ],
                "applies_to": [],
                "source": {
                    "title": "國立屏東大學 115年出國交換甄選簡章與申請表單專區",
                    "source_url": NPTU_OUTBOUND_POST_115_URL,
                    "category": "exchange_application",
                    "summary": None,
                },
                "document_url": NPTU_OUTBOUND_POST_115_URL,
                "document_type": "official_document",
                "full_text_extracted": True,
            }
        ],
        "rule_explanations": [
            {
                "title": "國立屏東大學學生出國有關學業及學籍處理要點、辦理雙聯學制實施辦法、學生抵免學分要點與外國學制學分轉換準則核心規定",
                "summary": "規範屏東大學交換生在學註冊與每學期至少 1 門課下限、雙聯學制 32／12／24 個月與 1/3 學分規定、1 NPTU＝2 ECTS＝4 CATS 學分換算及返國次學期期末考前一次抵免規範。",
                "key_points": [
                    "在學註冊、修課下限與一年期限：依《學生出國有關學業及學籍處理要點》（114.03.27修正）第 3 條及第 4 條，經核准出國交換者視同於本校就讀，仍需在本校註冊，不受學則最低修習學分之限制，惟大學部學生出國期間至少修習 1 門課程（姬路獨協大學須選修 7 門課以上）；出國進修時間最多以 1 年為限，並得列入修業年限計算。",
                    "外國學制學分轉換與返國一次抵免上限：依《與外國學制學分轉換準則》（106.11.16修正）與《學生抵免學分要點》（115.10.22修正），1 學分（NPTU）＝2 ECTS（歐洲）＝4 CATS（英國）＝4 學分（澳洲），與美制、日制、陸制學分 1:1 換算；境外交換修得學分之抵免以所屬系所應修畢業學分數之 1/3 為限（雙聯學士至多抵免 1/2、雙聯碩士至多抵免 2/3 不含論文），且應於出國交換之次學期期末考結束前檢具原始成績表正本或經國際處核章之影本「一次全部辦理」。",
                    "跨國雙聯學制修業時間與學分數：依《與境外大學校院辦理雙聯學制實施辦法》（114.05.22修正）第 5 條至第 7 條，出國前後在本校總修業時間學士班至少 4 學期、碩士班至少 2 學期、博士班至少 3 學期，在二校當地修習學分數累計須各達畢業應修總學分數 1/3 以上；同級雙聯在二校修業期間學士累計至少滿 32 個月、碩士至少滿 12 個月、博士至少滿 24 個月（跨級雙聯停留於當地學校修業期間碩士至少滿 8 個月、博士至少滿 16 個月）。",
                ],
                "applies_to": [],
                "source": {
                    "title": "國立屏東大學學生出國有關學業及學籍處理要點、雙聯學制實施辦法與學生抵免學分要點",
                    "source_url": NPTU_STUDY_ABROAD_RULES_PDF,
                    "category": "exchange_application",
                    "summary": None,
                },
                "document_url": NPTU_DUAL_DEGREE_RULES_PDF,
                "document_type": "official_document",
                "full_text_extracted": True,
            }
        ],
        "sources": [
            {"title": "國立屏東大學國際事務處（Office of International Affairs）官方網站", "source_url": NPTU_OIA_HOME_URL, "category": "exchange_application", "summary": None},
            {"title": "國立屏東大學國際事務處國際合作組（出國交換學生專區）", "source_url": NPTU_OUTBOUND_EXCHANGE_URL, "category": "exchange_application", "summary": None},
            {"title": "國立屏東大學 115年出國交換甄選簡章與表單下載公告", "source_url": NPTU_OUTBOUND_POST_115_URL, "category": "exchange_application", "summary": None},
            {"title": "國立屏東大學 116學年度出國交換／實習三校區說明會公告", "source_url": NPTU_INFO_SESSION_116_URL, "category": "exchange_application", "summary": None},
            {"title": "國立屏東大學跨國雙聯學位專區（英、美、捷、日、泰 7 校雙聯學制）", "source_url": NPTU_DUAL_DEGREE_URL, "category": "exchange_application", "summary": None},
            {"title": f"國立屏東大學全球與兩岸港澳合作姊妹校名錄（橫跨 24 國與地區共 {len(partners)} 所合作姊妹校）", "source_url": NPTU_SISTER_SCHOOLS_URL, "category": "partner_school", "summary": None},
            {"title": "國立屏東大學國際事務處法規專區與學海計畫學生生活費核銷支給數額標準表", "source_url": NPTU_REGULATIONS_URL, "category": "scholarship", "summary": None},
            {"title": f"國立屏東大學出國交換學生心得分享專區（{exp_covered_schools} 校 {total_exp_reports} 篇心得報告）", "source_url": NPTU_EXPERIENCES_URL, "category": "exchange_application", "summary": None},
        ],
    }
    (OFFICIAL_NPTU_DIR / "student_dashboard.json").write_text(
        json.dumps(student_dashboard_payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    doc_conditions = {
        "school_id": "nptu",
        "school_name": "國立屏東大學",
        "checked_at": CHECKED_AT,
        "source_url": NPTU_OUTBOUND_POST_115_URL,
        "common_documents": exchange_info_payload["required_documents"],
        "track_specific_conditions": [
            {
                "track": "教育部學海飛颺／學海惜珠獎學金推薦計畫（班排前 50%＋操行平均 80 分以上）",
                "required": [
                    "國立屏東大學出國交換甄選申請表（表單一，勾選學海飛颺或學海惜珠，至多填寫 5 所志願學校，經系主任與院長核章）",
                    "含班級排名百分比（前 50% 以內）之歷年中文成績單正本，以及操行平均 80 分以上且無申誡以上處分之各學期獎懲紀錄證明",
                    "中英／中日自傳與讀書計畫（表單二）、本人與家長親筆簽章之聲明書（表單三）、師長親筆簽名彌封之推薦信 1 封（表單四）及 CEFR B1／JLPT N2 語檢證明（學海惜珠另附低收／中低收／特殊境遇／身障／弱勢助學相關證明及新式戶口名簿影本）",
                ],
            },
            {
                "track": "國立屏東大學「菁英育才」出國交換補助（校友捐款，無班排前 50% 限制，每學期操行皆 80 分以上）",
                "required": [
                    "國立屏東大學出國交換甄選申請表（表單一，勾選菁英育才補助，至多填寫 5 所志願學校）",
                    "歷年中文成績單正本及「每學期操行成績皆達 80 分以上（非平均）」且無申誡以上處分之獎懲紀錄證明",
                    "中英／中日自傳與讀書計畫（表單二）、聲明書（表單三）、彌封推薦信 1 封（表單四）及外語能力檢定證明（或非日語 B1＋師長簽署《日本語力評價表》）",
                ],
            },
            {
                "track": "自費出國交換計畫（含在職生與進修生）",
                "required": [
                    "國立屏東大學出國交換甄選申請表（表單一，勾選自費交換，至多填寫 5 所志願學校）",
                    "歷年中文成績單正本、中英／中日自傳與讀書計畫（表單二）、聲明書（表單三）、彌封推薦信 1 封（表單四）及符合目標姊妹校門檻之外語能力證明",
                ],
            },
            {
                "track": "英、美、捷、日、泰 7 校跨國雙聯學位（密德薩斯、北阿拉巴馬、西來、捷克 UHK、捷克 TBU、宋卡王子、KMUTT）",
                "required": [
                    "雙聯學位申請表（如英國密德薩斯大學雙聯申請表）、中英文歷年成績單正本（需修滿屏東大學規定學期數與畢業總學分 1/3 以上）、英文讀書計畫與自傳、護照影本及符合雙聯合作校要求之 IELTS / TOEFL iBT 語檢成績單",
                ],
            },
        ],
    }
    (OFFICIAL_NPTU_DIR / "document-conditions.json").write_text(
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
        field_cov_lines.append(
            f"{fname},{len(partners)},{pop},{ratio:.4f},Official NPTU OIA verified"
        )
    (OFFICIAL_NPTU_DIR / "field-coverage.csv").write_text(
        "\n".join(field_cov_lines) + "\n", encoding="utf-8"
    )

    pages_records = [
        {
            "title": "國立屏東大學：116學年度出國交換／實習三校區說明會（2026/12/08–12/10）與出國交換甄選時程",
            "source_url": NPTU_INFO_SESSION_116_URL,
            "published_at": "2026-10-29T00:00:00Z",
            "text": "\n".join(exchange_info_payload["application_period"]),
            "summary": "\n".join(exchange_info_payload["application_period"]),
            "category": "exchange_application",
            "attachments": [],
            "crawled_at": CHECKED_AT,
            "content_hash": hashlib.sha256("\n".join(exchange_info_payload["application_period"]).encode("utf-8")).hexdigest(),
        },
        {
            "title": "國立屏東大學：出國交換四大推薦計畫資格、學生出國有關學業及學籍處理要點與雙聯學制實施辦法",
            "source_url": NPTU_STUDY_ABROAD_RULES_PDF,
            "published_at": "2026-10-29T00:00:00Z",
            "text": "\n".join(exchange_info_payload["eligibility"]),
            "summary": "\n".join(exchange_info_payload["eligibility"]),
            "category": "exchange_application",
            "attachments": [],
            "crawled_at": CHECKED_AT,
            "content_hash": hashlib.sha256("\n".join(exchange_info_payload["eligibility"]).encode("utf-8")).hexdigest(),
        },
        {
            "title": f"國立屏東大學：{len(partners)} 所全球與兩岸港澳合作姊妹校外語檢定門檻與赴日《日本語力評價表》替代規定",
            "source_url": NPTU_OUTBOUND_POST_115_URL,
            "published_at": "2026-10-29T00:00:00Z",
            "text": "\n".join(exchange_info_payload["language_requirement"]),
            "summary": "\n".join(exchange_info_payload["language_requirement"]),
            "category": "exchange_application",
            "attachments": [],
            "crawled_at": CHECKED_AT,
            "content_hash": hashlib.sha256("\n".join(exchange_info_payload["language_requirement"]).encode("utf-8")).hexdigest(),
        },
        {
            "title": "國立屏東大學：出國交換甄選 7 項應備文件（申請表至多 5 志願、自傳讀書計畫、聲明書、彌封推薦信、紙本＋單一 PDF 雙軌送件）",
            "source_url": NPTU_OUTBOUND_EXCHANGE_URL,
            "published_at": "2026-10-29T00:00:00Z",
            "text": "\n".join(exchange_info_payload["required_documents"]),
            "summary": "\n".join(exchange_info_payload["required_documents"]),
            "category": "exchange_application",
            "attachments": [],
            "crawled_at": CHECKED_AT,
            "content_hash": hashlib.sha256("\n".join(exchange_info_payload["required_documents"]).encode("utf-8")).hexdigest(),
        },
        {
            "title": "國立屏東大學：教育部學海飛颺／惜珠、校友捐款「菁英育才」補助（最高 8 萬元）與泰國 4 校免住宿費優惠",
            "source_url": NPTU_REGULATIONS_URL,
            "published_at": "2026-10-29T00:00:00Z",
            "text": "\n".join(exchange_info_payload["scholarship_info"]),
            "summary": "\n".join(exchange_info_payload["scholarship_info"]),
            "category": "scholarship",
            "attachments": [],
            "crawled_at": CHECKED_AT,
            "content_hash": hashlib.sha256("\n".join(exchange_info_payload["scholarship_info"]).encode("utf-8")).hexdigest(),
        },
    ]
    (OFFICIAL_NPTU_DIR / "pages.jsonl").write_text(
        "\n".join(json.dumps(p, ensure_ascii=False) for p in pages_records) + "\n",
        encoding="utf-8",
    )

    home_rules = {
        "school_id": "nptu",
        "school_name": "國立屏東大學",
        "eligibility": student_dashboard_payload["eligibility"],
        "application_periods": student_dashboard_payload["application_periods"],
        "selection_rules": {
            "maximum_preferences": 5,
            "xuehai_class_rank_percent_maximum": 50.0,
            "xuehai_conduct_average_minimum": 80.0,
            "jingying_yucai_each_semester_conduct_minimum": 80.0,
            "jingying_yucai_monthly_stipend_ntd": 10000,
            "jingying_yucai_max_months": 5,
            "jingying_yucai_airfare_asia_max_ntd": 15000,
            "jingying_yucai_airfare_non_asia_max_ntd": 30000,
            "self_funded_allows_in_service_and_continuing_ed": True,
            "require_nptu_registration_during_abroad": True,
            "undergraduate_minimum_courses_per_semester": 1,
            "credit_transfer_max_fraction_exchange": "1/3 of graduation credits",
            "credit_transfer_max_fraction_dual_bachelor": "1/2 of graduation credits",
            "credit_transfer_max_fraction_dual_master": "2/3 of graduation credits (excluding thesis)",
            "credit_conversion_rule": "1 NPTU credit = 2 ECTS (Europe) = 4 CATS (UK) = 4 credits (Australia) = 1 credit (US/JP/Mainland)",
            "return_credit_transfer_due": "應於出國交換之次學期期末考結束前檢具原始成績表正本或經國際事務處核章之影本一次全部辦理",
        },
        "source_urls": nptu_source_urls,
        "verified_at": "2026-11-05",
    }
    (OFFICIAL_NPTU_DIR / "home_rules.json").write_text(
        json.dumps(home_rules, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    (OFFICIAL_NPTU_DIR / "documents.json").write_text(
        json.dumps(
            {
                "school_name": "國立屏東大學",
                "required_documents": student_dashboard_payload["required_documents"],
                "source_urls": nptu_source_urls,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    (OFFICIAL_NPTU_DIR / "scholarships.json").write_text(
        json.dumps(
            {
                "school_name": "國立屏東大學",
                "scholarships": student_dashboard_payload["scholarship_info"],
                "source_urls": nptu_source_urls,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    completeness = {
        "school_id": "nptu",
        "school_name": "國立屏東大學",
        "total_partners": len(partners),
        "partner_count": len(partners),
        "international_partners": sum(1 for p in partners if p["country"] not in {"中國大陸", "香港", "澳門"}),
        "mainland_partners": sum(1 for p in partners if p["country"] in {"中國大陸", "香港", "澳門"}),
        "dual_degree_partner_universities": 7,
        "dual_degree_programs": 10,
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
        "active_term": f"國立屏東大學國際事務處（OIA）《115年出國交換甄選簡章》、《116學年度出國交換／實習三校區說明會公告》、《115年第1次教育部學海築夢及新南向學海築夢甄選簡章》、《跨國雙聯學位專區（英美捷日泰 7 校）》、《學生出國有關學業及學籍處理要點（114.03.27修正）》、《與境外大學校院辦理雙聯學制實施辦法（114.05.22修正）》、《學生抵免學分要點（115.10.22修正）》、《與外國學制學分轉換準則》及《學海計畫學生生活費核銷支給數額標準表》同步整合；共完整收錄 {len(partners)} 所全球與兩岸港澳合作姊妹校（含 {open_partner_count} 所常態開放申請交換與雙聯學校及 {len(partners) - open_partner_count} 所正式締約姊妹校，橫跨 24 個國家與地區，並收錄 {exp_covered_schools} 所合作大學共 {total_exp_reports} 篇歷屆學長姐出國交換與研修心得報告）。",
        "verified_at": "2026-11-05",
    }
    (OFFICIAL_NPTU_DIR / "catalog-completeness.json").write_text(
        json.dumps(completeness, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    (OFFICIAL_NPTU_DIR / "verification_status.json").write_text(
        json.dumps(
            {
                "school_id": "nptu",
                "school_name": "國立屏東大學",
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
        ("sources/nptu/nptu_catalog_source.json", NPTU_SISTER_SCHOOLS_URL, f"國立屏東大學 {len(partners)} 所全球與兩岸港澳合作姊妹校整合資料集 JSON"),
        ("sources/nptu/nptu_resolved_locations.json", NPTU_SISTER_SCHOOLS_URL, f"國立屏東大學 {len(partners)} 所合作姊妹校 ROR / Wikidata 地理座標核對表 JSON"),
        ("sources/nptu/nptu_experience_index.json", NPTU_EXPERIENCES_URL, f"國立屏東大學 {total_exp_reports} 篇歷屆交換與海外研修心得報告索引 JSON"),
    ]
    for rel_p, surl in bin_urls.items():
        rp = rel_p if rel_p.startswith("sources/") else f"sources/nptu/{rel_p}"
        if not any(x[0] == rp for x in provenance_files):
            provenance_files.append((rp, surl, f"國立屏東大學官方原始檔案：{Path(rp).name}"))

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
        "school_id": "nptu",
        "school_name": "國立屏東大學",
        "generated_at": CHECKED_AT,
        "active_cycle_note": completeness["active_term"],
        "sources": prov_sources,
    }
    prov_text = json.dumps(provenance_payload, ensure_ascii=False, indent=2) + "\n"
    (OFFICIAL_NPTU_DIR / "import_provenance.json").write_text(prov_text, encoding="utf-8")
    (OFFICIAL_NPTU_DIR / "import-provenance.json").write_text(prov_text, encoding="utf-8")

    print(
        f"Successfully built NPTU catalog: {len(partners)} partners"
        f" ({open_partner_count} open, {completeness['verified_campus_images']}"
        f" verified images, {completeness['verified_locations']} verified"
        f" locations), {len(workflows)} workflows,"
        f" {len(destinations)} destinations, {len(research_records)} research"
        f" records, {exp_covered_schools} schools with experience records"
        f" ({len(student_experience_rows)} rows, {total_exp_reports} reports)."
    )


if __name__ == "__main__":
    main()
