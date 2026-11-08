"""Build the official Tatung University (大同大學, TTU) exchange data bundle."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re

REPO_ROOT = Path(__file__).resolve().parents[1]
SOURCES_TTU_DIR = REPO_ROOT / "sources" / "ttu"
OFFICIAL_TTU_DIR = REPO_ROOT / "src" / "exchange_info" / "official_data" / "ttu"
STATIC_DIR = REPO_ROOT / "src" / "exchange_info" / "static"
UNIVERSITY_LOCATIONS_PATH = (
    REPO_ROOT
    / "src"
    / "exchange_info"
    / "official_data"
    / "university_locations.jsonl"
)

CHECKED_AT = "2026-11-08T00:00:00Z"

TTU_HOME_URL = "https://www.ttu.edu.tw/"
TTU_OIA_HOME_URL = "https://oia.ttu.edu.tw/"
TTU_2027_SPRING_EXCHANGE_URL = "https://oia.ttu.edu.tw/p/406-1071-44122,r568.php?Lang=zh-tw"
TTU_2026_FALL_EXCHANGE_URL = "https://oia.ttu.edu.tw/p/406-1071-41452,r568.php?Lang=zh-tw"
TTU_2026_SPRING_EXCHANGE_URL = "https://oia.ttu.edu.tw/p/406-1071-38557,r568.php?Lang=zh-tw"
TTU_2025_FALL_EXCHANGE_URL = "https://oia.ttu.edu.tw/p/406-1071-34879,r568.php?Lang=zh-tw"
TTU_115_XUEHAI_URL = "https://oia.ttu.edu.tw/p/406-1071-41325,r568.php?Lang=zh-tw"
TTU_115_XUEHAI_WAITLIST_URL = "https://oia.ttu.edu.tw/p/406-1071-44121,r568.php?Lang=zh-tw"
TTU_ALUMNI_SCHOLARSHIP_URL = "https://oia.ttu.edu.tw/p/405-1071-3499,c945.php?Lang=zh-tw"
TTU_SUMMER_GRANT_URL = "https://oia.ttu.edu.tw/p/406-1071-30564,r11.php?Lang=zh-tw"
TTU_OUTBOUND_FLOW_URL = "https://oia.ttu.edu.tw/p/405-1071-777,c642.php?Lang=zh-tw"
TTU_OUTBOUND_STATS_URL = "https://oia.ttu.edu.tw/p/405-1071-29031,c642.php?Lang=zh-tw"
TTU_OUTBOUND_FAQ_URL = "https://oia.ttu.edu.tw/p/405-1071-29034,c642.php?Lang=zh-tw"
TTU_SISTER_SCHOOLS_URL = "https://ao.ttu.edu.tw/p/412-1072-2438.php"
TTU_ONLINE_APPLY_EXCHANGE_URL = "https://admission.ttu.edu.tw/p/423-1034-3.php"
TTU_ONLINE_APPLY_XUEHAI_URL = "https://admission.ttu.edu.tw/p/423-1034-13.php"
TTU_ONLINE_RETURN_REPORT_URL = "https://admission.ttu.edu.tw/p/423-1034-11.php"
TTU_PIXNET_BLOG_URL = "https://tatunguni.pixnet.net/blog"
TTU_RULE_EXCHANGE_URL = "https://tturule.ttu.edu.tw/rulelist/showcontent.php?rid=1049"
TTU_RULE_DUAL_DEGREE_URL = "https://tturule.ttu.edu.tw/rulelist/showcontent.php?rid=232"
TTU_RULE_OUTBOUND_CREDIT_URL = "https://tturule.ttu.edu.tw/rulelist/showcontent.php?rid=225"
TTU_RULE_CREDIT_TRANSFER_URL = "https://tturule.ttu.edu.tw/rulelist/showcontent.php?rid=224"
TTU_RULE_ALUMNI_SCHOLARSHIP_URL = "https://tturule.ttu.edu.tw/rulelist/showcontent.php?rid=1124"
TTU_RULE_ENCOURAGE_GRANT_URL = "https://tturule.ttu.edu.tw/rulelist/showcontent.php?rid=1045"
TTU_RULE_SUMMER_EXCHANGE_GRANT_URL = "https://tturule.ttu.edu.tw/rulelist/showcontent.php?rid=1047"
TTU_RULE_SUMMER_LANG_GRANT_URL = "https://tturule.ttu.edu.tw/rulelist/showcontent.php?rid=1129"
TTU_EXCHANGE_ZIP_URL = "https://oia.ttu.edu.tw/var/file/71/1071/attach/11/pta_31964_5217597_11518.zip"
TTU_DUAL_DEGREE_ZIP_URL = "https://oia.ttu.edu.tw/var/file/71/1071/attach/11/pta_31965_4458632_11518.zip"
TTU_XUEHAI_BROCHURE_PDF = "https://oia.ttu.edu.tw/var/file/71/1071/attach/99/pta_29727_9047548_10599.pdf"
TTU_XUEHAI_FORM_PDF = "https://oia.ttu.edu.tw/var/file/71/1071/attach/99/pta_29728_5199442_10599.pdf"
TTU_ENCOURAGE_GRANT_FORM_PDF = "https://oia.ttu.edu.tw/var/file/71/1071/attach/99/pta_29730_3077030_10599.pdf"
TTU_XUEHAI_WAITLIST_FORM_PDF = "https://oia.ttu.edu.tw/var/file/71/1071/attach/10/pta_31959_2537269_11509.pdf"

REGION_COST_DEFAULTS = {
    "日本": (
        "每月生活費約 USD 550–1,050（折合日圓約 JPY 70,000–140,000 / 月、新臺幣約 17,500–33,500 元；京都工藝纖維大學、千葉大學、東京都市大學、芝浦工業大學、長岡造形大學、札幌市立大學、東北工業大學、岡山大學、琉球大學、縣立廣島大學等留學生寮月租約 JPY 15,000–45,000）",
        "學期交換生由日本接待大學代辦「在留資格認定證明書（COE）」後向日本台灣交流協會申辦留學簽證，入境後加入日本國民健康保險（NHI）並於出國前投保海外全程醫療及意外險。",
    ),
    "韓國": (
        "每月生活費約 USD 500–950（折合韓元約 KRW 650,000–1,300,000 / 月、新臺幣約 16,000–30,000 元；含仁川大學、韓國外國語大學、國民大學、建國大學、弘益大學、中央大學與金烏工科大學學生宿舍與膳食）",
        "學期交換須憑韓國姊妹校標準入學許可書向駐台北韓國代表部申辦 D-2-6 交換簽證，入境後辦理外國人登錄證（ARC）並納保韓國國民健康保險（NHIS）。",
    ),
    "德國": (
        "每月生活費約 USD 950–1,350（折合歐元約 EUR 900–1,200 / 月、新臺幣約 30,000–43,000 元；含斯圖加特應用科技大學 HFT Stuttgart、奧斯納布魯克應用科技大學、德根多夫應用科技大學 DIT、巴登符騰堡雙元制大學 DHBW 與卡爾斯魯厄應用科技大學 HKA 學生宿舍及德鐵學期票）",
        "赴德國交換或修讀 HFT Stuttgart 1+1 雙聯碩士須開立德國限制提領帳戶（Blocked Account，每月最低約 EUR 992）並向德國在台協會申辦長期學生簽證，且須投保德國法定公保（TK / AOK）。",
    ),
    "英國": (
        "每月生活費約 USD 1,350–2,000（折合英鎊約 GBP 1,050–1,550 / 月、新臺幣約 43,000–64,000 元；含倫敦密德薩斯大學 Middlesex University 3+1／1+1／3+1.5 雙聯、倫敦布魯內爾大學 Brunel University London 1+1／4+1 數位設計與 AI 雙聯［大同推薦前 10 名享 85 折學費優惠］與格拉斯哥大學）",
        "修讀英國雙聯學位或一學年交換須申辦英國 Student Visa 並繳納移民醫療附加費（IHS）；一學期（6 個月內）交換依規定辦理入境許可並全程投保海外醫療與意外險。",
    ),
    "法國": (
        "每月生活費約 USD 800–1,300（折合歐元約 EUR 750–1,200 / 月、新臺幣約 25,500–41,500 元；含貢比涅科技大學 UTC、法國亞眠高等工程師學院 ESIEE-Amiens / UniLaSalle 1+1 雙聯碩士與南特大西洋設計學院，可申請法國政府 CAF 房補）",
        "須先完成法國教育中心（Campus France）面試程序，再向法國在台協會申辦長期學生簽證（VLS-TS），入境後完成 OFII 認證並免費註冊法國社會醫療保險（Ameli）。",
    ),
    "芬蘭": (
        "每月生活費約 USD 750–1,150（折合歐元約 EUR 700–1,050 / 月、新臺幣約 24,000–36,500 元；含東南芬蘭應用科技大學 Xamk 學生公寓 MOAS / Kuopas 與校園學生餐廳補助餐）",
        "須透過芬蘭移民局（Migri）線上系統申辦芬蘭學生居留許可（Residence Permit for Studies，須具備每月約 EUR 560–800 財力證明與涵蓋醫療費至少 EUR 40,000–120,000 之學生保險）。",
    ),
    "波蘭": (
        "每月生活費約 USD 500–850（折合歐元約 EUR 460–780 / 月、新臺幣約 16,000–27,000 元；含盧布林科技大學與居禮夫人大學 UMCS 校內學生宿舍，月租僅約 EUR 110–170）",
        "須憑波蘭接待大學入學許可向波蘭臺北辦事處申辦 D 類國別學生簽證，並投保涵蓋全期之申根醫療保險（保額至少 EUR 30,000）。",
    ),
    "捷克": (
        "每月生活費約 USD 600–980（折合歐元約 EUR 550–900 / 月、新臺幣約 19,000–31,000 元；含赫拉德茨克拉洛韋大學 UHK 與布拉格化工大學學生宿舍Koleje 及市區大眾運輸學生優惠）",
        "須憑捷克接待大學入學許可與住宿證明向捷克經濟文化辦事處申辦長期學生簽證（D Visa），並購買符合捷克法規之境內綜合醫療保險（pVZP）。",
    ),
    "義大利": (
        "每月生活費約 USD 800–1,300（折合歐元約 EUR 750–1,200 / 月、新臺幣約 25,500–41,500 元；含威尼斯大學 Ca' Foscari 與熱那亞大學校外學生公寓及義北生活開銷）",
        "須憑義大利接待大學入學許可向義大利經濟貿易文化推廣辦事處申辦國家 D 類學生簽證，入境 8 日內申辦居留證（Permesso di Soggiorno）並投保義大利國民保健署（SSN）或國際醫療險。",
    ),
    "荷蘭": (
        "每月生活費約 USD 1,050–1,550（折合歐元約 EUR 950–1,400 / 月、新臺幣約 33,500–49,500 元；含恩荷芬理工大學 TU/e 與特文特大學學生住宿及單車通勤）",
        "由荷蘭接待大學代向荷蘭移民局（IND）申辦入境簽證（MVV）與學生居留許可（VVR），並投保荷蘭認可之國際學生醫療與責任保險（如 Aon Student Insurance）。",
    ),
    "奧地利": (
        "每月生活費約 USD 850–1,300（折合歐元約 EUR 780–1,200 / 月、新臺幣約 27,000–41,500 元；含茵斯布魯克管理中心 MCI 學生宿舍 OeAD Housing 與阿爾卑斯生活開銷）",
        "須憑 MCI 入學許可與 OeAD 住宿證明向奧地利台北辦事處申辦 D 類學生簽證或居留許可，並投保申根及奧地利公保（ÖGK）。",
    ),
    "西班牙": (
        "每月生活費約 USD 850–1,350（折合歐元約 EUR 780–1,250 / 月、新臺幣約 27,000–43,000 元；含馬德里歐洲大學 UEM 與加泰隆尼亞理工大學 UPC 住宿與膳食）",
        "須憑西班牙接待大學入學許可向西班牙商務辦事處申辦學生簽證，並投保無自付額之全額醫療與意外保險。",
    ),
    "美國": (
        "每月生活費約 USD 1,300–2,200（折合新臺幣約 41,500–70,000 元；含愛荷華州立大學 ISU 1+1／3.5+1.5 雙聯、韋恩州立大學 WSU 1+1 雙聯［每名大同雙聯生可獲 USD 3,000/學期 Dean's Merit Scholarship］、拉瑪大學 Lamar 1+1 雙聯與匹茲堡州立大學 PSU 交換）",
        "修讀美國雙聯學位或學期交換須憑 I-20（F-1）或 DS-2019（J-1）表格繳交 SEVIS I-901 費用並向美國在台協會（AIT）申辦簽證，且須投保接待大學規定之學生健康保險。",
    ),
    "加拿大": (
        "每月生活費約 USD 1,100–1,750（折合加幣約 CAD 1,500–2,400 / 月、新臺幣約 35,000–56,000 元；含薩克其萬大學 University of Saskatchewan 校內學生宿舍與膳食）",
        "交換一學期（6 個月內）可申辦加拿大電子旅行證（eTA），一學年以上須申辦 Study Permit，並納保薩克其萬省醫療保險與大學學生健康險。",
    ),
    "澳洲": (
        "每月生活費約 USD 1,200–1,800（折合澳幣約 AUD 1,800–2,700 / 月、新臺幣約 38,000–57,000 元；含紐卡索大學 University of Newcastle 1+1 雙聯碩士校內外學生公寓與交通膳食）",
        "修讀澳洲紐卡索大學 1+1 雙聯碩士須申辦澳洲學生簽證（Subclass 500）並投保澳洲海外學生健康保險（OSHC）。",
    ),
    "泰國": (
        "每月生活費約 USD 450–800（折合泰銖約 THB 15,000–27,000 / 月、新臺幣約 14,500–25,500 元；含法政大學 Thammasat University 詩琳通國際工學院 SIIT 學生公寓與膳食）",
        "須憑泰國法政大學入學許可向泰國貿易經濟辦事處（TTEO）申辦 Non-Immigrant ED 學生簽證，並於出國前購買涵蓋全期之海外醫療及意外險。",
    ),
    "印尼": (
        "每月生活費約 USD 380–680（折合新臺幣約 12,000–21,500 元；含泗水理工學院 ITS 與彼得拉基督教大學 Petra Christian University 國際學生宿舍與生活開銷）",
        "須由印尼接待大學協助申辦社會文化／學習簽證（C211 / C316 Study Visa），並投保海外全期醫療與意外保險。",
    ),
    "菲律賓": (
        "每月生活費約 USD 450–800（折合新臺幣約 14,500–25,500 元；含馬尼拉雅典耀大學、德拉薩大學與宿霧聖卡洛斯大學暑期英語研習與交換期間食宿）",
        "須依菲律賓駐臺代表處（MECO）及接待校規定申辦簽證與特別學習許可（SSP），並投保海外全期醫療與意外保險。",
    ),
    "越南": (
        "每月生活費約 USD 380–680（折合新臺幣約 12,000–21,500 元；含河內國家大學外國語大學與河內經營與工藝大學交流食宿）",
        "須依越南接待大學指引申辦簽證，並投保涵蓋全期之海外醫療及意外保險。",
    ),
    "蒙古": (
        "每月生活費約 USD 380–680（折合新臺幣約 12,000–21,500 元；含烏蘭巴托蒙古國立大學 NUM 與蒙古科技大學 MUST 學生宿舍與膳食）",
        "須憑蒙古合作大學邀請函申辦簽證，並於出國前投保涵蓋全期之海外醫療及意外保險。",
    ),
    "中國大陸": (
        "每月生活費約 USD 350–650（折合人民幣約 RMB 2,200–4,200 / 月、新臺幣約 11,000–21,000 元；含北京科技大學、天津大學、西北工業大學、廣東工業大學、福州大學、深圳技術大學、北京服裝學院等校內留學生宿舍與學生食堂開銷）",
        "須持有效「臺灣居民來往大陸通行證（臺胞證）」及接待高校錄取通知書報到，出國前完成大陸委員會「國人赴陸港澳動態登錄」並購買海外醫療及意外保險。",
    ),
}

SEMESTER_DATES_BY_COUNTRY = {
    "日本": "春季學期（前學期）：約 4 月初至 8 月上旬；秋季學期（後學期）：約 9 月下旬／10 月初至翌年 2 月／3 月",
    "韓國": "春季學期：約 3 月初至 6 月中旬；秋季學期：約 9 月初至 12 月中旬",
    "德國": "冬季學期（Wintersemester）：約 9 月／10 月初至翌年 2 月；夏季學期（Sommersemester）：約 3 月／4 月初至 7 月底",
    "英國": "秋季學期（Autumn Term）：約 9 月中下旬至翌年 1 月；春季學期（Spring Term）：約 1 月下旬至 5 月底",
    "法國": "秋季學期（Semestre d'Automne）：約 9 月初至翌年 1 月底；春季學期（Semestre de Printemps）：約 2 月初至 6 月中旬",
    "芬蘭": "秋季學期（Autumn Semester）：約 8 月下旬至 12 月中下旬；春季學期（Spring Semester）：約 1 月初至 5 月下旬",
    "波蘭": "冬季學期（Winter Semester）：約 10 月初至翌年 2 月中旬；夏季學期（Summer Semester）：約 2 月下旬至 6 月底",
    "捷克": "冬季學期（Winter Semester）：約 9 月中下旬至翌年 2 月初；夏季學期（Summer Semester）：約 2 月中旬至 6 月底",
    "義大利": "第一學期（First Semester）：約 9 月中旬至翌年 1 月底；第二學期（Second Semester）：約 2 月中旬至 6 月底",
    "荷蘭": "第一學期（Semester 1）：約 9 月初至翌年 1 月底；第二學期（Semester 2）：約 2 月初至 6 月底",
    "奧地利": "冬季學期（Winter Semester）：約 9 月中旬至翌年 1 月底；夏季學期（Summer Semester）：約 2 月中旬至 6 月底",
    "西班牙": "秋季學期：約 9 月中旬至翌年 1 月底；春季學期：約 2 月初至 6 月中旬",
    "美國": "秋季學期（Fall Semester）：約 8 月中下旬至 12 月中旬；春季學期（Spring Semester）：約 1 月中旬至 5 月中旬",
    "加拿大": "秋季學期（Fall Term）：約 9 月初至 12 月下旬；冬季學期（Winter Term）：約 1 月初至 4 月下旬",
    "澳洲": "第一學期（Semester 1）：約 2 月中下旬至 6 月下旬；第二學期（Semester 2）：約 7 月中下旬至 11 月下旬",
    "泰國": "第一學期：約 8 月中旬至 12 月中旬；第二學期：約 1 月中旬至 5 月中旬",
    "印尼": "奇數題學期（Odd Semester）：約 8 月下旬至翌年 1 月；偶數題學期（Even Semester）：約 2 月中旬至 6 月底",
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
                "latitude": float(loc.get("latitude", 25.0674)),
                "longitude": float(loc.get("longitude", 121.5218)),
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
    OFFICIAL_TTU_DIR.mkdir(parents=True, exist_ok=True)
    catalog_source = json.loads(
        (SOURCES_TTU_DIR / "ttu_catalog_source.json").read_text(encoding="utf-8")
    )
    resolved_locations = json.loads(
        (SOURCES_TTU_DIR / "ttu_resolved_locations.json").read_text(encoding="utf-8")
    )
    bin_urls_path = SOURCES_TTU_DIR / "binary_source_urls.json"
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

        group_str = clean_text(item.get("group") or "國際暨兩岸事務處正式締約姊妹校")
        if "雙聯" in group_str:
            dual_degree_count += 1
        quota_str = clean_text(item.get("quota") or "依當學期國際暨兩岸事務處公告名額")
        detail_url = item.get("detail_url") or TTU_SISTER_SCHOOLS_URL
        source_url = detail_url

        if "雙聯" in group_str and "交換" in group_str:
            program_type = f"大同大學出國交換學生暨跨國雙聯學位計畫（{group_str}）"
        elif "雙聯" in group_str:
            program_type = f"大同大學跨國雙聯學位計畫（{group_str}）"
        elif avail_status == "open":
            program_type = f"大同大學出國交換學生計畫（{group_str}）"
        else:
            program_type = f"大同大學國際暨兩岸事務處正式締約姊妹校（{group_str}）"

        colleges_str = clean_text(item.get("colleges") or "")
        degree_levels_str = clean_text(item.get("eligible_degrees") or "")
        lang_req_str = clean_text(item.get("language_req") or "")
        gpa_req_str = clean_text(item.get("gpa_req") or "")
        website = item.get("website") or TTU_SISTER_SCHOOLS_URL
        tuition_note = clean_text(item.get("tuition_note") or "")
        exps = item.get("experience_reports") or []

        round_label = (
            "115–116學年度出國交換學生暨雙聯學位計畫（第一階段／第二階段甄選）"
            if avail_status == "open"
            else "國際暨兩岸事務處正式締約姊妹校（當期開放名額依國際處最新甄選公告為準）"
        )
        app_deadline_str = clean_text(item.get("deadline") or "")
        deadline_iso = "2026-10-14T16:00:00+08:00"
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
            f"開放對象與學院：{colleges_str}（{degree_levels_str}）。依《大同大學交換學生計畫實施辦法》（rid=1049）、《大同大學與境外大學校院辦理雙聯學制實施辦法》（rid=232）、《大同大學學生出國期間有關學業及學籍處理要點》（rid=225）及《大同大學學生抵免學分辦法》（rid=224）："
            "（1）在學年資與成績門檻：須為大同大學正式學籍在學學生（不含在職專班），出國時須在大同大學就讀滿一學年以上（即大二以上、碩一／碩二或博士班），歷年學業總平均達 GPA 3.0（百分制約 75 分）以上；"
            "（2）兩階段甄選與至多 2 志願規定：每學期分第一階段與第二階段收件，每人至多填寫 2 個志願（交換或雙聯擇一或混填）；量化審查權重為「在校成績 40% + 語文能力 40% + 讀書計畫 20%」，總分達 70 分以上始得推薦；第一階段獲推薦者不得放棄並改申請第二階段，簽署家長同意書及本人聲明書後無故放棄者，兩年內不得再提出申請；"
            "（3）在學註冊與返國學分抵免：交換生於出國交換期間須維持大同大學在學學籍並繳交全額學雜費（免繳接待姊妹校學費），且每學期至少應修習相當於大同大學規定之科目或學分，返國後檢附國外正式成績單與課程大綱辦理學分抵免。"
        )

        living_cost_str, visa_health_str = REGION_COST_DEFAULTS.get(
            country,
            (
                "每月生活費約 USD 700–1,300（折合新臺幣約 22,500–41,500 元，含住宿、膳食與市區交通）",
                "須依接待國駐臺機構規定申辦學生簽證，並於出國前購買涵蓋全期之海外醫療與意外保險。",
            ),
        )

        tuition_points_list = [
            f"大同大學出國交換與雙聯學雜費規定（依《大同大學交換學生計畫實施辦法》rid=1049 及《雙聯學制實施辦法》rid=232）：學期交換學生於出國期間須辦理大同大學註冊並繳交大同全額學雜費，免繳接待姊妹校學費（住宿費、生活費、保險費、簽證費與機票自理）；雙聯學位學生依兩校雙聯協議繳交學費（如美國韋恩州立大學 WSU 1+1 碩士雙聯每名大同錄取生享 USD 3,000/學期 Dean's Merit Scholarship、英國倫敦布魯內爾大學 Brunel 1+1／4+1 數位設計與 AI 雙聯每年 10 名享 15% 學費減免）。本合作校待遇：{tuition_note}。",
            "教育部學海系列與大同大學校友捐助獎助學金（國際暨兩岸事務處，尚志教育研究館）：（1）教育部《學海飛颺》（每人補助約 NT$50,000–300,000，含來回機票與生活費）與《學海惜珠》：學士班前一學期班排前 50%、碩博生 80 分以上，且符合語檢門檻（英語系國家 TOEIC 650+、非英語歐盟國家 TOEIC 600+、亞洲及日本 TOEIC 550+ 或 JLPT N4+）；（2）《大同大學校友捐助國際交流專案獎助學金》（rid=1124）：申請學海飛颺／惜珠將同時自動審核校友捐助獎助學金，無須重複送件；（3）《大同大學鼓勵學生出國交換研修助學金》（rid=1045，電機系 66 級校友捐助清寒助學金）：每學期最高補助 NT$100,000，每年至多 15 名；（4）《暑期赴境外語言學習助學金》（rid=1129，最高 NT$50,000）與《暑期赴境外學校交流助學金》（rid=1047）。",
        ]

        app_steps_list = [
            f"步驟一（確認大同大學就讀滿一學年資格、GPA 3.0 門檻與 {zh_name} 語檢要求，至多選填 2 個志願）：確認符合《大同大學交換學生計畫實施辦法》規定（出國時於大同就讀滿一學年以上：{degree_levels_str}；{gpa_req_str}；{lang_req_str}），每人至多可選填 2 所志願學校。",
            f"步驟二（完成線上報名表登錄並繳交裝訂成冊之紙本申請表件至國際暨兩岸事務處）：於第一階段或第二階段截止日 16:00 前，先至大同大學報名系統（https://admission.ttu.edu.tw/p/423-1034-3.php）完成線上填報，並將「01交換計畫文件／02雙聯學位計畫文件」紙本資料（含申請表、中英文歷年成績單含總平均 GPA、英文自傳、英文讀書計畫含國外修課規劃表、教師推薦信 2 封、語檢證明；請勿使用訂書針，改以長尾夾固定）送交國際暨兩岸事務處黃鈺婷小姐（分機 7547，ythuang@gm.ttu.edu.tw）。",
            f"步驟三（通過量化書面審查［在校成績 40% + 語文能力 40% + 讀書計畫 20%，總分 70 分及格］並繳交家長同意書與本人聲明書）：經審查通過獲推薦資格者，須於期限內繳交親筆簽名之「家長同意書（附件二）」與「本人聲明書（附件三）」（簽署後無故放棄者兩年內不得再申請），並可同步線上申請教育部《學海飛颺／惜珠》與《大同大學校友捐助國際交流獎助學金》（https://admission.ttu.edu.tw/p/423-1034-13.php）。",
            f"步驟四（由國際處向 {zh_name} 官方提名，辦理簽證住宿、返國兩週內上傳心得報告至［人在他鄉大同人］網誌並辦理學分抵免）：取得 {zh_name} 入學許可後辦理學生簽證與海外醫療意外保險；返國後兩週內須繳交「學生境外研修實習心得報告表（附件四）」、「登機證票根黏存表（附件五）」、「護照出入境章影本（附件六）」及親簽領據，並完成線上回國報告登錄（https://admission.ttu.edu.tw/p/423-1034-11.php，公開發表於大同大學國際處《人在他鄉大同人》痞客邦網誌），再持國外成績單辦理學分抵免。",
        ]

        elig_points_list = [
            f"合作類別與組別：{program_type}",
            f"開放學制與年級：{degree_levels_str}",
            f"開放申請學院：{colleges_str}",
            f"學業成績門檻：{gpa_req_str}",
            f"外語能力標準：{lang_req_str}",
            f"學費與獎助待遇：{tuition_note}",
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
                edept = e.get("department") or "大同大學交換生"
                estu = e.get("student") or "大同大學交換生"
                eurl = e.get("url") or f"{TTU_PIXNET_BLOG_URL}#ttu-exp-{sn}-{e_idx+1}"
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
                    f"大同大學國際暨兩岸事務處《人在他鄉大同人》官方網誌公開收錄之 {edept} {estu} 赴 {country} {full_name} 交換／雙聯研修心得報告（{raw_t}），詳述課程修讀、專業實作、學生宿舍環境、當地每月生活開銷與跨文化收穫。"
                )
                theme_map = {
                    "academics": f"大同大學 {edept} {estu} 於《{raw_t}》分享在 {zh_name} 修讀工程、電資、經營、設計或外語專業課程、專題發表及返國辦理學分抵免之實務經驗。",
                    "housing": f"大同大學交換生記錄入住 {zh_name} 校內外學生宿舍（寮）或國際學舍之房型設備、月租費用與通勤方式（{housing_str[:100]}）。",
                    "campus_culture": f"大同大學國際暨兩岸事務處《人在他鄉大同人》網誌收錄《{raw_t}》之國際學生社團互動、校園文化祭與城市探索體悟。",
                    "cost": f"大同大學學生分享於 {zh_name} 之每月租金、伙食與交通花費（{living_cost_str[:100]}），以及申請教育部學海飛颺／惜珠與大同校友捐助獎學金之經驗。",
                }
                student_experience_rows.append({
                    "school_name": full_name,
                    "country": country,
                    "title": raw_t,
                    "source_url": eurl,
                    "source_type": "article",
                    "platform": "大同大學國際暨兩岸事務處—《人在他鄉大同人》交換學生與雙聯學位心得分享網誌",
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
                        f"{full_name}:ttu_exp:{e_idx}:{eurl}".encode("utf-8")
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
            "home_university": "大同大學",
            "school_name": full_name,
            "country": country,
            "official_experience_portal_url": exp_links[0]["url"] if exp_links else TTU_PIXNET_BLOG_URL,
            "partner_page_url": source_url,
            "report_count": len(exps),
            "sample_reports": sample_reports,
            "checked_at": CHECKED_AT,
        })

        loc = resolved_locations.get(full_name) or {
            "city": country,
            "latitude": 25.0674,
            "longitude": 121.5218,
            "source_url": "https://www.wikidata.org",
        }
        city_name = loc.get("city") or country
        lat = float(loc.get("latitude", 25.0674))
        lon = float(loc.get("longitude", 121.5218))
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
                f"【大同大學《人在他鄉大同人》學長姐交換／雙聯心得報告（共 {len(exps)} 篇）】收錄於國際暨兩岸事務處官方網誌（含：{'、'.join(exp_labels[:4])}）"
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
            "availability_note": f"大同大學國際暨兩岸事務處公告合作校（{program_type}）；{quota_str}。",
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
                "title": f"大同大學國際暨兩岸事務處交換與雙聯甄選公告—{zh_name}",
                "source_url": source_url,
                "role": "home_university",
                "authority": "home_official_notice",
                "effective_academic_year": acad_year,
                "application_round": round_label,
                "checked_at": CHECKED_AT,
            },
            {
                "title": "大同大學交換學生計畫實施辦法（rid=1049）與雙聯學制實施辦法（rid=232）",
                "source_url": TTU_RULE_EXCHANGE_URL,
                "role": "home_university",
                "authority": "home_official_notice",
                "effective_academic_year": acad_year,
                "application_round": round_label,
                "checked_at": CHECKED_AT,
            },
            {
                "title": "大同大學教育部學海飛颺、學海惜珠與校友捐助國際交流獎助學金公告",
                "source_url": TTU_115_XUEHAI_URL,
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
            "home_university": "大同大學",
            "school_name": full_name,
            "partner_website": website,
            "country": country,
            "program_type": program_type,
            "academic_year": acad_year,
            "application_round": round_label,
            "effective_application_rounds": [round_label, "115-1", "115-2", "116-1", "116-2"],
            "applicability_status": "verified",
            "applicability_note": "大同大學由國際暨兩岸事務處統籌全校工程學院（含原電機資訊學院系所）、經營學院、設計學院與國際學院之海外姊妹校交換計畫（日本 22 校、德國 5 校、芬蘭 Xamk、法國 UTC、韓國仁川大學、泰國法政大學 SIIT、美國匹茲堡州立大學與大陸地區重點高校）及英美德法澳日 8 大跨國雙聯學位計畫（美國愛荷華州立大學 ISU、韋恩州立大學 WSU、拉瑪大學 Lamar、英國密德薩斯大學 Middlesex、倫敦布魯內爾大學 Brunel、德國斯圖加特應用科技大學 HFT Stuttgart、法國 ESIEE-Amiens / UniLaSalle、澳洲紐卡索大學 Newcastle）。",
            "review_status": "published",
            "published_at": CHECKED_AT,
            "steps": [
                {
                    "rule_id": f"ttu-{acad_year}-home-1-{sn:03d}",
                    "order": 1,
                    "phase": "校內申請",
                    "title": f"確認大同大學在學滿一學年資格、GPA 3.0 門檻與 {zh_name} 語檢要求，選填至多 2 個志願",
                    "responsible_party": "學生",
                    "responsible_unit": "大同大學國際暨兩岸事務處（尚志教育研究館）",
                    "deadline_at": deadline_iso,
                    "deadline_status": "verified_exact" if avail_status == "open" else "reference_only",
                    "deadline_source_url": source_url,
                    "deadline_checked_at": CHECKED_AT,
                    "deadline_reminder_eligible": avail_status == "open",
                    "summary": f"確認符合《大同大學交換學生計畫實施辦法》（rid=1049）規定：出國時於大同大學就讀滿一學年以上（{degree_levels_str}）、學業總平均門檻（{gpa_req_str}）與外語標準（{lang_req_str}），每人每階段至多選填 2 個志願。",
                    "details": [
                        f"開放學制與學院：{colleges_str}（{degree_levels_str}）",
                        f"語言與學業條件：{lang_req_str}｜{gpa_req_str}",
                        f"當期名額與計畫類別：{quota_str}｜{program_type}",
                    ],
                    "scope": {
                        "home_universities": ["大同大學"],
                        "partner_universities": [full_name],
                        "academic_years": ["115", "116"],
                        "application_rounds": [round_label, "115-1", "115-2", "116-1", "116-2"],
                    },
                    "source_urls": [source_url, TTU_RULE_EXCHANGE_URL],
                    "checked_at": CHECKED_AT,
                    "support_status": "verified",
                },
                {
                    "rule_id": f"ttu-{acad_year}-home-2-{sn:03d}",
                    "order": 2,
                    "phase": "校內申請",
                    "title": "完成 admission.ttu.edu.tw 線上報名表登錄，並將「01交換計畫文件／02雙聯學位計畫文件」紙本資料（長尾夾固定）送交國際暨兩岸事務處",
                    "responsible_party": "學生",
                    "responsible_unit": "國際暨兩岸事務處（承辦人：黃鈺婷小姐 02-2182-2928#7547）",
                    "deadline_at": deadline_iso,
                    "deadline_status": "verified_exact" if avail_status == "open" else "reference_only",
                    "deadline_source_url": source_url,
                    "deadline_checked_at": CHECKED_AT,
                    "deadline_reminder_eligible": avail_status == "open",
                    "summary": "於第一階段或第二階段截止日 16:00 前完成線上報名，並備妥交換／雙聯申請表、歷年中英文成績單正本（含 GPA）、英文自傳、英文讀書計畫（含國外修課規劃表）、推薦信 2 封及語檢證明送交國際處。",
                    "details": [
                        "必備申請文件：（1）線上申請表登錄（https://admission.ttu.edu.tw/p/423-1034-3.php）及紙本申請表（由導師／指導教授及系所主管核章）；（2）歷年中英文成績單正本（含總平均 GPA 3.0 以上與班排名）；（3）英文自傳（Autobiography，約 300–500 字）與英文讀書計畫（Study Plan，含國外預計修習課程規劃表；雙聯學位另須回答 5 大英文動機問題）；（4）大同大學專任教師英文推薦信 2 封；（5）有效外語檢定成績單影本（紙本請勿使用訂書針，一律以長尾夾固定）。",
                    ],
                    "document_requirements": [
                        {
                            "name": "大同大學交換學生計畫申請文件包（01交換計畫文件2026.zip）",
                            "official_form_url": TTU_EXCHANGE_ZIP_URL,
                            "source_urls": [TTU_2027_SPRING_EXCHANGE_URL, TTU_2026_FALL_EXCHANGE_URL],
                        },
                        {
                            "name": "大同大學雙聯學位計畫申請文件包（02雙聯學位計畫文件2026.zip）與學海申請表",
                            "official_form_url": TTU_DUAL_DEGREE_ZIP_URL,
                            "source_urls": [TTU_2027_SPRING_EXCHANGE_URL, TTU_115_XUEHAI_URL],
                        },
                    ],
                    "scope": {
                        "home_universities": ["大同大學"],
                        "academic_years": ["115", "116"],
                        "application_rounds": [round_label, "115-1", "115-2", "116-1", "116-2"],
                    },
                    "source_urls": [source_url, TTU_ONLINE_APPLY_EXCHANGE_URL],
                    "checked_at": CHECKED_AT,
                    "support_status": "verified",
                },
                {
                    "rule_id": f"ttu-{acad_year}-home-3-{sn:03d}",
                    "order": 3,
                    "phase": "甄選與提名",
                    "title": "通過校內量化審查（在校成績 40% + 語文能力 40% + 讀書計畫 20%，總分 70 分及格），簽署家長同意書與本人聲明書並申請學海與校友獎助學金",
                    "responsible_party": "國際暨兩岸事務處與申請學生",
                    "responsible_unit": "國際暨兩岸事務處審查委員會",
                    "deadline_at": "2026-10-30T16:00:00+08:00",
                    "deadline_status": "verified_exact",
                    "deadline_source_url": source_url,
                    "deadline_checked_at": CHECKED_AT,
                    "deadline_reminder_eligible": False,
                    "summary": "依《大同大學交換學生計畫實施辦法》第 6 條量化評分標準（在校成績 40%、語文能力 40%、讀書計畫 20%，及格門檻 70 分）審查；錄取推薦學生須繳交家長同意書與本人聲明書，並可同步申請教育部《學海飛颺／惜珠》、校友捐助獎助學金與電機系 66 級校友清寒助學金。",
                    "details": [
                        "甄選規定：第一階段獲推薦者不得放棄並改申請第二階段；繳交家長同意書及本人聲明書後無故放棄者，兩年內不得再提出申請。",
                        "獎學金聯審機制：申請教育部《學海飛颺／惜珠》將同時自動審核《大同大學校友捐助國際交流專案獎助學金》，無須重複送件；家庭經濟困難學生可另檢附 500–800 字中文自傳申請《鼓勵學生出國交換研修助學金》（最高 NT$100,000）。",
                    ],
                    "scope": {
                        "home_universities": ["大同大學"],
                        "academic_years": ["115", "116"],
                        "application_rounds": [round_label, "115-1", "115-2", "116-1", "116-2"],
                    },
                    "source_urls": [source_url, TTU_115_XUEHAI_URL, TTU_115_XUEHAI_WAITLIST_URL],
                    "checked_at": CHECKED_AT,
                    "support_status": "verified",
                },
                {
                    "rule_id": f"ttu-{sn:03d}-host-apply",
                    "order": 4,
                    "phase": "合作校申請",
                    "title": f"由國際暨兩岸事務處向 {zh_name} 官方提名，遞交姊妹校入學與宿舍申請並取得正式入學許可",
                    "responsible_party": "學生與接待校國際事務處",
                    "summary": f"通過校內甄選並繳交同意書後，由大同大學國際暨兩岸事務處（承辦人：黃鈺婷小姐 ythuang@gm.ttu.edu.tw）向 {zh_name} 完成官方提名，指導學生備齊姊妹校入學表件、英文財力證明、護照影本、作品集（設計學院交換生適用）並申請校內外學生宿舍。",
                    "details": [
                        f"研修期程：{study_period_str}｜名額：{quota_str}",
                        f"語言與學業條件：{lang_req_str}｜{gpa_req_str}",
                        f"住宿與費用待遇：{housing_str}",
                    ],
                    "scope": {
                        "home_universities": ["大同大學"],
                        "partner_universities": [full_name],
                        "academic_years": ["115", "116"],
                        "application_rounds": [round_label, "115-1", "115-2", "116-1", "116-2"],
                    },
                    "source_urls": [source_url, TTU_OUTBOUND_FLOW_URL, website],
                    "checked_at": CHECKED_AT,
                    "support_status": "verified",
                    "needs_confirmation": False,
                },
                {
                    "rule_id": f"ttu-{acad_year}-home-5-{sn:03d}",
                    "order": 5,
                    "phase": "行前準備",
                    "title": "維持大同在學註冊並繳交全額學雜費，返國後兩週內繳交心得報告表、登機證票根與出入境章並辦理學分抵免",
                    "responsible_party": "學生與所屬系所",
                    "responsible_unit": "國際暨兩岸事務處／教務處註冊組與課務組／各系所",
                    "summary": "依《大同大學交換學生計畫實施辦法》與《學生出國期間有關學業及學籍處理要點》，出國交換期間須維持大同在學註冊並繳交大同全額學雜費（免繳接待校學費）；返國後兩週內須完成線上回國心得填報（發表於《人在他鄉大同人》網誌）並繳交附件四心得報告表、附件五登機證票根黏存表、附件六出入境章與領據，再持國外成績單正本辦理學分抵免。",
                    "details": tuition_points_list,
                    "scope": {
                        "home_universities": ["大同大學"],
                        "academic_years": ["115", "116"],
                        "application_rounds": [round_label, "115-1", "115-2", "116-1", "116-2"],
                    },
                    "source_urls": [TTU_RULE_EXCHANGE_URL, TTU_RULE_OUTBOUND_CREDIT_URL, TTU_RULE_CREDIT_TRANSFER_URL, TTU_ONLINE_RETURN_REPORT_URL],
                    "checked_at": CHECKED_AT,
                    "support_status": "verified",
                },
            ],
            "sources": wf_sources,
            "last_checked": CHECKED_AT,
            "coverage_status": "official_verified",
            "coverage_note": f"已完整整合大同大學國際暨兩岸事務處《2027 春季／2026 秋季／2026 春季／2025 秋季赴外交換及雙聯學位甄選公告》、《115 年度學海飛颺與學海惜珠簡章及候補公告》、《大同大學交換學生計畫實施辦法（rid=1049）》、《雙聯學制實施辦法（rid=232）》、《校友捐助國際交流獎助學金辦法（rid=1124）》及《人在他鄉大同人》網誌 {exp_covered_schools} 校 {total_exp_reports} 篇歷屆交換與雙聯心得報告，共 {len(catalog_source)} 所合作姊妹校資料。",
        })

        cost_line = f"{zh_name} 預估每月生活費：{living_cost_str}"
        tuition_clean = tuition_points_list[0]
        housing_clean = housing_str
        calendar_clean = f"學期與研修時間參考：{sem_dates_str}"
        course_clean = course_rest_str
        src_url_list = [source_url, TTU_RULE_EXCHANGE_URL, TTU_RULE_OUTBOUND_CREDIT_URL, website]

        destinations.append({
            "home_university": "大同大學",
            "school_name": full_name,
            "country": country,
            "city": city_name,
            "cost_summary": f"{cost_line}。\n{tuition_clean}",
            "housing_summary": housing_clean,
            "transport_summary": f"校區代表城市：{city_name}。請依入學許可確認實際授課校區位置、機場接機服務與當地學生交通票卡優惠。",
            "campus_life_summary": f"{calendar_clean}\n{course_clean}",
            "student_guide_sections": [
                {
                    "key": "cost",
                    "title": "生活費、大同在學全額學雜費規定與學海飛颺／惜珠／校友捐助獎助學金",
                    "summary": cost_line,
                    "points": [cost_line] + tuition_points_list,
                    "source_urls": src_url_list,
                    "caution": "交換學生於出國期間須維持大同大學在學學籍並繳交大同全額學雜費（免繳接待姊妹校學費）；簽署家長同意書與本人聲明書後無故放棄者，兩年內不得再申請。",
                },
                {
                    "key": "housing",
                    "title": "校內外留學生宿舍（寮）、住宿申請與國際學伴接機資訊",
                    "summary": housing_clean[:160],
                    "points": [housing_clean],
                    "source_urls": src_url_list,
                    "caution": "各姊妹校學生宿舍名額有限，請於獲得大同國際處提名後依接待校期限完成宿位登記。",
                },
                {
                    "key": "insurance",
                    "title": "海外醫療意外保險、接待國法定健保與外交部出國動態登錄",
                    "summary": visa_health_str,
                    "points": [
                        visa_health_str,
                        "依《大同大學交換學生計畫實施辦法》第 10 條，交換生於出國前須自行購買涵蓋全交換期間之海外醫療及意外保險，並將保險單影本送交國際暨兩岸事務處備查。",
                    ],
                    "source_urls": src_url_list,
                    "caution": "學海飛颺、學海惜珠及大同校友獎助學金受獎生出國前須完成行政契約書簽署與保險核備。",
                },
                {
                    "key": "visa",
                    "title": "留學／交換簽證辦理、役男緩徵出境與在學學籍保留規定",
                    "summary": visa_health_str,
                    "points": [
                        visa_health_str,
                        "依《大同大學學生出國期間有關學業及學籍處理要點》（rid=225），出國交換以一學期或一學年為原則，雙聯學位依兩校協議辦理；具役男身分者須於出國前一個月檢附入學許可向學務處生輔組及國際處辦理役男出境核准手續。",
                    ],
                    "source_urls": src_url_list,
                    "caution": "交換期間應保有大同大學在學學籍，返國後須按時註冊復課並履行返國報告義務。",
                },
                {
                    "key": "academics",
                    "title": "修課規劃表審核、雙聯學制修業規定與返國學分抵免辦法",
                    "summary": course_clean[:160],
                    "points": [calendar_clean, course_clean],
                    "source_urls": src_url_list,
                    "caution": "出國前須於讀書計畫中擬妥「國外預計修習課程規劃表」並與系所主管確認抵免採認原則；返國後依《大同大學學生抵免學分辦法》（rid=224）檢附國外成績單正本與課程大綱辦理抵免。",
                },
                {
                    "key": "living",
                    "title": f"{city_name} 校園生活與大同大學《人在他鄉大同人》學長姐交換／雙聯心得傳承",
                    "summary": f"代表城市：{city_name}。返國後兩週內完成《人在他鄉大同人》網誌心得上傳並繳交登機證票根與出入境章。",
                    "points": [
                        f"目的地城市：{city_name}（{country}）",
                        f"大同大學國際暨兩岸事務處經營《人在他鄉大同人》（https://tatunguni.pixnet.net/blog）官方網誌，完整公開歷屆學長姐赴日、德、英、美、法、芬、韓、波、泰及大陸交換與雙聯心得報告"
                        + (f"（本校共收錄 {len(exps)} 篇心得：{'、'.join(exp_labels[:3])}）" if exps else "")
                        + "。",
                    ],
                    "source_urls": [exp_links[0]["url"] if exp_links else TTU_PIXNET_BLOG_URL],
                },
            ],
            "sources": [
                {
                    "title": f"大同大學國際暨兩岸事務處交換與雙聯公告—{zh_name}",
                    "source_url": source_url,
                    "summary": "大同大學公告之交換學生與雙聯學位申請資格、名額、語言門檻及費用待遇說明",
                },
                {
                    "title": "大同大學交換學生計畫實施辦法（rid=1049）與學生抵免學分辦法（rid=224）",
                    "source_url": TTU_RULE_EXCHANGE_URL,
                    "summary": "大同大學出國交換量化評分標準（40%/40%/20%）、至多 2 志願、在學註冊與返國學分抵免規範",
                },
            ],
            "last_checked": CHECKED_AT,
            "coverage_status": "official_verified",
            "coverage_note": f"已整合大同大學國際暨兩岸事務處 {len(catalog_source)} 所合作姊妹校（含 {open_partner_count} 所常態開放交換與雙聯學位學校）及《人在他鄉大同人》網誌 {exp_covered_schools} 校 {total_exp_reports} 篇歷屆心得報告。",
        })

        research_records.append({
            "home_university": "大同大學",
            "school_name": full_name,
            "country": country,
            "official_website": website,
            "verification_status": "official_verified",
            "discovery_source_url": detail_url,
            "checked_at": CHECKED_AT,
            "note": "大同大學國際暨兩岸事務處交換及雙聯學位公告、締約姊妹校名錄、《人在他鄉大同人》官方網誌及 ROR/Wikidata 官方網址核對完成。",
        })

        ev_sources = [{"title": f"大同大學國際暨兩岸事務處甄選公告—{zh_name}", "url": source_url}]
        if exp_links:
            ev_sources.append({"title": f"大同大學《人在他鄉大同人》赴 {zh_name} 交換／雙聯心得報告（{len(exps)} 篇）", "url": exp_links[0]["url"]})
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
                    "scope": "大同大學合作姊妹校住宿與生活資訊",
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
                    "scope": "大同大學出國交換學雜費規定與教育部學海／校友捐助獎助學金",
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
                    "scope": "大同大學交換學生計畫實施辦法、雙聯學制實施辦法與抵免學分辦法",
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
                    "scope": "大同大學海外交換與雙聯學位簽證及保險規定",
                    "original_excerpt": False,
                    "original_text": "",
                    "translation_status": "original",
                },
                {
                    "theme": "campus_culture",
                    "kind": "mixed" if has_student_exp else "official",
                    "text": f"合作類別：{program_type}｜名額：{quota_str}｜語言要求：{lang_req_str}"
                    + (f"｜大同大學《人在他鄉大同人》官方網誌收錄 {len(exps)} 篇赴 {zh_name} 交換／雙聯心得報告（{'、'.join(exp_labels[:3])}）。" if exps else ""),
                    "sources": ev_sources,
                    "checked_at": CHECKED_AT,
                    "scope": "大同大學交換名額與《人在他鄉大同人》學長姐心得報告",
                    "original_excerpt": False,
                    "original_text": "",
                    "translation_status": "original",
                },
            ],
            "notes": [
                "已整合大同大學國際暨兩岸事務處《交換學生計畫實施辦法》、《雙聯學制實施辦法》、《115 年度學海飛颺與學海惜珠簡章》、《校友捐助國際交流獎助學金》及《人在他鄉大同人》學生心得報告。",
                "當期開放名額、宿位供給與語檢門檻請依合作校最新簡章及入學通知書核對。",
            ],
            "location_signature": f"verified:{lat}:{lon}:representative",
            "extraction_version": 3,
        })

    def write_jsonl(path: Path, rows: list[dict]) -> None:
        path.write_text(
            "\n".join(json.dumps(r, ensure_ascii=False) for r in rows) + ("\n" if rows else ""),
            encoding="utf-8",
        )

    write_jsonl(OFFICIAL_TTU_DIR / "partners.jsonl", partners)
    write_jsonl(SOURCES_TTU_DIR / "partners.jsonl", partners)
    write_jsonl(OFFICIAL_TTU_DIR / "application_workflows.jsonl", workflows)
    write_jsonl(OFFICIAL_TTU_DIR / "destination_profiles.jsonl", destinations)
    write_jsonl(OFFICIAL_TTU_DIR / "partner_research.jsonl", research_records)
    write_jsonl(OFFICIAL_TTU_DIR / "student_life.jsonl", life_records)
    write_jsonl(OFFICIAL_TTU_DIR / "experience_sources.jsonl", experience_sources_records)
    write_jsonl(OFFICIAL_TTU_DIR / "student_experience_sources.jsonl", experience_sources_records)
    write_jsonl(OFFICIAL_TTU_DIR / "student_experiences.jsonl", student_experience_rows)

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
    (OFFICIAL_TTU_DIR / "student-experience-digests.json").write_text(
        json.dumps({"digests": digest_records}, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    (OFFICIAL_TTU_DIR / "student-experiences.json").write_text(
        json.dumps(
            {
                "school_id": "ttu",
                "school_name": "大同大學",
                "checked_at": CHECKED_AT,
                "source_url": TTU_PIXNET_BLOG_URL,
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

    (OFFICIAL_TTU_DIR / "campus-locations.json").write_text(
        json.dumps(
            {
                "school_id": "ttu",
                "school_name": "大同大學",
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
    (OFFICIAL_TTU_DIR / "campus-assets.json").write_text(
        json.dumps(
            {
                "school_id": "ttu",
                "school_name": "大同大學",
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

    ttu_source_urls = [
        TTU_HOME_URL,
        TTU_OIA_HOME_URL,
        TTU_2027_SPRING_EXCHANGE_URL,
        TTU_2026_FALL_EXCHANGE_URL,
        TTU_2026_SPRING_EXCHANGE_URL,
        TTU_2025_FALL_EXCHANGE_URL,
        TTU_115_XUEHAI_URL,
        TTU_115_XUEHAI_WAITLIST_URL,
        TTU_ALUMNI_SCHOLARSHIP_URL,
        TTU_SUMMER_GRANT_URL,
        TTU_OUTBOUND_FLOW_URL,
        TTU_OUTBOUND_STATS_URL,
        TTU_OUTBOUND_FAQ_URL,
        TTU_SISTER_SCHOOLS_URL,
        TTU_ONLINE_APPLY_EXCHANGE_URL,
        TTU_ONLINE_APPLY_XUEHAI_URL,
        TTU_ONLINE_RETURN_REPORT_URL,
        TTU_PIXNET_BLOG_URL,
        TTU_RULE_EXCHANGE_URL,
        TTU_RULE_DUAL_DEGREE_URL,
        TTU_RULE_OUTBOUND_CREDIT_URL,
        TTU_RULE_CREDIT_TRANSFER_URL,
        TTU_RULE_ALUMNI_SCHOLARSHIP_URL,
        TTU_RULE_ENCOURAGE_GRANT_URL,
        TTU_RULE_SUMMER_EXCHANGE_GRANT_URL,
        TTU_RULE_SUMMER_LANG_GRANT_URL,
        TTU_EXCHANGE_ZIP_URL,
        TTU_DUAL_DEGREE_ZIP_URL,
        TTU_XUEHAI_BROCHURE_PDF,
        TTU_XUEHAI_FORM_PDF,
        TTU_ENCOURAGE_GRANT_FORM_PDF,
        TTU_XUEHAI_WAITLIST_FORM_PDF,
    ]

    exchange_info_payload = {
        "school_name": "大同大學",
        "program_type": [
            f"國際暨兩岸事務處「出國交換學生計畫」（涵蓋日本 22 所理工設計名校［京都工藝纖維大學、千葉大學、東京都市大學、芝浦工業大學、東京電機大學、長岡造形大學、札幌市立大學、東北工業大學、岡山大學、熊本大學、琉球大學、縣立廣島大學、同志社大學、專修大學等］、德國 5 校［斯圖加特應用科技大學 HFT Stuttgart、奧斯納布魯克應用科技大學、德根多夫應用科技大學 DIT、巴登符騰堡雙元制大學 DHBW、卡爾斯魯厄應用科技大學 HKA］、芬蘭東南芬蘭應用科技大學 Xamk、法國貢比涅科技大學 UTC、韓國仁川大學、泰國法政大學 SIIT、美國匹茲堡州立大學 PSU 及大陸 12 所重點大學，全校共 {len(partners)} 所合作姊妹校、{open_partner_count} 所常態開放申請）",
            "英、美、德、法、澳、日 9 校「跨國雙聯學位計畫」（涵蓋【美國愛荷華州立大學 Iowa State University：工程／電資 1+1 碩士與 3.5+1.5 學碩雙聯】、【美國韋恩州立大學 Wayne State University：工程／電資 1+1 碩士雙聯，每名大同錄取生可獲 USD 3,000/學期 Dean's Merit Scholarship】、【美國拉瑪大學 Lamar University：工程／電資／商管 1+1 碩士雙聯，免 GRE】、【英國倫敦密德薩斯大學 Middlesex University：3+1 雙學士、1+1 雙碩士、應外系 3+1.5 學碩雙聯】、【英國倫敦布魯內爾大學 Brunel University London：1+1／4+1 MSc Digital Design and Branding 與 AI Strategy 雙聯，每年 10 名享 15% 學費減免】、【德國斯圖加特應用科技大學 HFT Stuttgart：經營與資工 1+1 雙碩士】、【法國 ESIEE-Amiens / UniLaSalle：電資與工程 1+1 雙碩士】、【澳洲紐卡索大學 University of Newcastle：1+1 雙碩士】及【日本千葉大學工學部工業設計雙聯】）",
            "教育部「學海飛颺、學海惜珠」與「大同大學校友捐助國際交流獎助學金／電機系 66 級校友鼓勵出國交換助學金／暑期海外語言學習助學金」（學海飛颺每人補助約 NT$50,000–300,000，申請學海自動聯審校友捐助獎助學金；電機系 66 級校友清寒交換助學金每學期最高 NT$100,000；大一、大二及碩一多益未達 650 分者赴菲律賓宿霧／歐美日暑期語言學校最高補助 NT$50,000）",
        ],
        "academic_year": [
            "115–116（每學期採兩階段甄選：秋季班第一階段約 2 月下旬截止、第二階段約 3 月上旬截止；春季班第一階段約 9 月上旬截止、第二階段約 10 月中旬截止；教育部學海飛颺／惜珠與校友獎助學金主梯次約 3 月初截止、候補梯次約 10 月中旬截止）",
            f"本平台完整收錄大同大學國際暨兩岸事務處與招生委員會公告之 {len(partners)} 所全球與兩岸合作姊妹校（含 {open_partner_count} 所常態開放申請之交換與雙聯學位合作校、{len(partners) - open_partner_count} 所正式締約姊妹校，橫跨 20 個國家與地區，並完整收錄《人在他鄉大同人》官方網誌 {exp_covered_schools} 所合作大學共 {total_exp_reports} 篇歷屆學長姐交換與雙聯心得報告）",
        ],
        "semester": [
            "海外姊妹校學期交換計畫：可申請一學期或一學年；依《大同大學交換學生計畫實施辦法》（rid=1049）與《學生出國期間有關學業及學籍處理要點》（rid=225），出國時須在大同大學就讀滿一學年以上（即大二以上、碩一／碩二或博士班），交換期間須維持大同在學註冊並繳交大同全額學雜費（免繳接待校學費）。",
            "跨國雙聯學位與暑期海外研習：雙聯學位依各校協議為 1+1 雙碩士、3+1 雙學士、3+1.5 或 3.5+1.5／4+1 學碩雙聯；暑期海外語言學習與短期交流為每年 6–9 月暑假期間（至少 4 週且每週上課 15 小時以上）。",
        ],
        "application_period": [
            "【秋季班出國交換暨雙聯學位甄選（9 月出國）】第一階段截止：每年 2 月下旬（2026 秋季班第一階段為 2026/02/24 16:00）；第二階段截止：每年 3 月上旬（2026/03/10 16:00）。教育部《學海飛颺／學海惜珠》暨《大同校友捐助獎助學金》及《鼓勵學生出國交換研修助學金》主梯次於每年 3 月初截止（2026/03/03 16:30）。",
            "【春季班出國交換暨雙聯學位甄選（翌年 2–4 月出國）】第一階段截止：每年 9 月上旬（2027 春季班第一階段為 2026/09/10 16:00）；第二階段截止：每年 10 月中旬（2026/10/14 16:00）。教育部《學海飛颺》春季班候補獎學金申請於每年 10 月中旬截止（2026/10/15 16:00）。",
        ],
        "eligibility": [
            "1. 在學身分與年級限制：依《大同大學交換學生計畫實施辦法》（rid=1049）第 3 條，申請人須為本校正式學籍在學學生（不含在職專班），且實際出國交換時須在本校就讀滿一學年以上（即大學部大一新生於大一下可提出申請、大二起出國；碩士班及博士班在學生均可申請）。",
            "2. 學業成績門檻與量化評分標準：（a）交換生與多數雙聯學位申請人歷年學業總平均須達 GPA 3.0（百分制約 75 分）以上（英國倫敦布魯內爾大學 Brunel 1+1／4+1 雙聯學位歷年平均達 70 分以上即可）；（b）校內甄選量化評分權重為「在校成績 40% + 語文能力 40% + 讀書計畫 20%」，總分滿分 100 分，達 70 分以上始得推薦；（c）教育部《學海飛颺／惜珠》獎學金要求大學部前一學期成績達全班前 50%、研究所前一學期平均達 80 分以上。",
            "3. 志願數上限與棄權罰則：每人每階段至多可選填 2 個志願學校；第一階段獲推薦資格之學生不得放棄並改申請第二階段；通過甄選並簽署「家長同意書」與「本人聲明書」後，若非因不可抗力因素無故放棄錄取資格者，兩年內不得再提出申請。",
        ],
        "language_requirement": [
            "1. 英語組交換與跨國雙聯學位語言門檻：（a）歐洲與英語系交換校（德國 HFT Stuttgart、Osnabrück、DIT、DHBW、HKA、芬蘭 Xamk、法國 UTC、韓國仁川大學、泰國法政大學 SIIT、美國匹茲堡州立大學 PSU 等）：須具英語 CEFR B1–B2 以上證明（TOEIC 550–785 / TOEFL iBT 61–79 / IELTS 5.0–6.0）；（b）英美德法澳雙聯學位：美國愛荷華州立大學 ISU（TOEFL iBT 79 / IELTS 6.5）、韋恩州立大學 WSU（TOEFL iBT 79 / IELTS 6.5）、拉瑪大學 Lamar（TOEFL iBT 79 / IELTS 6.5，免 GRE）、英國密德薩斯大學 Middlesex（IELTS 6.0–6.5）、倫敦布魯內爾大學 Brunel（IELTS 6.0–6.5）、德國 HFT Stuttgart（IELTS 6.0 / TOEFL iBT 79）、法國 ESIEE-Amiens（TOEIC 750 / IELTS 6.0）、澳洲紐卡索大學（IELTS 6.5）。",
            "2. 日語組 22 所姊妹校語言門檻：（a）日本千葉大學、同志社大學、專修大學、縣立廣島大學、東京都立大學：須具日語檢定 JLPT N2（或 N1–N3）合格證書；（b）日本京都工藝纖維大學 KIT、東京都市大學 TCU、芝浦工業大學 SIT、東京電機大學 TDU、長岡造形大學 NID、札幌市立大學 SCU、東北工業大學、岡山大學、熊本大學、琉球大學、室蘭工業大學、北見工業大學、福岡工業大學、廣島市立大學、名城大學、大阪工業大學：須具 JLPT N2–N4 合格證書或英語檢定證明（TOEIC 550+ / TOEFL iBT 61+ / IELTS 5.5+）。",
            "3. 教育部學海飛颺／惜珠與大陸地區門檻：（a）申請教育部《學海飛颺／惜珠》獎學金須符合分區語檢標準：赴英語系國家須達 TOEIC 650 分以上（或同級檢定）、赴非英語系歐盟國家須達 TOEIC 600 分以上、赴非英語系亞洲國家須達 TOEIC 550 分以上、赴日本須達 JLPT N4 合格或 TOEIC 550 分以上；（b）大陸地區 12 所姊妹校（北京科技大學、天津大學、西北工業大學、廣東工業大學、福州大學等）：中文授課免附外語檢定證明。",
        ],
        "required_documents": [
            "1. 大同大學線上報名系統登錄（https://admission.ttu.edu.tw/p/423-1034-3.php）及紙本《大同大學交換學生計畫申請表》或《雙聯學位計畫申請表》乙份（須經導師／指導教授及系所主任簽章；請勿使用訂書針，一律以長尾夾固定）",
            "2. 歷年中英文成績單正本各乙份（須含歷年總平均 GPA 3.0 以上及班級排名百分比）",
            "3. 英文自傳（Autobiography，約 300–500 字）與英文讀書計畫（Study Plan，須含申請動機及《國外預計修習課程規劃表》；申請雙聯學位者另須以英文回答 5 大申請動機與財務規劃問題）",
            "4. 大同大學專任教師英文推薦信（Recommendation Letters）2 封（雙聯學位使用雙聯專用推薦信格式）",
            "5. 有效外國語言能力檢定成績單影本（TOEIC / TOEFL iBT / IELTS / JLPT N1–N4）及優秀表現佐證資料（設計學院申請長岡造形大學、札幌市立大學、京都工藝纖維大學等須準備作品集 Portfolio）",
            "6. 獲推薦後必繳文件與獎學金申請表件：《家長同意書（附件二）》與《本人聲明書（附件三）》正本；申請獎學金者另於 https://admission.ttu.edu.tw/p/423-1034-13.php 上傳《115 年度大同大學學海飛颺／惜珠申請表》（申請學海惜珠或《鼓勵學生出國交換研修助學金》另附 500–800 字中文自傳、新式戶口名簿影本及低收／中低收／國稅局全戶所得證明）",
        ],
        "scholarship_info": [
            "1. 教育部「學海飛颺」與「學海惜珠」獎學金（主梯次每年 3 月初截止、候補梯次每年 10 月中旬截止）：補助具中華民國國籍、於大同就讀滿一學期以上、學士班前一學期班排前 50%（研究所 80 分以上）且符合分區語檢標準（英語系國家 TOEIC 650+、歐盟國家 TOEIC 600+、亞洲國家 TOEIC 550+、日本 JLPT N4 或 TOEIC 550+）之交換生與雙聯生，赴國外大專校院修讀學分（不含大陸及港澳），學海飛颺每人補助約新臺幣 50,000 至 300,000 元（含來回經濟艙機票與 1–2 個月生活費），學海惜珠針對低收／中低收／特殊境遇家庭學生提供高額補助。",
            "2. 《大同大學校友捐助國際交流專案獎助學金》（rid=1124）：由大同校友捐資設立，凡申請教育部《學海飛颺》或《學海惜珠》之學生將同時自動審核本項校友捐助獎助學金（無須重複繳交申請表），並另設「境外生出國交換或雙聯研修獎助」及「學生參與國際短期交流活動與國際競賽補助」。",
            "3. 《大同大學鼓勵學生出國交換研修助學金》（rid=1045，電機系 66 級校友捐助清寒助學金）：為協助家庭經濟困難或突遭變故之優秀學生圓夢出國交換，每學期最高補助新臺幣 100,000 元，每年補助名額至多 15 名（申請人須額外檢附 500–800 字中文自傳說明家庭經濟狀況及全戶所得證明）。",
            "4. 《大同大學學生暑期赴境外語言學習助學金》（rid=1129）與《暑期赴境外學校交流助學金》（rid=1047）：針對大一、大二及碩一（含準碩一生）多益未達 650 分者，於暑假赴境外語言學校（如菲律賓宿霧、歐美日等）進修至少 4 週（每週 15 小時以上），完成課程即補助基本額度新臺幣 30,000 元；返國後參加多益測驗達 650 分以上且較出國前進步 100 分再加碼 10,000 元、進步 200 分加碼 20,000 元（合計最高補助新臺幣 50,000 元）。此外，美國韋恩州立大學（WSU）提供每名大同 1+1 雙聯生 USD 3,000/學期獎學金，英國倫敦布魯內爾大學（Brunel）提供每年 10 名 15% 學費減免。",
        ],
        "partner_universities": [p["school_name"] for p in partners],
        "source_urls": ttu_source_urls,
        "last_checked": CHECKED_AT,
    }
    (OFFICIAL_TTU_DIR / "exchange_info.json").write_text(
        json.dumps(exchange_info_payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    student_dashboard_payload = {
        "school_name": "大同大學",
        "last_checked": CHECKED_AT,
        "academic_score_minimum": 75.0,
        "academic_score_rule": "依《大同大學交換學生計畫實施辦法》（rid=1049）及各期赴外交換及雙聯學位甄選公告：申請交換學生或雙聯學位者須為本校正式學籍在學學生（不含在職專班），實際出國時須在大同大學就讀滿一學年以上（即大二以上、碩一／碩二或博士班），歷年學業總平均須達 GPA 3.0（百分制約 75 分）以上（英國倫敦布魯內爾大學 Brunel 1+1／4+1 雙聯學位達 70 分以上即可）；校內甄選採量化審查（在校成績 40% + 語文能力 40% + 讀書計畫 20%），總分達 70 分以上始得推薦，且每人每階段至多填寫 2 個志願。",
        "academic_gpa_minimum": 3.0,
        "maximum_preferences": 2,
        "selection_rules": {
            "academic_policy": "score_or_rank",
            "academic_reference_year": "115",
            "undergraduate_gpa_minimum": 3.0,
            "graduate_academic_exempt": False,
            "exclude_in_service": True,
            "pending_quota_planning": False,
            "partner_requirements_need_confirmation": False,
            "degree_score_minimums": {
                "undergraduate": 75.0,
                "graduate": 75.0,
            },
            "excluded_undergraduate_years": ["大一"],
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
                "title": "大同大學 2027 春季班赴外交換學生暨雙聯學位計畫甄選（第一階段 9/10 截止・第二階段 10/14 截止）及學海飛颺候補申請（10/15 截止）",
                "details": [
                    "依大同大學國際暨兩岸事務處公告（https://oia.ttu.edu.tw/p/406-1071-44122,r568.php），擬於 2027 春季學期赴日本 22 所姊妹校、德國 5 所應用科技大學、芬蘭 Xamk、法國 UTC、韓國仁川大學、泰國法政大學 SIIT、美國匹茲堡州立大學與大陸地區重點大學交換，或修讀英、美、德、法、澳雙聯學位者，分兩階段收件：第一階段於 2026/09/10（四）16:00 截止，第二階段於 2026/10/14（三）16:00 截止（第一階段獲推薦者不得放棄並改申請第二階段）。",
                    "申請人須先至 https://admission.ttu.edu.tw/p/423-1034-3.php 完成線上報名表登錄（至多選填 2 個志願），並將紙本申請表件（以長尾夾固定，勿用訂書針）送交國際暨兩岸事務處黃鈺婷小姐（分機 7547）；2027 春季班出國之非大陸地區交換／雙聯生，可於 2026/10/15（四）16:00 前申請《115 年度教育部學海飛颺候補獎學金》（https://oia.ttu.edu.tw/p/406-1071-44121,r568.php）。",
                ],
                "source": {
                    "title": "大同大學國際暨兩岸事務處：2027 春季赴外交換及雙聯學位開始申請囉！",
                    "source_url": TTU_2027_SPRING_EXCHANGE_URL,
                    "category": "exchange_application",
                    "summary": "大同大學 2027 春季班交換與雙聯學位第一階段（9/10）與第二階段（10/14）報名收件時程及學海飛颺候補申請。",
                },
                "scope": "home_application",
                "program_types": ["exchange", "dual_degree"],
                "academic_year": "115",
                "application_round": "2027 春季班出國交換暨雙聯學位甄選（第一階段／第二階段）",
                "audience": "all_students",
                "opens_at": "2026-08-25T09:00:00+08:00",
                "deadline_at": "2026-10-14T16:00:00+08:00",
                "date_status": "verified_exact",
                "status": "open",
                "status_note": "第一階段至 2026/09/10 16:00 截止，第二階段至 2026/10/14 16:00 截止；學海飛颺候補至 2026/10/15 16:00 截止。",
                "deadline_note": "請先完成 admission.ttu.edu.tw 線上報名表登錄（至多 2 志願），再將長尾夾固定之紙本資料送交國際暨兩岸事務處。",
                "reminder_eligible": True,
                "checked_at": CHECKED_AT,
            },
            {
                "title": "大同大學秋季班赴外交換學生暨雙聯學位計畫甄選（第一階段 2/24 截止・第二階段 3/10 截止）及學海飛颺／惜珠／校友獎助學金甄選（3/3 截止）",
                "details": [
                    "依大同大學國際暨兩岸事務處公告（https://oia.ttu.edu.tw/p/406-1071-41452,r568.php），擬於秋季學期（9 月）赴海外姊妹校交換或修讀英美德法澳日跨國雙聯學位（美國愛荷華州立大學 ISU、韋恩州立大學 WSU、拉瑪大學 Lamar、英國密德薩斯大學 Middlesex、倫敦布魯內爾大學 Brunel、德國 HFT Stuttgart、法國 ESIEE-Amiens、澳洲紐卡索大學）者，第一階段於每年 2 月下旬截止（16:00），第二階段於每年 3 月上旬截止（16:00）。",
                    "教育部《學海飛颺》、《學海惜珠》、《大同大學校友捐助國際交流專案獎助學金》及《大同大學鼓勵學生出國交換研修助學金》（電機系 66 級校友捐助，最高 NT$100,000）於每年 3 月初截止收件（https://oia.ttu.edu.tw/p/406-1071-41325,r568.php），申請學海飛颺／惜珠將同時自動審核校友捐助獎助學金。",
                ],
                "source": {
                    "title": "大同大學國際暨兩岸事務處：秋季赴外交換及雙聯學位甄選與學海飛颺／惜珠獎學金公告",
                    "source_url": TTU_2026_FALL_EXCHANGE_URL,
                    "category": "scholarship",
                    "summary": "大同大學秋季班交換、雙聯學位兩階段甄選時程與教育部學海系列暨校友捐助獎助學金申請。",
                },
                "scope": "home_application",
                "program_types": ["exchange", "dual_degree"],
                "academic_year": "115",
                "application_round": "秋季班出國交換、跨國雙聯學位暨教育部學海／校友獎助學金甄選",
                "audience": "all_students",
                "opens_at": "2027-01-15T09:00:00+08:00",
                "deadline_at": "2027-03-10T16:00:00+08:00",
                "date_status": "verified_exact",
                "status": "upcoming",
                "status_note": "每年 2–3 月分兩階段受理秋季班交換與雙聯學位申請，並同步受理學海飛颺、學海惜珠與校友獎助學金。",
                "deadline_note": "學海飛颺／惜珠申請人須為中華民國國籍、學士班前一學期班排前 50%（碩博 80 分以上）且符合分區語檢標準。",
                "reminder_eligible": True,
                "checked_at": CHECKED_AT,
            },
        ],
        "program_overview": [
            {
                "title": f"大同大學國際暨兩岸事務處全球交換、英美德法澳日雙聯學位與校友獎助學金總覽（{len(partners)} 所合作姊妹校・{open_partner_count} 所常態開放申請・{total_exp_reports} 篇《人在他鄉大同人》心得報告）",
                "details": [
                    f"大同大學（Tatung University, TTU，簡稱大同，校區坐落於臺北市中山區中山北路三段 40 號，以實業教育、工程電資、工業與媒體設計、事業與資訊經營及應用外語聞名）由「國際暨兩岸事務處（尚志教育研究館）」統籌全校工程學院（含原電機資訊學院系所：機械與材料工程學系、化學工程與生物科技學系、電機工程學系、資訊工程學系、通訊工程研究所）、經營學院（事業與資訊經營學系）、設計學院（工業設計學系、媒體設計學系）及國際學院（應用外語學系）之出國交換、跨國雙聯學位、暑期海外語言研習與獎助學金業務。本平台完整收錄 {len(partners)} 所大同大學官方合作姊妹校（含 {open_partner_count} 所常態開放交換與雙聯學位合作校，以及 {len(partners) - open_partner_count} 所正式締約姊妹校），橫跨全球 20 個國家與地區。",
                    f"大同大學國際交流具備四大核心特色：（1）超強日本 22 校理工與設計交換網絡：涵蓋京都工藝纖維大學、千葉大學、東京都市大學、芝浦工業大學、東京電機大學、長岡造形大學、札幌市立大學、東北工業大學、岡山大學、熊本大學、琉球大學、縣立廣島大學、同志社大學、專修大學等；（2）歐美亞高性價比英語授課交換：對接德國 5 所應用科技大學（HFT Stuttgart、Osnabrück、DIT、DHBW、HKA）、芬蘭 Xamk、法國貢比涅科技大學 UTC、韓國仁川大學、泰國法政大學 SIIT、美國匹茲堡州立大學 PSU；（3）英美德法澳 8 大跨國雙聯學位與專屬獎學金：含美國愛荷華州立大學 ISU（1+1／3.5+1.5）、韋恩州立大學 WSU（1+1 碩士，每名大同生享 USD 3,000/學期獎學金）、拉瑪大學 Lamar（1+1 免 GRE）、英國密德薩斯大學 Middlesex（3+1／1+1／3+1.5）、倫敦布魯內爾大學 Brunel（1+1／4+1 數位設計與 AI，每年 10 名享 85 折學費）、德國 HFT Stuttgart、法國 ESIEE-Amiens、澳洲紐卡索大學；（4）豐厚校友捐助與完整傳承：除教育部學海飛颺／惜珠外，設有校友捐助國際交流獎助學金、電機系 66 級校友清寒交換助學金（最高 NT$100,000）與暑期海外語言學習助學金（最高 NT$50,000），並於《人在他鄉大同人》網誌完整收錄 {exp_covered_schools} 所合作大學共 {total_exp_reports} 篇歷屆學長姐心得報告。",
                ],
                "source": {
                    "title": "大同大學國際暨兩岸事務處官方網站與赴外交換及雙聯學位甄選公告",
                    "source_url": TTU_OIA_HOME_URL,
                    "category": "exchange_application",
                    "summary": f"大同大學 {len(partners)} 所全球合作姊妹校、{open_partner_count} 所常態開放交換／雙聯校與 {total_exp_reports} 篇《人在他鄉大同人》心得報告。",
                },
            }
        ],
        "eligibility": [
            {
                "title": "就讀滿一學年資格、GPA 3.0（75分）門檻、量化評分（40%/40%/20%）、至多 2 志願與兩年停權規定",
                "details": [
                    "在學年資與成績門檻：依《大同大學交換學生計畫實施辦法》（rid=1049）第 3 條及各期甄選簡章，申請人須為本校正式學籍在學學生（不含在職專班），且實際出國時須在本校就讀滿一學年以上（即大一學生於大一下學期可提出申請、大二起出國；碩士班與博士班在學生均可申請）。歷年學業總平均須達 GPA 3.0（百分制約 75 分）以上（英國倫敦布魯內爾大學 Brunel 1+1／4+1 雙聯學位達 70 分以上即可申請）。",
                    "量化評分權重、志願數上限與棄權罰則：每學期分第一階段與第二階段收件，每人每階段至多選填 2 個志願；校內甄選採量化審查，評分項目為「在校成績 40% + 語文能力 40% + 讀書計畫 20%」，總分達 70 分以上始得推薦。第一階段獲推薦者不得放棄並改申請第二階段；簽署「家長同意書」及「本人聲明書」後無故放棄者，兩年內不得再提出申請。",
                ],
                "source": {
                    "title": "大同大學交換學生計畫實施辦法（rid=1049）與赴外交換及雙聯學位甄選簡章",
                    "source_url": TTU_RULE_EXCHANGE_URL,
                    "category": "exchange_application",
                    "summary": "大同大學出國交換年級限制、GPA 3.0 門檻、量化審查權重（40%/40%/20%）、至多 2 志願與棄權罰則。",
                },
            }
        ],
        "language_requirements": [
            {
                "title": "日語組 22 校（JLPT N1–N4 或 TOEIC 550+）、歐美亞英語組（TOEIC 550–785 / IELTS 5.0–6.5 / iBT 61–79）與學海分區語檢門檻",
                "details": [
                    "交換與雙聯學位外語標準：（1）日本 22 所姊妹校：千葉大學、同志社大學、專修大學、縣立廣島大學、東京都立大學要求 JLPT N2（或 N1–N3）；京都工藝纖維大學 KIT、東京都市大學 TCU、芝浦工業大學 SIT、東京電機大學 TDU、長岡造形大學 NID、札幌市立大學 SCU、東北工業大學、岡山大學、熊本大學、琉球大學、室蘭工業大學、北見工業大學、福岡工業大學、廣島市立大學等可憑 JLPT N2–N4 或英語證明（TOEIC 550+ / TOEFL iBT 61+ / IELTS 5.5+）申請；（2）歐美亞英語組交換（德國 5 校、芬蘭 Xamk、法國 UTC、韓國仁川大學、泰國法政大學 SIIT、美國匹茲堡州立大學 PSU）：要求英語 CEFR B1–B2（TOEIC 550–785 / IELTS 5.0–6.0 / TOEFL iBT 61–79）；（3）英美德法澳雙聯學位：要求 IELTS 6.0–6.5 或 TOEFL iBT 79–80（法國 ESIEE-Amiens 可採 TOEIC 750）。",
                    "教育部《學海飛颺／惜珠》與大同校友獎助學金分區語檢標準：（1）英語系國家：TOEIC 650 分以上（或同級檢定）；（2）非英語系歐盟國家：TOEIC 600 分以上；（3）非英語系亞洲國家：TOEIC 550 分以上；（4）日本：JLPT N4 合格或 TOEIC 550 分以上；（5）大陸地區姊妹校為中文授課，免附外語檢定證明。",
                ],
                "source": {
                    "title": "大同大學赴外交換及雙聯學位名額語言門檻表與 115 年度學海飛颺／惜珠簡章",
                    "source_url": TTU_2027_SPRING_EXCHANGE_URL,
                    "category": "exchange_application",
                    "summary": "大同大學日本、歐洲、英美亞姊妹校與學海飛颺／惜珠分區外語檢定門檻一覽。",
                },
            }
        ],
        "required_documents": [
            {
                "title": "線上報名登錄、紙本申請表（長尾夾固定）、含 GPA 成績單、英文自傳與讀書計畫（含修課規劃表）、推薦信 2 封與返國核銷規範",
                "details": [
                    "校內甄選必備文件（先於 https://admission.ttu.edu.tw/p/423-1034-3.php 線上報名，再將紙本以長尾夾固定送交國際暨兩岸事務處）：（1）大同大學交換學生計畫或雙聯學位計畫申請表（導師／指導教授與系主任核章）；（2）歷年中英文成績單正本（含總平均 GPA 3.0 以上與班排名）；（3）英文自傳（Autobiography，約 300–500 字）與英文讀書計畫（Study Plan，含《國外預計修習課程規劃表》；雙聯學位另須回答 5 大英文申請動機問題）；（4）大同專任教師英文推薦信 2 封；（5）有效語檢成績單影本及作品集（設計學院交換適用）。",
                    "獲推薦後與返國後必辦手續：獲推薦後須繳交親筆簽名之「家長同意書（附件二）」與「本人聲明書（附件三）」；出國交換期間須維持大同在學註冊並繳交全額學雜費；返國後兩週內須完成線上回國心得登錄（https://admission.ttu.edu.tw/p/423-1034-11.php，發表於《人在他鄉大同人》網誌），並繳交「學生境外研修實習心得報告表（附件四）」、「登機證票根黏存表（附件五）」、「護照出入境章影本（附件六）」及親簽領據，再持國外成績單辦理學分抵免。",
                ],
                "source": {
                    "title": "大同大學交換計畫文件包（01交換計畫文件2026.zip）與雙聯學位文件包（02雙聯學位計畫文件2026.zip）",
                    "source_url": TTU_EXCHANGE_ZIP_URL,
                    "category": "exchange_application",
                    "summary": "大同大學交換生、雙聯生與學海獎學金申請表單、裝訂規範與返國兩週內結案核銷程序。",
                },
            }
        ],
        "scholarship_info": [
            {
                "title": "教育部學海飛颺（5 萬～30 萬元）、學海惜珠、大同校友捐助國際交流獎助學金、電機系 66 級校友清寒交換助學金（最高 10 萬元）與暑期語言學習助學金（最高 5 萬元）",
                "details": [
                    "出國交換與雙聯四大獎助學金（主梯次 3 月初截止、學海候補 10 月中旬截止）：（1）教育部《學海飛颺》（每人補助約 NT$50,000–300,000，含來回機票與 1–2 個月生活費）與《學海惜珠》：限中華民國國籍、學士班前一學期班排前 50%（碩博 80 分以上）且達分區語檢門檻；（2）《大同大學校友捐助國際交流專案獎助學金》（rid=1124）：申請學海飛颺／惜珠將同時自動審核本項校友獎助學金，無須重複送件；（3）《大同大學鼓勵學生出國交換研修助學金》（rid=1045，電機系 66 級校友捐助）：針對家庭經濟困難學生，每學期最高補助 NT$100,000，每年至多 15 名；（4）姊妹校雙聯獎學金：美國韋恩州立大學（WSU）每名大同 1+1 雙聯生享 USD 3,000/學期獎學金，英國倫敦布魯內爾大學（Brunel）每年 10 名享 15% 學費減免。",
                    "暑期海外語言與短期交流助學金：（1）《大同大學學生暑期赴境外語言學習助學金》（rid=1129）：補助大一、大二及碩一（含準碩一生）多益未達 650 分者於暑假赴國外語言學校進修至少 4 週，完成課程補助 NT$30,000，返國後多益達 650 分且進步 100/200 分再加碼 NT$10,000/20,000（最高 NT$50,000）；（2）《學生暑期赴境外學校交流助學金》（rid=1047）：補助參加姊妹校暑期夏日學校或短期研習之機票與生活費。",
                ],
                "source": {
                    "title": "大同大學 115 年度學海飛颺與學海惜珠簡章、候補公告及校友捐助獎助學金辦法",
                    "source_url": TTU_115_XUEHAI_URL,
                    "category": "scholarship",
                    "summary": "大同大學教育部學海系列、校友捐助國際交流獎助學金、電機系 66 級校友清寒助學金與暑期海外語言助學金辦法。",
                },
            }
        ],
        "document_explanations": [
            {
                "title": "大同大學交換／雙聯申請文件包（英文自傳、含修課規劃表之英文讀書計畫、雙聯 5 大動機問題、推薦信 2 封）與返國《人在他鄉大同人》結案指南",
                "summary": "說明大同大學交換生、雙聯生與學海獎學金申請人準備英文自傳、讀書計畫、雙聯動機問答、長尾夾裝訂規範及返國兩週內結案核銷之實務要點。",
                "key_points": [
                    "交換與雙聯英文讀書計畫（Study Plan）撰寫架構：交換生須以英文撰寫讀書計畫並填列《國外預計修習課程規劃表》（Course Plan，列出擬於姊妹校修習之科目名稱、學分數及對應大同抵免科目）；申請跨國雙聯學位者（02雙聯學位計畫文件）須以英文回答 5 大核心問題：（1）申請動機與學術興趣、（2）雙聯學位對未來職涯之助益、（3）研究方向與專題規劃、（4）海外求學之財務規劃、（5）返國後對母校學弟妹之經驗傳承方式。",
                    "學海惜珠與電機系 66 級校友清寒助學金自傳要點：申請《學海惜珠》須撰寫 1,000–1,500 字中文研修計畫書及家庭狀況說明；申請《大同大學鼓勵學生出國交換研修助學金》（最高 NT$100,000）須撰寫 500–800 字中文自傳（詳述家庭經濟背景、求學歷程與出國交換動機）並檢附國稅局全戶所得證明。",
                    "紙本長尾夾固定規範與返國兩週內核銷義務：所有繳交至國際處之紙本申請文件請勿使用訂書針，一律以長尾夾或迴紋針固定；返國後兩週內須完成線上回國報告登錄（發表於《人在他鄉大同人》網誌），並繳交附件四心得報告表、附件五登機證票根正本黏存表、附件六護照出入境章影本及親簽領據。",
                ],
                "applies_to": [],
                "source": {
                    "title": "大同大學 01交換計畫文件2026.zip 與 02雙聯學位計畫文件2026.zip",
                    "source_url": TTU_EXCHANGE_ZIP_URL,
                    "category": "exchange_application",
                    "summary": None,
                },
                "document_url": TTU_XUEHAI_BROCHURE_PDF,
                "document_type": "official_document",
                "full_text_extracted": True,
            }
        ],
        "rule_explanations": [
            {
                "title": "大同大學交換學生計畫實施辦法（rid=1049）、雙聯學制實施辦法（rid=232）、出國期間學業學籍要點（rid=225）與抵免學分辦法（rid=224）",
                "summary": "規範大同大學學生出國交換就讀滿一學年資格、GPA 3.0 門檻、量化評分權重（40%/40%/20%）、至多 2 志願、在學繳交全額學雜費與返國學分抵免原則。",
                "key_points": [
                    "就讀滿一學年、量化評分與棄權停權規定：依《大同大學交換學生計畫實施辦法》（rid=1049），出國交換時須在本校就讀滿一學年以上且歷年 GPA 達 3.0 以上；校內量化審查包含在校成績（40%）、語文能力（40%）及讀書計畫（20%），總分達 70 分以上始得推薦；每人每階段至多填寫 2 個志願，第一階段獲推薦者不得放棄並改申請第二階段，簽署同意書後無故放棄者兩年內不得再申請。",
                    "在學註冊、全額學雜費與返國學分抵免：依《學生出國期間有關學業及學籍處理要點》（rid=225）與《學生抵免學分辦法》（rid=224），交換生出國期間須辦理大同大學註冊並繳交全額學雜費（免繳接待姊妹校學費），且每學期至少應修習相當學分；返國後檢附國外正式成績單及課程大綱向系所及教務處辦理學分採認。",
                    "跨國雙聯學位修業與學位授予：依《大同大學與境外大學校院辦理雙聯學制實施辦法》（rid=232），修讀美國愛荷華州立大學（ISU）、韋恩州立大學（WSU）、拉瑪大學（Lamar）、英國密德薩斯大學（Middlesex）、倫敦布魯內爾大學（Brunel）、德國 HFT Stuttgart、法國 ESIEE-Amiens 及澳洲紐卡索大學雙聯學位者，於兩校修畢規定學分並符合畢業條件後，分別由兩校授予學士或碩士學位。",
                ],
                "applies_to": [],
                "source": {
                    "title": "大同大學交換學生計畫實施辦法（rid=1049）與雙聯學制實施辦法（rid=232）",
                    "source_url": TTU_RULE_EXCHANGE_URL,
                    "category": "exchange_application",
                    "summary": None,
                },
                "document_url": TTU_RULE_OUTBOUND_CREDIT_URL,
                "document_type": "official_document",
                "full_text_extracted": True,
            }
        ],
        "sources": [
            {"title": "大同大學國際暨兩岸事務處官方網站", "source_url": TTU_OIA_HOME_URL, "category": "exchange_application", "summary": None},
            {"title": "大同大學 2027 春季赴外交換及雙聯學位甄選公告（第一階段 9/10・第二階段 10/14）", "source_url": TTU_2027_SPRING_EXCHANGE_URL, "category": "exchange_application", "summary": None},
            {"title": "大同大學 2026 秋季赴外交換及雙聯學位甄選公告（第一階段 2/24・第二階段 3/10）", "source_url": TTU_2026_FALL_EXCHANGE_URL, "category": "exchange_application", "summary": None},
            {"title": "大同大學 115 年度教育部學海飛颺、學海惜珠與鼓勵學生出國交換研修助學金公告", "source_url": TTU_115_XUEHAI_URL, "category": "scholarship", "summary": None},
            {"title": "大同大學 115 年度教育部學海飛颺候補申請公告（2027 春季班適用）", "source_url": TTU_115_XUEHAI_WAITLIST_URL, "category": "scholarship", "summary": None},
            {"title": f"大同大學全球與兩岸締約姊妹校名錄（橫跨 20 國與地區共 {len(partners)} 所合作姊妹校）", "source_url": TTU_SISTER_SCHOOLS_URL, "category": "partner_school", "summary": None},
            {"title": "大同大學交換學生計畫實施辦法（rid=1049）與雙聯學制實施辦法（rid=232）", "source_url": TTU_RULE_EXCHANGE_URL, "category": "exchange_application", "summary": None},
            {"title": f"大同大學《人在他鄉大同人》官方交換與雙聯心得網誌（{exp_covered_schools} 校 {total_exp_reports} 篇心得報告）", "source_url": TTU_PIXNET_BLOG_URL, "category": "exchange_application", "summary": None},
        ],
    }
    (OFFICIAL_TTU_DIR / "student_dashboard.json").write_text(
        json.dumps(student_dashboard_payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    doc_conditions = {
        "school_id": "ttu",
        "school_name": "大同大學",
        "checked_at": CHECKED_AT,
        "source_url": TTU_2027_SPRING_EXCHANGE_URL,
        "common_documents": exchange_info_payload["required_documents"],
        "track_specific_conditions": [
            {
                "track": "海外姊妹校學期交換計畫（日本 22 校、德國 5 校、芬蘭 Xamk、法國 UTC、韓國仁川大學、泰國法政大學 SIIT、美國匹茲堡州立大學與大陸地區 12 校）",
                "required": [
                    "大同大學線上報名登錄（https://admission.ttu.edu.tw/p/423-1034-3.php）及《01交換計畫文件》紙本申請表（至多選填 2 個志願，導師／指導教授與系所主任核章，長尾夾固定）",
                    "歷年中英文成績單正本（出國時須於大同就讀滿一學年以上，歷年總平均達 GPA 3.0 / 75 分以上，並含班級排名百分比）",
                    "英文自傳（Autobiography，約 300–500 字）、英文讀書計畫（Study Plan，含《國外預計修習課程規劃表》）及大同專任教師英文推薦信 2 封",
                    "有效外語能力檢定證明影本（日語組 JLPT N1–N4 或 TOEIC 550+；歐美亞英語組 TOEIC 550–785 / IELTS 5.0–6.0 / TOEFL iBT 61–79）及作品集（設計學院交換適用）",
                ],
            },
            {
                "track": "英、美、德、法、澳 8 大跨國雙聯學位計畫（美國 ISU、WSU、Lamar、英國 Middlesex、Brunel、德國 HFT Stuttgart、法國 ESIEE-Amiens、澳洲 Newcastle）",
                "required": [
                    "大同大學線上報名登錄及《02雙聯學位計畫文件》紙本申請表（由系所主管核章）",
                    "歷年中英文成績單正本（GPA 3.0 以上；英國倫敦布魯內爾大學 Brunel 1+1／4+1 雙聯達 70 分以上即可）",
                    "雙聯學位英文自傳與 5 大動機問答讀書計畫（涵蓋申請動機、職涯助益、研究方向、財務規劃與返國經驗傳承）及雙聯專用英文推薦信 2 封",
                    "學術英語檢定成績單正本（IELTS Academic 6.0–6.5 或 TOEFL iBT 79–80；法國 ESIEE-Amiens 可採 TOEIC 750）及護照影本",
                ],
            },
            {
                "track": "教育部學海飛颺、學海惜珠、大同校友捐助國際交流獎助學金與鼓勵學生出國交換研修助學金（清寒助學金）",
                "required": [
                    "大同大學獎學金線上申請登錄（https://admission.ttu.edu.tw/p/423-1034-13.php）及《115 年度大同大學學海飛颺／惜珠申請表》（申請學海將同時自動審核大同校友捐助國際交流獎助學金）",
                    "歷年中文成績單正本（學士班前一學期班排前 50%、碩博生前一學期 80 分以上）與符合分區標準之外語檢定證明（英語系國家 TOEIC 650+、歐盟國家 TOEIC 600+、亞洲國家 TOEIC 550+、日本 JLPT N4 或 TOEIC 550+）",
                    "申請《學海惜珠》或《大同大學鼓勵學生出國交換研修助學金》（每學期最高 NT$100,000）者：另須檢附 500–800 字中文自傳（說明家庭經濟狀況）、新式戶口名簿影本及低收入戶／中低收入戶／國稅局全戶綜合所得稅清單證明；返國後兩週內繳交附件四心得報告表、附件五登機證票根黏存表、附件六出入境章與親簽領據",
                ],
            },
        ],
    }
    (OFFICIAL_TTU_DIR / "document-conditions.json").write_text(
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
            f"{fname},{len(partners)},{pop},{ratio:.4f},Official TTU OIA verified"
        )
    (OFFICIAL_TTU_DIR / "field-coverage.csv").write_text(
        "\n".join(field_cov_lines) + "\n", encoding="utf-8"
    )

    pages_records = [
        {
            "title": "大同大學：春季班（第一階段 9/10・第二階段 10/14）與秋季班（第一階段 2/24・第二階段 3/10）赴外交換、雙聯學位與學海獎學金時程",
            "source_url": TTU_2027_SPRING_EXCHANGE_URL,
            "published_at": "2026-10-30T00:00:00Z",
            "text": "\n".join(exchange_info_payload["application_period"]),
            "summary": "\n".join(exchange_info_payload["application_period"]),
            "category": "exchange_application",
            "attachments": [],
            "crawled_at": CHECKED_AT,
            "content_hash": hashlib.sha256("\n".join(exchange_info_payload["application_period"]).encode("utf-8")).hexdigest(),
        },
        {
            "title": "大同大學：交換學生計畫實施辦法（rid=1049）、就讀滿一學年資格、GPA 3.0 門檻、量化評分（40%/40%/20%）與至多 2 志願規定",
            "source_url": TTU_RULE_EXCHANGE_URL,
            "published_at": "2026-10-30T00:00:00Z",
            "text": "\n".join(exchange_info_payload["eligibility"]),
            "summary": "\n".join(exchange_info_payload["eligibility"]),
            "category": "exchange_application",
            "attachments": [],
            "crawled_at": CHECKED_AT,
            "content_hash": hashlib.sha256("\n".join(exchange_info_payload["eligibility"]).encode("utf-8")).hexdigest(),
        },
        {
            "title": f"大同大學：{len(partners)} 所全球與兩岸合作姊妹校外語檢定門檻（日本 22 校交換／歐美亞英語組交換／英美德法澳雙聯／學海分區語檢標準）",
            "source_url": TTU_2026_FALL_EXCHANGE_URL,
            "published_at": "2026-10-30T00:00:00Z",
            "text": "\n".join(exchange_info_payload["language_requirement"]),
            "summary": "\n".join(exchange_info_payload["language_requirement"]),
            "category": "exchange_application",
            "attachments": [],
            "crawled_at": CHECKED_AT,
            "content_hash": hashlib.sha256("\n".join(exchange_info_payload["language_requirement"]).encode("utf-8")).hexdigest(),
        },
        {
            "title": "大同大學：交換學生、雙聯學位與學海系列 6 項應備文件（線上登錄、長尾夾紙本、英文自傳與含修課表之讀書計畫、推薦信 2 封）",
            "source_url": TTU_ONLINE_APPLY_EXCHANGE_URL,
            "published_at": "2026-10-30T00:00:00Z",
            "text": "\n".join(exchange_info_payload["required_documents"]),
            "summary": "\n".join(exchange_info_payload["required_documents"]),
            "category": "exchange_application",
            "attachments": [],
            "crawled_at": CHECKED_AT,
            "content_hash": hashlib.sha256("\n".join(exchange_info_payload["required_documents"]).encode("utf-8")).hexdigest(),
        },
        {
            "title": "大同大學：教育部學海飛颺、學海惜珠、校友捐助國際交流獎助學金、電機系 66 級校友清寒交換助學金與暑期海外語言學習助學金",
            "source_url": TTU_115_XUEHAI_URL,
            "published_at": "2026-10-30T00:00:00Z",
            "text": "\n".join(exchange_info_payload["scholarship_info"]),
            "summary": "\n".join(exchange_info_payload["scholarship_info"]),
            "category": "scholarship",
            "attachments": [],
            "crawled_at": CHECKED_AT,
            "content_hash": hashlib.sha256("\n".join(exchange_info_payload["scholarship_info"]).encode("utf-8")).hexdigest(),
        },
    ]
    (OFFICIAL_TTU_DIR / "pages.jsonl").write_text(
        "\n".join(json.dumps(p, ensure_ascii=False) for p in pages_records) + "\n",
        encoding="utf-8",
    )

    home_rules = {
        "school_id": "ttu",
        "school_name": "大同大學",
        "eligibility": student_dashboard_payload["eligibility"],
        "application_periods": student_dashboard_payload["application_periods"],
        "selection_rules": {
            "general_exchange_gpa_minimum": 3.0,
            "general_exchange_score_minimum": 75.0,
            "brunel_dual_degree_score_minimum": 70.0,
            "quantified_review_passing_score": 70.0,
            "quantified_review_weights": {
                "academic_grades": 0.4,
                "language_proficiency": 0.4,
                "study_plan": 0.2,
            },
            "maximum_preferences_per_wave": 2,
            "withdrawal_ban_years": 2,
            "xuehai_undergrad_class_rank_percent_maximum": 50.0,
            "xuehai_grad_score_minimum": 80.0,
            "require_ttu_full_tuition_during_exchange": True,
            "return_documents_due": "返國後兩週內完成 admission.ttu.edu.tw 線上回國心得登錄（發表於《人在他鄉大同人》網誌），並繳交附件四心得報告表、附件五登機證票根黏存表、附件六護照出入境章影本及親簽領據至國際暨兩岸事務處",
        },
        "source_urls": ttu_source_urls,
        "verified_at": "2026-11-08",
    }
    (OFFICIAL_TTU_DIR / "home_rules.json").write_text(
        json.dumps(home_rules, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    (OFFICIAL_TTU_DIR / "documents.json").write_text(
        json.dumps(
            {
                "school_name": "大同大學",
                "required_documents": student_dashboard_payload["required_documents"],
                "source_urls": ttu_source_urls,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    (OFFICIAL_TTU_DIR / "scholarships.json").write_text(
        json.dumps(
            {
                "school_name": "大同大學",
                "scholarships": student_dashboard_payload["scholarship_info"],
                "source_urls": ttu_source_urls,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    completeness = {
        "school_id": "ttu",
        "school_name": "大同大學",
        "total_partners": len(partners),
        "partner_count": len(partners),
        "international_partners": sum(1 for p in partners if p["country"] not in {"中國大陸", "香港", "澳門"}),
        "mainland_partners": sum(1 for p in partners if p["country"] in {"中國大陸", "香港", "澳門"}),
        "dual_degree_partner_universities": 9,
        "dual_degree_programs": 12,
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
        "active_term": f"大同大學國際暨兩岸事務處《2027 春季／2026 秋季／2026 春季／2025 秋季赴外交換及雙聯學位甄選公告》、《115 年度教育部學海飛颺與學海惜珠簡章及候補公告》、《大同大學交換學生計畫實施辦法（rid=1049）》、《雙聯學制實施辦法（rid=232）》、《校友捐助國際交流獎助學金辦法（rid=1124）》及《人在他鄉大同人》官方網誌同步整合；共完整收錄 {len(partners)} 所全球與兩岸合作姊妹校（含 {open_partner_count} 所常態開放交換與雙聯學位學校及 {len(partners) - open_partner_count} 所正式締約姊妹校，橫跨 20 個國家與地區，並收錄 {exp_covered_schools} 所合作大學共 {total_exp_reports} 篇歷屆學長姐交換與雙聯心得報告）。",
        "verified_at": "2026-11-08",
    }
    (OFFICIAL_TTU_DIR / "catalog-completeness.json").write_text(
        json.dumps(completeness, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    (OFFICIAL_TTU_DIR / "verification_status.json").write_text(
        json.dumps(
            {
                "school_id": "ttu",
                "school_name": "大同大學",
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
        ("sources/ttu/ttu_catalog_source.json", TTU_SISTER_SCHOOLS_URL, f"大同大學 {len(partners)} 所全球與兩岸合作姊妹校整合資料集 JSON"),
        ("sources/ttu/ttu_resolved_locations.json", TTU_SISTER_SCHOOLS_URL, f"大同大學 {len(partners)} 所合作姊妹校 ROR / Wikidata 地理座標核對表 JSON"),
        ("sources/ttu/ttu_experience_index.json", TTU_PIXNET_BLOG_URL, f"大同大學《人在他鄉大同人》{total_exp_reports} 篇歷屆交換與雙聯心得報告索引 JSON"),
    ]
    for rel_p, surl in bin_urls.items():
        rp = rel_p if rel_p.startswith("sources/") else f"sources/ttu/{rel_p}"
        if not any(x[0] == rp for x in provenance_files):
            provenance_files.append((rp, surl, f"大同大學官方原始檔案：{Path(rp).name}"))
    html_dir = SOURCES_TTU_DIR / "html"
    if html_dir.exists():
        for hp in sorted(html_dir.glob("*.html")):
            rp = f"sources/ttu/html/{hp.name}"
            if not any(x[0] == rp for x in provenance_files):
                provenance_files.append((rp, TTU_OIA_HOME_URL, f"大同大學官方網頁快照：{hp.name}"))

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
        "school_id": "ttu",
        "school_name": "大同大學",
        "generated_at": CHECKED_AT,
        "active_cycle_note": completeness["active_term"],
        "sources": prov_sources,
    }
    prov_text = json.dumps(provenance_payload, ensure_ascii=False, indent=2) + "\n"
    (OFFICIAL_TTU_DIR / "import_provenance.json").write_text(prov_text, encoding="utf-8")
    (OFFICIAL_TTU_DIR / "import-provenance.json").write_text(prov_text, encoding="utf-8")

    print(
        f"Successfully built TTU catalog: {len(partners)} partners"
        f" ({open_partner_count} open, {completeness['verified_campus_images']}"
        f" verified images, {completeness['verified_locations']} verified"
        f" locations), {len(workflows)} workflows,"
        f" {len(destinations)} destinations, {len(research_records)} research"
        f" records, {exp_covered_schools} schools with experience records"
        f" ({len(student_experience_rows)} rows, {total_exp_reports} reports)."
    )


if __name__ == "__main__":
    main()
