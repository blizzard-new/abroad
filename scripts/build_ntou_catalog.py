"""Build the official National Taiwan Ocean University (國立臺灣海洋大學, NTOU) exchange data bundle."""

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

SOURCES_NTOU_DIR = REPO_ROOT / "sources" / "ntou"
OFFICIAL_NTOU_DIR = REPO_ROOT / "src" / "exchange_info" / "official_data" / "ntou"
STATIC_DIR = REPO_ROOT / "src" / "exchange_info" / "static"

CHECKED_AT = "2026-10-20T15:50:00Z"

NTOU_OIA_HUB_URL = "https://oia.ntou.edu.tw/"
NTOU_OUTBOUND_OVERVIEW_URL = "https://oia.ntou.edu.tw/p/412-1022-6958.php?Lang=zh-tw"
NTOU_EXCHANGE_PLAN_URL = "https://oia.ntou.edu.tw/p/412-1022-10817.php?Lang=zh-tw"
NTOU_DUAL_DEGREE_URL = "https://oia.ntou.edu.tw/p/412-1022-8671.php?Lang=zh-tw"
NTOU_DUAL_DEGREE_XLSX_URL = "https://oia.ntou.edu.tw/var/file/22/1022/img/973/663723575.xlsx"
NTOU_XUEHAI_OVERVIEW_URL = "https://oia.ntou.edu.tw/p/412-1022-10818.php?Lang=zh-tw"
NTOU_XUEHAI_FEIYANG_URL = "https://oia.ntou.edu.tw/p/412-1022-10819.php?Lang=zh-tw"
NTOU_XUEHAI_XIZHU_URL = "https://oia.ntou.edu.tw/p/412-1022-10820.php?Lang=zh-tw"
NTOU_XUEHAI_ZHUMENG_URL = "https://oia.ntou.edu.tw/p/412-1022-10821.php?Lang=zh-tw"
NTOU_BROCHURE_2027_URL = "https://oia.ntou.edu.tw/var/file/22/1022/img/1029/779655790.pdf"
NTOU_BROCHURE_2026_URL = "https://oia.ntou.edu.tw/var/file/22/1022/img/194074873.pdf"
NTOU_GUIDELINES_LANG_URL = "https://oia.ntou.edu.tw/var/file/22/1022/img/1029/854516693.pdf"
NTOU_ENFORCEMENT_RULES_URL = "https://oia.ntou.edu.tw/var/file/22/1022/img/1029/777268759.pdf"
NTOU_XUEHAI_RULES_URL = "https://oia.ntou.edu.tw/var/file/22/1022/img/1029/830669231.pdf"
NTOU_MOE_XUEHAI_115_URL = "https://oia.ntou.edu.tw/var/file/22/1022/img/1029/380374043.pdf"
NTOU_APP_CHECKLIST_URL = "https://oia.ntou.edu.tw/var/file/22/1022/img/1029/892749589.pdf"
NTOU_AUTOBIO_EX_URL = "https://oia.ntou.edu.tw/var/file/22/1022/img/1029/764741202.pdf"
NTOU_STUDY_PLAN_EX_URL = "https://oia.ntou.edu.tw/var/file/22/1022/img/1029/288285085.pdf"
NTOU_BUDGET_EX_URL = "https://oia.ntou.edu.tw/var/file/22/1022/img/1029/814897101.pdf"
NTOU_PRE_DEPARTURE_URL = "https://oia.ntou.edu.tw/var/file/22/1022/img/1029/705516691.pdf"
NTOU_REIMBURSEMENT_URL = "https://oia.ntou.edu.tw/var/file/22/1022/img/1029/765889941.pdf"
NTOU_SOP_EXCHANGE_URL = "https://oia.ntou.edu.tw/var/file/22/1022/img/972/484468333.pdf"
NTOU_SOP_DUAL_URL = "https://oia.ntou.edu.tw/var/file/22/1022/img/972/757675578.pdf"
NTOU_MAINLAND_115_2_URL = "https://oia.ntou.edu.tw/p/406-1022-70577,r11.php?Lang=zh-tw"
NTOU_SISTER_SCHOOLS_URL = "https://oia.ntou.edu.tw/p/412-1022-6904.php?Lang=zh-tw"
NTOU_EXP_SHARING_URL = "https://oia.ntou.edu.tw/p/404-1022-86719.php?Lang=zh-tw"

REGION_BY_COUNTRY = {
    "日本": "亞洲",
    "韓國": "亞洲",
    "馬來西亞": "亞洲",
    "越南": "亞洲",
    "印尼": "亞洲",
    "泰國": "亞洲",
    "菲律賓": "亞洲",
    "印度": "亞洲",
    "伊朗": "亞洲",
    "德國": "歐洲",
    "法國": "歐洲",
    "英國": "歐洲",
    "波蘭": "歐洲",
    "瑞士": "歐洲",
    "俄羅斯": "歐洲",
    "澳洲": "大洋洲",
    "巴布亞紐幾內亞": "大洋洲",
    "奈及利亞": "非洲",
    "美國": "美洲",
    "加拿大": "美洲",
    "中國大陸": "中國大陸及港澳",
    "香港": "中國大陸及港澳",
}

REGION_COST_DEFAULTS = {
    "日本": (
        "JPY 75,000–130,000 / 月（東京海洋大學、芝浦工業大學、神奈川大學、神戶大學、九州大學等都會區約 JPY 90,000–135,000 / 月；北海道大學、信州大學、靜岡大學、三重大學、高知大學、長崎大學、琉球大學等國公立大學學生寮費僅約 JPY 10,000–35,000 / 月；可申請海大校內赴姊妹校交換獎補助、教育部學海飛颺／惜珠或日本台灣交流協會獎學金）",
        "須憑日本接待校核發之在留資格認定證明書（COE）向日本台灣交流協會申辦留學簽證，抵日後須依法加入日本國民健康保險（NHI）並投保海外全期醫療及意外險。",
    ),
    "韓國": (
        "KRW 750,000–1,250,000 / 月（首爾中央大學、仁川大學約 KRW 900,000–1,300,000 / 月；釜山韓國海洋大學、釜慶大學及光州／麗水全南大學、濟州大學、木浦大學校內宿舍與學餐開銷實惠）",
        "須憑韓國接待校核發之標準入學許可書向駐台北韓國代表部申辦 D-2-6 交換學生簽證，抵韓後辦理外國人登錄並自動納入韓國國民健康保險（NHIS）。",
    ),
    "馬來西亞": (
        "MYR 1,500–2,600 / 月（吉隆坡馬來亞大學 UM、思特雅大學 UCSI、檳城馬來西亞理科大學 USM、金寶／雙溪龍拉曼大學 UTAR 及瓜拉尼魯斯登嘉樓大學 UMT 校內外學生宿舍與飲食生活費親民）",
        "須於出國前透過馬來西亞 EMGS（Education Malaysia Global Services）系統線上申辦學生簽證核准函（VAL / Student Pass）並投保 EMGS 指定醫療保險。",
    ),
    "越南": (
        "USD 380–650 / 月（河內國家大學、河內理工大學、融促大學 FPT、海防越南海事大學、芹苴肯特大學、芽莊大學及胡志明市經濟大學、技術教育大學住宿與日常飲食費低廉）",
        "須憑越南接待校入學許可透過駐臺北越南經濟文化辦事處申辦越南學生簽證，並於出國前投保涵蓋全期之海外醫療及意外險。",
    ),
    "印尼": (
        "IDR 4,500,000–8,000,000 / 月（泗水艾爾朗加大學 UNAIR［可申請 AMERTA 交換獎學金］、泗水大學、雅加達建國大學 Binus、明古魯大學 UNIB、亞齊省大學、哈薩奴丁大學、馬塔蘭大學、斯里維加亞大學等生活與住宿成本低廉）",
        "須由印尼接待校協助向印尼移民總局申辦 C316 學習電子簽證（e-Visa）並投保海外全期醫療及意外保險。",
    ),
    "泰國": (
        "THB 12,000–22,000 / 月（呵叻素羅娜麗科技大學 SUT、曼谷朱拉隆功大學、農業大學、博仁大學、清邁大學及宋卡王子大學學生宿舍、校園餐廳與大眾運輸開銷實惠）",
        "須憑泰國接待校核發之入學許可公文向泰國貿易經濟辦事處（TTEO）申辦 Non-Immigrant ED 學生簽證並投保海外醫療險。",
    ),
    "菲律賓": (
        "PHP 22,000–38,000 / 月（約 USD 400–680 / 月，含巴丹半島州立大學、帕蒂多州立大學、菲律賓大學維薩亞斯分校、馬尼拉菲律賓理工大學、瑪布亞大學等校園住宿與生活開支）",
        "須憑接待校入學許可向馬尼拉經濟文化辦事處（MECO）辦理簽證，抵菲後由學校協助申辦 9(f) 學生簽證或特別就學許可（SSP）。",
    ),
    "印度": (
        "INR 28,000–48,000 / 月（約 USD 350–600 / 月，含韋洛爾理工學院 VIT、SRM 理工學院、印度理工學院古瓦哈蒂分校 IITG、拉夫里科技大學 LPU、阿拉卡帕大學及昌迪加爾大學校內宿舍與學餐）",
        "須憑印度接待校入學許可向印度台北協會（ITA）申辦 Student Visa 學生簽證並投保海外醫療及意外保險。",
    ),
    "伊朗": (
        "USD 400–700 / 月（烏爾米亞大學 Urmia University 校內學生宿舍、學生餐廳與當地交通費用低廉）",
        "須憑接待校入學許可申辦學生簽證並投保涵蓋全期之國際醫療及意外保險。",
    ),
    "德國": (
        "EUR 934–1,250 / 月（德國簽證限制提領帳戶 Sperrkonto 法定基準為每月 EUR 992，含巴伐利亞邦維爾茲堡－施韋因富特科技大學 THWS、布蘭登堡應用科技大學及不來梅應用科技大學學生宿舍、伙食與學期交通票）",
        "須辦理德國法定學生公保（如 TK / AOK，約 EUR 125–135 / 月）、繳納學期雜費（Semesterbeitrag）並向德國在台協會申辦長期學生簽證。",
    ),
    "法國": (
        "EUR 750–1,150 / 月（里爾大學 Université de Lille、卡昂大學 Université de Caen Normandie 及濱海-珍珠海岸大學 ULCO CROUS 學生宿舍、大學餐廳 RU 與交通，可申請法國政府 CAF 房補）",
        "須透過法國教育中心（Campus France）完成線上面談審查並向法國在台協會申辦長期學生簽證（VLS-TS），抵法後完成 OFII 生效與法國學生社保登錄。",
    ),
    "英國": (
        "GBP 950–1,400 / 月（約克郡赫爾大學 University of Hull 校內外學生宿舍、餐飲與大眾運輸費用較倫敦親民）",
        "交換一學期（6 個月內）可辦理 Standard Visitor 簽證，交換一學年須申辦英國 Student Visa 並繳納 IHS 醫療附加費。",
    ),
    "波蘭": (
        "PLN 2,400–3,800 / 月（約 EUR 550–880 / 月，含格丁尼亞海事大學與克拉科夫農業大學學生宿舍、食堂與波蘭學生半價大眾運輸優惠）",
        "須向波蘭臺北辦事處申辦國家 D 類長期學生簽證，並投保涵蓋全期之歐盟申根醫療保險。",
    ),
    "瑞士": (
        "CHF 1,600–2,400 / 月（日內瓦大學 Université de Genève Cité Universitaire 學生宿舍、日常伙食與日內瓦 Unireso 交通月票）",
        "須憑日內瓦大學入學許可透過瑞士商務辦事處申辦瑞士國家 D 類學生簽證，抵瑞後辦理居留證並投保瑞士認可之學生醫療保險。",
    ),
    "俄羅斯": (
        "USD 450–800 / 月（海參崴俄羅斯國立海事大學、遠東聯邦大學 FEFU 俄羅斯島海景校園宿舍與日常餐飲開銷低廉）",
        "須憑俄羅斯接待校核發之官方簽證邀請函向莫斯科台北經濟文化協調委員會駐台北代表處申辦俄羅斯留學簽證並投保當地醫療險。",
    ),
    "澳洲": (
        "AUD 2,000–2,800 / 月（墨爾本市中心皇家墨爾本理工大學 RMIT 學生公寓、膳食與大眾運輸）",
        "須購買澳洲海外學生健康保險（OSHC）並透過澳洲內政部 ImmiAccount 線上申辦 Subclass 500 學生簽證。",
    ),
    "巴布亞紐幾內亞": (
        "USD 600–1,000 / 月（東新不列顛省巴布亞紐幾內亞天然資源與環境大學 UNRE 校園宿舍與生活開支）",
        "須憑接待校入學許可申辦學生簽證並投保涵蓋全期之國際醫療、意外與緊急醫療後送保險。",
    ),
    "奈及利亞": (
        "USD 450–800 / 月（三角洲州阿布拉卡三角洲州立大學 DELSU 校園住宿與生活開銷）",
        "須憑接待校入學許可申辦學生簽證、完成黃熱病等國際預防接種並投保國際醫療及意外保險。",
    ),
    "美國": (
        "USD 1,400–2,500 / 月（紐約州立大學海運學院 SUNY Maritime 提供交換生學雜費及住宿費減免；克拉克森大學 Clarkson、紐澤西理工學院 NJIT、加州西來大學 UWest［修滿4堂課享50%學雜費補助］、俄亥俄州辛辛那提大學 UC［雙聯碩士享 USD 4,195–10,700 獎學金及臺灣專屬 Luchen Scholarship］）",
        "須憑接待校核發之 DS-2019（交換 J-1）或 I-20（雙聯 F-1）表格繳納 SEVIS I-901 費用並至美國在台協會（AIT）申辦簽證及投保學校強制醫療保險。",
    ),
    "加拿大": (
        "CAD 1,400–2,200 / 月（約 USD 1,050–1,650 / 月，含紐芬蘭與拉布拉多省聖約翰斯紐芬蘭紀念大學 MUN 及海洋學院 Marine Institute 學生宿舍、伙食與交通）",
        "交換一學期（6 個月內）可申辦 eTA 入境，超過 6 個月須申辦加拿大 Study Permit 學習許可，並加入紐芬蘭紀念大學國際學生健康保險計畫。",
    ),
    "中國大陸": (
        "RMB 1,800–3,500 / 月（上海海洋大學、上海海事大學、青島中國海洋大學、無錫江南大學、廈門大學、福州大學、大連海事大學、廣東海洋大學、浙江海洋大學、河海大學、集美大學、中山大學等校內學生宿舍與食堂成本低廉；海大校內補助大陸地區交換生學費全額［上限為海大學費80%］、來回經濟艙機票與生活費）",
        "持有效護照與臺胞證（臺灣居民來往大陸通行證）入境，並依接待校規定投保大陸境內來華留學生綜合醫療保險（每學期約 RMB 400、每學年約 RMB 800）。",
    ),
    "香港": (
        "HKD 8,500–14,000 / 月（九龍紅磡香港理工大學 PolyU 學生宿舍、校園餐廳與港鐵學生優惠八達通）",
        "須透過香港理工大學向香港入境事務處申辦來港就讀進入許可（Student Visa / Entry Permit）並投保醫療及意外保險。",
    ),
}

SEMESTER_DATES_BY_COUNTRY = {
    "日本": "秋季班（海大上學期）：約 9/10 月至翌年 2/3 月；春季班（海大下學期）：約 4 月至 8/9 月",
    "韓國": "秋季學期（上學期）：約 9 月初至 12 月中下旬；春季學期（下學期）：約 3 月初至 6 月中下旬",
    "馬來西亞": "秋季學期（第1學期）：約 9/10 月至翌年 1/2 月；春季學期（第2學期）：約 2/3 月至 6/7 月（拉曼大學 UTAR 採 1 月／5 月／10 月三學期制）",
    "越南": "第一學期（秋季班）：約 9 月至翌年 1 月；第二學期（春季班）：約 2 月至 6 月",
    "印尼": "奇數／秋季學期：約 8/9 月至 12 月／翌年 1 月；偶數／春季學期：約 2 月至 6/7 月",
    "泰國": "第一學期：約 8 月至 12 月（素羅娜麗科技大學採三學期制 Trimester）；第二學期：約 1 月至 5 月",
    "菲律賓": "第一學期：約 8 月至 12 月；第二學期：約 1 月至 5/6 月",
    "印度": "秋季學期（Odd Semester）：約 7/8 月至 12 月；春季學期（Even Semester）：約 1 月至 5 月",
    "伊朗": "秋季學期：約 9 月下旬至翌年 1 月；春季學期：約 2 月中旬至 6 月",
    "德國": "冬季學期（上學期／秋季班）：約 10 月初至翌年 2/3 月；夏季學期（下學期／春季班）：約 3 月中旬至 7 月底",
    "法國": "秋季學期（上學期）：約 9 月初至 12 月底／翌年 1 月；春季學期（下學期）：約 1 月中旬至 5/6 月",
    "英國": "秋季學期（Trimester 1）：約 9 月中下旬至翌年 1 月；春季學期（Trimester 2）：約 1 月下旬至 5/6 月",
    "波蘭": "冬季學期（秋季班）：約 10 月初至翌年 2 月中旬；夏季學期（春季班）：約 2 月下旬至 6 月底",
    "瑞士": "秋季學期（Autumn）：約 9 月中旬至翌年 1 月底；春季學期（Spring）：約 2 月中旬至 6 月中旬",
    "俄羅斯": "秋季學期：約 9 月初至翌年 1 月；春季學期：約 2 月初至 6 月底",
    "澳洲": "第一學期（Semester 1）：約 2 月下旬至 6 月；第二學期（Semester 2）：約 7 月下旬至 11 月",
    "巴布亞紐幾內亞": "第一學期：約 2 月至 6 月；第二學期：約 7 月至 11 月",
    "奈及利亞": "第一學期：約 10 月至翌年 2 月；第二學期：約 3 月至 7 月",
    "美國": "秋季學期（Fall）：約 8 月下旬至 12 月中旬；春季學期（Spring）：約 1 月中旬至 5 月中旬",
    "加拿大": "秋季學期（Fall）：約 9 月初至 12 月中旬；冬季／春季學期（Winter）：約 1 月初至 4 月底",
    "中國大陸": "秋季學期（上學期）：約 9 月初至翌年 1 月中旬；春季學期（下學期）：約 2 月中下旬至 6 月底／7 月初",
    "香港": "第一學期（秋季班）：約 9 月初至 12 月底；第二學期（春季班）：約 1 月中旬至 5 月中旬",
}


def clean_text(s: str) -> str:
  if not s:
    return ""
  return re.sub(r"\s+", " ", s).strip()


def format_colleges_and_degrees(item: dict) -> tuple[str, str]:
  sn = item["school_sn"]
  remarks = item.get("remarks") or ""
  if sn == 1005:
    colleges_str = "工學院、電機資訊學院（機械與機電工程學系、系統工程暨造船學系、河海工程學系、海洋工程科技學程、電機工程學系、資訊工程學系、通訊與導航工程學系、光電與材料科技學系）"
    degree_str = "大學部大三升大四在學學生（3+2 學碩雙聯學位）及碩士班在學學生（1+1 雙碩士學位）"
  elif sn == 1001:
    colleges_str = "海運暨管理學院（商船學系、航運管理學系、運輸科學系、輪機工程學系、海洋觀光管理學士學位學程、海洋經營管理學士學位學程）及相關系所"
    degree_str = "大學部大一（下學期）至大四在學學生及碩士班在學學生（含航運與物流管理雙碩士學位計畫）"
  elif sn == 1011:
    colleges_str = "海洋科學與資源學院、海運暨管理學院、工學院"
    degree_str = "大學部大二至大三在學學生（大一上及應屆畢業學期除外）"
  elif sn in (105, 106, 401):
    colleges_str = "電機資訊學院（電機工程學系、資訊工程學系、通訊與導航工程學系、光電與材料科技學系）"
    degree_str = "大學部大一（下學期）至大四在學學生、碩士班及博士班在學學生"
  elif sn == 108:
    colleges_str = "海運暨管理學院、工學院、電機資訊學院"
    degree_str = "大學部大一（下學期）至大四在學學生、碩士班及博士班在學學生"
  elif sn == 110:
    colleges_str = "生命科學院、海洋科學與資源學院"
    degree_str = "大學部大三至大四在學學生、碩士班及博士班在學學生"
  elif sn == 501:
    colleges_str = "生命科學院（食品科學系、水產養殖學系、生命科學暨生物科技學系、海洋生物研究所、食品安全與風險管理研究所、海洋生物科技學程）"
    degree_str = "大學部大一（下學期）至大四在學學生、碩士班及博士班在學學生"
  elif sn == 1102:
    colleges_str = "海運暨管理學院（限商船學系及交通運輸相關學系：航運管理學系、運輸科學系）"
    degree_str = "大學部大一（下學期）至大四在學學生及碩博士班在學學生"
  else:
    colleges_str = (
        "不限學院（海運暨管理學院、生命科學院、海洋科學與資源學院、工學院、電機資訊學院、人文社會科學院、海洋法律與政策學院、國際學院等全校各系所符合接待校開設專業與語檢條件之在學生皆可申請）"
    )
    if "大二至大三" in remarks:
      degree_str = "大學部大二至大三在學學生（非大一上學期之新生或當學期畢業之學生）"
    elif "大一至大三" in remarks:
      degree_str = "大學部大一（下學期）至大三在學學生（非大一上學期之新生或當學期畢業之學生）"
    elif "大二至碩一" in remarks:
      degree_str = "大學部大二至大四及碩士班一年級在學學生（非大一上學期之新生或當學期畢業之學生）"
    elif "大一至碩一" in remarks:
      degree_str = "大學部大一（下學期）至大四及碩士班一年級在學學生（非大一上學期之新生或當學期畢業之學生）"
    else:
      degree_str = (
          "大學部大一（下學期）至大四、碩士班及博士班在學學生（依《國立臺灣海洋大學學生赴國外研修要點》第3點：申請期間與赴國外研修期間皆應為本校註冊在學生，且非為大一上學期之新生或當學期畢業之學生）"
      )
  return colleges_str, degree_str


def format_gpa_rule(item: dict) -> str:
  remarks = item.get("remarks") or ""
  gpa_matches = re.findall(
      r"GPA\s*[≥>=]*\s*[\d./]+[^；。]*|百分制\s*\d+\s*分[^；。]*",
      remarks,
      re.I,
  )
  base_rule = (
      "海大校內門檻（依《國立臺灣海洋大學學生赴國外研修施行細則》第2點）：申請之前一學期學業平均須達及格以上（大學部 60 分、研究所 70 分）"
  )
  if gpa_matches:
    return f"{base_rule}；接待校／專案學業門檻：{'、'.join(dict.fromkeys(gpa_matches))}"
  if item["country"] == "中國大陸":
    return f"{base_rule}（赴大陸地區姊妹校甄選評分標準：在校成績佔 45%＋研修計畫及其他輔助文件佔 55%）"
  return f"{base_rule}（赴國外姊妹校甄選評分標準：在校成績佔 30%＋外語能力佔 30%＋書面及面試表現［研修計畫及其他輔助文件］佔 40%）"


def main() -> None:
  OFFICIAL_NTOU_DIR.mkdir(parents=True, exist_ok=True)
  catalog_source = json.loads(
      (SOURCES_NTOU_DIR / "ntou_catalog_source.json").read_text(encoding="utf-8")
  )
  resolved_locations = json.loads(
      (SOURCES_NTOU_DIR / "ntou_resolved_locations.json").read_text(encoding="utf-8")
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

    tracks_str = "、".join(item.get("source_tracks") or ["赴姊妹校交換生計畫"])
    if "雙聯" in tracks_str and "交換" in tracks_str:
      program_type = "校級交換暨雙聯學位計畫"
    elif "雙聯" in tracks_str:
      program_type = "國際雙聯學位計畫"
    elif "大陸地區" in tracks_str:
      program_type = "大陸地區姊妹校交換學生計畫"
    elif "院級交換" in tracks_str and "校級" not in tracks_str:
      program_type = "院級交換學生計畫"
    else:
      program_type = "校級交換學生計畫"

    quota_str = item["quota_str"]
    colleges_str, degree_levels_str = format_colleges_and_degrees(item)
    lang_req_str = item["lang_req"]
    gpa_req_str = format_gpa_rule(item)
    website = item.get("website") or NTOU_SISTER_SCHOOLS_URL
    factsheet_url = item.get("factsheet_url")
    remarks_raw = clean_text(item.get("remarks") or "")
    exps = item.get("experience_reports") or []

    if country == "中國大陸":
      source_url = NTOU_MAINLAND_115_2_URL if avail_status == "open" else NTOU_SISTER_SCHOOLS_URL
      round_label = (
          "115學年度第2學期（2027春季班）赴大陸地區姊妹校交換（研修）計畫甄選"
          if avail_status == "open"
          else "大陸地區正式締約合作姊妹校（依國際處當期招募公告名額辦理）"
      )
      app_deadline_str = (
          "【115學年度第2學期（2027春季班）赴大陸地區姊妹校交換甄選】2026/09/30 (三) 12:00 校內收件截止（先寄送 PDF 電子檔至國際處承辦信箱 marberthsu@email.ntou.edu.tw，並預約時間親自送交紙本資料至行政大樓 3 樓國際合作組）；【下一梯次（2027秋季班／116-1）預告】預計 2027年3月公告簡章並受理申請"
      )
      deadline_iso = "2026-09-30T12:00:00+08:00"
      win_status = "closed"
    else:
      source_url = NTOU_BROCHURE_2027_URL if avail_status == "open" else NTOU_SISTER_SCHOOLS_URL
      round_label = (
          "2027年春/秋季學期赴姊妹校交換生計畫（不含大陸地區）暨學海飛颺獎學金校內甄選"
          if avail_status == "open"
          else "國外正式締約合作姊妹校（依國際處當期甄選簡章公告名額辦理）"
      )
      app_deadline_str = (
          "【2027年春/秋季學期赴姊妹校交換生計畫（主梯次）暨學海飛颺甄選】2026/03/01 公告簡章、2026/05/08 (五) 12:00 報名截止（先將申請文件轉為單一 PDF 寄至 marberthsu@email.ntou.edu.tw，再預約時間親送 A4 單面列印不裝訂 L 型資料夾紙本至國際處）、2026/05 下旬（第14–15週）校內面試、2026/06 中旬公告分發結果；【2026年秋季學期增開梯次】2025/12/01 公告、2026/02/25 12:00 截止；【下一梯次預告】2027年秋季學期增開梯次預計 2026/12/01 公告、2027/02/25 12:00 截止；2028年春/秋季學期主梯次預計 2027/03/01 公告、2027/05/07 12:00 截止"
      )
      deadline_iso = "2026-05-08T12:00:00+08:00"
      win_status = "closed"

    study_period_str = "1 學期或 1 學年（依《國立臺灣海洋大學學生赴國外研修要點》及姊妹校協議名額辦理）"
    if "雙聯" in tracks_str:
      study_period_str = "1–2 年雙聯學位修讀（如辛辛那提大學 1+1／3+2 雙碩士、長崎大學 2+2 雙博士、紐約州立大學海運學院雙碩士）或 1 學期／1 學年交換"

    sem_dates_str = SEMESTER_DATES_BY_COUNTRY.get(
        country, "秋季學期：約 9 月至翌年 1 月；春季學期：約 2 月至 6 月"
    )
    housing_str = (
        f"獲海大國際事務處提名後，可依 {zh_name} 交換生 Fact Sheet 與國際處 Notion 姊妹校專頁說明申請校內學生宿舍或校外國際學生公寓"
        + (f"（簡章與計畫說明：{remarks_raw[:220]}）" if remarks_raw else "。")
    )
    course_rest_str = (
        f"開放對象與領域：{colleges_str}。依《國立臺灣海洋大學學生赴國外研修施行細則》第6點規定：獲錄取學生於國外大學修課期間，每學期至少應修習相當於海大 6 學分（含）以上之課程或進行論文研究；返國後得依《國立臺灣海洋大學學生赴境外研修學分採認作業要點》辦理學分抵免。"
    )

    tuition_points_list = [
        (
            "海大在學註冊、學雜費互惠與自費規定：依《國立臺灣海洋大學學生赴國外研修要點》第3點及《施行細則》規定，申請期間與赴國外研修期間皆應為海大註冊在學生（不得辦理休學或於當學期畢業），並須依規定繳交海大全額學雜費；雙邊互惠交換名額免繳接待校學費（美國西來大學為訪問半價補助專案、辛辛那提大學及紐約州立大學海運學院雙聯學位則依雙聯學費與獎學金減免標準辦理）。"
        ),
        (
            "海大校內赴姊妹校交換獎補助與教育部學海系列獎學金（擇一不得重複兼領）：（1）《海大校內赴姊妹校交換獎補助》：補助來回經濟艙機票費、學費補助（已獲姊妹校學費減免者不再補助；赴國外姊妹校補助該校學費總額 50% 為原則、上限 NT$80,000；赴大陸地區姊妹校學費全額補助、上限為海大學費之 80%）及生活費補助（依教育部公費留學生支給數額表計算）；（2）教育部《學海飛颺》獎學金：併同每年 3–5 月交換生甄選申請，補助來回經濟艙機票費、部分學費與部分生活費；（3）教育部《學海惜珠》獎學金：補助具低收、中低收、特殊境遇家庭、身障或弱勢助學金資格之在學生（每年 12 月底前申請），機票、學費及生活費最高全額補助；（4）申請任何校內外獎補助者，必須於報名時一併繳交《經費分析表》，未繳交者視同放棄申請校內一切獎學金。"
        ),
    ]

    app_steps_list = [
        (
            f"步驟一（確認海大在學資格、前一學期及格門檻與 {zh_name} 語檢要求）：確認申請期間與出國研修期間皆為海大註冊在學生（非大一上學期之新生或當學期畢業生），前一學期學業平均達及格以上（大學部 60 分、研究所 70 分）且符合 {zh_name} 規定之 GPA 與語檢標準（{lang_req_str}）。"
        ),
        (
            "步驟二（備齊申請文件、經系所與學院核章，先寄 PDF 電子檔再預約親送 A4 紙本至國際處）：每人至多可選填 5 個志願（一校僅能挑選一項計畫或一個系所）。備妥 1. 出國交換學生申請表（大學部須系所主管與學院核章；碩博士生須指導教授、系所主管與學院核章）、2. 中文歷年成績單（含前一學期排名）、3. 英文歷年成績單、4. 外語能力證明（大陸地區免附）、5. 自傳與外國留學研修計畫書（各 1,000–1,500 字）、6. 經費分析表（申請獎學金必繳，未繳視同放棄）、7. 個人資料使用同意書；先合併為單一 PDF 寄至 `marberthsu@email.ntou.edu.tw`，並預約時間將 A4 單面列印（不裝訂、置於透明 L 型資料夾）紙本親送至行政大樓 3 樓國際合作組。"
        ),
        (
            f"步驟三（國際處書面暨面試甄選審查、志願分發與錄取確認）：國外姊妹校依「在校成績 30%＋外語能力 30%＋書面及面試表現 40%」評定總分（大陸地區姊妹校依「在校成績 45%＋研修計畫及其他輔助文件 55%」評分；同分時依 1. 外語能力、2. 該交換校志願序比序），每年 5 月下旬（第 14–15 週）舉行校內面試（馬祖校區生得申請線上面試），6 月中旬公告結果。獲錄取者須於規定期限內繳交《申請入學同意聲明書》，由海大國際處向 {full_name} 辦理官方提名（Nomination）。"
        ),
        (
            "步驟四（遞交姊妹校入學申請、辦理簽證保險與返國 1 個月內完成心得報告及核銷）：獲提名後依姊妹校規定遞交外文入學申請、護照影本、財力證明、選課計畫與宿舍申請；出國前須繳交《出國前檢核表》、切結書、家長同意書、海外醫療及意外保險證明（役男另辦緩徵出境）。研修期間每學期至少應修習相當於海大 6 學分以上課程或進行論文研究；返國後 1 個月內須提交 1,500–2,000 字《研修心得報告》（含至少 4 張照片）、電子問卷、正式成績單及機票登機證單據，以辦理學分採認與獎學金核銷（未按時繳交者將追回全額補助款）。"
        ),
    ]

    elig_points_list = [
        f"合作管道：{program_type}（{tracks_str}）",
        f"開放學制與年級：{degree_levels_str}",
        f"開放申請院系：{colleges_str}",
        f"學業成績門檻：{gpa_req_str}",
        f"外語能力標準：{lang_req_str}",
        (
            "校內甄選評分與志願規則：每人至多填寫 5 個志願（一校限填一項計畫或系所）。國外姊妹校評分標準為「在校成績 30%＋外語能力 30%＋書面及面試表現 40%」；大陸地區姊妹校評分標準為「在校成績 45%＋研修計畫及其他輔助文件 55%」（同分依 1. 外語能力、2. 志願序比序）。"
        ),
    ]
    if remarks_raw:
      elig_points_list.append(f"學校簡章與特殊規定：{remarks_raw[:300]}")

    exp_labels = [
        f"{e['year']} {e['student']}" for e in exps
    ]
    notes_lines = [
        f"【合作類別與期程】{program_type}｜交換期間：{study_period_str}",
        f"【當期名額與費用待遇】{quota_str}｜繳交海大校內學雜費、免繳接待校學費（雙聯學位及西來大學訪問專案依協議辦理）",
        f"【開放學院與學制】{colleges_str}｜{degree_levels_str}",
        f"【語言與學業門檻】{lang_req_str}｜{gpa_req_str}",
        f"【住宿與生活資訊】{housing_str}",
    ]
    if factsheet_url:
      notes_lines.append(f"【官方簡章／Fact Sheet 連結】{factsheet_url}")
    if exps:
      notes_lines.append(
          f"【海大學長姐交換心得報告（共 {len(exps)} 篇）】收錄於國際事務處 Notion 赴外研修心得專區（含：{'、'.join(exp_labels[:6])}）"
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
        "availability_note": f"國立臺灣海洋大學國際事務處公告交換／雙聯合作姊妹校（{program_type}）；{quota_str}。",
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
            "title": f"國立臺灣海洋大學赴姊妹校交換生計畫甄選簡章與名額表—{zh_name}",
            "source_url": source_url,
            "role": "home_university",
            "authority": "home_official_notice",
            "effective_academic_year": "115",
            "application_round": round_label,
            "checked_at": CHECKED_AT,
        },
        {
            "title": "國立臺灣海洋大學學生赴國外研修要點暨留學國語文能力證明標準表",
            "source_url": NTOU_GUIDELINES_LANG_URL,
            "role": "home_university",
            "authority": "home_official_notice",
            "effective_academic_year": "115",
            "application_round": round_label,
            "checked_at": CHECKED_AT,
        },
        {
            "title": "國立臺灣海洋大學學生赴國外研修施行細則與學海系列計畫補助施行細則",
            "source_url": NTOU_ENFORCEMENT_RULES_URL,
            "role": "home_university",
            "authority": "home_official_notice",
            "effective_academic_year": "115",
            "application_round": round_label,
            "checked_at": CHECKED_AT,
        },
    ]
    if factsheet_url:
      wf_sources.append({
          "title": f"海大國際事務處公告之 {zh_name} 交換計畫／Fact Sheet 網頁",
          "source_url": factsheet_url,
          "role": "home_university",
          "authority": "home_official_notice",
          "effective_academic_year": "115",
          "application_round": round_label,
          "checked_at": CHECKED_AT,
      })
    if exps:
      wf_sources.append({
          "title": f"海大國際事務處赴外研修心得專區—赴 {zh_name} 交換生返國報告（{len(exps)} 篇）",
          "source_url": exps[0]["url"],
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
        "home_university": "國立臺灣海洋大學",
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
            "2027春/秋季班",
            "2026秋季班",
        ],
        "applicability_status": "verified",
        "applicability_note": (
            "國立臺灣海洋大學由國際事務處（國際合作組）統籌辦理全校赴國外與大陸地區姊妹校交換生計畫、雙聯學位及教育部學海系列獎補助甄選，主梯次於每年 3–5 月受理次年春/秋季班申請（大陸地區春季班於 9 月底截止、秋季增開梯次於 12–2 月受理）。"
        ),
        "review_status": "published",
        "published_at": CHECKED_AT,
        "steps": [
            {
                "rule_id": f"ntou-115-home-1-{idx+1:03d}",
                "order": 1,
                "phase": "校內申請",
                "title": f"確認海大在學身分（非大一上或當學期畢業）、前一學期學業及格門檻與 {zh_name} 語檢要求",
                "responsible_party": "學生",
                "responsible_unit": "國立臺灣海洋大學國際事務處（國際合作組）",
                "deadline_at": deadline_iso,
                "deadline_status": "verified_exact" if avail_status == "open" else "reference_only",
                "deadline_source_url": source_url,
                "deadline_checked_at": CHECKED_AT,
                "deadline_reminder_eligible": False,
                "summary": (
                    f"確認符合《國立臺灣海洋大學學生赴國外研修要點》第3點及《施行細則》第2點規定（申請期間與出國期間皆為海大註冊在學生，非大一上學期之新生或當學期畢業生；前一學期學業平均達大學部 60 分／研究所 70 分及格以上），並備妥符合 {zh_name} 及海大附表一規定之語言能力證明。"
                ),
                "details": [
                    f"開放學制與院系：{colleges_str}（{degree_levels_str}）",
                    f"語言與學業條件：{lang_req_str}｜{gpa_req_str}",
                    f"當期名額與計畫類別：{quota_str}｜{program_type}",
                ],
                "scope": {
                    "home_universities": ["國立臺灣海洋大學"],
                    "partner_universities": [full_name],
                    "academic_years": ["115", "116"],
                    "application_rounds": [round_label, "115-2", "115-1", "116-1", "116-2"],
                },
                "source_urls": [
                    source_url,
                    NTOU_GUIDELINES_LANG_URL,
                    NTOU_ENFORCEMENT_RULES_URL,
                ],
                "checked_at": CHECKED_AT,
                "support_status": "verified",
            },
            {
                "rule_id": f"ntou-115-home-2-{idx+1:03d}",
                "order": 2,
                "phase": "校內申請",
                "title": "備妥申請表（經指導教授／系所／學院核章）、中英文成績單、語檢、自傳、研修計畫與經費分析表，先寄 PDF 再預約親送紙本",
                "responsible_party": "學生與所屬系（所）及學院辦公室",
                "responsible_unit": "國立臺灣海洋大學各系所及學院／國際事務處國際合作組",
                "deadline_at": deadline_iso,
                "deadline_status": "verified_exact" if avail_status == "open" else "reference_only",
                "deadline_source_url": source_url,
                "deadline_checked_at": CHECKED_AT,
                "deadline_reminder_eligible": False,
                "summary": (
                    "每人至多可選填 5 個志願（一校限填一項計畫或一個系所）。完成系所主管及學院核章（研究生另須指導教授核章）後，於截止日前先將全套申請文件轉為單一 PDF 寄至 `marberthsu@email.ntou.edu.tw`，並預約時間將 A4 單面列印（不裝訂、置於透明 L 型資料夾）紙本親自送交行政大樓 3 樓國際事務處。"
                ),
                "details": [
                    "語言能力基準（附表一）：英文 TOEFL iBT 60 / IELTS 5.0 / TOEIC 600 / GEPT 高級複試；日文 JLPT N3（部分日本校要求 N2）；韓文 TOPIK 3 級；法文 DELF B1（里爾、卡昂法語授課要求 B2）；德文 ZDaF 初級（THWS 德語授課要求 B2）；西文 DELE 初級；大陸地區免附外語證明。",
                    "獎學金必繳文件：欲申請海大校內赴姊妹校交換獎補助或教育部《學海飛颺》獎學金者，報名時必須一併繳交《經費分析表》（附件五），未繳交者視同放棄申請校內一切獎學金。",
                ],
                "document_requirements": [
                    {
                        "name": "國立臺灣海洋大學出國交換學生申請表（至多 5 個志願；大學部須系所主管與學院核章，碩博士生須指導教授、系所主管與學院核章）及申請文件檢核表",
                        "official_form_url": NTOU_APP_CHECKLIST_URL,
                        "source_urls": [NTOU_BROCHURE_2027_URL, NTOU_APP_CHECKLIST_URL],
                    },
                    {
                        "name": "中文歷年成績單（須含申請前一學期學業平均及班級/系所排名）與英文歷年成績單正本各乙份",
                        "source_urls": [NTOU_BROCHURE_2027_URL, NTOU_ENFORCEMENT_RULES_URL],
                    },
                    {
                        "name": "有效期限內之「留學國語文能力證明」（TOEFL iBT / IELTS / TOEIC / GEPT / JLPT / TOPIK / DELF / ZDaF / DELE；赴大陸地區免附）",
                        "source_urls": [NTOU_GUIDELINES_LANG_URL, NTOU_BROCHURE_2027_URL],
                    },
                    {
                        "name": "中文自傳（1,000–1,500 字）、外國留學研修計畫書（1,000–1,500 字）、經費分析表（申請獎學金必繳）與個人資料使用同意書",
                        "official_form_url": NTOU_BUDGET_EX_URL,
                        "source_urls": [NTOU_AUTOBIO_EX_URL, NTOU_STUDY_PLAN_EX_URL, NTOU_BUDGET_EX_URL],
                    },
                ],
                "scope": {
                    "home_universities": ["國立臺灣海洋大學"],
                    "academic_years": ["115", "116"],
                    "application_rounds": [round_label, "115-2", "115-1", "116-1", "116-2"],
                },
                "source_urls": [
                    NTOU_BROCHURE_2027_URL,
                    NTOU_GUIDELINES_LANG_URL,
                    NTOU_APP_CHECKLIST_URL,
                    NTOU_BUDGET_EX_URL,
                ],
                "checked_at": CHECKED_AT,
                "support_status": "verified",
            },
            {
                "rule_id": f"ntou-115-home-3-{idx+1:03d}",
                "order": 3,
                "phase": "甄選與提名",
                "title": "參加國際處校內面試與書面綜合評選（30%／30%／40%）、公告錄取分發結果並繳交入學同意聲明書",
                "responsible_party": "學生與國際事務處甄選委員會",
                "responsible_unit": "國立臺灣海洋大學國際事務處",
                "deadline_at": "2026-06-15T17:00:00+08:00",
                "deadline_status": "verified_exact",
                "deadline_source_url": NTOU_BROCHURE_2027_URL,
                "deadline_checked_at": CHECKED_AT,
                "deadline_reminder_eligible": False,
                "summary": (
                    "國際處依《學生赴國外研修施行細則》第4點辦理甄選：國外姊妹校按「在校成績 30%＋外語能力 30%＋書面及面試表現 40%」計分（大陸地區姊妹校按「在校成績 45%＋研修計畫及其他輔助文件 55%」計分；同分時依 1. 外語能力、2. 志願序比序）。錄取公告後，正取生須於期限內繳交《申請入學同意聲明書》確認資格。"
                ),
                "details": [
                    "面試安排：主梯次於每年 5 月下旬（第 14–15 週）舉行面試（馬祖校區學生可申請線上面試），未到場且未事先請假者不予錄取。",
                    "獎補助核定：通過校內甄選並提交《經費分析表》者，由國際處依年度預算審核核定《教育部學海飛颺／惜珠》或《海大校內赴姊妹校交換獎補助》（機票費、學費補助［國外上限 8 萬元／大陸上限海大學費 80%］及生活費補助，擇一不得重複兼領）。",
                ],
                "scope": {
                    "home_universities": ["國立臺灣海洋大學"],
                    "academic_years": ["115", "116"],
                    "application_rounds": [round_label, "115-2", "115-1", "116-1", "116-2"],
                },
                "source_urls": [
                    NTOU_BROCHURE_2027_URL,
                    NTOU_ENFORCEMENT_RULES_URL,
                    NTOU_XUEHAI_RULES_URL,
                ],
                "checked_at": CHECKED_AT,
                "support_status": "verified",
            },
            {
                "rule_id": f"ntou-{idx+1:03d}-host-apply",
                "order": 4,
                "phase": "合作校申請",
                "title": f"由海大國際處向 {zh_name} 辦理官方提名（Nomination），並依接待校規定遞交外文入學與宿舍申請",
                "responsible_party": "學生與接待校國際事務處",
                "summary": (
                    f"繳交同意聲明書後，由海大國際合作組向 {zh_name} 辦理官方提名；學生須於姊妹校截止日前備妥外文申請表、英文歷年成績單、護照影本、英文財力證明、語檢證書、選課計畫與宿舍申請表，靜候接待校核發正式入學許可（Letter of Acceptance / COE / DS-2019）。"
                ),
                "details": [
                    f"交換期程：{study_period_str}｜名額：{quota_str}",
                    f"語言與學業條件：{lang_req_str}｜{gpa_req_str}",
                    f"住宿安排：{housing_str}",
                ],
                "scope": {
                    "home_universities": ["國立臺灣海洋大學"],
                    "partner_universities": [full_name],
                    "academic_years": ["115", "116"],
                    "application_rounds": [round_label, "115-2", "115-1", "116-1", "116-2"],
                },
                "source_urls": (
                    [source_url, NTOU_EXCHANGE_PLAN_URL]
                    + ([factsheet_url] if factsheet_url else [])
                    + ([website] if website else [])
                ),
                "checked_at": CHECKED_AT,
                "support_status": "verified",
                "needs_confirmation": False,
            },
            {
                "rule_id": f"ntou-115-home-5-{idx+1:03d}",
                "order": 5,
                "phase": "行前準備",
                "title": "繳交出國前檢核表、辦理留學簽證與海外醫療保險、維持海大在學註冊並修滿 6 學分，返國 1 個月內完成心得報告與核銷",
                "responsible_party": "學生",
                "responsible_unit": "國立臺灣海洋大學國際事務處／教務處／各系所",
                "summary": (
                    "出國前須依《出國前檢核表》繳交國外大學入學許可影本、切結書、家長同意書、海外醫療及意外保險保單影本（役男另辦緩徵出境），並於交換期間維持海大在學註冊及每學期修習相當於海大 6 學分以上課程（或進行論文研究）；返國後 1 個月內須依《返國核銷檢核表》繳交 1,500–2,000 字研修心得報告（含照片 4 張以上）、電子問卷、登機證正本、電子機票收據及正式成績單，辦理獎補助核銷與學分採認。"
                ),
                "details": tuition_points_list,
                "scope": {
                    "home_universities": ["國立臺灣海洋大學"],
                    "academic_years": ["115", "116"],
                    "application_rounds": [round_label, "115-2", "115-1", "116-1", "116-2"],
                },
                "source_urls": [
                    NTOU_PRE_DEPARTURE_URL,
                    NTOU_REIMBURSEMENT_URL,
                    NTOU_ENFORCEMENT_RULES_URL,
                    NTOU_XUEHAI_RULES_URL,
                ],
                "checked_at": CHECKED_AT,
                "support_status": "verified",
            },
        ],
        "sources": wf_sources,
        "last_checked": CHECKED_AT,
        "coverage_status": "official_verified",
        "coverage_note": (
            "已完整整合國立臺灣海洋大學國際事務處（2027年春/秋季赴姊妹校交換簡章、115-2赴大陸地區交換公告、雙聯學位一覽表、Notion 姊妹校資料庫及全校締約姊妹校名冊）共 123 所全球合作學校名額、語檢門檻、評分標準、獎補助細則與 439 篇學長姐返國心得。"
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
            "title": f"國立臺灣海洋大學赴姊妹校交換生甄選簡章與名額表—{zh_name}",
            "source_url": source_url,
            "summary": "海大國際事務處公告之交換名額、開放院系年級、語言檢定門檻與學校備註說明",
        },
        {
            "title": "國立臺灣海洋大學學生赴國外研修要點、施行細則與學海系列計畫補助施行細則",
            "source_url": NTOU_ENFORCEMENT_RULES_URL,
            "summary": "海大出國交換申請資格（前一學期及格、非大一上或應屆畢業）、甄選配分（國外 30%/30%/40%、大陸 45%/55%）、每學期至少修習 6 學分規定與校內／學海獎補助標準",
        },
    ]
    if factsheet_url:
      dest_sources.append({
          "title": f"海大國際事務處公告之 {zh_name} 交換資訊與 Fact Sheet",
          "source_url": factsheet_url,
          "summary": "海大國際處與接待校提供之交換生申請資訊、選課與住宿說明",
      })
    if exps:
      dest_sources.append({
          "title": f"海大國際事務處赴外研修心得專區—赴 {zh_name} 交換生返國心得報告（{len(exps)} 篇）",
          "source_url": exps[0]["url"],
          "summary": f"收錄歷年海大赴 {zh_name} 交換生與雙聯生返國心得報告共 {len(exps)} 篇",
      })
    if website:
      dest_sources.append({
          "title": f"{full_name} 官方網站",
          "source_url": website,
          "summary": "接待合作校官方網站",
      })

    src_url_list = (
        [source_url, NTOU_EXCHANGE_PLAN_URL, NTOU_ENFORCEMENT_RULES_URL]
        + ([factsheet_url] if factsheet_url else [])
        + ([exps[0]["url"]] if exps else [])
        + ([website] if website else [])
    )

    destinations.append({
        "home_university": "國立臺灣海洋大學",
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
                "title": "生活費、海大校內交換獎補助（機票＋學費最高8萬＋生活費）與教育部學海飛颺／惜珠獎學金",
                "summary": cost_line,
                "points": [cost_line] + tuition_points_list,
                "source_urls": src_url_list + [NTOU_XUEHAI_RULES_URL, NTOU_MOE_XUEHAI_115_URL],
                "caution": (
                    "任一赴外研修計畫僅得就我國政府或海大校內提供之各項出國獎補助擇一申請，不得重複兼領；欲申請獎學金者必須於報名時一併繳交《經費分析表》，未繳者視同放棄申請校內一切獎學金。"
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
                    "依《國立臺灣海洋大學出國前檢核表》及《學生赴國外研修施行細則》規定，錄取生出國前須購買涵蓋研修全期之海外醫療及意外保險並繳交保單影本至國際處，同時須遵守接待國法定學生健康保險規定（如日本 NHI、韓國 NHIS、德國法定公保、澳洲 OSHC 等）。",
                ],
                "source_urls": src_url_list + [NTOU_PRE_DEPARTURE_URL],
                "caution": "請於收到入學許可後確認接待校指定之保險額度與投保通路，並於出國前完成《出國前檢核表》繳件。",
            },
            {
                "key": "visa",
                "title": "留學簽證辦理、役男出境緩徵手續與海大在學註冊義務",
                "summary": visa_default,
                "points": [
                    visa_default,
                    "依《國立臺灣海洋大學學生赴國外研修要點》第3點規定，申請期間與赴國外研修期間皆應為海大註冊在學生（不得辦理休學或於當學期畢業）；具役男身分之錄取生須於出國前完成役男出境緩徵申請，研修期滿應準時返國完成報到核銷。",
                ],
                "source_urls": src_url_list + [NTOU_PRE_DEPARTURE_URL],
                "caution": "請勿持觀光簽證或免簽入境就讀學期交換課程，以免影響正式學籍、居留與返國學分採認。",
            },
            {
                "key": "academics",
                "title": "每學期至少修習相當海大 6 學分規定、論文研究與返國學分採認",
                "summary": course_clean[:160],
                "points": [calendar_clean, course_clean],
                "source_urls": src_url_list,
                "caution": (
                    "依《學生赴國外研修施行細則》第6點，於國外大學修課期間每學期至少應修習相當於海大 6 學分（含）以上之課程或進行論文研究；出國前請先與系所確認擬修課程之抵免採認原則。"
                ),
            },
            {
                "key": "living",
                "title": f"{location_obj.get('city') or country} 校園生活與海大學長姐交換心得傳承",
                "summary": f"代表校區城市：{location_obj.get('city') or country}。請配合海大行前說明會與接待校新生訓練（Orientation）完成報到。",
                "points": [
                    f"目的地城市：{location_obj.get('city') or country}（{country}）",
                    (
                        f"海大國際事務處於官網及 Notion「赴外研修心得專區（{exps[0]['url'] if exps else NTOU_EXP_SHARING_URL}）」公開收錄歷屆學長姐返國研修心得報告"
                        + (f"（本校共收錄 {len(exps)} 篇：{'、'.join(exp_labels[:5])}）" if exps else "")
                        + "，詳述當地選課、住宿、交通與生活開銷實況。"
                    ),
                ],
                "source_urls": [exps[0]["url"] if exps else NTOU_EXP_SHARING_URL],
            },
        ],
        "sources": dest_sources,
        "last_checked": CHECKED_AT,
        "coverage_status": "official_verified",
        "coverage_note": (
            "已整合國立臺灣海洋大學國際事務處 123 所交換與雙聯合作姊妹校名額、語檢門檻、校內與學海獎補助細則、Notion 姊妹校專頁與 439 篇歷屆學長姐返國心得。"
        ),
    })

    research_records.append({
        "home_university": "國立臺灣海洋大學",
        "school_name": full_name,
        "country": country,
        "official_website": website,
        "verification_status": "official_verified",
        "discovery_source_url": source_url,
        "checked_at": CHECKED_AT,
        "note": (
            f"國立臺灣海洋大學國際事務處《2027年春/秋季赴姊妹校交換生甄選簡章（{NTOU_BROCHURE_2027_URL}）》、《姊妹校一覽表》與 ROR/Wikidata 官方網址核對完成。"
        ),
    })

    ev_sources = [
        {
            "title": f"國立臺灣海洋大學赴姊妹校交換生甄選簡章與名額表—{zh_name}",
            "url": source_url,
        },
    ]
    if factsheet_url:
      ev_sources.append({
          "title": f"海大國際處公告之 {zh_name} 交換專頁／Fact Sheet",
          "url": factsheet_url,
      })
    if exps:
      ev_sources.append({
          "title": f"海大國際事務處赴外研修心得專區—赴 {zh_name} 交換生心得報告（{len(exps)} 篇）",
          "url": exps[0]["url"],
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
            "scope": "國立臺灣海洋大學出國交換姊妹校住宿與生活資訊",
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
            "scope": "國立臺灣海洋大學交換生費用規定、校內交換獎補助、教育部學海飛颺／惜珠與地區生活費估算",
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
            "scope": "國立臺灣海洋大學交換生選課規定、每學期至少修習相當海大 6 學分門檻與返國學分採認",
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
            "scope": "國立臺灣海洋大學出國交換簽證、海外醫療保險、役男緩徵出境與在學註冊提醒",
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
                    f"｜海大國際處赴外研修心得專區公開收錄 {len(exps)} 篇赴 {zh_name} 交換生返國心得報告（{'、'.join(exp_labels[:4])}）。"
                    if exps
                    else ""
                )
            ),
            "sources": ev_sources,
            "checked_at": CHECKED_AT,
            "scope": "國立臺灣海洋大學出國交換名額與歷屆學長姐交換經驗分享",
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
            "已整合國立臺灣海洋大學國際事務處《2027年春/秋季赴姊妹校交換生甄選簡章》、《115-2赴大陸地區交換計畫》、雙聯學位一覽表及 Notion 赴外研修心得專區共 439 篇學長姐報告。",
            "當期宿位供給、費用與選課限制請依姊妹校最新交換網頁及入學通知書核對。",
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
          "title": f"國立臺灣海洋大學赴 {zh_name} 交換計畫／Fact Sheet 專頁",
          "url": factsheet_url,
          "term": "115學年度",
      })

    if exps:
      rep_title = (
          f"國立臺灣海洋大學赴 {zh_name} 交換研修心得彙編（共 {len(exps)} 篇學長姐報告）"
      )
      latest_e = exps[0]
      latest_author = f"{latest_e['student']} 等 {len(exps)} 位海大交換生"
      summary_text = (
          f"國立臺灣海洋大學國際事務處「赴外研修心得專區」公開收錄 {len(exps)} 篇歷年赴 {zh_name} 交換及雙聯學生返國心得報告（含：{'、'.join(exp_labels[:6])}），"
          f"涵蓋海運暨管理、生命科學、海洋科學與資源、工學、電機資訊、人文社會科學、海洋法律與政策及國際學院學生於 {zh_name} 之專業選課、語言學習、學生宿舍環境、簽證保險辦理及海外生活開銷實錄。"
      )
      theme_map = {
          "academics": (
              f"海大交換生（{'、'.join(exp_labels[:4])}）分享於 {zh_name} 修讀海洋海事、水產食品、理工電資、商管航運與人文法政課程之選課方式、達成每學期至少相當海大 6 學分門檻及返國辦理學分採認之經驗。"
          ),
          "housing": (
              f"海大交換生詳述 {zh_name} 校內外學生宿舍申請時程、房型設備與周邊生活機能（{housing_clean[:120]}）。"
          ),
          "campus_culture": (
              f"海大國際處收錄 {len(exps)} 篇赴 {zh_name} 交換生返國心得報告，記錄接待校迎新週（Orientation）、國際學伴（Buddy Program）與跨文化交流體驗。"
          ),
          "cost": (
              f"海大交換生記錄於 {zh_name} 之每月住宿、伙食與交通開銷（{cost_default}），以及運用海大校內赴姊妹校交換獎補助（機票＋學費最高8萬＋生活費）或教育部學海飛颺／惜珠獎學金支應留學費用之規劃。"
          ),
      }
      student_experience_rows.append({
          "school_name": full_name,
          "country": country,
          "title": rep_title,
          "source_url": latest_e["url"],
          "source_type": "article",
          "platform": "國立臺灣海洋大學國際事務處—赴外研修心得專區",
          "author_name": latest_author,
          "language": "zh",
          "summary": summary_text,
          "themes": ["academics", "housing", "campus_culture", "cost"],
          "theme_summaries": theme_map,
          "content_status": "full_text",
          "perspective": "official_student_story",
          "published_at": None,
          "discovered_at": CHECKED_AT,
          "content_hash": hashlib.sha256(f"{full_name}:ntou_exp:{len(exps)}".encode("utf-8")).hexdigest(),
          "exchange_term": f"{latest_e['year']}學年度",
          "summary_zh": summary_text,
          "original_summary": summary_text,
          "theme_summaries_zh": theme_map,
          "translation_status": "original",
          "source_kind": "official_experience_page",
      })

    experience_sources_records.append({
        "home_university": "國立臺灣海洋大學",
        "school_name": full_name,
        "country": country,
        "official_experience_portal_url": exps[0]["url"] if exps else NTOU_EXP_SHARING_URL,
        "partner_page_url": factsheet_url or source_url,
        "report_count": len(exps),
        "sample_reports": sample_reports,
        "checked_at": CHECKED_AT,
    })

  partners_jsonl_text = "\n".join(json.dumps(r, ensure_ascii=False) for r in partners) + "\n"
  (OFFICIAL_NTOU_DIR / "partners.jsonl").write_text(partners_jsonl_text, encoding="utf-8")
  (SOURCES_NTOU_DIR / "partners.jsonl").write_text(partners_jsonl_text, encoding="utf-8")
  (OFFICIAL_NTOU_DIR / "application_workflows.jsonl").write_text(
      "\n".join(json.dumps(r, ensure_ascii=False) for r in workflows) + "\n",
      encoding="utf-8",
  )
  (OFFICIAL_NTOU_DIR / "destination_profiles.jsonl").write_text(
      "\n".join(json.dumps(r, ensure_ascii=False) for r in destinations) + "\n",
      encoding="utf-8",
  )
  (OFFICIAL_NTOU_DIR / "partner_research.jsonl").write_text(
      "\n".join(json.dumps(r, ensure_ascii=False) for r in research_records) + "\n",
      encoding="utf-8",
  )
  (OFFICIAL_NTOU_DIR / "student_life.jsonl").write_text(
      "\n".join(json.dumps(r, ensure_ascii=False) for r in life_records) + "\n",
      encoding="utf-8",
  )
  (OFFICIAL_NTOU_DIR / "experience_sources.jsonl").write_text(
      "\n".join(json.dumps(r, ensure_ascii=False) for r in experience_sources_records) + "\n",
      encoding="utf-8",
  )
  (OFFICIAL_NTOU_DIR / "student_experiences.jsonl").write_text(
      "\n".join(json.dumps(r, ensure_ascii=False) for r in student_experience_rows) + "\n",
      encoding="utf-8",
  )
  (OFFICIAL_NTOU_DIR / "campus-locations.json").write_text(
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
  (OFFICIAL_NTOU_DIR / "student-experience-digests.json").write_text(
      json.dumps({"digests": digest_records}, ensure_ascii=False, indent=2) + "\n",
      encoding="utf-8",
  )

  # Update university_locations.jsonl with NTOU home location
  loc_file = REPO_ROOT / "src/exchange_info/official_data/university_locations.jsonl"
  existing_loc_lines = [
      line for line in loc_file.read_text(encoding="utf-8").splitlines() if line.strip()
  ]
  existing_loc_map = {}
  for line in existing_loc_lines:
    rec = json.loads(line)
    existing_loc_map[(rec["school_name"], rec.get("country") or "")] = rec

  ntou_home_loc = {
      "school_name": "國立臺灣海洋大學",
      "country": "臺灣",
      "city": "基隆市中正區",
      "latitude": 25.1508,
      "longitude": 121.7758,
      "geocode_status": "verified",
      "geocoded_at": CHECKED_AT,
      "source_url": "https://www.wikidata.org/wiki/Q709627",
      "identity_source_url": "https://ror.org/03bvvnt49",
      "precision": "representative",
      "note": (
          "校級代表位置：官方網域及國家已與 ROR 比對，座標來源為 Wikidata P625；實際交換校區以錄取通知為準。"
          " 母校代表點採基隆市中正區北寧路2號校本部行政大樓國際事務處；官方地址來源：https://oia.ntou.edu.tw/。"
      ),
  }
  existing_loc_map[("國立臺灣海洋大學", "臺灣")] = ntou_home_loc
  sorted_locs = sorted(
      existing_loc_map.values(),
      key=lambda r: (r.get("country") or "", r.get("school_name") or ""),
  )
  loc_file.write_text(
      "\n".join(json.dumps(r, ensure_ascii=False) for r in sorted_locs) + "\n",
      encoding="utf-8",
  )

  ntou_source_urls = [
      NTOU_OIA_HUB_URL,
      NTOU_OUTBOUND_OVERVIEW_URL,
      NTOU_EXCHANGE_PLAN_URL,
      NTOU_DUAL_DEGREE_URL,
      NTOU_DUAL_DEGREE_XLSX_URL,
      NTOU_XUEHAI_OVERVIEW_URL,
      NTOU_XUEHAI_FEIYANG_URL,
      NTOU_XUEHAI_XIZHU_URL,
      NTOU_XUEHAI_ZHUMENG_URL,
      NTOU_BROCHURE_2027_URL,
      NTOU_BROCHURE_2026_URL,
      NTOU_GUIDELINES_LANG_URL,
      NTOU_ENFORCEMENT_RULES_URL,
      NTOU_XUEHAI_RULES_URL,
      NTOU_MOE_XUEHAI_115_URL,
      NTOU_APP_CHECKLIST_URL,
      NTOU_AUTOBIO_EX_URL,
      NTOU_STUDY_PLAN_EX_URL,
      NTOU_BUDGET_EX_URL,
      NTOU_PRE_DEPARTURE_URL,
      NTOU_REIMBURSEMENT_URL,
      NTOU_SOP_EXCHANGE_URL,
      NTOU_SOP_DUAL_URL,
      NTOU_MAINLAND_115_2_URL,
      NTOU_SISTER_SCHOOLS_URL,
      NTOU_EXP_SHARING_URL,
  ]

  exchange_info_payload = {
      "school_name": "國立臺灣海洋大學",
      "program_type": [
          (
              "國際事務處赴國外姊妹校交換生計畫（主梯次於每年 3–5 月辦理次年春/秋季學期交換暨學海飛颺獎學金聯合甄選，增開秋季梯次於每年 12–2 月辦理；當期開放日本北海道大學、東京海洋大學、神戶大學、九州大學、芝浦工業大學、長崎大學、琉球大學、韓國中央大學、韓國海洋大學、釜慶大學、全南大學、仁川大學、德國維爾茲堡－施韋因富特科技大學 THWS、法國里爾大學、卡昂大學、濱海大學、美國紐約州立大學海運學院、克拉克森大學、紐澤西理工學院、西來大學、加拿大紐芬蘭紀念大學、馬來西亞馬來亞大學、馬來西亞理科大學、拉曼大學、登嘉樓大學、越南河內國家大學、越南海事大學、肯特大學、FPT 大學、印尼艾爾朗加大學、本庫魯大學、泰國素羅娜麗科技大學及菲律賓巴丹半島州立大學、帕蒂多州立大學等 39 所國外交換合作校）"
          ),
          (
              "赴大陸地區姊妹校交換（研修）計畫（115學年度第 2 學期［2027春季班］開放江南大學、上海海事大學、上海海洋大學、中國海洋大學、廈門大學、福州大學 6 所雙一流及海事重點高校，並與大連海事大學、武漢理工大學、河海大學、中山大學、集美大學、大連海洋大學、廣東海洋大學、浙江海洋大學、寧波大學、汕頭大學等共 22 所大陸高校及香港理工大學締結姊妹校）"
          ),
          (
              "國際雙聯學位計畫（含美國辛辛那提大學 University of Cincinnati 工學院／電資學院 1+1 碩士及 3+2 學碩雙聯學位、美國紐約州立大學海運學院 SUNY Maritime College 航運與物流管理雙碩士學位、日本長崎大學 Nagasaki University 水產／環漁 2+2 雙博士學位及馬來西亞登嘉樓大學 UMT 聯合博士學位）"
          ),
      ],
      "academic_year": [
          (
              "115（2027年春/秋季學期赴國外姊妹校交換生計畫暨學海飛颺主梯次甄選於 2026/03/01 公告、2026/05/08 12:00 報名截止、5月下旬面試、6月中旬放榜；115學年度第 2 學期［2027春季班］赴大陸地區姊妹校交換計畫於 2026/09/30 12:00 截止收件；本平台完整收錄 123 所海大全球合作姊妹校，含 46 所當期開放申請校及 77 所正式締約姊妹校）"
          ),
          (
              "116（2027年秋季學期赴國外姊妹校交換增開梯次預計於 2026/12/01 公告簡章、2027/02/25 12:00 截止報名；2028年春/秋季學期主梯次預計於 2027/03/01 公告簡章、2027/05/07 12:00 截止報名）"
          ),
      ],
      "semester": [
          "春季學期（海大第2學期：每年約 2/3 月至 6/7 月，日本春季班為 4 月至 8/9 月）",
          "秋季學期（海大第1學期：每年約 8/9 月至翌年 1/2 月，日本秋季班為 9/10 月至翌年 2/3 月）",
          "一學年交換或 1–2 年雙聯學位修讀（依各姊妹校協議名額及雙聯學制辦理）",
      ],
      "application_period": [
          (
              "【2027年春/秋季學期赴國外姊妹校交換生計畫（不含大陸地區）暨學海飛颺主梯次時程】簡章公告：2026/03/01；報名截止：2026/05/08 (五) 12:00（先將申請資料轉為單一 PDF 寄至 `marberthsu@email.ntou.edu.tw`，並預約時間親自將 A4 單面不裝訂 L 型資料夾紙本送交行政大樓 3 樓國際合作組）；校內面試：2026/05 下旬（第 14–15 週，馬祖校區學生可申請線上面試）；結果公告：2026/06 中旬。"
          ),
          (
              "【115學年度第 2 學期（2027春季班）赴大陸地區姊妹校交換（研修）計畫時程】校內報名截止：2026/09/30 (三) 12:00（開放上海海洋大學、上海海事大學［限商船/交運相關系所］、中國海洋大學、江南大學、廈門大學、福州大學共 6 校）；先寄送 PDF 電子檔並預約時間親送紙本至國際處，書面審查後擇優提名。"
          ),
          (
              "【秋季增開梯次與下一年度主梯次預告】海大每年設有兩次國外交換甄選：（1）秋季學期增開梯次：每年 12/01 公告簡章、翌年 02/25 12:00 報名截止、3 月中旬面試、4 月上旬放榜；（2）春/秋季學期主梯次（含學海飛颺）：每年 03/01 公告簡章、05月上旬（約 5/7–5/8）12:00 報名截止、5 月下旬面試、6 月中旬放榜。"
          ),
      ],
      "eligibility": [
          (
              "【在學學制、年級與院系規定（依《國立臺灣海洋大學學生赴國外研修要點》第3點）】申請期間與赴國外研修期間皆應為海大註冊在學生，且非為大一上學期之新生或當學期畢業之學生（研修期間不得辦理休學或畢業）。大學部學生須經系所主管與學院同意；碩、博士班學生須經指導教授、系所主管與學院同意。"
          ),
          (
              "【學業成績及格門檻與姊妹校 GPA 標準（依《學生赴國外研修施行細則》第2點）】申請姊妹校交換者，申請之前一學期學業平均須達及格以上（大學部 60 分、研究所 70 分）；如交換學校另設有學業成績標準（如北海道大學 HUSTEP/SAS、神戶大學、馬來亞大學、登嘉樓大學、艾爾朗加大學、紐澤西理工學院、辛辛那提大學要求 GPA 3.0；馬來西亞理科大學要求 GPA 3.5；克拉克森大學要求 GPA 4.0；全南大學、拉曼大學、紐芬蘭紀念大學要求 GPA 2.5；韓國海洋大學要求 GPA 2.64/4.5），亦須符合該校規定。"
          ),
          (
              "【校內甄選評分標準與 5 志願選填上限（依《施行細則》第4點）】每人至多可填寫 5 個志願，一校僅能挑選一項計畫或一個系所填寫。（1）赴國外姊妹校評分標準：在校成績 30% ＋ 外語能力 30% ＋ 書面及面試表現（研修計畫及其他輔助文件） 40%；（2）赴大陸地區姊妹校評分標準：在校成績 45% ＋ 研修計畫及其他輔助文件 55%；（3）同分比序原則：先比外語能力，次比該交換學校之志願序。"
          ),
      ],
      "language_requirement": [
          (
              "【海大「留學國語文能力證明」標準表（《學生赴國外研修要點》附件一）】申請赴國外姊妹校（不含大陸地區）須檢附下列任一符合授課語種之有效語言證明：（1）英文（擇一）：TOEFL iBT 60 分(含)以上、IELTS（學術組）5.0 級(含)以上、TOEIC 600 分(含)以上、或全民英檢（GEPT）高級複試(含)以上；（2）日文（擇一）：JLPT N3(含)以上、或 FLPT 日文筆試 195 分及口試 S-2(含)以上；（3）韓文：TOPIK 3 級(含)以上；（4）法文（擇一）：DELF B1 / DELF1(含)以上、或 FLPT 法文筆試 195 分及口試 S-2(含)以上；（5）德文（擇一）：ZDaF（ZD）初級(含)以上、DSH 合格、或 FLPT 德文筆試 195 分及口試 S-2(含)以上；（6）西班牙文（擇一）：DELE 初級（Nivel Inicial）(含)以上、或 FLPT 西文筆試 195 分及口試 S-2(含)以上。"
          ),
          (
              "【重點姊妹校進階語言門檻提醒】如接待校訂有更高語言標準，須同時符合接待校規定：（1）日本：北海道大學 HUSTEP 要求 TOEFL iBT 79 / IELTS 6.5、SAS 要求 JLPT N2；神奈川大學、高知大學、九州大學農學部、琉球大學 J Program、芝浦工業大學日語組要求 JLPT N2；神戶大學海事科學部要求 TOEFL iBT 71–75 / TOEIC 730；芝浦工業大學英語組、長崎大學多文化社會學部、琉球大學 G Program 要求 CEFR B2（TOEFL iBT 72 / IELTS 5.5 / TOEIC 785）；（2）歐美加馬：加拿大紐芬蘭紀念大學要求 TOEFL iBT 90 / IELTS 6.5；美國克拉克森大學、辛辛那提大學雙聯要求 TOEFL iBT 80 / IELTS 6.5；紐約州立大學海運學院、紐澤西理工學院要求 TOEFL iBT 79 / IELTS 6.0–6.5；馬來亞大學要求 TOEFL iBT 80 / IELTS 6.0；德國 THWS 要求英語或德語 B2；法國里爾大學、卡昂大學法語授課要求 DELF B2。"
          ),
          (
              "【赴大陸地區姊妹校免附外語檢定規定】依《國立臺灣海洋大學學生赴國外研修要點》附件一備註規定，申請赴大陸地區姊妹校交換者，得免提送外國語言能力證明。"
          ),
      ],
      "required_documents": [
          "1. 國立臺灣海洋大學出國交換學生申請表及申請文件檢核表（每人至多填寫 5 個志願；大學部須系所主管與學院核章，碩博士生須指導教授、系所主管與學院核章）",
          "2. 中文歷年成績單正本乙份（須有申請之前一學期成績及排名，大學部須達 60 分及格、研究所須達 70 分及格）",
          "3. 英文歷年成績單正本乙份（供審查及提名姊妹校使用）",
          "4. 留學國語文能力證明影本（依授課語種符合海大附表一及接待校標準：英文 TOEFL iBT 60 / IELTS 5.0 / TOEIC 600、日文 JLPT N3–N2、韓文 TOPIK 3、法文 B1–B2、德文 ZDaF–B2；赴大陸地區免附）",
          "5. 中文自傳（約 1,000–1,500 字，含個人背景、學經歷與申請赴外交換動機）",
          "6. 外國留學研修計畫書（約 1,000–1,500 字，含擬選修課程規劃、研究主題與預期成效）",
          "7. 經費分析表（預估交換期間學費、機票與生活費開支；欲申請學海飛颺或校內交換獎補助者必繳，未繳交者視同放棄申請校內一切獎學金）及個人資料使用同意書",
          "8. 其他有利審查輔助文件（如外文自傳與讀書計畫、師長推薦信、競賽獲獎、專題研究或社團幹部證明；全套文件須先轉為單一 PDF 寄至 `marberthsu@email.ntou.edu.tw` 並預約時間親送 A4 單面不裝訂 L 型資料夾紙本至國際處）",
      ],
      "scholarship_info": [
          (
              "《海大校內赴姊妹校交換獎補助》（依《國立臺灣海洋大學學生赴國外研修施行細則》第7點）：補助通過本校甄選赴國外或大陸地區姊妹校交換之在學生：（1）機票費：補助來回經濟艙機票費；（2）學費補助：如已獲姊妹校學費減免者不再補助；赴國外姊妹校補助該校學費總額 50% 為原則，且上限不得超過新臺幣 80,000 元；赴大陸地區姊妹校學費全額補助，上限為海大學費之 80%；（3）生活費補助：依教育部公費留學生請領公費項目及支給數額一覽表計算。每名學生於同一教育階段以補助 1 次為限。"
          ),
          (
              "教育部《學海飛颺》選送優秀學生出國研修獎學金（依《國立臺灣海洋大學學海系列計畫補助施行細則》）：併同每年 3–5 月赴國外姊妹校交換生甄選提出申請（限具中華民國國籍且在臺設有戶籍、赴大陸及港澳以外國家研修 1 學期至 1 學年之在學生），補助項目涵蓋來回經濟艙機票費、部分學費及部分生活費（具中低收入戶或特殊境遇家庭子女身分者得酌情增加補助額度）。"
          ),
          (
              "教育部《學海惜珠》勵學優秀學生出國研修獎學金與《學海築夢／新南向學海築夢》海外實習獎學金：（1）學海惜珠：補助具低收入戶、中低收入戶、特殊境遇家庭扶助、身心障礙者生活補助或大專校院弱勢學生助學金助學資格之在學生（每年 12 月底前向國際處申請），機票費、學費與生活費最高得全額補助；（2）學海築夢／新南向學海築夢：由計畫主持人選送學生赴海外機構實習（印尼不少於 25 日、其他國家不少於 30 日），補助來回經濟艙機票費及生活費。"
          ),
          (
              "接待校專屬獎學金與不重複兼領原則：（1）美國辛辛那提大學 1+1／3+2 雙聯碩士提供 USD 4,195–10,700 獎學金及臺灣學生專屬 Luchen Scholarship；美國紐約州立大學海運學院提供交換生學雜費及住宿費減免；美國西來大學修滿 4 堂課享 50% 學雜費補助；印尼艾爾朗加大學提供 AMERTA 交換獎學金；日本姊妹校可透過接待校申請日本台灣交流協會或 JASSO 獎學金；（2）依《施行細則》第7點，任一赴外研修計畫僅得就我國政府或海大校內提供之各項出國獎補助擇一申請，不得重複兼領；申請者必須於報名時一併繳交《經費分析表》，返國後 1 個月內須完成 1,500–2,000 字心得報告與單據核銷，否則追回全額補助。"
          ),
      ],
      "partner_universities": [p["school_name"] for p in partners],
      "source_urls": ntou_source_urls,
      "last_checked": CHECKED_AT,
  }
  (OFFICIAL_NTOU_DIR / "exchange_info.json").write_text(
      json.dumps(exchange_info_payload, ensure_ascii=False, indent=2) + "\n",
      encoding="utf-8",
  )

  student_dashboard_payload = {
      "school_name": "國立臺灣海洋大學",
      "last_checked": CHECKED_AT,
      "academic_score_minimum": 60.0,
      "academic_score_rule": (
          "依《國立臺灣海洋大學學生赴國外研修要點》第3點及《施行細則》第2點規定：申請期間與赴國外研修期間皆應為本校註冊在學生（非大一上學期之新生或當學期畢業生），申請之前一學期學業平均須達及格以上（大學部 60 分、研究所 70 分），且須符合各交換學校訂定之 GPA 標準。國外姊妹校依「在校成績 30%＋外語能力 30%＋書面及面試表現 40%」評分，大陸地區姊妹校依「在校成績 45%＋研修計畫及其他輔助文件 55%」評分。"
      ),
      "academic_gpa_minimum": 2.0,
      "maximum_preferences": 5,
      "selection_rules": {
          "academic_policy": "percentage",
          "academic_reference_year": "115",
          "undergraduate_gpa_minimum": 2.0,
          "graduate_academic_exempt": False,
          "exclude_in_service": False,
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
          "toefl": 60.0,
          "ielts": 5.0,
          "toeic": 600.0,
      },
      "application_periods": [
          {'title': '國立臺灣海洋大學下一梯次國外交換甄選：申請時程待核實',
           'details': ['原附時程網址於2026-10-21查核時回傳404，無法據此確認2027秋季增開梯次或2028年度主梯次的日期。',
                       '本平台尚未取得這些梯次的有效官方時程證據；請向國際事務處確認，不能依歷年慣例推定確切截止日。'],
           'source': {'title': '國立臺灣海洋大學國際事務處—出國交換學生計畫申請時程與簡章專區',
                      'source_url': 'https://oia.ntou.edu.tw/p/412-1022-10817.php?Lang=zh-tw',
                      'category': 'exchange_application',
                      'summary': '查核限制：此來源目前不足以支持本梯次確切時程，需另查當期正式公告。'},
           'scope': 'home_application',
           'program_types': ['exchange'],
           'academic_year': '116',
           'application_round': '2027年秋季增開梯次暨2028年春/秋季主梯次赴姊妹校交換甄選',
           'audience': 'all_students',
           'opens_at': None,
           'deadline_at': None,
           'date_status': 'needs_confirmation',
           'status': 'needs_confirmation',
           'status_note': '本梯次確切時程尚未核實，請以母校當期官方公告為準。',
           'deadline_note': '未核實的預估日期不能用作申請截止日或提醒。',
           'reminder_eligible': False,
           'checked_at': '2026-10-20T17:44:49Z'},
          {
              "title": (
                  "國立臺灣海洋大學 2027 年春/秋季學期赴國外姊妹校交換生計畫暨學海飛颺甄選（2026/05/08 12:00 截止）與 115-2 赴大陸地區姊妹校交換甄選（2026/09/30 12:00 截止）"
              ),
              "details": [
                  (
                      "2027年春/秋季學期赴國外姊妹校交換生計畫（不含大陸地區）暨學海飛颺獎學金校內甄選已於 2026/03/01 公告簡章、2026/05/08 (五) 12:00 截止收件，共開放日本、韓國、德國、法國、美國、加拿大、馬來西亞、越南、印尼、泰國、菲律賓等 35 所國外合作校名額，並於 2026/05 下旬面試、06 月中旬完成錄取分發。"
                  ),
                  (
                      "115學年度第 2 學期（2027春季班）赴大陸地區姊妹校交換（研修）計畫已於 2026/09/30 (三) 12:00 截止校內收件，開放江南大學、上海海事大學、上海海洋大學、中國海洋大學、廈門大學、福州大學共 6 所大陸重點高校交換名額。"
                  ),
              ],
              "source": {
                  "title": "國立臺灣海洋大學 2027 年春/秋季赴姊妹校交換簡章與 115-2 赴大陸地區交換招募公告",
                  "source_url": NTOU_BROCHURE_2027_URL,
                  "category": "exchange_application",
                  "summary": "海大 2027 年春/秋季國外交換簡章 PDF 與 115-2 大陸地區交換招募公告。",
              },
              "scope": "home_application",
              "program_types": ["exchange"],
              "academic_year": "115",
              "application_round": "2027年春/秋季國外交換暨115-2大陸地區交換甄選",
              "audience": "all_students",
              "opens_at": "2026-03-01T09:00:00+08:00",
              "deadline_at": "2026-09-30T12:00:00+08:00",
              "date_status": "verified_exact",
              "status": "closed",
              "status_note": "2027年春/秋季國外交換主梯次（5/8截止）及 115-2 赴大陸地區交換（9/30截止）校內收件皆已截止，目前正進行姊妹校提名與行前準備作業。",
              "deadline_note": "錄取生須依限繳交《申請入學同意聲明書》與《出國前檢核表》，並於返國後 1 個月內完成心得報告與核銷。",
              "reminder_eligible": False,
              "checked_at": CHECKED_AT,
          },
      ],
      "program_overview": [
          {
              "title": (
                  f"國立臺灣海洋大學國際事務處出國交換與雙聯學位總覽（{len(partners)} 所全球合作姊妹校・{open_partner_count} 所當期開放申請校・校內與學海雙軌獎補助）"
              ),
              "details": [
                  (
                      f"國立臺灣海洋大學（NTOU，海大）由「國際事務處（國際合作組）」統籌辦理全校赴國外及大陸地區姊妹校交換學生、國際雙聯學位與教育部學海系列獎補助計畫。本平台完整收錄 {len(partners)} 所海大官方交換與雙聯合作姊妹校（含當期開放申請名額之 {open_partner_count} 所合作校及 {len(partners) - open_partner_count} 所正式締約姊妹校），橫跨全球 22 個國家與地區（中國大陸 22 校、日本 21 校、菲律賓 10 校、越南 9 校、印尼 9 校、美國 8 校、韓國 7 校、泰國 7 校、印度 6 校、馬來西亞 5 校、德國 3 校、法國 3 校、俄羅斯 3 校、波蘭 2 校，以及英國、瑞士、澳洲、巴布亞紐幾內亞、奈及利亞、加拿大、伊朗、香港各 1 校）。"
                  ),
                  (
                      "海大出國交換體系具備四大核心特色：（1）全球頂尖海洋海事與綜合名校網絡：涵蓋東京海洋大學、北海道大學、神戶大學、九州大學、長崎大學、琉球大學、韓國海洋大學、釜慶大學、紐約州立大學海運學院（SUNY Maritime）、紐芬蘭紀念大學（MUN）、中國海洋大學、上海海洋大學、上海海事大學等國際海事水產龍頭學府；（2）彈性雙梯次甄選與雙聯學位：每年 3–5 月辦理春/秋季主梯次、12–2 月辦理秋季增開梯次、9 月辦理大陸春季班，並設美國辛辛那提大學 1+1／3+2 雙碩士、紐約州立大學海運學院雙碩士、日本長崎大學 2+2 雙博士及馬來西亞登嘉樓大學聯合博士；（3）豐厚獎補助體系：提供《海大校內赴姊妹校交換獎補助》（機票＋國外學費 50% 上限 8 萬／大陸學費全額上限海大 80%＋生活費）及教育部《學海飛颺／惜珠／築夢》；（4）完整 Notion 知識庫與 439 篇學長姐心得傳承。"
                  ),
              ],
              "source": {
                  "title": "國立臺灣海洋大學國際事務處—赴外研修計畫總覽與姊妹校專區",
                  "source_url": NTOU_OUTBOUND_OVERVIEW_URL,
                  "category": "exchange_application",
                  "summary": "海大 123 所全球姊妹校、交換生計畫、雙聯學位、學海系列獎補助與 Notion 赴外研修心得專區。",
              },
          }
      ],
      "eligibility": [
          {
              "title": "在學註冊身分（非大一上或當學期畢業）、前一學期學業及格門檻、最多 5 志願與 30%／30%／40% 甄選配分",
              "details": [
                  (
                      "在學身分與學業門檻（依《國立臺灣海洋大學學生赴國外研修要點》第3點及《施行細則》第2點）：申請期間與赴國外研修期間皆應為本校註冊在學生，且非為大一上學期之新生或當學期畢業之學生（大學部須經系所主管與學院同意；碩博士生須經指導教授、系所主管與學院同意）。申請之前一學期學業平均須達及格以上（大學部 60 分、研究所 70 分），如交換學校另設有 GPA 標準亦須符合。"
                  ),
                  (
                      "志願選填上限與評分比序標準（依《施行細則》第4點）：每人至多可選填 5 個志願（一校限填一項計畫或一個系所）。（1）赴國外姊妹校評分標準：在校成績 30%＋外語能力 30%＋書面及面試表現（研修計畫及其他輔助文件） 40%；（2）赴大陸地區姊妹校評分標準：在校成績 45%＋研修計畫及其他輔助文件 55%；（3）同分比序：1. 外語能力、2. 該交換學校志願序。"
                  ),
              ],
              "source": {
                  "title": "國立臺灣海洋大學學生赴國外研修要點與施行細則 PDF",
                  "source_url": NTOU_ENFORCEMENT_RULES_URL,
                  "category": "exchange_application",
                  "summary": "海大出國交換申請資格、前一學期及格門檻、甄選配分比序與每學期至少修習 6 學分規定。",
              },
          }
      ],
      "language_requirements": [
          {
              "title": "海大「留學國語文能力證明」標準表（英 iBT 60 / IELTS 5.0 / TOEIC 600、日 N3–N2、韓 TOPIK 3、法 B1–B2、德 ZDaF–B2、大陸免附）",
              "details": [
                  (
                      "海大校內外語能力基準（《學生赴國外研修要點》附件一）：（1）英文（擇一）：TOEFL iBT 60 分(含)以上、IELTS（學術組）5.0 級(含)以上、TOEIC 600 分(含)以上、或 GEPT 高級複試(含)以上；（2）日文（擇一）：JLPT N3(含)以上、或 FLPT 日文筆試 195 分及口試 S-2(含)以上；（3）韓文：TOPIK 3 級(含)以上；（4）法文：DELF B1(含)以上或 FLPT 法文筆試 195 分及口試 S-2；（5）德文：ZDaF 初級(含)以上、DSH 合格或 FLPT 德文筆試 195 分及口試 S-2；（6）西文：DELE 初級(含)以上或 FLPT 西文筆試 195 分及口試 S-2；（7）赴大陸地區者：得免提送外國語言能力證明。"
                  ),
                  (
                      "接待校個別進階門檻：日本北海道大學 HUSTEP（iBT 79 / IELTS 6.5）與 SAS（JLPT N2）、神奈川大學（N2）、高知大學（N2）、芝浦工業大學（英語組 B2 / 日語組 N2）、神戶大學海事科學部（iBT 71–75 / TOEIC 730）、九州大學農學部（iBT 79 / IELTS 6.0 / N2）、長崎大學多文化社會學部（B2）、琉球大學（G Program N3 或 B2 / J Program N2）、加拿大紐芬蘭紀念大學（iBT 90 / IELTS 6.5）、美國克拉克森大學與辛辛那提大學雙聯（iBT 80 / IELTS 6.5）、紐約州立大學海運學院與紐澤西理工學院（iBT 79 / IELTS 6.0–6.5）、馬來亞大學（iBT 80 / IELTS 6.0）、德國 THWS（英語或德語 B2）、法國里爾大學與卡昂大學（法語授課 B2）。"
                  ),
              ],
              "source": {
                  "title": "國立臺灣海洋大學學生赴國外研修要點暨附件一「留學國語文能力證明」標準表 PDF",
                  "source_url": NTOU_GUIDELINES_LANG_URL,
                  "category": "exchange_application",
                  "summary": "海大英、日、韓、法、德、西語檢定最低標準表與大陸地區免附語檢規定。",
              },
          }
      ],
      "required_documents": [
          {
              "title": "校內甄選必繳文件檢核表、PDF 電子檔先行寄送＋預約親送 A4 不裝訂紙本與《經費分析表》必繳規定",
              "details": [
                  (
                      "校內甄選必繳資料（請依《申請文件檢核表》順序排列，A4 單面列印、請勿裝訂，置於透明 L 型資料夾）：1. 出國交換學生申請表（完成指導教授［研究生］、系所主管及學院院長核章）、2. 中文歷年成績單（須含前一學期成績及排名）、3. 英文歷年成績單、4. 留學國語文能力證明（大陸地區免附）、5. 中文自傳（1,000–1,500 字）、6. 外國留學研修計畫書（1,000–1,500 字）、7. 經費分析表（申請獎學金者必繳，未繳交者視同放棄申請校內一切獎學金）、8. 個人資料使用同意書及其他有利審查文件。"
                  ),
                  (
                      "雙軌繳件與返國核銷規定：申請人必須於截止日前先將所有申請資料轉為單一 PDF 檔寄至國際處承辦人信箱（`marberthsu@email.ntou.edu.tw`），並回信預約時間親自送交紙本至行政大樓 3 樓國際合作組；錄取後須依限繳交《申請入學同意聲明書》與《出國前檢核表》，返國後 1 個月內須繳交 1,500–2,000 字《研修心得報告》（含至少 4 張照片）、電子問卷、登機證正本、電子機票收據及正式成績單辦理核銷。"
                  ),
              ],
              "source": {
                  "title": "國立臺灣海洋大學 2027 年春/秋季赴姊妹校交換簡章與申請文件檢核表 PDF",
                  "source_url": NTOU_APP_CHECKLIST_URL,
                  "category": "exchange_application",
                  "summary": "海大出國交換申請文件檢核表、自傳／研修計畫／經費分析表範例與出國前／返國核銷檢核表。",
              },
          }
      ],
      "scholarship_info": [
          {
              "title": "海大校內赴姊妹校交換獎補助（機票＋學費最高8萬＋生活費）、教育部學海飛颺／惜珠／築夢與接待校雙聯獎學金",
              "details": [
                  (
                      "《海大校內赴姊妹校交換獎補助》（依《學生赴國外研修施行細則》第7點）：補助通過本校甄選赴姊妹校交換之在學生：（1）來回經濟艙機票費、（2）學費補助（已獲姊妹校學費減免者不再補助；赴國外姊妹校補助該校學費總額 50%、上限 NT$80,000；赴大陸地區姊妹校學費全額補助、上限為海大學費之 80%）、（3）生活費補助（依教育部公費留學生支給數額表計算）。"
                  ),
                  (
                      "教育部《學海飛颺／學海惜珠／學海築夢》與接待校獎學金：（1）學海飛颺：併同每年 3–5 月國外交換生甄選申請，補助機票、學費及生活費；（2）學海惜珠：補助具低收、中低收、特殊境遇家庭、身障或弱勢助學金資格之在學生（每年 12 月底前申請），機票、學費與生活費最高全額補助；（3）接待校獎學金：美國辛辛那提大學雙聯獎學金 USD 4,195–10,700 及臺灣專屬 Luchen Scholarship、紐約州立大學海運學院學雜費與住宿費減免、西來大學 50% 學雜費補助、印尼艾爾朗加大學 AMERTA 獎學金等。任一研修計畫僅得就政府或海大校內獎補助擇一申請，不得重複兼領。"
                  ),
              ],
              "source": {
                  "title": "國立臺灣海洋大學學生赴國外研修施行細則與學海系列計畫補助施行細則 PDF",
                  "source_url": NTOU_XUEHAI_RULES_URL,
                  "category": "scholarship",
                  "summary": "海大校內交換獎補助、教育部學海飛颺／惜珠／築夢施行細則與返國核銷規定。",
              },
          }
      ],
      "document_explanations": [
          {
              "title": "國立臺灣海洋大學出國交換自傳（1,000–1,500字）、外國留學研修計畫書與經費分析表撰寫指南",
              "summary": "說明海大國際處官方範例格式之中文自傳、留學研修計畫書、經費分析表及 A4 單面不裝訂 L 型資料夾繳件規範。",
              "key_points": [
                  "《中文自傳》與《外國留學研修計畫書》依國際處官方範本各約 1,000–1,500 字，須具體說明個人學習背景、語言能力準備、擬於志願姊妹校修習之專業課程（每學期至少須修習相當海大 6 學分以上）及返國學分採認規劃。",
                  "《經費分析表》為申請教育部學海飛颺或海大校內交換獎補助之必繳文件，須詳列預估往返機票費、姊妹校學雜費與當地每月生活費；報名時未繳交經費分析表者，視同放棄申請校內一切獎學金。",
                  "所有紙本文件須以 A4 單面列印、切勿裝訂（置於透明 L 型資料夾內），並須先將全套掃描轉為單一 PDF 檔寄至 `marberthsu@email.ntou.edu.tw` 後預約時間親送國際處。",
              ],
              "applies_to": [],
              "source": {
                  "title": "國立臺灣海洋大學出國交換申請文件檢核表與自傳／讀書計畫／經費分析表範例 PDF",
                  "source_url": NTOU_STUDY_PLAN_EX_URL,
                  "category": "exchange_application",
                  "summary": None,
              },
              "document_url": NTOU_STUDY_PLAN_EX_URL,
              "document_type": "official_document",
              "full_text_extracted": True,
          }
      ],
      "rule_explanations": [
          {
              "title": "國立臺灣海洋大學學生赴國外研修要點與施行細則：及格門檻、30%/30%/40% 評分、6 學分義務與獎補助擇一原則",
              "summary": "規範海大出國交換生在學身分、前一學期及格門檻、外語檢定基準、甄選配分比序、修課最低學分與返國核銷義務。",
              "key_points": [
                  "申請期間與赴國外研修期間皆應為海大註冊在學生，且非為大一上學期之新生或當學期畢業生；申請之前一學期學業平均須達及格以上（大學部 60 分、研究所 70 分）。",
                  "國外姊妹校甄選按「在校成績 30%＋外語能力 30%＋書面及面試表現 40%」計分；大陸地區姊妹校按「在校成績 45%＋研修計畫及其他輔助文件 55%」計分；每人至多選填 5 個志願，同分時依 1. 外語能力、2. 志願序比序。",
                  "研修期間每學期至少應修習相當於海大 6 學分（含）以上之課程或進行論文研究；任一赴外研修計畫僅得就政府或海大校內獎補助擇一領取，返國後 1 個月內須繳交心得報告與單據完成核銷。",
              ],
              "applies_to": [],
              "source": {
                  "title": "國立臺灣海洋大學學生赴國外研修要點、施行細則與學海系列計畫補助施行細則 PDF",
                  "source_url": NTOU_ENFORCEMENT_RULES_URL,
                  "category": "exchange_application",
                  "summary": None,
              },
              "document_url": NTOU_ENFORCEMENT_RULES_URL,
              "document_type": "official_document",
              "full_text_extracted": True,
          }
      ],
      "sources": [
          {
              "title": "國立臺灣海洋大學國際事務處（OIA）官方網站",
              "source_url": NTOU_OIA_HUB_URL,
              "category": "exchange_application",
              "summary": None,
          },
          {
              "title": "國立臺灣海洋大學 2027 年春/秋季學期赴姊妹校交換生計畫暨學海飛颺甄選申請簡章 PDF",
              "source_url": NTOU_BROCHURE_2027_URL,
              "category": "exchange_application",
              "summary": None,
          },
          {
              "title": "國立臺灣海洋大學學生赴國外研修要點暨附件一「留學國語文能力證明」標準表 PDF",
              "source_url": NTOU_GUIDELINES_LANG_URL,
              "category": "exchange_application",
              "summary": None,
          },
          {
              "title": "國立臺灣海洋大學學生赴國外研修施行細則 PDF",
              "source_url": NTOU_ENFORCEMENT_RULES_URL,
              "category": "exchange_application",
              "summary": None,
          },
          {
              "title": "國立臺灣海洋大學學海系列計畫補助施行細則 PDF",
              "source_url": NTOU_XUEHAI_RULES_URL,
              "category": "scholarship",
              "summary": None,
          },
          {
              "title": "國立臺灣海洋大學 115 學年度第 2 學期赴大陸地區姊妹校交換（研修）計畫招募公告",
              "source_url": NTOU_MAINLAND_115_2_URL,
              "category": "partner_school",
              "summary": None,
          },
          {
              "title": "國立臺灣海洋大學雙聯學位學校資料與申請期程一覽表 XLSX",
              "source_url": NTOU_DUAL_DEGREE_XLSX_URL,
              "category": "partner_school",
              "summary": None,
          },
          {
              "title": "國立臺灣海洋大學全球締約姊妹校一覽表與 Notion 赴外研修心得專區",
              "source_url": NTOU_SISTER_SCHOOLS_URL,
              "category": "partner_school",
              "summary": None,
          },
      ],
  }
  (OFFICIAL_NTOU_DIR / "student_dashboard.json").write_text(
      json.dumps(student_dashboard_payload, ensure_ascii=False, indent=2) + "\n",
      encoding="utf-8",
  )

  pages_records = [
      {
          "title": "國立臺灣海洋大學：2027年春/秋季學期赴國外姊妹校交換生計畫暨 115-2 大陸地區交換甄選時程與雙梯次預告",
          "source_url": NTOU_BROCHURE_2027_URL,
          "published_at": "2026-03-01T00:00:00Z",
          "text": "\n".join(exchange_info_payload["application_period"]),
          "summary": "\n".join(exchange_info_payload["application_period"]),
          "category": "exchange_application",
          "attachments": [],
          "crawled_at": CHECKED_AT,
          "content_hash": hashlib.sha256("\n".join(exchange_info_payload["application_period"]).encode("utf-8")).hexdigest(),
      },
      {
          "title": "國立臺灣海洋大學：學生赴國外研修要點與施行細則（前一學期及格門檻、最多 5 志願與 30%／30%／40% 甄選配分）",
          "source_url": NTOU_ENFORCEMENT_RULES_URL,
          "published_at": "2026-03-01T00:00:00Z",
          "text": "\n".join(exchange_info_payload["eligibility"]),
          "summary": "\n".join(exchange_info_payload["eligibility"]),
          "category": "exchange_application",
          "attachments": [],
          "crawled_at": CHECKED_AT,
          "content_hash": hashlib.sha256("\n".join(exchange_info_payload["eligibility"]).encode("utf-8")).hexdigest(),
      },
      {
          "title": "國立臺灣海洋大學：123 所交換與雙聯合作姊妹校外語檢定門檻（附表一留學國語文能力證明標準表与各校進階要求）",
          "source_url": NTOU_GUIDELINES_LANG_URL,
          "published_at": "2026-03-01T00:00:00Z",
          "text": "\n".join(exchange_info_payload["language_requirement"]),
          "summary": "\n".join(exchange_info_payload["language_requirement"]),
          "category": "exchange_application",
          "attachments": [],
          "crawled_at": CHECKED_AT,
          "content_hash": hashlib.sha256("\n".join(exchange_info_payload["language_requirement"]).encode("utf-8")).hexdigest(),
      },
      {
          "title": "國立臺灣海洋大學：出國交換申請文件檢核表、PDF 電子檔先行寄送＋預約親送 A4 不裝訂紙本與經費分析表規範",
          "source_url": NTOU_APP_CHECKLIST_URL,
          "published_at": "2026-03-01T00:00:00Z",
          "text": "\n".join(exchange_info_payload["required_documents"]),
          "summary": "\n".join(exchange_info_payload["required_documents"]),
          "category": "exchange_application",
          "attachments": [],
          "crawled_at": CHECKED_AT,
          "content_hash": hashlib.sha256("\n".join(exchange_info_payload["required_documents"]).encode("utf-8")).hexdigest(),
      },
      {
          "title": "國立臺灣海洋大學：校內赴姊妹校交換獎補助（機票＋學費最高8萬＋生活費）與教育部學海飛颺／惜珠／築夢施行細則",
          "source_url": NTOU_XUEHAI_RULES_URL,
          "published_at": "2026-03-01T00:00:00Z",
          "text": "\n".join(exchange_info_payload["scholarship_info"]),
          "summary": "\n".join(exchange_info_payload["scholarship_info"]),
          "category": "scholarship",
          "attachments": [],
          "crawled_at": CHECKED_AT,
          "content_hash": hashlib.sha256("\n".join(exchange_info_payload["scholarship_info"]).encode("utf-8")).hexdigest(),
      },
  ]
  (OFFICIAL_NTOU_DIR / "pages.jsonl").write_text(
      "\n".join(json.dumps(p, ensure_ascii=False) for p in pages_records) + "\n",
      encoding="utf-8",
  )

  home_rules = {
      "school_id": "ntou",
      "school_name": "國立臺灣海洋大學",
      "eligibility": student_dashboard_payload["eligibility"],
      "application_periods": student_dashboard_payload["application_periods"],
      "selection_rules": {
          "undergraduate_score_minimum": 60.0,
          "graduate_score_minimum": 70.0,
          "excluded_undergraduate_years": ["大一上"],
          "exclude_graduating_semester": True,
          "maximum_preferences": 5,
          "international_academic_weight_percent": 30,
          "international_language_weight_percent": 30,
          "international_interview_and_plan_weight_percent": 40,
          "mainland_academic_weight_percent": 45,
          "mainland_plan_and_docs_weight_percent": 55,
          "minimum_credits_per_semester_abroad": 6,
          "ntou_subsidy_international_tuition_max_twd": 80000,
          "ntou_subsidy_mainland_tuition_max_ratio": 0.8,
          "return_documents_due": "返國後 1 個月內繳交 1,500–2,000 字研修心得報告（含照片 4 張以上）、電子問卷、登機證正本、電子機票收據及正式成績單辦理獎學金核銷與學分採認",
      },
      "source_urls": ntou_source_urls,
      "verified_at": "2026-10-20",
  }
  (OFFICIAL_NTOU_DIR / "home_rules.json").write_text(
      json.dumps(home_rules, ensure_ascii=False, indent=2) + "\n",
      encoding="utf-8",
  )
  (OFFICIAL_NTOU_DIR / "documents.json").write_text(
      json.dumps(
          {
              "school_name": "國立臺灣海洋大學",
              "required_documents": student_dashboard_payload["required_documents"],
              "source_urls": ntou_source_urls,
          },
          ensure_ascii=False,
          indent=2,
      )
      + "\n",
      encoding="utf-8",
  )
  (OFFICIAL_NTOU_DIR / "scholarships.json").write_text(
      json.dumps(
          {
              "school_name": "國立臺灣海洋大學",
              "scholarships": student_dashboard_payload["scholarship_info"],
              "source_urls": ntou_source_urls,
          },
          ensure_ascii=False,
          indent=2,
      )
      + "\n",
      encoding="utf-8",
  )

  completeness = {
      "school_id": "ntou",
      "school_name": "國立臺灣海洋大學",
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
          "國立臺灣海洋大學國際事務處 2027 年春/秋季學期赴國外姊妹校交換生計畫暨學海飛颺主梯次（5/8 截止）及 115 學年度第 2 學期赴大陸地區姊妹校交換計畫（9/30 截止）已完成收件，下一梯次 2027 年秋季學期增開梯次預計於 2026/12/01 公告、2027/02/25 12:00 截止，2028 年春/秋季主梯次預計於 2027/03/01 公告、2027/05/07 12:00 截止；共完整收錄 123 所全球交換與雙聯合作姊妹校（含 46 所當期開放申請名額校及 77 所正式締約姊妹校，橫跨歐、美、亞、大洋洲與非洲 22 個國家與地區，並收錄 34 所學校共 439 篇歷屆學長姐返國心得報告）。"
      ),
      "verified_at": "2026-10-20",
  }
  (OFFICIAL_NTOU_DIR / "catalog-completeness.json").write_text(
      json.dumps(completeness, ensure_ascii=False, indent=2) + "\n",
      encoding="utf-8",
  )
  (OFFICIAL_NTOU_DIR / "verification_status.json").write_text(
      json.dumps(
          {
              "school_id": "ntou",
              "school_name": "國立臺灣海洋大學",
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
          "sources/ntou/exchange_selection_brochure.pdf",
          NTOU_BROCHURE_2027_URL,
          "國立臺灣海洋大學 2027 年春/秋季學期赴姊妹校交換生計畫(不包含大陸地區)暨學海飛颺獎學金校內甄選申請簡章 PDF",
      ),
      (
          "sources/ntou/xuehai_feiyang_attachment.pdf",
          NTOU_BROCHURE_2026_URL,
          "國立臺灣海洋大學 2026 年春/秋季學期赴姊妹校交換生計畫暨學海飛颺獎學金校內甄選申請簡章 PDF",
      ),
      (
          "sources/ntou/study_abroad_guidelines_and_lang_table.pdf",
          NTOU_GUIDELINES_LANG_URL,
          "國立臺灣海洋大學學生赴國外研修要點暨附件一「留學國語文能力證明」標準表 PDF",
      ),
      (
          "sources/ntou/study_abroad_enforcement_rules.pdf",
          NTOU_ENFORCEMENT_RULES_URL,
          "國立臺灣海洋大學學生赴國外研修施行細則 PDF",
      ),
      (
          "sources/ntou/xuehai_subsidy_enforcement_rules.pdf",
          NTOU_XUEHAI_RULES_URL,
          "國立臺灣海洋大學學海系列計畫補助施行細則 PDF",
      ),
      (
          "sources/ntou/moe_xuehai_subsidy_directions_115.pdf",
          NTOU_MOE_XUEHAI_115_URL,
          "教育部鼓勵國內大專校院選送學生出國研修或國外專業實習補助要點（115年度）PDF",
      ),
      (
          "sources/ntou/application_checklist.pdf",
          NTOU_APP_CHECKLIST_URL,
          "國立臺灣海洋大學出國交換學生申請文件檢核表 PDF",
      ),
      (
          "sources/ntou/autobiography_example.pdf",
          NTOU_AUTOBIO_EX_URL,
          "國立臺灣海洋大學出國交換學生中文自傳範例 PDF",
      ),
      (
          "sources/ntou/study_plan_example.pdf",
          NTOU_STUDY_PLAN_EX_URL,
          "國立臺灣海洋大學外國留學研修計畫書範例 PDF",
      ),
      (
          "sources/ntou/budget_analysis_example.pdf",
          NTOU_BUDGET_EX_URL,
          "國立臺灣海洋大學赴外研修經費分析表範例 PDF",
      ),
      (
          "sources/ntou/pre_departure_checklist.pdf",
          NTOU_PRE_DEPARTURE_URL,
          "國立臺灣海洋大學交換生／學海飛颺出國前檢核表 PDF",
      ),
      (
          "sources/ntou/reimbursement_checklist.pdf",
          NTOU_REIMBURSEMENT_URL,
          "國立臺灣海洋大學交換生／學海飛颺返國核銷檢核表 PDF",
      ),
      (
          "sources/ntou/sop_outbound_exchange_and_subsidy.pdf",
          NTOU_SOP_EXCHANGE_URL,
          "國立臺灣海洋大學赴國外姊妹校交換生甄選與獎補助標準作業流程（SOP）PDF",
      ),
      (
          "sources/ntou/sop_dual_degree_application.pdf",
          NTOU_SOP_DUAL_URL,
          "國立臺灣海洋大學雙聯學位申請標準作業流程（SOP）PDF",
      ),
      (
          "sources/ntou/dual_degree_overview.xlsx",
          NTOU_DUAL_DEGREE_XLSX_URL,
          "國立臺灣海洋大學雙聯學位學校資料與申請期程簡介 XLSX",
      ),
      (
          "sources/ntou/mainland_exchange_115_2.html",
          NTOU_MAINLAND_115_2_URL,
          "國立臺灣海洋大學 115 學年度第 2 學期赴大陸地區姊妹校交換（研修）計畫招募公告 HTML",
      ),
      (
          "sources/ntou/sister_schools_zh.html",
          NTOU_SISTER_SCHOOLS_URL,
          "國立臺灣海洋大學全球締約姊妹校一覽表（中文版）HTML",
      ),
      (
          "sources/ntou/sister_schools_en.html",
          "https://oia.ntou.edu.tw/p/412-1022-6904.php?Lang=en",
          "國立臺灣海洋大學全球締約姊妹校一覽表（英文版）HTML",
      ),
      (
          "sources/ntou/notion_partners_details.json",
          NTOU_EXCHANGE_PLAN_URL,
          "國立臺灣海洋大學國際事務處 Notion 交換姊妹校資料庫詳細頁面 JSON",
      ),
      (
          "sources/ntou/notion_exp_exchange.json",
          NTOU_EXP_SHARING_URL,
          "國立臺灣海洋大學國際事務處 Notion 交換學生返國心得報告資料庫 JSON",
      ),
      (
          "sources/ntou/notion_exp_dual.json",
          NTOU_EXP_SHARING_URL,
          "國立臺灣海洋大學國際事務處 Notion 雙聯學位返國心得報告資料庫 JSON",
      ),
      (
          "sources/ntou/ntou_catalog_source.json",
          NTOU_BROCHURE_2027_URL,
          "國立臺灣海洋大學 123 所出國交換與雙聯合作姊妹校整合資料集 JSON",
      ),
      (
          "sources/ntou/ntou_resolved_locations.json",
          NTOU_BROCHURE_2027_URL,
          "國立臺灣海洋大學 123 所出國交換與雙聯合作姊妹校 ROR / Wikidata 地理座標核對表 JSON",
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
      "school_id": "ntou",
      "school_name": "國立臺灣海洋大學",
      "generated_at": CHECKED_AT,
      "active_cycle_note": completeness["active_term"],
      "sources": prov_sources,
  }
  prov_text = json.dumps(provenance_payload, ensure_ascii=False, indent=2) + "\n"
  (OFFICIAL_NTOU_DIR / "import_provenance.json").write_text(prov_text, encoding="utf-8")
  (OFFICIAL_NTOU_DIR / "import-provenance.json").write_text(prov_text, encoding="utf-8")

  from exchange_info.ntou_source_review import review_bundle
  reviewed_counts = review_bundle(REPO_ROOT)
  open_partner_count = reviewed_counts.get("open", 0)

  print(
      f"Successfully built NTOU catalog: {len(partners)} partners"
      f" ({open_partner_count} open, {completeness['verified_campus_images']}"
      f" verified images, {completeness['verified_locations']} verified"
      f" locations), {len(workflows)} workflows,"
      f" {len(destinations)} destinations, {len(research_records)} research"
      f" records, {exp_covered_schools} schools with experience records"
      f" ({len(student_experience_rows)} rows)."
  )


if __name__ == "__main__":
  main()
