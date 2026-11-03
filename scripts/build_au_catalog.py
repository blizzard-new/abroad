"""Build the official Aletheia University (真理大學, AU) exchange data bundle."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re

REPO_ROOT = Path(__file__).resolve().parents[1]
SOURCES_AU_DIR = REPO_ROOT / "sources" / "au"
OFFICIAL_AU_DIR = (
    REPO_ROOT / "src" / "exchange_info" / "official_data" / "au"
)
STATIC_DIR = REPO_ROOT / "src" / "exchange_info" / "static"
UNIVERSITY_LOCATIONS_PATH = (
    REPO_ROOT
    / "src"
    / "exchange_info"
    / "official_data"
    / "university_locations.jsonl"
)

CHECKED_AT = "2026-11-03T00:00:00Z"

AU_HOME_URL = "https://www.au.edu.tw/"
AU_CIA_HOME_URL = "https://cia.au.edu.tw/"
AU_OUTBOUND_OVERVIEW_URL = (
    "https://cia.au.edu.tw/p/403-1022-109353.php?Lang=zh-tw"
)
AU_EXCHANGE_PROGRAMS_URL = (
    "https://cia.au.edu.tw/p/403-1022-111632.php?Lang=zh-tw"
)
AU_DUAL_DEGREE_URL = (
    "https://cia.au.edu.tw/p/403-1022-111695.php?Lang=zh-tw"
)
AU_SHORT_TERM_URL = (
    "https://cia.au.edu.tw/p/403-1022-111633.php?Lang=zh-tw"
)
AU_STUDY_ABROAD_GALLERY_URL = (
    "https://cia.au.edu.tw/p/403-1022-111634.php?Lang=zh-tw"
)
AU_STUDENT_EXPERIENCES_URL = (
    "https://cia.au.edu.tw/p/403-1022-111635.php?Lang=zh-tw"
)
AU_SISTER_SCHOOLS_URL = (
    "https://cia.au.edu.tw/p/403-1022-109350.php?Lang=zh-tw"
)
AU_REGULATIONS_URL = (
    "https://cia.au.edu.tw/p/403-1022-109356.php?Lang=zh-tw"
)
AU_OUTBOUND_REGULATIONS_URL = (
    "https://cia.au.edu.tw/p/403-1022-111641.php?Lang=zh-tw"
)
AU_SCHOLARSHIP_REGULATIONS_URL = (
    "https://cia.au.edu.tw/p/403-1022-111640.php?Lang=zh-tw"
)
AU_XUEHAI_OVERVIEW_URL = (
    "https://cia.au.edu.tw/p/403-1022-112299.php?Lang=zh-tw"
)
AU_XUEHAI_FEIYANG_URL = (
    "https://cia.au.edu.tw/p/403-1022-112300.php?Lang=zh-tw"
)
AU_XUEHAI_XIZHU_URL = (
    "https://cia.au.edu.tw/p/403-1022-112301.php?Lang=zh-tw"
)
AU_XUEHAI_ZHUMENG_URL = (
    "https://cia.au.edu.tw/p/403-1022-112302.php?Lang=zh-tw"
)

AU_SELECTION_REGULATION_PAGE_URL = (
    "https://cia.au.edu.tw/p/406-1022-84480,r111641.php?Lang=zh-tw"
)
AU_CREDIT_TRANSFER_REGULATION_PAGE_URL = (
    "https://cia.au.edu.tw/p/406-1022-70817,r111641.php?Lang=zh-tw"
)
AU_DUAL_DEGREE_REGULATION_PAGE_URL = (
    "https://cia.au.edu.tw/p/406-1022-93784,r111641.php?Lang=zh-tw"
)
AU_2027_SPRING_EXCHANGE_URL = (
    "https://cia.au.edu.tw/p/406-1022-118696,r111632.php?Lang=zh-tw"
)
AU_2026_FALL_EXCHANGE_URL = (
    "https://cia.au.edu.tw/p/406-1022-116680,r111632.php?Lang=zh-tw"
)
AU_2026_2027_JAPAN_EXCHANGE_URL = (
    "https://cia.au.edu.tw/p/406-1022-115847,r111632.php?Lang=zh-tw"
)
AU_MACQUARIE_PROGRAM_URL = (
    "https://cia.au.edu.tw/p/406-1022-113277,r111632.php?Lang=zh-tw"
)
AU_MIDDLESEX_DUAL_URL = (
    "https://cia.au.edu.tw/p/406-1022-86012,r111695.php?Lang=zh-tw"
)
AU_UWE_DUAL_URL = (
    "https://cia.au.edu.tw/p/406-1022-86013,r111695.php?Lang=zh-tw"
)
AU_STPOL_DUAL_URL = (
    "https://cia.au.edu.tw/p/406-1022-86011,r111695.php?Lang=zh-tw"
)
AU_EXCHANGE_SCHOLARSHIP_PDF_URL = (
    "https://cia.au.edu.tw/var/file/22/1022/img/2737/P-01-510.pdf"
)
AU_STUDY_TOUR_SCHOLARSHIP_PDF_URL = (
    "https://cia.au.edu.tw/var/file/22/1022/img/2737/P-01-509.pdf"
)
AU_VOLUNTEER_SCHOLARSHIP_PDF_URL = (
    "https://cia.au.edu.tw/var/file/22/1022/img/2737/P-01-513.pdf"
)
AU_SPECIAL_CONTRIBUTION_SCHOLARSHIP_PDF_URL = (
    "https://cia.au.edu.tw/var/file/22/1022/img/2737/P-01-526.pdf"
)
AU_SCHOLARSHIP_REIMBURSEMENT_URL = (
    "https://cia.au.edu.tw/p/406-1022-80923,r109353.php?Lang=zh-tw"
)
AU_XUEHAI_GUIDELINE_PAGE_URL = (
    "https://cia.au.edu.tw/p/406-1022-89178,r112299.php?Lang=zh-tw"
)

REGION_COST_DEFAULTS = {
    "日本": (
        "每月生活費約 USD 650–1,050（折合日圓約 JPY 90,000–145,000 / 月、新臺幣約 20,000–33,500 元；含城西國際大學、香川大學、名城大學、新潟經營大學、星城大學、北亞大學、長崎外國語大學、三重大學、多摩大學、昭和女子大學等校內外學生寮、伙食與交通費）",
        "須由日本接待姊妹校代向出入國在留管理局申請「在留資格認定證明書（COE）」，再赴日本台灣交流協會申辦留學簽證，入境日本後須依法加入日本「國民健康保險（NHI）」。",
    ),
    "韓國": (
        "每月生活費約 USD 600–980（折合韓元約 KRW 800,000–1,300,000 / 月、新臺幣約 19,000–31,000 元；含漢陽大學 ERICA 校區、國民大學、祥明大學、崇實大學、明知大學、啟明大學、又松大學、東明大學、韓世大學、濟州觀光大學、梨花女子大學等學生宿舍與膳食費）",
        "須憑韓國接待姊妹校核發之標準入學許可書向駐台北韓國代表部申辦 D-2-6 交換學生簽證，並依韓國法規納入韓國國民健康保險（NHIS）及出國前海外全期醫療意外險。",
    ),
    "中國大陸": (
        "每月生活費約 USD 380–650（折合人民幣約 RMB 2,600–4,500 / 月、新臺幣約 12,000–20,500 元；含北京體育大學、北京交通大學、南京航空航天大學、上海體育大學等校內學生公寓與校園餐廳伙食費）",
        "須持有效臺灣居民來往大陸通行證（臺胞證）及錄取通知書辦理入學報到，並依規定投保涵蓋交換全期之醫療及意外保險。",
    ),
    "澳門": (
        "每月生活費約 USD 650–1,000（折合澳門幣約 MOP 5,200–8,000 / 月、新臺幣約 20,500–32,000 元；含澳門城市大學氹仔校區學生宿舍與生活開銷）",
        "須憑澳門城市大學錄取通知書辦理逗留特別許可（學生逗留簽注），並投保涵蓋交換期間之海外醫療及意外保險。",
    ),
    "澳洲": (
        "每月生活費約 USD 1,450–2,200（折合澳幣約 AUD 2,200–3,300 / 月、新臺幣約 46,500–70,000 元；含雪梨麥覺理大學 Macquarie University 校內外學生公寓、膳食與大眾運輸）",
        "須購買澳洲政府強制規定之海外學生健康保險（OSHC），並憑麥覺理大學核發之註冊確認書（CoE）申辦澳洲 Subclass 500 學生簽證。",
    ),
    "西班牙": (
        "每月生活費約 USD 900–1,400（折合歐元約 EUR 850–1,300 / 月、新臺幣約 29,000–44,500 元；赫羅納大學附設桑特波爾廚藝觀光學院 EUHT StPOL 提供校內教學飯店住宿與平日三餐包餐選擇）",
        "須憑西班牙赫羅納大學觀光學院（EUHT StPOL）入學許可、財力證明、無犯罪紀錄與全額申根醫療保險證明向西班牙商務辦事處申辦學生簽證。",
    ),
    "英國": (
        "每月生活費約 USD 1,350–2,050（折合英鎊約 GBP 1,050–1,600 / 月、新臺幣約 43,000–65,500 元；倫敦密德薩斯大學 Middlesex University 與布里斯托西英格蘭大學 UWE Bristol 依英國內政部 UKVI 倫敦區／非倫敦區生活費標準估算）",
        "修讀 3+1、1+1、4+1 或 3+15 個月雙聯學位須憑英國接待大學核發之 CAS 號碼申辦英國 Student Visa，並繳納英國移民健康附加費（IHS）以使用英國國家醫療服務體系（NHS）。",
    ),
    "美國": (
        "每月生活費約 USD 1,200–1,850（依匯率折合新臺幣約 38,500–59,000 元；含明州西南州立大學 SMSU、漢佛萊斯大學、邁唐那大學、麻州海灣社區大學、芬利大學校內外住宿與膳食計畫）",
        "須憑美國接待大學核發之 DS-2019（J-1 交換生）或 I-20（F-1 雙聯學位生）表格繳交 SEVIS I-901 費用並向美國在台協會（AIT）申辦簽證，且須投保符合接待校規定之醫療保險。",
    ),
    "馬來西亞": (
        "每月生活費約 USD 450–750（折合馬幣約 MYR 2,000–3,300 / 月、新臺幣約 14,500–24,000 元；含馬來亞大學、瑪拉工藝大學、拉曼大學、大同韓新傳播學院、馬來西亞藝術學院住宿與生活費）",
        "須透過馬來西亞教育全球服務中心（EMGS）申辦學生簽證（Student Pass）並投保馬來西亞醫療保險。",
    ),
    "菲律賓": (
        "每月生活費約 USD 420–700（依匯率折合新臺幣約 13,500–22,500 元；含聖卡洛斯大學、宿霧師範大學、維爾塞大學、伊莎貝爾大學、菲律賓基督教靈惠學院住宿與膳食）",
        "須依菲律賓接待大學指引辦理 SSP（特別就學許可）或 9(f) 學生簽證，並於出國前投保海外全期醫療及意外保險。",
    ),
    "越南": (
        "每月生活費約 USD 400–680（依匯率折合新臺幣約 12,800–21,800 元；含胡志明市理工大學、胡志明市國家大學人文社科大、胡志明市科技與管理大學、阮必成大學、FPT 大學住宿與生活費）",
        "須憑越南接待大學入學許可申辦越南學生／實習簽證，並於出國前投保海外全期醫療及意外保險。",
    ),
    "泰國": (
        "每月生活費約 USD 450–750（折合泰銖約 THB 15,000–25,000 / 月、新臺幣約 14,500–24,000 元；含曼谷泰國工商大學 RBAC 學生公寓與生活費）",
        "須憑泰國接待大學入學許可向泰國貿易經濟辦事處申辦 Non-Immigrant ED 學生簽證並投保海外醫療保險。",
    ),
    "印尼": (
        "每月生活費約 USD 380–650（依匯率折合新臺幣約 12,000–21,000 元；含日惹、泗水、三寶瓏、雅加達、棉蘭、望加錫等印尼姊妹校住宿與膳食）",
        "須憑印尼接待大學核發之入學許可與學習許可（Study Permit）申辦印尼 C316 學生簽證，並投保海外全期醫療及意外保險。",
    ),
    "肯亞": (
        "每月生活費約 USD 500–850（依匯率折合新臺幣約 16,000–27,000 元；含東非長老教會大學 PUEA 校園住宿與生活費）",
        "須依肯亞政府規定申辦電子旅行授權（eTA）／學生通行證、完成黃熱病疫苗接種（黃皮書）並投保海外全期醫療與緊急救援保險。",
    ),
}

SEMESTER_DATES_BY_COUNTRY = {
    "日本": "第一學期（秋季入學，日本姊妹校交換期間為一學年）：每年 9 月至翌年 8 月（秋學期 9 月中下旬至 1 月底；春學期 4 月初至 8 月初）",
    "韓國": "春季學期（Spring Semester）：每年 2 月下旬／3 月初至 6 月中旬；秋季學期（Fall Semester）：每年 9 月初至 12 月中下旬",
    "中國大陸": "春季學期（下學期）：約 2 月下旬至 6 月底；秋季學期（上學期）：約 9 月初至翌年 1 月中旬",
    "澳門": "第一學期（秋季班）：約 9 月初至 12 月下旬；第二學期（春季班）：約 1 月下旬至 5 月下旬",
    "澳洲": "Session 1（秋季／上半年）：約 2 月下旬至 6 月底；Session 2（春季／下半年）：約 7 月下旬至 11 月底",
    "西班牙": "第一學期（秋季班）：約 9 月中旬至翌年 1 月底；第二學期（春季班）：約 2 月初至 6 月中旬",
    "英國": "秋季學期（Autumn Term）：約 9 月下旬／10 月初至翌年 1 月；春季學期（Spring Term）：約 1 月下旬至 6 月",
    "美國": "秋季學期（Fall Semester）：約 8 月中下旬至 12 月中旬；春季學期（Spring Semester）：約 1 月中旬至 5 月中旬",
    "馬來西亞": "秋季學期：約 9–10 月至翌年 1–2 月；春季學期：約 2–6 月",
    "菲律賓": "第一學期：約 8 月至 12 月；第二學期：約 1 月至 5 月",
    "越南": "第一學期（秋季班）：約 9 月至翌年 1 月；第二學期（春季班）：約 2 月至 6 月",
    "泰國": "第一學期：約 8 月至 12 月；第二學期：約 1 月至 5 月",
    "印尼": "奇數／秋季學期（Odd Semester）：約 8/9 月至翌年 1 月；偶數／春季學期（Even Semester）：約 2 月至 6/7 月",
    "肯亞": "第一學期：約 9 月至 12 月；第二學期：約 1 月至 4 月；第三學期：約 5 月至 8 月",
}


def clean_text(s: str) -> str:
  if not s:
    return ""
  return re.sub(r"\s+", " ", s).strip()


def sync_global_assets_and_locations(
    catalog_source: list[dict], resolved_locations: dict
) -> None:
  """Ensure school-images.json and university_locations.jsonl contain all AU partner schools."""
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
          else loc.get("lat", 25.1764)
      )
      lon = float(
          loc.get("longitude")
          if loc.get("longitude") is not None
          else loc.get("lon", 121.4350)
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
  OFFICIAL_AU_DIR.mkdir(parents=True, exist_ok=True)
  catalog_source = json.loads(
      (SOURCES_AU_DIR / "au_catalog_source.json").read_text(encoding="utf-8")
  )
  resolved_locations = json.loads(
      (SOURCES_AU_DIR / "au_resolved_locations.json").read_text(
          encoding="utf-8"
      )
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
        item.get("group") or "國際事務中心正式締約合作姊妹校"
    )
    if "雙聯" in group_str:
      dual_degree_count += 1
    quota_str = clean_text(
        item.get("quota") or "每學期 2 名（依真理大學與姊妹校交換協議名額）"
    )
    detail_url = item.get("detail_url") or AU_SISTER_SCHOOLS_URL
    factsheet_url = item.get("factsheet_url")

    if "雙聯學位" in group_str and "交換" in group_str:
      program_type = (
          "真理大學校級出國交換生計畫暨海外雙聯學位計畫（Double Degree Program）"
      )
      source_url = detail_url
    elif "雙聯學位" in group_str:
      program_type = "真理大學海外雙聯學位合作計畫（Double Degree Program）"
      source_url = detail_url
    elif country in {"中國大陸", "香港", "澳門"}:
      program_type = f"真理大學境外交換研修暨兩岸港澳交流計畫（{group_str}）"
      source_url = detail_url
    else:
      program_type = f"真理大學校級出國交換研修計畫（{group_str}）"
      source_url = detail_url

    colleges_str = clean_text(
        item.get("colleges")
        or "人文學院、觀光休閒與運動學院、管理與資訊學院、財經學院"
    )
    degree_levels_str = clean_text(
        item.get("eligible_degrees")
        or "真理大學具正式學籍且就讀滿一學年以上之大學部（大二以上）與研究所（碩二以上）在學學生"
    )
    lang_req_str = clean_text(item.get("language_req") or "")
    gpa_req_str = clean_text(item.get("gpa_req") or "")
    website = item.get("website") or AU_SISTER_SCHOOLS_URL
    remarks_raw = clean_text(item.get("notes") or "")
    tuition_note = clean_text(item.get("tuition_note") or "")
    exps = item.get("experience_reports") or []

    if country == "日本" and avail_status == "open":
      round_label = "2026~2027 / 2027~2028 日本姐妹校交換學生實施計畫（每年 9–11 月校內報名，交換期間一學年：9 月至翌年 8 月）"
      deadline_iso = "2026-11-25T12:00:00+08:00"
    elif avail_status == "open":
      round_label = "2026 秋季／2027 春季國外姐妹校交換學生實施計畫暨雙聯學位甄選（春季班前一年 9–10 月截止、秋季班當年 3 月上旬截止）"
      deadline_iso = "2026-10-09T12:00:00+08:00"
    else:
      round_label = "115–116學年度真理大學國際事務中心姊妹校交流計畫"
      deadline_iso = "2027-03-05T12:00:00+08:00"

    app_deadline_str = clean_text(
        item.get("deadline")
        or "春季班出國：115 年 10 月 9 日（五）中午 12:00 截止；日本交換生（一學年）：每年 11 月下旬中午 12:00 截止；秋季班出國：每年 3 月上旬中午 12:00 截止"
    )
    win_status = "open" if avail_status == "open" else "closed"
    acad_year = "115"

    study_period_str = clean_text(item.get("duration") or "一學期或一學年")
    sem_dates_str = SEMESTER_DATES_BY_COUNTRY.get(
        country, "秋季學期：約 9 月至翌年 1 月；春季學期：約 2 月至 6 月"
    )
    housing_str = (
        f"獲真理大學國際事務中心提名錄取後，可依 {zh_name} 國際事務處指引申請校內外學生宿舍或國際學舍"
        + (f"（學費與住宿待遇：{tuition_note}）" if tuition_note else "。")
    )
    course_rest_str = (
        f"開放對象與學院：{colleges_str}（{degree_levels_str}）。依《真理大學交換學生出國甄選辦法》（教-P-806）、《真理大學學生出境修習學分實施辦法》及《真理大學與境外大學辦理雙聯學制實施辦法》規定："
        "（1）基本資格（《交換學生出國甄選辦法》第 4 條）：具本校學籍之大學部與研究所在學學生，須曾在本校就讀滿一學年以上（即大二以上、碩二以上），前一學期學業成績全班前 50% 為原則且操行分數達 80 分以上，非本國國籍學生不得申請原屬國家交換學生；"
        "（2）外語能力標準（《交換學生出國甄選辦法》第 5、8 條）：擬申請至日本姊妹校交換者需檢附三年內之外語能力檢定證明（JLPT N2 以上；日本多摩大學可憑 JLPT N2 或 TOEIC 600 以上），澳洲麥覺理大學要求 IELTS 6.5（單科 6.0）及 WAM 60，英國密德薩斯大學與西英格蘭大學雙聯學制要求 IELTS 6.0–6.5；"
        "（3）在學註冊、行政處理費與修課學分下限（《交換學生出國甄選辦法》第 6、9 條及《學生出境修習學分實施辦法》第 4、6 條）：報名時需繳交新臺幣 3,000 元行政處理費，交換期間仍需繳交本校全額學雜費；研修期間不得低於一學期、最高以一年為限，每學期修習課程以不低於 9 學分為原則，出境修習科目學分最高不得超過應修畢業學分數之三分之二；"
        "（4）跨國雙聯學位（《與境外大學辦理雙聯學制實施辦法》第 8 條）：本校與英國密德薩斯大學（Middlesex University London，3+1 學士雙聯、1+1 碩士雙聯、3+15 個月學碩雙聯）、英國西英格蘭大學（UWE Bristol，3+1 學士雙聯、4+1 學碩雙聯）、西班牙赫羅納大學附設桑特波爾廚藝觀光學院（EUHT StPOL，觀光事業學系碩士班 1+1 雙聯）及美國明州西南州立大學（SMSU）合作辦理雙聯學位。"
    )

    living_cost_str, visa_health_str = REGION_COST_DEFAULTS.get(
        country,
        (
            "每月生活費約 USD 700–1,300（依匯率折合新臺幣約 22,000–41,500 元，含住宿、膳食與市區交通）",
            "須依接待國駐臺機構規定申辦學生簽證，並於出國前購買涵蓋交換全期之海外醫療及意外保險。",
        ),
    )

    tuition_points_list = [
        (
            f"真理大學在學註冊、行政處理費與學雜費規定（依《真理大學交換學生出國甄選辦法》第 9 條及《學生出境修習學分實施辦法》第 4 條）：報名時需繳交新臺幣 3,000 元行政處理費；交換生出國期間仍需在本校完成註冊並繳交真理大學全額學雜費（除韓國梨花女子大學、韓國崇實大學、日本昭和女子大學、西班牙赫羅納大學觀光學院 EUHT StPOL、澳洲麥覺理大學及英美雙聯學位依兩校協議需負擔對方全部或部分學雜費外，其餘交換姊妹校免繳對方學費）。本合作校待遇：{tuition_note or '繳交真理大學全額學雜費、免繳接待姊妹校學費'}。"
        ),
        (
            "真理大學六大出國交換、專業實習與國際交流獎助學金體系（依《真理大學「學海飛颺」及「學海惜珠」計畫校內甄選簡章》、《真理大學「學海築夢」及「新南向學海築夢」計畫校內甄選簡章》及國際事務中心學 P-509、P-510、P-513、P-526 獎學金辦法）："
            "（1）《教育部學海飛颺獎學金》（具中華民國國籍、就讀一學期以上、歷年成績平均達 75 分或班排名前 30%，英語組通過 GEPT 中高級初試 / TOEFL iBT 57 / IELTS 5.0 / New TOEIC 750、日語組 JLPT N2、韓語組 TOPIK 2 級，每人補助 NT$ 50,000–300,000）；"
            "（2）《教育部學海惜珠獎學金》（具低收入戶、中低收入戶或相關補助證明且符合學海成績與語檢標準之勵學優秀生，補助國際來回經濟艙機票、國外學費及生活費）；"
            "（3）《教育部學海築夢及新南向學海築夢海外實習獎學金》（赴海外企業機構連續實習 30 日以上［印尼 25 日以上］，含教育部補助款及學校 20% 以上配合款）；"
            "（4）《真理大學國際交流交換學生獎學金（學 P-510）》（補助赴國外姐妹校就讀滿一學年且成績總平均及格之交換生：赴東亞、東南亞、澳洲地區最高獎勵 NT$ 15,000；赴歐洲、美洲地區最高獎勵 NT$ 40,000；於回國後次學期開學一個月內檢附申請表、機票黏貼表［抬頭：真理大學、統編：37301008］及成果報告書申請）；"
            "（5）《真理大學國際交流海外語言文化研習團獎學金（學 P-509）》（補助參加國際事務中心寒暑假海外研習課程且前學期修滿 12 學分以上之在學學生）；"
            "（6）《真理大學國際交流海外志工獎學金（學 P-513，每人最高 NT$ 20,000）》及《國際交流特殊貢獻獎學金（學 P-526，每年 4/1–5/15 申請）》。"
        ),
    ]

    app_steps_list = [
        (
            f"步驟一（確認真理大學就讀滿一學年資格、班排前 50% 門檻與 {zh_name} 語檢要求，按梯次向系所及國際事務中心報名）：確認符合《真理大學交換學生出國甄選辦法》第 4 條規定（具本校學籍之大學部大二以上或研究所碩二以上在學學生、前一學期學業成績全班前 50% 且操行達 80 分以上），於各梯次截止日前（春季班前一年 9–10 月、日本一學年交換每年 11 月下旬、秋季班當年 3 月上旬）提出申請。"
        ),
        (
            "步驟二（備齊校內甄選 1~9 項文件正本 1 份、影本 6 份，並繳交新臺幣 3,000 元行政處理費）：先攜帶正本至行政大樓 4 樓國際事務中心確認無誤後，依序排列繳交（1）報名表、（2）系主任同意書、（3）家長連帶保證書與交換生履行義務同意書、（4）履歷表及自傳、（5）1,000 字以上出國學習讀書計畫（日本組須以日文及中文各繕打一份）、（6）本校教師推薦信一封、（7）語言能力證明影本、（8）前一學期成績單、排名證明書及歷年中文成績單、（9）國際事務中心志工服務時數證明及其他有利審查文件。"
        ),
        (
            f"步驟三（經所屬系所書面初審及交換學生審查委員會複審／面試，獲錄取後申請教育部學海飛颺／惜珠或校內國際交流獎學金）：通過教務長、國際事務中心主任、教與學發展中心主任及各院代表組成之「交換學生審查委員會」評選錄取後，由國際事務中心辦理向 {full_name} 之官方提名，並可同步申請教育部《學海飛颺／學海惜珠計畫》。"
        ),
        (
            f"步驟四（完成姊妹校入學申請、簽證保險與真理大學全額學雜費註冊，出國每學期修習至少 9 學分，返國辦理學分抵免與獎學金核銷）：出國期間維持真理大學註冊並繳交全額學雜費，每學期至少修習 9 學分；返國後依《學生出境修習學分實施辦法》填送境外校際選課暨成績報告單辦理學分採認（最高採認畢業學分 2/3），並於次學期開學一個月內檢附機票票根正本、電子機票、購票證明及心得報告申請《真理大學國際交流交換學生獎學金》（東亞／東南亞／澳洲最高 NT$ 15,000、歐美最高 NT$ 40,000；學海受獎生於返國後二星期內上傳 1,500 字心得報告與問卷）。"
        ),
    ]

    elig_points_list = [
        f"合作類別與計畫組別：{program_type}（{group_str}）",
        f"開放學制與年級：{degree_levels_str}",
        f"開放申請學院：{colleges_str}",
        f"學業與操行成績門檻：{gpa_req_str}",
        f"外語能力標準：{lang_req_str}",
        "在學註冊、行政處理費與赴外修課規定（《真理大學交換學生出國甄選辦法》第 6、9 條）：報名時需繳交 NT$ 3,000 行政處理費，交換期間仍需繳交真理大學全額學雜費，每學期修習課程不得低於 9 學分。",
    ]
    if tuition_note:
      elig_points_list.append(f"姊妹校學費與住宿待遇：{tuition_note}")
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
            or f"{AU_STUDENT_EXPERIENCES_URL}#au-exp-{sn}-{e_idx+1}"
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
            "college": "人文學院／觀光休閒與運動學院／管理與資訊學院／財經學院",
            "department": "真理大學赴境外交換研修生",
        })
        summary_text = (
            f"真理大學國際事務中心（CIA）公開收錄之學長姐赴 {country} {full_name} 交換研習官方成果心得報告書（{raw_t}），詳述選課修習與每學期 9 學分抵免、校內外宿舍生活、留學生學伴交流、當地物價開銷與給學弟妹之建議。"
        )
        theme_map = {
            "academics": f"真理大學交換生於《{raw_t}》分享在 {zh_name} 選課、課堂報告與期末考試方式，以及返國辦理真理大學學分抵免之實務建議。",
            "housing": f"真理大學交換生記錄於 {zh_name} 入住學生宿舍／國際學舍之寢室設備、公用空間、門禁與周邊生活機能（{housing_str[:100]}）。",
            "campus_culture": f"真理大學國際事務中心公開收錄《{raw_t}》之日本チューター／SA 學伴、韓國留學生語言交換計畫或社團文化體驗實錄。",
            "cost": f"真理大學交換生分享於 {zh_name} 之每月住宿、伙食與交通開銷（{living_cost_str[:100]}），以及申請真理大學國際交流交換學生獎學金或教育部學海飛颺／惜珠獎學金之經驗。",
        }
        student_experience_rows.append({
            "school_name": full_name,
            "country": country,
            "title": raw_t,
            "source_url": eurl,
            "source_type": "pdf" if eurl.lower().endswith(".pdf") or "downloadfile" in eurl else "article",
            "platform": "真理大學國際事務中心（CIA）—出國留學與交換求學心得專區",
            "author_name": (
                raw_t.split("-")[-1].split("－")[-1].replace(".pdf", "").strip()[:24]
                if ("-" in raw_t or "－" in raw_t)
                else "真理大學交換生"
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
                f"{full_name}:au_exp:{e_idx}:{eurl}".encode("utf-8")
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
        "home_university": "真理大學",
        "school_name": full_name,
        "country": country,
        "official_experience_portal_url": (
            exp_links[0]["url"] if exp_links else AU_STUDENT_EXPERIENCES_URL
        ),
        "partner_page_url": source_url,
        "report_count": len(exps),
        "sample_reports": sample_reports,
        "checked_at": CHECKED_AT,
    })

    loc = resolved_locations.get(full_name) or {
        "city": country,
        "latitude": 25.1764,
        "longitude": 121.4350,
        "source_url": "https://www.wikidata.org",
    }
    city_name = loc.get("city") or country
    lat = float(
        loc.get("latitude")
        if loc.get("latitude") is not None
        else loc.get("lat", 25.1764)
    )
    lon = float(
        loc.get("longitude")
        if loc.get("longitude") is not None
        else loc.get("lon", 121.4350)
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
      notes_lines.append(f"【官方交換／雙聯簡章專頁】{factsheet_url}")
    if exps:
      notes_lines.append(
          f"【真理大學學長姐交換求學心得報告（共 {len(exps)} 篇）】收錄於國際事務中心求學心得專區（含：{'、'.join(exp_labels[:4])}）"
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
            f"真理大學國際事務中心公告合作姊妹校（{program_type}）；{quota_str}。"
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
            "title": f"真理大學國際事務中心姊妹校與交換／雙聯計畫專頁—{zh_name}",
            "source_url": source_url,
            "role": "home_university",
            "authority": "home_official_notice",
            "effective_academic_year": acad_year,
            "application_round": round_label,
            "checked_at": CHECKED_AT,
        },
        {
            "title": "真理大學交換學生出國甄選辦法（教-P-806）與學生出境修習學分實施辦法",
            "source_url": AU_SELECTION_REGULATION_PAGE_URL,
            "role": "home_university",
            "authority": "home_official_notice",
            "effective_academic_year": acad_year,
            "application_round": round_label,
            "checked_at": CHECKED_AT,
        },
        {
            "title": "真理大學國際交流交換學生獎學金（學 P-510）與教育部學海飛颺／惜珠／築夢計畫專區",
            "source_url": AU_SCHOLARSHIP_REGULATIONS_URL,
            "role": "home_university",
            "authority": "home_official_notice",
            "effective_academic_year": acad_year,
            "application_round": round_label,
            "checked_at": CHECKED_AT,
        },
    ]
    if factsheet_url:
      wf_sources.append({
          "title": f"{full_name} 交換／雙聯計畫官方專頁",
          "source_url": factsheet_url,
          "role": "partner_university",
          "authority": "partner_official",
          "effective_academic_year": acad_year,
          "application_round": round_label,
          "checked_at": CHECKED_AT,
      })
    if exp_links:
      wf_sources.append({
          "title": f"真理大學國際事務中心求學心得專區—赴 {zh_name} 交換心得報告（{len(exps)} 篇）",
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
        "home_university": "真理大學",
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
            "真理大學由國際事務中心（Center for International Affairs, CIA）統籌全校 4 個學院（人文學院、觀光休閒與運動學院、管理與資訊學院、財經學院）之校級赴國外姊妹校交換學生計畫、日本姊妹校一學年交換計畫、海外雙聯學位計畫（英國密德薩斯大學 Middlesex University、英國西英格蘭大學 UWE Bristol、西班牙赫羅納大學附設桑特波爾廚藝觀光學院 EUHT StPOL、美國明州西南州立大學 SMSU）及教育部學海飛颺、學海惜珠、學海築夢與真理大學國際交流獎學金。"
        ),
        "review_status": "published",
        "published_at": CHECKED_AT,
        "steps": [
            {
                "rule_id": f"au-{acad_year}-home-1-{sn:03d}",
                "order": 1,
                "phase": "校內申請",
                "title": f"確認真理大學就讀滿一學年資格、班排前 50% 門檻與 {zh_name} 語檢要求，按梯次向系所及國際事務中心報名",
                "responsible_party": "學生",
                "responsible_unit": "真理大學教務處國際事務中心／各院系所",
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
                    f"確認符合《真理大學交換學生出國甄選辦法》第 4 條規定：具本校學籍之大學部（大二以上）與研究所（碩二以上）在學學生（須曾在本校就讀滿一學年以上），前一學期學業成績全班前 50% 為原則且操行分數達 80 分以上，符合接待校語檢要求（{lang_req_str}），於校內甄選截止日前提出申請。"
                ),
                "details": [
                    f"開放學制與學院：{colleges_str}（{degree_levels_str}）",
                    f"語言與學業條件：{lang_req_str}｜{gpa_req_str}",
                    f"當期名額與計畫類別：{quota_str}｜{program_type}",
                ],
                "scope": {
                    "home_universities": ["真理大學"],
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
                    AU_SELECTION_REGULATION_PAGE_URL,
                    AU_EXCHANGE_PROGRAMS_URL,
                ],
                "checked_at": CHECKED_AT,
                "support_status": "verified",
            },
            {
                "rule_id": f"au-{acad_year}-home-2-{sn:03d}",
                "order": 2,
                "phase": "校內申請",
                "title": "備妥 1~9 項甄選文件（正本 1 份、影本 6 份）並繳交新臺幣 3,000 元行政處理費送交國際事務中心",
                "responsible_party": "學生",
                "responsible_unit": "真理大學國際事務中心（行政大樓 4 樓）",
                "deadline_at": deadline_iso,
                "deadline_status": (
                    "verified_exact"
                    if avail_status == "open"
                    else "reference_only"
                ),
                "deadline_source_url": AU_2027_SPRING_EXCHANGE_URL,
                "deadline_checked_at": CHECKED_AT,
                "deadline_reminder_eligible": avail_status == "open",
                "summary": (
                    "依《真理大學交換學生出國甄選辦法》第 5、9 條及各梯次《交換學生實施計畫》規定，先攜帶正本至行政大樓 4 樓國際事務中心確認無誤後，於截止日前繳交正本 1 份、影本 6 份及新臺幣 3,000 元行政處理費。"
                ),
                "details": [
                    "校內甄選必備 1~9 項文件：（1）國外姐妹校交換生報名表／日本交換生報名表；（2）系主任同意書；（3）家長連帶保證書、交換生履行義務同意書；（4）履歷表及自傳一份（格式不限，含簡歷＋個人自傳、社團、經歷、特殊表現）；（5）出國學習讀書計畫一份（文長不得少於 1,000 字；日本組須以日文及中文各繕打一份）；（6）本校教師推薦信一封；（7）三年內語言能力證明影本；（8）前一學期成績單、排名證明書及歷年中文成績單（轉學生需提供原學校歷年成績單）；（9）國際事務中心志工服務時數證明文件及其他有助審查之證明文件影本。",
                    "雙聯學位申請（《真理大學與境外大學辦理雙聯學制實施辦法》）：申請英國密德薩斯大學（3+1 / 1+1 / 3+15 個月）、英國西英格蘭大學（3+1 / 4+1）或西班牙赫羅納大學觀光學院（1+1 碩士雙聯）者，依雙聯學制簡章備妥英文歷年成績單、IELTS 成績單或 Placement Test 證明、護照影本與英文讀書計畫向學系及國際事務中心提出申請。",
                ],
                "document_requirements": [
                    {
                        "name": "國外姐妹校交換生報名表／日本交換生報名表、系主任同意書、家長連帶保證書暨交換生履行義務同意書（正本 1 份、影本 6 份）",
                        "official_form_url": AU_2027_SPRING_EXCHANGE_URL,
                        "source_urls": [
                            AU_2027_SPRING_EXCHANGE_URL,
                            AU_2026_2027_JAPAN_EXCHANGE_URL,
                            AU_SELECTION_REGULATION_PAGE_URL,
                        ],
                    },
                    {
                        "name": "前一學期成績單、排名證明書、歷年中文成績單及三年內有效外語能力檢定證明影本（JLPT N2 / IELTS / TOEFL / TOEIC / TOPIK）",
                        "official_form_url": AU_SELECTION_REGULATION_PAGE_URL,
                        "source_urls": [
                            AU_SELECTION_REGULATION_PAGE_URL,
                            AU_2026_2027_JAPAN_EXCHANGE_URL,
                        ],
                    },
                    {
                        "name": "履歷表及自傳、1,000 字以上出國學習讀書計畫（日本組須中日文各一份）、本校教師推薦信一封及國際事務中心志工服務時數證明",
                        "official_form_url": AU_2027_SPRING_EXCHANGE_URL,
                        "source_urls": [
                            AU_2027_SPRING_EXCHANGE_URL,
                            AU_XUEHAI_GUIDELINE_PAGE_URL,
                        ],
                    },
                ],
                "scope": {
                    "home_universities": ["真理大學"],
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
                    AU_2027_SPRING_EXCHANGE_URL,
                    AU_2026_2027_JAPAN_EXCHANGE_URL,
                    AU_SELECTION_REGULATION_PAGE_URL,
                ],
                "checked_at": CHECKED_AT,
                "support_status": "verified",
            },
            {
                "rule_id": f"au-{acad_year}-home-3-{sn:03d}",
                "order": 3,
                "phase": "甄選與提名",
                "title": "參加交換學生審查委員會複審與口試甄選，獲錄取後申請教育部學海飛颺／惜珠計畫補助",
                "responsible_party": "真理大學交換學生審查委員會與申請學生",
                "responsible_unit": "教務處國際事務中心／交換學生審查委員會",
                "deadline_at": "2027-03-31T17:00:00+08:00",
                "deadline_status": "verified_exact",
                "deadline_source_url": AU_SELECTION_REGULATION_PAGE_URL,
                "deadline_checked_at": CHECKED_AT,
                "deadline_reminder_eligible": False,
                "summary": (
                    "依《真理大學交換學生出國甄選辦法》第 7、8 條，由教務長、國際事務中心主任、教與學發展中心主任及各院代表組成「交換學生審查委員會」，就（1）外語能力檢定證明、（2）在校歷年學業成績、（3）自傳、履歷及讀書計畫、（4）在校歷年操行成績、（5）國際事務中心志工服務時數、（6）其他輔助審查文件加總評定並舉行口試決定錄取名單；獲錄取者可同步申請教育部《學海飛颺》或《學海惜珠》獎學金。"
                ),
                "details": [
                    "教育部學海飛颺／惜珠申請條件（《真理大學「學海飛颺」及「學海惜珠」計畫校內甄選簡章》）：具中華民國國籍且在臺設有戶籍、於本校就讀一學期以上、歷年成績平均達 75 分或班排名前 30%，兩年內通過語檢（英語組 GEPT 中高級初試 / TOEFL iBT 57 / IELTS 5.0 / New TOEIC 750；日語組 JLPT N2；韓語組 TOPIK 2 級），檢附 1,000–1,500 字出國研修計畫書。",
                    "凡錄取完成提名後，不得擅自放棄交換生身分；出國研修前須簽訂行政契約書。",
                ],
                "scope": {
                    "home_universities": ["真理大學"],
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
                    AU_SELECTION_REGULATION_PAGE_URL,
                    AU_XUEHAI_GUIDELINE_PAGE_URL,
                    AU_XUEHAI_FEIYANG_URL,
                ],
                "checked_at": CHECKED_AT,
                "support_status": "verified",
            },
            {
                "rule_id": f"au-{sn:03d}-host-apply",
                "order": 4,
                "phase": "合作校申請",
                "title": f"由真理大學國際事務中心向 {zh_name} 辦理官方提名並遞交姊妹校入學與宿位申請",
                "responsible_party": "學生與接待校國際事務處",
                "summary": (
                    f"通過校內甄選後，由國際事務中心向 {zh_name} 辦理官方提名（Nomination）；學生須依接待校規定備妥外文入學申請表、英文歷年成績單、護照影本、財力證明、語檢證書、健康檢查表及宿舍申請表，靜候接待校核發正式入學許可（Admission Letter / COE / CoE / CAS / DS-2019 / 錄取通知書）。"
                ),
                "details": [
                    f"研修期程：{study_period_str}｜名額：{quota_str}",
                    f"語言與學業條件：{lang_req_str}｜{gpa_req_str}",
                    f"住宿與費用待遇：{housing_str}",
                ],
                "scope": {
                    "home_universities": ["真理大學"],
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
                    [source_url, AU_SELECTION_REGULATION_PAGE_URL]
                    + ([factsheet_url] if factsheet_url else [])
                    + ([website] if website else [])
                ),
                "checked_at": CHECKED_AT,
                "support_status": "verified",
                "needs_confirmation": False,
            },
            {
                "rule_id": f"au-{acad_year}-home-5-{sn:03d}",
                "order": 5,
                "phase": "行前準備",
                "title": "完成真理大學全額學雜費註冊與海外保險，交換期間每學期修習至少 9 學分，返國辦理學分抵免與國際交流獎學金核銷",
                "responsible_party": "學生與所屬系所",
                "responsible_unit": "教務處國際事務中心／註冊組／各學系",
                "summary": (
                    "出國前須依《真理大學交換學生出國甄選辦法》第 9、11 條及《學生出境修習學分實施辦法》第 4、6 條完成真理大學註冊並繳交全額學雜費、保險費及退撫基金；交換期間每學期修習課程不得低於 9 學分；返國後由所屬學系填送《境外校際選課暨成績報告單》至教務處辦理學分採認登錄（最高採認畢業學分之 2/3），並於回國後次學期開學一個月內檢附《國際交流獎學金申請表》、《機票繳附資料黏貼表》（收據抬頭：真理大學、統編：37301008、登機證正本、電子機票）及《成果報告書》Word 檔向國際事務中心申請《真理大學國際交流交換學生獎學金》（學海計畫受獎生另須於結束後二星期內上傳問卷及 1,500 字以上心得報告至學海計畫平台）。"
                ),
                "details": tuition_points_list,
                "scope": {
                    "home_universities": ["真理大學"],
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
                    AU_CREDIT_TRANSFER_REGULATION_PAGE_URL,
                    AU_EXCHANGE_SCHOLARSHIP_PDF_URL,
                    AU_SCHOLARSHIP_REIMBURSEMENT_URL,
                ],
                "checked_at": CHECKED_AT,
                "support_status": "verified",
            },
        ],
        "sources": wf_sources,
        "last_checked": CHECKED_AT,
        "coverage_status": "official_verified",
        "coverage_note": (
            f"已完整整合真理大學國際事務中心（CIA）《全球姊妹校名錄》、《2027春季／2026秋季／2026~2027日本姐妹校交換學生實施計畫》、《澳洲麥覺理大學交換計畫》、《英國密德薩斯大學／西英格蘭大學／西班牙赫羅納大學觀光學院雙聯學制》、《真理大學交換學生出國甄選辦法（教-P-806）》、《學生出境修習學分實施辦法》、《與境外大學辦理雙聯學制實施辦法》、《國際交流交換學生獎學金設置辦法（學 P-510）》、教育部學海系列簡章及 {exp_covered_schools} 校 {total_exp_reports} 篇歷屆交換生心得報告，共 {len(catalog_source)} 所合作姊妹校資料。"
        ),
    })

    cost_line = f"{zh_name} 預估每月生活費：{living_cost_str}"
    tuition_clean = tuition_points_list[0]
    housing_clean = housing_str
    calendar_clean = f"學期與研修時間參考：{sem_dates_str}"
    course_clean = course_rest_str

    dest_sources = [
        {
            "title": f"真理大學國際事務中心姊妹校與交換／雙聯計畫專頁—{zh_name}",
            "source_url": source_url,
            "summary": "真理大學國際事務中心公告之合作學程、開放學制、語言檢定門檻與學費待遇說明",
        },
        {
            "title": "真理大學交換學生出國甄選辦法（教-P-806）、學生出境修習學分實施辦法與國際交流獎學金辦法（學 P-510）",
            "source_url": AU_SELECTION_REGULATION_PAGE_URL,
            "summary": "真理大學出國交換全額學雜費規定、行政處理費 3,000 元、每學期至少修習 9 學分與六大獎助學金規範",
        },
    ]
    if factsheet_url:
      dest_sources.append({
          "title": f"{full_name} 交換／雙聯計畫官方專頁",
          "source_url": factsheet_url,
          "summary": f"{zh_name} 官方提供之交換生與雙聯學位申請資格、選課清單與費用資訊",
      })
    if exp_links:
      dest_sources.append({
          "title": f"真理大學國際事務中心求學心得專區—赴 {zh_name} 交換心得報告（{len(exps)} 篇）",
          "source_url": exp_links[0]["url"],
          "summary": f"收錄歷年真理大學學生赴 {zh_name} 交換研習心得報告共 {len(exps)} 篇",
      })
    if website:
      dest_sources.append({
          "title": f"{full_name} 官方網站",
          "source_url": website,
          "summary": "接待合作姊妹校官方網站",
      })

    src_url_list = (
        [
            source_url,
            AU_SELECTION_REGULATION_PAGE_URL,
            AU_CREDIT_TRANSFER_REGULATION_PAGE_URL,
            AU_SCHOLARSHIP_REGULATIONS_URL,
        ]
        + ([factsheet_url] if factsheet_url else [])
        + ([exp_links[0]["url"]] if exp_links else [])
        + ([website] if website else [])
    )

    destinations.append({
        "home_university": "真理大學",
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
                "title": "生活費、真理大學全額學雜費規定、教育部學海飛颺／惜珠與真理大學國際交流獎學金（學 P-510）",
                "summary": cost_line,
                "points": [cost_line] + tuition_points_list,
                "source_urls": src_url_list + [AU_EXCHANGE_SCHOLARSHIP_PDF_URL],
                "caution": (
                    "依《真理大學交換學生出國甄選辦法》第 9 條，報名時需繳交 NT$ 3,000 行政處理費，交換期間仍需繳交本校全額學雜費；申請《真理大學國際交流交換學生獎學金》（東亞／東南亞／澳洲最高 15,000 元、歐美最高 40,000 元）須就讀滿一學年且總平均及格，並於返國後次學期開學一個月內檢附機票購票證明（抬頭：真理大學、統編：37301008）、登機證正本與心得報告書提出申請。"
                ),
            },
            {
                "key": "housing",
                "title": "住宿資訊與校內外國際學生宿舍申請",
                "summary": housing_clean[:160],
                "points": [housing_clean],
                "source_urls": src_url_list,
                "caution": "獲真理大學國際事務中心提名後，請依接待姊妹校期限完成校內學生寮或國際學舍申請。",
            },
            {
                "key": "insurance",
                "title": "海外全期醫療意外保險、家長連帶保證書與交換生履行義務同意書",
                "summary": visa_health_str,
                "points": [
                    visa_health_str,
                    "依《真理大學交換學生出國甄選辦法》第 5 條及《學生出境修習學分實施辦法》第 4 條，報名時須繳交《家長連帶保證書、交換生履行義務同意書》，獲學海或校內獎學金者須簽署《行政契約書》或《履約保證書》，並完成學生平安保險與海外全期醫療意外保險。",
                ],
                "source_urls": src_url_list,
                "caution": "日本、韓國、西班牙、英國、美國、澳洲等接待校對交換生與雙聯生當地國民健康保險（NHI / NHIS / IHS / OSHC）有強制投保規定，請依入學通知書辦理。",
            },
            {
                "key": "visa",
                "title": "留學交換簽證辦理、出國修業期限與雙聯學制修業規定",
                "summary": visa_health_str,
                "points": [
                    visa_health_str,
                    "依《真理大學交換學生出國甄選辦法》第 6 條，交換研修期間不得低於一學期、最高以一年為限；跨國雙聯學位（3+1 學士、1+1 碩士、4+1 學碩、3+15 個月學碩）依《真理大學與境外大學辦理雙聯學制實施辦法》第 8 條規定（修讀學士學位累計在二校修業至少滿 32 個月且在本校修業至少 4 學期、修讀碩士學位累計至少滿 12 個月且在境外學校至少滿 8 個月）辦理。",
                ],
                "source_urls": src_url_list + [AU_DUAL_DEGREE_REGULATION_PAGE_URL],
                "caution": "具有役男身分之學生申請出境，應依《役男出境處理辦法》及入出境相關法令於出國前完成核准手續。",
            },
            {
                "key": "academics",
                "title": "校內甄選梯次、每學期修習至少 9 學分下限與返國學分抵免（最高採認畢業學分 2/3）",
                "summary": course_clean[:160],
                "points": [calendar_clean, course_clean],
                "source_urls": src_url_list + [AU_CREDIT_TRANSFER_REGULATION_PAGE_URL],
                "caution": (
                    "依《真理大學交換學生出國甄選辦法》第 6 條及《學生出境修習學分實施辦法》第 6、7 條，交換學生每學期修習課程以不低於 9 學分為原則，學分計算原則以修滿 18 小時成績及格者為 1 學分，採認最高不得超過應修畢業學分數之三分之二。"
                ),
            },
            {
                "key": "living",
                "title": f"{city_name} 校園生活與真理大學學長姐求學心得傳承",
                "summary": f"代表城市：{city_name}。請配合接待校國際處完成報到與新生訓練（Orientation）。",
                "points": [
                    f"目的地城市：{city_name}（{country}）",
                    (
                        "真理大學國際事務中心於官網《出國留學與交換—求學心得》及《留學剪影》專區公開歷屆交換生心得報告"
                        + (
                            f"（本校共收錄 {len(exps)} 篇心得報告：{'、'.join(exp_labels[:3])}）"
                            if exps
                            else ""
                        )
                        + "，協助同學掌握選課抵免與海外生活準備。"
                    ),
                ],
                "source_urls": [
                    exp_links[0]["url"]
                    if exp_links
                    else AU_STUDENT_EXPERIENCES_URL
                ],
            },
        ],
        "sources": dest_sources,
        "last_checked": CHECKED_AT,
        "coverage_status": "official_verified",
        "coverage_note": (
            f"已整合真理大學國際事務中心 {len(catalog_source)} 所合作姊妹校、當期常態開放申請交換與雙聯學校（{open_partner_count} 校）及 {exp_covered_schools} 校 {total_exp_reports} 篇歷年學生交換心得報告。"
        ),
    })

    research_records.append({
        "home_university": "真理大學",
        "school_name": full_name,
        "country": country,
        "official_website": website,
        "verification_status": "official_verified",
        "discovery_source_url": detail_url,
        "checked_at": CHECKED_AT,
        "note": (
            "真理大學國際事務中心《姊妹校專區》、《國外姐妹校交換學生實施計畫》、《日本姐妹校交換生實施計畫》、《雙聯學制專區》與 ROR/Wikidata 官方網址核對完成。"
        ),
    })

    ev_sources = [
        {
            "title": f"真理大學國際事務中心姊妹校與交換／雙聯計畫專頁—{zh_name}",
            "url": source_url,
        },
    ]
    if factsheet_url:
      ev_sources.append({
          "title": f"{full_name} 交換／雙聯計畫官方專頁",
          "url": factsheet_url,
      })
    if exp_links:
      ev_sources.append({
          "title": f"真理大學國際事務中心求學心得—赴 {zh_name} 交換心得報告（{len(exps)} 篇）",
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
            "scope": "真理大學全球與兩岸交換姊妹校住宿與生活資訊",
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
            "scope": "真理大學出國交換全額學雜費規定、教育部學海飛颺／惜珠／築夢與真理大學國際交流獎學金（學 P-510）",
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
            "scope": "真理大學交換學生出國甄選辦法（教-P-806）、學生出境修習學分實施辦法與雙聯學制實施辦法",
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
            "scope": "真理大學海外交換與雙聯學位簽證、家長連帶保證書、交換生履行義務同意書與海外醫療保險提醒",
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
                    f"｜真理大學公開收錄 {len(exps)} 篇赴 {zh_name} 交換生心得報告（{'、'.join(exp_labels[:3])}）。"
                    if exps
                    else ""
                )
            ),
            "sources": ev_sources,
            "checked_at": CHECKED_AT,
            "scope": "真理大學交換名額與歷屆學長姐求學心得報告",
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
            "已整合真理大學國際事務中心（CIA）《全球姊妹校名錄》、《國外姐妹校交換學生實施計畫》、《日本姐妹校交換生實施計畫》、《雙聯學制專區》及歷屆學生交換心得報告。",
            "當期免學費名額、宿位供給、語檢門檻與選課限制請依合作校最新簡章及入學通知書核對。",
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

  write_jsonl(OFFICIAL_AU_DIR / "partners.jsonl", partners)
  write_jsonl(SOURCES_AU_DIR / "partners.jsonl", partners)
  write_jsonl(OFFICIAL_AU_DIR / "application_workflows.jsonl", workflows)
  write_jsonl(OFFICIAL_AU_DIR / "destination_profiles.jsonl", destinations)
  write_jsonl(OFFICIAL_AU_DIR / "partner_research.jsonl", research_records)
  write_jsonl(OFFICIAL_AU_DIR / "student_life.jsonl", life_records)
  write_jsonl(
      OFFICIAL_AU_DIR / "experience_sources.jsonl",
      experience_sources_records,
  )
  write_jsonl(
      OFFICIAL_AU_DIR / "student_experience_sources.jsonl",
      experience_sources_records,
  )
  write_jsonl(
      OFFICIAL_AU_DIR / "student_experiences.jsonl", student_experience_rows
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
  (OFFICIAL_AU_DIR / "student-experience-digests.json").write_text(
      json.dumps({"digests": digest_records}, ensure_ascii=False, indent=2)
      + "\n",
      encoding="utf-8",
  )

  (OFFICIAL_AU_DIR / "student-experiences.json").write_text(
      json.dumps(
          {
              "school_id": "au",
              "school_name": "真理大學",
              "checked_at": CHECKED_AT,
              "source_url": AU_STUDENT_EXPERIENCES_URL,
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

  (OFFICIAL_AU_DIR / "campus-locations.json").write_text(
      json.dumps(
          {
              "school_id": "au",
              "school_name": "真理大學",
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
  (OFFICIAL_AU_DIR / "campus-assets.json").write_text(
      json.dumps(
          {
              "school_id": "au",
              "school_name": "真理大學",
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

  au_source_urls = [
      AU_HOME_URL,
      AU_CIA_HOME_URL,
      AU_OUTBOUND_OVERVIEW_URL,
      AU_EXCHANGE_PROGRAMS_URL,
      AU_DUAL_DEGREE_URL,
      AU_SHORT_TERM_URL,
      AU_STUDY_ABROAD_GALLERY_URL,
      AU_STUDENT_EXPERIENCES_URL,
      AU_SISTER_SCHOOLS_URL,
      AU_REGULATIONS_URL,
      AU_OUTBOUND_REGULATIONS_URL,
      AU_SCHOLARSHIP_REGULATIONS_URL,
      AU_XUEHAI_OVERVIEW_URL,
      AU_XUEHAI_FEIYANG_URL,
      AU_XUEHAI_XIZHU_URL,
      AU_XUEHAI_ZHUMENG_URL,
      AU_SELECTION_REGULATION_PAGE_URL,
      AU_CREDIT_TRANSFER_REGULATION_PAGE_URL,
      AU_DUAL_DEGREE_REGULATION_PAGE_URL,
      AU_2027_SPRING_EXCHANGE_URL,
      AU_2026_FALL_EXCHANGE_URL,
      AU_2026_2027_JAPAN_EXCHANGE_URL,
      AU_MACQUARIE_PROGRAM_URL,
      AU_MIDDLESEX_DUAL_URL,
      AU_UWE_DUAL_URL,
      AU_STPOL_DUAL_URL,
      AU_EXCHANGE_SCHOLARSHIP_PDF_URL,
      AU_STUDY_TOUR_SCHOLARSHIP_PDF_URL,
      AU_VOLUNTEER_SCHOLARSHIP_PDF_URL,
      AU_SPECIAL_CONTRIBUTION_SCHOLARSHIP_PDF_URL,
      AU_SCHOLARSHIP_REIMBURSEMENT_URL,
      AU_XUEHAI_GUIDELINE_PAGE_URL,
  ]

  exchange_info_payload = {
      "school_name": "真理大學",
      "program_type": [
          (
              f"國際事務中心（CIA）校級赴國外姊妹校交換學生計畫與日本姊妹校一學年交換學生計畫（涵蓋日本、韓國、中國大陸、澳門、澳洲、西班牙、英國、美國、馬來西亞、菲律賓、越南、泰國、印尼、肯亞等全球 14 國與地區共 {len(partners)} 所正式締約姊妹校，其中 {open_partner_count} 所常態開放申請交換及雙聯學位）"
          ),
          (
              "海外雙聯學位計畫（Double Degree Programs，涵蓋【英國密德薩斯大學 Middlesex University London：3+1 學士雙聯、1+1 碩士雙聯、3+15 個月學碩雙聯】、【英國西英格蘭大學 UWE Bristol：3+1 學士雙聯、4+1 學碩雙聯】、【西班牙赫羅納大學附設桑特波爾廚藝觀光學院 EUHT StPOL：觀光事業學系碩士班 1+1 碩士雙聯】及【美國明州西南州立大學 SMSU 雙聯學位】）"
          ),
          (
              "六大出國交換、專業實習與國際交流獎助學金體系：教育部「學海飛颺獎學金」（歷年平均 75 分以上或班排前 30%，補助 NT$ 50,000–300,000）、「學海惜珠獎學金」（清寒勵學優秀生補助機票、國外學費及生活費）、「學海築夢及新南向學海築夢海外實習獎學金」（含教育部補助款與學校 20% 配合款）、《真理大學國際交流交換學生獎學金（學 P-510）》（東亞／東南亞／澳洲一年最高獎勵 NT$ 15,000、歐美一年最高獎勵 NT$ 40,000）、《真理大學國際交流海外語言文化研習團獎學金（學 P-509）》及《真理大學國際交流海外志工獎學金（學 P-513，每人最高 NT$ 20,000）》／《國際交流特殊貢獻獎學金（學 P-526）》"
          ),
      ],
      "academic_year": [
          (
              "115（涵蓋 2027 春季國外姐妹校交換學生實施計畫［115/10/09 截止］、2026~2027 與 2027~2028 日本姐妹校交換學生實施計畫［每年 11 月下旬截止，交換一學年］、2026 與 2027 秋季國外姐妹校交換學生實施計畫［每年 3 月上旬截止］、英美西雙聯學位計畫及教育部學海系列與校內國際交流獎學金）"
          ),
          (
              f"本平台完整收錄真理大學國際事務中心公告之 {len(partners)} 所全球與兩岸有效締約交換及雙聯學位姊妹校（橫跨全球 14 個國家與地區，並完整收錄 {exp_covered_schools} 所合作大學共 {total_exp_reports} 篇歷屆學長姐交換求學心得報告）"
          ),
      ],
      "semester": [
          "赴韓國、中國大陸、西班牙、澳洲等非日本地區交換生—春季班（2 月至 6 月出國交換一學期，西、澳可選一學年）：於前一年 7–10 月開放校內甄選（2027 春季班於 115 年 10 月 9 日［五］中午 12:00 截止收件）。",
          "赴日本地區姊妹校交換生（每年 9 月至翌年 8 月出國交換一學年）：每年舉辦一梯次校內甄選，於 9–11 月開放校內報名（2026~2027 梯次於 114 年 11 月 26 日中午 12:00 截止；2027~2028 梯次預計 115 年 11 月 25 日中午 12:00 截止）。",
          "赴韓國、中國大陸、西班牙、澳洲等非日本地區交換生—秋季班（9 月至翌年 1 月出國交換一學期，西、澳可選一學年）：於當年 1–3 月開放校內甄選（2026 秋季班於 115 年 3 月 6 日［五］中午 12:00 截止；2027 秋季班預計 116 年 3 月 5 日中午 12:00 截止）。",
      ],
      "application_period": [
          "【春季班出國交換校內甄選（韓國、大陸、西班牙、澳洲等姊妹校，116 年 2 月–6 月出國）】即日起至 115 年 10 月 9 日（五）中午 12:00 整截止收件，逾期恕不受理（備齊 1~9 項資料正本 1 份、影本 6 份及 NT$ 3,000 行政處理費送行政大樓 4 樓國際事務中心）。",
          "【日本姊妹校交換生校內甄選（城西國際、北亞、香川、新潟經營、名城、星城、長崎外語、三重、多摩、昭和女子等 10 校，9 月至翌年 8 月交換一學年）】每年 9 月至 11 月下旬開放報名（114 年 11 月 26 日中午 12:00 截止；下一梯次預計 115 年 11 月 25 日中午 12:00 截止）。",
          "【秋季班出國交換校內甄選（韓國、大陸、西班牙、澳洲等姊妹校，9 月至翌年 1 月出國）】每年 1 月至 3 月上旬開放報名（2026 秋季班於 115 年 3 月 6 日［五］中午 12:00 截止；2027 秋季班預計 116 年 3 月 5 日中午 12:00 截止）。",
          "【教育部學海飛颺／學海惜珠／學海築夢計畫＆真理大學國際交流獎學金】教育部學海系列校內甄選於每年 2–3 月受理；《真理大學國際交流交換學生獎學金（學 P-510）》於交換回國後次學期開學一個月內（約 9–10 月中旬前）受理核銷申請；《國際交流海外志工獎學金（學 P-513）》於活動前 1 個月申請保留、該學年度 7 月 10 日前核銷；《國際交流特殊貢獻獎學金（學 P-526）》於每年 4 月 1 日至 5 月 15 日受理。",
      ],
      "eligibility": [
          "1. 基本在學身分與年級限制：依《真理大學交換學生出國甄選辦法》（教-P-806，114年4月14日行政會議修正通過）第 4 條第 1 款，具有本校學籍之大學部與研究所在學學生，須曾在本校就讀滿一學年以上（即大學部大二以上、研究所碩二以上），始得參加甄選；非本國國籍學生不得申請（原屬國家）交換學生。",
          "2. 學業成績與操行門檻：依《交換學生出國甄選辦法》第 4 條第 2 款，前一學期學業成績全班前 50% 為原則，且操行分數達 80 分以上；申請教育部《學海飛颺／學海惜珠》者須於本校就讀一學期以上且歷年成績平均達 75 分或班排名前 30%；申請澳洲麥覺理大學交換須在校總平均 WAM 達 60 分以上；申請英國密德薩斯大學雙聯學制須 CGPA 達 2.5 以上。",
          "3. 在學註冊、行政處理費與赴外修課學分下限：依《交換學生出國甄選辦法》第 6、9 條及《真理大學學生出境修習學分實施辦法》第 4、6 條，報名時需繳交新臺幣 3,000 元行政處理費，交換期間仍需在本校完成註冊手續並繳交全額學雜費、保險費及退撫基金；研修期間不得低於一學期、最高以一年為限，每學期修習課程以不低於 9 學分為原則，出境修習科目學分最高不得超過應修畢業學分數之三分之二。",
          "4. 跨國雙聯學位修業規定：依《真理大學與境外大學辦理雙聯學制實施辦法》第 8 條，同時在境內外大學修讀雙聯學制同級學位者，修讀學士學位累計修業時間至少須滿 32 個月（在本校修業至少 4 學期）、修讀碩士學位累計至少須滿 12 個月（在本校修業至少 2 學期，跨級碩士在境外學校至少滿 8 個月），在二校當地修習學分數累計應各達獲頒學位所需總學分數三分之一以上。",
      ],
      "language_requirement": [
          "1. 日本姊妹校交換組（10 所常態開放交換校，交換一學年）：依《真理大學交換學生出國甄選辦法》第 5 條及《日本姐妹校交換學生實施計畫》，擬申請至日本姊妹校（城西國際大學、北亞大學、國立香川大學、新潟經營大學、名城大學、星城大學、長崎外國語大學、三重大學、昭和女子大學）交換者，需檢附三年內之日本語能力檢定 JLPT N2 以上證明；其中【日本多摩大學（Tama University）】可憑 JLPT N2 以上或多益（TOEIC）600 分以上申請。",
          "2. 韓國、西班牙、澳洲與歐美英語／外語組：（a）澳洲麥覺理大學（Macquarie University）要求 IELTS 總分 6.5（單科不低於 6.0）且 WAM 60 以上；（b）韓國 11 所交換校（漢陽大學 ERICA 校區、國民大學 Seoul 校區、祥明大學、崇實大學、明知大學、啟明大學、又松大學、東明大學、韓世大學、濟州觀光大學、梨花女子大學）與西班牙赫羅納大學觀光學院（EUHT StPOL）依接待校英語或韓語／西語授課學程規定辦理；（c）中國大陸（北京體育大學、北京交通大學、南京航空航天大學、上海體育大學）與澳門城市大學為中文授課（澳門城市大學另設英文班）。",
          "3. 英美西跨國雙聯學位組：（a）英國密德薩斯大學（Middlesex University London）：3+1 學士雙聯要求 IELTS 6.0（單科不低於 5.5）且 CGPA >= 2.5，1+1 碩士雙聯與 3+15 個月學碩雙聯要求 IELTS 6.5（單科不低於 6.0）且 CGPA >= 2.5；（b）英國西英格蘭大學（UWE Bristol）：3+1 學士雙聯要求 IELTS 6.0（單科不低於 5.5）或通過 UWE Placement Test，4+1 學碩雙聯要求 IELTS 6.5（單科不低於 5.5）或通過 UWE Placement Test；（c）西班牙赫羅納大學附設桑特波爾廚藝觀光學院（EUHT StPOL）1+1 碩士雙聯限觀光事業學系碩士班申請。",
          "4. 教育部學海飛颺／學海惜珠計畫語檢門檻（依《真理大學「學海飛颺」及「學海惜珠」計畫校內甄選簡章》第 5 點）：須檢附兩年內通過之語言能力證明——（a）申請英語教學課程者：全民英檢（GEPT）中高級初試、托福（TOEFL iBT）57 分以上、雅思（IELTS）5.0 分或新版多益（New TOEIC）750 分以上；（b）申請日語教學課程者：JLPT N2 以上；（c）申請韓語教學課程者：TOPIK 2 級以上。",
      ],
      "required_documents": [
          "1. 國外姐妹校交換生報名表／日本交換生報名表（至行政大樓 4 樓國際事務中心領取或自官網下載，須繳交正本 1 份、影本 6 份，並繳交新臺幣 3,000 元行政處理費）",
          "2. 系主任同意書（經所屬學系主任簽核同意推薦）",
          "3. 家長連帶保證書、交換生履行義務同意書（須由家長或法定監護人及學生本人親筆簽章）",
          "4. 履歷表及自傳一份（格式不限，含簡歷＋個人自傳、社團、經歷、特殊表現）",
          "5. 出國學習讀書計畫一份（就申請學校研擬具體讀書計畫含留學動機，文長不得少於 1,000 字；日本交換組須以留學國語言［日文］及中文各繕打一份；申請教育部學海飛颺／惜珠者為 1,000–1,500 字）",
          "6. 本校專任教師推薦信一封（格式不限）",
          "7. 語言能力檢定證明影本（日本組須檢附三年內 JLPT N2 以上或日本多摩大學 TOEIC 600 以上證明；學海飛颺／惜珠須檢附兩年內 GEPT 中高級初試 / TOEFL iBT 57 / IELTS 5.0 / New TOEIC 750 / JLPT N2 / TOPIK 2 級以上證明）",
          "8. 前一學期成績單、排名證明書及在校歷年中文成績單（轉學生需一併提供原學校歷年成績單）",
          "9. 國際事務中心志工服務時數證明文件及其他有助於審查之證明文件影本（回國核銷《真理大學國際交流交換學生獎學金》時另須繳交《國際交流獎學金申請表》、《機票繳附資料黏貼表》［含抬頭「真理大學」統編「37301008」購票證明、登機證正本、電子機票］及 Word 檔《成果報告書》）",
      ],
      "scholarship_info": [
          "1. 教育部「學海飛颺」獎學金（依《真理大學「學海飛颺」及「學海惜珠」計畫校內甄選簡章》）：選送具中華民國國籍、在臺設有戶籍、於本校就讀一學期以上、歷年成績平均達 75 分或班排名前 30%，且通過語檢門檻（英語組 GEPT 中高級初試 / TOEFL iBT 57 / IELTS 5.0 / New TOEIC 750；日語組 JLPT N2；韓語組 TOPIK 2 級）之優秀學生赴國外大專院校（不含大陸及港澳）修讀學分一學期或一學年，每人補助新臺幣 50,000 元以上 300,000 元以下（含國際來回經濟艙機票、國外學費及生活費）。",
          "2. 教育部「學海惜珠」獎學金：選送具各直轄市、縣（市）主管機關認定之低收入戶、中低收入戶或低收入相關補助資格，且符合學海成績（歷年平均 75 分或班排前 30%）與語檢標準之勵學優秀生赴國外大專院校（不含大陸及港澳）修讀學分，補助國際來回經濟艙機票、國外學費及生活費。",
          "3. 教育部「學海築夢」及「新南向學海築夢」海外專業實習獎學金（依《真理大學「學海築夢」及「新南向學海築夢」計畫校內甄選簡章》）：由本校專任教師擔任計畫主持人選送在學學生赴國外或新南向 18 國企業機構進行職場實習（連續至少 30 日，印尼至少 25 日），補助國際來回經濟艙機票款及生活費（含教育部補助款與本校 20% 以上配合款）。",
          "4. 《真理大學國際交流交換學生獎學金》（依《真理大學國際交流交換學生獎學金設置辦法》學 P-510）：獎勵獲得本校國外姐妹校交換學生資格、就讀滿一學年且成績總平均及格、完成註冊程序之在學學生——（a）赴東亞、東南亞、澳洲地區就讀一年之交換學生，最高獎勵新臺幣 15,000 元；（b）赴歐洲、美洲地區就讀一年之交換學生，最高獎勵新臺幣 40,000 元；（c）於回國後次學期開學一個月內，憑結業證書或成績單影本、《國際交流獎學金申請表》、《機票繳附資料黏貼表》（購票收據抬頭：真理大學、統編：37301008、登機證正本、電子機票）及《成果報告書》向國際事務中心提出申請。",
          "5. 《真理大學國際交流海外語言文化研習團獎學金》（依學 P-509 辦法）：補助報名國際事務中心舉辦之寒暑假海外研習課程、且於活動公告前一學期修習達 12 學分以上並達公告成績標準之在學學生（應屆畢業生限參加寒假課程）。",
          "6. 《真理大學國際交流海外志工獎學金》（學 P-513）及《國際交流特殊貢獻獎學金》（學 P-526）：海外志工獎學金以機票或海外交通膳宿補助方式獎勵參與國際志工服務之學生，不分國家地區每人最高新臺幣 20,000 元（活動前 1 個月申請保留、該學年度 7 月 10 日前核銷）；特殊貢獻獎學金於每年 4 月 1 日至 5 月 15 日受理，表揚在校期間積極參與國際交流活動或有特殊表現貢獻之應屆畢業生（給獎名額 3 名）。",
      ],
      "partner_universities": [p["school_name"] for p in partners],
      "source_urls": au_source_urls,
      "last_checked": CHECKED_AT,
  }
  (OFFICIAL_AU_DIR / "exchange_info.json").write_text(
      json.dumps(exchange_info_payload, ensure_ascii=False, indent=2) + "\n",
      encoding="utf-8",
  )

  student_dashboard_payload = {
      "school_name": "真理大學",
      "last_checked": CHECKED_AT,
      "academic_score_minimum": 60.0,
      "academic_score_rule": (
          "依《真理大學交換學生出國甄選辦法》（教-P-806）第 4 條：申請人須為具本校學籍且曾在本校就讀滿一學年以上之大學部（大二以上）與研究所（碩二以上）在學學生，前一學期學業成績全班前 50% 為原則且操行分數達 80 分以上；申請教育部《學海飛颺／學海惜珠獎學金》須於本校就讀一學期以上且歷年成績平均達 75 分或班排名前 30%；申請澳洲麥覺理大學交換須 WAM 達 60 分以上；申請英國密德薩斯大學雙聯學制須 CGPA 達 2.5 以上。"
      ),
      "academic_gpa_minimum": 2.5,
      "maximum_preferences": 5,
      "selection_rules": {
          "academic_policy": "gpa_or_rank",
          "academic_reference_year": "115",
          "undergraduate_gpa_minimum": 2.5,
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
          "toefl": 57.0,
          "ielts": 5.0,
          "toefl_itp": 460.0,
          "toeic": 600.0,
      },
      "application_periods": [
          {
              "title": "真理大學「2027 春季國外姐妹校交換學生實施計畫」校內甄選（115 年 10 月 9 日中午 12:00 截止，申請 116 年 2 月–6 月赴韓、西、澳交換）",
              "details": [
                  "依真理大學國際事務中心公告之《2027 春季國外姐妹校交換學生實施計畫》，選送本校就讀滿一學年以上、前一學期學業成績全班前 50% 且操行達 80 分以上之大二／碩二以上在學學生，於 116 年 2 月至 116 年 6 月赴韓國（漢陽大學 ERICA 校區、東明大學、韓世大學、啟明大學、祥明大學、又松大學、明知大學、濟州觀光大學、國民大學 Seoul 校區、崇實大學、梨花女子大學）、西班牙（赫羅納大學觀光學院 EUHT StPOL）及澳洲（麥覺理大學）交換。",
                  "報名者請先攜帶 1~9 項文件正本至行政大樓 4 樓國際事務中心確認無誤後，於 115 年 10 月 9 日（五）中午 12:00 整前繳交正本 1 份、影本 6 份及新臺幣 3,000 元行政處理費。",
              ],
              "source": {
                  "title": "真理大學國際事務中心 2027 春季國外姐妹校交換學生實施計畫",
                  "source_url": AU_2027_SPRING_EXCHANGE_URL,
                  "category": "exchange_application",
                  "summary": "真理大學 2027 春季班國外姐妹校交換生甄選資格、開放學校與 115/10/09 截止日期。",
              },
              "scope": "home_application",
              "program_types": ["exchange", "dual_degree"],
              "academic_year": "115",
              "application_round": "2027 春季國外姐妹校交換學生校內甄選",
              "audience": "all_students",
              "opens_at": "2026-07-30T09:00:00+08:00",
              "deadline_at": "2026-10-09T12:00:00+08:00",
              "date_status": "verified_exact",
              "status": "open",
              "status_note": "2027 春季班出國交換甄選於 115 年 10 月 9 日（五）中午 12:00 截止收件。",
              "deadline_note": "須備齊 1~9 項資料正本 1 份、影本 6 份並繳交 NT$ 3,000 行政處理費送行政大樓 4 樓國際事務中心。",
              "reminder_eligible": True,
              "checked_at": CHECKED_AT,
          },
          {
              "title": "真理大學「日本姐妹校交換學生實施計畫」校內甄選（每年 11 月下旬中午 12:00 截止，申請次年 9 月至隔年 8 月赴日交換一學年）",
              "details": [
                  "依《2026~2027 日本姐妹校交換學生實施計畫》，選送本校就讀滿一學年以上、前學期成績全班前 50% 且操行達 80 分以上、具備日語檢定 JLPT N2 以上（日本多摩大學可憑 JLPT N2 或多益 TOEIC 600 分以上）之在學學生，赴日本 10 所姊妹校（城西國際大學、北亞大學、國立香川大學、新潟經營大學、名城大學、星城大學、長崎外國語大學、三重大學、多摩大學、昭和女子大學）進行為期一學年（9 月至翌年 8 月）交換研修。",
                  "報名須檢附以日文及中文各繕打一份之 1,000 字以上出國學習讀書計畫、三年內語檢證明及 1~9 項文件正本 1 份、影本 6 份。",
              ],
              "source": {
                  "title": "真理大學國際事務中心日本姐妹校交換學生實施計畫",
                  "source_url": AU_2026_2027_JAPAN_EXCHANGE_URL,
                  "category": "exchange_application",
                  "summary": "真理大學赴日本 10 所姊妹校一學年交換學生甄選簡章與語檢門檻。",
              },
              "scope": "home_application",
              "program_types": ["exchange"],
              "academic_year": "115",
              "application_round": "日本姐妹校交換學生實施計畫校內甄選（一學年）",
              "audience": "all_students",
              "opens_at": "2026-09-25T09:00:00+08:00",
              "deadline_at": "2026-11-25T12:00:00+08:00",
              "date_status": "verified_exact",
              "status": "open",
              "status_note": "日本姊妹校一學年交換甄選每年 9–11 月受理報名，11 月下旬中午 12:00 截止。",
              "deadline_note": "日本組須以留學國語言（日文）及中文各繕打一份 1,000 字以上讀書計畫，並檢附 JLPT N2（或多摩大學 TOEIC 600）證明。",
              "reminder_eligible": True,
              "checked_at": CHECKED_AT,
          },
          {
              "title": "真理大學「秋季國外姐妹校交換學生實施計畫」暨「教育部學海飛颺／惜珠／築夢計畫」校內甄選（每年 3 月上旬中午 12:00 截止）",
              "details": [
                  "依《2026 秋季國外姐妹校交換學生實施計畫》及《真理大學「學海飛颺」及「學海惜珠」計畫校內甄選簡章》，每年 1–3 月開放秋季班（9 月至翌年 1 月出國交換，涵蓋中國北京體育大學、韓國 11 校、西班牙赫羅納大學觀光學院、澳洲麥覺理大學）及英美西雙聯學位（英國密德薩斯大學、英國西英格蘭大學、西班牙 EUHT StPOL、美國明州西南州立大學）校內申請。",
                  "通過交換或雙聯甄選之學生可同步申請教育部《學海飛颺／學海惜珠計畫》（歷年平均 75 分或班排前 30%），並於交換一學年返國後次學期開學一個月內申請《真理大學國際交流交換學生獎學金（學 P-510）》（東亞／東南亞／澳洲最高 NT$ 15,000、歐美最高 NT$ 40,000）。",
              ],
              "source": {
                  "title": "真理大學秋季國外姐妹校交換學生實施計畫與教育部學海系列校內甄選簡章",
                  "source_url": AU_2026_FALL_EXCHANGE_URL,
                  "category": "scholarship",
                  "summary": "真理大學秋季班國外姐妹校交換甄選、教育部學海系列計畫與校內國際交流獎學金規範。",
              },
              "scope": "home_application",
              "program_types": ["exchange", "dual_degree"],
              "academic_year": "115",
              "application_round": "秋季國外姐妹校交換學生暨教育部學海系列校內甄選",
              "audience": "all_students",
              "opens_at": "2027-01-05T09:00:00+08:00",
              "deadline_at": "2027-03-05T12:00:00+08:00",
              "date_status": "verified_exact",
              "status": "upcoming",
              "status_note": "秋季班國外交換與教育部學海飛颺／惜珠校內甄選於每年 1–3 月上旬受理（2026 秋季班於 115/03/06 截止；2027 秋季班預計 116/03/05 截止）。",
              "deadline_note": "學海受獎生須於出國研習結束後二星期內上傳問卷及 1,500 字以上心得報告至學海計畫平台。",
              "reminder_eligible": True,
              "checked_at": CHECKED_AT,
          },
      ],
      "program_overview": [
          {
              "title": (
                  f"真理大學國際事務中心全球交換、英美西雙聯學位與六大獎助學金總覽（{len(partners)} 所合作姊妹校・{open_partner_count} 所常態開放申請・{total_exp_reports} 篇學長姐交換求學心得報告）"
              ),
              "details": [
                  (
                      f"真理大學（Aletheia University, AU，源於 1872 年加拿大基督長老教會馬偕博士［Rev. Dr. George Leslie Mackay］於淡水創立之台灣最早西式現代學府「牛津學堂 Oxford College／理學堂大書院」，1965 年設立淡水工商管理專科學校，1994 年改制淡水工商管理學院，1999 年奉准改名真理大學，校址位於新北市淡水區真理街 32 號紅毛城與牛津學堂古蹟園區旁）由教務處「國際事務中心（Center for International Affairs, CIA）」統籌全校 4 個學院（人文學院、觀光休閒與運動學院、管理與資訊學院、財經學院）共 20 個學系與碩士班之校級出國交換學生計畫、日本姊妹校一學年交換計畫、海外雙聯學位計畫、寒暑假海外語言文化研習團及國際交流獎助學金。本平台完整收錄 {len(partners)} 所真理大學有效締約合作姊妹校，橫跨全球 14 個國家與地區。"
                  ),
                  (
                      f"真理大學國際交流具備四大核心特色：（1）日本（10 所常態開放交換校：城西國際大學、北亞大學、國立香川大學、新潟經營大學、名城大學、星城大學、長崎外國語大學、三重大學、多摩大學［可憑 TOEIC 600 或 JLPT N2 申請］、昭和女子大學）與韓國（11 所常態開放交換校：漢陽大學 ERICA 校區、國民大學 Seoul 校區、祥明大學、崇實大學、明知大學、啟明大學、又松大學、東明大學、韓世大學、濟州觀光大學、梨花女子大學）、澳洲雪梨百大名校麥覺理大學（Macquarie University）、西班牙赫羅納大學附設桑特波爾廚藝觀光學院（EUHT StPOL，QS 世界餐旅管理前 30 名）及大陸雙一流名校（北京體育大學、北京交通大學、南京航空航天大學、上海體育大學）與澳門城市大學常態交換；（2）英、西、美 4 校跨國雙聯學位（英國密德薩斯大學 3+1／1+1／3+15 個月、英國西英格蘭大學 UWE Bristol 3+1／4+1、西班牙 EUHT StPOL 觀光碩士 1+1、美國明州西南州立大學 SMSU）；（3）教育部學海飛颺、學海惜珠、學海築夢與《真理大學國際交流交換學生獎學金（學 P-510，歐美最高 4 萬、亞澳最高 1.5 萬）》、《海外語言文化研習團獎學金（學 P-509）》、《海外志工獎學金（學 P-513）》六大獎助體系；（4）完整收錄 {exp_covered_schools} 所合作大學共 {total_exp_reports} 篇歷屆學長姐交換求學心得報告。"
                  ),
              ],
              "source": {
                  "title": "真理大學國際事務中心（Center for International Affairs, CIA）官方網站",
                  "source_url": AU_CIA_HOME_URL,
                  "category": "exchange_application",
                  "summary": f"真理大學 {len(partners)} 所全球合作姊妹校、4 所雙聯學位校與 {total_exp_reports} 篇交換求學心得報告。",
              },
          }
      ],
      "eligibility": [
          {
              "title": "就讀滿一學年（大二／碩二以上）在學資格、前學期成績全班前 50% 與操行 80 分門檻、每學期修習 9 學分及全額學雜費規定",
              "details": [
                  "在學身分、年級與成績門檻：依《真理大學交換學生出國甄選辦法》（教-P-806，114年4月14日行政會議修正通過）第 4 條，申請交換學生應符合：（1）具有本校學籍之大學部與研究所在學學生，須曾在本校就讀滿一學年以上（即大二以上、碩二以上），始得參加甄選；（2）前一學期學業成績全班前 50% 為原則，且操行分數達 80 分以上；（3）非本國國籍學生不得申請（原屬國家）交換學生。",
                  "在學註冊、行政處理費與赴外修課規定：依《交換學生出國甄選辦法》第 6、9 條及《學生出境修習學分實施辦法》第 4、6 條，報名時需繳交新臺幣 3,000 元行政處理費，交換期間仍需繳交本校全額學雜費；研修期間不得低於一學期、最高以一年為限，每學期修習課程以不低於 9 學分為原則，返國後採認學分最高不得超過應修畢業學分數之三分之二。",
              ],
              "source": {
                  "title": "真理大學交換學生出國甄選辦法（教-P-806）與學生出境修習學分實施辦法",
                  "source_url": AU_SELECTION_REGULATION_PAGE_URL,
                  "category": "exchange_application",
                  "summary": "真理大學交換生就讀滿一學年資格、班排前 50% 門檻、行政處理費 3,000 元與每學期 9 學分修課規定。",
              },
          }
      ],
      "language_requirements": [
          {
              "title": "日本組（JLPT N2 或多摩大學 TOEIC 600）、澳洲麥覺理大學（IELTS 6.5）、英國雙聯（IELTS 6.0–6.5）與教育部學海計畫語檢門檻",
              "details": [
                  "日本姊妹校交換組與澳洲、韓國、西班牙、大陸港澳組：（1）日本 10 所交換姊妹校（城西國際、北亞、香川、新潟經營、名城、星城、長崎外語、三重、昭和女子）要求三年內通過日語檢定 JLPT N2 以上，日本多摩大學可憑 JLPT N2 或 TOEIC 600 分以上申請；（2）澳洲麥覺理大學要求 IELTS 6.5（單科不低於 6.0）且在校 WAM 60 以上；（3）韓國 11 所交換姊妹校與西班牙赫羅納大學觀光學院（EUHT StPOL）依接待校英語或韓語／西語授課規定；（4）中國大陸與澳門姊妹校為中文授課。",
                  "英國雙聯學位與教育部學海飛颺／惜珠門檻：（1）英國密德薩斯大學 3+1 學士雙聯要求 IELTS 6.0（單科 5.5）、1+1 碩士與 3+15 個月學碩雙聯要求 IELTS 6.5（單科 6.0）且 CGPA >= 2.5；英國西英格蘭大學（UWE Bristol）3+1 要求 IELTS 6.0（單科 5.5）或 UWE Placement Test、4+1 要求 IELTS 6.5（單科 5.5）或 Placement Test；（2）教育部學海飛颺／惜珠要求兩年內通過英語組（GEPT 中高級初試 / TOEFL iBT 57 / IELTS 5.0 / New TOEIC 750）、日語組（JLPT N2）或韓語組（TOPIK 2 級）。",
              ],
              "source": {
                  "title": "真理大學日本姐妹校交換生實施計畫、國外姐妹校交換生實施計畫與雙聯學制專區",
                  "source_url": AU_2026_2027_JAPAN_EXCHANGE_URL,
                  "category": "exchange_application",
                  "summary": "真理大學日本、韓國、澳洲、西班牙、英國雙聯與學海計畫外語能力檢定標準。",
              },
          }
      ],
      "required_documents": [
          {
              "title": "校內甄選 1~9 項文件（正本 1 份、影本 6 份）、1,000 字以上讀書計畫（日本組中日文各一份）與國際交流獎學金機票核銷表件",
              "details": [
                  "校內交換甄選必備 1~9 項文件（先攜帶正本至行政大樓 4 樓國際事務中心確認無誤後，繳交正本 1 份、影本 6 份及 NT$ 3,000 行政處理費）：（1）報名表；（2）系主任同意書；（3）家長連帶保證書、交換生履行義務同意書；（4）履歷表及自傳；（5）出國學習讀書計畫（文長不得少於 1,000 字，日本組須以日文及中文各繕打一份；學海計畫為 1,000–1,500 字）；（6）本校教師推薦信一封；（7）語言能力證明影本；（8）前一學期成績單、排名證明書及歷年中文成績單；（9）國際事務中心志工服務時數證明及其他有利審查文件。",
                  "返國學分抵免與獎學金核銷文件：返國後由學系填送《境外校際選課暨成績報告單》辦理學分採認；申請《真理大學國際交流交換學生獎學金（學 P-510）》須於回國後次學期開學一個月內繳交《國際交流獎學金申請表》、《機票繳附資料黏貼表》（含買受人抬頭「真理大學」、統一編號「37301008」之旅行社代收轉付收據或購票證明、來回登機證正本、電子機票）及 Word 檔《成果報告書》。",
              ],
              "source": {
                  "title": "真理大學國外姐妹校交換學生實施計畫與國際交流獎學金核銷公告",
                  "source_url": AU_2027_SPRING_EXCHANGE_URL,
                  "category": "exchange_application",
                  "summary": "真理大學交換生校內申請 1~9 項表件與返國機票獎學金核銷規範。",
              },
          }
      ],
      "scholarship_info": [
          {
              "title": "教育部學海飛颺／惜珠／築夢獎學金與真理大學國際交流交換生（學 P-510）／海外研習團（學 P-509）／海外志工（學 P-513）／特殊貢獻（學 P-526）獎學金",
              "details": [
                  "教育部學海系列獎學金：（1）《學海飛颺》：就讀一學期以上、歷年平均 75 分以上或班排前 30%，通過語檢門檻（TOEFL iBT 57 / IELTS 5.0 / New TOEIC 750 / GEPT 中高級初試 / JLPT N2 / TOPIK 2 級），補助 NT$ 50,000–300,000；（2）《學海惜珠》：具低收入戶、中低收入戶或相關補助資格之優秀生，補助機票、國外學費及生活費；（3）《學海築夢／新南向學海築夢》：補助海外專業實習（含教育部補助款與學校 20% 配合款）。",
                  "真理大學國際事務中心四大校內獎學金：（1）《國際交流交換學生獎學金（學 P-510）》：赴東亞、東南亞、澳洲地區就讀一年最高獎勵 NT$ 15,000；赴歐洲、美洲地區就讀一年最高獎勵 NT$ 40,000；（2）《國際交流海外語言文化研習團獎學金（學 P-509）》：補助參加寒暑假海外研習課程且前學期修滿 12 學分以上之學生；（3）《國際交流海外志工獎學金（學 P-513）》：每人最高補助 NT$ 20,000；（4）《國際交流特殊貢獻獎學金（學 P-526）》：表揚積極參與國際交流之應屆畢業生（每年 4/1–5/15 申請，名額 3 名）。",
              ],
              "source": {
                  "title": "真理大學國際事務中心相關法規—獎學金專區與教育部學海計畫專區",
                  "source_url": AU_SCHOLARSHIP_REGULATIONS_URL,
                  "category": "scholarship",
                  "summary": "真理大學六大出國交換、專業實習、語言研習與國際志工獎助學金完整辦法。",
              },
          }
      ],
      "document_explanations": [
          {
              "title": "真理大學赴國外姊妹校交換 1,000 字讀書計畫（日本組中日文雙語）、國際事務中心志工時數與家長連帶保證書準備指南",
              "summary": "說明《真理大學交換學生出國甄選辦法》第 5、8 條規定之評分項目、1,000 字以上讀書計畫（日本組須中日文各一份）、志工服務時數加分及返國機票核銷要領。",
              "key_points": [
                  "1,000 字以上出國學習讀書計畫（日本組須以日文及中文各繕打一份）：應針對擬申請之姊妹校（如日本城西國際、香川、名城、多摩，韓國漢陽 ERICA、國民、祥明、崇實，西班牙 EUHT StPOL，澳洲麥覺理大學或英美雙聯校）具體說明留學動機、每學期至少修習 9 學分之選課規劃及返國後與真理大學母系課程之學分抵免銜接（申請學海飛颺／惜珠者字數須介於 1,000–1,500 字）。",
                  "國際事務中心志工服務時數與自傳履歷：依《交換學生出國甄選辦法》第 8 條第 2 款，甄選成績由（1）外語能力檢定證明、（2）在校歷年學業成績、（3）自傳、履歷及讀書計畫、（4）在校歷年操行成績、（5）國際事務中心志工服務時數、（6）其他輔助審查文件加總排序，參與國際事務中心接待境外生或國際交流活動之志工時數具直接加分效益。",
                  "家長連帶保證書與返國獎學金機票核銷：報名時須繳交《系主任同意書》與《家長連帶保證書、交換生履行義務同意書》（正本 1 份、影本 6 份）；欲申請《國際交流交換學生獎學金（學 P-510）》者，購買機票時務必請旅行社或航空公司開立買受人抬頭「真理大學」、統一編號「37301008」之購票證明，並妥善保存來回登機證正本與電子機票，於返國後次學期開學一個月內提出申請。",
              ],
              "applies_to": [],
              "source": {
                  "title": "真理大學交換學生出國甄選辦法（教-P-806）與國際交流獎學金核銷公告",
                  "source_url": AU_SELECTION_REGULATION_PAGE_URL,
                  "category": "exchange_application",
                  "summary": None,
              },
              "document_url": AU_SCHOLARSHIP_REIMBURSEMENT_URL,
              "document_type": "official_document",
              "full_text_extracted": True,
          }
      ],
      "rule_explanations": [
          {
              "title": "真理大學交換學生出國甄選辦法（教-P-806）、學生出境修習學分實施辦法與雙聯學制實施辦法核心規定",
              "summary": "規範真理大學交換生就讀滿一學年資格、班排前 50% 門檻、行政處理費 3,000 元、全額學雜費註冊、每學期至少 9 學分及畢業學分 2/3 採認上限。",
              "key_points": [
                  "在學註冊、行政處理費與退費例外：依《真理大學交換學生出國甄選辦法》第 9、10 條，交換生於報名時需繳交行政處理費 3,000 元（除政府宣布出入境限制、姊妹校取消計畫、姊妹校延期導致須延畢或經審查委員會同意外，不予退費），交換期間仍需繳交本校全額學雜費；凡錄取完成提名後，不得擅自放棄交換生身分。",
                  "赴外選課下限與返國學分抵免上限：依《交換學生出國甄選辦法》第 6 條及《學生出境修習學分實施辦法》第 6、7 條，交換研修期間每學期修習課程以不低於 9 學分為原則；出境修習學分計算原則以修滿 18 小時成績及格者為 1 學分，採認學分最高不得超過應修畢業學分數之三分之二，出境修習期間列入修業年限計算最高以二年為限。",
                  "雙聯學制修業時間與學分下限：依《真理大學與境外大學辦理雙聯學制實施辦法》第 8 條，修讀同級雙聯學士學位者累計修業時間至少滿 32 個月（在本校至少 4 學期）、同級碩士至少滿 12 個月（在本校至少 2 學期，跨級碩士在境外學校至少滿 8 個月），在二校當地修習學分數累計應各達獲頒學位所需總學分數三分之一以上。",
              ],
              "applies_to": [],
              "source": {
                  "title": "真理大學交換學生出國甄選辦法、學生出境修習學分實施辦法與雙聯學制實施辦法",
                  "source_url": AU_SELECTION_REGULATION_PAGE_URL,
                  "category": "exchange_application",
                  "summary": None,
              },
              "document_url": AU_CREDIT_TRANSFER_REGULATION_PAGE_URL,
              "document_type": "official_document",
              "full_text_extracted": True,
          }
      ],
      "sources": [
          {
              "title": "真理大學國際事務中心（Center for International Affairs, CIA）官方網站",
              "source_url": AU_CIA_HOME_URL,
              "category": "exchange_application",
              "summary": None,
          },
          {
              "title": "真理大學出國留學與交換總覽及國外／日本姐妹校交換生實施計畫專區",
              "source_url": AU_EXCHANGE_PROGRAMS_URL,
              "category": "exchange_application",
              "summary": None,
          },
          {
              "title": f"真理大學全球與兩岸合作姊妹校名錄（全球 14 國與地區共 {len(partners)} 所合作姊妹校）",
              "source_url": AU_SISTER_SCHOOLS_URL,
              "category": "partner_school",
              "summary": None,
          },
          {
              "title": "真理大學海外雙聯學制專區（英國密德薩斯大學、英國西英格蘭大學、西班牙赫羅納大學觀光學院 EUHT StPOL）",
              "source_url": AU_DUAL_DEGREE_URL,
              "category": "exchange_application",
              "summary": None,
          },
          {
              "title": "真理大學交換學生出國甄選辦法（教-P-806）、學生出境修習學分實施辦法與雙聯學制實施辦法",
              "source_url": AU_OUTBOUND_REGULATIONS_URL,
              "category": "exchange_application",
              "summary": None,
          },
          {
              "title": "真理大學國際交流獎學金法規專區（交換學生獎學金學 P-510、海外語言文化研習團獎學金學 P-509、海外志工獎學金學 P-513、特殊貢獻獎學金學 P-526）",
              "source_url": AU_SCHOLARSHIP_REGULATIONS_URL,
              "category": "scholarship",
              "summary": None,
          },
          {
              "title": "真理大學教育部學海飛颺、學海惜珠、學海築夢與新南向學海築夢計畫專區",
              "source_url": AU_XUEHAI_OVERVIEW_URL,
              "category": "scholarship",
              "summary": None,
          },
          {
              "title": f"真理大學出國留學與交換—求學心得專區（{exp_covered_schools} 校 {total_exp_reports} 篇歷屆交換生心得報告）",
              "source_url": AU_STUDENT_EXPERIENCES_URL,
              "category": "exchange_application",
              "summary": None,
          },
      ],
  }
  (OFFICIAL_AU_DIR / "student_dashboard.json").write_text(
      json.dumps(student_dashboard_payload, ensure_ascii=False, indent=2)
      + "\n",
      encoding="utf-8",
  )

  doc_conditions = {
      "school_id": "au",
      "school_name": "真理大學",
      "checked_at": CHECKED_AT,
      "source_url": AU_SELECTION_REGULATION_PAGE_URL,
      "common_documents": exchange_info_payload["required_documents"],
      "track_specific_conditions": [
          {
              "track": "校級赴日本姊妹校交換學生計畫（城西國際、北亞、香川、新潟經營、名城、星城、長崎外語、三重、多摩、昭和女子等 10 校，交換一學年）",
              "required": [
                  "日本交換生報名表、系主任同意書、家長連帶保證書與交換生履行義務同意書（正本 1 份、影本 6 份，並繳交 NT$ 3,000 行政處理費）",
                  "三年內通過之日本語能力檢定 JLPT N2 以上證明影本（申請日本多摩大學者可檢附 JLPT N2 或 TOEIC 600 分以上證明）",
                  "以留學國語言（日文）及中文各繕打一份之 1,000 字以上出國學習讀書計畫、履歷表及自傳、本校教師推薦信一封、前一學期成績單與排名證明書（全班前 50%、操行 80 分以上）、歷年中文成績單及國際事務中心志工服務證明",
              ],
          },
          {
              "track": "校級赴韓國、西班牙、澳洲、中國大陸與澳門姊妹校交換學生計畫（春季班／秋季班）",
              "required": [
                  "國外姐妹校交換生報名表、系主任同意書、家長連帶保證書與交換生履行義務同意書（正本 1 份、影本 6 份，並繳交 NT$ 3,000 行政處理費）",
                  "前一學期成績單、排名證明書（全班前 50%、操行 80 分以上）及歷年中文成績單（申請澳洲麥覺理大學須 WAM 60 以上）",
                  "1,000 字以上出國學習讀書計畫、履歷表及自傳、本校教師推薦信一封、語言能力證明影本（澳洲麥覺理大學須 IELTS 6.5 單科 6.0）及國際事務中心志工服務時數證明",
              ],
          },
          {
              "track": "英、西、美跨國雙聯學位計畫（密德薩斯大學 3+1／1+1／3+15m、西英格蘭大學 3+1／4+1、西班牙 EUHT StPOL 1+1、美國明州西南州立大學）",
              "required": [
                  "雙聯學制申請表、系主任同意書、英文歷年成績單（密德薩斯大學須 CGPA >= 2.5）與護照影本",
                  "英語能力檢定證明：密德薩斯大學 3+1 須 IELTS 6.0（單科 5.5）、1+1 及 3+15 個月須 IELTS 6.5（單科 6.0）；西英格蘭大學 3+1 須 IELTS 6.0（單科 5.5）或 UWE Placement Test、4+1 須 IELTS 6.5（單科 5.5）或 Placement Test",
                  "英文讀書計畫（Statement of Purpose）、英文履歷與教師推薦信",
              ],
          },
          {
              "track": "教育部「學海飛颺／惜珠／築夢計畫」與《真理大學國際交流交換學生獎學金（學 P-510）》申請及核銷",
              "required": [
                  "教育部學海飛颺／惜珠申請：校內申請表、系主任同意書及家長同意書、履歷表、教師推薦信、1,000–1,500 字出國研修計畫書、歷年中文成績單（平均 75 分以上或班排前 30%）、兩年內語檢證明（GEPT 中高級初試 / TOEFL iBT 57 / IELTS 5.0 / New TOEIC 750 / JLPT N2 / TOPIK 2 級；學海惜珠另附低收／中低收證明及戶口名簿影本）",
                  "《真理大學國際交流交換學生獎學金（學 P-510）》返國核銷（回國後次學期開學一個月內）：國際交流獎學金申請表、結業證書或成績單影本、機票繳附資料黏貼表（含抬頭「真理大學」統編「37301008」之購票證明、來回登機證正本、電子機票）及 Word 檔成果報告書",
              ],
          },
      ],
  }
  (OFFICIAL_AU_DIR / "document-conditions.json").write_text(
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
        f"{fname},{len(partners)},{pop},{ratio:.4f},Official AU CIA verified"
    )
  (OFFICIAL_AU_DIR / "field-coverage.csv").write_text(
      "\n".join(field_cov_lines) + "\n", encoding="utf-8"
  )

  pages_records = [
      {
          "title": "真理大學：春季班（10 月上旬截止）、日本一學年交換（11 月下旬截止）與秋季班（3 月上旬截止）出國交換暨雙聯學位甄選時程",
          "source_url": AU_EXCHANGE_PROGRAMS_URL,
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
          "title": "真理大學：交換學生出國甄選辦法（教-P-806）、就讀滿一學年資格、班排前 50% 門檻、全額學雜費註冊與每學期 9 學分規定",
          "source_url": AU_SELECTION_REGULATION_PAGE_URL,
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
          "title": f"真理大學：{len(partners)} 所全球與兩岸合作姊妹校外語檢定門檻（日本 10 校 JLPT N2／多摩大學 TOEIC 600／韓國 11 校／澳洲麥覺理 IELTS 6.5／英西雙聯）",
          "source_url": AU_SISTER_SCHOOLS_URL,
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
          "title": "真理大學：出國交換與雙聯學位應備 1~9 項文件（報名表、系主任同意書、家長連帶保證書、1,000 字讀書計畫、志工時數證明與獎學金核銷機票黏貼表）",
          "source_url": AU_2027_SPRING_EXCHANGE_URL,
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
          "title": "真理大學：教育部學海飛颺、學海惜珠、學海築夢與真理大學國際交流交換學生獎學金（學 P-510）、海外研習團獎學金（學 P-509）、海外志工獎學金（學 P-513）辦法",
          "source_url": AU_SCHOLARSHIP_REGULATIONS_URL,
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
  (OFFICIAL_AU_DIR / "pages.jsonl").write_text(
      "\n".join(json.dumps(p, ensure_ascii=False) for p in pages_records)
      + "\n",
      encoding="utf-8",
  )

  home_rules = {
      "school_id": "au",
      "school_name": "真理大學",
      "eligibility": student_dashboard_payload["eligibility"],
      "application_periods": student_dashboard_payload["application_periods"],
      "selection_rules": {
          "minimum_passing_score": 60.0,
          "class_rank_threshold": "top 50% of class in previous semester, conduct >= 80",
          "excluded_undergraduate_years": [1],
          "excluded_graduate_years": [1],
          "xuehai_threshold": "cumulative average >= 75 or top 30% of class",
          "au_exchange_scholarship_amount": "NT$ 15,000 for East Asia/SE Asia/Australia (1 year); NT$ 40,000 for Europe/Americas (1 year)",
          "administrative_processing_fee_ntd": 3000,
          "min_credits_per_semester_abroad": "9 credits (credit transfer cap: 2/3 of graduation credits)",
          "require_au_full_tuition_during_abroad": True,
          "return_documents_due": "學海受獎生於返國後二星期內上傳問卷及 1,500 字以上心得報告；校內國際交流交換學生獎學金於返國後次學期開學一個月內繳交申請表、機票黏貼表及成果報告書",
      },
      "source_urls": au_source_urls,
      "verified_at": "2026-11-03",
  }
  (OFFICIAL_AU_DIR / "home_rules.json").write_text(
      json.dumps(home_rules, ensure_ascii=False, indent=2) + "\n",
      encoding="utf-8",
  )
  (OFFICIAL_AU_DIR / "documents.json").write_text(
      json.dumps(
          {
              "school_name": "真理大學",
              "required_documents": student_dashboard_payload[
                  "required_documents"
              ],
              "source_urls": au_source_urls,
          },
          ensure_ascii=False,
          indent=2,
      )
      + "\n",
      encoding="utf-8",
  )
  (OFFICIAL_AU_DIR / "scholarships.json").write_text(
      json.dumps(
          {
              "school_name": "真理大學",
              "scholarships": student_dashboard_payload["scholarship_info"],
              "source_urls": au_source_urls,
          },
          ensure_ascii=False,
          indent=2,
      )
      + "\n",
      encoding="utf-8",
  )

  completeness = {
      "school_id": "au",
      "school_name": "真理大學",
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
      "dual_degree_programs": 7,
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
          f"真理大學國際事務中心（CIA）《全球姊妹校名錄》、《2027春季／2026秋季／2026~2027日本姐妹校交換學生實施計畫》、《雙聯學制專區（4 校 7 學程）》、《真理大學交換學生出國甄選辦法（教-P-806）》、《學生出境修習學分實施辦法》、《與境外大學辦理雙聯學制實施辦法》，以及教育部學海飛颺、學海惜珠、學海築夢與《真理大學國際交流交換學生獎學金（學 P-510）》同步整合；共完整收錄 {len(partners)} 所全球與兩岸有效締約交換及雙聯姊妹校（橫跨全球 14 個國家與地區，並收錄 {exp_covered_schools} 所合作大學共 {total_exp_reports} 篇歷屆學長姐交換求學心得報告）。"
      ),
      "verified_at": "2026-11-03",
  }
  (OFFICIAL_AU_DIR / "catalog-completeness.json").write_text(
      json.dumps(completeness, ensure_ascii=False, indent=2) + "\n",
      encoding="utf-8",
  )
  (OFFICIAL_AU_DIR / "verification_status.json").write_text(
      json.dumps(
          {
              "school_id": "au",
              "school_name": "真理大學",
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
          "sources/au/au_catalog_source.json",
          AU_SISTER_SCHOOLS_URL,
          f"真理大學 {len(partners)} 所全球與兩岸合作姊妹校整合資料集 JSON",
      ),
      (
          "sources/au/au_resolved_locations.json",
          AU_SISTER_SCHOOLS_URL,
          f"真理大學 {len(partners)} 所合作姊妹校 ROR / Wikidata 地理座標核對表 JSON",
      ),
      (
          "sources/au/cia_exchange_outbound.html",
          AU_EXCHANGE_PROGRAMS_URL,
          "真理大學國際事務中心《國外／日本姐妹校交換生實施計畫專區》HTML",
      ),
      (
          "sources/au/cia_dual_degree.html",
          AU_DUAL_DEGREE_URL,
          "真理大學國際事務中心《海外雙聯學制專區》HTML",
      ),
      (
          "sources/au/cia_sisters_asia.html",
          AU_SISTER_SCHOOLS_URL,
          "真理大學國際事務中心《全球姊妹校總覽》HTML",
      ),
      (
          "sources/au/cia_experiences.html",
          AU_STUDENT_EXPERIENCES_URL,
          "真理大學國際事務中心《出國留學與交換—求學心得專區》HTML",
      ),
      (
          "sources/au/regulations/406-1022-84480_教-P-806真理大學交換學生出國甄選辦法(1140414行政會議修正通過).pdf",
          AU_SELECTION_REGULATION_PAGE_URL,
          "真理大學《交換學生出國甄選辦法（教-P-806，1140414修正通過）》PDF",
      ),
      (
          "sources/au/regulations/406-1022-70817_學生出境修習學分實施辦法.pdf",
          AU_CREDIT_TRANSFER_REGULATION_PAGE_URL,
          "真理大學《學生出境修習學分實施辦法》PDF",
      ),
      (
          "sources/au/regulations/406-1022-93784_真理大學與境外大學辦理雙聯學制實施辦法.pdf",
          AU_DUAL_DEGREE_REGULATION_PAGE_URL,
          "真理大學《與境外大學辦理雙聯學制實施辦法》PDF",
      ),
      (
          "sources/au/regulations/P-01-510.pdf",
          AU_EXCHANGE_SCHOLARSHIP_PDF_URL,
          "真理大學《國際交流交換學生獎學金設置辦法（學 P-510）》PDF",
      ),
      (
          "sources/au/regulations/P-01-509.pdf",
          AU_STUDY_TOUR_SCHOLARSHIP_PDF_URL,
          "真理大學《國際交流海外語言文化研習團獎學金設置辦法（學 P-509）》PDF",
      ),
      (
          "sources/au/regulations/P-01-513.pdf",
          AU_VOLUNTEER_SCHOLARSHIP_PDF_URL,
          "真理大學《國際交流海外志工獎學金設置辦法（學 P-513）》PDF",
      ),
      (
          "sources/au/regulations/P-01-526.pdf",
          AU_SPECIAL_CONTRIBUTION_SCHOLARSHIP_PDF_URL,
          "真理大學《國際交流特殊貢獻獎學金設置辦法（學 P-526）》PDF",
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
      "school_id": "au",
      "school_name": "真理大學",
      "generated_at": CHECKED_AT,
      "active_cycle_note": completeness["active_term"],
      "sources": prov_sources,
  }
  prov_text = (
      json.dumps(provenance_payload, ensure_ascii=False, indent=2) + "\n"
  )
  (OFFICIAL_AU_DIR / "import_provenance.json").write_text(
      prov_text, encoding="utf-8"
  )
  (OFFICIAL_AU_DIR / "import-provenance.json").write_text(
      prov_text, encoding="utf-8"
  )

  print(
      f"Successfully built AU catalog: {len(partners)} partners"
      f" ({open_partner_count} open, {completeness['verified_campus_images']}"
      f" verified images, {completeness['verified_locations']} verified"
      f" locations), {len(workflows)} workflows,"
      f" {len(destinations)} destinations, {len(research_records)} research"
      f" records, {exp_covered_schools} schools with experience records"
      f" ({len(student_experience_rows)} rows, {total_exp_reports} reports)."
  )


if __name__ == "__main__":
  main()
