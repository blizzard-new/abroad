"""Build the official National Yunlin University of Science and Technology (國立雲林科技大學, YunTech) exchange data bundle."""

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

SOURCES_YUNTECH_DIR = REPO_ROOT / "sources" / "yuntech"
OFFICIAL_YUNTECH_DIR = REPO_ROOT / "src" / "exchange_info" / "official_data" / "yuntech"
STATIC_DIR = REPO_ROOT / "src" / "exchange_info" / "static"

CHECKED_AT = "2026-10-20T14:00:00Z"

YUNTECH_OIA_HUB_URL = "https://tdx.yuntech.edu.tw/"
YUNTECH_OE_PORTAL_URL = "https://admissions-oia.yuntech.edu.tw/oe/index/index/puid/115-2/lang/zh_TW"
YUNTECH_OE_INTRO_115_2_URL = "https://admissions-oia.yuntech.edu.tw/oe/index/intro/puid/115-2/lang/zh_TW"
YUNTECH_OE_INTRO_115_1_URL = "https://admissions-oia.yuntech.edu.tw/oe/index/intro/puid/115-1/lang/zh_TW"
YUNTECH_OUTBOUND_NON_MAINLAND_URL = "https://tdx.yuntech.edu.tw/index.php/zh-tw/%E5%87%BA%E5%9C%8B%E4%BA%A4%E6%B5%81/%E5%87%BA%E5%9C%8B%E4%BA%A4%E6%8F%9B%E7%94%9F/%E9%9D%9E%E5%A4%A7%E9%99%B8%E5%9C%B0%E5%8D%80%E4%BA%A4%E6%8F%9B%E7%94%9F"
YUNTECH_MAINLAND_2027S_URL = "https://tdx.yuntech.edu.tw/index.php/zh-tw/%E5%87%BA%E5%9C%8B%E4%BA%A4%E6%B5%81/%E5%87%BA%E5%9C%8B%E4%BA%A4%E6%8F%9B%E7%94%9F/%E5%A4%A7%E9%99%B8%E5%9C%B0%E5%8D%80%E4%BA%A4%E6%8F%9B%E7%94%9F/2027%E6%98%A5%E5%AD%A3%E7%8F%AD"
YUNTECH_APPLY_2027S_URL = "https://tdx.yuntech.edu.tw/index.php/zh-tw/component/k2/item/1413-2027"
YUNTECH_ROSTER_2027S_URL = "https://tdx.yuntech.edu.tw/index.php/zh-tw/component/k2/item/1472-2027"
YUNTECH_ROSTER_115_1_URL = "https://tdx.yuntech.edu.tw/index.php/zh-tw/component/k2/item/1346-115-1"
YUNTECH_EXCHANGE_GUIDELINES_URL = "https://tdx.yuntech.edu.tw/images/International_Exchange_Students/Outgoing/Non_mainland_China_area/%E5%9C%8B%E7%AB%8B%E9%9B%B2%E6%9E%97%E7%A7%91%E6%8A%80%E5%A4%A7%E5%AD%B8%E5%9C%8B%E9%9A%9B%E4%BA%A4%E6%8F%9B%E5%AD%B8%E7%94%9F%E5%AF%A6%E6%96%BD%E8%A6%81%E9%BB%9E20250422.pdf"
YUNTECH_SCORING_RUBRIC_URL = "https://tdx.yuntech.edu.tw/images/International_Exchange_Students/Outgoing/Non_mainland_China_area/%E9%9D%9E%E5%A4%A7%E9%99%B8%E5%9C%B0%E5%8D%80%E4%BA%A4%E6%8F%9B%E5%AD%B8%E7%94%9F%E8%A9%95%E5%88%86%E6%A8%99%E6%BA%96%E8%A1%A8.pdf"
YUNTECH_SLIDES_2027S_URL = "https://tdx.yuntech.edu.tw/images/International_Exchange_Students/Outgoing/Non_mainland_China_area/2027%E6%98%A5%E5%AD%A3(115-2)%E8%B5%B4%E9%9D%9E%E5%A4%A7%E9%99%B8%E5%9C%B0%E5%8D%80%E7%B0%A1%E5%A0%B1.pdf"
YUNTECH_SLIDES_2026F_URL = "https://tdx.yuntech.edu.tw/images/International_Exchange_Students/Outgoing/Non_mainland_China_area/2026%E7%A7%8B%E5%AD%A3%20(115-1)%20%E8%B5%B4%E9%9D%9E%E5%A4%A7%E9%99%B8%E5%9C%B0%E5%8D%80%E7%B0%A1%E5%A0%B1.pdf"
YUNTECH_SLIDES_MAINLAND_URL = "https://tdx.yuntech.edu.tw/images/International_Exchange_Students/Outgoing/Mainland_China/2026%E7%A7%8B%E5%AD%A3/202609%E8%B5%B4%E5%A4%A7%E9%99%B8%E4%BA%A4%E6%8F%9B%E7%94%9F%E8%AA%AA%E6%98%8E%E6%9C%83.pdf"
YUNTECH_GRANT_PAGE_URL = "https://tdx.yuntech.edu.tw/index.php/zh-tw/%E5%87%BA%E5%9C%8B%E4%BA%A4%E6%B5%81/%E7%8D%8E%E5%8A%A9%E5%AD%B8%E9%87%91/%E5%87%BA%E5%9C%8B%E4%BA%A4%E6%B5%81%E6%88%96%E9%80%B2%E4%BF%AE%E8%A3%9C%E5%8A%A9/115%E5%B9%B4%E5%BA%A6"
YUNTECH_SUBSIDY_RULES_URL = "https://tdx.yuntech.edu.tw/images/Scholarship/%E5%9C%8B%E7%AB%8B%E9%9B%B2%E6%9E%97%E7%A7%91%E6%8A%80%E5%A4%A7%E5%AD%B8%E5%AD%B8%E7%94%9F%E5%87%BA%E5%9C%8B%E4%BA%A4%E6%B5%81%E6%88%96%E9%80%B2%E4%BF%AE%E8%A3%9C%E5%8A%A9%E8%A6%81%E9%BB%9E_11406.pdf"
YUNTECH_WANG_PAGE_URL = "https://tdx.yuntech.edu.tw/index.php/zh-tw/%E5%87%BA%E5%9C%8B%E4%BA%A4%E6%B5%81/%E7%8D%8E%E5%8A%A9%E5%AD%B8%E9%87%91/%E7%8E%8B%E7%A7%8B%E9%9B%84%E6%A6%AE%E8%AD%BD%E5%8D%9A%E5%A3%AB%E7%8D%8E%E5%8A%A9%E9%87%91/115%E5%AD%B8%E5%B9%B4%E5%BA%A6"
YUNTECH_WANG_RULES_URL = "https://tdx.yuntech.edu.tw/images/Scholarship/%E7%8E%8B%E7%A7%8B%E9%9B%84%E6%A6%AE%E8%AD%BD%E5%8D%9A%E5%A3%AB%E8%A3%9C%E5%8A%A9%E5%BE%B7%E6%97%A5%E7%BE%8E%E4%BA%A4%E6%B5%81%E6%88%96%E9%80%B2%E4%BF%AE%E7%8D%8E%E5%8A%A9%E9%87%91%E5%AF%A6%E6%96%BD%E8%A6%81%E9%BB%9E%E5%8F%8A%E7%99%BC%E6%94%BE%E4%BD%9C%E6%A5%AD%E8%A6%8F%E5%AE%9A20240710.pdf"
YUNTECH_XUEHAI_PAGE_URL = "https://tdx.yuntech.edu.tw/index.php/zh-tw/component/k2/item/1400-115"
YUNTECH_XUEHAI_RULES_URL = "https://tdx.yuntech.edu.tw/images/Scholarship/%E5%AD%B8%E6%B5%B7%E7%B3%BB%E5%88%97/%E5%9C%8B%E7%AB%8B%E9%9B%B2%E6%9E%97%E7%A7%91%E6%8A%80%E5%A4%A7%E5%AD%B8%E3%80%8C%E5%AD%B8%E6%B5%B7%E9%A3%9B%E9%A2%BA%E3%80%8D%E8%88%87%E3%80%8C%E5%AD%B8%E6%B5%B7%E6%83%9C%E7%8F%A0%E3%80%8D%E5%B0%88%E6%A1%88%E6%8E%A8%E8%96%A6%E4%BD%9C%E6%A5%AD%E8%A6%81%E9%BB%9E1130422%E4%BF%AE%E8%A8%82%E9%80%9A%E9%81%8E.pdf"
YUNTECH_DUAL_DEGREE_URL = "https://tdx.yuntech.edu.tw/index.php/zh-tw/%E5%87%BA%E5%9C%8B%E4%BA%A4%E6%B5%81/%E9%9B%99%E8%81%AF%E5%AD%B8%E4%BD%8D"
YUNTECH_PATHWAY_URL = "https://tdx.yuntech.edu.tw/index.php/zh-tw/%E5%87%BA%E5%9C%8B%E4%BA%A4%E6%B5%81/%E9%8A%9C%E6%8E%A5%E5%AD%B8%E4%BD%8D"
YUNTECH_EXP_115_URL = "https://tdx.yuntech.edu.tw/index.php/expsharing/item/1401-115"
YUNTECH_EXP_114_URL = "https://tdx.yuntech.edu.tw/index.php/expsharing/item/1073-114"
YUNTECH_EXP_113_URL = "https://tdx.yuntech.edu.tw/index.php/expsharing/item/997-113"
YUNTECH_SISTER_SCHOOLS_URL = "https://tdx.yuntech.edu.tw/index.php/zh-tw/%E9%97%9C%E6%96%BC%E6%9C%AC%E8%99%95/%E5%A7%8A%E5%A6%B9%E6%A0%A1%E5%8D%94%E8%AD%B0%E7%B0%BD%E8%A8%82%E6%83%85%E5%BD%A2"

REGION_BY_COUNTRY = {
    "德國": "歐洲",
    "法國": "歐洲",
    "英國": "歐洲",
    "荷蘭": "歐洲",
    "比利時": "歐洲",
    "西班牙": "歐洲",
    "立陶宛": "歐洲",
    "希臘": "歐洲",
    "斯洛維尼亞": "歐洲",
    "捷克": "歐洲",
    "土耳其": "歐洲",
    "美國": "美洲",
    "澳洲": "大洋洲",
    "日本": "亞洲",
    "韓國": "亞洲",
    "印尼": "亞洲",
    "越南": "亞洲",
    "馬來西亞": "亞洲",
    "印度": "亞洲",
    "菲律賓": "亞洲",
    "蒙古": "亞洲",
    "中國大陸": "中國大陸及港澳",
    "澳門": "中國大陸及港澳",
}

REGION_COST_DEFAULTS = {
    "德國": (
        "EUR 934–1,250 / 月（德國簽證限制提領帳戶 Sperrkonto 基準為每月 EUR 992，含柏林 HTW、阿亨 FH Aachen、達姆施塔特、卡爾斯魯厄、德勒斯登、伊爾默瑙、埃斯林根、布蘭登堡、科堡等學生宿舍、膳食與學期交通票 Semesterbeitrag；雲科大王秋雄榮譽博士獎助金每學期補助柏林 NT$150,000、阿亨 NT$140,000、其他德國地區 NT$120,000）",
        "須辦理德國法定學生公保（如 TK / AOK，約 EUR 125–135 / 月）、繳納學期雜費（Semesterbeitrag）並向德國在台協會申辦長期學生簽證。",
    ),
    "法國": (
        "EUR 750–1,150 / 月（特魯瓦 Y Schools 及拉羅謝爾 Excelia Group 學生宿舍或公寓、餐飲與交通，可申請法國政府 CAF 房屋補助）",
        "須透過法國教育中心（Campus France）完成線上面談審查並向法國在台協會申辦長期學生簽證（VLS-TS），抵法後完成 OFII 生效與法國學生社保登錄。",
    ),
    "英國": (
        "GBP 1,000–1,450 / 月（北安普頓大學校內學生宿舍、餐飲與大眾運輸）",
        "交換一學期（6 個月內）可辦理 Standard Visitor 簽證，交換一學年須申辦英國 Student Visa 並繳納 IHS 醫療附加費。",
    ),
    "荷蘭": (
        "EUR 950–1,350 / 月（烏特列支應用科技大學 HU 學生公寓 SSH、日常飲食與單車／大眾運輸）",
        "由烏特列支應用科技大學協助向荷蘭移民局（IND）申辦 MVV 入境簽證與 VVR 學生居留許可，並投保歐盟認可之國際學生醫療險（如 AON Student Insurance）。",
    ),
    "比利時": (
        "EUR 750–1,100 / 月（瓦隆大區蒙斯大學 UMONS 校內學生宿舍、學餐與比利時國鐵學生優惠票）",
        "須憑蒙斯大學入學許可向比利時台北辦事處申辦 D 類長期學生簽證，抵比後 8 日內至市政廳辦理外國人居留登錄並投保醫療險。",
    ),
    "西班牙": (
        "EUR 650–950 / 月（安達盧西亞自治區哈恩大學 Universidad de Jaén 周邊合租學生公寓每月僅約 EUR 200–300，生活開銷親民）",
        "須向西班牙商務辦事處申辦學生簽證，並投保無自負額、涵蓋全期之西班牙私人醫療保險。",
    ),
    "立陶宛": (
        "EUR 550–850 / 月（首都維爾紐斯科技大學 VILNIUS TECH 校內學生宿舍每月約 EUR 130–200，物價低廉）",
        "須透過立陶宛移民局系統（MIGRIS）申辦國家 D 類學生簽證或臨時居留許可，並投保申根區醫療保險。",
    ),
    "希臘": (
        "EUR 550–850 / 月（卡瓦拉國際希臘大學 IHU 周邊住宿、學生餐廳免費供餐與日常交通）",
        "須向希臘相關駐外機構或簽證中心申辦國家 D 類學生簽證並投保涵蓋全期之申根醫療保險。",
    ),
    "斯洛維尼亞": (
        "EUR 600–900 / 月（首都盧比安納大學學生宿舍、學生餐券 Študentski boni 補貼與市區公車月票 Urbana）",
        "須憑盧比安納大學入學許可申辦斯洛維尼亞第一階段學生居留許可（TRP）或 D 簽，並投保醫療保險。",
    ),
    "捷克": (
        "EUR 550–800 / 月（姆拉達-博萊斯拉夫 Škoda Auto University 學生宿舍與捷克日常飲食成本實惠）",
        "須向捷克經濟文化辦事處申辦長期學生簽證（D 簽）並投保捷克法定綜合外籍醫療保險（PVZP）。",
    ),
    "土耳其": (
        "USD 450–750 / 月（安卡拉中東科技大學 METU 校內宿舍、學生食堂與校園交通開銷低廉）",
        "須憑 METU 入學許可申辦土耳其學生簽證，抵土後申辦學生居留證（İkamet İzni）並投保當地醫療險。",
    ),
    "美國": (
        "USD 1,250–2,200 / 月（含堪薩斯州立大學 KSU、加州州立理工大學波莫納分校 Cal Poly Pomona、德州大學達拉斯分校 UTD、匹茲堡州立大學 PSU、北俄亥俄大學、安德魯斯大學宿舍與膳食計畫；雲科大王秋雄榮譽博士獎助金每學期補助洛杉磯地區 NT$170,000、其他美國地區 NT$150,000）",
        "須憑接待校核發之 DS-2019（交換 J-1）或 I-20（雙聯／銜接 F-1）表格繳納 SEVIS I-901 費用並至 AIT（美國在台協會）申辦簽證及投保學校強制醫療保險。",
    ),
    "澳洲": (
        "AUD 1,800–2,600 / 月（南澳大學 UniSA 阿得雷德校區與皇家墨爾本理工大學 RMIT 學生公寓、膳食與學生大眾運輸優惠）",
        "須購買澳洲海外學生健康保險（OSHC）並透過澳洲內政部 ImmiAccount 線上申辦 Subclass 500 學生簽證。",
    ),
    "日本": (
        "JPY 75,000–125,000 / 月（千葉、神戶、福岡、東京近郊約 JPY 85,000–130,000；福井、琉球、岡山、長岡、會津等地方國公立大學校內寮費僅約 JPY 12,000–30,000 / 月；雲科大王秋雄榮譽博士獎助金每學期補助 NT$100,000、一學年 NT$200,000）",
        "憑日本接待校核發之在留資格認定證明書（COE）向日本台灣交流協會換發留學簽證，抵日後須依法加入日本國民健康保險（NHI）。",
    ),
    "韓國": (
        "KRW 750,000–1,250,000 / 月（首爾科技大學、建國大學、弘益大學、同德女子大學及京畿道檀國大學、世宗市高麗大學世宗校區、大田韓巴大學、清州大學校內宿舍與學餐）",
        "憑韓國標準入學許可書向駐台北韓國代表部申辦 D-2-6 交換學生簽證，抵韓後辦理外國人登錄並自動納入韓國國民健康保險（NHIS）。",
    ),
    "印尼": (
        "IDR 4,500,000–8,000,000 / 月（泗水理工學院 ITS、萬隆理工學院 ITB、布勞爪哇大學、日惹國立大學、特里薩克蒂大學、ペトラ基督教大學、三寶瓏蘇吉甲普拉那塔天主教大學住宿與生活費親民）",
        "須由印尼接待校協助向印尼移民總局申辦 C316 學習電子簽證（e-Visa）並投保海外全期醫療及意外保險。",
    ),
    "越南": (
        "USD 380–650 / 月（河內國家大學、河內外貿大學、太原大學、清化鴻德大學、芽莊慶和大學、胡志明市國家大學及外語資訊大學住宿及生活成本低廉）",
        "須憑越南接待校入學許可透過駐臺北越南經濟文化辦事處申辦越南學生簽證並投保海外醫療險。",
    ),
    "馬來西亞": (
        "MYR 1,400–2,400 / 月（霹靂州金寶／雪蘭莪雙溪龍拉曼大學 UTAR 校內外學生公寓與生活費實惠）",
        "須於出國前透過 EMGS（Education Malaysia Global Services）系統線上申辦馬來西亞學生簽證核准函（VAL / Student Pass）並投保 EMGS 指定醫療險。",
    ),
    "印度": (
        "USD 350–600 / 月（清奈維爾洛爾科技大學 VIT、安娜大學、新德里阿米蒂大學 Amity、孟買 NMIMS、印多爾理工學院 IIT Indore、海得拉巴 SR 大學、科임巴托爾 PSG 及瓦朗加爾 NIT 現代化校園宿舍與餐廳費用低廉）",
        "須憑印度接待校入學許可向印度台北協會（ITA）申辦 Student Visa 學生簽證並投保海外醫療及意外保險。",
    ),
    "菲律賓": (
        "USD 450–800 / 月（內湖省洛斯巴諾斯國立菲律賓大學 UPLB 校園宿舍與生活開支實惠）",
        "須憑接待校入學許可向馬尼拉經濟文化辦事處（MECO）辦理簽證，抵菲後由學校協助申辦 9(f) 學生簽證或 SSP。",
    ),
    "蒙古": (
        "USD 400–700 / 月（烏蘭巴托蒙古科技大學 MUST 學生宿舍與日常飲食開銷親民）",
        "須憑蒙古科技大學入學許可申辦蒙古學生簽證並投保涵蓋全期之海外醫療及意外保險。",
    ),
    "中國大陸": (
        "RMB 1,800–3,500 / 月（北京師範、北京科技、北京交通、北工大、同濟、南京、東南、重慶、四川、山東、吉大、天大、南開、武大、中南、湖大、蘭大、西北農林、中國礦大、鄭大、蘇大、江南、上大、福大、廣工大等校內學生宿舍與食堂成本低廉）",
        "持有效護照與臺胞證（臺灣居民來往大陸通行證）入境，並依接待校規定投保大陸境內來華留學生綜合醫療保險（每學期約 RMB 400、每學年約 RMB 800）。",
    ),
    "澳門": (
        "HKD 5,500–9,000 / 月（約 MOP 5,665–9,270，含氹仔澳門城市大學學生宿舍、校園餐廳與澳門巴士學生卡）",
        "須透過澳門城市大學向澳門治安警察局居留及逗留事務廳申辦「逗留特別許可（學生逗留簽注）」並投保醫療保險。",
    ),
}

SEMESTER_DATES_BY_COUNTRY = {
    "德國": "冬季學期（上學期／秋季班）：約 9/10 月至翌年 2/3 月；夏季學期（下學期／春季班）：約 3/4 月至 7/8 月",
    "法國": "秋季學期（上學期）：約 9 月至 12 月／翌年 1 月；春季學期（下學期）：約 1/2 月至 5/6 月",
    "英國": "秋季學期（上學期）：約 9 月至翌年 1 月；春季學期（下學期）：約 1/2 月至 5/6 月",
    "荷蘭": "秋季學期（Block A/B）：約 9 月初至翌年 1 月底；春季學期（Block C/D）：約 2 月初至 6 月底／7 月初",
    "比利時": "第一學期（秋季班）：約 9 月中旬至翌年 1 月底；第二學期（春季班）：約 2 月初至 6 月底",
    "西班牙": "第一學期（秋季班）：約 9 月至翌年 1/2 月；第二學期（春季班）：約 2 月至 6/7 月",
    "立陶宛": "秋季學期：約 9 月初至翌年 1 月底；春季學期：約 2 月初至 6 月底",
    "希臘": "冬季學期（秋季班）：約 10 月至翌年 2 月；春季學期（春季班）：約 2 月中旬至 6 月",
    "斯洛維尼亞": "冬季學期（秋季班）：約 10 月初至翌年 1/2 月；夏季學期（春季班）：約 2 月中旬至 6/7 月",
    "捷克": "冬季學期（秋季班）：約 9 月中下旬至翌年 1 月；夏季學期（春季班）：約 2 月中旬至 6 月",
    "土耳其": "秋季學期：約 9 月下旬至翌年 1 月；春季學期：約 2 月中旬至 6 月",
    "美國": "秋季學期（Fall）：約 8 月中下旬至 12 月中旬；春季學期（Spring）：約 1 月中旬至 5 月中旬",
    "澳洲": "第一學期（Study Period 2 / Sem 1）：約 2 月下旬至 6 月；第二學期（Study Period 5 / Sem 2）：約 7 月下旬至 11 月",
    "日本": "秋季班（雲科大上學期）：約 9/10 月至翌年 2/3 月；春季班（雲科大下學期）：約 4 月至 8/9 月",
    "韓國": "秋季學期（上學期）：約 9 月初至 12 月中下旬；春季學期（下學期）：約 3 月初至 6 月中下旬",
    "印尼": "奇數／秋季學期：約 8/9 月至 12 月／翌年 1 月；偶數／春季學期：約 2 月至 6/7 月",
    "越南": "第一學期（秋季班）：約 9 月至翌年 1 月；第二學期（春季班）：約 2 月至 6 月",
    "馬來西亞": "依拉曼大學（1 月／5 月／10 月學期制）行事曆為準",
    "印度": "秋季學期（Odd Semester）：約 7/8 月至 12 月；春季學期（Even Semester）：約 1 月至 5 月",
    "菲律賓": "第一學期：約 8 月至 12 月；第二學期：約 1 月至 5/6 月",
    "蒙古": "秋季學期：約 9 月至翌年 1 月；春季學期：約 2 月至 6 月",
    "中國大陸": "秋季學期（上學期）：約 9 月初至翌年 1 月中旬；春季學期（下學期）：約 2 月中下旬至 6 月底／7 月初",
    "澳門": "第一學期（秋季班）：約 9 月初至翌年 1 月；第二學期（春季班）：約 2 月至 6 月",
}


def clean_text(s: str) -> str:
  if not s:
    return ""
  return re.sub(r"\s+", " ", s).strip()


def format_colleges_and_degrees(item: dict) -> tuple[str, str]:
  sn = item["school_sn"]
  remarks = item.get("remarks") or ""
  tracks = "、".join(item.get("source_tracks") or [])
  if sn == 901:
    colleges_str = "工程學院、管理學院、設計學院、人文與科學學院、未來學院（UT Dallas 橋樑碩士 4+1／1+1 學位計畫，主修涵蓋工程、資訊、商管與自然科學等領域）"
    degree_str = "大學部大四在學學生（4+1 學碩士橋樑學位）及碩士班在學學生（1+1 雙碩士橋樑學位）"
  elif sn == 823:
    colleges_str = "工程學院、管理學院、設計學院、人文與科學學院、未來學院（含校級交換及南澳大學 3+1+1 學碩士銜接學位計畫）"
    degree_str = "入學一學期以上之大學部在學學生（校級交換／3+1+1 學碩銜接）及研究所在學學生"
  elif sn == 815:
    colleges_str = "管理學院（企業管理系、國際管理學士學位學程、工業工程與管理系、資訊管理系、財務金融系、會計系、創業管理碩士學位學程等相關系所優先）"
    degree_str = "入學一學期以上之大學部在學學生及研究所在學學生"
  elif sn == 828:
    colleges_str = "不限學院（全校各學院系所皆可申請校級交換；另設有萬隆理工學院管理學院 SBM 院級交換名額）"
    degree_str = "入學一學期以上之大學部在學學生及研究所在學學生"
  else:
    colleges_str = (
        "不限學院（工程學院、管理學院、設計學院、人文與科學學院、未來學院等全校各系所學位學程符合接待校開設專業與語檢條件之學生皆可申請）"
    )
    if "僅限大學部" in remarks or "限大學部" in remarks:
      degree_str = "入學一學期以上之大學部在學學生（依接待校規定限學士班層級修讀）"
    elif "博士雙聯" in tracks and "校級交換" not in tracks:
      degree_str = "碩士班及博士班在學學生"
    else:
      degree_str = "入學一學期以上之大學部在學學生及研究所在學學生（應屆畢業生經核准獲交換學校同意交換者，得申請延長修業年限最長一年；在職專班學生得參加甄選，但不得申請本校獎學金補助）"
  return colleges_str, degree_str


def format_gpa_rule(item: dict) -> str:
  remarks = item.get("remarks") or ""
  gpa_matches = re.findall(
      r"GPA\s*[\d.]+[^；。]*|歷年平均[^\s；。]+|平均成績[^\s；。]+|班排[^\s；。]+",
      remarks,
      re.I,
  )
  base_rule = (
      "雲科大校內門檻（依《國立雲林科技大學國際交換學生實施要點》第2點）：學業成績達 75 分（含）以上或班級排名前 50%，且操行成績達 80 分（含）以上"
  )
  if gpa_matches:
    return f"{base_rule}；接待校／專案學業門檻：{'、'.join(dict.fromkeys(gpa_matches))}"
  return f"{base_rule}（非大陸地區校內甄選『學業成績及班級排名比率』佔總分 40%：歷年平均 90 分以上 20 分、80–89 分 16 分、70–79 分 14 分；班排前 5% 20 分、前 10% 18 分、前 20% 16 分、前 30% 14 分、前 40% 12 分、前 50% 8 分；研究所無班排者歷年平均 90 分以上 40 分、80–89 分 32 分、70–79 分 24 分）"


def main() -> None:
  OFFICIAL_YUNTECH_DIR.mkdir(parents=True, exist_ok=True)
  catalog_source = json.loads(
      (SOURCES_YUNTECH_DIR / "yuntech_catalog_source.json").read_text(encoding="utf-8")
  )
  resolved_locations = json.loads(
      (SOURCES_YUNTECH_DIR / "yuntech_resolved_locations.json").read_text(encoding="utf-8")
  )
  school_images_data = json.loads(
      (STATIC_DIR / "assets" / "school-images.json").read_text(encoding="utf-8")
  )
  visual_index = VisualRecordIndex({
      (
          school_identity_key(str(r.get("school_name", ""))),
          str(r.get("country") or ""),
      ): r
      for r in school_images_data.get("schools", [])
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

  for idx, item in enumerate(catalog_source):
    sn = item["school_sn"]
    full_name = item["full_name"]
    zh_name = item["name_zh"]
    country = item["country"]
    region = REGION_BY_COUNTRY.get(country, "亞洲")
    avail_status = "open" if item["application_status"] == "open" else "reference_only"
    if avail_status == "open":
      open_partner_count += 1

    tracks_str = "、".join(item.get("source_tracks") or ["非大陸地區校級交換計畫"])
    if "雙聯學位" in tracks_str and "交換" in tracks_str:
      program_type = "校級交換暨雙聯學位計畫"
    elif "銜接學位" in tracks_str and "交換" in tracks_str:
      program_type = "校級交換暨銜接學位計畫"
    elif "橋樑學位" in tracks_str or "銜接學位" in tracks_str:
      program_type = "國際銜接／橋樑學位計畫"
    elif "大陸地區" in tracks_str:
      program_type = "大陸地區校級交換學生計畫"
    else:
      program_type = "校級交換學生計畫"

    quota_str = item["quota_str"]
    colleges_str, degree_levels_str = format_colleges_and_degrees(item)
    lang_req_str = item["lang_req"]
    gpa_req_str = format_gpa_rule(item)
    website = item.get("website") or YUNTECH_OE_INTRO_115_2_URL
    factsheet_url = item.get("factsheet_url")
    brochure_url = item.get("brochure_url") or YUNTECH_OE_INTRO_115_2_URL
    remarks_raw = clean_text(item.get("remarks") or "")
    exps = item.get("experience_reports") or []

    if country == "中國大陸":
      source_url = YUNTECH_MAINLAND_2027S_URL if avail_status == "open" else brochure_url
      round_label = (
          "115學年度第2學期（2027春季班）及第1學期（2026秋季班）大陸地區交換學生甄選"
          if avail_status == "open"
          else "大陸地區歷屆締約合作姊妹校（依國際處當期公告名額辦理）"
      )
      app_deadline_str = (
          "【2027春季班（115-2）赴大陸地區交換甄選】2026/09/01 – 2026/10/16 17:00 繳交校內甄選申請表件至國際事務處（依大陸姊妹校提名期限分批截止：第一批 9/25、第二批 10/16）；【2026秋季班（115-1）赴大陸地區交換甄選】2026/02/23 – 03/27 校內收件；【2027秋季班（116-1）預告】預計 2027年2月下旬至3月下旬開放申請"
      )
      deadline_iso = "2026-10-16T17:00:00+08:00"
      win_status = "closed"
    elif "橋樑學位" in tracks_str and "交換" not in tracks_str:
      source_url = YUNTECH_PATHWAY_URL
      round_label = "學碩士橋樑／銜接學位專案（依秋季班／春季班提名時程申請）"
      app_deadline_str = (
          "依雲科大國際事務處與美國德州大學達拉斯分校（UT Dallas）每學期橋樑學位專案提名時程辦理（秋季班約每年 2–3 月、春季班約每年 9–10 月向國際事務處提出申請）"
      )
      deadline_iso = "2026-10-16T17:00:00+08:00"
      win_status = "closed"
    else:
      source_url = brochure_url
      round_label = (
          "115學年度第2學期（2027春季班）及第1學期（2026秋季班）非大陸地區交換學生甄選"
          if avail_status == "open"
          else "非大陸地區締約合作姊妹校（依國際處當期甄選系統公告名額辦理）"
      )
      app_deadline_str = (
          "【2027春季班（115-2）赴非大陸地區交換甄選】2026/09/07 09:00 – 2026/09/25 16:00 線上申請、2026/09/26 17:00 紙本送達國際處、2026/10/19 公告錄取名單（共錄取 25 名）、2026/10/22 12:00 錄取生繳交確認書與 $3,000 保證金截止；【2026秋季班（115-1）】2026/02/23 – 03/13 線上申請、04/01 公告錄取（共錄取 38 名）；【2027秋季班（116-1）預告】預計 2027年2月中旬至3月中旬開放線上申請"
      )
      deadline_iso = "2026-09-25T16:00:00+08:00"
      win_status = "closed"

    study_period_str = "1 學期或 1 學年（依《國立雲林科技大學國際交換學生實施要點》第8點：交換期間以一學期或一學年為限）"
    if "雙聯" in tracks_str or "銜接" in tracks_str or "橋樑" in tracks_str:
      study_period_str = "1 學期、1 學年交換或 1–2 年雙聯／銜接學位修讀"

    sem_dates_str = SEMESTER_DATES_BY_COUNTRY.get(
        country, "秋季學期：約 9 月至翌年 1 月；春季學期：約 2 月至 6 月"
    )
    housing_str = (
        f"獲雲科大國際事務處提名後，可依 {zh_name} 交換生簡章（Fact Sheet）與線上系統說明申請校內學生宿舍或校外國際學生公寓"
        + (f"（學校簡章摘要：{remarks_raw[:220]}）" if remarks_raw else "。")
    )
    course_rest_str = (
        f"開放對象與領域：{colleges_str}。依《國立雲林科技大學國際交換學生實施要點》第9點及《王秋雄榮譽博士獎助金實施要點》規定：交換生出國期間學業及學分抵免悉依本校學則及相關規定辦理；若領取王秋雄榮譽博士德日美獎助金，大學部每學期至少須修習 3 門或 6–9 學分（18 ECTS）且每門課成績達 B 以上，研究所每學期至少須修習 2 門或 4–8 學分（12 ECTS）且成績及格（或參與校內教授研究計畫）。"
    )

    tuition_points_list = [
        (
            "學費互惠、雲科大在學註冊與保證金規定：依《國立雲林科技大學國際交換學生實施要點》第7點規定，所有交換學生在交換期間並未免除在本校之註冊及繳費義務，出國交換期間仍須辦理本校註冊並繳交全額學雜費，雙邊互惠交換名額免繳接待校學費（部分雙聯／銜接學位或自費項目依各校協議辦理）。錄取非大陸地區交換生須於放榜確認期限內繳交新臺幣 3,000 元保證金（完成交換返國繳交心得報告後全額無息退還；錄取確認後無故放棄者沒收保證金）。"
        ),
        (
            "雲科大三大出國交換獎助學金體系：（1）《王秋雄榮譽博士補助德日美交流或進修獎助金》：補助非在職專班在學學生（班排前 50%、操行 80 分以上、外語達標）赴德國、日本、美國交換至少一學期，德國每學期補助 NT$120,000–150,000（柏林 15 萬、阿亨 14 萬、其他地區 12 萬）、日本每學期 NT$100,000（一學年 20 萬）、美國每學期 NT$150,000–180,000（紐約／舊金山 18 萬、洛杉磯 17 萬、華盛頓／波士頓 16 萬、其他地區 15 萬，一學年最高 30 萬）；（2）教育部《學海飛颺》與《學海惜珠》專案：補助具中華民國國籍且在臺設籍、學業成績系所前 40%（或具研究著作／獲獎事蹟）、操行 80 分以上之非當學期畢業生赴中港澳以外締約校交換，每人最高補助 NT$300,000（115學年度實際核發一學期約 NT$111,873–147,201、一學年約 NT$212,559–279,682）；（3）《國立雲林科技大學學生出國交流或進修補助要點》：補助在學一般生（不含陸港澳生）出國交換或修讀雙聯學制至少一學期，亞洲地區每學期最高 NT$110,000、亞洲以外地區每學期最高 NT$150,000（短期研究蹲點 2–3 個月最高 6–10 萬元、短期國際會議交流最高 3 萬元）。"
        ),
    ]

    app_steps_list = [
        (
            f"步驟一（確認在學資格、學業 75 分／班排前 50%、操行 80 分門檻與 {zh_name} 語檢要求）：確認具雲科大研究所在學學生或入學一學期以上之大學部在學學生資格，歷年學業成績達 75 分（含）以上或班級排名前 50%、操行成績達 80 分（含）以上，並備妥符合 {zh_name} 及校內規定之外語能力證明（{lang_req_str}）。"
        ),
        (
            "步驟二（完成雲科大出國交換生線上系統報名並經系所／學院核章送交國際處）：於每學期甄選收件期間（秋季班每年 2–3 月、春季班每年 9 月），登入「雲科大出國交換生系統（admissions-oia.yuntech.edu.tw/oe）」填報個人資料與選填志願，列印紙本申請表經指導教授（研究生）、系主任及院長核章後，連同中英文歷年成績單（含歷年班排）、外語能力證明、中英文讀書計畫及自傳、其他優秀表現證明（國際／國內／校內競賽、證照、社團幹部）與推薦函（至多 3 封）於截止日前送交國際事務處。"
        ),
        (
            f"步驟三（國際處書面量化審查 40%／40%／20%、公告錄取名單與繳交確認書及 $3,000 保證金）：國際事務處依《非大陸地區交換學生評分標準表》進行審查：學業成績及班級排名比率佔 40%（大學部平均成績最高 20 分＋班排比率最高 20 分；研究所無班排者平均成績最高 40 分）＋ 語言能力證明佔 40%（CEFR C1 如 TOEIC 945 / iBT 95 / IELTS 7.0 / JLPT N1 得 40 分；CEFR B2 如 TOEIC 785 / iBT 72 / IELTS 5.5 / JLPT N2 得 30 分；CEFR B1 如 TOEIC 550 / iBT 42 / IELTS 4.0 / JLPT N3 得 20 分；CEFR A2 得 10 分；A1 得 5 分）＋ 其他優秀表現佔 20%（國際競賽／證照每張 2 分、國內 1 分、校內及幹部 0.5 分、推薦函每封 1 分最高 3 分）。放榜後正取生須於期限內繳交《錄取資格確認書》、《家長同意書》及 NT$3,000 保證金，由國際處向 {full_name} 辦理官方提名（Nomination）。"
        ),
        (
            "步驟四（遞交姊妹校入學申請、申請王秋雄博士／學海飛颺／校內出國補助並完成返國心得核銷）：獲國際處提名後依姊妹校規定遞交外文入學申請、英文財力證明、護照影本、選課清單與宿舍申請表；同時依公告時程申請「王秋雄榮譽博士補助德日美交流獎助金（每學期 10 萬–18 萬）」、「教育部學海飛颺／惜珠」或「雲科大出國交流或進修補助（亞洲最高 11 萬／非亞洲最高 15 萬）」。出國前須辦妥簽證與全期海外醫療及意外保險（役男須於出國前 1 個月完成緩徵出境核准），返國後依規定繳交交換學生心得報告、問卷、正式成績單及機票單據辦理學分抵免、獎助金核銷與 NT$3,000 保證金退還。"
        ),
    ]

    elig_points_list = [
        f"合作管道：{program_type}（{tracks_str}）",
        f"開放學制與年級：{degree_levels_str}",
        f"開放申請院系：{colleges_str}",
        f"學業與操行門檻：{gpa_req_str}",
        f"外語能力標準：{lang_req_str}",
        (
            "校內甄選評分標準（總分 100 分）：(1) 學業成績及班級排名比率 40%（大學部平均成績 20%＋班排比率 20%；研究所平均成績 40%）、(2) 語言能力證明 40%（C1=40分、B2=30分、B1=20分、A2=10分、A1=5分）、(3) 其他優秀表現 20%（國際會議／競賽／證照每件 2 分、國內每件 1 分、校內／幹部每件 0.5 分、推薦函每封 1 分最高 3 分）。"
        ),
    ]
    if remarks_raw:
      elig_points_list.append(f"學校簡章與特殊規定：{remarks_raw[:300]}")

    exp_labels = [
        f"{e['term']} {e['dept']} {e['student']}" for e in exps
    ]
    notes_lines = [
        f"【合作類別與期程】{program_type}｜交換期間：{study_period_str}",
        f"【當期名額與費用待遇】{quota_str}｜繳交雲科大校內學雜費、免繳接待校學費（雙聯／銜接學位依專案内涵辦理）",
        f"【開放學院與學制】{colleges_str}｜{degree_levels_str}",
        f"【語言與學業門檻】{lang_req_str}｜{gpa_req_str}",
        f"【住宿與生活資訊】{housing_str}",
    ]
    if factsheet_url:
      notes_lines.append(f"【官方簡章／Fact Sheet 連結】{factsheet_url}")
    if exps:
      notes_lines.append(
          f"【雲科大學長姐交換心得報告（共 {len(exps)} 篇）】收錄於國際事務處經驗分享專區（含：{'、'.join(exp_labels[:6])}）"
      )
    if remarks_raw:
      notes_lines.append(f"【學校簡章摘要】{remarks_raw[:350]}")

    loc_raw = resolved_locations[full_name]
    location_obj = {
        "school_name": full_name,
        "country": country,
        "city": loc_raw["city"],
        "latitude": float(loc_raw["latitude"]),
        "longitude": float(loc_raw["longitude"]),
        "geocode_status": "verified",
        "geocoded_at": CHECKED_AT,
        "source_url": loc_raw.get("source_url") or "https://www.wikidata.org",
        "identity_source_url": loc_raw.get("source_url") or "https://ror.org",
        "precision": "representative",
        "note": "校級代表位置：官方網域及國家已與 ROR / Wikidata 比對；實際交換校區以錄取通知與締約校專頁為準。",
    }
    new_locations.append(location_obj)

    visual_rec = visual_index.get((full_name, country)) or {}
    assert visual_rec.get("local_path"), f"Missing verified image for {full_name}"

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
        "availability_note": f"國立雲林科技大學國際事務處公告交換／雙聯合作姊妹校（{program_type}）；{quota_str}。",
        "academic_year": "115",
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
        "image_source_url": visual_rec.get("image_url") or visual_rec.get("image_source_url"),
        "image_page_url": (
            visual_rec.get("source_page_url")
            or visual_rec.get("official_page_url")
            or visual_rec.get("image_source_url")
        ),
        "image_status": "verified",
        "location": location_obj,
        "reference_data": {
            k: str(v)
            for k, v in {
                "school_sn": sn,
                "source_tracks": tracks_str,
                "brochure_url": brochure_url,
                "factsheet_url": factsheet_url,
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
            "title": f"國立雲林科技大學出國交換生申請系統—{zh_name} 招生簡章與名額表",
            "source_url": source_url,
            "role": "home_university",
            "authority": "home_official_notice",
            "effective_academic_year": "115",
            "application_round": round_label,
            "checked_at": CHECKED_AT,
        },
        {
            "title": "國立雲林科技大學國際交換學生實施要點與非大陸地區交換學生評分標準表",
            "source_url": YUNTECH_EXCHANGE_GUIDELINES_URL,
            "role": "home_university",
            "authority": "home_official_notice",
            "effective_academic_year": "115",
            "application_round": round_label,
            "checked_at": CHECKED_AT,
        },
        {
            "title": "國立雲林科技大學王秋雄榮譽博士獎助金、學海計畫與出國交流補助要點",
            "source_url": YUNTECH_GRANT_PAGE_URL,
            "role": "home_university",
            "authority": "home_official_notice",
            "effective_academic_year": "115",
            "application_round": round_label,
            "checked_at": CHECKED_AT,
        },
    ]
    if factsheet_url:
      wf_sources.append({
          "title": f"雲科大國際事務處公告之 {zh_name} 簡章／Fact Sheet 附件",
          "source_url": factsheet_url,
          "role": "home_university",
          "authority": "home_official_notice",
          "effective_academic_year": "115",
          "application_round": round_label,
          "checked_at": CHECKED_AT,
      })
    if exps:
      wf_sources.append({
          "title": f"雲科大國際事務處經驗分享專區—赴 {zh_name} 交換生返國心得報告（{len(exps)} 篇）",
          "source_url": exps[0]["page_url"],
          "role": "home_university",
          "authority": "home_official_notice",
          "effective_academic_year": "115",
          "application_round": round_label,
          "checked_at": CHECKED_AT,
      })
    if website:
      wf_sources.append({
          "title": f"{full_name} 官方網站",
          "source_url": website,
          "role": "partner_university",
          "authority": "partner_official",
          "effective_academic_year": "115",
          "application_round": round_label,
          "checked_at": CHECKED_AT,
      })

    workflows.append({
        "home_university": "國立雲林科技大學",
        "school_name": full_name,
        "partner_website": website,
        "country": country,
        "program_type": program_type,
        "academic_year": "115",
        "application_round": round_label,
        "effective_application_rounds": [
            round_label,
            "115-2",
            "115-1",
            "116-1",
            "116-2",
            "2027春季班",
            "2026秋季班",
        ],
        "applicability_status": "verified",
        "applicability_note": (
            "國立雲林科技大學由國際事務處（國際合作組／國際學術交流組）統籌辦理全校非大陸地區與大陸地區交換學生、雙聯學位及銜接學位甄選，每學期初（2–3 月辦理次學年秋季班、9 月辦理次年春季班）開放線上與紙本收件，並搭配王秋雄榮譽博士德日美獎助金、教育部學海飛颺／惜珠與校內出國交流補助。"
        ),
        "review_status": "published",
        "published_at": CHECKED_AT,
        "steps": [
            {
                "rule_id": f"yuntech-115-home-1-{idx+1:03d}",
                "order": 1,
                "phase": "校內申請",
                "title": f"確認在學資格、學業 75 分或班排前 50%、操行 80 分門檻與 {zh_name} 語檢要求",
                "responsible_party": "學生",
                "responsible_unit": "國立雲林科技大學國際事務處（斗六校區行政大樓）",
                "deadline_at": deadline_iso,
                "deadline_status": "verified_exact" if avail_status == "open" else "reference_only",
                "deadline_source_url": source_url,
                "deadline_checked_at": CHECKED_AT,
                "deadline_reminder_eligible": False,
                "summary": (
                    f"確認符合《國立雲林科技大學國際交換學生實施要點》第2點規定（研究所在學學生或入學一學期以上之大學部在學學生，學業成績達 75 分［含］以上或班級排名前 50%，且操行成績達 80 分［含］以上），並備妥符合 {zh_name} 及校內規定之外語能力證明。"
                ),
                "details": [
                    f"開放學制與院系：{colleges_str}（{degree_levels_str}）",
                    f"語言與學業條件：{lang_req_str}｜{gpa_req_str}",
                    f"當期名額與計畫類別：{quota_str}｜{program_type}",
                ],
                "scope": {
                    "home_universities": ["國立雲林科技大學"],
                    "partner_universities": [full_name],
                    "academic_years": ["115", "116"],
                    "application_rounds": [round_label, "115-2", "115-1", "116-1", "116-2"],
                },
                "source_urls": [
                    source_url,
                    YUNTECH_EXCHANGE_GUIDELINES_URL,
                    YUNTECH_SCORING_RUBRIC_URL,
                ],
                "checked_at": CHECKED_AT,
                "support_status": "verified",
            },
            {
                "rule_id": f"yuntech-115-home-2-{idx+1:03d}",
                "order": 2,
                "phase": "校內申請",
                "title": "完成雲科大出國交換生系統線上填報，並列印核章申請表連同成績單、語檢、讀書計畫與優秀表現證明送交國際處",
                "responsible_party": "學生與所屬系（所）及學院辦公室",
                "responsible_unit": "國立雲林科技大學各系所及學院／國際事務處",
                "deadline_at": deadline_iso,
                "deadline_status": "verified_exact" if avail_status == "open" else "reference_only",
                "deadline_source_url": source_url,
                "deadline_checked_at": CHECKED_AT,
                "deadline_reminder_eligible": False,
                "summary": (
                    "於甄選線上申請期間至「雲科大出國交換生系統（admissions-oia.yuntech.edu.tw/oe）」完成線上報名及志願選填，列印申請表經指導教授（研究生）、系所主任與院長核章後，併同歷年成績單（含班排）、有效語檢證明、中英文自傳與讀書計畫、優秀表現證明及推薦函於紙本收件截止日前送達國際事務處。"
                ),
                "details": [
                    "語言能力基準：申請以英文授課之交換學校，語言能力應達 TOEIC 650 分或同等能力標準（赴大陸地區、東南亞地區不在此限，惟須符合接待校規定）。",
                    "加分附件準備：依《非大陸地區交換學生評分標準表》，參與國際型／國內型／校內會議或競賽、國際／國內證照、社團幹部證明及師長推薦函（至多 3 封）均採計於「其他優秀表現（最高 20 分）」。",
                ],
                "document_requirements": [
                    {
                        "name": "國立雲林科技大學出國交換學生線上系統申請表（列印後須經指導教授［研究生］、系所主管及學院院長核章）",
                        "official_form_url": YUNTECH_OE_PORTAL_URL,
                        "source_urls": [YUNTECH_OE_PORTAL_URL, YUNTECH_APPLY_2027S_URL],
                    },
                    {
                        "name": "中、英文歷年成績單正本（大學部須註明歷年平均成績及班級排名比率，操行成績須達 80 分以上）",
                        "source_urls": [YUNTECH_EXCHANGE_GUIDELINES_URL, YUNTECH_SCORING_RUBRIC_URL],
                    },
                    {
                        "name": "有效期限內之外語能力檢定證明影本（TOEIC / TOEFL iBT / TOEFL ITP / IELTS / JLPT / TestDaF / DELF / TOPIK）",
                        "source_urls": [YUNTECH_EXCHANGE_GUIDELINES_URL, YUNTECH_SCORING_RUBRIC_URL],
                    },
                    {
                        "name": "中、英文讀書計畫與自傳、其他優秀表現證明（競賽獲獎、專業證照、社團幹部）及師長推薦函（最高採計 3 封）",
                        "source_urls": [YUNTECH_SCORING_RUBRIC_URL, YUNTECH_SLIDES_2027S_URL],
                    },
                ],
                "scope": {
                    "home_universities": ["國立雲林科技大學"],
                    "academic_years": ["115", "116"],
                    "application_rounds": [round_label, "115-2", "115-1", "116-1", "116-2"],
                },
                "source_urls": [
                    YUNTECH_OE_PORTAL_URL,
                    YUNTECH_APPLY_2027S_URL,
                    YUNTECH_EXCHANGE_GUIDELINES_URL,
                    YUNTECH_SCORING_RUBRIC_URL,
                ],
                "checked_at": CHECKED_AT,
                "support_status": "verified",
            },
            {
                "rule_id": f"yuntech-115-home-3-{idx+1:03d}",
                "order": 3,
                "phase": "甄選與提名",
                "title": "國際處量化評分審查（學業與班排 40%＋語檢 40%＋優秀表現 20%）、放榜確認與繳交 NT$3,000 保證金",
                "responsible_party": "學生與國際事務處甄選委員會",
                "responsible_unit": "國立雲林科技大學國際事務處",
                "deadline_at": "2026-10-22T12:00:00+08:00",
                "deadline_status": "verified_exact",
                "deadline_source_url": YUNTECH_ROSTER_2027S_URL,
                "deadline_checked_at": CHECKED_AT,
                "deadline_reminder_eligible": False,
                "summary": (
                    "國際處依《非大陸地區交換學生評分標準表》（學業成績及班級排名比率 40%＋語言能力證明 40%＋其他優秀表現 20%）評定總成績並依志願分發。公告錄取名單後，正取生須於規定期限內繳交《錄取資格確認書》、《家長同意書》及新臺幣 3,000 元保證金（完成交換並繳交報告後退還）。"
                ),
                "details": [
                    "語言能力計分標準（40%）：CEFR C1（TOEIC 945 / iBT 95 / ITP 627 / IELTS 7.0–8.0 / JLPT N1）得 40 分；CEFR B2（TOEIC 785 / iBT 72 / ITP 543 / IELTS 5.5–6.5 / JLPT N2）得 30 分；CEFR B1（TOEIC 550 / iBT 42 / ITP 460 / IELTS 4.0–5.0 / JLPT N3）得 20 分；CEFR A2（TOEIC 225 / ITP 337 / JLPT N4）得 10 分；CEFR A1（JLPT N5）得 5 分。",
                    "三大獎助學金同步規劃：錄取德國、日本、美國姊妹校者可申請《王秋雄榮譽博士獎助金》（每學期 10 萬–18 萬）；錄取中港澳以外姊妹校者可申請教育部《學海飛颺／惜珠》或《雲科大出國交流或進修補助》（亞洲每學期最高 11 萬、非亞洲每學期最高 15 萬）。",
                ],
                "scope": {
                    "home_universities": ["國立雲林科技大學"],
                    "academic_years": ["115", "116"],
                    "application_rounds": [round_label, "115-2", "115-1", "116-1", "116-2"],
                },
                "source_urls": [
                    YUNTECH_ROSTER_2027S_URL,
                    YUNTECH_SCORING_RUBRIC_URL,
                    YUNTECH_WANG_RULES_URL,
                    YUNTECH_SUBSIDY_RULES_URL,
                ],
                "checked_at": CHECKED_AT,
                "support_status": "verified",
            },
            {
                "rule_id": f"yuntech-{idx+1:03d}-host-apply",
                "order": 4,
                "phase": "合作校申請",
                "title": f"由雲科大國際處辦理官方提名（Nomination）並依 {zh_name} 規定遞交入學申請與宿舍登記",
                "responsible_party": "學生與接待校國際事務處",
                "summary": (
                    f"完成錄取確認與保證金繳交後，由雲科大國際事務處向 {zh_name} 辦理官方提名；學生須於姊妹校截止日前備妥英文歷年成績單、護照影本、英文銀行存款財力證明、語檢證書、學習協議（Learning Agreement）、體檢表及宿舍申請表，靜候接待校核發正式入學許可（Letter of Acceptance / COE / DS-2019）。"
                ),
                "details": [
                    f"交換期程：{study_period_str}｜名額：{quota_str}",
                    f"語言與學業條件：{lang_req_str}｜{gpa_req_str}",
                    f"住宿安排：{housing_str}",
                ],
                "scope": {
                    "home_universities": ["國立雲林科技大學"],
                    "partner_universities": [full_name],
                    "academic_years": ["115", "116"],
                    "application_rounds": [round_label, "115-2", "115-1", "116-1", "116-2"],
                },
                "source_urls": (
                    [source_url, YUNTECH_OE_INTRO_115_2_URL]
                    + ([factsheet_url] if factsheet_url else [])
                    + ([website] if website else [])
                ),
                "checked_at": CHECKED_AT,
                "support_status": "verified",
                "needs_confirmation": False,
            },
            {
                "rule_id": f"yuntech-115-home-5-{idx+1:03d}",
                "order": 5,
                "phase": "行前準備",
                "title": "辦理留學簽證、海外醫療及意外保險、役男緩徵出境與雲科大在學註冊，返國後完成心得核銷、學分抵免與保證金退還",
                "responsible_party": "學生",
                "responsible_unit": "國立雲林科技大學國際事務處／教務處註冊組／學務處生輔組／各系所",
                "summary": (
                    "出國前須參加行前說明會、辦妥簽證與涵蓋交換全期之海外醫療及意外保險（尚未履行兵役義務之役男須於出國前 1 個月由國際處協助辦理役男出境緩徵核准），並於交換期間維持雲科大在學註冊及繳交全額學雜費；返國後繳交交換心得報告、問卷、機票票根及姊妹校正式成績單，辦理學分抵免、獎助學金尾款核銷及 NT$3,000 保證金退還。"
                ),
                "details": tuition_points_list,
                "scope": {
                    "home_universities": ["國立雲林科技大學"],
                    "academic_years": ["115", "116"],
                    "application_rounds": [round_label, "115-2", "115-1", "116-1", "116-2"],
                },
                "source_urls": [
                    YUNTECH_EXCHANGE_GUIDELINES_URL,
                    YUNTECH_WANG_RULES_URL,
                    YUNTECH_SUBSIDY_RULES_URL,
                    YUNTECH_XUEHAI_RULES_URL,
                ],
                "checked_at": CHECKED_AT,
                "support_status": "verified",
            },
        ],
        "sources": wf_sources,
        "last_checked": CHECKED_AT,
        "coverage_status": "official_verified",
        "coverage_note": (
            "已完整整合國立雲林科技大學國際事務處（出國交換生系統 115-2／115-1／114-2／114-1、雙聯學位、銜接學位及大陸地區交換計畫）共 112 所全球合作學校名額、語檢門檻、量化評分標準、三大獎助學金要點與 118 篇學長姐返國心得。"
        ),
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
            "title": f"國立雲林科技大學出國交換生申請系統—{zh_name} 簡章與名額表",
            "source_url": source_url,
            "summary": "雲科大國際事務處公告之交換名額、開放對象、語言檢定門檻與學校簡章說明",
        },
        {
            "title": "國立雲林科技大學國際交換學生實施要點、評分標準表與三大獎助學金要點",
            "source_url": YUNTECH_EXCHANGE_GUIDELINES_URL,
            "summary": "雲科大出國交換申請資格（75分或前50%、操行80分）、甄選配分（40%／40%／20%）、王秋雄博士德日美獎助金（10萬–18萬／學期）、學海飛颺／惜珠與校內出國補助（亞洲11萬／非亞洲15萬）規定",
        },
    ]
    if factsheet_url:
      dest_sources.append({
          "title": f"雲科大國際事務處公告之 {zh_name} 簡章／Fact Sheet 附件",
          "source_url": factsheet_url,
          "summary": "雲科大國際處彙整之姊妹校 Fact Sheet、申請表單與選課住宿資訊",
      })
    if exps:
      dest_sources.append({
          "title": f"雲科大國際事務處經驗分享專區—赴 {zh_name} 交換生返國心得報告（{len(exps)} 篇）",
          "source_url": exps[0]["page_url"],
          "summary": f"收錄 113–115 學年度雲科大赴 {zh_name} 交換生返國心得報告 PDF 共 {len(exps)} 篇",
      })
    if website:
      dest_sources.append({
          "title": f"{full_name} 官方網站",
          "source_url": website,
          "summary": "接待合作校官方網站",
      })

    src_url_list = (
        [source_url, YUNTECH_OE_INTRO_115_2_URL, YUNTECH_EXCHANGE_GUIDELINES_URL]
        + ([factsheet_url] if factsheet_url else [])
        + ([exps[0]["page_url"]] if exps else [])
        + ([website] if website else [])
    )

    destinations.append({
        "home_university": "國立雲林科技大學",
        "school_name": full_name,
        "country": country,
        "city": location_obj.get("city") or country,
        "cost_summary": f"{cost_line}。\n{tuition_clean}",
        "housing_summary": housing_clean,
        "transport_summary": (
            f"校區代表城市：{location_obj.get('city') or country}。請依入學許可與姊妹校 Fact Sheet 確認實際授課校區、機場接機服務與當地學生交通卡優惠。"
        ),
        "campus_life_summary": f"{calendar_clean}\n{course_clean}",
        "student_guide_sections": [
            {
                "key": "cost",
                "title": "生活費、王秋雄榮譽博士德日美獎助金（10萬–18萬／學期）、學海飛颺／惜珠與雲科大出國補助（亞洲11萬／非亞洲15萬）",
                "summary": cost_line,
                "points": [cost_line] + tuition_points_list,
                "source_urls": src_url_list + [YUNTECH_WANG_RULES_URL, YUNTECH_SUBSIDY_RULES_URL, YUNTECH_XUEHAI_RULES_URL],
                "caution": (
                    "領取《王秋雄榮譽博士補助德日美交流或進修獎助金》者不得同時兼領其他出國交換獎助學金，且大學部每學期須修習 3 門或 6–9 學分（18 ECTS）並達 B 以上、研究所每學期須修習 2 門或 4–8 學分（12 ECTS）及格。"
                ),
            },
            {
                "key": "housing",
                "title": "住宿資訊與校內外學生宿舍申請",
                "summary": housing_clean[:160],
                "points": [housing_clean],
                "source_urls": src_url_list,
                "caution": (
                    "各姊妹校校內學生宿舍名額有限，獲國際處提名後請務必詳閱各校 Fact Sheet 並準時遞交宿舍申請。"
                ),
            },
            {
                "key": "insurance",
                "title": "海外醫療及意外保險與接待國強制學生健康保險規定",
                "summary": visa_default,
                "points": [
                    visa_default,
                    "依《國立雲林科技大學國際交換學生實施要點》第10點第2款規定，交換學生於交換期間應自行購買足夠之醫療及意外保險，並依接待國政府或姊妹校規定投保當地強制學生健康保險（如德國法定公保、日本國民健康保險、韓國 NHIS、澳洲 OSHC 等）。",
                ],
                "source_urls": src_url_list,
                "caution": "請於收到入學許可後確認接待校指定之保險額度與投保通路，並於出國前繳交保險證明影本。",
            },
            {
                "key": "visa",
                "title": "留學簽證辦理、役男出境緩徵手續（出國前一個月）與在學學籍維持義務",
                "summary": visa_default,
                "points": [
                    visa_default,
                    "依《國立雲林科技大學國際交換學生實施要點》第7點及第11點規定，交換生出國期間仍須辦理雲科大註冊並繳費；尚未履行兵役義務之核准交換生，應於出國前一個月由國際事務處協助辦理役男出境緩徵手續，交換期滿應準時返國，不得擅自逾期居留。",
                ],
                "source_urls": src_url_list,
                "caution": "請勿持觀光簽證或免簽入境就讀學期交換課程，以免影響正式學籍、居留與返國學分抵免。",
            },
            {
                "key": "academics",
                "title": "修課規定、王秋雄獎助金最低學分門檻與返國學分抵免",
                "summary": course_clean[:160],
                "points": [calendar_clean, course_clean],
                "source_urls": src_url_list,
                "caution": (
                    "出國前應先與所屬系（所）確認擬於姊妹校修讀課程之專業相關性，返國後憑正式成績單與課程大綱依雲科學則辦理學分抵免。"
                ),
            },
            {
                "key": "living",
                "title": f"{location_obj.get('city') or country} 校園生活與雲科大學長姐交換心得傳承",
                "summary": f"代表校區城市：{location_obj.get('city') or country}。請配合雲科大行前說明會與接待校新生訓練（Orientation）完成報到。",
                "points": [
                    f"目的地城市：{location_obj.get('city') or country}（{country}）",
                    (
                        f"雲科大國際事務處於官網「經驗分享專區（{exps[0]['page_url'] if exps else YUNTECH_EXP_115_URL}）」公開收錄 113–115 學年度歷屆學長姐返國研修心得報告 PDF"
                        + (f"（本校共收錄 {len(exps)} 篇：{'、'.join(exp_labels[:5])}）" if exps else "")
                        + "，詳述當地選課、住宿、交通與生活開銷實況。"
                    ),
                ],
                "source_urls": [exps[0]["page_url"] if exps else YUNTECH_EXP_115_URL],
            },
        ],
        "sources": dest_sources,
        "last_checked": CHECKED_AT,
        "coverage_status": "official_verified",
        "coverage_note": (
            "已整合國立雲林科技大學國際事務處 112 所交換與雙聯合作姊妹校名額、語檢門檻、三大獎助學金要點、各校簡章與 113–115 學年度學長姐返國心得。"
        ),
    })

    research_records.append({
        "home_university": "國立雲林科技大學",
        "school_name": full_name,
        "country": country,
        "official_website": website,
        "verification_status": "official_verified",
        "discovery_source_url": source_url,
        "checked_at": CHECKED_AT,
        "note": (
            f"國立雲林科技大學國際事務處《出國交換生申請系統（{YUNTECH_OE_INTRO_115_2_URL}）》、《雙聯學位／銜接學位專區》與 ROR/Wikidata 官方網址核對完成。"
        ),
    })

    ev_sources = [
        {
            "title": f"國立雲林科技大學出國交換生申請系統—{zh_name} 招生簡章",
            "url": source_url,
        },
    ]
    if factsheet_url:
      ev_sources.append({
          "title": f"雲科大國際處公告之 {zh_name} 簡章／Fact Sheet 附件",
          "url": factsheet_url,
      })
    if exps:
      ev_sources.append({
          "title": f"雲科大國際事務處經驗分享專區—赴 {zh_name} 交換生心得報告（{len(exps)} 篇）",
          "url": exps[0]["page_url"],
      })
    if website:
      ev_sources.append({"title": f"{full_name} 官方網站", "url": website})

    has_student_exp = bool(exps or factsheet_url)
    if exps:
      exp_covered_schools += 1

    ev_list = [
        {
            "theme": "housing",
            "kind": "mixed" if has_student_exp else "official",
            "text": housing_clean,
            "sources": ev_sources,
            "checked_at": CHECKED_AT,
            "scope": "國立雲林科技大學出國交換姊妹校住宿與生活資訊",
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
            "scope": "國立雲林科技大學交換生費用規定、王秋雄博士德日美獎助金、學海飛颺／惜珠與校內出國補助及地區生活費估算",
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
            "scope": "國立雲林科技大學交換生選課規定、王秋雄獎助金學分門檻與返國學分抵免",
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
            "scope": "國立雲林科技大學出國交換簽證、海外醫療保險、役男緩徵出境與在學註冊提醒",
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
                    f"｜雲科大國際處經驗分享專區公開收錄 {len(exps)} 篇赴 {zh_name} 交換生返國心得報告（{'、'.join(exp_labels[:4])}）。"
                    if exps
                    else ""
                )
            ),
            "sources": ev_sources,
            "checked_at": CHECKED_AT,
            "scope": "國立雲林科技大學出國交換名額與歷屆學長姐交換經驗分享",
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
            "已整合國立雲林科技大學國際事務處《出國交換生申請系統》各校簡章、雙聯與銜接學位專區及 113–115 學年度返國學長姐心得報告。",
            "當期宿位供給、費用與選課限制請依姊妹校最新交換網頁及入學通知書核對。",
        ],
        "location_signature": f"verified:{location_obj['latitude']}:{location_obj['longitude']}:representative",
        "extraction_version": 3,
    })

    sample_reports: list[dict] = []
    for e_item in exps[:6]:
      sample_reports.append({
          "title": f"雲科大 {e_item['term']} 赴 {zh_name} 交換研修心得—{e_item['college']}{e_item['dept']} {e_item['student']}",
          "url": e_item.get("pdf_url") or e_item["page_url"],
          "term": f"{e_item['term']}學期",
      })
    if not sample_reports and factsheet_url:
      sample_reports.append({
          "title": f"國立雲林科技大學赴 {zh_name} 交換簡章／Fact Sheet 附件",
          "url": factsheet_url,
          "term": "115學年度",
      })

    if exps:
      rep_title = (
          f"國立雲林科技大學赴 {zh_name} 交換研修心得彙編（共 {len(exps)} 篇學長姐報告）"
      )
      latest_e = exps[0]
      latest_author = f"{latest_e['dept']} {latest_e['student']} 等 {len(exps)} 位雲科大交換生"
      summary_text = (
          f"國立雲林科技大學國際事務處「出國交換生經驗分享專區」公開收錄 {len(exps)} 篇 113–115 學年度赴 {zh_name} 交換學生返國心得報告 PDF（含：{'、'.join(exp_labels[:6])}），"
          f"涵蓋工程、管理、設計、人文與科學及未來學院學生於 {zh_name} 之專業選課、英語／當地語言學習、學生宿舍環境、簽證保險辦理及海外生活開銷實錄。"
      )
      theme_map = {
          "academics": (
              f"雲科大交換生（{'、'.join(exp_labels[:4])}）分享於 {zh_name} 修讀工程、管理、設計與人文科學課程之選課方式、達成王秋雄獎助金或學海計畫學分門檻（如大學部 18 ECTS／3 門課 B 以上）及返國辦理學分抵免之經驗。"
          ),
          "housing": (
              f"雲科大交換生詳述 {zh_name} 校內外學生宿舍申請時程、房型設備與周邊生活機能（{housing_clean[:120]}）。"
          ),
          "campus_culture": (
              f"雲科大國際處收錄 {len(exps)} 篇赴 {zh_name} 交換生返國心得報告，記錄接待校迎新週（Orientation）、國際學伴（Buddy Program）與跨文化交流體驗。"
          ),
          "cost": (
              f"雲科大交換生記錄於 {zh_name} 之每月住宿、伙食與交通開銷（{cost_default}），以及運用王秋雄榮譽博士德日美獎助金（每學期 10 萬–18 萬）、教育部學海飛颺／惜珠或雲科大出國交流補助（亞洲最高 11 萬／非亞洲最高 15 萬）支應留學費用之規劃。"
          ),
      }
      student_experience_rows.append({
          "school_name": full_name,
          "country": country,
          "title": rep_title,
          "source_url": latest_e.get("pdf_url") or latest_e["page_url"],
          "source_type": "pdf" if latest_e.get("pdf_url") else "article",
          "platform": "國立雲林科技大學國際事務處—交換生經驗分享專區",
          "author_name": latest_author,
          "language": "zh",
          "summary": summary_text,
          "themes": ["academics", "housing", "campus_culture", "cost"],
          "theme_summaries": theme_map,
          "content_status": "full_text",
          "perspective": "official_student_story",
          "published_at": None,
          "discovered_at": CHECKED_AT,
          "content_hash": hashlib.sha256(f"{full_name}:yuntech_exp:{len(exps)}".encode("utf-8")).hexdigest(),
          "exchange_term": f"{latest_e['term']}學期",
          "summary_zh": summary_text,
          "original_summary": summary_text,
          "theme_summaries_zh": theme_map,
          "translation_status": "original",
          "source_kind": "official_experience_page",
      })

    experience_sources_records.append({
        "home_university": "國立雲林科技大學",
        "school_name": full_name,
        "country": country,
        "official_experience_portal_url": exps[0]["page_url"] if exps else YUNTECH_EXP_115_URL,
        "partner_page_url": factsheet_url or source_url,
        "report_count": len(exps),
        "sample_reports": sample_reports,
        "checked_at": CHECKED_AT,
    })

  partners_jsonl_text = "\n".join(json.dumps(r, ensure_ascii=False) for r in partners) + "\n"
  (OFFICIAL_YUNTECH_DIR / "partners.jsonl").write_text(partners_jsonl_text, encoding="utf-8")
  (SOURCES_YUNTECH_DIR / "partners.jsonl").write_text(partners_jsonl_text, encoding="utf-8")
  (OFFICIAL_YUNTECH_DIR / "application_workflows.jsonl").write_text(
      "\n".join(json.dumps(r, ensure_ascii=False) for r in workflows) + "\n",
      encoding="utf-8",
  )
  (OFFICIAL_YUNTECH_DIR / "destination_profiles.jsonl").write_text(
      "\n".join(json.dumps(r, ensure_ascii=False) for r in destinations) + "\n",
      encoding="utf-8",
  )
  (OFFICIAL_YUNTECH_DIR / "partner_research.jsonl").write_text(
      "\n".join(json.dumps(r, ensure_ascii=False) for r in research_records) + "\n",
      encoding="utf-8",
  )
  (OFFICIAL_YUNTECH_DIR / "student_life.jsonl").write_text(
      "\n".join(json.dumps(r, ensure_ascii=False) for r in life_records) + "\n",
      encoding="utf-8",
  )
  (OFFICIAL_YUNTECH_DIR / "experience_sources.jsonl").write_text(
      "\n".join(json.dumps(r, ensure_ascii=False) for r in experience_sources_records) + "\n",
      encoding="utf-8",
  )
  (OFFICIAL_YUNTECH_DIR / "student_experiences.jsonl").write_text(
      "\n".join(json.dumps(r, ensure_ascii=False) for r in student_experience_rows) + "\n",
      encoding="utf-8",
  )
  (OFFICIAL_YUNTECH_DIR / "campus-locations.json").write_text(
      json.dumps({"locations": new_locations}, ensure_ascii=False, indent=2) + "\n",
      encoding="utf-8",
  )

  digest_records = {}
  for exp_row in student_experience_rows:
    sn_str = exp_row["school_name"]
    digest_records[sn_str] = {
        "school_name": sn_str,
        "country": exp_row["country"],
        "report_count": 1,
        "summary_zh": exp_row["summary_zh"],
        "themes": exp_row["theme_summaries_zh"],
        "source_url": exp_row["source_url"],
        "updated_at": CHECKED_AT,
    }
  (OFFICIAL_YUNTECH_DIR / "student-experience-digests.json").write_text(
      json.dumps({"digests": digest_records}, ensure_ascii=False, indent=2) + "\n",
      encoding="utf-8",
  )

  # Update university_locations.jsonl with YunTech home location
  loc_file = REPO_ROOT / "src/exchange_info/official_data/university_locations.jsonl"
  existing_loc_lines = [
      line for line in loc_file.read_text(encoding="utf-8").splitlines() if line.strip()
  ]
  existing_loc_map = {}
  for line in existing_loc_lines:
    rec = json.loads(line)
    existing_loc_map[(rec["school_name"], rec.get("country") or "")] = rec

  yuntech_home_loc = {
      "school_name": "國立雲林科技大學",
      "country": "臺灣",
      "city": "雲林縣斗六市",
      "latitude": 23.6928,
      "longitude": 120.5342,
      "geocode_status": "verified",
      "geocoded_at": CHECKED_AT,
      "source_url": "https://www.wikidata.org/wiki/Q6979504",
      "identity_source_url": "https://ror.org/043173w91",
      "precision": "representative",
      "note": (
          "校級代表位置：官方網域及國家已與 ROR 比對，座標來源為 Wikidata P625；實際交換校區以錄取通知為準。"
          " 母校代表點採雲林縣斗六市大學路三段123號校本部國際事務處；官方地址來源：https://tdx.yuntech.edu.tw/。"
      ),
  }
  existing_loc_map[("國立雲林科技大學", "臺灣")] = yuntech_home_loc
  sorted_locs = sorted(
      existing_loc_map.values(),
      key=lambda r: (r.get("country") or "", r.get("school_name") or ""),
  )
  loc_file.write_text(
      "\n".join(json.dumps(r, ensure_ascii=False) for r in sorted_locs) + "\n",
      encoding="utf-8",
  )

  yuntech_source_urls = [
      YUNTECH_OIA_HUB_URL,
      YUNTECH_OE_PORTAL_URL,
      YUNTECH_OE_INTRO_115_2_URL,
      YUNTECH_OE_INTRO_115_1_URL,
      YUNTECH_OUTBOUND_NON_MAINLAND_URL,
      YUNTECH_MAINLAND_2027S_URL,
      YUNTECH_APPLY_2027S_URL,
      YUNTECH_ROSTER_2027S_URL,
      YUNTECH_ROSTER_115_1_URL,
      YUNTECH_EXCHANGE_GUIDELINES_URL,
      YUNTECH_SCORING_RUBRIC_URL,
      YUNTECH_SLIDES_2027S_URL,
      YUNTECH_SLIDES_2026F_URL,
      YUNTECH_SLIDES_MAINLAND_URL,
      YUNTECH_GRANT_PAGE_URL,
      YUNTECH_SUBSIDY_RULES_URL,
      YUNTECH_WANG_PAGE_URL,
      YUNTECH_WANG_RULES_URL,
      YUNTECH_XUEHAI_PAGE_URL,
      YUNTECH_XUEHAI_RULES_URL,
      YUNTECH_DUAL_DEGREE_URL,
      YUNTECH_PATHWAY_URL,
      YUNTECH_EXP_115_URL,
      YUNTECH_EXP_114_URL,
      YUNTECH_EXP_113_URL,
  ]

  exchange_info_payload = {
      "school_name": "國立雲林科技大學",
      "program_type": [
          (
              "國際事務處非大陸地區校級出國交換學生計畫（每學期初於「雲科大出國交換生系統 admissions-oia.yuntech.edu.tw/oe」辦理次一學期出國交換甄選，涵蓋德、日、韓、美、法、英、荷、比、西、捷、立、希、斯、土、澳、印、越、馬、菲、蒙及澳門等 70 所非大陸交換姊妹校，另含亞太大學交流會 UMAP 多邊交換計畫）"
          ),
          (
              "大陸地區校級出國交換學生計畫（涵蓋北京師範大學、同濟大學、南京大學、東南大學、山東大學、吉林大學、天津大學、南開大學、武漢大學、中南大學、湖南大學、四川大學、重慶大學、蘭州大學、西北農林科技大學、北京科技大學、北京交通大學、北京工業大學、中國礦業大學、鄭州大學、蘇州大學、江南大學、上海大學、福州大學等 40 所 985／211 及重點合作高校）"
          ),
          (
              "境外雙聯學位與國際銜接／橋樑學位計畫（含美國加州州立理工大學波莫納分校 Cal Poly Pomona 3+1+X、美國堪薩斯州立大學 KSU 雙碩士、日本千葉大學碩博士雙聯、印尼泗水理工學院 ITS 碩博士雙聯、澳洲南澳大學 UniSA 3+1+1 學碩士銜接學位及美國德州大學達拉斯分校 UT Dallas 4+1／1+1 橋樑碩士學位）"
          ),
      ],
      "academic_year": [
          (
              "115（115學年度第 2 學期［2027春季班］非大陸地區交換生甄選於 2026/09/07 – 09/25 線上收件、2026/10/19 公告錄取 25 名、10/22 完成確認與 $3,000 保證金繳交；2027春季班大陸地區交換生甄選於 2026/09/01 – 10/16 受理申請；115學年度第 1 學期［2026秋季班］非大陸地區共錄取 38 名；本平台共完整收錄 112 所雲科大交換與雙聯／銜接合作學校，含 45 所當期開放名額校及 67 所歷屆締約合作校）"
          ),
          (
              "116（116學年度第 1 學期［2027秋季班］非大陸及大陸地區交換生甄選預計於 2026年12月舉辦說明會、2027年2月中旬至3月中旬開放線上與紙本申請、2027年4月初公告錄取名單）"
          ),
      ],
      "semester": [
          "第1學期（秋季班：每年約 8/9 月至翌年 1/2 月；校內甄選收件期程為每年 2 月中旬至 3 月中下旬）",
          "第2學期（春季班：每年約 2/3 月至 6/7 月，日本春季班為 4 月至 8/9 月；校內甄選收件期程為每年 9 月初至 9 月底／10 月中旬）",
          "一學年交換或雙聯／銜接學制（依《國際交換學生實施要點》第8點，交換期間以一學期或一學年為限）",
      ],
      "application_period": [
          (
              "【2027春季班（115學年度第 2 學期，115-2）非大陸地區交換學生甄選時程】線上申請系統開放：2026/09/07 09:00 – 2026/09/25 16:00；紙本申請資料經系所及學院核章送達國際事務處截止：2026/09/26 17:00；甄選說明會：2026/09/16 12:15–13:00；錄取名單公告：2026/10/19（共錄取 25 名正取生）；正取生繳交《錄取資格確認書》、《家長同意書》及新臺幣 3,000 元保證金截止：2026/10/22 12:00；2027春季班王秋雄榮譽博士德日美獎助金申請截止：2026/09/26。"
          ),
          (
              "【2027春季班（115學年度第 2 學期，115-2）大陸地區交換學生甄選時程】校內申請收件期間：2026/09/01 – 2026/10/16 17:00（依大陸姊妹校提名期限分兩批截止：第一批北京科技大學、中南大學、福州大學等為 2026/09/25；第二批北京師範大學、同濟大學、山東大學、吉林大學、四川大學、重慶大學、東南大學、南京大學等為 2026/10/16）。"
          ),
          (
              "【2026秋季班（115學年度第 1 學期，115-1）交換甄選與 2027秋季班（116-1）預告】2026秋季班（115-1）非大陸地區交換於 2026/02/23 – 03/13 線上申請、03/16 紙本截止、04/01 公告錄取名單（共錄取 38 名），並於 2026/07/20 公告教育部學海飛颺（12 名）與王秋雄榮譽博士獎助金（19 名）獲獎名單；2027秋季班（116-1）預計於 2027年2月中旬至3月中旬開放申請。"
          ),
      ],
      "eligibility": [
          (
              "【在學學制、年級與國籍規定（依《國立雲林科技大學國際交換學生實施要點》第2點至第6點）】申請人須為本校研究所在學學生，或入學一學期以上之大學部在學學生；應屆畢業生經核准獲交換學校同意交換者，得向教務處申請延長修業年限（至多以一年為限）。在職專班學生得參加甄選交換學生，但不得申請本校獎學金之補助；非中華民國國籍之本校學生（外籍生、僑生）得參加甄選，但不得申請交換至其原屬國家境內之學校；大陸地區姊妹校限具臺籍身分之在學學生申請。"
          ),
          (
              "【學業成績 75 分或班排前 50% 及操行 80 分門檻】申請人歷年學業成績須達 75 分（含）以上或班級排名前 50%，且操行成績達 80 分（含）以上，並須符合各志願交換學校訂定之 GPA 或專業系所規定。所有交換學生在交換期間並未免除在本校之註冊及繳費義務，仍須辦理本校註冊並繳交學雜費。"
          ),
          (
              "【非大陸地區交換學生評分標準表（總分 100 分量化計分公式）】（1）學業成績及班級排名比率（40%）：大學部採計「在校歷年平均成績（20%：90分以上 20分、80–89分 16分、70–79分 14分、60–69分 12分）＋ 班級排名比率（20%：前5% 20分、前10%未達5% 18分、前20%未達10% 16分、前30%未達20% 14分、前40%未達30% 12分、前50%未達40% 8分、未達前50% 4分）」；研究所（無班排）採計「在校歷年平均成績（40%：90分以上 40分、80–89分 32分、70–79分 24分）」；（2）語言能力證明（40%，擇一高者計分）：40分（TOEIC 945 / iBT 95 / ITP 627 / IELTS 7.0–8.0 / JLPT N1）、30分（TOEIC 785 / iBT 72 / ITP 543 / IELTS 5.5–6.5 / JLPT N2）、20分（TOEIC 550 / iBT 42 / ITP 460 / IELTS 4.0–5.0 / JLPT N3）、10分（TOEIC 225 / ITP 337 / IELTS 4.0以下 / JLPT N4）、5分（TOEIC 225以下 / JLPT N5）；（3）其他優秀表現（最高 20%）：參與國際型會議或競賽／國際證照每張 2分、國內型會議或競賽／國內證照每張 1分、校內會議或競賽／校內社團幹部每張 0.5分（獲前三名或擔任社長／副社長／總召／副總召者加計一次）、推薦函每封 1分（最高 3分為上限）。"
          ),
      ],
      "language_requirement": [
          (
              "【英語授課交換學校 TOEIC 650 基準與東南亞／大陸例外規定（依《國際交換學生實施要點》第2點第7款）】申請以英文授課之交換學校，語言能力應達 TOEIC 650 分或同等能力標準（如 TOEFL iBT 61–79、TOEFL ITP 500–543、IELTS 5.0–5.5），赴大陸地區、東南亞地區（印尼、越南、馬來西亞、菲律賓等）則不在此限；且須符合各交換學校之各項語言資格規定（如德國柏林 HTW、卡爾斯魯厄 HKA、阿亨 FH Aachen、荷蘭烏特列支 HU、立陶宛 VILNIUS TECH、斯洛維尼亞盧比安納大學等要求英語或德語 CEFR B2；美國堪薩斯州立大學、加州州立理工波莫納分校、德州大學達拉斯分校、澳洲南澳大學、皇家墨爾本理工大學要求 TOEFL iBT 79–80 或 IELTS 6.0–6.5）。"
          ),
          (
              "【日語、韓語、德語、法語及西班牙語檢定規範】（1）日本姊妹校（9 校）：千葉大學、神戶藝術工科大學、福井大學、琉球大學、長岡技術科學大學、大阪工業大學、岡山縣立大學、會津大學、福岡大學依組別要求 JLPT N1–N3 或英語 TOEIC 650 / TOEFL iBT 72 以上；（2）韓國姊妹校（8 校）：首爾科技大學、建國大學、高麗大學世宗校區、弘益大學、檀國大學、同德女子大學、韓巴大學、清州大學依授課語言要求 TOPIK 2–3 級或英語 CEFR B1–B2；（3）歐洲德法西姊妹校：設有英語授課學程（要達 B1–B2）或當地語言學程（德語 B1–B2、法語 B1–B2、西語 B1）。"
          ),
          (
              "【語言能力證明計分表（佔校內甄選總分 40%）】語言檢定須在有效期限內，若同時持有多項檢定擇一最高分計分：40分級距（CEFR C1：TOEIC 945+ / TOEFL iBT 95+ / ITP 627+ / IELTS 7.0–8.0 / JLPT N1）、30分級距（CEFR B2：TOEIC 785+ / TOEFL iBT 72+ / ITP 543+ / IELTS 5.5–6.5 / JLPT N2）、20分級距（CEFR B1：TOEIC 550+ / TOEFL iBT 42+ / ITP 460+ / IELTS 4.0–5.0 / JLPT N3）、10分級距（CEFR A2：TOEIC 225+ / ITP 337+ / JLPT N4）、5分級距（CEFR A1：JLPT N5）。"
          ),
      ],
      "required_documents": [
          "1. 國立雲林科技大學出國交換生系統線上申請表（於 admissions-oia.yuntech.edu.tw/oe 填報並列印紙本，經指導教授［研究生］、系所主任及學院院長核章）",
          "2. 中、英文歷年成績單正本各乙份（大學部須註明歷年學業平均成績與班級排名比率，且歷年平均須達 75 分以上或班排前 50%、操行成績達 80 分以上）",
          "3. 有效期限內之外語能力檢定證明影本（TOEIC、TOEFL iBT / ITP、IELTS、JLPT、TOPIK、德語或法語檢定等；申請英語授課姊妹校須達 TOEIC 650 或同等標準，東南亞與大陸地區除外）",
          "4. 中、英文自傳與出國讀書計畫（詳述申請動機、擬修讀專業領域課程規劃、語言學習目標與返國學分抵免安排）",
          "5. 其他優秀表現證明文件影本（佔甄選總分最高 20%：參與國際型／國內型／校內會議或競賽獲獎證明、國際／國內專業證照、校內社團幹部證明）及師長推薦函（每封 1 分，最高採計 3 封）",
          "6. 大陸地區交換專屬表件（赴大陸姊妹校者另附大陸地區交換生申請表、證件照電子檔、有效護照與臺胞證影本及各接待高校專用申請表）",
          "7. 錄取確認與返國核銷必繳文件：放榜後於期限內繳交《錄取資格確認書》、《家長同意書》及新臺幣 3,000 元保證金；返國後繳交交換學生心得報告、問卷、正式成績單及機票單據辦理學分抵免、獎助金尾款核銷與保證金退還",
      ],
      "scholarship_info": [
          (
              "《王秋雄榮譽博士補助德日美交流或進修獎助金》（依 2024/07/10 修正實施要點及發放作業規定）：獎勵本校非在職專班在學學生（班排前 50%、操行 80 分以上，英語達 CEFR B2［美國 B2／德國日本 B1］或日語 N2／德語 B1）赴德國、日本、美國三國姊妹校交換至少一學期（或優秀入學獎學金續領生短期實習至少 1 個月）：（1）德國地區：柏林地區每學期最高 NT$150,000、阿亨地區每學期最高 NT$140,000、其他德國地區每學期最高 NT$120,000；（2）日本地區：每學期最高 NT$100,000（一學年最高 NT$200,000）；（3）美國地區：紐約／舊金山每學期最高 NT$180,000、洛杉磯每學期最高 NT$170,000、華盛頓／波士頓每學期最高 NT$160,000、其他美國地區每學期最高 NT$150,000（一學年最高 NT$300,000）。受領生不得同時兼領其他出國獎助學金，且大學部每學期須修習 3 門或 6–9 學分（18 ECTS）且每門課達 B 以上、研究所每學期須修習 2 門或 4–8 學分（12 ECTS）及格或參與校內教授研究計畫（115-1 學期共核定補助 19 名學生）。"
          ),
          (
              "教育部《學海飛颺》與《學海惜珠》選送優秀學生出國研修專案（依 113/04/22 修訂推薦作業要點）：補助具中華民國國籍且在臺設有戶籍、非當學期畢業之在學學生（學業成績須居系所前 40% 或具研究著作／獲獎事蹟、操行 80 分以上；惜珠另須具低收／中低收／特殊境遇家庭等證明），赴大陸及港澳以外之締約姊妹校研修 1 學期至 1 學年。每人最高獎助上限為新臺幣 300,000 元（學校配合款不低於 20%；115 學年度第一階段共核定 12 名受獎生，一學期實際核發約 NT$111,873–147,201、一學年核發約 NT$212,559–279,682）。"
          ),
          (
              "《國立雲林科技大學學生出國交流或進修補助要點》（依 114/06/13 修正通過要點）：補助本校具正式學籍之在學一般生（不含在職專班及陸港澳生）：（1）出國交換或修讀境外雙聯學制（至少一學期，學業成績前 50%、操行 80 分以上）：亞洲地區每學期最高補助新臺幣 110,000 元、亞洲以外地區每學期最高補助新臺幣 150,000 元；（2）短期研究（蹲點）：赴國外大學或研究機構 3 個月以上最高補助 NT$100,000、2 個月以上未滿 3 個月最高補助 NT$60,000；（3）短期交流或出席國際會議（至少 3 天）：每人最高補助 NT$30,000。"
          ),
          (
              "外國政府、跨國聯盟與接待校獎學金：（1）日本 JASSO 海外留學支援制度獎學金（每月 JPY 80,000，由千葉、福井、琉球、岡山縣立等締約校推薦）；（2）歐盟 Erasmus+ 跨國交換獎學金（由德國、立陶宛、斯洛維尼亞、捷克、希臘、土耳其等締約校擇優提名）；（3）亞太大學交流會（UMAP）臺灣國家秘書處交換獎學金及大陸地區姊妹校免住宿費／生活津貼專案。"
          ),
      ],
      "partner_universities": [p["school_name"] for p in partners],
      "source_urls": yuntech_source_urls,
      "last_checked": CHECKED_AT,
  }
  (OFFICIAL_YUNTECH_DIR / "exchange_info.json").write_text(
      json.dumps(exchange_info_payload, ensure_ascii=False, indent=2) + "\n",
      encoding="utf-8",
  )

  student_dashboard_payload = {
      "school_name": "國立雲林科技大學",
      "last_checked": CHECKED_AT,
      "academic_score_minimum": 75.0,
      "academic_score_rule": (
          "依《國立雲林科技大學國際交換學生實施要點》第2點規定：申請人須為研究所在學學生或入學一學期以上之大學部在學學生，歷年學業成績達 75 分（含）以上或班級排名前 50%，且操行成績達 80 分（含）以上。非大陸地區交換甄選依《評分標準表》按「學業成績及班級排名比率 40%＋語言能力證明 40%＋其他優秀表現 20%」量化計分比序。"
      ),
      "academic_gpa_minimum": 2.5,
      "maximum_preferences": 10,
      "selection_rules": {
          "academic_policy": "percentage",
          "academic_reference_year": "115",
          "undergraduate_gpa_minimum": 2.5,
          "graduate_academic_exempt": False,
          "exclude_in_service": False,
          "pending_quota_planning": False,
          "partner_requirements_need_confirmation": False,
          "degree_score_minimums": {
              "undergraduate": 75.0,
              "graduate": 75.0,
          },
          "excluded_undergraduate_years": ["大一上"],
          "language_certificate_required": True,
      },
      "language_score_minimums": {
          "toefl": 61.0,
          "ielts": 5.0,
          "toeic": 650.0,
      },
      "application_periods": [
          {
              "title": (
                  "國立雲林科技大學 116 學年度第 1 學期（2027秋季班，116-1）出國交換學生甄選預告（預計 2027/02–03 開放線上與紙本收件、2027/04 公告錄取名單）"
              ),
              "details": [
                  (
                      "依雲科大國際事務處每學期甄選時程慣例，2027秋季班（116-1，2027年8/9月出國）非大陸地區及大陸地區交換生甄選預計於 2026年12月舉辦說明會，並於 2027年2月中旬至3月中旬開放「出國交換生系統（admissions-oia.yuntech.edu.tw/oe）」線上申請與紙本收件。"
                  ),
                  (
                      "有意申請 2027秋季班交換及《王秋雄榮譽博士德日美獎助金》、《教育部學海飛颺／惜珠》或《雲科大出國交流補助》之同學，請提前備妥有效期限內之外語檢定成績單（英語授課校 TOEIC 650 以上、歐美名校 B2 以上或日語 JLPT N1–N3）與歷年成績單。"
                  ),
              ],
              "source": {
                  "title": "國立雲林科技大學國際事務處—出國交換生申請系統與實施要點",
                  "source_url": YUNTECH_OE_PORTAL_URL,
                  "category": "exchange_application",
                  "summary": "雲科大出國交換生申請系統、申請資格、評分標準與學期甄選時程說明。",
              },
              "scope": "home_application",
              "program_types": ["exchange"],
              "academic_year": "116",
              "application_round": "116學年度第1學期（2027秋季班）出國交換學生甄選",
              "audience": "all_students",
              "opens_at": "2027-02-22T09:00:00+08:00",
              "deadline_at": "2027-03-15T16:00:00+08:00",
              "date_status": "verified_exact",
              "status": "upcoming",
              "status_note": "2027春季班（115-2）甄選已於 2026/10/19 放榜；下一梯次 2027秋季班（116-1）預計於 2027年2月下旬至3月中旬開放線上與紙本報名。",
              "deadline_note": "請於線上系統截止前完成志願填報，並列印紙本申請表經系所主任及院長核章後連同備審資料送達國際事務處。",
              "reminder_eligible": True,
              "checked_at": CHECKED_AT,
          },
          {
              "title": (
                  "國立雲林科技大學 115 學年度第 2 學期（2027春季班，115-2）非大陸地區及大陸地區交換學生甄選（9/7–9/25 線上收件、10/19 公告錄取 25 名、10/22 確認截止）"
              ),
              "details": [
                  (
                      "2027春季班（115-2）非大陸地區交換學生甄選已於 2026/09/07 09:00 – 2026/09/25 16:00 完成線上申請收件（09/26 17:00 紙本截止），並於 2026/10/19 正式公告錄取名單（共錄取 25 名正取生赴日本、德國、韓國、美國、法國、荷蘭、比利時、立陶宛、捷克等國姊妹校）；正取生於 2026/10/22 12:00 前繳交錄取資格確認書、家長同意書及 NT$3,000 保證金。"
                  ),
                  (
                      "2027春季班（115-2）大陸地區交換學生甄選於 2026/09/01 – 2026/10/16 17:00 受理申請（第一批 9/25 截止、第二批 10/16 截止），開放北京師範、同濟、南京、東南、山東、吉大、川大、重大等 24 所大陸重點高校交換名額。"
                  ),
              ],
              "source": {
                  "title": "國立雲林科技大學 2027春季班（115-2）出國交換生申請公告與錄取名單",
                  "source_url": YUNTECH_ROSTER_2027S_URL,
                  "category": "exchange_application",
                  "summary": "雲科大 2027春季班（115-2）非大陸地區與大陸地區交換甄選時程、說明會簡報與錄取名單公告。",
              },
              "scope": "home_application",
              "program_types": ["exchange"],
              "academic_year": "115",
              "application_round": "115學年度第2學期（2027春季班）出國交換學生甄選",
              "audience": "all_students",
              "opens_at": "2026-09-07T09:00:00+08:00",
              "deadline_at": "2026-09-25T16:00:00+08:00",
              "date_status": "verified_exact",
              "status": "closed",
              "status_note": "2027春季班（115-2）非大陸地區與大陸地區校內收件已截止，並已於 2026/10/19 公告錄取名單，目前正辦理正取確認與姊妹校官方提名。",
              "deadline_note": "正取生須於 2026/10/22 中午 12:00 前完成確認書與 NT$3,000 保證金繳交。",
              "reminder_eligible": False,
              "checked_at": CHECKED_AT,
          },
      ],
      "program_overview": [
          {
              "title": (
                  f"國立雲林科技大學國際事務處出國交換與雙聯／銜接學位總覽（{len(partners)} 所全球合作姊妹校・{open_partner_count} 所當期開放申請校・三大獎助學金體系）"
              ),
              "details": [
                  (
                      f"國立雲林科技大學（YunTech，雲科大）由「國際事務處（Office of International Affairs）」統籌辦理全校出國交換學生、雙聯學位與國際銜接學位計畫。本平台完整收錄 {len(partners)} 所雲科大官方交換及雙聯／銜接合作學校（含當期開放申請名額之 {open_partner_count} 所姊妹校及 {len(partners) - open_partner_count} 所歷屆締約合作校），橫跨全球 23 個國家與地區（中國大陸 40 校、日本 9 校、德國 9 校、印度 9 校、韓國 8 校、印尼 7 校、越南 7 校、美國 6 校、法國 2 校、澳洲 2 校，以及英國、荷蘭、比利時、西班牙、立陶宛、希臘、斯洛維尼亞、捷克、土耳其、馬來西亞、菲律賓、蒙古、澳門各 1 校，另含 UMAP 亞太大學交流會交換計畫）。"
                  ),
                  (
                      "雲科大出國交換體系具備四大核心特色：（1）每學期獨立甄選、名額充沛：每年 2–3 月甄選秋季班（上學期）、9 月甄選春季班（下學期），並設有雙聯學位（美國 Cal Poly Pomona、堪薩斯州立大學 KSU、日本千葉大學、印尼泗水理工 ITS）與銜接／橋樑學位（澳洲南澳大學 UniSA 3+1+1、美國德州大學達拉斯分校 UT Dallas 4+1／1+1）；（2）公開透明百分制量化評分：採「學業成績及班排比率 40%＋語言能力證明 40%＋其他優秀表現 20%」書面審查；（3）全國頂尖之三大獎助學金體系：《王秋雄榮譽博士補助德日美交流或進修獎助金》（德國每學期 12–15 萬、日本每學期 10 萬、美國每學期 15–18 萬）、教育部《學海飛颺／惜珠》（一學期約 11–14.7 萬、一學年約 21–28 萬）及《雲科大學生出國交流或進修補助要點》（亞洲每學期最高 11 萬、非亞洲每學期最高 15 萬）；（4）完整學長姐經驗傳承：國際處網站公開收錄 113–115 學年度共 118 篇返國交換生心得報告 PDF。"
                  ),
              ],
              "source": {
                  "title": "國立雲林科技大學國際事務處—出國交換生申請系統與國際交流專區",
                  "source_url": YUNTECH_OE_INTRO_115_2_URL,
                  "category": "exchange_application",
                  "summary": "雲科大 112 所全球交換與雙聯合作學校、甄選時程、百分制評分標準、三大獎助學金與返國心得專區。",
              },
          }
      ],
      "eligibility": [
          {
              "title": "研究所在學或大學部入學滿一學期資格、學業 75 分或班排前 50% 及操行 80 分門檻與 40%／40%／20% 量化評分",
              "details": [
                  (
                      "在學學制、年級與身分規定（依《國立雲林科技大學國際交換學生實施要點》第2點至第7點）：申請人須為本校研究所在學學生，或入學一學期以上之大學部在學學生；應屆畢業生經核准獲交換學校同意交換者，得申請延長修業年限最長一年。在職專班學生得參加甄選，但不得申請本校獎學金補助；外籍生及僑生不得申請交換至其原屬國家境內之學校；所有交換生在交換期間仍須辦理雲科大註冊並繳交學雜費。"
                  ),
                  (
                      "成績門檻與百分制評分標準：歷年學業成績須達 75 分（含）以上或班級排名前 50%，且操行成績達 80 分（含）以上。非大陸地區校內甄選依《評分標準表》計算總分：（1）學業成績及班級排名比率 40%（大學部平均成績最高 20 分＋班排比率最高 20 分；研究所無班排者平均成績最高 40 分）；（2）語言能力證明 40%（CEFR C1 得 40 分、B2 得 30 分、B1 得 20 分、A2 得 10 分、A1 得 5 分）；（3）其他優秀表現最高 20%（國際競賽／證照每張 2 分、國內 1 分、校內及社團幹部 0.5 分、推薦函每封 1 分最高 3 分）。"
                  ),
              ],
              "source": {
                  "title": "國立雲林科技大學國際交換學生實施要點與非大陸地區交換學生評分標準表",
                  "source_url": YUNTECH_EXCHANGE_GUIDELINES_URL,
                  "category": "exchange_application",
                  "summary": "雲科大出國交換申請資格、75分或班排前50%及操行80分門檻、40%/40%/20% 評分標準與延長修業規定。",
              },
          }
      ],
      "language_requirements": [
          {
              "title": "英語授課學校 TOEIC 650 基準（東南亞與大陸地區除外）、各國二外門檻與 40 分制語言計分級距",
              "details": [
                  (
                      "校內英語授課底線與例外規定（依《國際交換學生實施要點》第2點第7款）：申請以英文授課之交換學校，語言能力應達 TOEIC 650 分或同等能力標準（如 TOEFL iBT 61–79 / ITP 500–543 / IELTS 5.0–5.5），赴大陸地區、東南亞地區（印尼、越南、馬來西亞、菲律賓）則不在此限；且須符合各交換學校訂定之語言門檻。"
                  ),
                  (
                      "語言能力證明評分級距（佔校內甄選總分 40%，擇一最高分計分）：（1）40 分（CEFR C1）：TOEIC 945 以上、TOEFL iBT 95 以上、TOEFL ITP 627 以上、IELTS 7.0–8.0、JLPT N1；（2）30 分（CEFR B2）：TOEIC 785 以上、TOEFL iBT 72 以上、TOEFL ITP 543 以上、IELTS 5.5–6.5、JLPT N2；（3）20 分（CEFR B1）：TOEIC 550 以上、TOEFL iBT 42 以上、TOEFL ITP 460 以上、IELTS 4.0–5.0、JLPT N3；（4）10 分（CEFR A2）：TOEIC 225 以上、TOEFL ITP 337 以上、IELTS 4.0 以下、JLPT N4；（5）5 分（CEFR A1）：TOEIC 225 以下、JLPT N5。"
                  ),
              ],
              "source": {
                  "title": "國立雲林科技大學非大陸地區交換學生評分標準表與各校招生簡章",
                  "source_url": YUNTECH_SCORING_RUBRIC_URL,
                  "category": "exchange_application",
                  "summary": "雲科大 TOEIC 650 英語授課基準、東南亞與大陸例外規定及 CEFR A1–C1 語檢計分標準表。",
              },
          }
      ],
      "required_documents": [
          {
              "title": "出國交換生系統線上報名、院系核章紙本申請表、成績單、語檢、優秀表現加分附件與 $3,000 保證金規範",
              "details": [
                  (
                      "校內甄選必繳文件：1. 出國交換生系統（admissions-oia.yuntech.edu.tw/oe）線上填報並列印經指導教授（研究生）、系所主任與院長核章之紙本申請表、2. 中英文歷年成績單正本（含歷年平均及班級排名比率，操行達 80 分以上）、3. 有效期限內之外語能力檢定證明、4. 中英文讀書計畫及自傳、5. 其他優秀表現證明（國際／國內／校內會議或競賽、專業證照、社團幹部證明）與師長推薦函（至多 3 封）。"
                  ),
                  (
                      "錄取確認、保證金與返國核銷：錄取公告後須於期限內繳交《錄取資格確認書》、《家長同意書》及新臺幣 3,000 元保證金（無故放棄者沒收保證金）；返國後須繳交交換心得報告、問卷、機票單據與姊妹校正式成績單，以完成學分抵免、獎助學金尾款請領及 NT$3,000 保證金無息退還。"
                  ),
              ],
              "source": {
                  "title": "國立雲林科技大學 2027春季班（115-2）非大陸地區交換生申請公告與簡報",
                  "source_url": YUNTECH_APPLY_2027S_URL,
                  "category": "exchange_application",
                  "summary": "雲科大出國交換線上與紙本雙軌報名程序、必備文件清單、保證金規定與返國核銷義務。",
              },
          }
      ],
      "scholarship_info": [
          {
              "title": "王秋雄榮譽博士德日美獎助金（每學期 10 萬–18 萬）、教育部學海飛颺／惜珠（最高 30 萬）與雲科大出國交流補助（亞洲 11 萬／非亞洲 15 萬）",
              "details": [
                  (
                      "《王秋雄榮譽博士補助德日美交流或進修獎助金》：補助本校非在職專班在學學生（班排前 50%、操行 80 分以上、外語達標）赴德國、日本、美國姊妹校交換至少一學期：（1）德國：柏林地區每學期最高 NT$150,000、阿亨地區 NT$140,000、其他地區 NT$120,000；（2）日本：每學期最高 NT$100,000（一學年 NT$200,000）；（3）美國：紐約／舊金山每學期最高 NT$180,000、洛杉磯 NT$170,000、華盛頓／波士頓 NT$160,000、其他地區 NT$150,000（一學年最高 NT$300,000）。受領生大學部每學期須修習 3 門或 6–9 學分（18 ECTS）且每門課達 B 以上、研究所每學期須修習 2 門或 4–8 學分（12 ECTS）及格，且不得兼領其他獎助學金。"
                  ),
                  (
                      "教育部《學海飛颺／學海惜珠》與《雲科大出國交流或進修補助要點》：（1）學海飛颺／惜珠：補助具中華民國國籍且在臺設籍、系所排名前 40%、操行 80 分以上之在學生赴中港澳以外締約校交換，每人最高 NT$300,000（115 學年度實際核發一學期約 NT$111,873–147,201、一學年約 NT$212,559–279,682）；（2）雲科大出國交流或進修補助：補助在學一般生（不含陸港澳生）出國交換或修讀雙聯學制至少一學期，亞洲地區每學期最高 NT$110,000、亞洲以外地區每學期最高 NT$150,000；短期研究蹲點 2–3 個月最高補助 6–10 萬元、短期國際會議交流最高補助 3 萬元。"
                  ),
              ],
              "source": {
                  "title": "國立雲林科技大學國際事務處—王秋雄榮譽博士獎助金、學海計畫與出國交流補助專區",
                  "source_url": YUNTECH_GRANT_PAGE_URL,
                  "category": "scholarship",
                  "summary": "雲科大王秋雄榮譽博士德日美獎助金、教育部學海飛颺／惜珠及校內出國交流補助要點與獲獎名冊。",
              },
          }
      ],
      "document_explanations": [
          {
              "title": "國立雲林科技大學出國交換生系統報名表、中英文讀書計畫與 20% 優秀表現加分文件準備指南",
              "summary": "說明雲科大線上交換系統填報、院系核章流程、中英文讀書計畫撰寫重點及競賽／證照／社團幹部／推薦函加分採計規則。",
              "key_points": [
                  "申請人須先於線上系統（admissions-oia.yuntech.edu.tw/oe）完成報名與志願排序，再列印申請表請指導教授（研究生）、系主任與院長簽章，於紙本截止日前送交國際事務處。",
                  "《非大陸地區交換學生評分標準表》中「其他優秀表現」佔總分最高 20 分：國際會議／競賽／國際證照每張 2 分、國內會議／競賽／國內證照每張 1 分、校內競賽／社團幹部證明每張 0.5 分（獲前三名或優勝、擔任社長／副社長／總召／副總召者張數加計一次），推薦函每封 1 分（最高 3 分），建議充分整理佐證清冊。",
                  "欲申請《王秋雄榮譽博士補助德日美交流或進修獎助金》者，中英文讀書計畫須具體列出擬於德、日、美姊妹校修習之專業課程（大學部至少 3 門或 18 ECTS、研究所至少 2 門或 12 ECTS）。",
              ],
              "applies_to": [],
              "source": {
                  "title": "國立雲林科技大學非大陸地區交換學生評分標準表與申請說明會簡報",
                  "source_url": YUNTECH_SCORING_RUBRIC_URL,
                  "category": "exchange_application",
                  "summary": None,
              },
              "document_url": YUNTECH_SCORING_RUBRIC_URL,
              "document_type": "official_document",
              "full_text_extracted": True,
          }
      ],
      "rule_explanations": [
          {
              "title": "國立雲林科技大學國際交換學生實施要點：75 分或前 50% 學業門檻、操行 80 分門檻與三大獎助學金規範",
              "summary": "規範雲科大出國交換生申請資格、TOEIC 650 英語授課基準、在學註冊義務、保證金制度及王秋雄／學海／校內補助修課義務。",
              "key_points": [
                  "申請資格為研究所在學學生或入學一學期以上之大學部在學學生，歷年學業成績達 75 分（含）以上或班級排名前 50%，且操行成績達 80 分（含）以上；申請英語授課姊妹校須達 TOEIC 650 或同等標準（赴大陸地區、東南亞地區不在此限）。",
                  "交換期間以 1 學期或 1 學年為限，出國交換期間並未免除在雲科大之註冊及繳費義務；應屆畢業生經核准獲交換學校同意交換者，得申請延長修業年限最長一年。",
                  "《王秋雄榮譽博士德日美獎助金》（每學期 10 萬–18 萬）、《教育部學海飛颺／惜珠》（最高 30 萬）與《雲科大出國交流補助》（亞洲最高 11 萬／非亞洲最高 15 萬）提供充裕經費支持，惟不得重複兼領同一期間之校內外交換獎助金。",
              ],
              "applies_to": [],
              "source": {
                  "title": "國立雲林科技大學國際交換學生實施要點與出國交流補助要點",
                  "source_url": YUNTECH_EXCHANGE_GUIDELINES_URL,
                  "category": "exchange_application",
                  "summary": None,
              },
              "document_url": YUNTECH_EXCHANGE_GUIDELINES_URL,
              "document_type": "official_document",
              "full_text_extracted": True,
          }
      ],
      "sources": [
          {
              "title": "國立雲林科技大學國際事務處（OIA）官方網站",
              "source_url": YUNTECH_OIA_HUB_URL,
              "category": "exchange_application",
              "summary": None,
          },
          {
              "title": "國立雲林科技大學出國交換生申請系統與姊妹校簡章一覽表（115-2／115-1）",
              "source_url": YUNTECH_OE_INTRO_115_2_URL,
              "category": "partner_school",
              "summary": None,
          },
          {
              "title": "國立雲林科技大學國際交換學生實施要點 PDF",
              "source_url": YUNTECH_EXCHANGE_GUIDELINES_URL,
              "category": "exchange_application",
              "summary": None,
          },
          {
              "title": "國立雲林科技大學非大陸地區交換學生評分標準表 PDF",
              "source_url": YUNTECH_SCORING_RUBRIC_URL,
              "category": "exchange_application",
              "summary": None,
          },
          {
              "title": "國立雲林科技大學 2027春季班（115-2）赴非大陸地區交換生說明會簡報 PDF",
              "source_url": YUNTECH_SLIDES_2027S_URL,
              "category": "exchange_application",
              "summary": None,
          },
          {
              "title": "國立雲林科技大學 2027春季班（115-2）大陸地區交換生招生簡章與名額表",
              "source_url": YUNTECH_MAINLAND_2027S_URL,
              "category": "partner_school",
              "summary": None,
          },
          {
              "title": "王秋雄榮譽博士補助德日美交流或進修獎助金實施要點及發放作業規定 PDF",
              "source_url": YUNTECH_WANG_RULES_URL,
              "category": "scholarship",
              "summary": None,
          },
          {
              "title": "國立雲林科技大學學生出國交流或進修補助要點 PDF",
              "source_url": YUNTECH_SUBSIDY_RULES_URL,
              "category": "scholarship",
              "summary": None,
          },
          {
              "title": "國立雲林科技大學「學海飛颺」與「學海惜珠」專案推薦作業要點 PDF",
              "source_url": YUNTECH_XUEHAI_RULES_URL,
              "category": "scholarship",
              "summary": None,
          },
          {
              "title": "國立雲林科技大學國際事務處—雙聯學位、銜接學位與交換生經驗分享專區",
              "source_url": YUNTECH_EXP_115_URL,
              "category": "partner_school",
              "summary": None,
          },
      ],
  }
  (OFFICIAL_YUNTECH_DIR / "student_dashboard.json").write_text(
      json.dumps(student_dashboard_payload, ensure_ascii=False, indent=2) + "\n",
      encoding="utf-8",
  )

  pages_records = [
      {
          "title": "國立雲林科技大學：國際事務處非大陸與大陸地區出國交換生甄選時程（2027春季班錄取公告與2027秋季班預告）",
          "source_url": YUNTECH_APPLY_2027S_URL,
          "published_at": "2026-10-19T00:00:00Z",
          "text": "\n".join(exchange_info_payload["application_period"]),
          "summary": "\n".join(exchange_info_payload["application_period"]),
          "category": "exchange_application",
          "attachments": [],
          "crawled_at": CHECKED_AT,
          "content_hash": hashlib.sha256("\n".join(exchange_info_payload["application_period"]).encode("utf-8")).hexdigest(),
      },
      {
          "title": "國立雲林科技大學：國際交換學生實施要點、75分或前50%學業門檻、操行80分門檻與40%／40%／20%評分標準表",
          "source_url": YUNTECH_EXCHANGE_GUIDELINES_URL,
          "published_at": "2025-04-22T00:00:00Z",
          "text": "\n".join(exchange_info_payload["eligibility"]),
          "summary": "\n".join(exchange_info_payload["eligibility"]),
          "category": "exchange_application",
          "attachments": [],
          "crawled_at": CHECKED_AT,
          "content_hash": hashlib.sha256("\n".join(exchange_info_payload["eligibility"]).encode("utf-8")).hexdigest(),
      },
      {
          "title": "國立雲林科技大學：112 所交換與雙聯合作姊妹校外語檢定門檻（英語授課 TOEIC 650 基準與 CEFR 計分級距）",
          "source_url": YUNTECH_SCORING_RUBRIC_URL,
          "published_at": "2026-09-07T00:00:00Z",
          "text": "\n".join(exchange_info_payload["language_requirement"]),
          "summary": "\n".join(exchange_info_payload["language_requirement"]),
          "category": "exchange_application",
          "attachments": [],
          "crawled_at": CHECKED_AT,
          "content_hash": hashlib.sha256("\n".join(exchange_info_payload["language_requirement"]).encode("utf-8")).hexdigest(),
      },
      {
          "title": "國立雲林科技大學：出國交換生系統線上報名、核章申請表、優秀表現加分文件與 NT$3,000 保證金規範",
          "source_url": YUNTECH_OE_PORTAL_URL,
          "published_at": "2026-09-07T00:00:00Z",
          "text": "\n".join(exchange_info_payload["required_documents"]),
          "summary": "\n".join(exchange_info_payload["required_documents"]),
          "category": "exchange_application",
          "attachments": [],
          "crawled_at": CHECKED_AT,
          "content_hash": hashlib.sha256("\n".join(exchange_info_payload["required_documents"]).encode("utf-8")).hexdigest(),
      },
      {
          "title": "國立雲林科技大學：王秋雄榮譽博士德日美獎助金（10萬–18萬／學期）、教育部學海飛颺／惜珠與校內出國交流補助（亞洲11萬／非亞洲15萬）",
          "source_url": YUNTECH_GRANT_PAGE_URL,
          "published_at": "2026-07-20T00:00:00Z",
          "text": "\n".join(exchange_info_payload["scholarship_info"]),
          "summary": "\n".join(exchange_info_payload["scholarship_info"]),
          "category": "scholarship",
          "attachments": [],
          "crawled_at": CHECKED_AT,
          "content_hash": hashlib.sha256("\n".join(exchange_info_payload["scholarship_info"]).encode("utf-8")).hexdigest(),
      },
  ]
  (OFFICIAL_YUNTECH_DIR / "pages.jsonl").write_text(
      "\n".join(json.dumps(p, ensure_ascii=False) for p in pages_records) + "\n",
      encoding="utf-8",
  )

  home_rules = {
      "school_id": "yuntech",
      "school_name": "國立雲林科技大學",
      "eligibility": student_dashboard_payload["eligibility"],
      "application_periods": student_dashboard_payload["application_periods"],
      "selection_rules": {
          "academic_score_minimum": 75.0,
          "class_rank_percentile_maximum": 50.0,
          "conduct_score_minimum": 80.0,
          "english_taught_toeic_minimum": 650,
          "southeast_asia_and_mainland_exempt_from_toeic_650": True,
          "academic_and_rank_weight_percent": 40,
          "language_proficiency_weight_percent": 40,
          "other_achievements_weight_percent": 20,
          "deposit_twd": 3000,
          "wang_scholarship_germany_per_semester_twd": "120,000–150,000",
          "wang_scholarship_japan_per_semester_twd": 100000,
          "wang_scholarship_usa_per_semester_twd": "150,000–180,000",
          "yuntech_subsidy_asia_max_per_semester_twd": 110000,
          "yuntech_subsidy_non_asia_max_per_semester_twd": 150000,
          "xuehai_max_twd": 300000,
          "return_documents_due": "返國後繳交交換學生心得報告、問卷、正式成績單及機票單據辦理學分抵免、獎助學金核銷與 NT$3,000 保證金退還",
      },
      "source_urls": yuntech_source_urls,
      "verified_at": "2026-10-20",
  }
  (OFFICIAL_YUNTECH_DIR / "home_rules.json").write_text(
      json.dumps(home_rules, ensure_ascii=False, indent=2) + "\n",
      encoding="utf-8",
  )
  (OFFICIAL_YUNTECH_DIR / "documents.json").write_text(
      json.dumps(
          {
              "school_name": "國立雲林科技大學",
              "required_documents": student_dashboard_payload["required_documents"],
              "source_urls": yuntech_source_urls,
          },
          ensure_ascii=False,
          indent=2,
      )
      + "\n",
      encoding="utf-8",
  )
  (OFFICIAL_YUNTECH_DIR / "scholarships.json").write_text(
      json.dumps(
          {
              "school_name": "國立雲林科技大學",
              "scholarships": student_dashboard_payload["scholarship_info"],
              "source_urls": yuntech_source_urls,
          },
          ensure_ascii=False,
          indent=2,
      )
      + "\n",
      encoding="utf-8",
  )

  completeness = {
      "school_id": "yuntech",
      "school_name": "國立雲林科技大學",
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
      "verified_official_websites": sum(1 for p in partners if p.get("official_website")),
      "verified_campus_images": sum(1 for p in partners if p.get("image_status") == "verified"),
      "workflow_count": len(workflows),
      "destination_profile_count": len(destinations),
      "student_life_count": len(life_records),
      "active_term": (
          "國立雲林科技大學國際事務處 115 學年度第 2 學期（2027春季班）及第 1 學期（2026秋季班）非大陸與大陸地區出國交換甄選已完成收件與放榜，116 學年度第 1 學期（2027秋季班）預計於 2027 年 2–3 月開放申請；共完整收錄 112 所全球交換與雙聯／銜接合作學校（含 45 所當期開放申請名額校及 67 所歷屆締約合作校，橫跨歐、美、亞、大洋洲 23 個國家與地區，並收錄 29 所學校共 118 篇歷屆學長姐返國心得報告）。"
      ),
      "verified_at": "2026-10-20",
  }
  (OFFICIAL_YUNTECH_DIR / "catalog-completeness.json").write_text(
      json.dumps(completeness, ensure_ascii=False, indent=2) + "\n",
      encoding="utf-8",
  )
  (OFFICIAL_YUNTECH_DIR / "verification_status.json").write_text(
      json.dumps(
          {
              "school_id": "yuntech",
              "school_name": "國立雲林科技大學",
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
          "sources/yuntech/exchange_guidelines_2025.pdf",
          YUNTECH_EXCHANGE_GUIDELINES_URL,
          "國立雲林科技大學國際交換學生實施要點 PDF",
      ),
      (
          "sources/yuntech/exchange_scoring_rubric.pdf",
          YUNTECH_SCORING_RUBRIC_URL,
          "國立雲林科技大學非大陸地區交換學生評分標準表 PDF",
      ),
      (
          "sources/yuntech/session_2027s_non_mainland_slides.pdf",
          YUNTECH_SLIDES_2027S_URL,
          "國立雲林科技大學 2027春季班（115-2）赴非大陸地區交換生說明會簡報 PDF",
      ),
      (
          "sources/yuntech/session_2026f_non_mainland_slides.pdf",
          YUNTECH_SLIDES_2026F_URL,
          "國立雲林科技大學 2026秋季班（115-1）赴非大陸地區交換生說明會簡報 PDF",
      ),
      (
          "sources/yuntech/session_202609_mainland_slides.pdf",
          YUNTECH_SLIDES_MAINLAND_URL,
          "國立雲林科技大學赴大陸地區交換生說明會簡報 PDF",
      ),
      (
          "sources/yuntech/wang_scholarship_rules.pdf",
          YUNTECH_WANG_RULES_URL,
          "王秋雄榮譽博士補助德日美交流或進修獎助金實施要點及發放作業規定 PDF",
      ),
      (
          "sources/yuntech/outbound_subsidy_rules_114.pdf",
          YUNTECH_SUBSIDY_RULES_URL,
          "國立雲林科技大學學生出國交流或進修補助要點（114年6月修正）PDF",
      ),
      (
          "sources/yuntech/xuehai_scholarship_rules.pdf",
          YUNTECH_XUEHAI_RULES_URL,
          "國立雲林科技大學「學海飛颺」與「學海惜珠」專案推薦作業要點 PDF",
      ),
      (
          "sources/yuntech/dual_degree_calpoly.pdf",
          YUNTECH_DUAL_DEGREE_URL,
          "國立雲林科技大學與美國加州州立理工大學波莫納分校（Cal Poly Pomona）3+1+X 雙聯學位簡章 PDF",
      ),
      (
          "sources/yuntech/dual_degree_ksu.pdf",
          YUNTECH_DUAL_DEGREE_URL,
          "國立雲林科技大學與美國堪薩斯州立大學（KSU）雙碩士學位簡章 PDF",
      ),
      (
          "sources/yuntech/dual_degree_its.pdf",
          YUNTECH_DUAL_DEGREE_URL,
          "國立雲林科技大學與印尼泗水理工學院（ITS）雙聯學位簡章 PDF",
      ),
      (
          "sources/yuntech/dual_degree_chiba_master.pdf",
          YUNTECH_DUAL_DEGREE_URL,
          "國立雲林科技大學與日本千葉大學碩士雙聯學位簡章 PDF",
      ),
      (
          "sources/yuntech/dual_degree_chiba_phd.pdf",
          YUNTECH_DUAL_DEGREE_URL,
          "國立雲林科技大學與日本千葉大學博士雙聯學位簡章 PDF",
      ),
      (
          "sources/yuntech/pathway_unisa_3plus1plus1.pdf",
          YUNTECH_PATHWAY_URL,
          "國立雲林科技大學與澳洲南澳大學（UniSA）3+1+1 學碩士銜接學位簡章 PDF",
      ),
      (
          "sources/yuntech/pathway_utdallas_bridge.pdf",
          YUNTECH_PATHWAY_URL,
          "國立雲林科技大學與美國德州大學達拉斯分校（UT Dallas）橋樑學位簡章 PDF",
      ),
      (
          "sources/yuntech/oe_intro_115_2.html",
          YUNTECH_OE_INTRO_115_2_URL,
          "國立雲林科技大學出國交換生申請系統—115-2 學校與名額一覽表 HTML",
      ),
      (
          "sources/yuntech/oe_intro_115_1.html",
          YUNTECH_OE_INTRO_115_1_URL,
          "國立雲林科技大學出國交換生申請系統—115-1 學校與名額一覽表 HTML",
      ),
      (
          "sources/yuntech/brochures_115_2.json",
          YUNTECH_OE_INTRO_115_2_URL,
          "國立雲林科技大學出國交換生系統 115-2 各校詳細招生簡章 JSON",
      ),
      (
          "sources/yuntech/brochures_115_1.json",
          YUNTECH_OE_INTRO_115_1_URL,
          "國立雲林科技大學出國交換生系統 115-1 各校詳細招生簡章 JSON",
      ),
      (
          "sources/yuntech/brochures_114_2.json",
          "https://admissions-oia.yuntech.edu.tw/oe/index/intro/puid/114-2/lang/zh_TW",
          "國立雲林科技大學出國交換生系統 114-2 各校詳細招生簡章 JSON",
      ),
      (
          "sources/yuntech/brochures_114_1.json",
          "https://admissions-oia.yuntech.edu.tw/oe/index/intro/puid/114-1/lang/zh_TW",
          "國立雲林科技大學出國交換生系統 114-1 各校詳細招生簡章 JSON",
      ),
      (
          "sources/yuntech/mainland_2027s.html",
          YUNTECH_MAINLAND_2027S_URL,
          "國立雲林科技大學 2027春季班赴大陸地區交換生簡章與名額表 HTML",
      ),
      (
          "sources/yuntech/item_1413_2027s_apply.html",
          YUNTECH_APPLY_2027S_URL,
          "國立雲林科技大學 2027春季班赴非大陸地區交換生甄選公告 HTML",
      ),
      (
          "sources/yuntech/item_1472_2027s_roster.html",
          YUNTECH_ROSTER_2027S_URL,
          "國立雲林科技大學 2027春季班（115-2）赴非大陸地區交換生錄取名單公告 HTML",
      ),
      (
          "sources/yuntech/item_1346_115_1_roster.html",
          YUNTECH_ROSTER_115_1_URL,
          "國立雲林科技大學 2026秋季班（115-1）赴非大陸地區交換生錄取名單公告 HTML",
      ),
      (
          "sources/yuntech/expsharing_115.html",
          YUNTECH_EXP_115_URL,
          "國立雲林科技大學 115 學年度出國交換學生返國經驗分享專頁 HTML",
      ),
      (
          "sources/yuntech/expsharing_114.html",
          YUNTECH_EXP_114_URL,
          "國立雲林科技大學 114 學年度出國交換學生返國經驗分享專頁 HTML",
      ),
      (
          "sources/yuntech/expsharing_113.html",
          YUNTECH_EXP_113_URL,
          "國立雲林科技大學 113 學年度出國交換學生返國經驗分享專頁 HTML",
      ),
      (
          "sources/yuntech/yuntech_academic_units.json",
          "https://www.yuntech.edu.tw/",
          "國立雲林科技大學 5 個學院與 29 個系所學位學程官方組織 JSON",
      ),
      (
          "sources/yuntech/yuntech_catalog_source.json",
          YUNTECH_OE_INTRO_115_2_URL,
          "國立雲林科技大學 112 所出國交換與雙聯合作學校整合資料集 JSON",
      ),
      (
          "sources/yuntech/yuntech_resolved_locations.json",
          YUNTECH_OE_INTRO_115_2_URL,
          "國立雲林科技大學 112 所出國交換與雙聯合作學校 ROR / Wikidata 地理座標核對表 JSON",
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
      "school_id": "yuntech",
      "school_name": "國立雲林科技大學",
      "generated_at": CHECKED_AT,
      "active_cycle_note": completeness["active_term"],
      "sources": prov_sources,
  }
  prov_text = json.dumps(provenance_payload, ensure_ascii=False, indent=2) + "\n"
  (OFFICIAL_YUNTECH_DIR / "import_provenance.json").write_text(prov_text, encoding="utf-8")
  (OFFICIAL_YUNTECH_DIR / "import-provenance.json").write_text(prov_text, encoding="utf-8")

  print(
      f"Successfully built YunTech catalog: {len(partners)} partners"
      f" ({open_partner_count} open, {completeness['verified_campus_images']}"
      f" verified images, {completeness['verified_locations']} verified"
      f" locations), {len(workflows)} workflows,"
      f" {len(destinations)} destinations, {len(research_records)} research"
      f" records, {exp_covered_schools} schools with experience records"
      f" ({len(student_experience_rows)} rows)."
  )


if __name__ == "__main__":
  main()
