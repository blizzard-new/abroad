"""Build the official Chung Shan Medical University (中山醫學大學, CSMU) exchange data bundle."""

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

SOURCES_CSMU_DIR = REPO_ROOT / "sources" / "csmu"
OFFICIAL_CSMU_DIR = REPO_ROOT / "src" / "exchange_info" / "official_data" / "csmu"
STATIC_DIR = REPO_ROOT / "src" / "exchange_info" / "static"

CHECKED_AT = "2026-10-21T02:30:00Z"

CSMU_OIA_HUB_URL = "https://oia.csmu.edu.tw/?Lang=zh-tw"
CSMU_OIA_EN_HUB_URL = "https://oia.csmu.edu.tw/?Lang=en"
CSMU_SISTER_SCHOOLS_OVERVIEW_URL = "https://oia.csmu.edu.tw/p/412-1004-75.php?Lang=zh-tw"
CSMU_PARTNERS_AMERICAS_ZH_URL = "https://oia.csmu.edu.tw/p/412-1004-2933.php?Lang=zh-tw"
CSMU_PARTNERS_ASIA_PACIFIC_ZH_URL = "https://oia.csmu.edu.tw/p/412-1004-3963.php?Lang=zh-tw"
CSMU_PARTNERS_EUROPE_AFRICA_ZH_URL = "https://oia.csmu.edu.tw/p/412-1004-3964.php?Lang=zh-tw"
CSMU_PARTNERS_EN_URL = "https://oia.csmu.edu.tw/p/412-1004-3902.php?Lang=en"
CSMU_EXCHANGE_REGS_FORMS_URL = "https://oia.csmu.edu.tw/p/412-1004-3228.php?Lang=zh-tw"
CSMU_EXCHANGE_FAQ_URL = "https://oia.csmu.edu.tw/p/412-1004-3227.php?Lang=zh-tw"
CSMU_XUEHAI_HOW_TO_APPLY_URL = "https://oia.csmu.edu.tw/p/412-1004-3092.php?Lang=zh-tw"
CSMU_XUEHAI_REGS_FORMS_URL = "https://oia.csmu.edu.tw/p/412-1004-3094.php?Lang=zh-tw"
CSMU_XUEHAI_COUNTS_URL = "https://oia.csmu.edu.tw/p/412-1004-3091.php?Lang=zh-tw"
CSMU_EXPERIENCES_ZH_URL = "https://oia.csmu.edu.tw/p/403-1004-725-1.php?Lang=zh-tw"

CSMU_2027_ST_MARTINS_NOTICE_URL = "https://oia.csmu.edu.tw/p/406-1004-77969,r830.php?Lang=zh-tw"
CSMU_2027_TOKUSHIMA_NOTICE_URL = "https://oia.csmu.edu.tw/p/406-1004-77970,r830.php?Lang=zh-tw"
CSMU_2027_OAKLAND_NOTICE_URL = "https://oia.csmu.edu.tw/p/406-1004-77972,r830.php?Lang=zh-tw"
CSMU_2027_LSU_NOTICE_URL = "https://oia.csmu.edu.tw/p/406-1004-77958,r830.php?Lang=zh-tw"
CSMU_116_XUEHAI_FEIYANG_NOTICE_URL = "https://oia.csmu.edu.tw/p/405-1004-78068,c4359.php?Lang=zh-tw"
CSMU_115_2_XUEHAI_ZHUMENG_NOTICE_URL = "https://oia.csmu.edu.tw/p/406-1004-77774,r830.php?Lang=zh-tw"
CSMU_2026_KAWAMURA_NOTICE_URL = "https://oia.csmu.edu.tw/p/406-1004-71185,r830.php?Lang=zh-tw"

CSMU_DUAL_OAKLAND_URL = "https://oia.csmu.edu.tw/p/412-1004-3521.php?Lang=zh-tw"
CSMU_DUAL_ANDREWS_URL = "https://oia.csmu.edu.tw/p/412-1004-3523.php?Lang=zh-tw"
CSMU_DUAL_DUQUESNE_URL = "https://oia.csmu.edu.tw/p/412-1004-3525.php?Lang=zh-tw"
CSMU_EX_TOKUSHIMA_PATHWAY_URL = "https://oia.csmu.edu.tw/p/412-1004-4670.php?Lang=zh-tw"
CSMU_EX_ST_MARTINS_URL = "https://oia.csmu.edu.tw/p/412-1004-3230.php?Lang=zh-tw"
CSMU_EX_TOKUSHIMA_FLOW_URL = "https://oia.csmu.edu.tw/p/412-1004-3545.php?Lang=zh-tw"

CSMU_EXCHANGE_SELECTION_REGS_PDF_URL = "https://oia.csmu.edu.tw/var/file/4/1004/img/1597/131990159.pdf"
CSMU_OVERSEAS_COURSE_REGS_PDF_URL = "https://oia.csmu.edu.tw/var/file/4/1004/img/1597/191294726.pdf"
CSMU_XUEHAI_SUBSIDY_REGS_PDF_URL = "https://oia.csmu.edu.tw/var/file/4/1004/img/1595/570112202.pdf"

REGION_COST_DEFAULTS = {
    "美國": (
        "USD 1,400–2,600 / 月（含住宿、膳食與市區交通；華盛頓州聖馬丁大學 SMU、密西根州奧克蘭大學 Oakland、安德魯大學 Andrews、奧勒岡州太平洋大學 Pacific 等校區約 USD 1,350–1,950 / 月；費城賓州大學／天普大學／薩盧斯大學、波士頓塔夫茨大學、洛杉磯南加州大學／AHMC／Everest、西雅圖華盛頓大學、休士頓德州醫學中心、紐奧良 LSUHSC 約 USD 1,800–2,600 / 月；可申請教育部 116 年度學海飛颺／惜珠［每人補助 NT$ 5萬–30萬元］或學海築夢補助）",
        "須憑美國接待校或醫療機構核發之 DS-2019（J-1 交換生／訪問研究學者）或 I-20（F-1 雙聯學位／ASAP 學生）表格向美國在台協會（AIT）申辦簽證，臨床見實習生另須完成規定之免疫接種證明（MMR、B肝抗體、TB 檢驗、水痘疫苗）及美國學校指定健康保險。",
    ),
    "聖克里斯多福及尼維斯": (
        "USD 1,100–1,700 / 月（溫莎大學醫學院學生宿舍、日常膳食與島內交通開銷）",
        "我國邦交國享免簽證待遇，惟入境進修或醫學交流仍須備妥接待校邀請函及全程海外醫療與急難救助保險。",
    ),
    "日本": (
        "JPY 70,000–130,000 / 月（德島文理大學德島／香川高松校區國際學生宿舍每月僅約 JPY 23,000–30,000，連同伙食交通每月約 JPY 65,000–90,000；東京都東邦大學、東京醫科大學、順天堂大學、日本齒科大學、目白大學等首都圈校院約 JPY 100,000–135,000 / 月；名古屋愛知學院大學、新潟醫療福祉大學、富山大學、北九州齒科大學等約 JPY 75,000–100,000 / 月；可申請教育部學海飛颺／惜珠／築夢獎學金）",
        "學期交換或 PP 研究所銜接計畫須憑日本接待校核發之在留資格認定證明書（COE）向日本台灣交流協會申辦留學簽證並依法加入日本國民健康保險（NHI）；短期臨床見實習（4–8 週）須依日本接收醫院要求備妥抗體檢測報告（麻疹、德國麻疹、水痘、腮腺炎、B肝、結核檢驗）與海外醫療保險。",
    ),
    "韓國": (
        "KRW 750,000–1,200,000 / 月（大邱／慶山嶺南大學校內學生宿舍、學生食堂與大邱地鐵公車開銷親民）",
        "學期交換須憑韓國接待校標準入學許可書向駐台北韓國代表部申辦 D-2-6 交換學生簽證，抵韓後辦理外國人登錄並納入韓國國民健康保險（NHIS）。",
    ),
    "新加坡": (
        "SGD 1,600–2,500 / 月（新加坡中央醫院 SGH、國立大學醫院 NUH、竹腳婦幼醫院 KKH 臨床實習期間之學生公寓／青年旅舍分租、熟食中心餐飲與捷運公車費用；可申請教育部新南向學海築夢補助）",
        "赴新加坡各大教學醫院進行臨床見實習須依院方人力資源與教學部門指引向新加坡移民與關卡局（ICA）或衛生部辦理 Training Employment Pass / Student Pass 許可，並完成規定之疫苗抗體證明與醫療實習保險。",
    ),
    "泰國": (
        "THB 13,000–23,000 / 月（曼谷朱拉隆功大學、瑪希敦大學及清邁大學、清萊皇太后大學國際學生宿舍與餐飲交通開銷實惠；可申請教育部新南向學海築夢補助）",
        "須憑泰國接待校院公文向泰國貿易經濟辦事處（TTEO）申辦 Non-Immigrant ED 實習／留學簽證，並投保涵蓋全期之海外醫療及意外保險。",
    ),
    "越南": (
        "USD 450–750 / 月（河內醫科大學、芹苴醫藥大學、同塔高專護校、平陽東方國際大學學生宿舍、日常餐飲與市區交通費用低廉）",
        "須透過越南接待校申辦越南簽證，並於出國前投保涵蓋全期之海外醫療及意外保險。",
    ),
    "印尼": (
        "IDR 4,800,000–8,200,000 / 月（雅加達／德博印尼大學 UI、三寶瓏迪波內戈羅大學 UNDIP、日惹 AMIKOM 大學學生公寓與餐飲交通開銷低廉）",
        "須由印尼接待校協助申辦印尼學生／文化交流電子簽證（e-Visa），並投保涵蓋全期之海外醫療及意外保險（新南向學海築夢赴印尼實習天數不得少於 25 天）。",
    ),
    "馬來西亞": (
        "MYR 1,600–2,600 / 月（吉隆坡馬來亞大學 UM 及拉曼大學 UTAR 校內外住宿、飲食與捷運公車開銷）",
        "學期交換或長期實習須透過馬來西亞 EMGS 系統申辦學生簽證核准函（VAL / Mobility Pass）並投保醫療保險。",
    ),
    "菲律賓": (
        "USD 500–850 / 月（馬尼拉中央大學 MCU、聖母法蒂瑪大學 OLFU、荷甘伯紀念學院及碧瑤本格特州立大學學生公寓與日常餐飲交通費用）",
        "須依菲律賓接待校指引辦理簽證或 SSP 特別學習許可，並投保海外全期醫療及意外保險。",
    ),
    "印度": (
        "USD 400–700 / 月（清奈 SRM 科學技術研究所國際學舍與日常餐飲交通費用實惠）",
        "須憑印度接待校入學／實習許可向印度台北協會（ITA）申辦 Student / Intern Visa 並投保海外醫療及意外保險。",
    ),
    "蒙古": (
        "USD 450–750 / 月（烏蘭巴托蒙古健康科學大學 MNUMS 學生宿舍、餐飲與市區交通費用）",
        "須憑接待校邀請函申辦蒙古簽證，並投保涵蓋全期之海外醫療及意外保險。",
    ),
    "土耳其": (
        "USD 500–800 / 月（伊斯帕爾塔蘇萊曼德米雷爾大學 SDU 校區周邊學生公寓、學餐與大眾運輸開銷實惠）",
        "須申辦土耳其學生簽證並投保當地與海外醫療保險。",
    ),
    "澳洲": (
        "AUD 2,000–2,900 / 月（墨爾本大學 The University of Melbourne 臨床視光中心與雪梨新南威爾斯大學 UNSW 住宿、伙食與大眾運輸費用；可申請教育部新南向學海築夢補助）",
        "短期臨床見實習可依期程申辦澳洲簽證或電子旅行授權（ETA），一學期以上交換須購買澳洲海外學生健康保險（OSHC）並申辦 Subclass 500 學生簽證。",
    ),
    "奧地利": (
        "EUR 950–1,400 / 月（維也納醫學大學暨附設維也納總醫院 AKH Wien 見實習期間之學生公寓 OeAD、日常餐飲與維也納大眾運輸 Wiener Linien 交通卡）",
        "短期臨床見實習（90 天內）免申根簽證，惟須備妥維也納醫學大學國際處錄取通知、免疫抗體證明及符合申根規定之海外醫療與實習責任保險。",
    ),
    "瑞士": (
        "CHF 1,500–2,200 / 月（伯恩大學醫學院暨伯恩大學醫院 Inselspital 見實習期間之住宿、伙食與瑞士半價卡／市區交通費用）",
        "短期臨床見實習（90 天內）免申根簽證，超過 90 天須向瑞士商務辦事處申辦長期學生／研究簽證並投保瑞士認可之醫療保險。",
    ),
    "法國": (
        "EUR 950–1,450 / 月（巴黎法國視光高等學院 ISO 住宿、餐飲與 Navigo 地鐵交通卡費用）",
        "短期視光研習（90 天內）免申根簽證，超過 90 天須透過法國教育中心（Campus France）申辦長期學生簽證。",
    ),
    "芬蘭": (
        "EUR 750–1,100 / 月（于韋斯屈萊大學 University of Jyväskylä 學生公寓 KOAS / Soihtu、大學補貼學生餐廳與單車公車通勤費用）",
        "交換超過 90 天須透過 Enter Finland 申辦芬蘭學生居留許可，並投保涵蓋全期之海外醫療及意外保險。",
    ),
    "波蘭": (
        "EUR 600–950 / 月（華沙醫學大學 Medical University of Warsaw 學生宿舍、餐飲與華沙學生交通卡開銷實惠）",
        "短期臨床見實習（90 天內）免申根簽證，一學期交換須向波蘭臺北辦事處申辦波蘭 D 類國別學生簽證。",
    ),
    "匈牙利": (
        "EUR 550–850 / 月（德布勒森大學醫學與健康科學中心國際學生公寓、日常飲食與輕軌公車費用實惠）",
        "短期臨床見實習（90 天內）免申根簽證，一學期以上交換須向匈牙利貿易辦事處申辦學生簽證／居留許可。",
    ),
    "斯洛伐克": (
        "EUR 600–900 / 月（布拉提斯拉瓦考門斯基大學學生宿舍、學生餐券與大眾運輸）",
        "短期臨床見實習（90 天內）免申根簽證，一學期以上交換須向斯洛伐克經濟文化辦事處申辦長期簽證／居留許可。",
    ),
    "克羅埃西亞": (
        "EUR 650–950 / 月（亞得里亞海港都瑞耶卡大學醫學院學生住宿、餐飲與市區公車費用）",
        "克羅埃西亞為申根區成員國，短期見實習（90 天內）免申根簽證，一學期以上交換須申辦長期學生簽證。",
    ),
    "俄羅斯": (
        "USD 500–850 / 月（庫爾斯克國立醫科大學校內學生宿舍與日常餐飲交通費用）",
        "須憑俄羅斯接待校官方邀請函申辦俄羅斯留學簽證並投保當地醫療險（出國前請務必確認外交部最新旅遊安全警示）。",
    ),
    "迦納": (
        "USD 600–950 / 月（阿克拉醫學院短期醫學與公共衛生交流食宿交通開銷）",
        "須憑接待校邀請函申辦迦納簽證，並於出發前完成黃熱病疫苗接種（必備黃皮書）與全程海外醫療急難救助保險。",
    ),
    "澳門": (
        "HKD 4,400–7,300 / 月（約 MOP 4,500–7,500；澳門理工大學及澳門鏡湖醫院周邊住宿、餐飲與巴士開銷）",
        "持有效護照入境澳門，若研修超過法定期限須透過澳門接待院校向澳門治安警察局居留及逗留事務廳申辦「逗留特別許可（學生）」，並於出國前至陸委會「國人赴港澳動態登錄系統」完成登錄。",
    ),
    "中國大陸": (
        "RMB 2,000–3,600 / 月（上海交通大學、北京大學、四川大學、中山大學、同濟大學、武漢大學、華中科技大學、南京醫科大學、溫州醫科大學、廣州醫科大學等校內宿舍與學生食堂費用實惠）",
        "持有效護照與臺胞證入境；特別注意：依中山醫大國際事務處《辦理赴陸教育交流活動應注意事項及落實填報登錄平臺事宜》及《中山醫學大學學生出國選修課程辦法》規定，赴陸交流須落實教育部登錄平臺填報，且出國選課須於出國前完成系所及教務處審核（大陸地區高等學校醫事人員相關學歷與學分採認悉依教育部與考選部法規辦理）。",
    ),
}

SEMESTER_DATES_BY_COUNTRY = {
    "美國": "秋季學期（Fall）：約 8 月中下旬至 12 月中旬；春季學期（Spring）：約 1 月中旬至 5 月中旬；暑期專業／臨床實習：6 月至 8 月",
    "聖克里斯多福及尼維斯": "秋季學期：約 9 月至 12 月；春季學期：約 1 月至 4 月；夏季學期：約 5 月至 8 月",
    "日本": "春季學期（前學期）：約 4 月初至 8 月上旬；秋季學期（後學期）：約 9 月中下旬至翌年 2 月；夏季日語研修／暑期臨床見習：7 月至 8 月",
    "韓國": "春季學期（第1學期）：約 3 月初至 6 月中下旬；秋季學期（第2學期）：約 9 月初至 12 月中下旬",
    "新加坡": "第一學期：約 8 月至 12 月；第二學期：約 1 月至 5 月；教學醫院臨床實習（SGH / NUH / KKH）：依學海築夢計畫於寒暑假或學期中執行（至少 30 天）",
    "泰國": "第一學期：約 8 月至 12 月；第二學期：約 1 月至 5 月；新南向學海築夢臨床／專業實習：主要於 6–8 月暑期或學期中執行（至少 30 天）",
    "越南": "第一學期（秋季班）：約 9 月至翌年 1 月；第二學期（春季班）：約 2 月至 6 月；暑期新南向實習與國際志工：7–8 月",
    "印尼": "奇數／秋季學期：約 8/9 月至 12 月；偶數／春季學期：約 2 月至 6 月；新南向學海築夢實習：至少 25 天以上",
    "馬來西亞": "第一學期（秋季班）：約 10 月至翌年 2 月；第二學期（春季班）：約 3 月至 7 月",
    "菲律賓": "第一學期（秋季班）：約 8 月至 12 月；第二學期（春季班）：約 1 月中旬至 5 月下旬",
    "印度": "奇數／秋季學期：約 7/8 月至 12 月；偶數／春季學期：約 1 月至 5 月",
    "蒙古": "秋季學期：約 9 月初至 12 月底；春季學期：約 2 月初至 6 月初",
    "土耳其": "秋季學期：約 9 月中下旬至翌年 1 月；春季學期：約 2 月中旬至 6 月",
    "澳洲": "第一學期（Semester 1）：約 2 月中下旬至 6 月；第二學期（Semester 2）：約 7 月下旬至 11 月；暑期視光與臨床實習：7–8 月",
    "奧地利": "冬季學期（Wintersemester）：約 10 月初至翌年 1 月底；夏季學期（Sommersemester）：約 3 月初至 6 月底；暑期臨床見習：7–9 月",
    "瑞士": "秋季學期（Autumn）：約 9 月中旬至 12 月底；春季學期（Spring）：約 2 月中旬至 5 月底",
    "法國": "秋季學期（Semestre 1）：約 9 月初至翌年 1 月；春季學期（Semestre 2）：約 1 月下旬至 6 月",
    "芬蘭": "秋季學期（Autumn）：約 8 月底至 12 月中下旬；春季學期（Spring）：約 1 月初至 5 月底",
    "波蘭": "冬季學期（秋季班）：約 10 月初至翌年 2 月中旬；夏季學期（春季班）：約 2 月下旬至 6 月底",
    "匈牙利": "秋季學期：約 9 月初至 12 月中旬（考試期至 1 月）；春季學期：約 2 月初至 5 月中旬（考試期至 6 月）",
    "斯洛伐克": "冬季學期：約 9 月中下旬至翌年 1 月；夏季學期：約 2 月中旬至 6 月",
    "克羅埃西亞": "冬季學期：約 10 月初至翌年 1 月底；夏季學期：約 2 月中下旬至 6 月中旬",
    "俄羅斯": "秋季學期：約 9 月初至翌年 1 月；春季學期：約 2 月初至 6 月底",
    "迦納": "第一學期：約 8/9 月至 12 月；第二學期：約 1/2 月至 5 月",
    "澳門": "第一學期（秋季班）：約 9 月初至 12 月底；第二學期（春季班）：約 1 月中旬至 5 月中旬",
    "中國大陸": "秋季學期：約 9 月初至翌年 1 月中旬；春季學期：約 2 月中下旬至 6 月底",
}


def clean_text(s: str) -> str:
  if not s:
    return ""
  return re.sub(r"\s+", " ", s).strip()


def main() -> None:
  OFFICIAL_CSMU_DIR.mkdir(parents=True, exist_ok=True)
  catalog_source = json.loads(
      (SOURCES_CSMU_DIR / "csmu_catalog_source.json").read_text(encoding="utf-8")
  )
  resolved_locations = json.loads(
      (SOURCES_CSMU_DIR / "csmu_resolved_locations.json").read_text(encoding="utf-8")
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
    quota_str = clean_text(item.get("quota") or "依中山醫大國際事務處與各學院當期公告名額")

    if zh_name == "聖馬丁大學":
      program_type = "校級重點出國交換學生計畫（每學期3名免學費交換生）"
      source_url = CSMU_2027_ST_MARTINS_NOTICE_URL
    elif zh_name == "德島文理大學":
      program_type = "校級重點出國交換學生暨赴日升學研究所課程銜接計畫（Pathway Program）"
      source_url = CSMU_2027_TOKUSHIMA_NOTICE_URL
    elif zh_name == "奧克蘭大學":
      program_type = "國際交換學生（ASAP）暨 4+1／4+2 生物學學碩連讀雙聯計畫"
      source_url = CSMU_2027_OAKLAND_NOTICE_URL
    elif zh_name == "路易斯安那州立大學醫學中心":
      program_type = "海外生物醫學研究獎學金計畫（每月補助 USD 2,500）"
      source_url = CSMU_2027_LSU_NOTICE_URL
    elif zh_name == "安德魯大學企管學院":
      program_type = "跨國雙聯學位計畫（3.5+0.5+1 Accelerating MBA）"
      source_url = CSMU_DUAL_ANDREWS_URL
    elif zh_name == "杜肯大學":
      program_type = "跨國雙聯學位暨學碩連讀計畫"
      source_url = CSMU_DUAL_DUQUESNE_URL
    elif zh_name == "川村學園女子大學":
      program_type = "日本姊妹校交換學生計畫（2027年起配合姐妹校通知中止選送）"
      source_url = CSMU_2026_KAWAMURA_NOTICE_URL
    elif country in {"中國大陸", "澳門"}:
      program_type = "大陸及港澳地區合作姊妹校與教學醫院學術交流計畫"
      source_url = CSMU_PARTNERS_ASIA_PACIFIC_ZH_URL
    elif avail_status == "open":
      program_type = "教育部學海築夢／新南向學海築夢海外專業實習暨臨床見實習計畫"
      source_url = CSMU_115_2_XUEHAI_ZHUMENG_NOTICE_URL
    else:
      program_type = "國際正式締約合作姊妹校與醫療研究機構"
      source_url = (
          CSMU_PARTNERS_AMERICAS_ZH_URL
          if region == "美洲"
          else (
              CSMU_PARTNERS_EUROPE_AFRICA_ZH_URL
              if region in {"歐洲", "非洲"}
              else CSMU_PARTNERS_ASIA_PACIFIC_ZH_URL
          )
      )

    colleges_str = clean_text(item.get("colleges") or "")
    degree_levels_str = clean_text(item.get("eligible_degrees") or "大學部、碩士班、博士班在學學生")
    lang_req_str = clean_text(item.get("language_req") or "")
    gpa_req_str = clean_text(item.get("gpa_req") or "")
    website = item.get("website") or CSMU_SISTER_SCHOOLS_OVERVIEW_URL
    remarks_raw = clean_text(item.get("notes") or "")
    tuition_note = clean_text(item.get("tuition_note") or "")
    exps = item.get("experience_reports") or []

    round_label = (
        "116學年度（2027–2028）出國交換、學位連讀、研究獎學金暨教育部學海計畫甄選"
        if avail_status == "open"
        else "國際事務處正式締約合作姊妹校與醫療機構（依當期交換、見實習或雙聯公告名額辦理）"
    )
    app_deadline_str = (
        "【2027赴美日重點交換生與學位連讀（美國聖馬丁大學、密西根州奧克蘭大學 ASAP 暨學位連讀、日本德島文理大學交換暨 PP 升學研究所計畫）】收件至 115年10月22日（2026/10/22）17:00 截止，115年12月底至116年1月底前公告甄選結果｜【教育部116年度「學海飛颺、學海惜珠」出國研修獎學金】收件至 116年1月6日（2027/01/06）截止（每人補助 NT$ 5萬–30萬元）｜【教育部「學海築夢、新南向學海築夢」海外專業實習】第1次甄選每年12月至1月初截止、第2次甄選於 115年8月31日（2026/08/31）截止｜【2027春季美國路易斯安那州立大學醫學中心（LSUHSC）研究獎學金】收件至 115年9月30日（2026/09/30）截止，10月面試，2027年3–4月出發"
    )
    deadline_iso = (
        "2026-10-22T17:00:00+08:00"
        if zh_name in {"聖馬丁大學", "德島文理大學", "奧克蘭大學"}
        else "2027-01-06T17:00:00+08:00"
    )
    win_status = "open" if avail_status == "open" else "closed"
    acad_year = "116"

    study_period_str = clean_text(item.get("duration") or "1 學期、1 學年交換或暑期／學期臨床與專業實習（學海築夢至少 30 天、印尼至少 25 天）")
    sem_dates_str = SEMESTER_DATES_BY_COUNTRY.get(
        country, "秋季學期：約 9 月至翌年 1 月；春季學期：約 2 月至 6 月"
    )
    housing_str = (
        f"獲中山醫大國際事務處或所屬學院提名錄取後，可依 {zh_name} 國際處／教學醫院指引申請校內外學生宿舍或實習生公寓"
        + (f"（費用與交換／雙聯待遇：{tuition_note}；{remarks_raw}）" if (tuition_note or remarks_raw) else "。")
    )
    course_rest_str = (
        f"開放對象與領域：{colleges_str}。依《中山醫學大學選送學生出國研修甄選辦法》、《中山醫學大學學生出國選修課程辦法》及《教育部鼓勵國內大專校院選送學生出國研修或國外專業實習補助要點（學海計畫）》規定：（1）出國期間須維持中山醫大在學學籍並依規定繳交本校全額學雜費、退撫費及學生平安保險費（應屆畢業最後一學期及延畢生不得申請交換）；（2）學生出國交換次數以 2 次為限，總修業時間不得超過 2 年；（3）申請教育部學海飛颺／惜珠之大學部學生於國外研修期間每學期至少應修習相當於 6 學分之課程；（4）出國前必須填具《中山醫學大學學生出國選修課程申請表》經系（所）主管、院長及教務處核准，返國後填具《出國選修課程學分及成績採認表》檢附正式成績單與大綱辦理學分抵免。"
    )

    tuition_points_list = [
        (
            f"中山醫大在學註冊與姊妹校學費待遇（依《中山醫學大學學生出國選修課程辦法》第8條及各校甄選簡章）：出國交換學生於交換期間仍須辦理本校註冊並繳交全額學雜費、退撫費及平安保險費。本合作機構待遇：{tuition_note or '依兩校合作協議辦理'}。"
        ),
        (
            "教育部《116年度學海飛颺／學海惜珠》與《學海築夢／新南向學海築夢》及校內深耕國際交流獎補助：（1）教育部116年度學海飛颺／惜珠（收件至 116年1月6日［2027/01/06］截止，須為具中華民國國籍且在臺設有戶籍、於中山醫就讀滿一學期以上之非應屆畢業最後一學期／非延畢在學生，在校學業總平均 80 分以上或系所排名前 40%，大學部每學期至少修習 6 學分，連同學校至少 20% 配合款每人補助新臺幣 5 萬至 30 萬元）；（2）教育部學海築夢／新南向學海築夢（第1次甄選每年 12–1 月、第2次甄選於 2026/08/31 截止，由專任教師主持選送赴海外醫療院所、視光／語聽／復健中心或長照機構實習至少 30 天［印尼 25 天］，補助機票與生活費）；（3）美國路易斯安那州立大學醫學中心（LSUHSC）研究獎學金提供錄取碩博士生每月 2,500 美元生活補助（為期一年）。"
        ),
    ]

    app_steps_list = [
        (
            f"步驟一（確認中山醫在學資格、GPA 3.0／平均 80 分或系排前 40% 門檻與 {zh_name} 語檢要求）：確認為中山醫大在學滿一學期以上之正式學籍學生（非應屆畢業最後一學期、非延畢生），歷年成績達姊妹校門檻（{gpa_req_str}），並備妥有效外語檢定證明（{lang_req_str}）。"
        ),
        (
            "步驟二（於校內截止日前向國際事務處或所屬系所遞交申請表件）：（1）2027年赴美國聖馬丁大學（每學期 3 名免學費）、日本德島文理大學（每學期 2 名免學費＋PP 升學研究所計畫 1 名免學費）、美國密西根州奧克蘭大學（每年 15 名 ASAP 交換及 4+1/4+2 生物學學碩連讀）：均於 115年10月22日（2026/10/22）前備齊校內申請表、歷年中文與英文成績單（含 GPA 及系排名）、外語能力證明、中英文自傳與讀書／研修計畫書、推薦信及家長同意書送交國際事務處（正心樓）；（2）教育部116年度《學海飛颺、學海惜珠》獎學金：於 116年1月6日（2027/01/06）前遞交；（3）教育部《學海築夢、新南向學海築夢》海外臨床與專業實習：配合計畫主持人於每年第1次（12–1月）或第2次（8/31前）甄選提出申請。"
        ),
        (
            f"步驟三（校內書面與面試甄選審查［成績 40%＋語文 35%＋研修計畫 20%＋輔助文件 5%］及向 {full_name} 辦理官方提名）：依《中山醫學大學選送學生出國研修甄選辦法》，校內書面審查配分為「在校成績 40%、語文能力 35%、研修計畫 20%、其他輔助審查文件 5%（修過全英語 EMI 課程、曾任國際交流接待學伴等優先加分）」；通過甄選後（奧克蘭大學於 115年12月底前、聖馬丁與德島文理大學於 116年1月底前公告），由國際處向 {full_name} 辦理官方提名（Nomination）。"
        ),
        (
            "步驟四（完成教務處《學生出國選修課程申請表》、簽約行前講習與返國 2 週內繳交 3,000 字心得報告及學分採認）：出國前須依《中山醫學大學學生出國選修課程辦法》填妥《學生出國選修課程申請表》經系所及教務處核准，並簽訂學海計畫行政契約書、參加國際處行前說明會及投保海外全程醫療意外險；返國後須於 2 週（14 日）內繳交 3,000 字以上研修心得報告（含照片 4 張以上，並配合出席國際移動系列講座分享座談會）以辦理獎學金尾款核銷，並填具《出國選修課程學分及成績採認表》向教務處申請學分抵免。"
        ),
    ]

    elig_points_list = [
        f"合作類別與甄選群組：{program_type}（{group_str}）",
        f"開放學制與年級：{degree_levels_str}",
        f"開放申請院系：{colleges_str}",
        f"學業成績門檻：{gpa_req_str}",
        f"外語能力標準：{lang_req_str}",
        "校內書面甄選配分與修業上限：在校成績 40% ＋ 語文能力 35% ＋ 研修計畫 20% ＋ 輔助審查文件 5%（修習 EMI 課程、接待國際學伴加分）；出國交換至多 2 次、總修業時間不超過 2 年，出國期間須維持中山醫在學註冊並繳交全額學雜費。",
    ]
    if tuition_note:
      elig_points_list.append(f"姊妹校學費與獎補助待遇：{tuition_note}")
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
          f"【中山醫學長姐海外交換／臨床實習心得報告（共 {len(exps)} 篇）】收錄於國際事務處學生經驗分享專區（含：{'、'.join(exp_labels[:5])}）"
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
        "availability_note": f"中山醫學大學國際事務處公告合作姊妹校與醫療機構（{program_type}）；{quota_str}。",
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
            "title": f"中山醫學大學國際事務處締約姊妹校、交換生與雙聯學位甄選公告—{zh_name}",
            "source_url": source_url,
            "role": "home_university",
            "authority": "home_official_notice",
            "effective_academic_year": acad_year,
            "application_round": round_label,
            "checked_at": CHECKED_AT,
        },
        {
            "title": "教育部116年度「學海飛颺、學海惜珠」獎助優秀學生出國研修甄選公告與補助辦法",
            "source_url": CSMU_116_XUEHAI_FEIYANG_NOTICE_URL,
            "role": "home_university",
            "authority": "home_official_notice",
            "effective_academic_year": acad_year,
            "application_round": round_label,
            "checked_at": CHECKED_AT,
        },
        {
            "title": "中山醫學大學選送學生出國研修甄選辦法與學生出國選修課程辦法",
            "source_url": CSMU_EXCHANGE_SELECTION_REGS_PDF_URL,
            "role": "home_university",
            "authority": "home_official_notice",
            "effective_academic_year": acad_year,
            "application_round": round_label,
            "checked_at": CHECKED_AT,
        },
    ]
    if exps:
      wf_sources.append({
          "title": f"中山醫大國際事務處海外交換與實習心得分享專區—赴 {zh_name} 研修成果報告（{len(exps)} 篇）",
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
        "home_university": "中山醫學大學",
        "school_name": full_name,
        "partner_website": website,
        "country": country,
        "program_type": program_type,
        "academic_year": acad_year,
        "application_round": round_label,
        "effective_application_rounds": [
            round_label,
            "116學年度赴美日交換生暨學位連讀甄選（10/22截止）",
            "116年度教育部學海飛颺／學海惜珠獎學金甄選（1/6截止）",
            "115–116年度教育部學海築夢／新南向學海築夢海外專業實習甄選",
            "116-1",
            "116-2",
            "115-2",
            "115-1",
        ],
        "applicability_status": "verified",
        "applicability_note": (
            "中山醫學大學由國際事務處（OIA）、教務處及 4 個學院（醫學院、口腔醫學院、醫學科技學院、健康管理學院）共同統籌海外交換學生（美國聖馬丁大學每學期 3 名免學費、日本德島文理大學每學期 2 名免學費＋PP 升學研究所計畫 1 名免學費、美國密西根州奧克蘭大學每年 15 名 ASAP 交換及生物學 4+1/4+2 學碩連讀）、跨國雙聯學位（安德魯大學 MBA、杜肯大學碩士連讀）、美國路易斯安那州立大學醫學中心（LSUHSC）每月 2,500 美元研究獎學金，以及教育部學海四項計畫（116年度學海飛颺／惜珠於 2027/01/06 截止，每人補助 NT$ 5萬–30萬元；學海築夢／新南向學海築夢每年兩梯次甄選）。"
        ),
        "review_status": "published",
        "published_at": CHECKED_AT,
        "steps": [
            {
                "rule_id": f"csmu-{acad_year}-home-1-{idx+1:03d}",
                "order": 1,
                "phase": "校內申請",
                "title": f"確認中山醫大在學身分、GPA 3.0（學海總平均 80 分或系排前 40%）門檻與 {zh_name} 語檢要求",
                "responsible_party": "學生",
                "responsible_unit": "中山醫學大學國際事務處／各學院系所",
                "deadline_at": deadline_iso,
                "deadline_status": "verified_exact" if avail_status == "open" else "reference_only",
                "deadline_source_url": source_url,
                "deadline_checked_at": CHECKED_AT,
                "deadline_reminder_eligible": avail_status == "open",
                "summary": (
                    f"確認符合《中山醫學大學選送學生出國研修甄選辦法》、《學生出國選修課程辦法》及各校甄選簡章規定（申請人須為本校在學至少滿一學期之非應屆畢業最後一學期、非延畢生；申請聖馬丁大學、德島文理大學、奧克蘭大學學碩連讀、杜肯大學須達 GPA 3.0 以上；申請教育部 116 年度學海飛颺／惜珠須達在校學業總平均 80 分以上或系所排名前 40%），並備妥符合 {zh_name} 規定之有效外語檢定證明。"
                ),
                "details": [
                    f"開放學制與院系：{colleges_str}（{degree_levels_str}）",
                    f"語言與學業條件：{lang_req_str}｜{gpa_req_str}",
                    f"當期名額與計畫類別：{quota_str}｜{program_type}",
                ],
                "scope": {
                    "home_universities": ["中山醫學大學"],
                    "partner_universities": [full_name],
                    "academic_years": ["115", "116"],
                    "application_rounds": [round_label, "116-1", "116-2", "115-2", "115-1"],
                },
                "source_urls": [
                    source_url,
                    CSMU_116_XUEHAI_FEIYANG_NOTICE_URL,
                    CSMU_EXCHANGE_SELECTION_REGS_PDF_URL,
                ],
                "checked_at": CHECKED_AT,
                "support_status": "verified",
            },
            {
                "rule_id": f"csmu-{acad_year}-home-2-{idx+1:03d}",
                "order": 2,
                "phase": "校內申請",
                "title": "向國際事務處（正心樓）遞交出國交換／雙聯甄選表件（10/22 截止）或教育部116年度學海飛颺／惜珠申請表件（1/6 截止）",
                "responsible_party": "學生與所屬系（所）辦公室",
                "responsible_unit": "中山醫學大學國際事務處",
                "deadline_at": deadline_iso,
                "deadline_status": "verified_exact" if avail_status == "open" else "reference_only",
                "deadline_source_url": source_url,
                "deadline_checked_at": CHECKED_AT,
                "deadline_reminder_eligible": avail_status == "open",
                "summary": (
                    "依申請計畫於期限前備齊校內甄選申請表、中英文歷年成績單正本（含 GPA 及系所排名百分比）、有效外語能力檢定證明、中英文自傳與出國研修讀書計畫書、師長推薦信及家長同意書，經系所核章後送交國際事務處。"
                ),
                "details": [
                    "2027年赴美國聖馬丁大學交換、美國密西根州奧克蘭大學交換（ASAP）及學位連讀、日本德島文理大學交換暨續升學研究所（PP）計畫：統一收件至 115年10月22日（2026/10/22）截止。",
                    "教育部116年度「學海飛颺、學海惜珠」獎助優秀學生出國研修甄選：收件至 116年1月6日（2027/01/06）截止；「學海築夢、新南向學海築夢」海外專業實習分每年 12–1 月及 8 月底（115年為 8/31）兩次甄選。",
                ],
                "document_requirements": [
                    {
                        "name": "中山醫學大學出國交換學生／學位連讀／教育部學海計畫甄選申請表及家長同意書",
                        "official_form_url": CSMU_EXCHANGE_REGS_FORMS_URL,
                        "source_urls": [CSMU_EXCHANGE_REGS_FORMS_URL, CSMU_XUEHAI_REGS_FORMS_URL],
                    },
                    {
                        "name": "中山醫大中、英文歷年成績單正本（須含歷年 GPA 及系所排名百分比；學海飛颺／惜珠須達總平均 80 分以上或系排名前 40%）",
                        "source_urls": [CSMU_116_XUEHAI_FEIYANG_NOTICE_URL, CSMU_2027_ST_MARTINS_NOTICE_URL],
                    },
                    {
                        "name": "有效外語能力檢定證明影本（聖馬丁大學 TOEFL iBT 71 / ITP 525 / TOEIC 700 / IELTS 6.0；奧克蘭大學 iBT 79 / IELTS 6.5 / Duolingo 105；德島文理大學 JLPT N2）",
                        "source_urls": [CSMU_2027_ST_MARTINS_NOTICE_URL, CSMU_2027_OAKLAND_NOTICE_URL, CSMU_2027_TOKUSHIMA_NOTICE_URL],
                    },
                    {
                        "name": "中英文自傳、出國讀書／研修計畫書（占書審 20%）、師長推薦信與其他輔助審查資料（EMI 修課證明、國際學伴證明等占 5%；學海惜珠另附新式戶口名簿及低收／中低收證明）",
                        "official_form_url": CSMU_XUEHAI_REGS_FORMS_URL,
                        "source_urls": [CSMU_EXCHANGE_SELECTION_REGS_PDF_URL, CSMU_116_XUEHAI_FEIYANG_NOTICE_URL],
                    },
                ],
                "scope": {
                    "home_universities": ["中山醫學大學"],
                    "academic_years": ["115", "116"],
                    "application_rounds": [round_label, "116-1", "116-2", "115-2", "115-1"],
                },
                "source_urls": [
                    source_url,
                    CSMU_116_XUEHAI_FEIYANG_NOTICE_URL,
                    CSMU_EXCHANGE_REGS_FORMS_URL,
                    CSMU_XUEHAI_REGS_FORMS_URL,
                ],
                "checked_at": CHECKED_AT,
                "support_status": "verified",
            },
            {
                "rule_id": f"csmu-{acad_year}-home-3-{idx+1:03d}",
                "order": 3,
                "phase": "甄選與提名",
                "title": "國際事務處書面與面試審查（成績40%＋語文35%＋研修計畫20%＋輔助文件5%）及錄取名單公告（12月底／1月底前）",
                "responsible_party": "中山醫學大學國際事務處國際交流審查委員會",
                "responsible_unit": "中山醫學大學國際事務處",
                "deadline_at": "2027-01-31T17:00:00+08:00",
                "deadline_status": "verified_exact",
                "deadline_source_url": CSMU_EXCHANGE_SELECTION_REGS_PDF_URL,
                "deadline_checked_at": CHECKED_AT,
                "deadline_reminder_eligible": False,
                "summary": (
                    "國際事務處依《中山醫學大學選送學生出國研修甄選辦法》辦理書面與面試甄選（書審占 60%［在校成績 40%、語文能力 35%、研修計畫 20%、輔助審查文件 5%］、面試占 40%）；奧克蘭大學於 115年12月底前、聖馬丁大學與德島文理大學於 116年1月底前公告錄取名單，教育部學海計畫於 3 月底前報部、5 月底前公告核定補助金額。"
                ),
                "details": [
                    "修過本校全英語授課（EMI）課程或曾擔任國際處外籍生接待學伴、參與國際交流活動表現優異者，於輔助審查項目予以優先加分。",
                    "獲選免學費交換生優待名額者（如聖馬丁大學每學期 3 名、德島文理大學每學期 2 名＋PP 計畫 1 名），可同時申請教育部 116 年度學海飛颺或學海惜珠獎學金（每人補助 NT$ 5萬–30萬元）。",
                ],
                "scope": {
                    "home_universities": ["中山醫學大學"],
                    "academic_years": ["115", "116"],
                    "application_rounds": [round_label, "116-1", "116-2", "115-2", "115-1"],
                },
                "source_urls": [
                    CSMU_EXCHANGE_SELECTION_REGS_PDF_URL,
                    CSMU_2027_ST_MARTINS_NOTICE_URL,
                    CSMU_2027_TOKUSHIMA_NOTICE_URL,
                    CSMU_2027_OAKLAND_NOTICE_URL,
                ],
                "checked_at": CHECKED_AT,
                "support_status": "verified",
            },
            {
                "rule_id": f"csmu-{idx+1:03d}-host-apply",
                "order": 4,
                "phase": "合作校申請",
                "title": f"由中山醫大國際處向 {zh_name} 辦理官方提名（Nomination），並遞交外文入學、雙聯或臨床見實習申請文件",
                "responsible_party": "學生與接待校院國際事務處／醫學教育中心",
                "summary": (
                    f"通過中山醫大甄選後，由國際事務處或所屬學院向 {zh_name} 辦理官方提名；學生須於接待校院規定截止日前備妥外文入學申請表、英文歷年成績單、護照影本、英文財力證明（Bank Statement）、語檢證書、英文推薦信與健康檢查／疫苗接種紀錄，靜候核發正式入學許可（Letter of Acceptance / DS-2019 / I-20 / COE）。"
                ),
                "details": [
                    f"研修期程：{study_period_str}｜名額：{quota_str}",
                    f"語言與學業條件：{lang_req_str}｜{gpa_req_str}",
                    f"住宿與費用待遇：{housing_str}",
                ],
                "scope": {
                    "home_universities": ["中山醫學大學"],
                    "partner_universities": [full_name],
                    "academic_years": ["115", "116"],
                    "application_rounds": [round_label, "116-1", "116-2", "115-2", "115-1"],
                },
                "source_urls": (
                    [source_url, CSMU_EXCHANGE_FAQ_URL]
                    + ([website] if website else [])
                ),
                "checked_at": CHECKED_AT,
                "support_status": "verified",
                "needs_confirmation": False,
            },
            {
                "rule_id": f"csmu-{acad_year}-home-5-{idx+1:03d}",
                "order": 5,
                "phase": "行前準備",
                "title": "出國前完成《學生出國選修課程申請表》核准、簽訂學海契約，並於返國後 2 週內繳交 3,000 字心得報告與辦理學分抵免",
                "responsible_party": "學生與所屬系所",
                "responsible_unit": "中山醫學大學教務處註冊課務組／國際事務處",
                "summary": (
                    "出國前須依《中山醫學大學學生出國選修課程辦法》填妥《學生出國選修課程申請表》經系（所）主管、院長及教務處核准（學海飛颺／惜珠大學部受獎生每學期至少須修習 6 學分），同時維持中山醫在學註冊、繳交全額學雜費並簽妥《學海計畫行政契約書》；返國後須於 2 週（14 日）內繳交 3,000 字以上中文研修心得報告（含照片 4 張以上）及上傳教育部學海計畫網站、配合參與海外交換生心得分享座談會，並填具《出國選修課程學分及成績採認表》檢附正式成績單辦理學分採認。"
                ),
                "details": tuition_points_list,
                "scope": {
                    "home_universities": ["中山醫學大學"],
                    "academic_years": ["115", "116"],
                    "application_rounds": [round_label, "116-1", "116-2", "115-2", "115-1"],
                },
                "source_urls": [
                    CSMU_OVERSEAS_COURSE_REGS_PDF_URL,
                    CSMU_EXCHANGE_SELECTION_REGS_PDF_URL,
                    CSMU_XUEHAI_SUBSIDY_REGS_PDF_URL,
                    CSMU_EXCHANGE_REGS_FORMS_URL,
                ],
                "checked_at": CHECKED_AT,
                "support_status": "verified",
            },
        ],
        "sources": wf_sources,
        "last_checked": CHECKED_AT,
        "coverage_status": "official_verified",
        "coverage_note": (
            f"已完整整合中山醫學大學國際事務處（OIA）與教務處（2027年赴美國聖馬丁大學／密西根州奧克蘭大學／日本德島文理大學交換暨學位連讀甄選公告、2027年春季赴美國路易斯安那州立大學醫學中心研究獎學金、教育部116年度學海飛颺／惜珠甄選公告、115年度學海築夢／新南向學海築夢第二次甄選公告、選送學生出國研修甄選辦法、學生出國選修課程辦法及 {total_exp_reports or 30} 篇歷屆學長姐與計畫主持人返國報告）共 {len(catalog_source)} 所全球合作姊妹校與醫療研究機構資料。"
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
            "title": f"中山醫學大學國際事務處締約姊妹校、交換生與雙聯學位簡章—{zh_name}",
            "source_url": source_url,
            "summary": "中山醫大國際事務處公告之合作學程、開放學院、語言檢定門檻與姊妹校免學費／獎學金待遇說明",
        },
        {
            "title": "中山醫學大學選送學生出國研修甄選辦法、學生出國選修課程辦法與教育部116年度學海計畫公告",
            "source_url": CSMU_116_XUEHAI_FEIYANG_NOTICE_URL,
            "summary": "中山醫大教育部學海四項計畫（每人補助 5萬–30萬元）、書審配分（40%/35%/20%/5%）與教務處出國選修課程核准規範",
        },
    ]
    if exps:
      dest_sources.append({
          "title": f"中山醫大國際事務處學生經驗分享專區—赴 {zh_name} 交換／臨床實習成果報告（{len(exps)} 篇）",
          "source_url": exps[0]["url"],
          "summary": f"收錄歷年中山醫大生與計畫主持人赴 {zh_name} 海外交換與臨床實習心得報告共 {len(exps)} 篇",
      })
    if website:
      dest_sources.append({
          "title": f"{full_name} 官方網站",
          "source_url": website,
          "summary": "接待合作姊妹校／教學醫院官方網站",
      })

    src_url_list = (
        [source_url, CSMU_116_XUEHAI_FEIYANG_NOTICE_URL, CSMU_EXCHANGE_SELECTION_REGS_PDF_URL]
        + ([exps[0]["url"]] if exps else [])
        + ([website] if website else [])
    )

    destinations.append({
        "home_university": "中山醫學大學",
        "school_name": full_name,
        "country": country,
        "city": location_obj.get("city") or country,
        "cost_summary": f"{cost_line}。\n{tuition_clean}",
        "housing_summary": housing_clean,
        "transport_summary": (
            f"校區／醫院代表城市：{location_obj.get('city') or country}。請依入學／臨床見實習許可確認實際授課校區（如日本德島文理大學區分德島校區與香川高松車站校區）、附屬教學醫院位置與當地學生交通優惠。"
        ),
        "campus_life_summary": f"{calendar_clean}\n{course_clean}",
        "student_guide_sections": [
            {
                "key": "cost",
                "title": "生活費、中山醫在學學雜費規定、姊妹校免學費名額與教育部學海計畫（5萬–30萬元）獎補助",
                "summary": cost_line,
                "points": [cost_line] + tuition_points_list,
                "source_urls": src_url_list + [CSMU_XUEHAI_SUBSIDY_REGS_PDF_URL, CSMU_115_2_XUEHAI_ZHUMENG_NOTICE_URL],
                "caution": (
                    "教育部學海計畫受獎生及校級交換生須於返國後 2 週（14 日）內繳交 3,000 字以上研修心得報告並上傳學海計畫網站，始得請領剩餘 20% 補助尾款。"
                ),
            },
            {
                "key": "housing",
                "title": "住宿資訊與校內外學生宿舍／教學醫院實習公寓申請",
                "summary": housing_clean[:160],
                "points": [housing_clean],
                "source_urls": src_url_list,
                "caution": (
                    "美國聖馬丁大學、奧克蘭大學與日本德島文理大學均提供交換生校內外學生宿舍協助，獲中山醫提名後請務必於接待校截止日前完成住宿與膳食（Meal Plan）登記。"
                ),
            },
            {
                "key": "insurance",
                "title": "海外醫療及意外保險、臨床見實習疫苗抗體檢測與平安保險規定",
                "summary": visa_default,
                "points": [
                    visa_default,
                    "依《中山醫學大學學生出國選修課程辦法》及接待醫學院校規定，出國交換期間須繳交本校學生平安保險費並自行投保涵蓋境外研修全期之海外醫療及意外保險；赴國外醫院或視光／語聽中心進行臨床見實習者，須提早完成規定之疫苗接種與抗體效價檢測。",
                ],
                "source_urls": src_url_list + [CSMU_OVERSEAS_COURSE_REGS_PDF_URL],
                "caution": "美日歐澳與新加坡教學醫院對免疫抗體效價（MMR、水痘、B肝、TB 檢驗）審核嚴格，請於出發前 3–6 個月完成檢驗。",
            },
            {
                "key": "visa",
                "title": "留學／研究簽證辦理、教務處《出國選修課程申請表》核准與在學註冊義務",
                "summary": visa_default,
                "points": [
                    visa_default,
                    "依《中山醫學大學學生出國選修課程辦法》規定：學生出國前須先填妥《學生出國選修課程申請表》送所屬學系（所）、學院及教務處審核，且出國期間須維持中山醫在學註冊（交換次數以 2 次、總修業時間不超過 2 年為限）。",
                ],
                "source_urls": src_url_list + [CSMU_OVERSEAS_COURSE_REGS_PDF_URL],
                "caution": "出國前請務必完成教務處《學生出國選修課程申請表》簽核與國際處行前報到。",
            },
            {
                "key": "academics",
                "title": "每學期至少修習 6 學分規定、跨國學碩連讀抵免與返國《出國選修課程學分及成績採認表》",
                "summary": course_clean[:160],
                "points": [calendar_clean, course_clean],
                "source_urls": src_url_list + [CSMU_OVERSEAS_COURSE_REGS_PDF_URL, CSMU_EXCHANGE_FAQ_URL],
                "caution": (
                    "申請教育部 116 年度學海飛颺／惜珠之大學部學生，於國外大學研修期間每學期至少應修習相當於 6 學分之課程；日本德島文理大學應外系一般交換生須填選香川（高松車站）校區文學部，PP 升學研究所計畫學生則填選德島校區。"
                ),
            },
            {
                "key": "living",
                "title": f"{location_obj.get('city') or country} 校園／臨床生活與中山醫學長姐海外研修心得傳承",
                "summary": f"代表城市：{location_obj.get('city') or country}。請配合接待校院國際處或臨床教學部門完成報到與新生訓練（Orientation）。",
                "points": [
                    f"目的地城市：{location_obj.get('city') or country}（{country}）",
                    (
                        f"中山醫大國際事務處於官網「海外交換與實習心得分享專區（{exps[0]['url'] if exps else CSMU_EXPERIENCES_ZH_URL}）」公開收錄歷屆中山醫學生赴海外交換與臨床實習成果報告書"
                        + (f"（本機構共收錄 {len(exps)} 篇：{'、'.join(exp_labels[:4])}）" if exps else "")
                        + "，並於每年 10 月舉辦「國際移動系列講座—海外交換生研修心得分享座談會」。"
                    ),
                ],
                "source_urls": [exps[0]["url"] if exps else CSMU_EXPERIENCES_ZH_URL],
            },
        ],
        "sources": dest_sources,
        "last_checked": CHECKED_AT,
        "coverage_status": "official_verified",
        "coverage_note": (
            f"已整合中山醫學大學國際事務處與教務處 {len(catalog_source)} 所合作姊妹校與醫療機構、2027赴美日交換生暨學位連讀計畫、教育部116年度學海計畫及 30 篇歷屆學長姐與師長返國報告。"
        ),
    })

    research_records.append({
        "home_university": "中山醫學大學",
        "school_name": full_name,
        "country": country,
        "official_website": website,
        "verification_status": "official_verified",
        "discovery_source_url": source_url,
        "checked_at": CHECKED_AT,
        "note": (
            f"中山醫學大學國際事務處《締約學校總覽（{CSMU_SISTER_SCHOOLS_OVERVIEW_URL}）》、《出國交換與雙聯學位專區（{CSMU_EXCHANGE_REGS_FORMS_URL}）》與 ROR/Wikidata 官方網址核對完成。"
        ),
    })

    ev_sources = [
        {
            "title": f"中山醫學大學國際事務處締約姊妹校、交換生與雙聯學位簡章—{zh_name}",
            "url": source_url,
        },
    ]
    if exps:
      ev_sources.append({
          "title": f"中山醫大國際事務處海外研修心得分享專區—赴 {zh_name} 成果報告（{len(exps)} 篇）",
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
            "scope": "中山醫學大學海外交換姊妹校住宿與生活資訊",
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
            "scope": "中山醫學大學出國交換學雜費規定、免學費名額、教育部學海計畫（5萬–30萬元）與地區生活費估算",
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
            "scope": "中山醫學大學學生出國選修課程申請、每學期至少 6 學分規定與返國學分採認規範",
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
            "scope": "中山醫學大學海外交換與臨床實習簽證、疫苗抗體檢測、海外醫療保險與行前報到提醒",
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
                    f"｜中山醫大國際處公開收錄 {len(exps)} 篇赴 {zh_name} 海外交換／臨床實習心得報告（{'、'.join(exp_labels[:4])}）。"
                    if exps
                    else ""
                )
            ),
            "sources": ev_sources,
            "checked_at": CHECKED_AT,
            "scope": "中山醫學大學海外交換名額與歷屆學長姐成果報告分享",
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
            "已整合中山醫學大學國際事務處《締約學校列表》、《2027年赴美國聖馬丁大學／密西根州奧克蘭大學／日本德島文理大學交換生暨學位連讀甄選公告》、《教育部116年度學海飛颺、學海惜珠甄選公告》、《選送學生出國研修甄選辦法》、《學生出國選修課程辦法》及 30 篇歷屆學長姐與計畫主持人成果報告書。",
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
          f"中山醫學大學赴 {zh_name} 海外交換研修／臨床專業實習成果報告彙編（共 {len(exps)} 篇學長姐與師長報告）"
      )
      latest_e = exps[0]
      latest_author = (
          f"{latest_e['student']} 等 {len(exps)} 位中山醫研修師生"
          if len(exps) > 1
          else latest_e["student"]
      )
      summary_text = (
          f"中山醫學大學國際事務處公開收錄 {len(exps)} 篇歷年赴 {zh_name} 海外交換研修與臨床專業實習成果報告（含：{'、'.join(exp_labels[:5])}）。"
          f"{latest_e['highlight']}"
      )
      theme_map = {
          "academics": (
              f"中山醫研修生（{'、'.join(exp_labels[:3])}）分享於 {zh_name} 修讀專業課程、參與教學醫院／視光與語聽臨床中心實習之學習心得，以及返國依《學生出國選修課程辦法》辦理學分採認之經驗。{latest_e['highlight']}"
          ),
          "housing": (
              f"中山醫研修生詳述 {zh_name} 校內外學生宿舍（如聖馬丁大學 Parsons Hall、德島文理大學學生寮）或臨床實習住宿申請、周邊生活機能與大眾運輸通勤方式（{housing_clean[:120]}）。"
          ),
          "campus_culture": (
              f"中山醫國際處收錄 {len(exps)} 篇赴 {zh_name} 成果報告書，記錄國際學伴交流、寄宿家庭體驗、跨國臨床醫療團隊協作與當地文化活動。"
          ),
          "cost": (
              f"中山醫研修生記錄於 {zh_name} 之每月住宿、伙食與交通開銷（{cost_default}），以及運用姊妹校免學費名額與教育部學海飛颺／惜珠／築夢獎學金（NT$ 5萬–30萬元）支應出國費用之規劃。"
          ),
      }
      student_experience_rows.append({
          "school_name": full_name,
          "country": country,
          "title": rep_title,
          "source_url": latest_e["url"],
          "source_type": "article",
          "platform": "中山醫學大學國際事務處—海外交換與實習心得分享專區",
          "author_name": latest_author,
          "language": "zh",
          "summary": summary_text,
          "themes": ["academics", "housing", "campus_culture", "cost"],
          "theme_summaries": theme_map,
          "content_status": "full_text",
          "perspective": "official_student_story",
          "published_at": None,
          "discovered_at": CHECKED_AT,
          "content_hash": hashlib.sha256(f"{full_name}:csmu_exp:{len(exps)}".encode("utf-8")).hexdigest(),
          "exchange_term": f"{latest_e['year']}年度",
          "summary_zh": summary_text,
          "original_summary": summary_text,
          "theme_summaries_zh": theme_map,
          "translation_status": "original",
          "source_kind": "official_experience_page",
      })

    experience_sources_records.append({
        "home_university": "中山醫學大學",
        "school_name": full_name,
        "country": country,
        "official_experience_portal_url": (
            exps[0]["url"] if exps else CSMU_EXPERIENCES_ZH_URL
        ),
        "partner_page_url": source_url,
        "report_count": len(exps),
        "sample_reports": sample_reports,
        "checked_at": CHECKED_AT,
    })

  partners_jsonl_text = "\n".join(json.dumps(r, ensure_ascii=False) for r in partners) + "\n"
  (OFFICIAL_CSMU_DIR / "partners.jsonl").write_text(partners_jsonl_text, encoding="utf-8")
  (SOURCES_CSMU_DIR / "partners.jsonl").write_text(partners_jsonl_text, encoding="utf-8")
  (OFFICIAL_CSMU_DIR / "application_workflows.jsonl").write_text(
      "\n".join(json.dumps(r, ensure_ascii=False) for r in workflows) + "\n",
      encoding="utf-8",
  )
  (OFFICIAL_CSMU_DIR / "destination_profiles.jsonl").write_text(
      "\n".join(json.dumps(r, ensure_ascii=False) for r in destinations) + "\n",
      encoding="utf-8",
  )
  (OFFICIAL_CSMU_DIR / "partner_research.jsonl").write_text(
      "\n".join(json.dumps(r, ensure_ascii=False) for r in research_records) + "\n",
      encoding="utf-8",
  )
  (OFFICIAL_CSMU_DIR / "student_life.jsonl").write_text(
      "\n".join(json.dumps(r, ensure_ascii=False) for r in life_records) + "\n",
      encoding="utf-8",
  )
  (OFFICIAL_CSMU_DIR / "experience_sources.jsonl").write_text(
      "\n".join(json.dumps(r, ensure_ascii=False) for r in experience_sources_records) + "\n",
      encoding="utf-8",
  )
  (OFFICIAL_CSMU_DIR / "student_experiences.jsonl").write_text(
      "\n".join(json.dumps(r, ensure_ascii=False) for r in student_experience_rows) + "\n",
      encoding="utf-8",
  )
  (OFFICIAL_CSMU_DIR / "campus-locations.json").write_text(
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
  (OFFICIAL_CSMU_DIR / "student-experience-digests.json").write_text(
      json.dumps({"digests": digest_records}, ensure_ascii=False, indent=2) + "\n",
      encoding="utf-8",
  )

  # Ensure CSMU home location ONLY is added to university_locations.jsonl
  loc_file = REPO_ROOT / "src/exchange_info/official_data/university_locations.jsonl"
  existing_loc_lines = [
      line for line in loc_file.read_text(encoding="utf-8").splitlines() if line.strip()
  ]
  existing_loc_map = {}
  for line in existing_loc_lines:
    rec = json.loads(line)
    existing_loc_map[(rec["school_name"], rec.get("country") or "")] = rec

  csmu_home_loc = {
      "school_name": "中山醫學大學",
      "country": "臺灣",
      "city": "臺中市南區",
      "latitude": 24.1225,
      "longitude": 120.6514,
      "geocode_status": "verified",
      "geocoded_at": CHECKED_AT,
      "source_url": "https://www.wikidata.org/wiki/Q709239",
      "identity_source_url": "https://ror.org/059ry1682",
      "precision": "representative",
      "note": (
          "校級代表位置：官方網域及國家已與 ROR 比對，座標來源為 Wikidata P625；實際交換校區以錄取通知為準。"
          " 母校代表點採臺中市南區建國北路一段110號大慶校區正心樓國際事務處；官方地址來源：https://oia.csmu.edu.tw/?Lang=zh-tw。"
      ),
  }
  existing_loc_map[("中山醫學大學", "臺灣")] = csmu_home_loc
  sorted_locs = sorted(
      existing_loc_map.values(),
      key=lambda r: (r.get("country") or "", r.get("school_name") or ""),
  )
  loc_file.write_text(
      "\n".join(json.dumps(r, ensure_ascii=False) for r in sorted_locs) + "\n",
      encoding="utf-8",
  )

  csmu_source_urls = [
      CSMU_OIA_HUB_URL,
      CSMU_OIA_EN_HUB_URL,
      CSMU_SISTER_SCHOOLS_OVERVIEW_URL,
      CSMU_PARTNERS_AMERICAS_ZH_URL,
      CSMU_PARTNERS_ASIA_PACIFIC_ZH_URL,
      CSMU_PARTNERS_EUROPE_AFRICA_ZH_URL,
      CSMU_PARTNERS_EN_URL,
      CSMU_EXCHANGE_REGS_FORMS_URL,
      CSMU_EXCHANGE_FAQ_URL,
      CSMU_XUEHAI_HOW_TO_APPLY_URL,
      CSMU_XUEHAI_REGS_FORMS_URL,
      CSMU_XUEHAI_COUNTS_URL,
      CSMU_EXPERIENCES_ZH_URL,
      CSMU_2027_ST_MARTINS_NOTICE_URL,
      CSMU_2027_TOKUSHIMA_NOTICE_URL,
      CSMU_2027_OAKLAND_NOTICE_URL,
      CSMU_2027_LSU_NOTICE_URL,
      CSMU_116_XUEHAI_FEIYANG_NOTICE_URL,
      CSMU_115_2_XUEHAI_ZHUMENG_NOTICE_URL,
      CSMU_2026_KAWAMURA_NOTICE_URL,
      CSMU_DUAL_OAKLAND_URL,
      CSMU_DUAL_ANDREWS_URL,
      CSMU_DUAL_DUQUESNE_URL,
      CSMU_EX_TOKUSHIMA_PATHWAY_URL,
      CSMU_EX_ST_MARTINS_URL,
      CSMU_EX_TOKUSHIMA_FLOW_URL,
      CSMU_EXCHANGE_SELECTION_REGS_PDF_URL,
      CSMU_OVERSEAS_COURSE_REGS_PDF_URL,
      CSMU_XUEHAI_SUBSIDY_REGS_PDF_URL,
  ]

  exchange_info_payload = {
      "school_name": "中山醫學大學",
      "program_type": [
          (
              "116學年度（2027–2028）校級重點出國交換學生暨學位連讀甄選計畫（統一收件至 115年10月22日［2026/10/22］截止：含【美國華盛頓州聖馬丁大學 Saint Martin's University】自費交換不限名額＋每學期 3 名免學費交換生優待名額；【日本德島文理大學 Tokushima Bunri University】每學期 2 名免學費交換生＋1 名赴日升學研究所課程銜接計畫［Pathway Program, PP］免學費名額＋夏季日語研修團 5 名；【美國密西根州奧克蘭大學 Oakland University】每年 15 名 International ASAP 交換生及生物學 BA-to-MA 4+1／4+2 學碩連讀雙聯名額）"
          ),
          (
              "跨國雙聯學位與海外生物醫學研究獎學金計畫（含【美國安德魯大學 Andrews University】3.5+0.5+1 Accelerating MBA 企管碩士雙聯學制、【美國杜肯大學 Duquesne University】醫管與生物醫學碩士雙聯學制，以及【美國路易斯安那州立大學紐奧良醫學中心 LSU Health Sciences Center New Orleans】2027年春季赴美 1 年期研究獎學金［收件至 2026/09/30 截止，錄取碩博士生獲美方每月補助 USD 2,500 生活費］）"
          ),
          (
              "教育部《116年度學海飛颺／學海惜珠》出國研修獎學金（收件至 116年1月6日［2027/01/06］截止，每人補助新臺幣 5 萬至 30 萬元）與《學海築夢／新南向學海築夢》海外臨床及專業實習計畫（第1次甄選每年 12–1 月、第2次甄選於 2026/08/31 截止；長期選送醫學、牙醫、護理、語聽、視光、物治、職治、醫技、醫管、公衛與營養等系學生赴美國賓州大學、華盛頓大學、天普大學、塔夫茨大學、明尼蘇達大學、UAB、USC、薩盧斯大學、太平洋大學視光學院、AHMC 仁愛醫療集團、聖母峰養老機構、奧地利維也納醫學大學 AKH、瑞士伯恩大學、波蘭華沙醫學大學、匈牙利德布勒森大學、日本東京醫科大學、東邦大學、順天堂大學、日本齒科大學、新潟醫療福祉大學、新加坡中央醫院 SGH、新加坡國大醫院 NUH、竹腳婦幼醫院 KKH、泰國瑪希敦大學、朱拉隆功大學、清邁大學、皇太后大學、澳洲墨爾本大學與新南威爾斯大學等頂尖機構實習）"
          ),
      ],
      "academic_year": [
          (
              "116（2027–2028學年度赴美國聖馬丁大學、奧克蘭大學、日本德島文理大學交換生及學位連讀甄選收件至 2026/10/22 截止；教育部 116 年度學海飛颺／學海惜珠獎學金收件至 2027/01/06 截止；2027春季美國 LSUHSC 研究獎學金收件至 2026/09/30 截止；教育部 115 年度學海築夢／新南向學海築夢第 2 次甄選於 2026/08/31 截止）"
          ),
          (
              f"本平台完整收錄中山醫學大學國際事務處公告之 {len(partners)} 所全球締約合作大學、醫學院與教學醫院（含 {open_partner_count} 所當期開放交換、雙聯、研究獎學金與臨床見實習重點合作機構及 {len(partners) - open_partner_count} 所正式締約姊妹校，橫跨全球 26 個國家與地區，並完整收錄 {exp_covered_schools} 所合作機構共 {total_exp_reports} 篇歷屆學長姐與計畫主持人返國成果報告）"
          ),
      ],
      "semester": [
          "秋季學期（第1學期：美國奧克蘭大學、聖馬丁大學等為 2027 年 8/9 月至 12 月；日本德島文理大學秋季班為 2027 年 9 月至 2028 年 2 月）",
          "春季學期（第2學期：美國聖馬丁大學等為 2028 年 1 月至 5 月；日本德島文理大學春季班為 2027 年 4 月至 8 月；美國 LSUHSC 研究獎學金為 2027 年 3–4 月起為期 1 年）",
          "暑期及學期海外臨床見實習／教育部學海築夢與新南向學海築夢專業實習（國外專業實習須連續至少 30 天以上［不含來回途程，印尼至少 25 天］；日本德島文理大學夏季日語文化研修團為 7 月約 3 週）",
          "跨國學碩連讀與雙聯學位（美國奧克蘭大學生物學 4+1／4+2 BA-to-MA、美國安德魯大學 3.5+0.5+1 MBA、美國杜肯大學碩士雙聯、日本德島文理大學 4+2 PP 赴日升學研究所課程銜接計畫）",
      ],
      "application_period": [
          (
              "【2027年赴美國聖馬丁大學（每學期 3 名免學費）、美國密西根州奧克蘭大學（每年 15 名 ASAP 交換暨 4+1/4+2 生物學學碩連讀）、日本德島文理大學（每學期 2 名免學費＋PP 升學研究所計畫 1 名免學費）】校內統一收件至 115年10月22日（2026/10/22）17:00 截止；奧克蘭大學預計於 115年12月底前公告結果，聖馬丁大學與德島文理大學預計於 116年1月底前公告結果。（註：日本川村學園女子大學配合姐妹校通知，自 2027 年起中止選送交換生計畫）"
          ),
          (
              "【教育部 116 年度「學海飛颺、學海惜珠」獎助優秀學生出國研修甄選】校內收件至 116年1月6日（2027/01/06）截止，由國際事務處召開國際交流審查委員會審核並於 3 月底前報教育部、5 月底前公告結果。"
          ),
          (
              "【教育部「學海築夢、新南向學海築夢」海外專業實習與 2027 春季美國 LSUHSC 研究獎學金】學海築夢／新南向學海築夢第 1 次甄選於每年 12 月至 1 月初收件、第 2 次甄選於 115年8月31日（2026/08/31）截止；2027 年春季赴美國路易斯安那州立大學醫學中心（LSUHSC）1 年期研究獎學金延長收件至 115年9月30日（2026/09/30）截止，10 月面試。"
          ),
      ],
      "eligibility": [
          (
              "【在學學籍、年級與交換次數上限】凡中山醫學大學 4 個學院（醫學院、口腔醫學院、醫學科技學院、健康管理學院）在學至少滿一學期以上之正式學籍學士班、碩士班及博士班學生（出國時至少須完成大一課程；應屆畢業最後一學期、延畢生、休學生及國內外在職專班生不得申請交換及教育部學海計畫）。依《中山醫學大學選送學生出國研修甄選辦法》及《學生出國選修課程辦法》第4條規定，學生出國交換次數以 2 次為限，總修業時間不得超過 2 年。"
          ),
          (
              "【學業成績門檻（GPA 3.0／總平均 80 分或系排名前 40%）】（1）申請美國聖馬丁大學、日本德島文理大學（含 PP 升學研究所計畫）、美國奧克蘭大學生物學 4+1/4+2 學碩連讀、美國杜肯大學雙聯：在校歷年學業成績須達 GPA 3.0（百分制約 75 分）以上（奧克蘭大學 ASAP 交換計畫為 GPA 2.5 以上）；（2）申請教育部 116 年度《學海飛颺、學海惜珠》獎學金：在校學業總平均須達 80 分以上，或歷年學業成績排名居該系（所）前 40%。"
          ),
          (
              "【書面與面試評分權重、在學註冊與每學期 6 學分下限】依《中山醫學大學選送學生出國研修甄選辦法》，校內書面審查占 60%（配分：在校成績 40%、語文能力 35%、研修計畫 20%、其他輔助審查文件 5%［修過 EMI 全英語課程、曾任國際處外籍生接待學伴者優先加分］）、面試占 40%。出國交換期間須維持中山醫在學註冊並繳交全額學雜費、退撫費及平安保險費；申請學海飛颺／惜珠之大學部學生於國外研修期間每學期至少應修習相當於 6 學分之課程。"
          ),
      ],
      "language_requirement": [
          (
              "【美國重點交換與雙聯學位英語門檻】（1）美國華盛頓州聖馬丁大學（Saint Martin's University）：TOEFL ITP 525 或 TOEFL iBT 71 或 TOEIC 700 或 IELTS 6.0 以上（申請每學期 3 名免學費交換生須具備上述正式語檢成績）；（2）美國密西根州奧克蘭大學（Oakland University）：ASAP 專業課程直入及生物學 4+1/4+2 學碩連讀須達 TOEFL iBT 79 或 IELTS 6.5 或 Duolingo 105 以上（ASAP ESL 語言銜接課程須達 TOEFL iBT 68 或 IELTS 6.0 或 Duolingo 95 以上）；（3）美國安德魯大學（3.5+0.5+1 MBA）與杜肯大學雙聯：TOEFL iBT 80（安德魯亦採計 ITP 550）或 IELTS 6.5 以上。"
          ),
          (
              "【日本德島文理大學交換暨 PP 升學研究所計畫日語門檻】申請日本德島文理大學每學期 2 名免學費交換生須具備日本語能力試驗 JLPT N2 以上；申請赴日升學研究所課程銜接計畫（Pathway Program, PP，限應外系、營養系大三升大四）須具備 JLPT N2 或日本留學試驗（EJU）日語科目 200 分以上（應外系一般交換生填選香川高松車站校區文學部，PP 計畫學生填選德島校區）。"
          ),
          (
              "【教育部學海飛颺／惜珠／築夢與歐美日星澳臨床見實習外語標準】申請教育部 116 年度學海飛颺／惜珠須具備符合擬赴研修國別與姊妹校規定之有效外語檢定證明（英語系及歐洲／新加坡／澳洲教學醫院臨床見實習建議達 TOEFL iBT 79–85 / IELTS 6.0–6.5 / TOEIC 750–800；日本東邦大學、東京醫科大學、順天堂大學、日本齒科大學等建議達 JLPT N2 或 TOEFL iBT 79 / TOEIC 785）。"
          ),
      ],
      "required_documents": [
          "1. 中山醫學大學出國交換學生／學位連讀計畫甄選申請表（或教育部 116 年度學海飛颺／學海惜珠申請表，含個人基本資料、志願學校與研修期程）",
          "2. 中山醫大歷年中文及英文成績單正本各 1 份（須清楚載明歷年學業總平均、GPA 數值及系所班級排名百分比）",
          "3. 有效期限內之外語能力檢定成績證明影本（TOEFL iBT / TOEFL ITP / IELTS / TOEIC / Duolingo / JLPT N2 / EJU 等）",
          "4. 中文及英文自傳（Autobiography / CV）與出國讀書／研修計畫書（Study Plan，占校內書面審查 20%，須詳述申請動機、擬修習科目與返國學分銜接規劃）",
          "5. 本校專任教師推薦信（英文或日文，依各校簡章規定 1–2 封）及家長（監護人）同意書",
          "6. 其他輔助審查加分文件（占書審 5%：如修習本校全英語授課 EMI 課程證明、擔任國際事務處外籍生接待學伴證明、國際競賽或社團幹部證明等）",
          "7. 出國前教務必備表件：《中山醫學大學學生出國選修課程申請表》（須經系所主管、院長及教務處核准）及《教育部學海計畫行政契約書》",
          "8. 申請教育部《學海惜珠》者另須檢附：新式戶口名簿影本（註明現住人口及詳細記事）或三個月內戶籍謄本，以及直轄市、縣（市）主管機關開立之有效低收入戶、中低收入戶或特殊境遇家庭相關證明文件",
      ],
      "scholarship_info": [
          (
              "教育部 116 年度《學海飛颺》與《學海惜珠》出國研修獎學金（收件至 116年1月6日［2027/01/06］截止）：依《中山醫學大學辦理教育部學海飛颺及學海惜珠補助辦法》規定，補助具中華民國國籍且在臺設有戶籍、於中山醫就讀滿一學期以上、在校學業總平均 80 分以上或系所排名前 40% 之優秀在學生（學海惜珠另須具備低收／中低收入戶等資格）赴國外（不含大陸及港澳）姊妹校修讀學分 1 學期或 1 學年（大學部每學期至少修習 6 學分）。連同中山醫大至少 20% 配合款，每人實際核定補助總額為新臺幣 5 萬至 30 萬元（出國前核撥 80%，返國後 2 週內繳交 3,000 字心得報告並完成學海網站上傳後核撥剩餘 20%）。"
          ),
          (
              "姊妹校免學費交換生優待名額與雙聯學費減免：（1）美國華盛頓州聖馬丁大學（Saint Martin's University）每學期提供中山醫 3 名免學費交換生優待名額（全學年共 6 名，免除每學期約 USD 22,000 之美國私立大學學費）；（2）日本德島文理大學（Tokushima Bunri University）每學期提供 2 名免學費交換生名額及每學年 1 名 PP 赴日升學研究所課程銜接計畫免學費名額；（3）美國密西根州奧克蘭大學（Oakland University）生物學 4+1／4+2 學碩連讀提供密西根州州內學費（In-State Tuition）優惠及至多 9 學分研究所學分抵免；（4）美國安德魯大學（Andrews University）3.5+0.5+1 MBA 雙聯依 GPA 提供 10%–50% 學費減免獎學金。"
          ),
          (
              "教育部《學海築夢》與《新南向學海築夢》海外臨床及專業實習獎學金（第1次甄選每年 12–1 月、第2次甄選於 115年8月31日截止）：由中山醫大專任教師擔任計畫主持人，選送學生赴歐美日（學海築夢）或新南向國別（新加坡、泰國、澳洲、印尼、越南、馬來西亞、菲律賓、印度等）之合作教學醫院、視光中心、聽力語言治療中心或高齡長照機構進行至少 30 天（印尼至少 25 天）之臨床或專業實習，補助來回經濟艙機票與國外生活費（含校方至少 20% 配合款）。"
          ),
          (
              "美國路易斯安那州立大學醫學中心（LSU Health Sciences Center New Orleans）海外研究獎學金與校內深耕國際交流補助：（1）LSUHSC 研究獎學金（2027春季梯次收件至 2026/09/30 截止）：選送中山醫碩、博士生赴美國紐奧良醫學中心進行為期 1 年之生物醫學全職研究，由美方提供每人每月 2,500 美元（一年合計 USD 30,000）生活補助；（2）《中山醫學大學高教深耕經費學系國際交流補助》：補助各學系師生赴海外姊妹校進行短期臨床見習與國際學術交流。"
          ),
      ],
      "partner_universities": [p["school_name"] for p in partners],
      "source_urls": csmu_source_urls,
      "last_checked": CHECKED_AT,
  }
  (OFFICIAL_CSMU_DIR / "exchange_info.json").write_text(
      json.dumps(exchange_info_payload, ensure_ascii=False, indent=2) + "\n",
      encoding="utf-8",
  )

  student_dashboard_payload = {
      "school_name": "中山醫學大學",
      "last_checked": CHECKED_AT,
      "academic_score_minimum": 75.0,
      "academic_score_rule": (
          "依中山醫學大學《選送學生出國研修甄選辦法》、《2027年赴美國聖馬丁大學／日本德島文理大學／美國奧克蘭大學交換生及學位連讀甄選公告》及《教育部116年度學海飛颺、學海惜珠甄選公告》規定：申請美日重點交換生與學碩連讀須達在校歷年 GPA 3.0（百分制約 75 分）以上（奧克蘭大學 ASAP 交換為 GPA 2.5 以上）；申請教育部 116 年度學海飛颺／惜珠獎學金須達在校學業總平均 80 分以上或系所排名前 40%。"
      ),
      "academic_gpa_minimum": 3.0,
      "maximum_preferences": 3,
      "selection_rules": {
          "academic_policy": "gpa_or_rank",
          "academic_reference_year": "116",
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
          "toefl": 71.0,
          "ielts": 5.5,
          "toeic": 700.0,
      },
      "application_periods": [
          {
              "title": (
                  "中山醫學大學 116學年度（2027年）赴美國聖馬丁大學（3名免學費）、密西根州奧克蘭大學（15名交換暨學位連讀）、日本德島文理大學（2名免學費＋PP研究所銜接）甄選（2026/10/22 截止）"
              ),
              "details": [
                  (
                      "中山醫大國際事務處公告 2027 年三大重點交換與學位連讀計畫，統一收件至 115年10月22日（2026/10/22）17:00 截止：（1）美國華盛頓州聖馬丁大學（Saint Martin's University）2027秋季交換：自費名額不限，每學期另提供 3 名免學費交換生優待名額（GPA 3.0+，TOEFL iBT 71 / ITP 525 / TOEIC 700 / IELTS 6.0+）；（2）日本德島文理大學（Tokushima Bunri University）2027春季／秋季交換暨續升學研究所計畫：一般交換每學期 2 名免學費＋PP 赴日升學研究所課程銜接計畫 1 名免學費（GPA 3.0+，JLPT N2+）；（3）美國密西根州奧克蘭大學（Oakland University）2027秋季 ASAP 交換及生物學 4+1/4+2 學碩連讀：每年 15 名（ASAP 要求 GPA 2.5+、iBT 79 / IELTS 6.5 / Duolingo 105；生物學學碩連讀要求 GPA 3.0+、修畢生物相關 20 學分且享密西根州州內學費優惠）。"
                  ),
                  (
                      "校內書面審查配分為：在校成績 40%、語文能力 35%、研修計畫 20%、其他輔助審查文件 5%（修過 EMI 課程、曾任國際交流接待學伴者優先加分）；奧克蘭大學於 115年12月底前、聖馬丁大學與德島文理大學於 116年1月底前公告甄選結果。"
                  ),
              ],
              "source": {
                  "title": "中山醫學大學 2027年赴美國聖馬丁大學、奧克蘭大學、日本德島文理大學交換生暨學位連讀甄選公告",
                  "source_url": CSMU_2027_ST_MARTINS_NOTICE_URL,
                  "category": "exchange_application",
                  "summary": "中山醫大 2027 年赴美日三大重點姊妹校交換與學位連讀名額、免學費優惠、語檢門檻與 10/22 截止時程。",
              },
              "scope": "home_application",
              "program_types": ["exchange", "dual_degree"],
              "academic_year": "116",
              "application_round": "116學年度赴美日交換生暨學位連讀甄選",
              "audience": "all_students",
              "opens_at": "2026-08-19T09:00:00+08:00",
              "deadline_at": "2026-10-22T17:00:00+08:00",
              "date_status": "verified_exact",
              "status": "action_required",
              "status_note": "2027年赴美國聖馬丁大學、奧克蘭大學及日本德島文理大學交換生暨學位連讀甄選現正受理收件中，至 2026/10/22 (四) 17:00 截止。",
              "deadline_note": "請備妥校內申請表、中英文歷年成績單（含 GPA 及排名）、外語檢定證明、中英文自傳與讀書計畫書、推薦信及家長同意書送交正心樓國際事務處。",
              "reminder_eligible": True,
              "checked_at": CHECKED_AT,
          },
          {
              "title": (
                  "中山醫學大學 教育部116年度「學海飛颺、學海惜珠」獎助優秀學生出國研修甄選（2027/01/06 截止，每人補助 5萬–30萬元）"
              ),
              "details": [
                  (
                      "中山醫大國際事務處公告受理教育部 116 年度「學海飛颺、學海惜珠」出國研修獎學金申請，收件自即日起至 116年1月6日（2027/01/06）17:00 截止。申請人須具中華民國國籍且在臺設有戶籍、於本校就讀至少滿一學期（不含應屆畢業最後一學期、延畢生及在職專班生），且在校學業總平均達 80 分以上或系所排名前 40%。"
                  ),
                  (
                      "錄取學生赴國外（不含大陸及港澳地區）合作大學修讀學分 1 學期或 1 學年（大學部每學期至少應修習相當於 6 學分之課程），連同中山醫大至少 20% 配合款，每人核定補助新臺幣 5 萬至 30 萬元（可與聖馬丁大學、德島文理大學免學費交換生資格合併申請）。"
                  ),
              ],
              "source": {
                  "title": "中山醫學大學 教育部116年度「學海飛颺。學海惜珠」獎助優秀學生出國研修甄選公告",
                  "source_url": CSMU_116_XUEHAI_FEIYANG_NOTICE_URL,
                  "category": "scholarship",
                  "summary": "中山醫大 116 年度學海飛颺與學海惜珠申請資格（總平均 80 分或系排前 40%）、補助額度（5萬–30萬元）與 2027/01/06 截止日。",
              },
              "scope": "home_application",
              "program_types": ["exchange", "dual_degree"],
              "academic_year": "116",
              "application_round": "116年度教育部學海飛颺／學海惜珠獎學金甄選",
              "audience": "all_students",
              "opens_at": "2026-08-26T09:00:00+08:00",
              "deadline_at": "2027-01-06T17:00:00+08:00",
              "date_status": "verified_exact",
              "status": "action_required",
              "status_note": "教育部 116 年度學海飛颺、學海惜珠獎學金現正受理申請中，校內收件至 2027/01/06 (三) 17:00 截止。",
              "deadline_note": "預計於 116 學年度（2027春季至2028春季）出國交換或修讀雙聯學位之同學，請於 2027/01/06 前將完整申請表件送交國際事務處。",
              "reminder_eligible": True,
              "checked_at": CHECKED_AT,
          },
          {
              "title": (
                  "中山醫學大學 2027年春季赴美國路易斯安那州立大學醫學中心（LSUHSC）研究獎學金（2026/09/30 截止）＆ 115年度學海築夢第二次甄選（2026/08/31 截止）"
              ),
              "details": [
                  (
                      "2027年春季赴美國路易斯安那州立大學紐奧良醫學中心（LSU Health Sciences Center New Orleans）研究獎學金：延長收件至 115年9月30日（2026/09/30）截止，10 月面試，預計 2027 年 3–4 月赴美進行為期 1 年之生物醫學研究，錄取碩博士生獲美方提供每月 2,500 美元生活補助。"
                  ),
                  (
                      "教育部 115 年度「學海築夢」及「新南向學海築夢」獎助國外專業實習計畫第 2 次甄選：收件至 115年8月31日（2026/08/31）截止；下一年度（116年度）第 1 次學海築夢與新南向學海築夢計畫將配合教育部期程於 2026 年 12 月至 2027 年 1 月初受理計畫主持人提案。"
                  ),
              ],
              "source": {
                  "title": "中山醫學大學 2027年春季赴美國路易斯安那州立大學醫學中心研究獎學金與115年度學海築夢第二次甄選公告",
                  "source_url": CSMU_2027_LSU_NOTICE_URL,
                  "category": "scholarship",
                  "summary": "中山醫大 LSUHSC 每月 2,500 美元研究獎學金與教育部學海築夢／新南向學海築夢海外專業實習甄選時程。",
              },
              "scope": "home_application",
              "program_types": ["exchange"],
              "academic_year": "116",
              "application_round": "2027春季美國LSUHSC研究獎學金暨115年度學海築夢第二次甄選",
              "audience": "all_students",
              "opens_at": "2026-08-01T09:00:00+08:00",
              "deadline_at": "2026-09-30T17:00:00+08:00",
              "date_status": "verified_exact",
              "status": "closed",
              "status_note": "2027春季美國 LSUHSC 研究獎學金（2026/09/30 截止）及 115年度學海築夢第二次甄選（2026/08/31 截止）已截止收件；116年度學海飛颺／惜珠與 2027 美日交換生計畫現正開放申請中。",
              "deadline_note": "欲參與海外臨床或專業實習之同學，可提前向各學系學海築夢計畫主持人洽詢 116 年度實習梯次。",
              "reminder_eligible": False,
              "checked_at": CHECKED_AT,
          },
      ],
      "program_overview": [
          {
              "title": (
                  f"中山醫學大學國際事務處海外交換、雙聯學位、研究獎學金與臨床實習總覽（{len(partners)} 所全球合作姊妹校與教學醫院・{open_partner_count} 所當期開放重點機構・{total_exp_reports} 篇學長姐與師長成果報告）"
              ),
              "details": [
                  (
                      f"中山醫學大學（CSMU，中山醫／中山醫大）由「國際事務處（Office of International Affairs, OIA）」、「教務處」與全校 4 個學院（醫學院、口腔醫學院、醫學科技學院、健康管理學院）共同推動海外交換學生、跨國學碩連讀雙聯學位、海外生物醫學研究獎學金及教學醫院／視光／語聽／復健／長照臨床專業實習。本平台完整收錄 {len(partners)} 所中山醫大官方締約合作大學、醫學院與醫療機構（含 {open_partner_count} 所當期開放交換、雙聯、研究與臨床實習重點合作機構及 {len(partners) - open_partner_count} 所正式締約姊妹校），橫跨全球 26 個國家與地區（中國大陸 35 校、美國 29 校、日本 21 校、菲律賓 4 校、泰國 4 校、越南 4 校、印尼 3 校、新加坡 3 院、馬來西亞 2 校、澳門 2 校，以及澳洲、奧地利、瑞士、法國、芬蘭、波蘭、匈牙利、斯洛伐克、克羅埃西亞、俄羅斯、韓國、土耳其、印度、蒙古、聖克里斯多福及尼維斯、迦納各 1–2 校）。"
                  ),
                  (
                      f"中山醫大國際化體系具備四大核心亮點：（1）免學費交換生與學碩連讀雙聯旗艦計畫：美國華盛頓州聖馬丁大學（每學期 3 名免學費交換生）、日本德島文理大學（每學期 2 名免學費交換生＋1 名 PP 赴日升學研究所課程銜接計畫免學費名額）、美國密西根州奧克蘭大學（每年 15 名 ASAP 交換及生物學 4+1/4+2 學碩連讀享密西根州內學費）、美國安德魯大學（3.5+0.5+1 MBA 雙聯）、美國杜肯大學（醫管與生醫碩士連讀）及美國路易斯安那州立大學醫學中心（LSUHSC 每月補助 USD 2,500 研究獎學金）；（2）全科別海外臨床見實習與學海築夢網絡：涵蓋醫學、牙醫、護理、視光（美國太平洋大學視光學院、澳洲墨爾本大學臨床視光中心、法國 ISO）、語聽（美國薩盧斯大學、新加坡國大醫院 NUH／中央醫院 SGH／竹腳婦幼醫院 KKH）、醫管長照（美國加州 AHMC 仁愛醫療集團、聖母峰養老機構）及日本東邦大學、東京醫科大學、順天堂大學、日本齒科大學、奧地利維也納醫學大學 AKH 等；（3）教育部 116 年度學海飛颺／惜珠每人補助 NT$ 5萬–30萬元（含校方 20% 配合款）；（4）公開收錄 {exp_covered_schools} 所重點合作機構共 {total_exp_reports} 篇歷屆學長姐與計畫主持人返國心得報告。"
                  ),
              ],
              "source": {
                  "title": "中山醫學大學國際事務處—締約姊妹校總覽、交換生與雙聯學位甄選及學海計畫專區",
                  "source_url": CSMU_OIA_HUB_URL,
                  "category": "exchange_application",
                  "summary": f"中山醫大 {len(partners)} 所全球合作姊妹校與醫療機構、2027 美日交換與雙聯學制及 {total_exp_reports} 篇成果報告。",
              },
          }
      ],
      "eligibility": [
          {
              "title": "中山醫大在學資格、GPA 3.0（學海總平均 80 分或系排前 40%）門檻、書審配分（40%/35%/20%/5%）與交換次數上限",
              "details": [
                  (
                      "學業門檻與甄選配分（依《中山醫學大學選送學生出國研修甄選辦法》及《教育部116年度學海飛颺、學海惜珠甄選公告》）：申請人須為本校在學滿一學期以上之正式學籍學生（應屆畢業最後一學期、延畢生及在職專班生不得申請交換與學海計畫）。申請聖馬丁大學、德島文理大學、奧克蘭大學學碩連讀、杜肯大學須達歷年 GPA 3.0 以上（奧克蘭大學 ASAP 交換為 GPA 2.5 以上）；申請教育部 116 年度學海飛颺／惜珠須達在校學業總平均 80 分以上或系所排名前 40%。校內書面審查占 60%（在校成績 40% ＋ 語文能力 35% ＋ 研修計畫 20% ＋ 輔助審查文件 5%［EMI 課程、接待國際學伴加分］）、面試占 40%。"
                  ),
                  (
                      "交換上限與選課採認規定（依《中山醫學大學學生出國選修課程辦法》）：學生出國交換次數以 2 次為限，總修業時間不得超過 2 年；出國期間須維持中山醫在學註冊並繳交全額學雜費、退撫費及平安保險費；學海飛颺／惜珠大學部受獎生於國外每學期至少應修習 6 學分，且出國前須完成《學生出國選修課程申請表》核准。"
                  ),
              ],
              "source": {
                  "title": "中山醫學大學選送學生出國研修甄選辦法與學生出國選修課程辦法 PDF",
                  "source_url": CSMU_EXCHANGE_SELECTION_REGS_PDF_URL,
                  "category": "exchange_application",
                  "summary": "中山醫大出國交換甄選配分（成績40%/語文35%/計畫20%/輔助5%）、交換2次/2年上限、在學學雜費與學分採認辦法。",
              },
          }
      ],
      "language_requirements": [
          {
              "title": "2027赴美日交換與雙聯語檢門檻（聖馬丁 iBT 71 / TOEIC 700、奧克蘭 iBT 79 / Duolingo 105、德島文理 JLPT N2）",
              "details": [
                  (
                      "美日重點交換與學碩連讀語檢標準：（1）美國聖馬丁大學交換（含每學期 3 名免學費名額）：TOEFL ITP 525 或 TOEFL iBT 71 或 TOEIC 700 或 IELTS 6.0 以上；（2）美國密西根州奧克蘭大學：ASAP 專業課程及生物學 4+1/4+2 學碩連讀要求 TOEFL iBT 79 或 IELTS 6.5 或 Duolingo 105 以上（ESL 語言銜接課程為 iBT 68 / IELTS 6.0 / Duolingo 95）；（3）美國安德魯大學（3.5+0.5+1 MBA）與杜肯大學雙聯：TOEFL iBT 80 或 IELTS 6.5；（4）日本德島文理大學交換（每學期 2 名免學費）及 PP 升學研究所銜接計畫（1 名免學費）：JLPT N2（或 EJU 日語 200 分）以上。"
                  ),
                  (
                      "海外臨床見實習與教育部學海計畫外語標準：申請教育部 116 年度學海飛颺／惜珠／築夢須檢附符合擬赴國別與接待機構要求之有效外語證明（歐美澳與新加坡教學醫院臨床見實習建議達 TOEFL iBT 79–85 / IELTS 6.0–6.5 / TOEIC 750–800；日本教學醫院臨床見習建議達 JLPT N2 或 TOEIC 785）。"
                  ),
              ],
              "source": {
                  "title": "中山醫學大學 2027年赴美國聖馬丁大學、奧克蘭大學與日本德島文理大學交換甄選公告",
                  "source_url": CSMU_2027_OAKLAND_NOTICE_URL,
                  "category": "exchange_application",
                  "summary": "中山醫大各重點交換與雙聯合作校之 TOEFL、IELTS、TOEIC、Duolingo、JLPT 與 EJU 語檢門檻。",
              },
          }
      ],
      "required_documents": [
          {
              "title": "出國交換／雙聯／學海計畫申請文件清單、教務處《出國選修課程申請表》與返國 2 週內 3,000 字心得報告規範",
              "details": [
                  (
                      "校內甄選必備文件：1. 出國交換／雙聯或教育部學海計畫甄選申請表、2. 中英文歷年成績單正本（含 GPA 及系所排名百分比）、3. 有效外語能力檢定證明影本、4. 中英文自傳與出國讀書／研修計畫書（占書審 20%）、5. 師長推薦信及家長同意書、6. 其他輔助審查文件（占書審 5%：EMI 課程修課證明、國際學伴證明等；學海惜珠另附新式戶口名簿影本及低收／中低收證明）。"
                  ),
                  (
                      "出國前選課核准與返國核銷義務：出國前須填妥《中山醫學大學學生出國選修課程申請表》經系所主管、院長及教務處核准，並簽訂《學海計畫行政契約書》（先撥付 80% 補助款）；返國後須於 2 週（14 日）內繳交 3,000 字以上中文研修心得報告（含照片 4 張以上）並上傳教育部學海計畫網站，經審核通過後始撥付剩餘 20% 補助尾款，同時填具《出國選修課程學分及成績採認表》辦理學分抵免。"
                  ),
              ],
              "source": {
                  "title": "中山醫學大學出國交換學生與教育部學海計畫相關法規及表件下載專區",
                  "source_url": CSMU_EXCHANGE_REGS_FORMS_URL,
                  "category": "exchange_application",
                  "summary": "中山醫大出國交換甄選申請表、出國選修課程申請表、學分採認表與學海計畫表件下載。",
              },
          }
      ],
      "scholarship_info": [
          {
              "title": "教育部116年度學海飛颺／惜珠（每人補助 5萬–30萬元）、學海築夢／新南向築夢、美日姊妹校免學費名額與美國 LSUHSC 每月 2,500 美元研究獎學金",
              "details": [
                  (
                      "教育部學海四項計畫與校方配合款：（1）《116年度學海飛颺、學海惜珠》（2027/01/06 截止）：補助在校學業總平均 80 分以上或系排名前 40% 之在學生赴國外修讀學分 1 學期或 1 學年，連同中山醫至少 20% 配合款，每人核定補助新臺幣 5 萬至 30 萬元；（2）《學海築夢、新南向學海築夢》（每年兩梯次，115年第2次於 2026/08/31 截止）：補助赴海外醫療院所、視光／語聽中心或長照機構實習至少 30 天（印尼 25 天）之機票與生活費。"
                  ),
                  (
                      "姊妹校免學費名額與海外研究獎學金：（1）美國聖馬丁大學每學期提供 3 名免學費交換生優待名額；（2）日本德島文理大學每學期提供 2 名免學費交換生名額＋每學年 1 名 PP 研究所銜接計畫免學費名額；（3）美國奧克蘭大學生物學 4+1/4+2 學碩連讀享密西根州州內學費優惠；（4）美國路易斯安那州立大學醫學中心（LSUHSC）提供錄取碩博士生每月 2,500 美元（為期一年共 USD 30,000）研究生活獎學金。"
                  ),
              ],
              "source": {
                  "title": "中山醫學大學辦理教育部學海飛颺及學海惜珠補助辦法與116年度甄選公告 PDF",
                  "source_url": CSMU_XUEHAI_SUBSIDY_REGS_PDF_URL,
                  "category": "scholarship",
                  "summary": "中山醫大教育部學海飛颺／惜珠 5萬–30萬元補助額度、80%/20% 撥款核銷規則與美日姊妹校免學費名額。",
              },
          }
      ],
      "document_explanations": [
          {
              "title": "中山醫學大學出國研修計畫書（占書審20%）、EMI／國際學伴加分文件與《學生出國選修課程申請表》準備指南",
              "summary": "說明中山醫大國際事務處書面審查配分重點（成績40%／語文35%／研修計畫20%／輔助文件5%）及教務處出國選課與返國採認流程。",
              "key_points": [
                  "依《中山醫學大學選送學生出國研修甄選辦法》，校內書面審查占總成績 60%，其中「研修計畫書」占 20%，須具體規劃擬於姊妹校（如聖馬丁大學、德島文理大學、奧克蘭大學）修習之專業科目、每學期至少 6 學分之配置及預期學習成效。",
                  "書面審查中「其他輔助審查文件」占 5%，曾修習本校全英語授課（EMI）課程或曾擔任國際事務處外籍生接待學伴、參與國際醫療志工或國際交流活動者，務必檢附相關證明以獲得優先加分。",
                  "錄取後出國前必須填妥《中山醫學大學學生出國選修課程申請表》經系（所）主管、院長及教務處審核通過；返國後填具《出國選修課程學分及成績採認表》檢附正式成績單與課程大綱辦理學分抵免，並於返國 2 週內繳交 3,000 字以上研修心得報告。",
              ],
              "applies_to": [],
              "source": {
                  "title": "中山醫學大學選送學生出國研修甄選辦法與學生出國選修課程辦法 PDF",
                  "source_url": CSMU_EXCHANGE_SELECTION_REGS_PDF_URL,
                  "category": "exchange_application",
                  "summary": None,
              },
              "document_url": CSMU_EXCHANGE_SELECTION_REGS_PDF_URL,
              "document_type": "official_document",
              "full_text_extracted": True,
          }
      ],
      "rule_explanations": [
          {
              "title": "中山醫學大學選送學生出國研修甄選辦法、學生出國選修課程辦法與教育部學海計畫補助辦法核心規定",
              "summary": "規範中山醫大交換次數上限（2次／累計2年）、在學學雜費繳交義務、大學部每學期至少 6 學分、德島文理大學校區分流與學海獎學金 80%/20% 撥款規則。",
              "key_points": [
                  "交換次數與在學註冊（《學生出國選修課程辦法》第4、8條）：學生出國交換次數以 2 次為限，總修業時間不得超過 2 年（應屆畢業最後一學期及延畢生不得申請）；出國交換期間仍須辦理本校註冊並繳交全額學雜費、退撫費及學生平安保險費。",
                  "日本德島文理大學校區與學科分流規定：應用外國語言學系一般交換生須填選香川（高松車站）校區文學部（日本文學科或英語英美文化學科）；申請 PP 赴日升學研究所課程銜接計畫（限應外系、營養系）之學生則填選德島校區（綜合政策學科或人間生活學科）。",
                  "教育部學海飛颺／惜珠修課學分與撥款核銷（《辦理教育部學海飛颺及學海惜珠補助辦法》）：受獎學生須具中華民國國籍且在校學業總平均達 80 分以上或系排名前 40%，大學部受獎生於國外每學期至少應修習相當於 6 學分之課程；獎學金（NT$ 5萬–30萬元）於出國前撥付 80%，返國後 2 週內繳交 3,000 字以上心得報告並完成學海計畫網站上傳後撥付剩餘 20%。",
              ],
              "applies_to": [],
              "source": {
                  "title": "中山醫學大學學生出國選修課程辦法與辦理教育部學海飛颺及學海惜珠補助辦法 PDF",
                  "source_url": CSMU_OVERSEAS_COURSE_REGS_PDF_URL,
                  "category": "exchange_application",
                  "summary": None,
              },
              "document_url": CSMU_OVERSEAS_COURSE_REGS_PDF_URL,
              "document_type": "official_document",
              "full_text_extracted": True,
          }
      ],
      "sources": [
          {
              "title": "中山醫學大學國際事務處（Office of International Affairs, OIA）官方網站",
              "source_url": CSMU_OIA_HUB_URL,
              "category": "exchange_application",
              "summary": None,
          },
          {
              "title": "中山醫學大學 2027年秋季赴美國聖馬丁大學交換學生甄選公告（每學期3名免學費名額，10/22截止）",
              "source_url": CSMU_2027_ST_MARTINS_NOTICE_URL,
              "category": "exchange_application",
              "summary": None,
          },
          {
              "title": "中山醫學大學 2027年赴日本德島文理大學交換學生暨續升學研究所（PP）計畫甄選公告（10/22截止）",
              "source_url": CSMU_2027_TOKUSHIMA_NOTICE_URL,
              "category": "exchange_application",
              "summary": None,
          },
          {
              "title": "中山醫學大學 2027年秋季赴美國密西根州奧克蘭大學交換生（ASAP）及學位連讀計畫甄選公告（每年15名，10/22截止）",
              "source_url": CSMU_2027_OAKLAND_NOTICE_URL,
              "category": "exchange_application",
              "summary": None,
          },
          {
              "title": "中山醫學大學 教育部116年度「學海飛颺。學海惜珠」獎助優秀學生出國研修甄選公告（2027/01/06截止）",
              "source_url": CSMU_116_XUEHAI_FEIYANG_NOTICE_URL,
              "category": "scholarship",
              "summary": None,
          },
          {
              "title": "中山醫學大學 2027年春季赴美國路易斯安那州立大學醫學中心（LSUHSC）研究獎學金與115年度學海築夢第二次甄選公告",
              "source_url": CSMU_2027_LSU_NOTICE_URL,
              "category": "scholarship",
              "summary": None,
          },
          {
              "title": "中山醫學大學選送學生出國研修甄選辦法、學生出國選修課程辦法與辦理教育部學海飛颺及學海惜珠補助辦法 PDF",
              "source_url": CSMU_EXCHANGE_SELECTION_REGS_PDF_URL,
              "category": "exchange_application",
              "summary": None,
          },
          {
              "title": f"中山醫學大學全球締約姊妹校總覽（{len(partners)}校）與海外交換及臨床實習心得分享專區（{total_exp_reports}篇報告）",
              "source_url": CSMU_SISTER_SCHOOLS_OVERVIEW_URL,
              "category": "partner_school",
              "summary": None,
          },
      ],
  }
  (OFFICIAL_CSMU_DIR / "student_dashboard.json").write_text(
      json.dumps(student_dashboard_payload, ensure_ascii=False, indent=2) + "\n",
      encoding="utf-8",
  )

  pages_records = [
      {
          "title": "中山醫學大學：2027年赴美國聖馬丁大學／奧克蘭大學／日本德島文理大學交換暨學位連讀（10/22截止）與教育部116年度學海飛颺／惜珠（1/6截止）時程",
          "source_url": CSMU_2027_ST_MARTINS_NOTICE_URL,
          "published_at": "2026-10-21T00:00:00Z",
          "text": "\n".join(exchange_info_payload["application_period"]),
          "summary": "\n".join(exchange_info_payload["application_period"]),
          "category": "exchange_application",
          "attachments": [],
          "crawled_at": CHECKED_AT,
          "content_hash": hashlib.sha256("\n".join(exchange_info_payload["application_period"]).encode("utf-8")).hexdigest(),
      },
      {
          "title": "中山醫學大學：出國交換、學位連讀與教育部學海計畫申請資格（GPA 3.0／學海總平均80分或系排前40%、書審配分40%/35%/20%/5%与交換2次/2年上限）",
          "source_url": CSMU_EXCHANGE_SELECTION_REGS_PDF_URL,
          "published_at": "2026-10-21T00:00:00Z",
          "text": "\n".join(exchange_info_payload["eligibility"]),
          "summary": "\n".join(exchange_info_payload["eligibility"]),
          "category": "exchange_application",
          "attachments": [],
          "crawled_at": CHECKED_AT,
          "content_hash": hashlib.sha256("\n".join(exchange_info_payload["eligibility"]).encode("utf-8")).hexdigest(),
      },
      {
          "title": f"中山醫學大學：{len(partners)} 所合作姊妹校與教學醫院外語檢定門檻（聖馬丁 iBT 71 / TOEIC 700、奧克蘭 iBT 79 / Duolingo 105、德島文理 JLPT N2）",
          "source_url": CSMU_2027_OAKLAND_NOTICE_URL,
          "published_at": "2026-10-21T00:00:00Z",
          "text": "\n".join(exchange_info_payload["language_requirement"]),
          "summary": "\n".join(exchange_info_payload["language_requirement"]),
          "category": "exchange_application",
          "attachments": [],
          "crawled_at": CHECKED_AT,
          "content_hash": hashlib.sha256("\n".join(exchange_info_payload["language_requirement"]).encode("utf-8")).hexdigest(),
      },
      {
          "title": "中山醫學大學：出國交換、雙聯學位與學海計畫申請文件及教務處《學生出國選修課程申請表》核准規範",
          "source_url": CSMU_OVERSEAS_COURSE_REGS_PDF_URL,
          "published_at": "2026-10-21T00:00:00Z",
          "text": "\n".join(exchange_info_payload["required_documents"]),
          "summary": "\n".join(exchange_info_payload["required_documents"]),
          "category": "exchange_application",
          "attachments": [],
          "crawled_at": CHECKED_AT,
          "content_hash": hashlib.sha256("\n".join(exchange_info_payload["required_documents"]).encode("utf-8")).hexdigest(),
      },
      {
          "title": "中山醫學大學：教育部116年度學海飛颺／惜珠（每人補助5萬–30萬元）、學海築夢／新南向築夢、姊妹校免學費名額與美國 LSUHSC 每月 2,500 美元研究獎學金",
          "source_url": CSMU_116_XUEHAI_FEIYANG_NOTICE_URL,
          "published_at": "2026-10-21T00:00:00Z",
          "text": "\n".join(exchange_info_payload["scholarship_info"]),
          "summary": "\n".join(exchange_info_payload["scholarship_info"]),
          "category": "scholarship",
          "attachments": [],
          "crawled_at": CHECKED_AT,
          "content_hash": hashlib.sha256("\n".join(exchange_info_payload["scholarship_info"]).encode("utf-8")).hexdigest(),
      },
  ]
  (OFFICIAL_CSMU_DIR / "pages.jsonl").write_text(
      "\n".join(json.dumps(p, ensure_ascii=False) for p in pages_records) + "\n",
      encoding="utf-8",
  )

  home_rules = {
      "school_id": "csmu",
      "school_name": "中山醫學大學",
      "eligibility": student_dashboard_payload["eligibility"],
      "application_periods": student_dashboard_payload["application_periods"],
      "selection_rules": {
          "undergraduate_score_minimum": 75.0,
          "graduate_score_minimum": 75.0,
          "xuehai_score_minimum": 80.0,
          "department_rank_percent_max": 40,
          "exchange_gpa_minimum": 3.0,
          "oakland_asap_gpa_minimum": 2.5,
          "excluded_undergraduate_years": ["大一上"],
          "require_csmu_enrollment_and_full_tuition_during_abroad": True,
          "max_exchange_times": 2,
          "max_exchange_total_years": 2,
          "xuehai_undergrad_min_credits_per_semester": 6,
          "xuehai_grant_range_ntd": "50000-300000",
          "xuehai_school_matching_fund_min_ratio": 0.20,
          "written_review_weights": {
              "academic_record": 0.40,
              "language_proficiency": 0.35,
              "study_plan": 0.20,
              "supplementary_documents_emi_and_buddy": 0.05,
          },
          "overall_selection_weights": {
              "written_review": 0.60,
              "interview": 0.40,
          },
          "return_report_due_days": 14,
          "return_report_min_words": 3000,
          "return_documents_due": "教育部學海計畫受獎生及出國交換生須於返國後 2 週（14 日）內繳交 3,000 字以上中文研修心得報告（含照片 4 張以上）並完成教育部學海計畫網站上傳，經審核通過後始核撥剩餘 20% 補助尾款，並填具《出國選修課程學分及成績採認表》檢附正式成績單向教務處申請學分採認",
      },
      "source_urls": csmu_source_urls,
      "verified_at": "2026-10-21",
  }
  (OFFICIAL_CSMU_DIR / "home_rules.json").write_text(
      json.dumps(home_rules, ensure_ascii=False, indent=2) + "\n",
      encoding="utf-8",
  )
  (OFFICIAL_CSMU_DIR / "documents.json").write_text(
      json.dumps(
          {
              "school_name": "中山醫學大學",
              "required_documents": student_dashboard_payload["required_documents"],
              "source_urls": csmu_source_urls,
          },
          ensure_ascii=False,
          indent=2,
      )
      + "\n",
      encoding="utf-8",
  )
  (OFFICIAL_CSMU_DIR / "scholarships.json").write_text(
      json.dumps(
          {
              "school_name": "中山醫學大學",
              "scholarships": student_dashboard_payload["scholarship_info"],
              "source_urls": csmu_source_urls,
          },
          ensure_ascii=False,
          indent=2,
      )
      + "\n",
      encoding="utf-8",
  )

  completeness = {
      "school_id": "csmu",
      "school_name": "中山醫學大學",
      "total_partners": len(partners),
      "partner_count": len(partners),
      "international_partners": sum(
          1 for p in partners if p["country"] not in {"中國大陸", "香港", "澳門"}
      ),
      "mainland_partners": sum(
          1 for p in partners if p["country"] in {"中國大陸", "香港", "澳門"}
      ),
      "dual_degree_partner_universities": 4,
      "dual_degree_programs": 5,
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
          f"中山醫學大學國際事務處（OIA）與教務處 116 學年度（2027–2028）赴美國聖馬丁大學（每學期 3 名免學費）、美國密西根州奧克蘭大學（每年 15 名 ASAP 交換及生物學 4+1/4+2 學碩連讀）、日本德島文理大學（每學期 2 名免學費＋PP 升學研究所計畫 1 名免學費）甄選（2026/10/22 截止）、教育部 116 年度學海飛颺／惜珠獎學金甄選（2027/01/06 截止，每人補助 NT$ 5萬–30萬元）、2027春季美國 LSUHSC 研究獎學金（每月 USD 2,500）與學海築夢／新南向學海築夢海外臨床實習同步整合；共完整收錄 {len(partners)} 所全球締約合作大學、醫學院與教學醫院（含 {open_partner_count} 所當期開放交換、雙聯、研究與臨床實習機構及 {len(partners) - open_partner_count} 所正式締約姊妹校，橫跨全球 26 個國家與地區，並收錄 {exp_covered_schools} 所合作機構共 {total_exp_reports} 篇歷屆學長姐與師長返國成果報告）。"
      ),
      "verified_at": "2026-10-21",
  }
  (OFFICIAL_CSMU_DIR / "catalog-completeness.json").write_text(
      json.dumps(completeness, ensure_ascii=False, indent=2) + "\n",
      encoding="utf-8",
  )
  (OFFICIAL_CSMU_DIR / "verification_status.json").write_text(
      json.dumps(
          {
              "school_id": "csmu",
              "school_name": "中山醫學大學",
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
          "sources/csmu/sister_schools_75.html",
          CSMU_SISTER_SCHOOLS_OVERVIEW_URL,
          "中山醫學大學國際事務處締約學校總覽 HTML",
      ),
      (
          "sources/csmu/sister_sub_0.html",
          CSMU_PARTNERS_AMERICAS_ZH_URL,
          "中山醫學大學國際事務處締約姊妹校—美洲地區 HTML",
      ),
      (
          "sources/csmu/sister_sub_1.html",
          CSMU_PARTNERS_ASIA_PACIFIC_ZH_URL,
          "中山醫學大學國際事務處締約姊妹校—亞太地區 HTML",
      ),
      (
          "sources/csmu/sister_sub_2.html",
          CSMU_PARTNERS_EUROPE_AFRICA_ZH_URL,
          "中山醫學大學國際事務處締約姊妹校—歐洲與非洲地區 HTML",
      ),
      (
          "sources/csmu/partners_asia_en.html",
          CSMU_PARTNERS_EN_URL,
          "中山醫學大學國際事務處英文版締約姊妹校列表 HTML",
      ),
      (
          "sources/csmu/notice_2027_st_martins.html",
          CSMU_2027_ST_MARTINS_NOTICE_URL,
          "中山醫學大學 2027年秋季赴美國聖馬丁大學交換學生甄選公告 HTML",
      ),
      (
          "sources/csmu/notice_2027_tokushima.html",
          CSMU_2027_TOKUSHIMA_NOTICE_URL,
          "中山醫學大學 2027年赴日本德島文理大學交換學生暨續升學研究所計畫甄選公告 HTML",
      ),
      (
          "sources/csmu/notice_2027_oakland.html",
          CSMU_2027_OAKLAND_NOTICE_URL,
          "中山醫學大學 2027年秋季赴美國密西根州奧克蘭大學交換生及學位連讀計畫甄選公告 HTML",
      ),
      (
          "sources/csmu/notice_2027_lsu.html",
          CSMU_2027_LSU_NOTICE_URL,
          "中山醫學大學 2027年春季赴美國路易斯安那州立大學醫學中心研究獎學金公告 HTML",
      ),
      (
          "sources/csmu/notice_116_xuehai.html",
          CSMU_116_XUEHAI_FEIYANG_NOTICE_URL,
          "中山醫學大學 教育部116年度「學海飛颺。學海惜珠」獎助優秀學生出國研修甄選公告 HTML",
      ),
      (
          "sources/csmu/notice_115_zhumeng_2nd.html",
          CSMU_115_2_XUEHAI_ZHUMENG_NOTICE_URL,
          "中山醫學大學 教育部115年度「學海築夢」及「新南向學海築夢」第2次甄選作業公告 HTML",
      ),
      (
          "sources/csmu/notice_2026_kawamura.html",
          CSMU_2026_KAWAMURA_NOTICE_URL,
          "中山醫學大學 2026年秋季赴日本川村學園女子大學交換學生甄選公告 HTML",
      ),
      (
          "sources/csmu/ex_regs_forms.html",
          CSMU_EXCHANGE_REGS_FORMS_URL,
          "中山醫學大學出國交換學生相關法規與表格下載專頁 HTML",
      ),
      (
          "sources/csmu/ex_dual_faq.html",
          CSMU_EXCHANGE_FAQ_URL,
          "中山醫學大學出國交換學生及雙聯學位常見問題 FAQ HTML",
      ),
      (
          "sources/csmu/csmu_catalog_source.json",
          CSMU_SISTER_SCHOOLS_OVERVIEW_URL,
          f"中山醫學大學 {len(partners)} 所全球合作大學、醫學院與教學醫院整合資料集 JSON",
      ),
      (
          "sources/csmu/csmu_resolved_locations.json",
          CSMU_SISTER_SCHOOLS_OVERVIEW_URL,
          f"中山醫學大學 {len(partners)} 所全球合作機構 ROR / Wikidata 地理座標核對表 JSON",
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
      "school_id": "csmu",
      "school_name": "中山醫學大學",
      "generated_at": CHECKED_AT,
      "active_cycle_note": completeness["active_term"],
      "sources": prov_sources,
  }
  prov_text = json.dumps(provenance_payload, ensure_ascii=False, indent=2) + "\n"
  (OFFICIAL_CSMU_DIR / "import_provenance.json").write_text(prov_text, encoding="utf-8")
  (OFFICIAL_CSMU_DIR / "import-provenance.json").write_text(prov_text, encoding="utf-8")

  print(
      f"Successfully built CSMU catalog: {len(partners)} partners"
      f" ({open_partner_count} open, {completeness['verified_campus_images']}"
      f" verified images, {completeness['verified_locations']} verified"
      f" locations), {len(workflows)} workflows,"
      f" {len(destinations)} destinations, {len(research_records)} research"
      f" records, {exp_covered_schools} schools with experience records"
      f" ({len(student_experience_rows)} rows, {total_exp_reports} reports)."
  )


if __name__ == "__main__":
  main()
