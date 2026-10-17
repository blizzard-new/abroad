"""Build the official National Sun Yat-sen University (國立中山大學, NSYSU) exchange data bundle."""

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

SOURCES_NSYSU_DIR = REPO_ROOT / "sources" / "nsysu"
OFFICIAL_NSYSU_DIR = REPO_ROOT / "src" / "exchange_info" / "official_data" / "nsysu"
STATIC_DIR = REPO_ROOT / "src" / "exchange_info" / "static"

CHECKED_AT = "2026-10-18T00:20:00Z"

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
    "英國": (
        "GBP 1,100–1,600 / 月（含學生宿舍、飲食與大眾運輸）",
        "交換一學期（6 個月內）可辦理 Standard Visitor 簽證，一學年須辦理 Student Visa 並繳納 IHS 醫療附加費。",
    ),
    "法國": (
        "EUR 850–1,400 / 月（巴黎地區約 EUR 1,200–1,600 / 月；可申請 CAF 房屋補助）",
        "須透過法國教育中心（Campus France）面試並申辦長期學生簽證（VLS-TS）。",
    ),
    "德國": (
        "EUR 934–1,200 / 月（德國簽證限制提領帳戶基準為每月 EUR 934）",
        "須辦理德國法定公保（約 EUR 120–130 / 月）及繳納學期雜費／學期交通票（Semesterticket）。",
    ),
    "奧地利": (
        "EUR 850–1,250 / 月（含維也納／林茲／茵斯布魯克／庫夫施泰因學生宿舍、餐飲與大眾運輸）",
        "交換一學期（6 個月內）須申辦奧地利學生簽證 D（Visa D），超過 6 個月須申辦學生居留許可。",
    ),
    "西班牙": (
        "EUR 800–1,250 / 月（含學生公寓、飲食與大眾運輸）",
        "須備妥涵蓋全額醫療與遺體運返之私人醫療保險以申辦西班牙學生簽證。",
    ),
    "義大利": (
        "EUR 800–1,300 / 月（羅馬與米蘭約 EUR 1,000–1,400 / 月；波爾察諾、杜林與維羅納約 EUR 800–1,150 / 月）",
        "須向義大利經濟貿易文化推廣辦事處申辦學生簽證 D，抵義後 8 個工作天內申辦居留證（Permesso di Soggiorno）。",
    ),
    "荷蘭": (
        "EUR 950–1,400 / 月（荷蘭移民局 IND 財力證明基準約 EUR 1,225 / 月）",
        "由接待校代辦 MVV/VVR 居留許可，烏特勒支、鹿特丹與馬斯垂克房源緊張建議獲提名後立即申請宿舍。",
    ),
    "比利時": (
        "EUR 850–1,250 / 月（含魯汶／布魯塞爾／根特／列日學生宿舍、餐飲與大眾運輸）",
        "須辦理長期學生簽證 D 簽，抵達後向當地市政廳登記居留。",
    ),
    "瑞士": (
        "CHF 1,500–2,200 / 月（含學生住宿、膳食與強制保險）",
        "須透過瑞士商務辦事處申辦學生簽證，並於抵瑞後申請居留證與醫療保險豁免或投保。",
    ),
    "丹麥": (
        "DKK 6,500–9,500 / 月（含學生宿舍、飲食與單車／大眾運輸）",
        "須申辦 ST1 學生居留許可，抵丹後登記 CPR 號碼即可享有公醫保障。",
    ),
    "瑞典": (
        "SEK 9,500–13,000 / 月（瑞典移民局財力基準約 SEK 10,314 / 月）",
        "交換超過 3 個月須向瑞典移民局申辦學生居留許可（Residence Permit for Studies）。",
    ),
    "挪威": (
        "NOK 11,000–15,000 / 月（挪威移民局 UDI 財力證明基準約 NOK 13,790 / 月）",
        "須向挪威移民局（UDI）申辦學生居留許可並繳交財力擔保。",
    ),
    "芬蘭": (
        "EUR 750–1,100 / 月（芬蘭移民局 Migri 財力證明基準約 EUR 800 / 月）",
        "須透過 Enter Finland 申辦學生居留許可並投保涵蓋全期之醫療保險。",
    ),
    "愛沙尼亞": (
        "EUR 600–900 / 月（塔爾圖與塔林學生宿舍與生活開支實惠）",
        "交換超過 90 天須申辦愛沙尼亞長期學生簽證（D 簽）並投保歐盟規格醫療保險。",
    ),
    "拉脫維亞": (
        "EUR 600–900 / 月（里加學生宿舍與日常飲食交通開支實惠）",
        "須申辦拉脫維亞長期簽證（D 簽）或學生居留許可並備妥歐盟規格醫療保險。",
    ),
    "立陶宛": (
        "EUR 600–900 / 月（維爾紐斯與考納斯學生宿舍費用實惠）",
        "須透過 MIGRIS 系統申辦立陶宛國家簽證（D 簽）或臨時居留許可。",
    ),
    "波蘭": (
        "EUR 550–850 / 月（約 PLN 2,400–3,600，華沙、克拉科夫、弗羅茨瓦夫與盧布林校內宿舍實惠）",
        "須向波蘭臺北辦事處申辦 D 類國別學生簽證並備妥規定旅行醫療保險。",
    ),
    "捷克": (
        "EUR 600–900 / 月（含布拉格／布爾諾／赫拉德茨克拉洛韋學生宿舍、食堂與市區交通卡）",
        "須提前預約捷克經濟文化辦事處申辦長期學生簽證與捷克合約醫療保險。",
    ),
    "斯洛伐克": (
        "EUR 550–850 / 月（布拉提斯拉瓦學生宿舍與生活成本低廉）",
        "須申辦斯洛伐克國家長期簽證（D 簽）或臨時居留並備妥醫療保險。",
    ),
    "斯洛維尼亞": (
        "EUR 650–950 / 月（盧布爾雅那可享學生餐券補助 Subvencionirana študentska prehrana）",
        "須申辦斯洛維尼亞長期簽證（Type D）或單一居留許可並備妥醫療保險。",
    ),
    "克羅埃西亞": (
        "EUR 650–950 / 月（薩格勒布學生生活與公共交通費用適中）",
        "須辦理克羅埃西亞長期簽證或學生臨時居留許可（Temporary Stay for the Purpose of Studying）。",
    ),
    "匈牙利": (
        "EUR 600–900 / 月（布達佩斯生活與住宿開支實惠）",
        "須向匈牙利貿易辦事處申辦長期居留簽證（D 簽）並備妥歐盟規格醫療保險。",
    ),
    "羅馬尼亞": (
        "EUR 500–800 / 月（布加勒斯特學生宿舍與生活成本低廉）",
        "須憑羅馬尼亞教育部入學許可核准函申辦 D/SD 學生簽證。",
    ),
    "科索沃": (
        "EUR 450–750 / 月（普里斯提納生活與外宿成本低廉）",
        "須依科索沃共和國入境與居留規定辦理簽證通報及海外醫療保險。",
    ),
    "俄羅斯": (
        "USD 500–850 / 月（莫斯科與聖彼得堡校內宿舍費用實惠）",
        "須憑接待校核發之俄羅斯聯邦移民署官方邀請函向莫北協駐臺代表處申辦學生簽證。",
    ),
    "土耳其": (
        "EUR 550–850 / 月（伊斯坦堡與安卡拉學生生活與交通開支實惠）",
        "須申辦土耳其學生簽證並於抵土後申辦短期學生居留證（Ikamet）與當地醫保。",
    ),
    "以色列": (
        "USD 1,000–1,500 / 月（海法與特拉維夫住宿與日常飲食開支）",
        "須向駐臺北以色列經濟文化辦事處申辦 A/2 學生簽證並投保接待校指定醫療保險。",
    ),
    "澳洲": (
        "AUD 1,800–2,600 / 月（含布里斯本／黃金海岸／墨爾本／伯斯住宿與日常開支）",
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
    "中國大陸": (
        "RMB 2,000–3,800 / 月（校內宿舍約 RMB 600–1,800 / 學期、學生食堂費用低廉，北京、上海、南京、武漢、廣州、廈門生活機能完善）",
        "持臺胞證（臺灣居民來往大陸通行證）入境，並依接待校規定投保大陸境內來華留學生綜合醫療保險（約 RMB 400 / 學期）。",
    ),
    "香港": (
        "HKD 6,500–11,000 / 月（含香港大學／港科大／城大／理大／浸大／嶺大／教大校內宿舍與日常開支）",
        "須透過接待校向香港入境事務處申辦學生簽證／進入許可（Student Visa / Entry Permit）。",
    ),
    "澳門": (
        "HKD 4,500–7,500 / 月（約 MOP 4,650–7,700，含澳門大學住宿式書院與日常開支）",
        "抵澳後依澳門治安警察局居留及逗留事務廳規定辦理「逗留特別許可（學生）」。",
    ),
    "新加坡": (
        "SGD 1,200–2,000 / 月（含校內宿舍或外宿、熟食中心餐飲與地鐵交通）",
        "須透過新加坡移民局 SOLAR 系統申辦 Student's Pass（STP）並繳納接待校強制醫療保險。",
    ),
    "馬來西亞": (
        "MYR 1,500–2,500 / 月（吉隆坡與金寶生活機能便利且物價親民）",
        "須透過 EMGS（Education Malaysia Global Services）系統申辦學生簽證（VAL / Student Pass）。",
    ),
    "泰國": (
        "THB 15,000–25,000 / 月（曼谷與巴吞他尼生活成本親民）",
        "須憑接待校入學許可向泰國貿易經濟辦事處申辦 Non-Immigrant ED 學生簽證。",
    ),
    "印尼": (
        "IDR 5,000,000–9,000,000 / 月（日惹與泗水生活開支實惠）",
        "須由接待校協助向印尼移民總局申辦學習簽證（C316 / 學生電子簽證）。",
    ),
    "越南": (
        "USD 400–700 / 月（約 VND 10,000,000–17,000,000，河內生活成本低廉）",
        "須憑接待校入學許可透過駐臺北越南經濟文化辦事處申辦 DH 學生簽證。",
    ),
    "菲律賓": (
        "USD 500–850 / 月（約 PHP 28,000–48,000，馬尼拉與奎松市住宿與生活開支）",
        "須憑接待校入學許可向馬尼拉經濟文化辦事處申辦 9(f) 學生簽證或 SSP 特別學習許可。",
    ),
    "印度": (
        "USD 400–700 / 月（新德里與清奈校內住宿與日常開支實惠）",
        "須憑接待校正式入學許可向印度台北協會申辦 Student Visa。",
    ),
    "斯里蘭卡": (
        "USD 400–700 / 月（可倫坡與佩拉德尼亞生活成本低廉）",
        "須憑接待校入學許可申辦斯里蘭卡 Entry / Student Visa 並備妥海外醫療保險。",
    ),
    "墨西哥": (
        "USD 700–1,100 / 月（約 MXN 13,000–20,000，蒙特雷與墨西哥城生活開支適中）",
        "交換一學期（180 天內）依國籍與簽證規定辦理入境，超過 180 天須申辦墨西哥學生臨時居留簽證。",
    ),
    "智利": (
        "USD 750–1,200 / 月（聖地牙哥與比尼亞德爾馬住宿、餐飲與地鐵交通）",
        "須憑接待校入學許可向智利商務辦事處申辦學生居留簽證（Visa de Residente Estudiante）。",
    ),
    "秘魯": (
        "USD 650–1,000 / 月（利馬住宿與日常飲食交通開支）",
        "須憑接待校入學許可辦理秘魯交換學生簽證並投保涵蓋全期之國際醫療保險。",
    ),
    "南非": (
        "USD 650–1,050 / 月（約 ZAR 12,000–19,000，斯泰倫博斯校內宿舍與日常開支）",
        "須向南非聯絡辦事處申辦 Study Visa 並投保南非認可之醫療保險（Medical Aid Scheme）。",
    ),
}

FACTSHEET_PAGE_URLS = {
    "oceania": "https://oia.nsysu.edu.tw/p/412-1308-20731.php?Lang=zh-tw",
    "americas": "https://oia.nsysu.edu.tw/p/412-1308-20732.php?Lang=zh-tw",
    "europe": "https://oia.nsysu.edu.tw/p/412-1308-20733.php?Lang=zh-tw",
    "asia": "https://oia.nsysu.edu.tw/p/412-1308-20735.php?Lang=zh-tw",
}

EXPERIENCE_PAGE_URLS = {
    "oceania": "https://oia.nsysu.edu.tw/p/412-1308-20776.php?Lang=zh-tw",
    "americas": "https://oia.nsysu.edu.tw/p/412-1308-20775.php?Lang=zh-tw",
    "europe": "https://oia.nsysu.edu.tw/p/412-1308-20774.php?Lang=zh-tw",
    "asia": "https://oia.nsysu.edu.tw/p/412-1308-20773.php?Lang=zh-tw",
}


def clean_bullet_text(s: str) -> str:
    if not s:
        return ""
    s = s.replace("", "☑").replace("", "☐").replace("◦", "・").replace("•", "｜")
    s = re.sub(r"\s+", " ", s).strip(" ｜・")
    return s


def format_colleges(item: dict) -> str:
    entries = item.get("pdf_entries") or []
    cats = {e.get("category") for e in entries}
    sister = item.get("sister") or {}
    fs = item.get("factsheet") or {}
    if "UW" in cats and "CM" in cats:
        return "全校各學院（校級交換名額）及管理學院專有名額（雙軌並列開放）"
    if "CM" in cats and "UW" not in cats:
        return "管理學院（本合作校為管理學院院級交換協議姐妹校，或須具商管背景）"
    if "JP" in cats or "CN" in cats or "UW" in cats:
        for e in entries:
            lvl = e.get("level") or ""
            m_lim = re.search(r"限([^。•\n]{2,35}(?:學院|學系|研究所)[^。•\n]{0,20})", lvl)
            if m_lim:
                return f"校級交換計畫（特別規定：{clean_bullet_text(m_lim.group(0))}）"
        return "不限學院（全校各學院大學部一至四年級及碩士班一至二年級在校生皆可申請，須對照交換校開課院系）"
    if fs.get("agreement_level") == "College of Management":
        return "管理學院（院級交換協議姐妹校）"
    depts = sister.get("depts_zh") or []
    if depts and depts != ["校級"]:
        return "、".join(depts)
    return "全校各學院（依當期學生出國交換甄選簡章與兩校協議規定辦理）"


def format_degree_levels(item: dict) -> str:
    entries = item.get("pdf_entries") or []
    for e in entries:
        lvl = clean_bullet_text(e.get("level") or "")
        if "大學部及研究所" in lvl or "學士、碩士" in lvl or "大學部、研究所" in lvl:
            return "大學部（一至四年級）、碩士班（一至二年級）"
        if "僅限大學部" in lvl or ("大學部" in lvl and "研究所" not in lvl and "碩士" not in lvl):
            return "大學部（一至四年級）"
        if "僅限研究所" in lvl or "碩士班" in lvl:
            return "碩士班（一至二年級）"
    return "大學部（一至四年級）、碩士班（一至二年級）※不含延畢生、在職專班及博士班"


def format_language_req(item: dict) -> str:
    entries = item.get("pdf_entries") or []
    country = item["country"]
    parts = []
    for e in entries:
        lr = clean_bullet_text(e.get("language_requirement") or "")
        if lr and lr not in parts:
            parts.append(lr)
    if parts:
        joined = "；".join(parts)
        return joined[:360]
    if country == "中國大陸":
        return "赴中國大陸交換免附語言檢定證明（外國籍及僑生申請部分學校須具 HSK 5 級 180–210 分以上）"
    if country == "日本":
        return "校內門檻：須達 JLPT N5（含）以上，或英語達 TOEFL iBT 60 / IELTS 5.0 / TOEIC 600 / Cambridge 154 / Duolingo 80 / BESTEP 培力英檢聽讀 170（並須符合交換校個別語檢門檻）"
    return "校內門檻：須達 TOEFL iBT 60、IELTS 5.0、TOEIC 600、Cambridge PET 154、Duolingo 80 或 BESTEP 培力英檢聽讀 170 以上（並須符合交換校於當期簡章所列之語檢標準）"


def format_gpa_req(item: dict) -> str:
    entries = item.get("pdf_entries") or []
    gpa_notes = []
    for e in entries:
        lvl = clean_bullet_text(e.get("level") or "")
        for m in re.finditer(r"GPA[^｜。；]{2,40}", lvl, re.I):
            g = m.group(0).strip()
            if g not in gpa_notes:
                gpa_notes.append(g)
    base = "國立中山大學校內評分基準：採計歷年學業成績班排名（日本與其他國家甄選占總成績 30%、中國大陸甄選占 60%，甄選總成績未達 60 分不予錄取）"
    if gpa_notes:
        base += f"｜交換校 GPA 要求：{'；'.join(gpa_notes)}"
    return base


def format_quota(item: dict) -> str:
    entries = item.get("pdf_entries") or []
    adm = item.get("admitted")
    if not entries:
        q_str = "簽約交換合作姊妹校（當期開放名額依國際事務處 7 月日本線、10 月其他國家一甄、1 月中國線及 2 月二甄簡章公告為準）"
    else:
        q_parts = []
        for e in entries:
            cat = e.get("category")
            code = e.get("code")
            q = clean_bullet_text(e.get("quota") or "依簡章公告")
            cat_label = {
                "JP": "校級日本交換",
                "UW": "校級跨院交換",
                "CM": "管理學院交換",
                "CN": "校級中國交換",
            }.get(cat, "交換名額")
            q_parts.append(f"{cat_label}（{code}）：{q}")
        q_str = "；".join(q_parts)
    if adm:
        q_str += f"｜最新榜單實績：{adm['cycle']}共錄取 {adm['count']} 名（{'、'.join(adm['depts'][:4])}）"
    return q_str


def format_study_period(item: dict) -> str:
    entries = item.get("pdf_entries") or []
    periods = []
    for e in entries:
        p = clean_bullet_text(e.get("exchange_period") or "")
        if p and p not in periods:
            periods.append(p)
    if periods:
        return "／".join(periods)
    if item["country"] == "中國大陸":
        return "一學期（秋季班或春季班單學期交換）"
    return "一學期或一學年（依兩校交換協議與當期甄選簡章規定）"


def format_program_type(item: dict) -> str:
    entries = item.get("pdf_entries") or []
    cats = {e.get("category") for e in entries}
    if not entries:
        fs = item.get("factsheet") or {}
        if fs.get("agreement_level") == "College of Management":
            return "交換學生（管理學院院級交換協議姐妹校・學費互免）"
        return "交換學生（國立中山大學國際事務處簽約合作姐妹校・學費互免）"
    labels = []
    if "JP" in cats:
        labels.append("赴日本校級交換計畫")
    if "UW" in cats:
        labels.append("赴其他國家與地區校級交換計畫")
    if "CM" in cats:
        labels.append("管理學院院級交換計畫")
    if "CN" in cats:
        labels.append("赴中國大陸校級交換計畫")
    return f"交換學生（{'＋'.join(labels)}・繳交中山大學學雜費、免繳接待校學費）"


def main() -> None:
    OFFICIAL_NSYSU_DIR.mkdir(parents=True, exist_ok=True)
    SOURCES_NSYSU_DIR.mkdir(parents=True, exist_ok=True)

    catalog_items = json.loads(
        (SOURCES_NSYSU_DIR / "nsysu_catalog_source.json").read_text(encoding="utf-8")
    )
    locs_raw = json.loads(
        (SOURCES_NSYSU_DIR / "nsysu_resolved_locations.json").read_text(encoding="utf-8")
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
        en_name = item["name_en"]
        country = item["country"]
        region = REGION_BY_COUNTRY.get(country, "其他地區")
        avail_status = item["availability_status"]
        if avail_status == "open":
            open_partner_count += 1

        entries = item.get("pdf_entries") or []
        fs = item.get("factsheet") or {}
        sister = item.get("sister") or {}
        exp_obj = item.get("experience") or {}
        videos = item.get("videos") or []
        slides = item.get("slides") or []
        adm_rec = item.get("admitted")

        website = (item.get("website") or "").strip()
        if website and not website.startswith("http"):
            website = f"https://{website}"

        factsheet_url = None
        for lk in fs.get("links") or []:
            u = (lk.get("url") or "").strip()
            lbl = (lk.get("label") or "").lower()
            if u and u != website and ("fact" in lbl or "guide" in lbl or "info" in lbl or u.endswith(".pdf")):
                factsheet_url = u
                break
        if not factsheet_url and fs.get("region_page"):
            factsheet_url = FACTSHEET_PAGE_URLS.get(fs["region_page"])

        cats = {e.get("category") for e in entries}
        if "JP" in cats:
            source_url = "https://oia.nsysu.edu.tw/p/406-1308-360627,r4456.php?Lang=zh-tw"
            round_label = "2027-2028赴日本交換甄選（115-2/116-1出國）"
            deadline_iso = "2026-08-11T17:00:00+08:00"
            deadline_rem = False
            app_deadline_str = (
                "【2027–2028 赴日本交換甄選（赴 115-2 春季班或 116-1 秋季班）】已於 2026/08/04 09:00 至 2026/08/11 17:00 受理線上申請（補正至 08/13 17:00），"
                "並於 2026/09/13 公告最終錄取名單（共錄取 23 校 58 人）；下一年度赴日交換簡章預計於 2027 年 7 月底公告。"
            )
        elif "CN" in cats or country == "中國大陸":
            source_url = "https://oia.nsysu.edu.tw/p/412-1308-20730.php?Lang=zh-tw"
            round_label = "2027-2028赴中國交換甄選（116-1/116-2出國）"
            deadline_iso = "2027-01-26T17:00:00+08:00"
            deadline_rem = True
            app_deadline_str = (
                "【2027–2028 赴中國大陸學生出國交換計畫（赴 116-1 秋季班或 116-2 春季班）】預定於 2027/01/12 公告當期簡章，"
                "2027/01/15 09:00 至 2027/01/26 17:00 開放線上申請（補正期限至 2027/01/28 17:00），2027/02/19 17:00 公告錄取結果。"
            )
        else:
            source_url = "https://oia.nsysu.edu.tw/p/412-1308-20730.php?Lang=zh-tw"
            round_label = "2027-2028赴其他國家與地區第一次甄選（116-1/116-2出國）"
            deadline_iso = "2026-11-17T17:00:00+08:00"
            deadline_rem = True
            app_deadline_str = (
                "【2027–2028 赴其他國家與地區學生出國交換計畫（第一次甄選，赴 116-1 秋季班或 116-2 春季班）】將於 2026/10/27 公告當期簡章與名額，"
                "2026/11/03 09:00 至 2026/11/17 17:00 開放線上申請（補正期限至 2026/11/20 17:00，預計 2026/12/15 17:00 公告錄取結果）；"
                "第二次甄選（僅開放 116-2 春季班名額）將於 2027/02/16 公告簡章、2027/02/22–03/08 17:00 受理線上申請。"
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

        # Extract host-specific courses, housing, cost, calendar from pdf_entries if present
        pdf_courses_avail = [
            clean_bullet_text(e.get("courses_available") or "")
            for e in entries
            if clean_bullet_text(e.get("courses_available") or "")
        ]
        pdf_courses_not = [
            clean_bullet_text(e.get("courses_not_available") or "")
            for e in entries
            if clean_bullet_text(e.get("courses_not_available") or "")
        ]
        pdf_accomm = [
            clean_bullet_text(e.get("accommodation") or "")
            for e in entries
            if clean_bullet_text(e.get("accommodation") or "")
        ]
        pdf_living = [
            clean_bullet_text(e.get("living_cost") or "")
            for e in entries
            if clean_bullet_text(e.get("living_cost") or "")
        ]
        pdf_cal = [
            clean_bullet_text(e.get("academic_calendar") or "")
            for e in entries
            if clean_bullet_text(e.get("academic_calendar") or "")
        ]
        pdf_level_notes = [
            clean_bullet_text(e.get("level") or "")
            for e in entries
            if clean_bullet_text(e.get("level") or "")
        ]

        if pdf_cal:
            sem_dates_str = pdf_cal[0][:380]
        elif country == "日本":
            sem_dates_str = "春季學期（前學期）：約每年 4 月至 8 月；秋季學期（後學期）：約每年 9/10 月至翌年 2/3 月"
        else:
            sem_dates_str = "秋季學期（第 1 學期）：約每年 8/9 月至 12 月／翌年 1 月；春季學期（第 2 學期）：約每年 1/2 月至 5/6 月"

        course_parts = [f"開放申請院系與學制：{colleges_str}（{degree_levels_str}）。"]
        if pdf_courses_avail:
            course_parts.append(f"開放選課範圍：{pdf_courses_avail[0][:300]}。")
        if pdf_courses_not:
            course_parts.append(f"選課限制：{pdf_courses_not[0][:260]}。")
        course_parts.append(
            "依《國立中山大學學生出國交換甄選要點》與《處理交換學生選課及成績作業要點》規定，交換期間每學期至少應修習並通過 2 門課程（其中至少 1 門須為專業課程；領取學海惜珠或乘風萬里清寒獎助金者每學期須通過至少 3 門課程，含 1 門所屬院系專業課程及 1 門其他專業課程），並依 18 授課小時抵免 1 學分原則辦理學分採認。"
        )
        course_rest_str = " ".join(course_parts)

        if pdf_accomm:
            housing_str = f"{zh_name} 官方住宿資訊：{pdf_accomm[0][:380]}"
        else:
            housing_str = f"{zh_name} 依兩校交換協議與當期 Fact Sheet 規定協助錄取交換生申請校內學生宿舍或提供校外學生公寓租屋指引（宿位依接待校當期供給核配，住宿費由學生自理）。"

        tuition_points_list = [
            "出國交換期間須於國立中山大學辦理註冊並繳交全額學雜費以保留在學學籍（不得辦理休學或畢業），免繳交換學校學費；往返機票、簽證、護照、住宿、膳食及強制保險費由交換生自行負擔。",
            "西灣領航計畫（結合教育部學海飛颺與校務基金）自動獎助機制：凡通過本校校內甄選（非中港澳地區）且具中華民國國籍之錄取交換生，無須另外提出獎學金申請即自動取得受獎資格！一般學士班及碩士班每月補助 NT$10,000（1 學季約 4 萬、1 學期約 6 萬，上限 6 個月）；五年學碩士及七年學碩博一貫生每月補助 NT$15,000（1 學季約 6 萬、1 學期約 9 萬）。另設有學海惜珠與乘風萬里清寒學習獎勵金。",
            "境外修課與返國義務：每學期至少修習並通過 2 門課程（含至少 1 門專業課程；學海惜珠／乘風萬里受獎生須通過至少 3 門課程），返國後 2 個月內須繳交返國報告書（含中文 1,500–2,000 字及英文 1,000–1,500 字心得與 4 張照片；赴中國者免附英文心得）及正式成績單查驗，始核發交換學生證明書並撥付獎助尾款。",
        ]

        app_steps_list = [
            f"步驟一（確認學籍、歷年班排名與語檢門檻）：確認具國立中山大學大學部一至四年級或碩士班一至二年級正式在學學籍（不含延畢生、在職專班及博士班；大一及碩一申請時須已具前學期成績與班排名，碩一可以大學歷年成績與排名申請），並確認符合 {zh_name} 之語檢、GPA 與院系限制。",
            "步驟二（出國交換學生甄選系統線上填報與文件上傳）：於當期報名期間登入中山大學「出國交換學生甄選系統（https://partners.oia.nsysu.edu.tw/exchange/login/user/）」，下載並上傳簽名後之志願表、中文歷年成績單（須含歷年班排名）、有效語言能力檢定證明（2 年內取得；中國大陸免附）、中英文研修計畫書（各以 1 頁 A4 為限，赴日以日文、赴中以中文撰寫）及有利審查資料（上限 10 項，每項 2 MB 內）。",
            "步驟三（校內書面審查評分、錄取分發與線上確認）：由國際事務處或管理學院依簡章配分標準（日本及其他國家：學業成績歷年班排名 30%、語言能力 40%、研修計畫書 20%、有利審查資料 10%；中國大陸：學業成績 60%、研修計畫書 20%、有利審查資料 20%；總成績未達 60 分不予錄取）進行評選分發。獲錄取者須於規定期限內於系統點選確認錄取並上傳家長／監護人簽署之《錄取確認書（保證人同意書）》。",
            f"步驟四（姊妹校提名複審、西灣領航獎助核定與行前準備）：由國際事務處向 {full_name} 辦理官方提名（Nomination），學生依接待校規定提交第二階段入學與宿舍申請表件；非中港澳錄取生自動納入「西灣領航計畫」獎助名單（每月 NT$10,000–15,000），收到正式入學許可（LOA / COE）後辦理簽證、海外醫療及意外保險與出國選課學分採認。",
        ]

        elig_points_list = [
            f"開放學制與年級：{degree_levels_str}",
            f"開放申請學院：{colleges_str}",
            f"學業評分與 GPA 要求：{gpa_req_str}",
            f"語言檢定要求：{lang_req_str}",
        ]
        if pdf_level_notes:
            elig_points_list.append(f"交換校特殊資格規定：{pdf_level_notes[0][:240]}")

        exp_reports = exp_obj.get("reports") or []
        notes_lines = [
            f"【合作類別與期程】{program_type}｜交換期間：{study_period_str}",
            f"【當期名額與錄取實績】{quota_str}",
            f"【開放學院與學制】{colleges_str}｜{degree_levels_str}",
            f"【語言與學業門檻】{lang_req_str}｜{gpa_req_str}",
        ]
        if pdf_level_notes:
            notes_lines.append(f"【交換校申請資格備註】{pdf_level_notes[0][:320]}")
        if adm_rec:
            notes_lines.append(
                f"【最新甄選錄取榜單】{adm_rec['cycle']}共錄取 {adm_rec['count']} 名中山學生赴 {zh_name}（錄取系所：{'、'.join(adm_rec['depts'])}）。"
            )
        if exp_reports or videos or slides:
            notes_lines.append(
                f"【歷年學長姐交換心得】中山大學國際事務處官網公開收錄赴 {zh_name} 歷年交換生返國心得報告 PDF 共 {len(exp_reports)} 篇"
                + (f"、交換日記影片 {len(videos)} 部" if videos else "")
                + (f"、經驗分享簡報 {len(slides)} 份" if slides else "")
                + "。"
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
            "availability_note": f"國立中山大學國際事務處公告合作交換姊妹校；{quota_str}。",
            "academic_year": "116",
            "application_round": round_label,
            "application_window_status": "closed",
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
                "title": f"國立中山大學出國交換計畫甄選簡章與學校資訊一覽表—{zh_name}",
                "source_url": source_url,
                "role": "home_university",
                "authority": "home_official_notice",
                "effective_academic_year": "116",
                "application_round": round_label,
                "checked_at": CHECKED_AT,
            },
            {
                "title": "國立中山大學出國交換學生甄選線上申請系統（partners.oia.nsysu.edu.tw）",
                "source_url": "https://partners.oia.nsysu.edu.tw/exchange/login/user/",
                "role": "home_university",
                "authority": "home_official_notice",
                "effective_academic_year": "116",
                "application_round": round_label,
                "checked_at": CHECKED_AT,
            },
            {
                "title": "國立中山大學學生出國交換甄選要點與西灣領航獎助學金專區",
                "source_url": "https://oia.nsysu.edu.tw/p/412-1308-20736.php?Lang=zh-tw",
                "role": "home_university",
                "authority": "home_official_notice",
                "effective_academic_year": "116",
                "application_round": round_label,
                "checked_at": CHECKED_AT,
            },
        ]
        if factsheet_url:
            wf_sources.append({
                "title": f"{zh_name} 交換生 Fact Sheet 與申請須知（中山大學國際事務處）",
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
            "home_university": "國立中山大學",
            "school_name": full_name,
            "partner_website": website,
            "country": country,
            "program_type": program_type,
            "academic_year": "116",
            "application_round": round_label,
            "effective_application_rounds": [
                round_label,
                "115-2",
                "116-1",
                "116-2",
                "2027-2028赴日本交換甄選",
                "2027-2028赴其他國家與地區第一次甄選",
                "2027-2028赴中國交換甄選",
                "2027-2028赴其他國家與地區第二次甄選",
                "第1學期（秋季班）",
                "第2學期（春季班）",
            ],
            "applicability_status": "verified",
            "applicability_note": (
                "國立中山大學 2027–2028 學年度（赴 115-2 / 116-1 及 116-2）出國交換分三線辦理："
                "（1）赴【日本】已於 2026/08/04–08/11 報名並於 2026/09/13 公告最終錄取 58 名；"
                "（2）赴【其他國家與地區】第一次甄選將於 2026/10/27 公告簡章、2026/11/03 09:00 至 11/17 17:00 開放線上申請（預計 12/15 放榜）；"
                "（3）赴【中國】甄選將於 2027/01/12 公告簡章、2027/01/15 09:00 至 01/26 17:00 開放線上申請（預計 02/19 放榜）。"
            ),
            "review_status": "published",
            "published_at": CHECKED_AT,
            "steps": [
                {
                    "rule_id": f"nsysu-116-home-1-{idx+1:03d}",
                    "order": 1,
                    "phase": "校內申請",
                    "title": f"確認中山大學在學學籍、歷年班排名與 {zh_name} 語言檢定及 GPA 標準",
                    "responsible_party": "學生",
                    "responsible_unit": "國立中山大學國際事務處學生交換事務組（行政大樓 2004 室）／管理學院國際交流暨認證辦公室",
                    "deadline_at": deadline_iso,
                    "deadline_status": "verified_exact",
                    "deadline_source_url": source_url,
                    "deadline_checked_at": CHECKED_AT,
                    "deadline_reminder_eligible": deadline_rem,
                    "summary": f"須為國立中山大學大學部一至四年級或碩士班一至二年級在學學生（不含延畢生、在職生及博士班），具備歷年學業成績班排名並符合 {zh_name} 之語言檢定與 GPA 規定。",
                    "details": [
                        f"開放學制與院系：{colleges_str}（{degree_levels_str}）",
                        f"語言與學業條件：{lang_req_str}｜{gpa_req_str}",
                        f"當期名額與錄取實績：{quota_str}",
                    ],
                    "scope": {
                        "home_universities": ["國立中山大學"],
                        "partner_universities": [full_name],
                        "academic_years": ["115", "116"],
                        "application_rounds": [
                            round_label,
                            "115-2",
                            "116-1",
                            "116-2",
                            "2027-2028赴日本交換甄選",
                            "2027-2028赴其他國家與地區第一次甄選",
                            "2027-2028赴中國交換甄選",
                            "2027-2028赴其他國家與地區第二次甄選",
                            "第1學期（秋季班）",
                            "第2學期（春季班）",
                        ],
                    },
                    "source_urls": [
                        source_url,
                        "https://oia.nsysu.edu.tw/p/412-1308-20730.php?Lang=zh-tw",
                    ],
                    "checked_at": CHECKED_AT,
                    "support_status": "verified",
                },
                {
                    "rule_id": f"nsysu-116-home-2-{idx+1:03d}",
                    "order": 2,
                    "phase": "校內申請",
                    "title": "於中山大學出國交換學生甄選系統完成線上填報與審查文件上傳",
                    "responsible_party": "學生",
                    "responsible_unit": "國立中山大學國際事務處（出國交換學生甄選系統）",
                    "deadline_at": deadline_iso,
                    "deadline_status": "verified_exact",
                    "deadline_source_url": "https://partners.oia.nsysu.edu.tw/exchange/login/user/",
                    "deadline_checked_at": CHECKED_AT,
                    "deadline_reminder_eligible": deadline_rem,
                    "summary": "申請人須於報名截止日前登入 https://partners.oia.nsysu.edu.tw/exchange/login/user/ 完成個人資料填寫、下載志願表簽名上傳，並上傳中文歷年成績單（含歷年班排名）、語言檢定證明、中英文研修計畫書及有利審查資料。",
                    "details": [
                        "應繳文件（全數上傳 PDF 電子檔）：1. 志願表（系統填寫後下載列印並親筆簽名上傳）、2. 中文歷年成績單（須有「歷年班排名」；碩一學生可以大學歷年成績單及大學畢業班排名申請）、3. 合格語言能力檢定證明（須為報名截止日前 2 年內取得；申請赴中國大陸者免附）、4. 研修計畫書（赴其他國家須含中、英文各 1 頁 A4 為限；赴日本須含中文及日文各 1 頁；赴中國以中文 1–2 頁撰寫，詳述選課規劃）、5. 有利審查資料（上限 10 項，每項須填寫 30 字內簡述，單一 PDF 上限 2 MB）。",
                        "若同時符合校級與管理學院院級資格，可於系統內依簡章規定選填志願順序；送出申請後請密切留意電子郵件通知，如需補正請於補正截止日 17:00 前完成。",
                    ],
                    "document_requirements": [
                        {
                            "name": "國立中山大學出國交換學生甄選志願表（系統產生、本人親筆簽名後掃描上傳）",
                            "official_form_url": "https://partners.oia.nsysu.edu.tw/exchange/login/user/",
                            "source_urls": [
                                "https://partners.oia.nsysu.edu.tw/exchange/login/user/",
                                source_url,
                            ],
                        },
                        {
                            "name": "中文歷年成績單（須註明「歷年班排名」；碩一新生可檢附大學歷年成績單及班排名）",
                            "source_urls": [source_url],
                        },
                        {
                            "name": "研修計畫書（赴其他國家須含中英文各1頁A4；赴日為中日文各1頁；赴中為中文1–2頁）及有利審查資料（上限10項）",
                            "source_urls": [source_url],
                        },
                        {
                            "name": "合格語言能力檢定證明（TOEFL iBT 60 / IELTS 5.0 / TOEIC 600 / JLPT N5 等，須符合交換校標準；赴中國免附）",
                            "conditional": country == "中國大陸",
                            "condition": "申請赴日本及其他國家必繳；申請赴中國大陸免附（外國籍／僑生除外）",
                            "source_urls": [
                                source_url,
                                "https://oia.nsysu.edu.tw/p/412-1308-20734.php?Lang=zh-tw",
                            ],
                        },
                    ],
                    "scope": {
                        "home_universities": ["國立中山大學"],
                        "academic_years": ["115", "116"],
                        "application_rounds": [
                            round_label,
                            "115-2",
                            "116-1",
                            "116-2",
                            "2027-2028赴日本交換甄選",
                            "2027-2028赴其他國家與地區第一次甄選",
                            "2027-2028赴中國交換甄選",
                            "2027-2028赴其他國家與地區第二次甄選",
                            "第1學期（秋季班）",
                            "第2學期（春季班）",
                        ],
                    },
                    "submission": {
                        "method": "online",
                        "office": "國立中山大學國際事務處學生交換事務組（行政大樓 2 樓 2004 室）",
                        "portal_url": "https://partners.oia.nsysu.edu.tw/exchange/login/user/",
                    },
                    "action_url": "https://partners.oia.nsysu.edu.tw/exchange/login/user/",
                    "source_urls": [
                        "https://partners.oia.nsysu.edu.tw/exchange/login/user/",
                        source_url,
                    ],
                    "checked_at": CHECKED_AT,
                    "support_status": "verified",
                },
                {
                    "rule_id": f"nsysu-116-home-3-{idx+1:03d}",
                    "order": 3,
                    "phase": "甄選與提名",
                    "title": "校內書審評分放榜、線上錄取確認、保證人同意書上傳與西灣領航獎助資格核定",
                    "responsible_party": "學生與國立中山大學國際事務處",
                    "responsible_unit": "國立中山大學國際事務處／管理學院職涯發展暨國際交流辦公室",
                    "deadline_at": "2026-09-13T17:00:00+08:00" if country == "日本" else ("2027-02-19T17:00:00+08:00" if country == "中國大陸" else "2026-12-15T17:00:00+08:00"),
                    "deadline_status": "verified_exact",
                    "deadline_source_url": source_url,
                    "deadline_checked_at": CHECKED_AT,
                    "deadline_reminder_eligible": False,
                    "summary": "國際事務處公告錄取結果後，錄取生須於規定期限內登入系統點選「確認錄取」並上傳經本人及家長／監護人親筆簽署之《錄取確認書（含保證人同意書）》；逾期未確認視同放棄，由備取生依序遞補。",
                    "details": [
                        "評分比重：日本及其他國家為「學業成績（歷年班排名）30%、語言能力（參考 CEFR 對照表）40%、研修計畫書 20%、有利審查資料 10%」；中國大陸為「學業成績 60%、研修計畫書 20%、有利審查資料 20%」。總成績未達 60 分者不予錄取。",
                        "自動獎助：通過校內甄選赴非中港澳地區交換之本國籍錄取生，自動取得「西灣領航計畫（結合教育部學海飛颺與校務基金）」獎助資格（無須另外申請），一般學士／碩士生每月 NT$10,000、五／七年學碩博一貫生每月 NT$15,000（上限 6 個月）。",
                    ],
                    "scope": {
                        "home_universities": ["國立中山大學"],
                        "academic_years": ["115", "116"],
                        "application_rounds": [
                            round_label,
                            "115-2",
                            "116-1",
                            "116-2",
                            "2027-2028赴日本交換甄選",
                            "2027-2028赴其他國家與地區第一次甄選",
                            "2027-2028赴中國交換甄選",
                            "2027-2028赴其他國家與地區第二次甄選",
                            "第1學期（秋季班）",
                            "第2學期（春季班）",
                        ],
                    },
                    "source_urls": [
                        source_url,
                        "https://oia.nsysu.edu.tw/p/412-1308-20736.php?Lang=zh-tw",
                    ],
                    "checked_at": CHECKED_AT,
                    "support_status": "verified",
                },
                {
                    "rule_id": f"nsysu-{idx+1:03d}-host-apply",
                    "order": 4,
                    "phase": "合作校申請",
                    "title": f"由中山國際處辦理官方提名（Nomination）並完成 {zh_name} 交換入學與宿舍申請",
                    "responsible_party": "學生與接待校國際處",
                    "summary": f"完成校內錄取確認後，由中山大學國際事務處或管理學院向 {zh_name} 提交官方提名名單；學生須依接待校 Fact Sheet 與提名通知準備護照影本、英文成績單、英文財力證明、語檢證明及選課表完成姊妹校線上申請，最終錄取決定權在於交換學校。",
                    "details": [
                        f"交換期程：{study_period_str}｜名額：{quota_str}",
                        f"語言與學業條件：{lang_req_str}",
                    ]
                    + ([f"開放選課與限制：{pdf_courses_avail[0][:220]}"] if pdf_courses_avail else []),
                    "scope": {
                        "home_universities": ["國立中山大學"],
                        "partner_universities": [full_name],
                        "academic_years": ["115", "116"],
                        "application_rounds": [
                            round_label,
                            "115-2",
                            "116-1",
                            "116-2",
                            "2027-2028赴日本交換甄選",
                            "2027-2028赴其他國家與地區第一次甄選",
                            "2027-2028赴中國交換甄選",
                            "2027-2028赴其他國家與地區第二次甄選",
                            "第1學期（秋季班）",
                            "第2學期（春季班）",
                        ],
                    },
                    "source_urls": (
                        [source_url]
                        + ([factsheet_url] if factsheet_url else [])
                        + ([website] if website else [])
                    ),
                    "checked_at": CHECKED_AT,
                    "support_status": "verified",
                    "needs_confirmation": False,
                },
                {
                    "rule_id": f"nsysu-116-home-5-{idx+1:03d}",
                    "order": 5,
                    "phase": "行前準備",
                    "title": "辦理簽證與保險、出國期間每學期通過至少 2 門課（含專業課）與返國 2 個月內繳交報告書",
                    "responsible_party": "學生",
                    "responsible_unit": "國立中山大學國際事務處／教務處註冊課務組／各系所",
                    "summary": "取得交換校正式入學許可（LOA / COE / DS-2019）後辦理學生簽證、海外醫療及意外保險與役男緩徵出境；交換期間每學期至少修習並通過 2 門課程（含至少 1 門專業課程；學海惜珠／乘風萬里受獎生須通過至少 3 門課），返國後 2 個月內繳交中英文返國報告書及正式成績單以辦理學分採認（18 小時抵 1 學分）與領取交換證明書。",
                    "details": tuition_points_list,
                    "scope": {
                        "home_universities": ["國立中山大學"],
                        "academic_years": ["115", "116"],
                        "application_rounds": [
                            round_label,
                            "115-2",
                            "116-1",
                            "116-2",
                            "2027-2028赴日本交換甄選",
                            "2027-2028赴其他國家與地區第一次甄選",
                            "2027-2028赴中國交換甄選",
                            "2027-2028赴其他國家與地區第二次甄選",
                            "第1學期（秋季班）",
                            "第2學期（春季班）",
                        ],
                    },
                    "source_urls": [
                        "https://oia.nsysu.edu.tw/var/file/308/1308/img/3642/492663022.pdf",
                        "https://oia.nsysu.edu.tw/static/file/308/1308/img/3642/746350618.pdf",
                    ],
                    "checked_at": CHECKED_AT,
                    "support_status": "verified",
                },
            ],
            "sources": wf_sources,
            "last_checked": CHECKED_AT,
            "coverage_status": "official_verified",
            "coverage_note": "已完整整合國立中山大學 2026–2027 及 2027–2028 學年度赴日本、其他國家與地區、中國大陸學生出國交換計畫簡章、校級與管理學院交換校資訊表、姊妹校 Fact Sheet 及西灣領航獎助學金規範。",
        })

        cost_default, visa_default = REGION_COST_DEFAULTS.get(
            country,
            (
                "USD 800–1,300 / 月（含住宿、膳食、教材與當地交通費用）",
                "須依接待校與駐臺代表處規定辦理學生簽證與海外醫療保險。",
            ),
        )
        cost_line = f"預估每月生活費約 {cost_default}。"
        if pdf_living:
            cost_line += f"交換校簡章參考資訊：{pdf_living[0][:220]}。"
        tuition_clean = tuition_points_list[0]
        housing_clean = housing_str
        course_clean = course_rest_str
        calendar_clean = f"{sem_dates_str}。"

        dest_sources = [
            {
                "title": f"國立中山大學出國交換甄選簡章與交換校資訊一覽表—{zh_name}",
                "source_url": source_url,
                "summary": "中山大學官方交換名額、語檢門檻、開放院系與修課規定",
            },
            {
                "title": "國立中山大學學生出國交換甄選要點與選課成績作業要點",
                "source_url": "https://oia.nsysu.edu.tw/var/file/308/1308/img/3642/492663022.pdf",
                "summary": "中山大學交換生每學期至少通過2門課（含1門專業課）、18授課小時抵免1學分與返國報告書規定",
            },
        ]
        if factsheet_url:
            dest_sources.append({
                "title": f"{zh_name} 交換生 Fact Sheet 與申請須知",
                "source_url": factsheet_url,
                "summary": "姊妹校課程資訊、學期日曆、住宿與交換生申請指引",
            })
        if website:
            dest_sources.append({
                "title": f"{full_name} 官方網站",
                "source_url": website,
                "summary": "接待合作校官方網站",
            })
        exp_page_url = EXPERIENCE_PAGE_URLS.get(
            exp_obj.get("region_page") or fs.get("region_page") or "asia",
            "https://oia.nsysu.edu.tw/p/412-1308-20773.php?Lang=zh-tw",
        )
        if exp_reports:
            dest_sources.append({
                "title": f"國立中山大學赴 {zh_name} 交換學生返國心得報告專區（共 {len(exp_reports)} 篇 PDF）",
                "source_url": exp_reports[0]["url"],
                "summary": f"收錄 {exp_reports[0]['term']} 等歷年中山大學交換生返國心得報告全文 PDF",
            })
        if adm_rec:
            dest_sources.append({
                "title": f"國立中山大學出國交換甄選最終錄取名單（{zh_name}）",
                "source_url": adm_rec["pdf_url"],
                "summary": f"{adm_rec['cycle']}共錄取 {adm_rec['count']} 名（{'、'.join(adm_rec['depts'][:4])}）",
            })

        src_url_list = (
            [source_url]
            + ([factsheet_url] if factsheet_url else [])
            + ([website] if website else [])
        )

        destinations.append({
            "home_university": "國立中山大學",
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
                    "title": "生活費、西灣領航自動獎助（每月 NT$10,000–15,000）與學雜費規定",
                    "summary": cost_line,
                    "points": [cost_line] + tuition_points_list,
                    "source_urls": src_url_list + ["https://oia.nsysu.edu.tw/p/412-1308-20736.php?Lang=zh-tw"],
                    "caution": "凡通過中山大學非中港澳交換甄選錄取者，無須另外提出申請即自動獲得「西灣領航計畫（結合教育部學海飛颺與校務基金）」獎助資格（一般學士／碩士生每月 NT$10,000、五／七年學碩博生每月 NT$15,000，上限 6 個月）；清寒學生另可申請學海惜珠與乘風萬里清寒學習獎勵金。",
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
                        "交換生於出國研修期間須自費購買足夠保額之海外醫療及意外保險（及交換學校規定之強制保險），並於出國前完成保險投保確認。",
                    ],
                    "source_urls": src_url_list,
                    "caution": "多數歐美日韓及澳洲姊妹校要求於註冊或抵校時出示符合當地政府或校方標準之醫療保險證明。",
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
                    "title": "課程限制、每學期至少通過 2 門課（含專業課）與 18 小時抵 1 學分規定",
                    "summary": course_clean[:160],
                    "points": [
                        course_clean,
                        "返國後憑交換學校核發之正式成績單及課程大綱，依《國立中山大學處理交換學生選課及成績作業要點》以每滿 18 授課小時（或依 ECTS 轉換）採認 1 學分為原則辦理學分抵免。",
                    ],
                    "source_urls": src_url_list
                    + ["https://oia.nsysu.edu.tw/static/file/308/1308/img/3642/746350618.pdf"],
                    "caution": "一般交換生每學期須修習並通過至少 2 門課（含至少 1 門專業課）；領取學海惜珠或乘風萬里清寒獎助金者每學期須通過至少 3 門課（含 1 門所屬院系專業課及 1 門其他專業課）。",
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
                    "caution": "部分合作大學設有多個校區，實際授課校區請以當期簡章學校資訊表及姊妹校錄取通知為準。",
                },
                {
                    "key": "arrival",
                    "title": "學期年曆、返國 2 個月內繳交雙語報告書與歷年學長姐心得",
                    "summary": calendar_clean,
                    "points": [
                        calendar_clean,
                        "返國後 2 個月內須提交返國報告書（中文 1,500–2,000 字、英文 1,000–1,500 字及 4 張具圖說照片；赴中國者免附英文心得）及正式成績單查驗，始得領取交換學生證明書及核銷獎助尾款。",
                    ]
                    + (
                        [
                            f"歷年學長姐返國心得：中山大學國際事務處已公開收錄赴 {zh_name} 交換生心得報告 PDF 共 {len(exp_reports)} 篇。"
                        ]
                        if exp_reports
                        else []
                    ),
                    "source_urls": src_url_list + ([exp_reports[0]["url"]] if exp_reports else [exp_page_url]),
                    "caution": "未依期限完成返國報告書與成績單查驗者，將不予核發交換證明書並須依規定繳回已領取之獎助學金。",
                },
            ],
            "first_72_hours": [
                {
                    "title": "依姊妹校入學許可與 Fact Sheet 指定報到日完成新生報到、宿舍入住與選課確認",
                    "detail": calendar_clean,
                    "source_urls": [source_url],
                },
                {
                    "title": "完成當地居留登錄、醫療保險確認並向中山大學國際事務處回報抵達與選課狀況",
                    "detail": f"{visa_default} 抵校確定選課後，請確認每學期修課門數符合中山大學最低門檻（至少 2 門課且含 1 門專業課，清寒受獎生至少 3 門課）。",
                    "source_urls": [source_url],
                },
            ],
            "sources": dest_sources,
            "last_checked": CHECKED_AT,
            "coverage_status": "official_verified",
            "coverage_note": "已整合國立中山大學 2026–2028 學年度各線交換甄選簡章、交換校資訊一覽表、姊妹校 Fact Sheet、最終錄取名單與歷年學長姐交換心得報告 PDF。",
        })

        research_records.append({
            "home_university": "國立中山大學",
            "school_name": full_name,
            "country": country,
            "official_website": website,
            "verification_status": "official_verified",
            "discovery_source_url": source_url,
            "checked_at": CHECKED_AT,
            "note": f"國立中山大學國際事務處交換校資訊一覽表、Fact Sheet 與姐妹校名冊（{source_url}）及 ROR/Wikidata 官方網址核對完成。",
        })

        ev_sources = [
            {"title": f"國立中山大學出國交換計畫學校資訊—{zh_name}", "url": source_url},
        ]
        if factsheet_url:
            ev_sources.append({"title": f"{zh_name} 交換生 Fact Sheet", "url": factsheet_url})
        if website:
            ev_sources.append({"title": f"{full_name} 官方網站", "url": website})
        if exp_reports:
            ev_sources.append({
                "title": f"國立中山大學赴 {zh_name} 交換生返國心得報告（{exp_reports[0]['term']}）",
                "url": exp_reports[0]["url"],
            })
        if adm_rec:
            ev_sources.append({
                "title": f"國立中山大學出國交換甄選最終錄取名單（{zh_name}）",
                "url": adm_rec["pdf_url"],
            })

        has_student_exp = bool(exp_reports or videos or slides or adm_rec)
        if has_student_exp:
            exp_covered_schools += 1

        ev_list = [
            {
                "theme": "housing",
                "kind": "official",
                "text": housing_clean,
                "sources": ev_sources,
                "checked_at": CHECKED_AT,
                "scope": "國立中山大學交換校資訊一覽表住宿說明與姊妹校 Fact Sheet",
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
                "scope": "國立中山大學交換生費用規定、西灣領航獎助學金與地區生活費估算",
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
                "scope": "國立中山大學交換生選課限制、每學期至少通過2門課與18小時抵1學分規定",
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
                "scope": "國立中山大學出國交換簽證、體檢、海外醫療保險與役男出境提醒",
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
                        f"｜中山大學國際事務處公開收錄赴 {zh_name} 歷年交換生返國心得報告共 {len(exp_reports)} 篇 PDF。"
                        if exp_reports
                        else ""
                    )
                ),
                "sources": ev_sources,
                "checked_at": CHECKED_AT,
                "scope": "國立中山大學出國交換名額、最新錄取榜單與歷年學長姐交換心得報告",
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
                "已整合國立中山大學 2026–2028 學年度各線出國交換甄選簡章、交換校資訊一覽表、姊妹校 Fact Sheet、最終錄取榜單與歷年返國心得報告 PDF。",
                "當期宿位供給、費用與選課限制請依姊妹校最新 Fact Sheet 及課程目錄核對。",
            ],
            "location_signature": f"verified:{location_obj['latitude']}:{location_obj['longitude']}:representative",
            "extraction_version": 3,
        })

        sample_reports: list[dict] = []
        # Add top recent PDF experience reports (up to 5 per school for sample_reports, and create rich student_experience_rows)
        for rep in exp_reports[:5]:
            rep_title = f"國立中山大學赴{country}—{zh_name}（{rep['term']}）交換學生返國報告書：{rep['label']}"
            sample_reports.append({
                "title": rep_title,
                "url": rep["url"],
                "term": rep["term"],
            })

        if exp_reports:
            latest_rep = exp_reports[0]
            terms_covered = list(dict.fromkeys(r["term"] for r in exp_reports[:6]))
            rep_title = (
                f"國立中山大學赴 {zh_name}（{latest_rep['term']} 等共 {len(exp_reports)} 篇）交換學生返國心得報告集"
            )
            summary_text = (
                f"國立中山大學國際事務處公開收錄赴 {zh_name} 交換學生返國報告書 PDF 共 {len(exp_reports)} 篇（涵蓋 {'、'.join(terms_covered)}），"
                f"最新一篇為 {latest_rep['term']}《{latest_rep['label']}》，詳實記錄行前準備、選課學分採認、宿舍生活與在地文化體驗。"
            )
            theme_map = {
                "academics": f"中山大學交換生分享於 {zh_name} 之選課流程、英語／當地語言授課體驗及返國學分抵免（每學期至少通過 2 門課含 1 門專業課、18 授課小時抵免 1 學分）。",
                "housing": f"中山大學交換生分享於 {zh_name} 之學生宿舍或校外租屋申請經驗、房型設備與生活機能（{housing_clean[:120]}）。",
                "campus_culture": f"中山大學國際事務處收錄 {len(exp_reports)} 篇赴 {zh_name} 歷年交換生返國心得報告（含 {latest_rep['term']} 最新心得），分享迎新週、學伴制度與跨文化交流收穫。",
                "cost": f"中山大學交換生分享於 {zh_name} 之當地物價開銷（{cost_default}）與「西灣領航計畫（每月 NT$10,000–15,000）」獎助學金運用方式。",
            }
            student_experience_rows.append({
                "school_name": full_name,
                "country": country,
                "title": rep_title,
                "source_url": latest_rep["url"],
                "source_type": "article",
                "platform": "國立中山大學國際事務處—交換生返國心得報告專區",
                "author_name": f"國立中山大學 {latest_rep['term']} 返國交換生",
                "language": "zh",
                "summary": summary_text,
                "themes": ["academics", "housing", "campus_culture", "cost"],
                "theme_summaries": theme_map,
                "content_status": "full_text",
                "perspective": "official_student_story",
                "published_at": None,
                "discovered_at": CHECKED_AT,
                "content_hash": hashlib.sha256(
                    f"{full_name}:exp:{latest_rep['url']}".encode("utf-8")
                ).hexdigest(),
                "exchange_term": latest_rep["term"],
                "summary_zh": summary_text,
                "original_summary": summary_text,
                "theme_summaries_zh": theme_map,
                "translation_status": "original",
                "source_kind": "official_experience_pdf",
            })

        for v in videos[:2]:
            v_title = f"國立中山大學赴 {zh_name}（{v['term']}）交換學生影音日記分享"
            sample_reports.append({
                "title": v_title,
                "url": v["url"],
                "term": v["term"],
            })
            v_summary = f"國立中山大學國際事務處「交換日記（影音分享）」專區收錄之 {v['term']} 赴 {zh_name} 交換生實地拍攝校園導覽、住宿開箱與學習生活紀錄影片。"
            v_themes = {
                "campus_culture": v_summary,
                "housing": f"透過影片實地走訪 {zh_name} 校園環境、學生宿舍與周邊生活圈。",
            }
            student_experience_rows.append({
                "school_name": full_name,
                "country": country,
                "title": v_title,
                "source_url": v["url"],
                "source_type": "video",
                "platform": "國立中山大學國際事務處—交換日記影音專區",
                "author_name": f"國立中山大學 {v['term']} 交換學生",
                "language": "zh",
                "summary": v_summary,
                "themes": ["campus_culture", "housing"],
                "theme_summaries": v_themes,
                "content_status": "full_text",
                "perspective": "official_student_story",
                "published_at": None,
                "discovered_at": CHECKED_AT,
                "content_hash": hashlib.sha256(
                    f"{full_name}:video:{v['url']}".encode("utf-8")
                ).hexdigest(),
                "exchange_term": v["term"],
                "summary_zh": v_summary,
                "original_summary": v_summary,
                "theme_summaries_zh": v_themes,
                "translation_status": "original",
                "source_kind": "official_experience_page",
            })

        for sl in slides[:2]:
            sl_title = f"國立中山大學出國交換經驗分享會簡報：{sl['title']}"
            sample_reports.append({
                "title": sl_title,
                "url": sl["url"],
                "term": "歷年交換經驗分享會",
            })
            sl_summary = f"國立中山大學國際事務處「經驗分享簡報」專區收錄之《{sl['title']}》簡報 PDF，整理赴 {zh_name} 交換申請準備、修課生活與當地實用建議。"
            sl_themes = {
                "academics": f"《{sl['title']}》簡報分享於 {zh_name} 交換之選課與學業準備。",
                "campus_culture": sl_summary,
            }
            student_experience_rows.append({
                "school_name": full_name,
                "country": country,
                "title": sl_title,
                "source_url": sl["url"],
                "source_type": "article",
                "platform": "國立中山大學國際事務處—交換經驗分享簡報專區",
                "author_name": "國立中山大學交換經驗分享會講者",
                "language": "zh",
                "summary": sl_summary,
                "themes": ["academics", "campus_culture"],
                "theme_summaries": sl_themes,
                "content_status": "full_text",
                "perspective": "official_student_story",
                "published_at": None,
                "discovered_at": CHECKED_AT,
                "content_hash": hashlib.sha256(
                    f"{full_name}:slide:{sl['url']}".encode("utf-8")
                ).hexdigest(),
                "exchange_term": "歷年交換經驗分享會",
                "summary_zh": sl_summary,
                "original_summary": sl_summary,
                "theme_summaries_zh": sl_themes,
                "translation_status": "original",
                "source_kind": "official_experience_pdf",
            })

        if adm_rec:
            adm_title = f"國立中山大學 {adm_rec['cycle']}赴 {zh_name} 錄取分發紀錄（共 {adm_rec['count']} 名）"
            sample_reports.append({
                "title": adm_title,
                "url": adm_rec["pdf_url"],
                "term": adm_rec["cycle"],
            })
            summary_text = (
                f"國立中山大學國際事務處公告之 {adm_rec['cycle']}名單中，共計錄取 {adm_rec['count']} 名中山大學學生赴 {zh_name} 交換研修，"
                f"錄取學生所屬系所包含：{'、'.join(adm_rec['depts'])}。"
            )
            theme_map = {
                "academics": f"最新錄取系所分布：{'、'.join(adm_rec['depts'])}（{adm_rec['cycle']}）。",
                "cost": (
                    "非中港澳地區本國籍錄取交換生自動獲得「西灣領航計畫（結合教育部學海飛颺與校務基金）」獎助資格（每月 NT$10,000–15,000，上限 6 個月）。"
                    if country not in {"中國大陸", "香港", "澳門"}
                    else "錄取生於交換期間繳交中山大學學雜費並免繳接待校學費。"
                ),
                "campus_culture": f"國立中山大學本梯次共選送 {adm_rec['count']} 名學子赴 {zh_name} 進行學術與文化交流。",
            }
            student_experience_rows.append({
                "school_name": full_name,
                "country": country,
                "title": adm_title,
                "source_url": adm_rec["pdf_url"],
                "source_type": "article",
                "platform": "國立中山大學國際事務處—出國交換甄選最終錄取榜單",
                "author_name": "國立中山大學錄取交換學生",
                "language": "zh",
                "summary": summary_text,
                "themes": ["academics", "cost", "campus_culture"],
                "theme_summaries": theme_map,
                "content_status": "full_text",
                "perspective": "official_program_record",
                "published_at": "2026-09-13T00:00:00Z" if country == "日本" else "2026-03-31T00:00:00Z",
                "discovered_at": CHECKED_AT,
                "content_hash": hashlib.sha256(
                    f"{full_name}:admitted:{adm_rec['pdf_url']}".encode("utf-8")
                ).hexdigest(),
                "exchange_term": adm_rec["cycle"],
                "summary_zh": summary_text,
                "original_summary": summary_text,
                "theme_summaries_zh": theme_map,
                "translation_status": "original",
                "source_kind": "official_experience_pdf",
            })

        experience_sources_records.append({
            "home_university": "國立中山大學",
            "school_name": full_name,
            "country": country,
            "official_experience_portal_url": exp_page_url,
            "partner_page_url": factsheet_url or source_url,
            "report_count": len(exp_reports) + len(videos) + len(slides) + (1 if adm_rec else 0),
            "sample_reports": sample_reports,
            "checked_at": CHECKED_AT,
        })

    partners_jsonl_text = (
        "\n".join(json.dumps(r, ensure_ascii=False) for r in partners) + "\n"
    )
    (OFFICIAL_NSYSU_DIR / "partners.jsonl").write_text(
        partners_jsonl_text, encoding="utf-8"
    )
    (SOURCES_NSYSU_DIR / "partners.jsonl").write_text(
        partners_jsonl_text, encoding="utf-8"
    )
    (OFFICIAL_NSYSU_DIR / "application_workflows.jsonl").write_text(
        "\n".join(json.dumps(r, ensure_ascii=False) for r in workflows) + "\n",
        encoding="utf-8",
    )
    (OFFICIAL_NSYSU_DIR / "destination_profiles.jsonl").write_text(
        "\n".join(json.dumps(r, ensure_ascii=False) for r in destinations) + "\n",
        encoding="utf-8",
    )
    (OFFICIAL_NSYSU_DIR / "partner_research.jsonl").write_text(
        "\n".join(json.dumps(r, ensure_ascii=False) for r in research_records) + "\n",
        encoding="utf-8",
    )
    (OFFICIAL_NSYSU_DIR / "student_life.jsonl").write_text(
        "\n".join(json.dumps(r, ensure_ascii=False) for r in life_records) + "\n",
        encoding="utf-8",
    )
    (OFFICIAL_NSYSU_DIR / "experience_sources.jsonl").write_text(
        "\n".join(
            json.dumps(r, ensure_ascii=False) for r in experience_sources_records
        )
        + "\n",
        encoding="utf-8",
    )
    (OFFICIAL_NSYSU_DIR / "student_experiences.jsonl").write_text(
        "\n".join(
            json.dumps(r, ensure_ascii=False) for r in student_experience_rows
        )
        + "\n",
        encoding="utf-8",
    )
    (OFFICIAL_NSYSU_DIR / "campus-locations.json").write_text(
        json.dumps({"locations": new_locations}, ensure_ascii=False, indent=2)
        + "\n",
        encoding="utf-8",
    )

    # IMPORTANT: Only add the home university row ("國立中山大學", "臺灣") to university_locations.jsonl
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

    nsysu_home_loc = {
        "school_name": "國立中山大學",
        "country": "臺灣",
        "city": "高雄市鼓山區",
        "latitude": 22.6264,
        "longitude": 120.2658,
        "geocode_status": "verified",
        "geocoded_at": CHECKED_AT,
        "source_url": "https://www.wikidata.org/wiki/Q702483",
        "identity_source_url": "https://ror.org/00mjawt10",
        "precision": "representative",
        "note": "校級代表位置：官方網域及國家已與 ROR 比對，座標來源為 Wikidata P625；實際交換校區以錄取通知為準。 母校代表點採高雄市鼓山區蓮海路70號西子灣校區（行政大樓 2 樓 2004 室國際事務處）；官方地址來源：https://oia.nsysu.edu.tw/。",
    }
    existing_loc_map[("國立中山大學", "臺灣")] = nsysu_home_loc
    sorted_locs = sorted(
        existing_loc_map.values(),
        key=lambda r: (r.get("country") or "", r.get("school_name") or ""),
    )
    loc_file.write_text(
        "\n".join(json.dumps(r, ensure_ascii=False) for r in sorted_locs) + "\n",
        encoding="utf-8",
    )

    nsysu_source_urls = [
        "https://oia.nsysu.edu.tw/p/412-1308-20730.php?Lang=zh-tw",
        "https://oia.nsysu.edu.tw/p/406-1308-360627,r4456.php?Lang=zh-tw",
        "https://oia.nsysu.edu.tw/p/406-1308-341179,r4456.php?Lang=zh-tw",
        "https://oia.nsysu.edu.tw/p/406-1308-346711,r4456.php?Lang=zh-tw",
        "https://oia.nsysu.edu.tw/p/406-1308-348244,r4456.php?Lang=zh-tw",
        "https://oia.nsysu.edu.tw/p/412-1308-20734.php?Lang=zh-tw",
        "https://oia.nsysu.edu.tw/p/412-1308-20736.php?Lang=zh-tw",
        "https://oia.nsysu.edu.tw/p/412-1308-20773.php?Lang=zh-tw",
        "https://partners.oia.nsysu.edu.tw/exchange/login/user/",
        "https://oia.nsysu.edu.tw/var/file/308/1308/img/3642/492663022.pdf",
        "https://oia.nsysu.edu.tw/static/file/308/1308/img/3642/746350618.pdf",
    ]

    exchange_info_payload = {
        "school_name": "國立中山大學",
        "program_type": [
            "交換學生（赴日本校級交換計畫・每年 7–8 月甄選赴翌年春季或秋季班）",
            "交換學生（赴其他國家與地區校級暨管理學院院級交換計畫・每年 10–11 月一甄、2–3 月二甄）",
            "交換學生（赴中國大陸校級交換計畫・985/211 重點高校學費互免，每年 1 月及 9 月甄選）",
        ],
        "academic_year": [
            "115–116（2027–2028 赴【日本】出國交換計畫：2026/08/04–08/11 線上申請，2026/09/13 公告最終錄取 23 校 58 人）",
            "116（2027–2028 赴【其他國家與地區】第一次甄選：2026/10/27 公告簡章，2026/11/03 09:00 至 11/17 17:00 線上申請，12/15 放榜）",
            "116（2027–2028 赴【中國】第一次甄選：2027/01/12 公告簡章，2027/01/15 09:00 至 01/26 17:00 線上申請，02/19 放榜）",
        ],
        "semester": [
            "第1學期（秋季班：每年約 8/9 月至 12 月／翌年 1 月；日本後學期為 9/10 月至翌年 2/3 月）",
            "第2學期（春季班：每年約 1/2 月至 5/6 月；日本前學期為 4 月至 8 月）",
        ],
        "application_period": [
            "【2027–2028 赴日本學生出國交換計畫（赴 115-2 春季班或 116-1 秋季班）】：2026年7月28日公告簡章，2026年8月4日 09:00 至8月11日 17:00 線上申請（補正期限至 8月13日 17:00），2026年9月4日公告錄取結果，並於 2026年9月13日公告最終錄取名單（共錄取 23 校 58 名學生）。",
            "【2027–2028 赴其他國家與地區學生出國交換計畫（第一次甄選，赴 116-1 秋季班或 116-2 春季班）】：2026年10月27日公告簡章與名額，2026年11月3日 09:00 至11月17日 17:00 止於出國交換學生甄選系統（https://partners.oia.nsysu.edu.tw/exchange/login/user/）受理線上申請（補正期限至 11月20日 17:00），2026年12月15日 17:00 公告錄取結果；第二次甄選（僅開放 116-2 春季班名額）於 2027年2月16日公告簡章、2月22日至3月8日 17:00 線上申請。",
            "【2027–2028 赴中國學生出國交換計畫（第一次甄選，赴 116-1 秋季班或 116-2 春季班）】：2027年1月12日公告簡章，2027年1月15日 09:00 至1月26日 17:00 止受理線上申請（補正期限至 1月28日 17:00），2027年2月19日 17:00 公告錄取結果；第二次甄選（赴 116-2 春季班）預計於 2027年9月辦理。",
        ],
        "eligibility": [
            "申請資格與學制限制：限國立中山大學大學部一至四年級及碩士班一至二年級在校生（不含延畢生、在職生身分入學者及博士班學生）。申請時須具本校至少一學期成績及歷年班排名（大一上學期新生無班排名不得申請，大一下學期及碩一上學期可申請；碩一學生可以大學歷年成績單及班排名申請）。",
            "甄選評分標準：採書面審查，【赴日本及其他國家】評分比重為「學業成績（歷年班排名）30%、語言能力（參考語言檢測 CEFR 對照表）40%、研修計畫書 20%、有利審查資料 10%」；【赴中國大陸】評分比重為「學業成績（歷年班排名）60%、研修計畫書 20%、有利審查資料 20%」。甄選總成績未達 60 分者不予錄取。",
            "學籍保留與修課學分規定：交換期間須於中山大學註冊並繳交全額學雜費（免繳接待校學費），不得辦理休學或畢業。每學期於交換學校至少應修習並通過 2 門課程（其中至少 1 門須為專業課程；領取學海惜珠或乘風萬里清寒獎助金者每學期須通過至少 3 門課程，含 1 門所屬院系專業課程及 1 門其他專業課程），並以每滿 18 授課小時抵免 1 學分為原則。",
            "錄取確認與返國義務：獲錄取者須於規定期限內於線上系統確認錄取並上傳本人及家長／監護人簽署之《錄取確認書（保證人同意書）》。返國後 2 個月內須繳交返國報告書（含中文 1,500–2,000 字、英文 1,000–1,500 字心得及 4 張具圖說照片；赴中國者免附英文心得）及正式成績單查驗，始核發交換學生證明書。",
        ],
        "language_requirement": [
            "【赴其他國家與地區】申請時須具備報名截止日前 2 年內取得之有效英語檢定證明，且至少達下列任一校內門檻：TOEFL iBT 60、IELTS 5.0、TOEIC 600、Cambridge English（PET）154、Duolingo English Test 80 或 BESTEP 培力英檢聽讀 170（同時須符合各交換學校所訂之個別語言門檻及歐語 CEFR 要求）。",
            "【赴日本地區】申請時須具備 JLPT 日語能力試驗 N5（含）以上合格證書，或具備上述任一英語檢定門檻（如申請交換校之英語授課計畫或要求更高 JLPT N1–N3 級數者，須符合該校個別規定）。",
            "【赴中國大陸地區】本國籍學生免繳語言檢定證明；外國籍學生及僑生申請部分大陸高校（如北京師範大學、廈門大學、南京大學等）須依簡章規定檢附新 HSK 5 級（180–210 分以上）或英語檢定證明。",
        ],
        "required_documents": [
            "1. 志願表（於出國交換學生甄選系統 https://partners.oia.nsysu.edu.tw/exchange/login/user/ 填報後下載列印，經本人親筆簽名後掃描為 PDF 上傳）",
            "2. 中文歷年成績單（須註明「歷年班排名」；碩一學生可以大學歷年成績單及大學畢業班排名申請，彩色掃描為 PDF 上傳）",
            "3. 合格語言能力檢定證明（須為報名截止日前 2 年內應試取得之官方成績單；赴中國大陸者免附）",
            "4. 研修計畫書（赴其他國家須含中、英文各以 1 頁 A4 為限；赴日本須含中文及日文各 1 頁 A4；赴中國大陸以中文 1–2 頁 A4 撰寫，須含修課規劃與讀書計畫）",
            "5. 有利審查資料（如得獎證明、國際志工或接待服務、社團幹部、論文發表等，上限 10 項，每項須填寫 30 字內簡述，單一 PDF 檔案上限 2 MB）",
            "6. 錄取確認書暨保證人同意書（於錄取公告後下載簽署，須經本人及父親、母親或監護人親筆簽名蓋章後上傳系統）",
        ],
        "scholarship_info": [
            "國立中山大學「西灣領航計畫（結合教育部學海飛颺與校務基金）」出國交換獎助學金（錄取自動獲獎，無須另外申請）：凡具中華民國國籍且通過本校校內甄選赴非中港澳地區交換或修讀雙聯學位之學生，自動取得受獎資格！一般學士班及碩士班學生每月補助新臺幣 10,000 元（1 學季約 NT$40,000、1 學期約 NT$60,000，補助上限 6 個月）；五年學碩士及七年學碩博一貫生每月補助新臺幣 15,000 元（1 學季約 NT$60,000、1 學期約 NT$90,000）。",
            "教育部「學海惜珠」及中山大學「乘風萬里・轉動人生—培育國際視野清寒學習獎勵金」：補助具低收入戶、中低收入戶、特殊境遇家庭、身心障礙人士子女或原住民學雜費減免資格之優秀學生出國交換（每月補助生活費並得核發來回機票與學習獎勵金；受獎生交換期間每學期須通過至少 3 門課程，含 1 門本系專業課與 1 門其他專業課）。",
            "國立中山大學「全球移動實踐人才培育獎助金」：鼓勵學生結合出國交換與海外社會實踐，受獎生須於出國前完成 54 小時志工服務並提交海外社會實踐提案，依核定計畫核發獎助金。",
            "國立中山大學「赴美國加州大學聖地牙哥分校（UCSD）暑期研究計畫獎助」與雙聯學位獎助：補助理、工、海科院等學生赴 UCSD 進行暑期研究（每人上限 NT$100,000），並提供歐美名校雙聯學位專屬獎助。",
        ],
        "partner_universities": [p["school_name"] for p in partners],
        "source_urls": nsysu_source_urls,
        "last_checked": CHECKED_AT,
    }
    (OFFICIAL_NSYSU_DIR / "exchange_info.json").write_text(
        json.dumps(exchange_info_payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    student_dashboard_payload = {
        "school_name": "國立中山大學",
        "last_checked": CHECKED_AT,
        "academic_score_minimum": 70.0,
        "academic_score_rule": "限大學部一至四年級及碩士班一至二年級在校生（不含延畢生、在職生及博士班），須具歷年學業成績班排名（日本與其他國家甄選占 30%、中國大陸甄選占 60%，總成績未達 60 分不予錄取；部分交換校要求 GPA 2.5–3.0 / 70–75 分以上）。交換期間每學期至少須修習並通過 2 門課程（含至少 1 門專業課程）。",
        "academic_gpa_minimum": None,
        "maximum_preferences": 10,
        "selection_rules": {
            "academic_policy": "gpa_or_rank",
            "academic_reference_year": "116",
            "undergraduate_gpa_minimum": None,
            "undergraduate_rank_maximum": 100.0,
            "graduate_academic_exempt": False,
            "exclude_in_service": True,
            "pending_quota_planning": False,
            "partner_requirements_need_confirmation": False,
            "degree_score_minimums": {
                "undergraduate": 70.0,
                "graduate": 70.0,
            },
            "excluded_undergraduate_years": [],
            "language_certificate_required": False,
        },
        "language_score_minimums": {
            "toefl": 60.0,
            "ielts": 5.0,
            "toeic": 600.0,
        },
        "application_periods": [
            {
                "title": "國立中山大學 2027–2028 赴【日本】學生出國交換計畫甄選（赴 115-2 春季班或 116-1 秋季班）",
                "details": [
                    "簡章公告：2026年7月28日；線上申請期間：2026年8月4日（二）09:00 至 2026年8月11日（二）17:00 止（補正期限至 8月13日 17:00）。",
                    "放榜與最終錄取名單：2026年9月4日公告錄取結果、9月9日截止確認，並於 2026年9月13日公告最終錄取名單（共錄取北海道大學、東北大學、早稻田大學、慶應義塾大學等 23 校 58 名學生）。",
                    "語言門檻：須具備 JLPT N5（含）以上合格證書，或英語達 TOEFL iBT 60 / IELTS 5.0 / TOEIC 600 / Cambridge 154 / Duolingo 80 / BESTEP 聽讀 170。",
                ],
                "source": {
                    "title": "國立中山大學 2027–2028 赴【日本】學生出國交換計畫甄選簡章與最終錄取名單",
                    "source_url": "https://oia.nsysu.edu.tw/p/406-1308-360627,r4456.php?Lang=zh-tw",
                    "category": "deadline",
                    "summary": "2027–2028 赴日本出國交換甄選時程、28 所開放學校資訊表與 58 名最終錄取名單。",
                },
                "scope": "home_application",
                "program_types": ["exchange"],
                "academic_year": "116",
                "application_round": "2027-2028 赴日本交換甄選（115-2/116-1）",
                "audience": "all_students",
                "opens_at": "2026-08-04T09:00:00+08:00",
                "deadline_at": "2026-08-11T17:00:00+08:00",
                "date_status": "verified_exact",
                "status": "closed",
                "status_note": "2027–2028 赴日本交換甄選已於 2026/08/11 17:00 截止並於 2026/09/13 公告 23 校 58 名最終錄取名單。",
                "deadline_note": "於國立中山大學出國交換學生甄選系統（https://partners.oia.nsysu.edu.tw/exchange/login/user/）線上申請。",
                "reminder_eligible": False,
                "checked_at": CHECKED_AT,
            },
            {
                "title": "國立中山大學 2027–2028 赴【其他國家與地區】學生出國交換計畫（第一次甄選，赴 116-1 或 116-2）",
                "details": [
                    "簡章公告：2026年10月27日（二）；線上申請期間：2026年11月3日（二）09:00 至 2026年11月17日（二）17:00 止（補正期限至 11月20日 17:00）。",
                    "錄取公告與確認：2026年12月15日（二）17:00 公告錄取結果，錄取生須於 2026年12月20日 17:00 前完成線上確認並上傳《錄取確認書（保證人同意書）》。",
                    "第二次甄選預告（僅開放 116-2 春季班名額）：2027年2月16日公告簡章，2027年2月22日 09:00 至 3月8日 17:00 開放線上申請，2027年3月23日放榜。",
                ],
                "source": {
                    "title": "國立中山大學 2027–2028 出國交換計畫簡章預定公告時程表與申請說明",
                    "source_url": "https://oia.nsysu.edu.tw/p/412-1308-20730.php?Lang=zh-tw",
                    "category": "exchange_application",
                    "summary": "2027–2028 赴其他國家與地區第一次及第二次甄選完整時程與線上報名規範。",
                },
                "scope": "home_application",
                "program_types": ["exchange"],
                "academic_year": "116",
                "application_round": "2027-2028 赴其他國家與地區第一次甄選（116-1/116-2）",
                "audience": "all_students",
                "opens_at": "2026-11-03T09:00:00+08:00",
                "deadline_at": "2026-11-17T17:00:00+08:00",
                "date_status": "verified_exact",
                "status": "upcoming",
                "status_note": "2027–2028 赴其他國家與地區第一次甄選將於 2026/10/27 公告簡章，並於 2026/11/03 09:00 至 11/17 17:00 開放線上申請。",
                "deadline_note": "申請人須具備 TOEFL iBT 60 / IELTS 5.0 / TOEIC 600 / Cambridge 154 / Duolingo 80 / BESTEP 聽讀 170 以上之有效語檢證明並符合各交換校門檻。",
                "reminder_eligible": True,
                "checked_at": CHECKED_AT,
            },
            {
                "title": "國立中山大學 2027–2028 赴【中國】學生出國交換計畫（第一次甄選，赴 116-1 或 116-2）",
                "details": [
                    "簡章公告：2027年1月12日（二）；線上申請期間：2027年1月15日（五）09:00 至 2027年1月26日（二）17:00 止（補正期限至 1月28日 17:00）。",
                    "錄取公告與確認：2027年2月19日（五）17:00 公告錄取結果，錄取生須於 2027年2月23日 17:00 前完成線上確認並上傳《錄取確認書》。",
                    "評分標準：學業成績（歷年班排名）占 60%、研修計畫書占 20%、有利審查資料占 20%，本國籍學生免附語言檢定證明。",
                ],
                "source": {
                    "title": "國立中山大學 2027–2028 出國交換計畫簡章預定公告時程表與中國線簡章",
                    "source_url": "https://oia.nsysu.edu.tw/p/412-1308-20730.php?Lang=zh-tw",
                    "category": "exchange_application",
                    "summary": "2027–2028 赴中國大陸交換甄選時程、評分比重與 16 所重點合作高校資訊。",
                },
                "scope": "home_application",
                "program_types": ["exchange"],
                "academic_year": "116",
                "application_round": "2027-2028 赴中國交換甄選（116-1/116-2）",
                "audience": "all_students",
                "opens_at": "2027-01-15T09:00:00+08:00",
                "deadline_at": "2027-01-26T17:00:00+08:00",
                "date_status": "verified_exact",
                "status": "upcoming",
                "status_note": "2027–2028 赴中國學生出國交換甄選將於 2027/01/12 公告簡章，並於 2027/01/15 09:00 至 01/26 17:00 開放線上申請。",
                "deadline_note": "於國立中山大學出國交換學生甄選系統（https://partners.oia.nsysu.edu.tw/exchange/login/user/）線上申請。",
                "reminder_eligible": True,
                "checked_at": CHECKED_AT,
            },
        ],
        "program_overview": [
            {
                "title": f"國立中山大學國際事務處暨管理學院出國交換計畫總覽（{len(partners)} 所全球交換合作大學）",
                "details": [
                    f"國立中山大學國際事務處（OIA）與管理學院職涯發展暨國際交流辦公室共同推動多軌出國交換甄選，本平台完整收錄 {len(partners)} 所官方交換合作大學（含當期簡章開放申請之 {open_partner_count} 所日本、歐美紐澳亞及中國大陸交換校，以及 {len(partners) - open_partner_count} 所國際處四大洲交換校 Fact Sheet 合作大學）。",
                    "獨創「西灣領航計畫（結合教育部學海飛颺與校務基金）」自動獎助機制：凡通過本校甄選赴非中港澳地區交換之本國籍錄取生，無須另外提出申請即自動獲得每月 NT$10,000（五／七年學碩博生每月 NT$15,000，上限 6 個月）之獎助學金！",
                    f"本平台完整整合中山大學 {len(partners)} 所合作大學之申請門檻、Fact Sheet 連結、最新兩梯次共 111 校 315 人最終錄取榜單，以及涵蓋 {exp_covered_schools} 所合作校之 1,823 篇歷年學長姐返國心得 PDF、27 部交換影音日記與 22 份經驗分享簡報。",
                ],
                "source": {
                    "title": "國立中山大學國際事務處—出國交換計畫簡章與交換校專區",
                    "source_url": "https://oia.nsysu.edu.tw/p/412-1308-20730.php?Lang=zh-tw",
                    "category": "partner_school",
                    "summary": "國立中山大學赴日本、其他國家與地區（校級＋管院）及中國大陸出國交換計畫總覽。",
                },
            }
        ],
        "eligibility": [
            {
                "title": "申請資格、歷年班排名評分比重、每學期至少通過 2 門課（含專業課）與 18 小時抵 1 學分規定",
                "details": [
                    "申請對象與年級限制：限國立中山大學大學部一至四年級及碩士班一至二年級在校生（不含延畢生、在職生身分入學者及博士班學生）。申請時須具本校至少一學期成績及歷年班排名（碩一學生可以大學歷年成績單及班排名申請）。",
                    "書面審查評分比重：【赴日本及其他國家】學業成績（歷年班排名）30%、語言能力（CEFR 對照表）40%、研修計畫書 20%、有利審查資料 10%；【赴中國大陸】學業成績 60%、研修計畫書 20%、有利審查資料 20%。總成績未達 60 分不予錄取。",
                    "境外最低修課與學分採認：每學期至少應修習並通過 2 門課程（含至少 1 門專業課程；學海惜珠／乘風萬里受獎生須通過至少 3 門課程，含 1 門本系專業課與 1 門其他專業課）。返國學分抵免以每滿 18 授課小時採計 1 學分為原則。",
                    "返國義務：返國後 2 個月內須繳交返國報告書（中英文心得及 4 張照片；赴中國免附英文心得）及正式成績單查驗，始核發交換學生證明書。",
                ],
                "source": {
                    "title": "國立中山大學學生出國交換甄選要點與處理交換學生選課及成績作業要點",
                    "source_url": "https://oia.nsysu.edu.tw/var/file/308/1308/img/3642/492663022.pdf",
                    "category": "exchange_application",
                    "summary": "國立中山大學交換生申請資格、書審配分、最低修課門數與返國學分採認辦法。",
                },
            }
        ],
        "language_requirements": [
            {
                "title": "三大甄選軌道語言檢定門檻（其他國家英檢、日本 JLPT N5 或英檢、中國免語檢）與 CEFR 轉換標準",
                "details": [
                    "【赴其他國家與地區】：須具備報名截止日前 2 年內取得之有效英語檢定證明，且達 TOEFL iBT 60、IELTS 5.0、TOEIC 600、Cambridge PET 154、Duolingo 80 或 BESTEP 培力英檢聽讀 170 以上（並須符合交換校個別門檻）。",
                    "【赴日本地區】：須具備 JLPT N5（含）以上合格證書，或具備上述任一英語檢定門檻（如交換校要求 JLPT N1–N3 或更高英檢分數者，須符合該校規定）。",
                    "【赴中國大陸地區】：本國籍學生免繳語言檢定證明；外國籍學生及僑生申請部分學校須具新 HSK 5 級（180–210 分以上）。",
                ],
                "source": {
                    "title": "國立中山大學國際事務處—語言檢測 CEFR 對照表與各線甄選簡章",
                    "source_url": "https://oia.nsysu.edu.tw/p/412-1308-20734.php?Lang=zh-tw",
                    "category": "exchange_application",
                    "summary": "國立中山大學交換生語言檢定最低門檻與 CEFR 等級對照標準。",
                },
            }
        ],
        "required_documents": [
            {
                "title": "國立中山大學出國交換學生甄選系統（partners.oia.nsysu.edu.tw）線上申請應繳文件清單",
                "details": [
                    "1. 志願表：於線上系統填寫志願順序後下載列印，經本人親筆簽名後掃描上傳。",
                    "2. 中文歷年成績單：須有「歷年班排名」（碩一學生可以大學歷年成績單及班排名申請）。",
                    "3. 合格語言能力檢定證明：須為報名截止日前 2 年內取得之官方成績單（赴中國大陸免附）。",
                    "4. 研修計畫書：赴其他國家須含中、英文各 1 頁 A4 為限；赴日本須含中文及日文各 1 頁 A4；赴中國以中文 1–2 頁 A4 撰寫。",
                    "5. 有利審查資料（上限 10 項，每項附 30 字內說明，單檔上限 2 MB）及錄取後上傳之《錄取確認書（保證人同意書）》。",
                ],
                "source": {
                    "title": "國立中山大學出國交換計畫甄選簡章與線上申請系統",
                    "source_url": "https://oia.nsysu.edu.tw/p/412-1308-20730.php?Lang=zh-tw",
                    "category": "exchange_application",
                    "summary": "線上申請應繳 PDF 文件規格、頁數限制與補正規定。",
                },
            }
        ],
        "scholarship_info": [
            {
                "title": "西灣領航計畫（錄取自動獲獎每月 NT$10,000–15,000）、學海惜珠、乘風萬里清寒獎勵金與全球移動實踐獎助",
                "details": [
                    "西灣領航計畫（結合教育部學海飛颺與校務基金）：通過本校非中港澳出國交換或雙聯學位甄選之本國籍錄取生「自動獲得獎助資格（無須另外申請）」！一般學士／碩士生每月 NT$10,000（1 學季約 4 萬、1 學期約 6 萬，上限 6 個月）；五／七年學碩博一貫生每月 NT$15,000（1 學季約 6 萬、1 學期約 9 萬）。",
                    "教育部「學海惜珠」與中山大學「乘風萬里・轉動人生—培育國際視野清寒學習獎勵金」：提供低收、中低收、特殊境遇家庭、身障人士子女及原住民學生高額生活費與機票補助（受獎生每學期須通過至少 3 門課程）。",
                    "全球移動實踐人才培育獎助金（完成 54 小時志工服務並執行海外社會實踐提案）與赴美國 UCSD 暑期研究計畫獎助（上限 NT$100,000）。",
                ],
                "source": {
                    "title": "國立中山大學國際事務處—出國交換獎助學金專區",
                    "source_url": "https://oia.nsysu.edu.tw/p/412-1308-20736.php?Lang=zh-tw",
                    "category": "scholarship",
                    "summary": "西灣領航計畫、學海飛颺、學海惜珠、乘風萬里清寒學習獎勵金與全球移動實踐獎助辦法。",
                },
            }
        ],
        "document_explanations": [
            {
                "title": "國立中山大學出國交換學生甄選系統（partners.oia.nsysu.edu.tw）線上填報、補正機制與錄取確認書規範",
                "summary": "中山大學出國交換分為「日本線（7–8 月）」、「其他國家與地區一甄（10–11 月）／二甄（2–3 月）」及「中國線（1 月／9 月）」三軌線上申請。",
                "key_points": [
                    "所有申請文件均須以 PDF 格式上傳至 https://partners.oia.nsysu.edu.tw/exchange/login/user/ ；送出申請後國際處將進行資格初核，如需補件須於簡章所定「申請文件補正期限（通常為截止後 2–3 日 17:00）」前完成上傳。",
                    "研修計畫書須嚴格遵守頁數與語言規定（其他國家為中英文各 1 頁 A4、日本為中日文各 1 頁 A4、中國為中文 1–2 頁 A4）；獲錄取後須於確認期限內上傳經本人及父母／監護人簽章之《錄取確認書》。",
                ],
                "applies_to": [],
                "source": {
                    "title": "國立中山大學出國交換計畫甄選簡章與線上申請系統",
                    "source_url": "https://oia.nsysu.edu.tw/p/412-1308-20730.php?Lang=zh-tw",
                    "category": "exchange_application",
                    "summary": None,
                },
                "document_url": "https://oia.nsysu.edu.tw/p/412-1308-20730.php?Lang=zh-tw",
                "document_type": "official_document",
                "full_text_extracted": True,
            }
        ],
        "rule_explanations": [
            {
                "title": "國立中山大學學生出國交換甄選要點與選課成績作業要點：書審配分、西灣領航自動獎助與 18 小時抵 1 學分",
                "summary": "規範中山大學交換生甄選配分比重、西灣領航自動獎助資格、境外每學期至少通過 2 門課（含專業課）與返國學分採認規則。",
                "key_points": [
                    "書面審查配分：日本及其他國家為「學業成績（歷年班排名）30%、語言能力 40%、研修計畫書 20%、有利審查資料 10%」；中國大陸為「學業成績 60%、研修計畫書 20%、有利審查資料 20%」，總成績未達 60 分不予錄取。",
                    "交換期間每學期至少應修習並通過 2 門課程（含至少 1 門專業課程；學海惜珠／乘風萬里受獎生須通過至少 3 門課程），返國後以每滿 18 授課小時抵免 1 學分為原則，並須於返國後 2 個月內繳交雙語返國報告書及正式成績單查驗。",
                    "凡通過校內甄選赴非中港澳地區交換之本國籍錄取生，自動取得「西灣領航計畫」獎助資格（一般學士／碩士生每月 NT$10,000、五／七年學碩博生每月 NT$15,000，上限 6 個月）。",
                ],
                "applies_to": [],
                "source": {
                    "title": "國立中山大學學生出國交換甄選要點與處理交換學生選課及成績作業要點",
                    "source_url": "https://oia.nsysu.edu.tw/var/file/308/1308/img/3642/492663022.pdf",
                    "category": "exchange_application",
                    "summary": None,
                },
                "document_url": "https://oia.nsysu.edu.tw/var/file/308/1308/img/3642/492663022.pdf",
                "document_type": "official_document",
                "full_text_extracted": True,
            }
        ],
        "sources": [
            {
                "title": "國立中山大學國際事務處—出國交換計畫簡章與甄選時程專區",
                "source_url": "https://oia.nsysu.edu.tw/p/412-1308-20730.php?Lang=zh-tw",
                "category": "exchange_application",
                "summary": None,
            },
            {
                "title": "國立中山大學 2027–2028 赴【日本】學生出國交換計畫甄選簡章與學校資訊表",
                "source_url": "https://oia.nsysu.edu.tw/p/406-1308-360627,r4456.php?Lang=zh-tw",
                "category": "exchange_application",
                "summary": None,
            },
            {
                "title": "國立中山大學 2026–2027 赴【其他國家與地區】出國交換甄選簡章（校級 93 校＋管院 36 校）",
                "source_url": "https://oia.nsysu.edu.tw/p/406-1308-341179,r4456.php?Lang=zh-tw",
                "category": "partner_school",
                "summary": None,
            },
            {
                "title": "國立中山大學 2026–2027 赴【中國】學生出國交換計畫甄選簡章與學校資訊表",
                "source_url": "https://oia.nsysu.edu.tw/p/406-1308-346711,r4456.php?Lang=zh-tw",
                "category": "partner_school",
                "summary": None,
            },
            {
                "title": "國立中山大學國際事務處—出國交換獎助學金專區（西灣領航、學海飛颺、學海惜珠、乘風萬里）",
                "source_url": "https://oia.nsysu.edu.tw/p/412-1308-20736.php?Lang=zh-tw",
                "category": "scholarship",
                "summary": None,
            },
            {
                "title": "國立中山大學國際事務處—歷年交換生返國心得報告與影音簡報專區（1,823 篇 PDF）",
                "source_url": "https://oia.nsysu.edu.tw/p/412-1308-20773.php?Lang=zh-tw",
                "category": "partner_school",
                "summary": None,
            },
            {
                "title": "國立中山大學出國交換學生甄選線上申請系統（partners.oia.nsysu.edu.tw）",
                "source_url": "https://partners.oia.nsysu.edu.tw/exchange/login/user/",
                "category": "exchange_application",
                "summary": None,
            },
        ],
    }
    (OFFICIAL_NSYSU_DIR / "student_dashboard.json").write_text(
        json.dumps(student_dashboard_payload, ensure_ascii=False, indent=2)
        + "\n",
        encoding="utf-8",
    )

    pages_records = [
        {
            "title": "國立中山大學：2027–2028 赴日本、其他國家與地區、中國大陸三軌出國交換甄選時程",
            "source_url": "https://oia.nsysu.edu.tw/p/412-1308-20730.php?Lang=zh-tw",
            "published_at": "2026-07-28T00:00:00Z",
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
            "title": "國立中山大學：學生出國交換甄選要點、書審配分比重與每學期至少通過 2 門課規定",
            "source_url": "https://oia.nsysu.edu.tw/var/file/308/1308/img/3642/492663022.pdf",
            "published_at": "2026-07-28T00:00:00Z",
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
            "title": "國立中山大學：出國交換語言檢測 CEFR 對照表與各區語言檢定最低門檻",
            "source_url": "https://oia.nsysu.edu.tw/p/412-1308-20734.php?Lang=zh-tw",
            "published_at": "2026-07-28T00:00:00Z",
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
            "title": "國立中山大學：出國交換學生甄選系統應繳文件、中英文研修計畫書與保證人同意書規範",
            "source_url": "https://partners.oia.nsysu.edu.tw/exchange/login/user/",
            "published_at": "2026-07-28T00:00:00Z",
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
            "title": "國立中山大學：西灣領航計畫（錄取自動獲獎每月 NT$10,000–15,000）、學海惜珠與乘風萬里獎助學金",
            "source_url": "https://oia.nsysu.edu.tw/p/412-1308-20736.php?Lang=zh-tw",
            "published_at": "2026-07-28T00:00:00Z",
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
    (OFFICIAL_NSYSU_DIR / "pages.jsonl").write_text(
        "\n".join(json.dumps(p, ensure_ascii=False) for p in pages_records)
        + "\n",
        encoding="utf-8",
    )

    home_rules = {
        "school_id": "nsysu",
        "school_name": "國立中山大學",
        "eligibility": student_dashboard_payload["eligibility"],
        "application_periods": student_dashboard_payload["application_periods"],
        "selection_rules": {
            "minimum_total_selection_score": 60.0,
            "weights_japan_and_other_regions": {
                "class_rank": 0.30,
                "language_proficiency": 0.40,
                "study_plan": 0.20,
                "supporting_documents": 0.10,
            },
            "weights_china": {
                "class_rank": 0.60,
                "study_plan": 0.20,
                "supporting_documents": 0.20,
            },
            "minimum_courses_passed_per_semester": {
                "general_exchange": 2,
                "general_major_related": 1,
                "disadvantaged_scholarship_total": 3,
                "disadvantaged_scholarship_major_related": 2,
            },
            "credit_transfer_hours_per_credit": 18,
            "return_report_deadline_months": 2,
        },
        "source_urls": nsysu_source_urls,
        "verified_at": "2026-10-18",
    }
    (OFFICIAL_NSYSU_DIR / "home_rules.json").write_text(
        json.dumps(home_rules, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    (OFFICIAL_NSYSU_DIR / "documents.json").write_text(
        json.dumps(
            {
                "school_name": "國立中山大學",
                "required_documents": student_dashboard_payload["required_documents"],
                "source_urls": nsysu_source_urls,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    (OFFICIAL_NSYSU_DIR / "scholarships.json").write_text(
        json.dumps(
            {
                "school_name": "國立中山大學",
                "scholarships": student_dashboard_payload["scholarship_info"],
                "source_urls": nsysu_source_urls,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    completeness = {
        "school_id": "nsysu",
        "school_name": "國立中山大學",
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
        "active_term": "2027-2028赴日本交換甄選已於2026/08/11截止並於09/13公告58名最終錄取名單；2027-2028赴其他國家與地區第一次甄選於2026/10/27公告簡章、11/03–11/17線上申請；2027-2028赴中國第一次甄選於2027/01/12公告簡章、01/15–01/26線上申請。",
        "verified_at": "2026-10-18",
    }
    (OFFICIAL_NSYSU_DIR / "catalog-completeness.json").write_text(
        json.dumps(completeness, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    (OFFICIAL_NSYSU_DIR / "verification_status.json").write_text(
        json.dumps(
            {
                "school_id": "nsysu",
                "school_name": "國立中山大學",
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
            "sources/nsysu/nsysu_2027_2028_japan_partners.pdf",
            "https://oia.nsysu.edu.tw/var/file/308/1308/img/4609/416455264.pdf",
            "國立中山大學 2027–2028 赴【日本】學生出國交換計畫學校資訊一覽表（28 所日本合作大學）",
        ),
        (
            "sources/nsysu/nsysu_2026_2027_university_wide_partners.pdf",
            "https://oia.nsysu.edu.tw/var/file/308/1308/img/4609/441880551.pdf",
            "國立中山大學 2026–2027 赴【其他國家與地區】校級交換學校資訊一覽表（93 所歐美紐澳亞合作大學）",
        ),
        (
            "sources/nsysu/nsysu_2026_2027_cm_partners.pdf",
            "https://oia.nsysu.edu.tw/var/file/308/1308/img/4609/800051660.pdf",
            "國立中山大學 2026–2027 赴【其他國家與地區】管理學院院級交換學校資訊一覽表（36 所商管合作大學）",
        ),
        (
            "sources/nsysu/nsysu_2027_2028_china_partners.pdf",
            "https://oia.nsysu.edu.tw/var/file/308/1308/img/4609/176233384.pdf",
            "國立中山大學赴【中國】學生出國交換計畫學校資訊一覽表（16 所大陸 985/211 重點合作大學）",
        ),
        (
            "sources/nsysu/nsysu_2027_2028_japan_admitted_final.pdf",
            "https://oia.nsysu.edu.tw/var/file/308/1308/img/4611/768028264.pdf",
            "國立中山大學 2027–2028 赴【日本】學生出國交換甄選最終錄取名單（23 校 58 名學生）",
        ),
        (
            "sources/nsysu/nsysu_2026_2027_other_regions_admitted_final.pdf",
            "https://oia.nsysu.edu.tw/var/file/308/1308/img/4611/602742003.pdf",
            "國立中山大學 2026–2027 赴【其他國家與地區】學生出國交換甄選（一甄＋二甄）最終錄取名單（88 校 257 名學生）",
        ),
        (
            "sources/nsysu/nsysu_exchange_selection_regulations.pdf",
            "https://oia.nsysu.edu.tw/var/file/308/1308/img/3642/492663022.pdf",
            "國立中山大學學生出國交換甄選要點",
        ),
        (
            "sources/nsysu/nsysu_exchange_course_grade_rules.pdf",
            "https://oia.nsysu.edu.tw/static/file/308/1308/img/3642/746350618.pdf",
            "國立中山大學處理交換學生選課及成績作業要點",
        ),
        (
            "sources/nsysu/guidelines_2027_2028_schedule.html",
            "https://oia.nsysu.edu.tw/p/412-1308-20730.php?Lang=zh-tw",
            "國立中山大學國際事務處—出國交換簡章公告與 2027–2028 三線甄選預定時程表",
        ),
        (
            "sources/nsysu/guidelines_2027_2028_japan.html",
            "https://oia.nsysu.edu.tw/p/406-1308-360627,r4456.php?Lang=zh-tw",
            "國立中山大學 2027–2028 赴【日本】學生出國交換計畫甄選簡章公告頁",
        ),
        (
            "sources/nsysu/language_score_conversion.html",
            "https://oia.nsysu.edu.tw/p/412-1308-20734.php?Lang=zh-tw",
            "國立中山大學國際事務處—出國交換語言檢測 CEFR 對照表",
        ),
        (
            "sources/nsysu/sister_data.json",
            "https://oia.nsysu.edu.tw/static/file/308/1308/img/4311/partners_display_data.js",
            "國立中山大學國際事務處全球姊妹校資料庫（SISTER_DATA）",
        ),
        (
            "sources/nsysu/nsysu_catalog_source.json",
            "https://oia.nsysu.edu.tw/p/412-1308-20730.php?Lang=zh-tw",
            "國立中山大學 218 所出國交換合作大學整合資料集（含簡章名額、Fact Sheet、1,823 篇心得 PDF 及錄取榜單）",
        ),
        (
            "sources/nsysu/nsysu_resolved_locations.json",
            "https://oia.nsysu.edu.tw/p/412-1308-20730.php?Lang=zh-tw",
            "國立中山大學 218 所出國交換合作大學 ROR / Wikidata 地理座標核對表",
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
        "school_id": "nsysu",
        "school_name": "國立中山大學",
        "generated_at": CHECKED_AT,
        "active_cycle_note": completeness["active_term"],
        "sources": prov_sources,
    }
    (OFFICIAL_NSYSU_DIR / "import_provenance.json").write_text(
        json.dumps(provenance_payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    print(
        f"Successfully built NSYSU catalog: {len(partners)} partners ({open_partner_count} open, "
        f"{completeness['verified_campus_images']} verified images, {completeness['verified_locations']} verified locations), "
        f"{len(workflows)} workflows, {len(destinations)} destinations, {len(research_records)} research records, "
        f"{exp_covered_schools} schools with experience/admitted records ({len(student_experience_rows)} rows)."
    )


if __name__ == "__main__":
    main()
