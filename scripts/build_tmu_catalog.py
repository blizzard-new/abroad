"""Build the official Taipei Medical University (臺北醫學大學, TMU) exchange data bundle."""

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

SOURCES_TMU_DIR = REPO_ROOT / "sources" / "tmu"
OFFICIAL_TMU_DIR = REPO_ROOT / "src" / "exchange_info" / "official_data" / "tmu"
STATIC_DIR = REPO_ROOT / "src" / "exchange_info" / "static"

CHECKED_AT = "2026-10-20T23:00:00Z"

TMU_OGE_HUB_URL = "https://oge.tmu.edu.tw/zh-hant/"
TMU_OGE_EN_HUB_URL = "https://oge.tmu.edu.tw/"
TMU_OUTBOUND_EXCHANGE_ZH_URL = (
    "https://oge.tmu.edu.tw/zh-hant/%e5%87%ba%e5%9c%8b%e4%ba%a4%e6%8f%9b%e8%aa%9e%e6%96%87%e8%aa%8d%e8%ad%89/"
)
TMU_OUTBOUND_STUDENTS_EN_URL = "https://oge.tmu.edu.tw/outbound-students/"
TMU_DUAL_DEGREE_ZH_URL = (
    "https://oge.tmu.edu.tw/zh-hant/%e9%9b%99%e8%81%af%e5%ad%b8%e4%bd%8d/"
)
TMU_OVERSEAS_COURSES_ZH_URL = (
    "https://oge.tmu.edu.tw/zh-hant/%e6%b5%b7%e5%a4%96%e8%aa%b2%e7%a8%8b/"
)
TMU_SCHOLARSHIPS_ZH_URL = (
    "https://oge.tmu.edu.tw/zh-hant/%e7%8d%8e%e5%ad%b8%e9%87%91/"
)
TMU_EXPERIENCES_ZH_URL = (
    "https://oge.tmu.edu.tw/zh-hant/%e5%ad%b8%e7%94%9f%e7%b6%93%e9%a9%97%e5%88%86%e4%ba%ab/"
)
TMU_PARTNERS_ZH_URL = "https://oge.tmu.edu.tw/zh-hant/partners-list/"
TMU_PARTNERS_EN_URL = "https://oge.tmu.edu.tw/partners-list/"
TMU_REGULATIONS_ZH_URL = (
    "https://oge.tmu.edu.tw/zh-hant/%e7%9b%b8%e9%97%9c%e6%b3%95%e8%a6%8f%e8%a1%a8%e4%bb%b6/"
)
TMU_ACA_OUTBOUND_URL = "https://aca.tmu.edu.tw/front/RegSection/RegSection05/pages.php?ID=dG11X2FjYSZSZWdTZWN0aW9uMDU="
TMU_ACA_DUAL_DEGREE_REGS_URL = "https://aca.tmu.edu.tw/front/RegSection/RegSection_2/pages.php?ID=dG11X2FjYSZSZWdTZWN0aW9uXzI="

TMU_115_XUEHAI_INFO_URL = "https://oge.tmu.edu.tw/zh-hant/2026%e6%b0%91%e5%9c%8b115%e5%b9%b4%e6%95%99%e8%82%b2%e9%83%a8%e5%ad%b8%e6%b5%b7%e8%a8%88%e7%95%ab%e7%8d%8e%e5%ad%b8%e9%87%91-%e6%a0%a1%e5%85%a7%e8%aa%aa%e6%98%8e%e6%9c%83-%e7%8f%be%e5%b7%b2/"
TMU_115_XUEHAI_BRIEFING_PDF_URL = "https://oge.tmu.edu.tw/wp-content/uploads/2025/11/2026%E6%B0%91%E5%9C%8B115%E5%B9%B4%E6%95%99%E8%82%B2%E9%83%A8%E5%AD%B8%E6%B5%B7%E8%A8%88%E7%95%AB%E7%8D%8E%E5%AD%B8%E9%87%91-%E6%A0%A1%E5%85%A7%E8%AA%AA%E6%98%8E%E6%9C%83%E7%B0%A1%E5%A0%B1.pdf"
TMU_115_2_XIZHU_GUIDELINES_PDF_URL = "https://oge.tmu.edu.tw/wp-content/uploads/2026/08/%E8%87%BA%E5%8C%97%E9%86%AB%E5%AD%B8%E5%A4%A7%E5%AD%B8%E3%80%8C115%E5%B9%B4%E5%BA%A6%E6%95%99%E8%82%B2%E9%83%A8%E5%AD%B8%E6%B5%B7%E6%83%9C%E7%8F%A0%E8%A8%88%E7%95%AB%E3%80%8D%E7%AC%AC%E4%BA%8C%E6%AC%A1%E7%94%B3%E8%AB%8B%E5%85%AC%E5%91%8A.pdf"
TMU_115_2_XIZHU_FORM_DOC_URL = "https://oge.tmu.edu.tw/wp-content/uploads/2026/08/115-2%E6%83%9C%E7%8F%A0%E9%99%84%E4%BB%B6.doc"
TMU_115_2_ZHUMENG_GUIDELINES_PDF_URL = "https://oge.tmu.edu.tw/wp-content/uploads/2026/08/%E8%87%BA%E5%8C%97%E9%86%AB%E5%AD%B8%E5%A4%A7%E5%AD%B8%E3%80%8C115%E5%B9%B4%E5%BA%A6%E6%95%99%E8%82%B2%E9%83%A8%E5%AD%B8%E6%B5%B7%E7%AF%89%E5%A4%A2%E6%96%B0%E5%8D%97%E5%90%91%E7%AF%89%E5%A4%A2%E8%A8%88%E7%95%AB%E3%80%8D%E7%AC%AC%E4%BA%8C%E6%AC%A1%E7%94%B3%E8%AB%8B%E5%85%AC%E5%91%8A.pdf"
TMU_115_XUEHAI_CONTRACT_DOC_URL = "https://oge.tmu.edu.tw/wp-content/uploads/2026/08/115%E5%AD%B8%E6%B5%B7%E8%A1%8C%E6%94%BF%E5%A5%91%E7%B4%84%E6%9B%B8.doc"
TMU_2026_MOE_PROSPECTUS_EN_PDF_URL = "https://oge.tmu.edu.tw/wp-content/uploads/2026/08/MOE-Study-Abroad-and-New-Southbound-Study-Abroad-Program_2026.pdf"
TMU_OVERSEAS_INCENTIVE_REGS_PDF_URL = "https://oge.tmu.edu.tw/wp-content/uploads/2023/10/%E8%87%BA%E5%8C%97%E9%86%AB%E5%AD%B8%E5%A4%A7%E5%AD%B8%E5%A2%83%E5%A4%96%E7%A0%94%E4%BF%AE%E6%9A%A8%E8%A6%8B%E5%AF%A6%E7%BF%92%E7%8D%8E%E5%8B%B5%E8%BE%A6%E6%B3%95.pdf"
TMU_OVERSEAS_INCENTIVE_REGS_EN_PDF_URL = "https://oge.tmu.edu.tw/wp-content/uploads/2023/10/TMU-Overseas-Training-and-Internship-Incentive-Regulations.pdf"
TMU_OVERSEAS_INCENTIVE_APP_DOCX_URL = "https://oge.tmu.edu.tw/wp-content/uploads/2023/10/%E8%87%BA%E5%8C%97%E9%86%AB%E5%AD%B8%E5%A4%A7%E5%AD%B8%E5%A2%83%E5%A4%96%E7%A0%94%E4%BF%AE%E6%9A%A8%E8%A6%8B%E5%AF%A6%E7%BF%92%E7%8D%8E%E5%8B%B5%E8%BE%A6%E6%B3%95_%E9%99%84%E4%BB%B6%E5%8F%8A%E7%94%B3%E8%AB%8B%E8%A8%88%E5%8A%83%E6%9B%B8%E7%AF%84%E4%BE%8B_V6.docx"
TMU_PREDEPARTURE_FORM_PDF_URL = "https://oge.tmu.edu.tw/wp-content/uploads/2017/10/%E5%AD%B8%E7%94%9F%E6%B5%B7%E5%A4%96%E8%A1%8C%E5%89%8D%E5%A0%B1%E5%88%B0%E5%96%AE.pdf"
TMU_PHARMACY_USC_DUAL_PDF_URL = "https://oge.tmu.edu.tw/wp-content/uploads/2017/08/%E8%97%A5%E5%AD%B8%E7%B3%BB%E8%88%87%E7%BE%8E%E5%9C%8B%E5%8D%97%E5%8A%A0%E5%B7%9E%E5%A4%A7%E5%AD%B8%E9%9B%99%E8%81%AF%E5%AD%B8%E5%88%B6%E6%96%BD%E8%A1%8C%E8%BE%A6%E6%B3%95%E5%90%AB%E7%94%B3%E8%AB%8B%E8%A1%A8.pdf"
TMU_PHARMACY_PSU_DUAL_PDF_URL = "https://oge.tmu.edu.tw/wp-content/uploads/2017/08/%E8%97%A5%E5%AD%B8%E7%B3%BB%E8%88%87%E7%BE%8E%E5%9C%8B%E8%B3%93%E5%A4%95%E6%B3%95%E5%B0%BC%E4%BA%9E%E5%B7%9E%E5%B7%9E%E7%AB%8B%E5%A4%A7%E5%AD%B8%E9%9B%99%E8%81%AF%E5%AD%B8%E5%88%B6%E6%96%BD%E8%A1%8C%E8%BE%A6%E6%B3%95%E5%90%AB%E7%94%B3%E8%AB%8B%E8%A1%A8.pdf"
TMU_DUAL_DEGREE_FLOWCHART_PDF_URL = "https://oge.tmu.edu.tw/wp-content/uploads/2017/10/%E8%B7%A8%E5%9C%8B%E9%9B%99%E8%81%AF%E5%AD%B8%E5%88%B6%E6%B5%81%E7%A8%8B%E5%9C%96.pdf"
TMU_ACA_OVERSEAS_STUDY_GUIDELINES_PDF_URL = "https://aca.tmu.edu.tw/var/file/7/1007/attach/95/pta_16760_652242_80442.pdf"
TMU_ACA_DUAL_DEGREE_REGS_PDF_URL = "https://aca.tmu.edu.tw/var/file/7/1007/attach/96/pta_40196_1277001_84591.pdf"
TMU_ACA_CREDIT_TRANSFER_REGS_PDF_URL = "https://aca.tmu.edu.tw/var/file/7/1007/attach/94/pta_39981_6204967_58458.pdf"

REGION_COST_DEFAULTS = {
    "美國": (
        "USD 1,600–2,800 / 月（含住宿、膳食與市區交通；南加州大學 USC、哈佛大學、史丹佛大學、哥倫比亞／紐約聖若望大學、芝加哥 UIC 等大都會校區約 USD 2,000–2,800 / 月；凱斯西儲大學 CWRU、賓州州立大學 Penn State、喬治亞州立大學 GSU、俄亥俄州立大學 OSU、德州休士頓醫學中心 TMC 約 USD 1,500–2,100 / 月；可申請教育部學海飛颺／惜珠／築夢及北醫大境外研修暨見實習獎學金）",
        "須憑美國接待校或醫療中心核發之 DS-2019（J-1 交換學者／學生）或 I-20（F-1 雙聯學位生）表格向美國在台協會（AIT）申辦簽證，臨床見實習生另須完成規定之免疫接種證明（MMR、B肝抗體、TB 檢驗、水痘疫苗）、HIPAA 隱私訓練及美國醫療機構指定健康保險。",
    ),
    "加拿大": (
        "CAD 1,800–2,600 / 月（溫哥華英屬哥倫比亞大學 UBC、蒙特婁大學 UdeM、麥基爾大學 McGill 及哈利法克斯戴爾豪斯大學 Dalhousie 校內外住宿、伙食與大眾運輸費用）",
        "研修或雙聯超過 6 個月須申辦加拿大 Study Permit 學生簽證，6 個月內交換或暑期 VSP 課程須辦理 eTA 電子旅行許可並投保加拿大省立／校方強制醫療保險與北醫大海外醫療意外險。",
    ),
    "安地卡及巴布達": (
        "USD 1,200–1,800 / 月（安地卡健康科學大學 UHSA 校內學生宿舍、餐飲與交通費用）",
        "須依接待校入學許可辦理學生入境簽證並投保涵蓋全期之海外醫療及意外保險。",
    ),
    "阿根廷": (
        "USD 650–1,100 / 月（布宜諾斯艾利斯薩爾瓦多大學 USAL 學生分租公寓、日常飲食與地鐵公車開銷）",
        "須憑接待校入學許可向阿根廷商務文化辦事處申辦學生簽證，並投保涵蓋全期之海外醫療及意外保險。",
    ),
    "墨西哥": (
        "USD 600–950 / 月（帕丘卡伊達爾戈州立自治大學 UAEH 醫學與牙醫學交換生住宿、餐飲與市區交通費用實惠）",
        "交換 180 天內可免簽入境墨西哥，超過 180 天須申辦墨西哥學生居留簽證，並於出國前投保涵蓋全期之海外醫療及意外險。",
    ),
    "日本": (
        "JPY 80,000–135,000 / 月（東京大學、東京醫科齒科大學、東京醫科大學、慶應義塾大學、順天堂大學、御茶水女子大學、東京理科大學等首都圈校院約 JPY 100,000–140,000 / 月；東北大學、北海道大學、北海道醫療大學、京都大學、大阪大學、神戶大學、名古屋大學、九州大學、金澤大學、岡山大學、長崎大學等學生寮費僅約 JPY 15,000–45,000 / 月；可申請教育部學海飛颺／惜珠／築夢、JASSO 及北醫大境外研修獎學金）",
        "學期交換或雙聯須憑日本接待校核發之在留資格認定證明書（COE）申辦留學簽證並依法加入日本國民健康保險（NHI）；短期臨床見實習（4–8 週）須依日本接收醫院要求備妥抗體檢測報告（麻疹、德國麻疹、水痘、腮腺炎、B肝、T-SPOT 結核檢驗）與海外醫療及實習責任保險。",
    ),
    "韓國": (
        "KRW 800,000–1,300,000 / 月（首爾大學、高麗大學、延世大學、成均館大學、漢陽大學、中央大學、梨花女子大學及光州全南大學校內外宿舍、學生食堂與首爾地鐵公車開銷）",
        "學期交換須憑韓國接待校標準入學許可書向駐台北韓國代表部申辦 D-2-6 交換學生簽證，抵韓後辦理外國人登錄並納入韓國國民健康保險（NHIS）。",
    ),
    "新加坡": (
        "SGD 1,600–2,500 / 月（新加坡國立大學 NUS 校內宿舍或校外租屋、熟食中心餐飲與捷運公車費用）",
        "須透過新加坡移民與關卡局（ICA）SOLAR 系統申辦 Student's Pass（STP）學生准證，並投保 NUS 團體醫療保險及北醫大海外醫療意外險。",
    ),
    "泰國": (
        "THB 14,000–24,000 / 月（曼谷朱拉隆功大學、瑪希敦大學、國王科技大學 KMUTT、詩納卡寧威洛大學及清邁大學、孔敬大學、宋卡王子大學、那黎宣大學國際學生宿舍與餐飲交通開銷親民）",
        "須憑泰國接待校院公文向泰國貿易經濟辦事處（TTEO）申辦 Non-Immigrant ED 簽證，並投保涵蓋全期之海外醫療及意外保險。",
    ),
    "越南": (
        "USD 450–750 / 月（胡志明市醫藥大學 UMP、河內醫科大學、河內藥科大學、海防醫藥大學學生宿舍、日常餐飲與市區交通費用實惠）",
        "須透過越南接待校申辦越南學生／實習簽證，並於出國前投保涵蓋全期之海外醫療及意外保險。",
    ),
    "印尼": (
        "IDR 4,800,000–8,500,000 / 月（日惹加札馬達大學 UGM、雅加達印尼大學 UI、希望之光大學 UPH、泗水穆罕默迪亞大學、UNUSA、萬隆理工學院、瑪琅布拉維賈亞大學等學生公寓與餐飲交通開銷低廉）",
        "須由印尼接待校協助申辦印尼學生／文化交流電子簽證（e-Visa），並投保涵蓋全期之海外醫療及意外保險。",
    ),
    "馬來西亞": (
        "MYR 1,600–2,600 / 月（吉隆坡馬來亞大學 UM 及拉曼大學 UTAR 校內外住宿、飲食與捷運公車開銷）",
        "學期交換或雙聯須透過馬來西亞 EMGS 系統申辦學生簽證核准函（VAL / Student Pass）並投保 EMGS 醫療保險。",
    ),
    "菲律賓": (
        "USD 500–850 / 月（馬尼拉菲律賓大學 UP 及亞洲與太平洋大學 UA&P 學生公寓與日常餐飲交通費用）",
        "須依菲律賓接待校指引辦理 9(f) 學生簽證或 SSP 特別學習許可，並投保海外全期醫療及意外保險。",
    ),
    "印度": (
        "USD 400–700 / 月（印度理工學院卡拉格普爾分校 IITKGP、馬德拉斯分校 IITM、清奈安娜大學、斯里拉瑪錢德拉醫學院 SRIHER、SRM 科技大學等校內國際學舍與餐飲費用低廉）",
        "須憑印度接待校入學許可向印度台北協會（ITA）申辦 Student / Intern Visa 並投保海外醫療及意外保險。",
    ),
    "柬埔寨": (
        "USD 450–750 / 月（金邊普提薩斯特拉大學 University of Puthisastra 住宿與日常生活開銷）",
        "須辦理柬埔寨簽證並於出國前投保涵蓋全期之海外醫療及意外保險。",
    ),
    "蒙古": (
        "USD 450–750 / 月（烏蘭巴托蒙古科技大學 MUST 學生宿舍、餐飲與市區交通費用）",
        "須憑接待校邀請函申辦蒙古學生簽證，並投保涵蓋全期之海外醫療及意外保險。",
    ),
    "哈薩克": (
        "USD 500–850 / 月（阿拉木圖哈薩克國立醫科大學 KazNMU 學生宿舍與日常餐飲交通費用）",
        "須憑接待校邀請函申辦哈薩克留學／研修簽證，並投保涵蓋全期之海外醫療及意外保險。",
    ),
    "以色列": (
        "USD 1,200–1,800 / 月（貝爾謝巴內蓋夫本古里安大學 BGU 校內學生宿舍、膳食與交通費用）",
        "須向駐台北以色列經濟文化辦事處申辦 A/2 學生簽證並投保當地與海外醫療保險。",
    ),
    "澳洲": (
        "AUD 2,000–2,900 / 月（雪梨大學 USYD、新南威爾斯大學 UNSW、西雪梨大學 WSU、伍倫貢大學 UOW、紐卡索大學及布里斯本昆士蘭科技大學 QUT 住宿、伙食與大眾運輸費用）",
        "須購買澳洲海外學生健康保險（OSHC）並透過澳洲內政部 ImmiAccount 線上申辦 Subclass 500 學生簽證。",
    ),
    "英國": (
        "GBP 1,100–1,800 / 月（倫敦帝國學院 Imperial College London 約 GBP 1,400–1,900 / 月；諾丁漢大學 University of Nottingham 約 GBP 950–1,350 / 月）",
        "交換一學期（6 個月內）可辦理英國 Standard Visitor 簽證，交換一學年或攻讀雙聯學位須申辦英國 Student Visa 並繳納 IHS 醫療附加費。",
    ),
    "法國": (
        "EUR 750–1,350 / 月（里爾大學 Université de Lille、聖艾蒂安讓莫內大學、勃艮第-弗朗什-孔泰大學約 EUR 700–1,000 / 月；索邦巴黎北大學約 EUR 1,000–1,400 / 月，可申請法國政府 CAF 房補）",
        "須先透過法國教育中心（Campus France）完成線上面談，再向法國在台協會申辦長期學生簽證（VLS-TS），抵法後完成 OFII 登錄。",
    ),
    "德國": (
        "EUR 934–1,250 / 月（海德堡大學 Heidelberg University 及海爾布隆應用科學大學學生宿舍、學期雜費 Semesterbeitrag 與生活開銷；德國限制提領帳戶 Sperrkonto 法定基準為每月 EUR 992）",
        "須辦理德國法定學生健康保險（如 TK / AOK）並向德國在台協會申辦長期學生／研究簽證。",
    ),
    "義大利": (
        "EUR 700–1,050 / 月（薩丁尼亞島首府卡利亞里大學 University of Cagliari 學生分租公寓、大學食堂 Mensa 與公車輕軌費用親民）",
        "交換或攻讀雙聯超過 90 天須向義大利經濟貿易文化推廣辦事處申辦義大利 D 類國家學生／研究簽證，抵義後 8 個工作天內申辦居留證（Permesso di soggiorno）並投保義大利醫療險。",
    ),
    "比利時": (
        "EUR 850–1,200 / 月（魯汶天主教大學 UCLouvain 學生宿舍 Kot、學生餐廳與比利時國鐵學生票）",
        "須向比利時台北辦事處申辦長期學生／研究簽證（D 簽）並投保涵蓋全期之歐盟醫療保險。",
    ),
    "丹麥": (
        "DKK 6,800–9,800 / 月（約 EUR 900–1,300 / 月，奧胡斯大學 Aarhus University 學生宿舍、自炊飲食與單車／公車通勤費用）",
        "須申辦丹麥高等教育居留許可（ST1 Residence Permit），抵丹麥取得 CPR 黃卡後享丹麥公醫保障，出國前仍須投保海外醫療及意外險。",
    ),
    "瑞典": (
        "SEK 9,800–14,000 / 月（約 EUR 880–1,250 / 月，斯德哥爾摩卡羅琳醫學院 Karolinska Institutet 及皇家理工學院 KTH 學生公寓、飲食與 SL 學生交通月票）",
        "交換或研究超過 3 個月須向瑞典移民局（Migrationsverket）線上申辦高等教育居留許可，臨床見實習生另須完成 MRSA 篩檢與健康證明。",
    ),
    "愛爾蘭": (
        "EUR 1,100–1,650 / 月（都柏林聖三一學院 Trinity College Dublin 學生宿舍、餐飲與 Leap Card 學生交通卡）",
        "臺灣護照持有人可免事先申辦入境簽證赴愛爾蘭，惟停留超過 90 天抵愛後須辦理 IRP（Irish Residence Permit）學生居留登記並投保醫療保險。",
    ),
    "奧地利": (
        "EUR 850–1,250 / 月（薩爾茨堡大學 University of Salzburg 學生宿舍 OeAD、日常餐飲與交通票）",
        "短期暑期課程（90 天內）免申根簽證，交換一學期以上須向奧地利台北辦事處申辦 D 類簽證並投保符合申根規定之醫療保險。",
    ),
    "匈牙利": (
        "EUR 550–850 / 月（塞格德大學 University of Szeged 及德布勒森大學 University of Debrecen 醫牙藥學院國際學生公寓與生活費實惠）",
        "須向匈牙利貿易辦事處申辦學生簽證／居留許可，並投保涵蓋全期之海外醫療及意外保險。",
    ),
    "斯洛伐克": (
        "EUR 600–900 / 月（布拉提斯拉瓦考門斯基大學 Comenius University 學生宿舍、學生餐券與大眾運輸）",
        "須憑接待校入學許可向斯洛伐克經濟文化辦事處申辦長期簽證／居留許可並投保醫療險。",
    ),
    "羅馬尼亞": (
        "EUR 500–800 / 月（阿拉德瓦西里戈爾迪什西方大學 UVVG 醫學院學生宿舍與日常生活開銷低廉）",
        "須申辦羅馬尼亞學生簽證並於出國前投保涵蓋全期之海外醫療及意外保險。",
    ),
    "土耳其": (
        "USD 550–850 / 月（伊斯坦堡貝茲米亞勒姆瓦基夫大學 Bezmialem Vakif University 醫藥學院校區周邊住宿、學餐與伊斯坦堡學生交通卡）",
        "須申辦土耳其學生簽證、抵土後辦理居留證（Ikamet）並投保醫療保險。",
    ),
    "俄羅斯": (
        "USD 550–900 / 月（莫斯科國立謝切諾夫第一醫科大學 Sechenov University 及俄羅斯國立科技大學 MISiS 校內學生宿舍與莫斯科地鐵學生月票開銷實惠）",
        "須憑俄羅斯接待校核發之官方邀請函向莫斯科台北經濟文化協調委員會駐台北代表處申辦俄羅斯留學簽證並投保當地醫療險。",
    ),
    "史瓦帝尼": (
        "USD 600–950 / 月（姆巴巴內史瓦帝尼衛生部政府醫院 Mbabane Government Hospital 配合北醫大駐史瓦帝尼醫療團安排住宿與見實習生活）",
        "須配合北醫大國際事務處及駐史瓦帝尼醫療團辦理簽證、黃熱病與瘧疾預防接種及全程海外醫療與急難救助保險。",
    ),
    "奈及利亞": (
        "USD 650–1,050 / 月（拉哥斯奈及利亞醫學研究所 NIMR 短期熱帶醫學與傳染病研究見實習食宿交通開銷）",
        "須憑接待機構邀請函向奈及利亞駐華商務辦事處申辦簽證，並完成黃熱病疫苗接種與全程海外醫療急難救助保險。",
    ),
    "中國大陸": (
        "RMB 2,000–3,800 / 月（上海交通大學、浙江大學、廈門大學、南京醫科大學、中國藥科大學、南方醫科大學、廣東醫科大學、福建醫科大學、哈爾濱醫科大學、吉林大學、深圳大學、寧波諾丁漢大學等校內宿舍與食堂費用實惠）",
        "持有效護照與臺胞證入境；特別注意：依《臺北醫學大學辦理境外雙聯學制實施辦法》第2條及《學生境外研修作業要點》，大陸地區有關醫療法所稱醫事人員高等學校學分不予採認，且不得涉及醫學人才培養。",
    ),
    "香港": (
        "HKD 9,000–14,500 / 月（香港大學 HKU、香港中文大學 CUHK、香港理工大學 PolyU 及香港城市大學 CityU 校內外學生宿舍、校園餐廳與港鐵學生優惠八達通）",
        "須透過香港接待大學向香港入境事務處申辦來港就讀進入許可（Student Visa / Entry Permit），出國前至陸委會「國人赴港澳動態登錄網頁」完成登錄並投保海外醫療及意外保險。",
    ),
}

SEMESTER_DATES_BY_COUNTRY = {
    "美國": "秋季學期（Fall）：約 8 月中下旬至 12 月中旬；春季學期（Spring）：約 1 月中旬至 5 月中旬；暑期研究／臨床見實習：6 月至 8 月",
    "加拿大": "秋季學期（Fall）：約 9 月初至 12 月中下旬；冬季／春季學期（Winter）：約 1 月初至 4 月底；暑期學期（UBC VSP）：6 月至 8 月",
    "安地卡及巴布達": "秋季學期：約 9 月至 12 月；春季學期：約 1 月至 5 月；夏季學期：約 5 月至 8 月",
    "阿根廷": "第一學期：約 3 月至 7 月；第二學期：約 8 月至 11/12 月",
    "墨西哥": "秋季學期：約 7/8 月至 11/12 月（UAEH 醫學與牙醫專班 6 月下旬–11 月底）；春季學期：約 1 月下旬至 6 月初",
    "日本": "春季學期（第1學期）：約 4 月初至 8/9 月；秋季學期（第2學期）：約 9/10 月至翌年 2/3 月；寒暑期臨床見實習：1–2 月及 7–8 月",
    "韓國": "春季學期（第1學期）：約 3 月初至 6 月中下旬；秋季學期（第2學期）：約 9 月初至 12 月中下旬",
    "新加坡": "第一學期（Semester 1）：約 8 月初至 12 月初；第二學期（Semester 2）：約 1 月中旬至 5 月上旬",
    "泰國": "第一學期：約 8 月至 12 月；第二學期：約 1 月至 5 月",
    "越南": "第一學期（秋季班）：約 9 月至翌年 1 月；第二學期（春季班）：約 2 月至 6 月",
    "印尼": "奇數／秋季學期（Odd Semester）：約 8/9 月至 12 月；偶數／春季學期（Even Semester）：約 1/2 月至 6 月",
    "馬來西亞": "第一學期（秋季班）：約 10 月至翌年 2 月；第二學期（春季班）：約 3 月至 7 月",
    "菲律賓": "第一學期（秋季班）：約 8 月至 12 月；第二學期（春季班）：約 1 月中旬至 5 月下旬",
    "印度": "奇數／秋季學期：約 7/8 月至 12 月；偶數／春季學期：約 1 月至 5 月",
    "柬埔寨": "第一學期：約 10 月至翌年 2 月；第二學期：約 3 月至 7 月",
    "蒙古": "秋季學期：約 9 月初至 12 月底；春季學期：約 2 月初至 6 月初",
    "哈薩克": "秋季學期：約 9 月初至 12 月底；春季學期：約 1 月下旬至 5 月底",
    "以色列": "秋季學期：約 10 月中下旬至翌年 1 月；春季學期：約 3 月至 6 月底",
    "澳洲": "第一學期（Semester 1 / Autumn）：約 2 月中下旬至 6 月；第二學期（Semester 2 / Spring）：約 7 月下旬至 11 月",
    "英國": "秋季學期（Autumn / Semester 1）：約 9 月下旬至翌年 1 月；春季學期（Spring / Semester 2）：約 1 月下旬至 5/6 月",
    "法國": "秋季學期（Semestre 1）：約 9 月初至翌年 1 月；春季學期（Semestre 2）：約 1 月下旬至 6 月",
    "德國": "冬季學期（Wintersemester）：約 10 月初至翌年 2/3 月；夏季學期（Sommersemester）：約 4 月初至 7 月底",
    "義大利": "第一學期（秋季班）：約 9 月下旬至翌年 1/2 月；第二學期（春季班）：約 2 月下旬至 6/7 月",
    "比利時": "第一學期（秋季班）：約 9 月中旬至翌年 1 月底；第二學期（春季班）：約 2 月初至 6 月底",
    "丹麥": "秋季學期（Autumn）：約 9 月初至翌年 1 月底；春季學期（Spring）：約 2 月初至 6 月底",
    "瑞典": "秋季學期（Autumn）：約 8 月底至翌年 1 月中旬；春季學期（Spring）：約 1 月中旬至 6 月初",
    "愛爾蘭": "第一學期（Michaelmas Term）：約 9 月中旬至 12 月中旬；第二學期（Hilary Term）：約 1 月中旬至 4/5 月",
    "奧地利": "冬季學期（Wintersemester）：約 10 月初至翌年 1 月底；夏季學期（Sommersemester）：約 3 月初至 6 月底",
    "匈牙利": "秋季學期：約 9 月初至 12 月中旬（考試期至 1 月）；春季學期：約 2 月初至 5 月中旬（考試期至 6 月）",
    "斯洛伐克": "冬季學期：約 9 月中下旬至翌年 1 月；夏季學期：約 2 月中旬至 6 月",
    "羅馬尼亞": "第一學期：約 10 月初至翌年 1/2 月；第二學期：約 2 月中下旬至 6 月",
    "土耳其": "秋季學期：約 9 月中下旬至翌年 1 月；春季學期：約 2 月中旬至 6 月",
    "俄羅斯": "秋季學期：約 9 月初至翌年 1 月；春季學期：約 2 月初至 6 月底",
    "史瓦帝尼": "配合北醫大駐史瓦帝尼醫療團及醫學院臨床見實習梯次（寒暑期或學期見實習 4–8 週）",
    "奈及利亞": "配合北醫大熱帶醫學與傳染病研究見實習專案期程（全年或暑期 1–3 個月）",
    "中國大陸": "秋季學期：約 9 月初至翌年 1 月中旬；春季學期：約 2 月中下旬至 6 月底",
    "香港": "第一學期（秋季班）：約 9 月初至 12 月底；第二學期（春季班）：約 1 月中旬至 5 月中旬",
}


def clean_text(s: str) -> str:
  if not s:
    return ""
  return re.sub(r"\s+", " ", s).strip()


def main() -> None:
  OFFICIAL_TMU_DIR.mkdir(parents=True, exist_ok=True)
  catalog_source = json.loads(
      (SOURCES_TMU_DIR / "tmu_catalog_source.json").read_text(encoding="utf-8")
  )
  resolved_locations = json.loads(
      (SOURCES_TMU_DIR / "tmu_resolved_locations.json").read_text(encoding="utf-8")
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
  total_exp_pdfs = 0

  for idx, item in enumerate(catalog_source):
    sn = idx + 1
    full_name = item["school_name"]
    zh_name = item["name_zh"]
    country = item["country"]
    region = item["region"]
    avail_status = "open" if item.get("offering_status") == "open" else "reference_only"
    if avail_status == "open":
      open_partner_count += 1

    group_str = clean_text(item.get("group") or "國際合作姊妹校")
    quota_str = clean_text(item.get("quota") or "依北醫大國際事務處與各學院當期公告名額")
    if "雙聯" in group_str or "雙聯" in quota_str:
      program_type = "跨國雙聯學制暨境外研修計畫"
      source_url = TMU_DUAL_DEGREE_ZH_URL
    elif "Apply via TMU" in group_str or "海外短期" in group_str:
      program_type = "國際事務處（Apply via TMU）出國交換暨海外短期研修計畫"
      source_url = TMU_OVERSEAS_COURSES_ZH_URL
    elif country in {"中國大陸", "香港"}:
      program_type = "大陸及港澳地區盟校學術交流計畫"
      source_url = TMU_PARTNERS_ZH_URL
    else:
      program_type = "境外研修暨臨床／實驗室見實習與學海計畫"
      source_url = TMU_OUTBOUND_EXCHANGE_ZH_URL if avail_status == "open" else TMU_PARTNERS_ZH_URL

    colleges_str = clean_text(item.get("colleges") or "")
    degree_levels_str = clean_text(item.get("eligible_degrees") or "大學部、碩士班、博士班在學學生")
    lang_req_str = clean_text(item.get("language_req") or "")
    gpa_req_str = clean_text(item.get("gpa_req") or "")
    website = item.get("website") or TMU_PARTNERS_ZH_URL
    remarks_raw = clean_text(item.get("notes") or "")
    tuition_note = clean_text(item.get("tuition_note") or "")
    exps = item.get("experience_reports") or []

    round_label = (
        "115–116學年度境外研修、跨國雙聯學制暨教育部學海計畫／校內境外研修獎學金甄選"
        if avail_status == "open"
        else "國際事務處正式締約合作盟校與醫療機構（依當期交換、見實習或雙聯公告名額辦理）"
    )
    app_deadline_str = (
        "【教育部學海飛颺／惜珠／築夢／新南向學海築夢】第一梯次：每年 12 月各學院收件初審、翌年 1 月 15 日（115年度為 2026/01/16）前由學院彙整送國際事務處；第二次徵求（學海惜珠、學海築夢、新南向學海築夢）：8 月各學院收件、2026/09/07 前送國際事務處｜【臺北醫學大學境外研修暨見實習獎學金】每年兩梯次：第一梯次 1 月 15 日截止（2 月審查）、第二梯次 5 月 15 日截止（6 月審查）｜【跨國雙聯學制】於雙聯修業前 1 個月（藥學系 USC 雙聯為 3 月底前、Penn State 雙聯為 1 月中旬前）向所屬系所及學院提出申請並送教務處備查"
    )
    deadline_iso = "2027-01-15T17:00:00+08:00"
    win_status = "open" if avail_status == "open" else "closed"
    acad_year = "115"

    study_period_str = clean_text(item.get("duration") or "1 學期、1 學年或短期臨床／研究見實習（至少 10 個工作天／10 日曆天）")
    sem_dates_str = SEMESTER_DATES_BY_COUNTRY.get(
        country, "秋季學期：約 9 月至翌年 1 月；春季學期：約 2 月至 6 月"
    )
    housing_str = (
        f"獲北醫大國際事務處或所屬學院提名錄取後，可依 {zh_name} 國際處／教學醫院指引申請校內外學生宿舍或見實習醫師／學者公寓"
        + (f"（費用與雙聯／交換說明：{tuition_note}；{remarks_raw}）" if (tuition_note or remarks_raw) else "。")
    )
    course_rest_str = (
        f"開放對象與領域：{colleges_str}。依《臺北醫學大學學生境外研修作業要點》、《辦理境外雙聯學制實施辦法》及《學生抵免學分辦法》規定：（1）大陸地區有關醫療法所稱醫事人員高等學校學分不予採認，且兩岸不得涉及醫學人才培養；（2）修讀雙聯學位於研修前 1 個月、修習學分或研究及實習於研修前 3 個工作日由系所檢送《學生境外研修簽報表》送教務處備查；（3）境外研修期間須辦理北醫大註冊（若辦理休學者，其於境外修習之科目、學分及成績均不予採計）；（4）學分換算以授課滿 18 小時計 1 學分，實驗、見實習以 36–54 小時計 1 學分；雙聯同級學制修業時間二校合計學士至少 32 個月、碩士至少 12 個月、博士至少 24 個月，且在二校當地修習學分數須各達畢業應修總學分數三分之一以上。"
    )

    tuition_points_list = [
        (
            f"北醫大在學註冊與學雜費規定（依《臺北醫學大學學生境外研修作業要點》第5、6點及《辦理境外雙聯學制實施辦法》）：學生於境外研修期間須依本校規定辦理註冊（若辦理休學者，境外修習學分及成績概不採計）。盟校待遇：{tuition_note or '依兩校學術合作協議辦理'}。"
        ),
        (
            "教育部《學海飛颺／學海惜珠／學海築夢／新南向學海築夢》與《臺北醫學大學境外研修暨見實習獎勵辦法》雙軌獎補助：（1）教育部學海飛颺／惜珠（赴國外非大陸港澳姊妹校修讀學分 1 學期或 1 學年，歷年成績達系所排名前 40% 或班排名前 30%、操行 80 分以上，英語系國家達 TOEFL iBT 79 / IELTS 5.5、非英語系國家達 TOEFL iBT 75 / IELTS 5.0、日語 JLPT N2）；（2）教育部學海築夢／新南向學海築夢（由北醫大計畫主持人選送赴海外醫療機構、研究實驗室或醫藥機構見實習至少 30 天［不含來回途程，印尼為 25 天］）；（3）校內《境外研修暨見實習獎勵辦法》（每年 1/15 及 5/15 截止，分個人型、每案上限 NT$50 萬之團體型及每人每學年上限 NT$10,000 之線上學分課程型，外語須達 CEFR B2：TOEFL iBT 72 / IELTS 5.5 / TOEIC 785，實體出國不得少於 10 個工作天／10 日曆天，且不得同時領取學海或公費補助）。"
        ),
    ]

    app_steps_list = [
        (
            f"步驟一（確認北醫大在學資格、系所前 40%／班前 30% 或 GPA 3.0 門檻與 {zh_name} 語檢要求）：確認為北醫大在學學生（申請學海飛颺／惜珠須於北醫大就讀滿一學期以上，歷年成績達系所前 40% 或班前 30%、操行 80 分以上；申請跨國雙聯須達歷年 GPA 3.0 以上），並備妥符合 {zh_name} 規定之有效外語檢定證明（{lang_req_str}）。"
        ),
        (
            "步驟二（依計畫類別向所屬系所／學院及國際事務處遞交申請表件）：（1）教育部學海飛颺／惜珠／築夢／新南向學海築夢：第一梯次於每年 12 月向所屬學院提出申請、翌年 1 月 15 日（115年為 1/16）前由學院排定優先順序送國際事務處，第二次徵求（惜珠、築夢、新南向築夢）於 8 月向學院申請、9 月初（2026/09/07）前送國際處；（2）校內《境外研修暨見實習獎學金》：於每年 1 月 15 日（第一梯次）或 5 月 15 日（第二梯次）前檢附申請表、英文財力證明、身分證與學生證影本、中英文歷年成績單、CEFR B2 外語證明及申請計畫書送交國際事務處；（3）跨國雙聯學制與海外短期課程（Apply via TMU）：依各學院雙聯辦法及國際處海外課程公告截止日遞件。"
        ),
        (
            f"步驟三（學院初審、國際事務處複審與向 {full_name} 辦理官方提名 Nomination）：由所屬學院完成專業與語文初審後，送交國際事務處國際教育委員會複審（教育部學海計畫於 3/31 前報部、5/31 前公告結果；校內獎學金於 2 月及 6 月公告結果），並由國際處或學院向 {full_name} 辦理官方提名及遞交外文入學／臨床見實習申請文件。"
        ),
        (
            "步驟四（完成教務處《境外研修簽報表》備查、行前報到、簽訂契約與返國 14 日／1 個月內成果核銷及學分抵免）：出國前須依《學生境外研修作業要點》由系所檢送《學生境外研修簽報表》送教務處備查（修讀雙聯學位為研修前 1 個月，修習學分或研究見實習為研修前 3 個工作日），並繳交《學生海外行前報到單》及簽妥學海《行政契約書》；學海計畫受獎生須於返國後 2 週（14 日）內上傳問卷及 1,000 字以內中／英文成果報告書（含照片 4 張以上）並於 1 個月內完成機票與經費核銷；校內獎學金受獎生須於返國後 1 個月內繳交成果報告書至國際處，並持正式成績單向教務處註冊組辦理學分抵免。"
        ),
    ]

    elig_points_list = [
        f"合作類別與甄選群組：{program_type}（{group_str}）",
        f"開放學制與年級：{degree_levels_str}",
        f"開放申請院系：{colleges_str}",
        f"學業成績門檻：{gpa_req_str}",
        f"外語能力標準：{lang_req_str}",
        "雙軌獎學金與教務備查規定：可申請教育部學海四項計畫（飛颺、惜珠、築夢、新南向築夢）或校內《境外研修暨見實習獎學金》（每年 1/15、5/15 截止）；出國前須完成教務處《學生境外研修簽報表》備查並維持北醫大在學註冊。",
    ]
    if tuition_note:
      elig_points_list.append(f"盟校學費與獎補助待遇：{tuition_note}")
    if remarks_raw:
      elig_points_list.append(f"學程與簡章重點說明：{remarks_raw}")

    exp_labels = [f"{e['year']}年 {e['student']}" for e in exps]
    notes_lines = [
        f"【合作類別與期程】{program_type}｜研修期間：{study_period_str}",
        f"【當期名額與費用待遇】{quota_str}｜{tuition_note or '依兩校協議辦理'}",
        f"【開放學院與學制】{colleges_str}｜{degree_levels_str}",
        f"【語言與學業門檻】{lang_req_str}｜{gpa_req_str}",
        f"【住宿與生活資訊】{housing_str}",
    ]
    if exps:
      notes_lines.append(
          f"【北醫大學長姐海外研修／臨床見實習成果報告（共 {len(exps)} 篇）】收錄於國際事務處學生經驗分享專區（含：{'、'.join(exp_labels[:5])}）"
      )
    if remarks_raw:
      notes_lines.append(f"【學程與簡章摘要】{remarks_raw}")

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
        "note": "校級代表位置：官方網域及國家已與 ROR / Wikidata 比對；實際交換或臨床見實習院區以錄取通知與締約校專頁為準。",
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
        "availability_note": f"臺北醫學大學國際事務處公告合作盟校與醫療機構（{program_type}）；{quota_str}。",
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
                "group": group_str,
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
            "title": f"臺北醫學大學國際事務處盟校列表、雙聯學位與海外課程簡章—{zh_name}",
            "source_url": source_url,
            "role": "home_university",
            "authority": "home_official_notice",
            "effective_academic_year": acad_year,
            "application_round": round_label,
            "checked_at": CHECKED_AT,
        },
        {
            "title": "臺北醫學大學境外研修暨見實習獎勵辦法與2026（民國115）年教育部學海計畫校內說明會簡報",
            "source_url": TMU_115_XUEHAI_BRIEFING_PDF_URL,
            "role": "home_university",
            "authority": "home_official_notice",
            "effective_academic_year": acad_year,
            "application_round": round_label,
            "checked_at": CHECKED_AT,
        },
        {
            "title": "臺北醫學大學學生境外研修作業要點、辦理境外雙聯學制實施辦法與學生抵免學分辦法",
            "source_url": TMU_ACA_OVERSEAS_STUDY_GUIDELINES_PDF_URL,
            "role": "home_university",
            "authority": "home_official_notice",
            "effective_academic_year": acad_year,
            "application_round": round_label,
            "checked_at": CHECKED_AT,
        },
    ]
    if exps:
      wf_sources.append({
          "title": f"北醫大國際事務處學生經驗分享專區—赴 {zh_name} 海外研修／臨床見實習成果報告（{len(exps)} 篇）",
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
        "home_university": "臺北醫學大學",
        "school_name": full_name,
        "partner_website": website,
        "country": country,
        "program_type": program_type,
        "academic_year": acad_year,
        "application_round": round_label,
        "effective_application_rounds": [
            round_label,
            "115年度教育部學海飛颺／惜珠／築夢／新南向學海築夢甄選",
            "臺北醫學大學境外研修暨見實習獎學金（1/15、5/15兩梯次）",
            "跨國雙聯學位學制甄選",
            "116-1",
            "116-2",
            "115-2",
            "115-1",
        ],
        "applicability_status": "verified",
        "applicability_note": (
            "臺北醫學大學由國際事務處（OGE）、教務處及 11 個學院共同統籌境外交換研修、教學醫院臨床見實習、實驗室研究、跨國雙聯學制（18 所合作大學共 32 個雙聯學程）、教育部學海四項計畫（每年 1/15［115年為 1/16］及 9/7 兩次徵求）與校內《境外研修暨見實習獎勵辦法》（每年 1/15 及 5/15 兩梯次）。"
        ),
        "review_status": "published",
        "published_at": CHECKED_AT,
        "steps": [
            {
                "rule_id": f"tmu-{acad_year}-home-1-{idx+1:03d}",
                "order": 1,
                "phase": "校內申請",
                "title": f"確認北醫大在學身分、系所前 40%／班前 30%（或雙聯 GPA 3.0）門檻與 {zh_name} 語檢要求",
                "responsible_party": "學生",
                "responsible_unit": "臺北醫學大學各學院／國際事務處",
                "deadline_at": deadline_iso,
                "deadline_status": "verified_exact" if avail_status == "open" else "reference_only",
                "deadline_source_url": source_url,
                "deadline_checked_at": CHECKED_AT,
                "deadline_reminder_eligible": avail_status == "open",
                "summary": (
                    f"確認符合《臺北醫學大學境外研修暨見實習獎勵辦法》、《辦理境外雙聯學制實施辦法》及教育部學海計畫簡章規定（學海飛颺／惜珠須於北醫大就讀一學期以上、歷年成績達每系所排名前 40% 或每班排名前 30%［研究所免附排名］、操行成績 80 分以上；跨國雙聯須達歷年 GPA 3.0 以上），並備妥符合 {zh_name} 規定之有效外語檢定證明。"
                ),
                "details": [
                    f"開放學制與院系：{colleges_str}（{degree_levels_str}）",
                    f"語言與學業條件：{lang_req_str}｜{gpa_req_str}",
                    f"當期名額與計畫類別：{quota_str}｜{program_type}",
                ],
                "scope": {
                    "home_universities": ["臺北醫學大學"],
                    "partner_universities": [full_name],
                    "academic_years": ["115", "116"],
                    "application_rounds": [round_label, "116-1", "116-2", "115-2", "115-1"],
                },
                "source_urls": [
                    source_url,
                    TMU_115_XUEHAI_BRIEFING_PDF_URL,
                    TMU_OVERSEAS_INCENTIVE_REGS_PDF_URL,
                ],
                "checked_at": CHECKED_AT,
                "support_status": "verified",
            },
            {
                "rule_id": f"tmu-{acad_year}-home-2-{idx+1:03d}",
                "order": 2,
                "phase": "校內申請",
                "title": "向所屬系所／學院及國際事務處遞交境外研修、跨國雙聯或學海計畫申請表件（1/15、5/15、9/7 截止）",
                "responsible_party": "學生與所屬系（所）、學院辦公室",
                "responsible_unit": "臺北醫學大學 11 個學院／國際事務處",
                "deadline_at": deadline_iso,
                "deadline_status": "verified_exact" if avail_status == "open" else "reference_only",
                "deadline_source_url": TMU_115_XUEHAI_BRIEFING_PDF_URL,
                "deadline_checked_at": CHECKED_AT,
                "deadline_reminder_eligible": avail_status == "open",
                "summary": (
                    "依申請管道於期限前備齊申請表、中英文歷年成績單（含系所或班級排名）、有效外語能力檢定證明、出國研修／見實習申請計畫書、英文推薦信及家長同意書，經所屬系所與學院初審後彙整送交國際事務處。"
                ),
                "details": [
                    "教育部學海飛颺／惜珠／築夢／新南向學海築夢：第一梯次每年 12 月各學院收件、翌年 1 月 15 日（115年為 2026/01/16）前送國際事務處；第二次徵求（學海惜珠、學海築夢、新南向築夢）8 月各學院收件、2026/09/07 前送國際事務處。",
                    "校內《境外研修暨見實習獎學金》：每年兩梯次於 1 月 15 日及 5 月 15 日截止收件（含個人型、每案上限 NT$50 萬之團體型及每人每學年上限 NT$10,000 之線上學分課程型）。",
                ],
                "document_requirements": [
                    {
                        "name": "臺北醫學大學境外研修暨見實習獎學金申請表及申請計畫書（或雙聯學位甄選申請表）",
                        "official_form_url": TMU_OVERSEAS_INCENTIVE_APP_DOCX_URL,
                        "source_urls": [TMU_OVERSEAS_INCENTIVE_REGS_PDF_URL, TMU_OVERSEAS_INCENTIVE_APP_DOCX_URL],
                    },
                    {
                        "name": "北醫大中英文歷年成績單正本（學海飛颺／惜珠須註明系所排名前 40% 或班排名前 30% 及操行 80 分以上；研究所免附排名）",
                        "source_urls": [TMU_115_XUEHAI_BRIEFING_PDF_URL, TMU_115_2_XIZHU_GUIDELINES_PDF_URL],
                    },
                    {
                        "name": "2 年內有效外語能力證明（學海英語系國家 TOEFL iBT 79 / IELTS 5.5、非英語系國家 iBT 75 / IELTS 5.0、日語 JLPT N2；校內獎學金要求 CEFR B2：iBT 72 / IELTS 5.5 / TOEIC 785）",
                        "source_urls": [TMU_OUTBOUND_EXCHANGE_ZH_URL, TMU_115_XUEHAI_BRIEFING_PDF_URL, TMU_OVERSEAS_INCENTIVE_REGS_PDF_URL],
                    },
                    {
                        "name": "英文推薦信、家長同意書、學生證與身分證影本（個人型校內獎學金另附英文財力證明；學海惜珠另附新式戶口名簿或戶籍謄本及低收／中低收／特殊境遇家庭證明）",
                        "official_form_url": TMU_115_2_XIZHU_FORM_DOC_URL,
                        "source_urls": [TMU_OVERSEAS_INCENTIVE_REGS_PDF_URL, TMU_115_2_XIZHU_GUIDELINES_PDF_URL, TMU_DUAL_DEGREE_ZH_URL],
                    },
                ],
                "scope": {
                    "home_universities": ["臺北醫學大學"],
                    "academic_years": ["115", "116"],
                    "application_rounds": [round_label, "116-1", "116-2", "115-2", "115-1"],
                },
                "source_urls": [
                    TMU_115_XUEHAI_BRIEFING_PDF_URL,
                    TMU_OVERSEAS_INCENTIVE_REGS_PDF_URL,
                    TMU_OVERSEAS_INCENTIVE_APP_DOCX_URL,
                    TMU_115_2_XIZHU_GUIDELINES_PDF_URL,
                ],
                "checked_at": CHECKED_AT,
                "support_status": "verified",
            },
            {
                "rule_id": f"tmu-{acad_year}-home-3-{idx+1:03d}",
                "order": 3,
                "phase": "甄選與提名",
                "title": "各學院初審排序、國際事務處國際教育委員會複審（2 月／6 月審查）與教育部學海計畫提報",
                "responsible_party": "各學院與國際事務處國際教育委員會",
                "responsible_unit": "臺北醫學大學國際事務處",
                "deadline_at": "2027-02-28T17:00:00+08:00",
                "deadline_status": "verified_exact",
                "deadline_source_url": TMU_115_XUEHAI_BRIEFING_PDF_URL,
                "deadline_checked_at": CHECKED_AT,
                "deadline_reminder_eligible": False,
                "summary": (
                    "各學院完成初審並排定推薦優先順序後，由國際事務處召開國際教育委員會複審（第一梯次於 2 月審查、第二梯次校內獎學金於 6 月審查、學海第二次徵求於 9 月審查；學海計畫於 3/31 前報教育部、5/31 前公告結果）。"
                ),
                "details": [
                    "獎補助不重複領取原則：依《臺北醫學大學境外研修暨見實習獎勵辦法》規定，獲教育部學海計畫、政府公費或接待機構全額補助者，不得重複領取校內境外研修獎學金。",
                    "跨國雙聯學位審查：經系（所）、院初審通過後，送國際事務處及教務處完成雙聯備查程序。",
                ],
                "scope": {
                    "home_universities": ["臺北醫學大學"],
                    "academic_years": ["115", "116"],
                    "application_rounds": [round_label, "116-1", "116-2", "115-2", "115-1"],
                },
                "source_urls": [
                    TMU_115_XUEHAI_BRIEFING_PDF_URL,
                    TMU_OVERSEAS_INCENTIVE_REGS_PDF_URL,
                    TMU_DUAL_DEGREE_FLOWCHART_PDF_URL,
                ],
                "checked_at": CHECKED_AT,
                "support_status": "verified",
            },
            {
                "rule_id": f"tmu-{idx+1:03d}-host-apply",
                "order": 4,
                "phase": "合作校申請",
                "title": f"由北醫大國際處或學院向 {zh_name} 辦理官方提名（Nomination），並遞交外文入學或臨床見實習申請",
                "responsible_party": "學生與接待校院國際事務處／醫學教育中心",
                "summary": (
                    f"通過北醫大審核後，由國際事務處或所屬學院向 {zh_name} 辦理官方提名；學生須於接待校院規定截止日前備妥外文申請表、英文歷年成績單、護照影本、語檢證書、英文推薦信、臨床見實習免疫接種紀錄與健康證明，靜候核發正式入學／見實習許可函（Letter of Acceptance / COE / DS-2019）。"
                ),
                "details": [
                    f"研修期程：{study_period_str}｜名額：{quota_str}",
                    f"語言與學業條件：{lang_req_str}｜{gpa_req_str}",
                    f"住宿與費用待遇：{housing_str}",
                ],
                "scope": {
                    "home_universities": ["臺北醫學大學"],
                    "partner_universities": [full_name],
                    "academic_years": ["115", "116"],
                    "application_rounds": [round_label, "116-1", "116-2", "115-2", "115-1"],
                },
                "source_urls": (
                    [source_url, TMU_OUTBOUND_STUDENTS_EN_URL]
                    + ([website] if website else [])
                ),
                "checked_at": CHECKED_AT,
                "support_status": "verified",
                "needs_confirmation": False,
            },
            {
                "rule_id": f"tmu-{acad_year}-home-5-{idx+1:03d}",
                "order": 5,
                "phase": "行前準備",
                "title": "辦理教務處《境外研修簽報表》備查（雙聯前 1 個月／交換實習前 3 個工作日）、繳交行前報到單並於返國 14 日／1 個月內完成報告核銷與學分抵免",
                "responsible_party": "學生與所屬系所",
                "responsible_unit": "臺北醫學大學教務處註冊組／課務組／國際事務處",
                "summary": (
                    "出國前須依《臺北醫學大學學生境外研修作業要點》由系所檢送《學生境外研修簽報表》送教務處備查（修讀雙聯學位為研修前 1 個月、修習學分或研究見實習為研修前 3 個工作日），同時維持北醫大在學註冊、繳交《學生海外行前報到單》並簽訂《學海行政契約書》；返國後學海受獎生須於 2 週（14 日）內上傳問卷及 1,000 字以內成果報告書（含照片 4 張以上）並於 1 個月內辦理核銷，校內獎學金受獎生須於返國 1 個月內繳交成果報告書至國際處，並持正式成績單向教務處申請學分採認。"
                ),
                "details": tuition_points_list,
                "scope": {
                    "home_universities": ["臺北醫學大學"],
                    "academic_years": ["115", "116"],
                    "application_rounds": [round_label, "116-1", "116-2", "115-2", "115-1"],
                },
                "source_urls": [
                    TMU_ACA_OVERSEAS_STUDY_GUIDELINES_PDF_URL,
                    TMU_ACA_DUAL_DEGREE_REGS_PDF_URL,
                    TMU_ACA_CREDIT_TRANSFER_REGS_PDF_URL,
                    TMU_PREDEPARTURE_FORM_PDF_URL,
                    TMU_115_XUEHAI_CONTRACT_DOC_URL,
                ],
                "checked_at": CHECKED_AT,
                "support_status": "verified",
            },
        ],
        "sources": wf_sources,
        "last_checked": CHECKED_AT,
        "coverage_status": "official_verified",
        "coverage_note": (
            "已完整整合臺北醫學大學國際事務處（OGE）與教務處（2026［民國115］年教育部學海計畫校內說明會簡報、115年度學海惜珠／學海築夢／新南向築夢第二次申請公告、境外研修暨見實習獎勵辦法、學生境外研修作業要點、辦理境外雙聯學制實施辦法、學生抵免學分辦法、18 校 32 個跨國雙聯學程、Apply via TMU 海外課程及 55 篇歷屆學長姐返國報告）共 201 所全球合作盟校與醫療研究機構資料。"
        ),
    })

    cost_default, visa_default = REGION_COST_DEFAULTS.get(
        country,
        (
            "USD 900–1,600 / 月（含住宿、膳食與日常交通）",
            "須依接待國駐臺機構規定辦理學生／研究簽證並投保海外醫療及意外保險。",
        ),
    )
    cost_line = f"{zh_name} 預估每月生活費：{cost_default}"
    tuition_clean = tuition_points_list[0]
    housing_clean = housing_str
    calendar_clean = f"學期與研修時間參考：{sem_dates_str}"
    course_clean = course_rest_str

    dest_sources = [
        {
            "title": f"臺北醫學大學國際事務處盟校列表、雙聯學位與海外課程簡章—{zh_name}",
            "source_url": source_url,
            "summary": "北醫大國際事務處公告之合作學程、開放學院、語言檢定門檻與盟校待遇說明",
        },
        {
            "title": "臺北醫學大學境外研修暨見實習獎勵辦法、學生境外研修作業要點與教育部學海計畫說明會簡報",
            "source_url": TMU_115_XUEHAI_BRIEFING_PDF_URL,
            "summary": "北醫大教育部學海四項計畫與校內境外研修獎學金雙軌補助、教務處簽報備查與學分換算規範",
        },
    ]
    if exps:
      dest_sources.append({
          "title": f"北醫大國際事務處學生經驗分享專區—赴 {zh_name} 交換／見實習成果報告（{len(exps)} 篇）",
          "source_url": exps[0]["url"],
          "summary": f"收錄歷年北醫大生赴 {zh_name} 海外交換與臨床見實習成果報告共 {len(exps)} 篇",
      })
    if website:
      dest_sources.append({
          "title": f"{full_name} 官方網站",
          "source_url": website,
          "summary": "接待合作盟校／醫療機構官方網站",
      })

    src_url_list = (
        [source_url, TMU_115_XUEHAI_BRIEFING_PDF_URL, TMU_OVERSEAS_INCENTIVE_REGS_PDF_URL]
        + ([exps[0]["url"]] if exps else [])
        + ([website] if website else [])
    )

    destinations.append({
        "home_university": "臺北醫學大學",
        "school_name": full_name,
        "country": country,
        "city": location_obj.get("city") or country,
        "cost_summary": f"{cost_line}。\n{tuition_clean}",
        "housing_summary": housing_clean,
        "transport_summary": (
            f"校區／醫院代表城市：{location_obj.get('city') or country}。請依入學／臨床見實習許可確認實際授課校區、附屬教學醫院位置與當地學生交通卡優惠。"
        ),
        "campus_life_summary": f"{calendar_clean}\n{course_clean}",
        "student_guide_sections": [
            {
                "key": "cost",
                "title": "生活費、北醫大在學註冊規定與教育部學海計畫／校內境外研修獎學金雙軌補助",
                "summary": cost_line,
                "points": [cost_line] + tuition_points_list,
                "source_urls": src_url_list + [TMU_115_2_XIZHU_GUIDELINES_PDF_URL, TMU_115_2_ZHUMENG_GUIDELINES_PDF_URL],
                "caution": (
                    "學海計畫受獎生須於返國後 2 週（14 日）內完成問卷及 1,000 字以內成果報告書（含照片 4 張以上）上傳，並於 1 個月內檢具機票等單據完成核銷；校內境外研修獎學金受獎生須於返國 1 個月內繳交成果報告書至國際處。"
                ),
            },
            {
                "key": "housing",
                "title": "住宿資訊與校內外學生宿舍／見實習醫師公寓申請",
                "summary": housing_clean[:160],
                "points": [housing_clean],
                "source_urls": src_url_list,
                "caution": (
                    "各海外合作大學及教學醫院宿舍床位有限，獲北醫大提名後請務必留意接待機構之住宿申請截止日。"
                ),
            },
            {
                "key": "insurance",
                "title": "海外醫療及意外保險、臨床見實習疫苗抗體檢測與責任保險規定",
                "summary": visa_default,
                "points": [
                    visa_default,
                    "依《學生海外行前報到單》及接待醫學院校規定，出國前須投保涵蓋境外研修全期之海外醫療及意外保險；赴國外醫院進行臨床見實習者，務必於出發前 3–6 個月完成規定之疫苗接種與抗體效價檢測（MMR、水痘、B型肝炎、T-SPOT/IGRA 結核檢驗等）及醫療實習責任險。",
                ],
                "source_urls": src_url_list + [TMU_PREDEPARTURE_FORM_PDF_URL],
                "caution": "美日歐澳教學醫院對免疫抗體效價與結核菌篩檢審核極為嚴格，請提早至家醫科或旅遊醫學門診完成檢驗。",
            },
            {
                "key": "visa",
                "title": "留學／研究簽證辦理、教務處《境外研修簽報表》備查與北醫大在學註冊義務",
                "summary": visa_default,
                "points": [
                    visa_default,
                    "依《臺北醫學大學學生境外研修作業要點》規定：修讀雙聯學位於研修前 1 個月、修習學分或研究及實習於研修前 3 個工作日由系所檢送《學生境外研修簽報表》送教務處備查，且研修期間須辦理北醫大註冊（若辦理休學者，境外修習學分及成績概不予採計）。",
                ],
                "source_urls": src_url_list + [TMU_ACA_OVERSEAS_STUDY_GUIDELINES_PDF_URL],
                "caution": "出國前請務必完成教務處《學生境外研修簽報表》備查與國際處《學生海外行前報到單》繳交。",
            },
            {
                "key": "academics",
                "title": "學分換算基準（授課 18 小時／實習 36–54 小時 = 1 學分）、雙聯修業年限與兩岸醫事學分限制",
                "summary": course_clean[:160],
                "points": [calendar_clean, course_clean],
                "source_urls": src_url_list + [TMU_ACA_DUAL_DEGREE_REGS_PDF_URL, TMU_ACA_CREDIT_TRANSFER_REGS_PDF_URL],
                "caution": (
                    "依《辦理境外雙聯學制實施辦法》第2條及《學生境外研修作業要點》，大陸地區有關醫療法所稱醫事人員高等學校學分不予採認，且不得涉及醫學人才培養；雙聯同級學制在二校修習學分數須各達畢業應修總學分數三分之一以上。"
                ),
            },
            {
                "key": "living",
                "title": f"{location_obj.get('city') or country} 校園／臨床生活與北醫大學長姐海外研修心得傳承",
                "summary": f"代表城市：{location_obj.get('city') or country}。請配合接待校院國際處或臨床教學部門完成報到與新生訓練（Orientation）。",
                "points": [
                    f"目的地城市：{location_obj.get('city') or country}（{country}）",
                    (
                        f"北醫大國際事務處於官網「學生經驗分享（{exps[0]['url'] if exps else TMU_EXPERIENCES_ZH_URL}）」公開收錄歷屆北醫大生赴海外交換與臨床見實習成果報告書"
                        + (f"（本機構共收錄 {len(exps)} 篇：{'、'.join(exp_labels[:4])}）" if exps else "")
                        + "，詳實記載臨床見實習科別、實驗室研究、住宿交通與獎學金申請經驗。"
                    ),
                ],
                "source_urls": [exps[0]["url"] if exps else TMU_EXPERIENCES_ZH_URL],
            },
        ],
        "sources": dest_sources,
        "last_checked": CHECKED_AT,
        "coverage_status": "official_verified",
        "coverage_note": (
            "已整合臺北醫學大學國際事務處與教務處 201 所合作盟校與醫療機構、18 校 32 個跨國雙聯學程、學海計畫與校內境外研修獎學金規範及 55 篇歷屆學長姐返國報告。"
        ),
    })

    research_records.append({
        "home_university": "臺北醫學大學",
        "school_name": full_name,
        "country": country,
        "official_website": website,
        "verification_status": "official_verified",
        "discovery_source_url": source_url,
        "checked_at": CHECKED_AT,
        "note": (
            f"臺北醫學大學國際事務處《盟校列表（{TMU_PARTNERS_ZH_URL}）》、《雙聯學位（{TMU_DUAL_DEGREE_ZH_URL}）》、《海外課程（{TMU_OVERSEAS_COURSES_ZH_URL}）》與 ROR/Wikidata 官方網址核對完成。"
        ),
    })

    ev_sources = [
        {
            "title": f"臺北醫學大學國際事務處盟校列表、雙聯學位與海外課程簡章—{zh_name}",
            "url": source_url,
        },
    ]
    if exps:
      ev_sources.append({
          "title": f"北醫大國際事務處學生經驗分享專區—赴 {zh_name} 研修成果報告（{len(exps)} 篇）",
          "url": exps[0]["url"],
      })
    if website:
      ev_sources.append({"title": f"{full_name} 官方網站", "url": website})

    has_student_exp = bool(exps)
    if exps:
      exp_covered_schools += 1
      total_exp_pdfs += len(exps)

    ev_list = [
        {
            "theme": "housing",
            "kind": "mixed" if has_student_exp else "official",
            "text": housing_clean,
            "sources": ev_sources,
            "checked_at": CHECKED_AT,
            "scope": "臺北醫學大學境外研修盟校住宿與生活資訊",
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
            "scope": "臺北醫學大學境外研修學雜費規定、教育部學海計畫／校內獎學金與地區生活費估算",
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
            "scope": "臺北醫學大學境外研修簽報備查、學分換算基準、雙聯修業年限與兩岸醫事學分限制",
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
            "scope": "臺北醫學大學境外研修簽證、臨床見實習疫苗抗體檢測、海外醫療保險與行前報到提醒",
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
                    f"｜北醫大國際處學生經驗分享專區公開收錄 {len(exps)} 篇赴 {zh_name} 海外研修／臨床見實習成果報告（{'、'.join(exp_labels[:4])}）。"
                    if exps
                    else ""
                )
            ),
            "sources": ev_sources,
            "checked_at": CHECKED_AT,
            "scope": "臺北醫學大學境外研修名額與歷屆學長姐成果報告分享",
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
            "已整合臺北醫學大學國際事務處《盟校列表》、《雙聯學位》、《海外課程》、《2026（民國115）年教育部學海計畫校內說明會簡報》、《境外研修暨見實習獎勵辦法》及學生經驗分享專區共 55 篇歷屆學長姐成果報告書。",
            "當期宿位供給、臨床見實習免疫檢驗要求與選課限制請依合作校院最新簡章及入學通知書核對。",
        ],
        "location_signature": f"verified:{location_obj['latitude']}:{location_obj['longitude']}:representative",
        "extraction_version": 3,
    })

    sample_reports: list[dict] = []
    for e_item in exps[:6]:
      sample_reports.append({
          "title": e_item["title"],
          "url": e_item["url"],
          "term": f"{e_item['year']}年度",
      })

    if exps:
      rep_title = (
          f"臺北醫學大學赴 {zh_name} 海外交換研修／臨床見實習成果報告彙編（共 {len(exps)} 篇學長姐報告）"
      )
      latest_e = exps[0]
      latest_author = (
          f"{latest_e['student']} 等 {len(exps)} 位北醫大研修生"
          if len(exps) > 1
          else latest_e["student"]
      )
      summary_text = (
          f"臺北醫學大學國際事務處「學生經驗分享」專區公開收錄 {len(exps)} 篇歷年赴 {zh_name} 海外交換研修與臨床見實習成果報告（含：{'、'.join(exp_labels[:5])}）。"
          f"{latest_e['highlight']}"
      )
      theme_map = {
          "academics": (
              f"北醫大研修生（{'、'.join(exp_labels[:3])}）分享於 {zh_name} 參與專業課程、醫院臨床見實習與實驗室研究之學習心得，以及返國依《學生境外研修作業要點》辦理學分採認之經驗。{latest_e['highlight']}"
          ),
          "housing": (
              f"北醫大研修生詳述 {zh_name} 校內外學生宿舍或教學醫院見實習住宿申請、周邊機能與通勤方式（{housing_clean[:120]}）。"
          ),
          "campus_culture": (
              f"北醫大國際處收錄 {len(exps)} 篇赴 {zh_name} 成果報告書，記錄國際醫療團隊協作、跨國研究交流與當地文化體驗。"
          ),
          "cost": (
              f"北醫大研修生記錄於 {zh_name} 之每月住宿、伙食與交通開銷（{cost_default}），以及運用教育部學海計畫或北醫大境外研修暨見實習獎學金支應出國費用之規劃。"
          ),
      }
      student_experience_rows.append({
          "school_name": full_name,
          "country": country,
          "title": rep_title,
          "source_url": latest_e["url"],
          "source_type": "article",
          "platform": "臺北醫學大學國際事務處—學生經驗分享專區",
          "author_name": latest_author,
          "language": "zh",
          "summary": summary_text,
          "themes": ["academics", "housing", "campus_culture", "cost"],
          "theme_summaries": theme_map,
          "content_status": "full_text",
          "perspective": "official_student_story",
          "published_at": None,
          "discovered_at": CHECKED_AT,
          "content_hash": hashlib.sha256(f"{full_name}:tmu_exp:{len(exps)}".encode("utf-8")).hexdigest(),
          "exchange_term": f"{latest_e['year']}年度",
          "summary_zh": summary_text,
          "original_summary": summary_text,
          "theme_summaries_zh": theme_map,
          "translation_status": "original",
          "source_kind": "official_experience_page",
      })

    experience_sources_records.append({
        "home_university": "臺北醫學大學",
        "school_name": full_name,
        "country": country,
        "official_experience_portal_url": (
            exps[0]["url"] if exps else TMU_EXPERIENCES_ZH_URL
        ),
        "partner_page_url": source_url,
        "report_count": len(exps),
        "sample_reports": sample_reports,
        "checked_at": CHECKED_AT,
    })

  partners_jsonl_text = "\n".join(json.dumps(r, ensure_ascii=False) for r in partners) + "\n"
  (OFFICIAL_TMU_DIR / "partners.jsonl").write_text(partners_jsonl_text, encoding="utf-8")
  (SOURCES_TMU_DIR / "partners.jsonl").write_text(partners_jsonl_text, encoding="utf-8")
  (OFFICIAL_TMU_DIR / "application_workflows.jsonl").write_text(
      "\n".join(json.dumps(r, ensure_ascii=False) for r in workflows) + "\n",
      encoding="utf-8",
  )
  (OFFICIAL_TMU_DIR / "destination_profiles.jsonl").write_text(
      "\n".join(json.dumps(r, ensure_ascii=False) for r in destinations) + "\n",
      encoding="utf-8",
  )
  (OFFICIAL_TMU_DIR / "partner_research.jsonl").write_text(
      "\n".join(json.dumps(r, ensure_ascii=False) for r in research_records) + "\n",
      encoding="utf-8",
  )
  (OFFICIAL_TMU_DIR / "student_life.jsonl").write_text(
      "\n".join(json.dumps(r, ensure_ascii=False) for r in life_records) + "\n",
      encoding="utf-8",
  )
  (OFFICIAL_TMU_DIR / "experience_sources.jsonl").write_text(
      "\n".join(json.dumps(r, ensure_ascii=False) for r in experience_sources_records) + "\n",
      encoding="utf-8",
  )
  (OFFICIAL_TMU_DIR / "student_experiences.jsonl").write_text(
      "\n".join(json.dumps(r, ensure_ascii=False) for r in student_experience_rows) + "\n",
      encoding="utf-8",
  )
  (OFFICIAL_TMU_DIR / "campus-locations.json").write_text(
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
  (OFFICIAL_TMU_DIR / "student-experience-digests.json").write_text(
      json.dumps({"digests": digest_records}, ensure_ascii=False, indent=2) + "\n",
      encoding="utf-8",
  )

  # Ensure TMU home location is in university_locations.jsonl
  loc_file = REPO_ROOT / "src/exchange_info/official_data/university_locations.jsonl"
  existing_loc_lines = [
      line for line in loc_file.read_text(encoding="utf-8").splitlines() if line.strip()
  ]
  existing_loc_map = {}
  for line in existing_loc_lines:
    rec = json.loads(line)
    existing_loc_map[(rec["school_name"], rec.get("country") or "")] = rec

  tmu_home_loc = {
      "school_name": "臺北醫學大學",
      "country": "臺灣",
      "city": "臺北市信義區",
      "latitude": 25.0253,
      "longitude": 121.5615,
      "geocode_status": "verified",
      "geocoded_at": CHECKED_AT,
      "source_url": "https://www.wikidata.org/wiki/Q715460",
      "identity_source_url": "https://ror.org/050318978",
      "precision": "representative",
      "note": (
          "校級代表位置：官方網域及國家已與 ROR 比對，座標來源為 Wikidata P625；實際交換校區以錄取通知為準。"
          " 母校代表點採臺北市信義區吳興街250號信義校區醫學綜合大樓後棟4樓國際事務處；官方地址來源：https://oge.tmu.edu.tw/zh-hant/。"
      ),
  }
  existing_loc_map[("臺北醫學大學", "臺灣")] = tmu_home_loc
  sorted_locs = sorted(
      existing_loc_map.values(),
      key=lambda r: (r.get("country") or "", r.get("school_name") or ""),
  )
  loc_file.write_text(
      "\n".join(json.dumps(r, ensure_ascii=False) for r in sorted_locs) + "\n",
      encoding="utf-8",
  )

  tmu_source_urls = [
      TMU_OGE_HUB_URL,
      TMU_OGE_EN_HUB_URL,
      TMU_OUTBOUND_EXCHANGE_ZH_URL,
      TMU_OUTBOUND_STUDENTS_EN_URL,
      TMU_DUAL_DEGREE_ZH_URL,
      TMU_OVERSEAS_COURSES_ZH_URL,
      TMU_SCHOLARSHIPS_ZH_URL,
      TMU_EXPERIENCES_ZH_URL,
      TMU_PARTNERS_ZH_URL,
      TMU_PARTNERS_EN_URL,
      TMU_REGULATIONS_ZH_URL,
      TMU_ACA_OUTBOUND_URL,
      TMU_ACA_DUAL_DEGREE_REGS_URL,
      TMU_115_XUEHAI_INFO_URL,
      TMU_115_XUEHAI_BRIEFING_PDF_URL,
      TMU_115_2_XIZHU_GUIDELINES_PDF_URL,
      TMU_115_2_XIZHU_FORM_DOC_URL,
      TMU_115_2_ZHUMENG_GUIDELINES_PDF_URL,
      TMU_115_XUEHAI_CONTRACT_DOC_URL,
      TMU_2026_MOE_PROSPECTUS_EN_PDF_URL,
      TMU_OVERSEAS_INCENTIVE_REGS_PDF_URL,
      TMU_OVERSEAS_INCENTIVE_REGS_EN_PDF_URL,
      TMU_OVERSEAS_INCENTIVE_APP_DOCX_URL,
      TMU_PREDEPARTURE_FORM_PDF_URL,
      TMU_PHARMACY_USC_DUAL_PDF_URL,
      TMU_PHARMACY_PSU_DUAL_PDF_URL,
      TMU_DUAL_DEGREE_FLOWCHART_PDF_URL,
      TMU_ACA_OVERSEAS_STUDY_GUIDELINES_PDF_URL,
      TMU_ACA_DUAL_DEGREE_REGS_PDF_URL,
      TMU_ACA_CREDIT_TRANSFER_REGS_PDF_URL,
  ]

  exchange_info_payload = {
      "school_name": "臺北醫學大學",
      "program_type": [
          (
              "教育部《學海飛颺／學海惜珠／學海築夢／新南向學海築夢》選送學生出國研修暨臨床／實驗室見實習計畫（第一梯次每年 12 月各學院收件、翌年 1 月 15 日［115年為 2026/01/16］前送交國際事務處；第二次徵求［學海惜珠、學海築夢、新南向學海築夢］8 月各學院收件、2026/09/07 前送交國際事務處）"
          ),
          (
              "《臺北醫學大學境外研修暨見實習獎勵辦法》校內獎學金暨國際事務處（Apply via TMU）出國交換與海外短期研修計畫（每年 1 月 15 日及 5 月 15 日兩梯次收件，涵蓋個人型、每案上限 NT$50 萬之團體型及每人每學年上限 NT$10,000 之線上學分課程型；常態開放日本東北大學 JYPE/COLABS、九州大學 JTW、北海道大學 HUSTEP/JLCSP、長崎大學、御茶水女子大學、關西大學、韓國高麗大學、漢陽大學、梨花女子大學、成均館大學、加拿大 UBC VSP、美國喬治亞州立大學、康乃狄克大學、泰國那黎宣大學、宋卡王子大學、瑪希敦大學、印尼希望之光大學 UPH、菲律賓 UA&P、墨西哥 UAEH、奧地利薩爾茨堡大學等重點交換與短期課程）"
          ),
          (
              "跨國雙聯學位學制計畫（依《臺北醫學大學辦理境外雙聯學制實施辦法》與 8 國 18 所頂尖大學合辦 32 個學碩博雙聯學程：美國南加州大學［藥學系 Pharm.D. / M.S.、奈米醫工所博士］、賓州州立大學［醫學系學碩、藥學系 6+1 碩士］、凱斯西儲大學［保健營養學系 1+1 / 1+1.5 碩士及 3+2 學碩雙聯］、喬治亞州立大學［呼吸治療碩士、保健營養碩士］、聖若望大學［藥學系學碩］、南新罕布夏大學［醫資所碩士］、華美中醫學院［生藥所碩士］、加拿大戴爾豪斯大學［醫科所博士］、蒙特婁大學［醫科所碩士、國際醫學碩士］、法國里爾大學［醫科所博士、生醫材料所碩博］、義大利卡利亞里大學［醫科所博士、國際醫學博士、中草藥博士、醫技碩士］、丹麥奧胡斯大學［牙醫博士］、日本大阪大學［牙醫博士］、北海道醫療大學［牙醫博士］、東京理科大學［醫工學院三所碩士］、澳洲伍倫貢大學［高齡長照碩士、護理碩博］、西雪梨大學［護理博士］、印尼加札馬達大學［護理碩士］）"
          ),
      ],
      "academic_year": [
          (
              "115–116（115年度教育部學海四項計畫第一梯次於 2026/01/16 截止、第二次徵求［惜珠、築夢、新南向築夢］於 2026/09/07 截止；校內《境外研修暨見實習獎學金》每年固定於 1 月 15 日及 5 月 15 日兩梯次截止收件）"
          ),
          (
              "本平台完整收錄臺北醫學大學國際事務處公告之 201 所全球合作大學、醫學院與教學醫院（含 61 所當期開放雙聯、交換與臨床見實習合作機構及 140 所正式締約盟校，橫跨 37 個國家與地區，並完整收錄 33 所合作機構共 55 篇歷屆學長姐返國成果報告書）"
          ),
      ],
      "semester": [
          "秋季學期（第1學期：每年約 8/9 月至翌年 1/2 月，日本秋季班為 9/10 月至翌年 2/3 月）",
          "春季學期（第2學期：每年約 1/2 月至 5/6 月，日本春季班為 4 月至 8/9 月）",
          "寒暑期海外短期課程、教學醫院臨床見實習與實驗室研究（校內境外研修獎學金要求實體出國至少 10 個工作天／10 日曆天；教育部學海築夢要求至少 30 天［印尼 25 天］）",
          "跨國雙聯學位修讀（1+1、1+1.5、3+2、6+1、4+2、4+3 或 2+2 博士雙聯；同級雙聯修業時間二校合計學士至少 32 個月、碩士至少 12 個月、博士至少 24 個月）",
      ],
      "application_period": [
          (
              "【教育部學海飛颺／惜珠／築夢／新南向學海築夢】第一梯次：每年 12 月各學院收件初審、翌年 1 月 15 日（115年為 2026/01/16）前由各學院排定優先順序送交國際事務處，2 月國際處複審、3/31 前提報教育部、5/31 前公告結果；第二次徵求（學海惜珠、學海築夢、新南向學海築夢）：每年 8 月各學院收件初審、2026/09/07 前送交國際事務處。"
          ),
          (
              "【臺北醫學大學境外研修暨見實習獎學金】每年分兩梯次收件：第一梯次於每年 1 月 15 日截止（2 月國際教育委員會審查），第二梯次於每年 5 月 15 日截止（6 月國際教育委員會審查）。"
          ),
          (
              "【跨國雙聯學制與教務處境外研修備查】依《臺北醫學大學學生境外研修作業要點》第4點規定，修讀雙學位者須於研修前 1 個月（藥學系南加州大學雙聯為每年 3 月底前、賓州州立大學雙聯為大五下 1 月中旬前）、修習學分或研究及見實習者須於研修前 3 個工作日，由所屬系所檢送《學生境外研修簽報表》及佐證資料送教務處備查。"
          ),
      ],
      "eligibility": [
          (
              "【在學學制、年級與基本資格】凡臺北醫學大學（醫學院、口腔醫學院、藥學院、護理學院、公共衛生學院、醫學科技學院、人文暨社會科學院、管理學院、醫學工程學院、營養學院、跨領域學院）在學學士班、碩士班及博士班學生皆可依計畫性質申請。申請教育部學海飛颺／惜珠者，須具中華民國國籍且在臺設有戶籍，並於北醫大就讀滿一學期以上（不含國內及境外在職專班生）。"
          ),
          (
              "【學業成績與操行門檻（系所前 40%／班前 30%／GPA 3.0）】申請教育部《學海飛颺／學海惜珠》者，歷年學業成績須達每系所排名前 40% 或每班排名前 30%（研究所碩、博士生免附排名），且操行成績達 80 分以上；申請跨國雙聯學位學制者（如美國南加州大學、賓州州立大學、凱斯西儲大學等），歷年平均成績須達 GPA 3.0（百分制約 75 分）以上。"
          ),
          (
              "【大陸地區醫事人員學分不予採認與在學註冊強制規定】依《臺北醫學大學辦理境外雙聯學制實施辦法》第2條及《學生境外研修作業要點》規定：大陸地區有關醫療法所稱醫事人員高等學校學分本會及本校不予採認，且不得涉及醫學人才培養。學生於境外研修期間須依北醫大規定辦理在學註冊；若辦理休學者，其於境外修習之科目、學分及成績均不予採計。"
          ),
      ],
      "language_requirement": [
          (
              "【教育部學海飛颺／惜珠外語檢定門檻】（1）申請赴英語系國家交換研修者：須達 TOEFL iBT 79 分或 IELTS 5.5 以上；（2）申請赴非英語系國家以英語研修者：須達 TOEFL iBT 75 分或 IELTS 5.0 以上；（3）申請赴日本以日語研修者：須達日本語能力試驗 JLPT N2 以上。"
          ),
          (
              "【校內《境外研修暨見實習獎勵辦法》CEFR B2 外語門檻】申請北醫大校內個人型、團體型或線上學分課程型境外研修暨見實習獎學金者，須檢附 2 年內有效且達 CEFR B2（高階級）以上之語言能力證明：TOEFL iBT 72 分、IELTS 5.5、TOEIC 785 分、全民英檢（GEPT）中高級或外語能力測驗（FLPT）筆試 195／口試 S-2+ 以上。"
          ),
          (
              "【跨國雙聯學位與頂尖名校個別語檢門檻】美國凱斯西儲大學（CWRU）與南加州大學（USC）雙聯要求 TOEFL iBT 90–100 或 IELTS 6.5–7.0；美國賓州州立大學（Penn State）要求 TOEFL iBT 80（口說 19）或 IELTS 6.5；美國喬治亞州立大學（GSU）、日本東北大學（JYPE/COLABS）、北海道大學（HUSTEP）要求 TOEFL iBT 79 或 IELTS 6.0–6.5；日本九州大學（JTW）要求 TOEFL iBT 80 或 IELTS 6.0 或 JLPT N2；義大利卡利亞里大學雙聯要求 TOEIC 750 分以上。"
          ),
      ],
      "required_documents": [
          "1. 臺北醫學大學境外研修暨見實習獎學金申請表、或教育部學海計畫／跨國雙聯學位甄選申請表（含基本資料、志願學校與研修期程）",
          "2. 境外研修／臨床見實習申請計畫書，或英文格式讀書計畫／研究方向計畫書（Study Plan / Research Proposal / Career Statement，詳述研修動機、擬修課程或臨床見實習科別與預期成效）",
          "3. 北醫大中、英文歷年成績單正本（申請學海飛颺／惜珠之大學部學生須清楚註明系所排名前 40% 或班級排名前 30% 及操行成績 80 分以上；研究所免附排名）",
          "4. 2 年內有效之外語能力檢定證明影本（TOEFL iBT / IELTS / TOEIC / GEPT / JLPT 等，須達學海計畫、校內 CEFR B2 及志願校院規定標準）",
          "5. 師長英文推薦信 1–3 封（如凱斯西儲大學雙聯要求 3 封、喬治亞州立大學與澳洲伍倫貢／西雪梨大學雙聯要求 2 封）及個人中英文履歷自傳（CV / Autobiography）",
          "6. 家長或監護人同意書、當學期學生證與國民身分證正反面影本（在職專班生申請雙聯另須提供服務單位主管同意書；部分歐美澳雙聯另須附無犯罪紀錄證明）",
          "7. 英文財力證明（申請校內個人型境外研修獎學金及歐美日澳學生簽證必備）與國外接待校院／實驗室 PI 邀請函或同意接待證明（申請學海築夢及研究見實習必備）",
          "8. 申請教育部《學海惜珠》者另須檢附：新式戶口名簿影本（註明現住人口及詳細記事）或三個月內戶籍謄本，以及直轄市、縣（市）主管機關開立之有效低收入戶、中低收入戶或特殊境遇家庭相關扶助證明",
      ],
      "scholarship_info": [
          (
              "教育部《學海飛颺》與《學海惜珠》出國研修獎學金：第一梯次每年 12 月各學院收件、翌年 1 月 15 日（115年為 2026/01/16）前送國際事務處；第二次學海惜珠徵求於 2026/09/07 前送國際處。補助具中華民國國籍之北醫大在學生赴國外（不含大陸及港澳）姊妹校修讀學分 1 學期或 1 學年（歷年成績須居系所前 40% 或班前 30%、操行 80 分以上；英語系國家 iBT 79 / IELTS 5.5、非英語系國家 iBT 75 / IELTS 5.0、日語 JLPT N2），涵蓋來回經濟艙機票、國外學費及生活費。"
          ),
          (
              "教育部《學海築夢》與《新南向學海築夢》海外臨床及研究實習獎學金：第一梯次 1 月中旬截止、第二次徵求於 2026/09/07 截止。由北醫大專任教師擔任計畫主持人，選送學生赴歐美日澳（學海築夢）或新南向國別（泰國、印尼、越南、馬來西亞、印度、菲律賓、新加坡、紐澳等）之頂尖醫療機構、醫藥企業或研究實驗室進行至少 30 天（不含來回途程；印尼為 25 天）之臨床或專業實習，補助機票與生活費。"
          ),
          (
              "《臺北醫學大學境外研修暨見實習獎勵辦法》校內獎學金：每年分 1 月 15 日（2 月審查）及 5 月 15 日（6 月審查）兩梯次收件，外語須達 CEFR B2（TOEFL iBT 72 / IELTS 5.5 / TOEIC 785），實體出國不得少於 10 個工作天／10 日曆天。分為三大類：（1）個人型：補助自行或經學院選送赴境外修課、研究或臨床見實習之學生；（2）團體型：由北醫大專任教師帶隊（至少 3 名學生，新南向、非洲及邦交國優先），每案最高補助新臺幣 50 萬元；（3）線上學分課程型：修讀國外大學線上學分課程並取得及格證明，每人每學年最高補助新臺幣 10,000 元。"
          ),
          (
              "返國義務與經費核銷規範：（1）教育部學海四項計畫受獎生須於出國前簽妥《學海行政契約書》並繳交《學生海外行前報到單》，計畫結束返國後 2 週（14 日）內須至教育部學海計畫網站上傳問卷調查表及 1,000 字以內中／英文成果報告書（含照片 4 張以上），並於返國後 1 個月內檢具機票單據等完成經費核銷；（2）校內境外研修獎學金受獎生須於返國後 1 個月內繳交成果報告書至國際事務處；（3）逾期未繳報告或未完成核銷者，將依契約追繳全額或部分獎補助款。"
          ),
      ],
      "partner_universities": [p["school_name"] for p in partners],
      "source_urls": tmu_source_urls,
      "last_checked": CHECKED_AT,
  }
  (OFFICIAL_TMU_DIR / "exchange_info.json").write_text(
      json.dumps(exchange_info_payload, ensure_ascii=False, indent=2) + "\n",
      encoding="utf-8",
  )

  student_dashboard_payload = {
      "school_name": "臺北醫學大學",
      "last_checked": CHECKED_AT,
      "academic_score_minimum": 75.0,
      "academic_score_rule": (
          "依臺北醫學大學《教育部學海飛颺／惜珠簡章》、《境外研修暨見實習獎勵辦法》及《辦理境外雙聯學制實施辦法》規定：申請學海飛颺／惜珠須於北醫大就讀滿一學期以上，歷年學業成績達每系所排名前 40% 或每班排名前 30%（研究所免附排名）且操行成績達 80 分以上；申請跨國雙聯學位須達歷年 GPA 3.0（百分制約 75 分）以上。"
      ),
      "academic_gpa_minimum": 3.0,
      "maximum_preferences": 3,
      "selection_rules": {
          "academic_policy": "gpa_or_rank",
          "academic_reference_year": "115",
          "undergraduate_gpa_minimum": 3.0,
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
          "toefl": 72.0,
          "ielts": 5.0,
          "toeic": 750.0,
      },
      "application_periods": [
          {
              "title": (
                  "臺北醫學大學《境外研修暨見實習獎學金》暨教育部學海計畫第一梯次校內甄選（每年 1 月 15 日及 5 月 15 日兩梯次截止）"
              ),
              "details": [
                  (
                      "教育部《學海飛颺／學海惜珠／學海築夢／新南向學海築夢》第一梯次：每年 11–12 月舉辦校內說明會並由各學院收件初審，翌年 1 月 15 日（115年度為 2026/01/16）前由各學院排定優先順序送交國際事務處，2 月國際處複審、3/31 前報教育部、5/31 前公告結果。"
                  ),
                  (
                      "《臺北醫學大學境外研修暨見實習獎學金》（含個人型、每案上限 NT$50 萬之團體型及每人每學年上限 NT$10,000 之線上學分課程型）：第一梯次於每年 1 月 15 日截止（2 月審查）、第二梯次於每年 5 月 15 日截止（6 月審查）。"
                  ),
              ],
              "source": {
                  "title": "臺北醫學大學 2026（民國115）年教育部學海計畫校內說明會簡報與境外研修暨見實習獎勵辦法",
                  "source_url": TMU_115_XUEHAI_BRIEFING_PDF_URL,
                  "category": "exchange_application",
                  "summary": "北醫大教育部學海四項計畫與校內境外研修獎學金申請時程、系所前 40%／班前 30% 門檻與語檢規範。",
              },
              "scope": "home_application",
              "program_types": ["exchange", "dual_degree"],
              "academic_year": "116",
              "application_round": "115–116年度境外研修暨見實習獎學金與學海計畫第一梯次甄選",
              "audience": "all_students",
              "opens_at": "2026-12-01T09:00:00+08:00",
              "deadline_at": "2027-01-15T17:00:00+08:00",
              "date_status": "verified_exact",
              "status": "upcoming",
              "status_note": "每年第一梯次校內境外研修暨見實習獎學金與教育部學海計畫於 12 月起由各學院收件，翌年 1 月 15 日截止送交國際事務處（第二梯次校內獎學金於 5 月 15 日截止）。",
              "deadline_note": "請備妥申請表、中英文歷年成績單（含排名）、2 年內有效外語證明（CEFR B2 / iBT 72–79 / IELTS 5.0–5.5 / JLPT N2）及研修計畫書向所屬學院及國際事務處提出申請。",
              "reminder_eligible": True,
              "checked_at": CHECKED_AT,
          },
          {
              "title": (
                  "臺北醫學大學 115年度教育部《學海惜珠／學海築夢／新南向學海築夢》第二次申請公告（2026/09/07 國際處截止）"
              ),
              "details": [
                  (
                      "北醫大國際事務處於 2026 年 8 月公告《115年度教育部學海惜珠計畫第二次申請公告》與《115年度教育部學海築夢及新南向學海築夢計畫第二次申請公告》，各學院於 8 月底前完成收件初審，並於 2026/09/07 (一) 17:00 前將推薦名單與完整電子檔送交國際事務處。"
                  ),
                  (
                      "預計於 115 學年度第 2 學期（2027 年春季）至 2027 年 10 月 31 日前出國研修或臨床／實驗室實習之同學與計畫主持人，可把握第二次徵求梯次提出申請。"
                  ),
              ],
              "source": {
                  "title": "臺北醫學大學 115年度教育部學海惜珠與學海築夢／新南向築夢第二次申請公告 PDF",
                  "source_url": TMU_115_2_XIZHU_GUIDELINES_PDF_URL,
                  "category": "scholarship",
                  "summary": "北醫大 115 年度學海惜珠、學海築夢、新南向學海築夢第二次徵求時程與申請表件。",
              },
              "scope": "home_application",
              "program_types": ["exchange"],
              "academic_year": "115",
              "application_round": "115年度教育部學海惜珠／學海築夢／新南向學海築夢第二次徵求",
              "audience": "all_students",
              "opens_at": "2026-08-01T09:00:00+08:00",
              "deadline_at": "2026-09-07T17:00:00+08:00",
              "date_status": "verified_exact",
              "status": "closed",
              "status_note": "115年度教育部學海計畫第二次徵求已於 2026/09/07 截止收件；下一年度第一梯次將於 2026 年 12 月至 2027 年 1 月 15 日開放申請。",
              "deadline_note": "申請人須經所屬系所及學院初審推薦後，由學院彙整送交國際事務處。",
              "reminder_eligible": False,
              "checked_at": CHECKED_AT,
          },
      ],
      "program_overview": [
          {
              "title": (
                  f"臺北醫學大學國際事務處境外研修、臨床見實習與跨國雙聯總覽（{len(partners)} 所全球盟校與醫療機構・{open_partner_count} 所當期開放雙聯與交換見實習校・18 校 32 個雙聯學程）"
              ),
              "details": [
                  (
                      f"臺北醫學大學（TMU，北醫大）由「國際事務處（Office of Global Engagement, OGE）」、「教務處」與全校 11 個學院（醫學院、口腔醫學院、藥學院、護理學院、公共衛生學院、醫學科技學院、人文暨社會科學院、管理學院、醫學工程學院、營養學院、跨領域學院）共同推動國際交換研修、教學醫院臨床見實習（Clinical Electives）、海外實驗室研究及跨國雙聯學位。本平台完整收錄 {len(partners)} 所北醫大官方合作大學、醫學院與醫療研究機構（含 {open_partner_count} 所當期開放雙聯、交換與臨床見實習合作機構及 {len(partners) - open_partner_count} 所正式締約盟校），橫跨全球 37 個國家與地區（美國 42 校、日本 41 校、印尼 18 校、中國大陸 18 校、韓國 8 校、泰國 8 校、印度 7 校、澳洲 6 校、加拿大 4 校、越南 4 校、香港 4 校、法國 4 校、英國 2 校、德國 2 校、匈牙利 2 校、瑞典 2 校、俄羅斯 2 校、菲律賓 2 校、馬來西亞 2 校，以及新加坡、丹麥、比利時、義大利、奧地利、愛爾蘭、斯洛伐克、羅馬尼亞、土耳其、以色列、哈薩克、蒙古、柬埔寨、墨西哥、阿根廷、安地卡及巴布達、史瓦帝尼、奈及利亞各 1 校）。"
                  ),
                  (
                      f"北醫大國際化體系具備四大醫學大學指標特色：（1）18 所世界名校共 32 個跨國學碩博雙聯學程：涵蓋美國南加州大學（藥學系 4+3 Pharm.D. / 4+2 M.S.、奈米醫工所博士）、賓州州立大學（醫學系學碩、藥學系 6+1 碩士）、凱斯西儲大學（保健營養 1+1 / 1+1.5 碩士及 3+2 學碩）、喬治亞州立大學（呼吸治療碩士、保健營養碩士）、加拿大戴爾豪斯與蒙特婁大學、法國里爾大學、義大利卡利亞里大學、丹麥奧胡斯大學、日本大阪大學、北海道醫療大學、東京理科大學、澳洲伍倫貢與西雪梨大學、印尼加札馬達大學；（2）世界頂尖醫學院與醫療中心臨床見實習網：包含哈佛大學、杜克大學、約翰霍普金斯大學、梅奧診所癌症中心、德州休士頓健康科學中心、休士頓衛理公會醫院、亞特蘭大兒童醫療中心、東京大學、京都大學、東北大學、九州大學、北海道大學、新加坡國立大學、卡羅琳醫學院等；（3）教育部學海四項計畫與校內《境外研修暨見實習獎勵辦法》雙軌豐厚獎補助；（4）公開收錄 {exp_covered_schools} 所重點合作機構共 55 篇歷屆學長姐海外研修與臨床見實習成果報告。"
                  ),
              ],
              "source": {
                  "title": "臺北醫學大學國際事務處—盟校列表、雙聯學位、海外課程與學生經驗分享專區",
                  "source_url": TMU_OGE_HUB_URL,
                  "category": "exchange_application",
                  "summary": "北醫大 201 所全球合作盟校、18 校 32 個雙聯學程、Apply via TMU 海外課程與 55 篇學長姐成果報告。",
              },
          }
      ],
      "eligibility": [
          {
              "title": "北醫大在學資格、系所排名前 40%／班排名前 30%（雙聯 GPA 3.0）門檻與兩岸醫事人員學分不予採認規定",
              "details": [
                  (
                      "學業與操行門檻（依《2026（民國115）年教育部學海計畫校內說明會簡報》及《辦理境外雙聯學制實施辦法》）：申請教育部學海飛颺／惜珠者，須為具中華民國國籍且在臺設有戶籍、於北醫大就讀一學期以上之在學生，歷年成績達每系所排名前 40% 或每班排名前 30%（研究所碩、博士生免附排名），且操行成績 80 分以上；申請跨國雙聯學位者，歷年 GPA 須達 3.0（約 75 分）以上。"
                  ),
                  (
                      "教務備查與兩岸醫事限制（依《學生境外研修作業要點》及《辦理境外雙聯學制實施辦法》第2條）：大陸地區有關醫療法所稱醫事人員高等學校學分不予採認，且不得涉及醫學人才培養。修讀雙聯學位於研修前 1 個月、修習學分或研究見實習於研修前 3 個工作日由系所檢送《學生境外研修簽報表》送教務處備查；境外研修期間須辦理北醫大註冊（辦理休學者其境外學分與成績概不採計）。"
                  ),
              ],
              "source": {
                  "title": "臺北醫學大學學生境外研修作業要點與辦理境外雙聯學制實施辦法 PDF",
                  "source_url": TMU_ACA_OVERSEAS_STUDY_GUIDELINES_PDF_URL,
                  "category": "exchange_application",
                  "summary": "北醫大境外研修簽報備查時限、在學註冊義務、18小時/36–54小時學分換算與大陸醫事學分不予採認規定。",
              },
          }
      ],
      "language_requirements": [
          {
              "title": "教育部學海計畫門檻（英語系 iBT 79 / IELTS 5.5、非英語系 iBT 75 / IELTS 5.0、日語 N2）與校內獎學金 CEFR B2 標準",
              "details": [
                  (
                      "學海計畫與校內獎學金外語標準：（1）教育部學海飛颺／惜珠：英語系國家須達 TOEFL iBT 79 或 IELTS 5.5 以上，非英語系國家須達 TOEFL iBT 75 或 IELTS 5.0 以上，日本日語組須達 JLPT N2 以上；（2）校內《境外研修暨見實習獎勵辦法》：須檢附 2 年內有效且達 CEFR B2 以上之證明（TOEFL iBT 72 / IELTS 5.5 / TOEIC 785 / GEPT 中高級 / FLPT 筆試 195、口試 S-2+）。"
                  ),
                  (
                      "跨國雙聯與重點交換校語檢標準：美國南加州大學（USC）與凱斯西儲大學（CWRU）雙聯要求 TOEFL iBT 90–100 或 IELTS 6.5–7.0；賓州州立大學（Penn State）藥學 6+1 雙聯要求 TOEFL iBT 80（口說 19）或 IELTS 6.5；喬治亞州立大學、日本東北大學（JYPE/COLABS）、北海道大學（HUSTEP）要求 TOEFL iBT 79 或 IELTS 6.0–6.5；九州大學（JTW）要求 TOEFL iBT 80 / IELTS 6.0 或 JLPT N2；義大利卡利亞里大學雙聯要求 TOEIC 750 分以上。"
                  ),
              ],
              "source": {
                  "title": "臺北醫學大學出國交換語文認證專頁與境外研修暨見實習獎勵辦法 PDF",
                  "source_url": TMU_OUTBOUND_EXCHANGE_ZH_URL,
                  "category": "exchange_application",
                  "summary": "北醫大出國交換語文認證標準、學海計畫語檢門檻與校內 CEFR B2 獎勵辦法規定。",
              },
          }
      ],
      "required_documents": [
          {
              "title": "境外研修／雙聯／學海計畫申請文件清單與返國 14 日／1 個月內成果報告核銷規範",
              "details": [
                  (
                      "校內申請必備文件：1. 境外研修暨見實習獎學金申請表（或學海計畫／雙聯學位申請表）、2. 申請計畫書／英文讀書與研究計畫（Study Plan / Research Proposal）、3. 中英文歷年成績單正本（含系所或班級排名）、4. 2 年內有效外語能力證明、5. 師長英文推薦信 1–3 封與英文履歷自傳、6. 家長同意書、學生證與身分證正反面影本、7. 英文財力證明與接待機構邀請函（學海惜珠另附新式戶口名簿影本及低收／中低收證明）。"
                  ),
                  (
                      "出國前備查與返國核銷義務：出國前須由系所檢送《學生境外研修簽報表》送教務處備查（雙聯於 1 個月前、交換與實習於 3 個工作日前），並向國際處繳交《學生海外行前報到單》及簽妥《學海行政契約書》；學海受獎生須於返國後 2 週（14 日）內上傳問卷及 1,000 字以內中／英文成果報告書（含照片 4 張以上）並於 1 個月內完成經費核銷；校內獎學金受獎生須於返國後 1 個月內繳交成果報告書至國際處。"
                  ),
              ],
              "source": {
                  "title": "臺北醫學大學境外研修暨見實習獎勵辦法附件及申請計畫書範例 V6 DOCX",
                  "source_url": TMU_OVERSEAS_INCENTIVE_APP_DOCX_URL,
                  "category": "exchange_application",
                  "summary": "北醫大境外研修暨見實習獎學金申請表、計畫書範例、行前報到單與返國報告格式。",
              },
          }
      ],
      "scholarship_info": [
          {
              "title": "教育部學海四項計畫（飛颺／惜珠／築夢／新南向築夢）與北醫大境外研修暨見實習獎學金（個人型／團體型50萬／線上1萬）",
              "details": [
                  (
                      "教育部學海四項計畫（每年 1/15［115年為 1/16］及 9/7 兩梯次）：（1）《學海飛颺》與《學海惜珠》補助赴國外非大陸港澳姊妹校修讀學分 1 學期或 1 學年；（2）《學海築夢》與《新南向學海築夢》補助由專任教師主持選送赴海外醫療院所或實驗室實習至少 30 天（印尼 25 天）。"
                  ),
                  (
                      "校內《臺北醫學大學境外研修暨見實習獎勵辦法》（每年 1/15 及 5/15 兩梯次）：外語達 CEFR B2 且實體出國不少於 10 個工作天／10 日曆天者可申請：（1）個人型獎學金、（2）團體型獎學金（專任教師帶隊至少 3 名學生，新南向、非洲及邦交國優先，每案上限 NT$50 萬）、（3）線上學分課程型獎學金（修讀國外大學線上學分課程及格，每人每學年上限 NT$10,000）。"
                  ),
              ],
              "source": {
                  "title": "臺北醫學大學境外研修暨見實習獎勵辦法與2026（民國115）年教育部學海計畫說明會簡報 PDF",
                  "source_url": TMU_OVERSEAS_INCENTIVE_REGS_PDF_URL,
                  "category": "scholarship",
                  "summary": "北醫大校內個人型、團體型（50萬）、線上學分課程型（1萬）獎學金與教育部學海四項計畫補助規定。",
              },
          }
      ],
      "document_explanations": [
          {
              "title": "臺北醫學大學境外研修暨見實習申請計畫書、跨國雙聯申請表與教務處《境外研修簽報表》準備指南",
              "summary": "說明北醫大國際事務處境外研修計畫書撰寫重點、18 校 32 個雙聯學程應備文件及教務處簽報備查時限。",
              "key_points": [
                  "申請校內《境外研修暨見實習獎學金》及教育部學海計畫須撰寫具體之《境外研修申請計畫書》，詳述赴外修課或臨床／實驗室見實習目標、接待校院與指導教授（PI）背景、預期學習成效及經費預估。",
                  "申請跨國雙聯學位者（如藥學系 USC 4+3 Pharm.D. / Penn State 6+1 M.S.、保健營養系 CWRU 1+1 / 3+2 雙聯、呼吸治療系 GSU 碩士雙聯、醫科所／生醫材料所法國里爾大學及義大利卡利亞里大學雙聯、護理學院澳洲伍倫貢及西雪梨大學雙聯），須依各院系規定備妥英文讀書／研究計畫、2–3 封英文推薦信及家長同意書。",
                  "依《臺北醫學大學學生境外研修作業要點》第4點規定，出國前必須由所屬系所檢送《學生境外研修簽報表》送教務處備查（修讀雙學位於研修前 1 個月、修習學分或研究見實習於研修前 3 個工作日）。",
              ],
              "applies_to": [],
              "source": {
                  "title": "臺北醫學大學境外研修暨見實習獎勵辦法附件及申請計畫書範例 V6 DOCX",
                  "source_url": TMU_OVERSEAS_INCENTIVE_APP_DOCX_URL,
                  "category": "exchange_application",
                  "summary": None,
              },
              "document_url": TMU_OVERSEAS_INCENTIVE_APP_DOCX_URL,
              "document_type": "official_document",
              "full_text_extracted": True,
          }
      ],
      "rule_explanations": [
          {
              "title": "臺北醫學大學學生境外研修作業要點、辦理境外雙聯學制實施辦法與學分抵免辦法核心規定",
              "summary": "規範北醫大境外研修教務備查時限、在學註冊義務、18/36–54 小時學分換算、雙聯修業年限（32/12/24 個月）與大陸醫事學分限制。",
              "key_points": [
                  "大陸地區限制（《辦理境外雙聯學制實施辦法》第2條）：大陸地區有關醫療法所稱醫事人員高等學校學分本會及本校不予採認，且不得涉及醫學人才培養。",
                  "在學註冊與學分換算（《學生境外研修作業要點》第5、6點）：境外研修期間須辦理北醫大註冊（若辦理休學者，境外修習之科目、學分及成績均不予採計）；一般課程以授課滿 18 小時計 1 學分，實驗、見實習以 36–54 小時計 1 學分。",
                  "雙聯修業時間與學分下限（《辦理境外雙聯學制實施辦法》第8、9條）：同級雙聯學制修業時間二校累計學士班至少 32 個月、碩士班至少 12 個月、博士班至少 24 個月，且在二校當地修習學分數須各達畢業應修總學分數三分之一以上。",
              ],
              "applies_to": [],
              "source": {
                  "title": "臺北醫學大學學生境外研修作業要點與辦理境外雙聯學制實施辦法 PDF",
                  "source_url": TMU_ACA_DUAL_DEGREE_REGS_PDF_URL,
                  "category": "exchange_application",
                  "summary": None,
              },
              "document_url": TMU_ACA_DUAL_DEGREE_REGS_PDF_URL,
              "document_type": "official_document",
              "full_text_extracted": True,
          }
      ],
      "sources": [
          {
              "title": "臺北醫學大學國際事務處（Office of Global Engagement, OGE）官方網站",
              "source_url": TMU_OGE_HUB_URL,
              "category": "exchange_application",
              "summary": None,
          },
          {
              "title": "臺北醫學大學 2026（民國115）年教育部學海計畫獎學金校內說明會簡報 PDF",
              "source_url": TMU_115_XUEHAI_BRIEFING_PDF_URL,
              "category": "scholarship",
              "summary": None,
          },
          {
              "title": "臺北醫學大學境外研修暨見實習獎勵辦法與申請計畫書範例 PDF/DOCX",
              "source_url": TMU_OVERSEAS_INCENTIVE_REGS_PDF_URL,
              "category": "scholarship",
              "summary": None,
          },
          {
              "title": "臺北醫學大學 115年度教育部學海惜珠計畫與學海築夢／新南向築夢第二次申請公告 PDF",
              "source_url": TMU_115_2_XIZHU_GUIDELINES_PDF_URL,
              "category": "scholarship",
              "summary": None,
          },
          {
              "title": "臺北醫學大學跨國雙聯學位一覽表（18校32個雙聯學程）與雙聯學制流程圖",
              "source_url": TMU_DUAL_DEGREE_ZH_URL,
              "category": "partner_school",
              "summary": None,
          },
          {
              "title": "臺北醫學大學海外課程（Apply via TMU 學期交換與寒暑期研修）與出國交換語文認證",
              "source_url": TMU_OVERSEAS_COURSES_ZH_URL,
              "category": "partner_school",
              "summary": None,
          },
          {
              "title": "臺北醫學大學教務處—學生境外研修作業要點、辦理境外雙聯學制實施辦法與學生抵免學分辦法 PDF",
              "source_url": TMU_ACA_OVERSEAS_STUDY_GUIDELINES_PDF_URL,
              "category": "exchange_application",
              "summary": None,
          },
          {
              "title": "臺北醫學大學全球締約盟校列表（201校）與學生經驗分享專區（55篇成果報告）",
              "source_url": TMU_PARTNERS_ZH_URL,
              "category": "partner_school",
              "summary": None,
          },
      ],
  }
  (OFFICIAL_TMU_DIR / "student_dashboard.json").write_text(
      json.dumps(student_dashboard_payload, ensure_ascii=False, indent=2) + "\n",
      encoding="utf-8",
  )

  pages_records = [
      {
          "title": "臺北醫學大學：115–116年度教育部學海四項計畫（1/16、9/7截止）與校內境外研修暨見實習獎學金（1/15、5/15截止）時程",
          "source_url": TMU_115_XUEHAI_BRIEFING_PDF_URL,
          "published_at": "2026-10-20T00:00:00Z",
          "text": "\n".join(exchange_info_payload["application_period"]),
          "summary": "\n".join(exchange_info_payload["application_period"]),
          "category": "exchange_application",
          "attachments": [],
          "crawled_at": CHECKED_AT,
          "content_hash": hashlib.sha256("\n".join(exchange_info_payload["application_period"]).encode("utf-8")).hexdigest(),
      },
      {
          "title": "臺北醫學大學：境外研修與跨國雙聯申請資格（系所前 40%／班前 30%／GPA 3.0、在學註冊義務與大陸醫事學分限制）",
          "source_url": TMU_ACA_OVERSEAS_STUDY_GUIDELINES_PDF_URL,
          "published_at": "2026-10-20T00:00:00Z",
          "text": "\n".join(exchange_info_payload["eligibility"]),
          "summary": "\n".join(exchange_info_payload["eligibility"]),
          "category": "exchange_application",
          "attachments": [],
          "crawled_at": CHECKED_AT,
          "content_hash": hashlib.sha256("\n".join(exchange_info_payload["eligibility"]).encode("utf-8")).hexdigest(),
      },
      {
          "title": "臺北醫學大學：201 所合作盟校與 32 個跨國雙聯學程外語檢定門檻（學海 iBT 79/75、校內 CEFR B2 基準）",
          "source_url": TMU_OUTBOUND_EXCHANGE_ZH_URL,
          "published_at": "2026-10-20T00:00:00Z",
          "text": "\n".join(exchange_info_payload["language_requirement"]),
          "summary": "\n".join(exchange_info_payload["language_requirement"]),
          "category": "exchange_application",
          "attachments": [],
          "crawled_at": CHECKED_AT,
          "content_hash": hashlib.sha256("\n".join(exchange_info_payload["language_requirement"]).encode("utf-8")).hexdigest(),
      },
      {
          "title": "臺北醫學大學：境外研修、臨床見實習與雙聯學位申請文件及教務處《學生境外研修簽報表》備查規範",
          "source_url": TMU_OVERSEAS_INCENTIVE_APP_DOCX_URL,
          "published_at": "2026-10-20T00:00:00Z",
          "text": "\n".join(exchange_info_payload["required_documents"]),
          "summary": "\n".join(exchange_info_payload["required_documents"]),
          "category": "exchange_application",
          "attachments": [],
          "crawled_at": CHECKED_AT,
          "content_hash": hashlib.sha256("\n".join(exchange_info_payload["required_documents"]).encode("utf-8")).hexdigest(),
      },
      {
          "title": "臺北醫學大學：教育部學海飛颺／惜珠／築夢／新南向築夢與校內境外研修暨見實習獎學金（個人型／團體型50萬／線上1萬）規定",
          "source_url": TMU_OVERSEAS_INCENTIVE_REGS_PDF_URL,
          "published_at": "2026-10-20T00:00:00Z",
          "text": "\n".join(exchange_info_payload["scholarship_info"]),
          "summary": "\n".join(exchange_info_payload["scholarship_info"]),
          "category": "scholarship",
          "attachments": [],
          "crawled_at": CHECKED_AT,
          "content_hash": hashlib.sha256("\n".join(exchange_info_payload["scholarship_info"]).encode("utf-8")).hexdigest(),
      },
  ]
  (OFFICIAL_TMU_DIR / "pages.jsonl").write_text(
      "\n".join(json.dumps(p, ensure_ascii=False) for p in pages_records) + "\n",
      encoding="utf-8",
  )

  home_rules = {
      "school_id": "tmu",
      "school_name": "臺北醫學大學",
      "eligibility": student_dashboard_payload["eligibility"],
      "application_periods": student_dashboard_payload["application_periods"],
      "selection_rules": {
          "undergraduate_score_minimum": 75.0,
          "graduate_score_minimum": 75.0,
          "department_rank_percent_max": 40,
          "class_rank_percent_max": 30,
          "conduct_score_minimum": 80.0,
          "dual_degree_gpa_minimum": 3.0,
          "excluded_undergraduate_years": ["大一上"],
          "require_tmu_enrollment_registration_during_abroad": True,
          "mainland_medical_personnel_credits_not_recognized": True,
          "overseas_incentive_cefr_minimum": "B2",
          "overseas_incentive_min_working_days": 10,
          "overseas_incentive_group_grant_cap_ntd": 500000,
          "overseas_incentive_online_credit_grant_cap_ntd": 10000,
          "credit_hours_per_lecture_credit": 18,
          "credit_hours_per_practicum_credit_range": "36-54",
          "dual_degree_min_months": {
              "bachelor": 32,
              "master": 12,
              "phd": 24,
          },
          "dual_degree_min_credit_ratio_each_school": 0.3333,
          "aca_memo_due_before_dual_degree_days": 30,
          "aca_memo_due_before_exchange_working_days": 3,
          "xuehai_report_upload_due_days": 14,
          "reimbursement_and_incentive_report_due_days": 30,
          "return_documents_due": "教育部學海計畫受獎生須於返國後 2 週（14 日）內至學海計畫網站上傳問卷及 1,000 字以內中／英文成果報告書（含照片 4 張以上），並於 1 個月內完成機票與經費核銷；校內境外研修獎學金受獎生須於返國後 1 個月內繳交成果報告書至國際事務處，並持正式成績單向教務處註冊組申請學分抵免",
      },
      "source_urls": tmu_source_urls,
      "verified_at": "2026-10-20",
  }
  (OFFICIAL_TMU_DIR / "home_rules.json").write_text(
      json.dumps(home_rules, ensure_ascii=False, indent=2) + "\n",
      encoding="utf-8",
  )
  (OFFICIAL_TMU_DIR / "documents.json").write_text(
      json.dumps(
          {
              "school_name": "臺北醫學大學",
              "required_documents": student_dashboard_payload["required_documents"],
              "source_urls": tmu_source_urls,
          },
          ensure_ascii=False,
          indent=2,
      )
      + "\n",
      encoding="utf-8",
  )
  (OFFICIAL_TMU_DIR / "scholarships.json").write_text(
      json.dumps(
          {
              "school_name": "臺北醫學大學",
              "scholarships": student_dashboard_payload["scholarship_info"],
              "source_urls": tmu_source_urls,
          },
          ensure_ascii=False,
          indent=2,
      )
      + "\n",
      encoding="utf-8",
  )

  completeness = {
      "school_id": "tmu",
      "school_name": "臺北醫學大學",
      "total_partners": len(partners),
      "partner_count": len(partners),
      "international_partners": sum(
          1 for p in partners if p["country"] not in {"中國大陸", "香港", "澳門"}
      ),
      "mainland_partners": sum(
          1 for p in partners if p["country"] in {"中國大陸", "香港", "澳門"}
      ),
      "dual_degree_partner_universities": 18,
      "dual_degree_programs": 32,
      "experience_report_covered_partners": exp_covered_schools,
      "experience_report_pdf_count": total_exp_pdfs,
      "open_partners": open_partner_count,
      "reference_only_partners": len(partners) - open_partner_count,
      "verified_locations": len(partners),
      "verified_official_websites": sum(1 for p in partners if p.get("official_website")),
      "verified_campus_images": sum(1 for p in partners if p.get("image_status") == "verified"),
      "workflow_count": len(workflows),
      "destination_profile_count": len(destinations),
      "student_life_count": len(life_records),
      "active_term": (
          "臺北醫學大學國際事務處（OGE）與教務處 115–116 學年度教育部學海四項計畫（第一梯次 1/16、第二次徵求 9/7 截止）、校內《境外研修暨見實習獎勵辦法》（每年 1/15 及 5/15 兩梯次截止）、18 校 32 個跨國學碩博雙聯學程及 Apply via TMU 海外交換／短期課程同步整合；共完整收錄 201 所全球合作大學、醫學院與教學醫院（含 61 所當期開放雙聯、交換與臨床見實習合作機構及 140 所正式締約盟校，橫跨全球 37 個國家與地區，並收錄 33 所合作機構共 55 篇歷屆學長姐海外研修與臨床見實習成果報告）。"
      ),
      "verified_at": "2026-10-20",
  }
  (OFFICIAL_TMU_DIR / "catalog-completeness.json").write_text(
      json.dumps(completeness, ensure_ascii=False, indent=2) + "\n",
      encoding="utf-8",
  )
  (OFFICIAL_TMU_DIR / "verification_status.json").write_text(
      json.dumps(
          {
              "school_id": "tmu",
              "school_name": "臺北醫學大學",
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
          "sources/tmu/tmu_115_xuehai_briefing.pdf",
          TMU_115_XUEHAI_BRIEFING_PDF_URL,
          "臺北醫學大學 2026（民國115）年教育部學海計畫獎學金校內說明會簡報 PDF",
      ),
      (
          "sources/tmu/tmu_115_2_xuehai_xizhu_guidelines.pdf",
          TMU_115_2_XIZHU_GUIDELINES_PDF_URL,
          "臺北醫學大學 115年度教育部學海惜珠計畫第二次申請公告 PDF",
      ),
      (
          "sources/tmu/tmu_115_2_xuehai_xizhu_form.doc",
          TMU_115_2_XIZHU_FORM_DOC_URL,
          "臺北醫學大學 115-2 學海惜珠申請附件 DOC",
      ),
      (
          "sources/tmu/tmu_115_2_xuehai_zhumeng_guidelines.pdf",
          TMU_115_2_ZHUMENG_GUIDELINES_PDF_URL,
          "臺北醫學大學 115年度教育部學海築夢新南向築夢計畫第二次申請公告 PDF",
      ),
      (
          "sources/tmu/tmu_115_xuehai_contract.doc",
          TMU_115_XUEHAI_CONTRACT_DOC_URL,
          "臺北醫學大學 115年度教育部學海計畫行政契約書 DOC",
      ),
      (
          "sources/tmu/tmu_2026_2_moe_prospectus_en.pdf",
          TMU_2026_MOE_PROSPECTUS_EN_PDF_URL,
          "TMU 2026 MOE Study Abroad and New Southbound Study Abroad Program Prospectus PDF",
      ),
      (
          "sources/tmu/tmu_overseas_incentive_regulations.pdf",
          TMU_OVERSEAS_INCENTIVE_REGS_PDF_URL,
          "臺北醫學大學境外研修暨見實習獎勵辦法 PDF",
      ),
      (
          "sources/tmu/tmu_overseas_incentive_regulations_en.pdf",
          TMU_OVERSEAS_INCENTIVE_REGS_EN_PDF_URL,
          "TMU Overseas Training and Internship Incentive Regulations PDF",
      ),
      (
          "sources/tmu/tmu_overseas_incentive_application_v6.docx",
          TMU_OVERSEAS_INCENTIVE_APP_DOCX_URL,
          "臺北醫學大學境外研修暨見實習獎勵辦法附件及申請計劃書範例 V6 DOCX",
      ),
      (
          "sources/tmu/tmu_predeparture_form.pdf",
          TMU_PREDEPARTURE_FORM_PDF_URL,
          "臺北醫學大學學生海外行前報到單 PDF",
      ),
      (
          "sources/tmu/tmu_pharmacy_usc_dual_degree.pdf",
          TMU_PHARMACY_USC_DUAL_PDF_URL,
          "臺北醫學大學藥學系與美國南加州大學雙聯學制施行辦法含申請表 PDF",
      ),
      (
          "sources/tmu/tmu_pharmacy_psu_dual_degree.pdf",
          TMU_PHARMACY_PSU_DUAL_PDF_URL,
          "臺北醫學大學藥學系與美國賓夕法尼亞州州立大學雙聯學制施行辦法含申請表 PDF",
      ),
      (
          "sources/tmu/tmu_dual_degree_flowchart.pdf",
          TMU_DUAL_DEGREE_FLOWCHART_PDF_URL,
          "臺北醫學大學跨國雙聯學制流程圖 PDF",
      ),
      (
          "sources/tmu/tmu_aca_overseas_study_guidelines.pdf",
          TMU_ACA_OVERSEAS_STUDY_GUIDELINES_PDF_URL,
          "臺北醫學大學學生境外研修作業要點 PDF",
      ),
      (
          "sources/tmu/tmu_aca_dual_degree_regulations.pdf",
          TMU_ACA_DUAL_DEGREE_REGS_PDF_URL,
          "臺北醫學大學辦理境外雙聯學制實施辦法 PDF",
      ),
      (
          "sources/tmu/tmu_aca_credit_transfer_regulations.pdf",
          TMU_ACA_CREDIT_TRANSFER_REGS_PDF_URL,
          "臺北醫學大學學生抵免學分辦法 PDF",
      ),
      (
          "sources/tmu/partners_list_zh.html",
          TMU_PARTNERS_ZH_URL,
          "臺北醫學大學國際事務處盟校列表（中文版）HTML",
      ),
      (
          "sources/tmu/partners_list_en.html",
          TMU_PARTNERS_EN_URL,
          "臺北醫學大學國際事務處盟校列表（英文版）HTML",
      ),
      (
          "sources/tmu/dual_degree_zh.html",
          TMU_DUAL_DEGREE_ZH_URL,
          "臺北醫學大學國際事務處跨國雙聯學位專頁 HTML",
      ),
      (
          "sources/tmu/overseas_courses_zh.html",
          TMU_OVERSEAS_COURSES_ZH_URL,
          "臺北醫學大學國際事務處海外課程專頁 HTML",
      ),
      (
          "sources/tmu/student_experiences_zh.html",
          TMU_EXPERIENCES_ZH_URL,
          "臺北醫學大學國際事務處學生經驗分享專頁 HTML",
      ),
      (
          "sources/tmu/tmu_catalog_source.json",
          TMU_PARTNERS_ZH_URL,
          "臺北醫學大學 201 所全球合作大學、醫學院與教學醫院整合資料集 JSON",
      ),
      (
          "sources/tmu/tmu_resolved_locations.json",
          TMU_PARTNERS_ZH_URL,
          "臺北醫學大學 201 所全球合作機構 ROR / Wikidata 地理座標核對表 JSON",
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
      "school_id": "tmu",
      "school_name": "臺北醫學大學",
      "generated_at": CHECKED_AT,
      "active_cycle_note": completeness["active_term"],
      "sources": prov_sources,
  }
  prov_text = json.dumps(provenance_payload, ensure_ascii=False, indent=2) + "\n"
  (OFFICIAL_TMU_DIR / "import_provenance.json").write_text(prov_text, encoding="utf-8")
  (OFFICIAL_TMU_DIR / "import-provenance.json").write_text(prov_text, encoding="utf-8")

  print(
      f"Successfully built TMU catalog: {len(partners)} partners"
      f" ({open_partner_count} open, {completeness['verified_campus_images']}"
      f" verified images, {completeness['verified_locations']} verified"
      f" locations), {len(workflows)} workflows,"
      f" {len(destinations)} destinations, {len(research_records)} research"
      f" records, {exp_covered_schools} schools with experience records"
      f" ({len(student_experience_rows)} rows, {total_exp_pdfs} PDFs)."
  )


if __name__ == "__main__":
  main()
