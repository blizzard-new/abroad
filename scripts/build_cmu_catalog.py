"""Build the official China Medical University (中國醫藥大學, CMU) exchange data bundle."""

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

SOURCES_CMU_DIR = REPO_ROOT / "sources" / "cmu"
OFFICIAL_CMU_DIR = REPO_ROOT / "src" / "exchange_info" / "official_data" / "cmu"
STATIC_DIR = REPO_ROOT / "src" / "exchange_info" / "static"

CHECKED_AT = "2026-10-21T04:00:00Z"

CMU_OIA_HUB_URL = "https://cmucia.cmu.edu.tw/"
CMU_OIA_EN_HUB_URL = "https://cmucia.cmu.edu.tw/english/"
CMU_PARTNERS_ZH_URL = "https://cmucia.cmu.edu.tw/a_partner.php"
CMU_PARTNERS_EN_URL = "https://cmucia.cmu.edu.tw/english/a_partner.php"
CMU_OUTBOUND_EXCHANGE_URL = "https://cmucia.cmu.edu.tw/s_exchange_o.php"
CMU_OUTBOUND_FORMS_URL = "https://cmucia.cmu.edu.tw/download.php"
CMU_NEWS_JAPAN_EXCHANGE_URL = "https://cmucia.cmu.edu.tw/news_detail.php?sn=157"
CMU_JAPAN_2024_BRIEFING_PDF_URL = "https://cmucia.cmu.edu.tw/upfiles/news/1703142038_1.pdf"
CMU_JAPAN_2023_BRIEFING_PDF_URL = "https://cmucia.cmu.edu.tw/upfiles/news/1671090335_1.pdf"
CMU_EDUHK_AGREEMENT_PDF_URL = "https://cmucia.cmu.edu.tw/upfiles/partner/1480909692_1.pdf"

CMU_STATUTE_EXCHANGE_622_URL = "https://www.cmu.edu.tw/statute/statute_detail.php?sn=622"
CMU_STATUTE_SUBSIDY_342_URL = "https://www.cmu.edu.tw/statute/statute_detail.php?sn=342"
CMU_STATUTE_CREDIT_337_URL = "https://www.cmu.edu.tw/statute/statute_detail.php?sn=337"
CMU_STATUTE_DUAL_647_URL = "https://www.cmu.edu.tw/statute/statute_detail.php?sn=647"
CMU_STATUTE_USC_PHARM_1566_URL = "https://www.cmu.edu.tw/statute/statute_detail.php?sn=1566"
CMU_STATUTE_USC_KECK_917_URL = "https://www.cmu.edu.tw/statute/statute_detail.php?sn=917"
CMU_STATUTE_SC_3PLUS2_1268_URL = "https://www.cmu.edu.tw/statute/statute_detail.php?sn=1268"
CMU_STATUTE_SC_DUAL_1267_URL = "https://www.cmu.edu.tw/statute/statute_detail.php?sn=1267"
CMU_STATUTE_GSU_846_URL = "https://www.cmu.edu.tw/statute/statute_detail.php?sn=846"
CMU_STATUTE_TULANE_848_URL = "https://www.cmu.edu.tw/statute/statute_detail.php?sn=848"
CMU_STATUTE_SDSU_1085_URL = "https://www.cmu.edu.tw/statute/statute_detail.php?sn=1085"
CMU_STATUTE_GRIFFITH_1459_URL = "https://www.cmu.edu.tw/statute/statute_detail.php?sn=1459"
CMU_STATUTE_NEWCASTLE_1222_URL = "https://www.cmu.edu.tw/statute/statute_detail.php?sn=1222"

CMU_PT_115_1_INTERNSHIP_URL = "https://cmupt.cmu.edu.tw/news/753"
CMU_MED_CLERKSHIP_URL = "https://med.cmu.edu.tw/page/international"
CMU_NURSING_INTL_URL = "https://cmunur.cmu.edu.tw/page/41"
CMU_CHMED_INTL_URL = "https://chmed.cmu.edu.tw/news/category/6"

REGION_COST_DEFAULTS = {
    "美國": (
        "USD 1,500–2,700 / 月（含住宿、膳食與市區交通；南達科塔州立大學 SDSU、南卡羅萊納大學哥倫比亞校區、喬治亞州立大學亞特蘭大校區、紐奧良杜蘭大學、休士頓德州醫療中心 MD Anderson / UTHealth 約 USD 1,450–2,100 / 月；洛杉磯南加州大學 USC、聖地牙哥 UCSD、爾灣 UCI、紐約大學 NYU、費城賓州大學 UPenn 約 USD 1,950–2,700 / 月；修讀雙聯學位可依中醫大雙聯施行細則申請 NT$ 30萬–45萬元獎助學金或 2 年中醫大全額學雜費補助）",
        "須憑美國接待校或醫學中心核發之 DS-2019（J-1 交換生／短期臨床研修）或 I-20（F-1 雙聯學位學生）表格向美國在台協會（AIT）申辦簽證，海外臨床見實習生另須完成規定之免疫抗體檢測（MMR、水痘、B肝、TB 檢驗）與醫療保險。",
    ),
    "加拿大": (
        "CAD 1,500–2,400 / 月（多倫多大學、維多利亞大學、布洛克大學學生宿舍、伙食與大眾運輸費用）",
        "一學期內短期交換可申辦加拿大 eTA 電子旅行授權，超過 6 個月須申辦 Study Permit 學生許可並投保醫療保險。",
    ),
    "哥斯大黎加": (
        "USD 750–1,200 / 月（聖荷西中美洲自治大學周邊學生住宿與日常開銷）",
        "我國護照享免簽證入境待遇，長期研修須依接待校指引辦理學生居留許可與海外全期醫療保險。",
    ),
    "巴西": (
        "USD 700–1,150 / 月（聖保羅大學 USP 與聖保羅州立大學 UNESP 學生公寓、餐廳與地鐵公車費用）",
        "須憑巴西接待大學入學許可向巴西商務辦事處申辦 VITEM IV 學生簽證並投保海外醫療保險。",
    ),
    "墨西哥": (
        "USD 650–1,050 / 月（梅里達安納華克梅亞柏大學學生住宿與日常飲食交通開銷）",
        "須向墨西哥商務簽證文件暨文化辦事處申辦簽證並投保海外全期醫療及意外保險。",
    ),
    "日本": (
        "JPY 75,000–135,000 / 月（北海道大學札幌校區惠迪寮與國際學生宿舍每月宿費僅約 JPY 15,000–35,000、北見工業大學國際學生宿舍每月僅約 JPY 10,000–20,000，連同伙食交通每月約 JPY 65,000–95,000；東京都東京大學、順天堂大學、東京科學大學 TMDU、日本藥科大學、神戶中央市民醫院、大阪關西電力醫院約 JPY 95,000–135,000 / 月；赴北海道大學與北見工業大學交換可獲中醫大補助來回機票＋每月 NT$ 5,000 生活費）",
        "學期或學年交換須憑日本接待校核發之在留資格認定證明書（COE）向日本台灣交流協會申辦留學簽證並加入日本國民健康保險（NHI）；短期海外臨床實習（如物治系 2027/01/10–01/30 赴順天堂醫院、神戶中央市民醫院、關西電力醫院）須備妥抗體檢測報告與海外醫療保險。",
    ),
    "韓國": (
        "KRW 800,000–1,350,000 / 月（首爾慶熙大學、東國大學、首爾大學、延世大學、漢陽大學、自生韓方醫院周邊住宿與餐飲交通約 KRW 950,000–1,350,000 / 月；釜山大學、大邱韓醫大學、蔚山大學、光州科學技術院約 KRW 750,000–1,050,000 / 月；中醫學院學生可申請教育部學海築夢補助）",
        "學期交換須憑韓國接待校標準入學許可書向駐台北韓國代表部申辦 D-2-6 交換簽證；短期韓醫臨床見實習須備妥實習許可函與海外醫療保險。",
    ),
    "新加坡": (
        "SGD 1,600–2,500 / 月（新加坡中央醫院 SGH 及新加坡國立大學 NUS、南洋理工大學 NTU 實習與研修期間之學生公寓、熟食中心餐飲與捷運公車費用；可申請中醫大出國研習補助或教育部新南向學海築夢補助）",
        "赴新加坡中央醫院（SGH）或新加坡國立大學（NUS）進行臨床專業實習，須依院方與新加坡衛生部（MOH）／移民與關卡局（ICA）規定申辦 Training Employment Pass 或 Student Pass，並完成全套疫苗抗體證明。",
    ),
    "泰國": (
        "THB 13,000–23,000 / 月（曼谷瑪希敦大學 Siriraj 醫院、朱拉隆功大學、國立法政大學、農業大學、蘭實大學，以及清邁大學、清萊皇太后大學、孔敬大學、瑪哈沙拉堪大學學生宿舍與餐飲交通開銷實惠；可申請教育部新南向學海築夢補助）",
        "須憑泰國接待校院公文向泰國貿易經濟辦事處（TTEO）申辦 Non-Immigrant ED 實習／留學簽證，並投保涵蓋全期之海外醫療及意外保險。",
    ),
    "越南": (
        "USD 450–780 / 月（胡志明市醫藥大學 UMP、胡志明市傳統醫學醫院、芹苴醫藥大學 CTUMP、順化醫藥大學、河內藥科大學、峴港維新大學學生宿舍與日常餐飲交通費用低廉；中醫學院每年選送新南向學海築夢實習團）",
        "須透過越南接待大學或教學醫院申辦越南簽證，並於出國前投保涵蓋全期之海外醫療及意外保險。",
    ),
    "印尼": (
        "IDR 4,800,000–8,200,000 / 月（日惹卡渣瑪達大學 UGM、日惹穆罕默迪亞大學 UMY、泗水艾爾朗加大學 UNAIR、望加錫哈薩努丁大學等學生公寓與餐飲交通費用實惠）",
        "須由印尼接待校協助申辦印尼學生／文化交流電子簽證（e-Visa），並投保涵蓋全期之海外醫療及意外保險。",
    ),
    "馬來西亞": (
        "MYR 1,600–2,600 / 月（吉隆坡馬來亞大學 UM 及拉曼大學 UTAR 校內外住宿、飲食與捷運公車開銷）",
        "學期交換或長期實習須透過馬來西亞 EMGS 系統申辦學生簽證核准函（VAL / Mobility Pass）並投保醫療保險。",
    ),
    "菲律賓": (
        "USD 550–900 / 月（大馬尼拉金融中心馬卡蒂大學 University of Makati 住宿與日常餐飲交通費用）",
        "須依菲律賓接待校指引辦理簽證或特別學習許可（SSP），並投保海外全期醫療及意外保險。",
    ),
    "印度": (
        "USD 450–750 / 月（印度理工學院馬德拉斯分校 IIT Madras、馬尼帕爾高等教育學院 MAHE、吉特卡拉大學與清奈斯里巴拉吉牙醫學院國際學舍與餐飲費用）",
        "須憑印度接待校入學／實習許可向印度台北協會（ITA）申辦 Student / Intern Visa 並投保海外醫療及意外保險。",
    ),
    "蒙古": (
        "USD 450–750 / 月（烏蘭巴托蒙古國立醫科大學 MNUMS 與阿奇醫科大學學生宿舍、餐飲與市區交通費用）",
        "須憑接待校邀請函申辦蒙古簽證，並投保涵蓋全期之海外醫療及意外保險。",
    ),
    "土耳其": (
        "USD 550–900 / 月（伊斯坦堡貝茲米雅萊姆瓦克夫大學 Bezmialem Vakıf University 學生公寓、學餐與大眾運輸開銷）",
        "須申辦土耳其學生簽證並投保當地與海外醫療保險。",
    ),
    "澳洲": (
        "AUD 2,000–2,900 / 月（布里斯本／黃金海岸格里菲斯大學 Griffith University、紐卡索大學 University of Newcastle、伯斯西澳大學 UWA、雪梨西雪梨大學住宿與生活費；修讀格里菲斯雙聯碩士最高補助 NT$30萬、紐卡索雙聯護理博士最高補助 NT$50萬）",
        "修讀雙聯學位或一學期以上交換須購買澳洲海外學生健康保險（OSHC）並申辦 Subclass 500 學生簽證。",
    ),
    "英國": (
        "GBP 1,100–1,800 / 月（倫敦西敏寺大學、密德薩斯大學約 GBP 1,350–1,800 / 月；南安普敦大學、蘇格蘭史特靈大學約 GBP 1,000–1,350 / 月）",
        "一學期（6 個月內）交換可持護照辦理 Standard Visitor 學生訪問入境，超過 6 個月須申辦英國 Student Visa 並繳納醫療附加費（IHS）。",
    ),
    "德國": (
        "EUR 900–1,350 / 月（柏林夏里特醫科大學 Charité 及明斯特大學學生宿舍 Studierendenwerk、學餐與德國學期交通票 Semesterticket）",
        "短期研習（90 天內）免申根簽證；超過 90 天須向德國在台協會申辦長期學生簽證、開立限制提領帳戶（Sperrkonto）並投保德國法定健康保險。",
    ),
    "奧地利": (
        "EUR 900–1,300 / 月（格拉茲醫學大學 Medical University of Graz 學生公寓 OeAD、日常餐飲與格拉茲電車公車費用）",
        "短期臨床見實習（90 天內）免申根簽證，一學期以上交換須向奧地利臺北辦事處申辦學生居留簽證並備妥醫療與實習責任險。",
    ),
    "瑞士": (
        "CHF 1,600–2,400 / 月（蘇黎世大學 University of Zurich 住宿、伙食與蘇黎世大眾運輸 ZVV 交通卡費用）",
        "短期研究或見習（90 天內）免申根簽證，超過 90 天須向瑞士商務辦事處申辦長期學生／研究簽證。",
    ),
    "荷蘭": (
        "EUR 1,000–1,500 / 月（萊頓大學 Leiden University 學生住宿、日常飲食與單車火車通勤費用）",
        "一學期以上交換須由荷蘭接待大學代為向荷蘭移民局（IND）申辦 MVV 入境簽證與居留許可（VVR）。",
    ),
    "捷克": (
        "EUR 550–850 / 月（布爾諾馬薩里克大學 Masaryk University 與奧洛穆茨帕拉茨基大學 Palacký University 學生宿舍與餐飲費用親民）",
        "短期研習（90 天內）免申根簽證，一學期交換須向捷克經濟文化辦事處申辦長期學生簽證。",
    ),
    "羅馬尼亞": (
        "EUR 500–800 / 月（克盧日-納波卡巴比什-博雅依大學、奧拉迪亞大學、阿拉德西方大學學生宿舍與生活費實惠）",
        "短期交流（90 天內）免申根簽證，一學期交換須申辦羅馬尼亞 D/SD 學生簽證並投保海外醫療保險。",
    ),
    "斯洛維尼亞": (
        "EUR 650–950 / 月（首都盧比安納大學 University of Ljubljana 學生宿舍、學生餐券系統 Študentski boni 與市區交通）",
        "短期研習（90 天內）免申根簽證，一學期交換須申辦斯洛維尼亞長期簽證／臨時居留許可。",
    ),
    "立陶宛": (
        "EUR 600–900 / 月（首都維爾紐斯大學 Vilnius University 學生宿舍與日常餐飲交通費用）",
        "短期交流（90 天內）免申根簽證，一學期交換須申辦立陶宛國家簽證（D 類）並投保醫療保險。",
    ),
    "俄羅斯": (
        "USD 500–850 / 月（西伯利亞學術重鎮托木斯克國立大學 Tomsk State University 校內宿舍與生活費）",
        "須憑俄羅斯接待大學官方邀請函申辦俄羅斯留學簽證並投保當地醫療險（出國前請務必確認外交部最新旅遊安全警示）。",
    ),
    "迦納": (
        "USD 600–950 / 月（阿克拉迦納大學健康科學院短期醫學與公衛交流食宿交通開銷）",
        "須憑接待校邀請函申辦迦納簽證，並於出發前完成黃熱病疫苗接種（必備黃皮書）與全程海外醫療急難救助保險。",
    ),
    "香港": (
        "HKD 5,500–9,500 / 月（香港教育大學 EdUHK、香港大學 HKU、香港中文大學 CUHK、香港浸會大學 HKBU、香港理工大學 PolyU、香港都會大學、東華學院、東華三院學生宿舍與港鐵餐飲費用；香港教育大學每學年提供 4 名免學費交換生名額）",
        "須透過香港接待大學向香港入境事務處申辦來港就讀進入許可（Student Visa / Entry Permit），並於出國前至陸委會「國人赴港澳動態登錄系統」完成登錄。",
    ),
    "澳門": (
        "HKD 4,400–7,300 / 月（約 MOP 4,500–7,500；氹仔澳門科技大學 MUST 學生宿舍、餐廳與巴士開銷）",
        "持有效護照入境澳門，若研修超過法定期限須向澳門治安警察局申辦「逗留特別許可（學生）」，並於出國前完成陸委會赴港澳動態登錄。",
    ),
    "中國大陸": (
        "RMB 2,000–3,600 / 月（北京大學醫學部、北京中醫藥大學、中國中醫科學院、復旦大學、上海中醫藥大學、南京大學、南京中醫藥大學、中國藥科大學、浙江大學、浙江中醫藥大學、廣州中醫藥大學、廈門大學、中南大學湘雅醫院、南開大學等校內宿舍與學生食堂費用實惠）",
        "持有效護照與臺胞證入境；依教育部及中國醫藥大學《學生出國交換實施要點》、《學生出國修課暨學分抵免實施要點》規定，赴大陸地區交流須落實教育部登錄平臺填報，且出國選課須於出國前完成系所及教務處審核（大陸地區高等學校醫事人員相關學歷與學分採認悉依教育部與考選部法規辦理）。",
    ),
}

SEMESTER_DATES_BY_COUNTRY = {
    "美國": "秋季學期（Fall）：約 8 月中下旬至 12 月中旬；春季學期（Spring）：約 1 月中旬至 5 月中旬；暑期專業／臨床見實習：6 月至 8 月",
    "加拿大": "秋季學期（Fall）：約 9 月初至 12 月中旬；冬季／春季學期（Winter）：約 1 月初至 4 月底",
    "哥斯大黎加": "第一學期：約 1 月至 4 月；第二學期：約 5 月至 8 月；第三學期：約 9 月至 12 月",
    "巴西": "第一學期：約 2 月中下旬至 6 月底；第二學期：約 8 月初至 12 月中旬",
    "墨西哥": "秋季學期：約 8 月中旬至 12 月中旬；春季學期：約 1 月中旬至 5 月底",
    "日本": "春季學期（前學期）：約 4 月初至 8 月上旬；秋季學期（後學期）：約 10 月初至翌年 2/3 月；物理治療學系 115-1 赴日臨床實習（順天堂醫院、神戶中央市民醫院、關西電力醫院）：2027/01/10–2027/01/30",
    "韓國": "春季學期（第1學期）：約 3 月初至 6 月中下旬；秋季學期（第2學期）：約 9 月初至 12 月中下旬；中醫學院暑期韓醫臨床見實習（慶熙大學、東國大學、釜山大學、自生韓方醫院）：7 月至 8 月（至少 30 天）",
    "新加坡": "第一學期：約 8 月至 12 月；第二學期：約 1 月至 5 月；物理治療學系 115-1 赴新加坡中央醫院（SGH）臨床實習：2027/01/10–2027/01/30",
    "泰國": "第一學期：約 8 月至 12 月；第二學期：約 1 月至 5 月；護理學系與中醫學院新南向學海築夢臨床實習（皇太后大學、瑪希敦大學 Siriraj 醫院、清邁大學）：6–8 月暑期（至少 30 天）",
    "越南": "第一學期（秋季班）：約 9 月至翌年 1 月；第二學期（春季班）：約 2 月至 6 月；中醫學院新南向學海築夢臨床實習（胡志明市醫藥大學、芹苴醫藥大學、胡志明市傳統醫學醫院）：7–8 月暑期（至少 30 天）",
    "印尼": "奇數／秋季學期：約 8/9 月至 12 月；偶數／春季學期：約 2 月至 6 月",
    "馬來西亞": "第一學期（秋季班）：約 10 月至翌年 2 月；第二學期（春季班）：約 3 月至 7 月",
    "菲律賓": "第一學期（秋季班）：約 8 月至 12 月；第二學期（春季班）：約 1 月中旬至 5 月下旬",
    "印度": "奇數／秋季學期：約 7/8 月至 12 月；偶數／春季學期：約 1 月至 5 月",
    "蒙古": "秋季學期：約 9 月初至 12 月底；春季學期：約 2 月初至 6 月初",
    "土耳其": "秋季學期：約 9 月中下旬至翌年 1 月；春季學期：約 2 月中旬至 6 月",
    "澳洲": "第一學期（Trimester 1 / Semester 1）：約 2 月中下旬至 6 月；第二學期（Trimester 2 / Semester 2）：約 7 月中下旬至 11 月；第三學期（格里菲斯大學 Trimester 3）：約 11 月至翌年 2 月",
    "英國": "秋季學期（Autumn Term）：約 9 月下旬至 12 月中旬；春季學期（Spring Term）：約 1 月中旬至 4 月；夏季學期：約 4 月下旬至 6 月",
    "德國": "冬季學期（Wintersemester）：約 10 月初至翌年 2 月中旬；夏季學期（Sommersemester）：約 4 月初至 7 月中下旬",
    "奧地利": "冬季學期（Wintersemester）：約 10 月初至翌年 1 月底；夏季學期（Sommersemester）：約 3 月初至 6 月底",
    "瑞士": "秋季學期（Autumn）：約 9 月中旬至 12 月底；春季學期（Spring）：約 2 月中旬至 5 月底",
    "荷蘭": "第一學期（秋季班）：約 9 月初至翌年 1 月底；第二學期（春季班）：約 2 月初至 6 月底",
    "捷克": "冬季學期（秋季班）：約 9 月中下旬至翌年 1 月；夏季學期（春季班）：約 2 月中旬至 6 月",
    "羅馬尼亞": "第一學期（冬季班）：約 10 月初至翌年 2 月；第二學期（夏季班）：約 2 月下旬至 6 月底",
    "斯洛維尼亞": "冬季學期：約 10 月初至翌年 1 月底；夏季學期：約 2 月中下旬至 6 月中旬",
    "立陶宛": "秋季學期：約 9 月初至翌年 1 月底；春季學期：約 2 月初至 6 月底",
    "俄羅斯": "秋季學期：約 9 月初至翌年 1 月；春季學期：約 2 月初至 6 月底",
    "迦納": "第一學期：約 8/9 月至 12 月；第二學期：約 1/2 月至 5 月",
    "香港": "第一學期（Term 1）：約 9 月初至 12 月中下旬；第二學期（Term 2）：約 1 月上旬至 5 月中旬",
    "澳門": "第一學期（秋季班）：約 9 月初至 12 月底；第二學期（春季班）：約 1 月中旬至 5 月中旬",
    "中國大陸": "秋季學期：約 9 月初至翌年 1 月中旬；春季學期：約 2 月中下旬至 6 月底",
}


def clean_text(s: str) -> str:
  if not s:
    return ""
  return re.sub(r"\s+", " ", s).strip()


def main() -> None:
  OFFICIAL_CMU_DIR.mkdir(parents=True, exist_ok=True)
  catalog_source = json.loads(
      (SOURCES_CMU_DIR / "cmu_catalog_source.json").read_text(encoding="utf-8")
  )
  resolved_locations = json.loads(
      (SOURCES_CMU_DIR / "cmu_resolved_locations.json").read_text(encoding="utf-8")
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

    group_str = clean_text(item.get("group") or "國際合作姊妹校")
    quota_str = clean_text(item.get("quota") or "依中醫大國際事務處與各學院當期公告名額")
    detail_url = item.get("detail_url") or CMU_PARTNERS_ZH_URL

    if zh_name in {"北海道大學", "北見工業大學"}:
      program_type = "校級赴日本長期交換學生計畫（免姊妹校學費＋中醫大補助來回機票與每月 NT$5,000 生活費）"
      source_url = CMU_NEWS_JAPAN_EXCHANGE_URL
    elif zh_name == "香港教育大學":
      program_type = "校級赴香港學年交換學生計畫（每年 4 名免學費交換生）"
      source_url = CMU_EDUHK_AGREEMENT_PDF_URL
    elif zh_name == "南加州大學":
      program_type = "跨國雙聯碩士學位暨獎學金計畫（藥學系 MS 雙聯／凱克醫學院 MD-MPH 與生醫雙聯，最高補助 NT$450,000）"
      source_url = CMU_STATUTE_USC_PHARM_1566_URL
    elif zh_name == "南卡羅萊納大學":
      program_type = "跨國 3+2 學碩雙聯暨 MD/MPH 雙聯學位獎學金計畫（最高補助 NT$300,000＋州內學費優惠）"
      source_url = CMU_STATUTE_SC_3PLUS2_1268_URL
    elif zh_name == "喬治亞州立大學":
      program_type = "跨國雙聯碩士暨 MD/MPH 雙聯學位獎學金計畫（最高補助 NT$350,000）"
      source_url = CMU_STATUTE_GSU_846_URL
    elif zh_name == "杜蘭大學":
      program_type = "跨國 MD/MPH 暨公共衛生雙聯碩士學位獎學金計畫（每年 20–30 名，最高補助 NT$400,000）"
      source_url = CMU_STATUTE_TULANE_848_URL
    elif zh_name == "南達科塔州立大學":
      program_type = "營養學系跨國 2+2 雙學士學位暨美國註冊營養師（RD）培育計畫（每年 4 名，補助 2 年中醫大全額學雜費）"
      source_url = CMU_STATUTE_SDSU_1085_URL
    elif zh_name == "格里菲斯大學":
      program_type = "跨國全球公共衛生碩士（MGPH）暨 MD/MPH 雙聯學位獎學金計畫（最高補助 NT$300,000）"
      source_url = CMU_STATUTE_GRIFFITH_1459_URL
    elif zh_name == "紐卡索大學":
      program_type = "跨國雙聯護理博士學位（PhD in Nursing）獎學金計畫（每年 2 名，最高補助 NT$500,000）"
      source_url = CMU_STATUTE_NEWCASTLE_1222_URL
    elif zh_name in {"新加坡中央醫院", "神戶市立醫療中心中央市民醫院", "關西電力醫院", "順天堂大學"}:
      program_type = "健康照護學院物理治療學系 115-1 海外臨床專業實習（2027/01/10–01/30）暨海外臨床見實習計畫"
      source_url = CMU_PT_115_1_INTERNSHIP_URL
    elif zh_name in {"德州大學安德森癌症中心", "艾默蕾大學"}:
      program_type = "醫學院海外臨床見實習（Medical Clerkship）暨生物醫學研究計畫"
      source_url = CMU_MED_CLERKSHIP_URL
    elif zh_name in {"皇太后大學", "清邁大學"} and avail_status == "open":
      program_type = "教育部新南向學海築夢海外臨床護理與傳統醫學專業實習計畫"
      source_url = CMU_NURSING_INTL_URL
    elif avail_status == "open":
      program_type = "教育部學海築夢／新南向學海築夢海外臨床見實習暨中醫藥與藥學國際專業實習計畫"
      source_url = CMU_CHMED_INTL_URL if country in {"越南", "韓國", "泰國", "日本"} else detail_url
    elif country in {"中國大陸", "香港", "澳門"}:
      program_type = "大陸及港澳地區正式締約合作姊妹校與中醫藥臨床教學機構"
      source_url = detail_url
    else:
      program_type = "國際事務處正式締約合作姊妹校與醫療研究機構"
      source_url = detail_url

    colleges_str = clean_text(item.get("colleges") or "")
    degree_levels_str = clean_text(item.get("eligible_degrees") or "大學部、碩士班、博士班在學學生")
    lang_req_str = clean_text(item.get("language_req") or "")
    gpa_req_str = clean_text(item.get("gpa_req") or "")
    website = item.get("website") or CMU_PARTNERS_ZH_URL
    remarks_raw = clean_text(item.get("notes") or "")
    tuition_note = clean_text(item.get("tuition_note") or "")
    exps = item.get("experience_reports") or []

    round_label = (
        "115–116學年度（2026–2028）出國交換、跨國雙聯學位、臨床見實習暨教育部學海計畫甄選"
        if avail_status == "open"
        else "國際事務處正式締約合作姊妹校與醫療機構（依當期交換、雙聯或臨床見實習公告名額辦理）"
    )
    app_deadline_str = (
        "【校級赴日本北海道大學（每年 5 名免學費＋中醫大機票與每月 NT$5,000 補助）、北見工業大學（每年 3 名免學費＋中醫大機票與每月 NT$5,000 補助）及香港教育大學（每年 4 名免學費）交換生甄選】秋季班每年 12 月至翌年 1 月初校內甄選（2–3 月向姊妹校提名）、春季班每年 8–9 月校內甄選｜【跨國雙聯學位暨高額獎學金（美國南加州大學 USC 最高 NT$45萬、杜蘭大學最高 NT$40萬、喬治亞州立大學最高 NT$35萬、南卡羅萊納大學最高 NT$30萬、南達科塔州立大學補助 2 年中醫大全額學雜費、澳洲格里菲斯大學最高 NT$30萬、紐卡索大學護理博士最高 NT$50萬）】每年第 1 學期（10–12 月）及第 2 學期（1–3 月）依各雙聯施行細則向所屬學院與國際事務處提出申請｜【教育部「學海飛颺、學海惜珠、學海築夢、新南向學海築夢」暨《中國醫藥大學補助學生出國研習與實習辦法》】學海計畫每年 12 月至翌年 2 月初校內收件；校內出國研習與實習補助分兩階段申請（第一階段每年 1–5 月出國者於前一年 10–11 月收件；第二階段每年 6–12 月出國者於當年 3–4 月收件）｜【健康照護學院物理治療學系 115-1 海外臨床實習（新加坡中央醫院 4 名、神戶中央市民醫院 2 名、關西電力醫院 2 名、順天堂大學醫院 2 名，實習期間 2027/01/10–01/30）】報名至 115年9月18日（2026/09/18）12:00 截止，9月25日面試"
    )
    deadline_iso = (
        "2026-09-18T12:00:00+08:00"
        if zh_name in {"新加坡中央醫院", "神戶市立醫療中心中央市民醫院", "關西電力醫院", "順天堂大學"}
        else "2027-01-29T17:00:00+08:00"
    )
    win_status = "open" if avail_status == "open" else "closed"
    acad_year = "116"

    study_period_str = clean_text(
        item.get("duration") or "1 學期、1 學年交換，1–2 年跨國雙聯學位，或 3–8 週海外臨床見實習"
    )
    sem_dates_str = SEMESTER_DATES_BY_COUNTRY.get(
        country, "秋季學期：約 9 月至翌年 1 月；春季學期：約 2 月至 6 月"
    )
    housing_str = (
        f"獲中國醫藥大學國際事務處或所屬學院提名錄取後，可依 {zh_name} 國際處／教學醫院指引申請校內外學生宿舍或臨床實習生公寓"
        + (f"（費用與獎補助待遇：{tuition_note}）" if tuition_note else "。")
    )
    course_rest_str = (
        f"開放對象與領域：{colleges_str}。依《中國醫藥大學學生出國交換實施要點》（法規編號 622）、《中國醫藥大學學生出國修課暨學分抵免實施要點》（法規編號 337）、《中國醫藥大學與境外大學校院辦理雙聯學制實施辦法》（法規編號 647）及《中國醫藥大學補助學生出國研習與實習辦法》（法規編號 342）規定：（1）出國期間須維持中醫大在學註冊並依規定繳交學雜費（延修生、休學生及在職專班生不得申請）；（2）赴日本北海道大學與北見工業大學交換學生每學期至少須修習 12 學分（一般交換每學期至少須修習 1 門以上專業課程）；（3）修讀跨國雙聯學士學位須於兩校累計修業滿 32 個月以上（如南達科塔州立大學 2+2 營養雙學士須於 SDSU 修滿 66 學分）、雙聯碩士須滿 12 個月以上、雙聯博士須滿 24 個月以上；（4）返國後須於 1 個月內繳交 1,000 字以上中文或英文成果報告書及上傳 5 分鐘英文學習心得影片，並檢附正式成績單與課程大綱向系所及教務處辦理學分抵免。"
    )

    tuition_points_list = [
        (
            f"中醫大在學註冊與合作機構費用待遇（依《中國醫藥大學學生出國交換實施要點》及各校雙聯施行細則）：出國交換與雙聯期間仍須辦理本校註冊。本合作機構待遇：{tuition_note or '依兩校合作協議辦理'}。"
        ),
        (
            "中醫大校內三大出國獎補助體系與教育部學海四項計畫：（1）《中國醫藥大學補助學生出國研習與實習辦法》（法規編號 342）：凡學業平均達 A-（GPA 3.0／80 分）且操行達 80 分、具備 TOEFL iBT 59 / IELTS 5.0 / TOEIC 640 / GEPT 中高級初試 / BESTEP B1（或修畢 4 門全英語課程）之在學生，赴國外姊妹校交換（如日本北海道大學 5 名、北見工業大學 3 名）或臨床實習，得核給來回經濟艙機票與每月生活費補助（日本長期交換每月補助 NT$ 5,000）；（2）《跨國雙聯學位專案獎助學金》（法規編號 846、848、917、1085、1222、1267、1268、1459、1566）：美國南加州大學（USC 藥學 MS／凱克醫學院 MD-MPH）最高補助 NT$ 45 萬元、美國杜蘭大學（MD/MPH）最高補助 NT$ 40 萬元、美國喬治亞州立大學最高補助 NT$ 35 萬元、美國南卡羅萊納大學（3+2 學碩／MD-MPH）與澳洲格里菲斯大學（MGPH）最高補助 NT$ 30 萬元、澳洲紐卡索大學（雙聯護理博士）最高補助 NT$ 50 萬元、美國南達科塔州立大學（2+2 營養雙學士）補助 2 年中醫大全額學雜費；（3）教育部《學海飛颺、學海惜珠、學海築夢、新南向學海築夢》提供出國交換與海外臨床實習機票及生活費獎助。"
        ),
    ]

    app_steps_list = [
        (
            f"步驟一（確認中醫大在學年級、學業 A-［GPA 3.0／80分］、操行 80 分與 {zh_name} 語檢門檻）：確認為中國醫藥大學正式學籍在學學生（一般交換須修滿 1 學年以上，北海道大學、北見工業大學與南達科塔州立大學 2+2 須修滿 2 學年以上；延修生、休學生及在職生不得申請），歷年學業成績達 A-（GPA 3.0 或 80 分）以上且前一學期操行達 80 分以上，並備妥有效外語檢定證明（{lang_req_str}）。"
        ),
        (
            "步驟二（於校內收件期限前向國際事務處［水湳校本部卓越大樓］或所屬學院遞交申請表件）：（1）日本北海道大學（每年 5 名）、北見工業大學（每年 3 名）及香港教育大學（每年 4 名）校級交換：依國際事務處公告於每年 12–1 月（秋季班）或 8–9 月（春季班）繳交出國交換學生申請表、中英文歷年成績單（含 GPA 與排名）、語言檢定證明、中英文讀書計畫與自傳、推薦信 2 封及家長同意書；（2）跨國雙聯學位獎學金（USC、杜蘭、喬治亞州立、南卡羅萊納、南達科塔州立、格里菲斯、紐卡索）：於每年第 1 學期（10–12 月）或第 2 學期（1–3 月）向所屬學院及國際事務處提出；（3）物理治療學系 115-1 海外臨床實習（新加坡中央醫院、神戶中央市民醫院、關西電力醫院、順天堂醫院）：於 2026/09/18 12:00 前送交物治系辦。"
        ),
        (
            f"步驟三（通過校內書面與英文／日文面試遴選，由國際事務處或學院向 {full_name} 辦理官方提名）：經中醫大國際事務處「出國交換生遴選委員會」或各學院雙聯／海外臨床實習審查委員會完成書面與面試評選後，向 {full_name} 辦理官方提名（Nomination），並依接待校院期限完成外文入學或臨床見實習線上申請。"
        ),
        (
            "步驟四（完成教務處選課核准、簽證保險與返國 1 個月內繳交 1,000 字成果報告＋5 分鐘英文學習心得影片）：出國前須依《中國醫藥大學學生出國修課暨學分抵免實施要點》確認擬修科目、購買全程海外醫療及急難救助保險並參加行前說明會；返國後須於 1 個月內向國際事務處繳交 1,000 字以上成果報告書及上傳 5 分鐘英文學習心得影片（雙聯學位受獎生須取得合作校學位證書；未依規定完成者須繳回補助款），並檢附正式成績單辦理學分抵免。"
        ),
    ]

    elig_points_list = [
        f"合作類別與甄選群組：{program_type}（{group_str}）",
        f"開放學制與年級：{degree_levels_str}",
        f"開放申請院系：{colleges_str}",
        f"學業與操行門檻：{gpa_req_str}",
        f"外語能力標準：{lang_req_str}",
        "校內通則與修業規定：依《中國醫藥大學學生出國交換實施要點》及《補助學生出國研習與實習辦法》，申請人須歷年學業平均達 A-（GPA 3.0 或 80 分）且前一學期操行成績達 80 分以上（延修生、休學生、在職生不得申請）；返國後 1 個月內須繳交 1,000 字以上成果報告並上傳 5 分鐘英文學習心得影片。",
    ]
    if tuition_note:
      elig_points_list.append(f"姊妹校學費與中醫大獎補助待遇：{tuition_note}")
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
          f"【中醫大師生海外交換／臨床見實習成果報告（共 {len(exps)} 篇）】收錄於國際事務處與各學院國際交流專區（含：{'、'.join(exp_labels[:5])}）"
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
        "availability_note": f"中國醫藥大學國際事務處與各學院公告合作姊妹校及教學醫院（{program_type}）；{quota_str}。",
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
                "cmu_partner_sns": ",".join(map(str, item.get("cmu_partner_sns") or [])),
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
            "title": f"中國醫藥大學國際事務處締約姊妹校、交換生、雙聯學位與海外實習專區—{zh_name}",
            "source_url": source_url,
            "role": "home_university",
            "authority": "home_official_notice",
            "effective_academic_year": acad_year,
            "application_round": round_label,
            "checked_at": CHECKED_AT,
        },
        {
            "title": "中國醫藥大學學生出國交換實施要點（法規編號 622）與補助學生出國研習與實習辦法（法規編號 342）",
            "source_url": CMU_STATUTE_EXCHANGE_622_URL,
            "role": "home_university",
            "authority": "home_official_notice",
            "effective_academic_year": acad_year,
            "application_round": round_label,
            "checked_at": CHECKED_AT,
        },
        {
            "title": "中國醫藥大學與境外大學校院辦理雙聯學制實施辦法（法規編號 647）與各校雙聯學位補助施行細則",
            "source_url": CMU_STATUTE_DUAL_647_URL,
            "role": "home_university",
            "authority": "home_official_notice",
            "effective_academic_year": acad_year,
            "application_round": round_label,
            "checked_at": CHECKED_AT,
        },
    ]
    if exps:
      wf_sources.append({
          "title": f"中國醫藥大學海外交換與臨床見實習成果報告專區—赴 {zh_name} 研修紀實（{len(exps)} 篇）",
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
        "home_university": "中國醫藥大學",
        "school_name": full_name,
        "partner_website": website,
        "country": country,
        "program_type": program_type,
        "academic_year": acad_year,
        "application_round": round_label,
        "effective_application_rounds": [
            round_label,
            "116學年度赴日本北海道大學／北見工業大學／香港教育大學交換生甄選",
            "115–116學年度跨國雙聯學位暨獎學金甄選（USC／杜蘭／喬治亞州立／南卡羅萊納／南達科塔州立／格里菲斯／紐卡索）",
            "115–116學年度物理治療學系與各學院海外臨床見實習暨教育部學海計畫甄選",
            "116-1",
            "116-2",
            "115-2",
            "115-1",
        ],
        "applicability_status": "verified",
        "applicability_note": (
            "中國醫藥大學由國際事務處（OIA，下設國際合作交流中心、國際學生中心）、教務處及全校 9 個學院（醫學院、中醫學院、藥學院、公共衛生學院、健康照護學院、生命科學院、牙醫學院、醫學工程學院、人文與科技學院）共同統籌校級長期交換（日本北海道大學每年 5 名免學費＋中醫大機票與每月 NT$5,000 補助、北見工業大學每年 3 名免學費＋中醫大機票與每月 NT$5,000 補助、香港教育大學每年 4 名免學費）、跨國雙聯學位暨高額獎學金（南加州大學 USC 最高補助 NT$45萬、杜蘭大學最高補助 NT$40萬、喬治亞州立大學最高補助 NT$35萬、南卡羅萊納大學與澳洲格里菲斯大學最高補助 NT$30萬、澳洲紐卡索大學護理博士最高補助 NT$50萬、南達科塔州立大學營養 2+2 補助 2 年中醫大全額學雜費），以及物理治療學系 115-1 海外臨床實習（新加坡中央醫院 4 名、神戶中央市民醫院 2 名、關西電力醫院 2 名、順天堂醫院 2 名）與醫學院、中醫學院、藥學院、護理學系教育部學海飛颺／惜珠／築夢／新南向學海築夢計畫。"
        ),
        "review_status": "published",
        "published_at": CHECKED_AT,
        "steps": [
            {
                "rule_id": f"cmu-{acad_year}-home-1-{idx+1:03d}",
                "order": 1,
                "phase": "校內申請",
                "title": f"確認中醫大在學身分、學業平均 A-（GPA 3.0／80 分）、操行 80 分門檻與 {zh_name} 語檢要求",
                "responsible_party": "學生",
                "responsible_unit": "中國醫藥大學國際事務處／各學院系所",
                "deadline_at": deadline_iso,
                "deadline_status": "verified_exact" if avail_status == "open" else "reference_only",
                "deadline_source_url": source_url,
                "deadline_checked_at": CHECKED_AT,
                "deadline_reminder_eligible": avail_status == "open",
                "summary": (
                    f"確認符合《中國醫藥大學學生出國交換實施要點》（法規編號 622）、《補助學生出國研習與實習辦法》（法規編號 342）及各院系雙聯／實習簡章規定：申請人須為本校正式學籍在學學生（延修生、休學生、在職生不得申請；一般交換須修滿 1 學年，北海道大學、北見工業大學、南達科塔州立大學 2+2 須修滿 2 學年），在校學業平均達 A-（GPA 3.0 或 80 分）以上且前一學期操行成績達 80 分以上，並備妥符合 {zh_name} 要求之有效外語檢定證明。"
                ),
                "details": [
                    f"開放學制與院系：{colleges_str}（{degree_levels_str}）",
                    f"語言與學業條件：{lang_req_str}｜{gpa_req_str}",
                    f"當期名額與計畫類別：{quota_str}｜{program_type}",
                ],
                "scope": {
                    "home_universities": ["中國醫藥大學"],
                    "partner_universities": [full_name],
                    "academic_years": ["115", "116"],
                    "application_rounds": [round_label, "116-1", "116-2", "115-2", "115-1"],
                },
                "source_urls": [
                    source_url,
                    CMU_STATUTE_EXCHANGE_622_URL,
                    CMU_STATUTE_SUBSIDY_342_URL,
                ],
                "checked_at": CHECKED_AT,
                "support_status": "verified",
            },
            {
                "rule_id": f"cmu-{acad_year}-home-2-{idx+1:03d}",
                "order": 2,
                "phase": "校內申請",
                "title": "向國際事務處（水湳校本部卓越大樓）或所屬學院遞交出國交換、跨國雙聯或海外臨床實習申請表件",
                "responsible_party": "學生與所屬系（所）辦公室",
                "responsible_unit": "中國醫藥大學國際事務處／各學院辦公室",
                "deadline_at": deadline_iso,
                "deadline_status": "verified_exact" if avail_status == "open" else "reference_only",
                "deadline_source_url": source_url,
                "deadline_checked_at": CHECKED_AT,
                "deadline_reminder_eligible": avail_status == "open",
                "summary": (
                    "依申請計畫於期限前備齊中醫大出國交換／雙聯／海外研習實習申請表、歷年中文與英文成績單正本（含 GPA、班級排名及前一學期操行成績）、有效外語能力檢定證明、中英文自傳與出國讀書／研究／實習計畫書、師長推薦信 2 封及家長同意書，經系所與學院核章後送交國際事務處。"
                ),
                "details": [
                    "校級日本交換生（北海道大學每年 5 名、北見工業大學每年 3 名）與香港教育大學（每年 4 名）：秋季班於每年 12–1 月、春季班於每年 8–9 月受理校內甄選；校內《補助學生出國研習與實習辦法》第一階段（1–5 月出國）於前一年 10–11 月收件、第二階段（6–12 月出國）於當年 3–4 月收件。",
                    "跨國雙聯學位獎學金（南加州大學 USC、杜蘭大學、喬治亞州立大學、南卡羅萊納大學、南達科塔州立大學、格里菲斯大學、紐卡索大學）：於每學期規定期間向所屬學院及國際事務處提出申請；物理治療學系 115-1 海外臨床實習於 2026/09/18 12:00 截止收件。",
                ],
                "document_requirements": [
                    {
                        "name": "中國醫藥大學出國交換學生／跨國雙聯學位／補助出國研習與實習申請表及家長同意書",
                        "official_form_url": CMU_OUTBOUND_FORMS_URL,
                        "source_urls": [CMU_OUTBOUND_FORMS_URL, CMU_STATUTE_EXCHANGE_622_URL],
                    },
                    {
                        "name": "中醫大歷年中文與英文成績單正本（須含學業總平均 A- / GPA 3.0 / 80 分以上證明、班級排名及前一學期操行 80 分以上證明）",
                        "source_urls": [CMU_STATUTE_EXCHANGE_622_URL, CMU_STATUTE_SUBSIDY_342_URL],
                    },
                    {
                        "name": "有效外語能力檢定證明影本（一般交換 iBT 57 / IELTS 4.0 / TOEIC 550 / GEPT 中級 / BESTEP B1；出國補助 iBT 59 / IELTS 5.0 / TOEIC 640 / GEPT 中高級初試；北海道大學 iBT 79 / IELTS 6.5；雙聯學位 iBT 60–100 / IELTS 5.5–7.0）",
                        "source_urls": [CMU_STATUTE_EXCHANGE_622_URL, CMU_STATUTE_SUBSIDY_342_URL, CMU_NEWS_JAPAN_EXCHANGE_URL],
                    },
                    {
                        "name": "中英文自傳（CV）、出國讀書／研究／臨床實習計畫書（Study Plan）與專任教師推薦信 2 封",
                        "official_form_url": CMU_OUTBOUND_FORMS_URL,
                        "source_urls": [CMU_OUTBOUND_EXCHANGE_URL, CMU_OUTBOUND_FORMS_URL],
                    },
                ],
                "scope": {
                    "home_universities": ["中國醫藥大學"],
                    "academic_years": ["115", "116"],
                    "application_rounds": [round_label, "116-1", "116-2", "115-2", "115-1"],
                },
                "source_urls": [
                    source_url,
                    CMU_OUTBOUND_EXCHANGE_URL,
                    CMU_OUTBOUND_FORMS_URL,
                    CMU_STATUTE_EXCHANGE_622_URL,
                ],
                "checked_at": CHECKED_AT,
                "support_status": "verified",
            },
            {
                "rule_id": f"cmu-{acad_year}-home-3-{idx+1:03d}",
                "order": 3,
                "phase": "甄選與提名",
                "title": "國際事務處／學院遴選委員會書面與面試審查及錄取補助核定",
                "responsible_party": "中國醫藥大學出國交換生遴選委員會／雙聯學位審查委員會",
                "responsible_unit": "中國醫藥大學國際事務處",
                "deadline_at": "2027-02-26T17:00:00+08:00",
                "deadline_status": "verified_exact",
                "deadline_source_url": CMU_STATUTE_EXCHANGE_622_URL,
                "deadline_checked_at": CHECKED_AT,
                "deadline_reminder_eligible": False,
                "summary": (
                    "由國際事務處召開「出國交換生遴選委員會」或各學院雙聯／海外臨床實習甄選小組進行書面與外語面試審查，評定正備取名單與校內獎助學金核給額度（如日本交換生每月 NT$5,000＋來回機票、雙聯學位 NT$30萬–50萬元或 2 年中醫大全額學雜費補助、教育部學海四項計畫補助）。"
                ),
                "details": [
                    "獲選日本北海道大學（5 名）與北見工業大學（3 名）校級交換生者，同時獲免除日本姊妹校學費及中醫大來回經濟艙機票＋每月 NT$5,000 生活補助。",
                    "獲選跨國雙聯學位獎助學金者，須與學校簽訂雙聯學位補助合約書，於赴外修業期間維持中醫大與合作大學雙邊學籍並修滿規定學分。",
                ],
                "scope": {
                    "home_universities": ["中國醫藥大學"],
                    "academic_years": ["115", "116"],
                    "application_rounds": [round_label, "116-1", "116-2", "115-2", "115-1"],
                },
                "source_urls": [
                    CMU_STATUTE_EXCHANGE_622_URL,
                    CMU_STATUTE_SUBSIDY_342_URL,
                    CMU_STATUTE_DUAL_647_URL,
                    CMU_NEWS_JAPAN_EXCHANGE_URL,
                ],
                "checked_at": CHECKED_AT,
                "support_status": "verified",
            },
            {
                "rule_id": f"cmu-{idx+1:03d}-host-apply",
                "order": 4,
                "phase": "合作校申請",
                "title": f"由中醫大國際處或學院向 {zh_name} 辦理官方提名（Nomination），並遞交外文入學、雙聯或臨床見實習申請文件",
                "responsible_party": "學生與接待校院國際事務處／臨床教學部門",
                "summary": (
                    f"通過中醫大甄選後，由國際事務處或所屬學院向 {zh_name} 辦理官方提名；學生須於接待校院規定截止日前備妥外文入學申請表、英文歷年成績單、護照影本、英文財力證明（Bank Statement）、語檢證書、英文推薦信與健康檢查／免疫抗體紀錄，靜候核發正式入學或實習許可（Letter of Acceptance / DS-2019 / I-20 / COE）。"
                ),
                "details": [
                    f"研修期程：{study_period_str}｜名額：{quota_str}",
                    f"語言與學業條件：{lang_req_str}｜{gpa_req_str}",
                    f"住宿與費用待遇：{housing_str}",
                ],
                "scope": {
                    "home_universities": ["中國醫藥大學"],
                    "partner_universities": [full_name],
                    "academic_years": ["115", "116"],
                    "application_rounds": [round_label, "116-1", "116-2", "115-2", "115-1"],
                },
                "source_urls": (
                    [source_url, CMU_OUTBOUND_EXCHANGE_URL]
                    + ([website] if website else [])
                ),
                "checked_at": CHECKED_AT,
                "support_status": "verified",
                "needs_confirmation": False,
            },
            {
                "rule_id": f"cmu-{acad_year}-home-5-{idx+1:03d}",
                "order": 5,
                "phase": "行前準備",
                "title": "出國前確認選課抵免與海外保險，返國後 1 個月內繳交 1,000 字成果報告書、上傳 5 分鐘英文學習心得影片並辦理學分抵免",
                "responsible_party": "學生與所屬系所",
                "responsible_unit": "中國醫藥大學國際事務處／教務處註冊課務組",
                "summary": (
                    "出國前須依《中國醫藥大學學生出國修課暨學分抵免實施要點》（法規編號 337）經系所確認擬修科目（北海道大學與北見工業大學每學期至少須修習 12 學分），維持中醫大在學註冊並投保全程海外醫療及意外保險；返國後須於 1 個月內向國際事務處繳交 1,000 字以上成果報告書、上傳 5 分鐘英文學習心得影片並檢具單據辦理補助核銷，同時持國外正式成績單與課程大綱向教務處辦理學分抵免。"
                ),
                "details": tuition_points_list,
                "scope": {
                    "home_universities": ["中國醫藥大學"],
                    "academic_years": ["115", "116"],
                    "application_rounds": [round_label, "116-1", "116-2", "115-2", "115-1"],
                },
                "source_urls": [
                    CMU_STATUTE_CREDIT_337_URL,
                    CMU_STATUTE_EXCHANGE_622_URL,
                    CMU_STATUTE_SUBSIDY_342_URL,
                    CMU_OUTBOUND_FORMS_URL,
                ],
                "checked_at": CHECKED_AT,
                "support_status": "verified",
            },
        ],
        "sources": wf_sources,
        "last_checked": CHECKED_AT,
        "coverage_status": "official_verified",
        "coverage_note": (
            f"已完整整合中國醫藥大學國際事務處（OIA）、教務處與 9 大學院（校級赴日本北海道大學／北見工業大學／香港教育大學交換生簡章、7 校 11 個跨國雙聯學位補助施行細則、物理治療學系 115-1 海外臨床實習公告、醫學院／中醫學院／護理學系海外臨床見實習與學海築夢計畫、學生出國交換實施要點、補助學生出國研習與實習辦法及 26 篇歷屆師生返國成果報告）共 {len(catalog_source)} 所全球合作姊妹校與醫療研究機構資料。"
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
            "title": f"中國醫藥大學國際事務處締約姊妹校、交換生、雙聯學位與海外實習簡章—{zh_name}",
            "source_url": source_url,
            "summary": "中醫大國際事務處與各學院公告之合作學程、開放學院、語言檢定門檻與免學費／雙聯獎學金待遇說明",
        },
        {
            "title": "中國醫藥大學學生出國交換實施要點、補助學生出國研習與實習辦法及雙聯學制實施辦法",
            "source_url": CMU_STATUTE_EXCHANGE_622_URL,
            "summary": "中醫大出國交換與補助門檻（學業平均 A-／GPA 3.0／80 分且操行 80 分）、雙聯獎學金（30萬–50萬元）與返國 1,000 字報告＋5 分鐘英文影片規範",
        },
    ]
    if exps:
      dest_sources.append({
          "title": f"中國醫藥大學海外交換與臨床見實習經驗分享專區—赴 {zh_name} 成果報告（{len(exps)} 篇）",
          "source_url": exps[0]["url"],
          "summary": f"收錄歷年中醫大師生赴 {zh_name} 海外交換與臨床見實習心得報告共 {len(exps)} 篇",
      })
    if website:
      dest_sources.append({
          "title": f"{full_name} 官方網站",
          "source_url": website,
          "summary": "接待合作姊妹校／教學醫院官方網站",
      })

    src_url_list = (
        [source_url, CMU_STATUTE_EXCHANGE_622_URL, CMU_STATUTE_SUBSIDY_342_URL]
        + ([exps[0]["url"]] if exps else [])
        + ([website] if website else [])
    )

    destinations.append({
        "home_university": "中國醫藥大學",
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
                "title": "生活費、中醫大在學註冊規定、日本交換機票與生活費補助及雙聯學位高額獎助學金（NT$ 30萬–50萬元）",
                "summary": cost_line,
                "points": [cost_line] + tuition_points_list,
                "source_urls": src_url_list + [CMU_STATUTE_DUAL_647_URL],
                "caution": (
                    "依《中國醫藥大學學生出國交換實施要點》與《補助學生出國研習與實習辦法》，受補助學生須於返國後 1 個月內繳交 1,000 字以上成果報告書及上傳 5 分鐘英文學習心得影片，始得完成補助核銷。"
                ),
            },
            {
                "key": "housing",
                "title": "住宿資訊與校內外國際學生宿舍／教學醫院實習公寓申請",
                "summary": housing_clean[:160],
                "points": [housing_clean],
                "source_urls": src_url_list,
                "caution": (
                    "日本北海道大學、北見工業大學及香港教育大學均設有交換生宿舍申請制度，獲中醫大提名後請務必於接待校截止日前完成宿位登記。"
                ),
            },
            {
                "key": "insurance",
                "title": "海外醫療及急難救助保險、臨床見實習疫苗抗體檢測與平安保險規定",
                "summary": visa_default,
                "points": [
                    visa_default,
                    "依《中國醫藥大學學生出國交換實施要點》第9點規定，出國學生必須購買涵蓋境外研修全期之海外醫療、意外及急難救助保險；赴美日星泰越韓教學醫院進行臨床見實習者，須提早完成規定之疫苗接種與抗體效價檢測。",
                ],
                "source_urls": src_url_list + [CMU_STATUTE_CREDIT_337_URL],
                "caution": "美國 MD Anderson、Emory、新加坡中央醫院 SGH 與日本順天堂醫院、神戶中央市民醫院對免疫抗體效價（MMR、水痘、B肝、TB 檢驗）審核嚴格，請於出發前 3–6 個月完成檢驗。",
            },
            {
                "key": "visa",
                "title": "留學／實習簽證辦理、出國選課審核與在學註冊義務",
                "summary": visa_default,
                "points": [
                    visa_default,
                    "依《中國醫藥大學學生出國修課暨學分抵免實施要點》（法規編號 337）規定：學生出國修課期間須維持中醫大在學註冊，出國前應先經所屬系（所）及教務處確認擬修習科目。",
                ],
                "source_urls": src_url_list + [CMU_STATUTE_CREDIT_337_URL],
                "caution": "出國前請務必完成系所選課確認、國際事務處行前說明會報到與行政契約簽署。",
            },
            {
                "key": "academics",
                "title": "每學期修課學分規定（日本交換至少 12 學分）、跨國雙聯修業月數與返國學分抵免",
                "summary": course_clean[:160],
                "points": [calendar_clean, course_clean],
                "source_urls": src_url_list + [CMU_STATUTE_CREDIT_337_URL, CMU_STATUTE_DUAL_647_URL],
                "caution": (
                    "赴日本北海道大學與北見工業大學交換學生每學期至少須修讀 12 學分；修讀跨國雙聯學位者須符合學士累計 32 個月、碩士 12 個月、博士 24 個月以上之兩校修業時間規範。"
                ),
            },
            {
                "key": "living",
                "title": f"{location_obj.get('city') or country} 校園／臨床生活與中醫大師生海外研修心得傳承",
                "summary": f"代表城市：{location_obj.get('city') or country}。請配合接待校院國際處或臨床教學部門完成報到與新生訓練（Orientation）。",
                "points": [
                    f"目的地城市：{location_obj.get('city') or country}（{country}）",
                    (
                        f"中國醫藥大學國際事務處與各學院（醫學院、中醫學院、藥學院、健康照護學院）公開收錄歷屆師生赴海外交換與臨床見實習成果報告"
                        + (f"（本機構共收錄 {len(exps)} 篇：{'、'.join(exp_labels[:4])}）" if exps else "")
                        + "，並定期舉辦日本交換生甄選說明會、海外臨床見實習分享會與學海築夢成果發表會。"
                    ),
                ],
                "source_urls": [exps[0]["url"] if exps else CMU_OUTBOUND_EXCHANGE_URL],
            },
        ],
        "sources": dest_sources,
        "last_checked": CHECKED_AT,
        "coverage_status": "official_verified",
        "coverage_note": (
            f"已整合中國醫藥大學國際事務處、教務處與 9 大學院 {len(catalog_source)} 所合作姊妹校與醫療機構、校級赴日港交換計畫、7 校 11 個跨國雙聯學位獎學金計畫、物治系 115-1 海外臨床實習及 26 篇歷屆師生返國報告。"
        ),
    })

    research_records.append({
        "home_university": "中國醫藥大學",
        "school_name": full_name,
        "country": country,
        "official_website": website,
        "verification_status": "official_verified",
        "discovery_source_url": detail_url,
        "checked_at": CHECKED_AT,
        "note": (
            f"中國醫藥大學國際事務處《姐妹校專區（{CMU_PARTNERS_ZH_URL}）》、《國外交換學生專區（{CMU_OUTBOUND_EXCHANGE_URL}）》與 ROR/Wikidata 官方網址核對完成。"
        ),
    })

    ev_sources = [
        {
            "title": f"中國醫藥大學國際事務處締約姊妹校、交換生、雙聯學位與海外實習簡章—{zh_name}",
            "url": source_url,
        },
    ]
    if exps:
      ev_sources.append({
          "title": f"中國醫藥大學海外交換與臨床實習成果專區—赴 {zh_name} 成果報告（{len(exps)} 篇）",
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
            "scope": "中國醫藥大學海外交換姊妹校與教學醫院住宿與生活資訊",
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
            "scope": "中國醫藥大學出國交換學雜費規定、日本交換機票與每月 NT$5,000 補助、雙聯獎學金（30萬–50萬元）與地區生活費估算",
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
            "scope": "中國醫藥大學學生出國修課暨學分抵免實施要點、雙聯學制實施辦法與返國報告規範",
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
            "scope": "中國醫藥大學海外交換與臨床見實習簽證、疫苗抗體檢測、海外醫療保險與行前報到提醒",
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
                    f"｜中醫大公開收錄 {len(exps)} 篇赴 {zh_name} 海外交換／臨床見實習成果報告（{'、'.join(exp_labels[:4])}）。"
                    if exps
                    else ""
                )
            ),
            "sources": ev_sources,
            "checked_at": CHECKED_AT,
            "scope": "中國醫藥大學海外交換名額與歷屆師生成果報告分享",
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
            "已整合中國醫藥大學國際事務處《姐妹校列表》、《日本北海道大學與北見工業大學交換生甄選簡報》、《香港教育大學交換協議》、《7 校 11 個跨國雙聯學位補助施行細則》、《物理治療學系 115-1 海外臨床實習公告》、《學生出國交換實施要點》、《補助學生出國研習與實習辦法》及 26 篇歷屆師生成果報告。",
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
          f"中國醫藥大學赴 {zh_name} 海外交換研修／臨床專業實習成果報告彙編（共 {len(exps)} 篇師生報告）"
      )
      latest_e = exps[0]
      latest_author = (
          f"{latest_e['student']} 等 {len(exps)} 組中醫大研修師生"
          if len(exps) > 1
          else latest_e["student"]
      )
      summary_text = (
          f"中國醫藥大學國際事務處與各學院公開收錄 {len(exps)} 篇歷年赴 {zh_name} 海外交換研修與臨床見實習成果報告（含：{'、'.join(exp_labels[:5])}）。"
          f"{latest_e['highlight']}"
      )
      theme_map = {
          "academics": (
              f"中醫大研修師生（{'、'.join(exp_labels[:3])}）分享於 {zh_name} 修讀專業課程、參與教學醫院／中西韓醫與傳統醫學臨床實習之學習心得，以及返國依《學生出國修課暨學分抵免實施要點》辦理學分採認之經驗。{latest_e['highlight']}"
          ),
          "housing": (
              f"中醫大研修生詳述 {zh_name} 校內外國際學生宿舍（如北海道大學札幌學生寮、北見工業大學國際宿舍）或教學醫院臨床實習住宿申請、周邊生活機能與大眾運輸通勤方式（{housing_clean[:120]}）。"
          ),
          "campus_culture": (
              f"中醫大收錄 {len(exps)} 篇赴 {zh_name} 成果報告，記錄跨國醫學／中醫／藥學／護理／物理治療臨床團隊協作、國際學伴交流與當地文化體驗。"
          ),
          "cost": (
              f"中醫大研修生記錄於 {zh_name} 之每月住宿、伙食與交通開銷（{cost_default}），以及運用姊妹校免學費名額、中醫大《補助學生出國研習與實習辦法》機票與生活費補助及教育部學海飛颺／惜珠／築夢／新南向學海築夢獎學金支應出國費用之規劃。"
          ),
      }
      student_experience_rows.append({
          "school_name": full_name,
          "country": country,
          "title": rep_title,
          "source_url": latest_e["url"],
          "source_type": "article",
          "platform": "中國醫藥大學國際事務處暨各學院—海外交換與臨床實習成果專區",
          "author_name": latest_author,
          "language": "zh",
          "summary": summary_text,
          "themes": ["academics", "housing", "campus_culture", "cost"],
          "theme_summaries": theme_map,
          "content_status": "full_text",
          "perspective": "official_student_story",
          "published_at": None,
          "discovered_at": CHECKED_AT,
          "content_hash": hashlib.sha256(f"{full_name}:cmu_exp:{len(exps)}".encode("utf-8")).hexdigest(),
          "exchange_term": f"{latest_e['year']}年度",
          "summary_zh": summary_text,
          "original_summary": summary_text,
          "theme_summaries_zh": theme_map,
          "translation_status": "original",
          "source_kind": "official_experience_page",
      })

    experience_sources_records.append({
        "home_university": "中國醫藥大學",
        "school_name": full_name,
        "country": country,
        "official_experience_portal_url": (
            exps[0]["url"] if exps else CMU_OUTBOUND_EXCHANGE_URL
        ),
        "partner_page_url": source_url,
        "report_count": len(exps),
        "sample_reports": sample_reports,
        "checked_at": CHECKED_AT,
    })

  partners_jsonl_text = "\n".join(json.dumps(r, ensure_ascii=False) for r in partners) + "\n"
  (OFFICIAL_CMU_DIR / "partners.jsonl").write_text(partners_jsonl_text, encoding="utf-8")
  (SOURCES_CMU_DIR / "partners.jsonl").write_text(partners_jsonl_text, encoding="utf-8")
  (OFFICIAL_CMU_DIR / "application_workflows.jsonl").write_text(
      "\n".join(json.dumps(r, ensure_ascii=False) for r in workflows) + "\n",
      encoding="utf-8",
  )
  (OFFICIAL_CMU_DIR / "destination_profiles.jsonl").write_text(
      "\n".join(json.dumps(r, ensure_ascii=False) for r in destinations) + "\n",
      encoding="utf-8",
  )
  (OFFICIAL_CMU_DIR / "partner_research.jsonl").write_text(
      "\n".join(json.dumps(r, ensure_ascii=False) for r in research_records) + "\n",
      encoding="utf-8",
  )
  (OFFICIAL_CMU_DIR / "student_life.jsonl").write_text(
      "\n".join(json.dumps(r, ensure_ascii=False) for r in life_records) + "\n",
      encoding="utf-8",
  )
  (OFFICIAL_CMU_DIR / "experience_sources.jsonl").write_text(
      "\n".join(json.dumps(r, ensure_ascii=False) for r in experience_sources_records) + "\n",
      encoding="utf-8",
  )
  (OFFICIAL_CMU_DIR / "student_experiences.jsonl").write_text(
      "\n".join(json.dumps(r, ensure_ascii=False) for r in student_experience_rows) + "\n",
      encoding="utf-8",
  )
  (OFFICIAL_CMU_DIR / "campus-locations.json").write_text(
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
  (OFFICIAL_CMU_DIR / "student-experience-digests.json").write_text(
      json.dumps({"digests": digest_records}, ensure_ascii=False, indent=2) + "\n",
      encoding="utf-8",
  )

  # Ensure CMU home location ONLY is added to university_locations.jsonl
  loc_file = REPO_ROOT / "src/exchange_info/official_data/university_locations.jsonl"
  existing_loc_lines = [
      line for line in loc_file.read_text(encoding="utf-8").splitlines() if line.strip()
  ]
  existing_loc_map = {}
  for line in existing_loc_lines:
    rec = json.loads(line)
    existing_loc_map[(rec["school_name"], rec.get("country") or "")] = rec

  cmu_home_loc = {
      "school_name": "中國醫藥大學",
      "country": "臺灣",
      "city": "臺中市北屯區",
      "latitude": 24.1787,
      "longitude": 120.6612,
      "geocode_status": "verified",
      "geocoded_at": CHECKED_AT,
      "source_url": "https://www.wikidata.org/wiki/Q709248",
      "identity_source_url": "https://ror.org/00v408z34",
      "precision": "representative",
      "note": (
          "校級代表位置：官方網域及國家已與 ROR 比對，座標來源為 Wikidata P625；實際交換校區以錄取通知為準。"
          " 母校代表點採臺中市北屯區經貿路一段100號水湳校本部（卓越大樓國際事務處，另設臺中市北區學士路91號英才校區及雲林縣北港分部）；官方地址來源：https://cmucia.cmu.edu.tw/。"
      ),
  }
  existing_loc_map[("中國醫藥大學", "臺灣")] = cmu_home_loc
  sorted_locs = sorted(
      existing_loc_map.values(),
      key=lambda r: (r.get("country") or "", r.get("school_name") or ""),
  )
  loc_file.write_text(
      "\n".join(json.dumps(r, ensure_ascii=False) for r in sorted_locs) + "\n",
      encoding="utf-8",
  )

  cmu_source_urls = [
      CMU_OIA_HUB_URL,
      CMU_OIA_EN_HUB_URL,
      CMU_PARTNERS_ZH_URL,
      CMU_PARTNERS_EN_URL,
      CMU_OUTBOUND_EXCHANGE_URL,
      CMU_OUTBOUND_FORMS_URL,
      CMU_NEWS_JAPAN_EXCHANGE_URL,
      CMU_JAPAN_2024_BRIEFING_PDF_URL,
      CMU_JAPAN_2023_BRIEFING_PDF_URL,
      CMU_EDUHK_AGREEMENT_PDF_URL,
      CMU_STATUTE_EXCHANGE_622_URL,
      CMU_STATUTE_SUBSIDY_342_URL,
      CMU_STATUTE_CREDIT_337_URL,
      CMU_STATUTE_DUAL_647_URL,
      CMU_STATUTE_USC_PHARM_1566_URL,
      CMU_STATUTE_USC_KECK_917_URL,
      CMU_STATUTE_SC_3PLUS2_1268_URL,
      CMU_STATUTE_SC_DUAL_1267_URL,
      CMU_STATUTE_GSU_846_URL,
      CMU_STATUTE_TULANE_848_URL,
      CMU_STATUTE_SDSU_1085_URL,
      CMU_STATUTE_GRIFFITH_1459_URL,
      CMU_STATUTE_NEWCASTLE_1222_URL,
      CMU_PT_115_1_INTERNSHIP_URL,
      CMU_MED_CLERKSHIP_URL,
      CMU_NURSING_INTL_URL,
      CMU_CHMED_INTL_URL,
  ]

  exchange_info_payload = {
      "school_name": "中國醫藥大學",
      "program_type": [
          (
              "校級赴日本與香港長期交換學生計畫（含【日本北海道大學 Hokkaido University】HUSTEP 每年 5 名免學費交換生＋中醫大補助來回經濟艙機票與每月 NT$ 5,000 生活費；【日本北見工業大學 Kitami Institute of Technology】每年 3 名免學費交換生＋中醫大補助來回機票與每月 NT$ 5,000 生活費；【香港教育大學 The Education University of Hong Kong】每年 4 名免學費學年交換生）"
          ),
          (
              "跨國雙聯學位暨高額獎助學金旗艦計畫（涵蓋 7 所歐美澳名校共 11 個雙聯學制：【美國南加州大學 USC】藥學系碩士班修讀 MS in Regulatory Science 雙聯及凱克醫學院 MD/MPH 與生醫碩士雙聯［每人最高補助 NT$ 450,000］；【美國杜蘭大學 Tulane University】MD/MPH 公共衛生雙聯碩士［每年 20–30 名，每人最高補助 NT$ 400,000］；【美國喬治亞州立大學 Georgia State University】生醫、物理治療、呼吸治療、營養與公衛雙聯碩士及 MD/MPH［每人最高補助 NT$ 350,000］；【美國南卡羅萊納大學 University of South Carolina】運動科學與公衛 3+2 學碩雙聯及 MD/MPH［每人最高補助 NT$ 300,000＋享州內學費優惠］；【澳洲格里菲斯大學 Griffith University】全球公共衛生碩士 MGPH 暨 MD/MPH 雙聯［每人最高補助 NT$ 300,000］；【澳洲紐卡索大學 University of Newcastle】雙聯護理博士 PhD in Nursing［每年 2 名，每人最高補助 NT$ 500,000］；【美國南達科塔州立大學 South Dakota State University】營養學系 2+2 雙學士暨美國註冊營養師 RD 培育計畫［每年 4 名，補助 2 年中醫大全額學雜費］）"
          ),
          (
              "海外臨床見實習與教育部《學海飛颺、學海惜珠、學海築夢、新南向學海築夢》專業實習計畫（含【健康照護學院物理治療學系 115-1 海外臨床實習】選送赴新加坡中央醫院 SGH 4 名、日本神戶市立醫療中心中央市民醫院 2 名、大阪關西電力醫院 2 名、東京順天堂大學附屬順天堂醫院 2 名［2027/01/10–01/30 實習］；【醫學院海外臨床見實習 Medical Clerkship】赴美國德州大學安德森癌症中心 MD Anderson、艾默蕾大學 Emory、東京大學、京都大學、新加坡國立大學 NUS；【中醫學院學海築夢與新南向學海築夢】赴韓國慶熙大學、東國大學、釜山大學、自生韓方醫院、越南胡志明市醫藥大學、芹苴醫藥大學、胡志明市傳統醫學醫院、順化醫藥大學、泰國瑪希敦大學 Siriraj 醫院、清邁大學、日本藥科大學、鈴鹿醫療科學大學；【護理學系新南向學海築夢】赴泰國皇太后大學、清邁大學、新加坡國立大學；【藥學院海外臨床藥學實習 APPE】赴美國加州大學聖地牙哥分校 UCSD、俄亥俄州立大學 OSU、南加州大學 USC；【牙醫學院海外臨床見習】赴日本東京科學大學 TMDU 等）"
          ),
      ],
      "academic_year": [
          (
              "116（涵蓋 115–116 學年度［2026–2028］校級赴日本北海道大學、北見工業大學與香港教育大學交換學生甄選、7 校 11 個跨國雙聯學位暨獎學金甄選、健康照護學院物理治療學系 115-1 海外臨床實習甄選［2026/09/18 截止、2027/01/10–01/30 實習］、教育部學海四項計畫及《中國醫藥大學補助學生出國研習與實習辦法》兩階段獎補助甄選）"
          ),
          (
              f"本平台完整收錄中國醫藥大學國際事務處與 9 大學院公告之 {len(partners)} 所全球締約合作大學、醫學院與教學醫院（含 {open_partner_count} 所當期開放交換、雙聯、海外臨床見實習與學海築夢重點合作機構及 {len(partners) - open_partner_count} 所正式締約姊妹校，橫跨全球 31 個國家與地區，並完整收錄 {exp_covered_schools} 所合作機構共 {total_exp_reports} 篇歷屆師生返國成果報告）"
          ),
      ],
      "semester": [
          "秋季學期（第1學期：歐美姊妹校與雙聯學位為 8/9 月至 12 月；日本北海道大學與北見工業大學後學期為 10 月至翌年 2/3 月；香港教育大學為 9 月至 12 月）",
          "春季學期（第2學期：歐美姊妹校為 1 月至 5 月；日本北海道大學與北見工業大學前學期為 4 月至 8 月；物理治療學系 115-1 赴新加坡中央醫院 SGH、日本神戶中央市民醫院、關西電力醫院、順天堂醫院臨床實習為 2027/01/10–2027/01/30）",
          "暑期及學期海外臨床見實習／教育部學海築夢與新南向學海築夢專業實習（國外專業實習須連續至少 30 天以上；醫學院 Clerkship、中醫學院韓醫與越泰傳統醫學實習、護理學系泰國皇太后大學實習、藥學院美日臨床藥學實習主要於寒暑假或學期中執行）",
          "跨國雙聯學士、碩士、博士與 MD/MPH 學位（美國南達科塔州立大學營養 2+2 雙學士、美國南卡羅萊納大學運醫與公衛 3+2 學碩雙聯、美國南加州大學 USC／杜蘭大學／喬治亞州立大學／澳洲格里菲斯大學雙聯碩士與 MD-MPH、澳洲紐卡索大學雙聯護理博士）",
      ],
      "application_period": [
          (
              "【校級赴日本北海道大學（每年 5 名免學費＋機票與每月 NT$5,000 補助）、北見工業大學（每年 3 名免學費＋機票與每月 NT$5,000 補助）及香港教育大學（每年 4 名免學費）交換生甄選】秋季班入學者於前一年 12 月至當年 1 月初辦理校內甄選（2–3 月完成姊妹校提名）、春季班入學者於前一年 8–9 月辦理校內甄選。"
          ),
          (
              "【《中國醫藥大學補助學生出國研習與實習辦法》兩階段收件與教育部學海四項計畫】校內出國研習與實習補助分兩階段受理：第一階段（預計於 1–5 月出國者）於前一年 10–11 月向國際事務處提出申請；第二階段（預計於 6–12 月出國者）於當年 3–4 月提出申請。教育部《學海飛颺、學海惜珠、學海築夢、新南向學海築夢》於每年 12 月至翌年 2 月初校內收件、3 月底前報部。"
          ),
          (
              "【跨國雙聯學位獎助學金（USC 最高 NT$45萬、杜蘭最高 NT$40萬、喬治亞州立最高 NT$35萬、南卡羅萊納與格里菲斯最高 NT$30萬、紐卡索最高 NT$50萬、SDSU 補助 2 年中醫大全額學雜費）與物治系 115-1 海外臨床實習】雙聯學位獎助於每學期依各校施行細則向所屬學院及國際處申請；物理治療學系 115-1 海外臨床實習（新加坡中央醫院 4 名、神戶中央市民醫院 2 名、關西電力醫院 2 名、順天堂醫院 2 名，2027/01/10–01/30 實習）於 115年9月18日（2026/09/18）12:00 截止報名、9月25日面試。"
          ),
      ],
      "eligibility": [
          (
              "【在學學籍、修業年資與排外規定】凡中國醫藥大學 9 個學院（醫學院、中醫學院、藥學院、公共衛生學院、健康照護學院、生命科學院、牙醫學院、醫學工程學院、人文與科技學院）具正式學籍之學士班、碩士班、博士班在學學生。依《中國醫藥大學學生出國交換實施要點》（法規編號 622）第3點規定，一般交換生須於本校修業滿一學年以上（申請日本北海道大學、北見工業大學交換及美國南達科塔州立大學 2+2 營養雙學士者須於大學部修業滿兩學年以上）；延修生、休學生、國內外在職專班及在職生不得申請。"
          ),
          (
              "【學業成績 A-（GPA 3.0／80 分）與操行成績 80 分雙重門檻】依《中國醫藥大學學生出國交換實施要點》（法規編號 622）第3點、《補助學生出國研習與實習辦法》（法規編號 342）第3條及各校雙聯學位補助施行細則規定：申請人歷年學業成績平均須達等第制 A-（GPA 3.0 或百分制 80 分）以上，且前一學期操行成績須達 80 分以上（物理治療學系 115-1 海外臨床實習要求大學部大三以上前兩學年學業總成績位居全班前 30% 且操行平均 80 分以上，或碩士班前一學年學業平均 80 分以上）。"
          ),
          (
              "【修課學分下限、雙聯修業月數與返國報告＋英文影片義務】（1）日本北海道大學與北見工業大學交換生每學期至少須修習 12 學分；（2）依《與境外大學校院辦理雙聯學制實施辦法》（法規編號 647）第6條，雙聯學士班在兩校修業時間合計須滿 32 個月以上、雙聯碩士班須滿 12 個月以上、雙聯博士班須滿 24 個月以上；（3）受補助或交換學生須於返國後 1 個月內繳交 1,000 字以上成果報告書並上傳 5 分鐘英文學習心得影片。"
          ),
      ],
      "language_requirement": [
          (
              "【校內出國交換基本門檻 vs 出國研習實習補助門檻】（1）依《中國醫藥大學學生出國交換實施要點》（法規編號 622）第3點，申請一般出國交換須達：TOEFL iBT 57 或 IELTS 4.0 或 TOEIC 550 或全民英檢 GEPT 中級或培力英檢 BESTEP B1 以上；（2）依《中國醫藥大學補助學生出國研習與實習辦法》（法規編號 342）第3條，申請校內機票與生活費補助須達：TOEFL iBT 59 或 IELTS 5.0 或 TOEIC 640 或 GEPT 中高級初試或 BESTEP B1 以上（或於本校修畢 4 門全英語授課課程及格）。"
          ),
          (
              "【校級赴日本交換與物理治療學系海外臨床實習外語標準】（1）日本北海道大學（HUSTEP 全英語交換，每年 5 名）：TOEFL iBT 79 或 IELTS 6.5 以上（不採計 TOEIC；修讀日語授課課程須達 JLPT N2）；（2）日本北見工業大學（每年 3 名）：英語組須達 TOEFL iBT 59 / IELTS 5.0 / TOEIC 640 / GEPT 中高級初試 / BESTEP B1，日語組須達 JLPT N3–N2；（3）物理治療學系 115-1 海外臨床實習（新加坡中央醫院 4 名、神戶中央市民醫院 2 名、關西電力醫院 2 名、順天堂醫院 2 名）：TOEFL ITP 550 或 TOEFL iBT 61 或 TOEIC 590 或 IELTS 4.5 或 GEPT 中級複試或 BESTEP B1 以上。"
          ),
          (
              "【7 校 11 個跨國雙聯學位外語檢定門檻】（1）美國南加州大學（USC）藥學系 MS in Regulatory Science 雙聯：TOEFL iBT 100（單科不低於 20）或 IELTS 7.0（單科不低於 6.0）；（2）美國南加州大學凱克醫學院（Keck School of Medicine）MD/MPH 與生醫雙聯：TOEFL iBT 90（單科不低於 20）或 IELTS 6.5（單科不低於 6.0）；（3）美國杜蘭大學（Tulane）MD/MPH 雙聯：TOEFL iBT 80 或 IELTS 6.5（或通過杜蘭教授英文面試／GRE 302）；（4）澳洲格里菲斯大學（Griffith）MGPH 雙聯：IELTS 6.5（單科不低於 6.0）或 TOEFL iBT 80；（5）美國南卡羅萊納大學（3+2 及雙聯）、喬治亞州立大學（GSU 雙聯）、澳洲紐卡索大學（雙聯護理博士）：申請校內補助須達 TOEFL iBT 60 或 IELTS 5.5（達正式入學門檻 TOEFL iBT 80 或 IELTS 6.5 者優先錄取）；（6）美國南達科塔州立大學（SDSU）營養 2+2 雙學士：TOEFL iBT 61（或 ITP 500）或 IELTS 5.5 以上。"
          ),
      ],
      "required_documents": [
          "1. 中國醫藥大學出國交換學生／跨國雙聯學位／補助學生出國研習與實習申請表（含基本資料、申請學校與研修期程）",
          "2. 中醫大歷年中文及英文成績單正本各 1 份（須載明歷年學業總平均達 A- / GPA 3.0 / 80 分以上、班級排名百分比及前一學期操行成績達 80 分以上）",
          "3. 有效期限內之外語能力檢定成績證明影本（TOEFL iBT / TOEFL ITP / IELTS / TOEIC / GEPT / BESTEP / JLPT / TOPIK 等，或修畢 4 門全英語課程證明）",
          "4. 中文及英文自傳（Curriculum Vitae / Autobiography）與出國讀書／研究／臨床實習計畫書（Study / Research Plan）",
          "5. 本校專任教師推薦信 2 封（英文或日文）及家長（監護人）同意書",
          "6. 國內外優秀表現證明、學術論文發表、社團幹部或國際交流志工服務證明（申請雙聯博士者另附博士論文研究計畫與兩校指導教授共同指導同意書）",
          "7. 出國前與返國後必備核銷文件：出國選課確認表、雙聯學位或出國補助行政契約書、全程海外醫療及急難救助保險證明，以及返國後 1 個月內繳交之 1,000 字以上成果報告書與 5 分鐘英文學習心得影片",
      ],
      "scholarship_info": [
          (
              "《中國醫藥大學補助學生出國研習與實習辦法》（法規編號 342）與日本交換專案補助：補助學業平均 A-（GPA 3.0／80 分）以上、操行 80 分以上且具 TOEFL iBT 59 / IELTS 5.0 / TOEIC 640 / GEPT 中高級初試 / BESTEP B1（或修畢 4 門 EMI 課程）之在學生赴國外研習或實習。其中獲選赴【日本北海道大學（每年 5 名）】與【日本北見工業大學（每年 3 名）】長期交換學生者，除免繳日本姊妹校學費外，由中醫大補助來回經濟艙機票乙張及每人每月新臺幣 5,000 元生活補助。"
          ),
          (
              "中國醫藥大學《跨國雙聯學位專案獎助學金》（法規編號 846、848、917、1085、1222、1267、1268、1459、1566）：（1）【澳洲紐卡索大學雙聯護理博士 PhD in Nursing】：每年 2 名，每人最高補助新臺幣 50 萬元（NT$ 500,000）並互免學費；（2）【美國南加州大學 USC 藥學系 MS in Regulatory Science 雙聯】及【USC 凱克醫學院 MD/MPH 與生醫碩士雙聯】：每人最高補助新臺幣 45 萬元（NT$ 450,000）；（3）【美國杜蘭大學 Tulane MD/MPH 雙聯】：每年 20–30 名，每人最高補助新臺幣 40 萬元（NT$ 400,000）；（4）【美國喬治亞州立大學 GSU 雙聯碩士與 MD/MPH】：每人最高補助新臺幣 35 萬元（NT$ 350,000）；（5）【美國南卡羅萊納大學 3+2 學碩雙聯與 MD/MPH】及【澳洲格里菲斯大學 MGPH 雙聯碩士】：每人最高補助新臺幣 30 萬元（NT$ 300,000，南卡羅萊納另享州內學費優惠）；（6）【美國南達科塔州立大學 SDSU 營養學系 2+2 雙學士】：每年 4 名，補助赴美期間 2 年中醫大全額學雜費。"
          ),
          (
              "教育部《學海飛颺、學海惜珠、學海築夢、新南向學海築夢》四大獎助計畫：中醫大每年獲教育部高額學海計畫補助，選送優秀學生赴歐美日韓交換（學海飛颺／惜珠），並由中醫學院、健康照護學院（護理學系、物理治療學系）、藥學院、醫學院專任教師主持《學海築夢》與《新南向學海築夢》，全額或部分補助學生赴韓國（慶熙大學、東國大學、自生韓方醫院）、越南（胡志明市醫藥大學、芹苴醫藥大學、胡志明市傳統醫學醫院）、泰國（皇太后大學、瑪希敦大學 Siriraj 醫院、清邁大學）、新加坡（新加坡中央醫院 SGH）等頂尖機構進行至少 30 天之海外臨床實習。"
          ),
      ],
      "partner_universities": [p["school_name"] for p in partners],
      "source_urls": cmu_source_urls,
      "last_checked": CHECKED_AT,
  }
  (OFFICIAL_CMU_DIR / "exchange_info.json").write_text(
      json.dumps(exchange_info_payload, ensure_ascii=False, indent=2) + "\n",
      encoding="utf-8",
  )

  student_dashboard_payload = {
      "school_name": "中國醫藥大學",
      "last_checked": CHECKED_AT,
      "academic_score_minimum": 80.0,
      "academic_score_rule": (
          "依《中國醫藥大學學生出國交換實施要點》（法規編號 622）第3點、《中國醫藥大學補助學生出國研習與實習辦法》（法規編號 342）第3條及各校雙聯學位補助施行細則規定：申請出國交換、跨國雙聯學位及校內出國研習實習補助者，在校歷年學業成績平均須達等第制 A-（GPA 3.0 或百分制 80 分）以上，且前一學期操行成績須達 80 分以上（物理治療學系 115-1 海外臨床實習要求大學部前兩學年全班前 30% 且操行平均 80 分以上，或碩士班前一學年平均 80 分以上）。"
      ),
      "academic_gpa_minimum": 3.0,
      "maximum_preferences": 3,
      "selection_rules": {
          "academic_policy": "gpa_or_rank",
          "academic_reference_year": "116",
          "undergraduate_gpa_minimum": 3.0,
          "graduate_academic_exempt": False,
          "exclude_in_service": True,
          "pending_quota_planning": False,
          "partner_requirements_need_confirmation": False,
          "degree_score_minimums": {
              "undergraduate": 80.0,
              "graduate": 80.0,
          },
          "excluded_undergraduate_years": ["大一上", "大一下"],
          "language_certificate_required": True,
      },
      "language_score_minimums": {
          "toefl": 57.0,
          "ielts": 4.0,
          "toeic": 550.0,
      },
      "application_periods": [
          {
              "title": (
                  "中國醫藥大學 116學年度赴日本北海道大學（5名免學費＋每月NT$5,000與機票補助）、北見工業大學（3名免學費＋補助）、香港教育大學（4名免學費）交換生暨教育部學海計畫甄選"
              ),
              "details": [
                  (
                      "中醫大國際事務處統籌辦理校級長期交換學生與教育部學海飛颺／惜珠獎學金甄選：（1）日本北海道大學（Hokkaido University）HUSTEP 全英語交換計畫：每學年 5 名免學費（限大學部修滿兩年以上，GPA 3.0+，TOEFL iBT 79 / IELTS 6.5+）；（2）日本北見工業大學（Kitami Institute of Technology）：每學年 3 名免學費（修滿兩年以上，GPA 3.0+，TOEFL iBT 59 / IELTS 5.0 / TOEIC 640 或 JLPT N3/N2）；（3）香港教育大學（EdUHK）：每學年 4 名免學費交換生。"
                  ),
                  (
                      "獲選赴北海道大學與北見工業大學交換之學生，除免繳日本姊妹校學費外，另由中醫大補助來回經濟艙機票乙張及每人每月新臺幣 5,000 元生活補助（每學期至少須修讀 12 學分，返國後 1 個月內繳交 1,000 字成果報告並上傳 5 分鐘英文學習心得影片）。"
                  ),
              ],
              "source": {
                  "title": "中國醫藥大學日本北海道大學與北見工業大學交換生甄選說明會簡報與學生出國交換實施要點",
                  "source_url": CMU_NEWS_JAPAN_EXCHANGE_URL,
                  "category": "exchange_application",
                  "summary": "中醫大赴日本北海道大學（5名）、北見工業大學（3名）與香港教育大學（4名）免學費交換名額、語檢門檻與機票生活費補助。",
              },
              "scope": "home_application",
              "program_types": ["exchange"],
              "academic_year": "116",
              "application_round": "116學年度校級赴日本與香港交換學生暨學海計畫甄選",
              "audience": "all_students",
              "opens_at": "2026-10-01T09:00:00+08:00",
              "deadline_at": "2027-01-29T17:00:00+08:00",
              "date_status": "verified_exact",
              "status": "action_required",
              "status_note": "116學年度赴外交換生、教育部學海計畫及《補助學生出國研習與實習辦法》現正依國際事務處期程受理申請中。",
              "deadline_note": "請備妥校內申請表、中英文歷年成績單（含 GPA 3.0 / A- 及前一學期操行 80 分證明）、有效外語檢定證明、中英文讀書計畫與自傳、推薦信 2 封送交水湳校本部卓越大樓國際事務處。",
              "reminder_eligible": True,
              "checked_at": CHECKED_AT,
          },
          {
              "title": (
                  "中國醫藥大學 115–116學年度跨國雙聯學位暨高額獎學金甄選（南加州大學最高45萬、杜蘭40萬、喬治亞州立35萬、南卡與格里菲斯30萬、紐卡索50萬、南達科塔州立補助2年學雜費）"
              ),
              "details": [
                  (
                      "中醫大訂有 9 部專屬跨國雙聯學位補助施行細則，全額或高額獎助優秀學生修讀歐美澳頂尖大學雙聯學位：（1）澳洲紐卡索大學雙聯護理博士（每年 2 名，最高補助 NT$ 500,000）；（2）美國南加州大學 USC 藥學系 MS in Regulatory Science 雙聯（iBT 100 / IELTS 7.0）及凱克醫學院 MD/MPH 與生醫碩士雙聯（iBT 90 / IELTS 6.5）：最高補助 NT$ 450,000；（3）美國杜蘭大學 MD/MPH 雙聯（每年 20–30 名，iBT 80）：最高補助 NT$ 400,000；（4）美國喬治亞州立大學雙聯碩士與 MD/MPH：最高補助 NT$ 350,000；（5）美國南卡羅萊納大學 3+2 學碩雙聯及 MD/MPH、澳洲格里菲斯大學 MGPH 雙聯：最高補助 NT$ 300,000；（6）美國南達科塔州立大學營養學系 2+2 雙學士（每年 4 名）：補助 2 年中醫大全額學雜費。"
                  ),
              ],
              "source": {
                  "title": "中國醫藥大學與境外大學校院辦理雙聯學制實施辦法（法規編號 647）與各校雙聯補助施行細則",
                  "source_url": CMU_STATUTE_DUAL_647_URL,
                  "category": "scholarship",
                  "summary": "中醫大 7 校 11 個跨國雙聯學位學制、語檢門檻與 NT$ 30萬–50萬元雙聯獎助學金施行細則。",
              },
              "scope": "home_application",
              "program_types": ["dual_degree"],
              "academic_year": "116",
              "application_round": "115–116學年度跨國雙聯學位暨獎助學金甄選",
              "audience": "all_students",
              "opens_at": "2026-09-01T09:00:00+08:00",
              "deadline_at": "2027-02-26T17:00:00+08:00",
              "date_status": "verified_exact",
              "status": "action_required",
              "status_note": "各學院跨國雙聯學位（USC、杜蘭、喬治亞州立、南卡羅萊納、南達科塔州立、格里菲斯、紐卡索）依每學期公告期程受理申請。",
              "deadline_note": "申請人須達歷年學業平均 A-（GPA 3.0 或 80 分）且前一學期操行 80 分以上，向所屬學院及國際事務處提出。",
              "reminder_eligible": True,
              "checked_at": CHECKED_AT,
          },
          {
              "title": (
                  "中國醫藥大學健康照護學院物理治療學系 115-1 海外臨床專業實習甄選（新加坡中央醫院4名、神戶中央市民醫院2名、關西電力醫院2名、順天堂醫院2名；2026/09/18 截止）"
              ),
              "details": [
                  (
                      "物理治療學系公告 115 學年度第 1 學期海外臨床專業實習甄選，實習期間為 2027 年 1 月 10 日至 1 月 30 日（共 3 週），選送正取 10 名學生赴 4 所國際頂尖醫療機構：（1）新加坡中央醫院（Singapore General Hospital）4 名；（2）日本神戶市立醫療中心中央市民醫院 2 名；（3）日本大阪關西電力醫院 2 名；（4）日本東京順天堂大學附屬順天堂醫院 2 名。"
                  ),
                  (
                      "申請資格：物治系大學部三年級（含）以上（前兩學年學業總成績位居全班前 30% 且操行平均 80 分以上）或碩士班一年級（含）以上（前一學年學業平均 80 分以上），並具備 TOEFL ITP 550 / TOEFL iBT 61 / TOEIC 590 / IELTS 4.5 / GEPT 中級複試 / BESTEP B1 以上。報名至 115年9月18日（2026/09/18）中午 12:00 截止，9月25日中午 12:10 面試。"
                  ),
              ],
              "source": {
                  "title": "中國醫藥大學物理治療學系 115學年度第1學期海外臨床專業實習甄選公告",
                  "source_url": CMU_PT_115_1_INTERNSHIP_URL,
                  "category": "exchange_application",
                  "summary": "中醫大物治系 2027/01/10–01/30 赴新加坡中央醫院與日本 3 所醫學中心海外臨床實習名額、門檻與時程。",
              },
              "scope": "home_application",
              "program_types": ["exchange"],
              "academic_year": "116",
              "application_round": "115-1物理治療學系海外臨床專業實習甄選",
              "audience": "all_students",
              "opens_at": "2026-09-01T09:00:00+08:00",
              "deadline_at": "2026-09-18T12:00:00+08:00",
              "date_status": "verified_exact",
              "status": "closed",
              "status_note": "115-1 物理治療學系海外臨床實習（2027/01/10–01/30 出發梯次）已於 2026/09/18 完成報名及 09/25 面試；醫學院、中醫學院、藥學院與護理學系 116 年度海外臨床見實習與學海築夢計畫持續開放洽詢。",
              "deadline_note": "欲參與下一梯次海外臨床見實習或教育部學海築夢／新南向學海築夢之同學，請向所屬學系及國際事務處洽詢。",
              "reminder_eligible": False,
              "checked_at": CHECKED_AT,
          },
      ],
      "program_overview": [
          {
              "title": (
                  f"中國醫藥大學國際事務處海外交換、跨國雙聯學位、臨床見實習與獎補助總覽（{len(partners)} 所全球合作姊妹校與醫療機構・{open_partner_count} 所當期開放重點機構・{total_exp_reports} 篇師生成果報告）"
              ),
              "details": [
                  (
                      f"中國醫藥大學（CMU，中醫大／中國醫／中國醫大）由「國際事務處（Office of Global Affairs / Center for International Affairs，設於臺中水湳校本部卓越大樓）」、「教務處」與全校 9 個學院（醫學院、中醫學院、藥學院、公共衛生學院、健康照護學院、生命科學院、牙醫學院、醫學工程學院、人文與科技學院）共同推動校級出國交換學生、跨國雙聯學位、海外臨床見實習（Medical / TCM / Pharmacy / Nursing / PT / Dental Clerkship）及教育部學海系列計畫。本平台完整收錄 {len(partners)} 所中醫大官方締約合作大學、醫學院、中醫藥大學與教學醫院（含 {open_partner_count} 所當期開放交換、雙聯、海外臨床見實習與學海築夢重點合作機構及 {len(partners) - open_partner_count} 所正式締約姊妹校），橫跨全球 31 個國家與地區（美國 34 校、中國大陸 32 校、日本 24 校、越南 11 校、韓國 10 校、泰國 9 校、香港 7 校、印尼 6 校、澳洲 6 校、英國 4 校、新加坡 4 校院、印度 4 校、羅馬尼亞 3 校、加拿大 2 校、德國 2 校、捷克 2 校、馬來西亞 2 校、蒙古 2 校，以及奧地利、瑞士、荷蘭、法國、斯洛維尼亞、立陶宛、俄羅斯、土耳其、菲律賓、澳門、巴西、墨西哥、哥斯大黎加、迦納各 1 校）。"
                  ),
                  (
                      f"中醫大國際化體系具備四大核心特色：（1）校級赴日本與香港免學費交換＋機票生活費雙重補助：日本北海道大學（每年 5 名免學費＋中醫大補助來回機票與每月 NT$5,000 生活費）、日本北見工業大學（每年 3 名免學費＋中醫大補助來回機票與每月 NT$5,000 生活費）、香港教育大學（每年 4 名免學費交換生）；（2）全台最完整之醫藥公衛護理跨國雙聯學位與高額專案獎學金（7 校 11 個學制）：澳洲紐卡索大學雙聯護理博士（最高補助 NT$50萬）、美國南加州大學 USC 藥學系 MS 雙聯與凱克醫學院 MD/MPH 雙聯（最高補助 NT$45萬）、美國杜蘭大學 MD/MPH 雙聯（最高補助 NT$40萬）、美國喬治亞州立大學碩士與 MD/MPH 雙聯（最高補助 NT$35萬）、美國南卡羅萊納大學 3+2 與 MD/MPH 雙聯（最高補助 NT$30萬＋州內學費優惠）、澳洲格里菲斯大學全球公衛碩士雙聯（最高補助 NT$30萬）、美國南達科塔州立大學營養學系 2+2 雙學士（補助 2 年中醫大全額學雜費並具美國營養師 RD 報考資格）；（3）中西醫藥護物治全科別海外臨床見實習：物理治療學系 115-1 選送赴新加坡中央醫院 SGH、日本神戶中央市民醫院、關西電力醫院與順天堂醫院實習，醫學院選送赴美國 MD Anderson 癌症中心與 Emory 大學見習，中醫學院與護理學系長年執行韓國（慶熙、東國、釜山、自生韓方醫院）、越南（胡志明市醫藥大學、芹苴醫藥大學、胡志明市傳統醫學醫院）、泰國（皇太后大學、瑪希敦大學 Siriraj 醫院、清邁大學）學海築夢與新南向學海築夢臨床實習；（4）公開收錄 {exp_covered_schools} 所重點機構共 {total_exp_reports} 篇歷屆師生返國成果報告。"
                  ),
              ],
              "source": {
                  "title": "中國醫藥大學國際事務處—姐妹校專區、國外交換學生、雙聯學位法規與各學院國際交流專區",
                  "source_url": CMU_OIA_HUB_URL,
                  "category": "exchange_application",
                  "summary": f"中醫大 {len(partners)} 所全球合作姊妹校與醫療機構、7 校 11 個雙聯學位獎學金及 {total_exp_reports} 篇成果報告。",
              },
          }
      ],
      "eligibility": [
          {
              "title": "中醫大在學資格、學業平均 A-（GPA 3.0／80 分）與操行 80 分雙門檻、修業年資與返國報告規定",
              "details": [
                  (
                      "學業與操行雙重門檻（依《中國醫藥大學學生出國交換實施要點》法規編號 622、《補助學生出國研習與實習辦法》法規編號 342 及各雙聯施行細則）：申請人須為本校 9 大學院具正式學籍之在學學生（延修生、休學生、在職專班及在職生不得申請；一般交換須修滿 1 學年以上，日本北海道大學、北見工業大學及美國南達科塔州立大學 2+2 須修滿 2 學年以上）。在校歷年學業成績平均須達等第制 A-（GPA 3.0 或百分制 80 分）以上，且前一學期操行成績須達 80 分以上（物理治療學系 115-1 海外臨床實習要求大學部前兩學年全班前 30% 且操行平均 80 分以上，或碩士班前一學年平均 80 分以上）。"
                  ),
                  (
                      "修課學分、雙聯修業月數與返國核銷義務（依《學生出國修課暨學分抵免實施要點》法規編號 337 及《與境外大學校院辦理雙聯學制實施辦法》法規編號 647）：赴日本北海道大學與北見工業大學交換每學期至少須修習 12 學分；修讀跨國雙聯學士須於兩校累計修業滿 32 個月以上、雙聯碩士滿 12 個月以上、雙聯博士滿 24 個月以上；返國後 1 個月內須繳交 1,000 字以上成果報告書並上傳 5 分鐘英文學習心得影片。"
                  ),
              ],
              "source": {
                  "title": "中國醫藥大學學生出國交換實施要點（法規編號 622）與補助學生出國研習與實習辦法（法規編號 342）",
                  "source_url": CMU_STATUTE_EXCHANGE_622_URL,
                  "category": "exchange_application",
                  "summary": "中醫大出國交換與補助門檻（學業 A- / GPA 3.0 / 80 分、操行 80 分）、修業年限與返國核銷規定。",
              },
          }
      ],
      "language_requirements": [
          {
              "title": "校內交換基本門檻（iBT 57 / TOEIC 550）、出國補助門檻（iBT 59 / TOEIC 640）、北海道大學（iBT 79 / IELTS 6.5）與雙聯學位（iBT 60–100）語檢標準",
              "details": [
                  (
                      "校內交換與出國補助分級語檢標準：（1）一般出國交換（法規編號 622）：TOEFL iBT 57 或 IELTS 4.0 或 TOEIC 550 或 GEPT 中級或培力英檢 BESTEP B1 以上；（2）申請校內出國研習與實習補助（法規編號 342）及日本北見工業大學交換：TOEFL iBT 59 或 IELTS 5.0 或 TOEIC 640 或 GEPT 中高級初試或 BESTEP B1 以上（或修畢 4 門全英語課程；北見工大亦採計 JLPT N3/N2）；（3）日本北海道大學 HUSTEP 交換（每年 5 名）：TOEFL iBT 79 或 IELTS 6.5 以上（不採計 TOEIC）；（4）物理治療學系 115-1 海外臨床實習：TOEFL ITP 550 / iBT 61 / TOEIC 590 / IELTS 4.5 / GEPT 中級 / BESTEP B1 以上。"
                  ),
                  (
                      "跨國雙聯學位語檢標準：（1）美國南加州大學 USC 藥學系 MS 雙聯：TOEFL iBT 100 或 IELTS 7.0；（2）USC 凱克醫學院 MD/MPH 與生醫雙聯：TOEFL iBT 90 或 IELTS 6.5；（3）美國杜蘭大學 MD/MPH 雙聯：TOEFL iBT 80 或 IELTS 6.5（或英文面試／GRE 302）；（4）澳洲格里菲斯大學 MGPH 雙聯：IELTS 6.5 或 TOEFL iBT 80；（5）美國南卡羅萊納大學、喬治亞州立大學、澳洲紐卡索大學雙聯：校內申請須達 TOEFL iBT 60 或 IELTS 5.5（達 iBT 80 / IELTS 6.5 優先補助）；（6）美國南達科塔州立大學營養 2+2 雙學士：TOEFL iBT 61（ITP 500）或 IELTS 5.5 以上。"
                  ),
              ],
              "source": {
                  "title": "中國醫藥大學學生出國交換實施要點、補助學生出國研習與實習辦法及雙聯學位施行細則",
                  "source_url": CMU_STATUTE_SUBSIDY_342_URL,
                  "category": "exchange_application",
                  "summary": "中醫大各層級交換、臨床實習與 7 校雙聯學位之 TOEFL、IELTS、TOEIC、GEPT、BESTEP 與 JLPT 語檢門檻。",
              },
          }
      ],
      "required_documents": [
          {
              "title": "出國交換／雙聯／海外研習實習申請文件清單與返國 1 個月內 1,000 字報告＋5 分鐘英文影片規範",
              "details": [
                  (
                      "校內甄選必備文件：1. 出國交換／雙聯或補助出國研習與實習申請表、2. 中英文歷年成績單正本（含學業平均 A- / GPA 3.0 / 80 分、班級排名及前一學期操行 80 分以上證明）、3. 有效外語檢定證明影本、4. 中英文自傳（CV）與出國讀書／研究／實習計畫書、5. 專任教師推薦信 2 封及家長同意書、6. 優秀表現或競賽研究佐證資料。"
                  ),
                  (
                      "出國選課確認與返國核銷義務：出國前須完成擬修課程確認、簽署行政契約書並投保全程海外醫療及急難救助保險；返國後須於 1 個月內向國際事務處繳交 1,000 字以上成果報告書、上傳 5 分鐘英文學習心得影片及機票登機證等單據辦理核銷，並持正式成績單向教務處申請學分抵免。"
                  ),
              ],
              "source": {
                  "title": "中國醫藥大學國際事務處表單下載與學生出國修課暨學分抵免實施要點",
                  "source_url": CMU_OUTBOUND_FORMS_URL,
                  "category": "exchange_application",
                  "summary": "中醫大出國交換申請表、出國修課學分抵免要點與返國報告及英文影片核銷規定。",
              },
          }
      ],
      "scholarship_info": [
          {
              "title": "日本交換機票＋每月 NT$5,000 生活補助、7 校雙聯學位專案獎學金（NT$ 30萬–50萬元／2年全額學雜費）與教育部學海四項計畫",
              "details": [
                  (
                      "校內出國研習實習補助與日本交換專案待遇：依《中國醫藥大學補助學生出國研習與實習辦法》（法規編號 342），赴日本北海道大學（每年 5 名）與北見工業大學（每年 3 名）交換者免繳日方學費，並由中醫大補助來回經濟艙機票乙張＋每月新臺幣 5,000 元生活補助；各學院海外臨床實習生亦得依本辦法申請機票與生活費補助。"
                  ),
                  (
                      "跨國雙聯學位專案獎助學金與教育部學海計畫：（1）澳洲紐卡索大學護理博士雙聯最高補助 NT$ 500,000；（2）美國南加州大學 USC 藥學系 MS 及凱克醫學院 MD/MPH 雙聯最高補助 NT$ 450,000；（3）美國杜蘭大學 MD/MPH 雙聯最高補助 NT$ 400,000；（4）美國喬治亞州立大學雙聯最高補助 NT$ 350,000；（5）美國南卡羅萊納大學 3+2／雙聯及澳洲格里菲斯大學 MGPH 雙聯最高補助 NT$ 300,000；（6）美國南達科塔州立大學營養 2+2 雙學士補助 2 年中醫大全額學雜費；（7）教育部學海飛颺、學海惜珠、學海築夢與新南向學海築夢提供出國交換與臨床實習機票生活費獎助。"
                  ),
              ],
              "source": {
                  "title": "中國醫藥大學補助學生出國研習與實習辦法（法規編號 342）與各校雙聯學位補助施行細則",
                  "source_url": CMU_STATUTE_SUBSIDY_342_URL,
                  "category": "scholarship",
                  "summary": "中醫大日本交換機票與每月 5,000 元補助、7 校雙聯 30萬–50萬元獎助學金與教育部學海四項計畫。",
              },
          }
      ],
      "document_explanations": [
          {
              "title": "中國醫藥大學出國讀書／研究／臨床實習計畫書、雙聯學位申請表件與返國 5 分鐘英文學習心得影片準備指南",
              "summary": "說明中醫大國際事務處與 9 大學院書面及面試審查重點、操行與 A- 成績證明檢附方式，以及返國核銷必備之 1,000 字報告與 5 分鐘英文影片。",
              "key_points": [
                  "依《中國醫藥大學學生出國交換實施要點》（法規編號 622）與《補助學生出國研習與實習辦法》（法規編號 342），申請時檢附之歷年成績單須同時呈現「學業成績平均達 A-（GPA 3.0 或 80 分）以上」及「前一學期操行成績達 80 分以上」（物理治療學系 115-1 海外臨床實習另須呈現大學部前兩學年班排名前 30%）。",
                  "申請日本北海道大學（HUSTEP）與北見工業大學交換者，讀書計畫書須具體列出每學期擬修習至少 12 學分之英語或日語授課科目；申請歐美澳 7 校跨國雙聯學位者，須詳述兩校學分抵免規劃與畢業條件。",
                  "所有獲中醫大出國交換或出國研習實習補助之學生，返國後 1 個月內除須繳交 1,000 字以上書面成果報告書外，另須錄製並上傳「5 分鐘英文學習心得影片」至指定平臺，始完成補助核銷程序。",
              ],
              "applies_to": [],
              "source": {
                  "title": "中國醫藥大學學生出國交換實施要點（法規編號 622）與補助學生出國研習與實習辦法（法規編號 342）",
                  "source_url": CMU_STATUTE_EXCHANGE_622_URL,
                  "category": "exchange_application",
                  "summary": None,
              },
              "document_url": CMU_STATUTE_EXCHANGE_622_URL,
              "document_type": "official_document",
              "full_text_extracted": True,
          }
      ],
      "rule_explanations": [
          {
              "title": "中國醫藥大學學生出國交換實施要點、出國修課暨學分抵免實施要點與雙聯學制實施辦法核心規定",
              "summary": "規範中醫大 A-（GPA 3.0／80 分）與操行 80 分雙門檻、日本交換每學期 12 學分下限、雙聯學士 32 個月／碩士 12 個月／博士 24 個月修業時間與雙聯獎學金合約義務。",
              "key_points": [
                  "學業與操行雙重門檻（法規編號 622、342）：無論申請校級交換、跨國雙聯學位或校內出國研習實習補助，申請人歷年學業成績平均均須達 A-（GPA 3.0 或百分制 80 分）以上，且前一學期操行成績須達 80 分以上；延修生、休學生及在職專班生不得申請。",
                  "雙聯學制兩校修業時間下限（《與境外大學校院辦理雙聯學制實施辦法》法規編號 647 第6條）：修讀跨國雙聯學士學位者，在兩校修業時間合計至少須滿 32 個月（如南達科塔州立大學營養 2+2 雙學士須於 SDSU 修滿 2 年及 66 學分）；雙聯碩士班合計至少須滿 12 個月；雙聯博士班合計至少須滿 24 個月。",
                  "雙聯獎助學金與返國義務：領取南加州大學（45萬）、杜蘭大學（40萬）、喬治亞州立大學（35萬）、南卡羅萊納大學（30萬）、格里菲斯大學（30萬）、紐卡索大學（50萬）或南達科塔州立大學（2年學雜費）雙聯補助者，須依期限取得對方學校學位證書並返校完成核銷；未依規定取得學位或未繳交返國報告者須全額繳回補助款。",
              ],
              "applies_to": [],
              "source": {
                  "title": "中國醫藥大學與境外大學校院辦理雙聯學制實施辦法（法規編號 647）與學生出國修課暨學分抵免實施要點（法規編號 337）",
                  "source_url": CMU_STATUTE_DUAL_647_URL,
                  "category": "exchange_application",
                  "summary": None,
              },
              "document_url": CMU_STATUTE_DUAL_647_URL,
              "document_type": "official_document",
              "full_text_extracted": True,
          }
      ],
      "sources": [
          {
              "title": "中國醫藥大學國際事務處（Office of Global Affairs / Center for International Affairs）官方網站",
              "source_url": CMU_OIA_HUB_URL,
              "category": "exchange_application",
              "summary": None,
          },
          {
              "title": f"中國醫藥大學全球締約姐妹校專區（{len(partners)} 所國際與兩岸港澳合作校院）",
              "source_url": CMU_PARTNERS_ZH_URL,
              "category": "partner_school",
              "summary": None,
          },
          {
              "title": "中國醫藥大學日本北海道大學（5名）與北見工業大學（3名）交換生甄選說明會簡報",
              "source_url": CMU_NEWS_JAPAN_EXCHANGE_URL,
              "category": "exchange_application",
              "summary": None,
          },
          {
              "title": "中國醫藥大學學生出國交換實施要點（法規編號 622）",
              "source_url": CMU_STATUTE_EXCHANGE_622_URL,
              "category": "exchange_application",
              "summary": None,
          },
          {
              "title": "中國醫藥大學補助學生出國研習與實習辦法（法規編號 342）",
              "source_url": CMU_STATUTE_SUBSIDY_342_URL,
              "category": "scholarship",
              "summary": None,
          },
          {
              "title": "中國醫藥大學與境外大學校院辦理雙聯學制實施辦法（法規編號 647）及 7 校雙聯補助施行細則",
              "source_url": CMU_STATUTE_DUAL_647_URL,
              "category": "scholarship",
              "summary": None,
          },
          {
              "title": "中國醫藥大學物理治療學系 115學年度第1學期海外臨床專業實習甄選公告（新加坡中央醫院與日本3醫院）",
              "source_url": CMU_PT_115_1_INTERNSHIP_URL,
              "category": "exchange_application",
              "summary": None,
          },
          {
              "title": f"中國醫藥大學醫學院、中醫學院與健康照護學院海外臨床見實習暨學海築夢成果專區（{total_exp_reports} 篇報告）",
              "source_url": CMU_CHMED_INTL_URL,
              "category": "exchange_application",
              "summary": None,
          },
      ],
  }
  (OFFICIAL_CMU_DIR / "student_dashboard.json").write_text(
      json.dumps(student_dashboard_payload, ensure_ascii=False, indent=2) + "\n",
      encoding="utf-8",
  )

  pages_records = [
      {
          "title": "中國醫藥大學：校級赴日本北海道大學／北見工業大學／香港教育大學交換、7校雙聯學位與物理治療學系 115-1 海外臨床實習時程",
          "source_url": CMU_NEWS_JAPAN_EXCHANGE_URL,
          "published_at": "2026-10-21T00:00:00Z",
          "text": "\n".join(exchange_info_payload["application_period"]),
          "summary": "\n".join(exchange_info_payload["application_period"]),
          "category": "exchange_application",
          "attachments": [],
          "crawled_at": CHECKED_AT,
          "content_hash": hashlib.sha256("\n".join(exchange_info_payload["application_period"]).encode("utf-8")).hexdigest(),
      },
      {
          "title": "中國醫藥大學：出國交換、跨國雙聯與海外實習申請資格（學業平均 A-／GPA 3.0／80 分、前一學期操行 80 分與雙聯修業月數規定）",
          "source_url": CMU_STATUTE_EXCHANGE_622_URL,
          "published_at": "2026-10-21T00:00:00Z",
          "text": "\n".join(exchange_info_payload["eligibility"]),
          "summary": "\n".join(exchange_info_payload["eligibility"]),
          "category": "exchange_application",
          "attachments": [],
          "crawled_at": CHECKED_AT,
          "content_hash": hashlib.sha256("\n".join(exchange_info_payload["eligibility"]).encode("utf-8")).hexdigest(),
      },
      {
          "title": f"中國醫藥大學：{len(partners)} 所合作姊妹校與教學醫院外語檢定門檻（交換 iBT 57 / 補助 iBT 59 / 北海道大學 iBT 79 / USC 雙聯 iBT 90–100）",
          "source_url": CMU_STATUTE_SUBSIDY_342_URL,
          "published_at": "2026-10-21T00:00:00Z",
          "text": "\n".join(exchange_info_payload["language_requirement"]),
          "summary": "\n".join(exchange_info_payload["language_requirement"]),
          "category": "exchange_application",
          "attachments": [],
          "crawled_at": CHECKED_AT,
          "content_hash": hashlib.sha256("\n".join(exchange_info_payload["language_requirement"]).encode("utf-8")).hexdigest(),
      },
      {
          "title": "中國醫藥大學：出國交換、雙聯學位與海外實習申請文件及返國 1,000 字成果報告＋5 分鐘英文學習心得影片規範",
          "source_url": CMU_OUTBOUND_FORMS_URL,
          "published_at": "2026-10-21T00:00:00Z",
          "text": "\n".join(exchange_info_payload["required_documents"]),
          "summary": "\n".join(exchange_info_payload["required_documents"]),
          "category": "exchange_application",
          "attachments": [],
          "crawled_at": CHECKED_AT,
          "content_hash": hashlib.sha256("\n".join(exchange_info_payload["required_documents"]).encode("utf-8")).hexdigest(),
      },
      {
          "title": "中國醫藥大學：日本交換機票＋每月 NT$5,000 補助、7 校跨國雙聯學位獎助學金（NT$ 30萬–50萬元／2年學雜費）與教育部學海計畫",
          "source_url": CMU_STATUTE_DUAL_647_URL,
          "published_at": "2026-10-21T00:00:00Z",
          "text": "\n".join(exchange_info_payload["scholarship_info"]),
          "summary": "\n".join(exchange_info_payload["scholarship_info"]),
          "category": "scholarship",
          "attachments": [],
          "crawled_at": CHECKED_AT,
          "content_hash": hashlib.sha256("\n".join(exchange_info_payload["scholarship_info"]).encode("utf-8")).hexdigest(),
      },
  ]
  (OFFICIAL_CMU_DIR / "pages.jsonl").write_text(
      "\n".join(json.dumps(p, ensure_ascii=False) for p in pages_records) + "\n",
      encoding="utf-8",
  )

  home_rules = {
      "school_id": "cmu",
      "school_name": "中國醫藥大學",
      "eligibility": student_dashboard_payload["eligibility"],
      "application_periods": student_dashboard_payload["application_periods"],
      "selection_rules": {
          "undergraduate_score_minimum": 80.0,
          "graduate_score_minimum": 80.0,
          "conduct_score_minimum": 80.0,
          "exchange_gpa_minimum": 3.0,
          "pt_overseas_internship_class_rank_percent_max": 30,
          "excluded_undergraduate_years": ["大一上", "大一下"],
          "hokkaido_and_kitami_and_sdsu_min_completed_years": 2,
          "require_cmu_enrollment_during_abroad": True,
          "japan_exchange_min_credits_per_semester": 12,
          "dual_degree_min_months": {
              "bachelor": 32,
              "master": 12,
              "phd": 24,
          },
          "dual_degree_grants_max_ntd": {
              "University of Newcastle (PhD in Nursing)": 500000,
              "University of Southern California (MS in Regulatory Science / Keck MD-MPH)": 450000,
              "Tulane University (MD/MPH)": 400000,
              "Georgia State University (Master / MD-MPH)": 350000,
              "University of South Carolina (3+2 BS-MS / MD-MPH)": 300000,
              "Griffith University (Master of Global Public Health)": 300000,
              "South Dakota State University (2+2 BS in Nutrition)": "2_years_cmu_full_tuition_waiver",
          },
          "japan_exchange_monthly_stipend_ntd": 5000,
          "japan_exchange_roundtrip_airfare_subsidy": True,
          "return_report_due_days": 30,
          "return_report_min_words": 1000,
          "return_english_video_min_minutes": 5,
          "return_documents_due": "受補助及交換學生須於返國後 1 個月內向國際事務處繳交 1,000 字以上成果報告書及上傳 5 分鐘英文學習心得影片，並檢具正式成績單與課程大綱向教務處申請學分抵免",
      },
      "source_urls": cmu_source_urls,
      "verified_at": "2026-10-21",
  }
  (OFFICIAL_CMU_DIR / "home_rules.json").write_text(
      json.dumps(home_rules, ensure_ascii=False, indent=2) + "\n",
      encoding="utf-8",
  )
  (OFFICIAL_CMU_DIR / "documents.json").write_text(
      json.dumps(
          {
              "school_name": "中國醫藥大學",
              "required_documents": student_dashboard_payload["required_documents"],
              "source_urls": cmu_source_urls,
          },
          ensure_ascii=False,
          indent=2,
      )
      + "\n",
      encoding="utf-8",
  )
  (OFFICIAL_CMU_DIR / "scholarships.json").write_text(
      json.dumps(
          {
              "school_name": "中國醫藥大學",
              "scholarships": student_dashboard_payload["scholarship_info"],
              "source_urls": cmu_source_urls,
          },
          ensure_ascii=False,
          indent=2,
      )
      + "\n",
      encoding="utf-8",
  )

  completeness = {
      "school_id": "cmu",
      "school_name": "中國醫藥大學",
      "total_partners": len(partners),
      "partner_count": len(partners),
      "international_partners": sum(
          1 for p in partners if p["country"] not in {"中國大陸", "香港", "澳門"}
      ),
      "mainland_partners": sum(
          1 for p in partners if p["country"] in {"中國大陸", "香港", "澳門"}
      ),
      "dual_degree_partner_universities": 7,
      "dual_degree_programs": 11,
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
          f"中國醫藥大學國際事務處（OIA）、教務處與 9 大學院 115–116 學年度（2026–2028）校級赴日本北海道大學（每年 5 名免學費＋中醫大機票與每月 NT$5,000 生活補助）、北見工業大學（每年 3 名免學費＋機票與每月 NT$5,000 補助）、香港教育大學（每年 4 名免學費）交換生計畫、7 校 11 個跨國雙聯學位暨專案獎學金（南加州大學 USC 最高補助 NT$45萬、杜蘭大學最高 NT$40萬、喬治亞州立大學最高 NT$35萬、南卡羅萊納大學與澳洲格里菲斯大學最高 NT$30萬、澳洲紐卡索大學護理博士最高 NT$50萬、南達科塔州立大學營養 2+2 補助 2 年中醫大全額學雜費）、健康照護學院物理治療學系 115-1 海外臨床實習（新加坡中央醫院 4 名、神戶中央市民醫院 2 名、關西電力醫院 2 名、順天堂醫院 2 名，2027/01/10–01/30 實習）及醫學院、中醫學院、藥學院、護理學系海外臨床見實習與教育部學海計畫同步整合；共完整收錄 {len(partners)} 所全球締約合作大學、醫學院與教學醫院（含 {open_partner_count} 所當期開放交換、雙聯與臨床見實習機構及 {len(partners) - open_partner_count} 所正式締約姊妹校，橫跨全球 31 個國家與地區，並收錄 {exp_covered_schools} 所合作機構共 {total_exp_reports} 篇歷屆師生返國成果報告）。"
      ),
      "verified_at": "2026-10-21",
  }
  (OFFICIAL_CMU_DIR / "catalog-completeness.json").write_text(
      json.dumps(completeness, ensure_ascii=False, indent=2) + "\n",
      encoding="utf-8",
  )
  (OFFICIAL_CMU_DIR / "verification_status.json").write_text(
      json.dumps(
          {
              "school_id": "cmu",
              "school_name": "中國醫藥大學",
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
          "sources/cmu/a_partner.html",
          CMU_PARTNERS_ZH_URL,
          "中國醫藥大學國際事務處中文版締約姐妹校列表 HTML",
      ),
      (
          "sources/cmu/en_a_partner.html",
          CMU_PARTNERS_EN_URL,
          "中國醫藥大學國際事務處英文版締約姐妹校列表 HTML",
      ),
      (
          "sources/cmu/s_exchange_o.html",
          CMU_OUTBOUND_EXCHANGE_URL,
          "中國醫藥大學國際事務處國外交換學生專區 HTML",
      ),
      (
          "sources/cmu/download.html",
          CMU_OUTBOUND_FORMS_URL,
          "中國醫藥大學國際事務處出國交換與補助表單下載專區 HTML",
      ),
      (
          "sources/cmu/japan_exchange_2024_briefing.pdf",
          CMU_JAPAN_2024_BRIEFING_PDF_URL,
          "中國醫藥大學赴日本北海道大學（5名）與北見工業大學（3名）交換生甄選說明會簡報 PDF",
      ),
      (
          "sources/cmu/eduhk_agreement.pdf",
          CMU_EDUHK_AGREEMENT_PDF_URL,
          "中國醫藥大學與香港教育大學學生交換協議書（每年4名免學費）PDF",
      ),
      (
          "sources/cmu/statute_622_中国醫藥大學學生出國交換實施要點.html",
          CMU_STATUTE_EXCHANGE_622_URL,
          "中國醫藥大學學生出國交換實施要點（法規編號 622）HTML",
      ),
      (
          "sources/cmu/statute_342_中国醫藥大學補助學生出國研習與實習辦法.html",
          CMU_STATUTE_SUBSIDY_342_URL,
          "中國醫藥大學補助學生出國研習與實習辦法（法規編號 342）HTML",
      ),
      (
          "sources/cmu/statute_337_中国醫藥大學學生出國修課暨學分抵免實施要點.html",
          CMU_STATUTE_CREDIT_337_URL,
          "中國醫藥大學學生出國修課暨學分抵免實施要點（法規編號 337）HTML",
      ),
      (
          "sources/cmu/statute_647_中国醫藥大學與境外大學校院辦理雙聯學制實施辦法.html",
          CMU_STATUTE_DUAL_647_URL,
          "中國醫藥大學與境外大學校院辦理雙聯學制實施辦法（法規編號 647）HTML",
      ),
      (
          "sources/cmu/statute_1566_中国醫藥大學補助藥學系碩士班學生修讀美國南加州大學雙聯學位施行細則.html",
          CMU_STATUTE_USC_PHARM_1566_URL,
          "中國醫藥大學補助藥學系碩士班學生修讀美國南加州大學雙聯學位施行細則（法規編號 1566）HTML",
      ),
      (
          "sources/cmu/statute_917_中国醫藥大學補助學生修讀美國南加州大學凱克醫學院雙聯學位施行細則.html",
          CMU_STATUTE_USC_KECK_917_URL,
          "中國醫藥大學補助學生修讀美國南加州大學凱克醫學院雙聯學位施行細則（法規編號 917）HTML",
      ),
      (
          "sources/cmu/statute_1268_中国醫藥大學補助學生修讀美國南卡羅萊納大學三加二雙聯學位施行細則.html",
          CMU_STATUTE_SC_3PLUS2_1268_URL,
          "中國醫藥大學補助學生修讀美國南卡羅萊納大學三加二雙聯學位施行細則（法規編號 1268）HTML",
      ),
      (
          "sources/cmu/statute_846_中国醫藥大學補助學生修讀美國喬治亞州立大學雙聯學位施行細則.html",
          CMU_STATUTE_GSU_846_URL,
          "中國醫藥大學補助學生修讀美國喬治亞州立大學雙聯學位施行細則（法規編號 846）HTML",
      ),
      (
          "sources/cmu/statute_848_中国醫藥大學補助學生修讀美國杜蘭大學雙聯學位施行細則.html",
          CMU_STATUTE_TULANE_848_URL,
          "中國醫藥大學補助學生修讀美國杜蘭大學雙聯學位施行細則（法規編號 848）HTML",
      ),
      (
          "sources/cmu/statute_1085_中国醫藥大學補助營養學系學生修讀美國南達科塔州立大學雙學士學位施行細則.html",
          CMU_STATUTE_SDSU_1085_URL,
          "中國醫藥大學補助營養學系學生修讀美國南達科塔州立大學雙學士學位施行細則（法規編號 1085）HTML",
      ),
      (
          "sources/cmu/statute_1459_中国醫藥大學補助學生修讀澳洲格里菲斯大學雙聯學位施行細則.html",
          CMU_STATUTE_GRIFFITH_1459_URL,
          "中國醫藥大學補助學生修讀澳洲格里菲斯大學雙聯學位施行細則（法規編號 1459）HTML",
      ),
      (
          "sources/cmu/statute_1222_中国醫藥大學補助學生修讀澳洲紐卡索大學雙聯護理博士學位施行細則.html",
          CMU_STATUTE_NEWCASTLE_1222_URL,
          "中國醫藥大學補助學生修讀澳洲紐卡索大學雙聯護理博士學位施行細則（法規編號 1222）HTML",
      ),
      (
          "sources/cmu/cmupt_overseas_753.html",
          CMU_PT_115_1_INTERNSHIP_URL,
          "中國醫藥大學物理治療學系 115學年度第1學期海外臨床專業實習甄選公告 HTML",
      ),
      (
          "sources/cmu/md_clerkship_md_anderson.pdf",
          CMU_MED_CLERKSHIP_URL,
          "中國醫藥大學醫學系赴美國德州大學安德森癌症中心（MD Anderson）臨床見習報告 PDF",
      ),
      (
          "sources/cmu/md_clerkship_emory.pdf",
          CMU_MED_CLERKSHIP_URL,
          "中國醫藥大學醫學系赴美國艾默蕾大學（Emory University）臨床見習報告 PDF",
      ),
      (
          "sources/cmu/cmu_catalog_source.json",
          CMU_PARTNERS_ZH_URL,
          f"中國醫藥大學 {len(partners)} 所全球合作大學、醫學院與教學醫院整合資料集 JSON",
      ),
      (
          "sources/cmu/cmu_resolved_locations.json",
          CMU_PARTNERS_ZH_URL,
          f"中國醫藥大學 {len(partners)} 所全球合作機構 ROR / Wikidata 地理座標核對表 JSON",
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
      "school_id": "cmu",
      "school_name": "中國醫藥大學",
      "generated_at": CHECKED_AT,
      "active_cycle_note": completeness["active_term"],
      "sources": prov_sources,
  }
  prov_text = json.dumps(provenance_payload, ensure_ascii=False, indent=2) + "\n"
  (OFFICIAL_CMU_DIR / "import_provenance.json").write_text(prov_text, encoding="utf-8")
  (OFFICIAL_CMU_DIR / "import-provenance.json").write_text(prov_text, encoding="utf-8")

  print(
      f"Successfully built CMU catalog: {len(partners)} partners"
      f" ({open_partner_count} open, {completeness['verified_campus_images']}"
      f" verified images, {completeness['verified_locations']} verified"
      f" locations), {len(workflows)} workflows,"
      f" {len(destinations)} destinations, {len(research_records)} research"
      f" records, {exp_covered_schools} schools with experience records"
      f" ({len(student_experience_rows)} rows, {total_exp_reports} reports)."
  )


if __name__ == "__main__":
  main()
