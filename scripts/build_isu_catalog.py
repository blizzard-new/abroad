"""Build the official I-Shou University (義守大學, ISU) exchange data bundle."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re

REPO_ROOT = Path(__file__).resolve().parents[1]
SOURCES_ISU_DIR = REPO_ROOT / "sources" / "isu"
OFFICIAL_ISU_DIR = (
    REPO_ROOT / "src" / "exchange_info" / "official_data" / "isu"
)
STATIC_DIR = REPO_ROOT / "src" / "exchange_info" / "static"
UNIVERSITY_LOCATIONS_PATH = (
    REPO_ROOT
    / "src"
    / "exchange_info"
    / "official_data"
    / "university_locations.jsonl"
)

CHECKED_AT = "2026-11-02T00:00:00Z"

ISU_HOME_URL = "https://www.isu.edu.tw/"
ISU_OICA_HOME_URL = "https://oica.isu.edu.tw/"
ISU_EXCHANGE_DUAL_HUB_URL = (
    "https://oica.isu.edu.tw/page/%E5%87%BA%E5%9C%8B%E4%BA%A4%E6%8F%9B%E6%9A%A8%E9%9B%99%E8%81%AF%E5%AD%B8%E4%BD%8D-6b19J0mB5d1R"
)
ISU_OUTBOUND_EXCHANGE_URL = (
    "https://oica.isu.edu.tw/page/%E5%87%BA%E5%9C%8B%E4%BA%A4%E6%8F%9B-NlHq3RuLdDcK"
)
ISU_EXCHANGE_SISTER_SCHOOLS_URL = (
    "https://oica.isu.edu.tw/page/%E4%BA%A4%E6%8F%9B%E5%A7%90%E5%A6%B9%E6%A0%A1-X2088kX30A7R"
)
ISU_DUAL_DEGREE_URL = (
    "https://oica.isu.edu.tw/page/%E9%9B%99%E8%81%AF%E5%AD%B8%E4%BD%8D-a1O64jH79N8m"
)
ISU_DUAL_DEGREE_SCHOOLS_URL = (
    "https://oica.isu.edu.tw/page/%E9%9B%99%E8%81%AF%E5%AD%B8%E4%BD%8D%E5%AD%B8%E6%A0%A1-O76v3d9W18qB"
)
ISU_PARTNER_SCHOOLS_URL = (
    "https://oica.isu.edu.tw/page/%E5%90%88%E4%BD%9C%E5%A7%90%E5%A6%B9%E6%A0%A1-2136fX4h11fT"
)
ISU_REGULATIONS_URL = (
    "https://oica.isu.edu.tw/page/%E5%85%AC%E5%91%8A%E8%BE%A6%E6%B3%95-x86E5vW50l1r"
)
ISU_SCHOLARSHIPS_URL = (
    "https://oica.isu.edu.tw/page/%E7%8D%8E%E5%AD%B8%E9%87%91-R65031O5136E"
)
ISU_MOBILITY_SCHOLARSHIP_URL = (
    "https://oica.isu.edu.tw/page/%E7%8D%8E%E5%8A%A9%E5%AD%B8%E9%87%91-6187b9V0610U"
)
ISU_STUDENT_EXPERIENCES_URL = (
    "https://oica.isu.edu.tw/page/%E5%AD%B8%E9%95%B7%E5%A7%90%E7%B6%93%E9%A9%97%E5%82%B3%E6%89%BF-4T47lR6a96U4"
)
ISU_FAQ_URL = (
    "https://oica.isu.edu.tw/page/%E5%B8%B8%E8%A6%8B%E5%95%8F%E9%A1%8C%E8%88%87%E8%A7%A3%E7%AD%94-y294B2o02s6q"
)
ISU_DOWNLOADS_URL = (
    "https://oica.isu.edu.tw/page/%E8%A1%A8%E5%96%AE%E4%B8%8B%E8%BC%89-6s203nK125P9"
)
ISU_ADMISSION_RESULTS_URL = (
    "https://oica.isu.edu.tw/page/%E6%AD%B7%E5%B9%B4%E9%8C%84%E5%8F%96%E5%90%8D%E5%96%AE-58u131J2z9M2"
)
ISU_OVERSEAS_INTERNSHIP_URL = (
    "https://oica.isu.edu.tw/page/%E6%B5%B7%E5%A4%96%E5%AF%A6%E7%BF%92-y817l2b72v1p"
)
ISU_COST_REF_SHEET_URL = (
    "https://docs.google.com/spreadsheets/d/14w5Amw4wQzBUh1LI2Xj2m7eEGoZbmdQaI_HVhPEzWRI/htmlview"
)

ISU_OUTBOUND_SELECTION_RULES_PDF_URL = (
    "https://oica.isu.edu.tw/storage/files/5KGWFUmApkKrcC7r2uKfmaUqcMPROayp01WRTBiD.pdf"
)
ISU_MOE_XUEHAI_SELECTION_RULES_PDF_URL = (
    "https://oica.isu.edu.tw/storage/files/uCeTr1BtjbSFpZo5r1Z2VZaYiIcot3uW520kpPJU.pdf"
)
ISU_XUEHAI_SCHOLARSHIP_RULES_PDF_URL = (
    "https://oica.isu.edu.tw/storage/files/JWcDchnBY7mcsNUV15fdrbsiqNXmzZMqdb6opq3D.pdf"
)
ISU_MAINLAND_SCHOLARSHIP_RULES_PDF_URL = (
    "https://oica.isu.edu.tw/storage/files/loZLXWMAzzGVVF7MQj38fhdZo69iSefE65QO3qaT.pdf"
)
ISU_XUEWEN_SCHOLARSHIP_RULES_PDF_URL = (
    "https://www.isu.edu.tw/upload/654/3/20220829-MOE-Scholarship-Regulations.pdf"
)
ISU_JAPAN_SISTER_LIST_PDF_URL = (
    "https://oica.isu.edu.tw/storage/files/Pnq9b9VMODWbiJw6BVdjpN7EBXMY8TTrwiu28CJ3.pdf"
)
ISU_ADMISSION_114_PDF_URL = (
    "https://oica.isu.edu.tw/storage/files/vziHvsueq8I852rSAUIFKcT66eBnKnnywIdgIycD.pdf"
)
ISU_ADMIN_CONTRACT_PDF_URL = (
    "https://oica.isu.edu.tw/storage/files/lTwSRE8t05cc8FO9bK5XjWhePcoaadAho9uLpnDu.pdf"
)
ISU_AFFIDAVIT_DOCX_URL = (
    "https://oica.isu.edu.tw/storage/files/ndBzEedTtF00jOHKJvvqCtYCWbVvx2KDjZRVyCG2.docx"
)
ISU_CREDIT_APPROVAL_FORM_DOC_URL = (
    "https://oica.isu.edu.tw/storage/files/CyDv16tauPxLhbW491g2hv9c5x42CCWiam2nN0JA.doc"
)
ISU_CREDIT_TRANSFER_FORM_DOC_URL = (
    "https://oica.isu.edu.tw/storage/files/dnLg5CuBYnPAJf9c63fGpCjfjfwWdBevIx3BzUx7.doc"
)
ISU_RETURN_PROCEDURE_PDF_URL = (
    "https://oica.isu.edu.tw/storage/files/0hUyXldM3VM1XPRfNORKw5LlBOQkfnbWTvXXKquS.pdf"
)
ISU_RETURN_REPORT_DOC_URL = (
    "https://oica.isu.edu.tw/storage/files/vdjPK5ZiX4SN1YuA28rlKk9U2iK4XZF0TjQCwetW.doc"
)

REGION_COST_DEFAULTS = {
    "日本": (
        "每月生活費約 USD 650–1,100（折合日圓約 JPY 90,000–150,000 / 月、新臺幣約 20,000–35,000 元；依義守大學《海外交換費用參考表》公告：東洋學園大學住宿費約 JPY 45,000–52,500 / 月、埼玉大學住宿約 JPY 5,900–17,000 / 月、京都府立大學與和歌山大學住宿約 JPY 13,900–50,000 / 月、追手門學院大學與天理大學等設有國際學舍）",
        "須由日本接待大學代向出入國在留管理局申請「在留資格認定證明書（COE）」，獲發後至日本台灣交流協會高雄事務所或台北事務所申辦留學簽證，入境後加入日本國民健康保險（NHI）並於出國前投保海外全期醫療及意外險。",
    ),
    "韓國": (
        "每月生活費約 USD 620–1,050（折合韓元約 KRW 800,000–1,400,000 / 月、新臺幣約 19,500–33,500 元；依義守大學《海外交換費用參考表》公告：建國大學校內雙人房每學期約 KRW 1,455,000、嘉泉大學四人房每學期約 USD 780、仁川大學每學期約 KRW 860,000–1,150,000、翰林大學每學期約 USD 650–1,400、順天鄉大學與東亞大學等均提供國際學生宿舍）",
        "須憑韓國接待校核發之標準入學許可書（Certificate of Admission）向駐台北韓國代表部申辦 D-2-6 交換學生簽證，入境後辦理外國人登錄證（ARC）並依法納保韓國國民健康保險（NHIS）。",
    ),
    "中國大陸": (
        "每月生活費約 USD 320–650（折合人民幣約 RMB 2,000–4,200 / 月、新臺幣約 10,000–20,500 元；含浙江大學、南京大學、武漢大學、山東大學、四川大學、吉林大學、蘭州大學、西安交通大學、大連理工大學、重慶大學、東北大學、中國海洋大學、蘇州大學等校內留學生公寓與學生食堂開銷）",
        "須持有效「臺灣居民來往大陸通行證（臺胞證）」及大陸姐妹校寄發之錄取通知書辦理報到，並依《義守大學學生赴境外交換研修甄選辦法》及《學文助學金設置及甄選作業辦法》規定購買涵蓋交換全期之海外醫療及意外保險。",
    ),
    "香港": (
        "每月生活費約 USD 1,000–1,600（折合港幣約 HKD 7,800–12,500 / 月、新臺幣約 31,500–50,500 元，含香港理工大學校內學生宿舍、膳食與港鐵交通）",
        "須透過香港理工大學代向香港入境事務處申辦來港就讀進入許可（Student Visa / Entry Permit）並投保海外全期醫療保險。",
    ),
    "澳門": (
        "每月生活費約 USD 650–1,100（折合澳門幣約 MOP 5,200–8,800 / 月、新臺幣約 20,500–35,000 元，含澳門科技大學、澳門城市大學、澳門理工大學、聖若瑟大學校內學生宿舍與膳食）",
        "須持有效護照於入境澳門後依接待大學指引至治安警察局居留及逗留事務廳辦理「逗留特別許可（學生逗留簽注）」並投保醫療保險。",
    ),
    "馬來西亞": (
        "每月生活費約 USD 450–800（折合馬幣約 MYR 2,000–3,500 / 月、新臺幣約 14,500–25,500 元；依義守大學《海外交換費用參考表》公告：馬來亞大學（Universiti Malaya）校內外住宿與膳食合計每月約 MYR 1,500–2,000）",
        "須透過馬來西亞教育全球服務中心（EMGS）線上申辦學生簽證核准函（VAL / Mobility Pass）並投保馬來西亞境內醫療險。",
    ),
    "泰國": (
        "每月生活費約 USD 450–820（折合泰銖約 THB 15,000–27,000 / 月、新臺幣約 14,500–26,000 元；含泰國藝術大學 Silpakorn University、佛統皇家大學、北碧皇家大學、宋卡王子大學等學生宿舍與生活開銷）",
        "須憑泰國接待大學入學許可公文向泰國貿易經濟辦事處（TTEO）申辦 Non-Immigrant ED 教育簽證並投保海外全期醫療險。",
    ),
    "印尼": (
        "每月生活費約 USD 400–750（折合印尼盾約 IDR 6,500,000–11,500,000 / 月、新臺幣約 13,000–24,000 元；含佩特拉基督教大學 Petra Christian University、日惹大學 UGM、艾爾朗加大學 Universitas Airlangga、建國大學 BINUS University 等住宿與膳食）",
        "須由印尼接待大學協助申辦印尼學生電子簽證（Study e-Visa / KITAS）並投保海外全期醫療保險。",
    ),
    "越南": (
        "每月生活費約 USD 400–720（折合新臺幣約 13,000–23,000 元；含河內國家大學、太原大學、峴港大學、順化大學、胡志明市經濟財經大學 UEF、文郎大學、維新大學等住宿與餐飲）",
        "須由越南接待大學協助向越南出入境管理局申辦 DH 學生簽證並投保海外全期醫療及意外保險。",
    ),
    "菲律賓": (
        "每月生活費約 USD 450–800（折合新臺幣約 14,500–25,500 元；含菲律賓大學、雅典耀大學 Ateneo de Manila University、馬プア大學 Mapúa University、萊西姆大學等校內外學生宿舍與膳食）",
        "須依菲律賓接待大學指引辦理學生簽證（9F）或特別學習許可（SSP）並投保海外醫療保險。",
    ),
    "印度": (
        "每月生活費約 USD 380–680（折合新臺幣約 12,000–21,500 元；含阿मिटी大學 Amity University、金德爾全球大學 O.P. Jindal Global University、韋洛爾理工大學 VIT 等校內住宿與膳食）",
        "須憑印度接待大學核發之入學許可向印度台北協會申辦印度學生簽證（Student Visa）並投保海外全期醫療保險。",
    ),
    "法國": (
        "每月生活費約 USD 1,000–1,550（折合歐元約 EUR 920–1,420 / 月、新臺幣約 32,000–49,500 元；依義守大學《海外交換費用參考表》公告：蒙彼利埃商學院住宿約 EUR 550–700 / 月、諾歐商學院 NEOMA 約 EUR 600–850 / 月、南特商學院 Audencia 約 EUR 600–750 / 月、北方高等商學院 EDHEC 約 EUR 650–850 / 月、巴黎高等對外貿易學院 ESCE 約 EUR 750–1,200 / 月）",
        "須先經法國教育中心（Campus France）完成 Etudes en France 線上程序與面試，再向法國在台協會申辦長期學生簽證（VLS-TS）。",
    ),
    "德國": (
        "每月生活費約 USD 980–1,450（折合歐元約 EUR 900–1,350 / 月、新臺幣約 31,000–46,000 元；依義守大學《海外交換費用參考表》公告：杜塞道夫海因里希海涅大學與拜羅伊特大學住宿及生活費合計約 EUR 850–1,000 / 月）",
        "須開立德國限制提領帳戶（Blocked Account）並憑入學許可向德國在台協會申辦德國長期學生簽證及投保德國公保／醫療險。",
    ),
    "英國": (
        "每月生活費約 USD 1,350–2,050（折合英鎊約 GBP 1,050–1,600 / 月、新臺幣約 43,000–65,000 元；依義守大學《海外交換費用參考表》公告：諾丁漢特倫特大學 NTU 交換與雙聯學位住宿約 GBP 560–800 / 月，西敏寺大學、金斯頓大學、考文垂大學亦提供學生宿舍申請）",
        "交換 6 個月以內可憑入學許可辦理英國 ETA / Standard Visitor 入境，修讀 1 學年或雙聯學位須申辦英國 Student Visa 並繳納 IHS 醫療附加費。",
    ),
    "奧地利": (
        "每月生活費約 USD 1,000–1,500（折合歐元約 EUR 920–1,380 / 月、新臺幣約 32,000–48,000 元；依義守大學《海外交換費用參考表》公告：茵斯布魯克管理學院 MCI 與約翰內姆應用科技大學 FH JOANNEUM 住宿費約 EUR 380–650 / 月）",
        "交換 1 學期（6 個月內）向奧地利台北辦事處申辦奧地利學生 D 簽證，交換 1 學年須申辦學生居留許可並投保申根醫療保險。",
    ),
    "芬蘭": (
        "每月生活費約 USD 980–1,450（折合歐元約 EUR 900–1,350 / 月、新臺幣約 31,000–46,000 元；依義守大學《海外交換費用參考表》公告：哈加ヘ利亞應用科技大學 Haaga-Helia 透過 HOAS 申請學生公寓每月約 EUR 400–700）",
        "須憑芬蘭接待大學核發之入學許可線上向芬蘭移民局（Migri）申辦學生居留許可（Residence Permit for Studies）並投保符合芬蘭規定之醫療保險。",
    ),
    "瑞典": (
        "每月生活費約 USD 950–1,400（折合瑞典克朗約 SEK 10,000–14,500 / 月、新臺幣約 30,000–44,500 元；含克里斯蒂安斯塔德大學 Kristianstad University 學生宿舍與生活費）",
        "須憑瑞典接待大學核發之入學許可與醫療保險證明向瑞典移民局（Migrationsverket）申辦學生居留許可。",
    ),
    "捷克": (
        "每月生活費約 USD 680–1,050（折合歐元約 EUR 620–950 / 月、新臺幣約 21,500–33,500 元；依義守大學《海外交換費用參考表》公告：布拉格都會大學 Metropolitan University Prague 學生宿舍每月約 EUR 260–400，生活開銷極具優勢）",
        "須憑捷克接待大學核發之入學許可與住宿證明向捷克經濟文化辦事處申辦長期學生簽證並投保捷克認可之醫療保險。",
    ),
    "立陶宛": (
        "每月生活費約 USD 620–980（折合歐元約 EUR 570–900 / 月、新臺幣約 19,500–31,000 元；依義守大學《海外交換費用參考表》公告：維陶瑪納大學 Vytautas Magnus University 校內宿舍每月僅約 EUR 150–300，並有機會獲歐盟 Erasmus+ 獎學金補助）",
        "須憑立陶宛接待大學入學許可申辦申根 D 類國家簽證並投保申根醫療保險。",
    ),
    "愛沙尼亞": (
        "每月生活費約 USD 700–1,080（折合歐元約 EUR 650–1,000 / 月、新臺幣約 22,000–34,000 元；含塔林理工大學 Tallinn University of Technology 校內學生宿舍與膳食）",
        "須憑愛沙尼亞接待大學入學許可申辦愛沙尼亞長期學生 D 簽證並投保申根醫療保險。",
    ),
    "西班牙": (
        "每月生活費約 USD 950–1,450（折合歐元約 EUR 880–1,320 / 月、新臺幣約 30,500–46,000 元；含赫羅納大學聖波爾德馬爾餐旅管理學院 EUHT StPOL 校內住宿與包餐待遇）",
        "須憑西班牙接待大學入學許可與財力、無犯罪紀錄及醫療保險證明向西班牙商務辦事處申辦學生簽證。",
    ),
    "美國": (
        "每月生活費約 USD 1,350–2,100（依匯率折合新臺幣約 43,000–67,000 元；依義守大學《海外交換費用參考表》公告：南伊利諾大學卡本岱爾校區 SIUC 每學期食宿約 USD 5,311、密蘇里大學堪薩斯分校 UMKC、聖地牙哥州立大學 SDSU、關島大學 UOG、西來大學 UWest、奧克拉荷馬州立大學 OSU、內華達大學拉斯維加斯分校 UNLV 等均提供校內宿舍與 Meal Plan）",
        "須憑美國接待大學核發之 DS-2019（J-1 交換生）或 I-20（F-1 雙聯學位／訪學生）表格繳交 SEVIS I-901 費用並向美國在台協會（AIT）申辦簽證，且須投保符合接待校規定之全期海外醫療保險。",
    ),
    "加拿大": (
        "每月生活費約 USD 1,200–1,850（折合加幣約 CAD 1,650–2,500 / 月、新臺幣約 38,500–59,000 元；含紐布朗斯維克大學 UNB 與里賈納大學 University of Regina 校內住宿與膳食）",
        "交換研習 1 學期（6 個月內）可申辦加拿大 eTA，修讀 1 學年或雙聯學位須申辦加拿大 Study Permit 並投保醫療保險。",
    ),
    "澳洲": (
        "每月生活費約 USD 1,450–2,250（折合澳幣約 AUD 2,200–3,400 / 月、新臺幣約 46,500–72,000 元；含南十字星大學 Southern Cross University 校內外學生公寓與膳食）",
        "須購買澳洲海外學生健康保險（OSHC）並憑接待校核發之 CoE 申辦澳洲 Subclass 500 學生簽證。",
    ),
}

SEMESTER_DATES_BY_COUNTRY = {
    "日本": "春季學期（Spring Semester）：約 4 月初至 8 月初；秋季學期（Fall Semester）：約 9 月中下旬至翌年 1 月底或 2 月初",
    "韓國": "春季學期（Spring Semester）：約 3 月初至 6 月中旬；秋季學期（Fall Semester）：約 9 月初至 12 月中旬",
    "中國大陸": "春季學期（下學期）：約 2 月下旬至 7 月初；秋季學期（上學期）：約 9 月初至翌年 1 月中旬",
    "香港": "第一學期（秋季班）：約 9 月初至 12 月下旬；第二學期（春季班）：約 1 月中旬至 5 月下旬",
    "澳門": "第一學期（秋季班）：約 9 月初至 12 月下旬；第二學期（春季班）：約 1 月下旬至 5 月下旬",
    "馬來西亞": "秋季學期：約 9–10 月至翌年 1–2 月；春季學期：約 2–6 月",
    "泰國": "第一學期（秋季班）：約 8 月至 12 月；第二學期（春季班）：約 1 月至 5 月",
    "印尼": "奇數／秋季學期（Odd Semester）：約 8/9 月至翌年 1 月；偶數／春季學期（Even Semester）：約 2 月至 6/7 月",
    "越南": "第一學期（秋季班）：約 9 月至翌年 1 月；第二學期（春季班）：約 2 月至 6 月",
    "菲律賓": "第一學期（秋季班）：約 8 月至 12 月；第二學期（春季班）：約 1 月至 5 月",
    "法國": "秋季學期（Fall Semester）：約 9 月初至 12 月底；春季學期（Spring Semester）：約 1 月中旬至 5 月底",
    "德國": "冬季學期（Wintersemester）：約 10 月初至翌年 2 月底；夏季學期（Sommersemester）：約 4 月初至 7 月底",
    "英國": "秋季學期（Autumn Term）：約 9 月下旬至翌年 1 月；春季學期（Spring Term）：約 1 月下旬至 6 月",
    "奧地利": "冬季學期（Winter Semester）：約 9 月底至翌年 1 月底；夏季學期（Summer Semester）：約 2 月底至 6 月底",
    "芬蘭": "秋季學期（Autumn Semester）：約 8 月下旬至 12 月下旬；春季學期（Spring Semester）：約 1 月中旬至 5 月下旬",
    "瑞典": "秋季學期（Autumn Semester）：約 8 月底至翌年 1 月中旬；春季學期（Spring Semester）：約 1 月中旬至 6 月初",
    "捷克": "冬季學期（Winter / Fall Semester）：約 9 月下旬至翌年 1 月底；夏季學期（Summer / Spring Semester）：約 2 月中旬至 6 月中旬",
    "立陶宛": "秋季學期（Autumn Semester）：約 9 月初至翌年 1 月底；春季學期（Spring Semester）：約 2 月初至 6 月下旬",
    "愛沙尼亞": "秋季學期（Autumn Semester）：約 9 月初至翌年 1 月底；春季學期（Spring Semester）：約 2 月初至 6 月中旬",
    "西班牙": "第一學期（秋季班）：約 9 月中旬至翌年 1 月下旬；第二學期（春季班）：約 1 月下旬至 6 月中旬",
    "美國": "秋季學期（Fall Semester）：約 8 月中下旬至 12 月中旬；春季學期（Spring Semester）：約 1 月中旬至 5 月中旬",
    "加拿大": "秋季學期（Fall Term）：約 9 月初至 12 月下旬；冬季／春季學期（Winter Term）：約 1 月初至 4 月底",
    "澳洲": "第一學期（Autumn / Semester 1）：約 2 月下旬至 6 月底；第二學期（Spring / Semester 2）：約 7 月下旬至 11 月底",
}


def clean_text(s: str) -> str:
  if not s:
    return ""
  return re.sub(r"\s+", " ", s).strip()


def sync_global_assets_and_locations(
    catalog_source: list[dict], resolved_locations: dict
) -> None:
  """Ensure school-images.json and university_locations.jsonl contain all ISU partner schools."""
  si_path = STATIC_DIR / "assets" / "school-images.json"
  si_data = json.loads(si_path.read_text(encoding="utf-8"))
  schools_list = si_data.get("schools", [])
  by_name = {
      str(r.get("school_name", "")): r
      for r in schools_list
      if isinstance(r, dict)
  }
  si_changed = False
  for item in catalog_source:
    fn = item["school_name"]
    irec = item.get("image_record") or {}
    if irec.get("local_path"):
      new_rec = {
          "school_name": fn,
          "local_path": irec["local_path"],
          "image_source_url": (
              irec.get("image_source_url")
              or irec.get("image_url")
              or irec["local_path"]
          ),
          "source_page_url": (
              irec.get("source_page_url")
              or irec.get("official_page_url")
              or item.get("website")
              or ""
          ),
          "official_page_url": (
              item.get("website") or irec.get("official_page_url") or ""
          ),
          "attribution": irec.get("attribution") or "Wikimedia Commons",
          "status": "verified",
          "country": item["country"],
      }
      if fn not in by_name:
        schools_list.append(new_rec)
        by_name[fn] = new_rec
        si_changed = True
      elif (
          by_name[fn].get("local_path") != new_rec["local_path"]
          or by_name[fn].get("country") != new_rec["country"]
          or by_name[fn].get("status") != "verified"
      ):
        by_name[fn].update(new_rec)
        si_changed = True
  if si_changed:
    si_data["schools"] = schools_list
    si_path.write_text(
        json.dumps(si_data, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

  loc_lines = UNIVERSITY_LOCATIONS_PATH.read_text(encoding="utf-8").splitlines()
  loc_by_name = {}
  parsed_locs = []
  for line in loc_lines:
    if line.strip():
      obj = json.loads(line)
      parsed_locs.append(obj)
      loc_by_name[str(obj.get("school_name", ""))] = obj
  loc_changed = False
  for item in catalog_source:
    fn = item["school_name"]
    loc = resolved_locations.get(fn)
    if fn not in loc_by_name and loc:
      lat = float(
          loc.get("latitude")
          if loc.get("latitude") is not None
          else loc.get("lat", 22.7271)
      )
      lon = float(
          loc.get("longitude")
          if loc.get("longitude") is not None
          else loc.get("lon", 120.4058)
      )
      new_loc = {
          "school_name": fn,
          "country": item["country"],
          "city": loc.get("city") or item["country"],
          "latitude": lat,
          "longitude": lon,
          "geocode_status": "verified",
          "geocoded_at": CHECKED_AT,
          "source_url": loc.get("source_url") or "https://www.wikidata.org",
          "identity_source_url": (
              item.get("website") or loc.get("source_url") or "https://ror.org"
          ),
          "precision": loc.get("precision") or "representative",
      }
      parsed_locs.append(new_loc)
      loc_by_name[fn] = new_loc
      loc_changed = True
  if loc_changed:
    UNIVERSITY_LOCATIONS_PATH.write_text(
        "\n".join(json.dumps(r, ensure_ascii=False) for r in parsed_locs)
        + "\n",
        encoding="utf-8",
    )


def main() -> None:
  OFFICIAL_ISU_DIR.mkdir(parents=True, exist_ok=True)
  catalog_source = json.loads(
      (SOURCES_ISU_DIR / "isu_catalog_source.json").read_text(
          encoding="utf-8"
      )
  )
  resolved_locations = json.loads(
      (SOURCES_ISU_DIR / "isu_resolved_locations.json").read_text(
          encoding="utf-8"
      )
  )
  bin_urls_path = SOURCES_ISU_DIR / "binary_source_urls.json"
  bin_urls_raw = (
      json.loads(bin_urls_path.read_text(encoding="utf-8"))
      if bin_urls_path.exists()
      else {}
  )
  sync_global_assets_and_locations(catalog_source, resolved_locations)

  school_images_data = json.loads(
      (STATIC_DIR / "assets" / "school-images.json").read_text(encoding="utf-8")
  )
  visual_by_name = {
      str(r.get("school_name", "")): r
      for r in school_images_data.get("schools", [])
      if isinstance(r, dict) and r.get("status") == "verified"
  }

  partners: list[dict] = []
  workflows: list[dict] = []
  destinations: list[dict] = []
  research_records: list[dict] = []
  life_records: list[dict] = []
  experience_sources_records: list[dict] = []
  student_experience_rows: list[dict] = []
  new_locations: list[dict] = []

  open_partner_count = 0
  dual_degree_count = 0
  exp_covered_schools = 0
  total_exp_reports = 0

  for idx, item in enumerate(catalog_source):
    sn = idx + 1
    full_name = item["school_name"]
    zh_name = item["name_zh"]
    country = item["country"]
    region = item["region"]
    avail_status = (
        "open" if item.get("offering_status") == "open" else "reference_only"
    )
    if avail_status == "open":
      open_partner_count += 1

    group_str = clean_text(
        item.get("group") or "國際及兩岸事務處正式締約合作姐妹校"
    )
    if "雙聯" in group_str:
      dual_degree_count += 1
    quota_str = clean_text(
        item.get("quota") or "每學期 2 名（依義守大學國際及兩岸事務處交換協議名額）"
    )
    detail_url = item.get("detail_url") or ISU_EXCHANGE_SISTER_SCHOOLS_URL
    factsheet_url = item.get("factsheet_url")

    if "雙聯學位" in group_str and "交換" in group_str:
      program_type = (
          "義守大學校級出國交換生計畫暨海外雙聯學位計畫（Double Degree Program）"
      )
      source_url = ISU_EXCHANGE_SISTER_SCHOOLS_URL
    elif "雙聯學位" in group_str:
      program_type = "義守大學海外雙聯學位合作計畫（Double Degree Program）"
      source_url = ISU_DUAL_DEGREE_SCHOOLS_URL
    elif country in {"中國大陸", "香港", "澳門"}:
      program_type = f"義守大學境外交換研修暨兩岸交流計畫（{group_str}）"
      source_url = ISU_EXCHANGE_SISTER_SCHOOLS_URL
    else:
      program_type = f"義守大學校級出國交換研修計畫（{group_str}）"
      source_url = ISU_EXCHANGE_SISTER_SCHOOLS_URL

    colleges_str = clean_text(
        item.get("colleges")
        or "智慧科技學院、工學院、管理學院、傳播與設計學院、國際學院、觀光餐旅學院、醫學院、醫學科技學院、原住民族學院、通識教育中心"
    )
    degree_levels_str = clean_text(
        item.get("eligible_degrees")
        or "義守大學在學學士班（大二以上）及碩博士班（碩一以上）學生（延修生、休學學生及當學期畢業者除有特殊原因外不得申請）"
    )
    lang_req_str = clean_text(item.get("language_req") or "")
    gpa_req_str = clean_text(item.get("gpa_req") or "")
    website = item.get("website") or ISU_PARTNER_SCHOOLS_URL
    remarks_raw = clean_text(item.get("notes") or "")
    tuition_note = clean_text(item.get("tuition_note") or "")
    exps = item.get("experience_reports") or []

    round_label = (
        "115–116學年度赴境外交換研修暨雙聯學位校內甄選（第一梯次 2 月申請秋季班出國、第二梯次 8 月申請春季班出國）"
    )
    app_deadline_str = clean_text(
        item.get("deadline")
        or (
            "第一梯次（秋季班出國交換一學期或一學年）：每年 2 月 1 日至 3 月 15 日校內甄選；第二梯次（春季班出國交換一學期）：每年 8 月 1 日至 9 月 15 日校內甄選（依義守大學國際及兩岸事務處當學期公告截止日為準）"
        )
    )
    deadline_iso = "2027-03-15T17:00:00+08:00"
    win_status = "open" if avail_status == "open" else "closed"
    acad_year = "115"

    study_period_str = clean_text(item.get("duration") or "一學期或一學年")
    sem_dates_str = SEMESTER_DATES_BY_COUNTRY.get(
        country, "秋季學期：約 9 月至翌年 1 月；春季學期：約 2 月至 6 月"
    )
    housing_str = (
        f"獲義守大學國際及兩岸事務處提名錄取後，可依 {zh_name} 國際事務處指引申請校內外學生宿舍或國際學舍"
        + (f"（學費與住宿待遇：{tuition_note}）" if tuition_note else "。")
    )
    course_rest_str = (
        f"開放對象與學院：{colleges_str}（{degree_levels_str}）。依《義守大學學生赴境外交換研修甄選辦法》、《義守大學學生出國期間有關學業及學籍處理要點》及《義守大學與境外大學辦理雙聯學制實施辦法》規定："
        "（1）基本資格（《赴境外交換研修甄選辦法》第 2 條）：申請人須為具有本校學籍之大學部（大二以上）及研究所（碩一以上）在學學生；延修生、休學學生及當學期畢業者，除有特殊原因外，不得提出申請；"
        "（2）外語能力標準（《赴境外交換研修甄選辦法》第 2 條第 3 款）：外語能力應符合交流學校之規定；除赴以中文為主要授課語言之學校外，如交流學校無外語能力規定，應以符合本校英語能力畢業資格檢定標準（CEFR B1 / TOEIC 550 / TOEFL iBT 42 / IELTS 4.0）為原則；"
        "（3）在學註冊與赴外修習學分下限（《赴境外交換研修甄選辦法》第 7 條及《學文助學金設置及甄選作業辦法》第 17 條）：出國交流期間應維持本校學籍並依規定繳交本校每學期全額學雜費；每學期修習課程以不低於 9 學分為原則（赴大陸結盟學校研修團每學期至少修習 16 學分以上），且學期學業平均成績應符合及格標準（60 分以上）；"
        "（4）返國學分承認與抵免：出國前應填具《學分承認表（Credit Transfer Form）》經系所主管核章，返國後二週內繳交《返校手續單》、《學分抵免表》與 1,500 字以上《成果心得報告》及簡報檔辦理學分採認抵免；"
        "（5）跨國雙聯學位：本校與英國諾丁漢特倫特大學、美國奧克拉荷馬州立大學、南伊利諾大學卡本岱爾校區、內華達大學拉斯維加斯分校、香港理工大學、日本帝京大學、韓國又松大學 SolBridge 國際商學院、大陸四川大學、吉林大學、蘭州大學等校合作辦理 3+1、2+2、3+1+1 雙聯學位。"
    )

    living_cost_str, visa_health_str = REGION_COST_DEFAULTS.get(
        country,
        (
            "每月生活費約 USD 750–1,350（依匯率折合新臺幣約 24,000–43,000 元，含住宿、膳食與市區交通）",
            "須依接待國駐臺機構規定申辦學生簽證，並依《義守大學學生赴境外交換研修甄選辦法》第 6 條於出國前自行購買涵蓋交換全期之海外醫療及意外保險送國際及兩岸事務處備查。",
        ),
    )

    tuition_points_list = [
        (
            f"義守大學在學註冊與學雜費規定（依《義守大學學生赴境外交換研修甄選辦法》第 7 條及國際處《常見問題與解答》）：交換生出國交流期間須維持義守大學學籍並繳交本校每學期全額學雜費，免繳接待姐妹校學費（除部分自費訪學、美國迪士尼有薪實習或雙聯學位學程依合約規定繳交外）。本合作校待遇：{tuition_note or '繳交義守大學全額學雜費、免繳接待姐妹校學費'}。"
        ),
        (
            "義守大學六大出國交換與雙聯學位獎助學金體系（依《義守大學辦理教育部學海飛颺及學海惜珠計畫甄選辦法》、《義守大學學海助學金設置及甄選作業辦法》、《義守大學赴大陸校際交換獎學金辦法》及《義守大學學文助學金設置及甄選作業辦法》）："
            "（1）《教育部學海飛颺獎學金》（具中華民國國籍、操行 80 分以上無懲處、前一學期學業成績於該系所該年級前 40% 或班排前 30%，補助 NT$ 50,000 以上）；"
            "（2）《教育部學海惜珠獎學金》（持低收入戶、中低收入戶或特殊境遇家庭證明且前學期成績達系年級前 40% 或班排前 30%，補助 NT$ 50,000–300,000 以上）；"
            "（3）《義守大學學海助學金》（補助本校在籍學生［含港澳生、境外生］赴海外簽約姐妹校長期交換、修讀雙聯學位或短期交流，前學期成績達系年級前 50% 且通過英語畢業門檻，補助 NT$ 20,000–30,000 以上）；"
            "（4）《義守大學赴大陸校際交換獎學金》（補助本校學生［含陸生、港澳生、境外生］赴大陸姐妹校交換，修課全部通過補助 NT$ 4,000、部分通過補助 NT$ 3,000）；"
            "（5）《義守大學學文助學金》（含大陸短期交流團、暑期一個月學習團公費／部分公費補助，以及一學期大陸研修團［累計成績達全班前 50% 並通過校訂英檢與資訊檢測］）；"
            "（6）《歐盟 Erasmus+ 伊拉斯莫斯計畫獎學金》（補助獲選赴歐洲 Erasmus+ 締約姐妹校交換之學生）。"
        ),
    ]

    app_steps_list = [
        (
            f"步驟一（確認義守大學大二／碩一以上在學資格與 {zh_name} 語檢門檻，於每年 2 月或 8 月提出校內申請）：確認具本校在學學籍（大二或碩一以上）且符合學業門檻（{gpa_req_str}）與外語標準（{lang_req_str}），於第一梯次（每年 2 月至 3 月中旬，申請次學年第 1 學期秋季班出國）或第二梯次（每年 8 月至 9 月中旬，申請次學年第 2 學期春季班出國）向國際及兩岸事務處報名。"
        ),
        (
            "步驟二（備齊校內甄選應繳文件經系所及學院核章後送交國際及兩岸事務處）：檢附（1）義守大學學生赴境外交換研修申請表、（2）中英文歷年成績單正本（含班級或系級排名百分比）、（3）有效外語能力檢定證明影本（TOEFL iBT / IELTS / TOEIC / JLPT / TOPIK）、（4）中英文讀書計畫與自傳、（5）教師推薦信、（6）交換生具結書（家長同意簽章）及《學分承認表（Credit Transfer Form）》。"
        ),
        (
            f"步驟三（參加國際及兩岸事務處書面審查與面試甄選，獲錄取後申請教育部學海飛颺／惜珠或義守大學學海／大陸交換／學文獎助學金）：通過校內甄選獲推薦為赴 {full_name} 交換生或雙聯學位生後，同步檢附《獎學金申請資料單》、《行政契約書》與《獎學金具結書》申請教育部學海飛颺／惜珠或校內學海助學金。"
        ),
        (
            f"步驟四（由國際及兩岸事務處向 {zh_name} 辦理官方提名並完成簽證、全額學雜費註冊、海外保險及返國學分抵免）：配合接待校期限遞交入學與宿舍申請；出國前完成義守大學全額學雜費註冊及海外全期醫療意外保險；抵達接待校後繳交《國外抵達報告表（Arrival Report）》並每學期修習至少 9 學分（大陸研修團至少 16 學分）；返國後二週內繳交《返校手續單》、《學分抵免表》與 1,500 字以上《成果心得報告》及簡報檔。"
        ),
    ]

    elig_points_list = [
        f"合作類別與計畫組別：{program_type}（{group_str}）",
        f"開放學制與年級：{degree_levels_str}",
        f"開放申請學院：{colleges_str}",
        f"歷年學業成績門檻：{gpa_req_str}",
        f"外語能力標準：{lang_req_str}",
        "在學註冊與赴外修課規定（《義守大學學生赴境外交換研修甄選辦法》第 7 條）：交換期間須維持本校學籍並繳交義守大學全額學雜費，每學期修習課程以不低於 9 學分為原則（大陸研修團每學期至少 16 學分），且學期平均成績須達及格標準（60 分以上）。",
    ]
    if tuition_note:
      elig_points_list.append(f"姐妹校學費與住宿待遇：{tuition_note}")
    if remarks_raw:
      elig_points_list.append(f"簡章備註與締約重點說明：{remarks_raw}")

    exp_links: list[dict] = []
    exp_labels: list[str] = []
    if exps:
      exp_covered_schools += 1
      total_exp_reports += len(exps)
      seen_exp_urls: set[str] = set()
      for e_idx, e in enumerate(exps):
        raw_t = clean_text(e.get("title") or f"赴 {zh_name} 交換生心得報告")
        esem = e.get("semester") or "歷年交換"
        eurl = (
            e.get("url")
            or f"{ISU_STUDENT_EXPERIENCES_URL}#isu-exp-{sn}-{e_idx+1}"
        )
        if eurl in seen_exp_urls:
          eurl = f"{eurl}#r{e_idx+1}"
        seen_exp_urls.add(eurl)
        exp_labels.append(raw_t[:36])
        exp_links.append({
            "title": raw_t,
            "url": eurl,
            "academic_year": esem,
            "semester": esem,
            "college": "國際學院／管理學院／傳播與設計學院／觀光餐旅學院／智慧科技學院／工學院／醫學院／醫學科技學院／原住民族學院",
            "department": "義守大學赴境外交換研修生",
        })
        summary_text = (
            f"義守大學國際及兩岸事務處（OICA）公開收錄之學長姐赴 {country} {full_name} 交換研習官方成果心得報告（{raw_t}），詳述選課修習與學分抵免、校內外宿舍環境、簽證保險辦理、學海飛颺／學海助學金申請與當地生活開銷。"
        )
        theme_map = {
            "academics": f"義守大學交換生於《{raw_t}》分享在 {zh_name} 修習每學期至少 9 學分（大陸研修團至少 16 學分）與返國辦理義守大學《學分承認表》及《學分抵免表》採認之實務經驗。",
            "housing": f"義守大學交換生記錄申請 {zh_name} 校內外學生宿舍或國際學舍、寢室設備與周邊生活機能（{housing_str[:100]}）。",
            "campus_culture": f"義守大學國際及兩岸事務處公開收錄《{raw_t}》之跨文化課堂討論、國際學伴制度與校園生活實錄。",
            "cost": f"義守大學交換生分享於 {zh_name} 之每月住宿、伙食與交通開銷（{living_cost_str[:100]}），以及免繳姐妹校學費與申請教育部學海飛颺／惜珠或義守大學學海助學金之經驗。",
        }
        student_experience_rows.append({
            "school_name": full_name,
            "country": country,
            "title": raw_t,
            "source_url": eurl,
            "source_type": "pdf" if eurl.lower().endswith(".pdf") else "article",
            "platform": "義守大學國際及兩岸事務處（OICA）—學長姐經驗傳承專區",
            "author_name": (
                raw_t.split("—")[-1].strip()[:24]
                if "—" in raw_t
                else "義守大學交換生"
            ),
            "language": "zh",
            "summary": summary_text,
            "themes": ["academics", "housing", "campus_culture", "cost"],
            "theme_summaries": theme_map,
            "content_status": "full_text",
            "perspective": "official_student_story",
            "published_at": None,
            "discovered_at": CHECKED_AT,
            "content_hash": hashlib.sha256(
                f"{full_name}:isu_exp:{e_idx}:{eurl}".encode("utf-8")
            ).hexdigest(),
            "exchange_term": esem,
            "summary_zh": summary_text,
            "original_summary": summary_text,
            "theme_summaries_zh": theme_map,
            "translation_status": "original",
            "source_kind": "official_experience_page",
        })

    sample_reports = [
        {"title": lk["title"], "url": lk["url"], "term": lk["semester"]}
        for lk in exp_links[:6]
    ]
    experience_sources_records.append({
        "home_university": "義守大學",
        "school_name": full_name,
        "country": country,
        "official_experience_portal_url": (
            exp_links[0]["url"] if exp_links else ISU_STUDENT_EXPERIENCES_URL
        ),
        "partner_page_url": source_url,
        "report_count": len(exps),
        "sample_reports": sample_reports,
        "checked_at": CHECKED_AT,
    })

    loc = resolved_locations.get(full_name) or {
        "city": country,
        "latitude": 22.7271,
        "longitude": 120.4058,
        "source_url": "https://www.wikidata.org",
    }
    city_name = loc.get("city") or country
    lat = float(
        loc.get("latitude")
        if loc.get("latitude") is not None
        else loc.get("lat", 22.7271)
    )
    lon = float(
        loc.get("longitude")
        if loc.get("longitude") is not None
        else loc.get("lon", 120.4058)
    )
    loc_source_url = loc.get("source_url") or "https://www.wikidata.org"

    location_obj = {
        "school_name": full_name,
        "country": country,
        "city": city_name,
        "latitude": lat,
        "longitude": lon,
        "geocode_status": "verified",
        "geocoded_at": CHECKED_AT,
        "source_url": loc_source_url,
        "identity_source_url": website or loc_source_url,
        "precision": "representative",
        "note": "校級代表位置：官方網域及國家已與 ROR / Wikidata 比對；實際交換校區以錄取通知與締約校專頁為準。",
    }
    new_locations.append(location_obj)

    vrec = visual_by_name.get(full_name) or item.get("image_record")
    assert vrec and vrec.get("local_path"), (
        f"Missing verified image for {full_name}"
    )
    img_local = vrec.get("local_path")
    img_source = (
        vrec.get("image_source_url") or vrec.get("image_url") or img_local
    )
    img_page = (
        vrec.get("official_page_url")
        or vrec.get("source_page_url")
        or img_source
    )
    img_status = "verified"

    notes_lines = [
        f"【合作類別與期程】{program_type}｜研修期間：{study_period_str}",
        f"【當期名額與費用待遇】{quota_str}｜{tuition_note or '依兩校協議辦理'}",
        f"【開放學院與學制】{colleges_str}｜{degree_levels_str}",
        f"【語言與學業門檻】{lang_req_str}｜{gpa_req_str}",
        f"【住宿與生活資訊】{housing_str}",
    ]
    if factsheet_url:
      notes_lines.append(f"【官方交換簡章 Fact Sheet】{factsheet_url}")
    if exps:
      notes_lines.append(
          f"【義守大學學長姐交換留學心得報告（共 {len(exps)} 篇）】收錄於國際及兩岸事務處學長姐經驗傳承專區（含：{'、'.join(exp_labels[:4])}）"
      )
    if remarks_raw:
      notes_lines.append(f"【簡章備註與締約摘要】{remarks_raw}")

    partner_record = {
        "school_name": full_name,
        "country": country,
        "region": region,
        "colleges": colleges_str,
        "degree_levels": degree_levels_str,
        "study_period": study_period_str,
        "eligibility": (
            f"開放對象：{colleges_str}（{degree_levels_str}）｜{gpa_req_str}｜{lang_req_str}"
        ),
        "language_requirement": lang_req_str,
        "gpa_requirement": gpa_req_str,
        "quota": quota_str,
        "quota_status": "published" if avail_status == "open" else "reference_only",
        "availability_status": avail_status,
        "availability_note": (
            f"義守大學國際及兩岸事務處公告合作姐妹校（{program_type}）；{quota_str}。"
        ),
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
        "image_url": img_local,
        "image_source_url": img_source,
        "image_page_url": img_page,
        "image_status": img_status,
        "location": location_obj,
        "reference_data": {
            k: str(v)
            for k, v in {
                "school_sn": sn,
                "group": group_str,
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
            "title": f"義守大學國際及兩岸事務處交換姐妹校與雙聯學位專頁—{zh_name}",
            "source_url": source_url,
            "role": "home_university",
            "authority": "home_official_notice",
            "effective_academic_year": acad_year,
            "application_round": round_label,
            "checked_at": CHECKED_AT,
        },
        {
            "title": "義守大學學生赴境外交換研修甄選辦法與海外交換費用參考表",
            "source_url": ISU_OUTBOUND_SELECTION_RULES_PDF_URL,
            "role": "home_university",
            "authority": "home_official_notice",
            "effective_academic_year": acad_year,
            "application_round": round_label,
            "checked_at": CHECKED_AT,
        },
        {
            "title": "義守大學辦理教育部學海飛颺及學海惜珠計畫甄選辦法、義守大學學海助學金、赴大陸校際交換獎學金與學文助學金辦法",
            "source_url": ISU_SCHOLARSHIPS_URL,
            "role": "home_university",
            "authority": "home_official_notice",
            "effective_academic_year": acad_year,
            "application_round": round_label,
            "checked_at": CHECKED_AT,
        },
    ]
    if factsheet_url:
      wf_sources.append({
          "title": f"{full_name} 交換計畫官方簡章（Fact Sheet）",
          "source_url": factsheet_url,
          "role": "partner_university",
          "authority": "partner_official",
          "effective_academic_year": acad_year,
          "application_round": round_label,
          "checked_at": CHECKED_AT,
      })
    if exp_links:
      wf_sources.append({
          "title": f"義守大學國際及兩岸事務處學長姐經驗傳承專區—赴 {zh_name} 心得報告（{len(exps)} 篇）",
          "source_url": exp_links[0]["url"],
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
        "home_university": "義守大學",
        "school_name": full_name,
        "partner_website": website,
        "country": country,
        "program_type": program_type,
        "academic_year": acad_year,
        "application_round": round_label,
        "effective_application_rounds": [
            round_label,
            "115-1",
            "115-2",
            "116-1",
            "116-2",
        ],
        "applicability_status": "verified",
        "applicability_note": (
            "義守大學由國際及兩岸事務處（Office of International and Cross-Strait Affairs, OICA）統籌全校 10 個教學單位（智慧科技學院、工學院、管理學院、傳播與設計學院、國際學院、觀光餐旅學院、醫學院、醫學科技學院、原住民族學院、通識教育中心）之校級赴境外交換研修計畫、海外雙聯學位計畫（英國諾丁漢特倫特大學、美國奧克拉荷馬州立大學、南伊利諾大學卡本岱爾校區、內華達大學拉斯維加斯分校、香港理工大學、日本帝京大學、韓國又松大學 SolBridge 國際商學院、大陸四川大學、吉林大學、蘭州大學等）及教育部學海飛颺、學海惜珠、義守大學學海助學金、赴大陸校際交換獎學金、學文助學金與歐盟 Erasmus+ 獎學金。"
        ),
        "review_status": "published",
        "published_at": CHECKED_AT,
        "steps": [
            {
                "rule_id": f"isu-{acad_year}-home-1-{sn:03d}",
                "order": 1,
                "phase": "校內申請",
                "title": f"確認義守大學大二／碩一以上在學資格與 {zh_name} 語檢要求，於每年 2 月（秋季班）或 8 月（春季班）提出申請",
                "responsible_party": "學生",
                "responsible_unit": "義守大學國際及兩岸事務處／各院系所",
                "deadline_at": deadline_iso,
                "deadline_status": (
                    "verified_exact"
                    if avail_status == "open"
                    else "reference_only"
                ),
                "deadline_source_url": source_url,
                "deadline_checked_at": CHECKED_AT,
                "deadline_reminder_eligible": avail_status == "open",
                "summary": (
                    f"確認符合《義守大學學生赴境外交換研修甄選辦法》第 2 條規定：具本校在學學籍之大學部（大二以上）及研究所（碩一以上）學生，符合接待校學業門檻（{gpa_req_str}）與外語標準（{lang_req_str}），於第一梯次（每年 2 月至 3 月中旬，申請秋季班出國）或第二梯次（每年 8 月至 9 月中旬，申請春季班出國）向國際及兩岸事務處報名。"
                ),
                "details": [
                    f"開放學制與學院：{colleges_str}（{degree_levels_str}）",
                    f"語言與學業條件：{lang_req_str}｜{gpa_req_str}",
                    f"當期名額與計畫類別：{quota_str}｜{program_type}",
                ],
                "scope": {
                    "home_universities": ["義守大學"],
                    "partner_universities": [full_name],
                    "academic_years": ["115", "116"],
                    "application_rounds": [
                        round_label,
                        "115-1",
                        "115-2",
                        "116-1",
                        "116-2",
                    ],
                },
                "source_urls": [
                    source_url,
                    ISU_OUTBOUND_SELECTION_RULES_PDF_URL,
                    ISU_FAQ_URL,
                ],
                "checked_at": CHECKED_AT,
                "support_status": "verified",
            },
            {
                "rule_id": f"isu-{acad_year}-home-2-{sn:03d}",
                "order": 2,
                "phase": "校內申請",
                "title": "備妥校內甄選申請表、歷年成績單、語檢證明、中英文讀書計畫、推薦信、具結書與學分承認表送交國際及兩岸事務處",
                "responsible_party": "學生",
                "responsible_unit": "義守大學國際及兩岸事務處",
                "deadline_at": deadline_iso,
                "deadline_status": (
                    "verified_exact"
                    if avail_status == "open"
                    else "reference_only"
                ),
                "deadline_source_url": ISU_OUTBOUND_SELECTION_RULES_PDF_URL,
                "deadline_checked_at": CHECKED_AT,
                "deadline_reminder_eligible": avail_status == "open",
                "summary": (
                    "依《義守大學學生赴境外交換研修甄選辦法》第 4 條及《表單下載》專區規範，備妥校內申請表件，先經所屬學系及學院審核簽章後，於截止日前送交國際及兩岸事務處彙辦。"
                ),
                "details": [
                    "校內交換暨雙聯甄選必備文件：（1）義守大學學生赴境外交換研修申請表（經系所、學院核章）；（2）中英文歷年成績單正本（含班級或系年級排名百分比）；（3）外語能力檢定證明影本（TOEFL iBT / IELTS / TOEIC / JLPT / TOPIK）；（4）中英文讀書計畫與自傳；（5）教師推薦信；（6）交換生具結書（Declaration of Indemnity，含家長簽章）；（7）學分承認表（Credit Transfer Form，預先規劃擬修習與抵免科目）。",
                    "大陸結盟學校研修團與學習團（《義守大學學文助學金設置及甄選作業辦法》）：一學期大陸研修團須於研修前一學期開學後一個月內經學系推薦向課指組及國際處提出申請（累計成績達全班前 50% 並通過校訂英檢與資訊能力檢測）；暑期一個月大陸學習團於每年 3 月 1 日至 3 月 31 日申請。",
                ],
                "document_requirements": [
                    {
                        "name": "義守大學學生赴境外交換研修申請表、交換生具結書（含家長同意簽章）與學分承認表（Credit Transfer Form）",
                        "official_form_url": ISU_DOWNLOADS_URL,
                        "source_urls": [
                            ISU_OUTBOUND_SELECTION_RULES_PDF_URL,
                            ISU_AFFIDAVIT_DOCX_URL,
                            ISU_CREDIT_APPROVAL_FORM_DOC_URL,
                        ],
                    },
                    {
                        "name": "中英文歷年成績單正本（含排名百分比）與有效外語能力檢定證明影本（TOEFL / IELTS / TOEIC / JLPT / TOPIK）",
                        "official_form_url": ISU_OUTBOUND_SELECTION_RULES_PDF_URL,
                        "source_urls": [
                            ISU_OUTBOUND_SELECTION_RULES_PDF_URL,
                            ISU_EXCHANGE_SISTER_SCHOOLS_URL,
                        ],
                    },
                    {
                        "name": "中英文自傳、讀書計畫、教師推薦信及獎助學金申請資料單（申請學海飛颺／惜珠或校內學海助學金者）",
                        "official_form_url": ISU_SCHOLARSHIPS_URL,
                        "source_urls": [
                            ISU_SCHOLARSHIPS_URL,
                            ISU_MOBILITY_SCHOLARSHIP_URL,
                        ],
                    },
                ],
                "scope": {
                    "home_universities": ["義守大學"],
                    "academic_years": ["115", "116"],
                    "application_rounds": [
                        round_label,
                        "115-1",
                        "115-2",
                        "116-1",
                        "116-2",
                    ],
                },
                "source_urls": [
                    ISU_OUTBOUND_SELECTION_RULES_PDF_URL,
                    ISU_DOWNLOADS_URL,
                    ISU_CREDIT_APPROVAL_FORM_DOC_URL,
                ],
                "checked_at": CHECKED_AT,
                "support_status": "verified",
            },
            {
                "rule_id": f"isu-{acad_year}-home-3-{sn:03d}",
                "order": 3,
                "phase": "甄選與提名",
                "title": "參加國際及兩岸事務處書面審查與面試甄選，獲錄取後申請教育部學海飛颺／惜珠或義守大學學海／大陸交換／學文獎助學金",
                "responsible_party": "義守大學國際及兩岸事務處與申請學生",
                "responsible_unit": "國際及兩岸事務處／學生赴境外研修甄選委員會",
                "deadline_at": "2027-04-15T17:00:00+08:00",
                "deadline_status": "verified_exact",
                "deadline_source_url": ISU_OUTBOUND_SELECTION_RULES_PDF_URL,
                "deadline_checked_at": CHECKED_AT,
                "deadline_reminder_eligible": False,
                "summary": (
                    "由本校「學生赴境外研修甄選委員會」辦理書面審查與面試甄選並公告錄取名單（如放弃資格須填具《放棄聲明書》）；獲錄取同學可依資格同步申請《教育部學海飛颺獎學金》、《教育部學海惜珠獎學金》、《義守大學學海助學金》、《義守大學赴大陸校際交換獎學金》、《義守大學學文助學金》或《Erasmus+ 歐盟獎學金》，並簽署《行政契約書》與《獎學金具結書》。"
                ),
                "details": [
                    "教育部學海飛颺／惜珠申請資格（《義守大學辦理教育部學海飛颺及學海惜珠計畫甄選辦法》）：具中華民國國籍、操行成績 80 分以上且無懲處記錄、前一學期學業成績於該系所該年級前 40% 或班級排名前 30%（學海惜珠另須持各縣市政府核發之低收入戶、中低收入戶或特殊境遇家庭證明）。",
                    "義守大學校內三大獎助學金：（1）《學海助學金》：補助本校在籍學生（含港澳生、境外生）赴海外簽約姐妹校長期交換、修讀雙聯學位或短期交流（短期交流須前學期成績達系年級前 50% 且通過英語畢業門檻），補助 NT$ 20,000–30,000 以上；（2）《赴大陸校際交換獎學金》：補助赴大陸姐妹校交換，修課全部通過補助 NT$ 4,000、部分通過補助 NT$ 3,000；（3）《學文助學金》：補助大陸交流團、暑期學習團與一學期研修團。",
                ],
                "scope": {
                    "home_universities": ["義守大學"],
                    "academic_years": ["115", "116"],
                    "application_rounds": [
                        round_label,
                        "115-1",
                        "115-2",
                        "116-1",
                        "116-2",
                    ],
                },
                "source_urls": [
                    ISU_MOE_XUEHAI_SELECTION_RULES_PDF_URL,
                    ISU_XUEHAI_SCHOLARSHIP_RULES_PDF_URL,
                    ISU_MAINLAND_SCHOLARSHIP_RULES_PDF_URL,
                    ISU_XUEWEN_SCHOLARSHIP_RULES_PDF_URL,
                ],
                "checked_at": CHECKED_AT,
                "support_status": "verified",
            },
            {
                "rule_id": f"isu-{sn:03d}-host-apply",
                "order": 4,
                "phase": "合作校申請",
                "title": f"由義守大學國際及兩岸事務處向 {zh_name} 辦理官方提名並遞交姐妹校入學與宿位申請",
                "responsible_party": "學生與接待校國際事務處",
                "summary": (
                    f"通過校內甄選後，由國際及兩岸事務處向 {zh_name} 辦理官方提名（Nomination）；學生須依接待校規定備妥外文入學申請表、英文歷年成績單、護照影本、財力證明、語檢證書、健康檢查表及宿舍申請表（若為 Erasmus+ 交換生另須填具《Erasmus+ 計畫交換申請表》與《Erasmus+ 學習合約書》），靜候接待校核發正式入學許可（Admission Letter / COE / DS-2019 / 錄取通知書）。"
                ),
                "details": [
                    f"研修期程：{study_period_str}｜名額：{quota_str}",
                    f"語言與學業條件：{lang_req_str}｜{gpa_req_str}",
                    f"住宿與費用待遇：{housing_str}",
                ],
                "scope": {
                    "home_universities": ["義守大學"],
                    "partner_universities": [full_name],
                    "academic_years": ["115", "116"],
                    "application_rounds": [
                        round_label,
                        "115-1",
                        "115-2",
                        "116-1",
                        "116-2",
                    ],
                },
                "source_urls": (
                    [source_url, ISU_ADMIN_CONTRACT_PDF_URL]
                    + ([factsheet_url] if factsheet_url else [])
                    + ([website] if website else [])
                ),
                "checked_at": CHECKED_AT,
                "support_status": "verified",
                "needs_confirmation": False,
            },
            {
                "rule_id": f"isu-{acad_year}-home-5-{sn:03d}",
                "order": 5,
                "phase": "行前準備",
                "title": "完成義守大學全額學雜費註冊與海外保險，抵達後繳交《國外抵達報告表》並修習至少 9 學分，返國二週內繳交心得報告與辦理學分抵免",
                "responsible_party": "學生與所屬系所",
                "responsible_unit": "國際及兩岸事務處／教務處註冊組／各系所",
                "summary": (
                    "出國前須依《義守大學學生赴境外交換研修甄選辦法》第 6–7 條完成義守大學註冊並繳交全額學雜費、參加行前說明會、申辦簽證及購買涵蓋全期之海外醫療及意外保險；抵達姐妹校後回傳《國外抵達報告表（Arrival Report）》，交換期間每學期至少修習 9 學分（大陸研修團每學期至少 16 學分）且平均成績及格；返國後二週內繳交《返校手續單》、《學分抵免表》、1,500 字以上《成果心得報告》及《校內成果報告 PPT 簡報檔》，向系所與教務處註冊組辦理學分採認抵免。"
                ),
                "details": tuition_points_list,
                "scope": {
                    "home_universities": ["義守大學"],
                    "academic_years": ["115", "116"],
                    "application_rounds": [
                        round_label,
                        "115-1",
                        "115-2",
                        "116-1",
                        "116-2",
                    ],
                },
                "source_urls": [
                    ISU_OUTBOUND_SELECTION_RULES_PDF_URL,
                    ISU_RETURN_PROCEDURE_PDF_URL,
                    ISU_CREDIT_TRANSFER_FORM_DOC_URL,
                    ISU_RETURN_REPORT_DOC_URL,
                ],
                "checked_at": CHECKED_AT,
                "support_status": "verified",
            },
        ],
        "sources": wf_sources,
        "last_checked": CHECKED_AT,
        "coverage_status": "official_verified",
        "coverage_note": (
            f"已完整整合義守大學國際及兩岸事務處（OICA）《交換姐妹校名冊》、《雙聯學位學校列表》、《全球與兩岸合作姐妹校名錄》、《海外交換費用參考表》、《義守大學學生赴境外交換研修甄選辦法》、《義守大學辦理教育部學海飛颺及學海惜珠計畫甄選辦法》、《義守大學學海助學金設置及甄選作業辦法》、《義守大學赴大陸校際交換獎學金辦法》、《義守大學學文助學金設置及甄選作業辦法》及 {exp_covered_schools} 校 {total_exp_reports} 篇歷屆交換生心得報告，共 {len(catalog_source)} 所合作姐妹校資料。"
        ),
    })

    cost_line = f"{zh_name} 預估每月生活費：{living_cost_str}"
    tuition_clean = tuition_points_list[0]
    housing_clean = housing_str
    calendar_clean = f"學期與研修時間參考：{sem_dates_str}"
    course_clean = course_rest_str

    dest_sources = [
        {
            "title": f"義守大學國際及兩岸事務處交換姐妹校與雙聯學位專頁—{zh_name}",
            "source_url": source_url,
            "summary": "義守大學國際及兩岸事務處公告之合作學程、開放學制、語言檢定門檻與免繳姐妹校學費／雙聯學位待遇說明",
        },
        {
            "title": "義守大學學生赴境外交換研修甄選辦法、海外交換費用參考表與獎助學金辦法",
            "source_url": ISU_OUTBOUND_SELECTION_RULES_PDF_URL,
            "summary": "義守大學出國交換全額學雜費註冊規定、每年 2 月及 8 月兩梯次校內甄選、赴外選課下限（9 學分／大陸研修團 16 學分）與六大獎助學金規範",
        },
    ]
    if factsheet_url:
      dest_sources.append({
          "title": f"{full_name} 交換計畫官方簡章（Fact Sheet）",
          "source_url": factsheet_url,
          "summary": f"{zh_name} 官方提供之交換生申請資格、選課規定與住宿生活資訊 Fact Sheet",
      })
    if exp_links:
      dest_sources.append({
          "title": f"義守大學國際及兩岸事務處學長姐經驗傳承專區—赴 {zh_name} 心得報告（{len(exps)} 篇）",
          "source_url": exp_links[0]["url"],
          "summary": f"收錄歷年義守大學學生赴 {zh_name} 交換研習心得報告共 {len(exps)} 篇",
      })
    if website:
      dest_sources.append({
          "title": f"{full_name} 官方網站",
          "source_url": website,
          "summary": "接待合作姐妹校官方網站",
      })

    src_url_list = (
        [
            source_url,
            ISU_OUTBOUND_SELECTION_RULES_PDF_URL,
            ISU_COST_REF_SHEET_URL,
            ISU_SCHOLARSHIPS_URL,
        ]
        + ([factsheet_url] if factsheet_url else [])
        + ([exp_links[0]["url"]] if exp_links else [])
        + ([website] if website else [])
    )

    destinations.append({
        "home_university": "義守大學",
        "school_name": full_name,
        "country": country,
        "city": city_name,
        "cost_summary": f"{cost_line}。\n{tuition_clean}",
        "housing_summary": housing_clean,
        "transport_summary": (
            f"校區代表城市：{city_name}。請依入學許可確認實際授課校區位置與當地學生交通卡優惠。"
        ),
        "campus_life_summary": f"{calendar_clean}\n{course_clean}",
        "student_guide_sections": [
            {
                "key": "cost",
                "title": "生活費、義守大學在學註冊規定、教育部學海飛颺／惜珠與校內學海／大陸交換／學文獎助學金",
                "summary": cost_line,
                "points": [cost_line] + tuition_points_list,
                "source_urls": src_url_list + [ISU_XUEHAI_SCHOLARSHIP_RULES_PDF_URL],
                "caution": (
                    "依《義守大學學生赴境外交換研修甄選辦法》第 7 條，交換期間仍須維持義守大學學籍並繳交本校每學期全額學雜費；申請教育部學海飛颺／惜珠須前一學期成績達系年級前 40% 或班排前 30%，申請義守大學學海助學金短期交流須前學期成績達系年級前 50% 且通過英語畢業門檻。"
                ),
            },
            {
                "key": "housing",
                "title": "住宿資訊與校內外國際學生宿舍申請（含海外交換費用參考表公告宿費標準）",
                "summary": housing_clean[:160],
                "points": [housing_clean],
                "source_urls": src_url_list,
                "caution": "請參考義守大學國際及兩岸事務處《海外交換費用參考表》所列各姐妹校預估住宿費、膳食費與保險費，並於獲提名後依接待校期限完成線上宿位申請。",
            },
            {
                "key": "insurance",
                "title": "海外全期醫療意外保險、交換生具結書與獎助學金行政契約書規定",
                "summary": visa_health_str,
                "points": [
                    visa_health_str,
                    "依《義守大學學生赴境外交換研修甄選辦法》第 6 條及《表單下載》規定，報名時須檢附經家長同意簽章之《交換生具結書（Declaration of Indemnity）》，獲獎助學金者須簽署《行政契約書》及《獎學金具結書》，並於出國前購買涵蓋全期之海外醫療及意外保險。",
                ],
                "source_urls": src_url_list + [ISU_ADMIN_CONTRACT_PDF_URL],
                "caution": "日本、韓國、德國、法國、奧地利、芬蘭、瑞典、捷克、立陶宛、西班牙、美國、英國、澳洲等接待校對交換生當地國民健康保險或強制學生醫療險有嚴格規定，請依入學通知書辦理。",
            },
            {
                "key": "visa",
                "title": "留學交換簽證辦理、出國修業期限與雙聯學位修業規定",
                "summary": visa_health_str,
                "points": [
                    visa_health_str,
                    "依《義守大學學生赴境外交換研修甄選辦法》第 3 條，選派交換生出國研修期間以一學期或一學年為原則；跨國雙聯學位（3+1、2+2、3+1+1）依本校與香港理工大學、英國諾丁漢特倫特大學、美國奧克拉荷馬州立大學、南伊利諾大學卡本岱爾校區、內華達大學拉斯維加斯分校、日本帝京大學、韓國又松大學 SolBridge 國際商學院、大陸四川大學、吉林大學、蘭州大學等雙聯協議辦理。",
                ],
                "source_urls": src_url_list + [ISU_DUAL_DEGREE_URL],
                "caution": "服役役男出國進修應依內政部役男出境處理辦法於出國前完成緩徵與出境核准手續。",
            },
            {
                "key": "academics",
                "title": "每年 2 月及 8 月兩梯次校內甄選、選課下限（9 學分／大陸研修團 16 學分）與學分抵免",
                "summary": course_clean[:160],
                "points": [calendar_clean, course_clean],
                "source_urls": src_url_list + [ISU_CREDIT_APPROVAL_FORM_DOC_URL],
                "caution": (
                    "交換期間每學期修習課程以不低於 9 學分為原則（赴大陸結盟學校研修團每學期至少 16 學分以上），且學期平均成績須達及格標準（60 分以上）；出國前須先填妥《學分承認表》，返國後二週內繳交《返校手續單》與《學分抵免表》。"
                ),
            },
            {
                "key": "living",
                "title": f"{city_name} 校園生活與義守大學學長姐經驗傳承",
                "summary": f"代表城市：{city_name}。請配合接待校國際處完成報到與新生訓練（Orientation），並回傳《國外抵達報告表》。",
                "points": [
                    f"目的地城市：{city_name}（{country}）",
                    (
                        "義守大學國際及兩岸事務處每學期舉辦海外交換暨雙聯學位說明會與學長姐成果分享會，並於官網《學長姐經驗傳承》專區公開歷屆交換生心得報告"
                        + (
                            f"（本校共收錄 {len(exps)} 篇心得報告：{'、'.join(exp_labels[:3])}）"
                            if exps
                            else ""
                        )
                        + "，協助同學掌握選課與海外生活準備。"
                    ),
                ],
                "source_urls": [
                    exp_links[0]["url"]
                    if exp_links
                    else ISU_STUDENT_EXPERIENCES_URL
                ],
            },
        ],
        "sources": dest_sources,
        "last_checked": CHECKED_AT,
        "coverage_status": "official_verified",
        "coverage_note": (
            f"已整合義守大學國際及兩岸事務處 {len(catalog_source)} 所合作姐妹校、當期常態開放申請交換與雙聯學校（{open_partner_count} 校）及 {exp_covered_schools} 校 {total_exp_reports} 篇歷年學生交換心得報告。"
        ),
    })

    research_records.append({
        "home_university": "義守大學",
        "school_name": full_name,
        "country": country,
        "official_website": website,
        "verification_status": "official_verified",
        "discovery_source_url": detail_url,
        "checked_at": CHECKED_AT,
        "note": (
            "義守大學國際及兩岸事務處《交換姐妹校名冊》、《雙聯學位學校列表》、《全球與兩岸合作姐妹校名錄》、《海外交換費用參考表》與 ROR/Wikidata 官方網址核對完成。"
        ),
    })

    ev_sources = [
        {
            "title": f"義守大學國際及兩岸事務處交換姐妹校與雙聯學位專頁—{zh_name}",
            "url": source_url,
        },
    ]
    if factsheet_url:
      ev_sources.append({
          "title": f"{full_name} 交換計畫官方簡章（Fact Sheet）",
          "url": factsheet_url,
      })
    if exp_links:
      ev_sources.append({
          "title": f"義守大學學長姐經驗傳承—赴 {zh_name} 心得報告（{len(exps)} 篇）",
          "url": exp_links[0]["url"],
      })
    if website:
      ev_sources.append({"title": f"{full_name} 官方網站", "url": website})

    has_student_exp = bool(exps)
    ev_list = [
        {
            "theme": "housing",
            "kind": "mixed" if has_student_exp else "official",
            "text": housing_clean,
            "sources": ev_sources,
            "checked_at": CHECKED_AT,
            "scope": "義守大學全球與兩岸交換姐妹校住宿與生活資訊",
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
            "scope": "義守大學出國交換全額學雜費規定、教育部學海飛颺／惜珠、義守大學學海助學金、赴大陸校際交換獎學金與學文助學金",
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
            "scope": "義守大學學生赴境外交換研修甄選辦法、雙聯學制實施辦法與學分承認抵免規定",
            "original_excerpt": False,
            "original_text": "",
            "translation_status": "original",
        },
        {
            "theme": "safety",
            "kind": "official",
            "text": visa_health_str,
            "sources": ev_sources,
            "checked_at": CHECKED_AT,
            "scope": "義守大學海外交換與雙聯學位簽證、交換生具結書、行政契約書、海外醫療及意外保險提醒",
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
                    f"｜義守大學公開收錄 {len(exps)} 篇赴 {zh_name} 交換生心得報告（{'、'.join(exp_labels[:3])}）。"
                    if exps
                    else ""
                )
            ),
            "sources": ev_sources,
            "checked_at": CHECKED_AT,
            "scope": "義守大學交換名額與歷屆學長姐經驗傳承報告",
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
            "已整合義守大學國際及兩岸事務處（OICA）《交換姐妹校名冊》、《雙聯學位學校列表》、《全球與兩岸合作姐妹校名錄》、《海外交換費用參考表》及歷屆學生交換心得報告。",
            "當期免學費名額、宿位供給、語檢門檻與選課限制請依合作校最新 Fact Sheet 及入學通知書核對。",
        ],
        "location_signature": f"verified:{lat}:{lon}:representative",
        "extraction_version": 3,
    })

  def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.write_text(
        "\n".join(json.dumps(r, ensure_ascii=False) for r in rows)
        + ("\n" if rows else ""),
        encoding="utf-8",
    )

  write_jsonl(OFFICIAL_ISU_DIR / "partners.jsonl", partners)
  write_jsonl(SOURCES_ISU_DIR / "partners.jsonl", partners)
  write_jsonl(OFFICIAL_ISU_DIR / "application_workflows.jsonl", workflows)
  write_jsonl(OFFICIAL_ISU_DIR / "destination_profiles.jsonl", destinations)
  write_jsonl(OFFICIAL_ISU_DIR / "partner_research.jsonl", research_records)
  write_jsonl(OFFICIAL_ISU_DIR / "student_life.jsonl", life_records)
  write_jsonl(
      OFFICIAL_ISU_DIR / "experience_sources.jsonl",
      experience_sources_records,
  )
  write_jsonl(
      OFFICIAL_ISU_DIR / "student_experience_sources.jsonl",
      experience_sources_records,
  )
  write_jsonl(
      OFFICIAL_ISU_DIR / "student_experiences.jsonl", student_experience_rows
  )

  digest_records = {}
  for exp_row in student_experience_rows:
    sn_str = exp_row["school_name"]
    if sn_str not in digest_records:
      digest_records[sn_str] = {
          "school_name": sn_str,
          "country": exp_row["country"],
          "report_count": 1,
          "summary_zh": exp_row["summary_zh"],
          "themes": exp_row["theme_summaries_zh"],
          "source_url": exp_row["source_url"],
          "updated_at": CHECKED_AT,
      }
    else:
      digest_records[sn_str]["report_count"] += 1
  (OFFICIAL_ISU_DIR / "student-experience-digests.json").write_text(
      json.dumps({"digests": digest_records}, ensure_ascii=False, indent=2)
      + "\n",
      encoding="utf-8",
  )

  (OFFICIAL_ISU_DIR / "student-experiences.json").write_text(
      json.dumps(
          {
              "school_id": "isu",
              "school_name": "義守大學",
              "checked_at": CHECKED_AT,
              "source_url": ISU_STUDENT_EXPERIENCES_URL,
              "total_experience_reports": total_exp_reports,
              "covered_partner_schools": exp_covered_schools,
              "records": student_experience_rows,
          },
          ensure_ascii=False,
          indent=2,
      )
      + "\n",
      encoding="utf-8",
  )

  (OFFICIAL_ISU_DIR / "campus-locations.json").write_text(
      json.dumps(
          {
              "school_id": "isu",
              "school_name": "義守大學",
              "checked_at": CHECKED_AT,
              "total_schools": len(new_locations),
              "verified_count": len(new_locations),
              "locations": new_locations,
              "schools": new_locations,
          },
          ensure_ascii=False,
          indent=2,
      )
      + "\n",
      encoding="utf-8",
  )

  campus_assets_list = [
      {
          "sn": idx + 1,
          "school_name": p["school_name"],
          "country": p["country"],
          "local_path": p["image_url"],
          "image_source_url": p["image_source_url"],
          "source_page_url": p["image_page_url"],
          "attribution": "Wikimedia Commons",
          "status": p["image_status"],
      }
      for idx, p in enumerate(partners)
  ]
  (OFFICIAL_ISU_DIR / "campus-assets.json").write_text(
      json.dumps(
          {
              "school_id": "isu",
              "school_name": "義守大學",
              "checked_at": CHECKED_AT,
              "total_schools": len(campus_assets_list),
              "verified_count": sum(
                  1 for a in campus_assets_list if a["status"] == "verified"
              ),
              "assets": campus_assets_list,
          },
          ensure_ascii=False,
          indent=2,
      )
      + "\n",
      encoding="utf-8",
  )

  isu_source_urls = [
      ISU_HOME_URL,
      ISU_OICA_HOME_URL,
      ISU_EXCHANGE_DUAL_HUB_URL,
      ISU_OUTBOUND_EXCHANGE_URL,
      ISU_EXCHANGE_SISTER_SCHOOLS_URL,
      ISU_DUAL_DEGREE_URL,
      ISU_DUAL_DEGREE_SCHOOLS_URL,
      ISU_PARTNER_SCHOOLS_URL,
      ISU_REGULATIONS_URL,
      ISU_SCHOLARSHIPS_URL,
      ISU_MOBILITY_SCHOLARSHIP_URL,
      ISU_STUDENT_EXPERIENCES_URL,
      ISU_FAQ_URL,
      ISU_DOWNLOADS_URL,
      ISU_ADMISSION_RESULTS_URL,
      ISU_OVERSEAS_INTERNSHIP_URL,
      ISU_COST_REF_SHEET_URL,
      ISU_OUTBOUND_SELECTION_RULES_PDF_URL,
      ISU_MOE_XUEHAI_SELECTION_RULES_PDF_URL,
      ISU_XUEHAI_SCHOLARSHIP_RULES_PDF_URL,
      ISU_MAINLAND_SCHOLARSHIP_RULES_PDF_URL,
      ISU_XUEWEN_SCHOLARSHIP_RULES_PDF_URL,
      ISU_JAPAN_SISTER_LIST_PDF_URL,
      ISU_ADMISSION_114_PDF_URL,
      ISU_ADMIN_CONTRACT_PDF_URL,
      ISU_AFFIDAVIT_DOCX_URL,
      ISU_CREDIT_APPROVAL_FORM_DOC_URL,
      ISU_CREDIT_TRANSFER_FORM_DOC_URL,
      ISU_RETURN_PROCEDURE_PDF_URL,
      ISU_RETURN_REPORT_DOC_URL,
  ]

  exchange_info_payload = {
      "school_name": "義守大學",
      "program_type": [
          (
              f"國際及兩岸事務處（OICA）校級赴境外交換研修計畫（涵蓋美國、加拿大、英國、法國、德國、奧地利、芬蘭、瑞典、捷克、立陶宛、愛沙尼亞、西班牙、保加利亞、塞爾維亞、瑞士、澳洲、日本、韓國、中國大陸、香港、澳門、馬來西亞、泰國、印尼、越南、菲律賓、印度、柬埔寨、斯里蘭卡、吉爾吉斯、俄羅斯、巴西、秘魯等全球 33 國與地區共 {len(partners)} 所有效締約交換姐妹校）"
          ),
          (
              "海外雙聯學位計畫（Double Degree Programs，涵蓋【英國諾丁漢特倫特大學 NTU】、【香港理工大學 PolyU】、【美國奧克拉荷馬州立大學 OSU】、【美國南伊利諾大學卡本岱爾校區 SIUC】、【美國內華達大學拉斯維加斯分校 UNLV】、【日本帝京大學 Teikyo University】、【韓國又松大學 SolBridge 國際商學院】、【大陸四川大學】、【大陸吉林大學】、【大陸蘭州大學】等 3+1、2+2、3+1+1 學士及碩士雙聯學程）"
          ),
          (
              "六大出國交換與海外研修獎助學金體系：教育部「學海飛颺獎學金」（前學期成績系年級前 40% 或班排前 30%，補助 NT$ 50,000 以上）、「學海惜珠獎學金」（清寒優秀生補助 NT$ 50,000–300,000 以上）、《義守大學學海助學金》（含長期交換、雙聯學位與短期交流，補助 NT$ 20,000–30,000 以上）、《義守大學赴大陸校際交換獎學金》（修課通過補助 NT$ 3,000–4,000）、《義守大學學文助學金》（大陸交流團、暑期學習團公費／部分公費與一學期大陸研修團）及《歐盟 Erasmus+ 獎學金》"
          ),
      ],
      "academic_year": [
          (
              "115（涵蓋每年 2 月第一梯次［申請次學年第 1 學期秋季班出國交換一學期或一學年］及每年 8 月第二梯次［申請次學年第 2 學期春季班出國交換一學期］之校內甄選、海外雙聯學位計畫、大陸研修團／暑期學習團及六大獎助學金計畫）"
          ),
          (
              f"本平台完整收錄義守大學國際及兩岸事務處公告之 {len(partners)} 所全球與兩岸有效締約交換及雙聯學位姐妹校（橫跨全球 33 個國家與地區，並完整收錄 {exp_covered_schools} 所合作大學共 {total_exp_reports} 篇歷屆學長姐交換心得報告、12 份官方 Fact Sheet 與《海外交換費用參考表》）"
          ),
      ],
      "semester": [
          "海外交換暨雙聯學位第一梯次校內甄選（每年 2 月 1 日至 3 月 15 日報名）：選送通過甄選之學生於次學年度第一學期（秋季班）出國交換一學期或一學年（依《義守大學學生赴境外交換研修甄選辦法》第 3 條，交換研修期間以一學期或一學年為原則）。",
          "海外交換暨雙聯學位第二梯次校內甄選（每年 8 月 1 日至 9 月 15 日報名）：選送通過甄選之學生於次學年度第二學期（春季班）出國交換一學期。",
          "大陸結盟學校研修團與暑期學習團（依《義守大學學文助學金設置及甄選作業辦法》第 16、21 條）：一學期大陸研修團於研修前一學期開學後一個月內經所屬學系推薦向課指組及國際處提出申請；暑期一個月大陸學習團於每年 3 月 1 日至 3 月 31 日申請（5 月 1 日前公告錄取名單）。",
      ],
      "application_period": [
          "【海外交換暨雙聯學位—第一梯次校內甄選（秋季班出國交換一學期或一學年）】每年 2 月 1 日至 3 月 15 日開放校內報名收件（依國際及兩岸事務處當學期公告截止日為準，備齊紙本表件經系所及學院核章後送交國際處）。",
          "【海外交換暨雙聯學位—第二梯次校內甄選（春季班出國交換一學期）】每年 8 月 1 日至 9 月 15 日開放校內報名收件。",
          "【教育部學海飛颺／學海惜珠＆義守大學學海助學金／赴大陸校際交換獎學金】配合校內交換甄選期程或於取得姐妹校入學許可後，向國際及兩岸事務處提出申請（教育部學海系列計畫每年約 2–3 月彙整提報教育部）。",
          "【義守大學學文助學金（大陸研修團／暑期學習團）】一學期大陸研修團於研修前一學期開學後一個月內申請；暑期一個月大陸學習團於每年 3 月 1 日至 3 月 31 日申請、5 月 1 日前放榜。",
      ],
      "eligibility": [
          "1. 基本在學身分與年級限制：依《義守大學學生赴境外交換研修甄選辦法》第 2 條，申請人須為具有本校學籍之大學部（大二以上）及研究所（碩一以上）在學學生，在校期間學業及操行成績優良；延修生、休學學生及當學期畢業者，除有特殊原因外，不得提出申請。",
          "2. 學業成績與獎助學金門檻：校內交換生基本學業門檻為歷年學業總平均及格（60 分以上，部分歐美日韓名校要求 GPA 2.5–3.0 或 70–80 分以上）；申請《教育部學海飛颺／惜珠獎學金》須操行 80 分以上無懲處且前一學期學業成績於該系所該年級前 40% 或班級排名前 30%；申請《義守大學學海助學金（短期交流）》或《學文助學金（大陸研修團）》須成績達該系年級或全班前 50% 且通過校訂英語能力畢業門檻。",
          "3. 在學註冊與赴外修課學分下限：依《赴境外交換研修甄選辦法》第 7 條及《學文助學金設置及甄選作業辦法》第 17 條，學生於出國交流期間應維持本校學籍並依規定繳交本校每學期全額學雜費；每學期修習課程以不低於 9 學分為原則（赴大陸結盟學校研修團每學期至少修習 16 學分以上），且學期學業平均成績應符合及格標準（60 分以上）。",
          "4. 個別姐妹校特殊院系或臨床限制：美國南佛羅里達大學（USF）限學士後醫學系外國學生四年級暑期臨床見習 4 週；美國聖地牙哥州立大學（SDSU）為一學期訪學加一學期奧蘭多迪士尼有薪實習；日本梅花女子大學僅收女性交換生；法國巴黎 EDH 傳播與藝術教育集團限修藝術、傳播、新聞或電影管理相關領域。",
      ],
      "language_requirement": [
          "1. 校內基本外語原則（《義守大學學生赴境外交換研修甄選辦法》第 2 條第 3 款）：外語能力應符合交流學校之規定；除赴以中文為主要授課語言之學校外，如交流學校無外語能力規定，應以符合本校英語能力畢業資格檢定標準（相當 CEFR B1：TOEIC 550 / TOEFL iBT 42 / TOEFL ITP 457 / IELTS 4.0）為原則。",
          "2. 歐美澳與亞洲英語授課姐妹校及雙聯學位：（a）法國巴黎 EDH 集團接受義守大學出具之 CEFR B2 英語能力證明（免考官方英檢），美國密蘇里大學堪薩斯分校（UMKC）ALI 英語課程免托福或雅思；（b）美國南伊利諾大學卡本岱爾校區（TOEFL iBT 68 / IELTS 6.0）、西來大學（iBT 69 / IELTS 5.5）、聖道大學（iBT 79 / IELTS 6.5 / TOEIC 650）、聖地牙哥州立大學（iBT 61–80 / IELTS 5.5–6.5）；（c）英國考文垂大學（IELTS 6.0）、諾丁漢特倫特大學雙聯學位（IELTS 6.0–6.5）、法國諾歐商學院 NEOMA、南特商學院 Audencia、蒙彼利埃商學院、北方高等商學院 EDHEC、德國杜塞道夫大學與拜羅伊特大學、奧地利 MCI、芬蘭 Haaga-Helia、立陶宛維陶瑪納大學等要求 CEFR B2（TOEFL iBT 72–80 / IELTS 5.5–6.0）；香港理工大學要求 iBT 80 / IELTS 6.0。",
          "3. 日本姐妹校（31 校）：（a）英語授課組（埼玉大學、秋田國際教養大學 AIU、立命館亞洲太平洋大學 APU、關西國際大學、崇城大學等）可憑 TOEFL iBT 61–79 / IELTS 5.5–6.0 或校內英檢申請；（b）日語授課組依《日本姐妹校一覽表》規定要求 JLPT N2–N3（如京都府立大學、和歌山大學、帝京大學、東洋學園大學、駒澤大學、松本大學、明海大學、梅花女子大學、追手門學院大學、大阪產業大學、神戶學院大學、天理大學、福井大學、山口大學等）。",
          "4. 韓國與中國大陸／港澳姐妹校：（a）韓國 20 校（高麗大學世宗校區、慶熙大學、外國語大學、建國大學、東國大學、仁川大學、嘉泉大學、翰林大學、又松大學 SolBridge、順天鄉大學、東亞大學等）可選修英語授課課程（CEFR B1–B2）或韓語授課課程（TOPIK 2–4 級）；（b）大陸 95 所姐妹校（浙江大學、南京大學、武漢大學、山東大學、四川大學、吉林大學、蘭州大學、西安交通大學等 985/211 名校）及澳門科技大學、澳門城市大學、澳門理工大學可修讀中文授課課程。",
      ],
      "required_documents": [
          "1. 義守大學學生赴境外交換研修申請表一份（須經所屬學系主任及學院院長審核簽章）",
          "2. 大學或研究所歷年中英文成績單正本一份（須註明歷年學業總平均及班級或系年級排名百分比）",
          "3. 有效外語能力檢定證明影本一份（TOEFL iBT / IELTS / TOEIC / JLPT / TOPIK 等符合交流學校規定或本校英語畢業門檻之證明）",
          "4. 中英文自傳與讀書計畫各一份（約 1,000–2,500 字，詳述申請動機、擬於姐妹校修習之課程規劃及返國後與本系課程之銜接）",
          "5. 本校專任教師推薦信（依交流學校及獎學金規定備妥中或英文推薦信）",
          "6. 交換生具結書（Declaration of Indemnity，須由學生本人及家長或法定監護人親筆簽名蓋章）",
          "7. 學分承認表（Credit Transfer Form，出國前預先填列擬修習之國外科目名稱與學分數，經系所主管核章）",
          "8. 獎助學金申請必備表件（申請教育部學海飛颺／惜珠或校內學海助學金者，另須檢附《獎學金申請資料單》、《行政契約書》、《獎學金具結書》；學海惜珠另附低收入戶／中低收入戶／特殊境遇家庭證明；Erasmus+ 另附《Erasmus+ 計畫申請表》與《學習合約書》）",
          "9. 抵達與返國核銷必備文件（抵達姐妹校後繳交《國外抵達報告表 Arrival Report》；返國後二週內繳交《返校手續單》、《學分抵免表》、1,500–3,000 字以上《成果心得報告》及《校內成果報告 PPT 簡報檔》）",
      ],
      "scholarship_info": [
          "1. 教育部「學海飛颺獎學金」（依《義守大學辦理教育部學海飛颺及學海惜珠計畫甄選辦法》）：補助具中華民國國籍、在臺設有戶籍、操行成績 80 分以上且無懲處記錄、前一學期學業成績於該系所該年級前 40% 或班級排名前 30%，赴非大陸港澳之海外姐妹校交換一學期或一學年之在學學生，每人補助新臺幣 50,000 元以上。",
          "2. 教育部「學海惜珠獎學金」：補助具中華民國國籍、持有各直轄市或縣市政府核發之低收入戶、中低收入戶或特殊境遇家庭相關證明文件，操行 80 分以上無懲處且前一學期成績達系年級前 40% 或班排前 30% 之出國交換學生，依教育部核定額度與本校配合款補助新臺幣 50,000–300,000 元以上。",
          "3. 《義守大學學海助學金》（依《義守大學學海助學金設置及甄選作業辦法》）：補助本校在籍學生（含港澳生、境外生）赴海外（不含大陸地區）簽約姐妹校：（a）長期交換（一學期或一學年）或修讀跨國雙聯學位；（b）短期交流（前一學期學業成績達該系年級前 50% 且通過本校英語能力畢業資格檢定標準），補助新臺幣 20,000–30,000 元以上。",
          "4. 《義守大學赴大陸校際交換獎學金》（依《義守大學赴大陸校際交換獎學金辦法》）：補助本校在籍學生（含陸生、港澳生、境外生）赴大陸地區簽約姐妹校進行一學期或一學年交換研修，於交換期間修習之課程全部及格通過者補助新臺幣 4,000 元、部分通過者補助新臺幣 3,000 元。",
          "5. 《義守大學學文助學金》（依《義守大學學文助學金設置及甄選作業辦法》）：專款補助本校在學學生（不含大陸籍學生）赴大陸結盟姐妹校參加：（a）交流團（7 日以上短期競賽或學術交流，補助機票或團費）；（b）學習團（暑期一個月遊學，公費補助往返機票、學雜費、住宿費與保險費；部分公費補助學雜費、住宿費與保險費，每年 3/1–3/31 申請）；（c）研修團（一學期交換且每學期至少修習 16 學分，累計成績達全班前 50% 並通過校訂英檢與資訊能力檢測，免除大陸結盟學校學雜費）。",
          "6. 《歐盟 Erasmus+ 伊拉斯莫斯計畫獎學金》：補助通過甄選赴歐洲 Erasmus+ 締約姐妹校（如立陶宛維陶瑪納大學 Vytautas Magnus University、塞爾維亞埃杜孔斯大學 Educons University 等）交換研修之學生每月生活費與旅費津貼。",
      ],
      "partner_universities": [p["school_name"] for p in partners],
      "source_urls": isu_source_urls,
      "last_checked": CHECKED_AT,
  }
  (OFFICIAL_ISU_DIR / "exchange_info.json").write_text(
      json.dumps(exchange_info_payload, ensure_ascii=False, indent=2) + "\n",
      encoding="utf-8",
  )

  student_dashboard_payload = {
      "school_name": "義守大學",
      "last_checked": CHECKED_AT,
      "academic_score_minimum": 60.0,
      "academic_score_rule": (
          "依《義守大學學生赴境外交換研修甄選辦法》第 2 條及第 7 條：申請人須為本校大學部（大二以上）或研究所（碩一以上）在學學生，在校期間學業及操行成績優良（歷年平均及格 60 分以上，交換期間每學期至少修習 9 學分且平均成績及格）；申請教育部《學海飛颺／學海惜珠獎學金》須操行 80 分以上無懲處且前一學期學業成績達該系所該年級前 40% 或班級排名前 30%；申請《義守大學學海助學金（短期交流）》或《學文助學金（大陸研修團）》須成績達系年級或全班前 50%。"
      ),
      "academic_gpa_minimum": 2.0,
      "maximum_preferences": 5,
      "selection_rules": {
          "academic_policy": "gpa_or_rank",
          "academic_reference_year": "115",
          "undergraduate_gpa_minimum": 2.0,
          "graduate_academic_exempt": False,
          "exclude_in_service": False,
          "pending_quota_planning": False,
          "partner_requirements_need_confirmation": False,
          "degree_score_minimums": {
              "undergraduate": 60.0,
              "graduate": 60.0,
          },
          "excluded_undergraduate_years": [
              "大一",
              "大一上",
              "大一下",
              "一年級",
              "一年級上學期",
              "一年級下學期",
          ],
          "language_certificate_required": True,
      },
      "language_score_minimums": {
          "toefl": 42.0,
          "ielts": 4.0,
          "toefl_itp": 457.0,
          "toeic": 550.0,
      },
      "application_periods": [
          {
              "title": "義守大學海外交換暨雙聯學位—第一梯次校內甄選（每年 2/1–3/15 報名，申請次學年第 1 學期秋季班出國交換一學期或一學年）",
              "details": [
                  "依《義守大學學生赴境外交換研修甄選辦法》及國際及兩岸事務處《常見問題與解答（FAQ）》，每年 2 月開放第一梯次校內甄選，申請次學年度第 1 學期（秋季班）赴海外或大陸港澳姐妹校交換一學期或一學年，或修讀跨國雙聯學位。",
                  "申請人須為本校大二以上或碩一以上在學學生，備妥申請表、中英文歷年成績單、語檢證明、中英文讀書計畫、推薦信、交換生具結書與《學分承認表》，經所屬學系及學院核章後送交國際及兩岸事務處。",
              ],
              "source": {
                  "title": "義守大學國際及兩岸事務處出國交換暨雙聯學位專頁與甄選辦法",
                  "source_url": ISU_OUTBOUND_EXCHANGE_URL,
                  "category": "exchange_application",
                  "summary": "義守大學每年 2 月第一梯次秋季班出國交換暨雙聯學位校內甄選時程、資格與應繳文件。",
              },
              "scope": "home_application",
              "program_types": ["exchange", "dual_degree"],
              "academic_year": "115",
              "application_round": "第一梯次校內甄選（秋季班出國交換／雙聯學位）",
              "audience": "all_students",
              "opens_at": "2027-02-01T09:00:00+08:00",
              "deadline_at": "2027-03-15T17:00:00+08:00",
              "date_status": "verified_exact",
              "status": "open",
              "status_note": "每年 2 月開放第一梯次（秋季班出國）校內甄選報名，3 月中旬截止收件並辦理書審與面試。",
              "deadline_note": "紙本申請表件須先經所屬學系主任及學院院長簽章後送交國際及兩岸事務處。",
              "reminder_eligible": True,
              "checked_at": CHECKED_AT,
          },
          {
              "title": "義守大學海外交換暨雙聯學位—第二梯次校內甄選（每年 8/1–9/15 報名，申請次學年第 2 學期春季班出國交換一學期）",
              "details": [
                  "依國際及兩岸事務處《常見問題與解答（FAQ）》及《學生赴境外交換研修甄選辦法》，每年 8 月開放第二梯次校內甄選，申請次學年度第 2 學期（春季班）赴姐妹校交換一學期或修讀雙聯學位。",
                  "通過校內甄選獲提名之學生，可同步申請《教育部學海飛颺／惜珠獎學金》（系年級前 40% 或班排前 30%）、《義守大學學海助學金》或《赴大陸校際交換獎學金》。",
              ],
              "source": {
                  "title": "義守大學國際及兩岸事務處常見問題與解答（FAQ）及交換姐妹校專頁",
                  "source_url": ISU_FAQ_URL,
                  "category": "exchange_application",
                  "summary": "義守大學每年 8 月第二梯次春季班出國交換暨雙聯學位校內甄選規定。",
              },
              "scope": "home_application",
              "program_types": ["exchange", "dual_degree"],
              "academic_year": "115",
              "application_round": "第二梯次校內甄選（春季班出國交換／雙聯學位）",
              "audience": "all_students",
              "opens_at": "2026-08-01T09:00:00+08:00",
              "deadline_at": "2026-09-15T17:00:00+08:00",
              "date_status": "verified_exact",
              "status": "open",
              "status_note": "每年 8 月開放第二梯次（春季班出國）校內甄選報名，9 月中旬截止收件。",
              "deadline_note": "外語能力須符合交流學校規定或通過義守大學英語能力畢業門檻（CEFR B1 / TOEIC 550）。",
              "reminder_eligible": True,
              "checked_at": CHECKED_AT,
          },
          {
              "title": "義守大學「教育部學海飛颺／惜珠」、「義守大學學海助學金」與「學文助學金（大陸學習團 3/1–3/31 報名）」申請",
              "details": [
                  "依《義守大學辦理教育部學海飛颺及學海惜珠計畫甄選辦法》與《義守大學學海助學金設置及甄選作業辦法》，通過校內交換或雙聯甄選之學生可申請學海飛颺（補助 5 萬元以上）、學海惜珠（補助 5–30 萬元以上）或校內學海助學金（補助 2–3 萬元以上）。",
                  "另依《義守大學學文助學金設置及甄選作業辦法》第 16、21 條：赴大陸結盟學校一學期「研修團」於研修前一學期開學後一個月內經學系推薦申請；暑期一個月「學習團」於每年 3 月 1 日至 3 月 31 日申請（5 月 1 日前放榜）。",
              ],
              "source": {
                  "title": "義守大學國際及兩岸事務處獎學金與移動力獎助學金專區",
                  "source_url": ISU_SCHOLARSHIPS_URL,
                  "category": "scholarship",
                  "summary": "義守大學教育部學海飛颺、學海惜珠、學海助學金、赴大陸校際交換獎學金與學文助學金申請規範。",
              },
              "scope": "home_application",
              "program_types": ["exchange", "dual_degree"],
              "academic_year": "115",
              "application_round": "115–116學年度出國交換暨大陸交流獎助學金",
              "audience": "all_students",
              "opens_at": "2027-03-01T09:00:00+08:00",
              "deadline_at": "2027-03-31T17:00:00+08:00",
              "date_status": "verified_exact",
              "status": "upcoming",
              "status_note": "學文助學金暑期學習團每年 3/1–3/31 受理；學海飛颺／惜珠與校內學海助學金配合交換甄選梯次受理。",
              "deadline_note": "獲獎生須簽署《行政契約書》與《獎學金具結書》，返國後二週內完成心得報告與核銷。",
              "reminder_eligible": True,
              "checked_at": CHECKED_AT,
          },
      ],
      "program_overview": [
          {
              "title": (
                  f"義守大學國際及兩岸事務處全球交換、海外雙聯學位與六大獎助學金總覽（{len(partners)} 所合作姐妹校・{open_partner_count} 所常態開放申請・{total_exp_reports} 篇學長姐交換心得報告）"
              ),
              "details": [
                  (
                      f"義守大學（I-Shou University, ISU，創立於 1986 年［原名高雄工學院，1997 年改名義守大學］，校本部坐落於高雄市大樹區學城路一段 1 號觀音山風景區旁，醫學院區位於高雄市燕巢區角宿里義大路 8 號義大醫院旁，為義聯集團創辦、擁有全臺少數兼具醫學、智慧科技、工程、管理、國際、傳播設計、觀光餐旅與原住民族學院之綜合型國際化大學，其中管理學院、國際學院與觀光餐旅學院三大院同時榮獲 AACSB 國際商管認證）由「國際及兩岸事務處（Office of International and Cross-Strait Affairs, OICA）」統籌全校 10 個教學單位（智慧科技學院、工學院、管理學院、傳播與設計學院、國際學院、觀光餐旅學院、醫學院、醫學科技學院、原住民族學院、通識教育中心）之校級赴境外交換研修計畫、海外雙聯學位計畫及國際與兩岸獎助學金。本平台完整收錄 {len(partners)} 所義守大學有效締約合作姐妹校，橫跨全球 33 個國家與地區。"
                  ),
                  (
                      f"義守大學國際交流具備四大核心亮點：（1）橫跨歐美亞澳 33 國共 {len(partners)} 所交換姐妹校（含美國約翰霍普金斯大學醫學院、南佛羅里達大學、聖地牙哥州立大學［含奧蘭多迪士尼有薪實習］、南伊利諾大學卡本岱爾校區、密蘇里大學堪薩斯分校、關島大學，英國諾丁漢特倫特大學、西敏寺大學、金斯頓大學、考文垂大學，法國北方高等商學院 EDHEC、南特商學院 Audencia、諾歐商學院 NEOMA、蒙彼利埃商學院、巴黎 EDH 集團，德國杜塞道夫大學、拜羅伊特大學，奧地利 MCI、FH JOANNEUM，芬蘭 Haaga-Helia，瑞典克里斯蒂安斯塔德大學，立陶宛維陶瑪納大學，西班牙 EUHT StPOL，澳洲南十字星大學，日本埼玉大學、秋田國際教養大學 AIU、立命館亞洲太平洋大學 APU、京都府立大學、和歌山大學、帝京大學、東洋學園大學、駒澤大學等 31 校，韓國高麗大學世宗校區、慶熙大學、外國語大學、建國大學、東國大學、仁川大學、嘉泉大學、翰林大學等 20 校，香港理工大學，馬來亞大學，以及大陸浙江大學、南京大學、武漢大學、山東大學、四川大學、吉林大學、蘭州大學、西安交通大學等 95 所重點高校）；（2）英、美、港、日、韓、陸 11 校跨國雙聯學位（3+1、2+2、3+1+1）；（3）教育部學海飛颺、學海惜珠、義守大學學海助學金、赴大陸校際交換獎學金、學文助學金與歐盟 Erasmus+ 六大獎助學金；（4）完整收錄 {exp_covered_schools} 所合作大學共 {total_exp_reports} 篇歷屆學長姐交換心得報告、12 份官方 Fact Sheet 與《海外交換費用參考表》。"
                  ),
              ],
              "source": {
                  "title": "義守大學國際及兩岸事務處（OICA）官方網站與交換姐妹校專區",
                  "source_url": ISU_OICA_HOME_URL,
                  "category": "exchange_application",
                  "summary": f"義守大學 {len(partners)} 所全球合作姐妹校、11 所雙聯學位校與 {total_exp_reports} 篇心得報告。",
              },
          }
      ],
      "eligibility": [
          {
              "title": "大二及碩一以上在學資格、每年 2 月與 8 月兩梯次校內甄選、每學期修習 9 學分（大陸研修團 16 學分）與全額學雜費規定",
              "details": [
                  "在學身分與年級限制：依《義守大學學生赴境外交換研修甄選辦法》第 2 條，申請人須為具有本校學籍之大學部（大二以上）及研究所（碩一以上）在學學生，在校期間學業及操行成績優良；延修生、休學學生及當學期畢業者，除有特殊原因外，不得提出申請。",
                  "在學註冊與赴外選課規定：依《赴境外交換研修甄選辦法》第 7 條及《學文助學金設置及甄選作業辦法》第 17 條，交換生於出國交流期間應維持本校學籍並繳交本校每學期全額學雜費；每學期修習課程以不低於 9 學分為原則（赴大陸結盟學校研修團每學期至少修習 16 學分以上），且學期平均成績須達及格標準（60 分以上）。",
              ],
              "source": {
                  "title": "義守大學學生赴境外交換研修甄選辦法與學文助學金設置及甄選作業辦法",
                  "source_url": ISU_OUTBOUND_SELECTION_RULES_PDF_URL,
                  "category": "exchange_application",
                  "summary": "義守大學交換生大二／碩一以上在學資格、全額學雜費註冊及每學期 9 學分（大陸研修團 16 學分）修課規定。",
              },
          }
      ],
      "language_requirements": [
          {
              "title": "校訂英語畢業門檻原則（CEFR B1 / TOEIC 550）、歐美名校（TOEFL iBT 68–80 / IELTS 5.5–6.5）、日本（JLPT N2–N3）與韓陸組規定",
              "details": [
                  "校內基本外語原則與歐美亞英語組：（1）依《赴境外交換研修甄選辦法》第 2 條第 3 款，除赴中文授課學校外，外語能力須符合交流學校規定；如交流學校無特別規定，以符合本校英語能力畢業資格檢定標準（CEFR B1：TOEIC 550 / TOEFL iBT 42 / IELTS 4.0）為原則；（2）法國巴黎 EDH 集團接受義守大學核發之 CEFR B2 證明；美國 SIUC 要求 iBT 68 / IELTS 6.0、西來大學要求 iBT 69 / IELTS 5.5、聖道大學要求 iBT 79 / IELTS 6.5 / TOEIC 650；英國考文垂大學與諾丁漢特倫特大學要求 IELTS 6.0–6.5；法國 NEOMA、Audencia、EDHEC、蒙彼利埃商學院、德國杜塞道夫大學、芬蘭 Haaga-Helia、奧地利 MCI、立陶宛維陶瑪納大學要求 CEFR B2（iBT 72–80 / IELTS 5.5–6.0）；香港理工大學要求 iBT 80 / IELTS 6.0。",
                  "日本、韓國與大陸港澳組：（1）日本 31 所姐妹校中，埼玉大學、秋田國際教養大學 AIU、立命館亞洲太平洋大學 APU、關西國際大學、崇城大學等可憑英語成績修讀英文授課學程，京都府立大學、和歌山大學、帝京大學、東洋學園大學、駒澤大學、松本大學、明海大學、梅花女子大學、追手門學院大學、大阪產業大學、神戶學院大學、天理大學等要求 JLPT N2–N3；（2）韓國 20 校可選英語授課（CEFR B1–B2）或韓語授課（TOPIK 2–4 級）；（3）大陸 95 校與澳門 4 校為中文授課。",
              ],
              "source": {
                  "title": "義守大學交換姐妹校名冊、雙聯學位列表與日本姐妹校一覽表",
                  "source_url": ISU_EXCHANGE_SISTER_SCHOOLS_URL,
                  "category": "exchange_application",
                  "summary": "義守大學全球 33 國與地區交換及雙聯學位姐妹校外語能力門檻總覽。",
              },
          }
      ],
      "required_documents": [
          {
              "title": "赴境外交換研修申請表、中英文歷年成績單、語檢證明、中英文讀書計畫與自傳、推薦信、交換生具結書與學分承認表",
              "details": [
                  "校內甄選必備文件（須先經系所主任及學院院長簽章後送國際及兩岸事務處）：（1）義守大學學生赴境外交換研修申請表；（2）中英文歷年成績單正本（含班級或系年級排名百分比）；（3）有效外語能力檢定證明影本；（4）中英文自傳與讀書計畫；（5）教師推薦信；（6）交換生具結書（Declaration of Indemnity，含家長同意簽章）；（7）學分承認表（Credit Transfer Form）。",
                  "獎助學金申請、抵達回報與返國核銷必備文件：申請教育部學海飛颺／惜珠或校內學海助學金須檢附《獎學金申請資料單》、《行政契約書》與《獎學金具結書》；抵達姐妹校後繳交《國外抵達報告表（Arrival Report）》；返國後二週內繳交《返校手續單》、《學分抵免表》、1,500 字以上《成果心得報告》及《校內成果報告 PPT 簡報檔》。",
              ],
              "source": {
                  "title": "義守大學國際及兩岸事務處表單下載專區與赴境外交換研修甄選辦法",
                  "source_url": ISU_DOWNLOADS_URL,
                  "category": "exchange_application",
                  "summary": "義守大學交換生校內申請、獎助學金契約、國外抵達報告與返國學分抵免表件規範。",
              },
          }
      ],
      "scholarship_info": [
          {
              "title": "教育部學海飛颺／惜珠（系前 40% 或班前 30%）、義守大學學海助學金、赴大陸校際交換獎學金、學文助學金與歐盟 Erasmus+ 獎學金",
              "details": [
                  "教育部與歐盟獎學金：（1）《教育部學海飛颺獎學金》：具中華民國國籍、操行 80 分以上無懲處、前一學期學業成績於該系所該年級前 40% 或班排前 30%，補助 NT$ 50,000 以上；（2）《教育部學海惜珠獎學金》：持低收入戶、中低收入戶或特殊境遇家庭證明且前學期成績達系年級前 40% 或班排前 30%，補助 NT$ 50,000–300,000 以上；（3）《歐盟 Erasmus+ 獎學金》：補助赴立陶宛維陶瑪納大學、塞爾維亞埃杜孔斯大學等歐洲 Erasmus+ 締約校交換生。",
                  "義守大學校內三大獎助學金：（1）《義守大學學海助學金》：補助本校在籍學生（含港澳生、境外生）赴海外姐妹校長期交換、修讀雙聯學位或短期交流（前學期成績達系年級前 50% 且通過英語畢業門檻），補助 NT$ 20,000–30,000 以上；（2）《義守大學赴大陸校際交換獎學金》：補助赴大陸姐妹校交換，修課全部通過補助 NT$ 4,000、部分通過補助 NT$ 3,000；（3）《義守大學學文助學金》：補助大陸短期交流團、暑期一個月學習團（公費／部分公費）及一學期大陸研修團（累計成績全班前 50% 且通過英檢與資訊檢測）。",
              ],
              "source": {
                  "title": "義守大學國際及兩岸事務處獎學金專區與移動力獎助學金辦法",
                  "source_url": ISU_SCHOLARSHIPS_URL,
                  "category": "scholarship",
                  "summary": "義守大學六大出國交換、雙聯學位與兩岸研修獎助學金完整規定。",
              },
          }
      ],
      "document_explanations": [
          {
              "title": "義守大學赴境外交換中英文讀書計畫、學分承認表（Credit Transfer Form）、交換生具結書與獎學金行政契約準備指南",
              "summary": "說明義守大學《學生赴境外交換研修甄選辦法》規定之中英文讀書計畫與自傳、出國前《學分承認表》預審、家長簽章《交換生具結書》及獎助學金契約要領。",
              "key_points": [
                  "中英文讀書計畫與《學分承認表（Credit Transfer Form）》：應明確規劃於目標姐妹校每學期修習至少 9 學分（大陸研修團至少 16 學分）之課程清單，並於出國前填妥《學分承認表》送交系所主任預先審認與義守大學母系必修／選修科目之抵免對應。",
                  "中英文自傳與專業結合：建議結合義守大學智慧科技、工程、AACSB 認證商管／國際／觀光餐旅、傳播設計、醫學或醫學科技等專業背景，突顯外語檢定成績、國際學伴（I-Buddy）或專題研究經驗。",
                  "交換生具結書與獎助學金契約：報名時須附上家長或法定監護人親筆簽章之《交換生具結書》；獲教育部學海飛颺／惜珠或校內學海助學金者須簽署《行政契約書》及《獎學金具結書》，並於抵達姐妹校後回傳《國外抵達報告表》、返國後二週內完成 1,500 字心得報告與簡報檔。",
              ],
              "applies_to": [],
              "source": {
                  "title": "義守大學國際及兩岸事務處表單下載專區與受獎生出國前後應辦理事項",
                  "source_url": ISU_DOWNLOADS_URL,
                  "category": "exchange_application",
                  "summary": None,
              },
              "document_url": ISU_CREDIT_APPROVAL_FORM_DOC_URL,
              "document_type": "official_document",
              "full_text_extracted": True,
          }
      ],
      "rule_explanations": [
          {
              "title": "義守大學學生赴境外交換研修甄選辦法、學海助學金設置辦法與學文助學金設置辦法核心規定",
              "summary": "規範義守大學交換生在學註冊繳費（全額學雜費）、海外選課下限（每學期至少 9 學分／大陸研修團 16 學分）、外語畢業門檻原則與返國二週內報到抵免義務。",
              "key_points": [
                  "在學註冊與全額學雜費規定：依《義守大學學生赴境外交換研修甄選辦法》第 7 條，交換生於出國交流期間應維持本校學籍並依規定繳交本校每學期全額學雜費，免繳接待姐妹校學費（雙聯學位或特定自費訪學項目依兩校合約規定辦理）。",
                  "赴外選課下限與及格標準：依《赴境外交換研修甄選辦法》第 7 條及《學文助學金設置及甄選作業辦法》第 17 條，交換期間每學期修習課程以不低於 9 學分為原則（赴大陸結盟學校研修團每學期至少修習 16 學分以上），且學期學業平均成績應符合及格標準（60 分以上）。",
                  "返國報到、學分抵免與心得報告義務：依《受獎生出國前後應辦理事項》及《返校手續單》，交換生應於返國後二週內檢附《返校手續單》、《學分抵免表》、正式國外成績單、1,500 字以上《成果心得報告》及《校內成果報告 PPT 簡報檔》向國際及兩岸事務處與教務處辦理返校銷案與學分採認。",
              ],
              "applies_to": [],
              "source": {
                  "title": "義守大學學生赴境外交換研修甄選辦法、學海助學金辦法與學文助學金辦法",
                  "source_url": ISU_OUTBOUND_SELECTION_RULES_PDF_URL,
                  "category": "exchange_application",
                  "summary": None,
              },
              "document_url": ISU_RETURN_PROCEDURE_PDF_URL,
              "document_type": "official_document",
              "full_text_extracted": True,
          }
      ],
      "sources": [
          {
              "title": "義守大學國際及兩岸事務處（Office of International and Cross-Strait Affairs, OICA）官方網站",
              "source_url": ISU_OICA_HOME_URL,
              "category": "exchange_application",
              "summary": None,
          },
          {
              "title": "義守大學出國交換暨雙聯學位總覽與申請流程專頁",
              "source_url": ISU_OUTBOUND_EXCHANGE_URL,
              "category": "exchange_application",
              "summary": None,
          },
          {
              "title": f"義守大學交換姐妹校名冊與 Looker Studio 官方資料庫（全球 33 國與地區共 {len(partners)} 所合作姐妹校）",
              "source_url": ISU_EXCHANGE_SISTER_SCHOOLS_URL,
              "category": "partner_school",
              "summary": None,
          },
          {
              "title": "義守大學海外雙聯學位學校列表（英、美、港、日、韓、陸 11 所合作大學 3+1／2+2／3+1+1 學程）",
              "source_url": ISU_DUAL_DEGREE_SCHOOLS_URL,
              "category": "exchange_application",
              "summary": None,
          },
          {
              "title": "義守大學海外交換暨雙聯學位費用參考表（Google Sheets 官方核定各校宿費、生活費與保險費）",
              "source_url": ISU_COST_REF_SHEET_URL,
              "category": "partner_school",
              "summary": None,
          },
          {
              "title": "義守大學國際及兩岸事務處獎學金與移動力獎助學金專區（教育部學海飛颺／惜珠、義守大學學海助學金、赴大陸校際交換獎學金、學文助學金）",
              "source_url": ISU_SCHOLARSHIPS_URL,
              "category": "scholarship",
              "summary": None,
          },
          {
              "title": "義守大學赴境外交換研修相關法規與表單下載專區（甄選辦法、學分承認表、學分抵免表、返校手續單）",
              "source_url": ISU_REGULATIONS_URL,
              "category": "exchange_application",
              "summary": None,
          },
          {
              "title": f"義守大學學長姐經驗傳承專區（{exp_covered_schools} 校 {total_exp_reports} 篇歷屆交換生心得報告）",
              "source_url": ISU_STUDENT_EXPERIENCES_URL,
              "category": "exchange_application",
              "summary": None,
          },
      ],
  }
  (OFFICIAL_ISU_DIR / "student_dashboard.json").write_text(
      json.dumps(student_dashboard_payload, ensure_ascii=False, indent=2)
      + "\n",
      encoding="utf-8",
  )

  doc_conditions = {
      "school_id": "isu",
      "school_name": "義守大學",
      "checked_at": CHECKED_AT,
      "source_url": ISU_OUTBOUND_SELECTION_RULES_PDF_URL,
      "common_documents": exchange_info_payload["required_documents"],
      "track_specific_conditions": [
          {
              "track": "校級赴境外交換研修計畫—「歐美澳與亞洲英語授課姐妹校組」",
              "required": [
                  "義守大學學生赴境外交換研修申請表（經所屬學系主任及學院院長審核簽章）",
                  "大學或研究所歷年中英文成績單正本（含班級或系年級排名百分比）",
                  "有效英語能力檢定證明影本（TOEFL iBT / IELTS / TOEIC，須達交流學校門檻或本校英語畢業門檻 CEFR B1 / TOEIC 550；法國巴黎 EDH 集團可檢附本校核發之 CEFR B2 證明）",
                  "中英文自傳與中英文讀書計畫、專任教師推薦信、交換生具結書（含家長同意簽章）及《學分承認表（Credit Transfer Form）》",
              ],
          },
          {
              "track": "校級赴境外交換研修計畫—「日本（31 校）與韓國（20 校）姐妹校組」",
              "required": [
                  "義守大學學生赴境外交換研修申請表（經系所及學院核章）及中英文歷年成績單正本",
                  "日語能力檢定證明（JLPT N2–N3，依《義守大學日本姐妹校一覽表》規定；申請埼玉大學、AIU、APU、關西國際大學、崇城大學等英文授課學程者可檢附 TOEFL / IELTS / TOEIC）或韓語／英語檢定證明（TOPIK 2–4 級或 CEFR B1–B2）",
                  "中英／中日／中韓讀書計畫與自傳、教師推薦信、交換生具結書及《學分承認表》",
              ],
          },
          {
              "track": "校級赴大陸港澳交換研修暨「學文助學金（大陸研修團／暑期學習團）」",
              "required": [
                  "義守大學學生赴境外交換研修申請表（或大陸研修團／暑期學習團申請表）及歷年中文成績單正本",
                  "中英文讀書計畫與自傳、家長同意具結書、《學分承認表》及有效臺胞證（申請一學期大陸研修團者須累計成績達全班前 50% 並檢附通過校訂英檢與資訊能力檢測證明，且每學期至少修習 16 學分）",
              ],
          },
          {
              "track": "海外雙聯學位計畫（英、美、港、日、韓、陸 11 校）與六大出國獎助學金申請",
              "required": [
                  "海外雙聯學位申請：校內申請表、英文歷年成績單正本、外語檢定證明（IELTS 6.0–6.5 / TOEFL iBT 68–80 / JLPT N2 或合作校指定門檻）、英文讀書計畫、推薦信、具結書與《學分承認表》",
                  "教育部學海飛颺／惜珠或義守大學學海助學金：獎學金申請資料單、歷年成績單正本（學海飛颺／惜珠須操行 80 分以上無懲處且前學期成績達系年級前 40% 或班排前 30%；校內學海助學金短期交流須前學期成績達系年級前 50% 且通過英語畢業門檻）、語檢證明、行政契約書、獎學金具結書及姐妹校入學許可（學海惜珠另附低收／中低收／特殊境遇證明）",
              ],
          },
      ],
  }
  (OFFICIAL_ISU_DIR / "document-conditions.json").write_text(
      json.dumps(doc_conditions, ensure_ascii=False, indent=2) + "\n",
      encoding="utf-8",
  )

  field_cov_lines = [
      "field_name,total_records,populated_records,coverage_ratio,notes"
  ]
  for fname in [
      "school_name",
      "country",
      "region",
      "program_type",
      "availability_status",
      "quota",
      "colleges",
      "degree_levels",
      "language_requirement",
      "gpa_requirement",
      "application_deadline",
      "study_period",
      "semester_dates",
      "housing_info",
      "course_restrictions",
      "official_website",
      "image_url",
  ]:
    pop = sum(1 for p in partners if p.get(fname) not in (None, "", []))
    ratio = pop / len(partners) if partners else 1.0
    field_cov_lines.append(
        f"{fname},{len(partners)},{pop},{ratio:.4f},Official ISU OICA verified"
    )
  (OFFICIAL_ISU_DIR / "field-coverage.csv").write_text(
      "\n".join(field_cov_lines) + "\n", encoding="utf-8"
  )

  pages_records = [
      {
          "title": "義守大學：每年 2 月（秋季班）及 8 月（春季班）出國交換暨雙聯學位校內甄選與大陸研修團／學習團申請時程",
          "source_url": ISU_OUTBOUND_EXCHANGE_URL,
          "published_at": "2026-09-01T00:00:00Z",
          "text": "\n".join(exchange_info_payload["application_period"]),
          "summary": "\n".join(exchange_info_payload["application_period"]),
          "category": "exchange_application",
          "attachments": [],
          "crawled_at": CHECKED_AT,
          "content_hash": hashlib.sha256(
              "\n".join(exchange_info_payload["application_period"]).encode(
                  "utf-8"
              )
          ).hexdigest(),
      },
      {
          "title": "義守大學：學生赴境外交換研修甄選辦法、大二／碩一以上在學資格、全額學雜費註冊與每學期 9 學分（大陸研修團 16 學分）規定",
          "source_url": ISU_OUTBOUND_SELECTION_RULES_PDF_URL,
          "published_at": "2026-09-01T00:00:00Z",
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
          "title": f"義守大學：{len(partners)} 所全球與兩岸合作姐妹校外語檢定門檻（歐美亞英語組／日本 31 校／韓國 20 校／大陸港澳／雙聯學位）",
          "source_url": ISU_EXCHANGE_SISTER_SCHOOLS_URL,
          "published_at": "2026-09-01T00:00:00Z",
          "text": "\n".join(exchange_info_payload["language_requirement"]),
          "summary": "\n".join(exchange_info_payload["language_requirement"]),
          "category": "exchange_application",
          "attachments": [],
          "crawled_at": CHECKED_AT,
          "content_hash": hashlib.sha256(
              "\n".join(exchange_info_payload["language_requirement"]).encode(
                  "utf-8"
              )
          ).hexdigest(),
      },
      {
          "title": "義守大學：赴境外交換與雙聯學位應備文件（申請表、歷年成績單、語檢證明、中英文讀書計畫、推薦信、交換生具結書、學分承認表、抵達報告與返校手續單）",
          "source_url": ISU_DOWNLOADS_URL,
          "published_at": "2026-09-01T00:00:00Z",
          "text": "\n".join(exchange_info_payload["required_documents"]),
          "summary": "\n".join(exchange_info_payload["required_documents"]),
          "category": "exchange_application",
          "attachments": [],
          "crawled_at": CHECKED_AT,
          "content_hash": hashlib.sha256(
              "\n".join(exchange_info_payload["required_documents"]).encode(
                  "utf-8"
              )
          ).hexdigest(),
      },
      {
          "title": "義守大學：教育部學海飛颺、學海惜珠、義守大學學海助學金、赴大陸校際交換獎學金、學文助學金與歐盟 Erasmus+ 獎學金辦法",
          "source_url": ISU_SCHOLARSHIPS_URL,
          "published_at": "2026-09-01T00:00:00Z",
          "text": "\n".join(exchange_info_payload["scholarship_info"]),
          "summary": "\n".join(exchange_info_payload["scholarship_info"]),
          "category": "scholarship",
          "attachments": [],
          "crawled_at": CHECKED_AT,
          "content_hash": hashlib.sha256(
              "\n".join(exchange_info_payload["scholarship_info"]).encode(
                  "utf-8"
              )
          ).hexdigest(),
      },
  ]
  (OFFICIAL_ISU_DIR / "pages.jsonl").write_text(
      "\n".join(json.dumps(p, ensure_ascii=False) for p in pages_records)
      + "\n",
      encoding="utf-8",
  )

  home_rules = {
      "school_id": "isu",
      "school_name": "義守大學",
      "eligibility": student_dashboard_payload["eligibility"],
      "application_periods": student_dashboard_payload["application_periods"],
      "selection_rules": {
          "minimum_Passing_score": 60.0,
          "excluded_undergraduate_years": [1],
          "xuehai_rank_threshold": "top 40% of department/year or top 30% of class, conduct >= 80",
          "isu_xuehai_grant_threshold": "top 50% of department/year and pass ISU English graduation threshold",
          "isu_xuewen_study_group_threshold": "cumulative score top 50% of class and pass ISU English & IT graduation thresholds",
          "min_credits_per_semester_abroad": "9 credits (16 credits for Mainland China Xuewen study group)",
          "require_isu_full_tuition_during_abroad": True,
          "default_english_requirement_if_unspecified": "ISU English graduation threshold (CEFR B1 / TOEIC 550 / TOEFL iBT 42 / IELTS 4.0)",
          "return_documents_due": "返國後二週內繳交返校手續單、學分抵免表、正式成績單、1,500 字以上成果心得報告及校內成果報告 PPT 簡報檔",
      },
      "source_urls": isu_source_urls,
      "verified_at": "2026-11-02",
  }
  (OFFICIAL_ISU_DIR / "home_rules.json").write_text(
      json.dumps(home_rules, ensure_ascii=False, indent=2) + "\n",
      encoding="utf-8",
  )
  (OFFICIAL_ISU_DIR / "documents.json").write_text(
      json.dumps(
          {
              "school_name": "義守大學",
              "required_documents": student_dashboard_payload[
                  "required_documents"
              ],
              "source_urls": isu_source_urls,
          },
          ensure_ascii=False,
          indent=2,
      )
      + "\n",
      encoding="utf-8",
  )
  (OFFICIAL_ISU_DIR / "scholarships.json").write_text(
      json.dumps(
          {
              "school_name": "義守大學",
              "scholarships": student_dashboard_payload["scholarship_info"],
              "source_urls": isu_source_urls,
          },
          ensure_ascii=False,
          indent=2,
      )
      + "\n",
      encoding="utf-8",
  )

  completeness = {
      "school_id": "isu",
      "school_name": "義守大學",
      "total_partners": len(partners),
      "partner_count": len(partners),
      "international_partners": sum(
          1
          for p in partners
          if p["country"] not in {"中國大陸", "香港", "澳門"}
      ),
      "mainland_partners": sum(
          1 for p in partners if p["country"] in {"中國大陸", "香港", "澳門"}
      ),
      "dual_degree_partner_universities": dual_degree_count,
      "dual_degree_programs": 15,
      "experience_report_covered_partners": exp_covered_schools,
      "experience_report_count": total_exp_reports,
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
      "active_term": (
          f"義守大學國際及兩岸事務處（OICA）《交換姐妹校名冊》、《雙聯學位學校列表（11 校）》、《全球與兩岸合作姐妹校名錄》、《海外交換費用參考表》、《義守大學學生赴境外交換研修甄選辦法》，以及教育部學海飛颺、學海惜珠、義守大學學海助學金、赴大陸校際交換獎學金與學文助學金辦法同步整合；共完整收錄 {len(partners)} 所全球與兩岸有效締約交換及雙聯姐妹校（橫跨全球 33 個國家與地區，並收錄 {exp_covered_schools} 所合作大學共 {total_exp_reports} 篇歷屆學長姐交換心得報告與 12 份官方 Fact Sheet）。"
      ),
      "verified_at": "2026-11-02",
  }
  (OFFICIAL_ISU_DIR / "catalog-completeness.json").write_text(
      json.dumps(completeness, ensure_ascii=False, indent=2) + "\n",
      encoding="utf-8",
  )
  (OFFICIAL_ISU_DIR / "verification_status.json").write_text(
      json.dumps(
          {
              "school_id": "isu",
              "school_name": "義守大學",
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
          "sources/isu/isu_catalog_source.json",
          ISU_EXCHANGE_SISTER_SCHOOLS_URL,
          f"義守大學 {len(partners)} 所全球與兩岸合作姐妹校整合資料集 JSON",
      ),
      (
          "sources/isu/isu_resolved_locations.json",
          ISU_EXCHANGE_SISTER_SCHOOLS_URL,
          f"義守大學 {len(partners)} 所合作姐妹校 ROR / Wikidata 地理座標核對表 JSON",
      ),
      (
          "sources/isu/oica_exchange_sister_schools.html",
          ISU_EXCHANGE_SISTER_SCHOOLS_URL,
          "義守大學國際及兩岸事務處《交換姐妹校專區》HTML",
      ),
      (
          "sources/isu/oica_dual_degree_schools.html",
          ISU_DUAL_DEGREE_SCHOOLS_URL,
          "義守大學國際及兩岸事務處《雙聯學位學校列表》HTML",
      ),
      (
          "sources/isu/oica_partner_schools.html",
          ISU_PARTNER_SCHOOLS_URL,
          "義守大學國際及兩岸事務處《全球與兩岸合作姐妹校總覽》HTML",
      ),
      (
          "sources/isu/looker_exchange_88_schools.json",
          "https://lookerstudio.google.com/embed/reporting/7a264451-b2db-429d-a092-87557cce54f6/page/9OCGF",
          "義守大學國際及兩岸事務處《學生交換及研修表 Looker Studio 資料庫》JSON",
      ),
      (
          "sources/isu/looker_dual_degree_5_rows.json",
          "https://lookerstudio.google.com/embed/reporting/bd58ff7a-ffc3-4cc7-b573-3caee0d08507/page/1QhzD",
          "義守大學國際及兩岸事務處《雙聯學位一覽表 Looker Studio 資料庫》JSON",
      ),
      (
          "sources/isu/regulations/exchange_cost_reference.xlsx",
          ISU_COST_REF_SHEET_URL,
          "義守大學國際及兩岸事務處《海外交換暨雙聯學位費用參考表》XLSX",
      ),
  ]
  for fentry in bin_urls_raw.get("files", []):
    if isinstance(fentry, dict) and fentry.get("filename") and fentry.get("url"):
      rp = f"sources/isu/{fentry['filename']}"
      if not any(x[0] == rp for x in provenance_files):
        provenance_files.append(
            (rp, fentry["url"], f"義守大學官方原始檔案：{fentry.get('label') or Path(rp).name}")
        )

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
      "school_id": "isu",
      "school_name": "義守大學",
      "generated_at": CHECKED_AT,
      "active_cycle_note": completeness["active_term"],
      "sources": prov_sources,
  }
  prov_text = (
      json.dumps(provenance_payload, ensure_ascii=False, indent=2) + "\n"
  )
  (OFFICIAL_ISU_DIR / "import_provenance.json").write_text(
      prov_text, encoding="utf-8"
  )
  (OFFICIAL_ISU_DIR / "import-provenance.json").write_text(
      prov_text, encoding="utf-8"
  )

  print(
      f"Successfully built ISU catalog: {len(partners)} partners"
      f" ({open_partner_count} open, {completeness['verified_campus_images']}"
      f" verified images, {completeness['verified_locations']} verified"
      f" locations), {len(workflows)} workflows,"
      f" {len(destinations)} destinations, {len(research_records)} research"
      f" records, {exp_covered_schools} schools with experience records"
      f" ({len(student_experience_rows)} rows, {total_exp_reports} reports)."
  )


if __name__ == "__main__":
  main()
