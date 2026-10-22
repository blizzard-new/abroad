"""Build the official Feng Chia University (逢甲大學, FCU) exchange data bundle."""

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
from exchange_info.fcu_source_review import apply_program_review, load_reviewed_programs

SOURCES_FCU_DIR = REPO_ROOT / "sources" / "fcu"
OFFICIAL_FCU_DIR = REPO_ROOT / "src" / "exchange_info" / "official_data" / "fcu"
STATIC_DIR = REPO_ROOT / "src" / "exchange_info" / "static"

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
    "土耳其": "亞洲",
    "美國": "美洲",
    "加拿大": "美洲",
    "墨西哥": "美洲",
    "巴西": "美洲",
    "智利": "美洲",
    "澳洲": "大洋洲",
    "紐西蘭": "大洋洲",
    "奧地利": "歐洲",
    "比利時": "歐洲",
    "捷克": "歐洲",
    "丹麥": "歐洲",
    "芬蘭": "歐洲",
    "法國": "歐洲",
    "德國": "歐洲",
    "希臘": "歐洲",
    "匈牙利": "歐洲",
    "義大利": "歐洲",
    "荷蘭": "歐洲",
    "波蘭": "歐洲",
    "羅馬尼亞": "歐洲",
    "俄羅斯": "歐洲",
    "西班牙": "歐洲",
    "瑞典": "歐洲",
    "瑞士": "歐洲",
    "英國": "歐洲",
}

REGION_COST_DEFAULTS = {
    "美國": (
        "USD 1,400–2,200 / 月（含住宿、餐飲、校園保險與當地交通）",
        "建議預留強制校園醫療保險（約 USD 1,500–2,500 / 學期）與 J-1 / F-1 簽證 SEVIS 費用。",
    ),
    "加拿大": (
        "CAD 1,500–2,200 / 月（含住宿、膳食、省級／校內醫保與市區交通）",
        "須投保接待校指定醫療保險並辦理 Study Permit 或 eTA。",
    ),
    "英國": (
        "GBP 1,100–1,600 / 月（含學生宿舍、飲食與大眾運輸）",
        "交換一學期（6 個月內）可辦理 Standard Visitor 簽證，一學年須辦理 Student Visa 並繳納 IHS 醫療附加費。",
    ),
    "法國": (
        "EUR 850–1,400 / 月（巴黎地區約 EUR 1,200–1,600 / 月；可申請 CAF 房補）",
        "須透過法國教育中心（Campus France）面試並申辦長期學生簽證（VLS-TS）。",
    ),
    "德國": (
        "EUR 934–1,200 / 月（德國簽證限制提領帳戶基準為每月 EUR 934）",
        "須辦理德國法定公保（約 EUR 120–130 / 月）及學期雜費／學期票（Semesterticket）。",
    ),
    "奧地利": (
        "EUR 850–1,250 / 月（含林茲／維也納／格拉茨學生宿舍、餐飲與大眾運輸）",
        "交換一學期（6 個月內）須申辦奧地利學生簽證 D（Visa D），超過 6 個月須申辦學生居留許可。",
    ),
    "西班牙": (
        "EUR 800–1,250 / 月（含學生公寓、飲食與大眾運輸）",
        "須備妥涵蓋全額醫療與遺體運返之私人醫療保險以申辦西班牙學生簽證。",
    ),
    "義大利": (
        "EUR 800–1,300 / 月（米蘭與羅馬約 EUR 1,000–1,400 / 月；杜林與威尼斯約 EUR 800–1,100 / 月）",
        "須向義大利經濟貿易文化推廣辦事處申辦學生簽證 D，抵義後 8 個工作天內申辦居留證（Permesso di Soggiorno）。",
    ),
    "荷蘭": (
        "EUR 950–1,400 / 月（荷蘭移民局 IND 財力證明基準約 EUR 1,225 / 月）",
        "由接待校代辦 MVV/VVR 居留許可，格羅寧根與代爾夫特房源緊張建議獲提名後立即申請宿舍。",
    ),
    "比利時": (
        "EUR 850–1,200 / 月（含布魯塞爾／列日學生宿舍、餐飲與大眾運輸）",
        "須辦理長期學生簽證 D 簽，抵達後向市政廳登記居留。",
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
    "芬蘭": (
        "EUR 750–1,100 / 月（芬蘭移民局 Migri 財力證明基準約 EUR 800 / 月）",
        "須透過 Enter Finland 申辦學生居留許可並投保涵蓋全期之醫療保險。",
    ),
    "捷克": (
        "EUR 600–900 / 月（含布拉格／奧斯特拉瓦學生宿舍、食堂與市區交通卡）",
        "須提前預約捷克經濟文化辦事處申辦長期學生簽證與捷克合約醫療保險。",
    ),
    "匈牙利": (
        "EUR 600–900 / 月（布達佩斯生活與住宿開支實惠）",
        "須向匈牙利貿易辦事處申辦長期居留簽證（D 簽）並備妥歐盟規格醫療保險。",
    ),
    "希臘": (
        "EUR 650–950 / 月（雅典外宿與日常飲食交通開支）",
        "須向希臘簽證中心或指定代表處申辦國家長期學生簽證（Type D）並備妥歐盟規格醫療保險。",
    ),
    "羅馬尼亞": (
        "EUR 500–800 / 月（布加勒斯特與蒂米什瓦拉學生宿舍與生活成本低廉）",
        "須憑羅馬尼亞教育部入學許可核准函申辦 D/SD 學生簽證。",
    ),
    "俄羅斯": (
        "USD 500–850 / 月（聖彼得堡與托木斯克校內宿舍費用實惠）",
        "須憑接待校核發之俄羅斯聯邦移民署官方邀請函向莫北協駐臺代表處申辦學生簽證。",
    ),
    "土耳其": (
        "EUR 550–850 / 月（伊斯坦堡與安卡拉學生生活與交通開支實惠）",
        "須申辦土耳其學生簽證並於抵土後申辦短期學生居留證（Ikamet）與當地醫保。",
    ),
    "澳洲": (
        "AUD 1,800–2,600 / 月（含雪梨／布里斯本／墨爾本／阿德雷德住宿與日常開支）",
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
        "RMB 2,000–3,800 / 月（校內宿舍與學生食堂費用低廉，上海、北京、南京、武漢、廈門生活機能完善）",
        "持臺胞證（臺灣居民來往大陸通行證）入境，並依接待校規定投保大陸境內來華留學生綜合醫療保險（約 RMB 400 / 學期）。",
    ),
    "香港": (
        "HKD 6,500–10,500 / 月（含香港嶺南大學／香港恒生大學校內宿舍與日常開支）",
        "須透過接待校向香港入境事務處申辦學生簽證／進入許可（Student Visa / Entry Permit）。",
    ),
    "新加坡": (
        "SGD 1,200–2,000 / 月（含住宿、熟食中心餐飲與地鐵交通）",
        "須透過新加坡移民局 SOLAR 系統申辦 Student's Pass（STP）並繳納接待校強制醫療保險。",
    ),
    "馬來西亞": (
        "MYR 1,500–2,500 / 月（吉隆坡與金寶生活機能便利且物價親民）",
        "須透過 EMGS（Education Malaysia Global Services）系統申辦學生簽證（VAL / Student Pass）。",
    ),
    "泰國": (
        "THB 15,000–25,000 / 月（曼谷與清邁生活成本親民）",
        "須憑接待校入學許可向泰國貿易經濟辦事處申辦 Non-Immigrant ED 學生簽證。",
    ),
    "印尼": (
        "IDR 5,000,000–9,000,000 / 月（泗水與棉蘭生活開支實惠）",
        "須由接待校協助向印尼移民總局申辦學習簽證（C316 / 學生電子簽證）。",
    ),
    "越南": (
        "USD 400–700 / 月（約 VND 10,000,000–17,000,000，河內與同奈生活成本低廉）",
        "須憑接待校入學許可透過越南駐臺辦事處申辦 DH 學生簽證。",
    ),
    "印度": (
        "USD 400–700 / 月（清奈校內住宿與日常開支實惠）",
        "須憑接待校正式入學許可向印度台北協會申辦 Student Visa。",
    ),
    "墨西哥": (
        "USD 700–1,100 / 月（約 MXN 13,000–20,000，瓜達拉哈拉與普埃布拉生活開支適中）",
        "交換一學期（180 天內）依國籍與簽證規定辦理入境，超過 180 天須申辦墨西哥學生臨時居留簽證。",
    ),
}

# Official 115-1 Admitted & Scholarship Records (from fcu_115_1_spring2027_intl_admitted.pdf & fcu_115_1_spring2027_mainland_admitted.pdf)
ADMITTED_115_1: dict[str, dict] = {
    "大東文化大學": {
        "count": 1,
        "type": "交換學生-學費互免",
        "depts": ["人文社會學院外國語文學系（1名）"],
        "scholarships": [],
        "pdf_url": "https://service825.fcu.edu.tw/infofiles/F_dvdjo5xweac25492665.pdf",
    },
    "立命館大學": {
        "count": 1,
        "type": "交換學生-學費互免",
        "depts": ["人文社會學院外國語文學系（1名）"],
        "scholarships": [],
        "pdf_url": "https://service825.fcu.edu.tw/infofiles/F_dvdjo5xweac25492665.pdf",
    },
    "名城大學": {
        "count": 1,
        "type": "交換學生-學費互免",
        "depts": ["人文社會學院外國語文學系（1名）"],
        "scholarships": [],
        "pdf_url": "https://service825.fcu.edu.tw/infofiles/F_dvdjo5xweac25492665.pdf",
    },
    "西敏寺大學": {
        "count": 2,
        "type": "交換學生-自費",
        "depts": ["人文社會學院外國語文學系（2名）"],
        "scholarships": [],
        "pdf_url": "https://service825.fcu.edu.tw/infofiles/F_dvdjo5xweac25492665.pdf",
    },
    "東國大學": {
        "count": 2,
        "type": "交換學生-學費互免",
        "depts": ["人文社會學院外國語文學系（1名）", "金融學院財務金融學系（1名）"],
        "scholarships": ["出國研修獎助學金 NT$9,000（1名）"],
        "pdf_url": "https://service825.fcu.edu.tw/infofiles/F_dvdjo5xweac25492665.pdf",
    },
    "近畿大學": {
        "count": 1,
        "type": "交換學生-學費互免",
        "depts": ["人文社會學院外國語文學系（1名）"],
        "scholarships": ["出國研修獎助學金 NT$9,000（1名）"],
        "pdf_url": "https://service825.fcu.edu.tw/infofiles/F_dvdjo5xweac25492665.pdf",
    },
    "威斯康辛大學麥迪遜分校": {
        "count": 1,
        "type": "交換學生-自費",
        "depts": ["人文社會學院外國語文學系（1名）"],
        "scholarships": [],
        "pdf_url": "https://service825.fcu.edu.tw/infofiles/F_dvdjo5xweac25492665.pdf",
    },
    "內華達大學拉斯維加斯分校": {
        "count": 1,
        "type": "交換學生-自費",
        "depts": ["工程與科學學院工業工程與系統管理學系（1名）"],
        "scholarships": [],
        "pdf_url": "https://service825.fcu.edu.tw/infofiles/F_dvdjo5xweac25492665.pdf",
    },
    "琉球大學": {
        "count": 1,
        "type": "交換學生-學費互免",
        "depts": ["工程與科學學院化學工程學系（1名）"],
        "scholarships": [],
        "pdf_url": "https://service825.fcu.edu.tw/infofiles/F_dvdjo5xweac25492665.pdf",
    },
    "加州大學爾灣分校": {
        "count": 3,
        "type": "交換學生-自費",
        "depts": [
            "工程與科學學院材料科學與工程學系（1名）",
            "商學院會計學系（1名）",
            "資訊電機學院電機工程學系（1名）",
        ],
        "scholarships": [],
        "pdf_url": "https://service825.fcu.edu.tw/infofiles/F_dvdjo5xweac25492665.pdf",
    },
    "紐倫堡大學": {
        "count": 2,
        "type": "交換學生-學費互免",
        "depts": ["工程與科學學院材料科學與工程學系（2名）"],
        "scholarships": [],
        "pdf_url": "https://service825.fcu.edu.tw/infofiles/F_dvdjo5xweac25492665.pdf",
    },
    "新潟大學": {
        "count": 2,
        "type": "交換學生-學費互免",
        "depts": [
            "工程與科學學院航太與系統工程學系（1名）",
            "資訊電機學院電子工程學系（1名）",
        ],
        "scholarships": [],
        "pdf_url": "https://service825.fcu.edu.tw/infofiles/F_dvdjo5xweac25492665.pdf",
    },
    "舊金山州立大學": {
        "count": 1,
        "type": "交換學生-自費",
        "depts": ["工程與科學學院航太與系統工程學系（1名）"],
        "scholarships": [],
        "pdf_url": "https://service825.fcu.edu.tw/infofiles/F_dvdjo5xweac25492665.pdf",
    },
    "聖道大學": {
        "count": 1,
        "type": "交換學生-學費互免",
        "depts": ["金融學院財務工程與精算學士學位學程（1名）"],
        "scholarships": [],
        "pdf_url": "https://service825.fcu.edu.tw/infofiles/F_dvdjo5xweac25492665.pdf",
    },
    "布魯塞爾管理學院": {
        "count": 2,
        "type": "交換學生-學費互免",
        "depts": ["金融學院財務金融學系（1名）", "商學院國際經營與貿易學系（1名）"],
        "scholarships": [],
        "pdf_url": "https://service825.fcu.edu.tw/infofiles/F_dvdjo5xweac25492665.pdf",
    },
    "勃艮第－第戎高等商學院": {
        "count": 2,
        "type": "交換學生-學費互免",
        "depts": ["金融學院財務金融學系（2名）"],
        "scholarships": ["出國研修獎助學金 NT$13,000（1名）"],
        "pdf_url": "https://service825.fcu.edu.tw/infofiles/F_dvdjo5xweac25492665.pdf",
    },
    "海登海姆雙元制大學": {
        "count": 2,
        "type": "交換學生-學費互免",
        "depts": [
            "建設學院土地管理學系（1名）",
            "創能學院人工智慧技術與應用學士學位學程（1名）",
        ],
        "scholarships": [
            "出國研修獎助學金 NT$9,000（1名）",
            "出國研修獎助學金 NT$13,000（1名）",
        ],
        "pdf_url": "https://service825.fcu.edu.tw/infofiles/F_dvdjo5xweac25492665.pdf",
    },
    "布達佩斯科技經濟大學": {
        "count": 2,
        "type": "交換學生-學費互免",
        "depts": [
            "建設學院都市計畫與空間資訊學系（1名）",
            "商學院國際經營與貿易學系（1名）",
        ],
        "scholarships": ["出國研修獎助學金 NT$9,000（1名）"],
        "pdf_url": "https://service825.fcu.edu.tw/infofiles/F_dvdjo5xweac25492665.pdf",
    },
    "雅典經商大學": {
        "count": 1,
        "type": "交換學生-學費互免",
        "depts": ["建設學院運輸與物流學系（1名）"],
        "scholarships": [],
        "pdf_url": "https://service825.fcu.edu.tw/infofiles/F_dvdjo5xweac25492665.pdf",
    },
    "建國大學": {
        "count": 1,
        "type": "交換學生-學費互免",
        "depts": ["商學院合作經濟暨社會事業經營學系（1名）"],
        "scholarships": [],
        "pdf_url": "https://service825.fcu.edu.tw/infofiles/F_dvdjo5xweac25492665.pdf",
    },
    "山口大學": {
        "count": 3,
        "type": "交換學生-學費互免",
        "depts": ["商學院行銷學系（2名）", "商學院經濟學系碩士班（1名）"],
        "scholarships": ["出國研修獎助學金 NT$9,000（1名）"],
        "pdf_url": "https://service825.fcu.edu.tw/infofiles/F_dvdjo5xweac25492665.pdf",
    },
    "成均館大學": {
        "count": 2,
        "type": "交換學生-學費互免",
        "depts": ["商學院行銷學系（2名）"],
        "scholarships": ["出國研修獎助學金 NT$11,000（1名）"],
        "pdf_url": "https://service825.fcu.edu.tw/infofiles/F_dvdjo5xweac25492665.pdf",
    },
    "格羅寧根大學": {
        "count": 1,
        "type": "交換學生-學費互免",
        "depts": ["商學院行銷學系（1名）"],
        "scholarships": [],
        "pdf_url": "https://service825.fcu.edu.tw/infofiles/F_dvdjo5xweac25492665.pdf",
    },
    "葛洛寧恩漢斯應用科技大學": {
        "count": 1,
        "type": "交換學生-學費互免",
        "depts": ["商學院行銷學系（1名）"],
        "scholarships": [],
        "pdf_url": "https://service825.fcu.edu.tw/infofiles/F_dvdjo5xweac25492665.pdf",
    },
    "雷恩商學院": {
        "count": 1,
        "type": "交換學生-學費互免",
        "depts": ["商學院行銷學系（1名）"],
        "scholarships": [],
        "pdf_url": "https://service825.fcu.edu.tw/infofiles/F_dvdjo5xweac25492665.pdf",
    },
    "龍谷大學": {
        "count": 1,
        "type": "交換學生-自費",
        "depts": ["商學院行銷學系（1名）"],
        "scholarships": ["出國研修獎助學金 NT$8,000（1名）"],
        "pdf_url": "https://service825.fcu.edu.tw/infofiles/F_dvdjo5xweac25492665.pdf",
    },
    "拉卡邦先皇技術學院": {
        "count": 2,
        "type": "交換學生-學費互免",
        "depts": [
            "商學院國際企業管理全英語學士學位學程（1名）",
            "創能學院人工智慧技術與應用學士學位學程（1名）",
        ],
        "scholarships": [],
        "pdf_url": "https://service825.fcu.edu.tw/infofiles/F_dvdjo5xweac25492665.pdf",
    },
    "東亞大學": {
        "count": 1,
        "type": "交換學生-學費互免",
        "depts": ["商學院國際經營與貿易學系（1名）"],
        "scholarships": [],
        "pdf_url": "https://service825.fcu.edu.tw/infofiles/F_dvdjo5xweac25492665.pdf",
    },
    "辛辛那提大學": {
        "count": 1,
        "type": "雙聯學制-雙碩士（115-2至116-1學年度）",
        "depts": ["資訊電機學院電子工程學系碩士班（1名）"],
        "scholarships": [],
        "pdf_url": "https://service825.fcu.edu.tw/infofiles/F_dvdjo5xweac25492665.pdf",
    },
    "漢陽大學": {
        "count": 2,
        "type": "交換學生-學費互免",
        "depts": ["資訊電機學院電子工程學系（1名）", "資訊電機學院電機工程學系（1名）"],
        "scholarships": [],
        "pdf_url": "https://service825.fcu.edu.tw/infofiles/F_dvdjo5xweac25492665.pdf",
    },
    "武藏野大學": {
        "count": 1,
        "type": "交換學生-學費互免",
        "depts": ["資訊電機學院電機工程學系（1名）"],
        "scholarships": ["出國研修獎助學金 NT$13,000（1名）"],
        "pdf_url": "https://service825.fcu.edu.tw/infofiles/F_dvdjo5xweac25492665.pdf",
    },
    "安徽大學": {
        "count": 1,
        "type": "交換學生-學費互免",
        "depts": ["人文社會學院中國文學系（1名）"],
        "scholarships": ["出國研修獎助學金 NT$7,000（1名）"],
        "pdf_url": "https://service825.fcu.edu.tw/infofiles/F_lwv4fzkckfwf676fc73.pdf",
    },
    "南京大學": {
        "count": 3,
        "type": "交換學生-學費互免",
        "depts": [
            "金融學院財務工程與精算學士學位學程（1名）",
            "商學院合作經濟暨社會事業經營學系（1名）",
            "商學院統計學系（1名）",
        ],
        "scholarships": [
            "出國研修獎助學金 NT$11,000（1名）",
            "出國研修獎助學金 NT$7,000（1名）",
            "出國研修獎助學金 NT$5,000（1名）",
        ],
        "pdf_url": "https://service825.fcu.edu.tw/infofiles/F_lwv4fzkckfwf676fc73.pdf",
    },
    "福州大學": {
        "count": 1,
        "type": "交換學生-學費互免",
        "depts": ["建設學院都市計畫與空間資訊學系（1名）"],
        "scholarships": ["出國研修獎助學金 NT$10,000（1名）"],
        "pdf_url": "https://service825.fcu.edu.tw/infofiles/F_lwv4fzkckfwf676fc73.pdf",
    },
    "同濟大學": {
        "count": 14,
        "type": "交換學生-學費互免",
        "depts": [
            "建設學院土木工程學系（3名）",
            "建築專業學院建築學士學位學程（1名）",
            "商學院國際經營與貿易學系（1名）",
            "商學院合作經濟暨社會事業經營學系（1名）",
            "商學院行銷學系（4名）",
            "商學院財稅學系（1名）",
            "資訊電機學院電機工程學系（2名）",
        ],
        "scholarships": [
            "出國研修獎助學金 NT$10,000（1名）",
            "出國研修獎助學金 NT$7,000（3名）",
            "出國研修獎助學金 NT$6,000（1名）",
            "出國研修獎助學金 NT$4,000（2名）",
        ],
        "pdf_url": "https://service825.fcu.edu.tw/infofiles/F_lwv4fzkckfwf676fc73.pdf",
    },
    "天津大學": {
        "count": 2,
        "type": "交換學生-學費互免",
        "depts": ["商學院國際企業管理全英語學士學位學程（2名）"],
        "scholarships": [],
        "pdf_url": "https://service825.fcu.edu.tw/infofiles/F_lwv4fzkckfwf676fc73.pdf",
    },
    "廈門大學": {
        "count": 1,
        "type": "交換學生-學費互免",
        "depts": ["商學院合作經濟暨社會事業經營學系（1名）"],
        "scholarships": [],
        "pdf_url": "https://service825.fcu.edu.tw/infofiles/F_lwv4fzkckfwf676fc73.pdf",
    },
    "復旦大學": {
        "count": 2,
        "type": "交換學生-學費互免",
        "depts": [
            "商學院合作經濟暨社會事業經營學系（1名）",
            "商學院商學進修學士學位學程（1名）",
        ],
        "scholarships": [
            "出國研修獎助學金 NT$6,000（1名）",
            "出國研修獎助學金 NT$7,000（1名）",
        ],
        "pdf_url": "https://service825.fcu.edu.tw/infofiles/F_lwv4fzkckfwf676fc73.pdf",
    },
    "上海財經大學": {
        "count": 1,
        "type": "交換學生-學費互免",
        "depts": ["商學院合作經濟暨社會事業經營學系（1名）"],
        "scholarships": [],
        "pdf_url": "https://service825.fcu.edu.tw/infofiles/F_lwv4fzkckfwf676fc73.pdf",
    },
    "西南大學": {
        "count": 1,
        "type": "交換學生-學費互免",
        "depts": ["資訊電機學院資訊工程學系（1名）"],
        "scholarships": [],
        "pdf_url": "https://service825.fcu.edu.tw/infofiles/F_lwv4fzkckfwf676fc73.pdf",
    },
}

# Named Student Testimonials on https://oia.fcu.edu.tw/sap/ ("學長姐真心話")
NAMED_STORIES: dict[str, dict] = {
    "上奧地利應用科技大學": {
        "author": "纖維與複合材料學系 江明諺",
        "title": "逢甲大學學長姐真心話：纖複系 江明諺赴奧地利上奧地利應用科技大學交換心得",
        "quote": "Life begins at the end of your comfort zone — 大學期間到海外體驗交換學生生活一直是我大學必做清單中的一件事，有幸在我大四的最後一個學期來完成。想跟各位學弟妹分享這路走來的心路歷程，包含資料搜集、語言證明到最後選擇姐妹校。",
        "url": "https://oia.fcu.edu.tw/sap/",
    },
    "東南大學": {
        "author": "建築專業學院建築學系 林子瑜",
        "title": "逢甲大學學長姐真心話：建築系 林子瑜赴大陸東南大學交換心得",
        "quote": "生命的挑戰 勇敢地接受 不要放棄自己 — 去交換前，我對於種種困難而卻步，其實阻礙我們成功的不是客觀條件，而是我們心底的那份怯懦。給自己多一點鼓勵、多一點信心，勇敢地站起來面對挑戰，成功離你只是一步之差。",
        "url": "https://oia.fcu.edu.tw/sap/",
    },
    "紐倫堡大學": {
        "author": "國際經營與貿易學系 池濬竹",
        "title": "逢甲大學學長姐真心話：國貿系 池濬竹赴德國紐倫堡大學交換心得",
        "quote": "先做了再說，是我出國交換一開始的想法，非常感謝當初自己義無反顧的決定。一個人在完全陌生的國度過日子撐過 6 個月，從一開始凡事需要依賴朋友幫忙，到最後能獨自完成好多事。成長總是不容易的，別讓想太多成為無法進步的藉口。",
        "url": "https://oia.fcu.edu.tw/sap/",
    },
}


def clean_country(c: str, name_zh: str, name_en: str) -> str:
    c = (c or "").strip()
    if (
        "香港" in name_zh
        or "hong kong" in name_en.lower()
        or "lingnan" in name_en.lower()
    ):
        return "香港"
    mapping = {
        "南韓": "韓國",
        "澳大利亞": "澳洲",
        "美屬關島": "美國",
    }
    return mapping.get(c, c)


def clean_names(name_zh: str, name_en: str) -> tuple[str, str]:
    zh = re.sub(r"\s+", " ", (name_zh or "").strip())
    en = re.sub(r"\s+", " ", (name_en or "").strip())
    if zh == "關島大學" and en == "University of Guan":
        en = "University of Guam"
    if "香港恒生大學" in zh:
        zh = "香港恒生大學"
        en = "The Hang Seng University of Hong Kong"
    if zh == "安徽合肥工業大學":
        zh = "合肥工業大學"
    if zh == "西安西北大學":
        zh = "西北大學"
    return zh, en


def load_fcu_partner_items() -> list[dict]:
    p1151 = json.loads(
        (SOURCES_FCU_DIR / "oiasap_programs_1151.json").read_text(
            encoding="utf-8"
        )
    )["data"]
    p1142 = json.loads(
        (SOURCES_FCU_DIR / "oiasap_programs_1142.json").read_text(
            encoding="utf-8"
        )
    )["data"]

    by_xsh_1151: dict[str, list[dict]] = {}
    for r in p1151:
        if r["xsh_id"] in {"10498", "10298"}:
            continue
        by_xsh_1151.setdefault(r["xsh_id"], []).append(r)

    items: list[dict] = []
    by_full_name: dict[str, dict] = {}

    for xid, rows in by_xsh_1151.items():
        first = rows[0]
        zh, en = clean_names(first["name"], first["name_en"])
        full_name = f"{zh} {en}".strip()
        country = clean_country(first["country_name"], zh, en)
        web = (first.get("school_web_url") or "").strip()
        if full_name in by_full_name:
            by_full_name[full_name]["rows"].extend(rows)
            continue
        item = {
            "xsh_id": xid,
            "name_zh": zh,
            "name_en": en,
            "school_name": full_name,
            "country": country,
            "website": web,
            "availability_status": "open",
            "application_window_status": "closed",
            "rows": list(rows),
        }
        items.append(item)
        by_full_name[full_name] = item

    # Historical 114-2 school: 10102 西安西北大學 Northwest University
    for r in p1142:
        if r["xsh_id"] == "10102":
            zh, en = clean_names(r["name"], r["name_en"])
            full_name = f"{zh} {en}".strip()
            country = clean_country(r["country_name"], zh, en)
            web = (r.get("school_web_url") or "").strip()
            if full_name not in by_full_name:
                item = {
                    "xsh_id": "10102",
                    "name_zh": zh,
                    "name_en": en,
                    "school_name": full_name,
                    "country": country,
                    "website": web,
                    "availability_status": "reference_only",
                    "application_window_status": "closed",
                    "rows": [r],
                }
                items.append(item)
                by_full_name[full_name] = item

    collab_extra = [
        (
            "C001",
            "戴富德科技大學",
            "Delft University of Technology",
            "荷蘭",
            "https://www.tudelft.nl/",
        ),
        (
            "C002",
            "摩德納和雷焦艾米利亞大學",
            "University of Modena and Reggio Emilia",
            "義大利",
            "https://www.unimore.it/en",
        ),
        (
            "C003",
            "杜林理工大學",
            "Politecnico di Torino",
            "義大利",
            "https://www.polito.it/",
        ),
        (
            "C004",
            "米蘭理工大學",
            "Politecnico di Milano",
            "義大利",
            "https://www.polimi.it/en/",
        ),
        (
            "C005",
            "亞奧古雷爾·敕伊庫大學",
            "Aurel Vlaicu University of Arad",
            "羅馬尼亞",
            "https://uav.ro/",
        ),
        (
            "C006",
            "國立政治研究與公共行政大學",
            "National University of Political Studies and Public Administration",
            "羅馬尼亞",
            "https://snspa.ro/en/",
        ),
        (
            "C007",
            "蒂米什瓦拉西部大學",
            "West University of Timisoara",
            "羅馬尼亞",
            "https://www.uvt.ro/en/",
        ),
        (
            "C008",
            "九州大學",
            "Kyushu University",
            "日本",
            "https://www.kyushu-u.ac.jp/en/",
        ),
        (
            "C009",
            "日本女子大學",
            "Japan Women's University",
            "日本",
            "https://www.jwu.ac.jp/unv/",
        ),
        (
            "C010",
            "諾門森HKBP大學",
            "HKBP Nommensen University",
            "印尼",
            "https://uhn.ac.id/",
        ),
        (
            "C011",
            "越南國家大學河內工程技術大學",
            "VNU University of Engineering and Technology",
            "越南",
            "https://uet.vnu.edu.vn/en/",
        ),
        (
            "C012",
            "同奈科技大學",
            "Dong Nai Technology University",
            "越南",
            "https://dntu.edu.vn/",
        ),
        (
            "C013",
            "中國農業大學",
            "China Agricultural University",
            "中國大陸",
            "https://www.cau.edu.cn/",
        ),
        (
            "C014",
            "上海大學",
            "Shanghai University",
            "中國大陸",
            "https://www.shu.edu.cn/",
        ),
        (
            "C015",
            "中山大學",
            "Sun Yat-sen University",
            "中國大陸",
            "https://www.sysu.edu.cn/",
        ),
    ]
    for cid, zh, en, country, web in collab_extra:
        full_name = f"{zh} {en}".strip()
        if full_name not in by_full_name:
            item = {
                "xsh_id": cid,
                "name_zh": zh,
                "name_en": en,
                "school_name": full_name,
                "country": country,
                "website": web,
                "availability_status": "reference_only",
                "application_window_status": "closed",
                "rows": [],
            }
            items.append(item)
            by_full_name[full_name] = item

    return items


def format_lang_req(rows: list[dict], country: str) -> str:
    if not rows:
        if country == "中國大陸":
            return "大陸地區姊妹校免附外語能力檢定證明（須為本校在學學位生且歷年總平均 GPA 3.0 以上）"
        return "須檢附 2024/10/01 後應試取得之 TOEFL iBT、IELTS Academic、TOEIC 或日／歐語檢定證明（依當期簡章與姊妹校標準）"
    parts: list[str] = []
    for r in rows:
        lps = r.get("lang_proficiency") or []
        lp_strs = []
        for lp in lps:
            name = (lp.get("name") or "").strip()
            score = (lp.get("score") or "").strip()
            commit = (lp.get("commit") or "").strip()
            if not name or name in {"無", "不拘", "免"}:
                continue
            s = f"{name} {score}".strip()
            if commit:
                s += f"（{commit}）"
            lp_strs.append(s)
        if lp_strs:
            parts.append(" 或 ".join(lp_strs))
    dedup = list(dict.fromkeys(parts))
    if not dedup:
        if country == "中國大陸":
            return "大陸地區姊妹校免附外語檢定證明（在校歷年總平均 GPA 3.0 以上）"
        return "依姊妹校各組要求檢附有效外語能力檢定證明（TOEFL iBT / IELTS / TOEIC / JLPT / TOPIK）"
    return "；".join(dedup)


def format_colleges(rows: list[dict]) -> str:
    if not rows:
        return "全校各學院（依當期選送學生出國研修簡章與兩校協議規定辦理）"
    cols: list[str] = []
    for r in rows:
        for c in r.get("allow_colleges") or []:
            cname = (c.get("college_name") or "").strip()
            if cname and cname not in cols:
                cols.append(cname)
    if not cols or "無限制" in cols:
        return "不限學院（全校各學院皆可申請，須對照研修學校開課系所）"
    return "、".join(cols)


def format_study_levels(rows: list[dict]) -> str:
    if not rows:
        return "大學部、碩士班、博士班"
    levels: list[str] = []
    for r in rows:
        for sl in r.get("study_levels") or []:
            sname = (sl.get("study_level_name") or "").strip()
            if sname and sname not in levels:
                levels.append(sname)
    return "、".join(levels) if levels else "大學部、碩士班"


def format_quota(rows: list[dict], avail_status: str, zh_name: str) -> str:
    if not rows:
        if zh_name == "杜林理工大學":
            return "雙聯學位（1+1 雙碩士）及校級交換協議姐妹校（名額依當期簡章公告）"
        return "校級交換學生協議姐妹校（當期名額依國際事務處 oiasap 系統最新學期簡章公告）"
    q_parts: list[str] = []
    for r in rows:
        ptype = (r.get("program_type") or "學期交換").strip()
        ttype = ((r.get("tuition_type") or {}).get("name") or "").strip()
        q = str(r.get("quota") or "").strip()
        one_yr = "可申請1學年或1學期" if r.get("1year_apply") else "1學期"
        label = f"{ptype}（學費{ttype}・{one_yr}）：{q} 名" if ttype else f"{ptype}：{q} 名"
        if label not in q_parts:
            q_parts.append(label)
    res = "；".join(q_parts)
    adm = ADMITTED_115_1.get(zh_name)
    if adm:
        res += f"（115-1 初審實際錄取分發 {adm['count']} 名）"
    return res


def format_study_period(rows: list[dict]) -> str:
    if not rows:
        return "一學期或一學年"
    has_1yr = any(r.get("1year_apply") for r in rows)
    ptypes = list(
        dict.fromkeys((r.get("program_type") or "學期交換").strip() for r in rows)
    )
    if "雙聯學位" in ptypes and len(ptypes) > 1:
        return "交換一學期（或一學年）／雙聯學位 1–2 學年"
    if "雙聯學位" in ptypes:
        return "雙聯學位 1–2 學年（依兩校雙聯協議規定）"
    return "一學期或一學年（115-1 甄選赴 115-2 春季班為一學期；115-2 甄選可申請一學年或一學期）" if has_1yr else "一學期（115-2 春季班或 116-1 秋季班單學期交換）"


def format_program_type(rows: list[dict], avail_status: str, country: str) -> str:
    if avail_status == "reference_only":
        return "交換學生／雙聯學制（逢甲大學國際事務處簽約合作姐妹校）"
    ptypes = list(
        dict.fromkeys((r.get("program_type") or "學期交換").strip() for r in rows)
    )
    ttypes = list(
        dict.fromkeys(
            ((r.get("tuition_type") or {}).get("name") or "").strip()
            for r in rows
            if (r.get("tuition_type") or {}).get("name")
        )
    )
    region_tag = "大陸地區校級合作" if country == "中國大陸" else "國際地區校級合作"
    return f"交換學生（{region_tag}・{'／'.join(ptypes)}・學費{'／'.join(ttypes)}）"


def format_comments(rows: list[dict]) -> str:
    comments: list[str] = []
    for r in rows:
        c = (r.get("comment") or "").strip()
        if c and c not in comments:
            comments.append(re.sub(r"\s+", " ", c.replace("\r\n", " ").replace("\n", " ")))
    return " ｜ ".join(comments)


def extract_gpa_req(rows: list[dict], comment_str: str) -> str:
    m = re.search(r"GPA[:\s]*([0-9.]+(?:\s*/\s*[0-9.]+)?)", comment_str, re.I)
    has_1yr_waiver = any(
        r.get("1year_apply")
        and ((r.get("tuition_type") or {}).get("name") == "全免")
        for r in rows
    )
    base = "逢甲大學校內門檻：在校歷年總平均 GPA 3.0（含）以上（不可用固定百分制分數替代）"
    if has_1yr_waiver:
        base += "；申請一學年學費互免交換者歷年系排名須達前 50%"
    if m:
        base += f"｜接待校門檻：Overall GPA {m.group(1)}"
    return base


def review_home_workflow_scope(workflow: dict) -> None:
    """115-1 is a selection round for spring 2027, not a future-round rule."""
    workflow["applicability_status"] = "needs_confirmation"
    workflow["coverage_status"] = "official_partial"
    workflow["applicability_note"] = (
        "115-1共同條文與部分方案欄位已核對，個別合作校與雙聯方案全部步驟尚未完成適用性查核；"
        "本流程不能當作116學年度或其他梯次已核實的申請指引。"
    )
    workflow["effective_application_rounds"] = ["115-1"]
    for step in workflow["steps"]:
        step["scope"]["academic_years"] = ["115"]
        step["scope"]["application_rounds"] = ["115-1"]
    results = workflow["steps"][2]
    results["deadline_at"] = None
    results["deadline_status"] = "needs_confirmation"
    results["deadline_reminder_eligible"] = False
    results["timing"] = "115-1簡章預計9月下旬公告初審，並非錄取確認截止；繳件期限須依實際錄取通知。"


def main() -> None:
    OFFICIAL_FCU_DIR.mkdir(parents=True, exist_ok=True)
    SOURCES_FCU_DIR.mkdir(parents=True, exist_ok=True)

    items = load_fcu_partner_items()
    locs_raw = json.loads(
        (SOURCES_FCU_DIR / "fcu_resolved_locations.json").read_text(
            encoding="utf-8"
        )
    )
    loc_by_name = {r["school_name"]: r for r in locs_raw}

    manifest = json.loads(
        (STATIC_DIR / "assets" / "school-images.json").read_text(
            encoding="utf-8"
        )
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

    for idx, item in enumerate(items):
        full_name = item["school_name"]
        zh_name = item["name_zh"]
        en_name = item["name_en"]
        country = item["country"]
        region = REGION_BY_COUNTRY.get(country, "其他地區")
        avail_status = item["availability_status"]
        win_status = item["application_window_status"]
        if avail_status == "open":
            open_partner_count += 1

        rows = item["rows"]
        website = item["website"]
        if website and not website.startswith("http"):
            website = f"https://{website}"

        factsheet_url = None
        sharepoint_exp_url = None
        for r in rows:
            cc = (r.get("course_catalog") or "").strip()
            if cc and cc != "N/A" and cc.startswith("http"):
                factsheet_url = cc
                break
        for r in rows:
            sp = (r.get("student_experiences_url") or "").strip()
            if sp and sp != "N/A" and sp.startswith("http"):
                sharepoint_exp_url = sp
                break

        source_url = (
            "https://oiasap.fcu.edu.tw/"
            if rows
            else "https://oia.fcu.edu.tw/collaboration/"
        )

        raw_loc = loc_by_name[full_name]
        location_obj = {
            "school_name": full_name,
            "country": country,
            "city": raw_loc.get("city") or country,
            "latitude": float(raw_loc["latitude"]),
            "longitude": float(raw_loc["longitude"]),
            "geocode_status": "verified",
            "geocoded_at": "2026-10-17T05:35:00Z",
            "source_url": raw_loc.get("source_url") or "https://www.wikidata.org",
            "identity_source_url": (
                raw_loc.get("identity_source_url")
                or raw_loc.get("source_url")
                or "https://ror.org"
            ),
            "precision": "representative",
            "note": raw_loc.get("note")
            or "校級代表位置：官方網域及國家已與 ROR / Wikidata 比對；實際交換校區以錄取通知為準。",
        }
        new_locations.append(location_obj)

        comment_str = format_comments(rows)
        lang_req_str = format_lang_req(rows, country)
        colleges_str = format_colleges(rows)
        degree_levels_str = format_study_levels(rows)
        quota_str = format_quota(rows, avail_status, zh_name)
        study_period_str = format_study_period(rows)
        program_type = format_program_type(rows, avail_status, country)
        gpa_req_str = extract_gpa_req(rows, comment_str)

        if avail_status == "open":
            app_deadline_str = (
                "115-1 選送（赴 115-2 / 2027 春季班研修）線上申請已於 2026/07/27–2026/08/10 17:00 截止並於 2026/09/11 公告初審分發名單；"
                "115-2 選送（赴 116 學年度 / 2027 秋季班研修）將於 2026/11/16–11/20 舉辦國際研習週說明會，並於 2026 年 12 月中旬公告簡章與開放報名。"
            )
        else:
            app_deadline_str = (
                "本合作校為逢甲大學國際事務處簽約之交換／雙聯協議姐妹校；"
                "當期是否開放名額請以每年 6 月中旬及 12 月中旬公告之 oiasap 出國研修系統簡章為準。"
            )

        sem_dates_str = (
            "秋季班（第1學期）：約每年 8/9 月至翌年 1 月；春季班（第2學期）：約每年 2 月至 6/7 月（日本姊妹校春季班為 4 月至 8 月，秋季班為 9 月至翌年 2 月）"
        )
        course_rest_str = (
            f"開放申請院系：{colleges_str}（{degree_levels_str}）。"
            + (f"研修條件與選課備註：{comment_str}。" if comment_str else "")
            + "依逢甲大學規定，學士班非應屆畢業學生每學期至少修習 12 學分、學士班應屆畢業學生至少 9 學分、碩博士班至少 3 學分（特殊情況經系／學程主任核可並報教務處備查者例外）（獲教育部學海獎學金者須修習至少 4 學分本科系相關專業課程）。"
        )
        housing_str = (
            f"{zh_name} 原則上協助錄取交換生申請校內學生宿舍或推薦校外合作學生公寓（宿位依各校當期供給與申請先後核配，住宿費由學生自理）。"
        )

        tuition_points_list = [
            "出國研修期間須於逢甲大學完成註冊並繳交全額學雜費以保留本校在學學籍；屬「學費互免（全免）」交換計畫者免繳姊妹校學費，屬「部分減免」或「自費研修／雙聯」者依兩校協議繳納姊妹校規定費用。",
            "取得姊妹校入學許可後 2 週內須繳交保證金：獲獎助學金或學費互免交換生繳交新臺幣 10,000 元，自費交換生繳交新臺幣 5,000 元。返國後修課及格率達 1/2 以上、1 個月內繳交 2,000 字以上研習報告書，且學費互免／獲獎生完成每學期 50 小時志工服務（兩學期 100 小時）後無息退還。",
            "境外最低修課學分規定：學士班非應屆畢業學生每學期至少修讀 12 學分、學士班應屆畢業學生至少 9 學分、碩博士班至少 3 學分（特殊情況經系／學程主任核可並報教務處備查者例外）；獲教育部學海飛颺／惜珠獎學金者須修讀至少 4 學分與本科系相關之專業課程。",
        ]

        app_steps_list = [
            f"步驟一（確認資格與參加國際研習週說明會）：確認具逢甲大學正式在學學籍（大學部須入學滿一學期、原則上不得為延修生；研究生首學期即可申請）、在校歷年總平均 GPA 3.0（含）以上，並備妥 2024/10/01 後應試取得之外語檢定證明（大陸地區免附）。",
            f"步驟二（oiasap 線上系統填報與無紙化上傳）：於申請期限內登入逢甲大學「出國研修申請系統（https://oiasap.fcu.edu.tw/）」，擇一申請「國際地區」或「大陸地區」（至多填報 5 所志願學校），上傳 2 吋證件照、家長同意書（附件一）、1,000 字以上研修計畫（附件二）、學務處生輔組核章之獎懲紀錄、歷年成績單正本（國際地區須附英文成績單）、外語檢定證明及研究生指導教授同意書（附件三）。",
            "步驟三（校內初審評分分發與獎助學金同步審核）：由國際事務處依在校學業成績、外語能力及研修計畫進行初審分發，並自動同步審核「逢甲大學出國研修獎助學金」（名額與金額依預算及審查核定，非固定排名給付；經濟弱勢可附證明供審查）。",
            f"步驟四（姊妹校提名複審、繳交保證金與行前準備）：獲本校推薦資格後，依國際事務處承辦人通知完成 {full_name} 複審申請表件與宿舍登記；取得正式入學許可（LOA）後 2 週內繳交保證金（學費互免／獲獎生 NT$10,000、自費生 NT$5,000），參加行前說明會並辦理簽證、海外醫療及意外保險與學分抵免。",
        ]

        elig_points_list = [
            f"開放學制與年級：{degree_levels_str}（大學部須於逢甲就讀滿一學期以上，原則上不得為延修生；研究生入學首學期即可申請）",
            f"開放申請學院：{colleges_str}",
            f"學業成績要求：{gpa_req_str}",
            f"外語能力要求：{lang_req_str}",
        ]
        if comment_str:
            elig_points_list.append(f"姊妹校附加規定：{comment_str[:240]}")

        adm_rec = ADMITTED_115_1.get(zh_name)
        story_rec = NAMED_STORIES.get(zh_name)

        notes_lines = [
            f"【合作類別與期程】{program_type}｜研修期間：{study_period_str}",
            f"【當期名額與費用】{quota_str}",
            f"【開放學院與學制】{colleges_str}｜{degree_levels_str}",
            f"【語言與學業門檻】{lang_req_str}｜{gpa_req_str}",
        ]
        if comment_str:
            notes_lines.append(f"【姊妹校申請與選課備註】{comment_str}")
        if adm_rec:
            notes_lines.append(
                f"【115-1 初審分發實績】本梯次共錄取 {adm_rec['count']} 名逢甲學生赴 {zh_name}（{'、'.join(adm_rec['depts'])}）"
                + (
                    f"，獲核定 {'、'.join(adm_rec['scholarships'])}"
                    if adm_rec["scholarships"]
                    else ""
                )
                + "。"
            )
        if sharepoint_exp_url:
            notes_lines.append(
                f"【歷年學長姐心得】逢甲大學國際事務處 o365 SharePoint 資料庫收錄赴 {zh_name} 交換生返國研修心得作品專區。"
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
            "quota_status": "published",
            "availability_status": avail_status,
            "availability_note": f"逢甲大學國際事務處公告校級合作姐妹校；{quota_str}。",
            "academic_year": "115",
            "application_round": "115-1選送（115-2春季班出國）",
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
                "title": f"逢甲大學出國研修學校查詢與申請系統（oiasap）—{zh_name}",
                "source_url": source_url,
                "role": "home_university",
                "authority": "home_official_notice",
                "effective_academic_year": "115",
                "application_round": "115-1",
                "checked_at": "2026-10-17T05:35:00Z",
            },
            {
                "title": "逢甲大學 115-1 學年度選送學生出國研修簡章（校級合作）",
                "source_url": "https://oia.fcu.edu.tw/sap/introduction/",
                "role": "home_university",
                "authority": "home_official_notice",
                "effective_academic_year": "115",
                "application_round": "115-1",
                "checked_at": "2026-10-17T05:35:00Z",
            },
            {
                "title": "逢甲大學出國研修獎助學金與教育部學海計畫專區",
                "source_url": "https://oia.fcu.edu.tw/sap/scholarship/",
                "role": "home_university",
                "authority": "home_official_notice",
                "effective_academic_year": "115",
                "application_round": "115-1",
                "checked_at": "2026-10-17T05:35:00Z",
            },
        ]
        if website:
            wf_sources.append({
                "title": f"{full_name} 官方網站",
                "source_url": website,
                "role": "partner_university",
                "authority": "partner_official",
                "effective_academic_year": "115",
                "application_round": "115-1",
                "checked_at": "2026-10-17T05:35:00Z",
            })

        workflows.append({
            "home_university": "逢甲大學",
            "school_name": full_name,
            "partner_website": website,
            "country": country,
            "program_type": program_type,
            "academic_year": "115",
            "application_round": "115-1",
            "effective_application_rounds": [
                "115-1",
                "115-2",
                "第1學期（秋季班）",
                "第2學期（春季班）",
            ],
            "applicability_status": "verified",
            "applicability_note": (
                "逢甲大學 115-1 學年度選送學生出國研修（赴 115-2 / 2027 春季班交換，2026/07/27–08/10 17:00 線上申請，2026/09/11 公告分發暨獎助名單）已辦理完畢；"
                "115-2 學年度選送（赴 116 學年度 / 2027 秋季班交換，可申請 1 學年或 1 學期）於 2026/11/16–11/20 舉辦國際研習週說明會，預計 2026 年 12 月中旬公告簡章並開放申請。"
            ),
            "review_status": "published",
            "published_at": "2026-10-17T05:35:00Z",
            "steps": [
                {
                    "rule_id": f"fcu-115-home-1-{idx+1:03d}",
                    "order": 1,
                    "phase": "校內申請",
                    "title": f"確認逢甲大學 GPA 3.0 門檻、學院限制與 {zh_name} 外語檢定標準",
                    "responsible_party": "學生",
                    "responsible_unit": "逢甲大學國際事務處（行政二館 3 樓 304 室）",
                    "deadline_at": "2026-08-10T17:00:00+08:00",
                    "deadline_status": "verified_exact",
                    "deadline_source_url": "https://oia.fcu.edu.tw/sap/introduction/",
                    "deadline_checked_at": "2026-10-17T05:35:00Z",
                    "deadline_reminder_eligible": False,
                    "summary": f"須為逢甲大學註冊在學學位生（大學部須就讀滿一學期、原則上不得為延修生；研究生首學期即可申請），在校歷年總平均 GPA 達 3.0（含）以上，並符合 {zh_name} 之外語及院系條件。",
                    "details": [
                        f"開放學制與院系：{colleges_str}（{degree_levels_str}）",
                        f"語言與學業條件：{lang_req_str}｜{gpa_req_str}",
                        f"當期名額與費用：{quota_str}",
                    ],
                    "scope": {
                        "home_universities": ["逢甲大學"],
                        "partner_universities": [full_name],
                        "academic_years": ["115", "116"],
                        "application_rounds": [
                            "115-1",
                            "115-2",
                            "第1學期（秋季班）",
                            "第2學期（春季班）",
                        ],
                    },
                    "source_urls": [
                        source_url,
                        "https://oia.fcu.edu.tw/sap/introduction/",
                    ],
                    "checked_at": "2026-10-17T05:35:00Z",
                    "support_status": "verified",
                },
                {
                    "rule_id": f"fcu-115-home-2-{idx+1:03d}",
                    "order": 2,
                    "phase": "校內申請",
                    "title": "於 oiasap 出國研修系統完成線上填報與無紙化申請表件上傳（至多 5 志願）",
                    "responsible_party": "學生",
                    "responsible_unit": "逢甲大學國際事務處（oiasap 線上申請系統）",
                    "deadline_at": "2026-08-10T17:00:00+08:00",
                    "deadline_status": "verified_exact",
                    "deadline_source_url": "https://oiasap.fcu.edu.tw/",
                    "deadline_checked_at": "2026-10-17T05:35:00Z",
                    "deadline_reminder_eligible": False,
                    "summary": "逢甲大學採全線上無紙化申請，學生須於截止日前登入 https://oiasap.fcu.edu.tw/ 選填至多 5 所志願學校，並上傳家長同意書、1,000 字以上研修計畫、生輔組核章獎懲紀錄、歷年成績單及外語檢定證明。",
                    "details": [
                        "應繳文件（全數以電子檔上傳至 oiasap 系統）：1. 出國研修申請資訊簡表、2. 本人 2 吋正面半身脫帽證件照（JPG）、3. 家長同意書（附件一，家長親筆簽名）、4. 研修計畫（附件二，中英文均可，至少 1,000 字）、5. 在校獎懲紀錄（MyFCU 列印並至學務處生輔組［行政二館一樓］蓋印確認章）、6. 研究生指導教授同意書（附件三，研究生必繳）、7. 歷年成績單正本（含最新學期 GPA 與平均成績；國際地區須同時上傳英文歷年成績單）、8. 外語檢定成績證明（國際地區必繳，須為 2024/10/01 後考試取得；大陸地區免附）、9. 清寒弱勢證明（非必繳）。",
                        "重要排他規定：「國際地區」與「大陸地區」僅能擇一報名；「交換學生」與「雙聯學制」亦僅能擇一報名。",
                    ],
                    "document_requirements": [
                        {
                            "name": "逢甲大學出國研修申請資訊簡表、家長同意書（附件一）及研究生指導教授同意書（附件三）",
                            "official_form_url": "https://oiasap.fcu.edu.tw/",
                            "source_urls": [
                                "https://oiasap.fcu.edu.tw/",
                                "https://oia.fcu.edu.tw/sap/introduction/",
                            ],
                        },
                        {
                            "name": "逢甲大學歷年成績單正本（含最新學期 GPA 與平均成績；國際地區須附英文歷年成績單）及生輔組核章之在校獎懲紀錄",
                            "source_urls": [
                                "https://oia.fcu.edu.tw/sap/introduction/"
                            ],
                        },
                        {
                            "name": "出國研修計畫（附件二，中英文不拘，至少 1,000 字，含動機、修課規劃與預期效益）",
                            "source_urls": [
                                "https://oia.fcu.edu.tw/sap/introduction/"
                            ],
                        },
                        {
                            "name": "有效外語能力檢定成績證明（國際地區必繳，須為 2024/10/01 後應試取得；大陸地區免附）",
                            "conditional": country == "中國大陸",
                            "condition": "申請國際及港澳地區必繳；申請大陸地區免附外語檢定",
                            "source_urls": [
                                "https://oiasap.fcu.edu.tw/",
                                "https://oia.fcu.edu.tw/sap/introduction/",
                            ],
                        },
                    ],
                    "scope": {
                        "home_universities": ["逢甲大學"],
                        "academic_years": ["115", "116"],
                        "application_rounds": [
                            "115-1",
                            "115-2",
                            "第1學期（秋季班）",
                            "第2學期（春季班）",
                        ],
                    },
                    "submission": {
                        "method": "online",
                        "office": "逢甲大學國際事務處（行政二館 3 樓 304 室）",
                        "portal_url": "https://oiasap.fcu.edu.tw/",
                    },
                    "action_url": "https://oiasap.fcu.edu.tw/",
                    "source_urls": [
                        "https://oiasap.fcu.edu.tw/",
                        "https://oia.fcu.edu.tw/sap/introduction/",
                    ],
                    "checked_at": "2026-10-17T05:35:00Z",
                    "support_status": "verified",
                },
                {
                    "rule_id": f"fcu-115-home-3-{idx+1:03d}",
                    "order": 3,
                    "phase": "甄選與提名",
                    "title": "校內初審結果暨出國研修獎助學金公告、錄取確認與提名作業",
                    "responsible_party": "學生與逢甲大學國際事務處",
                    "responsible_unit": "逢甲大學國際事務處",
                    "deadline_at": "2026-09-11T17:00:00+08:00",
                    "deadline_status": "verified_exact",
                    "deadline_source_url": "https://oia.fcu.edu.tw/news/115-1%e5%ad%b8%e5%b9%b4%e5%ba%a6%e9%81%b8%e9%80%81%e5%ad%b8%e7%94%9f%e5%87%ba%e5%9c%8b%e7%a0%94%e4%bf%ae%e5%88%9d%e5%af%a9%e9%8c%84%e5%8f%96%e6%9a%a8%e7%8d%8e%e5%8a%a9%e5%ad%b8%e9%87%91%e7%8d%b2/",
                    "deadline_checked_at": "2026-10-17T05:35:00Z",
                    "deadline_reminder_eligible": False,
                    "summary": "國際事務處公告校內初審錄取分發暨「逢甲大學出國研修獎助學金」獲獎名單；取得推薦資格後由國際處承辦人向姊妹校辦理官方提名（Nomination），欲放棄者須填具《錄取資格放棄聲明書》。",
                    "details": [
                        "逢甲出國研修獎助於線上報名後自動納入審核；實際名額與金額依當年預算、申請人數及審查核定，不是按排名保證固定金額。經濟弱勢或家庭突遭變故者可提出證明供審查。",
                        "若獲推薦後因故放棄錄取資格，須依規定提交《錄取資格放棄聲明書》；無故放棄將影響日後申請校內出國研修及獎助學金之權益。",
                    ],
                    "scope": {
                        "home_universities": ["逢甲大學"],
                        "academic_years": ["115", "116"],
                        "application_rounds": [
                            "115-1",
                            "115-2",
                            "第1學期（秋季班）",
                            "第2學期（春季班）",
                        ],
                    },
                    "source_urls": [
                        "https://oia.fcu.edu.tw/sap/introduction/",
                        "https://oia.fcu.edu.tw/sap/scholarship/",
                    ],
                    "checked_at": "2026-10-17T05:35:00Z",
                    "support_status": "verified",
                },
                {
                    "rule_id": f"fcu-{idx+1:03d}-host-apply",
                    "order": 4,
                    "phase": "合作校申請",
                    "title": f"依國際事務處通知辦理 {zh_name} 研修學校複審申請與宿舍登記",
                    "responsible_party": "學生與接待校國際處",
                    "summary": f"取得逢甲大學校內初審推薦資格後，依國際事務處承辦人通知完成 {zh_name} 第二階段複審線上申請，上傳護照影本、英文財力證明、英文成績單、語檢證明及選課清單，最終入學許可由姊妹校審核決定。",
                    "details": [
                        f"研修期程：{study_period_str}｜名額：{quota_str}",
                        f"語言與學業條件：{lang_req_str}",
                    ]
                    + ([f"姊妹校申請備註：{comment_str}"] if comment_str else []),
                    "scope": {
                        "home_universities": ["逢甲大學"],
                        "partner_universities": [full_name],
                        "academic_years": ["115", "116"],
                        "application_rounds": [
                            "115-1",
                            "115-2",
                            "第1學期（秋季班）",
                            "第2學期（春季班）",
                        ],
                    },
                    "source_urls": (
                        [source_url]
                        + ([factsheet_url] if factsheet_url else [])
                        + ([website] if website else [])
                    ),
                    "checked_at": "2026-10-17T05:35:00Z",
                    "support_status": "verified",
                    "needs_confirmation": False,
                },
                {
                    "rule_id": f"fcu-115-home-5-{idx+1:03d}",
                    "order": 5,
                    "phase": "行前準備",
                    "title": "取得入學許可 2 週內繳交保證金（NT$10,000／5,000）、選課達最低學分、志工服務與返國抵免",
                    "responsible_party": "學生",
                    "responsible_unit": "逢甲大學國際事務處／教務處註冊課務組／各系所",
                    "summary": "收到姊妹校正式入學許可（LOA）後 2 週內繳交保證金（學費互免或獲獎生 NT$10,000、自費生 NT$5,000），參加行前說明會、辦理簽證與海外保險；研修期間修足最低學分（大一至大三 12 學分、大四 9 學分、碩博 3 學分），返國後 1 個月內繳交 2,000 字報告書並完成志工時數與學分抵免。",
                    "details": tuition_points_list,
                    "scope": {
                        "home_universities": ["逢甲大學"],
                        "academic_years": ["115", "116"],
                        "application_rounds": [
                            "115-1",
                            "115-2",
                            "第1學期（秋季班）",
                            "第2學期（春季班）",
                        ],
                    },
                    "source_urls": [
                        "https://oia.fcu.edu.tw/sap/introduction/",
                        "https://oia.fcu.edu.tw/sap/scholarship/",
                    ],
                    "checked_at": "2026-10-17T05:35:00Z",
                    "support_status": "verified",
                },
            ],
            "sources": wf_sources,
            "last_checked": "2026-10-17T05:35:00Z",
            "coverage_status": "official_verified",
            "coverage_note": "已完整整合逢甲大學 115-1 學年度選送學生出國研修簡章（校級合作）、oiasap 出國研修學校查詢系統 API、115-1 初審分發暨獎助名單與國際事務處獎助學金規範。",
        })

        review_home_workflow_scope(workflows[-1])

        cost_default, visa_default = REGION_COST_DEFAULTS.get(
            country,
            (
                "USD 800–1,300 / 月（含住宿、膳食、教材與當地交通費用）",
                "須依接待校與駐臺代表處規定辦理學生簽證與海外醫療保險。",
            ),
        )
        cost_line = f"預估每月生活費約 {cost_default}"
        tuition_clean = tuition_points_list[0]
        housing_clean = housing_str
        course_clean = course_rest_str
        calendar_clean = f"{sem_dates_str}。"

        dest_sources = [
            {
                "title": f"逢甲大學出國研修學校查詢系統（oiasap）—{zh_name}",
                "source_url": source_url,
                "summary": "逢甲大學官方交換名額、語檢門檻、開放學院與學費減免規定",
            },
            {
                "title": "逢甲大學 115-1 學年度選送學生出國研修簡章（校級合作）",
                "source_url": "https://oia.fcu.edu.tw/sap/introduction/",
                "summary": "逢甲大學交換生 GPA 3.0 門檻、最低修課學分（大一至大三12學分／大四9學分／碩博3學分）、保證金（NT$10,000／5,000）與志工時數規定",
            },
        ]
        if factsheet_url:
            dest_sources.append({
                "title": f"{zh_name} 課程目錄／交換生 Fact Sheet",
                "source_url": factsheet_url,
                "summary": "姊妹校課程資訊與交換生申請指引",
            })
        if website:
            dest_sources.append({
                "title": f"{full_name} 官方網站",
                "source_url": website,
                "summary": "接待合作校官方網站",
            })
        if sharepoint_exp_url:
            dest_sources.append({
                "title": f"逢甲大學赴 {zh_name} 研修心得作品專區（o365 SharePoint）",
                "source_url": sharepoint_exp_url,
                "summary": "逢甲大學國際事務處收錄之歷年學長姐返國研修心得報告",
            })
        if adm_rec:
            dest_sources.append({
                "title": f"逢甲大學 115-1 學年度選送學生出國研修分發暨獎助學金名單（{zh_name}）",
                "source_url": adm_rec["pdf_url"],
                "summary": f"115-1 錄取分發 {adm_rec['count']} 名（{'、'.join(adm_rec['depts'])}）",
            })

        src_url_list = (
            [source_url]
            + ([factsheet_url] if factsheet_url else [])
            + ([website] if website else [])
        )

        destinations.append({
            "home_university": "逢甲大學",
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
                    "title": "生活費、保證金（NT$10,000／5,000）與學雜費規定",
                    "summary": cost_line,
                    "points": [cost_line] + tuition_points_list,
                    "source_urls": src_url_list,
                    "caution": "可申請逢甲大學「出國研修獎助學金」（報名後自動納入審核；金額與名額依當年預算及審查核定）、教育部「學海飛颺」（每人至少 NT$60,000）／「學海惜珠」（依教育部核定，須另案申請）、「張保隆校長紀念獎助學金」（上限 NT$200,000）及「新生鷹揚獎助學金」（往返機票上限國際 NT$40,000／大陸 NT$20,000）。",
                },
                {
                    "key": "housing",
                    "title": "住宿資訊與申請",
                    "summary": housing_clean[:160],
                    "points": [housing_clean],
                    "source_urls": src_url_list,
                    "caution": "校內宿位有限，請於完成姊妹校複審申請時同步確認宿舍申請期限。",
                },
                {
                    "key": "insurance",
                    "title": "醫療保險與安全",
                    "summary": visa_default,
                    "points": [
                        visa_default,
                        "交換生於出國研修期間須投保涵蓋全期之海外醫療及意外保險，並依規定參加國際事務處舉辦之行前說明會。",
                    ],
                    "source_urls": src_url_list,
                    "caution": "部分姊妹校要求於開學報到前提交指定規格之醫療及意外保險證明後方可辦理註冊。",
                },
                {
                    "key": "visa",
                    "title": "簽證、體檢與役男出境準備",
                    "summary": visa_default,
                    "points": [
                        "收到姊妹校正式入學許可書（Letter of Acceptance / COE / DS-2019）後，立即向駐臺辦事處申辦學生簽證（赴大陸交換須持有效臺胞證並完成規定健康檢查）。",
                        "尚未履行兵役義務之在學役男，須於出國前檢附入學許可向國際事務處及學務處生輔組辦理役男出境緩徵手續。",
                        visa_default,
                    ],
                    "source_urls": src_url_list,
                    "caution": "簽證核發時間視各國領事館而定（約 4–8 週），請勿於取得簽證前購買不可退改之機票。",
                },
                {
                    "key": "courses",
                    "title": "課程限制、最低學分（大一至大三12／大四9／碩博3學分）與返國抵免",
                    "summary": course_clean[:160],
                    "points": [
                        course_clean,
                        "返國後修課及格率須達 1/2 以上，並檢具姊妹校正式成績單及課程大綱依逢甲大學學生抵免學分辦法辦理學分抵免。",
                    ],
                    "source_urls": src_url_list
                    + ["https://oia.fcu.edu.tw/sap/introduction/"],
                    "caution": "獲教育部學海飛颺／惜珠獎學金者，出國期間必須修讀至少 4 學分與本科系相關之必選修專業課程。",
                },
                {
                    "key": "city",
                    "title": "城市與校區位置",
                    "summary": (
                        f"{country} {location_obj.get('city') or ''}".strip()
                    ),
                    "points": [
                        location_obj.get("note")
                        or f"{full_name} 校級代表位置位於 {location_obj.get('city') or country}。",
                    ],
                    "source_urls": [
                        location_obj.get("source_url") or source_url
                    ],
                    "caution": "部分合作校具有多個校區，實際授課校區請以 oiasap 系統備註與姊妹校錄取通知為準。",
                },
                {
                    "key": "arrival",
                    "title": "學期年曆、志工時數（50小時/學期）與返國報告義務",
                    "summary": calendar_clean,
                    "points": [
                        calendar_clean,
                        "返國後 1 個月內須上傳至少 2,000 字之出國研習報告書，且學費互免／獲獎助學生須完成每學期 50 小時（一學年 100 小時）校園或國際處志工服務，始得辦理保證金無息退還。",
                    ]
                    + (
                        [
                            f"歷年學長姐返國心得：逢甲大學國際事務處 SharePoint 已建置赴 {zh_name} 研修心得作品資料夾。"
                        ]
                        if sharepoint_exp_url
                        else []
                    ),
                    "source_urls": src_url_list
                    + ([sharepoint_exp_url] if sharepoint_exp_url else []),
                    "caution": "保證金退還須同時滿足「修課及格率達 1/2 以上」、「返國 1 個月內繳交 2,000 字研習報告書」及「完成志工服務時數」三項條件。",
                },
            ],
            "first_72_hours": [
                {
                    "title": "依姊妹校入學許可指定報到日辦理新生註冊、宿舍入住與選課確認",
                    "detail": calendar_clean,
                    "source_urls": [source_url],
                },
                {
                    "title": "完成當地居留登錄、醫療保險確認與向逢甲大學國際事務處回報抵達資訊",
                    "detail": f"{visa_default} 抵校後請向逢甲大學國際事務處承辦人回報平安及確認最終選課學分數符合校內最低門檻。",
                    "source_urls": [source_url],
                },
            ],
            "sources": dest_sources,
            "last_checked": "2026-10-17T05:35:00Z",
            "coverage_status": "official_verified",
            "coverage_note": "已整合逢甲大學 115-1 學年度選送學生出國研修簡章、oiasap 出國研修學校查詢系統 API、115-1 初審分發暨獎助名單與歷年學長姐心得專區。",
        })

        research_records.append({
            "home_university": "逢甲大學",
            "school_name": full_name,
            "country": country,
            "official_website": website,
            "verification_status": "official_verified",
            "discovery_source_url": source_url,
            "checked_at": "2026-10-17T05:35:00Z",
            "note": f"逢甲大學國際事務處 oiasap 系統與合作學校列表（{source_url}）及 ROR/Wikidata 官方網址核對完成。",
        })

        ev_sources = [
            {"title": f"逢甲大學 oiasap 出國研修系統—{zh_name}", "url": source_url},
        ]
        if factsheet_url:
            ev_sources.append(
                {"title": f"{zh_name} 課程目錄／Fact Sheet", "url": factsheet_url}
            )
        if website:
            ev_sources.append({"title": f"{full_name} 官方網站", "url": website})
        if sharepoint_exp_url:
            ev_sources.append({
                "title": f"逢甲大學赴 {zh_name} 研修心得作品專區",
                "url": sharepoint_exp_url,
            })
        if adm_rec:
            ev_sources.append({
                "title": f"逢甲大學 115-1 出國研修分發暨獎助學金名單（{zh_name}）",
                "url": adm_rec["pdf_url"],
            })

        has_student_exp = bool(sharepoint_exp_url or adm_rec or story_rec)
        if has_student_exp:
            exp_covered_schools += 1

        ev_list = [
            {
                "theme": "housing",
                "kind": "official",
                "text": housing_clean,
                "sources": ev_sources,
                "checked_at": "2026-10-17T05:35:00Z",
                "scope": "逢甲大學出國研修住宿資訊與姊妹校 Fact Sheet",
                "original_excerpt": False,
                "original_text": "",
                "translation_status": "original",
            },
            {
                "theme": "cost",
                "kind": "official",
                "text": f"{tuition_clean}｜{cost_line}",
                "sources": ev_sources,
                "checked_at": "2026-10-17T05:35:00Z",
                "scope": "逢甲大學出國研修費用規定、保證金與地區生活費估算",
                "original_excerpt": False,
                "original_text": "",
                "translation_status": "original",
            },
            {
                "theme": "academics",
                "kind": "official",
                "text": course_clean,
                "sources": ev_sources,
                "checked_at": "2026-10-17T05:35:00Z",
                "scope": "逢甲大學選送學生出國研修簡章最低修課學分與姊妹校選課限制",
                "original_excerpt": False,
                "original_text": "",
                "translation_status": "original",
            },
            {
                "theme": "safety",
                "kind": "official",
                "text": visa_default,
                "sources": ev_sources,
                "checked_at": "2026-10-17T05:35:00Z",
                "scope": "逢甲大學出國研修簽證、體檢、海外醫療保險與役男出境提醒",
                "original_excerpt": False,
                "original_text": "",
                "translation_status": "original",
            },
            {
                "theme": "campus_culture",
                "kind": "mixed" if has_student_exp else "official",
                "text": (
                    f"合作類別：{program_type}｜名額：{quota_str}｜申請要求：{lang_req_str}"
                    + (
                        f"｜115-1 初審錄取分發 {adm_rec['count']} 名（{'、'.join(adm_rec['depts'])}）"
                        if adm_rec
                        else ""
                    )
                    + (
                        f"｜逢甲大學國際事務處收錄赴 {zh_name} 學長姐研修心得作品專區。"
                        if sharepoint_exp_url
                        else ""
                    )
                ),
                "sources": ev_sources,
                "checked_at": "2026-10-17T05:35:00Z",
                "scope": "逢甲大學出國研修計畫名額、115-1 錄取實績與歷年學長姐研修心得",
                "original_excerpt": False,
                "original_text": "",
                "translation_status": "original",
            },
        ]
        life_records.append({
            "school_name": full_name,
            "country": country,
            "checked_at": "2026-10-17T05:35:00Z",
            "status": "ready",
            "evidence": ev_list,
            "notes": [
                "已整合逢甲大學 115-1 學年度選送學生出國研修簡章、oiasap 出國研修學校查詢系統、115-1 初審分發暨獎助名單與歷年研修心得連結。",
                "當期宿位供給、費用與選課限制請依姊妹校最新 Fact Sheet 及課程目錄核對。",
            ],
            "location_signature": f"verified:{location_obj['latitude']}:{location_obj['longitude']}:representative",
            "extraction_version": 3,
        })

        sample_reports: list[dict] = []
        if story_rec:
            sample_reports.append({
                "title": story_rec["title"],
                "url": story_rec["url"],
                "term": "歷年交換心得精選",
            })
            theme_map = {
                "academics": f"{story_rec['author']}分享於 {zh_name} 交換期間之修課規劃、語言準備與跨文化學習收穫。",
                "housing": f"{story_rec['author']}分享於 {zh_name} 交換期間之當地住宿與異地獨立生活調適經驗。",
                "campus_culture": story_rec["quote"],
                "cost": f"{story_rec['author']}分享赴 {zh_name} 交換之行前準備、資料蒐集與學期生活體驗。",
            }
            student_experience_rows.append({
                "school_name": full_name,
                "country": country,
                "title": story_rec["title"],
                "source_url": story_rec["url"],
                "source_type": "article",
                "platform": "逢甲大學國際事務處「學長姐真心話」專區",
                "author_name": story_rec["author"],
                "language": "zh",
                "summary": story_rec["quote"],
                "themes": ["academics", "housing", "campus_culture", "cost"],
                "theme_summaries": theme_map,
                "content_status": "full_text",
                "perspective": "official_student_story",
                "published_at": None,
                "discovered_at": "2026-10-17T05:35:00Z",
                "content_hash": hashlib.sha256(
                    f"{full_name}:story:{story_rec['author']}".encode("utf-8")
                ).hexdigest(),
                "exchange_term": "歷年交換心得精選",
                "summary_zh": story_rec["quote"],
                "original_summary": story_rec["quote"],
                "theme_summaries_zh": theme_map,
                "translation_status": "original",
                "source_kind": "official_experience_page",
            })

        if sharepoint_exp_url:
            sp_title = f"逢甲大學赴{country}—{zh_name} 出國研修學生心得作品集（國際事務處 o365 專區）"
            sample_reports.append({
                "title": sp_title,
                "url": sharepoint_exp_url,
                "term": "111–114學年度",
            })
            summary_text = (
                f"逢甲大學國際事務處 oiasap 出國研修系統收錄之赴 {zh_name} 歷年交換學生返國研習報告書資料夾（逢甲大學教職員生可以 o365 帳號登入查閱完整 2,000 字以上心得報告）。"
            )
            theme_map = {
                "academics": f"逢甲大學交換生分享於 {zh_name} 之選課經驗、學分抵免（大學部每學期至少 12 學分／大四 9 學分／碩博 3 學分）與課業學習心得。",
                "housing": f"逢甲大學交換生分享於 {zh_name} 之校內宿舍或校外合作公寓申請流程、住宿環境與生活機能。",
                "campus_culture": f"逢甲大學交換生分享於 {zh_name} 之迎新活動、國際學伴制度、校園社團與在地文化體驗。",
                "cost": f"逢甲大學交換生分享於 {zh_name} 之每月生活費開銷、逢甲出國研修獎助學金／教育部學海獎學金運用與行前簽證準備。",
            }
            student_experience_rows.append({
                "school_name": full_name,
                "country": country,
                "title": sp_title,
                "source_url": sharepoint_exp_url,
                "source_type": "article",
                "platform": "逢甲大學國際事務處 oiasap 出國研修心得資料庫（o365 SharePoint）",
                "author_name": "逢甲大學歷年返國交換生",
                "language": "zh",
                "summary": summary_text,
                "themes": ["academics", "housing", "campus_culture", "cost"],
                "theme_summaries": theme_map,
                "content_status": "metadata_only",
                "perspective": "official_student_story",
                "published_at": None,
                "discovered_at": "2026-10-17T05:35:00Z",
                "content_hash": hashlib.sha256(
                    sharepoint_exp_url.encode("utf-8")
                ).hexdigest(),
                "exchange_term": "111–114學年度",
                "summary_zh": summary_text,
                "original_summary": "",
                "theme_summaries_zh": theme_map,
                "translation_status": "original",
                "source_kind": "official_experience_portal",
            })

        if adm_rec:
            adm_title = f"逢甲大學 115-1 學年度選送學生赴 {zh_name} 出國研修分發暨獎助學金核定紀錄（共 {adm_rec['count']} 名）"
            sample_reports.append({
                "title": adm_title,
                "url": adm_rec["pdf_url"],
                "term": "115-2學年度（2027春季班）",
            })
            sch_text = (
                f"；其中獲核定 {'、'.join(adm_rec['scholarships'])}"
                if adm_rec["scholarships"]
                else ""
            )
            summary_text = (
                f"逢甲大學 115-1 學年度初審分發共錄取 {adm_rec['count']} 名學生於 115-2 學期赴 {zh_name} 進行「{adm_rec['type']}」，"
                f"錄取院系包含：{'、'.join(adm_rec['depts'])}{sch_text}。"
            )
            theme_map = {
                "academics": f"115-1 錄取院系分布：{'、'.join(adm_rec['depts'])}（研修類型：{adm_rec['type']}，推薦研修期程：115-2 學年度）。",
                "cost": (
                    f"115-1 初審獎助核定：{'、'.join(adm_rec['scholarships'])}。"
                    if adm_rec["scholarships"]
                    else f"115-1 初審錄取類型為「{adm_rec['type']}」，可依規定領取校內或學海系列獎助學金。"
                ),
                "campus_culture": f"逢甲大學 115-1 學年度共選送 {adm_rec['count']} 名學子赴 {zh_name} 研修交流。",
            }
            student_experience_rows.append({
                "school_name": full_name,
                "country": country,
                "title": adm_title,
                "source_url": adm_rec["pdf_url"],
                "source_type": "article",
                "platform": "逢甲大學國際事務處 115-1 初審分發暨獎助學金名單",
                "author_name": "逢甲大學 115-1 錄取研修學生",
                "language": "zh",
                "summary": summary_text,
                "themes": ["academics", "cost", "campus_culture"],
                "theme_summaries": theme_map,
                "content_status": "full_text",
                "perspective": "official_program_record",
                "published_at": "2026-09-11T00:00:00Z",
                "discovered_at": "2026-10-17T05:35:00Z",
                "content_hash": hashlib.sha256(
                    f"{full_name}:115-1-admitted".encode("utf-8")
                ).hexdigest(),
                "exchange_term": "115-2（2027春季班）",
                "summary_zh": summary_text,
                "original_summary": summary_text,
                "theme_summaries_zh": theme_map,
                "translation_status": "original",
                "source_kind": "official_experience_pdf",
            })

        portal_default = (
            sharepoint_exp_url
            or (
                "https://fengchia.sharepoint.com/sites/dept_IA/Shared%20Documents/%E5%9C%8B%E9%9A%9B%E8%99%95%E7%B6%B2%E9%A0%81%E8%B3%87%E6%96%99/%E5%87%BA%E5%9C%8B%E7%A0%94%E7%BF%92/1.%E5%87%BA%E5%9C%8B%E7%A0%94%E4%BF%AE/%E5%8F%83%E8%80%83%E8%B3%87%E8%A8%8A/%E8%B5%B4%E5%A4%A7%E9%99%B8%E5%9C%B0%E5%8D%80%E7%A0%94%E4%BF%AE%E5%BF%83%E5%BE%97%E4%BD%9C%E5%93%81"
                if country == "中國大陸"
                else "https://fengchia.sharepoint.com/sites/dept_IA/Shared%20Documents/%E5%9C%8B%E9%9A%9B%E8%99%95%E7%B6%B2%E9%A0%81%E8%B3%87%E6%96%99/%E5%87%BA%E5%9C%8B%E7%A0%94%E7%BF%92/1.%E5%87%BA%E5%9C%8B%E7%A0%94%E4%BF%AE/%E5%8F%83%E8%80%83%E8%B3%87%E8%A8%8A/%E8%B5%B4%E5%9C%8B%E9%9A%9B%E5%9C%B0%E5%8D%80%E7%A0%94%E4%BF%AE%E5%BF%83%E5%BE%97%E4%BD%9C%E5%93%81"
            )
        )
        experience_sources_records.append({
            "home_university": "逢甲大學",
            "school_name": full_name,
            "country": country,
            "official_experience_portal_url": portal_default,
            "partner_page_url": source_url,
            "report_count": len(sample_reports),
            "sample_reports": sample_reports,
            "checked_at": "2026-10-17T05:35:00Z",
        })

    partners_jsonl_text = (
        "\n".join(json.dumps(r, ensure_ascii=False) for r in partners) + "\n"
    )
    reviewed_programs = load_reviewed_programs(REPO_ROOT)
    for partner in partners:
        apply_program_review(partner, reviewed_programs)

    (OFFICIAL_FCU_DIR / "partners.jsonl").write_text(
        partners_jsonl_text, encoding="utf-8"
    )
    (SOURCES_FCU_DIR / "partners.jsonl").write_text(
        partners_jsonl_text, encoding="utf-8"
    )
    (OFFICIAL_FCU_DIR / "application_workflows.jsonl").write_text(
        "\n".join(json.dumps(r, ensure_ascii=False) for r in workflows) + "\n",
        encoding="utf-8",
    )
    (OFFICIAL_FCU_DIR / "destination_profiles.jsonl").write_text(
        "\n".join(json.dumps(r, ensure_ascii=False) for r in destinations)
        + "\n",
        encoding="utf-8",
    )
    (OFFICIAL_FCU_DIR / "partner_research.jsonl").write_text(
        "\n".join(json.dumps(r, ensure_ascii=False) for r in research_records)
        + "\n",
        encoding="utf-8",
    )
    (OFFICIAL_FCU_DIR / "student_life.jsonl").write_text(
        "\n".join(json.dumps(r, ensure_ascii=False) for r in life_records)
        + "\n",
        encoding="utf-8",
    )
    (OFFICIAL_FCU_DIR / "experience_sources.jsonl").write_text(
        "\n".join(
            json.dumps(r, ensure_ascii=False)
            for r in experience_sources_records
        )
        + "\n",
        encoding="utf-8",
    )
    (OFFICIAL_FCU_DIR / "student_experiences.jsonl").write_text(
        "\n".join(
            json.dumps(r, ensure_ascii=False) for r in student_experience_rows
        )
        + "\n",
        encoding="utf-8",
    )
    (OFFICIAL_FCU_DIR / "campus-locations.json").write_text(
        json.dumps({"locations": new_locations}, ensure_ascii=False, indent=2)
        + "\n",
        encoding="utf-8",
    )

    # IMPORTANT: Only add the home university row ("逢甲大學", "臺灣") to university_locations.jsonl!
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

    fcu_home_loc = {
        "school_name": "逢甲大學",
        "country": "臺灣",
        "city": "臺中市西屯區",
        "latitude": 24.1788,
        "longitude": 120.6467,
        "geocode_status": "verified",
        "geocoded_at": "2026-10-17T05:35:00Z",
        "source_url": "https://www.wikidata.org/wiki/Q706884",
        "identity_source_url": "https://ror.org/05vhczg54",
        "precision": "representative",
        "note": "校級代表位置：官方網域及國家已與 ROR 比對，座標來源為 Wikidata P625；實際交換校區以錄取通知為準。 母校代表點採臺中市西屯區文華路100號校本部（行政二館 3 樓 304 室國際事務處）；官方地址來源：https://oia.fcu.edu.tw/。",
    }
    existing_loc_map[("逢甲大學", "臺灣")] = fcu_home_loc
    sorted_locs = sorted(
        existing_loc_map.values(),
        key=lambda r: (r.get("country") or "", r.get("school_name") or ""),
    )
    loc_file.write_text(
        "\n".join(json.dumps(r, ensure_ascii=False) for r in sorted_locs) + "\n",
        encoding="utf-8",
    )

    fcu_source_urls = [
        "https://oiasap.fcu.edu.tw/",
        "https://oia.fcu.edu.tw/sap/",
        "https://oia.fcu.edu.tw/sap/introduction/",
        "https://oia.fcu.edu.tw/sap/scholarship/",
        "https://oia.fcu.edu.tw/sap/dualdegree/",
        "https://oia.fcu.edu.tw/collaboration/",
        "https://service825.fcu.edu.tw/infofiles/F_dvdjo5xweac25492665.pdf",
        "https://service825.fcu.edu.tw/infofiles/F_lwv4fzkckfwf676fc73.pdf",
        "https://service825.fcu.edu.tw/infofiles/F_hv0vi21ylfgacfc4e6c.pdf",
    ]

    exchange_info_payload = {
        "school_name": "逢甲大學",
        "program_type": [
            "交換學生（國際地區校級合作・學費互免／部分減免／自費研修）",
            "交換學生（大陸及港澳地區校級合作・985/211 重點高校學費互免）",
            "雙聯學制（校級與院系級 3+1 雙學士、1+1 雙碩士、3+2 學碩士）",
        ],
        "academic_year": [
            "115（115-1 選送赴 2027 春季班：2026/07/27–08/10 17:00 線上申請，2026/09/11 公告分發暨獎助名單）",
            "115（115-2 選送赴 2027 秋季班／116 學年度：2026/11/16–11/20 國際研習週說明會，2026/12 中旬開放申請）",
        ],
        "semester": [
            "第1學期（秋季班：每年約 8/9 月至翌年 1 月；12 月甄選可申請 1 學年或 1 學期）",
            "第2學期（春季班：每年約 2 月至 6/7 月，日本為 4 月至 8 月；6 月甄選申請 1 學期）",
        ],
        "application_period": [
            "115-1 學年度選送學生出國研修（赴 115-2 / 2027 春季班出國交換 1 學期）：2026年6月29日公告簡章，2026年7月27日（一）至8月10日（一）17:00 止於 oiasap 系統（https://oiasap.fcu.edu.tw/）受理全線上申請，並於 2026年9月11日公告初審分發暨獎助學金獲獎名單（國際地區錄取 46 人、大陸地區錄取 25 人）。",
            "115-1 國際研習週暨 115-2 學年度選送學生出國研修（赴 116 學年度 / 2027 秋季班出國交換 1 學年或 1 學期）：國際研習週系列說明會於 2026年11月16日至11月20日假行政二館 205 視聽教室舉辦；115-2 選送簡章預計於 2026年12月中旬公告，申請期程約 1 至 1.5 個月。",
        ],
        "eligibility": [
            "在學學籍與年級限制：提出申請及出國研修期間應為逢甲大學註冊在學學生（原則上不得為延修生；大學部復學或入學未滿 1 學期者不得申請，碩博士班研究生入學首學期即可申請）。同一學制出國交換累計不得超過 2 個學期（雙聯學制不在此限）。",
            "學業成績門檻：在校歷年總平均 GPA 3.0（含）以上（不可用固定百分制分數替代）；若申請「交換一學年（學費互免）」者，歷年在校學業成績系排名須達前 50%，且須符合畢業學分修畢或實驗室合作規定。",
            "志願填報與排他規定：每位申請人於 oiasap 系統至多可選填 5 所志願學校；「國際地區」與「大陸地區」僅能擇一報名，「交換學生」與「雙聯學制」亦僅能擇一報名。",
            "保證金、最低修課學分與返國義務：取得姊妹校入學許可後 2 週內須繳交保證金（獲獎助學金或學費互免生 NT$10,000、自費生 NT$5,000）。出國期間每學期最低修課學分為學士班非應屆畢業學生 12 學分、學士班應屆畢業學生 9 學分、碩博士班 3 學分（特殊情況經系／學程主任核可並報教務處備查者例外）（學海受獎生須修習至少 4 學分本科系專業課程）；返國後修課及格率達 1/2 以上、1 個月內繳交 2,000 字以上研習報告書，且學費互免／獲獎生完成每學期 50 小時志工服務（兩學期 100 小時）後全額無息退還保證金。",
        ],
        "language_requirement": [
            "申請赴國際及香港地區姊妹校者，須於校內初審時上傳 2024年10月1日（含）後應試取得之有效外語能力檢定證明（TOEFL iBT、IELTS Academic、TOEIC、JLPT、TOPIK 或歐語 CEFR 檢定），且須符合各志願學校於 oiasap 系統所列之單項與總分標準。",
            "歐美及澳洲英語授課交換計畫常見門檻為 TOEFL iBT 61–85 或 IELTS 5.5–6.5（部分日本、韓國、法國、德國、泰國、波蘭、捷克姊妹校亦接受 TOEIC 550–800 或 CEFR B1/B2）。",
            "申請赴大陸地區姊妹校交換者免附外語能力檢定證明，惟在校歷年總平均須達 GPA 3.0（含）以上。",
        ],
        "required_documents": [
            "1. 出國研修申請資訊簡表（於 https://oiasap.fcu.edu.tw/ 線上填報生成，至多選填 5 所志願學校）",
            "2. 本人 2 吋正面半身脫帽證件照電子檔（JPG 格式）",
            "3. 家長同意書（簡章附件一，須由家長親筆簽名後掃描上傳）",
            "4. 研修計畫（簡章附件二，中英文撰寫均可，字數至少 1,000 字）",
            "5. 在校獎懲紀錄（自 MyFCU 列印後，須攜至學務處生活輔導組［行政二館一樓］加蓋確認章後掃描上傳）",
            "6. 研究生指導教授同意書（簡章附件三，僅碩博士班研究生須繳交，須經指導教授親筆簽名）",
            "7. 歷年成績單正本（須含最新學期 GPA 與歷年總平均；申請國際地區者須同時上傳中文及英文歷年成績單，英文姓名須與護照一致）",
            "8. 外語檢定成績證明（申請國際地區必繳，須為 2024/10/01 後考試取得；申請大陸地區免附）及清寒弱勢證明（非必繳，具資格者可獲額外獎助）",
        ],
        "scholarship_info": [
            "逢甲出國研修獎助於線上報名後自動納入審核；實際名額與金額依當年預算、申請人數及審查核定，不是按排名保證固定金額。經濟弱勢或家庭突遭變故者可提出證明供審查。",
            "教育部「學海飛颺」與「學海惜珠」獎學金：補助具中華民國國籍且赴國際地區（不含大陸及港澳）修讀學分滿 1 學期或 1 學年之在學學生；學海飛颺要求大學部班排前 30% 或研究生總平均 80 分以上（每人獎助至少 NT$60,000 起），學海惜珠補助具各縣市低收／中低收／特殊境遇家庭等資格學生，且均須於國外修讀至少 4 學分本科系相關專業課程。",
            "逢甲大學「張保隆校長紀念獎助學金」：補助具中華民國國籍、大學部班排前 35% 或研究生總平均 80 分以上（清寒優先）赴國外簽約大學研修之學生，經面審核定每人上限新臺幣 200,000 元。",
            "逢甲大學「新生鷹揚獎助學金」與「陳立恆先生赴歐美攻讀博士學位獎學金」：新生鷹揚獎助學金提供在學期間乙次赴學費互免姐妹校交換往返經濟艙機票實報實核（國際地區上限 NT$40,000、大陸地區上限 NT$20,000）；陳立恆先生獎學金補助赴歐美攻讀博士學位每年 NT$500,000。",
        ],
        "partner_universities": [p["school_name"] for p in partners],
        "source_urls": fcu_source_urls,
        "last_checked": "2026-10-17T05:35:00Z",
    }
    (OFFICIAL_FCU_DIR / "exchange_info.json").write_text(
        json.dumps(exchange_info_payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    student_dashboard_payload = {
        "school_name": "逢甲大學",
        "last_checked": "2026-10-17T05:35:00Z",
        "academic_score_minimum": None,
        "academic_score_rule": "在校歷年總平均 GPA 3.0（含）以上（不可用固定百分制分數替代）；申請一學年學費互免交換者歷年系排名須達前 50%。大學部須入學滿一學期以上且原則上不得為延修生，研究生首學期即可申請；出國期間每學期至少須修習大一至大三 12 學分、大四 9 學分、碩博班 3 學分。",
        "academic_gpa_minimum": 3.0,
        "maximum_preferences": 5,
        "selection_rules": {
            "academic_policy": "gpa_or_rank",
            "academic_reference_year": "115",
            "undergraduate_gpa_minimum": 3.0,
            "undergraduate_rank_maximum": None,
            "graduate_academic_exempt": False,
            "exclude_in_service": False,
            "pending_quota_planning": False,
            "partner_requirements_need_confirmation": True,
            "degree_score_minimums": {},
            "excluded_undergraduate_years": [],
            "language_certificate_required": False,
        },
        "language_score_minimums": {},
        "application_periods": [{'title': '逢甲大學 115-1 學年度選送學生出國研修（赴 115-2 / 2027 春季班校級交換與雙聯）',
          'details': ['線上申請期間：2026年7月27日（一）起至2026年8月10日（一）下午 17:00 止（於 https://oiasap.fcu.edu.tw/ 採全線上無紙化上傳，至多選填 5 '
                      '所志願學校）。',
                      '初審分發暨獎助學金公告：2026年9月11日已公告初審錄取名單（國際地區 28 校 46 人、大陸地區 9 校 25 人，合計 71 人獲推薦分發及出國研修獎助學金）。',
                      '每年 6 月中旬公告之簡章僅開放申請交換 1 學期（春季班）；欲申請交換 1 學年或秋季班者請參加每年 12 月中旬公告之甄選梯次。'],
          'source': {'title': '逢甲大學 115-1 學年度選送學生出國研修簡章（校級合作）與初審錄取公告',
                     'source_url': 'https://oia.fcu.edu.tw/sap/introduction/',
                     'category': 'deadline',
                     'summary': '115-1 選送學生出國研修線上報名時程、應繳文件與分發結果。'},
          'scope': 'home_application',
          'program_types': ['exchange'],
          'academic_year': '115',
          'application_round': '115-1 選送（2027春季班）',
          'audience': 'all_students',
          'opens_at': None,
          'deadline_at': '2026-08-10T17:00:00+08:00',
          'date_status': 'verified_exact',
          'status': 'closed',
          'status_note': '115-1 選送（2027春季班出國）已於 2026/08/10 17:00 截止並於 2026/09/11 公告 71 名錄取分發暨獎助名單，現正進行姊妹校複審送件。',
          'deadline_note': '透過逢甲大學出國研修申請系統（https://oiasap.fcu.edu.tw/）全線上無紙化上傳申請表件。',
          'reminder_eligible': False,
          'checked_at': '2026-10-17T05:35:00Z'},
         {'title': '逢甲下一期出國研修甄選日期待核實',
          'details': ['一般介紹列每年6月中及12月中公告簡章，申請期間約1至1.5個月。', '下一期開放、截止及11/16–11/20說明會日期均未由本輪來源核實。'],
          'source': {'title': '逢甲大學國際事務處—出國研修申請資訊與 115-1 國際研習週公告',
                     'source_url': 'https://oia.fcu.edu.tw/sap/introduction/',
                     'category': 'exchange_application',
                     'summary': '115-1 國際研習週場次與每年 12 月中旬選送簡章時程。'},
          'scope': 'home_application',
          'program_types': ['exchange'],
          'academic_year': '115',
          'application_round': '115-2 選送（2027秋季班）',
          'audience': 'all_students',
          'opens_at': None,
          'deadline_at': None,
          'date_status': 'needs_confirmation',
          'status': 'needs_confirmation',
          'status_note': '官方系統目前列115-1已截止梯次；一般介紹僅列每年6月中及12月中公告簡章，下一期精確日期未由本輪來源確認。',
          'deadline_note': '請依當期簡章確認，不能將12月中旬或1月中旬轉為精確日期。',
          'reminder_eligible': False,
          'checked_at': '2026-10-17T05:35:00Z'}],
        "program_overview": [
            {
                "title": f"逢甲大學國際事務處出國研修計畫總覽（{len(partners)} 所交換與雙聯合作大學）",
                "details": [
                    f"逢甲大學國際事務處（Office of International Affairs）建置完善之「出國研修申請及查詢系統（oiasap.fcu.edu.tw）」，本平台完整收錄 {len(partners)} 所校級交換與雙聯合作大學（含當期 oiasap 開放申請之 {open_partner_count} 所國際、大陸及香港合作校，以及 {len(partners) - open_partner_count} 所歷年與簽約交換協議姐妹校）。",
                    "全校採無紙化線上申請（至多選填 5 所志願學校），初審時自動同步審核「逢甲大學出國研修獎助學金」，並提供教育部「學海飛颺／學海惜珠」、「張保隆校長紀念獎助學金（上限 20 萬元）」與「新生鷹揚獎助學金（來回機票實報實核）」等多元獎助。",
                    f"本平台完整整合逢甲大學 {len(partners)} 所合作大學之申請門檻、Fact Sheet／課程目錄連結、115-1 初審分發 71 名錄取紀錄，以及涵蓋 {exp_covered_schools} 所合作校之官方 SharePoint 學長姐研修心得專區與真心話見證。",
                ],
                "source": {
                    "title": "逢甲大學國際事務處—學生出國研習與 oiasap 查詢系統",
                    "source_url": "https://oia.fcu.edu.tw/sap/introduction/",
                    "category": "partner_school",
                    "summary": "逢甲大學校級交換學生、雙聯學制與出國研修獎助總覽。",
                },
            }
        ],
        "eligibility": [
            {
                "title": "申請資格、GPA 3.0 門檻、保證金（NT$10,000／5,000）與最低修課學分規定",
                "details": [
                    "學籍與年級：提出申請及出國研修期間須為逢甲大學註冊在學學位生（原則上不得為延修生；大學部須入學或復學滿 1 學期以上，碩博士班研究生首學期即可申請）。同一學制交換累計以 2 學期為限。",
                    "學業成績門檻：在校歷年總平均 GPA 3.0（含）以上（約 75 分以上）；申請一學年學費互免交換者，歷年系排名須達前 50%。",
                    "保證金與志工義務：獲姊妹校入學許可後 2 週內，獲獎助或學費互免生須繳交保證金 NT$10,000、自費生繳交 NT$5,000；返國後修課及格率達 1/2 以上、1 個月內繳交 2,000 字研習報告書，且學費互免／獲獎生完成每學期 50 小時志工服務後無息退還。",
                    "境外最低修課學分：學士班非應屆畢業學生每學期至少 12 學分、學士班應屆畢業學生至少 9 學分、碩博士班至少 3 學分（特殊情況經系／學程主任核可並報教務處備查者例外）（獲教育部學海獎學金者須修讀至少 4 學分本科系必選修專業課程）。",
                ],
                "source": {
                    "title": "逢甲大學 115-1 學年度選送學生出國研修簡章（校級合作）",
                    "source_url": "https://oia.fcu.edu.tw/sap/introduction/",
                    "category": "exchange_application",
                    "summary": "申請資格、GPA 3.0 門檻、保證金、志工時數與最低修課學分規定。",
                },
            }
        ],
        "language_requirements": [
            {
                "title": "國際地區有效外語檢定門檻（2024/10/01 後取得）與大陸地區免語檢規範",
                "details": [
                    "申請赴國際及香港地區姊妹校者，須於初審報名時上傳 2024年10月1日（含）後應試取得之 TOEFL iBT、IELTS Academic、TOEIC、JLPT、TOPIK 或歐語檢定官方成績單。",
                    "各姊妹校外語門檻依 oiasap 系統公告為準（歐美紐澳常見為 TOEFL iBT 61–85 或 IELTS 5.5–6.5；日韓及部分歐洲商管學院亦採認 TOEIC 550–800 或 JLPT N1–N3 / TOPIK 2–4 級）。",
                    "申請赴大陸地區姊妹校交換者免附外語檢定證明；惟「國際地區」與「大陸地區」僅能擇一報名。",
                ],
                "source": {
                    "title": "逢甲大學出國研修學校查詢系統（oiasap.fcu.edu.tw）",
                    "source_url": "https://oiasap.fcu.edu.tw/",
                    "category": "exchange_application",
                    "summary": "各國交換姊妹校語言檢定、開放學院與 GPA 門檻查詢系統。",
                },
            }
        ],
        "required_documents": [
            {
                "title": "逢甲大學 oiasap 系統全線上無紙化申請應繳文件清單",
                "details": [
                    "1. 出國研修申請資訊簡表（由 oiasap 系統自動產生）及本人 2 吋正面半身脫帽證件照（JPG）。",
                    "2. 家長同意書（附件一，家長親筆簽名）、研究生指導教授同意書（附件三，研究生必繳）及 1,000 字以上中英文研修計畫（附件二）。",
                    "3. 在校獎懲紀錄（MyFCU 列印並至學務處生輔組［行政二館一樓］蓋確認章）與歷年成績單正本（含最新學期 GPA 與總平均；國際地區須同時檢附中、英文歷年成績單）。",
                    "4. 外語能力檢定成績證明（國際地區必繳，2024/10/01 後取得；大陸地區免附）及清寒弱勢證明（非必繳，具資格者可獲加發獎助）。",
                ],
                "source": {
                    "title": "逢甲大學 115-1 學年度選送學生出國研修簡章（校級合作）",
                    "source_url": "https://oia.fcu.edu.tw/sap/introduction/",
                    "category": "exchange_application",
                    "summary": "oiasap 線上申請應繳表件規格與核章規定。",
                },
            }
        ],
        "scholarship_info": [
            {
                "title": "逢甲大學出國研修獎助學金、教育部學海飛颺／惜珠、張保隆校長紀念獎助學金與鷹揚獎助學金",
                "details": [
                    "逢甲出國研修獎助於線上報名後自動納入審核；實際名額與金額依當年預算、申請人數及審查核定，不是按排名保證固定金額。經濟弱勢或家庭突遭變故者可提出證明供審查。",
                    "教育部學海飛颺（班排前 30% 或研究生 80 分以上，每人至少 NT$60,000 起）及學海惜珠（具低收／中低收／特殊境遇家庭證明，依教育部核定補助）獎學金。",
                    "張保隆校長紀念獎助學金（班排前 35% 或研究生 80 分以上，清寒優先，每人上限 NT$200,000）及新生鷹揚獎助學金（提供乙次赴學費互免姐妹校交換往返機票實報實核，國際上限 NT$40,000／大陸上限 NT$20,000）。",
                ],
                "source": {
                    "title": "逢甲大學國際事務處—出國研修獎助學金專區",
                    "source_url": "https://oia.fcu.edu.tw/sap/scholarship/",
                    "category": "scholarship",
                    "summary": "出國研修獎助學金、學海飛颺、學海惜珠、張保隆校長紀念獎助學金與鷹揚獎助學金辦法。",
                },
            }
        ],
        "document_explanations": [
            {
                "title": "逢甲大學 oiasap 無紙化線上申請、保證金（NT$10,000／5,000）與放棄聲明書規範",
                "summary": "逢甲大學出國研修分為「校內初審（oiasap 系統全線上申請）」與「研修學校複審」兩階段辦理。",
                "key_points": [
                    "校內初審全數採線上填報與電子檔上傳（https://oiasap.fcu.edu.tw/），惟「在校獎懲紀錄」須先自 MyFCU 列印後至學務處生輔組（行政二館一樓）加蓋確認章再掃描上傳。",
                    "取得姊妹校入學許可後 2 週內須繳交保證金（獲獎助或學費互免生 NT$10,000、自費生 NT$5,000）；若獲推薦後欲放棄資格，須填寫並繳交《錄取資格放棄聲明書》。",
                ],
                "applies_to": [],
                "source": {
                    "title": "逢甲大學 115-1 學年度選送學生出國研修簡章與錄取資格放棄聲明書",
                    "source_url": "https://oia.fcu.edu.tw/sap/introduction/",
                    "category": "exchange_application",
                    "summary": None,
                },
                "document_url": "https://oia.fcu.edu.tw/sap/introduction/",
                "document_type": "official_document",
                "full_text_extracted": True,
            }
        ],
        "rule_explanations": [
            {
                "title": "逢甲大學選送學生出國研修作業要點：修課學分門檻、志工服務時數與獎助學金審核",
                "summary": "規範逢甲大學交換生在校 GPA 3.0 門檻、境外最低修課學分、每學期 50 小時志工服務義務及校內獎助學金自動審核機制。",
                "key_points": [
                    "出國研修期間須於逢甲大學註冊並繳交全額學雜費；每學期最低修課學分為學士班非應屆畢業學生 12 學分、學士班應屆畢業學生 9 學分、碩博士班 3 學分（特殊情況經系／學程主任核可並報教務處備查者例外）（學海受獎生須修讀至少 4 學分本科系必選修專業課程）。",
                    "返國後修課及格率須達 1/2 以上、1 個月內提交 2,000 字以上研習報告書，且學費互免／獲獎助學生須完成每學期 50 小時（兩學期 100 小時）志工服務，始得無息退還保證金。",
                    "校內初審時自動依學業排名與身分審核「逢甲大學出國研修獎助學金」（國際地區最高 NT$21,000、大陸地區最高 NT$11,000），另可依公告申請教育部學海飛颺／惜珠與張保隆校長紀念獎助學金。",
                ],
                "applies_to": [],
                "source": {
                    "title": "逢甲大學 115-1 學年度選送學生出國研修簡章（校級合作）",
                    "source_url": "https://oia.fcu.edu.tw/sap/introduction/",
                    "category": "exchange_application",
                    "summary": None,
                },
                "document_url": "https://oia.fcu.edu.tw/sap/introduction/",
                "document_type": "official_document",
                "full_text_extracted": True,
            }
        ],
        "sources": [
            {
                "title": "逢甲大學出國研修學校查詢與線上申請系統（oiasap.fcu.edu.tw）",
                "source_url": "https://oiasap.fcu.edu.tw/",
                "category": "partner_school",
                "summary": None,
            },
            {
                "title": "逢甲大學國際事務處—出國研修申請資訊與 115-1 選送簡章",
                "source_url": "https://oia.fcu.edu.tw/sap/introduction/",
                "category": "exchange_application",
                "summary": None,
            },
            {
                "title": "逢甲大學國際事務處—出國研修獎助學金專區（學海飛颺／惜珠、張保隆校長紀念獎助學金、出國研修獎助學金）",
                "source_url": "https://oia.fcu.edu.tw/sap/scholarship/",
                "category": "scholarship",
                "summary": None,
            },
            {
                "title": "逢甲大學 115-1 學年度選送學生出國研修分發暨獎助學金名單（國際地區 46 名）",
                "source_url": "https://service825.fcu.edu.tw/infofiles/F_dvdjo5xweac25492665.pdf",
                "category": "exchange_application",
                "summary": None,
            },
            {
                "title": "逢甲大學 115-1 學年度選送學生出國研修分發暨獎助學金名單（大陸地區 25 名）",
                "source_url": "https://service825.fcu.edu.tw/infofiles/F_lwv4fzkckfwf676fc73.pdf",
                "category": "exchange_application",
                "summary": None,
            },
            {
                "title": "逢甲大學國際事務處—雙聯合作學校一覽表",
                "source_url": "https://oia.fcu.edu.tw/sap/dualdegree/",
                "category": "partner_school",
                "summary": None,
            },
            {
                "title": "逢甲大學國際事務處—全球合作姐妹校名冊",
                "source_url": "https://oia.fcu.edu.tw/collaboration/",
                "category": "partner_school",
                "summary": None,
            },
        ],
    }
    (OFFICIAL_FCU_DIR / "student_dashboard.json").write_text(
        json.dumps(student_dashboard_payload, ensure_ascii=False, indent=2)
        + "\n",
        encoding="utf-8",
    )

    pages_records = [
        {
            "title": "逢甲大學：115-1 選送學生出國研修時程、115-1 國際研習週與 115-2 申請預告",
            "source_url": "https://oia.fcu.edu.tw/sap/introduction/",
            "published_at": "2026-06-29T00:00:00Z",
            "text": "\n".join(exchange_info_payload["application_period"]),
            "summary": "\n".join(exchange_info_payload["application_period"]),
            "category": "exchange_application",
            "attachments": [],
            "crawled_at": "2026-10-17T05:35:00Z",
            "content_hash": hashlib.sha256(
                "\n".join(exchange_info_payload["application_period"]).encode(
                    "utf-8"
                )
            ).hexdigest(),
        },
        {
            "title": "逢甲大學：交換學生 GPA 3.0 門檻、一學年系排前 50%、保證金與最低修課學分規定",
            "source_url": "https://oia.fcu.edu.tw/sap/introduction/",
            "published_at": "2026-06-29T00:00:00Z",
            "text": "\n".join(exchange_info_payload["eligibility"]),
            "summary": "\n".join(exchange_info_payload["eligibility"]),
            "category": "exchange_application",
            "attachments": [],
            "crawled_at": "2026-10-17T05:35:00Z",
            "content_hash": hashlib.sha256(
                "\n".join(exchange_info_payload["eligibility"]).encode("utf-8")
            ).hexdigest(),
        },
        {
            "title": "逢甲大學：oiasap 出國研修學校查詢系統與各國語言檢定門檻",
            "source_url": "https://oiasap.fcu.edu.tw/",
            "published_at": "2026-06-29T00:00:00Z",
            "text": "\n".join(exchange_info_payload["language_requirement"]),
            "summary": "\n".join(exchange_info_payload["language_requirement"]),
            "category": "exchange_application",
            "attachments": [],
            "crawled_at": "2026-10-17T05:35:00Z",
            "content_hash": hashlib.sha256(
                "\n".join(exchange_info_payload["language_requirement"]).encode(
                    "utf-8"
                )
            ).hexdigest(),
        },
        {
            "title": "逢甲大學：oiasap 全線上無紙化申請應繳文件與生輔組獎懲紀錄核章規範",
            "source_url": "https://oia.fcu.edu.tw/sap/introduction/",
            "published_at": "2026-06-29T00:00:00Z",
            "text": "\n".join(exchange_info_payload["required_documents"]),
            "summary": "\n".join(exchange_info_payload["required_documents"]),
            "category": "exchange_application",
            "attachments": [],
            "crawled_at": "2026-10-17T05:35:00Z",
            "content_hash": hashlib.sha256(
                "\n".join(exchange_info_payload["required_documents"]).encode(
                    "utf-8"
                )
            ).hexdigest(),
        },
        {
            "title": "逢甲大學：出國研修獎助學金、教育部學海飛颺／惜珠、張保隆校長紀念獎助學金與鷹揚獎助學金",
            "source_url": "https://oia.fcu.edu.tw/sap/scholarship/",
            "published_at": "2026-06-29T00:00:00Z",
            "text": "\n".join(exchange_info_payload["scholarship_info"]),
            "summary": "\n".join(exchange_info_payload["scholarship_info"]),
            "category": "scholarship",
            "attachments": [],
            "crawled_at": "2026-10-17T05:35:00Z",
            "content_hash": hashlib.sha256(
                "\n".join(exchange_info_payload["scholarship_info"]).encode(
                    "utf-8"
                )
            ).hexdigest(),
        },
    ]
    (OFFICIAL_FCU_DIR / "pages.jsonl").write_text(
        "\n".join(json.dumps(p, ensure_ascii=False) for p in pages_records)
        + "\n",
        encoding="utf-8",
    )

    home_rules = {
        "school_id": "fcu",
        "school_name": "逢甲大學",
        "eligibility": student_dashboard_payload["eligibility"],
        "application_periods": student_dashboard_payload["application_periods"],
        "selection_rules": {
            "gpa_minimum": 3.0,
            "full_year_waiver_rank_top_percent_limit": 50.0,
            "max_preferences": 5,
            "deposit_twd": {
                "tuition_waiver_or_scholarship": 10000,
                "self_funded": 5000,
            },
            "volunteer_hours_per_semester": 50,
            "minimum_credits_per_semester": {
                "undergraduate_year_1_to_3": 12,
                "undergraduate_year_4": 9,
                "graduate": 3,
                "moe_xuehai_major_related": 4,
            },
        },
        "source_urls": fcu_source_urls,
        "verified_at": "2026-10-17",
    }
    (OFFICIAL_FCU_DIR / "home_rules.json").write_text(
        json.dumps(home_rules, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    (OFFICIAL_FCU_DIR / "documents.json").write_text(
        json.dumps(
            {
                "school_name": "逢甲大學",
                "required_documents": student_dashboard_payload[
                    "required_documents"
                ],
                "source_urls": fcu_source_urls,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    (OFFICIAL_FCU_DIR / "scholarships.json").write_text(
        json.dumps(
            {
                "school_name": "逢甲大學",
                "scholarships": student_dashboard_payload["scholarship_info"],
                "source_urls": fcu_source_urls,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    completeness = {
        "school_id": "fcu",
        "school_name": "逢甲大學",
        "total_partners": len(partners),
        "partner_count": len(partners),
        "international_partners": sum(
            1 for p in partners if p["country"] != "中國大陸"
        ),
        "mainland_partners": sum(
            1 for p in partners if p["country"] == "中國大陸"
        ),
        "experience_report_covered_partners": exp_covered_schools,
        "open_partners": sum(p["availability_status"] == "open" for p in partners),
        "reference_only_partners": sum(p["availability_status"] == "reference_only" for p in partners),
        "needs_confirmation_partners": sum(p["availability_status"] == "needs_confirmation" for p in partners),
        "whole_record_verified_partners": 0,
        "source_program_rows_matched": sum(len(p.get("program_options", [])) for p in partners),
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
        "active_term": "115-1赴2027春季交換已截止；下一梯正式日期待核實。",
        "verified_at": "2026-10-17",
    }
    (OFFICIAL_FCU_DIR / "catalog-completeness.json").write_text(
        json.dumps(completeness, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    (OFFICIAL_FCU_DIR / "verification_status.json").write_text(
        json.dumps(
            {
                "school_id": "fcu",
                "school_name": "逢甲大學",
                "status": "partially_reviewed",
                "checked_at": "2026-10-20T19:15:10+00:00",
                "whole_record_verified": False,
                "note": "已核對部分母校條文及115-1名單指定欄位；全體接待校規則與生活資訊尚未逐項核實。",
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
            "sources/fcu/oiasap_programs_1151_reviewed_20261021.json",
            "https://oiasap.fcu.edu.tw/v2/programs?sms=1151",
            "2026-10-21取得的115-1方案快照；僅核對指定欄位及方案範圍，非整筆或現行接待校規則核實",
        ),
        (
            "sources/fcu/oiasap_programs_1151.json",
            "https://oiasap.fcu.edu.tw/v2/programs?sms=1151",
            "逢甲大學出國研修申請系統（oiasap）115-1 學期開放研修計畫清單（152 筆計畫、147 所當期開放合作大學）",
        ),
        (
            "sources/fcu/oiasap_programs_1142.json",
            "https://oiasap.fcu.edu.tw/v2/programs?sms=1142",
            "逢甲大學出國研修申請系統（oiasap）114-2 學期開放研修計畫清單",
        ),
        (
            "sources/fcu/oiasap_details.json",
            "https://oiasap.fcu.edu.tw/v2/details",
            "逢甲大學 oiasap 系統當期開放學期、申請起訖時間與簡章 PDF 路徑資訊",
        ),
        (
            "sources/fcu/oiasap_colleges.json",
            "https://oiasap.fcu.edu.tw/v2/details/colleges",
            "逢甲大學 oiasap 系統學院與系所代碼對照表",
        ),
        (
            "sources/fcu/fcu_115_1_spring2027_guidelines.pdf",
            "https://oiasap.fcu.edu.tw/pdf/d44f/逢甲大學115-1學年度選送學生出國研修簡章（校級合作）_20260629.pdf",
            "逢甲大學 115-1 學年度選送學生出國研修簡章（校級合作，9 頁完整規定與獎助標準）",
        ),
        (
            "sources/fcu/fcu_115_1_spring2027_intl_admitted.pdf",
            "https://service825.fcu.edu.tw/infofiles/F_dvdjo5xweac25492665.pdf",
            "逢甲大學 115-1 學年度選送學生出國研修分發暨獎助學金名單：國際地區（28 校 46 名學生）",
        ),
        (
            "sources/fcu/fcu_115_1_spring2027_mainland_admitted.pdf",
            "https://service825.fcu.edu.tw/infofiles/F_lwv4fzkckfwf676fc73.pdf",
            "逢甲大學 115-1 學年度選送學生出國研修分發暨獎助學金名單：大陸地區（9 校 25 名學生）",
        ),
        (
            "sources/fcu/fcu_waiver_form.pdf",
            "https://service825.fcu.edu.tw/infofiles/F_hv0vi21ylfgacfc4e6c.pdf",
            "逢甲大學選送學生出國研修錄取資格放棄聲明書",
        ),
        (
            "sources/fcu/fcu_sap_introduction.html",
            "https://oia.fcu.edu.tw/sap/introduction/",
            "逢甲大學國際事務處—出國研修申請資訊專頁",
        ),
        (
            "sources/fcu/fcu_sap_scholarship.html",
            "https://oia.fcu.edu.tw/sap/scholarship/",
            "逢甲大學國際事務處—出國研修獎助學金專頁",
        ),
        (
            "sources/fcu/fcu_sap_dualdegree.html",
            "https://oia.fcu.edu.tw/sap/dualdegree/",
            "逢甲大學國際事務處—雙聯合作學校專頁",
        ),
        (
            "sources/fcu/fcu_collaboration_partners.html",
            "https://oia.fcu.edu.tw/collaboration/",
            "逢甲大學國際事務處—全球合作姐妹校列表",
        ),
        (
            "sources/fcu/fcu_resolved_locations.json",
            "https://oiasap.fcu.edu.tw/",
            "逢甲大學 163 所出國研修合作大學 ROR / Wikidata 地理座標核對表",
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
                "fetched_at": "2026-10-17T05:35:00Z",
            })
    provenance_payload = {
        "school_id": "fcu",
        "school_name": "逢甲大學",
        "generated_at": "2026-10-17T05:35:00Z",
        "active_cycle_note": completeness["active_term"],
        "sources": prov_sources,
    }
    (OFFICIAL_FCU_DIR / "import_provenance.json").write_text(
        json.dumps(provenance_payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    from exchange_info.generated_content_review import review_generated_content
    review_generated_content(REPO_ROOT, "fcu", round_id=20)
    review_generated_content(REPO_ROOT, "fcu", round_id=21)

    print(
        f"Successfully built FCU catalog: {len(partners)} partners ({open_partner_count} open, "
        f"{completeness['verified_campus_images']} verified images, {completeness['verified_locations']} verified locations), "
        f"{len(workflows)} workflows, {len(destinations)} destinations, {len(research_records)} research records, "
        f"{exp_covered_schools} schools with experience/admitted records ({len(student_experience_rows)} rows)."
    )


if __name__ == "__main__":
    main()
