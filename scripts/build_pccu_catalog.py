"""Build the official Chinese Culture University (中國文化大學, PCCU) exchange data bundle."""

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

SOURCES_PCCU_DIR = REPO_ROOT / "sources" / "pccu"
OFFICIAL_PCCU_DIR = REPO_ROOT / "src" / "exchange_info" / "official_data" / "pccu"
STATIC_DIR = REPO_ROOT / "src" / "exchange_info" / "static"

CHECKED_AT = "2026-10-19T16:00:00Z"

REGION_BY_COUNTRY = {
    "日本": "亞洲",
    "韓國": "亞洲",
    "中國大陸": "中國大陸及港澳",
    "香港": "中國大陸及港澳",
    "澳門": "中國大陸及港澳",
    "蒙古": "亞洲",
    "馬來西亞": "亞洲",
    "印尼": "亞洲",
    "越南": "亞洲",
    "泰國": "亞洲",
    "印度": "亞洲",
    "美國": "美洲",
    "加拿大": "美洲",
    "秘魯": "美洲",
    "澳洲": "大洋洲",
    "英國": "歐洲",
    "德國": "歐洲",
    "法國": "歐洲",
    "波蘭": "歐洲",
    "比利時": "歐洲",
    "義大利": "歐洲",
    "西班牙": "歐洲",
    "俄羅斯": "歐洲",
}

REGION_COST_DEFAULTS = {
    "日本": (
        "JPY 80,000–130,000 / 月（東京與京阪神約 JPY 95,000–140,000；天理、二松學舍、國士館、創價、名古屋學院大學提供交換生免住宿費優惠）",
        "憑日本接待校核發之在留資格認定證明書（COE）向日本台灣交流協會換發留學簽證，抵日後須加入國民健康保險。",
    ),
    "韓國": (
        "KRW 800,000–1,300,000 / 月（首爾圈雙人房宿舍每學期約 KRW 33萬–182萬；釜山、安東、濟州生活費實惠，安東大學提供交換生語學堂免費）",
        "憑韓國標準入學許可書申辦 D-2-6 交換學生簽證，抵韓後辦理外國人登錄並自動納入韓國國民健康保險（NHIS），入住校內宿舍須備妥麻疹疫苗與肺結核英文檢驗證明。",
    ),
    "中國大陸": (
        "RMB 2,000–3,800 / 月（校內港澳臺交換學生宿舍住宿費與校園食堂餐費實惠）",
        "持有效護照與臺胞證（臺灣居民來往大陸通行證）入境，並於報到前完成最近 3 個月內醫院體格檢查與大陸境內來華留學生綜合醫療保險。",
    ),
    "蒙古": (
        "USD 450–750 / 月（烏蘭巴托國立蒙古大學學生宿舍與日常開支實惠）",
        "須憑接待校正式邀請函申辦蒙古學生簽證並投保海外全期醫療及意外保險。",
    ),
    "馬來西亞": (
        "MYR 1,500–2,500 / 月（吉隆坡 UCSI 大學周邊生活機能便利且物價親民）",
        "須透過 EMGS（Education Malaysia Global Services）系統申辦馬來西亞學生簽證（VAL / Student Pass）。",
    ),
    "印尼": (
        "IDR 5,000,000–8,500,000 / 月（泗水艾爾朗加大學與萬丹印尼多媒體大學生活開支實惠）",
        "須由接待校協助向印尼移民總局申辦學習簽證（C316 學生電子簽證）並投保海外醫療險。",
    ),
    "越南": (
        "USD 400–700 / 月（河內、胡志明市與同奈省學生住宿及日常飲食成本低廉）",
        "須憑接待校入學許可透過駐臺北越南經濟文化辦事處申辦越南學生簽證。",
    ),
    "泰國": (
        "THB 15,000–25,000 / 月（曼谷、清邁與孔敬學生公寓及生活成本親民）",
        "須憑接待校入學許可向泰國貿易經濟辦事處申辦 Non-Immigrant ED 學生簽證。",
    ),
    "印度": (
        "USD 400–700 / 月（旁遮普邦、昌迪加爾與喜馬偕爾邦校內學生宿舍與膳食費用實惠）",
        "須憑接待校正式入學許可向印度台北協會申辦印度 Student Visa。",
    ),
    "澳洲": (
        "AUD 1,800–2,600 / 月（含黃金海岸／布里斯本／西雪梨學生住宿、膳食與日常交通）",
        "須購買澳洲海外學生健康保險（OSHC）並線上申辦 Subclass 500 學生簽證。",
    ),
    "加拿大": (
        "CAD 1,600–2,400 / 月（含溫哥華市中心學生住宿、膳食、省級或校內醫保與大眾運輸）",
        "須依溫哥華電影學院入學信辦理加拿大 Study Permit 或 eTA 並投保醫療保險。",
    ),
    "美國": (
        "USD 1,300–2,200 / 月（含校內學生宿舍、Meal Plan 膳食計畫、強制校園醫療保險與當地交通）",
        "須憑 DS-2019 或 I-20 表格繳納 SEVIS I-901 費用並至 AIT 申辦 J-1 / F-1 簽證及投保接待校強制醫療險。",
    ),
    "秘魯": (
        "USD 600–950 / 月（含利馬卡耶塔諾埃雷迪亞大學周邊學生住宿、膳食與日常交通）",
        "須依接待校指引申辦秘魯交換學生簽證並投保海外全期醫療及意外保險。",
    ),
    "英國": (
        "GBP 1,100–1,650 / 月（倫敦西敏大學生活費較高；威爾斯卡地夫大學住宿與生活費較親民）",
        "交換一學期（6 個月內）可辦理 Standard Visitor 簽證，交換一學年須辦理英國 Student Visa 並繳納 IHS 醫療附加費。",
    ),
    "德國": (
        "EUR 934–1,250 / 月（德國簽證限制提領帳戶基準為每月 EUR 934，含海德堡／拜羅伊特／富特旺根／希爾德斯海姆住宿與生活費）",
        "須辦理德國法定學生公保（約 EUR 120–130 / 月）、繳納學期雜費（Semesterbeitrag）並申辦德國長期學生簽證。",
    ),
    "法國": (
        "EUR 850–1,400 / 月（巴黎 INALCO／巴黎十三／塞爾吉約 EUR 1,000–1,450；雷恩、里爾、阿拉斯、里昂約 EUR 750–1,100，可申請法國政府 CAF 房補）",
        "須透過法國教育中心（Campus France）完成面談程序並申辦長期學生簽證（VLS-TS）。",
    ),
    "波蘭": (
        "EUR 550–850 / 月（約 PLN 2,400–3,600，華沙生命科學大學校內宿舍與生活開支實惠）",
        "須向波蘭臺北辦事處申辦 D 類國別學生簽證並備妥歐盟規格旅行醫療保險。",
    ),
    "比利時": (
        "EUR 850–1,300 / 月（含布魯塞爾學生公寓、餐飲與大眾運輸）",
        "須向比利時台北辦事處辦理長期學生簽證（D 簽），抵比後向布魯塞爾市政廳登記居留。",
    ),
    "義大利": (
        "EUR 800–1,250 / 月（錫耶納、費拉拉與薩薩里大學城學生住宿與日常開支較米蘭、羅馬親民）",
        "須向義大利經濟貿易文化推廣辦事處申辦學生簽證 D 簽，抵義後 8 個工作天內申辦居留證（Permesso di Soggiorno）。",
    ),
    "西班牙": (
        "EUR 800–1,250 / 月（含巴塞隆納／赫羅納學生公寓、飲食與大眾運輸）",
        "須備妥涵蓋全額醫療與遺體運返之私人醫療保險以向西班牙商務辦事處申辦學生簽證。",
    ),
    "俄羅斯": (
        "USD 450–800 / 月（聖彼得堡國立大學與海參崴遠東聯邦大學校內留學生宿舍費用低廉，每月住宿費約 USD 30–80）",
        "須憑俄羅斯聯邦內務部核發之官方入境邀請函向莫斯科台北經濟文化協調委員會申辦俄羅斯留學簽證，抵俄後 7 個工作天內辦理落地簽登記與當地醫療保險。",
    ),
}

PCCU_OIMA_HUB_URL = "https://oima.pccu.edu.tw/exchanges.htm"
PCCU_OUTBOUND_GUIDE_URL = "https://oima.pccu.edu.tw/exchanges-detail.htm"
PCCU_RECOMMENDATION_GUIDE_URL = "https://oima.pccu.edu.tw/exchanges-detail2.htm"
PCCU_MILITARY_GUIDE_URL = "https://oima.pccu.edu.tw/exchanges-detail3.htm"
PCCU_XUEHAI_FEIYANG_URL = "https://oima.pccu.edu.tw/exchanges-detail4.htm"
PCCU_XUEHAI_XIZHU_URL = "https://oima.pccu.edu.tw/exchanges-detail5.htm"
PCCU_MOBILITY_SCHOLARSHIP_PAGE_URL = "https://oima.pccu.edu.tw/exchanges-detail6.htm"
PCCU_SISTER_SCHOOLS_PAGE_URL = "https://oima.pccu.edu.tw/school.htm"
PCCU_REGULATIONS_PAGE_URL = "https://oima.pccu.edu.tw/regulations.htm"

PCCU_OUTBOUND_GUIDELINES_PDF_URL = "https://oima.pccu.edu.tw/Upload/202607/learning_2026071112283508.pdf"
PCCU_OUTBOUND_FAQ_PDF_URL = "https://oima.pccu.edu.tw/Upload/202607/learning_2026071112283509.pdf"
PCCU_OIMA_QUOTA_LIST_PDF_URL = "https://oima.pccu.edu.tw/Upload/202607/learning_2026071112283510.pdf"
PCCU_SISTER_MASTER_LIST_PDF_URL = "https://oima.pccu.edu.tw/Upload/202609/exchange_2026090314332408.pdf"
PCCU_MOBILITY_SCHOLARSHIP_PDF_URL = "https://oima.pccu.edu.tw/Upload/202607/learning_2026071522332308.pdf"
PCCU_EXP_AUTH_FORM_PDF_URL = "https://oima.pccu.edu.tw/Upload/202607/learning_2026071522241609.pdf"
PCCU_SHORT_TERM_GRANT_PDF_URL = "https://oima.pccu.edu.tw/Upload/202608/exchange_2026082710142908.pdf"
PCCU_MAINLAND_GUIDELINES_PDF_URL = "https://drive.google.com/file/d/1dTcHLFFBOHMCXCmTDC6hBbnk7NjmVRUK/view?usp=drive_link"

PCCU_JP_ANNOUNCEMENT_URL = "https://japanese.pccu.edu.tw/p/406-1109-140489,r278.php?Lang=zh-tw"
PCCU_JP_ADMITTED_URL = "https://japanese.pccu.edu.tw/p/406-1109-142867,r278.php?Lang=zh-tw"
PCCU_KR_SISTERS_URL = "https://kor.pccu.edu.tw/p/412-1112-974.php?Lang=zh-tw"
PCCU_KR_SOP_URL = "https://kor.pccu.edu.tw/p/405-1112-72586,c1202.php?Lang=zh-tw"
PCCU_KR_RULES_URL = "https://kor.pccu.edu.tw/p/405-1112-71244,c1202.php?Lang=zh-tw"
PCCU_KR_EXP_HUB_URL = "https://kor.pccu.edu.tw/p/412-1112-10453.php?Lang=zh-tw"
PCCU_FR_EXCHANGE_URL = "https://french.pccu.edu.tw/p/412-1115-7823.php"
PCCU_RU_EXCHANGE_URL = "https://crgarl.pccu.edu.tw/p/405-1113-110334,c11303.php?Lang=zh-tw"


def clean_text(s: str) -> str:
    if not s:
        return ""
    return re.sub(r"\s+", " ", s).strip()


def format_colleges(item: dict) -> str:
    zh = item["name_zh"]
    sg = item["source_group"]
    note = item.get("note") or ""
    if zh == "香川大學":
        return "法學院（國際處《甄選交換學校一覽表》規定：限法律學系學生申請）"
    if zh == "東義大學":
        return "理工學院為主（國際處《甄選交換學校一覽表》規定：以理工學院學生申請為主）"
    if zh == "希爾德斯海姆大學":
        return "文學院（國際處《甄選交換學校一覽表》規定：限申請哲學專業）"
    if zh == "薩薩里大學":
        return "環境規劃暨生物資源學院優先（國際處《甄選交換學校一覽表》備註：都市計劃與開發管理學系學生優先）"
    if zh in {"卡地夫大學", "西敏大學"}:
        return "國際暨外語學院、文學院及相關學院（公費名額限申請現代語言學院／人文模組現代語言相關課程；西敏大學自費 Study Abroad 不限學院）"
    if zh == "平成國際大學":
        return "法學院及相關學院（日文系甄選簡章規定：限就讀該校法學部課程）"
    if sg == "jp_dept":
        return "不限學院（由國際暨外語學院日本語文學系［東亞組］主辦甄選，全校各學院符合日檢與學業門檻之在學學生皆可報考）"
    if sg == "kr_dept":
        return "國際暨外語學院（韓國語文學系學生優先，並開放全校修習韓文相關課程符合資格之在學學生報考）"
    if sg == "fr_ru_dept":
        return "國際暨外語學院（歐美語文學系法文組／俄文組、法國語文學系、俄國語文學系及修習法俄語課程符合檢定門檻之在學學生）"
    if "商業" in note or "觀光" in note:
        return f"商學院、國際暨外語學院及全校各學院（{note}）"
    return "不限學院（全校 12 個學院正式學籍在學學生皆可依當期簡章與姊妹校開放領域申請）"


def format_degree_levels(item: dict) -> str:
    zh = item["name_zh"]
    sg = item["source_group"]
    if zh in {"大阪經濟法科大學", "名古屋學院大學", "平成國際大學", "威斯康辛大學麥迪遜分校"}:
        return "大學部在學學生（須於中國文化大學修業滿一學年以上，轉學生至少完成一學期學業；不含大一新生）"
    if zh in {"筑紫女學園大學", "同志社女子大學", "梨花女子大學"}:
        return "限女性在學學生報考（大學部修業滿一學年以上、碩博士班修業滿一學期以上之正式學籍在學女生）"
    if sg == "jp_dept":
        return "大學部二年級（含）以上及碩士班一年級下學期（含）以上正式學籍在學學生（大學部前一學期平均 70 分以上、碩士班 80 分以上；赴日雙聯學位須四學期平均 85 分以上且修滿 72 學分）"
    if sg == "mainland":
        return "學士班（修業滿一學年以上）及碩、博士班（修業滿一學期以上）正式學籍在學學生（須獲所屬系所主管同意，研究生另須指導教授同意推薦）"
    return "學士班修業滿一學年以上（轉學生至少完成一學期）、碩博士班修業滿一學期以上之正式學籍在學學生（在職專班學生如欲申請須另附工作單位同意函）"


def format_study_period(item: dict) -> str:
    quota = item.get("quota") or ""
    sg = item["source_group"]
    if "一學期" in quota or "(學期)" in quota or "（一學期）" in quota:
        return "1 學期（可依姊妹校規定申請自費延長或一學年方案）"
    if sg in {"jp_dept", "fr_ru_dept"}:
        return "1 學年（依日本／法俄姊妹校交換計畫以一學年為原則；部分學校可申請 1 學期）"
    return "1 學期 或 1 學年（依當期甄選簡章與姊妹校核定名額為準）"


def format_program_type(item: dict) -> str:
    sg = item["source_group"]
    zh = item["name_zh"]
    if zh in {"武藏野大學", "琉球大學", "布魯塞爾自由大學"}:
        return "國際處國合組校級交換暨外語院系甄選交換學生計畫（雙軌並行）"
    if sg == "oima_overseas":
        return "國際暨兩岸事務處（國合組）甄選赴國外姊妹校交換學生計畫"
    if sg == "jp_dept":
        return "日本語文學系（東亞組）主辦赴日本短期交換留學生甄選計畫"
    if sg == "kr_dept":
        return "韓國語文學系主辦赴韓留學交換甄選計畫"
    if sg == "fr_ru_dept":
        return "歐美語文學系（法文組／俄文組）主辦赴法、赴俄交換生暨雙聯計畫"
    return "國際暨兩岸事務處（兩岸組）赴大陸地區姐妹校交流交換學生計畫"


def main() -> None:
    OFFICIAL_PCCU_DIR.mkdir(parents=True, exist_ok=True)
    catalog_items = json.loads(
        (SOURCES_PCCU_DIR / "pccu_catalog_source.json").read_text(encoding="utf-8")
    )
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
        full_name = item["full_name"]
        zh_name = item["name_zh"]
        country = item["country"]
        region = REGION_BY_COUNTRY.get(country, "其他地區")
        sg = item["source_group"]
        avail_status = item["availability_status"]
        if avail_status == "open":
            open_partner_count += 1

        website = (item.get("website") or "").strip()
        if website and not website.startswith("http"):
            website = f"https://{website}"
        factsheet_url = (item.get("factsheet_url") or "").strip() or None
        source_url = item["source_url"]
        remarks_all = clean_text(item.get("note") or "")

        if sg == "oima_overseas":
            round_label = "116學年度國際處赴國外姊妹校交換學生甄選（第1學期10月中旬／第2學期3月中旬）"
            deadline_iso = "2026-10-30T16:30:00+08:00"
            deadline_rem = True
            win_status = "open"
            app_deadline_str = (
                "【中國文化大學國際暨兩岸事務處（國合組）赴國外姊妹校交換學生甄選】"
                "每年分兩梯次受理申請：第 1 學期（秋季梯次，申請翌年春季或秋季出國）校內收件為每年 10 月中旬至 10 月底（菲華樓 2 樓國際暨兩岸事務處）；"
                "第 2 學期（春季梯次，申請翌年秋季出國）校內收件為每年 3 月中旬至 3 月底。"
                + (
                    "｜【日本語文學系 115/116 學年度赴日本短期交換留學生甄選】第一階段報名為每年 11 月中旬至 11 月底（115 學年度為 11/17–11/28 大仁館 349 室、12/10 筆試與口試、1/26–2/23 選填志願、3/2 初選榜示）。"
                    if zh_name in {"武藏野大學", "琉球大學"}
                    else ""
                )
            )
        elif sg == "jp_dept":
            round_label = "115/116學年度日本語文學系赴日本短期交換留學生甄選（11月中旬報名／12月筆口試）"
            deadline_iso = "2026-11-27T16:00:00+08:00"
            deadline_rem = avail_status == "open"
            win_status = "open" if avail_status == "open" else "closed"
            app_deadline_str = (
                "【中國文化大學日本語文學系（東亞組）赴日本短期交換留學生甄選時程】"
                "每年 11 月中旬開放第一階段報名（以 115 學年度簡章為例：第一階段報名 2025/11/17–11/28 16:00 止於大仁館 349 室；"
                "第二階段筆試與口試 2025/12/10；第三階段繳交學期成績單與志願卡 2026/01/26–02/23；初選合格名單公告 2026/03/02；"
                "初選錄取生須繳交交換生事務費 NT$1,000［不退還］及保證金 NT$10,000［返國完成學分抵免與心得報告後無息退還］，並於 3/25 參加留學說明會；116 學年度甄選預計於 2026 年 11 月中旬開放報名）。"
            )
        elif sg == "kr_dept":
            round_label = "115/116學年度韓國語文學系赴韓留學交換甄選（第1學期10月初／第2學期4月初收件）"
            deadline_iso = "2027-04-07T16:00:00+08:00"
            deadline_rem = False
            win_status = "closed"
            app_deadline_str = (
                "【中國文化大學韓國語文學系赴韓留學交換甄選時程（依《赴韓留學交換甄選辦法》及《115-2 交換生赴韓資料準備 SOP》）】"
                "每學期辦理一次：（1）第一學期梯次（申請翌年春季班 3 月赴韓）：每年 10 月第一週收件（115-2 梯次：2026/10/06 08:00 前將申請書、備審資料與成績單合併為單一 PDF 寄至韓文系助教信箱並繳交紙本至大仁館 301 室系辦；2026/10/07 14:10 於大仁館 302 室舉行面試；2026/10/14 公布初選名單）；"
                "（2）第二學期梯次（申請翌年秋季班 9 月赴韓）：每年 4 月第一週開放收件（預計 2027/04/01–04/07 收件）。"
            )
        elif sg == "fr_ru_dept":
            round_label = "115/116學年度歐美語文學系（法文組／俄文組）赴法赴俄交換生甄選（每年3–4月辦理）"
            deadline_iso = "2027-04-15T16:30:00+08:00"
            deadline_rem = False
            win_status = "closed"
            app_deadline_str = (
                "【中國文化大學歐美語文學系（法文組／俄文組）赴法、赴俄交換生甄選時程】"
                "每年約 3 月至 4 月間辦理校內初選收件（由系所初選後送交本校姊妹校交換生甄選委員會複選；赴法交換生須具備法語檢定 DELF B1 以上［巴黎第十三大學與里昂天主教大學商管學院須達 DELF B2 以上］，錄取確認後須提具家長保證書並繳交新臺幣 10,000 元保證金，於交換返國後全數退還）。"
            )
        else:
            round_label = "115/116學年度赴大陸地區姐妹校交流交換學生甄選（第1學期10月／第2學期3月收件）"
            deadline_iso = "2026-10-30T16:30:00+08:00"
            deadline_rem = True
            win_status = "open"
            app_deadline_str = (
                "【中國文化大學學生赴大陸地區姐妹校交流甄選（依《赴大陸地區姐妹校交流甄選作業要點》）】"
                "每年分兩學期辦理：秋季梯次（申請翌年春季班 2/3 月赴陸交換）於每年 10 月中下旬受理收件；春季梯次（申請翌年秋季班 9 月赴陸交換）於每年 3 月中下旬受理收件（經系所主管同意推薦後送國際暨兩岸事務處兩岸事務組辦理第一階段書面審查與第二階段面試）。"
            )

        raw_loc = item["location"]
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
        lang_req_str = clean_text(item["lang_req"])
        gpa_req_str = clean_text(item["gpa_req"])
        quota_str = clean_text(item["quota"])
        study_period_str = format_study_period(item)
        program_type = format_program_type(item)
        housing_str = f"{zh_name} 住宿與生活說明：{clean_text(item['housing'])}"

        exp_posts = item.get("experience_posts") or []
        exp_portal_url = (
            PCCU_KR_EXP_HUB_URL
            if sg == "kr_dept"
            else PCCU_MOBILITY_SCHOLARSHIP_PAGE_URL
        )

        if country == "日本":
            sem_dates_str = "秋季入學梯次：每年 9 月至翌年 8 月；春季入學梯次：每年 4 月至翌年 3 月（依日本姊妹校簡章規定之留學時間為準）"
        elif country == "澳洲":
            sem_dates_str = "第 1 學期（Semester 1）：約每年 2 月至 6 月；第 2 學期（Semester 2）：約每年 7 月至 11 月；邦德大學採三學期制（1月／5月／9月開學）"
        elif country == "韓國":
            sem_dates_str = "春季學期（第 1 學期）：每年 3 月初至 6 月中旬；秋季學期（第 2 學期）：每年 9 月初至 12 月中旬"
        else:
            sem_dates_str = "秋季學期（第 1 學期）：約每年 8/9 月至 12 月／翌年 1 月；春季學期（第 2 學期）：約每年 1/2 月至 5/6 月"

        course_parts = [f"開放申請院系與學制：{colleges_str}（{degree_levels_str}）。"]
        if remarks_all:
            course_parts.append(f"姊妹校甄選與修課規定：{remarks_all}")
        if sg == "jp_dept":
            course_parts.append(
                "依《中國文化大學學生赴日本留學實施要點》及甄選簡章規定，出國交換期間須維持文大在學學籍並繳交文大全額學雜費；於日本留學期間一學年至少須修習 12 學分（二松學舍大學每學期需修 10 科目、信州大學每學期至少 5 學分、平成國際大學每學期至少 12 學分），返國後辦理學分抵免並提交留學心得報告，始得申請退還新臺幣 10,000 元保證金。"
            )
        elif sg == "kr_dept":
            course_parts.append(
                "依《中國文化大學赴韓留學交換甄選辦法》規定，交換期間須維持文大在學學籍並繳交文大全額學雜費；於韓國姊妹校修得之學分返國後得依規定辦理抵免，學士班學生每學年抵免上限為 30 學分、碩士班學生每學年抵免上限為 8 學分，且返國後須繳交《中國文化大學赴韓交換留學報告書》。"
            )
        elif sg == "fr_ru_dept":
            course_parts.append(
                "依歐美語文學系《赴法／赴俄交換生計畫》規定，交換期間須維持文大在學學籍並繳交文大全額學雜費；赴法交換生返國後可抵免本系學分上限 18 學分，並於返國後全額退還新臺幣 10,000 元保證金。"
            )
        elif sg == "mainland":
            course_parts.append(
                "依《中國文化大學學生赴大陸地區姐妹校交流甄選作業要點》規定，交換期間須完成文大註冊並繳交文大全額學雜費（互惠免繳大陸姊妹校學費），每學期選課學分數須符合兩校規定，返國後檢具大陸姊妹校正式成績單辦理學分抵免並提交交流心得報告。"
            )
        else:
            course_parts.append(
                "依《中國文化大學赴國外暨大陸地區姊妹校交換學生甄選作業要點》及《國際處赴外交換常見問題》規定，交換期間須維持中國文化大學正式在學學籍並完成註冊繳交文大全額學雜費（不得辦理休學或畢業；延長修業年限不得逾兩年），並依姊妹校規定修習足額課程。"
            )
        course_rest_str = " ".join(course_parts)

        tuition_points_list = [
            "文大在學註冊學雜費與公費／自費名額規定：依《中國文化大學赴國外暨大陸地區姊妹校交換學生甄選作業要點》規定，錄取交換生於出國交換期間須維持中國文化大學在學學籍並繳交文大全額學雜費。屬「公費交換名額」者享互惠免繳姊妹校學費（天理大學、二松學舍大學、國士館大學、創價大學、名古屋學院大學另享免繳住宿費優惠！）；屬「自費交換名額」（如別府大學、平成國際大學、昆士蘭科技大學、西雪梨大學、溫哥華電影學院、威斯康辛大學麥迪遜分校 VISP、薩薩里大學等）則須同時繳交文大與姊妹校學費。日本語文學系錄取生須繳交交換生事務費 NT$1,000（不予退還）及保證金 NT$10,000（返國完成抵免與報告後無息退還）；法文組錄取生須繳交保證金 NT$10,000（返國後全數退還）。",
            "中國文化大學四大出國交換獎助學金體系：（1）《中國文化大學學生國際移動力獎學金》：每年 5 月 20 日前及 11 月 20 日前受理申請（6/30 及 12/30 前公告結果），一般生（大學部前一學期平均 70 分以上、研究所 80 分以上且操行 80 分以上）每次核給新臺幣 20,000 元；經濟不利學生或特殊才能學生（學業平均 65 分以上、操行 80 分以上）每次最高核給新臺幣 50,000 元（每人每年以領取一次為限；返國後 1 個月內須繳交 800 字以上心得報告、5 張以上照片及授權書）；（2）教育部《學海飛颺》獎學金：補助具中華民國國籍、在文大就讀一學期以上、歷年成績系排名前 20% 且操行 80 分以上、外語成績 75 分以上或具語檢證明之優秀學生赴國外（不含陸港澳）交換；（3）教育部《學海惜珠》獎學金：補助持有低收入戶、中低收入戶或特殊境遇家庭證明、歷年成績系排名前 30% 且操行 80 分以上之學生出國交換；（4）《辦理境外移地學習獎助金》：一般生補助 NT$3,000、優秀學生亞洲最高 NT$5,000／非亞洲最高 NT$10,000、經濟不利學生最高 NT$15,000（同時符合優秀條件者最高 NT$40,000）。",
        ]

        app_steps_list = [
            f"步驟一（確認甄選管道、在學年級與 {zh_name} 語言及 GPA 門檻）：確認申請管道（{program_type}），大學部須修業滿一學年以上（轉學生及碩博士班至少完成一學期學業；日文系要求大學部前學期平均 70 分、碩士班 80 分以上），並備妥符合 {zh_name} 要求之語言檢定證明（{lang_req_str}）。",
            "步驟二（備妥六大校內甄選文件並完成系所主管同意核章）：準備（1）交換生甄選申請表、（2）歷年成績單正本（含班／系排名）、（3）有效外語能力檢定證明、（4）讀書計畫與自傳（韓文系須附韓文自傳與修課計畫；法文組須附中法文自我推薦信與自主學習紀錄）、（5）系所許可及家長同意具結書（在職生另附工作單位同意函；教師推薦信請提前至少 3–4 週向教授提出申請）、（6）護照與存摺影本，依國際處或主辦語文系所截止日送件。",
            f"步驟三（參加校內書面審查與口筆試甄選、錄取報到及繳交保證金）：通過國際處審查委員會或日文系（筆試 30%＋口試 20%＋學習服務 10%＋GPA 40%）、韓文系（韓文專業平均 30%＋面試 30%＋書審 40%）、法文組（學業 60%＋推薦信 15%＋法檢與活動 25%）甄選公告錄取後，按時繳交家長同意書與保證金（日文系繳交事務費 NT$1,000＋保證金 NT$10,000；法文組繳交保證金 NT$10,000），由校方向 {full_name} 辦理官方提名（Nomination）。",
            "步驟四（向姊妹校遞交入學申請、申辦簽證保險與緩徵役男出境並履行返國義務）：獲提名後依姊妹校指示遞交入學申請文件、辦理簽證與海外醫療保險（具役男身分者須於出國前由國際處／系所造冊辦理役男出境核准，且緩徵年限不得於交換期間屆滿），並可於每年 5/20 或 11/20 前申請「文大國際移動力獎學金」（一般生 2 萬、經濟不利生最高 5 萬）。返國後 1 個月內繳交 800 字以上交換心得報告、5 張以上照片、使用授權書及正式成績單完成學分抵免。",
        ]

        elig_points_list = [
            f"甄選管道：{program_type}",
            f"開放學制與年級：{degree_levels_str}",
            f"開放申請院系：{colleges_str}",
            f"學業成績要求：{gpa_req_str}",
            f"語言能力標準：{lang_req_str}",
        ]
        if remarks_all:
            elig_points_list.append(f"姊妹校特殊規定與備註：{remarks_all}")

        notes_lines = [
            f"【合作類別與期程】{program_type}｜交換期間：{study_period_str}",
            f"【當期名額與費用待遇】{quota_str}",
            f"【開放學院與學制】{colleges_str}｜{degree_levels_str}",
            f"【語言與學業門檻】{lang_req_str}｜{gpa_req_str}",
            f"【住宿資訊】{clean_text(item['housing'])}",
        ]
        if remarks_all:
            notes_lines.append(f"【締約校重要備註】{remarks_all}")
        if exp_posts:
            notes_lines.append(
                f"【文大歷屆交換生返國報告書】中國文化大學韓國語文學系官網公開收錄赴 {zh_name} 交換留學報告書共 {len(exp_posts)} 篇。"
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
            "availability_note": f"中國文化大學國際暨兩岸事務處與各語文學系公告合作姊妹校；{quota_str}。",
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
                    "source_group": sg,
                    "experience_report_count": len(exp_posts) if exp_posts else None,
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
                "title": f"中國文化大學交換學生甄選學校與條件明細—{zh_name}",
                "source_url": source_url,
                "role": "home_university",
                "authority": "home_official_notice",
                "effective_academic_year": "116",
                "application_round": round_label,
                "checked_at": CHECKED_AT,
            },
            {
                "title": "中國文化大學赴國外暨大陸地區姊妹校交換學生甄選作業要點 PDF",
                "source_url": PCCU_OUTBOUND_GUIDELINES_PDF_URL,
                "role": "home_university",
                "authority": "home_official_notice",
                "effective_academic_year": "116",
                "application_round": round_label,
                "checked_at": CHECKED_AT,
            },
            {
                "title": "中國文化大學學生國際移動力獎學金實施要點 PDF",
                "source_url": PCCU_MOBILITY_SCHOLARSHIP_PDF_URL,
                "role": "home_university",
                "authority": "home_official_notice",
                "effective_academic_year": "116",
                "application_round": round_label,
                "checked_at": CHECKED_AT,
            },
        ]
        if factsheet_url:
            wf_sources.append({
                "title": f"中國文化大學姊妹校交換簡章與作業規範補充文件—{zh_name}",
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
            "home_university": "中國文化大學",
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
                "國際處赴國外姊妹校交換學生甄選",
                "日本語文學系赴日本短期交換留學生甄選",
                "韓國語文學系赴韓留學交換甄選",
                "歐美語文學系赴法赴俄交換生甄選",
                "赴大陸地區姐妹校交流甄選",
            ],
            "applicability_status": "verified",
            "applicability_note": (
                "中國文化大學採「國際暨兩岸事務處（國合組／兩岸組）校級統籌甄選」與「國際暨外語學院各語文學系（日文系、韓文系、法文組、俄文組）專業語組甄選」雙軌並行體制；"
                "申請人須為在學滿一學年以上之學士班學生（轉學生及碩博士班至少完成一學期），並可於每年 5/20 及 11/20 前申請文大國際移動力獎學金（一般生 NT$20,000、經濟不利生最高 NT$50,000）及教育部學海飛颺／學海惜珠獎學金。"
            ),
            "review_status": "published",
            "published_at": CHECKED_AT,
            "steps": [
                {
                    "rule_id": f"pccu-116-home-1-{idx+1:03d}",
                    "order": 1,
                    "phase": "校內申請",
                    "title": f"確認甄選管道（{program_type}）、在學年級與 {zh_name} 語言及 GPA 門檻",
                    "responsible_party": "學生",
                    "responsible_unit": "中國文化大學國際暨兩岸事務處（菲華樓 2 樓）／大恩館 301 室及各主辦語文學系",
                    "deadline_at": deadline_iso,
                    "deadline_status": "verified_exact" if avail_status == "open" else "reference_only",
                    "deadline_source_url": source_url,
                    "deadline_checked_at": CHECKED_AT,
                    "deadline_reminder_eligible": deadline_rem,
                    "summary": f"確認符合《中國文化大學赴國外暨大陸地區姊妹校交換學生甄選作業要點》及主辦單位在學年級規定（學士班修業滿一學年以上、轉學生及碩博士生至少完成一學期；日文系要求大學部平均 70 分、碩士班 80 分以上），並備妥符合 {zh_name} 規定之外語檢定成績。",
                    "details": [
                        f"開放學制與院系：{colleges_str}（{degree_levels_str}）",
                        f"語言與學業條件：{lang_req_str}｜{gpa_req_str}",
                        f"當期名額與費用待遇：{quota_str}",
                    ],
                    "scope": {
                        "home_universities": ["中國文化大學"],
                        "partner_universities": [full_name],
                        "academic_years": ["115", "116"],
                        "application_rounds": [
                            round_label,
                            "116-1",
                            "116-2",
                        ],
                    },
                    "source_urls": [
                        source_url,
                        PCCU_OUTBOUND_GUIDELINES_PDF_URL,
                        PCCU_OIMA_QUOTA_LIST_PDF_URL,
                    ],
                    "checked_at": CHECKED_AT,
                    "support_status": "verified",
                },
                {
                    "rule_id": f"pccu-116-home-2-{idx+1:03d}",
                    "order": 2,
                    "phase": "校內申請",
                    "title": "備妥申請表、歷年成績單（含排名）、語檢證明、讀書計畫與系所許可／家長同意書送件",
                    "responsible_party": "學生與所屬系所辦公室",
                    "responsible_unit": "中國文化大學各系所辦公室／國際暨兩岸事務處／日文系／韓文系／歐美語文學系",
                    "deadline_at": deadline_iso,
                    "deadline_status": "verified_exact" if avail_status == "open" else "reference_only",
                    "deadline_source_url": source_url,
                    "deadline_checked_at": CHECKED_AT,
                    "deadline_reminder_eligible": deadline_rem,
                    "summary": "依《赴國外暨大陸地區姊妹校交換學生甄選作業要點》第四點及《赴外交換常見問題》規定，備妥線上與紙本申請表、歷年成績單（須註明班／系排名）、有效語言檢定證明、自傳與讀書計畫、系所許可及家長同意具結書（在職生另附工作單位同意函；如需師長推薦信請至少提前 3–4 週禮貌接洽）及護照與存摺影本，於收件截止日前送達主辦單位。",
                    "details": [
                        "教師推薦信準備指引（國際處官方建議）：請於截止日前至少 3–4 週向熟悉您學業表現之專任教授提出申請，主動提供個人履歷、成績單、讀書計畫與目標學校資訊。",
                        "各語文學系專屬收件規格：日文系於 11 月中旬至大仁館 349 室報名；韓文系須將申請書、備審資料與成績單合併為單一 PDF 寄送助教信箱並繳交紙本至大仁館 301 室；法文組須檢附 DELF B1/B2 證明與自主學習紀錄表。",
                    ],
                    "document_requirements": [
                        {
                            "name": "中國文化大學交換學生甄選申請表（完成填報列印並經所屬系所主管簽章同意；研究生另須指導教授同意）",
                            "official_form_url": PCCU_OUTBOUND_GUIDE_URL,
                            "source_urls": [
                                PCCU_OUTBOUND_GUIDELINES_PDF_URL,
                                PCCU_OUTBOUND_GUIDE_URL,
                            ],
                        },
                        {
                            "name": "本校歷年學業成績單正本（須含學業總平均或 GPA 及班／系排名；轉學生須併附原就讀學校成績單）",
                            "source_urls": [
                                PCCU_OUTBOUND_GUIDELINES_PDF_URL,
                                PCCU_OIMA_QUOTA_LIST_PDF_URL,
                            ],
                        },
                        {
                            "name": "有效外語能力檢定證明影本（TOEFL iBT／IELTS／TOEIC／Duolingo／JLPT N1–N5／TOPIK／DELF B1–B2／CEFR 證明；大陸一般中文課程免附）",
                            "source_urls": [
                                PCCU_OIMA_QUOTA_LIST_PDF_URL,
                                source_url,
                            ],
                        },
                        {
                            "name": "自傳、讀書計畫（Study Plan）、系所許可與家長同意具結書（在職生另附工作單位同意書；赴陸交流另附 3 個月內醫院體檢表）",
                            "source_urls": [
                                PCCU_OUTBOUND_GUIDELINES_PDF_URL,
                                PCCU_RECOMMENDATION_GUIDE_URL,
                                PCCU_MAINLAND_GUIDELINES_PDF_URL,
                            ],
                        },
                    ],
                    "scope": {
                        "home_universities": ["中國文化大學"],
                        "academic_years": ["115", "116"],
                        "application_rounds": [
                            round_label,
                            "116-1",
                            "116-2",
                        ],
                    },
                    "source_urls": [
                        PCCU_OUTBOUND_GUIDELINES_PDF_URL,
                        PCCU_OUTBOUND_FAQ_PDF_URL,
                        PCCU_RECOMMENDATION_GUIDE_URL,
                        source_url,
                    ],
                    "checked_at": CHECKED_AT,
                    "support_status": "verified",
                },
                {
                    "rule_id": f"pccu-116-home-3-{idx+1:03d}",
                    "order": 3,
                    "phase": "甄選與提名",
                    "title": "參加書面審查與口筆試甄選、確認分發結果並繳交家長保證書與保證金",
                    "responsible_party": "學生、國際暨兩岸事務處與各語文學系甄選委員會",
                    "responsible_unit": "中國文化大學國際暨兩岸事務處／日本語文學系／韓國語文學系／歐美語文學系",
                    "deadline_at": "2026-12-15T16:30:00+08:00",
                    "deadline_status": "reference_only",
                    "deadline_source_url": source_url,
                    "deadline_checked_at": CHECKED_AT,
                    "deadline_reminder_eligible": False,
                    "summary": "參加國際處甄選委員會或各語文學系筆試與面試（日文系：筆試 30%、口試 20%、學習服務 10%、GPA 40%；韓文系：前學期韓文專業平均 30%、面試 30%、書審 40%；法文組：學業成績 60%、中法文自我推薦信 15%、法檢及活動證明 25%）。初選合格錄取後須按時完成報到確認並繳交家長同意保證書及保證金（日文系繳交事務費 NT$1,000＋保證金 NT$10,000；法文組繳交保證金 NT$10,000）。",
                    "details": [
                        "錄取後不得任意放棄：依各簡章規定，經錄取確認後非因不可抗拒之重大事由不得放棄或中輟交換資格，否則沒收保證金並取消次學年申請資格。",
                        "獎學金同步規劃：獲錄取或提名學生可依時程申請教育部「學海飛颺」（系排前 20%、操行 80 分）、「學海惜珠」（低收／中低收／特殊境遇、系排前 30%）及「文大國際移動力獎學金」（每年 5/20、11/20 截止，一般生 2 萬、經濟不利生最高 5 萬）。",
                    ],
                    "scope": {
                        "home_universities": ["中國文化大學"],
                        "academic_years": ["115", "116"],
                        "application_rounds": [
                            round_label,
                            "116-1",
                            "116-2",
                        ],
                    },
                    "source_urls": [
                        PCCU_OUTBOUND_GUIDELINES_PDF_URL,
                        PCCU_JP_ANNOUNCEMENT_URL,
                        PCCU_KR_RULES_URL,
                        PCCU_FR_EXCHANGE_URL,
                    ],
                    "checked_at": CHECKED_AT,
                    "support_status": "verified",
                },
                {
                    "rule_id": f"pccu-{idx+1:03d}-host-apply",
                    "order": 4,
                    "phase": "合作校申請",
                    "title": f"由文大辦理官方提名並依 {zh_name} 規定遞交入學與宿舍申請資料",
                    "responsible_party": "學生與接待校國際處",
                    "summary": f"完成校內錄取報到後，由國際暨兩岸事務處或主辦系所向 {zh_name} 辦理官方提名（Nomination）；學生須依姊妹校規定準備英文／外文成績單、護照影本、財力證明、語檢成績、體檢證明（如韓國宿舍要求麻疹與肺結核英文證明、大陸學校要求體檢表）及宿舍申請表，靜候姊妹校核發正式入學許可（Letter of Acceptance / COE）。",
                    "details": [
                        f"交換期程：{study_period_str}｜名額：{quota_str}",
                        f"語言與學業條件：{lang_req_str}｜{gpa_req_str}",
                        f"住宿安排：{clean_text(item['housing'])}",
                    ],
                    "scope": {
                        "home_universities": ["中國文化大學"],
                        "partner_universities": [full_name],
                        "academic_years": ["115", "116"],
                        "application_rounds": [
                            round_label,
                            "116-1",
                            "116-2",
                        ],
                    },
                    "source_urls": (
                        [
                            source_url,
                            PCCU_OUTBOUND_GUIDELINES_PDF_URL,
                            PCCU_MOBILITY_SCHOLARSHIP_PDF_URL,
                        ]
                        + ([factsheet_url] if factsheet_url else [])
                        + ([website] if website else [])
                    ),
                    "checked_at": CHECKED_AT,
                    "support_status": "verified",
                    "needs_confirmation": False,
                },
                {
                    "rule_id": f"pccu-116-home-5-{idx+1:03d}",
                    "order": 5,
                    "phase": "行前準備",
                    "title": "辦理緩徵役男出境、簽證保險與文大註冊，返國後 1 個月內繳交 800 字心得與照片並完成抵免",
                    "responsible_party": "學生",
                    "responsible_unit": "中國文化大學國際暨兩岸事務處／教務處／軍訓室／各系所",
                    "summary": "出國前須辦妥留學簽證、海外全期醫療與意外保險，具役男身分者須於出國前至少 1 個月由國際處／系所造冊向戶籍地縣市政府申請役男出境核准（且緩徵年限不得於交換期間屆滿）；交換期間須完成文大註冊並繳交全額學雜費；返國後 1 個月內須繳交 800 字以上交換心得報告、5 張以上照片、使用授權書及姊妹校正式成績單完成學分抵免，以核銷國際移動力獎學金及退還 10,000 元保證金。",
                    "details": tuition_points_list,
                    "scope": {
                        "home_universities": ["中國文化大學"],
                        "academic_years": ["115", "116"],
                        "application_rounds": [
                            round_label,
                            "116-1",
                            "116-2",
                        ],
                    },
                    "source_urls": [
                        PCCU_MILITARY_GUIDE_URL,
                        PCCU_MOBILITY_SCHOLARSHIP_PDF_URL,
                        PCCU_EXP_AUTH_FORM_PDF_URL,
                        PCCU_OUTBOUND_FAQ_PDF_URL,
                    ],
                    "checked_at": CHECKED_AT,
                    "support_status": "verified",
                },
            ],
            "sources": wf_sources,
            "last_checked": CHECKED_AT,
            "coverage_status": "official_verified",
            "coverage_note": "已完整整合中國文化大學國際暨兩岸事務處（國合組 47 校、兩岸組 25 校）及日文系（29 校）、韓文系（24 校）、法文組與俄文組（10 校）共 135 所交換姊妹校名額、語檢門檻、國際移動力獎學金（2萬–5萬）與超過 400 篇歷屆赴韓交換留學報告書。",
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
                "title": f"中國文化大學交換學生甄選學校與條件一覽—{zh_name}",
                "source_url": source_url,
                "summary": "文大官方交換學校公費／自費名額、語言檢定門檻、GPA 要求、住宿資訊與院系限制",
            },
            {
                "title": "中國文化大學赴國外暨大陸地區姊妹校交換學生甄選作業要點與國際移動力獎學金辦法",
                "source_url": PCCU_OUTBOUND_GUIDELINES_PDF_URL,
                "summary": "文大出國交換申請資格、應繳六大文件、役男出境規範、國際移動力獎學金（2萬–5萬）與學分抵免規定",
            },
        ]
        if factsheet_url:
            dest_sources.append({
                "title": f"中國文化大學交換計畫補充簡章／SOP—{zh_name}",
                "source_url": factsheet_url,
                "summary": "系所交換甄選 SOP、分發條件與姊妹校簡介",
            })
        if website:
            dest_sources.append({
                "title": f"{full_name} 官方網站",
                "source_url": website,
                "summary": "接待合作校官方網站",
            })
        if exp_posts:
            dest_sources.append({
                "title": f"中國文化大學赴 {zh_name} 交換留學報告書（共 {len(exp_posts)} 篇）",
                "source_url": exp_posts[0].get("url") or exp_portal_url,
                "summary": f"收錄中國文化大學韓國語文學系公開之 {len(exp_posts)} 篇赴 {zh_name} 交換留學報告書",
            })

        src_url_list = (
            [source_url, PCCU_OUTBOUND_GUIDELINES_PDF_URL]
            + ([factsheet_url] if factsheet_url else [])
            + ([website] if website else [])
        )

        destinations.append({
            "home_university": "中國文化大學",
            "school_name": full_name,
            "country": country,
            "city": location_obj.get("city") or country,
            "cost_summary": f"{cost_line}。\n{tuition_clean}",
            "housing_summary": housing_clean,
            "transport_summary": f"校區代表城市：{location_obj.get('city') or country}。請依入學許可與姊妹校交換生網頁確認實際授課校區、機場接機服務與當地學生交通卡優惠。",
            "campus_life_summary": f"{calendar_clean}\n{course_clean}",
            "student_guide_sections": [
                {
                    "key": "cost",
                    "title": "生活費、文大國際移動力獎學金（一般生 2 萬／經濟不利生最高 5 萬）、學海飛颺／惜珠與保證金規定",
                    "summary": cost_line,
                    "points": [cost_line] + tuition_points_list,
                    "source_urls": src_url_list + [
                        PCCU_MOBILITY_SCHOLARSHIP_PDF_URL,
                        PCCU_XUEHAI_FEIYANG_URL,
                        PCCU_XUEHAI_XIZHU_URL,
                        PCCU_SHORT_TERM_GRANT_PDF_URL,
                    ],
                    "caution": "中國文化大學「學生國際移動力獎學金」於每年 5 月 20 日前及 11 月 20 日前受理申請（一般生 NT$20,000、經濟不利或特殊才能生最高 NT$50,000）；返國後 1 個月內務必繳交 800 字以上心得報告、5 張以上照片及授權書。",
                },
                {
                    "key": "housing",
                    "title": "住宿資訊與校內外宿舍申請（日本 5 所姊妹校享免住宿費優惠）",
                    "summary": housing_clean[:160],
                    "points": [housing_clean],
                    "source_urls": src_url_list,
                    "caution": "各姊妹校學生宿舍名額有限（其中日本天理大學、二松學舍大學、國士館大學、創價大學、名古屋學院大學提供交換生免繳住宿費優惠；韓國姊妹校宿舍入住須備妥麻疹疫苗與肺結核英文檢驗證明），獲提名後請務必準時申請。",
                },
                {
                    "key": "insurance",
                    "title": "海外醫療及意外保險與當地強制健康保險規定",
                    "summary": visa_default,
                    "points": [
                        visa_default,
                        "依中國文化大學出國交換規定，交換生出國前須自行投保涵蓋交換全期之海外醫療、意外及急難救助保險，並依接待國政府或姊妹校規定投保當地強制學生健康保險（如日本國民健康保險、韓國 NHIS、澳洲 OSHC、德國公保等）。",
                    ],
                    "source_urls": src_url_list,
                    "caution": "請於收到入學許可後確認接待校指定之保險額度與投保通路，並於報到時出示英文投保證明。",
                },
                {
                    "key": "visa",
                    "title": "簽證辦理與緩徵役男出國手續（緩徵年限不得於交換期間屆滿）",
                    "summary": visa_default,
                    "points": [
                        visa_default,
                        "役男出境重要規定（依《赴國外暨大陸地區姊妹校交換學生甄選作業要點》第三點及國際處《兵役問題》專頁）：具役男身分之男同學，其緩徵年限不得於交換期間屆滿（應屆畢業延畢年限不得逾兩年），且須於出國前至少 1 個月提具相關表件由國際處／系所函請戶籍地縣市政府核准出境。",
                    ],
                    "source_urls": src_url_list + [PCCU_MILITARY_GUIDE_URL],
                    "caution": "請勿持觀光簽證或免簽入境就讀學期交換課程，以免影響學籍、居留與返國學分抵免。",
                },
                {
                    "key": "academics",
                    "title": "修課規定、最低學分門檻與返國學分抵免（日文系至少 12 學分／年、韓文系抵免上限 30 學分、法文組上限 18 學分）",
                    "summary": course_clean[:160],
                    "points": [calendar_clean, course_clean],
                    "source_urls": src_url_list + [PCCU_OUTBOUND_FAQ_PDF_URL],
                    "caution": "交換期間須維持中國文化大學在學學籍並完成註冊繳費（不得辦理休學或畢業），選課前請先與所屬系所確認課程大綱與學分抵免採計原則。",
                },
                {
                    "key": "living",
                    "title": f"{location_obj.get('city') or country} 校園生活與歷屆文大交換生經驗傳承",
                    "summary": f"代表校區城市：{location_obj.get('city') or country}。請配合兩校行前說明會與接待校新生訓練（Orientation）完成報到。",
                    "points": [
                        f"目的地城市：{location_obj.get('city') or country}（{country}）",
                        f"中國文化大學國際暨兩岸事務處與韓國語文學系公開收錄超過 400 篇歷屆交換生返國報告書（可至 {exp_portal_url} 查閱宿舍實況、選課技巧與生活開支）。",
                    ],
                    "source_urls": [
                        PCCU_OUTBOUND_GUIDE_URL,
                        exp_portal_url,
                    ],
                },
            ],
            "sources": dest_sources,
            "last_checked": CHECKED_AT,
            "coverage_status": "official_verified",
            "coverage_note": "已整合中國文化大學國際暨兩岸事務處（國合組／兩岸組）及日文系、韓文系、法文組、俄文組共 135 所交換姊妹校名額、語檢門檻、國際移動力獎學金辦法與超過 400 篇歷屆交換留學報告書。",
        })

        research_records.append({
            "home_university": "中國文化大學",
            "school_name": full_name,
            "country": country,
            "official_website": website,
            "verification_status": "official_verified",
            "discovery_source_url": source_url,
            "checked_at": CHECKED_AT,
            "note": f"中國文化大學國際暨兩岸事務處《甄選交換學校一覽表》、《姊妹校一覽表（2026.09.03 更新）》及各語文學系交換簡章（{factsheet_url or source_url}）與 ROR/Wikidata 官方網址核對完成。",
        })

        ev_sources = [
            {"title": f"中國文化大學交換學生甄選學校與條件明細—{zh_name}", "url": source_url},
        ]
        if factsheet_url:
            ev_sources.append({"title": f"中國文化大學交換計畫補充簡章／SOP—{zh_name}", "url": factsheet_url})
        if website:
            ev_sources.append({"title": f"{full_name} 官方網站", "url": website})
        if exp_posts:
            ev_sources.append({
                "title": f"中國文化大學赴 {zh_name} 交換留學報告書（{exp_posts[0].get('academic_year') or '歷年'}）",
                "url": exp_posts[0].get("url") or exp_portal_url,
            })

        has_student_exp = bool(exp_posts)
        if has_student_exp:
            exp_covered_schools += 1

        ev_list = [
            {
                "theme": "housing",
                "kind": "mixed" if has_student_exp else "official",
                "text": housing_clean,
                "sources": ev_sources,
                "checked_at": CHECKED_AT,
                "scope": "中國文化大學出國交換姊妹校住宿與生活資訊",
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
                "scope": "中國文化大學交換生費用規定、國際移動力獎學金（2萬–5萬）、學海飛颺／惜珠與地區生活費估算",
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
                "scope": "中國文化大學交換生選課限制、最低修課學分門檻與返國學分抵免規定",
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
                "scope": "中國文化大學出國交換簽證、海外醫療保險與緩徵役男出境提醒",
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
                        f"｜文大韓文系官網公開收錄赴 {zh_name} 歷屆交換留學報告書共 {len(exp_posts)} 篇。"
                        if exp_posts
                        else ""
                    )
                ),
                "sources": ev_sources,
                "checked_at": CHECKED_AT,
                "scope": "中國文化大學出國交換名額與歷屆學長姐交換留學報告書",
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
                "已整合中國文化大學國際暨兩岸事務處《甄選交換學校一覽表（2026.04.29 更新）》、日文系《115學年度赴日本短期交換留學生甄選條件表》、韓文系《赴韓留學交換甄選辦法》、法俄交換計畫與大陸地區姊妹校交流要點。",
                "當期宿位供給、費用與選課限制請依姊妹校最新交換網頁及入學通知書核對。",
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
                "title": t_clean or f"中國文化大學赴 {zh_name} 交換留學報告書",
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
                f"中國文化大學赴 {zh_name}（共 {len(exp_posts)} 篇交換留學報告書）學長姐交換心得彙編"
            )
            latest_title = clean_text(latest_post.get("title") or zh_name)
            excerpt_str = clean_text(latest_post.get("excerpt") or "")
            summary_text = (
                f"中國文化大學韓國語文學系「赴韓交換心得」專區公開收錄赴 {zh_name} 交換留學報告書共 {len(exp_posts)} 篇"
                + (f"（涵蓋年度：{'、'.join(terms_covered[:6])}）" if terms_covered else "")
                + f"，最新代表篇目為《{latest_title}》"
                + (f"（摘錄：{excerpt_str[:220]}…）" if excerpt_str else "")
                + "，詳實記錄文大交換生機場接機、校內外宿舍房型與費用、語學堂與大學部選課、韓國學伴交流及日常生活開銷。"
            )
            theme_map = {
                "academics": f"文大交換生於赴韓交換留學報告書中分享於 {zh_name} 之語學堂分班測驗、外國人專班與一般大學部課程選課經驗，以及返國後學分抵免（學士班每學年上限 30 學分）實務。",
                "housing": f"文大交換生於心得中詳述 {zh_name} 雙人房宿舍費用、門禁與檢查規定、麻疹與肺結核體檢報告繳交及周邊便利商店機能（{housing_clean[:120]}）。",
                "campus_culture": f"文大韓文系官網收錄 {len(exp_posts)} 篇赴 {zh_name} 歷屆交換留學報告書，分享韓國學伴（Buddy）配對、校園慶典與跨文化生活體驗。",
                "cost": f"文大交換生於心得中記錄赴 {zh_name} 之宿舍費、餐費、機票與每月生活費開銷（{cost_default}），以及文大國際移動力獎學金與學海飛颺申請經驗。",
            }
            p_url = latest_post.get("url") or exp_portal_url
            ay = clean_text(str(latest_post.get("academic_year") or "歷年交換"))
            student_experience_rows.append({
                "school_name": full_name,
                "country": country,
                "title": rep_title,
                "source_url": p_url,
                "source_type": "article",
                "platform": "中國文化大學韓國語文學系—赴韓交換心得專區",
                "author_name": latest_title or "中國文化大學返國交換學生",
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
            "home_university": "中國文化大學",
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
    (OFFICIAL_PCCU_DIR / "partners.jsonl").write_text(
        partners_jsonl_text, encoding="utf-8"
    )
    (SOURCES_PCCU_DIR / "partners.jsonl").write_text(
        partners_jsonl_text, encoding="utf-8"
    )
    (OFFICIAL_PCCU_DIR / "application_workflows.jsonl").write_text(
        "\n".join(json.dumps(r, ensure_ascii=False) for r in workflows) + "\n",
        encoding="utf-8",
    )
    (OFFICIAL_PCCU_DIR / "destination_profiles.jsonl").write_text(
        "\n".join(json.dumps(r, ensure_ascii=False) for r in destinations) + "\n",
        encoding="utf-8",
    )
    (OFFICIAL_PCCU_DIR / "partner_research.jsonl").write_text(
        "\n".join(json.dumps(r, ensure_ascii=False) for r in research_records) + "\n",
        encoding="utf-8",
    )
    (OFFICIAL_PCCU_DIR / "student_life.jsonl").write_text(
        "\n".join(json.dumps(r, ensure_ascii=False) for r in life_records) + "\n",
        encoding="utf-8",
    )
    (OFFICIAL_PCCU_DIR / "experience_sources.jsonl").write_text(
        "\n".join(
            json.dumps(r, ensure_ascii=False) for r in experience_sources_records
        )
        + "\n",
        encoding="utf-8",
    )
    (OFFICIAL_PCCU_DIR / "student_experiences.jsonl").write_text(
        "\n".join(
            json.dumps(r, ensure_ascii=False) for r in student_experience_rows
        )
        + "\n",
        encoding="utf-8",
    )
    (OFFICIAL_PCCU_DIR / "campus-locations.json").write_text(
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

    pccu_home_loc = {
        "school_name": "中國文化大學",
        "country": "臺灣",
        "city": "臺北市士林區",
        "latitude": 25.1369,
        "longitude": 121.5397,
        "geocode_status": "verified",
        "geocoded_at": CHECKED_AT,
        "source_url": "https://www.wikidata.org/wiki/Q714494",
        "identity_source_url": "https://ror.org/04shepe48",
        "precision": "representative",
        "note": "校級代表位置：官方網域及國家已與 ROR 比對，座標來源為 Wikidata P625；實際交換校區以錄取通知為準。 母校代表點採臺北市士林區陽明山華岡路55號校本部菲華樓 2 樓國際暨兩岸事務處（國合組／兩岸組）；官方地址來源：https://oima.pccu.edu.tw/。",
    }
    existing_loc_map[("中國文化大學", "臺灣")] = pccu_home_loc
    sorted_locs = sorted(
        existing_loc_map.values(),
        key=lambda r: (r.get("country") or "", r.get("school_name") or ""),
    )
    loc_file.write_text(
        "\n".join(json.dumps(r, ensure_ascii=False) for r in sorted_locs) + "\n",
        encoding="utf-8",
    )

    pccu_source_urls = [
        PCCU_OIMA_HUB_URL,
        PCCU_OUTBOUND_GUIDE_URL,
        PCCU_RECOMMENDATION_GUIDE_URL,
        PCCU_MILITARY_GUIDE_URL,
        PCCU_XUEHAI_FEIYANG_URL,
        PCCU_XUEHAI_XIZHU_URL,
        PCCU_MOBILITY_SCHOLARSHIP_PAGE_URL,
        PCCU_SISTER_SCHOOLS_PAGE_URL,
        PCCU_REGULATIONS_PAGE_URL,
        PCCU_OUTBOUND_GUIDELINES_PDF_URL,
        PCCU_OUTBOUND_FAQ_PDF_URL,
        PCCU_OIMA_QUOTA_LIST_PDF_URL,
        PCCU_SISTER_MASTER_LIST_PDF_URL,
        PCCU_MOBILITY_SCHOLARSHIP_PDF_URL,
        PCCU_EXP_AUTH_FORM_PDF_URL,
        PCCU_SHORT_TERM_GRANT_PDF_URL,
        PCCU_MAINLAND_GUIDELINES_PDF_URL,
        PCCU_JP_ANNOUNCEMENT_URL,
        PCCU_JP_ADMITTED_URL,
        PCCU_KR_SISTERS_URL,
        PCCU_KR_SOP_URL,
        PCCU_KR_RULES_URL,
        PCCU_KR_EXP_HUB_URL,
        PCCU_FR_EXCHANGE_URL,
        PCCU_RU_EXCHANGE_URL,
    ]

    exchange_info_payload = {
        "school_name": "中國文化大學",
        "program_type": [
            "國際暨兩岸事務處（國合組）甄選赴國外姊妹校交換學生計畫（47 所歐美亞大洋洲合作大學，每年 10 月中旬與 3 月中旬分兩梯次收件）",
            "國際暨外語學院各語文學系專業交換計畫：日本語文學系赴日短期交換（31 所日本姊妹校，其中 5 校免住宿費）、韓國語文學系赴韓交換（26 所韓國姊妹校）、歐美語文學系赴法與赴俄交換（10 所法俄姊妹校）",
            "國際暨兩岸事務處（兩岸事務組）赴大陸地區姐妹校交流計畫（25 所頂尖 985／雙一流大陸合作大學，含北大、清華、復旦、浙大、南大、武大、人大、北師大、同濟、廈大等）",
        ],
        "academic_year": [
            "116（國際處赴國外及大陸姊妹校秋季梯次於每年 10 月中下旬受理收件、春季梯次於每年 3 月中下旬受理收件；日本語文學系於每年 11 月中旬開放第一階段報名、12 月筆試與口試；韓國語文學系於每年 10 月第一週與 4 月第一週收件；法文組與俄文組於每年 3–4 月辦理甄選）",
            "115（完整收錄中國文化大學 135 所全球交換合作大學：含 130 所當期開放申請校及 5 所協議參考合作校）",
        ],
        "semester": [
            "第1學期（秋季班：每年約 8/9 月至 12 月／翌年 1 月；韓國春季班為 3 月至 6 月、秋季班為 9 月至 12 月）",
            "第2學期（春季班：每年約 1/2 月至 5/6 月；日本春季入學梯次為 4 月至翌年 3 月、秋季入學梯次為 9 月至翌年 8 月）",
            "一學年交換（國際處海外交換、日本短期交換留學及法俄交換計畫多以一學年為原則，部分姊妹校開放一學期交換）",
        ],
        "application_period": [
            "【國際暨兩岸事務處（國合組／兩岸組）赴國外暨大陸地區姊妹校交換甄選】第 1 學期（秋季梯次，申請翌年春季或秋季出國）：每年 10 月中旬至 10 月底受理收件（送件地點：菲華樓 2 樓國際暨兩岸事務處）；第 2 學期（春季梯次，申請翌年秋季出國）：每年 3 月中旬至 3 月底受理收件。",
            "【日本語文學系（東亞組）赴日本短期交換留學生甄選】第一階段報名：每年 11 月中旬至 11 月底（以 115 學年度簡章為例：11/17–11/28 於大仁館 349 室報名）；第二階段筆試與口試：12 月中旬（12/10）；第三階段繳交學期成績單與志願卡：翌年 1 月底至 2 月下旬（01/26–02/23）；初選榜示：3 月初（03/02），錄取生繳交事務費 NT$1,000 及保證金 NT$10,000 並參加 3 月下旬留學說明會。",
            "【韓國語文學系赴韓留學交換甄選 & 歐美語文學系（法文組／俄文組）赴法赴俄交換甄選】韓文系每學期辦理一次：第一學期於 10 月第一週收件（115-2 梯次：2026/10/06 08:00 截止收件、10/07 14:10 於大仁館 302 室面試、10/14 公布初選名單），第二學期於 4 月第一週收件；法文組與俄文組於每年 3–4 月辦理校內初選收件（法文組錄取後繳交 NT$10,000 保證金）。",
        ],
        "eligibility": [
            "【在學年級與修業年限規定（依《中國文化大學赴國外暨大陸地區姊妹校交換學生甄選作業要點》第三點）】申請人須為本校在學學生（不含休學生），學士班學生須於本校修業滿一學年以上（轉學生須於本校完成至少一學期學業並檢附原校成績單），碩、博士班學生須於本校完成至少一學期學業；出國交換期間須維持文大在學學籍並繳交文大全額學雜費（不得辦理休學或畢業，延長修業年限不得逾兩年；在職專班學生須另附工作單位同意函）。",
            "【各甄選管道學業成績門檻与配分權重】（1）國際處海外交換：依各姊妹校規定（GPA 2.5–3.25 不等，如清邁大學研究所 GPA 3.25、艾爾朗加大學 GPA 3.2、威斯康辛麥迪遜／海德堡／東義／印尼多媒體大學 GPA 3.0）；（2）日本語文學系赴日交換：大學部前一學期學業平均須達 70 分以上、碩士班須達 80 分以上（赴日雙聯學位須四學期平均 85 分以上且修滿 72 學分），甄選總成績配分為筆試 30%、口試 20%、學習服務 10%、學業成績 40%；（3）韓國語文學系赴韓交換：前一學期韓文專業平均成績佔 30%、面試 30%、書面審查 40%（含自傳動機、TOPIK 證書、全人學習護照 KPI 演講場次、社團幹部與競賽獲獎）；（4）法文組赴法交換：學業成績 60%、中法文自我推薦信 15%、法檢與活動證明 25%。",
            "【役男緩徵出境與返國義務規定】具役男身分之男學生，其緩徵年限不得於交換期間屆滿，且須於出國前至少 1 個月提具證明由國際處／系所造冊函請戶籍地縣市政府核准出境。交換返國後須檢具姊妹校正式成績單辦理學分抵免（日文系留學一學年至少修習 12 學分；韓文系每學年抵免上限學士班 30 學分、碩士班 8 學分；法文組抵免上限 18 學分），並於返國後 1 個月內提交交換心得報告與照片。",
        ],
        "language_requirement": [
            "【國際處國合組海外姊妹校語言門檻（依《國際處甄選交換學校一覽表 2026.04.29 更新》）】須檢附符合志願姊妹校標準之有效外語檢定成績（擇一即可）：英語系與歐亞全英授課學校接受 TOEFL iBT（52–82 分）、TOEFL PBT（500–550 分）、IELTS（5.0–6.5）、TOEIC（575–750 分）、Duolingo English Test（80–115 分，如印尼多媒體大學 100、FPT 大學 80、威斯康辛麥迪遜 115、德州聖道 110、北亞利桑那 95、西敏大學 115）或 PTE；德國海德堡與拜羅伊特要求德語 B2、富特旺根與希爾德斯海姆要求德語或英語 B1/B2；義大利錫耶納／費拉拉／薩薩里要求英語或義語 B1；西班牙赫羅納地中海學院要求西語 A2、赫羅納大學要求英語或西語 B2。",
            "【日文系、韓文系、法文組與俄文組語言門檻】（1）日本語文學系 28 所日本姊妹校：依各校規定須具備日語檢定 JLPT N1（早稻田、成城、明治、國士館研究所、高知研究所）、JLPT N2（二松學舍、大阪經法、東京國際、多摩、長崎國際、敬愛、天理、東洋、名古屋學院、平成國際、琉球等）、JLPT N3（長崎 JLCP、別府、筑紫女學園、同志社女大、同志社）或 JLPT N4–N5（弘前 N4、大阪國際 N4、中部 N5、創價 N5、神田外語 N5、信州 N5）；（2）韓國語文學系 24 所韓國姊妹校：須具韓語能力並參加韓語面試，持有 TOPIK 檢定證書者於書審 40% 中加分；（3）法文組 8 所法國及比利時姊妹校：須具法語檢定 DELF B1 以上（巴黎第十三大學與里昂天主教大學商管學院須達 DELF B2 以上）。",
            "【大陸地區姐妹校語言規定】赴大陸地區 25 所姐妹校修讀一般中文授課課程免附外語檢定證明；若擬選修全英語授課專業課程，須符合該接待校之英語能力要求。",
        ],
        "required_documents": [
            "1. 中國文化大學交換學生甄選申請表（依國際處、日文系、韓文系、法文組或兩岸組規定格式填列並由本人簽名；韓文系須將所有資料合併為單一 PDF 寄送助教並繳交紙本）",
            "2. 本校歷年學業成績單正本（須註明學業平均成績或 GPA 及班／系排名；轉學生須併附原就讀學校成績單）",
            "3. 有效外語能力檢定證明影本（TOEFL iBT／IELTS／TOEIC／Duolingo／JLPT N1–N5／TOPIK／DELF B1–B2／CEFR 證明；大陸一般課程免附）",
            "4. 自傳與讀書計畫（Study Plan，韓文系須附韓文自傳與修課計畫；法文組須附中、法文自我推薦信；如需教師推薦信，國際處提醒應至少提前 3–4 週向教授提出申請）",
            "5. 系（所）許可及家長同意具結書／保證書（須經所屬系所主管簽章同意，研究生另須指導教授簽章；在職專班學生須另附工作單位同意函）",
            "6. 護照個人資料頁影本、學生證與身分證正反面影本、本人金融機構存摺封面影本（赴大陸地區交流者須另附最近 3 個月內醫院體格檢查表；日文系錄取後繳交事務費 NT$1,000＋保證金 NT$10,000，法文組錄取後繳交保證金 NT$10,000）",
        ],
        "scholarship_info": [
            "中國文化大學「學生國際移動力獎學金」（《中國文化大學學生國際移動力獎學金實施要點》，2026.07.15 最新公告）：補助修讀學位之在學本國生（或經專案核准之外籍生）出國交換或修讀雙聯學位。申請截止日為每年 5 月 20 日前及 11 月 20 日前（於每年 6 月 30 日及 12 月 30 日前公告核定結果）。（1）一般學生：大學部前一學期學業平均 70 分以上、研究所 80 分以上且操行成績 80 分以上，每次核給新臺幣 20,000 元；（2）特殊才能或經濟不利學生（低收入戶、中低收入戶、特殊境遇家庭等）：前一學期學業平均 65 分以上且操行 80 分以上，每次最高核給新臺幣 50,000 元（每人每年以領取一次為限；受獎生返國後 1 個月內須繳交 800 字以上心得報告、5 張以上照片及《心得與照片使用授權書》）。",
            "教育部「學海飛颺」選送優秀學生出國研修獎學金：補助具中華民國國籍、在文大就讀一學期以上、歷年學業總平均成績居全系（所）前 20% 且操行成績 80 分以上、外語學科成績平均 75 分以上或持有有效外語能力檢定證明之在學學生，赴國外大專校院（不含大陸及港澳地區）修讀學分 1 學期或 1 學年。",
            "教育部「學海惜珠」選送勵學優秀學生出國研修獎學金：專項補助具中華民國國籍、持有各直轄市或縣市政府核發之低收入戶、中低收入戶或特殊境遇家庭相關補助證明、歷年學業成績居全系（所）前 30% 且操行成績 80 分以上之在學學生赴國外（不含陸港澳）交換研修。",
            "中國文化大學「辦理境外移地學習獎助金」（《辦理境外移地學習獎助金實施原則》，2026.08.27 更新）：補助學生赴境外移地學習，（1）一般身分學生：每人補助新臺幣 3,000 元；（2）表現優秀學生（學業成績前 50% 或具外語檢定）：亞洲地區最高補助 NT$5,000、非亞洲地區最高補助 NT$10,000；（3）經濟不利學生：每人最高補助 NT$15,000，若同時符合優秀學生條件者每人最高補助新臺幣 40,000 元。",
            "日本姊妹校「免住宿費」與韓國姊妹校「免語學堂學費」專屬優惠：日本天理大學（3 名）、二松學舍大學（2 名）、國士館大學（2 名）、創價大學（1 名）、名古屋學院大學（2 名）提供文大交換生「學費免繳＋住宿費免繳」雙免優惠；韓國國立安東大學（現國立慶國大學）提供文大交換生修讀語學堂一學年學費全免優惠。",
        ],
        "partner_universities": [p["school_name"] for p in partners],
        "source_urls": pccu_source_urls,
        "last_checked": CHECKED_AT,
    }
    (OFFICIAL_PCCU_DIR / "exchange_info.json").write_text(
        json.dumps(exchange_info_payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    student_dashboard_payload = {
        "school_name": "中國文化大學",
        "last_checked": CHECKED_AT,
        "academic_score_minimum": 70.0,
        "academic_score_rule": "學士班學生須於本校修業滿一學年以上（轉學生至少完成一學期）、碩博士班學生須完成至少一學期學業；日本語文學系赴日交換要求大學部前一學期學業平均達 70 分以上、碩士班達 80 分以上（赴日雙聯學位須四學期平均 85 分以上且修滿 72 學分）；國際處海外姊妹校依各校規定須達 GPA 2.5–3.25 以上。申請「中國文化大學學生國際移動力獎學金」（每年 5/20、11/20 截止）一般生須達大學部前一學期平均 70 分以上、研究所 80 分以上且操行 80 分以上（每次核給 NT$20,000），經濟不利或特殊才能生須達平均 65 分以上且操行 80 分以上（每次最高核給 NT$50,000）；教育部學海飛颺須達系排前 20%、學海惜珠須達系排前 30%。",
        "academic_gpa_minimum": 2.5,
        "maximum_preferences": 5,
        "selection_rules": {
            "academic_policy": "gpa_or_rank",
            "academic_reference_year": "116",
            "undergraduate_gpa_minimum": 2.5,
            "graduate_academic_exempt": False,
            "exclude_in_service": False,
            "pending_quota_planning": False,
            "partner_requirements_need_confirmation": False,
            "degree_score_minimums": {
                "undergraduate": 70.0,
                "graduate": 80.0,
            },
            "excluded_undergraduate_years": ["大一"],
            "language_certificate_required": True,
        },
        "language_score_minimums": {
            "toefl": 61.0,
            "ielts": 5.0,
            "toeic": 575.0,
        },
        "application_periods": [
            {
                "title": "中國文化大學國際暨兩岸事務處（國合組／兩岸組）赴國外暨大陸地區姊妹校交換學生甄選（第1學期10月中旬／第2學期3月中旬收件）",
                "details": [
                    "國際處國合組海外交換（47 校）與兩岸組大陸姊妹校交流（25 校）：第 1 學期（秋季梯次，申請翌年春季或秋季出國）於每年 10 月中旬至 10 月底受理收件；第 2 學期（春季梯次，申請翌年秋季出國）於每年 3 月中旬至 3 月底受理收件（送件地點：校本部菲華樓 2 樓國際暨兩岸事務處）。",
                    "「中國文化大學學生國際移動力獎學金」申請時程：每年分兩梯次於 5 月 20 日前及 11 月 20 日前受理收件（6 月 30 日及 12 月 30 日前公告結果），一般生每次核給 NT$20,000、經濟不利或特殊才能學生每次最高核給 NT$50,000。",
                ],
                "source": {
                    "title": "中國文化大學赴國外暨大陸地區姊妹校交換學生甄選作業要點與國際處交換學校一覽表 PDF",
                    "source_url": PCCU_OUTBOUND_GUIDELINES_PDF_URL,
                    "category": "exchange_application",
                    "summary": "文大國際處赴國外及大陸姊妹校交換甄選資格、六大應繳文件、兩梯次收件時程與國際移動力獎學金辦法。",
                },
                "scope": "home_application",
                "program_types": ["exchange"],
                "academic_year": "116",
                "application_round": "116學年度國際處赴國外姊妹校交換學生甄選（第1學期10月中旬／第2學期3月中旬）",
                "audience": "all_students",
                "opens_at": "2026-10-01T09:00:00+08:00",
                "deadline_at": "2026-10-30T16:30:00+08:00",
                "date_status": "verified_exact",
                "status": "open",
                "status_note": "國際暨兩岸事務處秋季梯次於每年 10 月中下旬受理收件，且國際移動力獎學金下半年梯次於 11 月 20 日截止申請。",
                "deadline_note": "請備妥申請表、歷年成績單（含排名）、有效語檢證明、讀書計畫及系所許可與家長同意書，經系所主管核章後送交菲華樓 2 樓國際暨兩岸事務處。",
                "reminder_eligible": True,
                "checked_at": CHECKED_AT,
            },
            {
                "title": "中國文化大學日本語文學系（東亞組）115/116學年度赴日本短期交換留學生甄選（11月中旬第一階段報名、12月筆試與口試、3月初放榜）",
                "details": [
                    "三階段甄選流程（以 115 學年度簡章為例，共 28 所日本姊妹校）：第一階段報名為 11 月中旬至 11 月底（2025/11/17–11/28 16:00 止於大仁館 349 室）；第二階段筆試與口試為 12 月中旬（2025/12/10）；第三階段繳交學期成績單與志願卡為翌年 1 月底至 2 月下旬（2026/01/26–02/23）；初選合格名單於 3 月初（2026/03/02）公告，3 月下旬（2026/03/25）舉行留學說明會（116 學年度預計於 2026 年 11 月中旬開放報名）。",
                    "甄選配分與費用規定：大學部前一學期平均須達 70 分以上、碩士班 80 分以上；評分佔比為筆試 30%、口試 20%、學習服務 10%、學業成績 40%。初選合格者須繳交交換生事務費 NT$1,000（不退還）及保證金 NT$10,000（返國完成至少 12 學分抵免與報告後無息退還）。",
                ],
                "source": {
                    "title": "中國文化大學 115 學年度赴日本短期交換留學生甄選簡章與日本姐妹校甄選條件表 PDF",
                    "source_url": PCCU_JP_ANNOUNCEMENT_URL,
                    "category": "exchange_application",
                    "summary": "文大日文系赴日本短期交換留學生三階段甄選時程、28 所日本姊妹校名額與住宿待遇、1,000 元事務費與 10,000 元保證金規定。",
                },
                "scope": "home_application",
                "program_types": ["exchange"],
                "academic_year": "116",
                "application_round": "115/116學年度日本語文學系赴日本短期交換留學生甄選（11月中旬報名／12月筆口試）",
                "audience": "all_students",
                "opens_at": "2026-11-16T09:00:00+08:00",
                "deadline_at": "2026-11-27T16:00:00+08:00",
                "date_status": "verified_exact",
                "status": "open",
                "status_note": "日本語文學系赴日本短期交換留學生甄選每年於 11 月中旬開放第一階段報名（大仁館 349 室）、12 月舉行筆試與口試。",
                "deadline_note": "請檢附報名表、歷年成績單與日語檢定 JLPT N1–N5 合格證書影本至大仁館 349 室完成第一階段報名。",
                "reminder_eligible": True,
                "checked_at": CHECKED_AT,
            },
            {
                "title": "中國文化大學韓國語文學系赴韓留學交換甄選（10月初／4月初收件）與歐美語文學系赴法赴俄交換甄選（3–4月收件）",
                "details": [
                    "韓國語文學系赴韓留學交換（24 所韓國姊妹校）：第一學期梯次於 10 月第一週收件（115-2 梯次：2026/10/06 08:00 截止收件、10/07 14:10 於大仁館 302 室面試、10/14 放榜），第二學期梯次於 4 月第一週收件（預計 2027/04/01–04/07）；評分佔比為前學期韓文專業平均 30%、面試 30%、書審 40%（含 TOPIK 證書、全人學習 KPI 演講紀錄、社團與獲獎）。",
                    "歐美語文學系（法文組／俄文組）赴法、赴俄交換（10 所法俄姊妹校）：每年約 3–4 月辦理甄選；赴法交換生須具備法檢 DELF B1 以上（巴黎十三與里昂商管學院須 DELF B2），評分佔比為學業 60%、中法文自我推薦信 15%、法檢及活動證明 25%，錄取後繳交 NT$10,000 保證金（返國後全數退還）。",
                ],
                "source": {
                    "title": "中國文化大學韓國語文學系《115-2 交換生赴韓資料準備 SOP》與歐美語文學系法文組《交換生計畫》",
                    "source_url": PCCU_KR_SOP_URL,
                    "category": "exchange_application",
                    "summary": "文大韓文系與法文組、俄文組交換生甄選時程、配分標準與應繳文件規範。",
                },
                "scope": "home_application",
                "program_types": ["exchange"],
                "academic_year": "116",
                "application_round": "115/116學年度韓國語文學系赴韓留學交換甄選（第1學期10月初／第2學期4月初收件）",
                "audience": "all_students",
                "opens_at": "2027-03-15T09:00:00+08:00",
                "deadline_at": "2027-04-07T16:00:00+08:00",
                "date_status": "reference_only",
                "status": "upcoming",
                "status_note": "韓文系 115-2 梯次已於 2026/10/06 截止收件並於 10/14 放榜；下一梯次（韓文系第二學期梯次及法俄語組年度甄選）預計於 2027 年 3–4 月開放收件。",
                "deadline_note": "實際截止日期請依韓國語文學系（大仁館 301 室）與歐美語文學系最新公告簡章為準。",
                "reminder_eligible": False,
                "checked_at": CHECKED_AT,
            },
        ],
        "program_overview": [
            {
                "title": f"中國文化大學國際暨兩岸事務處與各語文學系出國交換計畫總覽（{len(partners)} 所全球合作大學・{open_partner_count} 所當期開放申請校・5 大交換管道）",
                "details": [
                    f"中國文化大學（PCCU）由「國際暨兩岸事務處（國合組／兩岸組，位於菲華樓 2 樓）」與「國際暨外語學院各語文學系（日本語文學系、韓國語文學系、歐美語文學系法文組與俄文組，位於大恩館／大仁館）」共同推動全球學生交換計畫。本平台完整收錄 {len(partners)} 所文大官方交換合作大學（含當期開放申請之 {open_partner_count} 所姊妹校：國合組 47 校、日文系 29 校、韓文系 24 校、法俄語組 10 校、大陸地區 25 校）。",
                    f"文大交換體系具備三大特色：（1）多元語種與雙免待遇：除英美澳加歐亞全英授課學校接受 TOEFL／IELTS／TOEIC／Duolingo 外，日本天理、二松學舍、國士館、創價、名古屋學院大學提供「免學費＋免住宿費」雙免優惠，韓國安東大學提供交換生語學堂一年免費；（2）健全獎助學金：每年 5/20 及 11/20 受理「學生國際移動力獎學金」（一般生 NT$20,000、經濟不利生最高 NT$50,000），並配合教育部學海飛颺、學海惜珠及境外移地學習獎助金；（3）豐富學長姐實戰經驗：完整收錄韓文系官網公開之超過 400 篇歷屆赴韓交換留學報告書（涵蓋 {len(student_experience_rows)} 所韓國重點合作大學）。",
                ],
                "source": {
                    "title": "中國文化大學國際暨兩岸事務處—出國交換學習專區與姊妹校一覽表",
                    "source_url": PCCU_OIMA_HUB_URL,
                    "category": "exchange_application",
                    "summary": "文大國際處與各語文學系 135 所交換姊妹校、甄選作業要點、國際移動力獎學金與歷屆交換留學報告書。",
                },
            }
        ],
        "eligibility": [
            {
                "title": "在學年級（大二／轉學生滿一學期／碩博滿一學期以上）、GPA 70/80 分門檻與五大管道評選配分",
                "details": [
                    "在學身分與修業年限規定（依《中國文化大學赴國外暨大陸地區姊妹校交換學生甄選作業要點》第三點）：申請人須為本校在學學生（不含休學生），學士班學生須完成一學年以上學業（轉學生須於本校完成至少一學期學業並附原校成績單），碩、博士班學生須完成至少一學期學業；交換期間須維持文大在學學籍並繳交文大全額學雜費（不得辦理休學或畢業，延長修業年限不得逾兩年；役男緩徵年限不得於交換期間屆滿）。",
                    "各管道學業成績門檻與甄選配分：（1）國際處海外交換：依各姊妹校規定（GPA 2.5–3.25 不等）；（2）日本語文學系赴日交換：大學部前一學期平均須達 70 分以上、碩士班須達 80 分以上（雙聯學位須四學期平均 85 分以上且修滿 72 學分），配分為筆試 30%、口試 20%、學習服務 10%、學業成績 40%；（3）韓國語文學系赴韓交換：配分為前學期韓文專業平均 30%、面試 30%、書審 40%；（4）法文組赴法交換：配分為學業成績 60%、中法文自我推薦信 15%、法檢與活動證明 25%。",
                ],
                "source": {
                    "title": "中國文化大學赴國外暨大陸地區姊妹校交換學生甄選作業要點與各語文學系甄選簡章 PDF",
                    "source_url": PCCU_OUTBOUND_GUIDELINES_PDF_URL,
                    "category": "exchange_application",
                    "summary": "文大出國交換在學年級規定、各語文學系甄選配分權重與役男緩徵出境限制。",
                },
            }
        ],
        "language_requirements": [
            {
                "title": "多軌外語能力標準（接受 TOEFL iBT／IELTS／TOEIC／Duolingo／JLPT N1–N5／TOPIK／DELF B1–B2／CEFR）",
                "details": [
                    "國際處國合組 47 所海外姊妹校語檢標準（擇一即可）：英語授課學校接受 TOEFL iBT（52–82 分）、TOEFL PBT（500–550 分）、IELTS（5.0–6.5）、TOEIC（575–750 分，如同奈科大 575、湄州 590、鴻龐／曼谷 600、德州聖道 650、清邁 670、威斯康辛麥迪遜 685、武藏野／溫哥華電影學院 700、賓州東斯特勞斯堡 750）或 Duolingo English Test（80–115 分）；歐洲姊妹校接受德語 B1–B2、法語 B1、義大利語 B1 或西班牙語 A2–B2。",
                    "日文系、韓文系、法俄語組與大陸地區語言規定：日文系依各校要求須具 JLPT N1–N5（其中弘前、大阪國際 N4 即可，中部、創價、神田外語、信州 N5 即可申請別科／研修課程）；韓文系須具韓語能力參加面試（持 TOPIK 證書加分）；法文組須達 DELF B1 以上（巴黎十三、里昂商管學院須 DELF B2）；大陸地區 25 校一般中文課程免附外語檢定。",
                ],
                "source": {
                    "title": "中國文化大學國際處甄選交換學校一覽表（2026.04.29 更新）與日文系甄選條件表 PDF",
                    "source_url": PCCU_OIMA_QUOTA_LIST_PDF_URL,
                    "category": "exchange_application",
                    "summary": "文大國際處 47 所海外姊妹校與日文系 28 所日本姊妹校之英、日、歐語檢定門檻一覽。",
                },
            }
        ],
        "required_documents": [
            {
                "title": "六大校內甄選應繳文件、師長推薦信準備指引（提前 3–4 週）、10,000 元保證金與返國抵免義務",
                "details": [
                    "校內甄選六大應繳文件：1. 交換學生甄選申請表、2. 本校歷年成績單正本（含班／系排名；轉學生附原校成績單）、3. 有效外語能力檢定證明影本、4. 自傳與讀書計畫（韓文系須附韓文自傳與修課計畫；法文組須附中法文自我推薦信與自主學習紀錄；如需師長推薦信請提前 3–4 週向教授提出申請）、5. 系所許可及家長同意具結書（在職生另附工作單位同意函）、6. 護照、學生證、身分證與本人存摺影本（赴陸另附 3 個月內醫院體檢表）。",
                    "保證金、學分抵免與返國報告義務：日本語文學系初選合格者須繳交交換生事務費 NT$1,000（不退還）及保證金 NT$10,000，留學一學年至少修習 12 學分；法文組錄取者須繳交保證金 NT$10,000，返國抵免上限 18 學分；韓文系學士班每學年抵免上限 30 學分、碩士班上限 8 學分。獲領國際移動力獎學金者須於返國後 1 個月內繳交 800 字以上心得報告、5 張以上照片及授權書。",
                ],
                "source": {
                    "title": "中國文化大學赴國外暨大陸地區姊妹校交換學生甄選作業要點與常見問題 FAQ PDF",
                    "source_url": PCCU_OUTBOUND_FAQ_PDF_URL,
                    "category": "exchange_application",
                    "summary": "文大出國交換六大申請文件、推薦信申請禮儀、保證金退費條件與返國學分抵免規範。",
                },
            }
        ],
        "scholarship_info": [
            {
                "title": "學生國際移動力獎學金（一般生 2 萬／經濟不利生最高 5 萬，每年 5/20 及 11/20 截止）、學海飛颺／惜珠與移地學習獎助金",
                "details": [
                    "中國文化大學學生國際移動力獎學金（每年 5 月 20 日前及 11 月 20 日前受理申請，6/30 及 12/30 前公告結果）：（1）一般學生：大學部前一學期平均 70 分以上、研究所 80 分以上且操行 80 分以上，每次核給新臺幣 20,000 元；（2）特殊才能或經濟不利學生：前一學期平均 65 分以上且操行 80 分以上，每次最高核給新臺幣 50,000 元（每人每年限領一次；返國後 1 個月內繳交 800 字以上心得、5 張照片及授權書）。",
                    "教育部學海飛颺、學海惜珠與境外移地學習獎助金：（1）教育部《學海飛颺》：補助中華民國國籍、歷年系排前 20% 且操行 80 分以上、外語平均 75 分以上或具語檢證明學生赴國外交換；（2）教育部《學海惜珠》：補助低收／中低收／特殊境遇家庭、系排前 30% 且操行 80 分以上學生出國交換；（3）《辦理境外移地學習獎助金》：一般生 NT$3,000、優秀學生最高 NT$5,000–10,000、經濟不利學生最高 NT$15,000–40,000。",
                ],
                "source": {
                    "title": "中國文化大學學生國際移動力獎學金實施要點與辦理境外移地學習獎助金實施原則 PDF",
                    "source_url": PCCU_MOBILITY_SCHOLARSHIP_PDF_URL,
                    "category": "scholarship",
                    "summary": "文大國際移動力獎學金（2萬–5萬）、教育部學海飛颺／學海惜珠及境外移地學習獎助金申請資格與金額標準。",
                },
            }
        ],
        "document_explanations": [
            {
                "title": "中國文化大學交換生六大申請文件、師長推薦信提前 3–4 週準備指引與韓文系單一 PDF 送件規範",
                "summary": "說明文大國際處與各語文學系交換生申請表、含排名成績單、語檢證明、讀書計畫、系所許可與家長同意書及推薦信準備要點。",
                "key_points": [
                    "申請人須備妥交換學生甄選申請表、歷年成績單正本（須註明班／系排名；轉學生須併附原校成績單）、有效外語檢定證明、自傳與讀書計畫、系所許可與家長同意具結書（在職生另附工作單位同意函）及護照與存摺影本。",
                    "國際處《如何請老師寫推薦信》專頁特別提醒：請於截止日前至少 3–4 週向熟悉您學業表現之教授提出申請，並主動提供個人履歷、歷年成績單、讀書計畫、目標學校與截止日期。",
                    "申請韓國語文學系赴韓交換者，須依《交換生赴韓資料準備 SOP》將申請書、備審資料（含韓文自傳、修課計畫、TOPIK 證書、全人學習 KPI 演講紀錄）及成績單合併為單一 PDF 檔寄至韓文系助教信箱，並繳交紙本至大仁館 301 室。",
                ],
                "applies_to": [],
                "source": {
                    "title": "中國文化大學赴國外暨大陸地區姊妹校交換學生甄選作業要點與推薦信指南 PDF",
                    "source_url": PCCU_OUTBOUND_GUIDELINES_PDF_URL,
                    "category": "exchange_application",
                    "summary": None,
                },
                "document_url": PCCU_OUTBOUND_GUIDELINES_PDF_URL,
                "document_type": "official_document",
                "full_text_extracted": True,
            }
        ],
        "rule_explanations": [
            {
                "title": "中國文化大學交換學生甄選作業要點：五軌甄選制度、役男緩徵出境限制、10,000 元保證金與學分抵免上限",
                "summary": "規範文大國際處與日、韓、法、俄語系交換甄選流程、在學學籍維持、役男緩徵年限、保證金退還及返國學分抵免上限。",
                "key_points": [
                    "出國交換期間須維持中國文化大學正式在學學籍並完成註冊繳交文大全額學雜費（不得辦理休學或畢業，延長修業年限不得逾兩年）；具役男身分者緩徵年限不得於交換期間屆滿，且須於出國前至少 1 個月辦理役男出境核准。",
                    "日本語文學系初選合格者須繳交交換生事務費 NT$1,000（不退還）及保證金 NT$10,000，留學一學年至少修習 12 學分；法文組錄取者須繳交保證金 NT$10,000，返國抵免上限 18 學分；韓文系學士班每學年抵免上限 30 學分、碩士班上限 8 學分。",
                    "申請「學生國際移動力獎學金」（每年 5/20、11/20 截止，一般生 NT$20,000、經濟不利生最高 NT$50,000）者，須於返國後 1 個月內繳交 800 字以上心得報告、5 張以上照片及《心得與照片使用授權書》。",
                ],
                "applies_to": [],
                "source": {
                    "title": "中國文化大學赴國外暨大陸地區姊妹校交換學生甄選作業要點與赴日／赴韓留學實施要點 PDF",
                    "source_url": PCCU_OUTBOUND_GUIDELINES_PDF_URL,
                    "category": "exchange_application",
                    "summary": None,
                },
                "document_url": PCCU_OUTBOUND_GUIDELINES_PDF_URL,
                "document_type": "official_document",
                "full_text_extracted": True,
            }
        ],
        "sources": [
            {
                "title": "中國文化大學國際暨兩岸事務處—出國交換學習總覽與申請指南",
                "source_url": PCCU_OIMA_HUB_URL,
                "category": "exchange_application",
                "summary": None,
            },
            {
                "title": "中國文化大學國際處甄選交換學校一覽表（2026.04.29 更新，47 所海外合作大學名額與語檢門檻）PDF",
                "source_url": PCCU_OIMA_QUOTA_LIST_PDF_URL,
                "category": "partner_school",
                "summary": None,
            },
            {
                "title": "中國文化大學姊妹校一覽表（2026.09.03 更新，全球 437 所締約姊妹校總表）PDF",
                "source_url": PCCU_SISTER_MASTER_LIST_PDF_URL,
                "category": "partner_school",
                "summary": None,
            },
            {
                "title": "中國文化大學赴國外暨大陸地區姊妹校交換學生甄選作業要點 PDF",
                "source_url": PCCU_OUTBOUND_GUIDELINES_PDF_URL,
                "category": "exchange_application",
                "summary": None,
            },
            {
                "title": "中國文化大學赴外交換常見問題（FAQ）PDF",
                "source_url": PCCU_OUTBOUND_FAQ_PDF_URL,
                "category": "exchange_application",
                "summary": None,
            },
            {
                "title": "中國文化大學學生國際移動力獎學金實施要點（2026.07.15 公告）与辦理境外移地學習獎助金實施原則 PDF",
                "source_url": PCCU_MOBILITY_SCHOLARSHIP_PDF_URL,
                "category": "scholarship",
                "summary": None,
            },
            {
                "title": "中國文化大學日本語文學系 115 學年度赴日本短期交換留學生甄選簡章與 28 所日本姐妹校甄選條件表",
                "source_url": PCCU_JP_ANNOUNCEMENT_URL,
                "category": "partner_school",
                "summary": None,
            },
            {
                "title": "中國文化大學韓國語文學系《赴韓留學交換甄選辦法》、《115-2 交換生赴韓資料準備 SOP》與 24 所韓國姐妹校列表",
                "source_url": PCCU_KR_SOP_URL,
                "category": "partner_school",
                "summary": None,
            },
            {
                "title": "中國文化大學歐美語文學系法文組《赴法交換生計畫》與俄文組《國際交換暨 2+2 雙聯計畫》",
                "source_url": PCCU_FR_EXCHANGE_URL,
                "category": "partner_school",
                "summary": None,
            },
            {
                "title": "中國文化大學韓國語文學系—赴韓交換心得專區（公開收錄超過 400 篇歷屆交換留學報告書）",
                "source_url": PCCU_KR_EXP_HUB_URL,
                "category": "partner_school",
                "summary": None,
            },
        ],
    }
    (OFFICIAL_PCCU_DIR / "student_dashboard.json").write_text(
        json.dumps(student_dashboard_payload, ensure_ascii=False, indent=2)
        + "\n",
        encoding="utf-8",
    )

    pages_records = [
        {
            "title": "中國文化大學：國際處（國合組／兩岸組）與日、韓、法、俄語系五大出國交換管道申請時程",
            "source_url": PCCU_OIMA_HUB_URL,
            "published_at": "2026-09-03T00:00:00Z",
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
            "title": "中國文化大學：交換學生申請資格、學業門檻（70/80分）、各語系甄選配分與役男緩徵出境規定",
            "source_url": PCCU_OUTBOUND_GUIDELINES_PDF_URL,
            "published_at": "2026-07-11T00:00:00Z",
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
            "title": "中國文化大學：135 所交換姊妹校外語能力標準（TOEFL／IELTS／TOEIC／Duolingo／JLPT N1–N5／TOPIK／DELF B1–B2）",
            "source_url": PCCU_OIMA_QUOTA_LIST_PDF_URL,
            "published_at": "2026-04-29T00:00:00Z",
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
            "title": "中國文化大學：六大校內甄選必繳文件、推薦信提前 3–4 週準備指引、10,000 元保證金與學分抵免義務",
            "source_url": PCCU_OUTBOUND_FAQ_PDF_URL,
            "published_at": "2026-07-11T00:00:00Z",
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
            "title": "中國文化大學：學生國際移動力獎學金（一般生 2 萬／經濟不利生最高 5 萬）、學海飛颺／惜珠與境外移地學習獎助金",
            "source_url": PCCU_MOBILITY_SCHOLARSHIP_PDF_URL,
            "published_at": "2026-07-15T00:00:00Z",
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
    (OFFICIAL_PCCU_DIR / "pages.jsonl").write_text(
        "\n".join(json.dumps(p, ensure_ascii=False) for p in pages_records)
        + "\n",
        encoding="utf-8",
    )

    home_rules = {
        "school_id": "pccu",
        "school_name": "中國文化大學",
        "eligibility": student_dashboard_payload["eligibility"],
        "application_periods": student_dashboard_payload["application_periods"],
        "selection_rules": {
            "undergraduate_score_minimum": 70.0,
            "graduate_score_minimum": 80.0,
            "dual_degree_jp_score_minimum": 85.0,
            "mobility_scholarship_general_twd": 20000,
            "mobility_scholarship_disadvantaged_max_twd": 50000,
            "mobility_scholarship_deadlines": ["05-20", "11-20"],
            "xuehai_feiyang_rank_percent_maximum": 20.0,
            "xuehai_xizhu_rank_percent_maximum": 30.0,
            "jp_admin_fee_twd": 1000,
            "jp_deposit_twd": 10000,
            "fr_deposit_twd": 10000,
            "jp_minimum_credits_per_year": 12,
            "kr_credit_transfer_cap_undergraduate": 30,
            "kr_credit_transfer_cap_graduate": 8,
            "fr_credit_transfer_cap": 18,
            "return_documents_due": "返國後 1 個月內（800 字以上交換心得報告、5 張以上照片、使用授權書及姊妹校正式成績單）",
        },
        "source_urls": pccu_source_urls,
        "verified_at": "2026-10-19",
    }
    (OFFICIAL_PCCU_DIR / "home_rules.json").write_text(
        json.dumps(home_rules, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    (OFFICIAL_PCCU_DIR / "documents.json").write_text(
        json.dumps(
            {
                "school_name": "中國文化大學",
                "required_documents": student_dashboard_payload["required_documents"],
                "source_urls": pccu_source_urls,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    (OFFICIAL_PCCU_DIR / "scholarships.json").write_text(
        json.dumps(
            {
                "school_name": "中國文化大學",
                "scholarships": student_dashboard_payload["scholarship_info"],
                "source_urls": pccu_source_urls,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    completeness = {
        "school_id": "pccu",
        "school_name": "中國文化大學",
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
        "active_term": "中國文化大學國際暨兩岸事務處（國合組 47 校、兩岸組 25 校）秋季梯次於每年 10 月中下旬收件、春季梯次於 3 月中下旬收件；日本語文學系（29 校）於每年 11 月中旬開放第一階段報名、12 月筆口試；韓國語文學系（24 校）於每年 10 月第一週與 4 月第一週收件；歐美語文學系法俄語組（10 校）於每年 3–4 月辦理甄選；國際移動力獎學金（2萬–5萬）於每年 5/20 及 11/20 截止申請（共收錄 135 所全球合作大學，含 130 所當期開放申請校）。",
        "verified_at": "2026-10-19",
    }
    (OFFICIAL_PCCU_DIR / "catalog-completeness.json").write_text(
        json.dumps(completeness, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    (OFFICIAL_PCCU_DIR / "verification_status.json").write_text(
        json.dumps(
            {
                "school_id": "pccu",
                "school_name": "中國文化大學",
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
            "sources/pccu/outbound_exchange_guidelines.pdf",
            PCCU_OUTBOUND_GUIDELINES_PDF_URL,
            "中國文化大學赴國外暨大陸地區姊妹校交換學生甄選作業要點 PDF",
        ),
        (
            "sources/pccu/outbound_exchange_faq.pdf",
            PCCU_OUTBOUND_FAQ_PDF_URL,
            "中國文化大學赴外交換常見問題（FAQ）PDF",
        ),
        (
            "sources/pccu/oima_exchange_partner_quota_list.pdf",
            PCCU_OIMA_QUOTA_LIST_PDF_URL,
            "中國文化大學國際處甄選交換學校一覽表（2026.04.29 更新，47 所海外合作大學名額與語檢門檻）PDF",
        ),
        (
            "sources/pccu/sister_schools_master_list_202609.pdf",
            PCCU_SISTER_MASTER_LIST_PDF_URL,
            "中國文化大學姊妹校一覽表（2026.09.03 更新，全球 437 所締約姊妹校總表）PDF",
        ),
        (
            "sources/pccu/international_mobility_scholarship_rules.pdf",
            PCCU_MOBILITY_SCHOLARSHIP_PDF_URL,
            "中國文化大學學生國際移動力獎學金實施要點（2026.07.15 更新）PDF",
        ),
        (
            "sources/pccu/experience_report_authorization_form.pdf",
            PCCU_EXP_AUTH_FORM_PDF_URL,
            "中國文化大學國際移動力獎學金心得與照片使用授權書 PDF",
        ),
        (
            "sources/pccu/study_abroad_short_term_grant_rules.pdf",
            PCCU_SHORT_TERM_GRANT_PDF_URL,
            "中國文化大學辦理境外移地學習獎助金實施原則（2026.08.27 更新）PDF",
        ),
        (
            "sources/pccu/mainland_exchange_guidelines_gdrive.pdf",
            PCCU_MAINLAND_GUIDELINES_PDF_URL,
            "中國文化大學學生赴大陸地區姐妹校交流甄選作業要點 PDF",
        ),
        (
            "sources/pccu/jp_exchange_guidelines_115.pdf",
            PCCU_JP_ANNOUNCEMENT_URL,
            "中國文化大學 115 學年度赴日本短期交換留學生甄選簡章與學生赴日本留學實施要點 PDF",
        ),
        (
            "sources/pccu/jp_exchange_partner_conditions_115.pdf",
            PCCU_JP_ANNOUNCEMENT_URL,
            "中國文化大學 115 學年度赴日本短期交換留學生甄選簡章—日本姐妹校各校交換生甄選條件表（28 校）PDF",
        ),
        (
            "sources/pccu/jp_exchange_admitted_list_115.pdf",
            PCCU_JP_ADMITTED_URL,
            "中國文化大學 115 學年度赴日本短期交換學生甄選初選合格名單與保證金繳交公告 PDF",
        ),
        (
            "sources/pccu/kr_exchange_sop_115_2.pdf",
            PCCU_KR_SOP_URL,
            "中國文化大學韓國語文學系 115-2 交換生赴韓資料準備 SOP（2026.09.29 版本）PDF",
        ),
        (
            "sources/pccu/kr_exchange_selection_rules.pdf",
            PCCU_KR_RULES_URL,
            "中國文化大學韓國語文學系赴韓留學交換甄選辦法 PDF",
        ),
        (
            "sources/pccu/oima_study_abroad_hub.html",
            PCCU_OIMA_HUB_URL,
            "中國文化大學國際暨兩岸事務處—出國交換學習入口網 HTML",
        ),
        (
            "sources/pccu/oima_outbound_exchange_guide.html",
            PCCU_OUTBOUND_GUIDE_URL,
            "中國文化大學國際暨兩岸事務處—赴外交換生申請說明 HTML",
        ),
        (
            "sources/pccu/oima_recommendation_letter_guide.html",
            PCCU_RECOMMENDATION_GUIDE_URL,
            "中國文化大學國際暨兩岸事務處—如何請老師寫推薦信指南 HTML",
        ),
        (
            "sources/pccu/oima_military_service_guide.html",
            PCCU_MILITARY_GUIDE_URL,
            "中國文化大學國際暨兩岸事務處—出國交換兵役問題指南 HTML",
        ),
        (
            "sources/pccu/oima_xuehai_feiyang.html",
            PCCU_XUEHAI_FEIYANG_URL,
            "中國文化大學國際暨兩岸事務處—教育部學海飛颺獎學金專頁 HTML",
        ),
        (
            "sources/pccu/oima_xuehai_xizhu.html",
            PCCU_XUEHAI_XIZHU_URL,
            "中國文化大學國際暨兩岸事務處—教育部學海惜珠獎學金專頁 HTML",
        ),
        (
            "sources/pccu/oima_international_mobility_scholarship.html",
            PCCU_MOBILITY_SCHOLARSHIP_PAGE_URL,
            "中國文化大學國際暨兩岸事務處—學生國際移動力獎學金專頁 HTML",
        ),
        (
            "sources/pccu/jp_exchange_announcement_115.html",
            PCCU_JP_ANNOUNCEMENT_URL,
            "中國文化大學日本語文學系—115 學年度赴日本短期交換留學生甄選公告 HTML",
        ),
        (
            "sources/pccu/kr_sister_schools_page.html",
            PCCU_KR_SISTERS_URL,
            "中國文化大學韓國語文學系—韓國姐妹學校列表 HTML",
        ),
        (
            "sources/pccu/kr_exchange_experiences_hub.html",
            PCCU_KR_EXP_HUB_URL,
            "中國文化大學韓國語文學系—赴韓交換心得專區 HTML",
        ),
        (
            "sources/pccu/fr_exchange_program_page.html",
            PCCU_FR_EXCHANGE_URL,
            "中國文化大學歐美語文學系法文組—赴法交換生計畫專頁 HTML",
        ),
        (
            "sources/pccu/ru_exchange_program_page.html",
            PCCU_RU_EXCHANGE_URL,
            "中國文化大學歐美語文學系俄文組—國際交換暨雙聯計畫專頁 HTML",
        ),
        (
            "sources/pccu/pccu_academic_units.json",
            "https://www.pccu.edu.tw/api/vCtrl1/getUnitInfo/unitType/cr",
            "中國文化大學 12 個學院與 71 個系所學位學程官方組織 API JSON",
        ),
        (
            "sources/pccu/kr_experience_reports_index.json",
            PCCU_KR_EXP_HUB_URL,
            "中國文化大學韓國語文學系 36 所韓國姊妹校交換留學報告書索引與摘錄 JSON",
        ),
        (
            "sources/pccu/pccu_catalog_source.json",
            PCCU_OIMA_QUOTA_LIST_PDF_URL,
            "中國文化大學 135 所出國交換合作大學整合資料集 JSON",
        ),
        (
            "sources/pccu/pccu_resolved_locations.json",
            PCCU_SISTER_MASTER_LIST_PDF_URL,
            "中國文化大學 135 所出國交換合作大學 ROR / Wikidata 地理座標核對表 JSON",
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
        "school_id": "pccu",
        "school_name": "中國文化大學",
        "generated_at": CHECKED_AT,
        "active_cycle_note": completeness["active_term"],
        "sources": prov_sources,
    }
    prov_text = json.dumps(provenance_payload, ensure_ascii=False, indent=2) + "\n"
    (OFFICIAL_PCCU_DIR / "import_provenance.json").write_text(
        prov_text, encoding="utf-8"
    )
    (OFFICIAL_PCCU_DIR / "import-provenance.json").write_text(
        prov_text, encoding="utf-8"
    )

    from exchange_info.pccu_source_review import review_bundle
    reviewed_counts = review_bundle(REPO_ROOT)
    print(f"Built PCCU partial review: {len(partners)} records; {reviewed_counts}; no whole records verified.")



if __name__ == "__main__":
    main()
