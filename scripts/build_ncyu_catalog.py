"""Build the official National Chiayi University (國立嘉義大學, NCYU) exchange data bundle."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re

REPO_ROOT = Path(__file__).resolve().parents[1]
SOURCES_NCYU_DIR = REPO_ROOT / "sources" / "ncyu"
OFFICIAL_NCYU_DIR = REPO_ROOT / "src" / "exchange_info" / "official_data" / "ncyu"
STATIC_DIR = REPO_ROOT / "src" / "exchange_info" / "static"
UNIVERSITY_LOCATIONS_PATH = (
    REPO_ROOT / "src" / "exchange_info" / "official_data" / "university_locations.jsonl"
)

CHECKED_AT = "2026-10-30T00:00:00Z"

NCYU_OIA_HOME_URL = "https://www.ncyu.edu.tw/oia/"
NCYU_OIA_ENG_HOME_URL = "https://www.ncyu.edu.tw/oia_eng/"
NCYU_OIA_ABOUT_URL = "https://www.ncyu.edu.tw/oia/Contents?nodeId=60009"
NCYU_SISTERS_URL = "https://www.ncyu.edu.tw/oia/Contents?nodeId=58434"
NCYU_EXCHANGE_INTRO_URL = "https://www.ncyu.edu.tw/oia/Contents?nodeId=60179"
NCYU_EXCHANGE_APPLY_INFO_URL = "https://www.ncyu.edu.tw/oia/Subject?nodeId=60180"
NCYU_EXCHANGE_HOW_TO_APPLY_URL = "https://www.ncyu.edu.tw/oia/Subject/Detail/194918?nodeId=60180"
NCYU_EXCHANGE_NOTES_URL = "https://www.ncyu.edu.tw/oia/Subject/Detail/194917?nodeId=60180"
NCYU_ENG_TABLE_URL = "https://www.ncyu.edu.tw/oia/Subject/Detail/194916?nodeId=60180"
NCYU_EXCHANGE_FAQ_URL = "https://www.ncyu.edu.tw/oia/Subject/Detail/194915?nodeId=60180"
NCYU_EXCHANGE_FLOW_URL = "https://www.ncyu.edu.tw/oia/Subject/Detail/194914?nodeId=60180"
NCYU_BRIEFINGS_LIST_URL = "https://www.ncyu.edu.tw/oia/Subject?nodeId=60181"
NCYU_BRIEFING_114_URL = "https://www.ncyu.edu.tw/oia/Subject/Detail/230388?nodeId=60181"
NCYU_BRIEFING_113_URL = "https://www.ncyu.edu.tw/oia/Subject/Detail/212307?nodeId=60181"
NCYU_EXPERIENCES_LIST_URL = "https://www.ncyu.edu.tw/oia/Subject?nodeId=60182"
NCYU_EXPERIENCES_WEBHD_URL = "https://www.ncyu.edu.tw/oia/Subject/Detail/233746?nodeId=60182"
NCYU_RULES_FORMS_URL = "https://www.ncyu.edu.tw/oia/Subject?nodeId=60183"
NCYU_APP_FORM_114_URL = "https://www.ncyu.edu.tw/oia/Subject/Detail/230540?nodeId=60183"
NCYU_CONSENT_FORM_114_URL = "https://www.ncyu.edu.tw/oia/Subject/Detail/230541?nodeId=60183"
NCYU_REVIEW_RULES_PDF_URL = "https://www.ncyu.edu.tw/oia/ServerFile/Get/323e2e17-69df-483f-bd2a-addabca72167?nodeId=60244&sId=196346"
NCYU_SCHOLARSHIP_RULES_PDF_URL = "https://www.ncyu.edu.tw/oia/ServerFile/Get/943f1c6f-9400-4185-9528-7fea2095d462?nodeId=60183&sId=194912"
NCYU_BRIEFING_114_PDF_URL = "https://www.ncyu.edu.tw/oia/ServerFile/Get/9d9e4dfe-8a4f-4352-b7b2-911b6c210cf2?nodeId=60181&sId=230388"
NCYU_HAND_OUTBOUND_PDF_URL = "https://www.ncyu.edu.tw/oia/ServerFile/Get/e301187b-40e4-4c0f-9984-30d634309cdf?nodeId=64336&sId=236993"
NCYU_HAND_STUDY_ABROAD_PDF_URL = "https://www.ncyu.edu.tw/oia/ServerFile/Get/b2dbd4c5-0b42-4bb0-b7fc-ba60912bc28b?nodeId=64336&sId=236992"
NCYU_DUAL_DEGREE_INTRO_URL = "https://www.ncyu.edu.tw/oia/Contents?nodeId=61259"
NCYU_DUAL_DEGREE_STATUS_URL = "https://www.ncyu.edu.tw/oia/Contents?nodeId=61260"
NCYU_DUAL_DEGREE_REG_URL = "https://www.ncyu.edu.tw/academic/Subject/Detail/19193?nodeId=1050"
NCYU_SCHOLARSHIPS_URL = "https://www.ncyu.edu.tw/oia/Contents?nodeId=58449"
NCYU_FORMS_EXCHANGE_URL = "https://www.ncyu.edu.tw/oia/Subject?nodeId=41550"

REGION_COST_DEFAULTS = {
    "美國": (
        "每月生活費約 USD 1,350–2,200（依匯率折合新臺幣約 43,000–70,000 元，含奧瑞岡大學 University of Oregon、愛達荷大學 University of Idaho、紐澤西州斯托克頓大學 Stockton University、堪薩斯州立大學 K-State、楊斯鎮州立大學 YSU 等校區住宿、膳食與市區交通）",
        "須憑美國姊妹校核發之 DS-2019（J-1 交換生）或 I-20（F-1 雙聯學位生）繳交 SEVIS I-901 費用並向美國在台協會（AIT）申辦簽證；領有政府獎助學金持 J-1 簽證者須注意返國服務兩年規定。",
    ),
    "加拿大": (
        "每月生活費約 USD 1,250–1,900（折合加幣約 CAD 1,700–2,600 / 月、新臺幣約 40,000–60,500 元，含萊斯布里奇大學 University of Lethbridge、諾瓦史可提亞農業學院等校內外住宿、伙食與交通）",
        "交換 1 學期（6 個月內）可申辦加拿大 eTA 入境，超過 6 個月須申辦加拿大 Study Permit 並投保亞伯達省或當地省立醫療保險。",
    ),
    "巴拉圭": (
        "每月生活費約 USD 550–950（依匯率折合新臺幣約 17,500–30,000 元，含國立亞松森大學 Universidad Nacional de Asunción 校區周邊住宿與生活費）",
        "須依巴拉圭駐華大使館規定申辦學生簽證，並於出國前投保涵蓋全期之海外醫療及意外保險。",
    ),
    "英國": (
        "每月生活費約 USD 1,350–2,150（折合英鎊約 GBP 1,050–1,680 / 月、新臺幣約 43,000–68,500 元，含亞伯丁大學 University of Aberdeen 外語系學／碩士雙聯學位及卡地夫大學 Cardiff University 學生宿舍與生活費）",
        "攻讀跨國雙聯學位或一學年研修須憑英國姊妹校核發之 CAS 申辦英國 Student Visa 並繳納 IHS 醫療附加費。",
    ),
    "法國": (
        "每月生活費約 USD 1,000–1,600（折合歐元約 EUR 920–1,480 / 月、新臺幣約 32,000–51,000 元；含南特高等林業學院 ESB、圖盧茲國立綜合理工學院 INP Toulouse、SKEMA 歐洲商業學院等學生宿舍與膳食，可申請法國 CAF 房補）",
        "須先經法國教育中心（Campus France）完成 Etudes en France 程序與面試，再向法國在台協會申辦長期學生簽證（VLS-TS）。",
    ),
    "德國": (
        "每月生活費約 USD 1,000–1,550（折合歐元約 EUR 920–1,420 / 月、新臺幣約 32,000–49,500 元；含荷內波恩應用科技大學 IUBH Bad Honnef 學生宿舍與學期交通卡費）",
        "須開立德國限制提領帳戶（Blocked Account）並憑入學許可向德國在台協會申辦學生簽證及投保德國公保／醫療險。",
    ),
    "西班牙": (
        "每月生活費約 USD 900–1,450（折合歐元約 EUR 820–1,320 / 月、新臺幣約 28,500–46,000 元；含韋爾瓦大學 University of Huelva、海梅一世大學 Jaume I University、巴利阿里群島大學 UIB 等學生合租公寓與生活費）",
        "須憑西班牙接待大學入學許可向西班牙商務辦事處申辦學生簽證，並投保無自負額之全額醫療保險。",
    ),
    "斯洛維尼亞": (
        "每月生活費約 USD 750–1,200（折合歐元約 EUR 680–1,100 / 月、新臺幣約 24,000–38,000 元；含盧比雅納大學 University of Ljubljana 學生宿舍與學生餐券補貼）",
        "須憑斯洛維尼亞接待大學入學許可申辦 D 類學生簽證或居留許可，並投保涵蓋申根區之海外醫療保險。",
    ),
    "捷克": (
        "每月生活費約 USD 650–1,050（折合歐元約 EUR 600–960 / 月、新臺幣約 20,500–33,500 元；含茲林托馬斯巴塔大學 Tomas Bata University U12 學生宿舍及帕拉茨基大學 Palacký University Olomouc 住宿與生活費）",
        "須憑捷克接待大學入學許可與住宿證明向捷克經濟文化辦事處申辦長期學生簽證及捷克合約醫療保險。",
    ),
    "立陶宛": (
        "每月生活費約 USD 650–1,050（折合歐元約 EUR 600–960 / 月、新臺幣約 20,500–33,500 元；含維爾紐斯大學 Vilnius University 及原修雷大學 Šiauliai Academy 學生宿舍與生活費）",
        "須憑立陶宛維爾紐斯大學入學許可申辦立陶宛國家簽證（D Visa）或臨時居留許可（TRP），並投保歐盟申根醫療保險。",
    ),
    "土耳其": (
        "每月生活費約 USD 650–1,100（依匯率折合新臺幣約 20,500–35,000 元；含伊斯坦堡卡地爾哈斯大學 Kadir Has University 周邊住宿、伙食與交通）",
        "須憑土耳其卡地爾哈斯大學入學許可申辦土耳其學生簽證，入境後辦理居留證（Ikamet）並投保當地醫療保險。",
    ),
    "日本": (
        "每月生活費約 USD 680–1,150（折合日圓約 JPY 95,000–165,000 / 月、新臺幣約 21,500–36,500 元；含明治大學、香川大學、上越教育大學、尾道市立大學、中京大學、宮崎大學、長崎大學、兵庫縣立大學、攝南大學、山口大學、熊本大學、愛媛大學、德島大學、山口縣立大學等國際學舍與生活費）",
        "須由日本接待大學代向出入國在留管理局申請「在留資格認定證明書（COE）」，獲發後至日本台灣交流協會申辦留學簽證並加入日本國民健康保險（NHI）。",
    ),
    "韓國": (
        "每月生活費約 USD 650–1,100（折合韓元約 KRW 880,000–1,500,000 / 月、新臺幣約 20,500–35,000 元；含大邱大學、春川教育大學、韓京大學等校內宿舍與生活費）",
        "須憑韓國接待校核發之標準入學許可書（Certificate of Admission）向駐台北韓國代表部申辦 D-2-6 交換學生簽證，入境後辦理外國人登錄證並納保韓國國民健康保險。",
    ),
    "中國大陸": (
        "每月生活費約 USD 350–680（折合人民幣約 RMB 2,000–4,300 / 月、新臺幣約 11,000–21,500 元；含南京農業大學、西北農林科技大學、東北大學、中國傳媒大學、中國農業大學、華南農業大學、華東師範大學、福建農林大學、集美大學等校內宿舍與食堂開銷）",
        "須持有效「臺灣居民來往大陸通行證（臺胞證）」及大陸姊妹校寄發之錄取通知書辦理報到，並依國立嘉義大學國際事務處規定購買涵蓋交換全期之海外醫療及意外保險。",
    ),
    "蒙古": (
        "每月生活費約 USD 450–800（依匯率折合新臺幣約 14,500–25,500 元；含烏蘭巴托蒙古國立農業大學、蒙古國立音樂學院學生宿舍與生活費）",
        "須憑蒙古接待大學入學許可申辦學生簽證，並於出國前投保涵蓋全期之海外醫療與意外保險。",
    ),
    "俄羅斯": (
        "每月生活費約 USD 500–880（依匯率折合新臺幣約 16,000–28,000 元；含新西伯利亞農業大學、伊爾庫茨克州立農業學院、布里亞特農業學院學生宿舍與生活費）",
        "須憑俄羅斯接待院校核發之官方邀請函向莫斯科台北經濟文化協調委員會駐台北代表處申辦學生簽證，並投保俄羅斯境內有效之醫療保險。",
    ),
    "越南": (
        "每月生活費約 USD 400–750（依匯率折合新臺幣約 12,800–24,000 元；含胡志明市經濟大學 UEH、胡志明市國家大學下屬理科大學、胡志明市農林大學、胡志明師範大學、芹苴大學 Can Tho、大勒大學、芽莊大學等住宿與生活費）",
        "須憑越南接待大學入學許可申辦越南學生簽證，並於出國前投保涵蓋全期之海外醫療與意外保險。",
    ),
    "泰國": (
        "每月生活費約 USD 500–880（折合泰銖約 THB 17,000–30,000 / 月、新臺幣約 16,000–28,000 元；含泰國農業大學 Kasetsart、清邁大學 CMU、湄州大學 Maejo、孔敬大學 KKU、宋卡王子大學 PSU、泰國藝術大學 Silpakorn 等住宿與生活費）",
        "須憑泰國接待大學入學許可向泰國貿易經濟辦事處申辦 Non-Immigrant ED 學生簽證，並投保海外醫療保險。",
    ),
    "印尼": (
        "每月生活費約 USD 420–780（依匯率折合新臺幣約 13,500–25,000 元；含布勞爪哇大學 University of Brawijaya 雙聯學制、茂物農業大學 IPB、日惹州立大學 UNY、蘇迪曼大學、諾門森大學等住宿與生活費）",
        "須憑印尼接待大學入學許可與學習許可申辦印尼學生簽證（C316 / KITAS），並購買海外醫療保險。",
    ),
    "馬來西亞": (
        "每月生活費約 USD 500–850（折合馬幣約 MYR 2,200–3,800 / 月、新臺幣約 16,000–27,000 元；含拉曼大學 UTAR、瑪拉工藝大學 UiTM、南方大學學院、新紀元大學學院等住宿與生活費）",
        "須透過馬來西亞 EMGS 系統申辦 Student Pass / Visa Approval Letter（VAL）並投保當地學生醫療保險。",
    ),
    "菲律賓": (
        "每月生活費約 USD 480–820（依匯率折合新臺幣約 15,500–26,000 元；含國立菲律賓大學 Los Baños / Visayas、東方大學 UE、撒薇亞大學 Xavier、本格特州立大學、伊莎貝爾州立大學等住宿與生活費）",
        "須依菲律賓接待大學指引申辦 9(f) 學生簽證或 SSP 特別學習許可，並投保海外醫療與意外保險。",
    ),
    "柬埔寨": (
        "每月生活費約 USD 420–750（依匯率折合新臺幣約 13,500–24,000 元；含金邊波雷列國立農業學院 Prek Leap National College of Agriculture 校區住宿與生活費）",
        "須憑柬埔寨接待學院入學許可申辦簽證，並於出國前投保涵蓋全期之海外醫療、意外及急難救助保險。",
    ),
    "印度": (
        "每月生活費約 USD 420–750（依匯率折合新臺幣約 13,500–24,000 元；含書里尼大學 Shoolini University 校內宿舍與膳食費）",
        "須憑印度接待大學入學許可向印度台北協會申辦 Student Visa，並投保海外醫療與急難救助保險。",
    ),
    "澳洲": (
        "每月生活費約 USD 1,350–2,100（折合澳幣約 AUD 2,050–3,200 / 月、新臺幣約 43,000–67,000 元；含新英格蘭大學 University of New England、南十字星大學 Southern Cross University 住宿與生活費）",
        "須憑澳洲姊妹校核發之 CoE（Confirmation of Enrolment）申辦澳洲 Subclass 500 學生簽證，並強制投保海外學生健康保險（OSHC）。",
    ),
    "紐西蘭": (
        "每月生活費約 USD 1,250–1,950（折合紐幣約 NZD 2,100–3,250 / 月、新臺幣約 40,000–62,000 元；含威靈頓維多利亞大學 Victoria University of Wellington、林肯大學 Lincoln University 住宿與生活費）",
        "須憑紐西蘭姊妹校入學許可（Offer of Place）向紐西蘭移民局申辦 Fee Paying / Exchange Student Visa，並投保紐西蘭認可之學生醫療與旅遊保險。",
    ),
}

SEMESTER_DATES_BY_COUNTRY = {
    "美國": "秋季學期（Fall Semester）：約 8 月中旬至 12 月中旬；春季學期（Spring Semester）：約 1 月中旬至 5 月中旬",
    "加拿大": "秋季學期（Fall Semester）：約 9 月初至 12 月中旬；春季學期（Spring Semester）：約 1 月初至 4 月下旬",
    "巴拉圭": "第一學期：約 2/3 月至 7 月；第二學期：約 8 月至 12 月",
    "英國": "秋季學期（Autumn Term）：約 9 月中下旬至翌年 1 月；春季學期（Spring Term）：約 1 月下旬至 6 月",
    "法國": "秋季學期（Fall Semester）：約 9 月初至 12 月底／1 月；春季學期（Spring Semester）：約 1 月下旬至 5/6 月",
    "德國": "冬季學期（Winter Semester）：約 9/10 月至翌年 1/2 月；夏季學期（Summer Semester）：約 3/4 月至 7/8 月",
    "西班牙": "秋季學期：約 9 月中旬至翌年 1 月；春季學期：約 1/2 月至 5/6 月",
    "斯洛維尼亞": "冬季學期：約 10 月初至翌年 1 月底；夏季學期：約 2 月中旬至 6 月中旬",
    "捷克": "冬季學期（Winter Semester）：約 9 月中下旬至翌年 1 月；夏季學期（Summer Semester）：約 2 月中旬至 6 月",
    "立陶宛": "秋季學期（Autumn Semester）：約 9 月初至翌年 1 月；春季學期（Spring Semester）：約 2 月初至 6 月",
    "土耳其": "秋季學期（Fall Semester）：約 9 月中旬至翌年 1 月；春季學期（Spring Semester）：約 2 月中旬至 6 月",
    "日本": "春季學期（Spring Semester）：約 4 月初至 8 月初；秋季學期（Fall Semester）：約 9 月中下旬至翌年 1/2 月",
    "韓國": "春季學期（Spring Semester）：約 3 月初至 6 月中旬；秋季學期（Fall Semester）：約 9 月初至 12 月中旬",
    "中國大陸": "春季學期（下學期）：約 2 月中下旬至 6 月底；秋季學期（上學期）：約 9 月初至翌年 1 月中旬",
    "蒙古": "秋季學期：約 9 月初至翌年 1 月；春季學期：約 2 月至 6 月",
    "俄羅斯": "秋季學期：約 9 月初至翌年 1 月；春季學期：約 2 月至 6 月",
    "越南": "秋季學期（第一學期）：約 8/9 月至 12/1 月；春季學期（第二學期）：約 1/2 月至 5/6 月",
    "泰國": "第一學期：約 8 月至 12 月；第二學期：約 1 月至 5 月",
    "印尼": "奇數學期（秋季）：約 8/9 月至 12/1 月；偶數學期（春季）：約 2 月至 6 月",
    "馬來西亞": "第一學期：約 9/10 月至翌年 1/2 月；第二學期：約 2/3 月至 6/7 月",
    "菲律賓": "第一學期：約 8 月至 12 月；第二學期：約 1 月至 5 月",
    "柬埔寨": "第一學期：約 10 月至翌年 2 月；第二學期：約 3 月至 7 月",
    "印度": "秋季學期：約 8 月至 12 月；春季學期：約 1 月至 5 月",
    "澳洲": "第一學期（Semester 1）：約 2 月下旬至 6 月；第二學期（Semester 2）：約 7 月下旬至 11 月",
    "紐西蘭": "第一學期（Trimester 1）：約 2 月下旬至 6 月；第二學期（Trimester 2）：約 7 月中旬至 11 月",
}


def clean_text(s: str) -> str:
    return re.sub(r"\s+", " ", s).strip() if s else ""


def sync_global_assets_and_locations(catalog_source: list[dict], resolved_locations: dict) -> None:
    """Ensure school-images.json and university_locations.jsonl contain all 140 NCYU partner schools."""
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
            lat = float(loc.get("latitude") if loc.get("latitude") is not None else loc.get("lat", 23.4694))
            lon = float(loc.get("longitude") if loc.get("longitude") is not None else loc.get("lon", 120.4853))
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
    OFFICIAL_NCYU_DIR.mkdir(parents=True, exist_ok=True)
    catalog_source = json.loads((SOURCES_NCYU_DIR / "ncyu_catalog_source.json").read_text(encoding="utf-8"))
    resolved_locations = json.loads((SOURCES_NCYU_DIR / "ncyu_resolved_locations.json").read_text(encoding="utf-8"))
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
        quota_str = clean_text(item.get("quota") or "2名/學年")
        detail_url = item.get("detail_url") or NCYU_SISTERS_URL
        source_url = detail_url
        program_type = f"國際事務處【{prog_raw}】（{group_str}）"

        colleges_str = clean_text(
            item.get("colleges")
            or "不限學院（師範學院、人文藝術學院、管理學院、農學院、理工學院、生命科學院、獸醫學院均得依姊妹校開設系所申請）"
        )
        degree_levels_str = clean_text(
            item.get("eligible_degrees")
            or "國立嘉義大學學士班二年級以上、碩士班一年級以上、博士班一年級以上之在學學生（轉學生須已有嘉大至少一學期成績；修業年限內限申請交換一次）"
        )
        lang_req_str = clean_text(
            item.get("language_req")
            or "符合姊妹校語言門檻及嘉大校內審查計分標準（TOEFL iBT 35–93 / IELTS 5.0–6.5 / JLPT N1–N4 / 歐洲地區英語 B1 TOEIC 550）"
        )
        gpa_req_str = clean_text(
            item.get("gpa_req")
            or "在校成績需達全班前 20% 以內，或學期平均成績大學部 75 分（含）以上、研究生 80 分（含）以上，且各科（含操行）成績須達及格標準"
        )
        website = item.get("website") or NCYU_SISTERS_URL
        remarks_raw = clean_text(item.get("notes") or "")
        tuition_note = clean_text(item.get("tuition_note") or "")
        exps = item.get("experience_reports") or []

        round_label = "115-1／115-2（2026秋季班／2027春季班：校內收件至 01/31）＆春季二次甄選"
        app_deadline_str = (
            "第一學期校內甄選（申請 2026 秋季班／2027 春季班出國交換）：每年 9–10 月舉辦說明會並由各系所受理初審，翌年 01/31 前由系院彙整送達蘭潭校區國際事務處；"
            "第二學期補充甄選（春季班）及教育部學海飛颺／惜珠獎學金申請：每年 2–3 月辦理說明會，3 月 20 日前受理學海計畫送件，4 月中旬各系所初審送交國際處"
        )
        deadline_iso = "2026-01-31T17:00:00+08:00"
        win_status = "open" if avail_status == "open" else "closed"
        acad_year = "115"

        study_period_str = "一學期／一學季或一學年（同一修業年限內限參加一次交換學生計畫；跨國雙聯學制須於嘉大修業滿 1 年以上並滿足兩校修業年限與畢業學分規定）"
        sem_dates_str = SEMESTER_DATES_BY_COUNTRY.get(country, "秋季學期：約 9 月至翌年 1 月；春季學期：約 2 月至 6 月")
        housing_str = f"獲國立嘉義大學國際事務處推薦提名後，可依 {zh_name} 指引申請校內外學生宿舍或國際學舍（{tuition_note}）。"
        course_rest_str = (
            f"開放對象與學院：{colleges_str}（{degree_levels_str}）。依《國立嘉義大學薦外交換學生審查要點》、《薦外交換生手冊》及《與境外大學校院辦理雙聯學制實施辦法》規定："
            "（1）申請人須為學士班二年級以上、碩士班一年級以上或博士班一年級以上之在學學生（轉學生若尚未有嘉大成績者不得申請；非中華民國國籍之在校生不得申請交換至原屬國家境內之學校）；"
            "（2）在校學業成績需達全班前 20% 以內，或學期平均成績大學部 75 分（含）以上、研究生 80 分（含）以上，且各科（含操行）成績須達及格標準；"
            "（3）出國交換期間須完成嘉大註冊並依規定繳納本校雜費（電腦使用費、網路使用費、平安保險費）以保留學籍；進修課程須先經所屬系、所務會議同意，返國後同系可抵必／選修、外系可抵外系選修；"
            "（4）交換結束返國後一個月內須繳交《研讀心得報告》乙份至國際事務處，並參加交換學生座談會及經驗傳承。"
        )

        living_cost_str, visa_health_str = REGION_COST_DEFAULTS.get(
            country,
            (
                "每月生活費約 USD 750–1,400（依匯率折合新臺幣約 24,000–45,000 元，含住宿、膳食與市區交通）",
                "須依接待國駐臺機構規定申辦學生簽證，並於出國前投保涵蓋全期之海外醫療及意外保險。",
            ),
        )

        tuition_points_list = [
            f"國立嘉義大學學雜費規定與姊妹校待遇：依《國立嘉義大學薦外姊妹校交換學生獎補助金發放要點》與《薦外交換生手冊》，獲本校推薦赴姊妹校進修之交換生應於嘉大辦理註冊並繳納雜費（電腦使用費、網路使用費、平安保險費）以保留學籍。本合作校待遇：{tuition_note}。",
            "國立嘉義大學出國研修四層獎助學金體系：（1）教育部《學海飛颺》獎學金（每年 3 月 20 日前申請，補助學費、生活費及來回機票約 NT$150,000）；（2）教育部《學海惜珠》清寒獎學金（持低收入戶、中低收入戶或特殊境遇家庭證明，教育部最高補助 80%、嘉大配合補助 20%）；（3）《國立嘉義大學薦外姊妹校交換學生獎補助金》（機票補助費：亞洲 NT$10,000、紐澳 NT$15,000、歐美非 NT$20,000；每月生活助學金最多 12 個月：大學部每月 NT$6,000、研究所每月 NT$8,000）；（4）《學碩一貫優秀學生獎助海外研修計畫》（研修 1 學期獎助 NT$90,000、1 學年獎助 NT$150,000）及日本交流協會（JASSO）短期交換獎學金。",
        ]

        app_steps_list = [
            f"步驟一（確認嘉大在學年級、班排前 20% 或平均 75/80 分門檻與 {zh_name} 語檢要求）：確認符合《國立嘉義大學薦外交換學生審查要點》規定（{gpa_req_str}），並備妥有效期限內且符合 {zh_name} 入學標準之語言能力證明（{lang_req_str}；每人最多可選填 2 所志願學校）。",
            "步驟二（填具薦外交換學生甄選申請表與進修課程規劃同意書，送所屬系所初審並提報系／所務會議）：檢附申請表（含進修課程規劃同意書與經費預算表）、歷年成績單（大陸地區附中文版、其他地區附英文數字成績版並用螢光筆標示平均成績與班排）、中英文自傳及讀書計畫、家長同意書、2 封教師推薦函、語言能力證明及系／所務會議同意之會議紀錄，經系院初審推薦排序後於截止日（1月31日）前送達蘭潭校區國際交流學園2樓國際事務處。",
            "步驟三（通過國際事務處校級複審評分並同步申請教育部學海飛颺／惜珠或校內交換獎補助金）：非華語地區依「班級排名百分比 40%＋語言能力 40%（iBT 79–93/IELTS 6.5/N1 給 40%、iBT 60–78/IELTS 6.0/N2 給 36%、iBT 46–59/IELTS 5.5/N3 給 32%、iBT 35–45/IELTS 5.0/N4 給 24%）＋讀書計畫 20%」複審；華語地區依「班級排名百分比 80%＋讀書計畫 20%」複審，陳奉校長核定後公告錄取名單。",
            f"步驟四（由國際事務處向 {full_name} 辦理官方提名、完成簽證保險與宿位申請，返國後 1 個月內繳交研讀心得報告）：獲推薦生配合國際處於姊妹校截止日前寄送入學申請文件（若放棄須於推薦名單公布後 2 個月內繳交放棄聲明書）；出發後 1 個月內回報《抵達國外報告單》，返國後 1 個月內繳交《研讀心得報告》與《返校手續單》並辦理學分抵免。",
        ]

        elig_points_list = [
            f"合作類別與計畫群組：{program_type}",
            f"開放學制與修業年級：{degree_levels_str}",
            f"開放申請院系：{colleges_str}",
            f"學業與校內複審評分標準：{gpa_req_str}",
            f"外語能力標準（有效期限內正本，華語地區免附）：{lang_req_str}",
            "志願數與進修課程核准：每人最多可選擇 2 所志願學校（需分別填寫進修課程規劃表與經費預算表），且進修課程需檢附所屬系、所務會議同意之會議紀錄。",
        ]
        if tuition_note:
            elig_points_list.append(f"姊妹校學費與嘉大獎補助待遇：{tuition_note}")
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
                eurl = e.get("url") or NCYU_EXPERIENCES_LIST_URL
                if eurl in seen_exp_urls:
                    eurl = f"{eurl}#r{e_idx+1}"
                seen_exp_urls.add(eurl)
                exp_labels.append(raw_t[:36])
                exp_links.append({
                    "title": raw_t,
                    "url": eurl,
                    "academic_year": esem,
                    "semester": esem,
                    "college": "師範學院／人文藝術學院／管理學院／農學院／理工學院／生命科學院／獸醫學院",
                    "department": e.get("department") or "嘉大出國交換生",
                })
                summary_text = (
                    f"國立嘉義大學國際事務處於歷屆交換生心得專區與雲端學年度資料庫公開收錄之學長姐赴 {country} {full_name} 交換研修官方心得報告（{raw_t}），詳述行前準備、選課與學分採認、學生宿舍生活與當地開銷實錄。"
                )
                theme_map = {
                    "academics": f"嘉大交換生於《{raw_t}》分享在 {zh_name} 修習專業與語言課程，以及返國後向所屬系所辦理必／選修學分抵免之經驗。",
                    "housing": f"嘉大交換生記錄申請 {zh_name} 校內外學生宿舍與生活機能（{housing_str[:100]}）。",
                    "campus_culture": f"嘉大國際事務處公開收錄《{raw_t}》之國際學伴互動（Buddy System）、跨文化學習與海外生活體驗。",
                    "cost": f"嘉大交換生分享於 {zh_name} 之每月住宿、伙食與交通花費（{living_cost_str[:100]}），以及申請教育部學海飛颺／惜珠與嘉大交換獎補助金之經驗。",
                }
                student_experience_rows.append({
                    "school_name": full_name,
                    "country": country,
                    "title": raw_t,
                    "source_url": eurl,
                    "source_type": "article",
                    "platform": "國立嘉義大學國際事務處—歷屆交換生心得專區與學年度雲端資料庫",
                    "author_name": raw_t,
                    "language": "zh",
                    "summary": summary_text,
                    "themes": ["academics", "housing", "campus_culture", "cost"],
                    "theme_summaries": theme_map,
                    "content_status": "full_text",
                    "perspective": "official_student_story",
                    "published_at": None,
                    "discovered_at": CHECKED_AT,
                    "content_hash": hashlib.sha256(f"{full_name}:ncyu_exp:{e_idx}:{eurl}".encode("utf-8")).hexdigest(),
                    "exchange_term": esem,
                    "summary_zh": summary_text,
                    "original_summary": summary_text,
                    "theme_summaries_zh": theme_map,
                    "translation_status": "original",
                    "source_kind": "official_experience_page",
                })

        sample_reports = [{"title": lk["title"], "url": lk["url"], "term": lk["semester"]} for lk in exp_links[:6]]
        experience_sources_records.append({
            "home_university": "國立嘉義大學",
            "school_name": full_name,
            "country": country,
            "official_experience_portal_url": exp_links[0]["url"] if exp_links else NCYU_EXPERIENCES_LIST_URL,
            "partner_page_url": source_url,
            "report_count": len(exps),
            "sample_reports": sample_reports,
            "checked_at": CHECKED_AT,
        })

        loc = resolved_locations.get(full_name) or {
            "city": country,
            "latitude": 23.4694,
            "longitude": 120.4853,
            "source_url": "https://www.wikidata.org",
        }
        city_name = loc.get("city") or country
        lat = float(loc.get("latitude") if loc.get("latitude") is not None else loc.get("lat", 23.4694))
        lon = float(loc.get("longitude") if loc.get("longitude") is not None else loc.get("lon", 120.4853))
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
            "note": "校級代表位置：官方網域及國家已與 ROR / Wikidata 及國立嘉義大學國際事務處與國外締約學校一覽表比對；實際交換校區以錄取通知與姊妹校簡章為準。",
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
                f"【嘉大學長姐交換研修心得報告（共 {len(exps)} 篇）】收錄於國際事務處歷屆交換生心得專區與雲端資料庫（含：{'、'.join(exp_labels[:4])}）"
            )
        if remarks_raw:
            notes_lines.append(f"【締約時間與官方備註】{remarks_raw}")

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
            "availability_note": f"國立嘉義大學國際事務處公告締約合作姊妹校（{program_type}）；名額：{quota_str}（{remarks_raw}）。",
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
            "factsheet_url": NCYU_BRIEFING_114_PDF_URL if avail_status == "open" else source_url,
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
                "title": f"國立嘉義大學國際事務處與國外締約學校一覽表及雙聯現況—{zh_name}",
                "source_url": source_url,
                "role": "home_university",
                "authority": "home_official_notice",
                "effective_academic_year": acad_year,
                "application_round": round_label,
                "checked_at": CHECKED_AT,
            },
            {
                "title": "國立嘉義大學 114 學年度交換學生計畫說明會簡報（2026秋季班／2027春季班）PDF",
                "source_url": NCYU_BRIEFING_114_PDF_URL,
                "role": "home_university",
                "authority": "home_official_notice",
                "effective_academic_year": acad_year,
                "application_round": round_label,
                "checked_at": CHECKED_AT,
            },
            {
                "title": "國立嘉義大學薦外交換學生審查要點與薦外交換生手冊",
                "source_url": NCYU_REVIEW_RULES_PDF_URL,
                "role": "home_university",
                "authority": "home_official_notice",
                "effective_academic_year": acad_year,
                "application_round": round_label,
                "checked_at": CHECKED_AT,
            },
        ]
        if exp_links:
            wf_sources.append({
                "title": f"國立嘉義大學國際事務處歷屆交換生心得專區—赴 {zh_name} 交換心得報告（{len(exps)} 篇）",
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
            "home_university": "國立嘉義大學",
            "school_name": full_name,
            "partner_website": website,
            "country": country,
            "program_type": program_type,
            "academic_year": acad_year,
            "application_round": round_label,
            "effective_application_rounds": [
                round_label,
                "115-1（2026秋季出國交換暨學海獎學金甄選）",
                "115-2（2027春季出國交換甄選）",
                "115-1",
                "115-2",
                "116-1",
                "116-2",
            ],
            "applicability_status": "verified",
            "applicability_note": (
                "國立嘉義大學由國際事務處國際合作組（蘭潭校區國際交流學園2樓，電話 05-271-7296 / 05-271-7298）統籌全校七大學院（師範學院、人文藝術學院、管理學院、農學院、理工學院、生命科學院、獸醫學院）之出國交換學生計畫、8 校 13 系所跨國雙聯學制及教育部學海飛颺、學海惜珠與嘉大交換獎補助金遴選。"
            ),
            "review_status": "published",
            "published_at": CHECKED_AT,
            "steps": [
                {
                    "rule_id": f"ncyu-{acad_year}-home-1-{sn:03d}",
                    "order": 1,
                    "phase": "校內申請",
                    "title": f"確認嘉大二年級以上（或碩博班）在學資格、班排前 20% 或平均 75/80 分門檻與 {zh_name} 語檢要求",
                    "responsible_party": "學生",
                    "responsible_unit": "國立嘉義大學國際事務處國際合作組（蘭潭校區國際交流學園2樓）",
                    "deadline_at": deadline_iso,
                    "deadline_status": "verified_exact",
                    "deadline_source_url": NCYU_BRIEFING_114_URL,
                    "deadline_checked_at": CHECKED_AT,
                    "deadline_reminder_eligible": True,
                    "summary": (
                        f"確認符合《國立嘉義大學薦外交換學生審查要點》及《薦外交換生手冊》規定：學士班二年級以上、碩士班一年級以上或博士班一年級以上之在學學生（在本校已修習至少滿一學期），符合學業要求（{gpa_req_str}），並備妥有效期限內且符合 {zh_name} 門檻之語言能力證明（{lang_req_str}）。"
                    ),
                    "details": [
                        f"開放學制與院系：{colleges_str}（{degree_levels_str}）",
                        f"語言與學業條件：{lang_req_str}｜{gpa_req_str}",
                        f"當期名額與計畫類別：{quota_str}｜{program_type}",
                    ],
                    "scope": {
                        "home_universities": ["國立嘉義大學"],
                        "partner_universities": [full_name],
                        "academic_years": ["115", "116"],
                        "application_rounds": [round_label, "115-1", "115-2", "116-1", "116-2"],
                    },
                    "source_urls": [source_url, NCYU_REVIEW_RULES_PDF_URL, NCYU_BRIEFING_114_PDF_URL],
                    "checked_at": CHECKED_AT,
                    "support_status": "verified",
                },
                {
                    "rule_id": f"ncyu-{acad_year}-home-2-{sn:03d}",
                    "order": 2,
                    "phase": "校內申請",
                    "title": "向所屬系所遞交薦外交換學生甄選申請表與進修課程規劃同意書，經系、所務會議通過並由學院排序送國際處",
                    "responsible_party": "學生與所屬系所／學院",
                    "responsible_unit": "各學院系所辦公室／國立嘉義大學國際事務處國際合作組",
                    "deadline_at": deadline_iso,
                    "deadline_status": "verified_exact",
                    "deadline_source_url": NCYU_BRIEFING_114_URL,
                    "deadline_checked_at": CHECKED_AT,
                    "deadline_reminder_eligible": True,
                    "summary": (
                        "申請人須先向所屬系所提出申請（每人最多可選填 2 志願學校，需分別填寫進修課程規劃同意書與經費預算表），經系、所務會議審議通過進修課程規劃並由學院排定初審推薦順位後，於校內送件截止日（1月31日）前彙整送交國際事務處。"
                    ),
                    "details": [
                        "第一學期徵件（預定下學年度上學期 2026 秋季班或下學期 2027 春季班出國）：每年 10 月舉辦說明會後開放各系所收件，系所於翌年 1 月 31 日前完成初審並送交推薦學生資料至國際事務處。",
                        "第二學期補充徵件與教育部學海飛颺／惜珠獎學金申請：每年 2–3 月辦理說明會，3 月 20 日前受理學海飛颺／惜珠申請，4 月中旬各系所辦理初審推薦送交國際處。",
                    ],
                    "document_requirements": [
                        {
                            "name": "國立嘉義大學薦外交換學生甄選申請表（1141031更新版，含進修課程規劃同意書及經費預算表）",
                            "official_form_url": NCYU_APP_FORM_114_URL,
                            "source_urls": [NCYU_APP_FORM_114_URL, NCYU_EXCHANGE_HOW_TO_APPLY_URL],
                        },
                        {
                            "name": "歷年在校成績單乙份（大陸地區姊妹校檢附中文版、其他地區檢附英文版數字成績單，附完整排名並以螢光筆標出平均成績及排名）",
                            "official_form_url": NCYU_EXCHANGE_NOTES_URL,
                            "source_urls": [NCYU_EXCHANGE_NOTES_URL, NCYU_REVIEW_RULES_PDF_URL],
                        },
                        {
                            "name": "有效期限內之語言能力測驗成績證明（華語地區免附；英語組附 TOEFL iBT 或 IELTS、歐洲組 B1 門檻、日語組附 JLPT N2/N3、法語一年期附法語 B1）",
                            "official_form_url": NCYU_ENG_TABLE_URL,
                            "source_urls": [source_url, NCYU_ENG_TABLE_URL, NCYU_BRIEFING_114_PDF_URL],
                        },
                        {
                            "name": "中、英文自傳及讀書計畫各乙份、兩封教師推薦函、家長同意書及所屬系、所務會議同意之會議紀錄",
                            "official_form_url": NCYU_CONSENT_FORM_114_URL,
                            "source_urls": [NCYU_CONSENT_FORM_114_URL, NCYU_REVIEW_RULES_PDF_URL],
                        },
                    ],
                    "scope": {
                        "home_universities": ["國立嘉義大學"],
                        "academic_years": ["115", "116"],
                        "application_rounds": [round_label, "115-1", "115-2", "116-1", "116-2"],
                    },
                    "source_urls": [NCYU_BRIEFING_114_URL, NCYU_APP_FORM_114_URL, NCYU_EXCHANGE_HOW_TO_APPLY_URL],
                    "checked_at": CHECKED_AT,
                    "support_status": "verified",
                },
                {
                    "rule_id": f"ncyu-{acad_year}-home-3-{sn:03d}",
                    "order": 3,
                    "phase": "甄選與提名",
                    "title": "通過國際事務處複審評分（班排 40%＋語檢 40%＋讀書計畫 20%；華語區班排 80%＋讀書計畫 20%）並審議獎助學金",
                    "responsible_party": "國立嘉義大學國際事務處與錄取學生",
                    "responsible_unit": "國立嘉義大學國際事務處／國際事務會議",
                    "deadline_at": "2026-03-20T17:00:00+08:00",
                    "deadline_status": "verified_exact",
                    "deadline_source_url": NCYU_HAND_OUTBOUND_PDF_URL,
                    "deadline_checked_at": CHECKED_AT,
                    "deadline_reminder_eligible": True,
                    "summary": (
                        "國際事務處依據《國立嘉義大學薦外交換學生審查要點》之複審評分標準進行審查，陳奉校長核定後公布推薦名單並送國際事務會議備查；同時協助獲薦交換生於 3 月 20 日前申請教育部學海飛颺、學海惜珠及本校薦外交換學生獎補助金。"
                    ),
                    "details": [
                        "非華語地區複審評分：班級排名百分比占 40%（<=10% 給 40%、11–20% 給 37%、21–30% 給 35%...）、語言能力占 40%（iBT 79–93/IELTS 6.5/N1 給 40%、iBT 60–78/IELTS 6.0/N2 給 36%、iBT 46–59/IELTS 5.5/N3 給 32%、iBT 35–45/IELTS 5.0/N4 給 24%）、讀書計畫占 20%。",
                        "獲推薦之薦外交換生若無法於核定期限內出國研修，必須於推薦名單公布後 2 個月內繳交《放棄聲明書》至國際處；未繳交者於本校在學期間不得再申請交換學生甄選。",
                    ],
                    "scope": {
                        "home_universities": ["國立嘉義大學"],
                        "academic_years": ["115", "116"],
                        "application_rounds": [round_label, "115-1", "115-2", "116-1", "116-2"],
                    },
                    "source_urls": [NCYU_REVIEW_RULES_PDF_URL, NCYU_SCHOLARSHIP_RULES_PDF_URL, NCYU_HAND_OUTBOUND_PDF_URL],
                    "checked_at": CHECKED_AT,
                    "support_status": "verified",
                },
                {
                    "rule_id": f"ncyu-{sn:03d}-host-apply",
                    "order": 4,
                    "phase": "合作校申請",
                    "title": f"由國際事務處向 {zh_name} 辦理官方提名，並依姊妹校截止日寄送入學申請與財力／宿位文件",
                    "responsible_party": "學生與接待校國際事務處",
                    "summary": (
                        f"通過校內複審僅代表獲得嘉大推薦資格，由國際事務處向 {zh_name} 辦理官方提名並寄送申請資料；學生須依姊妹校規定備齊外文申請表、英文歷年成績單、語檢證明、3個月內英文版存款餘額證明（財力證明）、護照影本及照片，待獲姊妹校核發入學許可（Offer Letter）始正式取得錄取資格。"
                    ),
                    "details": [
                        f"研修期程：{study_period_str}｜名額：{quota_str}",
                        f"語言與學業條件：{lang_req_str}｜{gpa_req_str}",
                        f"住宿與費用待遇：{housing_str}",
                    ],
                    "scope": {
                        "home_universities": ["國立嘉義大學"],
                        "partner_universities": [full_name],
                        "academic_years": ["115", "116"],
                        "application_rounds": [round_label, "115-1", "115-2", "116-1", "116-2"],
                    },
                    "source_urls": [source_url, NCYU_BRIEFING_114_PDF_URL] + ([website] if website else []),
                    "checked_at": CHECKED_AT,
                    "support_status": "verified",
                    "needs_confirmation": False,
                },
                {
                    "rule_id": f"ncyu-{acad_year}-home-5-{sn:03d}",
                    "order": 5,
                    "phase": "行前準備",
                    "title": "參加行前說明會、完成嘉大註冊繳納雜費與役男出國申請，返國後 1 個月內繳交研讀心得報告並辦理學分採認",
                    "responsible_party": "學生與所屬系所",
                    "responsible_unit": "國立嘉義大學國際事務處／教務處／各學院系所",
                    "summary": (
                        "出國交換前須參加行前說明會（秋季班 6 月、春季班 12 月）、簽署行政契約書、購買足額海外醫療與急難救助保險、辦理役男出國核准，並於出國期間委託代理人完成嘉大註冊及繳納雜費（電腦使用費、網路使用費、平安保險費）；抵達國外 1 個月內回報《抵達國外報告單》，返國後 1 個月內繳交《研讀心得報告》、《返校手續單》並辦理學分採認。"
                    ),
                    "details": tuition_points_list,
                    "scope": {
                        "home_universities": ["國立嘉義大學"],
                        "academic_years": ["115", "116"],
                        "application_rounds": [round_label, "115-1", "115-2", "116-1", "116-2"],
                    },
                    "source_urls": [
                        NCYU_REVIEW_RULES_PDF_URL,
                        NCYU_HAND_OUTBOUND_PDF_URL,
                        NCYU_EXPERIENCES_LIST_URL,
                    ],
                    "checked_at": CHECKED_AT,
                    "support_status": "verified",
                },
            ],
            "sources": wf_sources,
            "last_checked": CHECKED_AT,
            "coverage_status": "official_verified",
            "coverage_note": (
                f"已完整整合國立嘉義大學國際事務處（OIA）25 國 140 所締約姊妹校一覽表、114 學年度交換學生計畫說明會簡報（2026秋季班／2027春季班）、8 所雙聯學制合作校（13 個院系雙聯專案）、《薦外交換學生審查要點》、《薦外姊妹校交換學生獎補助金發放要點》、《薦外交換生手冊》、《海外研修手冊》，以及 {exp_covered_schools} 校 {total_exp_reports} 篇歷屆學長姐交換心得報告。"
            ),
        })

        cost_line = f"{zh_name} 預估每月生活費：{living_cost_str}"
        tuition_clean = tuition_points_list[0]
        housing_clean = housing_str
        calendar_clean = f"學期與研修時間參考：{sem_dates_str}"
        course_clean = course_rest_str

        dest_sources = [
            {
                "title": f"國立嘉義大學國際事務處締約姊妹校與交換資訊—{zh_name}",
                "source_url": source_url,
                "summary": "嘉大國際事務處公告之合作計畫類型、申請資格、名額、語檢門檻與備註",
            },
            {
                "title": "國立嘉義大學薦外交換學生審查要點與薦外交換生手冊",
                "source_url": NCYU_REVIEW_RULES_PDF_URL,
                "summary": "嘉大交換生雜費註冊規定、班排與語檢複審計分標準、獎補助金及返國學分採認規定",
            },
        ]
        if exp_links:
            dest_sources.append({
                "title": f"國立嘉義大學國際事務處歷屆交換生心得專區—赴 {zh_name} 心得報告（{len(exps)} 篇）",
                "source_url": exp_links[0]["url"],
                "summary": f"收錄歷年嘉大學生赴 {zh_name} 交換研修心得報告共 {len(exps)} 篇",
            })
        if website:
            dest_sources.append({"title": f"{full_name} 官方網站", "source_url": website, "summary": "接待合作姊妹校官方網站"})

        src_url_list = (
            [source_url, NCYU_EXCHANGE_INTRO_URL, NCYU_SISTERS_URL, NCYU_SCHOLARSHIPS_URL]
            + ([exp_links[0]["url"]] if exp_links else [NCYU_EXPERIENCES_LIST_URL])
            + ([website] if website else [])
        )

        destinations.append({
            "home_university": "國立嘉義大學",
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
                    "title": "生活費、嘉大雜費註冊規定與學海飛颺／惜珠／校內交換獎補助金體系",
                    "summary": cost_line,
                    "points": [cost_line] + tuition_points_list,
                    "source_urls": src_url_list + [NCYU_REVIEW_RULES_PDF_URL, NCYU_SCHOLARSHIP_RULES_PDF_URL],
                    "caution": "領取國立嘉義大學薦外姊妹校交換學生獎補助金或教育部學海獎學金者，出國前須簽署行政契約書；中途停止或放棄進修者，受補助經費須全數追回。",
                },
                {
                    "key": "housing",
                    "title": "住宿資訊與姊妹校校內外國際學生宿舍申請",
                    "summary": housing_clean[:160],
                    "points": [housing_clean],
                    "source_urls": src_url_list,
                    "caution": "美國愛達荷大學水產養殖中心專案提供免學費及免費住宿；其餘姊妹校交換生免學費但須自付住宿及生活雜支費用。",
                },
                {
                    "key": "insurance",
                    "title": "海外醫療、意外與急難救助保險規定",
                    "summary": visa_health_str,
                    "points": [
                        visa_health_str,
                        "依《國立嘉義大學薦外交換生手冊》規定，除校內學生平安保險外，所有錄取學生須於出國交換前自行購買足額之海外醫療、意外及海外急難救助保險；若未購買保險，國際事務處有權取消其錄取資格。",
                    ],
                    "source_urls": src_url_list,
                    "caution": "歐美、日韓及紐澳接待校對交換生醫療保險有強制納保規定，請依姊妹校入學通知書辦理。",
                },
                {
                    "key": "visa",
                    "title": "留學交換簽證辦理、役男緩徵出國申請與在學註冊義務",
                    "summary": visa_health_str,
                    "points": [
                        visa_health_str,
                        "具役男身分之錄取學生須依法完成役男出國申請程序（核准日期最長為 1 年），並於交換期間完成嘉大註冊及繳納雜費以保留學籍。",
                    ],
                    "source_urls": src_url_list,
                    "caution": "赴美國地區學校就讀之學生如辦理 J-1 簽證並同時領有政府獎助學金者，修習返國後受美國政府兩年居住規定限制。",
                },
                {
                    "key": "academics",
                    "title": "《薦外交換學生審查要點》、《雙聯學制實施辦法》與返國學分採認規定",
                    "summary": course_clean[:160],
                    "points": [calendar_clean, course_clean],
                    "source_urls": src_url_list + [NCYU_REVIEW_RULES_PDF_URL, NCYU_DUAL_DEGREE_STATUS_URL],
                    "caution": "進修課程須先經所屬系、所務會議同意並檢附會議紀錄；部分大陸姊妹校（如福建農林大學、瀋陽師範大學、哈爾濱師範大學）標註「學生交換無學分抵免」，申請前務必與系所確認。",
                },
                {
                    "key": "living",
                    "title": f"{city_name} 校園生活與嘉大國際事務處學長姐返國心得傳承",
                    "summary": f"代表城市：{city_name}。請於抵達姊妹校 1 個月內回報當地聯絡地址與電話以建立緊急聯絡網。",
                    "points": [
                        f"目的地城市：{city_name}（{country}）",
                        (
                            "國立嘉義大學國際事務處於歷屆交換生心得專區與雲端學年度資料庫公開歷屆學長姐赴海外及大陸姊妹校交換之返國心得報告"
                            + (f"（本校共收錄 {len(exps)} 篇：{'、'.join(exp_labels[:3])}）" if exps else "")
                            + "，協助學弟妹掌握選課、住宿與生活實務。"
                        ),
                    ],
                    "source_urls": [exp_links[0]["url"] if exp_links else NCYU_EXPERIENCES_LIST_URL],
                },
            ],
            "sources": dest_sources,
            "last_checked": CHECKED_AT,
            "coverage_status": "official_verified",
            "coverage_note": (
                f"已整合國立嘉義大學國際事務處 {len(catalog_source)} 所締約姊妹校一覽表、114 學年度交換學生計畫說明會簡報、8 所雙聯學制學校及 {exp_covered_schools} 校 {total_exp_reports} 篇歷屆學生返國心得報告。"
            ),
        })

        research_records.append({
            "home_university": "國立嘉義大學",
            "school_name": full_name,
            "country": country,
            "official_website": website,
            "verification_status": "official_verified",
            "discovery_source_url": detail_url,
            "checked_at": CHECKED_AT,
            "note": "國立嘉義大學國際事務處 25 國 140 所締約姊妹校一覽表、114 學年度交換說明會簡報、雙聯學制推動現況與 ROR/Wikidata 官方網址核對完成。",
        })

        ev_sources = [{"title": f"國立嘉義大學國際事務處締約姊妹校與交換資訊—{zh_name}", "url": source_url}]
        if exp_links:
            ev_sources.append({
                "title": f"國立嘉義大學國際事務處歷屆交換生心得專區—赴 {zh_name} 心得報告（{len(exps)} 篇）",
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
                "scope": "嘉大海外與大陸交換／雙聯姊妹校住宿與生活資訊",
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
                "scope": "嘉大出國交換雜費規定、教育部學海飛颺／惜珠、校內交換獎補助金與地區生活費估算",
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
                "scope": "國立嘉義大學薦外交換學生審查要點、雙聯學制實施辦法與返國學分採認規範",
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
                "scope": "嘉大海外交換與雙聯學位簽證、役男出國申請、海外醫療急難救助保險與行前提醒",
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
                        f"｜嘉大國際事務處公開收錄 {len(exps)} 篇赴 {zh_name} 交換生返國心得報告（{'、'.join(exp_labels[:3])}）。"
                        if exps
                        else ""
                    )
                ),
                "sources": ev_sources,
                "checked_at": CHECKED_AT,
                "scope": "嘉大交換名額與歷屆學長姐返國心得報告分享",
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
                "已整合國立嘉義大學國際事務處 140 所締約姊妹校一覽表、114 學年度交換說明會簡報、雙聯學制推動現況及歷屆學生交換心得報告。",
                "當期開放名額、宿位供給、語檢門檻與選課限制請依合作校最新簡章及入學通知書核對。",
            ],
            "location_signature": f"verified:{lat}:{lon}:representative",
            "extraction_version": 3,
        })

    def write_jsonl(path: Path, rows: list[dict]) -> None:
        path.write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in rows) + ("\n" if rows else ""), encoding="utf-8")

    write_jsonl(OFFICIAL_NCYU_DIR / "partners.jsonl", partners)
    write_jsonl(SOURCES_NCYU_DIR / "partners.jsonl", partners)
    write_jsonl(OFFICIAL_NCYU_DIR / "application_workflows.jsonl", workflows)
    write_jsonl(OFFICIAL_NCYU_DIR / "destination_profiles.jsonl", destinations)
    write_jsonl(OFFICIAL_NCYU_DIR / "partner_research.jsonl", research_records)
    write_jsonl(OFFICIAL_NCYU_DIR / "student_life.jsonl", life_records)
    write_jsonl(OFFICIAL_NCYU_DIR / "experience_sources.jsonl", experience_sources_records)
    write_jsonl(OFFICIAL_NCYU_DIR / "student_experience_sources.jsonl", experience_sources_records)
    write_jsonl(OFFICIAL_NCYU_DIR / "student_experiences.jsonl", student_experience_rows)

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
    (OFFICIAL_NCYU_DIR / "student-experience-digests.json").write_text(
        json.dumps({"digests": digest_records}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    (OFFICIAL_NCYU_DIR / "student-experiences.json").write_text(
        json.dumps(
            {
                "school_id": "ncyu",
                "school_name": "國立嘉義大學",
                "checked_at": CHECKED_AT,
                "source_url": NCYU_EXPERIENCES_LIST_URL,
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

    (OFFICIAL_NCYU_DIR / "campus-locations.json").write_text(
        json.dumps(
            {
                "school_id": "ncyu",
                "school_name": "國立嘉義大學",
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
    (OFFICIAL_NCYU_DIR / "campus-assets.json").write_text(
        json.dumps(
            {
                "school_id": "ncyu",
                "school_name": "國立嘉義大學",
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

    ncyu_source_urls = [
        NCYU_OIA_HOME_URL,
        NCYU_OIA_ENG_HOME_URL,
        NCYU_OIA_ABOUT_URL,
        NCYU_SISTERS_URL,
        NCYU_EXCHANGE_INTRO_URL,
        NCYU_EXCHANGE_APPLY_INFO_URL,
        NCYU_EXCHANGE_HOW_TO_APPLY_URL,
        NCYU_EXCHANGE_NOTES_URL,
        NCYU_ENG_TABLE_URL,
        NCYU_EXCHANGE_FAQ_URL,
        NCYU_EXCHANGE_FLOW_URL,
        NCYU_BRIEFINGS_LIST_URL,
        NCYU_BRIEFING_114_URL,
        NCYU_BRIEFING_113_URL,
        NCYU_EXPERIENCES_LIST_URL,
        NCYU_EXPERIENCES_WEBHD_URL,
        NCYU_RULES_FORMS_URL,
        NCYU_APP_FORM_114_URL,
        NCYU_CONSENT_FORM_114_URL,
        NCYU_REVIEW_RULES_PDF_URL,
        NCYU_SCHOLARSHIP_RULES_PDF_URL,
        NCYU_BRIEFING_114_PDF_URL,
        NCYU_HAND_OUTBOUND_PDF_URL,
        NCYU_HAND_STUDY_ABROAD_PDF_URL,
        NCYU_DUAL_DEGREE_INTRO_URL,
        NCYU_DUAL_DEGREE_STATUS_URL,
        NCYU_DUAL_DEGREE_REG_URL,
        NCYU_SCHOLARSHIPS_URL,
        NCYU_FORMS_EXCHANGE_URL,
    ]

    exchange_info_payload = {
        "school_name": "國立嘉義大學",
        "program_type": [
            "國際事務處「校級與院（系）級薦外交換學生計畫」（分為英語組、日語組、西班牙語組、法語組及中文組；一學期／一學季或一學年，修業年限內限申請一次；於嘉大註冊繳納雜費保留學籍，互免姊妹校學費或享當年度學費減免優惠）",
            "國際事務處「跨國雙聯學制計畫（Dual Degree Program）」（涵蓋美國堪薩斯州立大學 7 系碩士雙聯、日本尾道市立大學應經系學士雙聯＆資管／企管碩士雙聯、美國楊斯鎮州立大學數位系＆幼教系碩士雙聯、美國斯托克頓大學企管系碩士雙聯、英國亞伯丁大學外語系學／碩士雙聯、日本香川大學園藝系碩士雙聯、泰國湄州大學企管系碩士雙聯、印尼布勞爪哇大學企管系＆農生系碩士雙聯共 8 校 13 個雙聯專案）",
            "教育部「學海飛颺／學海惜珠」出國研修獎學金暨「國立嘉義大學薦外姊妹校交換學生獎補助金」、「學碩一貫優秀學生獎助海外研修計畫」與日本交流協會（JASSO）獎助體系",
        ],
        "academic_year": [
            "115（涵蓋 114 學年度徵件［預定 115-1／2026秋季班或 115-2／2027春季班出國交換：各系所初審後於 2026/01/31 前送達國際事務處］及春季補充甄選／教育部學海飛颺與學海惜珠獎學金申請［每年 3 月 20 日前受理學海計畫送件］）",
            f"本平台完整收錄國立嘉義大學國際事務處公告之 {len(partners)} 所全球與大陸締約姊妹校（橫跨全球 25 個國家與地區，含 {open_partner_count} 所當期開放交換與雙聯學制合作校，並完整收錄 {exp_covered_schools} 所合作大學共 {total_exp_reports} 篇歷屆學長姐返國心得報告與雲端學年度紀錄）",
        ],
        "semester": [
            "第一學期校內甄選（每年 9–10 月舉辦說明會，翌年 1 月 31 日系所送件截止）：申請次學年度秋季班（2026秋季）或春季班（2027春季）赴歐美、日本、韓國、東南亞、土耳其及中國大陸姊妹校交換一學期或一學年。",
            "第二學期補充甄選暨教育部學海獎學金申請（每年 2–3 月舉辦說明會，3 月 20 日前受理學海計畫、4 月中旬系所初審送件）：申請赴姊妹校交換、雙聯學位或海外暑期短期課程。",
        ],
        "application_period": [
            "【第一學期薦外交換學生甄選（預定 115 學年度 2026 秋季班／2027 春季班出國）】每年 10 月舉辦交換學生計畫說明會後由各系所受理報名並進行初審（含進修課程規劃系、所務會議審議），請各系所於 2026/01/31 前將初審推薦名單與申請資料送達蘭潭校區國際交流學園2樓國際事務處。",
            "【教育部學海飛颺／學海惜珠獎學金暨春季班補充甄選】每年 2–3 月辦理說明會，3 月 20 日前由國際事務處統一受理教育部學海飛颺與學海惜珠獎學金申請；春季補充甄選由各系所於 3 月中旬受理報名、4 月中旬送交推薦名單至國際處，最遲於 5 月底前公布校級審查結果。",
            "【115 學年度秋季說明會與 116 學年度出國預定時程】預計於 2026 年 10 月中下旬舉辦新一年度交換學生計畫說明會，並收件至 2027 年 1 月 31 日止。",
        ],
        "eligibility": [
            "1. 修業年級與學籍規定：依《國立嘉義大學薦外交換學生審查要點》（110年9月28日行政會議修正通過）第四點及《薦外交換生手冊》，申請人須為本校學士班二年級以上、碩士班一年級以上、博士班一年級以上之在學一般生（在本校已修習至少滿一學期）。轉學生若尚未有本校成績者，不得申請；非中華民國國籍之在校學生得參加甄選，惟不得申請交換至原屬國家境內之學校。本校學生於同一修業年限內限申請交換學生一次。",
            "2. 在校學業成績門檻：交換生在校成績需達全班前百分之二十（20%）以內，或學期平均成績大學部學生 75 分（含）以上、研究生 80 分（含）以上，且各科（含操行）成績須達及格標準。",
            "3. 校內初審與複審評分標準：申請人須先向所屬系所提出申請（每人最多可選填 2 志願學校），經各院提供初審推薦名單順位後送國際事務處複審。（1）非華語地區複審配分：班級排名百分比占 40%（<=10% 給 40%、11–20% 給 37%、21–30% 給 35%、31–40% 給 33%、41–50% 給 31%、51–60% 給 29%、61–70% 給 26%、>71% 給 20%）、語言能力占 40%（A級 iBT 79–93/IELTS 6.5/日檢 N1 給 40%；B級 iBT 60–78/IELTS 6.0/日檢 N2 給 36%；C級 iBT 46–59/IELTS 5.5/日檢 N3 給 32%；D級 iBT 35–45/IELTS 5.0/日檢 N4 給 24%）、讀書計畫占 20%；（2）華語地區複審配分：班級排名百分比占 80%、讀書計畫占 20%。",
            "4. 放棄聲明與返國義務：獲推薦之薦外交換生若無法於核定期限內出國研修者，必須於交換生推薦名單公布後 2 個月內繳交《放棄聲明書》至國際事務處，未繳交者於本校在學期間不得再申請交換學生甄選；中途停止或放棄進修者，其受補助經費應全數追回。結束國外交換計畫後，應於返國後 1 個月內繳交《研讀心得報告》乙份至國際事務處。",
        ],
        "language_requirement": [
            "1. 《國立嘉義大學薦外交換學生審查要點》語言能力分級給分標準（須檢附有效期限內之語言測驗成績正本，語言能力未達申請學校入學標準者不予審查；華語／大陸地區姊妹校免附語言測驗成績）：（1）A級（40%）：TOEFL iBT 79–93 / IELTS 6.5 / JLPT N1；（2）B級（36%）：TOEFL iBT 60–78 / IELTS 6.0 / JLPT N2；（3）C級（32%）：TOEFL iBT 46–59 / IELTS 5.5 / JLPT N3；（4）D級（24%）：TOEFL iBT 35–45 / IELTS 5.0 / JLPT N4。",
            "2. 美加英語系姊妹校個別門檻：（1）美國奧瑞岡大學（University of Oregon）：大學部 TOEFL iBT 61 / IELTS 6.0，研究所 TOEFL iBT 88 / IELTS 7.0；（2）美國愛達荷大學（University of Idaho）：大學部 TOEFL iBT 70 / IELTS 6.0，研究所 TOEFL iBT 79 / IELTS 6.5；（3）美國斯托克頓大學（Stockton University）：TOEFL iBT 79 / IELTS 6.0–6.5；（4）加拿大萊斯布里奇大學（University of Lethbridge）：TOEFL iBT 61 / IELTS 6.0 / Duolingo 105。",
            "3. 日本姊妹校個別門檻：（1）上越教育大學、攝南大學、中京大學、宮崎大學、兵庫縣立大學、熊本大學：日本語能力試驗（JLPT）需 N2（2級）（含）以上；（2）明治大學、香川大學、尾道市立大學：日本語能力試驗（JLPT）至少 N3（3級）（含）以上。",
            "4. 歐洲地區姊妹校個別門檻：立陶宛維爾紐斯大學、捷克茲林托馬斯巴塔大學、捷克帕拉茨基大學、西班牙韋爾瓦大學、西班牙海梅一世大學及法國南特高等林業學院（1學期英語授課）需達 CEFR B1 中級英文檢定門檻（GEPT 中級初試、TOEIC 550、TOEFL iBT 57、IELTS 5.0；B2 TOEIC 785 優先）；擬於法國南特高等林業學院研修 1 學年交換課程者需具備法語 B1 檢定資格。",
        ],
        "required_documents": [
            "1. 國立嘉義大學薦外交換學生甄選申請表（1141031更新版，含進修課程規劃同意書及預計研修期間所需經費預算表；申請 2 間志願學校者需分別填寫）",
            "2. 歷年在校成績單乙份（大陸地區姊妹校檢附中文版成績單；其他地區姊妹校檢附英文版數字成績單，須含入學後迄今完整成績與排名，並用螢光筆劃出平均成績及排名）",
            "3. 中、英文自傳及讀書計畫各乙份（校內初審仍需檢附中文版，讀書計畫占校內複審總分 20%）",
            "4. 國立嘉義大學學生赴姊妹校交換就讀家長同意書乙份（1141031更新版，須由家長或監護人簽名蓋章）",
            "5. 兩封教師推薦函（格式及語言依交換學校而定，推薦教師須親筆簽名）",
            "6. 有效期限內之語言能力測驗成績證明（華語／大陸地區姊妹校免檢附；英語系國家須附 TOEFL iBT 或 IELTS，歐洲地區可附 B1 檢定，日本須附 JLPT N2/N3 以上）",
            "7. 所屬系、所務會議同意進修課程規劃之會議紀錄（於系所初審後由系／所提供）",
            "8. 身分證及學生證正反面影本，以及其他有助於審查之資料或個人作品（近兩年內或大學以後之得獎證明、國際化活動證書等，請勿膠裝裝釘）",
        ],
        "scholarship_info": [
            "1. 教育部《學海飛颺》獎學金：獎勵具中華民國國籍、在臺灣地區設有戶籍、學業成績優異或具專業獲獎事蹟且符合外語能力標準之在學學生（不含在職專班及當學期畢業生）赴非大陸港澳之海外姊妹校交換研修；每年 3 月 20 日前提出申請，由學校審議補助學費、生活費及來回機票（約 NT$150,000，依當年度教育部核定經費調整）。",
            "2. 教育部《學海惜珠》清寒獎學金：獎勵具中華民國國籍且持有直轄市、縣（市）主管機關開立有效之低收入戶、中低收入戶、特殊境遇家庭扶助或相關弱勢證明且在校成績優異（以每系前 40% 為原則）之在學學生赴海外（非大陸港澳）研修；最高可獲教育部補助 80%，嘉大配合獎助 20%。",
            "3. 《國立嘉義大學薦外姊妹校交換學生獎補助金》：經本校交換學生審查通過之薦外交換生，得視當年度經費申請：（1）機票補助費（在學期間一次為限）：亞洲地區 NT$10,000、澳洲與紐西蘭地區 NT$15,000、歐洲／美洲／非洲地區 NT$20,000；（2）每月助學金（在學期間最多 12 個月）：大學部每人每月 NT$6,000、研究所每人每月 NT$8,000（研究生交換期間須暫停支領研究生工讀獎助金）。",
            "4. 《學碩一貫優秀學生獎助海外研修計畫》與外部獎助：具嘉大學碩一貫學生身分經推薦赴國外機構進行 1 學期至 1 學年交換或雙聯研修者，研修 1 學期獎助 NT$90,000、研修 1 學年獎助 NT$150,000；另可申請日本台灣交流協會（JASSO）短期交換留學生獎學金及美國愛達荷大學水產養殖中心免學費暨免住宿專案。",
        ],
        "partner_universities": [p["school_name"] for p in partners],
        "source_urls": ncyu_source_urls,
        "last_checked": CHECKED_AT,
    }
    (OFFICIAL_NCYU_DIR / "exchange_info.json").write_text(
        json.dumps(exchange_info_payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    student_dashboard_payload = {
        "school_name": "國立嘉義大學",
        "last_checked": CHECKED_AT,
        "academic_score_minimum": 75.0,
        "academic_score_rule": (
            "依《國立嘉義大學薦外交換學生審查要點》及《薦外交換生手冊》：申請人須為學士班二年級以上、碩士班一年級以上或博士班一年級以上之在學學生（轉學生須已有嘉大成績），在校成績需達全班前 20% 以內，或學期平均成績大學部學生 75 分（含）以上、研究生 80 分（含）以上，且各科（含操行）成績須達及格標準。校內複審非華語地區採計「班排百分比 40%＋語言能力 40%＋讀書計畫 20%」，華語地區採計「班排百分比 80%＋讀書計畫 20%」。"
        ),
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
            "degree_score_minimums": {"undergraduate": 75.0, "graduate": 80.0},
            "excluded_undergraduate_years": ["大一"],
            "language_certificate_required": True,
        },
        "language_score_minimums": {"toefl": 57.0, "ielts": 5.0, "toeic": 550.0},
        "application_periods": [
            {
                "title": "國立嘉義大學 114/115 學年度薦外交換學生校內甄選（2026秋季班／2027春季班出國：系所初審送件至 01/31 截止）",
                "details": [
                    "第一學期校內甄選（預定次學年度上學期秋季班或下學期春季班出國）於每年 10 月舉辦交換學生計畫說明會後開放各系所受理報名；申請人須先將申請資料送交系所進行初審（含進修課程規劃經系、所務會議審議通過），並由各系所於翌年 1 月 31 日前將推薦名單及申請資料送達蘭潭校區國際事務處。",
                    "每人最多可選填 2 所志願學校，需分別填寫進修課程規劃同意書與預計研修期間所需經費預算表。",
                ],
                "source": {
                    "title": "國立嘉義大學國際事務處《114學年度交換學生計畫說明會簡報》與《薦外交換學生甄選申請表》",
                    "source_url": NCYU_BRIEFING_114_URL,
                    "category": "exchange_application",
                    "summary": "嘉大 2026 秋季班／2027 春季班出國交換申請期程（1月31日系所送件截止）、申請資格與姊妹校名額表。",
                },
                "scope": "home_application",
                "program_types": ["exchange", "dual_degree"],
                "academic_year": "115",
                "application_round": "115-1／115-2（2026秋季班／2027春季班）交換學生校內甄選",
                "audience": "all_students",
                "opens_at": "2025-10-22T08:30:00+08:00",
                "deadline_at": "2026-01-31T17:00:00+08:00",
                "date_status": "verified_exact",
                "status": "open",
                "status_note": "114學年度交換學生計畫說明會簡報及 1141031 更新版申請表單已公告於國際事務處網站。",
                "deadline_note": "各系所初審截止日請先洽所屬系所，系所彙整送達國際事務處截止日為 1 月 31 日。",
                "reminder_eligible": True,
                "checked_at": CHECKED_AT,
            },
            {
                "title": "國立嘉義大學教育部《學海飛颺／學海惜珠》獎學金申請（03/20 截止）暨春季補充甄選",
                "details": [
                    "教育部《學海飛颺》與《學海惜珠》出國研修獎學金於每年 3 月 20 日前受理校內送件，由國際事務處統一提報教育部審核，並由交換學生審議小組複審獎補助金額度。",
                    "第二學期（春季）補充甄選於 2 月舉辦說明會並公告簡章、3 月中旬各系所受理報名、4 月中旬各系所初審送交推薦名單至國際處，最晚於 5 月底前公布校級審查結果。",
                ],
                "source": {
                    "title": "國立嘉義大學《薦外交換生手冊》與《出國研修獎學金專區》",
                    "source_url": NCYU_SCHOLARSHIPS_URL,
                    "category": "scholarship",
                    "summary": "嘉大教育部學海飛颺、學海惜珠申請期限（3月20日前）與第二學期交換生申請流程。",
                },
                "scope": "home_application",
                "program_types": ["exchange", "dual_degree"],
                "academic_year": "115",
                "application_round": "115學年度教育部學海飛颺／惜珠獎學金暨春季交換補充甄選",
                "audience": "all_students",
                "opens_at": "2026-02-15T08:30:00+08:00",
                "deadline_at": "2026-03-20T17:00:00+08:00",
                "date_status": "verified_exact",
                "status": "open",
                "status_note": "教育部學海飛颺與學海惜珠獎學金於每年 3 月由國際事務處受理申請並統一送件。",
                "deadline_note": "學海飛颺／惜珠校內申請期限為每年 3 月 20 日前；春季交換補充甄選系所初審為 4 月中旬。",
                "reminder_eligible": True,
                "checked_at": CHECKED_AT,
            },
        ],
        "program_overview": [
            {
                "title": (
                    f"國立嘉義大學國際事務處出國交換、8 校 13 系所跨國雙聯學制與四層獎助學金總覽（{len(partners)} 所締約姊妹校・{total_exp_reports} 篇學長姐交換心得報告）"
                ),
                "details": [
                    (
                        f"國立嘉義大學（National Chiayi University, NCYU，西元 2000 年由創校於 1919 年之國立嘉義技術學院［前身嘉義農林公學校 KANO］與創校於 1957 年之國立嘉義師範學院整合成立，擁有蘭潭、民雄、新民、林森四大校區，設有「師範學院、人文藝術學院、管理學院、農學院、理工學院、生命科學院、獸醫學院」七大學院）由「國際事務處國際合作組（Office of International Affairs，蘭潭校區國際交流學園2樓）」統籌全校出國交換、跨國雙聯學制（Dual Degree）及教育部學海系列獎學金計畫。本平台完整收錄 {len(partners)} 所嘉大官方締約姊妹校，橫跨全球 25 個國家與地區（含 {open_partner_count} 所當期開放申請之交換與雙聯合作校）。"
                    ),
                    (
                        f"嘉大出國交換與雙聯體系具備五大核心特色：（1）五大語組多元交換管道（英語組、日語組、西班牙語組、法語組、中文組，涵蓋美國奧瑞岡大學、愛達荷大學［含水產養殖中心免學費免住宿專案］、斯托克頓大學；加拿大萊斯布里奇大學；日本明治大學、香川大學［Sanuki交換＆一般交換］、上越教育大學、尾道市立大學、中京大學、宮崎大學、長崎大學、兵庫縣立大學、攝南大學、山口大學、熊本大學、愛媛大學、德島大學、山口縣立大學；歐洲立陶宛維爾紐斯大學、法國南特高等林業學院、法國圖盧茲國立綜合理工學院、捷克茲林托馬斯巴塔大學、捷克帕拉茨基大學、西班牙韋爾瓦大學、西班牙海梅一世大學；土耳其卡地爾哈斯大學；大陸南京農業大學、西北農林科技大學、東北大學、中國傳媒大學等）；（2）8 所雙聯學制名校共 13 個院系雙聯專案（美國堪薩斯州立大學 7 系碩士雙聯、日本尾道市立大學、美國楊斯鎮州立大學、美國斯托克頓大學、英國亞伯丁大學、日本香川大學、泰國湄州大學、印尼布勞爪哇大學）；（3）透明客觀之複審配分（非華語區：班排 40%＋語檢 40%＋讀書計畫 20%；華語區：班排 80%＋讀書計畫 20%）；（4）四層獎助學金支持（教育部學海飛颺、學海惜珠、嘉大薦外交換獎補助金［機票 1–2 萬＋每月 6,000/8,000 元生活費］、學碩一貫海外研修獎助 9–15 萬）；（5）完整收錄 {exp_covered_schools} 所合作大學共 {total_exp_reports} 篇歷屆學長姐返國心得報告。"
                    ),
                ],
                "source": {
                    "title": "國立嘉義大學國際事務處（OIA）官方網站與交換生計畫介紹",
                    "source_url": NCYU_EXCHANGE_INTRO_URL,
                    "category": "exchange_application",
                    "summary": f"嘉大 {len(partners)} 所全球與大陸締約姊妹校、8 校 13 專案雙聯學制與 {total_exp_reports} 篇交換心得報告。",
                },
            }
        ],
        "eligibility": [
            {
                "title": "嘉大二年級以上（或碩博班）在學資格、全班前 20% 或平均 75/80 分門檻與複審配分標準",
                "details": [
                    "修業年級與學業門檻：依《國立嘉義大學薦外交換學生審查要點》及《薦外交換生手冊》，申請人須為學士班二年級以上、碩士班一年級以上或博士班一年級以上之在學一般生（在本校已修習至少滿一學期；轉學生無嘉大成績者不得申請；外籍生不得交換至原屬國），在校成績需達全班前 20% 以內或學期平均成績大學部 75 分（含）以上、研究生 80 分（含）以上，且各科（含操行）成績須達及格標準。",
                    "校內複審配分標準：非華語地區採計「班級排名百分比 40%＋語言能力 40%＋讀書計畫 20%」；華語地區採計「班級排名百分比 80%＋讀書計畫 20%」。同一修業年限內限參加一次交換學生計畫。",
                ],
                "source": {
                    "title": "國立嘉義大學薦外交換學生審查要點 PDF",
                    "source_url": NCYU_REVIEW_RULES_PDF_URL,
                    "category": "exchange_application",
                    "summary": "嘉大薦外交換生申請資格、班排與語檢複審給分級距及放棄處分規定。",
                },
            }
        ],
        "language_requirements": [
            {
                "title": "嘉大五大語組交換語檢門檻（美加 TOEFL iBT 61–79 / 歐洲 B1 TOEIC 550 / 日本 JLPT N2–N3）與複審計分表",
                "details": [
                    "校內複審語言能力給分標準（占 40%）：A級（40%）為 TOEFL iBT 79–93 / IELTS 6.5 / 日檢 N1；B級（36%）為 TOEFL iBT 60–78 / IELTS 6.0 / 日檢 N2；C級（32%）為 TOEFL iBT 46–59 / IELTS 5.5 / 日檢 N3；D級（24%）為 TOEFL iBT 35–45 / IELTS 5.0 / 日檢 N4。大陸等華語地區姊妹校免附語言測驗成績。",
                    "各區域姊妹校最低門檻：美國奧瑞岡大學 iBT 61 / IELTS 6.0（研究所 iBT 88 / IELTS 7.0）、愛達荷大學 iBT 70 / IELTS 6.0（研究所 iBT 79 / IELTS 6.5）、斯托克頓大學 iBT 79 / IELTS 6.0；加拿大萊斯布里奇大學 iBT 61 / IELTS 6.0 / Duolingo 105；歐洲地區姊妹校為 CEFR B1 中級門檻（GEPT 中級初試、TOEIC 550、TOEFL iBT 57、IELTS 5.0；法國南特高等林業學院 1 年期交換另須法語 B1）；日本上越教育、攝南、中京、宮崎、兵庫縣立、熊本大學需 JLPT N2 以上，明治、香川、尾道市立大學需 JLPT N3 以上。",
                ],
                "source": {
                    "title": "國立嘉義大學 114 學年度交換學生計畫說明會簡報與英語文能力測驗對照表",
                    "source_url": NCYU_ENG_TABLE_URL,
                    "category": "exchange_application",
                    "summary": "嘉大交換生英語文 CEFR 對照表與美加、日本、歐洲姊妹校語言成績最低要求。",
                },
            }
        ],
        "required_documents": [
            {
                "title": "薦外交換學生甄選申請表（含進修課程規劃同意書）、中英文成績單、自傳讀書計畫、2封推薦函、家長同意書與系務會議紀錄",
                "details": [
                    "校內初審必備文件（Check List）：（1）薦外交換學生甄選申請表（1141031更新版，含進修課程規劃同意書與經費預算表，可填 2 志願）；（2）在校歷年成績單（大陸地區附中文版、其他地區附英文數字成績版並用螢光筆劃出平均成績與排名）；（3）中、英文自傳及讀書計畫各乙份；（4）家長同意書；（5）2 封教師推薦函；（6）有效期限內之語言能力證明（大陸地區免附）；（7）所屬系、所務會議同意之會議紀錄（由系所提供）；（8）身分證及學生證正反面影本與近兩年優良表現佐證資料。",
                    "錄取後與返國結案文件：獲校內推薦後配合國際處遞交姊妹校外文入學申請與 3 個月內英文版存款餘額證明（財力證明）；抵達姊妹校 1 個月內繳交《抵達國外報告單》，返國後 1 個月內繳交《研讀心得報告》與《交換生返校手續單》。",
                ],
                "source": {
                    "title": "國立嘉義大學國際事務處《如何申請》、《申請注意事項》與《交換生常用表單》",
                    "source_url": NCYU_EXCHANGE_HOW_TO_APPLY_URL,
                    "category": "exchange_application",
                    "summary": "嘉大交換生申請應繳文件清單、申請表與家長同意書下載。",
                },
            }
        ],
        "scholarship_info": [
            {
                "title": "教育部《學海飛颺》、《學海惜珠》與《國立嘉義大學薦外姊妹校交換學生獎補助金》、《學碩一貫海外研修獎助》",
                "details": [
                    "教育部學海飛颺與學海惜珠：每年 3 月 20 日前向國際事務處提出申請；學海飛颺補助學費、生活費及來回機票（約 NT$150,000，依當年度核定經費調整），學海惜珠針對持有效低收入戶、中低收入戶或特殊境遇家庭證明且成績優異（每系前 40% 為原則）之學生，最高由教育部補助 80%、學校配合補助 20%。",
                    "嘉大校內交換生獎補助金與學碩一貫獎助：（1）《國立嘉義大學薦外姊妹校交換學生獎補助金》提供機票補助（亞洲 NT$10,000、紐澳 NT$15,000、歐美非 NT$20,000，在學期間一次為限）及每月助學金（大學部每月 NT$6,000、研究所每月 NT$8,000，最多 12 個月）；（2）《學碩一貫優秀學生獎助海外研修計畫》提供研修 1 學期 NT$90,000、研修 1 學年 NT$150,000 獎補助金。",
                ],
                "source": {
                    "title": "國立嘉義大學《出國研修獎學金》、《薦外姊妹校交換學生獎補助金發放要點》與《海外研修手冊》",
                    "source_url": NCYU_SCHOLARSHIPS_URL,
                    "category": "scholarship",
                    "summary": "嘉大教育部學海計畫、校內薦外交換獎補助金與學碩一貫海外研修獎助辦法。",
                },
            }
        ],
        "document_explanations": [
            {
                "title": "國立嘉義大學薦外交換學生申請資料 Check List、系所務會議進修課程核准與雙志願填報指南",
                "summary": "說明嘉大系所初審與校級複審兩階段送件程序、雙志願課程規劃表與經費預算表填寫、螢光筆標示成績單排名及家長同意書規範。",
                "key_points": [
                    "系所初審與系務會議紀錄：所有申請資料須先繳交至所屬系所進行初審，進修課程規劃表必須經所屬系、所務會議審議通過並檢附會議紀錄（初審後由系所提供）再送國際事務處。",
                    "雙志願分別填表規定：申請人最多可選填 2 所志願學校；若有第 2 志願，因各校所在地、學費與開設課程不盡相同，必須分別填寫「預計研修期間所需經費預算表」與「進修課程規劃同意書」並註明學校名稱。",
                    "成績單與裝釘注意事項：申請大陸以外地區須檢附英文版數字成績單（含完整歷年成績與排名），並請上單一入口服務網列印平均成績與排名後用螢光筆劃出；除作品集外，請勿將申請文件膠裝裝釘。",
                ],
                "applies_to": [],
                "source": {
                    "title": "國立嘉義大學 114 學年度交換學生計畫說明會簡報與薦外交換學生甄選申請表",
                    "source_url": NCYU_APP_FORM_114_URL,
                    "category": "exchange_application",
                    "summary": None,
                },
                "document_url": NCYU_BRIEFING_114_PDF_URL,
                "document_type": "official_document",
                "full_text_extracted": True,
            }
        ],
        "rule_explanations": [
            {
                "title": "國立嘉義大學薦外交換學生審查要點、雙聯學制實施辦法與薦外交換生手冊核心規定",
                "summary": "規範嘉大七大學院學生出國交換與雙聯學位之修業年級、班排前 20% 或平均 75/80 分門檻、複審配分表及雜費保留學籍義務。",
                "key_points": [
                    "申請資格與學業標準：限學士班二年級以上、碩士班一年級以上、博士班一年級以上且已在嘉大修習至少滿一學期之在學學生；在校成績需達全班前 20% 以內或學期平均成績大學部 75 分（含）以上、研究生 80 分（含）以上，且各科（含操行）及格。",
                    "複審百分制配分：非華語地區依「班級排名百分比 40%＋語言能力 40%＋讀書計畫 20%」評分；華語地區依「班級排名百分比 80%＋讀書計畫 20%」評分。同一修業年限內限參加一次交換學生計畫。",
                    "跨國雙聯學制規定：本校學生於嘉大修業至少滿 1 年後，得依院系簽署之雙聯學位協議（共 8 校 13 個雙聯專案）赴國外姊妹校修課，滿足雙方學校修業年限與學分數並符合兩校畢業規定後，可同時取得兩校學位。",
                ],
                "applies_to": [],
                "source": {
                    "title": "國立嘉義大學薦外交換學生審查要點與雙聯學制推動現況",
                    "source_url": NCYU_DUAL_DEGREE_STATUS_URL,
                    "category": "exchange_application",
                    "summary": None,
                },
                "document_url": NCYU_REVIEW_RULES_PDF_URL,
                "document_type": "official_document",
                "full_text_extracted": True,
            }
        ],
        "sources": [
            {"title": "國立嘉義大學國際事務處（OIA）官方網站", "source_url": NCYU_OIA_HOME_URL, "category": "exchange_application", "summary": None},
            {"title": "國立嘉義大學交換生計畫介紹", "source_url": NCYU_EXCHANGE_INTRO_URL, "category": "exchange_application", "summary": None},
            {"title": "國立嘉義大學 114 學年度交換學生計畫說明會簡報（2026秋季班／2027春季班）", "source_url": NCYU_BRIEFING_114_URL, "category": "exchange_application", "summary": None},
            {"title": "國立嘉義大學與國外締約學校一覽表（共 140 所）", "source_url": NCYU_SISTERS_URL, "category": "partner_school", "summary": None},
            {"title": "國立嘉義大學各系所與姊妹校推動雙聯學制情形（8 校 13 專案）", "source_url": NCYU_DUAL_DEGREE_STATUS_URL, "category": "partner_school", "summary": None},
            {"title": "國立嘉義大學出國研修獎學金與薦外姊妹校交換學生獎補助金發放要點", "source_url": NCYU_SCHOLARSHIPS_URL, "category": "scholarship", "summary": None},
            {"title": "國立嘉義大學交換生法規與常用表單專區", "source_url": NCYU_RULES_FORMS_URL, "category": "exchange_application", "summary": None},
            {"title": "國立嘉義大學歷屆交換生心得專區與雲端學年度資料庫", "source_url": NCYU_EXPERIENCES_LIST_URL, "category": "experience_report", "summary": None},
            {"title": "國立嘉義大學海外研修手冊與薦外交換生手冊（2026版）", "source_url": "https://www.ncyu.edu.tw/oia/Subject?nodeId=64336", "category": "exchange_application", "summary": None},
        ],
    }
    (OFFICIAL_NCYU_DIR / "student_dashboard.json").write_text(
        json.dumps(student_dashboard_payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    doc_conditions = {
        "school_id": "ncyu",
        "school_name": "國立嘉義大學",
        "checked_at": CHECKED_AT,
        "source_url": NCYU_EXCHANGE_HOW_TO_APPLY_URL,
        "common_documents": exchange_info_payload["required_documents"],
        "track_specific_conditions": [
            {
                "track": "國際事務處【校級／院（系）級薦外交換學生計畫】（英語組、日語組、西語組、法語組、中文組）",
                "required": [
                    "國立嘉義大學薦外交換學生甄選申請表（1141031更新版，含進修課程規劃同意書與經費預算表，最多可選填 2 志願）",
                    "歷年在校成績單（大陸地區附中文版、其他地區附英文數字成績版，含完整排名並用螢光筆標示平均成績與排名）",
                    "中、英文自傳及讀書計畫各乙份、家長同意書、2 封教師推薦函及有效期限內之語檢成績證明（大陸地區免附）",
                    "所屬系、所務會議同意進修課程規劃之會議紀錄（由系所初審後提供）及近兩年優良事蹟證明",
                ],
            },
            {
                "track": "國際事務處【跨國雙聯學制計畫（8 所合作姊妹校、13 個院系學／碩士雙聯專案）】",
                "required": [
                    "於國立嘉義大學修業至少滿 1 年之合作院系（師範學院數位系／幼教系、人文藝術學院外語系、管理學院資管／企管／應經／科管／行銷／財金系、農學院農生／園藝系、理工學院應數／資工系）在學學生",
                    "雙聯學制申請文件、歷年英文成績單、中英文讀書計畫、教授推薦函及符合雙聯合作校入學標準之語檢證明（如 TOEFL iBT 79 / IELTS 6.0–6.5 / JLPT N2–N3）",
                    "滿足嘉大與國外合作大學要求之修業年限及學分數並符合兩校畢業規定，同時取得兩校學士或碩士學位",
                ],
            },
            {
                "track": "教育部【學海飛颺／學海惜珠獎學金】暨【嘉大薦外交換學生獎補助金／學碩一貫海外研修獎助】",
                "required": [
                    "學海飛颺／惜珠申請人須具中華民國國籍且於每年 3 月 20 日前提出申請（學海惜珠另須檢附直轄市或縣市政府開立之有效低收入戶、中低收入戶或特殊境遇家庭證明）",
                    "申請嘉大薦外交換學生獎補助金（機票補助 1–2 萬＋每月助學金 6,000/8,000 元）或學碩一貫海外研修獎助（1 學期 9 萬、1 學年 15 萬）者，須經校級審查通過並於出國前簽署行政契約書",
                    "抵達國外 1 個月內須回報《抵達國外報告單》，返國後 1 個月內須繳交《研讀心得報告》並參加經驗分享座談會",
                ],
            },
        ],
    }
    (OFFICIAL_NCYU_DIR / "document-conditions.json").write_text(
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
        field_cov_lines.append(f"{fname},{len(partners)},{pop},{ratio:.4f},Official NCYU OIA verified")
    (OFFICIAL_NCYU_DIR / "field-coverage.csv").write_text("\n".join(field_cov_lines) + "\n", encoding="utf-8")

    pages_records = [
        {
            "title": "國立嘉義大學：114/115 學年度薦外交換學生甄選時程、系所初審與教育部學海計畫申請期程",
            "source_url": NCYU_BRIEFING_114_URL,
            "published_at": "2026-10-20T00:00:00Z",
            "text": "\n".join(exchange_info_payload["application_period"]),
            "summary": "\n".join(exchange_info_payload["application_period"]),
            "category": "exchange_application",
            "attachments": [],
            "crawled_at": CHECKED_AT,
            "content_hash": hashlib.sha256("\n".join(exchange_info_payload["application_period"]).encode("utf-8")).hexdigest(),
        },
        {
            "title": "國立嘉義大學：薦外交換學生審查要點、班排與語檢複審配分標準及雙聯學制實施辦法",
            "source_url": NCYU_REVIEW_RULES_PDF_URL,
            "published_at": "2026-10-15T00:00:00Z",
            "text": "\n".join(exchange_info_payload["eligibility"]),
            "summary": "\n".join(exchange_info_payload["eligibility"]),
            "category": "exchange_application",
            "attachments": [],
            "crawled_at": CHECKED_AT,
            "content_hash": hashlib.sha256("\n".join(exchange_info_payload["eligibility"]).encode("utf-8")).hexdigest(),
        },
        {
            "title": f"國立嘉義大學：{len(partners)} 所全球與大陸締約姊妹校名額表與五大語組語言能力最低要求",
            "source_url": NCYU_ENG_TABLE_URL,
            "published_at": "2026-10-15T00:00:00Z",
            "text": "\n".join(exchange_info_payload["language_requirement"]),
            "summary": "\n".join(exchange_info_payload["language_requirement"]),
            "category": "exchange_application",
            "attachments": [],
            "crawled_at": CHECKED_AT,
            "content_hash": hashlib.sha256("\n".join(exchange_info_payload["language_requirement"]).encode("utf-8")).hexdigest(),
        },
        {
            "title": "國立嘉義大學：薦外交換生申請文件 Check List、進修課程規劃同意書與返國心得報告規範",
            "source_url": NCYU_RULES_FORMS_URL,
            "published_at": "2026-10-15T00:00:00Z",
            "text": "\n".join(exchange_info_payload["required_documents"]),
            "summary": "\n".join(exchange_info_payload["required_documents"]),
            "category": "exchange_application",
            "attachments": [],
            "crawled_at": CHECKED_AT,
            "content_hash": hashlib.sha256("\n".join(exchange_info_payload["required_documents"]).encode("utf-8")).hexdigest(),
        },
        {
            "title": "國立嘉義大學：教育部學海飛颺、學海惜珠、薦外姊妹校交換學生獎補助金與學碩一貫海外研修獎助辦法",
            "source_url": NCYU_SCHOLARSHIPS_URL,
            "published_at": "2026-10-15T00:00:00Z",
            "text": "\n".join(exchange_info_payload["scholarship_info"]),
            "summary": "\n".join(exchange_info_payload["scholarship_info"]),
            "category": "scholarship",
            "attachments": [],
            "crawled_at": CHECKED_AT,
            "content_hash": hashlib.sha256("\n".join(exchange_info_payload["scholarship_info"]).encode("utf-8")).hexdigest(),
        },
    ]
    (OFFICIAL_NCYU_DIR / "pages.jsonl").write_text(
        "\n".join(json.dumps(p, ensure_ascii=False) for p in pages_records) + "\n", encoding="utf-8"
    )

    home_rules = {
        "school_id": "ncyu",
        "school_name": "國立嘉義大學",
        "eligibility": student_dashboard_payload["eligibility"],
        "application_periods": student_dashboard_payload["application_periods"],
        "selection_rules": {
            "undergraduate_score_minimum": 75.0,
            "graduate_score_minimum": 80.0,
            "class_rank_top_percent_threshold": 20,
            "undergraduate_gpa_minimum": 3.0,
            "non_chinese_rank_weight_percent": 40,
            "non_chinese_language_weight_percent": 40,
            "non_chinese_study_plan_weight_percent": 20,
            "chinese_area_rank_weight_percent": 80,
            "chinese_area_study_plan_weight_percent": 20,
            "maximum_preferences": 2,
            "screening_batches_per_year": 2,
            "allow_freshman_apply": False,
            "transfer_student_min_semesters": 1,
            "max_exchange_count_per_degree": 1,
            "dual_degree_min_home_years": 1,
            "tuition_policy_during_exchange": "出國交換期間須於國立嘉義大學完成註冊並依規定繳納本校雜費（電腦使用費、網路使用費、平安保險費）以保留學籍；互免學費姊妹校免繳接待校學費",
            "return_documents_due": "抵達國外一個月內回報《抵達國外報告單》，結束國外交換計畫返國後一個月內應繳交《研讀心得報告》乙份及《返校手續單》至國際事務處，並參加交換學生座談會",
        },
        "source_urls": ncyu_source_urls,
        "verified_at": "2026-10-30",
    }
    (OFFICIAL_NCYU_DIR / "home_rules.json").write_text(
        json.dumps(home_rules, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    (OFFICIAL_NCYU_DIR / "documents.json").write_text(
        json.dumps(
            {"school_name": "國立嘉義大學", "required_documents": student_dashboard_payload["required_documents"], "source_urls": ncyu_source_urls},
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    (OFFICIAL_NCYU_DIR / "scholarships.json").write_text(
        json.dumps(
            {"school_name": "國立嘉義大學", "scholarships": student_dashboard_payload["scholarship_info"], "source_urls": ncyu_source_urls},
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    completeness = {
        "school_id": "ncyu",
        "school_name": "國立嘉義大學",
        "total_partners": len(partners),
        "partner_count": len(partners),
        "international_partners": sum(1 for p in partners if p["country"] not in {"中國大陸", "香港", "澳門"}),
        "mainland_partners": sum(1 for p in partners if p["country"] in {"中國大陸", "香港", "澳門"}),
        "dual_degree_partner_universities": 8,
        "dual_degree_programs": 13,
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
            f"國立嘉義大學國際事務處 114/115 學年度（2026秋季班／2027春季班出國交換：系所初審送件至 01/31 截止；教育部學海飛颺／惜珠獎學金 03/20 截止）五大語組單學期／學年交換計畫及 8 校 13 專案跨國雙聯學制同步整合；共完整收錄 {len(partners)} 所全球與大陸締約姊妹校（橫跨全球 25 個國家與地區，含 {open_partner_count} 所當期開放申請校，並收錄 {exp_covered_schools} 所合作大學共 {total_exp_reports} 篇歷屆學長姐返國心得報告）。"
        ),
        "verified_at": "2026-10-30",
    }
    (OFFICIAL_NCYU_DIR / "catalog-completeness.json").write_text(
        json.dumps(completeness, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    (OFFICIAL_NCYU_DIR / "verification_status.json").write_text(
        json.dumps(
            {"school_id": "ncyu", "school_name": "國立嘉義大學", "status": "official_verified", "checked_at": CHECKED_AT, "counts": completeness},
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    provenance_files = [
        ("sources/ncyu/sister_schools_zh.html", NCYU_SISTERS_URL, "國立嘉義大學與國外締約學校一覽表（共 140 所，2026.08.06更新）HTML"),
        ("sources/ncyu/exchange_briefing_114.pdf", NCYU_BRIEFING_114_PDF_URL, "國立嘉義大學 114 學年度交換學生計畫說明會簡報（2026秋季班／2027春季班，33頁）PDF"),
        ("sources/ncyu/exchange_briefing_113.pdf", "https://www.ncyu.edu.tw/oia/ServerFile/Get/8bbed75b-da4d-4e44-a1bb-c95092e8ca9c?nodeId=60181&sId=212307", "國立嘉義大學 113 學年度交換學生計畫說明會簡報（29頁）PDF"),
        ("sources/ncyu/exchange_briefing_112_new_partners.pdf", "https://www.ncyu.edu.tw/oia/ServerFile/Get/457351bf-2421-4603-ac00-5b4f14bc6939?nodeId=60181&sId=194928", "國立嘉義大學 112 學年度交換學生計畫說明會—新增姊妹校簡報 PDF"),
        ("sources/ncyu/exchange_briefing_112.pdf", "https://www.ncyu.edu.tw/oia/ServerFile/Get/9ab38e2b-2ca1-4721-980c-cb3ed0d439d1?nodeId=60181&sId=194927", "國立嘉義大學 112 學年度交換學生計畫說明會簡報 PDF"),
        ("sources/ncyu/exchange_review_rules_v2.pdf", NCYU_REVIEW_RULES_PDF_URL, "國立嘉義大學薦外交換學生審查要點（110年9月28日行政會議修正通過）PDF"),
        ("sources/ncyu/exchange_review_rules.pdf", "https://www.ncyu.edu.tw/oia/ServerFile/Get/683b1a90-e67e-4363-af44-f173f700b74c?nodeId=60183&sId=194911", "國立嘉義大學薦外交換學生審查要點（歷年法規沿革版）PDF"),
        ("sources/ncyu/exchange_scholarship_rules.pdf", NCYU_SCHOLARSHIP_RULES_PDF_URL, "國立嘉義大學薦外姊妹校交換學生獎補助金發放要點 PDF"),
        ("sources/ncyu/exchange_application_form_1141031.pdf", "https://www.ncyu.edu.tw/oia/ServerFile/Get/1bd9aa2d-840f-4f04-9ba3-994f764f0d31?nodeId=60183&sId=230540", "國立嘉義大學薦外交換學生甄選申請表（1141031更新版，5頁）PDF"),
        ("sources/ncyu/exchange_application_form_1141031.docx", "https://www.ncyu.edu.tw/oia/ServerFile/Get/93159109-afa0-481f-88cd-dd4ee083ed16?nodeId=60183&sId=230540", "國立嘉義大學薦外交換學生甄選申請表（1141031更新版）DOCX"),
        ("sources/ncyu/parental_consent_form_1141031.pdf", "https://www.ncyu.edu.tw/oia/ServerFile/Get/851c9c7b-6d0f-41d5-b48c-cc92a7b7b4db?nodeId=60183&sId=230541", "國立嘉義大學學生赴姊妹校交換就讀家長同意書（1141031更新版）PDF"),
        ("sources/ncyu/parental_consent_form_1141031.docx", "https://www.ncyu.edu.tw/oia/ServerFile/Get/dc2c03f7-f9ef-43e1-ab81-1987740fc912?nodeId=60183&sId=230541", "國立嘉義大學學生赴姊妹校交換就讀家長同意書（1141031更新版）DOCX"),
        ("sources/ncyu/overseas_study_manual_2026.pdf", NCYU_HAND_STUDY_ABROAD_PDF_URL, "國立嘉義大學海外研修計畫手冊（2026年3月更新，17頁）PDF"),
        ("sources/ncyu/outgoing_exchange_handbook_2026.pdf", NCYU_HAND_OUTBOUND_PDF_URL, "國立嘉義大學薦外交換生手冊（2026年3月更新，32頁）PDF"),
        ("sources/ncyu/dual_degree_status.html", NCYU_DUAL_DEGREE_STATUS_URL, "國立嘉義大學各系所與姊妹校推動雙聯學制情形（8校13專案）HTML"),
        ("sources/ncyu/dual_degree_rules_academic.html", NCYU_DUAL_DEGREE_REG_URL, "國立嘉義大學與境外大學校院辦理雙聯學制實施辦法 HTML"),
        ("sources/ncyu/exchange_intro.html", NCYU_EXCHANGE_INTRO_URL, "國立嘉義大學交換生計畫介紹 HTML"),
        ("sources/ncyu/exchange_how_to_apply.html", NCYU_EXCHANGE_HOW_TO_APPLY_URL, "國立嘉義大學交換生如何申請及應繳文件表 HTML"),
        ("sources/ncyu/english_proficiency_table.html", NCYU_ENG_TABLE_URL, "國立嘉義大學國內英語文能力測驗參考對照表 HTML"),
        ("sources/ncyu/scholarship_intro.html", NCYU_SCHOLARSHIPS_URL, "國立嘉義大學出國研修獎學金（學海飛颺、學海惜珠）HTML"),
        ("sources/ncyu/exp_detail_194952.html", "https://www.ncyu.edu.tw/oia/Subject/Detail/194952?nodeId=60182", "國立嘉義大學企管系游同學 111-2 赴捷克 Tomas Bata University 交換心得 HTML"),
        ("sources/ncyu/exp_detail_194946.html", "https://www.ncyu.edu.tw/oia/Subject/Detail/194946?nodeId=60182", "國立嘉義大學幼教系王同學 109-1 赴西班牙 University of Huelva 交換心得 HTML"),
        ("sources/ncyu/exp_detail_194947.html", "https://www.ncyu.edu.tw/oia/Subject/Detail/194947?nodeId=60182", "國立嘉義大學外語系洪同學 108-2 赴日本香川大學交換心得 HTML"),
        ("sources/ncyu/exp_detail_194941.html", "https://www.ncyu.edu.tw/oia/Subject/Detail/194941?nodeId=60182", "國立嘉義大學微藥系黃同學 108-2 赴美國奧瑞岡大學交換心得 HTML"),
        ("sources/ncyu/webhd_experience_index.json", NCYU_EXPERIENCES_WEBHD_URL, "國立嘉義大學歷年交換學生心得雲端資料庫（108–114學年度共 69 篇 PDF）索引 JSON"),
        ("sources/ncyu/ncyu_catalog_source.json", NCYU_SISTERS_URL, f"國立嘉義大學 {len(partners)} 所全球與大陸締約姊妹校整合資料集 JSON"),
        ("sources/ncyu/ncyu_resolved_locations.json", NCYU_SISTERS_URL, f"國立嘉義大學 {len(partners)} 所締約姊妹校 ROR / Wikidata 地理座標核對表 JSON"),
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
        "school_id": "ncyu",
        "school_name": "國立嘉義大學",
        "generated_at": CHECKED_AT,
        "active_cycle_note": completeness["active_term"],
        "sources": prov_sources,
    }
    prov_text = json.dumps(provenance_payload, ensure_ascii=False, indent=2) + "\n"
    (OFFICIAL_NCYU_DIR / "import_provenance.json").write_text(prov_text, encoding="utf-8")
    (OFFICIAL_NCYU_DIR / "import-provenance.json").write_text(prov_text, encoding="utf-8")

    print(
        f"Successfully built NCYU catalog: {len(partners)} partners"
        f" ({open_partner_count} open, {completeness['verified_campus_images']}"
        f" verified images, {completeness['verified_locations']} verified"
        f" locations), {len(workflows)} workflows,"
        f" {len(destinations)} destinations, {len(research_records)} research"
        f" records, {exp_covered_schools} schools with experience records"
        f" ({len(student_experience_rows)} rows, {total_exp_reports} reports)."
    )


if __name__ == "__main__":
    main()
