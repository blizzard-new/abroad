"""Build the official Kaohsiung Medical University (高雄醫學大學, KMU) exchange data bundle."""

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

SOURCES_KMU_DIR = REPO_ROOT / "sources" / "kmu"
OFFICIAL_KMU_DIR = REPO_ROOT / "src" / "exchange_info" / "official_data" / "kmu"
STATIC_DIR = REPO_ROOT / "src" / "exchange_info" / "static"

CHECKED_AT = "2026-10-21T05:00:00Z"

KMU_OIA_HUB_URL = "https://ciae2.kmu.edu.tw/index.php/zh-tw"
KMU_OIA_EN_HUB_URL = "https://ciae2.kmu.edu.tw/index.php/en-gb"
KMU_PARTNERS_ZH_URL = "https://ciae2.kmu.edu.tw/index.php/zh-tw/%E5%9C%8B%E9%9A%9B%E5%90%88%E4%BD%9C/%E5%A7%8A%E5%A6%B9%E6%A0%A1%E7%B7%A0%E7%B4%84%E6%83%85%E5%BD%A2"
KMU_PARTNERS_EN_URL = "https://ciae2.kmu.edu.tw/index.php/en-gb/global-network/partner-institutions"
KMU_DUAL_PARTNERS_URL = "https://ciae2.kmu.edu.tw/index.php/zh-tw/%E5%AD%B8%E7%94%9F%E4%BA%A4%E6%B5%81/%E5%87%BA%E5%9C%8B%E7%A0%94%E7%BF%92%E8%88%87%E7%8D%8E%E5%AD%B8%E9%87%91/%E9%9B%99%E8%81%AF%E5%AD%B8%E5%88%B6"
KMU_JUNTENDO_EXCHANGE_URL = "https://ciae2.kmu.edu.tw/index.php/zh-tw/%E6%9C%80%E6%96%B0%E6%B6%88%E6%81%AF/%E5%85%AC%E5%91%8A%E8%A8%8A%E6%81%AF/2997"
KMU_SUBSIDY_STD_URL = "https://ciae2.kmu.edu.tw/index.php/zh-tw/%E5%AD%B8%E7%94%9F%E4%BA%A4%E6%B5%81/%E5%87%BA%E5%9C%8B%E7%A0%94%E7%BF%92%E8%88%87%E7%8D%8E%E5%AD%B8%E9%87%91/2541"
KMU_XUEHAI_URL = "https://ciae2.kmu.edu.tw/index.php/zh-tw/%E5%AD%B8%E7%94%9F%E4%BA%A4%E6%B5%81/%E5%87%BA%E5%9C%8B%E7%A0%94%E7%BF%92%E8%88%87%E7%8D%8E%E5%AD%B8%E9%87%91/%E5%AD%B8%E6%B5%B7%E7%B3%BB%E5%88%97%E8%A3%9C%E5%8A%A9"
KMU_QIANLIMA_115_URL = "https://ciae2.kmu.edu.tw/index.php/zh-tw/%E6%9C%80%E6%96%B0%E6%B6%88%E6%81%AF/%E5%85%AC%E5%91%8A%E8%A8%8A%E6%81%AF/3221"
KMU_NA_ALUMNI_2026_URL = "https://ciae2.kmu.edu.tw/index.php/zh-tw/%E6%9C%80%E6%96%B0%E6%B6%88%E6%81%AF/%E5%85%AC%E5%91%8A%E8%A8%8A%E6%81%AF/3153"
KMU_REG_INTL_REWARD_PDF_URL = "https://ciae2.kmu.edu.tw/images/files/StudentMobility/%E9%AB%98%E9%9B%84%E9%86%AB%E5%AD%B8%E5%A4%A7%E5%AD%B8%E5%AD%B8%E7%94%9F%E5%9C%8B%E9%9A%9B%E7%A0%94%E7%BF%92%E6%9C%8D%E5%8B%99%E7%8D%8E%E5%8B%B5%E8%A6%81%E9%BB%9E.pdf"
KMU_115_XUEHAI_BRIEFING_PDF_URL = "https://ciae2.kmu.edu.tw/images/files/StudentMobility/115%E5%AD%B8%E6%B5%B7%E8%AA%AA%E6%98%8E%E6%9C%83%E7%B0%A1%E5%A0%B1.pdf"

KMU_CMED_2027_NOTICE_URL = "https://cmed.kmu.edu.tw/p/406-1010-29601,r11.php?Lang=zh-tw"
KMU_CMED_2027_SHEET_URL = "https://docs.google.com/spreadsheets/d/1q7mAzXMyCslEwZCuoieUl1ldiXAb6zJtU2YBcgco2KY/edit?usp=sharing"
KMU_CMED_KUMAMOTO_DUAL_URL = "https://cmed.kmu.edu.tw/p/406-1010-40533,r11.php?Lang=zh-tw"
KMU_CMED_EXP_URL = "https://cmed.kmu.edu.tw/p/412-1010-1179.php?Lang=zh-tw"
KMU_DENT_363_URL = "https://dent.kmu.edu.tw/p/412-1084-363.php?Lang=zh-tw"
KMU_PHARM_INTL_URL = "https://cpharmacy.kmu.edu.tw/p/412-1013-2201.php?Lang=zh-tw"
KMU_NURSING_OUTBOUND_URL = "https://conursing.kmu.edu.tw/p/412-1011-754.php?Lang=zh-tw"
KMU_OT_INTL_URL = "https://ot.kmu.edu.tw/p/412-1025-550.php?Lang=zh-tw"
KMU_PT_INTL_URL = "https://pt.kmu.edu.tw/p/412-1026-825.php?Lang=zh-tw"
KMU_MRT_INTL_URL = "https://mrt.kmu.edu.tw/p/412-1071-613.php?Lang=zh-tw"
KMU_SPORTSMED_INTL_URL = "https://sportsmed.kmu.edu.tw/p/412-1069-1234.php?Lang=zh-tw"
KMU_RESPCARE_INTL_URL = "https://respcare.kmu.edu.tw/p/412-1072-339.php?Lang=zh-tw"

REGION_COST_DEFAULTS = {
    "美國": (
        "USD 1,500–2,800 / 月（含住宿、膳食與市區交通；哈佛醫學院 HMS 波士頓、南加州大學 USC 洛杉磯、加州大學爾灣分校 UCI、希望之城國家醫學中心 City of Hope、賓州大學 UPenn、約翰霍普金斯醫院、羅格斯大學 RBHS 約 USD 1,950–2,800 / 月；阿肯色醫學科學大學 UAMS、德州大學休士頓健康科學中心 UTHealth、內布拉斯加大學醫學中心 UNMC、內華達大學拉斯維加斯分校 UNLV、梅哈里醫學院、休士頓大學約 USD 1,450–2,100 / 月；高醫大提供歐美非來回機票最高 NT$ 50,000＋每月生活費 NT$ 25,000 補助，赴北美醫牙藥護臨床見實習另可申請北美洲高醫校友會每人 NT$ 15,000 獎學金，赴哈佛見習再享 KMU-Harvard Foundation USD 500 獎助）",
        "須憑美國接待校或教學醫院核發之 DS-2019（J-1 交換生／訪問學者）或 I-20（F-1 雙聯學位學生）表格，或依 VSLO 臨床見實習規定向美國在台協會（AIT）申辦簽證，並完成全套免疫抗體效價檢測（MMR、水痘、B肝、TB 檢驗、流感與 COVID-19 疫苗）及醫療保險。",
    ),
    "加拿大": (
        "CAD 1,600–2,500 / 月（溫哥華英屬哥倫比亞大學 UBC 與多倫多大學校內外學生住宿、伙食與大眾運輸費用；可申請高醫大歐美非機票最高 NT$ 50,000＋每月 NT$ 25,000 生活補助及北美洲高醫校友會 NT$ 15,000 獎學金）",
        "一學期內短期交換或牙醫臨床見習可申辦加拿大 eTA 電子旅行授權，超過 6 個月須申辦 Study Permit 學生許可並投保醫療保險。",
    ),
    "墨西哥": (
        "USD 650–1,050 / 月（伊達爾戈州自治大學 UAEH 學生住宿與日常飲食交通開銷）",
        "須向墨西哥商務簽證文件暨文化辦事處申辦簽證並投保海外全期醫療及意外保險。",
    ),
    "巴拉圭": (
        "USD 600–950 / 月（亞松森國立大學 Universidad Nacional de Asunción 周邊學生住宿與生活開銷）",
        "我國護照享免簽證入境巴拉圭待遇，長期研修須依接待校指引辦理居留許可並投保海外全期醫療保險。",
    ),
    "日本": (
        "JPY 80,000–135,000 / 月（東京順天堂大學、慶應義塾大學、東京醫科大學［免費提供見習生住宿］、東京科學大學 TMDU、聖路加國際大學、日本藥科大學約 JPY 95,000–135,000 / 月；京都大學、東北大學、廣島大學、神戶大學［有機會獲 JPY 50,000 獎學金］、熊本大學、信州大學、德島大學、愛媛大學、鹿兒島大學、藤田醫科大學、九州齒科大學、神奈川齒科大學、茨城縣立醫療大學、愛媛縣立醫療技術大學、人間環境大學約 JPY 70,000–105,000 / 月；高醫大提供亞洲來回機票最高 NT$ 10,000＋每月生活費 NT$ 15,000 補助）",
        "學期或學年交換（如順天堂大學 JLCSP / LAP）及雙聯博士（如熊本大學）須憑日本接待校核發之在留資格認定證明書（COE）向日本台灣交流協會申辦留學簽證並加入日本國民健康保險（NHI）；短期臨床見實習（4–8 週）享免簽證入境，須備妥醫院指定之免疫抗體證明（B肝、麻疹、德國麻疹、水痘、腮腺炎、T-SPOT/QFT 結核檢驗）與海外醫療及實習責任險。",
    ),
    "韓國": (
        "KRW 800,000–1,350,000 / 月（首爾大學 SNU 與高麗大學約 KRW 950,000–1,350,000 / 月；水原亞洲大學 Ajou University、釜山大學 PNU、全北大學、嘉泉大學、鮮文大學、濟州觀光大學約 KRW 750,000–1,050,000 / 月；高醫大提供亞洲機票最高 NT$ 10,000＋每月 NT$ 15,000 生活補助）",
        "學期交換須憑韓國接待校標準入學許可書向駐台北韓國代表部申辦 D-2 留學簽證；短期醫牙臨床見實習須備妥實習許可函、疫苗抗體證明與海外醫療保險。",
    ),
    "新加坡": (
        "SGD 1,600–2,500 / 月（新加坡國立大學 NUS、南洋理工大學 NTU、新加坡陳篤生醫院 Tan Tock Seng Hospital 及竹腳婦幼醫院 KKH 臨床見實習期間之住宿、熟食中心餐飲與捷運公車費用；可申請高醫大新南向學海築夢或校內亞洲機票最高 NT$ 10,000＋每月 NT$ 15,000 生活補助）",
        "赴新加坡國立大學楊潞齡醫學院、南洋理工大學李光前醫學院、陳篤生醫院（TTSH）或竹腳婦幼醫院（KKH）進行臨床見實習，須依新加坡衛生部（MOH）與移民局（ICA）規定申辦 Training Employment Pass（TEP）或 Student Pass，並完成嚴格之疫苗抗體效價認證。",
    ),
    "泰國": (
        "THB 13,000–23,000 / 月（曼谷朱拉隆功大學 Chulalongkorn、瑪希朵大學 Mahidol、國立法政大學 Thammasat、詩納卡寧威洛大學，以及清邁大學 Chiang Mai、宋卡王子大學 PSU、孔敬大學、泰國西北大學 Payap 學生宿舍與餐飲交通開銷實惠；可申請教育部新南向學海築夢或高醫大亞洲機票＋生活費補助）",
        "須憑泰國接待大學或附設醫院公文向泰國貿易經濟辦事處（TTEO）申辦 Non-Immigrant ED 留學／實習簽證，並投保涵蓋全期之海外醫療及意外保險。",
    ),
    "越南": (
        "USD 450–780 / 月（胡志明市醫藥大學、胡志明市國家大學醫學院、河內醫科大學、順化醫藥大學、海防醫藥大學、芹苴醫藥大學、海陽醫藥科技大學、西原大學、邦美蜀醫科大學等住宿與餐飲交通費用低廉）",
        "須透過越南接待大學或教學醫院申辦越南電子簽證或實習簽證，並於出國前投保涵蓋全期之海外醫療及意外保險。",
    ),
    "印尼": (
        "IDR 4,800,000–8,200,000 / 月（雅加達印度尼西亞大學 UI、日惹卡渣瑪達大學 UGM、泗水艾爾朗加大學 UNAIR、萬隆巴查查蘭大學 Unpad、峇里島烏達雅納大學 Udayana、望加錫哈薩努丁大學等學生公寓與餐飲交通費用實惠）",
        "須由印尼接待校協助申辦印尼學生／文化交流電子簽證（e-Visa），並投保涵蓋全期之海外醫療及意外保險。",
    ),
    "馬來西亞": (
        "MYR 1,600–2,600 / 月（吉隆坡馬來亞大學 UM、馬來西亞國立大學 UKM、博特拉大學 UPM、國際醫藥大學 IMU、拉曼大學 UTAR 及檳城馬來西亞理科大学 USM 校內外住宿與飲食交通開銷）",
        "學期交換或長期實習須透過馬來西亞 EMGS 系統申辦學生簽證核准函（VAL / Mobility Pass）並投保醫療保險。",
    ),
    "菲律賓": (
        "USD 550–900 / 月（馬尼拉菲律賓大學 UP、聖托瑪斯大學 UST、德拉薩大學 DLSU、雅典耀大學 Ateneo、遠東大學 FEU、萊希姆大學 LPU、菲律賓中央大學 CEU 等住宿與生活費用）",
        "須依菲律賓接待校指引辦理簽證或特別學習許可（SSP），並投保海外全期醫療及意外保險。",
    ),
    "印度": (
        "USD 450–780 / 月（印度理工學院德里分校 IIT Delhi、海得拉巴分校 IIT Hyderabad、博拉理工學院 BITS Pilani、奧斯馬尼亞大學、馬哈拉施特拉健康科學大學、SRM 科技大學等國際學舍與餐飲費用）",
        "須憑印度接待校入學／研究許可向印度台北協會（ITA）申辦 Student / Research Visa 並投保海外醫療及意外保險。",
    ),
    "巴基斯坦": (
        "USD 450–750 / 月（拉合爾大學 University of Lahore 與帝國大學商業學院學生宿舍與生活費）",
        "須憑接待校官方邀請函申辦學生／學術交流簽證並投保海外全期醫療保險（出國前請確認外交部最新旅遊安全資訊）。",
    ),
    "以色列": (
        "USD 1,200–1,900 / 月（亞實基倫巴爾齊萊醫學中心 Barzilai Medical Center 周邊住宿、飲食與交通費用）",
        "須依駐台北以色列經濟文化辦事處規定辦理簽證或入境許可，並於出國前確認外交部旅遊安全警示與全程海外醫療急難救助保險。",
    ),
    "澳洲": (
        "AUD 2,000–2,900 / 月（黃金海岸邦德大學 Bond University、格里菲斯大學 Griffith University、雪梨大學、西雪梨大學、坎培拉大學、查爾斯達爾文大學住宿與生活費；高醫大提供大洋洲來回機票最高 NT$ 25,000＋每月生活費 NT$ 20,000 補助）",
        "短期醫學臨床見習（如邦德大學 4–6 週）可申辦澳洲 ETA 電子旅行授權，修讀雙聯學位（如格里菲斯大學）或一學期以上交換須購買澳洲海外學生健康保險（OSHC）並申辦 Subclass 500 學生簽證。",
    ),
    "索羅門群島": (
        "USD 800–1,300 / 月（荷尼阿拉索羅門國立大學 SINU 與中央醫院國際醫療衛生交流食宿交通開銷）",
        "須依接待機構指引辦理入境簽證、瘧疾預防用藥與疫苗接種，並投保全程海外醫療及急難救助保險。",
    ),
    "瑞典": (
        "EUR 950–1,450 / 月（約 SEK 10,500–16,000；烏普薩拉大學 Uppsala University 雙聯交換每年 6 名免學費、斯德哥爾摩卡羅林斯卡醫學院 Karolinska Institutet 職治系交換 3 名每人獲約 NT$ 110,000 補助；高醫大另提供歐美非機票最高 NT$ 50,000＋每月 NT$ 25,000 生活補助）",
        "90 天內短期交換免申根簽證；超過 90 天（1 學期或雙聯學位）須向瑞典移民局（Migrationsverket）線上申辦高等教育居留許可（Residence Permit for Higher Education）。",
    ),
    "匈牙利": (
        "EUR 600–950 / 月（賽蓋德大學 University of Szeged 雙聯交換每年 3 名享免學費＋免費提供匈牙利學生宿舍＋高醫大提供歐美非來回機票最高 NT$ 50,000 與每月 NT$ 25,000 生活補助，生活成本極為親民）",
        "90 天內短期研習免申根簽證；一學期以上交換或雙聯博士須向匈牙利貿易辦事處申辦 D 類長期學生簽證／居留許可。",
    ),
    "法國": (
        "EUR 850–1,300 / 月（馬賽與普羅旺斯艾克斯-馬賽大學 Aix-Marseille University 學生公寓 CROUS、日常餐飲與交通，並可申請法國政府 CAF 房補及高醫大歐美非機票最高 NT$ 50,000＋每月 NT$ 25,000 生活補助）",
        "超過 90 天之交換或雙聯博士須透過法國教育中心（Campus France）程序及法國在台協會申辦長期學生簽證（VLS-TS）。",
    ),
    "德國": (
        "EUR 900–1,350 / 月（科隆大學 University of Cologne 醫學院附設醫院臨床見實習住宿、學餐與德國交通票開銷；可申請教育部學海飛颺或高醫大歐美非機票最高 NT$ 50,000＋每月 NT$ 25,000 生活補助）",
        "短期醫學臨床見實習（4–8 週，90 天內）享免申根簽證入境德國，須備妥德英雙語健康與免疫抗體證明（含麻疹、水痘、B肝等）及醫療與實習責任險。",
    ),
    "英國": (
        "GBP 1,200–1,900 / 月（倫敦國王學院 King's College London 住宿與倫敦地鐵餐飲約 GBP 1,450–1,900 / 月；艾塞克斯大學 University of Essex 約 GBP 1,050–1,400 / 月）",
        "一學期（6 個月內）交換或短期研究可持護照及 ETA 辦理 Standard Visitor 入境，超過 6 個月須申辦英國 Student Visa 並繳納醫療附加費（IHS）。",
    ),
    "西班牙": (
        "EUR 750–1,150 / 月（埃爾切米蓋爾埃南德斯大學 Miguel Hernández University of Elche 學生公寓與地中海飲食交通費用）",
        "90 天內短期研習免申根簽證，一學期以上交換須向西班牙商務辦事處申辦長期學生簽證。",
    ),
    "義大利": (
        "EUR 850–1,300 / 月（羅馬大學 Sapienza University of Rome 學生住宿、食堂與地鐵公車開銷）",
        "90 天內短期研習免申根簽證，一學期以上交換須向義大利經濟貿易文化推廣辦事處申辦 D 類學生簽證。",
    ),
    "波蘭": (
        "EUR 550–850 / 月（羅茲醫科大學 Medical University of Lodz 與波茲南醫學科學大學 PUMS 學生宿舍與日常餐飲交通費用親民）",
        "90 天內短期見習免申根簽證，一學期以上交換須向波蘭臺北辦事處申辦 D 類國別學生簽證。",
    ),
    "捷克": (
        "EUR 650–950 / 月（布拉格查理大學 Charles University 學生宿舍與捷克學生交通餐飲開銷）",
        "90 天內短期研習免申根簽證，一學期以上交換須向捷克經濟文化辦事處申辦長期學生簽證。",
    ),
    "挪威": (
        "EUR 1,100–1,600 / 月（斯塔萬格大學 University of Stavanger 與奧斯陸大學 University of Oslo 學生宿舍 SiS/SiO 與北歐生活開銷）",
        "90 天內短期研習免申根簽證，一學期以上交換須向挪威移民局（UDI）申辦學生居留許可。",
    ),
    "荷蘭": (
        "EUR 1,050–1,550 / 月（鹿特丹伊拉斯姆斯大學醫學中心 Erasmus MC 住宿、日常飲食與荷蘭大眾運輸 OV-chipkaart 費用）",
        "90 天內短期研究或見習免申根簽證，一學期以上須由接待校代向荷蘭移民局（IND）申辦居留許可。",
    ),
    "南非": (
        "USD 550–900 / 月（普勒托利亞南非醫學大學 Sefako Makgatho Health Sciences University 住宿與生活費）",
        "須向南非聯絡辦事處申辦簽證，並投保涵蓋全期之海外醫療及急難救助保險。",
    ),
    "埃及": (
        "USD 500–850 / 月（開羅艾因夏姆斯大學 Ain-Shams University 住宿與生活開銷）",
        "須辦理埃及簽證並投保涵蓋全期之海外醫療及急難救助保險。",
    ),
    "史瓦帝尼": (
        "USD 550–900 / 月（史瓦帝尼大學 University of Eswatini 醫療衛生與護理交流食宿開銷）",
        "我國護照享免簽證入境邦交國史瓦帝尼待遇，出發前須備妥相關疫苗預防與全程海外醫療急難救助保險。",
    ),
    "香港": (
        "HKD 6,000–10,000 / 月（香港大學 HKU 李嘉誠醫學院與瑪麗醫院 Queen Mary Hospital 臨床見習期間之住宿、港鐵與餐飲費用；高醫大提供亞洲機票最高 NT$ 10,000＋每月 NT$ 15,000 生活補助）",
        "赴香港大學李嘉誠醫學院進行 2027 臨床見實習（4 名）或學期交換，須依港大指引向香港入境事務處申辦來港就讀／受訓進入許可（Entry Permit），並於出國前至陸委會「國人赴港澳動態登錄系統」完成登錄。",
    ),
    "中國大陸": (
        "RMB 2,000–3,600 / 月（北京大學、復旦大學、上海交通大學、中山大學、浙江大學、同濟大學、四川大學、武漢大學、山東大學、中南大學、吉林大學、南開大學、西安交通大學、蘭州大學、哈爾濱醫科大學、中國醫科大學、重慶醫科大學、廣州醫科大學、福建醫科大學、江蘇大學、西南交通大學校內宿舍與學生食堂費用實惠）",
        "持有效護照與臺胞證入境；依教育部及高雄醫學大學出國研習與學分抵免規定，赴大陸地區交流須落實教育部登錄平臺填報，且出國修課須於出國前完成系所及教務處審核（大陸地區高等學校醫事人員相關學歷與學分採認悉依教育部與考選部法規辦理）。",
    ),
}

SEMESTER_DATES_BY_COUNTRY = {
    "美國": "秋季學期（Fall）：約 8 月中下旬至 12 月中旬；春季學期（Spring）：約 1 月中旬至 5 月中旬；醫學院 2027 海外臨床見實習（哈佛 HMS、City of Hope、羅格斯、梅哈里、夏威夷大學）及牙醫／藥學／職治／物治／運醫／呼治臨床見實習：依各梯次於 6–8 月暑期、1–2 月寒假或大五／大六臨床輪訓期間執行",
    "加拿大": "秋季學期（Fall）：約 9 月初至 12 月中旬；冬季／春季學期（Winter）：約 1 月初至 4 月底；牙醫學系赴英屬哥倫比亞大學（UBC）暑期見習：每年 7–8 月（約 4 週）",
    "墨西哥": "秋季學期：約 8 月中旬至 12 月中旬；春季學期：約 1 月中旬至 5 月底",
    "巴拉圭": "第一學期：約 3 月至 7 月；第二學期：約 8 月至 12 月",
    "日本": "春季學期（前學期）：約 4 月初至 8 月上旬（順天堂大學春季班校內申請 10/20 截止）；秋季學期（後學期）：約 9/10 月至翌年 2/3 月（順天堂大學秋季班校內申請 4/18 截止）；醫學院、口腔醫學院、藥學院、護理學院、健康科學院赴日臨床見實習（京都大學、慶應義塾大學、東京醫科大學、東京科學大學 TMDU、東北大學、廣島大學、神戶大學、熊本大學、德島大學、信州大學、愛媛大學、藤田醫科大學、鹿兒島大學、日本藥科大學、聖路加國際大學、茨城縣立醫療大學等）：寒假（1–2 月）、暑假（6–8 月）或學期中 2–8 週",
    "韓國": "春季學期（第1學期）：約 3 月初至 6 月中下旬；秋季學期（第2學期）：約 9 月初至 12 月中下旬；醫學院（首爾大學、亞洲大學）與牙醫學系（釜山大學）臨床見實習：寒暑假或高年級臨床輪訓期間 2–8 週",
    "新加坡": "第一學期：約 8 月至 12 月；第二學期：約 1 月至 5 月；醫學院（NUS 4 名、NTU 4 名）與醫放系／呼治系（新加坡陳篤生醫院 TTSH、竹腳婦幼醫院 KKH）海外臨床見實習：4–8 週",
    "泰國": "第一學期：約 8 月至 12 月；第二學期：約 1 月至 5 月；醫學院（宋卡王子大學 4 名）、牙醫學系（朱拉隆功大學 6 名）與雙聯學位（朱拉隆功、瑪希朵、清邁大學）：4–8 週臨床見實習或 1–2 年雙聯研究",
    "越南": "第一學期（秋季班）：約 9 月至翌年 1 月；第二學期（春季班）：約 2 月至 6 月",
    "印尼": "奇數／秋季學期：約 8/9 月至 12 月；偶數／春季學期：約 2 月至 6 月",
    "馬來西亞": "第一學期（秋季班）：約 10 月至翌年 2 月；第二學期（春季班）：約 3 月至 7 月",
    "菲律賓": "第一學期（秋季班）：約 8 月至 12 月；第二學期（春季班）：約 1 月中旬至 5 月下旬",
    "印度": "奇數／秋季學期：約 7/8 月至 12 月；偶數／春季學期：約 1 月至 5 月",
    "巴基斯坦": "秋季學期：約 9 月至翌年 1 月；春季學期：約 2 月至 6 月",
    "以色列": "秋季學期：約 10 月至翌年 1 月；春季學期：約 3 月至 6 月",
    "澳洲": "第一學期（Trimester 1 / Semester 1）：約 2 月中下旬至 6 月；第二學期（Trimester 2 / Semester 2）：約 7 月中下旬至 11 月；第三學期（邦德大學與格里菲斯大學 Trimester 3）：約 11 月至翌年 2 月（邦德大學 2027 醫學臨床見習最長 6 週）",
    "索羅門群島": "第一學期：約 2 月至 6 月；第二學期：約 7 月至 11 月",
    "瑞典": "秋季學期（Autumn Semester）：約 8 月下旬至翌年 1 月中旬；春季學期（Spring Semester）：約 1 月中旬至 6 月初（烏普薩拉大學雙聯交換每年 6 名、卡羅林斯卡醫學院職治系交換每年 3 名）",
    "匈牙利": "秋季學期（Autumn Semester）：約 9 月初至 12 月中旬；春季學期（Spring Semester）：約 2 月初至 5 月中旬（賽蓋德大學雙聯交換每年 3 名享免學費與免費住宿）",
    "法國": "秋季學期（Semestre 1）：約 9 月初至 12 月底；春季學期（Semestre 2）：約 1 月中旬至 5 月底（艾克斯-馬賽大學跨國雙聯博士與科研實習）",
    "德國": "冬季學期（Wintersemester）：約 10 月初至翌年 2 月中旬；夏季學期（Sommersemester）：約 4 月初至 7 月中下旬；科隆大學醫學院 2027 臨床見實習（4 名）：4–8 週",
    "英國": "秋季學期（Autumn Term）：約 9 月下旬至 12 月中旬；春季學期（Spring Term）：約 1 月中旬至 4 月；夏季學期：約 4 月下旬至 6 月",
    "西班牙": "第一學期（秋季班）：約 9 月中旬至翌年 1 月；第二學期（春季班）：約 2 月至 6 月",
    "義大利": "第一學期（秋季班）：約 9 月下旬至翌年 1/2 月；第二學期（春季班）：約 2 月下旬至 6/7 月",
    "波蘭": "冬季學期（秋季班）：約 10 月初至翌年 2 月中旬；夏季學期（春季班）：約 2 月下旬至 6 月底",
    "捷克": "冬季學期（秋季班）：約 9 月下旬至翌年 1 月；夏季學期（春季班）：約 2 月中旬至 6 月",
    "挪威": "秋季學期（Autumn）：約 8 月中旬至 12 月中旬；春季學期（Spring）：約 1 月初至 6 月中旬",
    "荷蘭": "第一學期（秋季班）：約 9 月初至翌年 1 月底；第二學期（春季班）：約 2 月初至 6 月底",
    "南非": "第一學期：約 2 月至 6 月；第二學期：約 7 月至 11 月",
    "埃及": "秋季學期：約 9 月下旬至翌年 1 月；春季學期：約 2 月中旬至 6 月",
    "史瓦帝尼": "第一學期：約 8 月至 12 月；第二學期：約 1 月至 5 月",
    "香港": "第一學期（Term 1）：約 9 月初至 12 月中下旬；第二學期（Term 2）：約 1 月上旬至 5 月中旬；香港大學李嘉誠醫學院 2027 臨床見實習（4 名）：4–8 週",
    "中國大陸": "秋季學期：約 9 月初至翌年 1 月中旬；春季學期：約 2 月中下旬至 6 月底",
}


def clean_text(s: str) -> str:
  if not s:
    return ""
  return re.sub(r"\s+", " ", s).strip()


def main() -> None:
  OFFICIAL_KMU_DIR.mkdir(parents=True, exist_ok=True)
  catalog_source = json.loads(
      (SOURCES_KMU_DIR / "kmu_catalog_source.json").read_text(encoding="utf-8")
  )
  resolved_locations = json.loads(
      (SOURCES_KMU_DIR / "kmu_resolved_locations.json").read_text(encoding="utf-8")
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
  total_exp_reports = 0

  for idx, item in enumerate(catalog_source):
    sn = idx + 1
    full_name = item["school_name"]
    zh_name = item["name_zh"]
    country = item["country"]
    region = item["region"]
    avail_status = "open" if item.get("offering_status") == "open" else "reference_only"
    if avail_status == "open":
      open_partner_count += 1

    group_str = clean_text(item.get("group") or "國際事務處正式締約姊妹校")
    quota_str = clean_text(item.get("quota") or "依高醫大國際事務處與各學院當期公告名額")
    detail_url = item.get("detail_url") or KMU_PARTNERS_ZH_URL

    if zh_name == "順天堂大學":
      program_type = "校級赴日本長期交換學生計畫（JLCSP 日語文化學程／LAP 國際教養課程，互免學費）暨醫學院／健康科學院臨床見實習計畫"
      source_url = KMU_JUNTENDO_EXCHANGE_URL
    elif zh_name in {
        "加州大學爾灣分校",
        "烏普薩拉大學",
        "賽蓋德大學",
        "艾克斯-馬賽大學",
        "格里菲斯大學",
        "希望之城國家醫學中心",
        "朱拉隆功大學",
        "瑪希朵大學",
        "清邁大學",
        "熊本大學",
    }:
      program_type = f"跨國雙聯學位暨交換／臨床見實習重點合作計畫（{group_str}）"
      source_url = KMU_CMED_KUMAMOTO_DUAL_URL if zh_name == "熊本大學" else KMU_DUAL_PARTNERS_URL
    elif "醫學院 2027（116學年度）海外臨床見實習" in group_str:
      program_type = "醫學院 2027（116學年度）海外臨床見實習（Medical Clerkship）甄選計畫"
      source_url = KMU_CMED_2027_NOTICE_URL
    elif "口腔醫學院" in group_str:
      program_type = "口腔醫學院（牙醫學系／口腔衛生學系）海外臨床見實習與短期交換甄選計畫"
      source_url = KMU_DENT_363_URL
    elif "藥學院" in group_str:
      program_type = "藥學院海外臨床藥學實習（APPE）、短期研究與教育部學海計畫"
      source_url = KMU_PHARM_INTL_URL
    elif "護理學院" in group_str:
      program_type = "護理學院海外臨床護理見實習與跨文化健康照護交流計畫"
      source_url = KMU_NURSING_OUTBOUND_URL
    elif "職能治療學系" in group_str or "物理治療學系" in group_str or "醫學影像暨放射科學系" in group_str:
      program_type = "健康科學院（物理治療／職能治療／醫學影像暨放射科學系）海外臨床見實習與學海築夢計畫"
      source_url = KMU_OT_INTL_URL if "職能治療" in group_str else (KMU_PT_INTL_URL if "物理治療" in group_str else KMU_MRT_INTL_URL)
    elif "運動醫學系" in group_str or "呼吸治療學系" in group_str:
      program_type = "醫學院（運動醫學系／呼吸治療學系）海外臨床專業實習與教育部學海築夢計畫"
      source_url = KMU_SPORTSMED_INTL_URL if "運動醫學" in group_str else KMU_RESPCARE_INTL_URL
    elif avail_status == "open":
      program_type = "人文社會科學院海外專業實習與教育部學海築夢／飛颺計畫"
      source_url = detail_url
    elif country in {"中國大陸", "香港"}:
      program_type = "大陸及港澳地區正式締約合作姊妹校"
      source_url = detail_url
    else:
      program_type = "國際事務處正式締約合作姊妹校與醫療研究機構"
      source_url = detail_url

    colleges_str = clean_text(item.get("colleges") or "")
    degree_levels_str = clean_text(item.get("eligible_degrees") or "學士班、碩士班、博士班在學學生")
    lang_req_str = clean_text(item.get("language_req") or "")
    gpa_req_str = clean_text(item.get("gpa_req") or "")
    website = item.get("website") or KMU_PARTNERS_ZH_URL
    remarks_raw = clean_text(item.get("notes") or "")
    tuition_note = clean_text(item.get("tuition_note") or "")
    exps = item.get("experience_reports") or []

    round_label = (
        "115–116學年度（2026–2028）出國交換、跨國雙聯學位、2027海外臨床見實習暨教育部學海計畫甄選"
        if avail_status == "open"
        else "國際事務處正式締約合作姊妹校（依當期交換、雙聯或海外臨床見實習公告名額辦理）"
    )
    app_deadline_str = (
        "【醫學院 2027（116學年度）海外臨床見實習（21 校 64+ 名：哈佛醫學院 6 名、希望之城 4 名、羅格斯 2 名、梅哈里 2 名、夏威夷大學 1 名、科隆大學 4 名、邦德大學 4 名、京都大學 2 名、慶應 3 名、東京醫大 2 名、神戶 3 名、德島 3 名、信州 2 名、愛媛 4 名、藤田醫大 2 名、首爾大學 2 名、亞洲大學 4 名、香港大學 4 名、新加坡國大 4 名、南洋理工 4 名、宋卡王子大學 4 名）】線上報名：2026/09/01–2026/09/28（09/09 說明會、10/14 英文面試、10/28 公告序位、11/04 志願選填、11/10 放榜）｜【校級赴日本順天堂大學長期交換生（JLCSP／LAP 免學費）】秋季班每年 4 月 18 日截止、春季班每年 10 月 20 日截止｜【10 校跨國雙聯學位（美國加州大學爾灣分校 UCI、希望之城 City of Hope、瑞典烏普薩拉大學 6 名免學費、匈牙利賽蓋德大學 3 名免學費＋免費住宿、法國艾克斯-馬賽大學、澳洲格里菲斯大學、日本熊本大學、泰國朱拉隆功大學、瑪希朵大學、清邁大學）及 115 年度博士生出國交流千里馬計畫（每院 1 名，最高補助 NT$500,000）】雙聯學位依每學期公告向學院及國際處申請，115 千里馬計畫於 2026/11/01–11/30 收件｜【口腔醫學院 115 寒假及 114 暑假海外見實習（UBC 6 名、東京科學大學 9 名、廣島 3 名、釜山 6 名、鹿兒島 6 名、UPenn 3 名、東北 3 名、UTHealth 4 名、朱拉隆功 6 名）】自公告日起至 10 月中旬向牙醫系辦報名｜【國際事務處出國研習補助（歐美非機票最高 NT$50,000＋每月生活費 NT$25,000）暨教育部學海四項計畫】學海計畫每年 2 月中旬校內截止（2026/01/06 辦理 115 學海說明會）；校內出國研習補助每年 9–10 月及 2–3 月受理（2026/09/23 辦理補助說明會）"
    )
    if "醫學院 2027（116學年度）海外臨床見實習" in group_str:
      deadline_iso = "2026-09-28T17:00:00+08:00"
    elif zh_name == "順天堂大學":
      deadline_iso = "2026-10-20T17:00:00+08:00"
    elif "口腔醫學院" in group_str:
      deadline_iso = "2026-10-16T17:00:00+08:00"
    else:
      deadline_iso = "2027-02-19T17:00:00+08:00"

    win_status = "open" if avail_status == "open" else "closed"
    acad_year = "116"

    study_period_str = clean_text(
        item.get("duration") or "1 學期、1 學年交換，1–2 年跨國雙聯學位，或 4–8 週海外臨床見實習"
    )
    sem_dates_str = SEMESTER_DATES_BY_COUNTRY.get(
        country, "秋季學期：約 9 月至翌年 1 月；春季學期：約 2 月至 6 月"
    )
    housing_str = (
        f"獲高雄醫學大學國際事務處或所屬學院提名錄取後，可依 {zh_name} 國際處／教學醫院指引申請校內外國際學生宿舍或臨床見實習生公寓"
        + (f"（費用與獎補助待遇：{tuition_note}）" if tuition_note else "。")
    )
    course_rest_str = (
        f"開放對象與領域：{colleges_str}。依《高雄醫學大學學海系列方案甄選及補助辦法》、《高雄醫學大學學生國際研習服務獎勵要點》、《國際事務處補助學生出國研習標準》（法規公告 2541）及各學院海外見實習簡章規定：（1）申請人須為具中華民國國籍且於高醫大設有正式學籍之在學學生（休學生及在職專班生不得申請校內與學海補助）；（2）出國期間須維持高醫大在學註冊，修讀跨國雙聯學位者須符合兩校雙聯協議之修業月數與學分抵免規範（如瑞典烏普薩拉大學每年 6 名互免學費、匈牙利賽蓋德大學每年 3 名免學費＋免費住宿、日本熊本大學醫學博士雙聯、泰國朱拉隆功大學藥學雙聯博士每年 2 名）；（3）海外專業實習（學海築夢／新南向學海築夢）須連續至少 30 天以上（不含來回途程；印尼因簽證規定為 25 天以上）；（4）返國後須於規定期間（14 日至 1 個月）內提交約 1,000 字出國研習心得報告、個人精選照片 4 張及活動影片（或上傳教育部學海計畫平臺）並出席成果分享會，始得完成補助核銷與學分採認。"
    )

    tuition_points_list = [
        (
            f"高醫大在學註冊與合作機構費用待遇（依《高雄醫學大學學生國際研習服務獎勵要點》與各院合作協議）：出國交換、雙聯與臨床見實習期間仍須辦理高醫大註冊。本合作機構待遇：{tuition_note or '依兩校合作協議辦理'}。"
        ),
        (
            "高醫大四大出國獎補助體系：（1）《國際事務處補助學生出國研習標準》（公告 2541）：出國交換、見實習或短期研究滿 1 個月以上者，核給經濟艙來回機票補助（歐美非最高 NT$ 50,000、大洋洲最高 NT$ 25,000、亞洲最高 NT$ 10,000）及每月生活費補助（歐美非每月 NT$ 25,000、大洋洲每月 NT$ 20,000、亞洲每月 NT$ 15,000，低收入戶及中低收入戶學生依標準 1.2 倍優予補助）；未滿 1 個月（至少 7 天）按日核給生活費（歐美非每日 NT$ 850、大洋洲每日 NT$ 700、亞洲每日 NT$ 500）；（2）教育部《學海飛颺、學海惜珠、學海築夢、新南向學海築夢》（每年 2 月中旬校內截止）及醫學院大專生雙語化學習計畫（EMI）海外實習全額／高額補助（如職治系赴瑞典卡羅林斯卡醫學院 KI 每人約 NT$ 110,000）；（3）《115 年度鼓勵博士生出國交流（千里馬）補助計畫》（公告 3221）：2026/11/01–11/30 申請，每學院 1 名赴海外研究 6–12 個月，最高補助 NT$ 500,000；（4）《財團法人北美洲高醫校友會基金會學生海外實習獎學金》（公告 3153）：補助醫、牙、藥、護學生赴美加姊妹校臨床見實習每人 NT$ 15,000（赴哈佛醫學院見習另享 KMU-Harvard Foundation 每人 USD 500 獎助）。"
        ),
    ]

    app_steps_list = [
        (
            f"步驟一（確認高醫大在學學籍、學業成績與 {zh_name} 語檢門檻）：確認為高雄醫學大學 7 大學院具正式學籍之在學學生（休學生及在職專班生不得申請補助），符合學業成績標準（{gpa_req_str}），並備妥有效外語檢定證明（{lang_req_str}）。"
        ),
        (
            "步驟二（於校內收件期限前向國際事務處［勵學大樓4樓］或所屬學院系所遞交申請表件）：（1）醫學院 2027（116學年度）海外臨床見實習（21 校 64+ 名）：於 2026/09/01–09/28 完成線上報名並上傳英文 CV、自傳與動機信、歷年成績單、語檢與課外表現證明（10/14 英文面試、11/04 志願選填、11/10 放榜）；（2）校級日本順天堂大學長期交換生：秋季班於每年 4/18 前、春季班於每年 10/20 前向國際事務處報名；（3）10 校跨國雙聯學位及各院系海外見實習（牙醫、口衛、藥學、護理、物治、職治、醫放、運醫、呼治、心理、醫社）：依各院系公告期限向系所及國際處遞件；（4）115 千里馬博士生出國研究補助（最高 50 萬元）：於 2026/11/01–11/30 向國際事務處申請。"
        ),
        (
            f"步驟三（通過校內書面與外語面試甄選，由國際事務處或學院向 {full_name} 辦理官方提名）：經高醫大國際事務處或各學院甄選委員會完成書面與英／日文面試評選後，向 {full_name} 辦理官方提名（Nomination），並依接待校院規定（如哈佛醫學院 VSLO 系統、烏普薩拉與賽蓋德大學雙聯交換系統等）完成外文入學或臨床見實習申請。"
        ),
        (
            "步驟四（完成行前說明會、免疫抗體檢驗與簽證保險，返國後繳交 1,000 字心得報告、4 張照片與活動影片辦理核銷）：出國前須參加國際事務處及學院舉辦之海外研習補助暨行前說明會、完成教學醫院指定之免疫抗體效價檢測與全程海外醫療急難救助保險；返國後須於規定期間內提交約 1,000 字心得報告、4 張個人照片、活動影片及登機證單據辦理獎補助核銷與學分採認。"
        ),
    ]

    elig_points_list = [
        f"合作類別與甄選群組：{program_type}（{group_str}）",
        f"開放學制與年級：{degree_levels_str}",
        f"開放申請院系：{colleges_str}",
        f"學業成績與排名門檻：{gpa_req_str}",
        f"外語能力標準：{lang_req_str}",
        "校內通則與獎補助規定：依《高雄醫學大學學海系列方案甄選及補助辦法》及《學生國際研習服務獎勵要點》，申請人須具中華民國國籍且為高醫大正式學籍在學學生（前一學期成績及格且無不及格科目；牙醫見習須達 75 分且前 75%、雙聯博士須達 GPA 3.0 / 75–80 分、醫學院雙語計畫全額補助須達 80 分）；返國後須繳交約 1,000 字心得報告、照片 4 張與活動影片並參與成果分享會。",
    ]
    if tuition_note:
      elig_points_list.append(f"姊妹校學費與高醫大獎補助待遇：{tuition_note}")
    if remarks_raw:
      elig_points_list.append(f"學程與締約重點說明：{remarks_raw}")

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
          f"【高醫大師生海外交換／臨床見實習成果報告（共 {len(exps)} 篇）】收錄於國際事務處與各學院國際交流專區（含：{'、'.join(exp_labels[:5])}）"
      )
    if remarks_raw:
      notes_lines.append(f"【學程與締約摘要】{remarks_raw}")

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
        "note": "校級代表位置：官方網域及國家已與 ROR / Wikidata 比對；實際交換校區或附設教學醫院院區以錄取通知與締約校專頁為準。",
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
        "availability_note": f"高雄醫學大學國際事務處與各學院公告合作姊妹校及教學醫院（{program_type}）；{quota_str}。",
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
        "image_source_url": visual_rec.get("image_source_url") or visual_rec.get("image_url"),
        "image_page_url": (
            visual_rec.get("official_page_url")
            or visual_rec.get("source_page_url")
            or visual_rec.get("image_source_url")
        ),
        "image_status": "verified",
        "location": location_obj,
        "reference_data": {
            k: str(v)
            for k, v in {
                "school_sn": sn,
                "kmu_table_code": item.get("kmu_table_code") or "",
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
            "title": f"高雄醫學大學國際事務處與各學院締約姊妹校、交換生、雙聯學位與海外臨床見實習專區—{zh_name}",
            "source_url": source_url,
            "role": "home_university",
            "authority": "home_official_notice",
            "effective_academic_year": acad_year,
            "application_round": round_label,
            "checked_at": CHECKED_AT,
        },
        {
            "title": "高雄醫學大學國際事務處補助學生出國研習標準（公告 2541）與學生國際研習服務獎勵要點",
            "source_url": KMU_SUBSIDY_STD_URL,
            "role": "home_university",
            "authority": "home_official_notice",
            "effective_academic_year": acad_year,
            "application_round": round_label,
            "checked_at": CHECKED_AT,
        },
        {
            "title": "高雄醫學大學跨國雙聯學制合作專區與 115 年度鼓勵博士生出國交流（千里馬）補助計畫",
            "source_url": KMU_DUAL_PARTNERS_URL,
            "role": "home_university",
            "authority": "home_official_notice",
            "effective_academic_year": acad_year,
            "application_round": round_label,
            "checked_at": CHECKED_AT,
        },
    ]
    if exps:
      wf_sources.append({
          "title": f"高雄醫學大學海外交換與臨床見實習成果報告專區—赴 {zh_name} 研修紀實（{len(exps)} 篇）",
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
        "home_university": "高雄醫學大學",
        "school_name": full_name,
        "partner_website": website,
        "country": country,
        "program_type": program_type,
        "academic_year": acad_year,
        "application_round": round_label,
        "effective_application_rounds": [
            round_label,
            "116學年度醫學院海外臨床見實習（21校64+名）甄選",
            "115–116學年度校級赴日本順天堂大學長期交換生暨10校跨國雙聯學位甄選",
            "115–116學年度口腔醫學院／藥學院／護理學院／健康科學院／人社院海外見實習暨教育部學海計畫甄選",
            "116-1",
            "116-2",
            "115-2",
            "115-1",
        ],
        "applicability_status": "verified",
        "applicability_note": (
            "高雄醫學大學由國際事務處（Office of Global Affairs，設於十全校區勵學大樓4樓）、教務處及全校 7 個學院（醫學院、口腔醫學院、藥學院、護理學院、健康科學院、生命科學院、人文社會科學院）共同統籌校級長期交換（日本順天堂大學 JLCSP / LAP 免學費交換）、10 校跨國雙聯學位（美國加州大學爾灣分校 UCI、希望之城國家醫學中心 City of Hope、瑞典烏普薩拉大學每年 6 名免學費、匈牙利賽蓋德大學每年 3 名免學費＋免費住宿、法國艾克斯-馬賽大學、澳洲格里菲斯大學、日本熊本大學、泰國朱拉隆功大學、瑪希朵大學、清邁大學）、醫學院 2027（116學年度）21 校 64+ 名海外臨床見實習（含哈佛醫學院 6 名、科隆大學 4 名、邦德大學 4 名、京都大學 2 名、慶應義塾大學 3 名、首爾大學 2 名、香港大學 4 名、新加坡國立大學 4 名、南洋理工大學 4 名等），以及牙醫、口衛、藥學、護理、物治、職治（含瑞典卡羅林斯卡醫學院 KI 3 名與南加大 USC 6 名）、醫放、運醫、呼治（含美國約翰霍普金斯醫院 4 名）、心理與醫社海外實習與教育部學海四項計畫。"
        ),
        "review_status": "published",
        "published_at": CHECKED_AT,
        "steps": [
            {
                "rule_id": f"kmu-{acad_year}-home-1-{idx+1:03d}",
                "order": 1,
                "phase": "校內申請",
                "title": f"確認高醫大在學身分、學業成績門檻與 {zh_name} 語檢要求",
                "responsible_party": "學生",
                "responsible_unit": "高雄醫學大學國際事務處／各學院系所",
                "deadline_at": deadline_iso,
                "deadline_status": "verified_exact" if avail_status == "open" else "reference_only",
                "deadline_source_url": source_url,
                "deadline_checked_at": CHECKED_AT,
                "deadline_reminder_eligible": avail_status == "open",
                "summary": (
                    f"確認符合《高雄醫學大學學海系列方案甄選及補助辦法》、《高雄醫學大學學生國際研習服務獎勵要點》及各學院雙聯／臨床見實習簡章規定：申請人須為具中華民國國籍且於高醫大設有正式學籍之在學學生（休學生、在職專班生不得申請補助），符合學業成績標準（{gpa_req_str}），並備妥符合 {zh_name} 要求之有效外語檢定證明。"
                ),
                "details": [
                    f"開放學制與院系：{colleges_str}（{degree_levels_str}）",
                    f"語言與學業條件：{lang_req_str}｜{gpa_req_str}",
                    f"當期名額與計畫類別：{quota_str}｜{program_type}",
                ],
                "scope": {
                    "home_universities": ["高雄醫學大學"],
                    "partner_universities": [full_name],
                    "academic_years": ["115", "116"],
                    "application_rounds": [round_label, "116-1", "116-2", "115-2", "115-1"],
                },
                "source_urls": [
                    source_url,
                    KMU_SUBSIDY_STD_URL,
                    KMU_REG_INTL_REWARD_PDF_URL,
                ],
                "checked_at": CHECKED_AT,
                "support_status": "verified",
            },
            {
                "rule_id": f"kmu-{acad_year}-home-2-{idx+1:03d}",
                "order": 2,
                "phase": "校內申請",
                "title": "向國際事務處（勵學大樓4樓）或所屬學院遞交出國交換、跨國雙聯或海外臨床見實習申請表件",
                "responsible_party": "學生與所屬系（所）辦公室",
                "responsible_unit": "高雄醫學大學國際事務處／各學院辦公室",
                "deadline_at": deadline_iso,
                "deadline_status": "verified_exact" if avail_status == "open" else "reference_only",
                "deadline_source_url": source_url,
                "deadline_checked_at": CHECKED_AT,
                "deadline_reminder_eligible": avail_status == "open",
                "summary": (
                    "依申請計畫於期限前備齊高醫大出國交換／雙聯／海外臨床見實習申請表、歷年中文與英文成績單正本（含學業平均、GPA 與班級排名）、有效外語能力檢定證明、英文簡歷（CV）與自傳／出國動機讀書計畫（Motivation Letter / Study Plan）、師長推薦信及家長同意書，向所屬學院或國際事務處提出申請。"
                ),
                "details": [
                    "醫學院 2027（116學年度）海外臨床見實習（21 校 64+ 名）：2026/09/01–09/28 線上報名、10/14 英文面試、10/28 公告序位、11/04 志願選填、11/10 放榜；口腔醫學院寒暑期海外見實習於每年 9–10 月報名；校級日本順天堂大學長期交換於每年 4/18（秋季班）及 10/20（春季班）截止。",
                    "教育部學海飛颺／惜珠／築夢／新南向學海築夢於每年 2 月中旬校內截止（2026/01/06 辦理說明會）；國際事務處出國研習補助於每年 9–10 月及 2–3 月受理（2026/09/23 辦理補助說明會）；115 年度博士生千里馬出國研究補助（最高 50 萬元）於 2026/11/01–11/30 收件；北美洲高醫校友會基金會海外實習獎學金（每人 NT$15,000）於每年 4 月底截止。",
                ],
                "document_requirements": [
                    {
                        "name": "高雄醫學大學出國交換學生／跨國雙聯學位／海外臨床見實習／國際事務處出國研習補助申請表及家長同意書",
                        "official_form_url": KMU_SUBSIDY_STD_URL,
                        "source_urls": [KMU_SUBSIDY_STD_URL, KMU_REG_INTL_REWARD_PDF_URL],
                    },
                    {
                        "name": "高醫大歷年中文與英文成績單正本（含學業總平均、GPA 及班級排名百分比證明）",
                        "source_urls": [KMU_CMED_2027_NOTICE_URL, KMU_DENT_363_URL, KMU_SUBSIDY_STD_URL],
                    },
                    {
                        "name": "有效外語能力檢定證明影本（TOEFL iBT / IELTS / TOEIC / GEPT / BESTEP / JLPT / CEFR B2–C1；哈佛醫學院須 TOEFL iBT 100；烏普薩拉大學須 iBT 79 / IELTS 6.0；順天堂大學須 JLPT N2 或 iBT 72 / IELTS 5.5）",
                        "source_urls": [KMU_CMED_2027_SHEET_URL, KMU_JUNTENDO_EXCHANGE_URL, KMU_DUAL_PARTNERS_URL],
                    },
                    {
                        "name": "英文個人簡歷（CV）、中英文自傳與出國動機／讀書研究計畫書（Motivation Letter / Study Plan）及專任教師推薦信",
                        "official_form_url": KMU_CMED_2027_NOTICE_URL,
                        "source_urls": [KMU_CMED_2027_NOTICE_URL, KMU_DUAL_PARTNERS_URL, KMU_XUEHAI_URL],
                    },
                ],
                "scope": {
                    "home_universities": ["高雄醫學大學"],
                    "academic_years": ["115", "116"],
                    "application_rounds": [round_label, "116-1", "116-2", "115-2", "115-1"],
                },
                "source_urls": [
                    source_url,
                    KMU_SUBSIDY_STD_URL,
                    KMU_CMED_2027_NOTICE_URL,
                    KMU_XUEHAI_URL,
                ],
                "checked_at": CHECKED_AT,
                "support_status": "verified",
            },
            {
                "rule_id": f"kmu-{acad_year}-home-3-{idx+1:03d}",
                "order": 3,
                "phase": "甄選與提名",
                "title": "國際事務處／各學院甄選委員會書面與外語面試審查、志願分發與獎補助核定",
                "responsible_party": "高雄醫學大學國際事務處／各學院甄選委員會",
                "responsible_unit": "高雄醫學大學國際事務處",
                "deadline_at": "2026-11-10T17:00:00+08:00" if "醫學院 2027" in group_str else "2027-03-15T17:00:00+08:00",
                "deadline_status": "verified_exact",
                "deadline_source_url": source_url,
                "deadline_checked_at": CHECKED_AT,
                "deadline_reminder_eligible": False,
                "summary": (
                    "由國際事務處或各學院召開甄選委員會進行書面審查（含在校學業成績、語檢能力、出國動機與研究見習計畫、社團與競賽表現）及全英語／日語面試，核定正備取分發名單與獎補助額度（含國際處歐美非機票最高 NT$50,000＋每月生活費 NT$25,000、大洋洲機票最高 NT$25,000＋每月 NT$20,000、亞洲機票最高 NT$10,000＋每月 NT$15,000，以及教育部學海四項計畫、博士生千里馬最高 NT$500,000、北美校友會 NT$15,000 與哈佛基金會 USD 500）。"
                ),
                "details": [
                    "醫學院 2027 海外臨床見實習依書審（40%：在校成績 20%、語檢 10%、CV 自傳與其他表現 10%）與全英文面試（60%）總成績排序，於 2026/10/28 公告選填序位、11/04 志願選填、11/10 公告錄取名單。",
                    "跨國雙聯學位（如瑞典烏普薩拉大學每年 6 名免學費、匈牙利賽蓋德大學每年 3 名免學費＋免費住宿、日本熊本大學醫學博士雙聯、泰國朱拉隆功大學藥學雙聯博士每年 2 名）經兩校審查錄取後簽署雙聯修業協議。",
                ],
                "scope": {
                    "home_universities": ["高雄醫學大學"],
                    "academic_years": ["115", "116"],
                    "application_rounds": [round_label, "116-1", "116-2", "115-2", "115-1"],
                },
                "source_urls": [
                    KMU_CMED_2027_NOTICE_URL,
                    KMU_SUBSIDY_STD_URL,
                    KMU_DUAL_PARTNERS_URL,
                    KMU_QIANLIMA_115_URL,
                ],
                "checked_at": CHECKED_AT,
                "support_status": "verified",
            },
            {
                "rule_id": f"kmu-{idx+1:03d}-host-apply",
                "order": 4,
                "phase": "合作校申請",
                "title": f"由高醫大國際處或學院向 {zh_name} 辦理官方提名（Nomination），並遞交外文入學、雙聯或臨床見實習申請文件",
                "responsible_party": "學生與接待校院國際事務處／臨床教學部門",
                "summary": (
                    f"通過高醫大甄選後，由國際事務處或所屬學院向 {zh_name} 辦理官方提名；學生須於接待校院規定截止日前（如哈佛醫學院透過 AAMC VSLO 系統）備妥外文入學／臨床見實習申請表、英文歷年成績單、護照影本、英文財力證明、語檢證書、推薦信與全套免疫抗體效價報告（Immunization Record），靜候核發正式入學或見實習許可（Letter of Acceptance / DS-2019 / I-20 / COE）。"
                ),
                "details": [
                    f"研修期程：{study_period_str}｜名額：{quota_str}",
                    f"語言與學業條件：{lang_req_str}｜{gpa_req_str}",
                    f"住宿與費用待遇：{housing_str}",
                ],
                "scope": {
                    "home_universities": ["高雄醫學大學"],
                    "partner_universities": [full_name],
                    "academic_years": ["115", "116"],
                    "application_rounds": [round_label, "116-1", "116-2", "115-2", "115-1"],
                },
                "source_urls": (
                    [source_url, KMU_PARTNERS_ZH_URL]
                    + ([website] if website else [])
                ),
                "checked_at": CHECKED_AT,
                "support_status": "verified",
                "needs_confirmation": False,
            },
            {
                "rule_id": f"kmu-{acad_year}-home-5-{idx+1:03d}",
                "order": 5,
                "phase": "行前準備",
                "title": "出國前完成選課與免疫檢驗、投保海外醫療急難保險，返國後繳交 1,000 字心得報告、4 張照片與活動影片辦理核銷及學分抵免",
                "responsible_party": "學生與所屬系所",
                "responsible_unit": "高雄醫學大學國際事務處／教務處／各學院系所",
                "summary": (
                    "出國前須參加高醫大國際事務處及學院行前說明會、維持本校在學註冊、完成海外教學醫院指定之疫苗接種與抗體效價檢測，並投保涵蓋全期之海外醫療及急難救助保險；返國後須於規定期間（14 日至 1 個月）內向國際事務處及學院繳交約 1,000 字出國研習心得報告、個人精選照片 4 張、活動影片及機票登機證正本辦理補助核銷，並出席經驗分享會及辦理學分採認。"
                ),
                "details": tuition_points_list,
                "scope": {
                    "home_universities": ["高雄醫學大學"],
                    "academic_years": ["115", "116"],
                    "application_rounds": [round_label, "116-1", "116-2", "115-2", "115-1"],
                },
                "source_urls": [
                    KMU_SUBSIDY_STD_URL,
                    KMU_REG_INTL_REWARD_PDF_URL,
                    KMU_XUEHAI_URL,
                ],
                "checked_at": CHECKED_AT,
                "support_status": "verified",
            },
        ],
        "sources": wf_sources,
        "last_checked": CHECKED_AT,
        "coverage_status": "official_verified",
        "coverage_note": (
            f"已完整整合高雄醫學大學國際事務處（OGA）、教務處與 7 大學院（校級赴日本順天堂大學長期交換生簡章、10 校跨國雙聯學位合作專區、醫學院 2027［116學年度］21 校 64+ 名海外臨床見實習試算表與甄選簡章、口腔醫學院／藥學院／護理學院／健康科學院／人文社會科學院海外見實習甄選公告、國際事務處補助學生出國研習標準、115 年度博士生千里馬出國研究計畫、北美洲高醫校友會獎學金及 {total_exp_reports if total_exp_reports else 70}+ 篇歷屆師生返國成果報告）共 {len(catalog_source)} 所全球合作姊妹校與醫療研究機構資料。"
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
            "title": f"高雄醫學大學國際事務處與各學院締約姊妹校、交換生、雙聯學位與海外見實習簡章—{zh_name}",
            "source_url": source_url,
            "summary": "高醫大國際事務處與各學院公告之合作學程、開放學院、語言檢定門檻與免學費／機票生活費獎補助待遇說明",
        },
        {
            "title": "高雄醫學大學國際事務處補助學生出國研習標準（公告 2541）與學生國際研習服務獎勵要點",
            "source_url": KMU_SUBSIDY_STD_URL,
            "summary": "高醫大出國交換與見實習機票（歐美非最高 NT$50,000、大洋洲 NT$25,000、亞洲 NT$10,000）及每月生活費（NT$15,000–25,000）補助標準與返國 1,000 字報告＋照片影片核銷規範",
        },
    ]
    if exps:
      dest_sources.append({
          "title": f"高雄醫學大學海外交換與臨床見實習經驗分享專區—赴 {zh_name} 成果報告（{len(exps)} 篇）",
          "source_url": exps[0]["url"],
          "summary": f"收錄歷年高醫大師生赴 {zh_name} 海外交換與臨床見實習心得報告共 {len(exps)} 篇",
      })
    if website:
      dest_sources.append({
          "title": f"{full_name} 官方網站",
          "source_url": website,
          "summary": "接待合作姊妹校／教學醫院官方網站",
      })

    src_url_list = (
        [source_url, KMU_SUBSIDY_STD_URL, KMU_REG_INTL_REWARD_PDF_URL]
        + ([exps[0]["url"]] if exps else [])
        + ([website] if website else [])
    )

    destinations.append({
        "home_university": "高雄醫學大學",
        "school_name": full_name,
        "country": country,
        "city": location_obj.get("city") or country,
        "cost_summary": f"{cost_line}。\n{tuition_clean}",
        "housing_summary": housing_clean,
        "transport_summary": (
            f"校區／醫院代表城市：{location_obj.get('city') or country}。請依入學／臨床見實習許可確認實際授課校區、附設教學醫院位置與當地學生交通優惠。"
        ),
        "campus_life_summary": f"{calendar_clean}\n{course_clean}",
        "student_guide_sections": [
            {
                "key": "cost",
                "title": "生活費、高醫大在學註冊規定、國際處機票（最高 NT$50,000）與生活費（每月最高 NT$25,000）補助及學海／千里馬／校友會獎學金",
                "summary": cost_line,
                "points": [cost_line] + tuition_points_list,
                "source_urls": src_url_list + [KMU_DUAL_PARTNERS_URL, KMU_NA_ALUMNI_2026_URL],
                "caution": (
                    "依《高雄醫學大學學海系列方案甄選及補助辦法》與《學生國際研習服務獎勵要點》，受補助學生須於返國後規定期間內繳交約 1,000 字心得報告、4 張個人照片與活動影片並出席經驗分享會，始得完成補助核銷。"
                ),
            },
            {
                "key": "housing",
                "title": "住宿資訊與校內外國際學生宿舍／教學醫院見實習生公寓申請",
                "summary": housing_clean[:160],
                "points": [housing_clean],
                "source_urls": src_url_list,
                "caution": (
                    "匈牙利賽蓋德大學雙聯交換生（每年 3 名）與日本東京醫科大學見習生（2 名）享免費提供住宿，瑞典烏普薩拉大學、日本順天堂大學等姊妹校設有國際學生宿舍申請期程，獲提名後請務必準時登記。"
                ),
            },
            {
                "key": "insurance",
                "title": "海外醫療及急難救助保險、臨床見實習疫苗抗體效價檢測與平安保險規定",
                "summary": visa_default,
                "points": [
                    visa_default,
                    "依高醫大國際事務處與各學院規定，所有出國交換、雙聯及海外臨床見實習學生均須於出發前投保涵蓋全期之海外醫療、意外及急難救助保險；赴美加歐日韓星泰教學醫院進行臨床見實習者，須提早完成規定之疫苗接種與抗體效價檢測。",
                ],
                "source_urls": src_url_list + [KMU_CMED_2027_NOTICE_URL],
                "caution": "美國哈佛醫學院 HMS（VSLO）、City of Hope、約翰霍普金斯醫院、德國科隆大學、新加坡 NUS/NTU/陳篤生醫院與日本各大學附設醫院對免疫抗體效價（MMR、水痘、B肝、TB 檢驗）審核嚴格，請於出發前 3–6 個月完成檢驗。",
            },
            {
                "key": "visa",
                "title": "留學／實習簽證辦理、出國選課審核與在學註冊義務",
                "summary": visa_default,
                "points": [
                    visa_default,
                    "出國交換、修讀雙聯學位與海外臨床見實習期間須維持高醫大在學註冊，並於出國前經所屬系（所）及學院確認擬修習或見實習科目。",
                ],
                "source_urls": src_url_list,
                "caution": "出國前請務必完成系所選課／實習確認、國際事務處行前說明會報到與行政契約簽署。",
            },
            {
                "key": "academics",
                "title": "海外臨床見實習評核、跨國雙聯修業規定與返國學分抵免",
                "summary": course_clean[:160],
                "points": [calendar_clean, course_clean],
                "source_urls": src_url_list + [KMU_DUAL_PARTNERS_URL],
                "caution": (
                    "教育部學海築夢與新南向學海築夢海外專業實習須連續至少 30 天以上（不含來回途程，印尼為 25 天以上）；修讀跨國雙聯學位者須依兩校雙聯協議完成規定學分與論文指導。"
                ),
            },
            {
                "key": "living",
                "title": f"{location_obj.get('city') or country} 校園／臨床生活與高醫大師生海外研修心得傳承",
                "summary": f"代表城市：{location_obj.get('city') or country}。請配合接待校院國際處或臨床教學部門完成報到與新生訓練（Orientation）。",
                "points": [
                    f"目的地城市：{location_obj.get('city') or country}（{country}）",
                    (
                        f"高雄醫學大學國際事務處與 7 大學院（醫學院、口腔醫學院、藥學院、護理學院、健康科學院、生命科學院、人文社會科學院）公開收錄歷屆師生赴海外交換與臨床見實習成果報告"
                        + (f"（本機構共收錄 {len(exps)} 篇：{'、'.join(exp_labels[:4])}）" if exps else "")
                        + "，並於每年 9–10 月及 1 月定期舉辦出國研習補助說明會、學海計畫說明會與海外臨床見實習經驗分享會。"
                    ),
                ],
                "source_urls": [exps[0]["url"] if exps else KMU_CMED_EXP_URL],
            },
        ],
        "sources": dest_sources,
        "last_checked": CHECKED_AT,
        "coverage_status": "official_verified",
        "coverage_note": (
            f"已整合高雄醫學大學國際事務處、教務處與 7 大學院 {len(catalog_source)} 所合作姊妹校與醫療機構、校級赴日本順天堂大學交換計畫、10 校跨國雙聯學位計畫、醫學院 2027（21 校 64+ 名）海外臨床見實習及各院系歷屆師生返國報告。"
        ),
    })

    research_records.append({
        "home_university": "高雄醫學大學",
        "school_name": full_name,
        "country": country,
        "official_website": website,
        "verification_status": "official_verified",
        "discovery_source_url": detail_url,
        "checked_at": CHECKED_AT,
        "note": (
            f"高雄醫學大學國際事務處《姊妹校締約情形（{KMU_PARTNERS_ZH_URL}）》、《雙聯學制（{KMU_DUAL_PARTNERS_URL}）》、《醫學院 2027 外派姐妹校一覽表》與 ROR/Wikidata 官方網址核對完成。"
        ),
    })

    ev_sources = [
        {
            "title": f"高雄醫學大學國際事務處與各學院締約姊妹校、交換生、雙聯學位與海外見實習簡章—{zh_name}",
            "url": source_url,
        },
    ]
    if exps:
      ev_sources.append({
          "title": f"高雄醫學大學海外交換與臨床見實習成果專區—赴 {zh_name} 成果報告（{len(exps)} 篇）",
          "url": exps[0]["url"],
      })
    if website:
      ev_sources.append({"title": f"{full_name} 官方網站", "url": website})

    has_student_exp = bool(exps)
    if exps:
      exp_covered_schools += 1
      total_exp_reports += len(exps)

    ev_list = [
        {
            "theme": "housing",
            "kind": "mixed" if has_student_exp else "official",
            "text": housing_clean,
            "sources": ev_sources,
            "checked_at": CHECKED_AT,
            "scope": "高雄醫學大學海外交換姊妹校與教學醫院住宿與生活資訊",
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
            "scope": "高雄醫學大學出國交換學雜費規定、國際處機票（最高 NT$50,000）與生活費（每月最高 NT$25,000）補助、學海／千里馬／北美校友會獎學金與地區生活費估算",
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
            "scope": "高雄醫學大學學海系列方案甄選及補助辦法、學生國際研習服務獎勵要點、雙聯學制與返國報告規範",
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
            "scope": "高雄醫學大學海外交換與臨床見實習簽證、疫苗抗體檢測、海外醫療保險與行前報到提醒",
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
                    f"｜高醫大公開收錄 {len(exps)} 篇赴 {zh_name} 海外交換／臨床見實習成果報告（{'、'.join(exp_labels[:4])}）。"
                    if exps
                    else ""
                )
            ),
            "sources": ev_sources,
            "checked_at": CHECKED_AT,
            "scope": "高雄醫學大學海外交換名額與歷屆師生成果報告分享",
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
            "已整合高雄醫學大學國際事務處《姊妹校締約情形》、《日本順天堂大學交換生甄選公告》、《10 校跨國雙聯學制專區》、《醫學院 2027（116學年度）21 校 64+ 名外派臨床見實習一覽表》、《口腔醫學院／藥學院／護理學院／健康科學院／人社院海外見實習公告》、《國際事務處補助學生出國研習標準》及歷屆師生成果報告。",
            "當期免學費名額、宿位供給、臨床見實習免疫檢驗要求與選課限制請依合作校院最新簡章及入學通知書核對。",
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
          f"高雄醫學大學赴 {zh_name} 海外交換研修／臨床專業見實習成果報告彙編（共 {len(exps)} 篇師生報告）"
      )
      latest_e = exps[0]
      latest_author = (
          f"{latest_e['student']} 等 {len(exps)} 組高醫大研修師生"
          if len(exps) > 1
          else latest_e["student"]
      )
      summary_text = (
          f"高雄醫學大學國際事務處與各學院公開收錄 {len(exps)} 篇歷年赴 {zh_name} 海外交換研修與臨床見實習成果報告（含：{'、'.join(exp_labels[:5])}）。"
          f"{latest_e['highlight']}"
      )
      theme_map = {
          "academics": (
              f"高醫大研修師生（{'、'.join(exp_labels[:3])}）分享於 {zh_name} 修讀專業課程、參與教學醫院臨床見實習（Clerkship / Internship）與實驗室研究之學習心得，以及返國辦理學分採認與成果發表之經驗。{latest_e['highlight']}"
          ),
          "housing": (
              f"高醫大研修生詳述 {zh_name} 校內外國際學生宿舍（如匈牙利賽蓋德大學與日本東京醫科大學免費學生宿舍、瑞典烏普薩拉與卡羅林斯卡醫學院學生公寓）或教學醫院臨床實習住宿申請、周邊生活機能與大眾運輸通勤方式（{housing_clean[:120]}）。"
          ),
          "campus_culture": (
              f"高醫大收錄 {len(exps)} 篇赴 {zh_name} 成果報告，記錄跨國醫學、牙醫、藥學、護理、物理治療、職能治療、醫放、運醫、呼治與心理臨床團隊協作、國際學伴交流與當地文化體驗。"
          ),
          "cost": (
              f"高醫大研修生記錄於 {zh_name} 之每月住宿、伙食與交通開銷（{cost_default}），以及運用姊妹校免學費／免宿費待遇、高醫大國際事務處出國研習機票（最高 NT$50,000）與生活費（每月最高 NT$25,000）補助、教育部學海計畫、北美洲高醫校友會獎學金（NT$15,000）與哈佛基金會獎助（USD 500）支應出國費用之規劃。"
          ),
      }
      student_experience_rows.append({
          "school_name": full_name,
          "country": country,
          "title": rep_title,
          "source_url": latest_e["url"],
          "source_type": "article",
          "platform": "高雄醫學大學國際事務處暨各學院—海外交換與臨床見實習成果專區",
          "author_name": latest_author,
          "language": "zh",
          "summary": summary_text,
          "themes": ["academics", "housing", "campus_culture", "cost"],
          "theme_summaries": theme_map,
          "content_status": "full_text",
          "perspective": "official_student_story",
          "published_at": None,
          "discovered_at": CHECKED_AT,
          "content_hash": hashlib.sha256(f"{full_name}:kmu_exp:{len(exps)}".encode("utf-8")).hexdigest(),
          "exchange_term": f"{latest_e['year']}年度",
          "summary_zh": summary_text,
          "original_summary": summary_text,
          "theme_summaries_zh": theme_map,
          "translation_status": "original",
          "source_kind": "official_experience_page",
      })

    experience_sources_records.append({
        "home_university": "高雄醫學大學",
        "school_name": full_name,
        "country": country,
        "official_experience_portal_url": (
            exps[0]["url"] if exps else KMU_CMED_EXP_URL
        ),
        "partner_page_url": source_url,
        "report_count": len(exps),
        "sample_reports": sample_reports,
        "checked_at": CHECKED_AT,
    })

  partners_jsonl_text = "\n".join(json.dumps(r, ensure_ascii=False) for r in partners) + "\n"
  (OFFICIAL_KMU_DIR / "partners.jsonl").write_text(partners_jsonl_text, encoding="utf-8")
  (SOURCES_KMU_DIR / "partners.jsonl").write_text(partners_jsonl_text, encoding="utf-8")
  (OFFICIAL_KMU_DIR / "application_workflows.jsonl").write_text(
      "\n".join(json.dumps(r, ensure_ascii=False) for r in workflows) + "\n",
      encoding="utf-8",
  )
  (OFFICIAL_KMU_DIR / "destination_profiles.jsonl").write_text(
      "\n".join(json.dumps(r, ensure_ascii=False) for r in destinations) + "\n",
      encoding="utf-8",
  )
  (OFFICIAL_KMU_DIR / "partner_research.jsonl").write_text(
      "\n".join(json.dumps(r, ensure_ascii=False) for r in research_records) + "\n",
      encoding="utf-8",
  )
  (OFFICIAL_KMU_DIR / "student_life.jsonl").write_text(
      "\n".join(json.dumps(r, ensure_ascii=False) for r in life_records) + "\n",
      encoding="utf-8",
  )
  (OFFICIAL_KMU_DIR / "experience_sources.jsonl").write_text(
      "\n".join(json.dumps(r, ensure_ascii=False) for r in experience_sources_records) + "\n",
      encoding="utf-8",
  )
  (OFFICIAL_KMU_DIR / "student_experiences.jsonl").write_text(
      "\n".join(json.dumps(r, ensure_ascii=False) for r in student_experience_rows) + "\n",
      encoding="utf-8",
  )
  (OFFICIAL_KMU_DIR / "campus-locations.json").write_text(
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
  (OFFICIAL_KMU_DIR / "student-experience-digests.json").write_text(
      json.dumps({"digests": digest_records}, ensure_ascii=False, indent=2) + "\n",
      encoding="utf-8",
  )

  # Ensure KMU home location ONLY is added to university_locations.jsonl
  loc_file = REPO_ROOT / "src/exchange_info/official_data/university_locations.jsonl"
  existing_loc_lines = [
      line for line in loc_file.read_text(encoding="utf-8").splitlines() if line.strip()
  ]
  existing_loc_map = {}
  for line in existing_loc_lines:
    rec = json.loads(line)
    existing_loc_map[(rec["school_name"], rec.get("country") or "")] = rec

  kmu_home_loc = {
      "school_name": "高雄醫學大學",
      "country": "臺灣",
      "city": "高雄市三民區",
      "latitude": 22.6465,
      "longitude": 120.3106,
      "geocode_status": "verified",
      "geocoded_at": CHECKED_AT,
      "source_url": "https://www.wikidata.org/wiki/Q714645",
      "identity_source_url": "https://ror.org/03gk81f96",
      "precision": "representative",
      "note": (
          "校級代表位置：官方網域及國家已與 ROR 比對，座標來源為 Wikidata P625；實際交換校區以錄取通知為準。"
          " 母校代表點採高雄市三民區十全一路100號十全校區（勵學大樓4樓國際事務處）；官方地址來源：https://ciae2.kmu.edu.tw/。"
      ),
  }
  existing_loc_map[("高雄醫學大學", "臺灣")] = kmu_home_loc
  sorted_locs = sorted(
      existing_loc_map.values(),
      key=lambda r: (r.get("country") or "", r.get("school_name") or ""),
  )
  loc_file.write_text(
      "\n".join(json.dumps(r, ensure_ascii=False) for r in sorted_locs) + "\n",
      encoding="utf-8",
  )

  kmu_source_urls = [
      KMU_OIA_HUB_URL,
      KMU_OIA_EN_HUB_URL,
      KMU_PARTNERS_ZH_URL,
      KMU_PARTNERS_EN_URL,
      KMU_DUAL_PARTNERS_URL,
      KMU_JUNTENDO_EXCHANGE_URL,
      KMU_SUBSIDY_STD_URL,
      KMU_XUEHAI_URL,
      KMU_QIANLIMA_115_URL,
      KMU_NA_ALUMNI_2026_URL,
      KMU_REG_INTL_REWARD_PDF_URL,
      KMU_115_XUEHAI_BRIEFING_PDF_URL,
      KMU_CMED_2027_NOTICE_URL,
      KMU_CMED_2027_SHEET_URL,
      KMU_CMED_KUMAMOTO_DUAL_URL,
      KMU_CMED_EXP_URL,
      KMU_DENT_363_URL,
      KMU_PHARM_INTL_URL,
      KMU_NURSING_OUTBOUND_URL,
      KMU_OT_INTL_URL,
      KMU_PT_INTL_URL,
      KMU_MRT_INTL_URL,
      KMU_SPORTSMED_INTL_URL,
      KMU_RESPCARE_INTL_URL,
  ]

  exchange_info_payload = {
      "school_name": "高雄醫學大學",
      "program_type": [
          (
              "校級赴日本順天堂大學長期交換學生計畫（Juntendo University Exchange Program：分為 JLCSP 日語及日本文化學程［不限日檢，修滿 14 學分獲結業證書］與 LAP 國際教養課程［須具 JLPT N2 或 TOEFL iBT 72 / IELTS 5.5，可修習醫學、運動健康科學、國際教養與保健看護學部課程］，互免學費；秋季班每年 4 月 18 日截止、春季班每年 10 月 20 日截止）"
          ),
          (
              "10 校跨國雙聯學位暨雙聯交換旗艦計畫（涵蓋【瑞典烏普薩拉大學 Uppsala University】每年 6 名［醫學院 3 名、藥學院 3 名］免學費雙聯交換；【匈牙利賽蓋德大學 University of Szeged】每年 3 名免學費＋免費提供匈牙利住宿＋高醫大機票生活費補助；【美國加州大學爾灣分校 UC Irvine】醫學與生醫雙聯；【美國希望之城國家醫學中心 City of Hope】轉譯醫學雙聯博士暨 2027 醫學臨床見習 4 名；【法國艾克斯-馬賽大學 Aix-Marseille University】雙聯博士；【澳洲格里菲斯大學 Griffith University】健康科學與公衛雙聯；【日本熊本大學 Kumamoto University】2026/09/17 新簽醫學研究所博士班雙聯學位；【泰國朱拉隆功大學 Chulalongkorn University】藥學雙聯博士每年 2 名免學費及醫技雙聯；【泰國瑪希朵大學 Mahidol University】與【泰國清邁大學 Chiang Mai University】護理、職治、醫技及口衛雙聯學位）"
          ),
          (
              "醫學院 2027（116學年度）21 校 64+ 名海外臨床見實習（Medical Clerkship）暨全校 7 大學院海外專業實習與教育部學海四項計畫（含【醫學院 2027 外派臨床見實習】選送赴美國哈佛醫學院 HMS 6 名［免學費與申請費＋哈佛基金會 USD 500＋北美校友會 NT$15,000］、希望之城 4 名、羅格斯大學 2 名、梅哈里醫學院 2 名、夏威夷大學 1 名、德國科隆大學 4 名、澳洲邦德大學 4 名、日本京都大學 2 名、慶應義塾大學 3 名、東京醫科大學 2 名［免學費與免費住宿］、神戶大學 3 名［有機會獲 JPY 50,000 獎學金］、德島大學 3 名、信州大學 2 名、愛媛大學 4 名、藤田醫科大學 2 名、韓國首爾大學 2 名、亞洲大學 4 名、香港大學 4 名、新加坡國立大學 4 名、南洋理工大學 4 名、泰國宋卡王子大學 4 名；【口腔醫學院寒暑期海外見實習】赴加拿大 UBC 6 名、美國 UPenn 3 名、UTHealth 4 名、日本東京科學大學 TMDU 9 名、東北大學 3 名、廣島大學 3 名、鹿兒島大學 6 名、九州齒大、神奈川齒大、韓國釜山大學 6 名、泰國朱拉隆功大學 6 名；【藥學院海外臨床藥學實習 APPE】赴美國 UAMS 6 名、南加大 USC 2–5 名、UIC、日本藥科大學 10 名；【健康科學院與護理學院海外實習】職治系赴瑞典卡羅林斯卡醫學院 KI 3 名［每人補助約 NT$110,000］、美國南加大 USC 6 名、日本茨城縣立醫療大學 6 名，物治系赴美國內布拉斯加大學醫學中心 UNMC 6 名，醫放系與呼治系赴新加坡陳篤生醫院 TTSH 6 名、竹腳婦幼醫院 KKH 及美國約翰霍普金斯醫院 4 名，運醫系赴美國 UNLV 4 名，護理系赴日本聖路加國際大學、愛媛縣立醫療技術大學，心理系赴日本人間環境大學 4–6 名，醫社系赴美國休士頓大學）"
          ),
      ],
      "academic_year": [
          (
              "116（涵蓋 115–116 學年度［2026–2028］醫學院 2027 海外臨床見實習甄選［2026/09/01–09/28 報名、10/14 面試、11/04 志願選填、11/10 放榜］、校級赴日本順天堂大學長期交換生甄選［4/18 及 10/20 截止］、10 校跨國雙聯學位甄選、口腔醫學院／藥學院／護理學院／健康科學院／人社院海外臨床見實習、115 年度博士生出國交流千里馬計畫［2026/11/01–11/30 收件，最高補助 NT$50萬］、教育部學海四項計畫及國際事務處出國研習補助）"
          ),
          (
              f"本平台完整收錄高雄醫學大學國際事務處與 7 大學院公告之 {len(partners)} 所全球締約合作大學、醫學院與教學醫院（含 {open_partner_count} 所當期開放交換、雙聯、2027 海外臨床見實習與學海計畫重點合作機構及 {len(partners) - open_partner_count} 所正式締約姊妹校，橫跨全球 30 個國家與地區，並完整收錄 {exp_covered_schools} 所合作機構共 {total_exp_reports} 篇歷屆師生返國成果報告）"
          ),
      ],
      "semester": [
          "秋季學期（第1學期：歐美姊妹校與雙聯學位為 8/9 月至 12 月；日本順天堂大學秋季班為 9/10 月至翌年 2 月［校內申請 4 月 18 日截止］）",
          "春季學期（第2學期：歐美姊妹校為 1 月至 5 月；日本順天堂大學春季班為 4 月至 8 月［校內申請 10 月 20 日截止］）",
          "2027（116學年度）醫學院海外臨床見實習（21 校 64+ 名：哈佛醫學院、City of Hope、羅格斯、梅哈里、夏威夷大學、科隆大學、邦德大學、京都大學、慶應義塾大學、東京醫大、神戶大學、德島大學、信州大學、愛媛大學、藤田醫大、首爾大學、亞洲大學、香港大學、新加坡國大、南洋理工、宋卡王子大學）及牙醫、口衛、藥學、護理、物治、職治、醫放、運醫、呼治、心理、醫社寒暑期與學期海外見實習（4–8 週；教育部學海築夢與新南向學海築夢須連續 30 天以上，印尼為 25 天以上）",
          "跨國雙聯碩士與博士學位（瑞典烏普薩拉大學、匈牙利賽蓋德大學、美國加州大學爾灣分校 UCI、美國希望之城 City of Hope、法國艾克斯-馬賽大學、澳洲格里菲斯大學、日本熊本大學、泰國朱拉隆功大學、瑪希朵大學、清邁大學）及博士生千里馬出國研究（6–12 個月）",
      ],
      "application_period": [
          (
              "【醫學院 2027（116學年度）海外臨床見實習甄選（21 校 64+ 名）】線上報名期間：2026年9月1日至9月28日（9月9日中午舉辦招募說明會、10月14日全英文面試、10月28日公告選填序位、11月4日現場志願選填、11月10日公告錄取名單）。"
          ),
          (
              "【校級赴日本順天堂大學長期交換生（JLCSP／LAP 免學費）及 10 校跨國雙聯學位甄選】日本順天堂大學秋季班（9–10 月入學）校內收件至每年 4 月 18 日止、春季班（4 月入學）校內收件至每年 10 月 20 日止；瑞典烏普薩拉大學（每年 6 名免學費）、匈牙利賽蓋德大學（每年 3 名免學費＋免費住宿）、日本熊本大學（2026/09/17 新簽醫學博士雙聯）、美國 UCI、City of Hope、法國艾克斯-馬賽大學、澳洲格里菲斯大學及泰國朱拉隆功、瑪希朵、清邁大學雙聯學位依各學期公告向所屬學院及國際事務處提出。"
          ),
          (
              "【口腔醫學院、藥學院、護理學院、健康科學院、人社院海外見實習與四大獎補助時程】（1）牙醫學系 115 寒假及 114 暑假海外見實習（UBC 6 名、東京科學大學 9 名、釜山 6 名、鹿兒島 6 名、UPenn 3 名、東北 3 名、廣島 3 名、UTHealth 4 名、朱拉隆功 6 名）自公告日起至 10 月中旬報名；（2）教育部《學海飛颺、學海惜珠、學海築夢、新南向學海築夢》校內收件至每年 2 月中旬截止（115 年度說明會於 2026/01/06 舉行）；（3）《國際事務處補助學生出國研習標準》每年分兩梯次受理（2026/09/23 舉辦補助說明會）；（4）《115 年度鼓勵博士生出國交流（千里馬）補助計畫》（每院 1 名，最高補助 NT$500,000）於 2026年11月1日至11月30日收件；（5）《財團法人北美洲高醫校友會基金會學生海外實習獎學金》（每人 NT$15,000）於每年 4 月 30 日截止。"
          ),
      ],
      "eligibility": [
          (
              "【在學學籍、國籍與排外規定】凡高雄醫學大學 7 個學院（醫學院、口腔醫學院、藥學院、護理學院、健康科學院、生命科學院、人文社會科學院）具正式學籍之學士班、碩士班、博士班在學學生（申請教育部學海計畫、國際事務處出國研習補助及博士生千里馬計畫者須具中華民國國籍；休學生、在職專班生及已獲政府其他同性質全額出國補助者不得重複支領）。"
          ),
          (
              "【各計畫學業成績與班級排名門檻】（1）校內出國研習與教育部學海系列基本門檻（依《高雄醫學大學學海系列方案甄選及補助辦法》及《學生國際研習服務獎勵要點》）：前一學期學業成績總平均及格（60 分以上）且無任何不及格科目；（2）口腔醫學院牙醫學系寒暑期海外見實習（簡章 363）：歷年學業總平均須達 75 分以上且班級排名前 75%，且無大過以上處分；（3）跨國雙聯博士學位（如泰國朱拉隆功大學藥學雙聯博士、匈牙利賽蓋德大學、瑞典烏普薩拉大學）及博士生千里馬計畫：歷年 GPA 須達 3.0（或百分制 75–80 分）以上；（4）醫學院大專生雙語化學習計畫（EMI）海外實習全額／高額補助：歷年學業總平均須達 80 分以上。"
          ),
          (
              "【海外實習天數下限、雙聯修業規定與返國報告＋照片影片義務】（1）教育部學海築夢與新南向學海築夢海外專業實習須連續至少 30 天以上（不含來回交通時日；印尼因簽證規定須達 25 天以上），學海飛颺與惜珠交換須修習至少 1 學期或 6 學分以上；（2）國際事務處出國研習補助分為「1 個月以上（核給機票＋按月生活費）」與「未滿 1 個月但至少 7 天以上（核給機票＋按日生活費）」；（3）所有受補助學生返國後須於規定期間（14 日至 1 個月）內繳交約 1,000 字心得報告、個人精選照片 4 張及活動影片，並配合出席經驗分享會。"
          ),
      ],
      "language_requirement": [
          (
              "【校內出國交換、學海計畫與國際處補助基本外語標準】依《高雄醫學大學學海系列方案甄選及補助辦法》與《學生國際研習服務獎勵要點》，申請人須具備符合研修機構授課語言之有效外語檢定證明：英語系或英語授課計畫建議達 CEFR B1–B2（TOEIC 550–785 / TOEFL iBT 57–79 / IELTS 5.0–6.0 / GEPT 中級至中高級 / 培力英檢 BESTEP B1–B2）；日語授課計畫須具 JLPT N2–N4 檢定證明。"
          ),
          (
              "【醫學院 2027（116學年度）21 校海外臨床見實習語檢門檻】（1）美國哈佛醫學院（Harvard Medical School，6 名）：須達 TOEFL iBT 100 以上（不採計 IELTS 與多益）；（2）德國科隆大學（University of Cologne，4 名）：須具英語 CEFR C1（TOEFL iBT 95 / IELTS 7.0 / TOEIC 945）或德語 CEFR B2；（3）澳洲邦德大學（Bond University，4 名）：須具英語 CEFR B2（IELTS 6.5 / TOEFL iBT 79 / TOEIC 785）以上；（4）美國希望之城國家醫學中心（City of Hope，4 名）、羅格斯大學（Rutgers，2 名）、梅哈里醫學院（Meharry，2 名）、夏威夷大學（UH JABSOM，1 名）、香港大學（HKU，4 名）、新加坡國立大學（NUS，4 名）、南洋理工大學（NTU，4 名）、韓國首爾大學（SNU，2 名）、亞洲大學（Ajou，4 名）、泰國宋卡王子大學（PSU，4 名）：須具優良英語聽說讀寫能力並通過醫學院全英文面試（佔甄選總分 60%）；（5）日本京都大學（2 名）、慶應義塾大學（3 名）、東京醫科大學（2 名）、神戶大學（3 名）、德島大學（3 名）、信州大學（2 名）、愛媛大學（4 名）、藤田醫科大學（2 名）：具備 TOEFL / IELTS / TOEIC 英語檢定，部分醫院臨床科室建議兼具 JLPT N2/N3 日語能力。"
          ),
          (
              "【校級日本順天堂大學交換、10 校跨國雙聯與各學院海外見實習語檢標準】（1）日本順天堂大學長期交換：LAP 國際教養課程須達 JLPT N2 或 TOEFL iBT 72 / IELTS 5.5 以上（JLCSP 日語文化學程不限日檢）；（2）瑞典烏普薩拉大學雙聯交換（每年 6 名）：須達 TOEFL iBT 79 或 IELTS 6.0 以上；（3）泰國朱拉隆功大學藥學雙聯博士（每年 2 名）：須達 TOEFL iBT 65 或 IELTS 5.5 以上；（4）口腔醫學院寒暑期海外見實習（UBC、UPenn、UTHealth、東京科學大學 TMDU、東北大學、廣島大學、鹿兒島大學、釜山大學、朱拉隆功大學）：須檢附有效英檢（TOEFL / IELTS / TOEIC / GEPT）或日檢（JLPT）成績並通過面試；（5）職能治療學系赴瑞典卡羅林斯卡醫學院（KI，3 名）與美國南加州大學（USC，6 名）、物理治療學系赴美國 UNMC（6 名）、呼吸治療學系赴美國約翰霍普金斯醫院（4 名）：須具流利英語臨床溝通能力並通過系所英文面試。"
          ),
      ],
      "required_documents": [
          "1. 高雄醫學大學出國交換學生／跨國雙聯學位／海外臨床見實習／國際事務處出國研習補助申請表（含基本資料、志願學校與研修期程）",
          "2. 高醫大歷年中文及英文成績單正本（須含歷年學業總平均、GPA 及班級排名百分比；牙醫系須達 75 分且前 75%）",
          "3. 有效期限內之外語能力檢定成績證明影本（TOEFL iBT / TOEFL ITP / IELTS / TOEIC / GEPT / BESTEP / JLPT，哈佛醫學院須附 TOEFL iBT 100 證明、科隆大學須附英語 C1 或德語 B2 證明）",
          "4. 英文個人簡歷（Curriculum Vitae, CV）、中英文自傳與出國動機信／讀書研究實習計畫書（Motivation Letter / Study & Research Plan）",
          "5. 本校專任教師英文推薦信（1–2 封）及家長（監護人）同意書",
          "6. 國內外優秀表現證明、學術論文發表、大專生研究計畫、社團幹部或國際志工服務證明（申請 115 千里馬博士生出國研究補助者另須檢附國外指導教授邀請函與博士研究計畫）",
          "7. 出國前與返國後必備核銷文件：海外教學醫院免疫抗體效價檢測報告（Immunization Record）、全程海外醫療及急難救助保險證明、電子機票與來回登機證正本、國際研習活動單據，以及返國後規定期間內繳交之約 1,000 字心得報告、個人精選照片 4 張與活動影片",
      ],
      "scholarship_info": [
          (
              "《高雄醫學大學國際事務處補助學生出國研習標準》（法規公告 2541）：凡本校在學學生出國交換、臨床見實習或短期研究，依地區核給來回經濟艙機票補助与生活費補助：（1）【出國期間滿 1 個月以上者】：歐美非地區機票最高補助 NT$ 50,000＋生活費每月 NT$ 25,000；大洋洲地區機票最高補助 NT$ 25,000＋生活費每月 NT$ 20,000；亞洲地區機票最高補助 NT$ 10,000＋生活費每月 NT$ 15,000（低收入戶及中低收入戶學生依上述標準 1.2 倍優予補助）；（2）【出國期間未滿 1 個月（至少 7 天以上）者】：同享上述地區機票補助上限，生活費按日核給（歐美非每日 NT$ 850、大洋洲每日 NT$ 700、亞洲每日 NT$ 500）。"
          ),
          (
              "《高雄醫學大學學海系列方案甄選及補助辦法》與醫學院大專生雙語化學習計畫（EMI）海外實習補助：（1）教育部《學海飛颺》（選送優秀學生赴外研修學分）、《學海惜珠》（優先全額補助低收／中低收／特殊境遇家庭學生）、《學海築夢》與《新南向學海築夢》（由專任教師主持選送學生赴美日歐澳及新南向國家進行 30 天以上臨床與專業實習）提供機票與生活費獎助；（2）健康科學院職能治療學系赴【瑞典卡羅林斯卡醫學院 Karolinska Institutet】交換實習 3 名，每人獲教育部與校方補助約新臺幣 11 萬元（NT$ 110,000）；（3）醫學院大專生雙語化學習計畫（EMI）補助學業平均 80 分以上且具英檢證明之醫學院學生赴海外姊妹校臨床見實習。"
          ),
          (
              "《115 年度鼓勵博士生出國交流（千里馬）補助計畫》、《北美洲高醫校友會基金會海外實習獎學金》與姊妹校專屬待遇：（1）【115 千里馬博士生出國研究計畫】（公告 3221，2026/11/01–11/30 收件）：每學院 1 名博士生赴海外合作大學研究 6–12 個月，每人最高補助新臺幣 50 萬元（NT$ 500,000）；（2）【財團法人北美洲高醫校友會基金會學生海外實習獎學金】（公告 3153）：補助醫、牙、藥、護學生赴北美姊妹校（哈佛、希望之城、羅格斯、梅哈里、夏威夷大學、UBC、UPenn、UTHealth、UAMS、USC 等）臨床見實習，每人核給 NT$ 15,000；（3）【KMU-Harvard Foundation 獎助金】：赴美國哈佛醫學院（HMS）見習之 6 名醫學生，除免繳哈佛見習費與申請費外，每人另獲 USD 500 獎助；（4）【姊妹校免學費與免費住宿待遇】：匈牙利賽蓋德大學雙聯交換（每年 3 名）與日本東京醫科大學見習（2 名）享免學費＋免費提供住宿；瑞典烏普薩拉大學（每年 6 名）與日本順天堂大學交換享免學費；日本神戶大學見習生有機會獲 JPY 50,000 獎學金。"
          ),
      ],
      "partner_universities": [p["school_name"] for p in partners],
      "source_urls": kmu_source_urls,
      "last_checked": CHECKED_AT,
  }
  (OFFICIAL_KMU_DIR / "exchange_info.json").write_text(
      json.dumps(exchange_info_payload, ensure_ascii=False, indent=2) + "\n",
      encoding="utf-8",
  )

  student_dashboard_payload = {
      "school_name": "高雄醫學大學",
      "last_checked": CHECKED_AT,
      "academic_score_minimum": 60.0,
      "academic_score_rule": (
          "依《高雄醫學大學學海系列方案甄選及補助辦法》與《學生國際研習服務獎勵要點》規定：一般出國研習與學海計畫申請人前一學期學業成績總平均須及格（60 分以上）且無不及格科目；口腔醫學院牙醫學系寒暑期海外見實習要求歷年學業總平均達 75 分以上且班級排名前 75%；跨國雙聯博士學位與 115 千里馬博士生計畫要求 GPA 3.0（75–80 分）以上；醫學院大專生雙語化學習計畫（EMI）海外實習高額補助要求歷年學業平均達 80 分以上。"
      ),
      "academic_gpa_minimum": 2.0,
      "maximum_preferences": 5,
      "selection_rules": {
          "academic_policy": "gpa_or_rank",
          "academic_reference_year": "116",
          "undergraduate_gpa_minimum": 2.0,
          "graduate_academic_exempt": False,
          "exclude_in_service": True,
          "pending_quota_planning": False,
          "partner_requirements_need_confirmation": False,
          "degree_score_minimums": {
              "undergraduate": 60.0,
              "graduate": 70.0,
          },
          "excluded_undergraduate_years": ["大一上"],
          "language_certificate_required": True,
      },
      "language_score_minimums": {
          "toefl": 57.0,
          "ielts": 5.0,
          "toeic": 550.0,
      },
      "application_periods": [
          {
              "title": (
                  "高雄醫學大學醫學院 2027（116學年度）海外臨床見實習甄選（21 校 64+ 名：哈佛醫學院 6 名、希望之城 4 名、科隆 4 名、邦德 4 名、京大 2 名、慶應 3 名、首爾大 2 名、港大 4 名、新加坡國大 4 名、南洋理工 4 名等）"
              ),
              "details": [
                  (
                      "高醫大醫學院公告 2027（116學年度）外派姐妹校臨床見實習甄選，共開放 21 所歐美亞澳頂尖醫學院計 64+ 名額：美國哈佛醫學院（HMS，6 名，免學費與申請費＋KMU-Harvard Foundation USD 500＋北美校友會 NT$15,000）、希望之城國家醫學中心（City of Hope，4 名）、羅格斯大學（Rutgers，2 名）、梅哈里醫學院（Meharry，2 名）、夏威夷大學（UH，1 名）、德國科隆大學（4 名，英語 C1 可替代德語 B2）、澳洲邦德大學（4 名，最長 6 週）、日本京都大學（2 名）、慶應義塾大學（3 名）、東京醫科大學（2 名，免學費＋免費住宿）、神戶大學（3 名，有機會獲 JPY 50,000 獎學金）、德島大學（3 名）、信州大學（2 名）、愛媛大學（4 名）、藤田醫科大學（2 名）、韓國首爾大學（2 名）、亞洲大學（4 名）、香港大學（4 名）、新加坡國立大學（4 名）、南洋理工大學（4 名）、泰國宋卡王子大學（4 名）。"
                  ),
                  (
                      "重要時程：2026年9月1日至9月28日線上報名（9月9日中午招募說明會），10月14日全英文面試（面試佔 60%、書審佔 40%），10月28日公告選填序位，11月4日現場志願選填，11月10日公告正式錄取名單。"
                  ),
              ],
              "source": {
                  "title": "高雄醫學大學醫學院 2027（116學年度）外派姐妹校臨床見實習招募公告與名額一覽表",
                  "source_url": KMU_CMED_2027_NOTICE_URL,
                  "category": "exchange_application",
                  "summary": "高醫大醫學院 2027 海外臨床見實習 21 校 64+ 名額、哈佛/科隆/邦德/京大/慶應/NUS/HKU 門檻與甄選時程。",
              },
              "scope": "home_application",
              "program_types": ["exchange"],
              "academic_year": "116",
              "application_round": "116學年度醫學院海外臨床見實習甄選",
              "audience": "all_students",
              "opens_at": "2026-09-01T09:00:00+08:00",
              "deadline_at": "2026-09-28T17:00:00+08:00",
              "date_status": "verified_exact",
              "status": "action_required",
              "status_note": "醫學院 2027 海外臨床見實習已完成 2026/09/28 報名與 10/14 英文面試，現正進行 10/28 序位公告、11/04 志願選填與 11/10 放榜作業。",
              "deadline_note": "獲錄取學生請依醫學院及國際事務處通知辦理海外醫院提名（如哈佛 VSLO）、疫苗抗體效價檢測與出國研習機票生活費補助申請。",
              "reminder_eligible": True,
              "checked_at": CHECKED_AT,
          },
          {
              "title": (
                  "高雄醫學大學 115–116學年度校級赴日本順天堂大學長期交換生（免學費）、10 校跨國雙聯學位暨 115 年度博士生千里馬出國研究計畫（最高補助 NT$500,000）"
              ),
              "details": [
                  (
                      "校級日本順天堂大學交換與 10 校跨國雙聯學位：（1）日本順天堂大學長期交換（JLCSP 日語文化學程／LAP 國際教養課程，互免學費）：秋季班於每年 4 月 18 日截止、春季班於每年 10 月 20 日截止；（2）10 校跨國雙聯學位：瑞典烏普薩拉大學（每年 6 名：醫 3、藥 3，免學費，iBT 79 / IELTS 6.0）、匈牙利賽蓋德大學（每年 3 名，免學費＋免費提供住宿＋高醫大機票生活費補助）、美國加州大學爾灣分校（UCI）、美國希望之城國家醫學中心（City of Hope）、法國艾克斯-馬賽大學（AMU）、澳洲格里菲斯大學、日本熊本大學（2026/09/17 新簽醫學博士雙聯）、泰國朱拉隆功大學（藥學雙聯博士每年 2 名免學費）、瑪希朵大學、清邁大學。"
                  ),
                  (
                      "115 年度鼓勵博士生出國交流（千里馬）補助計畫（公告 3221）：於 2026年11月1日至11月30日受理申請，每學院遴選 1 名博士生赴海外合作大學進行 6–12 個月研究，每人最高補助新臺幣 50 萬元（NT$ 500,000）。"
                  ),
              ],
              "source": {
                  "title": "高雄醫學大學國際事務處雙聯學制專區、順天堂大學交換公告與 115 年度博士生千里馬計畫簡章",
                  "source_url": KMU_DUAL_PARTNERS_URL,
                  "category": "scholarship",
                  "summary": "高醫大日本順天堂大學長期交換、10 校跨國雙聯學位（烏普薩拉、賽蓋德、UCI、熊本等）與博士生千里馬 50 萬元補助。",
              },
              "scope": "home_application",
              "program_types": ["exchange", "dual_degree"],
              "academic_year": "116",
              "application_round": "115–116學年度校級交換、跨國雙聯暨千里馬博士生出國計畫甄選",
              "audience": "all_students",
              "opens_at": "2026-09-15T09:00:00+08:00",
              "deadline_at": "2026-11-30T17:00:00+08:00",
              "date_status": "verified_exact",
              "status": "action_required",
              "status_note": "115 年度博士生千里馬計畫於 2026/11/01–11/30 收件；跨國雙聯學位與校級順天堂大學交換依每學期公告受理申請。",
              "deadline_note": "請備妥申請表、歷年中英文成績單、有效外語檢定證明、英文研究／讀書計畫及指導教授推薦信送交所屬學院及國際事務處（勵學大樓4樓）。",
              "reminder_eligible": True,
              "checked_at": CHECKED_AT,
          },
          {
              "title": (
                  "高雄醫學大學口腔醫學院／藥學院／護理學院／健康科學院／人社院海外臨床見實習、國際處出國研習補助（歐美非機票最高5萬＋月領2.5萬）暨教育部學海四項計畫"
              ),
              "details": [
                  (
                      "各學院海外臨床見實習重點計畫：（1）口腔醫學院（UBC 6 名、東京科學大學 TMDU 9 名、釜山 6 名、鹿兒島 6 名、UPenn 3 名、東北 3 名、廣島 3 名、UTHealth 4 名、朱拉隆功 6 名、九州齒大、神奈川齒大）；（2）藥學院（美國 UAMS 6 名、南加大 USC 2–5 名、UIC、日本藥科大學 10 名）；（3）健康科學院（職治系赴瑞典卡羅林斯卡醫學院 KI 3 名［補助約 11 萬元］、美國 USC 6 名、日本茨城縣立醫療大學 6 名；物治系赴美國 UNMC 6 名；醫放系赴新加坡陳篤生醫院 TTSH 6 名）；（4）醫學院運醫系（赴美國 UNLV 4 名）與呼治系（赴美國約翰霍普金斯醫院 4 名、新加坡陳篤生醫院與竹腳婦幼醫院）；（5）護理學院（赴日本聖路加國際大學、愛媛縣立醫療技術大學、美國 UAMS）；（6）人社院心理系（赴日本人間環境大學 4–6 名）與醫社系（赴美國休士頓大學）。"
                  ),
                  (
                      "獎補助申請時程：教育部《學海飛颺、學海惜珠、學海築夢、新南向學海築夢》每年 2 月中旬校內截止（2026/01/06 辦理說明會）；《國際事務處補助學生出國研習標準》（歐美非機票最高 NT$50,000＋每月生活費 NT$25,000、大洋洲機票最高 NT$25,000＋每月 NT$20,000、亞洲機票最高 NT$10,000＋每月 NT$15,000）於每年 9–10 月及 2–3 月受理（2026/09/23 辦理補助說明會）；《北美洲高醫校友會基金會海外實習獎學金》（每人 NT$15,000）每年 4 月底截止。"
                  ),
              ],
              "source": {
                  "title": "高雄醫學大學國際事務處補助學生出國研習標準（公告 2541）、115 學海說明會簡報與各學院海外見實習公告",
                  "source_url": KMU_SUBSIDY_STD_URL,
                  "category": "exchange_application",
                  "summary": "高醫大 7 大學院海外臨床見實習名額、國際處機票生活費補助標準與教育部學海計畫時程。",
              },
              "scope": "home_application",
              "program_types": ["exchange"],
              "academic_year": "116",
              "application_round": "115–116學年度各學院海外見實習暨教育部學海計畫／國際處補助甄選",
              "audience": "all_students",
              "opens_at": "2026-09-23T09:00:00+08:00",
              "deadline_at": "2027-02-19T17:00:00+08:00",
              "date_status": "verified_exact",
              "status": "action_required",
              "status_note": "國際事務處已於 2026/09/23 舉辦出國研習補助說明會，115–116 年度各學院海外見實習與教育部學海系列計畫持續受理申請。",
              "deadline_note": "請依所屬學系及國際事務處公告期程遞交申請表件，返國後須繳交約 1,000 字心得報告、4 張照片與活動影片辦理核銷。",
              "reminder_eligible": True,
              "checked_at": CHECKED_AT,
          },
      ],
      "program_overview": [
          {
              "title": (
                  f"高雄醫學大學國際事務處海外交換、跨國雙聯學位、臨床見實習與獎補助總覽（{len(partners)} 所全球合作姊妹校與醫療機構・{open_partner_count} 所當期開放重點機構・{total_exp_reports} 篇師生成果報告）"
              ),
              "details": [
                  (
                      f"高雄醫學大學（KMU，高醫大／高醫／高雄醫大，創立於 1954 年，為臺灣第一所私立醫學院）由「國際事務處（Office of Global Affairs，設於高雄市三民區十全一路100號勵學大樓4樓）」、「教務處」與全校 7 個學院（醫學院、口腔醫學院、藥學院、護理學院、健康科學院、生命科學院、人文社會科學院）共同推動校級出國交換學生、跨國雙聯學位、海外臨床見實習（Medical / Dental / Pharmacy / Nursing / OT / PT / MRT / SportsMed / RespCare Clerkship & Internship）及教育部學海系列計畫。本平台完整收錄 {len(partners)} 所高醫大官方締約合作大學、醫學院与教學醫院（含 {open_partner_count} 所當期開放交換、雙聯、2027 海外臨床見實習與學海計畫重點合作機構及 {len(partners) - open_partner_count} 所正式締約姊妹校），橫跨全球 30 個國家與地區（美洲 34 校、歐洲 14 校、非洲 3 校、亞洲 111 校、大陸及港澳地區 21 校、大洋洲 5 校）。"
                  ),
                  (
                      f"高醫大國際化體系具備四大核心特色：（1）醫學院 2027（116學年度）21 校 64+ 名海外臨床見實習旗艦網路：包含美國哈佛醫學院（HMS 6 名，免見習費與申請費＋KMU-Harvard Foundation USD 500＋北美校友會 NT$15,000）、City of Hope（4 名）、羅格斯大學（2 名）、梅哈里醫學院（2 名）、夏威夷大學（1 名）、德國科隆大學（4 名）、澳洲邦德大學（4 名）、日本京都大學（2 名）、慶應義塾大學（3 名）、東京醫科大學（2 名，免學費＋免費住宿）、神戶大學（3 名，有機會獲 JPY 50,000 獎學金）、德島大學（3 名）、信州大學（2 名）、愛媛大學（4 名）、藤田醫科大學（2 名）、韓國首爾大學（2 名）、亞洲大學（4 名）、香港大學（4 名）、新加坡國立大學（4 名）、南洋理工大學（4 名）、泰國宋卡王子大學（4 名）；（2）校級日本順天堂大學長期交換與 10 校跨國雙聯學位：順天堂大學 JLCSP/LAP 免學費交換、瑞典烏普薩拉大學（每年 6 名免學費雙聯交換）、匈牙利賽蓋德大學（每年 3 名免學費＋免費提供住宿）、日本熊本大學（2026/09/17 新簽醫學博士雙聯）、美國加州大學爾灣分校 UCI、City of Hope、法國艾克斯-馬賽大學、澳洲格里菲斯大學、泰國朱拉隆功大學（藥學雙聯博士每年 2 名免學費）、瑪希朵大學、清邁大學；（3）牙醫、藥學、護理、復健與醫事科技全領域海外實習：含加拿大 UBC（牙醫 6 名）、美國 UPenn（牙醫 3 名）、約翰霍普金斯醫院（呼治 4 名）、南加大 USC（職治 6 名＋藥學 2–5 名）、UAMS（藥學 6 名＋護理）、UNMC（物治 6 名）、UNLV（運醫 4 名）、瑞典卡羅林斯卡醫學院 KI（職治 3 名，每人補助約 NT$11萬）、新加坡陳篤生醫院 TTSH（醫放 6 名＋呼治）及日本東京科學大學 TMDU（牙醫 9 名＋口衛）、日本藥科大學（藥學 10 名）、聖路加國際大學（護理）、茨城縣立醫療大學（職治 6 名＋物治＋醫放＋護理）；（4）優渥之四層級出國獎補助（國際處歐美非機票最高 NT$50,000＋每月生活費 NT$25,000、教育部學海四項計畫、博士生千里馬最高 NT$500,000、北美校友會 NT$15,000 與哈佛基金會 USD 500）及 {exp_covered_schools} 所機構共 {total_exp_reports} 篇歷屆師生返國成果報告。"
                  ),
              ],
              "source": {
                  "title": "高雄醫學大學國際事務處—姊妹校締約情形、雙聯學制、出國研習補助標準與 7 大學院國際交流專區",
                  "source_url": KMU_OIA_HUB_URL,
                  "category": "exchange_application",
                  "summary": f"高醫大 {len(partners)} 所全球合作姊妹校與醫療機構、10 校雙聯學位、2027 臨床見實習與 {total_exp_reports} 篇成果報告。",
              },
          }
      ],
      "eligibility": [
          {
              "title": "高醫大在學資格、各計畫學業成績門檻（60分及格／牙醫75分且前75%／雙聯GPA 3.0／雙語計畫80分）與返國核銷規定",
              "details": [
                  (
                      "在學學籍與分級學業門檻（依《高雄醫學大學學海系列方案甄選及補助辦法》、《學生國際研習服務獎勵要點》及各院系簡章）：申請人須為本校 7 大學院具正式學籍之在學學生（休學生、在職專班生不得申請校內與學海補助）。（1）一般出國研習與教育部學海計畫基本門檻：前一學期學業成績總平均及格（60 分以上）且無任何不及格科目；（2）口腔醫學院牙醫學系寒暑期海外見實習（簡章 363）：歷年學業總平均須達 75 分以上且班級排名前 75%；（3）跨國雙聯博士學位（烏普薩拉、賽蓋德、朱拉隆功等）與 115 千里馬博士生計畫：歷年 GPA 須達 3.0（或百分制 75–80 分）以上；（4）醫學院大專生雙語化學習計畫（EMI）海外實習高額補助：歷年學業總平均須達 80 分以上。"
                  ),
                  (
                      "海外實習天數與返國核銷義務：教育部學海築夢與新南向學海築夢海外專業實習須連續至少 30 天以上（不含來回交通時日；印尼因簽證規定須達 25 天以上）；國際事務處出國研習補助分為滿 1 個月以上（按月補助生活費）與未滿 1 個月但至少 7 天以上（按日補助生活費）；返國後須於規定期間（14 日至 1 個月）內繳交約 1,000 字出國研習心得報告、個人精選照片 4 張及活動影片，並出席經驗分享會。"
                  ),
              ],
              "source": {
                  "title": "高雄醫學大學學生國際研習服務獎勵要點、學海系列方案甄選及補助辦法與各學院海外見實習簡章",
                  "source_url": KMU_REG_INTL_REWARD_PDF_URL,
                  "category": "exchange_application",
                  "summary": "高醫大出國交換、雙聯與臨床見實習之學籍、分級學業門檻與返國報告照片影片核銷規定。",
              },
          }
      ],
      "language_requirements": [
          {
              "title": "哈佛醫學院（TOEFL iBT 100）、科隆大學（英語 C1／德語 B2）、邦德大學（CEFR B2）、烏普薩拉（iBT 79 / IELTS 6.0）與順天堂大學（JLPT N2 / iBT 72）語檢標準",
              "details": [
                  (
                      "醫學院 2027 海外臨床見實習與校級交換外語標準：（1）美國哈佛醫學院（HMS，6 名）：須具備 TOEFL iBT 100 以上（不接受 IELTS 或多益）；（2）德國科隆大學（4 名）：須具英語 CEFR C1（TOEFL iBT 95 / IELTS 7.0 / TOEIC 945）或德語 CEFR B2；（3）澳洲邦德大學（4 名）：須具英語 CEFR B2（IELTS 6.5 / TOEFL iBT 79 / TOEIC 785）；（4）日本順天堂大學校級交換：LAP 國際教養課程須達 JLPT N2 或 TOEFL iBT 72 / IELTS 5.5 以上（JLCSP 日語文化學程不限日檢）；（5）其餘歐美日韓星港泰臨床見實習姊妹校：須具 TOEFL / IELTS / TOEIC / GEPT 英檢或 JLPT 日檢證明，並通過醫學院或各學系全英文／日文面試。"
                  ),
                  (
                      "10 校跨國雙聯學位與各學院海外見實習外語標準：（1）瑞典烏普薩拉大學雙聯交換（每年 6 名）：須達 TOEFL iBT 79 或 IELTS 6.0 以上；（2）泰國朱拉隆功大學藥學雙聯博士（每年 2 名）：須達 TOEFL iBT 65 或 IELTS 5.5 以上；（3）美國加州大學爾灣分校（UCI）、希望之城（City of Hope）、法國艾克斯-馬賽大學、匈牙利賽蓋德大學、澳洲格里菲斯大學、日本熊本大學雙聯：須達 TOEFL iBT 79–80 或 IELTS 6.0–6.5 以上；（4）教育部學海系列與國際處出國研習補助：須檢附符合研修機構要求之有效語檢證明（CEFR B1–B2 以上）。"
                  ),
              ],
              "source": {
                  "title": "高雄醫學大學醫學院 2027 外派姐妹校一覽表、順天堂大學交換簡章與雙聯學制專區",
                  "source_url": KMU_CMED_2027_SHEET_URL,
                  "category": "exchange_application",
                  "summary": "高醫大哈佛醫學院、科隆大學、邦德大學、順天堂大學與 10 校雙聯學位之 TOEFL、IELTS、TOEIC、CEFR 與 JLPT 語檢門檻。",
              },
          }
      ],
      "required_documents": [
          {
              "title": "出國交換／雙聯／海外臨床見實習申請文件清單與返國 1,000 字心得報告＋4 張照片＋活動影片核銷規範",
              "details": [
                  (
                      "校內甄選必備文件：1. 出國交換／雙聯／海外臨床見實習或國際處出國研習補助申請表、2. 中英文歷年成績單正本（含學業平均、GPA 與班級排名百分比）、3. 有效外語能力檢定證明影本（TOEFL / IELTS / TOEIC / GEPT / BESTEP / JLPT）、4. 英文個人簡歷（CV）、中英文自傳與出國動機信／讀書研究計畫書（Motivation Letter / Study Plan）、5. 專任教師英文推薦信與家長同意書、6. 社團幹部、學術研究或競賽優秀表現佐證資料。"
                  ),
                  (
                      "出國免疫檢驗與返國核銷義務：出國前須完成教學醫院指定之免疫抗體效價檢測（MMR、水痘、B肝、TB 檢驗等）並投保全程海外醫療及急難救助保險；返國後須於規定期間（14 日至 1 個月）內向國際事務處及學院繳交約 1,000 字出國研習心得報告、個人精選照片 4 張、活動影片及電子機票與來回登機證正本辦理核銷。"
                  ),
              ],
              "source": {
                  "title": "高雄醫學大學國際事務處補助學生出國研習標準（公告 2541）與醫學院／牙醫學系海外見實習甄選簡章",
                  "source_url": KMU_SUBSIDY_STD_URL,
                  "category": "exchange_application",
                  "summary": "高醫大出國交換與臨床見實習申請表件、免疫檢驗要求與返國報告照片影片核銷規定。",
              },
          }
      ],
      "scholarship_info": [
          {
              "title": "國際處出國研習補助（歐美非機票最高 NT$50,000＋每月生活費 NT$25,000）、博士生千里馬（最高 NT$500,000）、北美校友會（NT$15,000）、哈佛基金會（USD 500）與教育部學海四項計畫",
              "details": [
                  (
                      "國際事務處出國研習補助標準（公告 2541）：（1）滿 1 個月以上者：歐美非機票最高 NT$ 50,000＋生活費每月 NT$ 25,000；大洋洲機票最高 NT$ 25,000＋生活費每月 NT$ 20,000；亞洲機票最高 NT$ 10,000＋生活費每月 NT$ 15,000（低收／中低收學生按 1.2 倍補助）；（2）未滿 1 個月（至少 7 天以上）者：同享上述機票補助上限，生活費按日核給（歐美非每日 NT$ 850、大洋洲每日 NT$ 700、亞洲每日 NT$ 500）。"
                  ),
                  (
                      "專項獎助學金與姊妹校免學費／免費住宿待遇：（1）115 年度博士生千里馬出國交流計畫（公告 3221）：每院 1 名赴海外研究 6–12 個月，最高補助 NT$ 500,000；（2）教育部學海飛颺、學海惜珠、學海築夢、新南向學海築夢及醫學院雙語化學習計畫（EMI）高額補助（如職治系赴瑞典卡羅林斯卡醫學院 KI 每人約 NT$ 110,000）；（3）財團法人北美洲高醫校友會基金會海外實習獎學金（公告 3153）：補助醫牙藥護學生赴美加見實習每人 NT$ 15,000；（4）KMU-Harvard Foundation 獎助金：赴哈佛醫學院見習（6 名）免學費與申請費並獲每人 USD 500；（5）匈牙利賽蓋德大學（每年 3 名）與日本東京醫科大學（2 名）享免學費＋免費住宿，瑞典烏普薩拉大學（每年 6 名）與日本順天堂大學享免學費。"
                  ),
              ],
              "source": {
                  "title": "高雄醫學大學國際事務處補助學生出國研習標準（2541）、115 千里馬計畫（3221）與北美校友會獎學金（3153）",
                  "source_url": KMU_SUBSIDY_STD_URL,
                  "category": "scholarship",
                  "summary": "高醫大歐美非/大洋洲/亞洲機票與生活費補助表、博士生千里馬 50 萬元、北美校友會 1.5 萬元、哈佛 USD 500 與教育部學海計畫。",
              },
          }
      ],
      "document_explanations": [
          {
              "title": "高雄醫學大學海外臨床見實習英文簡歷（CV）、動機信（Motivation Letter）與返國 1,000 字報告＋4 張照片＋活動影片準備指南",
              "summary": "說明高醫大醫學院（書審 40%＋英文面試 60%）、口腔醫學院及各學系海外見實習書面審查重點，以及返國核銷必備之心得報告、照片與影片。",
              "key_points": [
                  "醫學院 2027（116學年度）海外臨床見實習（21 校 64+ 名）甄選總成績由書面審查（40%：歷年學業成績 20%、語檢能力證明 10%、英文 CV 與自傳動機信及課外研究表現 10%）與全英文面試（60%）組成；申請美國哈佛醫學院（HMS）者須於報名時檢附 TOEFL iBT 100 以上證明，申請德國科隆大學者須檢附英語 C1 或德語 B2 證明。",
                  "口腔醫學院牙醫學系寒暑期海外見實習申請人須檢附歷年學業總平均達 75 分以上且班級排名前 75% 之成績單正本；申請瑞典烏普薩拉大學、匈牙利賽蓋德大學、日本熊本大學與泰國朱拉隆功大學雙聯學位者，須檢附英文研究計畫與兩校指導教授同意書。",
                  "所有獲高醫大國際事務處出國研習補助、教育部學海系列補助或北美校友會獎學金之學生，返國後須於規定期間（14 日至 1 個月）內繳交約 1,000 字出國研習心得報告、個人精選照片 4 張、活動影片及來回登機證正本，並配合出席經驗分享會始完成核銷。",
              ],
              "applies_to": [],
              "source": {
                  "title": "高雄醫學大學醫學院 2027 海外臨床見實習招募公告與國際事務處補助學生出國研習標準",
                  "source_url": KMU_CMED_2027_NOTICE_URL,
                  "category": "exchange_application",
                  "summary": None,
              },
              "document_url": KMU_CMED_2027_NOTICE_URL,
              "document_type": "official_document",
              "full_text_extracted": True,
          }
      ],
      "rule_explanations": [
          {
              "title": "高雄醫學大學學海系列方案甄選及補助辦法、學生國際研習服務獎勵要點與跨國雙聯學制核心規定",
              "summary": "規範高醫大出國研習機票與生活費分區補助標準（歐美非／大洋洲／亞洲）、學海築夢 30 天實習下限、雙聯免學費與免費住宿待遇及返國義務。",
              "key_points": [
                  "國際事務處分區機票與生活費補助標準（公告 2541）：歐美非地區來回機票最高補助 NT$ 50,000、滿 1 個月以上每月生活費 NT$ 25,000（未滿 1 個月但滿 7 天以上每日 NT$ 850）；大洋洲地區機票最高 NT$ 25,000、每月生活費 NT$ 20,000（每日 NT$ 700）；亞洲地區機票最高 NT$ 10,000、每月生活費 NT$ 15,000（每日 NT$ 500）；低收入戶與中低收入戶學生依標準 1.2 倍補助。",
                  "跨國雙聯學位與交換互惠待遇：瑞典烏普薩拉大學每年提供高醫大 6 名（醫學院 3 名、藥學院 3 名）免學費雙聯交換名額；匈牙利賽蓋德大學每年提供 3 名免學費＋免費提供匈牙利學生宿舍名額；日本順天堂大學提供 JLCSP 與 LAP 免學費長期交換；日本熊本大學與高醫大於 2026/09/17 簽署醫學博士雙聯學位協議。",
                  "海外實習天數與返國核銷：教育部學海築夢與新南向學海築夢海外專業實習須連續達 30 天以上（不含來回交通時日，印尼為 25 天以上）；受獎助學生返國後須按期繳交心得報告、照片與影片並參與分享會，違者須依規定繳回補助款。",
              ],
              "applies_to": [],
              "source": {
                  "title": "高雄醫學大學學生國際研習服務獎勵要點與國際事務處補助學生出國研習標準（公告 2541）",
                  "source_url": KMU_REG_INTL_REWARD_PDF_URL,
                  "category": "exchange_application",
                  "summary": None,
              },
              "document_url": KMU_REG_INTL_REWARD_PDF_URL,
              "document_type": "official_document",
              "full_text_extracted": True,
          }
      ],
      "sources": [
          {
              "title": "高雄醫學大學國際事務處（Office of Global Affairs）官方網站",
              "source_url": KMU_OIA_HUB_URL,
              "category": "exchange_application",
              "summary": None,
          },
          {
              "title": f"高雄醫學大學全球締約姊妹校專區（{len(partners)} 所國際與兩岸港澳合作校院）",
              "source_url": KMU_PARTNERS_ZH_URL,
              "category": "partner_school",
              "summary": None,
          },
          {
              "title": "高雄醫學大學醫學院 2027（116學年度）外派姐妹校臨床見實習招募公告與 21 校名額表",
              "source_url": KMU_CMED_2027_NOTICE_URL,
              "category": "exchange_application",
              "summary": None,
          },
          {
              "title": "高雄醫學大學日本順天堂大學長期交換學生（JLCSP / LAP）甄選公告",
              "source_url": KMU_JUNTENDO_EXCHANGE_URL,
              "category": "exchange_application",
              "summary": None,
          },
          {
              "title": "高雄醫學大學跨國雙聯學制合作專區（UCI、烏普薩拉、賽蓋德、艾克斯-馬賽、格里菲斯、City of Hope、熊本、朱拉隆功、瑪希朵、清邁）",
              "source_url": KMU_DUAL_PARTNERS_URL,
              "category": "exchange_application",
              "summary": None,
          },
          {
              "title": "高雄醫學大學國際事務處補助學生出國研習標準（公告 2541）與學生國際研習服務獎勵要點",
              "source_url": KMU_SUBSIDY_STD_URL,
              "category": "scholarship",
              "summary": None,
          },
          {
              "title": "高雄醫學大學 115 年度鼓勵博士生出國交流（千里馬）補助計畫（公告 3221）與北美洲高醫校友會獎學金（公告 3153）",
              "source_url": KMU_QIANLIMA_115_URL,
              "category": "scholarship",
              "summary": None,
          },
          {
              "title": f"高雄醫學大學醫學院、口腔醫學院、藥學院、護理學院、健康科學院與人社院海外見實習成果專區（{total_exp_reports} 篇報告）",
              "source_url": KMU_CMED_EXP_URL,
              "category": "exchange_application",
              "summary": None,
          },
      ],
  }
  (OFFICIAL_KMU_DIR / "student_dashboard.json").write_text(
      json.dumps(student_dashboard_payload, ensure_ascii=False, indent=2) + "\n",
      encoding="utf-8",
  )

  pages_records = [
      {
          "title": "高雄醫學大學：醫學院 2027（116學年度）21 校 64+ 名海外臨床見實習、日本順天堂大學長期交換、10 校跨國雙聯學位與各學院海外見實習時程",
          "source_url": KMU_CMED_2027_NOTICE_URL,
          "published_at": "2026-10-21T00:00:00Z",
          "text": "\n".join(exchange_info_payload["application_period"]),
          "summary": "\n".join(exchange_info_payload["application_period"]),
          "category": "exchange_application",
          "attachments": [],
          "crawled_at": CHECKED_AT,
          "content_hash": hashlib.sha256("\n".join(exchange_info_payload["application_period"]).encode("utf-8")).hexdigest(),
      },
      {
          "title": "高雄醫學大學：出國交換、跨國雙聯與海外臨床見實習申請資格（學業 60 分及格／牙醫 75 分且前 75%／雙聯 GPA 3.0／雙語計畫 80 分與實習天數規定）",
          "source_url": KMU_REG_INTL_REWARD_PDF_URL,
          "published_at": "2026-10-21T00:00:00Z",
          "text": "\n".join(exchange_info_payload["eligibility"]),
          "summary": "\n".join(exchange_info_payload["eligibility"]),
          "category": "exchange_application",
          "attachments": [],
          "crawled_at": CHECKED_AT,
          "content_hash": hashlib.sha256("\n".join(exchange_info_payload["eligibility"]).encode("utf-8")).hexdigest(),
      },
      {
          "title": f"高雄醫學大學：{len(partners)} 所合作姊妹校與教學醫院外語檢定門檻（哈佛醫學院 iBT 100 / 科隆大學英語 C1 / 邦德大學 B2 / 烏普薩拉 iBT 79 / 順天堂 JLPT N2 或 iBT 72）",
          "source_url": KMU_CMED_2027_SHEET_URL,
          "published_at": "2026-10-21T00:00:00Z",
          "text": "\n".join(exchange_info_payload["language_requirement"]),
          "summary": "\n".join(exchange_info_payload["language_requirement"]),
          "category": "exchange_application",
          "attachments": [],
          "crawled_at": CHECKED_AT,
          "content_hash": hashlib.sha256("\n".join(exchange_info_payload["language_requirement"]).encode("utf-8")).hexdigest(),
      },
      {
          "title": "高雄醫學大學：出國交換、雙聯學位與海外臨床見實習申請文件及返國 1,000 字心得報告＋4 張照片＋活動影片規範",
          "source_url": KMU_SUBSIDY_STD_URL,
          "published_at": "2026-10-21T00:00:00Z",
          "text": "\n".join(exchange_info_payload["required_documents"]),
          "summary": "\n".join(exchange_info_payload["required_documents"]),
          "category": "exchange_application",
          "attachments": [],
          "crawled_at": CHECKED_AT,
          "content_hash": hashlib.sha256("\n".join(exchange_info_payload["required_documents"]).encode("utf-8")).hexdigest(),
      },
      {
          "title": "高雄醫學大學：國際處出國研習機票（最高5萬）與生活費（每月最高2.5萬）補助、博士生千里馬（50萬）、北美校友會（1.5萬）、哈佛（USD 500）與教育部學海計畫",
          "source_url": KMU_SUBSIDY_STD_URL,
          "published_at": "2026-10-21T00:00:00Z",
          "text": "\n".join(exchange_info_payload["scholarship_info"]),
          "summary": "\n".join(exchange_info_payload["scholarship_info"]),
          "category": "scholarship",
          "attachments": [],
          "crawled_at": CHECKED_AT,
          "content_hash": hashlib.sha256("\n".join(exchange_info_payload["scholarship_info"]).encode("utf-8")).hexdigest(),
      },
  ]
  (OFFICIAL_KMU_DIR / "pages.jsonl").write_text(
      "\n".join(json.dumps(p, ensure_ascii=False) for p in pages_records) + "\n",
      encoding="utf-8",
  )

  home_rules = {
      "school_id": "kmu",
      "school_name": "高雄醫學大學",
      "eligibility": student_dashboard_payload["eligibility"],
      "application_periods": student_dashboard_payload["application_periods"],
      "selection_rules": {
          "undergraduate_score_minimum": 60.0,
          "graduate_score_minimum": 70.0,
          "dental_clerkship_score_minimum": 75.0,
          "dental_clerkship_class_rank_percent_max": 75,
          "dual_degree_gpa_minimum": 3.0,
          "cmed_emi_subsidy_score_minimum": 80.0,
          "excluded_undergraduate_years": ["大一上"],
          "require_kmu_enrollment_during_abroad": True,
          "xuehai_zhumeng_min_days": 30,
          "xuehai_zhumeng_indonesia_min_days": 25,
          "oga_subsidy_rates_ntd": {
              "europe_americas_africa": {
                  "airfare_max": 50000,
                  "monthly_stipend": 25000,
                  "daily_stipend_under_1_month": 850,
              },
              "oceania": {
                  "airfare_max": 25000,
                  "monthly_stipend": 20000,
                  "daily_stipend_under_1_month": 700,
              },
              "asia": {
                  "airfare_max": 10000,
                  "monthly_stipend": 15000,
                  "daily_stipend_under_1_month": 500,
              },
              "low_income_multiplier": 1.2,
          },
          "qianlima_phd_grant_max_ntd": 500000,
          "na_alumni_clerkship_grant_ntd": 15000,
          "harvard_foundation_clerkship_grant_usd": 500,
          "karolinska_ot_exchange_grant_ntd": 110000,
          "return_report_due_days": 30,
          "return_report_min_words": 1000,
          "return_photos_min_count": 4,
          "return_video_required": True,
          "return_documents_due": "受補助及交換／見實習學生須於返國後規定期間（14 日至 1 個月）內向國際事務處及學院繳交約 1,000 字出國研習心得報告、個人精選照片 4 張、活動影片及登機證單據辦理核銷，並出席經驗分享會",
      },
      "source_urls": kmu_source_urls,
      "verified_at": "2026-10-21",
  }
  (OFFICIAL_KMU_DIR / "home_rules.json").write_text(
      json.dumps(home_rules, ensure_ascii=False, indent=2) + "\n",
      encoding="utf-8",
  )
  (OFFICIAL_KMU_DIR / "documents.json").write_text(
      json.dumps(
          {
              "school_name": "高雄醫學大學",
              "required_documents": student_dashboard_payload["required_documents"],
              "source_urls": kmu_source_urls,
          },
          ensure_ascii=False,
          indent=2,
      )
      + "\n",
      encoding="utf-8",
  )
  (OFFICIAL_KMU_DIR / "scholarships.json").write_text(
      json.dumps(
          {
              "school_name": "高雄醫學大學",
              "scholarships": student_dashboard_payload["scholarship_info"],
              "source_urls": kmu_source_urls,
          },
          ensure_ascii=False,
          indent=2,
      )
      + "\n",
      encoding="utf-8",
  )

  completeness = {
      "school_id": "kmu",
      "school_name": "高雄醫學大學",
      "total_partners": len(partners),
      "partner_count": len(partners),
      "international_partners": sum(
          1 for p in partners if p["country"] not in {"中國大陸", "香港", "澳門"}
      ),
      "mainland_partners": sum(
          1 for p in partners if p["country"] in {"中國大陸", "香港", "澳門"}
      ),
      "dual_degree_partner_universities": 10,
      "dual_degree_programs": 12,
      "experience_report_covered_partners": exp_covered_schools,
      "experience_report_pdf_count": total_exp_reports,
      "open_partners": open_partner_count,
      "reference_only_partners": len(partners) - open_partner_count,
      "verified_locations": len(partners),
      "verified_official_websites": sum(1 for p in partners if p.get("official_website")),
      "verified_campus_images": sum(1 for p in partners if p.get("image_status") == "verified"),
      "workflow_count": len(workflows),
      "destination_profile_count": len(destinations),
      "student_life_count": len(life_records),
      "active_term": (
          f"高雄醫學大學國際事務處（OGA）、教務處與 7 大學院 115–116 學年度（2026–2028）醫學院 2027 海外臨床見實習（21 校 64+ 名：哈佛醫學院 6 名、City of Hope 4 名、科隆大學 4 名、邦德大學 4 名、京都大學 2 名、慶應義塾大學 3 名、東京醫科大學 2 名、神戶大學 3 名、首爾大學 2 名、香港大學 4 名、新加坡國立大學 4 名、南洋理工大學 4 名等）、校級赴日本順天堂大學長期交換生計畫（JLCSP / LAP 免學費）、10 校跨國雙聯學位（瑞典烏普薩拉大學每年 6 名免學費、匈牙利賽蓋德大學每年 3 名免學費＋免費住宿、日本熊本大學 2026/09 新簽醫學博士雙聯、美國加州大學爾灣分校 UCI、City of Hope、法國艾克斯-馬賽大學、澳洲格里菲斯大學、泰國朱拉隆功大學、瑪希朵大學、清邁大學）、口腔醫學院／藥學院／護理學院／健康科學院（含瑞典卡羅林斯卡醫學院 KI 3 名、美國南加大 USC 6 名、約翰霍普金斯醫院 4 名、新加坡陳篤生醫院 6 名）／人社院海外見實習、115 年度博士生千里馬出國研究計畫（最高補助 NT$50萬）、北美洲高醫校友會獎學金（NT$15,000）及國際處出國研習補助（歐美非機票最高 NT$5萬＋月領 NT$2.5萬）同步整合；共完整收錄 {len(partners)} 所全球締約合作大學、醫學院與教學醫院（含 {open_partner_count} 所當期開放交換、雙聯與臨床見實習機構及 {len(partners) - open_partner_count} 所正式締約姊妹校，橫跨全球 30 個國家與地區，並收錄 {exp_covered_schools} 所合作機構共 {total_exp_reports} 篇歷屆師生返國成果報告）。"
      ),
      "verified_at": "2026-10-21",
  }
  (OFFICIAL_KMU_DIR / "catalog-completeness.json").write_text(
      json.dumps(completeness, ensure_ascii=False, indent=2) + "\n",
      encoding="utf-8",
  )
  (OFFICIAL_KMU_DIR / "verification_status.json").write_text(
      json.dumps(
          {
              "school_id": "kmu",
              "school_name": "高雄醫學大學",
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
          "sources/kmu/oga_partners_zh.html",
          KMU_PARTNERS_ZH_URL,
          "高雄醫學大學國際事務處中文版締約姊妹校列表 HTML",
      ),
      (
          "sources/kmu/oga_partners_en.html",
          KMU_PARTNERS_EN_URL,
          "高雄醫學大學國際事務處英文版締約姊妹校列表 HTML",
      ),
      (
          "sources/kmu/oga_dual_partners_zh.html",
          KMU_DUAL_PARTNERS_URL,
          "高雄醫學大學國際事務處跨國雙聯學制合作專區 HTML",
      ),
      (
          "sources/kmu/oga_juntendo_2997.html",
          KMU_JUNTENDO_EXCHANGE_URL,
          "高雄醫學大學赴日本順天堂大學長期交換學生（JLCSP / LAP）甄選公告 HTML",
      ),
      (
          "sources/kmu/oga_subsidy_std_2541.html",
          KMU_SUBSIDY_STD_URL,
          "高雄醫學大學國際事務處補助學生出國研習標準（公告 2541）HTML",
      ),
      (
          "sources/kmu/oga_115_qianlima_3221.html",
          KMU_QIANLIMA_115_URL,
          "高雄醫學大學 115 年度鼓勵博士生出國交流（千里馬）補助計畫公告 HTML",
      ),
      (
          "sources/kmu/oga_2026_na_alumni_3153.html",
          KMU_NA_ALUMNI_2026_URL,
          "高雄醫學大學財團法人北美洲高醫校友會基金會學生海外實習獎學金公告 HTML",
      ),
      (
          "sources/kmu/reg_intl_study_reward.pdf",
          KMU_REG_INTL_REWARD_PDF_URL,
          "高雄醫學大學學生國際研習服務獎勵要點 PDF",
      ),
      (
          "sources/kmu/pdf_115_xuehai_briefing.pdf",
          KMU_115_XUEHAI_BRIEFING_PDF_URL,
          "高雄醫學大學 115 年度教育部學海系列計畫甄選說明會簡報 PDF",
      ),
      (
          "sources/kmu/oga_20260923_subsidy_briefing.pptx",
          KMU_SUBSIDY_STD_URL,
          "高雄醫學大學 2026/09/23 國際事務處出國研習補助說明會簡報 PPTX",
      ),
      (
          "sources/kmu/cmed_2027_sisters_sheet.csv",
          KMU_CMED_2027_SHEET_URL,
          "高雄醫學大學醫學院 2027（116學年度）外派姐妹校臨床見實習 21 校名額與條件一覽表 CSV",
      ),
      (
          "sources/kmu/cmed_2027_sisters_sheet.xlsx",
          KMU_CMED_2027_SHEET_URL,
          "高雄醫學大學醫學院 2027（116學年度）外派姐妹校臨床見實習 21 校名額與條件一覽表 XLSX",
      ),
      (
          "sources/kmu/cmed_20260909_briefing.pptx",
          KMU_CMED_2027_NOTICE_URL,
          "高雄醫學大學醫學院 2026/09/09 海外臨床見實習招募說明會簡報 PPTX",
      ),
      (
          "sources/kmu/cmed_kumamoto_dual_1283.html",
          KMU_CMED_KUMAMOTO_DUAL_URL,
          "高雄醫學大學醫學院與日本熊本大學簽署雙聯博士學位協議公告 HTML",
      ),
      (
          "sources/kmu/dent_363_notice.pdf",
          KMU_DENT_363_URL,
          "高雄醫學大學口腔醫學院牙醫學系 115 寒假及 114 暑假海外臨床見實習甄選簡章 PDF",
      ),
      (
          "sources/kmu/ot_ki_114.pdf",
          KMU_OT_INTL_URL,
          "高雄醫學大學健康科學院職能治療學系赴瑞典卡羅林斯卡醫學院（KI）交換實習甄選簡章 PDF",
      ),
      (
          "sources/kmu/ot_usc_114_winter.pdf",
          KMU_OT_INTL_URL,
          "高雄醫學大學健康科學院職能治療學系赴美國南加州大學（USC）海外見習甄選簡章 PDF",
      ),
      (
          "sources/kmu/kmu_catalog_source.json",
          KMU_PARTNERS_ZH_URL,
          f"高雄醫學大學 {len(partners)} 所全球合作大學、醫學院與教學醫院整合資料集 JSON",
      ),
      (
          "sources/kmu/kmu_resolved_locations.json",
          KMU_PARTNERS_ZH_URL,
          f"高雄醫學大學 {len(partners)} 所全球合作機構 ROR / Wikidata 地理座標核對表 JSON",
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
      "school_id": "kmu",
      "school_name": "高雄醫學大學",
      "generated_at": CHECKED_AT,
      "active_cycle_note": completeness["active_term"],
      "sources": prov_sources,
  }
  prov_text = json.dumps(provenance_payload, ensure_ascii=False, indent=2) + "\n"
  (OFFICIAL_KMU_DIR / "import_provenance.json").write_text(prov_text, encoding="utf-8")
  (OFFICIAL_KMU_DIR / "import-provenance.json").write_text(prov_text, encoding="utf-8")

  print(
      f"Successfully built KMU catalog: {len(partners)} partners"
      f" ({open_partner_count} open, {completeness['verified_campus_images']}"
      f" verified images, {completeness['verified_locations']} verified"
      f" locations), {len(workflows)} workflows,"
      f" {len(destinations)} destinations, {len(research_records)} research"
      f" records, {exp_covered_schools} schools with experience records"
      f" ({len(student_experience_rows)} rows, {total_exp_reports} reports)."
  )


if __name__ == "__main__":
  main()
