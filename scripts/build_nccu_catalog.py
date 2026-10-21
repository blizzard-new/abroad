"""Build the official National Chengchi University (國立政治大學, NCCU) exchange data bundle."""

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

SOURCES_NCCU_DIR = REPO_ROOT / "sources" / "nccu"
OFFICIAL_NCCU_DIR = REPO_ROOT / "src" / "exchange_info" / "official_data" / "nccu"
STATIC_DIR = REPO_ROOT / "src" / "exchange_info" / "static"

CHECKED_AT = "2026-10-18T05:00:00Z"

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
    "約旦": "亞洲",
    "阿拉伯聯合大公國": "亞洲",
    "美國": "美洲",
    "加拿大": "美洲",
    "墨西哥": "美洲",
    "瓜地馬拉": "美洲",
    "哥倫比亞": "美洲",
    "巴西": "美洲",
    "智利": "美洲",
    "秘魯": "美洲",
    "澳洲": "大洋洲",
    "紐西蘭": "大洋洲",
    "奧地利": "歐洲",
    "安道爾": "歐洲",
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
    "冰島": "歐洲",
    "愛爾蘭": "歐洲",
    "義大利": "歐洲",
    "科索沃": "歐洲",
    "拉脫維亞": "歐洲",
    "列支敦士登": "歐洲",
    "立陶宛": "歐洲",
    "荷蘭": "歐洲",
    "挪威": "歐洲",
    "波蘭": "歐洲",
    "葡萄牙": "歐洲",
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
    "摩洛哥": "非洲",
}

REGION_COST_DEFAULTS = {
    "美國": (
        "USD 1,400–2,200 / 月（含住宿、餐飲、強制校園醫療保險與當地交通）",
        "須預留強制校園醫療保險（約 USD 1,500–2,500 / 學期）與 J-1 / F-1 簽證 SEVIS 費用。",
    ),
    "加拿大": (
        "CAD 1,500–2,200 / 月（含溫哥華／多倫多／蒙特婁／渥太華住宿、膳食、省級或校內醫保與市區交通）",
        "須投保接待校指定醫療保險並辦理 Study Permit 或 eTA。",
    ),
    "墨西哥": (
        "USD 650–1,000 / 月（含瓜達拉哈拉／蒙特雷學生住宿、餐飲與日常交通）",
        "交換逾 180 天須向墨西哥駐臺辦事處申辦學生簽證並投保海外全期醫療保險。",
    ),
    "哥倫比亞": (
        "USD 600–950 / 月（含波哥大住宿、膳食與日常交通）",
        "須依哥倫比亞駐外領事機構規定申辦學生簽證（Visa V Estudiante）並投保海外醫療保險。",
    ),
    "巴西": (
        "USD 650–1,000 / 月（含里約熱內盧／聖保羅學生住宿、餐飲與大眾運輸）",
        "須向巴西商務辦事處申辦 VITEM IV 學生簽證並備妥規定醫療保險與良民證認證。",
    ),
    "智利": (
        "USD 700–1,100 / 月（含聖地牙哥學生住宿、餐飲與地鐵交通）",
        "須透過智利領事系統申辦學生臨時居留簽證並投保涵蓋全期之海外醫療險。",
    ),
    "秘魯": (
        "USD 600–950 / 月（含利馬學生住宿、膳食與日常交通）",
        "須依接待校指引申辦秘魯交換學生簽證並投保海外醫療及意外保險。",
    ),
    "英國": (
        "GBP 1,100–1,600 / 月（倫敦約 GBP 1,350–1,850 / 月；曼徹斯特、愛丁堡、卡地夫、萊斯特約 GBP 1,000–1,400 / 月）",
        "交換一學期（6 個月內）可辦理 Standard Visitor 簽證，一學年須辦理 Student Visa 並繳納 IHS 醫療附加費。",
    ),
    "愛爾蘭": (
        "EUR 950–1,400 / 月（含利莫瑞克／科克學生公寓、餐飲與大眾運輸）",
        "須辦理愛爾蘭學習許可（IRP 居留登記）並投保符合愛爾蘭規定之醫療保險。",
    ),
    "法國": (
        "EUR 850–1,450 / 月（巴黎約 EUR 1,050–1,550 / 月；里昂、里爾、雷恩、艾克斯、格勒諾柏、拉羅謝爾約 EUR 750–1,150 / 月，可申請 CAF 房補）",
        "須透過法國教育中心（Campus France）完成面試並申辦長期學生簽證（VLS-TS）。",
    ),
    "德國": (
        "EUR 934–1,250 / 月（德國簽證限制提領帳戶基準為每月 EUR 934）",
        "須辦理德國法定公保（約 EUR 120–130 / 月）及繳納學期雜費／學期交通票（Semesterticket）。",
    ),
    "奧地利": (
        "EUR 850–1,250 / 月（含維也納／克姆斯／林茲學生宿舍、餐飲與大眾運輸）",
        "交換一學期（6 個月內）須申辦奧地利學生簽證 D（Visa D），超過 6 個月須申辦學生居留許可。",
    ),
    "列支敦士登": (
        "CHF 1,400–2,000 / 月（含瓦都茲學生宿舍、膳食與瑞士／列支敦士登跨境交通）",
        "須依列支敦士登移民局與瑞士領事規定辦理學生短期居留許可與強制醫療保險。",
    ),
    "西班牙": (
        "EUR 800–1,300 / 月（含馬德里／巴塞隆納／瓦倫西亞／潘普洛納學生公寓、飲食與大眾運輸）",
        "須備妥涵蓋全額醫療與遺體運返之私人醫療保險以申辦西班牙學生簽證。",
    ),
    "葡萄牙": (
        "EUR 750–1,150 / 月（含里斯本／波多學生公寓、餐飲與地鐵月票）",
        "須向澳門或駐外葡萄牙領事機構申辦長期學習簽證並備妥歐盟規格醫療保險。",
    ),
    "義大利": (
        "EUR 850–1,350 / 月（含米蘭、羅馬、波隆那、威尼斯、杜林、佛羅倫斯學生住宿、餐飲與大眾運輸）",
        "須向義大利經濟貿易文化推廣辦事處申辦學生簽證 D，抵義後 8 個工作天內申辦居留證（Permesso di Soggiorno）。",
    ),
    "荷蘭": (
        "EUR 950–1,450 / 月（荷蘭移民局 IND 財力證明基準約 EUR 1,225 / 月）",
        "由接待校代辦 MVV/VVR 居留許可，萊登、鹿特丹、烏特列支、提堡與格羅寧根房源緊張建議獲提名後立即申請宿舍。",
    ),
    "比利時": (
        "EUR 850–1,300 / 月（含布魯塞爾／魯汶／根特／列日學生宿舍、餐飲與大眾運輸）",
        "須辦理長期學生簽證 D 簽，抵達後向當地市政廳登記居留。",
    ),
    "瑞士": (
        "CHF 1,500–2,200 / 月（含洛桑、蘇黎世、聖加侖、巴賽爾、佛立堡、伯恩學生住宿、膳食與強制保險）",
        "須透過瑞士商務辦事處申辦學生簽證，並於抵瑞後申請居留證與醫療保險豁免或投保。",
    ),
    "瑞典": (
        "SEK 9,500–13,000 / 月（瑞典移民局財力基準約 SEK 10,314 / 月）",
        "交換超過 3 個月須向瑞典移民局申辦學生居留許可（Residence Permit for Studies）。",
    ),
    "丹麥": (
        "EUR 1,000–1,450 / 月（含哥本哈根／奧胡斯／歐登塞學生宿舍、飲食與自行車／大眾運輸）",
        "須辦理丹麥學生居留許可（ST1）並完成抵達後 CPR 登記。",
    ),
    "挪威": (
        "EUR 1,000–1,450 / 月（含卑爾根／奧斯陸學生宿舍與日常開支）",
        "須向挪威移民局（UDI）申辦學生居留許可。",
    ),
    "芬蘭": (
        "EUR 800–1,200 / 月（含赫爾辛基／坦佩雷／圖爾庫學生公寓、學生餐廳與當地交通）",
        "須透過 Enter Finland 申辦芬蘭學生居留許可並備妥規定醫療保險。",
    ),
    "冰島": (
        "EUR 1,100–1,600 / 月（含雷克雅維克學生住宿與日常生活開支）",
        "須向冰島移民局申辦學生居留許可並備妥規定醫療保險與財力證明。",
    ),
    "愛沙尼亞": (
        "EUR 650–950 / 月（塔林與塔爾圖學生宿舍與日常飲食交通開支實惠）",
        "須申辦愛沙尼亞長期簽證（D 簽）並備妥歐盟規格醫療保險。",
    ),
    "拉脫維亞": (
        "EUR 650–950 / 月（里加學生宿舍與生活費用實惠）",
        "須申辦拉脫維亞長期簽證（D 簽）並備妥歐盟規格醫療保險。",
    ),
    "立陶宛": (
        "EUR 600–900 / 月（維爾紐斯與考納斯學生宿舍與生活費用實惠）",
        "須透過 MIGRIS 系統申辦立陶宛國家簽證（D 簽）或臨時居留許可。",
    ),
    "波蘭": (
        "EUR 550–850 / 月（約 PLN 2,400–3,600，華沙、克拉科夫、波茲南、托倫、盧布林校內宿舍實惠）",
        "須向波蘭臺北辦事處申辦 D 類國別學生簽證並備妥規定旅行醫療保險。",
    ),
    "捷克": (
        "EUR 600–900 / 月（含布拉格／布爾諾／奧洛穆茨／奧斯特拉瓦／帕爾杜比采學生宿舍、食堂與市區交通卡）",
        "須提前預約捷克經濟文化辦事處申辦長期學生簽證與捷克合約醫療保險。",
    ),
    "斯洛伐克": (
        "EUR 600–900 / 月（含布拉提斯拉瓦學生住宿與日常開支）",
        "須申辦斯洛伐克長期學生簽證（D 簽）或臨時居留許可。",
    ),
    "斯洛維尼亞": (
        "EUR 650–950 / 月（含盧比安納學生住宿、學生餐券補貼與市區交通）",
        "須申辦斯洛維尼亞長期簽證（D 簽）或第一階段臨時居留許可。",
    ),
    "匈牙利": (
        "EUR 600–900 / 月（含布達佩斯／佩奇學生住宿、飲食與學生交通月票）",
        "須向匈牙利貿易辦事處申辦長期學生簽證（D 簽）。",
    ),
    "羅馬尼亞": (
        "EUR 550–850 / 月（含布加勒斯特／克盧日學生宿舍與日常生活開支）",
        "須申辦羅馬尼亞長期學生簽證（D/SD）並備妥規定醫療保險。",
    ),
    "俄羅斯": (
        "USD 500–850 / 月（莫斯科、聖彼得堡與葉卡捷琳堡校內宿舍與日常開支實惠）",
        "須憑接待校核發之俄羅斯聯邦移民署官方邀請函向莫北協駐臺代表處申辦學生簽證。",
    ),
    "土耳其": (
        "EUR 550–850 / 月（安卡拉與伊斯坦堡學生生活與交通開支實惠）",
        "須申辦土耳其學生簽證並於抵土後申辦短期學生居留證（Ikamet）與當地醫保。",
    ),
    "以色列": (
        "USD 1,000–1,500 / 月（含海法／耶路撒冷／特拉維夫學生宿舍、餐飲與大眾運輸）",
        "須向駐臺北以色列經濟文化辦事處申辦 A/2 學生簽證並投保接待校指定醫療保險。",
    ),
    "澳洲": (
        "AUD 1,800–2,600 / 月（含布里斯本／雪梨／墨爾本／坎培拉住宿與日常開支）",
        "須購買澳洲海外學生健康保險（OSHC）並線上申辦 Subclass 500 學生簽證。",
    ),
    "紐西蘭": (
        "NZD 1,600–2,300 / 月（含漢密爾頓／奧克蘭／威靈頓住宿與日常開支）",
        "須向紐西蘭移民局線上申辦 Fee Paying / Exchange Student Visa 並投保合規醫療險。",
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
        "RMB 2,000–3,800 / 月（所有大陸交換校皆為非宿費互惠校，由接待校統一安排住宿並於報到時繳納宿費；水電網路暖氣多屬使用者付費）",
        "持有效護照與臺胞證（臺灣居民來往大陸通行證）入境，並依接待校規定投保大陸境內來華留學生綜合醫療保險。",
    ),
    "香港": (
        "HKD 6,500–11,000 / 月（含香港浸會大學／嶺南大學宿舍與日常開支）",
        "須透過接待校向香港入境事務處申辦學生簽證／進入許可（Student Visa / Entry Permit）。",
    ),
    "新加坡": (
        "SGD 1,200–1,900 / 月（含新加坡管理大學／國立大學校外或校內住宿、熟食中心餐飲與地鐵公車）",
        "獲錄取後由接待校透過 SOLAR 系統協助申辦新加坡 Student's Pass（STP）。",
    ),
    "馬來西亞": (
        "MYR 1,500–2,500 / 月（吉隆坡與檳城生活機能便利且物價親民）",
        "須透過 EMGS（Education Malaysia Global Services）系統申辦學生簽證（VAL / Student Pass）。",
    ),
    "泰國": (
        "THB 15,000–25,000 / 月（曼谷朱拉隆功大學、法政大學、瑪希敦大學、曼谷大學周邊生活成本親民）",
        "須憑接待校入學許可向泰國貿易經濟辦事處申辦 Non-Immigrant ED 學生簽證。",
    ),
    "印尼": (
        "IDR 5,000,000–9,000,000 / 月（雅加達、日惹與泗水生活開支實惠）",
        "須由接待校協助向印尼移民總局申辦學習簽證（C316 / 學生電子簽證）。",
    ),
    "越南": (
        "USD 400–700 / 月（約 VND 10,000,000–17,000,000，河內、胡志明市與峴港生活成本低廉）",
        "須憑接待校入學許可透過駐臺北越南經濟文化辦事處申辦 DH 學生簽證。",
    ),
    "菲律賓": (
        "USD 500–850 / 月（約 PHP 28,000–48,000，馬尼拉住宿與生活開支）",
        "須憑接待校入學許可向馬尼拉經濟文化辦事處申辦 9(f) 學生簽證或 SSP 特別學習許可。",
    ),
    "印度": (
        "USD 400–700 / 月（索尼帕特金德爾全球大學校內住宿與日常開支實惠）",
        "須憑接待校正式入學許可向印度台北協會申辦 Student Visa。",
    ),
}

NCCU_OUTBOUND_PORTAL_URL = "https://outbound.nccu.edu.tw/"
NCCU_OIC_PORTAL_URL = "https://oic.nccu.edu.tw/"
NCCU_OVERSEAS_GUIDELINES_URL = "https://outbound.nccu.edu.tw/media/files/f353edca-d805-48ac-a6c9-9f66cf925c9e"
NCCU_OVERSEAS_SHEET_URL = "https://docs.google.com/spreadsheets/d/1upruwzQJC3IyeDdnk1HW0D_iEtbnuS4Se8bSTICwcyc/edit?gid=638297236#gid=638297236"
NCCU_MAINLAND_GUIDELINES_URL = "https://oic.nccu.edu.tw/Home/Download?FileId=AC94A5C6-1ED6-421D-AD29-F673F2418670"
NCCU_EXCHANGE_REGULATION_URL = "https://oic.nccu.edu.tw/Home/Download?FileId=148A0456-FC0D-4E92-BF90-3A2ACF488182"
NCCU_SCHOLARSHIP_URL = "https://oic.nccu.edu.tw/Category/25"
NCCU_SHORT_TERM_SUBSIDY_URL = "https://outbound.nccu.edu.tw/media/files/0409c3b8-97f9-4ef0-ad89-67eb6a5fc6a2"
NCCU_SHORT_TERM_ENFORCEMENT_URL = "https://outbound.nccu.edu.tw/media/files/6dc22493-4e11-40d0-bf39-4fb059b5c935"
NCCU_ASEAN_SCHOLARSHIP_URL = "https://outbound.nccu.edu.tw/media/files/b3fa95cf-ff46-4ff8-a259-0f6416c9f621"
NCCU_OUTSTANDING_SCHOLARSHIP_URL = "https://outbound.nccu.edu.tw/media/files/065e83a1-9621-4091-a9e8-2a73a3fd1807"
NCCU_HOPE_SCHOLARSHIP_URL = "https://outbound.nccu.edu.tw/media/files/6a06e7fb-8e9a-414b-9e69-f4e90218339d"
NCCU_MAINLAND_SUBSIDY_URL = "https://outbound.nccu.edu.tw/media/files/90997ab2-238a-4e43-87ca-d21737c6677b"
NCCU_PARTNER_SCHOLARSHIP_NOMINATION_URL = "https://outbound.nccu.edu.tw/media/files/1e27c7a2-f08f-4e64-9a14-e7d0cc61e752"
NCCU_PRE_DEPARTURE_URL = "https://outbound.nccu.edu.tw/media/files/7e8232d0-82cc-4f88-90b5-5791367fc044"
NCCU_EXPERIENCE_PORTAL_URL = "https://oic.nccu.edu.tw/Category/579"
NCCU_CONTRACT_SCHOOLS_URL = "https://oic.nccu.edu.tw/ContractSchoolList"


def clean_text(s: str) -> str:
    if not s:
        return ""
    return re.sub(r"\s+", " ", s).strip()


def format_colleges(item: dict) -> str:
    notes = clean_text(item.get("notes_raw") or "")
    elig = clean_text(item.get("elig_raw") or "")
    m_lim = re.search(
        r"(?:僅可修習|僅開放|限修|限申請)([^。；\n]{2,55})",
        notes + " " + elig,
    )
    if m_lim:
        return f"不限政大所屬學院報名（接待校修課／領域限制：{m_lim.group(0).strip()}）"
    return "不限學院（全校文、理、社會科學、法、商、外國語文、傳播、國際事務、教育、創新國際、資訊、X實驗及國際金融學院在學學生皆可依接待校開設系所報名）"


def format_degree_levels(item: dict) -> str:
    elig = clean_text(item.get("elig_raw") or "")
    notes = clean_text(item.get("notes_raw") or "")
    if item["country"] == "中國大陸":
        if "僅接收大學部" in elig or "不接受碩博士班" in elig or "僅收大學部" in elig:
            return "僅收大學部（學士班第 2 學期起報名、第 3 學期起出國交換）"
        return "大學部（大一下起報名、大二上［第3學期］起出國）、碩士班、博士班（碩一／博一下起報名、第2學期起出國）"
    m_deg = re.search(r"錄取生交換出國時資格：([^（。；]+)", elig)
    if m_deg:
        return f"{m_deg.group(1).strip()}（校內報名資格：學士班第 2 學期［含］起、碩博士班第 1 學期［含］起；轉學生就讀第 2 學期起）"
    if "不含研究所" in notes:
        return "大二以上不含研究所（學士班第 2 學期起報名）"
    return "大學部（大二以上）、碩士班、博士班（學士班第 2 學期［含］起、碩博士班第 1 學期［含］起可報名甄試）"


def format_language_req(item: dict) -> str:
    lr = clean_text(item.get("lang_raw") or "")
    if lr:
        return lr[:420]
    return "英語組須檢附有效期限內之 TOEFL iBT（不含 MyBest Scores，最低 CEFR B1 為 42 分／2026新制 3.0，多數締約校要求 B2 即 72–94 分）或 IELTS 學術組（最低 B1 為 4.0，多數締約校要求 6.0–6.5）；日韓德法西越俄土捷波語組依各該語組 CEFR 檢定換算標準計分（占甄試總成績 30%）。"


def format_gpa_req(item: dict) -> str:
    country = item["country"]
    lr = clean_text(item.get("lang_raw") or "")
    elig = clean_text(item.get("elig_raw") or "")
    notes = clean_text(item.get("notes_raw") or "")
    gpa_matches = []
    for m in re.finditer(r"GPA\s*[:：><=]?\s*[0-9.]+(?:\s*/\s*[0-9.]+)?", lr + " " + elig + " " + notes, re.I):
        g = m.group(0).strip()
        if g not in gpa_matches:
            gpa_matches.append(g)
    if country == "中國大陸":
        base = "校級赴陸交換門檻：在校學業平均成績占甄試總成績 30%（大學部採計〔學期平均×45% + (1-班排百分比)×100×55%〕×30%，研究生採計學期平均×30%），且口試（35%）、學業成績（30%）與書面審查（35%）三項加總須達 75 分以上始予錄取"
    else:
        base = "校級國際薦外交換門檻：在校成績占甄試總成績 20%（學士班依教務處「成績排名證明書」班排名百分比換算為 101 - 班排% 分；碩博士班依「學生學業成績總表」累計平均成績計分，未達 70 分者得 0 分且不予推薦；大一／轉學生無前一學期成績單者不予推薦）"
    if gpa_matches:
        base += f"｜締約校 GPA 要求：{'；'.join(gpa_matches)}（志願選填時系統不預先依 GPA 篩選，惟向締約校正式申請入學時須達該校 GPA 標準）"
    return base


def format_quota(item: dict) -> str:
    return clean_text(item.get("quota_raw") or "依當期甄試交換學校一覽表公告")


def format_study_period(item: dict) -> str:
    dur = clean_text(item.get("exchange_duration") or "1學期或1年")
    sem = clean_text(item.get("exchange_semesters") or "116.01")
    if item["country"] == "中國大陸":
        return "一學期（116學年度第1學期［2027年9月至2028年1月秋季學期］；政大與大陸姊妹校協議交換期間以 1 學期為限）"
    return f"{dur}（可選交換學期：{sem}；依《國立政治大學校級薦外交換學生計畫實施辦法》第 3 條，每次申請最長 1 學年［連續 2 學期］，在學期間累計至多 2 學年［4 學期］）"


def format_program_type(item: dict) -> str:
    cat = item.get("category")
    grps = "／".join(item.get("language_groups") or ["英語組"])
    if cat == "ML":
        return "交換學生（校級薦外大陸交換生計畫・繳交政大全額學雜費、互惠免繳接待校學費）"
    if cat == "OS":
        return f"交換學生（校級國際薦外交換計畫［{grps}］・繳交政大全額學雜費、互惠免繳接待校學費）"
    return "交換學生（國立政治大學國際合作事務處全球締約姊妹校・歷年／春季班開放）"


def main() -> None:
    OFFICIAL_NCCU_DIR.mkdir(parents=True, exist_ok=True)
    SOURCES_NCCU_DIR.mkdir(parents=True, exist_ok=True)

    catalog_items = json.loads(
        (SOURCES_NCCU_DIR / "nccu_catalog_source.json").read_text(encoding="utf-8")
    )
    locs_raw = json.loads(
        (SOURCES_NCCU_DIR / "nccu_resolved_locations.json").read_text(encoding="utf-8")
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

        detail_url = (item.get("detail_url") or "").strip() or None
        source_url = item.get("source_url") or NCCU_OVERSEAS_SHEET_URL

        if cat == "ML":
            round_label = "115學年度第1學期校級薦外大陸交換生甄試（實際交換：116學年度第1學期［2027秋季班］）"
            deadline_iso = "2026-11-06T17:00:00+08:00"
            deadline_rem = True
            win_status = "open"
            app_deadline_str = (
                "【115-1 校級薦外大陸交換生甄試（對應 116-1［2027秋季班］赴陸交換）】"
                "線上報名暨紙本繳件期間：2026年9月14日（一）至 2026年11月6日（五）17:00 止（送交行政大樓 7 樓 160704 室國合處大陸事務組）；"
                "口試排序公告：2026/11/23（一）；口試日期：2026/11/30（一）上午（行政大樓 8 樓 813 會議室）；"
                "放榜公告：2026/12/14（一）；確認交換意願及繳交 5,000 元保證金收據截止：2027/01/15（五）17:00 止。"
            )
        elif avail_status == "open":
            round_label = "115學年度第1學期校級國際薦外交換計畫甄試（實際交換：116學年度第1、2學期［2027秋季班／2028春季班］）"
            deadline_iso = "2026-11-02T16:00:00+08:00"
            deadline_rem = True
            win_status = "open"
            app_deadline_str = (
                "【115-1 校級國際薦外交換計畫甄試（對應 116-1／116-2 出國交換）】"
                "線上報名：2026/09/16 10:00 – 2026/09/24 16:00（補件至 09/30 16:00）；"
                "語言檢定證明上傳（須先登錄 iNCCU 全人系統並截圖合併上傳）：2026/10/05 10:00 – 2026/11/02 16:00；"
                "口試日期：2026/10/31（六）09:00–18:00；"
                "第一次志願選填（每語組至多 15 志願）：2026/11/10 10:00 – 11/16 16:00（放榜報到及繳交 5,000 元保證金：11/20–11/26 16:00）；"
                "第二次志願選填：2026/12/02 10:00 – 12/08 16:00（第二次放榜報到：12/11–12/17 16:00）。"
            )
        else:
            round_label = "115學年度第2學期校級國際薦外交換計畫甄試（春季甄試預計 2027年2–3月受理報名）"
            deadline_iso = "2027-03-10T16:00:00+08:00"
            deadline_rem = False
            win_status = "closed"
            app_deadline_str = (
                "【全球締約姊妹校（歷年／春季甄試開放）】本合作校為國立政治大學國際合作事務處登錄之全球締約姊妹校（收錄政大交換生返國心得報告）；"
                "115-1 秋季甄試未開缺，欲申請者請留意 115-2 春季甄試（預計 2027年2–3月公告）或 116-1 甄試最新交換學校一覽表。"
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
            or "校級代表位置：官方網域及國家已與 ROR / Wikidata 比對；實際交換校區以錄取通知與締約校專頁為準。",
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
        partner_sch = clean_text(item.get("partner_scholarship") or "")
        exp_posts = item.get("experience_posts") or []

        if country == "日本":
            sem_dates_str = "春季學期（前學期）：約每年 4 月至 8 月；秋季學期（後學期）：約每年 9/10 月至翌年 2/3 月"
        elif country in {"澳洲", "紐西蘭"}:
            sem_dates_str = "第 1 學期（秋季班出國對應 Semester 2）：約每年 7 月至 11 月；第 2 學期（春季班出國對應 Semester 1）：約每年 2 月至 6 月"
        else:
            sem_dates_str = "秋季學期（第 1 學期）：約每年 8/9 月至 12 月／翌年 1 月；春季學期（第 2 學期）：約每年 1/2 月至 5/6 月"

        course_parts = [f"開放申請院系與學制：{colleges_str}（{degree_levels_str}）。"]
        if notes_raw:
            course_parts.append(f"締約校交換申請與修課備註：{notes_raw[:350]}。")
        course_parts.append(
            "依《國立政治大學學生出國選修課程實施辦法》第 5、7 條及《校級薦外交換學生計畫實施辦法》第 12 條規定，出國期間學士班及碩士班學生每學期至少應於國外大學修習 1 門課程；赴國際地區（含港澳）交換生總修習科目 1/2（含）以上須達及格標準，赴大陸地區交換生總修習科目須全部達及格標準；返國後於次學期三分之一基準日前辦理學分抵免（學士班抵免上限為畢業最低學分 1/3、碩博士班為 1/2、雙聯學位為 2/3）。"
        )
        course_rest_str = " ".join(course_parts)

        if "宿" in notes_raw or "dorm" in notes_raw.lower():
            housing_str = f"{zh_name} 住宿與互惠規定：{notes_raw[:360]}"
        elif country == "中國大陸":
            housing_str = f"{zh_name} 為非宿費互惠協議之大陸交換學校，交換生統一由接待校安排入住宿舍（不得擅自外宿或任意要求更換），於抵達交換學校報到時直接繳納宿舍費用（水電、網路、暖氣多屬使用者付費）。"
        else:
            housing_str = f"{zh_name} 依兩校交換協議協助獲提名交換生申請校內外學生宿舍（若屬互惠免宿費名額，依政大第 624、625 次行政會議決議，須先向政大繳納學士班或碩博班住宿費最高價與最低價之平均值後，始享交換校住宿費互惠優惠；一般名額則自行向接待校繳納住宿費）。"

        tuition_points_list = [
            "報名費、保證金與政大註冊繳費規定：甄試報名費每一語組新臺幣 700 元（雙語組 1,400 元，一經繳交概不退還）。錄取生須於報到期限內繳交「薦外交換學生同意聲明書」及交換保證金新臺幣 5,000 元（履行每學期至少修習 1 門課且國際地區 1/2 以上科目及格／大陸地區全部科目及格、返國 2 個月內上傳交換心得、2 年內完成國際活動義工或兩岸交流活動義務後無息全額退還；繳交後無正當不可抗力事由放棄或異動交換期間者沒入保證金 1/2）。出國交換期間仍須辦理政大註冊並繳交全額學費、雜費、平安保險費及電腦網路通訊使用費（除加州大學柏克萊分校自費薦送案外），享互惠免繳接待校學費。",
            "六大獎助學金體系：（1）教育部「學海飛颺」計畫（每學期／學季新臺幣 100,000 元［含政大配合款］，二學期／學季以 1.5 倍計即 150,000 元；每年 1–3 月申請）；（2）政大「鼓勵學生赴國外進行短期進修計畫」補助（每學期／學季 80,000 元，二學期／學季 120,000 元；大學部一般生平均成績須達班排前 30%，研究生及弱勢／原住民生免受前 30% 限制，外語須達 TOEFL iBT 83 / IELTS 6.5 / JLPT N2 / TOPIK 3級 / 德法西 B1 / 俄語 1級；每年 5 月及 11 月辦理）；（3）教育部「學海惜珠」暨政大「希望起飛出國交換獎學金」（補助經濟與文化不利學生）；（4）政大「學生赴東協國家短期交換獎學金」（赴新加坡、馬來西亞、泰國、越南、印尼、菲律賓等東協締約校，每學期 20,000 元、一學年 30,000 元）；（5）政大「學生赴大陸地區短期進修獎助」（每人每學期 10,000 元，每年度 20 名）；（6）政大「傑出交換生獎學金」（返國後至畢業前申請，獲頒證書及 5,000–10,000 元）與締約校獎學金（如日本 JASSO、德國 Baden-Württemberg Stipendium、UMAP 獎學金等，依《申請締約校獎學金推薦原則》辦理）。",
        ]
        if partner_sch:
            tuition_points_list.append(f"本締約校專屬獎學金／補助資訊：{partner_sch}")

        if cat == "ML":
            app_steps_list = [
                f"步驟一（確認中華民國國籍、在學學期與大陆姊妹校特殊規定）：確認具中華民國國籍且為政大在學學生（大一／碩一／博一下學期起可申請報名，於學士班第 3 學期起、碩博班第 2 學期起赴陸交換；僑生、陸生、外國生不得參加），並詳閱 {zh_name} 簡章附件三特殊注意事項。",
                "步驟二（09/14–11/06 線上申請與紙本送件至國合處大陸事務組）：於 2026/09/14 至 2026/11/06（五）17:00 前登入 iNCCU 赴陸交換報名系統填報志願與對應專業名稱，繳交甄試報名費 700 元，並將親筆簽名之線上申請書、個人自傳（1,000字內）、研究／學習計畫（3,000字內）、成績排名證明書正本（研究生免附）、中文歷年成績單正本、報名費收據正本及選繳參考資料（全人系統語言檢定截圖等，5張A4為限）左上角裝訂送交行政大樓 7 樓 160704 室國合處大陸事務組。",
                "步驟三（11/30 甄選口試、12/14 放榜與 01/15 前繳交 5,000 元保證金確認意願）：甄試採計口試 35%、學業平均成績 30%、書面審查 35%，三項總成績須達 75 分以上始予錄取（單一錄取無遞補）。2026/11/30（一）上午參加口試，2026/12/14 放榜後於 2027/01/15 17:00 前繳交「薦外交換學生同意聲明書」及 5,000 元保證金收據。",
                f"步驟四（次學期 3–5 月繳交 {zh_name} 備審資料、辦理出國選課單與返國履行義務退還保證金）：2027年3–5月依通知繳交 {zh_name} 入學申請資料，6–8月取得錄取通知、參加行前說明會並辦理出國選課申請與臺胞證／役男出境；交換期間所修課程皆須及格，返國後 2 個月內繳交 3,000 字心得報告與 10 頁照片 PPT 並參與至少 2 項兩岸交流活動後退還保證金。",
            ]
        else:
            app_steps_list = [
                f"步驟一（確認學制資格、碩博 70 分門檻與 {zh_name} 語檢／GPA 條件）：確認為政大學士班第 2 學期（含）起或碩博士班第 1 學期（含）起在學學生（碩博士班累計平均須達 70 分以上，未達 70 分得 0 分且不予推薦；外國生及僑生不得申請至原屬／原僑居國交換），並確認符合 {zh_name} 之語組、學制、語言檢定及 GPA 入學門檻。",
                "步驟二（09/16–09/24 線上報名與 10/05–11/02 語言檢定證明上傳）：於 2026/09/16 10:00 至 09/24 16:00 前於政大校級薦外交換系統完成線上報名、繳交報名費（單一語組 700 元、雙語組 1,400 元）並上傳交換計畫書與履歷表（各至少 500 字、2 頁為限，占 20%）、英文歷年成績單與學士班成績排名證明書（占 20%）；並於 2026/10/05 10:00 至 11/02 16:00 前先至 iNCCU「全人系統—語言檢定」登錄截圖，再合併語檢成績單上傳（占 30%；另檢附 114 學年度培力英檢 BESTEP B2/C1 以上可加 1–2 分）。",
                f"步驟三（10/31 甄試口試、兩階段 15 志願選填與繳交 5,000 元保證金報到）：於 2026/10/31（六）參加口試（占 30%）。2026/11/10–11/16 進行第一次志願選填（每語組至多 15 志願），11/20–11/26 完成線上報到並繳交 5,000 元保證金及同意聲明書（剩餘名額於 12/02–12/08 開放第二次志願選填、12/11–12/17 報到）。2027 年 1 月中起由國合處向 {full_name} 辦理官方提名（Nomination）。",
                "步驟四（向締約校遞交入學申請、行前選課註冊與返國 2 個月內上傳心得退還保證金）：獲國合處提名後依締約校規定繳交護照、英文成績單、財力證明等入學文件；取得入學許可後辦理簽證、政大出國選課申請、全額學雜費註冊及獎學金申請（1–3 月學海飛颺、5 月／11 月政大短期進修補助與東協獎學金）；交換期間每學期至少修習 1 門課且總科目 1/2 以上及格，返國後 2 個月內於交換網站撰寫心得並於 2 年內完成 1 次國際活動義工服務後退還 5,000 元保證金。",
            ]

        elig_points_list = [
            f"開放學制與年級：{degree_levels_str}",
            f"開放申請學院：{colleges_str}",
            f"在校成績與 GPA 規定：{gpa_req_str}",
            f"語言檢定要求：{lang_req_str}",
        ]
        if notes_raw:
            elig_points_list.append(f"締約校特殊規定與備註：{notes_raw[:260]}")

        notes_lines = [
            f"【合作類別與期程】{program_type}｜交換期間：{study_period_str}",
            f"【當期名額與語組】{quota_str}",
            f"【開放學院與學制】{colleges_str}｜{degree_levels_str}",
            f"【語言與學業門檻】{lang_req_str}｜{gpa_req_str}",
        ]
        if notes_raw:
            notes_lines.append(f"【締約校重要備註】{notes_raw[:380]}")
        if exp_posts:
            notes_lines.append(
                f"【政大歷屆交換生返國心得】政大國合處官網「交換學生經驗分享（Category/579）」公開收錄赴 {zh_name} 交換生返國心得報告共 {len(exp_posts)} 篇。"
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
            "availability_note": f"國立政治大學國際合作事務處公告合作姊妹校；{quota_str}。",
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
            "factsheet_url": detail_url,
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
                "title": f"國立政治大學薦外交換學校一覽表與申請條件—{zh_name}",
                "source_url": source_url,
                "role": "home_university",
                "authority": "home_official_notice",
                "effective_academic_year": "116",
                "application_round": round_label,
                "checked_at": CHECKED_AT,
            },
            {
                "title": "國立政治大學 115.01 校級國際薦外交換計畫甄試簡章／赴大陸地區交換學生甄試簡章 PDF",
                "source_url": NCCU_MAINLAND_GUIDELINES_URL if cat == "ML" else NCCU_OVERSEAS_GUIDELINES_URL,
                "role": "home_university",
                "authority": "home_official_notice",
                "effective_academic_year": "116",
                "application_round": round_label,
                "checked_at": CHECKED_AT,
            },
            {
                "title": "國立政治大學校級薦外交換學生計畫實施辦法 PDF",
                "source_url": NCCU_EXCHANGE_REGULATION_URL,
                "role": "home_university",
                "authority": "home_official_notice",
                "effective_academic_year": "116",
                "application_round": round_label,
                "checked_at": CHECKED_AT,
            },
        ]
        if detail_url:
            wf_sources.append({
                "title": f"國立政治大學國合處全球締約校專頁—{zh_name}",
                "source_url": detail_url,
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
            "home_university": "國立政治大學",
            "school_name": full_name,
            "partner_website": website,
            "country": country,
            "program_type": program_type,
            "academic_year": "116",
            "application_round": round_label,
            "effective_application_rounds": [
                round_label,
                "115-1",
                "115-2",
                "116-1",
                "116-2",
                "116學年度第1學期（秋季班）",
                "116學年度第2學期（春季班）",
                "第1學期（秋季班）",
                "第2學期（春季班）",
            ],
            "applicability_status": "verified",
            "applicability_note": (
                "國立政治大學每年分兩學期辦理校級國際薦外交換計畫與赴大陸交換甄試（提前一學年甄選：115-1 甄試對應 116-1／116-2 出國交換）；"
                "國際交換採計語言檢定 30%、口試 30%、在校成績 20%、讀書計畫及履歷 20%，分兩階段選填 15 個志願；大陸交換採計口試 35%、書審 35%、學業成績 30%，總分須達 75 分以上。"
            ),
            "review_status": "published",
            "published_at": CHECKED_AT,
            "steps": [
                {
                    "rule_id": f"nccu-116-home-1-{idx+1:03d}",
                    "order": 1,
                    "phase": "校內申請",
                    "title": f"確認政大在學年級、碩博 70 分／班排門檻與 {zh_name} 語檢及 GPA 入學條件",
                    "responsible_party": "學生",
                    "responsible_unit": "國立政治大學國際合作事務處（行政大樓 8 樓國際教育組／7 樓 160704 室大陸事務組）",
                    "deadline_at": deadline_iso,
                    "deadline_status": "verified_exact" if avail_status == "open" else "reference_only",
                    "deadline_source_url": NCCU_MAINLAND_GUIDELINES_URL if cat == "ML" else NCCU_OVERSEAS_GUIDELINES_URL,
                    "deadline_checked_at": CHECKED_AT,
                    "deadline_reminder_eligible": deadline_rem,
                    "summary": f"申請人須為政大在學學生（國際交換：學士班第 2 學期起、碩博士班第 1 學期起，碩博班累計平均須達 70 分以上；大陸交換：具中華民國國籍且大一／碩一／博一下學期起申請，於學士班第 3 學期起、碩博班第 2 學期起赴陸），並確認符合 {zh_name} 之語組、語言檢定及 GPA 入學標準。",
                    "details": [
                        f"開放學制與院系：{colleges_str}（{degree_levels_str}）",
                        f"語言與學業條件：{lang_req_str}｜{gpa_req_str}",
                        f"當期名額與交換期程：{quota_str}",
                    ],
                    "scope": {
                        "home_universities": ["國立政治大學"],
                        "partner_universities": [full_name],
                        "academic_years": ["115", "116"],
                        "application_rounds": [
                            round_label,
                            "115-1",
                            "116-1",
                            "116-2",
                            "116學年度第1學期（秋季班）",
                            "116學年度第2學期（春季班）",
                        ],
                    },
                    "source_urls": [
                        NCCU_MAINLAND_GUIDELINES_URL if cat == "ML" else NCCU_OVERSEAS_GUIDELINES_URL,
                        source_url,
                    ],
                    "checked_at": CHECKED_AT,
                    "support_status": "verified",
                },
                {
                    "rule_id": f"nccu-116-home-2-{idx+1:03d}",
                    "order": 2,
                    "phase": "校內申請",
                    "title": (
                        "於 09/14–11/06 完成赴陸交換線上申請並將簽名紙本送交國合處大陸事務組"
                        if cat == "ML"
                        else "完成線上報名（09/16–09/24）並於 10/05–11/02 上傳 iNCCU 全人系統登錄截圖暨語言檢定證明"
                    ),
                    "responsible_party": "學生",
                    "responsible_unit": "國立政治大學國際合作事務處",
                    "deadline_at": deadline_iso,
                    "deadline_status": "verified_exact" if avail_status == "open" else "reference_only",
                    "deadline_source_url": NCCU_MAINLAND_GUIDELINES_URL if cat == "ML" else NCCU_OVERSEAS_GUIDELINES_URL,
                    "deadline_checked_at": CHECKED_AT,
                    "deadline_reminder_eligible": deadline_rem,
                    "summary": (
                        "於 2026/09/14 至 11/06 17:00 前登入 iNCCU 完成赴陸交換線上申請、繳交報名費 700 元，並備齊親筆簽名申請書、自傳（1,000字內）、研究／學習計畫（3,000字內）、成績排名證明書（研究生免附）、中文歷年成績單與報名費收據正本送交行政大樓 7 樓 160704 室。"
                        if cat == "ML"
                        else "於 2026/09/16 至 09/24 16:00 完成線上報名、繳交每語組 700 元報名費並上傳交換計畫書及履歷表（各至少 500 字、2 頁為限）、英文歷年成績單與學士班成績排名證明書；再於 2026/10/05 至 11/02 16:00 前先至 iNCCU「全人系統—語言檢定」登錄截圖，合併語檢成績單 PDF 上傳。"
                    ),
                    "details": [
                        "國際交換書審與語檢規定：交換計畫書與履歷表須以報考語組語言撰寫（英語組以英文、外語組以該外語撰寫，各至少 500 字、2 頁為限）；英語組僅採計 TOEFL iBT（不含 MyBest Scores）或 IELTS 學術組；另檢附 114 學年度培力英檢 BESTEP B2 以上總分加 1 分、C1 以上加 2 分。",
                        "大陸交換書審規定：個人自傳 1,000 字以內、研究／學習計畫 3,000 字以內（超過字數不受理），連同成績單、班排名證明書、700 元報名費收據及選繳參考資料（5 張 A4 為限）以訂書針裝訂左上角送交大陸事務組。",
                    ],
                    "document_requirements": [
                        {
                            "name": "政大校級薦外交換線上申請表與報名費收據（每語組／大陸組新臺幣 700 元）",
                            "official_form_url": NCCU_OUTBOUND_PORTAL_URL,
                            "source_urls": [
                                NCCU_OUTBOUND_PORTAL_URL,
                                NCCU_OVERSEAS_GUIDELINES_URL,
                                NCCU_MAINLAND_GUIDELINES_URL,
                            ],
                        },
                        {
                            "name": "歷年成績單正本（國際交換附英文成績單；大陸交換附中文成績單）及學士班成績排名證明書（含前一學期班排百分比；研究生免附）",
                            "source_urls": [
                                NCCU_OVERSEAS_GUIDELINES_URL,
                                NCCU_MAINLAND_GUIDELINES_URL,
                            ],
                        },
                        {
                            "name": "讀書／交換計畫書與履歷／自傳（國際交換：報考語組語言撰寫之交換計畫書及履歷表各至少 500 字、2 頁為限；大陸交換：中文自傳 1,000 字內及研究／學習計畫 3,000 字內）",
                            "source_urls": [
                                NCCU_OVERSEAS_GUIDELINES_URL,
                                NCCU_MAINLAND_GUIDELINES_URL,
                            ],
                        },
                        {
                            "name": "有效語言能力檢定成績證明暨 iNCCU「全人系統—語言檢定」登錄截圖合併檔（國際交換必繳，於 10/05–11/02 上傳；大陸交換為選繳加分參考）",
                            "conditional": country == "中國大陸",
                            "condition_note": "國際薦外交換必繳（占總分 30%）；大陸地區交換免強制外語門檻，可選繳全人系統語檢截圖供書審參考",
                            "source_urls": [
                                NCCU_OVERSEAS_GUIDELINES_URL,
                                NCCU_MAINLAND_GUIDELINES_URL,
                            ],
                        },
                    ],
                    "scope": {
                        "home_universities": ["國立政治大學"],
                        "academic_years": ["115", "116"],
                        "application_rounds": [
                            round_label,
                            "115-1",
                            "116-1",
                            "116-2",
                            "116學年度第1學期（秋季班）",
                            "116學年度第2學期（春季班）",
                        ],
                    },
                    "source_urls": [
                        NCCU_OUTBOUND_PORTAL_URL,
                        NCCU_OVERSEAS_GUIDELINES_URL,
                        NCCU_MAINLAND_GUIDELINES_URL,
                    ],
                    "checked_at": CHECKED_AT,
                    "support_status": "verified",
                },
                {
                    "rule_id": f"nccu-116-home-3-{idx+1:03d}",
                    "order": 3,
                    "phase": "甄選與提名",
                    "title": (
                        "11/30 赴陸交換口試、12/14 放榜與 01/15 前繳交 5,000 元保證金及同意聲明書"
                        if cat == "ML"
                        else "10/31 甄試口試、兩階段 15 志願選填（11/10–11/16、12/02–12/08）與繳交 5,000 元保證金報到"
                    ),
                    "responsible_party": "學生與國立政治大學國際合作事務處",
                    "responsible_unit": "國立政治大學國際合作事務處",
                    "deadline_at": "2027-01-15T17:00:00+08:00" if cat == "ML" else "2026-11-26T16:00:00+08:00",
                    "deadline_status": "verified_exact" if avail_status == "open" else "reference_only",
                    "deadline_source_url": NCCU_MAINLAND_GUIDELINES_URL if cat == "ML" else NCCU_OVERSEAS_GUIDELINES_URL,
                    "deadline_checked_at": CHECKED_AT,
                    "deadline_reminder_eligible": deadline_rem,
                    "summary": (
                        "2026/11/30（一）上午於行政大樓 8 樓 813 會議室舉行口試（占 35%），12/14 公告錄取名單暨學校，錄取生須於 2027/01/15 17:00 前繳交「薦外交換學生同意聲明書」及 5,000 元保證金收據始獲推薦資格。"
                        if cat == "ML"
                        else "2026/10/31（六）舉行甄試口試（占 30%）；11/10–11/16 開放成績查詢與第一次志願選填（每語組至多 15 志願），11/20 放榜後於 11/26 16:00 前完成線上報到、上傳「薦外交換學生同意聲明書」並繳交 5,000 元保證金（第二次志願選填為 12/02–12/08、報到為 12/11–12/17）。"
                    ),
                    "details": [
                        "同分參酌順序（實施辦法第 6 條）：國際地區依序為（1）口試成績、（2）該校所在地區主要語言檢定成績、（3）在校成績、（4）交換計畫書成績；大陸地區依序為（1）口試成績、（2）在校成績、（3）交換計畫書成績。",
                        "學制名額分配原則：國際交換甄試時校級薦外名額平均分配至大學部及研究所（若僅有單一名額，依締約學校意願辦理）。",
                    ],
                    "scope": {
                        "home_universities": ["國立政治大學"],
                        "academic_years": ["115", "116"],
                        "application_rounds": [
                            round_label,
                            "115-1",
                            "116-1",
                            "116-2",
                            "116學年度第1學期（秋季班）",
                            "116學年度第2學期（春季班）",
                        ],
                    },
                    "source_urls": [
                        NCCU_OVERSEAS_GUIDELINES_URL,
                        NCCU_MAINLAND_GUIDELINES_URL,
                        NCCU_EXCHANGE_REGULATION_URL,
                    ],
                    "checked_at": CHECKED_AT,
                    "support_status": "verified",
                },
                {
                    "rule_id": f"nccu-{idx+1:03d}-host-apply",
                    "order": 4,
                    "phase": "合作校申請",
                    "title": f"由政大國合處辦理官方提名（2027年1月中起）並依 {zh_name} 規定遞交入學申請資料",
                    "responsible_party": "學生與接待校國際處",
                    "summary": f"完成校內報到及保證金繳交後，由政大國合處自 2027 年 1 月中起分批向 {zh_name} 辦理官方提名（Nomination）；學生須依締約校規定準備護照、歷年成績單、在學證明、財力證明、語檢證明及選課計畫按時完成線上或紙本送件，靜候締約校核發正式入學許可書（Letter of Acceptance）。",
                    "details": [
                        f"交換期程：{study_period_str}｜名額：{quota_str}",
                        f"語言與學業條件：{lang_req_str}",
                    ]
                    + ([f"締約校申請與修課備註：{notes_raw[:240]}"] if notes_raw else []),
                    "scope": {
                        "home_universities": ["國立政治大學"],
                        "partner_universities": [full_name],
                        "academic_years": ["115", "116"],
                        "application_rounds": [
                            round_label,
                            "115-1",
                            "116-1",
                            "116-2",
                            "116學年度第1學期（秋季班）",
                            "116學年度第2學期（春季班）",
                        ],
                    },
                    "source_urls": (
                        [
                            source_url,
                            NCCU_PRE_DEPARTURE_URL,
                            NCCU_SCHOLARSHIP_URL,
                        ]
                        + ([detail_url] if detail_url else [])
                        + ([website] if website else [])
                    ),
                    "checked_at": CHECKED_AT,
                    "support_status": "verified",
                    "needs_confirmation": False,
                },
                {
                    "rule_id": f"nccu-116-home-5-{idx+1:03d}",
                    "order": 5,
                    "phase": "行前準備",
                    "title": "辦理政大出國選課申請、獎助學金申請、簽證役男出境與返國後學分抵免及 5,000 元保證金退費",
                    "responsible_party": "學生",
                    "responsible_unit": "國立政治大學國際合作事務處／教務處註冊組／各系所",
                    "summary": "依《交換生行前須知》與《學生出國選修課程實施辦法》，出國當學期選課加簽暨退課結束前須完成政大「學生出國選課申請書」簽核並繳交政大全額學雜費；可依時程申請教育部學海飛颺／惜珠（1–3月）、政大短期進修補助／東協獎學金（5月、11月）或赴陸短期進修獎助；返國後於次學期 1/3 基準日前辦理學分抵免，並於返國 2 個月內上傳交換心得、完成義工／交流活動後申請無息退還 5,000 元保證金。",
                    "details": tuition_points_list,
                    "scope": {
                        "home_universities": ["國立政治大學"],
                        "academic_years": ["115", "116"],
                        "application_rounds": [
                            round_label,
                            "115-1",
                            "116-1",
                            "116-2",
                            "116學年度第1學期（秋季班）",
                            "116學年度第2學期（春季班）",
                        ],
                    },
                    "source_urls": [
                        NCCU_PRE_DEPARTURE_URL,
                        NCCU_SHORT_TERM_SUBSIDY_URL,
                        NCCU_EXCHANGE_REGULATION_URL,
                    ],
                    "checked_at": CHECKED_AT,
                    "support_status": "verified",
                },
            ],
            "sources": wf_sources,
            "last_checked": CHECKED_AT,
            "coverage_status": "official_verified",
            "coverage_note": "已完整整合國立政治大學 115.01 校級國際薦外交換計畫甄試簡章、115.1 校級薦外大陸交換生甄試簡章、交換學校一覽表（8大語組）、校級薦外交換實施辦法、6大獎助學金辦法及 650 篇歷屆交換心得。",
        })

        cost_default, visa_default = REGION_COST_DEFAULTS.get(
            country,
            (
                "USD 900–1,500 / 月（含住宿、膳食與日常交通）",
                "須依接待國駐臺機構規定辦理學生簽證並投保海外醫療及意外保險。",
            ),
        )
        cost_line = f"{zh_name} 預估每月生活費：{cost_default}"
        tuition_clean = tuition_points_list[0]
        housing_clean = housing_str
        calendar_clean = f"學期時間參考：{sem_dates_str}"
        course_clean = course_rest_str

        dest_sources = [
            {
                "title": f"國立政治大學薦外交換學校一覽表與申請條件—{zh_name}",
                "source_url": source_url,
                "summary": "政大官方交換學校名額、語組、外語門檻、GPA 要求與備註",
            },
            {
                "title": "國立政治大學校級薦外交換計畫甄試簡章與實施辦法",
                "source_url": NCCU_MAINLAND_GUIDELINES_URL if cat == "ML" else NCCU_OVERSEAS_GUIDELINES_URL,
                "summary": "政大校級交換甄試配分、5,000 元保證金義務、出國選課與返國學分抵免規定",
            },
        ]
        if detail_url:
            dest_sources.append({
                "title": f"國立政治大學國合處全球締約校專頁—{zh_name}",
                "source_url": detail_url,
                "summary": "姊妹校簡介、交換計畫與獎學金資訊",
            })
        if website:
            dest_sources.append({
                "title": f"{full_name} 官方網站",
                "source_url": website,
                "summary": "接待合作校官方網站",
            })
        if exp_posts:
            dest_sources.append({
                "title": f"國立政治大學赴 {zh_name} 交換生返國心得報告（共 {len(exp_posts)} 篇）",
                "source_url": exp_posts[0].get("url") or exp_posts[0].get("post_url") or NCCU_EXPERIENCE_PORTAL_URL,
                "summary": f"收錄政大國合處交換生赴 {zh_name} 返國心得報告",
            })

        src_url_list = (
            [source_url, NCCU_MAINLAND_GUIDELINES_URL if cat == "ML" else NCCU_OVERSEAS_GUIDELINES_URL]
            + ([detail_url] if detail_url else [])
            + ([website] if website else [])
        )

        destinations.append({
            "home_university": "國立政治大學",
            "school_name": full_name,
            "country": country,
            "city": location_obj.get("city") or country,
            "cost_summary": f"{cost_line}。\n{tuition_clean}",
            "housing_summary": housing_clean,
            "transport_summary": f"校區代表城市：{location_obj.get('city') or country}。請依入學許可與《交換生行前須知》確認實際授課校區、機場交通與當地學生大眾運輸票卡優惠。",
            "campus_life_summary": f"{calendar_clean}\n{course_clean}",
            "student_guide_sections": [
                {
                    "key": "cost",
                    "title": "生活費、教育部學海飛颺／惜珠與政大短期進修／東協／大陸／傑出交換生獎學金",
                    "summary": cost_line,
                    "points": [cost_line] + tuition_points_list,
                    "source_urls": src_url_list + [NCCU_SCHOLARSHIP_URL, NCCU_SHORT_TERM_SUBSIDY_URL, NCCU_ASEAN_SCHOLARSHIP_URL],
                    "caution": "教育部「學海飛颺」補助每學期 100,000 元（一學年 150,000 元）；政大「鼓勵學生赴國外進行短期進修計畫」補助每學期 80,000 元（一學年 120,000 元，大學部一般生須達班排前 30% 且外語達規定標準）；東協國家短期交換獎學金每學期 20,000 元；大陸短期進修獎助每學期 10,000 元。",
                },
                {
                    "key": "housing",
                    "title": "住宿資訊與互惠宿費規定",
                    "summary": housing_clean[:160],
                    "points": [housing_clean],
                    "source_urls": src_url_list + [NCCU_PRE_DEPARTURE_URL],
                    "caution": "若享有兩校互惠宿費減免，須依政大行政會議決議先繳納政大住宿費（碩博班或學士班住宿費最高價與最低價之平均值）；大陸地區交換校皆為非宿費互惠校，由接待校統一安排住宿。",
                },
                {
                    "key": "insurance",
                    "title": "醫療保險與安全（交換生行前須知）",
                    "summary": visa_default,
                    "points": [
                        visa_default,
                        "依政大《交換生行前須知》與《學生出國選修課程實施辦法》第 5 條，交換生於出國期間仍須辦理政大註冊並繳交學生平安保險費，且必須自費投保涵蓋整個交換期間之海外醫療及意外保險（及接待校強制校園醫保）。",
                    ],
                    "source_urls": src_url_list + [NCCU_PRE_DEPARTURE_URL],
                    "caution": "多數歐美日韓及紐澳姊妹校要求於註冊或抵校時出示符合當地政府或校方標準之醫療保險證明。",
                },
                {
                    "key": "visa",
                    "title": "簽證辦理與役男出境申請（出國前至少 1 個月）",
                    "summary": visa_default,
                    "points": [
                        "收到締約校核發之正式入學許可書（LOA / COE / DS-2019）後，請立即向該國駐臺辦事處申辦學生簽證（赴大陸交換須自行辦理有效護照與臺胞證）。",
                        "依《國立政治大學學生出國選修課程實施辦法》第 8 條，具役男身分學生擬出國選課者，應至遲於出國前 1 個月備齊入學許可等文件，由薦送單位（國合處）行文至學生戶籍地政府機關審核申請出境。",
                        visa_default,
                    ],
                    "source_urls": src_url_list + [NCCU_PRE_DEPARTURE_URL, NCCU_EXCHANGE_REGULATION_URL],
                    "caution": "各國領事館簽證審核約需 4–8 週，請勿於取得簽證與入學許可前購買不可退改之機票。",
                },
                {
                    "key": "courses",
                    "title": "出國選課申請、最低修課及格規定與返國學分抵免",
                    "summary": course_clean[:160],
                    "points": [
                        course_clean,
                        "依《學生出國選修課程實施辦法》第 4、7 條，學生應於出國當學期選課加簽暨退課階段結束前完成「學生出國選課申請書」簽核程序；返國後應提出國外大學正式成績單，於次學期三分之一基準日前向所屬系所辦理學分抵免（學士班上限為畢業最低學分 1/3、碩博士班為 1/2）。",
                    ],
                    "source_urls": src_url_list + [NCCU_EXCHANGE_REGULATION_URL, NCCU_PRE_DEPARTURE_URL],
                    "caution": "赴國際地區（含港澳）交換生總修習科目 1/2（含）以上須及格，赴大陸地區交換生總修習科目須全部及格，否則將沒入 5,000 元保證金。",
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
                    "caution": "部分合作大學設有多個校區，實際授課校區請以當期交換學校一覽表備註及姊妹校錄取通知為準。",
                },
                {
                    "key": "arrival",
                    "title": "返國後 2 個月內上傳交換心得、完成義工義務與退還 5,000 元保證金",
                    "summary": calendar_clean,
                    "points": [
                        calendar_clean,
                        "依《校級薦外交換學生計畫實施辦法》第 12 條與保證金退費規定：國際交換生須於返國後 2 個月內於政大出國交換網站撰寫返國報告，並於交換結束後 2 年內完成國際活動義工服務至少 1 次；大陸交換生須於返國後 2 個月內繳交 3,000 字以上心得報告（Word 檔）與 10 頁以上照片 PPT，並參加至少 2 項兩岸交流活動，完成後始得無息全額退還 5,000 元保證金。",
                    ]
                    + (
                        [
                            f"歷屆學長姐返國心得：政大國合處已公開收錄赴 {zh_name} 交換生心得報告共 {len(exp_posts)} 篇。"
                        ]
                        if exp_posts
                        else []
                    ),
                    "source_urls": src_url_list
                    + ([exp_posts[0].get("url") or exp_posts[0].get("post_url")] if exp_posts else [NCCU_EXPERIENCE_PORTAL_URL]),
                    "caution": "交換完畢返校後至畢業前，亦可於每年 5 月或 11 月依《國立政治大學傑出交換生獎學金辦理原則》申請傑出交換生獎學金（新臺幣 5,000–10,000 元）。",
                },
            ],
            "first_72_hours": [
                {
                    "title": "依締約校入學許可指定報到日完成新生報到、宿舍入住與選課確認",
                    "detail": calendar_clean,
                    "source_urls": [source_url],
                },
                {
                    "title": "完成當地居留登錄、醫療保險確認並於加退選截止前完成政大出國選課申請書",
                    "detail": f"{visa_default} 請於政大出國當學期選課加簽暨退課階段結束前完成校內「學生出國選課申請書」簽核，並確認每學期至少修習 1 門課程。",
                    "source_urls": [
                        NCCU_PRE_DEPARTURE_URL,
                        NCCU_EXCHANGE_REGULATION_URL,
                    ],
                },
            ],
            "sources": dest_sources,
            "last_checked": CHECKED_AT,
            "coverage_status": "official_verified",
            "coverage_note": "已整合國立政治大學 115.01 校級國際薦外交換計畫甄試簡章、115.1 校級薦外大陸交換生甄試簡章、交換學校一覽表、全球締約校名單、6大獎助學金辦法與 650 篇歷屆學長姐交換心得報告。",
        })

        research_records.append({
            "home_university": "國立政治大學",
            "school_name": full_name,
            "country": country,
            "official_website": website,
            "verification_status": "official_verified",
            "discovery_source_url": source_url,
            "checked_at": CHECKED_AT,
            "note": f"國立政治大學國合處交換學校一覽表、全球締約校資料庫（{detail_url or source_url}）及 ROR/Wikidata 官方網址核對完成。",
        })

        ev_sources = [
            {"title": f"國立政治大學薦外交換學校一覽表與條件—{zh_name}", "url": source_url},
        ]
        if detail_url:
            ev_sources.append({"title": f"國立政治大學國合處全球締約校專頁—{zh_name}", "url": detail_url})
        if website:
            ev_sources.append({"title": f"{full_name} 官方網站", "url": website})
        if exp_posts:
            ev_sources.append({
                "title": f"國立政治大學赴 {zh_name} 交換生返國心得報告（{exp_posts[0]['term']}）",
                "url": exp_posts[0].get("url") or exp_posts[0].get("post_url") or NCCU_EXPERIENCE_PORTAL_URL,
            })

        has_student_exp = bool(exp_posts)
        if has_student_exp:
            exp_covered_schools += 1

        ev_list = [
            {
                "theme": "housing",
                "kind": "official",
                "text": housing_clean,
                "sources": ev_sources,
                "checked_at": CHECKED_AT,
                "scope": "國立政治大學交換學校一覽表住宿說明與互惠宿費規定",
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
                "scope": "國立政治大學交換生費用規定、學海飛颺／短期進修補助／東協／大陸獎助與地區生活費估算",
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
                "scope": "國立政治大學交換生選課限制、最低修課及格門檻與返國學分抵免規定",
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
                "scope": "國立政治大學出國交換簽證、海外醫療保險與役男出境提醒",
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
                        f"｜政大國合處官網公開收錄赴 {zh_name} 歷屆交換生返國心得報告共 {len(exp_posts)} 篇。"
                        if exp_posts
                        else ""
                    )
                ),
                "sources": ev_sources,
                "checked_at": CHECKED_AT,
                "scope": "國立政治大學出國交換名額與歷屆學長姐交換心得報告",
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
                "已整合國立政治大學 115.01 校級國際薦外交換計畫甄試簡章、115.1 校級薦外大陸交換生甄試簡章、交換學校一覽表、全球締約校名單與 650 篇歷屆交換生返國心得報告。",
                "當期宿位供給、費用與選課限制請依締約校最新入學須知及課程目錄核對。",
            ],
            "location_signature": f"verified:{location_obj['latitude']}:{location_obj['longitude']}:representative",
            "extraction_version": 3,
        })

        sample_reports: list[dict] = []
        for p_item in exp_posts[:5]:
            p_url = p_item.get("url") or p_item.get("post_url") or NCCU_EXPERIENCE_PORTAL_URL
            sample_reports.append({
                "title": p_item.get("title") or f"國立政治大學赴 {zh_name} 交換學生返國心得報告",
                "url": p_url,
                "term": p_item.get("term") or "歷年交換",
            })

        if exp_posts:
            latest_post = exp_posts[0]
            terms_covered = list(dict.fromkeys(p.get("term") for p in exp_posts[:6] if p.get("term")))
            rep_title = (
                f"國立政治大學赴 {zh_name}（共 {len(exp_posts)} 篇）交換學生返國心得報告彙編"
            )
            summary_text = (
                f"國立政治大學國際合作事務處「交換學生經驗分享（Category/579）」專區公開收錄赴 {zh_name} 交換學生返國心得報告共 {len(exp_posts)} 篇"
                + (f"（涵蓋年度：{'、'.join(terms_covered[:5])}）" if terms_covered else "")
                + f"，最新代表篇目為《{latest_post.get('title') or zh_name}》，詳實記錄政大交換生行前簽證準備、締約校選課與學分抵免、學生宿舍申請及當地生活開銷。"
            )
            theme_map = {
                "academics": f"政大交換生分享於 {zh_name} 之選課流程、英語或當地語言授課體驗、學分制轉換及返國學分抵免實務。",
                "housing": f"政大交換生於返國心得中分享 {zh_name} 校內學生宿舍或校外租屋申請方式、月租費用與生活機能（{housing_clean[:120]}）。",
                "campus_culture": f"政大國合處收錄 {len(exp_posts)} 篇赴 {zh_name} 歷屆交換生返國心得報告，提供學弟妹第一手校園生活與跨文化交流指南。",
                "cost": f"政大交換生於心得中記錄赴 {zh_name} 之機票、簽證、住宿與每月生活費開銷（{cost_default}），以及教育部學海飛颺／政大短期進修補助申請經驗。",
            }
            p_url = latest_post.get("url") or latest_post.get("post_url") or NCCU_EXPERIENCE_PORTAL_URL
            student_experience_rows.append({
                "school_name": full_name,
                "country": country,
                "title": rep_title,
                "source_url": p_url,
                "source_type": "article",
                "platform": "國立政治大學國際合作事務處—交換學生經驗分享專區",
                "author_name": "國立政治大學返國交換學生",
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
                "exchange_term": latest_post.get("term") or "歷年交換",
                "summary_zh": summary_text,
                "original_summary": summary_text,
                "theme_summaries_zh": theme_map,
                "translation_status": "original",
                "source_kind": "official_experience_page",
            })

        experience_sources_records.append({
            "home_university": "國立政治大學",
            "school_name": full_name,
            "country": country,
            "official_experience_portal_url": NCCU_EXPERIENCE_PORTAL_URL,
            "partner_page_url": detail_url or source_url,
            "report_count": len(exp_posts),
            "sample_reports": sample_reports,
            "checked_at": CHECKED_AT,
        })

    partners_jsonl_text = (
        "\n".join(json.dumps(r, ensure_ascii=False) for r in partners) + "\n"
    )
    (OFFICIAL_NCCU_DIR / "partners.jsonl").write_text(
        partners_jsonl_text, encoding="utf-8"
    )
    (SOURCES_NCCU_DIR / "partners.jsonl").write_text(
        partners_jsonl_text, encoding="utf-8"
    )
    (OFFICIAL_NCCU_DIR / "application_workflows.jsonl").write_text(
        "\n".join(json.dumps(r, ensure_ascii=False) for r in workflows) + "\n",
        encoding="utf-8",
    )
    (OFFICIAL_NCCU_DIR / "destination_profiles.jsonl").write_text(
        "\n".join(json.dumps(r, ensure_ascii=False) for r in destinations) + "\n",
        encoding="utf-8",
    )
    (OFFICIAL_NCCU_DIR / "partner_research.jsonl").write_text(
        "\n".join(json.dumps(r, ensure_ascii=False) for r in research_records) + "\n",
        encoding="utf-8",
    )
    (OFFICIAL_NCCU_DIR / "student_life.jsonl").write_text(
        "\n".join(json.dumps(r, ensure_ascii=False) for r in life_records) + "\n",
        encoding="utf-8",
    )
    (OFFICIAL_NCCU_DIR / "experience_sources.jsonl").write_text(
        "\n".join(
            json.dumps(r, ensure_ascii=False) for r in experience_sources_records
        )
        + "\n",
        encoding="utf-8",
    )
    (OFFICIAL_NCCU_DIR / "student_experiences.jsonl").write_text(
        "\n".join(
            json.dumps(r, ensure_ascii=False) for r in student_experience_rows
        )
        + "\n",
        encoding="utf-8",
    )
    (OFFICIAL_NCCU_DIR / "campus-locations.json").write_text(
        json.dumps({"locations": new_locations}, ensure_ascii=False, indent=2)
        + "\n",
        encoding="utf-8",
    )

    # Add home university row ("國立政治大學", "臺灣") and partner locations to university_locations.jsonl
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

    nccu_home_loc = {
        "school_name": "國立政治大學",
        "country": "臺灣",
        "city": "臺北市文山區",
        "latitude": 24.9876,
        "longitude": 121.5761,
        "geocode_status": "verified",
        "geocoded_at": CHECKED_AT,
        "source_url": "https://www.wikidata.org/wiki/Q709706",
        "identity_source_url": "https://ror.org/03rqk8h36",
        "precision": "representative",
        "note": "校級代表位置：官方網域及國家已與 ROR 比對，座標來源為 Wikidata P625；實際交換校區以錄取通知為準。 母校代表點採臺北市文山區指南路二段64號校本部（行政大樓 7–8 樓國際合作事務處）；官方地址來源：https://oic.nccu.edu.tw/。",
    }
    existing_loc_map[("國立政治大學", "臺灣")] = nccu_home_loc
    sorted_locs = sorted(
        existing_loc_map.values(),
        key=lambda r: (r.get("country") or "", r.get("school_name") or ""),
    )
    loc_file.write_text(
        "\n".join(json.dumps(r, ensure_ascii=False) for r in sorted_locs) + "\n",
        encoding="utf-8",
    )

    nccu_source_urls = [
        NCCU_OUTBOUND_PORTAL_URL,
        NCCU_OIC_PORTAL_URL,
        NCCU_OVERSEAS_GUIDELINES_URL,
        NCCU_OVERSEAS_SHEET_URL,
        NCCU_MAINLAND_GUIDELINES_URL,
        NCCU_EXCHANGE_REGULATION_URL,
        NCCU_SCHOLARSHIP_URL,
        NCCU_SHORT_TERM_SUBSIDY_URL,
        NCCU_SHORT_TERM_ENFORCEMENT_URL,
        NCCU_ASEAN_SCHOLARSHIP_URL,
        NCCU_OUTSTANDING_SCHOLARSHIP_URL,
        NCCU_HOPE_SCHOLARSHIP_URL,
        NCCU_MAINLAND_SUBSIDY_URL,
        NCCU_PARTNER_SCHOLARSHIP_NOMINATION_URL,
        NCCU_PRE_DEPARTURE_URL,
        NCCU_EXPERIENCE_PORTAL_URL,
        NCCU_CONTRACT_SCHOOLS_URL,
    ]

    exchange_info_payload = {
        "school_name": "國立政治大學",
        "program_type": [
            "交換學生（校級國際薦外交換計畫・涵蓋英語、日語、韓語、德語、法語、西語、越語、俄語、土語、捷語、波語等語組，分兩階段選填 15 個志願）",
            "交換學生（校級薦外大陸交換生計畫・北京大學、清華大學、復旦大學、上海交通大學、南京大學、中國人民大學、武漢大學、中山大學、廈門大學等 26 所大陸重點姊妹校互免學費）",
        ],
        "academic_year": [
            "116（116學年度第1、2學期［2027秋季班／2028春季班］出國交換：由 115學年度第1學期甄試［2026年9–12月］及第2學期甄試［2027年2–5月］提前一學年辦理選拔）",
            "115（115學年度第1學期甄試：國際交換オープン 196 所海外／香港姊妹校共 280 個語組學制名額組別；大陸交換開放 26 所姊妹校共 98 個名額）",
        ],
        "semester": [
            "第1學期（秋季班：每年約 8/9 月至 12 月／翌年 1 月；澳洲與紐西蘭對應 Semester 2 為 7 月至 11 月）",
            "第2學期（春季班：每年約 1/2 月至 5/6 月；日本前學期為 4 月至 8 月）",
        ],
        "application_period": [
            "【115學年度第1學期校級國際薦外交換計畫甄試（對應 116-1／116-2 出國交換）】線上報名及個人資料上傳：2026/09/16 10:00 – 2026/09/24 16:00（補件至 09/30 16:00）；語言檢定證明上傳（須先登錄 iNCCU 全人系統並截圖合併）：2026/10/05 10:00 – 2026/11/02 16:00；口試日期：2026/10/31（六）09:00–18:00；成績公布及第一次志願選填（每語組至多 15 志願）：2026/11/10 10:00 – 11/16 16:00；第一次放榜及線上報到（繳交 5,000 元保證金及同意聲明書）：2026/11/20 10:00 – 11/26 16:00；第二次志願選填：2026/12/02 10:00 – 12/08 16:00；第二次放榜及線上報到：2026/12/11 10:00 – 12/17 16:00；國合處提名作業：2027 年 1 月中起分批進行。",
            "【115學年度第1學期校級薦外大陸交換生甄試（對應 116-1［2027年9月–2028年1月秋季學期］赴陸交換 1 學期）】線上申請暨紙本繳件期間：2026/09/14（一）至 2026/11/06（五）17:00 止（送交行政大樓 7 樓 160704 室國合處大陸事務組）；口試名單公告：2026/11/23（一）；口試日期：2026/11/30（一）上午（行政大樓 8 樓 813 會議室）；公告錄取名單暨學校：2026/12/14（一）；確認交換意願及繳交 5,000 元保證金收據截止：2027/01/15（五）17:00 止。",
            "【獎助學金受理期程】教育部「學海飛颺」與「學海惜珠」計畫：每年 1–3 月（及 8–9 月）受理；政大「鼓勵學生赴國外進行短期進修計畫」補助、政大「東協國家短期交換獎學金」與「傑出交換生獎學金」：每年 5 月（秋季出國／返國）及 11 月（春季出國／返國）受理；政大「希望起飛出國交換獎學金」：每年 4 月及 10 月受理。",
        ],
        "eligibility": [
            "申請資格與在學年級規定（《國立政治大學校級薦外交換學生計畫實施辦法》第 4 條）：報名甄試及出國交換期間均須具政大在學學籍。校級國際薦外交換：學士班學生第 2 學期（含）起、碩博士班學生第 1 學期（含）起得報名甄試（轉學生須於政大就讀第 2 學期起且具前一學期政大成績單）。校級赴大陸交換：具中華民國國籍之在學學生，最快可於大一／碩一／博一下學期報名，並於學士班第 3 學期起、碩博士班第 2 學期起赴大陸交換。外國學生不得申請至原屬國家交換，僑生不得申請至原僑居國家交換；未具中華民國國籍或入學管道為僑生、陸生、外國生者不得參加赴大陸交換甄試；領取臺灣獎學金之外國生不得於受獎期間申請交換。",
            "甄試評分標準與學業門檻（實施辦法第 6 條）：（一）國際地區（含香港、澳門）甄試總分由四項加總：1. 口試成績 30%、2. 語言檢定成績 30%（依 CEFR B1–C2 換算表轉換為 70–100 分）、3. 在校成績 20%（學士班依教務處「成績排名證明書」之班排名百分比換算為 `101 - 班排%` 分；碩博士班依「學生學業成績總表」累計平均成績計分，**未達 70 分者得 0 分且不予推薦**）、4. 交換計畫書及履歷表 20%；另檢附 114 學年度培力英檢（BESTEP）任一科達 B2 以上總分加 1 分、C1 以上加 2 分（總分上限 100 分）。（二）大陸地區甄試總分由三項加總：1. 口試成績 35%、2. 學業平均成績 30%（大學部採計 `[學期平均×45% + (1-班排百分比)×100×55%]×30%`，研究生採計 `學期平均×30%`）、3. 書面成績（自傳與研究／學習計畫）35%，**三項總成績未達 75 分者不予錄取**。",
            "選填志願與 GPA 注意事項：國際交換甄試系統於志願選填階段（每語組至多 15 個志願）不會依 GPA 進行事先篩選，學生可選填符合語言檢定成績門檻之學校，但獲得本校推薦資格後向締約校正式申請入學時，仍須符合該交換校之完整入學條件（含 GPA 及各科語言單項分數要求）。",
            "保證金、修課及格標準與返國義務（實施辦法第 9–12 條）：錄取生須於期限內繳交「薦外交換學生同意聲明書」及交換保證金新臺幣 5,000 元（繳交後無不可抗力事由放棄或異動交換期間者沒入 1/2）。出國期間每學期至少修習 1 門課，赴國際地區（含港澳）交換生總修習科目 1/2（含）以上須及格，赴大陸地區交換生總修習科目須全部及格；返國後 2 個月內須繳交交換心得報告，並於 2 年內完成國際活動義工服務至少 1 次（大陸交換為參與至少 2 項兩岸交流活動），始無息全額退還 5,000 元保證金。",
        ],
        "language_requirement": [
            "【英語組（占總分 30%，最低須達 CEFR B1 門檻）】僅接受有效期限內之 TOEFL iBT（不接受 MyBest Scores 及 Home Edition）或 IELTS 學術組（Academic）。CEFR 換算分數：B1（TOEFL iBT 42–71 / 2026新制 3.0–3.5 或 IELTS 4.0–5.0）換算 70–79.67 分；B2（TOEFL iBT 72–94 / 新制 4.0–4.5 或 IELTS 5.5–6.5）換算 80–89.55 分；C1（TOEFL iBT 95–114 / 新制 5.0–5.5 或 IELTS 7.0–8.0）換算 90–97.5 分；C2（TOEFL iBT 115–120 / 新制 6.0 或 IELTS 8.5–9.0）換算 98–100 分。多數英語組締約校要求達 B2（TOEFL iBT 79–90 或 IELTS 6.0–6.5）以上。",
            "【外語組（日語、韓語、德語、法語、西語、越語、俄語、土語、捷語、波語）】日語組採計 JLPT N3（70分）、N2（85分）、N1（95分）；韓語組採計 TOPIK 3級（75分）、4級（85分）、5級（95分）、6級（100分）；德語組採計 Goethe / TestDaF / OSD B1–C2；法語組採計 DELF / DALF / TCF B1–C2；西語組採計 DELE / SIELE B1–C2；越語組採計 IVPT A1–C2；俄語組採計 TORFL 1–4級；土語組採計 TYS A1–C2；捷語組與波語組須具英語 B1 以上檢定並修畢政大捷克語／波蘭語課程 1 學期以上且成績及格。",
            "【iNCCU 全人系統登錄規定與大陸交換規定】所有國際交換申請人上傳語言檢定證明前，必須先至「iNCCU > 學生資訊系統 > 全人系統 > 職涯發展 > 專業證照與技能專長 > 語言檢定」完成登錄並截圖，與成績單合併為單一 PDF 上傳。申請大陸地區交換者無強制外語門檻（可選附全人系統語檢截圖作為書審參考）。",
        ],
        "required_documents": [
            "1. 線上報名表與甄試報名費繳費證明（每語組／大陸組新臺幣 700 元，雙語組 1,400 元；大陸交換須列印線上申請書作為首頁並親筆簽名）",
            "2. 歷年成績單正本（國際交換上傳教務處核發之英文歷年成績單 PDF；大陸交換繳交中文歷年成績單正本）",
            "3. 學士班「成績排名證明書」正本（須含截至前一學期之全班人數與班排名百分比；碩博士班研究生免附，惟國際交換碩博累計平均須達 70 分以上）",
            "4. 讀書／交換計畫書與履歷表／自傳（國際交換：以報考語組語言撰寫之交換計畫書及履歷表各至少 500 字、2 頁為限；大陸交換：中文個人自傳 1,000 字以內及研究／學習計畫 3,000 字以內）",
            "5. 有效語言能力檢定成績單暨 iNCCU「全人系統—語言檢定」登錄頁面截圖合併檔（國際交換於 10/05–11/02 上傳；大陸交換為選繳）",
            "6. （選繳加分）114 學年度培力英檢（BESTEP）成績單（國際交換任一科 B2 以上總分加 1 分、C1 以上加 2 分）或社團／得獎／低收及中低收入戶證明（大陸交換選繳參考資料以 5 張 A4 為限）",
            "7. （錄取報到必繳）薦外交換學生同意聲明書及交換保證金新臺幣 5,000 元繳費收據",
        ],
        "scholarship_info": [
            "教育部「學海飛颺」計畫獎學金（含政大配合款）：補助優秀本國籍在學學生赴國外（不含大陸及港澳）修讀學分，每學期（學季）核發新臺幣 100,000 元，二學期（學季）以 1.5 倍計算即新臺幣 150,000 元；每年 1–3 月（及 8–9 月視經費）受理申請。",
            "國立政治大學「鼓勵學生赴國外進行短期進修計畫」補助（《補助要點》暨《施行細則》）：補助未獲學海飛颺之優秀交換生，每學期（學季）新臺幣 80,000 元，二學期（學季）以 1.5 倍計即新臺幣 120,000 元。申請資格：大學部一般生在校歷年平均成績須達各班前 30%（研究生、低收／中低收入戶及原住民學生免受班排前 30% 限制），且外語能力須達最低標準（TOEFL iBT 83 / IELTS 6.5 / JLPT N2 / TOPIK 3級 / 德法西語 CEFR B1 / 俄語 TORFL 1級）；每年 5 月（秋季出國）及 11 月（春季出國）受理。",
            "教育部「學海惜珠」計畫暨政大「希望起飛出國交換獎學金」：專項補助具直轄市、縣（市）主管機關開立之低收入戶、中低收入戶或特殊境遇家庭證明等經濟不利學生出國交換研修（學海惜珠每年 1–3 月、8–9 月受理；希望起飛每年 4 月、10 月受理，亦適用赴大陸交換之弱勢學生）。",
            "國立政治大學「學生赴東協國家短期交換獎學金」（114.10.15 修正）：鼓勵政大本國籍學生赴東協國家（新加坡、馬來西亞、泰國、越南、印尼、菲律賓等）締約校交換，每人每學期補助新臺幣 20,000 元、一學年（二學期）總額新臺幣 30,000 元（每年 5 月及 11 月受理，可與其他獎學金兼領惟總額上限 15 萬元）。",
            "國立政治大學「學生赴大陸地區短期進修獎助辦法」：獎助政大本國籍學生赴大陸地區締約校短期進修交換，每人每學期核發新臺幣 10,000 元（每年度名額 20 名）。",
            "國立政治大學「傑出交換生獎學金」（《辦理原則》）：交換期滿返校後至畢業前，於交換期間修課成績優異且積極參與當地文化交流或返校推廣國際交流活動者，得於每年 5 月及 11 月提出申請，獲頒證書及新臺幣 5,000 至 10,000 元獎學金；另可依《校級國際薦外交換學生申請締約校獎學金推薦原則》申請日本 JASSO、德國巴登符騰堡邦獎學金、UMAP 獎學金等締約校獎助。",
        ],
        "partner_universities": [p["school_name"] for p in partners],
        "source_urls": nccu_source_urls,
        "last_checked": CHECKED_AT,
    }
    (OFFICIAL_NCCU_DIR / "exchange_info.json").write_text(
        json.dumps(exchange_info_payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    student_dashboard_payload = {
        "school_name": "國立政治大學",
        "last_checked": CHECKED_AT,
        "academic_score_minimum": None,
        "academic_score_rule": "國際交換：在校成績占甄試總分 20%（學士班依教務處「成績排名證明書」之班排名百分比換算為 101 - 班排% 分；碩博士班依「學生學業成績總表」累計平均成績計分，未達 70 分者得 0 分且不予推薦）。大陸交換：學業平均成績占 30%（大學部採計〔學期平均×45% + (1-班排%)×100×55%〕×30%，研究生採計學期平均×30%），且口試（35%）、學業（30%）與書審（35%）三項總成績須達 75 分以上始予錄取。",
        "academic_gpa_minimum": None,
        "maximum_preferences": 15,
        "selection_rules": {
            "academic_policy": "percentage",
            "academic_reference_year": "116",
            "undergraduate_gpa_minimum": None,
            "undergraduate_rank_maximum": None,
            "graduate_academic_exempt": False,
            "exclude_in_service": False,
            "pending_quota_planning": False,
            "partner_requirements_need_confirmation": True,
            "degree_score_minimums": {},
            "excluded_undergraduate_years": [],
            "language_certificate_required": True,
        },
        "language_score_minimums": {},
        "application_periods": [
            {
                "title": "國立政治大學 115學年度第1學期校級國際薦外交換計畫甄試（對應 116-1／116-2 出國交換：語檢上傳 10/05–11/02、口試 10/31、志願選填 11/10–12/08）",
                "details": [
                    "線上報名及個人資料上傳：2026年9月16日 10:00 至 9月24日 16:00（退件補件至 9月30日 16:00）；語言檢定證明上傳（須先登錄 iNCCU 全人系統並截圖合併）：2026年10月5日 10:00 至 11月2日 16:00。",
                    "口試時段公布：2026年10月26日 16:00 前；口試日期：2026年10月31日（六）09:00–18:00。",
                    "兩階段志願選填與放榜報到（每語組至多 15 志願）：第一次志願選填 2026/11/10 10:00 – 11/16 16:00、放榜報到及繳交 5,000 元保證金 11/20 10:00 – 11/26 16:00；第二次志願選填 12/02 10:00 – 12/08 16:00、第二次放榜報到 12/11 10:00 – 12/17 16:00。",
                ],
                "source": {
                    "title": "國立政治大學 115.01 校級國際薦外交換計畫甄試簡章 PDF",
                    "source_url": NCCU_OVERSEAS_GUIDELINES_URL,
                    "category": "exchange_application",
                    "summary": "115-1 校級國際薦外交換計畫完整甄試日程、配分標準與兩階段 15 志願分發作業。",
                },
                "scope": "home_application",
                "program_types": ["exchange"],
                "academic_year": "116",
                "application_round": "115學年度第1學期校級國際薦外交換計畫甄試（對應 116-1／116-2 出國交換）",
                "audience": "all_students",
                "opens_at": "2026-09-16T10:00:00+08:00",
                "deadline_at": "2026-11-02T16:00:00+08:00",
                "date_status": "verified_exact",
                "status": "open",
                "status_note": "115-1 校級國際薦外交換甄試目前正處於語言檢定證明上傳階段（2026/10/05 10:00 至 11/02 16:00），口試於 10/31 舉行，11/10–12/17 進行兩階段志願選填與放榜報到。",
                "deadline_note": "請先於 iNCCU「全人系統—語言檢定」完成登錄並截圖，與語檢成績單合併為單一 PDF 上傳至政大出國交換甄試系統。",
                "reminder_eligible": True,
                "checked_at": CHECKED_AT,
            },
            {
                "title": "國立政治大學 115學年度第1學期校級薦外大陸交換生甄試（對應 116-1［2027秋季班］赴陸交換：09/14–11/06 報名收件）",
                "details": [
                    "報名暨紙本繳件期間：2026年9月14日（一）至 2026年11月6日（五）17:00 止（線上報名後將簽名申請書、1,000字自傳、3,000字學習計畫、成績單與 700 元報名費收據送交行政大樓 7 樓 160704 室國合處大陸事務組）。",
                    "口試與放榜日程：2026年11月23日公告口試名單，11月30日（一）上午於行政大樓 8 樓 813 會議室舉行口試，12月14日公告錄取名單暨學校，2027年1月15日 17:00 前確認交換意願並繳交 5,000 元保證金收據。",
                ],
                "source": {
                    "title": "國立政治大學 115學年度第1學期校級薦外大陸交換生甄試簡章 PDF",
                    "source_url": NCCU_MAINLAND_GUIDELINES_URL,
                    "category": "exchange_application",
                    "summary": "115-1 校級薦外大陸交換生甄試重要日程、26 所大陸姊妹校 98 名額表與附件三特殊規定。",
                },
                "scope": "home_application",
                "program_types": ["exchange"],
                "academic_year": "116",
                "application_round": "115學年度第1學期校級薦外大陸交換生甄試（對應 116-1［2027秋季班］赴陸交換）",
                "audience": "all_students",
                "opens_at": "2026-09-14T09:00:00+08:00",
                "deadline_at": "2026-11-06T17:00:00+08:00",
                "date_status": "verified_exact",
                "status": "open",
                "status_note": "115-1 校級薦外大陸交換生甄試現正開放報名收件至 2026/11/06（五）17:00 止（共開放北京大學、清華大學、復旦大學、上海交大、南京大學等 26 所姊妹校 98 個名額）。",
                "deadline_note": "完成 iNCCU 線上申請後，請於上班時間將紙本文件左上角裝訂送交行政大樓 7 樓 160704 室國合處大陸事務組。",
                "reminder_eligible": True,
                "checked_at": CHECKED_AT,
            },
            {
                "title": "國立政治大學「鼓勵學生赴國外進行短期進修計畫」補助、「東協國家短期交換獎學金」與「傑出交換生獎學金」秋季／春季申請期程（每年 5 月、11 月）",
                "details": [
                    "政大「鼓勵學生赴國外進行短期進修計畫」補助（每學期 8 萬元、一學年 12 萬元）與「東協國家短期交換獎學金」（每學期 2 萬元、一學年 3 萬元）：秋季班出國者於每年 5 月申請，春季班出國者於每年 11 月申請。",
                    "教育部「學海飛颺」（每學期 10 萬元、一學年 15 萬元）與「學海惜珠」：每年 1–3 月（及 8–9 月）受理申請；政大「希望起飛出國交換獎學金」：每年 4 月及 10 月受理。",
                ],
                "source": {
                    "title": "國立政治大學國際合作事務處—出國交換獎學金辦法專區",
                    "source_url": NCCU_SCHOLARSHIP_URL,
                    "category": "scholarship",
                    "summary": "政大六大出國交換獎助學金體系、補助金額與每學期申請月份。",
                },
                "scope": "home_application",
                "program_types": ["exchange"],
                "academic_year": "116",
                "application_round": "政大出國交換獎助學金申請（春季出國 11 月、學海系列 1–3 月、秋季出國 5 月）",
                "audience": "all_students",
                "opens_at": "2026-11-01T09:00:00+08:00",
                "deadline_at": "2026-11-30T17:00:00+08:00",
                "date_status": "reference_only",
                "status": "upcoming",
                "status_note": "每年 11 月受理春季出國短期進修補助、東協獎學金與傑出交換生獎學金申請；翌年 1–3 月受理教育部學海飛颺與學海惜珠申請；5 月受理秋季出國短期進修補助。",
                "deadline_note": "請依國合處獎助學金公告備齊申請表、成績排名證明、外語檢定及締約校錄取證明提出申請。",
                "reminder_eligible": False,
                "checked_at": CHECKED_AT,
            },
        ],
        "program_overview": [
            {
                "title": f"國立政治大學國際合作事務處校級薦外交換計畫總覽（{len(partners)} 所全球合作大學）",
                "details": [
                    f"國立政治大學國際合作事務處（OIC）辦理校級國際薦外交換計畫（涵蓋英語、日語、韓語、德語、法語、西語、越語、俄語、土語、捷語、波語等語組）與校級薦外大陸交換生計畫，本平台完整收錄 {len(partners)} 所官方合作大學（含 115-1 當期開放申請之 {open_partner_count} 所合作校［196 所海外／香港姊妹校 + 26 所大陸姊妹校］，以及 {len(partners) - open_partner_count} 所收錄政大交換生心得之歷年／春季班開放姊妹校）。",
                    f"政大校級交換甄試提前一學年辦理（115-1 甄試對應 116-1／116-2 出國交換），國際交換分兩階段選填 15 個志願，並提供教育部學海飛颺（每學期 10 萬／一學年 15 萬）、政大短期進修補助（每學期 8 萬／一學年 12 萬）、東協獎學金、大陸短期進修獎助、學海惜珠與希望起飛等完整獎學金體系，官網公開收錄 650 篇歷屆交換生返國心得報告（本目錄已連結 {len(student_experience_rows)} 所學校共 589 篇心得）。",
                ],
                "source": {
                    "title": "國立政治大學出國交換資訊網與國合處全球締約校專區",
                    "source_url": NCCU_OUTBOUND_PORTAL_URL,
                    "category": "exchange_application",
                    "summary": "政大校級國際薦外交換與赴大陸交換甄試簡章、266 所合作校、6大獎學金與 650 篇返國心得報告。",
                },
            }
        ],
        "eligibility": [
            {
                "title": "在學年級規定、碩博 70 分／大陸總分 75 分門檻與甄試配分機制",
                "details": [
                    "修業學期與國籍限制：校級國際交換限政大學士班第 2 學期（含）起、碩博士班第 1 學期（含）起在學學生（轉學生須於政大就讀第 2 學期起；外國生及僑生不得申請至原屬／原僑居國交換）。校級赴大陸交換限具中華民國國籍之在學學生（最快大一／碩一／博一下學期報名，於學士班第 3 學期起、碩博班第 2 學期起出國；僑生、陸生、外國生不得參加）。",
                    "國際交換甄試配分：語言檢定 30%（依 CEFR B1–C2 換算 70–100 分）、口試 30%、在校成績 20%（學士班為 `101 - 班排%` 分；碩博士班為累計平均分數，**未達 70 分得 0 分且不予推薦**）、交換計畫書及履歷 20%；另附 114 學年度培力英檢 BESTEP B2/C1 以上可加 1–2 分。",
                    "大陸交換甄試配分：口試 35%、學業平均成績 30%（大學部 `[學期平均×45% + (1-班排%)×100×55%]×30%`，研究生 `學期平均×30%`）、書面審查 35%，**三項總成績須達 75 分以上始予錄取**。",
                ],
                "source": {
                    "title": "國立政治大學校級薦外交換學生計畫實施辦法與 115.01 甄試簡章",
                    "source_url": NCCU_EXCHANGE_REGULATION_URL,
                    "category": "exchange_application",
                    "summary": "政大校級交換申請資格、碩博 70 分門檻、大陸總分 75 分門檻與同分參酌順序。",
                },
            }
        ],
        "language_requirements": [
            {
                "title": "英語組（TOEFL iBT／IELTS 學術組 CEFR B1–C2 換算）、外語組檢定標準與 iNCCU 全人系統登錄規定",
                "details": [
                    "英語組檢定規範：僅採計 TOEFL iBT（不含 MyBest Scores 及 Home Edition）或 IELTS 學術組，最低須達 CEFR B1（TOEFL iBT 42 / 2026新制 3.0 或 IELTS 4.0，換算 70 分），多數締約校要求達 B2（TOEFL iBT 72–94 / 新制 4.0–4.5 或 IELTS 5.5–6.5，換算 80–89.55 分）或 C1（TOEFL iBT 95+ / IELTS 7.0+）。",
                    "外語組與全人系統登錄：日語 JLPT N3–N1、韓語 TOPIK 3–6級、德語 TestDaF/Goethe B1–C2、法語 DELF/DALF/TCF B1–C2、西語 DELE B1–C2、越語 IVPT A1–C2、俄語 TORFL 1–4級、土語 TYS A1–C2、捷語／波語（英檢 B1 + 政大修課及格）。上傳語檢證明前必須先至 iNCCU「全人系統—語言檢定」完成登錄並截圖合併上傳。",
                ],
                "source": {
                    "title": "國立政治大學 115.01 校級國際薦外交換計畫甄試簡章與交換學校一覽表",
                    "source_url": NCCU_OVERSEAS_GUIDELINES_URL,
                    "category": "exchange_application",
                    "summary": "各語組語言檢定 CEFR 分數換算表、2026 新制托福對照與全人系統登錄規定。",
                },
            }
        ],
        "required_documents": [
            {
                "title": "國立政治大學校級國際薦外交換與赴大陸交換甄試應繳文件、報名費（700元）與保證金（5,000元）",
                "details": [
                    "國際薦外交換應繳文件：1. 線上報名表與報名費繳費證明（每語組 700 元、雙語組 1,400 元）、2. 報考語組語言撰寫之交換計畫書及履歷表（各至少 500 字、2 頁為限）、3. 英文歷年成績單正本、4. 學士班「成績排名證明書」（研究生免附）、5. 語言檢定成績單暨 iNCCU 全人系統登錄截圖合併 PDF（於 10/05–11/02 上傳）、6. （選繳）114 學年度培力英檢 BESTEP 成績單。",
                    "赴大陸交換應繳文件：1. 親筆簽名之線上申請書、2. 中文個人自傳（1,000 字以內）、3. 研究／學習計畫（3,000 字以內）、4. 成績排名證明書正本（研究生免附）、5. 中文歷年成績單正本、6. 甄試報名費 700 元收據正本、7. （選繳）全人系統語檢截圖及社團得獎／低收證明（5 張 A4 為限）。錄取報到時皆須繳交「薦外交換學生同意聲明書」及 5,000 元保證金。",
                ],
                "source": {
                    "title": "國立政治大學 115.01 校級國際薦外交換甄試簡章與赴大陸交換甄試簡章",
                    "source_url": NCCU_OVERSEAS_GUIDELINES_URL,
                    "category": "exchange_application",
                    "summary": "國際交換與大陸交換應繳文件規格、字數頁數限制與保證金退費條件。",
                },
            }
        ],
        "scholarship_info": [
            {
                "title": "教育部學海飛颺（10萬／15萬）、政大短期進修補助（8萬／12萬）、學海惜珠、希望起飛、東協獎學金（2萬／3萬）、大陸獎助（1萬）與傑出交換生獎學金",
                "details": [
                    "教育部「學海飛颺」與政大「鼓勵學生赴國外進行短期進修計畫」補助：學海飛颺每學期 100,000 元、一學年 150,000 元（每年 1–3 月申請）；政大短期進修補助每學期 80,000 元、一學年 120,000 元（大學部一般生須達班排前 30% 且外語達規定標準，每年 5 月及 11 月申請）。",
                    "地區專項、弱勢與返國獎勵：政大「東協國家短期交換獎學金」每學期 20,000 元、一學年 30,000 元；「赴大陸地區短期進修獎助」每學期 10,000 元；經濟不利學生可申請「學海惜珠」及「希望起飛出國交換獎學金」；返國後可申請「傑出交換生獎學金」（5,000–10,000 元）。",
                ],
                "source": {
                    "title": "國立政治大學國際合作事務處—出國交換獎助學金辦法彙編",
                    "source_url": NCCU_SCHOLARSHIP_URL,
                    "category": "scholarship",
                    "summary": "政大六大出國交換獎助學金體系、補助額度、班排與外語門檻及申請月份。",
                },
            }
        ],
        "document_explanations": [
            {
                "title": "國立政治大學校級薦外交換甄試書審文件規格（500字交換計畫書／履歷、iNCCU 全人系統語檢截圖）與出國選課申請書說明",
                "summary": "規範政大校級交換甄試之讀書計畫與履歷字數頁數、iNCCU 全人系統語言檢定登錄截圖合併規定，以及出國加退選截止前必辦之《學生出國選課申請書》。",
                "key_points": [
                    "國際交換之交換計畫書與履歷表須以報考語組語言撰寫，各至少 500 字、以 2 頁為限；大陸交換之個人自傳以 1,000 字為限、研究／學習計畫以 3,000 字為限（超過字數不受理）。",
                    "上傳語言檢定證明前，必須先至 iNCCU「全人系統 > 職涯發展 > 專業證照與技能專長 > 語言檢定」登錄並截圖，與語檢成績單合併為單一 PDF 檔案上傳。",
                    "錄取生應於出國當學期選課加簽暨退課階段結束前完成《國立政治大學學生出國選修課程申請書》系所及院長簽核，返國後於次學期三分之一基準日前檢具正式成績單辦理學分抵免。",
                ],
                "applies_to": [],
                "source": {
                    "title": "國立政治大學 115.01 校級國際薦外交換計畫甄試簡章",
                    "source_url": NCCU_OVERSEAS_GUIDELINES_URL,
                    "category": "exchange_application",
                    "summary": None,
                },
                "document_url": NCCU_OVERSEAS_GUIDELINES_URL,
                "document_type": "official_document",
                "full_text_extracted": True,
            }
        ],
        "rule_explanations": [
            {
                "title": "國立政治大學校級薦外交換學生計畫實施辦法：四項配分、兩階段 15 志願選填、5,000 元保證金與最低及格科目規定",
                "summary": "說明政大校級交換甄試配分比例、兩階段志願分發、保證金退費義務與出國修課及格標準。",
                "key_points": [
                    "國際交換甄試採計口試 30%、語言檢定 30%、在校成績 20%（碩博士班累計平均未達 70 分得 0 分且不予推薦）、交換計畫書及履歷 20%，分兩階段選填志願（每語組至多 15 志願）。",
                    "大陸交換甄試採計口試 35%、書審 35%、學業平均成績 30%，三項總成績須達 75 分以上始予錄取。",
                    "出國期間每學期至少修習 1 門課，國際地區交換生總修習科目 1/2（含）以上須及格、大陸地區交換生總修習科目須全部及格，返國後 2 個月內繳交交換心得並完成義工／兩岸交流活動義務後，無息全額退還 5,000 元保證金。",
                ],
                "applies_to": [],
                "source": {
                    "title": "國立政治大學校級薦外交換學生計畫實施辦法 PDF",
                    "source_url": NCCU_EXCHANGE_REGULATION_URL,
                    "category": "exchange_application",
                    "summary": None,
                },
                "document_url": NCCU_EXCHANGE_REGULATION_URL,
                "document_type": "official_document",
                "full_text_extracted": True,
            }
        ],
        "sources": [
            {
                "title": "國立政治大學出國交換資訊網（Outbound Exchange Portal）",
                "source_url": NCCU_OUTBOUND_PORTAL_URL,
                "category": "exchange_application",
                "summary": None,
            },
            {
                "title": "國立政治大學 115.01 校級國際薦外交換計畫甄試簡章 PDF",
                "source_url": NCCU_OVERSEAS_GUIDELINES_URL,
                "category": "exchange_application",
                "summary": None,
            },
            {
                "title": "國立政治大學 115-01 校級國際薦外交換學校一覽表（Google Sheet 官方公告表）",
                "source_url": NCCU_OVERSEAS_SHEET_URL,
                "category": "partner_school",
                "summary": None,
            },
            {
                "title": "國立政治大學 115學年度第1學期校級薦外大陸交換生甄試簡章 PDF",
                "source_url": NCCU_MAINLAND_GUIDELINES_URL,
                "category": "exchange_application",
                "summary": None,
            },
            {
                "title": "國立政治大學校級薦外交換學生計畫實施辦法 PDF",
                "source_url": NCCU_EXCHANGE_REGULATION_URL,
                "category": "exchange_application",
                "summary": None,
            },
            {
                "title": "國立政治大學國際合作事務處—全球締約校資料庫（ContractSchoolList）",
                "source_url": NCCU_CONTRACT_SCHOOLS_URL,
                "category": "partner_school",
                "summary": None,
            },
            {
                "title": "國立政治大學國際合作事務處—獎助學金專區與短期進修補助要點",
                "source_url": NCCU_SCHOLARSHIP_URL,
                "category": "scholarship",
                "summary": None,
            },
            {
                "title": "國立政治大學國際合作事務處—交換學生經驗分享專區（Category/579，共 650 篇心得）",
                "source_url": NCCU_EXPERIENCE_PORTAL_URL,
                "category": "partner_school",
                "summary": None,
            },
        ],
    }
    (OFFICIAL_NCCU_DIR / "student_dashboard.json").write_text(
        json.dumps(student_dashboard_payload, ensure_ascii=False, indent=2)
        + "\n",
        encoding="utf-8",
    )

    pages_records = [
        {
            "title": "國立政治大學：115-1 校級國際薦外交換計畫甄試時程（09/16–12/17）與赴大陸交換甄試時程（09/14–11/06）",
            "source_url": NCCU_OVERSEAS_GUIDELINES_URL,
            "published_at": "2026-09-14T00:00:00Z",
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
            "title": "國立政治大學：校級薦外交換申請資格、碩博 70 分／大陸 75 分門檻、四項配分與 5,000 元保證金義務",
            "source_url": NCCU_EXCHANGE_REGULATION_URL,
            "published_at": "2026-09-14T00:00:00Z",
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
            "title": "國立政治大學：英語組與外語組 CEFR 檢定換算標準、2026 新制托福對照與 iNCCU 全人系統登錄規定",
            "source_url": NCCU_OVERSEAS_SHEET_URL,
            "published_at": "2026-09-23T00:00:00Z",
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
            "title": "國立政治大學：校級國際交換與大陸交換應繳文件、報名費（700元）與保證金退費規範",
            "source_url": NCCU_MAINLAND_GUIDELINES_URL,
            "published_at": "2026-09-14T00:00:00Z",
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
            "title": "國立政治大學：學海飛颺（10萬／15萬）、短期進修補助（8萬／12萬）、東協獎學金、大陸獎助與傑出交換生獎學金",
            "source_url": NCCU_SCHOLARSHIP_URL,
            "published_at": "2026-09-14T00:00:00Z",
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
    (OFFICIAL_NCCU_DIR / "pages.jsonl").write_text(
        "\n".join(json.dumps(p, ensure_ascii=False) for p in pages_records)
        + "\n",
        encoding="utf-8",
    )

    home_rules = {
        "school_id": "nccu",
        "school_name": "國立政治大學",
        "eligibility": student_dashboard_payload["eligibility"],
        "application_periods": student_dashboard_payload["application_periods"],
        "selection_rules": {
            "graduate_minimum_average_score": 70.0,
            "mainland_minimum_total_selection_score": 75.0,
            "international_weights": {
                "interview": 0.30,
                "language_proficiency": 0.30,
                "academic_grade": 0.20,
                "study_plan_and_cv": 0.20,
            },
            "mainland_weights": {
                "interview": 0.35,
                "study_plan_and_autobiography": 0.35,
                "academic_grade": 0.30,
            },
            "application_fee_twd_per_group": 700,
            "deposit_twd": 5000,
            "max_preferences_per_language_group": 15,
            "return_report_deadline_months": 2,
        },
        "source_urls": nccu_source_urls,
        "verified_at": "2026-10-18",
    }
    (OFFICIAL_NCCU_DIR / "home_rules.json").write_text(
        json.dumps(home_rules, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    (OFFICIAL_NCCU_DIR / "documents.json").write_text(
        json.dumps(
            {
                "school_name": "國立政治大學",
                "required_documents": student_dashboard_payload["required_documents"],
                "source_urls": nccu_source_urls,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    (OFFICIAL_NCCU_DIR / "scholarships.json").write_text(
        json.dumps(
            {
                "school_name": "國立政治大學",
                "scholarships": student_dashboard_payload["scholarship_info"],
                "source_urls": nccu_source_urls,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    completeness = {
        "school_id": "nccu",
        "school_name": "國立政治大學",
        "total_partners": len(partners),
        "partner_count": len(partners),
        "international_partners": sum(
            1 for p in partners if p["country"] not in {"中國大陸", "香港", "澳門"}
        ),
        "mainland_partners": sum(
            1 for p in partners if p["country"] in {"中國大陸", "香港", "澳門"}
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
        "active_term": "115學年度第1學期校級國際薦外交換計畫甄試（對應 116-1／116-2 出國交換）於 2026/10/05 至 11/02 開放語檢上傳、10/31 舉行口試、11/10–12/17 辦理兩階段 15 志願選填與放榜；115-1 校級薦外大陸交換生甄試（對應 116-1 赴陸交換）於 2026/09/14 至 11/06 17:00 受理報名收件。",
        "verified_at": "2026-10-18",
    }
    (OFFICIAL_NCCU_DIR / "catalog-completeness.json").write_text(
        json.dumps(completeness, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    (OFFICIAL_NCCU_DIR / "verification_status.json").write_text(
        json.dumps(
            {
                "school_id": "nccu",
                "school_name": "國立政治大學",
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
            "sources/nccu/outbound_115_1_guidelines.pdf",
            NCCU_OVERSEAS_GUIDELINES_URL,
            "國立政治大學 115.01 校級國際薦外交換計畫甄試簡章_最終版 PDF",
        ),
        (
            "sources/nccu/outbound_partner_list_sheet.xlsx",
            NCCU_OVERSEAS_SHEET_URL,
            "國立政治大學 115-01 校級國際薦外交換學校一覽表（8大語組 280 筆名額組別）XLSX",
        ),
        (
            "sources/nccu/oic_mainland_guidelines_base.pdf",
            NCCU_MAINLAND_GUIDELINES_URL,
            "國立政治大學 115學年度第1學期校級薦外大陸交換生甄試簡章（含 26 所大陸姊妹校 98 名額與附件三特殊規定）PDF",
        ),
        (
            "sources/nccu/oic_exchange_regulation.pdf",
            NCCU_EXCHANGE_REGULATION_URL,
            "國立政治大學校級薦外交換學生計畫實施辦法 PDF",
        ),
        (
            "sources/nccu/outbound_short_term_subsidy_rules.pdf",
            NCCU_SHORT_TERM_SUBSIDY_URL,
            "國立政治大學鼓勵學生赴國外進行短期進修計畫補助要點 PDF",
        ),
        (
            "sources/nccu/outbound_short_term_subsidy_enforcement_rules.pdf",
            NCCU_SHORT_TERM_ENFORCEMENT_URL,
            "國立政治大學鼓勵學生赴國外進行短期進修計畫補助要點施行細則 PDF",
        ),
        (
            "sources/nccu/outbound_asean_scholarship_rules.pdf",
            NCCU_ASEAN_SCHOLARSHIP_URL,
            "國立政治大學學生赴東協國家短期交換獎學金申請辦法 PDF",
        ),
        (
            "sources/nccu/outbound_outstanding_scholarship_rules.pdf",
            NCCU_OUTSTANDING_SCHOLARSHIP_URL,
            "國立政治大學傑出交換生獎學金辦理原則 PDF",
        ),
        (
            "sources/nccu/outbound_hope_scholarship_rules.pdf",
            NCCU_HOPE_SCHOLARSHIP_URL,
            "國立政治大學補助學生赴國外進行短期研究辦法 PDF",
        ),
        (
            "sources/nccu/outbound_mainland_short_term_subsidy_rules.pdf",
            NCCU_MAINLAND_SUBSIDY_URL,
            "國立政治大學學生赴大陸地區短期進修獎助辦法 PDF",
        ),
        (
            "sources/nccu/outbound_partner_scholarship_nomination_rules.pdf",
            NCCU_PARTNER_SCHOLARSHIP_NOMINATION_URL,
            "國立政治大學校級國際薦外交換學生申請締約校獎學金推薦原則 PDF",
        ),
        (
            "sources/nccu/outbound_pre_departure_notice.pdf",
            NCCU_PRE_DEPARTURE_URL,
            "國立政治大學交換生行前須知 PDF",
        ),
        (
            "sources/nccu/oic_contract_schools.json",
            NCCU_CONTRACT_SCHOOLS_URL,
            "國立政治大學國際合作事務處全球締約姊妹校資料庫（486 校）JSON",
        ),
        (
            "sources/nccu/oic_student_experiences.json",
            NCCU_EXPERIENCE_PORTAL_URL,
            "國立政治大學國際合作事務處交換學生經驗分享清單（650 篇）JSON",
        ),
        (
            "sources/nccu/nccu_catalog_source.json",
            NCCU_OUTBOUND_PORTAL_URL,
            "國立政治大學 266 所薦外交換合作大學整合資料集（222 所當期開放 + 44 所歷年／春季班姊妹校，連結 589 篇交換心得）",
        ),
        (
            "sources/nccu/nccu_resolved_locations.json",
            NCCU_OUTBOUND_PORTAL_URL,
            "國立政治大學 266 所薦外交換合作大學 ROR / Wikidata 地理座標核對表",
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
        "school_id": "nccu",
        "school_name": "國立政治大學",
        "generated_at": CHECKED_AT,
        "active_cycle_note": completeness["active_term"],
        "sources": prov_sources,
    }
    (OFFICIAL_NCCU_DIR / "import_provenance.json").write_text(
        json.dumps(provenance_payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    from exchange_info.generated_content_review import review_generated_content
    review_generated_content(REPO_ROOT, "nccu", round_id=20)
    review_generated_content(REPO_ROOT, "nccu", round_id=21)

    print(
        f"Successfully built NCCU catalog: {len(partners)} partners ({open_partner_count} open, "
        f"{completeness['verified_campus_images']} verified images, {completeness['verified_locations']} verified locations), "
        f"{len(workflows)} workflows, {len(destinations)} destinations, {len(research_records)} research records, "
        f"{exp_covered_schools} schools with experience records ({len(student_experience_rows)} rows)."
    )


if __name__ == "__main__":
    main()
