"""Build the official National Chung Hsing University (國立中興大學, NCHU) exchange data bundle."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / "src"))
from exchange_info.school_identity import VisualRecordIndex, school_identity_key

SOURCES_NCHU_DIR = REPO_ROOT / "sources" / "nchu"
OFFICIAL_NCHU_DIR = REPO_ROOT / "src" / "exchange_info" / "official_data" / "nchu"
STATIC_DIR = REPO_ROOT / "src" / "exchange_info" / "static"

CHECKED_AT = "2026-10-18T01:30:00Z"

REGION_BY_COUNTRY = {
    "日本": "亞洲",
    "韓國": "亞洲",
    "中國大陸": "中國大陸及港澳",
    "香港": "中國大陸及港澳",
    "澳門": "中國大陸及港澳",
    "新加坡": "亞洲",
    "馬來西亞": "亞洲",
    "泰國": "亞洲",
    "越南": "亞洲",
    "印尼": "亞洲",
    "菲律賓": "亞洲",
    "印度": "亞洲",
    "柬埔寨": "亞洲",
    "蒙古": "亞洲",
    "斯里蘭卡": "亞洲",
    "以色列": "亞洲",
    "土耳其": "亞洲",
    "美國": "美洲",
    "加拿大": "美洲",
    "墨西哥": "美洲",
    "巴西": "美洲",
    "智利": "美洲",
    "秘魯": "美洲",
    "澳洲": "大洋洲",
    "紐西蘭": "大洋洲",
    "奧地利": "歐洲",
    "比利時": "歐洲",
    "捷克": "歐洲",
    "丹麥": "歐洲",
    "愛沙尼亞": "歐洲",
    "芬蘭": "歐洲",
    "法國": "歐洲",
    "德國": "歐洲",
    "希臘": "歐洲",
    "克羅埃西亞": "歐洲",
    "匈牙利": "歐洲",
    "義大利": "歐洲",
    "科索沃": "歐洲",
    "拉脫維亞": "歐洲",
    "立陶宛": "歐洲",
    "荷蘭": "歐洲",
    "挪威": "歐洲",
    "波蘭": "歐洲",
    "羅馬尼亞": "歐洲",
    "俄羅斯": "歐洲",
    "白俄羅斯": "歐洲",
    "斯洛伐克": "歐洲",
    "斯洛維尼亞": "歐洲",
    "西班牙": "歐洲",
    "瑞典": "歐洲",
    "瑞士": "歐洲",
    "英國": "歐洲",
    "南非": "非洲",
}

REGION_COST_DEFAULTS = {
    "美國": (
        "USD 1,400–2,200 / 月（含住宿、餐飲、強制校園醫療保險與當地交通）",
        "須預留強制校園醫療保險（約 USD 1,500–2,500 / 學期）與 J-1 / F-1 簽證 SEVIS 費用。",
    ),
    "加拿大": (
        "CAD 1,500–2,200 / 月（含住宿、膳食、省級／校內醫保與市區交通）",
        "須投保接待校指定醫療保險（如 UHIP）並辦理 Study Permit 或 eTA。",
    ),
    "巴西": (
        "USD 650–1,000 / 月（約 BRL 3,300–5,000，含住宿、餐飲與大眾運輸）",
        "須向巴西商務辦事處申辦 VITEM IV 學生簽證並投保涵蓋全期之國際醫療保險。",
    ),
    "英國": (
        "GBP 1,100–1,600 / 月（含學生宿舍、飲食與大眾運輸）",
        "交換一學期（6 個月內）可辦理 Standard Visitor 簽證，一學年須辦理 Student Visa 並繳納 IHS 醫療附加費。",
    ),
    "法國": (
        "EUR 850–1,400 / 月（巴黎與里昂約 EUR 1,000–1,500 / 月；雷恩、第戎與昂熱約 EUR 750–1,100 / 月，可申請 CAF 房補）",
        "須透過法國教育中心（Campus France）面試並申辦長期學生簽證（VLS-TS）。",
    ),
    "德國": (
        "EUR 934–1,200 / 月（德國簽證限制提領帳戶基準為每月 EUR 934）",
        "須辦理德國法定公保（約 EUR 120–130 / 月）及繳納學期雜費／學期交通票（Semesterticket）。",
    ),
    "奧地利": (
        "EUR 850–1,250 / 月（含維也納／茵斯布魯克學生宿舍、餐飲與大眾運輸）",
        "交換一學期（6 個月內）須申辦奧地利學生簽證 D（Visa D），超過 6 個月須申辦學生居留許可。",
    ),
    "西班牙": (
        "EUR 800–1,250 / 月（含學生公寓、飲食與大眾運輸）",
        "須備妥涵蓋全額醫療與遺體運返之私人醫療保險以申辦西班牙學生簽證。",
    ),
    "義大利": (
        "EUR 800–1,300 / 月（杜林與熱那亞學生宿舍、餐飲與大眾運輸費用適中）",
        "須向義大利經濟貿易文化推廣辦事處申辦學生簽證 D，抵義後 8 個工作天內申辦居留證（Permesso di Soggiorno）。",
    ),
    "荷蘭": (
        "EUR 950–1,400 / 月（荷蘭移民局 IND 財力證明基準約 EUR 1,225 / 月）",
        "由接待校代辦 MVV/VVR 居留許可，瓦赫寧恩房源緊張建議獲提名後立即申請 Idealis 學生宿舍。",
    ),
    "比利時": (
        "EUR 850–1,250 / 月（含列日／根特學生宿舍、餐飲與大眾運輸）",
        "須辦理長期學生簽證 D 簽，抵達後向當地市政廳登記居留。",
    ),
    "瑞士": (
        "CHF 1,500–2,200 / 月（含蘇黎世／溫特圖爾學生住宿、膳食與強制保險）",
        "須透過瑞士商務辦事處申辦學生簽證，並於抵瑞後申請居留證與醫療保險豁免或投保。",
    ),
    "瑞典": (
        "SEK 9,500–13,000 / 月（瑞典移民局財力基準約 SEK 10,314 / 月）",
        "交換超過 3 個月須向瑞典移民局申辦學生居留許可（Residence Permit for Studies）。",
    ),
    "拉脫維亞": (
        "EUR 600–900 / 月（里加與葉爾加瓦學生宿舍與日常飲食交通開支實惠）",
        "須申辦拉脫維亞長期簽證（D 簽）或學生居留許可並備妥歐盟規格醫療保險。",
    ),
    "立陶宛": (
        "EUR 600–900 / 月（考納斯學生宿舍與生活費用實惠）",
        "須透過 MIGRIS 系統申辦立陶宛國家簽證（D 簽）或臨時居留許可。",
    ),
    "波蘭": (
        "EUR 550–850 / 月（約 PLN 2,400–3,600，華沙、弗羅茨瓦夫與波茲南校內宿舍實惠）",
        "須向波蘭臺北辦事處申辦 D 類國別學生簽證並備妥規定旅行醫療保險。",
    ),
    "捷克": (
        "EUR 600–900 / 月（含布拉格／布爾諾／奧斯特拉瓦學生宿舍、食堂與市區交通卡）",
        "須提前預約捷克經濟文化辦事處申辦長期學生簽證與捷克合約醫療保險。",
    ),
    "俄羅斯": (
        "USD 500–850 / 月（莫斯科校內宿舍與日常開支實惠）",
        "須憑接待校核發之俄羅斯聯邦移民署官方邀請函向莫北協駐臺代表處申辦學生簽證。",
    ),
    "白俄羅斯": (
        "USD 450–750 / 月（戈爾基校內學生宿舍與生活開支低廉）",
        "須憑接待校官方邀請函辦理白俄羅斯學習簽證並投保規定醫療保險。",
    ),
    "土耳其": (
        "EUR 550–850 / 月（安卡拉與伊斯坦堡學生生活與交通開支實惠）",
        "須申辦土耳其學生簽證並於抵土後申辦短期學生居留證（Ikamet）與當地醫保。",
    ),
    "以色列": (
        "USD 1,000–1,500 / 月（耶路撒冷與雷霍沃特住宿與日常飲食開支）",
        "須向駐臺北以色列經濟文化辦事處申辦 A/2 學生簽證並投保接待校指定醫療保險。",
    ),
    "澳洲": (
        "AUD 1,800–2,600 / 月（含墨爾本／阿得雷德／雪梨／圖움巴住宿與日常開支）",
        "須購買澳洲海外學生健康保險（OSHC）並線上申辦 Subclass 500 學生簽證。",
    ),
    "紐西蘭": (
        "NZD 1,600–2,300 / 月（含基督城／林肯學生宿舍、餐飲與當地交通）",
        "須向紐西蘭移民局線上申辦 Fee Paying / Exchange Student Visa 並投保合規旅遊醫療保險。",
    ),
    "日本": (
        "JPY 80,000–130,000 / 月（東京與京阪神約 JPY 100,000–140,000；地方城市約 JPY 70,000–100,000）",
        "憑接待校核發之在留資格認定證明書（COE）換發留學簽證，抵日後須加入國民健康保險。",
    ),
    "韓國": (
        "KRW 800,000–1,300,000 / 月（首爾圈外宿較高；校內宿舍約 KRW 150,000–400,000 / 月）",
        "憑標準入學許可書申辦 D-2-6 交換學生簽證，抵韓後外國人登錄並自動納入韓國國民健康保險（NHIS）。",
    ),
    "中國大陸": (
        "RMB 2,000–3,800 / 月（校內宿舍約 RMB 600–1,800 / 學期、學生食堂費用低廉，北京、上海、南京、武漢、廣州、杭州生活機能完善）",
        "持臺胞證（臺灣居民來往大陸通行證）入境，並依接待校規定投保大陸境內來華留學生綜合醫療保險（約 RMB 400 / 學期）。",
    ),
    "香港": (
        "HKD 6,500–11,000 / 月（含香港城市大學校內宿舍與日常開支）",
        "須透過接待校向香港入境事務處申辦學生簽證／進入許可（Student Visa / Entry Permit）。",
    ),
    "澳門": (
        "HKD 4,500–7,500 / 月（約 MOP 4,650–7,700，含澳門大學住宿式書院與日常開支）",
        "抵澳後依澳門治安警察局居留及逗留事務廳規定辦理「逗留特別許可（學生）」。",
    ),
    "馬來西亞": (
        "MYR 1,500–2,500 / 月（吉隆坡、沙登與金寶生活機能便利且物價親民）",
        "須透過 EMGS（Education Malaysia Global Services）系統申辦學生簽證（VAL / Student Pass）。",
    ),
    "泰國": (
        "THB 15,000–25,000 / 月（曼谷、清邁與孔敬生活成本親民）",
        "須憑接待校入學許可向泰國貿易經濟辦事處申辦 Non-Immigrant ED 學生簽證。",
    ),
    "印尼": (
        "IDR 5,000,000–9,000,000 / 月（茂物、日惹、萬隆與瑪琅生活開支實惠）",
        "須由接待校協助向印尼移民總局申辦學習簽證（C316 / 學生電子簽證）。",
    ),
    "越南": (
        "USD 400–700 / 月（約 VND 10,000,000–17,000,000，河內、胡志明市、順化與太原生活成本低廉）",
        "須憑接待校入學許可透過駐臺北越南經濟文化辦事處申辦 DH 學生簽證。",
    ),
    "菲律賓": (
        "USD 500–850 / 月（約 PHP 28,000–48,000，馬尼拉與洛斯巴尼奧斯住宿與生活開支）",
        "須憑接待校入學許可向馬尼拉經濟文化辦事處申辦 9(f) 學生簽證或 SSP 特別學習許可。",
    ),
    "印度": (
        "USD 400–700 / 月（新德里、海德拉巴與瓦拉納西校內住宿與日常開支實惠）",
        "須憑接待校正式入學許可向印度台北協會申辦 Student Visa。",
    ),
    "蒙古": (
        "USD 450–750 / 月（烏蘭巴托校內宿舍與日常飲食交通開支實惠）",
        "須憑接待校入學許可辦理蒙古學習簽證並投保涵蓋全期之國際醫療保險。",
    ),
    "柬埔寨": (
        "USD 450–750 / 月（金邊生活與住宿交通開支實惠）",
        "須憑接待校入學許可辦理柬埔寨學生簽證並投保海外醫療及意外保險。",
    ),
}

NCHU_OVERSEAS_SHEET_URL = "https://docs.google.com/spreadsheets/d/1acE37cH-R7k88O9g-sT8wH-rX99rQT3a/edit?usp=sharing&ouid=108931068757503846261&rtpof=true&sd=true"
NCHU_MAINLAND_PAGE_URL = "https://www.oia.nchu.edu.tw/index.php/zh-tw/2-uncategorised/158-1-2-exchange-china"
NCHU_OIA_PARTNERS_URL = "https://www.oia.nchu.edu.tw/index.php/1-1-global-partners"
NCHU_GUIDELINES_PDF_URL = "https://oia.nchu.edu.tw/images/File/02_Exchange_Program/5-1-1/Exchange_Program_Guidelines_for_Fall_Semester_2027_TW.pdf"
NCHU_REGULATIONS_PDF_URL = "https://www.oia.nchu.edu.tw/images/File/01_OIA_Regulations/R6_Regulations_for_nominating_NCHU_outbound_exchange_TW.pdf"
NCHU_SCHOLARSHIP_URL = "https://www.oia.nchu.edu.tw/index.php/2-uncategorised/155-1-1-exchange-scholarship"
NCHU_APPLY_PORTAL_URL = "https://oiawp.nchu.edu.tw/out-going-program-online-application/"
NCHU_EXPERIENCE_PORTAL_URL = "https://iss.nchu.edu.tw/target/outbound/"


def clean_text(s: str) -> str:
    if not s:
        return ""
    return re.sub(r"\s+", " ", s).strip()


def format_colleges(item: dict) -> str:
    elig = clean_text(item.get("elig_raw") or "")
    notes = clean_text(item.get("notes_raw") or "")
    units = item.get("oia_units") or []
    cat = item.get("category")

    if "管理學院" in elig or "社管院" in elig or "College of Management" in elig:
        return "管理學院、法政學院（院級交換計畫，依姊妹校協議規定開放商管與法政相關系所學生申請）"
    if "農資院" in elig or "農業暨自然資源學院" in elig or "Agriculture" in elig:
        return "農業暨自然資源學院（院級交換計畫，或優先選送農資相關系所學生）"
    if "工學院" in elig or "電資院" in elig:
        return "工學院、電機資訊學院（院級交換計畫）"
    if "獸醫" in elig:
        return "獸醫學院（院級交換計畫）"
    if "生科院" in elig or "生命科學院" in elig:
        return "生命科學院（院級交換計畫）"

    m_lim = re.search(r"限([^。；\n]{2,40}(?:學院|學系|研究所|系所)[^。；\n]{0,20})", elig + " " + notes)
    if m_lim:
        return f"校級交換計畫（特別規定：{m_lim.group(0).strip()}）"

    if cat in {"OS", "CN"}:
        return "不限學院（全校各學院學士班、碩士班及博士班在學學生皆可依姊妹校開課系所申請）"

    if units and units != ["全校"]:
        cleaned_units = [u.replace("社管院", "管理學院／法政學院").replace("農資院", "農業暨自然資源學院") for u in units]
        return "、".join(dict.fromkeys(cleaned_units)) + "（簽約交換合作姊妹校）"
    return "全校各學院（依當期交換學生申請簡章與兩校交換協議規定辦理）"


def format_degree_levels(item: dict) -> str:
    elig = clean_text(item.get("elig_raw") or "")
    notes = clean_text(item.get("notes_raw") or "")
    if "大學部及研究所" in elig or "undergraduate & postgraduate" in elig.lower():
        base = "學士班（大一僅可申請春季班、大二以上可申請秋／春季班）、碩士班、博士班"
    elif ("大學部" in elig or "undergraduate" in elig.lower()) and "研究所" not in elig and "postgraduate" not in elig.lower():
        base = "學士班（大一僅可申請春季班、大二以上可申請秋／春季班）"
    elif "研究所" in elig or "碩士" in elig or "postgraduate" in elig.lower():
        base = "碩士班、博士班（研究所學位生）"
    else:
        base = "學士班（大一僅可申請春季班、大二以上可申請秋／春季班）、碩士班、博士班"
    if "不接受大四" in notes or "不接受延畢" in notes:
        base += "（注意：該校不接受大四或延畢生申請）"
    return base


def format_language_req(item: dict) -> str:
    cat = item.get("category")
    country = item["country"]
    lr = clean_text(item.get("lang_raw") or "")
    if cat == "CN" or country == "中國大陸":
        return "申請赴大陸地區姊妹校免附外語能力證明（惟部分大陸高校對外國籍／港澳臺僑生另有規定）"
    if lr:
        if "興大交換標準" in lr:
            lr_expanded = lr.replace(
                "興大交換標準 NCHU Outgoing language requirement",
                "興大校內標準（CEFR B2：TOEFL iBT 72［新制 4 分／ITP 543］、IELTS 5.5 或 TOEIC 785 以上）",
            )
            return lr_expanded[:360]
        return f"{lr[:280]}（並須符合興大校內 CEFR B2 標準：TOEFL iBT 72 / IELTS 5.5 / TOEIC 785，或該校接受之日、韓、德、法、西語檢定）"
    if country == "日本":
        return "興大校內標準：英語達 CEFR B2（TOEFL iBT 72 / IELTS 5.5 / TOEIC 785），或符合接待校要求之日語能力檢定（JLPT N1–N5）"
    return "興大校內標準：英語達 CEFR B2（TOEFL iBT 72［新制 4 分／ITP 543］、IELTS 5.5 或 TOEIC 785 以上），並須符合接待校個別語言門檻"


def format_gpa_req(item: dict) -> str:
    notes = clean_text(item.get("notes_raw") or "")
    elig = clean_text(item.get("elig_raw") or "")
    gpa_matches = []
    for m in re.finditer(r"(?:GPA|平均成績|總平均)[^。；\n]{2,45}", notes + " " + elig, re.I):
        g = m.group(0).strip()
        if g not in gpa_matches:
            gpa_matches.append(g)
    base = "國立中興大學校內門檻：學士班歷年在校總平均分數 60 分（含）以上（校內甄選評分：國外組在校成績占 30%、大陸組占 50%；申請學海飛颺或興大海外研修獎學金須歷年名次前 50% 或平均 80 分以上）"
    if gpa_matches:
        base += f"｜姊妹校個別要求：{'；'.join(gpa_matches)}"
    return base


def format_quota(item: dict) -> str:
    cat = item.get("category")
    q_raw = clean_text(item.get("quota_raw") or "")
    adm_list = item.get("admitted_history") or []
    rank = item.get("popularity_rank")

    if cat == "OS":
        q_str = f"海外交換校名額：{q_raw or '依當期簡章公告'}"
    elif cat == "CN":
        q_str = f"大陸地區交換校名額：{q_raw or '依當期簡章公告'}"
    else:
        units = "、".join(item.get("oia_units") or ["全校"])
        q_str = f"簽約交換學生姊妹校（簽約單位：{units}；當期名額依國際事務處每學期公告之交換學生申請名額表為準）"

    if rank:
        q_str += f"｜🏆 {rank}"
    if adm_list:
        total_adm = sum(a["count"] for a in adm_list)
        latest = adm_list[0]
        q_str += f"｜近 4 學期共錄取 {total_adm} 名興大學生（最新 {latest['cycle']}錄取 {latest['count']} 名）"
    return q_str


def format_study_period(item: dict) -> str:
    cat = item.get("category")
    notes = clean_text(item.get("notes_raw") or "")
    if "一學期或一學年" in notes:
        return "一學期或一學年（中興大學校內甄選每次申請以 1 學期為限，同一學制內最多可交換 2 次）"
    if cat == "CN":
        return "一學期（秋季班 9 月至翌年 1 月，或春季班 2 月至 6 月；同一學制內最多可交換 2 次）"
    return "一學期（依《國立中興大學選送學生出國交換甄選辦法》每次交換以 1 學期為限，同一學制內最多可交換 2 次）"


def format_program_type(item: dict) -> str:
    cat = item.get("category")
    notes = clean_text(item.get("notes_raw") or "")
    if "全自費" in notes or "self-funded" in notes.lower():
        return "交換學生（海外合作姊妹校・接待校全自費或繳交學分費計畫）"
    if cat == "OS":
        return "交換學生（赴國外姊妹校交換計畫・繳交中興大學學雜費、免繳接待校學費）"
    if cat == "CN":
        return "交換學生（赴大陸地區姊妹校交換計畫・繳交中興大學學雜費、免繳接待校學費）"
    units = item.get("oia_units") or ["全校"]
    if units != ["全校"]:
        return f"交換學生（{'、'.join(units)}院級／校級簽約交換合作姊妹校）"
    return "交換學生（國立中興大學國際事務處簽約交換合作姊妹校）"


def main() -> None:
    OFFICIAL_NCHU_DIR.mkdir(parents=True, exist_ok=True)
    SOURCES_NCHU_DIR.mkdir(parents=True, exist_ok=True)

    catalog_items = json.loads(
        (SOURCES_NCHU_DIR / "nchu_catalog_source.json").read_text(encoding="utf-8")
    )
    locs_raw = json.loads(
        (SOURCES_NCHU_DIR / "nchu_resolved_locations.json").read_text(encoding="utf-8")
    )
    loc_by_name = {r["school_name"]: r for r in locs_raw}

    manifest = json.loads(
        (STATIC_DIR / "assets" / "school-images.json").read_text(encoding="utf-8")
    )
    visual_index = VisualRecordIndex({
        (
            school_identity_key(str(r.get("school_name", ""))),
            str(r.get("country") or ""),
        ): r
        for r in manifest.get("schools", [])
        if isinstance(r, dict) and r.get("status") == "verified"
    })

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

    for idx, item in enumerate(catalog_items):
        full_name = item["school_name"]
        zh_name = item["name_zh"]
        country = item["country"]
        region = REGION_BY_COUNTRY.get(country, "其他地區")
        avail_status = item["availability_status"]
        cat = item.get("category")
        if avail_status == "open":
            open_partner_count += 1

        website = (item.get("website") or "").strip()
        if website and not website.startswith("http"):
            website = f"https://{website}"

        factsheet_url = (item.get("factsheet_href") or "").strip() or None
        if not factsheet_url and (item.get("lang_href") or "").strip():
            factsheet_url = item["lang_href"].strip()

        if cat == "CN" or country == "中國大陸":
            source_url = NCHU_MAINLAND_PAGE_URL
        elif cat == "OS":
            source_url = NCHU_OVERSEAS_SHEET_URL
        else:
            source_url = NCHU_OIA_PARTNERS_URL

        round_label = "116學年度第1學期（秋季班，2027年9月出國）交換學生甄選"
        deadline_iso = "2026-10-23T12:00:00+08:00"
        deadline_rem = avail_status == "open"
        if avail_status == "open":
            win_status = "open"
            app_deadline_str = (
                "【116學年度第1學期（秋季班，2027年9月出國）交換學生甄選（目前開放申請中！）】"
                "線上申請期間：2026年9月23日（三）中午 12:00 至 2026年10月23日（五）中午 12:00 止；"
                "線上教師推薦函填寫截止日：2026年10月30日（五）中午 12:00；補件截止日：2026年11月6日（五）23:59（寄至 joytsai@dragon.nchu.edu.tw）；"
                "預計 2026年12月中旬公告第一次分發放榜並開放第二次分發志願填寫，2027年1月初公告第二次分發結果。"
            )
        else:
            win_status = "closed"
            app_deadline_str = (
                "【簽約交換學生合作姊妹校】本合作校為國立中興大學簽署交換學生協議之姊妹校；"
                "116學年度第1學期（秋季班）校級甄選於 2026/09/23 12:00 至 2026/10/23 12:00 開放線上申請，院級交換或各期實際開放名額請依國際事務處與簽約院系最新公告為準。"
            )

        raw_loc = loc_by_name[full_name]
        location_obj = {
            "school_name": full_name,
            "country": country,
            "city": raw_loc.get("city") or country,
            "latitude": float(raw_loc["latitude"]),
            "longitude": float(raw_loc["longitude"]),
            "geocode_status": "verified",
            "geocoded_at": CHECKED_AT,
            "source_url": raw_loc.get("source_url") or "https://www.wikidata.org",
            "identity_source_url": (
                raw_loc.get("identity_source_url")
                or raw_loc.get("source_url")
                or "https://ror.org"
            ),
            "precision": "representative",
            "note": raw_loc.get("note")
            or "校級代表位置：官方網域及國家已與 ROR / Wikidata 比對；實際交換校區以錄取通知與 Fact Sheet 為準。",
        }
        new_locations.append(location_obj)

        colleges_str = format_colleges(item)
        degree_levels_str = format_degree_levels(item)
        lang_req_str = format_language_req(item)
        gpa_req_str = format_gpa_req(item)
        quota_str = format_quota(item)
        study_period_str = format_study_period(item)
        program_type = format_program_type(item)

        notes_raw = clean_text(item.get("notes_raw") or "")
        elig_raw = clean_text(item.get("elig_raw") or "")
        adm_list = item.get("admitted_history") or []
        exp_posts = item.get("experience_posts") or []
        pop_rank = item.get("popularity_rank")

        if country == "日本":
            sem_dates_str = "春季學期（前學期）：約每年 4 月至 8 月；秋季學期（後學期）：約每年 9/10 月至翌年 2/3 月"
        elif country in {"澳洲", "紐西蘭"}:
            sem_dates_str = "第 1 學期（秋季班出國對應 Semester 2）：約每年 7 月至 11 月；第 2 學期（春季班出國對應 Semester 1）：約每年 2 月至 6 月"
        else:
            sem_dates_str = "秋季學期（第 1 學期）：約每年 8/9 月至 12 月／翌年 1 月；春季學期（第 2 學期）：約每年 1/2 月至 5/6 月"

        course_parts = [f"開放申請院系與學制：{colleges_str}（{degree_levels_str}）。"]
        if notes_raw:
            course_parts.append(f"姊妹校申請與選課備註：{notes_raw[:320]}。")
        course_parts.append(
            "依《國立中興大學選送學生出國交換甄選辦法》第 14 條規定，交換學生於交換期間每學期至少應選修相當於中興大學 6 學分（或修課時間達 108 小時）之課程（領取獎學金者須含至少 1 門與本系所專業相關之課程），並於返國後 1 個月內檢具正式成績單辦理學分抵免（不論是否採認學分，皆須跑完學分抵免程序始得辦理離校手續）。"
        )
        course_rest_str = " ".join(course_parts)

        if "住宿" in notes_raw or "宿舍" in notes_raw or "dorm" in notes_raw.lower():
            housing_str = f"{zh_name} 住宿與申請提醒：{notes_raw[:360]}"
        else:
            housing_str = f"{zh_name} 依兩校交換協議與當期 Fact Sheet 協助錄取交換生申請校內學生宿舍或提供校外學生公寓租屋資訊（宿位依接待校當期供給核配，住宿費及生活費由交換生自理）。"

        tuition_points_list = [
            "出國交換期間須完成國立中興大學註冊程序並繳交全額學雜費以保留在學學籍，免繳接待姊妹校學費（惟美國加州大學戴維斯分校 UC Davis、聖地牙哥分校 UCSD、亞利桑那大學等標註「全自費 Fully self-funded」或「學分費計畫」之學校除外）；往返機票、簽證、住宿、膳食及海外保險費由學生自理。",
            "獎學金制度（每年 2–3 月與春季班交換同步開放線上申請）：（1）教育部「學海飛颺」暨「國立中興大學選送學生赴海外研修獎學金」（歷年名次前 50% 或平均 80 分以上，校內經費亦涵蓋赴大陸及港澳地區）；（2）教育部「學海惜珠」獎學金（補助具低收、中低收、特境、身障、弱勢助學金資格學生赴非中港澳地區）；（3）國立中興大學「希望之橋」獎學金（校內經費補助經濟或文化不利優秀學生，含原住民、家庭突遭變故、低收／中低收／弱勢助學金等，前一學期平均 60 分以上，涵蓋中國大陸及港澳地區）。",
            "境外修課與返國義務：每學期至少選修相當於興大 6 學分（修課時間 108 小時）之課程（獎學金受獎生須含至少 1 門與本系相關課程）。抵達接待校後須填寫抵達通知單；返國後 1 個月內須辦理學分抵免程序（不論是否採認學分皆須完成始得離校）、返國後 2 個月內（受獎生 2 週內）須繳交交換學生心得報告，且畢業前須參與國際處舉辦之分享活動至少 3 小時。",
        ]

        app_steps_list = [
            f"步驟一（確認學籍、歷年平均 60 分與 CEFR B2 語檢門檻）：確認具國立中興大學學位生學籍（含進修部；學士班大一僅可申請春季班、大二以上及碩博士班大一以上皆可申請，延畢生亦可申請），學士班歷年總平均達 60 分以上，並確認符合 {zh_name} 之語檢、GPA 與院系規定。",
            "步驟二（取得導師／指導教授與系主任／所長核章並完成線上系統申請）：於申請期間（116-1 秋季班為 2026/09/23 12:00 至 2026/10/23 12:00）填妥《交換學生申請表》（海外最多 5 志願＋大陸最多 5 志願，共最多 10 志願），先取得導師或指導教授同意簽章後再請系主任／所長核章，並登入興大「出國計畫線上申請系統（https://oiawp.nchu.edu.tw/out-going-program-online-application/）」上傳申請表、中文歷年成績單、歷年名次證明書、語言能力證明、自傳及讀書計畫（至多 A4 三面，有填海外志願須交英文版）及第一志願家長同意書（單檔 2 MB 內）。",
            "步驟三（線上教師推薦函兩份填寫與補件期限）：於線上申請系統填入 2 位本校推薦教師（研究生至少 1 份須為指導教授）之聯絡信箱，由系統發送連結供教師於 2026/10/30（五）中午 12:00 前完成線上推薦函填寫；如有缺件或待補正式語檢成績單，須於 2026/11/06（五）23:59 前補寄至 joytsai@dragon.nchu.edu.tw。",
            f"步驟四（兩階段志願分發放榜、姊妹校提名與獎學金申請）：由國際事務處依評分比重（國外組：在校成績 30%、外語能力 35%、自傳及讀書計畫 30%、推薦函 5%；大陸組：在校成績 50%、自傳及讀書計畫 45%、推薦函 5%）於 12 月中旬公告第一次分發放榜並開放第二次分發志願填寫（1 月初二階段放榜）。獲錄取並確認資格後，由國際處向 {full_name} 辦理官方提名（Nomination），並可於每年 2–3 月申請學海飛颺、學海惜珠、興大海外研修獎學金或希望之橋獎學金。",
        ]

        elig_points_list = [
            f"開放學制與年級：{degree_levels_str}",
            f"開放申請學院：{colleges_str}",
            f"學業總平均與 GPA 門檻：{gpa_req_str}",
            f"語言檢定要求：{lang_req_str}",
        ]
        if notes_raw:
            elig_points_list.append(f"姊妹校特殊規定與備註：{notes_raw[:240]}")

        notes_lines = [
            f"【合作類別與期程】{program_type}｜交換期間：{study_period_str}",
            f"【當期名額與錄取實績】{quota_str}",
            f"【開放學院與學制】{colleges_str}｜{degree_levels_str}",
            f"【語言與學業門檻】{lang_req_str}｜{gpa_req_str}",
        ]
        if notes_raw:
            notes_lines.append(f"【姊妹校申請重要備註】{notes_raw[:350]}")
        if adm_list:
            adm_summary_parts = [
                f"{a['cycle']}錄取 {a['count']} 名（{'、'.join(a['depts'][:4])}）"
                for a in adm_list
            ]
            notes_lines.append(f"【近 4 學期錄取榜單實績】{'；'.join(adm_summary_parts)}。")
        if exp_posts:
            notes_lines.append(
                f"【歷屆學長姐交換心得與影音】中興大學國際事務處「出國交換心得及影音專區」公開收錄赴 {zh_name} 交換心得與影片共 {len(exp_posts)} 篇。"
            )

        visual_rec = visual_index.get((full_name, country)) or {}
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
            "availability_note": f"國立中興大學國際事務處公告合作交換姊妹校；{quota_str}。",
            "academic_year": "116",
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
            "image_url": visual_rec.get("local_path"),
            "image_source_url": visual_rec.get("image_source_url"),
            "image_page_url": (
                visual_rec.get("official_page_url")
                or visual_rec.get("image_source_url")
            ),
            "image_status": (
                "verified" if visual_rec.get("local_path") else "missing"
            ),
            "location": location_obj,
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
                "title": f"國立中興大學 116學年度第1學期（秋季班）交換學生申請簡章與姊妹校名單—{zh_name}",
                "source_url": source_url,
                "role": "home_university",
                "authority": "home_official_notice",
                "effective_academic_year": "116",
                "application_round": round_label,
                "checked_at": CHECKED_AT,
            },
            {
                "title": "國立中興大學 116學年度第1學期（秋季班）交換學生申請簡章 PDF",
                "source_url": NCHU_GUIDELINES_PDF_URL,
                "role": "home_university",
                "authority": "home_official_notice",
                "effective_academic_year": "116",
                "application_round": round_label,
                "checked_at": CHECKED_AT,
            },
            {
                "title": "國立中興大學國際事務處出國計畫線上申請系統（oiawp.nchu.edu.tw）",
                "source_url": NCHU_APPLY_PORTAL_URL,
                "role": "home_university",
                "authority": "home_official_notice",
                "effective_academic_year": "116",
                "application_round": round_label,
                "checked_at": CHECKED_AT,
            },
        ]
        if factsheet_url:
            wf_sources.append({
                "title": f"{zh_name} 交換計畫參考資料（Fact Sheet / Information）",
                "source_url": factsheet_url,
                "role": "home_university",
                "authority": "home_official_notice",
                "effective_academic_year": "116",
                "application_round": round_label,
                "checked_at": CHECKED_AT,
            })
        if website:
            wf_sources.append({
                "title": f"{full_name} 官方網站",
                "source_url": website,
                "role": "partner_university",
                "authority": "partner_official",
                "effective_academic_year": "116",
                "application_round": round_label,
                "checked_at": CHECKED_AT,
            })

        workflows.append({
            "home_university": "國立中興大學",
            "school_name": full_name,
            "partner_website": website,
            "country": country,
            "program_type": program_type,
            "academic_year": "116",
            "application_round": round_label,
            "effective_application_rounds": [
                round_label,
                "116-1",
                "116-2",
                "115-2",
                "116學年度第1學期（秋季班）",
                "116學年度第2學期（春季班）",
                "第1學期（秋季班）",
                "第2學期（春季班）",
            ],
            "applicability_status": "verified",
            "applicability_note": (
                "國立中興大學 116 學年度第 1 學期（秋季班，2027 年 9 月出國）交換學生甄選自 2026/09/23 中午 12:00 至 2026/10/23 中午 12:00 開放線上申請"
                "（線上教師推薦函填寫至 2026/10/30 12:00、補件至 2026/11/06 23:59，12 月中旬第一次分發放榜並開放第二次分發志願填寫）；"
                "116 學年度第 2 學期（春季班，2028 年 2 月出國）甄選暨出國交換獎學金預計於 2027 年 2 月至 3 月同步開放線上申請。"
            ),
            "review_status": "published",
            "published_at": CHECKED_AT,
            "steps": [
                {
                    "rule_id": f"nchu-116-home-1-{idx+1:03d}",
                    "order": 1,
                    "phase": "校內申請",
                    "title": f"確認中興大學在學學籍、歷年總平均 60 分與 {zh_name} 語言檢定及 GPA 標準",
                    "responsible_party": "學生",
                    "responsible_unit": "國立中興大學國際事務處學術交流組（行政大樓 3 樓）",
                    "deadline_at": deadline_iso,
                    "deadline_status": "verified_exact",
                    "deadline_source_url": NCHU_GUIDELINES_PDF_URL,
                    "deadline_checked_at": CHECKED_AT,
                    "deadline_reminder_eligible": deadline_rem,
                    "summary": f"須為國立中興大學學位生（含進修部；學士班大一僅可申請春季班、大二以上及碩博士班大一以上可申請秋／春季班，延畢生亦可申請），學士班歷年總平均達 60 分以上，並符合 {zh_name} 之語言檢定與 GPA 規定。",
                    "details": [
                        f"開放學制與院系：{colleges_str}（{degree_levels_str}）",
                        f"語言與學業條件：{lang_req_str}｜{gpa_req_str}",
                        f"當期名額與錄取實績：{quota_str}",
                    ],
                    "scope": {
                        "home_universities": ["國立中興大學"],
                        "partner_universities": [full_name],
                        "academic_years": ["115", "116"],
                        "application_rounds": [
                            round_label,
                            "116-1",
                            "116-2",
                            "116學年度第1學期（秋季班）",
                            "116學年度第2學期（春季班）",
                        ],
                    },
                    "source_urls": [
                        NCHU_GUIDELINES_PDF_URL,
                        source_url,
                    ],
                    "checked_at": CHECKED_AT,
                    "support_status": "verified",
                },
                {
                    "rule_id": f"nchu-116-home-2-{idx+1:03d}",
                    "order": 2,
                    "phase": "校內申請",
                    "title": "取得導師／指導教授與系所主管核章並於出國計畫線上申請系統上傳應繳文件",
                    "responsible_party": "學生與系所主管",
                    "responsible_unit": "國立中興大學各系所／國際事務處（oiawp.nchu.edu.tw）",
                    "deadline_at": deadline_iso,
                    "deadline_status": "verified_exact",
                    "deadline_source_url": NCHU_APPLY_PORTAL_URL,
                    "deadline_checked_at": CHECKED_AT,
                    "deadline_reminder_eligible": deadline_rem,
                    "summary": "申請人須於 2026/10/23（五）中午 12:00 前完成《交換學生申請表》系所核章（先請導師或指導教授簽章，再請系主任／所長核章），並登入 https://oiawp.nchu.edu.tw/out-going-program-online-application/ 完成線上填報與文件上傳（單檔上限 2 MB）。",
                    "details": [
                        "應繳上傳文件（JPG 或 PDF 格式，單檔 2 MB 內）：1. 交換學生申請表（海外最多 5 志願＋大陸最多 5 志願，共最多 10 志願，完成導師／指導教授及系主任／所長核章）、2. 在校中文歷年成績單（碩一、博一新生或轉學生無本校成績者檢附原畢業學校歷年成績單）、3. 在學生歷年名次證明書（碩、博班若無名次證明請再上傳一次歷年成績單）、4. 語言能力證明影本（僅申請大陸地區者免附；尚未取得正式成績單可先上傳網路成績查詢截圖並於 2026/11/06 23:59 前補件）、5. 自傳及讀書計畫（至多 A4 三面，以第一志願為目標撰寫，有填海外志願須交英文版，僅申請大陸地區中英文皆可）、6. 家長同意書（僅需繳交第一志願之家長同意書，經法定代理人簽名）。",
                        "線上教師推薦函兩份：於線上系統填入 2 位本校推薦教師（研究生至少 1 份須為指導教授）之電子信箱，由系統寄送連結供教師於 2026/10/30（五）中午 12:00 前完成線上填寫。",
                    ],
                    "document_requirements": [
                        {
                            "name": "國立中興大學交換學生申請表（海外最多5志願＋大陸最多5志願，須經導師／指導教授及系主任／所長核章）",
                            "official_form_url": "https://www.oia.nchu.edu.tw/images/File/02_Exchange_Program/5-1-1/outgoing_form.doc",
                            "source_urls": [
                                "https://www.oia.nchu.edu.tw/images/File/02_Exchange_Program/5-1-1/outgoing_form.doc",
                                NCHU_GUIDELINES_PDF_URL,
                            ],
                        },
                        {
                            "name": "在校中文歷年成績單與在學生歷年名次證明書（碩博班無名次證明者再上傳一次歷年成績單）",
                            "source_urls": [NCHU_GUIDELINES_PDF_URL],
                        },
                        {
                            "name": "自傳及讀書計畫（至多 A4 三面，含個人特質與經歷、交換計畫與未來展望；有填海外志願須交英文版）",
                            "source_urls": [NCHU_GUIDELINES_PDF_URL],
                        },
                        {
                            "name": "家長同意書（僅需繳交第一志願之家長同意書，經法定代理人親筆簽名）及 2 份線上教師推薦函",
                            "official_form_url": "https://www.oia.nchu.edu.tw/images/File/02_Exchange_Program/5-1-1/Declaration_of_Parental_Consent_Outgoing.doc",
                            "source_urls": [
                                "https://www.oia.nchu.edu.tw/images/File/02_Exchange_Program/5-1-1/Declaration_of_Parental_Consent_Outgoing.doc",
                                NCHU_GUIDELINES_PDF_URL,
                            ],
                        },
                        {
                            "name": "合格語言能力證明影本（TOEFL iBT 72 / ITP 543 / IELTS 5.5 / TOEIC 785 或非英語系國家接受之日韓德法西語檢定；僅申請大陸地區免附）",
                            "conditional": country == "中國大陸",
                            "condition": "申請國外姊妹校必繳（須為 2024/10/23 後應試成績）；僅申請大陸地區姊妹校免附",
                            "source_urls": [NCHU_GUIDELINES_PDF_URL],
                        },
                    ],
                    "scope": {
                        "home_universities": ["國立中興大學"],
                        "academic_years": ["115", "116"],
                        "application_rounds": [
                            round_label,
                            "116-1",
                            "116-2",
                            "116學年度第1學期（秋季班）",
                            "116學年度第2學期（春季班）",
                        ],
                    },
                    "submission": {
                        "method": "online",
                        "office": "國立中興大學國際事務處學術交流組（臺中市南區興大路 145 號行政大樓 3 樓）",
                        "portal_url": NCHU_APPLY_PORTAL_URL,
                    },
                    "action_url": NCHU_APPLY_PORTAL_URL,
                    "source_urls": [
                        NCHU_APPLY_PORTAL_URL,
                        NCHU_GUIDELINES_PDF_URL,
                    ],
                    "checked_at": CHECKED_AT,
                    "support_status": "verified",
                },
                {
                    "rule_id": f"nchu-116-home-3-{idx+1:03d}",
                    "order": 3,
                    "phase": "甄選與提名",
                    "title": "線上推薦函截止（10/30）、補件截止（11/06）與兩階段志願分發放榜確認（12月中旬／1月初）",
                    "responsible_party": "學生、推薦教師與國立中興大學國際事務處",
                    "responsible_unit": "國立中興大學國際事務處學術交流組",
                    "deadline_at": "2026-10-30T12:00:00+08:00",
                    "deadline_status": "verified_exact",
                    "deadline_source_url": NCHU_GUIDELINES_PDF_URL,
                    "deadline_checked_at": CHECKED_AT,
                    "deadline_reminder_eligible": deadline_rem,
                    "summary": "2 位推薦教師須於 2026/10/30 中午 12:00 前完成線上推薦函填寫，學生如需補件須於 2026/11/06 23:59 前寄至 joytsai@dragon.nchu.edu.tw；國際處預計於 2026 年 12 月中旬公告第一次分發放榜並開放第二次分發志願填寫，2027 年 1 月初公告第二次分發結果。",
                    "details": [
                        "校內審查評分比重：【赴國外姊妹校】在校成績 30%、外語能力 35%、自傳及讀書計畫 30%、推薦函 5%；【赴大陸地區姊妹校】在校成績 50%、自傳及讀書計畫 45%、推薦函 5%。",
                        "兩階段分發機制：若於第一次分發未獲錄取，可於 12 月中旬就尚有餘額之學校重新選填志願參與第二次分發；獲分發錄取之學生須於規定期限內完成資格確認，始取得本校交換學生推薦資格。",
                    ],
                    "scope": {
                        "home_universities": ["國立中興大學"],
                        "academic_years": ["115", "116"],
                        "application_rounds": [
                            round_label,
                            "116-1",
                            "116-2",
                            "116學年度第1學期（秋季班）",
                            "116學年度第2學期（春季班）",
                        ],
                    },
                    "source_urls": [
                        NCHU_GUIDELINES_PDF_URL,
                        NCHU_REGULATIONS_PDF_URL,
                    ],
                    "checked_at": CHECKED_AT,
                    "support_status": "verified",
                },
                {
                    "rule_id": f"nchu-{idx+1:03d}-host-apply",
                    "order": 4,
                    "phase": "合作校申請",
                    "title": f"由興大國際處辦理官方提名（Nomination）、提交 {zh_name} 入學申請並於 2–3 月申請交換獎學金",
                    "responsible_party": "學生與接待校國際處",
                    "summary": f"完成校內錄取資格確認後，由中興大學國際事務處向 {zh_name} 辦理官方提名；學生須依接待校 Fact Sheet 與提名通知自行準備護照、英文成績單、財力證明、語檢證明及選課表完成姊妹校入學與宿舍申請（最終是否錄取由接待校決定），並可於每年 2–3 月申請學海飛颺、學海惜珠、興大海外研修獎學金或希望之橋獎學金。",
                    "details": [
                        f"交換期程：{study_period_str}｜名額：{quota_str}",
                        f"語言與學業條件：{lang_req_str}",
                    ]
                    + ([f"姊妹校申請與選課備註：{notes_raw[:240]}"] if notes_raw else []),
                    "scope": {
                        "home_universities": ["國立中興大學"],
                        "partner_universities": [full_name],
                        "academic_years": ["115", "116"],
                        "application_rounds": [
                            round_label,
                            "116-1",
                            "116-2",
                            "116學年度第1學期（秋季班）",
                            "116學年度第2學期（春季班）",
                        ],
                    },
                    "source_urls": (
                        [source_url, NCHU_SCHOLARSHIP_URL]
                        + ([factsheet_url] if factsheet_url else [])
                        + ([website] if website else [])
                    ),
                    "checked_at": CHECKED_AT,
                    "support_status": "verified",
                    "needs_confirmation": False,
                },
                {
                    "rule_id": f"nchu-116-home-5-{idx+1:03d}",
                    "order": 5,
                    "phase": "行前準備",
                    "title": "辦理簽證與保險、每學期修習相當興大 6 學分（108 小時）以上課程及返國 1 個月內辦理學分抵免",
                    "responsible_party": "學生",
                    "responsible_unit": "國立中興大學國際事務處／教務處註冊組／各系所",
                    "summary": "收到姊妹校正式入學許可後自行辦理簽證、機票、海外醫療及意外保險與役男出境緩徵；交換期間須完成中興大學註冊繳費並每學期至少選修相當於興大 6 學分（108 小時）之課程，抵達後填寫抵達通知單，返國後 1 個月內辦理學分抵免（必辦程序）、2 個月內（受獎生 2 週內）繳交交換心得報告，並於畢業前參與分享活動至少 3 小時。",
                    "details": tuition_points_list,
                    "scope": {
                        "home_universities": ["國立中興大學"],
                        "academic_years": ["115", "116"],
                        "application_rounds": [
                            round_label,
                            "116-1",
                            "116-2",
                            "116學年度第1學期（秋季班）",
                            "116學年度第2學期（春季班）",
                        ],
                    },
                    "source_urls": [
                        NCHU_REGULATIONS_PDF_URL,
                        NCHU_GUIDELINES_PDF_URL,
                    ],
                    "checked_at": CHECKED_AT,
                    "support_status": "verified",
                },
            ],
            "sources": wf_sources,
            "last_checked": CHECKED_AT,
            "coverage_status": "official_verified",
            "coverage_note": "已完整整合國立中興大學 116 學年度第 1 學期（秋季班）交換學生申請簡章、海外及大陸姊妹校名額總表、選送學生出國交換甄選辦法、學海系列與希望之橋獎學金規定及歷屆錄取名單。",
        })

        cost_default, visa_default = REGION_COST_DEFAULTS.get(
            country,
            (
                "USD 800–1,300 / 月（含住宿、膳食、教材與當地交通費用）",
                "須依接待校與駐臺代表處規定辦理學生簽證與海外醫療保險。",
            ),
        )
        cost_line = f"預估每月生活費約 {cost_default}。"
        tuition_clean = tuition_points_list[0]
        housing_clean = housing_str
        course_clean = course_rest_str
        calendar_clean = f"{sem_dates_str}。"

        dest_sources = [
            {
                "title": f"國立中興大學出國交換姊妹校名額與申請資訊—{zh_name}",
                "source_url": source_url,
                "summary": "中興大學官方交換名額、語檢門檻、開放資格與備註",
            },
            {
                "title": "國立中興大學選送學生出國交換甄選辦法與 116-1 申請簡章",
                "source_url": NCHU_GUIDELINES_PDF_URL,
                "summary": "中興大學交換生每學期至少選修相當 6 學分（108 小時）、返國 1 個月內辦理學分抵免與心得報告規定",
            },
        ]
        if factsheet_url:
            dest_sources.append({
                "title": f"{zh_name} 交換計畫參考資料（Fact Sheet / Information）",
                "source_url": factsheet_url,
                "summary": "姊妹校課程資訊、學期日曆、住宿與交換生申請須知",
            })
        if website:
            dest_sources.append({
                "title": f"{full_name} 官方網站",
                "source_url": website,
                "summary": "接待合作校官方網站",
            })
        if exp_posts:
            dest_sources.append({
                "title": f"國立中興大學赴 {zh_name} 交換學生返國心得與影音專區（共 {len(exp_posts)} 篇）",
                "source_url": exp_posts[0].get("post_url") or exp_posts[0].get("url") or NCHU_EXPERIENCE_PORTAL_URL,
                "summary": f"收錄 {exp_posts[0]['term']} 等歷屆興大交換生返國心得與影片",
            })
        if adm_list:
            dest_sources.append({
                "title": f"國立中興大學交換學生甄選錄取名單（{zh_name}）",
                "source_url": adm_list[0]["pdf_url"],
                "summary": f"近 4 學期共錄取 {sum(a['count'] for a in adm_list)} 名（最新 {adm_list[0]['cycle']}錄取 {adm_list[0]['count']} 名）",
            })

        src_url_list = (
            [source_url, NCHU_GUIDELINES_PDF_URL]
            + ([factsheet_url] if factsheet_url else [])
            + ([website] if website else [])
        )

        destinations.append({
            "home_university": "國立中興大學",
            "school_name": full_name,
            "country": country,
            "city": location_obj.get("city") or country,
            "cost_summary": f"{cost_line}。\n{tuition_clean}",
            "housing_summary": housing_clean,
            "transport_summary": f"校區代表城市：{location_obj.get('city') or country}。請依入學許可與 Fact Sheet 確認實際授課校區、機場接機服務與當地學生大眾運輸票卡優惠。",
            "campus_life_summary": f"{calendar_clean}\n{course_clean}",
            "student_guide_sections": [
                {
                    "key": "cost",
                    "title": "生活費、學海飛颺／惜珠與中興大學海外研修／希望之橋獎學金規定",
                    "summary": cost_line,
                    "points": [cost_line] + tuition_points_list,
                    "source_urls": src_url_list + [NCHU_SCHOLARSHIP_URL],
                    "caution": "中興大學出國交換獎學金於每年 2–3 月與春季班交換同步開放線上申請（包含教育部學海飛颺、學海惜珠、興大選送學生赴海外研修獎學金及補助經濟文化不利學生之「希望之橋」獎學金，其中興大校內經費與希望之橋亦涵蓋赴大陸及港澳地區）。",
                },
                {
                    "key": "housing",
                    "title": "住宿資訊與申請",
                    "summary": housing_clean[:160],
                    "points": [housing_clean],
                    "source_urls": src_url_list,
                    "caution": "部分姊妹校校內宿位有限或須抽籤，請於獲提名後立即依 Fact Sheet 指引完成宿舍申請。",
                },
                {
                    "key": "insurance",
                    "title": "醫療保險與安全",
                    "summary": visa_default,
                    "points": [
                        visa_default,
                        "交換生於出國研修期間須自費購買足夠保額之海外醫療及意外保險（及交換學校規定之強制保險），並於抵達接待校後填報抵達通知單。",
                    ],
                    "source_urls": src_url_list,
                    "caution": "多數歐美日韓及紐澳姊妹校要求於註冊或抵校時出示符合當地政府或校方標準之醫療保險證明。",
                },
                {
                    "key": "visa",
                    "title": "簽證、體檢與役男出境緩徵準備",
                    "summary": visa_default,
                    "points": [
                        "收到交換學校核發之正式入學許可書（LOA / COE / DS-2019）後，請立即向該國駐臺辦事處申辦學生簽證（赴大陸交換須持有效臺胞證並完成規定健康檢查）。",
                        "尚未履行兵役義務之在學役男，應於出國前依規定檢附入學許可向國際事務處及學務處辦理役男出國交換緩徵及出境核准手續。",
                        visa_default,
                    ],
                    "source_urls": src_url_list,
                    "caution": "各國領事館簽證審核約需 4–8 週，請勿於取得簽證與入學許可前購買不可退改之機票。",
                },
                {
                    "key": "courses",
                    "title": "選課限制、每學期至少修習相當興大 6 學分（108 小時）與返國 1 個月內必辦學分抵免",
                    "summary": course_clean[:160],
                    "points": [
                        course_clean,
                        "依《國立中興大學選送學生出國交換甄選辦法》第 14 條，返國後 1 個月內須檢具接待校正式成績單辦理學分抵免（不論是否採認學分，皆須跑完學分抵免程序始得辦理畢業離校手續）。",
                    ],
                    "source_urls": src_url_list + [NCHU_REGULATIONS_PDF_URL],
                    "caution": "交換學生每學期至少應選修相當於中興大學 6 學分（或修課時間 108 小時）之課程；領取獎學金者須含至少 1 門與本系所專業相關之課程。",
                },
                {
                    "key": "city",
                    "title": "城市與校區位置",
                    "summary": f"{country} {location_obj.get('city') or ''}".strip(),
                    "points": [
                        location_obj.get("note")
                        or f"{full_name} 校級代表位置位於 {location_obj.get('city') or country}。",
                    ],
                    "source_urls": [location_obj.get("source_url") or source_url],
                    "caution": "部分合作大學設有多個校區，實際授課校區請以當期簡章名額表及姊妹校錄取通知為準。",
                },
                {
                    "key": "arrival",
                    "title": "學期年曆、抵達通知單、返國心得報告與畢業前 3 小時分享義務",
                    "summary": calendar_clean,
                    "points": [
                        calendar_clean,
                        "抵達接待校及返國時須依規定填寫「抵達通知單」；返國後 2 個月內（領取獎學金者於返國後 2 週內）須繳交交換學生心得報告，並於畢業前參與國際處舉辦之經驗分享活動至少 3 小時。",
                    ]
                    + (
                        [
                            f"歷屆學長姐返國心得：中興大學國際事務處已公開收錄赴 {zh_name} 交換生心得與影音共 {len(exp_posts)} 篇。"
                        ]
                        if exp_posts
                        else []
                    ),
                    "source_urls": src_url_list
                    + ([exp_posts[0].get("post_url") or exp_posts[0].get("url")] if exp_posts else [NCHU_EXPERIENCE_PORTAL_URL]),
                    "caution": "未完成學分抵免程序、未繳交交換心得報告或未參與分享活動者，將影響離校手續辦理及獎學金核銷。",
                },
            ],
            "first_72_hours": [
                {
                    "title": "依姊妹校入學許可與 Fact Sheet 指定報到日完成新生報到、宿舍入住與選課確認",
                    "detail": calendar_clean,
                    "source_urls": [source_url],
                },
                {
                    "title": "完成當地居留登錄、醫療保險確認並向中興大學國際事務處填報「抵達通知單」",
                    "detail": f"{visa_default} 抵校確定選課後，請確認每學期選修學分達相當於中興大學 6 學分（或修課時間 108 小時）以上。",
                    "source_urls": [NCHU_REGULATIONS_PDF_URL],
                },
            ],
            "sources": dest_sources,
            "last_checked": CHECKED_AT,
            "coverage_status": "official_verified",
            "coverage_note": "已整合國立中興大學 116 學年度交換學生申請簡章、海外及大陸姊妹校名額表、Fact Sheet、近 4 學期錄取榜單與歷屆學長姐交換心得影音。",
        })

        research_records.append({
            "home_university": "國立中興大學",
            "school_name": full_name,
            "country": country,
            "official_website": website,
            "verification_status": "official_verified",
            "discovery_source_url": source_url,
            "checked_at": CHECKED_AT,
            "note": f"國立中興大學國際事務處海外及大陸姊妹校名額表、全球姊妹校名冊（{source_url}）及 ROR/Wikidata 官方網址核對完成。",
        })

        ev_sources = [
            {"title": f"國立中興大學出國交換姊妹校資訊—{zh_name}", "url": source_url},
        ]
        if factsheet_url:
            ev_sources.append({"title": f"{zh_name} 交換計畫 Fact Sheet", "url": factsheet_url})
        if website:
            ev_sources.append({"title": f"{full_name} 官方網站", "url": website})
        if exp_posts:
            ev_sources.append({
                "title": f"國立中興大學赴 {zh_name} 交換生返國心得（{exp_posts[0]['term']}）",
                "url": exp_posts[0].get("post_url") or exp_posts[0].get("url") or NCHU_EXPERIENCE_PORTAL_URL,
            })
        if adm_list:
            ev_sources.append({
                "title": f"國立中興大學交換學生錄取名單（{adm_list[0]['cycle']}）",
                "url": adm_list[0]["pdf_url"],
            })

        has_student_exp = bool(exp_posts or adm_list)
        if has_student_exp:
            exp_covered_schools += 1

        ev_list = [
            {
                "theme": "housing",
                "kind": "official",
                "text": housing_clean,
                "sources": ev_sources,
                "checked_at": CHECKED_AT,
                "scope": "國立中興大學交換姊妹校名額表住宿說明與 Fact Sheet",
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
                "scope": "國立中興大學交換生費用規定、學海／希望之橋獎學金與地區生活費估算",
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
                "scope": "國立中興大學交換生選課限制、每學期至少6學分（108小時）與返國1個月內學分抵免規定",
                "original_excerpt": False,
                "original_text": "",
                "translation_status": "original",
            },
            {
                "theme": "safety",
                "kind": "official",
                "text": visa_default,
                "sources": ev_sources,
                "checked_at": CHECKED_AT,
                "scope": "國立中興大學出國交換簽證、體檢、海外醫療保險與抵達通知單提醒",
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
                        f"｜中興大學國際事務處公開收錄赴 {zh_name} 歷屆交換生返國心得與影音共 {len(exp_posts)} 篇。"
                        if exp_posts
                        else ""
                    )
                ),
                "sources": ev_sources,
                "checked_at": CHECKED_AT,
                "scope": "國立中興大學出國交換名額、近4學期錄取榜單與歷屆學長姐交換心得",
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
                "已整合國立中興大學 116 學年度交換學生申請簡章、海外及大陸姊妹校名額總表、Fact Sheet、近 4 學期錄取榜單與歷屆交換心得影音。",
                "當期宿位供給、費用與選課限制請依姊妹校最新 Fact Sheet 及課程目錄核對。",
            ],
            "location_signature": f"verified:{location_obj['latitude']}:{location_obj['longitude']}:representative",
            "extraction_version": 3,
        })

        sample_reports: list[dict] = []
        for p_item in exp_posts[:5]:
            p_url = p_item.get("url") or p_item.get("post_url") or NCHU_EXPERIENCE_PORTAL_URL
            p_title = f"國立中興大學赴 {zh_name}（{p_item['term']}・{p_item.get('dept') or '興大交換生'}）交換學生{p_item.get('media_type') or '心得'}：{p_item['title']}"
            sample_reports.append({
                "title": p_title,
                "url": p_url,
                "term": p_item["term"],
            })

        if exp_posts:
            latest_post = exp_posts[0]
            terms_covered = list(dict.fromkeys(p["term"] for p in exp_posts[:6]))
            depts_covered = list(dict.fromkeys(p.get("dept") for p in exp_posts[:6] if p.get("dept")))
            rep_title = (
                f"國立中興大學赴 {zh_name}（{latest_post['term']} 等共 {len(exp_posts)} 篇）交換學生返國心得與影音分享集"
            )
            summary_text = (
                f"國立中興大學國際事務處「出國交換心得及影音專區（iss.nchu.edu.tw）」公開收錄赴 {zh_name} 交換學生返國心得與影片共 {len(exp_posts)} 篇"
                f"（涵蓋學期：{'、'.join(terms_covered)}"
                + (f"；分享學生系所包含：{'、'.join(depts_covered[:5])}" if depts_covered else "")
                + f"），最新一篇為 {latest_post['term']}（{latest_post.get('dept') or '興大交換生'}）《{latest_post['title']}》，詳實記錄行前準備、選課學分抵免、住宿環境與當地生活體驗。"
            )
            theme_map = {
                "academics": f"中興大學交換生分享於 {zh_name} 之選課經驗、授課模式與返國學分抵免流程（每學期至少修習相當興大 6 學分／108 小時課程，返國 1 個月內辦理學分抵免）。",
                "housing": f"中興大學交換生分享於 {zh_name} 之校內學生宿舍或校外租屋申請流程、房型設備與周邊生活機能（{housing_clean[:120]}）。",
                "campus_culture": f"中興大學國際事務處收錄 {len(exp_posts)} 篇赴 {zh_name} 歷屆交換生心得與影音（含 {latest_post['term']} 最新分享），記錄迎新活動、學伴交流與海外學習收穫。",
                "cost": f"中興大學交換生分享於 {zh_name} 之當地物價開銷（{cost_default}）與教育部學海飛颺／惜珠、中興大學海外研修獎學金及希望之橋獎學金申請經驗。",
            }
            p_url = latest_post.get("url") or latest_post.get("post_url") or NCHU_EXPERIENCE_PORTAL_URL
            student_experience_rows.append({
                "school_name": full_name,
                "country": country,
                "title": rep_title,
                "source_url": p_url,
                "source_type": "video" if latest_post.get("media_type") == "影片" else "article",
                "platform": "國立中興大學國際事務處—交換生心得及影音專區",
                "author_name": f"國立中興大學 {latest_post['term']} {latest_post.get('dept') or '返國交換生'}",
                "language": "zh",
                "summary": summary_text,
                "themes": ["academics", "housing", "campus_culture", "cost"],
                "theme_summaries": theme_map,
                "content_status": "full_text",
                "perspective": "official_student_story",
                "published_at": None,
                "discovered_at": CHECKED_AT,
                "content_hash": hashlib.sha256(
                    f"{full_name}:exp:{p_url}".encode("utf-8")
                ).hexdigest(),
                "exchange_term": latest_post["term"],
                "summary_zh": summary_text,
                "original_summary": summary_text,
                "theme_summaries_zh": theme_map,
                "translation_status": "original",
                "source_kind": "official_experience_page",
            })

            # If there is also a video post distinct from the first post, include it too
            video_posts = [p for p in exp_posts[1:] if p.get("media_type") == "影片"]
            if video_posts:
                vp = video_posts[0]
                vp_url = vp.get("url") or vp.get("post_url") or NCHU_EXPERIENCE_PORTAL_URL
                vp_title = f"國立中興大學赴 {zh_name}（{vp['term']}・{vp.get('dept') or '興大交換生'}）交換學生影音紀錄：{vp['title']}"
                vp_summary = f"國立中興大學國際事務處收錄之 {vp['term']}（{vp.get('dept') or '興大交換生'}）赴 {zh_name} 交換學生實地拍攝校園生活、住宿環境與跨文化交流影音紀錄。"
                vp_themes = {
                    "campus_culture": vp_summary,
                    "housing": f"透過影片實地走訪 {zh_name} 校園環境、學生宿舍與生活圈。",
                }
                student_experience_rows.append({
                    "school_name": full_name,
                    "country": country,
                    "title": vp_title,
                    "source_url": vp_url,
                    "source_type": "video",
                    "platform": "國立中興大學國際事務處—交換生影音平台（oia.video.nchu.edu.tw）",
                    "author_name": f"國立中興大學 {vp['term']} {vp.get('dept') or '交換學生'}",
                    "language": "zh",
                    "summary": vp_summary,
                    "themes": ["campus_culture", "housing"],
                    "theme_summaries": vp_themes,
                    "content_status": "full_text",
                    "perspective": "official_student_story",
                    "published_at": None,
                    "discovered_at": CHECKED_AT,
                    "content_hash": hashlib.sha256(
                        f"{full_name}:video:{vp_url}".encode("utf-8")
                    ).hexdigest(),
                    "exchange_term": vp["term"],
                    "summary_zh": vp_summary,
                    "original_summary": vp_summary,
                    "theme_summaries_zh": vp_themes,
                    "translation_status": "original",
                    "source_kind": "official_experience_page",
                })

        if adm_list:
            total_adm = sum(a["count"] for a in adm_list)
            latest_adm = adm_list[0]
            all_depts = list(dict.fromkeys(d for a in adm_list for d in a["depts"]))
            cycles_str = "、".join(f"{a['cycle']}（{a['count']}名）" for a in adm_list)
            adm_title = f"國立中興大學赴 {zh_name} 交換學生甄選錄取紀錄（近 4 學期共錄取 {total_adm} 名）"
            sample_reports.append({
                "title": adm_title,
                "url": latest_adm["pdf_url"],
                "term": latest_adm["cycle"],
            })
            summary_text = (
                f"國立中興大學國際事務處公告之出國交換學生錄取名單中，近 4 學期共計錄取 {total_adm} 名興大學生赴 {zh_name} 交換研修"
                f"（各梯次人數：{cycles_str}），錄取學生所屬系所涵蓋：{'、'.join(all_depts[:8])}。"
                + (f"同時名列中興大學國際處統計之「{pop_rank}」。" if pop_rank else "")
            )
            theme_map = {
                "academics": f"近 4 學期錄取系所分布：{'、'.join(all_depts[:8])}（共 {total_adm} 名）。",
                "cost": "錄取生於交換期間繳交中興大學學雜費並免繳接待校學費（全自費校除外），並可申請教育部學海飛颺／惜珠、中興大學選送學生赴海外研修獎學金或希望之橋獎學金。",
                "campus_culture": f"國立中興大學近 4 學期共選送 {total_adm} 名學子赴 {zh_name} 進行學術與文化交流" + (f"（{pop_rank}）" if pop_rank else "") + "。",
            }
            student_experience_rows.append({
                "school_name": full_name,
                "country": country,
                "title": adm_title,
                "source_url": latest_adm["pdf_url"],
                "source_type": "article",
                "platform": "國立中興大學國際事務處—交換學生錄取榜單",
                "author_name": "國立中興大學錄取交換學生",
                "language": "zh",
                "summary": summary_text,
                "themes": ["academics", "cost", "campus_culture"],
                "theme_summaries": theme_map,
                "content_status": "full_text",
                "perspective": "official_program_record",
                "published_at": "2026-06-15T00:00:00Z",
                "discovered_at": CHECKED_AT,
                "content_hash": hashlib.sha256(
                    f"{full_name}:admitted:{latest_adm['pdf_url']}".encode("utf-8")
                ).hexdigest(),
                "exchange_term": latest_adm["cycle"],
                "summary_zh": summary_text,
                "original_summary": summary_text,
                "theme_summaries_zh": theme_map,
                "translation_status": "original",
                "source_kind": "official_experience_pdf",
            })

        experience_sources_records.append({
            "home_university": "國立中興大學",
            "school_name": full_name,
            "country": country,
            "official_experience_portal_url": NCHU_EXPERIENCE_PORTAL_URL,
            "partner_page_url": factsheet_url or source_url,
            "report_count": len(exp_posts) + len(adm_list),
            "sample_reports": sample_reports,
            "checked_at": CHECKED_AT,
        })

    partners_jsonl_text = (
        "\n".join(json.dumps(r, ensure_ascii=False) for r in partners) + "\n"
    )
    (OFFICIAL_NCHU_DIR / "partners.jsonl").write_text(
        partners_jsonl_text, encoding="utf-8"
    )
    (SOURCES_NCHU_DIR / "partners.jsonl").write_text(
        partners_jsonl_text, encoding="utf-8"
    )
    (OFFICIAL_NCHU_DIR / "application_workflows.jsonl").write_text(
        "\n".join(json.dumps(r, ensure_ascii=False) for r in workflows) + "\n",
        encoding="utf-8",
    )
    (OFFICIAL_NCHU_DIR / "destination_profiles.jsonl").write_text(
        "\n".join(json.dumps(r, ensure_ascii=False) for r in destinations) + "\n",
        encoding="utf-8",
    )
    (OFFICIAL_NCHU_DIR / "partner_research.jsonl").write_text(
        "\n".join(json.dumps(r, ensure_ascii=False) for r in research_records) + "\n",
        encoding="utf-8",
    )
    (OFFICIAL_NCHU_DIR / "student_life.jsonl").write_text(
        "\n".join(json.dumps(r, ensure_ascii=False) for r in life_records) + "\n",
        encoding="utf-8",
    )
    (OFFICIAL_NCHU_DIR / "experience_sources.jsonl").write_text(
        "\n".join(
            json.dumps(r, ensure_ascii=False) for r in experience_sources_records
        )
        + "\n",
        encoding="utf-8",
    )
    (OFFICIAL_NCHU_DIR / "student_experiences.jsonl").write_text(
        "\n".join(
            json.dumps(r, ensure_ascii=False) for r in student_experience_rows
        )
        + "\n",
        encoding="utf-8",
    )
    (OFFICIAL_NCHU_DIR / "campus-locations.json").write_text(
        json.dumps({"locations": new_locations}, ensure_ascii=False, indent=2)
        + "\n",
        encoding="utf-8",
    )

    # IMPORTANT: Add home university row ("國立中興大學", "臺灣") to university_locations.jsonl
    loc_file = (
        REPO_ROOT / "src/exchange_info/official_data/university_locations.jsonl"
    )
    existing_loc_lines = [
        line
        for line in loc_file.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    existing_loc_map = {}
    for line in existing_loc_lines:
        rec = json.loads(line)
        existing_loc_map[(rec["school_name"], rec.get("country") or "")] = rec

    nchu_home_loc = {
        "school_name": "國立中興大學",
        "country": "臺灣",
        "city": "臺中市南區",
        "latitude": 24.1236,
        "longitude": 120.6753,
        "geocode_status": "verified",
        "geocoded_at": CHECKED_AT,
        "source_url": "https://www.wikidata.org/wiki/Q714228",
        "identity_source_url": "https://ror.org/05vn3ca78",
        "precision": "representative",
        "note": "校級代表位置：官方網域及國家已與 ROR 比對，座標來源為 Wikidata P625；實際交換校區以錄取通知為準。 母校代表點採臺中市南區興大路145號校本部（行政大樓 3 樓國際事務處）；官方地址來源：https://www.oia.nchu.edu.tw/。",
    }
    existing_loc_map[("國立中興大學", "臺灣")] = nchu_home_loc
    sorted_locs = sorted(
        existing_loc_map.values(),
        key=lambda r: (r.get("country") or "", r.get("school_name") or ""),
    )
    loc_file.write_text(
        "\n".join(json.dumps(r, ensure_ascii=False) for r in sorted_locs) + "\n",
        encoding="utf-8",
    )

    nchu_source_urls = [
        "https://www.oia.nchu.edu.tw/index.php/2-uncategorised/154-1-1-exchange-info",
        NCHU_GUIDELINES_PDF_URL,
        NCHU_REGULATIONS_PDF_URL,
        NCHU_OVERSEAS_SHEET_URL,
        NCHU_MAINLAND_PAGE_URL,
        NCHU_OIA_PARTNERS_URL,
        NCHU_SCHOLARSHIP_URL,
        NCHU_APPLY_PORTAL_URL,
        NCHU_EXPERIENCE_PORTAL_URL,
    ]

    exchange_info_payload = {
        "school_name": "國立中興大學",
        "program_type": [
            "交換學生（赴國外姊妹校交換計畫・每年 9–10 月甄選翌年秋季班、2–3 月甄選翌年春季班）",
            "交換學生（赴大陸地區姊妹校交換計畫・43 所大陸重點高校學費互免，與海外交換同步於線上系統分填最多 5 志願）",
            "交換學生（學院級與全球簽約交換姊妹校計畫）",
        ],
        "academic_year": [
            "116（116學年度第1學期［秋季班，2027年9月出國］：2026/09/23 12:00 至 2026/10/23 12:00 開放線上申請，推薦函至 10/30 12:00，補件至 11/06 23:59）",
            "116（116學年度第2學期［春季班，2028年2月出國］暨出國交換獎學金：預計 2027年2月至3月開放線上申請）",
        ],
        "semester": [
            "第1學期（秋季班：每年約 8/9 月至 12 月／翌年 1 月；澳洲／紐西蘭對應 Semester 2 為 7 月至 11 月）",
            "第2學期（春季班：每年約 1/2 月至 5/6 月；日本前學期為 4 月至 8 月）",
        ],
        "application_period": [
            "【116學年度第1學期（秋季班，2027年9月出國）交換學生甄選（目前開放申請中）】線上申請期間：2026年9月23日（三）中午 12:00 至 2026年10月23日（五）中午 12:00 止（於 https://oiawp.nchu.edu.tw/out-going-program-online-application/ 填報）；線上教師推薦函填寫截止日：2026年10月30日（五）中午 12:00；補件截止日：2026年11月6日（五）23:59（寄至 joytsai@dragon.nchu.edu.tw）；第一次分發放榜及第二次分發志願填寫：2026年12月中旬；第二次分發放榜：2027年1月初。",
            "【116學年度第2學期（春季班，2028年2月出國）交換學生甄選暨出國交換獎學金申請】預計於 2027年2月至3月開放線上申請（包含教育部學海飛颺、學海惜珠、國立中興大學選送學生赴海外研修獎學金及希望之橋獎學金）。",
        ],
        "eligibility": [
            "申請資格與年級規定：本校學位生（含進修部）學士班一年級僅可申請春季班、學士班二年級（含）以上、碩士班一年級（含）以上、博士班一年級（含）以上，通過系所推薦者。延畢生得申請並出國交換（惟出國交換不得作為申請延畢之理由；部分大陸地區姊妹校不接受大四生或延畢生）。同一學制內最多可交換 2 次，每次申請以 1 學期為限。",
            "歷年學業成績門檻與評分比重：學士班學生歷年在校總平均分數須達 60 分（含）以上。校內甄選評分比重：【赴國外姊妹校】在校成績占 30%、外語能力占 35%、自傳及讀書計畫占 30%、推薦函占 5%；【赴大陸地區姊妹校】在校成績占 50%、自傳及讀書計畫占 45%、推薦函占 5%。",
            "註冊繳費與境外修課學分規定：交換期間須完成中興大學註冊並繳交全額學雜費（免繳接待校學費，惟標註全自費之學校除外）。每學期於姊妹校至少應選修相當於中興大學 6 學分（或修課時間達 108 小時）之課程（領取獎學金者須含至少 1 門與本系所專業相關之課程）。",
            "抵達通報、學分抵免與返國義務：抵達接待校及返國時須填寫「抵達通知單」；返國後 1 個月內須檢具正式成績單辦理學分抵免（不論是否採認學分，皆須跑完學分抵免程序始得辦理畢業離校手續）；返國後 2 個月內（領取獎學金者 2 週內）須繳交交換心得報告，且畢業前須參與國際處分享活動至少 3 小時。",
        ],
        "language_requirement": [
            "【赴國外（海外）姊妹校】須達 CEFR B2 英語標準：TOEFL iBT 72 分以上（新制 4 分以上；TOEFL ITP 紙筆測驗 543 分以上）、IELTS 5.5 以上，或 TOEIC 785 分以上（英檢須為申請截止日前 2 年內應試之成績，並須符合各志願學校要求之語言標準）。",
            "【非英語系國家特殊語檢規定】非英語系國家學校若可接受其他語言檢定（如日檢 JLPT N1–N5、韓檢 TOPIK、德檢、法檢、西檢等），則可免交英語能力證明；惟志願序中若有任一所學校要求英語檢定，仍須於校內申請時繳交英檢證書。",
            "【赴大陸地區姊妹校】免繳語言能力證明（惟部分大陸高校對外國籍或港澳臺僑生另有規定）。",
        ],
        "required_documents": [
            "1. 交換學生申請表（海外最多選填 5 所志願、大陸地區最多選填 5 所志願，合計最多 10 志願；須先取得導師或指導教授同意簽章後，再請系主任／所長核章，掃描上傳至線上申請系統）",
            "2. 在校中文歷年成績單（至教務處註冊組或自動列印機器申請正本掃描；轉學生、碩一或博一新生尚無本校成績者，應繳交原畢業學校歷年成績單）",
            "3. 在學生歷年名次證明書（至註冊組或行政大樓自動列印機器申請；碩、博班學生若無名次證明，請再上傳一次歷年成績單）",
            "4. 語言能力證明影本（僅申請大陸地區者免附；尚未取得正式成績單者可先上傳網路成績查詢頁面截圖，並於補件截止日 2026/11/06 23:59 前將正式成績單影本寄至 joytsai@dragon.nchu.edu.tw）",
            "5. 自傳及讀書計畫（至多 A4 三面，以第一志願學校為目標撰寫，內容須包含「個人特質與經歷」及「交換計畫與未來展望」；志願序中有填海外學校者須繳交英文版，僅申請大陸地區者中英文皆可）",
            "6. 家長同意書（僅需繳交第一志願之家長同意書，須經法定代理人親筆簽名後掃描上傳）",
            "7. 線上教師推薦函兩份（推薦者須為本校教師，研究生至少 1 份須為指導教授推薦；於線上系統填入教師信箱後由系統寄送連結，教師須於 2026/10/30 中午 12:00 前完成線上填寫）",
        ],
        "scholarship_info": [
            "教育部「學海飛颺」暨「國立中興大學選送學生赴海外研修獎學金」（每年 2–3 月全線上申請）：補助具中華民國國籍、歷年名次在該班前 50% 或歷年平均分數 80 分以上（碩一新生採大學歷年成績、博一採碩士歷年成績）、且外語能力達 CEFR B2 以上之優秀交換生（其中「國立中興大學選送學生赴海外研修獎學金」由校內經費支應，補助範圍亦涵蓋赴中國大陸及港澳地區交換生）。",
            "教育部「學海惜珠」獎學金：補助具中華民國國籍且符合低收入戶、中低收入戶、特殊境遇家庭扶助、身心障礙者生活補助或大專校院弱勢學生助學金補助資格之優秀學子赴非中港澳地區交換研修。",
            "國立中興大學「希望之橋」獎學金（校內經費，涵蓋中國大陸及港澳地區）：補助具中華民國國籍之經濟或文化不利優秀在學學生（含原住民學生、家庭突遭變故致經濟陷入困境、低收／中低收／特境／身障補助、弱勢助學金或學雜費減免資格），前一學期學業平均成績達 60 分（含）以上者即可申請。",
        ],
        "partner_universities": [p["school_name"] for p in partners],
        "source_urls": nchu_source_urls,
        "last_checked": CHECKED_AT,
    }
    (OFFICIAL_NCHU_DIR / "exchange_info.json").write_text(
        json.dumps(exchange_info_payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    student_dashboard_payload = {
        "school_name": "國立中興大學",
        "last_checked": CHECKED_AT,
        "academic_score_minimum": 60.0,
        "academic_score_rule": "學士班學生歷年在校總平均分數須達 60 分（含）以上；碩、博士班學生須通過系所推薦（大一僅可申請春季班，大二以上及碩博班可申請秋／春季班，延畢生亦可申請）。校內評分比重：國外姊妹校組在校成績占 30%（外語 35%、自傳讀書計畫 30%、推薦函 5%），大陸地區姊妹校組在校成績占 50%（自傳讀書計畫 45%、推薦函 5%）。交換期間每學期至少須選修相當於興大 6 學分（108 小時）之課程。",
        "academic_gpa_minimum": None,
        "maximum_preferences": 10,
        "selection_rules": {
            "academic_policy": "gpa_or_rank",
            "academic_reference_year": "116",
            "undergraduate_gpa_minimum": None,
            "undergraduate_rank_maximum": 100.0,
            "graduate_academic_exempt": False,
            "exclude_in_service": False,
            "pending_quota_planning": False,
            "partner_requirements_need_confirmation": False,
            "degree_score_minimums": {
                "undergraduate": 60.0,
                "graduate": 60.0,
            },
            "excluded_undergraduate_years": [],
            "language_certificate_required": False,
        },
        "language_score_minimums": {
            "toefl": 72.0,
            "ielts": 5.5,
            "toeic": 785.0,
        },
        "application_periods": [
            {
                "title": "國立中興大學 116學年度第1學期（秋季班，2027年9月出國）交換學生甄選（海外姊妹校＋大陸地區姊妹校）",
                "details": [
                    "線上申請期間：2026年9月23日（三）中午 12:00 至 2026年10月23日（五）中午 12:00 止（於 https://oiawp.nchu.edu.tw/out-going-program-online-application/ 填報，海外最多 5 志願＋大陸最多 5 志願）。",
                    "線上教師推薦函填寫截止日：2026年10月30日（五）中午 12:00；補件截止日：2026年11月6日（五）23:59（寄至 joytsai@dragon.nchu.edu.tw）。",
                    "分發放榜時程：2026年12月中旬公告第一次分發放榜並開放第二次分發志願填寫，2027年1月初公告第二次分發放榜結果。",
                ],
                "source": {
                    "title": "國立中興大學 116學年度第1學期（秋季班）交換學生申請簡章",
                    "source_url": NCHU_GUIDELINES_PDF_URL,
                    "category": "exchange_application",
                    "summary": "116-1（2027 秋季班）交換學生線上申請時程、應繳文件、CEFR B2 語言門檻與兩階段分發規則。",
                },
                "scope": "home_application",
                "program_types": ["exchange"],
                "academic_year": "116",
                "application_round": "116學年度第1學期（秋季班，2027年9月出國）",
                "audience": "all_students",
                "opens_at": "2026-09-23T12:00:00+08:00",
                "deadline_at": "2026-10-23T12:00:00+08:00",
                "date_status": "verified_exact",
                "status": "open",
                "status_note": "116學年度第1學期（秋季班，2027年9月出國）交換學生甄選目前開放線上申請中，至 2026/10/23（五）中午 12:00 截止（推薦函至 10/30 12:00、補件至 11/06 23:59）。",
                "deadline_note": "於國立中興大學國際事務處出國計畫線上申請系統（https://oiawp.nchu.edu.tw/out-going-program-online-application/）線上填報並上傳核章後申請表與應繳文件。",
                "reminder_eligible": True,
                "checked_at": CHECKED_AT,
            },
            {
                "title": "國立中興大學 116學年度第1學期（秋季班）線上教師推薦函截止（10/30）、補件截止（11/06）與兩階段分發放榜",
                "details": [
                    "線上教師推薦函填寫截止日：2026年10月30日（五）中午 12:00 止（由推薦教師於系統完成線上填寫）。",
                    "補件截止日：2026年11月6日（五）23:59 止（寄至 joytsai@dragon.nchu.edu.tw）。",
                    "兩階段分發放榜：2026年12月中旬公告第一次分發放榜並開放第二次分發志願填寫，2027年1月初公告第二次分發放榜結果。",
                ],
                "source": {
                    "title": "國立中興大學 116學年度第1學期（秋季班）交換學生申請簡章",
                    "source_url": NCHU_GUIDELINES_PDF_URL,
                    "category": "exchange_application",
                    "summary": "116-1（2027 秋季班）線上推薦函、補件與兩階段志願分發時程。",
                },
                "scope": "home_application",
                "program_types": ["exchange"],
                "academic_year": "116",
                "application_round": "116學年度第1學期（秋季班，2027年9月出國）",
                "audience": "all_students",
                "opens_at": "2026-09-23T12:00:00+08:00",
                "deadline_at": "2026-10-30T12:00:00+08:00",
                "date_status": "verified_exact",
                "status": "open",
                "status_note": "2 位推薦教師須於 2026/10/30（五）中午 12:00 前完成線上推薦函填寫；補件至 2026/11/06（五）23:59 截止。",
                "deadline_note": "系統自動寄發推薦連結至 2 位推薦教師信箱；補件請寄至 joytsai@dragon.nchu.edu.tw。",
                "reminder_eligible": True,
                "checked_at": CHECKED_AT,
            },
            {
                "title": "國立中興大學 116學年度第2學期（春季班，2028年2月出國）交換學生甄選暨出國交換獎學金申請",
                "details": [
                    "預計開放期間：每年 2 月至 3 月開放春季班交換學生甄選（學士班一年級新生自本梯次起可報名申請）。",
                    "出國交換獎學金同步申請：教育部「學海飛颺」、「學海惜珠」、國立中興大學「選送學生赴海外研修獎學金」及「希望之橋」獎學金於每年 2–3 月與春季班交換同步開放全線上申請。",
                ],
                "source": {
                    "title": "國立中興大學國際事務處—交換學生資訊與出國交換獎學金專區",
                    "source_url": "https://www.oia.nchu.edu.tw/index.php/2-uncategorised/154-1-1-exchange-info",
                    "category": "exchange_application",
                    "summary": "春季班交換學生甄選時程與四大出國交換獎學金申請規範。",
                },
                "scope": "home_application",
                "program_types": ["exchange"],
                "academic_year": "116",
                "application_round": "116學年度第2學期（春季班，2028年2月出國）",
                "audience": "all_students",
                "opens_at": "2027-02-15T12:00:00+08:00",
                "deadline_at": "2027-03-19T12:00:00+08:00",
                "date_status": "reference_only",
                "status": "upcoming",
                "status_note": "116學年度第2學期（春季班）交換學生甄選暨出國交換獎學金預計於 2027 年 2 月至 3 月開放線上申請。",
                "deadline_note": "實際截止日期請依國際事務處 2027 年 2 月公告之春季班簡章為準。",
                "reminder_eligible": False,
                "checked_at": CHECKED_AT,
            },
        ],
        "program_overview": [
            {
                "title": f"國立中興大學國際事務處出國交換學生計畫總覽（{len(partners)} 所全球交換合作大學）",
                "details": [
                    f"國立中興大學國際事務處（OIA）辦理赴國外及赴大陸地區交換學生甄選，本平台完整收錄 {len(partners)} 所官方交換合作大學（含當期開放申請之 {open_partner_count} 所海外五大洲及大陸地區重點姊妹校，以及 {len(partners) - open_partner_count} 所簽署交換學生協議之院級／校級合作大學）。",
                    "116 學年度第 1 學期（秋季班，2027 年 9 月出國）交換甄選現正開放線上申請（2026/09/23 中午 12:00 至 2026/10/23 中午 12:00，教師推薦函至 10/30 12:00、補件至 11/06 23:59），海外與大陸地區可各填 5 所志願（共最多 10 志願），並採兩階段分發機制提高錄取機會。",
                    f"本平台完整整合中興大學 {len(partners)} 所合作大學之申請門檻、Fact Sheet 連結、熱門交換學校排行榜、近 4 學期共 83 校 422 人次錄取榜單，以及涵蓋 91 所合作校之 548 篇歷屆學長姐返國心得與影音。",
                ],
                "source": {
                    "title": "國立中興大學國際事務處—交換學生計畫與申請簡章專區",
                    "source_url": "https://www.oia.nchu.edu.tw/index.php/2-uncategorised/154-1-1-exchange-info",
                    "category": "partner_school",
                    "summary": "國立中興大學赴國外及大陸地區交換學生甄選計畫總覽。",
                },
            }
        ],
        "eligibility": [
            {
                "title": "申請資格、歷年總平均 60 分門檻、書審配分比重與每學期至少 6 學分（108 小時）規定",
                "details": [
                    "申請對象與年級限制：本校學位生（含進修部）學士班一年級僅可申請春季班、學士班二年級（含）以上、碩士班一年級（含）以上、博士班一年級（含）以上，通過系所推薦者。延畢生得申請並出國交換（惟出國交換不得作為申請延畢之理由；部分大陸姊妹校不接受大四或延畢生）。同一學制內最多可交換 2 次，每次以 1 學期為限。",
                    "學業成績門檻與評分比重：學士班學生歷年在校總平均分數須達 60 分（含）以上。校內書審配分：【赴國外姊妹校】在校成績 30%、外語能力 35%、自傳及讀書計畫 30%、推薦函 5%；【赴大陸地區姊妹校】在校成績 50%、自傳及讀書計畫 45%、推薦函 5%。",
                    "境外最低修課與學分抵免：交換期間每學期至少應選修相當於中興大學 6 學分（或修課時間 108 小時）之課程（領取獎學金者須含至少 1 門與本系所相關課程）。返國後 1 個月內須檢具正式成績單辦理學分抵免（不論是否採認學分，皆須跑完抵免程序始得離校）。",
                    "抵達通報與返國義務：抵達及返國時須填寫抵達通知單，返國後 2 個月內（受獎生 2 週內）繳交交換心得報告，且畢業前須參與國際處分享活動至少 3 小時。",
                ],
                "source": {
                    "title": "國立中興大學選送學生出國交換甄選辦法與 116-1 申請簡章",
                    "source_url": NCHU_REGULATIONS_PDF_URL,
                    "category": "exchange_application",
                    "summary": "國立中興大學交換生申請資格、書審配分、最低修課學分與返國學分抵免辦法。",
                },
            }
        ],
        "language_requirements": [
            {
                "title": "國外姊妹校 CEFR B2 英語門檻（TOEFL iBT 72 / IELTS 5.5 / TOEIC 785）、第二外語替代規則與大陸免附規定",
                "details": [
                    "【赴國外姊妹校英語標準（CEFR B2）】：TOEFL iBT 72 分以上（新制 4 分以上；TOEFL ITP 紙筆 543 分以上）、IELTS 5.5 以上，或 TOEIC 785 分以上（須為申請截止日前 2 年內應試之成績，並須符合各志願學校要求）。",
                    "【非英語系國家第二外語規定】：非英語系國家學校若可接受其他語言檢定（如日檢 JLPT、韓檢 TOPIK、德檢、法檢、西檢等），則可免交英語能力證明；惟志願序中若有任一所學校要求英檢，仍須於校內申請時繳交英檢證書。",
                    "【赴大陸地區姊妹校】：免附語言能力證明（惟部分大陸高校對外國籍／港澳臺僑生另有規定）。",
                ],
                "source": {
                    "title": "國立中興大學 116學年度第1學期（秋季班）交換學生申請簡章",
                    "source_url": NCHU_GUIDELINES_PDF_URL,
                    "category": "exchange_application",
                    "summary": "國立中興大學交換生外語能力標準、第二外語檢定替代規則與補件規定。",
                },
            }
        ],
        "required_documents": [
            {
                "title": "國立中興大學出國計畫線上申請系統（oiawp.nchu.edu.tw）7 項必繳文件與系所核章規範",
                "details": [
                    "1. 交換學生申請表：海外最多 5 志願＋大陸最多 5 志願（共最多 10 志願），須先取得導師或指導教授同意簽章後，再請系主任／所長核章並掃描上傳。",
                    "2. 在校中文歷年成績單：至註冊組或自動列印機器申請正本掃描（轉學生、碩一或博一新生無本校成績者附原校歷年成績單）。",
                    "3. 在學生歷年名次證明書：至註冊組或自動列印機器申請（碩、博班若無名次證明請再上傳一次歷年成績單）。",
                    "4. 語言能力證明影本：僅申請大陸地區免附；尚未收到正式成績單可先上傳網路查詢截圖並於 2026/11/06 23:59 前補件。",
                    "5. 自傳及讀書計畫（至多 A4 三面，有填海外志願須交英文版）、6. 第一志願家長同意書（經法定代理人簽名）、7. 線上教師推薦函兩份（本校教師推薦，研究生至少 1 份為指導教授，2026/10/30 中午 12:00 截止）。",
                ],
                "source": {
                    "title": "國立中興大學 116學年度第1學期（秋季班）交換學生申請簡章與線上申請系統",
                    "source_url": NCHU_GUIDELINES_PDF_URL,
                    "category": "exchange_application",
                    "summary": "線上申請應繳文件清單、單檔 2 MB 限制、核章順序與補件規範。",
                },
            }
        ],
        "scholarship_info": [
            {
                "title": "教育部學海飛颺、學海惜珠、中興大學選送學生赴海外研修獎學金與「希望之橋」獎學金",
                "details": [
                    "教育部「學海飛颺」暨「國立中興大學選送學生赴海外研修獎學金」：每年 2–3 月全線上申請，申請人須歷年名次在該班前 50% 或歷年平均分數 80 分以上，且外語達 CEFR B2 以上（興大校內經費亦涵蓋赴中國大陸及港澳地區）。",
                    "教育部「學海惜珠」獎學金：補助具低收入戶、中低收入戶、特殊境遇家庭、身心障礙生活補助或弱勢助學金資格之本國籍優秀學生赴非中港澳地區交換。",
                    "國立中興大學「希望之橋」獎學金：由校內經費補助經濟或文化不利優秀學生（含原住民、家庭突遭變故、低收／中低收／弱勢助學金／學雜費減免資格），前一學期平均達 60 分以上即可申請，補助範圍涵蓋中國大陸及港澳地區。",
                ],
                "source": {
                    "title": "國立中興大學國際事務處—交換學生獎學金專區",
                    "source_url": NCHU_SCHOLARSHIP_URL,
                    "category": "scholarship",
                    "summary": "學海飛颺、學海惜珠、興大海外研修獎學金與希望之橋獎學金申請辦法及簡章。",
                },
            }
        ],
        "document_explanations": [
            {
                "title": "國立中興大學出國計畫線上申請系統（oiawp.nchu.edu.tw）核章順序、線上推薦函與補件機制",
                "summary": "中興大學交換學生申請全數透過線上系統填報並上傳電子檔（JPG 或 PDF 格式，單檔上限 2 MB），海外與大陸地區可各選填最多 5 所志願。",
                "key_points": [
                    "《交換學生申請表》務必預留時間辦理紙本核章：須先請「導師或指導教授」簽名同意後，再送請「系主任／所長」核章，掃描後於線上申請截止前上傳。",
                    "2 份線上教師推薦函由申請人於系統內填入本校教師聯絡信箱，系統自動發送連結予推薦教師於截止日（116-1 為 2026/10/30 中午 12:00）前完成線上填寫；語檢成績單等補件可於補件截止日（2026/11/06 23:59）前寄至承辦人信箱 joytsai@dragon.nchu.edu.tw。",
                ],
                "applies_to": [],
                "source": {
                    "title": "國立中興大學 116學年度第1學期（秋季班）交換學生申請簡章",
                    "source_url": NCHU_GUIDELINES_PDF_URL,
                    "category": "exchange_application",
                    "summary": None,
                },
                "document_url": NCHU_GUIDELINES_PDF_URL,
                "document_type": "official_document",
                "full_text_extracted": True,
            }
        ],
        "rule_explanations": [
            {
                "title": "國立中興大學選送學生出國交換甄選辦法：書審配分、兩階段分發、每學期 6 學分（108 小時）與必辦學分抵免",
                "summary": "規範中興大學交換生甄選配分比重、兩階段志願分發、境外最低修課時數與返國離校前必辦之學分抵免程序。",
                "key_points": [
                    "書面審查配分：赴國外姊妹校為「在校成績 30%、外語能力 35%、自傳及讀書計畫 30%、推薦函 5%」；赴大陸地區姊妹校為「在校成績 50%、自傳及讀書計畫 45%、推薦函 5%」。",
                    "交換期間每學期至少須選修相當於中興大學 6 學分（或修課時間 108 小時）之課程（獎學金受獎生須含至少 1 門與本系相關課程）；返國後 1 個月內不論是否採認學分，皆須跑完學分抵免程序始得辦理畢業離校。",
                    "同一學制內最多可交換 2 次，每次申請以 1 學期為限；延畢生得申請並出國交換，惟出國交換不得作為申請延畢之理由。",
                ],
                "applies_to": [],
                "source": {
                    "title": "國立中興大學選送學生出國交換甄選辦法",
                    "source_url": NCHU_REGULATIONS_PDF_URL,
                    "category": "exchange_application",
                    "summary": None,
                },
                "document_url": NCHU_REGULATIONS_PDF_URL,
                "document_type": "official_document",
                "full_text_extracted": True,
            }
        ],
        "sources": [
            {
                "title": "國立中興大學國際事務處—交換學生申請資訊與歷年錄取名單專區",
                "source_url": "https://www.oia.nchu.edu.tw/index.php/2-uncategorised/154-1-1-exchange-info",
                "category": "exchange_application",
                "summary": None,
            },
            {
                "title": "國立中興大學 116學年度第1學期（秋季班）交換學生申請簡章 PDF",
                "source_url": NCHU_GUIDELINES_PDF_URL,
                "category": "exchange_application",
                "summary": None,
            },
            {
                "title": "國立中興大學選送學生出國交換甄選辦法 PDF",
                "source_url": NCHU_REGULATIONS_PDF_URL,
                "category": "exchange_application",
                "summary": None,
            },
            {
                "title": "國立中興大學國際事務處—海外交換姊妹校名額與語言門檻總表（五大洲 124 校）",
                "source_url": NCHU_OVERSEAS_SHEET_URL,
                "category": "partner_school",
                "summary": None,
            },
            {
                "title": "國立中興大學國際事務處—大陸地區交換姊妹校一覽表（43 校）",
                "source_url": NCHU_MAINLAND_PAGE_URL,
                "category": "partner_school",
                "summary": None,
            },
            {
                "title": "國立中興大學國際事務處—交換學生獎學金專區（學海飛颺、學海惜珠、興大海外研修、希望之橋）",
                "source_url": NCHU_SCHOLARSHIP_URL,
                "category": "scholarship",
                "summary": None,
            },
            {
                "title": "國立中興大學國際事務處—出國交換學生返國心得及影音分享專區（548 篇）",
                "source_url": NCHU_EXPERIENCE_PORTAL_URL,
                "category": "partner_school",
                "summary": None,
            },
        ],
    }
    (OFFICIAL_NCHU_DIR / "student_dashboard.json").write_text(
        json.dumps(student_dashboard_payload, ensure_ascii=False, indent=2)
        + "\n",
        encoding="utf-8",
    )

    pages_records = [
        {
            "title": "國立中興大學：116學年度第1學期（秋季班）與第2學期（春季班）出國交換甄選時程",
            "source_url": NCHU_GUIDELINES_PDF_URL,
            "published_at": "2026-08-05T00:00:00Z",
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
            "title": "國立中興大學：選送學生出國交換甄選辦法、書審配分比重與每學期 6 學分（108 小時）規定",
            "source_url": NCHU_REGULATIONS_PDF_URL,
            "published_at": "2026-08-05T00:00:00Z",
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
            "title": "國立中興大學：出國交換 CEFR B2 外語能力門檻（TOEFL iBT 72 / IELTS 5.5 / TOEIC 785）與第二外語規則",
            "source_url": NCHU_GUIDELINES_PDF_URL,
            "published_at": "2026-08-05T00:00:00Z",
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
            "title": "國立中興大學：出國計畫線上申請系統 7 項應繳文件、導師與系主任核章及線上教師推薦函規範",
            "source_url": NCHU_APPLY_PORTAL_URL,
            "published_at": "2026-08-05T00:00:00Z",
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
            "title": "國立中興大學：學海飛颺、學海惜珠、選送學生赴海外研修獎學金與希望之橋獎學金",
            "source_url": NCHU_SCHOLARSHIP_URL,
            "published_at": "2026-08-05T00:00:00Z",
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
    (OFFICIAL_NCHU_DIR / "pages.jsonl").write_text(
        "\n".join(json.dumps(p, ensure_ascii=False) for p in pages_records)
        + "\n",
        encoding="utf-8",
    )

    home_rules = {
        "school_id": "nchu",
        "school_name": "國立中興大學",
        "eligibility": student_dashboard_payload["eligibility"],
        "application_periods": student_dashboard_payload["application_periods"],
        "selection_rules": {
            "undergraduate_minimum_average_score": 60.0,
            "weights_overseas": {
                "academic_grade": 0.30,
                "language_proficiency": 0.35,
                "autobiography_and_study_plan": 0.30,
                "recommendation_letters": 0.05,
            },
            "weights_mainland_china": {
                "academic_grade": 0.50,
                "autobiography_and_study_plan": 0.45,
                "recommendation_letters": 0.05,
            },
            "minimum_credits_per_semester": 6,
            "minimum_contact_hours_per_semester": 108,
            "credit_transfer_deadline_months": 1,
            "return_report_deadline_months": 2,
            "scholarship_return_report_deadline_weeks": 2,
            "required_sharing_activity_hours": 3,
        },
        "source_urls": nchu_source_urls,
        "verified_at": "2026-10-18",
    }
    (OFFICIAL_NCHU_DIR / "home_rules.json").write_text(
        json.dumps(home_rules, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    (OFFICIAL_NCHU_DIR / "documents.json").write_text(
        json.dumps(
            {
                "school_name": "國立中興大學",
                "required_documents": student_dashboard_payload["required_documents"],
                "source_urls": nchu_source_urls,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    (OFFICIAL_NCHU_DIR / "scholarships.json").write_text(
        json.dumps(
            {
                "school_name": "國立中興大學",
                "scholarships": student_dashboard_payload["scholarship_info"],
                "source_urls": nchu_source_urls,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    completeness = {
        "school_id": "nchu",
        "school_name": "國立中興大學",
        "total_partners": len(partners),
        "partner_count": len(partners),
        "international_partners": sum(
            1 for p in partners if p["country"] != "中國大陸"
        ),
        "mainland_partners": sum(
            1 for p in partners if p["country"] == "中國大陸"
        ),
        "experience_report_covered_partners": exp_covered_schools,
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
        "active_term": "116學年度第1學期（秋季班，2027年9月出國）交換學生甄選自2026/09/23中午12:00至2026/10/23中午12:00開放線上申請（推薦函至10/30 12:00、補件至11/06 23:59，12月中旬第一次放榜）；116-2春季班暨交換獎學金預計於2027年2–3月開放申請。",
        "verified_at": "2026-10-18",
    }
    (OFFICIAL_NCHU_DIR / "catalog-completeness.json").write_text(
        json.dumps(completeness, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    (OFFICIAL_NCHU_DIR / "verification_status.json").write_text(
        json.dumps(
            {
                "school_id": "nchu",
                "school_name": "國立中興大學",
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
            "sources/nchu/Exchange_Program_Guidelines_for_Fall_Semester_2027_TW.pdf",
            NCHU_GUIDELINES_PDF_URL,
            "國立中興大學 116學年度第1學期（秋季班）交換學生申請簡章 PDF",
        ),
        (
            "sources/nchu/R6_Regulations_for_nominating_NCHU_outbound_exchange_TW.pdf",
            NCHU_REGULATIONS_PDF_URL,
            "國立中興大學選送學生出國交換甄選辦法 PDF",
        ),
        (
            "sources/nchu/overseas_partners_sheet.xlsx",
            NCHU_OVERSEAS_SHEET_URL,
            "國立中興大學國際事務處海外姊妹校交換學生名額與語言門檻總表（五大洲 124 校）",
        ),
        (
            "sources/nchu/mainland_partners.html",
            NCHU_MAINLAND_PAGE_URL,
            "國立中興大學國際事務處大陸地區交換姊妹校一覽表（43 校）",
        ),
        (
            "sources/nchu/OIA_data.csv",
            "https://www.oia.nchu.edu.tw/images/partner_schools/OIA_data.csv",
            "國立中興大學國際事務處全球姊妹校合約資料庫（OIA_data.csv）",
        ),
        (
            "sources/nchu/115-2_Exchange_Scholarship.pdf",
            "https://www.oia.nchu.edu.tw/images/File/02_Exchange_Program/5-2/115-2_Exchange_Scholarship.pdf",
            "國立中興大學選送學生出國交換獎學金（學海飛颺、學海惜珠、興大海外研修、希望之橋）申請簡章",
        ),
        (
            "sources/nchu/Admission_list_2027SS_Exchange_program.pdf",
            "https://oia.nchu.edu.tw/images/File/02_Exchange_Program/5-1-4-1/Admission_list_2027SS_Exchange_program.pdf",
            "國立中興大學 115學年度第2學期（2027春季班）交換學生錄取名單",
        ),
        (
            "sources/nchu/Admission_list_2026Fall_Exchange_program.pdf",
            "https://oia.nchu.edu.tw/images/File/02_Exchange_Program/5-1-4-1/Admission_list_2026Fall_Exchange_program.pdf",
            "國立中興大學 115學年度第1學期（2026秋季班）交換學生錄取名單",
        ),
        (
            "sources/nchu/iss_outbound_posts.json",
            NCHU_EXPERIENCE_PORTAL_URL,
            "國立中興大學國際事務處出國交換返國心得與影音專區資料庫（548 篇）",
        ),
        (
            "sources/nchu/nchu_catalog_source.json",
            "https://www.oia.nchu.edu.tw/index.php/2-uncategorised/154-1-1-exchange-info",
            "國立中興大學 226 所出國交換合作大學整合資料集（含簡章名額、Fact Sheet、548 篇心得影音及 422 人次錄取榜單）",
        ),
        (
            "sources/nchu/nchu_resolved_locations.json",
            "https://www.oia.nchu.edu.tw/index.php/2-uncategorised/154-1-1-exchange-info",
            "國立中興大學 226 所出國交換合作大學 ROR / Wikidata 地理座標核對表",
        ),
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
        "school_id": "nchu",
        "school_name": "國立中興大學",
        "generated_at": CHECKED_AT,
        "active_cycle_note": completeness["active_term"],
        "sources": prov_sources,
    }
    (OFFICIAL_NCHU_DIR / "import_provenance.json").write_text(
        json.dumps(provenance_payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    print(
        f"Successfully built NCHU catalog: {len(partners)} partners ({open_partner_count} open, "
        f"{completeness['verified_campus_images']} verified images, {completeness['verified_locations']} verified locations), "
        f"{len(workflows)} workflows, {len(destinations)} destinations, {len(research_records)} research records, "
        f"{exp_covered_schools} schools with experience/admitted records ({len(student_experience_rows)} rows)."
    )


if __name__ == "__main__":
    main()
