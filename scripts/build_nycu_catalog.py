"""Build the official National Yang Ming Chiao Tung University (國立陽明交通大學, NYCU) exchange data bundle."""

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

SOURCES_NYCU_DIR = REPO_ROOT / "sources" / "nycu"
OFFICIAL_NYCU_DIR = REPO_ROOT / "src" / "exchange_info" / "official_data" / "nycu"
STATIC_DIR = REPO_ROOT / "src" / "exchange_info" / "static"

CHECKED_AT = "2026-10-19T12:00:00Z"

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
    "阿根廷": "美洲",
    "澳洲": "大洋洲",
    "紐西蘭": "大洋洲",
    "法屬玻里尼西亞": "大洋洲",
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
        "CAD 1,500–2,200 / 月（含溫哥華／多倫多／滑鐵盧／維多利亞住宿、膳食、省級或校內醫保與市區交通）",
        "須投保接待校指定醫療保險並辦理 Study Permit 或 eTA。",
    ),
    "墨西哥": (
        "USD 650–1,000 / 月（含蒙特雷／墨西哥城學生住宿、餐飲與日常交通）",
        "交換逾 180 天須向墨西哥駐臺辦事處申辦學生簽證並投保海外全期醫療保險。",
    ),
    "智利": (
        "USD 700–1,100 / 月（含聖地牙哥學生住宿、餐飲與大眾運輸）",
        "須向智利商務辦事處申辦學生簽證並投保涵蓋全交換期間之海外醫療保險。",
    ),
    "秘魯": (
        "USD 600–950 / 月（含利馬學生住宿、膳食與日常交通）",
        "須依接待校指引申辦秘魯交換學生簽證並投保海外醫療及意外保險。",
    ),
    "阿根廷": (
        "USD 600–950 / 月（含布宜諾斯艾利斯學生住宿、膳食與市區交通）",
        "須向阿根廷商務文化辦事處申辦學生簽證並投保海外醫療及意外保險。",
    ),
    "英國": (
        "GBP 1,100–1,600 / 月（倫敦約 GBP 1,350–1,850 / 月；修咸頓、艾克斯特、史崔克萊、薩ссе克斯約 GBP 1,000–1,400 / 月）",
        "交換一學期（6 個月內）可辦理 Standard Visitor 簽證，一學年須辦理 Student Visa 並繳納 IHS 醫療附加費。",
    ),
    "法國": (
        "EUR 850–1,450 / 月（巴黎地區約 EUR 1,050–1,550 / 月；里昂、圖盧茲、格勒諾布爾、南特、貢比涅約 EUR 750–1,150 / 月，可申請 CAF 房補）",
        "須透過法國教育中心（Campus France）完成面試並申辦長期學生簽證（VLS-TS）。",
    ),
    "德國": (
        "EUR 934–1,250 / 月（德國簽證限制提領帳戶基準為每月 EUR 934）",
        "須辦理德國法定公保（約 EUR 120–130 / 月）及繳納學期雜費／學期交通票（Semesterticket）。",
    ),
    "奧地利": (
        "EUR 850–1,250 / 月（含維也納／林茲／格拉茨／克拉根福學生宿舍、餐飲與大眾運輸）",
        "交換一學期（6 個月內）須申辦奧地利學生簽證 D（Visa D），超過 6 個月須申辦學生居留許可。",
    ),
    "西班牙": (
        "EUR 800–1,300 / 月（含馬德里／巴塞隆納／瓦倫西亞／塞維亞學生公寓、飲食與大眾運輸）",
        "須備妥涵蓋全額醫療與遺體運返之私人醫療保險以申辦西班牙學生簽證。",
    ),
    "義大利": (
        "EUR 850–1,350 / 月（含米蘭、羅馬、波隆那、帕多瓦、威尼斯學生住宿、餐飲與大眾運輸）",
        "須向義大利經濟貿易文化推廣辦事處申辦學生簽證 D，抵義後 8 個工作天內申辦居留證（Permesso di Soggiorno）。",
    ),
    "荷蘭": (
        "EUR 950–1,450 / 月（荷蘭移民局 IND 財力證明基準約 EUR 1,225 / 月）",
        "由接待校代辦 MVV/VVR 居留許可，阿姆斯特丹、萊頓、馬斯垂克與屯特房源緊張建議獲提名後立即申請宿舍。",
    ),
    "比利時": (
        "EUR 850–1,300 / 月（含魯汶／根特／布魯塞爾／列日／蒙斯學生宿舍、餐飲與大眾運輸）",
        "須辦理長期學生簽證 D 簽，抵達後向當地市政廳登記居留。",
    ),
    "瑞士": (
        "CHF 1,500–2,200 / 月（含蘇黎世／伯恩／溫特圖爾學生住宿、膳食與強制保險）",
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
        "EUR 1,000–1,450 / 月（含奧斯陸／特隆赫姆學生宿舍與日常開支）",
        "須向挪威移民局（UDI）申辦學生居留許可。",
    ),
    "芬蘭": (
        "EUR 800–1,200 / 月（含埃斯波／奧盧／坦佩雷／土庫學生公寓、學生餐廳與當地交通）",
        "須透過 Enter Finland 申辦芬蘭學生居留許可並備妥規定醫療保險。",
    ),
    "立陶宛": (
        "EUR 600–900 / 月（維爾紐斯與考納斯學生宿舍與生活費用實惠）",
        "須透過 MIGRIS 系統申辦立陶宛國家簽證（D 簽）或臨時居留許可。",
    ),
    "波蘭": (
        "EUR 550–850 / 月（約 PLN 2,400–3,600，華沙與克拉科夫校內宿舍實惠）",
        "須向波蘭臺北辦事處申辦 D 類國別學生簽證並備妥規定旅行醫療保險。",
    ),
    "捷克": (
        "EUR 600–900 / 月（含布拉格／布爾諾／赫拉德茨-克拉洛韋學生宿舍、食堂與市區交通卡）",
        "須提前預約捷克經濟文化辦事處申辦長期學生簽證與捷克合約醫療保險。",
    ),
    "匈牙利": (
        "EUR 600–950 / 月（含布達佩斯學生住宿、膳食與大眾運輸）",
        "須申辦匈牙利長期學生居留簽證（D 簽）並備妥歐盟規格醫療保險。",
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
        "USD 1,000–1,500 / 月（含海法／耶路撒冷學生宿舍、餐飲與大眾運輸）",
        "須向駐臺北以色列經濟文化辦事處申辦 A/2 學生簽證並投保接待校指定醫療保險。",
    ),
    "澳洲": (
        "AUD 1,800–2,600 / 月（含雪梨／布里斯本／臥龍崗／阿德雷德住宿與日常開支）",
        "須購買澳洲海外學生健康保險（OSHC）並線上申辦 Subclass 500 學生簽證。",
    ),
    "紐西蘭": (
        "NZD 1,600–2,300 / 月（含威靈頓住宿與日常開支）",
        "須向紐西蘭移民局線上申辦 Exchange Student Visa 並投保合規醫療險。",
    ),
    "法屬玻里尼西亞": (
        "EUR 900–1,400 / 月（含大溪地普納奧亞學生住宿與日常開支）",
        "須向法國在臺協會申辦法屬玻里尼西亞長期學生簽證並投保海外醫療保險。",
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
    "新加坡": (
        "SGD 1,200–1,900 / 月（含新加坡國立大學／南洋理工大學／新加坡科技設計大學住宿與日常開支）",
        "獲錄取後由接待校透過 SOLAR 系統協助申辦新加坡 Student's Pass（STP）。",
    ),
    "馬來西亞": (
        "MYR 1,500–2,500 / 月（吉隆坡、檳城與馬六甲生活機能便利且物價親民）",
        "須透過 EMGS（Education Malaysia Global Services）系統申辦學生簽證（VAL / Student Pass）。",
    ),
    "汶萊": (
        "SGD 700–1,200 / 月（汶萊元 BND 與新加坡幣 SGD 1:1 等值，含斯里巴加灣市校內宿舍與日常開支）",
        "須透過接待校向汶萊移民局申辦學生簽證（Student Pass）並投保醫療保險。",
    ),
    "泰國": (
        "THB 15,000–25,000 / 月（曼谷與巴吞他尼府生活成本親民）",
        "須憑接待校入學許可向泰國貿易經濟辦事處申辦 Non-Immigrant ED 學生簽證。",
    ),
    "印尼": (
        "IDR 5,000,000–9,000,000 / 月（萬隆、泗水與雅加達生活開支實惠）",
        "須由接待校協助向印尼移民總局申辦學習簽證（C316 / 學生電子簽證）。",
    ),
    "越南": (
        "USD 400–700 / 月（約 VND 10,000,000–17,000,000，河內生活成本低廉）",
        "須憑接待校入學許可透過駐臺北越南經濟文化辦事處申辦 DH 學生簽證。",
    ),
    "菲律賓": (
        "USD 500–850 / 月（約 PHP 28,000–48,000，馬尼拉住宿與生活開支）",
        "須憑接待校入學許可向馬尼拉經濟文化辦事處申辦 9(f) 學生簽證或 SSP 特別學習許可。",
    ),
    "印度": (
        "USD 400–700 / 月（印度理工學院各校區與印度科學理工學院住宿與日常開支實惠）",
        "須憑接待校正式入學許可向印度台北協會申辦 Student Visa。",
    ),
}

NYCU_OIA_HOME_URL = "https://oia.nycu.edu.tw/"
NYCU_OUTBOUND_TIMELINE_URL = "https://oia.nycu.edu.tw/oia/ch/app/artwebsite/view?module=artwebsite&id=279&serno=7a94f43d-a0ac-435e-9c2c-f99573ff26ba"
NYCU_PORTAL_URL = "https://oia-sys.nycu.edu.tw/outgoing"
NYCU_QUOTA_SHEET_URL = "https://docs.google.com/spreadsheets/d/1MjFpOfI77e4-yQWc3dHuukoR9MJB6ZndldtSFfXiyj4/edit?gid=114872685"
NYCU_CONTRACTS_SHEET_URL = "https://docs.google.com/spreadsheets/d/1XGeMX1F-niYApCrtge7n5f_YfsLZ1uZrp3ckdp-35UQ/edit?usp=sharing"
NYCU_DUAL_DEGREE_SHEET_URL = "https://docs.google.com/spreadsheets/d/10zt_cwrlv7HvZ6evw5NkIhS1tHhMjaxaUSB896nJBJ0/edit?usp=sharing"
NYCU_115_2_NOTICE_URL = "https://oia.nycu.edu.tw/oia/ch/app/data/view?module=nycu0006&id=286&serno=1aa55bc9-92e8-4d5c-b5d2-4286ae7af98d"
NYCU_115_1_NOTICE_URL = "https://oia.nycu.edu.tw/oia/ch/app/data/view?module=nycu0006&id=286&serno=d277af55-a210-42fc-be35-f9c549923c50"
NYCU_116_1_UST_NOTICE_URL = "https://oia.nycu.edu.tw/oia/ch/app/data/view?module=nycu0006&id=286&serno=8ee14cf9-321b-46af-9871-9d154c9e6647"
NYCU_115_2_GUIDELINES_PDF_URL = "https://oia.nycu.edu.tw/oia/ch/app/data/doc?module=nycu0006&detailNo=1501852894511501312&type=s"
NYCU_115_2_APPROVAL_FORM_PDF_URL = "https://oia.nycu.edu.tw/oia/ch/app/data/doc?module=nycu0006&detailNo=1501852894419226624&type=s"
NYCU_115_1_GUIDELINES_PDF_URL = "https://oia.nycu.edu.tw/oia/ch/app/data/doc?module=nycu0006&detailNo=1442785684455690240&type=s"
NYCU_REGULATIONS_PAGE_URL = "https://oia.nycu.edu.tw/oia/ch/app/data/view?module=nycu0014&id=4666&serno=8ac10576-c802-44b9-b160-df69a8465fb1"
NYCU_REGULATIONS_ZH_PDF_URL = "https://oia.nycu.edu.tw/oia/ch/app/data/doc?module=nycu0014&detailNo=1191618147807924224&type=s"
NYCU_REGULATIONS_EN_PDF_URL = "https://oia.nycu.edu.tw/oia/ch/app/data/doc?module=nycu0014&detailNo=1191618147837284352&type=s"
NYCU_SCHOLARSHIP_LIST_URL = "https://oia.nycu.edu.tw/oia/ch/app/data/list?module=nycu0007&id=300"
NYCU_SCHOLARSHIP_NOTICE_URL = "https://oia.nycu.edu.tw/oia/ch/app/data/view?module=nycu0007&id=300&serno=3cedb955-844b-4b3f-838f-fbe05d65eda3"
NYCU_SCHOLARSHIP_TYPE_A_PDF_URL = "https://oia.nycu.edu.tw/oia/ch/app/data/doc?module=nycu0007&detailNo=1202824643027668992&type=s"
NYCU_SCHOLARSHIP_TYPE_B_PDF_URL = "https://oia.nycu.edu.tw/oia/ch/app/data/doc?module=nycu0007&detailNo=1202824643048640512&type=s"
NYCU_ECON_DISADVANTAGED_URL = "https://oia.nycu.edu.tw/oia/ch/app/data/view?module=nycu0007&id=300&serno=70d0ebde-b4d4-4cdf-8973-c1ab8ee89a29"
NYCU_ECON_DISADVANTAGED_PDF_URL = "https://oia.nycu.edu.tw/oia/ch/app/data/doc?module=nycu0007&detailNo=1429663456809717760&type=s"
NYCU_UST_NOTICE_PDF_URL = "https://oia.nycu.edu.tw/oia/ch/app/data/doc?module=nycu0006&detailNo=1552119722735046656&type=s"
NYCU_DUAL_DEGREE_INTRO_URL = "https://oia.nycu.edu.tw/oia/ch/app/artwebsite/view?module=artwebsite&id=358&serno=c0f99f93-bf4a-42f0-ab38-058eb0081f7c"
NYCU_EXPERIENCE_ASIA_URL = "https://oia.nycu.edu.tw/oia/ch/app/data/list?module=nycu0008&id=307"
NYCU_EXPERIENCE_AMERICAS_URL = "https://oia.nycu.edu.tw/oia/ch/app/data/list?module=nycu0008&id=310"
NYCU_EXPERIENCE_EUROPE_URL = "https://oia.nycu.edu.tw/oia/ch/app/data/list?module=nycu0008&id=315"
NYCU_EXPERIENCE_OCEANIA_URL = "https://oia.nycu.edu.tw/oia/ch/app/data/list?module=nycu0008&id=319"

UST_EXTRA_SCHOOL_INFO = {
    "蘇黎世聯邦理工學院": "亦列入「116學年度臺灣聯合大學系統（UST）學生出國交換計畫」（暑期研究交換，收件至 2026/12/31 16:00 止）",
    "伯恩大學": "116學年度臺灣聯合大學系統（UST）一般學期交換合作校（合約名額 2 名，開放大學部二年級以上含碩士班學生；TOEFL iBT 90 或 IELTS 7.0、GPA 3.0，收件至 2026/12/31 16:00 止）",
    "香港中文大學": "除陽明交大校級／院系交換外，亦列入「116學年度臺灣聯合大學系統（UST）學生出國交換計畫」（新亞書院學期交換 4 名：TOEFL iBT 71／IELTS 6.0；理學院／工學院暑期交換各 6 名，限大學部二年級以上，收件至 2026/12/31 16:00 止）",
    "香港城市大學": "除陽明交大校級／院系交換外，亦列入「116學年度臺灣聯合大學系統（UST）學生出國交換計畫」（能源和環境學院、理學院、工學院學期與暑期交換共用各 4 名：TOEFL iBT 79／IELTS 6.5，限大學部二年級以上，收件至 2026/12/31 16:00 止）",
    "南洋理工大學": "除陽明交大校級交換外，亦列入「116學年度臺灣聯合大學系統（UST）學生出國交換計畫」（研究學期交換與暑期交換共用 6 名：TOEFL iBT 90／IELTS 6.0，研究學期交換開放大學部大二以上含碩士班，收件至 2026/12/31 16:00 止）",
    "馬里蘭大學": "116學年度臺灣聯合大學系統（UST）學生出國交換計畫合作校（暑期研究與學期交換計畫；前一學年 GPA 3.0 以上並具 2 年內有效 TOEFL iBT 或 IELTS 成績，陽明交大收件至 2026/12/31 16:00 止）",
    "加州大學聖地牙哥分校": "116學年度臺灣聯合大學系統（UST）學生出國交換計畫合作校（暑期研究交換計畫；前一學年 GPA 3.0 以上並具 2 年內有效 TOEFL iBT 或 IELTS 成績，陽明交大收件至 2026/12/31 16:00 止）",
    "新南威爾斯大學": "116學年度臺灣聯合大學系統（UST）學生出國交換計畫合作校（暑期研究與學期交換計畫；前一學年 GPA 3.0 以上並具 2 年內有效 TOEFL iBT 或 IELTS 成績，陽明交大收件至 2026/12/31 16:00 止）",
}


def clean_text(s: str) -> str:
    if not s:
        return ""
    return re.sub(r"\s+", " ", s).strip()


def group_sub_rows(sub_rows: list[dict]) -> list[dict]:
    """Deduplicate and merge sub_rows that share (quota, eligibility, language, grade)."""
    grouped: dict[tuple[str, str, str, str], list[str]] = {}
    for sr in sub_rows:
        q = clean_text(sr.get("quota") or "")
        el = clean_text(sr.get("eligibility") or "")
        la = clean_text(sr.get("language") or "")
        gr = clean_text(sr.get("grade") or "")
        rm = clean_text(sr.get("remarks") or "")
        key = (q, el, la, gr)
        if key not in grouped:
            grouped[key] = []
        if rm and rm not in {"參考網頁 Link", "Fact Sheet", "Link"} and rm not in grouped[key]:
            grouped[key].append(rm)
    out = []
    for (q, el, la, gr), rms in grouped.items():
        if not any((q, el, la, gr, rms)):
            continue
        out.append({
            "quota": q,
            "eligibility": el,
            "language": la,
            "grade": gr,
            "remarks": "；".join(rms),
        })
    return out


def format_colleges(item: dict, tracks: list[dict]) -> str:
    el_list = []
    for t in tracks:
        el = t["eligibility"]
        if el and el not in el_list:
            el_list.append(el)
    if el_list:
        joined = "；".join(el_list)
        if "全校" in joined or "U-wide" in joined:
            if len(el_list) == 1:
                return f"不限學院（{joined}；系所限制以主修或雙主修為準）"
            return f"校級全校名額與特定院系名額並行（{joined[:320]}；系所限制以主修或雙主修為準）"
        return f"限定院系／專業領域申請（{joined[:320]}；系所限制以主修或雙主修為準）"
    if item.get("is_ust") or item["name_zh"] == "伯恩大學":
        return "臺灣聯合大學系統（UST）交換計畫（依各接待校開放學院與科系領域申請）"
    dd_field = clean_text(item.get("contract_dual_degree_field") or "")
    if dd_field:
        return f"依當期名額表開放院系申請（另簽有雙聯學位合作領域：{dd_field}）"
    return "不限學院（全校 20 個學院在學學生皆可依當期《學生申請出國交換名額表》開放系所報名）"


def format_degree_levels(item: dict, tracks: list[dict]) -> str:
    combined = " ".join(
        f"{t['eligibility']} {t['remarks']}" for t in tracks
    )
    if (
        ("研究生不得申請" in combined or "PG students cannot apply" in combined)
        and "研究所" not in combined
    ):
        return "限大學部二年級以上在學學生（交換生不得為大一新生；研究生不得申請）"
    if "大學部二年級以上" in combined and "研究所" not in combined and "碩" not in combined and "PG" not in combined:
        return "限大學部二年級以上在學學生（交換生不得為大學部一年級新生；年級限制以出國交換時之年級為準）"
    if ("研究所" in combined or "碩" in combined or "PG" in combined) and "大學部" not in combined and "UG" not in combined:
        return "限研究所（碩士班、博士班一年級以上）在學學生（碩博一新生未有本校成績者須上傳前一學位含畢業排名之成績單）"
    return "大學部二年級以上、碩士班一年級以上、博士班一年級以上正式學籍生（交換生不得為大學部一年級新生；年級限制以出國交換時之年級為準）"


def format_language_req(item: dict, tracks: list[dict]) -> str:
    langs = []
    for t in tracks:
        if t["language"] and t["language"] not in langs:
            langs.append(t["language"])
    country = item["country"]
    if langs:
        lang_str = "；".join(langs)
        if country == "中國大陸":
            return f"締約校語言要求：{lang_str}（申請大陸地區交換者，校內書審不列外語能力佔比，惟接待校有英語授課門檻者仍須符合）"
        return (
            f"締約校語言能力限制：{lang_str}｜陽明交大校內規定：申請赴國外及港澳地區交換者，不論該校是否訂有語言分數門檻，皆須於截止日前提交有效語言能力成績證明"
            "（若使用 TOEIC 成績申請，須同時包含「聽力、閱讀、口說與寫作」四項測驗）"
        )
    if item["name_zh"] in UST_EXTRA_SCHOOL_INFO:
        return f"{UST_EXTRA_SCHOOL_INFO[item['name_zh']]}（須檢附 2 年內有效之 TOEFL iBT 或 IELTS 成績單）"
    if country == "中國大陸":
        return "申請大陸地區交換學校者，陽明交大校內不強制要求檢附外語檢定證明（書面審查配分為：大學部在校成績 60%、自傳 15%、讀書計畫 20%、其他表現 5%；研究所在校成績 40%、自傳 25%、讀書計畫 30%、其他表現 5%）。"
    return (
        "締約校未設特定分數門檻，惟依《國立陽明交通大學學生申請出國交換計畫簡章》規定，申請赴國外或港澳地區交換者，"
        "不論該校是否訂有語言能力限制，皆須於申請截止日前提交有效語言能力成績證明（TOEFL iBT、IELTS Academic、全民英檢複試通過、包含「聽讀及口說與寫作測驗」之 TOEIC，或日語 JLPT、韓語 TOPIK、德法西語檢定）。"
    )


def format_gpa_req(item: dict, tracks: list[dict]) -> str:
    grades = []
    for t in tracks:
        if t["grade"] and t["grade"] not in grades:
            grades.append(t["grade"])
    country = item["country"]
    if country == "中國大陸":
        base = "陽明交大校內評分基準：書面審查總分須達 60 分以上（大陸地區配分：大學部在校成績 60%、自傳 15%、讀書計畫 20%、其他表現 5%；研究所在校成績 40%、自傳 25%、讀書計畫 30%、其他表現 5%）"
    else:
        base = "陽明交大校內評分基準：書面審查總分須達 60 分以上（國外及港澳配分：大學部在校成績 50%、外語能力 20%、自傳 10%、讀書計畫 15%、其他表現 5%；研究所在校成績 30%、外語能力 20%、自傳 20%、讀書計畫 25%、其他表現 5%）"
    if grades:
        return f"締約校成績限制：{'；'.join(grades)}｜{base}"
    if item.get("is_ust") or item["name_zh"] == "伯恩大學":
        return f"台灣聯合大學系統（UST）交換門檻：前一學年平均成績達 GPA 3.0 或是 B 以上｜{base}"
    return f"締約校未明訂最低 GPA 限制（依校內書審成績擇優推薦）｜{base}"


def format_quota(item: dict, tracks: list[dict]) -> str:
    active_sheet = item.get("active_sheet") or ""
    parts = []
    for t in tracks:
        q = t["quota"] or "名額依當期公告"
        el = t["eligibility"]
        if el:
            el_short = el.split("\n")[0].strip()
            parts.append(f"{q}（{el_short}）")
        else:
            parts.append(q)
    tb_tag = "【拓荒者計畫獎學金重點補助校】" if item.get("is_trailblazer") else ""
    if parts:
        sheet_label = f"{active_sheet} 學期名額表" if active_sheet else "當期名額表"
        q_joined = "；".join(parts)
        if item["name_zh"] in UST_EXTRA_SCHOOL_INFO:
            return f"{tb_tag}{sheet_label}：{q_joined}｜另含 {UST_EXTRA_SCHOOL_INFO[item['name_zh']]}"
        return f"{tb_tag}{sheet_label}：{q_joined}"
    if item["name_zh"] in UST_EXTRA_SCHOOL_INFO:
        return f"{tb_tag}{UST_EXTRA_SCHOOL_INFO[item['name_zh']]}"
    c_rem = clean_text(item.get("contract_remark") or "")
    return f"{tb_tag}依當期《國立陽明交通大學學生申請出國交換名額表》公告（締約單位：{c_rem or 'NYCU 校級／院系級交換合約'}）"


def format_study_period(item: dict, tracks: list[dict]) -> str:
    q_text = " ".join(t["quota"] + " " + t["remarks"] for t in tracks)
    if item.get("is_ust") and not tracks:
        return "一學期（2027 秋季班／2028 春季班）或 2027 暑期交換（6–10 週），依台灣聯合大學系統出國交換計畫公告辦理"
    if "僅能申請一學期" in q_text or "one semester only" in q_text.lower():
        return "一學期（依締約校規定僅開放交換一學期）"
    return "一學期或一學年（第一梯次可申請秋季班、春季班或全學年；第二梯次申請春季班，交換期間為 1 學期或 2 學期）"


def format_program_type(item: dict) -> str:
    avail = item.get("availability_status")
    tags = []
    if item.get("is_trailblazer"):
        tags.append("拓荒者計畫重點獎學金校")
    if item.get("is_ust") or item["name_zh"] in UST_EXTRA_SCHOOL_INFO:
        tags.append("含台灣聯合大學系統 UST 交換計畫")
    if item.get("contract_dual_degree") == "V":
        dd_f = clean_text(item.get("contract_dual_degree_field") or "跨院系")
        tags.append(f"亦簽署雙聯學位合約：{dd_f}")
    tag_str = f"［{'・'.join(tags)}］" if tags else ""
    if avail == "open":
        return f"交換學生（陽明交大出國交換計畫當期開放申請校{tag_str}・繳交陽明交大全額學雜費、互惠免繳姐妹校學費）"
    return f"交換學生（國立陽明交通大學國際事務處締約合作姐妹校{tag_str}・歷年／院系級／雙聯交換合作校）"


def main() -> None:
    OFFICIAL_NYCU_DIR.mkdir(parents=True, exist_ok=True)
    SOURCES_NYCU_DIR.mkdir(parents=True, exist_ok=True)

    catalog_items = json.loads(
        (SOURCES_NYCU_DIR / "nycu_catalog_source.json").read_text(encoding="utf-8")
    )
    locs_raw = json.loads(
        (SOURCES_NYCU_DIR / "nycu_resolved_locations.json").read_text(encoding="utf-8")
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
    trailblazer_count = 0
    exp_covered_schools = 0

    for idx, item in enumerate(catalog_items):
        full_name = item["school_name"]
        zh_name = item["name_zh"]
        country = item["country"]
        region = REGION_BY_COUNTRY.get(country, "其他地區")
        avail_status = item["availability_status"]
        if avail_status == "open":
            open_partner_count += 1
        if item.get("is_trailblazer"):
            trailblazer_count += 1

        website = (item.get("website") or "").strip()
        if website and not website.startswith("http"):
            website = f"https://{website}"

        factsheet_url = (item.get("factsheet_url") or "").strip() or None
        source_url = (
            NYCU_116_1_UST_NOTICE_URL
            if item.get("is_ust")
            else NYCU_QUOTA_SHEET_URL
        )

        tracks = group_sub_rows(item.get("sub_rows") or [])
        remarks_all = "；".join(
            t["remarks"] for t in tracks if t.get("remarks")
        )
        ranking_val = clean_text(str(item.get("ranking") or ""))
        if ranking_val.endswith(".0"):
            ranking_val = ranking_val[:-2]

        if item.get("is_ust"):
            round_label = "116學年度臺灣聯合大學系統（UST）學生出國交換計畫（陽明交大校內收件至 2026/12/31 16:00 止）"
            deadline_iso = "2026-12-31T16:00:00+08:00"
            deadline_rem = True
            win_status = "open"
            app_deadline_str = (
                "【116學年度臺灣聯合大學系統（UST）學生出國交換計畫（含 2027 秋季／2028 春季學期交換與 2027 暑期研究交換）】"
                "陽明交大宣傳暨心得分享會：2026年12月3日（四）12:30；"
                "陽明交大校內收件截止日：2026年12月31日（四）下午 16:00 止（每種交換類別限填一份報名表、至多選填 2 個志願，紙本申請表與附件繳交至國際事務處劉小姐 ext. 50665，由校內初審後於 2027/01/11 前彙送台灣聯大系統審查，2027/02/28 前通知審查結果）。"
            )
        elif avail_status == "open":
            round_label = "校級出國交換計畫第一梯次甄選（每年12月1日09:00至翌年1月5日17:00線上申請）暨第二梯次春季班甄選（6月1日至7月10日17:00線上申請）"
            deadline_iso = "2027-01-05T17:00:00+08:00"
            deadline_rem = True
            win_status = "open"
            app_deadline_str = (
                "【第一梯次校級出國交換甄選（申請秋季班、春季班或全學年出國交換）】"
                "線上申請期間：每年 12月1日 09:00 至翌年 1月5日 17:00 止（於陽明交大出國交換申請系統 https://oia-sys.nycu.edu.tw/outgoing 完成填報並上傳系所及院長核章之申請簽核表與全套審查文件，至多選填 5 所志願學校）；"
                "初審結果公告：1月中旬（115-1 梯次為 01/19 17:00）；錄取確認並繳交保證金 NT$10,000：1月下旬（01/25 23:59 前）；出國交換獎學金申請截止：3月上旬（03/09 12:00）。"
                "【第二梯次校級出國交換甄選（申請春季班一學期出國交換）】"
                "線上申請期間：每年 6月1日 09:00 至 7月10日 17:00 止；初審結果公告：7月24日 15:00；錄取確認並繳交保證金 NT$10,000：7月31日 17:00 前；獎學金申請截止：10月31日。"
            )
        else:
            round_label = "國立陽明交通大學國際事務處締約合作姐妹校（依當期《學生申請出國交換名額表》或院系公告開放）"
            deadline_iso = "2027-01-05T17:00:00+08:00"
            deadline_rem = False
            win_status = "closed"
            app_deadline_str = (
                "【陽明交大國際締約姐妹校（歷年／院系級／雙聯交換合作校）】本合作校為國立陽明交通大學國際事務處登錄之締約合作學校；"
                "115 學年度校級名額表未開缺（可能僅於特定學期開放或屬院系級／雙聯合約），欲申請者請於每年 12月1日–1月5日（第一梯次）或 6月1日–7月10日（第二梯次）查閱最新《學生申請出國交換名額表》或洽所屬院系。"
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

        colleges_str = format_colleges(item, tracks)
        degree_levels_str = format_degree_levels(item, tracks)
        lang_req_str = format_language_req(item, tracks)
        gpa_req_str = format_gpa_req(item, tracks)
        quota_str = format_quota(item, tracks)
        study_period_str = format_study_period(item, tracks)
        program_type = format_program_type(item)

        exp_posts = item.get("experience_posts") or []
        exp_country_url = item.get("experience_country_url") or (
            NYCU_EXPERIENCE_EUROPE_URL
            if region == "歐洲"
            else (
                NYCU_EXPERIENCE_AMERICAS_URL
                if region == "美洲"
                else (
                    NYCU_EXPERIENCE_OCEANIA_URL
                    if region == "大洋洲"
                    else NYCU_EXPERIENCE_ASIA_URL
                )
            )
        )

        if country == "日本":
            sem_dates_str = "春季學期（前學期）：約每年 4 月至 8 月；秋季學期（後學期）：約每年 9/10 月至翌年 2/3 月"
        elif country in {"澳洲", "紐西蘭"}:
            sem_dates_str = "第 1 學期（秋季班出國對應 Semester 2）：約每年 7 月至 11 月；第 2 學期（春季班出國對應 Semester 1）：約每年 2 月至 6 月"
        else:
            sem_dates_str = "秋季學期（第 1 學期）：約每年 8/9 月至 12 月／翌年 1 月；春季學期（第 2 學期）：約每年 1/2 月至 5/6 月"

        course_parts = [f"開放申請院系與學制：{colleges_str}（{degree_levels_str}）。"]
        if remarks_all:
            course_parts.append(f"締約校交換申請與選課備註：{remarks_all[:350]}。")
        course_parts.append(
            "依《國立陽明交通大學學生申請出國交換實施辦法》及出國交換計畫簡章第拾壹點規定，交換期間大學部學生每學期至少須修習 3 門專業課程、研究所學生每學期至少須修習 2 門專業課程，且「所有修習課程皆須及格」（若有一門以上［含］修課不及格或因個人因素放棄交換，將全額沒收新臺幣 10,000 元保證金）；另須選修陽明交大 0 學分《海外學期交換》課程並按期繳交期中與期末報告。"
        )
        course_rest_str = " ".join(course_parts)

        if "宿" in remarks_all or "housing" in remarks_all.lower() or "dorm" in remarks_all.lower():
            housing_str = f"{zh_name} 住宿與申請說明：{remarks_all[:360]}"
        else:
            housing_str = f"{zh_name} 依兩校交換協議提供獲提名交換生校內學生宿舍申請資訊或校外住宿指引；宿位是否保證分配及收費標準以該校最新 Factsheet（{factsheet_url or website or '詳國際處名額表'}）與入學許可通知為準。"

        tuition_points_list = [
            "陽明交大註冊學雜費與 10,000 元保證金規定：錄取學生於出國交換期間須維持國立陽明交通大學正式學籍並完成註冊、繳交陽明交大全額學雜費（在職專班學生須另繳學分費），享互惠免繳接待校學費（住宿費、生活費、保險費、簽證費與往返機票均由學生自理）。錄取生確認參加計畫時須繳交保證金新臺幣 10,000 元（持低收入戶、中低收入戶或特殊境遇家庭證明者免繳）；須完成大學部每學期至少 3 門專業課程、研究所每學期至少 2 門專業課程且全部修課及格（有任一門不及格者沒收全額保證金），並繳交期中報告（開學 2 個月內：4/30 或 10/31 前）與期末報告（結束後 1 個月內：7/31 或 1/31 前，含 3–5 張照片）後始得無息退還。",
            "六大出國交換獎助學金體系：（1）《（A類）國立陽明交通大學優秀學生出國交換獎學金》：補助一學期或一學年約新臺幣 50,000–360,000 元（大學部赴亞洲地區須歷年班或系排名前 50%、赴非亞洲地區須排名前 20%；研究所須歷年 GPA 3.7 以上；語言須達 TOEFL iBT 83／IELTS 6.0／全民英檢中高級／TOEIC 聽400讀385說150寫150）；（2）《（B類）學士班優秀入學生出國短期進修獎學金》：每學期 100,000–150,000 元、每學年 200,000–300,000 元（大學部平均 80 分［GPA 3.38］以上、於陽明交大修畢 3 門英語授課課程，且達 TOEFL iBT 87／IELTS 6.5）；（3）教育部「學海飛颺」與（4）「學海惜珠」（低收／中低收／特殊境遇家庭學生，無排名門檻）；（5）《國立陽明交通大學經濟不利學生短期出國獎助金（高教深耕完善就學協助計畫）》：每學期最高補助 100,000 元（可與校內交換獎學金兼領）；（6）日本台灣交流協會獎學金、UMAP 獎學金及各締約校獎學金。",
        ]
        if item.get("is_trailblazer"):
            tuition_points_list.append(
                f"【拓荒者計畫（Trailblazer Program）紫色字體重點補助校】{zh_name} 列入陽明交大《學生申請出國交換名額表》紫色字體標示之「拓荒者計畫」合作學校！符合 A 類優秀學生出國交換獎學金資格並錄取本校者，享有優先獲得較高額度出國交換獎學金之鼓勵機制。"
            )

        app_steps_list = [
            f"步驟一（確認學籍年級、系所限制與 {zh_name} 語言及 GPA 條件）：確認為陽明交大大學部二年級以上或碩博士班一年級以上正式學籍生（交換生不得為大一新生；各校系所限制以主修或雙主修為準，年級限制以出國交換時之年級為準），並備妥有效外語檢定證明（申請國外及港澳地區者強制必繳；若使用 TOEIC 須包含聽讀及口說與寫作四項測驗）。",
            "步驟二（於線上申請系統填報至多 5 志願並完成《申請簽核表》五級核章）：於第一梯次（12/1 09:00 至翌年 1/5 17:00）或第二梯次（6/1 09:00 至 7/10 17:00）登入「陽明交大出國交換學生申請系統」（https://oia-sys.nycu.edu.tw/outgoing）選填至多 5 個志願學校，下載《學生出國交換申請簽核表》完成申請人、家長／監護人、導師／指導教授、系所主任及學院院長核章後，連同英文歷年成績單（含累计排名或 GPA）、外語能力證明、中英文自傳、讀書計畫及其他經歷證明一併上傳。",
            f"步驟三（校內書審評分、錄取確認與繳交 10,000 元保證金）：國際事務處依簡章配分辦理書面審查（審查總分未達 60 分不予錄取；同分依序參酌：1. 志願序、2. 讀書計畫、3. 外語能力、4. 在校成績）。放榜後正備取生須於期限內於系統完成錄取確認並匯款繳交保證金新臺幣 10,000 元（低收／中低收／特殊境遇家庭免繳），由國際處向 {full_name} 辦理官方提名（Nomination）。",
            "步驟四（向姐妹校遞交入學申請、申請 A/B/C 類或深耕獎助學金與履行修課報告義務）：獲提名後依姐妹校規定準備入學申請文件（最終錄取權在姐妹校）；於 3月上旬（第一梯次）或 10月底（第二梯次）前申請 A 類優秀學生出國交換獎學金（含拓荒者計畫）、B 類獎學金、學海飛颺／惜珠或經濟不利學生短期出國獎助金。交換期間須選修陽明交大 0 學分《海外學期交換》課程，大學部每學期至少修習 3 門專業課、研究所至少 2 門專業課且所有修課皆須及格，並按時繳交期中（4/30 或 10/31）與期末報告（7/31 或 1/31）以退還保證金。",
        ]

        elig_points_list = [
            f"開放學制與年級：{degree_levels_str}",
            f"開放申請院系：{colleges_str}",
            f"GPA 與校內書審配分：{gpa_req_str}",
            f"語言能力規定：{lang_req_str}",
        ]
        if ranking_val and ranking_val != "N/A":
            elig_points_list.append(f"QS / 世界大學排名參考：第 {ranking_val} 名")
        if remarks_all:
            elig_points_list.append(f"締約校特殊規定與備註：{remarks_all[:260]}")

        notes_lines = [
            f"【合作類別與期程】{program_type}｜交換期間：{study_period_str}",
            f"【當期名額與申請梯次】{quota_str}（涵蓋名額表梯次：{', '.join(item.get('sheets_present') or ['締約合作校'])}）",
            f"【開放學院與學制】{colleges_str}｜{degree_levels_str}",
            f"【語言與學業門檻】{lang_req_str}｜{gpa_req_str}",
        ]
        if item.get("is_trailblazer"):
            notes_lines.append(
                "【拓荒者計畫重點學校】本校為陽明交大名額表紫色字體標示之「拓荒者計畫」合作大學，符合 A 類出國交換獎學金資格者優先獲得較高額度補助。"
            )
        if remarks_all:
            notes_lines.append(f"【締約校重要備註】{remarks_all[:380]}")
        if exp_posts:
            notes_lines.append(
                f"【陽明交大歷屆交換生心得】陽明交大國際事務處官網「學生心得分享」專區公開收錄赴 {zh_name} 交換生期中／期末報告共 {len(exp_posts)} 篇。"
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
            "availability_note": f"國立陽明交通大學國際事務處公告合作姐妹校；{quota_str}。",
            "academic_year": "116" if item.get("is_ust") else "115",
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
                "title": f"國立陽明交通大學學生申請出國交換名額表與條件—{zh_name}",
                "source_url": source_url,
                "role": "home_university",
                "authority": "home_official_notice",
                "effective_academic_year": "116",
                "application_round": round_label,
                "checked_at": CHECKED_AT,
            },
            {
                "title": "國立陽明交通大學學生申請出國交換計畫簡章（第一梯次／第二梯次）PDF",
                "source_url": NYCU_115_1_GUIDELINES_PDF_URL,
                "role": "home_university",
                "authority": "home_official_notice",
                "effective_academic_year": "116",
                "application_round": round_label,
                "checked_at": CHECKED_AT,
            },
            {
                "title": "國立陽明交通大學學生申請出國交換實施辦法與優秀學生出國交換獎學金辦法",
                "source_url": NYCU_REGULATIONS_ZH_PDF_URL,
                "role": "home_university",
                "authority": "home_official_notice",
                "effective_academic_year": "116",
                "application_round": round_label,
                "checked_at": CHECKED_AT,
            },
        ]
        if factsheet_url:
            wf_sources.append({
                "title": f"國立陽明交通大學出國交換名額表合作校交換資訊／Fact Sheet—{zh_name}",
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
            "home_university": "國立陽明交通大學",
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
                "第一梯次（秋季班／春季班／一學年）",
                "第二梯次（春季班）",
                "臺灣聯合大學系統（UST）116學年度學生出國交換計畫",
            ],
            "applicability_status": "verified",
            "applicability_note": (
                "國立陽明交通大學每年分兩梯次辦理校級出國交換學生甄選（第一梯次於 12月1日 09:00 至翌年 1月5日 17:00 受理秋季班、春季班或全學年交換申請；"
                "第二梯次於 6月1日 09:00 至 7月10日 17:00 受理春季班交換申請；另辦理台灣聯合大學系統 116-1 出國交換計畫收件至 2026/12/31 16:00 止），"
                "書面審查總分須達 60 分以上，每人至多選填 5 個志願。"
            ),
            "review_status": "published",
            "published_at": CHECKED_AT,
            "steps": [
                {
                    "rule_id": f"nycu-116-home-1-{idx+1:03d}",
                    "order": 1,
                    "phase": "校內申請",
                    "title": f"確認陽明交大在學年級（大二／碩一／博一以上）、主修系所限制與 {zh_name} 語言及 GPA 門檻",
                    "responsible_party": "學生",
                    "responsible_unit": "國立陽明交通大學國際事務處（光復校區浩然圖書資訊中心 8 樓／陽明校區行政大樓 2 樓）",
                    "deadline_at": deadline_iso,
                    "deadline_status": "verified_exact" if avail_status == "open" else "reference_only",
                    "deadline_source_url": NYCU_116_1_UST_NOTICE_URL if item.get("is_ust") else NYCU_115_1_GUIDELINES_PDF_URL,
                    "deadline_checked_at": CHECKED_AT,
                    "deadline_reminder_eligible": deadline_rem,
                    "summary": f"申請人須為陽明交大大學部二年級以上、碩士班一年級以上或博士班一年級以上正式學籍生（交換生不得為大學部一年級新生；系所限制以主修或雙主修為準，年級限制以出國交換時之年級為準），並確認符合 {zh_name} 之學制、院系、外語檢定及 GPA 標準。",
                    "details": [
                        f"開放學制與院系：{colleges_str}（{degree_levels_str}）",
                        f"語言與學業條件：{lang_req_str}｜{gpa_req_str}",
                        f"當期名額與交換期程：{quota_str}",
                    ],
                    "scope": {
                        "home_universities": ["國立陽明交通大學"],
                        "partner_universities": [full_name],
                        "academic_years": ["115", "116"],
                        "application_rounds": [
                            round_label,
                            "115-1",
                            "115-2",
                            "116-1",
                            "116-2",
                            "第一梯次（秋季班／春季班／一學年）",
                            "第二梯次（春季班）",
                        ],
                    },
                    "source_urls": [
                        NYCU_115_1_GUIDELINES_PDF_URL,
                        NYCU_115_2_GUIDELINES_PDF_URL,
                        source_url,
                    ],
                    "checked_at": CHECKED_AT,
                    "support_status": "verified",
                },
                {
                    "rule_id": f"nycu-116-home-2-{idx+1:03d}",
                    "order": 2,
                    "phase": "校內申請",
                    "title": "於線上申請系統填報至多 5 志願並上傳經導師、系主任、院長五級核章之《申請簽核表》與全套書審文件",
                    "responsible_party": "學生",
                    "responsible_unit": "國立陽明交通大學國際事務處",
                    "deadline_at": deadline_iso,
                    "deadline_status": "verified_exact" if avail_status == "open" else "reference_only",
                    "deadline_source_url": NYCU_PORTAL_URL,
                    "deadline_checked_at": CHECKED_AT,
                    "deadline_reminder_eligible": deadline_rem,
                    "summary": "於第一梯次（12月1日 09:00 至翌年 1月5日 17:00）或第二梯次（6月1日 09:00 至 7月10日 17:00）登入陽明交大出國交換學生申請系統（https://oia-sys.nycu.edu.tw/outgoing）完成線上填報（至多選填 5 個志願），列印《國立陽明交通大學學生出國交換申請簽核表》經申請人、家長／監護人、導師／指導教授、系所主任及學院院長核章後，連同英文歷年成績單、有效外語能力證明、中英文自傳、讀書計畫及其他經歷證明上傳至系統。",
                    "details": [
                        "外語能力證明強制規定：申請赴國外及港澳地區交換者，不論該姐妹校是否訂有語言能力分數門檻，皆須於截止日前提交有效語言能力成績證明；若以多益（TOEIC）申請，成績單必須同時包含「聽力、閱讀、口說與寫作」四項測驗。",
                        "簽核流程序時提醒：《學生出國交換申請簽核表》須經導師／指導教授、系所主任及學院院長（雙主修生若以第二主修申請須加會第二主修系主任及院長）核章，請務必預留院系公文簽核時間，逾期未上傳完整核章文件者不予受理。",
                    ],
                    "document_requirements": [
                        {
                            "name": "國立陽明交通大學學生出國交換申請簽核表（須經本人、家長／監護人、導師／指導教授、系所主任及學院院長簽章）",
                            "official_form_url": NYCU_115_2_APPROVAL_FORM_PDF_URL,
                            "source_urls": [
                                NYCU_115_2_APPROVAL_FORM_PDF_URL,
                                NYCU_115_1_GUIDELINES_PDF_URL,
                                NYCU_115_2_GUIDELINES_PDF_URL,
                            ],
                        },
                        {
                            "name": "英文歷年成績單（大學部須含累計班或系排名百分比；研究所須含累計 GPA，碩一、博一新生未有本校成績者須上傳前一學位含畢業排名之成績單）",
                            "source_urls": [
                                NYCU_115_1_GUIDELINES_PDF_URL,
                                NYCU_115_2_GUIDELINES_PDF_URL,
                            ],
                        },
                        {
                            "name": "有效外語能力證明（申請國外及港澳地區必繳：TOEFL iBT、IELTS Academic、全民英檢複試通過、含「聽讀及口說與寫作測驗」之 TOEIC，或交換校指定外語檢定）",
                            "source_urls": [
                                NYCU_115_1_GUIDELINES_PDF_URL,
                                NYCU_QUOTA_SHEET_URL,
                            ],
                        },
                        {
                            "name": "自傳、讀書計畫（含出國修課規劃及未來展望）及其他有利審查之表現證明（獲獎、社團、競賽或研究發表）",
                            "source_urls": [
                                NYCU_115_1_GUIDELINES_PDF_URL,
                                NYCU_REGULATIONS_ZH_PDF_URL,
                            ],
                        },
                    ],
                    "scope": {
                        "home_universities": ["國立陽明交通大學"],
                        "academic_years": ["115", "116"],
                        "application_rounds": [
                            round_label,
                            "115-1",
                            "115-2",
                            "116-1",
                            "116-2",
                            "第一梯次（秋季班／春季班／一學年）",
                            "第二梯次（春季班）",
                        ],
                    },
                    "source_urls": [
                        NYCU_PORTAL_URL,
                        NYCU_115_1_GUIDELINES_PDF_URL,
                        NYCU_115_2_GUIDELINES_PDF_URL,
                        NYCU_115_2_APPROVAL_FORM_PDF_URL,
                    ],
                    "checked_at": CHECKED_AT,
                    "support_status": "verified",
                },
                {
                    "rule_id": f"nycu-116-home-3-{idx+1:03d}",
                    "order": 3,
                    "phase": "甄選與提名",
                    "title": "校內書審評分（總分須達 60 分）、初審放榜、線上錄取確認與繳交 10,000 元保證金",
                    "responsible_party": "學生與國立陽明交通大學國際事務處",
                    "responsible_unit": "國立陽明交通大學國際事務處",
                    "deadline_at": "2027-01-25T23:59:00+08:00" if avail_status == "open" else "2027-07-31T17:00:00+08:00",
                    "deadline_status": "reference_only",
                    "deadline_source_url": NYCU_115_1_GUIDELINES_PDF_URL,
                    "deadline_checked_at": CHECKED_AT,
                    "deadline_reminder_eligible": False,
                    "summary": "書面審查依國外／港澳或大陸地區及大學部／研究所不同權重計分（總分未達 60 分者不予錄取；同分參酌順序為：1. 志願序、2. 讀書計畫、3. 外語能力、4. 在校成績）。獲錄取後須於期限內至申請系統確認錄取資格並繳交保證金新臺幣 10,000 元（低收、中低收及特殊境遇家庭免繳）。",
                    "details": [
                        "書審配分權重：國外及港澳地區大學部（在校成績 50%、外語能力 20%、自傳 10%、讀書計畫 15%、其他表現 5%）、研究所（在校成績 30%、外語能力 20%、自傳 20%、讀書計畫 25%、其他表現 5%）；大陸地區大學部（在校成績 60%、自傳 15%、讀書計畫 20%、其他表現 5%）、研究所（在校成績 40%、自傳 25%、讀書計畫 30%、其他表現 5%）。",
                        "保證金沒收警示：確認錄取後若因個人因素放棄資格，或於交換期間有任一門修課不及格，保證金新臺幣 10,000 元將全額沒收不予退還。",
                    ],
                    "scope": {
                        "home_universities": ["國立陽明交通大學"],
                        "academic_years": ["115", "116"],
                        "application_rounds": [
                            round_label,
                            "115-1",
                            "115-2",
                            "116-1",
                            "116-2",
                            "第一梯次（秋季班／春季班／一學年）",
                            "第二梯次（春季班）",
                        ],
                    },
                    "source_urls": [
                        NYCU_115_1_GUIDELINES_PDF_URL,
                        NYCU_115_2_GUIDELINES_PDF_URL,
                        NYCU_REGULATIONS_ZH_PDF_URL,
                    ],
                    "checked_at": CHECKED_AT,
                    "support_status": "verified",
                },
                {
                    "rule_id": f"nycu-{idx+1:03d}-host-apply",
                    "order": 4,
                    "phase": "合作校申請",
                    "title": f"由陽明交大國際處辦理官方提名並依 {zh_name} 規定遞交入學申請資料",
                    "responsible_party": "學生與接待校國際處",
                    "summary": f"完成校內錄取確認與保證金繳交後，由陽明交大國際事務處向 {zh_name} 辦理官方提名（Nomination）；學生須自行密切留意姐妹校申請截止日，備妥英文成績單、護照、財力證明、語檢證明及選課計畫按時完成該校入學申請，靜候姐妹校核發正式入學許可（Letter of Acceptance）。",
                    "details": [
                        f"交換期程：{study_period_str}｜名額：{quota_str}",
                        f"語言與學業條件：{lang_req_str}",
                    ]
                    + ([f"締約校申請與修課備註：{remarks_all[:240]}"] if remarks_all else []),
                    "scope": {
                        "home_universities": ["國立陽明交通大學"],
                        "partner_universities": [full_name],
                        "academic_years": ["115", "116"],
                        "application_rounds": [
                            round_label,
                            "115-1",
                            "115-2",
                            "116-1",
                            "116-2",
                            "第一梯次（秋季班／春季班／一學年）",
                            "第二梯次（春季班）",
                        ],
                    },
                    "source_urls": (
                        [
                            source_url,
                            NYCU_115_1_GUIDELINES_PDF_URL,
                            NYCU_SCHOLARSHIP_LIST_URL,
                        ]
                        + ([factsheet_url] if factsheet_url else [])
                        + ([website] if website else [])
                    ),
                    "checked_at": CHECKED_AT,
                    "support_status": "verified",
                    "needs_confirmation": False,
                },
                {
                    "rule_id": f"nycu-116-home-5-{idx+1:03d}",
                    "order": 5,
                    "phase": "行前準備",
                    "title": "申請 A/B/C 類（含拓荒者計畫）或經濟不利出國獎助學金、修習全數及格專業課與繳交期中／期末報告退還保證金",
                    "responsible_party": "學生",
                    "responsible_unit": "國立陽明交通大學國際事務處／教務處註冊組／生輔組",
                    "summary": "於每年 3月上旬（第一梯次）或 10月底（第二梯次）前申請陽明交大 A 類優秀學生出國交換獎學金（5萬–36萬元，拓荒者計畫學校優先高額補助）、B 類獎學金（10萬–30萬元）、教育部學海飛颺／惜珠或經濟不利學生短期出國獎助金（最高 10 萬元）；役男應於出國前至少 1 個月辦理緩徵役男出境；交換期間須選修 0 學分《海外學期交換》課程，大學部每學期至少修習 3 門專業課程、研究所至少 2 門專業課程且全部及格，並按期繳交期中報告（4/30 或 10/31 前）與期末報告（7/31 或 1/31 前）後無息退還 10,000 元保證金。",
                    "details": tuition_points_list,
                    "scope": {
                        "home_universities": ["國立陽明交通大學"],
                        "academic_years": ["115", "116"],
                        "application_rounds": [
                            round_label,
                            "115-1",
                            "115-2",
                            "116-1",
                            "116-2",
                            "第一梯次（秋季班／春季班／一學年）",
                            "第二梯次（春季班）",
                        ],
                    },
                    "source_urls": [
                        NYCU_SCHOLARSHIP_LIST_URL,
                        NYCU_SCHOLARSHIP_TYPE_A_PDF_URL,
                        NYCU_SCHOLARSHIP_TYPE_B_PDF_URL,
                        NYCU_ECON_DISADVANTAGED_PDF_URL,
                        NYCU_115_1_GUIDELINES_PDF_URL,
                    ],
                    "checked_at": CHECKED_AT,
                    "support_status": "verified",
                },
            ],
            "sources": wf_sources,
            "last_checked": CHECKED_AT,
            "coverage_status": "official_verified",
            "coverage_note": "已完整整合國立陽明交通大學 115-2、115-1 出國交換計畫簡章、113–115 學年度 6 個學期名額表、全球姐妹校合約表、雙聯學位表、116-1 臺灣聯大交換公告、A/B/C 類及經濟不利獎學金辦法與 31 國歷屆交換心得。",
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
                "title": f"國立陽明交通大學學生申請出國交換名額表與條件—{zh_name}",
                "source_url": source_url,
                "summary": "陽明交大官方交換學校名額、外語能力限制、GPA 要求、拓荒者計畫標記與學制院系限制",
            },
            {
                "title": "國立陽明交通大學學生申請出國交換計畫簡章與實施辦法",
                "source_url": NYCU_115_1_GUIDELINES_PDF_URL,
                "summary": "陽明交大校級交換甄選配分、總分 60 分門檻、10,000 元保證金與大學部 3 門／研究所 2 門專業課全數及格規定",
            },
        ]
        if factsheet_url:
            dest_sources.append({
                "title": f"國立陽明交通大學出國交換名額表合作校 Fact Sheet—{zh_name}",
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
                "title": f"國立陽明交通大學赴 {zh_name} 交換生期中／期末心得報告（共 {len(exp_posts)} 篇）",
                "source_url": exp_country_url,
                "summary": f"收錄陽明交大國際處交換生赴 {zh_name} 期中與期末心得報告",
            })

        src_url_list = (
            [source_url, NYCU_115_1_GUIDELINES_PDF_URL]
            + ([factsheet_url] if factsheet_url else [])
            + ([website] if website else [])
        )

        destinations.append({
            "home_university": "國立陽明交通大學",
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
                    "title": "生活費、陽明交大 A 類優秀學生獎學金（5萬–36萬，含拓荒者計畫）、B 類獎學金、經濟不利補助與教育部學海計畫",
                    "summary": cost_line,
                    "points": [cost_line] + tuition_points_list,
                    "source_urls": src_url_list + [
                        NYCU_SCHOLARSHIP_LIST_URL,
                        NYCU_SCHOLARSHIP_TYPE_A_PDF_URL,
                        NYCU_SCHOLARSHIP_TYPE_B_PDF_URL,
                        NYCU_ECON_DISADVANTAGED_PDF_URL,
                    ],
                    "caution": "陽明交大「（A類）優秀學生出國交換獎學金」補助約 50,000–360,000 元（錄取紫色字體「拓荒者計畫」20 所重點學校者優先獲得較高額度補助）；「（B類）學士班優秀入學生出國短期進修獎學金」每學期 100,000–150,000 元；「經濟不利學生短期出國獎助金」每學期最高 100,000 元。",
                },
                {
                    "key": "housing",
                    "title": "住宿資訊與校內外宿舍申請",
                    "summary": housing_clean[:160],
                    "points": [housing_clean],
                    "source_urls": src_url_list,
                    "caution": "各姐妹校學生宿舍名額有限，獲陽明交大國際處提名後請務必於該校住宿申請截止日前完成登記。",
                },
                {
                    "key": "insurance",
                    "title": "海外醫療及意外保險與在地強制保險規定",
                    "summary": visa_default,
                    "points": [
                        visa_default,
                        "依《國立陽明交通大學學生申請出國交換計畫簡章》規定，交換生於出國前須自行購買足額之海外醫療、意外及海外急難救助保險，並依接待國及姐妹校規定投保當地強制學生健康保險。",
                    ],
                    "source_urls": src_url_list,
                    "caution": "多數歐美日韓及紐澳姐妹校要求於註冊或抵校時出示符合當地政府或校方標準之英文醫療保險證明。",
                },
                {
                    "key": "visa",
                    "title": "簽證辦理與緩徵役男出境手續（出國前至少 1 個月）",
                    "summary": visa_default,
                    "points": [
                        "收到姐妹校核發之正式入學許可書（LOA / COE / DS-2019）後，請立即向該國駐臺辦事處申辦學生簽證（赴大陸交換須自行辦理有效護照與臺胞證）。",
                        "依簡章第拾壹點規定，具役男身分之錄取學生，應於出國前至少 1 個月持姐妹校入學許可等文件，洽國際事務處及生輔組辦理役男出境核准手續。",
                        visa_default,
                    ],
                    "source_urls": src_url_list,
                    "caution": "各國領事館簽證審核約需 4–8 週，請勿於取得簽證與入學許可前購買不可退改之機票。",
                },
                {
                    "key": "courses",
                    "title": "每學期專業課程修習門檻（大學部 3 門／研究所 2 門全數及格）與《海外學期交換》0 學分課程",
                    "summary": course_clean[:160],
                    "points": [
                        course_clean,
                        "交換生於交換期間仍須於陽明交大註冊並選修 0 學分之《海外學期交換》課程；大學部每學期至少須修習 3 門專業課程、研究所每學期至少須修習 2 門專業課程，且所有修習課程皆須及格。",
                    ],
                    "source_urls": src_url_list,
                    "caution": "特別注意：依陽明交大簡章保證金規定，於姐妹校修課若「有一門以上（含）修課不及格者」，將全額沒收新臺幣 10,000 元保證金！選課時請務必審慎評估修課負荷。",
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
                    "caution": "部分合作大學設有多個校區，實際授課校區請以當期出國交換名額表及姐妹校錄取通知為準。",
                },
                {
                    "key": "arrival",
                    "title": "期中報告（4/30 或 10/31 前）、期末報告（7/31 或 1/31 前）與退還 10,000 元保證金",
                    "summary": calendar_clean,
                    "points": [
                        calendar_clean,
                        "依《國立陽明交通大學學生申請出國交換計畫簡章》規定，交換生須履行兩階段報告義務：（1）期中報告：於姐妹校開學後 2 個月內繳交（春季班於 4月30日 前、秋季班於 10月31日 前）；（2）期末報告與照片：於交換結束後 1 個月內繳交（春季班於 7月31日 前、秋季班於 1月31日 前，附 3–5 張交換生活照片）並檢附國外成績單正本，經審核通過後無息退還保證金 NT$10,000。",
                    ]
                    + (
                        [
                            f"歷屆學長姐返國心得：陽明交大國際處已公開收錄赴 {zh_name} 交換生期中／期末心得報告共 {len(exp_posts)} 篇。"
                        ]
                        if exp_posts
                        else []
                    ),
                    "source_urls": src_url_list + [exp_country_url],
                    "caution": "領取陽明交大 A/B 類出國交換獎學金、經濟不利學生短期出國獎助金或教育部學海系列計畫者，另須於返國後 1 個月內完成獎學金成果報告與經費核銷。",
                },
            ],
            "first_72_hours": [
                {
                    "title": "依姐妹校入學許可指定報到日完成新生報到、宿舍入住與選課確認",
                    "detail": calendar_clean,
                    "source_urls": [source_url],
                },
                {
                    "title": "確認修習足額專業課程（大學部至少 3 門／研究所至少 2 門）並於開學 2 個月內繳交期中報告",
                    "detail": f"{visa_default} 請於抵達後確認選課清單符合陽明交大每學期專業課程門檻（且所有修課須及格），並於 4/30（春季班）或 10/31（秋季班）前提交期中報告。",
                    "source_urls": [
                        NYCU_115_1_GUIDELINES_PDF_URL,
                        NYCU_OUTBOUND_TIMELINE_URL,
                    ],
                },
            ],
            "sources": dest_sources,
            "last_checked": CHECKED_AT,
            "coverage_status": "official_verified",
            "coverage_note": "已整合國立陽明交通大學 115-2、115-1 出國交換計畫簡章、113–115 學年度 6 個學期名額表、全球姐妹校合約表、雙聯學位表、獎學金辦法與 31 國歷屆學長姐交換心得報告。",
        })

        research_records.append({
            "home_university": "國立陽明交通大學",
            "school_name": full_name,
            "country": country,
            "official_website": website,
            "verification_status": "official_verified",
            "discovery_source_url": source_url,
            "checked_at": CHECKED_AT,
            "note": f"國立陽明交通大學國際事務處出國交換名額表、全球姐妹校合約表（{factsheet_url or source_url}）及 ROR/Wikidata 官方網址核對完成。",
        })

        ev_sources = [
            {"title": f"國立陽明交通大學學生申請出國交換名額表與條件—{zh_name}", "url": source_url},
        ]
        if factsheet_url:
            ev_sources.append({"title": f"國立陽明交通大學出國交換名額表 Fact Sheet—{zh_name}", "url": factsheet_url})
        if website:
            ev_sources.append({"title": f"{full_name} 官方網站", "url": website})
        if exp_posts:
            ev_sources.append({
                "title": f"國立陽明交通大學赴 {zh_name} 交換生心得報告（{exp_posts[0].get('academic_year') or '歷年'}學年度）",
                "url": exp_posts[0].get("url") or exp_country_url,
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
                "scope": "國立陽明交通大學出國交換名額表住宿與生活資訊",
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
                "scope": "國立陽明交通大學交換生費用規定、A/B/C 類獎學金（含拓荒者計畫）／經濟不利補助與地區生活費估算",
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
                "scope": "國立陽明交通大學交換生選課限制、大學部 3 門／研究所 2 門專業課全數及格門檻與返國學分抵免規定",
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
                "scope": "國立陽明交通大學出國交換簽證、海外醫療保險與緩徵役男出境提醒",
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
                        f"｜陽明交大國際處官網公開收錄赴 {zh_name} 歷屆交換生期中／期末心得報告共 {len(exp_posts)} 篇。"
                        if exp_posts
                        else ""
                    )
                ),
                "sources": ev_sources,
                "checked_at": CHECKED_AT,
                "scope": "國立陽明交通大學出國交換名額與歷屆學長姐交換心得報告",
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
                "已整合國立陽明交通大學 115-2、115-1 出國交換計畫簡章、113–115 學年度名額表、全球姐妹校合約表與 31 國歷屆交換生期中／期末心得報告。",
                "當期宿位供給、費用與選課限制請依姐妹校最新 Factsheet 及課程目錄核對。",
            ],
            "location_signature": f"verified:{location_obj['latitude']}:{location_obj['longitude']}:representative",
            "extraction_version": 3,
        })

        sample_reports: list[dict] = []
        for p_item in exp_posts[:5]:
            p_url = p_item.get("url") or exp_country_url
            ay = p_item.get("academic_year")
            term_str = f"{ay}學年度" if ay else "歷年交換"
            sum_clean = clean_text(p_item.get("summary") or "")
            lbl_clean = clean_text(p_item.get("label") or "")
            sample_reports.append({
                "title": f"{sum_clean}（{lbl_clean}）" if sum_clean and lbl_clean else (sum_clean or f"國立陽明交通大學赴 {zh_name} 交換學生心得報告"),
                "url": p_url,
                "term": term_str,
            })

        if exp_posts:
            latest_post = exp_posts[0]
            terms_covered = list(
                dict.fromkeys(
                    f"{p.get('academic_year')}學年度"
                    for p in exp_posts
                    if p.get("academic_year")
                )
            )
            rep_title = (
                f"國立陽明交通大學赴 {zh_name}（共 {len(exp_posts)} 篇期中／期末報告）交換學生心得彙編"
            )
            latest_summary = clean_text(latest_post.get("summary") or zh_name)
            summary_text = (
                f"國立陽明交通大學國際事務處「學生心得分享」專區公開收錄赴 {zh_name} 交換學生期中與期末報告共 {len(exp_posts)} 篇"
                + (f"（涵蓋學年度：{'、'.join(terms_covered[:6])}）" if terms_covered else "")
                + f"，代表篇目包含《{latest_summary}》，詳實記錄陽明交大交換生行前簽證準備、姐妹校專業課程選課（大學部每學期至少 3 門／研究所至少 2 門）、學生宿舍申請與當地生活開銷。"
            )
            theme_map = {
                "academics": f"陽明交大交換生分享於 {zh_name} 之選課流程、英語或當地語言授課體驗、大學部每學期至少 3 門／研究所至少 2 門專業課程及格規定與返國學分抵免實務。",
                "housing": f"陽明交大交換生於期中與期末心得中分享 {zh_name} 校內學生宿舍或校外租屋申請方式、月租費用與生活機能（{housing_clean[:120]}）。",
                "campus_culture": f"陽明交大國際處收錄 {len(exp_posts)} 篇赴 {zh_name} 歷屆交換生期中／期末心得報告，提供學弟妹第一手校園生活與跨文化交流指南。",
                "cost": f"陽明交大交換生於心得中記錄赴 {zh_name} 之機票、簽證、住宿與每月生活費開銷（{cost_default}），以及陽明交大 A/B 類出國交換獎學金與教育部學海飛颺申請經驗。",
            }
            p_url = latest_post.get("url") or exp_country_url
            ay = latest_post.get("academic_year")
            student_experience_rows.append({
                "school_name": full_name,
                "country": country,
                "title": rep_title,
                "source_url": p_url,
                "source_type": "article",
                "platform": "國立陽明交通大學國際事務處—學生心得分享專區",
                "author_name": latest_summary or "國立陽明交通大學返國交換學生",
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
                "exchange_term": f"{ay}學年度" if ay else "歷年交換",
                "summary_zh": summary_text,
                "original_summary": summary_text,
                "theme_summaries_zh": theme_map,
                "translation_status": "original",
                "source_kind": "official_experience_page",
            })

        experience_sources_records.append({
            "home_university": "國立陽明交通大學",
            "school_name": full_name,
            "country": country,
            "official_experience_portal_url": exp_country_url,
            "partner_page_url": factsheet_url or source_url,
            "report_count": len(exp_posts),
            "sample_reports": sample_reports,
            "checked_at": CHECKED_AT,
        })

    partners_jsonl_text = (
        "\n".join(json.dumps(r, ensure_ascii=False) for r in partners) + "\n"
    )
    (OFFICIAL_NYCU_DIR / "partners.jsonl").write_text(
        partners_jsonl_text, encoding="utf-8"
    )
    (SOURCES_NYCU_DIR / "partners.jsonl").write_text(
        partners_jsonl_text, encoding="utf-8"
    )
    (OFFICIAL_NYCU_DIR / "application_workflows.jsonl").write_text(
        "\n".join(json.dumps(r, ensure_ascii=False) for r in workflows) + "\n",
        encoding="utf-8",
    )
    (OFFICIAL_NYCU_DIR / "destination_profiles.jsonl").write_text(
        "\n".join(json.dumps(r, ensure_ascii=False) for r in destinations) + "\n",
        encoding="utf-8",
    )
    (OFFICIAL_NYCU_DIR / "partner_research.jsonl").write_text(
        "\n".join(json.dumps(r, ensure_ascii=False) for r in research_records) + "\n",
        encoding="utf-8",
    )
    (OFFICIAL_NYCU_DIR / "student_life.jsonl").write_text(
        "\n".join(json.dumps(r, ensure_ascii=False) for r in life_records) + "\n",
        encoding="utf-8",
    )
    (OFFICIAL_NYCU_DIR / "experience_sources.jsonl").write_text(
        "\n".join(
            json.dumps(r, ensure_ascii=False) for r in experience_sources_records
        )
        + "\n",
        encoding="utf-8",
    )
    (OFFICIAL_NYCU_DIR / "student_experiences.jsonl").write_text(
        "\n".join(
            json.dumps(r, ensure_ascii=False) for r in student_experience_rows
        )
        + "\n",
        encoding="utf-8",
    )
    (OFFICIAL_NYCU_DIR / "campus-locations.json").write_text(
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

    nycu_home_loc = {
        "school_name": "國立陽明交通大學",
        "country": "臺灣",
        "city": "新竹市東區",
        "latitude": 24.7868,
        "longitude": 120.9975,
        "geocode_status": "verified",
        "geocoded_at": CHECKED_AT,
        "source_url": "https://www.wikidata.org/wiki/Q104724092",
        "identity_source_url": "https://ror.org/00se2k293",
        "precision": "representative",
        "note": "校級代表位置：官方網域及國家已與 ROR 比對，座標來源為 Wikidata P625；實際交換校區以錄取通知為準。 母校代表點採新竹市東區大學路1001號光復校區浩然圖書資訊中心 8 樓（暨臺北市北投區立農街二段155號陽明校區行政大樓 2 樓）國際事務處；官方地址來源：https://oia.nycu.edu.tw/。",
    }
    existing_loc_map[("國立陽明交通大學", "臺灣")] = nycu_home_loc
    sorted_locs = sorted(
        existing_loc_map.values(),
        key=lambda r: (r.get("country") or "", r.get("school_name") or ""),
    )
    loc_file.write_text(
        "\n".join(json.dumps(r, ensure_ascii=False) for r in sorted_locs) + "\n",
        encoding="utf-8",
    )

    nycu_source_urls = [
        NYCU_OIA_HOME_URL,
        NYCU_OUTBOUND_TIMELINE_URL,
        NYCU_PORTAL_URL,
        NYCU_QUOTA_SHEET_URL,
        NYCU_CONTRACTS_SHEET_URL,
        NYCU_DUAL_DEGREE_SHEET_URL,
        NYCU_115_2_NOTICE_URL,
        NYCU_115_1_NOTICE_URL,
        NYCU_116_1_UST_NOTICE_URL,
        NYCU_115_2_GUIDELINES_PDF_URL,
        NYCU_115_2_APPROVAL_FORM_PDF_URL,
        NYCU_115_1_GUIDELINES_PDF_URL,
        NYCU_REGULATIONS_PAGE_URL,
        NYCU_REGULATIONS_ZH_PDF_URL,
        NYCU_REGULATIONS_EN_PDF_URL,
        NYCU_SCHOLARSHIP_LIST_URL,
        NYCU_SCHOLARSHIP_NOTICE_URL,
        NYCU_SCHOLARSHIP_TYPE_A_PDF_URL,
        NYCU_SCHOLARSHIP_TYPE_B_PDF_URL,
        NYCU_ECON_DISADVANTAGED_URL,
        NYCU_ECON_DISADVANTAGED_PDF_URL,
        NYCU_UST_NOTICE_PDF_URL,
        NYCU_DUAL_DEGREE_INTRO_URL,
        NYCU_EXPERIENCE_ASIA_URL,
        NYCU_EXPERIENCE_AMERICAS_URL,
        NYCU_EXPERIENCE_EUROPE_URL,
        NYCU_EXPERIENCE_OCEANIA_URL,
    ]

    exchange_info_payload = {
        "school_name": "國立陽明交通大學",
        "program_type": [
            "交換學生（校級及院系級出國交換學生計畫・涵蓋歐洲、美洲、亞洲、大洋洲及大陸港澳地區，每人至多選填 5 個志願，含 20 所「拓荒者計畫」紫色字體重點獎學金補助學校）",
            "臺灣聯合大學系統（UST）學生出國交換計畫（瑞士蘇黎世聯邦理工學院 ETH Zurich、瑞士伯恩大學、美國馬里蘭大學、加州大學聖地牙哥分校 UCSD、加州大學聖塔克魯茲分校 UCSC、澳洲新南威爾斯大學 UNSW、新加坡南洋理工大學 NTU、香港中文大學、香港城市大學）",
            "跨國雙聯學位計畫（全校 61 項學士、碩士、博士雙聯學位合作計畫）與 UMAP 亞太大學交流計畫",
        ],
        "academic_year": [
            "116（116學年度臺灣聯合大學系統［UST］學生出國交換計畫：即日起至 115年12月31日 16:00 受理校內收件；116學年度第一梯次校級出國交換預計 115年12月1日至116年1月5日 17:00 開放線上申請）",
            "115（115學年度第一梯次［115-1，含秋季班／春季班／一學年］及第二梯次［115-2 春季班］共開放 211 所交換學校，連同台聯大及歷年締約校共收錄 243 所全球合作大學）",
        ],
        "semester": [
            "第1學期（秋季班：每年約 8/9 月至 12 月／翌年 1 月；澳洲與紐西蘭對應 Semester 2 為 7 月至 11 月）",
            "第2學期（春季班：每年約 1/2 月至 5/6 月；日本前學期為 4 月至 8 月）",
            "一學年（第一梯次申請者可選擇出國交換一學期或一學年；第二梯次僅申請春季班一學期）",
        ],
        "application_period": [
            "【116學年度臺灣聯合大學系統（UST）學生出國交換計畫（2027 秋季／2028 春季學期交換與 2027 暑期研究交換）】陽明交大宣傳說明會：2026年12月3日（四）12:30；陽明交大校內收件截止日：2026年12月31日（四）16:00 止（由國際處初審後於 2027/01/11 前送台灣聯大系統，2027/02/28 前通知結果）。",
            "【第一梯次校級出國交換計畫甄選（申請秋季班、春季班或全學年出國交換）】線上申請期間：每年 12月1日 09:00 至翌年 1月5日 17:00 止（於 https://oia-sys.nycu.edu.tw/outgoing 填報至多 5 個志願並上傳完成五級核章之《申請簽核表》與書審文件）；初審放榜：1月中旬（115-1 為 01/19 17:00）；系統確認錄取並繳交保證金 NT$10,000：1月下旬（01/25 23:59 前）；出國交換獎學金申請截止：3月上旬（03/09 12:00）。",
            "【第二梯次校級出國交換計畫甄選（申請春季班出國交換）】線上申請期間：每年 6月1日 09:00 至 7月10日 17:00 止；初審放榜：7月24日 15:00；系統確認錄取並繳交保證金 NT$10,000：7月31日 17:00 前；出國交換獎學金申請截止：10月31日。",
        ],
        "eligibility": [
            "【學籍與年級限制】申請人須為國立陽明交通大學正式學籍生，且「交換生不得為大學部一年級新生」（大學部二年級以上、碩士班一年級以上、博士班一年級以上可申請；國防部專案計畫「系統工程與科技學士學位學程」學生由國防部專案辦理，不適用校級交換辦法）。各校系所限制以主修或雙主修為準，年級限制以「出國交換時之年級」為準。",
            "【書面審查總分 60 分門檻與配分權重】校內甄選採書面審查，審查總分未達 60 分者不予錄取。配分比重：（1）國外及港澳地區：大學部為「在校成績 50%、外語能力 20%、自傳 10%、讀書計畫 15%、其他表現 5%」，研究所為「在校成績 30%、外語能力 20%、自傳 20%、讀書計畫 25%、其他表現 5%」；（2）大陸地區：大學部為「在校成績 60%、自傳 15%、讀書計畫 20%、其他表現 5%」，研究所為「在校成績 40%、自傳 25%、讀書計畫 30%、其他表現 5%」。總分相同時依序參酌：1. 志願序、2. 讀書計畫、3. 外語能力、4. 在校成績。",
            "【出國修課門檻、報告義務與 10,000 元保證金沒收規定】交換期間須完成陽明交大註冊、繳交全額學雜費並選修 0 學分《海外學期交換》課程；大學部學生每學期至少須修習 3 門專業課程、研究所學生每學期至少須修習 2 門專業課程，且「所有修習課程皆須及格」。若有一門以上（含）修課不及格、因個人因素放棄交換，或未按期繳交期中報告（4/30 或 10/31 前）與期末報告（7/31 或 1/31 前），將全額沒收保證金新臺幣 10,000 元！",
        ],
        "language_requirement": [
            "【國外及港澳地區強制檢附外語證明規定】依《國立陽明交通大學學生申請出國交換計畫簡章》規定，申請赴國外或港澳地區交換者，不論該姐妹校是否訂有語言能力分數限制，皆須於申請截止日前提交有效語言能力成績證明（TOEFL iBT、IELTS Academic、全民英檢複試通過證書，或交換校指定之日語 JLPT、韓語 TOPIK、德語、法語、西語檢定）。",
            "【多益 TOEIC 須含聽讀說寫四項測驗之特別規定】簡章與獎學金辦法明訂：若使用多益（TOEIC）成績申請出國交換或校內出國交換獎學金，成績單必須同時包含「聽力、閱讀、口說與寫作」四項測驗（A 類及 B 類獎學金門檻為聽力 400 分、閱讀 385 分、口說 150 分、寫作 150 分以上）。",
            "【大陸地區語言規定】申請赴大陸地區交換者，校內書面審查不列外語能力配分，惟若接待學校針對英文授課課程訂有語言門檻者，仍須符合該校規定。",
        ],
        "required_documents": [
            "1. 國立陽明交通大學學生出國交換申請簽核表（於 https://oia-sys.nycu.edu.tw/outgoing 填報列印後，須經申請人、家長／監護人、導師／指導教授、系所主任及學院院長五級核章；雙主修生以第二主修申請者須加會第二主修系主任及院長）",
            "2. 英文歷年成績單（大學部須含累計班排名或系排名百分比；研究所須含累計 GPA，碩一、博一新生未有本校成績者須上傳前一學位含畢業排名之成績單）",
            "3. 有效外語能力證明（申請國外及港澳地區必繳；使用 TOEIC 者須同時包含聽力、閱讀、口說與寫作測驗）",
            "4. 中英文自傳（含個人學經歷背景與申請動機）",
            "5. 中英文讀書計畫（含擬赴姐妹校修讀之專業課程規劃、研究主題及未來展望，占書審 15%–30%）",
            "6. 其他優秀表現證明（社團幹部、學術競賽獲獎、論文發表、語檢超標或低收／中低收／特殊境遇家庭證明等，占書審 5%）",
        ],
        "scholarship_info": [
            "（A類）國立陽明交通大學「優秀學生出國交換獎學金」（《優秀學生出國交換獎學金辦法》）：補助具中華民國國籍之全職一般生（不含在職專班、雙聯學位及赴大陸港澳交換生）一學期或一學年約新臺幣 50,000–360,000 元。申請門檻：大學部歷年班或系排名前 50%（赴亞洲地區）或前 20%（赴非亞洲地區），研究所歷年 GPA 3.7 以上；語言須達 TOEFL iBT 83／IELTS 6.0／全民英檢中高級／TOEIC（聽400、讀385、說150、寫150）。錄取名額表紫色字體標示之 20 所「拓荒者計畫（Trailblazer Program）」學校者，優先獲得較高額度補助！",
            "（B類）國立陽明交通大學「學士班優秀入學生出國短期進修獎學金」：專項補助大學部在學學生赴國外著名大學短期進修交換，每學期新臺幣 100,000–150,000 元、每學年 200,000–300,000 元。申請門檻：大學部歷年平均成績 80 分（GPA 3.38）以上、出國前於陽明交大修畢至少 3 門英語授課（EMI）課程，且語言達 TOEFL iBT 87／IELTS 6.5／全民英檢中高級／TOEIC（聽400、讀385、說150、寫150）。",
            "（C類）教育部「學海飛颺」與「學海惜珠」計畫：學海飛颺與校內 A/B 類獎學金聯合受理評選；學海惜珠專項補助持有政府核發之低收入戶、中低收入戶或特殊境遇家庭證明之本國籍學生赴國外（不含大陸及港澳）交換，不受班系排名百分比限制。",
            "國立陽明交通大學「經濟不利學生短期出國獎助金（高教深耕完善就學協助計畫）」：補助低收入戶、中低收入戶、身心障礙、特殊境遇家庭、原住民或獲大專弱勢助學金之學生出國交換，每學期最高補助新臺幣 100,000 元（可與校內出國交換獎學金同時兼領，不得與教育部學海計畫兼領）。",
            "外國政府與締約姐妹校交換獎學金：包含日本台灣交流協會短期留學生獎學金（每月 JPY 80,000）、亞太大學交流會（UMAP）獎學金、德國巴登符騰堡邦獎學金、奧地利 Ernst Mach 獎學金等。",
        ],
        "partner_universities": [p["school_name"] for p in partners],
        "source_urls": nycu_source_urls,
        "last_checked": CHECKED_AT,
    }
    (OFFICIAL_NYCU_DIR / "exchange_info.json").write_text(
        json.dumps(exchange_info_payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    student_dashboard_payload = {
        "school_name": "國立陽明交通大學",
        "last_checked": CHECKED_AT,
        "academic_score_minimum": 60.0,
        "academic_score_rule": "校級出國交換採書面審查，審查總分未達 60 分者不予錄取（國外及港澳配分：大學部在校成績 50%、外語 20%、自傳 10%、讀書計畫 15%、其他表現 5%，研究所在校成績 30%、外語 20%、自傳 20%、讀書計畫 25%、其他表現 5%；大陸地區配分：大學部在校成績 60%、自傳 15%、讀書計畫 20%、其他表現 5%，研究所在校成績 40%、自傳 25%、讀書計畫 30%、其他表現 5%）。A 類優秀學生出國交換獎學金門檻為大學部排名前 50%（亞洲）／前 20%（非亞洲）或研究所 GPA 3.7 以上。",
        "academic_gpa_minimum": 3.0,
        "maximum_preferences": 5,
        "selection_rules": {
            "academic_policy": "gpa_or_rank",
            "academic_reference_year": "116",
            "undergraduate_gpa_minimum": 2.7,
            "undergraduate_rank_maximum": 50.0,
            "graduate_academic_exempt": False,
            "exclude_in_service": False,
            "pending_quota_planning": False,
            "partner_requirements_need_confirmation": False,
            "degree_score_minimums": {
                "undergraduate": 60.0,
                "graduate": 60.0,
            },
            "excluded_undergraduate_years": ["大一"],
            "language_certificate_required": True,
        },
        "language_score_minimums": {
            "toefl": 79.0,
            "ielts": 6.0,
            "toeic": 785.0,
        },
        "application_periods": [
            {
                "title": "116學年度臺灣聯合大學系統（UST）學生出國交換計畫甄選（說明會 12/03、陽明交大校內收件至 12/31 16:00 止）",
                "details": [
                    "合作學校：瑞士伯恩大學、瑞士蘇黎世聯邦理工學院（ETH Zurich）、新加坡南洋理工大學（NTU）、香港中文大學（新亞書院／理學院／工學院）、香港城市大學、美國加州大學聖塔克魯茲分校（UC Santa Cruz）、美國馬里蘭大學、美國加州大學聖地牙哥分校（UC San Diego）、澳洲新南威爾斯大學（UNSW），涵蓋 116-1（2027 秋季）、116-2（2028 春季）學期交換與 2027 暑期研究交換。",
                    "申請資格與期限：前一學年平均成績達 GPA 3.0 或 B 以上，並具 2 年內有效之 TOEFL iBT 或 IELTS 成績單。陽明交大宣傳說明會於 2026年12月3日（四）12:30 舉行；陽明交大校內收件截止日為 2026年12月31日（四）16:00 止（繳交至國際處劉小姐 ext. 50665），預計 2027年2月28日 前通知台灣聯大審查結果。",
                ],
                "source": {
                    "title": "國立陽明交通大學國際事務處—116學年度臺灣聯合大學系統學生出國交換計畫公告與簡章 PDF",
                    "source_url": NYCU_116_1_UST_NOTICE_URL,
                    "category": "exchange_application",
                    "summary": "116學年度台灣聯大學生出國交換計畫（含學期交換與暑期交換）名額表、申請條件與 12/31 校內收件截止日。",
                },
                "scope": "home_application",
                "program_types": ["exchange"],
                "academic_year": "116",
                "application_round": "116學年度臺灣聯合大學系統（UST）學生出國交換計畫（陽明交大收件至 2026/12/31 16:00 止）",
                "audience": "all_students",
                "opens_at": "2026-10-06T09:00:00+08:00",
                "deadline_at": "2026-12-31T16:00:00+08:00",
                "date_status": "verified_exact",
                "status": "open",
                "status_note": "116學年度臺灣聯合大學系統學生出國交換計畫已正式公告開放申請，陽明交大校內收件至 2026/12/31（四）16:00 止。",
                "deadline_note": "每種交換類別（學期或暑期）限填一份報名表、至多選填 2 個學校志願序，請於 2026/12/31 16:00 前將申請資料送達國際處。",
                "reminder_eligible": True,
                "checked_at": CHECKED_AT,
            },
            {
                "title": "國立陽明交通大學校級出國交換學生計畫—第一梯次甄選（每年 12/01 09:00 至翌年 01/05 17:00 線上申請，適用秋季班、春季班或一學年交換）",
                "details": [
                    "申請時程（以 115-1 簡章與國際處公告之固定時段為準）：每年 12月1日 09:00 至翌年 1月5日 17:00 止於「陽明交大出國交換學生申請系統」（https://oia-sys.nycu.edu.tw/outgoing）開放線上申請（可申請次學年秋季班、春季班或全學年出國交換，每人至多選填 5 個志願）。",
                    "後續重要日程：1月中旬（01/19 17:00）於系統公告校內初審結果；1月下旬（01/25 23:59 前）正備取生確認錄取並匯款繳交保證金新臺幣 10,000 元；3月上旬（03/09 12:00 前）截止受理出國交換獎學金申請。",
                ],
                "source": {
                    "title": "國立陽明交通大學出國交換計畫申請時段與第一梯次申請簡章 PDF",
                    "source_url": NYCU_115_1_GUIDELINES_PDF_URL,
                    "category": "exchange_application",
                    "summary": "陽明交大第一梯次（12/1–1/5）校級出國交換申請流程、五級簽核表、書審配分、保證金與獎學金時程。",
                },
                "scope": "home_application",
                "program_types": ["exchange"],
                "academic_year": "116",
                "application_round": "校級出國交換計畫第一梯次甄選（每年12月1日09:00至翌年1月5日17:00線上申請）",
                "audience": "all_students",
                "opens_at": "2026-12-01T09:00:00+08:00",
                "deadline_at": "2027-01-05T17:00:00+08:00",
                "date_status": "verified_exact",
                "status": "upcoming",
                "status_note": "依陽明交大國際處《出國交換計畫時段》公告，第一梯次固定於每年 12月1日 至翌年 1月上旬開放線上申請。",
                "deadline_note": "《學生出國交換申請簽核表》須完成導師／指導教授、系所主任及學院院長核章，請務必提早送簽並於截止前上傳系統。",
                "reminder_eligible": True,
                "checked_at": CHECKED_AT,
            },
            {
                "title": "國立陽明交通大學校級出國交換學生計畫—第二梯次春季班甄選（每年 06/01 09:00 至 07/10 17:00 線上申請，10/31 獎學金截止）",
                "details": [
                    "申請時程（115-2 簡章基準）：每年 6月1日 09:00 至 7月10日 17:00 止於線上申請系統受理次學年第 2 學期（春季班）出國交換申請；7月24日 15:00 公告校內初審結果；7月31日 17:00 前完成系統確認並繳交新臺幣 10,000 元保證金。",
                    "春季班出國交換獎學金申請：錄取春季班出國交換且符合 A 類、B 類、教育部學海飛颺／惜珠或經濟不利學生短期出國獎助金資格者，於每年 10月31日 前提出獎學金申請。",
                ],
                "source": {
                    "title": "國立陽明交通大學 115學年度第2學期學生申請出國交換計畫簡章 PDF",
                    "source_url": NYCU_115_2_GUIDELINES_PDF_URL,
                    "category": "exchange_application",
                    "summary": "陽明交大第二梯次（春季班 6/1–7/10）校級出國交換甄選時程、211 所當期開放學校名額表與 10/31 獎學金申請。",
                },
                "scope": "home_application",
                "program_types": ["exchange"],
                "academic_year": "116",
                "application_round": "校級出國交換計畫第二梯次春季班甄選（每年6月1日09:00至7月10日17:00線上申請）",
                "audience": "all_students",
                "opens_at": "2027-06-01T09:00:00+08:00",
                "deadline_at": "2027-07-10T17:00:00+08:00",
                "date_status": "reference_only",
                "status": "upcoming",
                "status_note": "第二梯次（春季班）校級出國交換固定於每年 6月1日 至 7月上旬開放線上申請；115-2 春季班交換獎學金於 10月31日 截止。",
                "deadline_note": "實際截止日期請依國際事務處 2027 年 5 月公告之 116-2 出國交換計畫簡章為準。",
                "reminder_eligible": False,
                "checked_at": CHECKED_AT,
            },
        ],
        "program_overview": [
            {
                "title": f"國立陽明交通大學國際事務處出國交換計畫總覽（{len(partners)} 所全球合作大學・{trailblazer_count} 所拓荒者計畫重點學校・61 項雙聯學位）",
                "details": [
                    f"國立陽明交通大學國際事務處（光復校區浩然圖書資訊中心 8 樓／陽明校區行政大樓 2 樓）每年分兩梯次（12月1日–1月5日 及 6月1日–7月10日）辦理校級及院系級出國交換甄選，並參與「臺灣聯合大學系統（UST）學生出國交換計畫」。本平台完整收錄 {len(partners)} 所官方海外與大陸港澳合作大學（含當期開放申請之 {open_partner_count} 所交換學校，以及 {len(partners) - open_partner_count} 所歷年或締約合作姐妹校）。",
                    f"陽明交大首創於《出國交換名額表》以紫色字體標示 {trailblazer_count} 所歐美日韓頂尖「拓荒者計畫（Trailblazer Program）」重點學校（符合 A 類優秀學生出國交換獎學金資格者優先獲得較高額度補助，最高可達新臺幣 36 萬元），同時提供 B 類學士班優秀入學生短期進修獎學金（10萬–30萬元）、經濟不利學生短期出國獎助金（每學期最高 10 萬元）及教育部學海飛颺／惜珠計畫，官網並公開收錄 31 國共 2,389 份歷屆交換生期中與期末心得報告（涵蓋 {len(student_experience_rows)} 所合作校）。",
                ],
                "source": {
                    "title": "國立陽明交通大學國際事務處—出國交換計畫時段與全球合作學校名額表",
                    "source_url": NYCU_OUTBOUND_TIMELINE_URL,
                    "category": "exchange_application",
                    "summary": "陽明交大第一、二梯次出國交換甄選簡章、243 所合作大學、20 所拓荒者計畫重點學校與 31 國交換生心得報告。",
                },
            }
        ],
        "eligibility": [
            {
                "title": "學籍年級規定（大二／碩一／博一以上）、書審總分 60 分門檻、國外與大陸地區四類配分權重及 5 志願分發機制",
                "details": [
                    "年級與學籍資格：限陽明交大大學部二年級以上、碩士班一年級以上、博士班一年級以上正式學籍生（交換生不得為大學部一年級新生；國防部專案計畫「系統工程與科技學士學位學程」學生由國防部專案辦理，不適用校級交換辦法）。各校系所限制以主修或雙主修為準，年級限制以「出國交換時之年級」為準。",
                    "書面審查配分與及格標準：審查總分未達 60 分者不予錄取。配分權重：（1）國外及港澳地區：大學部為「在校成績 50%、外語能力 20%、自傳 10%、讀書計畫 15%、其他表現 5%」，研究所為「在校成績 30%、外語能力 20%、自傳 20%、讀書計畫 25%、其他表現 5%」；（2）大陸地區：大學部為「在校成績 60%、自傳 15%、讀書計畫 20%、其他表現 5%」，研究所為「在校成績 40%、自傳 25%、讀書計畫 30%、其他表現 5%」。",
                    "志願選填與同分參酌：每人至多選填 5 所志願學校；書審總分相同時，依序以（1）志願序、（2）讀書計畫、（3）外語能力、（4）在校成績高分者優先錄取。",
                ],
                "source": {
                    "title": "國立陽明交通大學學生申請出國交換實施辦法與申請簡章 PDF",
                    "source_url": NYCU_REGULATIONS_ZH_PDF_URL,
                    "category": "exchange_application",
                    "summary": "陽明交大出國交換實施辦法、書審總分 60 分門檻、配分權重與同分參酌順序。",
                },
            }
        ],
        "language_requirements": [
            {
                "title": "國外及港澳地區強制檢附外語證明規定、多益 TOEIC 須含「聽讀說寫」四項測驗與 A/B 類獎學金語檢門檻",
                "details": [
                    "國外及港澳地區強制檢附規定：依簡章第陸點規定，申請赴國外或港澳地區交換者，不論該姐妹校是否訂有語言能力分數限制，皆須於申請截止日前提交有效語言能力成績證明（TOEFL iBT、IELTS Academic、全民英檢複試通過，或交換校指定之日語 JLPT、韓語 TOPIK、德法西語檢定）。",
                    "多益 TOEIC 特別規定与獎學金門檻：若使用 TOEIC 成績申請出國交換或獎學金，成績單必須同時包含「聽力、閱讀、口說與寫作」四項測驗！申請 A 類優秀學生出國交換獎學金須達 TOEFL iBT 83／IELTS 6.0／全民英檢中高級／TOEIC（聽400、讀385、說150、寫150）；申請 B 類獎學金須達 TOEFL iBT 87／IELTS 6.5。",
                ],
                "source": {
                    "title": "國立陽明交通大學學生申請出國交換計畫簡章與優秀學生出國交換獎學金辦法 PDF",
                    "source_url": NYCU_115_1_GUIDELINES_PDF_URL,
                    "category": "exchange_application",
                    "summary": "陽明交大外語檢定強制必繳規定、TOEIC 聽讀說寫四項要求與各校語言限制。",
                },
            }
        ],
        "required_documents": [
            {
                "title": "五級核章《學生出國交換申請簽核表》、6 項線上應繳文件與 10,000 元保證金（任一門不及格沒收）規定",
                "details": [
                    "線上申請應上傳文件（於 https://oia-sys.nycu.edu.tw/outgoing 提交）：1. 學生出國交換申請簽核表（須經本人、家長／監護人、導師／指導教授、系所主任及學院院長簽章；雙主修生以第二主修申請者須加會第二主修系主任及院長）、2. 英文歷年成績單（大學部含累計排名百分比、研究所含累計 GPA；碩博一新生附前一學位含畢業排名之成績單）、3. 有效外語能力證明、4. 中英文自傳、5. 中英文讀書計畫、6. 其他優秀表現證明。",
                    "10,000 元保證金與修課及格義務：錄取生須繳交保證金新臺幣 10,000 元（低收、中低收及特殊境遇家庭免繳）。交換期間大學部每學期至少須修習 3 門專業課程、研究所每學期至少須修習 2 門專業課程，且「所有修習課程皆須及格」（若有一門以上［含］修課不及格者，全額沒收保證金！），並須按期繳交期中報告（4/30 或 10/31 前）與期末報告（7/31 或 1/31 前，附 3–5 張照片）後無息退還。",
                ],
                "source": {
                    "title": "國立陽明交通大學學生出國交換申請簽核表與申請簡章 PDF",
                    "source_url": NYCU_115_2_APPROVAL_FORM_PDF_URL,
                    "category": "exchange_application",
                    "summary": "陽明交大五級核章簽核表、應繳文件規格、專業課全數及格要求與 10,000 元保證金退費規定。",
                },
            }
        ],
        "scholarship_info": [
            {
                "title": "A 類優秀學生獎學金（5萬–36萬，含 20 所拓荒者計畫重點校）、B 類獎學金（10萬–30萬）、經濟不利補助（10萬）與學海飛颺／惜珠",
                "details": [
                    "（A類）優秀學生出國交換獎學金（約 50,000–360,000 元）：開放大學部排名前 50%（赴亞洲）或前 20%（赴非亞洲）、研究所 GPA 3.7 以上，且達 TOEFL iBT 83／IELTS 6.0／GEPT 中高級／TOEIC（L400/R385/S150/W150）之本國籍一般生申請；錄取名額表紫色字體標示之 20 所「拓荒者計畫（Trailblazer Program）」重點學校者，優先核給較高額度獎學金。",
                    "（B類）學士班優秀入學生出國短期進修獎學金（每學期 10萬–15萬元、每學年 20萬–30萬元）：限大學部平均 80 分（GPA 3.38）以上、修畢 3 門英語授課課程且達 TOEFL iBT 87／IELTS 6.5 者；另設有「經濟不利學生短期出國獎助金」（每學期最高 10 萬元，可與校內獎學金兼領）、教育部「學海飛颺」、「學海惜珠」及日本台灣交流協會／UMAP 獎學金。",
                ],
                "source": {
                    "title": "國立陽明交通大學國際事務處—出國交換獎學金專區與 A/B 類及經濟不利獎助辦法",
                    "source_url": NYCU_SCHOLARSHIP_LIST_URL,
                    "category": "scholarship",
                    "summary": "陽明交大 A 類（含拓荒者計畫）、B 類、C 類學海系列與經濟不利學生短期出國獎助金辦法。",
                },
            }
        ],
        "document_explanations": [
            {
                "title": "國立陽明交通大學《學生出國交換申請簽核表》五級核章流程、TOEIC 四項測驗與英文成績單排名規範",
                "summary": "說明陽明交大出國交換申請簽核表之導師、系主任、院長簽核程序，以及英文歷年成績單與 TOEIC 聽讀說寫四項成績證明規格。",
                "key_points": [
                    "申請人於線上系統（https://oia-sys.nycu.edu.tw/outgoing）完成資料填寫後，須列印《學生出國交換申請簽核表》，依序由學生本人、家長或監護人、導師或指導教授、系所（專班／學位學程）主任及學院院長簽章後掃描上傳。",
                    "英文歷年成績單：大學部學生必須包含「累計班排名或系排名百分比」；研究所學生須包含累計 GPA（碩一、博一新生若尚無陽明交大成績單，須上傳前一學位含畢業排名之成績單）。",
                    "外語檢定證明：申請赴國外及港澳地區交換者一律必繳；若採計 TOEIC 成績，必須同時檢附「聽力、閱讀、口說與寫作」四項測驗成績單。",
                ],
                "applies_to": [],
                "source": {
                    "title": "國立陽明交通大學學生出國交換申請簽核表與簡章 PDF",
                    "source_url": NYCU_115_2_APPROVAL_FORM_PDF_URL,
                    "category": "exchange_application",
                    "summary": None,
                },
                "document_url": NYCU_115_2_APPROVAL_FORM_PDF_URL,
                "document_type": "official_document",
                "full_text_extracted": True,
            }
        ],
        "rule_explanations": [
            {
                "title": "國立陽明交通大學出國交換實施辦法：書審總分 60 分門檻、專業課全數及格與 10,000 元保證金退費規定",
                "summary": "規範陽明交大校級出國交換書面審查配分權重、志願分發同分參酌順序、出國期間最低專業課程修習門檻與保證金沒收條件。",
                "key_points": [
                    "書面審查總分未達 60 分者不予錄取；總分相同時依序參酌：（1）志願序、（2）讀書計畫、（3）外語能力、（4）在校成績。",
                    "交換期間須選修陽明交大 0 學分《海外學期交換》課程，大學部每學期至少修習 3 門專業課程、研究所每學期至少修習 2 門專業課程，且「所有修習課程皆須及格」。",
                    "若於姐妹校有一門以上（含）修課不及格、未按時繳交期中（4/30 或 10/31）與期末報告（7/31 或 1/31），或因個人因素放棄交換資格，新臺幣 10,000 元保證金將全額沒收。",
                ],
                "applies_to": [],
                "source": {
                    "title": "國立陽明交通大學學生申請出國交換實施辦法 PDF",
                    "source_url": NYCU_REGULATIONS_ZH_PDF_URL,
                    "category": "exchange_application",
                    "summary": None,
                },
                "document_url": NYCU_REGULATIONS_ZH_PDF_URL,
                "document_type": "official_document",
                "full_text_extracted": True,
            }
        ],
        "sources": [
            {
                "title": "國立陽明交通大學國際事務處—出國交換計畫時段與申請總覽",
                "source_url": NYCU_OUTBOUND_TIMELINE_URL,
                "category": "exchange_application",
                "summary": None,
            },
            {
                "title": "國立陽明交通大學學生申請出國交換名額表（113–115學年度 6 學期完整試算表，含 20 所拓荒者計畫重點學校）",
                "source_url": NYCU_QUOTA_SHEET_URL,
                "category": "partner_school",
                "summary": None,
            },
            {
                "title": "國立陽明交通大學全球姐妹校合約一覽表（Partner Institutions Contract List）",
                "source_url": NYCU_CONTRACTS_SHEET_URL,
                "category": "partner_school",
                "summary": None,
            },
            {
                "title": "國立陽明交通大學跨國雙聯學位合作學校一覽表（61 項雙聯計畫）",
                "source_url": NYCU_DUAL_DEGREE_SHEET_URL,
                "category": "partner_school",
                "summary": None,
            },
            {
                "title": "國立陽明交通大學 115學年度第1學期（第一梯次）學生申請出國交換計畫簡章 PDF",
                "source_url": NYCU_115_1_GUIDELINES_PDF_URL,
                "category": "exchange_application",
                "summary": None,
            },
            {
                "title": "國立陽明交通大學 115學年度第2學期（第二梯次）學生申請出國交換計畫簡章 PDF",
                "source_url": NYCU_115_2_GUIDELINES_PDF_URL,
                "category": "exchange_application",
                "summary": None,
            },
            {
                "title": "國立陽明交通大學 116學年度臺灣聯合大學系統（UST）學生出國交換計畫公告與簡章 PDF",
                "source_url": NYCU_116_1_UST_NOTICE_URL,
                "category": "exchange_application",
                "summary": None,
            },
            {
                "title": "國立陽明交通大學國際事務處—出國交換獎學金專區（A類、B類、學海飛颺／惜珠、經濟不利學生短期出國獎助金）",
                "source_url": NYCU_SCHOLARSHIP_LIST_URL,
                "category": "scholarship",
                "summary": None,
            },
            {
                "title": "國立陽明交通大學國際事務處—出國交換學生心得分享專區（亞洲、美洲、歐洲、大洋洲 31 國共 2,389 篇報告）",
                "source_url": NYCU_EXPERIENCE_ASIA_URL,
                "category": "partner_school",
                "summary": None,
            },
        ],
    }
    (OFFICIAL_NYCU_DIR / "student_dashboard.json").write_text(
        json.dumps(student_dashboard_payload, ensure_ascii=False, indent=2)
        + "\n",
        encoding="utf-8",
    )

    pages_records = [
        {
            "title": "國立陽明交通大學：第一梯次（12/1–1/5）、第二梯次（6/1–7/10）校級出國交換與 116-1 台灣聯大交換時程",
            "source_url": NYCU_OUTBOUND_TIMELINE_URL,
            "published_at": "2026-10-06T00:00:00Z",
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
            "title": "國立陽明交通大學：出國交換申請資格、書審總分 60 分門檻、配分權重、專業課全數及格與 10,000 元保證金規定",
            "source_url": NYCU_REGULATIONS_ZH_PDF_URL,
            "published_at": "2026-10-06T00:00:00Z",
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
            "title": "國立陽明交通大學：國外及港澳地區強制檢附外語證明規定與 TOEIC 聽讀說寫四項測驗要求",
            "source_url": NYCU_115_1_GUIDELINES_PDF_URL,
            "published_at": "2026-10-06T00:00:00Z",
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
            "title": "國立陽明交通大學：五級核章《學生出國交換申請簽核表》、6 項線上應繳文件與期中／期末報告義務",
            "source_url": NYCU_115_2_APPROVAL_FORM_PDF_URL,
            "published_at": "2026-10-06T00:00:00Z",
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
            "title": "國立陽明交通大學：A 類優秀學生獎學金（5萬–36萬，含拓荒者計畫）、B 類獎學金（10萬–30萬）、經濟不利補助与學海計畫",
            "source_url": NYCU_SCHOLARSHIP_LIST_URL,
            "published_at": "2026-10-06T00:00:00Z",
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
    (OFFICIAL_NYCU_DIR / "pages.jsonl").write_text(
        "\n".join(json.dumps(p, ensure_ascii=False) for p in pages_records)
        + "\n",
        encoding="utf-8",
    )

    home_rules = {
        "school_id": "nycu",
        "school_name": "國立陽明交通大學",
        "eligibility": student_dashboard_payload["eligibility"],
        "application_periods": student_dashboard_payload["application_periods"],
        "selection_rules": {
            "minimum_review_total_score": 60.0,
            "weights_international_undergraduate": {
                "academic_grade": 0.50,
                "foreign_language": 0.20,
                "autobiography": 0.10,
                "study_plan": 0.15,
                "other_achievements": 0.05,
            },
            "weights_international_graduate": {
                "academic_grade": 0.30,
                "foreign_language": 0.20,
                "autobiography": 0.20,
                "study_plan": 0.25,
                "other_achievements": 0.05,
            },
            "weights_mainland_undergraduate": {
                "academic_grade": 0.60,
                "autobiography": 0.15,
                "study_plan": 0.20,
                "other_achievements": 0.05,
            },
            "weights_mainland_graduate": {
                "academic_grade": 0.40,
                "autobiography": 0.25,
                "study_plan": 0.30,
                "other_achievements": 0.05,
            },
            "tie_breaker_order": [
                "preference_rank",
                "study_plan",
                "foreign_language",
                "academic_grade",
            ],
            "deposit_twd": 10000,
            "deposit_low_income_twd": 0,
            "max_preferences": 5,
            "minimum_passed_professional_courses_undergraduate": 3,
            "minimum_passed_professional_courses_graduate": 2,
            "any_failed_course_forfeits_deposit": True,
            "midterm_report_due": "開學後 2 個月內（4/30 或 10/31 前）",
            "final_report_due": "交換結束後 1 個月內（7/31 或 1/31 前，附 3–5 張照片）",
        },
        "source_urls": nycu_source_urls,
        "verified_at": "2026-10-19",
    }
    (OFFICIAL_NYCU_DIR / "home_rules.json").write_text(
        json.dumps(home_rules, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    (OFFICIAL_NYCU_DIR / "documents.json").write_text(
        json.dumps(
            {
                "school_name": "國立陽明交通大學",
                "required_documents": student_dashboard_payload["required_documents"],
                "source_urls": nycu_source_urls,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    (OFFICIAL_NYCU_DIR / "scholarships.json").write_text(
        json.dumps(
            {
                "school_name": "國立陽明交通大學",
                "scholarships": student_dashboard_payload["scholarship_info"],
                "source_urls": nycu_source_urls,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    completeness = {
        "school_id": "nycu",
        "school_name": "國立陽明交通大學",
        "total_partners": len(partners),
        "partner_count": len(partners),
        "international_partners": sum(
            1 for p in partners if p["country"] not in {"中國大陸", "香港", "澳門"}
        ),
        "mainland_partners": sum(
            1 for p in partners if p["country"] in {"中國大陸", "香港", "澳門"}
        ),
        "trailblazer_partners": trailblazer_count,
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
        "active_term": "116學年度臺灣聯合大學系統（UST）學生出國交換計畫即日起至 2026/12/31 16:00 受理校內收件（12/03 12:30 說明會）；校級第一梯次出國交換（秋季班／春季班／一學年）於每年 12/01 09:00 至翌年 01/05 17:00 開放線上申請，第二梯次（春季班）於 06/01 至 07/10 17:00 開放申請（共開放 214 所交換學校，含 20 所拓荒者計畫重點學校）。",
        "verified_at": "2026-10-19",
    }
    (OFFICIAL_NYCU_DIR / "catalog-completeness.json").write_text(
        json.dumps(completeness, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    (OFFICIAL_NYCU_DIR / "verification_status.json").write_text(
        json.dumps(
            {
                "school_id": "nycu",
                "school_name": "國立陽明交通大學",
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
            "sources/nycu/exchange_quotas.xlsx",
            NYCU_QUOTA_SHEET_URL,
            "國立陽明交通大學學生申請出國交換名額表（113-1 至 115-2 共 6 學期完整試算表，含紫色字體拓荒者計畫標記）XLSX",
        ),
        (
            "sources/nycu/partner_contracts.xlsx",
            NYCU_CONTRACTS_SHEET_URL,
            "國立陽明交通大學全球姐妹校合約一覽表（Partner Institutions Contract List）XLSX",
        ),
        (
            "sources/nycu/dual_degree.xlsx",
            NYCU_DUAL_DEGREE_SHEET_URL,
            "國立陽明交通大學跨國雙聯學位合作學校一覽表（61 項雙聯學位計畫）XLSX",
        ),
        (
            "sources/nycu/115-2-guidelines.pdf",
            NYCU_115_2_GUIDELINES_PDF_URL,
            "國立陽明交通大學 115學年度第2學期（第二梯次）學生申請出國交換計畫簡章 PDF",
        ),
        (
            "sources/nycu/115-1-guidelines.pdf",
            NYCU_115_1_GUIDELINES_PDF_URL,
            "國立陽明交通大學 115學年度第1學期（第一梯次）學生申請出國交換計畫簡章 PDF",
        ),
        (
            "sources/nycu/115-2-approval-form.pdf",
            NYCU_115_2_APPROVAL_FORM_PDF_URL,
            "國立陽明交通大學學生出國交換申請簽核表 PDF",
        ),
        (
            "sources/nycu/exchange-regulations-zh.pdf",
            NYCU_REGULATIONS_ZH_PDF_URL,
            "國立陽明交通大學學生申請出國交換實施辦法（中文版）PDF",
        ),
        (
            "sources/nycu/exchange-regulations-en.pdf",
            NYCU_REGULATIONS_EN_PDF_URL,
            "國立陽明交通大學學生申請出國交換實施辦法（英文版）PDF",
        ),
        (
            "sources/nycu/scholarship-type-a-reg.pdf",
            NYCU_SCHOLARSHIP_TYPE_A_PDF_URL,
            "國立陽明交通大學優秀學生出國交換獎學金辦法（A類）PDF",
        ),
        (
            "sources/nycu/scholarship-type-b-reg.pdf",
            NYCU_SCHOLARSHIP_TYPE_B_PDF_URL,
            "國立陽明交通大學學士班優秀入學生出國短期進修獎學金辦法（B類）PDF",
        ),
        (
            "sources/nycu/econ-disadvantaged-reg.pdf",
            NYCU_ECON_DISADVANTAGED_PDF_URL,
            "國立陽明交通大學經濟不利學生短期出國獎助金實施要點 PDF",
        ),
        (
            "sources/nycu/ust-116-1-notice-1.pdf",
            NYCU_UST_NOTICE_PDF_URL,
            "116學年度臺灣聯合大學系統（UST）學生出國交換計畫公告與學校總表 PDF",
        ),
        (
            "sources/nycu/nycu_dual_degree_programs.json",
            NYCU_DUAL_DEGREE_SHEET_URL,
            "國立陽明交通大學 61 項跨國雙聯學位合作計畫結構化資料集 JSON",
        ),
        (
            "sources/nycu/nycu_experience_reports.json",
            NYCU_EXPERIENCE_ASIA_URL,
            "國立陽明交通大學 31 國 160 組合作大學共 2,389 份歷屆交換生期中／期末心得報告索引 JSON",
        ),
        (
            "sources/nycu/nycu_catalog_source.json",
            NYCU_QUOTA_SHEET_URL,
            "國立陽明交通大學 243 所出國交換合作大學整合資料集（214 所當期開放 + 29 所歷年／締約合作校，含 20 所拓荒者計畫重點學校與 117 校交換心得）JSON",
        ),
        (
            "sources/nycu/nycu_resolved_locations.json",
            NYCU_QUOTA_SHEET_URL,
            "國立陽明交通大學 243 所出國交換合作大學 ROR / Wikidata 地理座標核對表 JSON",
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
        "school_id": "nycu",
        "school_name": "國立陽明交通大學",
        "generated_at": CHECKED_AT,
        "active_cycle_note": completeness["active_term"],
        "sources": prov_sources,
    }
    prov_text = json.dumps(provenance_payload, ensure_ascii=False, indent=2) + "\n"
    (OFFICIAL_NYCU_DIR / "import_provenance.json").write_text(
        prov_text, encoding="utf-8"
    )
    (OFFICIAL_NYCU_DIR / "import-provenance.json").write_text(
        prov_text, encoding="utf-8"
    )

    from exchange_info.nycu_source_review import review_bundle
    review_bundle(REPO_ROOT)

    from exchange_info.generated_content_review import review_generated_content
    review_generated_content(REPO_ROOT, "nycu", round_id=20)
    review_generated_content(REPO_ROOT, "nycu", round_id=21)
    from exchange_info.vilnius_akita_review import apply_vilnius_akita_review
    apply_vilnius_akita_review(REPO_ROOT, "nycu")

    print(
        f"Successfully built NYCU catalog: {len(partners)} partners ({open_partner_count} open, "
        f"{trailblazer_count} trailblazers, {completeness['verified_campus_images']} verified images, "
        f"{completeness['verified_locations']} verified locations), {len(workflows)} workflows, "
        f"{len(destinations)} destinations, {len(research_records)} research records, "
        f"{exp_covered_schools} schools with experience records ({len(student_experience_rows)} rows)."
    )


if __name__ == "__main__":
    main()
