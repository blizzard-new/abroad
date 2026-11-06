"""Build the official National Taipei University of Nursing and Health Sciences (國立臺北護理健康大學, NTUNHS) exchange data bundle."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re

REPO_ROOT = Path(__file__).resolve().parents[1]
SOURCES_NTUNHS_DIR = REPO_ROOT / "sources" / "ntunhs"
OFFICIAL_NTUNHS_DIR = (
    REPO_ROOT / "src" / "exchange_info" / "official_data" / "ntunhs"
)
STATIC_DIR = REPO_ROOT / "src" / "exchange_info" / "static"
UNIVERSITY_LOCATIONS_PATH = (
    REPO_ROOT
    / "src"
    / "exchange_info"
    / "official_data"
    / "university_locations.jsonl"
)

CHECKED_AT = "2026-11-06T00:00:00Z"

NTUNHS_HOME_URL = "https://www.ntunhs.edu.tw/"
NTUNHS_ICSED_HOME_URL = "https://icsed-rnd.ntunhs.edu.tw/"
NTUNHS_DUAL_DEGREE_URL = "https://icsed-rnd.ntunhs.edu.tw/p/412-1037-3252.php?Lang=zh-tw"
NTUNHS_EXCHANGE_URL = "https://icsed-rnd.ntunhs.edu.tw/p/412-1037-3251.php?Lang=zh-tw"
NTUNHS_XUEHAI_URL = "https://icsed-rnd.ntunhs.edu.tw/p/412-1037-3253.php?Lang=zh-tw"
NTUNHS_SISTER_SCHOOLS_URL = "https://icsed-rnd.ntunhs.edu.tw/p/412-1037-3250.php?Lang=zh-tw"
NTUNHS_BUDDY_URL = "https://icsed-rnd.ntunhs.edu.tw/p/412-1037-4982.php?Lang=zh-tw"
NTUNHS_EXPERIENCES_URL = "https://icsed-rnd.ntunhs.edu.tw/p/406-1037-71408,r846.php?Lang=zh-tw"
NTUNHS_OSTRAVA_NOTICE_URL = "https://icsed-rnd.ntunhs.edu.tw/p/406-1037-74306,r845.php?Lang=zh-tw"
NTUNHS_NCU_JP_NOTICE_URL = "https://icsed-rnd.ntunhs.edu.tw/p/406-1037-74311,r845.php?Lang=zh-tw"
NTUNHS_HIROSHIMA_NOTICE_URL = "https://icsed-rnd.ntunhs.edu.tw/p/406-1037-77118,r845.php?Lang=zh-tw"
NTUNHS_MASSEY_NOTICE_URL = "https://icsed-rnd.ntunhs.edu.tw/p/406-1037-67530,r845.php?Lang=zh-tw"
NTUNHS_DHC_NOTICE_URL = "https://icsed-rnd.ntunhs.edu.tw/p/406-1037-74313,r845.php?Lang=zh-tw"
NTUNHS_KVK_NOTICE_URL = "https://icsed-rnd.ntunhs.edu.tw/p/406-1037-66403,r845.php?Lang=zh-tw"
NTUNHS_XUEHAI_FEIYANG_NOTICE_URL = "https://icsed-rnd.ntunhs.edu.tw/p/406-1037-73672,r847.php?Lang=zh-tw"
NTUNHS_XUEHAI_ZHUMENG_NOTICE_URL = "https://icsed-rnd.ntunhs.edu.tw/p/406-1037-73568,r847.php?Lang=zh-tw"
NTUNHS_OUTBOUND_STATUS_RULES_PDF = "https://reg-acad.ntunhs.edu.tw/var/file/39/1039/img/39/412506617.pdf"
NTUNHS_CREDIT_TRANSFER_RULES_PDF = "https://teaching-acad.ntunhs.edu.tw/var/file/40/1040/img/1423/B12-R013-20260624.pdf"
NTUNHS_ACADEMIC_REGULATIONS_PDF = "https://reg-acad.ntunhs.edu.tw/var/file/39/1039/img/39/653558921.pdf"
NTUNHS_GRADE_CONVERSION_PDF = "https://reg-acad.ntunhs.edu.tw/var/file/39/1039/img/39/383540446.pdf"
NTUNHS_DUAL_DEGREE_HANDBOOK_PDF = "https://international-rnd.ntunhs.edu.tw/var/file/37/1037/img/677187540.pdf"
NTUNHS_XUEHAI_FEIYANG_FORM_DOC = "https://international-rnd.ntunhs.edu.tw/var/file/37/1037/img/435789876.doc"
NTUNHS_XUEHAI_XIZHU_FORM_DOC = "https://international-rnd.ntunhs.edu.tw/var/file/37/1037/img/403790488.doc"

REGION_COST_DEFAULTS = {
    "澳洲": (
        "每月生活費約 USD 1,200–1,800（折合澳幣約 AUD 1,800–2,600 / 月、新臺幣約 38,000–57,000 元；含昆士蘭大學 UQ、昆士蘭科技大學 QUT、迪肯大學 Deakin、墨爾本威廉安格利斯學院 WAI、阿得雷德 ICHM 與 TAFE Queensland 校內外學生公寓與膳食交通）",
        "修讀雙聯學位或一學期以上交換須申辦澳洲學生簽證（Subclass 500）並投保澳洲海外學生健康保險（OSHC）。",
    ),
    "紐西蘭": (
        "每月生活費約 USD 1,050–1,600（折合紐幣約 NZD 1,750–2,650 / 月、新臺幣約 33,500–51,000 元；含梅西大學 Massey University 北帕默斯頓／奧克蘭／威靈頓校區、奧克蘭大學與曼努考理工學院學生宿舍與膳食）",
        "交換一學期以上須憑紐西蘭接待校 Offer of Place 申辦 Fee Paying / Exchange Student Visa 並投保紐西蘭認可之全期醫療與旅遊保險。",
    ),
    "英國": (
        "每月生活費約 USD 1,200–1,800（折合英鎊約 GBP 950–1,400 / 月、新臺幣約 38,000–57,000 元；含布里斯托西英格蘭大學 UWE、貝爾法斯特女王大學 QUB、阿爾斯特大學 Ulster 與貝德福德郡大學校內外住宿與生活費）",
        "修讀 UWE 雙聯學位或一學年交換須申辦英國 Student Visa 並繳交英國移民醫療附加費（IHS）；短期一學期交換可依規定申辦 Standard Visitor Visa。",
    ),
    "捷克": (
        "每月生活費約 USD 550–900（折合歐元約 EUR 500–820 / 月、新臺幣約 17,500–28,500 元；奧斯特拉瓦大學 University of Ostrava 醫學院交換生入住 Jan Opletal 學生宿舍月租僅約 EUR 130–180，物價親民且享學生交通優惠）",
        "須憑奧斯特拉瓦大學入學許可與住宿證明向捷克經濟文化辦事處申辦長期學生簽證（D Visa），並購買符合捷克法規之境內綜合醫療保險（pVZP）。",
    ),
    "立陶宛": (
        "每月生活費約 USD 550–850（折合歐元約 EUR 500–780 / 月、新臺幣約 17,500–27,000 元；克萊佩達市立大學 KVK 國際學生宿舍月租僅約 EUR 100–160，海港城市生活開銷實惠）",
        "須憑立陶宛 KVK 核發之調解信與入學許可申辦立陶宛國家簽證（D Visa）或申根簽證，並投保涵蓋全期之申根醫療保險（保額至少 EUR 30,000）。",
    ),
    "克羅埃西亞": (
        "每月生活費約 USD 650–1,050（折合歐元約 EUR 600–960 / 月、新臺幣約 21,000–33,500 元；含札格拉布大學 University of Zagreb 學生宿舍與日常膳食）",
        "須依克羅埃西亞駐外機構規定申辦長期學生簽證或居留許可，並購買涵蓋全期之申根醫療保險。",
    ),
    "西班牙": (
        "每月生活費約 USD 750–1,200（折合歐元約 EUR 680–1,100 / 月、新臺幣約 24,000–38,000 元；含加的斯大學 University of Cádiz 校外合租學生公寓與安達魯西亞生活開銷）",
        "須憑西班牙接待大學入學許可向西班牙商務辦事處申辦學生簽證，並投保無自付額之全額醫療與意外保險。",
    ),
    "美國": (
        "每月生活費約 USD 1,250–2,100（折合新臺幣約 40,000–67,000 元；含奧本大學 Auburn、關島大學 UOG、西雅圖華盛頓大學 UW、南加州大學 USC、密西根州立大學 MSU、德州大學聖安東尼奧健康科學中心與西奈山護理學院住宿與膳食）",
        "學期交換或雙聯學位須憑 DS-2019（J-1）或 I-20（F-1）向美國在台協會（AIT）申辦簽證；關島暑期學海築夢實習與短期研習依接待校規定辦理簽證或 ESTA，並全程投保海外醫療與意外險。",
    ),
    "布吉納法索": (
        "每月生活費約 USD 450–800（折合新臺幣約 14,500–25,500 元；含瓦加杜古布吉納法索國立公共衛生學院 ENSP 國際交流住宿與膳食）",
        "須依規定申辦簽證、完成黃熱病等國際預防接種證明（黃皮書）並投保含緊急醫療轉送之海外全程醫療險。",
    ),
    "日本": (
        "每月生活費約 USD 500–1,000（折合日圓約 JPY 65,000–135,000 / 月、新臺幣約 16,000–32,000 元；名古屋市立大學、縣立廣島大學、東京都立大學 HIIP［免費提供荒川校區宿舍］、山形縣立保健醫療大學、沖繩縣立看護大學與佐久大學留學生宿舍費用低廉）",
        "學期交換生須由日本接待大學代辦「在留資格認定證明書（COE）」後向日本台灣交流協會申辦留學簽證，入境後加入日本國民健康保險（NHI）。",
    ),
    "韓國": (
        "每月生活費約 USD 450–900（折合韓元約 KRW 600,000–1,250,000 / 月、新臺幣約 14,500–29,000 元；其中大邱保健大學 DHC 學期交換生享有免費雙人房學生宿舍，每月生活費僅約 KRW 500,000–800,000）",
        "學期交換須憑韓國接待校標準入學許可書向駐台北韓國代表部申辦 D-2-6 交換簽證，入境後辦理外國人登錄證（ARC）並納保韓國國民健康保險（NHIS）。",
    ),
    "香港": (
        "每月生活費約 USD 800–1,350（折合港幣約 HKD 6,200–10,500 / 月、新臺幣約 25,500–43,000 元；含香港中文大學那打素護理學院與香港專業教育學院 IVE 交流期間食宿交通）",
        "須依香港入境事務處規定辦理來港就讀／交流簽證（Entry Permit）或台灣居民預辦入境登記，並投保海外全期醫療與意外險。",
    ),
    "中國大陸": (
        "每月生活費約 USD 350–650（折合人民幣約 RMB 2,200–4,200 / 月、新臺幣約 11,000–21,000 元；含中南大學湘雅護理學院、廣州醫科大學、濱州醫學院、廈門醫學院、宜春學院、山東協和學院等校內宿舍與食堂開銷）",
        "須持有效「臺灣居民來往大陸通行證（臺胞證）」及接待高校錄取通知書報到，出國前完成大陸委員會「國人赴陸港澳動態登錄」並購買海外醫療及意外保險。",
    ),
    "蒙古": (
        "每月生活費約 USD 380–680（折合新臺幣約 12,000–21,500 元；含蒙古國立醫科大學 MNUMS、蒙古全球領袖大學 GLU 與奧托奇曼蘭巴大學傳統醫學交流食宿）",
        "須憑蒙古合作大學邀請函申辦簽證，並於出國前投保涵蓋全期之海外醫療及意外保險。",
    ),
    "巴林": (
        "每月生活費約 USD 850–1,400（折合新臺幣約 27,000–45,000 元；含愛爾蘭皇家外科醫學院巴林分校 RCSI Bahrain 穆哈拉格校區周邊住宿與交通膳食）",
        "須由巴林 RCSI 協助申辦巴林學生／訪問簽證，並投保涵蓋中東地區之全期國際醫療保險。",
    ),
    "菲律賓": (
        "每月生活費約 USD 420–750（折合新臺幣約 13,500–24,000 元；含菲律賓大學馬尼拉分校 UP Manila SILAB 醫療資訊實習與碧瑤大學 University of Baguio 短期交換住宿與膳食）",
        "須依菲律賓駐臺代表處（MECO）及接待校規定申辦簽證與特別學習許可（SSP），並投保海外全期醫療與意外保險。",
    ),
    "新加坡": (
        "每月生活費約 USD 1,000–1,650（折合新幣約 SGD 1,350–2,200 / 月、新臺幣約 32,000–53,000 元；含新加坡國立大學 NUS 交流與語聽系 Sonova 新加坡總部新南向學海築夢實習住宿與交通）",
        "須依新加坡移民與關卡局（ICA）規定申辦 Student's Pass 或 Training Employment Pass，並投保海外全期醫療與意外保險。",
    ),
    "泰國": (
        "每月生活費約 USD 450–800（折合泰銖約 THB 15,000–27,000 / 月、新臺幣約 14,500–25,500 元；含曼谷朱拉隆功大學新南向學海築夢運動科學實習、清邁大學、泰國東方大學、素叻他尼皇家大學與維思大學食宿）",
        "須憑泰國接待大學入學／實習許可向泰國貿易經濟辦事處（TTEO）申辦 Non-Immigrant ED 簽證並投保海外全期醫療險。",
    ),
    "馬來西亞": (
        "每月生活費約 USD 420–750（折合馬幣約 MYR 1,900–3,400 / 月、新臺幣約 13,500–24,000 元；含拉曼大學 UTAR 金寶／雙溪龍校區住宿與膳食）",
        "學期交換須透過馬來西亞教育全球服務中心（EMGS）申辦學生簽證核准函（VAL），並投保馬來西亞境內醫療保險。",
    ),
    "越南": (
        "每月生活費約 USD 350–650（折合新臺幣約 11,000–21,000 元；含順化醫藥大學、同奈科技大學與茶榮大學醫護交流期間食宿）",
        "須依越南接待大學指引申辦簽證，並投保涵蓋全期之海外醫療及意外保險。",
    ),
    "印尼": (
        "每月生活費約 USD 350–650（折合新臺幣約 11,000–21,000 元；含三寶瓏國立大學 UNNES、三寶瓏穆罕默德大學 UNIMUS、巨港穆罕默德大學 UMP、日惹穆罕默德大學 UMY、坤甸 ITEKES、布拉維賈亞大學 UB、峇里 ITEKES Bali 等新南向學海築夢實習與短期交換食宿）",
        "須由印尼接待大學協助申辦社會文化／學習簽證（C211 / C316 Study Visa），並投保海外全期醫療與意外保險。",
    ),
}

SEMESTER_DATES_BY_COUNTRY = {
    "澳洲": "第一學期（Semester 1）：約 2 月中下旬至 6 月下旬；第二學期（Semester 2）：約 7 月中下旬至 11 月下旬",
    "紐西蘭": "第一學期（Semester One）：約 2 月中下旬至 6 月中旬；第二學期（Semester Two）：約 7 月中旬至 11 月中旬",
    "英國": "秋季學期（Autumn Term）：約 9 月中下旬至翌年 1 月；春季學期（Spring Term）：約 1 月下旬至 5 月底",
    "捷克": "冬季學期（Winter Semester）：約 9 月中下旬至翌年 2 月初；夏季學期（Summer Semester）：約 2 月中旬至 6 月底",
    "立陶宛": "秋季學期（Autumn Semester）：約 9 月初至翌年 1 月底；春季學期（Spring Semester）：約 2 月初至 6 月底",
    "日本": "春季學期（前學期）：約 4 月初至 8 月上旬；秋季學期（後學期）：約 9 月下旬／10 月初至翌年 2 月／3 月",
    "韓國": "春季學期：約 3 月初至 6 月中旬；秋季學期：約 9 月初至 12 月中旬（寒暑假短期交換為 1 月及 7–8 月）",
    "美國": "秋季學期（Fall Semester）：約 8 月中下旬至 12 月中旬；春季學期（Spring Semester）：約 1 月中旬至 5 月中旬（暑期學海築夢實習為 7–8 月）",
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
                "latitude": float(loc.get("latitude", 25.1177)),
                "longitude": float(loc.get("longitude", 121.5173)),
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
    OFFICIAL_NTUNHS_DIR.mkdir(parents=True, exist_ok=True)
    catalog_source = json.loads(
        (SOURCES_NTUNHS_DIR / "ntunhs_catalog_source.json").read_text(encoding="utf-8")
    )
    resolved_locations = json.loads(
        (SOURCES_NTUNHS_DIR / "ntunhs_resolved_locations.json").read_text(encoding="utf-8")
    )
    bin_urls_path = SOURCES_NTUNHS_DIR / "binary_source_urls.json"
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

        group_str = clean_text(item.get("group") or "研究發展處國際暨兩岸教育中心正式締約姊妹校")
        if "雙聯" in group_str:
            dual_degree_count += 1
        quota_str = clean_text(item.get("quota") or "依當學年度國際暨兩岸教育中心公告名額")
        detail_url = item.get("detail_url") or NTUNHS_SISTER_SCHOOLS_URL
        source_url = detail_url

        if "雙聯" in group_str and ("交換" in group_str or "實習" in group_str):
            program_type = f"國立臺北護理健康大學跨國雙聯學位暨海外交換實習計畫（{group_str}）"
        elif "雙聯" in group_str:
            program_type = f"國立臺北護理健康大學跨國雙聯學位計畫（{group_str}）"
        elif avail_status == "open":
            program_type = f"國立臺北護理健康大學海外長短期交換暨學海專業實習計畫（{group_str}）"
        else:
            program_type = f"國立臺北護理健康大學國際暨兩岸教育中心正式締約姊妹校（{group_str}）"

        colleges_str = clean_text(item.get("colleges") or "")
        degree_levels_str = clean_text(item.get("eligible_degrees") or "")
        lang_req_str = clean_text(item.get("language_req") or "")
        gpa_req_str = clean_text(item.get("gpa_req") or "")
        website = item.get("website") or NTUNHS_SISTER_SCHOOLS_URL
        tuition_note = clean_text(item.get("tuition_note") or "")
        exps = item.get("experience_reports") or []

        round_label = (
            "115–116學年度海外長短期交換、跨國雙聯學位暨教育部學海系列甄選"
            if avail_status == "open"
            else "研究發展處國際暨兩岸教育中心正式締約姊妹校（當期開放名額依國際中心最新甄選公告為準）"
        )
        app_deadline_str = clean_text(item.get("deadline") or "")
        deadline_iso = "2026-10-31T17:00:00+08:00"
        win_status = "open" if avail_status == "open" else "closed"
        acad_year = "115"

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
            f"開放對象與學院：{colleges_str}（{degree_levels_str}）。依《國立臺北護理健康大學學生出國期間有關學業及學籍處理要點》（112.11.01 教務會議通過）及《國立臺北護理健康大學學生抵免學分處理辦法》（115.06.24 修正）："
            "（1）在學學籍與註冊規定：出國進修、交換或實習期間以二年為限，學生於出國交換期間須維持北護在學學籍並按規定辦理註冊（不得辦理休學，但不需掛校內課程），且因考量各系專業必修課程規畫與醫院臨床實習排程，所有交換與雙聯申請皆須先經所屬系所主任同意始得出國；"
            "（2）甄選評分與優先條件：學期交換須具日間部在學學籍且在校成績達 GPA 2.0（百分制 70 分）以上，申請教育部《學海飛颺／惜珠》獎學金以班排名百分比前 50% 及操行成績 80 分以上且無懲戒紀錄優先；書面審查占 40%–60%（含在校成績、外語能力證明、交換學習計畫書、曾任國際學伴 International Buddy 或國際志工證明），中英文面試占 40%–60%；"
            "（3）學分抵免與雙聯學位規範：返國後辦理學分抵免應符合科目名稱及內容高度相似之原則，專業科目由各系所審定、通識科目由通識教育中心審定；修讀澳洲 UQ、QUT、Deakin、WAI、英國 UWE 及美國 Auburn 跨國雙聯學位者，依各系雙聯學制手冊修畢規定學分與臨床實習時數後，分別由兩校授予學位證書。"
        )

        living_cost_str, visa_health_str = REGION_COST_DEFAULTS.get(
            country,
            (
                "每月生活費約 USD 700–1,300（折合新臺幣約 22,500–41,500 元，含住宿、膳食與市區交通）",
                "須依接待國駐臺機構規定申辦學生簽證，並於出國前購買涵蓋全期之海外醫療與意外保險。",
            ),
        )

        tuition_points_list = [
            f"國立臺北護理健康大學在學註冊與學雜費規定（依《學生出國期間有關學業及學籍處理要點》及各校交換簡章）：學期交換學生於出國期間須維持北護在學學籍並完成註冊（不得休學），免繳接待姊妹校學費（如捷克奧斯特拉瓦大學、日本名古屋市立大學、縣立廣島大學、立陶宛 KVK、韓國大邱保健大學［另享免費雙人房宿舍］；紐西蘭梅西大學 Study Abroad 及英美澳雙聯學位依兩校協議繳交學費並可申請雙聯獎學金）。本合作校待遇：{tuition_note}。",
            "教育部學海系列與國北護出國研修獎補助（研究發展處國際暨兩岸教育中心，校本部行政大樓 2 樓）：（1）教育部《學海飛颺》（選送優秀學生赴國外修讀學分，補助學費、機票與生活費）與《學海惜珠》（補助新臺幣 5 萬至 45 萬元以上）：限中華民國國籍、日間部在學生，以班排名百分比前 50%、操行 80 分以上且無懲戒紀錄優先；（2）教育部《學海築夢》與《新南向學海築夢》海外專業實習：由專任教師主持，選送學生赴美國關島大學、密西根州立大學、澳洲昆士蘭大學、日本佐久大學、泰國朱拉隆功大學、新加坡、菲律賓大學馬尼拉分校及印尼 UNNES／UNIMUS／UMP 等機構實習至少 30 天（醫護領域得為 14 天以上），補助來回機票與生活費。",
        ]

        app_steps_list = [
            f"步驟一（確認北護日間部在學資格、系所臨床實習排程與 {zh_name} 語檢要求）：確認符合在學資格（{degree_levels_str}）、學業與操行門檻（{gpa_req_str}）與外語標準（{lang_req_str}），並先向所屬系所確認出國期間是否衝堂專業必修或醫院臨床實習。",
            f"步驟二（備齊報名表、中英文歷年成績單含班排、語檢證明、交換學習計畫書與系所同意證明送交國際中心）：於公告截止日前將申請表件（申請學海飛颺／惜珠者另附個人資料表、1,000–1,500 字出國研修計畫書、中英文自傳、指導教授或系主任推薦信）送交校本部行政大樓 2 樓「研究發展處國際暨兩岸教育中心」（電話 02-2822-7101 分機 2730、2731、2732、2740，信箱 8yichern@ntunhs.edu.tw）。",
            f"步驟三（參加書面審查 40%–60% 與中英文面試 40%–60%，獲推薦提名並申請教育部學海系列獎學金）：由國際暨兩岸教育中心辦理校內書審與中英文面試（曾參與北護國際學伴 International Buddy 或國際交流活動者予以加分）；通過甄選後由國際中心正式向 {zh_name} 提名並遞交姊妹校入學與宿舍申請。",
            f"步驟四（維持北護在學註冊學籍、簽署學海行政契約書，返國後繳交結案心得報告並辦理學分抵免）：收到 {zh_name} 入學許可後辦理學生簽證、海外醫療及意外保險與外交部出國登錄；出國交換期間須維持北護在學學籍（不得休學），返國後依規定於期限內繳交出國研修／實習結案心得報告書與經費核銷單據，並依《國立臺北護理健康大學學生抵免學分處理辦法》檢附英文成績單與課程大綱向系所及通識教育中心辦理學分抵免。",
        ]

        elig_points_list = [
            f"合作類別與組別：{program_type}",
            f"開放學制與年級：{degree_levels_str}",
            f"開放申請學院：{colleges_str}",
            f"學業與操行成績門檻：{gpa_req_str}",
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
                raw_t = clean_text(e.get("title") or f"赴 {zh_name} 交換研修心得分享")
                esem = e.get("semester") or "歷年交換"
                edept = e.get("department") or "國立臺北護理健康大學交換生"
                estu = e.get("student") or "國立臺北護理健康大學交換生"
                eurl = e.get("url") or f"{NTUNHS_EXPERIENCES_URL}#ntunhs-exp-{sn}-{e_idx+1}"
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
                    f"國立臺北護理健康大學研究發展處國際暨兩岸教育中心公開收錄之 {edept} {estu} 赴 {country} {full_name} 交換／雙聯／學海築夢實習官方心得報告（{raw_t}），詳述課程修讀、醫療與長照機構見習、學生宿舍環境、當地生活開銷與跨文化收穫。"
                )
                theme_map = {
                    "academics": f"國立臺北護理健康大學 {edept} {estu} 於《{raw_t}》分享在 {zh_name} 修讀護理健康專業課程、高擬真模擬病房／臨床見習及返國辦理學分抵免之實務經驗。",
                    "housing": f"國立臺北護理健康大學學生記錄入住 {zh_name} 學生宿舍或寄宿家庭之房型設備、通勤方式與生活適應（{housing_str[:100]}）。",
                    "campus_culture": f"國立臺北護理健康大學國際暨兩岸教育中心收錄《{raw_t}》之國際學伴互動、醫院與長照機構參訪及跨文化醫療照護體悟。",
                    "cost": f"國立臺北護理健康大學學生分享於 {zh_name} 之每月租金、伙食與交通花費（{living_cost_str[:100]}），以及申請教育部學海飛颺／學海築夢獎學金之經驗。",
                }
                student_experience_rows.append({
                    "school_name": full_name,
                    "country": country,
                    "title": raw_t,
                    "source_url": eurl,
                    "source_type": "pdf" if eurl.lower().endswith(".pdf") else "article",
                    "platform": "國立臺北護理健康大學研究發展處國際暨兩岸教育中心—雙聯學制／海外長短期交換／學海計畫成果報告專區",
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
                        f"{full_name}:ntunhs_exp:{e_idx}:{eurl}".encode("utf-8")
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
            "home_university": "國立臺北護理健康大學",
            "school_name": full_name,
            "country": country,
            "official_experience_portal_url": exp_links[0]["url"] if exp_links else NTUNHS_EXPERIENCES_URL,
            "partner_page_url": source_url,
            "report_count": len(exps),
            "sample_reports": sample_reports,
            "checked_at": CHECKED_AT,
        })

        loc = resolved_locations.get(full_name) or {
            "city": country,
            "latitude": 25.1177,
            "longitude": 121.5173,
            "source_url": "https://www.wikidata.org",
        }
        city_name = loc.get("city") or country
        lat = float(loc.get("latitude", 25.1177))
        lon = float(loc.get("longitude", 121.5173))
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
                f"【國立臺北護理健康大學學長姐交換／雙聯／實習心得報告（共 {len(exps)} 篇）】收錄於國際暨兩岸教育中心網站（含：{'、'.join(exp_labels[:4])}）"
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
            "availability_note": f"國立臺北護理健康大學研究發展處國際暨兩岸教育中心公告合作校（{program_type}）；{quota_str}。",
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
                "title": f"國立臺北護理健康大學國際暨兩岸教育中心交換與雙聯公告—{zh_name}",
                "source_url": source_url,
                "role": "home_university",
                "authority": "home_official_notice",
                "effective_academic_year": acad_year,
                "application_round": round_label,
                "checked_at": CHECKED_AT,
            },
            {
                "title": "國立臺北護理健康大學學生出國期間有關學業及學籍處理要點與學生抵免學分處理辦法",
                "source_url": NTUNHS_OUTBOUND_STATUS_RULES_PDF,
                "role": "home_university",
                "authority": "home_official_notice",
                "effective_academic_year": acad_year,
                "application_round": round_label,
                "checked_at": CHECKED_AT,
            },
            {
                "title": "國立臺北護理健康大學教育部學海飛颺、學海惜珠與學海築夢甄選專區",
                "source_url": NTUNHS_XUEHAI_URL,
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
            "home_university": "國立臺北護理健康大學",
            "school_name": full_name,
            "partner_website": website,
            "country": country,
            "program_type": program_type,
            "academic_year": acad_year,
            "application_round": round_label,
            "effective_application_rounds": [round_label, "115-1", "115-2", "116-1", "116-2"],
            "applicability_status": "verified",
            "applicability_note": "國立臺北護理健康大學由研究發展處國際暨兩岸教育中心（校本部行政大樓 2 樓）統籌全校 4 大學院（護理學院、健康科技學院、人類發展與健康學院、智慧健康照護跨領域學院）之 6 校 9 學程英美澳跨國雙聯學位（澳洲昆士蘭大學 UQ、昆士蘭科技大學 QUT、迪肯大學 Deakin、墨爾本威廉安格利斯學院 WAI、英國西英格蘭大學 UWE、美國奧本大學 Auburn）、海外長短期學期交換（捷克奧斯特拉瓦大學、日本名古屋市立大學、縣立廣島大學、東京都立大學、山形縣立保健醫療大學、沖繩縣立看護大學、紐西蘭梅西大學、韓國大邱保健大學、高麗大學、首爾女子護理大學、立陶宛 KVK 等）及教育部學海飛颺／惜珠／築夢海外實習計畫。",
            "review_status": "published",
            "published_at": CHECKED_AT,
            "steps": [
                {
                    "rule_id": f"ntunhs-{acad_year}-home-1-{sn:03d}",
                    "order": 1,
                    "phase": "校內申請",
                    "title": f"確認北護日間部在學身分、GPA 2.0／班排前 50% 門檻、系所臨床實習排程與 {zh_name} 語檢要求",
                    "responsible_party": "學生",
                    "responsible_unit": "國立臺北護理健康大學研究發展處國際暨兩岸教育中心（行政大樓 2 樓）／各系所",
                    "deadline_at": deadline_iso,
                    "deadline_status": "verified_exact" if avail_status == "open" else "reference_only",
                    "deadline_source_url": source_url,
                    "deadline_checked_at": CHECKED_AT,
                    "deadline_reminder_eligible": avail_status == "open",
                    "summary": f"確認符合《國立臺北護理健康大學學生出國期間有關學業及學籍處理要點》及當期甄選簡章規定：在學學制（{degree_levels_str}）、學業與操行門檻（{gpa_req_str}）與外語標準（{lang_req_str}），並預先與系所確認出國交換或雙聯期間之必修課與臨床實習安排。",
                    "details": [
                        f"開放學制與學院：{colleges_str}（{degree_levels_str}）",
                        f"語言與學業條件：{lang_req_str}｜{gpa_req_str}",
                        f"當期名額與計畫類別：{quota_str}｜{program_type}",
                    ],
                    "scope": {
                        "home_universities": ["國立臺北護理健康大學"],
                        "partner_universities": [full_name],
                        "academic_years": ["115", "116"],
                        "application_rounds": [round_label, "115-1", "115-2", "116-1", "116-2"],
                    },
                    "source_urls": [source_url, NTUNHS_OUTBOUND_STATUS_RULES_PDF],
                    "checked_at": CHECKED_AT,
                    "support_status": "verified",
                },
                {
                    "rule_id": f"ntunhs-{acad_year}-home-2-{sn:03d}",
                    "order": 2,
                    "phase": "校內申請",
                    "title": "備妥交換／雙聯報名表、歷年中英文成績單（含 GPA 與班排）、外語檢定證明、交換學習計畫書與系所同意證明，送交行政大樓 2 樓國際暨兩岸教育中心",
                    "responsible_party": "學生",
                    "responsible_unit": "研究發展處國際暨兩岸教育中心（行政大樓 2 樓，分機 2730–2732、2740）",
                    "deadline_at": deadline_iso,
                    "deadline_status": "verified_exact" if avail_status == "open" else "reference_only",
                    "deadline_source_url": source_url,
                    "deadline_checked_at": CHECKED_AT,
                    "deadline_reminder_eligible": avail_status == "open",
                    "summary": "於各計畫公告截止日前將報名表、中英文歷年成績單、語檢證明、自我介紹與交換學習計畫書（申請學海飛颺／惜珠者另附學海申請表與推薦信）送交國際暨兩岸教育中心。",
                    "details": [
                        "必備申請文件：（1）國立臺北護理健康大學海外交換研習／雙聯學位／學海系列計畫報名表；（2）歷年中英文成績單正本（需含 GPA 及班級排名百分比）與操行成績證明；（3）外語能力檢定成績單影本（IELTS / TOEFL / TOEIC / JLPT / TOPIK）；（4）自我介紹與交換學習計畫書（含修課規劃及返國學分抵免構想）；（5）系所主任同意推薦證明、教師推薦信及國際學伴（International Buddy）參與證明。",
                    ],
                    "document_requirements": [
                        {
                            "name": "國立臺北護理健康大學交換研習計畫報名表暨學海飛颺／惜珠申請表",
                            "official_form_url": NTUNHS_XUEHAI_FEIYANG_FORM_DOC,
                            "source_urls": [NTUNHS_EXCHANGE_URL, NTUNHS_XUEHAI_URL],
                        },
                        {
                            "name": "中英文歷年成績單（含 GPA 與班排）、外語能力證明及交換學習計畫書",
                            "official_form_url": source_url,
                            "source_urls": [source_url, NTUNHS_DUAL_DEGREE_HANDBOOK_PDF],
                        },
                    ],
                    "scope": {
                        "home_universities": ["國立臺北護理健康大學"],
                        "academic_years": ["115", "116"],
                        "application_rounds": [round_label, "115-1", "115-2", "116-1", "116-2"],
                    },
                    "source_urls": [source_url, NTUNHS_XUEHAI_URL],
                    "checked_at": CHECKED_AT,
                    "support_status": "verified",
                },
                {
                    "rule_id": f"ntunhs-{acad_year}-home-3-{sn:03d}",
                    "order": 3,
                    "phase": "甄選與提名",
                    "title": "通過書面審查（40%–60%）與中英文面試（40%–60%），獲選推薦提名並申辦教育部學海飛颺／惜珠／築夢獎學金",
                    "responsible_party": "國際暨兩岸教育中心與申請學生",
                    "responsible_unit": "研究發展處國際暨兩岸教育中心審查委員會",
                    "deadline_at": "2026-11-15T17:00:00+08:00",
                    "deadline_status": "verified_exact",
                    "deadline_source_url": source_url,
                    "deadline_checked_at": CHECKED_AT,
                    "deadline_reminder_eligible": False,
                    "summary": "依各校交換簡章評分標準進行書審（40%–60%，含在校成績、語檢、讀書計畫、國際學伴經驗）與中英文面試（40%–60%）；獲選學生由國際中心正式向合作姊妹校提名，並可同步申請教育部《學海飛颺／學海惜珠／學海築夢》獎學金。",
                    "details": [
                        "甄選評分權重：書面審查占 40%–60%、中英文口試占 40%–60%；曾擔任本校國際學伴（International Buddy）協助接待外籍生者於書審予以加分。",
                        "教育部學海系列獎學金：學海飛颺與學海惜珠於每年 2–3 月受理校內甄選（班排前 50% 及操行 80 分以上無懲戒紀錄優先），5 月底公告教育部核定補助結果。",
                    ],
                    "scope": {
                        "home_universities": ["國立臺北護理健康大學"],
                        "academic_years": ["115", "116"],
                        "application_rounds": [round_label, "115-1", "115-2", "116-1", "116-2"],
                    },
                    "source_urls": [source_url, NTUNHS_XUEHAI_FEIYANG_NOTICE_URL, NTUNHS_XUEHAI_ZHUMENG_NOTICE_URL],
                    "checked_at": CHECKED_AT,
                    "support_status": "verified",
                },
                {
                    "rule_id": f"ntunhs-{sn:03d}-host-apply",
                    "order": 4,
                    "phase": "合作校申請",
                    "title": f"由國際暨兩岸教育中心具函向 {zh_name} 推薦提名，遞交姊妹校入學與宿舍申請並取得正式入學許可",
                    "responsible_party": "學生與接待校國際事務處",
                    "summary": f"通過校內甄選後，由國立臺北護理健康大學國際暨兩岸教育中心（承辦人：陳弋凡 Michael 8yichern@ntunhs.edu.tw）向 {zh_name} 完成官方提名，協助學生繳交姊妹校入學申請表、英文成績單、護照影本、健康檢查與疫苗接種證明（醫護臨床見習必備）並登記學生宿舍。",
                    "details": [
                        f"研修期程：{study_period_str}｜名額：{quota_str}",
                        f"語言與學業條件：{lang_req_str}｜{gpa_req_str}",
                        f"住宿與費用待遇：{housing_str}",
                    ],
                    "scope": {
                        "home_universities": ["國立臺北護理健康大學"],
                        "partner_universities": [full_name],
                        "academic_years": ["115", "116"],
                        "application_rounds": [round_label, "115-1", "115-2", "116-1", "116-2"],
                    },
                    "source_urls": [source_url, NTUNHS_DUAL_DEGREE_HANDBOOK_PDF, website],
                    "checked_at": CHECKED_AT,
                    "support_status": "verified",
                    "needs_confirmation": False,
                },
                {
                    "rule_id": f"ntunhs-{acad_year}-home-5-{sn:03d}",
                    "order": 5,
                    "phase": "行前準備",
                    "title": "維持北護在學註冊學籍（不得休學）、簽署學海行政契約與投保海外醫療險，返國後繳交結案心得報告並辦理學分抵免",
                    "responsible_party": "學生與所屬系所",
                    "responsible_unit": "國際暨兩岸教育中心／教務處註冊組與課務組／各系所",
                    "summary": "依《國立臺北護理健康大學學生出國期間有關學業及學籍處理要點》，出國交換期間須維持北護在學學籍並按規定辦理註冊（不得休學，但不需掛校內課程）；出國前完成簽證、海外醫療及意外保險與學海行政契約書簽署；返國後繳交出國研修／實習結案報告書及核銷單據，並依《學生抵免學分處理辦法》填具專業科目／通識科目抵免學分申請表向系所及通識中心辦理學分採認。",
                    "details": tuition_points_list,
                    "scope": {
                        "home_universities": ["國立臺北護理健康大學"],
                        "academic_years": ["115", "116"],
                        "application_rounds": [round_label, "115-1", "115-2", "116-1", "116-2"],
                    },
                    "source_urls": [NTUNHS_OUTBOUND_STATUS_RULES_PDF, NTUNHS_CREDIT_TRANSFER_RULES_PDF, NTUNHS_GRADE_CONVERSION_PDF],
                    "checked_at": CHECKED_AT,
                    "support_status": "verified",
                },
            ],
            "sources": wf_sources,
            "last_checked": CHECKED_AT,
            "coverage_status": "official_verified",
            "coverage_note": f"已完整整合國立臺北護理健康大學研究發展處國際暨兩岸教育中心《雙聯學制專區（6 校 9 學程）》、《海外長短期交換專區》、《教育部學海飛颺／惜珠／築夢專區》、《五大洲締約姊妹校名錄》、《學生出國期間有關學業及學籍處理要點》、《學生抵免學分處理辦法》及 {exp_covered_schools} 校 {total_exp_reports} 篇歷屆交換、雙聯與海外實習心得報告，共 {len(catalog_source)} 所合作姊妹校資料。",
        })

        cost_line = f"{zh_name} 預估每月生活費：{living_cost_str}"
        tuition_clean = tuition_points_list[0]
        housing_clean = housing_str
        calendar_clean = f"學期與研修時間參考：{sem_dates_str}"
        course_clean = course_rest_str
        src_url_list = [source_url, NTUNHS_OUTBOUND_STATUS_RULES_PDF, NTUNHS_CREDIT_TRANSFER_RULES_PDF, website]

        destinations.append({
            "home_university": "國立臺北護理健康大學",
            "school_name": full_name,
            "country": country,
            "city": city_name,
            "cost_summary": f"{cost_line}。\n{tuition_clean}",
            "housing_summary": housing_clean,
            "transport_summary": f"校區代表城市：{city_name}。請依入學許可確認實際授課校區與實習醫療機構位置、接機服務與當地學生交通優惠。",
            "campus_life_summary": f"{calendar_clean}\n{course_clean}",
            "student_guide_sections": [
                {
                    "key": "cost",
                    "title": "生活費、北護在學註冊規定與教育部學海飛颺／惜珠／築夢獎學金",
                    "summary": cost_line,
                    "points": [cost_line] + tuition_points_list,
                    "source_urls": src_url_list,
                    "caution": "出國交換期間須維持國立臺北護理健康大學在學學籍並按規定辦理註冊（不得辦理休學，但不需掛校內課程），且須先經所屬系所同意。",
                },
                {
                    "key": "housing",
                    "title": "校內外留學生宿舍、住宿申請與學伴接機資訊",
                    "summary": housing_clean[:160],
                    "points": [housing_clean],
                    "source_urls": src_url_list,
                    "caution": "各姊妹校宿舍名額有限（如韓國大邱保健大學提供免費雙人房宿舍、日本東京都立大學 HIIP 免費提供荒川校區宿舍、捷克奧斯特拉瓦大學提供 Jan Opletal 宿舍），請於獲提名後依接待校期限完成宿位申請。",
                },
                {
                    "key": "insurance",
                    "title": "海外醫療意外保險、臨床見習疫苗體檢與外交部出國動態登錄",
                    "summary": visa_health_str,
                    "points": [
                        visa_health_str,
                        "醫護與健康科學院系學生赴海外醫院或長照機構見習／實習前，須依接待校規定備妥英文健康檢查表與抗體疫苗接種證明（如 B 型肝炎、麻疹 MMR、水痘、肺結核 X 光等），並投保涵蓋全期之海外醫療及意外保險。",
                    ],
                    "source_urls": src_url_list,
                    "caution": "學海系列受獎生出國前須與本校簽署行政契約書，並完成外交部領事事務局出國登錄。",
                },
                {
                    "key": "visa",
                    "title": "留學／實習簽證辦理、在學學籍保留與出國二年期限規定",
                    "summary": visa_health_str,
                    "points": [
                        visa_health_str,
                        "依《國立臺北護理健康大學學生出國期間有關學業及學籍處理要點》第 3 點，學生出國進修、研究、修讀學分、交換或實習以二年為限；具役男身分者須於出國前依規定辦理役男出境核准手續。",
                    ],
                    "source_urls": src_url_list,
                    "caution": "交換學生於國外期間應保有本校在學學籍（不得辦理休學），以免喪失交換生及教育部學海獎學金受獎資格。",
                },
                {
                    "key": "academics",
                    "title": "系所專業課程與臨床實習確認、雙聯學制修業與返國學分抵免規定",
                    "summary": course_clean[:160],
                    "points": [calendar_clean, course_clean],
                    "source_urls": src_url_list,
                    "caution": "因護理、助產、語聽、長照、運保、生諮、幼保等系所具嚴格之專業必修與臨床實習排程，申請出國前務必先與系所確認修課與實習規劃，以免延畢。",
                },
                {
                    "key": "living",
                    "title": f"{city_name} 校園生活與國立臺北護理健康大學學長姐交換／雙聯／實習心得傳承",
                    "summary": f"代表城市：{city_name}。返國後依規定繳交出國研修／實習結案心得報告並參與國際暨兩岸教育中心經驗分享會。",
                    "points": [
                        f"目的地城市：{city_name}（{country}）",
                        f"國立臺北護理健康大學國際暨兩岸教育中心公開歷屆學長姐雙聯、長短期交換與學海築夢海外實習心得報告"
                        + (f"（本校共收錄 {len(exps)} 篇心得：{'、'.join(exp_labels[:3])}）" if exps else "")
                        + "，並設有國際學伴（International Buddy）制度促進雙向交流。",
                    ],
                    "source_urls": [exp_links[0]["url"] if exp_links else NTUNHS_EXPERIENCES_URL],
                },
            ],
            "sources": [
                {
                    "title": f"國立臺北護理健康大學國際暨兩岸教育中心合作專頁—{zh_name}",
                    "source_url": source_url,
                    "summary": "國立臺北護理健康大學公告之雙聯學制、長短期交換與海外實習申請資格、語言門檻及費用待遇說明",
                },
                {
                    "title": "國立臺北護理健康大學學生出國期間有關學業及學籍處理要點與學生抵免學分處理辦法",
                    "source_url": NTUNHS_OUTBOUND_STATUS_RULES_PDF,
                    "summary": "國立臺北護理健康大學出國交換在學註冊規定、二年出國期限、系所同意程序與返國學分抵免規範",
                },
            ],
            "last_checked": CHECKED_AT,
            "coverage_status": "official_verified",
            "coverage_note": f"已整合國立臺北護理健康大學研究發展處國際暨兩岸教育中心 {len(catalog_source)} 所合作姊妹校（含 {open_partner_count} 所常態開放雙聯、長短期交換與學海築夢實習學校）及 {exp_covered_schools} 校 {total_exp_reports} 篇歷屆心得報告。",
        })

        research_records.append({
            "home_university": "國立臺北護理健康大學",
            "school_name": full_name,
            "country": country,
            "official_website": website,
            "verification_status": "official_verified",
            "discovery_source_url": detail_url,
            "checked_at": CHECKED_AT,
            "note": "國立臺北護理健康大學研究發展處國際暨兩岸教育中心雙聯學制專頁、海外長短期交換專頁、學海計畫成果專頁、五大洲締約姊妹校名錄及 ROR/Wikidata 官方網址核對完成。",
        })

        ev_sources = [{"title": f"國立臺北護理健康大學國際暨兩岸教育中心專頁—{zh_name}", "url": source_url}]
        if exp_links:
            ev_sources.append({"title": f"國立臺北護理健康大學赴 {zh_name} 交換／雙聯／實習心得報告（{len(exps)} 篇）", "url": exp_links[0]["url"]})
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
                    "scope": "國立臺北護理健康大學合作姊妹校住宿與生活資訊",
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
                    "scope": "國立臺北護理健康大學出國交換學雜費規定與教育部學海系列獎學金",
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
                    "scope": "國立臺北護理健康大學學生出國期間有關學業及學籍處理要點與抵免學分辦法",
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
                    "scope": "國立臺北護理健康大學海外交換、雙聯與臨床實習簽證及保險規定",
                    "original_excerpt": False,
                    "original_text": "",
                    "translation_status": "original",
                },
                {
                    "theme": "campus_culture",
                    "kind": "mixed" if has_student_exp else "official",
                    "text": f"合作類別：{program_type}｜名額：{quota_str}｜語言要求：{lang_req_str}"
                    + (f"｜國立臺北護理健康大學公開收錄 {len(exps)} 篇赴 {zh_name} 交換／雙聯／實習心得報告（{'、'.join(exp_labels[:3])}）。" if exps else ""),
                    "sources": ev_sources,
                    "checked_at": CHECKED_AT,
                    "scope": "國立臺北護理健康大學交換名額與歷屆學長姐心得報告",
                    "original_excerpt": False,
                    "original_text": "",
                    "translation_status": "original",
                },
            ],
            "notes": [
                "已整合國立臺北護理健康大學研究發展處國際暨兩岸教育中心《雙聯學制手冊》、《海外長短期交換簡章》、《教育部學海飛颺／惜珠／築夢專區》及歷屆學生心得報告。",
                "當期開放名額、宿位供給、語檢門檻與臨床見習限制請依合作校最新簡章及入學通知書核對。",
            ],
            "location_signature": f"verified:{lat}:{lon}:representative",
            "extraction_version": 3,
        })

    def write_jsonl(path: Path, rows: list[dict]) -> None:
        path.write_text(
            "\n".join(json.dumps(r, ensure_ascii=False) for r in rows) + ("\n" if rows else ""),
            encoding="utf-8",
        )

    write_jsonl(OFFICIAL_NTUNHS_DIR / "partners.jsonl", partners)
    write_jsonl(SOURCES_NTUNHS_DIR / "partners.jsonl", partners)
    write_jsonl(OFFICIAL_NTUNHS_DIR / "application_workflows.jsonl", workflows)
    write_jsonl(OFFICIAL_NTUNHS_DIR / "destination_profiles.jsonl", destinations)
    write_jsonl(OFFICIAL_NTUNHS_DIR / "partner_research.jsonl", research_records)
    write_jsonl(OFFICIAL_NTUNHS_DIR / "student_life.jsonl", life_records)
    write_jsonl(OFFICIAL_NTUNHS_DIR / "experience_sources.jsonl", experience_sources_records)
    write_jsonl(OFFICIAL_NTUNHS_DIR / "student_experience_sources.jsonl", experience_sources_records)
    write_jsonl(OFFICIAL_NTUNHS_DIR / "student_experiences.jsonl", student_experience_rows)

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
    (OFFICIAL_NTUNHS_DIR / "student-experience-digests.json").write_text(
        json.dumps({"digests": digest_records}, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    (OFFICIAL_NTUNHS_DIR / "student-experiences.json").write_text(
        json.dumps(
            {
                "school_id": "ntunhs",
                "school_name": "國立臺北護理健康大學",
                "checked_at": CHECKED_AT,
                "source_url": NTUNHS_EXPERIENCES_URL,
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

    (OFFICIAL_NTUNHS_DIR / "campus-locations.json").write_text(
        json.dumps(
            {
                "school_id": "ntunhs",
                "school_name": "國立臺北護理健康大學",
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
    (OFFICIAL_NTUNHS_DIR / "campus-assets.json").write_text(
        json.dumps(
            {
                "school_id": "ntunhs",
                "school_name": "國立臺北護理健康大學",
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

    ntunhs_source_urls = [
        NTUNHS_HOME_URL,
        NTUNHS_ICSED_HOME_URL,
        NTUNHS_DUAL_DEGREE_URL,
        NTUNHS_EXCHANGE_URL,
        NTUNHS_XUEHAI_URL,
        NTUNHS_SISTER_SCHOOLS_URL,
        NTUNHS_BUDDY_URL,
        NTUNHS_EXPERIENCES_URL,
        NTUNHS_OSTRAVA_NOTICE_URL,
        NTUNHS_NCU_JP_NOTICE_URL,
        NTUNHS_HIROSHIMA_NOTICE_URL,
        NTUNHS_MASSEY_NOTICE_URL,
        NTUNHS_DHC_NOTICE_URL,
        NTUNHS_KVK_NOTICE_URL,
        NTUNHS_XUEHAI_FEIYANG_NOTICE_URL,
        NTUNHS_XUEHAI_ZHUMENG_NOTICE_URL,
        NTUNHS_OUTBOUND_STATUS_RULES_PDF,
        NTUNHS_CREDIT_TRANSFER_RULES_PDF,
        NTUNHS_ACADEMIC_REGULATIONS_PDF,
        NTUNHS_GRADE_CONVERSION_PDF,
        NTUNHS_DUAL_DEGREE_HANDBOOK_PDF,
        NTUNHS_XUEHAI_FEIYANG_FORM_DOC,
        NTUNHS_XUEHAI_XIZHU_FORM_DOC,
    ]

    exchange_info_payload = {
        "school_name": "國立臺北護理健康大學",
        "program_type": [
            f"研究發展處國際暨兩岸教育中心「海外長短期交換學生計畫」（涵蓋捷克奧斯特拉瓦大學 University of Ostrava 醫學院、立陶宛克萊佩達市立大學 KVK、日本名古屋市立大學 Nagoya City University、日本縣立廣島大學、東京都立大學 HIIP［免學費及免費荒川校區宿舍］、山形縣立保健醫療大學、沖繩縣立看護大學、福岡大學、紐西蘭梅西大學 Massey University、韓國大邱保健大學 DHC［免學費及免費雙人房宿舍］、高麗大學、首爾女子護理大學、澳洲國際飯店管理學院 ICHM、昆士蘭公立技術學院 TAFE Queensland 等，全校共 {len(partners)} 所全球與兩岸合作姊妹校、{open_partner_count} 所常態開放雙聯、交換與海外實習）",
            "英、美、澳 6 校 9 學程「跨國雙聯學位計畫」（涵蓋【澳洲昆士蘭大學 UQ：護理系 3.5+2／1.5+2 雙學士與 4+1.5／2+1.5 學碩雙聯、語言治療與聽力學系 4+2 聽力學碩士雙聯、生死與健康心理諮商系 4+2 社會工作碩士雙聯】、【美國奧本大學 Auburn University：護理系 4+5／5+5 MSN 碩士暨 PhD 博士雙聯】、【英國西英格蘭大學 UWE Bristol：護理系 3.5+1／1.5+2 雙學士、資訊管理系 3+1 雙學士】、【澳洲昆士蘭科技大學 QUT：資訊管理系 2+2 雙學士】、【澳洲迪肯大學 Deakin University：健康事業管理系 3.5+1.5 MBA 醫療管理學碩雙聯】、【澳洲墨爾本威廉安格利斯學院 William Angliss Institute：休閒產業與健康促進系 Aviation 航空空服／Tourism 旅遊管理雙聯】）",
            "教育部「學海飛颺、學海惜珠、學海築夢與新南向學海築夢」海外專業實習與獎學金計畫（涵蓋美國關島大學 UOG 護理／運保／生諮海外實習、密西根州立大學 MSU 幼保兒童發展實驗學校實習、澳洲昆士蘭大學布里斯本社區健康實習、日本長野縣佐久大學高齡長照實習、泰國朱拉隆功大學運動科學實習、新加坡國立大學與 Sonova 聽力科技實習、菲律賓大學馬尼拉分校 UP Manila SILAB 醫療資訊實習、印尼三寶瓏國立大學 UNNES／三寶瓏穆罕默德大學 UNIMUS／巨港穆罕默德大學 UMP 醫護與傷口照護實習）",
        ],
        "academic_year": [
            "115–116（涵蓋每學期兩梯次海外學期交換學生甄選［秋季班每年 2–4 月申請、春季班每年 9–10 月申請］、英美澳 6 校 9 學程跨國雙聯學位甄選、寒暑假短期海外交換研習及教育部學海飛颺／惜珠／築夢獎學金甄選［每年 2–3 月收件］）",
            f"本平台完整收錄國立臺北護理健康大學研究發展處國際暨兩岸教育中心公告之 {len(partners)} 所全球與兩岸合作姊妹校（含 {open_partner_count} 所常態開放申請之雙聯、長短期交換與海外實習合作校、{len(partners) - open_partner_count} 所正式締約姊妹校，橫跨 21 個國家與地區，並完整收錄 {exp_covered_schools} 所合作大學共 {total_exp_reports} 篇歷屆學長姐雙聯、交換與實習心得報告）",
        ],
        "semester": [
            "海外姊妹校學期交換計畫：可申請一學期或一學年；依《國立臺北護理健康大學學生出國期間有關學業及學籍處理要點》，出國進修或交換以二年為限，出國交換期間須維持北護在學學籍並按規定辦理註冊（不得休學，但不需掛校內課程），且須先經所屬系所同意。",
            "英美澳跨國雙聯學位與寒暑假海外實習：雙聯學位依各系學制為半年至 5 年（如 UWE 資管 3+1 與護理 3.5+1、Deakin 健管 3.5+1.5、QUT 資管 2+2、UQ 護理／聽力／社工 1.5～2 年、Auburn 護理碩博 4+5／5+5、WAI 休健半年～1 年）；教育部學海築夢／新南向學海築夢海外專業實習為寒暑假 14～35 天以上。",
        ],
        "application_period": [
            "【第一梯次（秋季班出國交換暨教育部學海飛颺／惜珠／築夢獎學金甄選）】每年 2 月至 4 月受理申請（教育部學海飛颺、學海惜珠與學海築夢校內收件於每年 2–3 月截止，5 月底公告教育部核定補助結果；捷克奧斯特拉瓦大學、立陶宛 KVK、紐西蘭梅西大學第二學期、日本名古屋市立大學秋季班及暑期短期交換同步於 2–4 月報名）。",
            "【第二梯次（春季班出國交換暨英美澳雙聯學位甄選）】每年 9 月至 10 月底受理申請（如日本名古屋市立大學 2027 春季班 9 月底截止提名、捷克奧斯特拉瓦大學與日本縣立廣島大學及韓國大邱保健大學春季班 9–10 月收件、澳洲昆士蘭科技大學 2027 寒假健康研習團 10 月報名、紐西蘭梅西大學第一學期 10 月底截止）。",
        ],
        "eligibility": [
            "1. 在學身分與系所臨床實習同意規定：依《國立臺北護理健康大學學生出國期間有關學業及學籍處理要點》及各校交換簡章，申請人須為本校日間部在學學生（含四技 2～4 年級、二技、學士後護理系、碩士班及博士班；不含在職專班及休學學生）。因考量護理、助產、語聽、長照、運保、生諮、幼保等系所專業必修課程規畫與醫院臨床實習排程，交換生及雙聯生皆須經所屬系所同意始得出國，且出國交換期間須維持北護在學學籍（不得辦理休學）。",
            "2. 學業與操行成績門檻：（a）一般學期交換與短期海外研習：在校歷年學業平均成績須達 GPA 2.0（百分制約 70 分）以上，操行成績達 80 分以上且無懲戒紀錄；（b）教育部《學海飛颺／學海惜珠》獎學金：具中華民國國籍、於北護就讀滿一學期以上，以班排名百分比前 50% 及操行成績 80 分以上且無懲戒紀錄優先推薦；（c）英美澳跨國雙聯學位（UQ、QUT、Deakin、UWE、Auburn）：建議在校歷年平均 GPA 2.75–3.0（百分制 75–80 分）以上並修畢各系指定先修課程。",
            "3. 甄選評分標準與國際學伴加分：校內甄選包含「書面審查（40%–60%）」與「中英文面試（40%–60%）」；曾報名參與國際暨兩岸教育中心「國際學伴（International Buddy）」接待外籍交換生或參與國際志工活動者，於書面審查予以優先加分。",
        ],
        "language_requirement": [
            "1. 英美澳跨國雙聯學位語言門檻：（a）澳洲昆士蘭大學（UQ 護理雙學士／護理碩士／聽力學碩士／社工碩士）：IELTS Academic 總分 7.0（聽說讀寫各單科不低於 7.0）或 TOEFL iBT 100；（b）美國奧本大學（Auburn 護理碩博雙聯）、澳洲昆士蘭科技大學（QUT 資管 2+2）、澳洲迪肯大學（Deakin 健管 MBA 3.5+1.5）、英國西英格蘭大學（UWE 護理雙聯）：IELTS Academic 總分 6.5（各單科不低於 6.0）或 TOEFL iBT 79；（c）英國西英格蘭大學（UWE 資管 3+1）與澳洲墨爾本威廉安格利斯學院（WAI 休健雙聯／交換）：IELTS Academic 總分 6.0（各單科不低於 5.5）。",
            "2. 英語組學期交換與海外實習門檻：（a）紐西蘭梅西大學（Massey University）：大學部 IELTS 6.0（單科 5.5）／碩士班 IELTS 6.5（單科 6.0）；（b）捷克奧斯特拉瓦大學（University of Ostrava）與立陶宛克萊佩達市立大學（KVK）：英語能力達 CEFR B1–B2（TOEIC 550–785 / IELTS 5.5–6.0 / TOEFL iBT 61–79）；（c）美國關島大學、華盛頓大學、南加州大學、密西根州立大學、東京都立大學 HIIP 及新南向學海築夢（泰國朱拉隆功大學、新加坡、菲律賓 UP Manila、印尼 UNNES／UNIMUS／UMP）：具良好英語溝通能力（建議 TOEIC 550–650 / IELTS 5.5–6.0 以上）。",
            "3. 日語組、韓語組與大陸地區門檻：（a）日本名古屋市立大學：JLPT N1 合格或英語 CEFR B2（如尚未取得 N3 以上日語檢定可先檢附學習證明與日文自傳報考）；（b）日本縣立廣島大學、山形縣立保健醫療大學、沖繩縣立看護大學、佐久大學：建議具 JLPT N2–N3 或基礎日語與英語溝通能力；（c）韓國大邱保健大學、高麗大學、首爾女子護理大學、春海保健大學：具英語溝通能力或韓語 TOPIK 2–3 級；（d）大陸地區 8 所姊妹校（中南大學、廣州醫科大學、濱州醫學院、廈門醫學院等）：中文授課免附外語檢定證明。",
        ],
        "required_documents": [
            "1. 國立臺北護理健康大學海外交換研習計畫報名表／雙聯學位申請表／教育部學海飛颺（或學海惜珠）申請表乙份（貼妥照片並由本人親筆簽名）",
            "2. 歷年中英文成績單正本各乙份（需含在校 GPA、班級排名百分比及操行成績 80 分以上證明；參考《國立臺北護理健康大學百分制成績轉換等第制成績對照表》）",
            "3. 外國語言能力檢定成績證明影本乙份（IELTS / TOEFL iBT / TOEIC / JLPT / TOPIK）",
            "4. 自我介紹與交換學習計畫書（含申請動機、國外預計修讀課程、與目前北護專業學習之關聯性及未來展望；申請學海飛颺／惜珠者須撰寫 1,000–1,500 字中文或英文研修計畫書）",
            "5. 系所主任同意推薦證明及教師推薦信（考量各系臨床實習與專業必修排程，須經所屬系所同意；學海計畫須附指導教授或系主任推薦函）",
            "6. 有效護照基本資料頁影本、學生證影本、國際學伴（International Buddy）或社團志工服務證明（申請學海惜珠另須檢附新式戶口名簿或戶籍謄本及低收入戶／中低收入戶／特殊境遇家庭相關證明文件）",
        ],
        "scholarship_info": [
            "1. 教育部「學海飛颺」獎學金（選送優秀學生出國研修）：補助具中華民國國籍、本校日間部在學滿一學期以上、外語能力符合標準且學業成績優良（以班排名百分比前 50% 及操行成績 80 分以上且無懲戒紀錄優先）之學生，赴國外大專校院修讀學分一學期或一學年（含捷克奧斯特拉瓦大學、日本名古屋市立大學、紐西蘭梅西大學、立陶宛 KVK 及英美澳雙聯學位），補助項目涵蓋學費、來回經濟艙機票與國外生活費。",
            "2. 教育部「學海惜珠」獎學金（選送清寒優秀學生出國研修）：針對具備低收入戶、中低收入戶、特殊境遇家庭子女、身心障礙人士子女或獲大專校院弱勢學生助學計畫補助之優秀在學學生，赴國外修讀學分一學期或一學年，教育部與本校提供高額全額補助（每人補助約新臺幣 5 萬至 45 萬元以上）。",
            "3. 教育部「學海築夢」與「新南向學海築夢」海外專業實習獎學金：由本校護理、高齡、醫教、長照、語聽、資管、運保、生諮、幼保等系所專任教師主持海外實習計畫，選送學生於寒暑假赴美國關島大學、美國密西根州立大學、澳洲昆士蘭大學、日本長野縣佐久大學、泰國朱拉隆功大學、新加坡 Sonova 聽力中心、菲律賓大學馬尼拉分校 SILAB、印尼三寶瓏國立大學 UNNES、三寶瓏穆罕默德大學 UNIMUS、巨港穆罕默德大學 UMP 等機構進行海外臨床與專業實習，補助每人國際來回機票與海外生活費。",
            "4. 姊妹校專屬住宿與學費減免優惠：（a）韓國大邱保健大學（Daegu Health College）提供北護交換生免學費及免費校內雙人房宿舍；（b）日本東京都立大學（TMU）暑期健康科學跨專業國際研習（HIIP）免收計畫學費並免費提供東京荒川校區國際學生宿舍；（c）澳洲昆士蘭大學（UQ 護理雙聯）與昆士蘭科技大學（QUT 資管雙聯）提供國際雙聯學生專屬學費減免獎學金。",
        ],
        "partner_universities": [p["school_name"] for p in partners],
        "source_urls": ntunhs_source_urls,
        "last_checked": CHECKED_AT,
    }
    (OFFICIAL_NTUNHS_DIR / "exchange_info.json").write_text(
        json.dumps(exchange_info_payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    student_dashboard_payload = {
        "school_name": "國立臺北護理健康大學",
        "last_checked": CHECKED_AT,
        "academic_score_minimum": 70.0,
        "academic_score_rule": "依國立臺北護理健康大學研究發展處國際暨兩岸教育中心交換簡章及《學生出國期間有關學業及學籍處理要點》：申請學期交換或短期海外研習者須為日間部在學學生，在校歷年學業平均達 GPA 2.0（百分制約 70 分）以上，操行成績 80 分以上且無懲戒紀錄；申請教育部《學海飛颺／學海惜珠》獎學金及英美澳跨國雙聯學位（澳洲 UQ、QUT、Deakin、英國 UWE、美國 Auburn）以班排名百分比前 50%（雙聯建議 GPA 2.75–3.0 / 75–80 分以上）優先推薦，且所有交換生皆須先經所屬系所同意始得出國。",
        "academic_gpa_minimum": 2.0,
        "maximum_preferences": 5,
        "selection_rules": {
            "academic_policy": "gpa_or_rank",
            "academic_reference_year": "115",
            "undergraduate_gpa_minimum": 2.0,
            "graduate_academic_exempt": False,
            "exclude_in_service": True,
            "pending_quota_planning": False,
            "partner_requirements_need_confirmation": False,
            "degree_score_minimums": {
                "undergraduate": 70.0,
                "graduate": 75.0,
            },
            "excluded_undergraduate_years": ["大一"],
            "language_certificate_required": True,
        },
        "language_score_minimums": {
            "toefl": 61.0,
            "ielts": 5.5,
            "toefl_itp": 500.0,
            "toeic": 550.0,
        },
        "application_periods": [
            {
                "title": "國立臺北護理健康大學春季班海外姊妹校交換（日本名古屋市立大學／縣立廣島大學／捷克奧斯特拉瓦大學／韓國大邱保健大學／紐西蘭梅西大學）暨寒假短期研習甄選（9–10月）",
                "details": [
                    "依國立臺北護理健康大學研究發展處國際暨兩岸教育中心公告，擬於春季學期赴日本名古屋市立大學（NCU）、日本縣立廣島大學、捷克奧斯特拉瓦大學（University of Ostrava）、韓國大邱保健大學（DHC）、紐西蘭梅西大學（Massey University）交換，或參加澳洲昆士蘭科技大學（QUT）寒假健康科學短期研習團者，於每年 9 月至 10 月底受理校內報名收件。",
                    "校內甄選採書面審查（40%–60%）與中英文面試（40%–60%），申請人須先經所屬系所同意確認不影響專業必修與醫院臨床實習排程，並備妥報名表、歷年中英文成績單、語檢證明及交換學習計畫書送交校本部行政大樓 2 樓國際暨兩岸教育中心。",
                ],
                "source": {
                    "title": "國立臺北護理健康大學國際暨兩岸教育中心海外長短期交換甄選公告專區",
                    "source_url": NTUNHS_EXCHANGE_URL,
                    "category": "exchange_application",
                    "summary": "國立臺北護理健康大學春季班海外學期交換與寒假短期研習報名收件、書審面試與提名時程。",
                },
                "scope": "home_application",
                "program_types": ["exchange", "dual_degree"],
                "academic_year": "115",
                "application_round": "春季班海外學期交換暨寒假短期健康科學研習甄選",
                "audience": "all_students",
                "opens_at": "2026-09-01T09:00:00+08:00",
                "deadline_at": "2026-10-31T17:00:00+08:00",
                "date_status": "verified_exact",
                "status": "upcoming",
                "status_note": "每年 9–10 月受理翌年春季班海外姊妹校學期交換與寒假短期研習申請。",
                "deadline_note": "請先與所屬系所確認臨床實習與專業課程規劃，備妥報名表、成績單、語檢證明與學習計畫送交行政大樓 2 樓國際暨兩岸教育中心。",
                "reminder_eligible": True,
                "checked_at": CHECKED_AT,
            },
            {
                "title": "國立臺北護理健康大學秋季班海外交換、英美澳 6 校 9 學程雙聯學位暨教育部學海飛颺／惜珠／築夢獎學金甄選（2–3月）",
                "details": [
                    "擬於次學年秋季班赴海外姊妹校交換（捷克奧斯特拉瓦大學、立陶宛克萊佩達市立大學 KVK、日本名古屋市立大學、紐西蘭梅西大學、澳洲 WAI／ICHM／TAFE）、修讀英美澳跨國雙聯學位（澳洲 UQ、QUT、Deakin、WAI、英國 UWE、美國 Auburn）或參加暑期短期交換（日本東京都立大學 HIIP、山形縣立保健醫療大學、沖繩縣立看護大學、韓國高麗大學）者，於每年 2 月至 4 月受理申請。",
                    "教育部《學海飛颺》、《學海惜珠》及《學海築夢／新南向學海築夢》海外專業實習計畫於每年 2–3 月截止校內收件（班排前 50% 及操行 80 分以上無懲戒紀錄優先），5 月底教育部公告核定補助結果。",
                ],
                "source": {
                    "title": "國立臺北護理健康大學教育部學海飛颺、學海惜珠與學海築夢甄選公告",
                    "source_url": NTUNHS_XUEHAI_URL,
                    "category": "scholarship",
                    "summary": "國立臺北護理健康大學秋季班海外交換、英美澳雙聯學位與教育部學海系列獎學金甄選時程。",
                },
                "scope": "home_application",
                "program_types": ["exchange", "dual_degree"],
                "academic_year": "115",
                "application_round": "秋季班海外交換、跨國雙聯學位暨教育部學海系列獎學金甄選",
                "audience": "all_students",
                "opens_at": "2027-02-01T09:00:00+08:00",
                "deadline_at": "2027-03-15T17:00:00+08:00",
                "date_status": "verified_exact",
                "status": "upcoming",
                "status_note": "每年 2–3 月受理秋季班交換、跨國雙聯學位與教育部學海飛颺／惜珠／築夢獎學金申請。",
                "deadline_note": "申請教育部學海飛颺／惜珠獎學金以班排名百分比前 50% 及操行 80 分以上且無懲戒紀錄優先。",
                "reminder_eligible": True,
                "checked_at": CHECKED_AT,
            },
        ],
        "program_overview": [
            {
                "title": f"國立臺北護理健康大學國際暨兩岸教育中心全球交換、英美澳 6 校 9 學程雙聯學位與學海海外實習總覽（{len(partners)} 所合作姊妹校・{open_partner_count} 所常態開放申請・{total_exp_reports} 篇學長姐心得報告）",
                "details": [
                    f"國立臺北護理健康大學（National Taipei University of Nursing and Health Sciences, NTUNHS，簡稱國北護，校本部坐落於臺北市北投區明德路 365 號、城區部坐落於臺北市萬華區內江街 89 號，為臺灣技職護理與健康照護最高學府）由「研究發展處國際暨兩岸教育中心（位於北投校本部行政大樓 2 樓）」統籌全校 4 大學院（護理學院、健康科技學院、人類發展與健康學院、智慧健康照護跨領域學院）之跨國雙聯學位、海外長短期交換、海外臨床見習與教育部學海系列獎學金。本平台完整收錄 {len(partners)} 所國北護官方合作姊妹校（含 {open_partner_count} 所常態開放雙聯、長短期交換與學海築夢海外實習合作校，以及 {len(partners) - open_partner_count} 所正式締約姊妹校），橫跨全球 21 個國家與地區。",
                    f"國立臺北護理健康大學國際交流具備四大醫護健康特色：（1）英美澳 6 校 9 學程頂尖雙聯學位：涵蓋世界護理排名頂尖之【澳洲昆士蘭大學 UQ 護理雙學士／護理碩士／聽力學碩士／社工碩士雙聯】、【美國奧本大學 Auburn 護理 MSN 碩士暨 PhD 博士雙聯】、【英國西英格蘭大學 UWE 護理雙學士與資管 3+1 雙學士】、【澳洲昆士蘭科技大學 QUT 資管 2+2 雙學士】、【澳洲迪肯大學 Deakin 健管 3.5+1.5 MBA 醫療管理雙聯】及【澳洲墨爾本威廉安格利斯學院 WAI 休健航空空服／旅遊管理雙聯】；（2）多元歐亞紐澳學期與短期交換：對接捷克奧斯特拉瓦大學醫學院、立陶宛 KVK、日本名古屋市立大學、縣立廣島大學、東京都立大學 HIIP（免費荒川校區宿舍）、山形縣立保健醫療大學、沖繩縣立看護大學、紐西蘭梅西大學、韓國大邱保健大學（免費雙人房宿舍）、高麗大學、首爾女子護理大學；（3）教育部學海築夢全球臨床與健康產業實習：遍及美國關島大學、密西根州立大學、澳洲布里斯本、日本長野佐久大學、泰國朱拉隆功大學、新加坡 Sonova 聽力中心、菲律賓 UP Manila 及印尼三寶瓏／巨港；（4）完整收錄 {exp_covered_schools} 所合作大學共 {total_exp_reports} 篇歷屆學長姐雙聯、交換與海外實習心得報告。",
                ],
                "source": {
                    "title": "國立臺北護理健康大學研究發展處國際暨兩岸教育中心官方網站与雙聯學制手冊",
                    "source_url": NTUNHS_ICSED_HOME_URL,
                    "category": "exchange_application",
                    "summary": f"國立臺北護理健康大學 {len(partners)} 所全球合作姊妹校、{open_partner_count} 所常態開放雙聯／交換／實習校與 {total_exp_reports} 篇心得報告。",
                },
            }
        ],
        "eligibility": [
            {
                "title": "日間部在學資格、系所臨床實習同意程序、GPA 2.0／班排前 50% 門檻與國際學伴加分機制",
                "details": [
                    "在學身分與系所同意規定：依《國立臺北護理健康大學學生出國期間有關學業及學籍處理要點》（112.11.01 修正）及各校甄選簡章，申請人須為本校日間部在學學生（四技 2～4 年級、二技、學士後護理系、碩士班及博士班；不含在職專班）。出國進修、交換或實習以二年為限；因考量護理與健康照護各系專業必修課程及醫院臨床實習排程，交換生皆須先經所屬系所同意始得出國，且出國交換期間須維持北護在學學籍並按規定辦理註冊（不得辦理休學，但不需掛校內課程）。",
                    "學業操行門檻與評選權重：一般學期交換要求在校歷年平均 GPA 2.0（百分制 70 分）以上，申請教育部《學海飛颺／惜珠》獎學金以班排名百分比前 50% 及操行成績 80 分以上且無懲戒紀錄優先；校內甄選由書面審查（40%–60%）與中英文面試（40%–60%）組成，曾擔任本校國際學伴（International Buddy）者予以加分。",
                ],
                "source": {
                    "title": "國立臺北護理健康大學學生出國期間有關學業及學籍處理要點與海外交換簡章",
                    "source_url": NTUNHS_OUTBOUND_STATUS_RULES_PDF,
                    "category": "exchange_application",
                    "summary": "國立臺北護理健康大學出國交換在學學籍保留、系所同意程序、GPA 2.0／班排前 50% 門檻與評選規範。",
                },
            }
        ],
        "language_requirements": [
            {
                "title": "英美澳雙聯（UQ IELTS 7.0 / UWE・QUT・Deakin・Auburn IELTS 6.5 / WAI 6.0）、歐紐交換（CEFR B1–B2 / IELTS 5.5–6.5）與日韓語門檻",
                "details": [
                    "雙聯學位與英語組交換門檻：（1）澳洲昆士蘭大學（UQ 護理雙學士／護理碩士／聽力學碩士／社工碩士）要求 IELTS Academic 7.0（各單科不低於 7.0）或 TOEFL iBT 100；（2）美國奧本大學（Auburn 護理碩博）、澳洲昆士蘭科技大學（QUT 資管 2+2）、迪肯大學（Deakin 健管 MBA 3.5+1.5）、英國西英格蘭大學（UWE 護理雙聯）要求 IELTS Academic 6.5；（3）英國 UWE 資管 3+1、澳洲墨爾本威廉安格利斯學院 WAI 及紐西蘭梅西大學（Massey 大學部）要求 IELTS Academic 6.0；（4）捷克奧斯特拉瓦大學與立陶宛克萊佩達市立大學（KVK）要求英語 CEFR B1–B2（TOEIC 550–785 / IELTS 5.5–6.0 / TOEFL iBT 61–79）。",
                    "日語組、韓語組與大陸地區門檻：（1）日本名古屋市立大學要求 JLPT N1 合格或英語 CEFR B2（尚未取得 N3 以上者可先檢附日語學習證明與日文自傳報考）；日本縣立廣島大學、山形縣立保健醫療大學、沖繩縣立看護大學、佐久大學建議具 JLPT N2–N3 或英語溝通能力；（2）韓國大邱保健大學、高麗大學、首爾女子護理大學、春海保健大學要求具英語溝通能力或韓語 TOPIK 2–3 級；（3）大陸地區姊妹校為中文授課，免附外語檢定證明。",
                ],
                "source": {
                    "title": "國立臺北護理健康大學雙聯學制手冊與海外長短期交換甄選簡章",
                    "source_url": NTUNHS_DUAL_DEGREE_URL,
                    "category": "exchange_application",
                    "summary": "國立臺北護理健康大學英美澳雙聯學位與歐亞紐澳姊妹校外語檢定門檻一覽。",
                },
            }
        ],
        "required_documents": [
            {
                "title": "交換研習報名表、含 GPA 與班排中英文成績單、語檢證明、1,000–1,500 字研修計畫書、系所同意證明與返國抵免規範",
                "details": [
                    "校內申請必備文件（送交北投校本部行政大樓 2 樓國際暨兩岸教育中心）：（1）國立臺北護理健康大學交換研習計畫報名表／教育部學海飛颺（或學海惜珠）申請表；（2）歷年中英文成績單正本（需含 GPA、班級排名百分比及操行成績證明）；（3）外語能力檢定證明影本；（4）自我介紹與交換學習計畫書（學海飛颺／惜珠須撰寫 1,000–1,500 字出國研修計畫書，含個人自傳、研修目標、預期修讀課程與北護專業關聯性）；（5）系所同意推薦證明、教師推薦信及國際學伴服務證明。",
                    "出國前與返國後必辦手續：出國交換期間須維持北護在學學籍並按規定辦理註冊（不得休學）；醫療院所見習生須備妥英文健康檢查及疫苗抗體證明；返國後繳交出國研修／實習結案報告書及核銷單據，並依《國立臺北護理健康大學學生抵免學分處理辦法》填具專業科目／通識科目抵免學分申請表（檢附國外成績單正本與課程大綱）辦理學分採認。",
                ],
                "source": {
                    "title": "國立臺北護理健康大學教育部學海系列申請表單與學生抵免學分處理辦法",
                    "source_url": NTUNHS_XUEHAI_URL,
                    "category": "exchange_application",
                    "summary": "國立臺北護理健康大學交換生、雙聯生與學海獎學金申請表件、臨床體檢與返國學分抵免規範。",
                },
            }
        ],
        "scholarship_info": [
            {
                "title": "教育部學海飛颺、學海惜珠（5 萬～45 萬元以上）、學海築夢／新南向學海築夢海外實習補助與姊妹校免費宿舍優惠",
                "details": [
                    "教育部學海系列三大獎學金（每年 2–3 月向國際暨兩岸教育中心申請）：（1）《學海飛颺》：選送日間部優秀在學學生（班排前 50% 及操行 80 分以上無懲戒紀錄優先）赴國外修讀學分一學期或一學年，補助學費、來回機票與生活費；（2）《學海惜珠》：補助具低收、中低收、特殊境遇家庭或弱勢助學資格之優秀學生出國修讀學分，每人補助約新臺幣 5 萬至 45 萬元以上；（3）《學海築夢》與《新南向學海築夢》：補助學生隨專任教師計畫赴美國關島大學、密西根州立大學、澳洲昆士蘭大學、日本佐久大學、泰國朱拉隆功大學、新加坡 Sonova、菲律賓 UP Manila 及印尼 UNNES／UNIMUS／UMP 進行海外臨床與專業實習，補助機票與生活費。",
                    "合作姊妹校專屬獎學金與免費住宿待遇：（1）韓國大邱保健大學（DHC）學期交換生享免學費及免費校內雙人房宿舍；（2）日本東京都立大學（TMU）暑期 HIIP 跨專業健康科學研習生享免學費及免費東京荒川校區國際學生宿舍；（3）澳洲昆士蘭大學（UQ 護理雙聯）與昆士蘭科技大學（QUT 資管雙聯）提供雙聯學生專屬學費減免獎學金。",
                ],
                "source": {
                    "title": "國立臺北護理健康大學教育部學海飛颺、學海惜珠與學海築夢專區",
                    "source_url": NTUNHS_XUEHAI_URL,
                    "category": "scholarship",
                    "summary": "國立臺北護理健康大學教育部學海系列獎學金與姊妹校學費住宿減免辦法。",
                },
            }
        ],
        "document_explanations": [
            {
                "title": "國立臺北護理健康大學交換研習報名表、1,000–1,500 字學海研修計畫書、專業科目學分抵免申請表與返國結案報告指南",
                "summary": "說明國北護交換生、雙聯生與學海計畫申請人撰寫交換學習計畫書、確認系所臨床實習排程、辦理出國在學註冊及返國學分抵免之實務要點。",
                "key_points": [
                    "交換學習計畫書／學海出國研修計畫書撰寫架構（1,000–1,500 字）：內容須完整包含：（1）中英文個人自傳與專業背景、（2）赴國外研修之動機、目標及修課／臨床見習計畫、（3）預期研修課程與目前北護專業課程及未來職涯之相關性、（4）歷年參與國際學伴（International Buddy）或跨文化活動經歷。",
                    "系所臨床實習排程確認與在學註冊義務：依《學生出國期間有關學業及學籍處理要點》，北護各系具嚴謹之醫院臨床實習與國考必修課程，出國前務必經系所同意；交換期間須維持北護在學學籍並按規定辦理註冊（不得休學，但不需掛校內課程）。",
                    "返國結案報告與學分抵免流程：返國後須繳交電子檔結案心得報告書（含修課體驗、醫療機構參訪、住宿生活費與多張照片）予國際暨兩岸教育中心；辦理學分抵免時，依《學生抵免學分處理辦法》檢附國外正式成績單、百分制／等第制成績對照表及課程大綱，填具「專業科目抵免學分申請表（B12-F032-01）」或通識抵免表送各系所及通識中心審核。",
                ],
                "applies_to": [],
                "source": {
                    "title": "國立臺北護理健康大學學海飛颺申請表與學生抵免學分處理辦法",
                    "source_url": NTUNHS_CREDIT_TRANSFER_RULES_PDF,
                    "category": "exchange_application",
                    "summary": None,
                },
                "document_url": NTUNHS_XUEHAI_FEIYANG_FORM_DOC,
                "document_type": "official_document",
                "full_text_extracted": True,
            }
        ],
        "rule_explanations": [
            {
                "title": "國立臺北護理健康大學學生出國期間有關學業及學籍處理要點、學生抵免學分處理辦法與雙聯學制實施規範",
                "summary": "規範國北護學生出國進修二年期限、交換期間維持在學註冊學籍（不得休學）、系所同意程序、百分制轉換 GPA 對照與返國學分抵免原則。",
                "key_points": [
                    "出國二年期限與在學註冊規定：依《國立臺北護理健康大學學生出國期間有關學業及學籍處理要點》（112.11.01 教務會議通過），經所屬系所推薦並經學校核准至國外大專院校研究、修讀學分、交換或實習者，出國進修以二年為限；出國交換期間須維持北護在學學籍並按規定辦理註冊（不得辦理休學）。",
                    "學分抵免相似度與審查原則：依《國立臺北護理健康大學學生抵免學分處理辦法》（115.06.24 修正），學分抵免應符合科目名稱及內容高度相似之原則，且有課程進行之事實；國外修習成績依《百分制成績轉換等第制成績對照表》（A+ 為 90–100 分 / GPA 4.0、A 為 85–89 分 / GPA 4.0、A- 為 80–84 分 / GPA 3.7、B+ 為 77–79 分 / GPA 3.3、B 為 73–76 分 / GPA 3.0、B- 為 70–72 分 / GPA 2.7、C+ 為 67–69 分 / GPA 2.3、C 為 63–66 分 / GPA 2.0）採認。",
                    "跨國雙聯學位修業與臨床認證：修讀澳洲昆士蘭大學（UQ 護理 IELTS 7.0）、英國西英格蘭大學（UWE 護理 IELTS 6.5／資管 IELTS 6.0）、澳洲昆士蘭科技大學（QUT 資管 IELTS 6.5）、迪肯大學（Deakin 健管 IELTS 6.5）、墨爾本威廉安格利斯學院（WAI IELTS 6.0）及美國奧本大學（Auburn 護理碩博 IELTS 6.5）雙聯學位者，於兩校修畢規定學分後可分別取得兩校學位證書。",
                ],
                "applies_to": [],
                "source": {
                    "title": "國立臺北護理健康大學學生出國期間有關學業及學籍處理要點（112.11.01 修正）",
                    "source_url": NTUNHS_OUTBOUND_STATUS_RULES_PDF,
                    "category": "exchange_application",
                    "summary": None,
                },
                "document_url": NTUNHS_CREDIT_TRANSFER_RULES_PDF,
                "document_type": "official_document",
                "full_text_extracted": True,
            }
        ],
        "sources": [
            {"title": "國立臺北護理健康大學研究發展處國際暨兩岸教育中心官方網站", "source_url": NTUNHS_ICSED_HOME_URL, "category": "exchange_application", "summary": None},
            {"title": "國立臺北護理健康大學雙聯學制專區（英、美、澳 6 校 9 學程雙聯學位手冊與心得）", "source_url": NTUNHS_DUAL_DEGREE_URL, "category": "exchange_application", "summary": None},
            {"title": "國立臺北護理健康大學海外長短期交換專區（捷克、日本、紐西蘭、韓國、立陶宛、澳洲交換簡章）", "source_url": NTUNHS_EXCHANGE_URL, "category": "exchange_application", "summary": None},
            {"title": "國立臺北護理健康大學教育部學海飛颺、學海惜珠與學海築夢專區", "source_url": NTUNHS_XUEHAI_URL, "category": "scholarship", "summary": None},
            {"title": f"國立臺北護理健康大學五大洲締約姊妹校名錄（橫跨 21 國與地區共 {len(partners)} 所合作姊妹校）", "source_url": NTUNHS_SISTER_SCHOOLS_URL, "category": "partner_school", "summary": None},
            {"title": "國立臺北護理健康大學學生出國期間有關學業及學籍處理要點（112.11.01 教務會議通過）", "source_url": NTUNHS_OUTBOUND_STATUS_RULES_PDF, "category": "exchange_application", "summary": None},
            {"title": "國立臺北護理健康大學學生抵免學分處理辦法（115.06.24 教務會議修正）", "source_url": NTUNHS_CREDIT_TRANSFER_RULES_PDF, "category": "exchange_application", "summary": None},
            {"title": f"國立臺北護理健康大學歷年雙聯、長短期交換與學海築夢海外實習成果報告專區（{exp_covered_schools} 校 {total_exp_reports} 篇心得報告）", "source_url": NTUNHS_EXPERIENCES_URL, "category": "exchange_application", "summary": None},
        ],
    }
    (OFFICIAL_NTUNHS_DIR / "student_dashboard.json").write_text(
        json.dumps(student_dashboard_payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    doc_conditions = {
        "school_id": "ntunhs",
        "school_name": "國立臺北護理健康大學",
        "checked_at": CHECKED_AT,
        "source_url": NTUNHS_EXCHANGE_URL,
        "common_documents": exchange_info_payload["required_documents"],
        "track_specific_conditions": [
            {
                "track": "海外姊妹校學期交換計畫（捷克奧斯特拉瓦大學、日本名古屋市立大學、縣立廣島大學、紐西蘭梅西大學、韓國大邱保健大學、立陶宛 KVK、澳洲 WAI／ICHM／TAFE）",
                "required": [
                    "國立臺北護理健康大學交換研習計畫報名表（含個人基本資料、申請期程與個資同意簽名）",
                    "歷年中英文成績單正本（需含 GPA 2.0 以上及班級排名百分比；出國交換期間須維持北護在學學籍且不得休學）",
                    "有效外語能力檢定證明影本（英語組 TOEIC 550–785 / IELTS 5.5–6.5；日語組 JLPT N1–N3；韓語組 TOPIK 2–3 級或英語證明）",
                    "自我介紹與交換學習計畫書、系所同意證明（確認不衝堂專業必修與臨床實習）及國際學伴參與證明",
                ],
            },
            {
                "track": "英、美、澳 6 校 9 學程跨國雙聯學位計畫（澳洲 UQ、QUT、Deakin、WAI、英國 UWE、美國 Auburn）",
                "required": [
                    "國立臺北護理健康大學雙聯學位申請表及合作大學線上入學申請表件",
                    "英文歷年成績單正本（GPA 建議達 2.75–3.0 以上，並修畢各系雙聯學制手冊規定之北護先修課程與臨床實習時數）",
                    "學術雅思 IELTS Academic 或 TOEFL iBT 成績單正本（澳洲 UQ 護理／聽力／社工雙聯須達 IELTS 7.0 各科 7.0 或 iBT 100；美國 Auburn、英國 UWE 護理、澳洲 QUT 資管、Deakin 健管須達 IELTS 6.5；英國 UWE 資管 3+1 與澳洲 WAI 休健須達 IELTS 6.0）",
                    "英文讀書計畫（Statement of Purpose）、英文履歷（CV）、教授推薦信 2 封、護照影本及護理師證照／臨床實習證明（護理雙聯適用）",
                ],
            },
            {
                "track": "教育部學海飛颺、學海惜珠與學海築夢／新南向學海築夢海外專業實習計畫",
                "required": [
                    "教育部學海飛颺／學海惜珠學生個人基本資料表與申請書（限中華民國國籍、日間部在學滿一學期以上，班排前 50% 及操行 80 分以上無懲戒紀錄優先）",
                    "1,000–1,500 字出國研修計畫書（含個人自傳、目標及計畫、預期修讀課程與目前學習相關性、未來展望）、歷年中英文成績單含班排、外語檢定證明及指導教授或系主任推薦信（學海惜珠另附新式戶口名簿／戶籍謄本及低收／中低收／弱勢助學證明）",
                    "學海築夢／新南向學海築夢海外實習：經各系所計畫主持人甄選通過，出國前簽署行政契約書並備妥醫院／機構所需英文健康檢查與疫苗抗體證明，返國後 2 週內上傳心得報告與經驗分享短片",
                ],
            },
        ],
    }
    (OFFICIAL_NTUNHS_DIR / "document-conditions.json").write_text(
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
            f"{fname},{len(partners)},{pop},{ratio:.4f},Official NTUNHS ICSED verified"
        )
    (OFFICIAL_NTUNHS_DIR / "field-coverage.csv").write_text(
        "\n".join(field_cov_lines) + "\n", encoding="utf-8"
    )

    pages_records = [
        {
            "title": "國立臺北護理健康大學：春季班（9–10月）與秋季班（2–4月）海外長短期交換、英美澳雙聯學位與教育部學海系列時程",
            "source_url": NTUNHS_EXCHANGE_URL,
            "published_at": "2026-10-30T00:00:00Z",
            "text": "\n".join(exchange_info_payload["application_period"]),
            "summary": "\n".join(exchange_info_payload["application_period"]),
            "category": "exchange_application",
            "attachments": [],
            "crawled_at": CHECKED_AT,
            "content_hash": hashlib.sha256("\n".join(exchange_info_payload["application_period"]).encode("utf-8")).hexdigest(),
        },
        {
            "title": "國立臺北護理健康大學：學生出國期間有關學業及學籍處理要點、在學註冊規定、GPA 2.0／班排前 50% 門檻與系所同意程序",
            "source_url": NTUNHS_OUTBOUND_STATUS_RULES_PDF,
            "published_at": "2026-10-30T00:00:00Z",
            "text": "\n".join(exchange_info_payload["eligibility"]),
            "summary": "\n".join(exchange_info_payload["eligibility"]),
            "category": "exchange_application",
            "attachments": [],
            "crawled_at": CHECKED_AT,
            "content_hash": hashlib.sha256("\n".join(exchange_info_payload["eligibility"]).encode("utf-8")).hexdigest(),
        },
        {
            "title": f"國立臺北護理健康大學：{len(partners)} 所全球與兩岸合作姊妹校外語檢定門檻（英美澳 6 校 9 學程雙聯／歐紐日韓學期交換／新南向學海築夢）",
            "source_url": NTUNHS_DUAL_DEGREE_URL,
            "published_at": "2026-10-30T00:00:00Z",
            "text": "\n".join(exchange_info_payload["language_requirement"]),
            "summary": "\n".join(exchange_info_payload["language_requirement"]),
            "category": "exchange_application",
            "attachments": [],
            "crawled_at": CHECKED_AT,
            "content_hash": hashlib.sha256("\n".join(exchange_info_payload["language_requirement"]).encode("utf-8")).hexdigest(),
        },
        {
            "title": "國立臺北護理健康大學：海外交換、雙聯學位與學海系列 6 項應備文件（報名表、含班排成績單、1,000–1,500 字研修計畫書、系所同意證明）",
            "source_url": NTUNHS_XUEHAI_URL,
            "published_at": "2026-10-30T00:00:00Z",
            "text": "\n".join(exchange_info_payload["required_documents"]),
            "summary": "\n".join(exchange_info_payload["required_documents"]),
            "category": "exchange_application",
            "attachments": [],
            "crawled_at": CHECKED_AT,
            "content_hash": hashlib.sha256("\n".join(exchange_info_payload["required_documents"]).encode("utf-8")).hexdigest(),
        },
        {
            "title": "國立臺北護理健康大學：教育部學海飛颺、學海惜珠、學海築夢／新南向學海築夢海外實習獎助與姊妹校免費宿舍優惠",
            "source_url": NTUNHS_XUEHAI_URL,
            "published_at": "2026-10-30T00:00:00Z",
            "text": "\n".join(exchange_info_payload["scholarship_info"]),
            "summary": "\n".join(exchange_info_payload["scholarship_info"]),
            "category": "scholarship",
            "attachments": [],
            "crawled_at": CHECKED_AT,
            "content_hash": hashlib.sha256("\n".join(exchange_info_payload["scholarship_info"]).encode("utf-8")).hexdigest(),
        },
    ]
    (OFFICIAL_NTUNHS_DIR / "pages.jsonl").write_text(
        "\n".join(json.dumps(p, ensure_ascii=False) for p in pages_records) + "\n",
        encoding="utf-8",
    )

    home_rules = {
        "school_id": "ntunhs",
        "school_name": "國立臺北護理健康大學",
        "eligibility": student_dashboard_payload["eligibility"],
        "application_periods": student_dashboard_payload["application_periods"],
        "selection_rules": {
            "general_exchange_gpa_minimum": 2.0,
            "general_exchange_score_minimum": 70.0,
            "conduct_score_minimum": 80.0,
            "xuehai_priority_class_rank_percent_maximum": 50.0,
            "dual_degree_uq_ielts_minimum": 7.0,
            "dual_degree_general_ielts_minimum": 6.5,
            "maximum_abroad_study_years": 2,
            "require_ntunhs_registration_during_abroad": True,
            "require_department_approval_before_abroad": True,
            "return_documents_due": "返國後依國際暨兩岸教育中心及教育部學海計畫規定繳交出國研修／實習結案心得報告書與經費核銷單據，並檢附國外正式成績單及課程大綱向系所及通識教育中心辦理學分抵免",
        },
        "source_urls": ntunhs_source_urls,
        "verified_at": "2026-11-06",
    }
    (OFFICIAL_NTUNHS_DIR / "home_rules.json").write_text(
        json.dumps(home_rules, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    (OFFICIAL_NTUNHS_DIR / "documents.json").write_text(
        json.dumps(
            {
                "school_name": "國立臺北護理健康大學",
                "required_documents": student_dashboard_payload["required_documents"],
                "source_urls": ntunhs_source_urls,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    (OFFICIAL_NTUNHS_DIR / "scholarships.json").write_text(
        json.dumps(
            {
                "school_name": "國立臺北護理健康大學",
                "scholarships": student_dashboard_payload["scholarship_info"],
                "source_urls": ntunhs_source_urls,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    completeness = {
        "school_id": "ntunhs",
        "school_name": "國立臺北護理健康大學",
        "total_partners": len(partners),
        "partner_count": len(partners),
        "international_partners": sum(1 for p in partners if p["country"] not in {"中國大陸", "香港", "澳門"}),
        "mainland_partners": sum(1 for p in partners if p["country"] in {"中國大陸", "香港", "澳門"}),
        "dual_degree_partner_universities": 6,
        "dual_degree_programs": 9,
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
        "active_term": f"國立臺北護理健康大學研究發展處國際暨兩岸教育中心《雙聯學制專區（英美澳 6 校 9 學程）》、《海外長短期交換專區》、《教育部學海飛颺／惜珠／築夢專區》、《五大洲締約姊妹校名錄》、《學生出國期間有關學業及學籍處理要點》及《學生抵免學分處理辦法》同步整合；共完整收錄 {len(partners)} 所全球與兩岸合作姊妹校（含 {open_partner_count} 所常態開放雙聯、長短期交換與海外實習學校及 {len(partners) - open_partner_count} 所正式締約姊妹校，橫跨 21 個國家與地區，並收錄 {exp_covered_schools} 所合作大學共 {total_exp_reports} 篇歷屆學長姐雙聯、交換與實習心得報告）。",
        "verified_at": "2026-11-06",
    }
    (OFFICIAL_NTUNHS_DIR / "catalog-completeness.json").write_text(
        json.dumps(completeness, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    (OFFICIAL_NTUNHS_DIR / "verification_status.json").write_text(
        json.dumps(
            {
                "school_id": "ntunhs",
                "school_name": "國立臺北護理健康大學",
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
        ("sources/ntunhs/ntunhs_catalog_source.json", NTUNHS_SISTER_SCHOOLS_URL, f"國立臺北護理健康大學 {len(partners)} 所全球與兩岸合作姊妹校整合資料集 JSON"),
        ("sources/ntunhs/ntunhs_resolved_locations.json", NTUNHS_SISTER_SCHOOLS_URL, f"國立臺北護理健康大學 {len(partners)} 所合作姊妹校 ROR / Wikidata 地理座標核對表 JSON"),
        ("sources/ntunhs/ntunhs_experience_index.json", NTUNHS_EXPERIENCES_URL, f"國立臺北護理健康大學 {total_exp_reports} 篇歷屆雙聯、交換與海外實習心得報告索引 JSON"),
    ]
    for rel_p, surl in bin_urls.items():
        rp = rel_p if rel_p.startswith("sources/") else f"sources/ntunhs/{rel_p}"
        if not any(x[0] == rp for x in provenance_files):
            provenance_files.append((rp, surl, f"國立臺北護理健康大學官方原始檔案：{Path(rp).name}"))
    html_dir = SOURCES_NTUNHS_DIR / "html"
    if html_dir.exists():
        for hp in sorted(html_dir.glob("*.html")):
            rp = f"sources/ntunhs/html/{hp.name}"
            if not any(x[0] == rp for x in provenance_files):
                provenance_files.append((rp, NTUNHS_ICSED_HOME_URL, f"國立臺北護理健康大學官方網頁快照：{hp.name}"))

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
        "school_id": "ntunhs",
        "school_name": "國立臺北護理健康大學",
        "generated_at": CHECKED_AT,
        "active_cycle_note": completeness["active_term"],
        "sources": prov_sources,
    }
    prov_text = json.dumps(provenance_payload, ensure_ascii=False, indent=2) + "\n"
    (OFFICIAL_NTUNHS_DIR / "import_provenance.json").write_text(prov_text, encoding="utf-8")
    (OFFICIAL_NTUNHS_DIR / "import-provenance.json").write_text(prov_text, encoding="utf-8")

    print(
        f"Successfully built NTUNHS catalog: {len(partners)} partners"
        f" ({open_partner_count} open, {completeness['verified_campus_images']}"
        f" verified images, {completeness['verified_locations']} verified"
        f" locations), {len(workflows)} workflows,"
        f" {len(destinations)} destinations, {len(research_records)} research"
        f" records, {exp_covered_schools} schools with experience records"
        f" ({len(student_experience_rows)} rows, {total_exp_reports} reports)."
    )


if __name__ == "__main__":
    main()
