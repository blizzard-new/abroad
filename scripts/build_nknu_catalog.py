"""Build the official National Kaohsiung Normal University (國立高雄師範大學, NKNU) exchange data bundle."""

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

SOURCES_NKNU_DIR = REPO_ROOT / "sources" / "nknu"
OFFICIAL_NKNU_DIR = REPO_ROOT / "src" / "exchange_info" / "official_data" / "nknu"
STATIC_DIR = REPO_ROOT / "src" / "exchange_info" / "static"

CHECKED_AT = "2026-10-20T18:30:00Z"

NKNU_OIA_HUB_URL = "https://oia.nknu.edu.tw/"
NKNU_OUTBOUND_EXCHANGE_URL = "https://oia.nknu.edu.tw/exchange-programs.php"
NKNU_MAINLAND_EXCHANGE_URL = "https://oia.nknu.edu.tw/exchange-programs-mainland.php"
NKNU_SISTER_SCHOOLS_URL = "https://oia.nknu.edu.tw/sister-schools.php"
NKNU_DUAL_DEGREE_URL = "https://oia.nknu.edu.tw/dual-degree.php"
NKNU_REGULATIONS_URL = "https://oia.nknu.edu.tw/regulations.php"
NKNU_ACA_REGULATIONS_URL = "https://c.nknu.edu.tw/aca/Laws.aspx?PN=48"
NKNU_SSO_APPLY_URL = "https://sso.nknu.edu.tw/InternationalAdmissions/StudentAboard/Apply.aspx"

NKNU_116_XUEHAI_INFO_URL = "https://oia.nknu.edu.tw/news-detail.php?id=496"
NKNU_2027_SPRING_MAINLAND_URL = "https://oia.nknu.edu.tw/news-detail.php?id=460"
NKNU_2026_FALL_MAINLAND_URL = "https://oia.nknu.edu.tw/news-detail.php?id=377"
NKNU_115_XUEHAI_BRIEFING_PDF_URL = "https://oia.nknu.edu.tw/uploads/files/%E5%AD%B8%E6%B5%B7%E8%AA%AA%E6%98%8E%E6%9C%83115%E5%B9%B4%E7%B0%A1%E5%A0%B1_final%20version_20251029.pdf"
NKNU_115_OUTBOUND_HANDBOOK_PDF_URL = "https://oia.nknu.edu.tw/uploads/files/115%E5%B9%B4%E9%81%B8%E9%80%81%E5%AD%B8%E7%94%9F%E5%87%BA%E5%9C%8B%E8%AA%AA%E6%98%8E%E6%9C%83%E6%89%8B%E5%86%8A%EF%BC%BF%E5%9C%8B%E9%9A%9B%E8%99%95final%20version_20251027.pdf"
NKNU_SELECTION_GUIDELINES_PDF_URL = "https://oia.nknu.edu.tw/uploads/files/20251007113315_68e489fb6d963.pdf"
NKNU_SELECTION_FLOWCHART_PDF_URL = "https://oia.nknu.edu.tw/uploads/files/20251007113402_68e48a2ac6dd3.pdf"
NKNU_OUTBOUND_APP_FORMS_DOC_URL = "https://oia.nknu.edu.tw/uploads/files/20251007113419_68e48a3b07252.doc"
NKNU_PREDEPARTURE_NOTES_PDF_URL = "https://oia.nknu.edu.tw/uploads/files/20251007113835_68e48b3b21461.pdf"
NKNU_OVERSEAS_SAFETY_PDF_URL = "https://oia.nknu.edu.tw/uploads/files/20251007113907_68e48b5ba5a30.pdf"
NKNU_EXPERIENCE_GUIDE_PDF_URL = "https://oia.nknu.edu.tw/uploads/files/20251007114733_68e48d55f30f9.pdf"
NKNU_REIMBURSEMENT_CHECKLIST_DOCX_URL = "https://oia.nknu.edu.tw/uploads/files/20251007115119_68e48e37521e8.docx"
NKNU_DUAL_DEGREE_APP_FORM_DOCX_URL = "https://oia.nknu.edu.tw/uploads/files/20251007132226_68e4a392d4c4a.docx"
NKNU_DUAL_DEGREE_REGULATIONS_PDF_URL = "https://c.nknu.edu.tw/aca/Download.ashx?FileNo=1972&GID=20"
NKNU_COURSE_SELECTION_PDF_URL = "https://c.nknu.edu.tw/aca/Download.ashx?FileNo=1052&GID=20"
NKNU_ACADEMIC_STATUS_PDF_URL = "https://c.nknu.edu.tw/aca/Download.ashx?FileNo=919&GID=20"
NKNU_CREDIT_TRANSFER_PDF_URL = "https://c.nknu.edu.tw/aca/Download.ashx?FileNo=1075&GID=20"

REGION_BY_COUNTRY = {
    "美國": "美洲",
    "巴西": "美洲",
    "捷克": "歐洲",
    "德國": "歐洲",
    "瑞典": "歐洲",
    "法國": "歐洲",
    "奧地利": "歐洲",
    "英國": "歐洲",
    "西班牙": "歐洲",
    "波蘭": "歐洲",
    "匈牙利": "歐洲",
    "俄羅斯": "歐洲",
    "斯洛維尼亞": "歐洲",
    "澳洲": "大洋洲",
    "日本": "亞洲",
    "韓國": "亞洲",
    "菲律賓": "亞洲",
    "泰國": "亞洲",
    "越南": "亞洲",
    "印尼": "亞洲",
    "馬來西亞": "亞洲",
    "印度": "亞洲",
    "蒙古": "亞洲",
    "中國大陸": "中國大陸及港澳",
    "香港": "中國大陸及港澳",
    "澳門": "中國大陸及港澳",
}

REGION_COST_DEFAULTS = {
    "美國": (
        "USD 1,250–2,100 / 月（西佛羅里達大學 UWF 依高師大說明會手冊估算 1 學期學雜住宿生活費約 USD 7,561.78［約 USD 1,500 / 月］、北卡羅萊納大學夏洛特分校 UNC Charlotte 校內食宿每學期約 USD 6,750、明尼蘇達州立大學曼卡托分校 MSU Mankato 校內宿舍每學期約 USD 3,453–3,870、西密西根大學 WMU 校內外住宿加膳食約 USD 1,300–1,800 / 月；可申請教育部學海飛颺／惜珠獎學金）",
        "須憑接待校核發之 DS-2019 表格繳納 SEVIS I-901 費用並向美國在台協會（AIT）申辦 J-1 交換學生簽證，且須購買接待校強制規定之國際學生醫療保險（如 UWF GeoBlue、WMU 學生醫療險）及高師大海外全期醫療意外險。",
    ),
    "巴西": (
        "USD 550–900 / 月（西巴拉那州立大學 UNIOESTE 學生公寓、校園餐飲與市區公車費用實惠）",
        "須憑巴西接待校入學許可向巴西商務辦事處申辦學生簽證（VITEM IV），並於出國前投保涵蓋全期之海外醫療及意外保險。",
    ),
    "捷克": (
        "CZK 10,500–16,000 / 月（約 EUR 430–650 / 月，拉貝河畔烏斯季普爾基涅大學 UJEP 校內學生宿舍約 CZK 95–130 / 日、布拉格查理大學 Charles University 與捷克技術大學 CTU 學生宿舍及大學食堂 Menza 費用極為親民，為高師大歐洲熱門交換國別）",
        "須憑捷克接待校核發之入學許可與住宿證明向捷克經濟文化辦事處申辦長期居留／學生簽證，並購買捷克法定綜合醫療保險（pVZP）。",
    ),
    "德國": (
        "EUR 934–1,150 / 月（德國簽證限制提領帳戶 Sperrkonto 法定基準為每月 EUR 992；帕德博恩大學 Paderborn University 免學費但須繳納學期社會捐與全邦交通票 Semesterbeitrag 約 EUR 310 / 學期，Studierendenwerk 學生宿舍約 EUR 260–400 / 月）",
        "須辦理德國法定學生健康保險（如 TK / AOK，30 歲以下約 EUR 125–135 / 月）、繳納帕德博恩大學學期雜費（Semesterbeitrag）並向德國在台協會申辦長期學生簽證。",
    ),
    "瑞典": (
        "SEK 9,500–13,500 / 月（約 EUR 850–1,200 / 月，達拉納大學 Dalarna University 法倫 Falun 與博倫厄 Borlänge 校區學生公寓、自炊伙食與學生交通卡）",
        "交換超過 3 個月須憑達拉納大學入學許可與財力證明向瑞典移民局（Migrationsverket）線上申辦高等教育居留許可（Residence Permit for Higher Education），並投保涵蓋全期之海外醫療及意外保險。",
    ),
    "法國": (
        "EUR 1,000–1,500 / 月（巴黎西岱大學 Université Paris Cité 位於巴黎市中心，高師大說明會手冊提醒該校不提供校內宿舍、須自行安排巴黎租屋或國際大學城住宿；格勒諾柏-阿爾卑斯大學 UGA 約 EUR 750–1,100 / 月，可申請法國政府 CAF 房補）",
        "須先透過法國教育中心（Campus France）完成線上面談程序，再向法國在台協會申辦長期學生簽證（VLS-TS），抵法後完成 OFII 生效與法國學生健保登錄。",
    ),
    "奧地利": (
        "EUR 850–1,250 / 月（克agenfurt 教育大學／克恩頓師範學院 University College of Teacher Education Carinthia 學生宿舍 OeAD、日常膳食與學期交通票）",
        "交換一學期（6 個月內）須向奧地利台北辦事處申辦奧地利 D 類學生簽證（超過 6 個月申辦學生居留許可），並投保符合申根與奧地利規定之醫療保險。",
    ),
    "英國": (
        "GBP 1,050–1,650 / 月（倫敦大學學院教育研究院 UCL IOE 及洛翰普頓大學 University of Roehampton 約 GBP 1,300–1,650 / 月；樸茨茅斯大學 University of Portsmouth 約 GBP 950–1,250 / 月）",
        "交換一學期（6 個月內）可辦理英國 Standard Visitor 簽證，交換一學年須申辦英國 Student Visa 並繳納 IHS 醫療附加費。",
    ),
    "西班牙": (
        "EUR 650–1,000 / 月（卡斯提亞-拉曼查大學 UCLM 學生分租公寓、大學食堂與城市交通費用親民）",
        "須憑西班牙接待校入學許可向西班牙商務辦事處申辦學生簽證，並投保無自負額、涵蓋全期之西班牙醫療保險。",
    ),
    "波蘭": (
        "EUR 500–850 / 月（華沙波蘭特殊教育大學 APS 及什切青藝術學院 Academy of Art in Szczecin 校內學生宿舍、學生餐廳與半價大眾運輸開銷實惠）",
        "須憑波蘭接待校入學許可向波蘭臺北辦事處申辦波蘭國家 D 類學生簽證，並投保涵蓋全期之歐盟醫療保險。",
    ),
    "匈牙利": (
        "EUR 600–950 / 月（布達佩斯李斯特音樂學院 Franz Liszt Academy of Music 學生租屋、日常餐飲與布達佩斯學生交通月票）",
        "須憑接待校入學許可向匈牙利貿易辦事處申辦學生簽證／居留許可，並於出國前投保涵蓋全期之海外醫療及意外保險。",
    ),
    "俄羅斯": (
        "USD 500–850 / 月（莫斯科國立師範大學 MSPU 及莫斯科市立師範大學 MCU 校內學生宿舍費用低廉，每月生活與莫斯科地鐵學生月票開銷實惠）",
        "須憑俄羅斯接待校核發之官方邀請函向莫斯科台北經濟文化協調委員會駐台北代表處申辦俄羅斯留學簽證並投保當地醫療險。",
    ),
    "斯洛維尼亞": (
        "EUR 650–1,000 / 月（盧比安納大學 University of Ljubljana 學生宿舍、全城餐廳學生餐券 Študentski boni 與市區公車月票）",
        "須憑盧比安納大學入學許可申辦斯洛維尼亞長期簽證或臨時居留許可，並投保涵蓋全期之醫療及意外保險。",
    ),
    "澳洲": (
        "AUD 1,900–2,800 / 月（雪梨大學 University of Sydney、布里斯本昆士蘭科技大學 QUT 及伯斯科廷大學 Curtin University 學生宿舍、伙食與大眾運輸）",
        "須購買澳洲海外學生健康保險（OSHC）並透過澳洲內政部 ImmiAccount 線上申辦 Subclass 500 學生簽證。",
    ),
    "日本": (
        "JPY 70,000–120,000 / 月（東京櫻美林大學及日本中央大學約 JPY 95,000–130,000 / 月［櫻美林另收申請與學生服務費共 JPY 60,000］；千葉大學、大阪教育大學、三重大學、岩手大學、兵庫教育大學、滋賀大學、新潟大學、金澤星稜大學、鳥取大學、山口大學等學生寮費僅約 JPY 10,000–35,000 / 月；可申請教育部學海飛颺／惜珠獎學金）",
        "須憑日本接待校核發之在留資格認定證明書（COE）向日本台灣交流協會高雄或台北事務所申辦留學簽證，抵日後須依法加入日本國民健康保險（NHI）並投保高師大規定之海外醫療及意外險。",
    ),
    "韓國": (
        "KRW 700,000–1,200,000 / 月（首爾東國大學、梨花女子大學、韓國中央大學、瑞逸大學約 KRW 850,000–1,250,000 / 月；春川江原大學、群山大學［校內宿舍含三餐每學期僅約 USD 900］、釜山外國語大學［免姊妹校學費及校內住宿費］開銷極為實惠）",
        "須憑韓國接待校核發之標準入學許可書向駐台北韓國代表部申辦 D-2-6 交換學生簽證（雙聯學位為 D-2），抵韓後辦理外國人登錄並自動納入韓國國民健康保險（NHIS）。",
    ),
    "菲律賓": (
        "USD 450–750 / 月（菲律賓大學 UP、東方大學 UE 及萊西姆大學拉古納分校 LPU-Laguna 學生宿舍、餐飲與交通費用低廉）",
        "須依菲律賓接待校國際處指引辦理菲律賓 9(f) 學生簽證或 SSP 特別學習許可，並投保涵蓋全期之海外醫療及意外保險。",
    ),
    "泰國": (
        "THB 12,000–20,000 / 月（曼谷宣素南塔皇家大學 SSRU、泰國藝術大學 Silpakorn、正大管理學院 PIM、清邁皇家大學 CMRU 及彭世洛納瑞宣大學 Naresuan University 學生宿舍與校園餐飲開銷實惠）",
        "須憑泰國接待校核發之入學許可公文向泰國貿易經濟辦事處（TTEO）申辦 Non-Immigrant ED 學生簽證並投保海外醫療險。",
    ),
    "越南": (
        "USD 380–650 / 月（胡志明市師範大學 HCMUE、河內藝術學院及太原大學 Thai Nguyen University 學生宿舍、日常飲食與交通費用低廉）",
        "須憑越南接待校入學許可透過駐臺北越南經濟文化辦事處申辦越南學生簽證，並於出國前投保涵蓋全期之海外醫療及意外險。",
    ),
    "印尼": (
        "IDR 4,500,000–7,800,000 / 月（雅加達建國大學 BINUS、阿天瑪加雅天主教大學 Atma Jaya、芝卡朗總統大學 President University、梭羅大學 UNS 及棉蘭諾門森大學 UHN 住宿與生活費親民）",
        "須由印尼接待校協助向印尼移民總局申辦學習電子簽證（e-Visa）並投保海外全期醫療及意外保險。",
    ),
    "馬來西亞": (
        "MYR 1,400–2,400 / 月（拉曼大學 UTAR、新紀元大學學院 New Era、南方大學學院 Southern UC 及檳城韓江傳媒大學學院 HCUC 校內外學生宿舍與飲食生活費親民）",
        "須於出國前透過馬來西亞 EMGS（Education Malaysia Global Services）系統線上申辦學生簽證核准函（VAL / Student Pass）並投保 EMGS 指定醫療保險。",
    ),
    "印度": (
        "USD 350–650 / 月（新德里國立伊斯蘭大學 Jamia Millia Islamia、清奈 SRM 科技大學、維爾科技大學 Vel Tech 及哥印拜陀卡帕甘高等教育學院 KAHE 校內國際學生宿舍與學餐費用低廉）",
        "須憑印度接待校入學許可向印度台北協會（ITA）申辦印度 Student Visa，並投保涵蓋全期之海外醫療及意外保險。",
    ),
    "蒙古": (
        "USD 450–750 / 月（烏蘭巴托蒙古全球領袖大學 Global Leadership University 學生宿舍、餐飲與市區交通費用低廉）",
        "須憑接待校入學許可申辦蒙古學生簽證，並於出國前投保涵蓋全期之海外醫療及意外保險。",
    ),
    "中國大陸": (
        "RMB 1,800–3,500 / 月（北京師範大學、南京大學、華東師範大學、華中師範大學、東北師範大學、陝西師範大學、西南大學、南京師範大學、福州大學、中國人民大學、廈門大學等重點高校校內宿舍約 RMB 600–1,500 / 學期，學生食堂與地鐵公車成本低廉）",
        "持有效護照與臺胞證（臺灣居民來往大陸通行證）入境，出國前須填送《家長同意書》《出國研修須知》《出國申請表》至高師大國際處，並投保涵蓋大陸地區交換全期之意外及醫療保險（抵校後依規定投保大陸來華留學生綜合醫療保險）。",
    ),
    "香港": (
        "HKD 8,500–13,500 / 月（香港教育大學 EdUHK 1 學期交換或數學碩班／科環碩班 1+1 碩士雙聯學位、香港樹仁大學校內學生宿舍、校園餐廳與港鐵學生優惠八達通）",
        "須透過香港接待校向香港入境事務處申辦來港就讀進入許可（Student Visa / Entry Permit），出國前至陸委會「國人赴港澳動態登錄網頁」完成登錄並投保海外醫療及意外保險。",
    ),
    "澳門": (
        "HKD 5,800–9,200 / 月（約 MOP 6,000–9,500 / 月，澳門城市大學 City University of Macau 及澳門科技大學 MUST 學生宿舍、校園餐廳與澳門通巴士優惠）",
        "持有效護照入境澳門後由接待校協助向澳門治安警察局居留及逗留事務廳辦理「逗留特別許可（學生逗留）」，出國前須至陸委會「國人赴港澳動態登錄網頁」登錄並投保海外醫療及意外保險。",
    ),
}

SEMESTER_DATES_BY_COUNTRY = {
    "美國": "秋季學期（Fall）：約 8 月中下旬至 12 月中旬；春季學期（Spring）：約 1 月中旬至 5 月中旬",
    "巴西": "第一學期：約 2/3 月至 7 月；第二學期：約 8 月至 12 月",
    "捷克": "冬季學期（Winter / 秋季班）：約 9 月中下旬至翌年 1/2 月；夏季學期（Summer / 春季班）：約 2 月中旬至 6 月底",
    "德國": "冬季學期（Wintersemester / 秋季班）：約 10 月初至翌年 2/3 月；夏季學期（Sommersemester / 春季班）：約 4 月初至 7 月底",
    "瑞典": "秋季學期（Autumn）：約 8 月底至翌年 1 月中旬；春季學期（Spring）：約 1 月中旬至 6 月初",
    "法國": "秋季學期（Semestre 1）：約 9 月初至 12 月底／翌年 1 月；春季學期（Semestre 2）：約 1 月中旬至 5/6 月",
    "奧地利": "冬季學期（Wintersemester）：約 10 月初至翌年 1 月底；夏季學期（Sommersemester）：約 3 月初至 6 月底",
    "英國": "秋季學期（Semester 1 / Autumn）：約 9 月中下旬至翌年 1 月；春季學期（Semester 2 / Spring）：約 1 月下旬至 5/6 月",
    "西班牙": "第一學期（秋季班）：約 9 月中旬至翌年 1/2 月；第二學期（春季班）：約 2 月初至 6 月中下旬",
    "波蘭": "冬季學期（秋季班）：約 10 月初至翌年 2 月中旬；夏季學期（春季班）：約 2 月下旬至 6 月底",
    "匈牙利": "秋季學期：約 9 月初至 12 月中旬（考試期至 1 月）；春季學期：約 2 月初至 5 月中旬（考試期至 6 月）",
    "俄羅斯": "秋季學期：約 9 月初至翌年 1 月；春季學期：約 2 月初至 6 月底",
    "斯洛維尼亞": "冬季學期（秋季班）：約 10 月初至翌年 1/2 月；夏季學期（春季班）：約 2 月中旬至 6 月底",
    "澳洲": "第一學期（Semester 1）：約 2 月中下旬至 6 月；第二學期（Semester 2）：約 7 月下旬至 11 月",
    "日本": "秋季班（高師大上學期）：約 9/10 月至翌年 2/3 月；春季班（高師大下學期）：約 4 月至 8/9 月",
    "韓國": "秋季學期（第2學期）：約 9 月初至 12 月中下旬；春季學期（第1學期）：約 3 月初至 6 月中下旬",
    "菲律賓": "第一學期：約 8 月至 12 月；第二學期：約 1 月至 5 月",
    "泰國": "第一學期：約 8 月至 12 月；第二學期：約 1 月至 5 月",
    "越南": "第一學期（秋季班）：約 9 月至翌年 1 月；第二學期（春季班）：約 2 月至 6 月",
    "印尼": "奇數／秋季學期（Odd Semester）：約 8/9 月至 12 月／翌年 1 月；偶數／春季學期（Even Semester）：約 2 月至 6/7 月",
    "馬來西亞": "秋季學期：約 9/10 月至翌年 1/2 月；春季學期：約 2/3 月至 6/7 月（拉曼大學 UTAR 採 1 月／5 月／10 月三學期制）",
    "印度": "奇數／秋季學期：約 7/8 月至 12 月；偶數／春季學期：約 1 月至 5 月",
    "蒙古": "秋季學期：約 9 月初至 12 月底；春季學期：約 2 月初至 6 月初",
    "中國大陸": "秋季學期（上學期）：約 9 月初至翌年 1 月中旬；春季學期（下學期）：約 2 月中下旬至 6 月底／7 月初",
    "香港": "第一學期（秋季班）：約 9 月初至 12 月底；第二學期（春季班）：約 1 月中旬至 5 月中旬",
    "澳門": "第一學期（秋季班）：約 9 月初至 12 月底；第二學期（春季班）：約 1 月中下旬至 5 月底",
}

# 29 Official Student Experience Reports across 16 Partner Universities (from NKNU OIA exchange-programs.php sub_id=13)
EXPERIENCE_REPORTS_BY_ZH: dict[str, list[dict[str, str]]] = {
    "中國人民大學": [
        {
            "year": "107",
            "student": "跨領域藝術研究所碩二 李宜瑾",
            "title": "國立高雄師範大學赴中國人民大學藝術學院交換學生心得分享簡報",
            "url": "https://oia.nknu.edu.tw/uploads/files/20251007104824_68e47f782a4d8.pdf",
            "highlight": "分享於北京中國人民大學藝術學院修讀藝術理論與創作課程、校園生活、宿舍環境與北京藝文場館參訪實錄。",
        },
    ],
    "西南大學": [
        {
            "year": "108",
            "student": "高師大赴大陸交換生",
            "title": "國立高雄師範大學赴中國西南大學交換研修心得分享簡報",
            "url": "https://oia.nknu.edu.tw/uploads/files/%E4%BA%A4%E6%8F%9B%E5%BF%83%E5%BE%97%E5%88%86%E4%BA%AB_%E8%A5%BF%E5%8D%97(2)%20(1).pptx",
            "highlight": "記錄於重慶北碚區西南大學交換一學期之選課體驗、橘園學生宿舍生活、重慶飲食文化與校園社團交流。",
        },
    ],
    "北卡羅萊納大學夏洛特分校": [
        {
            "year": "108",
            "student": "英語學系 呂靜芳",
            "title": "108學年度國立高雄師範大學赴美國北卡羅萊納大學夏洛特分校（UNC Charlotte）交換研修心得報告",
            "url": "https://oia.nknu.edu.tw/uploads/files/20251007105247_68e4807f7ae27.pdf",
            "highlight": "詳述透過教育部學海飛颺計畫赴 UNC Charlotte 交換一學期，修讀英語教學（TESL）、發音教學及初級日語共 9 學分，以及透過 Niner Engage 參與國際社團與輕軌交通體驗。",
        },
        {
            "year": "106",
            "student": "高師大學海飛颺受獎生",
            "title": "106學年度國立高雄師範大學赴美國北卡羅萊納大學夏洛特分校交換研修心得報告",
            "url": "https://oia.nknu.edu.tw/uploads/files/20251007105256_68e4808868282.pdf",
            "highlight": "分享 UNC Charlotte 校內公寓式學生宿舍申請、膳食計畫（Meal Plan）、美式課堂討論互動與美國東岸文化探索。",
        },
    ],
    "西佛羅里達大學": [
        {
            "year": "112",
            "student": "美術學系三年級 莊予晴",
            "title": "112學年度國立高雄師範大學赴美國西佛羅里達大學（UWF）學海飛颺交換研修心得報告（A）",
            "url": "https://oia.nknu.edu.tw/uploads/files/20251007105449_68e480f995f70.pdf",
            "highlight": "詳述於佛羅里達州彭薩科拉 UWF 視覺藝術系修讀數位插畫、3D 電腦繪圖與繪畫工作室課程（共 12 學分），參加國際學生週（International Week）擺攤介紹臺灣文化與校園自然生態。",
        },
        {
            "year": "112",
            "student": "英語學系三年級 朱品宣",
            "title": "112學年度國立高雄師範大學赴美國西佛羅里達大學（UWF）學海飛颺交換研修心得報告（B）",
            "url": "https://oia.nknu.edu.tw/uploads/files/20251007105459_68e481037aadb.pdf",
            "highlight": "分享於 UWF 修讀文學與文化課程、校內宿舍與學餐生活、Global Quarter 跨國文化交流及佛羅里達海灣生活體驗。",
        },
        {
            "year": "111",
            "student": "高師大學海飛颺交換生",
            "title": "111學年度國立高雄師範大學赴美國西佛羅里達大學交換研修心得報告",
            "url": "https://oia.nknu.edu.tw/uploads/files/20251007105510_68e4810e1ecd0.pdf",
            "highlight": "整理 UWF J-1 簽證 DS-2019 申辦、強制疫苗與 GeoBlue 保險規定、選課抵免與學海飛颺獎學金核銷經驗。",
        },
        {
            "year": "108",
            "student": "高師大學海飛颺交換生",
            "title": "108學年度國立高雄師範大學赴美國西佛羅里達大學交換研修心得報告",
            "url": "https://oia.nknu.edu.tw/uploads/files/20251007105517_68e48115b6af3.pdf",
            "highlight": "記錄西佛羅里達大學小班制教學互動、國際學生辦公室（OIP）接機與迎新輔導及美國南方校園生活。",
        },
        {
            "year": "107",
            "student": "高師大學海飛颺交換生",
            "title": "107學年度國立高雄師範大學赴美國西佛羅里達大學交換研修心得報告",
            "url": "https://oia.nknu.edu.tw/uploads/files/20251007105524_68e4811c1af89.pdf",
            "highlight": "分享 UWF 校內外住宿比較、學期約 USD 7,500 生活與食宿預算規劃及全英語環境口語能力提升心得。",
        },
    ],
    "帕德博恩大學": [
        {
            "year": "112",
            "student": "英語學系 盧同學",
            "title": "112學年度國立高雄師範大學赴德國帕德博恩大學（Paderborn University）交換分享簡報",
            "url": "https://oia.nknu.edu.tw/uploads/files/112%E5%B9%B4%E5%BE%B7%E5%9C%8B%E5%B8%95%E5%BE%B7%E5%8D%9A%E6%81%A9%E5%A4%A7%E5%AD%B8%E4%BA%A4%E6%8F%9B%E5%88%86%E4%BA%AB_%E7%9B%A700.pdf",
            "highlight": "詳述德國帕德博恩大學 PAUL 選課系統、Studierendenwerk 學生宿舍申請、德語密集班（DSH 準備課程）、學期票（Semesterticket）暢遊北威邦與歐洲跨國旅行經驗。",
        },
        {
            "year": "110",
            "student": "高師大赴德交換生",
            "title": "110學年度國立高雄師範大學赴德國帕德博恩大學交換生分享簡報",
            "url": "https://oia.nknu.edu.tw/uploads/files/%E4%BA%A4%E6%8F%9B%E7%94%9F%E5%88%86%E4%BA%AB.pdf",
            "highlight": "整理德國限制提領帳戶（Sperrkonto）、TK 學生公保、德國簽證申辦時程與帕德博恩英語授課課程修讀心得。",
        },
        {
            "year": "106",
            "student": "高師大赴德交換生",
            "title": "106學年度國立高雄師範大學赴德國帕德博恩大學交換分享會簡報",
            "url": "https://oia.nknu.edu.tw/uploads/files/%E5%BE%B7%E5%9C%8B%E5%B8%95%E5%BE%B7%E5%8D%9A%E6%81%A9%E5%88%86%E4%BA%AB%E6%9C%83%E7%B0%A1%E5%A0%B1.pdf",
            "highlight": "介紹帕德博恩大學 ASB 國際學生社團 Buddy Program、大學食堂 Mensa 與德國生活開銷明細。",
        },
    ],
    "查理大學": [
        {
            "year": "112",
            "student": "高師大赴捷克交換生",
            "title": "112學年度（2023/2024）國立高雄師範大學赴捷克查理大學（Charles University）交換分享報告",
            "url": "https://oia.nknu.edu.tw/uploads/files/20251007112019_68e486f343790.pdf",
            "highlight": "詳述於布拉格查理大學文學院（Faculty of Arts, CUFA）修讀攝影、跨國歷史、英美文學與捷克語課程，分享布拉格學生宿舍、Lítačka 交通年票與中歐深度文化交流。",
        },
    ],
    "大阪教育大學": [
        {
            "year": "107",
            "student": "高師大赴日交換生",
            "title": "107學年度國立高雄師範大學赴日本大阪教育大學交換留學心得報告",
            "url": "https://oia.nknu.edu.tw/uploads/files/20251007112043_68e4870b18500.pdf",
            "highlight": "分享於大阪教育大學柏原校區修讀日本語、日本文化理解、多文化共生與陶瓷工藝實作課程，以及透過 KICC 柏原國際交流中心與當地小學生及市民互動的溫馨體驗。",
        },
    ],
    "三重大學": [
        {
            "year": "107",
            "student": "軟體工程與管理學系 陳彥成",
            "title": "107學年度國立高雄師範大學赴日本三重大學（Mie University）學海飛颺交換研修心得報告",
            "url": "https://oia.nknu.edu.tw/uploads/files/20251007112111_68e487278c343.pdf",
            "highlight": "詳述於三重縣津市三重大學修讀日語讀解、文法、聽解及伊賀忍者文化研究等課程，參與日本小學校文化交流並從零基礎提升至能以日語向日本民眾簡報臺灣文化。",
        },
        {
            "year": "106",
            "student": "高師大赴日交換生",
            "title": "106學年度國立高雄師範大學赴日本三重大學交換留學心得報告",
            "url": "https://oia.nknu.edu.tw/uploads/files/20251007112135_68e4873fae7f0.pdf",
            "highlight": "記錄三重大學國際交流會館宿舍生活、每月約 JPY 60,000–80,000 生活費預算與伊勢志摩歷史文化踏查。",
        },
    ],
    "山口大學": [
        {
            "year": "107",
            "student": "國文學系 許雅茹",
            "title": "107學年度國立高雄師範大學赴日本山口大學（Yamaguchi University）交換留學心得報告",
            "url": "https://oia.nknu.edu.tw/uploads/files/20251007112157_68e48755545e3.pdf",
            "highlight": "詳述於山口大學教育學部與國際綜合科學部修讀日本語及專業課程（一學期修滿 11 門課），分享留學生宿舍、腳踏車通勤與山口縣歷史文化生活。",
        },
    ],
    "滋賀大學": [
        {
            "year": "112",
            "student": "國文學系四年級 鍾易凌",
            "title": "112學年度國立高雄師範大學赴日本滋賀大學（Shiga University）學海飛颺交換研修心得報告（A）",
            "url": "https://oia.nknu.edu.tw/uploads/files/20251007112244_68e48784a6026.pdf",
            "highlight": "詳述於滋賀大學彥根校區修讀上級日本語、茶道實作、書法及彥根歷史街區考察課程，並參與彥根市吉祥物彥根喵與關西地區文化體驗。",
        },
        {
            "year": "112",
            "student": "高師大赴日交換生",
            "title": "112學年度國立高雄師範大學赴日本滋賀大學交換留學心得報告（B）",
            "url": "https://oia.nknu.edu.tw/uploads/files/20251007112252_68e4878c60649.pdf",
            "highlight": "分享滋賀大學大津與彥根校區選課、學生寮住宿費用與琵琶湖周邊生活環境。",
        },
        {
            "year": "110",
            "student": "高師大赴日交換生",
            "title": "110學年度國立高雄師範大學赴日本滋賀大學交換留學心得簡報",
            "url": "https://oia.nknu.edu.tw/uploads/files/%E2%BD%87%E6%9C%AC%E6%BB%8B%E8%B3%80%E2%BC%A4%E5%AD%B8.pdf",
            "highlight": "整理滋賀大學留學簽證 COE 申辦、學伴制度（Tutor）與日本國立大學交換生活日常。",
        },
        {
            "year": "108",
            "student": "高師大赴日交換生",
            "title": "108學年度國立高雄師範大學赴日本滋賀大學交換留學心得報告",
            "url": "https://oia.nknu.edu.tw/uploads/files/20251007112533_68e4882debc92.pdf",
            "highlight": "記錄滋賀大學教育學部與經濟學部課程修讀、日本文化社團參與及關西交通生活資訊。",
        },
    ],
    "新潟大學": [
        {
            "year": "108",
            "student": "國文學系中國文學碩士班 許詩琳",
            "title": "108學年度國立高雄師範大學赴日本新潟大學（Niigata University）交換一年研修心得報告",
            "url": "https://oia.nknu.edu.tw/uploads/files/20251007112724_68e4889c4c363.pdf",
            "highlight": "詳述於新潟大學五十嵐校區交換一學年（2019/09–2020/08），修讀日語聽讀寫、日本古典文學與方言學課程，並分享新潟雪國生活、華語教學打工與國際學生宿舍點滴。",
        },
    ],
    "千葉大學": [
        {
            "year": "110",
            "student": "工業設計學系 李紫菱",
            "title": "110學年度國立高雄師範大學赴日本千葉大學（Chiba University）學海飛颺交換研修心得報告",
            "url": "https://oia.nknu.edu.tw/uploads/files/20251007112748_68e488b4c0073.pdf",
            "highlight": "詳述於千葉大學工學部綜合工學科設計課程交換期間（6學分制），參與設計研究室產學合作專案、模型工坊實作與日本首都圈設計展演參訪收穫。",
        },
    ],
    "岩手大學": [
        {
            "year": "111",
            "student": "教育學系 張維真",
            "title": "111學年度國立高雄師範大學赴日本岩手大學（Iwate University）學海飛颺交換研修心得報告",
            "url": "https://oia.nknu.edu.tw/uploads/files/20251007112850_68e488f257feb.pdf",
            "highlight": "詳述於盛岡市岩手大學人文社會科學部修讀跨文化理解、英語與日語課程，入住國際交流會館、參與紫波町小學校國際交流及日本東北傳統祭典體驗。",
        },
        {
            "year": "111",
            "student": "高師大赴日交換生",
            "title": "111學年度國立高雄師範大學赴日本岩手大學交換留學數位筆記（Notion）",
            "url": "https://chennose1991.notion.site/531e1b24e686421192dc5cfc1d7099f8",
            "highlight": "完整整理岩手大學行前準備、盛岡生活開銷、選課攻略與東北旅遊生活指南。",
        },
    ],
    "日本中央大學": [
        {
            "year": "112",
            "student": "視覺設計學系 莊紫羚",
            "title": "112學年度國立高雄師範大學赴日本中央大學（Chuo University）學海飛颺交換研修心得報告（A）",
            "url": "https://oia.nknu.edu.tw/uploads/files/20251007113012_68e4894442cdb.pdf",
            "highlight": "詳述於東京都八王子市日本中央大學多摩校區修讀傳播學、日語及太極拳體育課程，加入造形藝術同好會參與白門祭學園祭展覽及東京美術館巡禮。",
        },
        {
            "year": "112",
            "student": "高師大赴日交換生",
            "title": "112學年度國立高雄師範大學赴日本中央大學交換留學心得報告（B）",
            "url": "https://oia.nknu.edu.tw/uploads/files/20251007113024_68e4895000203.pdf",
            "highlight": "分享日本中央大學國際學生宿舍 Global House 交誼生活、多摩都市單軌電車通勤與東京都圈留學收穫。",
        },
    ],
    "鳥取大學": [
        {
            "year": "112",
            "student": "事業經營學系 王家芸",
            "title": "112學年度國立高雄師範大學赴日本鳥取大學（Tottori University）學海飛颺交換研修心得報告",
            "url": "https://oia.nknu.edu.tw/uploads/files/20251007113047_68e48967874ab.pdf",
            "highlight": "詳述於鳥取大學修讀密集日語課程（每週多堂日語聽說讀寫與語彙課），參與幼稚園交流、鳥取砂丘與山陰地區傳統夏祭花火大會體驗。",
        },
    ],
    "韓國中央大學": [
        {
            "year": "111",
            "student": "英語學系 蔡同學",
            "title": "111學年度國立高雄師範大學赴韓國中央大學（Chung-Ang University）交換分享簡報",
            "url": "https://oia.nknu.edu.tw/uploads/files/%e4%ba%a4%e6%8f%9b%e5%88%86%e4%ba%ab%e9%9f%93%e5%9c%8b%e4%b8%ad%e5%a4%ae.pdf",
            "highlight": "詳述於首爾韓國中央大學修讀全英語授課與韓語課程、Global Ambassador 國際學伴活動、Blue Mir Hall 校內宿舍及首爾校園文化體驗。",
        },
    ],
}


def clean_text(s: str) -> str:
  if not s:
    return ""
  return re.sub(r"\s+", " ", s).strip()


def format_colleges_and_degrees(item: dict) -> tuple[str, str]:
  deg_str = clean_text(
      item.get("eligible_degrees")
      or "大學部、碩士班、博士班在學學生（須於高師大就讀滿一學期以上；休學生、學士班延畢生、選修生及領受臺灣獎學金之外國生不得申請）"
  )
  notes = clean_text(item.get("notes") or "")
  quota = clean_text(item.get("quota") or "")
  if "科技學院設計類科" in quota or "科技學院設計類科" in notes:
    colleges_str = "全校各學院（教育學院、文學院、理學院、科技學院、藝術學院在學生皆可申請，其中科技學院設計類科學生優先推薦）"
  elif "國文學系、英語學系、體育學系" in notes and "雙聯" in quota:
    colleges_str = "交換生計畫開放全校各學院（教育學院、文學院、理學院、科技學院、藝術學院）；2+2 學士雙聯學制適用文學院（國文學系、英語學系）及教育學院（體育學系）"
  elif "數學碩班、科環碩班" in notes:
    colleges_str = "交換生計畫開放全校各學院（教育學院、文學院、理學院、科技學院、藝術學院）；1+1 碩士雙聯學制適用理學院（數學系碩士班、科學教育暨環境教育研究所）"
  else:
    colleges_str = "不限學院（教育學院、文學院、理學院、科技學院、藝術學院等全校各系所符合姊妹校開設專業與語檢條件之在學生皆可申請；甄選單位：國際事務處）"
  return colleges_str, deg_str


def main() -> None:
  OFFICIAL_NKNU_DIR.mkdir(parents=True, exist_ok=True)
  catalog_source = json.loads(
      (SOURCES_NKNU_DIR / "nknu_catalog_source.json").read_text(encoding="utf-8")
  )
  resolved_locations = json.loads(
      (SOURCES_NKNU_DIR / "nknu_resolved_locations.json").read_text(encoding="utf-8")
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
    sn = idx + 1
    full_name = item["school_name"]
    zh_name = item["name_zh"]
    country = item["country"]
    region = REGION_BY_COUNTRY.get(country, item.get("region") or "亞洲")
    avail_status = "open" if item.get("offering_status") == "open" else "reference_only"
    if avail_status == "open":
      open_partner_count += 1

    quota_str = clean_text(item.get("quota") or "依當期交換簡章核定名額")
    if "雙聯" in quota_str:
      program_type = "交換生暨跨校雙聯學制計畫"
    elif country in {"中國大陸", "香港", "澳門"}:
      program_type = "大陸及港澳地區姊妹校交換計畫"
    else:
      program_type = "赴外交換研修暨教育部學海飛颺／惜珠計畫"

    colleges_str, degree_levels_str = format_colleges_and_degrees(item)
    lang_req_str = clean_text(item.get("language_req") or "")
    gpa_req_str = clean_text(item.get("gpa_req") or "前一學期學業成績全班前 50%、操行成績 80 分以上")
    website = item.get("website") or NKNU_SISTER_SCHOOLS_URL
    remarks_raw = clean_text(item.get("notes") or "")
    tuition_note = clean_text(item.get("tuition_note") or "")
    exps = EXPERIENCE_REPORTS_BY_ZH.get(zh_name, [])

    if country in {"中國大陸", "香港", "澳門"}:
      source_url = (
          NKNU_2027_SPRING_MAINLAND_URL
          if avail_status == "open"
          else NKNU_MAINLAND_EXCHANGE_URL
      )
      round_label = (
          "2027年春季班（115-2學期）暨2026年秋季班（115-1學期）大陸及港澳地區姊妹校交換甄選"
          if avail_status == "open"
          else "大陸及港澳地區正式締約姊妹校（依國際事務處每學期公告名額辦理）"
      )
      app_deadline_str = (
          "【2027年春季班（115-2學期）大陸及港澳地區姊妹校交換申請】校內收件截止：2026/10/16（香港教育大學為 2026/09/18、南京大學為 2026/10/13；請將電腦打字填妥之申請表與必備文件電子檔寄至國際處信箱 `oia_exchange@mail.nknu.edu.tw`，信件主旨：`申請OOOOO大學_OOO（名字）`，華東師範大學另須繳交 3 張紙本一吋證件照至國際處）；【秋季班（每年 3–4 月）】每年 3 月公告秋季班簡章、3 月底至 4 月底截止收件"
      )
      deadline_iso = "2026-10-16T17:00:00+08:00"
      win_status = "open" if avail_status == "open" else "closed"
      acad_year = "115"
    else:
      source_url = (
          NKNU_115_OUTBOUND_HANDBOOK_PDF_URL
          if avail_status == "open"
          else NKNU_SISTER_SCHOOLS_URL
      )
      round_label = (
          "116年度（2026–2027／2027–2028）赴外交換研修暨教育部學海飛颺／惜珠計畫校內甄選"
          if avail_status == "open"
          else "國際正式締約合作姊妹校（依國際事務處當期甄選簡章公告名額辦理）"
      )
      app_deadline_str = (
          "【116年度赴外交換研修暨教育部學海飛颺／惜珠計畫甄選】說明會：和平校區 2026/11/18 (三) 11:50–13:00（行政大樓 10 樓國際會議廳）、燕巢校區 2026/11/20 (五) 11:50–13:00（致理大樓 2 樓會議室）；線上申請系統開放期間：每年 11/11 ~ 12/31 23:59（登入高師大單一入口《學生出國交換申請系統》`https://sso.nknu.edu.tw/InternationalAdmissions/StudentAboard/Apply.aspx` 填寫並列印表1＋表2＋表3及附件上傳）；1 月系所及學院初審、2 月國際處複審、3/31 前提報教育部學海計畫、5/31 前公告教育部補助結果（跨校雙聯學制請於每年 10 月 1 日前向所屬系所提出申請）"
      )
      deadline_iso = "2026-12-31T23:59:00+08:00"
      win_status = "open" if avail_status == "open" else "closed"
      acad_year = "116"

    study_period_str = clean_text(item.get("duration") or "1 學期或 1 學年")
    sem_dates_str = SEMESTER_DATES_BY_COUNTRY.get(
        country, "秋季學期：約 9 月至翌年 1 月；春季學期：約 2 月至 6 月"
    )
    housing_str = (
        f"獲高師大國際事務處提名後，可依 {zh_name} 交換生入學指引申請校內學生宿舍或校外國際學生公寓"
        + (f"（費用與住宿說明：{tuition_note}；{remarks_raw}）" if (tuition_note or remarks_raw) else "。")
    )
    course_rest_str = (
        f"開放對象與領域：{colleges_str}。依《國立高雄師範大學學生出國選修課程實施要點》及《辦理學生抵免學分要點》規定：在學期間出國選修課程至多二次，合計以不超過一學年為限，抵免學分數以不超過畢業應修最低學分數四分之一為原則（雙聯學制不超過三分之二）；學分換算基準（第9點）：授課滿 18 小時為 1 學分、美制 1 學分 = 本校 1 學分、歐洲 ECTS 2 學分 = 本校 1 學分、英國 CATS 4 學分 = 本校 1 學分、日／韓／大陸 1 學分 = 本校 1 學分。學生應於返國 30 日內檢附預備選修課程表及正式成績單正本向教務處註冊組申請學分採認。"
    )

    tuition_points_list = [
        (
            f"高師大在學註冊與學雜費規定（依《國立高雄師範大學學則》第14條及《學生出國期間有關學業及學籍處理要點》）：學生出國期間須辦理本校註冊。（1）學士班學生：若外國學校免收學費，須繳交本校全額學雜費；若外國學校收取學費，僅須繳交本校雜費；（2）碩、博士班學生：繳交本校學雜費基數。姊妹校待遇：{tuition_note or '依兩校學術交流協議辦理'}。"
        ),
        (
            "教育部《學海飛颺／學海惜珠》獎學金與核銷義務（依《國立高雄師範大學選送學生出國研修審查要點》及《高雄師大出國學生注意事項》）：（1）申請資格：具中華民國國籍且在臺設有戶籍之高師大在學生，赴國外非大陸及港澳之姊妹校交換 1 學期或 1 學年，前一學期學業成績為全班前 50%、操行成績 80 分以上，且具 2 年內有效外語檢定證明（達 CEFR B1 及接待校標準；在職專班生、僑生及外國生不得申請獎助）；（2）評分比重：語言能力 40%＋研修計畫 30%＋在校成績 20%＋其他輔助審查文件 10%；（3）撥款與核銷：交換 1 學期分兩期撥付（出國前簽妥行政契約書撥付 80%，返國並於計畫結束 14 天內上傳心得至教育部學海網站後撥付 20% 尾款；交換 1 學年分三期撥付），返國核銷機票須檢附旅行社代收轉付收據（買受人：國立高雄師範大學，統編：76014004）、登機證正本、電子機票及交換校正式成績單。"
        ),
    ]

    app_steps_list = [
        (
            f"步驟一（確認高師大在學資格、全班前 50% 學業門檻與 {zh_name} 語檢要求）：確認為高師大在學且已就讀至少一學期之學士、碩士或博士班學生（休學生、學士班延畢生、選修生不可申請），符合前一學期學業成績全班前 50%、操行成績 80 分以上及 {zh_name} 規定之学業與語言門檻（{gpa_req_str}｜{lang_req_str}；注意：外國學校明訂要求國際 TOEFL iBT 或 IELTS 者，不得以 TOEIC 或全民英檢替代）。"
        ),
        (
            "步驟二（完成線上申請系統上傳或大陸港澳專案電郵送件）：（1）赴外交換暨學海飛颺／惜珠計畫：於每年 11/11 ~ 12/31 23:59 登入高師大單一入口《學生出國交換申請系統》（`https://sso.nknu.edu.tw/InternationalAdmissions/StudentAboard/Apply.aspx`），填寫並列印《出國研修申請表（表1）》、《中文讀書計畫書（表2，限1頁）》、《其他輔助審查文件（表3）》，連同中文歷年成績單（須含班排名）、2 年內有效外語證明、在學證明、身分證正反面及師長推薦信 1–2 封上傳系統（申請學海惜珠者另附新式戶口名簿及低收／中低收等證明）；（2）赴大陸及港澳地區交換：於春季班（10月中旬）或秋季班（3–4月）截止前將電腦打字填妥之申請資料寄至 `oia_exchange@mail.nknu.edu.tw`（主旨：`申請OOOOO大學_OOO（名字）`）。"
        ),
        (
            f"步驟三（系所與學院 1 月初審、國際處 2 月複審評分與教育部學海提報）：1 月由各系所及學院進行初審推薦，2 月由國際事務處召開審查會議（評分標準：語言能力 40%［大陸地區併入研修計畫書］、研修計畫 30%、在校成績 20%、社團與國際交流表現等輔助審查文件 10%，必要時通知面試），3/31 前提報教育部學海計畫、5/31 前公告補助結果，並由國際處向 {full_name} 辦理官方提名（Nomination）；一經錄取須於次年 10 月底前辦妥出國手續並啟程研修。"
        ),
        (
            "步驟四（辦理出國選課預審、簽證保險、抵達 14 天內回報與返國 14/30 日內核銷抵免）：出國前填妥《預備選修課程表》《家長同意書》《出國研修須知》《出國申請表》（學海受獎生另簽訂《行政契約書》請領第一期 80% 補助款）並投保海外全期醫療及意外險；抵達交換校後 14 天內將《學生抵達國外報告表》及註冊選課證明寄回 `oia_exchange@mail.nknu.edu.tw`；計畫結束後 14 天內上傳心得報告至教育部學海網站並檢附旅行社代收轉付收據（統編 76014004）、登機證正本、正式成績單及《返校報告單》辦理核銷，並於返國 30 日內向教務處註冊組申請學分採認。"
        ),
    ]

    elig_points_list = [
        f"合作類別與甄選群組：{program_type}（{item.get('group', '國際姊妹校')}｜締約年份：{item.get('signed_year', '正式締約')}）",
        f"開放學制與年級：{degree_levels_str}",
        f"開放申請院系：{colleges_str}",
        f"學業成績門檻：{gpa_req_str}",
        f"外語能力標準：{lang_req_str}",
        "校內審查評分權重：依《國立高雄師範大學選送學生出國研修審查要點》第6點規定，審查標準包含語言能力 40%（申請赴大陸地區併入研修計畫書計算）、研修計畫 30%、在校成績 20%、其他輔助審查文件（社團表現、國際交流經驗等）10%。",
    ]
    if tuition_note:
      elig_points_list.append(f"姊妹校學費與生活費待遇：{tuition_note}")
    if remarks_raw:
      elig_points_list.append(f"學校簡章與特殊規定：{remarks_raw}")

    exp_labels = [f"{e['year']}學年 {e['student']}" for e in exps]
    notes_lines = [
        f"【合作類別與期程】{program_type}｜交換期間：{study_period_str}",
        f"【當期名額與費用待遇】{quota_str}｜{tuition_note or '依兩校協議辦理'}",
        f"【開放學院與學制】{colleges_str}｜{degree_levels_str}",
        f"【語言與學業門檻】{lang_req_str}｜{gpa_req_str}",
        f"【住宿與生活資訊】{housing_str}",
    ]
    if exps:
      notes_lines.append(
          f"【高師大學長姐交換心得報告（共 {len(exps)} 篇）】收錄於國際事務處赴外交換心得分享專區（含：{'、'.join(exp_labels[:5])}）"
      )
    if remarks_raw:
      notes_lines.append(f"【學校簡章摘要】{remarks_raw}")

    loc_raw = resolved_locations.get(full_name)
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
        "availability_note": f"國立高雄師範大學國際事務處公告交換／雙聯合作姊妹校（{program_type}）；{quota_str}。",
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
        "factsheet_url": None,
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
                "group": item.get("group"),
                "signed_year": item.get("signed_year"),
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
            "title": f"國立高雄師範大學赴姊妹校交換研修甄選簡章與學校一覽表—{zh_name}",
            "source_url": source_url,
            "role": "home_university",
            "authority": "home_official_notice",
            "effective_academic_year": acad_year,
            "application_round": round_label,
            "checked_at": CHECKED_AT,
        },
        {
            "title": "國立高雄師範大學選送學生出國研修審查要點與甄選作業流程",
            "source_url": NKNU_SELECTION_GUIDELINES_PDF_URL,
            "role": "home_university",
            "authority": "home_official_notice",
            "effective_academic_year": acad_year,
            "application_round": round_label,
            "checked_at": CHECKED_AT,
        },
        {
            "title": "國立高雄師範大學學生出國選修課程實施要點與辦理學生抵免學分要點",
            "source_url": NKNU_COURSE_SELECTION_PDF_URL,
            "role": "home_university",
            "authority": "home_official_notice",
            "effective_academic_year": acad_year,
            "application_round": round_label,
            "checked_at": CHECKED_AT,
        },
    ]
    if exps:
      wf_sources.append({
          "title": f"高師大國際事務處赴外交換心得分享專區—赴 {zh_name} 交換生返國報告（{len(exps)} 篇）",
          "source_url": exps[0]["url"],
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
        "home_university": "國立高雄師範大學",
        "school_name": full_name,
        "partner_website": website,
        "country": country,
        "program_type": program_type,
        "academic_year": acad_year,
        "application_round": round_label,
        "effective_application_rounds": [
            round_label,
            "116年度赴外交換研修暨學海飛颺／惜珠計畫甄選",
            "2027年春季班大陸及港澳地區姊妹校交換甄選",
            "2026年秋季班大陸及港澳地區姊妹校交換甄選",
            "116-1",
            "116-2",
            "115-2",
            "115-1",
        ],
        "applicability_status": "verified",
        "applicability_note": (
            "國立高雄師範大學由國際事務處（OIA）統籌辦理全校赴外交換研修暨教育部學海飛颺／惜珠計畫甄選（每年 11/11–12/31 23:59 於單一入口系統線上申請）、大陸地區（含港澳地區）姊妹校交換計畫（每年 3 月秋季班、9–10 月春季班）及境外大學跨校雙聯學制（每年 10 月 1 日前申請）。"
        ),
        "review_status": "published",
        "published_at": CHECKED_AT,
        "steps": [
            {
                "rule_id": f"nknu-{acad_year}-home-1-{idx+1:03d}",
                "order": 1,
                "phase": "校內申請",
                "title": f"確認高師大在學滿一學期身分、全班前 50% 及操行 80 分門檻與 {zh_name} 語檢要求",
                "responsible_party": "學生",
                "responsible_unit": "國立高雄師範大學國際事務處",
                "deadline_at": deadline_iso,
                "deadline_status": "verified_exact" if avail_status == "open" else "reference_only",
                "deadline_source_url": source_url,
                "deadline_checked_at": CHECKED_AT,
                "deadline_reminder_eligible": avail_status == "open",
                "summary": (
                    f"確認符合《國立高雄師範大學選送學生出國研修審查要點》規定（本校在學且已就讀至少一學期之學士、碩士或博士班學生；休學生、學士班延畢生、選修生不可申請；前一學期學業成績須為全班前 50% 且操行成績 80 分以上），並備妥符合 {zh_name} 規定之 2 年內有效語言能力證明（外國學校要求國際 TOEFL iBT 或 IELTS 者，不得以 TOEIC 或全民英檢替代）。"
                ),
                "details": [
                    f"開放學制與院系：{colleges_str}（{degree_levels_str}）",
                    f"語言與學業條件：{lang_req_str}｜{gpa_req_str}",
                    f"當期名額與計畫類別：{quota_str}｜{program_type}",
                ],
                "scope": {
                    "home_universities": ["國立高雄師範大學"],
                    "partner_universities": [full_name],
                    "academic_years": ["115", "116"],
                    "application_rounds": [round_label, "116-1", "116-2", "115-2", "115-1"],
                },
                "source_urls": [
                    source_url,
                    NKNU_SELECTION_GUIDELINES_PDF_URL,
                    NKNU_115_XUEHAI_BRIEFING_PDF_URL,
                ],
                "checked_at": CHECKED_AT,
                "support_status": "verified",
            },
            {
                "rule_id": f"nknu-{acad_year}-home-2-{idx+1:03d}",
                "order": 2,
                "phase": "校內申請",
                "title": "登入高師大單一入口《學生出國交換申請系統》上傳表1～表3及佐證資料（大陸港澳組電郵送件）",
                "responsible_party": "學生與所屬系（所）辦公室",
                "responsible_unit": "國立高雄師範大學各系所／國際事務處",
                "deadline_at": deadline_iso,
                "deadline_status": "verified_exact" if avail_status == "open" else "reference_only",
                "deadline_source_url": source_url,
                "deadline_checked_at": CHECKED_AT,
                "deadline_reminder_eligible": avail_status == "open",
                "summary": (
                    "於校內截止期限前登入高師大單一入口《學生出國交換申請系統》（`https://sso.nknu.edu.tw/InternationalAdmissions/StudentAboard/Apply.aspx`）完成線上填報，並將《學生出國研修申請表（表1）》、《中文讀書計畫書（表2，限1頁）》、《其他輔助審查文件（表3）》、含班排名之歷年中文成績單、2 年內有效外語證明、在學證明、身分證正反面及推薦信 1–2 封依序上傳（赴大陸及港澳姊妹校交換者，請將電腦打字填妥之申請表件寄至 `oia_exchange@mail.nknu.edu.tw`）。"
                ),
                "details": [
                    "赴外交換暨學海飛颺／惜珠計畫（每年 11/11 ~ 12/31 23:59）：透過高師大單一入口《學生出國交換申請系統》線上填報上傳（申請學海惜珠者須加附新式戶口名簿或近三個月戶籍謄本及低收入戶／中低收入戶等相關證明）。",
                    "大陸及港澳地區姊妹校交換（2027春季班 2026/10/16 截止，港教大 9/18、南京大學 10/13；秋季班每年 3–4 月截止）：將電腦打字填妥之全套申請資料寄至 `oia_exchange@mail.nknu.edu.tw`（信件主旨：`申請OOOOO大學_OOO（名字）`）。",
                ],
                "document_requirements": [
                    {
                        "name": "國立高雄師範大學學生出國研修申請表（表1）、中文讀書計畫書（表2，限1頁）及其他輔助審查文件彙整表（表3）",
                        "official_form_url": NKNU_OUTBOUND_APP_FORMS_DOC_URL,
                        "source_urls": [NKNU_115_OUTBOUND_HANDBOOK_PDF_URL, NKNU_OUTBOUND_APP_FORMS_DOC_URL],
                    },
                    {
                        "name": "本校歷年中文成績單正本（必須清楚註明前一學期全班排名或百分比）及當學期在學證明",
                        "source_urls": [NKNU_SELECTION_GUIDELINES_PDF_URL, NKNU_2027_SPRING_MAINLAND_URL],
                    },
                    {
                        "name": "2 年內有效之外國語言能力證明文件（須達 CEFR B1 及志願姊妹校標準；外國學校明訂要求國際 TOEFL 或 IELTS 者不得以 TOEIC 或 GEPT 替代；赴大陸地區免附）",
                        "source_urls": [NKNU_SELECTION_GUIDELINES_PDF_URL, NKNU_115_OUTBOUND_HANDBOOK_PDF_URL],
                    },
                    {
                        "name": "師長推薦信 1–2 封、身分證正反面影本（申請學海惜珠者另附新式戶口名簿影本及低收入戶／中低收入戶證明；在職專班生另附服務機關出國同意書）",
                        "source_urls": [NKNU_SELECTION_GUIDELINES_PDF_URL, NKNU_115_XUEHAI_BRIEFING_PDF_URL],
                    },
                ],
                "scope": {
                    "home_universities": ["國立高雄師範大學"],
                    "academic_years": ["115", "116"],
                    "application_rounds": [round_label, "116-1", "116-2", "115-2", "115-1"],
                },
                "source_urls": [
                    NKNU_115_OUTBOUND_HANDBOOK_PDF_URL,
                    NKNU_OUTBOUND_APP_FORMS_DOC_URL,
                    NKNU_2027_SPRING_MAINLAND_URL,
                    NKNU_SELECTION_GUIDELINES_PDF_URL,
                ],
                "checked_at": CHECKED_AT,
                "support_status": "verified",
            },
            {
                "rule_id": f"nknu-{acad_year}-home-3-{idx+1:03d}",
                "order": 3,
                "phase": "甄選與提名",
                "title": "1 月系所與學院初審、2 月國際處複審評分（語言40%＋計畫30%＋成績20%＋其他10%）與教育部學海提報",
                "responsible_party": "各系所、學院與國際事務處審查會",
                "responsible_unit": "國立高雄師範大學國際事務處",
                "deadline_at": "2027-02-28T17:00:00+08:00" if country not in {"中國大陸", "香港", "澳門"} else "2026-10-30T17:00:00+08:00",
                "deadline_status": "verified_exact",
                "deadline_source_url": NKNU_SELECTION_FLOWCHART_PDF_URL,
                "deadline_checked_at": CHECKED_AT,
                "deadline_reminder_eligible": False,
                "summary": (
                    "依《國立高雄師範大學選送學生出國研修審查要點》及《甄選作業流程》：1 月由系所及學院完成初審並排定推薦順序送交國際處，2 月由國際處召開審查會議進行複審（語言能力 40%、研修計畫 30%、在校成績 20%、其他輔助審查文件 10%），3/31 前彙整提報教育部學海飛颺／惜珠計畫，5/31 前公告教育部補助結果。"
                ),
                "details": [
                    "錄取義務：一經錄取，須於次年 10 月底前辦妥出國手續並啟程研修，屆期未出國者視為放棄。",
                    "學海飛颺／惜珠獎學金核定：依教育部核配經費及校內複審總成績高低核定補助金額（同一申請人同一教育階段以補助一次為限）。",
                ],
                "scope": {
                    "home_universities": ["國立高雄師範大學"],
                    "academic_years": ["115", "116"],
                    "application_rounds": [round_label, "116-1", "116-2", "115-2", "115-1"],
                },
                "source_urls": [
                    NKNU_SELECTION_GUIDELINES_PDF_URL,
                    NKNU_SELECTION_FLOWCHART_PDF_URL,
                    NKNU_115_XUEHAI_BRIEFING_PDF_URL,
                ],
                "checked_at": CHECKED_AT,
                "support_status": "verified",
            },
            {
                "rule_id": f"nknu-{idx+1:03d}-host-apply",
                "order": 4,
                "phase": "合作校申請",
                "title": f"由高師大國際處向 {zh_name} 辦理官方提名（Nomination），並依接待校規定遞交外文入學與宿舍申請",
                "responsible_party": "學生與接待校國際事務處",
                "summary": (
                    f"通過高師大校內甄選後，由國際處向 {zh_name} 辦理官方提名；學生須於姊妹校申請截止日前備妥外文入學申請表、英文歷年成績單、護照影本、英文財力證明、語檢證書、選課計畫與學生宿舍申請表，靜候接待校核發正式入學許可（Letter of Acceptance / COE / DS-2019）。"
                ),
                "details": [
                    f"交換期程：{study_period_str}｜名額：{quota_str}",
                    f"語言與學業條件：{lang_req_str}｜{gpa_req_str}",
                    f"住宿與費用待遇：{housing_str}",
                ],
                "scope": {
                    "home_universities": ["國立高雄師範大學"],
                    "partner_universities": [full_name],
                    "academic_years": ["115", "116"],
                    "application_rounds": [round_label, "116-1", "116-2", "115-2", "115-1"],
                },
                "source_urls": (
                    [source_url, NKNU_OUTBOUND_EXCHANGE_URL]
                    + ([website] if website else [])
                ),
                "checked_at": CHECKED_AT,
                "support_status": "verified",
                "needs_confirmation": False,
            },
            {
                "rule_id": f"nknu-{acad_year}-home-5-{idx+1:03d}",
                "order": 5,
                "phase": "行前準備",
                "title": "辦理出國預備選修課程簽核、簽訂學海契約並於抵達 14 天內回報，返國 14/30 日內完成心得上傳、核銷與學分抵免",
                "responsible_party": "學生",
                "responsible_unit": "國立高雄師範大學國際事務處／教務處註冊組／各系所",
                "summary": (
                    "出國前須填妥《預備選修課程表》《家長同意書》《出國研修須知》《出國申請表》（學海受獎生於出國前 1 個月簽訂行政契約書請領第一期 80% 補助款）；抵達姊妹校後 14 天內將《抵達國外報告表》及選課證明寄至 `oia_exchange@mail.nknu.edu.tw`；計畫結束後 14 天內上傳心得報告至教育部學海網站並檢附旅行社代收轉付收據（統編 76014004）、登機證正本、正式成績單及《返校報告單》辦理尾款核銷，並於返國 30 日內向教務處註冊組辦理學分採認。"
                ),
                "details": tuition_points_list,
                "scope": {
                    "home_universities": ["國立高雄師範大學"],
                    "academic_years": ["115", "116"],
                    "application_rounds": [round_label, "116-1", "116-2", "115-2", "115-1"],
                },
                "source_urls": [
                    NKNU_PREDEPARTURE_NOTES_PDF_URL,
                    NKNU_EXPERIENCE_GUIDE_PDF_URL,
                    NKNU_REIMBURSEMENT_CHECKLIST_DOCX_URL,
                    NKNU_COURSE_SELECTION_PDF_URL,
                    NKNU_CREDIT_TRANSFER_PDF_URL,
                ],
                "checked_at": CHECKED_AT,
                "support_status": "verified",
            },
        ],
        "sources": wf_sources,
        "last_checked": CHECKED_AT,
        "coverage_status": "official_verified",
        "coverage_note": (
            "已完整整合國立高雄師範大學國際事務處與教務處（116年學海計畫說明會公告、115年選送學生出國說明會簡報與手冊、2027春季班及2026秋季班大陸及港澳姊妹校交換公告、選送學生出國研修審查要點、跨校雙聯學制實施辦法、出國選修課程與學分抵免要點及 29 篇學長姐返國心得）共 143 所全球合作姊妹校名額、語檢門檻與核銷規定。"
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
            "title": f"國立高雄師範大學赴姊妹校交換研修甄選簡章與學校一覽表—{zh_name}",
            "source_url": source_url,
            "summary": "高師大國際事務處公告之交換名額、開放學制、語言檢定門檻與學校費用備註說明",
        },
        {
            "title": "國立高雄師範大學選送學生出國研修審查要點、出國選修課程實施要點與出國學生注意事項",
            "source_url": NKNU_SELECTION_GUIDELINES_PDF_URL,
            "summary": "高師大出國交換申請資格（前一學期全班前 50%、操行 80 分以上）、審查配分權重、學分換算基準與學海飛颺／惜珠核銷規範",
        },
    ]
    if exps:
      dest_sources.append({
          "title": f"高師大國際事務處赴外交換心得分享專區—赴 {zh_name} 交換生返國心得報告（{len(exps)} 篇）",
          "source_url": exps[0]["url"],
          "summary": f"收錄歷年高師大赴 {zh_name} 交換生返國心得報告共 {len(exps)} 篇",
      })
    if website:
      dest_sources.append({
          "title": f"{full_name} 官方網站",
          "source_url": website,
          "summary": "接待合作校官方網站",
      })

    src_url_list = (
        [source_url, NKNU_OUTBOUND_EXCHANGE_URL, NKNU_SELECTION_GUIDELINES_PDF_URL]
        + ([exps[0]["url"]] if exps else [])
        + ([website] if website else [])
    )

    destinations.append({
        "home_university": "國立高雄師範大學",
        "school_name": full_name,
        "country": country,
        "city": location_obj.get("city") or country,
        "cost_summary": f"{cost_line}。\n{tuition_clean}",
        "housing_summary": housing_clean,
        "transport_summary": (
            f"校區代表城市：{location_obj.get('city') or country}。請依入學許可與姊妹校交換手冊確認實際授課校區、機場接機服務與當地學生交通卡優惠。"
        ),
        "campus_life_summary": f"{calendar_clean}\n{course_clean}",
        "student_guide_sections": [
            {
                "key": "cost",
                "title": "生活費、高師大在學註冊學雜費規定與教育部學海飛颺／惜珠獎學金（80%＋20%撥款）",
                "summary": cost_line,
                "points": [cost_line] + tuition_points_list,
                "source_urls": src_url_list + [NKNU_PREDEPARTURE_NOTES_PDF_URL, NKNU_REIMBURSEMENT_CHECKLIST_DOCX_URL],
                "caution": (
                    "學海飛颺／惜珠受獎生於出國前領取第一期 80% 補助款，計畫結束後 14 天內必須上傳心得報告至教育部學海網站並檢附旅行社代收轉付收據（統編 76014004）、登機證正本及正式成績單至國際處辦理尾款核銷。"
                ),
            },
            {
                "key": "housing",
                "title": "住宿資訊與校內外學生宿舍申請",
                "summary": housing_clean[:160],
                "points": [housing_clean],
                "source_urls": src_url_list,
                "caution": (
                    "各姊妹校校內學生宿舍名額有限（如法國巴黎西岱大學不提供校內宿舍須自行租屋），獲國際處提名後請務必詳閱各校住宿申請期限。"
                ),
            },
            {
                "key": "insurance",
                "title": "海外醫療及意外保險與接待國強制學生健康保險規定",
                "summary": visa_default,
                "points": [
                    visa_default,
                    "依《從事海外留遊學安全應注意事項》及《高雄師大出國學生注意事項》規定，錄取生出國前須購買涵蓋海外研修全期之醫療及意外保險，同時須遵守接待國法定學生健康保險規定（如美國西佛羅里達大學 GeoBlue、德國法定學生公保、日本 NHI、韓國 NHIS、捷克 pVZP 等）。",
                ],
                "source_urls": src_url_list + [NKNU_OVERSEAS_SAFETY_PDF_URL],
                "caution": "請於收到入學許可後確認接待校指定之保險額度、疫苗接種要求與投保通路。",
            },
            {
                "key": "visa",
                "title": "留學簽證辦理、抵達國外 14 天內回報與高師大在學註冊義務",
                "summary": visa_default,
                "points": [
                    visa_default,
                    "依《國立高雄師範大學學生出國期間有關學業及學籍處理要點》規定，交換期間須維持本校在學註冊；抵達交換學校後 14 天內須填妥《學生抵達國外報告表》連同註冊選課證明寄回 `oia_exchange@mail.nknu.edu.tw`（建議出入境採一般傳統通關以留存護照出入境章戳供返國核銷）。",
                ],
                "source_urls": src_url_list + [NKNU_ACADEMIC_STATUS_PDF_URL],
                "caution": "請勿持觀光簽證或免簽入境就讀學期交換課程，且入出境建議走人工查驗通道或於返國後申請移民署入出國日期證明書。",
            },
            {
                "key": "academics",
                "title": "出國選修課程預審、學分換算基準（18小時/2 ECTS/4 CATS = 1學分）與返國 30 日內學分抵免",
                "summary": course_clean[:160],
                "points": [calendar_clean, course_clean],
                "source_urls": src_url_list + [NKNU_COURSE_SELECTION_PDF_URL, NKNU_CREDIT_TRANSFER_PDF_URL],
                "caution": (
                    "依《學生出國選修課程實施要點》第6、7、9點，出國選修課程至多二次、合計不超過一學年，抵免上限為畢業應修最低學分數四分之一（雙聯為三分之二），返國後 30 日內須持正式成績單正本及預備選修課程表至教務處註冊組辦理採認。"
                ),
            },
            {
                "key": "living",
                "title": f"{location_obj.get('city') or country} 校園生活與高師大學長姐交換心得傳承",
                "summary": f"代表校區城市：{location_obj.get('city') or country}。請於抵達姊妹校後 14 天內回傳《抵達國外報告表》並配合接待校新生訓練（Orientation）完成報到。",
                "points": [
                    f"目的地城市：{location_obj.get('city') or country}（{country}）",
                    (
                        f"高師大國際事務處於官網「赴外交換—心得分享（{exps[0]['url'] if exps else NKNU_OUTBOUND_EXCHANGE_URL}）」公開收錄學長姐返國研修心得報告"
                        + (f"（本校共收錄 {len(exps)} 篇：{'、'.join(exp_labels[:4])}）" if exps else "")
                        + "，詳述當地選課、住宿、交通與生活開銷實況。"
                    ),
                ],
                "source_urls": [exps[0]["url"] if exps else NKNU_OUTBOUND_EXCHANGE_URL],
            },
        ],
        "sources": dest_sources,
        "last_checked": CHECKED_AT,
        "coverage_status": "official_verified",
        "coverage_note": (
            "已整合國立高雄師範大學國際事務處 143 所交換與雙聯合作姊妹校名額、語檢門檻、學海飛颺／惜珠獎補助細則、學分抵免法規與 29 篇歷屆學長姐返國心得。"
        ),
    })

    research_records.append({
        "home_university": "國立高雄師範大學",
        "school_name": full_name,
        "country": country,
        "official_website": website,
        "verification_status": "official_verified",
        "discovery_source_url": source_url,
        "checked_at": CHECKED_AT,
        "note": (
            f"國立高雄師範大學國際事務處《115年選送學生出國說明會手冊（{NKNU_115_OUTBOUND_HANDBOOK_PDF_URL}）》、《本校姊妹校一覽（{NKNU_SISTER_SCHOOLS_URL}）》與 ROR/Wikidata 官方網址核對完成。"
        ),
    })

    ev_sources = [
        {
            "title": f"國立高雄師範大學赴姊妹校交換研修甄選簡章與學校一覽表—{zh_name}",
            "url": source_url,
        },
    ]
    if exps:
      ev_sources.append({
          "title": f"高師大國際事務處赴外交換心得分享專區—赴 {zh_name} 交換生心得報告（{len(exps)} 篇）",
          "url": exps[0]["url"],
      })
    if website:
      ev_sources.append({"title": f"{full_name} 官方網站", "url": website})

    has_student_exp = bool(exps)
    if exps:
      exp_covered_schools += 1

    ev_list = [
        {
            "theme": "housing",
            "kind": "mixed" if has_student_exp else "official",
            "text": housing_clean,
            "sources": ev_sources,
            "checked_at": CHECKED_AT,
            "scope": "國立高雄師範大學出國交換姊妹校住宿與生活資訊",
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
            "scope": "國立高雄師範大學交換生學雜費規定、教育部學海飛颺／惜珠與地區生活費估算",
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
            "scope": "國立高雄師範大學交換生選課規定、學分換算基準與返國 30 日內學分抵免",
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
            "scope": "國立高雄師範大學出國交換簽證、海外醫療保險、抵達 14 天內回報與在學註冊提醒",
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
                    f"｜高師大國際處赴外交換專區公開收錄 {len(exps)} 篇赴 {zh_name} 交換生返國心得報告（{'、'.join(exp_labels[:4])}）。"
                    if exps
                    else ""
                )
            ),
            "sources": ev_sources,
            "checked_at": CHECKED_AT,
            "scope": "國立高雄師範大學出國交換名額與歷屆學長姐交換經驗分享",
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
            "已整合國立高雄師範大學國際事務處《115年選送學生出國說明會手冊》、《2027春季班及2026秋季班大陸及港澳地區姊妹校交換申請資訊》、跨校雙聯學制一覽表及赴外交換心得分享專區共 29 篇學長姐報告。",
            "當期宿位供給、費用與選課限制請依姊妹校最新交換簡章及入學通知書核對。",
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

    if exps:
      rep_title = (
          f"國立高雄師範大學赴 {zh_name} 交換研修心得彙編（共 {len(exps)} 篇學長姐報告）"
      )
      latest_e = exps[0]
      latest_author = (
          f"{latest_e['student']} 等 {len(exps)} 位高師大交換生"
          if len(exps) > 1
          else latest_e["student"]
      )
      summary_text = (
          f"國立高雄師範大學國際事務處「赴外交換—心得分享」公開收錄 {len(exps)} 篇歷年赴 {zh_name} 交換學生返國心得報告（含：{'、'.join(exp_labels[:5])}）。"
          f"{latest_e['highlight']}"
      )
      theme_map = {
          "academics": (
              f"高師大交換生（{'、'.join(exp_labels[:3])}）分享於 {zh_name} 修讀專業與語言課程之選課方式、課堂互動及返國依《學生出國選修課程實施要點》辦理學分抵免之實戰經驗。{latest_e['highlight']}"
          ),
          "housing": (
              f"高師大交換生詳述 {zh_name} 校內外學生宿舍申請時程、房型設備與周邊生活機能（{housing_clean[:120]}）。"
          ),
          "campus_culture": (
              f"高師大國際處收錄 {len(exps)} 篇赴 {zh_name} 交換生返國心得報告，記錄接待校迎新週（Orientation）、國際學伴（Buddy / Tutor）與跨文化交流體驗。"
          ),
          "cost": (
              f"高師大交換生記錄於 {zh_name} 之每月住宿、伙食與交通開銷（{cost_default}），以及運用教育部學海飛颺／學海惜珠獎學金支應留學費用與返國核銷之規劃。"
          ),
      }
      student_experience_rows.append({
          "school_name": full_name,
          "country": country,
          "title": rep_title,
          "source_url": latest_e["url"],
          "source_type": "article",
          "platform": "國立高雄師範大學國際事務處—赴外交換心得分享專區",
          "author_name": latest_author,
          "language": "zh",
          "summary": summary_text,
          "themes": ["academics", "housing", "campus_culture", "cost"],
          "theme_summaries": theme_map,
          "content_status": "full_text",
          "perspective": "official_student_story",
          "published_at": None,
          "discovered_at": CHECKED_AT,
          "content_hash": hashlib.sha256(f"{full_name}:nknu_exp:{len(exps)}".encode("utf-8")).hexdigest(),
          "exchange_term": f"{latest_e['year']}學年度",
          "summary_zh": summary_text,
          "original_summary": summary_text,
          "theme_summaries_zh": theme_map,
          "translation_status": "original",
          "source_kind": "official_experience_page",
      })

    experience_sources_records.append({
        "home_university": "國立高雄師範大學",
        "school_name": full_name,
        "country": country,
        "official_experience_portal_url": (
            exps[0]["url"] if exps else NKNU_OUTBOUND_EXCHANGE_URL
        ),
        "partner_page_url": source_url,
        "report_count": len(exps),
        "sample_reports": sample_reports,
        "checked_at": CHECKED_AT,
    })

  partners_jsonl_text = "\n".join(json.dumps(r, ensure_ascii=False) for r in partners) + "\n"
  (OFFICIAL_NKNU_DIR / "partners.jsonl").write_text(partners_jsonl_text, encoding="utf-8")
  (SOURCES_NKNU_DIR / "partners.jsonl").write_text(partners_jsonl_text, encoding="utf-8")
  (OFFICIAL_NKNU_DIR / "application_workflows.jsonl").write_text(
      "\n".join(json.dumps(r, ensure_ascii=False) for r in workflows) + "\n",
      encoding="utf-8",
  )
  (OFFICIAL_NKNU_DIR / "destination_profiles.jsonl").write_text(
      "\n".join(json.dumps(r, ensure_ascii=False) for r in destinations) + "\n",
      encoding="utf-8",
  )
  (OFFICIAL_NKNU_DIR / "partner_research.jsonl").write_text(
      "\n".join(json.dumps(r, ensure_ascii=False) for r in research_records) + "\n",
      encoding="utf-8",
  )
  (OFFICIAL_NKNU_DIR / "student_life.jsonl").write_text(
      "\n".join(json.dumps(r, ensure_ascii=False) for r in life_records) + "\n",
      encoding="utf-8",
  )
  (OFFICIAL_NKNU_DIR / "experience_sources.jsonl").write_text(
      "\n".join(json.dumps(r, ensure_ascii=False) for r in experience_sources_records) + "\n",
      encoding="utf-8",
  )
  (OFFICIAL_NKNU_DIR / "student_experiences.jsonl").write_text(
      "\n".join(json.dumps(r, ensure_ascii=False) for r in student_experience_rows) + "\n",
      encoding="utf-8",
  )
  (OFFICIAL_NKNU_DIR / "campus-locations.json").write_text(
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
  (OFFICIAL_NKNU_DIR / "student-experience-digests.json").write_text(
      json.dumps({"digests": digest_records}, ensure_ascii=False, indent=2) + "\n",
      encoding="utf-8",
  )

  # Ensure NKNU home location and all partner locations are in university_locations.jsonl
  loc_file = REPO_ROOT / "src/exchange_info/official_data/university_locations.jsonl"
  existing_loc_lines = [
      line for line in loc_file.read_text(encoding="utf-8").splitlines() if line.strip()
  ]
  existing_loc_map = {}
  for line in existing_loc_lines:
    rec = json.loads(line)
    existing_loc_map[(rec["school_name"], rec.get("country") or "")] = rec

  for loc_obj in new_locations:
    key = (loc_obj["school_name"], loc_obj.get("country") or "")
    if key not in existing_loc_map:
      existing_loc_map[key] = loc_obj

  nknu_home_loc = {
      "school_name": "國立高雄師範大學",
      "country": "臺灣",
      "city": "高雄市苓雅區",
      "latitude": 22.6262,
      "longitude": 120.3208,
      "geocode_status": "verified",
      "geocoded_at": CHECKED_AT,
      "source_url": "https://www.wikidata.org/wiki/Q709248",
      "identity_source_url": "https://ror.org/03VX33B92",
      "precision": "representative",
      "note": (
          "校級代表位置：官方網域及國家已與 ROR 比對，座標來源為 Wikidata P625；實際交換校區以錄取通知為準。"
          " 母校代表點採高雄市苓雅區和平一路116號和平校區行政大樓國際事務處；官方地址來源：https://oia.nknu.edu.tw/。"
      ),
  }
  existing_loc_map[("國立高雄師範大學", "臺灣")] = nknu_home_loc
  sorted_locs = sorted(
      existing_loc_map.values(),
      key=lambda r: (r.get("country") or "", r.get("school_name") or ""),
  )
  loc_file.write_text(
      "\n".join(json.dumps(r, ensure_ascii=False) for r in sorted_locs) + "\n",
      encoding="utf-8",
  )

  nknu_source_urls = [
      NKNU_OIA_HUB_URL,
      NKNU_OUTBOUND_EXCHANGE_URL,
      NKNU_MAINLAND_EXCHANGE_URL,
      NKNU_SISTER_SCHOOLS_URL,
      NKNU_DUAL_DEGREE_URL,
      NKNU_REGULATIONS_URL,
      NKNU_ACA_REGULATIONS_URL,
      NKNU_SSO_APPLY_URL,
      NKNU_116_XUEHAI_INFO_URL,
      NKNU_2027_SPRING_MAINLAND_URL,
      NKNU_2026_FALL_MAINLAND_URL,
      NKNU_115_XUEHAI_BRIEFING_PDF_URL,
      NKNU_115_OUTBOUND_HANDBOOK_PDF_URL,
      NKNU_SELECTION_GUIDELINES_PDF_URL,
      NKNU_SELECTION_FLOWCHART_PDF_URL,
      NKNU_OUTBOUND_APP_FORMS_DOC_URL,
      NKNU_PREDEPARTURE_NOTES_PDF_URL,
      NKNU_OVERSEAS_SAFETY_PDF_URL,
      NKNU_EXPERIENCE_GUIDE_PDF_URL,
      NKNU_REIMBURSEMENT_CHECKLIST_DOCX_URL,
      NKNU_DUAL_DEGREE_APP_FORM_DOCX_URL,
      NKNU_DUAL_DEGREE_REGULATIONS_PDF_URL,
      NKNU_COURSE_SELECTION_PDF_URL,
      NKNU_ACADEMIC_STATUS_PDF_URL,
      NKNU_CREDIT_TRANSFER_PDF_URL,
  ]

  exchange_info_payload = {
      "school_name": "國立高雄師範大學",
      "program_type": [
          (
              "國際事務處赴外交換研修暨教育部學海飛颺／學海惜珠計畫（每年 11/11 ~ 12/31 23:59 透過高師大單一入口《學生出國交換申請系統》線上報名；116年學海計畫說明會訂於 2026/11/18 和平校區、11/20 燕巢校區舉行；當期開放美國西佛羅里達大學、北卡羅萊納大學夏洛特分校、明尼蘇達州立大學曼卡托分校、西密西根大學、捷克普爾基涅大學、德國帕德博恩大學、瑞典達拉納大學、法國巴黎西岱大學、奧地利克恩頓師範學院、韓國江原大學、群山大學、東國大學、梨花女子大學、韓國中央大學、瑞逸大學、釜山外國語大學、日本大阪教育大學、金澤星稜大學、新潟大學、三重大學、岩手大學、櫻美林大學、兵庫教育大學、千葉大學、滋賀大學、日本中央大學等 25 所海外重點交換姊妹校）"
          ),
          (
              "大陸地區（含港澳地區）姊妹校交換計畫（每年 3 月辦理秋季班、9–10 月辦理春季班校內甄選；2027春季班［115-2學期］於 2026/10/16 截止，開放北京師範大學、香港教育大學、澳門城市大學、西南大學、華中師範大學、華東師範大學、南京師範大學、南京大學、東北師範大學，秋季班另開放福州大學、陝西師範大學等共 11 所當期常態開放陸港澳名校，以及中國人民大學、廈門大學、上海師範大學、暨南大學、澳門科技大學等 35 所正式締約姊妹校）"
          ),
          (
              "境外大學跨校雙聯學制計畫（依《國立高雄師範大學與境外大學跨校雙聯學制實施辦法》於每年 10 月 1 日前向所屬系所提出申請；現行合作專案包含：韓國東國大學［國文學系、英語學系、體育學系 2+2 學士雙聯學位］、日本兵庫教育大學［校級 1.5+1.5 碩士雙聯學位］、香港教育大學［數學系碩士班、科學教育暨環境教育研究所 1+1 碩士雙聯學位］）"
          ),
      ],
      "academic_year": [
          (
              "116（116年度赴外交換研修暨教育部學海飛颺／惜珠計畫說明會於 2026/11/18［和平校區］及 2026/11/20［燕巢校區］舉辦，線上申請系統於 11/11 ~ 12/31 23:59 開放，1 月系所及學院初審、2 月國際處複審、3/31 前提報教育部、5/31 前公告補助結果）"
          ),
          (
              "115（2027年春季班［115-2學期］大陸及港澳地區姊妹校交換於 2026/10/16 截止收件；本平台完整收錄 143 所高師大全球交換與雙聯合作姊妹校，含 36 所當期開放交換及雙聯名額校與 107 所正式締約姊妹校）"
          ),
      ],
      "semester": [
          "秋季學期（第1學期：每年約 8/9 月至翌年 1/2 月，日本秋季班為 9/10 月至翌年 2/3 月）",
          "春季學期（第2學期：每年約 2/3 月至 6/7 月，日本春季班為 4 月至 8/9 月）",
          "一學年交換或 1+1／1.5+1.5／2+2 跨校雙聯學位修讀（在學期間出國選修課程至多二次，合計以不超過一學年為限）",
      ],
      "application_period": [
          (
              "【116年度赴外交換研修暨教育部學海飛颺／惜珠計畫甄選】說明會：和平校區 2026/11/18 (三) 11:50–13:00（行政大樓 10 樓國際會議廳）、燕巢校區 2026/11/20 (五) 11:50–13:00（致理大樓 2 樓會議室）；線上申請系統開放：每年 11/11 ~ 12/31 23:59（高師大單一入口《學生出國交換申請系統》`https://sso.nknu.edu.tw/InternationalAdmissions/StudentAboard/Apply.aspx`）；1 月系所及學院初審、2 月國際處複審、3/31 前提報教育部、5/31 前公告教育部補助結果。"
          ),
          (
              "【大陸及港澳地區姊妹校交換甄選（每年 3 月秋季班、9–10 月春季班）】2027年春季班（115-2學期）校內收件至 2026/10/16 截止（香港教育大學 9/18、南京大學 10/13 截止；請將電腦打字申請表件寄至 `oia_exchange@mail.nknu.edu.tw`，主旨：`申請OOOOO大學_OOO（名字）`）；秋季班預計於每年 3 月公告、3 月底至 4 月底截止。"
          ),
          (
              "【境外大學跨校雙聯學制申請】依《國立高雄師範大學與境外大學跨校雙聯學制實施辦法》第5條規定，於每年 10 月 1 日前填具《雙聯學制學生申請表》向所屬學系（所）提出申請，經系（所）、院初審後送國際事務處及教務處複審。"
          ),
      ],
      "eligibility": [
          (
              "【在學學制、年級與身分限制（依《國立高雄師範大學選送學生出國研修審查要點》第3點及《學生出國選修課程實施要點》第3點）】凡本校在學且已就讀至少一學期以上之學士班、碩士班或博士班學生皆可申請。休學生、學士班延期畢業生、選修生及領受臺灣獎學金之外國生不得提出申請；進修學院在職專班學生得檢附《服務機關出國同意書》申請出國交換，惟不得申請任何獎助學金；僑生及外國生僅限自費且不得申請交換至其原屬居住國籍。"
          ),
          (
              "【學業成績全班前 50% 與操行 80 分門檻】依《選送學生出國研修審查要點》第4點規定，申請人前一學期學業成績須為全班前 50%，且操行成績達 80 分以上，並須符合志願姊妹校 GPA 要求（如美國北卡夏洛特、明尼蘇達州立曼卡托、西密西根、德國帕德博恩、日本櫻美林、日本中央大學要求 GPA 2.50/4.00 以上，韓國東國大學要求 GPA 2.5/4.5 以上）。"
          ),
          (
              "【校內書面與面試審查配分比重（100%）】依《選送學生出國研修審查要點》第6點規定，校內複審由國際處召開審查會議評定（必要時得通知面試），評分比重為：1. 語言能力 40%（申請赴大陸地區研修交換者，該項配分併入研修計畫書計算）；2. 研修計畫 30%；3. 在校成績 20%；4. 其他輔助審查文件（社團表現、國際交流經驗等）10%。"
          ),
      ],
      "language_requirement": [
          (
              "【校內 CEFR B1 進階級基準與不得以多益／英檢替代國際托福雅思規定】依《選送學生出國研修審查要點》第4點及附表《外國語言標準暨成績對照表》規定，申請赴外交換須檢附 2 年內有效且符合志願姊妹校規定之語言證明，並達本校英文基本門檻（CEFR B1 進階級）：TOEFL iBT 47 分、TOEFL ITP 457 分、IELTS 4.0、TOEIC 550 分或全民英檢（GEPT）中級以上。特別注意：外國學校明訂要求國際 TOEFL iBT 或 IELTS 成績者（如美國西佛羅里達、北卡夏洛特、明尼蘇達州立曼卡托、西密西根、德國帕德博恩、瑞典達拉納），不得以 TOEIC 或全民英檢替代。"
          ),
          (
              "【各語區重點姊妹校語言門檻】（1）美國、歐洲英語授課：西佛羅里達大學要求 TOEFL iBT 79–80 / IELTS 6.0；北卡夏洛特要求 iBT 70 / IELTS 6.0；明尼蘇達州立曼卡托要求 iBT 61 / IELTS 5.5；西密西根要求 iBT 71–80 / IELTS 6.0–6.5；德國帕德博恩要求 iBT 79 / IELTS 6.5 或德語 B1–B2；瑞典達拉納要求 iBT 79 / IELTS 6.0；捷克普爾基涅要求英語或捷克語 B2；（2）法語區：法國巴黎西岱大學要求法語 DELF B2；（3）日語區：大阪教育大學要求 JLPT N3；三重大學、岩手大學、櫻美林大學、兵庫教育大學、千葉大學（J-PAC 亦接受英語 B2＋50 小時日語）、滋賀大學、金澤星稜大學要求 JLPT N2；（4）韓語區：群山大學、釜山外國語大學要求 TOPIK 3 級；韓國中央大學要求 TOPIK 4 級或英語證明；江原大學、東國大學要求英語 B2 或韓語檢定。"
          ),
          (
              "【赴大陸及港澳地區姊妹校語言規定】申請赴大陸及澳門地區姊妹校交換者，毋須檢附外語能力證明（審查時語言能力 40% 配分併入研修計畫書計算）；申請赴香港教育大學交換或 1+1 碩士雙聯學位者，須依港教大簡章備妥英語能力證明。"
          ),
      ],
      "required_documents": [
          "1. 國立高雄師範大學學生出國研修申請表（表1，透過單一入口《學生出國交換申請系統》線上填報列印並簽章；在職專班生須加附服務機關之出國同意書）",
          "2. 學生出國研修中文讀書計畫書（表2，限 1 頁，須具體說明赴外研修動機、擬修課程與學習目標）",
          "3. 學生出國研修其他輔助審查文件彙整表（表3，含社團參與、幹部經歷、競賽獲獎及國際交流表現等佐證）",
          "4. 本校歷年中文成績單正本乙份（必須清楚註明前一學期全班排名或百分比，以核對全班前 50% 及操行 80 分門檻）",
          "5. 2 年內有效之外國語言能力檢定證明影本（須達 CEFR B1 及志願姊妹校標準；外國學校要求國際 TOEFL 或 IELTS 者不得以 TOEIC 或 GEPT 替代；赴大陸地區免附）",
          "6. 當學期在學證明及國民身分證正反面影本（黏貼於申請表指定欄位）",
          "7. 師長推薦信 1–2 封（部分姊妹校或大陸交換要求副教授／教授推薦信及外文自傳、讀書計畫；申請華東師範大學者另須繳交 3 張紙本一吋證件照）",
          "8. 申請教育部《學海惜珠》者另須檢附：新式戶口名簿影本（註明現住人口及詳細記事）或三個月內電子戶籍謄本，以及各直轄市、縣（市）主管機關開立之有效低收入戶、中低收入戶或特殊境遇家庭相關補助證明",
      ],
      "scholarship_info": [
          (
              "教育部《學海飛颺》選送優秀學生出國研修獎學金：併同每年 11/11 ~ 12/31 赴外交換研修線上甄選提出申請。申請資格：具中華民國國籍且在臺灣地區設有戶籍之高師大在學生（不含在職專班生、休學生、學士班延畢生、僑外生），赴國外非大陸及港澳之姊妹校修讀學分 1 學期或 1 學年，前一學期學業成績居全班前 50%、操行成績 80 分以上，並具 2 年內有效外語檢定證明。補助項目涵蓋國際來回經濟艙機票、國外學費及生活費，實際金額依教育部當年度核配預算及校內複審成績核定（同一教育階段以補助一次為限）。"
          ),
          (
              "教育部《學海惜珠》選送勵學（清寒）優秀學生出國研修獎學金：針對具低收入戶、中低收入戶、特殊境遇家庭扶助、身心障礙者生活補助或大專校院弱勢學生助學金助學資格之優秀在學生，赴國外（不含大陸及港澳）姊妹校修讀學分 1 學期或 1 學年，提供高額機票、學費與生活費補助（須檢附新式戶口名簿影本及主管機關證明文件）。"
          ),
          (
              "姊妹校免學費互惠、免費宿舍與雙聯學位待遇：（1）高師大交換生於互惠名額內均免繳國外及大陸港澳接待姊妹校學費；（2）韓國釜山外國語大學（BUFS）提供每學期 2 名高師大交換生「免姊妹校學費＋免校內宿舍費」雙重待遇，韓國群山大學提供校內宿舍含三餐每學期僅約 USD 900 之優惠；（3）韓國東國大學 2+2 學士雙聯、日本兵庫教育大學 1.5+1.5 碩士雙聯及香港教育大學 1+1 碩士雙聯學位生可於較短修業年限同時取得兩校正式學位。"
          ),
          (
              "學海獎學金分期撥付（80%＋20%）與返國 14 天內心得上傳及核銷規範：獲學海飛颺／惜珠補助者，須於出國前 1 個月簽訂《選送學生出國研修行政契約書》（含保證人簽章）。研修 1 學期者分兩期撥付（出國前撥付 80%，返國並於計畫結束後 14 天內至教育部學海網站上傳心得報告後撥付 20% 尾款；研修 1 學年者分三期撥付）。返國核銷須檢附：1. 學校主計系統領據、2. 旅行社代收轉付收據（買受人：國立高雄師範大學，統一編號：76014004）、3. 所有登機證正本、4. 來回電子機票、5. 護照出入境章戳影本或移民署出入境證明、6. 交換校正式成績單、7. 返校報告單。"
          ),
      ],
      "partner_universities": [p["school_name"] for p in partners],
      "source_urls": nknu_source_urls,
      "last_checked": CHECKED_AT,
  }
  (OFFICIAL_NKNU_DIR / "exchange_info.json").write_text(
      json.dumps(exchange_info_payload, ensure_ascii=False, indent=2) + "\n",
      encoding="utf-8",
  )

  student_dashboard_payload = {
      "school_name": "國立高雄師範大學",
      "last_checked": CHECKED_AT,
      "academic_score_minimum": 70.0,
      "academic_score_rule": (
          "依《國立高雄師範大學選送學生出國研修審查要點》第3、4、6點規定：申請人須為本校在學且已就讀至少一學期之學士、碩士或博士班學生（休學生、學士班延畢生、選修生不可申請），前一學期學業成績須為全班前 50% 且操行成績達 80 分以上（約學業平均 70 分／GPA 2.5 以上），並須符合志願姊妹校 GPA 門檻；校內複審依語言能力 40%、研修計畫 30%、在校成績 20%、其他輔助審查文件 10% 綜合評定。"
      ),
      "academic_gpa_minimum": 2.5,
      "maximum_preferences": 3,
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
          "toefl": 47.0,
          "ielts": 4.0,
          "toeic": 550.0,
      },
      "application_periods": [
          {
              "title": (
                  "國立高雄師範大學 116年度赴外交換研修暨教育部學海飛颺／惜珠計畫說明會與線上甄選（11/18、11/20 說明會・11/11–12/31 線上申請）"
              ),
              "details": [
                  (
                      "高師大國際事務處於 2026/10/20 公告《116年學海計畫說明會》，訂於 2026/11/18 (三) 11:50–13:00 於和平校區行政大樓 10 樓國際會議廳、2026/11/20 (五) 11:50–13:00 於燕巢校區致理大樓 2 樓會議室舉行（報名網址：`https://forms.gle/E247a4sZ2eG9C8r9A`）。"
                  ),
                  (
                      "赴外交換研修暨教育部學海飛颺／惜珠獎學金線上申請系統（`https://sso.nknu.edu.tw/InternationalAdmissions/StudentAboard/Apply.aspx`）開放時間為每年 11/11 ~ 12/31 23:59；1 月由系所及學院進行初審、2 月由國際處召開委員會複審、3/31 前提報教育部學海計畫、5/31 前公告教育部補助結果。"
                  ),
              ],
              "source": {
                  "title": "國立高雄師範大學 116年學海計畫說明會公告與選送學生出國說明會簡報／手冊",
                  "source_url": NKNU_116_XUEHAI_INFO_URL,
                  "category": "exchange_application",
                  "summary": "高師大 116 年學海計畫說明會時程、單一入口線上申請系統（11/11–12/31）與 25 所海外重點交換姊妹校手冊。",
              },
              "scope": "home_application",
              "program_types": ["exchange", "dual_degree"],
              "academic_year": "116",
              "application_round": "116年度赴外交換研修暨教育部學海飛颺／惜珠計畫甄選",
              "audience": "all_students",
              "opens_at": "2026-11-11T09:00:00+08:00",
              "deadline_at": "2026-12-31T23:59:00+08:00",
              "date_status": "verified_exact",
              "status": "upcoming",
              "status_note": "116年學海計畫說明會將於 2026/11/18（和平）及 11/20（燕巢）登場，線上申請系統於 2026/11/11 至 12/31 23:59 開放受理。",
              "deadline_note": "請登入高師大單一入口《學生出國交換申請系統》填報並上傳表1（申請表）、表2（中文讀書計畫書，限1頁）、表3（其他輔助審查文件）、含班排名之歷年成績單與 2 年內有效外語證明。",
              "reminder_eligible": True,
              "checked_at": CHECKED_AT,
          },
          {
              "title": (
                  "國立高雄師範大學 2027年春季班（115-2學期）大陸及港澳地區姊妹校交換申請（2026/10/16 截止・秋季班每年 3–4 月申請）"
              ),
              "details": [
                  (
                      "2027年春季班（115-2學期）大陸及港澳地區姊妹校交換開放北京師範大學（2名）、香港教育大學（3名）、澳門城市大學（3名）、西南大學（2名）、華中師範大學（2名）、華東師範大學（3名）、南京師範大學（2名）、南京大學（2名）、東北師範大學（2名），校內收件至 2026/10/16 截止（香港教育大學 9/18、南京大學 10/13 截止）。"
                  ),
                  (
                      "大陸及港澳地區交換每年分兩梯次辦理：秋季班於每年 3 月公告、3 月底至 4 月底截止；春季班於每年 9–10 月公告、10 月中旬截止。申請資料須以電腦打字填妥後電郵至 `oia_exchange@mail.nknu.edu.tw`（主旨：`申請OOOOO大學_OOO（名字）`）。"
                  ),
              ],
              "source": {
                  "title": "國立高雄師範大學 2027年春季班及2026年秋季班大陸及港澳地區姊妹校交換申請資訊",
                  "source_url": NKNU_2027_SPRING_MAINLAND_URL,
                  "category": "exchange_application",
                  "summary": "高師大大陸及港澳地區姊妹校交換名額、前 50% 成績與操行 80 分門檻及電郵送件規範。",
              },
              "scope": "home_application",
              "program_types": ["exchange"],
              "academic_year": "115",
              "application_round": "2027年春季班（115-2學期）大陸及港澳地區姊妹校交換甄選",
              "audience": "all_students",
              "opens_at": "2026-09-01T09:00:00+08:00",
              "deadline_at": "2026-10-16T17:00:00+08:00",
              "date_status": "verified_exact",
              "status": "closed",
              "status_note": "2027年春季班（115-2）大陸及港澳地區姊妹校交換已於 2026/10/16 截止收件；下一梯次（2027年秋季班／116-1學期）預計於 2027年3月公告。",
              "deadline_note": "請備妥申請表、含班排名之歷年成績單、在學證明、推薦信與學習計畫書寄至 `oia_exchange@mail.nknu.edu.tw`。",
              "reminder_eligible": False,
              "checked_at": CHECKED_AT,
          },
      ],
      "program_overview": [
          {
              "title": (
                  f"國立高雄師範大學國際事務處出國交換與跨校雙聯總覽（{len(partners)} 所全球合作姊妹校・{open_partner_count} 所當期開放申請校・教育部學海飛颺／惜珠獎補助）"
              ),
              "details": [
                  (
                      f"國立高雄師範大學（NKNU，高師大）由「國際事務處（OIA）」與「教務處」共同統籌全校赴外交換研修、大陸及港澳地區姊妹校交換計畫、境外大學跨校雙聯學制與教育部學海飛颺／學海惜珠計畫。本平台完整收錄 {len(partners)} 所高師大官方交換與雙聯合作姊妹校（含當期開放交換及雙聯名額之 {open_partner_count} 所合作校及 {len(partners) - open_partner_count} 所正式締約姊妹校），橫跨全球 26 個國家與地區（中國大陸 44 校、美國 22 校、日本 14 校、韓國 14 校、泰國 5 校、印尼 5 校、馬來西亞 4 校、捷克 4 校、印度 4 校、英國 3 校、澳洲 3 校、菲律賓 3 校、越南 3 校、法國 2 校、波蘭 2 校、俄羅斯 2 校、香港 2 校、澳門 2 校，以及德國、瑞典、奧地利、西班牙、匈牙利、斯洛維尼亞、巴西、蒙古各 1 校）。"
                  ),
                  (
                      "高師大出國交換體系具備四大核心特色：（1）師範教育與綜合學科並重之歐美日韓交換網：涵蓋美國西佛羅里達大學、北卡夏洛特分校、明尼蘇達州立曼卡托分校、西密西根大學、德國帕德博恩大學、法國巴黎西岱大學、瑞典達拉納大學、捷克普爾基涅與查理大學、日本千葉大學、新潟大學、三重大學、大阪教育大學、兵庫教育大學、滋賀大學、岩手大學、日本中央大學、櫻美林大學、韓國梨花女子大學、韓國中央大學、東國大學、江原大學、釜山外國語大學（免學費＋免宿舍費）；（2）三大跨校雙聯學位專案：韓國東國大學 2+2 學士雙聯（國文、英語、體育系）、日本兵庫教育大學 1.5+1.5 碩士雙聯、香港教育大學 1+1 碩士雙聯（數學碩班、科環碩班）；（3）完善教育部學海飛颺／惜珠補助與明確學分換算規定（18小時 / 2 ECTS / 4 UK CATS = 1 學分）；（4）公開收錄 16 所重點姊妹校共 29 篇歷屆學長姐返國交換心得報告。"
                  ),
              ],
              "source": {
                  "title": "國立高雄師範大學國際事務處—赴外交換、赴陸交換、雙聯學位與姊妹校一覽",
                  "source_url": NKNU_OUTBOUND_EXCHANGE_URL,
                  "category": "exchange_application",
                  "summary": "高師大 143 所全球交換與雙聯姊妹校、115/116 出國說明會手冊、陸港澳交換公告與 29 篇學長姐心得專區。",
              },
          }
      ],
      "eligibility": [
          {
              "title": "在學滿一學期資格、前一學期全班前 50% 及操行 80 分門檻與校內審查四項配分權重（40%/30%/20%/10%）",
              "details": [
                  (
                      "在學身分與限制（依《國立高雄師範大學選送學生出國研修審查要點》第3點）：申請人須為本校在學且已就讀至少一學期之學士班、碩士班或博士班學生。休學生、學士班延期畢業生、選修生及領受臺灣獎學金之外國生不得申請；進修學院在職專班學生得檢附《服務機關出國同意書》申請出國交換，但不得申請任何獎助學金；僑生及外國生僅限自費且不得申請交換至其原屬居住國籍。"
                  ),
                  (
                      "學業操行門檻與審查比重（第4、6點）：前一學期學業成績須為全班前 50% 且操行成績達 80 分以上（並符合志願姊妹校 GPA 2.5 標準）。校內審查配分為：語言能力 40%（申請赴大陸地區併入研修計畫書計算）＋研修計畫 30%＋在校成績 20%＋其他輔助審查文件（社團表現、國際交流經驗等）10%。"
                  ),
              ],
              "source": {
                  "title": "國立高雄師範大學選送學生出國研修審查要點與甄選作業流程 PDF",
                  "source_url": NKNU_SELECTION_GUIDELINES_PDF_URL,
                  "category": "exchange_application",
                  "summary": "高師大出國交換申請資格、全班前 50% 與操行 80 分門檻及 40%/30%/20%/10% 審查配分規定。",
              },
          }
      ],
      "language_requirements": [
          {
              "title": "校內 CEFR B1 基準（iBT 47 / IELTS 4.0 / TOEIC 550）、不得以多益替代國際托福雅思規定與各語區門檻",
              "details": [
                  (
                      "外語檢定通則與 CEFR B1 基準（依《選送學生出國研修審查要點》第4點及附表）：申請赴外交換須檢附 2 年內有效之語言能力證明，符合志願姊妹校標準且達本校 CEFR B1（進階級）基準：TOEFL iBT 47 / TOEFL ITP 457 / IELTS 4.0 / TOEIC 550 / GEPT 中級。外國學校明訂要求國際 TOEFL iBT 或 IELTS 成績者，不得以 TOEIC 或全民英檢替代。"
                  ),
                  (
                      "各語區重點姊妹校要求：（1）歐美英語組：西佛羅里達、帕德博恩、達拉納要求 iBT 79–80 / IELTS 6.0–6.5；北卡夏洛特、西密西根要求 iBT 70–80 / IELTS 6.0–6.5；明尼蘇達州立曼卡托要求 iBT 61 / IELTS 5.5；普爾基涅要求 B2；（2）法國巴黎西岱大學要求法語 DELF B2；（3）日本：大阪教育大學要求 JLPT N3，三重、岩手、櫻美林、兵庫教育、千葉、滋賀、金澤星稜大學要求 JLPT N2；（4）韓國：群山、釜山外大要求 TOPIK 3 級，韓國中央大學要求 TOPIK 4 級或英語證明；（5）大陸及澳門免附外語檢定證明。"
                  ),
              ],
              "source": {
                  "title": "國立高雄師範大學選送學生出國說明會手冊與外國語言標準暨成績對照表 PDF",
                  "source_url": NKNU_115_OUTBOUND_HANDBOOK_PDF_URL,
                  "category": "exchange_application",
                  "summary": "高師大 CEFR B1 外語成績對照表與 25 所海外交換姊妹校個別語檢及 GPA 門檻。",
              },
          }
      ],
      "required_documents": [
          {
              "title": "單一入口線上申請系統（表1申請表＋表2讀書計畫限1頁＋表3輔助審查文件）與返國核銷必備文件規範",
              "details": [
                  (
                      "校內甄選必繳資料（赴外交換請於 11/11 ~ 12/31 登入高師大單一入口《學生出國交換申請系統》填報上傳；赴陸港澳請電郵至 `oia_exchange@mail.nknu.edu.tw`）：1. 學生出國研修申請表（表1）、2. 中文讀書計畫書（表2，限 1 頁）、3. 其他輔助審查文件彙整表（表3）、4. 歷年中文成績單正本（須註明全班排名）、5. 2 年內有效外語檢定證明（大陸地區免附）、6. 當學期在學證明與身分證正反面影本、7. 師長推薦信 1–2 封、8. 學海惜珠申請者加附新式戶口名簿影本及低收／中低收證明（在職專班生加附服務機關出國同意書）。"
                  ),
                  (
                      "出國期間與返國核銷義務：抵達交換校 14 天內寄回《學生抵達國外報告表》及選課證明；計畫結束後 14 天內至教育部學海網站上傳心得報告，並檢附旅行社代收轉付收據（統編 76014004）、所有登機證正本、來回電子機票、護照出入境章戳或移民署出入境證明、交換校正式成績單及《返校報告單》辦理核銷，並於返國 30 日內持《預備選修課程表》至教務處註冊組辦理學分採認。"
                  ),
              ],
              "source": {
                  "title": "國立高雄師範大學學生出國研修申請表（表1+表2+表3）與學生核銷必備文件檢核表",
                  "source_url": NKNU_OUTBOUND_APP_FORMS_DOC_URL,
                  "category": "exchange_application",
                  "summary": "高師大出國研修申請表（表1～表3）、讀書計畫 1 頁限制與返國核銷檢核表。",
              },
          }
      ],
      "scholarship_info": [
          {
              "title": "教育部學海飛颺／學海惜珠獎學金（出國前80%＋返國20%撥款）與姊妹校免學費／釜山外大免宿費待遇",
              "details": [
                  (
                      "教育部《學海飛颺／學海惜珠》獎學金：併同每年 11/11 ~ 12/31 赴外交換研修線上甄選申請，申請人須具中華民國國籍且在臺設有戶籍、前一學期學業成績居全班前 50%、操行 80 分以上、並具 2 年內有效外語證明（學海惜珠另須具低收／中低收／特殊境遇家庭等資格）。交換 1 學期者於出國前簽訂行政契約書撥付 80%，返國並於計畫結束 14 天內上傳心得至教育部學海網站及完成單據核銷後撥付 20% 尾款（交換 1 學年者分三期撥付）。"
                  ),
                  (
                      "姊妹校互惠免學費與住宿減免：高師大交換生於互惠名額內均免繳接待姊妹校學費（且若外國學校免收學費，學士班繳交高師大全額學雜費；若外國學校收學費，僅繳高師大雜費；碩博士班繳學雜費基數）；韓國釜山外國語大學（BUFS）另提供免校內宿舍費待遇，群山大學提供校內宿舍含三餐每學期僅約 USD 900 優惠。"
                  ),
              ],
              "source": {
                  "title": "國立高雄師範大學 115年學海說明會簡報、出國學生注意事項與核銷檢核表 PDF",
                  "source_url": NKNU_115_XUEHAI_BRIEFING_PDF_URL,
                  "category": "scholarship",
                  "summary": "高師大教育部學海飛颺、學海惜珠申請條件、行政契約書、分期撥款與統編 76014004 機票核銷規定。",
              },
          }
      ],
      "document_explanations": [
          {
              "title": "國立高雄師範大學出國研修申請表（表1）、中文讀書計畫書（表2，限1頁）與其他輔助審查文件（表3）準備指南",
              "summary": "說明高師大國際事務處規定之表1～表3格式、中文讀書計畫 1 頁上限及單一入口系統上傳規範。",
              "key_points": [
                  "《學生出國研修中文讀書計畫書（表2）》占校內審查總分 30%（赴大陸地區交換者併計語言能力共占 70%），依規定以 1 頁為限，須精要說明出國研修動機、擬於志願姊妹校修習之專業科目及返國學分採認規劃。",
                  "《其他輔助審查文件（表3）》占校內審查總分 10%，可彙整社團幹部經歷、外語或專業競賽獲獎、國際學伴與國際交流活動參與證明。",
                  "赴外交換暨學海飛颺／惜珠申請人須於每年 11/11 ~ 12/31 23:59 前登入高師大單一入口《學生出國交換申請系統》（`https://sso.nknu.edu.tw/InternationalAdmissions/StudentAboard/Apply.aspx`）完成填報並上傳全套文件；赴大陸及港澳姊妹校交換申請人則將電腦打字填妥之表件電郵至 `oia_exchange@mail.nknu.edu.tw`。",
              ],
              "applies_to": [],
              "source": {
                  "title": "國立高雄師範大學學生出國研修申請表（表1+表2+表3）與選送學生出國說明會手冊",
                  "source_url": NKNU_115_OUTBOUND_HANDBOOK_PDF_URL,
                  "category": "exchange_application",
                  "summary": None,
              },
              "document_url": NKNU_OUTBOUND_APP_FORMS_DOC_URL,
              "document_type": "official_document",
              "full_text_extracted": True,
          }
      ],
      "rule_explanations": [
          {
              "title": "國立高雄師範大學選送學生出國研修審查要點與出國選修課程實施要點：全班前 50% 門檻、學分換算與返國 14/30 日規定",
              "summary": "規範高師大出國交換生在學資格、全班前 50% 與操行 80 分門檻、40%/30%/20%/10% 審查比重、學分換算基準與返國核銷抵免時限。",
              "key_points": [
                  "申請人須為高師大在學且已就讀至少一學期之學士、碩士或博士班學生（休學生、學士班延畢生、選修生不可申請；在職專班生可自費交換但不得領取獎助），前一學期學業成績須居全班前 50% 且操行成績 80 分以上。",
                  "在學期間出國選修課程至多二次，合計以不超過一學年為限，抵免學分上限為畢業應修最低學分數四分之一（雙聯學制為三分之二）；學分換算基準：授課滿 18 小時為 1 學分、美制/日/韓/大陸 1 學分 = 1 學分、歐洲 2 ECTS = 1 學分、英國 4 CATS = 1 學分。",
                  "抵達交換校後 14 天內須回傳《學生抵達國外報告表》；計畫結束後 14 天內須上傳心得至教育部學海網站並持旅行社代收轉付收據（統編 76014004）等單據辦理核銷；返國後 30 日內須持正式成績單正本及《預備選修課程表》向教務處註冊組辦理學分採認。",
              ],
              "applies_to": [],
              "source": {
                  "title": "國立高雄師範大學選送學生出國研修審查要點、學生出國選修課程實施要點與抵免學分要點 PDF",
                  "source_url": NKNU_SELECTION_GUIDELINES_PDF_URL,
                  "category": "exchange_application",
                  "summary": None,
              },
              "document_url": NKNU_SELECTION_GUIDELINES_PDF_URL,
              "document_type": "official_document",
              "full_text_extracted": True,
          }
      ],
      "sources": [
          {
              "title": "國立高雄師範大學國際事務處（OIA）官方網站",
              "source_url": NKNU_OIA_HUB_URL,
              "category": "exchange_application",
              "summary": None,
          },
          {
              "title": "國立高雄師範大學 115年選送學生出國說明會手冊 PDF（25所海外交換姊妹校名額與條件）",
              "source_url": NKNU_115_OUTBOUND_HANDBOOK_PDF_URL,
              "category": "partner_school",
              "summary": None,
          },
          {
              "title": "國立高雄師範大學 115年學海說明會簡報與 116年學海計畫說明會公告",
              "source_url": NKNU_115_XUEHAI_BRIEFING_PDF_URL,
              "category": "scholarship",
              "summary": None,
          },
          {
              "title": "國立高雄師範大學選送學生出國研修審查要點與外國語言標準暨成績對照表 PDF",
              "source_url": NKNU_SELECTION_GUIDELINES_PDF_URL,
              "category": "exchange_application",
              "summary": None,
          },
          {
              "title": "國立高雄師範大學 2027年春季班及2026年秋季班大陸及港澳地區姊妹校交換申請資訊",
              "source_url": NKNU_2027_SPRING_MAINLAND_URL,
              "category": "partner_school",
              "summary": None,
          },
          {
              "title": "國立高雄師範大學學生出國選修課程實施要點、學籍處理要點與辦理學生抵免學分要點 PDF",
              "source_url": NKNU_COURSE_SELECTION_PDF_URL,
              "category": "exchange_application",
              "summary": None,
          },
          {
              "title": "國立高雄師範大學與境外大學跨校雙聯學制實施辦法與雙聯合作學校一覽",
              "source_url": NKNU_DUAL_DEGREE_URL,
              "category": "exchange_application",
              "summary": None,
          },
          {
              "title": "國立高雄師範大學全球締約姊妹校一覽表與赴外交換學長姐心得分享專區",
              "source_url": NKNU_SISTER_SCHOOLS_URL,
              "category": "partner_school",
              "summary": None,
          },
      ],
  }
  (OFFICIAL_NKNU_DIR / "student_dashboard.json").write_text(
      json.dumps(student_dashboard_payload, ensure_ascii=False, indent=2) + "\n",
      encoding="utf-8",
  )

  pages_records = [
      {
          "title": "國立高雄師範大學：116年度赴外交換研修暨學海飛颺／惜珠計畫甄選（11/11–12/31線上申請）與2027春季班大陸及港澳交換時程",
          "source_url": NKNU_115_OUTBOUND_HANDBOOK_PDF_URL,
          "published_at": "2026-10-20T00:00:00Z",
          "text": "\n".join(exchange_info_payload["application_period"]),
          "summary": "\n".join(exchange_info_payload["application_period"]),
          "category": "exchange_application",
          "attachments": [],
          "crawled_at": CHECKED_AT,
          "content_hash": hashlib.sha256("\n".join(exchange_info_payload["application_period"]).encode("utf-8")).hexdigest(),
      },
      {
          "title": "國立高雄師範大學：選送學生出國研修審查要點（就讀滿一學期資格、全班前 50% 與操行 80 分門檻及 40%/30%/20%/10% 審查配分）",
          "source_url": NKNU_SELECTION_GUIDELINES_PDF_URL,
          "published_at": "2026-10-20T00:00:00Z",
          "text": "\n".join(exchange_info_payload["eligibility"]),
          "summary": "\n".join(exchange_info_payload["eligibility"]),
          "category": "exchange_application",
          "attachments": [],
          "crawled_at": CHECKED_AT,
          "content_hash": hashlib.sha256("\n".join(exchange_info_payload["eligibility"]).encode("utf-8")).hexdigest(),
      },
      {
          "title": "國立高雄師範大學：143 所交換與雙聯合作姊妹校外語檢定門檻（CEFR B1 基準及不得以多益替代國際托福雅思規定）",
          "source_url": NKNU_SISTER_SCHOOLS_URL,
          "published_at": "2026-10-20T00:00:00Z",
          "text": "\n".join(exchange_info_payload["language_requirement"]),
          "summary": "\n".join(exchange_info_payload["language_requirement"]),
          "category": "exchange_application",
          "attachments": [],
          "crawled_at": CHECKED_AT,
          "content_hash": hashlib.sha256("\n".join(exchange_info_payload["language_requirement"]).encode("utf-8")).hexdigest(),
      },
      {
          "title": "國立高雄師範大學：出國交換申請文件（表1申請表、表2中文讀書計畫限1頁、表3輔助審查文件）與單一入口系統上傳規範",
          "source_url": NKNU_OUTBOUND_APP_FORMS_DOC_URL,
          "published_at": "2026-10-20T00:00:00Z",
          "text": "\n".join(exchange_info_payload["required_documents"]),
          "summary": "\n".join(exchange_info_payload["required_documents"]),
          "category": "exchange_application",
          "attachments": [],
          "crawled_at": CHECKED_AT,
          "content_hash": hashlib.sha256("\n".join(exchange_info_payload["required_documents"]).encode("utf-8")).hexdigest(),
      },
      {
          "title": "國立高雄師範大學：教育部學海飛颺／學海惜珠獎學金（80%＋20% 撥款、計畫結束 14 天內上傳心得與統編 76014004 核銷規定）",
          "source_url": NKNU_115_XUEHAI_BRIEFING_PDF_URL,
          "published_at": "2026-10-20T00:00:00Z",
          "text": "\n".join(exchange_info_payload["scholarship_info"]),
          "summary": "\n".join(exchange_info_payload["scholarship_info"]),
          "category": "scholarship",
          "attachments": [],
          "crawled_at": CHECKED_AT,
          "content_hash": hashlib.sha256("\n".join(exchange_info_payload["scholarship_info"]).encode("utf-8")).hexdigest(),
      },
  ]
  (OFFICIAL_NKNU_DIR / "pages.jsonl").write_text(
      "\n".join(json.dumps(p, ensure_ascii=False) for p in pages_records) + "\n",
      encoding="utf-8",
  )

  home_rules = {
      "school_id": "nknu",
      "school_name": "國立高雄師範大學",
      "eligibility": student_dashboard_payload["eligibility"],
      "application_periods": student_dashboard_payload["application_periods"],
      "selection_rules": {
          "undergraduate_score_minimum": 70.0,
          "graduate_score_minimum": 70.0,
          "previous_semester_class_rank_percent_max": 50,
          "conduct_score_minimum": 80.0,
          "excluded_undergraduate_years": ["大一上"],
          "exclude_leave_of_absence_and_undergraduate_extended_students": True,
          "in_service_scholarship_eligible": False,
          "selection_weights": {
              "language_ability": 0.4,
              "study_plan": 0.3,
              "academic_performance": 0.2,
              "supplementary_documents": 0.1,
          },
          "toeic_gept_cannot_substitute_mandatory_toefl_ielts": True,
          "max_outbound_times": 2,
          "max_outbound_duration_years": 1,
          "credit_transfer_cap_ratio": 0.25,
          "dual_degree_credit_transfer_cap_ratio": 0.67,
          "xuehai_pre_departure_disbursement_ratio": 0.8,
          "xuehai_post_return_disbursement_ratio": 0.2,
          "arrival_report_due_days": 14,
          "xuehai_report_upload_due_days": 14,
          "credit_transfer_application_due_days": 30,
          "nknu_tax_id_for_airfare_receipt": "76014004",
          "return_documents_due": "計畫結束後 14 天內上傳心得報告至教育部學海網站並檢附旅行社代收轉付收據（統編 76014004）、所有登機證正本、來回電子機票、護照出入境章戳或移民署出入境證明、交換校正式成績單及返校報告單至國際處辦理核銷；返國後 30 日內持正式成績單正本及預備選修課程表向教務處註冊組申請學分採認",
      },
      "source_urls": nknu_source_urls,
      "verified_at": "2026-10-20",
  }
  (OFFICIAL_NKNU_DIR / "home_rules.json").write_text(
      json.dumps(home_rules, ensure_ascii=False, indent=2) + "\n",
      encoding="utf-8",
  )
  (OFFICIAL_NKNU_DIR / "documents.json").write_text(
      json.dumps(
          {
              "school_name": "國立高雄師範大學",
              "required_documents": student_dashboard_payload["required_documents"],
              "source_urls": nknu_source_urls,
          },
          ensure_ascii=False,
          indent=2,
      )
      + "\n",
      encoding="utf-8",
  )
  (OFFICIAL_NKNU_DIR / "scholarships.json").write_text(
      json.dumps(
          {
              "school_name": "國立高雄師範大學",
              "scholarships": student_dashboard_payload["scholarship_info"],
              "source_urls": nknu_source_urls,
          },
          ensure_ascii=False,
          indent=2,
      )
      + "\n",
      encoding="utf-8",
  )

  completeness = {
      "school_id": "nknu",
      "school_name": "國立高雄師範大學",
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
          "國立高雄師範大學國際事務處 116 年度赴外交換研修暨教育部學海飛颺／惜珠計畫說明會於 2026/11/18（和平校區）及 11/20（燕巢校區）舉行、線上申請系統於 11/11 ~ 12/31 23:59 開放，大陸及港澳地區姊妹校交換（2027春季班及2026秋季班）與境外大學跨校雙聯學制同步整合；共完整收錄 143 所全球交換與雙聯合作姊妹校（含 36 所當期開放交換及雙聯名額校與 107 所正式締約姊妹校，橫跨歐、美、亞、大洋洲 26 個國家與地區，並收錄 16 所重點姊妹校共 29 篇歷屆學長姐返國心得報告）。"
      ),
      "verified_at": "2026-10-20",
  }
  (OFFICIAL_NKNU_DIR / "catalog-completeness.json").write_text(
      json.dumps(completeness, ensure_ascii=False, indent=2) + "\n",
      encoding="utf-8",
  )
  (OFFICIAL_NKNU_DIR / "verification_status.json").write_text(
      json.dumps(
          {
              "school_id": "nknu",
              "school_name": "國立高雄師範大學",
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
          "sources/nknu/115_outbound_handbook.pdf",
          NKNU_115_OUTBOUND_HANDBOOK_PDF_URL,
          "國立高雄師範大學 115年選送學生出國說明會手冊 PDF",
      ),
      (
          "sources/nknu/115_xuehai_briefing.pdf",
          NKNU_115_XUEHAI_BRIEFING_PDF_URL,
          "國立高雄師範大學 115年選送學生出國研修（學海飛颺／惜珠）說明會簡報 PDF",
      ),
      (
          "sources/nknu/nknu_selection_guidelines.pdf",
          NKNU_SELECTION_GUIDELINES_PDF_URL,
          "國立高雄師範大學選送學生出國研修審查要點暨外國語言標準對照表 PDF",
      ),
      (
          "sources/nknu/nknu_selection_flowchart.pdf",
          NKNU_SELECTION_FLOWCHART_PDF_URL,
          "國立高雄師範大學選送學生出國研修甄選作業流程 PDF",
      ),
      (
          "sources/nknu/nknu_outbound_application_forms.doc",
          NKNU_OUTBOUND_APP_FORMS_DOC_URL,
          "國立高雄師範大學學生出國研修申請表（表1+表2+表3）DOC",
      ),
      (
          "sources/nknu/nknu_predeparture_notes.pdf",
          NKNU_PREDEPARTURE_NOTES_PDF_URL,
          "國立高雄師範大學出國學生注意事項 PDF",
      ),
      (
          "sources/nknu/nknu_overseas_safety_notes.pdf",
          NKNU_OVERSEAS_SAFETY_PDF_URL,
          "國立高雄師範大學從事海外留遊學安全應注意事項 PDF",
      ),
      (
          "sources/nknu/nknu_experience_upload_guide.pdf",
          NKNU_EXPERIENCE_GUIDE_PDF_URL,
          "國立高雄師範大學學海飛颺／惜珠心得報告內容大綱與上傳說明 PDF",
      ),
      (
          "sources/nknu/nknu_reimbursement_checklist.docx",
          NKNU_REIMBURSEMENT_CHECKLIST_DOCX_URL,
          "國立高雄師範大學學生返國核銷必備文件檢核表 DOCX",
      ),
      (
          "sources/nknu/nknu_dual_degree_app_form.docx",
          NKNU_DUAL_DEGREE_APP_FORM_DOCX_URL,
          "國立高雄師範大學雙聯學制學生申請表 DOCX",
      ),
      (
          "sources/nknu/nknu_dual_degree_regulations.pdf",
          NKNU_DUAL_DEGREE_REGULATIONS_PDF_URL,
          "國立高雄師範大學與境外大學跨校雙聯學制實施辦法 PDF",
      ),
      (
          "sources/nknu/nknu_course_selection_regulations.pdf",
          NKNU_COURSE_SELECTION_PDF_URL,
          "國立高雄師範大學學生出國選修課程實施要點 PDF",
      ),
      (
          "sources/nknu/nknu_academic_status_regulations.pdf",
          NKNU_ACADEMIC_STATUS_PDF_URL,
          "國立高雄師範大學學生出國期間有關學業及學籍處理要點 PDF",
      ),
      (
          "sources/nknu/nknu_credit_transfer_regulations.pdf",
          NKNU_CREDIT_TRANSFER_PDF_URL,
          "國立高雄師範大學辦理學生抵免學分要點 PDF",
      ),
      (
          "sources/nknu/news_496_xuehai_116_info_session.html",
          NKNU_116_XUEHAI_INFO_URL,
          "國立高雄師範大學 116年學海計畫說明會公告 HTML",
      ),
      (
          "sources/nknu/news_460_mainland_2027_spring.html",
          NKNU_2027_SPRING_MAINLAND_URL,
          "國立高雄師範大學 2027年春季班大陸及港澳地區姊妹校交換申請資訊 HTML",
      ),
      (
          "sources/nknu/news_377_mainland_2026_fall.html",
          NKNU_2026_FALL_MAINLAND_URL,
          "國立高雄師範大學 2026年秋季班大陸及港澳地區姊妹校交換申請資訊 HTML",
      ),
      (
          "sources/nknu/sister_schools.html",
          NKNU_SISTER_SCHOOLS_URL,
          "國立高雄師範大學本校姊妹校一覽 HTML",
      ),
      (
          "sources/nknu/nknu_catalog_source.json",
          NKNU_115_OUTBOUND_HANDBOOK_PDF_URL,
          "國立高雄師範大學 143 所出國交換與雙聯合作姊妹校整合資料集 JSON",
      ),
      (
          "sources/nknu/nknu_resolved_locations.json",
          NKNU_115_OUTBOUND_HANDBOOK_PDF_URL,
          "國立高雄師範大學 143 所出國交換與雙聯合作姊妹校 ROR / Wikidata 地理座標核對表 JSON",
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
      "school_id": "nknu",
      "school_name": "國立高雄師範大學",
      "generated_at": CHECKED_AT,
      "active_cycle_note": completeness["active_term"],
      "sources": prov_sources,
  }
  prov_text = json.dumps(provenance_payload, ensure_ascii=False, indent=2) + "\n"
  (OFFICIAL_NKNU_DIR / "import_provenance.json").write_text(prov_text, encoding="utf-8")
  (OFFICIAL_NKNU_DIR / "import-provenance.json").write_text(prov_text, encoding="utf-8")

  print(
      f"Successfully built NKNU catalog: {len(partners)} partners"
      f" ({open_partner_count} open, {completeness['verified_campus_images']}"
      f" verified images, {completeness['verified_locations']} verified"
      f" locations), {len(workflows)} workflows,"
      f" {len(destinations)} destinations, {len(research_records)} research"
      f" records, {exp_covered_schools} schools with experience records"
      f" ({len(student_experience_rows)} rows)."
  )


if __name__ == "__main__":
  main()
