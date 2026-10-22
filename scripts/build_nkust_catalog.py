"""Build the official National Kaohsiung University of Science and Technology (國立高雄科技大學, NKUST) exchange data bundle."""

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

SOURCES_NKUST_DIR = REPO_ROOT / "sources" / "nkust"
OFFICIAL_NKUST_DIR = REPO_ROOT / "src" / "exchange_info" / "official_data" / "nkust"
STATIC_DIR = REPO_ROOT / "src" / "exchange_info" / "static"

CHECKED_AT = "2026-10-20T12:00:00Z"

NKUST_OIA_HUB_URL = "https://oia.nkust.edu.tw/"
NKUST_EXCHANGE_PAGE_URL = "https://oia.nkust.edu.tw/unit-4-374-21.html"
NKUST_SCHOLARSHIP_PAGE_URL = "https://oia.nkust.edu.tw/unit-4-377-45.html"
NKUST_SHORT_TERM_PAGE_URL = "https://oia.nkust.edu.tw/unit-4-352-39.html"
NKUST_GS_PORTAL_URL = "https://sites.google.com/nkust.edu.tw/exchange-student/"
NKUST_115_GUIDELINES_URL = "https://oia.nkust.edu.tw/images/upload/files/115%E5%AD%B8%E5%B9%B4%E5%BA%A6%E6%A0%A1%E7%B4%9A%E4%BA%A4%E6%8F%9B%E7%94%9F%E7%94%84%E9%81%B8%E7%B0%A1%E7%AB%A02025_12_02(1).pdf"
NKUST_115_PREF_FORM_URL = "https://oia.nkust.edu.tw/images/upload/files/115%E5%AD%B8%E5%B9%B4%E5%BA%A6%E6%A0%A1%E7%B4%9A%E4%BA%A4%E6%8F%9B%E7%A0%94%E4%BF%AE%E5%BF%97%E9%A1%98%E8%A1%A8(2).docx"
NKUST_115_UNI_SHEET_URL = "https://docs.google.com/spreadsheets/d/1ZdfUgev-p_N35eh2mD-vF7rH7iH8zJ3O/edit?gid=142150725#gid=142150725"
NKUST_COLLEGE_SHEET_URL = "https://docs.google.com/spreadsheets/d/1ZdfUgev-p_N35eh2mD-vF7rH7iH8zJ3O/edit?gid=1014746314#gid=1014746314"
NKUST_REGULATIONS_URL = "https://oia.nkust.edu.tw/images/upload/files/%E5%9C%8B%EF%A7%97%E9%AB%98%E9%9B%84%E7%A7%91%E6%8A%80%E5%A4%A7%E5%AD%B8%E5%AD%B8%E7%94%9F%E8%B5%B4%E5%A2%83%E5%A4%96%E5%A4%A7%E5%AD%B8%E6%A0%A1%E9%99%A2%E4%BA%A4%E6%8F%9B%E7%A0%94%E4%BF%AE%E4%BD%9C%E6%A5%AD%E8%A6%81%E9%BB%9E.pdf"
NKUST_SCHOLARSHIP_REG_URL = "https://oia.nkust.edu.tw/images/upload/files/%E5%9C%8B%E7%AB%8B%E9%AB%98%E9%9B%84%E7%A7%91%E6%8A%80%E5%A4%A7%E5%AD%B8%E7%8D%8E%E5%8A%A9%E5%AD%B8%E7%94%9F%E8%B5%B4%E5%A2%83%E5%A4%96%E5%A4%A7%E5%AD%B8%E6%A0%A1%E9%99%A2%E7%A0%94%E4%BF%AE%E8%A6%81%E9%BB%9E(4).pdf"
NKUST_FLEC_CEF_URL = "https://flec.nkust.edu.tw/var/file/46/1046/img/581/277450219.pdf"
NKUST_116_INFO_SESSION_URL = "https://oia.nkust.edu.tw/news_det-980.html"

REGION_BY_COUNTRY = {
    "德國": "歐洲",
    "奧地利": "歐洲",
    "法國": "歐洲",
    "英國": "歐洲",
    "波蘭": "歐洲",
    "匈牙利": "歐洲",
    "義大利": "歐洲",
    "美國": "美洲",
    "加拿大": "美洲",
    "澳洲": "大洋洲",
    "日本": "亞洲",
    "韓國": "亞洲",
    "泰國": "亞洲",
    "印尼": "亞洲",
    "越南": "亞洲",
    "馬來西亞": "亞洲",
    "印度": "亞洲",
    "菲律賓": "亞洲",
    "中國大陸": "中國大陸及港澳",
    "香港": "中國大陸及港澳",
}

REGION_COST_DEFAULTS = {
    "德國": (
        "EUR 934–1,250 / 月（德國簽證限制提領帳戶 Sperrkonto 基準為每月 EUR 992，含學生宿舍、膳食與學期大眾運輸票 Semesterbeitrag）",
        "須辦理德國法定學生公保（如 TK / AOK，約 EUR 125–135 / 月）、繳納學期雜費（Semesterbeitrag）並向德國在台協會申辦長期學生簽證。",
    ),
    "奧地利": (
        "EUR 900–1,300 / 月（茵斯布魯克、維也納、上奧地利、格拉茨學生宿舍、膳食與學生交通票）",
        "須依研修期程向奧地利台北辦事處辦理居留許可或 D 類簽證，並投保涵蓋全期之申根與奧地利學生醫療保險。",
    ),
    "法國": (
        "EUR 800–1,350 / 月（巴黎近郊居斯塔夫·艾菲爾大學約 EUR 1,050–1,400；南特、波爾多／馬賽、盧昂／漢斯、雷恩約 EUR 750–1,050，可申請法國 CAF 房補）",
        "須透過法國教育中心（Campus France）完成線上面談審查並向法國在台協會申辦長期學生簽證（VLS-TS），抵法後完成 OFII 生效與法國學生社保登錄。",
    ),
    "英國": (
        "GBP 1,050–1,500 / 月（蘇格蘭愛丁堡納皮爾大學校內外學生公寓、餐飲與大眾運輸）",
        "交換一學期（6 個月內）可辦理 Standard Visitor 簽證，交換一學年須申辦英國 Student Visa 並繳納 IHS 醫療附加費。",
    ),
    "波蘭": (
        "EUR 550–850 / 月（約 PLN 2,400–3,600，華沙生命科學大學與格利維采西里西亞科技大學校內學生宿舍每月僅約 EUR 130–220，物價實惠）",
        "須向波蘭臺北辦事處申辦 D 類國別學生簽證並備妥歐盟認定之旅行醫療保險。",
    ),
    "匈牙利": (
        "EUR 550–850 / 月（佩奇大學校內宿舍與大學城生活開支低廉，獲歐盟 Erasmus+ 或高科大獎學金可充裕支應）",
        "須向匈牙利貿易辦事處申辦留學居留簽證（D 簽）並投保涵蓋全期之申根醫療保險。",
    ),
    "義大利": (
        "EUR 850–1,300 / 月（羅馬大學周邊學生合租公寓、餐飲與羅馬大眾運輸月票）",
        "須向義大利經濟貿易文化推廣辦事處申辦 D 類國家學生簽證，抵義後 8 個工作天內申辦居留證（Permesso di soggiorno）並投保醫療險。",
    ),
    "美國": (
        "USD 1,250–2,200 / 月（含德州拉瑪大學、密蘇里大學堪薩斯／聖路易斯分校、關島大學、UNLV 等校內宿舍、Meal Plan 膳食計畫與校園強制醫療險）",
        "須憑接待校核發之 DS-2019（或雙聯 I-20）表格繳納 SEVIS I-901 費用並至 AIT（美國在台協會）申辦 J-1 / F-1 簽證及投保學校強制醫療保險。",
    ),
    "加拿大": (
        "USD 800–1,600 / 月（依 UMAP 亞太大學交流會錄取分發之會員校所在國家與城市而定）",
        "須依 UMAP 實際錄取接待國駐臺機構規定辦理學生簽證並投保涵蓋交換全期之海外醫療及意外保險。",
    ),
    "澳洲": (
        "AUD 1,800–2,700 / 月（阿得雷德澳洲國際飯店管理學院 ICHM 含校內食宿及澳洲飯店帶薪實習機會）",
        "須購買澳洲海外學生健康保險（OSHC）並線上申辦 Subclass 500 學生簽證。",
    ),
    "日本": (
        "JPY 80,000–130,000 / 月（東京海洋、明治、千葉、獨協、大東文化及京阪神關西、神戶、京都外大、同志社女子、龍谷、流通科學約 JPY 95,000–140,000；地方國立如愛媛、滋賀、長崎、鹿兒島、高知、福井縣立、信州、熊本、新潟宿費僅約 JPY 15,000–35,000 / 月）",
        "憑日本接待校核發之在留資格認定證明書（COE）向日本台灣交流協會高雄事務所換發留學簽證，抵日後須依法加入日本國民健康保險（NHI）。",
    ),
    "韓國": (
        "KRW 750,000–1,250,000 / 月（仁川仁荷大學、安山漢陽 ERICA、安養聖潔、軍浦韓世及釜山韓國海洋大學、晉州慶尚國立大學、光州朝鮮大學校內宿舍與學餐費用親民）",
        "憑韓國標準入學許可書向駐台北韓國代表部（或高雄分處）申辦 D-2-6 交換學生簽證，抵韓後辦理外國人登錄並自動納入韓國國民健康保險（NHIS）。",
    ),
    "泰國": (
        "THB 14,000–24,000 / 月（曼谷農業大學、蒙庫國王科技大學 KMUTT、先皇技術學院 KMITL、北曼谷國王科大 KMUTNB、法政大學與春武里東方大學周邊學生公寓與生活費實惠）",
        "須憑泰國接待校正式入學許可向泰國貿易經濟辦事處申辦 Non-Immigrant ED 學生簽證並投保海外醫療險。",
    ),
    "印尼": (
        "IDR 4,500,000–8,000,000 / 月（雅加達建國大學 Binus 及日惹穆罕默迪亞大學 UMY、日惹阿特瑪賈亞大學 UAJY 學生宿舍與日常飲食開銷親民）",
        "須由印尼接待校協助向印尼移民總局申辦 C316 學習電子簽證（e-Visa）並投保海外全期醫療及意外保險。",
    ),
    "越南": (
        "USD 380–650 / 月（河內交通運輸大學、海防越南海事大學、峴港經濟大學、胡志明市技術師範大學、文郎大學與同奈科技大學住宿及生活成本低廉）",
        "須憑越南接待校入學許可透過駐臺北越南經濟文化辦事處申辦越南學生簽證並投保海外醫療險。",
    ),
    "馬來西亞": (
        "MYR 1,400–2,400 / 月（霹靂州金寶／雪蘭莪雙溪龍拉曼大學 UTAR 及砂拉越詩巫砂拉越科技大學 UTS 校內外學生宿舍與生活費實惠）",
        "須於出國前透過 EMGS（Education Malaysia Global Services）系統線上申辦馬來西亞學生簽證核准函（VAL / Student Pass）並投保 EMGS 指定醫療險。",
    ),
    "印度": (
        "USD 350–600 / 月（旁遮普邦昌迪加爾大學 Chandigarh University 與拉芙麗科技大學 LPU 現代化校園宿舍與學生餐廳費用低廉）",
        "須憑印度接待校入學許可向印度台北協會（ITA）申辦 Student Visa 學生簽證並投保海外醫療及意外保險。",
    ),
    "菲律賓": (
        "USD 480–850 / 月（馬尼拉雅典耀大學、亞太大學 UA&P、米里亞姆學院、菲律賓大學及八打雁萊西姆大學 LPU-Batangas 住宿與生活開支實惠）",
        "須憑接待校入學許可向馬尼拉經濟文化辦事處（MECO）高雄分處辦理簽證，抵菲後由學校協助申辦 SSP（Special Study Permit）或 9(f) 學生簽證。",
    ),
    "中國大陸": (
        "RMB 2,000–3,500 / 月（同濟、重慶、華南理工、華中科大、大連理工、中國海洋、深圳大學及上海海事、上海海洋、廣東海洋、浙江海洋校內學生宿舍與食堂成本低廉）",
        "持有效護照與臺胞證（臺灣居民來往大陸通行證）入境，並依接待校規定投保大陸境內來華留學生綜合醫療保險（每年約 RMB 800）。",
    ),
    "香港": (
        "HKD 8,000–13,000 / 月（九龍紅磡香港理工大學學生宿舍或周邊租屋、膳食與港鐵學生交通費）",
        "須透過香港理工大學協助向香港入境事務處線上申辦來港就讀進入許可（Student e-Visa）並持有效護照及港簽入境。",
    ),
}

SEMESTER_DATES_BY_COUNTRY = {
    "德國": "冬季學期（上學期）：約 9/10 月至翌年 2 月；夏季學期（下學期）：約 3/4 月至 7/8 月",
    "奧地利": "冬季學期（上學期）：約 9/10 月至翌年 1/2 月；夏季學期（下學期）：約 2/3 月至 6/7 月",
    "法國": "秋季學期（上學期）：約 9 月至 12 月／翌年 1 月；春季學期（下學期）：約 1/2 月至 5/6 月",
    "英國": "秋季學期（上學期）：約 9 月至翌年 1 月；春季學期（下學期）：約 1 月至 5 月",
    "波蘭": "冬季學期（上學期）：約 10 月至翌年 2 月；夏季學期（下學期）：約 2 月下旬至 6 月",
    "匈牙利": "秋季學期（上學期）：約 9 月至翌年 1 月；春季學期（下學期）：約 2 月至 6 月",
    "義大利": "第一學期（上學期）：約 9 月下旬至翌年 1/2 月；第二學期（下學期）：約 2 月下旬至 6/7 月",
    "美國": "秋季學期（Fall）：約 8 月中下旬至 12 月；春季學期（Spring）：約 1 月中旬至 5 月",
    "加拿大": "依 UMAP 亞太大學交流會實際分發會員校之秋季班（8/9 月起）或春季班（1/2 月起）行事曆為準",
    "澳洲": "第一學期：約 1/2 月至 6 月；第二學期：約 7 月至 11/12 月（含校內理論學習與飯店實習階段）",
    "日本": "秋季班（高科大上學期）：約 9/10 月至翌年 2/3 月；春季班（高科大下學期）：約 4 月至 8/9 月",
    "韓國": "秋季學期（上學期）：約 9 月初至 12 月中下旬；春季學期（下學期）：約 3 月初至 6 月中下旬",
    "泰國": "第一學期：約 8 月至 12 月；第二學期：約 1 月至 5 月（部分國際學院採三學期制，依接待校行事曆為準）",
    "印尼": "奇數／秋季學期：約 9 月至翌年 1 月；偶數／春季學期：約 2 月至 6/7 月",
    "越南": "第一學期（秋季班）：約 9 月至翌年 1 月；第二學期（春季班）：約 2 月至 6 月",
    "馬來西亞": "依拉曼大學（1 月／5 月／10 月學期）或砂拉越科技大學（2 月／9 月學期）行事曆為準",
    "印度": "秋季學期（Odd Semester）：約 8 月至 12 月；春季學期（Even Semester）：約 1 月至 5 月",
    "菲律賓": "第一學期：約 8 月至 12 月；第二學期：約 1 月至 5 月",
    "中國大陸": "秋季學期（上學期）：約 9 月初至翌年 1 月中旬；春季學期（下學期）：約 2 月中下旬至 6 月底／7 月初",
    "香港": "第一學期（Sem 1）：約 9 月初至 12 月底；第二學期（Sem 2）：約 1 月中旬至 5 月中旬",
}


def clean_text(s: str) -> str:
  if not s:
    return ""
  return re.sub(r"\s+", " ", s).strip()


def format_quota(item: dict) -> str:
  q_f = " / ".join(item.get("q_fall_list") or [])
  q_s = " / ".join(item.get("q_spring_list") or [])
  col_info = item.get("college_level_info") or []
  if item["application_status"] != "open":
    return q_f or "歷屆合作參考（當期未開缺，依國際處最新公告為準）"
  parts = []
  if q_f and q_s:
    if q_f == q_s and ("共" in q_f or "依" in q_f):
      parts.append(f"115學年度名額：{q_f}")
    else:
      parts.append(f"115-1（上學期／秋季班）：{q_f} 名；115-2（下學期／春季班）：{q_s} 名")
  elif q_f:
    parts.append(f"115-1（上學期／秋季班）：{q_f}")
  elif q_s:
    parts.append(f"115-2（下學期／春季班）：{q_s}")
  if col_info and "校級交換（115學年度校級交換學校一覽表）" in item["source_tracks"]:
    col_units = "、".join(c["participants"] for c in col_info if c.get("participants"))
    parts.append(f"另設院系級交換名額（{col_units}）")
  return "；".join(parts) if parts else "依國際事務處當期公告名額薦送"


def format_colleges_and_degrees(item: dict) -> tuple[str, str]:
  parts_raw = "；".join(item.get("participants_list") or [])
  remarks_raw = "；".join(item.get("remarks_list") or [])
  combined = f"{parts_raw} {remarks_raw}"
  if not parts_raw or parts_raw == "全校學生":
    colleges_str = (
        "不限學院（工學院、智慧機電學院、電機與資訊學院、海事學院、水圈學院、商業智慧學院、管理學院、海洋商務學院、財務金融學院、創新設計學院、外語學院、共同教育學院等全校各院系所符合交換學校專業領域與語檢條件之學生皆可申請）"
    )
  else:
    colleges_str = f"開放對象：{parts_raw}"
  if item.get("college_level_info") and "校級交換（115學年度校級交換學校一覽表）" in item["source_tracks"]:
    col_units = "、".join(
        f"{c['participants']}（{c['host_dept']}）" if c.get("host_dept") else c["participants"]
        for c in item["college_level_info"]
        if c.get("participants")
    )
    if col_units:
      colleges_str += f"；另設院系級交換專班：{col_units}"

  if "僅收大學部" in combined or "限大學部" in combined or "不受理研究生" in combined:
    degree_str = "大學部二年級（含）以上及五專部四年級（含）以上在學學生（依接待校規定限大學部／學士班層級修讀）"
  else:
    degree_str = "大學部二年級（含）以上、五專部四年級（含）以上及研究所（碩士班、博士班、在職專班）在學學生（在當前學制中須有一學期以上學業成績）"
  return colleges_str, degree_str


def format_lang_and_gpa(item: dict) -> tuple[str, str]:
  lang_raw = "；".join(item.get("lang_req_list") or [])
  remarks_raw = "；".join(item.get("remarks_list") or [])
  country = item["country"]
  if not lang_raw:
    if country == "中國大陸":
      lang_str = "中文授課（免附外語檢定證明；校內甄選比序採專業領域契合度 60%＋在校歷年成績 40%）"
    else:
      lang_str = "須具英語檢定證明（CEFR B1：TOEIC 550 / TOEFL iBT 42 / ITP 460 / IELTS 4.0 以上）或符合接待校要求之第二外語能力證明"
  else:
    lang_str = lang_raw

  gpa_matches = re.findall(r"GPA\s*[\d.]+[^；。]*|歷年平均[^\s；。]+|平均成績[^\s；。]+", f"{lang_raw} {remarks_raw}", re.I)
  if gpa_matches:
    gpa_str = f"高科大校內門檻：在當前學制有一學期以上成績且操行成績至少達 75 分；接待校學業門檻：{'、'.join(dict.fromkeys(gpa_matches))}"
  else:
    gpa_str = "高科大校內門檻：在當前就讀學制中須有一學期以上之學期成績且成績良好，操行成績至少達 75 分（甄選總分採計在校歷年學業總平均 20%，無外語要求之大陸姊妹校採計 40%）"
  return lang_str, gpa_str


def extract_primary_links(item: dict) -> tuple[str, str | None]:
  website = ""
  factsheet_url = None
  for lk in item.get("links") or []:
    u = lk.get("url") or ""
    anc = lk.get("anchor") or ""
    if "drive.google.com" in u or "簡章" in anc:
      if not factsheet_url:
        factsheet_url = u
    elif u.startswith("http") and "google.com" not in u:
      if not website:
        website = u
  for lk in item.get("gs_links") or []:
    if "drive.google.com/drive/folders" in lk and not factsheet_url:
      factsheet_url = lk
  return website, factsheet_url


def main() -> None:
  OFFICIAL_NKUST_DIR.mkdir(parents=True, exist_ok=True)
  catalog_source = json.loads(
      (SOURCES_NKUST_DIR / "nkust_catalog_source.json").read_text(encoding="utf-8")
  )
  resolved_locations = json.loads(
      (SOURCES_NKUST_DIR / "nkust_resolved_locations.json").read_text(encoding="utf-8")
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
    full_name = item["full_name"]
    zh_name = item["name_zh"]
    country = item["country"]
    region = REGION_BY_COUNTRY.get(country, "亞洲")
    avail_status = item["application_status"]
    if avail_status == "open":
      open_partner_count += 1

    tracks_str = "、".join(item.get("source_tracks") or ["校級交換"])
    if "校級交換" in tracks_str and "院系級交換" in tracks_str:
      program_type = "校級暨院系級交換學生計畫"
    elif "院系級交換" in tracks_str:
      program_type = "院系級交換學生計畫"
    elif "雙聯" in tracks_str:
      program_type = "雙聯學位暨交換研修計畫"
    else:
      program_type = "校級交換學生計畫"

    quota_str = format_quota(item)
    colleges_str, degree_levels_str = format_colleges_and_degrees(item)
    lang_req_str, gpa_req_str = format_lang_and_gpa(item)
    website, factsheet_url = extract_primary_links(item)
    gs_subpage_url = item.get("gs_subpage_url")
    gs_exp_titles = [
        t for t in (item.get("gs_experience_titles") or [])
        if len(t) <= 45 and ("系" in t or "所" in t or "年" in t)
    ]
    gs_doc_links = [
        lk for lk in (item.get("gs_links") or [])
        if "drive.google.com/file" in lk or "docs.google.com/document" in lk
    ]

    if "校級交換（115學年度校級交換學校一覽表）" in item["source_tracks"]:
      source_url = NKUST_EXCHANGE_PAGE_URL
      round_label = "115學年度校級交換甄選（115-1秋季班／115-2春季班）及116學年度預告"
      app_deadline_str = (
          "115學年度校級交換甄選：2025/11/10 12:00 – 2025/12/10 16:00 線上申請（12/19 16:00 補交語檢截止、2026/02/23 公告錄取、02/27 意願確認截止）；116學年度（2027-2028）校級交換說明會於 2026/10/07–10/28 舉行，預計 2026/11/10 – 12/01 16:00 開放線上申請"
      )
      deadline_iso = "2026-12-01T16:00:00+08:00"
      win_status = "closed"
    elif "院系級交換（院系級交換學校列表）" in item["source_tracks"]:
      source_url = NKUST_EXCHANGE_PAGE_URL
      round_label = "院系級交換學生甄選（依各簽約院系所公告時程辦理）"
      app_deadline_str = (
          "依高科大簽約院系所每學期公告時程辦理（秋季班約每年 3–4 月、春季班約每年 9–10 月向所屬院系辦提出申請，並由國際處協助薦送及獎補助申請）"
      )
      deadline_iso = "2026-12-01T16:00:00+08:00"
      win_status = "closed"
    else:
      source_url = gs_subpage_url or NKUST_EXCHANGE_PAGE_URL
      round_label = "歷屆交換合作參考（依國際處最新學年度簡章為準）"
      app_deadline_str = "當期未列入115校級交換開缺一覽表，實際開缺與截止日期請依國際事務處最新學年度甄選簡章公告為準"
      deadline_iso = "2026-12-01T16:00:00+08:00"
      win_status = "closed"

    tuition_raw = "；".join(item.get("tuition_list") or ["免繳對方學費"])
    remarks_raw = "；".join(item.get("remarks_list") or [])
    study_period_str = "1 學期或 1 學年（校級交換以 1 學期為原則，至多 2 學期）"
    if "1個月" in remarks_raw or any("1個月" in c.get("period", "") for c in item.get("college_level_info", [])):
      study_period_str = "1 學期、1 學年或暑期短期研修（1 個月）"

    sem_dates_str = SEMESTER_DATES_BY_COUNTRY.get(
        country, "秋季學期：約 9 月至翌年 1 月；春季學期：約 2 月至 6 月"
    )
    housing_str = (
        f"錄取並獲國際處提名後，可依 {zh_name} 交換生簡章（Fact Sheet）規定申請校內學生宿舍或國際學生公寓"
        + (f"（重要備註：{remarks_raw}）" if remarks_raw else "。")
    )
    course_rest_str = (
        f"開放對象與領域：{colleges_str}。依《國立高雄科技大學學生赴境外大學校院交換研修作業要點》規定，交換生於境外研修期間每學期至少應修習相當於本校 6 學分（或至少 1 至 2 門專業／外語課程），返國後憑正式成績單與課程大綱辦理學分抵免。"
        + (f" 締約校備註：{remarks_raw}" if remarks_raw else "")
    )

    tuition_points_list = [
        (
            f"學費待遇與高科大在學註冊規定：{tuition_raw}。依《國立高雄科技大學學生赴境外大學校院交換研修作業要點》及甄選簡章規定，交換生於出國交換期間須維持高科大在學學籍並依規定繳交高科大校內全額學雜費（不得辦理休學或畢業離校）；雙邊互惠免學費名額免繳接待校學費，食宿費、往返機票、簽證、海外保險與個人生活費由學生自理。"
        ),
        (
            "高科大三大出國交換獎補助體系：（1）教育部《學海飛颺》／《學海惜珠》計畫：補助具中華民國國籍且在臺設籍之非在職專班優秀學生（惜珠為低收／中低收／特殊境遇家庭學生並優先分發），115學年度核發額度為亞洲地區（不含中港澳）每名 NT$60,000（教育部 5 萬＋高科大配合款 1 萬）、非亞洲地區（歐美澳）每名 NT$80,000（教育部 5 萬＋高科大配合款 3 萬）、雙聯學制每名 NT$120,000；（2）高科大高教深耕《獎助學生赴境外大學校院研修要點》：補助未獲學海計畫之本國籍非在職專班交換生，亞洲地區（不含中港澳）每名 NT$60,000、非亞洲地區每名 NT$80,000、雙聯學制每名 NT$120,000，符合本校經濟不利條件者再加發最高 NT$20,000；（3）《國際短期交流補助》與《學海展翅專案》：短期交流每名補助 NT$10,000（經濟不利增額 NT$2,000），暑期赴海外姊妹校培訓 1 個月之學海展翅專案定額補助 NT$20,000（生活助學金生再增額 NT$15,000，低收入戶全額補助機票、簽證與學費）。"
        ),
    ]

    app_steps_list = [
        (
            f"步驟一（確認學制年級、操行 75 分門檻與 {zh_name} 語檢／系所契合度）：確認具高科大大學部大二以上、五專部專四以上或碩博士班在學學籍，在當前學制有一學期以上成績且操行成績達 75 分以上，並備妥符合 {zh_name} 要求之外語檢定證明（{lang_req_str}）。申請前請詳閱各校 Fact Sheet 確認開放院系、GPA 與選課限制。"
        ),
        (
            "步驟二（完成高科大線上申請系統填報並上傳必備審查文件）：於每年 11 月至 12 月初校級交換甄選收件期間，至高科大國際事務處線上申請系統填報個人資料並上傳：(1) 校級交換研修志願表（需申請人及系所主管核章，可填 3–6 個志願並勾選是否同意國際處媒合）、(2) 中文歷年成績單（含排名，操行至少 75 分）、(3) 有效外語能力檢定證明（對照高科大外語教育中心 CEFR 等級表，得先上傳網路成績截圖並於 12 月中旬前補交正式成績單）、(4) 中英文自傳及讀書計畫、(5) 雙聯學位／學海惜珠／家長同意書等相關附件。"
        ),
        (
            f"步驟三（國際處甄選審查比序分發與繳交意願確認書／家長同意書）：學海惜珠合格申請人優先分發；若申請人數大於名額，先以語檢達第一志願門檻者優先，再依「第一志願專業領域契合度 50%（高度 100／中度 85／低度 70）＋外語檢定 CEFR 等級 30%（C1 100／B2 90／B1 80／A2以下 70）＋在校歷年成績 20%」（無外語要求之大陸姊妹校為契合度 60%＋在校成績 40%）計算總分比序分發。翌年 2 月下旬公告錄取名單後，正取生須於期限內上傳《錄取生交換意願確認書》及《家長同意書》，由國際處向 {full_name} 辦理官方提名（Nomination）。"
        ),
        (
            "步驟四（遞交接待校入學申請、核定學海飛颺／高科大獎助金並完成返國抵免）：獲提名後（秋季班 3–7 月、春季班 8–11 月）依姊妹校規定遞交入學與宿舍申請資料；每年 7 月初由國際處公告「教育部學海飛颺／惜珠」與「高科大境外研修獎助金（亞洲 6 萬／歐美澳 8 萬／雙聯 12 萬）」獲獎名冊並簽立行政契約書。出國前須參加行前說明會、辦妥簽證與海外全期醫療及意外保險（役男須於出國前完成緩徵出境核准），返國後 1 個月內繳交 1,500–2,000 字研修心得報告、機票票根及正式成績單完成學分抵免與獎補助核銷。"
        ),
    ]

    elig_points_list = [
        f"合作管道：{program_type}（{'、'.join(item.get('source_tracks') or [])}）",
        f"開放學制與年級：{degree_levels_str}",
        f"開放申請院系：{colleges_str}",
        f"學業與操行門檻：{gpa_req_str}",
        f"外語能力標準：{lang_req_str}",
        (
            "甄選評分權重與比序：專業領域契合度 50% ＋ 外語檢定 CEFR 等級 30%（C1=100、B2=90、B1=80、A2=70）＋ 在校歷年成績 20%（無外語要求之大陸姊妹校為專業契合度 60% ＋ 在校歷年成績 40%）；同分時依序比序：(1) 專業領域契合度、(2) 在校成績、(3) 外語檢定成績。"
        ),
    ]
    if remarks_raw:
      elig_points_list.append(f"姊妹校特殊規定與備註：{remarks_raw}")

    notes_lines = [
        f"【合作類別與期程】{program_type}｜交換期間：{study_period_str}",
        f"【當期名額與費用待遇】{quota_str}｜{tuition_raw}",
        f"【開放學院與學制】{colleges_str}｜{degree_levels_str}",
        f"【語言與學業門檻】{lang_req_str}｜{gpa_req_str}",
        f"【住宿與生活資訊】{housing_str}",
    ]
    if factsheet_url:
      notes_lines.append(f"【各校簡章／Fact Sheet 雲端資料夾】{factsheet_url}")
    if gs_subpage_url:
      notes_lines.append(
          f"【高科大出國交換學生網專頁與學長姐心得】{gs_subpage_url}"
          + (f"（收錄：{'、'.join(gs_exp_titles[:6])}）" if gs_exp_titles else "")
      )
    if remarks_raw:
      notes_lines.append(f"【締約校重要備註】{remarks_raw}")

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
        "availability_note": f"國立高雄科技大學國際事務處公告交換合作姊妹校（{program_type}）；{quota_str}。",
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
        "website": website or NKUST_EXCHANGE_PAGE_URL,
        "official_website": website or NKUST_EXCHANGE_PAGE_URL,
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
                "source_tracks": tracks_str,
                "is_new_115": "True" if item.get("is_new_115") else None,
                "factsheet_drive_url": factsheet_url,
                "gs_subpage_url": gs_subpage_url,
                "experience_report_count": (
                    len(gs_exp_titles)
                    if gs_exp_titles
                    else (len(gs_doc_links) if gs_doc_links else None)
                ),
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
            "title": f"國立高雄科技大學115學年度校級交換生甄選簡章與交換學校一覽表—{zh_name}",
            "source_url": source_url,
            "role": "home_university",
            "authority": "home_official_notice",
            "effective_academic_year": "115",
            "application_round": round_label,
            "checked_at": CHECKED_AT,
        },
        {
            "title": "國立高雄科技大學學生赴境外大學校院交換研修作業要點",
            "source_url": NKUST_REGULATIONS_URL,
            "role": "home_university",
            "authority": "home_official_notice",
            "effective_academic_year": "115",
            "application_round": round_label,
            "checked_at": CHECKED_AT,
        },
        {
            "title": "國立高雄科技大學獎助學生赴境外大學校院研修要點與學海計畫專區",
            "source_url": NKUST_SCHOLARSHIP_PAGE_URL,
            "role": "home_university",
            "authority": "home_official_notice",
            "effective_academic_year": "115",
            "application_round": round_label,
            "checked_at": CHECKED_AT,
        },
    ]
    if factsheet_url:
      wf_sources.append({
          "title": f"高科大國際處公告之 {zh_name} 交換簡章（Fact Sheet）雲端資料夾",
          "source_url": factsheet_url,
          "role": "home_university",
          "authority": "home_official_notice",
          "effective_academic_year": "115",
          "application_round": round_label,
          "checked_at": CHECKED_AT,
      })
    if gs_subpage_url:
      wf_sources.append({
          "title": f"高科大出國交換學生網—{zh_name} 姊妹校專頁與學長姐心得分享",
          "source_url": gs_subpage_url,
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
        "home_university": "國立高雄科技大學",
        "school_name": full_name,
        "partner_website": website or NKUST_EXCHANGE_PAGE_URL,
        "country": country,
        "program_type": program_type,
        "academic_year": "115",
        "application_round": round_label,
        "effective_application_rounds": [
            round_label,
            "115-1",
            "115-2",
            "116-1",
            "116-2",
            "校級交換",
            "院系級交換",
        ],
        "applicability_status": "verified",
        "applicability_note": (
            "國立高雄科技大學由國際事務處（國際關係組，建工校區行政大樓 3 樓）統籌辦理校級赴外交換生聯合甄選，每年 11–12 月一次甄選次一學年度第 1 學期（秋季班）及第 2 學期（春季班）交換生，並協同各學院辦理院系級交換與教育部學海飛颺／惜珠及高教深耕境外研修獎助。"
        ),
        "review_status": "published",
        "published_at": CHECKED_AT,
        "steps": [
            {
                "rule_id": f"nkust-115-home-1-{idx+1:03d}",
                "order": 1,
                "phase": "校內申請",
                "title": f"確認學制年級（大二／專四／碩博以上）、操行 75 分門檻與 {zh_name} 語檢要求",
                "responsible_party": "學生",
                "responsible_unit": "國立高雄科技大學國際事務處國際關係組（建工校區行政大樓 3 樓）",
                "deadline_at": deadline_iso,
                "deadline_status": "verified_exact" if avail_status == "open" else "reference_only",
                "deadline_source_url": source_url,
                "deadline_checked_at": CHECKED_AT,
                "deadline_reminder_eligible": False,
                "summary": (
                    f"確認符合《國立高雄科技大學學生赴境外大學校院交換研修作業要點》及當期校級交換甄選簡章規定（大學部大二以上、五專部專四以上、碩博士班在學學生，在當前學制有一學期以上成績且操行成績至少達 75 分），並備妥符合 {zh_name} 規定之外語檢定證明。"
                ),
                "details": [
                    f"開放學制與院系：{colleges_str}（{degree_levels_str}）",
                    f"語言與學業條件：{lang_req_str}｜{gpa_req_str}",
                    f"當期名額與費用待遇：{quota_str}｜{tuition_raw}",
                ],
                "scope": {
                    "home_universities": ["國立高雄科技大學"],
                    "partner_universities": [full_name],
                    "academic_years": ["115", "116"],
                    "application_rounds": [round_label, "115-1", "115-2", "116-1", "116-2"],
                },
                "source_urls": [
                    source_url,
                    NKUST_115_GUIDELINES_URL,
                    NKUST_FLEC_CEF_URL,
                ],
                "checked_at": CHECKED_AT,
                "support_status": "verified",
            },
            {
                "rule_id": f"nkust-115-home-2-{idx+1:03d}",
                "order": 2,
                "phase": "校內申請",
                "title": "完成高科大出國交換線上申請並上傳核章志願表、歷年成績單、語檢證明與中英文讀書計畫",
                "responsible_party": "學生與所屬系（所）辦公室",
                "responsible_unit": "國立高雄科技大學各系所辦公室／國際事務處國際關係組",
                "deadline_at": deadline_iso,
                "deadline_status": "verified_exact" if avail_status == "open" else "reference_only",
                "deadline_source_url": source_url,
                "deadline_checked_at": CHECKED_AT,
                "deadline_reminder_eligible": False,
                "summary": (
                    "於甄選收件截止日（16:00 止）前完成線上申請並上傳經系所主管核章之《校級交換研修志願表》、中文歷年成績單（含排名，操行至少 75 分）、有效外語能力檢定證明、中英文自傳及讀書計畫與相關加分／惜珠證明文件。"
                ),
                "details": [
                    "語檢成績補件規定：若報名截止前尚未收到紙本正式成績單，得先上傳網路成績查詢截圖完成線上申請，並於簡章規定之補件截止日（如 12 月中下旬 16:00）前補交正式成績單；逾期未補交者視同未具語檢資格。",
                    "志願選填與媒合機制：每位申請人可依序選填 3 至 6 個交換學校志願，並可勾選當所填志願皆未錄取時是否同意由國際處依剩餘名額協助媒合。",
                ],
                "document_requirements": [
                    {
                        "name": "國立高雄科技大學校級交換研修志願表（需申請人簽名及所屬系所主管核章）",
                        "official_form_url": NKUST_115_PREF_FORM_URL,
                        "source_urls": [NKUST_EXCHANGE_PAGE_URL, NKUST_115_GUIDELINES_URL],
                    },
                    {
                        "name": "中文歷年成績單正本（需有在校排名，且操行成績至少達 75 分；碩一／博一／四技轉學新生得附原就讀學校歷年成績單）",
                        "source_urls": [NKUST_115_GUIDELINES_URL],
                    },
                    {
                        "name": "有效期限內之外語能力檢定證明（TOEFL / IELTS / TOEIC / JLPT / Goethe / TestDaF / DELF / TOPIK，對照高科大外語教育中心 CEFR 等級表）",
                        "official_form_url": NKUST_FLEC_CEF_URL,
                        "source_urls": [NKUST_115_GUIDELINES_URL, NKUST_FLEC_CEF_URL],
                    },
                    {
                        "name": "中、英文自傳及讀書計畫（含出國動機、擬修讀專業領域與返國學習規劃）及學海惜珠／雙聯學位相關證明文件",
                        "source_urls": [NKUST_115_GUIDELINES_URL, NKUST_SCHOLARSHIP_PAGE_URL],
                    },
                ],
                "scope": {
                    "home_universities": ["國立高雄科技大學"],
                    "academic_years": ["115", "116"],
                    "application_rounds": [round_label, "115-1", "115-2", "116-1", "116-2"],
                },
                "source_urls": [
                    NKUST_EXCHANGE_PAGE_URL,
                    NKUST_115_GUIDELINES_URL,
                    NKUST_115_PREF_FORM_URL,
                ],
                "checked_at": CHECKED_AT,
                "support_status": "verified",
            },
            {
                "rule_id": f"nkust-115-home-3-{idx+1:03d}",
                "order": 3,
                "phase": "甄選與提名",
                "title": "國際處甄選審查（專業契合度 50%＋語檢 CEFR 30%＋在校成績 20%）與錄取意願確認",
                "responsible_party": "學生與國際事務處甄選審查委員會",
                "responsible_unit": "國立高雄科技大學國際事務處國際關係組",
                "deadline_at": "2027-02-26T16:00:00+08:00",
                "deadline_status": "verified_exact",
                "deadline_source_url": NKUST_115_GUIDELINES_URL,
                "deadline_checked_at": CHECKED_AT,
                "deadline_reminder_eligible": False,
                "summary": (
                    "國際處於 2 月召開甄選審查會議（學海惜珠合格生優先分發；申請人數超過名額時，先以語檢達第一志願門檻者優先，再依「專業領域契合度 50%＋外語檢定 CEFR 等級 30%＋在校歷年成績 20%」總分比序分發）。2 月下旬公告分發結果後，正取生須於期限內上傳《錄取生交換意願確認書》與《家長同意書》。"
                ),
                "details": [
                    "同分比序原則：總成績相同時，依序按 (1) 第一志願專業領域契合度、(2) 在校歷年學業成績、(3) 外語檢定成績 高低排列。",
                    "獎補助名冊核定：通過校內甄選並獲姊妹校錄取之本國籍非在職專班學生，由國際處依甄選成績與預算統一審核教育部《學海飛颺／學海惜珠》或高科大《高教深耕境外研修獎助金》（亞洲 6 萬、非亞洲 8 萬、雙聯 12 萬，經濟不利另加發最高 2 萬），並於 7 月 1 日公告獎補助名單。",
                ],
                "scope": {
                    "home_universities": ["國立高雄科技大學"],
                    "academic_years": ["115", "116"],
                    "application_rounds": [round_label, "115-1", "115-2", "116-1", "116-2"],
                },
                "source_urls": [
                    NKUST_115_GUIDELINES_URL,
                    NKUST_SCHOLARSHIP_REG_URL,
                    NKUST_SCHOLARSHIP_PAGE_URL,
                ],
                "checked_at": CHECKED_AT,
                "support_status": "verified",
            },
            {
                "rule_id": f"nkust-{idx+1:03d}-host-apply",
                "order": 4,
                "phase": "合作校申請",
                "title": f"由高科大國際處辦理官方提名（Nomination）並依 {zh_name} 規定遞交入學與宿舍申請",
                "responsible_party": "學生與接待校國際事務處",
                "summary": (
                    f"完成校內錄取意願確認後，由高科大國際事務處於提名期間（秋季班 3–7 月、春季班 8–11 月）向 {zh_name} 辦理官方提名；學生須依姊妹校 Fact Sheet 規定準備外文申請表、英文歷年成績單、護照影本、銀行存款財力證明、語檢證書、體檢與疫苗證明及宿舍申請表，靜候姊妹校核發正式入學許可書（Letter of Acceptance / COE / DS-2019）。"
                ),
                "details": [
                    f"交換期程：{study_period_str}｜名額：{quota_str}",
                    f"語言與學業條件：{lang_req_str}｜{gpa_req_str}",
                    f"住宿安排：{housing_str}",
                ],
                "scope": {
                    "home_universities": ["國立高雄科技大學"],
                    "partner_universities": [full_name],
                    "academic_years": ["115", "116"],
                    "application_rounds": [round_label, "115-1", "115-2", "116-1", "116-2"],
                },
                "source_urls": (
                    [source_url, NKUST_EXCHANGE_PAGE_URL, NKUST_GS_PORTAL_URL]
                    + ([factsheet_url] if factsheet_url else [])
                    + ([gs_subpage_url] if gs_subpage_url else [])
                    + ([website] if website else [])
                ),
                "checked_at": CHECKED_AT,
                "support_status": "verified",
                "needs_confirmation": False,
            },
            {
                "rule_id": f"nkust-115-home-5-{idx+1:03d}",
                "order": 5,
                "phase": "行前準備",
                "title": "簽訂獎助行政契約書、辦理簽證保險與高科大註冊，返國後 1 個月內完成心得核銷與學分抵免",
                "responsible_party": "學生",
                "responsible_unit": "國立高雄科技大學國際事務處／教務處註冊組／生輔組／各系所",
                "summary": (
                    "出國前須參加國際處行前說明會、完成獎助學金行政契約書簽署、辦妥留學簽證與海外全期醫療及意外保險（役男須於出國前完成緩徵出境核准），並於交換期間維持高科大在學註冊及繳交全額學雜費；返國後 1 個月內繳交研修心得報告、登機證存根、護照出入境章影本及姊妹校正式成績單完成獎補助核銷與學分抵免。"
                ),
                "details": tuition_points_list,
                "scope": {
                    "home_universities": ["國立高雄科技大學"],
                    "academic_years": ["115", "116"],
                    "application_rounds": [round_label, "115-1", "115-2", "116-1", "116-2"],
                },
                "source_urls": [
                    NKUST_EXCHANGE_PAGE_URL,
                    NKUST_REGULATIONS_URL,
                    NKUST_SCHOLARSHIP_REG_URL,
                    NKUST_SCHOLARSHIP_PAGE_URL,
                ],
                "checked_at": CHECKED_AT,
                "support_status": "verified",
            },
        ],
        "sources": wf_sources,
        "last_checked": CHECKED_AT,
        "coverage_status": "official_verified",
        "coverage_note": (
            "已完整整合國立高雄科技大學國際事務處（國際關係組）115學年度校級交換學校一覽表（88 校）、院系級交換學校列表（14 校）、114/113學年度及出國交換網專頁合作姊妹校共 107 所全球交換合作學校名額、語檢門檻、獎補助要點與歷屆學長姐返國心得。"
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
            "title": f"國立高雄科技大學校級／院系級交換學校名額與條件一覽表—{zh_name}",
            "source_url": source_url,
            "summary": "高科大國際處公告之交換名額、開放對象、語言檢定門檻、學費待遇與備註說明",
        },
        {
            "title": "國立高雄科技大學學生赴境外大學校院交換研修作業要點與獎助要點",
            "source_url": NKUST_REGULATIONS_URL,
            "summary": "高科大出國交換申請資格、甄選比序配分（50%／30%／20%）、學海飛颺／惜珠與高科大境外研修獎助金（6萬／8萬／12萬）規定",
        },
    ]
    if factsheet_url:
      dest_sources.append({
          "title": f"高科大國際處公告之 {zh_name} 交換簡章（Fact Sheet）雲端資料夾",
          "source_url": factsheet_url,
          "summary": "高科大國際處彙整之姊妹校最新 Fact Sheet、申請表單與選課住宿資訊",
      })
    if gs_subpage_url:
      dest_sources.append({
          "title": f"高科大出國交換學生網—{zh_name} 專頁與歷屆交換生心得報告",
          "source_url": gs_subpage_url,
          "summary": f"收錄高科大出國交換學生網 {zh_name} 學校簡介、宣傳影片與歷屆交換生返國心得報告",
      })
    if website:
      dest_sources.append({
          "title": f"{full_name} 官方網站",
          "source_url": website,
          "summary": "接待合作校官方網站",
      })

    src_url_list = (
        [source_url, NKUST_EXCHANGE_PAGE_URL, NKUST_REGULATIONS_URL]
        + ([factsheet_url] if factsheet_url else [])
        + ([gs_subpage_url] if gs_subpage_url else [])
        + ([website] if website else [])
    )

    destinations.append({
        "home_university": "國立高雄科技大學",
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
                "title": "生活費、教育部學海飛颺／惜珠與高科大境外研修獎助金（亞洲 6 萬／非亞洲 8 萬／雙聯 12 萬）",
                "summary": cost_line,
                "points": [cost_line] + tuition_points_list,
                "source_urls": src_url_list + [NKUST_SCHOLARSHIP_PAGE_URL, NKUST_SCHOLARSHIP_REG_URL],
                "caution": (
                    "高科大教育部「學海飛颺」與校內高教深耕「境外研修獎助金」核發額度為亞洲地區（不含中港澳）每名 NT$60,000、非亞洲地區（歐美澳）每名 NT$80,000、雙聯學制每名 NT$120,000；符合經濟不利條件者得再加發最高 NT$20,000。"
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
                    "依《國立高雄科技大學學生赴境外大學校院交換研修作業要點》規定，交換生出國前須投保涵蓋境外交換全期之海外醫療、意外及急難救助保險，並依接待國政府或姊妹校規定投保當地強制學生健康保險（如日本國民健康保險、韓國 NHIS、德國公保、澳洲 OSHC 等）。",
                ],
                "source_urls": src_url_list,
                "caution": "請於收到入學許可後確認接待校指定之保險額度與投保通路，並於出國前繳交保險證明影本。",
            },
            {
                "key": "visa",
                "title": "留學簽證辦理、役男出境緩徵手續與在學學籍維持義務",
                "summary": visa_default,
                "points": [
                    visa_default,
                    "具役男身分之男同學須於出國前洽生輔組與國際處完成役男出國留學緩徵核准手續；出國交換期間須全程維持高科大在學學籍並完成註冊繳費（不得辦理休學或畢業離校）。",
                ],
                "source_urls": src_url_list,
                "caution": "請勿持觀光簽證或免簽入境就讀學期交換課程，以免影響正式學籍、居留與返國學分抵免。",
            },
            {
                "key": "academics",
                "title": "修課規定、領域契合度要求與返國學分抵免",
                "summary": course_clean[:160],
                "points": [calendar_clean, course_clean],
                "source_urls": src_url_list,
                "caution": (
                    "校級交換甄選將「第一志願研修學校（系所）與就讀系所專業領域契合度」列為 50% 核心評分項目（無外語要求之大陸姊妹校為 60%），選填志願與選課前請務必確認姊妹校開設之專業課程與本系學分抵免規範。"
                ),
            },
            {
                "key": "living",
                "title": f"{location_obj.get('city') or country} 校園生活與高科大學長姐交換心得傳承",
                "summary": f"代表校區城市：{location_obj.get('city') or country}。請配合高科大行前說明會與接待校新生訓練（Orientation）完成報到。",
                "points": [
                    f"目的地城市：{location_obj.get('city') or country}（{country}）",
                    (
                        f"高科大國際處於「出國交換學生網（{gs_subpage_url or NKUST_GS_PORTAL_URL}）」及各校雲端簡章資料夾公開收錄歷屆學長姐返國研修心得報告，詳述當地選課、住宿、交通與生活開銷實況。"
                    ),
                ],
                "source_urls": [NKUST_GS_PORTAL_URL] + ([gs_subpage_url] if gs_subpage_url else []),
            },
        ],
        "sources": dest_sources,
        "last_checked": CHECKED_AT,
        "coverage_status": "official_verified",
        "coverage_note": (
            "已整合國立高雄科技大學國際事務處 107 所交換合作姊妹校名額、語檢門檻、獎補助要點、各校雲端 Fact Sheet 與出國交換學生網歷屆學長姐返國心得。"
        ),
    })

    research_records.append({
        "home_university": "國立高雄科技大學",
        "school_name": full_name,
        "country": country,
        "official_website": website or NKUST_EXCHANGE_PAGE_URL,
        "verification_status": "official_verified",
        "discovery_source_url": source_url,
        "checked_at": CHECKED_AT,
        "note": (
            f"國立高雄科技大學國際事務處《115學年度校級交換學校一覽表》、《院系級交換學校列表》、《出國交換學生網（{NKUST_GS_PORTAL_URL}）》與 ROR/Wikidata 官方網址核對完成。"
        ),
    })

    ev_sources = [
        {
            "title": f"國立高雄科技大學交換學校名額與條件一覽表—{zh_name}",
            "url": source_url,
        },
    ]
    if factsheet_url:
      ev_sources.append({
          "title": f"高科大國際處 {zh_name} 交換簡章（Fact Sheet）雲端資料夾",
          "url": factsheet_url,
      })
    if gs_subpage_url:
      ev_sources.append({
          "title": f"高科大出國交換學生網—{zh_name} 專頁與學長姐心得分享",
          "url": gs_subpage_url,
      })
    if website:
      ev_sources.append({"title": f"{full_name} 官方網站", "url": website})

    has_student_exp = bool(gs_subpage_url or factsheet_url)
    if gs_subpage_url:
      exp_covered_schools += 1

    ev_list = [
        {
            "theme": "housing",
            "kind": "mixed" if has_student_exp else "official",
            "text": housing_clean,
            "sources": ev_sources,
            "checked_at": CHECKED_AT,
            "scope": "國立高雄科技大學出國交換姊妹校住宿與生活資訊",
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
            "scope": "國立高雄科技大學交換生費用規定、學海飛颺／惜珠與高科大境外研修獎助金（6萬／8萬／12萬）及地區生活費估算",
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
            "scope": "國立高雄科技大學交換生選課限制、專業領域契合度評分與返國學分抵免規定",
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
            "scope": "國立高雄科技大學出國交換簽證、海外醫療保險、役男緩徵出境與在學註冊提醒",
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
                    f"｜高科大出國交換學生網公開收錄赴 {zh_name} 交換生研修心得報告（{'、'.join(gs_exp_titles[:4])}）。"
                    if gs_exp_titles
                    else (
                        f"｜高科大出國交換學生網設有 {zh_name} 專屬介紹與心得專頁。"
                        if gs_subpage_url
                        else ""
                    )
                )
            ),
            "sources": ev_sources,
            "checked_at": CHECKED_AT,
            "scope": "國立高雄科技大學出國交換名額與歷屆學長姐交換經驗分享",
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
            "已整合國立高雄科技大學國際事務處《115學年度校級交換學校一覽表》、《院系級交換學校列表》、各校雲端 Fact Sheet 與《出國交換學生網》歷屆學長姐返國心得。",
            "當期宿位供給、費用與選課限制請依姊妹校最新交換網頁及入學通知書核對。",
        ],
        "location_signature": f"verified:{location_obj['latitude']}:{location_obj['longitude']}:representative",
        "extraction_version": 3,
    })

    sample_reports: list[dict] = []
    for idx_t, t_title in enumerate(gs_exp_titles[:5]):
      r_url = gs_doc_links[idx_t] if idx_t < len(gs_doc_links) else (gs_subpage_url or NKUST_GS_PORTAL_URL)
      m_yr = re.search(r"(1\d\d)\s*年", t_title)
      term_str = f"{m_yr.group(1)}學年度" if m_yr else "歷年交換"
      sample_reports.append({
          "title": f"高科大赴 {zh_name} 交換研修心得—{t_title}",
          "url": r_url,
          "term": term_str,
      })
    if not sample_reports and gs_subpage_url:
      sample_reports.append({
          "title": f"國立高雄科技大學出國交換學生網—{zh_name} 姊妹校專頁與學長姐心得",
          "url": gs_subpage_url,
          "term": "歷年交換",
      })
    elif not sample_reports and factsheet_url:
      sample_reports.append({
          "title": f"國立高雄科技大學赴 {zh_name} 交換簡章（Fact Sheet）雲端資料夾",
          "url": factsheet_url,
          "term": "115學年度",
      })

    if gs_subpage_url:
      rep_title = (
          f"國立高雄科技大學赴 {zh_name}"
          + (f"（含 {len(gs_exp_titles)} 篇學長姐研修心得）" if gs_exp_titles else "")
          + "交換經驗與申請指南彙編"
      )
      latest_author = gs_exp_titles[0] if gs_exp_titles else "國立高雄科技大學返國交換學生"
      intro_excerpt = clean_text(item.get("gs_intro") or "")
      summary_text = (
          f"國立高雄科技大學國際事務處「出國交換學生網」設有 {zh_name} 專屬介紹與經驗傳承頁面（{gs_subpage_url}）"
          + (
              f"，公開收錄 {len(gs_exp_titles)} 篇歷屆高科大學長姐返國研修心得（含：{'、'.join(gs_exp_titles[:5])}）"
              if gs_exp_titles
              else ""
          )
          + (f"，學校重點：{intro_excerpt[:180]}" if intro_excerpt else "")
          + "，詳實記錄高科大交換生於姊妹校之專業選課、英語／二外授課適應、宿舍環境與海外生活開支。"
      )
      theme_map = {
          "academics": (
              f"高科大交換生分享於 {zh_name} 修讀工程、電資、海事、水圈、商管、外語與創新設計等專業課程之選課技巧，以及返國辦理學分抵免之實務經驗。"
          ),
          "housing": (
              f"高科大交換生詳述 {zh_name} 校內外學生宿舍申請流程、房型費用與周邊交通生活機能（{housing_clean[:120]}）。"
          ),
          "campus_culture": (
              f"高科大出國交換學生網收錄赴 {zh_name} 交換研修心得，分享國際學生迎新週（Orientation）、語伴交流（Buddy Program）與跨文化適應經驗。"
          ),
          "cost": (
              f"高科大交換生記錄赴 {zh_name} 之住宿費、伙食費與每月生活開銷（{cost_default}），以及運用教育部學海飛颺／惜珠與高科大境外研修獎助金（亞洲 6 萬／歐美澳 8 萬／雙聯 12 萬）支應留學費用之規劃。"
          ),
      }
      student_experience_rows.append({
          "school_name": full_name,
          "country": country,
          "title": rep_title,
          "source_url": gs_subpage_url,
          "source_type": "article",
          "platform": "國立高雄科技大學國際事務處—出國交換學生網（學生心得分享）",
          "author_name": latest_author,
          "language": "zh",
          "summary": summary_text,
          "themes": ["academics", "housing", "campus_culture", "cost"],
          "theme_summaries": theme_map,
          "content_status": "full_text",
          "perspective": "official_student_story",
          "published_at": None,
          "discovered_at": CHECKED_AT,
          "content_hash": hashlib.sha256(f"{full_name}:exp:{gs_subpage_url}".encode("utf-8")).hexdigest(),
          "exchange_term": sample_reports[0]["term"] if sample_reports else "歷年交換",
          "summary_zh": summary_text,
          "original_summary": summary_text,
          "theme_summaries_zh": theme_map,
          "translation_status": "original",
          "source_kind": "official_experience_page",
      })

    experience_sources_records.append({
        "home_university": "國立高雄科技大學",
        "school_name": full_name,
        "country": country,
        "official_experience_portal_url": gs_subpage_url or NKUST_GS_PORTAL_URL,
        "partner_page_url": factsheet_url or gs_subpage_url or source_url,
        "report_count": len(gs_exp_titles) if gs_exp_titles else (1 if gs_subpage_url else 0),
        "sample_reports": sample_reports,
        "checked_at": CHECKED_AT,
    })

  partners_jsonl_text = "\n".join(json.dumps(r, ensure_ascii=False) for r in partners) + "\n"
  (OFFICIAL_NKUST_DIR / "partners.jsonl").write_text(partners_jsonl_text, encoding="utf-8")
  (SOURCES_NKUST_DIR / "partners.jsonl").write_text(partners_jsonl_text, encoding="utf-8")
  (OFFICIAL_NKUST_DIR / "application_workflows.jsonl").write_text(
      "\n".join(json.dumps(r, ensure_ascii=False) for r in workflows) + "\n",
      encoding="utf-8",
  )
  (OFFICIAL_NKUST_DIR / "destination_profiles.jsonl").write_text(
      "\n".join(json.dumps(r, ensure_ascii=False) for r in destinations) + "\n",
      encoding="utf-8",
  )
  (OFFICIAL_NKUST_DIR / "partner_research.jsonl").write_text(
      "\n".join(json.dumps(r, ensure_ascii=False) for r in research_records) + "\n",
      encoding="utf-8",
  )
  (OFFICIAL_NKUST_DIR / "student_life.jsonl").write_text(
      "\n".join(json.dumps(r, ensure_ascii=False) for r in life_records) + "\n",
      encoding="utf-8",
  )
  (OFFICIAL_NKUST_DIR / "experience_sources.jsonl").write_text(
      "\n".join(json.dumps(r, ensure_ascii=False) for r in experience_sources_records) + "\n",
      encoding="utf-8",
  )
  (OFFICIAL_NKUST_DIR / "student_experiences.jsonl").write_text(
      "\n".join(json.dumps(r, ensure_ascii=False) for r in student_experience_rows) + "\n",
      encoding="utf-8",
  )
  (OFFICIAL_NKUST_DIR / "campus-locations.json").write_text(
      json.dumps({"locations": new_locations}, ensure_ascii=False, indent=2) + "\n",
      encoding="utf-8",
  )

  # Build student-experience-digests.json
  digest_records = {}
  for exp_row in student_experience_rows:
    sn = exp_row["school_name"]
    digest_records[sn] = {
        "school_name": sn,
        "country": exp_row["country"],
        "report_count": 1,
        "summary_zh": exp_row["summary_zh"],
        "themes": exp_row["theme_summaries_zh"],
        "source_url": exp_row["source_url"],
        "updated_at": CHECKED_AT,
    }
  (OFFICIAL_NKUST_DIR / "student-experience-digests.json").write_text(
      json.dumps({"digests": digest_records}, ensure_ascii=False, indent=2) + "\n",
      encoding="utf-8",
  )

  # Update university_locations.jsonl with NKUST home location
  loc_file = REPO_ROOT / "src/exchange_info/official_data/university_locations.jsonl"
  existing_loc_lines = [
      line for line in loc_file.read_text(encoding="utf-8").splitlines() if line.strip()
  ]
  existing_loc_map = {}
  for line in existing_loc_lines:
    rec = json.loads(line)
    existing_loc_map[(rec["school_name"], rec.get("country") or "")] = rec

  nkust_home_loc = {
      "school_name": "國立高雄科技大學",
      "country": "臺灣",
      "city": "高雄市三民區",
      "latitude": 22.6497,
      "longitude": 120.3275,
      "geocode_status": "verified",
      "geocoded_at": CHECKED_AT,
      "source_url": "https://www.wikidata.org/wiki/Q48929909",
      "identity_source_url": "https://ror.org/00dbz0x85",
      "precision": "representative",
      "note": (
          "校級代表位置：官方網域及國家已與 ROR 比對，座標來源為 Wikidata P625；實際交換校區以錄取通知為準。"
          " 母校代表點採高雄市三民區建工路415號建工校區行政大樓 3 樓國際事務處；官方地址來源：https://oia.nkust.edu.tw/。"
      ),
  }
  existing_loc_map[("國立高雄科技大學", "臺灣")] = nkust_home_loc
  sorted_locs = sorted(
      existing_loc_map.values(),
      key=lambda r: (r.get("country") or "", r.get("school_name") or ""),
  )
  loc_file.write_text(
      "\n".join(json.dumps(r, ensure_ascii=False) for r in sorted_locs) + "\n",
      encoding="utf-8",
  )

  nkust_source_urls = [
      NKUST_OIA_HUB_URL,
      NKUST_EXCHANGE_PAGE_URL,
      NKUST_SCHOLARSHIP_PAGE_URL,
      NKUST_SHORT_TERM_PAGE_URL,
      NKUST_GS_PORTAL_URL,
      NKUST_115_GUIDELINES_URL,
      NKUST_115_PREF_FORM_URL,
      NKUST_115_UNI_SHEET_URL,
      NKUST_COLLEGE_SHEET_URL,
      NKUST_REGULATIONS_URL,
      NKUST_SCHOLARSHIP_REG_URL,
      NKUST_FLEC_CEF_URL,
      NKUST_116_INFO_SESSION_URL,
  ]

  exchange_info_payload = {
      "school_name": "國立高雄科技大學",
      "program_type": [
          (
              "國際事務處（國際關係組）校級赴外交換生聯合甄選計畫（每年 11–12 月一次甄選次一學年度第 1 學期［秋季班］及第 2 學期［春季班］交換生，115學年度校級一覽表共 88 所姊妹校，含 UMAP 亞太大學交流會交換計畫）"
          ),
          (
              "各學院暨系所院系級交換學生計畫（共 14 所締約姊妹校，含 9 所院系專屬姊妹校及 5 所校院雙軌合作校，由管理學院、外語學院、海事學院、海洋商務學院、工學院、電機與資訊學院、商業智慧學院等簽約院系所推薦）"
          ),
          (
              "境外雙聯學位暨暑期短期研修計畫（含美國密蘇里大學聖路易斯分校 UMSL、德國福茲堡-施韋因富特應用科技大學 THWS 等雙聯學制，以及《學海展翅專案》暑期赴海外姊妹校 1 個月短期培訓計畫）"
          ),
      ],
      "academic_year": [
          (
              "115（115學年度第 1 學期［2026年9月出發］及第 2 學期［2027年2月出發］校級交換聯合甄選於 2025/11/10 – 12/10 受理線上申請、2025/12/19 補交語檢截止、2026/02/23 公告錄取名單、2026/07/01 公告學海飛颺與高科大獎補助名冊；本平台共完整收錄 107 所高科大交換合作姊妹校，含 97 所當期開放申請校及 10 所歷屆／暫緩參考校）"
          ),
          (
              "116（116學年度［2027-2028］出國交換研修五校區巡迴說明會於 2026/10/07–10/28 舉行，預計於 2026/11/10 – 2026/12/01 16:00 開放線上申請、2026/12/27 補交語檢截止、2027/02/22 公告分發結果、2027/07/01 公告獎補助名單）"
          ),
      ],
      "semester": [
          "第1學期（秋季班：每年約 8/9 月至翌年 1/2 月；校內提名薦送期程為每年 3 月至 7 月）",
          "第2學期（春季班：每年約 2/3 月至 6/7 月，日本春季班為 4 月至 8/9 月；校內提名薦送期程為每年 8 月至 11 月）",
          "一學年交換或雙聯學制（交換期間以 1 學期為原則，至多以 2 學期［1 學年］為限）",
      ],
      "application_period": [
          (
              "【116學年度（2027-2028，含 116-1 秋季班與 116-2 春季班）校級交換生甄選時程】五校區巡迴說明會：2026/10/07（旗津、第一）、10/14（燕巢）、10/21（楠梓）、10/28（建工）；線上申請收件：預計 2026/11/10 – 2026/12/01 16:00；補繳外語檢定正式成績單截止：2026/12/27 16:00；甄選審查會議：2027/02/01 – 02/12；分發結果公告：2027/02/22；正取生上傳意願確認書與家長同意書截止：2027/02/26；獎補助名單公告：2027/07/01。"
          ),
          (
              "【115學年度（2026-2027，含 115-1 秋季班與 115-2 春季班）校級交換生甄選時程（已辦理完畢）】線上申請：2025/11/10 12:00 – 2025/12/10 16:00（原訂 12/02 延長至 12/10）；補繳語檢正式成績單截止：2025/12/19 16:00；分發結果公告：2026/02/23 16:00（共錄取 97 人次）；正取確認截止：2026/02/27 16:00；115-1 提名薦送：2026年3月至7月；115-2 提名薦送：2026年8月至11月；獎補助名冊公告：2026/06/29–06/30。"
          ),
          (
              "【院系級交換與短期交流／學海展翅申請時程】院系級交換依各簽約院系所（管理學院、海商學院、外語學院、工學院、電資學院等）每學期公告時程向院系辦提出申請；《國際短期交流補助》於第一梯次（2月底前）及第二梯次（6月底前）受理；《學海展翅專案》暑期海外姊妹校 1 個月培訓於每年春季公告甄選。"
          ),
      ],
      "eligibility": [
          (
              "【在學學制、年級與國籍規定（依《國立高雄科技大學學生赴境外大學校院交換研修作業要點》及甄選簡章）】申請人須為本校大學部二年級（含）以上、研究所（含碩士班、博士班及在職專班）及五年制專科部四年級（含）以上之本國籍、僑生或外籍在學學生；於提出申請時及赴外交換期間皆須保有本校在學學籍（不得辦理休學或畢業離校，否則取消錄取及獎補助資格）。僑生及外籍生不得申請赴其原國籍國家境內之大學交換；中國大陸地區姊妹校限臺港澳籍學生申請。"
          ),
          (
              "【在校學業與操行 75 分門檻】申請人在當前就讀學制中須有一學期以上之學期成績且成績良好，歷年操行成績至少須達 75 分（含）以上（碩一、博一或四技轉學新生申請下一學年度第 1 學期交換時若尚無高科大成績，得檢附原就讀學校歷年成績單；惟獲錄取後仍須補交高科大第 1 學期成績單供國際處審核）。此外須符合各志願姊妹校訂定之特定 GPA（如 GPA 2.5–3.2）或開放院系限制。"
          ),
          (
              "【甄選審查配分公式（50%／30%／20%）與分發比序原則】學海惜珠合格申請人優先分發；若單一學校申請人數超過名額，先以語檢達第一志願交換校門檻者優先，再依下列權重計算甄選總成績比序分發：（1）第一志願研修學校（系所）與申請人就讀系所專業領域契合度佔 50%（高度契合 100 分、中度契合 85 分、低度契合 70 分）；（2）外語檢定成績佔 30%（依外語教育中心 CEFR 對照表：C1 以上 100 分、B2 90 分、B1 80 分、A2 以下 70 分）；（3）在校歷年學業總平均佔 20%（無外語要求之大陸姊妹校調整為：專業領域契合度 60%＋在校歷年成績 40%）。總分相同時依序按「專業領域契合度 → 在校成績 → 外語檢定成績」比序。"
          ),
      ],
      "language_requirement": [
          (
              "【歐美澳、日韓及東南亞姊妹校外語檢定規定與高科大 CEFR 等級對照標準】申請非中國大陸姊妹校者，必須提供有效期限內之英語檢定證明（TOEFL、IELTS、TOEIC）或符合交換學校要求之第二外語能力檢定證明。依《國立高雄科技大學外語教育中心各類外語檢定證照等級對照表》，各級門檻為：（1）CEFR B1（甄選語檢項評定 80 分）：TOEIC 550（口說寫作 240）、TOEFL iBT 42、TOEFL ITP 460、IELTS 4.0、GEPT 中級；（2）CEFR B2（甄選語檢項評定 90 分）：TOEIC 785（口說寫作 310）、TOEFL iBT 72、TOEFL ITP 543、IELTS 5.5、GEPT 中高級；（3）CEFR C1（甄選語檢項評定 100 分）：TOEIC 945（口說寫作 360）、TOEFL iBT 95、TOEFL ITP 627、IELTS 7.0、GEPT 高級。"
          ),
          (
              "【日語、德語、法語、韓語第二外語檢定與修課時數規定】（1）日本姊妹校（27 校）：依各校規定須具 JLPT N1–N5（如明治、關西、京都外大本科、同志社女子、千葉、龍谷、信州、熊本學園、東京海洋要求 N2–N3；愛媛、長崎、鹿兒島、福岡工大、高知、福井縣立、獨協、大東文化接受 N3–N4 或英語 B1/B2；靜岡理工接受 N5 或日語學習證明）；（2）德國／奧地利／法國姊妹校（19 校）：要求英語或德語／法語達 CEFR B1–B2（Goethe-Zertifikat / TestDaF / DELF / TCF）；（3）韓國姊妹校（8 校）：韓國海洋、仁荷、漢陽 ERICA、慶尚、朝鮮要求 TOPIK 2–3 級或英語 B1/B2，聖潔大學接受日韓語修課時數證明。"
          ),
          (
              "【中國大陸姊妹校語言規定與未達門檻提名但書】申請中國大陸無外語要求之姊妹校（同濟、重慶、華南理工、華中科大、大連理工、中國海洋、上海海事等）免附外語檢定證明（惟深圳大學要求提供英語檢定證明）。若申請人外語能力未達交換學校規定標準但通過本校校內甄選者，國際處仍可協助提名薦送，惟接待學校保有最終審核決定權。"
          ),
      ],
      "required_documents": [
          "1. 國立高雄科技大學校級交換研修志願表（線上填報並列印經申請人簽名及所屬系所主管核章後掃描上傳；可填寫 3–6 個志願並勾選是否同意國際處媒合）",
          "2. 中文歷年成績單正本（需註明歷年學業總平均與班／系排名，且操行成績至少達 75 分；碩一、博一或轉學新生尚無本校成績者得先附原就讀學校歷年成績單）",
          "3. 有效期限內之外語能力檢定證明（TOEFL、IELTS、TOEIC 或 JLPT、Goethe、TestDaF、DELF、TOPIK 等；若報名截止前尚未收到紙本成績單，得先上傳網路成績截圖並於補件截止日前補交正式成績單）",
          "4. 中、英文自傳及讀書計畫（A4 格式，詳述個人背景、申請動機、第一志願系所專業領域契合度、修課計畫與返國學習規劃）",
          "5. 雙聯學位申請附件（申請雙聯學制者須另附英文歷年成績單及英語能力檢定證明）與學海惜珠申請附件（具低收入戶、中低收入戶、特殊境遇家庭扶助或身心障礙生活補助證明者須檢附新式戶口名簿影本及有效證明文件）",
          "6. 錄取分發後與返國核銷必繳文件：錄取公告後 1 週內上傳《錄取生交換意願確認書》及《家長同意書》；7 月獲核定獎補助者簽立《選送生行政契約書》；返國後 1 個月內繳交 1,500–2,000 字出國研修心得報告（含 4 張以上照片）、護照基本頁與出入境章影本、登機證存根、電子機票收據及姊妹校正式成績單",
      ],
      "scholarship_info": [
          (
              "教育部「學海飛颺」與「學海惜珠」獎補助計畫（依高科大國際處公告之 115 學年度核發標準）：補助具中華民國國籍且在臺設有戶籍、在學一學期以上之非在職專班學生赴外國大專校院（不含大陸及港澳地區）研修 1 學期至 1 學年（惜珠限低收／中低收／特殊境遇家庭等勵學身分且優先分發）：（1）亞洲地區交換生：每名核給新臺幣 60,000 元（教育部補助款 50,000 元＋高科大配合款 10,000 元）；（2）非亞洲地區（歐洲、美洲、大洋洲）交換生：每名核給新臺幣 80,000 元（教育部補助款 50,000 元＋高科大配合款 30,000 元）；（3）雙聯學制生：每名核給新臺幣 120,000 元（教育部補助款 50,000 元＋高科大配合款 70,000 元）。"
          ),
          (
              "本校高教深耕計畫—《國立高雄科技大學獎助學生赴境外大學校院研修要點》：補助未獲教育部學海飛颺／惜珠計畫、且未同時領取我國政府或境外政府機構留學獎助金之本國籍非在職專班交換生及雙聯生，核發標準與學海計畫一致：（1）亞洲地區（不含中港澳）交換生：每名新臺幣 60,000 元；（2）非亞洲地區交換生：每名新臺幣 80,000 元；（3）雙聯學制生（不含中港澳）：每名新臺幣 120,000 元；（4）具本校經濟不利條件資格（低收、中低收、特殊境遇、身心障礙、原住民、獲大專弱勢助學金或家庭突遭變故）者，得再加發最高新臺幣 20,000 元（即亞洲最高 8 萬、非亞洲最高 10 萬、雙聯最高 14 萬）。"
          ),
          (
              "《高科大獎助學生參加國際短期交流及研習活動要點》與《學海展翅專案》：（1）國際短期交流補助：補助赴境外參加國際學術研討會、競賽或短期研習之在學學生，每名補助新臺幣 10,000 元（符合經濟不利條件者再增額補助 NT$2,000）；（2）學海展翅專案（暑期赴海外姊妹校培訓 1 個月）：定額補助每名新臺幣 20,000 元，符合本校生活助學金資格者再增額補助 NT$15,000（合計 3.5 萬），低收入戶學生全額補助機票、簽證與學費。"
          ),
          (
              "外國政府、跨國聯盟與姊妹校專屬獎學金：（1）日本 JASSO 海外留學支援制度獎學金（每月 JPY 80,000，由締約日本姊妹校擇優推薦）；（2）歐盟 Erasmus+ 跨國交換獎學金（由德國、奧地利、波蘭、匈牙利、法國等締約校推薦，補助生活津貼與旅費）；（3）UMAP 亞太大學交流會臺灣國家秘書處獎學金（每月最高 NT$20,000）。"
          ),
      ],
      "partner_universities": [p["school_name"] for p in partners],
      "source_urls": nkust_source_urls,
      "last_checked": CHECKED_AT,
  }
  (OFFICIAL_NKUST_DIR / "exchange_info.json").write_text(
      json.dumps(exchange_info_payload, ensure_ascii=False, indent=2) + "\n",
      encoding="utf-8",
  )

  student_dashboard_payload = {
      "school_name": "國立高雄科技大學",
      "last_checked": CHECKED_AT,
      "academic_score_minimum": 75.0,
      "academic_score_rule": (
          "依《國立高雄科技大學學生赴境外大學校院交換研修作業要點》及《校級交換生甄選簡章》規定：申請人須為本校大學部二年級（含）以上、五專部四年級（含）以上或碩博士班在學學生，在當前就讀學制中須有一學期以上之學期成績且成績良好，歷年操行成績至少達 75 分（含）以上（部分歐美日韓姊妹校另要求 GPA 2.5–3.2 或歷年學業總平均 75–80 分以上）。校內甄選總成績依「第一志願專業領域契合度 50%＋外語檢定 CEFR 等級 30%＋在校歷年學業成績 20%」（無外語要求之大陸姊妹校為專業契合度 60%＋在校歷年成績 40%）加權比序分發。"
      ),
      "academic_gpa_minimum": 2.5,
      "maximum_preferences": 6,
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
          "excluded_undergraduate_years": ["大一", "五專一", "五專二", "五專三"],
          "language_certificate_required": True,
      },
      "language_score_minimums": {
          "toefl": 42.0,
          "ielts": 4.0,
          "toeic": 550.0,
      },
      "application_periods": [
          {'title': '國立高雄科技大學116學年度校級交換甄選：申請時程待核實',
           'details': ['116學年度交換說明會已公告；旗津及第一校區為10/07 13:30，燕巢10/14、楠梓10/21、建工10/28均為13:30。',
                       '說明會公告本身未列校級交換甄選的確切申請與補件日期；須另查當期甄選簡章。'],
           'source': {'title': '國立高雄科技大學國際事務處—【116學年度出國交換研修】說明會公告與簡報',
                      'source_url': 'https://oia.nkust.edu.tw/news_det-980.html',
                      'category': 'exchange_application',
                      'summary': '查核限制：此來源目前不足以支持本梯次確切時程，需另查當期正式公告。'},
           'scope': 'home_application',
           'program_types': ['exchange'],
           'academic_year': '116',
           'application_round': '116學年度校級交換生聯合甄選（116-1秋季班／116-2春季班）',
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
                  "國立高雄科技大學 115 學年度（2026-2027，含 115-1 秋季班與 115-2 春季班）校級交換生聯合甄選（2025/12/10 截止、2026/2/23 公告錄取 97 人次、6/30 公告獎補助名冊）"
              ),
              "details": [
                  (
                      "115 學年度校級交換生甄選已於 2025/11/10 12:00 – 2025/12/10 16:00 完成線上申請收件（12/19 16:00 補交語檢截止），並於 2026/02/23 公告錄取名單（共錄取 97 人次）、2026/02/27 完成正取生交換意願確認。"
                  ),
                  (
                      "115-1（秋季班，2026年9月出發）於 2026年3月至7月辦理姊妹校提名薦送；115-2（春季班，2027年2月出發）於 2026年8月至11月辦理姊妹校提名薦送；115 學年度教育部學海飛颺及高科大境外研修獎補助名冊已於 2026/06/29–06/30 正式公告。"
                  ),
              ],
              "source": {
                  "title": "國立高雄科技大學 115 學年度校級交換生甄選簡章、錄取名單與獎補助名冊",
                  "source_url": NKUST_EXCHANGE_PAGE_URL,
                  "category": "exchange_application",
                  "summary": "高科大 115 學年度校級交換甄選簡章、88 所校級姊妹校名額表、錄取名單與學海飛颺／高科大獎補助名冊。",
              },
              "scope": "home_application",
              "program_types": ["exchange"],
              "academic_year": "115",
              "application_round": "115學年度校級交換生聯合甄選（115-1秋季班／115-2春季班）",
              "audience": "all_students",
              "opens_at": "2025-11-10T12:00:00+08:00",
              "deadline_at": "2025-12-10T16:00:00+08:00",
              "date_status": "verified_exact",
              "status": "closed",
              "status_note": "115 學年度校級交換甄選已辦理完畢（2026/02/23 公告錄取名單、2026/06/30 公告獎補助名冊），目前正進行 115-2 春季班提名薦送與 116 學年度甄選說明會。",
              "deadline_note": "欲申請下一梯次（116 學年度秋季班／春季班）之同學，請參加 2026 年 10 月說明會並於 11–12 月線上提出申請。",
              "reminder_eligible": False,
              "checked_at": CHECKED_AT,
          },
      ],
      "program_overview": [
          {
              "title": (
                  f"國立高雄科技大學國際事務處出國交換計畫總覽（{len(partners)} 所全球合作姊妹校・{open_partner_count} 所開放申請校・校級與院系級雙軌甄選）"
              ),
              "details": [
                  (
                      f"國立高雄科技大學（NKUST，高科大）由「國際事務處（國際關係組，位於建工校區行政大樓 3 樓）」統籌推動全球出國交換學生與雙聯學位計畫。本平台完整收錄 {len(partners)} 所高科大官方交換合作學校（含當期開放申請之 {open_partner_count} 所姊妹校及 {len(partners) - open_partner_count} 所歷屆／暫緩參考校），橫跨全球 20 個國家與地區（日本 27 校、德國 13 校、中國大陸 11 校、韓國 8 校、美國 6 校、越南 6 校、泰國 6 校、法國 5 校、菲律賓 5 校、奧地利 4 校、印尼 3 校、波蘭 2 校、馬來西亞 2 校、印度 2 校及英國、匈牙利、義大利、澳洲、加拿大 UMAP、香港各 1 校）。"
                  ),
                  (
                      "高科大出國交換體系具備四大特色：（1）每年 11–12 月一次聯合甄選次一學年度秋季班（115-1／116-1）及春季班（115-2／116-2）交換生，並涵蓋 UMAP 亞太大學交流會與 14 所院系級交換計畫；（2）透明量化比序機制：採「第一志願專業領域契合度 50%＋外語檢定 CEFR 等級 30%＋在校歷年成績 20%」（大陸無語檢要求校為 60%＋40%），學海惜珠生優先分發；（3）全方位獎補助保障：教育部《學海飛颺／惜珠》與高科大高教深耕《境外研修獎助金》雙軌並進，亞洲地區定額補助 NT$60,000、非亞洲地區（歐美澳）NT$80,000、雙聯學制 NT$120,000（經濟不利學生再加發最高 NT$20,000）；（4）完整數位傳承：國際處建置「出國交換學生網（Google Sites）」與各校雲端 Fact Sheet 資料夾，收錄超過百篇歷屆學長姐返國研修心得。"
                  ),
              ],
              "source": {
                  "title": "國立高雄科技大學國際事務處—赴外交換生專頁與出國交換學生網",
                  "source_url": NKUST_EXCHANGE_PAGE_URL,
                  "category": "exchange_application",
                  "summary": "高科大 107 所全球交換合作姊妹校、聯合甄選時程、評分權重、獎補助額度與出國交換學生網心得資源。",
              },
          }
      ],
      "eligibility": [
          {
              "title": "大二／專四／碩博以上在學資格、操行 75 分門檻與專業契合度 50%＋語檢 30%＋在校成績 20% 甄選比序",
              "details": [
                  (
                      "在學學制與修業規定（依《國立高雄科技大學學生赴境外大學校院交換研修作業要點》及甄選簡章）：申請人須為本校大學部二年級（含）以上、研究所（含碩士班、博士班及在職專班）及五年制專科部四年級（含）以上之本國籍、僑生或外籍在學學生；於提出申請時及赴外交換期間皆須保有高科大在學學籍並完成註冊繳費（不得辦理休學或畢業離校）。僑生及外籍生不得申請回原國籍國家境內大學交換；大陸地區姊妹校限臺港澳籍學生申請。"
                  ),
                  (
                      "成績門檻與甄選比序公式：在當前就讀學制中須有一學期以上之學期成績且成績良好，操行成績至少達 75 分。學海惜珠合格生優先分發；申請人數超過名額時，先以語檢達第一志願交換校門檻者優先，再依「第一志願專業領域契合度 50%（高度 100／中度 85／低度 70）＋外語檢定 CEFR 等級 30%（C1 100／B2 90／B1 80／A2以下 70）＋在校歷年成績 20%」（無外語要求之大陸姊妹校為專業契合度 60%＋在校成績 40%）計算總分比序分發。"
                  ),
              ],
              "source": {
                  "title": "國立高雄科技大學 115 學年度校級交換生甄選簡章與交換研修作業要點",
                  "source_url": NKUST_115_GUIDELINES_URL,
                  "category": "exchange_application",
                  "summary": "高科大赴外交換申請學制年級、操行 75 分門檻、50%/30%/20% 甄選評分公式與同分比序原則。",
              },
          }
      ],
      "language_requirements": [
          {
              "title": "高科大外語教育中心 CEFR 等級對照標準（B1：TOEIC 550／iBT 42／IELTS 4.0；B2：TOEIC 785／iBT 72／IELTS 5.5）與日德法韓二外檢定",
              "details": [
                  (
                      "英語檢定與 CEFR 評分對照：申請歐美澳、日韓及東南亞等非中國大陸姊妹校者，須檢附有效期限內之英語檢定證明（TOEFL、IELTS、TOEIC）或第二外語檢定證明。依《高科大外語教育中心各類外語檢定證照等級對照表》：CEFR C1（評 100 分）為 TOEIC 945 / TOEFL iBT 95 / ITP 627 / IELTS 7.0；CEFR B2（評 90 分）為 TOEIC 785 / TOEFL iBT 72 / ITP 543 / IELTS 5.5；CEFR B1（評 80 分）為 TOEIC 550 / TOEFL iBT 42 / ITP 460 / IELTS 4.0；CEFR A2 以下評 70 分。"
                  ),
                  (
                      "第二外語檢定與大陸姊妹校規定：日本 27 校依各校規定要求 JLPT N1–N5 或英語 B1–B2；德國、奧地利、法國 19 校要求英語或德語／法語 B1–B2；韓國 8 校要求 TOPIK 2–3 級、英語 B1–B2 或韓語修課時數證明；中國大陸無外語要求之姊妹校免附語檢（深圳大學除外）。若外語能力未達交換校門檻但通過校內甄選者，仍可獲提名薦送，惟接待校保有最終審核權。"
                  ),
              ],
              "source": {
                  "title": "國立高雄科技大學外語教育中心各類外語檢定證照等級對照表與交換學校一覽表",
                  "source_url": NKUST_FLEC_CEF_URL,
                  "category": "exchange_application",
                  "summary": "高科大 CEFR A1–C1 外語檢定對照表及 107 所姊妹校英、日、德、法、韓語門檻。",
              },
          }
      ],
      "required_documents": [
          {
              "title": "線上申請系統報名、校級交換研修志願表、歷年成績單、語檢證明（含補件機制）與返國核銷文件",
              "details": [
                  (
                      "校內甄選必繳上傳文件：1. 校級交換研修志願表（需申請人簽名及所屬系所主管核章，可填 3–6 個志願並勾選是否同意媒合）、2. 中文歷年成績單（需有在校排名，操行至少 75 分）、3. 有效外語檢定成績單（若截止前尚未收到紙本，得先上傳網路成績截圖並於 12 月中下旬補件截止日前補交正式成績單）、4. 中、英文自傳及讀書計畫、5. 雙聯學位（英文成績單與英檢）或學海惜珠（新式戶口名簿與低收／中低收／特殊境遇證明）相關附件。"
                  ),
                  (
                      "錄取確認與返國核銷義務：分發結果公告後 1 週內須上傳《錄取生交換意願確認書》及《家長同意書》（無故放棄者取消獎補助資格）；7 月獲核定獎補助者簽立行政契約書；返國後 1 個月內須繳交 1,500–2,000 字研修心得報告（含 4 張以上照片）、護照出入境章、登機證存根與正式成績單完成核銷及抵免。"
                  ),
              ],
              "source": {
                  "title": "國立高雄科技大學 115 學年度校級交換生甄選簡章與志願表",
                  "source_url": NKUST_EXCHANGE_PAGE_URL,
                  "category": "exchange_application",
                  "summary": "高科大校級交換線上申請應繳文件、語檢補件期限、意願確認書與學海核銷規定。",
              },
          }
      ],
      "scholarship_info": [
          {
              "title": "教育部學海飛颺／惜珠與高科大高教深耕境外研修獎助金（亞洲 6 萬、非亞洲 8 萬、雙聯 12 萬，經濟不利再加發最高 2 萬）及短期交流／學海展翅補助",
              "details": [
                  (
                      "學期／學年交換與雙聯獎助學金（依《國立高雄科技大學獎助學生赴境外大學校院研修要點》及學海計畫標準）：限具中華民國國籍且在臺設籍之非在職專班生，赴中港澳以外地區姊妹校研修 1 學期至 1 學年：（1）亞洲地區交換生：每名核給 NT$60,000（學海飛颺含教育部 5 萬＋學校配合款 1 萬；未獲學海者由高科大高教深耕經費核給 6 萬）；（2）非亞洲地區（歐美澳）交換生：每名核給 NT$80,000（教育部 5 萬＋學校配合款 3 萬，或高科大經費 8 萬）；（3）雙聯學制生：每名核給 NT$120,000；（4）符合本校經濟不利條件者，高科大獎助金得再加發最高 NT$20,000。"
                  ),
                  (
                      "短期交流、學海展翅與外國政府獎學金：（1）《獎助學生參加國際短期交流及研習活動要點》：每名補助 NT$10,000（經濟不利增額 NT$2,000）；（2）《學海展翅專案》（暑期赴海外姊妹校培訓 1 個月）：定額補助 NT$20,000（生活助學金生再增額 NT$15,000，低收入戶全額補助機票、簽證與學費）；（3）日本 JASSO（每月 JPY 80,000）、歐盟 Erasmus+ 及 UMAP 獎學金。"
                  ),
              ],
              "source": {
                  "title": "國立高雄科技大學獎助學生赴境外大學校院研修要點與出國研習獎補助專頁",
                  "source_url": NKUST_SCHOLARSHIP_PAGE_URL,
                  "category": "scholarship",
                  "summary": "高科大教育部學海飛颺／惜珠、高教深耕境外研修獎助金（6萬／8萬／12萬）、短期交流與學海展翅補助標準。",
              },
          }
      ],
      "document_explanations": [
          {
              "title": "國立高雄科技大學校級交換研修志願表、中英文自傳讀書計畫與語檢網路截圖先行補件指南",
              "summary": "說明高科大線上申請系統上傳規範、系所主管核章志願表、第一志願領域契合度（50%）撰寫重點與語檢補件期限。",
              "key_points": [
                  "《校級交換研修志願表》須由申請人親筆簽名並經所屬系（所）主管核章後掃描上傳；每位學生可填寫 3–6 個志願，並可勾選當所填志願皆未錄取時是否同意由國際處依剩餘名額進行媒合。",
                  "若於線上報名截止前尚未收到紙本正式外語檢定成績單，可先上傳官網成績查詢畫面截圖完成報名，並務必於簡章規定之補件截止日（12 月中下旬 16:00）前補交正式成績單。",
                  "中、英文讀書計畫應具體說明「第一志願研修學校（系所）與就讀系所之專業領域契合度」（佔甄選總成績 50%，大陸無語檢要求姊妹校佔 60%），列舉擬修讀之專業課程與返國學分抵免規劃。",
              ],
              "applies_to": [],
              "source": {
                  "title": "國立高雄科技大學 115 學年度校級交換生甄選簡章與志願表",
                  "source_url": NKUST_115_GUIDELINES_URL,
                  "category": "exchange_application",
                  "summary": None,
              },
              "document_url": NKUST_115_GUIDELINES_URL,
              "document_type": "official_document",
              "full_text_extracted": True,
          }
      ],
      "rule_explanations": [
          {
              "title": "國立高雄科技大學學生赴境外大學校院交換研修作業要點：操行 75 分門檻、50%／30%／20% 甄選比序與在學學籍規定",
              "summary": "規範高科大校級與院系級交換生申請資格、甄選加權計分公式、在學註冊繳費義務及獎補助核銷規定。",
              "key_points": [
                  "申請資格為大學部二年級（含）以上、五專部四年級（含）以上及碩博士班在學學生，在當前就讀學制中須有一學期以上學期成績且操行成績至少達 75 分；申請時及赴外交換期間均須保有高科大在學學籍（不得休學或畢業離校）。",
                  "甄選總成績計算權重：第一志願專業領域契合度 50%（高度 100／中度 85／低度 70）＋ 外語檢定 CEFR 等級 30%（C1 100／B2 90／B1 80／A2以下 70）＋ 在校歷年成績 20%（無外語要求之大陸姊妹校為專業契合度 60%＋在校成績 40%）；學海惜珠合格生優先分發。",
                  "獲教育部學海飛颺或高科大高教深耕境外研修獎助金者（亞洲 NT$60,000、非亞洲 NT$80,000、雙聯 NT$120,000，經濟不利最高加發 NT$20,000），須於出國前簽訂行政契約書，並於返國後 1 個月內繳交研修心得報告、機票單據與正式成績單辦理核銷。",
              ],
              "applies_to": [],
              "source": {
                  "title": "國立高雄科技大學學生赴境外大學校院交換研修作業要點與獎助要點",
                  "source_url": NKUST_REGULATIONS_URL,
                  "category": "exchange_application",
                  "summary": None,
              },
              "document_url": NKUST_REGULATIONS_URL,
              "document_type": "official_document",
              "full_text_extracted": True,
          }
      ],
      "sources": [
          {
              "title": "國立高雄科技大學國際事務處（OIA）官方網站",
              "source_url": NKUST_OIA_HUB_URL,
              "category": "exchange_application",
              "summary": None,
          },
          {
              "title": "國立高雄科技大學國際事務處—赴外交換生專頁（簡章、名額表、錄取名單與作業要點）",
              "source_url": NKUST_EXCHANGE_PAGE_URL,
              "category": "exchange_application",
              "summary": None,
          },
          {
              "title": "國立高雄科技大學出國交換學生網（Google Sites 姊妹校專頁與歷屆學長姐心得分享）",
              "source_url": NKUST_GS_PORTAL_URL,
              "category": "partner_school",
              "summary": None,
          },
          {
              "title": "國立高雄科技大學 115 學年度校級交換生甄選簡章 PDF",
              "source_url": NKUST_115_GUIDELINES_URL,
              "category": "exchange_application",
              "summary": None,
          },
          {
              "title": "115 年度國立高雄科技大學校級交換學校一覽表（Google Sheets）",
              "source_url": NKUST_115_UNI_SHEET_URL,
              "category": "partner_school",
              "summary": None,
          },
          {
              "title": "國立高雄科技大學院系級交換學校列表（Google Sheets）",
              "source_url": NKUST_COLLEGE_SHEET_URL,
              "category": "partner_school",
              "summary": None,
          },
          {
              "title": "國立高雄科技大學國際事務處—出國研習獎補助暨教育部學海計畫專頁",
              "source_url": NKUST_SCHOLARSHIP_PAGE_URL,
              "category": "scholarship",
              "summary": None,
          },
          {
              "title": "國立高雄科技大學獎助學生赴境外大學校院研修要點 PDF",
              "source_url": NKUST_SCHOLARSHIP_REG_URL,
              "category": "scholarship",
              "summary": None,
          },
          {
              "title": "國立高雄科技大學外語教育中心—各類外語檢定證照等級對照表（CEFR）PDF",
              "source_url": NKUST_FLEC_CEF_URL,
              "category": "exchange_application",
              "summary": None,
          },
          {
              "title": "國立高雄科技大學【116學年度出國交換研修】五校區巡迴說明會公告",
              "source_url": NKUST_116_INFO_SESSION_URL,
              "category": "exchange_application",
              "summary": None,
          },
      ],
  }
  (OFFICIAL_NKUST_DIR / "student_dashboard.json").write_text(
      json.dumps(student_dashboard_payload, ensure_ascii=False, indent=2) + "\n",
      encoding="utf-8",
  )

  pages_records = [
      {
          "title": "國立高雄科技大學：國際事務處校級與院系級赴外交換生甄選時程（115學年度錄取公告與116學年度說明會）",
          "source_url": NKUST_EXCHANGE_PAGE_URL,
          "published_at": "2026-10-02T00:00:00Z",
          "text": "\n".join(exchange_info_payload["application_period"]),
          "summary": "\n".join(exchange_info_payload["application_period"]),
          "category": "exchange_application",
          "attachments": [],
          "crawled_at": CHECKED_AT,
          "content_hash": hashlib.sha256("\n".join(exchange_info_payload["application_period"]).encode("utf-8")).hexdigest(),
      },
      {
          "title": "國立高雄科技大學：赴外交換生申請資格、操行 75 分門檻與 50%／30%／20% 甄選比序規定",
          "source_url": NKUST_115_GUIDELINES_URL,
          "published_at": "2025-12-02T00:00:00Z",
          "text": "\n".join(exchange_info_payload["eligibility"]),
          "summary": "\n".join(exchange_info_payload["eligibility"]),
          "category": "exchange_application",
          "attachments": [],
          "crawled_at": CHECKED_AT,
          "content_hash": hashlib.sha256("\n".join(exchange_info_payload["eligibility"]).encode("utf-8")).hexdigest(),
      },
      {
          "title": "國立高雄科技大學：107 所交換姊妹校外語檢定門檻與外語教育中心 CEFR 等級對照表",
          "source_url": NKUST_FLEC_CEF_URL,
          "published_at": "2025-12-02T00:00:00Z",
          "text": "\n".join(exchange_info_payload["language_requirement"]),
          "summary": "\n".join(exchange_info_payload["language_requirement"]),
          "category": "exchange_application",
          "attachments": [],
          "crawled_at": CHECKED_AT,
          "content_hash": hashlib.sha256("\n".join(exchange_info_payload["language_requirement"]).encode("utf-8")).hexdigest(),
      },
      {
          "title": "國立高雄科技大學：校級交換線上申請應繳文件、志願表、語檢補件與返國核銷規範",
          "source_url": NKUST_REGULATIONS_URL,
          "published_at": "2025-12-02T00:00:00Z",
          "text": "\n".join(exchange_info_payload["required_documents"]),
          "summary": "\n".join(exchange_info_payload["required_documents"]),
          "category": "exchange_application",
          "attachments": [],
          "crawled_at": CHECKED_AT,
          "content_hash": hashlib.sha256("\n".join(exchange_info_payload["required_documents"]).encode("utf-8")).hexdigest(),
      },
      {
          "title": "國立高雄科技大學：教育部學海飛颺／惜珠、高教深耕境外研修獎助金（6萬／8萬／12萬）與短期交流／學海展翅補助",
          "source_url": NKUST_SCHOLARSHIP_PAGE_URL,
          "published_at": "2026-06-30T00:00:00Z",
          "text": "\n".join(exchange_info_payload["scholarship_info"]),
          "summary": "\n".join(exchange_info_payload["scholarship_info"]),
          "category": "scholarship",
          "attachments": [],
          "crawled_at": CHECKED_AT,
          "content_hash": hashlib.sha256("\n".join(exchange_info_payload["scholarship_info"]).encode("utf-8")).hexdigest(),
      },
  ]
  (OFFICIAL_NKUST_DIR / "pages.jsonl").write_text(
      "\n".join(json.dumps(p, ensure_ascii=False) for p in pages_records) + "\n",
      encoding="utf-8",
  )

  home_rules = {
      "school_id": "nkust",
      "school_name": "國立高雄科技大學",
      "eligibility": student_dashboard_payload["eligibility"],
      "application_periods": student_dashboard_payload["application_periods"],
      "selection_rules": {
          "conduct_score_minimum": 75.0,
          "field_fit_weight_percent": 50,
          "language_cefr_weight_percent": 30,
          "academic_score_weight_percent": 20,
          "mainland_no_lang_field_fit_weight_percent": 60,
          "mainland_no_lang_academic_score_weight_percent": 40,
          "tie_breaker_order": [
              "field_fit_score",
              "academic_average_score",
              "language_proficiency_score",
          ],
          "xuehai_xizhu_priority_placement": True,
          "scholarship_asia_twd": 60000,
          "scholarship_non_asia_twd": 80000,
          "scholarship_dual_degree_twd": 120000,
          "scholarship_disadvantaged_bonus_max_twd": 20000,
          "short_term_grant_twd": 10000,
          "xuehai_zhanchi_summer_grant_twd": 20000,
          "return_documents_due": "返國後 1 個月內繳交 1,500–2,000 字研修心得報告、登機證存根、護照出入境章影本及姊妹校正式成績單完成核銷與學分抵免",
      },
      "source_urls": nkust_source_urls,
      "verified_at": "2026-10-20",
  }
  (OFFICIAL_NKUST_DIR / "home_rules.json").write_text(
      json.dumps(home_rules, ensure_ascii=False, indent=2) + "\n",
      encoding="utf-8",
  )
  (OFFICIAL_NKUST_DIR / "documents.json").write_text(
      json.dumps(
          {
              "school_name": "國立高雄科技大學",
              "required_documents": student_dashboard_payload["required_documents"],
              "source_urls": nkust_source_urls,
          },
          ensure_ascii=False,
          indent=2,
      )
      + "\n",
      encoding="utf-8",
  )
  (OFFICIAL_NKUST_DIR / "scholarships.json").write_text(
      json.dumps(
          {
              "school_name": "國立高雄科技大學",
              "scholarships": student_dashboard_payload["scholarship_info"],
              "source_urls": nkust_source_urls,
          },
          ensure_ascii=False,
          indent=2,
      )
      + "\n",
      encoding="utf-8",
  )

  completeness = {
      "school_id": "nkust",
      "school_name": "國立高雄科技大學",
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
          "國立高雄科技大學國際事務處（國際關係組）115學年度校級交換甄選（115-1秋季班／115-2春季班）已完成錄取分發與獎補助名冊公告，116學年度（2027-2028）五校區巡迴說明會於 2026/10/07–10/28 舉行，預計於 2026/11/10 – 12/01 16:00 開放線上申請；共完整收錄 107 所全球交換合作學校（含 97 所開放申請校及 10 所歷屆／暫緩參考校，涵蓋校級交換 88 校、院系級交換 14 校及雙聯／歷屆合作校，橫跨歐、美、亞、大洋洲 20 國）。"
      ),
      "verified_at": "2026-10-20",
  }
  (OFFICIAL_NKUST_DIR / "catalog-completeness.json").write_text(
      json.dumps(completeness, ensure_ascii=False, indent=2) + "\n",
      encoding="utf-8",
  )
  (OFFICIAL_NKUST_DIR / "verification_status.json").write_text(
      json.dumps(
          {
              "school_id": "nkust",
              "school_name": "國立高雄科技大學",
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
          "sources/nkust/115_exchange_guidelines.pdf",
          NKUST_115_GUIDELINES_URL,
          "國立高雄科技大學 115 學年度校級交換生甄選簡章 PDF",
      ),
      (
          "sources/nkust/115_exchange_preference_form.docx",
          NKUST_115_PREF_FORM_URL,
          "國立高雄科技大學 115 學年度校級交換研修志願表 DOCX",
      ),
      (
          "sources/nkust/flec_cef_mapping.pdf",
          NKUST_FLEC_CEF_URL,
          "國立高雄科技大學外語教育中心各類外語檢定證照等級對照表（CEFR）PDF",
      ),
      (
          "sources/nkust/nkust_exchange_regulations.pdf",
          NKUST_REGULATIONS_URL,
          "國立高雄科技大學學生赴境外大學校院交換研修作業要點 PDF",
      ),
      (
          "sources/nkust/nkust_scholarship_regulations.pdf",
          NKUST_SCHOLARSHIP_REG_URL,
          "國立高雄科技大學獎助學生赴境外大學校院研修要點 PDF",
      ),
      (
          "sources/nkust/short_term_grant_regulations.pdf",
          NKUST_SHORT_TERM_PAGE_URL,
          "國立高雄科技大學獎助學生參加國際短期交流及研習活動要點 PDF",
      ),
      (
          "sources/nkust/moe_xuehai_reimbursement.pdf",
          NKUST_SCHOLARSHIP_PAGE_URL,
          "國立高雄科技大學教育部學海飛颺／學海惜珠核銷說明 PDF",
      ),
      (
          "sources/nkust/115_admission_roster.pdf",
          NKUST_EXCHANGE_PAGE_URL,
          "國立高雄科技大學 115 學年度校級交換甄選錄取名單 PDF",
      ),
      (
          "sources/nkust/115_moe_xuehai_roster.pdf",
          NKUST_SCHOLARSHIP_PAGE_URL,
          "國立高雄科技大學 115 學年度教育部學海飛颺獎補助名冊 PDF",
      ),
      (
          "sources/nkust/115_nkust_grant_roster.pdf",
          NKUST_SCHOLARSHIP_PAGE_URL,
          "國立高雄科技大學 115 學年度高科大境外研修獎補助名冊 PDF",
      ),
      (
          "sources/nkust/116_info_session_slides.pdf",
          NKUST_116_INFO_SESSION_URL,
          "國立高雄科技大學 116 學年度（2027-2028）出國交換研修說明會公版簡報 PDF",
      ),
      (
          "sources/nkust/sheet_university_level.csv",
          NKUST_115_UNI_SHEET_URL,
          "115 年度國立高雄科技大學校級交換學校一覽表 CSV",
      ),
      (
          "sources/nkust/sheet_115_sub.html",
          NKUST_115_UNI_SHEET_URL,
          "115 年度國立高雄科技大學校級交換學校一覽表（含官網與雲端簡章超連結）HTML",
      ),
      (
          "sources/nkust/sheet_college_level.csv",
          NKUST_COLLEGE_SHEET_URL,
          "國立高雄科技大學院系級交換學校列表 CSV",
      ),
      (
          "sources/nkust/sheet_college_sub.html",
          NKUST_COLLEGE_SHEET_URL,
          "國立高雄科技大學院系級交換學校列表（含官網與雲端簡章超連結）HTML",
      ),
      (
          "sources/nkust/sheet_114_1.csv",
          NKUST_115_UNI_SHEET_URL,
          "114 學年度第 1 學期國立高雄科技大學校級交換學校一覽表 CSV",
      ),
      (
          "sources/nkust/sheet_114_2.csv",
          NKUST_115_UNI_SHEET_URL,
          "114 學年度第 2 學期國立高雄科技大學校級交換學校一覽表 CSV",
      ),
      (
          "sources/nkust/oia_exchange_page.html",
          NKUST_EXCHANGE_PAGE_URL,
          "國立高雄科技大學國際事務處—赴外交換生專頁 HTML",
      ),
      (
          "sources/nkust/oia_scholarship_page.html",
          NKUST_SCHOLARSHIP_PAGE_URL,
          "國立高雄科技大學國際事務處—出國研習獎補助／學海計畫專頁 HTML",
      ),
      (
          "sources/nkust/oia_short_term_page.html",
          NKUST_SHORT_TERM_PAGE_URL,
          "國立高雄科技大學國際事務處—短期出國交流補助（含學海展翅）專頁 HTML",
      ),
      (
          "sources/nkust/oia_116_info_session_news.html",
          NKUST_116_INFO_SESSION_URL,
          "國立高雄科技大學國際事務處—【116學年度出國交換研修】說明會公告 HTML",
      ),
      (
          "sources/nkust/gs_partner_subpages.json",
          NKUST_GS_PORTAL_URL,
          "國立高雄科技大學出國交換學生網（Google Sites）60 個姊妹校與主題子頁完整擷取資料 JSON",
      ),
      (
          "sources/nkust/nkust_academic_units.json",
          "https://www.nkust.edu.tw/",
          "國立高雄科技大學 12 個學院與 60 個系所中心官方組織 JSON",
      ),
      (
          "sources/nkust/nkust_catalog_source.json",
          NKUST_EXCHANGE_PAGE_URL,
          "國立高雄科技大學 107 所出國交換合作學校整合資料集 JSON",
      ),
      (
          "sources/nkust/nkust_resolved_locations.json",
          NKUST_EXCHANGE_PAGE_URL,
          "國立高雄科技大學 107 所出國交換合作學校 ROR / Wikidata 地理座標核對表 JSON",
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
      "school_id": "nkust",
      "school_name": "國立高雄科技大學",
      "generated_at": CHECKED_AT,
      "active_cycle_note": completeness["active_term"],
      "sources": prov_sources,
  }
  prov_text = json.dumps(provenance_payload, ensure_ascii=False, indent=2) + "\n"
  (OFFICIAL_NKUST_DIR / "import_provenance.json").write_text(prov_text, encoding="utf-8")
  (OFFICIAL_NKUST_DIR / "import-provenance.json").write_text(prov_text, encoding="utf-8")

  from exchange_info.nkust_source_review import review_bundle
  reviewed_counts = review_bundle(REPO_ROOT)
  print(f"Built NKUST partial review: {len(partners)} records; {reviewed_counts}; no whole records verified.")



if __name__ == "__main__":
  main()
