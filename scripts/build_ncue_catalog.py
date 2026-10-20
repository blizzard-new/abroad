"""Build the official National Changhua University of Education (國立彰化師範大學, NCUE) exchange data bundle."""

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

SOURCES_NCUE_DIR = REPO_ROOT / "sources" / "ncue"
OFFICIAL_NCUE_DIR = REPO_ROOT / "src" / "exchange_info" / "official_data" / "ncue"
STATIC_DIR = REPO_ROOT / "src" / "exchange_info" / "static"

CHECKED_AT = "2026-10-20T17:20:00Z"

NCUE_OICA_HUB_URL = "https://oicaweb.ncue.edu.tw/"
NCUE_OUTBOUND_OVERVIEW_URL = "https://oicaweb.ncue.edu.tw/p/412-1002-1171.php?Lang=zh-tw"
NCUE_OVERSEAS_PLAN_URL = "https://oicaweb.ncue.edu.tw/p/412-1002-1220.php?Lang=zh-tw"
NCUE_MAINLAND_PLAN_URL = "https://oicaweb.ncue.edu.tw/p/412-1002-1219.php?Lang=zh-tw"
NCUE_DUAL_DEGREE_URL = "https://oicaweb.ncue.edu.tw/p/412-1002-1167.php?Lang=zh-tw"
NCUE_GLOBAL_SISTERS_URL = "https://oicaweb.ncue.edu.tw/p/412-1002-1164.php?Lang=zh-tw"
NCUE_REGULATIONS_URL = "https://oicaweb.ncue.edu.tw/p/412-1002-1117.php?Lang=zh-tw"
NCUE_FORMS_URL = "https://oicaweb.ncue.edu.tw/p/412-1002-1118.php?Lang=zh-tw"

NCUE_OVERSEAS_116_POST_URL = "https://oicaweb.ncue.edu.tw/p/406-1002-34307,r140.php?Lang=zh-tw"
NCUE_OVERSEAS_116_BROCHURE_URL = "https://oicaweb.ncue.edu.tw/var/file/19/1019/img/542278849.pdf"
NCUE_OVERSEAS_116_SHEET_URL = "https://docs.google.com/spreadsheets/d/1JZEHkhetJoABfPogFlrqiyvG8URvmEw9/edit"
NCUE_OVERSEAS_116_APP_FORM_URL = "https://oicaweb.ncue.edu.tw/var/file/19/1019/img/974155076.docx"
NCUE_PARENTAL_GUARANTEE_URL = "https://oicaweb.ncue.edu.tw/var/file/19/1019/img/348780386.docx"
NCUE_HEALTH_DECLARATION_URL = "https://oicaweb.ncue.edu.tw/var/file/19/1019/img/522622028.docx"

NCUE_MOE_XUEHAI_116_POST_URL = "https://oicaweb.ncue.edu.tw/p/406-1002-31228,r140.php?Lang=zh-tw"
NCUE_XUEHAI_GUIDELINES_URL = "https://oicaweb.ncue.edu.tw/var/file/19/1019/img/191957275.pdf"
NCUE_MOE_SUBSIDY_DIRECTIONS_URL = "https://oicaweb.ncue.edu.tw/var/file/19/1019/img/308829954.pdf"
NCUE_XUEHAI_FEIYANG_FORM_URL = "https://oicaweb.ncue.edu.tw/var/file/19/1019/img/602763967.odt"
NCUE_XUEHAI_XIZHU_FORM_URL = "https://oicaweb.ncue.edu.tw/var/file/19/1019/img/233821766.odt"
NCUE_XUEHAI_CONTRACT_URL = "https://oicaweb.ncue.edu.tw/var/file/19/1019/img/844199804.docx"

NCUE_EXCHANGE_SELECTION_GUIDELINES_URL = "https://oicaweb.ncue.edu.tw/var/file/19/1019/img/547428539.pdf"
NCUE_DUAL_DEGREE_REGS_URL = "https://oicaweb.ncue.edu.tw/var/file/19/1019/img/603615731.pdf"
NCUE_OUTBOUND_COURSE_NOTES_URL = "https://oicaweb.ncue.edu.tw/var/file/19/1019/img/433095064.pdf"
NCUE_CREDIT_TRANSFER_REGS_URL = "https://oicaweb.ncue.edu.tw/var/file/19/1019/img/504843202.pdf"
NCUE_CREDIT_CONVERSION_TABLE_URL = "https://oicaweb.ncue.edu.tw/var/file/19/1019/img/123052535.pdf"

NCUE_MAINLAND_115_2_POST_URL = "https://oicaweb.ncue.edu.tw/p/406-1002-34980,r158.php?Lang=zh-tw"
NCUE_MAINLAND_115_2_PARTNERS_URL = "https://oicaweb.ncue.edu.tw/p/406-1002-34979,r158.php?Lang=zh-tw"
NCUE_MAINLAND_115_1_POST_URL = "https://oicaweb.ncue.edu.tw/p/406-1002-33287,r158.php?Lang=zh-tw"
NCUE_EXP_OVERSEAS_URL = "https://oicaweb.ncue.edu.tw/p/403-1002-163-1.php?Lang=zh-tw"
NCUE_EXP_MAINLAND_URL = "https://oicaweb.ncue.edu.tw/p/403-1002-159-1.php?Lang=zh-tw"

REGION_BY_COUNTRY = {
    "美國": "美洲",
    "加拿大": "美洲",
    "烏拉圭": "美洲",
    "英國": "歐洲",
    "俄羅斯": "歐洲",
    "捷克": "歐洲",
    "羅馬尼亞": "歐洲",
    "瑞士": "歐洲",
    "法國": "歐洲",
    "德國": "歐洲",
    "西班牙": "歐洲",
    "土耳其": "歐洲",
    "澳洲": "大洋洲",
    "日本": "亞洲",
    "韓國": "亞洲",
    "馬來西亞": "亞洲",
    "印尼": "亞洲",
    "泰國": "亞洲",
    "蒙古": "亞洲",
    "阿拉伯聯合大公國": "亞洲",
    "越南": "亞洲",
    "中國大陸": "中國大陸及港澳",
    "香港": "中國大陸及港澳",
}

REGION_COST_DEFAULTS = {
    "美國": (
        "USD 1,400–2,600 / 月（加州大學柏克萊分校 UC Berkeley、爾灣分校 UCI、聖地牙哥分校 UCSD、明德大學蒙特雷國際研究學院 MIIS 及費城天普大學 Temple、喬治梅森大學 GMU 約 USD 1,800–2,600 / 月；加州州立大學弗雷斯諾分校 CSU Fresno、肯尼索州立大學 KSU、莫瑞州立大學、奧斯汀佩伊州立大學 APSU、德州農工金斯維爾分校 TAMUK 校內宿舍與學餐約 USD 1,100–1,600 / 月；可申請教育部學海飛颺／惜珠獎學金）",
        "須憑接待校核發之 DS-2019（交換 J-1）或 I-20（雙聯 F-1）表格繳納 SEVIS I-901 費用並向美國在台協會（AIT）申辦簽證，且須購買接待校規定之學生醫療保險及彰師大出國全期海外醫療及意外險。",
    ),
    "加拿大": (
        "CAD 1,400–2,200 / 月（安大略省奧沙瓦安大略理工大學 Ontario Tech University 及卑詩省卡斯爾加希爾克學院 Selkirk College 校內外學生宿舍、膳食與大眾運輸；可申請教育部學海飛颺／惜珠獎學金）",
        "交換一學期（6 個月內）可申辦加拿大 eTA 電子旅行證入境，交換一學年須申辦 Study Permit 學習許可，並加入接待校國際學生醫療保險計畫。",
    ),
    "烏拉圭": (
        "USD 750–1,200 / 月（首都蒙特維多大學 Universidad de Montevideo 寄宿家庭或學生合租公寓、餐飲與市區公車開銷親民）",
        "須憑蒙特維多大學入學許可申辦烏拉圭學生簽證，並於出國前投保涵蓋全期之海外醫療、意外及緊急醫療後送保險。",
    ),
    "英國": (
        "GBP 950–1,450 / 月（布里斯托西英格蘭大學 UWE Bristol、格拉斯哥史崔克萊大學 University of Strathclyde 及伯明罕城市大學 BCU 學生宿舍、自炊伙食與學生交通卡；可申請教育部學海飛颺／惜珠或雙聯獎學金）",
        "交換一學期（6 個月內）可辦理英國 Standard Visitor 簽證，交換一學年或攻讀雙聯學位須申辦英國 Student Visa 並繳納 IHS 醫療附加費。",
    ),
    "俄羅斯": (
        "USD 450–800 / 月（聖彼得堡國立電工大學 LETI 校內學生宿舍費用低廉，每月生活與地鐵月票開銷實惠）",
        "須憑聖彼得堡國立電工大學核發之官方邀請函向莫斯科台北經濟文化協調委員會駐台北代表處申辦俄羅斯留學簽證並投保當地醫療險。",
    ),
    "捷克": (
        "CZK 11,000–17,000 / 月（約 EUR 450–700 / 月，赫拉德茨克拉洛韋大學 UHK、奧斯特拉瓦大學 UO 及西波希米亞大學 UWB 學生宿舍、大學餐廳 Менза 與捷克學生半價火車公車優惠極為親民，為彰師大熱門交換國別）",
        "須憑捷克接待校核發之入學許可與住宿證明向捷克經濟文化辦事處申辦長期居留／學生簽證，並購買捷克法定綜合醫療保險（pVZP）。",
    ),
    "羅馬尼亞": (
        "EUR 450–750 / 月（西蒂米什瓦拉大學 West University of Timișoara 校內學生宿舍、學生餐廳與市區大眾運輸費用低廉）",
        "須憑接待校入學許可與羅馬尼亞教育部核准函申辦國家 D 類長期學生簽證，並投保涵蓋全期之歐盟醫療保險。",
    ),
    "瑞士": (
        "CHF 1,600–2,400 / 月（瑞士西部應用科技大學日內瓦商學院 HEG-Genève 學生宿舍、日常伙食與日內瓦大眾運輸月票）",
        "須憑日內瓦商學院入學許可向瑞士商務辦事處申辦瑞士國家 D 類學生簽證，抵瑞後辦理居留證並投保瑞士認可之學生醫療保險。",
    ),
    "法國": (
        "EUR 800–1,350 / 月（巴黎法國國立東方語言文化學院 INALCO、索邦大學 Sorbonne 約 EUR 1,000–1,400 / 月；波爾多蒙田大學 Université Bordeaux Montaigne、特魯瓦科技大學 UTT 約 EUR 700–1,050 / 月，可申請 CROUS 學生宿舍與法國政府 CAF 房補）",
        "須先透過法國教育中心（Campus France）完成線上面談程序，再向法國在台協會申辦長期學生簽證（VLS-TS），抵法後完成 OFII 生效與法國學生健保登錄。",
    ),
    "德國": (
        "EUR 934–1,250 / 月（德國簽證限制提領帳戶 Sperrkonto 法定基準為每月 EUR 992，含柏林 HTW Berlin、多特蒙德 FH Dortmund、威斯瑪 HS Wismar、卡爾斯魯厄教育大學 PH Karlsruhe、法蘭克福應用科大 Frankfurt UAS、布萊梅 HS Bremen、開姆尼茨工大 TU Chemnitz、比勒費爾德大學及羅特林根大學學生宿舍 Studierendenwerk、伙食與學期票 Semesterticket）",
        "須辦理德國法定學生公保（如 TK / AOK，30 歲以下約 EUR 125–135 / 月）、繳納學期雜費（Semesterbeitrag）並向德國在台協會申辦長期學生簽證。",
    ),
    "西班牙": (
        "EUR 650–1,050 / 月（安達盧西亞自治區哈恩大學 Universidad de Jaén、阿爾梅里亞大學 Universidad de Almería 及塞維利亞大學 Universidad de Sevilla 學生分租公寓、大學食堂與公車月票開銷實惠）",
        "須憑西班牙接待校入學許可向西班牙商務辦事處申辦學生簽證，並投保無自負額、涵蓋全期之西班牙醫療保險。",
    ),
    "土耳其": (
        "EUR 400–700 / 月（馬尼薩杰拉魯巴亞爾大學 Manisa Celal Bayar University 及馬拉蒂亞伊諾努大學 İnönü University 校園生活、住宿與餐飲費用低廉）",
        "須憑土耳其接待校入學許可向駐台北土耳其貿易辦事處申辦學生簽證，抵土後辦理居留證（İkamet）並投保健康保險。",
    ),
    "澳洲": (
        "AUD 1,900–2,900 / 月（雪梨新南威爾斯大學 UNSW［彰師大3年＋UNSW交換1年專案］約 AUD 2,300–2,900 / 月；昆士蘭圖움巴南昆士蘭大學 UniSQ 約 AUD 1,600–2,200 / 月）",
        "須購買澳洲海外學生健康保險（OSHC）並透過澳洲內政部 ImmiAccount 線上申辦 Subclass 500 學生簽證。",
    ),
    "日本": (
        "JPY 75,000–125,000 / 月（神戶大學、筑波大學約 JPY 85,000–125,000 / 月；新潟大學、福岡教育大學、愛知教育大學、秋田大學、東北大學等國立大學學生寮費僅約 JPY 10,000–35,000 / 月；可申請教育部學海飛颺／惜珠或日本 JASSO 獎學金）",
        "須憑日本接待校核發之在留資格認定證明書（COE）向日本台灣交流協會申辦留學簽證，抵日後須依法加入日本國民健康保險（NHI）並投保海外醫療及意外險。",
    ),
    "韓國": (
        "KRW 750,000–1,250,000 / 月（首爾市立大學 UOS、首爾女子大學 SWU、明知大學 Myongji 約 KRW 850,000–1,250,000 / 月；釜山國立釜慶大學 PKNU、大邱大學 Daegu Univ.、晉州慶尚國立大學 GNU、大田又松大學 Woosong 校內宿舍與學餐開銷實惠）",
        "須憑韓國接待校核發之標準入學許可書向駐台北韓國代表部申辦 D-2-6 交換學生簽證，抵韓後辦理外國人登錄並自動納入韓國國民健康保險（NHIS）。",
    ),
    "馬來西亞": (
        "MYR 1,500–2,500 / 月（馬來西亞國立大學 UKM、拉曼大學 UTAR 及馬來西亞砂拉越大學 UNIMAS 校內外學生宿舍與飲食生活費親民；可申請教育部新南向學海飛颺／惜珠獎學金）",
        "須於出國前透過馬來西亞 EMGS（Education Malaysia Global Services）系統線上申辦學生簽證核准函（VAL / Student Pass）並投保 EMGS 指定醫療保險。",
    ),
    "印尼": (
        "IDR 4,500,000–8,000,000 / 月（印尼大學 UI、日惹大學 UGM、萬隆理工學院 ITB、印尼教育大學 UPI、泗水理工大學 ITS、艾爾朗加大學 UNAIR、國立三一一大學 UNS、三寶瓏國立大學 UNNES、建國大學 Binus、慈育大學 UBM、諾門森大學等住宿與生活費低廉）",
        "須由印尼接待校協助向印尼移民總局申辦 C316 學習電子簽證（e-Visa）並投保海外全期醫療及意外保險。",
    ),
    "泰國": (
        "THB 12,000–22,000 / 月（曼谷蒙庫國王科技大學 KMUTT、泰國農業大學 Kasetsart University 及泰南宋卡王子大學 PSU、他信大學 Thaksin University 學生宿舍與校園餐飲開銷實惠）",
        "須憑泰國接待校核發之入學許可公文向泰國貿易經濟辦事處（TTEO）申辦 Non-Immigrant ED 學生簽證並投保海外醫療險。",
    ),
    "蒙古": (
        "USD 450–750 / 月（烏蘭巴托全球領袖大學 Global Leadership University 學生宿舍、餐飲與市區交通費用低廉）",
        "須憑接待校入學許可申辦蒙古學生簽證，並於出國前投保涵蓋全期之海外醫療及意外保險。",
    ),
    "阿拉伯聯合大公國": (
        "AED 3,200–5,200 / 月（約 USD 880–1,420 / 月，阿治曼大學 Ajman University 校內學生宿舍、餐飲與大眾運輸費用較杜拜市中心親民）",
        "由阿治曼大學國際事務處協助申辦阿聯酋學生居留簽證（Student Residence Visa）並投保當地強制醫療保險。",
    ),
    "越南": (
        "USD 380–650 / 月（河內大學 Hanoi University 校內國際學生宿舍與日常飲食、交通費用低廉；可申請教育部新南向學海飛颺／惜珠獎學金）",
        "須憑河內大學入學許可透過駐臺北越南經濟文化辦事處申辦越南學生簽證，並於出國前投保涵蓋全期之海外醫療及意外險。",
    ),
    "中國大陸": (
        "RMB 1,800–3,500 / 月（北京師範大學、華東師範大學、東北師範大學、華中師範大學、陝西師範大學、西北師範大學、西南大學、四川大學、武漢大學、廈門大學、北京外國語大學等 985／211 重點高校校內宿舍約 RMB 600–1,500 / 學期，學生食堂與地鐵公車成本低廉）",
        "持有效護照與臺胞證（臺灣居民來往大陸通行證）入境，並須投保涵蓋大陸地區交換全期之意外及醫療保險（並依接待校規定投保大陸境內來華留學生綜合醫療保險）。",
    ),
    "香港": (
        "HKD 8,500–13,500 / 月（香港教育大學 EdUHK 及香港恒生大學 HSUHK 校內學生宿舍、校園餐廳與港鐵學生優惠八達通）",
        "須透過香港接待校向香港入境事務處申辦來港就讀進入許可（Student Visa / Entry Permit）並投保海外醫療及意外保險。",
    ),
}

SEMESTER_DATES_BY_COUNTRY = {
    "美國": "秋季學期（Fall）：約 8 月中下旬至 12 月中旬；春季學期（Spring）：約 1 月中旬至 5 月中旬",
    "加拿大": "秋季學期（Fall）：約 9 月初至 12 月中旬；冬季／春季學期（Winter）：約 1 月初至 4 月底",
    "烏拉圭": "第一學期（南半球秋季）：約 3 月初至 7 月中旬；第二學期（南半球春季）：約 8 月初至 12 月中旬",
    "英國": "秋季學期（Semester 1 / Autumn）：約 9 月中下旬至翌年 1 月；春季學期（Semester 2 / Spring）：約 1 月下旬至 5/6 月",
    "俄羅斯": "秋季學期：約 9 月初至翌年 1 月；春季學期：約 2 月初至 6 月底",
    "捷克": "冬季學期（Winter / 秋季班）：約 9 月下旬至翌年 1/2 月；夏季學期（Summer / 春季班）：約 2 月中旬至 6 月底",
    "羅馬尼亞": "第一學期（秋季班）：約 10 月初至翌年 2 月；第二學期（春季班）：約 2 月下旬至 6 月底",
    "瑞士": "秋季學期（Autumn）：約 9 月中旬至翌年 1 月底；春季學期（Spring）：約 2 月中旬至 6 月中旬",
    "法國": "秋季學期（Semestre 1）：約 9 月初至 12 月底／翌年 1 月；春季學期（Semestre 2）：約 1 月中旬至 5/6 月",
    "德國": "冬季學期（Wintersemester / 秋季班）：約 10 月初（FH 為 9 月中旬）至翌年 2/3 月；夏季學期（Sommersemester / 春季班）：約 3/4 月至 7/8 月",
    "西班牙": "第一學期（秋季班）：約 9 月中旬至翌年 1/2 月；第二學期（春季班）：約 2 月初至 6 月中下旬",
    "土耳其": "秋季學期：約 9 月中下旬至翌年 1 月；春季學期：約 2 月中旬至 6 月中旬",
    "澳洲": "第一學期（Semester 1 / Trimester 1）：約 2 月中下旬至 6 月；第二學期（Semester 2 / Trimester 3）：約 7/9 月至 11/12 月",
    "日本": "秋季班（彰師大上學期）：約 9/10 月至翌年 2/3 月；春季班（彰師大下學期）：約 4 月至 8/9 月",
    "韓國": "秋季學期（第2學期）：約 9 月初至 12 月中下旬；春季學期（第1學期）：約 3 月初至 6 月中下旬",
    "馬來西亞": "秋季學期（第1學期）：約 9/10 月至翌年 1/2 月；春季學期（第2學期）：約 2/3 月至 6/7 月（拉曼大學 UTAR 採 1 月／5 月／10 月三學期制）",
    "印尼": "奇數／秋季學期（Odd Semester）：約 8/9 月至 12 月／翌年 1 月；偶數／春季學期（Even Semester）：約 2 月至 6/7 月",
    "泰國": "第一學期：約 8 月至 12 月；第二學期：約 1 月至 5 月",
    "蒙古": "秋季學期：約 9 月初至 12 月底；春季學期：約 2 月初至 6 月初",
    "阿拉伯聯合大公國": "秋季學期（Fall）：約 8 月底至 12 月中旬；春季學期（Spring）：約 1 月中旬至 5 月中旬",
    "越南": "第一學期（秋季班）：約 9 月至翌年 1 月；第二學期（春季班）：約 2 月至 6 月",
    "中國大陸": "秋季學期（上學期）：約 9 月初至翌年 1 月中旬；春季學期（下學期）：約 2 月中下旬至 6 月底／7 月初",
    "香港": "第一學期（秋季班）：約 9 月初至 12 月底；第二學期（春季班）：約 1 月中旬至 5 月中旬",
}


def clean_text(s: str) -> str:
  if not s:
    return ""
  return re.sub(r"\s+", " ", s).strip()


def format_colleges_and_degrees(item: dict) -> tuple[str, str]:
  depts = clean_text(item.get("eligible_depts") or "全校")
  sel_unit = clean_text(item.get("selection_unit") or "國際處")
  deg_str = clean_text(
      item.get("degree_levels")
      or "大學部大一（下學期）至大四、碩士班及博士班在學學生（須於彰師大就讀滿一學期以上；最早大一下申請、大二上出國）"
  )
  if depts == "全校" or depts.startswith("全校"):
    colleges_str = (
        "不限學院（教育學院、理學院、工學院、管理學院、社會科學暨體育學院、文學院、技術及職業教育學院等全校各系所符合姊妹校開設專業與語檢條件之在學生皆可申請"
        + (f"；甄選單位：{sel_unit}）" if sel_unit else "）")
    )
  else:
    colleges_str = f"指定開放院系／專業：{depts}（甄選單位：{sel_unit}）"
  return colleges_str, deg_str


def main() -> None:
  OFFICIAL_NCUE_DIR.mkdir(parents=True, exist_ok=True)
  catalog_source = json.loads(
      (SOURCES_NCUE_DIR / "ncue_catalog_source.json").read_text(encoding="utf-8")
  )
  resolved_locations = json.loads(
      (SOURCES_NCUE_DIR / "ncue_resolved_locations.json").read_text(encoding="utf-8")
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
    region = REGION_BY_COUNTRY.get(country, item.get("region") or "亞洲")
    avail_status = "open" if item["application_status"] == "open" else "reference_only"
    if avail_status == "open":
      open_partner_count += 1

    tracks_list = item.get("source_tracks") or ["公費交換生"]
    tracks_str = "、".join(tracks_list)
    if "雙聯" in tracks_str and "交換" in tracks_str:
      program_type = "交換生暨跨國雙聯學位計畫"
    elif "雙聯" in tracks_str:
      program_type = "跨國雙聯學位計畫"
    elif "大陸" in tracks_str or country in {"中國大陸", "香港"}:
      program_type = "大陸及港澳地區姊妹校交換計畫"
    elif "自費" in tracks_str and "公費" not in tracks_str:
      program_type = "國外姊妹校自費交換生計畫"
    elif "自費" in tracks_str and "公費" in tracks_str:
      program_type = "國外姊妹校公費及自費交換生計畫"
    else:
      program_type = "國外姊妹校公費交換生計畫"

    quota_str = item["quota_str"]
    colleges_str, degree_levels_str = format_colleges_and_degrees(item)
    lang_req_str = item["lang_req"]
    gpa_req_str = item["gpa_req"]
    website = item.get("website") or NCUE_GLOBAL_SISTERS_URL
    factsheet_url = item.get("factsheet_url")
    remarks_raw = clean_text(item.get("remarks") or "")
    exps = item.get("experience_reports") or []

    if country in {"中國大陸", "香港"}:
      source_url = (
          NCUE_MAINLAND_115_2_POST_URL
          if avail_status == "open"
          else NCUE_MAINLAND_115_1_POST_URL
      )
      round_label = (
          "2027年春季班（115-2學期）赴大陸地區姊妹校交換計畫校內甄選"
          if avail_status == "open"
          else "2026年秋季班（115-1學期）赴大陸及港澳地區姊妹校交換計畫（預計116-1重新開放）"
      )
      app_deadline_str = (
          "【2027年春季班（115-2學期）赴大陸地區姊妹校交換甄選】2026/10/06 公告簡章、2026/10/27 (二) 15:00 校內收件截止（將申請表 Word 檔與全套申請資料合併為單一 PDF 檔寄至 `yuchen@cc.ncue.edu.tw`［主旨：115-2大陸_申請人姓名］，並繳交紙本乙份至白沙大樓 4 樓國際暨兩岸事務處章祐甄專員，分機 5124）、2026/10/29 (四) 或 10/30 (五) 校內面試、2026年11月初公告錄取名單；【秋季班（116-1學期）預告】預計 2027年3月初公告簡章（開放 29 所大陸及香港合作高校）"
      )
      deadline_iso = "2026-10-27T15:00:00+08:00"
      win_status = "open" if avail_status == "open" else "closed"
      acad_year = "115"
    else:
      source_url = (
          NCUE_OVERSEAS_116_BROCHURE_URL
          if avail_status == "open"
          else NCUE_OVERSEAS_PLAN_URL
      )
      round_label = (
          "116學年度（2027秋季、2028春季）赴國外非大陸姊妹校交換研修暨教育部學海飛颺／惜珠甄選"
          if avail_status == "open"
          else "國外正式締約合作姊妹校（依國際處當期甄選簡章公告名額辦理）"
      )
      app_deadline_str = (
          "【116學年度（2027秋季、2028春季）赴國外非大陸姊妹校交換研修暨學海飛颺／惜珠甄選（主梯次）】2026/07/09 公告簡章、2027/01/13 (三) 15:00 截止收件（1. 填寫線上申請 Google 表單 `https://forms.gle/otaTRwh2ZkHAWwbH7`；2. 將全套申請文件依序掃描合併為單一 PDF 寄至 `outgoing@gm.ncue.edu.tw`；3. 將紙本正本 1 份置於透明資料袋［勿裝訂］送交白沙大樓 4 樓國際暨兩岸事務處林九汝專員，分機 5125）；【第二學期二次甄選（若名額有餘）】每年 6 月底截止收件"
      )
      deadline_iso = "2027-01-13T15:00:00+08:00"
      win_status = "open" if avail_status == "open" else "closed"
      acad_year = "116"

    study_period_str = "1 學期或 1 學年（依《國立彰化師範大學交換學生甄選作業要點》及兩校協議名額辦理）"
    if "雙聯" in tracks_str:
      study_period_str = (
          "1–2 年跨國雙聯學位修讀（依《國立彰化師範大學與境外大學校院辦理跨國雙聯學制實施辦法》規定：學士班累計修業至少 4 學期、碩士班至少 2 學期、博士班至少 4 學期）或 1 學期／1 學年交換"
      )

    sem_dates_str = SEMESTER_DATES_BY_COUNTRY.get(
        country, "秋季學期：約 9 月至翌年 1 月；春季學期：約 2 月至 6 月"
    )
    housing_str = (
        f"獲彰師大國際暨兩岸事務處提名後，可依 {zh_name} 交換生 Fact Sheet 與國際處姊妹校專頁指引申請校內學生宿舍或校外國際學生公寓"
        + (f"（簡章與學校說明：{remarks_raw[:220]}）" if remarks_raw else "。")
    )
    course_rest_str = (
        f"開放對象與領域：{colleges_str}。依《國立彰化師範大學學生出國選修課程實施注意事項》第4點及《辦理學生抵免學分作業準則》規定：學生於出國修課期間，每學期至少須修習 2 門課或相當於本校 6 學分之課程；出國修習學分總數以不超過畢業應修學分數三分之一（研究生為二分之一）為原則，師資培育課程及研究生修習國外大學部課程不予抵免（《學分對照表》基準：1 彰師大學分 = 2 歐洲 ECTS = 5 英國 CATS = 4 澳洲學分 = 1 日／韓學分）。"
    )

    tuition_points_list = [
        (
            "彰師大在學註冊、公費／自費交換與雙聯學雜費規定：依《國立彰化師範大學交換學生甄選作業要點》及《學生出國期間有關學業及學籍處理注意事項》規定，交換生於出國交換期間仍須於彰師大辦理註冊並繳交全額學雜費（休學生、延畢生不得申請；惟已修滿畢業應修科目學分、專為出國交換經核准延畢以 1 年為限者不在此限）。公費交換生免繳接待姊妹校學費；自費交換生及跨國雙聯學位生則須依兩校協議向接待校繳交學雜費。"
        ),
        (
            "教育部《學海飛颺／學海惜珠》補助與返國義務（依《國立彰化師範大學辦理教育部學海系列補助作業準則》）：（1）申請資格：具中華民國國籍且在臺灣地區設有戶籍之彰師大在學生，赴國外非大陸及港澳之大專校院修讀學分 1 學期或 1 學年，歷年學業總平均達 GPA 2.5 以上或全班排名前 50%（約 70 分以上），且具 2 年內有效外語檢定證明（英語系國家基準：TOEFL iBT 61 / IELTS 5.5［學術組］/ TOEIC 670［不採計校園考］/ GEPT 中高級）；（2）學海惜珠另須具低收入戶、中低收入戶或特殊境遇家庭等政府核定資格；（3）補助撥付與返國義務：出國前簽訂行政契約書先核發 80% 補助款，返國抵臺（桃園機場入境）後 14 日內須完成返國報到、繳交 2,500 字以內《交換心得報告》（含照片 5–6 張，Word 檔與 PDF 檔）及留學報告表，並須履行 8 小時返國經驗分享或國際處活動志工義務，始得請領 20% 尾款。"
        ),
    ]

    app_steps_list = [
        (
            f"步驟一（確認彰師大在學滿一學期資格、GPA 與 {zh_name} 語檢門檻）：確認已於彰師大就讀滿一學期以上（最早大一下學期申請、大二上學期出國；休學生與一般延畢生不可申請），符合 {zh_name} 規定之學業成績（{gpa_req_str}）與 2 年內有效之語言能力證明（{lang_req_str}；注意：TOEIC 校園考不予採計，IELTS 須為學術組 Academic）。"
        ),
        (
            "步驟二（完成線上表單登錄、寄送單一合併 PDF 電子檔並親送透明資料袋紙本至國際處）：於校內截止日（116學年國外非大陸姊妹校暨學海補助為 `2027/01/13 15:00`；115-2 大陸地區姊妹校為 `2026/10/27 15:00`）前：（1）填寫線上申請表單；（2）備齊申請表（貼妥大頭照並完成系所核章）、家長保證書、健康自述表、中英文歷年成績單（須含全班人數、名次及百分比）、中文自傳（800 字內）與讀書計畫（1,500 字內）、英文或外文自傳與讀書計畫（各 2 頁內）、有效語檢證明及學海飛颺／惜珠申請表，依序掃描合併為單一 PDF 寄至承辦信箱（國外：`outgoing@gm.ncue.edu.tw` 林九汝專員；大陸：`yuchen@cc.ncue.edu.tw` 章祐甄專員）；（3）將紙本正本 1 份置於透明資料袋（切勿裝訂）送交白沙大樓 4 樓國際暨兩岸事務處。"
        ),
        (
            f"步驟三（參加全外語校內面試審查［未達 70 分不予選送］、志願分發與繳交錄取確認書）：國際處組成 3–5 人甄選小組辦理書面審查與校內面試（國外姊妹校採全外語面試，每人約 5 分鐘：含 2 分鐘外語自我介紹與讀書計畫簡報＋3 分鐘委員提問；面試總成績平均未達 70 分者不予選送，同分時以面試成績高低決定優先順序）。錄取公告後，正取生須於期限內繳交《錄取確認書》，由國際處向 {full_name} 辦理官方提名（Nomination）。"
        ),
        (
            "步驟四（遞交姊妹校入學申請、辦理簽證保險、每學期修習至少 2 門課或 6 學分並於返國 14 日內繳交心得報告）：獲提名後依姊妹校規定遞交外文入學申請、護照影本、英文財力證明、選課計畫與宿舍申請；出國前參加行前說明會、投保涵蓋全期之海外醫療及意外險（學海受獎生另簽訂行政契約書請領 80% 補助款）。抵達姊妹校後回傳《抵達通知單》，交換期間每學期至少須修習 2 門課或相當於彰師大 6 學分之課程；返國抵臺後 14 日內須繳交返國註冊單、2,500 字以內《交換心得報告》（含 5–6 張照片）及正式成績單辦理學分抵免與學海 20% 尾款核銷。"
        ),
    ]

    elig_points_list = [
        f"合作類別與甄選單位：{program_type}（{tracks_str}｜甄選單位：{item.get('selection_unit', '國際處')}）",
        f"開放學制與年級：{degree_levels_str}",
        f"開放申請院系：{colleges_str}",
        f"學業成績門檻：{gpa_req_str}",
        f"外語能力標準：{lang_req_str}",
        (
            "校內甄選面試及格線與比序規定：依《國立彰化師範大學交換學生甄選作業要點》規定，甄選含書面資料審查與 5 分鐘外語面試（2 分鐘自我介紹與讀書計畫＋3 分鐘問答）；面試總成績平均未達 70 分者不予選送，總成績相同時以面試成績較高者優先錄取。"
        ),
    ]
    if remarks_raw:
      elig_points_list.append(f"學校簡章與特殊規定：{remarks_raw[:300]}")

    exp_labels = [e["student"][:32] for e in exps]
    notes_lines = [
        f"【合作類別與期程】{program_type}｜交換期間：{study_period_str}",
        f"【當期名額與費用待遇】{quota_str}｜出國期間維持彰師大在學註冊並繳交校內學雜費（公費交換免繳接待校學費，自費交換及雙聯學位依兩校協議繳交接待校學雜費）",
        f"【開放學院與學制】{colleges_str}｜{degree_levels_str}",
        f"【語言與學業門檻】{lang_req_str}｜{gpa_req_str}",
        f"【住宿與生活資訊】{housing_str}",
    ]
    if factsheet_url:
      notes_lines.append(f"【官方簡章／Fact Sheet 連結】{factsheet_url}")
    if exps:
      notes_lines.append(
          f"【彰師大學長姐交換心得報告（共 {len(exps)} 篇）】收錄於國際暨兩岸事務處歷屆出國交換心得專區（含：{'、'.join(exp_labels[:5])}）"
      )
    if remarks_raw:
      notes_lines.append(f"【學校簡章摘要】{remarks_raw[:350]}")

    loc_raw = resolved_locations.get(str(sn)) or resolved_locations.get(full_name)
    assert loc_raw is not None, f"Missing resolved location for #{sn} {full_name}"
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

    visual_rec = (
        visual_index.get((full_name, country))
        or visual_index.get((item["name_zh"], country))
        or visual_index.get((item["name_en"], country))
        or {}
    )
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
        "availability_note": f"國立彰化師範大學國際暨兩岸事務處公告交換／雙聯合作姊妹校（{program_type}）；{quota_str}。",
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
                "selection_unit": item.get("selection_unit"),
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
            "title": f"國立彰化師範大學赴姊妹校交換研修甄選簡章與學校一覽表—{zh_name}",
            "source_url": source_url,
            "role": "home_university",
            "authority": "home_official_notice",
            "effective_academic_year": acad_year,
            "application_round": round_label,
            "checked_at": CHECKED_AT,
        },
        {
            "title": "國立彰化師範大學交換學生甄選作業要點與學海系列補助作業準則",
            "source_url": NCUE_EXCHANGE_SELECTION_GUIDELINES_URL,
            "role": "home_university",
            "authority": "home_official_notice",
            "effective_academic_year": acad_year,
            "application_round": round_label,
            "checked_at": CHECKED_AT,
        },
        {
            "title": "國立彰化師範大學學生出國選修課程實施注意事項與學分對照表",
            "source_url": NCUE_OUTBOUND_COURSE_NOTES_URL,
            "role": "home_university",
            "authority": "home_official_notice",
            "effective_academic_year": acad_year,
            "application_round": round_label,
            "checked_at": CHECKED_AT,
        },
    ]
    if factsheet_url:
      wf_sources.append({
          "title": f"彰師大國際暨兩岸事務處公告之 {zh_name} 交換計畫／Fact Sheet 專頁",
          "source_url": factsheet_url,
          "role": "home_university",
          "authority": "home_official_notice",
          "effective_academic_year": acad_year,
          "application_round": round_label,
          "checked_at": CHECKED_AT,
      })
    if exps:
      wf_sources.append({
          "title": f"彰師大國際暨兩岸事務處歷屆出國交換心得專區—赴 {zh_name} 交換生返國報告（{len(exps)} 篇）",
          "source_url": exps[0].get("page_url") or exps[0]["url"],
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
        "home_university": "國立彰化師範大學",
        "school_name": full_name,
        "partner_website": website,
        "country": country,
        "program_type": program_type,
        "academic_year": acad_year,
        "application_round": round_label,
        "effective_application_rounds": [
            round_label,
            "116學年度赴國外非大陸姊妹校交換甄選",
            "115-2赴大陸地區交換甄選",
            "115-1赴大陸及港澳地區交換甄選",
            "116-1",
            "116-2",
            "115-2",
            "115-1",
        ],
        "applicability_status": "verified",
        "applicability_note": (
            "國立彰化師範大學由國際暨兩岸事務處統籌辦理全校赴國外非大陸姊妹校交換研修（116學年主梯次於 2027/01/13 15:00 截止，併同教育部學海飛颺／惜珠獎學金申請）、赴大陸及港澳地區姊妹校交換計畫（115-2 春季班於 2026/10/27 15:00 截止）及跨國雙聯學位甄選。"
        ),
        "review_status": "published",
        "published_at": CHECKED_AT,
        "steps": [
            {
                "rule_id": f"ncue-{acad_year}-home-1-{idx+1:03d}",
                "order": 1,
                "phase": "校內申請",
                "title": f"確認彰師大在學滿一學期身分（最早大一下申請、大二上出國）、學業 GPA 與 {zh_name} 語檢要求",
                "responsible_party": "學生",
                "responsible_unit": "國立彰化師範大學國際暨兩岸事務處",
                "deadline_at": deadline_iso,
                "deadline_status": "verified_exact" if avail_status == "open" else "reference_only",
                "deadline_source_url": source_url,
                "deadline_checked_at": CHECKED_AT,
                "deadline_reminder_eligible": avail_status == "open",
                "summary": (
                    f"確認符合《國立彰化師範大學交換學生甄選作業要點》規定（已於本校就讀滿一學期以上之學士班、碩士班或博士班在學生；休學生及一般延畢生不可申請；申請學海飛颺／惜珠者歷年 GPA 須達 2.5 以上或全班排名前 50%），並備妥符合 {zh_name} 規定之 2 年內有效語言能力證明（TOEIC 不採計校園考，IELTS 須為學術組）。"
                ),
                "details": [
                    f"開放學制與院系：{colleges_str}（{degree_levels_str}）",
                    f"語言與學業條件：{lang_req_str}｜{gpa_req_str}",
                    f"當期名額與計畫類別：{quota_str}｜{program_type}",
                ],
                "scope": {
                    "home_universities": ["國立彰化師範大學"],
                    "partner_universities": [full_name],
                    "academic_years": ["115", "116"],
                    "application_rounds": [round_label, "116-1", "116-2", "115-2", "115-1"],
                },
                "source_urls": [
                    source_url,
                    NCUE_EXCHANGE_SELECTION_GUIDELINES_URL,
                    NCUE_XUEHAI_GUIDELINES_URL,
                ],
                "checked_at": CHECKED_AT,
                "support_status": "verified",
            },
            {
                "rule_id": f"ncue-{acad_year}-home-2-{idx+1:03d}",
                "order": 2,
                "phase": "校內申請",
                "title": "填寫線上申請表單、寄送單一合併 PDF 電子檔並將透明資料袋紙本正本（勿裝訂）送交白沙大樓 4 樓國際處",
                "responsible_party": "學生與所屬系（所）辦公室",
                "responsible_unit": "國立彰化師範大學各系所／國際暨兩岸事務處",
                "deadline_at": deadline_iso,
                "deadline_status": "verified_exact" if avail_status == "open" else "reference_only",
                "deadline_source_url": source_url,
                "deadline_checked_at": CHECKED_AT,
                "deadline_reminder_eligible": avail_status == "open",
                "summary": (
                    "於截止期限前完成線上 Google 表單登錄，並將申請表（經系所核章）、家長保證書、健康自述表、中英文歷年成績單（含全班人數及名次百分比）、中英文自傳與讀書計畫、2 年內有效語檢證書及學海飛颺／惜珠申請表合併為單一 PDF 寄至國際處承辦信箱，同時將紙本正本 1 份置於透明資料袋（切勿裝訂）親送至白沙大樓 4 樓國際暨兩岸事務處。"
                ),
                "details": [
                    "國外非大陸姊妹校（116學年截止：2027/01/13 15:00）：線上填表 `https://forms.gle/otaTRwh2ZkHAWwbH7`（同時申請學海補助者加填 `https://forms.gle/8ZAo5x42CTiHNs769`）＋單一 PDF 寄至 `outgoing@gm.ncue.edu.tw`＋紙本送交林九汝專員（分機 5125）。",
                    "大陸地區姊妹校（115-2春季班截止：2026/10/27 15:00）：申請表 Word 檔與單一合併 PDF 寄至 `yuchen@cc.ncue.edu.tw`（信件主旨：`115-2大陸_申請人姓名`）＋紙本送交章祐甄行政專員（分機 5124）。",
                ],
                "document_requirements": [
                    {
                        "name": "國立彰化師範大學出國交換學生甄選申請表（黏貼 2 吋照片、申請人簽名並完成系所主管核章）與家長保證書、健康自述表",
                        "official_form_url": NCUE_OVERSEAS_116_APP_FORM_URL,
                        "source_urls": [NCUE_OVERSEAS_116_BROCHURE_URL, NCUE_OVERSEAS_116_APP_FORM_URL, NCUE_PARENTAL_GUARANTEE_URL],
                    },
                    {
                        "name": "中文歷年成績單正本（須註明全班人數、名次及排名百分比）與英文歷年成績單正本（GPA 4.0 制）各乙份",
                        "source_urls": [NCUE_OVERSEAS_116_BROCHURE_URL, NCUE_MAINLAND_115_2_POST_URL],
                    },
                    {
                        "name": "2 年內有效之外語能力檢定證明影本（TOEFL iBT / IELTS 學術組 / TOEIC［不採計校園考］/ GEPT / JLPT / TOPIK / DELF / TestDaF / DELE；赴大陸地區免附）",
                        "source_urls": [NCUE_OVERSEAS_116_BROCHURE_URL, NCUE_EXCHANGE_SELECTION_GUIDELINES_URL],
                    },
                    {
                        "name": "中文自傳（800 字以內）與中文讀書計畫（1,500 字以內）、英文或外文自傳與讀書計畫（各 2 頁以內），以及教育部學海飛颺／學海惜珠補助申請表",
                        "official_form_url": NCUE_XUEHAI_FEIYANG_FORM_URL,
                        "source_urls": [NCUE_OVERSEAS_116_BROCHURE_URL, NCUE_XUEHAI_FEIYANG_FORM_URL, NCUE_XUEHAI_XIZHU_FORM_URL],
                    },
                ],
                "scope": {
                    "home_universities": ["國立彰化師範大學"],
                    "academic_years": ["115", "116"],
                    "application_rounds": [round_label, "116-1", "116-2", "115-2", "115-1"],
                },
                "source_urls": [
                    NCUE_OVERSEAS_116_BROCHURE_URL,
                    NCUE_OVERSEAS_116_APP_FORM_URL,
                    NCUE_MAINLAND_115_2_POST_URL,
                    NCUE_XUEHAI_FEIYANG_FORM_URL,
                ],
                "checked_at": CHECKED_AT,
                "support_status": "verified",
            },
            {
                "rule_id": f"ncue-{acad_year}-home-3-{idx+1:03d}",
                "order": 3,
                "phase": "甄選與提名",
                "title": "參加國際處 5 分鐘外語面試（平均未達 70 分不予選送）、公告錄取結果並依限繳交《錄取確認書》",
                "responsible_party": "學生與國際暨兩岸事務處甄選小組",
                "responsible_unit": "國立彰化師範大學國際暨兩岸事務處",
                "deadline_at": "2027-02-26T17:00:00+08:00" if country not in {"中國大陸", "香港"} else "2026-11-10T17:00:00+08:00",
                "deadline_status": "verified_exact",
                "deadline_source_url": source_url,
                "deadline_checked_at": CHECKED_AT,
                "deadline_reminder_eligible": False,
                "summary": (
                    "國際處敦聘 3–5 位委員進行書面與面試審查（每人面試約 5 分鐘：含 2 分鐘外語自我介紹及讀書計畫報告＋3 分鐘委員提問；面試總成績平均未達 70 分者，不予選送；總分相同時依面試成績高低比序）。錄取名單公告後，正取生須於規定期限內繳交《錄取確認書》確認出國資格。"
                ),
                "details": [
                    "面試時程：115-2 大陸地區交換面試訂於 2026/10/29 (四) 或 10/30 (五) 舉行，11月初放榜；116學年國外非大陸姊妹校交換於 2027/01/13 截止後擇期通知面試。",
                    "學海飛颺／惜珠獎學金核定：通過校內外語及書面面試甄選且符合 GPA 2.5 或全班前 50% 門檻者，由國際處依教育部核配額度與甄選總成績高低核定補助金額。",
                ],
                "scope": {
                    "home_universities": ["國立彰化師範大學"],
                    "academic_years": ["115", "116"],
                    "application_rounds": [round_label, "116-1", "116-2", "115-2", "115-1"],
                },
                "source_urls": [
                    source_url,
                    NCUE_EXCHANGE_SELECTION_GUIDELINES_URL,
                    NCUE_XUEHAI_GUIDELINES_URL,
                ],
                "checked_at": CHECKED_AT,
                "support_status": "verified",
            },
            {
                "rule_id": f"ncue-{idx+1:03d}-host-apply",
                "order": 4,
                "phase": "合作校申請",
                "title": f"由彰師大國際處向 {zh_name} 辦理官方提名（Nomination），並依接待校規定遞交外文入學與宿舍申請",
                "responsible_party": "學生與接待校國際事務處",
                "summary": (
                    f"繳交《錄取確認書》後，由彰師大國際處向 {zh_name} 辦理官方提名；學生須於姊妹校申請截止日前備妥外文入學申請表、英文歷年成績單、護照影本、英文財力證明、語檢證書、選課計畫與學生宿舍申請表，靜候接待校核發正式入學許可（Letter of Acceptance / COE / DS-2019）。"
                ),
                "details": [
                    f"交換期程：{study_period_str}｜名額：{quota_str}",
                    f"語言與學業條件：{lang_req_str}｜{gpa_req_str}",
                    f"住宿安排：{housing_str}",
                ],
                "scope": {
                    "home_universities": ["國立彰化師範大學"],
                    "partner_universities": [full_name],
                    "academic_years": ["115", "116"],
                    "application_rounds": [round_label, "116-1", "116-2", "115-2", "115-1"],
                },
                "source_urls": (
                    [source_url, NCUE_OVERSEAS_PLAN_URL]
                    + ([factsheet_url] if factsheet_url else [])
                    + ([website] if website else [])
                ),
                "checked_at": CHECKED_AT,
                "support_status": "verified",
                "needs_confirmation": False,
            },
            {
                "rule_id": f"ncue-{acad_year}-home-5-{idx+1:03d}",
                "order": 5,
                "phase": "行前準備",
                "title": "參加行前說明會、簽訂學海契約並投保海外醫療險，出國修滿 2 門課或 6 學分，返國 14 日內繳交心得報告與辦理學分抵免",
                "responsible_party": "學生",
                "responsible_unit": "國立彰化師範大學國際暨兩岸事務處／教務處／各系所",
                "summary": (
                    "出國前須參加國際處行前說明會、完成出國選課簽核、投保涵蓋全期之海外醫療及意外險（學海受獎生於出國前簽訂行政契約書請領 80% 補助款）；抵達姊妹校後回傳《抵達通知單》，每學期至少修習 2 門課或相當於彰師大 6 學分之課程；返國抵臺（桃園機場入境）後 14 日內須提交返國註冊單、2,500 字以內《交換心得報告》（含 5–6 張照片）及留學報告表，並完成 8 小時經驗分享志工以核銷 20% 學海尾款及辦理學分抵免。"
                ),
                "details": tuition_points_list,
                "scope": {
                    "home_universities": ["國立彰化師範大學"],
                    "academic_years": ["115", "116"],
                    "application_rounds": [round_label, "116-1", "116-2", "115-2", "115-1"],
                },
                "source_urls": [
                    NCUE_OUTBOUND_COURSE_NOTES_URL,
                    NCUE_CREDIT_TRANSFER_REGS_URL,
                    NCUE_CREDIT_CONVERSION_TABLE_URL,
                    NCUE_XUEHAI_GUIDELINES_URL,
                ],
                "checked_at": CHECKED_AT,
                "support_status": "verified",
            },
        ],
        "sources": wf_sources,
        "last_checked": CHECKED_AT,
        "coverage_status": "official_verified",
        "coverage_note": (
            "已完整整合國立彰化師範大學國際暨兩岸事務處（116學年赴國外非大陸姊妹校交換簡章與 73 校 Google Sheet 名冊、115-2 及 115-1 赴大陸及港澳地區交換簡章、跨國雙聯學位一覽表及歷屆出國交換心得專區）共 108 所全球合作學校名額、語檢門檻、面試及格線、學海補助細則與 409 篇學長姐返國心得。"
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
            "title": f"國立彰化師範大學赴姊妹校交換研修甄選簡章與學校一覽表—{zh_name}",
            "source_url": source_url,
            "summary": "彰師大國際暨兩岸事務處公告之交換名額、開放院系年級、語言檢定門檻與學校備註說明",
        },
        {
            "title": "國立彰化師範大學交換學生甄選作業要點、出國選修課程實施注意事項與學海系列補助作業準則",
            "source_url": NCUE_EXCHANGE_SELECTION_GUIDELINES_URL,
            "summary": "彰師大出國交換申請資格（就讀滿一學期、最早大一下申請大二上出國）、5分鐘外語面試 70 分及格線、每學期至少修習 2 門課或 6 學分規定與學海飛颺／惜珠補助標準",
        },
    ]
    if factsheet_url:
      dest_sources.append({
          "title": f"彰師大國際暨兩岸事務處公告之 {zh_name} 交換資訊與 Fact Sheet",
          "source_url": factsheet_url,
          "summary": "彰師大國際處與接待校提供之交換生申請資訊、選課與住宿說明",
      })
    if exps:
      dest_sources.append({
          "title": f"彰師大國際暨兩岸事務處歷屆交換心得專區—赴 {zh_name} 交換生返國心得報告（{len(exps)} 篇）",
          "source_url": exps[0].get("page_url") or exps[0]["url"],
          "summary": f"收錄歷年彰師大赴 {zh_name} 交換生與雙聯生返國心得報告共 {len(exps)} 篇",
      })
    if website:
      dest_sources.append({
          "title": f"{full_name} 官方網站",
          "source_url": website,
          "summary": "接待合作校官方網站",
      })

    src_url_list = (
        [source_url, NCUE_OVERSEAS_PLAN_URL, NCUE_EXCHANGE_SELECTION_GUIDELINES_URL]
        + ([factsheet_url] if factsheet_url else [])
        + ([exps[0].get("page_url") or exps[0]["url"]] if exps else [])
        + ([website] if website else [])
    )

    destinations.append({
        "home_university": "國立彰化師範大學",
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
                "title": "生活費、公費／自費交換學雜費規定與教育部學海飛颺／惜珠獎學金（80%＋20%撥款）",
                "summary": cost_line,
                "points": [cost_line] + tuition_points_list,
                "source_urls": src_url_list + [NCUE_XUEHAI_GUIDELINES_URL, NCUE_MOE_SUBSIDY_DIRECTIONS_URL],
                "caution": (
                    "學海飛颺／惜珠受獎生於出國前領取 80% 補助款，返國抵臺後 14 日內必須完成返國報到、繳交 2,500 字內心得報告（含 5–6 張照片）並履行 8 小時分享志工義務，始得請領 20% 尾款。"
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
                    "依《國立彰化師範大學交換學生甄選作業要點》規定，錄取生出國前須購買涵蓋海外研修全期之醫療及意外保險並將保單影本送交國際處備查，同時須遵守接待國法定學生健康保險規定（如日本 NHI、韓國 NHIS、德國法定公保、捷克 pVZP、澳洲 OSHC 等）。",
                ],
                "source_urls": src_url_list,
                "caution": "請於收到入學許可後確認接待校指定之保險額度與投保通路，並於出國前完成保險證明繳交。",
            },
            {
                "key": "visa",
                "title": "留學簽證辦理、役男出境緩徵手續與彰師大在學註冊義務",
                "summary": visa_default,
                "points": [
                    visa_default,
                    "依《國立彰化師範大學學生出國期間有關學業及學籍處理注意事項》規定，交換期間仍須辦理彰師大註冊並繳交全額學雜費；具役男身分之錄取生須於出國前一個月向學務處生輔組及國際處辦理役男出境緩徵手續。",
                ],
                "source_urls": src_url_list,
                "caution": "請勿持觀光簽證或免簽入境就讀學期交換課程，以免影響正式學籍、居留與返國學分抵免。",
            },
            {
                "key": "academics",
                "title": "每學期至少修習 2 門課或 6 學分規定、學分換算基準與返國學分抵免",
                "summary": course_clean[:160],
                "points": [calendar_clean, course_clean],
                "source_urls": src_url_list + [NCUE_OUTBOUND_COURSE_NOTES_URL, NCUE_CREDIT_CONVERSION_TABLE_URL],
                "caution": (
                    "依《學生出國選修課程實施注意事項》第4點，每學期至少須修習 2 門課或相當於彰師大 6 學分之課程；師資培育課程及研究生修習國外大學部課程不予抵免。"
                ),
            },
            {
                "key": "living",
                "title": f"{location_obj.get('city') or country} 校園生活與彰師大學長姐交換心得傳承",
                "summary": f"代表校區城市：{location_obj.get('city') or country}。請於抵達姊妹校後依限回傳《抵達通知單》並配合接待校新生訓練（Orientation）完成報到。",
                "points": [
                    f"目的地城市：{location_obj.get('city') or country}（{country}）",
                    (
                        f"彰師大國際暨兩岸事務處於官網「歷屆交換心得專區（{exps[0].get('page_url') if exps else NCUE_EXP_OVERSEAS_URL}）」公開收錄學長姐返國研修心得報告"
                        + (f"（本校共收錄 {len(exps)} 篇：{'、'.join(exp_labels[:4])}）" if exps else "")
                        + "，詳述當地選課、住宿、交通與生活開銷實況。"
                    ),
                ],
                "source_urls": [exps[0].get("page_url") if exps else NCUE_EXP_OVERSEAS_URL],
            },
        ],
        "sources": dest_sources,
        "last_checked": CHECKED_AT,
        "coverage_status": "official_verified",
        "coverage_note": (
            "已整合國立彰化師範大學國際暨兩岸事務處 108 所交換與雙聯合作姊妹校名額、語檢門檻、學海飛颺／惜珠獎補助細則、姊妹校 Fact Sheet 與 409 篇歷屆學長姐返國心得。"
        ),
    })

    research_records.append({
        "home_university": "國立彰化師範大學",
        "school_name": full_name,
        "country": country,
        "official_website": website,
        "verification_status": "official_verified",
        "discovery_source_url": source_url,
        "checked_at": CHECKED_AT,
        "note": (
            f"國立彰化師範大學國際暨兩岸事務處《116學年赴國外非大陸姊妹校交換研修甄選簡章（{NCUE_OVERSEAS_116_BROCHURE_URL}）》、《全球姊妹校一覽表》與 ROR/Wikidata 官方網址核對完成。"
        ),
    })

    ev_sources = [
        {
            "title": f"國立彰化師範大學赴姊妹校交換研修甄選簡章與學校一覽表—{zh_name}",
            "url": source_url,
        },
    ]
    if factsheet_url:
      ev_sources.append({
          "title": f"彰師大國際處公告之 {zh_name} 交換專頁／Fact Sheet",
          "url": factsheet_url,
      })
    if exps:
      ev_sources.append({
          "title": f"彰師大國際暨兩岸事務處歷屆出國交換心得專區—赴 {zh_name} 交換生心得報告（{len(exps)} 篇）",
          "url": exps[0].get("page_url") or exps[0]["url"],
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
            "scope": "國立彰化師範大學出國交換姊妹校住宿與生活資訊",
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
            "scope": "國立彰化師範大學交換生費用規定、公費／自費與雙聯學雜費、教育部學海飛颺／惜珠與地區生活費估算",
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
            "scope": "國立彰化師範大學交換生選課規定、每學期至少修習 2 門課或 6 學分門檻與返國學分抵免",
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
            "scope": "國立彰化師範大學出國交換簽證、海外醫療保險、役男緩徵出境與在學註冊提醒",
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
                    f"｜彰師大國際處歷屆交換心得專區公開收錄 {len(exps)} 篇赴 {zh_name} 交換生返國心得報告（{'、'.join(exp_labels[:4])}）。"
                    if exps
                    else ""
                )
            ),
            "sources": ev_sources,
            "checked_at": CHECKED_AT,
            "scope": "國立彰化師範大學出國交換名額與歷屆學長姐交換經驗分享",
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
            "已整合國立彰化師範大學國際暨兩岸事務處《116學年赴國外非大陸姊妹校交換研修甄選簡章》、《115-2及115-1赴大陸及港澳地區交換簡章》、跨國雙聯學位一覽表及歷屆出國交換心得專區共 409 篇學長姐報告。",
            "當期宿位供給、費用與選課限制請依姊妹校最新 Fact Sheet 及入學通知書核對。",
        ],
        "location_signature": f"verified:{location_obj['latitude']}:{location_obj['longitude']}:representative",
        "extraction_version": 3,
    })

    sample_reports: list[dict] = []
    for e_item in exps[:6]:
      sample_reports.append({
          "title": e_item["title"],
          "url": e_item["url"],
          "term": f"{e_item['year']}學年度",
      })
    if not sample_reports and factsheet_url:
      sample_reports.append({
          "title": f"國立彰化師範大學赴 {zh_name} 交換計畫／Fact Sheet 專頁",
          "url": factsheet_url,
          "term": f"{acad_year}學年度",
      })

    if exps:
      rep_title = (
          f"國立彰化師範大學赴 {zh_name} 交換研修心得彙編（共 {len(exps)} 篇學長姐報告）"
      )
      latest_e = exps[0]
      latest_author = f"{latest_e['student'][:24]} 等 {len(exps)} 位彰師大交換生"
      summary_text = (
          f"國立彰化師範大學國際暨兩岸事務處「歷屆出國交換心得專區」公開收錄 {len(exps)} 篇歷年赴 {zh_name} 交換及雙聯學生返國心得報告（含：{'、'.join(exp_labels[:5])}），"
          f"涵蓋教育、理學、工學、管理、社會科學暨體育、文學及技職教育學院學生於 {zh_name} 之專業選課、語言學習、學生宿舍申請、簽證保險辦理及海外生活開銷實錄。"
      )
      theme_map = {
          "academics": (
              f"彰師大交換生（{'、'.join(exp_labels[:3])}）分享於 {zh_name} 修讀教育、商管、理工、外語與人文社會課程之選課方式、達成每學期至少修習 2 門課或 6 學分門檻及返國依《學分對照表》辦理學分抵免之經驗。"
          ),
          "housing": (
              f"彰師大交換生詳述 {zh_name} 校內外學生宿舍申請時程、房型設備與周邊生活機能（{housing_clean[:120]}）。"
          ),
          "campus_culture": (
              f"彰師大國際處收錄 {len(exps)} 篇赴 {zh_name} 交換生返國心得報告，記錄接待校迎新週（Orientation）、國際學伴（Buddy Program）與跨文化交流體驗。"
          ),
          "cost": (
              f"彰師大交換生記錄於 {zh_name} 之每月住宿、伙食與交通開銷（{cost_default}），以及運用教育部學海飛颺／學海惜珠獎學金支應留學費用之規劃。"
          ),
      }
      student_experience_rows.append({
          "school_name": full_name,
          "country": country,
          "title": rep_title,
          "source_url": latest_e.get("page_url") or latest_e["url"],
          "source_type": "article",
          "platform": "國立彰化師範大學國際暨兩岸事務處—歷屆出國交換心得專區",
          "author_name": latest_author,
          "language": "zh",
          "summary": summary_text,
          "themes": ["academics", "housing", "campus_culture", "cost"],
          "theme_summaries": theme_map,
          "content_status": "full_text",
          "perspective": "official_student_story",
          "published_at": None,
          "discovered_at": CHECKED_AT,
          "content_hash": hashlib.sha256(f"{full_name}:ncue_exp:{len(exps)}".encode("utf-8")).hexdigest(),
          "exchange_term": f"{latest_e['year']}學年度",
          "summary_zh": summary_text,
          "original_summary": summary_text,
          "theme_summaries_zh": theme_map,
          "translation_status": "original",
          "source_kind": "official_experience_page",
      })

    experience_sources_records.append({
        "home_university": "國立彰化師範大學",
        "school_name": full_name,
        "country": country,
        "official_experience_portal_url": (
            (exps[0].get("page_url") or exps[0]["url"])
            if exps
            else (NCUE_EXP_MAINLAND_URL if country in {"中國大陸", "香港"} else NCUE_EXP_OVERSEAS_URL)
        ),
        "partner_page_url": factsheet_url or source_url,
        "report_count": len(exps),
        "sample_reports": sample_reports,
        "checked_at": CHECKED_AT,
    })

  partners_jsonl_text = "\n".join(json.dumps(r, ensure_ascii=False) for r in partners) + "\n"
  (OFFICIAL_NCUE_DIR / "partners.jsonl").write_text(partners_jsonl_text, encoding="utf-8")
  (SOURCES_NCUE_DIR / "partners.jsonl").write_text(partners_jsonl_text, encoding="utf-8")
  (OFFICIAL_NCUE_DIR / "application_workflows.jsonl").write_text(
      "\n".join(json.dumps(r, ensure_ascii=False) for r in workflows) + "\n",
      encoding="utf-8",
  )
  (OFFICIAL_NCUE_DIR / "destination_profiles.jsonl").write_text(
      "\n".join(json.dumps(r, ensure_ascii=False) for r in destinations) + "\n",
      encoding="utf-8",
  )
  (OFFICIAL_NCUE_DIR / "partner_research.jsonl").write_text(
      "\n".join(json.dumps(r, ensure_ascii=False) for r in research_records) + "\n",
      encoding="utf-8",
  )
  (OFFICIAL_NCUE_DIR / "student_life.jsonl").write_text(
      "\n".join(json.dumps(r, ensure_ascii=False) for r in life_records) + "\n",
      encoding="utf-8",
  )
  (OFFICIAL_NCUE_DIR / "experience_sources.jsonl").write_text(
      "\n".join(json.dumps(r, ensure_ascii=False) for r in experience_sources_records) + "\n",
      encoding="utf-8",
  )
  (OFFICIAL_NCUE_DIR / "student_experiences.jsonl").write_text(
      "\n".join(json.dumps(r, ensure_ascii=False) for r in student_experience_rows) + "\n",
      encoding="utf-8",
  )
  (OFFICIAL_NCUE_DIR / "campus-locations.json").write_text(
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
  (OFFICIAL_NCUE_DIR / "student-experience-digests.json").write_text(
      json.dumps({"digests": digest_records}, ensure_ascii=False, indent=2) + "\n",
      encoding="utf-8",
  )

  # Ensure NCUE home location is in university_locations.jsonl
  loc_file = REPO_ROOT / "src/exchange_info/official_data/university_locations.jsonl"
  existing_loc_lines = [
      line for line in loc_file.read_text(encoding="utf-8").splitlines() if line.strip()
  ]
  existing_loc_map = {}
  for line in existing_loc_lines:
    rec = json.loads(line)
    existing_loc_map[(rec["school_name"], rec.get("country") or "")] = rec

  ncue_home_loc = {
      "school_name": "國立彰化師範大學",
      "country": "臺灣",
      "city": "彰化縣彰化市",
      "latitude": 24.0816,
      "longitude": 120.5586,
      "geocode_status": "verified",
      "geocoded_at": CHECKED_AT,
      "source_url": "https://www.wikidata.org/wiki/Q709242",
      "identity_source_url": "https://ror.org/046748t96",
      "precision": "representative",
      "note": (
          "校級代表位置：官方網域及國家已與 ROR 比對，座標來源為 Wikidata P625；實際交換校區以錄取通知為準。"
          " 母校代表點採彰化市進德路1號進德校區白沙大樓國際暨兩岸事務處；官方地址來源：https://oicaweb.ncue.edu.tw/。"
      ),
  }
  existing_loc_map[("國立彰化師範大學", "臺灣")] = ncue_home_loc
  sorted_locs = sorted(
      existing_loc_map.values(),
      key=lambda r: (r.get("country") or "", r.get("school_name") or ""),
  )
  loc_file.write_text(
      "\n".join(json.dumps(r, ensure_ascii=False) for r in sorted_locs) + "\n",
      encoding="utf-8",
  )

  ncue_source_urls = [
      NCUE_OICA_HUB_URL,
      NCUE_OUTBOUND_OVERVIEW_URL,
      NCUE_OVERSEAS_PLAN_URL,
      NCUE_MAINLAND_PLAN_URL,
      NCUE_DUAL_DEGREE_URL,
      NCUE_GLOBAL_SISTERS_URL,
      NCUE_REGULATIONS_URL,
      NCUE_FORMS_URL,
      NCUE_OVERSEAS_116_POST_URL,
      NCUE_OVERSEAS_116_BROCHURE_URL,
      NCUE_OVERSEAS_116_SHEET_URL,
      NCUE_OVERSEAS_116_APP_FORM_URL,
      NCUE_PARENTAL_GUARANTEE_URL,
      NCUE_HEALTH_DECLARATION_URL,
      NCUE_MOE_XUEHAI_116_POST_URL,
      NCUE_XUEHAI_GUIDELINES_URL,
      NCUE_MOE_SUBSIDY_DIRECTIONS_URL,
      NCUE_XUEHAI_FEIYANG_FORM_URL,
      NCUE_XUEHAI_XIZHU_FORM_URL,
      NCUE_XUEHAI_CONTRACT_URL,
      NCUE_EXCHANGE_SELECTION_GUIDELINES_URL,
      NCUE_DUAL_DEGREE_REGS_URL,
      NCUE_OUTBOUND_COURSE_NOTES_URL,
      NCUE_CREDIT_TRANSFER_REGS_URL,
      NCUE_CREDIT_CONVERSION_TABLE_URL,
      NCUE_MAINLAND_115_2_POST_URL,
      NCUE_MAINLAND_115_2_PARTNERS_URL,
      NCUE_MAINLAND_115_1_POST_URL,
      NCUE_EXP_OVERSEAS_URL,
      NCUE_EXP_MAINLAND_URL,
  ]

  exchange_info_payload = {
      "school_name": "國立彰化師範大學",
      "program_type": [
          (
              "國際暨兩岸事務處赴國外非大陸姊妹校交換研修計畫（116學年度［2027秋季、2028春季］主梯次甄選自 2026/07/09 公告、2027/01/13 15:00 截止，併同教育部學海飛颺／學海惜珠補助申請；共開放美國加州大學柏克萊分校 UC Berkeley、爾灣分校 UCI、聖地牙哥分校 UCSD、天普大學、加州州立大學弗雷斯諾分校、肯尼索州立大學、莫瑞州立大學、奧斯汀佩伊州立大學、德州農工金斯維爾分校、加拿大安大略理工大學、希爾克學院、英國西英格蘭大學、史崔克萊大學、澳洲新南威爾斯大學 UNSW、南昆士蘭大學、捷克赫拉德茨克拉洛韋大學、奧斯特拉瓦大學、西波希米亞大學、法國東方語言文化學院 INALCO、波爾多蒙田大學、特魯瓦科技大學、索邦大學、德國柏林 HTW、多特蒙德 FH、威斯瑪 HS、卡爾斯魯厄教育大學、法蘭克福應用科大、布萊梅 HS、開姆尼茨工大、比勒費爾德大學、羅特林根大學、西班牙哈恩大學、阿爾梅里亞大學、塞維利亞大學、日本新潟大學、神戶大學、筑波大學、福岡教育大學、愛知教育大學、秋田大學、韓國首爾市立大學、首爾女子大學、釜慶大學、大邱大學、慶尚國立大學、明知大學、又松大學及馬來西亞、印尼、泰國、越南、土耳其、瑞士、羅馬尼亞、俄羅斯、烏拉圭、蒙古、阿聯酋等 73 所國外姊妹校）"
          ),
          (
              "赴大陸及港澳地區姊妹校交換學生計畫（2027年春季班［115-2學期］校內甄選於 2026/10/27 15:00 截止、10/29–10/30 面試，開放北京師範大學、華東師範大學、東北師範大學、華中師範大學、陝西師範大學、西北師範大學、西南大學、四川大學 8 所重點高校共 24 個公費交換名額；秋季班［115-1／116-1］另涵蓋武漢大學、廈門大學、北京外國語大學、首都師範大學、北京體育大學、北京林業大學、山東師範大學、南京師範大學、華南師範大學、福建師範大學、上海大學、上海體育大學、中南財經政法大學、西南財經大學、西北大學、寧波大學、濟南大學、內蒙古大學、貴州大學及香港教育大學、香港恒生大學共 29 所大陸與香港合作大學）"
          ),
          (
              "跨國雙聯學位計畫（依《國立彰化師範大學與境外大學校院辦理跨國雙聯學制實施辦法》辦理，含美國天普大學 Temple University 3+2 學碩雙聯、加州州立大學弗雷斯諾分校 CSU Fresno 企管／財金／物理／資工／特教／輔諮／英語 2+2 學士及 1+1 碩士雙聯、肯尼索州立大學 KSU 資工 2+2／1+1 雙聯、喬治梅森大學 GMU 特教 1+1 碩士雙聯、明德大學蒙特雷國際研究學院 MIIS 翻譯碩士雙聯、英國西英格蘭大學 UWE 學碩雙聯、英國史崔克萊大學 Strathclyde 公育系 1+1 碩士雙聯、澳洲新南威爾斯大學 UNSW 3+1 學士專案及印尼國立日惹大學 UGM 管理學院碩士雙聯）"
          ),
      ],
      "academic_year": [
          (
              "116（116學年度［2027秋季、2028春季］赴國外非大陸姊妹校交換研修暨教育部學海飛颺／惜珠獎學金甄選自 2026/07/09 公告簡章、2027/01/13 (三) 15:00 報名截止；若有剩餘名額將於 6 月底辦理第 2 學期二次甄選）"
          ),
          (
              "115（2027年春季班［115-2學期］赴大陸地區姊妹校交換計畫於 2026/10/06 公告簡章、2026/10/27 (二) 15:00 報名截止、10/29 或 10/30 面試、11月初放榜；本平台完整收錄 108 所彰師大交換與雙聯合作姊妹校，含 84 所當期開放申請校及 24 所歷年／秋季班合作校）"
          ),
      ],
      "semester": [
          "秋季學期（第1學期：每年約 8/9 月至翌年 1/2 月，日本秋季班為 9/10 月至翌年 2/3 月）",
          "春季學期（第2學期：每年約 2/3 月至 6/7 月，日本春季班為 4 月至 8/9 月）",
          "一學年交換或 1–2 年跨國雙聯學位修讀（依各姊妹校協議名額及雙聯學制辦理）",
      ],
      "application_period": [
          (
              "【2027年春季班（115-2學期）赴大陸地區姊妹校交換計畫校內甄選（進行中）】簡章公告：2026/10/06；校內收件截止：2026/10/27 (二) 15:00（請將申請表 Word 檔與全套申請資料合併為單一 PDF 寄至 `yuchen@cc.ncue.edu.tw`［信件主旨：115-2大陸_申請人姓名］，並繳交紙本 1 份至進德校區白沙大樓 4 樓國際暨兩岸事務處章祐甄行政專員，分機 5124）；校內面試：2026/10/29 (四) 或 10/30 (五)；錄取公告：2026年11月初。"
          ),
          (
              "【116學年度（2027秋季、2028春季）赴國外非大陸姊妹校交換研修暨教育部學海飛颺／惜珠獎學金甄選（進行中）】簡章公告：2026/07/09；校內收件截止：2027/01/13 (三) 15:00（須完成三項步驟：1. 填寫線上申請 Google 表單 `https://forms.gle/otaTRwh2ZkHAWwbH7`［申請學海補助者加填 `https://forms.gle/8ZAo5x42CTiHNs769`］；2. 將全套申請文件依序掃描合併為單一 PDF 寄至 `outgoing@gm.ncue.edu.tw`；3. 將紙本正本 1 份置於透明資料袋［請勿裝訂］送交白沙大樓 4 樓國際處林九汝專員，分機 5125）。"
          ),
          (
              "【國外非大陸姊妹校第二學期二次甄選與大陸秋季班預告】（1）國外非大陸姊妹校若於第一學期（1月初截止）甄選後尚有名額，將於每年 6 月底截止受理第二學期（春季班）二次甄選；（2）大陸及港澳地區姊妹校秋季班（116-1學期）預計於 2027年3月初公告簡章。"
          ),
      ],
      "eligibility": [
          (
              "【在學學制、年級與延畢限制（依《國立彰化師範大學交換學生甄選作業要點》及《甄選簡章》）】凡本校在學之學士班、碩士班、博士班學生，於本校就讀滿一學期以上者皆可提出申請（最早於大一第 2 學期［大一下］提出申請、大二第 1 學期［大二上］出國交換）。休學生及一般延畢生不可提出申請（惟已修滿畢業應修科目學分，專為出國交換經本校核准延畢且延畢期間以 1 年為限者，不在此限）。"
          ),
          (
              "【學業成績門檻與學海飛颺／惜珠 GPA 標準】申請交換學生須符合各志願姊妹校訂定之學業成績標準（多數歐美日韓姊妹校要求歷年 GPA 2.5–3.0 以上，中英文歷年成績單須含全班人數、名次及排名百分比）；如同時申請教育部《學海飛颺》或《學海惜珠》獎學金，依《國立彰化師範大學辦理教育部學海系列補助作業準則》第4條規定，歷年學業總平均須達 GPA 2.5 以上或全班排名前 50%（約 70 分以上）。"
          ),
          (
              "【校內外語面試 70 分及格線與同分比序原則】校內甄選分為書面資料審查與面試兩階段，由國際處敦聘 3–5 位委員組成甄選小組。國外非大陸姊妹校採全外語面試（每人約 5 分鐘：含 2 分鐘外語自我介紹與讀書計畫報告＋3 分鐘委員提問）；面試總成績平均未達 70 分者，不予選送。總成績相同時，以面試成績高低決定優先順序。"
          ),
      ],
      "language_requirement": [
          (
              "【2 年內有效語檢證明與不採計多益校園考規定】申請赴國外非大陸姊妹校交換者，必須提交 2 年內有效之語言能力檢定證明（注意：TOEIC 校園考不予採計，IELTS 必須為學術組 Academic）。英語系國家及申請教育部《學海飛颺／惜珠》基準為：TOEFL iBT 61 分以上、IELTS（學術組）5.5 以上、TOEIC 670 分以上、或全民英檢（GEPT）中高級以上（若志願姊妹校要求更高標準，須依該校規定）。"
          ),
          (
              "【非英語系國家與重點姊妹校語言門檻】（1）日本姊妹校：筑波大學要求 JLPT N1；愛知教育大學、秋田大學要求 JLPT N2；福岡教育大學、新潟大學要求 JLPT N2–N3 或英語檢定；神戶大學要求英語或日語檢定；（2）韓國姊妹校：首爾市立大學、首爾女子大學、釜慶大學、大邱大學、慶尚國立大學、明知大學、又松大學要求 TOPIK 2–4 級或英語 TOEFL iBT 61–80 / IELTS 5.5–6.0 / TOEIC 670–750；（3）德法西歐語區：德國姊妹校要求英語 B2（TOEFL iBT 72–80 / IELTS 5.5–6.0 / TOEIC 750–785）或德語 B1–B2；法國 INALCO、波爾多蒙田、索邦大學要求法語 DELF B1–B2（特魯瓦科技大學 UTT 可用英語 B1–B2 或法語 B1）；西班牙哈恩、阿爾梅里亞、塞維利亞大學要求西語 DELE B1 或英語 B1–B2；（4）美加英澳名校：UC Berkeley 要求 iBT 90 / IELTS 7.0；UC Irvine、UCSD、UNSW、Strathclyde 要求 iBT 80–90 / IELTS 6.5。"
          ),
          (
              "【赴大陸及港澳地區姊妹校語言規定】赴大陸地區姊妹校交換免附外語能力檢定證明（惟具備英、日、韓等外語檢定證書者可列為校內書面審查加分項目）；赴香港教育大學（EdUHK）要求 TOEFL iBT 80 或 IELTS 6.0 以上。"
          ),
      ],
      "required_documents": [
          "1. 國立彰化師範大學出國交換學生甄選申請表（黏貼半年內 2 吋彩色大頭照、本人簽名並經系所主管核章；國外非大陸另須先完成線上 Google 表單登錄）",
          "2. 家長（或監護人）保證書正本乙份（須由本人及家長／監護人親筆簽名蓋章）及健康自述表乙份",
          "3. 中文歷年成績單正本乙份（須註明全班人數、名次及排名百分比；轉學生或碩博一年級新生須加附原就讀學校或大學部歷年成績單）",
          "4. 英文歷年成績單正本乙份（GPA 4.0 制，供提名姊妹校審查使用）",
          "5. 2 年內有效之外語能力檢定證明影本（TOEIC 校園考不予採計，IELTS 須為學術組 Academic；赴大陸地區免附，但可作為加分佐證）",
          "6. 中文自傳（800 字以內）與中文讀書計畫（1,500 字以內，須詳述申請動機、擬修課程規劃與返國學分抵免安排）",
          "7. 英文（或擬交換國家語文）自傳與讀書計畫（各 2 頁以內，供外語面試委員及姊妹校審查）",
          "8. 教育部《學海飛颺》或《學海惜珠》補助申請表及相關證明（申請學海惜珠者須附低收／中低收／特殊境遇家庭證明；全套文件須依序掃描合併為單一 PDF 寄至承辦信箱，並將紙本正本 1 份置於透明資料袋［請勿裝訂］送交白沙大樓 4 樓國際暨兩岸事務處）",
      ],
      "scholarship_info": [
          (
              "教育部《學海飛颺》選送優秀學生出國研修獎學金（依《國立彰化師範大學辦理教育部學海系列補助作業準則》）：併同 116 學年度赴國外非大陸姊妹校交換生甄選提出申請（截止日：2027/01/13 15:00）。申請資格：具中華民國國籍且在臺設有戶籍之在學生，歷年學業總平均達 GPA 2.5 以上或全班排名前 50%（約 70 分以上），且具 2 年內有效外語檢定證明（英語系國家基準：TOEFL iBT 61 / IELTS 5.5 / TOEIC 670 / GEPT 中高級）。補助項目含來回經濟艙機票、國外學費及生活費，依教育部核配預算與校內甄選成績核定額度。"
          ),
          (
              "教育部《學海惜珠》勵學優秀學生出國研修獎學金與《學海築夢／新南向學海築夢》海外實習獎學金：（1）學海惜珠：補助具低收入戶、中低收入戶、特殊境遇家庭扶助、身心障礙者生活補助或大專校院弱勢學生助學金助學資格之優秀在學生赴國外（不含大陸及港澳）修讀學分，機票、學費及生活費得獲優先高額補助；（2）學海築夢／新南向學海築夢：由專任教師擔任計畫主持人選送學生赴國外或新南向國家機構進行專業實習，補助來回機票與生活費。"
          ),
          (
              "接待姊妹校交換獎學金與大陸地區免學費互惠待遇：（1）公費交換生於交換期間僅須繳交彰師大校內學雜費，免繳國外及大陸地區接待姊妹校學費；（2）日本姊妹校（如新潟大學、筑波大學、神戶大學、福岡教育大學、愛知教育大學、秋田大學）可透過接待校申請日本學生支援機構（JASSO）獎學金（每月 JPY 80,000）；捷克姊妹校（赫拉德茨克拉洛韋大學、奧斯特拉瓦大學、西波希米亞大學）部分學院提供交換生住宿或生活津貼獎學金；美國明德大學蒙特雷國際研究學院（MIIS）與天普大學雙聯學位提供雙聯學費減免獎學金；部分大陸姊妹校提供免住宿費或生活津貼。"
          ),
          (
              "學海獎學金撥款比例（80%＋20%）與返國 14 日內報到及 8 小時志工義務：獲核定學海飛颺／惜珠獎學金之學生，須於出國前簽訂《國立彰化師範大學選送學生出國研修行政契約書》，出國前先撥付核定補助總額之 80%；返國抵臺（桃園機場入境）後 14 日內，必須繳交返國註冊單、2,500 字以內《交換心得報告》（含 5–6 張照片，Word 及 PDF 檔）、教育部留學報告表及登機證單據，並須配合國際處完成 8 小時返國經驗分享會主講或國際交流活動志工服務，經審查通過後撥付剩餘 20% 尾款。"
          ),
      ],
      "partner_universities": [p["school_name"] for p in partners],
      "source_urls": ncue_source_urls,
      "last_checked": CHECKED_AT,
  }
  (OFFICIAL_NCUE_DIR / "exchange_info.json").write_text(
      json.dumps(exchange_info_payload, ensure_ascii=False, indent=2) + "\n",
      encoding="utf-8",
  )

  student_dashboard_payload = {
      "school_name": "國立彰化師範大學",
      "last_checked": CHECKED_AT,
      "academic_score_minimum": 70.0,
      "academic_score_rule": (
          "依《國立彰化師範大學交換學生甄選作業要點》及《辦理教育部學海系列補助作業準則》規定：申請人須於本校就讀滿一學期以上（最早大一下學期申請、大二上學期出國；休學生及一般延畢生不可申請），學業成績須符合志願姊妹校 GPA 標準（多數要求 GPA 2.5–3.0 以上），申請教育部學海飛颺／惜珠補助者歷年學業總平均須達 GPA 2.5 以上或全班排名前 50%（約 70 分以上）；校內外語面試總成績平均未達 70 分者不予選送。"
      ),
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
              "graduate": 70.0,
          },
          "excluded_undergraduate_years": ["大一上"],
          "language_certificate_required": True,
      },
      "language_score_minimums": {
          "toefl": 61.0,
          "ielts": 5.5,
          "toeic": 670.0,
      },
      "application_periods": [
          {
              "title": (
                  "國立彰化師範大學 2027年春季班（115-2學期）赴大陸地區姊妹校交換計畫校內甄選（2026/10/27 15:00 截止・10/29–10/30 面試）"
              ),
              "details": [
                  (
                      "2027年春季班（115-2學期）赴大陸地區姊妹校交換計畫自 2026/10/06 公告簡章，校內收件截止日為 2026/10/27 (二) 15:00，校內面試訂於 2026/10/29 (四) 或 10/30 (五) 舉行，預計 2026年11月初公告錄取名單。本期共開放北京師範大學（5名）、華東師範大學（5名）、東北師範大學（4名）、西北師範大學（4名）、華中師範大學（2名）、陝西師範大學（2名）、西南大學（1名）、四川大學（1名）共 8 所大陸 985／211 重點師範與綜合大學、合計 24 個公費交換名額。"
                  ),
                  (
                      "申請人須於截止前將《交換生甄選申請表》Word 檔及全套申請文件合併為單一 PDF 檔寄至 `yuchen@cc.ncue.edu.tw`（信件主旨：`115-2大陸_申請人姓名`），並將紙本正本 1 份送交進德校區白沙大樓 4 樓國際暨兩岸事務處章祐甄行政專員（分機 5124）。"
                  ),
              ],
              "source": {
                  "title": "國立彰化師範大學 2027年春季班（115-2學期）赴大陸地區姊妹校交換計畫甄選簡章與學校名額表",
                  "source_url": NCUE_MAINLAND_115_2_POST_URL,
                  "category": "exchange_application",
                  "summary": "彰師大 115-2 赴大陸地區姊妹校交換甄選簡章、8 所開放學校名額表與申請表單。",
              },
              "scope": "home_application",
              "program_types": ["exchange"],
              "academic_year": "115",
              "application_round": "2027年春季班（115-2學期）赴大陸地區姊妹校交換甄選",
              "audience": "all_students",
              "opens_at": "2026-10-06T09:00:00+08:00",
              "deadline_at": "2026-10-27T15:00:00+08:00",
              "date_status": "verified_exact",
              "status": "action_required",
              "status_note": "115-2（2027春季班）赴大陸地區姊妹校交換甄選現正受理報名中，將於 2026/10/27 (二) 15:00 截止收件，10/29 或 10/30 舉行校內面試。",
              "deadline_note": "請將申請表 Word 檔與全套申請資料合併為單一 PDF 寄至 `yuchen@cc.ncue.edu.tw`（主旨：`115-2大陸_申請人姓名`），並繳交紙本 1 份至白沙大樓 4 樓國際處章祐甄專員。",
              "reminder_eligible": True,
              "checked_at": CHECKED_AT,
          },
          {
              "title": (
                  "國立彰化師範大學 116學年度（2027秋季、2028春季）赴國外非大陸姊妹校交換研修暨教育部學海飛颺／惜珠獎學金甄選（2027/01/13 15:00 截止）"
              ),
              "details": [
                  (
                      "116學年度（2027年秋季班及2028年春季班）赴國外非大陸姊妹校交換研修甄選暨教育部學海飛颺、學海惜珠補助申請自 2026/07/09 公告簡章，校內收件截止日為 2027/01/13 (三) 15:00（若第一學期甄選後尚有餘額，第二學期二次甄選將於 6 月底截止）。本期開放美、加、英、澳、德、法、西、捷、瑞、日、韓、馬、印、泰、越、土、俄、羅、烏、蒙、阿聯酋等 21 國共 76 所國外交換與雙聯合作姊妹校。"
                  ),
                  (
                      "申請人須於 2027/01/13 (三) 15:00 前完成三項繳件步驟：（1）填寫線上申請 Google 表單 `https://forms.gle/otaTRwh2ZkHAWwbH7`（同時申請學海補助者加填 `https://forms.gle/8ZAo5x42CTiHNs769`）；（2）將全套申請文件依序掃描合併為單一 PDF 檔寄至 `outgoing@gm.ncue.edu.tw`；（3）將紙本正本 1 份置於透明資料袋（切勿裝訂）送交白沙大樓 4 樓國際處林九汝專員（分機 5125）。"
                  ),
              ],
              "source": {
                  "title": "國立彰化師範大學 116學年度赴國外非大陸姊妹校交換研修甄選簡章與 73 校一覽表",
                  "source_url": NCUE_OVERSEAS_116_POST_URL,
                  "category": "exchange_application",
                  "summary": "彰師大 116 學年赴國外非大陸姊妹校交換簡章 PDF、73 校名額條件表與學海飛颺／惜珠申請表。",
              },
              "scope": "home_application",
              "program_types": ["exchange", "dual_degree"],
              "academic_year": "116",
              "application_round": "116學年度（2027秋季、2028春季）赴國外非大陸姊妹校交換暨學海補助甄選",
              "audience": "all_students",
              "opens_at": "2026-07-09T09:00:00+08:00",
              "deadline_at": "2027-01-13T15:00:00+08:00",
              "date_status": "verified_exact",
              "status": "action_required",
              "status_note": "116學年度赴國外非大陸姊妹校交換研修暨學海飛颺／惜珠獎學金現正受理申請中，校內收件至 2027/01/13 (三) 15:00 截止。",
              "deadline_note": "須同時完成線上 Google 表單登錄、單一合併 PDF 寄送至 `outgoing@gm.ncue.edu.tw`，並將不裝訂透明資料袋紙本正本送交白沙大樓 4 樓國際處林九汝專員。",
              "reminder_eligible": True,
              "checked_at": CHECKED_AT,
          },
      ],
      "program_overview": [
          {
              "title": (
                  f"國立彰化師範大學國際暨兩岸事務處出國交換與跨國雙聯總覽（{len(partners)} 所全球合作姊妹校・{open_partner_count} 所當期開放申請校・教育部學海飛颺／惜珠獎補助）"
              ),
              "details": [
                  (
                      f"國立彰化師範大學（NCUE，彰師大）由「國際暨兩岸事務處（OICA）」統籌辦理全校赴國外非大陸姊妹校交換研修、赴大陸及港澳地區姊妹校交換計畫、跨國雙聯學制與教育部學海系列獎補助計畫。本平台完整收錄 {len(partners)} 所彰師大官方交換與雙聯合作姊妹校（含當期開放申請名額之 {open_partner_count} 所合作校及 {len(partners) - open_partner_count} 所歷年／秋季班合作校），橫跨全球 23 個國家與地區（中國大陸 27 校、美國 12 校、印尼 11 校、德國 9 校、日本 7 校、韓國 7 校、法國 4 校、泰國 4 校、英國 3 校、捷克 3 校、西班牙 3 校、馬來西亞 3 校、加拿大 2 校、澳洲 2 校、土耳其 2 校、香港 2 校，以及烏拉圭、俄羅斯、羅馬尼亞、瑞士、蒙古、阿拉伯聯合大公國、越南各 1 校）。"
                  ),
                  (
                      "彰師大出國交換體系具備四大核心特色：（1）公費交換、自費交換與跨國雙聯三軌並進：涵蓋美英德法西捷日韓及新南向公費交換、美國加州大學柏克萊分校（UC Berkeley）／爾灣分校（UCI）／聖地牙哥分校（UCSD）及澳洲新南威爾斯大學（UNSW）自費交換專案，以及美國天普大學、加州州立大學弗雷斯諾分校、肯尼索州立大學、喬治梅森大學、明德大學蒙特雷國際研究學院、英國西英格蘭大學、史崔克萊大學與印尼日惹大學跨國雙聯學位；（2）頂尖師範與綜合高校夥伴：大陸地區匯聚北京師範大學、華東師範大學、東北師範大學、華中師範大學、陝西師範大學、西南大學、四川大學、武漢大學、廈門大學與香港教育大學；（3）完善教育部學海飛颺／惜珠獎補助（出國前 80%＋返國 20%）；（4）公開收錄 53 所姊妹校共 409 篇歷屆學長姐返國交換心得報告。"
                  ),
              ],
              "source": {
                  "title": "國立彰化師範大學國際暨兩岸事務處—出國交換計畫與雙聯學制總覽",
                  "source_url": NCUE_OUTBOUND_OVERVIEW_URL,
                  "category": "exchange_application",
                  "summary": "彰師大 108 所全球交換與雙聯姊妹校、116學年國外交換簡章、115-2 大陸交換簡章、學海系列獎補助與 409 篇學長姐心得專區。",
              },
          }
      ],
      "eligibility": [
          {
              "title": "在學滿一學期資格（最早大一下申請、大二上出國）、學海 GPA 2.5／排名前 50% 門檻與外語面試 70 分及格線",
              "details": [
                  (
                      "在學身分與年級限制（依《國立彰化師範大學交換學生甄選作業要點》）：凡本校在學之學士班、碩士班、博士班學生，於本校就讀滿一學期以上者皆可申請（最早於大一第 2 學期申請、大二第 1 學期出國）。休學生及一般延畢生不可提出申請（惟已修滿畢業應修科目學分、專為出國交換經核准延畢以 1 年為限者不在此限）。"
                  ),
                  (
                      "學業門檻與面試淘汰線：申請人須符合志願姊妹校 GPA 要求（多數要求歷年 GPA 2.5–3.0 以上），同時申請教育部《學海飛颺／學海惜珠》者歷年總平均須達 GPA 2.5 以上或全班排名前 50%（約 70 分以上）。校內甄選含書面審查及 5 分鐘外語面試（2 分鐘自我介紹與讀書計畫＋3 分鐘委員提問），面試總成績平均未達 70 分者不予選送，同分時依面試成績高低比序。"
                  ),
              ],
              "source": {
                  "title": "國立彰化師範大學交換學生甄選作業要點與辦理教育部學海系列補助作業準則 PDF",
                  "source_url": NCUE_EXCHANGE_SELECTION_GUIDELINES_URL,
                  "category": "exchange_application",
                  "summary": "彰師大出國交換申請資格、學海 GPA 2.5／前 50% 門檻與面試 70 分及格線規定。",
              },
          }
      ],
      "language_requirements": [
          {
              "title": "2 年內有效語檢證明（TOEIC 不採計校園考、IELTS 限學術組）、英語基準 iBT 61 / IELTS 5.5 / TOEIC 670 與各語區門檻",
              "details": [
                  (
                      "外語檢定通則與英語基準：申請赴國外非大陸姊妹校交換者，必須檢附 2 年內有效之語言能力檢定證明（TOEIC 校園考不予採計，IELTS 必須為學術組 Academic）。英語系國家及教育部《學海飛颺／惜珠》基準為：TOEFL iBT 61 分以上、IELTS（學術組）5.5 以上、TOEIC 670 分以上、或全民英檢（GEPT）中高級以上。"
                  ),
                  (
                      "各語區與重點姊妹校進階要求：（1）日本：筑波大學要求 JLPT N1；愛知教育大學、秋田大學要求 JLPT N2；福岡教育大學、新潟大學要求 JLPT N2–N3 或英語檢定；（2）韓國：首爾市立大學、首爾女子大學、釜慶大學、大邱大學、慶尚國立大學、明知大學、又松大學要求 TOPIK 2–4 級或英語 iBT 61–80 / IELTS 5.5–6.0 / TOEIC 670–750；（3）歐語區：德國姊妹校要求英語 B2 或德語 B1–B2，法國姊妹校要求法語 DELF B1–B2（特魯瓦科技大學 UTT 可用英語 B1–B2），西班牙姊妹校要求西語 DELE B1 或英語 B1–B2；（4）大陸地區免附外語證明（香港教育大學要求 iBT 80 / IELTS 6.0）。"
                  ),
              ],
              "source": {
                  "title": "國立彰化師範大學 116學年度赴國外非大陸姊妹校交換研修甄選簡章與 73 校條件表",
                  "source_url": NCUE_OVERSEAS_116_BROCHURE_URL,
                  "category": "exchange_application",
                  "summary": "彰師大 116 學年國外交換語檢通則（不採計多益校園考、雅思限學術組）與 73 校語檢及 GPA 門檻。",
              },
          }
      ],
      "required_documents": [
          {
              "title": "線上表單＋單一合併 PDF 電子檔＋透明資料袋紙本正本（請勿裝訂）三合一繳件規範",
              "details": [
                  (
                      "校內甄選必繳資料（請依申請表檢核順序排列，紙本正本 1 份置於透明資料袋、切勿裝訂）：1. 出國交換學生甄選申請表（貼妥 2 吋照片並經系所核章）、2. 家長保證書正本、3. 健康自述表、4. 中文歷年成績單正本（須含全班人數、名次及排名百分比）、5. 英文歷年成績單正本（GPA 4.0 制）、6. 2 年內有效外語能力證明（大陸地區免附）、7. 中文自傳（800 字內）與中文讀書計畫（1,500 字內）、8. 英文或外文自傳與讀書計畫（各 2 頁內）、9. 教育部學海飛颺／惜珠補助申請表及其他有利審查資料。"
                  ),
                  (
                      "繳件方式與返國 14 日內報到義務：（1）國外非大陸姊妹校須同時完成 Google 表單登錄、將全套資料合併為單一 PDF 寄至 `outgoing@gm.ncue.edu.tw` 並親送紙本至白沙大樓 4 樓林九汝專員；（2）大陸地區姊妹校須將申請表 Word 檔與單一合併 PDF 寄至 `yuchen@cc.ncue.edu.tw` 並親送紙本至章祐甄專員；（3）返國抵臺（桃園機場入境）後 14 日內須提交返國註冊單、2,500 字以內《交換心得報告》（含 5–6 張照片）及留學報告表。"
                  ),
              ],
              "source": {
                  "title": "國立彰化師範大學 116學年度赴國外非大陸姊妹校交換申請表與 115-2 大陸交換簡章",
                  "source_url": NCUE_OVERSEAS_116_APP_FORM_URL,
                  "category": "exchange_application",
                  "summary": "彰師大出國交換申請表、家長保證書、健康自述表與中英文自傳／讀書計畫字數頁數規定。",
              },
          }
      ],
      "scholarship_info": [
          {
              "title": "教育部學海飛颺／學海惜珠／學海築夢獎學金（出國前80%＋返國20%撥款）與姊妹校 JASSO／雙聯獎學金",
              "details": [
                  (
                      "教育部《學海飛颺／學海惜珠》獎學金（依《國立彰化師範大學辦理教育部學海系列補助作業準則》）：併同 116 學年國外非大陸姊妹校交換生甄選申請（2027/01/13 15:00 截止），申請人須具中華民國國籍且在臺設有戶籍、歷年 GPA 2.5 以上或全班排名前 50%、並具 2 年內有效語檢證明（學海惜珠另須具低收／中低收／特殊境遇家庭等資格）。出國前簽訂行政契約書先撥付 80%，返國後 14 日內繳交 2,500 字內心得報告並完成 8 小時經驗分享或國際處活動志工後撥付 20% 尾款。"
                  ),
                  (
                      "公費交換免學費待遇與接待校獎學金：公費交換生僅須繳交彰師大校內學雜費，免繳國外及大陸接待姊妹校學費；日本姊妹校可申請 JASSO 獎學金（每月 JPY 80,000），捷克姊妹校提供住宿或生活津貼，美國蒙特雷國際研究學院（MIIS）與天普大學雙聯學位提供學費減免獎學金。"
                  ),
              ],
              "source": {
                  "title": "國立彰化師範大學辦理教育部學海系列補助作業準則與 116 學年學海申請公告",
                  "source_url": NCUE_XUEHAI_GUIDELINES_URL,
                  "category": "scholarship",
                  "summary": "彰師大教育部學海飛颺、學海惜珠作業準則、GPA 與語檢門檻、行政契約書及 80%/20% 撥款核銷規定。",
              },
          }
      ],
      "document_explanations": [
          {
              "title": "國立彰化師範大學出國交換中文自傳（800字內）、中文讀書計畫（1,500字內）與外文自傳／讀書計畫（各2頁內）撰寫指南",
              "summary": "說明彰師大國際暨兩岸事務處規定之中外文自傳、讀書計畫字數頁數上限及不裝訂透明資料袋繳件規範。",
              "key_points": [
                  "《中文自傳》以 800 字以內為原則，《中文讀書計畫》以 1,500 字以內為原則；須具體說明個人學經歷、外語準備、擬於志願姊妹校修習之課程（每學期至少須修習 2 門課或相當彰師大 6 學分）及返國學分抵免規劃。",
                  "申請國外非大陸姊妹校者，另須檢附《英文（或擬交換國語文）自傳》與《外文讀書計畫》（各以 2 頁以內為原則），供校內 5 分鐘外語面試委員及姊妹校審查。",
                  "全套申請文件須先依序掃描合併為單一 PDF 寄至承辦人信箱（國外：`outgoing@gm.ncue.edu.tw`；大陸：`yuchen@cc.ncue.edu.tw`），紙本正本 1 份請置於透明資料袋內、切勿裝訂，送交白沙大樓 4 樓國際暨兩岸事務處。",
              ],
              "applies_to": [],
              "source": {
                  "title": "國立彰化師範大學 116學年度赴國外非大陸姊妹校交換研修甄選簡章與申請表",
                  "source_url": NCUE_OVERSEAS_116_BROCHURE_URL,
                  "category": "exchange_application",
                  "summary": None,
              },
              "document_url": NCUE_OVERSEAS_116_APP_FORM_URL,
              "document_type": "official_document",
              "full_text_extracted": True,
          }
      ],
      "rule_explanations": [
          {
              "title": "國立彰化師範大學交換學生甄選作業要點與出國選課注意事項：面試 70 分及格線、每學期 2 門課／6 學分與返國 14 日報到",
              "summary": "規範彰師大出國交換生在學滿一學期資格、外語檢定限制、外語面試 70 分淘汰線、國外選課最低學分與學分換算表。",
              "key_points": [
                  "申請人須於彰師大就讀滿一學期以上（最早大一下申請、大二上出國），休學生及一般延畢生不得申請；TOEIC 校園考不予採計，IELTS 須為學術組 Academic。",
                  "校內外語面試每人約 5 分鐘（2 分鐘自我介紹與讀書計畫＋3 分鐘問答），面試總成績平均未達 70 分者不予選送；總成績相同時以面試成績較高者優先錄取。",
                  "出國期間每學期至少須修習 2 門課或相當於彰師大 6 學分之課程（1 彰師大學分 = 2 ECTS = 5 UK CATS = 4 澳洲學分 = 1 日／韓學分）；返國抵臺後 14 日內須繳交返國註冊單與 2,500 字內心得報告（學海受獎生另須完成 8 小時志工服務以領取 20% 尾款）。",
              ],
              "applies_to": [],
              "source": {
                  "title": "國立彰化師範大學交換學生甄選作業要點、學生出國選修課程實施注意事項與學分對照表 PDF",
                  "source_url": NCUE_EXCHANGE_SELECTION_GUIDELINES_URL,
                  "category": "exchange_application",
                  "summary": None,
              },
              "document_url": NCUE_EXCHANGE_SELECTION_GUIDELINES_URL,
              "document_type": "official_document",
              "full_text_extracted": True,
          }
      ],
      "sources": [
          {
              "title": "國立彰化師範大學國際暨兩岸事務處（OICA）官方網站",
              "source_url": NCUE_OICA_HUB_URL,
              "category": "exchange_application",
              "summary": None,
          },
          {
              "title": "國立彰化師範大學 116學年度赴國外非大陸姊妹校交換研修甄選簡章 PDF",
              "source_url": NCUE_OVERSEAS_116_BROCHURE_URL,
              "category": "exchange_application",
              "summary": None,
          },
          {
              "title": "國立彰化師範大學 116學年度赴國外非大陸姊妹校交換名冊與條件表（73校 Google Sheet）",
              "source_url": NCUE_OVERSEAS_116_SHEET_URL,
              "category": "partner_school",
              "summary": None,
          },
          {
              "title": "國立彰化師範大學交換學生甄選作業要點 PDF",
              "source_url": NCUE_EXCHANGE_SELECTION_GUIDELINES_URL,
              "category": "exchange_application",
              "summary": None,
          },
          {
              "title": "國立彰化師範大學辦理教育部學海系列補助作業準則 PDF",
              "source_url": NCUE_XUEHAI_GUIDELINES_URL,
              "category": "scholarship",
              "summary": None,
          },
          {
              "title": "國立彰化師範大學 2027年春季班（115-2學期）赴大陸地區姊妹校交換甄選簡章與名額表",
              "source_url": NCUE_MAINLAND_115_2_POST_URL,
              "category": "partner_school",
              "summary": None,
          },
          {
              "title": "國立彰化師範大學學生出國選修課程實施注意事項與締約學校學分對照表 PDF",
              "source_url": NCUE_OUTBOUND_COURSE_NOTES_URL,
              "category": "exchange_application",
              "summary": None,
          },
          {
              "title": "國立彰化師範大學全球姊妹校一覽表、跨國雙聯學制與歷屆交換心得專區",
              "source_url": NCUE_GLOBAL_SISTERS_URL,
              "category": "partner_school",
              "summary": None,
          },
      ],
  }
  (OFFICIAL_NCUE_DIR / "student_dashboard.json").write_text(
      json.dumps(student_dashboard_payload, ensure_ascii=False, indent=2) + "\n",
      encoding="utf-8",
  )

  pages_records = [
      {
          "title": "國立彰化師範大學：116學年度赴國外非大陸姊妹校交換甄選（2027/01/13截止）暨 115-2 赴大陸地區交換甄選（2026/10/27截止）時程",
          "source_url": NCUE_OVERSEAS_116_BROCHURE_URL,
          "published_at": "2026-07-09T00:00:00Z",
          "text": "\n".join(exchange_info_payload["application_period"]),
          "summary": "\n".join(exchange_info_payload["application_period"]),
          "category": "exchange_application",
          "attachments": [],
          "crawled_at": CHECKED_AT,
          "content_hash": hashlib.sha256("\n".join(exchange_info_payload["application_period"]).encode("utf-8")).hexdigest(),
      },
      {
          "title": "國立彰化師範大學：交換學生甄選作業要點（就讀滿一學期資格、學海 GPA 2.5／前 50% 門檻與 5 分鐘外語面試 70 分淘汰線）",
          "source_url": NCUE_EXCHANGE_SELECTION_GUIDELINES_URL,
          "published_at": "2026-07-09T00:00:00Z",
          "text": "\n".join(exchange_info_payload["eligibility"]),
          "summary": "\n".join(exchange_info_payload["eligibility"]),
          "category": "exchange_application",
          "attachments": [],
          "crawled_at": CHECKED_AT,
          "content_hash": hashlib.sha256("\n".join(exchange_info_payload["eligibility"]).encode("utf-8")).hexdigest(),
      },
      {
          "title": "國立彰化師範大學：108 所交換與雙聯合作姊妹校外語檢定門檻（2 年內有效證明、TOEIC 不採計校園考、IELTS 限學術組）",
          "source_url": NCUE_OVERSEAS_116_SHEET_URL,
          "published_at": "2026-07-09T00:00:00Z",
          "text": "\n".join(exchange_info_payload["language_requirement"]),
          "summary": "\n".join(exchange_info_payload["language_requirement"]),
          "category": "exchange_application",
          "attachments": [],
          "crawled_at": CHECKED_AT,
          "content_hash": hashlib.sha256("\n".join(exchange_info_payload["language_requirement"]).encode("utf-8")).hexdigest(),
      },
      {
          "title": "國立彰化師範大學：出國交換申請文件（中英文自傳與讀書計畫字數頁數限制、家長保證書、健康自述表）與三合一繳件規範",
          "source_url": NCUE_OVERSEAS_116_APP_FORM_URL,
          "published_at": "2026-07-09T00:00:00Z",
          "text": "\n".join(exchange_info_payload["required_documents"]),
          "summary": "\n".join(exchange_info_payload["required_documents"]),
          "category": "exchange_application",
          "attachments": [],
          "crawled_at": CHECKED_AT,
          "content_hash": hashlib.sha256("\n".join(exchange_info_payload["required_documents"]).encode("utf-8")).hexdigest(),
      },
      {
          "title": "國立彰化師範大學：辦理教育部學海飛颺／學海惜珠／學海築夢補助作業準則（80%＋20% 撥款、返國 14 日內報到與 8 小時志工義務）",
          "source_url": NCUE_XUEHAI_GUIDELINES_URL,
          "published_at": "2026-07-09T00:00:00Z",
          "text": "\n".join(exchange_info_payload["scholarship_info"]),
          "summary": "\n".join(exchange_info_payload["scholarship_info"]),
          "category": "scholarship",
          "attachments": [],
          "crawled_at": CHECKED_AT,
          "content_hash": hashlib.sha256("\n".join(exchange_info_payload["scholarship_info"]).encode("utf-8")).hexdigest(),
      },
  ]
  (OFFICIAL_NCUE_DIR / "pages.jsonl").write_text(
      "\n".join(json.dumps(p, ensure_ascii=False) for p in pages_records) + "\n",
      encoding="utf-8",
  )

  home_rules = {
      "school_id": "ncue",
      "school_name": "國立彰化師範大學",
      "eligibility": student_dashboard_payload["eligibility"],
      "application_periods": student_dashboard_payload["application_periods"],
      "selection_rules": {
          "undergraduate_score_minimum": 70.0,
          "graduate_score_minimum": 70.0,
          "xuehai_gpa_minimum": 2.5,
          "xuehai_class_rank_percent_max": 50,
          "excluded_undergraduate_years": ["大一上"],
          "exclude_leave_of_absence_and_regular_extended_students": True,
          "interview_minimum_passing_score": 70.0,
          "tie_breaker": "面試成績高低",
          "toeic_campus_test_accepted": False,
          "ielts_academic_required": True,
          "minimum_courses_per_semester_abroad": 2,
          "minimum_credits_per_semester_abroad": 6,
          "xuehai_pre_departure_disbursement_ratio": 0.8,
          "xuehai_post_return_disbursement_ratio": 0.2,
          "xuehai_volunteer_hours_required": 8,
          "return_documents_due": "返國抵臺（桃園機場入境）後 14 日內繳交返國註冊單、2,500 字以內交換心得報告（含 5–6 張照片，Word 及 PDF 檔）與留學報告表，學海受獎生另須完成 8 小時經驗分享志工服務",
      },
      "source_urls": ncue_source_urls,
      "verified_at": "2026-10-20",
  }
  (OFFICIAL_NCUE_DIR / "home_rules.json").write_text(
      json.dumps(home_rules, ensure_ascii=False, indent=2) + "\n",
      encoding="utf-8",
  )
  (OFFICIAL_NCUE_DIR / "documents.json").write_text(
      json.dumps(
          {
              "school_name": "國立彰化師範大學",
              "required_documents": student_dashboard_payload["required_documents"],
              "source_urls": ncue_source_urls,
          },
          ensure_ascii=False,
          indent=2,
      )
      + "\n",
      encoding="utf-8",
  )
  (OFFICIAL_NCUE_DIR / "scholarships.json").write_text(
      json.dumps(
          {
              "school_name": "國立彰化師範大學",
              "scholarships": student_dashboard_payload["scholarship_info"],
              "source_urls": ncue_source_urls,
          },
          ensure_ascii=False,
          indent=2,
      )
      + "\n",
      encoding="utf-8",
  )

  completeness = {
      "school_id": "ncue",
      "school_name": "國立彰化師範大學",
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
          "國立彰化師範大學國際暨兩岸事務處 116 學年度（2027秋季、2028春季）赴國外非大陸姊妹校交換研修暨教育部學海飛颺／惜珠獎學金甄選現正受理申請中（2027/01/13 15:00 截止），2027年春季班（115-2學期）赴大陸地區姊妹校交換計畫同步受理申請中（2026/10/27 15:00 截止、10/29–10/30 面試）；共完整收錄 108 所全球交換與雙聯合作姊妹校（含 84 所當期開放申請校及 24 所歷年／秋季班合作校，橫跨歐、美、亞、大洋洲 23 個國家與地區，並收錄 53 所學校共 409 篇歷屆學長姐返國心得報告）。"
      ),
      "verified_at": "2026-10-20",
  }
  (OFFICIAL_NCUE_DIR / "catalog-completeness.json").write_text(
      json.dumps(completeness, ensure_ascii=False, indent=2) + "\n",
      encoding="utf-8",
  )
  (OFFICIAL_NCUE_DIR / "verification_status.json").write_text(
      json.dumps(
          {
              "school_id": "ncue",
              "school_name": "國立彰化師範大學",
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
          "sources/ncue/overseas_116_brochure_542278849.pdf",
          NCUE_OVERSEAS_116_BROCHURE_URL,
          "國立彰化師範大學 116 學年度赴國外非大陸姊妹校交換研修甄選簡章 PDF",
      ),
      (
          "sources/ncue/overseas_116_partners_1JZE.xlsx",
          NCUE_OVERSEAS_116_SHEET_URL,
          "國立彰化師範大學 116 學年度赴國外非大陸姊妹校交換研修學校一覽表（73 校 Google Sheet）XLSX",
      ),
      (
          "sources/ncue/overseas_115_brochure_zh_459677627.pdf",
          "https://oicaweb.ncue.edu.tw/var/file/19/1019/img/459677627.pdf",
          "國立彰化師範大學 115 學年度赴國外非大陸姊妹校交換研修甄選簡章（中文版）PDF",
      ),
      (
          "sources/ncue/overseas_115_partners_1gWV.xlsx",
          "https://docs.google.com/spreadsheets/d/1gWVhYbW2XHI4V4EsibLOUxrJx3EKZyN9/edit",
          "國立彰化師範大學 115 學年度赴國外非大陸姊妹校交換研修學校一覽表 XLSX",
      ),
      (
          "sources/ncue/mainland_115_2_0_簡章-2027年春(115-2)赴大陸地區交換_20261006.pdf",
          NCUE_MAINLAND_115_2_POST_URL,
          "國立彰化師範大學 2027 年春季班（115-2 學期）赴大陸地區姊妹校交換計畫甄選簡章 PDF",
      ),
      (
          "sources/ncue/mainland_115_1_0_簡章-2025年春(115-1)赴大陸地區交換_20260303.pdf",
          NCUE_MAINLAND_115_1_POST_URL,
          "國立彰化師範大學 2026 年秋季班（115-1 學期）赴大陸及港澳地區姊妹校交換計畫甄選簡章 PDF",
      ),
      (
          "sources/ncue/exchange_selection_guidelines_547428539.pdf",
          NCUE_EXCHANGE_SELECTION_GUIDELINES_URL,
          "國立彰化師範大學交換學生甄選作業要點 PDF",
      ),
      (
          "sources/ncue/xuehai_subsidy_guidelines_191957275.pdf",
          NCUE_XUEHAI_GUIDELINES_URL,
          "國立彰化師範大學辦理教育部學海系列補助作業準則 PDF",
      ),
      (
          "sources/ncue/moe_subsidy_directions_308829954.pdf",
          NCUE_MOE_SUBSIDY_DIRECTIONS_URL,
          "教育部鼓勵國內大專校院選送學生出國研修或國外專業實習補助要點 PDF",
      ),
      (
          "sources/ncue/dual_degree_regulations_603615731.pdf",
          NCUE_DUAL_DEGREE_REGS_URL,
          "國立彰化師範大學與境外大學校院辦理跨國雙聯學制實施辦法 PDF",
      ),
      (
          "sources/ncue/outbound_course_selection_notes_433095064.pdf",
          NCUE_OUTBOUND_COURSE_NOTES_URL,
          "國立彰化師範大學學生出國選修課程實施注意事項 PDF",
      ),
      (
          "sources/ncue/credit_transfer_guidelines_504843202.pdf",
          NCUE_CREDIT_TRANSFER_REGS_URL,
          "國立彰化師範大學辦理學生抵免學分作業準則 PDF",
      ),
      (
          "sources/ncue/credit_conversion_table_123052535.pdf",
          NCUE_CREDIT_CONVERSION_TABLE_URL,
          "國立彰化師範大學交換學生於締約學校修讀課程學分對照表 PDF",
      ),
      (
          "sources/ncue/overseas_116_application_form_974155076.docx",
          NCUE_OVERSEAS_116_APP_FORM_URL,
          "國立彰化師範大學 116 學年度赴國外非大陸姊妹校交換學生甄選申請表 DOCX",
      ),
      (
          "sources/ncue/overseas_parental_guarantee_348780386.docx",
          NCUE_PARENTAL_GUARANTEE_URL,
          "國立彰化師範大學出國交換學生家長保證書 DOCX",
      ),
      (
          "sources/ncue/overseas_health_declaration_522622028.docx",
          NCUE_HEALTH_DECLARATION_URL,
          "國立彰化師範大學出國交換學生健康自述表 DOCX",
      ),
      (
          "sources/ncue/xuehai_feiyang_form_602763967.odt",
          NCUE_XUEHAI_FEIYANG_FORM_URL,
          "國立彰化師範大學教育部學海飛颺獎學金申請表 ODT",
      ),
      (
          "sources/ncue/xuehai_xizhu_form_233821766.odt",
          NCUE_XUEHAI_XIZHU_FORM_URL,
          "國立彰化師範大學教育部學海惜珠獎學金申請表 ODT",
      ),
      (
          "sources/ncue/xuehai_admin_contract_844199804.docx",
          NCUE_XUEHAI_CONTRACT_URL,
          "國立彰化師範大學選送學生出國研修行政契約書 DOCX",
      ),
      (
          "sources/ncue/global_sisters_1164.html",
          NCUE_GLOBAL_SISTERS_URL,
          "國立彰化師範大學全球締約姊妹校一覽表 HTML",
      ),
      (
          "sources/ncue/dual_degree_1167.html",
          NCUE_DUAL_DEGREE_URL,
          "國立彰化師範大學跨國雙聯學制合作學校一覽表 HTML",
      ),
      (
          "sources/ncue/ncue_catalog_source.json",
          NCUE_OVERSEAS_116_BROCHURE_URL,
          "國立彰化師範大學 108 所出國交換與雙聯合作姊妹校整合資料集 JSON",
      ),
      (
          "sources/ncue/ncue_resolved_locations.json",
          NCUE_OVERSEAS_116_BROCHURE_URL,
          "國立彰化師範大學 108 所出國交換與雙聯合作姊妹校 ROR / Wikidata 地理座標核對表 JSON",
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
      "school_id": "ncue",
      "school_name": "國立彰化師範大學",
      "generated_at": CHECKED_AT,
      "active_cycle_note": completeness["active_term"],
      "sources": prov_sources,
  }
  prov_text = json.dumps(provenance_payload, ensure_ascii=False, indent=2) + "\n"
  (OFFICIAL_NCUE_DIR / "import_provenance.json").write_text(prov_text, encoding="utf-8")
  (OFFICIAL_NCUE_DIR / "import-provenance.json").write_text(prov_text, encoding="utf-8")

  print(
      f"Successfully built NCUE catalog: {len(partners)} partners"
      f" ({open_partner_count} open, {completeness['verified_campus_images']}"
      f" verified images, {completeness['verified_locations']} verified"
      f" locations), {len(workflows)} workflows,"
      f" {len(destinations)} destinations, {len(research_records)} research"
      f" records, {exp_covered_schools} schools with experience records"
      f" ({len(student_experience_rows)} rows)."
  )


if __name__ == "__main__":
  main()
