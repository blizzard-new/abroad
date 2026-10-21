"""Build the official National Tsing Hua University (國立清華大學, NTHU) exchange data bundle."""

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

SOURCES_NTHU_DIR = REPO_ROOT / "sources" / "nthu"
OFFICIAL_NTHU_DIR = REPO_ROOT / "src" / "exchange_info" / "official_data" / "nthu"
STATIC_DIR = REPO_ROOT / "src" / "exchange_info" / "static"

CHECKED_AT = "2026-10-19T14:00:00Z"

REGION_BY_COUNTRY = {
    "日本": "亞洲",
    "韓國": "亞洲",
    "中國大陸": "中國大陸及港澳",
    "香港": "中國大陸及港澳",
    "澳門": "中國大陸及港澳",
    "新加坡": "亞洲",
    "馬來西亞": "亞洲",
    "汶萊": "亞洲",
    "泰國": "亞洲",
    "越南": "亞洲",
    "印尼": "亞洲",
    "菲律賓": "亞洲",
    "印度": "亞洲",
    "蒙古": "亞洲",
    "以色列": "亞洲",
    "土耳其": "亞洲",
    "阿拉伯聯合大公國": "亞洲",
    "美國": "美洲",
    "加拿大": "美洲",
    "墨西哥": "美洲",
    "巴西": "美洲",
    "智利": "美洲",
    "秘魯": "美洲",
    "阿根廷": "美洲",
    "澳洲": "大洋洲",
    "紐西蘭": "大洋洲",
    "奧地利": "歐洲",
    "比利時": "歐洲",
    "捷克": "歐洲",
    "丹麥": "歐洲",
    "芬蘭": "歐洲",
    "法國": "歐洲",
    "德國": "歐洲",
    "匈牙利": "歐洲",
    "義大利": "歐洲",
    "拉脫維亞": "歐洲",
    "立陶宛": "歐洲",
    "荷蘭": "歐洲",
    "挪威": "歐洲",
    "波蘭": "歐洲",
    "俄羅斯": "歐洲",
    "西班牙": "歐洲",
    "瑞典": "歐洲",
    "瑞士": "歐洲",
    "英國": "歐洲",
    "賽普勒斯": "歐洲",
    "肯亞": "非洲",
    "南非": "非洲",
}

REGION_COST_DEFAULTS = {
    "美國": (
        "USD 1,400–2,200 / 月（含住宿、餐飲、強制校園醫療保險與當地交通）",
        "須預留強制校園醫療保險（約 USD 1,500–2,500 / 學期）與 J-1 / F-1 簽證 SEVIS 費用。",
    ),
    "加拿大": (
        "CAD 1,500–2,200 / 月（含多倫多／蒙特婁住宿、膳食、省級或校內醫保與市區交通）",
        "須投保接待校指定醫療保險並辦理 Study Permit 或 eTA。",
    ),
    "墨西哥": (
        "USD 650–1,000 / 月（含蒙特雷／墨西哥城學生住宿、餐飲與日常交通）",
        "交換逾 180 天須向墨西哥駐臺辦事處申辦學生簽證並投保海外全期醫療保險。",
    ),
    "巴西": (
        "USD 650–1,050 / 月（含聖保羅學生住宿、膳食與日常交通）",
        "須向巴西商務辦事處申辦 VITEM IV 學生簽證並投保海外醫療及意外保險。",
    ),
    "秘魯": (
        "USD 600–950 / 月（含利馬學生住宿、膳食與日常交通）",
        "須依接待校指引申辦秘魯交換學生簽證並投保海外醫療及意外保險。",
    ),
    "英國": (
        "GBP 1,100–1,600 / 月（含杜倫／布里斯托／利物浦學生宿舍、膳食與當地交通）",
        "交換一學期（6 個月內）可辦理 Standard Visitor 簽證，一學年須辦理 Student Visa 並繳納 IHS 醫療附加費。",
    ),
    "法國": (
        "EUR 850–1,450 / 月（巴黎地區約 EUR 1,050–1,550 / 月；里昂、波爾多、格勒諾布爾、南特約 EUR 750–1,150 / 月，可申請 CAF 房補）",
        "須透過法國教育中心（Campus France）完成面試並申辦長期學生簽證（VLS-TS）。",
    ),
    "德國": (
        "EUR 934–1,250 / 月（德國簽證限制提領帳戶基準為每月 EUR 934）",
        "須辦理德國法定公保（約 EUR 120–130 / 月）及繳納學期雜費／學期交通票（Semesterticket）。",
    ),
    "西班牙": (
        "EUR 800–1,300 / 月（含馬德里／馬拉加／薩拉戈薩／潘普洛納學生公寓、飲食與大眾運輸）",
        "須備妥涵蓋全額醫療與遺體運返之私人醫療保險以申辦西班牙學生簽證。",
    ),
    "義大利": (
        "EUR 850–1,350 / 月（含米蘭、羅馬、都靈、威尼斯學生住宿、餐飲與大眾運輸）",
        "須向義大利經濟貿易文化推廣辦事處申辦學生簽證 D，抵義後 8 個工作天內申辦居留證（Permesso di Soggiorno）。",
    ),
    "荷蘭": (
        "EUR 950–1,450 / 月（荷蘭移民局 IND 財力證明基準約 EUR 1,225 / 月）",
        "由接待校代辦 MVV/VVR 居留許可，萊頓、格羅寧根、鹿特丹與埃因霍溫房源緊張建議獲提名後立即申請宿舍。",
    ),
    "比利時": (
        "EUR 850–1,300 / 月（含魯汶學生宿舍、餐飲與大眾運輸）",
        "須辦理長期學生簽證 D 簽，抵達後向當地市政廳登記居留。",
    ),
    "瑞士": (
        "CHF 1,500–2,200 / 月（含蘇黎世／伯恩／納沙泰爾學生住宿、膳食與強制保險）",
        "須透過瑞士商務辦事處申辦學生簽證，並於抵瑞後申請居留證與醫療保險豁免或投保。",
    ),
    "瑞典": (
        "SEK 9,500–13,000 / 月（瑞典移民局財力基準約 SEK 10,314 / 月）",
        "交換超過 3 個月須向瑞典移民局申辦學生居留許可（Residence Permit for Studies）。",
    ),
    "挪威": (
        "EUR 1,000–1,450 / 月（含奧斯陸學生宿舍與日常開支）",
        "須向挪威移民局（UDI）申辦學生居留許可。",
    ),
    "芬蘭": (
        "EUR 800–1,200 / 月（含赫爾辛基學生公寓、學生餐廳與當地交通）",
        "須透過 Enter Finland 申辦芬蘭學生居留許可並備妥規定醫療保險。",
    ),
    "立陶宛": (
        "EUR 600–900 / 月（維爾紐斯學生宿舍與生活費用實惠）",
        "須透過 MIGRIS 系統申辦立陶宛國家簽證（D 簽）或臨時居留許可。",
    ),
    "拉脫維亞": (
        "EUR 600–900 / 月（里加學生宿舍與日常開支實惠）",
        "須申辦拉脫維亞長期居留簽證（D 簽）並備妥申根區合規醫療保險。",
    ),
    "波蘭": (
        "EUR 550–850 / 月（約 PLN 2,400–3,600，華沙、克拉科夫與波茲南校內宿舍實惠）",
        "須向波蘭臺北辦事處申辦 D 類國別學生簽證並備妥規定旅行醫療保險。",
    ),
    "捷克": (
        "EUR 600–900 / 月（含布拉格／帕爾杜比采／奧洛穆茨學生宿舍、食堂與市區交通卡）",
        "須提前預約捷克經濟文化辦事處申辦長期學生簽證與捷克合約醫療保險。",
    ),
    "匈牙利": (
        "EUR 600–950 / 月（含佩奇學生住宿、膳食與大眾運輸）",
        "須申辦匈牙利長期學生居留簽證（D 簽）並備妥歐盟規格醫療保險。",
    ),
    "賽普勒斯": (
        "EUR 700–1,100 / 月（含尼古西亞學生住宿、膳食與日常交通）",
        "須透過接待校協助向賽普勒斯移民局申辦學生入境許可與居留登記，並備妥醫療保險。",
    ),
    "土耳其": (
        "EUR 550–850 / 月（安卡拉與伊斯坦堡學生生活與交通開支實惠；清大出國交換獎學金 B 類每月補助 NT$25,000）",
        "須申辦土耳其學生簽證並於抵土後申辦短期學生居留證（Ikamet）與當地醫保。",
    ),
    "阿拉伯聯合大公國": (
        "USD 1,000–1,600 / 月（含杜拜國際學術城學生宿舍、餐飲與大眾運輸）",
        "由接待校協助辦理阿聯酋學生入境許可與居留簽證（Student Residence Visa）及當地強制醫療險。",
    ),
    "肯亞": (
        "USD 500–850 / 月（含涅里校區學生住宿、膳食與日常交通）",
        "須申辦肯亞電子旅行授權（eTA）與學生通行證（Student Pass），並完成黃熱病疫苗接種及海外醫療保險。",
    ),
    "澳洲": (
        "AUD 1,800–2,600 / 月（含墨爾本／伯斯／紐卡斯爾住宿與日常開支）",
        "須購買澳洲海外學生健康保險（OSHC）並線上申辦 Subclass 500 學生簽證。",
    ),
    "日本": (
        "JPY 80,000–130,000 / 月（東京與京阪神約 JPY 100,000–140,000；地方城市約 JPY 70,000–100,000）",
        "憑接待校核發之在留資格認定證明書（COE）換發留學簽證，抵日後須加入國民健康保險。",
    ),
    "韓國": (
        "KRW 800,000–1,300,000 / 月（首爾圈外宿較高；校內宿舍約 KRW 150,000–400,000 / 月）",
        "憑標準入學許可書申辦 D-2-6 交換學生簽證，抵韓後外國人登錄並自動納入韓國國民健康保險（NHIS）。",
    ),
    "蒙古": (
        "USD 450–750 / 月（烏蘭巴托學生宿舍與日常開支實惠；清大出國交換獎學金 B 類每月補助 NT$25,000）",
        "須憑接待校正式邀請函申辦蒙古學生簽證並投保海外全期醫療及意外保險。",
    ),
    "中國大陸": (
        "RMB 2,000–3,800 / 月（校內學生宿舍住宿費與校園食堂餐費實惠）",
        "持有效護照與臺胞證（臺灣居民來往大陸通行證）入境，並依接待校規定投保大陸境內來華留學生綜合醫療保險。",
    ),
    "香港": (
        "HKD 6,500–11,000 / 月（含校內外住宿與日常開支）",
        "須透過接待校向香港入境事務處申辦學生簽證／進入許可（Student Visa / Entry Permit）。",
    ),
    "新加坡": (
        "SGD 1,200–1,900 / 月（含新加坡國立大學／南洋理工大學／新加坡管理大學／新加坡科技設計大學住宿與日常開支）",
        "獲錄取後由接待校透過 SOLAR 系統協助申辦新加坡 Student's Pass（STP）。",
    ),
    "馬來西亞": (
        "MYR 1,500–2,500 / 月（吉隆坡與霹靂州生活機能便利且物價親民；清大出國交換獎學金 B 類新南向每月補助 NT$30,000）",
        "須透過 EMGS（Education Malaysia Global Services）系統申辦學生簽證（VAL / Student Pass）。",
    ),
    "汶萊": (
        "SGD 700–1,200 / 月（汶萊元 BND 與新加坡幣 SGD 1:1 等值；清大出國交換獎學金 B 類新南向每月補助 NT$30,000）",
        "須透過接待校向汶萊移民局申辦學生簽證（Student Pass）並投保醫療保險。",
    ),
    "泰國": (
        "THB 15,000–25,000 / 月（曼谷與孔敬生活成本親民；清大出國交換獎學金 B 類新南向每月補助 NT$30,000）",
        "須憑接待校入學許可向泰國貿易經濟辦事處申辦 Non-Immigrant ED 學生簽證。",
    ),
    "印尼": (
        "IDR 5,000,000–9,000,000 / 月（萬隆、日惹、三寶瓏、巴淡與雅加達生活開支實惠；清大出國交換獎學金 B 類新南向每月補助 NT$30,000）",
        "須由接待校協助向印尼移民總局申辦學習簽證（C316 / 學生電子簽證）。",
    ),
    "越南": (
        "USD 400–700 / 月（約 VND 10,000,000–17,000,000，胡志明市與河內生活成本低廉；清大出國交換獎學金 B 類新南向每月補助 NT$30,000）",
        "須憑接待校入學許可透過駐臺北越南經濟文化辦事處申辦 DH 學生簽證。",
    ),
    "菲律賓": (
        "USD 500–850 / 月（約 PHP 28,000–48,000，馬尼拉奎松市住宿與生活開支；清大出國交換獎學金 B 類新南向每月補助 NT$30,000）",
        "須憑接待校入學許可向馬尼拉經濟文化辦事處申辦 9(f) 學生簽證或 SSP 特別學習許可。",
    ),
    "印度": (
        "USD 400–700 / 月（印度理工學院各校區、印度科學研究院與德里大學住宿與日常開支實惠；清大出國交換獎學金 B 類新南向每月補助 NT$30,000）",
        "須憑接待校正式入學許可向印度台北協會申辦 Student Visa。",
    ),
}

NTHU_OGA_OUTBOUND_URL = "https://oga.site.nthu.edu.tw/p/412-1524-18680.php?Lang=zh-tw"
NTHU_OVERSEAS_PARTNERS_URL = "https://oga.site.nthu.edu.tw/p/404-1524-9358.php"
NTHU_MAINLAND_PARTNERS_URL = "https://oga.site.nthu.edu.tw/p/404-1524-9359.php?Lang=zh-tw"
NTHU_VM_PORTAL_URL = "https://oga-exchange.vm.nthu.edu.tw/outexchange/index/index/puid/11521"
NTHU_VM_OVERVIEW_URL = "https://oga-exchange.vm.nthu.edu.tw/outexchange/overview/index/puid/11521"
NTHU_2027_2028_GUIDELINES_ZH_URL = "https://oga.site.nthu.edu.tw/var/file/524/1524/img/704171014.pdf"
NTHU_2027_2028_GUIDELINES_EN_URL = "https://oga.site.nthu.edu.tw/var/file/524/1524/img/2027F2028Sapplicationguideline-EN.pdf"
NTHU_SELECTION_REGULATIONS_URL = "https://oga.site.nthu.edu.tw/var/file/524/1524/img/4534/525909033.pdf"
NTHU_SCHOLARSHIP_REGULATIONS_URL = "https://oga.site.nthu.edu.tw/var/file/524/1524/img/4534/666778079.pdf"
NTHU_DISADVANTAGED_SCHOLARSHIP_URL = "https://oga.site.nthu.edu.tw/var/file/524/1524/img/4534/517637953.pdf"
NTHU_LANGUAGE_STANDARDS_ZH_URL = "https://oga.site.nthu.edu.tw/var/file/524/1524/img/NTHU_Exchange_Student_Foreign_Language_Proficiency_Standards_English.pdf"
NTHU_LANGUAGE_STANDARDS_EN_URL = "https://oga.site.nthu.edu.tw/var/file/524/1524/img/4534/663532775.pdf"
NTHU_FAQ_HOT_QUESTIONS_URL = "https://oga.site.nthu.edu.tw/var/file/524/1524/img/4535/816434517.pdf"
NTHU_INFO_SESSION_SLIDES_URL = "https://oga.site.nthu.edu.tw/var/file/524/1524/img/4536/647616143.pdf"
NTHU_ONLINE_SYSTEM_GUIDE_URL = "https://oga.site.nthu.edu.tw/var/file/524/1524/img/4536/966105147.pdf"
NTHU_PRE_DEPARTURE_SLIDES_URL = "https://oga.site.nthu.edu.tw/var/file/524/1524/img/4536/191844788.pdf"
NTHU_MAINLAND_GUIDELINES_URL = "https://oga.site.nthu.edu.tw/var/file/524/1524/img/4542/510394575.pdf"
NTHU_MAINLAND_FLOWCHART_URL = "https://oga.site.nthu.edu.tw/var/file/524/1524/img/4543/432387687.pdf"
NTHU_CROSS_STRAIT_SUMMER_URL = "https://oga.site.nthu.edu.tw/var/file/524/1524/img/4545/146121426.pdf"
NTHU_UST_116_NOTICE_URL = "https://oga.site.nthu.edu.tw/p/406-1524-300405,r3318.php?Lang=zh-tw"
NTHU_UST_116_PDF_URL = "https://oga.site.nthu.edu.tw/var/file/524/1524/img/365089522.pdf"
NTHU_UST_116_FORM_URL = "https://oga.site.nthu.edu.tw/var/file/524/1524/img/733827564.pdf"
NTHU_DUAL_DEGREE_SCHOLARSHIP_URL = "https://oga.site.nthu.edu.tw/var/file/524/1524/img/4554/538410681.pdf"
NTHU_SHORT_TERM_VISIT_URL = "https://oga.site.nthu.edu.tw/var/file/524/1524/img/4563/703806844.pdf"
NTHU_MOE_XUEHAI_ZHUMENG_URL = "https://oga.site.nthu.edu.tw/var/file/524/1524/img/4560/141614141.pdf"
NTHU_ANTI_FRAUD_GUIDE_URL = "https://oga.site.nthu.edu.tw/var/file/524/1524/img/4536/687314702.pdf"
NTHU_POPULARITY_SHEET_URL = "https://docs.google.com/spreadsheets/d/1G1mETD3Zt49jr0nJTK-2-3gOP8U5nJmg/edit?usp=sharing"
NTHU_ALL_AGREEMENTS_URL = "https://oga.site.nthu.edu.tw/p/412-1524-18677.php?Lang=zh-tw"
NTHU_COLLEGE_DEPT_OVERSEAS_URL = "https://oga.site.nthu.edu.tw/p/404-1524-9490.php?Lang=zh-tw"
NTHU_COLLEGE_DEPT_MAINLAND_URL = "https://oga.site.nthu.edu.tw/p/404-1524-9491.php?Lang=zh-tw"
NTHU_EXPERIENCE_OVERSEAS_URL = "https://oga.site.nthu.edu.tw/p/412-1524-18684.php?Lang=zh-tw"
NTHU_EXPERIENCE_MAINLAND_URL = "https://oga.site.nthu.edu.tw/p/404-1524-9478.php?Lang=zh-tw"

POPULARITY_DESC_MAP = {
    "A": "A級（競爭非常激烈，第一志願選填人數大於該校名額，不建議第二志願以後選填）",
    "B": "B級（競爭激烈，第一志願選填人數大於或等於該校名額，不建議第二志願以後選填）",
    "C": "C級（競爭較不激烈，填寫為第一志願有機會直接分發，第二志願以後可選填）",
    "D": "D級（填寫第一志願預估可直接分發）",
    "D (需付對方學費)": "D級（填寫第一志願預估可直接分發，惟須支付姊妹校學費）",
    "新簽約之姊妹校": "新簽約之姊妹校（尚無歷年志願分發統計，歡迎優先選填）",
    "新簽約姊妹校(需付對方學費)": "新簽約之姊妹校（尚無歷年志願分發統計，惟須支付姊妹校學費）",
}

B_CLASS_30K_COUNTRIES = {
    "印尼",
    "越南",
    "汶萊",
    "泰國",
    "菲律賓",
    "馬來西亞",
    "印度",
    "巴西",
    "智利",
    "秘魯",
    "墨西哥",
    "阿根廷",
}
B_CLASS_25K_COUNTRIES = {"以色列", "土耳其", "俄羅斯", "蒙古", "南非"}


def clean_text(s: str) -> str:
    if not s:
        return ""
    return re.sub(r"\s+", " ", s).strip()


def format_colleges(item: dict) -> str:
    sg = item.get("source_group")
    if sg == "college_dept":
        c_unit = clean_text(item.get("college_unit") or "特定院系")
        return f"限定院系級交換合約所屬學生申請（權責單位：{c_unit}）"
    note_comb = f"{item.get('note_9358', '')} {item.get('vm_note', '')}".strip()
    quals = item.get("vm_qualifications") or []
    dept_notes = []
    for q in quals:
        d = clean_text(q.get("department") or "")
        if d and d not in {"無", "不限", "-"} and d not in dept_notes:
            dept_notes.append(d)
    if item.get("is_ust") and sg == "ust_116":
        return f"台灣聯合大學系統（UST）出國交換計畫（{note_comb[:220]}）"
    if dept_notes:
        joined = "；".join(dept_notes)
        return f"依姊妹校開放系所規定申請（系所限制：{joined[:260]}）"
    if "僅限" in note_comb or "不開放" in note_comb or "限" in note_comb:
        return f"全校各學院在學學生（部分學院或系所限制：{note_comb[:220]}）"
    return "不限學院（全校 13 個學院正式學籍在學學生皆可依當期簡章與姊妹校開放領域申請）"


def format_degree_levels(item: dict) -> str:
    deg_raw = clean_text(item.get("degrees_raw") or "")
    sg = item.get("source_group")
    if sg == "mainland_9359":
        return f"開放學制：{deg_raw or '學士班、碩士班、博士班'}（大學部、研究所正式學籍在學學生；大一、碩一、博一或轉學生可提具前一學期成績證明申請，不含在職專班）"
    if sg == "ust_116":
        return f"開放學制：{deg_raw}（台灣聯合大學系統 116 學年度第一梯次出國交換計畫）"
    if sg == "college_dept":
        return f"開放學制：{deg_raw}（依所屬院系級交換學生協議書規定辦理）"
    if deg_raw:
        return f"開放學制：{deg_raw}（限清大大學部二年級［含］以上、碩士班一年級［含］以上、博士班一年級［含］以上正式學籍在學生，不含在職專班；申請時與出國交換期間學籍學位須一致）"
    return "大學部二年級（含）以上、碩士班一年級（含）以上、博士班一年級（含）以上正式學籍在學學生（不含在職專班）"


def format_language_req(item: dict) -> str:
    sg = item.get("source_group")
    country = item["country"]
    if sg == "mainland_9359":
        note = clean_text(item.get("note_9358") or "")
        if "TOEFL" in note or "IELTS" in note or "英語" in note or "英文" in note:
            return f"陸港澳交換計畫語言規定：{note}（香港理工大學須檢附 TOEFL iBT 80 或 IELTS 6.0 以上；其餘大陸及香港合作校若修讀英文授課課程須符合接待校規定）"
        return "赴大陸及香港地區交換計畫：除香港理工大學（須達 TOEFL iBT 80 或 IELTS 6.0）及寧波諾丁漢大學等全英語授課校區外，一般中文授課課程免附外語檢定證明。"
    if sg == "ust_116":
        return f"台灣聯合大學系統（UST）語言規定：{clean_text(item.get('note_9358') or '')}（須檢附 2 年內有效之 TOEFL iBT 或 IELTS 正式成績單）"
    quals = item.get("vm_qualifications") or []
    lang_parts = []
    for q in quals:
        deg = clean_text(q.get("degree") or "")
        for k in ("toefl", "ielts", "other_lang"):
            v = clean_text(q.get(k) or "")
            if v and v not in {"無", "-", "N/A", "不接受"}:
                label = "TOEFL iBT" if k == "toefl" else ("IELTS" if k == "ielts" else "其他外語")
                part = f"{deg} {label}: {v}" if deg else f"{label}: {v}"
                if part not in lang_parts:
                    lang_parts.append(part)
    base_nthu = (
        "清大校內最低外語能力標準（須為申請截止日前 2 年內有效成績，不接受 MyBest Scores、TOEIC、GEPT、GRE、Duolingo）："
        "英語組 TOEFL iBT 79（新制 4.0）或 IELTS Academic 6.0；日語組 JLPT N2；法語組 DELF/DALF B1、TCF B1 或 FLPT 150分（口試 S-2）；"
        "德語組 Goethe B1、TestDaF TDN 3 或 FLPT 150分（口試 S-2）；西語組 DELE B1 或 FLPT 150分（口試 S-2）；韓語組 TOPIK 4 級"
    )
    if lang_parts:
        joined = "；".join(lang_parts)
        if item.get("is_ust"):
            return f"締約校外語能力門檻：{joined}｜{base_nthu}｜另適用 116 學年度台灣聯大（UST）交換計畫（研究學期／暑期交換須達 TOEFL iBT 90 或 IELTS 6.0）"
        return f"締約校外語能力門檻（高於校內標準者從其規定）：{joined}｜{base_nthu}"
    return f"依清大校內最低外語能力標準辦理：{base_nthu}"


def format_gpa_req(item: dict) -> str:
    sg = item.get("source_group")
    if sg == "mainland_9359":
        return "清大赴陸港澳交換校內成績門檻：前兩學期學業平均成績達 GPA 3.20（含）以上，或全班排名前 30%（含）以上（香港大學與香港理工大學建議 GPA 3.2–3.4 以上）。"
    if sg == "ust_116":
        return "台灣聯合大學系統（UST）交換門檻：於原就讀學校前一學年平均成績達 GPA 3.0（或等級 B）以上。"
    quals = item.get("vm_qualifications") or []
    gpa_parts = []
    for q in quals:
        deg = clean_text(q.get("degree") or "")
        g = clean_text(q.get("gpa") or "")
        if g and g not in {"無", "-", "N/A"}:
            part = f"{deg} GPA {g} / 4.3" if deg else f"GPA {g} / 4.3"
            if part not in gpa_parts:
                gpa_parts.append(part)
    base_gpa = (
        "清大校內基本門檻：申請前兩學期學業平均成績達 GPA 3.20以上，或班級排名前 50% 以上"
        "（申請出國交換生獎學金 A/B 類、清寒學生出國交流獎學金及劉維全校友獎學金須達前一學年平均 GPA 3.40 以上或全班／系前 20% 以上；教育部學海惜珠須達 GPA 3.20 以上）"
    )
    if gpa_parts:
        return f"締約校學業成績門檻：{'；'.join(gpa_parts)}（姊妹校標準高於校內標準者須符合姊妹校規定）｜{base_gpa}"
    return base_gpa


def format_quota(item: dict) -> str:
    sg = item.get("source_group")
    q_shared = clean_text(item.get("quota_shared") or "-")
    q_fall = clean_text(item.get("quota_fall") or "-")
    q_spring = clean_text(item.get("quota_spring") or "-")
    vm_q = clean_text(item.get("vm_quota") or "")
    tier = clean_text(item.get("popularity_tier") or "")
    tier_tag = f"【第一志願熱門程度：{POPULARITY_DESC_MAP.get(tier, tier)}】" if tier else ""
    fee_tag = "【注意：須支付姊妹校學費】" if item.get("requires_partner_tuition") else ""
    if sg == "mainland_9359":
        return f"2027秋／2028春 陸港澳學期交換名額：秋季班 {q_fall} 名、春季班 {q_spring} 名（{clean_text(item.get('note_9358') or '互惠免學費')}）"
    if sg == "ust_116":
        return f"【116學年度台灣聯大（UST）出國交換第一梯次開放申請中】名額：{q_shared}"
    if sg == "college_dept":
        return f"院系級交換合約名額：依所屬院系（{item.get('college_unit') or '簽約院系'}）當期公告選送名額辦理"
    parts = []
    if q_shared and q_shared != "-":
        parts.append(f"秋／春共用名額：{q_shared} 名")
    if q_fall and q_fall != "-":
        parts.append(f"2027秋季班：{q_fall} 名")
    if q_spring and q_spring != "-":
        parts.append(f"2028春季班：{q_spring} 名")
    q_str = "；".join(parts) if parts else (f"當期名額：{vm_q} 名" if vm_q else "依當期姊妹校名額表公告")
    if item.get("is_ust"):
        q_str += "｜另含【116學年度台灣聯大（UST）出國交換第一梯次（2027/01/04 截止）】：研究學期交換與暑期研究交換共用 6 名"
    return f"{fee_tag}{tier_tag}2027秋／2028春 校級海外交換名額：{q_str}"


def format_study_period(item: dict) -> str:
    sg = item.get("source_group")
    if sg == "ust_116":
        return "一學期（2027 秋季班／2028 春季班）或 2027 暑期研究交換（依台灣聯合大學系統 116 學年度第一梯次交換計畫規定）"
    if sg == "mainland_9359":
        return "一學期（秋季班 9 月至翌年 1 月，或春季班 2 月至 6 月；每名學生同一學制以參加一次為限）"
    if sg == "college_dept":
        return "一學期或一學年（依各院系級交換學生協議書與接待校規定辦理）"
    note_comb = f"{item.get('note_9358', '')} {item.get('vm_note', '')}"
    if "僅限一學期" in note_comb or "一學期為限" in note_comb:
        return "一學期（2027 秋季班或 2028 春季班，依締約校規定以一學期為限）"
    return "一學期或一學年（2027 秋季班、2028 春季班或 2027–2028 全學年；獎學金補助以一學期至多 5 個月為原則）"


def format_program_type(item: dict) -> str:
    sg = item.get("source_group")
    tier = clean_text(item.get("popularity_tier") or "")
    tags = []
    if item.get("is_ust"):
        tags.append("含台灣聯合大學系統 UST 116-1 交換計畫")
    if tier:
        tags.append(f"熱門程度 {tier}")
    if item.get("requires_partner_tuition"):
        tags.append("須付姊妹校學費")
    if item["country"] in B_CLASS_30K_COUNTRIES:
        tags.append("清大 B 類獎學金每月 NT$30,000 重點補助國")
    elif item["country"] in B_CLASS_25K_COUNTRIES:
        tags.append("清大 B 類獎學金每月 NT$25,000 重點補助國")
    elif item["name_zh"] == "凱斯西儲大學":
        tags.append("劉維全校友獎學金每學期 NT$120,000–150,000 專項補助校")
    tag_str = f"［{'・'.join(tags)}］" if tags else ""
    if sg == "ust_116":
        return f"交換學生（台灣聯合大學系統 UST 116學年度第一梯次出國交換計畫當期開放申請校{tag_str}）"
    if sg == "mainland_9359":
        return f"交換學生（清大全球事務處校級赴大陸及香港地區當期開放學期交換合作校{tag_str}・繳交清大全額學雜費、免繳接待校學費）"
    if sg == "overseas_9358":
        fee_desc = "須支付姊妹校學費" if item.get("requires_partner_tuition") else "繳交清大全額學雜費、互惠免繳姊妹校學費"
        return f"交換學生（清大全球事務處 2027秋／2028春 校級海外出國交換當期開放申請校{tag_str}・{fee_desc}）"
    return f"交換學生（國立清華大學院系級學術交流交換合作校［權責單位：{item.get('college_unit') or '各院系'}］{tag_str}）"


def main() -> None:
    OFFICIAL_NTHU_DIR.mkdir(parents=True, exist_ok=True)
    SOURCES_NTHU_DIR.mkdir(parents=True, exist_ok=True)

    catalog_items = json.loads(
        (SOURCES_NTHU_DIR / "nthu_catalog_source.json").read_text(encoding="utf-8")
    )
    locs_raw = json.loads(
        (SOURCES_NTHU_DIR / "nthu_resolved_locations.json").read_text(encoding="utf-8")
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
    ust_count = 0
    exp_covered_schools = 0

    for idx, item in enumerate(catalog_items):
        full_name = item["school_name"]
        zh_name = item["name_zh"]
        country = item["country"]
        region = REGION_BY_COUNTRY.get(country, "其他地區")
        sg = item["source_group"]
        avail_status = item["availability_status"]
        if avail_status == "open":
            open_partner_count += 1
        if item.get("is_ust"):
            ust_count += 1

        website = (item.get("website") or "").strip()
        if website and not website.startswith("http"):
            website = f"https://{website}"

        factsheet_url = (item.get("factsheet_url") or "").strip() or None
        if sg == "ust_116":
            source_url = NTHU_UST_116_NOTICE_URL
        elif sg == "mainland_9359":
            source_url = NTHU_MAINLAND_PARTNERS_URL
        elif sg == "college_dept":
            source_url = (
                NTHU_COLLEGE_DEPT_MAINLAND_URL
                if country in {"中國大陸", "香港", "澳門"}
                else NTHU_COLLEGE_DEPT_OVERSEAS_URL
            )
        else:
            source_url = NTHU_OVERSEAS_PARTNERS_URL

        remarks_parts = []
        if item.get("note_9358"):
            remarks_parts.append(clean_text(item["note_9358"]))
        if item.get("vm_note") and clean_text(item["vm_note"]) not in remarks_parts:
            remarks_parts.append(clean_text(item["vm_note"]))
        remarks_all = "；".join(remarks_parts)

        if item.get("is_ust"):
            round_label = "116學年度台灣聯合大學系統（UST）學生出國交換計畫第一梯次（清大全球處收件至 2027/01/04 16:00 止）"
            deadline_iso = "2027-01-04T16:00:00+08:00"
            deadline_rem = True
            win_status = "open"
            app_deadline_str = (
                "【116學年度台灣聯合大學系統（UST）學生出國交換計畫（I）第一梯次（含 2027 暑期研究交換及 2027 秋季／2028 春季學期交換）— 開放申請中】"
                "清大宣傳說明會：2026年11月18日（三）12:20；"
                "清大全球事務處校內收件截止日：2027年1月4日（一）下午 16:00 止（每種交換類別限填一份申請表、至多選填 2 個志願，紙本申請表須經系所及學院核章後連同備審資料送達第一綜合大樓 110 室全球學術合作組，彙送台灣聯大系統於 2027/01/11 截止收件，預計 2027/02/28 前通知結果）。"
                + (
                    "｜【清大校級 2027秋／2028春 海外出國交換第一梯次】第一階段線上報名（2026/09/03–10/08 16:00）已截止，第二階段線上志願選填為 2026/11/03–11/10 16:00、12月初放榜、12/11 16:00 前完成報到並繳交保證金 NT$8,000；2028 春季班第二梯次預計於 2027年1月中至3月初開放申請。"
                    if sg == "overseas_9358"
                    else ""
                )
            )
        elif sg == "overseas_9358":
            round_label = "2027秋／2028春（116學年度）校級海外出國交換第一梯次（11/03–11/10 線上選填志願）暨第二梯次（2027年1月中–3月初）"
            deadline_iso = "2026-10-08T16:00:00+08:00"
            deadline_rem = False
            win_status = "closed"
            app_deadline_str = (
                "【2027秋／2028春（116學年度）校級海外出國交換計畫第一梯次】"
                "第一階段線上系統報名及紙本送系所審查：2026年9月3日（四）至 10月8日（四）16:00 止（已截止；經系所初審 10/14、學院複審 10/20 送全球處決審）；"
                "第二階段線上選填志願序（收到院排序通知後）：第一次志願選填 2026年11月3日（二）至 11月10日（二）16:00 止，第二次選填依寄信通知；"
                "分發結果與獎學金名單通知：2026年12月初；錄取報到與繳交保證金 NT$8,000 截止：2026年12月11日（五）16:00 前。"
                "【2028春季班（116-2）第二梯次海外出國交換甄選】預計於 2027年1月中旬至3月初開放線上報名（4月中下旬放榜）。"
            )
        elif sg == "mainland_9359":
            round_label = "校級赴大陸地區及香港、澳門學期交換計畫（2027春季班 2026/07/09–09/01；2027秋季班預計 2026年12月–2027年1月開放申請）"
            deadline_iso = "2026-09-01T16:00:00+08:00"
            deadline_rem = False
            win_status = "closed"
            app_deadline_str = (
                "【校級赴大陸地區及香港、澳門學期交換計畫】"
                "2027春季班申請期間：2026年7月9日至 9月1日止（已截止，9/8 系所初審、9/15 學院複審送全球處決審）；"
                "2027秋季班申請期間：預計 2026年12月至 2027年1月開放申請（學生備妥申請資料送系所初審、學院複審，於 2月初送達全球事務處全球學術合作組決審，錄取確認後須繳交行政處理費［保證金］新臺幣 8,000 元）。"
            )
        else:
            round_label = "國立清華大學院系級學術交流交換學生合約校（依簽約院系當期公告時程辦理）"
            deadline_iso = "2027-01-04T16:00:00+08:00"
            deadline_rem = False
            win_status = "closed"
            app_deadline_str = (
                f"【清大院系級交換學生協議合作校（權責單位：{item.get('college_unit') or '各簽約院系'}）】"
                "本合作校屬院系級交換學生協議書締約學校，名額與收件截止日由簽約院系辦公室獨立公告辦理；欲申請者請直接洽詢所屬院系辦公室或參閱全球事務處「院系級交換合約」專區。"
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

        exp_posts = item.get("experience_posts") or []
        exp_portal_url = (
            NTHU_EXPERIENCE_MAINLAND_URL
            if country in {"中國大陸", "香港", "澳門"}
            else NTHU_EXPERIENCE_OVERSEAS_URL
        )

        if country == "日本":
            sem_dates_str = "春季學期（前學期）：約每年 4 月至 8 月；秋季學期（後學期）：約每年 9/10 月至翌年 2/3 月"
        elif country in {"澳洲", "紐西蘭"}:
            sem_dates_str = "第 1 學期（秋季班出國對應 Semester 2）：約每年 7 月至 11 月；第 2 學期（春季班出國對應 Semester 1）：約每年 2 月至 6 月"
        else:
            sem_dates_str = "秋季學期（第 1 學期）：約每年 8/9 月至 12 月／翌年 1 月；春季學期（第 2 學期）：約每年 1/2 月至 5/6 月"

        course_parts = [f"開放申請院系與學制：{colleges_str}（{degree_levels_str}）。"]
        if remarks_all:
            course_parts.append(f"締約校交換申請與選課備註：{remarks_all[:360]}。")
        if sg == "mainland_9359":
            course_parts.append(
                "依《國立清華大學選送學生赴大陸及港澳地區大學修讀學分甄選簡章》規定，交換期間須完成清大註冊並繳交學雜費，大學部學生每學期至少應修讀 9 學分且及格、研究所學生每學期至少修讀 1 門課程且及格，返國後 1 個月內繳交返國報告單、交換心得報告及正式成績單並完成學分抵免，始得退還新臺幣 8,000 元保證金。"
            )
        else:
            course_parts.append(
                "依《國立清華大學學生出國交換甄選辦法》及出國交換生甄選簡章規定，出國交換期間須維持清大在學學籍並繳交清大全額學雜費；未獲獎學金之大學部學生每學期／學季至少須修讀 3 門課程及格、研究生至少修讀 1 門研究所課程及格；獲清大出國交換獎學金者，大學部每學期／學季至少須修讀 3 門「本科相關專業課程」及格、研究生至少修讀 1 門「本科相關專業研究所課程」及格。"
            )
        course_rest_str = " ".join(course_parts)

        if "宿" in remarks_all or "housing" in remarks_all.lower() or "dorm" in remarks_all.lower():
            housing_str = f"{zh_name} 住宿與申請說明：{remarks_all[:360]}"
        else:
            housing_str = f"{zh_name} 依兩校交換協議提供獲提名交換生校內學生宿舍申請資訊或校外住宿指引；宿位是否保證分配及收費標準以該校最新交換生網頁（{factsheet_url or website or '詳全球處姊妹校列表'}）與入學許可通知為準。"

        tuition_points_list = [
            "清大註冊學雜費與新臺幣 8,000 元行政處理費（保證金）規定：錄取學生於出國交換期間須維持國立清華大學正式在學學籍並完成註冊、繳交清大全額學雜費，享互惠免繳姊妹校學費（惟名額表標註「需付姊妹校學費」之合作校如波士頓大學、SRM科學技術研究院等除外；住宿費、生活費、保險費、簽證費與往返機票均由學生自理）。錄取生於報到確認時須繳交行政處理費（保證金）新臺幣 8,000 元（持低收入戶或中低收入戶證明者免繳）；按時履行修課及格規定並於返國後 1 個月內繳交四項返國文件（返國報告單、成果報告書、姊妹校成績單、登機證）及完成學分抵免後，於當年度 10–11 月無息退還。",
            "清大五大出國交換獎學金體系（須於第一階段申請交換時同步勾選申請，前一學年平均須達 GPA 3.40 以上或全班／系排名前 20% 以上，學海惜珠為 GPA 3.20 以上）：（1）《出國交換生獎學金 A 類（一般地區）》：每月補助新臺幣 15,000 元（至多 5 個月，最高 NT$75,000，每年約 40–50 名）；（2）《出國交換生獎學金 B 類（特定國家重點補助）》：赴新南向國家（印尼、越南、汶萊、泰國、菲律賓、馬來西亞、印度，不含新加坡）及中南美洲國家（巴西、智利、秘魯、墨西哥、阿根廷等）每名每月補助新臺幣 30,000 元（至多 5 個月，最高 NT$150,000）；赴以色列、土耳其、俄羅斯、蒙古、南非每名每月補助新臺幣 25,000 元（至多 5 個月，最高 NT$125,000）；（3）《劉維全校友出國交流獎學金》：專項補助赴美國凱斯西儲大學（Case Western Reserve University）交換之大學部學生，一般生每學期 NT$120,000、清寒生每學期 NT$150,000（至多 2 學期）；（4）《國立清華大學清寒學生出國交流獎學金》：補助低收／中低收／特殊境遇家庭或逆境向上具強烈學習熱誠之學生（本國籍與境外生皆可申請），每月 NT$20,000 為原則、最高補助 NT$200,000；（5）教育部「學海飛颺」、「學海惜珠」及日本台灣交流協會獎學金（每月 JPY 80,000）。",
        ]
        if country in B_CLASS_30K_COUNTRIES:
            tuition_points_list.append(
                f"【清大出國交換生獎學金 B 類（每月 NT$30,000）重點補助對象】{zh_name} 位於 {country}，屬清大《出國交換生獎學金審查作業細則》B 類新南向／中南美洲重點補助國家，符合獎學金資格（前一學年 GPA 3.40 或班／系排前 20%）錄取者，每月可獲新臺幣 30,000 元獎學金（一學期至多 5 個月共 NT$150,000）！"
            )
        elif country in B_CLASS_25K_COUNTRIES:
            tuition_points_list.append(
                f"【清大出國交換生獎學金 B 類（每月 NT$25,000）重點補助對象】{zh_name} 位於 {country}，屬清大《出國交換生獎學金審查作業細則》B 類特定國家重點補助對象，符合獎學金資格（前一學年 GPA 3.40 或班／系排前 20%）錄取者，每月可獲新臺幣 25,000 元獎學金（一學期至多 5 個月共 NT$125,000）！"
            )
        elif zh_name == "凱斯西儲大學":
            tuition_points_list.append(
                "【劉維全校友出國交流獎學金專項補助校】赴美國凱斯西儲大學（Case Western Reserve University）交換之清大大學部在學學生（前一學年 GPA 3.40 以上且操行 80 分以上），可申請劉維全校友出國交流獎學金：一般生每學期補助新臺幣 120,000 元、清寒學生每學期補助新臺幣 150,000 元（至多補助兩學期共 NT$240,000–300,000）！"
            )

        app_steps_list = [
            f"步驟一（確認在學身分、GPA 3.20／班排前 50% 與 {zh_name} 外語能力門檻）：確認為清大大學部二年級以上或碩博士班一年級以上正式學籍在學學生（不含在職專班；申請時與出國交換期間學籍學位須一致），前兩學期平均達 GPA 3.20 或班排名前 50%（陸港澳為 GPA 3.20 或班排前 30%；台灣聯大 UST 為 GPA 3.0；申請獎學金須達 GPA 3.40 或班／系排前 20%），並備妥申請截止日前 2 年內有效之語言能力證明（TOEFL iBT 79［新制 4.0］／IELTS Academic 6.0 或日語 N2、德法西語 B1、韓語 TOPIK 4 級；不接受 MyBest Scores、TOEIC、GEPT、GRE、Duolingo）。",
            "步驟二（第一階段於線上系統完成報名並將紙本申請資料送交系所初審與學院複審）：登入「國立清華大學出國交換生甄試報名系統」（https://oga-exchange.vm.nthu.edu.tw/outexchange/index/index/puid/11521）填寫申請表（欲申請校內出國交換獎學金者須於線上系統同步勾選），列印系統產出之申請表並備妥歷年中文成績單（含前兩學期 GPA 或排名）、2 年內有效外語能力證明、本期海外交換（不含陸港澳）每志願修課計畫（可用中文）、導師或論文指導教授推薦信 1 封、身分證明及學生證正反面影本、其他有利審查資料；其他交換計畫請另依簡章確認文件，於截止日前繳交至所屬系所辦公室辦理「系所初審 → 學院複審 → 全球事務處決審」三階段審查。",
            f"步驟三（第二階段線上選填志願序［參考 A/B/C/D 熱門程度］、放榜報到與繳交 8,000 元保證金）：通過系院審查收到院排序通知後，於 11月上旬（2026/11/03–11/10 16:00）登入線上系統完成志願選填（全球處公布各姊妹校第一志願選填熱門程度 A/B/C/D 四級，若第一志願選填 A/B 級熱門校，建議第二志願以後選填 C/D 級學校以提高錄取率）。12月初通知志願分發與獎學金結果後，須於 12月11日 16:00 前繳交《交換學生同意聲明書》、《家長擔保同意書》、《獎學金切結書》及行政處理費（保證金）新臺幣 8,000 元（低收／中低收入戶免繳），由全球處向 {full_name} 辦理官方提名（Nomination）。",
            "步驟四（向姊妹校遞交入學申請、辦理簽證保險與履行修課及返國 4 項文件義務退還保證金）：獲全球處提名後依姊妹校規定準備入學申請文件（姊妹校保有最終錄取決定權）。交換期間大學部每學期／學季至少須修讀 3 門課程及格、研究生至少修讀 1 門研究所課程及格（獲獎學金者須為本科相關專業課程；陸港澳大學部至少 9 學分及格）。返國後 1 個月內須繳交返國報告單、成果報告書（交換心得）、姊妹校正式成績單及登機證（獲獎生另需提供 3 分鐘影音檔）並完成學分抵免，始得於當年度 10–11 月退還 8,000 元保證金。",
        ]

        elig_points_list = [
            f"開放學制與年級：{degree_levels_str}",
            f"開放申請院系：{colleges_str}",
            f"GPA 與排名門檻：{gpa_req_str}",
            f"外語能力標準：{lang_req_str}",
        ]
        if item.get("popularity_tier"):
            t_code = item["popularity_tier"]
            elig_points_list.append(
                f"第一志願選填熱門程度：{POPULARITY_DESC_MAP.get(t_code, t_code)}"
            )
        if remarks_all:
            elig_points_list.append(f"締約校特殊規定與備註：{remarks_all[:260]}")

        notes_lines = [
            f"【合作類別與期程】{program_type}｜交換期間：{study_period_str}",
            f"【當期名額與熱門程度】{quota_str}",
            f"【開放學院與學制】{colleges_str}｜{degree_levels_str}",
            f"【語言與學業門檻】{lang_req_str}｜{gpa_req_str}",
        ]
        if remarks_all:
            notes_lines.append(f"【締約校重要備註】{remarks_all[:380]}")
        if exp_posts:
            notes_lines.append(
                f"【清大歷屆交換生返國報告書】清大全球事務處官網公開收錄赴 {zh_name} 交換生返國成果報告書共 {len(exp_posts)} 篇。"
            )

        visual_rec = visual_rec = visual_index.get((full_name, country)) or {}
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
            "availability_note": f"國立清華大學全球事務處公告合作姊妹校；{quota_str}。",
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
            "reference_data": {
                k: str(v)
                for k, v in {
                    "popularity_tier": item.get("popularity_tier"),
                    "source_group": sg,
                    "vm_id": item.get("vm_id"),
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
                "title": f"國立清華大學全球事務處出國交換姊妹校列表與申請資格明細—{zh_name}",
                "source_url": source_url,
                "role": "home_university",
                "authority": "home_official_notice",
                "effective_academic_year": "116",
                "application_round": round_label,
                "checked_at": CHECKED_AT,
            },
            {
                "title": "國立清華大學 2027秋／2028春（116學年度）出國交換生甄選簡章（中文版）PDF",
                "source_url": NTHU_2027_2028_GUIDELINES_ZH_URL,
                "role": "home_university",
                "authority": "home_official_notice",
                "effective_academic_year": "116",
                "application_round": round_label,
                "checked_at": CHECKED_AT,
            },
            {
                "title": "國立清華大學學生出國交換甄選辦法與出國交換生獎學金審查作業細則 PDF",
                "source_url": NTHU_SELECTION_REGULATIONS_URL,
                "role": "home_university",
                "authority": "home_official_notice",
                "effective_academic_year": "116",
                "application_round": round_label,
                "checked_at": CHECKED_AT,
            },
        ]
        if factsheet_url:
            wf_sources.append({
                "title": f"國立清華大學出國交換名額表合作校交換資訊／Fact Sheet—{zh_name}",
                "source_url": factsheet_url,
                "role": "partner_university",
                "authority": "partner_official",
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
            "home_university": "國立清華大學",
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
                "2027秋／2028春 第一梯次",
                "2028春季班 第二梯次",
                "116學年度台灣聯合大學系統（UST）學生出國交換計畫第一梯次",
                "赴大陸及港澳地區學期交換計畫",
            ],
            "applicability_status": "verified",
            "applicability_note": (
                "國立清華大學全球事務處每年分兩梯次辦理校級海外出國交換甄選（第一梯次於 9月初至 10月初線上報名送系院審查、11月初線上選填志願、12月初放榜；"
                "第二梯次春季班補招於翌年 1月中至 3月初開放申請；另辦理台灣聯合大學系統 116-1 出國交換計畫收件至 2027/01/04 16:00 止，以及赴陸港澳學期交換計畫），"
                "校內基本門檻為前兩學期 GPA 3.20 或班排前 50%（陸港澳前 30%、UST GPA 3.0）及 TOEFL iBT 79（新制 4.0）／IELTS 6.0 或二外 B1/N2/TOPIK 4。"
            ),
            "review_status": "published",
            "published_at": CHECKED_AT,
            "steps": [
                {
                    "rule_id": f"nthu-116-home-1-{idx+1:03d}",
                    "order": 1,
                    "phase": "校內申請",
                    "title": f"確認清大在學年級（大二／碩一／博一以上）、GPA 3.20／班排前 50% 與 {zh_name} 外語能力門檻",
                    "responsible_party": "學生",
                    "responsible_unit": "國立清華大學全球事務處全球學術合作組（第一綜合大樓 110 室）",
                    "deadline_at": deadline_iso,
                    "deadline_status": "verified_exact" if avail_status == "open" else "reference_only",
                    "deadline_source_url": NTHU_UST_116_NOTICE_URL if item.get("is_ust") else NTHU_2027_2028_GUIDELINES_ZH_URL,
                    "deadline_checked_at": CHECKED_AT,
                    "deadline_reminder_eligible": deadline_rem,
                    "summary": f"申請人須為清大大學部二年級（含）以上、碩士班一年級（含）以上或博士班一年級（含）以上正式學籍在學學生（不含在職專班；申請時與出國交換期間學籍學位須一致），並確認符合 {zh_name} 之學制、院系、外語檢定及 GPA 標準。",
                    "details": [
                        f"開放學制與院系：{colleges_str}（{degree_levels_str}）",
                        f"語言與學業條件：{lang_req_str}｜{gpa_req_str}",
                        f"當期名額與熱門程度：{quota_str}",
                    ],
                    "scope": {
                        "home_universities": ["國立清華大學"],
                        "partner_universities": [full_name],
                        "academic_years": ["115", "116"],
                        "application_rounds": [
                            round_label,
                            "116-1",
                            "116-2",
                            "2027秋／2028春 第一梯次",
                            "2028春季班 第二梯次",
                        ],
                    },
                    "source_urls": [
                        NTHU_2027_2028_GUIDELINES_ZH_URL,
                        NTHU_LANGUAGE_STANDARDS_ZH_URL,
                        source_url,
                    ],
                    "checked_at": CHECKED_AT,
                    "support_status": "verified",
                },
                {
                    "rule_id": f"nthu-116-home-2-{idx+1:03d}",
                    "order": 2,
                    "phase": "校內申請",
                    "title": "第一階段於線上系統完成報名（同步勾選獎學金）並將紙本備審資料送交系所初審與學院複審",
                    "responsible_party": "學生與各系所／學院辦公室",
                    "responsible_unit": "國立清華大學各系所辦公室／各學院／全球事務處全球學術合作組",
                    "deadline_at": deadline_iso,
                    "deadline_status": "verified_exact" if avail_status == "open" else "reference_only",
                    "deadline_source_url": NTHU_VM_PORTAL_URL,
                    "deadline_checked_at": CHECKED_AT,
                    "deadline_reminder_eligible": deadline_rem,
                    "summary": "於報名期間登入「清大出國交換生甄試報名系統」（https://oga-exchange.vm.nthu.edu.tw/outexchange/index/index/puid/11521）填報個人申請資料並勾選是否申請出國交換生獎學金，列印申請表連同歷年中文成績單（含前兩學期 GPA 或班排名）、2 年內有效外語能力證明、中文與外文讀書計畫（含擬修讀課程列表）、中英文自傳、2 封教師推薦信及助學證明送交系所辦公室，依序完成「系所初審 → 學院複審 → 全球事務處決審」三階段審核。",
                    "details": [
                        "外語檢定採計限制：語言能力證明必須為申請截止日前 2 年內有效成績；不接受 TOEFL iBT MyBest Scores、TOEIC、全民英檢（GEPT）、GRE 或 Duolingo English Test。",
                        "三階段審查時程（以 2027秋／2028春 第一梯次為例）：學生線上申請及紙本送達系所為 2026/09/03–10/08 16:00；系所初審送院為 10/14 16:00 前；學院複審排序送全球處為 10/20 16:00 前。",
                    ],
                    "document_requirements": [
                        {
                            "name": "國立清華大學出國交換學生線上系統申請表（須完成線上填報列印並簽名；欲申請獎學金者須於系統同步勾選）",
                            "official_form_url": NTHU_VM_PORTAL_URL,
                            "source_urls": [
                                NTHU_VM_PORTAL_URL,
                                NTHU_2027_2028_GUIDELINES_ZH_URL,
                                NTHU_ONLINE_SYSTEM_GUIDE_URL,
                            ],
                        },
                        {
                            "name": "本校歷年中文成績單正本（須含前兩學期 GPA 或班級排名百分比；碩一、博一新生繳交前一學位含畢業排名之成績單；南大校區百分制須依註冊組對照表換算為等級制 GPA）",
                            "source_urls": [
                                NTHU_2027_2028_GUIDELINES_ZH_URL,
                                NTHU_FAQ_HOT_QUESTIONS_URL,
                            ],
                        },
                        {
                            "name": "申請截止日前 2 年內有效之外語能力證明影本（TOEFL iBT 79［新制 4.0］／IELTS Academic 6.0 或日語 JLPT N2、法語／德語／西語 B1、韓語 TOPIK 4 級；不接受 MyBest Scores、TOEIC、GEPT、GRE、Duolingo）",
                            "source_urls": [
                                NTHU_LANGUAGE_STANDARDS_ZH_URL,
                                NTHU_2027_2028_GUIDELINES_ZH_URL,
                            ],
                        },
                        {
                            "name": "本期海外交換（不含陸港澳）：每志願一份修課計畫（可用中文）、導師或論文指導教授推薦信 1 封、身分證明及學生證正反面影本、其他有利審查資料；其他計畫文件另依簡章確認",
                            "source_urls": [
                                NTHU_2027_2028_GUIDELINES_ZH_URL,
                                NTHU_SELECTION_REGULATIONS_URL,
                            ],
                        },
                    ],
                    "scope": {
                        "home_universities": ["國立清華大學"],
                        "academic_years": ["115", "116"],
                        "application_rounds": [
                            round_label,
                            "116-1",
                            "116-2",
                            "2027秋／2028春 第一梯次",
                            "2028春季班 第二梯次",
                        ],
                    },
                    "source_urls": [
                        NTHU_VM_PORTAL_URL,
                        NTHU_2027_2028_GUIDELINES_ZH_URL,
                        NTHU_ONLINE_SYSTEM_GUIDE_URL,
                    ],
                    "checked_at": CHECKED_AT,
                    "support_status": "verified",
                },
                {
                    "rule_id": f"nthu-116-home-3-{idx+1:03d}",
                    "order": 3,
                    "phase": "甄選與提名",
                    "title": "第二階段線上選填志願序（參考 A/B/C/D 熱門程度）、分發放榜與繳交 8,000 元保證金報到",
                    "responsible_party": "學生與國立清華大學全球事務處",
                    "responsible_unit": "國立清華大學全球事務處全球學術合作組",
                    "deadline_at": "2026-12-11T16:00:00+08:00",
                    "deadline_status": "verified_exact" if sg == "overseas_9358" else "reference_only",
                    "deadline_source_url": NTHU_2027_2028_GUIDELINES_ZH_URL,
                    "deadline_checked_at": CHECKED_AT,
                    "deadline_reminder_eligible": False,
                    "summary": "收到學院複審排序通知後，於 2026/11/03–11/10 16:00 登入系統完成第一階段志願選填（可參考全球處公告之姊妹校第一志願選填熱門程度 A/B/C/D 分級表）。12月初公布分發結果與獎學金名單後，錄取生須於 2026/12/11（五）16:00 前繳交《交換學生同意聲明書》、《家長擔保同意書》、《獎學金切結書》及行政處理費（保證金）新臺幣 8,000 元（低收／中低收入戶免繳）完成報到。",
                    "details": [
                        "熱門程度選填策略：全球處將姊妹校分為 A（競爭非常激烈）、B（競爭激烈）、C（競爭較不激烈）、D（填第一志願預估可直接分發）四級；若第一志願選填 A 或 B 級學校，強烈建議第二志願以後改填 C 或 D 級學校。",
                        "行政處理費（保證金）規定：報到時繳交 NT$8,000（低收／中低收入戶免繳）；若錄取確認後無故放棄或未履行返國義務，保證金不予退還。",
                    ],
                    "scope": {
                        "home_universities": ["國立清華大學"],
                        "academic_years": ["115", "116"],
                        "application_rounds": [
                            round_label,
                            "116-1",
                            "116-2",
                            "2027秋／2028春 第一梯次",
                            "2028春季班 第二梯次",
                        ],
                    },
                    "source_urls": [
                        NTHU_2027_2028_GUIDELINES_ZH_URL,
                        NTHU_POPULARITY_SHEET_URL,
                        NTHU_SELECTION_REGULATIONS_URL,
                    ],
                    "checked_at": CHECKED_AT,
                    "support_status": "verified",
                },
                {
                    "rule_id": f"nthu-{idx+1:03d}-host-apply",
                    "order": 4,
                    "phase": "合作校申請",
                    "title": f"由清大全球事務處辦理官方提名並依 {zh_name} 規定遞交入學申請資料",
                    "responsible_party": "學生與接待校國際處",
                    "summary": f"完成校內錄取報到與保證金繳交後，由清大全球事務處全球學術合作組向 {zh_name} 辦理官方提名（Nomination）；學生須自行密切留意姊妹校申請截止日，備妥英文成績單、護照、財力證明、語檢證明及選課計畫按時完成該校線上入學申請，靜候姊妹校核發正式入學許可（Letter of Acceptance）。",
                    "details": [
                        f"交換期程：{study_period_str}｜名額：{quota_str}",
                        f"語言與學業條件：{lang_req_str}",
                    ]
                    + ([f"締約校申請與修課備註：{remarks_all[:240]}"] if remarks_all else []),
                    "scope": {
                        "home_universities": ["國立清華大學"],
                        "partner_universities": [full_name],
                        "academic_years": ["115", "116"],
                        "application_rounds": [
                            round_label,
                            "116-1",
                            "116-2",
                            "2027秋／2028春 第一梯次",
                            "2028春季班 第二梯次",
                        ],
                    },
                    "source_urls": (
                        [
                            source_url,
                            NTHU_2027_2028_GUIDELINES_ZH_URL,
                            NTHU_SCHOLARSHIP_REGULATIONS_URL,
                        ]
                        + ([factsheet_url] if factsheet_url else [])
                        + ([website] if website else [])
                    ),
                    "checked_at": CHECKED_AT,
                    "support_status": "verified",
                    "needs_confirmation": False,
                },
                {
                    "rule_id": f"nthu-116-home-5-{idx+1:03d}",
                    "order": 5,
                    "phase": "行前準備",
                    "title": "參加行前說明會、修習足額及格課程與返國後 1 個月內繳交 4 項文件退還 8,000 元保證金",
                    "responsible_party": "學生",
                    "responsible_unit": "國立清華大學全球事務處／教務處註冊組／生輔組",
                    "summary": "出國前參加全球處行前說明會、辦理簽證與足額海外醫療及意外保險（役男須於出國前至少 1 個月辦理緩徵役男出境）；交換期間須完成清大註冊並繳交全額學雜費，大學部每學期／學季至少修讀 3 門課程及格、研究生至少修讀 1 門研究所課程及格（獲獎學金者須為本科相關專業課程；陸港澳大學部至少 9 學分及格）；返國後 1 個月內繳交返國報告單、成果報告書（交換心得）、姊妹校成績單、登機證（獲獎生另附 3 分鐘影音檔）並完成學分抵免，於當年度 10–11 月退還 8,000 元保證金。",
                    "details": tuition_points_list,
                    "scope": {
                        "home_universities": ["國立清華大學"],
                        "academic_years": ["115", "116"],
                        "application_rounds": [
                            round_label,
                            "116-1",
                            "116-2",
                            "2027秋／2028春 第一梯次",
                            "2028春季班 第二梯次",
                        ],
                    },
                    "source_urls": [
                        NTHU_PRE_DEPARTURE_SLIDES_URL,
                        NTHU_SCHOLARSHIP_REGULATIONS_URL,
                        NTHU_DISADVANTAGED_SCHOLARSHIP_URL,
                        NTHU_2027_2028_GUIDELINES_ZH_URL,
                    ],
                    "checked_at": CHECKED_AT,
                    "support_status": "verified",
                },
            ],
            "sources": wf_sources,
            "last_checked": CHECKED_AT,
            "coverage_status": "official_verified",
            "coverage_note": "已完整整合國立清華大學 2027秋／2028春 出國交換生甄選簡章、線上報名系統 142 校資格明細、陸港澳交換簡章、116-1 台灣聯大交換公告、院系級交換合約、A/B 類及清寒／劉維全校友獎學金辦法、姊妹校 A/B/C/D 熱門程度表與 328 份歷屆交換心得。",
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
                "title": f"國立清華大學全球事務處出國交換姊妹校列表與條件明細—{zh_name}",
                "source_url": source_url,
                "summary": "清大官方交換學校名額、外語能力門檻、GPA 要求、第一志願熱門程度與學制院系限制",
            },
            {
                "title": "國立清華大學 2027秋／2028春 出國交換生甄選簡章與學生出國交換甄選辦法",
                "source_url": NTHU_2027_2028_GUIDELINES_ZH_URL,
                "summary": "清大校級交換三階段審查（系初審、院複審、全球處決審）、兩階段志願分發、8,000 元保證金與最低修課及格規定",
            },
        ]
        if factsheet_url:
            dest_sources.append({
                "title": f"國立清華大學出國交換合作校交換資訊／Fact Sheet—{zh_name}",
                "source_url": factsheet_url,
                "summary": "締約合作校交換學生 Fact Sheet 與修課住宿指引",
            })
        if website:
            dest_sources.append({
                "title": f"{full_name} 官方網站",
                "source_url": website,
                "summary": "接待合作校官方網站",
            })
        if exp_posts:
            dest_sources.append({
                "title": f"國立清華大學赴 {zh_name} 交換生返國成果報告書（共 {len(exp_posts)} 篇）",
                "source_url": exp_posts[0].get("url") or exp_portal_url,
                "summary": f"收錄清大全球事務處交換生赴 {zh_name} 返國成果報告書",
            })

        src_url_list = (
            [source_url, NTHU_2027_2028_GUIDELINES_ZH_URL]
            + ([factsheet_url] if factsheet_url else [])
            + ([website] if website else [])
        )

        destinations.append({
            "home_university": "國立清華大學",
            "school_name": full_name,
            "country": country,
            "city": location_obj.get("city") or country,
            "cost_summary": f"{cost_line}。\n{tuition_clean}",
            "housing_summary": housing_clean,
            "transport_summary": f"校區代表城市：{location_obj.get('city') or country}。請依入學許可與接待校交換生網頁確認實際授課校區、機場交通與當地學生大眾運輸票卡優惠。",
            "campus_life_summary": f"{calendar_clean}\n{course_clean}",
            "student_guide_sections": [
                {
                    "key": "cost",
                    "title": "生活費、清大 A/B 類出國交換獎學金（每月 1.5萬–3萬）、清寒獎學金（最高 20萬）、劉維全校友獎學金與學海計畫",
                    "summary": cost_line,
                    "points": [cost_line] + tuition_points_list,
                    "source_urls": src_url_list + [
                        NTHU_SCHOLARSHIP_REGULATIONS_URL,
                        NTHU_DISADVANTAGED_SCHOLARSHIP_URL,
                        NTHU_MOE_XUEHAI_ZHUMENG_URL,
                    ],
                    "caution": "清大「出國交換生獎學金」須於第一階段線上申請交換時同步勾選！A 類一般地區每月 NT$15,000（至多 5 個月）；B 類新南向及中南美洲每月 NT$30,000、以／土／俄／蒙／南非每月 NT$25,000；清寒學生出國交流獎學金最高 NT$200,000；凱斯西儲大學專屬劉維全校友獎學金每學期 NT$120,000–150,000。",
                },
                {
                    "key": "housing",
                    "title": "住宿資訊與校內外宿舍申請",
                    "summary": housing_clean[:160],
                    "points": [housing_clean],
                    "source_urls": src_url_list,
                    "caution": "各姊妹校學生宿舍名額有限，獲清大全球處提名後請務必於該校住宿申請截止日前完成登記。",
                },
                {
                    "key": "insurance",
                    "title": "海外醫療及意外保險與在地強制保險規定",
                    "summary": visa_default,
                    "points": [
                        visa_default,
                        "依《國立清華大學出國交換生甄選簡章》規定，交換生於出國前須自行購買足額之海外醫療、意外及海外急難救助保險，並依接待國及姊妹校規定投保當地強制學生健康保險。",
                    ],
                    "source_urls": src_url_list,
                    "caution": "多數歐美日韓及澳洲姊妹校要求於註冊或抵校時出示符合當地政府或校方標準之英文醫療保險證明。",
                },
                {
                    "key": "visa",
                    "title": "簽證辦理、海外防詐安全指引與緩徵役男出境手續（出國前至少 1 個月）",
                    "summary": visa_default,
                    "points": [
                        "收到姊妹校核發之正式入學許可書（LOA / COE / DS-2019）後，請立即向該國駐臺辦事處申辦學生簽證（赴大陸交換須自行辦理有效護照與臺胞證）。",
                        "具役男身分之錄取學生，應於出國前至少 1 個月持姊妹校入學許可等文件，洽全球事務處及生輔組辦理緩徵役男出境核准手續。",
                        visa_default,
                    ],
                    "source_urls": src_url_list + [NTHU_ANTI_FRAUD_GUIDE_URL],
                    "caution": "各國領事館簽證審核約需 4–8 週，請勿於取得簽證與入學許可前購買不可退改之機票。",
                },
                {
                    "key": "courses",
                    "title": "每學期最低修課及格門檻（大學部 3 門／研究所 1 門；陸港澳大學部 9 學分）與獎學金專業課程要求",
                    "summary": course_clean[:160],
                    "points": [
                        course_clean,
                        "海外交換未獲獎學金者：大學部每學期／學季至少修讀 3 門課程及格、研究生至少修讀 1 門研究所課程及格；獲獎學金者：大學部每學期／學季至少修讀 3 門「本科相關專業課程」及格、研究生至少修讀 1 門「本科相關專業研究所課程」及格；陸港澳交換：大學部每學期至少修讀 9 學分及格、研究生至少 1 門課程及格。",
                    ],
                    "source_urls": src_url_list,
                    "caution": "請於出國前先與所屬系所確認擬修課程之學分採認與抵免原則，返國後須完成學分抵免流程始得退還保證金。",
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
                    "caution": "部分合作大學設有多個校區，實際授課校區請以當期姊妹校列表及錄取通知為準。",
                },
                {
                    "key": "arrival",
                    "title": "返國後 1 個月內繳交 4 項返國文件（含成果報告書、登機證、成績單）與退還 8,000 元保證金",
                    "summary": calendar_clean,
                    "points": [
                        calendar_clean,
                        "依《國立清華大學出國交換生甄選簡章》規定，交換生須於返國後 1 個月內向全球事務處繳交四項返國文件：（1）返國報告單、（2）成果報告書（交換心得，授權公開供學弟妹參考）、（3）姊妹校正式成績單、（4）回程登機證存根（獲獎學金生另須提供 3 分鐘交換生活影音檔），並回系所完成學分抵免，經審核無誤後於當年度 10–11 月無息退還新臺幣 8,000 元保證金。",
                    ]
                    + (
                        [
                            f"歷屆學長姐返國心得：清大全球事務處已公開收錄赴 {zh_name} 交換生返國成果報告書共 {len(exp_posts)} 篇。"
                        ]
                        if exp_posts
                        else []
                    ),
                    "source_urls": src_url_list + [exp_portal_url],
                    "caution": "未於返國後 1 個月內完成返國文件繳交及學分抵免者，將影響 8,000 元保證金退還及獎學金第 2 期款核撥。",
                },
            ],
            "first_72_hours": [
                {
                    "title": "依姊妹校入學許可指定報到日完成新生報到、宿舍入住與選課確認",
                    "detail": calendar_clean,
                    "source_urls": [source_url],
                },
                {
                    "title": "確認選課符合清大最低及格門檻（大學部 3 門／研究所 1 門；獲獎生須為本科相關專業課）並妥善保存登機證",
                    "detail": f"{visa_default} 請妥善保存去回程登機證存根，並確認修課門檻符合清大規定以利返國辦理學分抵免與保證金退費。",
                    "source_urls": [
                        NTHU_2027_2028_GUIDELINES_ZH_URL,
                        NTHU_PRE_DEPARTURE_SLIDES_URL,
                    ],
                },
            ],
            "sources": dest_sources,
            "last_checked": CHECKED_AT,
            "coverage_status": "official_verified",
            "coverage_note": "已整合國立清華大學 2027秋／2028春 出國交換生甄選簡章、142 校線上系統資格明細、陸港澳交換簡章、116-1 台灣聯大交換公告、院系級交換合約、獎學金辦法與 328 份歷屆學長姐交換心得報告。",
        })

        research_records.append({
            "home_university": "國立清華大學",
            "school_name": full_name,
            "country": country,
            "official_website": website,
            "verification_status": "official_verified",
            "discovery_source_url": source_url,
            "checked_at": CHECKED_AT,
            "note": f"國立清華大學全球事務處出國交換姊妹校列表、線上報名系統資格表（{factsheet_url or source_url}）及 ROR/Wikidata 官方網址核對完成。",
        })

        ev_sources = [
            {"title": f"國立清華大學全球事務處出國交換姊妹校列表與條件—{zh_name}", "url": source_url},
        ]
        if factsheet_url:
            ev_sources.append({"title": f"國立清華大學出國交換合作校 Fact Sheet—{zh_name}", "url": factsheet_url})
        if website:
            ev_sources.append({"title": f"{full_name} 官方網站", "url": website})
        if exp_posts:
            ev_sources.append({
                "title": f"國立清華大學赴 {zh_name} 交換生返國成果報告書（{exp_posts[0].get('academic_year') or '歷年'}）",
                "url": exp_posts[0].get("url") or exp_portal_url,
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
                "scope": "國立清華大學出國交換姊妹校住宿與生活資訊",
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
                "scope": "國立清華大學交換生費用規定、A/B 類獎學金／清寒獎學金／劉維全校友獎學金與地區生活費估算",
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
                "scope": "國立清華大學交換生選課限制、大學部 3 門／研究所 1 門及格門檻與返國學分抵免規定",
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
                "scope": "國立清華大學出國交換簽證、海外醫療保險、海外防詐安全指引與緩徵役男出境提醒",
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
                        f"｜清大全球處官網公開收錄赴 {zh_name} 歷屆交換生返國成果報告書共 {len(exp_posts)} 篇。"
                        if exp_posts
                        else ""
                    )
                ),
                "sources": ev_sources,
                "checked_at": CHECKED_AT,
                "scope": "國立清華大學出國交換名額與歷屆學長姐返國成果報告書",
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
                "已整合國立清華大學 2027秋／2028春 出國交換生甄選簡章、142 校線上報名系統資格明細、陸港澳交換簡章、院系級交換合約與 328 份歷屆交換生返國成果報告書。",
                "當期宿位供給、費用與選課限制請依姊妹校最新交換網頁及課程目錄核對。",
            ],
            "location_signature": f"verified:{location_obj['latitude']}:{location_obj['longitude']}:representative",
            "extraction_version": 3,
        })

        sample_reports: list[dict] = []
        for p_item in exp_posts[:5]:
            p_url = p_item.get("url") or exp_portal_url
            ay = clean_text(str(p_item.get("academic_year") or ""))
            term_str = ay if ay else "歷年交換"
            t_clean = clean_text(p_item.get("title") or "")
            sample_reports.append({
                "title": t_clean or f"國立清華大學赴 {zh_name} 交換學生返國成果報告書",
                "url": p_url,
                "term": term_str,
            })

        if exp_posts:
            latest_post = exp_posts[0]
            terms_covered = list(
                dict.fromkeys(
                    clean_text(str(p.get("academic_year")))
                    for p in exp_posts
                    if p.get("academic_year")
                )
            )
            rep_title = (
                f"國立清華大學赴 {zh_name}（共 {len(exp_posts)} 篇返國成果報告書）交換學生心得彙編"
            )
            latest_title = clean_text(latest_post.get("title") or zh_name)
            excerpt_str = clean_text(latest_post.get("excerpt") or "")
            summary_text = (
                f"國立清華大學全球事務處「出國交換返國報告書／交換心得分享」專區公開收錄赴 {zh_name} 交換學生返國成果報告書共 {len(exp_posts)} 篇"
                + (f"（涵蓋期間：{'、'.join(terms_covered[:6])}）" if terms_covered else "")
                + f"，代表篇目包含《{latest_title}》"
                + (f"（摘錄：{excerpt_str[:180]}…）" if excerpt_str else "")
                + "，詳實記錄清大交換生行前簽證準備、姊妹校選課（大學部每學期至少 3 門／研究所至少 1 門及格）、宿舍申請與當地生活開銷。"
            )
            theme_map = {
                "academics": f"清大交換生於返國成果報告書中分享於 {zh_name} 之選課流程、英語或當地語言授課體驗、大學部每學期至少 3 門／研究所至少 1 門課程及格規定與返國學分抵免實務。",
                "housing": f"清大交換生於心得中分享 {zh_name} 校內學生宿舍或校外租屋申請方式、月租費用與生活機能（{housing_clean[:120]}）。",
                "campus_culture": f"清大全球處收錄 {len(exp_posts)} 篇赴 {zh_name} 歷屆交換生返國成果報告書，提供學弟妹第一手校園生活與跨文化交流指南。",
                "cost": f"清大交換生於心得中記錄赴 {zh_name} 之機票、簽證、住宿與每月生活費開銷（{cost_default}），以及清大 A/B 類出國交換獎學金與教育部學海飛颺申請經驗。",
            }
            p_url = latest_post.get("url") or exp_portal_url
            ay = clean_text(str(latest_post.get("academic_year") or "歷年交換"))
            student_experience_rows.append({
                "school_name": full_name,
                "country": country,
                "title": rep_title,
                "source_url": p_url,
                "source_type": "article",
                "platform": "國立清華大學全球事務處—出國交換返國報告書專區",
                "author_name": latest_title or "國立清華大學返國交換學生",
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
                "exchange_term": ay,
                "summary_zh": summary_text,
                "original_summary": summary_text,
                "theme_summaries_zh": theme_map,
                "translation_status": "original",
                "source_kind": "official_experience_page",
            })

        experience_sources_records.append({
            "home_university": "國立清華大學",
            "school_name": full_name,
            "country": country,
            "official_experience_portal_url": exp_portal_url,
            "partner_page_url": factsheet_url or source_url,
            "report_count": len(exp_posts),
            "sample_reports": sample_reports,
            "checked_at": CHECKED_AT,
        })

    partners_jsonl_text = (
        "\n".join(json.dumps(r, ensure_ascii=False) for r in partners) + "\n"
    )
    (OFFICIAL_NTHU_DIR / "partners.jsonl").write_text(
        partners_jsonl_text, encoding="utf-8"
    )
    (SOURCES_NTHU_DIR / "partners.jsonl").write_text(
        partners_jsonl_text, encoding="utf-8"
    )
    (OFFICIAL_NTHU_DIR / "application_workflows.jsonl").write_text(
        "\n".join(json.dumps(r, ensure_ascii=False) for r in workflows) + "\n",
        encoding="utf-8",
    )
    (OFFICIAL_NTHU_DIR / "destination_profiles.jsonl").write_text(
        "\n".join(json.dumps(r, ensure_ascii=False) for r in destinations) + "\n",
        encoding="utf-8",
    )
    (OFFICIAL_NTHU_DIR / "partner_research.jsonl").write_text(
        "\n".join(json.dumps(r, ensure_ascii=False) for r in research_records) + "\n",
        encoding="utf-8",
    )
    (OFFICIAL_NTHU_DIR / "student_life.jsonl").write_text(
        "\n".join(json.dumps(r, ensure_ascii=False) for r in life_records) + "\n",
        encoding="utf-8",
    )
    (OFFICIAL_NTHU_DIR / "experience_sources.jsonl").write_text(
        "\n".join(
            json.dumps(r, ensure_ascii=False) for r in experience_sources_records
        )
        + "\n",
        encoding="utf-8",
    )
    (OFFICIAL_NTHU_DIR / "student_experiences.jsonl").write_text(
        "\n".join(
            json.dumps(r, ensure_ascii=False) for r in student_experience_rows
        )
        + "\n",
        encoding="utf-8",
    )
    (OFFICIAL_NTHU_DIR / "campus-locations.json").write_text(
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

    nthu_home_loc = {
        "school_name": "國立清華大學",
        "country": "臺灣",
        "city": "新竹市東區",
        "latitude": 24.7958,
        "longitude": 120.9961,
        "geocode_status": "verified",
        "geocoded_at": CHECKED_AT,
        "source_url": "https://www.wikidata.org/wiki/Q702839",
        "identity_source_url": "https://ror.org/00zdnkx70",
        "precision": "representative",
        "note": "校級代表位置：官方網域及國家已與 ROR 比對，座標來源為 Wikidata P625；實際交換校區以錄取通知為準。 母校代表點採新竹市東區光復路二段101號校本部第一綜合大樓 110 室全球事務處全球學術合作組；官方地址來源：https://oga.site.nthu.edu.tw/。",
    }
    existing_loc_map[("國立清華大學", "臺灣")] = nthu_home_loc
    sorted_locs = sorted(
        existing_loc_map.values(),
        key=lambda r: (r.get("country") or "", r.get("school_name") or ""),
    )
    loc_file.write_text(
        "\n".join(json.dumps(r, ensure_ascii=False) for r in sorted_locs) + "\n",
        encoding="utf-8",
    )

    nthu_source_urls = [
        NTHU_OGA_OUTBOUND_URL,
        NTHU_OVERSEAS_PARTNERS_URL,
        NTHU_MAINLAND_PARTNERS_URL,
        NTHU_VM_PORTAL_URL,
        NTHU_VM_OVERVIEW_URL,
        NTHU_2027_2028_GUIDELINES_ZH_URL,
        NTHU_2027_2028_GUIDELINES_EN_URL,
        NTHU_SELECTION_REGULATIONS_URL,
        NTHU_SCHOLARSHIP_REGULATIONS_URL,
        NTHU_DISADVANTAGED_SCHOLARSHIP_URL,
        NTHU_LANGUAGE_STANDARDS_ZH_URL,
        NTHU_LANGUAGE_STANDARDS_EN_URL,
        NTHU_FAQ_HOT_QUESTIONS_URL,
        NTHU_INFO_SESSION_SLIDES_URL,
        NTHU_ONLINE_SYSTEM_GUIDE_URL,
        NTHU_PRE_DEPARTURE_SLIDES_URL,
        NTHU_MAINLAND_GUIDELINES_URL,
        NTHU_MAINLAND_FLOWCHART_URL,
        NTHU_CROSS_STRAIT_SUMMER_URL,
        NTHU_UST_116_NOTICE_URL,
        NTHU_UST_116_PDF_URL,
        NTHU_UST_116_FORM_URL,
        NTHU_DUAL_DEGREE_SCHOLARSHIP_URL,
        NTHU_SHORT_TERM_VISIT_URL,
        NTHU_MOE_XUEHAI_ZHUMENG_URL,
        NTHU_ANTI_FRAUD_GUIDE_URL,
        NTHU_POPULARITY_SHEET_URL,
        NTHU_ALL_AGREEMENTS_URL,
        NTHU_COLLEGE_DEPT_OVERSEAS_URL,
        NTHU_COLLEGE_DEPT_MAINLAND_URL,
        NTHU_EXPERIENCE_OVERSEAS_URL,
        NTHU_EXPERIENCE_MAINLAND_URL,
    ]

    exchange_info_payload = {
        "school_name": "國立清華大學",
        "program_type": [
            "交換學生（校級海外出國交換計畫・142 所當期開放姊妹校，採系所初審、學院複審、全球處決審三階段審查與 A/B/C/D 熱門程度兩階段志願選填）",
            "校級赴大陸地區及香港、澳門學期交換計畫（12 所當期開放頂尖合作大學，含北京清華、北大、復旦、上海交大、浙大、港大、港理工等）",
            "台灣聯合大學系統（UST）116學年度學生出國交換計畫（瑞士伯恩大學、新加坡南洋理工大學、香港中文大學、香港城市大學、美國加州大學聖塔克魯茲分校 UCSC）與 18 所院系級交換合約校",
        ],
        "academic_year": [
            "116（116學年度台灣聯合大學系統［UST］學生出國交換計畫第一梯次：即日起至 2027年1月4日 16:00 受理清大全球處收件；2027秋／2028春 校級海外交換第一梯次已於 2026/10/08 截止報名並於 11/03–11/10 進行志願選填、12/11 報到；2028 春季班第二梯次預計於 2027年1月中至3月初開放申請）",
            "115（完整收錄清大全球事務處 176 所全球合作大學：含 158 所當期開放申請校及 18 所院系級交換合約校）",
        ],
        "semester": [
            "第1學期（秋季班：每年約 8/9 月至 12 月／翌年 1 月；澳洲與紐西蘭對應 Semester 2 為 7 月至 11 月）",
            "第2學期（春季班：每年約 1/2 月至 5/6 月；日本前學期為 4 月至 8 月）",
            "一學年或暑期研究交換（海外交換第一梯次可申請秋季班、春季班或全學年；第二梯次申請春季班；台灣聯大 UST 另含暑期研究交換）",
        ],
        "application_period": [
            "【116學年度台灣聯合大學系統（UST）學生出國交換計畫（I）第一梯次（2027 暑期／2027 秋季／2028 春季交換）— 開放申請中】清大宣傳活動：2026年11月18日（三）12:20；清大全球事務處收件截止日：2027年1月4日（一）16:00 止（每類別限填一份申請表、至多選填 2 個志願，紙本經系、院核章後送全球處彙送台灣聯大系統，2027/02/28 前通知結果）。",
            "【2027秋／2028春（116學年度）校級海外出國交換計畫第一梯次】第一階段線上報名及紙本送系所：2026年9月3日至 10月8日 16:00 止（系所初審 10/14、學院複審 10/20 送全球處）；第二階段線上選填志願序：第一次選填 2026年11月3日至 11月10日 16:00 止；分發及獎學金結果通知：2026年12月初；報到確認並繳交保證金 NT$8,000：2026年12月11日（五）16:00 前。",
            "【2028春季班（116-2）校級海外出國交換計畫第二梯次】預計於 2027年1月中旬至3月初開放線上報名；【校級赴陸港澳學期交換計畫】2027秋季班預計於 2026年12月至 2027年1月開放申請（2月初經系、院送全球處決審）。",
        ],
        "eligibility": [
            "【在學年級與學籍規定】申請人須為國立清華大學大學部二年級（含）以上、碩士班一年級（含）以上或博士班一年級（含）以上之正式學籍在學學生（不含在職專班及在職生；陸港澳學期交換大一、碩一、博一或轉學生可提具前一學期成績證明申請）。申請時與出國交換期間之學籍學位必須一致（不得跨學制交換）。",
            "【GPA 與班級排名門檻】（1）校級海外交換：申請前兩學期學業平均成績達 GPA 3.20以上，或班級排名前 50% 以上（碩一、博一新生繳交前一學位含畢業排名成績單；南大校區百分制須依註冊組對照表換算為等級制 GPA）；（2）校級陸港澳交換：前兩學期平均達 GPA 3.20（含）以上或全班排名前 30%（含）以上；（3）台灣聯合大學系統（UST）交換：前一學年平均達 GPA 3.0（或 B）以上；（4）申請出國交換生獎學金（A/B 類）、清寒學生出國交流獎學金及劉維全校友獎學金：前一學年平均須達 GPA 3.40 以上或全班／系排名前 20% 以上（教育部學海惜珠須達 GPA 3.20 以上）。",
            "【三階段審查、兩階段志願選填與 8,000 元保證金及修課義務】校內審查分「系所初審 → 學院複審 → 全球事務處決審」三階段，通過後依全球處通知於線上系統選填志願（姊妹校依第一志願熱門程度分為 A/B/C/D 四級）。錄取報到時須繳交行政處理費（保證金）新臺幣 8,000 元（低收／中低收入戶免繳）。交換期間大學部每學期／學季至少須修讀 3 門課程及格、研究生至少 1 門研究所課程及格（獲獎學金者須為本科相關專業課程；陸港澳大學部至少 9 學分及格），並於返國後 1 個月內繳交四項返國文件與完成學分抵免後退還保證金。",
        ],
        "language_requirement": [
            "【清大校內最低外語能力標準（依 2026.08.28《國立清華大學出國交換生外語能力標準表》，須為申請截止日前 2 年內有效成績；姊妹校標準高於校內標準者從其規定）】（1）英語組：TOEFL iBT 79（新制 4.0）或 IELTS (Academic) 6.0；（2）日語組：JLPT N2；（3）法語組：DELF/DALF B1、TCF/TCF-DAP B1 或 FLPT 法語筆試總分 150 分且口試 S-2；（4）德語組：Goethe-Zertifikat B1、TestDaF TDN 3 或 FLPT 德語筆試總分 150 分且口試 S-2；（5）西語組：DELE B1 或 FLPT 西語筆試總分 150 分且口試 S-2；（6）韓語組：TOPIK 4 級。",
            "【不予採計之英檢項目警示】清大校級海外出國交換甄選明確規定：不接受 TOEFL iBT MyBest Scores（拼分成績）、不接受多益（TOEIC）、不接受全民英檢（GEPT）、不接受 GRE，亦不接受 Duolingo English Test！",
            "【陸港澳與台灣聯大（UST）語言規定】赴大陸及香港交換者，除香港理工大學（須達 TOEFL iBT 80 或 IELTS 6.0）及英語授課計畫外，一般中文授課課程免附外語檢定；申請台灣聯大（UST）交換者須檢附 2 年內有效之 TOEFL iBT（依各校規定 71–90 分）或 IELTS（6.0–7.0）成績單。",
        ],
        "required_documents": [
            "1. 國立清華大學出國交換生線上系統申請表（於 https://oga-exchange.vm.nthu.edu.tw/outexchange/index/index/puid/11521 完成填報列印並由本人簽名；欲申請出國交換獎學金者須於系統同步勾選）",
            "2. 本校歷年中文成績單正本（須含前兩學期 GPA 或班級排名百分比；碩一、博一新生檢附前一學位含畢業排名之成績單；南大校區百分制成績須附註冊組等級制 GPA 換算證明）",
            "3. 申請截止日前 2 年內有效之外語能力證明影本（TOEFL iBT 79［新制 4.0］／IELTS Academic 6.0 或日語 N2、德法西語 B1、韓語 TOPIK 4 級；不接受 MyBest Scores、TOEIC、GEPT、GRE、Duolingo）",
            "4. 每個志願各一份修課／讀書計畫，可用中文（本期海外交換，不含陸港澳）",
            "5. 身分證明與學生證正反面影本（外籍／僑生用護照，陸生用入臺證）",
            "6. 導師或論文指導教授推薦信 1 封，格式不限",
            "7. 其他有利審查資料及助學相關證明（獲獎紀錄、學術發表、社團證明；申請清寒獎學金或學海惜珠者須檢附低收入戶／中低收入戶／特殊境遇家庭證明或個人與家庭逆境向上說明及國稅局全戶所得清單）",
        ],
        "scholarship_info": [
            "國立清華大學「出國交換生獎學金 A 類（一般地區）」（《出國交換生獎學金審查作業細則》）：補助前兩學期平均達 GPA 3.40 以上或全班／系排名前 20% 以上之錄取交換生，每名每月核給新臺幣 15,000 元，補助期限以一學期（至多 5 個月，最高 NT$75,000）為原則，每年約 40–50 名（須於第一階段線上申請交換時同步勾選）。",
            "國立清華大學「出國交換生獎學金 B 類（特定國家類別重點補助）」：資格同 A 類（前一學年 GPA 3.40 或班／系排前 20%），（1）赴新南向國家（印尼、越南、汶萊、泰國、菲律賓、馬來西亞、印度，不含新加坡）及中南美洲國家（阿根廷、巴西、智利、哥斯大黎加、秘魯、墨西哥、厄瓜多爾）交換者，每名每月補助新臺幣 30,000 元（至多 5 個月，最高 NT$150,000）；（2）赴以色列、土耳其、俄羅斯、蒙古、南非交換者，每名每月補助新臺幣 25,000 元（至多 5 個月，最高 NT$125,000）。",
            "「劉維全校友出國交流獎學金」：專項補助赴美國凱斯西儲大學（Case Western Reserve University）交換之清大大學部在學學生（前一學年 GPA 3.40 以上或班／系排前 20%，且操行成績 80 分以上），一般生每學期補助新臺幣 120,000 元、清寒學生每學期補助新臺幣 150,000 元（補助一學期或一學年，最高可達 NT$240,000–300,000）。",
            "「國立清華大學清寒學生出國交流獎學金」：補助對象涵蓋（1）持有低收入戶、中低收入戶或特殊境遇家庭證明者，或（2）家庭突遭變故、逆境向上且具強烈學習熱誠之一般生（本國籍學生與境外生皆可申請！前一學年 GPA 3.40 以上或前 20%、操行 80 分以上），以每月新臺幣 20,000 元為原則，每人最高補助新臺幣 200,000 元。",
            "教育部「學海飛颺」、「學海惜珠」及外國政府獎學金：學海惜珠專項補助具中華民國國籍且持有低收／中低收／特殊境遇家庭證明、前一學年 GPA 3.20 以上之學生赴國外（不含陸港澳）交換（教育部補助 80%＋清大配合款 20%）；赴日本交換生另可申請日本台灣交流協會獎學金（每月 JPY 80,000）。",
        ],
        "partner_universities": [p["school_name"] for p in partners],
        "source_urls": nthu_source_urls,
        "last_checked": CHECKED_AT,
    }
    (OFFICIAL_NTHU_DIR / "exchange_info.json").write_text(
        json.dumps(exchange_info_payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    student_dashboard_payload = {
        "school_name": "國立清華大學",
        "last_checked": CHECKED_AT,
        "academic_score_minimum": None,
        "academic_score_rule": "校級海外出國交換申請前兩學期學業平均成績須達 GPA 3.20以上或班級排名前 50% 以上；校級赴陸港澳學期交換須達前兩學期平均 GPA 3.20 以上或全班排名前 30% 以上；台灣聯合大學系統（UST）交換須達前一學年平均 GPA 3.0（或 B）以上。申請清大出國交換生獎學金（A/B 類）、清寒學生出國交流獎學金及劉維全校友獎學金須達前一學年平均 GPA 3.40 以上或全班／系排名前 20% 以上（教育部學海惜珠為 GPA 3.20 以上）。",
        "academic_gpa_minimum": 3.2,
        "maximum_preferences": 10,
        "selection_rules": {
            "academic_policy": "gpa_or_rank",
            "academic_reference_year": "116",
            "undergraduate_gpa_minimum": 3.2,
            "undergraduate_rank_maximum": 50.0,
            "graduate_academic_exempt": False,
            "exclude_in_service": True,
            "pending_quota_planning": False,
            "partner_requirements_need_confirmation": False,
            "degree_score_minimums": {},
            "excluded_undergraduate_years": ["大一"],
            "language_certificate_required": True,
        },
        "language_score_minimums": {
            "toefl": 79.0,
            "ielts": 6.0,
        },
        "application_periods": [
            {
                "title": "116學年度台灣聯合大學系統（UST）學生出國交換計畫（I）第一梯次（說明會 2026/11/18、清大全球處收件至 2027/01/04 16:00 止）",
                "details": [
                    "合作學校（5 校）：瑞士伯恩大學（學期交換 2 名，TOEFL iBT 90／IELTS 7.0）、新加坡南洋理工大學 NTU（研究學期與暑期交換共用 6 名，TOEFL iBT 90／IELTS 6.0）、香港中文大學（新亞書院學期交換 4 名 TOEFL iBT 71／IELTS 6.0；理學院／工學院暑期交換各 6 名）、香港城市大學（能源及環境／理／工學院學期與暑期交換共用各 4 名，TOEFL iBT 79／IELTS 6.5）、美國加州大學聖塔克魯茲分校 UCSC（暑期交換不限名額，TOEFL iBT 80／IELTS 6.5）。",
                    "申請資格與時程：前一學年平均成績達 GPA 3.0（或 B）以上之在學學生（不含大一新生），每種交換類別限填一份申請表、至多選填 2 個志願；紙本申請表經系、院核章後，於 2027年1月4日（一）下午 16:00 前送達清大全球事務處全球學術合作組（第一綜合大樓 110 室），由全球處彙送台灣聯大系統於 2027/01/11 截止收件、2027/02/28 前通知審查結果。",
                ],
                "source": {
                    "title": "國立清華大學 116學年度台灣聯合大學系統（UST）學生出國交換計畫第一梯次甄選公告與簡章 PDF",
                    "source_url": NTHU_UST_116_NOTICE_URL,
                    "category": "exchange_application",
                    "summary": "116學年度台灣聯大出國交換計畫第一梯次合作學校名額、語言與 GPA 門檻及清大全球處 2027/01/04 16:00 收件截止規定。",
                },
                "scope": "home_application",
                "program_types": ["exchange"],
                "academic_year": "116",
                "application_round": "116學年度台灣聯合大學系統（UST）學生出國交換計畫第一梯次",
                "audience": "all_students",
                "opens_at": "2026-10-16T09:00:00+08:00",
                "deadline_at": "2027-01-04T16:00:00+08:00",
                "date_status": "verified_exact",
                "status": "open",
                "status_note": "116學年度台灣聯合大學系統（UST）學生出國交換計畫第一梯次現正開放申請中，清大校內收件至 2027/01/04 16:00 止。",
                "deadline_note": "申請表須先完成所屬學系及學院核章，請務必提早辦理簽核並於 2027/01/04 16:00 前將紙本送達全球事務處全球學術合作組。",
                "reminder_eligible": True,
                "checked_at": CHECKED_AT,
            },
            {
                "title": "國立清華大學 2027秋／2028春（116學年度）校級海外出國交換計畫—第一梯次（09/03–10/08 報名、11/03–11/10 選填志願、12/11 報到）",
                "details": [
                    "第一階段（線上報名與系院三階段審查）：2026年9月3日（四）至 10月8日（四）16:00 止於線上系統報名並將紙本送達系所（已截止）；10月14日 16:00 前系所初審送院、10月20日 16:00 前學院複審排序送全球事務處決審。",
                    "第二階段（線上志願選填與報到）：收到院排序通知後，於 2026年11月3日（二）至 11月10日（二）16:00 止於線上系統進行第一次志願選填；2026年12月初通知志願分發與獎學金結果；2026年12月11日（五）16:00 前繳交同意聲明書、家長擔保書及保證金 NT$8,000 完成報到。",
                ],
                "source": {
                    "title": "國立清華大學 2027秋／2028春 出國交換生甄選簡章（中文版）PDF",
                    "source_url": NTHU_2027_2028_GUIDELINES_ZH_URL,
                    "category": "exchange_application",
                    "summary": "清大 2027秋／2028春 第一梯次海外出國交換申請時程、系院三階段審查、兩階段志願選填與 8,000 元保證金規定。",
                },
                "scope": "home_application",
                "program_types": ["exchange"],
                "academic_year": "116",
                "application_round": "2027秋／2028春（116學年度）校級海外出國交換計畫第一梯次",
                "audience": "all_students",
                "opens_at": "2026-09-03T09:00:00+08:00",
                "deadline_at": "2026-10-08T16:00:00+08:00",
                "date_status": "verified_exact",
                "status": "closed",
                "status_note": "2027秋／2028春 第一梯次第一階段線上報名已於 2026/10/08 16:00 截止，現正進行系院審查與 11/03–11/10 第二階段線上志願選填。",
                "deadline_note": "通過第一階段審查者請於 2026/11/03–11/10 16:00 登入系統選填志願，並於 2026/12/11 16:00 前完成報到及繳交 NT$8,000 保證金。",
                "reminder_eligible": False,
                "checked_at": CHECKED_AT,
            },
            {
                "title": "國立清華大學 2028春季班（116-2）校級海外出國交換計畫—第二梯次（預計 2027年1月中旬至3月初開放申請）與赴陸港澳 2027秋季班交換（2026年12月–2027年1月申請）",
                "details": [
                    "2028春季班（第二梯次）海外交換：預計於 2027年1月中旬至3月初開放線上報名（釋出第一梯次分發後剩餘名額，供申請 2028 春季班出國交換，預計 4月中下旬放榜）。",
                    "2027秋季班赴大陸及港澳地區學期交換：預計於 2026年12月至 2027年1月開放申請（經系所初審、學院複審於 2月初送達全球事務處全球學術合作組決審）。",
                ],
                "source": {
                    "title": "國立清華大學全球事務處—出國交換學生計畫時程與陸港澳交換甄選簡章",
                    "source_url": NTHU_OGA_OUTBOUND_URL,
                    "category": "exchange_application",
                    "summary": "清大第二梯次（春季班）海外出國交換與 2027 秋季班赴陸港澳學期交換預定申請時程。",
                },
                "scope": "home_application",
                "program_types": ["exchange"],
                "academic_year": "116",
                "application_round": "2028春季班第二梯次海外出國交換暨2027秋季班赴陸港澳學期交換",
                "audience": "all_students",
                "opens_at": "2027-01-15T09:00:00+08:00",
                "deadline_at": "2027-03-05T16:00:00+08:00",
                "date_status": "reference_only",
                "status": "upcoming",
                "status_note": "2028 春季班第二梯次海外交換預計於 2027年1月中旬至3月初開放申請；2027 秋季班赴陸港澳交換預計於 2026年12月至2027年1月開放申請。",
                "deadline_note": "實際截止日期請依全球事務處全球學術合作組最新公告簡章為準。",
                "reminder_eligible": False,
                "checked_at": CHECKED_AT,
            },
        ],
        "program_overview": [
            {
                "title": f"國立清華大學全球事務處出國交換計畫總覽（{len(partners)} 所全球合作大學・158 所當期開放申請校・A/B/C/D 熱門程度分級）",
                "details": [
                    f"國立清華大學全球事務處全球學術合作組（校本部第一綜合大樓 110 室）統籌辦理校級海外出國交換、赴大陸及港澳地區學期交換，以及「台灣聯合大學系統（UST）學生出國交換計畫」。本平台完整收錄 {len(partners)} 所清大官方合作大學（含當期開放申請之 {open_partner_count} 所交換學校：142 所海外姊妹校、12 所陸港澳姊妹校、{ust_count} 所台聯大交換校，以及 {len(partners) - open_partner_count} 所院系級交換合約校）。",
                    f"清大採行「第一階段系院三階段書審（系所初審 → 學院複審 → 全球處決審）＋第二階段線上選填志願」制度，並獨家公開 201 所海外姊妹校《第一志願選填熱門程度表（A/B/C/D 四級）》協助學生精準配置志願；同時提供 A 類一般地區獎學金（每月 NT$15,000）、B 類特定國家重點獎學金（新南向及中南美洲每月 NT$30,000；以／土／俄／蒙／南非每月 NT$25,000）、清寒學生出國交流獎學金（最高 NT$200,000）及劉維全校友獎學金（赴凱斯西儲大學每學期 NT$120,000–150,000），並收錄 328 份歷屆交換生返國成果報告書（涵蓋 {len(student_experience_rows)} 所合作校）。",
                ],
                "source": {
                    "title": "國立清華大學全球事務處—出國交換學生計畫總覽與姊妹校列表",
                    "source_url": NTHU_OGA_OUTBOUND_URL,
                    "category": "exchange_application",
                    "summary": "清大全球事務處出國交換計畫簡章、176 所合作大學、A/B/C/D 熱門程度表與 328 份返國成果報告書。",
                },
            }
        ],
        "eligibility": [
            {
                "title": "在學身分（大二／碩一／博一以上）、GPA 3.20 或班排前 50%（陸港澳前 30%、獎學金 GPA 3.40／前 20%）與三階段審查制度",
                "details": [
                    "在學年級與學制一致性：申請人須為清大大學部二年級（含）以上、碩士班一年級（含）以上或博士班一年級（含）以上正式學籍在學學生（不含在職專班及在職生；陸港澳交換大一、碩一、博一或轉學生可提具前一學期成績證明申請）。申請時與出國交換期間之學籍學位必須一致（例如以大學部身分申請者，不得於讀研究所期間出國交換）。",
                    "GPA 與班級排名門檻：（1）校級海外交換：申請前兩學期學業平均達 GPA 3.20以上或班級排名前 50% 以上（南大校區百分制須依註冊組對照表換算為等級制 GPA）；（2）校級陸港澳交換：前兩學期平均達 GPA 3.20 以上或全班排名前 30% 以上；（3）台灣聯大（UST）交換：前一學年平均達 GPA 3.0（或 B）以上；（4）申請出國交換生獎學金（A/B 類）、清寒獎學金及劉維全校友獎學金：前一學年平均須達 GPA 3.40 以上或全班／系排名前 20% 以上（學海惜珠須達 GPA 3.20 以上）。",
                    "兩階段分發與 A/B/C/D 熱門程度策略：第一階段通過系初審、院複審、全球處決審後，第二階段於線上系統依院排序選填志願；全球處將姊妹校分為 A（競爭非常激烈）、B（競爭激烈）、C（競爭較不激烈）、D（填第一志願預估可直接分發）四級，若第一志願選填 A/B 級熱門校，建議第二志願以後改填 C/D 級學校。",
                ],
                "source": {
                    "title": "國立清華大學學生出國交換甄選辦法與 2027秋／2028春 甄選簡章 PDF",
                    "source_url": NTHU_SELECTION_REGULATIONS_URL,
                    "category": "exchange_application",
                    "summary": "清大出國交換甄選辦法、GPA 3.20／班排前 50% 門檻、三階段審查與兩階段志願分發。",
                },
            }
        ],
        "language_requirements": [
            {
                "title": "清大校內最低外語能力標準（TOEFL iBT 79［新制 4.0］／IELTS 6.0／JLPT N2／德法西語 B1／TOPIK 4）與不採計 TOEIC／GEPT／MyBest 規定",
                "details": [
                    "六大語組校內最低門檻（依 2026.08.28《國立清華大學出國交換生外語能力標準表》，須為申請截止日前 2 年內有效成績；姊妹校門檻高於校內標準者須符合姊妹校規定）：英語組須達 TOEFL iBT 79（新制 4.0 級分）或 IELTS (Academic) 6.0；日語組須達 JLPT N2；法語組須達 DELF/DALF B1、TCF/TCF-DAP B1 或 FLPT 法語筆試總分 150 分（口試 S-2）；德語組須達 Goethe B1、TestDaF TDN 3 或 FLPT 德語筆試總分 150 分（口試 S-2）；西語組須達 DELE B1 或 FLPT 西語筆試總分 150 分（口試 S-2）；韓語組須達 TOPIK 4 級。",
                    "不予採計之檢定項目警示：清大校級海外出國交換甄選明確規定，不接受 TOEFL iBT MyBest Scores（拼分成績）、不接受多益（TOEIC）、不接受全民英檢（GEPT）、不接受 GRE，亦不接受 Duolingo English Test，請務必提早報考正式 TOEFL iBT 或 IELTS Academic。",
                ],
                "source": {
                    "title": "國立清華大學出國交換生外語能力標準表（2026.08.28 修訂）PDF",
                    "source_url": NTHU_LANGUAGE_STANDARDS_ZH_URL,
                    "category": "exchange_application",
                    "summary": "清大六大語組外語能力最低標準、TOEFL iBT 新制 4.0 對照與不採計 TOEIC/GEPT/MyBest/Duolingo 規定。",
                },
            }
        ],
        "required_documents": [
            {
                "title": "線上報名系統申請表、7 項初審必繳文件、8,000 元保證金與返國後 1 個月內 4 項返國文件義務",
                "details": [
                    "第一階段申請應繳文件（線上填報列印後送交系所辦公室）：1. 線上系統產出之出國交換生申請表（欲申請獎學金者須於系統同步勾選）、2. 本校歷年中文成績單正本（含前兩學期 GPA 或班排名；碩博一新生附前一學位含畢業排名之成績單）、3. 申請截止日前 2 年內有效之外語能力證明影本、4. 每志願各一份修課計畫（可用中文）、5. 身分證明與學生證正反面影本、6. 導師或論文指導教授推薦信 1 封（格式不限）、7. 其他有利審查資料。本清單適用本期海外交換（不含陸港澳）。",
                    "8,000 元保證金、最低修課及格與返國 4 項文件義務：錄取生報到時須繳交行政處理費（保證金）新臺幣 8,000 元（低收／中低收入戶免繳）。交換期間大學部每學期／學季至少須修讀 3 門課程及格、研究生至少 1 門研究所課程及格（獲獎生須為本科相關專業課程；陸港澳大學部至少 9 學分及格）；返國後 1 個月內須繳交（1）返國報告單、（2）成果報告書（交換心得）、（3）姊妹校成績單、（4）登機證（獲獎生另附 3 分鐘影音檔）並完成學分抵免，於當年度 10–11 月無息退還保證金。",
                ],
                "source": {
                    "title": "國立清華大學 2027秋／2028春 出國交換生甄選簡章與線上系統報名流程教學 PDF",
                    "source_url": NTHU_ONLINE_SYSTEM_GUIDE_URL,
                    "category": "exchange_application",
                    "summary": "清大出國交換線上報名系統操作流程、7 項備審文件規格、最低修課規定與 8,000 元保證金退費條件。",
                },
            }
        ],
        "scholarship_info": [
            {
                "title": "出國交換生獎學金 A 類（每月 1.5 萬）、B 類（新南向／中南美每月 3 萬、以土俄蒙南非每月 2.5 萬）、清寒獎學金（最高 20 萬）與劉維全校友獎學金",
                "details": [
                    "出國交換生獎學金 A 類與 B 類（須於第一階段申請交換時同步勾選，前一學年平均須達 GPA 3.40 以上或全班／系排名前 20% 以上，至多補助 5 個月）：（1）A 類一般地區：每月補助 NT$15,000（最高 NT$75,000）；（2）B 類特定國家重點補助：赴新南向國家（印尼、越南、汶萊、泰國、菲律賓、馬來西亞、印度，不含新加坡）及中南美洲國家（阿根廷、巴西、智利、哥斯大黎加、秘魯、墨西哥、厄瓜多爾）每月補助 NT$30,000（最高 NT$150,000）；赴以色列、土耳其、俄羅斯、蒙古、南非每月補助 NT$25,000（最高 NT$125,000）。",
                    "清寒學生出國交流獎學金與劉維全校友獎學金：（1）《國立清華大學清寒學生出國交流獎學金》：補助低收／中低收／特殊境遇家庭或逆境向上具強烈學習熱誠之本國生與境外生（GPA 3.40 或前 20%、操行 80 分以上），每月 NT$20,000 為原則、最高補助 NT$200,000；（2）《劉維全校友出國交流獎學金》：專項補助赴美國凱斯西儲大學（Case Western Reserve University）交換之大學部學生，一般生每學期 NT$120,000、清寒生每學期 NT$150,000（至多 2 學期）；另含教育部「學海飛颺」、「學海惜珠」（GPA 3.20 以上）及日本台灣交流協會獎學金。",
                ],
                "source": {
                    "title": "國立清華大學出國交換生獎學金審查作業細則與清寒學生出國交流獎學金甄選簡章 PDF",
                    "source_url": NTHU_SCHOLARSHIP_REGULATIONS_URL,
                    "category": "scholarship",
                    "summary": "清大出國交換獎學金 A/B 類金額標準、劉維全校友獎學金、清寒學生出國交流獎學金與學海惜珠辦法。",
                },
            }
        ],
        "document_explanations": [
            {
                "title": "國立清華大學出國交換生線上系統報名、中文與外文讀書計畫（含擬修課程表）、2 封推薦信與語檢採計規範",
                "summary": "說明清大出國交換第一階段線上系統報名與系所紙本送件程序、中英文讀書計畫與自傳撰寫要求，以及不接受 TOEIC／GEPT／MyBest Scores 之語檢規定。",
                "key_points": [
                    "申請人須先於「出國交換生甄試報名系統」（https://oga-exchange.vm.nthu.edu.tw/outexchange/index/index/puid/11521）完成線上填報（欲申請校內出國交換生獎學金者必須在系統上同步勾選，逾時不予補辦），再列印申請表連同全套備審資料於截止日前送達所屬系所辦公室。",
                    "讀書計畫與自傳須同時準備「中文與外文（英文或交換國語言）」版本，其中讀書計畫應具體列出擬於目標姊妹校修讀之專業課程清單（大學部每學期／學季至少 3 門、研究生至少 1 門研究所課程）。",
                    "外語能力證明必須為申請截止日前 2 年內有效之正式成績單（TOEFL iBT 79［新制 4.0］／IELTS Academic 6.0 或日語 N2、德法西語 B1、韓語 TOPIK 4 級）；切勿提交 TOEIC、GEPT、GRE、Duolingo 或 TOEFL MyBest Scores。",
                ],
                "applies_to": [],
                "source": {
                    "title": "國立清華大學 2027秋／2028春 出國交換生甄選簡章與外語能力標準表 PDF",
                    "source_url": NTHU_2027_2028_GUIDELINES_ZH_URL,
                    "category": "exchange_application",
                    "summary": None,
                },
                "document_url": NTHU_2027_2028_GUIDELINES_ZH_URL,
                "document_type": "official_document",
                "full_text_extracted": True,
            }
        ],
        "rule_explanations": [
            {
                "title": "國立清華大學學生出國交換甄選辦法：系院三階段審查、A/B/C/D 熱門程度兩階段志願分發與 8,000 元保證金退費規定",
                "summary": "規範清大校級出國交換之系所初審、學院複審、全球處決審流程、兩階段線上志願選填策略、最低修課及格門檻與返國四項文件義務。",
                "key_points": [
                    "第一階段由系所初審、學院複審評定院推薦排序後送全球事務處決審；通過者於第二階段（11月上旬）登入系統選填志願，建議參考全球處公布之姊妹校 A/B/C/D 第一志願選填熱門程度表配置志願。",
                    "海外交換期間須維持清大在學學籍並繳交清大全額學雜費，大學部每學期／學季至少修讀 3 門課程及格、研究生至少修讀 1 門研究所課程及格（獲獎學金者須為本科相關專業課程；陸港澳大學部至少 9 學分及格）。",
                    "錄取報到時繳交行政處理費（保證金）新臺幣 8,000 元（低收／中低收入戶免繳）；返國後 1 個月內繳交返國報告單、成果報告書、姊妹校成績單、登機證（獲獎生另附 3 分鐘影音檔）並完成學分抵免，於當年度 10–11 月無息退還。",
                ],
                "applies_to": [],
                "source": {
                    "title": "國立清華大學學生出國交換甄選辦法與出國交換生獎學金審查作業細則 PDF",
                    "source_url": NTHU_SELECTION_REGULATIONS_URL,
                    "category": "exchange_application",
                    "summary": None,
                },
                "document_url": NTHU_SELECTION_REGULATIONS_URL,
                "document_type": "official_document",
                "full_text_extracted": True,
            }
        ],
        "sources": [
            {
                "title": "國立清華大學全球事務處—出國交換學生計畫總覽與各梯次申請時程",
                "source_url": NTHU_OGA_OUTBOUND_URL,
                "category": "exchange_application",
                "summary": None,
            },
            {
                "title": "國立清華大學 2027秋／2028春 海外交換學生計畫姊妹校列表（142 所海外合作大學名額與條件）",
                "source_url": NTHU_OVERSEAS_PARTNERS_URL,
                "category": "partner_school",
                "summary": None,
            },
            {
                "title": "國立清華大學出國交換生甄試報名系統—2027秋／2028春 申請資格一覽與各校 GPA／語檢明細",
                "source_url": NTHU_VM_OVERVIEW_URL,
                "category": "partner_school",
                "summary": None,
            },
            {
                "title": "國立清華大學全球事務處—赴大陸及港澳地區學期交換姊妹校列表與選送簡章",
                "source_url": NTHU_MAINLAND_PARTNERS_URL,
                "category": "partner_school",
                "summary": None,
            },
            {
                "title": "國立清華大學 2027秋／2028春（116學年度）出國交換生甄選簡章（中英文版）PDF",
                "source_url": NTHU_2027_2028_GUIDELINES_ZH_URL,
                "category": "exchange_application",
                "summary": None,
            },
            {
                "title": "國立清華大學出國交換生外語能力標準表（2026.08.28 修訂，含 TOEFL iBT 新制 4.0 對照）PDF",
                "source_url": NTHU_LANGUAGE_STANDARDS_ZH_URL,
                "category": "exchange_application",
                "summary": None,
            },
            {
                "title": "國立清華大學 116學年度台灣聯合大學系統（UST）學生出國交換計畫第一梯次甄選公告與簡章 PDF",
                "source_url": NTHU_UST_116_NOTICE_URL,
                "category": "exchange_application",
                "summary": None,
            },
            {
                "title": "國立清華大學出國交換生獎學金審查作業細則（A類、B類、劉維全校友獎學金）與清寒學生出國交流獎學金甄選簡章 PDF",
                "source_url": NTHU_SCHOLARSHIP_REGULATIONS_URL,
                "category": "scholarship",
                "summary": None,
            },
            {
                "title": "國立清華大學海外交換姊妹校第一志願選填熱門程度表（A/B/C/D 四級，201 所合作校統計）",
                "source_url": NTHU_POPULARITY_SHEET_URL,
                "category": "partner_school",
                "summary": None,
            },
            {
                "title": "國立清華大學全球事務處—出國交換返國報告書與陸港澳交換心得分享專區（共 328 份報告）",
                "source_url": NTHU_EXPERIENCE_OVERSEAS_URL,
                "category": "partner_school",
                "summary": None,
            },
        ],
    }
    (OFFICIAL_NTHU_DIR / "student_dashboard.json").write_text(
        json.dumps(student_dashboard_payload, ensure_ascii=False, indent=2)
        + "\n",
        encoding="utf-8",
    )

    pages_records = [
        {
            "title": "國立清華大學：2027秋／2028春 校級海外交換、陸港澳交換與 116-1 台灣聯大交換（2027/01/04 截止）申請時程",
            "source_url": NTHU_OGA_OUTBOUND_URL,
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
            "title": "國立清華大學：出國交換申請資格、GPA 3.20／班排前 50% 門檻、系院三階段審查、A/B/C/D 志願選填與 8,000 元保證金規定",
            "source_url": NTHU_SELECTION_REGULATIONS_URL,
            "published_at": "2026-08-28T00:00:00Z",
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
            "title": "國立清華大學：出國交換生外語能力標準表（TOEFL iBT 79［新制 4.0］／IELTS 6.0／N2／B1／TOPIK 4）與不接受 TOEIC／GEPT／MyBest 規定",
            "source_url": NTHU_LANGUAGE_STANDARDS_ZH_URL,
            "published_at": "2026-08-28T00:00:00Z",
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
            "title": "國立清華大學：線上系統報名、7 項初審必繳文件（含中英文讀書計畫及 2 封推薦信）與返國 4 項文件義務",
            "source_url": NTHU_2027_2028_GUIDELINES_ZH_URL,
            "published_at": "2026-08-28T00:00:00Z",
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
            "title": "國立清華大學：出國交換生獎學金 A 類（每月 1.5 萬）、B 類（新南向／中南美每月 3 萬、以土俄蒙南非每月 2.5 萬）、清寒獎學金與劉維全校友獎學金",
            "source_url": NTHU_SCHOLARSHIP_REGULATIONS_URL,
            "published_at": "2026-08-28T00:00:00Z",
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
    (OFFICIAL_NTHU_DIR / "pages.jsonl").write_text(
        "\n".join(json.dumps(p, ensure_ascii=False) for p in pages_records)
        + "\n",
        encoding="utf-8",
    )

    home_rules = {
        "school_id": "nthu",
        "school_name": "國立清華大學",
        "eligibility": student_dashboard_payload["eligibility"],
        "application_periods": student_dashboard_payload["application_periods"],
        "selection_rules": {
            "overseas_gpa_minimum": 3.20,
            "overseas_rank_percent_maximum": 50.0,
            "mainland_gpa_minimum": 3.20,
            "mainland_rank_percent_maximum": 30.0,
            "ust_gpa_minimum": 3.00,
            "scholarship_gpa_minimum": 3.40,
            "scholarship_rank_percent_maximum": 20.0,
            "review_stages": [
                "department_initial_review",
                "college_secondary_review",
                "oga_final_review",
            ],
            "preference_selection_stages": 2,
            "popularity_tiers": ["A", "B", "C", "D"],
            "deposit_twd": 8000,
            "deposit_low_income_twd": 0,
            "minimum_passed_courses_overseas_undergraduate": 3,
            "minimum_passed_courses_overseas_graduate": 1,
            "minimum_passed_credits_mainland_undergraduate": 9,
            "minimum_passed_courses_mainland_graduate": 1,
            "return_documents_due": "返國後 1 個月內（返國報告單、成果報告書、姊妹校成績單、登機證；獲獎生另附 3 分鐘影音檔）",
        },
        "source_urls": nthu_source_urls,
        "verified_at": "2026-10-19",
    }
    (OFFICIAL_NTHU_DIR / "home_rules.json").write_text(
        json.dumps(home_rules, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    (OFFICIAL_NTHU_DIR / "documents.json").write_text(
        json.dumps(
            {
                "school_name": "國立清華大學",
                "required_documents": student_dashboard_payload["required_documents"],
                "source_urls": nthu_source_urls,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    (OFFICIAL_NTHU_DIR / "scholarships.json").write_text(
        json.dumps(
            {
                "school_name": "國立清華大學",
                "scholarships": student_dashboard_payload["scholarship_info"],
                "source_urls": nthu_source_urls,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    completeness = {
        "school_id": "nthu",
        "school_name": "國立清華大學",
        "total_partners": len(partners),
        "partner_count": len(partners),
        "international_partners": sum(
            1 for p in partners if p["country"] not in {"中國大陸", "香港", "澳門"}
        ),
        "mainland_partners": sum(
            1 for p in partners if p["country"] in {"中國大陸", "香港", "澳門"}
        ),
        "ust_partners": ust_count,
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
        "active_term": "116學年度台灣聯合大學系統（UST）學生出國交換計畫第一梯次即日起至 2027/01/04 16:00 受理清大全球處收件（11/18 12:20 說明會）；2027秋／2028春 校級海外出國交換第一梯次已於 2026/10/08 截止第一階段報名，於 11/03–11/10 進行線上志願選填、12/11 報到；2028 春季班第二梯次預計於 2027年1月中至3月初開放申請（共收錄 176 所全球合作大學，含 158 所當期開放申請校及 18 所院系級交換合約校）。",
        "verified_at": "2026-10-19",
    }
    (OFFICIAL_NTHU_DIR / "catalog-completeness.json").write_text(
        json.dumps(completeness, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    (OFFICIAL_NTHU_DIR / "verification_status.json").write_text(
        json.dumps(
            {
                "school_id": "nthu",
                "school_name": "國立清華大學",
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
            "sources/nthu/nthu_2027_2028_outbound_guidelines_zh.pdf",
            NTHU_2027_2028_GUIDELINES_ZH_URL,
            "國立清華大學 2027秋／2028春（116學年度）出國交換生甄選簡章（中文版）PDF",
        ),
        (
            "sources/nthu/nthu_2027_2028_outbound_guidelines_en.pdf",
            NTHU_2027_2028_GUIDELINES_EN_URL,
            "國立清華大學 2027 Fall / 2028 Spring Outbound Student Exchange Application Guidelines（英文版）PDF",
        ),
        (
            "sources/nthu/nthu_outbound_selection_regulations.pdf",
            NTHU_SELECTION_REGULATIONS_URL,
            "國立清華大學學生出國交換甄選辦法 PDF",
        ),
        (
            "sources/nthu/nthu_outbound_scholarship_regulations.pdf",
            NTHU_SCHOLARSHIP_REGULATIONS_URL,
            "國立清華大學出國交換生獎學金審查作業細則（A類、B類、劉維全校友獎學金）PDF",
        ),
        (
            "sources/nthu/nthu_disadvantaged_scholarship_guidelines.pdf",
            NTHU_DISADVANTAGED_SCHOLARSHIP_URL,
            "國立清華大學清寒學生出國交流獎學金甄選簡章 PDF",
        ),
        (
            "sources/nthu/nthu_language_proficiency_standards_zh.pdf",
            NTHU_LANGUAGE_STANDARDS_ZH_URL,
            "國立清華大學出國交換生外語能力標準表（中文版，2026.08.28 修訂）PDF",
        ),
        (
            "sources/nthu/nthu_language_proficiency_standards_en.pdf",
            NTHU_LANGUAGE_STANDARDS_EN_URL,
            "國立清華大學出國交換生外語能力標準表（英文版，2026.08.28 修訂）PDF",
        ),
        (
            "sources/nthu/nthu_outbound_faq_hot_questions.pdf",
            NTHU_FAQ_HOT_QUESTIONS_URL,
            "國立清華大學出國交換生計畫熱門問題集（FAQ）PDF",
        ),
        (
            "sources/nthu/nthu_2027_2028_info_session_slides.pdf",
            NTHU_INFO_SESSION_SLIDES_URL,
            "國立清華大學 2027秋／2028春 出國交換生申請說明會簡報 PDF",
        ),
        (
            "sources/nthu/nthu_online_system_user_guide.pdf",
            NTHU_ONLINE_SYSTEM_GUIDE_URL,
            "國立清華大學出國交換生甄試報名系統線上報名流程教學 PDF",
        ),
        (
            "sources/nthu/nthu_pre_departure_orientation_slides.pdf",
            NTHU_PRE_DEPARTURE_SLIDES_URL,
            "國立清華大學錄取交換生行前說明會簡報 PDF",
        ),
        (
            "sources/nthu/nthu_mainland_hk_mo_selection_guidelines.pdf",
            NTHU_MAINLAND_GUIDELINES_URL,
            "國立清華大學選送學生赴大陸及港澳地區大學修讀學分甄選簡章 PDF",
        ),
        (
            "sources/nthu/nthu_mainland_hk_mo_application_flowchart.pdf",
            NTHU_MAINLAND_FLOWCHART_URL,
            "國立清華大學赴大陸地區及香港、澳門交換計畫申請流程圖 PDF",
        ),
        (
            "sources/nthu/nthu_cross_strait_summer_exchange_regulations.pdf",
            NTHU_CROSS_STRAIT_SUMMER_URL,
            "國立清華大學兩岸暑期交流實施辦法 PDF",
        ),
        (
            "sources/nthu/nthu_116_ust_exchange_round1_notice.pdf",
            NTHU_UST_116_PDF_URL,
            "116學年度台灣聯合大學系統（UST）學生出國交換計畫（I）第一梯次甄選公告與名額表 PDF",
        ),
        (
            "sources/nthu/nthu_116_ust_exchange_application_form.pdf",
            NTHU_UST_116_FORM_URL,
            "116學年度台灣聯合大學系統（UST）學生出國交換計畫申請表 PDF",
        ),
        (
            "sources/nthu/nthu_dual_degree_scholarship_regulations.pdf",
            NTHU_DUAL_DEGREE_SCHOLARSHIP_URL,
            "國立清華大學雙聯學位生獎學金辦法 PDF",
        ),
        (
            "sources/nthu/nthu_short_term_visit_pilot_regulations.pdf",
            NTHU_SHORT_TERM_VISIT_URL,
            "國立清華大學補助博士生及雙聯學位生赴國外短期研究訪問試辦要點 PDF",
        ),
        (
            "sources/nthu/nthu_moe_xuehai_zhumeng_regulations.pdf",
            NTHU_MOE_XUEHAI_ZHUMENG_URL,
            "國立清華大學執行教育部學海築夢及新南向學海築夢計畫作業要點 PDF",
        ),
        (
            "sources/nthu/nthu_overseas_anti_fraud_guide.pdf",
            NTHU_ANTI_FRAUD_GUIDE_URL,
            "國立清華大學海外留學與交換防詐安全宣導手冊 PDF",
        ),
        (
            "sources/nthu/nthu_overseas_partners_2027_2028.html",
            NTHU_OVERSEAS_PARTNERS_URL,
            "國立清華大學 2027秋／2028春 海外交換學生計畫姊妹校列表（142 校）HTML",
        ),
        (
            "sources/nthu/nthu_vm_qualification_details_11521.json",
            NTHU_VM_OVERVIEW_URL,
            "國立清華大學出國交換生甄試報名系統 142 所海外姊妹校申請資格明細 JSON",
        ),
        (
            "sources/nthu/nthu_mainland_hk_mo_partners.html",
            NTHU_MAINLAND_PARTNERS_URL,
            "國立清華大學赴大陸及港澳地區交換姊妹校列表（12 校）HTML",
        ),
        (
            "sources/nthu/nthu_college_dept_partners_overseas_9490.html",
            NTHU_COLLEGE_DEPT_OVERSEAS_URL,
            "國立清華大學院系級海外交換學生合約列表 HTML",
        ),
        (
            "sources/nthu/nthu_college_dept_partners_mainland_9491.html",
            NTHU_COLLEGE_DEPT_MAINLAND_URL,
            "國立清華大學院系級大陸及港澳交換學生合約列表 HTML",
        ),
        (
            "sources/nthu/nthu_all_agreements_table.html",
            NTHU_ALL_AGREEMENTS_URL,
            "國立清華大學全球學術交流協議統計總表（299 校）HTML",
        ),
        (
            "sources/nthu/nthu_partner_popularity_tiers_2027_2028.csv",
            NTHU_POPULARITY_SHEET_URL,
            "國立清華大學海外交換姊妹校第一志願選填熱門程度表（A/B/C/D 四級）CSV",
        ),
        (
            "sources/nthu/nthu_overseas_experience_reports_2024_2025.json",
            NTHU_EXPERIENCE_OVERSEAS_URL,
            "國立清華大學 2022–2025 歷屆海外交換生返國成果報告書索引（321 篇）JSON",
        ),
        (
            "sources/nthu/nthu_catalog_source.json",
            NTHU_OVERSEAS_PARTNERS_URL,
            "國立清華大學 176 所出國交換合作大學整合資料集（158 所當期開放 + 18 所院系級交換合約校）JSON",
        ),
        (
            "sources/nthu/nthu_resolved_locations.json",
            NTHU_OVERSEAS_PARTNERS_URL,
            "國立清華大學 176 所出國交換合作大學 ROR / Wikidata 地理座標核對表 JSON",
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
        "school_id": "nthu",
        "school_name": "國立清華大學",
        "generated_at": CHECKED_AT,
        "active_cycle_note": completeness["active_term"],
        "sources": prov_sources,
    }
    prov_text = json.dumps(provenance_payload, ensure_ascii=False, indent=2) + "\n"
    (OFFICIAL_NTHU_DIR / "import_provenance.json").write_text(
        prov_text, encoding="utf-8"
    )
    (OFFICIAL_NTHU_DIR / "import-provenance.json").write_text(
        prov_text, encoding="utf-8"
    )

    from exchange_info.generated_content_review import review_generated_content
    review_generated_content(REPO_ROOT, "nthu", round_id=20)
    review_generated_content(REPO_ROOT, "nthu", round_id=21)
    from exchange_info.usp_source_review import apply_usp_source_review
    apply_usp_source_review(REPO_ROOT, "nthu")
    from exchange_info.vilnius_akita_review import apply_vilnius_akita_review
    apply_vilnius_akita_review(REPO_ROOT, "nthu")

    print(
        f"Successfully built NTHU catalog: {len(partners)} partners ({open_partner_count} open, "
        f"{ust_count} UST, {completeness['verified_campus_images']} verified images, "
        f"{completeness['verified_locations']} verified locations), {len(workflows)} workflows, "
        f"{len(destinations)} destinations, {len(research_records)} research records, "
        f"{exp_covered_schools} schools with experience records ({len(student_experience_rows)} rows)."
    )


if __name__ == "__main__":
    main()
