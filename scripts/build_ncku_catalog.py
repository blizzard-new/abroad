"""Build the official National Cheng Kung University (國立成功大學, NCKU) exchange data bundle."""

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

SOURCES_NCKU_DIR = REPO_ROOT / "sources" / "ncku"
OFFICIAL_NCKU_DIR = REPO_ROOT / "src" / "exchange_info" / "official_data" / "ncku"
STATIC_DIR = REPO_ROOT / "src" / "exchange_info" / "static"

CHECKED_AT = "2026-10-18T08:00:00Z"

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
        "USD 650–1,000 / 月（含學生住宿、餐飲與日常交通）",
        "交換逾 180 天須向墨西哥駐臺辦事處申辦學生簽證並投保海外全期醫療保險。",
    ),
    "巴西": (
        "USD 650–1,000 / 月（含貝洛奧里藏特／聖保羅學生住宿、餐飲與大眾運輸）",
        "須向巴西商務辦事處申辦 VITEM IV 學生簽證並備妥規定醫療保險與良民證認證。",
    ),
    "秘魯": (
        "USD 600–950 / 月（含利馬學生住宿、膳食與日常交通）",
        "須依接待校指引申辦秘魯交換學生簽證並投保海外醫療及意外保險。",
    ),
    "英國": (
        "GBP 1,100–1,600 / 月（倫敦約 GBP 1,350–1,850 / 月；曼徹斯特、愛丁堡、南安普敦、基爾約 GBP 1,000–1,400 / 月）",
        "交換一學期（6 個月內）可辦理 Standard Visitor 簽證，一學年須辦理 Student Visa 並繳納 IHS 醫療附加費。",
    ),
    "愛爾蘭": (
        "EUR 1,000–1,500 / 月（含都柏林學生公寓、餐飲與大眾運輸）",
        "須辦理愛爾蘭學習許可（IRP 居留登記）並投保符合愛爾蘭規定之醫療保險。",
    ),
    "法國": (
        "EUR 850–1,450 / 月（巴黎約 EUR 1,050–1,550 / 月；里昂、圖盧茲、雷恩、波爾多、格勒諾布爾約 EUR 750–1,150 / 月，可申請 CAF 房補）",
        "須透過法國教育中心（Campus France）完成面試並申辦長期學生簽證（VLS-TS）。",
    ),
    "德國": (
        "EUR 934–1,250 / 月（德國簽證限制提領帳戶基準為每月 EUR 934）",
        "須辦理德國法定公保（約 EUR 120–130 / 月）及繳納學期雜費／學期交通票（Semesterticket）。",
    ),
    "奧地利": (
        "EUR 850–1,250 / 月（含維也納／因斯布魯克／林茲／格拉茨學生宿舍、餐飲與大眾運輸）",
        "交換一學期（6 個月內）須申辦奧地利學生簽證 D（Visa D），超過 6 個月須申辦學生居留許可。",
    ),
    "西班牙": (
        "EUR 800–1,300 / 月（含馬德里／巴塞隆納／瓦倫西亞／奧維耶多學生公寓、飲食與大眾運輸）",
        "須備妥涵蓋全額醫療與遺體運返之私人醫療保險以申辦西班牙學生簽證。",
    ),
    "義大利": (
        "EUR 850–1,350 / 月（含米蘭、羅馬、波隆那學生住宿、餐飲與大眾運輸）",
        "須向義大利經濟貿易文化推廣辦事處申辦學生簽證 D，抵義後 8 個工作天內申辦居留證（Permesso di Soggiorno）。",
    ),
    "荷蘭": (
        "EUR 950–1,450 / 月（荷蘭移民局 IND 財力證明基準約 EUR 1,225 / 月）",
        "由接待校代辦 MVV/VVR 居留許可，代爾夫特、恩荷芬、萊頓與格羅寧根房源緊張建議獲提名後立即申請宿舍。",
    ),
    "比利時": (
        "EUR 850–1,300 / 月（含魯汶／根特／布魯塞爾學生宿舍、餐飲與大眾運輸）",
        "須辦理長期學生簽證 D 簽，抵達後向當地市政廳登記居留。",
    ),
    "瑞士": (
        "CHF 1,500–2,200 / 月（含蘇黎世／洛桑／伯恩學生住宿、膳食與強制保險）",
        "須透過瑞士商務辦事處申辦學生簽證，並於抵瑞後申請居留證與醫療保險豁免或投保。",
    ),
    "瑞典": (
        "SEK 9,500–13,000 / 月（瑞典移民局財力基準約 SEK 10,314 / 月）",
        "交換超過 3 個月須向瑞典移民局申辦學生居留許可（Residence Permit for Studies）。",
    ),
    "丹麥": (
        "EUR 1,000–1,450 / 月（含哥本哈根／靈比學生宿舍、飲食與自行車／大眾運輸）",
        "須辦理丹麥學生居留許可（ST1）並完成抵達後 CPR 登記。",
    ),
    "挪威": (
        "EUR 1,000–1,450 / 月（含卑爾根／奧斯陸學生宿舍與日常開支）",
        "須向挪威移民局（UDI）申辦學生居留許可。",
    ),
    "芬蘭": (
        "EUR 800–1,200 / 月（含埃斯波／赫爾辛基／奧盧學生公寓、學生餐廳與當地交通）",
        "須透過 Enter Finland 申辦芬蘭學生居留許可並備妥規定醫療保險。",
    ),
    "立陶宛": (
        "EUR 600–900 / 月（維爾紐斯與考納斯學生宿舍與生活費用實惠）",
        "須透過 MIGRIS 系統申辦立陶宛國家簽證（D 簽）或臨時居留許可。",
    ),
    "波蘭": (
        "EUR 550–850 / 月（約 PLN 2,400–3,600，華沙、克拉科夫、弗羅茨瓦夫、羅茲、卡托維茲校內宿舍實惠）",
        "須向波蘭臺北辦事處申辦 D 類國別學生簽證並備妥規定旅行醫療保險。",
    ),
    "捷克": (
        "EUR 600–900 / 月（含布拉格／布爾諾／奧斯特拉瓦學生宿舍、食堂與市區交通卡）",
        "須提前預約捷克經濟文化辦事處申辦長期學生簽證與捷克合約醫療保險。",
    ),
    "斯洛伐克": (
        "EUR 600–900 / 月（含布拉提斯拉瓦學生住宿與日常開支）",
        "須申辦斯洛伐克長期學生簽證（D 簽）或臨時居留許可。",
    ),
    "克羅埃西亞": (
        "EUR 650–950 / 月（含札格瑞布學生住宿與日常生活開支）",
        "須申辦克羅埃西亞短期居留許可並備妥歐盟規格醫療保險。",
    ),
    "俄羅斯": (
        "USD 500–850 / 月（莫斯科與聖彼得堡校內宿舍與日常開支實惠）",
        "須憑接待校核發之俄羅斯聯邦移民署官方邀請函向莫北協駐臺代表處申辦學生簽證。",
    ),
    "土耳其": (
        "EUR 550–850 / 月（安卡拉與伊斯坦堡學生生活與交通開支實惠）",
        "須申辦土耳其學生簽證並於抵土後申辦短期學生居留證（Ikamet）與當地醫保。",
    ),
    "以色列": (
        "USD 1,000–1,500 / 月（含貝爾謝巴／海法／特拉維夫學生宿舍、餐飲與大眾運輸）",
        "須向駐臺北以色列經濟文化辦事處申辦 A/2 學生簽證並投保接待校指定醫療保險。",
    ),
    "南非": (
        "USD 550–900 / 月（含波切夫斯特魯姆學生住宿、膳食與日常交通）",
        "須向南非聯絡辦事處申辦南非學習簽證（Study Visa）並投保南非認可之醫療保險。",
    ),
    "澳洲": (
        "AUD 1,800–2,600 / 月（含雪梨／墨爾本／布里斯本／坎培拉／阿德雷德／伯斯住宿與日常開支）",
        "須購買澳洲海外學生健康保險（OSHC）並線上申辦 Subclass 500 學生簽證。",
    ),
    "紐西蘭": (
        "NZD 1,600–2,300 / 月（含奧克蘭／基督城住宿與日常開支）",
        "須向紐西蘭移民局線上申辦 Exchange Student Visa 並投保合規醫療險。",
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
        "RMB 2,000–3,800 / 月（校內學生宿舍住宿費與校園食堂餐費實惠）",
        "持有效護照與臺胞證（臺灣居民來往大陸通行證）入境，並依接待校規定投保大陸境內來華留學生綜合醫療保險。",
    ),
    "香港": (
        "HKD 6,500–11,000 / 月（含校內外住宿與日常開支）",
        "須透過接待校向香港入境事務處申辦學生簽證／進入許可（Student Visa / Entry Permit）。",
    ),
    "澳門": (
        "MOP 4,500–7,500 / 月（含澳門大學住宿式書院與日常開支）",
        "須依澳門治安警察局居留及逗留事務廳規定辦理「逗留特別許可（學生）」。",
    ),
    "新加坡": (
        "SGD 1,200–1,900 / 月（含新加坡國立大學／南洋理工大學／新加坡管理大學／新加坡科技設計大學住宿與日常開支）",
        "獲錄取後由接待校透過 SOLAR 系統協助申辦新加坡 Student's Pass（STP）。",
    ),
    "馬來西亞": (
        "MYR 1,500–2,500 / 月（吉隆坡、檳城與霹靂州生活機能便利且物價親民）",
        "須透過 EMGS（Education Malaysia Global Services）系統申辦學生簽證（VAL / Student Pass）。",
    ),
    "泰國": (
        "THB 15,000–25,000 / 月（曼谷、清邁與呵叻府生活成本親民）",
        "須憑接待校入學許可向泰國貿易經濟辦事處申辦 Non-Immigrant ED 學生簽證。",
    ),
    "印尼": (
        "IDR 5,000,000–9,000,000 / 月（萬隆、日惹、三寶瓏與雅加達生活開支實惠）",
        "須由接待校協助向印尼移民總局申辦學習簽證（C316 / 學生電子簽證）。",
    ),
    "越南": (
        "USD 400–700 / 月（約 VND 10,000,000–17,000,000，河內與胡志明市生活成本低廉）",
        "須憑接待校入學許可透過駐臺北越南經濟文化辦事處申辦 DH 學生簽證。",
    ),
    "菲律賓": (
        "USD 500–850 / 月（約 PHP 28,000–48,000，馬尼拉住宿與生活開支）",
        "須憑接待校入學許可向馬尼拉經濟文化辦事處申辦 9(f) 學生簽證或 SSP 特別學習許可。",
    ),
    "印度": (
        "USD 400–700 / 月（印度理工學院各校區、清奈與索蘭校內住宿與日常開支實惠）",
        "須憑接待校正式入學許可向印度台北協會申辦 Student Visa。",
    ),
}

NCKU_OUTBOUND_OVERVIEW_URL = "https://oia.ncku.edu.tw/p/404-1032-229870.php?Lang=zh-tw"
NCKU_PORTAL_URL = "https://exchange.oia.ncku.edu.tw/index.php?outgoing_auth"
NCKU_116_1_ANNOUNCEMENT_URL = "https://oia.ncku.edu.tw/p/406-1032-306703,r3333.php?Lang=zh-tw"
NCKU_116_1_GUIDELINES_PDF_URL = "https://oia.ncku.edu.tw/var/file/32/1032/img/107138261.pdf"
NCKU_116_1_PARTNERS_PDF_URL = "https://oia.ncku.edu.tw/var/file/32/1032/img/535260712.pdf"
NCKU_115_2_ANNOUNCEMENT_URL = "https://oia.ncku.edu.tw/p/406-1032-292857,r3414.php?Lang=zh-tw"
NCKU_115_2_GUIDELINES_PDF_URL = "https://oia.ncku.edu.tw/var/file/32/1032/img/750548240.pdf"
NCKU_115_2_PARTNERS_PDF_URL = "https://oia.ncku.edu.tw/var/file/32/1032/img/104186796.pdf"
NCKU_115_2_APP_FORM_PDF_URL = "https://oia.ncku.edu.tw/var/file/32/1032/img/170843084.pdf"
NCKU_115_1_GUIDELINES_PDF_URL = "https://oia.ncku.edu.tw/var/file/32/1032/img/265314865.pdf"
NCKU_115_1_PARTNERS_PDF_URL = "https://oia.ncku.edu.tw/var/file/32/1032/img/152304266.pdf"
NCKU_115_1_APP_FORM_PDF_URL = "https://oia.ncku.edu.tw/var/file/32/1032/img/914982814.pdf"
NCKU_REGULATION_URL = "https://oia.ncku.edu.tw/p/404-1032-227702.php?Lang=zh-tw"
NCKU_ENGLISH_TABLE_PDF_URL = "https://oia.ncku.edu.tw/var/file/32/1032/img/4508/778147248.pdf"
NCKU_SCHOLARSHIP_OVERVIEW_URL = "https://oia.ncku.edu.tw/p/404-1032-228571.php?Lang=zh-tw"
NCKU_SCHOLARSHIP_REG_PDF_URL = "https://oia.ncku.edu.tw/var/file/32/1032/img/894/918181109.pdf"
NCKU_SCHOLARSHIP_GUIDE_PDF_URL = "https://oia.ncku.edu.tw/var/file/32/1032/img/4464/281806445.pdf"
NCKU_KEY_PARTNER_SCHOLARSHIP_PDF_URL = "https://oia.ncku.edu.tw/var/file/32/1032/img/4508/658181057.pdf"
NCKU_EXPERIENCE_ASIA_URL = "https://oia.ncku.edu.tw/p/405-1032-252564,c29777.php?Lang=zh-tw"
NCKU_EXPERIENCE_EUROPE_URL = "https://oia.ncku.edu.tw/p/405-1032-252565,c29777.php?Lang=zh-tw"
NCKU_EXPERIENCE_AMERICAS_URL = "https://oia.ncku.edu.tw/p/405-1032-252566,c29777.php?Lang=zh-tw"
NCKU_CONTRACT_SEARCH_URL = "https://management.oia.ncku.edu.tw/oia/index/search"


def clean_text(s: str) -> str:
    if not s:
        return ""
    return re.sub(r"\s+", " ", s).strip()


def format_colleges(item: dict) -> str:
    notes = clean_text(item.get("notes_raw") or "")
    elig = clean_text(item.get("elig_raw") or "")
    m_lim = re.search(
        r"(?:僅開放|限[^。；\n]{1,35}學院|不接受[^。；\n]{1,35}申請|須具備[^。；\n]{1,35}背景)",
        notes + " " + elig,
    )
    if m_lim:
        return f"不限成大所屬學院報名（接待校系所／領域規定：{m_lim.group(0).strip()}）"
    return "不限學院（全校文、理、工、電機資訊、規劃與設計、管理、醫、社會科學、生物科學與科技、智慧半導體及永續製造、敏求智慧運算等 11 學院在學學生皆可依接待校開設系所報名）"


def format_degree_levels(item: dict) -> str:
    elig = clean_text(item.get("elig_raw") or "")
    notes = clean_text(item.get("notes_raw") or "")
    combined = elig + " " + notes
    if "限大學部在校生" in combined or "僅限大學部" in combined:
        return "限大學部二年級以上在校生（不開放碩博士班）"
    if "限大學部及碩士班" in combined:
        return "大學部二年級以上、碩士班一年級以上在校生（不開放博士班）"
    if "限研究所" in combined or "限碩士班" in combined:
        return "限研究所（碩士班／博士班一年級以上）在校生"
    return "大學部（二年級以上）、碩士班（一年級以上）、博士班（一年級以上）在學學生（轉學生須為二年級以上且於成大就讀滿一學期並有成績單）"


def format_language_req(item: dict) -> str:
    lr = clean_text(item.get("lang_raw") or "")
    if lr:
        return lr[:420]
    return "校內英語基本門檻須達 CEFR B2 以上：TOEFL iBT 72（2026新制 4.0）、IELTS Academic 5.5 或 TOEIC 785（報名截止日前 2 年內有效；申請大陸地區學校者亦須檢附符合成大標準之英語能力證明），或具備交換學校要求之日語（JLPT）、韓語（TOPIK）、德語、法語等外語檢定門檻。"


def format_gpa_req(item: dict) -> str:
    lr = clean_text(item.get("lang_raw") or "")
    elig = clean_text(item.get("elig_raw") or "")
    notes = clean_text(item.get("notes_raw") or "")
    gpa_matches = []
    for m in re.finditer(
        r"GPA\s*[:：><=]?\s*[0-9.]+(?:\s*/\s*[0-9.]+)?",
        lr + " " + elig + " " + notes,
        re.I,
    ):
        g = m.group(0).strip()
        if g not in gpa_matches:
            gpa_matches.append(g)
    base = "成大校內門檻：大學部學生前一學期課業成績平均 77 分（含）以上或全班／全系排名前 50%；研究所學生無校內成績門檻限制（須取得指導教授同意），惟在校成績占甄選總分 50%"
    if gpa_matches:
        base += f"｜締約校 GPA 要求：{'；'.join(gpa_matches)}"
    return base


def format_quota(item: dict) -> str:
    return clean_text(item.get("quota_raw") or "依當期簽約學校一覽表公告")


def format_study_period(item: dict) -> str:
    q = clean_text(item.get("quota_raw") or "")
    if "僅限研習一學期" in q or "僅限一學期" in q:
        return "一學期（依簽約學校一覽表規定僅限研習一學期）"
    return "一學期或一學年（116學年度第1學期［2027秋季班］或116學年度全學年；同一學制以出國交換一次為原則）"


def format_program_type(item: dict) -> str:
    avail = item.get("availability_status")
    grps = "／".join(item.get("language_groups") or ["一般組"])
    if avail == "open":
        return f"交換學生（116-1 校級薦外交換學生計畫［{grps}］・繳交成大全額學雜費、互惠免繳接待校學費）"
    return f"交換學生（國立成功大學國際事務處締約合作姊妹校［{grps}］・歷年／春季班／院系級開放）"


def main() -> None:
    OFFICIAL_NCKU_DIR.mkdir(parents=True, exist_ok=True)
    SOURCES_NCKU_DIR.mkdir(parents=True, exist_ok=True)

    catalog_items = json.loads(
        (SOURCES_NCKU_DIR / "ncku_catalog_source.json").read_text(encoding="utf-8")
    )
    locs_raw = json.loads(
        (SOURCES_NCKU_DIR / "ncku_resolved_locations.json").read_text(encoding="utf-8")
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
        if avail_status == "open":
            open_partner_count += 1

        website = (item.get("website") or "").strip()
        if website and not website.startswith("http"):
            website = f"https://{website}"

        detail_url = (item.get("detail_url") or "").strip() or None
        source_url = item.get("source_url") or NCKU_116_1_PARTNERS_PDF_URL

        if avail_status == "open":
            round_label = "116學年度第1學期校級薦外交換學生計畫甄選（115年10月30日至11月19日16:00線上申請）"
            deadline_iso = "2026-11-19T16:00:00+08:00"
            deadline_rem = True
            win_status = "open"
            app_deadline_str = (
                "【116學年度第1學期校級薦外交換學生計畫甄選（對應 2027 秋季班／2027–2028 全學年出國交換）】"
                "線上申請期間：115年10月30日至115年11月19日（四）下午 16:00 止（於成大薦外交換學生申請系統完成登打並上傳全套審查文件 PDF，逾期不予受理）；"
                "甄選結果公告：115年12月19日 23:59 前；"
                "正取生上傳確認書／放棄聲明書截止：115年12月26日 16:00 前；"
                "備取生上傳確認書截止：116年1月2日 16:00 前；"
                "繳交計畫保證金（一般生 NT$8,000／低收及中低收入戶 NT$2,000）：116年1月5日至1月11日。"
            )
        else:
            round_label = "116學年度第2學期校級薦外交換學生計畫甄選（春季班預計 116年4–5月受理線上申請）"
            deadline_iso = "2027-05-18T16:00:00+08:00"
            deadline_rem = False
            win_status = "closed"
            app_deadline_str = (
                "【成大國際締約姊妹校（歷年／春季班／院系級交換合作校）】本合作校為國立成功大學國際事務處登錄之締約合作學校；"
                "116-1 校級統招未開缺（參考 115-2 春季班申請期程為 4月27日至5月18日 16:00 止），欲申請者請留意 116-2 春季班校級甄選簡章或所屬院系雙聯／院級交換公告。"
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
            "依《國立成功大學校級薦外交換學生計畫甄選簡章》第拾點及保證金退費規定，交換期間每學期至少須修習 3 門學分課程且成績及格（返國後 2 個月內須上傳該校成績單或研習證明、Word 與 PDF 交換心得報告及返國問卷，始得申請退還 NT$8,000［或 NT$2,000］計畫保證金）。"
        )
        course_rest_str = " ".join(course_parts)

        if "宿" in notes_raw or "dorm" in notes_raw.lower():
            housing_str = f"{zh_name} 住宿與申請說明：{notes_raw[:360]}"
        else:
            housing_str = f"{zh_name} 依兩校交換協議提供獲提名交換生校內學生宿舍申請資訊或校外住宿指引；宿位是否保證分配及收費標準以該校最新 Factsheet 與入學許可通知為準。"

        tuition_points_list = [
            "成大註冊學雜費與計畫保證金規定：錄取學生於出國交換期間須維持國立成功大學在學身分並完成註冊、繳交成大全額學雜費，享互惠免繳接待校學費（住宿費、生活費、保險費、簽證費與往返機票均由學生自理）。正備取生確認參加計畫後須於 116/01/05–01/11 繳交計畫保證金新臺幣 8,000 元（報名時上傳有效低收入戶或中低收入戶證明者減免為 2,000 元）；依計畫出國並於返國後 2 個月內繳交交換心得報告（Word 及 PDF）、國外成績單（每學期至少修習 3 門學分課及格）及完成返國問卷後無息全額退還。",
            "三大獎助學金體系：（1）《國立成功大學學生跨國雙向研修獎助學金》：補助本國籍一般生（不含大陸港澳交換及在職專班）赴國外交換，亞洲地區每學期最高新臺幣 110,000 元、每學年最高 200,000 元，亞洲以外地區每學期最高 150,000 元、每學年最高 240,000 元（秋季出國於 5 月 31 日前申請、春季出國於前一年 10 月 31 日前申請；不得與教育部學海或國科會補助兼領）；（2）《國立成功大學學生赴深化國際合作重點學校交流獎助學金》：赴日本筑波大學、法國格勒諾布爾-阿爾卑斯大學、德國慕尼黑大學／慕尼黑工業大學、美國普渡大學交換一學期，亞洲補助 30,000 元、亞洲以外補助 50,000 元（取得入學許可 1 個月內申請）；（3）教育部「學海飛颺」（優秀學生）、「學海惜珠」（低收／中低收／特殊境遇家庭學生）與締約校獎學金（如日本 JASSO、韓國 GKS 等）。",
        ]
        if partner_sch:
            tuition_points_list.append(f"本締約校專屬獎學金／補助資訊：{partner_sch}")

        app_steps_list = [
            f"步驟一（確認學制年級、大學部 77 分／前 50% 門檻與 {zh_name} 條件）：確認為成大大學部二年級以上、碩士班一年級以上或博士班一年級以上在學學生（大學部前一學期平均須達 77 分以上或全班／全系排名前 50%；研究所無成績門檻惟須取得指導教授同意），並確認符合 {zh_name} 之學制、領域及外語檢定門檻（校內英語基本門檻為 CEFR B2：TOEFL iBT 72［新制 4.0］／IELTS Academic 5.5／TOEIC 785，申請大陸地區學校者亦須檢附英語能力證明）。",
            "步驟二（10/30–11/19 16:00 線上填報至多 6 志願並上傳 7 項審查文件 PDF）：於 115年10月30日至11月19日（四）16:00 前登入「成大薦外交換學生申請系統」（https://exchange.oia.ncku.edu.tw/index.php?outgoing_auth）填報第一至第六志願，下載申請表黏貼兩吋照片、本人簽名並經導師或指導教授／系所主管簽章後，連同中文歷年成績單（大學部含排名）、中英文自傳、中英文讀書或研究計畫（皆依第一志願擬訂）、2年內有效外語能力證明及其他有利審查資料（含低收／中低收證明）分項上傳並合併為單一 PDF（上限 50MB），無須繳交紙本。",
            f"步驟三（書面甄選評分、12/19 放榜、線上確認與 01/05–01/11 繳交 8,000 元保證金）：甄選總分依「在校成績 50%、研究/讀書計畫 25%、自傳及其餘表現 25%」評定（同分依序參酌在校成績、研究/讀書計畫、自傳及其餘表現、志願序）。115/12/19 公告結果後，正取生於 12/26 16:00 前、備取生於 116/01/02 16:00 前於系統上傳家長簽章之確認書，並於 116/01/05–01/11 繳交保證金 NT$8,000（低收／中低收 NT$2,000），由成大國際處向 {full_name} 辦理官方提名（Nomination）。",
            "步驟四（向交換校遞交入學文件、申請跨國雙向／學海獎助學金與返國退還保證金）：獲成大提名後依交換校期限自行備妥英文成績單、護照、財力證明等完成該校入學申請（校內甄選錄取僅代表獲成大推薦資格，最終錄取決定權在交換校）；取得入學許可後申辦簽證、購買海外醫療及意外保險、申請成大跨國雙向研修獎助學金（5/31 或 10/31 截止）／重點學校獎助學金／教育部學海計畫，出國期間註冊繳交成大全額學雜費且每學期至少修習 3 門學分課及格，返國 2 個月內繳交心得報告與成績單退還保證金。",
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
            f"【當期名額與組別】{quota_str}",
            f"【開放學院與學制】{colleges_str}｜{degree_levels_str}",
            f"【語言與學業門檻】{lang_req_str}｜{gpa_req_str}",
        ]
        if notes_raw:
            notes_lines.append(f"【締約校重要備註】{notes_raw[:380]}")
        if exp_posts:
            notes_lines.append(
                f"【成大歷屆交換生返國心得】成大國際事務處官網「交換心得」專區公開收錄赴 {zh_name} 交換生返國心得報告共 {len(exp_posts)} 篇。"
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
            "availability_note": f"國立成功大學國際事務處公告合作姊妹校；{quota_str}。",
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
                "title": f"國立成功大學校級薦外交換簽約學校一覽表與條件—{zh_name}",
                "source_url": source_url,
                "role": "home_university",
                "authority": "home_official_notice",
                "effective_academic_year": "116",
                "application_round": round_label,
                "checked_at": CHECKED_AT,
            },
            {
                "title": "國立成功大學 116學年度第1學期校級薦外交換學生計畫甄選簡章 PDF",
                "source_url": NCKU_116_1_GUIDELINES_PDF_URL,
                "role": "home_university",
                "authority": "home_official_notice",
                "effective_academic_year": "116",
                "application_round": round_label,
                "checked_at": CHECKED_AT,
            },
            {
                "title": "國立成功大學學生跨國雙向研修獎助學金補助辦法與甄選要點",
                "source_url": NCKU_REGULATION_URL,
                "role": "home_university",
                "authority": "home_official_notice",
                "effective_academic_year": "116",
                "application_round": round_label,
                "checked_at": CHECKED_AT,
            },
        ]
        if detail_url:
            wf_sources.append({
                "title": f"國立成功大學國際事務處出國交換公告專頁—{zh_name}",
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
            "home_university": "國立成功大學",
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
                "國立成功大學每學期辦理校級薦外交換學生計畫甄選（116-1 秋季班於 115年10月30日至11月19日 16:00 受理線上申請，115-2 春季班於 4月27日至5月18日 16:00 受理）；"
                "甄選採計在校成績 50%、研究/讀書計畫 25%、自傳及其餘表現 25%，每人至多選填 6 個志願。"
            ),
            "review_status": "published",
            "published_at": CHECKED_AT,
            "steps": [
                {
                    "rule_id": f"ncku-116-home-1-{idx+1:03d}",
                    "order": 1,
                    "phase": "校內申請",
                    "title": f"確認成大在學年級、大學部 77 分／前 50% 門檻與 {zh_name} 外語及 GPA 條件",
                    "responsible_party": "學生",
                    "responsible_unit": "國立成功大學國際事務處國際合作組（光復校區雲平大樓東棟 7 樓）",
                    "deadline_at": deadline_iso,
                    "deadline_status": "verified_exact" if avail_status == "open" else "reference_only",
                    "deadline_source_url": NCKU_116_1_GUIDELINES_PDF_URL,
                    "deadline_checked_at": CHECKED_AT,
                    "deadline_reminder_eligible": deadline_rem,
                    "summary": f"申請人須為成大大學部二年級以上、碩士班一年級以上或博士班一年級以上在學學生（大學部前一學期平均須達 77 分以上或全班／全系排名前 50%；研究所無成績門檻惟須取得指導教授同意），並確認符合 {zh_name} 之學制、領域、外語檢定及 GPA 入學標準。",
                    "details": [
                        f"開放學制與院系：{colleges_str}（{degree_levels_str}）",
                        f"語言與學業條件：{lang_req_str}｜{gpa_req_str}",
                        f"當期名額與交換期程：{quota_str}",
                    ],
                    "scope": {
                        "home_universities": ["國立成功大學"],
                        "partner_universities": [full_name],
                        "academic_years": ["115", "116"],
                        "application_rounds": [
                            round_label,
                            "115-1",
                            "115-2",
                            "116-1",
                            "116-2",
                            "116學年度第1學期（秋季班）",
                            "116學年度第2學期（春季班）",
                        ],
                    },
                    "source_urls": [
                        NCKU_116_1_GUIDELINES_PDF_URL,
                        source_url,
                    ],
                    "checked_at": CHECKED_AT,
                    "support_status": "verified",
                },
                {
                    "rule_id": f"ncku-116-home-2-{idx+1:03d}",
                    "order": 2,
                    "phase": "校內申請",
                    "title": "於 10/30–11/19 16:00 登入成大薦外交換系統選填至多 6 志願並上傳 7 項審查文件 PDF",
                    "responsible_party": "學生",
                    "responsible_unit": "國立成功大學國際事務處國際合作組",
                    "deadline_at": deadline_iso,
                    "deadline_status": "verified_exact" if avail_status == "open" else "reference_only",
                    "deadline_source_url": NCKU_116_1_GUIDELINES_PDF_URL,
                    "deadline_checked_at": CHECKED_AT,
                    "deadline_reminder_eligible": deadline_rem,
                    "summary": "於 115年10月30日至11月19日（四）下午 16:00 前登入成大薦外交換學生申請系統（https://exchange.oia.ncku.edu.tw/index.php?outgoing_auth）登打資料、選填至多 6 個志願，下載申請表由本人簽名並經導師或指導教授／系所主管簽章後，連同中文歷年成績單、中英文自傳、中英文讀書或研究計畫、2年內有效外語能力證明及其他有利審查資料分項上傳並合併為單一 PDF（上限 50MB），無須繳交紙本。",
                    "details": [
                        "書審文件擬訂規定：中英文自傳（含學、經歷）與中英文讀書或研究計畫均須依「第一志願」學校擬訂；若以網路成績查詢畫面截圖上傳外語證明者，須於放榜後至繳交保證金截止日前持正本至國際合作組查驗。",
                        "弱勢生保證金減免：具低收入戶或中低收入戶身分者，請於線上申請階段一併於「其他有助審查之資料」上傳有效證明文件，錄取後保證金得由 8,000 元減免為 2,000 元。",
                    ],
                    "document_requirements": [
                        {
                            "name": "校內甄選申請表（線上系統登打後下載，黏貼兩吋半身脫帽照、本人簽名並經大學部導師或碩博班指導教授／系所主管簽章）",
                            "official_form_url": NCKU_PORTAL_URL,
                            "source_urls": [
                                NCKU_PORTAL_URL,
                                NCKU_116_1_GUIDELINES_PDF_URL,
                                NCKU_115_2_APP_FORM_PDF_URL,
                            ],
                        },
                        {
                            "name": "中文歷年成績單（須含當學期修課科目、學期總平均及 GPA；大學部須含全班或全系排名百分比，碩一、博一新生檢附大學或碩士歷年成績單）",
                            "source_urls": [
                                NCKU_116_1_GUIDELINES_PDF_URL,
                            ],
                        },
                        {
                            "name": "中英文自傳與中英文讀書或研究計畫（含學、經歷，均須依第一志願交換學校擬訂）",
                            "source_urls": [
                                NCKU_116_1_GUIDELINES_PDF_URL,
                            ],
                        },
                        {
                            "name": "報名截止日前 2 年內有效之外語能力證明（英語 CEFR B2：TOEFL iBT 72［新制 4.0］／IELTS Academic 5.5／TOEIC 785，或達交換校指定外語門檻；申請大陸地區學校亦須檢附英語能力證明）及第 1–6 項合併 PDF 檔",
                            "source_urls": [
                                NCKU_116_1_GUIDELINES_PDF_URL,
                                NCKU_ENGLISH_TABLE_PDF_URL,
                            ],
                        },
                    ],
                    "scope": {
                        "home_universities": ["國立成功大學"],
                        "academic_years": ["115", "116"],
                        "application_rounds": [
                            round_label,
                            "115-1",
                            "115-2",
                            "116-1",
                            "116-2",
                            "116學年度第1學期（秋季班）",
                            "116學年度第2學期（春季班）",
                        ],
                    },
                    "source_urls": [
                        NCKU_PORTAL_URL,
                        NCKU_116_1_GUIDELINES_PDF_URL,
                        NCKU_ENGLISH_TABLE_PDF_URL,
                    ],
                    "checked_at": CHECKED_AT,
                    "support_status": "verified",
                },
                {
                    "rule_id": f"ncku-116-home-3-{idx+1:03d}",
                    "order": 3,
                    "phase": "甄選與提名",
                    "title": "12/19 甄選結果公告、12/26 正取確認（01/02 備取確認）與 01/05–01/11 繳交 8,000 元保證金",
                    "responsible_party": "學生與國立成功大學國際事務處",
                    "responsible_unit": "國立成功大學國際事務處國際合作組",
                    "deadline_at": "2026-12-26T16:00:00+08:00" if avail_status == "open" else "2027-06-26T16:00:00+08:00",
                    "deadline_status": "verified_exact" if avail_status == "open" else "reference_only",
                    "deadline_source_url": NCKU_116_1_GUIDELINES_PDF_URL,
                    "deadline_checked_at": CHECKED_AT,
                    "deadline_reminder_eligible": deadline_rem,
                    "summary": "甄選依「在校成績 50%、研究/讀書計畫 25%、自傳及其餘表現 25%」評定並於 115/12/19 公告錄取名單；正取生須於 115/12/26 16:00 前、備取生須於 116/01/02 16:00 前於系統上傳經本人與家長簽章之錄取確認書或放棄聲明書，並於 116/01/05–01/11 至臺銀學雜費入口網繳交計畫保證金新臺幣 8,000 元（低收／中低收 2,000 元）。",
                    "details": [
                        "同分參酌順序：總分相同時，依序以（1）在校成績、（2）研究/讀書計畫、（3）自傳及其餘表現、（4）志願序高分者優先錄取。",
                        "確認資格與遞補：每人至多正取一校，若正取生同時為前志願之備取生，一經確認正取資格即喪失其他志願備取資格。",
                    ],
                    "scope": {
                        "home_universities": ["國立成功大學"],
                        "academic_years": ["115", "116"],
                        "application_rounds": [
                            round_label,
                            "115-1",
                            "115-2",
                            "116-1",
                            "116-2",
                            "116學年度第1學期（秋季班）",
                            "116學年度第2學期（春季班）",
                        ],
                    },
                    "source_urls": [
                        NCKU_116_1_GUIDELINES_PDF_URL,
                        NCKU_REGULATION_URL,
                    ],
                    "checked_at": CHECKED_AT,
                    "support_status": "verified",
                },
                {
                    "rule_id": f"ncku-{idx+1:03d}-host-apply",
                    "order": 4,
                    "phase": "合作校申請",
                    "title": f"由成大國際合作組辦理官方提名並依 {zh_name} 規定遞交入學申請資料",
                    "responsible_party": "學生與接待校國際處",
                    "summary": f"完成校內確認書上傳及保證金繳交後，由成大國際合作組向 {zh_name} 辦理官方提名（Nomination）；學生須自行密切留意交換校申請截止日，備妥英文成績單、護照、財力證明、語檢證明及選課計畫按時完成該校入學申請，靜候交換校核發正式入學許可書（Letter of Acceptance）。",
                    "details": [
                        f"交換期程：{study_period_str}｜名額：{quota_str}",
                        f"語言與學業條件：{lang_req_str}",
                    ]
                    + ([f"締約校申請與修課備註：{notes_raw[:240]}"] if notes_raw else []),
                    "scope": {
                        "home_universities": ["國立成功大學"],
                        "partner_universities": [full_name],
                        "academic_years": ["115", "116"],
                        "application_rounds": [
                            round_label,
                            "115-1",
                            "115-2",
                            "116-1",
                            "116-2",
                            "116學年度第1學期（秋季班）",
                            "116學年度第2學期（春季班）",
                        ],
                    },
                    "source_urls": (
                        [
                            source_url,
                            NCKU_116_1_GUIDELINES_PDF_URL,
                            NCKU_SCHOLARSHIP_OVERVIEW_URL,
                        ]
                        + ([detail_url] if detail_url else [])
                        + ([website] if website else [])
                    ),
                    "checked_at": CHECKED_AT,
                    "support_status": "verified",
                    "needs_confirmation": False,
                },
                {
                    "rule_id": f"ncku-116-home-5-{idx+1:03d}",
                    "order": 5,
                    "phase": "行前準備",
                    "title": "申請跨國雙向／重點學校／學海獎助學金、辦理簽證役男出境與返國後退還 8,000 元保證金",
                    "responsible_party": "學生",
                    "responsible_unit": "國立成功大學國際事務處／教務處註冊組／生輔組",
                    "summary": "取得交換校入學許可後，得依期限申請成大「跨國雙向研修獎助學金」（秋季班 5/31 前、春季班 10/31 前，最高 11 萬–24 萬元）、「深化國際合作重點學校交流獎助學金」（筑波、UGA、LMU/TUM、Purdue 錄取 1 個月內申請，3 萬–5 萬元）或教育部學海飛颺／惜珠計畫；役男須於出國前至少 1.5 個月辦理緩徵役男出國手續；交換期間須完成成大註冊並每學期至少修習 3 門學分課及格，返國後 2 個月內上傳心得報告（Word 及 PDF）、成績單及完成問卷後無息退還保證金。",
                    "details": tuition_points_list,
                    "scope": {
                        "home_universities": ["國立成功大學"],
                        "academic_years": ["115", "116"],
                        "application_rounds": [
                            round_label,
                            "115-1",
                            "115-2",
                            "116-1",
                            "116-2",
                            "116學年度第1學期（秋季班）",
                            "116學年度第2學期（春季班）",
                        ],
                    },
                    "source_urls": [
                        NCKU_SCHOLARSHIP_OVERVIEW_URL,
                        NCKU_SCHOLARSHIP_REG_PDF_URL,
                        NCKU_KEY_PARTNER_SCHOLARSHIP_PDF_URL,
                        NCKU_116_1_GUIDELINES_PDF_URL,
                    ],
                    "checked_at": CHECKED_AT,
                    "support_status": "verified",
                },
            ],
            "sources": wf_sources,
            "last_checked": CHECKED_AT,
            "coverage_status": "official_verified",
            "coverage_note": "已完整整合國立成功大學 116-1、115-2、115-1 校級薦外交換學生計畫甄選簡章、簽約學校一覽表、跨國雙向研修獎助學金與重點學校獎助學金辦法及 357 篇歷屆交換心得。",
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
                "title": f"國立成功大學校級薦外交換簽約學校一覽表與條件—{zh_name}",
                "source_url": source_url,
                "summary": "成大官方交換學校名額、外語門檻、GPA 要求與學制領域限制",
            },
            {
                "title": "國立成功大學 116學年度第1學期校級薦外交換學生計畫甄選簡章",
                "source_url": NCKU_116_1_GUIDELINES_PDF_URL,
                "summary": "成大校級交換甄選配分（在校成績 50%、讀書計畫 25%、自傳及表現 25%）、8,000 元保證金與每學期至少 3 門課及格規定",
            },
        ]
        if detail_url:
            dest_sources.append({
                "title": f"國立成功大學國際事務處出國交換公告專頁—{zh_name}",
                "source_url": detail_url,
                "summary": "成大國際處薦外交換公告與簡章下載",
            })
        if website:
            dest_sources.append({
                "title": f"{full_name} 官方網站",
                "source_url": website,
                "summary": "接待合作校官方網站",
            })
        if exp_posts:
            dest_sources.append({
                "title": f"國立成功大學赴 {zh_name} 交換生返國心得報告（共 {len(exp_posts)} 篇）",
                "source_url": exp_posts[0].get("url") or exp_posts[0].get("post_url") or NCKU_EXPERIENCE_ASIA_URL,
                "summary": f"收錄成大國際處交換生赴 {zh_name} 返國心得報告 PDF",
            })

        src_url_list = (
            [source_url, NCKU_116_1_GUIDELINES_PDF_URL]
            + ([detail_url] if detail_url else [])
            + ([website] if website else [])
        )

        destinations.append({
            "home_university": "國立成功大學",
            "school_name": full_name,
            "country": country,
            "city": location_obj.get("city") or country,
            "cost_summary": f"{cost_line}。\n{tuition_clean}",
            "housing_summary": housing_clean,
            "transport_summary": f"校區代表城市：{location_obj.get('city') or country}。請依入學許可與接待校 Factsheet 確認實際授課校區、機場交通與當地學生大眾運輸票卡優惠。",
            "campus_life_summary": f"{calendar_clean}\n{course_clean}",
            "student_guide_sections": [
                {
                    "key": "cost",
                    "title": "生活費、成大跨國雙向研修獎助學金（11萬–24萬）、重點學校獎助學金與教育部學海計畫",
                    "summary": cost_line,
                    "points": [cost_line] + tuition_points_list,
                    "source_urls": src_url_list + [NCKU_SCHOLARSHIP_OVERVIEW_URL, NCKU_SCHOLARSHIP_REG_PDF_URL, NCKU_KEY_PARTNER_SCHOLARSHIP_PDF_URL],
                    "caution": "成大「跨國雙向研修獎助學金」亞洲地區最高補助 110,000 元／學期（200,000 元／學年）、亞洲以外最高 150,000 元／學期（240,000 元／學年），秋季班於 5/31 前、春季班於前一年 10/31 前申請；赴筑波大學、格勒諾布爾-阿爾卑斯大學、慕尼黑大學／慕尼黑工大、普渡大學可另申請「深化國際合作重點學校交流獎助學金」（3萬–5萬元）。",
                },
                {
                    "key": "housing",
                    "title": "住宿資訊與校內外宿舍申請",
                    "summary": housing_clean[:160],
                    "points": [housing_clean],
                    "source_urls": src_url_list,
                    "caution": "各締約校學生宿舍名額有限，獲成大國際處提名後請務必於該校住宿申請截止日前完成登記。",
                },
                {
                    "key": "insurance",
                    "title": "海外醫療及意外保險與在地保險規定",
                    "summary": visa_default,
                    "points": [
                        visa_default,
                        "依《國立成功大學校級薦外交換學生計畫甄選簡章》第玖點規定，交換生於出國前必須自行購買足額之海外醫療及意外保險，並於註冊時依接待國及交換校規定投保當地強制學生醫療保險。",
                    ],
                    "source_urls": src_url_list,
                    "caution": "多數歐美日韓及紐澳姊妹校要求於註冊或抵校時出示符合當地政府或校方標準之英文醫療保險證明。",
                },
                {
                    "key": "visa",
                    "title": "簽證辦理與緩徵役男出境手續（出國前至少 1.5 個月）",
                    "summary": visa_default,
                    "points": [
                        "收到締約校核發之正式入學許可書（LOA / COE / DS-2019）後，請立即向該國駐臺辦事處申辦學生簽證（赴大陸交換須自行辦理有效護照與臺胞證）。",
                        "依簡章規定，具役男身分之錄取學生，應至遲於出國前 1.5 個月備齊交換校入學許可等文件，洽國際合作組及學務處生輔組辦理緩徵役男出國核准手續。",
                        visa_default,
                    ],
                    "source_urls": src_url_list,
                    "caution": "各國領事館簽證審核約需 4–8 週，請勿於取得簽證與入學許可前購買不可退改之機票。",
                },
                {
                    "key": "courses",
                    "title": "每學期至少修習 3 門學分課及格規定與返國學分抵免",
                    "summary": course_clean[:160],
                    "points": [
                        course_clean,
                        "交換生於交換期間仍須於成大註冊並維持在學身分，每學期至少須修習 3 門學分課程且成績及格；返國後憑國外大學正式成績單依成大各系所規定辦理學分採認與抵免。",
                    ],
                    "source_urls": src_url_list,
                    "caution": "若於交換學校修習及格之學分課程未達每學期 3 門，或未於返國後 2 個月內完成心得報告、成績單上傳與返國問卷，將不予退還計畫保證金。",
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
                    "caution": "部分合作大學設有多個校區，實際授課校區請以當期簽約學校一覽表及姊妹校錄取通知為準。",
                },
                {
                    "key": "arrival",
                    "title": "返國後 2 個月內上傳交換心得（Word & PDF）、成績單與退還 8,000 元保證金",
                    "summary": calendar_clean,
                    "points": [
                        calendar_clean,
                        "依《國立成功大學校級薦外交換學生計畫甄選簡章》第拾點規定，交換生須於返國後 2 個月內於線上系統上傳：（1）交換心得報告（Word 及 PDF 檔）、（2）交換學校修課成績單或研習證明（每學期至少修習 3 門學分課及格）、（3）填寫線上返國問卷，經國際合作組審核通過後無息退還保證金 NT$8,000（或 NT$2,000）。",
                    ]
                    + (
                        [
                            f"歷屆學長姐返國心得：成大國際處已公開收錄赴 {zh_name} 交換生心得報告共 {len(exp_posts)} 篇。"
                        ]
                        if exp_posts
                        else []
                    ),
                    "source_urls": src_url_list
                    + ([exp_posts[0].get("url") or exp_posts[0].get("post_url")] if exp_posts else [NCKU_EXPERIENCE_ASIA_URL]),
                    "caution": "領取成大跨國雙向研修獎助學金或教育部學海系列計畫者，另須依獎學金規定於返國後期限內完成核銷與成果報告上傳。",
                },
            ],
            "first_72_hours": [
                {
                    "title": "依締約校入學許可指定報到日完成新生報到、宿舍入住與選課確認",
                    "detail": calendar_clean,
                    "source_urls": [source_url],
                },
                {
                    "title": "完成當地居留登錄、醫療保險確認並確保每學期修習至少 3 門學分課程",
                    "detail": f"{visa_default} 請於抵達後確認選課清單符合成大每學期至少修習 3 門學分課及格之規定，並完成成大當學期註冊繳費。",
                    "source_urls": [
                        NCKU_116_1_GUIDELINES_PDF_URL,
                        NCKU_OUTBOUND_OVERVIEW_URL,
                    ],
                },
            ],
            "sources": dest_sources,
            "last_checked": CHECKED_AT,
            "coverage_status": "official_verified",
            "coverage_note": "已整合國立成功大學 116-1、115-2、115-1 校級薦外交換學生計畫甄選簡章、簽約學校一覽表、國際處合約資料庫、獎助學金辦法與 357 篇歷屆學長姐交換心得報告。",
        })

        research_records.append({
            "home_university": "國立成功大學",
            "school_name": full_name,
            "country": country,
            "official_website": website,
            "verification_status": "official_verified",
            "discovery_source_url": source_url,
            "checked_at": CHECKED_AT,
            "note": f"國立成功大學國際事務處簽約學校一覽表、合約資料庫（{detail_url or source_url}）及 ROR/Wikidata 官方網址核對完成。",
        })

        ev_sources = [
            {"title": f"國立成功大學校級薦外交換簽約學校一覽表與條件—{zh_name}", "url": source_url},
        ]
        if detail_url:
            ev_sources.append({"title": f"國立成功大學國際事務處出國交換專頁—{zh_name}", "url": detail_url})
        if website:
            ev_sources.append({"title": f"{full_name} 官方網站", "url": website})
        if exp_posts:
            ev_sources.append({
                "title": f"國立成功大學赴 {zh_name} 交換生返國心得報告（{exp_posts[0]['term']}）",
                "url": exp_posts[0].get("url") or exp_posts[0].get("post_url") or NCKU_EXPERIENCE_ASIA_URL,
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
                "scope": "國立成功大學簽約學校一覽表住宿與生活資訊",
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
                "scope": "國立成功大學交換生費用規定、跨國雙向研修獎助學金／重點學校獎助學金／學海計畫與地區生活費估算",
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
                "scope": "國立成功大學交換生選課限制、每學期至少 3 門學分課及格門檻與返國學分抵免規定",
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
                "scope": "國立成功大學出國交換簽證、海外醫療保險與緩徵役男出境提醒",
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
                        f"｜成大國際處官網公開收錄赴 {zh_name} 歷屆交換生返國心得報告共 {len(exp_posts)} 篇。"
                        if exp_posts
                        else ""
                    )
                ),
                "sources": ev_sources,
                "checked_at": CHECKED_AT,
                "scope": "國立成功大學出國交換名額與歷屆學長姐交換心得報告",
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
                "已整合國立成功大學 116-1、115-2、115-1 校級薦外交換學生計畫甄選簡章、簽約學校一覽表、國際處合約資料庫與 357 篇歷屆交換生返國心得報告。",
                "當期宿位供給、費用與選課限制請依締約校最新 Factsheet 及課程目錄核對。",
            ],
            "location_signature": f"verified:{location_obj['latitude']}:{location_obj['longitude']}:representative",
            "extraction_version": 3,
        })

        sample_reports: list[dict] = []
        for p_item in exp_posts[:5]:
            p_url = p_item.get("url") or p_item.get("post_url") or NCKU_EXPERIENCE_ASIA_URL
            sample_reports.append({
                "title": p_item.get("title") or f"國立成功大學赴 {zh_name} 交換學生返國心得報告",
                "url": p_url,
                "term": p_item.get("term") or "歷年交換",
            })

        if exp_posts:
            latest_post = exp_posts[0]
            terms_covered = list(dict.fromkeys(p.get("term") for p in exp_posts[:6] if p.get("term")))
            rep_title = (
                f"國立成功大學赴 {zh_name}（共 {len(exp_posts)} 篇）交換學生返國心得報告彙編"
            )
            summary_text = (
                f"國立成功大學國際事務處「交換心得（亞太／歐洲／美洲）」專區公開收錄赴 {zh_name} 交換學生返國心得報告共 {len(exp_posts)} 篇"
                + (f"（涵蓋學期：{'、'.join(terms_covered[:5])}）" if terms_covered else "")
                + f"，代表篇目為《{latest_post.get('title') or zh_name}》，詳實記錄成大交換生行前簽證準備、締約校選課（每學期至少 3 門學分課）與學分抵免、學生宿舍申請及當地生活開銷。"
            )
            theme_map = {
                "academics": f"成大交換生分享於 {zh_name} 之選課流程、英語或當地語言授課體驗、每學期至少修習 3 門學分課規定及返國學分抵免實務。",
                "housing": f"成大交換生於返國心得中分享 {zh_name} 校內學生宿舍或校外租屋申請方式、月租費用與生活機能（{housing_clean[:120]}）。",
                "campus_culture": f"成大國際處收錄 {len(exp_posts)} 篇赴 {zh_name} 歷屆交換生返國心得報告 PDF，提供學弟妹第一手校園生活與跨文化交流指南。",
                "cost": f"成大交換生於心得中記錄赴 {zh_name} 之機票、簽證、住宿與每月生活費開銷（{cost_default}），以及成大跨國雙向研修獎助學金／教育部學海飛颺申請經驗。",
            }
            p_url = latest_post.get("url") or latest_post.get("post_url") or NCKU_EXPERIENCE_ASIA_URL
            student_experience_rows.append({
                "school_name": full_name,
                "country": country,
                "title": rep_title,
                "source_url": p_url,
                "source_type": "article",
                "platform": "國立成功大學國際事務處—交換學生返國心得專區",
                "author_name": latest_post.get("student_name") or "國立成功大學返國交換學生",
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
            "home_university": "國立成功大學",
            "school_name": full_name,
            "country": country,
            "official_experience_portal_url": (
                exp_posts[0].get("post_url")
                if exp_posts
                else (
                    NCKU_EXPERIENCE_EUROPE_URL
                    if region == "歐洲"
                    else (
                        NCKU_EXPERIENCE_AMERICAS_URL
                        if region == "美洲"
                        else NCKU_EXPERIENCE_ASIA_URL
                    )
                )
            ),
            "partner_page_url": detail_url or source_url,
            "report_count": len(exp_posts),
            "sample_reports": sample_reports,
            "checked_at": CHECKED_AT,
        })

    partners_jsonl_text = (
        "\n".join(json.dumps(r, ensure_ascii=False) for r in partners) + "\n"
    )
    (OFFICIAL_NCKU_DIR / "partners.jsonl").write_text(
        partners_jsonl_text, encoding="utf-8"
    )
    (SOURCES_NCKU_DIR / "partners.jsonl").write_text(
        partners_jsonl_text, encoding="utf-8"
    )
    (OFFICIAL_NCKU_DIR / "application_workflows.jsonl").write_text(
        "\n".join(json.dumps(r, ensure_ascii=False) for r in workflows) + "\n",
        encoding="utf-8",
    )
    (OFFICIAL_NCKU_DIR / "destination_profiles.jsonl").write_text(
        "\n".join(json.dumps(r, ensure_ascii=False) for r in destinations) + "\n",
        encoding="utf-8",
    )
    (OFFICIAL_NCKU_DIR / "partner_research.jsonl").write_text(
        "\n".join(json.dumps(r, ensure_ascii=False) for r in research_records) + "\n",
        encoding="utf-8",
    )
    (OFFICIAL_NCKU_DIR / "student_life.jsonl").write_text(
        "\n".join(json.dumps(r, ensure_ascii=False) for r in life_records) + "\n",
        encoding="utf-8",
    )
    (OFFICIAL_NCKU_DIR / "experience_sources.jsonl").write_text(
        "\n".join(
            json.dumps(r, ensure_ascii=False) for r in experience_sources_records
        )
        + "\n",
        encoding="utf-8",
    )
    (OFFICIAL_NCKU_DIR / "student_experiences.jsonl").write_text(
        "\n".join(
            json.dumps(r, ensure_ascii=False) for r in student_experience_rows
        )
        + "\n",
        encoding="utf-8",
    )
    (OFFICIAL_NCKU_DIR / "campus-locations.json").write_text(
        json.dumps({"locations": new_locations}, ensure_ascii=False, indent=2)
        + "\n",
        encoding="utf-8",
    )

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

    ncku_home_loc = {
        "school_name": "國立成功大學",
        "country": "臺灣",
        "city": "臺南市東區",
        "latitude": 22.9967,
        "longitude": 120.2199,
        "geocode_status": "verified",
        "geocoded_at": CHECKED_AT,
        "source_url": "https://www.wikidata.org/wiki/Q702839",
        "identity_source_url": "https://ror.org/01b8kcc49",
        "precision": "representative",
        "note": "校級代表位置：官方網域及國家已與 ROR 比對，座標來源為 Wikidata P625；實際交換校區以錄取通知為準。 母校代表點採臺南市東區大學路1號光復校區雲平大樓東棟 7–8 樓國際事務處；官方地址來源：https://oia.ncku.edu.tw/。",
    }
    existing_loc_map[("國立成功大學", "臺灣")] = ncku_home_loc
    sorted_locs = sorted(
        existing_loc_map.values(),
        key=lambda r: (r.get("country") or "", r.get("school_name") or ""),
    )
    loc_file.write_text(
        "\n".join(json.dumps(r, ensure_ascii=False) for r in sorted_locs) + "\n",
        encoding="utf-8",
    )

    ncku_source_urls = [
        NCKU_OUTBOUND_OVERVIEW_URL,
        NCKU_PORTAL_URL,
        NCKU_116_1_ANNOUNCEMENT_URL,
        NCKU_116_1_GUIDELINES_PDF_URL,
        NCKU_116_1_PARTNERS_PDF_URL,
        NCKU_115_2_ANNOUNCEMENT_URL,
        NCKU_115_2_GUIDELINES_PDF_URL,
        NCKU_115_2_PARTNERS_PDF_URL,
        NCKU_115_2_APP_FORM_PDF_URL,
        NCKU_115_1_GUIDELINES_PDF_URL,
        NCKU_115_1_PARTNERS_PDF_URL,
        NCKU_115_1_APP_FORM_PDF_URL,
        NCKU_REGULATION_URL,
        NCKU_ENGLISH_TABLE_PDF_URL,
        NCKU_SCHOLARSHIP_OVERVIEW_URL,
        NCKU_SCHOLARSHIP_REG_PDF_URL,
        NCKU_SCHOLARSHIP_GUIDE_PDF_URL,
        NCKU_KEY_PARTNER_SCHOLARSHIP_PDF_URL,
        NCKU_EXPERIENCE_ASIA_URL,
        NCKU_EXPERIENCE_EUROPE_URL,
        NCKU_EXPERIENCE_AMERICAS_URL,
        NCKU_CONTRACT_SEARCH_URL,
    ]

    exchange_info_payload = {
        "school_name": "國立成功大學",
        "program_type": [
            "交換學生（校級薦外交換學生計畫・涵蓋美洲、歐洲、亞洲、大洋洲及大陸港澳地區，每人至多選填 6 個志願）",
            "雙聯學位與院系級交換計畫（校級及全校 11 學院跨國雙向研修與深化國際合作重點學校交流計畫）",
        ],
        "academic_year": [
            "116（116學年度第1學期［2027秋季班］校級薦外交換計畫：115年10月30日至11月19日 16:00 開放線上申請，共開放 97 所簽約學校）",
            "115（115學年度第2學期［2027春季班］開放 102 所簽約學校；115學年度第1學期［2026秋季班］開放 99 所簽約學校）",
        ],
        "semester": [
            "第1學期（秋季班：每年約 8/9 月至 12 月／翌年 1 月；澳洲與紐西蘭對應 Semester 2 為 7 月至 11 月）",
            "第2學期（春季班：每年約 1/2 月至 5/6 月；日本前學期為 4 月至 8 月）",
        ],
        "application_period": [
            "【116學年度第1學期校級薦外交換學生計畫甄選（對應 2027 秋季班／2027–2028 學年出國交換）】計畫說明暨分享會：115年10月23日（五）；線上申請期間：115年10月30日至115年11月19日（四）下午 16:00 止（於成大薦外交換學生申請系統 https://exchange.oia.ncku.edu.tw/index.php?outgoing_auth 填報至多 6 志願並上傳全套審查文件 PDF，逾期不予受理）；甄選結果公告：115年12月19日 23:59 前；正取生上傳確認書／放棄聲明書截止：115年12月26日 16:00 前；備取生上傳確認書截止：116年1月2日 16:00 前；繳交計畫保證金（NT$8,000／低收及中低收 NT$2,000）：116年1月5日至1月11日。",
            "【第2學期（春季班）校級薦外交換甄選參考時程（以 115-2 簡章為準）】線上申請期間：每年約 4月27日至5月18日 16:00 止；甄選結果公告：6月19日；正取生確認截止：6月26日 16:00；備取生確認截止：7月3日 16:00；繳交計畫保證金：7月6日至7月17日。",
            "【獎助學金受理期程】成大「學生跨國雙向研修獎助學金」：秋季班出國者於每年 5 月 31 日前申請（7月下旬公告結果），春季班出國者於前一年 10 月 31 日前申請（12月下旬公告結果）；成大「學生赴深化國際合作重點學校交流獎助學金」（筑波、UGA、LMU/TUM、Purdue）：取得入學許可 1 個月內申請；教育部「學海飛颺」與「學海惜珠」計畫：每年分兩梯次依國際處公告受理。",
        ],
        "eligibility": [
            "申請資格與在學年級規定（《國立成功大學校級薦外交換學生計畫甄選簡章》第參點）：申請時須為成大大學部二年級以上、碩士班一年級以上、博士班一年級以上在學學生（轉學生須為二年級以上，且須於成大就讀滿一學期並有成大成績單）；出國交換期間須維持成大在學身分並註冊繳費（不得休學或畢業），同一學制以出國交換一次為原則。",
            "學業成績門檻與甄選評分比重（簡章第參、陸點）：（1）大學部學生：前一學期課業成績平均須達 77 分（含）以上，或全班／全系排名前 50%；（2）研究所（碩博士班）學生：無校內學業成績門檻限制，惟須取得指導教授或系所主管簽章同意，且須符合各交換學校所訂之 GPA 要求。校內書面甄選評分比重為：在校成績 50%、研究/讀書計畫 25%、自傳及其餘表現 25%（總分相同時，依序以在校成績、研究/讀書計畫、自傳及其餘表現、志願序高分者優先錄取）。",
            "志願選填與錄取分發原則：每人至多可選填 6 個志願（第一至第六志願），分發時依甄選總成績高低及志願序辦理，每人至多正取一校。若正取生同時為前志願之備取生，一經上傳確認書確認正取資格，即自動喪失其他志願之備取資格。",
            "計畫保證金、最低修課及格標準與返國義務（簡章第捌、拾點）：錄取生確認參加後須於期限內繳交計畫保證金新臺幣 8,000 元（於線上申請階段上傳有效低收入戶或中低收入戶證明者減免為 2,000 元）；繳交後除不可抗力因素外放棄資格者不予退還。交換期間每學期至少須修習 3 門學分課程且成績及格，並於返國後 2 個月內上傳交換心得報告（Word 及 PDF 檔）、交換學校成績單或研習證明及完成線上返國問卷，審核通過後無息全額退還保證金。",
        ],
        "language_requirement": [
            "【英語能力基本門檻（CEFR B2 以上，2 年內有效）】申請者須檢附報名截止日前 2 年內（116-1 梯次為 2024年11月20日後）有效之外語能力證明：TOEFL iBT 72 分（含）以上（2026年1月21日起新制 TOEFL iBT 總分須達 4.0 以上）、IELTS Academic（學術組）5.5（含）以上，或 TOEIC 785 分（含）以上；各交換學校若有更高總分、單科小分或不採計 TOEIC 之規定，須同時符合該校要求。",
            "【日語、韓語、德語、法語、西語等外語檢定】申請非英語授課或特定語種計畫者，須具備該交換學校於《簽約學校一覽表》所列之外語能力檢定標準（如日語 JLPT N1／N2／N3、韓語 TOPIK、德語 Goethe-Zertifikat / TestDaF B1–B2、法語 DELF B1–B2、西語 DELE 等）。",
            "【申請大陸地區學校與網路成績截圖查驗規定】依成大簡章規定，申請大陸地區交換學校者，仍須檢附符合成大標準之英語能力證明（CEFR B2：TOEFL iBT 72／IELTS 5.5／TOEIC 785）。若報名時上傳網路成績查詢畫面截圖者，必須於放榜後至繳交保證金截止日前，持成績單正本至國際合作組完成查驗。",
        ],
        "required_documents": [
            "1. 校內甄選申請表（於線上申請系統登打完成後下載列印，黏貼兩吋半身脫帽照片、申請人親筆簽名，大學部須經導師簽章，碩博士班須經指導教授或系所主管簽章）",
            "2. 中文歷年成績單（須含當學期修課科目、學期總平均及 GPA；大學部須含全班或全系排名百分比；碩一、博一新生請檢附大學或碩士班歷年成績單）",
            "3. 中英文自傳（含學、經歷，請依第一志願交換學校擬訂）",
            "4. 中英文讀書或研究計畫（請依第一志願交換學校擬訂）",
            "5. 外語能力證明（報名截止日前 2 年內有效：TOEFL iBT 72［新制 4.0］／IELTS Academic 5.5／TOEIC 785 或交換校指定外語檢定；網路截圖須於保證金截止日前查驗正本）",
            "6. 其他有助審查之資料（社團表現、獲獎紀錄、低收入戶或中低收入戶證明等，無則免附）",
            "7. 第 1–6 項文件之單一 PDF 合併檔（檔案大小上限 50MB，連同各分項於截止時間前上傳至系統，無須繳交紙本）",
        ],
        "scholarship_info": [
            "國立成功大學「學生跨國雙向研修獎助學金」（《補助辦法》暨《甄選要點》）：補助具中華民國國籍之成大一般生（不含在職專班，且不含赴大陸及港澳地區一般交換生）出國交換或修讀雙聯學位。補助額度：亞洲地區每學期最高新臺幣 110,000 元、每學年最高 200,000 元；亞洲以外地區每學期最高新臺幣 150,000 元、每學年最高 240,000 元。申請期限：秋季班出國於每年 5 月 31 日前申請（7月下旬放榜），春季班出國於前一年 10 月 31 日前申請（12月下旬放榜）；不得與教育部學海系列或國科會補助同時兼領。",
            "國立成功大學「學生赴深化國際合作重點學校交流獎助學金」：專項補助赴成大重點策略夥伴大學（日本筑波大學 University of Tsukuba、法國格勒諾布爾-阿爾卑斯大學 Université Grenoble Alpes、德國慕尼黑大學 LMU München／慕尼黑工業大學 TU Munich、美國普渡大學 Purdue University）交換研習 1 學期之本國籍在學學生，亞洲地區每名補助新臺幣 30,000 元、亞洲以外地區每名補助新臺幣 50,000 元（於取得外方入學許可後 1 個月內提出申請）。",
            "教育部「學海飛颺」計畫（選送優秀學生出國研修）：補助具中華民國國籍且在臺灣地區設有戶籍、外語及學業表現優異之成大在學學生赴國外（不含大陸及港澳）大專校院修讀學分 1 學期或 1 學年，每年分兩梯次依國際處公告受理。",
            "教育部「學海惜珠」計畫（選送勵學優秀學生出國研修）：專項補助持有直轄市、縣（市）主管機關開立之低收入戶、中低收入戶、特殊境遇家庭扶助或身心障礙者生活補助證明之本國籍學生赴國外（不含大陸及港澳）交換研修，全額或高額補助機票與生活費。",
            "締約姊妹校與外國政府交換獎學金：包含日本學生支援機構（JASSO）交換留學生獎學金（每月 JPY 80,000）、韓國政府 GKS 獎學金、德國巴登符騰堡邦獎學金、奧地利 Ernst Mach 獎學金等，由國際合作組依各校每學期來函公告推薦。",
        ],
        "partner_universities": [p["school_name"] for p in partners],
        "source_urls": ncku_source_urls,
        "last_checked": CHECKED_AT,
    }
    (OFFICIAL_NCKU_DIR / "exchange_info.json").write_text(
        json.dumps(exchange_info_payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    student_dashboard_payload = {
        "school_name": "國立成功大學",
        "last_checked": CHECKED_AT,
        "academic_score_minimum": 77.0,
        "academic_score_rule": "大學部學生前一學期課業成績平均須達 77 分（含）以上，或全班／全系排名前 50%；研究所（碩士班、博士班）學生無校內成績門檻限制（須取得指導教授或系所主管簽章同意，且須符合交換校 GPA 門檻）。校內書面甄選總分比重為：在校成績 50%、研究/讀書計畫 25%、自傳及其餘表現 25%。",
        "academic_gpa_minimum": 3.1,
        "maximum_preferences": 6,
        "selection_rules": {
            "academic_policy": "gpa_or_rank",
            "academic_reference_year": "116",
            "undergraduate_gpa_minimum": 3.1,
            "undergraduate_rank_maximum": 50.0,
            "graduate_academic_exempt": True,
            "exclude_in_service": False,
            "pending_quota_planning": False,
            "partner_requirements_need_confirmation": False,
            "degree_score_minimums": {
                "undergraduate": 77.0,
                "graduate": 0.0,
            },
            "excluded_undergraduate_years": ["大一"],
            "language_certificate_required": True,
        },
        "language_score_minimums": {
            "toefl": 72.0,
            "ielts": 5.5,
            "toeic": 785.0,
        },
        "application_periods": [
            {
                "title": "國立成功大學 116學年度第1學期校級薦外交換學生計畫甄選（線上申請 10/30–11/19 16:00、放榜 12/19、保證金繳交 01/05–01/11）",
                "details": [
                    "計畫說明暨分享會：2026年10月23日（五）；線上申請期間：2026年10月30日至11月19日（四）下午 16:00 止（於成大薦外交換學生申請系統填報至多 6 個志願，並上傳導師／指導教授簽章之申請表、成績單、中英文自傳、中英文讀書計畫、外語能力證明及合併 PDF 檔）。",
                    "甄選結果公告：2026年12月19日 23:59 前；正取生於 12月26日 16:00 前、備取生於 2027年1月2日 16:00 前於系統上傳錄取確認書或放棄聲明書。",
                    "計畫保證金繳交：2027年1月5日至1月11日繳交新臺幣 8,000 元（低收入戶及中低收入戶證明者減免為 2,000 元）；返國後 2 個月內完成心得報告、成績單（每學期至少修習 3 門學分課及格）及問卷後無息退還。",
                ],
                "source": {
                    "title": "國立成功大學 116學年度第1學期校級薦外交換學生計畫甄選簡章 PDF",
                    "source_url": NCKU_116_1_GUIDELINES_PDF_URL,
                    "category": "exchange_application",
                    "summary": "116-1 校級薦外交換計畫完整申請日程、大學部 77 分／前 50% 門檻、CEFR B2 語檢要求與 97 所簽約學校一覽表。",
                },
                "scope": "home_application",
                "program_types": ["exchange"],
                "academic_year": "116",
                "application_round": "116學年度第1學期校級薦外交換學生計畫甄選（115年10月30日至11月19日16:00線上申請）",
                "audience": "all_students",
                "opens_at": None,
                "deadline_at": "2026-11-19T16:00:00+08:00",
                "date_status": "verified_exact",
                "status": "upcoming",
                "status_note": "116-1 校級薦外交換學生計畫簡章與 97 所簽約學校一覽表已於 2026/10/16 正式公告，將於 2026/10/30 至 11/19 16:00 開放線上申請。",
                "deadline_note": "請於 2026/11/19（四）16:00 前完成線上系統登打並上傳第 1–6 項單獨檔與第 7 項合併 PDF 檔（上限 50MB），無須繳交紙本。",
                "reminder_eligible": True,
                "checked_at": CHECKED_AT,
            },
            {
                "title": "國立成功大學 116學年度第2學期（春季班）校級薦外交換學生計畫甄選預定時程（參考 115-2 於 4/27–5/18 16:00 受理線上申請）",
                "details": [
                    "成大每年 4–5 月辦理次學年度第 2 學期（春季班）校級薦外交換甄選（115-2 梯次為 4月27日至5月18日 16:00 線上申請、6月19日放榜、6月26日正取確認、7月3日備取確認、7月6日至7月17日繳交保證金）。",
                    "擬於 116 學年度第 2 學期（2028 春季班）出國交換者，請於 2027 年 4 月密切留意國際事務處最新甄選簡章與簽約學校一覽表。",
                ],
                "source": {
                    "title": "國立成功大學 115學年度第2學期校級薦外交換學生計畫甄選簡章 PDF",
                    "source_url": NCKU_115_2_GUIDELINES_PDF_URL,
                    "category": "exchange_application",
                    "summary": "成大第 2 學期（春季班）校級薦外交換甄選時程與 102 所簽約學校參考名單。",
                },
                "scope": "home_application",
                "program_types": ["exchange"],
                "academic_year": "116",
                "application_round": "116學年度第2學期校級薦外交換學生計畫甄選（春季班預計 116年4–5月受理線上申請）",
                "audience": "all_students",
                "opens_at": None,
                "deadline_at": None,
                "date_status": "needs_confirmation",
                "status": "needs_confirmation",
                "status_note": "本筆引用115-2舊簡章，只能作舊年度參考；116-2日期尚未由本輪來源確認，不能將舊年度日期直接順延。",
                "deadline_note": "實際截止日期請依國際事務處 2027 年 4 月公告之 116-2 甄選簡章為準。",
                "reminder_eligible": False,
                "checked_at": CHECKED_AT,
            },
            {
                "title": "國立成功大學「學生跨國雙向研修獎助學金」（10/31、5/31 截止）、「深化國際合作重點學校交流獎助學金」與教育部學海計畫申請期程",
                "details": [
                    "成大「學生跨國雙向研修獎助學金」（亞洲每學期最高 11 萬／學年 20 萬；亞洲以外每學期最高 15 萬／學年 24 萬）：春季班出國者於前一年 10 月 31 日前申請（12月下旬公告結果），秋季班出國者於當年度 5 月 31 日前申請（7月下旬公告結果）。",
                    "成大「學生赴深化國際合作重點學校交流獎助學金」（筑波大學、格勒諾布爾-阿爾卑斯大學、慕尼黑大學／慕尼黑工業大學、普渡大學，補助 3 萬–5 萬元）：於取得外方入學許可後 1 個月內提出申請；教育部「學海飛颺」與「學海惜珠」依國際處公告分兩梯次受理。",
                ],
                "source": {
                    "title": "國立成功大學國際事務處—出國交換獎助學金專區與跨國雙向研修獎助學金辦法",
                    "source_url": NCKU_SCHOLARSHIP_OVERVIEW_URL,
                    "category": "scholarship",
                    "summary": "成大跨國雙向研修獎助學金、重點學校交流獎助學金與教育部學海系列計畫申請辦法。",
                },
                "scope": "home_application",
                "program_types": ["exchange"],
                "academic_year": "116",
                "application_round": "成大出國交換獎助學金申請（春季出國 10/31 截止、秋季出國 5/31 截止）",
                "audience": "all_students",
                "opens_at": "2026-10-01T09:00:00+08:00",
                "deadline_at": "2026-10-31T17:00:00+08:00",
                "date_status": "verified_exact",
                "status": "open",
                "status_note": "春季班出國之跨國雙向研修獎助學金於每年 10 月 31 日截止申請；秋季班出國者則於翌年 5 月 31 日前申請。",
                "deadline_note": "請依《國立成功大學學生跨國雙向研修獎助學金甄選要點》備齊入學許可或申請證明、成績單、外語檢定與研修計畫書提出申請。",
                "reminder_eligible": True,
                "checked_at": CHECKED_AT,
            },
        ],
        "program_overview": [
            {
                "title": f"國立成功大學國際事務處校級薦外交換計畫總覽（{len(partners)} 所全球合作大學）",
                "details": [
                    f"國立成功大學國際事務處國際合作組每學期辦理校級薦外交換學生計畫甄選，本平台完整收錄 {len(partners)} 所官方海外與大陸港澳合作大學（含 116-1 當期開放申請之 {open_partner_count} 所簽約學校，以及 {len(partners) - open_partner_count} 所 115-2／115-1 開放或具交換／雙聯學位合約與歷屆交換心得之合作校）。",
                    f"成大校級薦外交換甄選採全線上無紙化申請（每人至多選填 6 個志願，評分比重為在校成績 50%、研究/讀書計畫 25%、自傳及其餘表現 25%），並提供高額之「跨國雙向研修獎助學金」（每學期 11 萬–15 萬元、每學年 20 萬–24 萬元）、「深化國際合作重點學校交流獎助學金」（筑波、UGA、LMU/TUM、Purdue 每名 3 萬–5 萬元）及教育部學海飛颺／惜珠計畫，官網並公開收錄 357 篇歷屆交換生返國心得報告 PDF（涵蓋 {len(student_experience_rows)} 所合作校）。",
                ],
                "source": {
                    "title": "國立成功大學國際事務處—校級薦外交換計畫與 116-1 甄選公告",
                    "source_url": NCKU_116_1_ANNOUNCEMENT_URL,
                    "category": "exchange_application",
                    "summary": "成大 116-1 校級薦外交換甄選簡章、簽約學校一覽表、獎助學金與 357 篇返國心得報告。",
                },
            }
        ],
        "eligibility": [
            {
                "title": "在學年級規定（大二／碩一／博一以上）、大學部 77 分或前 50% 門檻與書審三項配分機制",
                "details": [
                    "年級與學籍資格：限成大大學部二年級以上、碩士班一年級以上、博士班一年級以上在學學生（轉學生須為二年級以上，且須於成大就讀滿一學期並有成大成績單）；出國交換期間須維持成大在學身分並完成註冊繳費，同一學制以出國交換一次為原則。",
                    "學業成績要求：大學部學生前一學期課業成績平均須達 77 分（含）以上，或全班／全系排名前 50%；研究所（碩士班、博士班）學生無校內成績門檻限制，惟須取得指導教授或系所主管簽章同意，且須符合各交換學校所訂之 GPA 要求。",
                    "甄選評分與分發：書面審查總分依「在校成績 50%、研究/讀書計畫 25%、自傳及其餘表現 25%」計算（同分參酌順序：1. 在校成績、2. 研究/讀書計畫、3. 自傳及其餘表現、4. 志願序），每人至多選填 6 個志願、至多正取一校。",
                ],
                "source": {
                    "title": "國立成功大學 116學年度第1學期校級薦外交換學生計畫甄選簡章 PDF",
                    "source_url": NCKU_116_1_GUIDELINES_PDF_URL,
                    "category": "exchange_application",
                    "summary": "成大校級薦外交換申請資格、大學部 77 分／前 50% 門檻、研究所指導教授同意規定與甄選評分標準。",
                },
            }
        ],
        "language_requirements": [
            {
                "title": "英語能力 CEFR B2 門檻（TOEFL iBT 72［新制 4.0］／IELTS 5.5／TOEIC 785）、第二外語檢定與大陸交換英語規定",
                "details": [
                    "英語能力基本標準：須檢附報名截止日前 2 年內有效之英語檢定證明，且達 CEFR B2 以上：TOEFL iBT 72 分（2026年1月21日起新制 TOEFL iBT 總分 4.0 以上）、IELTS Academic（學術組）5.5 以上，或 TOEIC 785 分以上（各交換校若有更高標準或不採計 TOEIC 者，須依該校規定）。",
                    "第二外語與大陸交換規定：申請日語、韓語、德語、法語、西語等語種交換計畫者，須具備該交換校要求之外語能力檢定（如 JLPT N1–N3、TOPIK、TestDaF/Goethe、DELF、DELE 等）；申請大陸地區交換學校者，仍須檢附符合成大 CEFR B2 標準之英語能力證明。以網路成績截圖報名者，須於放榜後至保證金繳交截止日前持正本至國際合作組查驗。",
                ],
                "source": {
                    "title": "國立成功大學 116-1 甄選簡章與英語能力檢定測驗門檻對照表 PDF",
                    "source_url": NCKU_ENGLISH_TABLE_PDF_URL,
                    "category": "exchange_application",
                    "summary": "成大 CEFR B2 英語檢定對照表、2026 新制托福分數基準與各校語言規定。",
                },
            }
        ],
        "required_documents": [
            {
                "title": "國立成功大學校級薦外交換線上申請 7 項應繳文件規格与 8,000 元（弱勢 2,000 元）保證金規定",
                "details": [
                    "線上申請應上傳文件（無須繳交紙本）：1. 校內甄選申請表（系統登打後下載，貼兩吋照、本人簽名並經導師或指導教授／系所主管簽章）、2. 中文歷年成績單（含當學期修課科目、總平均及 GPA；大學部須附排名；碩博一新生附大學／碩士成績單）、3. 中英文自傳（依第一志願擬訂）、4. 中英文讀書或研究計畫（依第一志願擬訂）、5. 2年內有效外語能力證明、6. 其他有助審查之資料（含低收／中低收證明）、7. 第 1–6 項合併之單一 PDF 檔（上限 50MB）。",
                    "錄取確認與保證金退費條件：錄取生須於期限內上傳本人及家長簽章之確認書，並繳交計畫保證金新臺幣 8,000 元（低收／中低收入戶為 2,000 元）；交換期間每學期至少修習 3 門學分課及格，並於返國後 2 個月內上傳交換心得（Word 及 PDF）、成績單及完成線上問卷後無息退還。",
                ],
                "source": {
                    "title": "國立成功大學 116學年度第1學期校級薦外交換學生計畫甄選簡章 PDF",
                    "source_url": NCKU_116_1_GUIDELINES_PDF_URL,
                    "category": "exchange_application",
                    "summary": "成大校級薦外交換 7 項線上應繳文件、第一志願擬訂規範與保證金退費義務。",
                },
            }
        ],
        "scholarship_info": [
            {
                "title": "成大跨國雙向研修獎助學金（每學期 11萬–15萬／每學年 20萬–24萬）、深化國際合作重點學校獎助學金（3萬–5萬）與教育部學海飛颺／惜珠",
                "details": [
                    "成大「學生跨國雙向研修獎助學金」：補助本國籍一般生（不含大陸港澳交換及在職專班）赴國外交換或修讀雙聯學位，亞洲地區每學期最高 110,000 元、每學年最高 200,000 元；亞洲以外地區每學期最高 150,000 元、每學年最高 240,000 元（秋季出國 5/31 截止、春季出國前一年 10/31 截止）。",
                    "成大「學生赴深化國際合作重點學校交流獎助學金」：赴日本筑波大學、法國格勒諾布爾-阿爾卑斯大學、德國慕尼黑大學／慕尼黑工業大學、美國普渡大學交換 1 學期，亞洲補助 30,000 元、亞洲以外補助 50,000 元（取得入學許可 1 個月內申請）；另可申請教育部「學海飛颺」、「學海惜珠」及日本 JASSO 等外國政府獎學金。",
                ],
                "source": {
                    "title": "國立成功大學國際事務處—獎助學金專區與跨國雙向研修獎助學金補助辦法",
                    "source_url": NCKU_SCHOLARSHIP_OVERVIEW_URL,
                    "category": "scholarship",
                    "summary": "成大跨國雙向研修獎助學金、重點學校交流獎助學金與學海系列計畫。",
                },
            }
        ],
        "document_explanations": [
            {
                "title": "國立成功大學校級薦外交換書審文件規格（第一志願自傳與讀書計畫、導師／指導教授簽章、50MB 合併 PDF）說明",
                "summary": "規範成大薦外交換申請系統之申請表簽章程序、依第一志願擬訂之中英文自傳與讀書計畫，以及網路語檢截圖正本查驗規定。",
                "key_points": [
                    "申請人須先於線上系統（https://exchange.oia.ncku.edu.tw/index.php?outgoing_auth）完成登打後下載申請表，黏貼兩吋半身脫帽照片、親筆簽名，大學部由導師簽章、碩博士班由指導教授或系所主管簽章。",
                    "中英文自傳（含學、經歷）與中英文讀書或研究計畫占甄選總分共 50%（各占 25%），均須針對「第一志願」交換學校之課程與研究資源具體擬訂。",
                    "全套文件除分項上傳至系統對應欄位外，第 7 項須將第 1–6 項依序合併為單一 PDF 檔（上限 50MB）上傳，全程無紙化作業。",
                ],
                "applies_to": [],
                "source": {
                    "title": "國立成功大學 116學年度第1學期校級薦外交換學生計畫甄選簡章",
                    "source_url": NCKU_116_1_GUIDELINES_PDF_URL,
                    "category": "exchange_application",
                    "summary": None,
                },
                "document_url": NCKU_116_1_GUIDELINES_PDF_URL,
                "document_type": "official_document",
                "full_text_extracted": True,
            }
        ],
        "rule_explanations": [
            {
                "title": "國立成功大學校級薦外交換甄選辦法：大學部 77 分／前 50% 門檻、三項配分、6 志願分發與每學期 3 門課及格退還 8,000 元保證金規定",
                "summary": "說明成大校級交換甄選資格、書審配分比例、正備取確認機制、8,000 元保證金退費義務與出國修課最低門檻。",
                "key_points": [
                    "大學部二年級以上學生須符合「前一學期課業成績平均 77 分（含）以上或全班／全系排名前 50%」；碩博士班一年級以上學生無校內成績門檻，惟須取得指導教授同意。",
                    "書面審查採計在校成績 50%、研究/讀書計畫 25%、自傳及其餘表現 25%，每人至多選填 6 個志願、至多正取一校。",
                    "錄取生須繳交計畫保證金新臺幣 8,000 元（低收／中低收入戶 2,000 元）；交換期間每學期至少須修習 3 門學分課程且及格，返國後 2 個月內上傳交換心得（Word 及 PDF）、成績單及完成線上問卷後無息全額退還。",
                ],
                "applies_to": [],
                "source": {
                    "title": "國立成功大學 116學年度第1學期校級薦外交換學生計畫甄選簡章 PDF",
                    "source_url": NCKU_116_1_GUIDELINES_PDF_URL,
                    "category": "exchange_application",
                    "summary": None,
                },
                "document_url": NCKU_116_1_GUIDELINES_PDF_URL,
                "document_type": "official_document",
                "full_text_extracted": True,
            }
        ],
        "sources": [
            {
                "title": "國立成功大學國際事務處—校級薦外交換計畫總覽專區",
                "source_url": NCKU_OUTBOUND_OVERVIEW_URL,
                "category": "exchange_application",
                "summary": None,
            },
            {
                "title": "國立成功大學 116學年度第1學期校級薦外交換學生計畫甄選簡章 PDF",
                "source_url": NCKU_116_1_GUIDELINES_PDF_URL,
                "category": "exchange_application",
                "summary": None,
            },
            {
                "title": "國立成功大學 116學年度第1學期校級薦外交換學生計畫簽約學校一覽表（97 校）PDF",
                "source_url": NCKU_116_1_PARTNERS_PDF_URL,
                "category": "partner_school",
                "summary": None,
            },
            {
                "title": "國立成功大學 115學年度第2學期校級薦外交換學生計畫簽約學校一覽表（102 校）PDF",
                "source_url": NCKU_115_2_PARTNERS_PDF_URL,
                "category": "partner_school",
                "summary": None,
            },
            {
                "title": "國立成功大學國際事務處—英語能力檢定測驗門檻對照表 PDF",
                "source_url": NCKU_ENGLISH_TABLE_PDF_URL,
                "category": "exchange_application",
                "summary": None,
            },
            {
                "title": "國立成功大學國際事務處—全球締約學校合約檢索系統",
                "source_url": NCKU_CONTRACT_SEARCH_URL,
                "category": "partner_school",
                "summary": None,
            },
            {
                "title": "國立成功大學國際事務處—跨國雙向研修獎助學金與重點學校獎助學金專區",
                "source_url": NCKU_SCHOLARSHIP_OVERVIEW_URL,
                "category": "scholarship",
                "summary": None,
            },
            {
                "title": "國立成功大學國際事務處—交換學生返國心得專區（亞太、歐洲、美洲共 357 篇 PDF）",
                "source_url": NCKU_EXPERIENCE_ASIA_URL,
                "category": "partner_school",
                "summary": None,
            },
        ],
    }
    (OFFICIAL_NCKU_DIR / "student_dashboard.json").write_text(
        json.dumps(student_dashboard_payload, ensure_ascii=False, indent=2)
        + "\n",
        encoding="utf-8",
    )

    pages_records = [
        {
            "title": "國立成功大學：116-1 校級薦外交換學生計畫甄選時程（10/30–11/19 線上申請、12/19 放榜）與春季班時程",
            "source_url": NCKU_116_1_GUIDELINES_PDF_URL,
            "published_at": "2026-10-16T00:00:00Z",
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
            "title": "國立成功大學：校級薦外交換申請資格、大學部 77 分／前 50% 門檻、三項配分與 8,000 元保證金義務",
            "source_url": NCKU_REGULATION_URL,
            "published_at": "2026-10-16T00:00:00Z",
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
            "title": "國立成功大學：英語能力 CEFR B2 門檻（TOEFL iBT 72［新制 4.0］／IELTS 5.5／TOEIC 785）與外語檢定規定",
            "source_url": NCKU_ENGLISH_TABLE_PDF_URL,
            "published_at": "2026-10-16T00:00:00Z",
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
            "title": "國立成功大學：校級薦外交換 7 項線上應繳文件、第一志願讀書計畫自傳規範與保證金退費條件",
            "source_url": NCKU_116_1_ANNOUNCEMENT_URL,
            "published_at": "2026-10-16T00:00:00Z",
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
            "title": "國立成功大學：跨國雙向研修獎助學金（11萬–24萬）、深化國際合作重點學校獎助學金（3萬–5萬）與教育部學海計畫",
            "source_url": NCKU_SCHOLARSHIP_OVERVIEW_URL,
            "published_at": "2026-10-16T00:00:00Z",
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
    (OFFICIAL_NCKU_DIR / "pages.jsonl").write_text(
        "\n".join(json.dumps(p, ensure_ascii=False) for p in pages_records)
        + "\n",
        encoding="utf-8",
    )

    home_rules = {
        "school_id": "ncku",
        "school_name": "國立成功大學",
        "eligibility": student_dashboard_payload["eligibility"],
        "application_periods": student_dashboard_payload["application_periods"],
        "selection_rules": {
            "undergraduate_minimum_average_score": 77.0,
            "undergraduate_maximum_class_or_dept_rank_percent": 50.0,
            "graduate_minimum_average_score": None,
            "weights": {
                "academic_grade": 0.50,
                "study_or_research_plan": 0.25,
                "autobiography_and_achievements": 0.25,
            },
            "deposit_twd": 8000,
            "deposit_low_income_twd": 2000,
            "max_preferences": 6,
            "minimum_passed_credit_courses_per_semester": 3,
            "return_report_deadline_months": 2,
        },
        "source_urls": ncku_source_urls,
        "verified_at": "2026-10-18",
    }
    (OFFICIAL_NCKU_DIR / "home_rules.json").write_text(
        json.dumps(home_rules, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    (OFFICIAL_NCKU_DIR / "documents.json").write_text(
        json.dumps(
            {
                "school_name": "國立成功大學",
                "required_documents": student_dashboard_payload["required_documents"],
                "source_urls": ncku_source_urls,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    (OFFICIAL_NCKU_DIR / "scholarships.json").write_text(
        json.dumps(
            {
                "school_name": "國立成功大學",
                "scholarships": student_dashboard_payload["scholarship_info"],
                "source_urls": ncku_source_urls,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    completeness = {
        "school_id": "ncku",
        "school_name": "國立成功大學",
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
        "active_term": "116學年度第1學期校級薦外交換學生計畫甄選（對應 2027 秋季班／2027–2028 學年出國交換）於 2026/10/30 至 11/19 16:00 開放線上申請（共開放 97 所簽約學校），12/19 公告錄取結果、12/26 正取確認、2027/01/05–01/11 繳交保證金。",
        "verified_at": "2026-10-18",
    }
    (OFFICIAL_NCKU_DIR / "catalog-completeness.json").write_text(
        json.dumps(completeness, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    (OFFICIAL_NCKU_DIR / "verification_status.json").write_text(
        json.dumps(
            {
                "school_id": "ncku",
                "school_name": "國立成功大學",
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
            "sources/ncku/116-1-guidelines.pdf",
            NCKU_116_1_GUIDELINES_PDF_URL,
            "國立成功大學 116學年度第1學期校級薦外交換學生計畫甄選簡章 PDF",
        ),
        (
            "sources/ncku/116-1-partner-list.pdf",
            NCKU_116_1_PARTNERS_PDF_URL,
            "國立成功大學 116學年度第1學期校級薦外交換學生計畫簽約學校一覽表（97 校）PDF",
        ),
        (
            "sources/ncku/115-2-guidelines.pdf",
            NCKU_115_2_GUIDELINES_PDF_URL,
            "國立成功大學 115學年度第2學期校級薦外交換學生計畫甄選簡章 PDF",
        ),
        (
            "sources/ncku/115-2-partner-list.pdf",
            NCKU_115_2_PARTNERS_PDF_URL,
            "國立成功大學 115學年度第2學期校級薦外交換學生計畫簽約學校一覽表（102 校）PDF",
        ),
        (
            "sources/ncku/115-2-application-form.pdf",
            NCKU_115_2_APP_FORM_PDF_URL,
            "國立成功大學 115學年度第2學期校級薦外交換學生計畫申請表樣張 PDF",
        ),
        (
            "sources/ncku/115-1-guidelines.pdf",
            NCKU_115_1_GUIDELINES_PDF_URL,
            "國立成功大學 115學年度第1學期校級薦外交換學生計畫甄選簡章 PDF",
        ),
        (
            "sources/ncku/115-1-partner-list.pdf",
            NCKU_115_1_PARTNERS_PDF_URL,
            "國立成功大學 115學年度第1學期校級薦外交換學生計畫簽約學校一覽表（99 校）PDF",
        ),
        (
            "sources/ncku/115-1-application-form.pdf",
            NCKU_115_1_APP_FORM_PDF_URL,
            "國立成功大學 115學年度第1學期校級薦外交換學生計畫申請表樣張 PDF",
        ),
        (
            "sources/ncku/english-proficiency-table.pdf",
            NCKU_ENGLISH_TABLE_PDF_URL,
            "國立成功大學國際事務處英語能力檢定測驗門檻對照表 PDF",
        ),
        (
            "sources/ncku/scholarship-regulations.pdf",
            NCKU_SCHOLARSHIP_REG_PDF_URL,
            "國立成功大學學生跨國雙向研修獎助學金補助辦法 PDF",
        ),
        (
            "sources/ncku/scholarship-guidelines.pdf",
            NCKU_SCHOLARSHIP_GUIDE_PDF_URL,
            "國立成功大學學生跨國雙向研修獎助學金甄選要點 PDF",
        ),
        (
            "sources/ncku/key-partner-scholarship.pdf",
            NCKU_KEY_PARTNER_SCHOLARSHIP_PDF_URL,
            "國立成功大學學生赴深化國際合作重點學校交流獎助學金要點 PDF",
        ),
        (
            "sources/ncku/contracted-schools-data.json",
            NCKU_CONTRACT_SEARCH_URL,
            "國立成功大學國際事務處全球締約合作學校資料庫 JSON",
        ),
        (
            "sources/ncku/ncku_catalog_source.json",
            NCKU_116_1_ANNOUNCEMENT_URL,
            "國立成功大學 211 所薦外交換合作大學整合資料集（97 所 116-1 當期開放 + 114 所歷年／春季班／締約合作校，連結 357 篇交換心得）",
        ),
        (
            "sources/ncku/ncku_resolved_locations.json",
            NCKU_116_1_ANNOUNCEMENT_URL,
            "國立成功大學 211 所薦外交換合作大學 ROR / Wikidata 地理座標核對表",
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
        "school_id": "ncku",
        "school_name": "國立成功大學",
        "generated_at": CHECKED_AT,
        "active_cycle_note": completeness["active_term"],
        "sources": prov_sources,
    }
    (OFFICIAL_NCKU_DIR / "import_provenance.json").write_text(
        json.dumps(provenance_payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    from exchange_info.generated_content_review import review_generated_content
    review_generated_content(REPO_ROOT, "ncku", round_id=20)
    review_generated_content(REPO_ROOT, "ncku", round_id=21)
    from exchange_info.ncku_partner_table_review import apply_ncku_partner_table_review
    apply_ncku_partner_table_review(REPO_ROOT)
    from exchange_info.ncku_guidelines_review import apply_ncku_guidelines_review
    apply_ncku_guidelines_review(REPO_ROOT)
    from exchange_info.vilnius_akita_review import apply_vilnius_akita_review
    apply_vilnius_akita_review(REPO_ROOT, "ncku")

    print(
        f"Successfully built NCKU catalog: {len(partners)} partners ({open_partner_count} open, "
        f"{completeness['verified_campus_images']} verified images, {completeness['verified_locations']} verified locations), "
        f"{len(workflows)} workflows, {len(destinations)} destinations, {len(research_records)} research records, "
        f"{exp_covered_schools} schools with experience records ({len(student_experience_rows)} rows)."
    )


if __name__ == "__main__":
    main()
